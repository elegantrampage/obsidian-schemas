"""
Base repository class for Obsidian entities.

Provides common functionality for loading, caching, and persisting
entities from markdown files with YAML frontmatter.
"""

import logging
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Generic, TypeVar, Optional, List, Type

from ..models import BaseEntity
from ..parser import parse_markdown_file
from ..writer import write_markdown_file

logger = logging.getLogger(__name__)

# Default vault path - can be overridden via constructor or env var
DEFAULT_VAULT_PATH = "/Users/davewascha/Documents/Obsidian/DaveRemoteVault"
ENV_VAULT_PATH = "OBSIDIAN_VAULT_PATH"

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
            vault_path: Path to Obsidian vault. Falls back to
                       OBSIDIAN_VAULT_PATH env var, then default.
            auto_load: If True, load vault on first query.
                      If False, must call load() explicitly.
        """
        if vault_path is None:
            vault_path = os.environ.get(ENV_VAULT_PATH, DEFAULT_VAULT_PATH)

        self.vault_path = Path(vault_path)
        self.auto_load = auto_load
        self._cache: dict[str, T] = {}  # lowercase name -> entity
        self._file_map: dict[str, Path] = {}  # lowercase name -> file path
        self._loaded = False

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
        self._cache.clear()
        self._file_map.clear()

        if not self.vault_path.exists():
            logger.warning(f"Vault path does not exist: {self.vault_path}")
            self._loaded = True
            return 0

        count = 0
        for file_path in self.vault_path.glob(self.file_pattern):
            entity = self._load_file(file_path)
            if entity:
                name_key = self._get_cache_key(entity)
                self._cache[name_key] = entity
                self._file_map[name_key] = file_path
                self._index_entity(entity, name_key)
                count += 1

        logger.info(f"Loaded {count} {self.type_name} entities from vault")
        self._loaded = True
        return count

    def _load_file(self, file_path: Path) -> Optional[T]:
        """
        Load a single entity from a file.

        Returns None if file doesn't contain expected entity type.
        """
        try:
            doc = parse_markdown_file(file_path, self.entity_type)
            if doc.entity and isinstance(doc.entity, self.entity_type):
                return doc.entity
        except Exception as e:
            logger.debug(f"Could not load {file_path}: {e}")
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
    ) -> Path:
        """
        Save an entity to the vault.

        Args:
            entity: Entity to save
            body: Markdown body content
            extra_fields: Additional frontmatter fields
            overwrite: If True, overwrite existing file

        Returns:
            Path to the saved file
        """
        name = getattr(entity, "name", "Unknown")
        filename = f"@{name}.md"
        file_path = self.vault_path / filename

        write_markdown_file(
            file_path,
            entity=entity,
            body=body,
            extra_fields=extra_fields,
            overwrite=overwrite,
        )

        # Update cache
        name_key = self._get_cache_key(entity)
        self._cache[name_key] = entity
        self._file_map[name_key] = file_path
        self._index_entity(entity, name_key)

        logger.info(f"Saved {self.type_name}: {filename}")
        return file_path

    def refresh(self) -> int:
        """
        Refresh the cache by reloading from vault.

        Returns:
            Number of entities loaded
        """
        self._loaded = False
        self._clear_indexes()
        return self.load()

    def _clear_indexes(self) -> None:
        """Clear any custom indexes. Override in subclasses."""
        pass

    def __len__(self) -> int:
        """Number of entities in repository."""
        self._ensure_loaded()
        return len(self._cache)

    def __contains__(self, name: str) -> bool:
        """Check if entity exists by name."""
        self._ensure_loaded()
        return name.lower().strip() in self._cache
