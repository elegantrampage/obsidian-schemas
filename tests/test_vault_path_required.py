"""WI-024 invariant tests: a vault must be configured, never defaulted.

The property under test is that a repository can only ever bind to a vault the
caller or the environment named explicitly. Omission — and its blank twins, in
either accepted argument type — must raise at construction rather than silently
binding a write-capable repository to a live vault or to the current working
directory.

Hermeticity note (WI-024 P5): every test that asserts unconfigured behaviour
scrubs OBSIDIAN_VAULT_PATH. The repo has no conftest.py and no test may
depend on the ambient environment — on Dave's machine the variable IS set, so a
test reading it would pass for the wrong reason there and fail elsewhere.

Fixture-free note: the four tests named by the `check:` field of a `criteria`
fence (AC-1, AC-3, AC-4, and the scan/artifact checks) MUST be callable with no
arguments. The pipeline's acceptance battery imports this module and calls each
named check directly — `getattr(mod, name)()` — outside pytest, so a
parametrised or fixture-taking AC test raises TypeError before it can assert
anything. Env manipulation therefore goes through the `_scrubbed_env` /
`_env_set` context managers rather than `monkeypatch`, and the argument shapes
are iterated inside the test instead of via `@pytest.mark.parametrize`.
Non-AC supporting tests are free to use fixtures.
"""

import os
import re
import subprocess
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path

import pytest

import obsidian_schemas.repositories.base
from obsidian_schemas import (
    BookRepository,
    CompanyRepository,
    MeetingRepository,
    PersonRepository,
    VaultPathNotConfiguredError,
)

ENV_VAR = "OBSIDIAN_VAULT_PATH"
REPO_ROOT = Path(__file__).parent.parent

# A sentinel distinguishing "call the constructor with no argument at all" from
# "pass None explicitly" — both must raise, but only the former exercises the
# defaulted-parameter path.
NO_ARG = object()

# Every argument shape that names no vault. Stated as a sample of the property
# "absent, or reduces to an empty/whitespace path, whatever type it arrives as"
# — NOT as the definition. Path("") is already Path(".") before __init__ sees
# it, which is why an isinstance(str)-gated guard would let it through.
UNCONFIGURED_ARGS = [
    NO_ARG,
    None,
    "",
    "   ",
    Path(""),
    Path("   "),
    ".",
    Path("."),
]

ALL_REPOSITORIES = [
    PersonRepository,
    CompanyRepository,
    MeetingRepository,
    BookRepository,
]


def _construct(repo_cls, arg):
    """Construct *repo_cls*, passing *arg* only when it is a real argument."""
    if arg is NO_ARG:
        return repo_cls()
    return repo_cls(arg)


@contextmanager
def _env_set(value):
    """Set OBSIDIAN_VAULT_PATH to *value*, or remove it when *value* is None.

    A fixture-free stand-in for monkeypatch.setenv/delenv, so the AC-named
    tests stay zero-argument (see the module docstring). Restores the previous
    state on the way out, including the case where it was originally absent.
    """
    previous = os.environ.get(ENV_VAR)
    try:
        if value is None:
            os.environ.pop(ENV_VAR, None)
        else:
            os.environ[ENV_VAR] = value
        yield
    finally:
        if previous is None:
            os.environ.pop(ENV_VAR, None)
        else:
            os.environ[ENV_VAR] = previous


def _scrubbed_env():
    """The env with no vault configured at all."""
    return _env_set(None)


@contextmanager
def _no_filesystem():
    """Make the filesystem surfaces the repositories use explode if reached.

    glob(), exists() and mkdir() are the three doors: load() reaches exists()
    before glob(), and the writer is the mkdir surface — patching glob alone
    would pass vacuously. Fixture-free for the same reason as _env_set.
    """
    originals = {name: getattr(Path, name) for name in ("glob", "exists", "mkdir")}

    def _fail(*args, **kwargs):
        raise AssertionError(
            "filesystem was touched before the unconfigured guard raised"
        )

    try:
        for name in originals:
            setattr(Path, name, _fail)
        yield
    finally:
        for name, original in originals.items():
            setattr(Path, name, original)


