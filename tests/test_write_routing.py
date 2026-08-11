"""WI-004's routing wall — five walls, each shipping its match-shape battery.

**Why every wall ships fixtures (WI-235).** A count oracle says NOTHING about a
matcher's reach: `matches == 0` is satisfied identically by a predicate that
resolves every claimed shape and by one that resolves almost none. Walls B, C
and E are each ZERO-COUNT on the arm the design leans on — there are no
`from os import` bindings, no `shutil`/`tempfile`/`fcntl`/`mmap` imports outside
the door, and no falsy returns anywhere — so a Wall B that never implements its
`ast.ImportFrom` arm, a Wall C that returns `[]` unconditionally and a Wall E
that resolves only the three door names are ALL green against this tree while
their criteria certify the opposite.

So each battery plants a scratch module and drives it through **the same
function the live wall calls, never a re-implementation**, asserting every
claimed shape MATCHED and every near-miss NOT matched. The near-misses are what
stop a wall from passing by matching everything; the declared blind spots are
what stop it from being "fixed" into a shape that cannot go green at all.
"""

from pathlib import Path

from tests.derivations import (
    COMMIT_FUNCTION_NAMES,
    FS_MODULES,
    OS_READONLY_NAMES,
    PACKAGE_ROOT,
    SCRIPTS_ROOT,
    base_repository_subclasses,
    falsy_returns_in,
    filesystem_mutation_uses,
    functions_calling,
    load_file_implementations,
    module_import_uses,
    os_module_attribute_uses,
    python_files_under,
)
from tests.support import temp_dir

SHARED_SCAN_MODULE = "tests.derivations"
DOOR_MODULE = "obsidian_schemas/vault_io.py"

# The module set Wall C polices. Derived from FS_MODULES minus `os`, which is
# deliberately NOT Wall C's business: a plain `import os` is legitimate at three
# live sites for `os.environ`, so `os` can only be policed at MEMBER
# granularity, which is Wall B's job.
WALL_C_MODULES = frozenset(FS_MODULES - {"os"})


def _single_sourced(*derivations):
    """Every wall imports its predicate from the shared scan module."""
    for derivation in derivations:
        assert derivation.__module__ == SHARED_SCAN_MODULE, (
            f"{derivation.__name__} is homed in {derivation.__module__}, not the "
            "shared scan module — a second copy IS the divergence"
        )


def _os_violations(uses):
    """Wall B's rule, applied ONCE and shared by the wall and its battery.

    `os_module_attribute_uses` returns every `os.<attr>` access and filters only
    its `ast.ImportFrom` arm; membership of OS_READONLY_NAMES is what Wall B
    decides on. Keeping that decision in one helper is what lets the battery
    drive the SAME code path the live wall takes rather than a second copy of
    the rule.
    """
    return [u for u in uses
            if u.qualname.split(".", 1)[-1] not in OS_READONLY_NAMES]


