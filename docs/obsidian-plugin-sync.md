---
id: WI-015
title: "Obsidian Plugin Sync"
project: obsidian-schemas
stage: parked
created: 2026-03-22
last_touched: 2026-09-06
stage_changed: 2026-07-05
touched_by: session
tags: [integration]
depends_on: []
---

# Obsidian Plugin Sync

**Status: CLOSED 2026-09-06 (queue review, Dave's word) — superseded by WI-004 (`b87fb77`, shipped 2026-08-11).** Merged into WI-004 on 07-05; WI-004 is done. Its derivation stamps and `ExternalWriteConflict` cover the detection half of this item (a write against a note another writer changed is refused, never clobbered). The coordination half has nothing to build: Obsidian exposes no lock or write-intent primitive, and its truncate-in-place write was observed and declared WI-004's residual. Closed.

**Status: Parked 2026-07-05 (campaign review) — merged into [WI-004](concurrent-access.md).** Same root cause (unlocked read-modify-write against files another writer may touch), same mechanism (atomic write + stale-read detection); WI-004's resliced scope covers the writer-vs-Obsidian case explicitly. Note WI-126 (body-preserving write primitive, shipped 2026-06) already narrowed this item's blast radius — it closes the writer-vs-itself silent-body-wipe class, not the writer-vs-Obsidian one.

## Problem / Motivation

Both obsidian-schemas (via writer) and Obsidian itself can write to the same vault files simultaneously. There's no coordination — if the writer updates a person's frontmatter while Obsidian has the file open, one write can silently overwrite the other. The risk increases as more automation writes to the vault (HAL9000 enrichment, contact detection, intro workflows). Detecting when Obsidian has the vault open and coordinating writes — or preferring Obsidian's API via MCP where possible — would prevent silent data loss from conflicting writes.
