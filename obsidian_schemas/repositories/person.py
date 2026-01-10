"""
Person repository for contact management.

Provides fast lookup of Person entities by:
- Name (exact and partial)
- Email address
- Phone number (with normalization)
- Aliases
"""

import re
import logging
from pathlib import Path
from typing import Optional, List, Type

from ..models import Person
from .base import BaseRepository

logger = logging.getLogger(__name__)


def normalize_phone(phone: str) -> str:
    """
    Normalize a phone number to digits only.

    Examples:
        "+44 7990 558521" → "447990558521"
        "447990558521@s.whatsapp.net" → "447990558521"
        "(555) 123-4567" → "5551234567"
    """
    if not phone:
        return ""

    # Remove WhatsApp JID suffix
    phone = phone.split("@")[0]

    # Keep only digits
    return re.sub(r"\D", "", phone)


def phones_match(phone1: str, phone2: str) -> bool:
    """
    Check if two phone numbers represent the same person.

    Handles country code variations:
    - UK: 44... vs 0...
    - US: 1... vs 10-digit
    """
    norm1 = normalize_phone(phone1)
    norm2 = normalize_phone(phone2)

    if not norm1 or not norm2:
        return False

    # Direct match
    if norm1 == norm2:
        return True

    # UK: 44 prefix vs 0 prefix
    if norm1.startswith("44") and norm2.startswith("0"):
        return norm1[2:] == norm2[1:]
    if norm2.startswith("44") and norm1.startswith("0"):
        return norm2[2:] == norm1[1:]

    # US: 1 prefix vs 10-digit
    if norm1.startswith("1") and len(norm1) == 11:
        if norm1[1:] == norm2:
            return True
    if norm2.startswith("1") and len(norm2) == 11:
        if norm2[1:] == norm1:
            return True

    return False


