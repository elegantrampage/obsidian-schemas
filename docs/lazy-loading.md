---
id: WI-003
title: "Lazy Loading"
project: obsidian-schemas
stage: idea
created: 2026-03-22
last_touched: 2026-03-22
stage_changed: 2026-03-22
touched_by: session
tags: [repository]
depends_on: []
---

# Lazy Loading

## Problem / Motivation

Repositories currently load all entities from disk on first access — every markdown file gets parsed, even if the caller only needs one person. For large vaults this means slow startup and high memory use. Lazy loading would parse individual files on demand, trading faster startup for slower first queries on specific entities. The design tradeoff is meaningful: bulk operations (reporting, search) benefit from eager loading, while lookup-by-name use cases benefit from lazy loading. The right answer may be a configurable strategy or hybrid approach.
