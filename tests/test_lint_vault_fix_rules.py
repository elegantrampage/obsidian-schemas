"""WI-026 — the test floor for `scripts/lint_vault.py`'s repair layer.

Five criteria checks, plus three non-AC siblings the plan adds. What they are
for, in one sentence each, because this module is the first thing under `tests/`
that ever drives `run_lint(..., do_fix=True)` and `apply_fixes` against a vault:

- AC-1 — every auto-fixable rule repairs to an oracle stated in the work item,
  over a rule set DERIVED from the script's own syntax rather than listed.
- AC-2 — every detector that causes a WRITE fires exactly on its declared
  subjects, in both directions, including the two `garbage_candidate_*` checks
  that decide what `--quarantine` RELOCATES.
- AC-3 — a note whose bytes will not decode is reported, stays in the index, and
  is never repaired or moved.
- AC-4 — a `--fix` run accounts for every auto-fixable ISSUE it was handed, and
  the operator's printed line says so.
- AC-5 — the conductor's live-vault baseline is committed, shaped, and agrees
  with the frozen census.

**THE CONTAINMENT DOOR, and why it is the first check in the file.** The path
that must never reach this module is one attribute access away:
`scripts/lint_vault.py:DEFAULT_VAULT` is an environment read, and on the author's
own machine that variable is populated. No standing wall reaches this —
`tests/test_vault_path_required.py:FORBIDDEN_DEFAULT_PATTERNS` is three literal
PATH shapes, none of which can see an environment read, and its sweep stops at
`("obsidian_schemas", "scripts")`. So this module ships its own, in five parts,
and no proper subset of them is sufficient:

1. RUNTIME — `_temp_vault` is the module's ONLY constructor of a vault path and
   asserts containment before it returns.
2. SYNTAX (spelling + non-vacuity + provenance) — every mutating drive's vault
   argument is the identifier `vault`, there is at least one, and EVERY binding
   of that name in this module is a call to the one door. Without the third
   clause, `vault = lint_vault.DEFAULT_VAULT` followed by
   `run_lint(vault, do_fix=True)` passes the first two while the door never runs.
3. IMPORT — this module names no subprocess-capable module, because a child
   process is unreadable to any in-process census by construction and omitting
   the path altogether is enough to reach the live vault through `main`'s
   `--vault` default.
4. SOURCE — this module NAMES the live vault path nowhere outside `_temp_vault`'s
   own body. Parts 1-3 all grade a drive's vault ARGUMENT, and `apply_fixes`
   never reads its `vault_path` (its write targets come from the issues), so a
   correctly-contained drive handed an issue list scanned from the live vault
   passes every one of them and rewrites Dave's notes.

5. LIBRARY (WI-031) — this module constructs NO `obsidian_schemas` repository,
   with any arguments, anywhere. Part 4 is total over the omission shapes that
   SPELL the path and not over one that OBTAINS it unspelled: the library's own
   `OBSIDIAN_VAULT_PATH` fallback in `repositories/base.py:_resolve_vault_path`
   runs inside every repository constructor, so `repo = PersonRepository()`
   beside `read_vault(repo.vault_path)` passes parts 1-4 with the door executed
   and rewrites the live vault wherever that variable is exported. Ruled
   closed by Dave on 2026-09-16; this module needs no repository.

No part is total over the whole, which is why all five stay load-bearing and
none is belt-and-braces; the residue is deliberate acts (a decoy spelled with
the door's own name), recorded as the wall's bound in WI-026's `## Scope
Boundary`.

Nothing here reads syntax directly: that capability is single-homed in
`tests/derivations.py`, and every scan below is imported from it.
"""

# FIRST, ahead of every package import: the conveyor may run this module's checks
# under an interpreter that is not this project's, where the imports below cannot
# resolve. A no-op under the floor command and under CI (WI-021).
from tests.ac_interpreter import ensure_project_interpreter

ensure_project_interpreter(__file__)

import contextlib  # noqa: E402 — everything below runs only once the interpreter is right
import importlib.util  # noqa: E402
import io  # noqa: E402
import os  # noqa: E402
import re  # noqa: E402
from pathlib import Path  # noqa: E402

from obsidian_schemas.repositories.base import SKIP_REASONS, UNREADABLE  # noqa: E402
from tests.derivations import (  # noqa: E402
    LIVE_PATH_ENV_KEY,
    LIVE_PATH_TOKENS,
    MODULE_LEVEL,
    NOT_A_CALL,
    PACKAGE_ROOT,
    SCRIPTS_ROOT,
    TESTS_ROOT,
    auto_fixable_branch_checks,
    auto_fixable_emitter_checks,
    character_class_strip_sites,
    address_splitting_implementations,
    filesystem_mutation_uses,
    frontmatter_write_arms,
    module_import_uses,
    modules_using_ast,
    mutating_drive_vault_args,
    os_module_attribute_uses,
    person_tier_arm_counts,
    python_files_under,
    skip_reason_literal_sites,
    ArmId,
    OS_READONLY_NAMES,
)
from tests.fixture_vault import CORPUS_ROOT, materialize_vault  # noqa: E402
from tests.support import patcher, temp_dir  # noqa: E402
# Design §9's fifth census reader lands beside WI-016's four, in their module,
# under the same whole-file `CENSUS_DIGEST` fixity — so it is IMPORTED here
# rather than copied. `tests/test_fixture_vault.py` already carries a
# cross-module test import of this shape (`:1296`).
from tests.test_fixture_vault import census_auto_fixable_rows  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
LINT_VAULT_PATH = SCRIPTS_ROOT / "lint_vault.py"
CENSUS = ROOT / "docs" / "vault-shape-census.md"
BASELINE = ROOT / "docs" / "lint-vault-live-baseline.md"
WORK_ITEM = ROOT / "docs" / "lint-vault-fix-safety.md"


