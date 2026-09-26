"""WI-029, AC-3 — `lint_vault` REPORTS filename/name divergence and never
repairs it.

Two checks: the AC-3 battery, and the containment wall it inherits.

**THE CONTAINMENT DOOR, and why it is the first check in the file.** This module
drives `lint_vault`'s mutating entry points, and the path that must never reach
it is one attribute access away: `scripts/lint_vault.py:DEFAULT_VAULT` is an
environment read, and on the author's own machine that variable is populated. No
standing wall reaches this — `tests/test_vault_path_required.py`'s sweep stops at
`("obsidian_schemas", "scripts")`. So this module ships WI-026/WI-031's wall in
all five parts, and no proper subset of them is sufficient:

1. RUNTIME — `_temp_vault` is the module's ONLY constructor of a vault path and
   asserts containment before it returns.
2. SYNTAX (spelling + non-vacuity + provenance) — every mutating drive's vault
   argument is the identifier `vault`, there is at least one, and EVERY binding
   of that name in this module is a call to the one door.
3. IMPORT — this module names no subprocess-capable module, because a child
   process is unreadable to any in-process census and omitting the path
   altogether is enough to reach the live vault through `main`'s `--vault`
   default.
4. SOURCE — this module NAMES the live vault path nowhere outside `_temp_vault`'s
   own body, because `apply_fixes` never reads its `vault_path` (its write
   targets come from the issues).
5. LIBRARY (WI-031) — this module constructs NO `obsidian_schemas` repository,
   with any arguments, anywhere: the library's own `OBSIDIAN_VAULT_PATH` fallback
   runs inside every repository constructor, so a construction reaches the live
   vault without spelling any token at all.

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
from pathlib import Path  # noqa: E402

from tests.derivations import (  # noqa: E402
    LIVE_PATH_TOKENS,
    SCRIPTS_ROOT,
    auto_fixable_emitter_checks,
    module_import_uses,
    mutating_drive_vault_args,
)
from tests.fixture_vault import CORPUS_ROOT, NOTES, materialize_vault  # noqa: E402
from tests.support import temp_dir  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
LINT_VAULT_PATH = SCRIPTS_ROOT / "lint_vault.py"


def _load_lint_vault():
    """`scripts/` is not a package, so the CLI is loaded from its own path —
    through the SAME shape `tests/test_lint_vault_fix_rules.py:_load_lint_vault`
    already carries, never a second loader."""
    spec = importlib.util.spec_from_file_location(
        "wi029_lint_vault", LINT_VAULT_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


lint_vault = _load_lint_vault()

#: The stems a plant may NOT reuse. `materialize_vault`'s "leaves everything else
#: alone" protects files a plant does not NAME; it does not protect one a plant
#: overwrites, and `@Dave  Marrowyn Fennwick` is the specific trap — it is the
#: note that proves the RAW comparison.
CORPUS_STEMS = frozenset(p.stem for p in CORPUS_ROOT.iterdir() if p.is_file())

#: Every temp root this process took from `tests.support.temp_dir()`, by resolved
#: path. `_temp_vault` asserts membership rather than guessing at a path SHAPE.
_ISSUED_TEMP_ROOTS: set = set()

DIVERGENCE_CHECK = "stem_name_divergence"

#: The sub-directory plant's home. Asserted against the tool's OWN skip list
#: rather than assumed: a name inside `SKIP_DIRS` would make the plant silent for
#: a reason that has nothing to do with the arm.
NESTED_DIR = "People"


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

    The three negative assertions below are MANDATORY rather than defensive: they
    are what makes the SOURCE clause's non-empty arm true, and they are why that
    clause's exemption is scoped to this function's own body.
    """
    built = materialize_vault(Path(tmp) / "vault")
    resolved = Path(built).resolve()
    root = Path(tmp).resolve()

    assert resolved.relative_to(root) != Path("."), (
        f"the vault must be a strict descendant of {root}, not the root itself")
    assert root in _ISSUED_TEMP_ROOTS, (
        f"{root} is not a directory this process took from temp_dir()")

    # `.get(..., "")` and NEVER a subscript: the variable is UNSET in the graded
    # and CI environments, where `os.environ[...]` raises KeyError and reddens
    # the door itself rather than a drive. The env key is spelled HERE, as a bare
    # literal, and nowhere else in this module.
    for live in (lint_vault.DEFAULT_VAULT, os.environ.get("OBSIDIAN_VAULT_PATH", "")):
        if live:
            assert resolved != Path(live).resolve(), (
                "a drive was about to be pointed at the LIVE vault")
    return built


# ==========================================================================
# The containment wall, DEFINED FIRST so an ordinary floor run fires it ahead of
# the driving check. An ordering COURTESY and not a guarantee; the guarantee is
# the runtime door plus the clauses that close the routes around it.
# ==========================================================================

