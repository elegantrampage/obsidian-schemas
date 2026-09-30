"""WI-033 AC-3 — the retired `introduced_by` key cannot creep back, and the
refusal is TOTAL over the arms rather than arm-conditional.

One check, in four legs plus the emptied-population scan.

**Why an unconditional ban needed a design and not a line of code.** The gate is
DECLARE-only: it reads nothing but its arguments, so it structurally cannot tell
"this write INTRODUCES the key" from "this projection RE-EMITS a key the note
already had" — and `model_to_frontmatter` emits `model_extra` unconditionally,
which means a blanket ban makes every carrier permanently unwritable through
`save`. That is the remedy-is-the-disease outcome the gate's own DELTA doctrine
was written against. It is resolved by MEASUREMENT rather than by an exemption:
live is already zero after the 2026-09-28 hand conversion, and the one fixture
carrier is re-keyed — so the rule stays unconditional, one place, one literal, and
no exemption arm exists for a later build to widen.

The inverted trade is deliberate: a note that regains the key by hand-edit is
unwritable through `save` until the key is deleted. That is correct pressure for a
RETIRED KEY (a one-line remedy, and `lint_vault`'s `retired_key_introduced_by`
names the note) where it would be punitive for a dirty NAME, which has no remedy
but a rename.

Nothing here reads syntax directly: that capability is single-homed in
`tests/derivations.py`, and every scan below is imported from it.
"""

# FIRST, ahead of every package import: the conveyor may run this module's checks
# under an interpreter that is not this project's, where the imports below cannot
# resolve. A no-op under the floor command and under CI.
from tests.ac_interpreter import ensure_project_interpreter

ensure_project_interpreter(__file__)

from pathlib import Path  # noqa: E402

import yaml  # noqa: E402

from obsidian_schemas import writer  # noqa: E402
from obsidian_schemas.errors import NameGateRefusal  # noqa: E402
from obsidian_schemas.models import Person  # noqa: E402
from obsidian_schemas.name_gate import (  # noqa: E402
    RETIRED_KEY_PATTERN,
    RETIRED_PERSON_KEY,
    gate_write,
)
from obsidian_schemas.repositories import PersonRepository  # noqa: E402
from tests.derivations import (  # noqa: E402
    PACKAGE_ROOT,
    gate_call_sites,
    python_files_under,
    select_fenced_blocks,
    select_sections,
)
from tests.fixture_vault import CORPUS_ROOT, NOTES  # noqa: E402
from tests.support import temp_dir  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
VAULT_FIXTURES_DOC = REPO_ROOT / "docs" / "vault-fixtures.md"
CORPUS_BASELINE_DOC = REPO_ROOT / "docs" / "wi-033-intro-corpus-baseline.md"

#: The ONE gate call site that structurally cannot carry a person frontmatter
#: delta: WI-021's D7 re-serialization arm, which introduces no field and passes
#: `None` deliberately. NAMED rather than discovered — a derived sweep that
#: quietly drops arms is indistinguishable from an incomplete one.
EXCLUDED_SITE = ("obsidian_schemas/writer.py", "roundtrip_file")

#: The re-keyed corpus carrier and its new value (`## Design` §6 / D9). Both
#: tokens are existing `NAME_POOL` members and the PAIR is no corpus note's name,
#: stem, alias or title — so it resolves to nothing and carries no second job,
#: which is D3's actual intent satisfied without touching the digest-frozen census.
CORPUS_CARRIER = "@Morvette Harkwell.md"
SWAPPED_LINE = 'manager: "Oskaline Thrandell"'

#: `docs/vault-fixtures.md`'s own bytes at `:279-280`, quoted VERBATIM rather than
#: from AC-3(c)'s paraphrase (which renders the sentence "a `manager:` or
#: `introduced_by:` key"; there is no "key" in the file).
CORRECTED_PHRASE = "a `manager:` on a schema-drift or forward-compatibility note"
STALE_PHRASE = "a `manager:` or `introduced_by:`"


def _normalize(text):
    """§12 Rule 2 — every phrase oracle compares WHITESPACE-NORMALIZED text.

    Not a convenience: `docs/vault-fixtures.md` hard-wraps at ~100 columns and the
    target sentence spans `:279-280`, so after the conductor's one-sentence
    deletion the corrected phrase still contains a NEWLINE and a literal `in` test
    would be RED against a correct edit — while the ABSENCE half is contiguous on
    one line today and would have passed, which is exactly what hid the defect.
    Re-wrapping is deliberately NOT asked of the conductor: it only moves the
    break to a different word, and no assertion in this item may depend on a wrap
    column.
    """
    return " ".join(text.split())