def _load_lint_vault():
    """`scripts/` is not a package, so the CLI is loaded from its own path —
    through the SAME shape `tests/test_lint_vault_fix_gate.py:_load_lint_vault`
    already carries, never a second loader. `WI-030 lint-vault-package-export`
    is the item that would repoint this seam."""
    spec = importlib.util.spec_from_file_location(
        "wi026_lint_vault", LINT_VAULT_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


lint_vault = _load_lint_vault()

#: The 53 stems a plant may NOT reuse. `materialize_vault`'s "leaves everything
#: else alone" protects files a plant does not NAME; it does not protect one a
#: plant overwrites, and `@Dave  Marrowyn Fennwick` is the specific trap — it
#: carries a well-formed `name:` and is the note that proves
#: `person_missing_name` stays SILENT on a healthy double-spaced stem.
CORPUS_STEMS = frozenset(p.stem for p in CORPUS_ROOT.iterdir() if p.is_file())

#: Every temp root this process took from `tests.support.temp_dir()`, by resolved
#: path. `_temp_vault` asserts membership rather than guessing at a path SHAPE —
#: a `/tmp` layout, a prefix or a `cage-wt-` substring is WI-149's scar and is
#: false in the graded environment.
_ISSUED_TEMP_ROOTS: set = set()


@contextlib.contextmanager
def _temp_root():
    """This module's ONLY source of a temp directory, and the issuing register
    `_temp_vault`'s second assertion reads."""
    with temp_dir() as root:
        resolved = Path(root).resolve()
        _ISSUED_TEMP_ROOTS.add(resolved)
        try:
            yield root
        finally:
            _ISSUED_TEMP_ROOTS.discard(resolved)


def _temp_vault(tmp):
    """The ONE door. Every mutating drive in this module takes its vault path
    from here, and the syntax half asserts that every binding of the identifier
    those drives pass is a call to this function.

    The three negative assertions below are MANDATORY rather than defensive, and
    they are why the source clause's exemption is scoped to this function's own
    body: a flat "the module names neither token" rule would be RED against the
    door the design orders.
    """
    built = materialize_vault(Path(tmp) / "vault")
    resolved = Path(built).resolve()
    root = Path(tmp).resolve()

    # A strict descendant of the temp root — `relative_to` RAISES when it is not.
    assert resolved.relative_to(root) != Path("."), (
        f"the vault must be a strict descendant of {root}, not the root itself")
    assert root in _ISSUED_TEMP_ROOTS, (
        f"{root} is not a directory this process took from temp_dir()")

    # `.get(..., "")` and NEVER a subscript: the variable is UNSET in the graded
    # and CI environments, where `os.environ[...]` raises KeyError and reddens
    # the door itself rather than a drive.
    # The env key is spelled HERE, as a bare literal, and nowhere else in this
    # module: this function's body is the source clause's one exemption, and
    # these three negative assertions are what make its NON-EMPTY arm true — a
    # matcher that resolves nothing would satisfy a zero-outside-the-door clause
    # most cheaply of all. Every other site in this module reads
    # `LIVE_PATH_ENV_KEY` instead, and a bare copy of it there is RED.
    for live in (lint_vault.DEFAULT_VAULT, os.environ.get("OBSIDIAN_VAULT_PATH", "")):
        if live:
            assert resolved != Path(live).resolve(), (
                "a drive was about to be pointed at the LIVE vault")
    return built


def _plant(into, stem, body):
    """Write one note on top of a materialized copy, REFUSING a corpus stem."""
    if stem in CORPUS_STEMS:
        raise AssertionError(
            f"{stem!r} is a corpus stem — planting over it would destroy a "
            f"frozen member and the evidence it carries (constraint 7)")
    path = Path(into) / f"{stem}.md"
    path.write_text(body, encoding="utf-8")
    return path


def _plant_bytes(into, stem, raw):
    """The same, for a note whose bytes deliberately do not decode."""
    if stem in CORPUS_STEMS:
        raise AssertionError(f"{stem!r} is a corpus stem")
    path = Path(into) / f"{stem}.md"
    path.write_bytes(raw)
    return path


def _scan(where):
    """`read_vault` -> `build_indexes` -> all five checks, exactly as `run_lint`
    composes them. Returns `(files, idx, issues)`."""
    files = lint_vault.read_vault(Path(where))
    idx = lint_vault.build_indexes(files)
    issues = []
    for fn in (lint_vault.check_structural, lint_vault.check_completeness,
               lint_vault.check_links, lint_vault.check_timeline,
               lint_vault.check_noise):
        issues.extend(fn(files, idx))
    return files, idx, issues


def _fixable(issues):
    return [i for i in issues if i.auto_fixable]


def _frontmatter(path):
    from obsidian_schemas.parser import parse_frontmatter
    return parse_frontmatter(Path(path).read_text(encoding="utf-8"))


def _person(stem, extra="", body=None):
    """A minimal typed person note. `body` defaults to the full expected set so
    the note's ONLY auto-fixable issue is the one a plant is about."""
    if body is None:
        body = "## To Discuss\n\n## Timeline\n\n## Notes\n"
    return f"---\ntype: person\nname: {stem.lstrip('@')}\n{extra}---\n\n{body}"


# ==========================================================================
# M3 / M5 / M6 / M7 / M8 + WI-031 — the containment wall, DEFINED FIRST so an ordinary
# floor run fires the detector ahead of every driving check in this module.
# It is an ordering COURTESY and not a guarantee (`-k` selection and direct
# invocation bypass it); the guarantee is the runtime door plus the clauses
# that close the routes around it.
# ==========================================================================

def test_every_mutating_drive_in_this_module_is_confined_to_a_temp_vault():
    """The FIVE clauses of the containment wall over this module's own source,
    inside ONE check, plus the WI-235 fixture battery that proves the predicate
    they run actually resolves the shapes it claims."""
    _check_the_five_containment_clauses()
    with _temp_root() as root:
        _check_the_runtime_door_contains_what_it_builds(root)
        _check_the_drives_census_reaches_its_claimed_shapes(root)
        _check_the_bindings_census_reaches_its_claimed_shapes(root)
        _check_the_source_census_reaches_its_claimed_shapes(root)
        _check_the_repository_census_reaches_its_claimed_shapes(root)


def _check_the_runtime_door_contains_what_it_builds(root):
    """The RUNTIME half, EXERCISED here rather than left to whichever driving
    check happens to run first.

    Found by mutate-and-observe: hand-editing `_temp_vault` to return a path
    outside its `tmp` left this check GREEN, because the other three clauses
    read syntax and never CALL the door. The full floor caught it a few checks
    later, but the detector is defined first precisely so it fires ahead of the
    drives — which it cannot do for the one clause that needs the door to run.

    The live-path comparisons are NOT repeated here and must not be: they are
    the door's own, and naming either token outside `_temp_vault`'s body is
    exactly what clause (iv) forbids — a first draft of this helper re-asserted
    them and was RED on the wall it sits inside.
    """
    vault = _temp_vault(root)
    resolved = Path(vault).resolve()
    assert resolved.relative_to(Path(root).resolve()) != Path(".")
    assert (resolved / "@Isolde Varnholt.md").exists(), (
        "the door must return a materialized corpus, not merely a contained path")


def _check_the_five_containment_clauses():
    scan = mutating_drive_vault_args([Path(__file__)])

    # (i) SPELLING. A drive passing `lint_vault.DEFAULT_VAULT`, a literal or an
    # environment read never reaches this assertion at all — the scan RAISES on
    # it — while one passing some other bound name is RED naming its line.
    wrong = sorted(t for t in scan.drives if t[2] != "vault")
    assert not wrong, f"a mutating drive takes a vault argument that is not `vault`: {wrong}"

    # (ii) NON-VACUITY. A module that stopped driving the tool cannot pass by
    # having nothing to grade.
    assert scan.drives, "this module drives nothing — the wall would be vacuous"

    # (iii) PROVENANCE, which is what makes the wall a claim about where the
    # path CAME FROM rather than how it is spelled. Clauses (i) and (ii) alone
    # are satisfied EXACTLY by `vault = lint_vault.DEFAULT_VAULT` followed by
    # `run_lint(vault, do_fix=True)`, with the runtime door never called.
    strays = sorted(b for b in scan.bindings if b[3] != "_temp_vault")
    assert not strays, (
        f"`vault` is bound by something other than the one door: {strays}")

    # (iv) SOURCE (M8). The first three grade the vault ARGUMENT, and
    # `apply_fixes` ignores its `vault_path` entirely — its write targets are
    # `issue.file_path` — so a check binding `vault = _temp_vault(tmp)` and
    # handing `apply_fixes` an issue list built from a scan of the LIVE vault
    # passes (i)-(iii) with the door executed and the import wall clean.
    outside = sorted(n for n in scan.live_path_names if n[3] != "_temp_vault")
    assert not outside, (
        f"this module names the live vault path outside `_temp_vault`'s own "
        f"body: {outside}")
    # The WI-235 element: a matcher that resolves NOTHING satisfies a
    # zero-outside-the-door clause most cheaply of all.
    assert scan.live_path_names, (
        "the source census resolved nothing in this module — the door's own "
        "three negative assertions must be visible to it")
    assert {n[2] for n in scan.live_path_names} == LIVE_PATH_TOKENS, (
        "the door must exercise all three token shapes, so the clause's green "
        "is a statement about a matcher that reaches every one of them")

    # (v) LIBRARY (WI-031). Clause (iv) grades what this module SPELLS, and the
    # library's own environment fallback lets a repository obtain the live path
    # unspelled — `repo = PersonRepository()` names no token at all. ZERO
    # constructions, with any arguments, in any scope INCLUDING the door's own
    # body: this module needs no repository. Non-vacuity of the matcher is
    # proved by the fixture battery below, never by this module's own zero.
    constructed = sorted(scan.repository_constructions)
    assert not constructed, (
        f"this module constructs an obsidian_schemas repository, which resolves "
        f"the live vault from the environment inside the library: {constructed}")


def _raises(fn, *args):
    try:
        fn(*args)
    except AssertionError:
        return True
    return False


def _check_the_drives_census_reaches_its_claimed_shapes(root):
    """Four collected shapes, the M5 and M7 callee-set shapes, the near-misses
    and the closed-set RAISES. Every fixture here is planted TEXT handed to the
    predicate — never a line of this module's own source — which is why it may
    legally spell tokens clause (iv) forbids."""
    def scan(name, source):
        return mutating_drive_vault_args([_plant_source(root, name, source)])

    collected = scan("drives_ok", (
        "vault = _temp_vault(tmp)\n"
        "apply_fixes(issues, vault, idx)\n"            # second positional
        "run_lint(vault, do_fix=True)\n"               # first positional
        "lint_vault.run_lint(vault_path=vault)\n"      # attribute + keyword
        "mod.apply_fixes(issues, vault)\n"             # attribute callee
    ))
    assert sorted(t[1] for t in collected.drives) == [2, 3, 4, 5], (
        "the callee reaches the module by two spellings and the argument by two "
        "positions; a matcher handling only the bare-name positional form is "
        "green on a module full of the other three")
    assert {t[2] for t in collected.drives} == {"vault"}

    # M7's shapes: `quarantine_garbage` is the member whose write is
    # IRREVERSIBLE, and all three are collected by NOTHING under a three-member
    # callee set.
    quarantine = scan("drives_quarantine", (
        "vault = _temp_vault(tmp)\n"
        "lint_vault.quarantine_garbage(issues, vault)\n"
        "quarantine_garbage(issues, vault)\n"
    ))
    assert sorted(t[1] for t in quarantine.drives) == [2, 3]
    assert _raises(scan, "drives_quarantine_live", (
        "vault = _temp_vault(tmp)\n"
        "lint_vault.quarantine_garbage(issues, lint_vault.DEFAULT_VAULT)\n"))

    # M5's shapes: `main` has NO vault-argument position, so every collected
    # call falls into the arm that already RAISES.
    for name, source in (
        ("drives_main_attr", "vault = _temp_vault(t)\nlint_vault.main()\n"),
        ("drives_main_bare", "vault = _temp_vault(t)\nmain()\n"),
        ("drives_default", "vault = _temp_vault(t)\nrun_lint(lint_vault.DEFAULT_VAULT)\n"),
        ("drives_literal", "vault = _temp_vault(t)\napply_fixes(i, Path('/tmp/x'), idx)\n"),
        ("drives_none", "vault = _temp_vault(t)\nrun_lint()\n"),
    ):
        assert _raises(scan, name, source), (
            f"{name} must RAISE rather than be skipped — an under-reading "
            f"census is green against precisely the drive it exists to catch")

    # …and the near-miss that stops the widening being satisfiable by matching
    # every argument-free call.
    near = scan("drives_nearmiss", (
        "vault = _temp_vault(tmp)\n"
        "run_lint(vault, do_fix=True)\n"
        "setup()\n"
        "helpers.main_menu()\n"
        "run_lint_report(vault)\n"
        "other_callee(vault)\n"
        "x = 'run_lint'\n"
    ))
    assert sorted(t[1] for t in near.drives) == [2], (
        "the callee set must reach `main` rather than anything shaped like it, "
        "and must not collect a docstring mention or an unrelated callee")


def _check_the_bindings_census_reaches_its_claimed_shapes(root):
    def scan(name, source):
        return mutating_drive_vault_args([_plant_source(root, name, source)])

    # THE RED THAT MATTERS: correct spelling, correct drive, door never called.
    for name, binding, provenance in (
        ("bind_attr", "vault = lint_vault.DEFAULT_VAULT", NOT_A_CALL),
        ("bind_env", 'vault = os.environ["OBSIDIAN_VAULT_PATH"]', NOT_A_CALL),
        ("bind_literal", "vault = '/somewhere/else/vault'", NOT_A_CALL),
        ("bind_wrapper", "vault = make_vault(tmp)", "make_vault"),
        ("bind_door", "vault = _temp_vault(tmp)", "_temp_vault"),
    ):
        out = scan(name, f"{binding}\nrun_lint(vault, do_fix=True)\n")
        assert {b[3] for b in out.bindings} == {provenance}, (
            f"{name}: expected provenance {provenance!r}")

    # THE NEAR-MISS, which is what stops the provenance clause being satisfiable
    # by matching every assignment: the census is scoped to the identifiers
    # `drives` names, so an honest module may bind whatever else it likes.
    honest = scan("bind_nearmiss", (
        "vault = _temp_vault(tmp)\n"
        "other = lint_vault.DEFAULT_VAULT\n"
        'path = os.environ["OBSIDIAN_VAULT_PATH"]\n'
        "run_lint(vault, do_fix=True)\n"
    ))
    assert {b[2] for b in honest.bindings} == {"vault"}
    assert {b[3] for b in honest.bindings} == {"_temp_vault"}

    # The CLOSED-SET raises — one per binding construct carrying no readable
    # provenance, plus the no-binding case.
    for name, source in (
        ("raise_param", "def check(vault):\n    run_lint(vault, do_fix=True)\n"),
        ("raise_for", "for vault in vaults:\n    run_lint(vault, do_fix=True)\n"),
        ("raise_with", "with make(t) as vault:\n    run_lint(vault, do_fix=True)\n"),
        ("raise_tuple", "vault, other = pair\nrun_lint(vault, do_fix=True)\n"),
        ("raise_aug", "vault = _temp_vault(t)\nvault += 'x'\nrun_lint(vault, do_fix=True)\n"),
        ("raise_alias", "import mod as vault\nrun_lint(vault, do_fix=True)\n"),
        ("raise_unbound", "run_lint(vault, do_fix=True)\n"),
    ):
        assert _raises(scan, name, source), (
            f"{name} must RAISE — 'every binding came from the door' is only a "
            f"claim about ALL of them if the unreadable shapes are loud")


def _check_the_source_census_reaches_its_claimed_shapes(root):
    def scan(name, source):
        return mutating_drive_vault_args([_plant_source(root, name, source)])

    # The four-line escape itself: every clause of the argument half GREEN, and
    # clause (iv) RED at the live-path reference's own line.
    escape = scan("source_escape", (
        "vault = _temp_vault(tmp)\n"
        "issues = lint_vault.check_noise("
        "lint_vault.read_vault(lint_vault.DEFAULT_VAULT), idx)\n"
        "lint_vault.apply_fixes(issues, vault)\n"
    ))
    assert {b[3] for b in escape.bindings} == {"_temp_vault"}, (
        "the argument half must stay GREEN on the escape — that is what makes "
        "the source half load-bearing rather than a restatement of it")
    assert {t[2] for t in escape.drives} == {"vault"}
    assert [(n[1], n[2], n[3]) for n in sorted(escape.live_path_names)] == [
        (2, "DEFAULT_VAULT", MODULE_LEVEL)]

    # Three tokens through two spellings each — a matcher reaching only the
    # dotted form is green on a module full of the rest.
    claimed = scan("source_claimed", (
        "from lint_vault import DEFAULT_VAULT\n"
        "from os import getenv\n"
        "a = lint_vault.DEFAULT_VAULT\n"
        "b = DEFAULT_VAULT\n"
        'c = "OBSIDIAN_VAULT_PATH"\n'
        "d = os.environ\n"
        "e = getenv('X')\n"
    ))
    assert {n[2] for n in claimed.live_path_names} == LIVE_PATH_TOKENS

    # The SCOPING shapes, which are what make the exemption checkable rather
    # than a tolerance. The nested `def` is the one an occurrence-count reading
    # is green on and the one that separates INNERMOST from outermost.
    scoped = scan("source_scoped", (
        "def _temp_vault(tmp):\n"
        "    a = lint_vault.DEFAULT_VAULT\n"
        "    def inner():\n"
        "        return os.environ.get('X')\n"
        "    return a\n"
        "def test_x():\n"
        "    b = lint_vault.DEFAULT_VAULT\n"
        'z = "OBSIDIAN_VAULT_PATH"\n'
    ))
    assert {(n[2], n[3]) for n in scoped.live_path_names} == {
        ("DEFAULT_VAULT", "_temp_vault"),
        ("os.environ", "inner"),
        ("DEFAULT_VAULT", "test_x"),
        (LIVE_PATH_ENV_KEY, MODULE_LEVEL),
    }

    # The NEAR-MISSES, which stop clause (iv) being satisfiable by matching
    # every name in sight. The Constant arm is EQUALITY and never containment —
    # which is exactly what makes THIS battery's own fixture strings legal.
    quiet = scan("source_nearmiss", (
        "default_vault = 1\n"
        "q = lint_vault.DEFAULT_CATEGORIES\n"
        'r = "OBSIDIAN_VAULT_PATH_OLD"\n'
        '"""A docstring mentioning OBSIDIAN_VAULT_PATH in running prose."""\n'
        "u = 'path = os.environ[\"OBSIDIAN_VAULT_PATH\"]'\n"
        "v = os.path\n"
        "w = os.sep\n"
    ))
    assert not quiet.live_path_names, (
        f"the source census matched a near-miss: {sorted(quiet.live_path_names)}")

    # NON-VACUITY: a module naming none of the three tokens must make the wall
    # RED for emptiness rather than green.
    assert not scan("source_empty", "x = 1\n").live_path_names


def _check_the_repository_census_reaches_its_claimed_shapes(root):
    """WI-031. Every fixture is planted TEXT handed to the predicate, which is
    why it may legally construct what clause (v) forbids this module."""
    def scan(name, source):
        return mutating_drive_vault_args([_plant_source(root, name, source)])

    # THE ESCAPE ITSELF: clauses (i)-(iv) all GREEN — the door is called, the
    # drive is spelled `vault`, and no live-path token appears anywhere — while
    # the library hands `read_vault` the live vault. Only clause (v) is RED.
    escape = scan("repo_escape", (
        "vault = _temp_vault(tmp)\n"
        "repo = PersonRepository()\n"
        "issues = lint_vault.check_noise("
        "lint_vault.read_vault(repo.vault_path), idx)\n"
        "lint_vault.apply_fixes(issues, vault)\n"
    ))
    assert {b[3] for b in escape.bindings} == {"_temp_vault"}
    assert {t[2] for t in escape.drives} == {"vault"}
    assert not escape.live_path_names, (
        "the escape must spell NO live-path token — that is what makes clause "
        "(v) load-bearing rather than a restatement of clause (iv)")
    assert [(n[1], n[2], n[3]) for n in sorted(escape.repository_constructions)] == [
        (2, "PersonRepository", MODULE_LEVEL)]

    # Both spellings, ANY arguments, and NO exemption for the door's own body —
    # an explicit-path construction is graded the same, because the rule is
    # zero rather than "no no-arg form" (`_is_unconfigured` swallows blank,
    # whitespace and "." too).
    claimed = scan("repo_claimed", (
        "a = PersonRepository()\n"
        "b = obsidian_schemas.CompanyRepository('/x')\n"
        "c = MeetingRepository(vault_path=tmp)\n"
        "def _temp_vault(tmp):\n"
        "    return BookRepository(tmp)\n"
    ))
    assert {(n[1], n[2], n[3]) for n in claimed.repository_constructions} == {
        (1, "PersonRepository", MODULE_LEVEL),
        (2, "CompanyRepository", MODULE_LEVEL),
        (3, "MeetingRepository", MODULE_LEVEL),
        (5, "BookRepository", "_temp_vault"),
    }

    # The NEAR-MISSES, which stop clause (v) being satisfiable by matching every
    # name with "repository" in it: the suffix is matched on the CALLEE, in
    # case, and a Constant, a bare name, a lower-case helper, a class whose name
    # merely contains the word and a method call on a repository-shaped object
    # are all invisible.
    quiet = scan("repo_nearmiss", (
        "repository = 1\n"
        'x = "PersonRepository()"\n'
        "y = get_repository(tmp)\n"
        "z = RepositoryError('x')\n"
        "w = PersonRepositoryFactory()\n"
        "v = repo.get_by_email(x)\n"
        '"""A docstring mentioning PersonRepository() in running prose."""\n'
    ))
    assert not quiet.repository_constructions, (
        f"the repository census matched a near-miss: "
        f"{sorted(quiet.repository_constructions)}")


def _plant_source(root, name, source):
    path = Path(root) / f"{name}.py"
    path.write_text(source, encoding="utf-8")
    return path


# ==========================================================================
# AC-1 — every auto-fixable rule repairs to its declared oracle.
# ==========================================================================

def test_every_auto_fixable_rule_repairs_to_its_declared_oracle():
    """Three legs: the two-sided derived rule set, an oracle table TOTAL over
    it, and the five oracles with their planted discriminators."""
    emitters = auto_fixable_emitter_checks([LINT_VAULT_PATH])
    branches = auto_fixable_branch_checks([LINT_VAULT_PATH])

    # (a) THE DERIVATION, TWO-SIDED. An emitter advertising a repair no branch
    # performs, and a branch no emitter can reach, are each RED — neither is
    # detectable in this repo any other way.
    assert emitters, "the emitter scan resolved no auto-fixable rule at all"
    assert emitters == branches, (
        f"the advertised rule set and the repairable rule set disagree: "
        f"emitters-only {sorted(emitters - branches)}, "
        f"branches-only {sorted(branches - emitters)}")

    # (b) THE ORACLE TABLE IS TOTAL OVER THAT SET — a sixth rule added later
    # fails this criterion until someone writes its oracle, rather than joining
    # the untested set silently.
    oracles = {
        "field_type_mismatch": _oracle_field_type_mismatch,
        "person_missing_name": _oracle_person_missing_name,
        "missing_body_sections": _oracle_missing_body_sections,
        "meeting_missing_from_timeline": _oracle_meeting_missing_from_timeline,
        "broken_wikilink": _oracle_broken_wikilink,
    }
    assert set(oracles) == emitters, (
        f"the oracle table does not cover the derived rule set: "
        f"untested {sorted(emitters - set(oracles))}, "
        f"stale {sorted(set(oracles) - emitters)}")

    # (c) EVERY RULE REPAIRS TO ITS DECLARED VALUE.
    for rule in sorted(oracles):
        with _temp_root() as root:
            oracles[rule](root)


def _oracle_field_type_mismatch(root):
    """The reparsed value is the BOOL of the branch's own truth set, on BOTH
    arms. The FALSE arm is the discriminator an always-True implementation
    fails, and the corpus cannot supply it — `auto_created` occurs nowhere in
    the 53 notes."""
    # The ONE door: `vault` is bound HERE and nowhere else in this module.
    vault = _temp_vault(root)
    truthy = _plant(vault, "@Tarnquil Sennaby",
                    _person("@Tarnquil Sennaby", extra="auto_created: 'yes'\n"))
    falsy = _plant(vault, "@Ostrivane Pellworth",
                   _person("@Ostrivane Pellworth", extra="auto_created: 'no'\n"))

    _, idx, issues = _scan(vault)
    subjects = [i for i in _fixable(issues)
                if i.check == "field_type_mismatch"
                and i.file_path in (truthy, falsy)]
    assert len(subjects) == 2, f"expected both arms to fire, got {subjects}"
    lint_vault.apply_fixes(subjects, vault, idx)

    assert _frontmatter(truthy)[0]["auto_created"] is True
    assert _frontmatter(falsy)[0]["auto_created"] is False, (
        "'no' must repair to False — an implementation that always writes True "
        "is green on every subject the live vault can supply")


def _oracle_person_missing_name(root):
    """The written name is `fpath.stem.lstrip("@")` BYTE-FOR-BYTE and not a
    cleaned form. The discriminator is a planted stem carrying the corpus's
    whitespace-damage shape — a DOUBLE SPACE — which `clean_person_name`
    collapses and which `gate_write` passes untouched, being a predicate on
    `name` rather than a transform."""
    # The ONE door: `vault` is bound HERE and nowhere else in this module.
    vault = _temp_vault(root)
    from obsidian_schemas.name_cleaning import clean_person_name

    stem = "@Tarnquil  Brenvik"           # NOT the corpus's @Dave  Marrowyn Fennwick
    damaged = _plant(vault, stem, "---\ntype: person\nname: ''\n---\n\n"
                                  "## To Discuss\n\n## Timeline\n\n## Notes\n")
    _, idx, issues = _scan(vault)
    subjects = [i for i in _fixable(issues)
                if i.check == "person_missing_name" and i.file_path == damaged]
    assert len(subjects) == 1, f"expected one subject, got {subjects}"
    lint_vault.apply_fixes(subjects, vault, idx)

    written = _frontmatter(damaged)[0]["name"]
    assert written == "Tarnquil  Brenvik", (
        f"the repair wrote {written!r}; the oracle is the stem byte-for-byte")
    assert written != clean_person_name(written), (
        "the fixture has stopped discriminating — `clean_person_name` no longer "
        "changes this stem, so a 'helpful' cleaning repair would pass")


def _oracle_missing_body_sections(root):
    """Every expected heading present, in `get_expected_sections` order, with
    the content already under the sections that existed still there. The
    discriminator is a note with SOME sections and REAL content under them: a
    build that writes the default body wholesale is RED, which is the WI-126
    shape."""
    # The ONE door: `vault` is bound HERE and nowhere else in this module.
    vault = _temp_vault(root)
    from obsidian_schemas.body_sections import get_expected_sections

    kept = "A real note somebody typed, which the repair must not discard.\n"
    partial = _plant(vault, "@Quenlaw Drostane",
                     _person("@Quenlaw Drostane", body=f"## Notes\n{kept}"))

    _, idx, issues = _scan(vault)
    subjects = [i for i in _fixable(issues)
                if i.check == "missing_body_sections" and i.file_path == partial]
    assert len(subjects) == 1, f"expected one subject, got {subjects}"
    lint_vault.apply_fixes(subjects, vault, idx)

    text = partial.read_text(encoding="utf-8")
    expected = get_expected_sections("person")
    order = [h for h in re.findall(r"^## (.+)$", text, re.MULTILINE) if h in expected]
    assert order == expected, (
        f"headings are {order}; the oracle is {expected} in that order")
    assert kept.strip() in text, (
        "pre-existing content under an existing section was discarded — a "
        "default-body rewrite rather than a repair")


def _oracle_meeting_missing_from_timeline(root):
    """The appended entry equals `_build_timeline_entry`'s declared format.
    Three discriminators: a meeting with FOUR topics (the `[:3]` truncation),
    one with NONE (the no-suffix arm), and a person whose Timeline already holds
    an entry (append, not replace)."""
    # The ONE door: `vault` is bound HERE and nowhere else in this module.
    vault = _temp_vault(root)
    _plant(vault, "Meeting 20260620 - Tarnquil Ostrivane", (
        "---\ntype: meeting\ndate: '2026-06-20'\n"
        "attendees:\n  - Tarnquil Ostrivane\n"
        "topics:\n  - alpha\n  - beta\n  - gamma\n  - delta\n---\n\n"
        "## Summary\nSomething happened.\n"))
    _plant(vault, "Meeting 20260621 - Tarnquil Ostrivane", (
        "---\ntype: meeting\ndate: '2026-06-21'\n"
        "attendees:\n  - Tarnquil Ostrivane\n---\n\n"
        "## Summary\nSomething else happened.\n"))
    existing = "### March 3, 2026\nAn entry that was already here.\n"
    person = _plant(vault, "@Tarnquil Ostrivane", _person(
        "@Tarnquil Ostrivane",
        body=f"## To Discuss\n\n## Timeline\n{existing}\n## Notes\n"))

    _, idx, issues = _scan(vault)
    subjects = [i for i in _fixable(issues)
                if i.check == "meeting_missing_from_timeline"
                and i.file_path == person]
    assert len(subjects) == 2, f"expected both meetings to fire, got {subjects}"
    lint_vault.apply_fixes(subjects, vault, idx)

    text = person.read_text(encoding="utf-8")
    assert "An entry that was already here." in text, (
        "the pre-existing Timeline entry was replaced rather than appended to")
    assert ("[[Meeting 20260620 - Tarnquil Ostrivane|Meeting]] - "
            "alpha, beta, gamma.") in text, (
        "the four-topic meeting must truncate at THREE topics and end with `.`")
    assert "delta" not in text, "the fourth topic must not be written"
    assert "[[Meeting 20260621 - Tarnquil Ostrivane|Meeting]]\n" in text, (
        "a meeting declaring no topics takes the no-suffix arm")
    assert "### June 20, 2026" in text and "### June 21, 2026" in text


def _oracle_broken_wikilink(root):
    """Both `[[old]]` and `[[old|alias]]` retarget to the resolved stem, and a
    link whose date matches TWO meetings is NOT rewritten. The ambiguous case is
    pure plant — the corpus's six meetings all carry distinct dates."""
    # The ONE door: `vault` is bound HERE and nowhere else in this module.
    vault = _temp_vault(root)
    _plant(vault, "Meeting 20260704 - Tarnquil Halvorne", (
        "---\ntype: meeting\ndate: '2026-07-04'\n---\n\n## Summary\nOne.\n"))
    # Two meetings sharing 20260705 — the ambiguity the repair must decline.
    for suffix in ("Alpha", "Beta"):
        _plant(vault, f"Meeting 20260705 - Tarnquil {suffix}", (
            "---\ntype: meeting\ndate: '2026-07-05'\n---\n\n## Summary\nTwo.\n"))

    linker = _plant(vault, "@Halvorne Ostrivane", _person(
        "@Halvorne Ostrivane",
        body=("## To Discuss\n\n## Timeline\n\n## Notes\n"
              "- [[Meeting 20260704 Missing]]\n"
              "- [[Meeting 20260704 Missing|that meeting]]\n"
              "- [[Meeting 20260705 Ambiguous]]\n")))

    _, idx, issues = _scan(vault)
    at_path = [i for i in issues
               if i.check == "broken_wikilink" and i.file_path == linker]
    fixable = [i for i in at_path if i.auto_fixable]
    assert len(fixable) == 2, (
        f"exactly the two unambiguous links are repairable, got {fixable}")
    assert len(at_path) == 3, "the ambiguous link is still REPORTED, just not fixable"

    lint_vault.apply_fixes(fixable, vault, idx)
    text = linker.read_text(encoding="utf-8")
    assert "[[Meeting 20260704 - Tarnquil Halvorne]]" in text
    assert "[[Meeting 20260704 - Tarnquil Halvorne|that meeting]]" in text
    assert "[[Meeting 20260704 Missing" not in text
    assert "[[Meeting 20260705 Ambiguous]]" in text, (
        "a date matching TWO meetings must not be rewritten — the repair has no "
        "way to choose and guessing rewrites a live link")


# ==========================================================================
# AC-2 — every detector that CAUSES A WRITE, in both directions.
# ==========================================================================

#: The SEVEN write-causing checks: the five auto-fixable ones, which decide what
#: gets WRITTEN, plus the two `garbage_candidate_*` ones, which are INFO and not
#: auto-fixable but are the sole input to `quarantine_garbage` and therefore
#: decide what gets RELOCATED — the irreversible write.
GARBAGE_CHECKS = ("garbage_candidate_person", "garbage_candidate_company")

#: The frozen corpus's OWN output over the pinned set, as `(filename, check) ->
#: ISSUE COUNT`. A COUNT and not a set of pairs: `check_timeline` emits per
#: (meeting, attendee) pair keyed on the PERSON's path, and three of the five
#: named attendees sit in two meetings each — so a build emitting one issue per
#: person rather than per pair drops three issues and is green against a
#: set-of-pairs assertion. The figure is a property of bytes pinned by
#: CORPUS_DIGEST, so it moves only when that digest does.
CORPUS_PINNED_ISSUES = {
    ("@Thrandell Ibberly.md", "meeting_missing_from_timeline"): 2,
    ("@Isolde Quenlaw.md", "meeting_missing_from_timeline"): 2,
    ("@Morvette Harkwell.md", "meeting_missing_from_timeline"): 2,
    ("@Caldreth Zebrant.md", "meeting_missing_from_timeline"): 1,
    ("@Elowick Varnholt.md", "meeting_missing_from_timeline"): 1,
}


def test_every_write_causing_detector_fires_exactly_on_its_declared_subjects():
    """Three legs: no false positives on 53 real-shaped notes, one planted
    subject per pinned member, and the move predicate pinned ARM BY ARM."""
    pinned = sorted(auto_fixable_emitter_checks([LINT_VAULT_PATH])) + list(GARBAGE_CHECKS)
    assert len(pinned) == 7, f"the pinned set is {pinned}"

    with _temp_root() as root:
        _check_the_corpus_is_a_false_positive_floor(root, pinned)
    with _temp_root() as root:
        _check_every_pinned_detector_fires_on_its_own_subject(root, pinned)
    with _temp_root() as root:
        _check_the_move_predicate_arm_by_arm(root)


def _check_the_corpus_is_a_false_positive_floor(root, pinned):
    """Leg (a). The corpus is 53 notes whose shapes were MEASURED from the live
    vault — diacritics, hyphens, an address-in-a-name, digit-named stems,
    stem/name divergence and three skip specimens — which is exactly what makes
    a naive detector over-fire on it."""
    # The ONE door: `vault` is bound HERE and nowhere else in this module.
    vault = _temp_vault(root)
    _, _, issues = _scan(vault)
    observed = {}
    for issue in issues:
        if issue.check in pinned:
            key = (issue.file_path.name, issue.check)
            observed[key] = observed.get(key, 0) + 1
    assert observed == CORPUS_PINNED_ISSUES, (
        f"the corpus's pinned-check output moved:\n"
        f"  unexpected {sorted(set(observed) - set(CORPUS_PINNED_ISSUES))}\n"
        f"  missing {sorted(set(CORPUS_PINNED_ISSUES) - set(observed))}\n"
        f"  miscounted "
        f"{sorted(k for k in set(observed) & set(CORPUS_PINNED_ISSUES) if observed[k] != CORPUS_PINNED_ISSUES[k])}")
    silent = set(pinned) - {"meeting_missing_from_timeline"}
    assert not {c for _, c in observed} & silent, (
        f"a detector that should be silent on the frozen corpus fired: {silent}")


def _check_every_pinned_detector_fires_on_its_own_subject(root, pinned):
    """Leg (b). Leg (a)'s six zeroes are satisfied identically by a build in
    which the checks return NOTHING; one planted subject per member is what
    makes them silence rather than blindness."""
    # The ONE door: `vault` is bound HERE and nowhere else in this module.
    vault = _temp_vault(root)
    subjects = {}

    subjects["field_type_mismatch"] = _plant(
        vault, "@Sennaby Ostrakine",
        _person("@Sennaby Ostrakine", extra="auto_created: 'true'\n"))
    subjects["person_missing_name"] = _plant(
        vault, "@Brenvik Lumbrek",
        "---\ntype: person\nname: ''\n---\n\n"
        "## To Discuss\n\n## Timeline\n\n## Notes\n")
    subjects["missing_body_sections"] = _plant(
        vault, "@Pellworth Ravensby",
        _person("@Pellworth Ravensby", body="## Notes\n"))
    _plant(vault, "Meeting 20260808 - Lumbrek Sennaby", (
        "---\ntype: meeting\ndate: '2026-08-08'\n"
        "attendees:\n  - Varnholt Quillam\n---\n\n## Summary\nMet.\n"))
    subjects["meeting_missing_from_timeline"] = _plant(
        vault, "@Varnholt Quillam", _person("@Varnholt Quillam"))
    _plant(vault, "Meeting 20260809 - Ravensby Quillam", (
        "---\ntype: meeting\ndate: '2026-08-09'\n---\n\n## Summary\nMet.\n"))
    subjects["broken_wikilink"] = _plant(
        vault, "@Ferrigan Nimbrook", _person(
            "@Ferrigan Nimbrook",
            body=("## To Discuss\n\n## Timeline\n\n## Notes\n"
                  "- [[Meeting 20260809 Wrong]]\n")))
    # The two quarantine subjects. Both `garbage_candidate_*` arms gate on a
    # TRUTHY `auto_created`, which occurs nowhere in the 53 notes — which is why
    # leg (a)'s two zeroes there are structural rather than lucky.
    subjects["garbage_candidate_person"] = _plant(
        vault, "@Ostrakine Zebrant",
        _person("@Ostrakine Zebrant", extra="auto_created: true\n"))
    subjects["garbage_candidate_company"] = _plant(
        vault, "@Drostane Holdings",
        "---\ntype: company\nname: Drostane Holdings\nauto_created: true\n---\n\n"
        "## People\n\n## Timeline\n\n## Documents\n\n## Notes\n")

    assert set(subjects) == set(pinned), "a pinned member has no planted subject"

    _, _, issues = _scan(vault)
    for check, path in sorted(subjects.items()):
        hits = [i for i in issues if i.check == check and i.file_path == path]
        assert len(hits) == 1, (
            f"{check} produced {len(hits)} issues at its own planted subject "
            f"{path.name}; the oracle is exactly one")


#: `classify_person_tier`'s SIX documented disjuncts, one planted specimen each,
#: every specimen `active` BY THAT DISJUNCT ALONE — every other disjunct false.
#: An implementation missing any arm returns `stub` for that specimen, and a
#: `stub` is a note `--quarantine` RELOCATES.
TIER_ARMS = {
    "auto_created false or missing": "",
    "2+ meeting wikilinks in Timeline":
        "## To Discuss\n\n## Timeline\n[[Meeting 20260104 - A]]\n"
        "[[Meeting 20260118 - B]]\n\n## Notes\n",
    "manual content in To Discuss or Notes":
        "## To Discuss\n- something to raise\n\n## Timeline\n\n## Notes\n",
    "1+ meeting AND a real email":
        "## To Discuss\n\n## Timeline\n[[Meeting 20260104 - A]]\n\n## Notes\n",
    "1+ meeting AND a company":
        "## To Discuss\n\n## Timeline\n[[Meeting 20260104 - A]]\n\n## Notes\n",
    "2+ plain-text timeline entries":
        "## To Discuss\n\n## Timeline\n### January 4, 2026\nA calendar event.\n"
        "### January 18, 2026\nAn intro.\n\n## Notes\n",
}


def _check_the_move_predicate_arm_by_arm(root):
    """Leg (c). Leg (b) proves the quarantine check fires on an OBVIOUS stub,
    which a `return "stub"` implementation also satisfies; only the per-arm
    table separates a correct classifier from a wrong-but-self-consistent one,
    and the cost of getting it wrong is a real note in `_quarantine/`.

    The enumeration is a declared NARROWING, not a derivation — the disjunction
    is four `if` statements over six conditions and has no table to iterate — so
    it is BOUND to the code by syntax ON BOTH SIDES.
    """
    # The ONE door: `vault` is bound HERE and nowhere else in this module.
    vault = _temp_vault(root)
    counts = person_tier_arm_counts([LINT_VAULT_PATH])
    bullets, active_sites = counts["scripts/lint_vault.py"]
    assert bullets == len(TIER_ARMS), (
        f"the docstring documents {bullets} disjuncts; this table declares "
        f"{len(TIER_ARMS)}")
    # The LOAD-BEARING half: a seventh arm added as a fifth
    # `if …: return "active"` moves this number whether or not the author
    # touches the docstring, which the bullet count alone cannot see.
    assert active_sites == 4, (
        f"`classify_person_tier` has {active_sites} `return \"active\"` sites; "
        f"the arm table was written against 4")

    plans = {
        "auto_created false or missing": "",
        "2+ meeting wikilinks in Timeline": "auto_created: true\n",
        "manual content in To Discuss or Notes": "auto_created: true\n",
        "1+ meeting AND a real email":
            "auto_created: true\nemails:\n  - someone@example.com\n",
        "1+ meeting AND a company": "auto_created: true\ncompany: Voxleaf Ltd\n",
        "2+ plain-text timeline entries": "auto_created: true\n",
    }
    for index, (arm, body) in enumerate(sorted(TIER_ARMS.items())):
        stem = f"@Arm{index} Tessamund"
        path = _plant(vault, stem, _person(
            stem, extra=plans[arm],
            body=body or "## To Discuss\n\n## Timeline\n\n## Notes\n"))
        files = lint_vault.read_vault(Path(path).parent)
        subject = next(f for f in files if f.path == path)
        assert lint_vault.classify_person_tier(subject) == "active", (
            f"the specimen for {arm!r} classifies as a stub — that arm is "
            f"missing, and a stub is a note `--quarantine` MOVES")

    stub_stem = "@Stubbly Tessamund"
    stub = _plant(vault, stub_stem,
                  _person(stub_stem, extra="auto_created: true\n"))
    files = lint_vault.read_vault(Path(stub).parent)
    subject = next(f for f in files if f.path == stub)
    assert lint_vault.classify_person_tier(subject) == "stub", (
        "a note satisfying NO disjunct must classify as a stub, or the table "
        "above is satisfiable by a classifier that answers `active` always")


# ==========================================================================
# AC-3 — the unreadable note is reported, indexed, quiet and never written.
# ==========================================================================

#: Bytes that are not valid UTF-8, the same shape the corpus's own
#: `@Isolde Varnholt.md` carries.
UNDECODABLE = b"---\ntype: person\nname: \xff\xfe\xfd\n---\n\n## Notes\n"


def test_an_unreadable_note_is_reported_indexed_and_never_silently_dropped():
    """Four legs over a planted non-UTF-8 note, plus the wall edit AC-3(a)
    describes."""
    _check_the_skip_reason_wall_reaches_the_script_without_moving_its_homes()
    with _temp_root() as root:
        _check_the_unreadable_note_is_reported_indexed_and_quiet(root)
    with _temp_root() as root:
        _check_the_unreadable_note_is_never_written_or_moved(root)


def _check_the_skip_reason_wall_reaches_the_script_without_moving_its_homes():
    """Leg (a)'s wall half. The UNIVERSE widens and the two declared-homes
    EXPECTED SETS do NOT, and that direction is the whole point: the derivation
    reports a file IFF one of its parsed Constants EQUALS a vocabulary member,
    so a CORRECTLY-written script is ABSENT from the reported set and a
    three-member equality would be greenable only by hand-typing the reason in
    the script — the exact drift this leg forbids."""
    universe = python_files_under(PACKAGE_ROOT, TESTS_ROOT, SCRIPTS_ROOT)
    # NON-VACUITY: a universe widened to a mistyped root is green for the wrong
    # reason.
    names = {p.relative_to(ROOT).as_posix() for p in universe}
    assert "scripts/lint_vault.py" in names, (
        "the widened universe does not reach the script; the two-member "
        "equality below would then be green because nobody looked")

    homes = skip_reason_literal_sites(universe, SKIP_REASONS)
    assert homes == {
        "obsidian_schemas/repositories/base.py",
        "tests/test_fixture_vault.py",
    }, f"the skip-reason vocabulary has a third hand-typed home: {sorted(homes)}"
    assert "scripts/lint_vault.py" not in homes, (
        "the script TRANSCRIBES the reason instead of importing it")

    # BOTH hand-typed call sites move, or the wall is half-extended and reads
    # green. Text, not syntax: `ast` is single-homed to `tests/derivations.py`.
    source = (TESTS_ROOT / "test_fixture_vault.py").read_text(encoding="utf-8")
    assert source.count(
        "python_files_under(PACKAGE_ROOT, TESTS_ROOT, SCRIPTS_ROOT)") == 2
    assert "python_files_under(PACKAGE_ROOT, TESTS_ROOT)" not in source


def _check_the_unreadable_note_is_reported_indexed_and_quiet(root):
    # The ONE door: `vault` is bound HERE and nowhere else in this module.
    vault = _temp_vault(root)
    undecodable = _plant_bytes(vault, "@Zebrant Corvallen", UNDECODABLE)

    # (b) INDEXED — and the DISCRIMINATOR, which is what separates "the skip is
    # loud" from "the report stopped lying about OTHER notes". Both of these
    # produce issues on the old code, which dropped the filename with the bytes.
    linker = _plant(vault, "@Corvallen Ashquill", _person(
        "@Corvallen Ashquill",
        body=("## To Discuss\n\n## Timeline\n\n## Notes\n"
              "- [[@Zebrant Corvallen]]\n")))
    meeting = _plant(vault, "Meeting 20260901 - Zebrant Corvallen", (
        "---\ntype: meeting\ndate: '2026-09-01'\n"
        "attendees:\n  - Zebrant Corvallen\n---\n\n## Summary\nMet.\n"))

    files, idx, issues = _scan(vault)
    assert "@Zebrant Corvallen" in idx["all_stems"], (
        "the unreadable note's STEM is gone from the index — five stem-keyed "
        "checks now report phantom breakage about healthy notes")

    # (a) REPORTED, with a reason from the IMPORTED vocabulary.
    at_path = [i for i in issues if i.file_path == undecodable]
    assert len(at_path) == 1, (
        f"expected exactly one issue for the unreadable note, got "
        f"{[(i.check, i.message) for i in at_path]}")
    issue = at_path[0]
    assert not issue.auto_fixable, (
        "an unreadable note must carry no auto-fixable issue — that is what "
        "places it OUTSIDE AC-4's per-issue partition by construction")
    carried = [r for r in SKIP_REASONS if r in issue.message]
    assert carried == [UNREADABLE], (
        f"the message must carry the imported reason value; got {issue.message!r}")

    # (b) the discriminator's two halves: neither healthy note is reported.
    assert not [i for i in issues if i.file_path == linker
                and i.check == "broken_wikilink"], (
        "a live link to the unreadable note is reported as broken — and one of "
        "those phantoms is AUTO-FIXABLE, so `--fix` rewrites it away from a "
        "target sitting right there on disk")
    assert not [i for i in issues if i.file_path == meeting
                and i.check == "meeting_attendee_not_found"], (
        "a meeting listing the unreadable note's person is reported as having a "
        "missing attendee")

    # (c) QUIET OTHERWISE — asserted for ALL of them, not only for the one the
    # build had to guard (`no_frontmatter`); `orphaned_note`, `possible_duplicate`
    # and every completeness check are safe BY CONSTRUCTION because each gates on
    # `vf.entity_type`, which stays "" for bytes that never parsed.
    assert issue.check == "unreadable_note"
    subject = next(f for f in files if f.path == undecodable)
    assert subject.entity_type == "" and subject.frontmatter == {}
    assert subject.read_error == UNREADABLE and subject.parse_error is None, (
        "read_error and parse_error are SIBLINGS and never both")
    assert subject.body == "" and subject.raw_content == "", (
        "undecodable bytes must never be decoded into any field")


def _check_the_unreadable_note_is_never_written_or_moved(root):
    """(d) NEVER WRITTEN — in no `--fix` target and in no `--quarantine` move."""
    # The ONE door: `vault` is bound HERE and nowhere else in this module.
    vault = _temp_vault(root)
    undecodable = _plant_bytes(vault, "@Zebrant Corvallen", UNDECODABLE)
    before = undecodable.read_bytes()

    _, idx, issues = _scan(vault)
    assert not [i for i in _fixable(issues) if i.file_path == undecodable]
    lint_vault.apply_fixes(_fixable(issues), vault, idx)
    assert undecodable.read_bytes() == before, "the unreadable note was rewritten"

    garbage = [i for i in issues if i.check.startswith("garbage_candidate_")]
    lint_vault.quarantine_garbage(garbage, vault)
    assert undecodable.exists(), "the unreadable note was MOVED"
    assert undecodable.read_bytes() == before


# ==========================================================================
# AC-4 — the four-bucket partition, the tie-break, the records, the print.
# ==========================================================================

#: A stem the semantic gate refuses, and a pattern a POSIX filename component
#: can actually raise (the shape WI-021's own fixture uses).
REFUSED_STEM = "@Unknown Contact Zeta-9"
REFUSED_PATTERN = "unknown_contact"


def test_every_auto_fixable_issue_is_accounted_for_and_the_printed_summary_says_so():
    """Four legs. The partition is per ISSUE and over FOUR buckets; the
    attribution rule is decided at the commit point of the write carrying each
    issue; the two new records are bounded; and the operator's printed LINE is
    read as bytes rather than inferred from the record."""
    with _temp_root() as root:
        _check_the_partition_is_total_over_four_buckets(root)
    with _temp_root() as root:
        _check_a_committed_write_is_never_relabelled_errored(root)
    with _temp_root() as root:
        _check_a_decline_is_attributed_at_its_own_branch(root)
    with _temp_root() as root:
        _check_the_two_new_records_are_typed_and_bounded(root)
    _check_the_printed_summary_carries_the_figures_the_run_computed()


def _decline_subjects(into):
    """One subject per DECLINE SITE, so the plant set is CLOSED rather than
    sampled. Returns `{guard: path}`."""
    # :890 — `auto_created` is already a bool, so `isinstance(raw, str)` is False.
    already_bool = _plant(into, "@Nimbrook Quenlaw",
                          _person("@Nimbrook Quenlaw", extra="auto_created: true\n"))
    # :906 — a type `get_expected_sections` returns [] for.
    untyped = _plant(into, "@Lumbrek Ashquill",
                     "---\ntype: watch\nname: Lumbrek Ashquill\n---\n\nbody\n")
    # :913 — declined for EVERY such issue whenever the caller takes `idx`'s own
    # signature default.
    _plant(into, "Meeting 20261010 - Ashquill Nimbrook", (
        "---\ntype: meeting\ndate: '2026-10-10'\n"
        "attendees:\n  - Ashquill Nimbrook\n---\n\n## Summary\nMet.\n"))
    attendee = _plant(into, "@Ashquill Nimbrook", _person("@Ashquill Nimbrook"))
    # :935-936 — a `suggested_fix` that is not JSON.
    # :963-973 — the repair's `old` text appears nowhere in the file, because
    # `check_links:510` STRIPPED the inner trailing space before emitting.
    _plant(into, "Meeting 20261011 - Quenlaw Lumbrek", (
        "---\ntype: meeting\ndate: '2026-10-11'\n---\n\n## Summary\nMet.\n"))
    absent = _plant(into, "@Quenlaw Ashquill", _person(
        "@Quenlaw Ashquill",
        body=("## To Discuss\n\n## Timeline\n\n## Notes\n"
              "- [[Meeting 20261011 Nonexistent ]]\n")))
    return {
        lint_vault.GUARD_AUTO_CREATED_NOT_A_STRING: already_bool,
        lint_vault.GUARD_NO_EXPECTED_SECTIONS: untyped,
        lint_vault.GUARD_NO_MEETING_INDEX: attendee,
        lint_vault.GUARD_UNPARSABLE_SUGGESTED_FIX: absent,
        lint_vault.GUARD_LINK_TEXT_ABSENT: absent,
    }


def _check_the_partition_is_total_over_four_buckets(root):
    """Leg (a). Every auto-fixable issue handed in ends `repaired`, `refused`,
    `errored` or `declined`; the four sets are pairwise disjoint by issue
    identity and their union is the input."""
    # The ONE door: `vault` is bound HERE and nowhere else in this module.
    vault = _temp_vault(root)
    subjects = _decline_subjects(vault)
    _plant(vault, "@Harkwell Voxleaf",
           _person("@Harkwell Voxleaf", body="## Notes\n"))        # repairable
    refused_note = _plant(vault, REFUSED_STEM,
                          "---\ntype: person\nname: ''\n---\n\n"
                          "## To Discuss\n\n## Timeline\n\n## Notes\n")
    vanished = Path(vault) / "gone" / "@Never Existed.md"          # errored

    _, idx, issues = _scan(vault)
    handed = _fixable(issues)
    # `idx` is deliberately NOT passed, which is what makes :913 decline every
    # `meeting_missing_from_timeline` issue — the 315-live case the summary
    # currently reports as a clean pass.
    handed = handed + [lint_vault.LintIssue(
        file_path=vanished, check="person_missing_name",
        severity=lint_vault.Severity.WARNING, message="planted",
        category="completeness", auto_fixable=True)]
    # THREE decline sites are reachable only through a HAND-BUILT issue, and
    # that is a property of the frame rather than a shortcut: a detector never
    # emits them. `check_structural` emits `field_type_mismatch` only when
    # `auto_created` IS a string, and `missing_body_sections` only for a type
    # `TYPE_TO_MODEL` carries — so the two guards below sit on branches an
    # honest scan cannot reach, which is exactly why they could decline forever
    # without anything going red. The third is the unparsable `suggested_fix`.
    for check, guard, extra in (
        ("field_type_mismatch", lint_vault.GUARD_AUTO_CREATED_NOT_A_STRING, {}),
        ("missing_body_sections", lint_vault.GUARD_NO_EXPECTED_SECTIONS, {}),
        ("broken_wikilink", lint_vault.GUARD_UNPARSABLE_SUGGESTED_FIX,
         {"suggested_fix": "{not json"}),
    ):
        handed = handed + [lint_vault.LintIssue(
            file_path=subjects[guard], check=check,
            severity=lint_vault.Severity.WARNING, message="planted",
            category="structural", auto_fixable=True, **extra)]

    captured = io.StringIO()
    with contextlib.redirect_stderr(captured):
        outcome = lint_vault.apply_fixes(handed, vault)

    total = (outcome.repaired + len(outcome.refused)
             + len(outcome.errored) + len(outcome.declined))
    assert total == len(handed), (
        f"{len(handed)} auto-fixable issues in, {total} accounted for: "
        f"repaired {outcome.repaired}, refused {len(outcome.refused)}, "
        f"errored {len(outcome.errored)}, declined {len(outcome.declined)}")
    assert outcome.repaired and outcome.refused and outcome.errored \
        and outcome.declined, (
        "each bucket must be non-empty in this run, or the equality above is "
        "satisfiable by a build in which three of the four are dead code")
    assert any(r.path == refused_note for r in outcome.refused)

    # The plant set is CLOSED over the five decline sites, and every guard id
    # observed is a member of the declared vocabulary.
    guards = {d.guard for d in outcome.declined}
    assert guards == set(lint_vault.DECLINE_GUARDS), (
        f"the run exercised {sorted(guards)}; the declared vocabulary is "
        f"{sorted(lint_vault.DECLINE_GUARDS)}")
    assert not (set(lint_vault.DECLINE_GUARDS) & set(SKIP_REASONS)), (
        "a guard id has joined the vocabulary the skip-reason wall polices")
    for guard, path in subjects.items():
        assert any(d.guard == guard and d.path == path
                   for d in outcome.declined), f"{guard} did not fire at {path}"


def _check_a_committed_write_is_never_relabelled_errored(root):
    """Leg (b), the M4 half. ONE file carrying a `missing_body_sections` issue
    whose FIRST write commits beside a `broken_wikilink` issue whose SECOND
    write raises: the first is `repaired` and only the second is `errored`.

    A build that folds once at the END of the lock block returns BOTH as
    `errored` — it reports a write that reached one of Dave's notes as one that
    failed, which sends the operator to re-run a repair already on disk.
    """
    # The ONE door: `vault` is bound HERE and nowhere else in this module.
    vault = _temp_vault(root)
    _plant(vault, "Meeting 20261112 - Voxleaf Harkwell", (
        "---\ntype: meeting\ndate: '2026-11-12'\n---\n\n## Summary\nMet.\n"))
    mixed = _plant(vault, "@Voxleaf Harkwell", _person(
        "@Voxleaf Harkwell",
        body="## Notes\n- [[Meeting 20261112 Wrong]]\n"))

    _, idx, issues = _scan(vault)
    handed = [i for i in _fixable(issues) if i.file_path == mixed]
    assert {i.check for i in handed} == {
        "missing_body_sections", "broken_wikilink"}, (
        f"the discriminating plant must carry BOTH issues, got {handed}")

    real_write = lint_vault.vault_io.write_note
    calls = []

    def second_write_raises(path, content, **kwargs):
        calls.append(path)
        if len(calls) >= 2:
            raise RuntimeError("the wikilink write failed")
        return real_write(path, content, **kwargs)

    captured = io.StringIO()
    with patcher() as patch, contextlib.redirect_stderr(captured):
        patch.setattr(lint_vault.vault_io, "write_note", second_write_raises)
        outcome = lint_vault.apply_fixes(handed, vault, idx)

    assert len(calls) == 2, "both writes must have been attempted"
    assert outcome.repaired == 1, (
        f"the issue whose write COMMITTED must stay repaired; got "
        f"{outcome.repaired}")
    assert len(outcome.errored) == 1 and outcome.errored[0].path == mixed
    assert outcome.errored[0].reason == "RuntimeError", (
        "the error record carries the exception's CLASS NAME and never str(exc)")
    assert outcome.repaired + len(outcome.errored) == len(handed)


def _check_a_decline_is_attributed_at_its_own_branch(root):
    """Leg (b), the TIE-BREAK. ONE file holding a declined issue AND an issue
    the gate then refuses: the decline STAYS declined.

    A declined issue contributed nothing to `delta`, so it was never in the
    write the gate refused; labelling it `refused` would attribute it to a gate
    that never saw it and make the refusal count un-actionable.
    """
    # The ONE door: `vault` is bound HERE and nowhere else in this module.
    vault = _temp_vault(root)
    both = _plant(vault, REFUSED_STEM,
                  "---\ntype: person\nname: ''\n---\n\n"
                  "## To Discuss\n\n## Timeline\n\n## Notes\n")
    handed = [
        lint_vault.LintIssue(
            file_path=both, check="meeting_missing_from_timeline",
            severity=lint_vault.Severity.WARNING, message="planted",
            category="timeline", auto_fixable=True,
            suggested_fix="Meeting 20260104 - Voxleaf Kelmarra"),
        lint_vault.LintIssue(
            file_path=both, check="person_missing_name",
            severity=lint_vault.Severity.WARNING, message="planted",
            category="completeness", auto_fixable=True),
    ]

    captured = io.StringIO()
    with contextlib.redirect_stderr(captured):
        # `idx` omitted — the signature's OWN default, which is what makes the
        # timeline issue decline at its branch before the gate is reached.
        outcome = lint_vault.apply_fixes(handed, vault)

    assert len(outcome.declined) == 1, (
        f"the timeline issue must be DECLINED at its own branch, got "
        f"{outcome.declined}")
    assert outcome.declined[0].guard == lint_vault.GUARD_NO_MEETING_INDEX
    assert outcome.declined[0].check == "meeting_missing_from_timeline"
    assert len(outcome.refused) == 1, (
        "exactly the issue the gate actually saw is refused — a build whose "
        "rule reads 'every issue on a refused file is refused' returns 2 here")
    assert outcome.refused[0].pattern == REFUSED_PATTERN
    assert outcome.repaired == 0 and outcome.errored == ()
    assert len(outcome.declined) + len(outcome.refused) == len(handed)


def _check_the_two_new_records_are_typed_and_bounded(root):
    """Leg (c). Both records are CLOSED like their sibling, both carry bounded
    values, and the refusal bucket keeps its exact-type filter — so a corrupt
    fence lands in ERRORED and not in refused."""
    # The ONE door: `vault` is bound HERE and nowhere else in this module.
    vault = _temp_vault(root)
    assert lint_vault.FixOutcome._fields == (
        "repaired", "refused", "errored", "declined")
    assert lint_vault.FixErrorRecord._fields == ("path", "reason")
    assert lint_vault.FixDeclineRecord._fields == ("path", "check", "guard")
    # The sibling's own closure does NOT move: per-ISSUE refusal counting is
    # obtained by emitting one record per refused issue, never by widening it.
    assert lint_vault.NameGateRefusalRecord._fields == ("path", "pattern")

    unclosed = _plant(vault, "@Broken Fence Ostrivane",
                      "---\ntype: person\nname: Broken Fence\n\nno closing fence\n")
    handed = [lint_vault.LintIssue(
        file_path=unclosed, check="person_missing_name",
        severity=lint_vault.Severity.WARNING, message="planted",
        category="completeness", auto_fixable=True)]

    captured = io.StringIO()
    with contextlib.redirect_stderr(captured):
        outcome = lint_vault.apply_fixes(handed, vault)

    assert outcome.refused == (), (
        "a corrupt fence is a sibling leaf of the SAME hierarchy root and is "
        "NOT a gate refusal")
    assert len(outcome.errored) == 1
    assert outcome.errored[0].reason == "FrontmatterParseError", (
        "the near-miss says where it did NOT go; this says where it DID")
    assert "\n" not in outcome.errored[0].reason
    for record in outcome.errored:
        assert record.reason.isidentifier(), (
            f"{record.reason!r} is not a bounded class name — note bytes and "
            f"str(exc) must never reach an operator-facing summary")


def _summary_figures(text):
    """Parse the printed line into `{label: int}` — a STRUCTURAL parse and never
    a substring match."""
    lines = [ln for ln in text.splitlines() if ln.startswith("Fix summary: ")]
    assert len(lines) == 1, f"expected exactly one summary line, got {lines}"
    figures = {}
    for part in lines[0][len("Fix summary: "):].split(", "):
        label, _, value = part.rpartition(" ")
        figures[label] = int(value)
    return figures


def _planted_vault_a(into):
    _plant(into, "@Harkwell Voxleaf", _person("@Harkwell Voxleaf", body="## Notes\n"))
    _plant(into, REFUSED_STEM, "---\ntype: person\nname: ''\n---\n\n"
                                "## To Discuss\n\n## Timeline\n\n## Notes\n")
    _plant(into, "Meeting 20261011 - Quenlaw Lumbrek", (
        "---\ntype: meeting\ndate: '2026-10-11'\n---\n\n## Summary\nMet.\n"))
    _plant(into, "@Quenlaw Ashquill", _person(
        "@Quenlaw Ashquill",
        body=("## To Discuss\n\n## Timeline\n\n## Notes\n"
              "- [[Meeting 20261011 Nonexistent ]]\n")))


def _planted_vault_b(into):
    _planted_vault_a(into)
    _plant(into, "@Ravensby Voxleaf", _person("@Ravensby Voxleaf", body="## Notes\n"))
    _plant(into, "@Unknown Contact Zeta-8", "---\ntype: person\nname: ''\n---\n\n"
                                             "## To Discuss\n\n## Timeline\n\n## Notes\n")
    _plant(into, "@Lumbrek Quenlaw", _person(
        "@Lumbrek Quenlaw",
        body=("## To Discuss\n\n## Timeline\n\n## Notes\n"
              "- [[Meeting 20261011 Alsomissing ]]\n")))
    _plant_bytes(into, "@Corvallen Zebrant", UNDECODABLE)


def _check_the_printed_summary_carries_the_figures_the_run_computed():
    """Leg (d). The check CAPTURES REAL STDOUT and binds every figure on the
    line to the number the same run computed — because a count that exists only
    in a returned tuple is bookkeeping, not accounting, and the precedent for
    getting this exactly wrong is in the file this item edits.

    TWO-SIDED over two planted vaults with different figure vectors, so a
    hard-coded line, a line printing only two of the five, and a line whose
    fifth figure is a constant are each RED.
    """
    labels = lint_vault.FIX_SUMMARY_LABELS
    # Pinned by a hand-written equality — with the fifth member IMPORTED rather
    # than spelled, because the printed label and the skip reason are the same
    # word and a bare copy of it here would redden the wall AC-3(a) states.
    assert labels == ("repaired", "refused", "errored", "declined", UNREADABLE)

    vectors = []
    for plant in (_planted_vault_a, _planted_vault_b):
        # The PRINTED side.
        with _temp_root() as root:
            vault = _temp_vault(root)
            plant(vault)
            printed = io.StringIO()
            with contextlib.redirect_stdout(printed), \
                    contextlib.redirect_stderr(io.StringIO()):
                lint_vault.run_lint(vault, do_fix=True, quiet=True)
            figures = _summary_figures(printed.getvalue())

        # The COMPUTED side: an independent `apply_fixes` over a SECOND
        # materialization of the same planted vault, through the issue list
        # `run_lint` itself builds.
        with _temp_root() as root:
            vault = _temp_vault(root)
            plant(vault)
            files, idx, issues = _scan(vault)
            with contextlib.redirect_stderr(io.StringIO()):
                outcome = lint_vault.apply_fixes(_fixable(issues), vault, idx)
            expected = {
                "repaired": outcome.repaired,
                "refused": len(outcome.refused),
                "errored": len(outcome.errored),
                "declined": len(outcome.declined),
                UNREADABLE: sum(1 for f in files if f.read_error),
            }

        assert set(figures) == set(labels), (
            f"the line carries {sorted(figures)}; all five labels are required")
        assert figures == expected, (
            f"the printed line says {figures}; the same run computed {expected}")
        vectors.append(figures)

    # The VARIATION requirement: a constant in any of these positions is RED.
    for label in ("repaired", "refused", "declined", UNREADABLE):
        assert vectors[0][label] != vectors[1][label], (
            f"{label} took the same value on both planted vaults, so this leg "
            f"cannot tell a computed figure from a hard-coded one")
    # `errored` is NOT producible end-to-end through `run_lint`'s own issue list
    # — a corrupt-fence note emits the non-fixable `parse_error` issue and never
    # enters `apply_fixes` — so it is asserted FORMAT-only here and BY VALUE at
    # the `apply_fixes` frame by legs (a)-(c).
    for vector in vectors:
        assert isinstance(vector["errored"], int)


def test_the_fix_summary_prints_even_when_nothing_is_auto_fixable():
    """Design §5 ruling 1, a NON-AC sibling. Today the print sat inside
    `if fixable:` and the else-arm said "No auto-fixable issues found." — so the
    figure an operator most needs on a bad run (`unreadable`) was absent exactly
    when nothing was fixable."""
    with _temp_root() as root:
        vault = _temp_vault(root)
        with contextlib.redirect_stdout(io.StringIO()), \
                contextlib.redirect_stderr(io.StringIO()):
            lint_vault.run_lint(vault, do_fix=True, quiet=True)   # converges
        printed = io.StringIO()
        with contextlib.redirect_stdout(printed), \
                contextlib.redirect_stderr(io.StringIO()):
            lint_vault.run_lint(vault, do_fix=True, quiet=True)
        text = printed.getvalue()

    assert "No auto-fixable issues found." not in text
    figures = _summary_figures(text)
    assert figures["repaired"] == 0, (
        f"the second pass has nothing left to repair; got {figures}")
    assert figures[UNREADABLE] == 1, (
        "the corpus's one undecodable member is still reported on a run with "
        "nothing to fix — which is exactly when that figure matters most")


# ==========================================================================
# AC-5 — the live-vault baseline, read back off the tree.
# ==========================================================================

#: `docs/vault-shape-census.md`'s auto-fixable table is keyed on the MESSAGE
#: SHAPE, so "compared rule by rule" has no join without this. Keyed on the
#: shape and NEVER on the table's parenthetical CATEGORY: the census annotates
#: `Empty name` as `(structural)` while that emitter's own category is
#: `"completeness"`, so a category-keyed mapping mis-joins one row in five.
CENSUS_SHAPE_TO_RULE = {
    "Missing sections: …": "missing_body_sections",
    "Attended [[…]] but it's not in Timeline": "meeting_missing_from_timeline",
    "auto_created is string '…' instead of bool": "field_type_mismatch",
    "Empty name (suggest: '…')": "person_missing_name",
    "[[…]] doesn't resolve (fixable → [[…]])": "broken_wikilink",
}

BASELINE_HEADINGS = {
    "0": "## 0. The run",
    "1": "## 1. The five auto-fixable counts",
    "2": "## 2. The five stem-keyed check counts",
    "3": "## 3. The undecodable scan",
    "4": "## 4. Post-build attestation",
}
_HEX40 = re.compile(r"(?<![0-9a-fA-F])[0-9a-f]{40}(?![0-9a-fA-F])")


def baseline_sections(text):
    """`{ordinal: section text}`, matched by heading PREFIX and never equality —
    §1's and §2's headings carry a trailing qualifier the artifact is entitled
    to. A missing, duplicate or unmatched ordinal RAISES with the heading
    quoted."""
    sections, current, buffer = {}, None, []
    for line in text.splitlines():
        if line.startswith("## "):
            if current is not None:
                sections[current] = "\n".join(buffer)
            match = re.match(r"## (\d+)\.", line)
            if match is None:
                raise AssertionError(f"unnumbered section heading: {line!r}")
            ordinal = match.group(1)
            expected = BASELINE_HEADINGS.get(ordinal)
            if expected is None or not line.startswith(expected):
                raise AssertionError(
                    f"heading {line!r} does not match the declared prefix "
                    f"{expected!r}")
            if ordinal in sections:
                raise AssertionError(f"duplicate section ordinal {ordinal}")
            current, buffer = ordinal, []
        elif current is not None:
            buffer.append(line)
    if current is not None:
        sections[current] = "\n".join(buffer)
    missing = set(BASELINE_HEADINGS) - set(sections)
    if missing:
        raise AssertionError(f"sections absent from the artifact: {sorted(missing)}")
    return sections


def fenced_blocks(section_text):
    """The triple-backtick-delimited blocks of one section, in order."""
    blocks, current = [], None
    for line in section_text.splitlines():
        if line.startswith("```"):
            if current is None:
                current = []
            else:
                blocks.append("\n".join(current))
                current = None
        elif current is not None:
            current.append(line)
    return blocks


def is_argv_fence(block):
    """True when the block's first non-empty line is an absolute path naming a
    python interpreter. This is the leg's RE-EXECUTABILITY element, and it is
    what replaced the `Command:` line the artifact does not carry: §0 spells its
    introduction `Command (the JSON report; …):` and §3 has no such line at
    all."""
    for line in block.splitlines():
        if line.strip():
            return line.strip().startswith("/") and "python" in line
    return False


def _int(cell):
    return int(cell.replace(",", "").strip())


def baseline_auto_fixable_rows(text):
    """§1's four-column table as `{rule_id: (census, today, delta)}`.

    Three row facts, each read off the committed bytes rather than assumed: the
    SIXTH row is a TOTALS row carrying no backticked identifier and is skipped
    BY THAT PROPERTY rather than by a hardcoded index, so a sixth rule row
    inserted above it cannot shift the skip onto a real rule; the rule id is the
    FIRST backticked span of column 1, which tolerates row five's trailing
    annotation; and the census cell is the LEADING integer before its
    parenthetical message shape.
    """
    rows = {}
    in_body = False
    for line in baseline_sections(text)["1"].splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) != 4:
            continue
        if set(cells[1]) <= set("-: "):
            in_body = True          # the separator row — the header is above it
            continue
        if not in_body:
            continue                # the HEADER row, whose first cell is
            # `` `check` (auto_fixable=True) `` and therefore carries a
            # backticked span exactly as a rule row does
        ids = re.findall(r"`([^`]+)`", cells[0])
        if not ids:
            continue            # the totals row — no backticked identifier
        rule = ids[0]
        census = re.match(r"([\d,]+)", cells[1])
        if census is None:
            raise AssertionError(f"non-integer census cell for {rule}: {cells[1]!r}")
        if rule in rows:
            raise AssertionError(f"duplicate rule id in the baseline table: {rule}")
        rows[rule] = (_int(census.group(1)), _int(cells[2]), _int(cells[3]))
    return rows


