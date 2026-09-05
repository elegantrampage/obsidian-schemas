"""WI-021 — AC-2: every Tier-1 pattern is refused at every door.

**The fixture space is SWEPT, never sampled.** It comes from the branch-unit
table the build reifies out of `name_validation` — ten records, including
`empty` and the sentinel-exempt `pure_digit` — crossed with the seven arms of
the typed pass. A hand-picked sample is the single-literal gap this class of
criterion exists to close, and a pattern added to `NameValidator` later joins
this sweep automatically because the table is the source.

**Why the unit is the BRANCH rather than the raised key.** Nine chain branches
raise seven distinct keys — the arrow, calendar and 'Me to' branches all raise
`calendar_prefix` deliberately — so a sweep keyed on the key yields seven
fixtures and leaves two branches unexercised.

**Why arm granularity.** `write_markdown_file`'s three branches build their
frontmatter separately and converge on ONE `write_frontmatter` call, so a
uniform dict-shaped harness would satisfy a function-granularity binding while a
gate wired inside `if entity is not None:` leaves the other two arms open. The
`entity=` arm is a required fixture in its own right, and a `type: person` value
arriving through the `frontmatter=` arm never stands in for it.

**Why the conjuncts are scoped per frame.** Two of the four are properties of
the FRAME, not of the gate: at the four in-lock arms `note_lock` has already
created its sentinel home and the `.lock` before the gate can speak, with no
compensating action. So the no-stray-directory conjunct is scoped BY EQUALITY to
the three arms that bind what they serialize from their own arguments — and its
oracle NAMES artifacts computed from values the test holds, never an ambient
recursive-listing snapshot, which is red against a correct build at four of
seven arms and flips on how the fixture planted its note.

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
from obsidian_schemas.name_gate import UNDECLARED_PATTERN
from obsidian_schemas.name_validation import TIER1_BRANCHES
from obsidian_schemas.parser import parse_frontmatter
from obsidian_schemas.repositories.person import PersonRepository
from obsidian_schemas.writer import (
    model_to_frontmatter,
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
    assert_default_lock_home,
    plant_note,
)

# The typed pass iterates AC-1's derived set at arm granularity, with the
# exclusion asserted to BE exactly {D7} — the one arm that introduces no fields.
TYPED_PASS_ARMS = (D1A, D1B, D1C, D4, D5, D6, D8)
TYPED_PASS_EXCLUSION = {D7}

# The undeclared case is CONSTRUCTIBLE at exactly four arms; the exclusion is
# asserted by equality, so an arm is out for a stated structural reason and
# never because an implementation skipped it.
UNDECLARED_ARMS = (D1B, D1C, D5, D6)
UNDECLARED_EXCLUSION = {D1A, D4, D7, D8}

# The arms that can mint a path-mangled parent: they bind what they serialize
# from their OWN arguments rather than from a parse of the target, which is why
# they need no target to exist and why they are the arms the hoist reaches.
NO_STRAY_DIRECTORY_ARMS = {D1A, D1B, D1C}


def _first_firing(name: str):
    """The record the reified table fires FIRST for `name` — the chain's own
    order, driven through the table's own matcher."""
    for record in TIER1_BRANCHES:
        if record.matches(name):
            return record
    return None


def _d8_constructible():
    """D8's per-record fixture set, DERIVED from that arm's closed delta key set
    rather than hand-scoped.

    At D8 the gate's only Tier-1-evaluable subject is `name`, and that name is
    ALWAYS the target file's own stem. So: plant each record's note at
    `@<specimen>.md`, compute the subject off the path the test itself created,
    and keep the record iff that computed name still fires that record's OWN
    branch. The RULE is the derivation, not today's answer — a record added to
    the table, a specimen re-spelled, or a byte added to a branch's regex moves
    this set with no edit here.
    """
    keep, drop = [], []
    for record in TIER1_BRANCHES:
        stem = Path(f"@{record.specimen}.md").stem.lstrip("@")
        (keep if _first_firing(stem) is record else drop).append(record)
    return keep, drop


