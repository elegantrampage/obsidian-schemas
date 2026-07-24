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
    """A call that commits bytes to the filesystem."""
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr in {"write_text", "write_bytes"}
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
