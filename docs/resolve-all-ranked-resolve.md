---
id: WI-018
title: "PersonRepository.resolve_all() — multi-candidate ranked resolve with company-hint disambiguation"
project: obsidian-schemas
stage: done
created: 2026-06-01
last_touched: 2026-06-01
stage_changed: 2026-06-01
touched_by: session
tags: [person-repository, dedupe-prevention, root-fix]
depends_on: []
---

# PersonRepository.resolve_all() — multi-candidate ranked resolve

**Pointer stub (created 2026-07-08).** This item was built and documented alongside
WI-019 in `../orchestrator/docs/find-or-create-stub.md` (the cross-repo doc both items'
state entries pointed at). This stub exists so obsidian-schemas' docs/ is the complete
source of truth for its own state file — `regenerate_state` refused to run (correctly,
fail-closed) while two state entries had no doc in this project's docs/.

## Problem / Motivation

resolve_all returns List[ResolveCandidate] with all plausible matches ranked by
confidence. Token-subset matching, short-form "First L" partial-match, company-hint bump
+0.25.

DONE 2026-06-01: 9 tests added test-first, commit ec4393a. Foundation for WI-019
find_or_create_stub. Full narrative: `../orchestrator/docs/find-or-create-stub.md`

## Design

Pointer stub — design lives in `../orchestrator/docs/find-or-create-stub.md` (this item is
its WI-018 foundation half; built and documented from orchestrator sessions).

## Approach

Pointer stub — see `../orchestrator/docs/find-or-create-stub.md`.

## Implementation Plan

Pointer stub — executed 2026-06-01, commit ec4393a (9 tests, test-first); plan recorded in
`../orchestrator/docs/find-or-create-stub.md`.
