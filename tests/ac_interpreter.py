"""The interpreter bridge for an acceptance criterion's `kind: test` check.

WI-021. This module is NOT a test module (its name does not match `test_*.py`, so
pytest never collects it). It exists for one reason, recorded here because the
failure it closes is invisible from inside the suite:

**The conveyor runs a `kind: test` check under an interpreter it chooses, and that
interpreter is not necessarily this project's.** The check battery discovers the
check by SOURCE scan and then runs exactly

    <some python> -c "<importlib bootstrap>" <module path> <check name>

with cwd set to the project (`src/stage_advancer.py`, `BOOTSTRAP_SRC` /
`build_check_argv`). The interpreter defaults to the ADVANCER's `sys.executable` and
is only this project's venv when the driver passes `--ac-python`. When it is not,
`import pydantic` fails at the check module's very first package import and every
criterion of this item reports `exit 1: ModuleNotFoundError: No module named
'pydantic'` — a red that says nothing whatever about the property the criterion
asserts. That is the exact battery output WI-021's first build attempt drew, on
five-of-five criteria, with a floor that was green in the same tree.

Every criterion this project has shipped before WI-021 happened to be a SOURCE
sweep (`tests/derivations.py` imports `ast` and `pathlib` and nothing else), so the
gap had never been reached: WI-021 is the first item whose criteria must EXECUTE the
library they gate.

The bridge: a check module calls `ensure_project_interpreter(__file__)` as its first
statement, ahead of every package import.

- Under the floor command (`.venv/bin/python -m pytest tests -q`) and under CI's
  `pip install -e ".[dev]"` the project's runtime deps are importable, and the call
  is a no-op — the collected module then imports and runs byte-identically to
  before, so nothing about the floor changes.
- Under a foreign interpreter it does NOT return: it re-execs the SAME check under
  the project's own interpreter (`<root>/.venv/bin/python`, which
  `pipeline-runners.yaml` already seeds into the battery's worktree via `seed_deps`
  for exactly this reason) as a one-node `pytest` run, so the child's exit status
  and output ARE the check's. There is no second copy of the assertions and no
  reporting to plumb.

Fail-closed everywhere: an unrecognized invocation shape, a missing interpreter, or
a delegation that lands on an interpreter still missing the deps RAISES with the
command a human can run by hand. It never degrades to "skipped" or to a green.
"""

import importlib.util
import os
import re
import sys
from pathlib import Path

# Set in the delegated child's environment. Its ONLY job is to make an impossible
# delegation loud on the second hop instead of forking forever.
DELEGATION_SENTINEL = "OBSIDIAN_SCHEMAS_AC_DELEGATED"

# The distribution whose importability decides the question. It is a RUNTIME
# dependency of the package (`pyproject.toml` -> dependencies), imported by
# `obsidian_schemas/models.py` at the top of the package's own `__init__`, so it is
# the first thing a check module's first import needs and the first thing a foreign
# interpreter lacks. `find_spec` answers the question without executing anything.
RUNTIME_DEP = "pydantic"

# The conveyor's child argv shape: `python -c SRC <module path> <check name>` lands
# as sys.argv == ['-c', <module path>, <check name>].
_BOOTSTRAP_ARGV0 = "-c"
_CHECK_NAME = re.compile(r"^test_[A-Za-z0-9_]+$")   # CHECK_NAME_PATTERN, conveyor-side


def runtime_deps_importable() -> bool:
    """True when the running interpreter can import the package's runtime deps."""
    return importlib.util.find_spec(RUNTIME_DEP) is not None


def project_root(module_file: str) -> Path:
    """The repo root, from a module living directly under `tests/`."""
    return Path(module_file).resolve().parent.parent


def project_interpreter(root: Path) -> Path:
    """The interpreter to delegate to: the project's venv python when it is there,
    else the running one.

    `<root>/.venv/bin/python` is the floor command's interpreter (CLAUDE.md) and the
    dep the cage seeds into the battery's worktree. The fallback is not a
    convenience: on a checkout with no venv (CI installs into the ambient
    environment) the only interpreter that can possibly have the deps IS the running
    one — it reached here only because site-packages were disabled or absent, and
    re-running it without that handicap is the whole delegation. A fallback that
    cannot import the deps either is caught by DELEGATION_SENTINEL on the next hop
    and raised, never looped.
    """
    venv_python = root / ".venv" / "bin" / "python"
    return venv_python if venv_python.is_file() else Path(sys.executable)


def check_name_from_argv(module_file: str) -> str | None:
    """The check name the conveyor handed this process, or None if this is not the
    conveyor's bootstrap invocation. Never guesses: the module path in argv must be
    THIS module and the name must satisfy the conveyor's own name pattern."""
    if len(sys.argv) != 3 or sys.argv[0] != _BOOTSTRAP_ARGV0:
        return None
    try:
        if Path(sys.argv[1]).resolve() != Path(module_file).resolve():
            return None
    except OSError:
        return None
    return sys.argv[2] if _CHECK_NAME.match(sys.argv[2]) else None


def delegated_argv(python: Path, module_file: str, check: str) -> list[str]:
    """The child command: ONE pytest node, run by the project's interpreter.

    pytest rather than a re-spelled importlib bootstrap, so the delegated check runs
    under the project's own `[tool.pytest.ini_options]` — the same conditions as the
    floor — and so this repo carries no copy of the conveyor's private bootstrap
    source to drift against. Exit 0 iff the one node passed.
    """
    node = f"{Path(module_file).resolve()}::{check}"
    return [str(python), "-m", "pytest", node, "-q", "--no-header",
            "-p", "no:cacheprovider"]


def ensure_project_interpreter(module_file: str) -> None:
    """No-op when the running interpreter has the package's runtime deps; otherwise
    REPLACES this process with the same check run under the project's interpreter.

    Call it as the first statement of a check module, ahead of every package import.
    """
    if runtime_deps_importable():
        return

    root = project_root(module_file)
    python = project_interpreter(root)
    hand_run = f"{root / '.venv' / 'bin' / 'python'} -m pytest {module_file} -q"

    if os.environ.get(DELEGATION_SENTINEL):
        raise RuntimeError(
            f"{Path(module_file).name}: delegated to {python} and '{RUNTIME_DEP}' is "
            f"STILL not importable — the project's dependencies are not installed for "
            f"that interpreter. Install them, or run by hand: {hand_run}")

    check = check_name_from_argv(module_file)
    if check is None:
        raise RuntimeError(
            f"{Path(module_file).name} needs the project's interpreter: "
            f"'{RUNTIME_DEP}' is not importable under {sys.executable}, and this is "
            f"not the conveyor's `-c <module> <check>` invocation, so there is no "
            f"single check to delegate. Run: {hand_run}")

    argv = delegated_argv(python, module_file, check)
    sys.stderr.write(
        f"[ac_interpreter] '{RUNTIME_DEP}' absent under {sys.executable}; "
        f"re-running {check} under {python}\n")
    sys.stderr.flush()
    os.execve(argv[0], argv, {**os.environ, DELEGATION_SENTINEL: "1"})
