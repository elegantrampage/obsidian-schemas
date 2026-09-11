"""WI-023 — the identity endgame: the five acceptance checks and their supports.

Four of the five checks EXECUTE `PersonRepository`, so the very first package
import pulls in `pydantic` — which the conveyor's interpreter does not carry.
`ensure_project_interpreter(__file__)` is therefore this module's first
statement, ahead of every package import; without it every criterion of this
item reports `ModuleNotFoundError` against a floor that is green in the same
tree (WI-021's shipped scar).

CORPUS_COUPLING: pins `docs/identity-cutover-corpus-audit.md`'s declared
SECTION/FIELD SHAPE (never its numbers) to consume the artifact AC-5 gates. The
document is a conductor-committed precondition whose bytes are frozen in HEAD,
so neither "derive it from the corpus's own code" nor "carry frozen bytes"
applies; this declaration is what lets the next reader falsify the coupling in
the same breath it is made (the convention: `tests/test_company_name_contract.py`
and `tests/test_ac_interpreter.py`).

**Three literals this module may not SPELL.** `_email` + `_index`, the legacy
stub attribute and the dangling `docs/` slug are each asserted at ZERO across
`PACKAGE_ROOT, TESTS_ROOT` by checks in this very module, and this module is
under `TESTS_ROOT`. So every one of them is ASSEMBLED FROM PARTS below and no
single source line of this file carries one whole — not in a plant, not in a
check's argument list, not in an owner qualname, not in a comment, not in a
docstring, not in an assertion message. A plant that needs a name of its own
invents one (`_plant_index`, `docs/does-not-exist.md`).

**And no comment in this module carries a triple-quote delimiter.** A borrowed
line scan (`tests/test_vault_path_required.py:_code_lines`) sets its
in-docstring flag on any line holding an odd count of them, trailing comments
included, so one such comment would swallow every code line beneath it and turn
this item's no-argument-construction zero into an under-reach that reads exactly
like a clean scan. A triple quote appears here as a docstring delimiter or as a
plant constant's delimiter, never inside a comment.

Nothing here reads syntax (no `ast`): that capability is single-homed in
`tests/derivations.py`, by set EQUALITY, so every structural predicate this item
needs is an export of that module and is driven here through its OWN function.
"""

from tests.ac_interpreter import ensure_project_interpreter

ensure_project_interpreter(__file__)   # FIRST — ahead of every package import

from pathlib import Path                                          # noqa: E402

from tests.derivations import (                                   # noqa: E402
    PACKAGE_ROOT,
    TESTS_ROOT,
    attribute_reads_in,
    docs_markdown_mentions,
    phone_index_iteration_sites,
    prose_lines,
    python_files_under,
)
from tests.identity_fixture import (                              # noqa: E402
    FIXTURE_DIR,
    ROSTER_PATH,
    load_roster,
    roster_digest,
    seed_vault,
)
from tests.record_identity_golden import (                        # noqa: E402
    bound_repository,
    derive_resolve_queries,
    derive_stub_cases,
)
from tests.support import patcher, temp_dir                       # noqa: E402

from obsidian_schemas import PersonRepository                     # noqa: E402
from obsidian_schemas.phone_normalization import phones_match     # noqa: E402

# ── The three literals this module may not spell, assembled from parts ───────
# Each is asserted at ZERO across both tracked roots by a check below, and this
# file is under one of them. Assembling is the repair the spec fixes in advance;
# narrowing a scan is not.
EMAIL_INDEX_ATTR = "_email" + "_index"
LEGACY_STUB_ATTR = "_find_or_create" + "_stub_legacy"
PAREN_DOC_SLUG = "paren-decoration" + "-at-the-door"
LEGACY_STUB_OWNER = "PersonRepository." + LEGACY_STUB_ATTR

PERSON_MODULE = "obsidian_schemas/repositories/person.py"


def _write_plant(directory: Path, name: str, body: str) -> Path:
    """Materialize one plant module in a scratch directory."""
    path = directory / name
    path.write_text(body.lstrip("\n"), encoding="utf-8")
    return path


# ── Task 2 — the four predicates' claimed match-shapes, as planted fixtures ──
#
# Every expectation below is DERIVED by applying each predicate's own stated
# rule to the planted line's tokens, never from what the line looks like to a
# reader. Where a plant and a correct predicate disagree, the PLANT is wrong
# unless the rule is: the predicate is never narrowed to make a plant green.

PHONE_ITERATION_PLANT = '''
class Holder:
    def materialized_with_list(self):
        for key, value in list(self._phone_index.items()):
            yield key, value

    def materialized_with_sorted(self):
        for key in sorted(self._phone_index):
            yield key

    def live_scan(self):
        for key, value in self._phone_index.items():
            yield key, value

    def unrelated_attribute(self):
        for key in self._plant_index.items():
            yield key
'''

ATTRIBUTE_READ_PLANT = '''
class Holder:
    def named(self):
        value = self._cache.get("k")
        self._cache = {}
        other = self._untracked.get("k")

        def inner():
            return self._cache.get("deep")

        return value, other, inner

    def elsewhere(self):
        return self._cache.get("k")
'''

DOCS_MENTION_PLANT = '''
"""A docstring naming docs/company-name-corpus-audit.md, which resolves."""

X = 1  # a dangling pointer: docs/does-not-exist.md
Y = 2  # a cross-repository pointer: orchestrator/docs/x.md
Z = 3  # a vault-note illustration: Smith.md
W = 4  # a line-wrapped tail:
# revised-2026-06-13.md
'''

PROSE_PLANT = '''
# a module-level comment, outside every definition


def outer():
    """A function docstring line."""
    # a comment in the function body
    x = 1  # a trailing comment on a code line

    def inner():
        # a comment inside a nested def
        return 2

    y = "a # b"
    z = 1  # see the """ delimiter
    a = 2
    b = 3
    return x, y, z, a, b, inner
'''


