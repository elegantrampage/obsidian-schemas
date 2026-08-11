"""The ONE shared importable scan module for WI-020's derived sweeps.

Every criterion that derives a sweep imports its derivation FROM HERE. Two
independently-written predicates that agree on today's tree diverge on the first
future write path, and that divergence IS the refuse-vs-propagate collision the
cross-criterion partition exists to catch — solve-in-one-place applies to the
harness as much as to the package.

Not a test file: `pyproject.toml` collects `test_*.py` only, so pytest will not
collect this. It is importable with no new machinery — `tests/__init__.py` makes
`tests/` a package under the rootdir prepend the whole suite already depends on,
and there is no `conftest.py` anywhere in the tree.

**This is the only file under `obsidian_schemas/` or `tests/` permitted to name
`ast`.** AC-7 asserts that single-homing by scanning for the capability every
derivation copy must exercise. A private re-implementation of any scan below is
therefore detectable even when nothing binds it.

Roots are derived from this file's own location, never from the cwd and never
from a path substring: the suite runs from a foreign cwd and inside a build
worktree whose path is not knowable in advance.
"""

import ast
from pathlib import Path
from typing import Iterable, NamedTuple, Optional

_REPO_ROOT = Path(__file__).resolve().parent.parent
PACKAGE_ROOT = _REPO_ROOT / "obsidian_schemas"
TESTS_ROOT = _REPO_ROOT / "tests"
SCRIPTS_ROOT = _REPO_ROOT / "scripts"


# --------------------------------------------------------------------------
# WI-004's routing vocabulary, PARTITIONED BY RESOLVABILITY (D10.1).
#
# The partition is not cosmetic. An attribute-NAME oracle over a vocabulary of
# stdlib verbs cannot separate a filesystem receiver from a str/dict receiver,
# and this tree exercises the non-filesystem side of two of those verbs today
# (fourteen `str.replace` call nodes, three `dict.copy` ones). So a name is
# matched on its own ONLY when it has no homonym; everything else is matched
# through IMPORT PROVENANCE, which is a discriminator syntax can decide.
# --------------------------------------------------------------------------

DOOR_NAMES = frozenset({"write_note", "create_note", "move_note"})

# (1) pathlib.Path mutator methods with NO str/dict/list/set homonym. Safe to
#     match on ATTRIBUTE NAME alone, on any receiver -- and the MUST-NOT-MATCH
#     battery in tests/test_write_routing.py is what keeps that claim honest.
PATH_MUTATION_NAMES = frozenset({
    "write_text", "write_bytes", "mkdir", "rmdir", "unlink", "rename",
    "symlink_to", "hardlink_to", "link_to", "touch", "chmod", "lchmod",
})

# (2) names that are filesystem verbs ONLY as members of a filesystem module.
#     Matched ONLY through import provenance, never on attribute name, because
#     each has (or could have) a live non-filesystem homonym: `replace` is
#     str.replace, `copy` is dict.copy, `write` is any file object's.
MODULE_MUTATION_NAMES = frozenset({
    "replace", "remove", "removedirs", "makedirs", "renames", "rename",
    "unlink", "rmdir", "link", "symlink", "truncate", "chown", "fdopen",
    "open", "write", "move", "copy", "copy2", "copyfile", "copytree",
    "rmtree", "mkstemp", "mkdtemp", "NamedTemporaryFile", "TemporaryFile",
})

FS_MODULES = frozenset({"os", "shutil", "tempfile", "fcntl", "filelock", "mmap"})
OS_READONLY_NAMES = frozenset({"environ", "getenv", "sep", "path", "fspath", "getcwd"})

# The vault_io surface whose returns a caller ACTS ON -- its path-, payload- and
# stamp-returning functions. `ensure_dir` returns the directory a caller then
# writes into and `read_note`/`stat_stamp` return the payload and the
# precondition a caller then commits on, so a falsy return from any of them is
# the same silent-noop class as one from `write_note`. `snapshot_stamp` is
# deliberately OUTSIDE the set: its None IS the zero case the whole precondition
# rule is built on.
COMMIT_FUNCTION_NAMES = frozenset({
    "write_note", "create_note", "move_note", "read_note",
    "stat_stamp", "record_snapshot", "ensure_dir",
})


