"""WI-023 — the identity endgame's fixture: one roster declaration, seeded.

The roster is committed DATA (`tests/fixtures/identity_endgame/roster.json`),
not a directory of committed notes, for two concrete reasons. First, the sweep
this fixture exists for MUTATES the vault — a create case mints notes, and a
pre-cut reuse writes identifiers back — so a committed corpus would be rewritten
by its own test. Second, `tests/test_vault_path_required.py` walks the repo for
`*.md` and committed fixture notes would join that wall's population; a JSON
declaration does not.

Not a `test_*.py` module, so pytest never collects it. It lives under `tests/`
rather than `scripts/` deliberately: it writes files with `Path.write_text`, and
`tests/test_write_routing.py` forbids that capability anywhere under
`obsidian_schemas/` or `scripts/`.

That placement is also what puts `seed_vault` OUTSIDE the standing wall against
caller-independent vault paths (`test_no_implicit_vault_path_defaults` scans
`obsidian_schemas/` and `scripts/` only), so it carries its own refusal at the
one door every seeding goes through — see `seed_vault`.
"""

import hashlib
import json
from pathlib import Path

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "identity_endgame"
ROSTER_PATH = FIXTURE_DIR / "roster.json"

SCHEMA_VERSION = 1


def load_roster() -> dict:
    """The frozen roster, as committed. Loud on a schema-version drift."""
    roster = json.loads(ROSTER_PATH.read_text(encoding="utf-8"))
    if roster.get("schema_version") != SCHEMA_VERSION:
        raise AssertionError(
            f"{ROSTER_PATH} carries schema_version "
            f"{roster.get('schema_version')!r}, not {SCHEMA_VERSION} — the "
            f"goldens are bound to this shape")
    return roster


def roster_digest() -> str:
    """The sha256 of the roster's committed BYTES. Every golden carries it."""
    return hashlib.sha256(ROSTER_PATH.read_bytes()).hexdigest()


def _is_swallowed_dest(dest) -> bool:
    """True for a `dest` the library would resolve elsewhere.

    Mirrors `obsidian_schemas/repositories/base.py:_is_unconfigured` by its
    stated rule — absent, blank/whitespace-only, or normalising to the current
    directory — on the NORMALISED string form rather than on a type test, since
    a `Path` is a legal argument here as it is there.
    """
    if dest is None:
        return True
    text = str(dest).strip()
    if not text:
        return True
    return Path(text) == Path(".")


def _note_text(note: dict) -> str:
    """One person note's markdown. Every list element is DOUBLE-QUOTED.

    That is load-bearing for exactly one roster entry: `Dana Okafor`'s padded
    `" dana@example.com "` must survive load with its spaces intact, and a bare
    YAML scalar is stripped by the loader, which would make the plant inert.
    Nothing downstream re-normalizes it — `models.py`'s `emails` is a bare
    `List[str]` with no validator, and the parser carries no strip.
    """
    lines = ["---", "type: person", f"name: {note['name']}"]
    for field in ("emails", "aliases", "phones"):
        values = note.get(field) or []
        if values:
            lines.append(f"{field}:")
            lines += [f'  - "{value}"' for value in values]
    if note.get("company"):
        lines.append(f"company: {note['company']}")
    lines += ["tags:", "  - person", "---", "", "## Timeline", ""]
    return "\n".join(lines)


def seed_vault(roster: dict, dest) -> Path:
    """Write one `@<name>.md` per roster entry into `dest`; return `dest`.

    REFUSES a `dest` the library would swallow — `None`, blank, whitespace-only,
    or normalising to `Path(".")` — raising BEFORE it writes anything. The
    reason is specific to where this module sits and is not hygiene:
    `base.py:_resolve_vault_path` takes the explicit argument OR
    `OBSIDIAN_VAULT_PATH` and raises only when BOTH are unconfigured, that
    variable IS set on the machine this fixture is authored on, and the standing
    wall that forbids caller-independent defaults never reaches `tests/`. A
    seeder handed a swallowed `dest` writes ten notes into the live vault.
    """
    if _is_swallowed_dest(dest):
        raise AssertionError(
            f"seed_vault refuses dest={dest!r}: the library would resolve it to "
            f"OBSIDIAN_VAULT_PATH and this seeding would land in the live vault")
    path = Path(dest)
    path.mkdir(parents=True, exist_ok=True)
    for note in roster["notes"]:
        (path / f"@{note['name']}.md").write_text(_note_text(note),
                                                  encoding="utf-8")
    return path
