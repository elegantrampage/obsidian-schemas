"""WI-021 — the derived wall: every frontmatter write ARM routes through the one
semantic gate, and the sweep's REACH is proven rather than assumed.

**Why a count oracle is not enough (WI-235).** Three of this item's oracles are
counts of structural matches — the arm sweep, the declaration pin and the
placement pin — and `matches == 8` says NOTHING about the matcher's reach: a
predicate resolving every claimed shape and one resolving almost none are
equally green. So every claimed match-shape is driven through the wall's OWN
predicate, never a re-implementation, as a planted GREEN fixture on every floor
run; the near-misses are what stop a wall passing by matching everything.

The specific trap here is the IMPORT ALIAS. `lint_vault.py` imports the
serializer as `write_frontmatter as _wfm` and calls `_wfm(fm)`, so a matcher
keyed on the literal name resolves seven arms and silently drops the eighth —
the one arm that lives outside the package, and the WI-232 shape exactly.

**Two live-corpus assertions, deliberately different in kind.** Corpus-wide the
floor is a FLOOR — at least the eight named `(qualname, arm)` pairs — because
the corpus is live and a ninth arm in a SEVENTH function must join every
criterion automatically with no wall edit. Within the six functions this item
EDITS the member count is pinned by EQUALITY, because there a new member is this
item's own routing edit minting one: `fm = gate_write(fm, …)` is a new binding
of the serialized name and therefore a NINTH arm of `write_markdown_file` on the
post-build tree, which is green under the floor alone and then makes AC-3's
`{D1a, D1b, D1c}` exclusion unsatisfiable. Its cost is stated so it is not
discovered: a sibling item later adding a legitimate gated fourth branch to one
of these six functions is RED here and must move that function's number.

Nothing here reads syntax (no `ast`): that capability is single-homed in
`tests/derivations.py`, asserted by set EQUALITY, so this module drives the
predicates and never re-implements one.
"""

# FIRST, ahead of every package import: the conveyor may run this module's check
# under an interpreter that is not this project's, where the imports below cannot
# resolve. A no-op under the floor command and under CI (WI-021; see
# `tests/ac_interpreter.py` for the failure this closes).
from tests.ac_interpreter import ensure_project_interpreter

ensure_project_interpreter(__file__)

import os  # noqa: E402 — everything below runs only once the interpreter is right
from pathlib import Path

import yaml

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
from tests.derivations import (
    COMMIT_FUNCTION_NAMES,
    FS_MODULES,
    OS_READONLY_NAMES,
    PACKAGE_ROOT,
    SCRIPTS_ROOT,
    TESTS_ROOT,
    ArmId,
    address_splitting_implementations,
    falsy_returns_in,
    filesystem_mutation_uses,
    frontmatter_write_arms,
    functions_calling,
    gate_call_declarations,
    gate_call_placement,
    module_id,
    module_import_uses,
    modules_using_ast,
    non_completed_write_sites,
    os_module_attribute_uses,
    python_files_under,
)
from tests.support import temp_dir

SHARED_SCAN_MODULE = "tests.derivations"

WRITER = "obsidian_schemas/writer.py"
BASE = "obsidian_schemas/repositories/base.py"
LINT = "scripts/lint_vault.py"

# AC-1(a)'s floor: eight arms across six functions, named by (qualname, arm).
# Never a line number — this item shifts every line number in five of the six.
D1A = ArmId(WRITER, "write_markdown_file", 1)
D1B = ArmId(WRITER, "write_markdown_file", 2)
D1C = ArmId(WRITER, "write_markdown_file", 3)
D4 = ArmId(BASE, "BaseRepository.update_fields", 1)
D5 = ArmId(WRITER, "update_frontmatter_field", 1)
D6 = ArmId(WRITER, "update_frontmatter_fields", 1)
D7 = ArmId(WRITER, "roundtrip_file", 1)
D8 = ArmId(LINT, "apply_fixes", 1)

FLOOR = (D1A, D1B, D1C, D4, D5, D6, D7, D8)

# (ii) — the six functions this item EDITS, pinned by EQUALITY on the tree the
# wall actually runs against.
EDITED_FUNCTION_ARM_COUNTS = {
    (WRITER, "write_markdown_file"): 3,
    (BASE, "BaseRepository.update_fields"): 1,
    (WRITER, "update_frontmatter_field"): 1,
    (WRITER, "update_frontmatter_fields"): 1,
    (WRITER, "roundtrip_file"): 1,
    (LINT, "apply_fixes"): 1,
}

# The placement values the ONE local rule resolves on the post-build tree.
PLACEMENT_ABOVE = {D1A, D1B, D1C, D7}
PLACEMENT_IN_LOCK = {D4, D5, D6, D8}


def _single_sourced(*derivations):
    """Every predicate is imported FROM the shared scan module.

    Two independently-written predicates that agree on today's tree diverge on
    the first future write path, and that divergence IS what the wall exists to
    catch — solve-in-one-place applies to the harness as much as to the package.
    """
    for derivation in derivations:
        assert derivation.__module__ == SHARED_SCAN_MODULE, (
            f"{derivation.__name__} is homed in {derivation.__module__}, not the "
            "shared scan module — a second copy IS the divergence"
        )


def _live_files():
    return python_files_under(PACKAGE_ROOT, SCRIPTS_ROOT)


# ---------------------------------------------------------------------------
# The planted corpus. String literals, because the predicates read PARSED
# SYNTAX: as syntax a literal is a Constant and is invisible to them, so the
# planter cannot match itself.
# ---------------------------------------------------------------------------

PLANT_CALLEE_FORMS = '''\
from obsidian_schemas.writer import write_frontmatter as _wfm


def bare_name_call(extra):
    fm = dict(extra)
    write_frontmatter(fm)


def attribute_call(extra):
    fm = dict(extra)
    writer.write_frontmatter(fm)


def alias_import_call(content):
    fm, body = parse_frontmatter(content)
    _wfm(fm)


def multi_branch(entity, frontmatter, extra_fields):
    if entity is not None:
        fm = model_to_frontmatter(entity, extra_fields)
    elif frontmatter is not None:
        fm = frontmatter.copy()
    else:
        fm = dict(extra_fields or {})
    write_frontmatter(fm)


def mutations_are_not_arms(content, extra):
    fm, body = parse_frontmatter(content)
    fm.update(extra)
    fm["auto_created"] = True
    write_frontmatter(fm)


def reads_and_returns_instead_of_serializing(content):
    fm, body = parse_frontmatter(content)
    fm["seen"] = True
    return fm
'''