# --------------------------------------------------------------------------
# Source-stable identities. NEVER a line number: this fix shifts every line
# number in person.py, and a function name alone cannot separate
# append_to_timeline's sites across three different buckets.
# --------------------------------------------------------------------------

class FunctionId(NamedTuple):
    module: str        # posix relpath from the repo root, e.g. "obsidian_schemas/writer.py"
    qualname: str      # e.g. "BaseRepository.update_fields"

    @property
    def name(self) -> str:
        return self.qualname.rsplit(".", 1)[-1]


class SiteId(NamedTuple):
    module: str
    qualname: str
    ordinal: int       # position among the sites the scan returns for that function


class AstUse(NamedTuple):
    module: str
    qualname: str
    lineno: int


def module_id(path: Path) -> str:
    """The ONE rule mapping a file on disk to the `module` field above.

    Public because a consumer that needs to name a file the scan reported must
    ASK for its identity rather than re-derive it. AC-7's planted negatives
    proved why: a check that spelled the plants' identity as `str(path)` was
    green only while the temp directory sat outside the repo root, and went red
    the moment `TMPDIR` pointed inside it (a build worktree's `tmp/`), because
    the relative branch below then applies. Two spellings of one rule diverge on
    an environment neither author picked — which is the second home this module
    exists to forbid, wearing a path instead of a predicate.

    Repo-relative posix inside the tree ("obsidian_schemas/writer.py"), the
    resolved absolute path outside it. Resolved on BOTH branches so the two
    spellings of a macOS temp path (`/var/...` and `/private/var/...`) cannot
    produce two identities for one file.
    """
    resolved = Path(path).resolve()
    try:
        return resolved.relative_to(_REPO_ROOT).as_posix()
    except ValueError:
        return str(resolved)


# --------------------------------------------------------------------------
# 1. The file-set walk (AC-1, AC-2, AC-3, AC-5, AC-7)
# --------------------------------------------------------------------------

def python_files_under(*roots: Path) -> list:
    """Every .py file under each root, recursively, discovered ON DISK.

    Parameterized rather than package-fixed precisely so AC-7's planted
    negatives can be scanned by the same code the live sweeps use: the sweeps
    pass PACKAGE_ROOT, AC-7 passes (PACKAGE_ROOT, TESTS_ROOT) for the live
    assertion and tmp_path for the plants. One walk, four uses.

    Naming a directory inside the scan would be the frozen list wearing a path:
    a fifth repository or a sixth silent-False writer added in a NEW module is
    invisible to a hand-scoped scan exactly as it is to the import graph.
    """
    out = []
    for root in roots:
        out.extend(sorted(Path(root).rglob("*.py")))
    # dedupe, preserving order
    seen = set()
    unique = []
    for p in out:
        rp = p.resolve()
        if rp not in seen:
            seen.add(rp)
            unique.append(p)
    return unique


# --------------------------------------------------------------------------
# Shared AST plumbing
# --------------------------------------------------------------------------

def _parse(path: Path):
    return ast.parse(Path(path).read_text(encoding="utf-8"))


def _iter_functions(path: Path, tree=None):
    """Yield (FunctionId, node) for every function/method defined in the file.

    Qualnames are built from the real nesting stack, so a method reads
    "BaseRepository.update_fields" and a module-level function reads its bare
    name — the same shape __qualname__ produces, which is what lets a
    class-derived contribution be normalised into this domain.
    """
    if tree is None:
        tree = _parse(path)
    module = module_id(path)

    def walk(node, prefix):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                qual = f"{prefix}{child.name}"
                yield FunctionId(module, qual), child
                yield from walk(child, f"{qual}.<locals>.")
            elif isinstance(child, ast.ClassDef):
                yield from walk(child, f"{prefix}{child.name}.")
            else:
                yield from walk(child, prefix)

    yield from walk(tree, "")


