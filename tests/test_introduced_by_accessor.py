"""WI-033 AC-2 — "who introduced this person" is ONE typed call that reads the
marker slot and nothing else, and it answers about the RIGHT person.

One check. Everything in it is PLANTED, and that is forced rather than chosen: the
frozen fixture corpus contains ZERO timeline entries, so it cannot tell a correct
accessor from a stub that returns `[]` — membership proves nothing where there are
no members. Both axes the accessor selects on therefore carry a PLANTED
discriminating member:

* THE KIND AXIS. `intro-to` and legacy `intro` are in the sweep precisely because
  `"intro" in kind` is the cheapest wrong implementation and would return three
  records where the definition says one. The out-of-table kind is there because
  `PARITY_KINDS` is a FIXTURE SPACE and not a gate: a build that quietly used it as
  the accessor's filter, or raised on an unlisted kind while reading a note, would
  otherwise be green.
* THE PERSON AXIS — the one the accessor's own first argument selects on. With
  `intro-by` data on exactly ONE note, a build that globs every note under the
  vault for markers (or reads a fixed or first note) returns precisely the record a
  one-note oracle expects and goes green on every other clause; shipped against a
  vault of a thousand person notes it could answer `introduced_by(@Alice)` with
  @Bob's introducer, or with the union of everyone's records, with a green floor.
  So a second person is planted, and the scoping is asserted in BOTH directions
  plus INVARIANCE to the other note's presence — which is what makes the promise
  "reads that person's own note" rather than "filters a vault-wide read by
  something".

Each planted entry is produced by the library's own `render`, so the fixture's
bytes are the DOOR's bytes and no hand-typed marker can drift from what a writer
would actually emit.

Nothing here reads syntax directly: that capability is single-homed in
`tests/derivations.py`, and the scan below is imported from it.
"""

# FIRST, ahead of every package import: the conveyor may run this module's checks
# under an interpreter that is not this project's, where the imports below cannot
# resolve. A no-op under the floor command and under CI.
from tests.ac_interpreter import ensure_project_interpreter

ensure_project_interpreter(__file__)

import importlib.util  # noqa: E402
from datetime import date, datetime  # noqa: E402
from pathlib import Path  # noqa: E402

from obsidian_schemas import timeline_entry  # noqa: E402
from obsidian_schemas.repositories import PersonRepository  # noqa: E402
from obsidian_schemas.timeline_entry import (  # noqa: E402
    INTRO_BY_KIND,
    IntroRecord,
    PARITY_KINDS,
    TimelineEntry,
    render,
)
from tests.derivations import (  # noqa: E402
    PACKAGE_ROOT,
    SCRIPTS_ROOT,
    marker_grammar_sites,
    python_files_under,
)
from tests.support import temp_dir  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
LINT_VAULT_PATH = SCRIPTS_ROOT / "lint_vault.py"

#: AC-1(a4)'s planted out-of-table kind, re-used here for the complementary
#: reason: the accessor's filter is the EXACT slug and is NOT `PARITY_KINDS`
#: membership, so a kind the library never captured must yield no record and must
#: not raise.
PLANTED_KIND = "deal-closed"

#: Person A — the KIND sweep's note. Its `intro-by` counterparty and day.
A_STEM = "@Alma Ostrivane"
A_INTRODUCER = "Tamsin Okoro-Vale"
A_DAY = date(2026, 9, 27)

#: Person B — the PERSON-axis discriminant. A different counterparty, a different
#: day, and therefore different `source` bytes in every field.
B_STEM = "@Brannock Sennaby"
B_INTRODUCER = "Sören Wexley"
B_DAY = date(2025, 11, 10)

#: The one definition of the marker grammar, after this item.
THE_ONE_GRAMMAR_HOME = "obsidian_schemas/timeline_entry.py"


def _entry(kind, introducer, day, text=None):
    return TimelineEntry(
        kind=kind,
        text=text or f"Introduced by [[{'@' + introducer}|{introducer}]] via gmail",
        when=datetime(day.year, day.month, day.day, 12, 0, 0),
        discriminator=introducer,
    )


