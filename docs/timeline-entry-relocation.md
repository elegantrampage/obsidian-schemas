---
id: WI-033
title: TimelineEntry relocates into the library, with a derived introduced_by accessor
project: obsidian-schemas
stage: idea
created: 2026-09-26
last_touched: 2026-09-28
stage_changed: 2026-09-26
touched_by: session
tags: []
depends_on: []
---

# TimelineEntry relocates into the library, with a derived introduced_by accessor

## Problem / Motivation

The vault's timeline-entry vocabulary — the `### {Month D, YYYY} [{kind}]` heading, the
`<!-- {kind}:{YYYY-MM-DD}:{discriminator} -->` dedupe marker, the kind-slug validation and the
`intro:{date}:{name}` key — lives in HAL9000's WI-058 door (`backend_fastapi/core/timeline_entry.py`,
`TimelineEntry`), not in this library: `obsidian_schemas` ships only
`PersonRepository.append_to_timeline(person, entry, deduplicate_key)`, a raw string appender with substring
dedupe (`repositories/person.py:1371-1415`), and `body_sections.py` knows sections, not entry kinds. That
was fine while HAL9000 was the only writer. Dave's 2026-09-26 ruling (threaded review; premise doc
`/Users/davewascha/Workspaces/mainspring/docs/identity-and-identifiers-recommendation-2026-09-26.md`,
disagreement 3) adds a second use: inbound third-party introductions are recorded as `[intro]` timeline
entries on BOTH parties (introducee "Introduced by [[X]] via email", introducer "Introduced Dave to [[Y]]",
discriminator `intro-in:<date>:<other>`) with NO stored `introduced_by` field, and consumers that need
"who introduced this person" — exocortex's relationship edges (the parked WI-006), orchestrator's capture,
HAL9000's own readers — must DERIVE it. A consumer deriving it today would parse a comment convention
another project owns: a boundary violation by construction, and two copies of the parser the day a second
consumer needs it.

Ruled, obsidian-schemas mints: (1) `TimelineEntry` RELOCATES from HAL9000 into `obsidian_schemas` —
the typed entry (kind, text, injectable `when`, optional discriminator), its render, its kind-slug and
discriminator validation (the `-->`/`<!--` forgery guard), and the dedupe-by-discriminator contract —
so the library owns the vocabulary and HAL9000 imports it (its door keeps its HTTP surface and readback;
`append_to_timeline` grows a typed overload or `TimelineEntry` renders to the string it already accepts).
(2) A typed accessor `PersonRepository.introduced_by(person) -> list[IntroRecord]` (introducer name, date,
source) derived from that person's `[intro]` entries by the library's own parser, so no consumer parses
the convention; exocortex builds its relationship edges from the same accessor without a frontmatter
change. Revisit a stored field only if query volume ever makes derivation a cost (Dave's words). Sequenced
at the top of `queue_order` behind WI-029 and WI-032 (Dave, 2026-09-26).

## Intent

Every timeline entry any writer puts on a vault note has ONE definition of its shape, and it lives in the
library every writer already installs. "Who introduced this person" is answerable by any consumer through
one typed call, without a stored field and without anyone parsing markdown they do not own.

## Ruling — 2026-09-28 (Dave, in-session; supersedes the `[intro]` / `intro-in` premise above)

Dave's words: *"Can we move the legacy 'introduced-by' all together and if there was a value add it as a
timeline entry?"* and, to the conductor's recommendation that follows, *"proceed with your recommendation"*.

**The audit the ruling rests on** (live vault, 2026-09-28, read before any write): ONE note carried a
stored `introduced_by` frontmatter key (`@Andy Shovel.md`, `'[[Sam Tucker]]'`; `Person` has never declared
the field — it survived on `extra="allow"`). 86 legacy `[intro]` timeline headings, ALL outbound
("Introduced to [[X]] via email" — Dave introduced this person to someone; not one is an introduced-by
fact), 22 of them with a dedupe marker, in three heading date grammars (43 `Month D, YYYY`, 38 ISO+time,
5 ISO). Zero `intro-by` / `intro-to` headings existed yet.

1. **The stored field is RETIRED, not modelled.** Its one value was converted by hand on 2026-09-28
   through the sanctioned doors and the key removed: an `intro-by` entry on Andy Shovel's note dated to the
   note's own `first_interaction` (2025-11-10; "day not recorded" is disclosed in the entry text),
   discriminator `Sam Tucker`, written through HAL9000's in-process `append_timeline_entry` (the HTTP door
   carries no `when` by design); the key removed through `vault_io` under lock with a one-line delta.
   Readback: `^introduced_by:` lines in the vault = 0; HAL9000's `GET /api/entities/person/Andy%20Shovel`
   no longer serves the key; the entry reads back with its `<!-- intro-by:2025-11-10:Sam Tucker -->` marker.
   **This item's write gate refuses `introduced_by` as a person frontmatter key** so it cannot creep back.
2. **The accessor reads `intro-by` ONLY**, taking the counterparty from the discriminator slot by kind and
   never from the prose; `intro-to` is the introducer-side mirror of the same event; legacy `[intro]` is
   NOT a data source for the accessor — it records the opposite direction. Slugs and slot are HAL9000
   WI-077's (`routers/introduce.py` `OBSERVED_KIND_ON_INTRODUCEE` / `OBSERVED_KIND_ON_INTRODUCER`,
   key `{kind}:{day}:{counterparty}`), exactly as WI-034 states — **WI-034 FOLDS into this item** and is
   parked with nothing of its own to build.
3. **The 86 `[intro]` entries stay as they are.** `lint_vault` gains a REPORT-ONLY detector for the legacy
   kind (never auto-fixed) so the corpus stays visible. Rewriting them to `intro-to` is a separate, later
   migration if ever wanted — dry-run → gated write → readback, WI-032's shape — and buys the accessor
   nothing.