def _own_body_nodes(func):
    """Every node inside `func` that does NOT belong to a nested function.

    Without this, a nested def's returns would be attributed to its parent and
    the site ordinals would silently shift.
    """
    out = []

    def walk(node):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                continue
            out.append(child)
            walk(child)

    walk(func)
    return out


def _called_names(func) -> set:
    """Every name this function CALLS — `f(...)` and `x.f(...)` alike.

    Attribute calls are collected by attribute name because that is what makes
    `self._load_file(...)` resolvable to the three implementations without a
    type inference pass this harness has no business doing.
    """
    names = set()
    for node in _own_body_nodes(func):
        if isinstance(node, ast.Call):
            f = node.func
            if isinstance(f, ast.Name):
                names.add(f.id)
            elif isinstance(f, ast.Attribute):
                names.add(f.attr)
    return names


def _names_in(node) -> set:
    return {n.id for n in ast.walk(node) if isinstance(n, ast.Name)}


def _is_write_call(node) -> bool:
    """A call that commits bytes to the filesystem.

    WI-004 widened the attr set by DOOR_NAMES and changed NOTHING else -- in
    particular the `ast.Attribute` gate stays. After that item the way package
    code commits bytes is by calling a vault_io door AS A MODULE ATTRIBUTE
    (`vault_io.write_note(...)`), so the meaning is unchanged and the extension
    carries over to the three sweeps that consume this predicate.
    """
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr in ({"write_text", "write_bytes"} | DOOR_NAMES)
    )


def _parse_frontmatter_calls(func):
    return [
        n for n in _own_body_nodes(func)
        if isinstance(n, ast.Call)
        and isinstance(n.func, ast.Name)
        and n.func.id == "parse_frontmatter"
    ]


# --------------------------------------------------------------------------
# 2. The LOOSE scan — "calls parse_frontmatter and later writes" (AC-1's
#    negative, AC-2's guard contribution via the set difference)
# --------------------------------------------------------------------------

def functions_parsing_then_writing(files: Iterable[Path]) -> set:
    """Adjacency, NOT data flow. This predicate is deliberately too loose: it
    returns write_markdown_file, which AC-1 must NOT sweep. It exists so that
    exclusion can be PROVEN by a predicate rather than performed by name, and so
    that AC-4's guard can be COMPUTED as this set minus the data-flow set rather
    than hardcoded into AC-2's stop set.
    """
    found = set()
    for path in files:
        tree = _parse(path)
        for fid, func in _iter_functions(path, tree):
            parses = _parse_frontmatter_calls(func)
            if not parses:
                continue
            first_parse = min(n.lineno for n in parses)
            if any(_is_write_call(n) and n.lineno > first_parse
                   for n in _own_body_nodes(func)):
                found.add(fid)
    return found


# --------------------------------------------------------------------------
# 3. The DATA-FLOW scan — the dict parse_frontmatter returned is re-serialized
#    into the bytes this same function writes (AC-1, AC-2)
# --------------------------------------------------------------------------

def functions_reserializing_parsed_frontmatter(files: Iterable[Path]) -> set:
    """The real predicate behind AC-1's sweep.

    A member is a function in which the FRONTMATTER DICT returned by
    parse_frontmatter reaches the argument of that function's own write call.
    write_markdown_file binds only the body half (`_, existing_body = ...`) and
    builds what it writes from its own entity/frontmatter ARGUMENTS, so it is
    reached by this traversal and rejected by this predicate — which is exactly
    the discrimination proof AC-1 requires, obtained without naming it.
    """
    found = set()
    for path in files:
        tree = _parse(path)
        for fid, func in _iter_functions(path, tree):
            if _taints_a_write(func):
                found.add(fid)
    return found


