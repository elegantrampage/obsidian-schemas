---
id: WI-006
title: "Relationship Tracking"
project: obsidian-schemas
stage: idea
created: 2026-03-22
last_touched: 2026-03-22
stage_changed: 2026-03-22
touched_by: session
tags: [entity-relationships]
depends_on: [WI-005]
---

# Relationship Tracking

## Problem / Motivation

The schema captures static attributes of people and companies but not the relationships between them. "Who introduced me to this person?" and "Who do I know at Company X?" are natural questions that the current model can't answer without manual vault searching. Tracking relationships like "introduced by" and "works at" (with dates, so employment history is preserved) would enable graph-like queries over the vault. This is foundational for relationship intelligence — Exocortex needs this data to surface connection paths and network insights.
