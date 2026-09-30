"""The vault's timeline-entry vocabulary — ONE definition, in the library every
writer installs (WI-033).

This module owns the `### {Month D, YYYY} [{kind}]` heading, the
`<!-- {kind}:{YYYY-MM-DD}:{discriminator} -->` machine marker, the kind-slug
rule that decides what a kind IS, the discriminator validation that keeps the
prose channel out of the machine channel, and the two readers that turn vault
bytes back into those parts. It RELOCATES HAL9000's
`backend_fastapi/core/timeline_entry.py` (Design §1): byte-for-byte on what it
RENDERS, no stricter on what it REFUSES beyond the five guards §1.4 enumerates.
The bytes it reproduces are committed as input→output pairs in
`docs/wi-033-hal9000-timeline-entry-capture.md` at `HAL9000_PARITY_ANCHOR`, and
`tests/test_timeline_entry.py` reads both sides out of that file.

**A LEAF.** Its only intra-package import is `errors`, matching
`obsidian_schemas/name_gate.py`'s stated leaf discipline. It must NOT import
`writer`, `parser`, `vault_io`, `models`, `body_sections` or anything under
`repositories/` — the write gate and the door both reach INTO here, never the
other way.

**It reads no clock.** HAL9000's module ships a `_now()` for its HTTP door's
convenience; the library does not relocate it. `when` is always the caller's,
which is what makes every render reproducible and is the property the parity
oracle rests on. A library that read a clock would let a caller mint an entry
whose bytes no test can predict.

**Two channels, and the asymmetry between them is deliberate.** The WRITE door
(`TimelineEntry.__post_init__`) refuses LOUDLY, because a caller can fix its own
input. The READ side (`parse_markers`, `parse_entries`) is total and raises
NOTHING, because it walks thousands of untrusted vault notes and one bad note
must not poison a whole scan; an entry it cannot read is REPORTED by
`scripts/lint_vault.py`'s `intro_by_without_marker` rather than raised on. That
is the one place this module departs from the package's loud-fail idiom, and the
departure is scoped to the reader.
"""

import re
from dataclasses import dataclass
from datetime import date, datetime
from typing import List, NamedTuple, NoReturn, Optional

from .errors import TimelineEntryRefusal

# ---------------------------------------------------------------------------
# §1.1 — One kind grammar, three uses
# ---------------------------------------------------------------------------
#
# The kind slug is written ONCE and the heading and marker patterns are composed
# from it, so the module cannot disagree with itself about what a kind is.

_KIND_BODY = r"[a-z][a-z0-9_-]{0,31}"

#: HAL9000's own rule, verbatim from the capture's part 1 — the OPEN slug rule
#: D8 rules as the write door. A kind that satisfies it constructs and renders
#: whether or not anyone has captured bytes for it; `PARITY_KINDS` below is a
#: parity universe and gates nothing.
KIND_PATTERN = re.compile(rf"^{_KIND_BODY}$")

#: DATE-AGNOSTIC by construction: it captures the date TEXT and never parses it.
#: That is the whole of why the three legacy heading grammars on disk (43
#: `Month D, YYYY`, 38 ISO-with-time, 5 bare ISO) cost this item nothing — the
#: day comes from the marker's own slot, which has exactly one grammar.
HEADING_PATTERN = re.compile(
    rf"^### (?P<date>.+?) \[(?P<kind>{_KIND_BODY})\] *$", re.MULTILINE)

#: `render`'s output read back: `<!-- {key} -->` alone on its line, the
#: discriminator slot non-empty. Line-anchored under `re.MULTILINE`, which is a
#: DECLARED bound rather than an accident — a marker not alone on its line is
#: invisible here, and so is a marker on a CRLF line (`$` matches before `\n`,
#: so a trailing `\r` leaves ` -->$` unmatched). This is identical to the
#: predicate the live census used, so the library's reach EQUALS the measured
#: population by construction.
MARKER_PATTERN = re.compile(
    rf"^<!-- (?P<kind>{_KIND_BODY}):(?P<day>\d{{4}}-\d{{2}}-\d{{2}}):"
    rf"(?P<discriminator>.+) -->$",
    re.MULTILINE)