def _note(stem, entries=(), extra_timeline="", extra_sections=""):
    """A person note whose `## Timeline` holds `entries` NEWEST FIRST, each
    rendered through the library's own renderer."""
    span = "".join(f"\n{render(entry)}" for entry in entries)
    return (f"---\ntype: person\nname: \"{stem.lstrip('@')}\"\n---\n\n"
            f"## Timeline\n{span}{extra_timeline}\n{extra_sections}")


def _plant(vault, stem, body):
    path = Path(vault) / f"{stem}.md"
    path.write_text(body, encoding="utf-8")
    return path


def _a_entries():
    """One entry per `PARITY_KINDS` member — ITERATED, never hand-listed — plus the
    planted out-of-table kind. Newest first, so the stored order the door produces
    is the order the fixture carries."""
    kinds = sorted(PARITY_KINDS) + [PLANTED_KIND]
    return [_entry(kind, A_INTRODUCER if kind == INTRO_BY_KIND
                   else f"Counterparty {kind}", A_DAY)
            for kind in kinds]


def _seed_two_people(vault):
    _plant(vault, A_STEM, _note(A_STEM, _a_entries()))
    _plant(vault, B_STEM, _note(
        B_STEM, [_entry(INTRO_BY_KIND, B_INTRODUCER, B_DAY)]))


# ==========================================================================
# AC-2 — one check
# ==========================================================================

def test_introduced_by_reads_only_this_persons_intro_by_markers():
    """AC-2's verify. Zero-arg and raising, per the check contract."""
    with temp_dir() as root:
        _check_the_kind_axis(root)                        # (a) + the main oracle
    with temp_dir() as root:
        _check_the_person_axis_in_both_directions(root)   # (a2)
    with temp_dir() as root:
        _check_plurality_and_order(root)                  # (b)
    with temp_dir() as root:
        _check_the_markerless_arm_is_narrowed(root)       # (c)
    with temp_dir() as root:
        _check_never_the_other_channels(root)             # (d)
    _check_the_grammar_has_exactly_one_definition()       # (e)


def _repo(root):
    vault = Path(root) / "vault"
    vault.mkdir()
    _seed_two_people(vault)
    return vault, PersonRepository(vault)


# --------------------------------------------------------------------------
# (a) — the kind axis, and the oracle this document states
# --------------------------------------------------------------------------

def _check_the_kind_axis(root):
    vault, repo = _repo(root)
    records = repo.introduced_by(repo.get(A_STEM.lstrip("@")))

    # THE ORACLE, stated in this document and not re-derived from the
    # implementation: exactly one record for the `intro-by` member, and NO record
    # for any other member — so a build keyed on `"intro" in kind` (which would
    # return three, sweeping up `intro-to` and legacy `intro`) MISMATCHES rather
    # than agreeing with itself.
    assert len(records) == 1, (
        f"the sweep planted one entry per PARITY_KINDS member plus an out-of-table "
        f"kind; exactly ONE of them is `intro-by`, and the accessor returned "
        f"{len(records)} records: {records}")
    record = records[0]
    assert isinstance(record, IntroRecord)
    assert record.introducer == A_INTRODUCER, (
        "the counterparty comes VERBATIM from the marker's discriminator slot")
    assert record.date == A_DAY, "the day comes from the marker's day slot"

    # `source` is the PROVENANCE field, pinned BYTE-FOR-BYTE against the marker
    # substring present in A's OWN note text. Without a pinned value the third slot
    # is a field a build could ship as `None` with every other clause green.
    note_text = (vault / f"{A_STEM}.md").read_text(encoding="utf-8")
    assert record.source, "`source` must be the bytes on the page, never None"
    assert record.source in note_text
    assert record.source.startswith("<!-- ") and record.source.endswith(" -->")
    assert A_INTRODUCER in record.source

    # No record carries B's counterparty or B's day, with B's note in the vault.
    assert B_INTRODUCER not in {r.introducer for r in records}
    assert B_DAY not in {r.date for r in records}

    # The out-of-table kind yields no record and does NOT raise: the filter is the
    # EXACT slug and is not `PARITY_KINDS` membership.
    assert PLANTED_KIND not in PARITY_KINDS
    assert PLANTED_KIND not in {r.introducer for r in records}


