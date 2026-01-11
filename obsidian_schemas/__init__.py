"""
Obsidian Schemas - Canonical entity schemas for Obsidian frontmatter.

This package provides Pydantic models for entity types used in Obsidian vaults,
along with parser and writer modules for reading/writing markdown frontmatter.

Usage:
    from obsidian_schemas import Person, Company, Book
    from obsidian_schemas.parser import parse_frontmatter
    from obsidian_schemas.writer import write_frontmatter

Entity types supported:
    - Person: Contact/person notes
    - Company: Organization notes
    - Book: Reading list items
    - Watch: Films/series to watch
    - Explore: Links/topics to explore
    - GiftIdea: Gift ideas for people
    - Meeting: Meeting notes
"""

from obsidian_schemas.models import (
    Person,
    Company,
    Book,
    Watch,
    Explore,
    GiftIdea,
    Meeting,
    EntityType,
    get_model_for_type,
)
from obsidian_schemas.parser import (
    parse_frontmatter,
    parse_markdown_file,
    ParsedDocument,
)
from obsidian_schemas.writer import (
    write_frontmatter,
    write_markdown_file,
    update_frontmatter_field,
)
from obsidian_schemas.body_sections import (
    parse_body_sections,
    write_body_sections,
    get_section,
    update_section,
    prepend_to_section,
    append_to_section,
    ensure_sections_exist,
    get_default_body,
    get_expected_sections,
    ENTITY_BODY_CONFIG,
    ToDiscussItem,
    parse_to_discuss_items,
    write_to_discuss_items,
)
from obsidian_schemas.repositories import (
    PersonRepository,
    CompanyRepository,
)

__version__ = "0.1.0"

__all__ = [
    # Models
    "Person",
    "Company",
    "Book",
    "Watch",
    "Explore",
    "GiftIdea",
    "Meeting",
    "EntityType",
    "get_model_for_type",
    # Parser
    "parse_frontmatter",
    "parse_markdown_file",
    "ParsedDocument",
    # Writer
    "write_frontmatter",
    "write_markdown_file",
    "update_frontmatter_field",
    # Body Sections
    "parse_body_sections",
    "write_body_sections",
    "get_section",
    "update_section",
    "prepend_to_section",
    "append_to_section",
    "ensure_sections_exist",
    "get_default_body",
    "get_expected_sections",
    "ENTITY_BODY_CONFIG",
    # To Discuss Items
    "ToDiscussItem",
    "parse_to_discuss_items",
    "write_to_discuss_items",
    # Repositories
    "PersonRepository",
    "CompanyRepository",
]
