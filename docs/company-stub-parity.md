---
id: WI-022
title: "Company stub parity: retire the deleted name-mangler, add validation + provenance"
project: obsidian-schemas
stage: idea
created: 2026-07-05
last_touched: 2026-07-05
stage_changed: 2026-07-05
touched_by: session
tags: [company-repository, data-quality, small-mechanical]
depends_on: []
---

# Company stub parity

> **Model routing** (2026-07-05 campaign, `docs/backlog-campaign-2026-07-05.md`; self-sufficient):
> - **Explore: —. Spec: Sonnet / low** (template: the Person-side WI-105/WI-111/WI-119 pattern, applied to Company). **Spec-review: Opus / medium. Build: Sonnet / medium** + Opus code-review (standing rule). Leaf build with executable ACs.
> - Sequencing: Phase 2; independent of WI-004/WI-021 — schedule opportunistically.

## Problem / Motivation

`CompanyRepository.create_stub` (company.py:171) still runs `re.sub(r'[^\w\s-]', '', name)` — the **exact mangler regex WI-111 deleted from the Person side** (person.py:1381-1388 documents the deletion and why). Consequences on real inputs: "O'Reilly Media"→"OReilly Media", "AT&T"→"ATT", "Yahoo!"→"Yahoo" — persisted as canonical name AND filename. The Company path also bypasses NameValidator entirely and writes no `created_by` provenance (WI-119 covered Person only). Company names differ from person names (punctuation is often load-bearing), so the fix is a company-appropriate cleaning contract, not a blind copy — but the shape (parse-don't-mangle at the boundary, provenance on create) is the shipped Person pattern.

2026-07-05 review finding N1; corruption of company names on write, one call site, well-tested neighboring pattern to follow.

## Intent

Company stubs get the same boundary discipline persons got: no lossy character-class stripping, a validating cleaning step, `created_by` provenance, and invariant tests on the punctuation cases the mangler destroyed.
