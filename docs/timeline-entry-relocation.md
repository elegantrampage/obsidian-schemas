---
id: WI-033
title: TimelineEntry relocates into the library, with a derived introduced_by accessor
project: obsidian-schemas
stage: idea
created: 2026-09-26
last_touched: 2026-09-26
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