def test_every_divergence_drive_in_this_module_is_confined_to_a_temp_vault():
    """The five clauses of WI-026/WI-031's containment wall over this module's own
    source, plus an exercise of the runtime door itself."""
    scan = mutating_drive_vault_args([Path(__file__)])

    # (i) SPELLING.
    wrong = sorted(t for t in scan.drives if t[2] != "vault")
    assert not wrong, (
        f"a mutating drive takes a vault argument that is not `vault`: {wrong}")

    # (ii) NON-VACUITY.
    assert scan.drives, "this module drives nothing — the wall would be vacuous"

    # (iii) PROVENANCE — what makes the wall a claim about where the path CAME
    # FROM rather than how it is spelled.
    strays = sorted(b for b in scan.bindings if b[3] != "_temp_vault")
    assert not strays, (
        f"`vault` is bound by something other than the one door: {strays}")

    # (iv) SOURCE.
    outside = sorted(n for n in scan.live_path_names if n[3] != "_temp_vault")
    assert not outside, (
        f"this module names the live vault path outside `_temp_vault`'s own "
        f"body: {outside}")
    assert scan.live_path_names, (
        "the source census resolved nothing — the door's own three negative "
        "assertions must be visible to it")
    assert {n[2] for n in scan.live_path_names} == LIVE_PATH_TOKENS, (
        "the door must exercise all three token shapes, so the clause's green "
        "is a statement about a matcher that reaches every one of them")

    # (v) LIBRARY (WI-031).
    constructed = sorted(scan.repository_constructions)
    assert not constructed, (
        f"this module constructs an obsidian_schemas repository, which resolves "
        f"the live vault from the environment inside the library: {constructed}")

    # (3) IMPORT — refused at the import, because a child process is graded by
    # none of the in-process clauses above.
    from tests.test_name_gate_wall import WALL_C_MODULES
    widened = WALL_C_MODULES | {"subprocess", "runpy"}
    assert not module_import_uses([Path(__file__).resolve()], widened), (
        "this module imports a subprocess-capable module and can therefore "
        "re-enter the CLI as a child process")

    # (1) RUNTIME — the door EXERCISED, not left to whichever drive runs first.
    with _temp_root() as root:
        vault = _temp_vault(root)
        assert (Path(vault) / "@Isolde Varnholt.md").exists(), (
            "the door must return a materialized corpus, not merely a "
            "contained path")


# ==========================================================================
# AC-3
# ==========================================================================

def _stem_of(filename: str) -> str:
    stem = Path(filename).stem
    return stem[1:] if stem.startswith("@") else stem


def _expected_divergent() -> dict:
    """AC-3(a)'s expected set, DERIVED from the manifest by the same predicate
    AC-1 uses and never from `shape_classes` — the label is not the class, and
    the shipped detector runs over a live vault where nothing is labelled. A
    `NoteSpec` declaring no `fields` is SKIPPED rather than crashed on."""
    return {
        filename: spec.fields["name"] for filename, spec in NOTES.items()
        if spec.declared_type == "person" and spec.fields is not None
        and _stem_of(filename) != spec.fields.get("name")
    }


def _person_bytes(name_line: str, stem: str) -> str:
    """A plant's BYTES. `name_line` is written verbatim so a quoted scalar's
    whitespace and a non-string value both survive to the detector."""
    assert stem not in CORPUS_STEMS, (
        f"{stem!r} is a corpus stem — planting over it would destroy a frozen "
        f"member and the evidence it carries")
    return (f"---\ntype: person\n{name_line}\ntags: [person]\n---\n\n"
            "## To Discuss\n\n## Timeline\n\n## Notes\n")