def _taints_a_write(func) -> bool:
    body = _own_body_nodes(func)

    # Seed: the name bound to the FRONTMATTER half (tuple position 0) of a
    # parse_frontmatter call. A function that discards it (`_, body = ...`)
    # seeds `_`, which then reaches nothing — no special case needed.
    tainted = set()
    for node in body:
        if not isinstance(node, ast.Assign):
            continue
        if not (isinstance(node.value, ast.Call)
                and isinstance(node.value.func, ast.Name)
                and node.value.func.id == "parse_frontmatter"):
            continue
        for target in node.targets:
            if isinstance(target, ast.Tuple) and target.elts:
                head = target.elts[0]
                if isinstance(head, ast.Name):
                    tainted.add(head.id)
            elif isinstance(target, ast.Name):
                # bound as a whole tuple — the dict is inside it
                tainted.add(target.id)
    if not tainted:
        return False

    # Propagate to a fixpoint: any assignment whose VALUE mentions a tainted
    # name taints its targets. Fixpoint rather than one pass so that source
    # order and loops cannot hide a hop.
    changed = True
    while changed:
        changed = False
        for node in body:
            if not isinstance(node, ast.Assign):
                continue
            if not (_names_in(node.value) & tainted):
                continue
            for target in node.targets:
                for name in _names_in(target):
                    if name not in tainted:
                        tainted.add(name)
                        changed = True

    # Sink: a write call carrying a tainted name.
    for node in body:
        if _is_write_call(node):
            for arg in list(node.args) + [k.value for k in node.keywords]:
                if _names_in(arg) & tainted:
                    return True
    return False


# --------------------------------------------------------------------------
# 4. The subclass scan (AC-3, and AC-2 via the MRO resolution)
# --------------------------------------------------------------------------

def base_repository_subclasses(files: Iterable[Path]) -> set:
    """Concrete BaseRepository subclasses, discovered from SOURCE.

    Deliberately NOT `BaseRepository.__subclasses__()`: the import graph is a
    weaker oracle than the source. A fifth repository module that
    `repositories/__init__.py` does not import is invisible to a runtime check
    at test time, so that discovery clause would reproduce the green-suite /
    zero-coverage gap it exists to close. Discovery is from source; the test
    then imports what the scan discovered.
    """
    import importlib

    found = set()
    for path in files:
        tree = _parse(path)
        module_rel = module_id(path)
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            if not any(_names_base(b) == "BaseRepository" for b in node.bases):
                continue
            mod_name = module_rel[:-len(".py")].replace("/", ".")
            cls = getattr(importlib.import_module(mod_name), node.name, None)
            if cls is not None:
                found.add(cls)
    return found


def _names_base(base) -> Optional[str]:
    """The base's bare name, seeing through `BaseRepository[Person]`."""
    if isinstance(base, ast.Subscript):
        base = base.value
    if isinstance(base, ast.Name):
        return base.id
    if isinstance(base, ast.Attribute):
        return base.attr
    return None


# --------------------------------------------------------------------------
# 5. The MRO resolution (AC-2)
# --------------------------------------------------------------------------

def load_file_implementations(classes: Iterable) -> set:
    """Resolve each discovered CLASS to the FUNCTION implementing its
    `_load_file`, then deduplicate.

    This conversion belongs to the consumer, and it is required rather than
    cosmetic: a class is not a member of a closure over functions, so consuming
    the subclass scan literally would contribute NOTHING to the stop set — the
    closure would never stop at base._load_file and would climb through load(),
    get_all() and resolve() into every consumer-facing method.

    The map is MANY-TO-ONE: four classes resolve to three functions today
    (PersonRepository and CompanyRepository declare no _load_file of their own),
    so a check asserting one loader per discovered class is red on a correct
    implementation.
    """
    out = set()
    for cls in classes:
        for owner in cls.__mro__:
            func = owner.__dict__.get("_load_file")
            if func is not None:
                out.add(_function_id_of(func))
                break
    return out