PLANT_DECLARATION_SHAPES = '''\
def declares_by_attribute(self, updates):
    fm = dict(updates)
    fm.update(gate_write(fm, declared_type=self.type_name, whole_record=False))
    write_frontmatter(fm)


def declares_by_type_get(content):
    fm, body = parse_frontmatter(content)
    fm.update(gate_write(fm, declared_type=fm.get("type"), whole_record=False))
    write_frontmatter(fm)


def declares_by_literal_none(content):
    fm, body = parse_frontmatter(content)
    gate_write({}, declared_type=None, whole_record=False)
    write_frontmatter(fm)


def hardcodes_a_literal_type(content):
    fm, body = parse_frontmatter(content)
    fm.update(gate_write(fm, declared_type="person", whole_record=False))
    write_frontmatter(fm)


def omits_the_keyword(content):
    fm, body = parse_frontmatter(content)
    fm.update(gate_write(fm, whole_record=False))
    write_frontmatter(fm)


def passes_an_unclassifiable_expression(content):
    fm, body = parse_frontmatter(content)
    fm.update(gate_write(fm, declared_type=_resolve(fm), whole_record=False))
    write_frontmatter(fm)
'''

PLANT_PLACEMENT_SHAPES = '''\
def guard_raises_above_the_anchor(fpath):
    if not fpath.exists():
        raise FileNotFoundError(fpath)
    with vault_io.note_lock(fpath):
        fm, body = parse_frontmatter(read(fpath))
        fm.update(gate_write(fm, declared_type=fm.get("type"), whole_record=False))
        write_frontmatter(fm)


def guard_only_logs(fpath):
    if not fpath.exists():
        report("missing")
    with vault_io.note_lock(fpath):
        fm, body = parse_frontmatter(read(fpath))
        fm.update(gate_write(fm, declared_type=fm.get("type"), whole_record=False))
        write_frontmatter(fm)


def no_guard_at_all(fpath, extra):
    fm = dict(extra)
    fm.update(gate_write(fm, declared_type=fm.get("type"), whole_record=False))
    with vault_io.note_lock(fpath):
        write_frontmatter(fm)


def gate_nested_in_an_arm_binding_branch(entity, extra_fields):
    if entity is not None:
        fm = model_to_frontmatter(entity, extra_fields)
        fm.update(gate_write(fm, declared_type=fm.get("type"), whole_record=True))
    else:
        fm = dict(extra_fields or {})
    with vault_io.note_lock(entity):
        write_frontmatter(fm)


def two_gate_calls(content):
    fm, body = parse_frontmatter(content)
    fm.update(gate_write(fm, declared_type=fm.get("type"), whole_record=False))
    fm.update(gate_write(fm, declared_type=fm.get("type"), whole_record=False))
    write_frontmatter(fm)
'''

PLANT_SPLITTER_SHAPES = '''\
import re
from email.utils import parseaddr


def splits_with_parseaddr(entry):
    display, address = parseaddr(entry)
    return address, display


def splits_with_a_hand_rolled_regex(entry):
    m = re.match(r"^(.*?)\\s*\\(\\s*([^@\\s]+@[^\\s)]+)\\s*\\)\\s*$", entry)
    if m:
        return m.group(2), m.group(1)
    return "", ""


def splits_on_a_bare_literal(raw):
    head, _, tail = raw.partition("<")
    return tail.rstrip(">"), head.strip()


def returns_a_triple_not_a_pair(entry):
    display, address = parseaddr(entry)
    return address, display, entry


def returns_a_pair_with_no_address_work(content):
    head, _, tail = content.partition("---")
    return head, tail
'''


def _plant(directory: Path, name: str, source: str) -> Path:
    path = directory / name
    path.write_text(source, encoding="utf-8")
    return path


def _arms_by_function(arms):
    counts = {}
    for arm in arms:
        counts[(arm.module, arm.qualname)] = counts.get(
            (arm.module, arm.qualname), 0) + 1
    return counts


# ---------------------------------------------------------------------------
# Task 6 — the predicates and their planted batteries
# ---------------------------------------------------------------------------

def test_the_arm_sweep_resolves_the_floor_and_its_match_shapes():
    """Task 6's verify. Zero-arg and raising, per the check contract."""
    _single_sourced(frontmatter_write_arms, gate_call_declarations,
                    gate_call_placement, address_splitting_implementations,
                    python_files_under)

    # THE LIVE ASSERTIONS FIRST, and that order is load-bearing rather than
    # incidental: `temp_dir()` honours TMPDIR, which can point INSIDE the repo
    # (a build worktree's own tmp/), so the plants must not be reachable by a
    # scan that has not already run.
    _check_the_live_floor_and_the_edited_function_equalities()

    with temp_dir() as scratch:
        _check_the_callee_and_binding_shapes(scratch)
        _check_all_five_declaration_cells(scratch)
        _check_the_placement_rule_and_its_near_misses(scratch)
        _check_the_splitter_job_shape(scratch)


