"""Single source of truth for what a 'person name' looks like (WI-105).

Architectural defect this fixes: `Person.name` is a free-form `str` and
`PersonRepository.create_stub` previously had no boundary contract on it.
Producers (Granola transcript ingester, scanners, LLM roles) could inject
any string. Each new corruption pattern got its own defensive parser
scattered across the codebase (WI-017 RFC 2822 fix in create_stub, the
clean_person_name helpers in exocortex, etc.) — patches on patches.

NameValidator centralizes the contract:

  Tier 1 — REJECT: patterns that CANNOT be a real human name. Raises
           NameValidationError. Producers must fix BEFORE calling
           create_stub. No silent ingestion.

  Tier 2 — CLEAN: trivial whitespace/normalization fixes. Applied
           transparently, recorded in CleanResult.repairs_applied so
           callers (and the invariant) can detect drift.

  Tier 3 — NOT touched here. Patterns with real false-positive risk
           (company-suffix, single-token brand-like) belong to the
           cleanup script (bin/repair-person-names.py) where a human
           reviews via HTML report. The validator is intentionally
           conservative — it must never destroy a real name.

The 2026-06-02 empirical audit across 1647 vault notes informed which
patterns are Tier 1 (definitively impossible) vs Tier 3 (ambiguous).
See orchestrator/docs/name-validation-and-cleanup.md for the audit.
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional


# ============================================================
# Tier 1 patterns — REJECT
# ============================================================

# Pattern: contiguous all-lowercase run (possibly with hyphens/digits) ending
# in a TLD — characteristic of an email that lost its @ and . punctuation and
# was concatenated into a name field.
# Examples:
#   'Naomi Pavie naomipavieatspeechmaticscom'  — ends in 'com'
#   'Anne Almeida-Anderson anneno-worriescouk' — ends in 'uk', has hyphen
#   'Faith Forster faithmforstergmailcom'      — ends in 'com'
#
# CRITICAL DESIGN: caller must NOT lowercase the input before matching. Real
# names like 'Maurizio' (ends in 'io'!), 'Francisco' (ends in 'co'),
# 'Patricio' ('io') would false-positive otherwise. The leaked-email run is
# always all-lowercase because it came from the email's local-part + domain.
# Requiring [a-z] on the *original* casing differentiates: real names start
# with a capital and would not match the run anchor.
_RFC2822_LEAK_RE = re.compile(
    r"\b[a-z][a-z0-9._\-]{4,}(com|net|org|io|ai|uk|co|gov|edu|app|biz)\b"
)

# Pattern: starts with 'Dave -', 'Me -', 'Me to', 'My -' followed by
# whitespace and a name token. Calendar event titles leaked into participant
# name field. NB: bounded with \b before the next word to avoid false-positive
# on real names like "David Field" or "Medea Smith".
_CALENDAR_PREFIX_RE = re.compile(
    r"^(Dave|Me|My)\s*[-/]\s+\w+",
)
# WI-111: loosened from `^(Me|My)\s+to\s+\w+` to `\bto\b`. The original required
# whitespace+word after "to", so 'Me to: David Field' (colon) slipped through —
# create_stub's legacy re.sub then stripped the colon → 'Me to David Field'
# (calendar_prefix), corrupting the note the morning after. `\bto\b` catches the
# colon form too. "Medea"/"Mehta" still pass (require whitespace after Me/My).
_ME_TO_PREFIX_RE = re.compile(
    r"^(Me|My)\s+to\b",
    re.IGNORECASE,
)

# WI-111: connective arrow '->' anywhere — a meeting/relationship descriptor
# ('Dave -> Thomas Gatten (Adzact)') leaked into a name. No human name contains
# '->'. Caught here so deleting create_stub's re.sub can't store the descriptor
# verbatim as a validate_strict-green-but-garbage name. Verified 2026-06-06:
# 0 of 1590 live vault names contain '->'.
_ARROW_CONNECTIVE_RE = re.compile(r"->")

# WI-111: forward slash '/' anywhere — path-hostile (breaks the @{name}.md file
# path) AND a connective descriptor form. create_stub used to strip this via the
# legacy re.sub; with that mangler deleted, '/' must be rejected at the boundary
# or it reaches the file path. Verified 2026-06-06: 0 live vault names contain '/'.
_PATH_HOSTILE_RE = re.compile(r"/")

# Pattern: 'zArchived' or 'zzArchived' prefix — Obsidian convention leak
_ARCHIVE_PREFIX_RE = re.compile(r"^z+Archived\b", re.IGNORECASE)

# Pattern: 'unknown contact' literal anywhere in name (WhatsApp scanner bug)
_UNKNOWN_CONTACT_RE = re.compile(r"unknown\s+contact", re.IGNORECASE)

# Pattern: contains @ (email leak — clear smoking gun that name field carries
# an email instead of a name). We deliberately do NOT include `<` or `>` here
# because parseaddr-style "Name <not-an-email>" malformed inputs are handled
# by the downstream regex sanitizer — they're junk but manageable, and the
# 2026-06-02 vault audit found 0 production records with `<`/`>` in name.
_EMAIL_CHARS_RE = re.compile(r"[@]")

# Pattern: pure digits (optionally with leading +) — phone string
_PURE_DIGIT_RE = re.compile(r"^\+?\d+$")


# ============================================================
# Tier 2 patterns — CLEAN
# ============================================================

_DOUBLE_SPACE_RE = re.compile(r"\s{2,}")


# ============================================================
# Public types
# ============================================================

class NameValidationError(ValueError):
    """Raised when a name matches a Tier 1 corruption pattern.

    Attributes:
        pattern: short stable identifier of the pattern matched
                 (e.g. "rfc2822_leak"). Used by invariant + cleanup script.
        detail:  human-readable description of why this name was rejected.
    """

    def __init__(self, pattern: str, detail: str):
        super().__init__(f"{pattern}: {detail}")
        self.pattern = pattern
        self.detail = detail


class WeakIdentityError(ValueError):
    """Raised by find_or_create_stub when a name is VALID but the identity is
    too weak to safely auto-create a new person note (WI-117).

    Distinct from NameValidationError: the name is a perfectly good human name,
    there's just not enough identity signal to justify spawning a (probably
    duplicate, probably half-empty) note for someone Dave likely already knows.
    Genuinely new people arrive ~5/week; a bare first name with no email/phone
    is overwhelmingly a thin mention of an EXISTING canonical, not a new person.

    Carries a human-readable `reason` string so callers can route it:
      - exocortex's _should_skip_stub wrapper → _flag_for_review(reason=...)
      - orchestrator contact_normalizer → WARN + weak_identity_skipped[] counter
      - HAL9000 entities endpoint → 422 (mirrors NameValidationError→422)

    Mirrors NameValidationError's carry-the-string pattern: `.reason` is the
    sibling of `.pattern`, kept stable so the exocortex review-queue text is
    unchanged across the round-trip.
    """

    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


# ============================================================
# Weak-identity predicate (WI-117)
# ============================================================

# Single source of truth for "is this identity too weak to auto-create a stub?"
# Moved here from exocortex's transcript._should_skip_stub so BOTH the meetings
# ingester (via a thin wrapper) and find_or_create_stub apply the SAME rule.
# The reason strings are kept BYTE-IDENTICAL to the exocortex originals
# (transcript.py:718,722) so the existing review_queue.json text is unchanged.

def weak_identity_reason(
    name: str,
    email: Optional[str] = None,
    phone: Optional[str] = None,
) -> Optional[str]:
    """Return a skip-reason string if `name` is too weak to auto-create a stub,
    else None.

    Two cases (matching the live exocortex _should_skip_stub exactly):

      1. Single-token name AND no email AND no phone — a bare first-name
         mention ("Darryl", "Vlad", "Gee"). Can't tell WHICH Darryl, and
         there's no identifier to disambiguate, so creating a new note almost
         always duplicates an existing canonical.

      2. Social-handle pattern: an underscore with no spaces ("darryl_f",
         "john_doe_92"). A handle, not a name — should be resolved to a person,
         not minted as one.

    The meetings path never supplies `phone` (it's (name, email, company)), so
    case 1 effectively gates exocortex on email-only — which is the historical
    _should_skip_stub behaviour, preserved.
    """
    if not name:
        # An empty/whitespace name is weaker than weak; let the NameValidator
        # boundary own that case. Treat as "not a weak-identity match" here.
        return None

    # Case 1: single-token name with no email and no phone.
    if " " not in name and not email and not phone:
        return "single-name, no email"

    # Case 2: social-handle pattern (underscore, no spaces).
    if "_" in name and " " not in name:
        return f"social handle pattern: {name}"

    return None


@dataclass(frozen=True)
class CleanResult:
    """Output of NameValidator.clean().

    Tier 1 patterns DO NOT appear here — clean() raises on Tier 1 just like
    validate_strict(). Tier 2 patterns get applied and recorded.
    """
    cleaned_name: str
    repairs_applied: List[str] = field(default_factory=list)
    ambiguous: bool = False  # reserved for future Tier 3 advisory output


# ============================================================
# Validator
# ============================================================

class NameValidator:
    """Boundary contract for person names.

    Pass `known_companies` if the caller has the vault's company set. This is
    NOT used in Tier 1 today (company-suffix detection is Tier 3, deferred to
    the cleanup script), but the param exists so the API is forward-compatible
    when we add advisory Tier 3 flagging.
    """

    def __init__(self, known_companies: set = None):
        self.known_companies = known_companies or set()

    # ----- main entry points -----

    def validate_strict(self, name: str, *, allow_phone_sentinel: bool = False) -> str:
        """Returns whitespace-normalized name. Raises NameValidationError on
        Tier 1 patterns.

        allow_phone_sentinel: opt-in for WI-083 phone-only stubs where the
        name field is intentionally a "+E164" or "447..." string. Off by
        default to keep producers honest.
        """
        # Phone sentinel: validated as-is when explicitly allowed
        if allow_phone_sentinel and _PURE_DIGIT_RE.match(name.strip()):
            return name.strip()

        # Empty / whitespace
        stripped = name.strip()
        if not stripped:
            raise NameValidationError("empty", "name is empty or whitespace-only")

        # Tier 1 checks (order matters for clearest error reporting)
        self._raise_on_tier1(stripped)

        # In-band light cleaning: collapse internal whitespace
        cleaned = _DOUBLE_SPACE_RE.sub(" ", stripped)
        return cleaned

    def clean(self, name: str, *, allow_phone_sentinel: bool = False) -> CleanResult:
        """Returns CleanResult. Raises on Tier 1 (the same as validate_strict).

        Tier 2 repairs are applied and recorded in repairs_applied. The
        cleaned_name reflects all applied repairs.
        """
        if allow_phone_sentinel and _PURE_DIGIT_RE.match(name.strip()):
            return CleanResult(cleaned_name=name.strip(), repairs_applied=[], ambiguous=False)

        if not name.strip():
            raise NameValidationError("empty", "name is empty or whitespace-only")

        repairs = []
        current = name

        # Tier 2: strip leading/trailing whitespace
        if current != current.strip():
            current = current.strip()
            repairs.append("strip_whitespace")

        # Tier 1 checks run AFTER strip (otherwise a name like '  Dave - X  ' would
        # not match the calendar-prefix regex). Strip is non-destructive.
        self._raise_on_tier1(current)

        # Tier 2: collapse internal double-spaces
        if _DOUBLE_SPACE_RE.search(current):
            current = _DOUBLE_SPACE_RE.sub(" ", current)
            repairs.append("double_space_collapse")

        return CleanResult(cleaned_name=current, repairs_applied=repairs, ambiguous=False)

    # ----- Tier 1 dispatcher -----

    def _raise_on_tier1(self, name: str) -> None:
        """Walks the Tier 1 pattern table; raises on the first match.

        Order matters: more-specific patterns first so the error reason is
        the most informative one. `@` is a clear smoking gun (always means
        the name carries an email), so it fires before the RFC 2822
        heuristic which would also match an intact "name@domain.com".
        """
        # Email-leak smoking gun: @ character in name
        if _EMAIL_CHARS_RE.search(name):
            raise NameValidationError(
                "contains_email_chars",
                f"name contains '@' which cannot appear in a human name: {name!r}",
            )

        # RFC 2822 leak — must search on ORIGINAL casing (see comment on
        # _RFC2822_LEAK_RE for why). Lowercasing here would false-positive
        # on 'Maurizio' / 'Francisco' / 'Patricio' and other names ending
        # in TLD-substring suffixes.
        if _RFC2822_LEAK_RE.search(name):
            raise NameValidationError(
                "rfc2822_leak",
                f"name appears to contain an email mashed into text (TLD-suffix run detected): {name!r}",
            )

        # Connective arrow ('Dave -> X', 'X -> Y') — meeting-descriptor leak.
        # Reuses the calendar_prefix pattern key so invariant by_pattern
        # reporting stays coherent (WI-111).
        if _ARROW_CONNECTIVE_RE.search(name):
            raise NameValidationError(
                "calendar_prefix",
                f"name contains a connective arrow '->' (meeting/relationship descriptor): {name!r}",
            )

        # Calendar prefix ('Dave -', 'Me -', 'My -')
        if _CALENDAR_PREFIX_RE.match(name):
            raise NameValidationError(
                "calendar_prefix",
                f"name starts with a calendar-event-title prefix ('Dave -', 'Me -', etc.): {name!r}",
            )

        # 'Me to X' / 'My to X' prefix variant
        if _ME_TO_PREFIX_RE.match(name):
            raise NameValidationError(
                "calendar_prefix",
                f"name starts with a 'Me to' / 'My to' transcript prefix: {name!r}",
            )

        # Path-hostile forward slash ('/') — breaks the @{name}.md file path
        # and is a connective descriptor form. WI-111: required because the
        # legacy create_stub re.sub that used to strip it has been deleted.
        if _PATH_HOSTILE_RE.search(name):
            raise NameValidationError(
                "path_hostile_char",
                f"name contains '/' which breaks the note file path: {name!r}",
            )

        # Archive convention leak
        if _ARCHIVE_PREFIX_RE.match(name):
            raise NameValidationError(
                "archive_prefix",
                f"name starts with Obsidian archive convention ('zArchived'): {name!r}",
            )

        # 'unknown contact' literal
        if _UNKNOWN_CONTACT_RE.search(name):
            raise NameValidationError(
                "unknown_contact",
                f"name contains 'unknown contact' literal (WhatsApp scanner artifact): {name!r}",
            )

        # Pure-digit name (sentinel path handled before this method runs)
        if _PURE_DIGIT_RE.match(name):
            raise NameValidationError(
                "pure_digit_name",
                f"name is pure digits (use allow_phone_sentinel=True for phone-only stubs): {name!r}",
            )