def _plant_carrier(vault: Path, stem: str = "@Carrier") -> Path:
    return plant_note(vault, stem, type="person", name=stem.lstrip("@"))


# ---------------------------------------------------------------------------
# AC-2's check
# ---------------------------------------------------------------------------

def test_every_tier1_pattern_is_refused_at_every_door():
    """AC-2's check. Zero-arg and raising, per the check contract."""
    assert_default_lock_home()

    # The sweep's source, asserted so a sampled fixture space cannot pass here.
    assert len(TIER1_BRANCHES) == 10
    assert set(TYPED_PASS_ARMS) | TYPED_PASS_EXCLUSION == {
        D1A, D1B, D1C, D4, D5, D6, D7, D8}
    assert TYPED_PASS_EXCLUSION == {D7}, (
        "the only arm excluded from the typed pass is the one that introduces "
        "no fields; every other exclusion would be an implementation's choice"
    )

    for record in TIER1_BRANCHES:
        with temp_dir() as root:
            _check_the_three_d1_arms(root / "d1", record)
        with temp_dir() as root:
            _check_the_repository_arm(root / "d4", record)
        with temp_dir() as root:
            _check_the_two_writer_doors(root / "d56", record)

    _check_the_d8_sweep_is_derived()
    with temp_dir() as root:
        _check_the_phone_sentinel_exemption(root / "sentinel")
    with temp_dir() as root:
        _check_the_undeclared_pass(root / "undeclared")
    _check_the_undeclared_exclusions_are_structural()


def _assert_refused(call, record, label):
    """Conjunct 1 (REFUSED) and conjunct 4 (TYPED REFUSAL), together."""
    try:
        call()
    except NameGateRefusal as exc:
        assert exc.pattern == record.pattern, (
            f"{label}/{record.branch_id}: expected pattern {record.pattern!r}, "
            f"got {exc.pattern!r}"
        )
        # No note content. The refused name is interpolated into
        # NameValidationError's message at every branch site, and for the
        # email-shaped branches that name IS an address.
        if record.specimen.strip():
            assert record.specimen not in str(exc)
        return exc
    raise AssertionError(
        f"{label}: {record.branch_id} ({record.specimen!r}) was NOT refused")


def _check_the_three_d1_arms(vault: Path, record):
    """D1a, D1b and D1c — three doors into one function, each a required fixture.

    Conjunct 2 (TARGET, not created) and conjunct 3 (NO STRAY DIRECTORY, scoped
    by equality to exactly these three arms) both ride here.
    """
    vault.mkdir(parents=True)
    arms = (
        (D1A, "entity=", lambda: dict(entity=Person(name=record.specimen))),
        (D1B, "frontmatter=",
         lambda: dict(frontmatter={"type": "person", "name": record.specimen})),
        (D1C, "extra_fields=",
         lambda: dict(extra_fields={"type": "person", "name": record.specimen})),
    )
    for arm, label, kwargs in arms:
        assert arm in NO_STRAY_DIRECTORY_ARMS
        # A parent the test did NOT create — the incident's own shape.
        target = vault / f"parent-{label.strip('=')}" / "note.md"
        assert not target.parent.exists()

        _assert_refused(lambda: write_markdown_file(target, **kwargs()),
                        record, label)

        # Conjunct 2: a target that did not exist is NOT created.
        assert not target.exists(), label
        # Conjunct 3: and neither is its parent, which SUBSUMES the lock home
        # and anything inside it. Named from values the test holds.
        assert not target.parent.exists(), (
            f"{label}/{record.branch_id}: the gate refused only AFTER "
            "note_lock had already minted the sentinel home"
        )
        assert not (target.parent / ".obsidian-schemas-locks").exists(), label


def _check_the_repository_arm(vault: Path, record):
    """D4 — `update_fields`, which always carries `self.type_name`."""
    vault.mkdir(parents=True)
    carrier = _plant_carrier(vault)
    before = carrier.read_bytes()
    repo = PersonRepository(vault)

    _assert_refused(
        lambda: repo.update_fields(repo.get("Carrier"),
                                   {"name": record.specimen}),
        record, "D4")

    # Conjunct 2: a target that EXISTED is byte-identical afterwards.
    assert carrier.read_bytes() == before, "D4 left the note modified"