#: A line-anchored markdown STRUCTURAL line. Exactly TWO readers, and they are
#: deliberately the same constant: §1.4's guard 5 on the write door, and
#: `parse_entries`' body boundary on the read side. Sharing it is the point — the
#: door refuses precisely the line the reader treats as a boundary, so the two
#: cannot drift apart and the module gains no second grammar. Nothing else
#: consults it: not `render`, not `dedupe_key`, not `parse_markers`.
#:
#: Its bound is DERIVED rather than chosen, and the derivation is a STRICT
#: SUPERSET rather than an exact union. `^#{2,3} ` COVERS every line-anchored
#: markdown-heading pattern this module's readers route on —
#: `body_sections.py:SECTION_HEADING_PATTERN`'s `^## (.+)$`, this module's own
#: `HEADING_PATTERN`, and `parse_entries`' body boundary — and it additionally
#: matches two shapes NEITHER reader accepts: a title-less `## ` line and a
#: kind-less `### ` line. Those extra members are INERT and their refusal is
#: harmless; the falsifiable property is COVERAGE — every shape a reader routes
#: on IS refused. The complement is declared with it, because a guard refusing
#: more than its readers route on would be an over-refusal the refusal-parity
#: equality has to carry: `# ` and `#### ` match NONE of the three reader
#: patterns AND none of this one, so neither truncates a span nor forges an
#: entry, and neither is refused.
STRUCTURAL_LINE_PATTERN = re.compile(r"^#{2,3} ", re.MULTILINE)


# ---------------------------------------------------------------------------
# §1.4 — The refusal `pattern` literals
# ---------------------------------------------------------------------------
#
# Module-level literals, following WI-032's precedent exactly
# (`name_gate.py:WHATSAPP_PATTERN`: the door's OWN literal, never a
# `NameValidator` branch record). `pattern` is what distinguishes the faults;
# the `REASONS` reason is per-DOOR and there is exactly one of it.

KIND_PATTERN_KEY: str = "kind_not_a_slug"
TEXT_EMPTY_KEY: str = "text_empty"
TEXT_FORGERY_KEY: str = "text_forges_a_marker"
TEXT_STRUCTURAL_LINE_KEY: str = "text_carries_a_structural_line"
DISCRIMINATOR_TYPE_KEY: str = "discriminator_not_a_string"
DISCRIMINATOR_FORGERY_KEY: str = "discriminator_forges_a_marker"
DISCRIMINATOR_EMPTY_KEY: str = "discriminator_empty"
DISCRIMINATOR_SEPARATOR_KEY: str = "discriminator_carries_the_key_separator"

#: The DOOR's own fault, not a field's: `append_to_timeline` handed BOTH a typed
#: `TimelineEntry` and a `deduplicate_key` (Design §2, branch 1). Declared HERE
#: beside the eight field literals rather than at the door, so every `pattern`
#: this vocabulary can carry has one home and a caller asserting on it imports
#: it from one module.
BOTH_ENTRY_AND_KEY_KEY: str = "both_entry_and_dedupe_key"

#: The ONE enumerated `REASONS` member this door carries, for every guard
#: including guard 5: the reason is per-door, `pattern` is per-fault.
_REFUSAL_REASON: str = "a timeline entry field this package refuses"

#: HAL9000's own two forgery sequences (`core/timeline_entry.py`'s
#: `_COMMENT_DELIMITERS`), verbatim.
_COMMENT_DELIMITERS = ("-->", "<!--")

#: The key's own field separator (see `_compose_key`).
_KEY_SEPARATOR = ":"


def _refuse(pattern_key: str) -> NoReturn:
    """Build and raise this door's refusal. The ONE construction site.

    No note-derived value enters the constructor and none is passed through
    `refused_value` either: at this door the refused value is a person's name or
    a note's prose, which is exactly what `name_gate.py:_refuse`'s rule 2 exists
    to keep out of a refusal. `pattern` is a source literal set as an ATTRIBUTE
    after construction, so it reaches no message and no traceback.
    """
    refusal = TimelineEntryRefusal(_REFUSAL_REASON)
    refusal.pattern = pattern_key
    raise refusal


