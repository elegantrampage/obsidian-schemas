---
id: WI-004
title: "Concurrent & external write safety (atomic writes, locking, stale-read protection)"
project: obsidian-schemas
stage: idea
created: 2026-03-22
last_touched: 2026-07-05
stage_changed: 2026-03-22
touched_by: session
tags: [repository, write-safety, corruption-class]
depends_on: ["WI-020"]
---

# Concurrent & external write safety

> **Model routing** (2026-07-05 campaign, `docs/backlog-campaign-2026-07-05.md`; self-sufficient):
> - **Explore: FABLE (claude-fable-5) / high** — justified by the fork it resolves: per-file `flock` vs single-writer process vs optimistic mtime-precondition vs temp-file+rename-only, × how the chosen frame coexists with Obsidian's own editor writes (absorbed WI-015). Genuinely open (four plausible frames with different consumer-facing semantics), expensive to reframe once three consumer repos depend on the semantics, and its failure mode — silent data loss — is by nature hard to detect downstream. Fable is explorer only here; the spec-review is deliberately a different model.
> - **Spec: Opus / high.** **Spec-review: Opus / xhigh** — the campaign's single xhigh: this primitive becomes the door every vault mutation walks through; a correlated miss here corrupts the live vault for all consumers.
> - **Build: Opus / high** — core write machinery.
> - Sequencing: after WI-020 (loud-fail floor first, so the primitive's failure modes surface instead of degrading). WI-021's write-door consolidation routes through the primitive this item ships.

**Resliced 2026-07-05 (campaign review).** The March framing (in-process thread-safety for the FastAPI server) is a subset of the real problem the code-health review confirmed: **every write in the package is an unlocked, non-atomic read-modify-write** (`base.py:254-273` update_fields, `writer.py:217/246-295/322`, five body-section writers in `person.py:1495-1831`, `scripts/lint_vault.py:875`), with zero locking of any kind (grep-verified), while HAL9000, orchestrator, and CLI sessions write the same live vault concurrently — and Obsidian itself edits the same files (absorbs **WI-015 Obsidian Plugin Sync**, parked → merged here; same root cause, same mechanism).

## Problem / Motivation

The repository layer currently assumes single-threaded use — no locking, no thread-safe cache operations. HAL9000 runs as a FastAPI server handling concurrent requests, which means multiple request handlers can read and write the same repository cache simultaneously. This creates race conditions: a refresh triggered by one request can corrupt the cache mid-read by another. Thread-safe cache operations with read-write locks are needed to make repositories safe for multi-threaded servers without serializing all access behind a single lock.

**Expanded scope (2026-07-05):**

1. **Lost-update class:** process A reads a note, process B appends a Timeline entry and writes, process A writes back a frontmatter-only change built from the stale body → B's edit silently gone. Same class with Obsidian as the second writer (ex-WI-015).
2. **Torn-write class:** a crash mid-`Path.write_text` leaves a truncated note. No temp-file+rename anywhere.
3. **Consolidation rider:** the package has **six hand-rolled `content.split("---", 2)` frontmatter splits** in the body-section writers (`person.py:1564-1805`) plus a seventh section-splitter in `append_to_timeline` (`person.py:1481-1494`), each a divergence risk from the canonical parser. The new primitive is the one door they all route through — solve-in-one-place.
4. In-process thread-safety (the original March scope) rides along: whatever locking frame the explore picks must also cover the repository cache races.

## Intent

One atomic, guarded, lock-aware write primitive; every vault mutation in the package routes through it; a concurrent or external edit can no longer be silently destroyed, and a crash can no longer tear a note.