def _check_the_two_writer_doors(vault: Path, record):
    """D5 and D6 — the public writer doors, gating the DELTA."""
    vault.mkdir(parents=True)
    carrier = _plant_carrier(vault)
    before = carrier.read_bytes()

    _assert_refused(
        lambda: update_frontmatter_field(carrier, "name", record.specimen),
        record, "D5")
    assert carrier.read_bytes() == before, "D5 left the note modified"

    _assert_refused(
        lambda: update_frontmatter_fields(carrier, {"name": record.specimen}),
        record, "D6")
    assert carrier.read_bytes() == before, "D6 left the note modified"


def _check_the_d8_sweep_is_derived():
    """D8 — RECORDED rather than raised, over the DERIVED per-record set.

    The exclusion is asserted BY EQUALITY to `{path_hostile}`, which is the one
    record `/`-freedom costs: its branch's predicate is `re.compile(r"/")`, and
    `/` is the one byte a POSIX filename component cannot hold. A record the
    predicate drops for any OTHER reason would surface here rather than being
    absorbed by an xfail, a skip or a narrowed sweep.
    """
    constructible, excluded = _d8_constructible()
    assert {record.branch_id for record in excluded} == {"path_hostile"}, (
        "the D8 exclusion set is exactly the records a filename stem cannot "
        f"raise; found {sorted(r.branch_id for r in excluded)}"
    )
    assert len(constructible) == 9

    for record in constructible:
        with temp_dir() as vault:
            note = plant_note(vault, f"@{record.specimen}",
                              type="person")
            before = note.read_bytes()
            issue = lint_vault.LintIssue(
                file_path=note, check="person_missing_name",
                severity=lint_vault.Severity.WARNING, message="planted",
                category="completeness", auto_fixable=True)

            captured = io.StringIO()
            with redirect_stderr(captured):
                outcome = lint_vault.apply_fixes([issue], vault)

            # RECORDED, not raised — and the run continues.
            assert len(outcome.refused) == 1, record.branch_id
            assert outcome.refused[0].pattern == record.pattern, record.branch_id
            assert outcome.fixed == 0, record.branch_id
            # Conjunct 2: the target is byte-identical afterwards.
            assert note.read_bytes() == before, record.branch_id
            assert "Name gate refused" in captured.getvalue()
            assert "Fix error on" not in captured.getvalue()


def _check_the_phone_sentinel_exemption(vault: Path):
    """`pure_digit_name` is CONDITIONAL — permitted when the record it is
    introduced with carries a phone (the WI-083 stub path), refused otherwise.
    Derived from the PAYLOAD, so the gate needs no new parameter."""
    vault.mkdir(parents=True)
    sentinel = "447700900123"

    # PERMITTED, at the entity arm where the WI-083 path actually writes.
    repo = PersonRepository(vault)
    path = repo.save(Person(name=sentinel, phones=[f"+{sentinel}"]))
    frontmatter, _body = parse_frontmatter(path.read_text(encoding="utf-8"))
    assert frontmatter["name"] == sentinel

    # REFUSED without the phone, through the same door.
    try:
        repo.save(Person(name=sentinel, phones=[]))
    except NameGateRefusal as exc:
        assert exc.pattern == "pure_digit_name"
    else:
        raise AssertionError("a pure-digit name with no phone must be refused")

    # At D8 the EXEMPTED direction is not constructible — no `phones` can
    # accompany the `name` in that arm's closed delta — so only the REFUSED
    # direction is asserted there, and that is stated rather than skipped.
    with temp_dir() as root:
        note = plant_note(root, f"@{sentinel}", type="person")
        issue = lint_vault.LintIssue(
            file_path=note, check="person_missing_name",
            severity=lint_vault.Severity.WARNING, message="planted",
            category="completeness", auto_fixable=True)
        captured = io.StringIO()
        with redirect_stderr(captured):
            outcome = lint_vault.apply_fixes([issue], root)
        assert len(outcome.refused) == 1
        assert outcome.refused[0].pattern == "pure_digit_name"