def _census_rows():
    """Design §9's FIFTH census reader, which lands beside the other four in
    `tests/test_fixture_vault.py` and is IMPORTED here — never re-implemented.

    The category vocabulary is handed in from this side because it must be read
    off the LOADED script module and the census readers' module has no loader
    (and may not mint a second one — see `_load_lint_vault`'s docstring and the
    work item's Build Log D5). This is the one line that holds that seam.
    """
    return census_auto_fixable_rows(
        CENSUS.read_text(encoding="utf-8"),
        categories=lint_vault.CATEGORY_ORDER)


def test_the_live_vault_baseline_is_committed_shaped_and_agrees_with_the_census():
    """Four legs over `docs/lint-vault-live-baseline.md`, the conductor's entry
    measurement — the criterion that stops this acceptance set being 100%
    hermetic.

    CORPUS_COUPLING: this check pins the committed TEXT of two conductor-owned
    artifacts, one of them digest-frozen. It consumes no behaviour of any module
    and no shape of any live population, so an ordinary ship cannot move what it
    reads.
    """
    _check_the_reader_predicates_reach_their_claimed_shapes()
    text = BASELINE.read_text(encoding="utf-8")
    sections = baseline_sections(text)
    _check_the_baseline_is_present_and_shaped(text, sections)
    _check_the_baseline_agrees_with_the_frozen_census(text)
    _check_the_undecodable_count_is_present_typed_and_clean(sections)
    _check_the_exit_obligation_is_committed_as_text(sections)


