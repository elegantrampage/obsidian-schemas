"""WI-033 AC-1 — the relocated vocabulary reproduces HAL9000's bytes and is no
stricter than HAL9000's door, proved against a COMMITTED EXTERNAL ORACLE.

Two checks: AC-1's capture-driven battery (Tasks 3 and 4), and the
wall-membership RUN over every file this item creates or edits (Task 11).

**Why the oracle is a file and not a literal.** "The module renders correctly" is
not the claim; BYTE PARITY with HAL9000 is. A hermetic suite comparing the module
against a literal a builder typed from the same reading of the same code would
stay green whichever way the reading went wrong, so BOTH sides — the inputs AND
the expected bytes — are read out of
`docs/wi-033-hal9000-timeline-entry-capture.md`, which the conductor produced by
RUNNING HAL9000's code. No literal from that file is re-typed here.

CORPUS_COUPLING: this module reads `docs/wi-033-hal9000-timeline-entry-capture.md`
at run time. It pins TWO heading names (`## Parity samples`, `## Validation
boundary`), the FIVE declared keys of each sample fence (`kind`, `text`, `when`,
`discriminator`, `rendered`) and the THREE of each probe fence (`field`, `value`,
`verdict`), and it consumes the property that every `rendered` block and every
`verdict` was produced by running HAL9000's code at the 40-hex HEAD the file
declares (asserted equal to `HAL9000_PARITY_ANCHOR`). It pins no count, no wrap,
no heading total and no section position: a regenerated capture may hold any
number of samples and probes. What it DOES require of the capture is that each
named heading occur exactly once at line start and that every `yaml` fence in the
file sit inside one of those two sections — the whole-file accounting below,
which is what makes a silently TRUNCATED span RED rather than green over a
narrowed population (Design §12 Rule 3).
"""

# FIRST, ahead of every package import: the conveyor may run this module's checks
# under an interpreter that is not this project's, where the imports below cannot
# resolve. A no-op under the floor command and under CI.
from tests.ac_interpreter import ensure_project_interpreter

ensure_project_interpreter(__file__)

import fnmatch  # noqa: E402 — everything below runs only once the interpreter is right
import re  # noqa: E402
from datetime import date, datetime  # noqa: E402
from pathlib import Path  # noqa: E402

import yaml  # noqa: E402

from obsidian_schemas.body_sections import get_section  # noqa: E402
from obsidian_schemas.errors import TimelineEntryRefusal  # noqa: E402
from obsidian_schemas.repositories import PersonRepository  # noqa: E402
from obsidian_schemas.timeline_entry import (  # noqa: E402
    BOTH_ENTRY_AND_KEY_KEY,
    DISCRIMINATOR_EMPTY_KEY,
    DISCRIMINATOR_FORGERY_KEY,
    DISCRIMINATOR_SEPARATOR_KEY,
    DISCRIMINATOR_TYPE_KEY,
    HAL9000_PARITY_ANCHOR,
    KIND_PATTERN_KEY,
    PARITY_KINDS,
    STRUCTURAL_LINE_PATTERN,
    TEXT_EMPTY_KEY,
    TEXT_FORGERY_KEY,
    TEXT_STRUCTURAL_LINE_KEY,
    TimelineEntry,
    dedupe_key,
    dedupe_probe,
    parse_entries,
    parse_markers,
    render,
)
from tests.derivations import (  # noqa: E402
    PACKAGE_ROOT,
    SCRIPTS_ROOT,
    TESTS_ROOT,
    select_fenced_blocks,
    select_sections,
)
from tests.support import temp_dir  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
CAPTURE = REPO_ROOT / "docs" / "wi-033-hal9000-timeline-entry-capture.md"

SAMPLES_HEADING = "## Parity samples"
BOUNDARY_HEADING = "## Validation boundary"

#: The 40-hex matcher shape `tests/test_lint_vault_fix_rules.py:_HEX40:1515`
#: already carries — non-hex boundaries on both sides, so a longer hex run is not
#: silently truncated into a false HEAD.
_HEX40 = re.compile(r"(?<![0-9a-fA-F])[0-9a-f]{40}(?![0-9a-fA-F])")

#: The capture's own probe baseline, declared at
#: `docs/wi-033-hal9000-timeline-entry-capture.md`'s "Machine-readable shape":
#: each verdict is whether HAL9000's constructor raised with the OTHER fields
#: held here. Transcribed once so a probe can be reconstituted as a full
#: constructor call; it is not an oracle and nothing below asserts on it.
_PROBE_BASELINE = {"kind": "note", "text": "probe", "discriminator": None}

#: A slug-valid kind absent from `PARITY_KINDS` — the DISCRIMINATING MEMBER that
#: tells an open slug door from a closed enum. Planted rather than sampled
#: because the frozen corpus holds zero timeline entries and so can supply a
#: second kind no more than a second person.
PLANTED_KIND = "deal-closed"


# --------------------------------------------------------------------------
# Capture parsing — one place, so every clause reads the same bytes
# --------------------------------------------------------------------------