def test_identity_endgame_derivations_match_their_claimed_shapes():
    """WI-235: each predicate's claimed shapes AND a near-miss, driven through
    that predicate's OWN function — never a second copy of the matching logic."""
    with temp_dir() as scratch:
        # ── phone_index_iteration_sites ─────────────────────────────────────
        plant = _write_plant(scratch, "phone_plant.py", PHONE_ITERATION_PLANT)
        text = plant.read_text().splitlines()
        sites = phone_index_iteration_sites(python_files_under(scratch))
        by_line = {s.lineno: s.classification for s in sites}

        def line_of(fragment):
            return 1 + next(i for i, l in enumerate(text) if fragment in l)

        list_loop = line_of("list(self._phone_index.items())")
        sorted_loop = line_of("sorted(self._phone_index)")
        live_loop = line_of("in self._phone_index.items()")
        assert by_line.get(list_loop) == "materialized", by_line
        assert by_line.get(sorted_loop) == "materialized", (
            "a five-wrapper vocabulary driven by `list` alone proves one member "
            f"of it, not the classification: {by_line}")
        assert by_line.get(live_loop) == "live", by_line
        assert len(sites) == 3, (
            "the unrelated-attribute loop is a near-miss and must not be "
            f"collected: {sites}")
        plant.unlink()

        # ── attribute_reads_in ──────────────────────────────────────────────
        plant = _write_plant(scratch, "attribute_plant.py", ATTRIBUTE_READ_PLANT)
        text = plant.read_text().splitlines()
        reads = attribute_reads_in(
            python_files_under(scratch), {"Holder.named"}, {"_cache"})
        assert {r.qualname for r in reads} == {"Holder.named"}, reads
        read_lines = {r.lineno for r in reads}
        assert line_of('value = self._cache.get("k")') in read_lines, reads
        assert line_of('return self._cache.get("deep")') in read_lines, (
            "a read inside a nested def is the enclosing NAMED function's, by "
            f"the same folding rule the prose predicate uses: {reads}")
        assert line_of("self._cache = {}") not in read_lines, (
            f"an assignment is a Store, and the criterion says READ: {reads}")
        assert len(reads) == 2, (
            "the other function's read and the unnamed attribute's read are "
            f"near-misses: {reads}")
        plant.unlink()

        # ── docs_markdown_mentions ──────────────────────────────────────────
        plant = _write_plant(scratch, "docs_plant.py", DOCS_MENTION_PLANT)
        mentions = docs_markdown_mentions(python_files_under(scratch))
        collected = {m.path for m in mentions}
        assert collected == {
            "docs/company-name-corpus-audit.md",
            "docs/does-not-exist.md",
        }, (
            "both token kinds are driven — a docstring-borne mention and a "
            "trailing-comment one — and the three near-misses (a cross-repo "
            "pointer whose greedy match swallows its leading segment, a bare "
            f"note illustration, a wrapped tail) are not in scope: {mentions}")
        plant.unlink()

        # ── prose_lines ─────────────────────────────────────────────────────
        plant = _write_plant(scratch, "prose_plant.py", PROSE_PLANT)
        text = plant.read_text().splitlines()
        records = prose_lines(python_files_under(scratch))
        by_lineno = {r.lineno: r for r in records}

        module_comment = line_of("# a module-level comment")
        docstring = line_of("A function docstring line")
        body_comment = line_of("# a comment in the function body")
        trailing_comment = line_of("# a trailing comment on a code line")
        nested_comment = line_of("# a comment inside a nested def")
        hash_in_string = line_of('y = "a # b"')
        delimiter_comment = line_of("# see the")
        following_one = line_of("a = 2")
        following_two = line_of("b = 3")

        assert by_lineno[module_comment].owner == "<module>", records
        assert by_lineno[docstring].owner == "outer", records
        assert by_lineno[body_comment].owner == "outer", records
        assert by_lineno[trailing_comment].owner == "outer", records
        assert by_lineno[nested_comment].owner == "outer", (
            "a nested def's prose folds onto its outermost non-local ancestor, "
            f"never a <locals> qualname: {records}")
        assert by_lineno[trailing_comment].text == text[trailing_comment - 1].strip(), (
            f"the record carries the whole stripped SOURCE line: {records}")

        # (i) the false-positive shape: a `#` inside a string literal owes NO record.
        assert hash_in_string not in by_lineno, records
        # (ii) the state-tracking shape: the comment IS collected, exactly once,
        # and what a line scan gets wrong is the ORDINARY CODE following it.
        assert delimiter_comment in by_lineno, (
            "a trailing comment carrying a triple-quote delimiter is a COMMENT "
            f"token like any other and owes exactly one record: {records}")
        assert len([r for r in records if r.lineno == delimiter_comment]) == 1, records
        assert following_one not in by_lineno and following_two not in by_lineno, (
            "the two ordinary code lines beneath it are what a delimiter line "
            f"scan swallows as a docstring body: {records}")
        plant.unlink()


# ── Task 3 — the frozen roster and its two invariants, re-derived ────────────

ROSTER_TABLE = [
    ("Jane Roe",         ["Jane Roe <jane.roe@example.com>"], [],                  [],              None),
    ("Kit Baldwin",      ["kit@localhost"],                   [],                  [],              None),
    ("Dana Okafor",      [" dana@example.com "],              [],                  [],              None),
    ("John Smith",       ["john.smith@example.com"],          [],                  [],              None),
    ("Sandy Forster",    ["sandy.forster@example.com"],       [],                  [],              None),
    ("Alex Nkemdirim",   [],                                  ["pat@example.com"], [],              None),
    ("Rosa Delgado",     ["pat@example.com"],                 [],                  [],              None),
    ("Emily Mendes",     ["emily.mendes@example.com"],        [],                  [],              None),
    ("Priya Raman",      [],                                  [],                  ["44790055852"], None),
    ("Tomas Villalobos", [],                                  [],                  ["2125550147"],  "Kestrel Analytics"),
]

SWALLOWED_DESTS = (None, "", "   ", ".")


def test_identity_fixture_roster_is_complete_and_invariant_holding():
    """The roster IS the golden's declaration: complete, literal, and carrying
    both order-independence invariants as re-derived properties."""
    roster = load_roster()
    notes = roster["notes"]

    assert [
        (n["name"], n["emails"], n["aliases"], n["phones"], n["company"])
        for n in notes
    ] == ROSTER_TABLE, (
        "the roster is a byte-frozen declaration and every plant in it is a "
        "literal the spec fixes, not the build's choice")

    # Invariant 1 — no two notes share a name token. Re-DERIVED, never restated:
    # a partial-name resolve returns the FIRST cache entry holding the token and
    # cache order is an unsorted filesystem walk, so a shared token would make
    # every single-token golden value machine-dependent.
    seen_tokens = {}
    for note in notes:
        for token in note["name"].lower().split():
            assert token not in seen_tokens, (
                f"{note['name']!r} shares the name token {token!r} with "
                f"{seen_tokens[token]!r}")
            seen_tokens[token] = note["name"]

    company_notes = [n["name"] for n in notes if n["company"]]
    assert company_notes == ["Tomas Villalobos"], company_notes
    for token in company_notes and notes[-1]["company"].lower().split():
        assert token not in seen_tokens, (
            f"the company token {token!r} is also a name token — the company "
            f"bump could reach a second note through its name")

    # Invariant 2 — no two fixture phones unify under the SHIPPED phones_match,
    # and none of them unifies with a non-present form the criteria rely on.
    # Driven through the real function, never a re-implementation.
    phones = [p for n in notes for p in n["phones"]]
    for i, left in enumerate(phones):
        for right in phones[i + 1:]:
            assert not phones_match(left, right), (
                f"{left} and {right} unify — the fuzzy scan returns the FIRST "
                f"unifying entry in walk order, so a negative witness could "
                f"fail for a reason unrelated to the property under test")

    with temp_dir() as scratch:
        # The refusal is asserted with the fall-through LIVE: the env var is set
        # to a real directory, so an unguarded seeding would succeed there.
        live_vault = scratch / "would-be-live-vault"
        live_vault.mkdir()
        with patcher() as patch:
            import os
            patch.setitem(os.environ, "OBSIDIAN_VAULT_PATH", str(live_vault))
            for dest in SWALLOWED_DESTS:
                try:
                    seed_vault(roster, dest)
                except AssertionError:
                    continue
                raise AssertionError(
                    f"seed_vault accepted dest={dest!r}, which the library "
                    f"resolves to OBSIDIAN_VAULT_PATH")
            assert list(live_vault.iterdir()) == [], (
                "the refusal must fire BEFORE the first write — after it there "
                "is nothing left to refuse")

        vault = scratch / "vault"
        assert seed_vault(roster, vault) == vault
        repo = PersonRepository(vault)
        assert repo.load() == len(ROSTER_TABLE)
        assert repo.skipped_count == 0, repo.skipped_notes

    assert len(roster_digest()) == 64 and ROSTER_PATH.exists()