def _check_the_baseline_is_present_and_shaped(text, sections):
    """Leg (a). MEASURED and DERIVED sections are held to DIFFERENT contracts,
    because §1 and §2 are read off §0's single report and re-running a command
    per section would be a second walk of Dave's vault for numbers §0 already
    holds."""
    # The HEAD SHA, ONCE, in the HEADER REGION — above `## 0. The run` — and
    # matched DELIMITED at both ends. Both scopings are properties of the bytes:
    # §0 carries a 64-hex sha256 inside which an undelimited 40-hex scan finds
    # twenty-five matches, and §4's `post-build HEAD` row acquires a SECOND real
    # 40-hex SHA when the conductor fills the exit column at `ready → done` —
    # and this check sits on the floor and runs for good.
    header = text.split(BASELINE_HEADINGS["0"])[0]
    assert len(_HEX40.findall(header)) == 1, (
        "the header region must carry the tree's HEAD SHA exactly once")

    for ordinal in ("0", "3"):
        blocks = fenced_blocks(sections[ordinal])
        assert len(blocks) >= 2, (
            f"§{ordinal} is a MEASURED section and carries {len(blocks)} fences")
        assert any(is_argv_fence(b) for b in blocks), (
            f"§{ordinal} carries no argv fence — nothing a reader can re-run to "
            f"contradict the number")
        assert not is_argv_fence(blocks[-1]), (
            f"§{ordinal}'s LAST fence must be the verbatim stdout")
    for ordinal in ("1", "2"):
        assert fenced_blocks(sections[ordinal]) == [], (
            f"§{ordinal} is a DERIVED section and must carry no fence at all")
        assert sections[ordinal].count("|") > 0, f"§{ordinal} carries no table"
        assert re.search(r"[Dd]erived from|from the same report", sections[ordinal]), (
            f"§{ordinal} must name the §0 run its numbers come from")