def _check_the_live_floor_and_the_edited_function_equalities():
    arms = frontmatter_write_arms(_live_files())

    # (i) CORPUS-WIDE: a FLOOR, never an equality. A ninth arm in a SEVENTH
    # function is a member this item WANTS joining every criterion automatically.
    missing = [arm for arm in FLOOR if arm not in arms]
    assert not missing, (
        "the derived set must contain at least the eight arms across six "
        f"functions AC-1(a) names. Missing: {missing}"
    )
    assert len(arms) >= len(FLOOR)
    assert len(set(arms)) == len(arms), "an arm must appear exactly once"

    # (ii) WITHIN THE SIX FUNCTIONS THIS ITEM EDITS: EQUALITY. This is what
    # makes `fm = gate_write(fm, …)` in Tasks 7-10 RED — under (i) alone it is
    # green, and AC-3's exclusion set, asserted by equality as exactly
    # {D1a, D1b, D1c}, then cannot reconcile.
    counts = _arms_by_function(arms)
    for key, expected in EDITED_FUNCTION_ARM_COUNTS.items():
        assert counts.get(key, 0) == expected, (
            f"{key[1]} must contribute EXACTLY {expected} arm(s), found "
            f"{counts.get(key, 0)}. The gate's result is MERGED into the object "
            "the arm serializes and is NEVER re-bound to the name that function "
            "passes to write_frontmatter — a re-binding mints a spurious arm."
        )

    # The two save methods and their two structurally identical siblings yield
    # ZERO from the SAME predicate, applied uniformly — they bind no frontmatter
    # dict and serialize nothing. Hand-listing them out is the vacuity hole the
    # arm derivation exists to close.
    for module, qualname in (
        (BASE, "BaseRepository.save"),
        ("obsidian_schemas/repositories/person.py", "PersonRepository.save"),
        ("obsidian_schemas/repositories/book.py", "BookRepository.save"),
        ("obsidian_schemas/repositories/meeting.py", "MeetingRepository.save"),
    ):
        assert counts.get((module, qualname), 0) == 0, (
            f"{qualname} is NOT an arm — it binds no frontmatter dict"
        )


def _check_the_callee_and_binding_shapes(scratch: Path):
    """Every claimed match-shape, driven through the wall's OWN predicate."""
    path = _plant(scratch, "callee_forms.py", PLANT_CALLEE_FORMS)
    module = module_id(path)
    arms = frontmatter_write_arms([path])
    counts = _arms_by_function(arms)

    # The three CALLEE forms. The alias arm is not optional: it is the only way
    # D8 is reachable at all.
    assert counts.get((module, "bare_name_call")) == 1
    assert counts.get((module, "attribute_call")) == 1
    assert counts.get((module, "alias_import_call")) == 1, (
        "a matcher keyed on the literal name `write_frontmatter` drops the "
        "aliased call — the one arm that lives outside the package"
    )

    # The two BINDING forms: a single `Name` assign and a tuple unpack. Four of
    # the six live functions bind by unpacking, so a single-Name rule resolves
    # three arms of the eight.
    assert counts.get((module, "mutations_are_not_arms")) == 1, (
        "a Subscript target and a method call mutate a dict already bound; "
        "neither BINDS it, so neither is an arm"
    )

    # A multi-branch function resolves as SEPARATE members.
    assert counts.get((module, "multi_branch")) == 3, (
        "three branches that converge on one write_frontmatter call are three "
        "arms — this is the branch-shaped bypass arm granularity closes"
    )
    assert {arm.arm for arm in arms
            if arm.qualname == "multi_branch"} == {1, 2, 3}

    # THE NEAR-MISS: reads and mutates a frontmatter dict, hands it back to its
    # caller instead of serializing it. Not matched — which is what stops the
    # wall passing by matching everything.
    assert counts.get((module, "reads_and_returns_instead_of_serializing"), 0) == 0


def _check_all_five_declaration_cells(scratch: Path):
    """§7 claims the classification is TOTAL. A battery driving only the four
    cells the intended build writes says nothing about the cell the predicate
    must RED on, so all five are driven on their own planted arms."""
    path = _plant(scratch, "declaration_shapes.py", PLANT_DECLARATION_SHAPES)
    module = module_id(path)
    classified = gate_call_declarations([path])

    def cell(qualname):
        return classified[ArmId(module, qualname, 1)]

    assert cell("declares_by_attribute") == "attribute"
    assert cell("declares_by_type_get") == "type_get_call"
    assert cell("declares_by_literal_none") == "constant"
    assert cell("hardcodes_a_literal_type") == "constant"
    assert cell("omits_the_keyword") == "absent"
    assert cell("passes_an_unclassifiable_expression") == "other", (
        "a Call on neither `.get` nor an Attribute must classify as `other` "
        "and be RED wherever it appears — a predicate that silently returned "
        "'unclassified' would green the pin by producing nothing"
    )

    # BOTH equality legs, exercised in both directions on the planted corpus:
    # the sets resolve to exactly the arms that write a literal / omit the
    # keyword, so removing either planted arm would turn its set empty.
    constants = {arm.qualname for arm, label in classified.items()
                 if label == "constant"}
    assert constants == {"declares_by_literal_none", "hardcodes_a_literal_type"}
    absent = {arm.qualname for arm, label in classified.items()
              if label == "absent"}
    assert absent == {"omits_the_keyword"}

    # A function with no gate call contributes no key at all, so a skipped arm
    # is a set DIFFERENCE rather than a silent pass.
    unrouted = _plant(scratch, "unrouted.py", PLANT_CALLEE_FORMS)
    assert gate_call_declarations([unrouted]) == {}


def _check_the_placement_rule_and_its_near_misses(scratch: Path):
    path = _plant(scratch, "placement_shapes.py", PLANT_PLACEMENT_SHAPES)
    module = module_id(path)
    placements = gate_call_placement([path])

    def site(qualname, arm=1):
        return placements[ArmId(module, qualname, arm)]

    # REQUIRED is DERIVED by one local syntactic rule: `in-lock` iff the frame
    # refuses on the target's non-existence above the anchor.
    assert site("guard_raises_above_the_anchor").required == "in-lock"
    assert site("guard_raises_above_the_anchor").observed == "in-lock"

    # NEAR-MISS: an `if not p.exists():` whose body LOGS instead of raising is
    # NOT a guard, so the frame falls to the `above` DEFAULT — and its in-lock
    # call is then the contradiction the wall REPORTS.
    logging_guard = site("guard_only_logs")
    assert logging_guard.required == "above", (
        "a guard that does not raise is not a guard; reading it as one would "
        "let a frame claim in-lock without refusing on a vanished target"
    )
    assert logging_guard.observed == "in-lock"

    # `above` is the DEFAULT for an arm the predicate does not recognise, so a
    # ninth arm is RED by omission rather than silently permitted.
    assert site("no_guard_at_all").required == "above"
    assert site("no_guard_at_all").observed == "above"

    # THE ASSOCIATION, which both per-arm predicates depend on.
    nested = site("gate_nested_in_an_arm_binding_branch")
    assert nested.nested_in_arm_branch is True, (
        "a gate call inside `if entity is not None:` is the exact bypass arm "
        "granularity was invented to close"
    )
    assert site("no_guard_at_all").nested_in_arm_branch is False
    assert site("two_gate_calls").calls_in_function == 2
    assert gate_call_declarations([path])[
        ArmId(module, "two_gate_calls", 1)] == "other", (
        "a function with two gate calls is RED rather than having one arm's "
        "call attributed to its siblings"
    )

    # The RED consistency leg: the arguments of a frame's gate call bound below
    # the anchor. D5/D6/D8 parse their declaration there, which is why an arm
    # the one rule requires `above` while its arguments bind in-lock is a
    # CONTRADICTION the wall reports rather than a second route to `in-lock`.
    assert logging_guard.arguments_bound_in_lock is True
    assert site("no_guard_at_all").arguments_bound_in_lock is False