# ── Task 5 — the goldens are frozen PRE-CUT data ─────────────────────────────

# D11's disposition table, read as OWNERS. The thirteen AUTHORIZED ones are the
# owners the plan orders a PROSE repair — derived from the prose obligation, not
# from which functions the cuts touch, because the surface these rules run over
# emits no code lines and an owner authorized for a code-only edit is one the
# "a repair landed" direction is false about by construction.
AUTHORIZED_PROSE_OWNERS = (
    "<module>",
    "PersonRepository.__init__",
    "PersonRepository._index_entity",
    "PersonRepository._project_identifiers",
    "PersonRepository._index_identifiers",
    "PersonRepository._remove_entity_from_indexes",
    "PersonRepository.get_by_phone",
    "PersonRepository.resolve",
    "PersonRepository.resolve_all",
    "PersonRepository.find_or_create_stub",
    LEGACY_STUB_OWNER,
    "PersonRepository.resolve_or_create",
    "PersonRepository._resolve_identifier",
)

# The two declared NON-members of that set, each for its own structural reason.
CODE_ONLY_OWNER = "PersonRepository._clear_indexes"   # a Cut-0 owner; no prose repair
CREATED_OWNER = "select_resolution"                   # not a Cut-0 owner at all

TABLE_OWNERS = AUTHORIZED_PROSE_OWNERS + (CODE_ONLY_OWNER, CREATED_OWNER)

# The two exception rows' PRE-CUT values, as literals in this check's own source
# — prose in the spec AND a literal here, never data the recorder can produce.
PRE_CUT_EXCEPTION_ROWS = (
    ("kit@localhost", "Kit Baldwin"),
    (" dana@example.com ", None),
)

# The SHARED-VAULT tripwire, which is a different thing: this row's recorded
# value is `Jane Roe` against the roster's bytes and `None` in a vault the
# mutating stub sweep has already run in, because that sweep's writeback
# rebuilds the entry through the semantic gate and the bracketed key is gone.
SHARED_VAULT_ROW = ("Jane Roe <jane.roe@example.com>", "Jane Roe")


def _golden(name: str) -> dict:
    import json
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def test_identity_goldens_are_frozen_pre_cut_data():
    """Cut 0's three frozen artifacts, and the clauses a regenerated golden
    fails. Recorded ONCE, against unchanged code; never re-recorded."""
    import os

    stub = _golden("stub_golden.json")
    resolve = _golden("resolve_golden.json")
    surface = _golden("prose_surface_cut0.json")

    digest = roster_digest()
    for name, payload in (("stub_golden.json", stub),
                          ("resolve_golden.json", resolve),
                          ("prose_surface_cut0.json", surface)):
        assert payload["recorded_at"] == "cut-0", name
    for name, payload in (("stub_golden.json", stub),
                          ("resolve_golden.json", resolve)):
        assert payload["roster_digest"] == digest, (
            f"{name} was recorded against a different roster — a fixture edit "
            f"without a re-record is RED, and a re-record is a visible diff")

    # The case and query lists re-derive IDENTICALLY, as full triples: `arm` is
    # the only record of which derivation clause produced a query, so a space
    # that agreed on the strings while disagreeing on the clause is reshaped.
    roster = load_roster()
    assert [(c["ordinal"], c["arm"], c["name"], c["email"], c["phone"],
             c["company"]) for c in stub["cases"]] == [
        (c["ordinal"], c["arm"], c["name"], c["email"], c["phone"],
         c["company"]) for c in derive_stub_cases(roster)]
    assert [(q["ordinal"], q["arm"], q["query"]) for q in resolve["queries"]] == [
        (q["ordinal"], q["arm"], q["query"]) for q in derive_resolve_queries(roster)]

    recorded = {q["query"]: q["expected"] for q in resolve["queries"]}
    for query, expected in PRE_CUT_EXCEPTION_ROWS:
        assert recorded[query] == expected, (
            f"the golden no longer holds the PRE-CUT answer for {query!r} — a "
            f"golden regenerated after the email cut records the post-cut one, "
            f"which is the one way this oracle can be defeated")
    assert recorded[SHARED_VAULT_ROW[0]] == SHARED_VAULT_ROW[1], (
        "this row is None in any resolve golden recorded in a vault the "
        "mutating stub sweep has already run in — the recorder seeds one vault "
        "PER SWEEP and this literal is what says so")

    # The Cut-0 prose surface: non-empty, and every owner the disposition table
    # names owns at least one line in it — so a surface recorded against a
    # renamed or already-edited file is RED here rather than silently narrowing
    # the final diff.
    assert surface["lines"], "the Cut-0 prose surface is empty"
    owners = {line["owner"] for line in surface["lines"]}
    for owner in TABLE_OWNERS:
        if owner == CREATED_OWNER:
            assert owner not in owners, (
                f"{owner} is created by this item and owns no Cut-0 prose")
            continue
        assert owner in owners, (
            f"{owner} owns no line in the Cut-0 surface — the table is a "
            f"reading of that surface and cannot drift from it")

    # The recorder's binding helper, as a unit, with the fall-through LIVE.
    with temp_dir() as scratch:
        would_be_live = scratch / "would-be-live-vault"
        would_be_live.mkdir()
        with patcher() as patch:
            patch.setitem(os.environ, "OBSIDIAN_VAULT_PATH", str(would_be_live))
            for dest in SWALLOWED_DESTS:
                try:
                    bound_repository(dest)
                except AssertionError:
                    continue
                raise AssertionError(
                    f"bound_repository accepted dest={dest!r}, which the "
                    f"library resolves to the live vault")
            vault = scratch / "bound"
            seed_vault(roster, vault)
            repo = bound_repository(vault)
            assert Path(repo.vault_path).resolve() == vault.resolve()