def _yaml_fences(section_text):
    """Every `yaml`-info fenced block of one text, `yaml.safe_load`ed.

    The info-string filter is the whole reason `select_fenced_blocks` retains it:
    the capture's four `python` fences must not be handed to `safe_load`, and the
    accounting below cannot be expressed without the discrimination.

    **The `+ "\\n"` is load-bearing and is not a convenience.** A fenced block in
    a markdown file always ends with a line break before its closing delimiter,
    and the walk's `"\\n".join` — the shipped shape's, faithfully copied — drops
    it. YAML's `|` literal block scalar CLIPS to whatever the input ends with, so
    without the restoration every `rendered` scalar loses its final newline and
    every parity comparison is off by exactly that byte. The capture says in its
    own words that this newline "is the renderer's own", so dropping it would make
    AC-1(a) assert against bytes HAL9000 never emitted.
    """
    return [yaml.safe_load(block + "\n")
            for info, block in select_fenced_blocks(section_text)
            if info == "yaml"]


def _yaml_fence_count(text):
    return len([1 for info, _block in select_fenced_blocks(text) if info == "yaml"])


def _probe_key(probe):
    """A probe's hashable identity. `value` is a `str` or `None`, both hashable,
    so the SET operations AC-1(c2) is expressed in need no second representation."""
    return (probe["field"], probe["value"])


def _library_refuses(probe):
    """Does THIS library's write door refuse the probe's value?

    The other two fields are held at the capture's own declared baseline, so the
    verdict compared is about the one field the probe is about.
    """
    fields = dict(_PROBE_BASELINE)
    fields[probe["field"]] = probe["value"]
    try:
        TimelineEntry(kind=fields["kind"], text=fields["text"],
                      when=datetime(2026, 1, 1),
                      discriminator=fields["discriminator"])
    except TimelineEntryRefusal:
        return True
    return False


def _guarded(probe):
    """Is the probe a member of this document's DECLARED guard set (§1.4)?

    FIVE predicates, derived from the document's own guard list rather than a
    typed list of probe values — which is what makes AC-1(c2) survive a
    regenerated capture that probes more boundary values. A sixth guard added
    later against a capture that DOES probe its shape shows up on both sides; a
    four-predicate filter would hide it.
    """
    field, value = probe["field"], probe["value"]
    if field == "text" and isinstance(value, str):
        if "-->" in value:                                   # guard 1
            return True
        if "<!--" in value:                                  # guard 2
            return True
        if STRUCTURAL_LINE_PATTERN.search(value):            # guard 5 (M1)
            return True
    if field == "discriminator" and isinstance(value, str):
        if not value.strip():                                # guard 3
            return True
        if ":" in value:                                     # guard 4
            return True
    return False


def _entry(kind, day=date(2026, 9, 27), discriminator="Counterparty"):
    return TimelineEntry(kind=kind, text=f"an entry of kind {kind}",
                         when=datetime(day.year, day.month, day.day, 12, 0, 0),
                         discriminator=discriminator)


def _person_note(stem, timeline_body="", extra_sections=""):
    return (f"---\ntype: person\nname: \"{stem.lstrip('@')}\"\n---\n\n"
            f"## Timeline\n{timeline_body}\n{extra_sections}")


# ==========================================================================
# AC-1 — the capture-driven battery (Tasks 3 and 4)
# ==========================================================================

def test_timeline_entry_reproduces_hal9000_render_and_validation_boundary():
    """AC-1's verify. Zero-arg and raising, per the check contract."""
    # The two derivations' own REACH first: both of this item's markdown oracles
    # turned on a selector's and a matcher's reach over a file nobody had read at
    # the granularity the oracle consumes, and "it parses the capture" is
    # satisfied identically by a selector honouring every rule below and by one
    # honouring almost none (WI-235).
    _check_select_sections_reaches_every_claimed_shape()
    _check_select_fenced_blocks_reaches_every_claimed_shape()

    text = CAPTURE.read_text(encoding="utf-8")
    sections = select_sections(text, [SAMPLES_HEADING, BOUNDARY_HEADING])

    # COMPLETENESS FIRST (§12 Rule 3, M2), before any sample or probe is read.
    _check_the_capture_spans_are_complete(text, sections)

    samples = _yaml_fences(sections[SAMPLES_HEADING])
    probes = _yaml_fences(sections[BOUNDARY_HEADING])

    # THEN non-vacuity: a fence reader that finds nothing is otherwise GREEN.
    _check_the_capture_is_non_vacuous(samples, probes)

    _check_render_is_byte_identical_to_every_sample(samples)          # (a)
    _check_parity_kinds_equals_the_captured_population(samples)       # (a2)
    _check_the_staleness_anchor_is_machine_checked(text)              # (a3)
    _check_the_kind_door_is_open(samples)                            # (a4)
    _check_every_kind_round_trips(samples)                           # (b)
    _check_each_declared_guard_raises_its_named_pattern()            # (c)
    _check_the_library_is_no_stricter_than_the_capture(probes)       # (c2)
    _check_guard_five_reaches_every_claimed_shape(probes)            # (c3)

    # Task 4 — the door. Its three clauses need a vault, so each takes its own.
    with temp_dir() as root:
        _check_the_door_cannot_disagree_with_itself(root)            # (d)
    with temp_dir() as root:
        _check_dedupe_is_anchored_to_the_timeline_span(root)         # (e)
    with temp_dir() as root:
        _check_placement_and_the_string_signature_are_unchanged(root)  # (f)


