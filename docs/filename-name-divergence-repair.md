---
id: WI-029
title: 'Filename/name divergence repair: rename the forked stems, then pin the invariant'
project: obsidian-schemas
stage: idea
created: 2026-09-06
last_touched: 2026-09-06
stage_changed: 2026-09-06
touched_by: session
tags: []
depends_on: []
---

# Filename/name divergence repair: rename the forked stems, then pin the invariant

## Problem / Motivation

Three live person notes carry a filename stem that differs from their stored `name:` — measured as
G4(b) in WI-021's 2026-08-11 shell pass and re-confirmed 2026-09-05: `@Dave Martin Right to Left.md`
vs `name: …Right To Left`, `@Maritza.md` vs `name: Maritza Bonano`, `@Owen OLoan.md` vs
`name: Owen O'Loan`. `BaseRepository.save` binds the target filename from the raw `entity.name`
(`base.py:381`) and never renames or unlinks, and WI-021's gate declines by design to repair a name
(its name output is an identity), so each of these notes forks into a SECOND note for one person on
its next `save()` — WI-021's "parked defect 1" corruption class, live today rather than
hypothetical. WI-021 explicitly scoped this out ("no rename, no backfill, no sweep") and named it
as the next item's neighbourhood.

The same shell passes booked four hand repairs that have no home and should ride with this item
so they are not lost: one book note carrying `type: person` (`The New York Trilogy - Paul
Auster.md`, `name: Nicole Stocker`, G5(a)), four notes with frontmatter but no `type:` (G1 bucket
(b), live), and three book notes whose frontmatter fence opened and did not parse (G1 bucket (d)).

**Queue review 2026-09-21 (Dave: ranking agreed — this item is now FIRST in `queue_order`; "proceed
with your recommendation" on the fold below).** Premise re-verified: the class has GROWN — the census
(`docs/vault-shape-census.md:262`, measured 2026-09-07) counts **8 live** stem≠name person notes against
the three named above, and `BaseRepository.save` still binds the filename from `entity.name`
(`base.py:381`). FOLD, counts only: load-time identity-reconciliation conflicts
(`PersonRepository.conflicts`, the load-time kind — one identifier on more than one note) are the
same duplicate-note class as a forked stem, so this item's conductor entry/exit measurement records
`len(PersonRepository().conflicts)` beside the divergence count, and the invariant test asserts it is
zero over the corpus. On 2026-09-21 one such pair was observed at the morning load (a two-note
conflict, last-wins) and had been merged by the re-check an hour later (1,172 → 1,171 person notes,
conflicts 0) — nothing to repair by hand today, and exactly the shape that should be visible on a
readout rather than in a log line nobody reads.

## Intent

A person note's filename and its stored name agree, everywhere in the live vault, and stay that
way: the three forked notes are renamed once through the one sanctioned door (`vault_io.move_note`,
old stem preserved as an alias so nothing that referenced the old file goes dark), and an invariant
test over the corpus goes red the moment the class recurs — so this is the last time it is repaired
by hand. The booked hand repairs are done in the same pass and the counts that found them are
re-run to zero.
