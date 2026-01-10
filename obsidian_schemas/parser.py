"""
Parser module for reading Obsidian markdown frontmatter.

This module provides functions to:
    - Parse YAML frontmatter from markdown files
    - Convert frontmatter to typed Pydantic models
    - Handle files with extra fields not in the model

The parser preserves extra fields for forward compatibility.
"""

import re
import yaml
from datetime import date, datetime
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Any, Type, Union

from obsidian_schemas.models import (
    BaseEntity,
    Person,
    Company,
    Book,
    Watch,
    Explore,
    GiftIdea,
    Meeting,
    get_model_for_type,
    EntityType,
)


@dataclass
class ParsedDocument:
    """
    Result of parsing an Obsidian markdown file.

    Attributes:
        frontmatter: Raw frontmatter dictionary (preserves all fields)
        entity: Typed Pydantic model if type is recognized, None otherwise
        body: Markdown body content after frontmatter
        file_path: Original file path if parsed from file
        extra_fields: Fields in frontmatter that aren't in the model
    """

    frontmatter: dict[str, Any]
    entity: Optional[EntityType]
    body: str
    file_path: Optional[Path] = None
    extra_fields: dict[str, Any] = field(default_factory=dict)


def parse_frontmatter(content: str) -> tuple[dict[str, Any], str]:
    """
    Parse YAML frontmatter from markdown content.

    Args:
        content: Full markdown content with optional frontmatter

    Returns:
        Tuple of (frontmatter dict, body content)
        If no frontmatter, returns ({}, full content)
    """
    if not content.startswith("---"):
        return {}, content

    # Match frontmatter between --- markers
    match = re.match(r"^---\n(.*?)\n---\n?(.*)", content, re.DOTALL)
    if not match:
        return {}, content

    try:
        frontmatter = yaml.safe_load(match.group(1))
        if frontmatter is None:
            frontmatter = {}
        body = match.group(2)
        return frontmatter, body
    except yaml.YAMLError:
        # If YAML parsing fails, treat as no frontmatter
        return {}, content


def _normalize_frontmatter(frontmatter: dict[str, Any]) -> dict[str, Any]:
    """
    Normalize frontmatter values for Pydantic parsing.

    Converts datetime objects to strings since YAML auto-parses dates
    but our models expect string fields.
    """
    result = {}
    for key, value in frontmatter.items():
        if isinstance(value, datetime):
            result[key] = value.strftime("%Y-%m-%d %H:%M:%S")
        elif isinstance(value, date):
            result[key] = value.strftime("%Y-%m-%d")
        elif isinstance(value, list):
            # Recursively handle list items
            result[key] = [
                v.strftime("%Y-%m-%d") if isinstance(v, date) else
                v.strftime("%Y-%m-%d %H:%M:%S") if isinstance(v, datetime) else v
                for v in value
            ]
        else:
            result[key] = value
    return result


def parse_to_model(
    frontmatter: dict[str, Any],
    model_class: Optional[Type[BaseEntity]] = None,
) -> tuple[Optional[EntityType], dict[str, Any]]:
    """
    Parse frontmatter dictionary into a typed Pydantic model.

    Args:
        frontmatter: Dictionary of frontmatter fields
        model_class: Optional specific model class to use.
                    If None, determines from 'type' field.

    Returns:
        Tuple of (model instance or None, extra fields dict)
    """
    if not frontmatter:
        return None, {}

    # Normalize values (convert dates to strings)
    normalized = _normalize_frontmatter(frontmatter)

    # Determine model class from type field if not provided
    if model_class is None:
        type_value = normalized.get("type")
        if type_value:
            model_class = get_model_for_type(type_value)

    if model_class is None:
        # Unknown type - can't create typed model
        return None, frontmatter.copy()

    try:
        # Create model - extra fields are allowed and stored in model_extra
        entity = model_class.model_validate(normalized)

        # Get extra fields that aren't in the model
        model_fields = set(model_class.model_fields.keys())
        extra_fields = {k: v for k, v in frontmatter.items() if k not in model_fields}

        return entity, extra_fields
    except Exception:
        # If model validation fails, return None with all fields as extra
        return None, frontmatter.copy()


def parse_markdown_file(
    file_path: Union[str, Path],
    expected_type: Optional[Type[BaseEntity]] = None,
) -> ParsedDocument:
    """
    Parse an Obsidian markdown file into a ParsedDocument.

    Args:
        file_path: Path to the markdown file
        expected_type: Optional expected model type for validation

    Returns:
        ParsedDocument with frontmatter, typed entity, and body

    Raises:
        FileNotFoundError: If file doesn't exist
        IOError: If file can't be read
    """
    file_path = Path(file_path)

    content = file_path.read_text(encoding="utf-8")
    frontmatter, body = parse_frontmatter(content)

    entity, extra_fields = parse_to_model(frontmatter, expected_type)

    return ParsedDocument(
        frontmatter=frontmatter,
        entity=entity,
        body=body,
        file_path=file_path,
        extra_fields=extra_fields,
    )


def parse_markdown_content(
    content: str,
    expected_type: Optional[Type[BaseEntity]] = None,
) -> ParsedDocument:
    """
    Parse markdown content string into a ParsedDocument.

    Args:
        content: Full markdown content with optional frontmatter
        expected_type: Optional expected model type for validation

    Returns:
        ParsedDocument with frontmatter, typed entity, and body
    """
    frontmatter, body = parse_frontmatter(content)
    entity, extra_fields = parse_to_model(frontmatter, expected_type)

    return ParsedDocument(
        frontmatter=frontmatter,
        entity=entity,
        body=body,
        file_path=None,
        extra_fields=extra_fields,
    )


# Convenience functions for specific entity types


def parse_person(content: str) -> Optional[Person]:
    """Parse content as a Person entity."""
    doc = parse_markdown_content(content, Person)
    return doc.entity if isinstance(doc.entity, Person) else None


def parse_company(content: str) -> Optional[Company]:
    """Parse content as a Company entity."""
    doc = parse_markdown_content(content, Company)
    return doc.entity if isinstance(doc.entity, Company) else None


def parse_book(content: str) -> Optional[Book]:
    """Parse content as a Book entity."""
    doc = parse_markdown_content(content, Book)
    return doc.entity if isinstance(doc.entity, Book) else None


def parse_meeting(content: str) -> Optional[Meeting]:
    """Parse content as a Meeting entity."""
    doc = parse_markdown_content(content, Meeting)
    return doc.entity if isinstance(doc.entity, Meeting) else None
