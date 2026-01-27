# Work Log

Detailed history of work on obsidian-schemas.

---

## 2026-01-26

### Slack Field Addition
- Added `slack: str = ""` field to Person model for Slack user ID/handle storage
- Updated Person docstring template to include slack field
- Added 4 tests for slack field (default, user ID, handle, all fields)
- Added slack indexing to PersonRepository:
  - `_slack_index: Dict[str, str]` for O(1) lookup
  - `get_by_slack(slack_id)` method with @ prefix normalization
  - Updated `_index_entity()`, `_clear_indexes()`, `_remove_entity_from_indexes()`
- Added 4 repository tests for slack lookup
- Updated README with slack in Person fields list
- Total: 195 tests passing

**Downstream updates:**
- HAL9000: Added `slack` to ContactInfo dataclass and `from_person()` method
- Exocortex: Added `slack` to ContactInfo dataclass and `from_person()` method
- Obsidian vault: Updated person.md template, added slack to @Emma Roberts.md

---

## 2026-01-19

### Birthday Field Addition
- Added `birthday: str = ""` field to Person model (DD-MM-YYYY or DD-MM format)
- Updated docstring with birthday format documentation
- Added 4 regression tests for birthday field
- Commit: `d075018` pushed to main

---

## 2026-01-11

### Entity CRUD System - BookRepository & MeetingRepository

- Added `BookRepository` (`repositories/book.py`, 346 lines)
  - Custom indexes: `_author_index`, `_isbn_index`
  - Methods: `get_by_author()`, `get_by_status()`, `get_by_isbn()`, `resolve()`
  - Overrode `_load_file()` to filter by `type: book` in frontmatter
  - Overrode `save()` to use "Title - Author.md" filename format
  - 15 tests

- Added `MeetingRepository` (`repositories/meeting.py`, 415 lines)
  - Custom indexes: `_meeting_id_index`, `_date_index`, `_attendee_index`, `_topic_index`
  - Methods: `get_by_meeting_id()`, `get_by_date()`, `get_by_date_range()`, `get_by_attendee()`, `get_by_topic()`, `resolve()`
  - 19 tests

- Made repo public for HAL9000 CI access
- PR #1 merged
- Total: 183 tests passing

---

### To Discuss Feature (continued from previous session)

- Created `remind-to-discuss` Claude Code skill at `~/.claude/skills/remind-to-discuss/SKILL.md`
  - Parses natural language "remind me to discuss X with Y"
  - Uses PersonRepository to resolve contacts
  - Calls `add_to_discuss_item()` to add items with auto-dating
- Tested skill end-to-end: created Emma Roberts @ Kato contact, added to-discuss item

### Previous session (same day)
- Completed Phase 0-6 of To Discuss implementation
- Added body_sections module for parsing/manipulating markdown sections
- Added ToDiscussItem dataclass and repository methods
- Created migration script, ran on vault (207 files updated)
- Updated README with full documentation

---

## 2026-01-10

- Added Person Schema enhancement idea to FUTURE.md:
  - `profession` field (engineer, designer, PM, etc.)
  - `seniority` field (junior through C-level)
  - Use case: match job opportunities to people in network

---

## 2026-01-06

- Created CLAUDE.md entry point
- (FUTURE.md already exists as backlog)

---

## 2026-01-10

- Created GitHub repo (elegantrampage/obsidian-schemas)
- Initial commit pushed to main branch
