"""WI-020 — AC-7: the derivations are single-sourced, proven by showing a copy
CANNOT EXIST rather than by comparing an object to itself.

This module deliberately does NOT name `ast`. It imports `modules_using_ast` and
asserts on its RESULT: a test that parsed files itself would be the second home
and would fail its own assertion.

Uniqueness is asserted at the CAPABILITY level, not by shape — and that is a
RULE, not a count (WI-021 rider (a): this said "three of the six derivations",
which went stale the moment a seventh sweep landed and was never the argument
anyway). SHAPE cannot discriminate a derivation from a copy of it: several
sweeps share one AST-walk shape, and the loose and data-flow predicates are
indistinguishable by any shape at all — they differ only semantically. What
every copy of a syntax-traversing derivation must DO is obtain syntax via the
ast module, so that is what is single-homed. Capability uniqueness implies
uniqueness of every predicate built on it, however many there are.

The `six` dict below is a REQUIRED SUBSET by its own comment, not a cardinality
bound on the module, so WI-021's four new sweeps deliberately do not join it and
`len(six) == 6` does not move.
"""

from tests.derivations import (
    PACKAGE_ROOT,
    TESTS_ROOT,
    base_repository_subclasses,
    functions_parsing_then_writing,
    functions_reserializing_parsed_frontmatter,
    load_file_implementations,
    module_id,
    modules_using_ast,
    python_files_under,
    seam_invocation_closure,
)
from tests.support import temp_dir

SHARED_SCAN_MODULE = "tests.derivations"
SHARED_MODULE_PATH = "tests/derivations.py"

# One plant per MARKER FORM the detector claims to match. Uniqueness is the one
# assertion in this AC set that an UNDER-GENERATING scan satisfies by finding
# nothing: a detector matching zero things still finds the single real site and
# still reports "exactly one". So the negative is PLANTED, not merely stated.
#
# These are string literals, which is why the marker must be read off parsed
# syntax: as syntax a literal is a Constant and is invisible to the scan. A text
# matcher would match THIS module and go red on a correct harness.
PLANT_IMPORT = """\
import ast


def sneaky_copy(path):
    return ast.parse(path.read_text())
"""

PLANT_FROM_IMPORT = """\
from ast import walk


def other_sneaky_copy(tree):
    return list(walk(tree))
"""


def test_derivations_are_single_sourced():
    """AC-7. Zero-arg: the battery calls it by name, and the planted negatives
    below need a scratch directory it therefore owns (tests/support.py).
    """
    with temp_dir() as tmp_path:
        _check_derivations_are_single_sourced(tmp_path)


def _check_derivations_are_single_sourced(tmp_path):
    # --- COMPLETENESS: six named exports, six DISTINCT function objects ------
    #
    # Completeness lives on NAMES because that is the one identity a scan can
    # decide. A seventh shared derivation extends this list; it is a required
    # subset, not a cardinality bound on the module.
    six = {
        "python_files_under": python_files_under,
        "functions_parsing_then_writing": functions_parsing_then_writing,
        "functions_reserializing_parsed_frontmatter":
            functions_reserializing_parsed_frontmatter,
        "base_repository_subclasses": base_repository_subclasses,
        "load_file_implementations": load_file_implementations,
        "seam_invocation_closure": seam_invocation_closure,
    }
    assert len(six) == 6
    assert len({id(f) for f in six.values()}) == 6, (
        "the six derivations must be six DISTINCT function objects — two names "
        "bound to one object is a derivation that was never written"
    )
    for name, func in six.items():
        assert func.__module__ == SHARED_SCAN_MODULE, (
            f"{name} is homed in {func.__module__}, not the shared scan module"
        )
        assert func.__name__ == name

    # --- SINGLE-HOMING over the derived file set, walked one directory wider --
    #
    # tests/ as well as obsidian_schemas/, because a private copy in a test
    # module nobody imports is precisely the target.
    live = modules_using_ast(python_files_under(PACKAGE_ROOT, TESTS_ROOT))
    homes = {use.module for use in live}
    assert homes == {SHARED_MODULE_PATH}, (
        "the ast capability must be single-homed to the shared scan module. "
        "A second module referencing it IS the copy. Found: "
        + ", ".join(
            f"{u.module}:{u.lineno} ({u.qualname})"
            for u in sorted(live, key=lambda u: (u.module, u.lineno))
            if u.module != SHARED_MODULE_PATH
        )
    )
    assert live, "the scan found NOTHING — an under-generating detector reports "\
                 "'exactly one' just as happily as a compliant one"

    # --- THE PLANTED NEGATIVES: reached, matched, and NAMED ------------------
    #
    # Written AFTER the live assertion above, and that order is load-bearing
    # rather than incidental: `temp_dir()` honours TMPDIR, which under the check
    # battery points INSIDE the repo (a build worktree's own `tmp/`). Plants can
    # therefore land within the tree — harmless here because the live scan is
    # rooted at the package and `tests/` and has already run, and because the
    # directory is removed on exit.
    plant_dir = tmp_path / "planted"
    plant_dir.mkdir()
    (plant_dir / "copy_via_import.py").write_text(PLANT_IMPORT, encoding="utf-8")
    (plant_dir / "copy_via_from_import.py").write_text(PLANT_FROM_IMPORT,
                                                       encoding="utf-8")

    planted = modules_using_ast(python_files_under(plant_dir))
    by_module = {}
    for use in planted:
        by_module.setdefault(use.module, []).append(use)

    # Identity is ASKED FOR, not re-spelled. `module_id` is the scan's own rule
    # and it is branchy (repo-relative inside the tree, absolute outside), so a
    # hardcoded `str(path)` here would agree with it only for as long as TMPDIR
    # happened to sit outside the repo — a second home for the rule, which is
    # the very thing this criterion forbids.
    import_module_id = module_id(plant_dir / "copy_via_import.py")
    from_module_id = module_id(plant_dir / "copy_via_from_import.py")

    # The scan is parameterized on its roots precisely so the plants are scanned
    # by the SAME code the live assertion above uses. One walk, both uses.
    assert set(by_module) == {import_module_id, from_module_id}, (
        f"the scan did not reach both plants: {sorted(by_module)}"
    )

    import_uses = by_module[import_module_id]
    assert {u.qualname for u in import_uses} == {"ast", "ast.parse"}, (
        "form 1 (`import ast` plus an attribute use) must be matched and named"
    )
    assert {u.lineno for u in import_uses} == {1, 5}

    from_uses = by_module[from_module_id]
    assert {u.qualname for u in from_uses} == {"walk"}, (
        "form 2 (`from ast import walk`) must be matched and named"
    )
    assert {u.lineno for u in from_uses} == {1}
