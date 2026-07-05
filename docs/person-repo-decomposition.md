---
id: WI-025
title: "Decompose person.py (1,839 LOC, five concerns)"
project: obsidian-schemas
stage: idea
created: 2026-07-05
last_touched: 2026-07-05
stage_changed: 2026-07-05
touched_by: session
tags: [architecture, maintainability]
depends_on: ["WI-023"]
---

# Decompose person.py

> **Model routing** (2026-07-05 campaign, `docs/backlog-campaign-2026-07-05.md`; self-sufficient):
> - **Explore: —** (the 2026-07-05 architecture review names the five concerns; the cut plan falls out of WI-023's deletions). **Spec: Opus / medium. Spec-review: Opus / medium. Build: Opus / medium** — pure-move refactor over identity machinery; 563-test suite is the net; WHY-comments (WI/date references) move with their code.
> - Sequencing: Phase 4, **strictly after WI-023** — delete the legacy duplicate and dormant-index ambiguity first, then move what remains. Do not reorder.

## Problem / Motivation

`repositories/person.py` is 1,839 LOC — 2.6× the workspace ~700-line ceiling — and the package's fan-in hub (imports six internal modules). It holds five separable concerns: index maintenance, the resolve cascades, the WI-125 identity engine, stub creation/name cleaning, and body-section CRUD (timeline / to-discuss writers). The 2026-07-05 review traced two live costs: the `identifier.py` lazy-import cycle exists only because `normalize_phone` is stranded here (fixed in WI-023), and every AI session that touches person resolution must load a file holding four unrelated concerns. Natural split: indexes+resolution / engine / stub-creation / body-ops, with `base.py` untouched.

## Intent

No file over ~700 LOC in the package; each concern findable by name; zero behavior change (suite green, no test edits except imports).
