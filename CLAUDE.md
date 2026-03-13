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

## Key Files

| File | Purpose |
|------|---------|
| `obsidian_schemas/models.py` | All entity schemas |
| `obsidian_schemas/parser.py` | Markdown → typed models |
| `obsidian_schemas/writer.py` | Models → markdown files |
| `obsidian_schemas/repositories/person.py` | PersonRepository |
| `obsidian_schemas/repositories/company.py` | CompanyRepository |

## Installation

```bash
# From HAL9000 or Exocortex
pip install -e /Users/davewascha/Workspaces/obsidian-schemas
```

## Running Tests

```bash
cd /Users/davewascha/Workspaces/obsidian-schemas
pytest  # 195+ tests
```

## Documentation

- **SESSION_LOG.md** - Chronological record of work (recent-first)
- **README.md** - Full API documentation with examples
- **BACKLOG.md** - Deferred enhancements and ideas
- **docs/** - Planning documents and reference material (currently empty)

Run `/wrap-up` at end of sessions to update all docs.

## Schema Changes

When modifying entity schemas:
1. Update `models.py`
2. Run tests: `pytest`
3. Both HAL9000 and Exocortex will pick up the change (they install via `-e`)

---

## Documentation Registry

When creating or significantly updating documentation in this project:

1. Create/update the local doc
2. Register in the global map at `/Users/davewascha/Workspaces/DOCS.md`:
   - Add entry to the project's table in "By Project" section
   - If it fits a topic category, add to "By Topic" section
   - Format: `| Doc Name | relative/path.md | Brief description |`

**What to register:** README, architecture docs, API docs, guides, specs, decisions.
**Skip:** SESSION_LOG, BACKLOG (these follow standard pattern and are assumed to exist).
