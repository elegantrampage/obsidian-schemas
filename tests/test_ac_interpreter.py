"""WI-021 — the standing wall over the interpreter bridge (`tests/ac_interpreter.py`).

The property: **every acceptance criterion of this item passes when its check is
run the way the conveyor runs it — the bootstrap argv shape, from the project root,
under an interpreter that does NOT carry the project's site-packages.** That last
clause is the one the floor cannot otherwise reach: the floor runs everything under
`.venv/bin/python`, where the bridge is a no-op, so a check module that lost its
guard would stay green here and go red in the battery, which is exactly the split
this module exists to close.

The foreign interpreter is `sys.executable -S`. `-S` skips `site`, so the venv's
site-packages are NOT on the child's path and `import pydantic` fails — the same
observable condition as the battery's own interpreter (workshop's venv, which has
no pydantic), reproduced hermetically with no second interpreter to find and no
assumption about what is installed where. `-c` still puts the cwd on `sys.path`, so
`import tests.…` resolves exactly as it does under the conveyor.

The criterion set is DERIVED from this item's `criteria` fences rather than listed,
so an AC added later joins this wall on the day it is written, and each name is
resolved to its module by the conveyor's own discovery rule (the unique top-level
`def <check>(` across `tests/*.py`) rather than by a table kept in step by hand.

CORPUS_COUPLING: pins `docs/write-door-bypasses.md`'s `criteria` fences (the
`check:` key inside them) to consume the set of check names the conveyor's battery
will run for WI-021. A rename of that doc, or a fence with no `check:`, is a loud
failure here, never a silent empty sweep.

Nothing here reads syntax (no `ast`): that capability is single-homed in
`tests/derivations.py`.
"""

import subprocess
import sys
from pathlib import Path

from tests.ac_interpreter import DELEGATION_SENTINEL

ROOT = Path(__file__).resolve().parent.parent
TESTS_ROOT = ROOT / "tests"
WORK_ITEM_DOC = ROOT / "docs" / "write-door-bypasses.md"

# The conveyor's child program, byte-for-byte in SHAPE: module path and check name
# arrive as argv, never interpolated into the source (src/stage_advancer.py,
# BOOTSTRAP_SRC). Copied rather than imported because workshop is not importable
# from this project — which is why the wall drives it by EXECUTION below, and why a
# drift in the shape shows up as a real red here rather than as a stale comment.
BOOTSTRAP_SRC = (
    "import importlib.util, sys\n"
    "p, name = sys.argv[1], sys.argv[2]\n"
    "spec = importlib.util.spec_from_file_location('_wi041_check', p)\n"
    "mod = importlib.util.module_from_spec(spec)\n"
    "spec.loader.exec_module(mod)\n"
    "getattr(mod, name)()\n"
)


def criterion_checks(doc: Path) -> list[str]:
    """Every `check:` named inside a ```criteria fence of `doc`, in document order.

    Fence-scoped on purpose: the `check:` key is only a criterion's when it is
    inside the fence the conveyor parses, and this document quotes the key in prose
    as well. Raises when the document is missing — an unfindable doc must not read
    as "this item has no criteria"."""
    text = doc.read_text()
    checks, in_fence = [], False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("```"):
            in_fence = stripped == "```criteria"
            continue
        if in_fence and stripped.startswith("check:"):
            checks.append(stripped.split(":", 1)[1].strip())
    return checks


def check_module(check: str) -> Path:
    """The one `tests/test_*.py` whose source defines `def <check>(` — the
    conveyor's discovery rule (one level, no rglob, unique match or loud)."""
    needle = f"def {check}("
    matches = [p for p in sorted(TESTS_ROOT.glob("test_*.py"))
               if needle in p.read_text()]
    if len(matches) != 1:
        raise AssertionError(
            f"check '{check}' resolves to {len(matches)} module(s) under "
            f"{TESTS_ROOT} ({[m.name for m in matches]}) — the conveyor's battery "
            f"refuses anything but exactly one")
    return matches[0]


def run_foreign(module: Path, check: str) -> subprocess.CompletedProcess:
    """Run one check the way the battery does, under an interpreter without the
    project's site-packages. cwd is the project root, as the conveyor's is."""
    return subprocess.run(
        [sys.executable, "-S", "-c", BOOTSTRAP_SRC, str(module), check],
        cwd=str(ROOT), capture_output=True, text=True, timeout=120)


def test_every_acceptance_criterion_passes_under_the_conveyors_interpreter():
    """AC battery parity: each criterion's check, run in the conveyor's shape under
    an interpreter missing the project's deps, exits 0 — and got there by
    delegating, not by some accident of the environment."""
    checks = criterion_checks(WORK_ITEM_DOC)
    assert checks, (
        f"no `check:` key found inside any ```criteria fence of {WORK_ITEM_DOC} — "
        f"the sweep would be vacuous")

    failures = []
    for check in checks:
        module = check_module(check)
        proc = run_foreign(module, check)
        if proc.returncode != 0:
            failures.append(
                f"{check} ({module.name}) exited {proc.returncode}\n"
                f"--- stdout ---\n{proc.stdout[-2000:]}\n"
                f"--- stderr ---\n{proc.stderr[-2000:]}")
        elif "[ac_interpreter]" not in proc.stderr:
            failures.append(
                f"{check} ({module.name}) exited 0 WITHOUT delegating — the "
                f"foreign interpreter imported the project's deps, so this run "
                f"proves nothing about the battery's conditions")
    assert not failures, (
        f"{len(failures)} of {len(checks)} criteria fail under the conveyor's "
        f"interpreter:\n\n" + "\n\n".join(failures))


def test_a_failing_delegated_check_is_red_not_silently_green():
    """The near-miss control: the bridge must not pass by exiting 0 whatever the
    child did. A name the module does not define is a check the battery must call
    RED — under the same delegation, through the same argv shape."""
    checks = criterion_checks(WORK_ITEM_DOC)
    module = check_module(checks[0])
    proc = run_foreign(module, "test_this_check_does_not_exist_anywhere")
    assert proc.returncode != 0, (
        f"a nonexistent check delegated to {module.name} exited 0 — the bridge is "
        f"reporting green for a run that proved nothing:\n{proc.stdout[-2000:]}")
    assert "[ac_interpreter]" in proc.stderr, (
        f"the failing run did not delegate, so it did not exercise the bridge:\n"
        f"{proc.stderr[-2000:]}")


def test_the_bridge_is_a_no_op_under_the_projects_own_interpreter():
    """The floor's own condition: with the deps importable, `ensure_project_
    interpreter` returns and delegates nothing — no subprocess, no sentinel, no
    behaviour change to the 654-case floor it sits in front of."""
    import os

    from tests.ac_interpreter import (
        ensure_project_interpreter,
        runtime_deps_importable,
    )

    assert runtime_deps_importable(), (
        "the floor is running without the project's runtime deps — the floor "
        "command is `.venv/bin/python -m pytest tests -q` (CLAUDE.md)")
    assert DELEGATION_SENTINEL not in os.environ, (
        f"{DELEGATION_SENTINEL} is set in the floor's own environment; a delegated "
        f"child's marker has leaked into the parent run")
    ensure_project_interpreter(__file__)      # returns, or this process is replaced
