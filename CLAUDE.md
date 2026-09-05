# obsidian-schemas

Canonical Pydantic entity schemas for Obsidian frontmatter.

## What It Does

Shared library providing:
- Pydantic models for entity types (Person, Company, Book, Meeting, etc.)
- Parser/writer for markdown frontmatter
- Repository layer for loading, querying, saving entities
- Phone normalization, alias matching, smart resolution

## Quick Start

```python
from obsidian_schemas import PersonRepository

repo = PersonRepository("/path/to/vault")  # or set OBSIDIAN_VAULT_PATH — one of the two is required
person = repo.resolve("john@example.com")  # Smart lookup
vips = repo.get_by_role("vip")
```

## Used By

- **HAL9000** - Contact resolution, intro previews
- **Exocortex** - Attendee resolution, entity linking
- **orchestrator** - Contact normalization, stub creation (find_or_create_stub)

## Key Files

| File | Purpose |
|------|---------|
| `obsidian_schemas/models.py` | All entity schemas |
| `obsidian_schemas/parser.py` | Markdown → typed models |
| `obsidian_schemas/writer.py` | Models → markdown files |
| `obsidian_schemas/vault_io.py` | THE write door (WI-004): atomic commit, per-file locking, stamp preconditions — every vault write routes here |
| `obsidian_schemas/repositories/person.py` | PersonRepository (incl. resolve cascade + WI-125 identity engine) |
| `obsidian_schemas/repositories/company.py` | CompanyRepository |
| `obsidian_schemas/identifier.py` | Typed Identifier union + EntityRef (identity core, WI-125) |
| `obsidian_schemas/name_validation.py` | NameValidator boundary contract (WI-105) |
| `obsidian_schemas/name_gate.py` | THE semantic write gate (WI-021, landing): every frontmatter-writing arm hands it the fields the write introduces plus a declared type; it refuses with `NameGateRefusal` or returns them normalized |
| `obsidian_schemas/phone_normalization.py` | `normalize_phone`/`phones_match` leaf (WI-021 relocation; `repositories/person.py` re-exports both for consumers) |
| `obsidian_schemas/name_cleaning.py` | clean_person_name (WI-117) |
| `obsidian_schemas/body_sections.py` | Markdown body section parse/write, To-Discuss items |

## Installation

```bash
# From HAL9000 or Exocortex
pip install -e /Users/davewascha/Workspaces/obsidian-schemas
```

## Running Tests

**Floor command** (the pipeline's test floor — one command, absolute, cwd-independent, exit 0/1):

```bash
/Users/davewascha/Workspaces/obsidian-schemas/.venv/bin/python -m pytest \
    /Users/davewascha/Workspaces/obsidian-schemas/tests -q
```

Hermetic, ~1s. Baseline: run the floor command to check the current count — never trust a number
written here (2026-07-24 conductor note: the hardcoded "607 passed" baseline was drift-prone; WI-020's
build raises the count substantially). The invariant is DIRECTIONAL: a drive that lands fewer cases
than the previous run without explanation has silently lost a test file. Last verified-by-hand
anchors, for archaeology only: 563 (pre-WI-024), 607 (2026-07-19 post-WI-024).

**Loud-fail API (WI-020; WI-021 adds `NameGateRefusal`):** `obsidian_schemas/errors.py` is one
hierarchy rooted at `LoudFailError` (a `ValueError`). Never trust a member COUNT written here — it
drifted from six to nine unnoticed; run `python -c 'import obsidian_schemas as o; print(o.__all__)'`
to see the exported members. The IDIOM is what matters: catch `LoudFailError` for "this package
refused"; `NoteParseError` covers both parse failures. A handler that RE-RAISES may filter on the
root; a handler that ABSORBS, and any test asserting a refusal, names the LEAF it means — e.g.
`NameGateRefusal` with its `pattern` attribute (WI-021) — because sibling leaves raise from the same
frames and a root filter would misattribute them. Repositories expose a queryable skip surface for
notes they own but could not load. Contract details live in the package docstrings (the builds carry
them there — this file holds only the pointer; neither WI-020's nor WI-021's build writes this file,
and this section is the conductor-committed landing note they rely on).

System python has no pytest — always use the `.venv` interpreter. Note that this `.venv`'s editable
install is stale (`_obsidian_schemas.pth` points at a path that no longer exists), so a bare
`import obsidian_schemas` fails; the suite works because pytest prepends its rootdir to `sys.path`.
See `pipeline-runners.yaml` for why that is load-bearing and must not be "fixed".

## What's Next

Read `state/work-items.json` for the current backlog and pipeline state. Work items are tracked using the work-item pipeline — see `/Users/davewascha/Workspaces/workshop/docs/pipeline-quickstart-guide.md` for how it works. Use `/capture-idea` to add new ideas.

## Documentation

- **SESSION_LOG.md** - Chronological record of work (recent-first)
- **README.md** - Full API documentation with examples
- **state/work-items.json** - Backlog and pipeline (replaces BACKLOG.md)
- **docs/** - Work-item docs (one per item, YAML frontmatter) + campaign docs. Current queue and routing: `docs/backlog-campaign-2026-07-05.md`

Run `/wrap-up` at end of sessions to update all docs.

## Schema Changes

When modifying entity schemas:
1. Update `models.py`
2. Run tests: `pytest`
3. Both HAL9000 and Exocortex will pick up the change (they install via `-e`)
