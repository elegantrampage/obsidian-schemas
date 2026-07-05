---
id: WI-016
title: "Frozen anonymized real-data fixture vault"
project: obsidian-schemas
stage: idea
created: 2026-03-22
last_touched: 2026-07-05
stage_changed: 2026-03-22
touched_by: session
tags: [testing, real-data-fixtures]
depends_on: []
---

# Frozen anonymized real-data fixture vault

> **Model routing** (2026-07-05 campaign, `docs/backlog-campaign-2026-07-05.md`; self-sufficient):
> - **Spec: Opus / high** — the anonymization design handles real personal data destined for a tracked repo; a bad frame either leaks personal data into git history (hard to undo) or produces fixtures that lose the exact failure-catching properties (diacritics, RFC 2822 leaks, mangled stubs) that motivate the item. **Coordinate with exocortex WI-034** (same item shape, same vault, same anonymization problem) — one shared design, not two.
> - **Spec-review: Opus / medium. Build: Sonnet / medium** + Opus code-review (standing rule).
> - Sequencing: Phase 3 (test floor). Unlocks property-based testing and gives every later name/identity-touching change its regression corpus.

**Resliced 2026-07-05 (campaign review).** Since March, real-data-shaped fixtures have emerged organically inline (José García, Anne-Sophie Legrain Vetup, RFC 2822 leak strings, the Moises Garcia ×3 collision) — the convention exists but the corpus is scattered literals, not a frozen shared sample. The residual ask: a **frozen anonymized ~50-note fixture vault** (persons + companies + meetings, including malformed-frontmatter and mangled-stub specimens) that every relevant test runs against, per the workspace real-data-fixtures rule. Include round-trip coverage for the untested `Exploration` model (models.py:266). Property-based testing (Hypothesis) stays in scope as a stretch, not the core.

## Problem / Motivation

Tests currently use small, hand-crafted fixture files that cover basic cases but miss edge cases and performance characteristics of real vaults. There's no shared test vault that multiple test suites can reference, no larger dataset for performance testing, and no property-based testing for exploring edge cases systematically. A shared fixture vault with realistic data, combined with property-based testing (e.g., Hypothesis), would catch parsing bugs that only appear with unusual frontmatter combinations and give confidence that performance optimizations actually help at realistic scale.
