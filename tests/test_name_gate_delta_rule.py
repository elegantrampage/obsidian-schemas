"""WI-021 — AC-3: a legacy-dirty name stays writable for unrelated writes.

**The delta rule, and why the item is invalid without it.** The gate judges what
a write INTRODUCES, never the stored record. Without that, this item bricks
every note whose name has been Tier-1 dirty since before it existed — and it
bricks the repair tools whose whole job is to clean them. Remedy-is-the-disease.

**Where the distinction is CONSTRUCTIBLE, which is why the exclusion set is
asserted by equality.** The excluded arms are exactly `{D1a, D1b, D1c}`: their
delta IS the whole record, so a stored-dirty note cannot be written through them
without re-introducing its own name, and refusal is the correct answer AC-2
already asserts. Every other arm must COMMIT. The two that matter most are D5
and D6 — `update_frontmatter_field`'s delta is two loose parameters while the
stored record sits bound one line above the natural call site, so a build gating
the merged record there greens AC-1's whole per-arm triple, greens AC-2 (a
refusal oracle cannot tell refused-because-INTRODUCED from
refused-because-STORED) and greens AC-4, while making that door permanently
refuse every legacy-dirty note.

**Every fixture here is SYNTHETIC, planted with `Path.write_text`, and the
reason is one line:** the only live Tier-1-dirty names are two WI-083
phone-sentinel stubs which the payload rule permits anyway, and the archived
ones sit under directories `SKIP_DIRS` bars from `lint_vault --fix` and the
root-only glob bars from `update_fields` — so no door in this package can be
exercised against the live population at all.

Nothing here reads syntax (no `ast`): that capability is single-homed in
`tests/derivations.py`.
"""

# FIRST, ahead of every package import: the conveyor may run this module's check
# under an interpreter that is not this project's, where the imports below cannot
# resolve. A no-op under the floor command and under CI (WI-021; see
# `tests/ac_interpreter.py` for the failure this closes).
from tests.ac_interpreter import ensure_project_interpreter

ensure_project_interpreter(__file__)

import io  # noqa: E402 — everything below runs only once the interpreter is right
from contextlib import redirect_stderr
from pathlib import Path

from obsidian_schemas.errors import NameGateRefusal
from obsidian_schemas.models import Person
from obsidian_schemas.parser import parse_frontmatter
from obsidian_schemas.repositories.person import PersonRepository
from obsidian_schemas.writer import (
    roundtrip_file,
    update_frontmatter_field,
    update_frontmatter_fields,
    write_markdown_file,
)
from tests.support import temp_dir
from tests.test_lint_vault_fix_gate import lint_vault
from tests.test_name_gate_wall import (
    D1A,
    D1B,
    D1C,
    D4,
    D5,
    D6,
    D7,
    D8,
    plant_note,
)

STORED_DIRTY = "Me to David Field"
DERIVED_SET = {D1A, D1B, D1C, D4, D5, D6, D7, D8}

# Asserted BY EQUALITY, so an arm is out of the preservation property only for a
# stated structural reason and never because an implementation skipped it.
PRESERVATION_EXCLUSION = {D1A, D1B, D1C}
PRESERVING_ARMS = DERIVED_SET - PRESERVATION_EXCLUSION


def _plant_dirty(vault: Path, **extra) -> Path:
    return plant_note(vault, f"@{STORED_DIRTY}", type="person",
                      name=STORED_DIRTY, **extra)


def test_a_legacy_dirty_name_stays_writable_for_unrelated_writes():
    """AC-3's check. Zero-arg and raising, per the check contract."""
    assert PRESERVATION_EXCLUSION == {D1A, D1B, D1C}
    assert PRESERVING_ARMS == {D4, D5, D6, D7, D8}
    assert PRESERVING_ARMS | PRESERVATION_EXCLUSION == DERIVED_SET, (
        "the property is bound to AC-1's derived set, so a ninth arm added "
        "later joins this criterion automatically"
    )

    with temp_dir() as root:
        _check_the_excluded_arms_refuse_and_say_why(root / "excluded")
    with temp_dir() as root:
        _check_the_repository_arm_commits(root / "d4")
    with temp_dir() as root:
        _check_the_delta_not_record_pin_at_d5_and_d6(root / "d56")
    with temp_dir() as root:
        _check_roundtrip_commits(root / "d7")
    with temp_dir() as root:
        _check_lint_vault_can_still_repair_a_dirty_note(root / "d8")
    with temp_dir() as root:
        _check_the_body_section_append_still_commits(root / "body")
    with temp_dir() as root:
        _check_the_phone_sentinel_stays_writable(root / "sentinel")


def _check_the_excluded_arms_refuse_and_say_why(vault: Path):
    """The three D1 arms are excluded because their delta IS the whole record:
    there is no way to write a stored-dirty note through them WITHOUT
    re-introducing its name, so refusal is correct rather than a gap."""
    vault.mkdir(parents=True)
    for label, kwargs in (
        ("D1a", dict(entity=Person(name=STORED_DIRTY, company="Acme"))),
        ("D1b", dict(frontmatter={"type": "person", "name": STORED_DIRTY,
                                  "company": "Acme"})),
        ("D1c", dict(extra_fields={"type": "person", "name": STORED_DIRTY,
                                   "company": "Acme"})),
    ):
        target = vault / f"@{label}.md"
        try:
            write_markdown_file(target, **kwargs)
        except NameGateRefusal as exc:
            assert exc.pattern == "calendar_prefix", label
        else:
            raise AssertionError(f"{label} re-introduces the name; it must refuse")