#: Every plant, one per free variable the frozen corpus is UNANIMOUS about. The
#: LIST is the obligation and never its length: a corpus unanimous on a dimension
#: certifies any implementation narrower than the definition along it.
#: `(filename, name_line, fires)`.
PLANTS = (
    # (i) ROW 8's SHAPE — no `@` prefix, a book-titled stem, `type: person`.
    # Refuses a guard narrowed to `is_at_prefixed and entity_type == "person"`,
    # which every corpus arm tolerates and the live report does not.
    ("The Wandering Ledger - Quill Marrow.md", 'name: "Marrowyn Vale"', True),
    # (ii) CASE-ONLY — refuses a `.lower()`-ed comparison; live baseline row 3.
    ("@case only person.md", 'name: "Case Only Person"', True),
    # (iii) DOUBLE `@` — refuses `lstrip("@")` in place of a one-character strip,
    # since the library's canonical target for that note is `@<name>.md`.
    ("@@Doubled Stem.md", 'name: "Doubled Stem"', True),
    # (iv) SUB-DIRECTORY — `read_vault` rglobs and `vf.stem` is depth-free.
    (f"{NESTED_DIR}/@Nested Person.md", 'name: "Nested Different"', True),
    # (v) NEAR-MISS, a NON-STRING `name:` — the declared narrowing. Stops the
    # check being satisfied by "report everything that is not an exact match".
    ("@List Named.md", "name: [One, Two]", False),
    # (vi) SECOND NEAR-MISS, a BLANK `name:` — the arm's `stored.strip()`
    # conjunct. Without it every blank-name note gets a never-fixable ERROR on
    # top of the auto-fixable `person_missing_name` that repairs it away.
    ("@Blank Named.md", 'name: "   "', False),
    # (vii) UNNORMALIZED OPERANDS — a SUB-CELL of the `!=` itself. Refuses both
    # spellings of the normalizing slip (`stem != stored.strip()` and
    # `stem.strip() != stored`), each of which drops a note whose next `save`
    # would mint `@  <n>  .md` and fork it.
    ("@Whitespace Name.md", 'name: "  Whitespace Name  "', True),
    # THE SENTINEL-EXEMPT DISCRIMINATOR — a divergent phone-only stub declaring
    # `phones`. The DOOR writes it, so it is reported UNMARKED and stays
    # repairable by rename; a detector built on the bare validator marks it.
    ("@447700900123.md",
     'name: "+447700900123"\nphones: ["+447700900123"]', True),
)

#: The one plant whose stored value the message must carry with its whitespace
#: intact, so plant (vii) cannot be satisfied by an arm reporting the note for a
#: different reason.
WHITESPACE_PLANT = "@Whitespace Name.md"


def _plant_into(where) -> dict:
    """Write every plant as BYTES into a materialized copy — never through
    `repo.save` or `write_markdown_file` (this module constructs no repository at
    all, and half the corpus is gate-refused). Returns `{filename: fires}`."""
    assert NESTED_DIR not in lint_vault.SKIP_DIRS, (
        f"{NESTED_DIR!r} is in the tool's own skip list; the sub-directory "
        f"plant would be silent for a reason that is not the arm's")
    expected = {}
    for filename, name_line, fires in PLANTS:
        path = Path(where) / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(_person_bytes(name_line, Path(filename).stem),
                        encoding="utf-8")
        expected[filename] = fires
    return expected


def _divergence_issues(where) -> list:
    """This check's OWN issues over a materialization — never the whole report,
    which carries unrelated arms."""
    files = lint_vault.read_vault(Path(where))
    idx = lint_vault.build_indexes(files)
    return [issue for issue in lint_vault.check_structural(files, idx)
            if issue.check == DIVERGENCE_CHECK]


def _relative_names(where, issues) -> set:
    root = Path(where).resolve()
    return {Path(issue.file_path).resolve().relative_to(root).as_posix()
            for issue in issues}