# ---------------------------------------------------------------------------
# AC-1 — the guard itself
# ---------------------------------------------------------------------------


def _assert_raises_naming_both_routes(repo_cls, arg):
    """Construct and require VaultPathNotConfiguredError naming both routes."""
    try:
        _construct(repo_cls, arg)
    except VaultPathNotConfiguredError as exc:
        message = str(exc)
        assert "vault_path" in message, (
            f"{repo_cls.__name__}({arg!r}): message omits the vault_path route"
        )
        assert ENV_VAR in message, (
            f"{repo_cls.__name__}({arg!r}): message omits the {ENV_VAR} route"
        )
        return exc
    raise AssertionError(
        f"{repo_cls.__name__}({arg!r}) did not raise VaultPathNotConfiguredError"
    )


def test_unconfigured_vault_path_raises():
    """AC-1: every unconfigured shape raises, naming both routes.

    Zero-argument by contract (see module docstring): the argument shapes are
    iterated here rather than parametrised, so the acceptance battery can call
    this function directly outside pytest.

    Two halves, matching AC-1's conjunction. First: each unconfigured argument
    shape with no env var at all. Second: no argument with a set-but-BLANK env
    var — the more common misconfiguration of the two, since it is what a
    broken .env or an unexpanded shell variable produces.
    """
    with _scrubbed_env():
        for arg in UNCONFIGURED_ARGS:
            _assert_raises_naming_both_routes(PersonRepository, arg)

    for blank_env in ("", "   ", "."):
        with _env_set(blank_env):
            _assert_raises_naming_both_routes(PersonRepository, NO_ARG)

    # The break degrades to a message change: a consumer's existing
    # `except ValueError` still catches. This is the whole reason for the
    # base class, so it is pinned inside the AC-named check rather than beside
    # it — the battery only ever runs the named function.
    assert issubclass(VaultPathNotConfiguredError, ValueError)
    with _scrubbed_env():
        try:
            PersonRepository()
        except ValueError:
            pass
        else:
            raise AssertionError("unconfigured construction did not raise ValueError")


@pytest.mark.parametrize("env_value", [None, "", "   ", "."])
@pytest.mark.parametrize("arg", UNCONFIGURED_ARGS)
def test_error_message_is_the_static_constant(arg, env_value, monkeypatch):
    """Threat model M2: the message never interpolates anything.

    Under EVERY raising combination the message must be byte-identical to the
    module constant. If it ever drifts into an f-string echoing the rejected
    vault_path or the env var's contents, that data would ride into tracebacks
    and logs across three consumer repos.
    """
    if env_value is None:
        monkeypatch.delenv(ENV_VAR, raising=False)
    else:
        monkeypatch.setenv(ENV_VAR, env_value)

    with pytest.raises(VaultPathNotConfiguredError) as exc_info:
        _construct(PersonRepository, arg)

    assert (
        str(exc_info.value)
        == obsidian_schemas.repositories.base.UNCONFIGURED_VAULT_MESSAGE
    )


def test_explicit_path_and_env_var_both_resolve(tmp_path, monkeypatch):
    """The happy paths still work, and an explicit argument wins over the env."""
    monkeypatch.delenv(ENV_VAR, raising=False)
    assert PersonRepository(tmp_path).vault_path == tmp_path

    env_vault = tmp_path / "from-env"
    env_vault.mkdir()
    monkeypatch.setenv(ENV_VAR, str(env_vault))
    assert PersonRepository().vault_path == env_vault
    assert PersonRepository(tmp_path).vault_path == tmp_path


# ---------------------------------------------------------------------------
# AC-3 — every subclass, every shape, before any filesystem access
# ---------------------------------------------------------------------------


