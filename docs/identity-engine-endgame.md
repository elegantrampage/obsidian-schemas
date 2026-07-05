---
id: WI-023
title: "Identity engine endgame: delete the legacy cascade, cut over the unified index"
project: obsidian-schemas
stage: idea
created: 2026-07-05
last_touched: 2026-07-05
stage_changed: 2026-07-05
touched_by: session
tags: [identity, wi-125-followup, strangler-completion]
depends_on: []
---

# Identity engine endgame

> **Model routing** (2026-07-05 campaign, `docs/backlog-campaign-2026-07-05.md`; self-sufficient):
> - **Explore: —** (the design was pre-recorded in the WI-125 strangler plan, person.py:181-184, and the 2026-07-05 architecture review maps the seams; the parity replay already PASSED — 942 inputs, 0 diffs, `orchestrator/state/identity-parity.json`).
> - **Spec: Opus / high. Spec-review: Opus / high. Build: Opus / medium** — deletion cut over identity machinery: mostly removal with a strong parity net, but the index cutover changes which code resolves email/phone, so the spec must state the parity evidence per cut.
> - Sequencing: Phase 3, after the Phase 1 floor. **WI-025 (person.py decomposition) is gated on this** — delete the duplicate before moving what remains.

## Problem / Motivation

WI-125 landed as a strangler: engine live, old paths retained, index dormant. The 2026-07-05 architecture review confirmed the retained half is now an **active maintenance tax** — WI-121 had to be threaded through the legacy body and the engine "symmetrically" by hand, with nothing forcing the two copies to agree. Scope:

1. **Delete `_find_or_create_stub_legacy`** (person.py:719, ~125 lines, "NOT called in production"). Its purpose (Phase-5 parity baseline + one-commit rollback) is served: the offline parity replay passed.
2. **Cut email/phone resolution over to the unified `_identifier_index`** — today `_resolve_identifier` (person.py:966-986) delegates back to the legacy fuzzy `get_by_email`/`get_by_phone`, so the index's only live effect is conflict observability. The spec must resolve the phone question: `Phone.key` is raw digits (identifier.py:248) and can't express `phones_match`'s UK-0/44 and US-1 equivalence (person.py:124-156) — either key-normalize into the index or keep phones on the fuzzy path *explicitly and documentedly*. Then collapse the per-kind dicts into views (the plan person.py:181-184 records) or record why not.
3. **Consolidate the resolution cascades** (review finding N5): `resolve()` (person.py:478-530) and `resolve_all()` (person.py:532-676) maintain separately-drifting match logic; make `resolve` a thin head of `resolve_all`.
4. **Break the lazy-import cycle**: move `normalize_phone`/`phones_match` (person.py:105-156) to a small util module so `identifier.py` stops importing backwards from a 1,839-line repo module (identifier.py:234-236).
5. **Riders:** fix the dangling doc reference at person.py:78 (`docs/paren-decoration-at-the-door.md` does not exist); keep or explicitly retire the slack-index carve-out note (person.py:260).

## Intent

One find-or-create implementation, one resolution cascade, an identifier index that is actually the resolution authority (or documentedly not, per kind), no import cycle — with the parity replay re-run green after each cut.
