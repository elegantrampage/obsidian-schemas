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

from obsidian_schemas.errors import (
    FrontmatterParseError,
    SchemaDriftError,
    chainable_cause,
)
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


def parse_frontmatter(
    content: str, *, path: Optional[Path] = None
) -> tuple[dict[str, Any], str]:
    """
    Parse YAML frontmatter from markdown content.

    Args:
        content: Full markdown content with optional frontmatter
        path: Optional path of the note, for the diagnostic only (keyword-only)

    Returns:
        Tuple of (frontmatter dict, body content)
        If no frontmatter, returns ({}, full content)
        An empty fence returns ({}, body) — a legitimate empty result.

    Raises:
        FrontmatterParseError: The document ANNOUNCED frontmatter and it did not
            parse — an opening fence with no closing fence, or YAML that
            yaml.safe_load refused (WI-020). A genuinely fence-less document is
            NOT an error and still returns ({}, content).
    """
    if not content.startswith("---"):
        return {}, content

    # Match frontmatter between --- markers.
    #
    # The `\n?` before the closing fence is load-bearing and was added by WI-020
    # (build, 2026-07-24). A zero-length frontmatter block -- `---\n---\n`, the
    # canonical way a human writes "empty frontmatter" -- has no newline of its
    # own to give the closing fence, so with a mandatory `\n` it did not match
    # here and fell through to the no-closing-fence branch below. That was
    # invisible while both branches returned the same ({}, content); once the
    # branch below RAISES, it would turn an ordinary empty fence into a hard
    # failure. The document closes its fence, so it belongs to the empty-fence
    # outcome class (safe_load -> None, normalised to {} below), not to the
    # unclosed-fence one.
    match = re.match(r"^---\n(.*?)\n?---\n?(.*)", content, re.DOTALL)
    if not match:
        raise FrontmatterParseError(
            "frontmatter fence opened but never closed", path=path
        )

    try:
        frontmatter = yaml.safe_load(match.group(1))
        if frontmatter is None:
            frontmatter = {}
        body = match.group(2)
        return frontmatter, body
    except yaml.YAMLError as e:
        raise FrontmatterParseError("frontmatter did not parse as YAML",
                                    path=path, cause=e) from chainable_cause(e)


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
    *,
    path: Optional[Path] = None,
) -> tuple[Optional[EntityType], dict[str, Any]]:
    """
    Parse frontmatter dictionary into a typed Pydantic model.

    Args:
        frontmatter: Dictionary of frontmatter fields
        model_class: Optional specific model class to use.
                    If None, determines from 'type' field.
        path: Optional path of the note, for the diagnostic only (keyword-only)

    Returns:
        Tuple of (model instance or None, extra fields dict)

    Raises:
        SchemaDriftError: The note declares OUR type and still failed
            model_validate — owned-and-drifted (WI-020). Ownership is decided on
            the note's own raw `type` value against the forced class's own
            declared type name, NEVER on whether model_validate succeeded: a
            well-formed note of a different readable type is an ANSWER, not a
            failure, and keeps returning None exactly as it does today.
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

    # Ownership is a property of the NOTE, never of the CALL. Every caller in
    # scope forces a model class, so `model_class` bears no relation to what the
    # note says it is — `declared` is that relation. The comparand is read off
    # the class's OWN Literal declaration, never hardcoded. `.get("type")` and
    # the `is not None` guard are what make the rule total: a class declaring
    # `type` without a Literal default (BaseEntity) fails the equality and lands
    # in the not-owned answer, and a class omitting the field entirely would
    # KeyError under `["type"]`.
    declared = normalized.get("type")
    type_field = model_class.model_fields.get("type")
    owned = (
        type_field is not None
        and declared is not None
        and declared == type_field.default
    )

    try:
        # Create model - extra fields are allowed and stored in model_extra
        entity = model_class.model_validate(normalized)

        # Get extra fields that aren't in the model
        model_fields = set(model_class.model_fields.keys())
        extra_fields = {k: v for k, v in frontmatter.items() if k not in model_fields}

        return entity, extra_fields
    except Exception as e:
        if owned:
            raise SchemaDriftError(
                "note declares our type and failed validation",
                path=path, declared_type=declared, cause=e,
            ) from chainable_cause(e)
        # Not ours: a readable foreign type, or no ownership evidence at all.
        # That is an ANSWER, not a failure — today's return, unchanged.
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
        FrontmatterParseError: If the note announced frontmatter that did not
            parse (WI-020) — propagated from parse_frontmatter
        SchemaDriftError: If the note declares this parser's type and failed
            validation (WI-020) — propagated from parse_to_model
    """
    file_path = Path(file_path)

    content = file_path.read_text(encoding="utf-8")
    # The ONE caller that threads the path: this is the load path, where
    # base._load_file catches and records the skip against a note the caller
    # never named, in a batch of hundreds.
    frontmatter, body = parse_frontmatter(content, path=file_path)

    entity, extra_fields = parse_to_model(frontmatter, expected_type, path=file_path)

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

    Raises:
        FrontmatterParseError: If the content announced frontmatter that did not
            parse (WI-020). This function holds no path, so the diagnostic omits
            one.
        SchemaDriftError: If the content declares this parser's type and failed
            validation (WI-020)
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