def test_all_repositories_raise_when_unconfigured():
    """AC-3: the guard reaches every door a consumer actually calls.

    The predicate lives once in BaseRepository, but the blast radius is
    per-subclass — and the Path-typed shape matters most, since the library's
    own person.py passes a Path into CompanyRepository.

    Zero-argument by contract: the full cross-product of four repositories ×
    every unconfigured shape is iterated here rather than parametrised.
    """
    with _scrubbed_env():
        for repo_cls in ALL_REPOSITORIES:
            for arg in UNCONFIGURED_ARGS:
                _assert_raises_naming_both_routes(repo_cls, arg)

        # AC-3's second clause: "at construction, before any glob or read of
        # the filesystem." Pinned inside the named check, not beside it — the
        # battery runs only the function the criteria fence names, so a clause
        # asserted in a sibling test is a clause the gate never observes.
        with _no_filesystem():
            for repo_cls in ALL_REPOSITORIES:
                _assert_raises_naming_both_routes(repo_cls, NO_ARG)


@pytest.mark.parametrize("repo_cls", ALL_REPOSITORIES)
def test_raise_precedes_any_filesystem_access(repo_cls, monkeypatch):
    """AC-3 / mitigation M1: no glob or exists() on an unresolved path."""
    monkeypatch.delenv(ENV_VAR, raising=False)

    def _fail(*args, **kwargs):
        pytest.fail("filesystem was touched before the unconfigured guard raised")

    monkeypatch.setattr(Path, "glob", _fail)
    monkeypatch.setattr(Path, "exists", _fail)
    monkeypatch.setattr(Path, "mkdir", _fail)

    with pytest.raises(VaultPathNotConfiguredError):
        repo_cls()


# ---------------------------------------------------------------------------
# AC-2 — no caller-independent path survives as a default
# ---------------------------------------------------------------------------

# Property: the vault is always supplied by the caller or the environment. A
# literal-string grep would miss a reintroduced expanduser("~/...") form, which
# is exactly how lint_vault.py:50 passed such a grep before this item.
FORBIDDEN_DEFAULT_PATTERNS = ["expanduser", "Path.home()", "/Users/"]


def _code_lines(path: Path):
    """Yield (lineno, line) for executable lines only — no comments, no docstrings."""
    in_docstring = False
    delimiter = None

    for lineno, raw in enumerate(path.read_text().splitlines(), start=1):
        line = raw.strip()

        if in_docstring:
            if delimiter in line:
                in_docstring = False
                delimiter = None
            continue

        if not line or line.startswith("#"):
            continue

        for candidate in ('"""', "'''"):
            if candidate in line:
                # A docstring that opens and closes on one line is fully skipped.
                if line.count(candidate) % 2 == 1:
                    in_docstring = True
                    delimiter = candidate
                break
        else:
            yield lineno, raw
            continue

        # The line opened (or contained) a docstring — never scanned as code.


def test_no_implicit_vault_path_defaults():
    """AC-2: zero live matches in obsidian_schemas/ and scripts/.

    Zero-match is the only maintainable resting state — a scan that carries an
    exception list is a scan nobody trusts.
    """
    offenders = []

    for directory in ("obsidian_schemas", "scripts"):
        for py_file in sorted((REPO_ROOT / directory).rglob("*.py")):
            for lineno, line in _code_lines(py_file):
                for pattern in FORBIDDEN_DEFAULT_PATTERNS:
                    if pattern in line:
                        rel = py_file.relative_to(REPO_ROOT)
                        offenders.append(f"{rel}:{lineno}: {line.strip()}")

    assert offenders == [], (
        "caller-independent filesystem path resolved as a default:\n"
        + "\n".join(offenders)
    )


def test_default_vault_path_constant_is_gone():
    """AC-2: the constant itself no longer exists."""
    assert not hasattr(obsidian_schemas.repositories.base, "DEFAULT_VAULT_PATH")


# ---------------------------------------------------------------------------
# AC-4 — the mutating script refuses an implicit vault
# ---------------------------------------------------------------------------


def _run_lint_vault(*args):
    """Run scripts/lint_vault.py with OBSIDIAN_VAULT_PATH scrubbed from the env."""
    env = {k: v for k, v in os.environ.items() if k != ENV_VAR}
    return subprocess.run(
        [sys.executable, "scripts/lint_vault.py", *args],
        env=env,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )


