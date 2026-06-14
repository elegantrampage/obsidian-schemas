"""
Writer module for writing Obsidian markdown frontmatter.

This module provides functions to:
    - Serialize Pydantic models to YAML frontmatter
    - Write complete markdown files with frontmatter
    - Update individual frontmatter fields while preserving others

The writer preserves extra fields that aren't in the model.
"""

import re
import yaml
from pathlib import Path
from typing import Any, Optional, Union
from collections import OrderedDict

from obsidian_schemas.models import BaseEntity, EntityType
from obsidian_schemas.parser import parse_frontmatter


# Custom YAML representer for OrderedDict to preserve field order
def _represent_ordereddict(dumper: yaml.Dumper, data: OrderedDict) -> yaml.Node:
    return dumper.represent_dict(data.items())


yaml.add_representer(OrderedDict, _represent_ordereddict)


class BodyTruncationError(Exception):
    """Raised when an overwrite would silently shrink an existing note's body.

    WI-126 — the write-layer invariant (R1). ``write_markdown_file`` rebuilds a
    file from scratch and never reads the existing one, so saving an entity with
    the default empty (or template) body over an existing note silently destroys
    the note body (the meeting Timeline). The frontmatter survives (``extra=allow``
    round-trips ``model_extra``); the body is the loss. This guard turns that
    silent data loss into a loud failure at the write boundary — it holds for
    every present/future/external caller, not just the doors we found.

    A caller that genuinely intends to replace or clear a body passes
    ``allow_body_replacement=True``; the body-preserving path for partial updates
    is ``update_fields`` (which never calls ``write_markdown_file``).
    """

    def __init__(self, file_path: Union[str, Path], dropped_count: int):
        self.file_path = str(file_path)
        self.dropped_count = dropped_count
        super().__init__(
            f"Refusing to overwrite {self.file_path}: the write would drop "
            f"{dropped_count} existing body content line(s). This is almost "
            f"always a body-only data-loss bug (use update_fields for a "
            f"frontmatter-only change); pass allow_body_replacement=True only if "
            f"replacing/clearing the body is intended."
        )


def _body_content_lines(body: str) -> set[str]:
    """The content lines of a markdown body: non-blank, non-heading lines,
    stripped. Headings (``#``/``##``/``###`` …) are structural scaffolding; the
    content that must not vanish silently is the ``[[…]]`` links and prose.
    """
    lines: set[str] = set()
    for raw in body.splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        lines.add(stripped)
    return lines


def model_to_frontmatter(
    entity: BaseEntity,
    extra_fields: Optional[dict[str, Any]] = None,
    preserve_order: bool = True,
) -> dict[str, Any]:
    """
    Convert a Pydantic model to a frontmatter dictionary.

    Args:
        entity: Pydantic model instance
        extra_fields: Additional fields to include (not in model)
        preserve_order: If True, use OrderedDict to preserve field order

    Returns:
        Dictionary suitable for YAML serialization
    """
    # Get model fields in definition order
    result = OrderedDict() if preserve_order else {}

    # Access model_fields from the class, not instance (Pydantic v2.11+ deprecation)
    model_class = type(entity)

    # Add model fields first (in definition order)
    for field_name in model_class.model_fields.keys():
        value = getattr(entity, field_name)
        # Handle field aliases (e.g., for_person -> for)
        field_info = model_class.model_fields[field_name]
        output_name = field_info.alias if field_info.alias else field_name
        result[output_name] = value

    # Add extra fields from model_extra (fields not in model)
    if hasattr(entity, "model_extra") and entity.model_extra:
        for key, value in entity.model_extra.items():
            if key not in result:
                result[key] = value

    # Add any explicitly provided extra fields
    if extra_fields:
        for key, value in extra_fields.items():
            if key not in result:
                result[key] = value

    return result


def write_frontmatter(
    frontmatter: dict[str, Any],
    default_flow_style: bool = False,
    sort_keys: bool = False,
    allow_unicode: bool = True,
) -> str:
    """
    Serialize a frontmatter dictionary to YAML string.

    Args:
        frontmatter: Dictionary to serialize
        default_flow_style: YAML flow style setting
        sort_keys: Whether to sort keys alphabetically
        allow_unicode: Allow unicode in output

    Returns:
        YAML string (without --- markers)
    """
    return yaml.dump(
        frontmatter,
        default_flow_style=default_flow_style,
        sort_keys=sort_keys,
        allow_unicode=allow_unicode,
    )


