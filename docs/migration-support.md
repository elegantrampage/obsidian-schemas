---
id: WI-010
title: "Migration Support"
project: obsidian-schemas
stage: parked
created: 2026-03-22
last_touched: 2026-08-11
stage_changed: 2026-08-11
touched_by: session
tags: [schema-evolution]
depends_on: []
---

# Migration Support

## Problem / Motivation

Schema changes are inevitable — fields get added, renamed, restructured. Currently there's no way to detect which vault files have outdated schemas or to migrate them automatically. When a schema change lands, every consumer silently gets partial data from old-format files until someone manually updates them. A `schema_version` field in frontmatter, combined with detection of outdated schemas and migration scripts, would make schema evolution safe and explicit. Without this, every schema change is a potential data integrity issue across hundreds of vault files.

## Parked — 2026-08-11 (queue review)

Un-park criterion: the first real schema migration that must walk the vault (none has occurred; WI-024/020/004 all changed code contracts, not stored frontmatter shape).