def _check_the_baseline_agrees_with_the_frozen_census(text):
    """Leg (b), the load-bearing one. This document's ENTIRE argument for
    covering all five rules rather than only the ones that fire rests on a
    five-row table measured on one day in a vault that churns.

    THE TOLERANCE: a rule whose CENSUS count is ZERO must still be zero (strict
    — AC-1's "no live subject" argument and AC-2's false-positive floor both
    lean on those two zeroes); a rule whose census count is NON-ZERO must still
    be non-zero (SIGN pinned, magnitude free); and in BOTH directions the
    computed `baseline − census` must EQUAL the artifact's own delta column,
    which is what stops a mis-stated delta passing with two legal endpoints.
    """
    census_rows = _census_rows()
    assert set(census_rows) == set(CENSUS_SHAPE_TO_RULE), (
        f"the census table's shapes moved: {sorted(census_rows)}")
    # The mapping's VALUE set is BOUND to the derived rule set, so a sixth
    # auto-fixable rule reddens this leg until someone decides whether the
    # census covers it.
    assert set(CENSUS_SHAPE_TO_RULE.values()) == auto_fixable_emitter_checks(
        [LINT_VAULT_PATH])

    baseline_rows = baseline_auto_fixable_rows(text)
    assert set(baseline_rows) == set(CENSUS_SHAPE_TO_RULE.values()), (
        f"the baseline's §1 rows are {sorted(baseline_rows)}")

    for shape, rule in sorted(CENSUS_SHAPE_TO_RULE.items()):
        census = census_rows[shape]
        stated_census, today, delta = baseline_rows[rule]
        assert stated_census == census, (
            f"{rule}: the baseline restates the census as {stated_census} where "
            f"`docs/vault-shape-census.md` (2026-09-07) carries {census}")
        if census == 0:
            assert today == 0, (
                f"{rule}: the census measured 0 on 2026-09-07 and the baseline "
                f"reports {today} — a rule that acquired a live subject "
                f"falsifies an argument this item makes")
        else:
            assert today > 0, (
                f"{rule}: the census measured {census} on 2026-09-07 and the "
                f"baseline reports {today} — a rule that fell to zero falsifies "
                f"the other half of the same argument")
        assert today - census == delta, (
            f"{rule}: the artifact states a delta of {delta} while its own two "
            f"numbers ({census} on 2026-09-07, {today}) differ by "
            f"{today - census}")