# --------------------------------------------------------------------------
# §12 Rule 3 — the whole-file accounting, and non-vacuity
# --------------------------------------------------------------------------

def _check_the_capture_spans_are_complete(text, sections):
    """A truncated selection is RED rather than green over a narrowed population.

    §12 Rule 1's boundary is deliberately fence-UNAWARE, so a line-start `## `
    introduced inside a fenced block would end a selected span early. For three
    of this item's four selected spans an existing assertion already fails on
    that; for `## Validation boundary` it does NOT — AC-1(c2)'s set equality
    holds over any SUBSET of the `accept` probes, so a partial truncation would
    silently retire the anti-widening ratchet while the floor stayed green. This
    is what closes it, over BOTH capture spans in one expression.

    NO literal count is typed and no occurrence figure is pinned: the cutover
    re-runs the capture and may legitimately probe more boundary values, and both
    sides of the accounting move together.
    """
    in_samples = _yaml_fence_count(sections[SAMPLES_HEADING])
    in_boundary = _yaml_fence_count(sections[BOUNDARY_HEADING])
    in_file = _yaml_fence_count(text)

    assert in_samples > 0, f"{SAMPLES_HEADING} holds no `yaml` fence"
    assert in_boundary > 0, f"{BOUNDARY_HEADING} holds no `yaml` fence"
    assert in_file > 0, "the capture holds no `yaml` fence at all"
    assert in_samples + in_boundary == in_file, (
        f"the capture's `yaml` fences do not all sit inside the two selected "
        f"sections: {in_samples} in {SAMPLES_HEADING!r} + {in_boundary} in "
        f"{BOUNDARY_HEADING!r} != {in_file} in the file. Either a span was "
        f"TRUNCATED by a line-start `## ` inside a fence, or the capture parks a "
        f"`yaml` fence in a third section — both of which would leave an oracle "
        f"answering over a narrowed population")


def _check_the_capture_is_non_vacuous(samples, probes):
    assert samples, "the capture declares no parity sample"
    assert probes, "the capture declares no validation probe"
    for sample in samples:
        assert set(sample) == {"kind", "text", "when", "discriminator", "rendered"}, (
            f"a sample fence declares {sorted(sample)} rather than the five "
            f"declared keys")
    for probe in probes:
        assert set(probe) == {"field", "value", "verdict"}, (
            f"a probe fence declares {sorted(probe)} rather than the three "
            f"declared keys")
        assert probe["field"] in ("kind", "text", "discriminator")
    verdicts = {probe["verdict"] for probe in probes}
    assert verdicts == {"accept", "refuse"}, (
        f"the probes carry {sorted(verdicts)}; a capture recording one verdict "
        f"only cannot pin a boundary")


# --------------------------------------------------------------------------
# (a) / (a2) / (a3) / (a4) / (b)
# --------------------------------------------------------------------------

def _check_render_is_byte_identical_to_every_sample(samples):
    """AC-1(a). Inputs AND expected output both read from the file."""
    for sample in samples:
        entry = TimelineEntry(
            kind=sample["kind"],
            text=sample["text"],
            when=datetime.fromisoformat(sample["when"]),
            discriminator=sample["discriminator"],
        )
        produced = render(entry)
        assert produced == sample["rendered"], (
            f"render is not byte-identical to HAL9000's for kind "
            f"{sample['kind']!r}:\n  library: {produced!r}\n  captured: "
            f"{sample['rendered']!r}")


def _check_parity_kinds_equals_the_captured_population(samples):
    """AC-1(a2), with R2's right-hand side: the SAMPLES' kinds and nothing else.

    `## Validation boundary` deliberately probes a slug-valid kind no sample
    renders, which must NOT be in `PARITY_KINDS` or this clause's own "a member
    with no sample is RED" half fires.

    What the equality buys, stated so nobody reads it as enforcement: it GATES
    NOTHING. It pins the FIXTURE SPACE of two derived sweeps to the population
    that actually exists, so a member with no captured bytes cannot be
    round-tripped self-consistently and an on-disk kind cannot be swept by
    nothing at all.
    """
    assert PARITY_KINDS == {sample["kind"] for sample in samples}, (
        f"PARITY_KINDS is {sorted(PARITY_KINDS)} and the capture's samples hold "
        f"{sorted({s['kind'] for s in samples})}")


def _check_the_staleness_anchor_is_machine_checked(text):
    """AC-1(a3), with §12 dimension (v)'s derivation: the SET, not the first match.

    The capture declares the same HEAD four times today. "The first match" would
    be GREEN against a capture that declared two DIFFERENT HEADs, which is the
    one thing an anchor must not be. No occurrence count is pinned — a re-run
    capture legitimately moves it.
    """
    heads = set(_HEX40.findall(text))
    assert len(heads) == 1, (
        f"the capture declares {len(heads)} distinct 40-hex tokens "
        f"({sorted(heads)}); an anchor with two candidate values pins nothing")
    assert HAL9000_PARITY_ANCHOR == next(iter(heads))


