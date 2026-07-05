---
id: WI-014
title: "HAL9000 Singleton"
project: obsidian-schemas
stage: parked
created: 2026-03-22
last_touched: 2026-07-05
stage_changed: 2026-07-05
touched_by: session
tags: [integration]
depends_on: []
---

# HAL9000 Singleton

**Status: Parked 2026-07-05 (campaign review) — premise eroded + wrong repo.** The headline premise ("no `get_person_repository()` factory") is outdated: HAL9000 now has a repository factory/registry (`hal9000/backend_fastapi/core/entity_registry.py:34 get_repository(entity_type)`). Whatever lifecycle work remains (shared cache, coordinated refresh) is HAL9000's to own — solve-in-one-place says the consuming repo manages its own repository lifecycle. If HAL9000-side gaps surface, capture there and cross-link. The library-side concurrency prerequisite this item pointed at lives on as WI-004.

## Problem / Motivation

HAL9000's FastAPI server creates repository instances ad-hoc across different endpoints and services. There's no centralized lifecycle management — no shared cache, no coordinated refresh, no single place to configure vault paths. A `get_person_repository()` factory function that returns a global singleton, configured from environment variables, would give all HAL9000 code a single repository instance with shared cache and consistent configuration. This is a prerequisite for concurrent access safety (WI-004) and makes it practical to add features like TTL-based cache (WI-002) in one place.