class PersonRepository(BaseRepository[Person]):
    """
    Repository for Person entities.

    Provides fast lookup by name, email, phone, or alias.
    Indexes are built on first load for O(1) lookups.

    Usage:
        repo = PersonRepository("/path/to/vault")
        person = repo.get("John Smith")
        person = repo.get_by_email("john@example.com")
        person = repo.get_by_phone("+447990558521")
    """

    def __init__(self, vault_path: Optional[str | Path] = None, **kwargs):
        super().__init__(vault_path, **kwargs)
        self._email_index: dict[str, str] = {}  # email -> cache_key
        self._phone_index: dict[str, str] = {}  # normalized phone -> cache_key
        self._alias_index: dict[str, str] = {}  # alias -> cache_key

    @property
    def entity_type(self) -> Type[Person]:
        return Person

    @property
    def type_name(self) -> str:
        return "person"

    def _index_entity(self, entity: Person, cache_key: str) -> None:
        """Build email, phone, and alias indexes."""
        # Index emails
        for email in entity.emails:
            if email:
                self._email_index[email.lower()] = cache_key

        # Index phones
        for phone in entity.phones:
            norm = normalize_phone(phone)
            if norm:
                self._phone_index[norm] = cache_key

        # Index WhatsApp number
        if entity.whatsapp:
            norm = normalize_phone(entity.whatsapp)
            if norm:
                self._phone_index[norm] = cache_key

        # Index aliases
        for alias in entity.aliases:
            if alias:
                self._alias_index[alias.lower()] = cache_key

    def _clear_indexes(self) -> None:
        """Clear custom indexes on refresh."""
        self._email_index.clear()
        self._phone_index.clear()
        self._alias_index.clear()

    def get_by_email(self, email: str) -> Optional[Person]:
        """
        Get a person by email address.

        Args:
            email: Email address to look up

        Returns:
            Person if found, None otherwise
        """
        self._ensure_loaded()
        email_lower = email.lower().strip()
        cache_key = self._email_index.get(email_lower)
        return self._cache.get(cache_key) if cache_key else None

    def get_by_phone(self, phone: str) -> Optional[Person]:
        """
        Get a person by phone number.

        Handles various formats and country code variations.

        Args:
            phone: Phone number in any format

        Returns:
            Person if found, None otherwise
        """
        self._ensure_loaded()
        digits = normalize_phone(phone)
        if not digits:
            return None

        # Direct lookup
        cache_key = self._phone_index.get(digits)
        if cache_key:
            return self._cache.get(cache_key)

        # Fuzzy match with country code handling
        for indexed_phone, cache_key in self._phone_index.items():
            if phones_match(digits, indexed_phone):
                return self._cache.get(cache_key)

        return None

    def get_by_alias(self, alias: str) -> Optional[Person]:
        """
        Get a person by alias/nickname.

        Args:
            alias: Alias to look up

        Returns:
            Person if found, None otherwise
        """
        self._ensure_loaded()
        alias_lower = alias.lower().strip()
        cache_key = self._alias_index.get(alias_lower)
        return self._cache.get(cache_key) if cache_key else None

    def resolve(self, query: str) -> Optional[Person]:
        """
        Resolve a query to a Person using multiple strategies.

        Tries in order:
        1. Exact name match
        2. Alias match
        3. Email match (if query contains @)
        4. Phone match (if query looks like phone number)
        5. Partial name match

        Args:
            query: Name, email, phone, or alias to search

        Returns:
            Person if found, None otherwise
        """
        self._ensure_loaded()

        if not query:
            return None

        query = query.strip()
        query_lower = query.lower()

        # 1. Exact name match
        if query_lower in self._cache:
            return self._cache[query_lower]

        # 2. Alias match
        if query_lower in self._alias_index:
            cache_key = self._alias_index[query_lower]
            return self._cache.get(cache_key)

        # 3. Email match
        if "@" in query_lower:
            cache_key = self._email_index.get(query_lower)
            if cache_key:
                return self._cache.get(cache_key)

        # 4. Phone match
        digits = normalize_phone(query)
        if len(digits) >= 7:
            person = self.get_by_phone(query)
            if person:
                return person

        # 5. Partial name match
        for name, person in self._cache.items():
            if query_lower in name:
                return person

        return None

    def get_by_role(self, role: str) -> List[Person]:
        """
        Get all people with a specific role.

        Args:
            role: Role to filter by (e.g., "vip", "coaching-client")

        Returns:
            List of people with that role
        """
        self._ensure_loaded()
        return [p for p in self._cache.values() if p.has_role(role)]

    def get_by_company(self, company: str) -> List[Person]:
        """
        Get all people at a company.

        Args:
            company: Company name (case-insensitive)

        Returns:
            List of people at that company
        """
        self._ensure_loaded()
        company_lower = company.lower()
        return [
            p for p in self._cache.values()
            if p.company and p.company.lower() == company_lower
        ]

    def create_stub(
        self,
        name: str,
        email: Optional[str] = None,
        company: Optional[str] = None,
        auto_created: bool = True,
    ) -> Person:
        """
        Create a minimal stub Person and save to vault.

        Useful for creating placeholder contacts from meeting attendees.

        Args:
            name: Person's name
            email: Optional email address
            company: Optional company name
            auto_created: Mark as auto-created for later review

        Returns:
            The created Person entity
        """
        from datetime import datetime

        # Clean name for use
        clean_name = re.sub(r'[^\w\s-]', '', name).strip()
        if not clean_name:
            clean_name = email.split("@")[0] if email else "Unknown"

        # Build aliases from email
        aliases = [email] if email else []

        person = Person(
            name=clean_name,
            aliases=aliases,
            emails=[email] if email else [],
            company=company or "",
            tags=["person"],
            created=datetime.now().strftime("%Y-%m-%d"),
        )

        extra_fields = {"auto_created": True} if auto_created else None
        self.save(person, body="## Timeline\n\n", extra_fields=extra_fields)

        return person
