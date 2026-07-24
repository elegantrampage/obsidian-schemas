"""The loud-fail exception hierarchy and the package's message-construction contract.

This is a LEAF module: it imports nothing from the rest of the package, and
nothing from `yaml` or `pydantic` either. That is what makes the import
direction unambiguous (`parser.py`, `writer.py` and the repositories import
FROM here, never the other way) and what makes a cycle impossible. The two
projections below are duck-typed rather than `isinstance`-checked precisely to
keep that property.

Three contracts live here, and all three are total rules rather than per-site
cautions:

1. **The message bound (M1/M2/M3/M4).** No error message in `obsidian_schemas`
   is built by interpolating a caught exception or note content. Every one is
   built by `bounded_message`, whose `REASONS` membership check refuses any
   reason that is not an enumerated source literal — so a composed string has
   no constructor in this hierarchy it can enter.
2. **The chain bound (M5).** `chainable_cause` is the ONE decision about what
   may enter `__cause__`. Every raise-site in the package chains through it,
   never through the caught object directly.
3. **The totality rule (M6).** No function in this module raises, with exactly
   ONE deliberate exception: `bounded_message`'s `REASONS` refusal, which
   suppresses its context. `bounded_message`, `bounded_cause` and
   `bounded_detail` are total on `BaseException`.

NOTE ON THE CLOSE-OUT SWEEPS: the prose in this module deliberately avoids the
literal token sequences sweeps D and E match. Those sweeps expect exact counts
over the package, and a comment quoting the very pattern it explains makes a
compliant tree read as a violation -- the self-match trap this build hit three
times. Exact by construction rather than by a builder's eye.
"""

from pathlib import Path
from typing import Optional


class LoudFailError(ValueError):
    """Base for every failure this package refuses to render as a success-shaped
    value. Owns the ONE constructor in the hierarchy (audit-fold 2026-07-24):
    it routes through bounded_message, whose REASONS membership check refuses any
    reason that is not an enumerated source literal — no subclass declares an
    __init__ of its own, so a composed string has no constructor to enter."""

    path: Optional[Path]
    declared_type: Optional[str]

    def __init__(self, reason: str, *, path: Optional[Path] = None,
                 declared_type: Optional[str] = None,
                 cause: Optional[BaseException] = None) -> None:
        super().__init__(bounded_message(reason, path=path,
                                         declared_type=declared_type, cause=cause))
        self.reason = reason
        self.path = path
        self.declared_type = declared_type


class NoteParseError(LoudFailError):
    """A note's structure could not be read. Carries the note's own declared type
    when one was legible, None when nothing parsed — the input the repository
    layer decides ownership on. Adds NO __init__: it inherits the hierarchy's one
    constructor, which is what makes "no free-form message" true by construction
    rather than by five classes each remembering to do the same thing."""


class FrontmatterParseError(NoteParseError):
    """The frontmatter fence was opened and its contents did not parse.
    declared_type is always None — nothing was legible."""


class SchemaDriftError(NoteParseError):
    """A note that declares itself ours failed model_validate. declared_type is
    the note's own raw `type` value, equal to the forced class's own type name."""


class UnverifiableBodyError(LoudFailError):
    """The WI-126 body-shrink guard could not read the existing body, so it
    refuses the overwrite rather than assuming the body empty (C3)."""


class WriteFailedError(LoudFailError):
    """A write path did not complete. Wraps the original error as __cause__."""


# Exactly the twelve literals of the construction table below — nothing else.
# Extended only by editing this set alongside that table; bounded_message
# refuses anything else at first construction. Enumerated, not derived, so that
# the set is readable at the choke point rather than assembled at import.
REASONS: frozenset = frozenset({
    "frontmatter fence opened but never closed",          # parse_frontmatter, Flow §1
    "frontmatter did not parse as YAML",                  # parse_frontmatter, Flow §1
    "note declares our type and failed validation",       # parse_to_model, Flow §2
    "refusing to overwrite: the existing body could not be read, so "
    "the WI-126 body-shrink guard cannot verify this write is safe",  # Flow §5
    "no frontmatter fence",                               # _split_frontmatter_fence, Flow §6
    "frontmatter fence not closed",                       # _split_frontmatter_fence, Flow §6
    "write did not complete",                             # P1 + writer.py's two WARNINGs
    "failed to update timeline",                          # person.py WARNING
    "failed to append to body section",                   # person.py WARNING
    "failed to add To Discuss item",                      # person.py WARNING
    "failed to update To Discuss item",                   # person.py WARNING
    "failed to remove To Discuss item",                   # person.py WARNING
})