def test_lint_vault_reports_stem_name_divergence_and_never_repairs_it():
    """AC-3. Zero-arg and raising, per the check contract."""
    expected = _expected_divergent()
    assert len(expected) == 4, (
        f"the definition selects four corpus members, derived and not listed: "
        f"{sorted(expected)}")

    with _temp_root() as root:
        # ---- (a) FIRES and (b) SILENT ELSEWHERE, over a PRISTINE copy ----
        vault = _temp_vault(root)
        issues = _divergence_issues(vault)
        assert _relative_names(vault, issues) == set(expected), (
            f"over the frozen corpus the check must fire on exactly the derived "
            f"four; got {sorted(_relative_names(vault, issues))}")

        for issue in issues:
            assert issue.severity is lint_vault.Severity.ERROR
            assert issue.category == "structural"
            # (d) NEVER REPAIRS, per issue.
            assert issue.auto_fixable is False, (
                f"{issue.file_path.name}: the divergence issue must never be "
                f"auto-fixable")
            stored = expected[Path(issue.file_path).name]
            assert _stem_of(issue.file_path.name) in issue.message
            assert stored in issue.message, (
                f"the message must name the stored name: {issue.message}")

        # (b)'s named members, asserted individually so the set equality above
        # cannot be read as covering them by accident.
        silent = _relative_names(vault, issues)
        for member in ("@Quillam Ostrivane Lumbrek.md",       # stem == name
                       "@Dave  Marrowyn Fennwick.md",         # the RAW pin
                       "@+447700900123.md",                   # pure digit
                       "@Oskaline Brenvik-Tarnquil.md",       # hyphenated
                       "@25 Corvallen Ravensby-3rd Pellworth-Wexlund 8.md"):
            assert member not in silent, f"{member} must be silent"
        for path in Path(vault).rglob("*.md"):
            if not path.stem.startswith("@"):
                assert path.name not in silent, (
                    f"{path.name}: no NON-person note may be reported, and every "
                    f"non-`@` corpus note declares a type other than person")

        # ---- (c) NOT-RENAMEABLE, reported and MARKED ----
        marked = {Path(issue.file_path).name for issue in issues
                  if lint_vault.NOT_RENAMEABLE_MARKER in issue.message}
        assert marked == {"@Perrowin Tessamund Drostane.md",
                          "@Yolvenna Brindlecote Skarnell.md"}, (
            f"the marker fires on the DOOR predicate and on nothing else: {marked}")
        patterns = {Path(issue.file_path).name:
                    "calendar_prefix" if "calendar_prefix" in issue.message
                    else "path_hostile_char" if "path_hostile_char" in issue.message
                    else None
                    for issue in issues}
        assert patterns["@Perrowin Tessamund Drostane.md"] == "calendar_prefix"
        assert patterns["@Yolvenna Brindlecote Skarnell.md"] == "path_hostile_char"
        assert patterns["@Quillam Ostrivane.md"] is None
        assert patterns["@Quillam Lumbrek.md"] is None

        # ---- (e) UNREADABLE NOTES — a placement property, not a second guard ----
        files = lint_vault.read_vault(Path(vault))
        idx = lint_vault.build_indexes(files)
        structural = lint_vault.check_structural(files, idx)
        triaged = {issue.file_path.name: issue.check for issue in structural}
        assert triaged.get("@Isolde Varnholt.md") == "unreadable_note", (
            "the undecodable note keeps its own ERROR")
        assert "@Isolde Varnholt.md" not in silent

        # ---- (d) NEVER REPAIRS — the accounting, and the emitter wall ----
        emitters = auto_fixable_emitter_checks([LINT_VAULT_PATH])
        assert DIVERGENCE_CHECK not in emitters, (
            "the new check must not join the auto-fixable emitter set, or "
            "WI-026's census-to-rule mapping and its committed baseline both "
            "go red")
        every = []
        for fn in (lint_vault.check_structural, lint_vault.check_completeness,
                   lint_vault.check_links, lint_vault.check_timeline,
                   lint_vault.check_noise):
            every.extend(fn(files, idx))
        fixable = [issue for issue in every if issue.auto_fixable]
        assert all(issue.check != DIVERGENCE_CHECK for issue in fixable)
        outcome = lint_vault.apply_fixes(every, vault, idx)
        accounted = (outcome.repaired + len(outcome.refused)
                     + len(outcome.errored) + len(outcome.declined))
        assert accounted == len(fixable), (
            f"WI-026's four-bucket partition must still total the auto-fixable "
            f"issue count with the new check enabled: {accounted} != "
            f"{len(fixable)}")
        for record in (*outcome.refused, *outcome.errored, *outcome.declined):
            assert getattr(record, "check", DIVERGENCE_CHECK) != DIVERGENCE_CHECK, (
                "a never-fixable issue reached the fix accounting")

        # …and the summary counts it among the ERRORS and not among the fixables.
        captured = io.StringIO()
        with contextlib.redirect_stdout(captured):
            lint_vault.print_summary(every, Path(vault), len(files), 0.0)
        printed = captured.getvalue()
        errors = sum(1 for issue in every
                     if issue.severity is lint_vault.Severity.ERROR)
        assert f"{errors} errors" in printed, printed[:400]
        assert DIVERGENCE_CHECK in printed

    # ---- the PLANTED materialization: the derived four PLUS exactly the
    # planted members declared to fire, and nothing else ----
    with _temp_root() as root:
        vault = _temp_vault(root)
        planted = _plant_into(vault)
        issues = _divergence_issues(vault)
        found = _relative_names(vault, issues)
        fires = {name for name, should in planted.items() if should}
        assert found == set(expected) | fires, (
            f"planted expectation missed: extra {sorted(found - set(expected) - fires)}, "
            f"absent {sorted((set(expected) | fires) - found)}")

        # The phone stub is reported UNMARKED — the arm that fails a detector
        # built on `NameValidator.validate_strict`.
        by_name = {Path(issue.file_path).name: issue for issue in issues}
        stub = by_name["@447700900123.md"]
        assert lint_vault.NOT_RENAMEABLE_MARKER not in stub.message, (
            "the DOOR writes a phone-only stub declaring `phones`, so its "
            "divergence is an ordinary one and its repair IS a rename")

        # Plant (vii)'s message carries the stored value with its whitespace
        # intact, so the plant cannot be satisfied by an arm that reports the
        # note for a different reason.
        whitespace = by_name[Path(WHITESPACE_PLANT).name]
        assert "'  Whitespace Name  '" in whitespace.message, whitespace.message
