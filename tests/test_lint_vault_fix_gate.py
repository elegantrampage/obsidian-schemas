"""WI-021 Task 10 — `lint_vault --fix`'s guard, delta threading, refusal record
and near-miss.

D8 is the one arm that is not a DOOR. It is a batch repair tool whose per-file
handler sits inside its own loop, so the sibling doors' `except LoudFailError:
raise` idiom is wrong here twice over: it would turn one refused note into a
vault-wide repair outage, and it filters on the hierarchy ROOT in a frame that
already raises four other subclasses of it — a lock timeout, a corrupt fence and
two commit failures, none of which can carry a `pattern`. So the refusal is its
own TYPE, the arm filters on that type and nothing wider, and it records, counts
and continues.

**What the negative legs assert, and what they deliberately do NOT.** The
discriminator is TWO EQUALITIES — the record's field set IS `{path, pattern}`
and the printed line IS a rendering of just those two. Not "the record carries a
`pattern`", which the diagnostic-minded build satisfies just as well; and NOT
"the line lacks the refused name", which is RED against the CORRECT build: the
name D8 refuses is `fpath.stem.lstrip("@")` and `path` — a field the record is
REQUIRED to carry — ends in `@<stem>.md`, so the intended build's own line
necessarily contains that name. A builder meeting that oracle red against code
they believe correct relaxes it, and the relaxation that greens it deletes the
mitigation.

Nothing here reads syntax (no `ast`): that capability is single-homed in
`tests/derivations.py`.
"""

import importlib.util
import io
from contextlib import redirect_stderr
from pathlib import Path

from tests.derivations import SCRIPTS_ROOT
from tests.support import patcher, temp_dir