# ---------------------------------------------------------------------------
# §1.2 — Types
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class TimelineEntry:
    """One timeline event, before it is markdown.

    `when` is ALWAYS the caller's — nothing here reads a clock — so a multi-write
    request can pin one stamp across all of its entries and every render is
    reproducible.

    Validation lives in `__post_init__` (§1.4) and is on CONSTRUCTION only, so it
    is impossible to hold an entry that renders to broken markdown. A `when` that
    is not a `datetime` is deliberately UNGUARDED: it is a required positional
    with no plausible wrong-type caller from data, and a wrong type is a
    programming error that should surface uncaught from `strftime`.
    """

    kind: str
    text: str
    when: datetime
    discriminator: Optional[str] = None

    def __post_init__(self) -> None:
        # HAL9000's rules first, in HAL9000's own order, so the refusal set this
        # door shares with it is reached identically.
        if not isinstance(self.kind, str) or not KIND_PATTERN.match(self.kind):
            _refuse(KIND_PATTERN_KEY)
        if not isinstance(self.text, str) or not self.text.strip():
            _refuse(TEXT_EMPTY_KEY)

        # Guards 1 and 2 — the marker channel. `text` is rendered VERBATIM on its
        # own lines inside the note body, so a delimiter in it is the one place a
        # prose channel can corrupt a machine channel: `-->` terminates the
        # comment the entry's own marker opens, `<!--` forges a second marker.
        # HAL9000 accepts both by design; this is a declared over-refusal.
        for delimiter in _COMMENT_DELIMITERS:
            if delimiter in self.text:
                _refuse(TEXT_FORGERY_KEY)

        # Guard 5 — the SECTION channel (M1). A markdown heading in the prose
        # channel truncates or shadows the `## Timeline` span that the accessor,
        # the marker-anchored dedupe and both new linter detectors all read
        # through, so it would silently hide every older entry on that note from
        # all three. Both effects are SILENT narrowings rather than errors, which
        # is what makes a refusal the right instrument.
        #
        # The line may be the text's FIRST (render puts it immediately after the
        # heading) or follow any `\n` inside it, so the test is the MULTILINE
        # pattern over the whole string and never `text.startswith`.
        if STRUCTURAL_LINE_PATTERN.search(self.text):
            _refuse(TEXT_STRUCTURAL_LINE_KEY)

        if self.discriminator is not None:
            if not isinstance(self.discriminator, str):
                _refuse(DISCRIMINATOR_TYPE_KEY)
            # HAL9000's own discriminator rules: a comment delimiter or a
            # newline, both of which break the single-line comment it lands in.
            for delimiter in _COMMENT_DELIMITERS:
                if delimiter in self.discriminator:
                    _refuse(DISCRIMINATOR_FORGERY_KEY)
            if "\n" in self.discriminator or "\r" in self.discriminator:
                _refuse(DISCRIMINATOR_FORGERY_KEY)

            # Guard 3 — an empty or whitespace-only discriminator renders a
            # marker `MARKER_PATTERN` cannot read (empty) or keys every
            # same-kind, same-day entry onto a blank counterparty (whitespace).
            # Either way the entry is one the accessor cannot honestly answer
            # from. HAL9000 accepts both.
            if not self.discriminator.strip():
                _refuse(DISCRIMINATOR_EMPTY_KEY)

            # Guard 4 — the key separator. `parse_markers` still READS such a
            # marker off disk (the pattern takes the rest of the line), so
            # nothing already written becomes invisible; what is refused is
            # MINTING a new key a consumer splitting on `:` reads as a different
            # kind/day/counterparty triple.
            if _KEY_SEPARATOR in self.discriminator:
                _refuse(DISCRIMINATOR_SEPARATOR_KEY)


class Marker(NamedTuple):
    """One well-formed machine marker, read off a page."""

    kind: str            # the marker's own kind slot
    day: date            # parsed from the day slot
    discriminator: str   # VERBATIM from the discriminator slot
    source: str          # the verbatim marker line, exactly as it appears

    @property
    def key(self) -> str:
        """The bare key this marker embeds, composed through the ONE composer.

        Exists for the READING side, so a round-trip assertion tests the render →
        parse round trip rather than two hand-kept copies of the key grammar
        agreeing with each other.
        """
        return _compose_key(self.kind, self.day, self.discriminator)


class Entry(NamedTuple):
    """One heading-anchored entry, for the reader that needs the HEADING.

    `scripts/lint_vault.py` needs to ask "this heading's entry has no marker"
    without owning a grammar; this is what it asks with. `date_text` is the
    heading's date text UNPARSED — the heading is presentation (D1).
    """

    kind: str                  # the heading's kind slot
    date_text: str             # the heading's date text, UNPARSED
    body: str                  # the heading's own body, to the next structural line
    marker: Optional[Marker]   # the well-formed marker inside that body, or None