def _check_the_splitter_job_shape(scratch: Path):
    """AC-5's sweep is keyed on the JOB, never on the `parseaddr` symbol."""
    path = _plant(scratch, "splitter_shapes.py", PLANT_SPLITTER_SHAPES)
    module = module_id(path)
    found = {fid.qualname for fid in address_splitting_implementations([path])
             if fid.module == module}
    assert found == {
        "splits_with_parseaddr",
        "splits_with_a_hand_rolled_regex",
        "splits_on_a_bare_literal",
    }, (
        "each implementation SHAPE must match, and the two near-misses must "
        f"not: a triple is not a pair, and a pair with no address work is not "
        f"this job. Found: {sorted(found)}"
    )


# ---------------------------------------------------------------------------
# Task 7 — D1a / D1b / D1c, routed with the hoist
# ---------------------------------------------------------------------------

DIRTY = "Dave/Bob"        # the path-hostile form, and the executed incident


def test_write_markdown_file_gates_all_three_arms_above_the_lock():
    """Task 7's verify. Zero-arg and raising, per the check contract."""
    assert_default_lock_home()
    with temp_dir() as vault:
        _check_the_repository_path_leaves_no_mangled_parent(vault / "repo")
    with temp_dir() as vault:
        _check_each_direct_arm_refuses_before_touching_disk(vault)


def _check_the_repository_path_leaves_no_mangled_parent(vault: Path):
    """The 2026-08-11 incident, replayed. `repo.save(Person(name="Dave/Bob"))`
    used to succeed and leave FOUR artefacts on disk: `<vault>/@Dave/`, its lock
    home, a `.lock` and `<vault>/@Dave/Bob.md`."""
    vault.mkdir(parents=True)
    repo = PersonRepository(vault)
    try:
        repo.save(Person(name=DIRTY))
    except NameGateRefusal as exc:
        assert exc.pattern == "path_hostile_char"
    else:
        raise AssertionError("a path-hostile name must be refused at save()")

    # The oracle NAMES artifacts computed from values the test holds — never
    # "the vault root's only child is X" and never an ambient recursive-listing
    # snapshot, both of which are RED against a correct build at the arms where
    # `note_lock` legitimately leaves debris.
    assert not (vault / "@Dave").exists(), (
        "the refusal must land BEFORE note_lock's sentinel mkdir — which "
        "subsumes the lock home and any note inside it"
    )
    assert not (vault / "@Dave.md").exists()

    # And a clean name through the same door still commits, so the refusal above
    # is the gate rather than anything else in the frame.
    repo.save(Person(name="Dave Smith"))
    assert (vault / "@Dave Smith.md").exists()


def _check_each_direct_arm_refuses_before_touching_disk(vault: Path):
    """Each of the three arms in its own right. A `type: person` value arriving
    through the `frontmatter=` arm never stands in for the `entity=` one: they
    are three doors into one function and arm granularity is what makes each get
    issued."""
    arms = (
        ("D1a entity=", dict(entity=Person(name=DIRTY))),
        ("D1b frontmatter=", dict(frontmatter={"type": "person", "name": DIRTY})),
        ("D1c extra_fields=", dict(extra_fields={"type": "person", "name": DIRTY})),
    )
    for label, kwargs in arms:
        target = vault / f"@{label.split()[0]}" / "Bob.md"
        assert not target.parent.exists(), "the test did not create this parent"
        try:
            write_markdown_file(target, **kwargs)
        except NameGateRefusal as exc:
            assert exc.pattern == "path_hostile_char", label
        else:
            raise AssertionError(f"{label} must refuse a path-hostile name")

        assert not target.exists(), label
        assert not target.parent.exists(), (
            f"{label}: the gate refused AFTER note_lock had already mkdir'd the "
            "sentinel home at the note's own parent"
        )
        assert not (target.parent / ".obsidian-schemas-locks").exists(), label

    # Each arm still commits a clean write — otherwise the three refusals above
    # would be satisfied by a function that refuses everything.
    for index, (label, kwargs) in enumerate(arms):
        clean = vault / f"@clean-{index}.md"
        if "entity" in kwargs:
            kwargs = dict(entity=Person(name="Dave Smith"))
        elif "frontmatter" in kwargs:
            kwargs = dict(frontmatter={"type": "person", "name": "Dave Smith"})
        else:
            kwargs = dict(extra_fields={"type": "person", "name": "Dave Smith"})
        write_markdown_file(clean, **kwargs)
        assert clean.exists(), label


# ---------------------------------------------------------------------------
# Task 8 — D4 in-lock, and the D3 rider's write-back
# ---------------------------------------------------------------------------

STORED_DIRTY = "Me to David Field"      # Tier-1 dirty, and dirty BEFORE this item


def plant_note(vault: Path, stem: str, **fields) -> Path:
    """A note planted with `Path.write_text`, never through a door.

    SYNTHETIC on purpose: the only live Tier-1-dirty names are two WI-083
    sentinel stubs the payload rule permits anyway, and the archived ones sit
    under directories `SKIP_DIRS` bars from `lint_vault --fix` and the root-only
    glob bars from `update_fields` — so no door in this package can be exercised
    against them.

    The frontmatter is SERIALIZED from the values rather than hand-spelled, so
    what a caller passes is what parses back. Hand-spelling silently changed the
    TYPE of anything YAML reads as a scalar — a planted `phones: ["447700900123"]`
    landed as a list of INTS, which then takes the gate's list-shape
    pass-through arm and makes a fixture claim something it never exercised.
    """
    path = vault / f"{stem}.md"
    frontmatter = yaml.dump(fields, default_flow_style=False, sort_keys=False,
                            allow_unicode=True)
    path.write_text(f"---\n{frontmatter}---\n\n## Timeline\n\n- planted\n",
                    encoding="utf-8")
    return path