def _function_id_of(func) -> FunctionId:
    """Normalise a live function object into the source-stable domain."""
    module = func.__module__.replace(".", "/") + ".py"
    return FunctionId(module, func.__qualname__)


# --------------------------------------------------------------------------
# 6. The closure computation (AC-2)
# --------------------------------------------------------------------------

SEAM_NAMES = ("parse_frontmatter", "parse_to_model")


def seam_invocation_closure(files: Iterable[Path], stop: Iterable[FunctionId]) -> set:
    """The FIXPOINT of "package functions that REACH the seam".

    Adjacency is NOT the predicate and cannot return this class: the four typed
    conveniences name neither seam symbol (they reach it through
    parse_markdown_content) and base._load_file reaches it only through
    parse_markdown_file. An adjacency scan returns nine functions containing
    none of those five.

    The walk STOPS at any function another criterion has already dispositioned.
    That stop rule is what makes this terminate and what makes "exactly one
    class" well-defined; without it the walk climbs through load(), resolve()
    and every consumer-facing method in the package.
    """
    stop = set(stop)

    calls: dict = {}
    for path in files:
        tree = _parse(path)
        for fid, func in _iter_functions(path, tree):
            calls[fid] = _called_names(func)

    # name -> the functions defined under that name
    by_name: dict = {}
    for fid in calls:
        by_name.setdefault(fid.name, set()).add(fid)

    closure = {fid for fid, names in calls.items()
               if any(seam in names for seam in SEAM_NAMES)}

    frontier = set(closure)
    while frontier:
        nxt = set()
        for member in frontier:
            if member in stop:
                continue        # dispositioned elsewhere — do not expand
            for caller, names in calls.items():
                if member.name in names and caller not in closure:
                    nxt.add(caller)
        closure |= nxt
        frontier = nxt
    return closure


# --------------------------------------------------------------------------
# 7. parse_frontmatter's exit sites (AC-2)
# --------------------------------------------------------------------------

def parse_frontmatter_exit_sites(files: Iterable[Path]) -> list:
    """Every EXIT site of parse_frontmatter, against POST-FIX source.

    "Return sites" means Return UNION Raise here, and that is forced: the fix
    converts two of the four returns into raises, so keying to Return alone
    would leave two outcome classes with no site at all.

    Sites are NOT in bijection with outcome classes and must not be conflated —
    the empty-fence class has no return of its own and shares the valid-
    frontmatter return. A map keyed by outcome class is red on a CORRECT
    implementation, and the cheap repair drops the unmatched class.
    """
    sites = []
    for path in files:
        tree = _parse(path)
        for fid, func in _iter_functions(path, tree):
            if fid.name != "parse_frontmatter":
                continue
            exits = [n for n in _own_body_nodes(func)
                     if isinstance(n, (ast.Return, ast.Raise))]
            exits.sort(key=lambda n: (n.lineno, n.col_offset))
            for i, _node in enumerate(exits):
                sites.append(SiteId(fid.module, fid.qualname, i))
    return sites


# --------------------------------------------------------------------------
# 8. The non-completed-write universe (AC-5)
# --------------------------------------------------------------------------

# The write paths themselves are DERIVED (a function that commits bytes), which
# is the half that carries the forward-looking property: a sixth silent-False
# writer copy-pasted into a NEW module next month is picked up with no edit
# here. These two are the AC's own second category -- the shared helpers the
# write paths route their fence split and body read through -- and they are
# named because "shared section-read helper" is a semantic property no scan can
# decide. The residue is stated rather than papered over: a NEW shared helper
# added beside them is not discovered by this scan. Its blast radius is bounded
# by the same fact -- a falsy return it invents reaches a caller only through a
# derived write path, whose own sites ARE scanned.
_SHARED_HELPERS = {"_get_body_content", "_split_frontmatter_fence"}