@dataclass(frozen=True)
class IntroRecord:
    """"Who introduced this person", as a typed value.

    Lives HERE rather than in `repositories/person.py`, so a consumer imports the
    vocabulary and its record type from ONE module and no second dataclass
    declares the same three fields.

    `source` is the record's PROVENANCE — the verbatim marker string it was read
    from — so a consumer that disagrees with the accessor has the exact substring
    to quote. `introducer` is attacker-influenceable vault prose returned
    VERBATIM: a consumer rendering it into HTML must escape it, and the library
    deliberately does not sanitize on a consumer's behalf.
    """

    introducer: str   # the counterparty, verbatim from the marker's discriminator slot
    date: date        # from the marker's day slot
    source: str       # the verbatim marker string the record was read from


# ---------------------------------------------------------------------------
# §1.3 — Functions, and the bytes
# ---------------------------------------------------------------------------

def _compose_key(kind: str, day: date, discriminator: str) -> str:
    """THE key grammar, spelled in exactly ONE expression.

    Every other route to a key delegates here — `dedupe_key`, `dedupe_probe` and
    `Marker.key` — so no second copy of `{kind}:{day}:{disc}` exists in this
    module, at the door, or in a test. That is not tidiness: the key format
    carries no `<!--`/`-->` delimiter, so a second spelling of it would sit
    OUTSIDE the one-definition scan's predicate by construction and no check in
    this item would catch it. This closes that gap by construction instead.

    The discriminator is carried VERBATIM — no slug, no case-fold, no
    transliteration, HAL9000's own rule, "or `Sören Winter` and `Søren Winter`
    would collide".
    """
    return f"{kind}:{day:%Y-%m-%d}:{discriminator}"


def render(entry: TimelineEntry) -> str:
    """The canonical bytes, and the only place they are composed.

    Exactly `### {when:%B %-d, %Y} [{kind}]\\n{text}\\n<!-- {key} -->\\n`, and
    without a discriminator exactly `### {when:%B %-d, %Y} [{kind}]\\n{text}\\n` —
    the HTML comment is OMITTED, never emitted empty.

    The heading date is composed as `%B` + `.day` + `.year` rather than with
    HAL9000's `strftime('%B %-d, %Y')`. The bytes are IDENTICAL (`%-d` is the
    no-pad day, which is `.day`) and the substitution drops a platform-specific
    `strftime` extension the library would otherwise carry into every consumer.
    `%B` stays, so both sides remain locale-sensitive in exactly the same way: a
    non-English locale moves both identically, which is why pinning a month table
    here would make the library DIFFER from the code it is relocating.
    """
    heading = f"### {entry.when.strftime('%B')} {entry.when.day}, {entry.when.year} [{entry.kind}]\n"
    body = f"{entry.text}\n"
    key = dedupe_key(entry)
    if key is None:
        return heading + body
    return f"{heading}{body}<!-- {key} -->\n"


def dedupe_key(entry: TimelineEntry) -> Optional[str]:
    """The BARE key — what a caller RECORDS.

    `None` when the entry carries no discriminator, which means "NO DEDUPE": a
    free-text note has no event identity to key on, and inventing one would
    silently suppress a second, genuinely intended note with the same words.
    """
    if entry.discriminator is None:
        return None
    return _compose_key(entry.kind, entry.when.date(), entry.discriminator)


def dedupe_probe(entry: TimelineEntry) -> Optional[str]:
    """The DELIMITED form, and the ONE string the door's dedupe test compares.

    Derived from the same `entry` whose comment `render` emits, so a key that is
    passed can never fail to be the key that was embedded. `Marker.source` is the
    verbatim `<!-- {key} -->` line that same `render` emits, which is what makes
    `any(m.source == dedupe_probe(entry) for m in parse_markers(timeline))` an
    equality over one comparand rather than two grammars agreeing.
    """
    key = dedupe_key(entry)
    return None if key is None else f"<!-- {key} -->"