def test_repository_writes_gate_in_lock_and_the_rider_writes_back():
    """Task 8's verify. Zero-arg and raising, per the check contract."""
    with temp_dir() as root:
        _check_d4_gates_the_delta_not_the_record(root / "d4")
    with temp_dir() as root:
        _check_the_rider_writes_identifiers_back_and_never_the_name(root / "rider")
    with temp_dir() as root:
        _check_the_filename_stem_and_the_stored_name_agree(root / "identity")


def _check_d4_gates_the_delta_not_the_record(vault: Path):
    vault.mkdir(parents=True)
    plant_note(vault, f"@{STORED_DIRTY}", type="person", name=STORED_DIRTY)
    repo = PersonRepository(vault)
    person = repo.get(STORED_DIRTY)
    assert person is not None, "the stored-dirty note must still LOAD"

    # The delta rule: an unrelated field still commits against a note whose
    # STORED name has been Tier-1 dirty since before this item. A build gating
    # the merged record would refuse this — remedy-is-the-disease.
    repo.update_fields(person, {"company": "Acme"})
    assert "company: Acme" in (vault / f"@{STORED_DIRTY}.md").read_text()

    # …while a write that INTRODUCES that same name is refused.
    try:
        repo.update_fields(repo.get(STORED_DIRTY), {"name": STORED_DIRTY})
    except NameGateRefusal as exc:
        assert exc.pattern == "calendar_prefix"
    else:
        raise AssertionError("introducing a Tier-1 name through D4 must refuse")

    # The refusal left the note byte-identical.
    assert "company: Acme" in (vault / f"@{STORED_DIRTY}.md").read_text()


def _check_the_rider_writes_identifiers_back_and_never_the_name(vault: Path):
    vault.mkdir(parents=True)
    repo = PersonRepository(vault)
    person = Person(
        name="Dave Smith",
        emails=["Al B <A@B.com>"],
        phones=["447700900123", "+44 7700 900123"],
        aliases=["x@y.com"],
    )
    repo.save(person)

    # The caller's OWN object carries the normalized values — the in-place model
    # mutation `_normalize_address_fields` used to perform, preserved.
    assert person.emails == ["a@b.com", "x@y.com"], (
        "the entity arm holds the whole record, so an address in aliases[] "
        "migrates to emails[]"
    )
    assert person.aliases == ["Al B"], (
        "and the display half of an emails[] entry migrates to aliases[]"
    )
    assert person.phones == ["+44 7700 900123"], (
        "phones[] is a NEW in-place mutation, and the E.164 spelling wins"
    )
    assert person.name == "Dave Smith", "the rider writes back NO name"

    # Idempotence, exercised for real rather than asserted: one save invokes the
    # gate twice — the rider, then the entity arm on the projection the rider
    # just produced.
    before = (vault / "@Dave Smith.md").read_text()
    repo.save(person)
    assert (vault / "@Dave Smith.md").read_text() == before
    assert person.emails == ["a@b.com", "x@y.com"]
    assert person.aliases == ["Al B"]
    assert person.phones == ["+44 7700 900123"]


def _check_the_filename_stem_and_the_stored_name_agree(vault: Path):
    """The name-identity control at the arm where it can actually diverge.

    The FILENAME is bound from the raw `entity.name` one frame ABOVE every gate
    call and never revisited, so a gate that repaired the name would write
    `name: Dave Smith` into `@Dave  Smith.md` and the next save() would mint a
    second note for one person.
    """
    vault.mkdir(parents=True)
    repo = PersonRepository(vault)
    tier2_dirty = "Dave  Smith"          # double space — Tier 2, never Tier 1
    path = repo.save(Person(name=tier2_dirty))

    assert path.name == f"@{tier2_dirty}.md"
    assert path.stem.lstrip("@") == tier2_dirty
    reloaded = repo._load_file(path)
    assert reloaded is not None and reloaded.name == tier2_dirty, (
        "RED for a build that reaches for NameValidator.clean or for "
        "validate_strict's RETURN value"
    )
    assert len(list(vault.glob("@*.md"))) == 1, "one person, one note"


# ---------------------------------------------------------------------------
# Task 9 — D5, D6 and D7
# ---------------------------------------------------------------------------

def test_the_public_writer_doors_gate_the_delta_not_the_record():
    """Task 9's verify. Zero-arg and raising, per the check contract."""
    with temp_dir() as root:
        _check_a_stored_dirty_note_stays_writable(root / "delta")
    with temp_dir() as root:
        _check_roundtrip_commits_a_stored_dirty_note(root / "roundtrip")
    with temp_dir() as root:
        _check_the_scalar_container_still_commits(root / "shape")


def _check_a_stored_dirty_note_stays_writable(vault: Path):
    vault.mkdir(parents=True)
    note = plant_note(vault, f"@{STORED_DIRTY}", type="person", name=STORED_DIRTY)

    # THE TEST THAT GOES RED FOR A BUILD GATING THE MERGED RECORD. At D5 the
    # stored record sits bound one line above the natural call site, so gating
    # it is the one-word mistake — and it greens the whole per-arm triple, greens
    # the refusal battery (a refusal oracle cannot tell refused-because-
    # introduced from refused-because-stored) and greens the identifier battery,
    # while making this door permanently refuse every legacy-dirty note.
    assert update_frontmatter_field(note, "company", "Acme") is True
    assert update_frontmatter_fields(note, {"role": "vip"}) is True
    frontmatter, _body = parse_frontmatter(note.read_text(encoding="utf-8"))
    assert frontmatter["company"] == "Acme"
    assert frontmatter["role"] == "vip"
    assert frontmatter["name"] == STORED_DIRTY, "the stored name is untouched"

    # …while INTRODUCING that name through either door is refused.
    for door, call in (
        ("D5", lambda: update_frontmatter_field(note, "name", STORED_DIRTY)),
        ("D6", lambda: update_frontmatter_fields(note, {"name": STORED_DIRTY})),
    ):
        try:
            call()
        except NameGateRefusal as exc:
            assert exc.pattern == "calendar_prefix", door
        else:
            raise AssertionError(f"{door} must refuse an introduced Tier-1 name")

    # The refusals left the note byte-identical.
    frontmatter, _body = parse_frontmatter(note.read_text(encoding="utf-8"))
    assert frontmatter["company"] == "Acme" and frontmatter["role"] == "vip"