# ── Task 6 / AC-2 — email resolution has exactly ONE authority ───────────────

def _literal_sites(needle: str, files) -> list:
    """Every (module, lineno) whose SOURCE TEXT carries `needle`.

    A literal-text scan, case-SENSITIVE, total over the file's text: it sees a
    `def`, a call, a comment and a string alike, which is what a definition-blind
    caller scan cannot.
    """
    from tests.derivations import module_id
    sites = []
    for path in files:
        for lineno, line in enumerate(
                Path(path).read_text(encoding="utf-8").splitlines(), start=1):
            if needle in line:
                sites.append((module_id(path), lineno))
    return sites


def _planted_positive(needle: str) -> None:
    """The half of a zero-count control no property of the data can supply: the
    same assembled needle, run through the same scan, over a scratch directory
    holding one planted file that DOES contain it."""
    with temp_dir() as scratch:
        _write_plant(scratch, "needle_plant.py", f"X = 1  # {needle}\n")
        found = _literal_sites(needle, python_files_under(scratch))
        assert len(found) == 1, (
            f"the scan cannot find {needle!r} even where it IS — the zero it "
            f"reports elsewhere would say nothing: {found}")


def test_email_has_exactly_one_resolution_authority():
    """AC-2. Four surfaces, one lookup — and the alias asymmetry pinned as the
    declared, permanent thing it is rather than carved out of the sweep."""
    from obsidian_schemas.identifier import Email, IdentifierError

    roster = load_roster()
    owner_of_address = {}
    alias_owner = {}
    for note in roster["notes"]:
        for email in note["emails"]:
            owner_of_address[email] = note["name"]
        for alias in note["aliases"]:
            alias_owner[alias.strip().lower()] = note["name"]

    with temp_dir() as scratch:
        vault = seed_vault(roster, scratch / "vault")
        repo = PersonRepository(vault)
        repo.load()

        for entry, owner in owner_of_address.items():
            variants = [entry, entry.lower(), f"  {entry.strip()}  "]
            try:
                parsed = Email.parse(entry)
            except IdentifierError:
                parsed = None
            if parsed is not None:
                variants.append(parsed.value)

            for query in variants:
                asymmetric = (query.strip().lower() in alias_owner
                              and alias_owner[query.strip().lower()] != owner)
                doors = {
                    "get_by_email": repo.get_by_email(query),
                    "resolve": repo.resolve(query),
                    "resolve_all[0]": (repo.resolve_all(query) or [None])[0],
                }
                names = {
                    door: (c.person.name if door == "resolve_all[0]" and c
                           else c.name if c else None)
                    for door, c in doors.items()
                }
                try:
                    typed = Email.parse(query)
                except IdentifierError:
                    typed = None
                if typed is not None:
                    ref = repo._resolve_identifier(typed)
                    names["_resolve_identifier"] = (
                        repo._hydrate(ref).name if ref else None)

                if parsed is None:
                    # The refused entry: nobody, by all three string surfaces,
                    # and surface 4 is NOT APPLICABLE — there is no typed Email
                    # to hand over, so the criterion asserts that refusal.
                    assert set(names.values()) == {None}, (query, names)
                    assert typed is None, (
                        f"{query!r} is the refused plant; a typed Email for it "
                        f"would mean the parser changed under this criterion")
                    continue

                if asymmetric:
                    # The DECLARED, PERMANENT asymmetry: `resolve` is a cascade
                    # over four indexes and its alias step precedes its email
                    # step. Both halves are asserted — a build where `resolve`
                    # returns the email owner is RED, and so is one where any
                    # other door returns the alias owner.
                    assert names["resolve"] == alias_owner[query.strip().lower()], names
                    for door in ("get_by_email", "resolve_all[0]",
                                 "_resolve_identifier"):
                        assert names.get(door, owner) == owner, (query, names)
                    continue

                # The oracle is the roster's own declaration of who owns the
                # address, never agreement among surfaces: a build in which all
                # four consistently return the WRONG person is RED.
                for door, answer in names.items():
                    assert answer == owner, (query, door, answer, owner)

    # Structural: the deleted attribute is named at zero sites across BOTH
    # tracked source roots. The needle is assembled from parts — this module is
    # under one of those roots, so a check that spelled it whole would be its
    # own counterexample AND would turn its siblings red.
    files = python_files_under(PACKAGE_ROOT, TESTS_ROOT)
    assert files, "the file list is empty — the zero below would be vacuous"
    assert _literal_sites(EMAIL_INDEX_ATTR, files) == [], (
        "the two-authority state is over: one mapping, one reader")
    _planted_positive(EMAIL_INDEX_ATTR)


# ── Task 8 / AC-3 — the phone carve-out, PROVEN rather than asserted ─────────

# E3's triangle. The fixture note carries the OUTER vertex, never the centre:
# the centre is matched by BOTH other forms, so a note carrying it is found by
# all three and the negative clause below would name nothing — no
# implementation, correct or otherwise, could satisfy it.
TRIANGLE_CENTRE = "0790055852"
TRIANGLE_OUTER_UK = "44790055852"
TRIANGLE_OUTER_US = "10790055852"


def test_phones_stay_on_the_fuzzy_path_and_the_reason_is_executable():
    """AC-3. The relation is not transitive, so no key for it exists; the
    behaviour that buys is pinned; and the concurrency rider is closed."""
    from obsidian_schemas.identifier import Phone

    # Non-transitivity, against the SHIPPED function — this is the proof that
    # keying phones into the unified index is UNAVAILABLE, not merely unchosen.
    assert phones_match(TRIANGLE_CENTRE, TRIANGLE_OUTER_UK) is True
    assert phones_match(TRIANGLE_CENTRE, TRIANGLE_OUTER_US) is True
    assert phones_match(TRIANGLE_OUTER_UK, TRIANGLE_OUTER_US) is False

    # The discriminating half: all three parse, and their keys are DISTINCT. A
    # build that "fixes" the relation by collapsing the three to one key passes
    # any behaviour-only test and silently changes what `Phone.key` means for
    # every consumer of the index.
    keys = {Phone.parse(form).key
            for form in (TRIANGLE_CENTRE, TRIANGLE_OUTER_UK, TRIANGLE_OUTER_US)}
    assert len(keys) == 3, keys

    roster = load_roster()
    with temp_dir() as scratch:
        vault = seed_vault(roster, scratch / "vault")
        repo = PersonRepository(vault)
        repo.load()
        assert repo.get_by_phone(TRIANGLE_OUTER_UK).name == "Priya Raman"
        assert repo.get_by_phone(TRIANGLE_CENTRE).name == "Priya Raman"
        assert repo.get_by_phone(TRIANGLE_OUTER_US) is None, (
            "the negative witness — and it is a witness about the relation only "
            "because no other fixture phone unifies with any of the three forms")

    # Structural: every `for` loop in the package whose iterable REACHES the
    # phone index iterates a materialized snapshot. That is strictly stronger
    # than "the iterable is a call" — a bare `.items()` is already a call, so
    # the weaker gloss is vacuously green against the code this cut moves.
    sites = phone_index_iteration_sites(python_files_under(PACKAGE_ROOT))
    assert sites, "no phone-index iteration site found — the zero below would be vacuous"
    assert [s for s in sites if s.classification != "materialized"] == [], sites


