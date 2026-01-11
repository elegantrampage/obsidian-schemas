"""
Repository layer for Obsidian entity management.

Provides high-level interfaces for loading, querying, and persisting
entities from the Obsidian vault.
"""

from .base import BaseRepository
from .person import PersonRepository
from .company import CompanyRepository
from .book import BookRepository

__all__ = [
    "BaseRepository",
    "PersonRepository",
    "CompanyRepository",
    "BookRepository",
]
