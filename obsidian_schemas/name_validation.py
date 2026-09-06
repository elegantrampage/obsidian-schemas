"""Single source of truth for what a 'person name' AND a 'company name' look
like (WI-105; WI-022 added the company table).

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

WI-022 — TWO Tier-1 tables, ONE dispatcher. `TIER1_BRANCHES` is the person
table and stays the default of every entry point, so nothing on the person path
moved. `COMPANY_TIER1_BRANCHES` is a second table with its OWN membership,
walked by the same `_raise_on_tier1` through the `branches=` keyword: a company
name is a domain often enough that `rfc2822_leak` would refuse the real
"wetransfer.com", and four more person branches are transcript artifacts with no
company producer — while the path-hostile class must be WIDER for a company,
because `company.py`'s deleted mangler had been silently absorbing every
filename- and wikilink-hostile character. The 2026-09-06 audit across 2159 live
company notes grounds that membership (docs/company-name-corpus-audit.md).
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
#
# WI-117 follow-up (2026-06-09): extended to UNICODE arrows (→ ⟶ ⇒ ➜ ↦ ⇨). A
# WhatsApp chat-direction label "Me → Thyra October" slipped through both the
# recovery pass (name_cleaning only handled ASCII '[-/]') AND this gate (ASCII
# '->' only), and was stored verbatim as a junk duplicate of the real
# '@Thyra October.md'. name_cleaning now RECOVERS the leading "Me →" first-person
# form (-> the participant); this gate rejects any arrow that survives recovery
# (mid-string connectives like 'X → Y'). Verified 2026-06-09: 1 live vault name
# contained '→' (that junk dup, removed in the same fix); 0 contain the others.
_ARROW_CONNECTIVE_RE = re.compile(r"->|[→⟶⇒➜↦⇨]")

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
# The Tier-1 refusal surface, REIFIED (WI-021, Design §3)
# ============================================================
#
# `_raise_on_tier1`'s docstring has always claimed a "pattern table"; the body
# was a hand-written `if` chain of nine branches raising SEVEN distinct keys,
# because the arrow, calendar and 'Me to' branches all raise `calendar_prefix`
# deliberately (WI-111). There was no iterable object anywhere in the module, so
# nothing could sweep it — and a sweep keyed on the RAISED KEY yields seven
# fixtures and leaves two branches unexercised.
#
# The unit is therefore the BRANCH, not the pattern key. Ten records: the nine
# chain branches plus `empty`, which both public entry points raise ABOVE the
# chain and which must NOT be moved into it — `_PURE_DIGIT_RE` is `^\+?\d+$` and
# cannot match an empty string, so the sentinel exemption sitting above the
# `empty` check cannot swallow an empty name.
#
# The rewrite below is BEHAVIOUR-PRESERVING: same order, same keys, same match
# methods (`.search` vs `.match` differ per branch and are part of the
# behaviour), same messages, same raise sites.


@dataclass(frozen=True)
class Tier1Branch:
    """One refusal branch of the Tier-1 surface.

    `branch_id` is the sweep's unit and is unique in the tuple; `pattern` is the
    stable key the branch RAISES and is deliberately not unique (three branches
    share `calendar_prefix`). `specimen` is a name that makes THIS branch fire
    and no earlier one, so a sweep has an input per record. `sentinel_exempt`
    marks the one branch the WI-083 phone-sentinel exemption suppresses.

    `regex` is `None` for exactly one record, `empty`, whose refusal is raised
    above the chain by `validate_strict` and `clean` rather than inside
    `_raise_on_tier1`.
    """

    branch_id: str
    pattern: str
    specimen: str
    sentinel_exempt: bool
    regex: Optional[re.Pattern]
    method: str                # "search" | "match" | "empty"
    detail_template: str
    # WI-022: a REAL name of this record's declared type that the branch must
    # NOT fire on. Defaulted so the ten person records keep compiling untouched;
    # the person table is out of the company sweep's scope and keeps the default.
    # A derived sweep proves MEMBERSHIP and never CORRECTNESS — a branch
    # implemented as `return True` refuses every specimen and passes the refusal
    # leg for all of them — so every member of COMPANY_TIER1_BRANCHES carries a
    # non-empty one and the sweep asserts it.
    negative_specimen: str = ""

    def matches(self, name: str) -> bool:
        """Does this branch fire for `name`? The same test the chain applies."""
        if self.regex is None:
            return not name.strip()
        probe = self.regex.search if self.method == "search" else self.regex.match
        return probe(name) is not None

    def detail(self, name: str) -> str:
        return self.detail_template.format(name=name)


TIER1_BRANCHES: tuple = (
    Tier1Branch(
        branch_id="email_chars",
        pattern="contains_email_chars",
        specimen="dave@example.com",
        sentinel_exempt=False,
        regex=_EMAIL_CHARS_RE,
        method="search",
        detail_template=(
            "name contains '@' which cannot appear in a human name: {name!r}"
        ),
    ),
    Tier1Branch(
        branch_id="rfc2822_leak",
        pattern="rfc2822_leak",
        specimen="Naomi Pavie naomipavieatspeechmaticscom",
        sentinel_exempt=False,
        regex=_RFC2822_LEAK_RE,
        method="search",
        detail_template=(
            "name appears to contain an email mashed into text "
            "(TLD-suffix run detected): {name!r}"
        ),
    ),
    Tier1Branch(
        branch_id="arrow_connective",
        pattern="calendar_prefix",
        specimen="Dave -> Thomas Gatten",
        sentinel_exempt=False,
        regex=_ARROW_CONNECTIVE_RE,
        method="search",
        detail_template=(
            "name contains a connective arrow '->' "
            "(meeting/relationship descriptor): {name!r}"
        ),
    ),
    Tier1Branch(
        branch_id="calendar_prefix",
        pattern="calendar_prefix",
        specimen="Dave - Thomas Gatten",
        sentinel_exempt=False,
        regex=_CALENDAR_PREFIX_RE,
        method="match",
        detail_template=(
            "name starts with a calendar-event-title prefix "
            "('Dave -', 'Me -', etc.): {name!r}"
        ),
    ),
    Tier1Branch(
        branch_id="me_to_prefix",
        pattern="calendar_prefix",
        specimen="Me to David Field",
        sentinel_exempt=False,
        regex=_ME_TO_PREFIX_RE,
        method="match",
        detail_template=(
            "name starts with a 'Me to' / 'My to' transcript prefix: {name!r}"
        ),
    ),
    Tier1Branch(
        branch_id="path_hostile",
        pattern="path_hostile_char",
        specimen="Bausch/Lomb",
        sentinel_exempt=False,
        regex=_PATH_HOSTILE_RE,
        method="search",
        detail_template=(
            "name contains '/' which breaks the note file path: {name!r}"
        ),
    ),
    Tier1Branch(
        branch_id="archive_prefix",
        pattern="archive_prefix",
        specimen="zArchived Dave Smith",
        sentinel_exempt=False,
        regex=_ARCHIVE_PREFIX_RE,
        method="match",
        detail_template=(
            "name starts with Obsidian archive convention ('zArchived'): {name!r}"
        ),
    ),
    Tier1Branch(
        branch_id="unknown_contact",
        pattern="unknown_contact",
        specimen="Unknown Contact Zeta-9",
        sentinel_exempt=False,
        regex=_UNKNOWN_CONTACT_RE,
        method="search",
        detail_template=(
            "name contains 'unknown contact' literal "
            "(WhatsApp scanner artifact): {name!r}"
        ),
    ),
    Tier1Branch(
        branch_id="pure_digit",
        pattern="pure_digit_name",
        specimen="447700900123",
        sentinel_exempt=True,
        regex=_PURE_DIGIT_RE,
        method="match",
        detail_template=(
            "name is pure digits (use allow_phone_sentinel=True for "
            "phone-only stubs): {name!r}"
        ),
    ),
    # Raised ABOVE the chain by both public entry points, never inside
    # `_raise_on_tier1`. A member of the table because it is a real refusal the
    # sweep must exercise, and because this item INTRODUCES it on the write path
    # — `create_stub` guards its validator call with `if name and name.strip():`,
    # so `empty` has never fired in production.
    Tier1Branch(
        branch_id="empty",
        pattern="empty",
        specimen="",
        sentinel_exempt=False,
        regex=None,
        method="empty",
        detail_template="name is empty or whitespace-only",
    ),
)

def _empty_branch_of(branches: tuple) -> Tier1Branch:
    """The record in `branches` whose refusal is raised ABOVE the chain.

    DERIVED rather than positional so a second table cannot ship without one: a
    table with no `empty` record would make `validate_strict` silently ACCEPT ""
    for that declared type. That is a loud failure, never a default.
    """
    for branch in branches:
        if branch.regex is None:
            return branch
    raise ValueError(
        "a Tier-1 table must carry an `empty` record (regex=None); this one "
        f"carries none: {[b.branch_id for b in branches]}"
    )


# The one record the chain does not walk, bound so the two entry points that
# raise it can name the table rather than re-spell its key and message. WI-022
# derives it instead of indexing: `empty` is the only regex-`None` record and it
# is last, so this is the SAME OBJECT `TIER1_BRANCHES[-1]` was.
EMPTY_BRANCH: Tier1Branch = _empty_branch_of(TIER1_BRANCHES)


# ============================================================
# The COMPANY Tier-1 surface (WI-022)
# ============================================================

# The filename- and wikilink-hostile characters a COMPANY name may not carry.
# Wider than `_PATH_HOSTILE_RE` (which is `/` alone) because the person side
# survives that under-reach — human names rarely carry `#` or `[` — and company
# names do not. `company.py`'s mangler has been silently ABSORBING this whole
# class, so deleting it un-shields characters nobody has judged: `/` and `\`
# break the note path; `: * ? " < >` are filesystem-hostile; `[ ] | # ^` are
# Obsidian wikilink syntax (link delimiters, alias separator, heading anchor,
# block anchor). Verified 2026-09-06 against 2,159 live company notes: ZERO
# carry any of them — grounded on the character CENSUS
# (docs/company-name-corpus-audit.md §2), which enumerates every character
# present outside [\w\s-] and returns only `&` and `.`, so every member of this
# class is absent by positive measurement. NOT on §1's per-branch row, whose
# printed pattern closes its class early and so measures nothing (§8.6).
_COMPANY_PATH_HOSTILE_RE = re.compile(r'[/\\:*?"<>|\[\]#^]')

# Five records, same `Tier1Branch` type, same field semantics. Membership is
# stated by `branch_id` and NEVER by `pattern` — the two keys diverge and
# `pattern` is not unique.
#
# ORDER IS BEHAVIOUR (the chain raises on the first match) and ONE constraint is
# load-bearing: `arrow_connective` MUST precede `path_hostile`.
# `_COMPANY_PATH_HOSTILE_RE` contains `>`, so `arrow_connective`'s specimen
# "Acme -> Globex" matches `path_hostile` too and raises `calendar_prefix` only
# by tuple position. The branch still earns its place: `_ARROW_CONNECTIVE_RE` is
# `->|[→⟶⇒➜↦⇨]` and the six unicode arrows are all OUTSIDE the widened class, so
# deleting it would stop refusing "Acme → Globex" altogether.
#
# EXCLUDED, by `branch_id`, each for a measured reason (WI-022 D2):
#   `rfc2822_leak`    — its regex matches "wetransfer.com", a real company
#   `calendar_prefix` \
#   `me_to_prefix`     } transcript artifacts of the PERSON ingest path
#   `unknown_contact` /
#   `pure_digit`      — a numeric brand or ticker-styled name is a real company
COMPANY_TIER1_BRANCHES: tuple = (
    Tier1Branch(
        branch_id="email_chars",
        pattern="contains_email_chars",
        specimen="info@acme.com",
        sentinel_exempt=False,
        regex=_EMAIL_CHARS_RE,
        method="search",
        detail_template=(
            "name contains '@' which cannot appear in a company name: {name!r}"
        ),
        negative_specimen="Booking.com",
    ),
    Tier1Branch(
        branch_id="arrow_connective",
        pattern="calendar_prefix",
        specimen="Acme -> Globex",
        sentinel_exempt=False,
        regex=_ARROW_CONNECTIVE_RE,
        method="search",
        detail_template=(
            "name contains a connective arrow '->' "
            "(meeting/relationship descriptor): {name!r}"
        ),
        negative_specimen="Hewlett-Packard",
    ),
    Tier1Branch(
        branch_id="path_hostile",
        # The SAME key the person branch raises, so a consumer routing on
        # `.pattern` sees one key for one class regardless of declared type. The
        # regex differs; the key does not.
        pattern="path_hostile_char",
        specimen="Acme/Corp",
        sentinel_exempt=False,
        regex=_COMPANY_PATH_HOSTILE_RE,
        method="search",
        detail_template=(
            "name contains a character that breaks the note file path or an "
            "Obsidian wikilink: {name!r}"
        ),
        negative_specimen="Smith & Co. (UK)",
    ),
    Tier1Branch(
        branch_id="archive_prefix",
        pattern="archive_prefix",
        specimen="zArchived Acme Corp",
        sentinel_exempt=False,
        regex=_ARCHIVE_PREFIX_RE,
        method="match",
        detail_template=(
            "name starts with Obsidian archive convention ('zArchived'): {name!r}"
        ),
        negative_specimen="Zendesk",
    ),
    # Raised ABOVE the chain by both public entry points, never inside
    # `_raise_on_tier1`, exactly as the person table's `empty` record is — and
    # LAST for the same reason.
    Tier1Branch(
        branch_id="empty",
        pattern="empty",
        specimen="",
        sentinel_exempt=False,
        regex=None,
        method="empty",
        detail_template="name is empty or whitespace-only",
        negative_specimen="Acme Corp",
    ),
)


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


def tier2_repair(name: str) -> CleanResult:
    """THE Tier-2 repair: strip, then collapse internal whitespace.

    Raises nothing and judges nothing. `repairs_applied` carries the same two
    labels it always has: "strip_whitespace", "double_space_collapse".

    Single-homed here (WI-022) so `CompanyRepository.create_stub` — which needs
    the repair WITHOUT a Tier-1 verdict, because its Tier-1 verdict belongs to
    the gate — can reuse it rather than spell `\\s{2,}` a second time. A second
    name authority is the thing this item exists to prevent.
    """
    repairs: List[str] = []
    current = name
    if current != current.strip():
        current = current.strip()
        repairs.append("strip_whitespace")
    if _DOUBLE_SPACE_RE.search(current):
        current = _DOUBLE_SPACE_RE.sub(" ", current)
        repairs.append("double_space_collapse")
    return CleanResult(cleaned_name=current, repairs_applied=repairs,
                       ambiguous=False)


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

    def validate_strict(self, name: str, *, allow_phone_sentinel: bool = False,
                        branches: tuple = TIER1_BRANCHES) -> str:
        """Returns whitespace-normalized name. Raises NameValidationError on
        Tier 1 patterns.

        allow_phone_sentinel: opt-in for WI-083 phone-only stubs where the
        name field is intentionally a "+E164" or "447..." string. Off by
        default to keep producers honest.

        branches: WI-022 — the Tier-1 table to walk. Defaults to the PERSON
        table, so every existing call site keeps its exact behaviour with no
        edit; `name_gate`'s company arm passes `COMPANY_TIER1_BRANCHES`.
        """
        # Phone sentinel: validated as-is when explicitly allowed
        if allow_phone_sentinel and _PURE_DIGIT_RE.match(name.strip()):
            return name.strip()

        # Empty / whitespace
        empty = _empty_branch_of(branches)
        stripped = name.strip()
        if not stripped:
            raise NameValidationError(empty.pattern, empty.detail(name))

        # Tier 1 checks (order matters for clearest error reporting)
        self._raise_on_tier1(stripped, branches=branches)

        # In-band light cleaning: collapse internal whitespace
        cleaned = _DOUBLE_SPACE_RE.sub(" ", stripped)
        return cleaned

    def clean(self, name: str, *, allow_phone_sentinel: bool = False,
              branches: tuple = TIER1_BRANCHES) -> CleanResult:
        """Returns CleanResult. Raises on Tier 1 (the same as validate_strict).

        Tier 2 repairs are applied and recorded in repairs_applied. The
        cleaned_name reflects all applied repairs.
        """
        if allow_phone_sentinel and _PURE_DIGIT_RE.match(name.strip()):
            return CleanResult(cleaned_name=name.strip(), repairs_applied=[], ambiguous=False)

        empty = _empty_branch_of(branches)
        if not name.strip():
            raise NameValidationError(empty.pattern, empty.detail(name))

        # WI-022: Tier 2 computed ONCE, by its one home. Behaviour-identical to
        # the former interleaved form: the chain below still judges
        # `name.strip()`, byte-for-byte the text it judged before, and a
        # whitespace collapse can neither create nor destroy a Tier-1 match —
        # every Tier-1 regex that spans whitespace spans it with `\s+` or `\s*`,
        # which match a single space as readily as a run, and no collapse can
        # join two word characters. So the only difference is the ORDER of two
        # computations whose results are independent.
        repaired = tier2_repair(name)
        self._raise_on_tier1(name.strip(), branches=branches)
        return repaired

    # ----- Tier 1 dispatcher -----

    def _raise_on_tier1(self, name: str, *,
                        branches: tuple = TIER1_BRANCHES) -> None:
        """Walks the Tier 1 pattern table; raises on the first match.

        WI-021: the table is now a real object, `TIER1_BRANCHES`, and this is a
        walk of it rather than a hand-written `if` chain claiming to be one.
        Behaviour is unchanged — same order, same keys, same per-branch match
        method, same messages.

        Order matters: more-specific patterns first so the error reason is
        the most informative one. `@` is a clear smoking gun (always means
        the name carries an email), so it fires before the RFC 2822
        heuristic which would also match an intact "name@domain.com". The
        RFC 2822 branch must match on ORIGINAL casing (see the comment on
        _RFC2822_LEAK_RE) — lowercasing would false-positive on 'Maurizio' /
        'Francisco' / 'Patricio' and other names ending in TLD-substring
        suffixes — which is why nothing here folds case.

        The `empty` record is SKIPPED here: its refusal is raised above this
        method by both public entry points, and moving it into the chain would
        put it below the sentinel exemption.
        """
        for branch in branches:
            if branch.regex is None:
                continue        # `empty` — raised above the chain, never in it
            if branch.matches(name):
                raise NameValidationError(branch.pattern, branch.detail(name))
