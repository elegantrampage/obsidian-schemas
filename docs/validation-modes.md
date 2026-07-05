---
id: WI-011
title: "Validation Modes"
project: obsidian-schemas
stage: idea
created: 2026-03-22
last_touched: 2026-03-22
stage_changed: 2026-03-22
touched_by: session
tags: [schema-evolution]
depends_on: []
---

# Validation Modes

**Scope note 2026-07-05 (campaign review):** the adjacent-but-distinct malformed-YAML silent-degrade bug class (parser returns `({}, content)` on YAMLError; rebuild paths then destroy frontmatter) is NOT this item — it's corruption-class and owned by [WI-020](loud-fail-boundaries.md), queued Phase 1. This item remains the strict/lenient/warn *mode selector* for unknown fields, unqueued.

## Problem / Motivation

The current parser silently preserves unknown fields (lenient mode) — if a vault file has frontmatter keys the schema doesn't recognize, they pass through without any signal. This is safe but hides problems: typos in field names, leftover fields from old schemas, and fields that should have been migrated all go unnoticed. Different contexts need different strictness: a migration tool should be strict (fail on unknown), daily operations should be lenient (don't break on unexpected data), and development should warn (surface issues without blocking). Configurable validation modes (strict/lenient/warn) would let each consumer choose the right tradeoff.
