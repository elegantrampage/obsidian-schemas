"""
Body section parser and writer for Obsidian markdown files.

This module provides generic, entity-agnostic utilities for parsing and
manipulating markdown body sections (like ## Timeline, ## Notes, etc.).

The parser/writer work with any markdown file that uses ## headings to
delineate sections. Entity-specific logic (like knowing Person has
"To Discuss", "Timeline", "Notes") lives in the repository layer.

Key functions:
    - parse_body_sections(): Parse body into ordered dict of sections
    - write_body_sections(): Convert sections dict back to markdown
    - get_section(): Extract a single section's content
    - update_section(): Replace a section's content
    - prepend_to_section(): Add content at start of section
    - append_to_section(): Add content at end of section
    - ensure_sections_exist(): Add missing sections to body

To Discuss items:
    - ToDiscussItem: Data class for checklist items with dates
    - parse_to_discuss_items(): Parse section content into items
    - write_to_discuss_items(): Convert items back to markdown
"""

import re
import logging
from collections import OrderedDict
from dataclasses import dataclass
from datetime import date
from typing import Optional, List

logger = logging.getLogger(__name__)

# Regex to match ## headings (but not ### or deeper)
SECTION_HEADING_PATTERN = re.compile(r'^## (.+)$', re.MULTILINE)


def parse_body_sections(body: str) -> OrderedDict[str, str]:
    """
    Parse markdown body into an ordered dict of {section_name: content}.

    Sections are delimited by ## headings. Content includes everything
    from after the heading to the next ## heading (or end of file).

    Args:
        body: Markdown body content (after frontmatter)

    Returns:
        OrderedDict mapping section names to their content.
        Order is preserved from the original document.

    Example:
        Input:
            ## Timeline
            ### Jan 2026
            Met at conference.

            ## Notes
            Some notes here.

        Output:
            OrderedDict([
                ("Timeline", "### Jan 2026\\nMet at conference.\\n\\n"),
                ("Notes", "Some notes here.\\n")
            ])
    """
    if not body or not body.strip():
        return OrderedDict()

    sections = OrderedDict()

    # Find all ## headings and their positions
    matches = list(SECTION_HEADING_PATTERN.finditer(body))

    if not matches:
        # No sections found - return empty (or could return entire body as unnamed section)
        return OrderedDict()

    for i, match in enumerate(matches):
        section_name = match.group(1).strip()
        content_start = match.end()

        # Content ends at next section or end of body
        if i + 1 < len(matches):
            content_end = matches[i + 1].start()
        else:
            content_end = len(body)

        # Extract content (strip leading newline from after heading)
        content = body[content_start:content_end]
        if content.startswith('\n'):
            content = content[1:]

        sections[section_name] = content

    return sections


def write_body_sections(sections: OrderedDict[str, str]) -> str:
    """
    Convert sections dict back to markdown body string.

    Args:
        sections: OrderedDict of {section_name: content}

    Returns:
        Markdown string with ## headings and content

    Example:
        Input:
            OrderedDict([("Timeline", "Entry 1\\n"), ("Notes", "Note text\\n")])

        Output:
            "## Timeline\\nEntry 1\\n\\n## Notes\\nNote text\\n"
    """
    if not sections:
        return ""

    parts = []
    for section_name, content in sections.items():
        # Normalize content: strip surrounding newlines, we'll add proper spacing
        content = content.strip('\n') if content else ""

        # Add content with newline if non-empty
        if content:
            parts.append(f"## {section_name}\n{content}\n")
        else:
            parts.append(f"## {section_name}\n")

    # Join sections with blank line between them
    result = "\n".join(parts)

    return result


def get_section(body: str, section_name: str) -> Optional[str]:
    """
    Extract content of a single section.

    Args:
        body: Markdown body content
        section_name: Name of section to extract (without ##)

    Returns:
        Section content if found, None otherwise
    """
    sections = parse_body_sections(body)
    return sections.get(section_name)