def write_markdown_file(
    file_path: Union[str, Path],
    entity: Optional[BaseEntity] = None,
    frontmatter: Optional[dict[str, Any]] = None,
    body: str = "",
    extra_fields: Optional[dict[str, Any]] = None,
    overwrite: bool = False,
    allow_body_replacement: bool = False,
) -> Path:
    """
    Write a complete Obsidian markdown file with frontmatter.

    Args:
        file_path: Path to write the file
        entity: Optional Pydantic model to use as frontmatter source
        frontmatter: Optional raw frontmatter dict (used if no entity)
        body: Markdown body content
        extra_fields: Additional fields to add to frontmatter
        overwrite: If True, overwrite existing file
        allow_body_replacement: If True, bypass the WI-126 body-shrink guard
            (the explicit escape for an intentional body replacement/clear).

    Returns:
        Path to the written file

    Raises:
        FileExistsError: If file exists and overwrite is False
        BodyTruncationError: If overwriting would silently drop existing body
            content lines and allow_body_replacement is False (WI-126 / R1).
    """
    file_path = Path(file_path)

    if file_path.exists() and not overwrite:
        raise FileExistsError(f"File already exists: {file_path}")

    # WI-126 (R1) — the body-shrink guard. On an overwrite of an existing file,
    # refuse to silently drop existing body content. This makes the silent-wipe
    # class (save() with an empty/template body over a rich note) impossible for
    # every caller. Body-preserving paths (update_fields, the section writers) do
    # their own read+write and never reach here, so they are guard-exempt. New
    # files have no existing body, so the guard is a no-op on create.
    if file_path.exists() and overwrite and not allow_body_replacement:
        try:
            _, existing_body = parse_frontmatter(
                file_path.read_text(encoding="utf-8")
            )
        except Exception:
            existing_body = ""
        existing_lines = _body_content_lines(existing_body)
        if existing_lines:
            dropped = existing_lines - _body_content_lines(body)
            if dropped:
                raise BodyTruncationError(file_path, len(dropped))

    # Build frontmatter from entity or raw dict
    if entity is not None:
        fm = model_to_frontmatter(entity, extra_fields)
    elif frontmatter is not None:
        fm = frontmatter.copy()
        if extra_fields:
            fm.update(extra_fields)
    else:
        fm = extra_fields or {}

    # Serialize to YAML
    yaml_content = write_frontmatter(fm)

    # Build full content
    content = f"---\n{yaml_content}---\n\n{body}"

    # Ensure parent directory exists
    file_path.parent.mkdir(parents=True, exist_ok=True)

    # Write file
    file_path.write_text(content, encoding="utf-8")

    return file_path


def update_frontmatter_field(
    file_path: Union[str, Path],
    field_name: str,
    field_value: Any,
) -> bool:
    """
    Update a single field in an existing file's frontmatter.

    Preserves all other frontmatter fields and the body content.

    Args:
        file_path: Path to the markdown file
        field_name: Name of the field to update
        field_value: New value for the field

    Returns:
        True if update succeeded, False otherwise
    """
    file_path = Path(file_path)

    if not file_path.exists():
        return False

    try:
        content = file_path.read_text(encoding="utf-8")
        frontmatter, body = parse_frontmatter(content)

        # Update the field
        frontmatter[field_name] = field_value

        # Rebuild and write
        yaml_content = write_frontmatter(frontmatter)
        new_content = f"---\n{yaml_content}---\n{body}"

        file_path.write_text(new_content, encoding="utf-8")
        return True

    except Exception:
        return False


def update_frontmatter_fields(
    file_path: Union[str, Path],
    updates: dict[str, Any],
) -> bool:
    """
    Update multiple fields in an existing file's frontmatter.

    Preserves all other frontmatter fields and the body content.

    Args:
        file_path: Path to the markdown file
        updates: Dictionary of field names to new values

    Returns:
        True if update succeeded, False otherwise
    """
    file_path = Path(file_path)

    if not file_path.exists():
        return False

    try:
        content = file_path.read_text(encoding="utf-8")
        frontmatter, body = parse_frontmatter(content)

        # Update all fields
        frontmatter.update(updates)

        # Rebuild and write
        yaml_content = write_frontmatter(frontmatter)
        new_content = f"---\n{yaml_content}---\n{body}"

        file_path.write_text(new_content, encoding="utf-8")
        return True

    except Exception:
        return False


def roundtrip_file(file_path: Union[str, Path]) -> str:
    """
    Read and re-write a file, preserving all content.

    Useful for normalizing YAML formatting while preserving data.

    Args:
        file_path: Path to the markdown file

    Returns:
        The content that was written
    """
    file_path = Path(file_path)

    content = file_path.read_text(encoding="utf-8")
    frontmatter, body = parse_frontmatter(content)

    yaml_content = write_frontmatter(frontmatter)
    new_content = f"---\n{yaml_content}---\n{body}"

    file_path.write_text(new_content, encoding="utf-8")

    return new_content
