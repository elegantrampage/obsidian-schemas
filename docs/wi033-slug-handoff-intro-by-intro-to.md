---
id: WI-034
title: 'WI-033 slug handoff: the accessor reads intro-by / intro-to (+ counterparty
  slot), not [intro]'
project: obsidian-schemas
stage: idea
created: 2026-09-27
last_touched: 2026-09-27
stage_changed: 2026-09-27
touched_by: session
tags: []
depends_on: []
---

# WI-033 slug handoff — the timeline accessor reads `intro-by` / `intro-to`, not `[intro]`

## Problem / Motivation

HAL9000 WI-077 (shipped 2026-09-27) writes a third-party introduction as TWO kinds through the WI-058 renderer: `intro-by` on the introducee's note ("Introduced by [[@Stem|Name]] via <channel-id> (thread <id>)") and `intro-to` on the introducer's ("Introduced Dave to [[@Stem|Name]] via <channel-id> (thread <id>)"), dated by the event and keyed `{kind}:{day}:{counterparty}`. Dave signed the examples-of-done that fix those slugs (ac_hash `7aa1e054fde1`). The identity recommendation's premise sentence still says `[intro]`, and the legacy outbound writer (`routers/introduce.py`'s `/api/introduce`) keeps writing `[intro]`. WI-033's derived `introduced_by` accessor on `TimelineEntry` must read the two new slugs — and the `counterparty` machine slot beside them (WI-077 note 6) — or the door's records are invisible to the one reader the ruling makes canonical.

## Intent

The accessor answers "who introduced Dave to X" from the `intro-by` entry's counterparty slot, by kind, never by parsing the sentence; the outbound `[intro]` corpus stays readable as what it is; and HAL9000 and obsidian-schemas agree on the slugs once, in WI-033's text, not in two places.