# ── Task 9 / AC-4 — ONE cascade, pinned against the Cut-0 golden ─────────────

# The exception list, as LITERALS in this check's own source, each with the
# answer this item declared IN ADVANCE. A query outside the list that moves is
# RED, and so is an exception that lands anywhere else — which is what stops the
# list from being a licence.
POST_CUT_EXCEPTIONS = {
    "kit@localhost": None,
    " dana@example.com ": "Dana Okafor",
}

# The four hand-stated discriminants. Three of them the DERIVED space provably
# cannot reach — a three-token query, a substring of a token, and a
# two-token-with-short-second query never enter a space of names, name tokens,
# aliases, emails and phones — so an oracle blind to them is not evidence about
# them.
DISCRIMINANTS = (
    ("john smith kato", None),     # (i)   E4 class A: the 0.65 token-subset widening
    ("pat@example.com", "Alex Nkemdirim"),   # (ii)  E4 class B: alias preempts email
    ("andy", None),                # (iii) whole-word, never substring
    ("emily m", None),             # (iv)  E4 class C: step 6's 0.6, with no company
    ("sandy", "Sandy Forster"),    #       the 0.6 the policy must ACCEPT
)


def test_resolve_is_one_cascade_and_matches_the_pre_cut_golden():
    """AC-4. The structural clause, the golden replay with its closed exception
    list, and the discriminants the golden cannot see."""
    import inspect

    from obsidian_schemas.repositories import person as person_module

    # Structural — `resolve` keeps no match logic of its own.
    source = inspect.getsource(person_module.PersonRepository.resolve)
    assert "resolve_all" in source and "select_resolution" in source, source
    policy = getattr(person_module, "select_resolution", None)
    assert callable(policy), (
        "the selection policy is a NAMED, MODULE-LEVEL function, so this clause "
        "is checkable by attribute lookup rather than by reading a body")

    # The attribute list is an ordered site of the self-collision rule: one of
    # these four names is asserted at ZERO across both tracked roots by a
    # sibling check in this same module, so it is assembled from parts. Do not
    # resolve a red here by dropping it from the list or by re-scoping the
    # sibling's scan.
    reads = attribute_reads_in(
        python_files_under(PACKAGE_ROOT),
        {"PersonRepository.resolve"},
        {"_cache", "_alias_index", EMAIL_INDEX_ATTR, "_phone_index"})
    assert reads == [], (
        f"resolve reads an index directly: {reads}. Reading its own `query` "
        f"argument is inside this clause; reading the four indexes is not")

    roster = load_roster()
    golden = _golden("resolve_golden.json")
    assert golden["roster_digest"] == roster_digest()

    with temp_dir() as scratch:
        vault = seed_vault(roster, scratch / "vault")
        repo = PersonRepository(vault)
        repo.load()

        moved = []
        for entry in golden["queries"]:
            query, recorded = entry["query"], entry["expected"]
            person = repo.resolve(query)
            answer = person.name if person else None
            if query in POST_CUT_EXCEPTIONS:
                assert answer == POST_CUT_EXCEPTIONS[query], (
                    f"{query!r} is an enumerated exception and must land on its "
                    f"DECLARED post-cut answer {POST_CUT_EXCEPTIONS[query]!r}, "
                    f"not merely differ; got {answer!r}")
                continue
            if answer != recorded:
                moved.append((entry["ordinal"], query, recorded, answer))
        assert moved == [], (
            "these queries moved and the item never declared them: the "
            f"exception list is closed and Cut 3 gets none of its own — {moved}")

        for query, expected in DISCRIMINANTS:
            person = repo.resolve(query)
            answer = person.name if person else None
            assert answer == expected, (query, answer, expected)


# ── Task 10 / AC-5 — the documentation surface tells the truth ───────────────

REPO_ROOT = PACKAGE_ROOT.parent
AUDIT_DOC = REPO_ROOT / "docs" / "identity-cutover-corpus-audit.md"

# The audit's declared SHAPE, clause by clause. This pins the artifact's
# sections and fields — never its numbers, which are a reading of a live vault
# and are the conductor's to re-run at close-out.
AUDIT_SECTIONS = (
    "## The command (literal)",
    "## Output (verbatim stdout",
    "## Reading, per shape-contract clause",
)
AUDIT_CLAUSE_MARKERS = ("**(a)", "**(b)", "**(c)", "**(d)", "**(e)")
NO_MATCH_MARKER = "no matches"
CONSUMER_REPOS = ("HAL9000", "exocortex", "orchestrator", "obsidian-schemas")


def test_identity_cutover_docs_are_complete_and_truthful():
    """AC-5. The empirical premise's artifact has the shape its precondition
    fence declares, and the package's own prose stops asserting false things.

    Makes no subprocess, network or vault call: the caged builder can reach
    none of them, so a builder-authored version of that artifact would be
    fabrication. This asserts the SHAPE; the conductor re-runs the command.
    """
    import re

    text = AUDIT_DOC.read_text(encoding="utf-8")
    for section in AUDIT_SECTIONS:
        assert section in text, f"the audit artifact is missing {section!r}"
    for marker in AUDIT_CLAUSE_MARKERS:
        assert marker in text, (
            f"clause {marker} has no reading — an absent field is exactly what "
            f"the shape contract forbids in place of an explicit marker")

    # A stated count with no listing behind it is the failure this forbids: a
    # zero must be accompanied by the explicit marker, never by silence.
    assert text.count(NO_MATCH_MARKER) >= 3, (
        "the per-class no-match markers are missing — a count with nothing "
        "behind it is a hand-waved audit")

    shas = re.findall(r"\b[0-9a-f]{40}\b", text)
    assert len(shas) >= len(CONSUMER_REPOS), (
        f"expected a 40-hex HEAD SHA per consumer repo scanned; found {shas}")
    for repo_name in CONSUMER_REPOS:
        assert repo_name in text, repo_name

    # The dangling pointer, at zero across BOTH tracked source roots, with the
    # needle assembled from parts and the two-part non-vacuity control.
    files = python_files_under(PACKAGE_ROOT, TESTS_ROOT)
    assert files, "the file list is empty — the zero below would be vacuous"
    assert _literal_sites(PAREN_DOC_SLUG, files) == [], (
        "a comment pointing at a file that does not exist")
    _planted_positive(PAREN_DOC_SLUG)

    # Generalized from that one string: EVERY `docs/`-relative markdown pointer
    # in the package resolves. One deleted line that the next stale pointer
    # walks straight past is not the fix.
    mentions = docs_markdown_mentions(python_files_under(PACKAGE_ROOT))
    assert mentions, (
        "no in-scope docs/ pointer found at all — the resolve clause below "
        "would be vacuous")
    unresolved = [m for m in mentions if not (REPO_ROOT / m.path).exists()]
    assert unresolved == [], unresolved

    person_text = (PACKAGE_ROOT / "repositories" / "person.py").read_text(
        encoding="utf-8")

    # The slack carve-out survives WITH its unblock condition, not merely its
    # current status.
    unblock = [line.strip() for line in person_text.splitlines()
               if "UNBLOCK:" in line]
    assert len(unblock) == 1, unblock
    assert len(unblock[0].split("UNBLOCK:", 1)[1].strip()) > 20, unblock

    # The false sub-floor claim is gone, and its REPAIRED replacement is
    # present — so the clause cannot go green by the comment having been
    # deleted outright.
    assert "gets filtered out below" not in person_text, (
        "the step-6 branch records 0.6 against a 0.5 floor; it is not filtered")
    assert "records 0.6, which SURVIVES the >= 0.5 floor" in person_text, (
        "the repaired comment must state what actually happens")