def _person_note(stem, extra_lines=""):
    return (f"---\ntype: person\nname: \"{stem.lstrip('@')}\"\n{extra_lines}---\n\n"
            "## To Discuss\n\n## Timeline\n\n## Notes\n")


# ==========================================================================
# AC-3 — one check, four legs, plus the emptied-population scan
# ==========================================================================

def test_the_write_gate_refuses_the_retired_introduced_by_key():
    """AC-3's verify. Zero-arg and raising, per the check contract.

    CORPUS_COUPLING: this check makes TWO `docs/**` reads. (1) It pins ONE heading
    name (`## Exploration Notes`) and the presence of ONE whitespace-normalized
    phrase inside it (`a `manager:` on a schema-drift or forward-compatibility
    note`) plus that phrase's stale two-key predecessor's ABSENCE from the same
    normalized text, in `docs/vault-fixtures.md`, and consumes the property that
    that file's undeclared-key example names the key the gate still permits. (2) It
    pins ONE heading name (`## Counts`) and ONE key
    (`introduced_by_frontmatter_carriers`) in the one `yaml` fence of
    `docs/wi-033-intro-corpus-baseline.md`, and consumes the property that the
    fence is a dated snapshot of the live vault produced by the committed census
    command — read as this criterion's PREMISE and never re-measured, because the
    floor is hermetic and cannot reach the vault.
    """
    _check_the_refusal_names_the_key_and_not_its_value()          # (a)
    _check_the_sweep_is_total_over_the_gated_arms()               # (b)
    _check_the_fixture_population_is_empty_not_exempted()         # (c)
    _check_nothing_else_moves()                                   # (d)


# --------------------------------------------------------------------------
# (a) — refused, on both values of `whole_record`, including the UNDECLARED route
# --------------------------------------------------------------------------

def _refusal_from(introduced, *, declared_type, whole_record):
    try:
        gate_write(introduced, declared_type=declared_type,
                   whole_record=whole_record)
    except NameGateRefusal as refusal:
        return refusal
    raise AssertionError(
        f"the gate accepted {introduced!r} (declared_type={declared_type!r}, "
        f"whole_record={whole_record})")


def _check_the_refusal_names_the_key_and_not_its_value():
    payload = {"name": "Oskaline Pellworth", RETIRED_PERSON_KEY: "Sam Tucker"}
    for whole_record in (True, False):
        refusal = _refusal_from(payload, declared_type="person",
                                whole_record=whole_record)
        assert refusal.pattern == RETIRED_KEY_PATTERN
        # The KEY, never the key's VALUE: at this arm the value is a person's
        # name, and keeping note-derived identity out of refusals is exactly what
        # the gate's `_refuse` rule 2 exists for.
        assert refusal.refused_value == RETIRED_PERSON_KEY
        assert "Sam Tucker" not in str(refusal)
        assert "Sam Tucker" != refusal.refused_value

    # THE UNDECLARED ROUTE, asserted EXPLICITLY. `gate_write`'s declared-non-person
    # early return is guarded by `is not None` precisely so an undeclared write
    # introducing identifiers but NO `name:` falls THROUGH to the person body — so
    # a rule keyed on `declared_type == PERSON_TYPE` would leave a person note
    # missing its `type:` free to carry the key. That is "cannot creep back" with a
    # hole in it, and this is the assertion that tells the two placements apart.
    undeclared = _refusal_from({RETIRED_PERSON_KEY: "Sam Tucker"},
                               declared_type=None, whole_record=False)
    assert undeclared.pattern == RETIRED_KEY_PATTERN


# --------------------------------------------------------------------------
# (b) — TOTAL over the arms, with the exclusion asserted as an EQUALITY
# --------------------------------------------------------------------------

