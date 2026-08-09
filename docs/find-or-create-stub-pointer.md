---
id: WI-019
title: "find_or_create_stub: lookup-before-create entry point for all 4 stub-creation paths"
project: obsidian-schemas
stage: done
created: 2026-06-01
last_touched: 2026-07-05
stage_changed: 2026-06-01
touched_by: session
tags: [person-repository, dedupe-prevention, root-fix]
depends_on: ["WI-018"]
---

# find_or_create_stub: lookup-before-create entry point

**Pointer stub (created 2026-07-08).** Built and documented in
`../orchestrator/docs/find-or-create-stub.md`; this stub exists so obsidian-schemas'
docs/ is the complete source of truth for its own state file (see WI-018 stub for the
regenerate_state fail-closed rationale).

## Problem / Motivation

Lookup-before-create entry point built on resolve_all (WI-018). Replaces ad-hoc
create_stub calls scattered across 4 paths (orchestrator contact_normalizer +
contact-detector + HAL9000 entities + exocortex Granola ingester). Cascade: get_by_email
→ get_by_phone → resolve_all with company hint at threshold ≥0.85 → fall through to
create_stub. Identifier write-back: on reuse, if call supplied new email/phone not on
canonical, append and save.

DONE 2026-06-01: 5 tests added test-first, commit ec4393a.

2026-07-05 campaign note: library side since reshaped into the WI-125 engine adapter
(person.py:678). Caller migration is HALF done and owner-elsewhere: paths 1
(contact_normalizer) + 3 (HAL9000 entities, with a create_stub fallback branch at
entities.py:203) migrated; path 2 (contact-detector role) and path 4 (exocortex Granola
ingester — highest-frequency caller) NOT migrated, tracked as orchestrator WI-118
(blocked on shadow harness). See campaign doc Cross-project signals.

## Design

Pointer stub — design lives in `../orchestrator/docs/find-or-create-stub.md` (built and
documented from orchestrator sessions; see stub header for the regenerate_state rationale).

## Approach

Pointer stub — see `../orchestrator/docs/find-or-create-stub.md`.

## Implementation Plan

Pointer stub — executed 2026-06-01, commit ec4393a (5 tests, test-first); plan recorded in
`../orchestrator/docs/find-or-create-stub.md`.