def _check_the_kind_door_is_open(samples):
    """AC-1(a4). The discriminating member is PLANTED, and its round trip is the
    discriminant — a build that closed the door over `PARITY_KINDS` is RED here
    and green on every other clause of this criterion."""
    assert PLANTED_KIND not in PARITY_KINDS, (
        "the planted kind must be ABSENT from the parity universe or it "
        "discriminates nothing")
    assert PLANTED_KIND not in {sample["kind"] for sample in samples}

    entry = _entry(PLANTED_KIND)
    produced = render(entry)
    assert f"[{PLANTED_KIND}]" in produced
    markers = parse_markers(produced)
    assert len(markers) == 1 and markers[0].kind == PLANTED_KIND
    assert dedupe_key(entry) == markers[0].key
    assert parse_entries(produced)[0].kind == PLANTED_KIND


def _check_every_kind_round_trips(samples):
    """AC-1(b). The fixture space is `PARITY_KINDS` ITERATED — never a hand list
    — plus (a4)'s planted out-of-table kind."""
    assert PARITY_KINDS, "the iterated fixture space is empty"
    for kind in sorted(PARITY_KINDS) + [PLANTED_KIND]:
        entry = _entry(kind, day=date(2025, 11, 10), discriminator="Tamsin Okoro-Vale")
        markers = parse_markers(render(entry))
        assert len(markers) == 1, f"kind {kind!r} round-tripped {len(markers)} markers"
        marker = markers[0]
        assert marker.kind == entry.kind
        assert marker.day == entry.when.date()
        assert marker.discriminator == entry.discriminator
        # Both sides compose through `_compose_key`, so this tests the RENDER ->
        # PARSE round trip rather than two hand-kept copies of the key grammar
        # agreeing with each other.
        assert dedupe_key(entry) == marker.key
        # The ONE string the door's dedupe test compares, pinned here rather
        # than only described in prose.
        assert marker.source == dedupe_probe(entry)


# --------------------------------------------------------------------------
# (c) / (c2) / (c3) — the refusal surface
# --------------------------------------------------------------------------

def _refusal_pattern(**fields):
    payload = dict(_PROBE_BASELINE)
    payload.update(fields)
    try:
        TimelineEntry(kind=payload["kind"], text=payload["text"],
                      when=datetime(2026, 1, 1),
                      discriminator=payload["discriminator"])
    except TimelineEntryRefusal as refusal:
        return refusal.pattern
    raise AssertionError(f"the door accepted {fields!r}")


def _check_each_declared_guard_raises_its_named_pattern():
    """AC-1(c). Each of the five guards, plus the four HAL9000 rules the door
    relocates, named by the LEAF and its `pattern` — never by the root, because
    sibling leaves raise from the same frames."""
    # The five library guards.
    assert _refusal_pattern(text="see --> here") == TEXT_FORGERY_KEY
    assert _refusal_pattern(text="<!-- forged") == TEXT_FORGERY_KEY
    assert _refusal_pattern(discriminator="") == DISCRIMINATOR_EMPTY_KEY
    assert _refusal_pattern(discriminator="   ") == DISCRIMINATOR_EMPTY_KEY
    assert _refusal_pattern(discriminator="a:b") == DISCRIMINATOR_SEPARATOR_KEY
    assert _refusal_pattern(text="## Notes") == TEXT_STRUCTURAL_LINE_KEY

    # HAL9000's own rules, relocated: these are PARITY and not tightening.
    assert _refusal_pattern(kind="Note") == KIND_PATTERN_KEY
    assert _refusal_pattern(kind=None) == KIND_PATTERN_KEY
    assert _refusal_pattern(text="") == TEXT_EMPTY_KEY
    assert _refusal_pattern(text=None) == TEXT_EMPTY_KEY
    assert _refusal_pattern(discriminator=7) == DISCRIMINATOR_TYPE_KEY
    assert _refusal_pattern(discriminator="x-->y") == DISCRIMINATOR_FORGERY_KEY
    assert _refusal_pattern(discriminator="a\nb") == DISCRIMINATOR_FORGERY_KEY


def _check_the_library_is_no_stricter_than_the_capture(probes):
    """AC-1(c2) in R1's reified form: BOTH sides derived from the capture.

    Read literally the signed clause cannot hold — the `-->`/`<!--` guard is
    HAL9000's own for the `kind` and `discriminator` fields, so those probes sit
    on the capture's REFUSE side and cannot appear in "capture-ACCEPTED". The
    operative form asserts what can actually break a post-cutover caller: the set
    of capture-ACCEPTED inputs the library refuses EQUALS the set of
    capture-ACCEPTED inputs matching this document's five guard predicates.

    The LOOSE direction — the library accepting something HAL9000 refuses — is
    asserted NOT AT ALL and is out of scope in writing: it cannot break a caller
    that works today, the library's own guards are pinned independently by (c),
    and validating on HAL9000's behalf is the cutover item's business.
    """
    accepted = [probe for probe in probes if probe["verdict"] == "accept"]
    assert accepted, "the capture records no ACCEPTED probe"

    refused_by_library = {_probe_key(p) for p in accepted if _library_refuses(p)}
    declared_guards = {_probe_key(p) for p in accepted if _guarded(p)}

    assert declared_guards, (
        "no capture-accepted probe matches any declared guard predicate — the "
        "equality below would be a pair of empty sets, which pins nothing")
    assert refused_by_library == declared_guards, (
        f"the library's over-refusals are not exactly its declared guard set. "
        f"Refused but not guarded (a NEW over-refusal that would break a "
        f"post-cutover HAL9000 caller): "
        f"{sorted(refused_by_library - declared_guards)}. Guarded but not "
        f"refused (a guard this document claims and the build does not have): "
        f"{sorted(declared_guards - refused_by_library)}")

    # The positive half of the same statement, said in its own terms: every
    # capture-accepted probe OUTSIDE the guard set constructs.
    for probe in accepted:
        if _probe_key(probe) in declared_guards:
            continue
        assert not _library_refuses(probe), (
            f"the library refuses {probe['field']}={probe['value']!r}, which "
            f"HAL9000 accepts and no guard claims")


