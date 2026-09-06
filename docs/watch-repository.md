---
id: WI-007
title: "WatchRepository"
project: obsidian-schemas
stage: idea
created: 2026-03-22
last_touched: 2026-09-06
stage_changed: 2026-03-22
touched_by: session
tags: [repository]
depends_on: []
---

# WatchRepository

**Premise rewritten 2026-09-06 (queue review):** the entity TYPE is done — `class Watch` exists at `models.py:173`. What does not exist is the repository (`obsidian_schemas/repositories/` holds base, book, company, meeting, person), writer/stub support, and tests. The shape to copy is the BookRepository sibling (`repositories/book.py`: `save` at :167-178, `create_stub` at :278). Any sentence below that says the Watch type is missing or 'likely' needs defining is stale; read this paragraph as the premise.

## Problem / Motivation

BookRepository was completed (2026-01-11) to manage reading list entities, but the equivalent for watch list items (movies, TV shows, documentaries) still doesn't exist. The Watch entity type likely follows the same patterns as Book — status tracking (to-watch, watching, watched), query by status, and frontmatter schema. Without it, watch list data in the vault is only accessible through raw Obsidian search, not through the typed repository API that HAL9000 and other consumers depend on.