def test_lint_vault_requires_explicit_vault():
    """AC-4 / mitigation M3: exit non-zero with both routes named, no TypeError.

    --vault "" is the corruption door: Path("") is Path("."), which always
    exists, so without the guard the linter would run against the current
    working directory — and --quarantine renames the files it finds.

    Zero-argument by contract: the three invocations are iterated here rather
    than parametrised, so the acceptance battery can call this directly.
    """
    for args in ((), ("--vault", ""), ("--vault", "   ")):
        result = _run_lint_vault(*args)
        where = f"lint_vault.py {' '.join(args)!r}".strip()

        assert result.returncode != 0, f"{where}: exited 0 with no vault configured"
        assert "TypeError" not in result.stderr, (
            f"{where}: crashed with a TypeError instead of naming both routes"
        )
        assert "--vault" in result.stderr, f"{where}: stderr omits the --vault route"
        assert ENV_VAR in result.stderr, f"{where}: stderr omits the {ENV_VAR} route"


# ---------------------------------------------------------------------------
# AC-5 — no doc advertises no-arg construction
# ---------------------------------------------------------------------------

NO_ARG_CONSTRUCTION = re.compile(r"\w+Repository\(\s*\)")

# docs/** and state/** are work-item pipeline RECORDS that quote the
# antipattern as the defect under discussion. Quoting a defect as evidence is
# not advertising it.
DOC_SCAN_EXCLUDED = {".git", ".venv", "docs", "state", "node_modules"}


def _temp_root_inside_repo():
    """The temp tree, IF the ambient TMPDIR happens to sit inside the repo.

    This scan's domain is the repo's own DOCUMENTATION; scratch output written
    by the suite mid-run is not documentation and was never in scope. It only
    became reachable when TMPDIR points inside the tree — which is exactly the
    build worktree's configuration (`TMPDIR=<worktree>/tmp`), where both
    pytest's `tmp_path` factory and `tests/support.temp_dir()` root themselves
    here and the walk below then descends into live fixture output.

    Derived from `tempfile.gettempdir()` rather than by excluding a directory
    NAME: the same rule the temp machinery itself uses, so it holds for a TMPDIR
    called `scratch/` as readily as one called `tmp/`. Returns None when the
    temp tree is outside the repo (the ordinary case), in which case the walk
    can never reach it and nothing is skipped.

    WI-020 (2026-07-24) surfaced this: that item added the suite's first `.md`
    fixture that is deliberately not valid UTF-8, so the unbounded walk stopped
    being merely over-broad and started raising UnicodeDecodeError.
    """
    try:
        temp_root = Path(tempfile.gettempdir()).resolve()
    except OSError:
        return None
    try:
        temp_root.relative_to(REPO_ROOT.resolve())
    except ValueError:
        return None
    return temp_root


def _scanned_markdown_files():
    temp_root = _temp_root_inside_repo()
    for md_file in sorted(REPO_ROOT.rglob("*.md")):
        relative = md_file.relative_to(REPO_ROOT)
        if DOC_SCAN_EXCLUDED.intersection(relative.parts):
            continue
        if temp_root is not None:
            try:
                md_file.resolve().relative_to(temp_root)
                continue
            except (ValueError, OSError):
                pass
        yield md_file


def test_docs_do_not_advertise_no_arg_construction():
    """AC-5: a general pattern scan, not a line-targeted check.

    Pinned as a pattern so it does not go stale against line numbers. Once the
    conductor's doc preconditions land this is a regression guard rather than a
    driver of work.
    """
    offenders = []

    for md_file in _scanned_markdown_files():
        # errors="replace", because a walk over the working tree can reach a
        # `.md` that is not valid UTF-8 (WI-020 added exactly such a fixture),
        # and a decode crash there grades the walk rather than the docs. This
        # cannot hide an offender: NO_ARG_CONSTRUCTION is pure ASCII, so
        # replacement chars land only on bytes that could never have matched.
        text = md_file.read_text(encoding="utf-8", errors="replace")
        for lineno, line in enumerate(text.splitlines(), start=1):
            if NO_ARG_CONSTRUCTION.search(line):
                rel = md_file.relative_to(REPO_ROOT)
                offenders.append(f"{rel}:{lineno}: {line.strip()}")

    assert offenders == [], (
        "documentation advertises no-arg repository construction:\n"
        + "\n".join(offenders)
    )