# --------------------------------------------------------------------------
# (a2) — the person axis, in BOTH directions, plus the invariance run
# --------------------------------------------------------------------------

def _check_the_person_axis_in_both_directions(root):
    vault, repo = _repo(root)

    a_records = repo.introduced_by(repo.get(A_STEM.lstrip("@")))
    b_records = repo.introduced_by(repo.get(B_STEM.lstrip("@")))

    # BOTH directions. A one-directional check would still pass whichever of the
    # two a union build happens to order first.
    assert [(r.introducer, r.date) for r in a_records] == [(A_INTRODUCER, A_DAY)]
    assert [(r.introducer, r.date) for r in b_records] == [(B_INTRODUCER, B_DAY)]

    # Never the UNION, and never the other person's record.
    assert a_records != b_records
    assert len(a_records) == 1 and len(b_records) == 1
    b_note = (vault / f"{B_STEM}.md").read_text(encoding="utf-8")
    assert b_records[0].source in b_note
    assert a_records[0].source not in b_note

    # THE INVARIANCE RUN — what makes the promise "reads that person's OWN note"
    # rather than "filters a vault-wide read by something". A build reading the
    # vault at large cannot be green in both runs.
    (vault / f"{B_STEM}.md").unlink()
    without_b = PersonRepository(vault)
    assert without_b.introduced_by(without_b.get(A_STEM.lstrip("@"))) == a_records


# --------------------------------------------------------------------------
# (b) — plurality and order, on ONE person's own note
# --------------------------------------------------------------------------

def _check_plurality_and_order(root):
    vault = Path(root) / "vault"
    vault.mkdir()
    # B stays in the vault, so plurality is that person's own two and never a
    # third borrowed from elsewhere.
    _plant(vault, B_STEM, _note(B_STEM, [_entry(INTRO_BY_KIND, B_INTRODUCER, B_DAY)]))

    newer = _entry(INTRO_BY_KIND, "Perrowin Quillam", date(2026, 6, 1))
    older = _entry(INTRO_BY_KIND, "Isolde Kelmarra", date(2024, 2, 2))
    _plant(vault, A_STEM, _note(A_STEM, [newer, older]))

    repo = PersonRepository(vault)
    records = repo.introduced_by(repo.get(A_STEM.lstrip("@")))
    assert [r.introducer for r in records] == ["Perrowin Quillam", "Isolde Kelmarra"], (
        "two `intro-by` entries on ONE person's own note return exactly two "
        "records, in stored document order — newest-first, because the door "
        "PREPENDS despite its name")
    assert [r.date for r in records] == [date(2026, 6, 1), date(2024, 2, 2)]
    assert B_INTRODUCER not in {r.introducer for r in records}


# --------------------------------------------------------------------------
# (c) — the NARROWED arm, stated rather than invented
# --------------------------------------------------------------------------

def _check_the_markerless_arm_is_narrowed(root):
    """An `intro-by` HEADING carrying no marker has no counterparty slot and
    therefore NO RIGHT ANSWER. It is asserted ABSENT from the result here AND
    asserted PRESENT in AC-4's `intro_by_without_marker` report, which is the
    declared marker that keeps the narrowing honest rather than convenient. Both
    halves matter: without the report, a build could quietly drop them."""
    vault = Path(root) / "vault"
    vault.mkdir()
    _plant(vault, B_STEM, _note(B_STEM, [_entry(INTRO_BY_KIND, B_INTRODUCER, B_DAY)]))

    good = _entry(INTRO_BY_KIND, "Perrowin Quillam", date(2026, 6, 1))
    markerless = "\n### March 4, 2026 [intro-by]\nIntroduced by somebody, no marker.\n"
    _plant(vault, A_STEM, _note(A_STEM, [good], extra_timeline=markerless))

    repo = PersonRepository(vault)
    records = repo.introduced_by(repo.get(A_STEM.lstrip("@")))
    assert [r.introducer for r in records] == ["Perrowin Quillam"], (
        "a markerless `intro-by` heading has no recoverable counterparty and must "
        "be ABSENT from the answer rather than guessed at")

    # The other half of the promise: the library's own heading reader SEES that
    # entry and reports it as marker-less, which is what AC-4(b)'s detector
    # consumes. Asserted here through the same function the detector calls, so the
    # two halves cannot disagree about what "well-formed" means.
    from obsidian_schemas.body_sections import get_section
    span = get_section((vault / f"{A_STEM}.md").read_text(encoding="utf-8"),
                       "Timeline") or ""
    unmarked = [e for e in timeline_entry.parse_entries(span)
                if e.kind == INTRO_BY_KIND and e.marker is None]
    assert len(unmarked) == 1, (
        f"the library's heading reader must SEE the markerless entry so the "
        f"linter can report it; it found {len(unmarked)}")