def _check_guard_five_reaches_every_claimed_shape(probes):
    """AC-1(c3) / M1 (WI-235). A refusal COUNT is satisfied identically by a
    predicate reaching every claimed heading shape and by one reaching almost
    none, so every CLAIMED shape and every near-miss is driven through the
    module's own construction — and then the CONSEQUENCE the guard exists to
    prevent is asserted rather than argued."""
    # The claimed shapes.
    for claimed in ("## Notes",                       # the text's FIRST line
                    "ok\n## Notes",                   # its SECOND — the `startswith` discriminant
                    "## Timeline",                    # the SHADOWING case
                    "### November 10, 2025 [intro-by]"):   # a forged entry heading
        assert _refusal_pattern(text=claimed) == TEXT_STRUCTURAL_LINE_KEY, (
            f"guard 5 does not reach the claimed shape {claimed!r}")

    # The near-misses the predicate must NOT match: each CONSTRUCTS and renders.
    near_misses = ["# h1", "#### h4", "see # here", "  ## x"]
    # Plus the capture's OWN multi-line accept probe, read from the file rather
    # than re-typed — the direct proof that (c2)'s equality is unmoved by M1.
    multiline = [p["value"] for p in probes
                 if p["field"] == "text" and p["verdict"] == "accept"
                 and isinstance(p["value"], str) and "\n" in p["value"]]
    assert multiline, (
        "the capture records no multi-line ACCEPTED `text` probe; without one, "
        "guard 5's harmlessness to the equality is unproven rather than proven")
    for value in near_misses + multiline:
        entry = TimelineEntry(kind="note", text=value, when=datetime(2026, 1, 1),
                             discriminator="X")
        assert value in render(entry)

    # THE CONSEQUENCE, built WITHOUT the door so the guard cannot suppress its
    # own demonstration. The oracle is a value this test computes (WI-149), never
    # a literal count.
    older = render(_entry("intro-by", day=date(2025, 1, 1), discriminator="Older"))
    newer = render(_entry("intro-by", day=date(2026, 1, 1), discriminator="Newer"))
    body = f"## Timeline\n\n{newer}\n{older}\n\n## Notes\n\nprose.\n"
    intact = len(parse_markers(get_section(body, "Timeline") or ""))
    assert intact == 2, f"the intact fixture holds {intact} markers, not two"

    for spliced_line in ("## Notes", "## Timeline"):
        spliced = body.replace(f"\n{older}", f"\n{spliced_line}\n{older}", 1)
        after = len(parse_markers(get_section(spliced, "Timeline") or ""))
        assert after < intact, (
            f"splicing {spliced_line!r} between two entries left {after} markers "
            f"visible, not fewer than {intact} — the span loss guard 5 exists to "
            f"prevent is not demonstrated, so a build that dropped the guard "
            f"would be RED only on a missing raise")


# --------------------------------------------------------------------------
# Task 4 — the door's three clauses
# --------------------------------------------------------------------------

def _check_the_door_cannot_disagree_with_itself(root):
    """AC-1(d). The typed path derives BOTH the written entry and the dedupe key
    from one object, so the key and the marker are the same string by
    construction."""
    vault = Path(root) / "vault"
    vault.mkdir()
    (vault / "@Alma Ostrivane.md").write_text(
        _person_note("@Alma Ostrivane"), encoding="utf-8")
    repo = PersonRepository(vault)
    person = repo.get("Alma Ostrivane")

    entry = _entry("intro-by", day=date(2026, 9, 27), discriminator="Sören Wexley")
    assert repo.append_to_timeline(person, entry) is True
    assert repo.append_to_timeline(person, entry) is False, (
        "the same entry twice must write once and return the deliberate dedupe "
        "False")

    text = (vault / "@Alma Ostrivane.md").read_text(encoding="utf-8")
    assert text.count(dedupe_probe(entry)) == 1

    # A typed entry AND a dedupe key is a caller asking the door to disagree
    # with itself: refused rather than silently preferring one.
    try:
        repo.append_to_timeline(person, entry, deduplicate_key="anything")
    except TimelineEntryRefusal as refusal:
        assert refusal.pattern == BOTH_ENTRY_AND_KEY_KEY
    else:
        raise AssertionError("the door accepted both an entry and a dedupe key")

    # A discriminator-less entry has NO event identity, so two identical `note`
    # entries legitimately write twice (the capture's own rule).
    free_text = TimelineEntry(kind="note", text="Mentioned the Lisbon offsite.",
                              when=datetime(2026, 12, 25, 23, 59, 59))
    assert dedupe_key(free_text) is None
    assert repo.append_to_timeline(person, free_text) is True
    assert repo.append_to_timeline(person, free_text) is True
    after = (vault / "@Alma Ostrivane.md").read_text(encoding="utf-8")
    assert after.count("Mentioned the Lisbon offsite.") == 2


