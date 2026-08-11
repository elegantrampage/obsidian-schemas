"""
Base repository class for Obsidian entities.

Provides common functionality for loading, caching, and persisting
entities from markdown files with YAML frontmatter.
"""

import logging
import os
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Generic, TypeVar, Optional, List, Type

from ..errors import FrontmatterParseError, SchemaDriftError, bounded_detail
from ..models import BaseEntity
from ..parser import parse_markdown_file, parse_frontmatter
from ..writer import write_markdown_file, write_frontmatter
# Module attribute call form throughout (WI-004 D7) — see writer.py's note.
from obsidian_schemas import vault_io

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SkippedNote:
    """A note this repository OWNS and could not load (WI-020, C4).

    Before this existed, an un-loadable note vanished at DEBUG: invisible to the
    cache, so resolve() missed it and find_or_create_stub minted a duplicate —
    the dup-proliferation class WI-119/WI-125 exist to fight.
    """

    path: Path
    reason: str      # "malformed-frontmatter" | "schema-drift" | "unreadable"
    detail: str      # bounded_detail(error) — never the raw rendering (M2)


def _skip_reason(error: BaseException) -> str:
    """Derived from the error TYPE, never passed in."""
    if isinstance(error, FrontmatterParseError):
        return "malformed-frontmatter"
    if isinstance(error, SchemaDriftError):
        return "schema-drift"
    return "unreadable"


class VaultPathNotConfiguredError(ValueError):
    """Raised when a repository is constructed with no usable vault path.

    Loud-fail at the boundary (WI-024): the library has no default vault, so a
    caller that supplies neither an explicit ``vault_path`` nor a non-blank
    ``OBSIDIAN_VAULT_PATH`` is misconfigured and must be told at construction —
    not silently bound to some machine's live vault or to the current working
    directory.

    Subclasses ``ValueError`` so a consumer's existing ``except ValueError``
    still catches: the break degrades to a message change, not an uncaught
    escape.
    """


ENV_VAULT_PATH = "OBSIDIAN_VAULT_PATH"

UNCONFIGURED_VAULT_MESSAGE = (
    "No Obsidian vault configured. Pass an explicit vault_path "
    "(e.g. PersonRepository('/path/to/vault')) or set the "
    "OBSIDIAN_VAULT_PATH environment variable. A missing, blank, "
    "whitespace-only, or current-directory ('.') value counts as "
    "unconfigured."
)


def _is_unconfigured(value: object) -> bool:
    """True when *value* names no vault at all.

    A value is unconfigured if it is absent, blank/whitespace-only, or
    normalises to the current directory. The check is on the NORMALISED
    string form, never on ``isinstance(value, str)`` — this module's own
    signature accepts ``str | Path`` and ``person.py`` really does pass a
    ``Path``, so a type-gated guard would fail exactly where the library
    calls itself.
    """
    if value is None:
        return True
    text = str(value).strip()
    if not text:
        return True
    return Path(text) == Path(".")


def _resolve_vault_path(vault_path: Optional[str | Path]) -> Path:
    """Resolve the effective vault path, or raise.

    Precedence: explicit argument, then OBSIDIAN_VAULT_PATH. An unconfigured
    argument falls through to the env var; an unconfigured env var after that
    is the error.
    """
    for candidate in (vault_path, os.environ.get(ENV_VAULT_PATH)):
        if not _is_unconfigured(candidate):
            return Path(str(candidate).strip())
    raise VaultPathNotConfiguredError(UNCONFIGURED_VAULT_MESSAGE)


T = TypeVar("T", bound=BaseEntity)