def non_completed_write_sites(files: Iterable[Path]) -> list:
    """Every FALSY RETURN across the package's write paths and shared helpers,
    against POST-FIX source.

    This is the exact predicate that yields the 28-site pre-fix universe:
    `return False`, `return None`, and bare `return` -- the success-shaped
    values a caller cannot tell a failure from. RAISES ARE NOT MEMBERS, and that
    is the point rather than an omission: a site this item moves to the raise
    side LEAVES the universe. So the post-fix universe is not a smaller sample
    of the same thing, it is the residue -- and the property worth asserting is
    that every member of it is a LEGITIMATE no-op, i.e. that nothing
    failure-shaped still reports as one.

    Pre-fix 28 is a baseline, never the answer: this item's own remedy removes
    sites (the four copy-pasted fence splits collapse into one raising helper,
    the structurally-dead split guard is deleted) and its accommodation converts
    another into a completed write.
    """
    sites = []
    for path in files:
        tree = _parse(path)
        for fid, func in _iter_functions(path, tree):
            body = _own_body_nodes(func)
            writes = any(_is_write_call(n) for n in body)
            if not writes and fid.name not in _SHARED_HELPERS:
                continue
            members = [n for n in body
                       if isinstance(n, ast.Return) and _is_falsy_return(n)]
            members.sort(key=lambda n: (n.lineno, n.col_offset))
            for i, _node in enumerate(members):
                sites.append(SiteId(fid.module, fid.qualname, i))
    return sites


def _is_falsy_return(node) -> bool:
    if node.value is None:
        return True
    return isinstance(node.value, ast.Constant) and not node.value.value


# --------------------------------------------------------------------------
# 9. The ast-capability marker (AC-7)
# --------------------------------------------------------------------------

def modules_using_ast(files: Iterable[Path]) -> list:
    """Every USE of the `ast` module, read off PARSED SYNTAX, never source text.

    Capability detection, not shape attribution: three of the six derivations
    share one AST-walk shape and the loose and data-flow predicates differ only
    semantically, so no shape discriminates them. What every copy of a
    syntax-traversing derivation must DO is obtain syntax via `ast` — so that is
    the marker, asserted single-homed to this module.

    Read as SYNTAX because the checking test necessarily carries its planted
    fixtures' source as string literals: a text matcher would match the planter
    and go red on a correct harness. As syntax, a string literal is a Constant
    and is invisible here.

    Three marker forms: an `import ast` alias, a `from ast import ...`, and an
    attribute access on a name bound by either.
    """
    uses = []
    for path in files:
        tree = _parse(path)
        module = module_id(path)

        bound = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == "ast" or alias.name.startswith("ast."):
                        bound.add(alias.asname or alias.name.split(".")[0])
                        uses.append(AstUse(module, alias.asname or alias.name,
                                           node.lineno))
            elif isinstance(node, ast.ImportFrom):
                if node.module == "ast":
                    for alias in node.names:
                        bound.add(alias.asname or alias.name)
                        uses.append(AstUse(module, alias.asname or alias.name,
                                           node.lineno))

        if bound:
            for node in ast.walk(tree):
                if (isinstance(node, ast.Attribute)
                        and isinstance(node.value, ast.Name)
                        and node.value.id in bound):
                    uses.append(AstUse(module, f"{node.value.id}.{node.attr}",
                                       node.lineno))
    return uses


# --------------------------------------------------------------------------
# 10. WI-004's routing wall predicates (Walls A-E)
#
# All five read PARSED SYNTAX, never source text -- the modules_using_ast
# lesson: a text matcher matches the test that plants its own fixtures as
# string literals and goes red on a correct harness.
# --------------------------------------------------------------------------

def _fs_module_bindings(tree) -> tuple:
    """The two provenance maps a file's imports establish.

    Returns (module_bindings, member_bindings):
      module_bindings: local name -> FS_MODULES member, from `import m` /
                       `import m as a`.
      member_bindings: local name -> the ORIGINAL member name, from
                       `from m import n` / `from m import n as a`.

    Provenance is the IMPORT, so a local alias is irrelevant to either map --
    which is what makes `from os import replace as _r; _r(a, b)` resolvable
    while `s.replace("-", "")` is not.
    """
    module_bindings = {}
    member_bindings = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                if root in FS_MODULES:
                    module_bindings[alias.asname or root] = root
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.module.split(".")[0] in FS_MODULES:
                for alias in node.names:
                    member_bindings[alias.asname or alias.name] = alias.name
    return module_bindings, member_bindings