def _check_the_undecodable_count_is_present_typed_and_clean(sections):
    """Leg (c). The count is the finding; the filenames are the operator's
    business and never the repo's.

    THE PRIVACY SCAN IS §3's STDOUT FENCE AND NEVER THE SECTION OR THE FILE, and
    the reason is in the committed bytes: §3's ARGV fence legitimately carries
    `rglob('*.md')` and an interpreter path, and §0's fences plus the header
    carry the project interpreter's own absolute path BY DESIGN — so a
    section-wide or file-wide scan is RED against a correct artifact.
    """
    stdout_fence = fenced_blocks(sections["3"])[-1]
    match = re.search(r"undecodable:\s*(\d+)", stdout_fence)
    assert match is not None, "§3's stdout fence carries no `undecodable:` count"
    assert int(match.group(1)) >= 0
    from tests.test_vault_path_required import FORBIDDEN_DEFAULT_PATTERNS
    # The pattern list is IMPORTED rather than spelled — it tracks the shipped
    # wall, and spelling one of its members here would make this very assertion
    # an offender of the text scan that owns it.
    named = [p for p in FORBIDDEN_DEFAULT_PATTERNS if p in stdout_fence]
    assert not named, f"a captured output names an absolute path: {named}"
    assert ".md" not in stdout_fence, "a captured output names a note filename"


