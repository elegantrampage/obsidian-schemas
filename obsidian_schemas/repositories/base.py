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
from ..name_gate import gate_write
from ..parser import parse_markdown_file, parse_frontmatter
# `update_frontmatter_field` is imported as a BARE NAME and called unqualified
# (WI-029): AC-5's enumeration reaches bare-name calls to a member of
# `path_taking_writer_names`, and Task 10 patches this module's own binding to
# drive the half-failed-rename residual. A `writer.update_frontmatter_field(...)`
# spelling moves both.
from ..writer import write_markdown_file, write_frontmatter, update_frontmatter_field
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


MALFORMED_FRONTMATTER = "malformed-frontmatter"
SCHEMA_DRIFT = "schema-drift"
UNREADABLE = "unreadable"

#: The complete codomain of `_skip_reason` — the classification `SkippedNote.reason`
#: carries. Declared so a consumer can read it instead of re-spelling it (WI-016);
#: bound to the function's own returns by tests/derivations.py:skip_reason_return_values.
SKIP_REASONS = frozenset({MALFORMED_FRONTMATTER, SCHEMA_DRIFT, UNREADABLE})


def _skip_reason(error: BaseException) -> str:
    """Derived from the error TYPE, never passed in."""
    if isinstance(error, FrontmatterParseError):
        return MALFORMED_FRONTMATTER
    if isinstance(error, SchemaDriftError):
        return SCHEMA_DRIFT
    return UNREADABLE


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