# ---------------------------------------------------------------------------
# AC-6 — the consumer-audit artifact has audit shape
# ---------------------------------------------------------------------------

AUDIT_PATH = REPO_ROOT / "docs" / "wi-024-consumer-audit.md"
AUDITED_REPOS = ["HAL9000", "Exocortex", "orchestrator"]
SHA_PATTERN = re.compile(r"\b[0-9a-f]{40}\b")
REMEDIATION_COMMAND = "zsh -c 'echo $OBSIDIAN_VAULT_PATH'"


def _audit_section(text, heading):
    """Return the body of '## <heading>' up to the next '## ' heading."""
    match = re.search(
        rf"^## {re.escape(heading)}\s*$(.*?)(?=^## |\Z)",
        text,
        re.MULTILINE | re.DOTALL,
    )
    assert match is not None, f"audit artifact has no '## {heading}' section"
    return match.group(1)


def test_consumer_audit_artifact_is_complete():
    """AC-6: pins the artifact's SHAPE, never re-running the scan.

    The audit's teeth are the kind: precondition write fence — this test makes
    an audit recorded as one hand-waved prose sentence fail, and the per-repo
    SHA makes the claim re-checkable by anyone with the three repos on disk
    (which this hermetic suite, by design, is not). No subprocess, no network.
    """
    assert AUDIT_PATH.exists(), f"missing consumer-audit artifact: {AUDIT_PATH}"
    text = AUDIT_PATH.read_text()

    for repo in AUDITED_REPOS:
        section = _audit_section(text, repo)

        assert re.search(r"^Command:", section, re.MULTILINE), (
            f"{repo}: no 'Command:' field"
        )
        commands = re.findall(r"```(.*?)```", section, re.DOTALL)
        assert commands and commands[0].strip(), (
            f"{repo}: 'Command:' is not followed by a non-empty fenced block"
        )

        # Output must be present: either a verbatim fenced block or an
        # explicit no-matches marker. An ABSENT Output field fails.
        assert re.search(r"^Output", section, re.MULTILINE), (
            f"{repo}: no 'Output' field"
        )
        has_verbatim = len(commands) > 1 and commands[1].strip()
        has_marker = "no matches" in section
        assert has_verbatim or has_marker, (
            f"{repo}: Output is neither a verbatim block nor a 'no matches' marker"
        )

        head_match = re.search(r"^HEAD:\s*`?([0-9a-f]+)`?", section, re.MULTILINE)
        assert head_match, f"{repo}: no 'HEAD:' line"
        assert SHA_PATTERN.fullmatch(head_match.group(1)), (
            f"{repo}: HEAD is not a 40-char hex SHA: {head_match.group(1)!r}"
        )

    # The remediation the 16 live orchestrator sites depend on must be
    # confirmed live, not merely planned (P3 / mitigation M4).
    remediation_match = re.search(
        r"^## remediation_confirmed.*?$(.*?)(?=^## |\Z)",
        text,
        re.MULTILINE | re.DOTALL,
    )
    assert remediation_match is not None, (
        "audit artifact carries no 'remediation_confirmed' record — the export "
        "the 16 live orchestrator sites depend on is unproven. Do NOT add this "
        "record yourself: the conductor must amend and commit the artifact."
    )
    remediation = remediation_match.group(1)
    assert REMEDIATION_COMMAND in remediation, (
        "remediation_confirmed does not record the literal readback command"
    )
    readback = re.findall(r"```(.*?)```", remediation, re.DOTALL)
    assert readback, "remediation_confirmed has no fenced readback block"
    output_lines = [
        line
        for line in readback[0].strip().splitlines()
        if line.strip() and not line.strip().startswith("$")
    ]
    assert output_lines, (
        "remediation_confirmed records the command but no non-empty output — "
        "the export is planned, not proven live"
    )