def _check_dedupe_is_anchored_to_the_timeline_span(root):
    """AC-1(e). The typed path matches the MARKER FORM inside `## Timeline` only,
    which is the P2 defect closed at the door rather than documented: today's
    check is a substring test over the WHOLE file including frontmatter, so a
    `## Notes` line quoting a key silently suppresses a real entry."""
    vault = Path(root) / "vault"
    vault.mkdir()
    entry = _entry("intro-by", day=date(2026, 3, 4), discriminator="Tamsin Okoro-Vale")
    quoting = f"## Notes\n\nSomeone pasted {dedupe_probe(entry)} in here.\n"
    path = vault / "@Brannock Sennaby.md"
    path.write_text(_person_note("@Brannock Sennaby", extra_sections=quoting),
                    encoding="utf-8")

    repo = PersonRepository(vault)
    person = repo.get("Brannock Sennaby")
    assert repo.append_to_timeline(person, entry) is True, (
        "a `## Notes` line quoting the key verbatim must NOT dedupe the entry "
        "away — the anchored test reads the `## Timeline` span only")

    text = path.read_text(encoding="utf-8")
    assert len(parse_markers(get_section(text, "Timeline") or "")) == 1

    # A quoted key INSIDE the span that is not a well-formed marker LINE does not
    # match either — the test is a marker equality, not a substring test.
    other = _entry("intro-by", day=date(2026, 5, 6), discriminator="Perrowin Quillam")
    inline = vault / "@Caldreth Ashquill.md"
    inline.write_text(
        _person_note("@Caldreth Ashquill",
                     timeline_body=f"\nprose mentioning {dedupe_probe(other)} inline\n"),
        encoding="utf-8")
    repo2 = PersonRepository(vault)
    assert repo2.append_to_timeline(repo2.get("Caldreth Ashquill"), other) is True


def _check_placement_and_the_string_signature_are_unchanged(root):
    """AC-1(f). The typed path PREPENDS inside `## Timeline` exactly as the string
    path does today, and the existing string-and-key signature keeps working
    unchanged — including its whole-file substring dedupe, which a live caller
    depends on."""
    vault = Path(root) / "vault"
    vault.mkdir()
    path = vault / "@Dalquest Nimbrook.md"
    path.write_text(_person_note("@Dalquest Nimbrook"), encoding="utf-8")
    repo = PersonRepository(vault)
    person = repo.get("Dalquest Nimbrook")

    first = _entry("intro-by", day=date(2025, 1, 1), discriminator="First")
    second = _entry("intro-by", day=date(2026, 1, 1), discriminator="Second")
    assert repo.append_to_timeline(person, first) is True
    assert repo.append_to_timeline(person, second) is True

    span = get_section(path.read_text(encoding="utf-8"), "Timeline") or ""
    order = [marker.discriminator for marker in parse_markers(span)]
    assert order == ["Second", "First"], (
        f"stored order is newest-first because the door PREPENDS; got {order}")

    # The string branch, byte-for-byte today's behaviour including the whole-file
    # substring dedupe.
    assert repo.append_to_timeline(person, "\n### Hand-written\nA raw entry.\n",
                                   deduplicate_key="A raw entry.") is True
    assert repo.append_to_timeline(person, "\n### Hand-written\nA raw entry.\n",
                                   deduplicate_key="A raw entry.") is False

    # A note with NO `## Timeline` section: the shipped accommodation creates it
    # at end of file and the typed entry lands (first-run vs subsequent-run).
    bare = vault / "@Elowick Ferrigan.md"
    bare.write_text("---\ntype: person\nname: \"Elowick Ferrigan\"\n---\n\nPreamble.\n",
                    encoding="utf-8")
    repo3 = PersonRepository(vault)
    before = bare.read_text(encoding="utf-8")
    assert repo3.append_to_timeline(repo3.get("Elowick Ferrigan"), first) is True
    grown = bare.read_text(encoding="utf-8")
    assert grown.startswith(before), (
        "the no-`## Timeline` accommodation must PRESERVE every pre-existing "
        "byte — it is a string insertion at end of file and never a "
        "parse_body_sections round trip")
    assert len(parse_markers(get_section(grown, "Timeline") or "")) == 1


# --------------------------------------------------------------------------
# The two derivations' WI-235 batteries — driven through the derivation ITSELF
# --------------------------------------------------------------------------

