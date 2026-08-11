---
id: WI-026
title: "lint_vault.py --fix safety: route through the guarded primitive + a test floor for scripts"
project: obsidian-schemas
stage: idea
created: 2026-07-05
last_touched: 2026-07-05
stage_changed: 2026-07-05
touched_by: session
tags: [scripts, write-safety, testing]
depends_on: ["WI-004", "WI-020"]
---

# lint_vault.py --fix safety

> **Model routing** (2026-07-05 campaign, `docs/backlog-campaign-2026-07-05.md`; self-sufficient):
> - **Explore: —. Spec: Sonnet / medium. Spec-review: Opus / medium. Build: Sonnet / medium** + Opus code-review (standing rule).
> - Sequencing: Phase 4, after WI-004 (the primitive it must route through) and WI-020 (the malformed-YAML semantics it must respect).

## Problem / Motivation

`scripts/lint_vault.py` (1,198 LOC, zero tests — the largest untested file in the repo) mutates the whole real vault under `--fix`, and its write path shares WI-020's root cause: it reads via `parse_frontmatter`, mutates, and rewrites directly (lint_vault.py:869-875), bypassing the WI-126 body-shrink guard entirely. On a malformed-YAML note where a fix fires (e.g. `person_missing_name`, lint_vault.py:828-832, with `fm={}` and body = the whole raw file), `--fix` writes a file that **drops the original frontmatter** — the C2 corruption, gated only by a manual flag. It also re-serializes YAML across every touched file (rewriting hand-formatting) and silently skips unreadable files (`read_vault:112 except Exception: continue`). `scripts/migrate_person_to_discuss.py` (216 LOC, one-shot, already run) needs no investment beyond a header marking it historical. (2026-07-05 review finding H2 + test-suite risks #2/#3.)

## Intent

`--fix` cannot produce a write the library's own guards would refuse: it routes through the WI-004 primitive, refuses malformed-parse rewrites per WI-020, and carries a fixture-vault test for every fix rule it ships.

## Currency note — 2026-08-11 (queue review) — premise HALF-CLOSED by WI-004, re-scope at spec time

WI-004 routed lint_vault's writes through vault_io (lock + read_note + write_note-with-
precondition at lint_vault.py:819-900; quarantine's mkdir via ensure_dir at :1043): the C2
mechanical hazard this doc leads with — direct rewrite bypassing the WI-126 guard, frontmatter
drop on malformed YAML — is now door-guarded, and WI-020's parse semantics apply at the door.
File is now 1,221 LOC; every line citation above is stale. REMAINING scope for this item:
(1) a fixture-vault test floor for the fix RULES themselves (zero tests today — pairs with
WI-016); (2) the silent skip of unreadable files (`except Exception: continue`, now :116) made
loud per WI-020; (3) the YAML re-serialization of hand formatting concern. Deps (WI-004,
WI-020) both done. The spec-writer should treat this doc's Problem section as historical and
re-audit before writing.