def _check_the_repository_arm_commits(vault: Path):
    vault.mkdir(parents=True)
    note = _plant_dirty(vault)
    repo = PersonRepository(vault)
    person = repo.get(STORED_DIRTY)
    assert person is not None, "the stored-dirty note must still LOAD"

    repo.update_fields(person, {"company": "Acme"})
    frontmatter, _body = parse_frontmatter(note.read_text(encoding="utf-8"))
    assert frontmatter["company"] == "Acme"
    assert frontmatter["name"] == STORED_DIRTY, "the stored name is untouched"


def _check_the_delta_not_record_pin_at_d5_and_d6(vault: Path):
    """THE test that goes RED for a build gating the merged record."""
    vault.mkdir(parents=True)
    note = _plant_dirty(vault)

    assert update_frontmatter_field(note, "company", "Acme") is True, (
        "update_frontmatter_field must gate {field_name: field_value}, the "
        "delta CONSTRUCTED in the frame — never the record parsed one line "
        "above the call site"
    )
    assert update_frontmatter_fields(note, {"role": "vip"}) is True, (
        "update_frontmatter_fields must gate the caller's `updates`, never the "
        "merged record"
    )
    frontmatter, _body = parse_frontmatter(note.read_text(encoding="utf-8"))
    assert frontmatter["company"] == "Acme"
    assert frontmatter["role"] == "vip"
    assert frontmatter["name"] == STORED_DIRTY

    # And the same door still refuses when the write INTRODUCES that name — a
    # refusal oracle alone cannot tell these two apart, which is why both
    # directions are asserted at the same arm.
    for door, call in (
        ("D5", lambda: update_frontmatter_field(note, "name", STORED_DIRTY)),
        ("D6", lambda: update_frontmatter_fields(note, {"name": STORED_DIRTY})),
    ):
        try:
            call()
        except NameGateRefusal as exc:
            assert exc.pattern == "calendar_prefix", door
        else:
            raise AssertionError(f"{door} must refuse an INTRODUCED dirty name")


def _check_roundtrip_commits(vault: Path):
    vault.mkdir(parents=True)
    note = _plant_dirty(vault)
    roundtrip_file(note)
    frontmatter, _body = parse_frontmatter(note.read_text(encoding="utf-8"))
    assert frontmatter["name"] == STORED_DIRTY


def _check_lint_vault_can_still_repair_a_dirty_note(vault: Path):
    """D8 is the tool whose JOB is repairing these notes, so bricking it would
    be the sharpest form of remedy-is-the-disease.

    Constructible through `field_type_mismatch` ONLY: that delta is
    `{auto_created: <bool>}` and introduces no name, so a stored-dirty note
    commits. The `person_missing_name` route would re-introduce the stem AS the
    name, which is AC-2's direction and not this one.
    """
    vault.mkdir(parents=True)
    note = _plant_dirty(vault, auto_created="true")
    issue = lint_vault.LintIssue(
        file_path=note, check="field_type_mismatch",
        severity=lint_vault.Severity.WARNING, message="planted",
        category="completeness", auto_fixable=True)

    captured = io.StringIO()
    with redirect_stderr(captured):
        outcome = lint_vault.apply_fixes([issue], vault)

    assert outcome.refused == (), captured.getvalue()
    assert outcome.fixed == 1
    frontmatter, _body = parse_frontmatter(note.read_text(encoding="utf-8"))
    assert frontmatter["auto_created"] is True, "the repair committed"
    assert frontmatter["name"] == STORED_DIRTY, "the dirty name is untouched"


def _check_the_body_section_append_still_commits(vault: Path):
    """A BEHAVIOURAL example, named as one: a body-section append is a Class-2
    pass-through — it is not an arm and not a member of the derived set — and it
    still commits against a stored-dirty note."""
    vault.mkdir(parents=True)
    note = _plant_dirty(vault)
    repo = PersonRepository(vault)
    person = repo.get(STORED_DIRTY)

    repo.append_to_timeline(person, "- a later note")
    body = note.read_text(encoding="utf-8")
    assert "a later note" in body
    frontmatter, _body = parse_frontmatter(body)
    assert frontmatter["name"] == STORED_DIRTY


def _check_the_phone_sentinel_stays_writable(vault: Path):
    """Under the delta rule an entity write's name is ALWAYS the delta, so
    without this leg every subsequent entity write for a WI-083 stub would be
    refused."""
    vault.mkdir(parents=True)
    sentinel = "+447700900123"
    repo = PersonRepository(vault)
    person = Person(name=sentinel, phones=[sentinel])
    path = repo.save(person)

    # A SECOND entity write for the same stub still commits.
    person.company = "Acme"
    repo.save(person)
    frontmatter, _body = parse_frontmatter(path.read_text(encoding="utf-8"))
    assert frontmatter["name"] == sentinel
    assert frontmatter["company"] == "Acme"

    # …while introducing that name WITHOUT the phone is refused.
    plain = plant_note(vault, "@Plain", type="person", name="Plain")
    try:
        update_frontmatter_fields(plain, {"name": sentinel})
    except NameGateRefusal as exc:
        assert exc.pattern == "pure_digit_name"
    else:
        raise AssertionError(
            "a pure-digit name introduced without a phone must be refused")
