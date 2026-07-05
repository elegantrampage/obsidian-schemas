---
id: WI-007
title: "WatchRepository"
project: obsidian-schemas
stage: idea
created: 2026-03-22
last_touched: 2026-03-22
stage_changed: 2026-03-22
touched_by: session
tags: [repository]
depends_on: []
---

# WatchRepository

## Problem / Motivation

BookRepository was completed (2026-01-11) to manage reading list entities, but the equivalent for watch list items (movies, TV shows, documentaries) still doesn't exist. The Watch entity type likely follows the same patterns as Book — status tracking (to-watch, watching, watched), query by status, and frontmatter schema. Without it, watch list data in the vault is only accessible through raw Obsidian search, not through the typed repository API that HAL9000 and other consumers depend on.
