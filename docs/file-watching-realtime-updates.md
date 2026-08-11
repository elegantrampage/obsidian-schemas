---
id: WI-001
title: "File Watching / Real-time Updates"
project: obsidian-schemas
stage: parked
created: 2026-03-22
last_touched: 2026-08-11
stage_changed: 2026-08-11
touched_by: session
tags: [repository]
depends_on: []
---

# File Watching / Real-time Updates

## Problem / Motivation

Long-running processes like the HAL9000 server hold repository instances in memory, but the underlying vault files can change at any time (Obsidian edits, other tools writing frontmatter). Currently there's no way to detect these changes — the cache goes stale silently, and queries return outdated data until someone manually calls `refresh()`. Integrating with `watchdog` for filesystem events would let repositories auto-refresh their cache when vault files change, keeping data current without polling or manual intervention.

## Parked — 2026-08-11 (queue review)

Un-park criterion: a REAL staleness incident in a long-running consumer. WI-004 (2026-08-11) declared read-staleness the caller's residual (R2) with `refresh()` as its owner, and its stamp registry now refuses stale WRITES — the corruption half is closed; this item is freshness-of-READS only, and no incident has demanded it.