def _check_the_exit_obligation_is_committed_as_text(sections):
    """Leg (d). An exit act that lives only in prose evaporates; committing the
    commands and the figure names as BYTES turns the ship step into a re-run and
    its absence into something a reader can see.

    PRESENCE AND NEVER EMPTINESS. The `exit` cells are unasserted in both
    directions: the conductor FILLS them at `ready → done` on this very item, so
    a leg asserting emptiness would go RED at its own close-out on an artifact
    completed exactly as this document prescribes.
    """
    exit_section = sections["4"]
    # §4's commands are INLINE code spans, not a fence, so this leg must not
    # demand one of it — §4 is neither a MEASURED nor a DERIVED section.
    assert fenced_blocks(exit_section) == []
    spans = re.findall(r"`([^`]+)`", exit_section)
    assert sum(1 for s in spans if "lint_vault.py" in s) >= 2, (
        "§4 must carry the re-run commands verbatim")
    assert any("undecodable" in s for s in spans)

    figures = " ".join(spans)
    for rule in sorted(auto_fixable_emitter_checks([LINT_VAULT_PATH])):
        assert rule in figures, (
            f"{rule} is absent from §4's figure column — a rule added later "
            f"cannot slip out of the exit obligation")
    assert "paths walked" in exit_section and "undecodable" in exit_section
    assert "post-build HEAD" in exit_section


