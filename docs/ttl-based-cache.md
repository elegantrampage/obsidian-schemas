---
id: WI-002
title: "TTL-based Cache"
project: obsidian-schemas
stage: idea
created: 2026-03-22
last_touched: 2026-03-22
stage_changed: 2026-03-22
touched_by: session
tags: [repository]
depends_on: []
---

# TTL-based Cache

## Problem / Motivation

The current cache model is all-or-nothing: data stays cached until explicitly refreshed. File watching (WI-001) solves this for local processes, but it adds a dependency on `watchdog` and filesystem events. A simpler middle ground is time-based cache invalidation — after a configurable TTL, the next query triggers a reload. This gives a `PersonRepository(vault_path, cache_ttl=300)` API that's lightweight, requires no external dependencies, and provides "good enough" freshness for most use cases without the complexity of real-time watching.
