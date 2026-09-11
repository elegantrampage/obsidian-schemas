"""WI-023 Cut 0 — the ONE-SHOT recorder for this item's two goldens.

Run BY HAND, once, against unchanged code, before Cut 1, before Cut 2, before
Cut 3 — and never again:

    cd <tree root> && .venv/bin/python -m tests.record_identity_golden

A second recording is the one way this item's oracle can be defeated: a golden
regenerated from post-cut code agrees with whatever the cut did. Three
tripwires make that RED rather than silent (see
`tests/test_identity_endgame.py:test_identity_goldens_are_frozen_pre_cut_data`).

Not a `test_*.py` module, so pytest never collects it, and under `tests/` rather
than `scripts/` because it writes with `Path.write_text`, which
`tests/test_write_routing.py` forbids under `obsidian_schemas/` or `scripts/`.

**Two independent temp vaults, one per sweep.** The stub sweep is not a benign
append: pre-cut, cases 1 and 3 fall through to the name branch and their
identifier writeback routes through the semantic write gate, whose `emails` arm
rebuilds the list from the parsed address — destroying the angle-bracket and
the whitespace-padded plants IN PLACE. A resolve golden recorded in that vault
would contradict the spec's hand-executed table on two of its three rows. So the
read-only resolve sweep runs in its own freshly-seeded vault and the mutating
stub sweep in another, and no sweep ever reads a vault another sweep wrote.

**Every repository is BOUND to the vault this run seeded.** This is the item's
one hand-run invocation; it runs from the tree root with the author's ambient
`OBSIDIAN_VAULT_PATH` set, and `base.py:_resolve_vault_path` falls back to that
variable for an absent, blank or `"."` argument. An unbound repository here
mints the ten not-present notes into the live vault and rewrites real notes'
frontmatter through the write gate. `bound_repository` refuses BEFORE the first
write, because after it there is nothing left to refuse.
"""

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from obsidian_schemas import PersonRepository

from tests.derivations import PACKAGE_ROOT, prose_lines, python_files_under
from tests.identity_fixture import (
    FIXTURE_DIR,
    _is_swallowed_dest,
    load_roster,
    roster_digest,
    seed_vault,
)

RECORDED_AT = "cut-0"
SCHEMA_VERSION = 1

PERSON_MODULE = "obsidian_schemas/repositories/person.py"

STUB_GOLDEN_PATH = FIXTURE_DIR / "stub_golden.json"
RESOLVE_GOLDEN_PATH = FIXTURE_DIR / "resolve_golden.json"
PROSE_SURFACE_PATH = FIXTURE_DIR / "prose_surface_cut0.json"

# The not-present variants, pinned as literals rather than generated. Each pairs
# with the base case of the same position: a multi-token name (a single-token
# one with no identifier raises at the weak-identity guard where the case
# expects a create), a phone that is not-present under `phones_match` and not
# merely under string equality, and a Branch-B variant whose name stays clear of
# the roster's own tokens so a company bump cannot convert a create into a
# reuse. None of the twenty fresh tokens appears in the roster's twenty.
NOT_PRESENT_VARIANTS = [
    ("Wilbur Achebe",      "email",   "wilbur.achebe@notpresent.example.com"),
    ("Greta Oyelaran",     "email",   "greta.oyelaran@notpresent.example.com"),
    ("Marcus Thibodeaux",  "email",   "marcus.thibodeaux@notpresent.example.com"),
    ("Ingrid Castellanos", "email",   "ingrid.castellanos@notpresent.example.com"),
    ("Otto Farrimond",     "email",   "otto.farrimond@notpresent.example.com"),
    ("Neve Kowalczyk",     "email",   "neve.kowalczyk@notpresent.example.com"),
    ("Rafael Ibarrola",    "email",   "rafael.ibarrola@notpresent.example.com"),
    ("Sunniva Blackwood",  "phone",   "33612345678"),
    ("Hugo Pemberton",     "phone",   "33698765432"),
    ("Delphine Marchetti", "company", "Kestrel Analytics"),
]


def bound_repository(dest) -> PersonRepository:
    """A `PersonRepository` PROVEN to be looking at `dest`, or a refusal.

    Every repository this module constructs goes through here, so "every
    repository is bound" is a property of the module rather than a habit.
    """
    if _is_swallowed_dest(dest):
        raise AssertionError(
            f"refusing to construct a repository on dest={dest!r}: the library "
            f"resolves it to OBSIDIAN_VAULT_PATH, i.e. the live vault")
    repo = PersonRepository(dest)
    resolved = Path(repo.vault_path).resolve()
    if resolved != Path(dest).resolve():
        raise AssertionError(
            f"the constructed repository resolved to {resolved}, not to the "
            f"temp vault {Path(dest).resolve()} this run seeded")
    return repo


