---
id: WI-020
title: "Loud-fail hardening: parse, guard, and write-return boundaries"
project: obsidian-schemas
stage: idea
created: 2026-07-05
last_touched: 2026-07-05
stage_changed: 2026-07-05
touched_by: session
tags: [corruption-class, loud-fail, parser, writer]
depends_on: []
---

# Loud-fail hardening: parse, guard, and write-return boundaries

> **Model routing** (2026-07-05 campaign, `docs/backlog-campaign-2026-07-05.md`; self-sufficient):
> - **Explore: —** (the 2026-07-05 code-health review is the exploration; findings C2/C3/C4/C5/N4 below are the target list).
> - **Spec: Opus / high** — the one real design decision is quarantine semantics for malformed notes: raise-and-abort breaks consumer batch loads (HAL9000 startup walks the whole vault); silent-quarantine recreates the bug. Workspace doctrine (default-loud-fail; silent must be explicit) constrains the space; the spec picks the mechanism (e.g. load survives, malformed notes land in a loudly-surfaced quarantine list + WARN, mutation paths REFUSE to write through a failed parse).
> - **Spec-review: Opus / high. Build: Opus / high** — corruption-class, touches parser + writer + base repository.
> - Sequencing: Phase 1, first in queue. WI-004 (atomic write primitive) builds on the loud floor this establishes.

## Problem / Motivation

Five silent-degrade sites at the package's safety boundaries, found and file:line-verified by the 2026-07-05 campaign review. The first two interact to destroy data:

1. **C2 — malformed YAML silently degrades to "no frontmatter"** (`parser.py:78-80`: `yaml.YAMLError` → `({}, content)`). Every rebuild path trusts it: `base.update_fields` (base.py:255-273) and `writer.update_frontmatter_field(s)` (writer.py:247-295) do `parse_frontmatter → rebuild → write`, so a note whose YAML doesn't parse at update time gets rewritten as `---\n{only the updates}\n---\n{whole original file as body}` — **original frontmatter destroyed and duplicated into the body, silently.**
2. **C3 — the WI-126 body-shrink guard disables itself on read error** (`writer.py:189-190`: `except Exception: existing_body = ""`). The one mechanism protecting against body-wipe turns off exactly when it can't verify. Must raise (or refuse the write), never assume-empty.
3. **C4 — un-loadable notes vanish at DEBUG** (`base.py:125-126`; also `meeting.py:70-83`). A person invisible to the cache → `resolve()` misses → `find_or_create_stub` mints a duplicate — the dup-proliferation class WI-119/WI-125 exist to fight. WARN + surfaced count.
4. **C5 — `parse_to_model` swallows all validation errors** (`parser.py:139-150`: `except Exception → (None, dict)`). Same duplicate-creation consequence; hides schema drift entirely.
5. **N4 — write paths return silent False** (`writer.py:259-260, 298-299`; five body-section writers `person.py:1500-1839`): "duplicate/not-found" and "disk full / torn write" are the same `False`. Failure must raise or be distinguishable.

## Intent

A malformed or unwritable note is loud at the boundary where it's met: loads surface what they skipped, guards refuse rather than assume, writes that fail raise. No vault mutation is ever built on a parse that failed. Every fix ships its invariant test (malformed-YAML round-trip protection is the keystone regression).
