---
id: WI-028
title: Person-resolution policy moves into the library
project: obsidian-schemas
stage: idea
created: 2026-08-31
last_touched: 2026-08-31
stage_changed: 2026-08-31
touched_by: session
tags: []
depends_on: []
---

# Person-Resolution Policy Moves Into the Library

## Problem / Motivation

Person MATCHING lives in one place (this library's PersonRepository.resolve_all), but resolution POLICY lives in two: HAL9000's WI-057 seam (core/person_resolution.py — the 0.85 cutoff, refuse-with-ranked-candidates on anything but exactly-one-match) and exocortex's transcript ingestion (transcript.py _find_or_create_contact — email-first lookup, >=0.85 acceptance, company-hint plausibility, a skip-gate routing low-quality names to review instead of stubbing). Two policy copies drift; the 2026-08-31 three-way session discussion (orchestrator/HAL9000/exocortex, transcript emailed to Dave) converged on unifying policy at the library level rather than forcing exocortex's pipeline through HAL9000's HTTP door (which would couple ingestion availability to HAL9000 uptime and split read/write brains).

## Intent

Exactly one set of person-resolution rules, in the shared library, so HAL9000's seam and exocortex's ingestion consume the same policy and cannot drift. Downstream consumers keep their own error-handling surfaces (HTTP outcomes, review queues) but no longer own thresholds or acceptance semantics. Deferred-but-noted extensions for when something needs them (not in scope unless pulled in): batch resolution, LinkedIn/Slack identifiers in the cascade, structured multi-identifier queries.
