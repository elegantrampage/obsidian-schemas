"""
Meeting repository for meeting note management.

Provides lookup of Meeting entities by meeting_id, date, attendee, or topic.
"""

import re
import logging
from pathlib import Path
from typing import Optional, Type, List
from datetime import datetime, date

from ..models import Meeting
from ..parser import parse_markdown_file, parse_frontmatter
from ..writer import write_markdown_file
from .base import BaseRepository

logger = logging.getLogger(__name__)


class MeetingRepository(BaseRepository[Meeting]):
    """
    Repository for Meeting entities.

    Provides lookup by meeting_id, date, attendee, and topic filtering.

    Usage:
        repo = MeetingRepository("/path/to/vault")
        meeting = repo.get_by_meeting_id("meeting_20251203_vc")
        meetings = repo.get_by_date("2025-12-03")
        meetings = repo.get_by_attendee("John Smith")
    """

    def __init__(self, vault_path: Optional[str | Path] = None, **kwargs):
        super().__init__(vault_path, **kwargs)
        self._meeting_id_index: dict[str, str] = {}  # meeting_id -> cache_key
        self._date_index: dict[str, list[str]] = {}  # date -> [cache_keys]
        self._attendee_index: dict[str, list[str]] = {}  # attendee_lower -> [cache_keys]
        self._topic_index: dict[str, list[str]] = {}  # topic_lower -> [cache_keys]

    @property
    def entity_type(self) -> Type[Meeting]:
        return Meeting

    @property
    def type_name(self) -> str:
        return "meeting"

    @property
    def file_pattern(self) -> str:
        """Meetings use 'Meeting DATE - Title.md' format."""
        return "Meeting *.md"

    def _get_cache_key(self, entity: Meeting) -> str:
        """Use meeting_id as cache key, or generate one from date."""
        if entity.meeting_id:
            return entity.meeting_id.lower().strip()
        # Fallback: use date + first attendee as key
        key_parts = [entity.date or "unknown"]
        if entity.attendees:
            key_parts.append(entity.attendees[0].lower())
        return "_".join(key_parts)

    def _load_file(self, file_path: Path) -> Optional[Meeting]:
        """
        Load a single meeting from a file.

        Only loads files that have type: meeting in frontmatter.
        """
        try:
            content = file_path.read_text(encoding="utf-8")
            frontmatter, _ = parse_frontmatter(content)

            # Only load if frontmatter explicitly has type: meeting
            if frontmatter.get("type") != "meeting":
                return None

            doc = parse_markdown_file(file_path, self.entity_type)
            if doc.entity and isinstance(doc.entity, self.entity_type):
                return doc.entity
        except Exception as e:
            # Broad on purpose — load()'s loop has no try, so this clause is the
            # no-abort guarantee. See BaseRepository._load_file (WI-020).
            self._note_skip(file_path, e)
        return None

    def _index_entity(self, entity: Meeting, cache_key: str) -> None:
        """Build meeting_id, date, attendee, and topic indexes."""
        # Meeting ID index (unique per meeting)
        if entity.meeting_id:
            meeting_id_lower = entity.meeting_id.lower().strip()
            self._meeting_id_index[meeting_id_lower] = cache_key

        # Date index (multiple meetings can be on same date)
        if entity.date:
            date_key = entity.date.strip()
            if date_key not in self._date_index:
                self._date_index[date_key] = []
            self._date_index[date_key].append(cache_key)

        # Attendee index (many-to-many)
        for attendee in entity.attendees:
            attendee_lower = attendee.lower().strip()
            if attendee_lower not in self._attendee_index:
                self._attendee_index[attendee_lower] = []
            self._attendee_index[attendee_lower].append(cache_key)

        # Topic index (many-to-many)
        for topic in entity.topics:
            topic_lower = topic.lower().strip()
            if topic_lower not in self._topic_index:
                self._topic_index[topic_lower] = []
            self._topic_index[topic_lower].append(cache_key)

    def _clear_indexes(self) -> None:
        """Clear custom indexes on refresh."""
        self._meeting_id_index.clear()
        self._date_index.clear()
        self._attendee_index.clear()
        self._topic_index.clear()

    def _remove_entity_from_indexes(self, entity: Meeting, cache_key: str) -> None:
        """Remove entity from custom indexes."""
        # Remove from meeting_id index
        if entity.meeting_id:
            meeting_id_lower = entity.meeting_id.lower().strip()
            if meeting_id_lower in self._meeting_id_index:
                del self._meeting_id_index[meeting_id_lower]

        # Remove from date index
        if entity.date:
            date_key = entity.date.strip()
            if date_key in self._date_index:
                self._date_index[date_key] = [
                    k for k in self._date_index[date_key] if k != cache_key
                ]
                if not self._date_index[date_key]:
                    del self._date_index[date_key]

        # Remove from attendee index
        for attendee in entity.attendees:
            attendee_lower = attendee.lower().strip()
            if attendee_lower in self._attendee_index:
                self._attendee_index[attendee_lower] = [
                    k for k in self._attendee_index[attendee_lower] if k != cache_key
                ]
                if not self._attendee_index[attendee_lower]:
                    del self._attendee_index[attendee_lower]

        # Remove from topic index
        for topic in entity.topics:
            topic_lower = topic.lower().strip()
            if topic_lower in self._topic_index:
                self._topic_index[topic_lower] = [
                    k for k in self._topic_index[topic_lower] if k != cache_key
                ]
                if not self._topic_index[topic_lower]:
                    del self._topic_index[topic_lower]

    def save(
        self,
        entity: Meeting,
        body: str = "",
        extra_fields: Optional[dict] = None,
        overwrite: bool = True,
        allow_body_replacement: bool = False,
    ) -> Path:
        """
        Save a meeting to the vault.

        Uses 'Meeting DATE - Title.md' filename format.

        Args:
            entity: Meeting to save
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

        logger.info(f"Saved meeting: {filename}")
        return file_path

    def _get_file_name(self, entity: Meeting) -> str:
        """
        Generate filename for a meeting.

        Format: "Meeting YYYYMMDD - Title.md" where Title is derived from
        first topic or attendees.
        """
        # Parse date
        date_str = entity.date.replace("-", "") if entity.date else "unknown"

        # Generate title from topics or attendees
        if entity.topics:
            title = entity.topics[0]
        elif entity.attendees:
            title = "with " + ", ".join(entity.attendees[:2])
            if len(entity.attendees) > 2:
                title += f" +{len(entity.attendees) - 2}"
        else:
            title = entity.meeting_id or "Untitled"

        # Clean title for filename
        title = re.sub(r'[<>:"/\\|?*]', '', title)[:50]

        return f"Meeting {date_str} - {title}.md"

    def get_by_meeting_id(self, meeting_id: str) -> Optional[Meeting]:
        """
        Get a meeting by its unique meeting_id.

        Args:
            meeting_id: Unique meeting identifier

        Returns:
            Meeting if found, None otherwise
        """
        self._ensure_loaded()
        meeting_id_lower = meeting_id.lower().strip()
        cache_key = self._meeting_id_index.get(meeting_id_lower)
        return self._cache.get(cache_key) if cache_key else None

    def get_by_date(self, date_str: str) -> List[Meeting]:
        """
        Get all meetings on a specific date.

        Args:
            date_str: Date string (YYYY-MM-DD format)

        Returns:
            List of meetings on that date
        """
        self._ensure_loaded()
        date_key = date_str.strip()
        cache_keys = self._date_index.get(date_key, [])
        return [self._cache[k] for k in cache_keys if k in self._cache]

    def get_by_date_range(
        self,
        start_date: str,
        end_date: str,
    ) -> List[Meeting]:
        """
        Get all meetings within a date range.

        Args:
            start_date: Start date (inclusive, YYYY-MM-DD format)
            end_date: End date (inclusive, YYYY-MM-DD format)

        Returns:
            List of meetings in the date range, sorted by date
        """
        self._ensure_loaded()
        results = []

        for date_key, cache_keys in self._date_index.items():
            if start_date <= date_key <= end_date:
                for k in cache_keys:
                    if k in self._cache:
                        results.append(self._cache[k])

        # Sort by date
        results.sort(key=lambda m: m.date or "")
        return results

    def get_by_attendee(self, attendee: str) -> List[Meeting]:
        """
        Get all meetings with a specific attendee.

        Args:
            attendee: Attendee name (case-insensitive)

        Returns:
            List of meetings with that attendee
        """
        self._ensure_loaded()
        attendee_lower = attendee.lower().strip()
        cache_keys = self._attendee_index.get(attendee_lower, [])
        return [self._cache[k] for k in cache_keys if k in self._cache]

    def get_by_topic(self, topic: str) -> List[Meeting]:
        """
        Get all meetings discussing a specific topic.

        Args:
            topic: Topic to search for (case-insensitive exact match)

        Returns:
            List of meetings discussing that topic
        """
        self._ensure_loaded()
        topic_lower = topic.lower().strip()
        cache_keys = self._topic_index.get(topic_lower, [])
        return [self._cache[k] for k in cache_keys if k in self._cache]

    def search_topics(self, query: str) -> List[Meeting]:
        """
        Search for meetings by partial topic match.

        Args:
            query: Search term to find in topics (case-insensitive)

        Returns:
            List of meetings with matching topics
        """
        self._ensure_loaded()
        query_lower = query.lower().strip()
        results = []
        seen = set()

        for topic, cache_keys in self._topic_index.items():
            if query_lower in topic:
                for k in cache_keys:
                    if k not in seen and k in self._cache:
                        results.append(self._cache[k])
                        seen.add(k)

        return results

    def resolve(self, query: str) -> Optional[Meeting]:
        """
        Resolve a query to a Meeting.

        Tries:
        1. Exact meeting_id match
        2. Date match (returns first if multiple)
        3. Attendee match (returns most recent)
        4. Topic search (returns first match)

        Args:
            query: Meeting ID, date, attendee name, or topic

        Returns:
            Meeting if found, None otherwise
        """
        self._ensure_loaded()

        if not query:
            return None

        query = query.strip()
        query_lower = query.lower()

        # 1. Try meeting_id match
        if query_lower in self._meeting_id_index:
            cache_key = self._meeting_id_index[query_lower]
            return self._cache.get(cache_key)

        # 2. Try date match (if query looks like a date)
        if re.match(r"^\d{4}-\d{2}-\d{2}$", query):
            meetings = self.get_by_date(query)
            if meetings:
                return meetings[0]

        # 3. Try attendee match
        meetings = self.get_by_attendee(query)
        if meetings:
            # Return most recent by date
            meetings.sort(key=lambda m: m.date or "", reverse=True)
            return meetings[0]

        # 4. Try topic search
        meetings = self.search_topics(query)
        if meetings:
            # Return most recent
            meetings.sort(key=lambda m: m.date or "", reverse=True)
            return meetings[0]

        return None

    def get_recent(self, limit: int = 10) -> List[Meeting]:
        """
        Get the most recent meetings.

        Args:
            limit: Maximum number of meetings to return

        Returns:
            List of meetings sorted by date (newest first)
        """
        self._ensure_loaded()
        all_meetings = list(self._cache.values())
        all_meetings.sort(key=lambda m: m.date or "", reverse=True)
        return all_meetings[:limit]

    def get_file_path_by_id(self, meeting_id: str) -> Optional[Path]:
        """
        Get the file path for a meeting by its meeting_id.

        Args:
            meeting_id: Unique meeting identifier

        Returns:
            Path to the markdown file, or None if not found
        """
        self._ensure_loaded()
        meeting_id_lower = meeting_id.lower().strip()
        cache_key = self._meeting_id_index.get(meeting_id_lower)
        return self._file_map.get(cache_key) if cache_key else None