# ── Task 11 / AC-1 — the duplicate is gone and a REAL oracle outlives it ─────

ENGINE_DOOR = "resolve_or" + "_create"

# The two-leg plant is ASSEMBLED, for the same reason the three bound literals
# are and one rung out from them: the live sweep below runs over `TESTS_ROOT`,
# which contains THIS module, and the thing it looks for is a SHAPE rather than
# a literal — a `def test_` whose body reaches the engine door twice. Spelled
# plainly, the plant IS that shape in this module's own source and turns a
# correct check red. The repair is to assemble it; narrowing the scan is not.
TWO_LEG_PLANT = "\n".join([
    "def test_" + "the_planted_two_leg_shape(tmp_path):",
    f"    a = Repo(tmp_path / 'a').{ENGINE_DOOR}([], display_name='X')",
    f"    b = Repo(tmp_path / 'b').{ENGINE_DOOR}([], display_name='X')",
    "    assert a == b",
    "",
])


def _two_leg_tests(files) -> list:
    """Every `def test_*` whose OWN source names the engine door TWICE.

    That is the tautology the deleted parity cases were: two legs, both calling
    `parse_identifiers` + the engine, which cannot fail for any change to either
    path. Asserting the ABSENCE of the shape is what stops a build "repairing"
    the harness by renaming it. Read off source text, one function at a time, so
    it sees a call the way a reader does.
    """
    from tests.derivations import module_id
    found = []
    for path in files:
        current, count = None, 0
        for line in Path(path).read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped.startswith("def test_") or (
                    stripped.startswith("def ") and line[:1] != " "):
                if current and count >= 2:
                    found.append((module_id(path), current))
                current = stripped[4:].split("(")[0] if stripped.startswith("def test_") else None
                count = 0
            elif current and f"{ENGINE_DOOR}(" in stripped:
                count += 1
        if current and count >= 2:
            found.append((module_id(path), current))
    return found


def test_legacy_stub_is_gone_and_the_golden_is_the_oracle():
    """AC-1. The zero-sites clause is the deletion; the golden clause is what
    stops the deletion from being a net loss of evidence."""
    files = python_files_under(PACKAGE_ROOT, TESTS_ROOT)
    assert files, "the file list is empty — the zero below would be vacuous"

    # A LITERAL-TEXT scan, so the 126-line `def` itself, every caller and any
    # comment or string mention are all in reach. A caller-scan cannot see a
    # `def`: deleting the callers while leaving the body returns the empty set
    # and this clause would go green with the duplicate still shipped.
    assert _literal_sites(LEGACY_STUB_ATTR, files) == [], (
        "the duplicate is still named somewhere in the tracked sources")
    _planted_positive(LEGACY_STUB_ATTR)

    # The both-legs clause, with its own non-vacuity positive: after this cut
    # the real population is empty, so an unreachable predicate would be green.
    assert _two_leg_tests(files) == [], (
        "a test whose two legs both reach the engine cannot fail for any change "
        "to either of them")
    with temp_dir() as scratch:
        _write_plant(scratch, "two_leg_plant.py", TWO_LEG_PLANT)
        assert _two_leg_tests(python_files_under(scratch)), (
            "the predicate cannot find the two-leg shape even where it IS")

    # The golden: DATA in the repository, replayed in the frozen ORDER, in a
    # freshly-seeded temp vault of its own — this is the sweep that WRITES.
    roster = load_roster()
    golden = _golden("stub_golden.json")
    assert golden["roster_digest"] == roster_digest()
    before = ROSTER_PATH.read_bytes()

    with temp_dir() as scratch:
        vault = seed_vault(roster, scratch / "vault")
        repo = PersonRepository(vault)
        mismatches = []
        for case in golden["cases"]:
            person, created = repo.find_or_create_stub(
                case["name"], email=case["email"], phone=case["phone"],
                company=case["company"])
            if (person.name, created) != (case["expected_name"],
                                          case["expected_created"]):
                mismatches.append(
                    (case["ordinal"], case["arm"], case["name"],
                     (case["expected_name"], case["expected_created"]),
                     (person.name, created)))
        assert mismatches == [], mismatches

    assert ROSTER_PATH.read_bytes() == before, (
        "the committed fixture was rewritten by its own test — every run seeds "
        "a fresh temp vault and discards it")


# ── Task 12 — the strangler-prose class, closed over an ENUMERATED SURFACE ───

# Every needle is ASSEMBLED from parts: a check that spells its own needle whole
# is its own counterexample, and two of these are literals sibling checks assert
# at zero across a root that contains this module.
TIER_A_NEEDLE_PARTS = (
    ("_email", "_index"),
    ("_find_or_create", "_stub_legacy"),
    ("Phase", "-5"),
    ("Tries in", " order"),
    ("Build email, phone,", " and alias indexes"),
    ("legacy ", "Strategy"),
    ("legacy ", "best-hit"),
)

TIER_B_NEEDLE_PARTS = (
    ("zero parity", " risk"),
    ("later deletion", " cut"),
    ("during ", "transition"),
    ("resolves the", " old way"),
    ("still indexes", " it"),
    ("stops at the first", " cascade hit"),
    ("bumped ", "0.65"),
    ("person.py:", "~476"),
    ("replay confirms", " zero"),
)

