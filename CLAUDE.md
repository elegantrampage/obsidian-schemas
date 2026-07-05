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

repo = PersonRepository()  # Uses OBSIDIAN_VAULT_PATH env var
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
| `obsidian_schemas/repositories/person.py` | PersonRepository (incl. resolve cascade + WI-125 identity engine) |
| `obsidian_schemas/repositories/company.py` | CompanyRepository |
| `obsidian_schemas/identifier.py` | Typed Identifier union + EntityRef (identity core, WI-125) |
| `obsidian_schemas/name_validation.py` | NameValidator boundary contract (WI-105) |
| `obsidian_schemas/name_cleaning.py` | clean_person_name (WI-117) |
| `obsidian_schemas/body_sections.py` | Markdown body section parse/write, To-Discuss items |

## Installation

```bash
# From HAL9000 or Exocortex
pip install -e /Users/davewascha/Workspaces/obsidian-schemas
```

## Running Tests

```bash
cd /Users/davewascha/Workspaces/obsidian-schemas
.venv/bin/python -m pytest -q  # hermetic, ~1s; run this for the current count (system python has no pytest)
```

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