def derive_stub_cases(roster: dict) -> list:
    """AC-1's twenty ordered cases: ten base, then ten not-present variants.

    Roster order, and within a note: emails, then phones, then company. A note
    with no email, no phone and no company contributes no base case — which is
    correct, and is why the coverage claim rests on the ROSTER rather than on
    the sweep.
    """
    base = []
    for note in roster["notes"]:
        for email in note["emails"]:
            base.append({"arm": "per-email", "name": note["name"],
                         "email": email, "phone": None, "company": None})
        for phone in note["phones"]:
            base.append({"arm": "per-phone", "name": note["name"],
                         "email": None, "phone": phone, "company": None})
        if note["company"]:
            base.append({"arm": "per-company",
                         "name": note["name"].split()[0],
                         "email": None, "phone": None,
                         "company": note["company"]})

    if len(base) != len(NOT_PRESENT_VARIANTS):
        raise AssertionError(
            f"{len(base)} base cases against {len(NOT_PRESENT_VARIANTS)} pinned "
            f"variants — the variant table pairs one-for-one with the bases")

    cases = []
    for ordinal, case in enumerate(base, start=1):
        cases.append(dict(case, ordinal=ordinal))
    for offset, (name, kind, value) in enumerate(NOT_PRESENT_VARIANTS):
        cases.append({
            "ordinal": len(base) + 1 + offset,
            "arm": "not-present",
            "name": name,
            "email": value if kind == "email" else None,
            "phone": value if kind == "phone" else None,
            "company": value if kind == "company" else None,
        })
    return cases


def derive_resolve_queries(roster: dict) -> list:
    """AC-4's query space: every name, name token, alias, email and phone, in
    roster order, de-duplicated by query STRING with the first occurrence
    winning. `arm` records WHICH derivation clause produced a query, so a
    re-derivation that agreed on the strings while disagreeing on the clause is
    still a reshaped space."""
    queries = []
    seen = set()

    def add(arm, query):
        if query in seen:
            return
        seen.add(query)
        queries.append({"ordinal": len(queries) + 1, "arm": arm, "query": query})

    for note in roster["notes"]:
        add("name", note["name"])
        for token in note["name"].split():
            add("name-token", token)
        for alias in note["aliases"]:
            add("alias", alias)
        for email in note["emails"]:
            add("email", email)
        for phone in note["phones"]:
            add("phone", phone)
    return queries


def record_stub_golden(roster: dict, cases: list, dest) -> dict:
    """Replay the frozen ordered case list in ONE temp vault. This sweep WRITES:
    a create case mints a note visible to every later case in the same run,
    which is why the order is frozen data rather than re-derived from a walk."""
    seed_vault(roster, dest)
    repo = bound_repository(dest)
    recorded = []
    for case in cases:
        person, created = repo.find_or_create_stub(
            case["name"], email=case["email"], phone=case["phone"],
            company=case["company"])
        recorded.append(dict(case, expected_name=person.name,
                             expected_created=created))
    return {"schema_version": SCHEMA_VERSION, "recorded_at": RECORDED_AT,
            "roster_digest": roster_digest(), "cases": recorded}


def record_resolve_golden(roster: dict, queries: list, dest) -> dict:
    """Replay the derived query space read-only, in a vault no sweep has
    written. `expected` is the resolved person's name, or null for a None."""
    seed_vault(roster, dest)
    repo = bound_repository(dest)
    recorded = []
    for query in queries:
        person = repo.resolve(query["query"])
        recorded.append(dict(query,
                             expected=person.name if person else None))
    return {"schema_version": SCHEMA_VERSION, "recorded_at": RECORDED_AT,
            "roster_digest": roster_digest(), "queries": recorded}


def record_prose_surface() -> dict:
    """The pre-cut prose surface of `person.py`, read from the file's BYTES.

    Not a third golden and the item still has exactly two: a golden records an
    ANSWER the code gave and is replayed by a criterion; this records what the
    code SAID and is replayed by nobody. It shares the recorder and the baseline
    moment for the one property it does share — after the first prose edit it
    can no longer be derived, so this is the only moment it can be captured.
    """
    records = [
        {"owner": record.owner, "line": record.lineno, "text": record.text}
        for record in prose_lines(python_files_under(PACKAGE_ROOT))
        if record.module == PERSON_MODULE
    ]
    if not records:
        raise AssertionError(
            f"the prose surface of {PERSON_MODULE} came back empty — a surface "
            f"recorded against a renamed file is not a baseline")
    return {"schema_version": SCHEMA_VERSION, "recorded_at": RECORDED_AT,
            "lines": records}


def _write(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8")


def main() -> None:
    roster = load_roster()
    cases = derive_stub_cases(roster)
    queries = derive_resolve_queries(roster)

    with TemporaryDirectory(prefix="wi023-resolve-") as resolve_dir:
        resolve_golden = record_resolve_golden(
            roster, queries, Path(resolve_dir) / "vault")
    with TemporaryDirectory(prefix="wi023-stub-") as stub_dir:
        stub_golden = record_stub_golden(
            roster, cases, Path(stub_dir) / "vault")

    FIXTURE_DIR.mkdir(parents=True, exist_ok=True)
    _write(RESOLVE_GOLDEN_PATH, resolve_golden)
    _write(STUB_GOLDEN_PATH, stub_golden)
    _write(PROSE_SURFACE_PATH, record_prose_surface())

    print(f"recorded {len(stub_golden['cases'])} stub cases, "
          f"{len(resolve_golden['queries'])} resolve queries, and "
          f"{len(record_prose_surface()['lines'])} prose lines at "
          f"{RECORDED_AT}")


if __name__ == "__main__":
    main()