def _write_mode_argument(node):
    """The mode argument of an `open`-shaped call, or None if it is not one.

    Two call forms carry the mode in different positions: `open(p, "w")` is a
    bare-name call whose mode is the SECOND positional argument, while
    `p.open("w")` is an attribute call whose mode is the FIRST. A `mode=`
    keyword beats both.
    """
    for kw in node.keywords:
        if kw.arg == "mode":
            return kw.value
    f = node.func
    if isinstance(f, ast.Name) and f.id == "open":
        return node.args[1] if len(node.args) > 1 else None
    if isinstance(f, ast.Attribute) and f.attr == "open":
        return node.args[0] if node.args else None
    return None


def filesystem_mutation_uses(files: Iterable[Path]) -> list:
    """Wall A. Every USE of a filesystem-MUTATION capability, by four arms.

    (a) attribute call whose attr is a homonym-free Path mutator;
    (b) attribute call on a name bound by an FS_MODULES import, whose attr is in
        either vocabulary -- `os.replace`, `shutil.move`, `tempfile.mkstemp`;
    (c) bare-name call on a name bound by `from <fs-module> import <n>` where the
        ORIGINAL n is in either vocabulary;
    (d) an `open`-shaped call whose mode literal contains w, a, x or +.

    What no arm resolves is `p.replace(q)` on a Path variable: `replace` is the
    one Path mutator whose attribute name collides with a builtin's method, so
    it is provenance-matched only. That blind spot is declared (WI-004 R10) and
    bounded by os_module_attribute_uses, which makes any `os` member outside
    OS_READONLY_NAMES red wherever it is named.
    """
    uses = []
    for path in files:
        tree = _parse(path)
        module = module_id(path)
        module_bindings, member_bindings = _fs_module_bindings(tree)

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            f = node.func

            if isinstance(f, ast.Attribute):
                # (b) module-qualified -- checked before (a) so the reported
                # capability names the module it came through.
                receiver = f.value
                if (isinstance(receiver, ast.Name)
                        and receiver.id in module_bindings
                        and f.attr in (MODULE_MUTATION_NAMES | PATH_MUTATION_NAMES)):
                    uses.append(AstUse(
                        module, f"{module_bindings[receiver.id]}.{f.attr}",
                        node.lineno))
                    continue
                # (a) homonym-free Path mutator, any receiver
                if f.attr in PATH_MUTATION_NAMES:
                    uses.append(AstUse(module, f.attr, node.lineno))
                    continue

            # (c) aliased import of a mutating member
            if isinstance(f, ast.Name) and f.id in member_bindings:
                original = member_bindings[f.id]
                if original in (MODULE_MUTATION_NAMES | PATH_MUTATION_NAMES):
                    uses.append(AstUse(module, original, node.lineno))
                    continue

            # (d) write-mode open
            mode = _write_mode_argument(node)
            if (isinstance(mode, ast.Constant)
                    and isinstance(mode.value, str)
                    and any(c in mode.value for c in "wax+")):
                uses.append(AstUse(module, f'open(mode={mode.value})',
                                   node.lineno))
    return uses


