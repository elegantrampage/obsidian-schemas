"""
Repository layer for Obsidian entity management.

Provides high-level interfaces for loading, querying, and persisting
entities from the Obsidian vault.
"""

from .base import BaseRepository, VaultPathNotConfiguredError
from .person import PersonRepository
from .company import CompanyRepository
from .book import BookRepository
from .meeting import MeetingRepository

__all__ = [
    "BaseRepository",
    "VaultPathNotConfiguredError",
    "PersonRepository",
    "CompanyRepository",
    "BookRepository",
    "MeetingRepository",
]