def update_section(
    body: str,
    section_name: str,
    new_content: str,
    create_if_missing: bool = False,
    insert_after: Optional[str] = None,
) -> str:
    """
    Replace content of a section, preserving other sections.

    Args:
        body: Original markdown body
        section_name: Name of section to update
        new_content: New content for the section
        create_if_missing: If True, create section if it doesn't exist
        insert_after: If creating, insert after this section (None = at end)

    Returns:
        Updated markdown body
    """
    sections = parse_body_sections(body)

    if section_name in sections:
        sections[section_name] = new_content
    elif create_if_missing:
        # Insert at appropriate position
        if insert_after and insert_after in sections:
            new_sections = OrderedDict()
            for name, content in sections.items():
                new_sections[name] = content
                if name == insert_after:
                    new_sections[section_name] = new_content
            sections = new_sections
        else:
            sections[section_name] = new_content

    return write_body_sections(sections)


def prepend_to_section(
    body: str,
    section_name: str,
    content: str,
    create_if_missing: bool = False,
) -> str:
    """
    Add content at the start of a section.

    Args:
        body: Original markdown body
        section_name: Name of section to prepend to
        content: Content to add at start
        create_if_missing: If True, create section if it doesn't exist

    Returns:
        Updated markdown body
    """
    sections = parse_body_sections(body)

    if section_name in sections:
        existing = sections[section_name]
        # Ensure proper spacing
        if not content.endswith('\n'):
            content += '\n'
        sections[section_name] = content + existing
    elif create_if_missing:
        sections[section_name] = content

    return write_body_sections(sections)


def append_to_section(
    body: str,
    section_name: str,
    content: str,
    create_if_missing: bool = False,
) -> str:
    """
    Add content at the end of a section.

    Args:
        body: Original markdown body
        section_name: Name of section to append to
        content: Content to add at end
        create_if_missing: If True, create section if it doesn't exist

    Returns:
        Updated markdown body
    """
    sections = parse_body_sections(body)

    if section_name in sections:
        existing = sections[section_name]
        # Ensure proper spacing
        if existing and not existing.endswith('\n'):
            existing += '\n'
        sections[section_name] = existing + content
    elif create_if_missing:
        sections[section_name] = content

    return write_body_sections(sections)


def ensure_sections_exist(
    body: str,
    required_sections: List[str],
    default_content: str = "",
) -> str:
    """
    Ensure body has all required sections, adding missing ones.

    Preserves existing sections and their content. Missing sections
    are added in the order specified, at the end of existing sections.

    Args:
        body: Original markdown body
        required_sections: List of section names that must exist (in order)
        default_content: Default content for new sections

    Returns:
        Updated markdown body with all required sections
    """
    sections = parse_body_sections(body)

    # Add missing sections in order
    for section_name in required_sections:
        if section_name not in sections:
            sections[section_name] = default_content

    # Reorder to match required_sections order for new sections
    # while preserving relative order of existing sections
    ordered = OrderedDict()

    # First, add sections in required order if they exist
    for section_name in required_sections:
        if section_name in sections:
            ordered[section_name] = sections[section_name]

    # Then add any extra sections that weren't in required list
    for section_name, content in sections.items():
        if section_name not in ordered:
            ordered[section_name] = content

    return write_body_sections(ordered)


# =============================================================================
# Entity Body Configuration
# =============================================================================

# Section configuration for each entity type
ENTITY_BODY_CONFIG = {
    "person": {
        "sections": ["To Discuss", "Timeline", "Notes"],
        "default_body": "## To Discuss\n\n## Timeline\n\n## Notes\n",
    },
    "company": {
        "sections": ["People", "Timeline", "Documents", "Notes"],
        "default_body": "## People\n\n## Timeline\n\n## Documents\n\n## Notes\n",
    },
    "meeting": {
        "sections": ["Summary", "Decisions", "Actions", "Commitments", "Key Topics", "Notable Quotes"],
        "default_body": "## Summary\n\n## Decisions\n\n## Actions\n\n## Commitments\n\n## Key Topics\n\n## Notable Quotes\n",
    },
    "book": {
        "sections": ["Notes", "Quotes"],
        "default_body": "## Notes\n\n## Quotes\n",
    },
}