def _check_the_undeclared_pass(vault: Path):
    """Rule (ii): a write that introduces a `name:` WITHOUT a declared type is
    refused with its OWN refusal, regardless of whether the name matches any
    Tier-1 pattern. Untypedness is not a way through, and it is not a way in."""
    vault.mkdir(parents=True)
    clean = "Alice Example"

    for arm, label, call in (
        (D1B, "D1b", lambda t: write_markdown_file(
            t, frontmatter={"name": clean})),
        (D1C, "D1c", lambda t: write_markdown_file(
            t, extra_fields={"name": clean})),
    ):
        assert arm in UNDECLARED_ARMS
        target = vault / f"undeclared-{label}.md"
        try:
            call(target)
        except NameGateRefusal as exc:
            assert exc.pattern == UNDECLARED_PATTERN, label
        else:
            raise AssertionError(f"{label}: an undeclared name write must refuse")
        assert not target.exists(), label

    # …and the same write COMMITS once the caller declares.
    declared = vault / "declared.md"
    write_markdown_file(declared, frontmatter={"name": clean},
                        extra_fields={"type": "person"})
    assert declared.exists()

    # D5 and D6, against a note whose frontmatter carries no `type:` — AND
    # against one with NO FRONTMATTER FENCE AT ALL, which `parse_frontmatter`
    # returns as an empty dict and which therefore REACHES the gate undeclared.
    untyped = plant_note(vault, "@Untyped", name="Untyped")
    fenceless = vault / "@Fenceless.md"
    fenceless.write_text("just a body, no fence at all\n", encoding="utf-8")

    for note, label in ((untyped, "untyped"), (fenceless, "fenceless")):
        before = note.read_bytes()
        for arm, door, call in (
            (D5, "D5", lambda: update_frontmatter_field(note, "name", clean)),
            (D6, "D6", lambda: update_frontmatter_fields(note, {"name": clean})),
        ):
            assert arm in UNDECLARED_ARMS
            try:
                call()
            except NameGateRefusal as exc:
                assert exc.pattern == UNDECLARED_PATTERN, f"{door}/{label}"
            else:
                raise AssertionError(f"{door}/{label} must refuse")
            assert note.read_bytes() == before, f"{door}/{label}"


def _check_the_undeclared_exclusions_are_structural():
    """Each exclusion is out for a STATED structural reason, read from the code
    rather than asserted — a fixture at any of these would pass with or without
    the rule and read as coverage."""
    assert UNDECLARED_EXCLUSION == {D1A, D4, D7, D8}

    # D1a: the projection ALWAYS stamps `type: person`, so the undeclared case
    # is unconstructible there rather than skipped.
    projection = model_to_frontmatter(Person(name="Alice Example"))
    assert projection["type"] == "person"

    # D4: `update_fields` carries `self.type_name` unconditionally.
    with temp_dir() as vault:
        assert PersonRepository(vault).type_name == "person"

    # D7: introduces nothing at all, so there is no `name:` for rule (ii) to
    # speak to.
    assert D7 in UNDECLARED_EXCLUSION and D7 in TYPED_PASS_EXCLUSION

    # D8: `missing_type` is a non-auto-fixable ERROR, so an undeclared note
    # never reaches the serialization at that arm.
    with temp_dir() as vault:
        untyped = plant_note(vault, "@Untyped", name="Untyped")
        files = lint_vault.read_vault(vault)
        index = lint_vault.build_indexes(files)
        # Swept from the linter's OWN check registry rather than from one
        # function this test happened to name, so a check relocated between
        # categories does not silently empty this leg.
        issues = [issue
                  for check in (lint_vault.check_structural,
                                lint_vault.check_completeness)
                  for issue in check(files, index)
                  if issue.check == "missing_type"]
        assert issues, "the untyped note must raise missing_type"
        assert all(not issue.auto_fixable for issue in issues), (
            "missing_type is not auto-fixable, so D8 continues before "
            "serializing an undeclared note"
        )
        assert untyped.exists()