# The near-miss line: a case-SENSITIVE scan must collect none of these. The
# second is spelled with a non-underscore character before it, which is what
# keeps it BOTH a near-miss and outside the contiguous-substring rule above.
NEAR_MISS_PLANT = (
    "X = 1  # Phase-4 survives; self.email_index survives; legacy strategy "
    "survives (lower-cased)\n")

GOLDEN_FILE_NAMES = ("stub_golden.json", "resolve_golden.json")


def _needles(*tables) -> list:
    return ["".join(parts) for table in tables for parts in table]


def test_strangler_prose_class_is_closed_in_the_package():
    """Clause (e) is the CLOSURE and (a)-(d) are the regression pin. That
    ordering matters: for two rounds the pin WAS the closure, and its finding
    step under-reached both times."""
    package_files = python_files_under(PACKAGE_ROOT)
    assert package_files, "the file list is empty — every zero below is vacuous"

    # (a) + (b) — a thing that no longer exists, and a falsified proposition
    # restated in the file's own words.
    surviving = {needle: _literal_sites(needle, package_files)
                 for needle in _needles(TIER_A_NEEDLE_PARTS, TIER_B_NEEDLE_PARTS)}
    assert {n: s for n, s in surviving.items() if s} == {}, surviving

    person_text = (PACKAGE_ROOT / "repositories" / "person.py").read_text(
        encoding="utf-8")

    # (c) — the surviving text POINTS AT the committed goldens. Without this,
    # the replay-claim needle above would be satisfied by deleting the sentence
    # and pointing at nothing.
    for name in GOLDEN_FILE_NAMES:
        assert name in person_text, name

    # (d) — the two-part non-vacuity control over EVERY needle, plus the
    # near-miss the scan must not collect.
    with temp_dir() as scratch:
        for needle in _needles(TIER_A_NEEDLE_PARTS, TIER_B_NEEDLE_PARTS):
            plant = _write_plant(scratch, "needle_plant.py", f"X = 1  # {needle}\n")
            assert len(_literal_sites(needle, python_files_under(scratch))) == 1, (
                f"the scan cannot find {needle!r} even where it IS")
            plant.unlink()
        _write_plant(scratch, "near_miss_plant.py", NEAR_MISS_PLANT)
        collected = {needle: _literal_sites(needle, python_files_under(scratch))
                     for needle in _needles(TIER_A_NEEDLE_PARTS,
                                            TIER_B_NEEDLE_PARTS)}
        assert {n: s for n, s in collected.items() if s} == {}, (
            "a case-sensitive scan must not collect the near-misses — otherwise "
            f"it could pass by matching everything: {collected}")

    # (e) — the disposition rule over the whole prose surface, both directions.
    cut0 = _golden("prose_surface_cut0.json")["lines"]
    final = [r for r in prose_lines(package_files) if r.module == PERSON_MODULE]

    # (e4), the non-vacuity positive for the whole clause, asserted FIRST so
    # neither direction below can be satisfied by an empty domain.
    assert cut0 and final, (len(cut0), len(final))
    cut0_owners = {line["owner"] for line in cut0}
    for owner in AUTHORIZED_PROSE_OWNERS:
        assert owner in cut0_owners, owner

    final_pairs = {(r.owner, r.text) for r in final}

    # (e1) — a Cut-0 line of an UNAUTHORIZED owner survives VERBATIM. Compared
    # on (owner, text), never on line numbers, so an authorized neighbour's
    # reflow does not go red for the reflow. A rewrite of an unauthorized
    # owner's prose DOES, and that is intended.
    unauthorized_losses = [
        (line["owner"], line["text"]) for line in cut0
        if line["owner"] not in AUTHORIZED_PROSE_OWNERS
        and (line["owner"], line["text"]) not in final_pairs]
    assert unauthorized_losses == [], (
        "prose this item was not authorized to touch changed — either it is a "
        f"member the plan missed (name it in the Build Log) or revert it: "
        f"{unauthorized_losses}")

    # (e2) — an authorized owner whose ordered repair never landed is RED.
    cut0_pairs_by_owner = {}
    for line in cut0:
        cut0_pairs_by_owner.setdefault(line["owner"], set()).add(line["text"])
    unrepaired = [
        owner for owner in AUTHORIZED_PROSE_OWNERS
        if not any((owner, text) not in final_pairs
                   for text in cut0_pairs_by_owner[owner])]
    assert unrepaired == [], (
        f"these owners were ordered a prose repair that never landed: {unrepaired}")

    # (e3) — strictly stronger than the (e2) it also satisfies, which is why it
    # is its own clause.
    assert [r for r in final if r.owner == LEGACY_STUB_OWNER] == [], (
        "the deleted duplicate still owns prose")


# ── Task 13 — wall membership, closed by RUNNING each wall's own predicate ───

# Every file this item creates or edits. Membership is closed by calling each
# wall's shipped predicate on their FINAL text, never by reasoning about which
# shapes match.
ITEM_PACKAGE_FILES = ("obsidian_schemas/repositories/person.py",)

ITEM_TESTS_FILES = (
    "tests/derivations.py",
    "tests/identity_fixture.py",
    "tests/record_identity_golden.py",
    "tests/test_identity_endgame.py",
    "tests/test_resolve_or_create.py",
    "tests/test_wi126_body_preservation.py",
    "tests/test_identity_index.py",
    "tests/test_ac_interpreter.py",
)

ITEM_FIXTURE_FILES = (
    "tests/fixtures/identity_endgame/roster.json",
    "tests/fixtures/identity_endgame/stub_golden.json",
    "tests/fixtures/identity_endgame/resolve_golden.json",
    "tests/fixtures/identity_endgame/prose_surface_cut0.json",
)

# The functions this item edited or deleted in the package — the cells that ask
# whether any of them joined a write-routing or gate universe.
ITEM_EDITED_QUALNAMES = frozenset({
    "PersonRepository.__init__",
    "PersonRepository._index_entity",
    "PersonRepository._project_identifiers",
    "PersonRepository._index_identifiers",
    "PersonRepository._clear_indexes",
    "PersonRepository._remove_entity_from_indexes",
    "PersonRepository.get_by_email",
    "PersonRepository.get_by_phone",
    "PersonRepository.resolve",
    "PersonRepository.resolve_all",
    "PersonRepository.find_or_create_stub",
    "PersonRepository.resolve_or_create",
    "PersonRepository._resolve_identifier",
    "select_resolution",
})

# The M3 non-vacuity plant is a TRIPLE-QUOTED PLANT CONSTANT, and that is the
# mechanism rather than a style choice: the borrowed line scan enters and leaves
# such a constant cleanly by its own delimiter tracking, so the construction
# inside it is correctly NOT counted as one of this module's own — which is what
# the zero below means. Spelled as an ordinary inline string it would be a code
# line, and this module would be its own offender.
NO_ARG_PLANT = '''
x = PersonRepository()
'''

