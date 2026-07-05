---
id: WI-001
title: "File Watching / Real-time Updates"
project: obsidian-schemas
stage: idea
created: 2026-03-22
last_touched: 2026-03-22
stage_changed: 2026-03-22
touched_by: session
tags: [repository]
depends_on: []
---

# File Watching / Real-time Updates

## Problem / Motivation

Long-running processes like the HAL9000 server hold repository instances in memory, but the underlying vault files can change at any time (Obsidian edits, other tools writing frontmatter). Currently there's no way to detect these changes — the cache goes stale silently, and queries return outdated data until someone manually calls `refresh()`. Integrating with `watchdog` for filesystem events would let repositories auto-refresh their cache when vault files change, keeping data current without polling or manual intervention.
