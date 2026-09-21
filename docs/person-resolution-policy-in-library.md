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

**Premise re-verified 2026-09-21 (queue review, Dave's word "proceed with your recommendation") — it
holds and is STRONGER than written; only the citations had moved.** Read this paragraph as the premise
and the original below as the 2026-08-31 record. There are now THREE policies, not two: (1) this
library's own — since WI-023 (2026-09-11) `PersonRepository.resolve` is one cascade over
`resolve_all` plus a NAMED selection policy (`repositories/person.py:150`), and `find_or_create_stub`
carries its own `confidence_threshold`/`threshold` defaults of 0.85 (`person.py:729`, `:787`);
(2) HAL9000's WI-057 seam, now at `backend_fastapi/core/person_resolution.py` —
`PERSON_RESOLVE_CUTOFF = 0.85` at `:46`, exactly-one-candidate-at-or-above-cutoff else refuse with
ranked candidates (`:134`); (3) exocortex's transcript ingestion, now at
`exocortex/ingestion/stages/resolve.py` — `resolve_attendees_by_name` (`:96`) with email-first lookup,
then `resolve_all` with a company hint and `candidates[0].confidence >= 0.85` acceptance (`:243-250`,
"mirrors find_or_create_stub default"), and the skip-gate routing low-quality names to review
(`:236-240`). The `transcript.py:_find_or_create_contact` name the paragraph below cites no longer
exists; the logic moved to the stage module. The drift is live and falsifiable in ten seconds: on TWO
candidates both at or above 0.85, HAL9000 REFUSES and exocortex TAKES THE TOP — the same person, two
answers, depending on which door asked.

## Problem / Motivation

Person MATCHING lives in one place (this library's PersonRepository.resolve_all), but resolution POLICY lives in two: HAL9000's WI-057 seam (core/person_resolution.py — the 0.85 cutoff, refuse-with-ranked-candidates on anything but exactly-one-match) and exocortex's transcript ingestion (transcript.py _find_or_create_contact — email-first lookup, >=0.85 acceptance, company-hint plausibility, a skip-gate routing low-quality names to review instead of stubbing). Two policy copies drift; the 2026-08-31 three-way session discussion (orchestrator/HAL9000/exocortex, transcript emailed to Dave) converged on unifying policy at the library level rather than forcing exocortex's pipeline through HAL9000's HTTP door (which would couple ingestion availability to HAL9000 uptime and split read/write brains).

## Intent

Exactly one set of person-resolution rules, in the shared library, so HAL9000's seam and exocortex's ingestion consume the same policy and cannot drift. Downstream consumers keep their own error-handling surfaces (HTTP outcomes, review queues) but no longer own thresholds or acceptance semantics. Deferred-but-noted extensions for when something needs them (not in scope unless pulled in): batch resolution, LinkedIn/Slack identifiers in the cascade, structured multi-identifier queries.
