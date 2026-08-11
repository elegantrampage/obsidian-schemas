---
id: WI-013
title: "Incremental Loading"
project: obsidian-schemas
stage: parked
created: 2026-03-22
last_touched: 2026-08-11
stage_changed: 2026-08-11
touched_by: session
tags: [performance]
depends_on: []
---

# Incremental Loading

## Problem / Motivation

The `refresh()` method reloads everything — every file gets re-parsed regardless of whether it changed. For a vault with hundreds of entity files, this is wasteful when only a few files were modified since the last load. Tracking file modification times and only reloading changed files would make refresh operations proportional to the number of changes, not the total vault size. This becomes increasingly important as the vault grows and as refresh gets called more frequently (e.g., with TTL-based cache or file watching).

## Parked — 2026-08-11 (queue review)

Un-park criterion: refresh() cost becomes measurable pain in a real consumer. Baseline 2026-08-11: full reload is 1.27s — no signal.
