---
id: WI-008
title: "Exploration Entity Type"
project: obsidian-schemas
stage: idea
created: 2026-03-22
last_touched: 2026-03-22
stage_changed: 2026-03-22
touched_by: session
tags: [repository]
depends_on: []
---

# Exploration Entity Type

**Premise updated 2026-07-05 (campaign review):** the model is now committed — `Exploration` exists at `models.py:266`, wired into `EntityType` (models.py:306) and `TYPE_TO_MODEL` (models.py:317). Residual scope is smaller than described: repository + tests + writer round-trip. The missing model *test* is folded into WI-016's fixture-vault scope.

## Problem / Motivation

The Exploration entity type is partially implemented — a Pydantic model exists but hasn't been committed. It's missing a repository, tests, and writer support. Explorations are living documents in the `explorations/` folder that capture ideas that may become projects. Without a proper entity type and repository, there's no programmatic way to query or manage explorations — they're invisible to the typed API layer. This matters for the orchestrator's project-manager agent and for any tooling that needs to surface "what's being explored" across the workspace.