def _check_roundtrip_commits_a_stored_dirty_note(vault: Path):
    """D7 introduces nothing, so its gate call can never refuse."""
    vault.mkdir(parents=True)
    note = plant_note(vault, f"@{STORED_DIRTY}", type="person", name=STORED_DIRTY)
    roundtrip_file(note)
    frontmatter, _body = parse_frontmatter(note.read_text(encoding="utf-8"))
    assert frontmatter["name"] == STORED_DIRTY
    assert frontmatter["type"] == "person"


def _check_the_scalar_container_still_commits(vault: Path):
    """The list-shape precondition at ARM granularity — where the shape actually
    arrives. `update_frontmatter_field` types its value `Any`, so this is a
    legal call that commits a scalar today and must still commit one."""
    vault.mkdir(parents=True)
    note = plant_note(vault, "@Dave Smith", type="person", name="Dave Smith")

    assert update_frontmatter_field(note, "phones", "+44 7700 900123") is True
    frontmatter, _body = parse_frontmatter(note.read_text(encoding="utf-8"))
    assert frontmatter["phones"] == "+44 7700 900123", (
        "RED under a build that iterates the value, which commits a list of "
        "sixteen single characters; and RED under a build that refuses it, "
        "which raises on a call that succeeds today"
    )

    # And the well-shaped case through the same door still normalizes.
    update_frontmatter_field(note, "phones",
                             ["447700900123", "+44 7700 900123"])
    frontmatter, _body = parse_frontmatter(note.read_text(encoding="utf-8"))
    assert frontmatter["phones"] == ["+44 7700 900123"]


# ---------------------------------------------------------------------------
# Task 11 — AC-1's full per-arm triple
# ---------------------------------------------------------------------------

TIER2_DIRTY = "Dave  Smith"       # double space: Tier 2, never Tier 1


def test_every_frontmatter_door_routes_through_the_semantic_gate():
    """AC-1's check. Zero-arg and raising, per the check contract."""
    files = _live_files()

    # (a)/(b)/(c) — the floor, the driven reach battery and the near-miss are a
    # STANDING artifact (Task 6's module) that re-resolves on this post-routing
    # tree unedited. They are re-asserted here rather than assumed, and they
    # must not be relaxed to accommodate a routing edit.
    _check_the_live_floor_and_the_edited_function_equalities()

    arms = set(frontmatter_write_arms(files))
    declarations = gate_call_declarations(files)
    placements = gate_call_placement(files)

    # EVERY member routes. A ninth arm added without a gate call — whether a new
    # function or a new branch inside an existing one — is red here without
    # editing the wall, because it joins `arms` and not `declarations`.
    unrouted = arms - set(declarations)
    assert not unrouted, (
        f"these write arms reach vault bytes with no gate call: {sorted(unrouted)}"
    )

    _check_the_pass_what_pin(arms, declarations)
    _check_the_placement_pin(arms, placements)
    _check_the_association(arms, placements)

    with temp_dir() as root:
        _check_the_rider_is_not_a_member_but_is_pinned(root / "rider")
    with temp_dir() as root:
        _check_the_name_identity_control_at_every_arm(root / "identity")


def _check_the_pass_what_pin(arms, declarations):
    """AC-1(d). The declaration each arm hands the gate is the one available AT
    that arm — and where none is available the absence is EXPRESSED rather than
    defaulted."""
    # `Constant` == {D7} BY EQUALITY. D7 is the one arm whose frame holds no
    # declaration to express: it parses a note it does not judge, and the only
    # dict in its frame binds INSIDE the lock while its gate call sits above.
    constants = {arm for arm in arms if declarations.get(arm) == "constant"}
    assert constants == {D7}, (
        f"only roundtrip_file may pass a literal; found {sorted(constants)}"
    )

    # `absent` == {} BY EQUALITY. This is the STATIC half of the no-default
    # signature — the runtime half is a TypeError — so a reader of the wall
    # alone cannot conclude that omitting the keyword is a permitted shape.
    absent = {arm for arm in arms if declarations.get(arm) == "absent"}
    assert absent == set(), (
        f"no arm may omit the declared_type keyword; found {sorted(absent)}"
    )

    # Every remaining arm passes the declaration the design names for it.
    assert declarations[D1A] == "type_get_call"
    assert declarations[D1B] == "type_get_call", (
        "read at the convergence point, this IS the POST-merge dict's `type:`"
    )
    assert declarations[D1C] == "type_get_call"
    assert declarations[D4] == "attribute", "self.type_name, carried unconditionally"
    assert declarations[D5] == "type_get_call", "the target note's own in-lock parse"
    assert declarations[D6] == "type_get_call"
    assert declarations[D8] == "type_get_call", (
        "fm.get('type') off the in-lock parse — never vf.entity_type, which "
        "this frame is never handed"
    )
    for arm in arms:
        assert declarations.get(arm) != "other", (
            f"{arm} passes an unclassifiable declaration expression"
        )


def _check_the_placement_pin(arms, placements):
    """AC-1(e). The triple (arm, declaration passed, gate-call placement), with
    the REQUIRED value DERIVED by one local syntactic rule over the arm's own
    frame rather than listed."""
    for arm in arms:
        site = placements[arm]
        assert site.observed == site.required, (
            f"{arm}: gate call is {site.observed} but its own frame requires "
            f"{site.required}. The repair is that frame's existence guard, "
            "never a hoist above the parse that supplies its type."
        )

    resolved_above = {arm for arm in arms if placements[arm].required == "above"}
    resolved_in_lock = {arm for arm in arms
                        if placements[arm].required == "in-lock"}
    assert PLACEMENT_ABOVE <= resolved_above
    assert PLACEMENT_IN_LOCK <= resolved_in_lock
    assert not (PLACEMENT_ABOVE & resolved_in_lock)
    assert not (PLACEMENT_IN_LOCK & resolved_above)

    # THE RED CONSISTENCY LEG, asserted as a check and never as a second route
    # to `in-lock`: an arm whose gate ARGUMENTS are bound below the anchor while
    # the one rule requires `above` is a CONTRADICTION the wall reports.
    contradictions = {arm for arm in arms
                      if placements[arm].required == "above"
                      and placements[arm].arguments_bound_in_lock}
    assert contradictions == set(), (
        f"{sorted(contradictions)}: the frame's gate arguments are bound inside "
        "the lock while the placement rule requires the call above it. The "
        "repair is that frame's missing existence guard."
    )

    # And the three arms that MUST stay in-lock really do read their declaration
    # from the note there.
    for arm in (D5, D6, D8):
        assert placements[arm].arguments_bound_in_lock is True


