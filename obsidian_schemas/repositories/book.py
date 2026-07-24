"""
Book repository for reading list management.

Provides lookup of Book entities by title, author, ISBN, or status.
"""

import re
import logging
from pathlib import Path
from typing import Optional, Type, List
from datetime import datetime

from ..models import Book
from ..parser import parse_markdown_file, parse_frontmatter
from ..writer import write_markdown_file
from .base import BaseRepository

logger = logging.getLogger(__name__)


class BookRepository(BaseRepository[Book]):
    """
    Repository for Book entities.

    Provides lookup by title, author, ISBN, and status filtering.

    Usage:
        repo = BookRepository("/path/to/vault")
        book = repo.get("4,000 Weeks")
        books = repo.get_by_status("reading")
        books = repo.get_by_author("Oliver Burkeman")
    """

    def __init__(self, vault_path: Optional[str | Path] = None, **kwargs):
        super().__init__(vault_path, **kwargs)
        self._author_index: dict[str, list[str]] = {}  # author_lower -> [cache_keys]
        self._isbn_index: dict[str, str] = {}  # isbn -> cache_key
        self._status_index: dict[str, list[str]] = {}  # status -> [cache_keys]

    @property
    def entity_type(self) -> Type[Book]:
        return Book

    @property
    def type_name(self) -> str:
        return "book"

    @property
    def file_pattern(self) -> str:
        """Books use 'Title - Author.md' format, not @prefix."""
        return "*.md"

    def _get_cache_key(self, entity: Book) -> str:
        """Use title as cache key for books."""
        return entity.title.lower().strip()

    def _load_file(self, file_path: Path) -> Optional[Book]:
        """
        Load a single book from a file.

        Only loads files that have type: book in frontmatter.
        This is stricter than base class because we use *.md pattern.
        """
        try:
            # Parse without expected_type first to check actual type in frontmatter
            content = file_path.read_text(encoding="utf-8")
            frontmatter, _ = parse_frontmatter(content)

            # Only load if frontmatter explicitly has type: book
            if frontmatter.get("type") != "book":
                return None

            # Now parse with the Book model
            doc = parse_markdown_file(file_path, self.entity_type)
            if doc.entity and isinstance(doc.entity, self.entity_type):
                return doc.entity
        except Exception as e:
            # Broad on purpose — load()'s loop has no try, so this clause is the
            # no-abort guarantee. See BaseRepository._load_file (WI-020).
            self._note_skip(file_path, e)
        return None

    def _index_entity(self, entity: Book, cache_key: str) -> None:
        """Build author, ISBN, and status indexes."""
        # Author index (one author can have many books)
        if entity.author:
            author_lower = entity.author.lower().strip()
            if author_lower not in self._author_index:
                self._author_index[author_lower] = []
            self._author_index[author_lower].append(cache_key)

        # ISBN index (unique per book)
        if entity.isbn:
            isbn_clean = entity.isbn.replace("-", "").replace(" ", "")
            self._isbn_index[isbn_clean] = cache_key

        # Status index
        if entity.status:
            status_lower = entity.status.lower().strip()
            if status_lower not in self._status_index:
                self._status_index[status_lower] = []
            self._status_index[status_lower].append(cache_key)

    def _clear_indexes(self) -> None:
        """Clear custom indexes on refresh."""
        self._author_index.clear()
        self._isbn_index.clear()
        self._status_index.clear()

    def _remove_entity_from_indexes(self, entity: Book, cache_key: str) -> None:
        """Remove entity from custom indexes."""
        # Remove from author index
        if entity.author:
            author_lower = entity.author.lower().strip()
            if author_lower in self._author_index:
                self._author_index[author_lower] = [
                    k for k in self._author_index[author_lower] if k != cache_key
                ]
                if not self._author_index[author_lower]:
                    del self._author_index[author_lower]

        # Remove from ISBN index
        if entity.isbn:
            isbn_clean = entity.isbn.replace("-", "").replace(" ", "")
            if isbn_clean in self._isbn_index:
                del self._isbn_index[isbn_clean]

        # Remove from status index
        if entity.status:
            status_lower = entity.status.lower().strip()
            if status_lower in self._status_index:
                self._status_index[status_lower] = [
                    k for k in self._status_index[status_lower] if k != cache_key
                ]
                if not self._status_index[status_lower]:
                    del self._status_index[status_lower]

    def save(
        self,
        entity: Book,
        body: str = "",
        extra_fields: Optional[dict] = None,
        overwrite: bool = True,
        allow_body_replacement: bool = False,
    ) -> Path:
        """
        Save a book to the vault.

        Uses 'Title - Author.md' filename format instead of '@name.md'.

        Args:
            entity: Book to save
            body: Markdown body content
            extra_fields: Additional frontmatter fields
            overwrite: If True, overwrite existing file

        Returns:
            Path to the saved file
        """
        filename = self._get_file_name(entity)
        file_path = self.vault_path / filename

        write_markdown_file(
            file_path,
            entity=entity,
            body=body,
            extra_fields=extra_fields,
            overwrite=overwrite,
            allow_body_replacement=allow_body_replacement,
        )

        # Update cache
        name_key = self._get_cache_key(entity)
        self._cache[name_key] = entity
        self._file_map[name_key] = file_path
        self._index_entity(entity, name_key)

        logger.info(f"Saved book: {filename}")
        return file_path

    def get_by_author(self, author: str) -> List[Book]:
        """
        Get all books by an author.

        Args:
            author: Author name (case-insensitive)

        Returns:
            List of books by that author
        """
        self._ensure_loaded()
        author_lower = author.lower().strip()
        cache_keys = self._author_index.get(author_lower, [])
        return [self._cache[k] for k in cache_keys if k in self._cache]

    def get_by_isbn(self, isbn: str) -> Optional[Book]:
        """
        Get a book by ISBN.

        Args:
            isbn: ISBN (10 or 13 digit, with or without dashes)

        Returns:
            Book if found, None otherwise
        """
        self._ensure_loaded()
        isbn_clean = isbn.replace("-", "").replace(" ", "")
        cache_key = self._isbn_index.get(isbn_clean)
        return self._cache.get(cache_key) if cache_key else None

    def get_by_status(self, status: str) -> List[Book]:
        """
        Get all books with a specific status.

        Args:
            status: Reading status (to-read, reading, read, abandoned)

        Returns:
            List of books with that status
        """
        self._ensure_loaded()
        status_lower = status.lower().strip()
        cache_keys = self._status_index.get(status_lower, [])
        return [self._cache[k] for k in cache_keys if k in self._cache]

    def resolve(self, query: str) -> Optional[Book]:
        """
        Resolve a query to a Book.

        Tries:
        1. Exact title match
        2. ISBN match
        3. Partial title match
        4. Author match (returns first book)

        Args:
            query: Book title, ISBN, or author name

        Returns:
            Book if found, None otherwise
        """
        self._ensure_loaded()

        if not query:
            return None

        query = query.strip()
        query_lower = query.lower()

        # 1. Exact title match
        if query_lower in self._cache:
            return self._cache[query_lower]

        # 2. ISBN match (if query looks like ISBN)
        isbn_clean = query.replace("-", "").replace(" ", "")
        if isbn_clean.isdigit() and len(isbn_clean) in (10, 13):
            book = self.get_by_isbn(isbn_clean)
            if book:
                return book

        # 3. Partial title match
        for title, book in self._cache.items():
            if query_lower in title:
                return book

        # 4. Author match (returns first book by that author)
        books = self.get_by_author(query)
        if books:
            return books[0]

        return None

    def create_stub(
        self,
        title: str,
        author: Optional[str] = None,
        status: str = "to-read",
        auto_created: bool = True,
    ) -> Book:
        """
        Create a minimal stub Book and save to vault.

        Args:
            title: Book title
            author: Optional author name
            status: Reading status (default: to-read)
            auto_created: Mark as auto-created for later review

        Returns:
            The created Book entity
        """
        # Clean title
        clean_title = title.strip()
        if not clean_title:
            clean_title = "Untitled Book"

        book = Book(
            title=clean_title,
            author=author or "",
            status=status,
            tags=["book"],
            date_added=datetime.now().strftime("%Y-%m-%d"),
        )

        body = f"""# {clean_title}

## Why I'm Reading This

## Key Takeaways

## Notes

## Quotes
"""

        extra_fields = {"auto_created": True} if auto_created else None
        self.save(book, body=body, extra_fields=extra_fields)

        return book

    def get_file_path(self, title: str) -> Optional[Path]:
        """
        Get the file path for a book.

        Args:
            title: Book title

        Returns:
            Path to the markdown file, or None if not found
        """
        self._ensure_loaded()
        cache_key = title.lower().strip()
        return self._file_map.get(cache_key)

    def _get_file_name(self, entity: Book) -> str:
        """
        Generate filename for a book.

        Format: "Title - Author.md" or "Title.md" if no author
        """
        title = entity.title.strip()
        # Clean title for filename (remove problematic characters)
        title = re.sub(r'[<>:"/\\|?*]', '', title)

        if entity.author:
            author = entity.author.strip()
            author = re.sub(r'[<>:"/\\|?*]', '', author)
            return f"{title} - {author}.md"
        else:
            return f"{title}.md"
