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

    Returns:
        Path to the written file

    Raises:
        FileExistsError: If file exists and overwrite is False
    """
    file_path = Path(file_path)

    if file_path.exists() and not overwrite:
        raise FileExistsError(f"File already exists: {file_path}")

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