def _check_select_sections_reaches_every_claimed_shape():
    """Every shape §12 Rule 1 CLAIMS, plus the near-misses it must not match,
    driven through `select_sections` itself rather than a re-implementation."""
    text = "\n".join([
        "preamble",
        "## Part 1 — source",              # NOT named: ignored as a candidate,
        "part one body",                   #            HONOURED as a boundary
        "## Parity samples",
        "sample body",
        "### Foo",                         # near-miss: neither candidate nor boundary
        "  ## Indented",                   # near-miss: neither
        "## Validation boundary",
        "probe body",
        "## Part 1 — source",              # a duplicate of an UNNAMED heading
        "the echo's body",
    ])
    got = select_sections(text, ["## Parity samples", "## Validation boundary"])

    # A named heading selected; the span stops at the next `## ` WHATEVER it is.
    assert got["## Parity samples"] == "sample body\n### Foo\n  ## Indented"
    # A named heading whose span runs to END OF FILE.
    assert got["## Validation boundary"] == "probe body"

    # A named heading whose span runs to EOF with nothing after it.
    eof = select_sections("## Only\nbody\nmore", ["## Only"])
    assert eof["## Only"] == "body\nmore"

    # Whole-line equality, not prefix — the one place this deliberately differs
    # from `baseline_sections`, which matches by prefix.
    _assert_raises_selection("## Foo bar\nbody", ["## Foo"])
    # Neither near-miss is a selection CANDIDATE for the name `## Foo` (their
    # non-candidacy as BOUNDARIES is asserted by the mixed text above, where both
    # sit INSIDE the selected span).
    _assert_raises_selection("### Foo\nbody", ["## Foo"])
    _assert_raises_selection("  ## Foo\nbody", ["## Foo"])
    # The RAISING discipline, in BOTH directions.
    _assert_raises_selection("## Other\nbody", ["## Parity samples"])
    _assert_raises_selection("## Dup\na\n## Dup\nb", ["## Dup"])


def _assert_raises_selection(text, names):
    try:
        select_sections(text, names)
    except AssertionError:
        return
    raise AssertionError(
        f"select_sections({names!r}) did not raise over {text!r}; a selector "
        f"that finds none or two must be RED, never return an empty dict")


def _check_select_fenced_blocks_reaches_every_claimed_shape():
    """The INFO STRING is the whole reason this helper deviates from the shipped
    `fenced_blocks:1550`, which DISCARDS it — so the discrimination is asserted
    rather than assumed. §12 Rule 3's accounting is a `yaml`-versus-`python`
    count and says nothing about whether that discrimination works."""
    mixed = "\n".join([
        "```yaml",
        "a: 1",
        "```",
        "prose",
        "```python",
        "x = 1",
        "```",
    ])
    pairs = select_fenced_blocks(mixed)
    assert [info for info, _ in pairs] == ["yaml", "python"]
    assert [block for _, block in pairs] == ["a: 1", "x = 1"]
    for _info, block in pairs:
        assert "```" not in block, "a delimiter line leaked into a block body"

    # A fence opened with NO info string.
    assert select_fenced_blocks("```\nbare\n```") == [("", "bare")]

    # Two consecutive fences, in order.
    assert select_fenced_blocks("```a\n1\n```\n```b\n2\n```") == [("a", "1"), ("b", "2")]

    # The NEAR-MISS: an INDENTED triple-backtick is not a delimiter, because the
    # toggle is `line.startswith` and never `line.strip().startswith`. Asserted
    # by the block count it does not change.
    indented = "```yaml\na: 1\n  ```\nb: 2\n```"
    assert select_fenced_blocks(indented) == [("yaml", "a: 1\n  ```\nb: 2")]


# ==========================================================================
# Task 11 — the wall memberships, closed by RUNNING each predicate
# ==========================================================================

def _touched_files():
    """Every file this item creates or edits that a source-reading wall can see.

    Derived from `## Write Targets`' builder paths, which is the list the merge
    boundary itself grades — so a path added there and not here is a divergence a
    reader can spot in one diff.
    """
    return [
        PACKAGE_ROOT / "timeline_entry.py",
        PACKAGE_ROOT / "errors.py",
        PACKAGE_ROOT / "__init__.py",
        PACKAGE_ROOT / "repositories" / "person.py",
        PACKAGE_ROOT / "name_gate.py",
        SCRIPTS_ROOT / "lint_vault.py",
        TESTS_ROOT / "derivations.py",
        TESTS_ROOT / "test_timeline_entry.py",
        TESTS_ROOT / "test_introduced_by_accessor.py",
        TESTS_ROOT / "test_retired_key_gate_rule.py",
        TESTS_ROOT / "test_lint_vault_fix_rules.py",
        TESTS_ROOT / "test_name_gate.py",
        TESTS_ROOT / "fixture_vault.py",
    ]


#: This item's four AC check names, each of which must resolve to exactly ONE
#: module tree-wide — the conveyor's own discovery rule, which raises on a
#: duplicate.
AC_CHECKS = (
    "test_timeline_entry_reproduces_hal9000_render_and_validation_boundary",
    "test_introduced_by_reads_only_this_persons_intro_by_markers",
    "test_the_write_gate_refuses_the_retired_introduced_by_key",
    "test_lint_vault_reports_the_intro_legacy_shapes_and_never_repairs_them",
)

CORPUS_NOTE = TESTS_ROOT / "fixtures" / "vault" / "@Morvette Harkwell.md"