def get_default_body(entity_type: str) -> str:
    """
    Get default body template for an entity type.

    Args:
        entity_type: Type name (e.g., "person", "company")

    Returns:
        Default body string with all sections, or empty string if unknown type
    """
    config = ENTITY_BODY_CONFIG.get(entity_type)
    return config["default_body"] if config else ""


def get_expected_sections(entity_type: str) -> List[str]:
    """
    Get expected section names for an entity type.

    Args:
        entity_type: Type name (e.g., "person", "company")

    Returns:
        List of section names in expected order, or empty list if unknown type
    """
    config = ENTITY_BODY_CONFIG.get(entity_type)
    return config["sections"] if config else []


# =============================================================================
# To Discuss Items
# =============================================================================

# Regex for parsing checkbox items: - [ ] or - [x] followed by text and optional (date)
TO_DISCUSS_PATTERN = re.compile(
    r'^- \[([ xX])\] (.+?)(?:\s+\((\d{4}-\d{2}-\d{2})\))?$',
    re.MULTILINE
)


@dataclass
class ToDiscussItem:
    """
    Represents a single item in the To Discuss section.

    Format in markdown:
        - [ ] Item text (2026-01-11)    # unchecked item
        - [x] Item text (2026-01-11)    # checked/completed item

    Attributes:
        text: The item text content
        completed: Whether the checkbox is checked
        date_added: Date the item was added (YYYY-MM-DD string)
    """

    text: str
    completed: bool = False
    date_added: Optional[str] = None

    def to_markdown(self) -> str:
        """Convert item to markdown checkbox format."""
        checkbox = "[x]" if self.completed else "[ ]"
        date_part = f" ({self.date_added})" if self.date_added else ""
        return f"- {checkbox} {self.text}{date_part}"

    @classmethod
    def from_markdown(cls, line: str) -> Optional["ToDiscussItem"]:
        """
        Parse a single markdown line into a ToDiscussItem.

        Args:
            line: A line like "- [ ] Item text (2026-01-11)"

        Returns:
            ToDiscussItem if parsing succeeds, None otherwise
        """
        match = TO_DISCUSS_PATTERN.match(line.strip())
        if not match:
            return None

        checkbox, text, date_str = match.groups()
        return cls(
            text=text.strip(),
            completed=checkbox.lower() == "x",
            date_added=date_str,
        )

    @classmethod
    def create(cls, text: str, completed: bool = False) -> "ToDiscussItem":
        """
        Create a new ToDiscussItem with today's date.

        Args:
            text: The item text
            completed: Whether the item is checked

        Returns:
            New ToDiscussItem with date_added set to today
        """
        return cls(
            text=text,
            completed=completed,
            date_added=date.today().isoformat(),
        )


def parse_to_discuss_items(content: str) -> List[ToDiscussItem]:
    """
    Parse To Discuss section content into a list of items.

    Args:
        content: The raw content of a To Discuss section (without heading)

    Returns:
        List of ToDiscussItem objects, in order they appear

    Example:
        Input:
            "- [ ] Call about project (2026-01-11)\\n- [x] Send proposal (2026-01-08)\\n"

        Output:
            [
                ToDiscussItem(text="Call about project", completed=False, date_added="2026-01-11"),
                ToDiscussItem(text="Send proposal", completed=True, date_added="2026-01-08")
            ]
    """
    items = []
    for line in content.split("\n"):
        line = line.strip()
        if not line:
            continue
        item = ToDiscussItem.from_markdown(line)
        if item:
            items.append(item)
    return items


def write_to_discuss_items(items: List[ToDiscussItem]) -> str:
    """
    Convert a list of ToDiscussItem objects to markdown content.

    Args:
        items: List of ToDiscussItem objects

    Returns:
        Markdown string with one checkbox per line

    Example:
        Input:
            [ToDiscussItem(text="Call about project", completed=False, date_added="2026-01-11")]

        Output:
            "- [ ] Call about project (2026-01-11)\\n"
    """
    if not items:
        return ""
    return "\n".join(item.to_markdown() for item in items) + "\n"
