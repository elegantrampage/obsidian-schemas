---
id: WI-009
title: "Professional Role & Seniority Fields"
project: obsidian-schemas
stage: idea
created: 2026-03-22
last_touched: 2026-03-22
stage_changed: 2026-03-22
touched_by: session
tags: [schema]
depends_on: []
---

# Professional Role & Seniority Fields

> **Model routing** (2026-07-05 campaign, `docs/backlog-campaign-2026-07-05.md`; self-sufficient):
> - **Explore: Opus / low** — a short taxonomy decision with Dave (list-vs-scalar profession, enum-vs-free-text seniority), driven by how the headhunter agent actually queries.
> - **Spec: Sonnet / medium. Spec-review: Opus / medium. Build: Sonnet / medium** + Opus code-review (standing rule). Leaf schema addition with executable ACs (field + index + tests + README), pattern identical to the shipped slack-field addition (SESSION_LOG 2026-01-26).
> - Sequencing: Phase 5 (capability). **Cross-project note:** this is a consumer-facing schema change — HAL9000/Exocortex ContactInfo dataclasses historically mirror new Person fields; the spec must list the downstream mirror updates.
> - Verified unshipped 2026-07-05: `models.py:78-90` has no `profession`/`seniority`; the existing `roles` field is behavior-modifier roles (vip, family…), not profession.

## Problem / Motivation

The Person schema has no structured fields for what someone does professionally or their seniority level. This blocks job-matching use cases — the headhunter agent can't programmatically filter "senior engineers" or "VP-level product people" from the network. Adding `profession` and `seniority` fields would enable this, but the design has open questions: should profession be a list (people wear multiple hats) or single value? Should seniority be free text or an enum? Enums are queryable but rigid; free text is flexible but hard to filter. The right answer likely depends on how the headhunter agent will actually consume this data.