class BaseRepository(ABC, Generic[T]):
    """
    Abstract base class for entity repositories.

    Handles:
    - Loading entities from vault on first access
    - Caching for performance
    - Common query patterns
    - Persisting entities back to files

    Subclasses implement entity-specific logic like file patterns
    and custom indexes.
    """

    def __init__(
        self,
        vault_path: Optional[str | Path] = None,
        auto_load: bool = True,
    ):
        """
        Initialize the repository.

        Args:
            vault_path: Path to Obsidian vault. Required unless the
                       OBSIDIAN_VAULT_PATH env var is set; there is no
                       default. A missing, blank, whitespace-only, or
                       current-directory ('.') value counts as unconfigured
                       and raises VaultPathNotConfiguredError.
            auto_load: If True, load vault on first query.
                      If False, must call load() explicitly.

        Raises:
            VaultPathNotConfiguredError: If neither route supplies a vault.
        """
        self.vault_path = _resolve_vault_path(vault_path)
        self.auto_load = auto_load
        self._cache: dict[str, T] = {}  # lowercase name -> entity
        self._file_map: dict[str, Path] = {}  # lowercase name -> file path
        self._skipped: List[SkippedNote] = []
        self._loaded = False
        # WI-004 AC-18 (the item's original March scope). Guards MUTATION of
        # _cache, _file_map and _skipped. Every mutation of the two mappings
        # REPLACES the container rather than mutating a live one, which is what
        # makes the lock-free read side true rather than aspirational: a lock
        # the reader does not take buys nothing while a writer clears and
        # repopulates in place.
        self._cache_lock = threading.RLock()

    def _adopt(self, name_key: str, entity: T, file_path: Path) -> None:
        """The ONE door through which a single entity enters the cache.

        Takes the lock, copies both mappings, sets the key in each copy, rebinds
        both attributes, and indexes — the identical three-part adoption every
        call site used to perform inline, written once.

        This is a DOOR rather than a nine-site list because a list derived over
        the pre-change tree cannot reach a site the change itself creates:
        WI-004's own create_stub recovery is the fifth caller, in the one file a
        pre-build sweep declared needed none.

        `load` deliberately does NOT call this: it is a bulk rebuild, and a
        per-note adoption would publish a half-built vault once per note instead
        of never, and copy the whole mapping N times.
        """
        with self._cache_lock:
            new_cache = dict(self._cache)
            new_file_map = dict(self._file_map)
            new_cache[name_key] = entity
            new_file_map[name_key] = file_path
            self._cache = new_cache
            self._file_map = new_file_map
            self._index_entity(entity, name_key)

    @property
    @abstractmethod
    def entity_type(self) -> Type[T]:
        """The Pydantic model class for this repository."""
        pass

    @property
    @abstractmethod
    def type_name(self) -> str:
        """The 'type' field value in frontmatter (e.g., 'person')."""
        pass

    @property
    def file_pattern(self) -> str:
        """Glob pattern for finding entity files. Default: @*.md"""
        return "@*.md"

    def _ensure_loaded(self) -> None:
        """Load vault if auto_load is enabled and not yet loaded."""
        if not self._loaded and self.auto_load:
            self.load()

    def load(self) -> int:
        """
        Load all entities from the vault.

        Returns:
            Number of entities loaded.
        """
        # A BULK rebuild, held across the whole walk: fresh local mappings are
        # filled key-by-key and both attributes are rebound ONCE at the end, so
        # a concurrent get_all() sees the complete pre- or post-refresh mapping
        # and never a half-built vault reported as the whole one. The live
        # `self._cache.clear()` this replaced is what made a writers-only lock
        # worthless to a lock-free reader (WI-004 AC-18).
        with self._cache_lock:
            new_cache: dict[str, T] = {}
            new_file_map: dict[str, Path] = {}
            self._skipped.clear()

            if not self.vault_path.exists():
                logger.warning(f"Vault path does not exist: {self.vault_path}")
                self._cache = new_cache
                self._file_map = new_file_map
                self._loaded = True
                return 0

            count = 0
            for file_path in self.vault_path.glob(self.file_pattern):
                entity = self._load_file(file_path)
                if entity:
                    name_key = self._get_cache_key(entity)
                    new_cache[name_key] = entity
                    new_file_map[name_key] = file_path
                    self._index_entity(entity, name_key)
                    count += 1

            self._cache = new_cache
            self._file_map = new_file_map

        logger.info(f"Loaded {count} {self.type_name} entities from vault")
        self._loaded = True
        return count

    @property
    def skipped_notes(self) -> List[SkippedNote]:
        """Notes this repository owns and could NOT load, since the last load()."""
        with self._cache_lock:
            return list(self._skipped)

    @property
    def skipped_count(self) -> int:
        with self._cache_lock:
            return len(self._skipped)

    def _owns(self, declared_type: Optional[str]) -> bool:
        """Can this repository PROVE the file is its own? Decided on the raw
        declared type, never on whether a model was built."""
        if declared_type is not None:
            return declared_type == self.type_name
        # Nothing legible in the note: the only remaining evidence is the glob,
        # and only if the glob is a naming convention rather than a catch-all.
        return Path(self.file_pattern).stem != "*"

    def _note_skip(self, file_path: Path, error: BaseException) -> None:
        declared = getattr(error, "declared_type", None)
        detail = bounded_detail(error)          # M2 — never the raw rendering
        if not self._owns(declared):
            logger.debug(f"Not ours, not skipped: {file_path}: {detail}")
            return
        with self._cache_lock:
            self._skipped.append(SkippedNote(file_path, _skip_reason(error), detail))
        logger.warning(f"Skipped {self.type_name} note {file_path}: {detail}")

    def _load_file(self, file_path: Path) -> Optional[T]:
        """
        Load a single entity from a file.

        Returns None if file doesn't contain expected entity type.

        The `except` stays BROAD deliberately: load()'s loop wraps this in no
        try of its own, so this clause IS the margin between one bad note and an
        aborted batch (a HAL9000 startup walks the whole vault). Loudness is
        delivered by _note_skip's WARNING plus the queryable skip surface, never
        by propagation.
        """
        try:
            # WI-004 D5: stat BEFORE the bytes are read, record only on the
            # branch that actually derives an entity. Stat-first makes the stamp
            # OLDER than the payload under a race, and an older stamp fails the
            # precondition — the failure direction is refusal. Stat-after would
            # make it newer and the failure direction a silent lost update.
            #
            # INSIDE the try, never above it: load()'s loop carries no try of
            # its own, so this broad except IS WI-020's no-abort guarantee, and
            # a stat raising above it would abort the whole vault walk on one
            # unreadable note.
            stamp = vault_io.stat_stamp(file_path)
            doc = parse_markdown_file(file_path, self.entity_type)
            if doc.entity and isinstance(doc.entity, self.entity_type):
                vault_io.remember_snapshot(file_path, stamp)
                return doc.entity
        except Exception as e:
            self._note_skip(file_path, e)
        return None

    def _get_cache_key(self, entity: T) -> str:
        """Get the cache key for an entity. Default: lowercase name."""
        return getattr(entity, "name", "").lower()

    def _index_entity(self, entity: T, cache_key: str) -> None:
        """
        Build additional indexes for the entity.

        Override in subclasses to add indexes (email, phone, etc.)
        """
        pass

    def get(self, name: str) -> Optional[T]:
        """
        Get an entity by name (case-insensitive).

        Args:
            name: Entity name to look up

        Returns:
            Entity if found, None otherwise
        """
        self._ensure_loaded()
        return self._cache.get(name.lower().strip())

    def get_all(self) -> List[T]:
        """
        Get all entities.

        Returns:
            List of all loaded entities
        """
        self._ensure_loaded()
        return list(self._cache.values())

    def get_file_path(self, name: str) -> Optional[Path]:
        """
        Get the file path for an entity by name.

        Args:
            name: Entity name

        Returns:
            Path to the entity's markdown file, or None
        """
        self._ensure_loaded()
        return self._file_map.get(name.lower().strip())

    def save(
        self,
        entity: T,
        body: str = "",
        extra_fields: Optional[dict] = None,
        overwrite: bool = True,
        allow_body_replacement: bool = False,
        allow_unverified_overwrite: bool = False,
    ) -> Path:
        """
        Save an entity to the vault.

        Args:
            entity: Entity to save
            body: Markdown body content
            extra_fields: Additional frontmatter fields
            overwrite: If True, overwrite existing file
            allow_body_replacement: If True, bypass the WI-126 body-shrink guard.
                Use only when intentionally replacing/clearing a body; for a
                frontmatter-only change use update_fields (body-preserving).

        Returns:
            Path to the saved file
        """
        name = getattr(entity, "name", "Unknown")
        filename = f"@{name}.md"
        file_path = self.vault_path / filename

        # NOT under _cache_lock: the repository lock spans the cache mutation
        # only, never the filesystem write, so no thread ever holds it while
        # acquiring note_lock (WI-004's lock-ordering ruling).
        write_markdown_file(
            file_path,
            entity=entity,
            body=body,
            extra_fields=extra_fields,
            overwrite=overwrite,
            allow_body_replacement=allow_body_replacement,
            allow_unverified_overwrite=allow_unverified_overwrite,
        )

        # Update cache — through the one adoption door.
        self._adopt(self._get_cache_key(entity), entity, file_path)

        logger.info(f"Saved {self.type_name}: {filename}")
        return file_path

    def update_fields(
        self,
        entity: T,
        updates: dict[str, Any],
    ) -> T:
        """
        Update frontmatter fields for an entity while preserving body content.

        This is the preferred way to modify entity fields - it reads the current
        file, updates only the specified fields, and writes back preserving the
        body and any extra fields.

        Args:
            entity: The entity to update (must already exist in vault)
            updates: Dictionary of field names to new values

        Returns:
            Updated entity instance

        Raises:
            ValueError: If entity not found in repository
            FileNotFoundError: If entity's file doesn't exist
        """
        name = getattr(entity, "name", "")
        file_path = self.get_file_path(name)

        if file_path is None:
            raise ValueError(f"{self.type_name} not found in repository: {name}")

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Door 1 (WI-004): read INSIDE the lock, write preconditioned on that
        # read. The transform below is unchanged.
        with vault_io.note_lock(file_path):
            content, stamp = vault_io.read_note(file_path)
            frontmatter, body = parse_frontmatter(content)

            # If name is changing, preserve old filename stem as alias so the
            # entity remains resolvable by its former name / wikilink target.
            if "name" in updates and updates["name"] != frontmatter.get("name", ""):
                old_stem = file_path.stem.lstrip("@")
                aliases = frontmatter.get("aliases", [])
                if old_stem not in aliases:
                    aliases.append(old_stem)
                    frontmatter["aliases"] = aliases

            # Update frontmatter with new values
            frontmatter.update(updates)

            # Rebuild and write file
            yaml_content = write_frontmatter(frontmatter)
            new_content = f"---\n{yaml_content}---\n{body}"
            vault_io.write_note(file_path, new_content, precondition=stamp)

        # Reload entity from file to get updated model
        updated_entity = self._load_file(file_path)
        if updated_entity is None:
            raise ValueError(f"Failed to reload {self.type_name} after update: {name}")

        # Update cache and indexes
        old_name_key = name.lower()
        new_name_key = self._get_cache_key(updated_entity)

        # Remove old cache entry and indexes
        old_entity = self._cache.get(old_name_key)
        # The REMOVAL half: copies, deleted from, rebound under the lock — never
        # a live mapping mutated in place. The _adopt call below closes the same
        # critical section (WI-004 AC-18).
        if old_entity:
            with self._cache_lock:
                self._remove_entity_from_indexes(old_entity, old_name_key)
                new_cache = dict(self._cache)
                new_file_map = dict(self._file_map)
                new_cache.pop(old_name_key, None)
                new_file_map.pop(old_name_key, None)
                self._cache = new_cache
                self._file_map = new_file_map

        # Also clean up new key if it already existed (shouldn't, but defensive)
        if new_name_key != old_name_key and new_name_key in self._cache:
            self._remove_entity_from_indexes(self._cache[new_name_key], new_name_key)

        self._adopt(new_name_key, updated_entity, file_path)

        logger.info(f"Updated {self.type_name} fields: {name} -> {list(updates.keys())}")
        return updated_entity

    def refresh(self) -> int:
        """
        Refresh the cache by reloading from vault.

        Safety guard: if the reload finds 0 entities while the existing cache
        had entries, the previous cache is restored and -1 is returned. This
        prevents catastrophic cache loss when ``Path.glob`` returns empty due
        to a transient filesystem/permission issue (e.g. macOS TCC/Full Disk
        Access denying directory enumeration on a vault that did load
        successfully at startup).

        Returns:
            Number of entities loaded, or -1 if the reload was refused to
            avoid clobbering a non-empty cache.
        """
        with self._cache_lock:
            cache_snapshot = dict(self._cache)
            file_map_snapshot = dict(self._file_map)
        had_entries = len(cache_snapshot) > 0

        self._loaded = False
        self._clear_indexes()
        count = self.load()

        if count == 0 and had_entries:
            logger.error(
                "refresh() found 0 %s entities but cache had %d - refusing "
                "to clobber. Likely a permission/enumeration issue (e.g. "
                "macOS TCC/Full Disk Access). Restoring previous cache.",
                self.type_name,
                len(cache_snapshot),
            )
            with self._cache_lock:
                self._cache = cache_snapshot
                self._file_map = file_map_snapshot
                for cache_key, entity in cache_snapshot.items():
                    self._index_entity(entity, cache_key)
            self._loaded = True
            return -1

        return count

    def _clear_indexes(self) -> None:
        """Clear any custom indexes. Override in subclasses."""
        pass

    def _remove_entity_from_indexes(self, entity: T, cache_key: str) -> None:
        """
        Remove a specific entity's entries from indexes.

        Override in subclasses to remove entity-specific index entries.
        Called before re-indexing during updates.

        Args:
            entity: The entity being removed/updated
            cache_key: The cache key for this entity
        """
        pass

    def __len__(self) -> int:
        """Number of entities in repository."""
        self._ensure_loaded()
        return len(self._cache)

    def __contains__(self, name: str) -> bool:
        """Check if entity exists by name."""
        self._ensure_loaded()
        return name.lower().strip() in self._cache