def test_the_wi033_files_close_their_wall_memberships_by_running_each_predicate():
    """Task 11's verify. Zero-arg and raising, per the check contract.

    §9's census is a FLOOR and never a total: it has under-reached at its reading
    step every time it has been run in this factory, which is why this check
    CALLS each wall's own shipped predicate on the files' FINAL text rather than
    reasoning about which shapes match. Anything the run returns that §9's table
    did not name is named in the Build Log and satisfied there, never by
    narrowing a wall.
    """
    from tests.derivations import (
        address_splitting_implementations,
        character_class_strip_sites,
        frontmatter_write_arms,
        modules_using_ast,
        python_files_under,
        skip_reason_literal_sites,
    )
    from obsidian_schemas.repositories.base import SKIP_REASONS
    from tests.test_ac_interpreter import check_module
    from tests.test_fixture_vault import _declared_pytest_python_files
    from tests.test_vault_path_required import NO_ARG_CONSTRUCTION

    touched = _touched_files()
    for path in touched:
        assert path.exists(), f"{path} is a declared write target and is absent"

    universe = python_files_under(PACKAGE_ROOT, TESTS_ROOT, SCRIPTS_ROOT)
    reached = {path.resolve() for path in universe}
    # NON-VACUITY FIRST: without it, every equality below is satisfied most
    # cheaply by a universe that never reaches the new files.
    missing = [p.name for p in touched if p.resolve() not in reached]
    assert missing == [], (
        f"the swept universe does not reach this item's own files: {missing}")

    # W-1 — the `ast` capability stays single-homed. A set EQUALITY whose universe
    # these files GROW, so a new member would redden it. `tests/test_name_gate.py`
    # is in the set and must NOT appear.
    homes = {use.module for use in modules_using_ast(universe)}
    assert homes == {"tests/derivations.py"}, (
        f"the `ast` capability must stay single-homed to the shared scan module; "
        f"found {sorted(homes)}")

    # W-15 — the skip vocabulary's legal homes, unchanged: no new file hand-types
    # a skip-reason literal.
    assert skip_reason_literal_sites(universe, SKIP_REASONS) == {
        "obsidian_schemas/repositories/base.py",
        "tests/test_fixture_vault.py",
    }

    # The frontmatter-write-arm derivation: the typed overload writes a BODY
    # through `vault_io` and the gate arm introduces no write, so the new module
    # contributes ZERO arms and `apply_fixes` is still exactly one.
    arms = frontmatter_write_arms(python_files_under(PACKAGE_ROOT, SCRIPTS_ROOT))
    for module in ("obsidian_schemas/timeline_entry.py",
                   "obsidian_schemas/name_gate.py",
                   "obsidian_schemas/repositories/person.py"):
        assert [a for a in arms if a.module == module] == [], (
            f"{module} grew a frontmatter write arm; the typed overload writes a "
            f"BODY through vault_io and the gate arm introduces no write at all")
    # `apply_fixes` is still EXACTLY ONE arm — the property two other modules pin
    # by equality, re-run here because Task 8 edits that file.
    linter = [a for a in arms if a.module == "scripts/lint_vault.py"]
    assert [a.qualname for a in linter] == ["apply_fixes"], linter

    # Two single-home walls whose own universe is the ROUTING one and does not
    # reach `tests/`. Run over the touched files inside that universe.
    in_routing_universe = [p for p in touched
                          if p.is_relative_to(PACKAGE_ROOT)
                          or p.is_relative_to(SCRIPTS_ROOT)]
    assert in_routing_universe, "the routing-universe slice is empty"
    assert character_class_strip_sites(in_routing_universe) == []
    # The address-splitting set over the touched files is exactly the ONE shipped
    # home and never the empty set: `name_gate.py` legitimately HOLDS that
    # implementation and Task 6 edits that file, so a zero here would be a wall
    # this item invented rather than the wall the tree declares. The requirement
    # is that this item adds no SECOND implementation.
    from tests.test_address_splitter import THE_ONE_HOME
    assert address_splitting_implementations(in_routing_universe) == {THE_ONE_HOME}

    # W-8 — the edited corpus note must not advertise no-arg construction.
    assert CORPUS_NOTE.exists()
    assert not NO_ARG_CONSTRUCTION.search(
        CORPUS_NOTE.read_text(encoding="utf-8", errors="replace"))

    # W-14 — the collection globs, read from the config's own declared values.
    globs = _declared_pytest_python_files()
    new_modules = [p for p in touched if p.parent == TESTS_ROOT
                   and p.name.startswith("test_")]
    assert len(new_modules) >= 4, new_modules
    for path in new_modules:
        assert any(fnmatch.fnmatch(path.name, pattern) for pattern in globs), (
            f"{path.name} matches no declared collection glob")
    # The corpus note and the manifest must still match NONE of them.
    for name in (CORPUS_NOTE.name, "fixture_vault.py", "derivations.py"):
        for pattern in globs:
            assert not fnmatch.fnmatch(name, pattern), (
                f"{name} matches the collection glob {pattern!r}")

    # W-10 — check-name uniqueness, over this item's four AC checks AND over
    # every top-level `def test_` in the one pre-existing check module Task 2
    # edits, whose two sweeping walls grade it from their own items' frozen lists.
    for name in AC_CHECKS:
        resolved = check_module(name)
        assert resolved.exists()
    gate_module = TESTS_ROOT / "test_name_gate.py"
    names = re.findall(r"^def (test_\w+)\(", gate_module.read_text(encoding="utf-8"), re.M)
    assert names, "test_name_gate.py defines no top-level check"
    for name in names:
        assert check_module(name) == gate_module
    assert any(fnmatch.fnmatch(gate_module.name, pattern) for pattern in globs), (
        "test_name_gate.py matches no declared collection glob — Task 2's edit "
        "would then be uncollected and its two sweeping walls would grade a file "
        "the floor never runs")
