---
id: WI-024
title: "Remove the hardcoded live-vault default path (loud-fail when unconfigured)"
project: obsidian-schemas
stage: idea
created: 2026-07-05
last_touched: 2026-07-05
stage_changed: 2026-07-05
touched_by: session
tags: [loud-fail, configuration, small-mechanical]
depends_on: []
---

# Remove the hardcoded live-vault default path

> **Model routing** (2026-07-05 campaign, `docs/backlog-campaign-2026-07-05.md`; self-sufficient):
> - **Explore: —. Spec: —** (this doc + a consumer audit list is the spec: grep HAL9000/exocortex/orchestrator for no-arg repository construction before flipping). **Spec-review: Opus / low. Build: Sonnet / low** + Opus code-review (standing rule).
> - Sequencing: Phase 1 (protect the floor). **Dave signed off 2026-07-05** on the breaking change (campaign session). Build prerequisite stands: audit and fix any no-arg repository construction in all 3 consumers before flipping the loud-fail.

## Problem / Motivation

`DEFAULT_VAULT_PATH = "/Users/davewascha/Documents/Obsidian/DaveRemoteVault"` (base.py:21) is the fallback whenever a repository is constructed with no path and `OBSIDIAN_VAULT_PATH` is unset — a machine-specific absolute path baked into a library three repos install, pointing at the **live vault**. Any consumer that forgets configuration silently reads and writes Dave's real data; no test asserts the fallback (tests always pass explicit paths), so nothing would catch a misconfigured caller. Duplicated at `scripts/lint_vault.py:50`. (2026-07-05 review findings H1 + test-suite risk #1.)

Fix shape: unconfigured construction raises with a clear message (constructor arg or env var required); both scripts get the same treatment; an invariant test pins it.

## Intent

It is impossible to touch the live vault by accident of omission — a repository without an explicit path or env var loud-fails at construction.
