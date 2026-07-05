---
id: WI-027
title: "Weak-identity needs_resolution flip (WI-125 deferred follow-on)"
project: obsidian-schemas
stage: idea
created: 2026-07-05
last_touched: 2026-07-05
stage_changed: 2026-07-05
touched_by: session
tags: [identity, wi-125-followup, cross-project]
depends_on: []
---

# Weak-identity `needs_resolution` flip

**Unqueued (someday) — captured 2026-07-05 so the in-code deferral note stops being the only record.**

## Problem / Motivation

`resolve_or_create` still raises `WeakIdentityError` on weak-identity inputs — person.py:895-896 marks this "UNCHANGED this cut — the `needs_resolution` flip is a follow-on" (WI-125 Phase 3). The flip — create the stub anyway, flagged `needs_resolution: true`, instead of raising — is **caller-visible behavior** across all find_or_create_stub consumers (orchestrator contact_normalizer, HAL9000 entities, eventually the exocortex ingester per orchestrator WI-118). It changes what callers must handle (a flagged stub vs an exception) and what downstream review queues must exist (someone has to work the needs_resolution list, or it becomes silent debt — the flip without the queue is worse than the raise).

Do not schedule from this repo alone: sequence with the orchestrator-side caller migration (WI-118 there) so the contract changes once, for everyone. Routing assigned when queued.

## Intent

Weak identities become visible work items in a reviewed queue instead of hard failures — but only once every caller and a review surface exist to receive them.