def os_module_attribute_uses(files: Iterable[Path]) -> list:
    """Wall B. Every reach into the `os` module outside OS_READONLY_NAMES,
    IN EITHER ACCESS FORM.

    This is a rule over the ATTRIBUTE, not a list of exempt files: three live
    sites need `os.environ` and all three pass by predicate. The discriminator
    is the MODULE rather than the member, so a name no vocabulary ever
    anticipated -- `os.fchmod` -- is caught with no vocabulary at all.

    The `from os import <n>` arm collects the BINDING, not the call: an unused
    mutator import is still a mutation capability sitting outside the door.

    FILTER PLACEMENT, because the two arms differ and that asymmetry is ruled
    (D10.3, and pinned by D10.6's Table 1): the ATTRIBUTE arm returns every
    `os.<attr>` access and Wall B asserts that everything it returns outside
    `vault_io.py` is in `OS_READONLY_NAMES` -- which is what makes that
    assertion a live, non-vacuous claim against the three `os.environ` reads
    this tree carries. The `ImportFrom` arm filters inside the predicate, per
    D10.3's "where `n` is not in `OS_READONLY_NAMES`".
    """
    uses = []
    for path in files:
        tree = _parse(path)
        module = module_id(path)

        bound = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == "os":
                        bound.add(alias.asname or "os")
            elif isinstance(node, ast.ImportFrom):
                if node.module == "os":
                    for alias in node.names:
                        if alias.name not in OS_READONLY_NAMES:
                            uses.append(AstUse(module, f"os.{alias.name}",
                                               node.lineno))

        if bound:
            for node in ast.walk(tree):
                if (isinstance(node, ast.Attribute)
                        and isinstance(node.value, ast.Name)
                        and node.value.id in bound):
                    uses.append(AstUse(module, f"os.{node.attr}", node.lineno))
    return uses


def module_import_uses(files: Iterable[Path], modules: Iterable[str]) -> list:
    """Wall C. Every IMPORT of one of `modules`, in both statement forms.

    The oracle is the import and not a call: bringing a mutation capability into
    a module is the thing this forbids. `qualname` is always the ORIGINAL module
    name, never the local alias, so a caller can compare the returned module set
    against the set it asked about.
    """
    wanted = frozenset(modules)
    uses = []
    for path in files:
        tree = _parse(path)
        module = module_id(path)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root = alias.name.split(".")[0]
                    if root in wanted:
                        uses.append(AstUse(module, root, node.lineno))
            elif isinstance(node, ast.ImportFrom):
                if node.module and node.module.split(".")[0] in wanted:
                    uses.append(AstUse(module, node.module.split(".")[0],
                                       node.lineno))
    return uses


def functions_calling(files: Iterable[Path], name: str) -> set:
    """Wall D. Every function whose OWN body calls `name`.

    Built on `_called_names` / `_own_body_nodes`, so `f(...)` and `x.f(...)`
    both count and a call moved into a nested helper does NOT count as the
    enclosing function's -- a loader that hides its recording in a closure is
    deliberately red.
    """
    found = set()
    for path in files:
        tree = _parse(path)
        for fid, func in _iter_functions(path, tree):
            if name in _called_names(func):
                found.add(fid)
    return found


def falsy_returns_in(files: Iterable[Path], names: Iterable[str]) -> list:
    """Wall E. Every explicit FALSY return in the own body of a function whose
    last dotted qualname segment is in `names`.

    Shares `_own_body_nodes` and `_is_falsy_return` with
    `non_completed_write_sites` -- one rule over two universes, never a second
    copy. That universe is needed because `non_completed_write_sites`' own gate
    is `_is_write_call`, which no vault_io function enters (the module commits
    through a file descriptor), so the door contract asserted against it would
    have been vacuous.

    An implicit fall-off-the-end is not an `ast.Return` node and is invisible
    here by construction. That limit is declared rather than papered over.
    """
    wanted = frozenset(names)
    sites = []
    for path in files:
        tree = _parse(path)
        for fid, func in _iter_functions(path, tree):
            if fid.name not in wanted:
                continue
            members = [n for n in _own_body_nodes(func)
                       if isinstance(n, ast.Return) and _is_falsy_return(n)]
            members.sort(key=lambda n: (n.lineno, n.col_offset))
            for i, _node in enumerate(members):
                sites.append(SiteId(fid.module, fid.qualname, i))
    return sites
