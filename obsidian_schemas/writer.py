"""
Writer module for writing Obsidian markdown frontmatter.

This module provides functions to:
    - Serialize Pydantic models to YAML frontmatter
    - Write complete markdown files with frontmatter
    - Update individual frontmatter fields while preserving others

The writer preserves extra fields that aren't in the model.
"""

import logging
import re
import yaml
from pathlib import Path
from typing import Any, Optional, Union
from collections import OrderedDict

from obsidian_schemas.errors import (
    FrontmatterParseError,
    LoudFailError,
    UnverifiableBodyError,
    WriteFailedError,
    bounded_message,
    chainable_cause,
)
from obsidian_schemas.models import BaseEntity, EntityType
from obsidian_schemas.name_gate import gate_write
from obsidian_schemas.parser import parse_frontmatter
# Imported as a MODULE and every door called as a module attribute (WI-004 D7):
# `tests/derivations.py:_is_write_call` gates on `ast.Attribute`, so a bare
# `write_note(...)` would match nothing and WI-020's four sweeps would go red
# against correct code.
from obsidian_schemas import vault_io

logger = logging.getLogger(__name__)


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
    allow_unverified_overwrite: bool = False,
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
        allow_unverified_overwrite: If True, commit an overwrite of a note this
            process never derived an entity from (WI-004 D8d). It says in the
            call what the caller actually knows — "I read this myself, outside
            the package's observation, and I accept that the package cannot
            verify it" — and it degrades door 2u to door-1 strength rather than
            to no protection: the write is still atomic, still mutually
            excluded, and still preconditioned on the door's own in-lock stat.
            It does NOT surrender the WI-126 body-shrink guard, which still
            runs; `allow_body_replacement` remains separately required to drop
            body content.

    Returns:
        Path to the written file

    Raises:
        NoteAlreadyExists: If the target exists and this is a create — either
            because overwrite is False, or because no entity was derived from
            those bytes in this process (WI-004 D8's zero case). This REPLACES
            the FileExistsError this function used to raise.
        StaleEntityWrite: If the target changed since the entity was derived.
        BodyTruncationError: If overwriting would silently drop existing body
            content lines and allow_body_replacement is False (WI-126 / R1).
    """
    file_path = Path(file_path)

    # WI-021 — the SEMANTIC gate, and it runs ABOVE the lock.
    #
    # The fm construction is HOISTED here from below `note_lock` because
    # `note_lock`'s own outermost acquisition `mkdir`s the sentinel home at a
    # path that DEFAULTS to the note's own parent, BEFORE any frontmatter
    # exists. A gate at the convergence point therefore refuses only AFTER
    # `<vault>/@Dave/` and a `.lock` are already on disk — confirmed by
    # execution, not by reading. Hoisting is legal precisely because the gate is
    # HANDED its declaration and reads nothing but its own arguments, so nothing
    # it touches is lock-protected.
    #
    # The hoist is mechanically local: nothing between the lock and the three
    # branches feeds them. The stamp lookup, the `unverified` flag, `is_create`
    # and the WI-126 body read are all downstream CONSUMERS of the lock, while
    # the arms read only `entity`, `frontmatter` and `extra_fields`, which are
    # parameters.
    #
    # ONE gate call, after the if/elif/else and before `write_frontmatter`,
    # never inside a branch; `whole_record` is carried to it by a local flag set
    # per branch rather than by a second call per branch. The result is MERGED —
    # `fm = gate_write(fm, …)` would be a NEW binding of `fm` and therefore a
    # NINTH arm of this function in the wall's own derived set.
    if entity is not None:
        fm = model_to_frontmatter(entity, extra_fields)
        # `model_to_frontmatter` emits every declared field unconditionally, so
        # this payload guarantees both a migration's source and its destination.
        gate_whole_record = True
    elif frontmatter is not None:
        fm = frontmatter.copy()
        if extra_fields:
            fm.update(extra_fields)
        gate_whole_record = False
    else:
        # A FRESH dict replacing what was `extra_fields or {}` — an ALIAS of the
        # dict the caller still holds. The merge below mutates whatever `fm` is
        # bound to, so leaving the alias would write the gate's normalized
        # `emails[]`/`phones[]` back into the caller's own dict: a new
        # caller-visible side effect on a documented public entry point. The
        # same single `Assign`, so this arm's identity is unchanged.
        fm = dict(extra_fields or {})
        gate_whole_record = False

    # `fm.get("type")` read HERE is the POST-merge dict's `type:` — `extra_fields`
    # merged one branch above — which is what the declaration pin requires at the
    # `frontmatter=` arm.
    fm.update(gate_write(fm, declared_type=fm.get("type"),
                         whole_record=gate_whole_record))

    # Door 2 (WI-004 D8). The lock spans the stamp lookup, the WI-126 guard's
    # read and the commit, so the guard verifies the SAME bytes the precondition
    # asserts — today those two reads had nothing held between them.
    with vault_io.note_lock(file_path) as resolved:
        stamp = vault_io.snapshot_stamp(resolved)

        # The named escape forces the 2u branch for a caller that read the note
        # itself, outside this package's observation.
        unverified = (allow_unverified_overwrite and overwrite
                      and file_path.exists())
        if unverified:
            logger.warning(
                "allow_unverified_overwrite: committing an overwrite of a note "
                "this process did not observe, path=%s", file_path,
            )

        # THE ZERO CASE. An absent stamp is the STRICTEST case, never the
        # loosest: a write whose bytes derive from no read of the target is
        # preconditioned on the target's NON-EXISTENCE, enforced atomically by
        # the kernel rather than by a check-then-mutate guard.
        is_create = not unverified and (stamp is None or overwrite is False)

        # WI-126 (R1) — the body-shrink guard. On an overwrite of an existing
        # file, refuse to silently drop existing body content. This makes the
        # silent-wipe class (save() with an empty/template body over a rich
        # note) impossible for every caller. Body-preserving paths
        # (update_fields, the section writers) do their own read+write and never
        # reach here, so they are guard-exempt. It does NOT run on the zero
        # case: there, non-existence IS the precondition, so there is no
        # existing body to shrink.
        if not is_create and file_path.exists() and not allow_body_replacement:
            try:
                _, existing_body = parse_frontmatter(
                    file_path.read_text(encoding="utf-8")
                )
            except (FrontmatterParseError, OSError, UnicodeDecodeError) as e:
                # C3 (WI-020): the one mechanism protecting against a body wipe
                # must not disable itself exactly when it cannot verify.
                raise UnverifiableBodyError(
                    "refusing to overwrite: the existing body could not be read, so "
                    "the WI-126 body-shrink guard cannot verify this write is safe",
                    path=file_path, cause=e,
                ) from chainable_cause(e)
            existing_lines = _body_content_lines(existing_body)
            if existing_lines:
                dropped = existing_lines - _body_content_lines(body)
                if dropped:
                    raise BodyTruncationError(file_path, len(dropped))

        # Serialize to YAML. The convergence point is unchanged: the fm
        # construction and its one gate call were hoisted above the lock (WI-021),
        # and `write_frontmatter` still runs here.
        yaml_content = write_frontmatter(fm)

        # Build full content
        content = f"---\n{yaml_content}---\n\n{body}"

        # Ensure parent directory exists. `mkdir` is a filesystem-mutation
        # capability, so it is named in vault_io and nowhere else (WI-004 R5).
        vault_io.ensure_dir(file_path.parent)

        if is_create:
            vault_io.create_note(resolved, content)
        else:
            vault_io.write_note(
                resolved, content, origin="entity",
                precondition=stamp if not unverified
                else vault_io.stat_stamp(resolved),
            )

        # The bytes this call just committed become the new stamp, so a process
        # that creates a note and then saves it again is a 2u update rather than
        # a refused create.
        vault_io.record_snapshot(resolved)

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
        True if update succeeded

    Raises:
        FileNotFoundError: If the file does not exist (WI-020 AC-5 P4 — this
            returned a silent False until then; base.update_fields already
            raised FileNotFoundError for the same condition)
        FrontmatterParseError: If the note's frontmatter did not parse — the
            file is left byte-identical rather than rebuilt from a failed parse
        WriteFailedError: If the write itself did not complete
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    try:
        # Door 1 (WI-004): the read happens INSIDE the lock and the write is
        # preconditioned on it, so this site structurally cannot commit from a
        # stale snapshot. The parse and the transform are unchanged.
        with vault_io.note_lock(file_path):
            content, stamp = vault_io.read_note(file_path)
            frontmatter, body = parse_frontmatter(content)

            # Update the field — through the SEMANTIC gate (WI-021, D5).
            #
            # The delta is CONSTRUCTED here, because there is no dict anywhere
            # in this frame: `field_name` and `field_value` are two loose
            # parameters. Gating the merged `frontmatter` instead would make
            # this function permanently refuse every note whose STORED name is
            # Tier-1 dirty — and D5/D6 are the only arms those notes are
            # reachable through at all, so that build greens every other
            # criterion while bricking the exact population the delta rule
            # exists to keep writable.
            #
            # IN-LOCK, and it MUST be: the declaration handed to the gate is
            # this note's own `type:`, parsed inside the lock one line above.
            frontmatter.update(gate_write({field_name: field_value},
                                          declared_type=frontmatter.get("type"),
                                          whole_record=False))

            # Rebuild and write
            yaml_content = write_frontmatter(frontmatter)
            new_content = f"---\n{yaml_content}---\n{body}"

            vault_io.write_note(file_path, new_content, precondition=stamp)
        return True

    except LoudFailError:
        raise                       # our own signal — never re-wrapped, never swallowed
    except Exception as e:
        logger.warning(bounded_message("write did not complete",
                                       path=file_path, cause=e))
        raise WriteFailedError("write did not complete",
                               path=file_path, cause=e) from chainable_cause(e)


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
        True if update succeeded

    Raises:
        FileNotFoundError: If the file does not exist (WI-020 AC-5 P4)
        FrontmatterParseError: If the note's frontmatter did not parse — the
            file is left byte-identical rather than rebuilt from a failed parse
        WriteFailedError: If the write itself did not complete
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    try:
        # Door 1 (WI-004) — see update_frontmatter_field.
        with vault_io.note_lock(file_path):
            content, stamp = vault_io.read_note(file_path)
            frontmatter, body = parse_frontmatter(content)

            # Update all fields — through the SEMANTIC gate (WI-021, D6).
            # The DELTA is the caller's `updates`, never the merged record; the
            # result merges into `frontmatter` and never into `updates`, which
            # the caller still holds. IN-LOCK for the same reason as D5: the
            # declaration is this note's own `type:`, parsed inside the lock.
            frontmatter.update(gate_write(updates,
                                          declared_type=frontmatter.get("type"),
                                          whole_record=False))

            # Rebuild and write
            yaml_content = write_frontmatter(frontmatter)
            new_content = f"---\n{yaml_content}---\n{body}"

            vault_io.write_note(file_path, new_content, precondition=stamp)
        return True

    except LoudFailError:
        raise                       # our own signal — never re-wrapped, never swallowed
    except Exception as e:
        logger.warning(bounded_message("write did not complete",
                                       path=file_path, cause=e))
        raise WriteFailedError("write did not complete",
                               path=file_path, cause=e) from chainable_cause(e)


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

    # WI-021 (D7). This function re-serializes the note's OWN parsed frontmatter
    # and introduces no field, so the gate is handed an EMPTY mapping, has
    # nothing to judge and can never refuse — which is exactly why the call is
    # worth writing rather than skipping: the wall's per-arm triple stays total,
    # and the ninth arm someone adds next month by copying this function
    # inherits a gate call instead of a hole.
    #
    # It HOLDS no declaration and therefore PASSES the literal `None`. The
    # parameter carries no default, so an absence is EXPRESSED rather than
    # defaulted; and this frame has no dict to read a `type:` off, because the
    # only one binds INSIDE the lock below. `None` is the one permitted literal
    # in this whole item, and the wall asserts that by equality.
    #
    # ABOVE the lock, by the placement rule's DEFAULT rather than by a hoist:
    # this frame carries no existence guard (that is a separate, parked defect),
    # and the placement costs nothing because the delta is empty. The result is
    # discarded — there is nothing in it.
    gate_write({}, declared_type=None, whole_record=False)

    # Door 1 (WI-004) — see update_frontmatter_field.
    with vault_io.note_lock(file_path):
        content, stamp = vault_io.read_note(file_path)
        frontmatter, body = parse_frontmatter(content)

        yaml_content = write_frontmatter(frontmatter)
        new_content = f"---\n{yaml_content}---\n{body}"

        vault_io.write_note(file_path, new_content, precondition=stamp)

    return new_content