def _check_the_association(arms, placements):
    """Each of the six arm functions carries exactly ONE gate call, and that
    call is not nested inside a branch that binds an arm — so a call written
    inside `if entity is not None:` is RED here as well as at the two per-arm
    predicates."""
    for arm in arms:
        site = placements[arm]
        assert site.calls_in_function == 1, (
            f"{arm.qualname} carries {site.calls_in_function} gate calls; the "
            "association attributes every arm of a function to its ONE call"
        )
        assert site.nested_in_arm_branch is False, (
            f"{arm.qualname}'s gate call sits inside a branch that binds an arm "
            "— the exact bypass arm granularity was invented to close"
        )


def _check_the_rider_is_not_a_member_but_is_pinned(vault: Path):
    """AC-1(f). The rider is the ONE gate call the wall cannot see, and the only
    frame that can write normalized values back onto a MODEL — the gate returns
    a dict and never touches one. Stated as a non-member so a future sweep
    neither misses it nor re-derives it as a ninth arm."""
    counts = _arms_by_function(frontmatter_write_arms(_live_files()))
    assert counts.get(
        ("obsidian_schemas/repositories/person.py", "PersonRepository.save"), 0
    ) == 0

    vault.mkdir(parents=True)
    repo = PersonRepository(vault)
    person = Person(name="Dave Smith", emails=["Al B <A@B.com>"], aliases=[])
    repo.save(person)
    assert person.emails == ["a@b.com"], (
        "the rider's write-back is what preserves the in-place model mutation "
        "callers observe; no other frame can perform it"
    )
    assert person.aliases == ["Al B"]
    assert person.name == "Dave Smith"


def _check_the_name_identity_control_at_every_arm(vault: Path):
    """AC-1(g). RED for a build that reaches for NameValidator.clean or for
    validate_strict's RETURN value.

    D7 is excluded with the rest of the introduce-a-name family: it introduces
    no fields at all.
    """
    vault.mkdir(parents=True)

    # The three D1 arms, by direct call.
    for index, kwargs in enumerate((
        dict(entity=Person(name=TIER2_DIRTY)),
        dict(frontmatter={"type": "person", "name": TIER2_DIRTY}),
        dict(extra_fields={"type": "person", "name": TIER2_DIRTY}),
    )):
        target = vault / f"@d1-{index}.md"
        write_markdown_file(target, **kwargs)
        frontmatter, _body = parse_frontmatter(target.read_text(encoding="utf-8"))
        assert frontmatter["name"] == TIER2_DIRTY, f"D1 arm {index}"

    # D5 and D6.
    note = plant_note(vault, "@carrier", type="person", name="Dave Smith")
    update_frontmatter_field(note, "name", TIER2_DIRTY)
    frontmatter, _body = parse_frontmatter(note.read_text(encoding="utf-8"))
    assert frontmatter["name"] == TIER2_DIRTY, "D5"
    update_frontmatter_fields(note, {"name": TIER2_DIRTY})
    frontmatter, _body = parse_frontmatter(note.read_text(encoding="utf-8"))
    assert frontmatter["name"] == TIER2_DIRTY, "D6"

    # D4, and the STEM/STORED-NAME agreement it shares with the entity path.
    repo = PersonRepository(vault / "repo")
    (vault / "repo").mkdir()
    path = repo.save(Person(name=TIER2_DIRTY))
    assert path.stem.lstrip("@") == TIER2_DIRTY
    frontmatter, _body = parse_frontmatter(path.read_text(encoding="utf-8"))
    assert frontmatter["name"] == TIER2_DIRTY, (
        "the filename is bound from the RAW name one frame above the gate and "
        "never revisited — a repaired name here forks the note's identity"
    )
    repo.update_fields(repo.get(TIER2_DIRTY), {"name": TIER2_DIRTY})
    frontmatter, _body = parse_frontmatter(path.read_text(encoding="utf-8"))
    assert frontmatter["name"] == TIER2_DIRTY, "D4"


# ---------------------------------------------------------------------------
# Task 16 — wall membership, closed by RUNNING each wall's own predicate
# ---------------------------------------------------------------------------

# The package and script files this item creates or edits. Its INBOUND half:
# every one of these JOINS the standing walls' universes, and the walls' claims
# must hold of them.
TOUCHED_PACKAGE_FILES = (
    "obsidian_schemas/name_gate.py",
    "obsidian_schemas/phone_normalization.py",
    "obsidian_schemas/errors.py",
    "obsidian_schemas/__init__.py",
    "obsidian_schemas/name_validation.py",
    "obsidian_schemas/identifier.py",
    "obsidian_schemas/writer.py",
    "obsidian_schemas/repositories/base.py",
    "obsidian_schemas/repositories/person.py",
    "scripts/lint_vault.py",
)

# The test modules this item creates or edits. Only ONE standing assertion has a
# universe that GROWS when a test file is added — the single-AST-home one — and
# it is asserted by set EQUALITY, so every module below has exactly one legal
# way to obtain syntax: import a predicate from the shared scan module.
TOUCHED_TEST_FILES = (
    "tests/derivations.py",
    "tests/test_loud_fail_harness.py",
    "tests/test_phone_normalization.py",
    "tests/test_name_gate.py",
    "tests/test_name_gate_wall.py",
    "tests/test_name_gate_refusals.py",
    "tests/test_name_gate_delta_rule.py",
    "tests/test_name_gate_identifiers.py",
    "tests/test_address_splitter.py",
    "tests/test_lint_vault_fix_gate.py",
)