def _check_the_reader_predicates_reach_their_claimed_shapes():
    """WI-235 for the five readers, whose oracles are match-shape claims over
    two committed artifacts and which fail the same way a count does when the
    matcher is narrower than its claim.

    `census_auto_fixable_rows` is graded here THROUGH THE IMPORT — it lives
    beside its four census siblings in `tests/test_fixture_vault.py` (Design §9)
    — so this fixture drives the shipped reader and never a copy."""
    # A heading with a trailing qualifier matched by PREFIX — and the near-miss,
    # a different ordinal, which must RAISE rather than be silently absorbed.
    planted = ("## 0. The run\na\n## 1. The five auto-fixable counts (vs x)\nb\n"
               "## 2. The five stem-keyed check counts (pre-change baseline)\nc\n"
               "## 3. The undecodable scan\nd\n## 4. Post-build attestation\ne\n")
    assert set(baseline_sections(planted)) == set(BASELINE_HEADINGS)
    try:
        baseline_sections(planted.replace("## 3.", "## 7."))
        raise AssertionError("an unmatched ordinal must RAISE")
    except AssertionError as exc:
        assert "7" in str(exc) or "absent" in str(exc)

    # The ARGV/stdout discrimination.
    assert is_argv_fence("\n/usr/bin/python3 -c 'x'\n")
    assert not is_argv_fence("paths walked: 3952\nundecodable: 0\n")
    # A 64-hex sha256 offered to the 40-hex DELIMITED matcher.
    assert not _HEX40.findall("b5c69cec51eece150f7e5d3657034ab5cce75f0e4da7743da688a3f15bb24b4b")
    assert _HEX40.findall("HEAD `e0ffbe860937ec775d286521181358ccdd2aec06` (pre-build)")

    # The bold totals row SKIPPED by its own property, and a category
    # parenthetical stripped while `(suggest: '…')` survives as part of the key.
    rows = census_auto_fixable_rows(
        "| rule | count |\n|---|---|\n"
        "| `Missing sections: …` (structural) | 821 |\n"
        "| `Empty name (suggest: '…')` | 0 |\n"
        "| **total** | **1,155 of 4,730** |\n",
        categories=lint_vault.CATEGORY_ORDER)
    assert rows == {"Missing sections: …": 821, "Empty name (suggest: '…')": 0}, rows
    totals = baseline_auto_fixable_rows(
        "## 0. The run\n## 1. The five auto-fixable counts\n"
        "| a | b | c | d |\n|---|---|---|---|\n"
        "| `missing_body_sections` | 821 (`x`) | 835 | +14 |\n"
        "| **total auto-fixable** | **1,155 of 4,730** | **1,169** | +14 |\n"
        "## 2. The five stem-keyed check counts\n## 3. The undecodable scan\n"
        "## 4. Post-build attestation\n")
    assert totals == {"missing_body_sections": (821, 835, 14)}, totals


# ==========================================================================
# WI-301 — the INBOUND half: the standing walls this item's files JOIN.
# ==========================================================================

#: The files this item creates or modifies. Every one JOINS the universes of the
#: walls below, and those walls' claims must hold of them.
TOUCHED_FILES = (
    "scripts/lint_vault.py",
    "tests/derivations.py",
    "tests/test_lint_vault_fix_rules.py",
    "tests/test_fixture_vault.py",
    "tests/test_lint_vault_fix_gate.py",
    "tests/test_name_gate_refusals.py",
    "tests/test_name_gate_identifiers.py",
    "tests/test_name_gate_delta_rule.py",
    "tests/test_ac_interpreter.py",
)

#: The filesystem-mutation capabilities this module is permitted to name, all of
#: them inside its two plant helpers. The ROUTING wall's own universe stops at
#: `(obsidian_schemas, scripts)` and does not reach `tests/` — every check module
#: that plants a note names one of these — so the assertion here is a CLOSED SET
#: rather than a zero: `rmtree`, `unlink`, `rename` and their siblings have no
#: business in a module whose only job is to write fixtures.
PERMITTED_PLANT_CAPABILITIES = frozenset({"write_text", "write_bytes"})


def test_wall_membership_is_closed_for_every_file_this_item_touches():
    """Each standing wall's OWN shipped predicate, RUN on this item's touched
    files' final text — never a re-implementation of it."""
    touched = [ROOT / name for name in TOUCHED_FILES]
    for path in touched:
        assert path.exists(), f"{path} — a Write Target that is not on disk"

    _check_the_routing_walls(touched)
    _check_the_process_boundary_is_refused_at_the_import()
    _check_the_derived_walls_this_item_joins(touched)
    _check_every_criterion_resolves_to_exactly_one_module()


def _check_the_routing_walls(touched):
    script = ROOT / "scripts" / "lint_vault.py"
    this_module = Path(__file__).resolve()

    # Wall A over the SCRIPT, which IS inside the routing wall's universe.
    offenders = filesystem_mutation_uses([script])
    assert not offenders, (
        "a filesystem-mutation capability is named outside vault_io. The fix is "
        "to route through the door — NEVER to add an exemption: "
        + ", ".join(f"{u.module}:{u.lineno} ({u.qualname})" for u in offenders))

    # …and over THIS module, which is not. A closed set, not a zero.
    named = {u.qualname for u in filesystem_mutation_uses([this_module])}
    assert named <= PERMITTED_PLANT_CAPABILITIES, (
        f"this module names a filesystem capability beyond its plant helpers: "
        f"{sorted(named - PERMITTED_PLANT_CAPABILITIES)}")

    # Wall B over both — M3's runtime door makes this module an `os.environ`
    # reader, so it is inside this predicate's reach and is RUN rather than
    # assumed clean.
    os_offenders = [u for u in os_module_attribute_uses([script, this_module])
                    if u.qualname.split(".", 1)[1] not in OS_READONLY_NAMES]
    assert not os_offenders, (
        "a non-read-only `os` member is reached outside the door: "
        + ", ".join(f"{u.module}:{u.lineno} ({u.qualname})" for u in os_offenders))

    # Wall C over the script under the STANDING set — the universe the routing
    # wall already grades that file under. Deliberately NOT the widened one:
    # this task must not silently re-scope a standing wall.
    from tests.test_name_gate_wall import WALL_C_MODULES
    assert not module_import_uses([script], WALL_C_MODULES)


def _check_the_process_boundary_is_refused_at_the_import():
    """M6. Every other clause of the containment wall reads this module's own
    syntax and grades the calls it makes IN THIS PROCESS. A drive that re-enters
    the tool as a CHILD process is graded by none of them — the callee is
    `subprocess.run`, the vault path is a STRING in an argv list, and omitting
    it altogether is enough, because `main`'s `--vault` defaults to the
    environment. So the route is refused at the IMPORT rather than at the call.
    """
    # The base set is IMPORTED, never hand-typed: a written-out copy stops
    # tracking `FS_MODULES` the day it gains a member.
    from tests.test_name_gate_wall import WALL_C_MODULES
    widened = WALL_C_MODULES | {"subprocess", "runpy"}
    this_module = Path(__file__).resolve()
    assert not module_import_uses([this_module], widened), (
        "this module imports a subprocess-capable module and can therefore "
        "re-enter the CLI as a child process, satisfying every in-process "
        "clause of the containment wall while mutating the live vault")

    # WI-235: the widened set's REACH, proved here rather than assumed from a
    # zero — `matches == 0` is satisfied identically by a set that reaches
    # `subprocess` and by one that reaches nothing.
    with _temp_root() as root:
        claimed = _plant_source(root, "imports_claimed", (
            "import subprocess\n"
            "import subprocess as sp\n"
            "from subprocess import run\n"
            "import runpy\n"
            "from runpy import run_path\n"))
        found = module_import_uses([claimed], widened)
        assert len(found) == 5, f"the widened set reached {len(found)} of 5 shapes"
        assert {u.qualname for u in found} == {"subprocess", "runpy"}, (
            "each import must be reported under the ORIGINAL module name, never "
            "the local alias")

        # The near-misses are deliberately this module's OWN legitimate imports,
        # so the wall cannot pass by matching every import and then be narrowed
        # back with nothing checking the narrowing. `import importlib.util` is a
        # DOTTED import whose root the predicate must split off correctly, and
        # `os` stays legal BY NAME (WALL_C_MODULES is FS_MODULES - {"os"})
        # because `_temp_vault` reads `os.environ` — so a builder who "tidies"
        # the widened set into FS_MODULES | {...} reddens the door itself.
        quiet = _plant_source(root, "imports_nearmiss", (
            "import importlib.util\n"
            "from contextlib import redirect_stdout\n"
            "import io\n"
            "import os\n"
            "from tests.support import temp_dir\n"
            '"""A docstring mentioning subprocess in running prose."""\n'))
        assert not module_import_uses([quiet], widened)


def _check_the_derived_walls_this_item_joins(touched):
    # The `ast` single-home equality, whose universe GROWS with every test file
    # this item adds.
    universe = python_files_under(PACKAGE_ROOT, TESTS_ROOT)
    homes = {u.module for u in modules_using_ast(universe)}
    assert homes == {"tests/derivations.py"}, (
        f"the `ast` capability must stay single-homed; found {sorted(homes)}")

    # The skip-reason equality over the WIDENED universe (this item's own edit).
    widened = python_files_under(PACKAGE_ROOT, TESTS_ROOT, SCRIPTS_ROOT)
    assert skip_reason_literal_sites(widened, SKIP_REASONS) == {
        "obsidian_schemas/repositories/base.py",
        "tests/test_fixture_vault.py",
    }

    # `apply_fixes` must still report EXACTLY ONE frontmatter write arm — pinned
    # twice elsewhere by equality, so the `write_frontmatter` call stays where it
    # is and no branch acquires its own.
    arms = [a for a in frontmatter_write_arms(
        python_files_under(PACKAGE_ROOT, SCRIPTS_ROOT))
        if a.module == "scripts/lint_vault.py"]
    assert arms == [ArmId("scripts/lint_vault.py", "apply_fixes", 1)], arms

    # Two single-home walls whose own universe is the ROUTING one
    # (`PACKAGE_ROOT, SCRIPTS_ROOT`) and does not reach `tests/`. Run over the
    # touched files that are INSIDE that universe, which for this item is the
    # script: the requirement is that this item adds no second implementation of
    # either job, and asserting a zero over `tests/` instead would invent a wall
    # nobody declared — `tests/test_name_gate_refusals.py:_d8_constructible` is a
    # standing, legitimate member of the address-splitting set.
    in_routing_universe = [p for p in touched
                           if p.is_relative_to(PACKAGE_ROOT)
                           or p.is_relative_to(SCRIPTS_ROOT)]
    assert in_routing_universe, "the routing-universe slice is empty"
    assert character_class_strip_sites(in_routing_universe) == []
    assert address_splitting_implementations(in_routing_universe) == set()

    # The three literal PATH shapes, re-run through the shipped wall's own line
    # reader over the two files this item AUTHORS — load-bearing rather than
    # redundant, because that wall's universe stops at
    # ("obsidian_schemas", "scripts") and does not reach `tests/`, so a
    # hard-coded `/Users/…` vault path in the new check module is reached by
    # nothing else.
    #
    # SCOPED TO THE AUTHORED FILES, and the reason is a property of the
    # predicate rather than a convenience: `_code_lines` is a TEXT scan, so a
    # line that FORBIDS one of these patterns necessarily contains it. The tree
    # already carries such a line — `tests/test_fixture_vault.py:1121`'s own
    # privacy assertion — which predates this item and is not a default resolved
    # anywhere. Widening this run to every touched file would go RED on it, and
    # the two available greens would each be worse than the scoping: an
    # exception list, or a narrowed oracle.
    from tests.test_vault_path_required import FORBIDDEN_DEFAULT_PATTERNS, _code_lines
    authored = [ROOT / "scripts" / "lint_vault.py", Path(__file__).resolve()]
    assert set(authored) <= set(touched)
    offenders = [f"{path.relative_to(ROOT)}:{lineno}"
                 for path in authored
                 for lineno, line in _code_lines(path)
                 for pattern in FORBIDDEN_DEFAULT_PATTERNS if pattern in line]
    assert offenders == [], (
        f"a caller-independent filesystem path is resolved as a default: "
        f"{offenders}")


def _check_every_criterion_resolves_to_exactly_one_module():
    """The conveyor's own discovery rule: a `kind: test` check is found by
    SOURCE-scanning the test roots for a unique top-level `def <check>(`."""
    from tests.test_ac_interpreter import WORK_ITEM_DOCS, check_module, criterion_checks

    assert WORK_ITEM in WORK_ITEM_DOCS, (
        "this item's criteria EXECUTE the library, so the document joins the "
        "foreign-interpreter wall that already exists rather than getting a "
        "second copy of its loop")
    checks = criterion_checks(WORK_ITEM)
    assert len(checks) == 5, f"expected five criteria, got {checks}"
    for check in checks:
        module = check_module(check)          # raises unless exactly one match
        assert module == Path(__file__).resolve(), (
            f"{check} resolves to {module.name}, not this module")
