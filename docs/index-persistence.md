---
id: WI-012
title: "Index Persistence"
project: obsidian-schemas
stage: parked
created: 2026-03-22
last_touched: 2026-08-11
stage_changed: 2026-08-11
touched_by: session
tags: [performance]
depends_on: []
---

# Index Persistence

## Problem / Motivation

Every time a repository is instantiated, it rebuilds its indexes from scratch by parsing every markdown file in the vault. For large vaults this is slow — startup time scales linearly with file count. Persisting indexes to disk (pickle or JSON) and only rebuilding when files change would make startup near-instant after the first run. The main challenge is cache invalidation: detecting when persisted indexes are stale and need rebuilding, ideally using file modification times rather than re-parsing everything.

## Parked — 2026-08-11 (queue review)

Un-park criterion: index rebuild cost becomes measurable pain. Baseline 2026-08-11: full rebuild rides a 1.27s load — no signal.