DOOR_MODULE = "obsidian_schemas/vault_io.py"
WALL_C_MODULES = frozenset(FS_MODULES - {"os"})

# The five functions `test_loud_fail_write.py` classifies falsy returns in. This
# item deletes a function from that module and adds two, so the removal
# direction has to be re-derived rather than assumed.
PERSON_FALSY_RETURN_FUNCTIONS = {
    "PersonRepository.append_to_timeline",
    "PersonRepository.append_to_body_section",
    "PersonRepository.update_to_discuss_item",
    "PersonRepository.remove_to_discuss_item",
    "PersonRepository._get_body_content",
}


def test_wall_membership_is_closed_by_running_each_walls_predicate():
    """Task 16's verify. Zero-arg and raising, per the check contract.

    Every wall that sweeps a file this item touched is RUN on that file's final
    text and its own requirement asserted here. This is the inbound half of the
    verification: the outbound half (does this item's own wall hold?) is Task
    11's; this asks whether the item's files satisfy the walls that were already
    standing.
    """
    touched = [PACKAGE_ROOT.parent / name for name in TOUCHED_PACKAGE_FILES]
    for path in touched:
        assert path.exists(), f"{path} — a Write Target that is not on disk"

    _check_walls_a_b_and_c(touched)
    _check_wall_d(touched)
    _check_wall_e(touched)
    _check_the_ast_capability_stays_single_homed()
    _check_the_loud_fail_write_universe_in_the_removal_direction()


def _check_walls_a_b_and_c(touched):
    """Walls A/B/C — the routing wall, whose universe is the package and the
    scripts root, and which every one of the ten touched files joins."""
    offenders = [use for use in filesystem_mutation_uses(touched)
                 if use.module != DOOR_MODULE]
    assert not offenders, (
        "a filesystem-mutation capability is named outside the one permitted "
        "home. The fix is to route through vault_io — NEVER to add an "
        "exemption. This is also what makes lint_vault's new existence guard a "
        "read-only `Path.exists` probe rather than a `touch`. Found: "
        + ", ".join(f"{u.module}:{u.lineno} ({u.qualname})" for u in offenders)
    )

    os_offenders = [use for use in os_module_attribute_uses(touched)
                    if use.module != DOOR_MODULE
                    and use.qualname.split(".", 1)[1] not in OS_READONLY_NAMES]
    assert not os_offenders, (
        "a non-read-only `os` member is reached outside the door: "
        + ", ".join(f"{u.module}:{u.lineno} ({u.qualname})" for u in os_offenders)
    )

    import_offenders = [use for use in module_import_uses(touched, WALL_C_MODULES)
                        if use.module != DOOR_MODULE]
    assert not import_offenders, (
        "a mutation-capable module is imported outside the door: "
        + ", ".join(f"{u.module}:{u.lineno} ({u.qualname})"
                    for u in import_offenders)
    )


def _check_wall_d(touched):
    """Wall D — no new call to `parse_markdown_file`. D8's work parses through
    `parse_frontmatter`, so the answer is "no"; any edit reaching for the other
    seam in `scripts/` would be RED."""
    callers = {fid.module for fid in functions_calling(touched,
                                                       "parse_markdown_file")}
    assert callers <= {"obsidian_schemas/repositories/base.py"}, (
        f"a touched file gained a parse_markdown_file call: {sorted(callers)}"
    )


def _check_wall_e(touched):
    """Wall E — no falsy return from a member of the committing-door set.

    `gate_write` returns a dict and is NOT a member; it must not join that set,
    because the doors' contract is about returns a caller ACTS ON.
    """
    assert "gate_write" not in COMMIT_FUNCTION_NAMES
    assert "split_address" not in COMMIT_FUNCTION_NAMES
    sites = falsy_returns_in(touched, COMMIT_FUNCTION_NAMES)
    assert sites == [], (
        f"a committing door reports failure as a success-shaped value: {sites}"
    )


def _check_the_ast_capability_stays_single_homed():
    """The ONE standing assertion whose universe GROWS when this item adds a
    test file — and it is a set EQUALITY, so eight new test modules and two new
    package modules each have exactly one legal way to obtain syntax."""
    live = modules_using_ast(python_files_under(PACKAGE_ROOT, TESTS_ROOT))
    homes = {use.module for use in live}
    assert homes == {"tests/derivations.py"}, (
        "the ast capability must stay single-homed to the shared scan module; "
        f"found {sorted(homes)}"
    )
    for name in TOUCHED_TEST_FILES + TOUCHED_PACKAGE_FILES:
        if name == "tests/derivations.py":
            continue
        assert name not in homes, f"{name} names `ast`, which it may not"


def _check_the_loud_fail_write_universe_in_the_removal_direction():
    """The classification map over `person.py` is asserted BIDIRECTIONALLY by a
    standing wall, so a classified site that DISAPPEARS is red exactly as a new
    unclassified one is. This item deletes a function from that module and adds
    two, so the removal direction is re-derived here rather than assumed."""
    person = PACKAGE_ROOT / "repositories" / "person.py"
    sites = non_completed_write_sites([person])
    qualnames = {site.qualname for site in sites}
    assert qualnames == PERSON_FALSY_RETURN_FUNCTIONS, (
        "the falsy-return universe over person.py moved. The classification map "
        "is keyed PER FUNCTION, so it survives edits elsewhere in the module — "
        f"but not a change inside these five. Found: {sorted(qualnames)}"
    )
    assert len(sites) == 8, (
        f"eight classified sites, found {len(sites)}: {sorted(sites)}"
    )


# ---------------------------------------------------------------------------
# The environment the AC-2 directory fixtures depend on
# ---------------------------------------------------------------------------

def assert_default_lock_home():
    """OBSIDIAN_SCHEMAS_LOCK_DIR must be UNSET for any no-stray-directory leg.

    With an absolute value configured, `_sentinel_path` puts the sentinel
    OUTSIDE the vault and no `@Dave/` ever appears — so a fixture that sets it
    passes against un-hoisted code while production fails.
    """
    configured = os.environ.get("OBSIDIAN_SCHEMAS_LOCK_DIR")
    assert not configured, (
        "OBSIDIAN_SCHEMAS_LOCK_DIR is set to "
        f"{configured!r}; the artifact oracles run under the DEFAULT lock home"
    )