# --------------------------------------------------------------------------
# (d) — never the other channels
# --------------------------------------------------------------------------

def _check_never_the_other_channels(root):
    """All three asserted with B's well-formed `intro-by` note PRESENT in the same
    vault, so "nothing" means NOTHING — not somebody else's record."""
    vault = Path(root) / "vault"
    vault.mkdir()
    _plant(vault, B_STEM, _note(B_STEM, [_entry(INTRO_BY_KIND, B_INTRODUCER, B_DAY)]))

    # 1. PROSE only. Reading it would rebuild `lint_vault`'s `intro_not_symmetric`
    #    regex inside the library — the second parser copy the Intent exists to
    #    prevent. The marker is the structure; the prose is the lossy copy.
    prose = _plant(vault, "@Caldreth Ashquill", _note(
        "@Caldreth Ashquill",
        extra_timeline="\n### May 6, 2026 [note]\nIntroduced by [[@Sam Tucker]] over dinner.\n"))

    # 2. A FRONTMATTER key. The ruling retires it; the accessor never reads it.
    #    Written as raw bytes rather than through a door, because the gate now
    #    refuses exactly this write — which is AC-3's business and not this one's.
    fm = Path(vault) / "@Dalquest Nimbrook.md"
    fm.write_text(
        "---\ntype: person\nname: \"Dalquest Nimbrook\"\n"
        "introduced_by: \"Sam Tucker\"\n---\n\n## Timeline\n\n", encoding="utf-8")

    # 3. NO `## Timeline` section at all — `[]` rather than a raise. Absence of
    #    entries is a legitimate answer.
    bare = Path(vault) / "@Elowick Ferrigan.md"
    bare.write_text("---\ntype: person\nname: \"Elowick Ferrigan\"\n---\n\nPreamble.\n",
                    encoding="utf-8")

    repo = PersonRepository(vault)
    for stem in ("Caldreth Ashquill", "Dalquest Nimbrook", "Elowick Ferrigan"):
        assert repo.introduced_by(repo.get(stem)) == [], (
            f"{stem} has no `intro-by` MARKER, so the answer is the empty list — "
            f"not a prose guess, not a frontmatter read, and not B's record")
    assert prose.exists() and fm.exists() and bare.exists()

    # A note that is not in the repository at all raises the door's own ValueError:
    # absence of entries is a legitimate answer, absence of a NOTE is not.
    from obsidian_schemas.models import Person
    try:
        repo.introduced_by(Person(type="person", name="Nobody Ravensby"))
    except ValueError as exc:
        assert "Nobody Ravensby" in str(exc)
    else:
        raise AssertionError("a person with no note must raise the door's ValueError")


# --------------------------------------------------------------------------
# (e) — ONE definition of the grammar, asserted structurally (Task 10)
# --------------------------------------------------------------------------