def _check_the_sweep_is_total_over_the_gated_arms():
    sites = gate_call_sites(python_files_under(PACKAGE_ROOT))
    assert sites, "the derived gate-call sweep is empty — every claim below is vacuous"

    excluded = {(site.module, site.qualname) for site in sites
                if site.fields_is_empty_literal
                and site.declared_type_is_none_literal}
    assert excluded == {EXCLUDED_SITE}, (
        f"the set of sites that structurally cannot carry a person delta must be "
        f"exactly {EXCLUDED_SITE}; got {sorted(excluded)}")

    covered = set()
    with temp_dir() as root:
        covered |= _drive_the_writer_arms(root)
    with temp_dir() as root:
        covered |= _drive_the_repository_arms(root)

    # THE DRIVE TABLE IS ASSERTED TOTAL, so a seventh call site added later is RED
    # until someone drives it rather than silently unswept.
    derived = {(site.module, site.qualname) for site in sites}
    assert covered | excluded == derived, (
        f"the drive table is not total over the derived gate-call sites. "
        f"Undriven and unexcluded: {sorted(derived - covered - excluded)}. "
        f"Driven but not derived: {sorted(covered - derived)}")

    _check_the_derivation_reaches_every_claimed_call_shape()


def _refuses_leaving_the_file_byte_identical(path, act):
    """Every driven arm refuses AND changes nothing. A refusal that fires after a
    partial write is worse than no refusal."""
    before = path.read_bytes()
    try:
        act()
    except NameGateRefusal as refusal:
        assert refusal.pattern == RETIRED_KEY_PATTERN
    else:
        raise AssertionError(f"the arm at {path.name} did not refuse")
    assert path.read_bytes() == before, (
        f"{path.name} changed despite the refusal — a refusal that fires after a "
        f"partial write is worse than no refusal")


def _drive_the_writer_arms(root):
    vault = Path(root) / "vault"
    vault.mkdir()
    carrying = {"type": "person", "name": "Quillam Ravensby",
                RETIRED_PERSON_KEY: "Sam Tucker"}

    # `write_markdown_file` with `frontmatter=` and with `entity=` — two of its
    # three converging branches, and the two that can carry a delta.
    dict_shaped = vault / "@Quillam Ravensby.md"
    dict_shaped.write_text(_person_note("@Quillam Ravensby"), encoding="utf-8")
    _refuses_leaving_the_file_byte_identical(
        dict_shaped,
        lambda: writer.write_markdown_file(dict_shaped, frontmatter=carrying))

    entity_shaped = vault / "@Sennaby Corvallen.md"
    entity_shaped.write_text(_person_note("@Sennaby Corvallen"), encoding="utf-8")
    person = Person(type="person", name="Sennaby Corvallen")
    # `extra="allow"`, so a bare attribute assignment lands in `model_extra` and
    # `model_to_frontmatter` re-emits it — which is the whole reason the gate
    # cannot tell an introduction from a re-emission.
    setattr(person, RETIRED_PERSON_KEY, "Sam Tucker")
    _refuses_leaving_the_file_byte_identical(
        entity_shaped,
        lambda: writer.write_markdown_file(entity_shaped, entity=person))

    field_shaped = vault / "@Tarnholt Lumbrek.md"
    field_shaped.write_text(_person_note("@Tarnholt Lumbrek"), encoding="utf-8")
    _refuses_leaving_the_file_byte_identical(
        field_shaped,
        lambda: writer.update_frontmatter_field(
            field_shaped, RETIRED_PERSON_KEY, "Sam Tucker"))

    fields_shaped = vault / "@Ulvestre Kelmarra.md"
    fields_shaped.write_text(_person_note("@Ulvestre Kelmarra"), encoding="utf-8")
    _refuses_leaving_the_file_byte_identical(
        fields_shaped,
        lambda: writer.update_frontmatter_fields(
            fields_shaped, {RETIRED_PERSON_KEY: "Sam Tucker"}))

    return {("obsidian_schemas/writer.py", "write_markdown_file"),
            ("obsidian_schemas/writer.py", "update_frontmatter_field"),
            ("obsidian_schemas/writer.py", "update_frontmatter_fields")}


def _drive_the_repository_arms(root):
    vault = Path(root) / "vault"
    vault.mkdir()
    for stem in ("@Varnholt Ashquill.md", "@Wexlund Brenvik.md"):
        (vault / stem).write_text(_person_note(stem[:-3]), encoding="utf-8")

    repo = PersonRepository(vault)

    update_target = vault / "@Varnholt Ashquill.md"
    person = repo.get("Varnholt Ashquill")
    _refuses_leaving_the_file_byte_identical(
        update_target,
        lambda: repo.update_fields(person, {RETIRED_PERSON_KEY: "Sam Tucker"}))

    # `save`, where the key arrives INSIDE `model_to_frontmatter`'s projection
    # because `Person` is `extra="allow"` — the arm the DELTA doctrine's objection
    # is actually about.
    save_target = vault / "@Wexlund Brenvik.md"
    saved = repo.get("Wexlund Brenvik")
    setattr(saved, RETIRED_PERSON_KEY, "Sam Tucker")
    _refuses_leaving_the_file_byte_identical(
        save_target, lambda: repo.save(saved))

    return {("obsidian_schemas/repositories/base.py", "BaseRepository.update_fields"),
            ("obsidian_schemas/repositories/person.py", "PersonRepository.save")}


