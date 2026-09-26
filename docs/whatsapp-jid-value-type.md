---
id: WI-032
title: Validate the WhatsApp JID shape at the person boundary
project: obsidian-schemas
stage: idea
created: 2026-09-21
last_touched: 2026-09-21
stage_changed: 2026-09-21
touched_by: session
tags: []
depends_on: []
---

# Validate the WhatsApp JID shape at the person boundary

**Premise re-anchored and scope RULED — 2026-09-26 (Dave, threaded review; premise doc
`/Users/davewascha/Workspaces/mainspring/docs/identity-and-identifiers-recommendation-2026-09-26.md`,
step 2; conductor note).** Read this paragraph as the premise; the original below is the 2026-09-21
mint. (1) The library ALREADY ships the JID type: `obsidian_schemas/identifier.py:WhatsAppJID.parse`
(WI-125/WI-035) accepts `<digits>@s.whatsapp.net` (pivots to `.phone`, keys `phone:<digits>`) AND
`<digits>@lid` (no phone, keys `jid:<lid>`) — the mint's "`<digits>@s.whatsapp.net`, or empty" is
NARROWER than the package's own definition. Ruling: the field's type IS `WhatsAppJID`, both forms; no
second spelling of "well-formed" anywhere. (2) SHAPE, ruled: `whatsapp: list[WhatsAppJID]`, and the other
identifier fields (`emails`, `phones`, `slack`, `linkedin`) become typed lists — the bridge store shows 51
people carrying both a phone-JID and a newer `@lid`, which a scalar cannot hold. Provenance
(`source`/`observed_at`/`corroboration`) stays OFF the note (writer's ledger, keyed by value). (3)
RESOLUTION, in scope: `resolve_all` has no `whatsapp_jid` step — a lid is indexed correctly under
`jid:<lid>` by `_project_identifiers` (`person.py:330-331`) but nothing in the cascade reads that kind, and
`_index_entity` (`person.py:267-270`) feeds a lid's DIGITS into the legacy `_phone_index` as if a phone.
Add a public `get_by_identifier(Identifier)` / a cascade step over the identifier index for the
`whatsapp_jid` kind, and stop feeding lids into `_phone_index` (only phone-bearing JIDs pivot). (4)
MIGRATION, ruled: scalar→list across ~1,170 live person notes plus the HAL9000/exocortex ContactInfo
mirrors goes through THIS repo's migration discipline — a DRY RUN that reports counts, the write through
`vault_io`, then a READBACK count — never a one-off script; this is WI-010's first real migration and
its un-park criterion. (5) QUEUE: top of `queue_order` behind the in-flight WI-029 (Dave, 2026-09-26);
HAL9000 WI-075 depends on it and gates orchestrator WI-192/193.

## Problem / Motivation

`Person.whatsapp` is a bare `str`, so every writer lets any string through: HAL9000's
`PATCH /api/entities/person/{name}` door, the `new-person` skill, the contact sync. A malformed
JID was written for Kim Faura and repaired by hand through the PATCH door on 2026-09-09 (HAL9000
WI-064-repair artifact); the repair session flagged the missing shape validation as
obsidian-schemas' call, since the field's type lives here and every consumer inherits it. Carried
unruled in HAL9000's session log since; Dave ruled "mint it" on 2026-09-21.

Per the estate rule "type the boundaries, not just the entities" (Workspaces/CLAUDE.md, Data
Quality Discipline): a stringly-typed identifier field is how a malformed value gets stored and
then confidently served to every resolver and sender downstream. The fix belongs in ONE place —
a `WhatsAppJID` value type with a validating constructor (`<digits>@s.whatsapp.net`, or empty) —
so that HAL9000's PATCH door, the skill and the sync all refuse a malformed value at write time
rather than any one of them re-implementing the check.

## Intent

A WhatsApp identifier that is not a well-formed JID never reaches a person note. Every writer
refuses it at the boundary, loudly and naming the value, and the one definition of "well-formed"
lives in obsidian-schemas so no consumer carries its own copy.
