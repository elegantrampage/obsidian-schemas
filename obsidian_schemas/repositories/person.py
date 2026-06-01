"""
Person repository for contact management.

Provides fast lookup of Person entities by:
- Name (exact and partial)
- Email address
- Phone number (with normalization)
- Aliases
- Slack user ID or handle

Also provides methods for managing To Discuss items.
"""

import re
import logging
from email.utils import parseaddr
from pathlib import Path
from typing import Optional, List, Type

from ..models import Person
from ..body_sections import (
    get_default_body,
    get_section,
    update_section,
    ToDiscussItem,
    parse_to_discuss_items,
    write_to_discuss_items,
)
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
        self._slack_index: dict[str, str] = {}  # slack ID/handle -> cache_key

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

        # Index Slack
        if entity.slack:
            # Store both with and without @ prefix for flexible lookup
            slack_id = entity.slack.lstrip("@").lower()
            self._slack_index[slack_id] = cache_key

    def _clear_indexes(self) -> None:
        """Clear custom indexes on refresh."""
        self._email_index.clear()
        self._phone_index.clear()
        self._alias_index.clear()
        self._slack_index.clear()

    def _remove_entity_from_indexes(self, entity: Person, cache_key: str) -> None:
        """Remove a person's entries from all indexes."""
        # Remove emails from index
        for email in entity.emails:
            if email:
                email_lower = email.lower()
                if self._email_index.get(email_lower) == cache_key:
                    del self._email_index[email_lower]

        # Remove phones from index
        for phone in entity.phones:
            norm = normalize_phone(phone)
            if norm and self._phone_index.get(norm) == cache_key:
                del self._phone_index[norm]

        # Remove WhatsApp from index
        if entity.whatsapp:
            norm = normalize_phone(entity.whatsapp)
            if norm and self._phone_index.get(norm) == cache_key:
                del self._phone_index[norm]

        # Remove aliases from index
        for alias in entity.aliases:
            if alias:
                alias_lower = alias.lower()
                if self._alias_index.get(alias_lower) == cache_key:
                    del self._alias_index[alias_lower]

        # Remove Slack from index
        if entity.slack:
            slack_id = entity.slack.lstrip("@").lower()
            if self._slack_index.get(slack_id) == cache_key:
                del self._slack_index[slack_id]

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

    def get_by_slack(self, slack_id: str) -> Optional[Person]:
        """
        Get a person by Slack user ID or handle.

        Handles both formats:
        - User ID: "U052R9S0RB6"
        - Handle: "@jsmith" or "jsmith"

        Args:
            slack_id: Slack user ID or handle

        Returns:
            Person if found, None otherwise
        """
        self._ensure_loaded()
        # Normalize: strip @ and lowercase
        slack_normalized = slack_id.lstrip("@").lower().strip()
        cache_key = self._slack_index.get(slack_normalized)
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

        # 5. Partial name match (whole words only)
        for name, person in self._cache.items():
            if query_lower in name.split():
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
        phone: Optional[str] = None,
        company: Optional[str] = None,
        auto_created: bool = True,
    ) -> Person:
        """
        Create a minimal stub Person and save to vault.

        Useful for creating placeholder contacts from meeting attendees, or
        from phone-only channels (iMessage, WhatsApp) where no name signal is
        available — in which case the caller passes `name` set to the phone
        string so the stub is identifiable by phone until enrichment confirms
        a real name.

        Args:
            name: Person's name (or phone string if no name is known)
            email: Optional email address
            phone: Optional phone number (E.164 preferred, e.g. "+447739341679")
            company: Optional company name
            auto_created: Mark as auto-created for later review

        Returns:
            The created Person entity
        """
        from datetime import datetime

        # WI-017: defensive RFC 2822 parse. If `name` looks like
        # "Display Name <email@domain>" form, separate it cleanly so the
        # regex sanitizer below doesn't mangle it into something like
        # "Display Name emailatdomaincom". This protects against any caller
        # passing the raw sender field from a scanner.
        parsed_name, parsed_email = parseaddr(name)
        if parsed_email and "@" in parsed_email:
            # An email was extracted from the input. The caller's explicit
            # `email` arg wins if present; otherwise we adopt the parsed one.
            if not email:
                email = parsed_email
            # Display-name part if present, else fall back to email local-part.
            name = parsed_name or parsed_email.split("@", 1)[0]

        # Clean name for use
        clean_name = re.sub(r'[^\w\s-]', '', name).strip()
        if not clean_name:
            clean_name = email.split("@")[0] if email else "Unknown"

        # Build aliases from email
        aliases = [email] if email else []

        phones = [phone] if phone else []

        person = Person(
            name=clean_name,
            aliases=aliases,
            emails=[email] if email else [],
            phones=phones,
            company=company or "",
            tags=["person"],
            created=datetime.now().strftime("%Y-%m-%d"),
        )

        extra_fields = {"auto_created": True} if auto_created else None
        self.save(person, body=get_default_body("person"), extra_fields=extra_fields)

        return person

    def append_to_timeline(
        self,
        person: Person,
        entry: str,
        deduplicate_key: Optional[str] = None,
    ) -> bool:
        """
        Append an entry to a person's Timeline section.

        Inserts the entry at the start of the ## Timeline section,
        preserving existing content.

        Args:
            person: The person whose timeline to update
            entry: The full entry to append (e.g., "### Dec 3, 2025\\n[[Meeting]]...")
            deduplicate_key: Optional string to check for duplicates.
                            If provided and found in existing content, skip the update.

        Returns:
            True if entry was added, False if skipped (duplicate or error)

        Raises:
            ValueError: If person not found in repository
        """
        file_path = self.get_file_path(person.name)
        if not file_path or not file_path.exists():
            raise ValueError(f"Person file not found: {person.name}")

        try:
            content = file_path.read_text(encoding="utf-8")

            # Check for duplicate if key provided
            if deduplicate_key and deduplicate_key in content:
                logger.debug(f"Timeline entry already exists for {person.name}: {deduplicate_key}")
                return False

            # Find the Timeline section
            timeline_marker = "## Timeline"
            if timeline_marker not in content:
                logger.warning(f"No Timeline section found in {person.name}")
                return False

            # Ensure entry starts with newline for clean formatting
            formatted_entry = entry if entry.startswith("\n") else f"\n{entry}"

            # Insert after "## Timeline" marker
            parts = content.split(timeline_marker, 1)
            if len(parts) != 2:
                return False

            new_content = parts[0] + timeline_marker + formatted_entry + parts[1]
            file_path.write_text(new_content, encoding="utf-8")

            logger.info(f"Updated timeline for {person.name}")
            return True

        except Exception as e:
            logger.warning(f"Failed to update timeline for {person.name}: {e}")
            return False

    # =========================================================================
    # To Discuss Methods
    # =========================================================================

    def _get_body_content(self, person: Person) -> Optional[str]:
        """Get the body content of a person's markdown file."""
        file_path = self.get_file_path(person.name)
        if not file_path or not file_path.exists():
            return None

        content = file_path.read_text(encoding="utf-8")

        # Split frontmatter and body
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                return parts[2].strip()
        return content

    def get_to_discuss_items(self, person: Person) -> List[ToDiscussItem]:
        """
        Get all To Discuss items for a person.

        Args:
            person: The person to get items for

        Returns:
            List of ToDiscussItem objects, or empty list if none

        Raises:
            ValueError: If person not found in repository
        """
        body = self._get_body_content(person)
        if body is None:
            raise ValueError(f"Person file not found: {person.name}")

        section_content = get_section(body, "To Discuss")
        if not section_content:
            return []

        return parse_to_discuss_items(section_content)

    def add_to_discuss_item(self, person: Person, text: str) -> bool:
        """
        Add a new To Discuss item for a person.

        Creates an unchecked item with today's date.

        Args:
            person: The person to add item for
            text: The item text

        Returns:
            True if item was added, False on error

        Raises:
            ValueError: If person not found in repository
        """
        file_path = self.get_file_path(person.name)
        if not file_path or not file_path.exists():
            raise ValueError(f"Person file not found: {person.name}")

        try:
            content = file_path.read_text(encoding="utf-8")

            # Split frontmatter and body
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    frontmatter = parts[1]
                    body = parts[2].lstrip("\n")
                else:
                    return False
            else:
                return False

            # Get existing items and add new one
            section_content = get_section(body, "To Discuss")
            items = parse_to_discuss_items(section_content) if section_content else []
            new_item = ToDiscussItem.create(text)
            items.append(new_item)

            # Update section
            new_section_content = write_to_discuss_items(items)
            new_body = update_section(body, "To Discuss", new_section_content, create_if_missing=True)

            # Write back
            new_content = f"---{frontmatter}---\n{new_body}"
            file_path.write_text(new_content, encoding="utf-8")

            logger.info(f"Added To Discuss item for {person.name}: {text[:50]}")
            return True

        except Exception as e:
            logger.warning(f"Failed to add To Discuss item for {person.name}: {e}")
            return False

    def update_to_discuss_item(
        self,
        person: Person,
        text: str,
        completed: bool,
    ) -> bool:
        """
        Update a To Discuss item's completion status.

        Args:
            person: The person to update item for
            text: The item text to match (exact match)
            completed: New completion status

        Returns:
            True if item was updated, False if not found or error

        Raises:
            ValueError: If person not found in repository
        """
        file_path = self.get_file_path(person.name)
        if not file_path or not file_path.exists():
            raise ValueError(f"Person file not found: {person.name}")

        try:
            content = file_path.read_text(encoding="utf-8")

            # Split frontmatter and body
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    frontmatter = parts[1]
                    body = parts[2].lstrip("\n")
                else:
                    return False
            else:
                return False

            # Get existing items
            section_content = get_section(body, "To Discuss")
            if not section_content:
                return False

            items = parse_to_discuss_items(section_content)

            # Find and update the item
            found = False
            for item in items:
                if item.text == text:
                    item.completed = completed
                    found = True
                    break

            if not found:
                logger.debug(f"To Discuss item not found for {person.name}: {text[:50]}")
                return False

            # Update section
            new_section_content = write_to_discuss_items(items)
            new_body = update_section(body, "To Discuss", new_section_content)

            # Write back
            new_content = f"---{frontmatter}---\n{new_body}"
            file_path.write_text(new_content, encoding="utf-8")

            status = "completed" if completed else "uncompleted"
            logger.info(f"Marked To Discuss item as {status} for {person.name}: {text[:50]}")
            return True

        except Exception as e:
            logger.warning(f"Failed to update To Discuss item for {person.name}: {e}")
            return False

    def remove_to_discuss_item(self, person: Person, text: str) -> bool:
        """
        Remove a To Discuss item.

        Args:
            person: The person to remove item from
            text: The item text to match (exact match)

        Returns:
            True if item was removed, False if not found or error

        Raises:
            ValueError: If person not found in repository
        """
        file_path = self.get_file_path(person.name)
        if not file_path or not file_path.exists():
            raise ValueError(f"Person file not found: {person.name}")

        try:
            content = file_path.read_text(encoding="utf-8")

            # Split frontmatter and body
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    frontmatter = parts[1]
                    body = parts[2].lstrip("\n")
                else:
                    return False
            else:
                return False

            # Get existing items
            section_content = get_section(body, "To Discuss")
            if not section_content:
                return False

            items = parse_to_discuss_items(section_content)
            original_count = len(items)

            # Filter out the item to remove
            items = [item for item in items if item.text != text]

            if len(items) == original_count:
                logger.debug(f"To Discuss item not found for {person.name}: {text[:50]}")
                return False

            # Update section
            new_section_content = write_to_discuss_items(items)
            new_body = update_section(body, "To Discuss", new_section_content)

            # Write back
            new_content = f"---{frontmatter}---\n{new_body}"
            file_path.write_text(new_content, encoding="utf-8")

            logger.info(f"Removed To Discuss item for {person.name}: {text[:50]}")
            return True

        except Exception as e:
            logger.warning(f"Failed to remove To Discuss item for {person.name}: {e}")
            return False