_PLANTS = {
    # (module name, source) -> the flags the derivation must report
    "direct_excluded.py": (
        "from obsidian_schemas.name_gate import gate_write\n"
        "def arm():\n"
        "    gate_write({}, declared_type=None, whole_record=False)\n",
        (True, True),
    ),
    "attribute_declaration.py": (
        "from obsidian_schemas.name_gate import gate_write\n"
        "def arm(self):\n"
        "    gate_write({}, declared_type=self.type_name, whole_record=True)\n",
        (True, False),
    ),
    "nonempty_and_none.py": (
        "from obsidian_schemas.name_gate import gate_write\n"
        "def arm(fm):\n"
        "    gate_write({'name': 'x'}, declared_type=None, whole_record=False)\n",
        (False, True),
    ),
    "aliased_import.py": (
        "def arm(fm):\n"
        "    from obsidian_schemas.name_gate import gate_write as _gw\n"
        "    _gw({}, declared_type=None, whole_record=False)\n",
        (True, True),
    ),
}

_NEAR_MISS = (
    '"""A docstring that says gate_write( and must not be collected."""\n'
    "def not_the_gate(fields, declared_type=None):\n"
    "    # a comment naming gate_write( too\n"
    "    return gate_written({}, declared_type=None)\n"
)


def _check_the_derivation_reaches_every_claimed_call_shape():
    """WI-235. `excluded == {one site}` is a COUNT oracle: it passes identically
    whether the predicate resolves every shape the spec claims or almost none. So
    every claimed shape is driven through the DERIVATION ITSELF, plus a near-miss
    it must not collect."""
    with temp_dir() as scratch:
        for name, (source, expected) in _PLANTS.items():
            (Path(scratch) / name).write_text(source, encoding="utf-8")
        (Path(scratch) / "near_miss.py").write_text(_NEAR_MISS, encoding="utf-8")

        sites = gate_call_sites(python_files_under(Path(scratch)))
        by_module = {Path(site.module).name: site for site in sites}

        assert set(by_module) == set(_PLANTS), (
            f"the derivation collected {sorted(by_module)} from the plants; the "
            f"near-miss must contribute nothing and every claimed shape exactly "
            f"one site (expected {sorted(_PLANTS)})")
        for name, (_source, expected) in _PLANTS.items():
            site = by_module[name]
            got = (site.fields_is_empty_literal,
                   site.declared_type_is_none_literal)
            assert got == expected, f"{name}: derivation reported {got}, claimed {expected}"
            assert site.ordinal == 1


# --------------------------------------------------------------------------
# (c) — the population is EMPTY, not exempted
# --------------------------------------------------------------------------

def _check_the_fixture_population_is_empty_not_exempted():
    # PIN BOTH WALKED POPULATIONS BY THEIR ONE LOAD-BEARING MEMBER FIRST. An
    # absence over a walked population is satisfied VACUOUSLY by a walk that
    # returns nothing — the same defect shape as a truncated markdown span, one
    # level up. A MEMBER pin and never a size pin: the corpus is a population
    # WI-016 is entitled to grow, so a count would be somebody else's ratchet.
    corpus_notes = [p for p in CORPUS_ROOT.iterdir() if p.is_file()]
    reached = {p.name for p in corpus_notes}
    assert CORPUS_CARRIER in reached, (
        f"the corpus walk does not reach {CORPUS_CARRIER} — every absence below "
        f"would then hold vacuously")
    carrier_text = (CORPUS_ROOT / CORPUS_CARRIER).read_text(encoding="utf-8")
    assert SWAPPED_LINE in carrier_text, (
        f"{CORPUS_CARRIER} does not carry the swapped line {SWAPPED_LINE!r}")

    assert CORPUS_CARRIER in NOTES, "the manifest walk does not reach the carrier"
    assert "manager" in NOTES[CORPUS_CARRIER].undeclared, (
        "the carrier's own NoteSpec no longer declares an undeclared `manager` "
        "key, so it has lost the AC-5(b) clause-3 job the swap was meant to keep")

    # THEN the absence, over both pinned populations.
    for path in corpus_notes:
        text = path.read_text(encoding="utf-8", errors="replace")
        assert RETIRED_PERSON_KEY not in text, (
            f"corpus note {path.name} still names the retired key")
    for stem, spec in NOTES.items():
        assert RETIRED_PERSON_KEY not in spec.undeclared, stem

    # The swapped value's tokens are all certified pool members — the constraint
    # that makes the swap BUILDABLE. A fresh token would need a new row in the
    # digest-frozen census, a live measurement the caged builder cannot make.
    from tests.fixture_vault import NAME_POOL
    for token in ("Oskaline", "Thrandell"):
        assert token in NAME_POOL, token

    _check_the_documentation_stops_offering_the_key()
    _check_the_live_half_is_a_committed_premise()