ITEM_CHECK_NAMES = (
    "test_legacy_stub_is_gone_and_the_golden_is_the_oracle",
    "test_email_has_exactly_one_resolution_authority",
    "test_phones_stay_on_the_fuzzy_path_and_the_reason_is_executable",
    "test_resolve_is_one_cascade_and_matches_the_pre_cut_golden",
    "test_identity_cutover_docs_are_complete_and_truthful",
)


def test_identity_endgame_wall_membership_is_closed():
    """Each wall's OWN predicate, run on this item's final text. Anything a run
    returns that the plan did not name is a Build Log entry and a repair —
    never a narrowed wall."""
    from tests.derivations import (
        SCRIPTS_ROOT,
        address_splitting_implementations,
        character_class_strip_sites,
        filesystem_mutation_uses,
        frontmatter_write_arms,
        modules_using_ast,
        module_import_uses,
        non_completed_write_sites,
        os_module_attribute_uses,
    )
    from tests.test_vault_path_required import (
        FORBIDDEN_DEFAULT_PATTERNS,
        NO_ARG_CONSTRUCTION,
        _code_lines,
        _scanned_markdown_files,
    )

    for relative in ITEM_PACKAGE_FILES + ITEM_TESTS_FILES + ITEM_FIXTURE_FILES:
        assert (REPO_ROOT / relative).exists(), relative

    both_roots = python_files_under(PACKAGE_ROOT, TESTS_ROOT)
    package_files = python_files_under(PACKAGE_ROOT)
    person_path = REPO_ROOT / ITEM_PACKAGE_FILES[0]
    item_test_paths = [REPO_ROOT / relative for relative in ITEM_TESTS_FILES]

    # Rows 1-2: the `ast` capability stays single-homed, by set EQUALITY. The
    # four new predicates are exports of that one module and no module this item
    # writes names `ast`.
    assert {use.module for use in modules_using_ast(both_roots)} == {
        "tests/derivations.py"}

    # Rows 3-4: no function this item edited or deleted is in the falsy-return
    # write universe — none of them names a write capability.
    stranded = [site for site in non_completed_write_sites(package_files)
                if site.qualname in ITEM_EDITED_QUALNAMES]
    assert stranded == [], stranded

    # Row 6: the package's edits name no filesystem-mutation capability, and the
    # three new modules are under `tests/`, OUTSIDE this universe — which is WHY
    # they are there. Asserted rather than assumed.
    routing_universe = {str(p) for p in
                        python_files_under(PACKAGE_ROOT, SCRIPTS_ROOT)}
    for relative in ITEM_TESTS_FILES:
        assert str(REPO_ROOT / relative) not in routing_universe, relative
    assert filesystem_mutation_uses([person_path]) == []
    assert os_module_attribute_uses([person_path]) == []
    assert module_import_uses([person_path], ("os", "shutil", "tokenize")) == []

    # Row 7: the package file contributes no write arm and no character-class
    # strip; the deleted function contained neither.
    assert [a for a in frontmatter_write_arms([person_path])] == []
    assert character_class_strip_sites([person_path]) == []

    # Row 8: address splitting stays single-homed IN THE WALL'S OWN UNIVERSE
    # (the package plus scripts, which is the scope the wall declares), and
    # nothing this item writes splits an address.
    homes = address_splitting_implementations(
        python_files_under(PACKAGE_ROOT, SCRIPTS_ROOT))
    assert {home.qualname for home in homes} == {"split_address"}, homes
    assert address_splitting_implementations(
        item_test_paths + [person_path]) == set(), (
        "a file this item writes implements address splitting — the job has one "
        "home and this is not it")

    # Row 9: the package edits introduce no caller-independent default path.
    offenders = [(lineno, line) for lineno, line in _code_lines(person_path)
                 for pattern in FORBIDDEN_DEFAULT_PATTERNS if pattern in line]
    assert offenders == [], offenders

    # Row 10: THIS ITEM adds no `.md` anywhere — its fixture is JSON and its
    # vault is seeded into a temp directory — so nothing it writes joins that
    # walk's population. Stated over this item's own files rather than over the
    # whole of `tests/`: WI-016 committed a fixture vault of `.md` notes after
    # D10's census was taken, so the blanket form is false of the tree while the
    # cell's actual requirement is untouched.
    scanned = {str(p.resolve()) for p in _scanned_markdown_files()}
    item_paths = {str((REPO_ROOT / relative).resolve()) for relative in
                  ITEM_PACKAGE_FILES + ITEM_TESTS_FILES + ITEM_FIXTURE_FILES}
    assert not [relative for relative in
                ITEM_PACKAGE_FILES + ITEM_TESTS_FILES + ITEM_FIXTURE_FILES
                if relative.endswith(".md")]
    assert scanned & item_paths == set(), scanned & item_paths

    # Row 11: each check name resolves to exactly one module.
    from tests.test_ac_interpreter import check_module
    for name in ITEM_CHECK_NAMES:
        assert check_module(name).name == "test_identity_endgame.py", name

    # Row 12 — the wall-SHAPED HOLE, not a wall. The shipped pattern reaches
    # `obsidian_schemas/` and `scripts/` only, and this item adds three
    # repository-constructing modules under `tests/`, two of which WRITE. The
    # pattern and the line iterator are IMPORTED, never re-spelled, so a future
    # narrowing of the wall's own regex cannot leave this asserting a shape the
    # wall no longer means.
    assert item_test_paths, "the file list is empty — the zero below is vacuous"
    constructions = [
        (relative, lineno, line.strip())
        for relative, path in zip(ITEM_TESTS_FILES, item_test_paths)
        for lineno, line in _code_lines(path)
        if NO_ARG_CONSTRUCTION.search(line)]
    assert constructions == [], constructions
    with temp_dir() as scratch:
        planted = _write_plant(scratch, "no_arg_plant.py", NO_ARG_PLANT)
        assert [1 for _, line in _code_lines(planted)
                if NO_ARG_CONSTRUCTION.search(line)], (
            "the borrowed pattern cannot collect the construction even where it "
            "IS — the zero above would say nothing")

    # The THIRD control, which the other zero-counts do not need because they
    # run through a tokenizer rather than a borrowed line scan: that scan sets
    # its in-docstring flag on any line holding an odd count of a triple-quote
    # delimiter, TRAILING COMMENTS INCLUDED, so one such comment swallows every
    # code line beneath it and the zero above reads exactly like a clean scan
    # while being an under-reach.
    swallowing = [
        (record.module, record.lineno, record.text)
        for record in prose_lines(item_test_paths)
        if "#" in record.text
        and any(delimiter in record.text.split("#", 1)[1]
                for delimiter in ('"' * 3, "'" * 3))]
    assert swallowing == [], (
        "a comment in one of this item's modules carries a triple-quote "
        f"delimiter; drop it out of the comment: {swallowing}")