def _load_lint_vault():
    """`scripts/` is not a package, so the CLI is loaded from its own path —
    through the SAME shape `tests/test_lint_vault_fix_rules.py:_load_lint_vault`
    already carries."""
    spec = importlib.util.spec_from_file_location(
        "wi033_lint_vault", LINT_VAULT_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_GRAMMAR_PLANTS = {
    # name -> (source, is a DEFINITION site)
    "defines_the_regex.py": (
        "import re\n"
        "MARKER = re.compile(r'^<!-- (?P<kind>[a-z-]+) -->$')\n",
        True,
    ),
    "only_in_a_docstring.py": (
        '"""Explains the <!-- kind:day:disc --> marker without defining it."""\n'
        "X = 1\n",
        False,
    ),
    "only_in_a_comment.py": (
        "# the marker looks like <!-- kind:day:disc -->\n"
        "X = 1\n",
        False,
    ),
    "merely_imports.py": (
        "from obsidian_schemas.timeline_entry import MARKER_PATTERN, parse_markers\n"
        "USES = (MARKER_PATTERN, parse_markers)\n",
        False,
    ),
    "near_miss_split.py": (
        "OPEN = '<!'\nDASHES = '--'\nCLOSE = '>'\n",
        False,
    ),
}


def _check_the_grammar_has_exactly_one_definition():
    """AC-2(e). The scan covers `obsidian_schemas/**` AND `scripts/**` — because
    `scripts/` is where the second copy has ALREADY appeared once in this tree
    (`intro_not_symmetric`'s prose regex) and where this item's own marker-reading
    detector lands. A scan bounded to the package would let a builder write a
    second marker regex in `scripts/lint_vault.py` and satisfy the criterion and
    violate the Intent in the same commit."""
    sites = marker_grammar_sites(python_files_under(PACKAGE_ROOT, SCRIPTS_ROOT))
    assert sites, "the grammar scan found nothing at all — every claim is vacuous"
    assert {site.module for site in sites} == {THE_ONE_GRAMMAR_HOME}, (
        f"the marker grammar must be DEFINED in exactly one file; found "
        f"{sorted({s.module for s in sites})}")
    assert [s for s in sites if s.module == "scripts/lint_vault.py"] == [], (
        "the linter must define no pattern of its own")

    # The clause permits an IMPORT and forbids a RE-DEFINITION, which is LESSONS
    # #4's rule ("route to the first, do not copy it") as a predicate a test can
    # run. Proved by OBJECT IDENTITY, which proves the import rather than a
    # spelling of it.
    lint_vault = _load_lint_vault()
    assert lint_vault.parse_entries is timeline_entry.parse_entries
    assert lint_vault.INTRO_BY_KIND is timeline_entry.INTRO_BY_KIND
    assert lint_vault.LEGACY_INTRO_KIND is timeline_entry.LEGACY_INTRO_KIND

    # `intro_not_symmetric`'s prose regex is UNTOUCHED by this item and is outside
    # the predicate BY CONSTRUCTION rather than by exemption: it contains no marker
    # delimiter at all.
    script_text = LINT_VAULT_PATH.read_text(encoding="utf-8")
    assert "[Ii]ntroduc(?:ed|tion)[^[]*" in script_text, (
        "the shipped prose detector was removed; that is a separate subtraction "
        "with its own audit and is not this item's")
    prose_regex_line = next(
        line for line in script_text.splitlines()
        if "[Ii]ntroduc(?:ed|tion)[^[]*" in line)
    assert "<!--" not in prose_regex_line and "-->" not in prose_regex_line

    _check_the_grammar_scan_reaches_every_claimed_shape()


def _check_the_grammar_scan_reaches_every_claimed_shape():
    """WI-235. `the module set is a singleton` is a COUNT oracle, satisfied
    identically by a predicate that resolves every claimed shape and by one that
    resolves almost none — so every claimed shape is driven through
    `marker_grammar_sites` ITSELF, plus the near-miss it must not collect."""
    with temp_dir() as scratch:
        for name, (source, _matched) in _GRAMMAR_PLANTS.items():
            (Path(scratch) / name).write_text(source, encoding="utf-8")
        collected = {Path(site.module).name
                     for site in marker_grammar_sites(python_files_under(Path(scratch)))}
        expected = {name for name, (_s, matched) in _GRAMMAR_PLANTS.items() if matched}
        assert collected == expected, (
            f"the grammar predicate collected {sorted(collected)}; it must collect "
            f"exactly {sorted(expected)} — a docstring, a comment, a bare import "
            f"and a split near-miss are all legal and must not be reported")