def _check_the_documentation_stops_offering_the_key():
    """AC-3(c)'s doc clause, as a POSITIVE, SECTION-SCOPED, WRAP-INSENSITIVE read.

    Never a whole-file absence pin: that is the WI-278 failure shape twice over —
    it pins a LIVE population's shape over another item's 6,200-line tracked
    document, and it would have been SATISFIED by deleting the sentence outright,
    which is the opposite of what this criterion asks for.

    The section selection is also what keeps WI-016's SIGNED `criteria` fence out
    of reach: that fence lives under `## Acceptance Criteria`, a different section,
    so the heading selection excludes it STRUCTURALLY rather than by a
    `criteria`-fence predicate no leaf in this tree declares.
    """
    section = select_sections(
        VAULT_FIXTURES_DOC.read_text(encoding="utf-8"),
        ["## Exploration Notes"])["## Exploration Notes"]
    normalized = _normalize(section)

    assert _normalize(CORRECTED_PHRASE) in normalized, (
        "the undeclared-key example in `docs/vault-fixtures.md`'s "
        "`## Exploration Notes` does not name `manager:` alone — a DELETION of the "
        "sentence fails this, which is the point of asserting it positively")
    assert _normalize(STALE_PHRASE) not in normalized, (
        "the stale two-key phrase survives in `## Exploration Notes`; a later "
        "reader would re-plant a key the gate now refuses")


def _check_the_live_half_is_a_committed_premise():
    """AC-3(c)'s live half, taking §12's same three rules (oracle #4).

    A premise READ, never a vault re-measured: the floor is hermetic and cannot
    reach the live vault, so the only honest form is the committed census's own
    number. The exactly-one-fence assertion comes FIRST, which is also what makes
    this oracle FAIL on a truncated span rather than narrow silently — a truncation
    yields zero fences and raises here.
    """
    section = select_sections(
        CORPUS_BASELINE_DOC.read_text(encoding="utf-8"), ["## Counts"])["## Counts"]
    fences = [block for info, block in select_fenced_blocks(section)
              if info == "yaml"]
    assert len(fences) == 1, (
        f"`## Counts` yields {len(fences)} `yaml` fences, not exactly one — a "
        f"capture that grew a second block must be RED rather than have its first "
        f"silently taken, and a TRUNCATED span yields zero and fails here")
    counts = yaml.safe_load(fences[0] + "\n")
    assert counts["introduced_by_frontmatter_carriers"] == 0, (
        f"the committed census records "
        f"{counts['introduced_by_frontmatter_carriers']} live carrier(s) of the "
        f"retired key; the unconditional ban rests on that population being EMPTY")


# --------------------------------------------------------------------------
# (d) — nothing else moves
# --------------------------------------------------------------------------

def _check_nothing_else_moves():
    """A ONE-KEY rule, not a whitelist of declared fields — and not a subtraction
    the ruling did not sign."""
    # Any other undeclared key, including the newly-swapped `manager`, is gated
    # and returned UNCHANGED.
    for key in ("manager", "nickname", "pronouns"):
        payload = {"name": "Yolvenna Skarnell", key: "Oskaline Thrandell"}
        returned = gate_write(payload, declared_type="person", whole_record=False)
        assert returned == payload, (returned, payload)

    # A `company`-declared and a `book`-declared payload carrying the key are NOT
    # refused: the ruling retires it as a PERSON frontmatter key, and silently
    # extending the ban to every entity type would be an unsigned subtraction.
    for declared_type in ("company", "book"):
        payload = {"name": "Voxleaf Ltd", RETIRED_PERSON_KEY: "Sam Tucker"}
        returned = gate_write(payload, declared_type=declared_type,
                              whole_record=False)
        assert returned == payload, (declared_type, returned)
