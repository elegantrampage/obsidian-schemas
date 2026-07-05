---
id: WI-005
title: "Cross-Repository Linking"
project: obsidian-schemas
stage: idea
created: 2026-03-22
last_touched: 2026-03-22
stage_changed: 2026-03-22
touched_by: session
tags: [entity-relationships]
depends_on: []
---

# Cross-Repository Linking

## Problem / Motivation

Entity relationships are currently string-based — a person's company field is just a name, not a resolved reference. Calling `person.company` returns `"Acme Corp"`, not the actual Company entity. To get the Company object you need to manually query CompanyRepository with that string, which is fragile and duplicates resolution logic across consumers. Cross-repository linking (`person.get_company() -> Company`) would make these relationships first-class, but requires repositories to know about each other. This points toward a unified `VaultRepository` that manages all entity types and can resolve cross-type references automatically.