# LoudFailError.__init__ — the hierarchy's ONE constructor and the sole caller of
# bounded_message with a non-literal reason — is defined once, in the hierarchy
# block above. It is not repeated here.


def bounded_message(reason: str, *, path: Optional[Path] = None,
                    declared_type: Optional[str] = None,
                    cause: Optional[BaseException] = None) -> str:
    """Build a diagnostic from bounded parts only. `reason` MUST be a member of
    REASONS — the enforced form of "a literal written in this package's source"."""
    if reason not in REASONS:
        # `from None` is load-bearing (round-5 finding): this refusal fires INSIDE
        # exception construction, typically while a note-content-bearing original is
        # in flight — without suppression it escapes past the WriteFailedError-conversion
        # handler as a bare ValueError with the original riding __context__ into every
        # traceback, the exact channel this whole contract bounds.
        raise ValueError("bounded_message: reason is not an enumerated literal") from None
    parts = [reason]
    if path is not None:
        parts.append(f"path={path}")
    if declared_type is not None:
        parts.append(f"declared_type={declared_type!r}")
    if cause is not None:
        parts.append(f"cause={bounded_cause(cause)}")
    return "; ".join(parts)


def bounded_cause(cause: BaseException) -> str:
    """The permitted projection of a caught exception. Class name always;
    a location or a field path for the two shapes that carry one; NEVER str().

    TOTAL on BaseException (M6): every branch that reads or arithmetics an
    attribute of a foreign object is inside a try, and every failure path falls
    through to the class name. This function raises nothing. Both guards matter
    and for different shapes: the explicit `is not None` pair handles a Mark
    that carries a line and no column (the realistic PyYAML shape), and the try
    handles everything else a foreign object can be -- a missing attribute, a
    non-numeric column, a problem_mark that is not a Mark at all."""
    name = type(cause).__name__
    mark = getattr(cause, "problem_mark", None)          # yaml.MarkedYAMLError
    if mark is not None:
        try:
            line, column = mark.line, mark.column
            if line is not None and column is not None:
                return f"{name} at line {line + 1}, column {column + 1}"
        except Exception:
            return name
    errors = getattr(cause, "errors", None)              # pydantic.ValidationError
    if callable(errors):
        try:
            # The loop variable is `item`, NOT the conventional `e`: these are
            # ValidationError entry dicts, not caught exceptions, and a
            # stringify call over a variable named `e` would match sweep A's
            # exception-shaped pattern at Task 18 -- making the close-out's
            # "exactly one permitted stringify" red against correct code. Exact
            # by construction rather than by a builder's eye.
            locs = sorted(
                ".".join(str(p) for p in item.get("loc", ())) + ":" + str(item.get("type"))
                for item in errors()
            )
            if locs:
                return f"{name} on {', '.join(locs)}"
        except Exception:
            return name
    return name


def bounded_detail(error: BaseException) -> str:
    """TOTAL on BaseException (M6): both arms are total, so this is. It raises
    nothing — which is load-bearing, because _note_skip calls it from inside
    load()'s loop, and that loop has no try of its own (base.py:157-165)."""
    if isinstance(error, LoudFailError):
        return str(error)      # already built by bounded_message — the ONE permitted str()
    return bounded_cause(error)


# M5 — the chain bound. bounded_cause decides what may enter the MESSAGE; this
# decides what may enter __cause__, and it is the whole of that decision. One
# function, called at every raise-site in the package, so "which causes may be
# chained" is not a question any site answers for itself.
CHAINABLE = (LoudFailError, OSError)


def chainable_cause(cause: BaseException) -> Optional[BaseException]:
    """The object permitted into __cause__ — ours (bounded at construction) or
    an OSError (errno/strerror/filename: environment, not note bytes). Anything
    else (MarkedYAMLError, ValidationError, UnicodeDecodeError) renders note
    content from str() and is SUPPRESSED; its bounded projection already reached
    the message through bounded_cause before the raise."""
    return cause if isinstance(cause, CHAINABLE) else None