def _load_lint_vault():
    """`scripts/` is not a package, so the CLI is loaded from its own path.

    Deriving the path from `SCRIPTS_ROOT` rather than spelling it keeps this in
    step with the roots every wall already uses — the suite runs from a foreign
    cwd and inside a build worktree whose path is not knowable in advance.
    """
    path = SCRIPTS_ROOT / "lint_vault.py"
    spec = importlib.util.spec_from_file_location("wi021_lint_vault", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


lint_vault = _load_lint_vault()

# The fixture the negative legs are built around: the stem IS the name the gate
# refuses, and `unknown_contact` is a pattern a POSIX filename component can
# actually raise. `path_hostile_char` deliberately is NOT used — its branch's
# predicate is `re.compile(r"/")`, and a filename component cannot contain `/`,
# so no D8 fixture could ever make that leg green.
REFUSED_STEM = "Unknown Contact Zeta-9"
REFUSED_PATTERN = "unknown_contact"


def _issue(path: Path, check: str):
    return lint_vault.LintIssue(
        file_path=path,
        check=check,
        severity=lint_vault.Severity.WARNING,
        message="planted",
        category="completeness",
        auto_fixable=True,
    )


def _plant(vault: Path, stem: str, body: str) -> Path:
    path = vault / f"{stem}.md"
    path.write_text(body, encoding="utf-8")
    return path


def _typed_note_without_a_name(vault: Path, stem: str) -> Path:
    return _plant(vault, stem, "---\ntype: person\n---\n\n## Timeline\n")


def test_lint_vault_fix_guards_threads_and_records_refusals():
    """Task 10's verify. Zero-arg and raising, per the check contract."""
    with temp_dir() as root:
        _check_the_guard_fires_above_the_lock(root / "vanished")
    with temp_dir() as root:
        _check_the_delta_carries_only_the_keys_the_branches_assigned(root / "delta")
    with temp_dir() as root:
        _check_a_refusal_is_recorded_counted_and_the_run_continues(root / "refuse")
    with temp_dir() as root:
        _check_the_two_equalities(root / "equalities")
    with temp_dir() as root:
        _check_the_near_miss_produces_no_refusal_record(root / "nearmiss")


def _check_the_guard_fires_above_the_lock(vault: Path):
    """A note deleted between the walk and this pass.

    Its assertable properties are the printed `Fix error on …` line naming a
    `FileNotFoundError` and the ABSENCE of the sentinel directory and the
    `.lock` — and NOT a raise out of `apply_fixes`, which its own
    `except Exception` (inside the per-file loop) absorbs, exactly as Design §6
    item 1 says. A leg reaching for `pytest.raises` here is red against the
    intended build, and its author's next move is to relax the guard until it
    fires.
    """
    vault.mkdir(parents=True)
    vanished = vault / "gone" / "@Ghost.md"
    assert not vanished.parent.exists()

    captured = io.StringIO()
    with redirect_stderr(captured):
        outcome = lint_vault.apply_fixes(
            [_issue(vanished, "person_missing_name")], vault)

    assert outcome.fixed == 0
    assert outcome.refused == ()
    # The existing per-file handler renders the exception's MESSAGE, not its
    # type, so the oracle is built from the message the guard raises and the
    # path the test created — not from the class name.
    printed = [line for line in captured.getvalue().splitlines() if line]
    assert printed == [
        f"  Fix error on {vanished.name}: File not found: {vanished}"
    ], printed

    # THE BUILD-PRODUCED ARTIFACTS, and they are the two that are ABSENT: the
    # guard runs above `note_lock`, whose outermost acquisition would otherwise
    # `mkdir` the sentinel home at the vanished note's own parent and drop a
    # `.lock` in it before `read_note` ever failed.
    assert not vanished.parent.exists(), (
        "the guard must fire ABOVE the lock — a vanished target must not get a "
        "sentinel directory minted for it"
    )
    assert not (vault / "gone" / ".obsidian-schemas-locks").exists()


def _check_the_delta_carries_only_the_keys_the_branches_assigned(vault: Path):
    """The closed key set, pinned from the RUN rather than from the spec.

    `apply_fixes` has exactly two branches that assign into `fm`, so the delta
    can carry no third key without an edit to that frame — which means the
    identifier rules and the phone-sentinel exemption have NO SUBJECT here. That
    vacuity is asserted from the captured delta so a later branch widening the
    frame turns it RED instead of leaving it silently true.
    """
    vault.mkdir(parents=True)
    named = _plant(
        vault, "@Dave Smith",
        "---\ntype: person\nname: Dave Smith\nauto_created: 'true'\n---\n\n#x\n")
    missing = _typed_note_without_a_name(vault, "@Alice Example")

    seen = []
    real_gate = lint_vault.gate_write

    def recording_gate(introduced, **kwargs):
        seen.append((dict(introduced), kwargs))
        return real_gate(introduced, **kwargs)

    with patcher() as patch:
        patch.setattr(lint_vault, "gate_write", recording_gate)
        outcome = lint_vault.apply_fixes(
            [_issue(named, "field_type_mismatch"),
             _issue(missing, "person_missing_name")], vault)

    assert outcome.fixed == 2 and outcome.refused == ()
    assert len(seen) == 2, "one gate call per file, unconditional in the frame"

    closed = {"auto_created", "name"}
    for introduced, kwargs in seen:
        assert set(introduced) <= closed, (
            f"D8's delta key set is closed at {sorted(closed)}; found "
            f"{sorted(introduced)}"
        )
        # …so no identifier field reaches the gate here at all, and the two
        # identifier sweeps quantify over an empty set at this arm.
        assert not ({"emails", "phones", "aliases"} & set(introduced))
        assert kwargs["declared_type"] == "person"
        assert kwargs["whole_record"] is False

    assert {frozenset(introduced) for introduced, _ in seen} == {
        frozenset({"auto_created"}), frozenset({"name"})}

    # And the run really did repair both notes.
    assert "auto_created: true" in named.read_text()
    assert "name: Alice Example" in missing.read_text()


def _check_a_refusal_is_recorded_counted_and_the_run_continues(vault: Path):
    vault.mkdir(parents=True)
    refused_note = _typed_note_without_a_name(vault, f"@{REFUSED_STEM}")
    healthy = _typed_note_without_a_name(vault, "@Alice Example")

    captured = io.StringIO()
    with redirect_stderr(captured):
        outcome = lint_vault.apply_fixes(
            [_issue(refused_note, "person_missing_name"),
             _issue(healthy, "person_missing_name")], vault)

    assert len(outcome.refused) == 1, "the refusal is COUNTED"
    assert outcome.fixed == 1, "and the run CONTINUES to the next file"
    assert "name: Alice Example" in healthy.read_text()

    # The refused note is left as it was — no partial repair.
    assert "name:" not in refused_note.read_text()

    printed = captured.getvalue()
    assert "Name gate refused" in printed
    assert "Fix error on" not in printed, (
        "the refusal line must be DISTINGUISHABLE from the IO-failure channel"
    )


def _check_the_two_equalities(vault: Path):
    """M3's discriminator, and the whole of it.

    Both equalities are RED under the diagnostic-minded build that carries ANY
    third value — `fm.get("name")`, the local `name`, `str(exc)`, or
    `str(exc.__context__)` (which renders the branch's own `{name!r}`
    interpolation) — because equality is total over "carries anything else".
    """
    vault.mkdir(parents=True)
    refused_note = _typed_note_without_a_name(vault, f"@{REFUSED_STEM}")

    captured = io.StringIO()
    with redirect_stderr(captured):
        outcome = lint_vault.apply_fixes(
            [_issue(refused_note, "person_missing_name")], vault)

    assert len(outcome.refused) == 1
    record = outcome.refused[0]

    # (1) THE RECORD'S FIELD SET, by EQUALITY — never "contains a pattern".
    assert set(record._fields) == {"path", "pattern"}, (
        f"the record carries {sorted(record._fields)}; the field set is CLOSED "
        "at exactly the operator's own path and the source-literal pattern"
    )
    assert record.pattern == REFUSED_PATTERN
    assert record.path == refused_note

    # (2) THE PRINTED LINE, by EQUALITY, built from the path the test created
    # and the source literal — so the oracle is derived from what the fixture
    # holds rather than re-spelled.
    expected = f"  Name gate refused {refused_note}: {REFUSED_PATTERN}"
    lines = [line for line in captured.getvalue().splitlines() if line]
    assert lines == [expected], (
        f"expected exactly {expected!r}, got {lines!r}"
    )


def _check_the_near_miss_produces_no_refusal_record(vault: Path):
    """One line, and it is what stops the refusal arm passing by matching every
    failure: the same run over a note whose frontmatter fence does not close
    raises a `FrontmatterParseError` — a sibling leaf of the SAME hierarchy root
    — and must produce NO refusal record."""
    vault.mkdir(parents=True)
    unclosed = _plant(vault, "@Broken Fence",
                      "---\ntype: person\nname: Broken Fence\n\nno closing fence\n")

    captured = io.StringIO()
    with redirect_stderr(captured):
        outcome = lint_vault.apply_fixes(
            [_issue(unclosed, "person_missing_name")], vault)

    assert outcome.refused == (), (
        "a corrupt fence is not a gate refusal. A handler filtering on the "
        "hierarchy ROOT would record it as one — and the refusal count would "
        "then be greenable on a build with no gate at this arm at all."
    )
    assert outcome.fixed == 0
    printed = captured.getvalue()
    assert "Fix error on" in printed
    assert "Name gate refused" not in printed


def test_the_fix_outcome_surfaces_both_counts():
    """The interface change: `apply_fixes` returns a two-field record and the
    CLI surfaces the refusal count beside the fixed count."""
    assert lint_vault.FixOutcome._fields == ("fixed", "refused")
    empty = lint_vault.apply_fixes([], Path("/nonexistent"))
    assert empty.fixed == 0 and empty.refused == ()