def parse_markers(timeline_text: str) -> List[Marker]:
    """Every well-formed marker in `timeline_text`, in DOCUMENT ORDER.

    Document order is newest-first for stored entries, because
    `PersonRepository.append_to_timeline` PREPENDS despite its name — stored
    ordering is a property every reader of the vault already depends on.

    TOTAL and NON-RAISING over arbitrary vault bytes. A marker whose day slot is
    an impossible date (`2026-13-45`) is a marker this library does not
    recognise; it yields nothing here and is REPORTED by `lint_vault`'s
    `intro_by_without_marker` rather than raised on. `lint_vault` walks thousands
    of files and one hostile note must not poison a whole scan.
    """
    out: List[Marker] = []
    for match in MARKER_PATTERN.finditer(timeline_text):
        try:
            day = date.fromisoformat(match.group("day"))
        except ValueError:
            continue
        out.append(Marker(
            kind=match.group("kind"),
            day=day,
            discriminator=match.group("discriminator"),
            # `m.group(0)` — the marker line WITHOUT its trailing newline, since
            # `$` is zero-width. Pinned byte-for-byte against the marker
            # substring present in the note's own text.
            source=match.group(0),
        ))
    return out


def parse_entries(timeline_text: str) -> List[Entry]:
    """Every heading-anchored entry in `timeline_text`, in document order.

    The body runs from the end of the heading line to the next line matching
    `STRUCTURAL_LINE_PATTERN` — the `^#{2,3} ` written once in §1.1 and SHARED
    with the write door's guard 5, so the "one grammar" claim is literal rather
    than approximate.

    `marker` is the FIRST `Marker` that `parse_markers` returns over that body,
    or `None`. It CALLS `parse_markers` rather than re-matching, so "well-formed"
    is ONE predicate in this module and `intro_by_without_marker` reports exactly
    the entries the accessor cannot see.

    TOTAL and NON-RAISING, for the same reason `parse_markers` is.
    """
    out: List[Entry] = []
    for match in HEADING_PATTERN.finditer(timeline_text):
        boundary = STRUCTURAL_LINE_PATTERN.search(timeline_text, match.end())
        body = timeline_text[match.end():boundary.start() if boundary else len(timeline_text)]
        markers = parse_markers(body)
        out.append(Entry(
            kind=match.group("kind"),
            date_text=match.group("date"),
            body=body,
            marker=markers[0] if markers else None,
        ))
    return out


# ---------------------------------------------------------------------------
# §1.5 — The parity universe and the staleness anchor
# ---------------------------------------------------------------------------

#: The kinds this library holds a COMMITTED BYTE-PARITY SAMPLE for, and nothing
#: else. It GATES NOTHING (D8): no `TimelineEntry` construction, no `render`, no
#: `dedupe_key`, no `dedupe_probe`, no `parse_markers` and no `parse_entries`
#: call reads it. A slug-valid kind absent from it constructs, renders and
#: round-trips — this item RELOCATES the vocabulary and does not tighten it, so a
#: closed enum would make the library STRICTER than the code it is relocating and
#: would lock out any new writer's new kind.
#:
#: Its only readers are the two derived sweeps' FIXTURE SPACES. It is asserted
#: equal to the capture's own sample kinds, which is what keeps that fixture
#: space equal to the population actually on disk rather than to a list a builder
#: chose. Adding a member therefore CLAIMS parity and is legal only when a
#: committed sample exists for it.
PARITY_KINDS = frozenset({"intro", "intro-by", "intro-to", "merge", "note"})

#: The 40-hex HAL9000 HEAD the parity capture froze. A PIN, not a monitor: it
#: detects nothing on its own, and drift in HAL9000's own copy during the window
#: before the cutover (HAL9000 WI-082) is undetected by this tree's hermetic
#: floor — accepted in writing (D7), not mitigated. What it buys is a defined
#: left-hand side: the cutover's first act re-runs the capture at HAL9000's
#: then-HEAD and diffs against this value, so a staleness re-run is one diff
#: rather than a paragraph. Asserted against the capture file rather than trusted.
HAL9000_PARITY_ANCHOR = "d54430da9547a93525c6cc1b20cf781c9a63f82e"

INTRO_BY_KIND = "intro-by"      # WI-077, on the INTRODUCEE's note — the accessor's only source
INTRO_TO_KIND = "intro-to"      # WI-077, the introducer-side mirror of the same event
LEGACY_INTRO_KIND = "intro"     # OUTBOUND; never a source for the accessor (ruling §2)