# The four PRECONDITIONS `update_fields` refuses on before it writes anything
# (WI-029). Declared as constants rather than spelled inline so a battery can
# assert WHICH precondition refused without re-typing a message: the whole point
# of the arm is that it cannot pass on a sibling clause. Each is a fragment of
# the raised `ValueError`'s message, never the whole of it.
NO_PROVENANCE_PRECONDITION = (
    "a name change needs the provenance a move is resolved from"
)
WRITE_GUARD_PRECONDITION = (
    "the write guard is not enforcing"
)
NAME_DECLARATION_PRECONDITION = (
    "this entity's own type declares no 'name' field, so it derives no "
    "@{name}.md destination"
)
FILENAME_RULE_PRECONDITION = (
    "this delta moves the entity type's own filename rule with no rename to "
    "follow it"
)

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

    def _resolve_write_target(self, entity: T) -> Optional[Path]:
        """THE one place a mutation target is chosen from PROVENANCE (WI-029).

        Returns the file this entity was parsed from when that file lies inside
        THIS repository's vault, and None otherwise. It NEVER falls back: each
        caller applies its own documented fallback, because the correct fallback
        differs by path and a uniform one would convert `update_fields`' and the
        body-writers' loud refusals into note CREATION.

        Existence is deliberately not part of the resolution — the stamp is a
        path, not a promise the file is still there. `save` creates at it (as the
        name-derived path does today); the refusing callers keep their own
        `.exists()` check one line later.
        """
        stamped = getattr(entity, "_source_path", None)
        if stamped is None:
            return None
        candidate = Path(stamped)
        try:
            inside = candidate.resolve().is_relative_to(self.vault_path.resolve())
        except (OSError, ValueError):
            return None
        return candidate if inside else None

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
        # The target comes from PROVENANCE first (WI-029): an entity the library
        # parsed writes back to its own note, so two notes sharing one stored
        # `name:` no longer collapse onto one filename and a divergent stem no
        # longer forks on the next save. The name-derived filename is the
        # FALLBACK, and this path's fallback CREATES — that is today's behaviour
        # for an entity with no provenance and it has to stay, or nothing can
        # create a note. The WARNING precedes the write because
        # `write_markdown_file` then reaches its zero case and refuses with
        # `NoteAlreadyExists`: the readout must come first or it is never seen.
        name = getattr(entity, "name", "Unknown")
        resolved = self._resolve_write_target(entity)
        derived = self.vault_path / f"@{name}.md"
        if resolved is None and derived.exists():
            logger.warning(
                "no provenance on this %s: the write targets the derived "
                "filename and a note already exists there, path=%s",
                self.type_name, derived)
        file_path = resolved or derived

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

        # The file ACTUALLY written, never the name-derived filename (WI-029):
        # under the resolved-or-derived shape the write can land somewhere the
        # derived name does not describe, and a log naming a file the call did
        # not write is worse than no log — this class has to be reconstructable
        # from a consumer's logs.
        logger.info(f"Saved {self.type_name}: {file_path.name}")
        return file_path

    def rename_note(self, entity: T, new_filename: str) -> Path:
        """Door 3's one repository caller (WI-029). Moves the note THIS ENTITY
        was parsed from to `new_filename` inside this vault, keeps the old stem
        as an alias, repairs the caches, and RE-STAMPS the entity so its next
        write follows the file instead of recreating the old stem.

        The destination is the CALLER'S, never derived from the entity: deriving
        it here would re-introduce a name-bound target on the one path whose
        whole job is to move files, and each type's filename rule differs
        (`@{name}.md`, `_get_file_name`).

        A re-run is always SAFE — it never moves twice, never appends twice and
        never forks — and it repairs exactly the residuals in which the MOVE did
        not happen and the cause has gone. It repairs NOTHING that happened after
        the move: after a rename whose move committed and whose alias write
        raised, provenance has already moved to the destination, so a second call
        takes the no-op branch and appends nothing. That residual's recovery is
        one caller-side field edit (`update_fields(entity, {"aliases": [...]})`).
        """
        source = self._resolve_write_target(entity)
        if source is None:
            raise ValueError(
                f"no provenance for this {self.type_name}: rename_note moves the "
                f"note an entity was PARSED FROM, and this entity was not")
        if not source.exists():
            raise FileNotFoundError(f"File not found: {source}")

        destination = self.vault_path / new_filename
        try:                                            # M1 — CONTAINMENT
            contained = destination.resolve().is_relative_to(
                self.vault_path.resolve())
        except (OSError, ValueError):
            contained = False                           # unresolvable == not contained
        if not contained:
            raise ValueError(
                f"refusing to move this {self.type_name} outside the vault: "
                f"new_filename={new_filename!r}")

        mode = vault_io.guard_mode()                 # M6 — FAIL CLOSED
        if mode != "enforce":
            raise ValueError(
                f"refusing to move this {self.type_name} while the write guard "
                f"is not enforcing (OBSIDIAN_SCHEMAS_WRITE_GUARD={mode!r}): "
                f"under it door 3 OVERWRITES an occupied destination instead "
                f"of raising NoteAlreadyExists")
        old_stem = source.stem.lstrip("@")

        # WHICH FILE each side names, never how it is SPELLED. `move_note`
        # returns `_resolved(dest)` (vault_io.py:_resolved, :_move_locked), so a
        # stamp written by an earlier rename is RESOLVED while
        # `self.vault_path / new_filename` carries whatever spelling this
        # repository was constructed with — two strings, one file. The PARENT
        # is resolved and the RAW `.name` is not: resolving the directory eats
        # the spellings the environment supplies, while leaving the basename
        # alone keeps a case-only destination out of this branch even on a
        # platform whose `resolve()` normalizes case. A final-component symlink
        # is deliberately not followed here — a symlinked SOURCE is door 3's
        # refusal and a symlinked DESTINATION is M1's containment question.
        same_place = ((destination.parent.resolve(), destination.name)
                      == (source.parent.resolve(), source.name))

        if same_place:                                  # idempotent re-run
            moved = source
            moved_now = False
        elif destination.exists() and source.samefile(destination):
            # CASE-ONLY on a case-insensitive filesystem: `os.link` would raise
            # FileExistsError against the note's OWN inode, so door 3 cannot go
            # straight there. Two steps through a staging name DERIVED FROM THE
            # SOURCE (never from the destination — the seam's value must reach
            # every move's first positional), and the staging name's own
            # existence is refused by door 3's syscall rather than by a check.
            # M3: the staging name keeps the `.md` SUFFIX, so the window between
            # the two moves holds a note every reader still sees.
            staging = source.with_name(destination.stem + ".rename-tmp.md")
            vault_io.move_note(source, staging)
            moved = vault_io.move_note(staging, destination)
            moved_now = True
        else:
            moved = vault_io.move_note(source, destination)
            moved_now = True

        entity._source_path = moved                     # RE-STAMP, before anything else can fail
        new_stem = moved.stem.lstrip("@")
        aliases = list(getattr(entity, "aliases", []) or [])
        aliased = False
        if old_stem and old_stem != new_stem and old_stem not in aliases:
            aliases.append(old_stem)
            aliased = True
            # The FILE write is unconditional (`aliases:` is Obsidian's own
            # type-agnostic key); the in-memory assignment is guarded on the
            # DECLARED field, so this door never mints an undeclared extra on a
            # Company, Book or Meeting entity.
            update_frontmatter_field(moved, "aliases", aliases)
            if hasattr(entity, "aliases"):
                entity.aliases = aliases
        if moved_now or aliased:
            # The bytes at `moved` are ones THIS CALL committed, so the WI-004
            # registry is told about them — exactly what door 2 does for its own
            # write (`writer.py`'s `record_snapshot(resolved)`). Without this the
            # moved note is left UNREGISTERED: `move_note` forgets BOTH paths'
            # snapshots (`vault_io.py:_move_locked`) and door 1's alias write
            # records none, so the entity's very next `save()` would find no
            # stamp, take `write_markdown_file`'s ZERO CASE and refuse with
            # `NoteAlreadyExists` against the note the rename just created —
            # which is AC-2(e)'s own save. Guarded on "this call committed
            # something" rather than unconditional, so the idempotent no-op
            # branch cannot launder a THIRD PARTY's write into an accepted
            # precondition.
            vault_io.record_snapshot(moved)
        self._adopt(self._get_cache_key(entity), entity, moved)
        logger.info("Renamed %s note from %s to %s",        # M4 — BOTH ends
                    self.type_name, source.name, moved.name)
        return moved

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
        # PROVENANCE first, then today's name-keyed lookup (WI-029). This path's
        # fallback REFUSES rather than creating: returning a name-derived path
        # here would convert a loud miss into a brand-new fork source. `resolved`
        # is bound under its own name and not collapsed into `file_path`, because
        # the name-change arm below must know WHICH arm answered — a move has no
        # provenance to resolve from when this frame fell back.
        name = getattr(entity, "name", "")
        resolved = self._resolve_write_target(entity)
        file_path = resolved
        if file_path is None:
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

            # A name change MOVES the file now (WI-029) rather than leaving it
            # behind: the leave-behind is the divergence this item exists to end.
            # The decision is computed here, inside the lock, because it reads
            # `frontmatter` — the NOTE's stored value against the CALLER's dict,
            # so a PATCH body echoing an unchanged name still writes.
            renaming = ("name" in updates
                        and updates["name"] != frontmatter.get("name", ""))
            new_name = updates["name"] if renaming else None

            # REFUSE BEFORE ANYTHING IS WRITTEN — the arm has TWO clauses.
            #
            # (1) A rename the door cannot complete. The predicate is the door's
            # whole PRECONDITION class and not a list of remembered conjuncts:
            # every reason the door refuses its own preconditions, i.e. every
            # cause knowable from this frame's arguments and environment. A cause
            # that depends on filesystem state at move time stays the syscall's
            # (an occupied destination is `NoteAlreadyExists` out of `os.link`,
            # never a pre-check here) and the residual it leaves is stated in the
            # spec: the content write has committed, the note carries its new
            # stored name at its old filename, and the recovery is to remove the
            # cause and call `rename_note` DIRECTLY.
            if renaming and (resolved is None
                             or vault_io.guard_mode() != "enforce"
                             or "name" not in type(entity).model_fields):
                if resolved is None:
                    precondition = NO_PROVENANCE_PRECONDITION
                elif vault_io.guard_mode() != "enforce":
                    precondition = WRITE_GUARD_PRECONDITION
                else:
                    precondition = NAME_DECLARATION_PRECONDITION
                raise ValueError(
                    f"update_fields refuses to rename this {self.type_name} to "
                    f"{new_name!r}: {precondition}")

            # (2) A delta that moves the entity type's OWN filename rule with no
            # rename to follow it. Keyed on the REPOSITORY'S declared rule and
            # never on `name` or a type name, so it is structurally inert for the
            # two types whose rule IS `@{name}.md`, and DELTA-RELATIVE so an
            # already-divergent note stays writable for every delta that does not
            # move its rule further. The rule is recomputed only to COMPARE — it
            # never composes a path, and nothing here renames a Book or Meeting.
            derive = getattr(self, "_get_file_name", None)
            if not renaming and derive is not None:
                current_rule = derive(entity)            # FIRST, outside any try
                declared = type(entity).model_fields
                projected = entity.model_copy(
                    update={k: v for k, v in updates.items() if k in declared})
                refusal = ValueError(
                    f"update_fields refuses this {self.type_name} update "
                    f"{sorted(updates)}: {FILENAME_RULE_PRECONDITION}")
                try:
                    projected_rule = derive(projected)
                except Exception as exc:
                    # `model_copy(update=…)` does not validate, so a non-string
                    # `title` or a non-list `topics` can raise out of the rule.
                    # The rule cannot be recomputed over this delta: fail CLOSED,
                    # the same direction M1 takes with an OSError out of its own
                    # resolve, and never with an AttributeError leaking out of
                    # `_get_file_name`.
                    raise refusal from exc
                if projected_rule != current_rule:
                    raise refusal

            # Update frontmatter with new values — through the SEMANTIC gate
            # (WI-021, D4). IN-LOCK, because this frame refuses on the target's
            # non-existence above `note_lock` and so has nothing to gain from
            # the hoist.
            #
            # The gate judges `updates` — the DELTA this write introduces —
            # never the merged record, which is what keeps a note whose STORED
            # name is already Tier-1 dirty writable for every write that does
            # not re-introduce that name.
            #
            # The result MERGES into `frontmatter` and never into `updates`,
            # which the caller still holds. `frontmatter` is bound exactly once
            # in this frame, at the parse above, and must still be bound exactly
            # once afterwards — a re-binding here would mint a spurious second
            # arm in the wall's own derived set.
            #
            # NOTE, so the delta is specified knowingly rather than loosely:
            # since WI-029 the alias append lives in the door and no longer
            # introduces a value here, so the delta handed to the gate is *the
            # caller's `updates` dict* and that is now the whole of what this
            # write introduces.
            frontmatter.update(gate_write(updates,
                                          declared_type=self.type_name,
                                          whole_record=False))

            # Rebuild and write file
            yaml_content = write_frontmatter(frontmatter)
            new_content = f"---\n{yaml_content}---\n{body}"
            vault_io.write_note(file_path, new_content, precondition=stamp)

            # Mirror what the write COMMITTED onto the entity, so the door does
            # not overwrite a caller-supplied `aliases` list with the parsed one
            # (WI-029). Gated on `renaming` because the door is this mirror's only
            # consumer: an ungated form would add a caller-visible in-place
            # mutation to every non-rename update as well. Keyed on the KEY THIS
            # WRITE INTRODUCED and never on a type name.
            if renaming and "aliases" in updates:
                entity.aliases = frontmatter["aliases"]

        # ---- the lock is RELEASED here. No lock is held across the door. ----
        # `move_note` takes two locks in a global sorted order and the door's
        # `update_frontmatter_field` takes a third, so a held outer lock is the
        # one configuration that order cannot defend (reentrancy excuses
        # re-acquisition, never ordering). The content write has already
        # COMMITTED above, `forget_snapshot(source)` is `move_note`'s own
        # business, and the reload below was already outside the block.
        if renaming:
            file_path = self.rename_note(entity, f"@{new_name}.md")

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