def _plant(directory: Path, name: str, source: str) -> Path:
    """A scratch module, PARSED and never imported or executed.

    It sits outside `python_files_under(PACKAGE_ROOT, SCRIPTS_ROOT)` by
    construction, so planting a mutation-capable import here can never reach a
    shipped module.
    """
    path = directory / name
    path.write_text(source, encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# AC-7 — Walls A, B and C, each with its battery
# ---------------------------------------------------------------------------

def test_filesystem_mutation_is_single_homed():
    """AC-7. Zero-arg and raising, per the conveyor's check contract."""
    _single_sourced(filesystem_mutation_uses, os_module_attribute_uses,
                    module_import_uses, python_files_under)
    files = python_files_under(PACKAGE_ROOT, SCRIPTS_ROOT)

    # --- WALL A: the live claim ------------------------------------------
    uses = filesystem_mutation_uses(files)
    offenders = [u for u in uses if u.module != DOOR_MODULE]
    assert not offenders, (
        "a filesystem-mutation capability is named outside the one permitted "
        "home. The fix is to route the call through vault_io — NEVER to remove "
        "a name from a vocabulary or add an exemption. Found: "
        + ", ".join(f"{u.module}:{u.lineno} ({u.qualname})"
                    for u in sorted(offenders, key=lambda u: (u.module, u.lineno)))
    )
    assert uses, (
        "the scan found NOTHING — an under-generating detector reports "
        "'single-homed' just as happily as a compliant one"
    )

    # --- WALL B: the live claim ------------------------------------------
    os_uses = os_module_attribute_uses(files)
    os_offenders = [u for u in _os_violations(os_uses) if u.module != DOOR_MODULE]
    assert not os_offenders, (
        "a non-read-only `os` member is reached outside the door. The "
        "discriminator is the MODULE, not the member, so a name no vocabulary "
        "ever anticipated is caught here. Found: "
        + ", ".join(f"{u.module}:{u.lineno} ({u.qualname})" for u in os_offenders)
    )

    # --- WALL C: the live claim ------------------------------------------
    imports = module_import_uses(files, WALL_C_MODULES)
    import_offenders = [u for u in imports if u.module != DOOR_MODULE]
    assert not import_offenders, (
        "a mutation-capable module is imported outside the door: "
        + ", ".join(f"{u.module}:{u.lineno} ({u.qualname})"
                    for u in import_offenders)
    )

    with temp_dir() as scratch:
        _wall_a_battery(scratch)
        _wall_b_battery(scratch)
        _wall_c_battery(scratch)


def _wall_a_battery(scratch: Path):
    """Every shape Wall A CLAIMS to resolve, driven through its own predicate."""
    matched_source = '''
import os
import shutil
import tempfile
from shutil import move
from os import replace as _r

def arm_a(p, q, b, s):
    p.write_text(s)
    p.write_bytes(b)
    Path(p).write_text(s)
    src.rename(dest)
    p.mkdir(parents=True)
    p.unlink()
    p.rmdir()
    p.touch()
    p.symlink_to(q)
    p.hardlink_to(q)
    p.chmod(0o600)

def arm_b(a, b, d, fd, by):
    os.replace(a, b)
    os.rename(a, b)
    os.remove(a)
    os.unlink(a)
    os.makedirs(d)
    os.link(a, b)
    os.write(fd, by)
    shutil.move(a, b)
    shutil.copyfile(a, b)
    shutil.copytree(a, b)
    shutil.rmtree(d)
    tempfile.NamedTemporaryFile()
    tempfile.mkstemp()

def arm_c(a, b):
    move(a, b)
    _r(a, b)

def arm_d(p):
    open(p, "w")
    open(p, mode="a")
    open(p, "x")
    p.open("w")
'''
    plant = _plant(scratch, "wall_a_matched.py", matched_source)
    resolved = filesystem_mutation_uses([plant])
    names = {u.qualname for u in resolved}
    for claimed in ("write_text", "write_bytes", "rename", "mkdir", "unlink",
                    "rmdir", "touch", "symlink_to", "hardlink_to", "chmod",
                    "os.replace", "os.rename", "os.remove", "os.unlink",
                    "os.makedirs", "os.link", "os.write", "shutil.move",
                    "shutil.copyfile", "shutil.copytree", "shutil.rmtree",
                    "tempfile.NamedTemporaryFile", "tempfile.mkstemp",
                    "move", "replace"):
        assert claimed in names, (
            f"Wall A claims to resolve {claimed!r} and its own predicate does "
            f"not. Resolved: {sorted(names)}"
        )
    assert any(n.startswith("open(mode=") for n in names), (
        f"arm (d) resolved no write-mode open; got {sorted(names)}"
    )

    # --- the NOT-matched half, including the three round-5 near-misses ----
    near_miss_source = '''
import os

def read_only_forms(p):
    open(p)
    open(p, "r")
    open(p, encoding="utf-8")
    fn = p.write_text          # an attribute ACCESS with no call
    os.environ.get("X")
    os.getcwd()
    return "write_text"        # a bare string literal, never source text

def homonyms(s, frontmatter, p, q):
    """A docstring naming shutil.move and os.replace."""
    # a comment mentioning os.replace
    s.replace("-", "")         # str.replace: fourteen live call nodes depend
                               # on this NOT matching
    frontmatter.copy()         # dict.copy: three live call nodes, one of them
                               # in parser.py, which is not a write target
    p.replace(q)               # R10, the DECLARED BLIND SPOT (D10.3).
                               # `replace` is the one Path mutator whose name
                               # collides with a builtin's method, so it is
                               # provenance-matched only. A reader who "fixes"
                               # this meets the ruling and the fourteen
                               # str.replace sites instead of shipping a wall
                               # that is red on arrival. Wall B independently
                               # makes os.replace red wherever it is named.
'''
    plant = _plant(scratch, "wall_a_near_miss.py", near_miss_source)
    resolved = filesystem_mutation_uses([plant])
    assert not resolved, (
        "Wall A matched a near-miss. Matching s.replace / frontmatter.copy / "
        "p.replace would make it RED ON DAY ONE against files the scope "
        "boundary forbids touching. Found: "
        + ", ".join(f"{u.qualname}@{u.lineno}" for u in resolved)
    )


def _wall_b_battery(scratch: Path):
    """Both of Wall B's access forms, and both halves of its readonly rule.

    ZERO-COUNT arm: there are no `from os import` bindings anywhere under either
    root, so a matcher that never implements the `ast.ImportFrom` collection is
    green at every other check in this build while AC-7 certifies "in either
    access form".
    """
    matched_source = '''
import os
import os as _o
from os import replace
from os import replace as _r
from os import unlink          # the BINDING, never called

def attribute_form(p, a, b, flags, fd, m):
    os.unlink(p)
    os.replace(a, b)
    os.open(p, flags)
    os.fchmod(fd, m)           # in NO vocabulary — the discriminator is the
                               # MODULE, not the member
    _o.unlink(p)               # the aliased module binding

def import_form(a, b):
    replace(a, b)
    _r(a, b)
'''
    plant = _plant(scratch, "wall_b_matched.py", matched_source)
    violations = _os_violations(os_module_attribute_uses([plant]))
    names = {u.qualname for u in violations}
    for claimed in ("os.unlink", "os.replace", "os.open", "os.fchmod"):
        assert claimed in names, (
            f"Wall B claims to resolve {claimed!r} and does not. Got {sorted(names)}"
        )
    # `from os import unlink` is never called, and the arm must still collect it.
    assert sum(1 for u in violations if u.qualname == "os.unlink") >= 2, (
        "the ImportFrom arm must collect the BINDING as well as the attribute "
        f"access — an unused mutator import is still a capability. Got {names}"
    )

    not_matched_source = '''
import os
from os import environ

def readonly_forms(a, b, p):
    """A docstring naming from os import unlink."""
    os.environ.get("X")
    os.getenv("X")
    os.getcwd()
    x = os.sep
    os.path.join(a, b)
    os.fspath(p)
    environ.get("Y")
    return "os.replace"        # parsed syntax, never source text

def other_module(a, b):
    shutil.move(a, b)          # not `os` — Wall C's and Wall A arm (b)'s
'''
    plant = _plant(scratch, "wall_b_near_miss.py", not_matched_source)
    violations = _os_violations(os_module_attribute_uses([plant]))
    assert not violations, (
        "Wall B flagged a read-only `os` member. All three live sites pass BY "
        "PREDICATE rather than by file exemption — that is its stated design. "
        f"Found: {[(u.qualname, u.lineno) for u in violations]}"
    )
    # A bare `import os` with no member access is Wall C's business, and Wall C
    # is deliberately not widened to `os`.
    plant = _plant(scratch, "wall_b_bare_import.py", "import os\n")
    assert not _os_violations(os_module_attribute_uses([plant])), (
        "a plain `import os` with no attribute access must not be a violation"
    )


def _wall_c_battery(scratch: Path):
    """Wall C's MATCHED imports are GENERATED by iterating the module set the
    wall is called with, so a member added to it cannot go unfixtured."""
    generated = "".join(f"import {module}\n" for module in sorted(WALL_C_MODULES))
    plant = _plant(scratch, "wall_c_matched.py", generated)
    resolved = module_import_uses([plant], WALL_C_MODULES)
    assert {u.qualname for u in resolved} == set(WALL_C_MODULES), (
        "Wall C must resolve every module it is called with; asked about "
        f"{sorted(WALL_C_MODULES)}, resolved {sorted({u.qualname for u in resolved})}"
    )

    both_forms = '''
import tempfile as _t
from filelock import FileLock
from shutil import move
from tempfile import NamedTemporaryFile as _n
import mmap                    # imported and NEVER used — the oracle is the
                               # IMPORT, not a call
'''
    plant = _plant(scratch, "wall_c_forms.py", both_forms)
    resolved = module_import_uses([plant], WALL_C_MODULES)
    assert {u.qualname for u in resolved} == {"tempfile", "filelock", "shutil", "mmap"}, (
        "Wall C must resolve both statement forms and their aliases; got "
        f"{sorted({u.qualname for u in resolved})}"
    )

    not_matched = '''
import os
import pathlib
from pathlib import Path
import hashlib
import threading

def not_imports():
    """A docstring naming import shutil."""
    # a comment naming import tempfile
    shutil = object()          # a local variable, with no import
    return "import shutil"     # parsed syntax, never source text
'''
    plant = _plant(scratch, "wall_c_near_miss.py", not_matched)
    resolved = module_import_uses([plant], WALL_C_MODULES)
    assert not resolved, (
        "Wall C matched a module outside its set — a wall matching everything "
        f"is as useless as one matching nothing. Found: {[u.qualname for u in resolved]}"
    )


# ---------------------------------------------------------------------------
# AC-12 — Wall D, the OBSERVATION side
# ---------------------------------------------------------------------------

def test_every_derived_loader_records_a_derivation_stamp():
    """AC-12. Walls A-C are total over MUTATION and structurally blind to a
    missing OBSERVATION: a loader that never records performs no write at all.
    """
    _single_sourced(functions_calling, load_file_implementations,
                    base_repository_subclasses, python_files_under)

    loaders = load_file_implementations(
        base_repository_subclasses(python_files_under(PACKAGE_ROOT)))
    files = python_files_under(PACKAGE_ROOT, SCRIPTS_ROOT)
    assert loaders, "the loader corpus is empty — the scan found nothing"

    # --- D(i): every loader records --------------------------------------
    for call in ("stat_stamp", "remember_snapshot"):
        callers = functions_calling(files, call)
        missing = loaders - callers
        assert not missing, (
            f"a loader in the derived corpus never calls {call!r}, so its entity "
            "type silently loses stamps and its first save() after load becomes "
            "NoteAlreadyExists: "
            + ", ".join(f"{f.module}:{f.qualname}" for f in sorted(missing))
        )

    # --- D(ii): nothing derives an entity OUTSIDE the corpus --------------
    derivers = functions_calling(files, "parse_markdown_file")
    assert derivers == loaders, (
        "an entity is derived from a note's bytes outside the loader corpus. "
        "Record a stamp there too, or say in writing why that payload never "
        f"reaches door 2. Extra: {sorted(derivers - loaders)}; "
        f"missing: {sorted(loaders - derivers)}"
    )

    with temp_dir() as scratch:
        _wall_d_battery(scratch)


def _wall_d_battery(scratch: Path):
    """A SUBSET assertion is satisfied identically by a predicate that resolves
    every call form and by one that resolves almost none (WI-235)."""
    matched_source = '''
def bare_name(x):
    foo(x)

class C:
    def attribute(self, x):
        self.foo(x)

def module_attribute(mod, x):
    mod.foo(x)

def nested_in_blocks(x, items):
    if x:
        foo(x)
    try:
        foo(x)
    except Exception:
        pass
    for item in items:
        foo(item)
'''
    plant = _plant(scratch, "wall_d_matched.py", matched_source)
    resolved = {f.qualname for f in functions_calling([plant], "foo")}
    for claimed in ("bare_name", "C.attribute", "module_attribute",
                    "nested_in_blocks"):
        assert claimed in resolved, (
            f"functions_calling must resolve {claimed!r}; got {sorted(resolved)}"
        )

    not_matched_source = '''
from m import foo

def only_a_docstring():
    """A docstring naming foo(x)."""
    # a comment naming foo(x)
    return "foo"

def only_an_attribute_access(self):
    fn = self.foo              # an access, never a call

def hides_it_in_a_closure(x):
    def inner():
        foo(x)                 # the _own_body_nodes boundary: a loader that
                               # hides its recording in a closure is
                               # deliberately RED
    return inner
'''
    plant = _plant(scratch, "wall_d_near_miss.py", not_matched_source)
    resolved = {f.qualname for f in functions_calling([plant], "foo")}
    for forbidden in ("only_a_docstring", "only_an_attribute_access",
                      "hides_it_in_a_closure"):
        assert forbidden not in resolved, (
            f"functions_calling matched {forbidden!r}, which it must not; "
            f"got {sorted(resolved)}"
        )


# ---------------------------------------------------------------------------
# AC-13 — Wall E, the doors' no-falsy-return contract
# ---------------------------------------------------------------------------

def test_committing_doors_never_return_falsy():
    """AC-13. The rule is stated over exactly the set the wall checks, and the
    predicate's REACH is DRIVEN rather than assumed."""
    _single_sourced(falsy_returns_in, python_files_under)

    sites = falsy_returns_in(python_files_under(PACKAGE_ROOT),
                             COMMIT_FUNCTION_NAMES)
    assert not sites, (
        "a path-, payload- or stamp-returning door returns a FALSY value. Every "
        "failure on those paths must raise — a falsy return is the silent-noop "
        "class WI-020 exists to kill. Found: "
        + ", ".join(f"{s.module}:{s.qualname}#{s.ordinal}" for s in sites)
    )

    with temp_dir() as scratch:
        _wall_e_battery(scratch)


def _wall_e_battery(scratch: Path):
    """The fixture space is DERIVED from COMMIT_FUNCTION_NAMES by ITERATING the
    frozenset, and asserted by SET EQUALITY rather than by containment — so a
    name added to the constant later cannot go unfixtured, and today's
    `read_note` / `stat_stamp` / `record_snapshot` / `ensure_dir` members are
    driven rather than assumed.
    """
    generated = "".join(
        f"def {name}(x):\n    return None\n\n" for name in sorted(COMMIT_FUNCTION_NAMES)
    )
    plant = _plant(scratch, "wall_e_generated.py", generated)
    resolved = {s.qualname.rsplit(".", 1)[-1]
                for s in falsy_returns_in([plant], COMMIT_FUNCTION_NAMES)}
    assert resolved == set(COMMIT_FUNCTION_NAMES), (
        "Wall E's reach must cover its WHOLE declared set. A falsy_returns_in "
        "resolving only the three door names leaves a `return None` in "
        "read_note or ensure_dir invisible while Wall E and AC-13 are both "
        f"green. Asked {sorted(COMMIT_FUNCTION_NAMES)}, resolved {sorted(resolved)}"
    )

    forms_source = '''
def write_note(x):
    return

class X:
    def read_note(self):
        return None            # a METHOD counts: selection is by the LAST
                               # dotted segment of the qualname

def create_note(x):
    if x:
        return ""              # the falsy-Constant arm, broader than the three
    return 0                   # named forms

def move_note(x):
    if x:
        return None
    try:
        return False           # _own_body_nodes descends into non-function
    except Exception:          # children
        pass
'''
    plant = _plant(scratch, "wall_e_forms.py", forms_source)
    sites = falsy_returns_in([plant], COMMIT_FUNCTION_NAMES)
    by_name = {}
    for site in sites:
        by_name.setdefault(site.qualname.rsplit(".", 1)[-1], []).append(site)
    for name, expected in (("write_note", 1), ("read_note", 1),
                           ("create_note", 2), ("move_note", 2)):
        assert len(by_name.get(name, [])) == expected, (
            f"Wall E must resolve {expected} falsy return(s) in {name!r}; got "
            f"{len(by_name.get(name, []))}"
        )

    not_matched_source = '''
def write_note(path):
    return path                # an ast.Name is never a member, which is why a
                               # door returning a real path is legal

def create_note(x):
    if x:
        return True
    return "text"

def move_note(x):
    return 1

def helper(x):
    return None                # a name outside COMMIT_FUNCTION_NAMES

def snapshot_stamp(x):
    return None                # DELIBERATE: this None IS the zero case the
                               # whole precondition rule is built on (D1, D4,
                               # D8 step 5). A wall that matched it would be RED
                               # AGAINST THE DESIGN.

def guard_mode():
    return None

def write_note(x):
    def inner():
        return None            # the _own_body_nodes BOUNDARY: a falsy return
                               # inside a NESTED function of write_note is not
                               # write_note's own, which is the same boundary
                               # Wall D's battery pins and the same reason the
                               # routed body writers may not move a dedup check
                               # into a closure
    return inner

def read_note(path):
    """A docstring naming return None."""
    name = "write_note"        # parsed syntax, never source text
    return name
'''
    plant = _plant(scratch, "wall_e_near_miss.py", not_matched_source)
    sites = falsy_returns_in([plant], COMMIT_FUNCTION_NAMES)
    assert not sites, (
        "Wall E matched a near-miss. In particular snapshot_stamp's None is the "
        "ZERO CASE and must never be a member. Found: "
        + ", ".join(f"{s.qualname}#{s.ordinal}" for s in sites)
    )

    # The DECLARED LIMIT, pinned so a later reader meets it rather than
    # "fixing" the wall into a claim it does not make: an implicit
    # fall-off-the-end is not an ast.Return node and is invisible by
    # construction.
    plant = _plant(scratch, "wall_e_implicit.py",
                   "def write_note(x):\n    if x:\n        pass\n")
    assert not falsy_returns_in([plant], COMMIT_FUNCTION_NAMES), (
        "an implicit fall-off-the-end carries no ast.Return and is outside this "
        "predicate's declared reach — pinned NOT matched deliberately"
    )
