---
id: WI-033
title: TimelineEntry relocates into the library, with a derived introduced_by accessor
project: obsidian-schemas
stage: specced
created: 2026-09-26
last_touched: 2026-09-28
stage_changed: 2026-09-28
touched_by: session
tags: []
depends_on: []
transitions: ["idea>exploring@2026-09-28@session", "exploring>specced@2026-09-28@porter"]
---

# TimelineEntry relocates into the library, with a derived introduced_by accessor

### Archived Rounds

<!-- archive-split: machine-maintained pointer; do not edit -->
Settled gate rounds for this item live in `docs/timeline-entry-relocation-rounds.md` — every round at a conveyor door
this item has already advanced past, byte-for-byte, append-only, never rewritten. READ ON DEMAND
ONLY: each gate's latest standing round is still in this document, so nothing needed to advance this
item is in the drawer. Open it only to read a settled round's full reasoning.


## Problem / Motivation

The vault's timeline-entry vocabulary — the `### {Month D, YYYY} [{kind}]` heading, the
`<!-- {kind}:{YYYY-MM-DD}:{discriminator} -->` dedupe marker, the kind-slug validation and the
`intro:{date}:{name}` key — lives in HAL9000's WI-058 door (`backend_fastapi/core/timeline_entry.py`,
`TimelineEntry`), not in this library: `obsidian_schemas` ships only
`PersonRepository.append_to_timeline(person, entry, deduplicate_key)`, a raw string appender with substring
dedupe (`repositories/person.py:1452-1557`), and `body_sections.py` knows sections, not entry kinds. That
was fine while HAL9000 was the only writer. Dave's 2026-09-26 ruling (threaded review; premise doc
`/Users/davewascha/Workspaces/mainspring/docs/identity-and-identifiers-recommendation-2026-09-26.md`,
disagreement 3) adds a second use: inbound third-party introductions are recorded as `[intro]` timeline
entries on BOTH parties (introducee "Introduced by [[X]] via email", introducer "Introduced Dave to [[Y]]",
discriminator `intro-in:<date>:<other>`) with NO stored `introduced_by` field, and consumers that need
"who introduced this person" — exocortex's relationship edges (the parked WI-006 — *conductor correction 2026-09-28: WI-006 is email ingestion; the measured waiting consumers are HAL9000 WI-078 and orchestrator WI-194, see `### Dependencies` and `docs/wi-033-consumer-audit.md`*), orchestrator's capture,
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

**Sharpened after exploration (2026-09-28).** Most of the paragraph above describes machinery; the pain
is one sentence. *The only structured record of who introduced whom is a `<!-- {kind}:{day}:{counterparty} -->`
comment whose grammar is defined in a project this library does not install — and the library's own
timeline writer cannot see that comment at all.* `PersonRepository.append_to_timeline` takes a raw
string and dedupes by whole-file substring (`repositories/person.py:1452-1557`), so at the door the
caller who renders the marker correctly and the caller who renders it wrong are indistinguishable, and
the key a caller dedupes on need not be the key it writes. Everything else follows from that one gap: a
consumer that wants "who introduced X" must either parse a convention another project owns, or
re-derive it from prose — which this tree ALREADY does once, in `lint_vault`'s `intro_not_symmetric`
regex over Timeline prose (`scripts/lint_vault.py:814-834`). That regex is the specimen of the second
copy the mint predicts; it exists today.

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

## Exploration Notes

Mode: **approval-only** (`involvement: null`, `state/work-items.json:2812`). The approach below is
re-derived from the frozen `## Intent` and from the 2026-09-28 ruling; the mint's named mechanisms are
treated as hypotheses and two of them did not survive (see *Rejected*, A3 and A6).

**Revised 2026-09-28 after the architectural review below.** Where each of its three blocking findings
landed, so a re-reader does not have to diff: **finding 1** (the Intent promises one definition, the
approach shipped a second copy silently) → the sequencing is now a decision with its alternatives,
**D7**; the cutover is a named follow-up with an owner and a re-entry condition (*The follow-up this
ruling mints*), recorded in this tree by **precondition 4** so the mint is an act the drive pauses for;
the absence is named in *What this item does NOT do*; the window's guard is stated in `## Approach` and
machine-checked by **AC-1(a3)**'s anchor; example-of-done 4 puts it in Dave's terms. **Finding 2**
(AC-1(a)'s oracle unexecutable) → precondition 1 now requires input→output PAIRS in a declared
machine-readable shape with `when` pinned per sample, and **AC-1(a)** is driven by the CAPTURE's sample
set with **AC-1(a2)** asserting the two kind tables coincide. **Finding 3** (the one-copy scan missed
`scripts/`) → **AC-2(e)** scans `obsidian_schemas/**` AND `scripts/**`, permits an import, forbids a
re-definition, and rests on the newly measured **P9**. The four non-blocking notes are taken too:
`IntroRecord.source` is pinned (AC-2), AC-4(d)'s baseline is named as a same-run derivation, AC-3(b)'s
derived set states and asserts its filter, and the stale `append_to_timeline` line range in
`## Problem / Motivation` is corrected.

**Revised again 2026-09-28 after the round-2 review.** Round 2 closed all three of round 1's findings and
raised one new one, in the fold itself: "declared kind table" was a CLOSED refusing enum in AC-1(a2) and an
OPEN kind-slug rule in `## Approach` and A1 — two different write doors with different post-cutover
consequences. It is resolved in ONE direction and recorded as a decision, **D8**: the write door is the OPEN
SLUG RULE; the table is renamed `PARITY_KINDS`, gates no write, and is the parity/sweep universe only. The
reading is made FALSIFIABLE rather than merely stated by **AC-1(a4)**, which plants a slug-valid kind that is
absent from `PARITY_KINDS` and asserts it constructs, renders and round-trips — the discriminating member
that tells the open door from the closed one, since no corpus can (P4). **AC-1(a2)**'s `why` is rewritten to
claim only what the set equality actually buys (the fixture space of two derived sweeps equals the on-disk
population) and to disclaim what it does not (it gates nothing). The finding's second clause — the library's
REFUSAL SET unpinned against HAL9000's, while the item's stated meaning of "relocate" is byte parity — is
closed by precondition 1's new **part 3** (a `## Validation boundary` section of INPUT→VERDICT pairs produced
by RUNNING HAL9000's code) and by **AC-1(c2)**, which pins the ACCEPT direction (no stricter) with the
by-design guard set asserted as a set equality so the exception cannot be widened, and states in writing that
the loose direction is out of scope. Round 2's four non-blocking notes are taken too: the drift-check
asymmetry is answered rather than left (the **D7** addendum), AC-3(a)'s placement is named and grounded in
the newly measured **P10** (the person body, so an undeclared write is covered), the fixture corpus's own
stale example sentence is folded into AC-3(c), and **D3** now picks the swapped value fresh.

**Revised a third time 2026-09-28 after the AC red-team.** The red-team's one finding is on the axis three
architect rounds did not run: AC-2 discriminated the KIND axis thoroughly (planting `intro-to`, legacy
`intro` and an out-of-table kind so a `"intro" in kind` build mismatches) and left the PERSON axis — the one
the accessor's own first argument selects on — with a single member, so a build that globs every note under
the vault for `intro-by` markers, or reads a fixed or first note, satisfied every clause while being able to
answer "who introduced @Alice" with @Bob's introducer in production. It is closed the same way the kind axis
was, by PLANTING the discriminating member (P4 again: the frozen corpus has zero entries, so it can supply a
second person no more than it can supply a second kind): AC-2's fixture now holds TWO person notes each with
its own `intro-by` entry — different counterparty, different day, different `source` bytes — and the new
**AC-2(a2)** asserts the scoping in BOTH directions plus invariance to the other note's presence, which rules
out the union build and the read-one-fixed-note build together. The read path is also stated once in prose so
the document is buildable one way only: `## Approach` and A1 now say the accessor reads THAT PERSON'S OWN
`## Timeline`, loaded through `parse_body_sections` from the note the person was parsed from, never a
vault-wide scan. Example-of-done 1 carries the same shape in Dave's terms.

### Premises measured this drive

Every premise below was RUN with the reader's granted tools (Read, Grep, Glob) against **the tree as this
drive seeded it** — worktree `cage-wt-3tushyul`, git HEAD `bc2f11e`, status clean at seed. Each states its
predicate so another reader can re-run it at that commit and contradict it. Premises this reader could
NOT settle — HAL9000's source, the live vault — are routed to `## Write Targets` as `kind: precondition`
fences, not asserted from memory.

**P1 — the vocabulary exists nowhere in this tree.** Predicate: case-insensitive grep for `timeline`
over the worktree (83 files) plus a full read of `obsidian_schemas/body_sections.py` and of
`person.py:1452-1557`. No module under `obsidian_schemas/**` defines a typed entry, a kind slug, a
marker grammar or a render. The only timeline writer is `append_to_timeline`, a raw-string prepender;
`body_sections.py` knows `^## `-delimited spans and `- [ ]` checklist items and nothing else — it is
documented as deliberately *entity-agnostic* (`body_sections.py:6-9`). So "relocates INTO the library"
is a genuine addition, not a move of something that half-exists here.

**P2 — the dedupe contract is a whole-file substring test.** `if deduplicate_key and deduplicate_key in
content` (`person.py:1502`), where `content` is the entire note INCLUDING frontmatter and every other
body section — not the `## Timeline` span, and not anchored to the marker form. A key like
`intro-by:2025-11-10:Sam Tucker` therefore also dedupes against a `## Notes` line that happens to quote
it, and a caller may pass a key that has no relationship at all to the marker it is about to write.
This is the defect the typed overload closes for free.

**P3 — `append_to_timeline` PREPENDS, despite its name.** `parts[0] + timeline_marker + formatted_entry
+ parts[1]` (`person.py:1543-1545`) inserts immediately after the `## Timeline` heading. Newest-first is
the de-facto stored ordering, and the relocated renderer must not change it — the accessor's declared
document order is therefore newest-first, not chronological.

**P4 — the frozen fixture corpus contains ZERO timeline entries.** Predicate: grep `^### |<!-- ` over
`tests/fixtures/vault/` → **no matches**, across all ~50 notes; confirmed by reading
`tests/fixtures/vault/@Morvette Harkwell.md`, whose body is exactly
`ENTITY_BODY_CONFIG["person"]["default_body"]`. `NoteSpec` has no body field at all
(`tests/fixture_vault.py:62-83`) — the manifest declares frontmatter and nothing else. **Consequence,
and it governs every AC below:** the live corpus cannot tell a right accessor from a wrong-but-present
one, because it has no entries. Every discriminating member in this item is PLANTED (WI-286), and
sampling is not an option that exists.

**P5 — exactly one fixture note carries the retired key.** `tests/fixtures/vault/@Morvette Harkwell.md:16`
(`introduced_by: "Voxleaf"`), declared at `tests/fixture_vault.py:320-326` as the AC-5(b) clause-3
specimen: *"a value for a key no model declares is an identity position BY DEFAULT, with no manifest flag
to opt out."* Its job is to be an UNDECLARED KEY; the particular key is incidental, and
`docs/vault-fixtures.md:279` names `manager:` as the co-equal example of the same class.

**P6 — a blanket key ban at the gate would brick that note, and the gate cannot tell the two cases
apart.** `Person` is `extra="allow"` (`models.py:34-35`); `writer.model_to_frontmatter` serializes
`model_extra` into every note the library writes (`models.py:49-52`, stated verbatim there); the entity
arm hands that whole projection to `gate_write(..., whole_record=True)` (`writer.py:229-233`, `:252-253`)
and `_writeback_identifier` does the same (`person.py:1270-1271`). So a `save()` of a note that ALREADY
carries `introduced_by` hands the key to the gate inside `introduced`. And the gate is DECLARE-only —
"it reads only its own arguments — no filesystem, no glob, no path shape, no sibling note"
(`name_gate.py:22-29`) — so it structurally cannot distinguish "this write introduces the key anew" from
"this projection re-emits a key the note already had". This is the exact "remedy-is-the-disease" shape
the DELTA doctrine was written against (`name_gate.py:31-36`). It is the sharpest design question in the
item and is resolved in *Decisions*, D3.

**P7 — the tree already parses intro PROSE once.** `check_timeline`'s `intro_not_symmetric` detector
regexes `[Ii]ntroduc(?:ed|tion)[^[]*\[\[(@[^\]|]+)` out of the Timeline section
(`scripts/lint_vault.py:814-834`), report-only (`auto_fixable` left at its `False` default). It is a
live specimen of the thing the Intent forbids, and it is IN SCOPE only as evidence — this item does not
change it (see *What this item does NOT do*).

**P8 — one rule lands in one place.** `gate_write` has exactly six call sites in the package:
`writer.py:252`, `:385`, `:443`, `:494`; `repositories/base.py:728`; `repositories/person.py:1270`.
A retired-key rule written into the gate is written once and reaches every frontmatter-writing arm.

**P9 — the marker delimiters appear in NO python source in this tree today, so AC-2(e)'s "exactly one
definition" starts from zero rather than from a population.** Predicate: grep for `<!--` or `-->` over
`obsidian_schemas/**/*.py` and `scripts/**/*.py` → **no matches**. This settles two things the scan clause
rests on. First, `intro_not_symmetric`'s prose regex (P7) is a second copy of a PARSER but not of the
MARKER GRAMMAR — it contains no delimiter — so it falls outside the predicate by construction and needs no
exemption. Second, the only files that will carry a delimiter after this item are the new module and,
unless the criterion says otherwise, `scripts/lint_vault.py` — which is exactly why the scan is widened to
`scripts/**` rather than bounded to the package.

**P10 — an UNDECLARED write falls through to the gate's person body, and a declared non-person write does
not, so AC-3(a)'s rule has exactly one correct placement.** Predicate: full read of
`gate_write`'s prologue, `name_gate.py:326-398`. Two branches precede the person body. The first
(`:359-360`) refuses when `"name" in introduced and declared_type is None` — it speaks ONLY to `name:`. The
second (`:373`) is `if declared_type is not None and declared_type != PERSON_TYPE:` and returns
`dict(introduced)` at `:398`, with the comment at `:364-368` stating verbatim that the `is not None` half is
load-bearing precisely so that "an UNDECLARED write that introduces identifiers but NO `name:` must fall
THROUGH and normalize exactly as a declared one". Consequence: a retired-key rule written into the PERSON
BODY (below `:398`) fires for a `person`-declared write AND for an undeclared one — which is the route a
person note missing its `type:` takes — while `company` and `book` are exempted for free by the `:373`
return. The same rule keyed on `declared_type == PERSON_TYPE` would satisfy every AC-3 clause as previously
worded and leave the undeclared route open. This settles the placement as a MEASURED fact rather than a
build-time coin flip; AC-3(a) now states it.

### Where the structure actually lives (the WI-185 seam question)

Asked of the draft approach: *the accessor reconstructs "who introduced X" at read time — where does that
structure exist, and why does it not survive to where we consume it?*

It DOES survive, and that is the finding that simplifies the whole design. HAL9000's WI-077 writer emits
the counterparty and the day into the machine slot — `<!-- {kind}:{day}:{counterparty} -->` — at the same
moment it renders them into the sentence. The marker is the structure; the prose is the lossy copy. So
the accessor never needs to reconstruct anything: it reads the slot. Three consequences fall out at once
and each removes work the mint implied:

- **The three heading date grammars are irrelevant.** The ruling's audit found headings in `Month D, YYYY`,
  ISO+time and bare ISO. None of them is parsed by anything this item builds — the day comes from the
  marker's own slot, which has exactly one grammar. A parser over three heading dialects was the
  expensive shape the mint invited; it is not built.
- **The prose is never read.** Not as a fallback, not as a tiebreak. This is the ruling's own rule, and
  the seam question independently arrives at it.
- **Where the structure genuinely DOESN'T survive, the honest answer is a report, not a guess.** The
  ruling's audit measured 22 of 86 legacy entries carrying a marker; the other 64 discarded it at write
  time and there is nothing to recover. A markerless entry is therefore REPORTED by the linter and is
  absent from the accessor's answer — the narrowing arm, not an invented oracle.

The one place structure IS discarded at a seam this item owns is P2: `append_to_timeline` accepts a
string and a dedupe key as two unrelated arguments, so the marker's grammar is re-typed by every caller
and the key can disagree with it. That seam is fixed at the door (the typed overload derives both from
one `TimelineEntry`), which is the WI-185 rule applied where it actually bites.

### Approaches considered

**A1 — one new leaf module + a typed overload + one gate rule + report-only detectors. CHOSEN.**
`obsidian_schemas/timeline_entry.py` is a LEAF (imports `errors` only, matching `name_gate.py`'s leaf
discipline, `name_gate.py:14-20`) holding `TimelineEntry` (kind, text, injectable `when`, optional
discriminator), `render()`, the derived `dedupe_key`, the kind-SLUG RULE (an open pattern — see D8; NOT an
enum over a fixed kind list) and discriminator validation including the `-->`/`<!--` forgery guard, the
marker regex, `parse_markers(timeline_text)`, and a declared `PARITY_KINDS` table that is the parity/sweep
universe and gates nothing.
`append_to_timeline` grows a typed overload that derives BOTH the rendered entry and the dedupe key from
one `TimelineEntry`. `PersonRepository.introduced_by(person)` reads THAT PERSON'S OWN `## Timeline` through
`parse_body_sections` — from the note the person was parsed from, never a vault-wide scan — filters
`parse_markers` by kind, and returns `IntroRecord`s. `gate_write` gains
the retired-key refusal. `lint_vault` gains three report-only detectors.

**A2 — put `TimelineEntry` in `body_sections.py`. REJECTED.** That module is documented as
entity-agnostic section machinery, with entity-specific knowledge explicitly deferred to the repository
layer (`body_sections.py:6-9`). Entry KINDS are vocabulary, not structure. Folding them in would make the
one module that knows `## ` headings also know `intro-by`, and would put a non-leaf dependency in reach
of the gate if the gate ever needs `PARITY_KINDS`.

**A3 — the accessor falls back to headings and prose for markerless entries. REJECTED**, and it was the
mint's implicit shape. Three independent reasons: the ruling forbids it (counterparty from the slot,
never from the prose); the fallback would be guesswork on 64 of 86 entries which record the OPPOSITE
direction anyway; and the mechanism it needs already exists as `intro_not_symmetric`'s regex (P7), so
building it would create exactly the second copy of a prose parser the Intent exists to prevent.

**A4 — model `introduced_by` as an optional `Person` field with a deprecation shim. REJECTED** by Dave's
ruling, and the audit seconds it: the live population is now zero, so the field would be a schema surface
with no data behind it and a permanent invitation to write to it.

**A5 — migrate the 86 legacy `[intro]` entries to `intro-to`. REJECTED** by ruling §3. They record the
outbound direction, so they buy the accessor nothing; rewriting them is a live-vault mutation needing its
own WI-032-shaped bracket. They stay, and a report-only detector keeps them visible.

**A6 — an unconditional key ban with no other change. REJECTED AS STATED**, because of P6: it bricks
`save()` on `@Morvette Harkwell.md` and on any live note that regains the key, at the entity arm, with no
way for the gate to tell a re-emission from an introduction. What survives of it is D3 — the ban is kept
unconditional and the colliding population is emptied instead.

### Decisions

**D1 — the marker is the data channel; the heading is presentation.** `TimelineEntry` owns both, but the
accessor and the detectors read only the marker. Stated as a rule so a later reader does not "improve"
the accessor by teaching it headings.

**D2 — the typed overload derives the dedupe key from the entry, and dedupe matches the MARKER FORM
anchored inside `## Timeline`** — not an arbitrary substring of the whole file (P2). The string-and-key
signature stays for the existing callers; the typed one is what new callers get.

**D3 — the retired-key ban is UNCONDITIONAL at the gate, and the population it could brick is emptied
rather than exempted.** Live: already zero (the 2026-09-28 conversion, readback in ruling §1). Fixture:
`@Morvette Harkwell.md`'s undeclared key is swapped to `manager:` — which serves its AC-5(b) clause-3
job identically (P5; `docs/vault-fixtures.md:279` already names it as the same specimen class) and costs
one `CORPUS_DIGEST` regeneration (`tests/fixture_vault.py:21-25`, `:44`). With both populations empty,
the DELTA doctrine's objection is void by measurement rather than by argument, and the ban is what keeps
them empty.
*The argued trade, stated because it INVERTS the name gate's stored-dirty ruling and a reader will
notice:* a note that regains `introduced_by` by hand-edit becomes unwritable through `save` until the key
is deleted. That is correct pressure here and wrong there — a Tier-1 dirty NAME has no remedy but a
rename, so refusing its writes is punitive; a retired KEY has a one-line remedy (delete it), the linter
names the note, and the conductor performed exactly that remedy once already.
*The swapped value is chosen FRESH, not carried over.* `introduced_by: "Voxleaf"`'s value happens to be the
corpus's own company stem (`@Voxleaf Ltd.md`, `tests/fixture_vault.py:367`); nothing depends on that, but the
new `manager:` value is picked as a name the identifier index cannot resolve, for the same reason the note
declares no `shape_classes` — an undeclared-key specimen should carry no second job.
*Runner-up, recorded so it is not re-explored:* keep the fixture key and declare Morvette a
`Verdict(kind="refusal", ...)` specimen. Rejected — it makes the frozen corpus a permanent carrier of the
retired key, and it re-opens WI-032's gate-arm placement question (`tests/fixture_vault.py:353-359`) for
no gain.

**D4 — the refusal names the KEY, never the value.** `NameGateRefusal.refused_value` is set to the
literal `"introduced_by"`. WI-032's arm sets it to the offending value, but here the offending value is a
person's name — `_refuse`'s rule 2 exists precisely to keep note-derived identity out of refusals
(`name_gate.py:174-186`), and the key is a constant that identifies the fault completely.

**D5 — all three new detectors are REPORT-ONLY, none auto-fixable.** `legacy_intro_entry` (ruling §3);
`intro_by_without_marker` — an `intro-by` heading with no marker, i.e. an entry the accessor structurally
cannot see, which is the honesty invariant for its narrowed promise; `retired_key_introduced_by` — ERROR,
because auto-deleting a frontmatter value is data loss and the direction is a judgement.

**D6 — fixtures live in a TEMP vault, not the frozen corpus,** except for D3's one-key swap. The
specimens this item needs are BEHAVIOURAL (entries of each kind, a markerless entry, a forged marker),
not shape-class members, so they owe the census no row; and every byte added to
`tests/fixtures/vault/` is swept by `test_no_corpus_note_carries_a_live_identifier` over the whole corpus
text (`tests/test_fixture_vault.py:1033-1036`), which is a wall worth not paying for entries a temp vault
holds just as well.

**D7 — LIBRARY-FIRST, and the HAL9000 cutover is MINTED here rather than left implied.** The Intent says
the vocabulary has ONE definition. This item, scoped to this tree, cannot deliver that on its own: when it
lands, `obsidian_schemas.timeline_entry` and HAL9000's `backend_fastapi/core/timeline_entry.py` are TWO
implementations of one grammar, and the parity test pins the library's copy against a capture of the other
frozen at one HEAD. A frozen capture cannot detect drift — if HAL9000 adds a kind or moves a space
tomorrow, AC-1(a) stays green (it compares against the committed file) and AC-2 stays green (it plants
entries with the library's OWN renderer), while the accessor could return `[]` against real HAL9000 bytes.
That is LESSONS #4 exactly — exocortex's private copy of the name-prefix regexes that never inherited the
canonical validator's fixes — and the rule it carries is that the work is to ROUTE to the one
implementation, not to copy it.
Three answers were available and the second is taken:
*(a) do both halves in one item* — rejected: the cutover is a write into another repo, outside this
drive's tree and outside the caged builder's reach, and it cannot be gated by this item's hermetic floor.
*(b) library-first, with the cutover MINTED as a named follow-up carrying a re-entry condition* — CHOSEN.
Sequencing the publish before the consumer swap is the ordinary shape for a shared schema package; what
makes it honest rather than a dangling intention is that the follow-up has an id, an owner and a
re-entry condition BEFORE this item ships, and that the window between the halves is described rather
than assumed away. The mint is a conductor act at the same pause as the other three precondition commits,
and precondition 4 is what puts the RECORD of it in this tree's HEAD, so the drive cannot proceed past it
while it is still a sentence.
*(c) ship the library and say nothing* — rejected: it is what the architect's finding 1 names, and it
leaves the document buildable two ways (a builder reading the Intent could believe the item is not done
until HAL9000 imports).
*What stands guard in the window, stated rather than assumed:* precondition 1 pins HAL9000's 40-hex HEAD;
the module carries it as a declared `HAL9000_PARITY_ANCHOR` constant and AC-1(a) asserts it equals the
HEAD the capture declares, so the anchor is machine-checked and a staleness re-run is one diff. Between
this item and the cutover, drift in HAL9000's own copy is UNDETECTED by this tree's hermetic floor — that
is accepted in writing, not mitigated, because the floor cannot reach another repo (WI-031 clause (v));
the instrument is the cutover item's first act (re-run the capture at HAL9000's then-HEAD, diff against
the anchor), which is exactly its re-entry condition below.
*Addendum — why the declined standing drift check is NOT the same shape as the linter, since this document
argues in AC-4's `why` that a report-only tool outside the floor is this tree's answer to exactly this kind of
blindness.* The two cases differ in OWNERSHIP and in whether the window closes. The vault is this library's
own data domain: every consumer's bytes, no other owner, an unbounded and permanent corruption window, and
`lint_vault` already exists as the standing instrument — so a report there is the cheapest honest answer.
HAL9000's source is ANOTHER PROJECT'S CODE behind a bounded window that ONE scheduled item closes, and a
checker living in this tree that reads a sibling repo's absolute path would invert the very ownership this
item establishes: it would make the PUBLISHER responsible for watching the copy, and it would re-open the
out-of-tree path dependency WI-031 clause (v) closed for the vault for the same reason. So the drift check
belongs to the holder of the second copy, which is the cutover item, and this item declines it deliberately
rather than by oversight. Recorded for the cutover item to take if it wants it standing rather than once: a
`scripts/`-resident parity re-check (re-run the capture at a given HAL9000 path, diff against
`HAL9000_PARITY_ANCHOR`) is the runnable-on-demand form, and it lands in HAL9000 or in the cutover's scope,
not here.

### The follow-up this ruling mints — the HAL9000 cutover

Named here so it is an item rather than a sentence in `### Dependencies` (architect finding 1, ii).

- **What it does.** HAL9000's `backend_fastapi/core/timeline_entry.py` is DELETED and its WI-058 door and
  WI-077 router import `obsidian_schemas.timeline_entry` instead; the library's module becomes the one
  definition of the grammar and HAL9000 keeps only its HTTP surface, its readback and its kind choices.
- **Where it is minted.** In HAL9000's backlog (its own project), by the conductor, at the same pause that
  commits the other three preconditions below. It is NOT minted in this tree — this tree only RECORDS it,
  which is what precondition 4 is for.
- **Re-entry condition, stated so the follow-up can be started without re-deriving it.** (1) This item is
  `done` and the library exports `TimelineEntry`, `render`, `parse_markers` and `dedupe_key`; (2) the
  parity capture is re-run at HAL9000's then-HEAD and diffed against `HAL9000_PARITY_ANCHOR` — a
  non-empty diff is the cutover's first finding and its scope grows to cover it; (3) the cutover ships
  when HAL9000's own floor is green with its module deleted, its imports repointed, and one live readback
  through its door showing bytes unchanged.
- **Why it is not folded into this item.** It writes another repo, its floor is HAL9000's, and its
  evidence is a live door readback — none of which this drive's cage or hermetic floor can reach.

### Decisions (continued)

**D8 — THE WRITE DOOR IS THE OPEN SLUG RULE; `PARITY_KINDS` IS A PARITY UNIVERSE AND GATES NOTHING.** The
round-1 fold left the document buildable two ways — "declared kind table" reads as a closed enum in AC-1(a2)
and as an open kind-slug pattern in A1 and `## Approach` — and the two are different doors with different
post-cutover consequences. Settled in the OPEN direction, for three reasons that all point the same way:

1. **This item RELOCATES; it does not tighten.** `### Constraints discovered` says parity with HAL9000 is the
   meaning of "relocate". HAL9000 validates a kind by SLUG (precondition 1 captures that rule as source), so a
   closed enum would make the library STRICTER than the code it is relocating, and post-cutover a HAL9000 call
   that writes today would raise. Tightening a shared vocabulary is a separate, signable subtraction — not a
   side effect of moving it.
2. **The item's own named consumers would be locked out.** Example-of-done 3 promises "orchestrator or any new
   writer that installs this library" can build a `TimelineEntry` and hand it to the door. A table frozen to
   the kinds HAL9000's capture happened to sample forbids exactly that for anything new, so the closed reading
   contradicts a promise this document already made in Dave's terms.
3. **The honest cost of the open reading is bounded and nameable.** A kind outside `PARITY_KINDS` has no
   parity oracle — nobody captured bytes for it — so the library makes no byte-parity CLAIM about it. That is
   the truth either way; the closed reading does not buy parity for new kinds, it merely forbids them.

So: `PARITY_KINDS` is a declared constant naming exactly the kinds this library holds a committed byte-parity
sample for. It is the FIXTURE SPACE the two derived sweeps iterate (AC-1(b), AC-2) and the left-hand side of
AC-1(a2)'s set equality. It is not consulted by `TimelineEntry`'s constructor, by `render()`, by `dedupe_key`
or by `parse_markers`. A slug-valid kind absent from it CONSTRUCTS AND RENDERS, and AC-1(a4) plants one and
asserts exactly that — because P4 means no corpus can tell the two doors apart, so the discriminating member
is planted (WI-286).
*What a new writer's new kind costs, stated so nobody reads the open door as "the table is optional":*
nothing at the door — it works immediately. Adding it to `PARITY_KINDS` is a separate, deliberate act that
CLAIMS parity, and it is legal only when precondition 1's capture (or its successor) carries a sample for it,
because AC-1(a2) is a set equality and an unsampled entry turns it RED. The table therefore grows only when
captured bytes grow, which is the property that keeps AC-1(b)'s sweep space equal to the population actually
on disk instead of to a list a builder chose.
*The refusal surface, same root, opposite direction.* Parity was pinned for RENDER only; a capture whose
samples are all VALID inputs cannot detect a library that refuses an input HAL9000 accepts. Precondition 1
gains **part 3** — a declared `## Validation boundary` section of INPUT→VERDICT pairs produced by RUNNING
HAL9000's code, including its boundary cases — and **AC-1(c2)** asserts the direction that can actually break
a post-cutover caller: the library is NO STRICTER, i.e. every input the capture records HAL9000 ACCEPTING, the
library accepts. The one exception class is enumerated and asserted as a SET EQUALITY (the `<!--`/`-->`
forgery inputs and the empty / whitespace-only / key-separator discriminators of AC-1(c)) so a build cannot
widen "deliberate guard" into an excuse for any other over-refusal. The LOOSE direction — the library
accepting something HAL9000 refuses — is OUT OF SCOPE in writing: it cannot break a caller that works today,
the library's own guards are pinned independently by AC-1(c), and validating on HAL9000's behalf is the
cutover item's business, exactly as D7 already rules for drift.

### Constraints discovered

- **The floor is hermetic and must stay so.** WI-031 clause (v) closed the library's env-fallback route
  (CLAUDE.md), so no test may reach the live vault. Every live fact this item rests on is a committed
  precondition, never a test.
- **Newest-first ordering is stored behaviour** (P3) and the accessor's declared order inherits it.
- **`CORPUS_DIGEST` is a speed bump by design** (`tests/fixture_vault.py:21-25`); D3's swap pays it once.
- **Byte parity with HAL9000 is the meaning of "relocate".** 22 marker-bearing legacy entries and every
  WI-077 entry are already on disk; a renderer that differs by a space stops round-tripping them. This is
  why precondition 1 must carry INPUT→OUTPUT parity samples — not just source, and not outputs alone: an
  output whose `when` is not pinned is not reproducible, so the test could not construct the entry whose
  render it is meant to compare.
- **Parity has TWO surfaces, and both are pinned in the ACCEPT direction (D8).** RENDER parity is the bytes;
  REFUSAL parity is what the door lets through. A renderer can be byte-perfect on every captured sample and
  still refuse an input HAL9000 accepts — which breaks a caller only after the cutover, when the hermetic
  floor is no longer watching that caller. Hence precondition 1's part 3 (INPUT→VERDICT pairs) and AC-1(c2)'s
  no-stricter assertion, with the library's own deliberate guards enumerated as an equality. The loose
  direction is declined in writing, not overlooked.
- **The library must not become STRICTER than the code it is relocating.** `PARITY_KINDS` is a parity
  universe, not an enum the door consults (D8); a slug-valid kind nobody captured still constructs and
  renders. Tightening the shared vocabulary would be a separate subtraction with its own audit and its own
  signature.
- **Parity is a PIN, not a monitor, until the cutover lands** (D7). The capture freezes HAL9000 at one
  HEAD; nothing in this tree's hermetic floor can notice HAL9000 changing after it. The anchor constant
  and the cutover's re-entry condition are the whole of the answer, and the window is accepted in writing.

### Dependencies

- **Inbound:** WI-034 is FOLDED (ruling §2) — nothing to build there, and the slugs are stated here.
  WI-029's provenance seam and WI-032's list-shape are both shipped; nothing in this item is waiting.
- **Outbound:** the accessor's waiting consumers, MEASURED by precondition 3 (conductor correction
  2026-09-28): HAL9000 WI-078 (`idea` — retire `core/intro_extractor.py` + the WI-129 T9 path) and
  orchestrator WI-194 (`idea` — retire the enricher's T9 Notes write). NOT exocortex: its WI-006 is "Email
  ingestion (Gmail threads)", not parked relationship edges, and no exocortex code waits. HAL9000's
  WI-058 door and WI-077 router becoming importers rather than owners is NOT a future fact this item
  assumes — it is the follow-up minted above (D7), with an owner, a home and a re-entry condition, and
  recorded in this tree by precondition 4. Precondition 3 MEASURES the consumers; it does not move them,
  and nothing in this item does. That audit is the estate-wide sweep the WI-032 scar demands — a wider
  sweep found a FOURTH reader there after the item was done.

### What this item does NOT do

Named so a downstream gate does not read the absences as gaps: **it does not cut HAL9000 over to the
library's module** — HAL9000 keeps its own `backend_fastapi/core/timeline_entry.py` until the follow-up
minted in D7 lands, so for that window two implementations of one grammar exist and the only thing
holding them together is the pinned parity anchor (D7 says what that does and does not detect); **it does not
narrow the set of kinds any writer may use** — `PARITY_KINDS` is a parity universe that gates no write (D8),
so this item ships no closed kind enum and adds no refusal HAL9000 does not already have beyond the four
guards AC-1(c) names and AC-1(c2) enumerates as an equality; **it does not validate on HAL9000's behalf** —
where the library ends up LOOSER than HAL9000's rule, that is out of scope in writing (D8) and is the cutover
item's business, exactly as drift is; it does
not rewrite the 86 legacy entries (A5); it does not change or remove `intro_not_symmetric` (P7 — it is
evidence, and removing a shipped report is a separate subtraction with its own audit); it does not add
`introduced_by` to any model (A4); it does not touch `append_to_timeline`'s existing string signature or
its prepend placement (P3); and it makes no live-vault write.

### Subtraction audit (the WI-123 REMOVE rule)

This item demotes two mechanisms. Each classification quotes the TRIGGER PREDICATE, read from this tree,
not the mechanism's name or purpose.

| Mechanism | Trigger predicate (read from the tree) | Classification |
| --- | --- | --- |
| `introduced_by` as a writable person frontmatter key | No predicate in this tree invokes it. `Person` declares no such field (`models.py:56+`); the key survives only on `model_config = ConfigDict(extra="allow")` (`models.py:34-35`) and is re-emitted by `model_to_frontmatter` because that function emits `model_extra` unconditionally (`models.py:49-52`). Nothing reads it anywhere under `obsidian_schemas/**` — grep for `introduced_by` over the package returns zero hits. | **REMOVE** (refuse at the gate). Safe precisely because there is no invoking predicate: nothing loses a caller. |
| legacy `[intro]` entries as a data source for the accessor | There is no accessor today, so there is no predicate to quote — the demotion is of a *proposed* source, not a shipped one. The evidence is directional instead: the ruling's audit read all 86 and found every one outbound ("Introduced to [[X]]"), zero introduced-by facts. | **NOT A SUBTRACTION** — it is a source that never existed. Recorded here so a later reader does not mistake ruling §2 for the removal of something working. The entries themselves are untouched (A5). |

Per the WI-123 rule's last clause, a capture-time audit is a hypothesis: the `[intro]` row above rests on
a live read this reader cannot reproduce, and precondition 2 is what converts it into a re-runnable
predicate BEFORE the criteria are signed.

## Approach

Add one leaf module, `obsidian_schemas/timeline_entry.py`, that owns the vault's timeline-entry
vocabulary: a typed `TimelineEntry` (kind, text, injectable `when`, optional discriminator), its render
to the `### {heading} [{kind}]` + `<!-- {kind}:{day}:{discriminator} -->` shape, its kind-slug and
discriminator validation including the `-->`/`<!--` forgery guard, a derived `dedupe_key`, and
`parse_markers()` — reproducing HAL9000's shipped bytes exactly, per the input→output parity samples
committed as precondition 1.

**Which door the kind check is, stated once so the module is buildable one way only (D8).** The write door is
the kind-SLUG RULE: an OPEN pattern, and a kind that satisfies it constructs and renders whether or not anyone
has captured bytes for it — so this item is a relocation and not a tightening, and example-of-done 3's "any new
writer that installs this library" stays true. The module ALSO declares `PARITY_KINDS`, and that constant is
NOT a gate: it names exactly the kinds a committed parity sample exists for, it is the fixture space the two
derived sweeps iterate (AC-1(b), AC-2), and AC-1(a2)'s set equality is what keeps it equal to the captured
population rather than to a list a builder chose. Nothing in `TimelineEntry.__init__`, `render()`,
`dedupe_key` or `parse_markers` reads it; AC-1(a4) plants a slug-valid kind absent from it and asserts the
round trip, so the open reading is machine-checked rather than merely written down. Parity is pinned on BOTH
surfaces in the direction that can break a caller: RENDER bytes by AC-1(a), and REFUSAL by AC-1(c2) — the
library is no STRICTER than the INPUT→VERDICT boundary precondition 1's part 3 captures, with its four
deliberate guards enumerated as a set equality so the exception cannot be widened. Being LOOSER than HAL9000
is out of scope in writing; the cutover item owns it, as it owns drift.

`PersonRepository.append_to_timeline` grows a typed overload that derives both
the rendered entry and the dedupe key from one entry object, and dedupes on the marker form inside
`## Timeline` rather than on a substring of the whole file. `PersonRepository.introduced_by(person)`
returns `IntroRecord`s — introducer, date, and `source`, the verbatim marker string the record was read
from — read from THAT PERSON'S OWN `## Timeline` section (loaded through `parse_body_sections` from the
note the person was parsed from, never a vault-wide scan), from `intro-by` MARKERS only, counterparty from
the slot, day from the slot, never from the
prose, never from `[intro]`, never from frontmatter, so exocortex, orchestrator and HAL9000 all answer
"who introduced this person" through one typed call. `gate_write` refuses `introduced_by` as a person
frontmatter key unconditionally, with the fixture corpus's one carrier re-keyed to `manager:` so no real
population is bricked. `lint_vault` gains three report-only detectors — legacy `[intro]` entries,
markerless `intro-by` entries, and any resurrected `introduced_by` key — and READS the marker grammar by
importing it, defining no pattern of its own, so the one-definition promise survives the one file that is
about to grow marker-reading code. No live-vault write; no model field; no prose parsing anywhere.

**Sequencing, stated because the Intent's "one definition" is bigger than this item (D7).** This is the
LIBRARY HALF only: HAL9000 keeps its own `timeline_entry.py` until the cutover follow-up minted in D7
lands, so for that window two implementations of one grammar exist. What holds them together is the
parity capture's 40-hex HEAD, declared in the module as `HAL9000_PARITY_ANCHOR` and asserted by AC-1(a)
to equal the HEAD the capture itself declares — that is the STALENESS ANCHOR. It is a pin, not a monitor:
it detects nothing on its own, and drift in HAL9000's copy during the window is undetected by this tree's
hermetic floor. Who re-runs it, and when, is named: the cutover item's first act, as its re-entry
condition (D7).

## Design

Written 2026-09-28 by the spec-writer, cold-start, against the tree at HEAD `133c27a`. Every citation
below was READ at its cited symbol this round; the preconditions were read end to end. The four
`criteria` fences and `## Intent` are FROZEN by the `ac-signoff` fence (`ac_hash a2bb3913f2c8`) and are
not touched by this spec — see §0.

### §0 — Where this spec's refinements live, and why not in the fences

`hash_section` freezes the WHOLE body of `## Intent` and `## Acceptance Criteria`, nested `###`
subsections included, and `docs/spec-reviews/WI-033-dave-review-2026-09-28.md` records the frozen bytes:
they include the section's `**DRAFT — not frozen.**` preamble and all of `### Examples of done`. So every
byte of that span is a signed artifact now, the preamble's own sentence included — it is left
byte-identical deliberately, and the `ac-signoff` fence beneath it is the operative status. One
consequence governs this whole section: **the five residual notes rounds 3 and 4 left for the spec-writer
are resolved HERE, in unsigned prose the builder reads, rather than by editing a signed fence.** A
within-spirit edit would invalidate the signature and buy a re-sign for text that changes no behaviour;
the builder executes `## Design` and `## Implementation Plan`, so a resolution stated here is binding
where it is needed. Nothing below weakens, rewrites or excepts a criterion; each entry says which clause
it reifies and the reifications are asserted, not merely written.

- **(R1) AC-1(c2)'s guard-set EQUALITY is reified (round 3 note 1, round 4 note 3).** Read literally the
  clause cannot hold: the `-->`/`<!--` guard is HAL9000's own, so those probes sit on the capture's
  REFUSE side and cannot appear in "capture-ACCEPTED". The operative form, and the one the builder
  implements: **both sides are derived from the capture, and the right-hand side is the capture's
  `accept` probes FILTERED by this document's four guard predicates** (§1.4) — never a typed list. The
  assertion is `{p for p in accept_probes if library_refuses(p)} == {p for p in accept_probes if
  guarded(p)}`, with a non-vacuity assertion that the second set is non-empty. At the capture's HEAD that
  set has exactly FIVE members and the data-premise gate already named them (`text` containing `-->`,
  `text` containing `<!--`, and a discriminator that is empty, whitespace-only or `:`-bearing); five is
  recorded here as INFORMATIONAL and is never a pinned count, because a re-run capture may probe more
  boundary values and the filter is what makes the clause survive that.
- **(R2) AC-1(a2)'s "the set of kinds the capture holds" means the `## Parity samples` section's kinds
  (round 3 note 2, round 4 note 3).** The `## Validation boundary` section deliberately probes
  `kind: deal-closed` — a slug-valid kind no sample renders — which must NOT be in `PARITY_KINDS` or
  (a2)'s own "a member with no sample is RED" fires. The equality's right-hand side is therefore
  `{sample["kind"] for sample in parity_samples}` and nothing else.
- **(R3) AC-3(d)'s undeclared-company corner is stated (round 3 note 3).** Writing the rule into the
  person body means an UNDECLARED write on a note that is semantically a company is ALSO refused for
  carrying `introduced_by` — it falls through `obsidian_schemas/name_gate.py:gate_write:373` exactly as
  an undeclared person write does. That is the ruled trade: covering the undeclared PERSON route (P10)
  matters more than exempting an undeclared COMPANY one for a key nothing may carry, and the live
  exposure is nil because all five driven arms derive a declaration
  (`obsidian_schemas/writer.py:update_frontmatter_field:386`,
  `obsidian_schemas/writer.py:update_frontmatter_fields:444`,
  `obsidian_schemas/repositories/base.py:update_fields:729`). AC-3(d)'s company/book exemption is about
  DECLARED `company`/`book` payloads, which return at `:373` before the rule.
- **(R4) AC-1(e)'s anchoring is a READ; the write path is untouched (round 4 note 2).** The typed arm
  locates `## Timeline` for the dedupe test by READING
  (`obsidian_schemas/body_sections.py:get_section:137`, which is `parse_body_sections` one frame in). The
  WRITE remains the shipped string insertion at
  `obsidian_schemas/repositories/person.py:append_to_timeline:1543-1545`, and the no-`## Timeline`
  accommodation at `:1512-1537` is not touched: its comment states at length why the
  `parse_body_sections`/`write_body_sections` round trip must never be the write mechanism (it keeps only
  `^## `-delimited spans, so it deletes a preamble and destroys a heading-less body). §2 states this as a
  rule so a builder cannot satisfy AC-1(f)'s placement clause while re-opening that data-loss guard.
- **(R5) A provenance-less `Person` is answered by mirroring the door (round 4 note 1).**
  `introduced_by` resolves the note by `_resolve_write_target` first and `get_file_path(person.name)`
  second and refuses third — byte-for-byte the two-step at
  `obsidian_schemas/repositories/person.py:append_to_timeline:1489-1493` — so
  `append_to_timeline(p, e)` followed by `introduced_by(p)` cannot read a different note than the one
  just written. §3 states it; §5's Edge Cases carry the refusal.

### §1 — The new leaf module `obsidian_schemas/timeline_entry.py`

A LEAF whose only intra-package import is `errors` (matching `obsidian_schemas/name_gate.py`'s stated
leaf discipline at `name_gate.py:14-20`). It imports `re`, `dataclasses`, `datetime` and `typing` from
the stdlib and nothing else. It must NOT import `writer`, `parser`, `vault_io`, `models`,
`body_sections` or anything under `repositories/`.

**It reads no clock.** HAL9000's module ships a `_now()` for its HTTP door's convenience
(`docs/wi-033-hal9000-timeline-entry-capture.md`, part 1, `core/timeline_entry.py:115-122`); the library
does not relocate it. `when` is always the caller's, which is what makes every render reproducible and is
the property AC-1(a)'s oracle rests on. This is a deliberate non-relocation, not an omission: a clock
read is not part of the vocabulary, and a library that had one would let a caller mint an entry whose
bytes no test can predict.

#### §1.1 One kind grammar, three uses

The kind slug is written ONCE and the heading and marker patterns are composed from it, so the module
cannot disagree with itself about what a kind is:

```python
_KIND_BODY = r"[a-z][a-z0-9_-]{0,31}"
KIND_PATTERN = re.compile(rf"^{_KIND_BODY}$")
HEADING_PATTERN = re.compile(rf"^### (?P<date>.+?) \[(?P<kind>{_KIND_BODY})\] *$", re.MULTILINE)
MARKER_PATTERN = re.compile(
    rf"^<!-- (?P<kind>{_KIND_BODY}):(?P<day>\d{{4}}-\d{{2}}-\d{{2}}):(?P<discriminator>.+) -->$",
    re.MULTILINE)
```

`KIND_PATTERN` is HAL9000's, verbatim from the capture's part 1
(`KIND_PATTERN = re.compile(r"^[a-z][a-z0-9_-]{0,31}$")`) — the OPEN slug rule D8 rules as the write
door. `MARKER_PATTERN`'s shape is the capture's `render` output read back: `<!-- {key} -->` on its own
line, `(?P<discriminator>.+)` non-empty. `HEADING_PATTERN` is date-AGNOSTIC — it captures the date text
and never parses it, which is the whole of why the three legacy heading grammars (43 `Month D, YYYY` /
38 ISO-with-time / 5 bare ISO, `docs/wi-033-intro-corpus-baseline.md`) cost this item nothing.

Two properties of these patterns are DECLARED rather than discovered, because each bounds the module's
reach and a later reader must be able to falsify the claim:

- **Line-anchored under `re.MULTILINE`.** A marker that is not alone on its line is invisible to
  `parse_markers`, and so is a marker on a CRLF line (`$` matches before `\n`, so a trailing `\r` leaves
  ` -->$` unmatched). This is identical to the predicate the live census used
  (`docs/wi-033-intro-corpus-baseline.md`, `## Definitions`: `^<!-- (?P<kind>…):(?P<day>…):(?P<disc>.+) -->$`),
  so the library's reach EQUALS the measured population by construction — the 22-of-86 legacy markers,
  the one live `intro-by` and the three `merge` markers are exactly what it sees.
- **The kind is bounded at 32 characters and the census's predicate was not** (`[a-z][a-z0-9_-]*`). A
  33-character kind on disk would be visible to the census and invisible to the library. Declared
  immaterial by measurement: the census found seven kinds, the longest 8 characters
  (`intro-by`/`intro-to`). One grammar bounded by the write door is worth more than agreement with a
  one-off measuring script.

#### §1.2 Types

```python
@dataclass(frozen=True)
class TimelineEntry:
    kind: str
    text: str
    when: datetime
    discriminator: Optional[str] = None
    # __post_init__ validates; see §1.4

class Marker(NamedTuple):
    kind: str            # the marker's own kind slot
    day: date            # parsed from the day slot
    discriminator: str   # VERBATIM from the discriminator slot
    source: str          # the verbatim marker line, exactly as it appears on the page

class Entry(NamedTuple):
    kind: str                  # the heading's kind slot
    date_text: str             # the heading's date text, UNPARSED
    body: str                  # the heading's own body, to the next `^#{2,3} ` line
    marker: Optional[Marker]   # the well-formed marker inside that body, or None

@dataclass(frozen=True)
class IntroRecord:
    introducer: str   # the counterparty, verbatim from the marker's discriminator slot
    date: date        # from the marker's day slot
    source: str       # the verbatim marker string the record was read from
```

`IntroRecord` lives HERE rather than in `repositories/person.py`, so a consumer imports the vocabulary
and its record type from one module and no second dataclass declares the same three fields.

#### §1.3 Functions, and the bytes

```python
def render(entry: TimelineEntry) -> str
def dedupe_key(entry: TimelineEntry) -> Optional[str]
def dedupe_probe(entry: TimelineEntry) -> Optional[str]
def parse_markers(timeline_text: str) -> list[Marker]
def parse_entries(timeline_text: str) -> list[Entry]
```

`render` emits, byte for byte, what the capture's `render` emits:
`### {month} {day}, {year} [{kind}]\n{text}\n` plus `<!-- {key} -->\n` when a key exists — the HTML
comment OMITTED, never emitted empty. The heading date is composed as
`f"{entry.when.strftime('%B')} {entry.when.day}, {entry.when.year}"` rather than with HAL9000's
`strftime('%B %-d, %Y')`. The bytes are identical (`%-d` is the no-pad day, which is `.day`), and the
substitution drops a platform-specific `strftime` extension the library would otherwise carry into every
consumer. `%B` stays, so both sides remain locale-sensitive in exactly the same way — a non-English
locale moves both identically, and the corpus on disk is English. AC-1(a) proves the equality against the
capture's own six samples.

`dedupe_key` is `f"{kind}:{when:%Y-%m-%d}:{discriminator}"`, `None` when there is no discriminator,
discriminator VERBATIM (no slug, no case-fold — the capture's own rule, "or `Sören Winter` and
`Søren Winter` would collide"). `dedupe_probe` is the delimited form `f"<!-- {key} -->"`, `None` when the
key is: it is the ONE string the door's dedupe test uses, so a key that is passed can never fail to be
the key that was embedded.

`parse_markers` is a flat `MARKER_PATTERN.finditer` in DOCUMENT ORDER, which is newest-first for stored
entries (P3: `append_to_timeline` prepends). It yields a `Marker` only when the day slot parses through
`date.fromisoformat`; an impossible date (`2026-13-45`) is a marker the library does not recognise, and
it is REPORTED by the linter's `intro_by_without_marker` rather than raised on. That direction is
deliberate and is the one place this module departs from the package's loud-fail idiom: the write door
refuses loudly (§1.4), and a READER over arbitrary vault bytes must not let one bad note poison a whole
scan — `lint_vault` walks 5,664 files.

`parse_entries` is the heading-anchored reader the linter needs: `HEADING_PATTERN.finditer` for the
heading, the body running to the next `^#{2,3} ` line (the census's own body definition), and
`marker` = the FIRST `Marker` that `parse_markers` returns over that body, or `None`. It calls
`parse_markers` rather than re-matching, so "well-formed" is ONE predicate in this module and
`intro_by_without_marker` reports exactly the entries the accessor cannot see. It exists so
`scripts/lint_vault.py` can ask "this heading's entry has no marker" without owning a grammar.

`Marker.source` is the regex match's own text — `m.group(0)`, the marker line WITHOUT its trailing
newline, since `$` is zero-width. Stated because AC-2 pins `source` byte-for-byte against "the marker
substring present in that note's own text".

#### §1.4 Validation — HAL9000's rules, plus exactly four declared guards

Reproduced from HAL9000 (capture part 1), refusing on the same inputs:

| Field | Refused when |
| --- | --- |
| `kind` | not a `str`, or does not match `KIND_PATTERN` |
| `text` | not a `str`, or empty after `.strip()` |
| `discriminator` | not a `str` and not `None`; or contains `-->`, `<!--`, `\n` or `\r` |

The library's FOUR OWN guards — the complete set of inputs HAL9000 accepts and the library refuses, which
is the enumerated exception AC-1(c2) asserts as an equality:

1. `text` contains `-->` — it would terminate the comment the entry's own marker opens.
2. `text` contains `<!--` — it would forge a second marker through the prose channel, which is the one
   place a text channel can corrupt a machine channel.
3. `discriminator` is empty or whitespace-only — the rendered marker would either be unreadable by
   `MARKER_PATTERN` (empty) or would key every same-kind, same-day entry onto a blank counterparty
   (whitespace). Either way the entry the door writes is one the accessor cannot honestly answer from.
4. `discriminator` contains `:` — the key separator. `parse_markers` still READS such a marker off disk
   (the pattern takes the rest of the line), so nothing on disk becomes invisible; what is refused is
   MINTING a new key that a consumer splitting on `:` reads as a different kind/day/counterparty triple.

The guard is on CONSTRUCTION only. Stating that split matters: the library is stricter than HAL9000 at
the write door and exactly as permissive as the census at the read door.

Refusals raise `TimelineEntryRefusal`, a new leaf of `LoudFailError` added to
`obsidian_schemas/errors.py` beside `NameGateRefusal` (`errors.py:NameGateRefusal:106`), declaring no
`__init__` — the hierarchy's one constructor is what bounds the message — and carrying a `pattern`
attribute set AFTER construction, exactly as `NameGateRefusal.pattern` is. It needs ONE new member in
`errors.py:REASONS:152`, because `bounded_message` refuses any reason that is not an enumerated literal
(`errors.py:bounded_message:177-188`): `"a timeline entry field this package refuses"`. The refusal
`pattern` values are module-level literals in `timeline_entry.py` — `KIND_PATTERN_KEY = "kind_not_a_slug"`,
`TEXT_EMPTY_KEY`, `TEXT_FORGERY_KEY`, `DISCRIMINATOR_TYPE_KEY`, `DISCRIMINATOR_FORGERY_KEY`,
`DISCRIMINATOR_EMPTY_KEY`, `DISCRIMINATOR_SEPARATOR_KEY` — following WI-032's precedent exactly
(`name_gate.py:WHATSAPP_PATTERN:90`: the gate's OWN literal, never a `NameValidator` branch record). No
note-derived value reaches the constructor; the refused VALUE is not passed at all, because at this door
the refused value is a person's name or a note's prose (the rule `name_gate.py:_refuse:174-192` exists
for).

#### §1.5 The parity universe and the staleness anchor

```python
PARITY_KINDS = frozenset({"intro", "intro-by", "intro-to", "merge", "note"})
HAL9000_PARITY_ANCHOR = "d54430da9547a93525c6cc1b20cf781c9a63f82e"
INTRO_BY_KIND = "intro-by"      # WI-077, on the INTRODUCEE's note — the accessor's only source
INTRO_TO_KIND = "intro-to"      # WI-077, the introducer-side mirror
LEGACY_INTRO_KIND = "intro"     # OUTBOUND; never a source for the accessor (ruling §2)
```

Both literals are FROZEN, not LIVE (WI-295): the capture is a committed artifact at a fixed 40-hex HEAD
and its epoch is closed, so an equality pin is legal — and both are nonetheless ASSERTED against the
file rather than trusted (AC-1(a2), AC-1(a3)). `PARITY_KINDS` gates nothing: no `TimelineEntry`
construction, no `render`, no `dedupe_key`, no `parse_markers` and no `parse_entries` call reads it
(D8, machine-checked by AC-1(a4)'s planted `deal-closed`). Its only readers are the two derived sweeps'
fixture spaces.

### §2 — The door: `append_to_timeline`'s typed overload

`obsidian_schemas/repositories/person.py:append_to_timeline:1452` becomes:

```python
def append_to_timeline(self, person: Person,
                       entry: Union[str, TimelineEntry],
                       deduplicate_key: Optional[str] = None) -> bool
```

Flow, with every branch named:

1. **A `TimelineEntry` AND a `deduplicate_key`** — refused with `TimelineEntryRefusal`, pattern
   `BOTH_ENTRY_AND_KEY_KEY`. The typed path derives the key; a caller supplying a second one is asking
   the door to disagree with itself, which is the defect AC-1(d) exists to close.
2. **A `TimelineEntry`** — `rendered = render(entry)`, `probe = dedupe_probe(entry)`. Dedupe is
   MARKER-ANCHORED: inside the lock, read the note, split the fence
   (`person.py:_split_frontmatter_fence:96`), take `get_section(body, "Timeline")`, and skip iff any
   `Marker` that `parse_markers` returns over THAT SPAN has a key equal to `dedupe_key(entry)`. Not a
   substring test at all: a `## Notes` line quoting the key verbatim is outside the span, and a quoted
   key inside the span that is not a well-formed marker line does not match. A `None` key — an entry with
   no discriminator — means NO DEDUPE (the capture's own rule: a free-text note has no event identity, and
   inventing one would suppress a second, genuinely intended note), so AC-1(d)'s "the same entry twice
   writes once" is about a DISCRIMINATOR-BEARING entry and two identical `note` entries legitimately write
   twice. `get_section` is `parse_body_sections` one frame in
   (`obsidian_schemas/body_sections.py:get_section:137`), which is what AC-1(e)'s span wording and
   AC-2(a2)'s `parse_body_sections` wording both name.
3. **A `str`** — byte-for-byte today's behaviour, INCLUDING the whole-file substring dedupe at
   `person.py:1502`. That looseness is load-bearing for a live caller: precondition 3's cross-repo
   reading item 2 records exocortex's kindless meeting writer
   (`ingestion/stages/note.py:375`) deduping on a bare meeting stem matched whole-file, and narrowing it
   would duplicate a meeting line on every hourly re-run. AC-1(f)'s "keeps working unchanged" is this
   branch.
4. **The write** — identical for both branches and unchanged: prepend after the `## Timeline` marker
   (`person.py:1543-1545`), or create the section at end of file by string insertion when the marker is
   absent (`person.py:1512-1537`). **The anchoring in step 2 is a READ and the write path is not
   touched** (R4): no `write_body_sections` round trip is introduced anywhere on this path.
5. **Returns** — `True` when written, `False` ONLY for the deliberate dedupe no-op, as today.

The existing three-argument string call is unchanged for all six live callers precondition 3 measured
(all pass a `str`, so the typed overload has ZERO callers on the day and the narrowing touches no live
call).

### §3 — The accessor `PersonRepository.introduced_by`

```python
def introduced_by(self, person: Person) -> list[IntroRecord]
```

1. Resolve the note: `self._resolve_write_target(person)`
   (`obsidian_schemas/repositories/base.py:_resolve_write_target:392`), else
   `self.get_file_path(person.name)`; if neither yields an existing path, raise
   `ValueError(f"Person file not found: {person.name}")` — the same expression the door raises at
   `person.py:1493` and at five sibling doors in that module. Mirroring the door is the point (R5): the
   READ and the WRITE must agree about which note is this person's note, or WI-029's divergence class
   re-opens on the one seam it just closed.
2. `content, _stamp = vault_io.read_note(file_path)` — NO lock. `vault_io.read_note:641-663` sanctions
   the unlocked read in its own contract ("a read outside the lock cannot lose a note … enforcing it
   would forbid the legitimate unlocked read"), and `write_note` is atomic, so a concurrent writer
   yields old bytes or new bytes and never torn ones.
3. `_, body = _split_frontmatter_fence(content, file_path)`; `timeline = get_section(body, "Timeline")`.
   `None` (no `## Timeline` section at all) returns `[]`.
4. `[IntroRecord(introducer=m.discriminator, date=m.day, source=m.source)
   for m in parse_markers(timeline) if m.kind == INTRO_BY_KIND]`.

Four properties, each a rule rather than an accident:

- **THE FILTER IS THE EXACT SLUG** `INTRO_BY_KIND`, never a substring and never `PARITY_KINDS`
  membership. A kind the library never captured yields no record and does not raise (AC-2(a)).
- **THE MARKER IS THE ONLY CHANNEL** (D1). Not the heading, not the prose, not frontmatter. This is why
  `parse_markers` and not `parse_entries` is the accessor's reader: the heading is presentation.
- **THE READ IS SCOPED TO THAT PERSON'S OWN NOTE.** No glob, no vault-wide scan, no repository index
  walk. AC-2(a2) asserts it in both directions on both people plus invariance to the other note's
  removal.
- **`source` IS THE BYTES ON THE PAGE** — `Marker.source` is the matched marker line verbatim, so a
  consumer that disagrees with the accessor has the exact substring to quote.

`obsidian_schemas/__init__.py` exports `TimelineEntry`, `IntroRecord`, `Marker`, `Entry`,
`TimelineEntryRefusal`, `render`, `dedupe_key`, `dedupe_probe`, `parse_markers`, `parse_entries`,
`PARITY_KINDS`, `HAL9000_PARITY_ANCHOR`, `INTRO_BY_KIND`, `INTRO_TO_KIND`, `LEGACY_INTRO_KIND` and adds
each to `__all__`. AC-2(e)'s closing clause ("`introduced_by` is exported from the package so a consumer
has a typed route") is satisfied by `IntroRecord`: the accessor is a method on the already-exported
`PersonRepository`, so what a consumer needs importable is the record type it returns.

### §4 — The gate rule

`obsidian_schemas/name_gate.py` gains two literals and one arm:

```python
RETIRED_PERSON_KEY: str = "introduced_by"     # ruling §1 — retired, not modelled
RETIRED_KEY_PATTERN: str = "retired_person_key"
```

**Placement, measured rather than chosen (P10).** The arm is a new section `3c`, INSIDE the person body
— below the declared-non-person early return at `name_gate.py:gate_write:373-398` — and immediately
AFTER the WhatsApp arm (`3b`, `:437-446`), before section 4's address normalization:

```python
if RETIRED_PERSON_KEY in introduced:
    _refuse(RETIRED_KEY_PATTERN, refused_value=RETIRED_PERSON_KEY)
```

Three reasons for that exact position, each quoting the code's own argument:

- **In the person body, not keyed on `declared_type == PERSON_TYPE`.** `:373`'s
  `declared_type is not None and declared_type != PERSON_TYPE` is guarded that way precisely so "an
  UNDECLARED write that introduces identifiers but NO `name:` must fall THROUGH" (`:364-368`). A rule
  keyed on the equality would leave a person note missing its `type:` free to carry the key.
  `company` and `book` are exempted for free by that same return (R3 states the undeclared-company
  corner).
- **After the name arm and the WhatsApp arm.** `3b`'s own comment states why its position is prescribed:
  corpus notes declare a refusal `Verdict` naming a NAME pattern and write their whole declared field set
  through the gated door, so keeping the name refusal first makes those declarations true BY
  CONSTRUCTION. A third arm inherits the same obligation, and it is not a name judgement either.
- **Before section 4.** Nothing is normalized on a payload that is about to be refused, and the refusal
  lands before any write in every arm.

`refused_value` carries the KEY and never the key's value (D4): at this arm the value is a person's name,
and `_refuse`'s rule 2 (`name_gate.py:_refuse:174-192`) exists to keep note-derived identity out of
refusals. `pattern` is a source literal, set as an attribute after construction, reaching no message.

One rule, one place, every arm (P8): `gate_write` has six call sites and the rule is written once.

### §5 — `lint_vault`'s three report-only detectors

All three land in `scripts/lint_vault.py:check_structural:366`, category `"structural"`, modelled
byte-for-byte on the shipped `whatsapp_not_storable` arm (`lint_vault.py:475-503`): report-only,
`auto_fixable` left at its `False` default, with the comment that arm already carries about the
four-bucket accounting. They are NOT added to `check_timeline`, and that is a decision rather than
taste: `check_timeline` walks `idx["meetings"]`/`idx["persons"]` and its leading comment
(`lint_vault.py:740-745`) states that it never iterates `files` and therefore owes no `read_error`
decline. A file-walk added there would make that comment false; `check_structural` already walks `files`
with the `read_error`/`parse_error` guards FIRST (`:378-397`), which discharges AC-4(f) with no new guard
code at all.

**Position inside the loop: immediately after the `parse_error` guard (`:397`) and BEFORE the
`no_frontmatter` arm (`:399`).** The four arms below it (`no_frontmatter`, `missing_type`,
`if not vf.entity_type`, the `TYPE_TO_MODEL` skip) all `continue`, and each is type-scoped triage — a
retired key on an untyped note is exactly the route AC-3(a) keeps closed, and `[intro]` entries are
counted by the census over every `*.md` rather than over typed person notes.

| check id | severity | fires on | message carries |
| --- | --- | --- | --- |
| `legacy_intro_entry` | WARNING | every `Entry` in the note's `## Timeline` whose kind is `LEGACY_INTRO_KIND` | the heading's own text (kind + date text), naming the note through `LintIssue.file_path` |
| `intro_by_without_marker` | WARNING | every `Entry` whose kind is `INTRO_BY_KIND` and whose `marker` is `None` | the heading's own text |
| `retired_key_introduced_by` | ERROR | every note whose frontmatter carries `RETIRED_PERSON_KEY`, of ANY type and of none | the key name, never its value |

**Why the detector's reach is wider than the gate's, stated so the two do not read as a contradiction.**
The GATE refuses exactly where the ruling retires the key — a person-declared or undeclared write (§4,
R3) — because refusing a `company` write would be an unsigned subtraction (AC-3(d)). The DETECTOR reports
every carrier whatever its `type:`, because the key is retired as a VOCABULARY matter and a note the
report skipped would be a note nobody could find; the report costs a line and repairs nothing. Live yield
is 0 either way (`docs/wi-033-intro-corpus-baseline.md`: `introduced_by_frontmatter_carriers: 0`).

All three read the LIBRARY's grammar. `scripts/lint_vault.py` adds
`from obsidian_schemas.timeline_entry import (INTRO_BY_KIND, LEGACY_INTRO_KIND, parse_entries)` beside
the library imports it already carries (`lint_vault.py:38-60` imports `body_sections`, `gate_write`,
`identifier` and `vault_io`), and `RETIRED_PERSON_KEY` from `obsidian_schemas.name_gate`. The two
timeline detectors call `parse_entries(get_section(vf.body, "Timeline") or "")`. The script defines NO
pattern of its own and no delimiter literal — AC-2(e)'s scan asserts exactly that, and the IMPORT is
asserted by OBJECT IDENTITY (`lint_vault.parse_entries is timeline_entry.parse_entries`), which proves
the import rather than a spelling of it.

`intro_not_symmetric` (`lint_vault.py:check_timeline:814-834`) is untouched (P7): it is the evidence the
Intent's boundary claim rests on, its prose regex contains no marker delimiter so it is outside AC-2(e)'s
predicate by construction, and removing a shipped report is a separate subtraction with its own audit.

### §6 — The fixture re-key, and the pool constraint that decides its value

`tests/fixtures/vault/@Morvette Harkwell.md:16` becomes `manager: "Oskaline Thrandell"`, and
`tests/fixture_vault.py:325`'s `undeclared={"introduced_by": "Voxleaf"}` becomes
`undeclared={"manager": "Oskaline Thrandell"}`. `CORPUS_DIGEST` (`tests/fixture_vault.py:44`) is
regenerated by the one command that module documents at `:24-25`.

**D9 — the swapped value is a FRESH COMBINATION of CERTIFIED tokens, never a fresh token, and the
constraint is structural.** D3 said "chosen FRESH … a name the identifier index cannot resolve". Read as
"an invented name" that is UNBUILDABLE, and the wall is worth naming because it is invisible until the
floor reddens: the manifest's `undeclared` VALUES are identity positions by AC-5(b) clause 3 and enter
`tests/test_fixture_vault.py:_identity_text:994-1016`, every identity token must be in
`fixture_vault.py:NAME_POOL:591` (or `CONNECTIVE_SET`, or an admitted org suffix), and
`NAME_POOL ⊆ docs/vault-shape-census.md`'s pool table, where each row carries the conductor's live-vault
NON-OCCURRENCE command and its verbatim stdout. A new token would need a new census row — a live
measurement the caged builder cannot make, in a digest-frozen document
(`test_fixture_vault.py:assert_census_is_frozen`). So: both tokens are existing `NAME_POOL` members
(`Oskaline`, `Thrandell`), and the PAIR is not any corpus note's name, stem, alias or title, which is
what makes it resolve to nothing and carry no second job — D3's actual intent, satisfied without
touching the census. `Voxleaf` stays certified and stays used (`@Voxleaf Ltd.md`), so the non-vacuity
clause (`NAME_POOL - id_tokens == ∅`) is unaffected in both directions.

**The manifest comment at `tests/fixture_vault.py:323-324` is left BYTE-IDENTICAL.** `reach_files()`
(`test_fixture_vault.py:386-392`) scans `tests/fixture_vault.py` itself, so every capitalized word in
that file is an extracted token that must be in `PROSE_ALLOWLIST` (`fixture_vault.py:615`) unless it is
an identity token. Re-wording the comment is a ratchet paid for nothing; only the dict literal moves.

**`docs/vault-fixtures.md:279` is a CONDUCTOR-COMMITTED PRECONDITION, not a builder write.** The
sentence "a `manager:` or `introduced_by:` on a schema-drift or forward-compatibility note" must read
`manager:` alone (AC-3(c)). That file is ANOTHER item's tracked work-item document (WI-016, `id: WI-016`
in its frontmatter), and since WI-245 the merge boundary admits a declared cross-doc edit only when it is
**additive prose outside every fence**. This edit REPLACES prose, so a caged builder's write to it is
refused at the merge boundary — the failure WI-245 says costs a conductor hand-landing plus a relaunch.
Declared instead as a fifth `kind: precondition` fence in `## Write Targets`. Two things make that safe
rather than a hope: the same sentence is also inside WI-016's SIGNED AC-5 fence at `:1434`, which is
**not** in scope and must not be touched (moving a typed parse of another item's doc is exactly what the
merge rule forbids, and it is another item's signed criterion); and the PRE-DRIVE floor check (WI-156 /
WI-164) is clean — no test in this tree reads `:279`'s prose, so the doc edit participates in no
bijection or symmetry invariant and needs no atomic landing with the builder's re-key. AC-3(c)'s own
check is what makes the edit verifiable at all, since a precondition probe reads presence and the file is
already in HEAD.

### §7 — Configuration

None. No setting, threshold, toggle, env var or flag is introduced. `lint_vault`'s three new checks are
always on, in the `structural` category, and `--category structural` already selects them; nothing is
gated behind a flag, because a report-only detector's cost is a line of output.

### §8 — Prerequisites & Assumptions

1. **Five conductor-committed preconditions in git HEAD before the build is armed** — the four already
   committed (`docs/wi-033-hal9000-timeline-entry-capture.md`, `docs/wi-033-intro-corpus-baseline.md`,
   `docs/wi-033-consumer-audit.md`, `docs/wi-033-hal9000-cutover-followup.md`) plus §6's
   `docs/vault-fixtures.md` edit. Each is declared as a `kind: precondition` fence.
2. **No live vault, no network, no service.** The floor is hermetic by WI-031 clause (v); HAL9000,
   exocortex, orchestrator and mainspring need not be running and are not called. Every live fact this
   item rests on is read from a committed precondition and never re-measured.
3. **The project interpreter.** `pipeline-runners.yaml` declares `seed_deps: [.venv]` and no `commands:`
   or `ac_runner:` block, so (a) the floor command is
   `/Users/davewascha/Workspaces/obsidian-schemas/.venv/bin/python -m pytest <tree>/tests -q`, (b) there
   is NO registered `command_id`, so no task may declare `verify: cmd:…`, and (c) every AC check is
   discovered by its bare top-level `def` and invoked with zero arguments under the conveyor's own
   interpreter. Therefore **every new check module begins with
   `from tests.ac_interpreter import ensure_project_interpreter` / `ensure_project_interpreter(__file__)`
   BEFORE any package import**, as `tests/test_stem_name_divergence_detector.py:38-40` does; without it
   the check is RED at `building → done` under an interpreter that cannot import pydantic.
4. **Trust boundary.** Vault bytes are UNTRUSTED input, and this item adds two readers of them
   (`parse_markers`, `parse_entries`) plus one accessor. Neither reader raises on hostile bytes; neither
   is used to build a path, a command or a write. The WRITE side is where validation lives, and it is
   total over the three fields (§1.4). Nothing is interpolated into a shell, a query or an error message.
5. **`PARITY_KINDS` and `HAL9000_PARITY_ANCHOR` are only as true as the capture**, which freezes HAL9000
   at one HEAD. Drift in HAL9000's own copy during the window between this item and the minted cutover
   (HAL9000 WI-082) is UNDETECTED by this tree's floor — accepted in writing by D7, not mitigated.
6. **WI-034 is folded** (ruling §2) and nothing else is waiting: WI-029's provenance seam and WI-032's
   list shape are shipped.

### §9 — What each touched file joins: the standing walls (WI-301)

DERIVED, not remembered: the population was found by sweeping `tests/` for modules that read the text of
files they did not name at authoring time — i.e. every module that calls
`tests/derivations.py:python_files_under:185` over `PACKAGE_ROOT` / `TESTS_ROOT` / `SCRIPTS_ROOT`, plus
the two markdown/corpus sweeps that reach files by `rglob` and `iterdir`. **This census is a FLOOR
measured on 2026-09-28 and never a total** — this derivation has under-reached at its reading step every
time it has been run in this factory, which is why Task 11 RUNS each predicate on the files' FINAL text
rather than reasoning about which shapes match, and why anything the run returns that this table does not
name is NAMED in the Build Log and satisfied, never worked around and never satisfied by narrowing the
wall.

| Wall (its own shipped predicate) | What it requires of this item's files |
| --- | --- |
| `modules_using_ast` == `{"tests/derivations.py"}` — asserted from `tests/test_fixture_vault.py:1383`, `test_name_gate_wall.py:1136`, `test_lint_vault_fix_rules.py:1957`, `test_loud_fail_harness.py:103` | NO new file may import or use `ast`. Both new derivations live in `tests/derivations.py`; the new test modules call them and never parse source themselves. |
| `skip_reason_literal_sites(…, SKIP_REASONS)` == `{base.py, tests/test_fixture_vault.py}` — `test_fixture_vault.py:1392`, `test_lint_vault_fix_rules.py:1963`, `test_whatsapp_migration.py:968`, `test_provenance_write_seam.py:1857` | No new file may hand-type a skip-reason literal. None does. |
| `frontmatter_write_arms(PACKAGE_ROOT, SCRIPTS_ROOT)` — `test_company_name_contract.py:621`, `test_lint_vault_fix_rules.py:1971` (`apply_fixes` == exactly one arm) | The typed overload writes a BODY through `vault_io`, introducing no frontmatter write arm; the gate arm adds none. |
| `character_class_strip_sites` == `[]` and `address_splitting_implementations` == `set()` over package+scripts — `test_address_splitter.py:102`, `test_lint_vault_fix_rules.py:1987` | `timeline_entry.py` must not roll a negated-character-class strip and must not parse an address. It does neither. |
| `gate_call_declarations` / `gate_call_placement` — `test_name_gate_wall.py` | The new gate arm adds no `gate_write` CALL and no new frontmatter arm, so both derived pins are unmoved. Task 6's new `gate_call_sites` derivation is additive. |
| `write_target_buckets` / `door_calls_inside_note_lock` / `non_completed_write_sites` / `falsy_returns_in(COMMIT_FUNCTION_NAMES)` — `test_write_target_seam_wall.py:227`, `test_provenance_write_seam.py:425,1274`, `test_write_routing.py:466` | The accessor is a READ and adds no write site; the typed arm reuses the existing `vault_io.write_note` calls inside the existing lock. `append_to_timeline` is not in `COMMIT_FUNCTION_NAMES`, so its deliberate `False` stays legal. |
| `NO_ARG_CONSTRUCTION` over every repo `*.md` outside `docs/`/`state/` — `test_vault_path_required.py:443-459`, re-run over the corpus by `test_fixture_vault.py:1414` | The edited corpus note must not contain `…Repository()`. It does not. (`docs/**` is excluded, so this document and the preconditions are out of reach.) |
| `test_fixture_vault.py:test_fixture_vault_is_frozen_and_materialized_by_byte_copy` + `test_no_corpus_note_carries_a_live_identifier` | `CORPUS_DIGEST` regenerated in the same commit as the note edit; the swapped value's tokens in `NAME_POOL` (§6); no new prose token in the manifest. |
| `test_fixture_vault.py:1419-1431` (W-14, pytest collection globs) and `check_module` uniqueness (W-10, `test_ac_interpreter.py:95-106`) | The three new test modules match `test_*.py` and each defines a check name that resolves to exactly ONE module tree-wide. Task 11 asserts the second by CALLING `check_module` on all four AC check names. |
| `test_lint_vault_fix_rules.py:288` — the five-clause containment wall over that module's OWN source | Task 9's additions there take their vault from `_temp_vault(root)`, bind it to the identifier `vault`, name no live-path token outside that door, and construct no repository. |
| `test_lint_vault_fix_rules.py:822` — `len(pinned) == 7` over `auto_fixable_emitter_checks + GARBAGE_CHECKS` | The three new checks are NOT auto-fixable, so the pin stays at 7. It is re-read rather than edited (Task 12), and it is the evidence for AC-4(e). |
| `test_lint_vault_fix_rules.py:1703-1708,1775` — `CENSUS_SHAPE_TO_RULE` and `docs/lint-vault-live-baseline.md`'s §1/§4 rows bound to the auto-fixable rule set | Unmoved for the same reason: a report-only rule owes the live baseline no row. This is why report-only is not merely ruling §3's preference but the only arm buildable inside a hermetic cage. |

**The conscious-pin sweep (WI-229).** The countable corpora this item touches are the lint check-id set
and the frozen fixture corpus. Their declaring symbols are
`tests/derivations.py:auto_fixable_emitter_checks`, `auto_fixable_branch_checks`,
`scripts/lint_vault.py:CATEGORY_ORDER` and `tests/fixture_vault.py:NOTES` / `CORPUS_DIGEST`. Reading
every file those symbols reach at FILE granularity returns the pins named in the last three rows above,
plus `CORPUS_DIGEST` itself. The obligation is stated as a predicate and never as a number: **the
auto-fixable rule set does not change, and the digest changes exactly once.**

### §10 — Pattern consistency

Every piece has a model in this tree: the leaf module's import discipline is `name_gate.py:14-20`; the
refusal leaf and its pattern literal are `NameGateRefusal` + `WHATSAPP_PATTERN`; the report-only detector
is `whatsapp_not_storable` (`lint_vault.py:475-503`); the gate arm's placement argument is `3b`'s own;
the accessor's note resolution is `append_to_timeline:1489-1493`; the new check modules' shape — the
interpreter shim first, one `def test_*` calling `_check_*` helpers, the containment wall defined first
where the module drives the linter — is `tests/test_stem_name_divergence_detector.py`; the capture-parsing
test's shape is `tests/test_lint_vault_fix_rules.py:113`'s declared-headings parse of
`docs/lint-vault-live-baseline.md`. The one deviation from a shipped pattern is §1.3's non-raising
reader, justified there.

### §11 — Mechanics a builder would otherwise have to guess

Four, each with the shipped thing to copy rather than a description:

1. **Parsing the capture.** Select the section by its declared `## ` heading, take every fenced block
   whose info string is `yaml` inside that section, and `yaml.safe_load` each one — the capture was
   produced with `yaml.safe_dump`, so the round trip is exact and the `rendered` block scalar's single
   trailing newline is the renderer's own. `yaml` is importable because the interpreter shim re-execs
   under the project interpreter (§8.3); under the conveyor's bare `-S` interpreter it is not, which is
   the whole reason the shim is the module's first statement. Shape to copy:
   `tests/test_lint_vault_fix_rules.py:113` and its declared-headings parse of
   `docs/lint-vault-live-baseline.md`.
2. **Planting source files for the two WI-235 batteries.** `tests/support.py:temp_dir` for the scratch
   root, plus a four-line local `_plant_source(root, name, source)` that writes `root/name` and returns
   the path — the shape `tests/test_lint_vault_fix_rules.py:_plant_source:352` already carries. The
   planted file is handed to the DERIVATION; the test itself never parses source, because `ast` is
   single-homed to `tests/derivations.py` (§9, row 1).
3. **Planting vault notes.** For the accessor and gate checks a plain temp directory plus
   `Path.write_text` is enough — no corpus is needed (D6: these specimens are BEHAVIOURAL and owe the
   census no row) — and each planted `## Timeline` entry is produced by the library's own `render`, so the
   fixture's bytes are the door's bytes. For AC-4's check, `_temp_vault(root)` + `_plant` inside
   `tests/test_lint_vault_fix_rules.py`, which materializes the frozen corpus and refuses a corpus stem.
4. **Constructing a repository.** Every repository in a test is constructed with an EXPLICIT temp path: a
   no-argument construction resolves the LIVE vault from the environment inside the library (WI-031), and
   in `tests/test_lint_vault_fix_rules.py` the containment wall's clause (v) asserts that module
   constructs none at all — so AC-4's check reaches the linter through `lint_vault`'s own entry points and
   never through a repository.

## Verified Diagnosis

Four load-bearing claims about how the current system behaves; if any were false the work would change
shape. Each was re-run this round with Read/Grep at HEAD `133c27a`.

1. **The dedupe contract is a whole-file substring test, and the key can disagree with the marker.**
   `obsidian_schemas/repositories/person.py:append_to_timeline:1502` is literally
   `if deduplicate_key and deduplicate_key in content:` where `content` is the entire note including
   frontmatter and every other body section (bound at `:1499` from `vault_io.read_note`), and `entry` and
   `deduplicate_key` are unrelated parameters (`:1455-1456`). Falsifiable in one read; it is what §2's
   branches 2 and 3 are about.
2. **The writer PREPENDS despite its name.** `person.py:1543-1545` —
   `parts = content.split(timeline_marker, 1)` then
   `parts[0] + timeline_marker + formatted_entry + parts[1]`. Newest-first is therefore the stored order
   and the accessor's declared order.
3. **Nothing in this library defines the vocabulary, and one second copy of a PROSE parser already
   exists.** `**/timeline_entry*.py` over the tree returns no file; `<!--` / `-->` over every `*.py`
   returns zero matches (so AC-2(e)'s scan starts from zero and needs no exemption); and
   `scripts/lint_vault.py:check_timeline:816` is
   `re.compile(r"[Ii]ntroduc(?:ed|tion)[^[]*\[\[(@[^\]|]+)")`, a live prose-parsing specimen, report-only.
4. **The gate structurally cannot distinguish an introduction from a re-emission, so an unconditional ban
   needs an emptied population rather than an exemption.** The gate reads only its arguments
   (`name_gate.py:22-29`); `Person` is `extra="allow"` (`models.py:34-40`); `model_to_frontmatter`
   serializes `model_extra` into every note the library writes (`models.py:45-53`, stated verbatim there);
   and `PersonRepository.save`'s write-back rider hands that whole projection to the gate —
   `gate_write(model_to_frontmatter(entity), declared_type=self.type_name, whole_record=True)`
   (`person.py:1270-1271`). So a `save()` of a note that already carries the key hands the key to the gate
   inside `introduced`. The live population is 0 carriers over 5,664 files
   (`docs/wi-033-intro-corpus-baseline.md`) and the fixture population is exactly one note, which §6
   empties.

## Edge Cases & Open Questions

- **Empty / null / malformed input.** *Case:* a caller passes `kind=None`, `text=""`, a non-`str`
  discriminator, or a `when` that is not a `datetime`. *Decision:* the first three raise
  `TimelineEntryRefusal` with the pattern §1.4 names (the `text` and `kind` rules are HAL9000's, so the
  refusal is parity, not tightening). A non-`datetime` `when` raises `AttributeError` from `strftime` at
  render time and is NOT guarded, because `when` is a required positional with no plausible wrong-type
  caller and a type check there would be the only validation in the module with no capture probe behind
  it. *Reasoning:* the door refuses what a caller can plausibly get wrong from data; a wrong TYPE is a
  programming error that should surface uncaught. *Test:* AC-1(c), AC-1(c2).
- **Malformed input on the READ side.** *Case:* a marker whose day is `2026-13-45`; a marker not alone on
  its line; a CRLF note; a `## Timeline` section containing a quoted key that is not a marker.
  *Decision:* none of these is a `Marker`; `parse_markers` yields nothing for them and raises nothing.
  The linter REPORTS an `intro-by` heading in that state as `intro_by_without_marker`. *Reasoning:* a
  reader over 5,664 untrusted files must not let one note poison a scan, and the narrowing is honest
  because the linter names every entry the accessor cannot see. *Test:* AC-2(c), AC-4(b).
- **Empty / absent sections.** *Case:* a person note with an empty `## Timeline`, with no `## Timeline`
  at all, or with no frontmatter fence. *Decision:* `[]` for the first two; the third raises
  `FrontmatterParseError` from `_split_frontmatter_fence:96`. *Reasoning:* absence of entries is a
  legitimate answer, absence of a parseable note is not. *Test:* AC-2(d).
- **Race conditions / concurrent access.** *Case:* an external writer (Obsidian, HAL9000) lands a write
  between the accessor's read and its caller's use; or two callers append the same entry at once.
  *Decision:* the accessor reads WITHOUT the lock, sanctioned by `vault_io.read_note:641-663`, and
  returns a snapshot; `write_note` is atomic so the read is never torn. The typed append keeps today's
  behaviour — one `note_lock` spanning read, dedupe and write (`person.py:1498-1546`) — so the second
  caller's dedupe test sees the first caller's marker and returns `False`. *Reasoning:* the door's
  existing lock discipline already makes the dedupe correct under concurrency once the test is anchored
  to the marker; widening the accessor to take a lock would forbid the legitimate unlocked read.
  *Test:* AC-1(d) (same entry twice writes once); the existing `tests/test_concurrent_access.py` battery
  is the regression.
- **External dependency failure.** *Case:* HAL9000 unreachable; the vault absent; a precondition file
  missing at test time. *Decision:* no service is called anywhere in this item. A missing note raises the
  door's own `ValueError`. A missing or unparseable capture file makes AC-1's check RAISE rather than
  skip — the test opens `docs/wi-033-hal9000-timeline-entry-capture.md` with no fallback and asserts its
  sample and probe sets are non-empty, because a fence reader that finds nothing is otherwise green
  (this tree's own scar, `tests/test_fixture_vault.py:1451-1454`). *Test:* AC-1(a), AC-1(c2).
- **First-run vs subsequent-run.** *Case:* the first typed append to a note with no `## Timeline`.
  *Decision:* identical to today — the section is created at end of file by string insertion
  (`person.py:1512-1537`) and the entry lands. There is no other first-run difference: no cache, no
  index, no migration, no state file. *Test:* AC-1(f).
- **Migration / backfill.** *Case:* getting from today's state to the new one. *Decision:* there is no
  data migration. The 86 legacy `[intro]` entries stay exactly as they are (A5, ruling §3) and become
  visible through `legacy_intro_entry`; the one stored `introduced_by` value was converted by hand on
  2026-09-28 through the sanctioned doors before this item (ruling §1), so the live population is already
  0; the only "migration" is the fixture re-key in §6. *Reasoning:* a rewrite of the legacy corpus buys
  the accessor nothing (all 86 are outbound) and would need its own WI-032-shaped live bracket.
  *Test:* AC-4(a) reports them; AC-3(c) reads the committed zero as a premise.
- **Idempotency.** *Case:* the same typed entry appended twice; the linter run twice; the builder's
  fixture re-key applied twice. *Decision:* the second append is the deliberate `False` no-op; the linter
  is read-only for these three checks, so N runs yield N identical reports; the re-key is a text edit
  whose second application is a no-op. *Test:* AC-1(d).
- **Retry semantics.** *Case:* a caller retries after a failure. *Decision:* unchanged from the door's
  shipped contract — `ExternalWriteConflict` is retryable (its retry re-reads), `StaleEntityWrite` is
  retryable after `refresh()`, `WriteFailedError` and both refusal leaves are NOT (a refusal is a
  deterministic function of the payload, so an identical retry gets an identical refusal —
  `errors.py:NameGateRefusal:130-134`). `TimelineEntryRefusal` inherits that reading and says so in its
  docstring. *Test:* covered by the existing loud-fail batteries (Regression, below).
- **Partial failure.** *Case:* the refusal fires after part of a write. *Decision:* impossible on both
  new paths. The gate arm refuses before `write_frontmatter` at every driven arm (AC-3(b) asserts NO FILE
  CHANGED); the typed arm's validation happens in `TimelineEntry.__post_init__`, i.e. before the object
  the door receives exists. *Reasoning:* a refusal that fires after a partial write is worse than no
  refusal. *Test:* AC-3(b).
- **Error propagation.** *Case:* what the caller sees. *Decision:* `TimelineEntryRefusal` and
  `NameGateRefusal` are both `LoudFailError` leaves, so `except LoudFailError` still means "this package
  refused"; every ABSORBING handler and every oracle names the LEAF and its `pattern`, per the idiom
  `errors.py:NameGateRefusal:122-128` states. The accessor's "no note" is the door's own `ValueError`.
  No message carries note content, and no refusal is chained to a foreign exception except through
  `chainable_cause`. *Test:* AC-1(c), AC-3(a).
- **Trust boundary crossings.** *Case:* hostile vault bytes reaching the marker readers; a caller forging
  a marker through the `text` channel. *Decision:* the readers are regex matchers over text, build no
  path and execute nothing; the forgery channel is closed at construction by guards 1 and 2 of §1.4.
  *Reasoning:* the machine channel (the marker) must not be writable from the prose channel (the text),
  which is the one crossing this item creates. *Test:* AC-1(c), AC-1(c2).
- **A kind nobody captured.** *Case:* a new writer builds `TimelineEntry(kind="deal-closed", …)`.
  *Decision:* it constructs, renders and round-trips; the library makes no byte-parity CLAIM about it;
  the accessor returns no record for it and does not raise. *Reasoning:* D8 — this item relocates and
  does not tighten. *Test:* AC-1(a4), AC-2(a).
- **A locale whose `%B` is not English.** *Case:* the heading's month name changes. *Decision:* accepted
  and unguarded: both HAL9000's renderer and the library's call `strftime('%B')`, so a locale moves both
  identically and parity is preserved; the on-disk corpus is English. *Reasoning:* pinning a month table
  in the library would make it DIFFER from the code it is relocating — the one thing §1 must not do.
  *Test:* AC-1(a) proves the equality under the build environment's own locale.

OPEN: None.

## Implementation Plan

Tasks are ordered by dependency and each is one sitting. Tasks 2–4 are one coherent leg (the leaf module
and its oracle) and must not be reordered. Tasks 5, 6 and 8 are independent of each other once Task 2
lands and may be done in any order; Tasks 9–12 come last.

- [ ] **Task 1 — Record the baseline the later assertions are deltas against.** Before the first edit,
  run the floor command and record in the Build Log: the case count it reports, the value of
  `tests/fixture_vault.py:CORPUS_DIGEST`, and the `len(pinned)` figure
  `tests/test_lint_vault_fix_rules.py:822` asserts (7). **Verify:** the three numbers are in the Build
  Log before any file is edited; no later check asserts them as literals.
  verify: baseline — the pre-edit floor count, CORPUS_DIGEST and the len(pinned)==7 reading are recorded in the Build Log; no later check pins them (WI-238).

- [ ] **Task 2 — The leaf module, its refusal leaf and the package exports.** Create
  `obsidian_schemas/timeline_entry.py` exactly as §1 specifies: `_KIND_BODY` and the three patterns
  (§1.1), the four types (§1.2), the five functions (§1.3), the validation table and the four guards with
  their pattern literals (§1.4), `PARITY_KINDS`, `HAL9000_PARITY_ANCHOR` and the three kind constants
  (§1.5). Add `TimelineEntryRefusal` to `obsidian_schemas/errors.py` beside `NameGateRefusal`, declaring
  no `__init__` and carrying `pattern: Optional[str] = None`, plus ONE new member in `REASONS`:
  `"a timeline entry field this package refuses"`. Export all of §3's names from
  `obsidian_schemas/__init__.py` and add each to `__all__`. **Verify:** Task 3's check is the oracle;
  this task is done when the module imports under the project interpreter and the new leaf is
  constructible.
  verify: test_timeline_entry_reproduces_hal9000_render_and_validation_boundary

- [ ] **Task 3 — The parity and validation-boundary check, driven by the committed capture.** Create
  `tests/test_timeline_entry.py` (interpreter shim first, per §8.3) defining
  `test_timeline_entry_reproduces_hal9000_render_and_validation_boundary`, which parses
  `docs/wi-033-hal9000-timeline-entry-capture.md` — the `## Parity samples` and `## Validation boundary`
  sections, one `yaml` fence per record, exactly as `tests/test_lint_vault_fix_rules.py:113` parses
  `docs/lint-vault-live-baseline.md` by declared headings — and asserts, with every oracle read from the
  file and NO literal re-typed into the test:
  (a) for every sample, `render(TimelineEntry(kind=…, text=…, when=datetime.fromisoformat(…),
  discriminator=…))` is byte-identical to that sample's `rendered` block;
  (a2) `PARITY_KINDS == {s["kind"] for s in samples}` — the `## Parity samples` section's kinds, per R2;
  (a3) `HAL9000_PARITY_ANCHOR` equals the 40-hex HEAD the capture declares, read out of the capture's own
  prose and asserted to match `^[0-9a-f]{40}$`;
  (a4) a PLANTED slug-valid kind absent from `PARITY_KINDS` (`deal-closed`) constructs, renders and
  round-trips, and `PARITY_KINDS` is asserted not to be consulted — the planted kind's own round trip is
  the discriminant;
  (b) for every member of `PARITY_KINDS` iterated (never a hand list) plus the planted kind,
  `parse_markers(render(entry))` returns exactly one `Marker` whose `kind`, `day` and `discriminator`
  equal the entry's, and `dedupe_key(entry)` equals that marker's reconstructed key;
  (c) each of §1.4's guards raises `TimelineEntryRefusal` with the pattern this document names;
  (c2) R1's reified equality — the set of `accept` probes the library REFUSES equals the set of `accept`
  probes matching this document's four guard predicates, with that second set asserted non-empty, and
  every `accept` probe outside it asserted to CONSTRUCT.
  Non-vacuity first: assert the sample set and the probe set are non-empty and that the probes carry both
  verdict values, so a fence reader that finds nothing is RED rather than green. **Verify:** the check
  raises when any sample's bytes are altered by one space (observe by hand-mutating a copy of the parsed
  dict in a scratch run, then revert).
  verify: test_timeline_entry_reproduces_hal9000_render_and_validation_boundary

- [ ] **Task 4 — The typed overload on the door.** Change
  `obsidian_schemas/repositories/person.py:append_to_timeline` to §2's five-branch flow: the
  `Union[str, TimelineEntry]` parameter, the both-arguments refusal, the marker-anchored dedupe over
  `get_section(body, "Timeline")` using `parse_markers` and `dedupe_key`, the unchanged string branch
  including its whole-file substring test, and the unchanged write and return values. Add
  `parse_body_sections`-backed `get_section` to nothing — it is already imported at `person.py:61`.
  Extend Task 3's check with AC-1(d), (e) and (f): the same entry twice writes once and returns `False`;
  a note whose `## Notes` section quotes the key verbatim is NOT deduped against and the entry IS
  appended; the typed path prepends inside `## Timeline` and the existing string-and-key signature still
  works. State in the method's docstring that the anchoring is a READ and that the write mechanism and
  the no-`## Timeline` accommodation are unchanged (R4). **Verify:** as declared.
  verify: test_timeline_entry_reproduces_hal9000_render_and_validation_boundary

- [ ] **Task 5 — The accessor, and the person axis discriminated.** Add
  `PersonRepository.introduced_by` exactly as §3 specifies. Create
  `tests/test_introduced_by_accessor.py` (interpreter shim first) defining
  `test_introduced_by_reads_only_this_persons_intro_by_markers` over a PLANTED temp vault holding two
  person notes: A carrying one entry per `PARITY_KINDS` member (iterated, never hand-listed) plus
  AC-1(a4)'s out-of-table kind, each with a known counterparty and day; B carrying its own well-formed
  `intro-by` entry with a different counterparty, a different day and different `source` bytes. Assert
  AC-2's oracle as this document states it, then (a) the kind axis; (a2) the person axis in BOTH
  directions on BOTH people, plus the invariance run — the same `introduced_by(A)` over a vault from
  which B's note has been removed returns the IDENTICAL list; (b) plurality and newest-first order with
  B's note still present; (c) a markerless `intro-by` heading absent from the result; (d) the three
  never-the-other-channels cases with B's note present. Each entry is planted by rendering it through the
  library's own `render` into the note's `## Timeline`, so the fixture's bytes are the door's bytes.
  **Verify:** as declared.
  verify: test_introduced_by_reads_only_this_persons_intro_by_markers

- [ ] **Task 6 — The gate rule, and a derived arm sweep that names what it excludes.** Add §4's two
  literals and the section-`3c` arm to `obsidian_schemas/name_gate.py`, with a comment stating the three
  placement reasons §4 gives. Add to `tests/derivations.py` a new derivation
  `gate_call_sites(files) -> list[GateCallSite]`, where a site is
  `(module, qualname, ordinal, fields_is_empty_literal, declared_type_is_none_literal)` for every call
  resolving to `gate_write` (reusing `_resolves_to` / `_import_aliases`, so an aliased import is
  collected). Create `tests/test_retired_key_gate_rule.py` (interpreter shim first) defining
  `test_the_write_gate_refuses_the_retired_introduced_by_key`: (a) the refusal on both values of
  `whole_record`, with `pattern` and `refused_value` asserted, plus the explicit undeclared route
  (`declared_type=None`, no `name:`); (b) the derived sweep — the excluded set (both flags true) asserted
  to EQUAL exactly the one site in `writer.py:roundtrip_file`, the other five each DRIVEN through its own
  public door (`write_markdown_file` with `entity=` and with `frontmatter=`,
  `update_frontmatter_field`, `update_frontmatter_fields`, `BaseRepository.update_fields`,
  `PersonRepository.save`), each asserted to refuse AND to leave the file byte-identical; and the drive
  table asserted TOTAL — its covered set plus the excluded set equals the derived site set, so a seventh
  call site added later is RED until someone drives it; (d) another undeclared key (including `manager`)
  passes through unchanged, and a `company`-declared and a `book`-declared payload carrying the key are
  NOT refused. Ship the WI-235 battery for the new derivation: plant source files carrying each claimed
  shape — a direct call with `{}` and `declared_type=None`, one with `{}` and an attribute declaration,
  one with a non-empty literal and `None`, one through an aliased import — drive them through
  `gate_call_sites` itself, and include a near-miss (a call to a different function named in a docstring)
  the predicate must NOT collect. **Verify:** as declared.
  verify: test_the_write_gate_refuses_the_retired_introduced_by_key

- [ ] **Task 7 — Empty the fixture population.** Apply §6: the note edit, the manifest edit with its
  comment left byte-identical, and the `CORPUS_DIGEST` regeneration using the command
  `tests/fixture_vault.py:24-25` documents. Add to Task 6's check the derived scan AC-3(c) names: no file
  under `tests/fixtures/vault/` and no `NoteSpec.undeclared` key in `tests/fixture_vault.py:NOTES` names
  `introduced_by` afterwards; the swapped value's extracted tokens are all in `NAME_POOL`; and
  `docs/vault-fixtures.md` (the conductor-committed precondition) names `manager:` alone in the sentence
  at its undeclared-key example, asserted by the absence of the phrase `` `introduced_by:` `` outside
  that file's `criteria` fences. Read the committed live zero from
  `docs/wi-033-intro-corpus-baseline.md` as a premise; never re-measure a vault. **Verify:** as declared
  — the corpus walls and the gate check together.
  verify: test_no_corpus_note_carries_a_live_identifier test_fixture_vault_is_frozen_and_materialized_by_byte_copy test_the_write_gate_refuses_the_retired_introduced_by_key

- [ ] **Task 8 — The three detectors.** Add §5's three arms to `scripts/lint_vault.py:check_structural`
  at the stated position, with the library imports §5 names and no pattern of the script's own. Each is
  `auto_fixable=False` by default, carries the severity the table gives, and its message names the
  heading or the key and never a value. **Verify:** Task 9's check.
  verify: test_lint_vault_reports_the_intro_legacy_shapes_and_never_repairs_them

- [ ] **Task 9 — AC-4's check, inside the module that already owns the containment wall.** Add
  `test_lint_vault_reports_the_intro_legacy_shapes_and_never_repairs_them` to
  `tests/test_lint_vault_fix_rules.py`, taking its vault from `_temp_vault(root)` and its plants from
  `_plant`, so the five-clause wall at `:252` covers the new drives with no second door. Assert: (a)
  `legacy_intro_entry` fires once per `[intro]` heading across all three planted heading grammars
  (`Month D, YYYY`, ISO-with-time, bare ISO); (b) `intro_by_without_marker` fires once per markerless
  `intro-by` heading, and the grammar it uses is the library's — asserted by object identity, e.g.
  `lint_vault.parse_entries is timeline_entry.parse_entries`; (c) `retired_key_introduced_by` fires once
  per carrier, including an UNTYPED note; (d) silence over the planted negatives AC-4(d) enumerates, and
  over the frozen corpus as a SET EQUALITY of `(note, rule_id)` pairs computed twice in the same run —
  once with the three rule ids present and once with them filtered out; (e) a `--fix` drive over a vault
  carrying both a planted auto-fixable issue and the three new ones: the four-bucket total still equals
  the auto-fixable issue count and the new issues are counted by the summary's non-fixable figure;
  (f) an undecodable note (planted with `_plant_bytes`) is reported by none of the three.
  **Verify:** as declared, together with the write-causing-detector pin that proves the report-only
  posture.
  verify: test_lint_vault_reports_the_intro_legacy_shapes_and_never_repairs_them test_every_write_causing_detector_fires_exactly_on_its_declared_subjects

- [ ] **Task 10 — One definition of the grammar, asserted structurally.** Add to
  `tests/derivations.py` a derivation `marker_grammar_sites(files) -> list[GrammarSite]`: every string
  `Constant` in the parsed tree whose value contains `<!--` or `-->`, EXCLUDING docstrings (the first
  statement of a module, class or function), reported as `(module, lineno)`. Add AC-2(e)'s clause to
  Task 5's check: over `python_files_under(PACKAGE_ROOT, SCRIPTS_ROOT)` the sites' module set equals
  exactly `{"obsidian_schemas/timeline_entry.py"}`; `scripts/lint_vault.py` contributes zero sites and
  imports the module (object identity, as in Task 9); and `intro_not_symmetric`'s regex is asserted to
  contain no delimiter, so its exclusion is by construction rather than by exemption. Ship the WI-235
  battery for the new derivation: plant a module defining a marker regex (matched), one carrying the
  delimiter only in a docstring (not matched), one carrying it only in a comment (not matched), one that
  merely imports the grammar (not matched), and a near-miss string containing `<!` and `--` separately
  (not matched) — every shape driven through `marker_grammar_sites` itself. **Verify:** as declared.
  verify: test_introduced_by_reads_only_this_persons_intro_by_markers

- [ ] **Task 11 — Close the wall memberships by RUNNING each predicate, and prove the checks are
  discoverable.** Add `test_the_wi033_files_close_their_wall_memberships_by_running_each_predicate` to
  `tests/test_timeline_entry.py`, modelled on
  `tests/test_fixture_vault.py:test_the_fixture_vault_files_close_their_wall_memberships_by_running_each_predicate`:
  for the FINAL text of every file this item creates or edits, CALL each wall's own shipped predicate
  from §9's table (`modules_using_ast`, `skip_reason_literal_sites`, `frontmatter_write_arms`,
  `character_class_strip_sites`, `address_splitting_implementations`, `NO_ARG_CONSTRUCTION` over the
  edited corpus note, and the pytest collection globs) and assert the answer each wall requires, with a
  non-vacuity assertion first that the universe actually reaches the new files. In the same check, call
  `tests/test_ac_interpreter.py:check_module` on all four of this item's AC check names and assert each
  resolves to exactly one module — the conveyor's own discovery rule, which raises on a duplicate name.
  Anything the run returns that §9's table did not name is NAMED in the Build Log and satisfied there,
  never by narrowing a wall. **Verify:** as declared.
  verify: test_the_wi033_files_close_their_wall_memberships_by_running_each_predicate

- [ ] **Task 12 — Floor green, and the pins re-read rather than edited.** Run the floor command. Confirm
  it is GREEN with a case count no lower than Task 1's baseline, and confirm by reading that
  `tests/test_lint_vault_fix_rules.py:822` still reads `len(pinned) == 7`, that
  `CENSUS_SHAPE_TO_RULE`'s value set still equals the derived auto-fixable set, and that
  `docs/lint-vault-live-baseline.md` needed no edit. Record the final count and all three pin readings in
  the Build Log. **Verify:** a hand-run of the floor command; `pipeline-runners.yaml` declares no
  `commands:` block, so there is no registered `command_id` to name.
  verify: hand-run — the floor command is not a registered command_id (pipeline-runners.yaml declares no commands block), so the whole-suite run plus three pin re-reads is an act recorded in the Build Log.

## Write Targets

Four `kind: precondition` artifacts, declared HERE so the drive pauses for the conductor's commits
BEFORE the acceptance-criteria frame is presented (WI-300). The builder is caged and this reader has no
shell: none of the four is reachable from inside the tree, and each settles a premise an AC or a stated
scope boundary below rests on. The spec-writer EXTENDS this section at `exploring → specced` with the
builder's own write targets; these four are never replaced.

**Extended 2026-09-28 by the spec-writer**, per the sentence above: the four ideation-authored
`grounds:` fences stand unchanged, ONE further `kind: precondition` fence is added for
`docs/vault-fixtures.md` (`## Design` §6 states why the caged builder cannot be its author — since
WI-245 the merge boundary admits a declared edit to another item's tracked document only when it is
additive prose outside every fence, and AC-3(c)'s edit REPLACES prose), and the builder's own write
targets follow it. Every builder path below sits inside this project's declared `write_authority`
(`obsidian_schemas/**`, `tests/**`, `scripts/**`, `docs/**`); nothing in the plan writes the project
root, `bin/**` or `state/**`, and no task's verify command writes anything at all — Task 12's floor
command and every check are read-only over the tree (WI-238).

```writes
kind: precondition
path: docs/wi-033-hal9000-timeline-entry-capture.md
grounds: Whether the library's relocated renderer, kind-slug rule, marker grammar and dedupe contract reproduce HAL9000's shipped ones — byte-for-byte on what they RENDER and no stricter on what they REFUSE — including WI-077's two intro kinds and its `{kind}:{day}:{counterparty}` key format
why: "Relocate" means byte parity or it means nothing — 22 marker-bearing legacy entries and every WI-077 entry are already on disk, and a renderer that differs by one space stops round-tripping them while every hermetic test stays green. The caged builder cannot read HAL9000, and this reader's answer from there would have no HEAD to pin a re-run to, so the bytes must be IN the tree. Contents, part 1 — verbatim source of `backend_fastapi/core/timeline_entry.py` (the `TimelineEntry` class, its render, the kind-slug validation, the `-->`/`<!--` forgery guard, the dedupe-by-discriminator contract) and the two kind constants plus the key format from `routers/introduce.py` (`OBSERVED_KIND_ON_INTRODUCEE`, `OBSERVED_KIND_ON_INTRODUCER`, WI-077 note 6); each with a 40-hex HEAD, path and line range. Contents, part 2, and this is the half a source dump does not give — PARITY SAMPLES, which are INPUT→OUTPUT PAIRS and not outputs alone: an output whose inputs are absent is not reproducible, and a builder handed one is forced into exactly the re-typed literal AC-1(a) forbids. Shape, declared so the test can parse it deterministically rather than guessing (the precedent is `docs/lint-vault-live-baseline.md`, whose declared headings `tests/test_lint_vault_fix_rules.py:113` already parses): a single `## Parity samples` section holding one fenced block per sample, each a YAML code fence (info string `yaml`) with exactly the keys `kind`, `text`, `when` (a pinned absolute timestamp, because `when` is injectable and feeds BOTH the heading and the marker's day slot, so an unpinned sample reproduces nothing), `discriminator` (explicit `null` where the shipped call passes none), and `rendered` (a YAML block scalar holding the verbatim bytes that code emitted for those inputs). One sample per kind HAL9000 renders, INCLUDING the legacy `intro` kind, produced by RUNNING that code and not by reading it. Contents, part 3, and this is the surface render samples structurally cannot reach (D8) — THE VALIDATION BOUNDARY, as INPUT→VERDICT pairs: a `## Validation boundary` section holding one `yaml` fence per probe with exactly the keys `field` (`kind`, `text` or `discriminator`), `value` (the literal probe string; explicit `null` where the probe is an absent discriminator) and `verdict` (the literal `accept` or `refuse`), produced by RUNNING HAL9000's validation on that value and not by reading its regex. Every sample here is a VALID input, so a capture of samples alone cannot detect a library that REFUSES an input HAL9000 accepts — a divergence invisible to this tree's hermetic floor and visible only after the cutover, when the caller it breaks is HAL9000's own. Probe both verdicts and include, at minimum: a kind HAL9000's slug rule accepts that no sample renders; a kind it refuses (uppercase, a space, an empty string); a discriminator that is absent, empty, whitespace-only, and one containing the `:` key separator; and a kind, a text and a discriminator each containing `-->` and `<!--`. AC-1(c2) reads every pair and asserts the library is NO STRICTER in the ACCEPT direction, with the four deliberate over-refusals enumerated in AC-1(c) asserted as a set EQUALITY so the exception cannot be widened; the loose direction is out of scope by D8. Also declare, in prose beside the samples, the 40-hex HEAD once as the artifact's staleness anchor — AC-1(a) asserts the module's `HAL9000_PARITY_ANCHOR` equals it, and D7's cutover re-entry condition diffs against it. Precedents: `docs/wi-024-consumer-audit.md`, `docs/wi-029-consumer-audit.md`.
```

```writes
kind: precondition
path: docs/wi-033-intro-corpus-baseline.md
grounds: What the live vault holds today for every kind this item reads or reports — the `intro-by`, `intro-to` and legacy `[intro]` entry counts, how many of each carry a well-formed marker, and whether any note still carries the retired `introduced_by` key
why: Three criteria rest on live numbers that exist today only as PROSE in the ruling, taken on 2026-09-28 around a hand conversion: AC-3's claim that the population an unconditional ban could brick is empty; AC-2's marker-only reach (the ruling's 22-of-86 marker rate is what makes the narrowing arm honest rather than convenient); AC-4's expected live yield for the two legacy detectors. WI-144 is the specimen of what a confident unexecuted reading costs — the correction arrived after the signature. The floor is hermetic by WI-031 clause (v) and the builder cannot reach the vault, so the only way these become dated, re-runnable snapshots is a committed artifact carrying the literal commands and their verbatim output. Counts and shapes only; no vault note name and no live identifier, matching `docs/vault-shape-census.md`'s own rule. This also serves as the ENTRY half of the bracket should the `[intro]` rewrite (A5) ever be taken.
```

```writes
kind: precondition
path: docs/wi-033-consumer-audit.md
grounds: Which consumers write or read a vault timeline entry today, whether any would break when `append_to_timeline` grows a typed overload and the dedupe narrows to the marker form, and which of them is waiting on the accessor
why: This item changes a door four repos call and publishes an accessor a fifth is parked on. WI-032's scar is the exact reason this is a precondition and not a build-time discovery: a wider sweep found a FOURTH reader — mainspring's dispatch cockpit — AFTER that item was marked done, and the standing lesson is to sweep the WHOLE estate and restart long-running services. The known surface to cover: HAL9000's WI-058 door and WI-077 router (which become importers rather than owners), orchestrator's capture path, exocortex's parked WI-006 relationship edges, mainspring. Per repo: 40-hex HEAD, dirty count, the literal scan command, verbatim matching lines, and a per-site classification of whether the call passes a dedupe key that disagrees with the marker it writes (P2's population, measured rather than assumed). Code paths only — no vault note name, no live identifier. Precedents: `docs/wi-029-consumer-audit.md`, `docs/wi-032-consumer-audit.md`.
```

```writes
kind: precondition
path: docs/wi-033-hal9000-cutover-followup.md
grounds: Whether the second half of the relocation — HAL9000 deleting its own `timeline_entry.py` and importing the library's — is a MINTED work item with an id, an owner and a re-entry condition, or an unscheduled intention this document merely predicts
why: The Intent promises ONE definition of the vocabulary; this item, scoped to this tree, ships only the library half, so at its `done` the durable state is two implementations of one grammar with the library's copy pinned against a frozen capture of the other. A frozen capture cannot detect drift, which is LESSONS #4 and its named scar (exocortex's private copy of the name-prefix regexes never inherited the canonical validator's fixes). Library-first is the right sequencing; leaving the second half as a sentence in `### Dependencies` is what turns it into that scar. This artifact is what makes the mint an ACT the drive pauses for rather than a prediction: the conductor mints the cutover in HAL9000's own backlog (it cannot be minted here — different project) and commits this record into this tree's HEAD. Contents: the minted item's id and project; a one-line scope (delete `backend_fastapi/core/timeline_entry.py`, repoint the WI-058 door and the WI-077 router to `obsidian_schemas.timeline_entry`, keep HAL9000's HTTP surface and readback); the re-entry condition verbatim from D7's three clauses, including the diff of a re-run parity capture against `HAL9000_PARITY_ANCHOR`; and the 40-hex HEAD of HAL9000 the anchor pins, so a later reader can compute the drift window rather than guess it. No vault note name, no live identifier. It is a RECORD, not a plan: if the mint does not happen, this file cannot be written truthfully and the drive stops at the pause — which is the point.
```

```writes
kind: precondition
path: docs/vault-fixtures.md
why: Task 7 / AC-3(c) — the conductor commits this one-sentence edit, because the caged builder cannot be its author. The file is ANOTHER item's tracked work-item document (`id: WI-016`), and since WI-245 the merge boundary admits a declared cross-doc edit only when it is ADDITIVE PROSE outside every fence; AC-3(c)'s edit REPLACES prose at `:279` ("a `manager:` or `introduced_by:` key" must read `manager:` alone), so a caged write to it is refused at the merge boundary and costs a conductor hand-landing plus a relaunch. The edit is ONE sentence and nothing else: the same phrase inside WI-016's SIGNED AC-5 `criteria` fence at `:1434` is explicitly OUT of scope and must not be touched — moving a typed parse of another item's document is what the merge rule forbids, and that fence is another item's signed criterion. Checked against the PRE-DRIVE floor (WI-156, WI-164): no test in this tree reads `:279`'s prose and the file participates in no bijection or symmetry invariant the floor enforces, so this lands independently of the builder's fixture re-key and no atomic landing is required. Presence alone is not the evidence — the file is already in HEAD, so the WI-156 probe is trivially satisfied and AC-3(c)'s own check is what makes the edit verifiable.
```

```writes
path: obsidian_schemas/timeline_entry.py
why: Task 2 — the new leaf module: the vault's timeline-entry vocabulary (`## Design` §1).
```

```writes
path: obsidian_schemas/errors.py
why: Task 2 — the `TimelineEntryRefusal` leaf beside `NameGateRefusal`, plus ONE new `REASONS` member.
```

```writes
path: obsidian_schemas/__init__.py
why: Task 2 — the package exports and `__all__` entries for the new vocabulary and `IntroRecord`.
```

```writes
path: obsidian_schemas/repositories/person.py
why: Tasks 4 and 5 — `append_to_timeline`'s typed overload and the `introduced_by` accessor.
```

```writes
path: obsidian_schemas/name_gate.py
why: Task 6 — the two retired-key literals and the section-3c refusal arm inside the person body.
```

```writes
path: scripts/lint_vault.py
why: Task 8 — the three report-only detectors in `check_structural`, reading the library's grammar by import.
```

```writes
path: tests/derivations.py
why: Tasks 6 and 10 — `gate_call_sites` and `marker_grammar_sites`, the single home of `ast` in this tree.
```

```writes
path: tests/test_timeline_entry.py
why: Tasks 3, 4 and 11 — AC-1's capture-driven check and the wall-membership RUN.
```

```writes
path: tests/test_introduced_by_accessor.py
why: Tasks 5 and 10 — AC-2's two-person planted vault and the one-definition scan.
```

```writes
path: tests/test_retired_key_gate_rule.py
why: Tasks 6 and 7 — AC-3's gate refusal, the derived arm sweep and the emptied-population scan.
```

```writes
path: tests/test_lint_vault_fix_rules.py
why: Task 9 — AC-4's check, added to the module that already owns the containment door and the planting helpers.
```

```writes
path: tests/fixture_vault.py
why: Task 7 — the manifest's `undeclared` re-key and the regenerated `CORPUS_DIGEST`.
```

```writes
path: tests/fixtures/vault/@Morvette Harkwell.md
why: Task 7 — the one corpus carrier's key re-keyed to `manager:` (`## Design` §6).
```

## Verification

How the whole thing is known to work, end to end. The floor command is
`/Users/davewascha/Workspaces/obsidian-schemas/.venv/bin/python -m pytest <tree>/tests -q`; every check
below is one of the four AC checks or a named existing test.

**Happy path (smoke).** Build a `TimelineEntry(kind="intro-by", text="Introduced by [[@X|X]] via gmail",
when=datetime(2026, 9, 27, 18, 42, 7), discriminator="X")`, hand it to `append_to_timeline`, then call
`introduced_by` on the same `Person`: one `IntroRecord` comes back whose `introducer` is `"X"`, whose
`date` is `date(2026, 9, 27)` and whose `source` is the marker line on the page. Every oracle here is
derived from values the test itself holds — the entry it constructed and the bytes it wrote — never from
an assumed layout (WI-149). Covered by
`test_introduced_by_reads_only_this_persons_intro_by_markers`.

**The external oracle.** "The module renders correctly" is not the claim; byte parity with HAL9000 is, and
it is proved by reading BOTH sides out of `docs/wi-033-hal9000-timeline-entry-capture.md` — the inputs and
the expected bytes — so no literal a builder re-typed from the same reading of the same code can make it
pass (WI-144). `test_timeline_entry_reproduces_hal9000_render_and_validation_boundary`.

**Failure modes, each with its observable output.** A forged text or a guarded discriminator raises
`TimelineEntryRefusal` with the named `pattern` and writes nothing. A payload introducing
`introduced_by` raises `NameGateRefusal` with `pattern == RETIRED_KEY_PATTERN` and
`refused_value == "introduced_by"`, at five derived arms, with the target file byte-identical afterwards.
A typed entry plus a `deduplicate_key` raises rather than silently preferring one. A note with no
`## Timeline` yields `[]`; a note that does not exist raises the door's own `ValueError`; a note whose
frontmatter fence is broken raises `FrontmatterParseError`. An undecodable note is reported once as
`unreadable_note` and by none of the three new checks.

**The counting walls ship their claimed shapes as fixtures (WI-235).** Three checks in this item have a
COUNT as their oracle, and each ships its claimed match-shapes through the wall's OWN predicate plus a
near-miss the predicate must not match: AC-2(e)'s "exactly one definition of the grammar" drives five
planted source shapes through `marker_grammar_sites` (Task 10); AC-3(b)'s "the excluded set is exactly
one site" drives four planted call shapes, aliased import included, through `gate_call_sites` (Task 6);
AC-4(d)'s "silent over the frozen corpus" is a SET EQUALITY of `(note, rule_id)` pairs computed twice in
the same run rather than a zero, so a new issue that displaces an old one cannot cancel out (Task 9).
Mutate-and-observe is used as the complementary half only — Task 3's one-space mutation — and never as
the proof.

**The delta assertion captures its baseline first (WI-238).** Task 1 records the pre-edit floor count,
the pre-edit `CORPUS_DIGEST` and the pre-edit `len(pinned)` reading in the Build Log before any file is
edited. Task 12 asserts only PROPERTIES — GREEN, a count no lower than the baseline, and three pins
re-read as unchanged — never a hardcoded number.

**Integration: the downstream consumers precondition 3 measured, none of which this item moves.** All six
live `append_to_timeline` call sites pass a `str` and stay on the unchanged branch, so the typed overload
has zero callers on the day and the marker-anchored narrowing touches no live call. `introduced_by` has
ZERO callers on the day and two measured waiting consumers (HAL9000 WI-078, orchestrator WI-194), both at
`idea`. `introduced_by` as a frontmatter key has zero readers and zero writers estate-wide, so the gate
rule breaks no caller. The three writer classes the data-premise gate's counterexample hunt found —
`append_to_body_section`'s four hand-composing instruction-driven callers, the four raw-file writers
(including this tree's own `lint_vault` fixer), and exocortex's kindless high-volume meeting writer — are
each false-by-design members of `## Intent`'s universal and are dispositioned as named exclusions or as
AC-1(f)'s declared outcome class; AC-4(d)'s planted negatives and AC-2(d)'s silence clauses assert the
behaviour they require (the new checks do not flag them; the accessor returns nothing for them).

**Regression — DERIVED from the edited surfaces, not inherited (WI-238).** Sweeping the resolved test
root for modules that name each `## Write Targets` path returns, and every one of these must still pass:
for `obsidian_schemas/name_gate.py` — `tests/test_name_gate.py`, `tests/test_name_gate_wall.py`,
`tests/test_name_gate_refusals.py`, `tests/test_company_name_contract.py`,
`tests/test_whatsapp_write_door.py`, `tests/test_lint_vault_fix_gate.py`; for
`obsidian_schemas/repositories/person.py` — `tests/test_repositories.py`,
`tests/test_provenance_write_seam.py`, `tests/test_write_target_seam_wall.py`,
`tests/test_identity_endgame.py`, `tests/test_concurrent_access.py`,
`tests/test_whatsapp_jid_storage.py`, `tests/test_whatsapp_migration.py`; for
`obsidian_schemas/errors.py` and `obsidian_schemas/__init__.py` — `tests/test_loud_fail_parse.py`,
`tests/test_loud_fail_load.py`, `tests/test_loud_fail_write.py`, `tests/test_loud_fail_harness.py`; for
`scripts/lint_vault.py` — `tests/test_lint_vault_fix_rules.py`, `tests/test_lint_vault_fix_gate.py`,
`tests/test_stem_name_divergence_detector.py`, `tests/test_write_routing.py`; for
`tests/derivations.py` — every module in §9's table, since each imports from it; for
`tests/fixture_vault.py` and the corpus note — `tests/test_fixture_vault.py`,
`tests/test_parser.py`, `tests/test_writer.py`, `tests/test_repositories.py`,
`tests/test_vault_path_required.py`, and every module that materializes the corpus
(`tests/test_lint_vault_fix_rules.py`, `tests/test_stem_name_divergence_detector.py`,
`tests/test_whatsapp_migration.py`, `tests/test_whatsapp_write_door.py`,
`tests/test_whatsapp_jid_storage.py`, `tests/test_provenance_write_seam.py`). The list is a SWEEP's
output at 2026-09-28 and the obligation is the whole floor being GREEN, not this enumeration being
complete.

**No incident replay is owed (WI-173).** This is not an incident-class item: nothing broke in production
and this spec asserts no live failure. The four diagnostic claims in `## Verified Diagnosis` are about
code shapes, each falsifiable by a read, and the one live fact that could have been an incident — the
single stored `introduced_by` value — was already converted and read back by the conductor on 2026-09-28
(ruling §1) before this item. No incident is manufactured to satisfy the check, and no plan task drains
live state.

**A corpus fixture derives or freezes (WI-278 analogue).** AC-1's check reaches into `docs/**` at run
time, which in this tree is the artifact class WI-031 clause (v) keeps out of the floor's path. It takes
the FROZEN-BYTES arm: `docs/wi-033-hal9000-timeline-entry-capture.md` is a conductor-committed,
machine-shaped artifact whose fences are the oracle, selected by its DECLARED headings
(`## Parity samples`, `## Validation boundary`) exactly as `tests/test_lint_vault_fix_rules.py:113`
selects `docs/lint-vault-live-baseline.md`'s — never by a glob, a size, a position or a live population's
shape. The coupling is DECLARED here in one line so the next reader can falsify it: **AC-1's check pins
those two heading names and the five/three declared keys per fence, and consumes the property that every
`rendered` block and every `verdict` was produced by RUNNING HAL9000's code at
`HAL9000_PARITY_ANCHOR`.**

## Scope Boundary

**What we are NOT doing.** Nothing in `## Exploration Notes`' *What this item does NOT do* is reopened,
and it is the operative list: no HAL9000 cutover (minted as HAL9000 WI-082, recorded by precondition 4);
no narrowing of the kinds any writer may use (`PARITY_KINDS` gates nothing); no validating on HAL9000's
behalf where the library ends up LOOSER; no rewrite of the 86 legacy `[intro]` entries; no change to
`intro_not_symmetric`; no `introduced_by` field on any model; no change to `append_to_timeline`'s existing
string signature, its whole-file substring dedupe on that branch, or its prepend placement; and no
live-vault write. Four further absences this spec adds, named so a builder does not drift in:

- **No standing cross-repo drift checker.** D7's addendum declines it in writing and records the runnable
  form for the cutover item. A `scripts/`-resident checker reading a sibling repo's absolute path would
  re-open the out-of-tree dependency WI-031 clause (v) closed.
- **No new lint CATEGORY, and no change to `check_fns`, `CATEGORY_ORDER` or `CATEGORY_LABELS`.** The
  three detectors join `check_structural` (§5). The `--category` CLI vocabulary is unchanged.
- **No auto-fix, and therefore no edit to `apply_fixes`, `FixOutcome`, `DECLINE_GUARDS`,
  `docs/lint-vault-live-baseline.md` or the `len(pinned) == 7` pin.** Those are re-read, never edited
  (Task 12).
- **No second timeline door.** `append_to_body_section` is untouched, and the `section`-as-a-variable
  route through it (`routers/entities.py` in HAL9000, per precondition 3) stays exactly as loose as it is
  today; this item makes its output VISIBLE through the linter rather than refusing it.
- **No clock in the library** (§1) and no `_now()` relocation.

**Unchanged files the builder must not touch.** `obsidian_schemas/body_sections.py` (A2 — it is
entity-agnostic by contract and entry kinds are vocabulary); `obsidian_schemas/models.py` (A4 — no field
is added, and `_source_path` is read through `_resolve_write_target`, never extended);
`obsidian_schemas/writer.py`, `obsidian_schemas/vault_io.py`,
`obsidian_schemas/repositories/base.py`, `obsidian_schemas/identifier.py`,
`obsidian_schemas/name_validation.py`, `obsidian_schemas/name_cleaning.py`,
`obsidian_schemas/phone_normalization.py`; `docs/vault-shape-census.md` (digest-frozen — and §6's D9 is
what keeps this item from needing a row in it); `docs/lint-vault-live-baseline.md`;
`docs/vault-fixtures-rounds.md` (declared byte-for-byte append-only by
`docs/vault-fixtures.md:3761`); WI-016's signed `criteria` fences inside `docs/vault-fixtures.md`;
`pipeline-runners.yaml`, `CLAUDE.md`, `README.md`, `SESSION_LOG.md` and `state/**` (outside the cage by
design); and every other corpus note under `tests/fixtures/vault/` except
`@Morvette Harkwell.md` — `_plant` refuses a corpus stem for a reason, and a second edited note costs a
second digest argument for nothing.

## Risk Analysis

This item changes a door four repos call, adds a refusal to THE write gate, and adds two readers of live
vault bytes. Three risks are material; each is stated with its likelihood, its impact and what actually
holds it.

| Risk | Likelihood | Impact | What holds it |
| --- | --- | --- | --- |
| **The gate's unconditional refusal bricks a live note.** A note that regains `introduced_by` by hand-edit becomes unwritable through `save` until the key is deleted — D3's deliberately INVERTED trade against the name gate's stored-dirty ruling. | Low: the live carrier population is 0 over 5,664 files and the key has zero writers estate-wide (preconditions 2 and 3). | One note's writes refuse loudly until a one-line hand fix. | The population is EMPTIED rather than exempted (D3), so there is no exemption arm to widen; the remedy is one line; `retired_key_introduced_by` names the note as an ERROR in the tool Dave runs; the refusal is loud and nothing is written (AC-3(b)). |
| **The library refuses an input HAL9000 accepts, and the first victim is HAL9000's own caller — after the cutover, when this tree's floor no longer watches it.** The four guards of §1.4 are deliberate over-refusals. | Low for `text` (a note name or a rendered sentence containing `-->` or `<!--`), very low for the discriminator cases (a counterparty name that is empty, whitespace or contains `:`). | A HAL9000 write that succeeds today would raise post-cutover. | The guard set is pinned as a SET EQUALITY against the capture's `accept` probes (AC-1(c2), R1), so the exception cannot be widened one case at a time; each guard has a stated reason (§1.4); the refusal is LOUD, never a silent drop; and the cutover item's first act re-runs the capture and diffs it, which is where a newly-diverging input surfaces. |
| **The parity pin goes stale silently.** `HAL9000_PARITY_ANCHOR` freezes HAL9000 at one HEAD; drift in its copy during the window is invisible to this tree's hermetic floor. | Certain to be possible; the window is bounded by one scheduled item. | The accessor could return `[]` against real HAL9000 bytes with a green floor. | Accepted in writing, not mitigated (D7). What exists: the anchor is machine-checked against the capture (AC-1(a3)), so a re-run is one diff; the cutover is a MINTED item with an id (HAL9000 WI-082, precondition 4) whose re-entry condition is that diff; and `intro_by_without_marker` makes an unreadable on-disk entry visible in the linter even if the grammars diverge. |

**Rollback.** Every change is additive except one line of the fixture corpus. Reverting the commit
removes a new module, a new error leaf, one gate arm, one accessor, three report-only checks and a
parameter widening; no data was migrated, no state file was written, no live note was touched. The only
non-additive step, the corpus re-key, reverses by restoring the note line, the manifest line and the
previous `CORPUS_DIGEST`.

**Migration path.** None is needed (see `## Edge Cases` > Migration / backfill). If the legacy `[intro]`
rewrite is ever wanted, `docs/wi-033-intro-corpus-baseline.md` is already the ENTRY half of that
bracket and A5 states the shape: dry run → gated write → readback, WI-032's own.

## Acceptance Criteria

**DRAFT — not frozen.** These four are the convergence artifact: what would prove this worked. They are
frozen only when Dave reviews and signs them through `/review-spec`
(`bin/review-spec-helper.py review --wi-id WI-033 --project <path>`), which writes the `ac-signoff`
fence. The spec-writer refines them in place until then.

```criteria
id: AC-1
desc: The vault's timeline-entry vocabulary has ONE definition, it lives in this library, and it reproduces HAL9000's bytes without becoming stricter than them. A leaf module `obsidian_schemas/timeline_entry.py` defines `TimelineEntry` (kind, text, injectable `when`, optional discriminator), a `render()`, a derived `dedupe_key`, `parse_markers()`, an OPEN kind-SLUG RULE as the write door, and a declared `PARITY_KINDS` constant that is the parity/sweep universe and GATES NO WRITE (D8). (a) PARITY, AND THE CAPTURE'S SAMPLE SET GOVERNS THE SWEEP — not the library's constant: the test parses the `## Parity samples` section of `docs/wi-033-hal9000-timeline-entry-capture.md` and, for EVERY sample it declares (one per kind HAL9000 renders, legacy `intro` included), constructs a `TimelineEntry` from THAT SAMPLE'S OWN INPUTS — `kind`, `text`, `when`, `discriminator` — and asserts `render()` is BYTE-IDENTICAL to the sample's `rendered` block. Inputs and expected output are BOTH read from the file; no literal is re-typed into the test, and a sample whose `when` is unpinned is not constructible, which is why precondition 1 requires input→output PAIRS in a declared machine-readable shape rather than outputs alone. (a2) `PARITY_KINDS` EQUALS THE CAPTURED POPULATION, ASSERTED — `PARITY_KINDS` equals the set of kinds the capture holds, as a SET EQUALITY: a member with no sample is RED (it would be swept by (b) with no captured bytes to sweep against, so the library would claim parity it cannot show), and a kind HAL9000 renders that `PARITY_KINDS` omits is RED (it would be an on-disk kind absent from every derived sweep's fixture space). This is a claim about the SWEEP SPACE, not a gate: see (a4). (a3) THE STALENESS ANCHOR IS MACHINE-CHECKED — the module declares `HAL9000_PARITY_ANCHOR` as a 40-hex HEAD and the test asserts it equals the HEAD the capture itself declares, so D7's cutover re-entry condition has a pin to diff against rather than a paragraph. (a4) THE DOOR IS OPEN, AND THAT READING IS PLANTED RATHER THAN STATED — a kind that satisfies the slug rule and is ABSENT from `PARITY_KINDS` (a novel kind planted by this test, e.g. `deal-closed`) CONSTRUCTS, renders, and round-trips through (b)'s assertions; no `TimelineEntry` construction, `render()`, `dedupe_key` or `parse_markers` call consults `PARITY_KINDS`, and a build that refuses the planted kind is RED. This is the discriminating member the corpus cannot supply (P4, WI-286): it is the one assertion that tells a closed enum from an open rule, and without it both builds are green. (b) ROUND TRIP, DERIVED — the fixture space is `PARITY_KINDS`, iterated (never a hand list in the test), plus (a4)'s planted out-of-table kind; for each member, `parse_markers(render(entry))` returns exactly one marker whose kind, day and discriminator equal the entry's, and `dedupe_key` equals that marker's key. (c) FORGERY — a text or discriminator containing `-->` or `<!--` is REFUSED with a `LoudFailError` leaf named in this document, so no caller can forge a marker through the text channel; a discriminator that is empty, whitespace-only, or contains the key separator is refused the same way. (c2) REFUSAL PARITY, IN THE DIRECTION THAT CAN BREAK A CALLER — the test reads every INPUT→VERDICT pair from the `## Validation boundary` section of the same capture and asserts the library is NO STRICTER: every `value` the capture records HAL9000 ACCEPTING, the library accepts. The sole exception is the guard set (c) names — a `<!--`/`-->` bearing text, kind or discriminator, and an empty, whitespace-only or `:`-bearing discriminator — and it is asserted as a SET EQUALITY: the set of capture-ACCEPTED inputs the library refuses equals exactly that enumerated guard set, so any other over-refusal is RED and cannot be waved through as deliberate. The LOOSE direction is asserted NOT AT ALL and is out of scope in writing (D8): an input HAL9000 refuses and the library accepts cannot break a caller that works today, and the library's own guards are pinned independently by (c). (d) THE DOOR CANNOT DISAGREE WITH ITSELF — `PersonRepository.append_to_timeline` accepts a `TimelineEntry` and derives BOTH the written entry and the dedupe key from it, so the key and the marker are the same string by construction; passing the same entry twice writes once, and the second call returns the deliberate dedup `False`. (e) DEDUPE IS ANCHORED — the typed path matches the MARKER FORM inside the `## Timeline` span only: a note whose `## Notes` section quotes the key verbatim is NOT deduped against, and an entry is still appended. (f) PLACEMENT UNCHANGED — the typed path prepends inside `## Timeline` exactly as the string path does today (`person.py:1543-1545`), and the existing string-and-key signature keeps working unchanged for existing callers.
why: (a) is the criterion's whole reason for resting on a precondition: "relocate" means byte parity, and 22 marker-bearing legacy entries plus every WI-077 entry on disk stop round-tripping if the renderer differs by a space — while a hermetic suite comparing the module against a literal a builder typed from the same reading of the same code would stay green either way (WI-144). Reading the committed sample is what makes the oracle external to the implementation, and it is only executable if the sample carries the INPUTS that produced it: `when` is injectable and feeds both the heading and the marker's day slot, so an output with no pinned `when` cannot be reproduced at all and the builder would be driven back to the re-typed literal this clause forbids — a failure that would otherwise land AFTER the conductor's commit pause, which is the expensive place for it. (a2) exists because the sweep and the samples are two different tables owned by two different repos: the earlier draft swept "the declared table" (the library's) against a capture holding HAL9000's, which is unsatisfiable by construction the moment the two differ; the set equality makes the difference itself the finding. What (a2) buys is stated precisely, because the round-2 review caught the earlier `why` overclaiming it as enforcement: it does NOT gate a write and it does not stop anyone using a new kind (D8, (a4)). It pins the FIXTURE SPACE — (b) and AC-2 both iterate `PARITY_KINDS`, so if that constant drifts from the capture, (b) round-trips a member against the library's own renderer with no captured bytes behind it (self-consistent, proving nothing) or a kind that exists on disk is swept by nothing at all. The equality is what keeps two derived sweeps' fixture space equal to the population that actually exists, and it makes the library's byte-parity CLAIM — which kinds it has captured bytes for — falsifiable instead of a builder's list. (a3) is the whole guard over D7's window written as one assertion: this item ships the library half only, HAL9000 keeps its own copy until the minted cutover lands, and a pinned anchor is what converts "someone should re-run the capture" into a diff with a defined left-hand side. (a4) is the round-2 finding closed as an ASSERTION rather than as prose, because the two readings of `PARITY_KINDS` are two different write doors and a document that merely says which one it means is still buildable both ways: a closed enum would make the library STRICTER than the code it relocates (post-cutover, a HAL9000 call that writes today raises) and would break example-of-done 3's promise to "any new writer that installs this library", so the open door is the ruled answer and the planted out-of-table kind is what makes a closed-enum build RED. It is planted rather than sampled for the P4 reason: the corpus has zero entries, so nothing on disk can discriminate. (b) derives the fixture space from the class's own declaration (WI-185) rather than sampling kinds, so a kind added later joins the sweep automatically — but membership is not correctness (WI-286), which is why the per-member oracle is the entry's own field values rather than "a marker came back". (c) is the guard the mint names explicitly and the one place a text channel can corrupt a machine channel. (c2) is the other half of what "relocate" means, and it was missing while the item's own standard was already broader than render: `### Constraints discovered` says parity with HAL9000 is the meaning of the word, but every parity SAMPLE is a valid input, so a capture of samples structurally cannot detect a library that refuses something HAL9000 accepts — a divergence the hermetic floor never sees and whose first victim, after the cutover, is HAL9000's own caller. Asserting only the ACCEPT direction is deliberate: over-refusal breaks working callers and is the failure this item can cause, while under-refusal cannot, and validating on HAL9000's behalf is the cutover item's business (D8), exactly as drift is D7's. The guard set is an EQUALITY rather than an allowance because "the library may be stricter where it means to be" with no enumerated set is an exemption a later build widens one case at a time. (d) and (e) are the P2 defect closed at the door rather than documented: today `deduplicate_key` and the entry string are unrelated arguments and the check is a substring test over the WHOLE file including frontmatter, so a caller can dedupe on a key it never writes, and a `## Notes` line quoting a key silently suppresses a real entry. (f) is stated because prepend-despite-the-name is stored behaviour every reader of the vault depends on, and because breaking the existing signature would break four repos precondition 3 enumerates.
check: test_timeline_entry_reproduces_hal9000_render_and_validation_boundary
kind: test
```

```criteria
id: AC-2
desc: "Who introduced this person" is one typed call that reads the marker slot and nothing else. `PersonRepository.introduced_by(person) -> list[IntroRecord]` — three fields, each with a pinned value below: `introducer`, `date`, and `source`, the VERBATIM MARKER STRING the record was read from (the provenance field; a record whose `source` is `None` or reconstructed rather than the bytes on the page fails this criterion). Over a PLANTED temp vault — the frozen corpus contains zero timeline entries, so nothing here is sampled — the vault holds TWO person notes, and both axes the accessor selects on carry a discriminating member. Person A is the kind sweep's note: the sweep iterates `PARITY_KINDS` — which by AC-1(a2) equals the capture's kinds and therefore already contains the legacy kind `intro`, and which is a FIXTURE SPACE here and not a gate (D8) — plus AC-1(a4)'s planted out-of-table kind, and plants one entry per member on A with a known counterparty and day. Person B is the PERSON-axis discriminant: a second person note carrying its OWN well-formed `intro-by` entry with a DIFFERENT counterparty and a DIFFERENT day, so A's record and B's record differ in every field including `source`. The oracle is stated HERE: `introduced_by(A)` contains exactly one record for the `intro-by` member, carrying that member's counterparty verbatim from the discriminator slot, its day parsed from the day slot, and its `source` equal BYTE-FOR-BYTE to the marker substring present in A'S OWN note text — and NO record for any other member, and NO record carrying B's counterparty or B's day. (a) THE DISCRIMINATING MEMBERS ARE PLANTED — `intro-to` and legacy `intro` are both in the sweep precisely because an implementation keyed on `"intro" in kind` is wrong-but-self-consistent and would return three records where the definition says one; AC-1(a4)'s out-of-table kind is in the sweep for the complementary reason — the accessor's filter is the EXACT slug `intro-by` and is not `PARITY_KINDS` membership, so a kind the library never captured yields no record and does not raise. (a2) THE PERSON AXIS IS DISCRIMINATED, NOT ASSUMED — the accessor's first argument selects a NOTE, and on a fixture holding `intro-by` data for exactly one person a build that globs every note under the vault for markers, or that reads a fixed or first note, is indistinguishable from a correct one; B is planted for exactly the reason `intro-to` is planted on the kind axis. Asserted in BOTH directions and on BOTH people: `introduced_by(A)` equals exactly A's one record — never B's alone, and never the union of the two — and `introduced_by(B)` equals exactly B's one record, carrying B's counterparty, B's day and B's `source` bytes and never A's. And the read is scoped to that person's OWN note rather than merely filtered: the same `introduced_by(A)` call over a temp vault from which B's note has been removed returns the IDENTICAL list, so a build reading the vault at large cannot be green in both runs. The accessor loads A's body through `parse_body_sections` from the note A was parsed from and reads only its `## Timeline` (`## Approach`); no clause here is satisfiable by a vault-wide scan. (b) PLURALITY AND ORDER — two `intro-by` entries on ONE person's own note return exactly two records, both that person's, in stored document order (newest-first, per `person.py:1543-1545`); with B's note still in the vault, so plurality is that person's own two and never a third borrowed from elsewhere. (c) NARROWED ARM, stated rather than invented — an `intro-by` HEADING carrying no marker has no counterparty slot and therefore no right answer; it is asserted ABSENT from the result AND asserted PRESENT in AC-4's `intro_by_without_marker` report, which is the declared marker that keeps the promise honest. (d) NEVER THE OTHER CHANNELS — the accessor returns nothing for a note whose Timeline prose says "Introduced by [[@X]]" with no marker; nothing for a note carrying an `introduced_by` frontmatter key; and `[]` for a person with no `## Timeline` section at all, rather than raising. All three of these are asserted with B's well-formed `intro-by` note PRESENT in the same vault, so "nothing" means nothing — not somebody else's record. (e) NO SECOND COPY OF THE GRAMMAR, AND THE SCAN COVERS THE PLACE THE SECOND COPY WOULD ACTUALLY APPEAR — a derived scan over every `.py` file under `obsidian_schemas/**` AND `scripts/**` (the two trees this item writes; `tests/derivations.py:185`'s `python_files_under` is the existing derivation) finds the marker grammar DEFINED in exactly one file, `obsidian_schemas/timeline_entry.py`. The predicate is a definition, not a mention: a pattern or format literal containing the marker delimiters `<!--` / `-->`. Every other file that needs the grammar IMPORTS it — named specifically because this item puts marker-reading code there, `scripts/lint_vault.py`'s new `intro_by_without_marker` detector (AC-4(b)) imports the module's regex/parser and defines no pattern of its own, which the same scan asserts by finding zero definitions in that file and an import of `obsidian_schemas.timeline_entry` in it. `intro_not_symmetric`'s prose regex (`scripts/lint_vault.py:816`) contains no marker delimiter, is untouched by this item (P7), and is therefore outside the predicate by construction rather than by exemption. And `introduced_by` is exported from the package so a consumer has a typed route.
why: This is the half of the Intent consumers actually call, and P4 is why every word of it is planted: the frozen corpus has ZERO timeline entries (grep `^### |<!-- ` over `tests/fixtures/vault/` returns nothing), so the corpus cannot tell a correct accessor from a stub that returns `[]` — membership proves nothing here because there are no members. (a) is the WI-286 discriminant chosen deliberately: `"intro" in kind` is the cheapest wrong implementation, and `intro-to` and `intro` are exactly the members that catch it, so both are planted rather than hoped for. The out-of-table member is there because D8 makes `PARITY_KINDS` a fixture space rather than a gate, and a build that quietly used it as the accessor's filter — or raised on an unlisted kind while reading a note — would otherwise be green here. The per-member oracle is a value this document defines (one record for one member, none for the rest), not a value re-derived from the implementation, so a wrong-but-self-consistent build MISMATCHES instead of agreeing with itself. (a2) is that same WI-286 discriminant applied to the axis the accessor's own first argument selects on — the one axis the earlier draft left with a single member while discriminating the kind axis three ways. With `intro-by` data on exactly ONE note, an implementation that globs every note under the vault for markers (or reads a fixed or first note) returns precisely the record the oracle expects and goes green on every other clause of this criterion and on example-of-done 1; shipped against the live vault's thousand-plus person notes it could answer `introduced_by(@Alice)` with @Bob's introducer, or with the union of everyone's records, and `## Intent`'s "who introduced THIS person" would be answered for the wrong person with a green floor. P4 is again why the second member is PLANTED rather than found: the frozen corpus has zero entries, so it can supply a second person no more than it can supply a second kind. Asserting BOTH directions is what rules out the union build and the read-one-fixed-note build in the same pair of assertions — a one-directional check would still pass whichever of the two happens to order A first — and the B-removed re-run is what makes the promise "reads that person's own note" rather than "filters a vault-wide read by something". (c) is the WI-286 narrowing arm taken honestly rather than papered over: the ruling's audit measured 22 of 86 legacy entries carrying a marker, so markerless entries are a real population with genuinely no recoverable counterparty — the criterion promises a REPORT for them, not a guess, and asserting both halves is what stops a build from quietly dropping them. (d)'s first clause is the seam rule (`## Exploration Notes`, "Where the structure actually lives") made falsifiable: the prose is a lossy copy and reading it would rebuild `lint_vault`'s `intro_not_symmetric` regex (`scripts/lint_vault.py:816`) inside the library — the second parser copy the mint predicts. (d)'s second clause pins the ruling's §1 and §2 as one behaviour rather than two. The `source` field is pinned rather than dropped because it is the record's provenance: a consumer that disagrees with the accessor (or a linter issue that needs to name the offending bytes) has the exact substring to quote, and without a pinned value the tuple's third slot is a field a build could ship as `None` with every other clause green. (e) is the boundary promise itself, asserted structurally so a later consumer copying the regex out is RED rather than merely impolite — and it reaches `scripts/**` because that is where the second copy has ALREADY appeared once in this tree (P7's prose parser) and where this item's own marker-reading detector lands: a scan bounded to `obsidian_schemas/**` would let a builder write a second marker regex in `scripts/lint_vault.py` and satisfy the criterion and violate the Intent in the same commit. The clause permits an IMPORT and forbids a RE-DEFINITION, which is the LESSONS #4 rule ("route to the first, do not copy it") stated as a predicate a test can run.
check: test_introduced_by_reads_only_this_persons_intro_by_markers
kind: test
```

```criteria
id: AC-3
desc: The retired `introduced_by` key cannot creep back, and the refusal is total rather than arm-conditional. (a) REFUSED, AND THE PLACEMENT IS NAMED — `gate_write` raises `NameGateRefusal` whenever `introduced_by` is among the fields a write INTRODUCES on a payload that reaches the gate's PERSON BODY, on BOTH values of `whole_record`, with `pattern` set to a literal this document names and `refused_value` set to the literal key `"introduced_by"` and never to the key's value. The rule lands IN THE PERSON BODY, below the declared-non-person early return at `name_gate.py:373-398`, NOT keyed on `declared_type == PERSON_TYPE` — so a `person`-declared write AND an UNDECLARED write (a person note missing its `type:`, which P10 measures as falling through to that body) are both refused, while `company` and `book` are exempted for free by that same return. The undeclared route is asserted explicitly: a write introducing `introduced_by` with `declared_type=None` and no `name:` is refused. (b) TOTAL OVER THE ARMS — the sweep derives the package's gated write arms rather than hand-listing them (the six `gate_write` call sites: `writer.py:252`, `:385`, `:443`, `:494`; `base.py:728`; `person.py:1270`) and drives each one that can carry a person frontmatter delta. THE FILTER IS STATED AND ITSELF ASSERTED, so the sweep's shortfall is visible rather than inferred: a site whose fields argument is a literal empty mapping AND whose `declared_type` is the literal `None` structurally cannot carry a person delta, and the excluded set is asserted to EQUAL exactly `writer.py:494` — WI-021's D7 re-serialization arm, which introduces no field and passes `None` deliberately (`writer.py:477-494`) — leaving the other five all driven. The sweep asserts the refusal at every driven arm and asserts NO FILE CHANGED — including the `save()` path, where the key arrives inside `model_to_frontmatter`'s projection because `Person` is `extra="allow"` (`models.py:34-35`, `:49-52`). (c) THE POPULATION IS EMPTY, NOT EXEMPTED — `tests/fixtures/vault/@Morvette Harkwell.md`'s undeclared key is re-keyed from `introduced_by` to `manager` and `CORPUS_DIGEST` is regenerated; the manifest's `undeclared` declaration moves with it and the note keeps its AC-5(b) clause-3 job; a derived scan asserts no note under `tests/fixtures/vault/` and no manifest entry names `introduced_by` afterwards, and the corpus's OWN documentation stops offering the key as a legitimate specimen — `docs/vault-fixtures.md:279` currently names "a `manager:` or `introduced_by:` key" as the undeclared-key example and is updated to name `manager:` alone, so a later reader does not re-plant a key the gate now refuses. The live half is the committed count in `docs/wi-033-intro-corpus-baseline.md`, read by the test as a premise rather than re-measured. (d) NOTHING ELSE MOVES — a person write carrying any other undeclared key (including the newly-swapped `manager`) is gated and returned unchanged, so this is a one-key rule and not a whitelist of declared fields; a `company`-declared and a `book`-declared payload carrying `introduced_by` are NOT refused, because the ruling retires it as a PERSON frontmatter key.
why: Ruling §1 says the gate refuses the key so it cannot creep back, and P6 is why that sentence needs a design rather than a line of code: the gate is DECLARE-only and reads nothing but its arguments (`name_gate.py:22-29`), so it structurally cannot tell "this write introduces the key" from "this projection re-emits a key the note already had" — and `model_to_frontmatter` re-emits `model_extra` unconditionally, which means a blanket ban makes every carrier permanently unwritable through `save`. That is the remedy-is-the-disease outcome the DELTA doctrine was written against (`name_gate.py:31-36`). (c) resolves it by measurement rather than by exemption: live is already zero after the 2026-09-28 conversion, and the one fixture carrier is re-keyed to a key `docs/vault-fixtures.md:279` already names as the same specimen class — so the rule stays unconditional, one place, one literal (P8), and no exemption arm exists for a later build to widen. The inverted trade is deliberate and argued in `## Exploration Notes` D3: a note that regains the key is unwritable until the key is deleted, which is correct pressure for a RETIRED KEY (one-line remedy, named by AC-4's detector) where it would be punitive for a dirty NAME (no remedy but a rename). (b) is derived rather than hand-listed for the WI-185 reason, and it asserts NO FILE CHANGED because a refusal that fires after a partial write is worse than no refusal. Its filter is asserted as an equality rather than left implicit because a derived sweep that quietly drops arms is indistinguishable from an incomplete one: `writer.py:494` passes a literal `{}` with `declared_type=None` and can never carry the key, so excluding it is correct — but a reader (and a later build that adds a sixth arm) needs the exclusion NAMED, not discovered. (a)'s placement is stated rather than left to the build because both placements satisfy every other clause of this criterion while differing on one real route: P10 measures that `gate_write`'s declared-non-person early return (`name_gate.py:373`) is guarded by `is not None` precisely so an UNDECLARED write with no `name:` falls through to the person body, so a rule keyed on `declared_type == PERSON_TYPE` would leave a person note missing its `type:` free to carry the key — "cannot creep back" with a hole in it. Writing the rule into the body closes that route and keeps AC-3(d)'s company/book exemption for free, because those return before reaching it. (d)'s last clause is the criterion refusing to over-reach: the ruling retires a person key, and silently extending the ban to every entity type would be an unsigned subtraction. `refused_value` carries the KEY because at this arm the value is a person's name, and keeping note-derived identity out of refusals is exactly what `_refuse`'s rule 2 exists for (`name_gate.py:174-186`).
check: test_the_write_gate_refuses_the_retired_introduced_by_key
kind: test
```

```criteria
id: AC-4
desc: `lint_vault` makes the legacy and retired shapes VISIBLE and repairs none of them. Three new checks, all report-only: (a) `legacy_intro_entry` — WARNING, one issue per `[intro]` timeline heading, naming the note and the heading, and firing for ALL THREE heading date grammars the ruling's audit measured (`Month D, YYYY`, ISO with time, bare ISO), each planted; (b) `intro_by_without_marker` — WARNING, one issue per `intro-by` heading whose entry carries no well-formed marker, i.e. exactly the entries AC-2(c) declares invisible to the accessor; "well-formed" is the LIBRARY's grammar, IMPORTED from `obsidian_schemas.timeline_entry` and never re-defined in `scripts/lint_vault.py`, which AC-2(e)'s scan asserts; (c) `retired_key_introduced_by` — ERROR, one issue per note carrying the retired frontmatter key. (d) SILENT ELSEWHERE — over a planted vault holding a well-formed `intro-by` entry, a well-formed `intro-to` entry, a person with an empty `## Timeline`, a person with no `## Timeline` at all, and a note whose prose merely mentions an introduction, none of the three checks fires; and over the frozen fixture corpus (which after AC-3(c) carries no `introduced_by` and no timeline entries at all) all three are silent, asserted as a SET EQUALITY whose baseline is DERIVED IN THE SAME RUN and named here: the set of `(note, rule_id)` pairs `lint_vault` yields over `tests/fixtures/vault/` with the three new checks registered equals the set it yields with those three rule ids filtered out. The baseline is that second computation, not a committed file — `docs/lint-vault-live-baseline.md` (`tests/test_lint_vault_fix_rules.py:113`) is the LIVE-vault bracket and is NOT the referent for this clause. A set equality rather than a count so a new issue that displaces an old one cannot cancel out. (e) NEVER REPAIRS — all three carry `auto_fixable=False`, so none enters `apply_fixes`; WI-026's four-bucket per-issue accounting still totals exactly the auto-fixable issue count with the three checks enabled, and each new issue is counted by the summary's non-fixable figure. (f) UNDECODABLE NOTES — a note `read_vault` cannot decode is reported by none of the three, preserving WI-026's `read_error` triage order.
why: Ruling §3 asks for the legacy detector by name; (b) and (c) are the two the ruling's other clauses imply and which would otherwise have no enforcement at all — (b) is the declared marker AC-2(c)'s narrowing arm asserts against, so without it the accessor's honest narrowing has nowhere to land, and (c) is what makes AC-3's "cannot creep back" observable on the tool Dave actually runs rather than only at a write door nobody watches. This matters because the hermetic floor structurally cannot watch the vault (WI-031 clause (v)) — the linter is the only standing instrument over live data. (a)'s three grammars are planted rather than sampled for the P4 reason (the corpus has no entries) and are named explicitly because the audit measured all three live (43 / 38 / 5) and a detector written against one of them would be silent on nearly half the corpus while passing a single-grammar test. (d) is asserted in both directions because a detector pinned only on its true positives is the WI-235 shape; the negative is cheap here and the `intro-to` member is the specific one that catches a substring-matching implementation, the same wrong-but-self-consistent build AC-2(a) discriminates against. (d)'s baseline is named as a derivation inside the same run rather than a committed file because this tree has no committed fixture-corpus issue set — the one baseline document it does carry is the LIVE bracket — and a clause pointing at a non-existent referent is a clause that cannot be run; computing the corpus's issue set twice, with and without the three rule ids, is the referent that actually exists and it also survives any future change to the corpus. (b) imports the grammar rather than re-stating it because `scripts/lint_vault.py` is precisely where this tree's one existing second copy of a parser already lives (P7), so it is the file most likely to grow a third. (e) is ruling §3's "never auto-fixed" made enforceable rather than documented, and it is the right call three times over: rewriting a legacy entry is a live migration with its own bracket (A5), synthesizing a missing marker would be inventing a counterparty, and deleting a frontmatter value is data loss whose direction is a judgement. (f) keeps WI-026's triage order intact — an undecodable note is reported as undecodable, once, and never as four separate faults.
check: test_lint_vault_reports_the_intro_legacy_shapes_and_never_repairs_them
kind: test
```

### Examples of done

**1 — the consumer question, answered by a call instead of a regex — and answered about the right person.**
*Given* a vault where Alice's note and Bob's note each carry their own `intro-by` entry written by
HAL9000's door, with different introducers on different days,
*when* exocortex asks `PersonRepository.introduced_by(alice)`,
*then* it gets back ALICE's introducer and date as typed values — not Bob's, and not both of them — and
exocortex contains no code that knows what `<!-- … -->` means.

**2 — the retired key cannot come back.**
*Given* any writer in the estate that tries to put `introduced_by` on a person note — through `save`,
through `update_fields`, or by setting the attribute on a loaded `Person` and saving it,
*when* the write reaches the library,
*then* it is refused loudly, nothing is written, and the error names the key. If one ever does land by a
hand-edit in Obsidian, `lint_vault` names that note as an ERROR the next time Dave runs it.

**3 — the vocabulary has a home to move INTO, and the old corpus stays honest.**
*Given* orchestrator or any new writer that installs this library,
*when* it builds a `TimelineEntry` and hands it to the door — including one carrying a kind NOBODY has used
before, such as `deal-closed`, which the library accepts on its slug rule without anyone editing a list,
*then* the rendered bytes are identical to what HAL9000 writes today for the kinds HAL9000 writes, the dedupe
key is the marker it actually writes, nothing the library now refuses was writable through HAL9000 yesterday,
and the 86 legacy `[intro]` entries are untouched but listed in `lint_vault`'s report —
visible, not silently rewritten and not silently ignored.

**4 — the second half is an item, not a hope.**
*Given* this item is done and HAL9000 still has its own `timeline_entry.py`,
*when* Dave asks "so is the vocabulary actually in one place yet?",
*then* the answer is a work item with an id, an owner and a re-entry condition — committed as
`docs/wi-033-hal9000-cutover-followup.md`, naming the HEAD the library is pinned against — rather than a
sentence in a dependencies list that nobody is holding.

## Architectural Review — 2026-09-28 (round 4)

**Recommendation: PROMOTE to architected.** This round re-reads the third fold — the one taken after the
AC red-team, on the PERSON axis of AC-2. The finding is CLOSED, and closed by the same instrument the kind
axis already used (a planted discriminating member) rather than by a sentence promising the right read
path. The read route is also now stated in prose in the three places a builder actually reads
(`## Approach`, A1, example-of-done 1), so the document is buildable one way. Nothing structural is open.
My residual findings are two spec-writer notes, both on corners that cannot ship a cross-attributing
library under either reading; I say why below rather than asserting it.

### Trigger check

Unchanged from rounds 1–3 and still firing: a new module (`obsidian_schemas/timeline_entry.py`); >3 files
in different concerns (`timeline_entry.py`, `repositories/person.py`, `name_gate.py`,
`scripts/lint_vault.py`, `tests/fixture_vault.py` + the corpus); a new persistent read contract over vault
bytes (the marker grammar); cross-system integration (a door four repos call, an accessor a fifth is parked
on); effort > 1 day. Review run in full.

### The red-team's finding, re-read

**CLOSED, and the closure is a discriminant rather than a promise.** The fold does three things and the
third is the one that matters. (i) AC-2's fixture now plants TWO person notes, A and B, each with its own
`intro-by` entry differing in counterparty, day and `source` bytes. (ii) **AC-2(a2)** asserts scoping in
BOTH directions and on BOTH people — `introduced_by(A)` is exactly A's record (never B's alone, never the
union) and `introduced_by(B)` is exactly B's. (iii) It adds the INVARIANCE run: the same `introduced_by(A)`
over a temp vault with B's note removed returns the IDENTICAL list.

I checked that the three assertions together actually close the two builds the red-team named, because a
pair of them would not have. The UNION build is caught by the A-direction assertion with B present, and
would go green on the B-removed run alone; the READ-ONE-FIXED-NOTE build is caught only by the second
person's direction (if A happens to be the note read, every A-side assertion passes in both runs) — so it
is the both-people clause, not the invariance clause, that kills it. Both are present. The invariance run
is what converts "filters a vault-wide read by something" into "reads that person's own note", which is the
clause's own stated intent. This is P4's WI-286 posture applied to the axis the accessor's first argument
selects on, and P4 is why it had to be planted: the frozen corpus has zero timeline entries
(`^### |<!-- ` over `tests/fixtures/vault/` still returns nothing at HEAD `bc2f11e`), so it can supply a
second person no more than it can supply a second kind.

**The read route is now stated, and it is buildable against code that exists.** `## Approach:553-556` and
A1 (`:275-277`) both say the accessor reads THAT PERSON'S OWN `## Timeline`, loaded through
`parse_body_sections` from the note the person was parsed from, never a vault-wide scan — and each half of
that has a mechanism in the tree. Provenance: `_source_path` is a `PrivateAttr` on `BaseEntity`
(`models.py:53`, unwritable by construction per `:49-52`), stamped by `parser.py:250-252` on every file
parse, and `repositories/base.py:392-414` `_resolve_write_target` is the one place it is turned into a
path. Section read: `body_sections.py:39` `parse_body_sections` returns an `OrderedDict` keyed by heading
text, so `"Timeline"` is a key lookup and no new parser is needed. So AC-2(a2)'s "from the note A was
parsed from" is a route, not an aspiration.

**Fold hygiene — no contradiction introduced.** I re-read the three surfaces the fold touched against the
rest of the document. D6 (fixtures in a temp vault, not the frozen corpus) still holds: two planted person
notes are behavioural specimens owing the census no row. AC-2(b)'s plurality scenario is now explicitly
run with B's note still present, so "two records" means that person's own two. AC-2(d)'s three silence
clauses are now run with B's well-formed note present, so "nothing" means nothing rather than somebody
else's record — which is the same discriminant applied to the negative direction, and it is the clause I
would have asked for had the fold only fixed the positive one. Example-of-done 1 carries the shape in
Dave's terms. Nothing in AC-1, AC-3 or AC-4 depends on AC-2's fixture cardinality.

### What verified clean this round

Only material newly asserted or newly depended on; rounds 1–3 verified the rest at the same HEAD.

**The provenance seam supplies what AC-2(a2) needs.** `models.py:53` declares `_source_path` as a
`PrivateAttr(default=None)`; `parser.py:250-252` stamps it on `parse_markdown_file`; `base.py:406` reads
it. Every Person the repository hands a consumer comes through `_load_file` → `parse_markdown_file`
(`base.py:336`), so the stamp is present on the whole live population, not just on the fixture.

**The sibling door already resolves the same way, which is why the accessor can.**
`person.py:1489-1493` is provenance first (`_resolve_write_target`), name-keyed lookup second, refuse
third — so an accessor built on the same two-step agrees with the writer about which note is "this
person's note". That matters more than it looks; see the first note below.

**Both derivations AC-2(e) and AC-3(b) rest on still exist and are still parameterized.**
`tests/derivations.py:185` `python_files_under(*roots)` takes roots varargs, so the widened
`obsidian_schemas/**` + `scripts/**` scan needs no new walker; `tests/derivations.py:1054`
`gate_call_declarations` is still the derivation the arm sweep extends.

### Review

**Fit.** Unchanged and still clean: a leaf module importing `errors` only mirrors `name_gate.py:14-20`;
A2's rejection of `body_sections.py` stands on that module's own entity-agnostic contract
(`body_sections.py:4-9`). The fold's read route — provenance then `parse_body_sections` — is the pattern
`append_to_timeline` already ships, so the accessor harmonizes with the door rather than inventing a
second way to find a note.

**Duplication.** The dimension the item exists to serve, and it survived the fold intact: AC-2(e) still
scans `obsidian_schemas/**` AND `scripts/**` for a DEFINITION of the marker grammar, permits an import,
forbids a re-definition. The fold added no new parser — it reuses `parse_body_sections`, which is the
right answer under LESSONS #4.

**Boundaries.** The WI-185 seam answer is unchanged and is now enforced on both of the accessor's axes:
the counterparty and day survive into the marker slot (kind axis), and the note identity survives into
`_source_path` (person axis). Neither is reconstructed. The fold is in fact a second instance of the same
seam discipline — a build that globbed the vault would have been reconstructing "whose note is this" from
file contents when the answer was already stamped on the object it was handed.

**Determinism boundary.** Nothing mechanical is handed to a judgement channel. Day and counterparty come
from slots; the person comes from the stamp; prose is never read, by D1 and by AC-2(d)'s assertion.

**Reversibility.** Additive module, additive overload, three report-only detectors, one gate rule; the one
sticky step is still the single `CORPUS_DIGEST` regeneration. The fold adds two temp-vault fixtures and
one clause — nothing durable.

**Generalization.** D8's split still holds and the fold does not disturb it: the door generalizes (any
slug-valid kind), the parity CLAIM stays bounded to captured bytes. The person-axis fold is the
complementary narrowing — the accessor's answer is bounded to one note, asserted rather than assumed.

**Cost & maintenance.** One capture artifact with a machine-anchored staleness pin (AC-1(a3)) and a minted
follow-up that re-runs it (D7 + precondition 4). The fold adds one fixture note to a temp vault: no
recurring cost.

**Build vs extend vs integrate.** Extend. A2–A6 record the alternatives with their trigger predicates;
nothing external is pulled in.

**Prior art (outside view).** Re-asked of this fold and unchanged in conclusion: not a
constraint-compensation item — nothing here builds machinery around a subtracted capability. The shape
(publish the shared schema package, cut consumers over in a following change, pin the publisher against
captured bytes in the interim) is the ordinary industry answer, and the scheduled cutover the world pairs
it with is minted (D7) and recorded in this tree (precondition 4). The standing drift check is declined IN
WRITING with an ownership argument and the runnable form recorded for the holder of the second copy, which
satisfies the role's blocking condition on a deferred option. Scoping a read to the entity it was handed,
rather than to a store-wide query, is the ordinary ORM/repository answer too — the fold moves toward the
standard shape, not away from it.

### Notes (non-blocking) for the spec-writer

- **AC-2 never says what the accessor does with a Person carrying NO provenance, and the READ door and the
  WRITE door should not answer that differently.** `_source_path` defaults to `None` (`models.py:53`), so a
  hand-constructed `Person(name=...)` — not one the repository parsed — has no stamp. Every clause of AC-2
  is written over PARSED fixtures, so all three plausible builds (raise; fall back to the name-keyed
  lookup; return `[]`) are green. Live exposure is nil today: every Person a consumer gets comes through
  `_load_file` → `parse_markdown_file` (`base.py:336`, `parser.py:250-252`), so the stamp is always there.
  My recommendation, stated so the spec-writer can take it in one clause rather than re-derive it:
  mirror `append_to_timeline` exactly — provenance first, `get_file_path(person.name)` second
  (`person.py:1489-1493`) — because an accessor that resolved "this person's note" by a DIFFERENT rule than
  the door that wrote the entry is a new divergence class in the one place WI-029 just spent an item
  closing: `append_to_timeline(p, e)` followed by `introduced_by(p)` could read a different note than the
  one just written. **Why this is not blocking:** none of the three builds cross-attributes for the live
  population, the one this item's Intent is about; the choice changes only a corner no consumer reaches
  today, and it is a one-clause statement on a DRAFT criteria frame.
- **The anchored dedupe (AC-1(e)) must locate the `## Timeline` span by READING, never by the
  parse/write round trip — and the file it lands in carries a comment warning about exactly that.**
  `person.py:1512-1534` documents, at length, why the no-`## Timeline` accommodation uses string insertion
  and NOT `parse_body_sections`/`write_body_sections`: that round trip keeps only `^## `-delimited spans,
  so it deletes any preamble above the first heading and destroys a heading-less body outright. Using
  `parse_body_sections` to FIND the span for a dedupe test is read-only and safe; using the round trip to
  write the entry would silently re-open a shipped data-loss guard while AC-1(f) (placement unchanged)
  stayed green, because placement and preamble-preservation are different properties. One sentence in
  AC-1(e) or (f) saying the anchoring is a read and the write path is untouched would close it.
- **Round 3's two open spec-writer notes are still open and still correctly non-blocking**: AC-1(c2)'s
  guard-set equality needs the right-hand side reified as *the guard-class probes the capture records as
  ACCEPTED* (the forgery guard is HAL9000's own, so those probes sit on the refuse side of the capture),
  and AC-1(a2)'s "the set of kinds the capture holds" should read "the kinds the `## Parity samples`
  section holds", since precondition 1 part 3 deliberately probes a slug-valid kind that no sample renders
  and which must therefore NOT be in `PARITY_KINDS`. I re-read both and neither ships a wrong system under
  either reading; I am recording them so they are not lost between the red-team fold and the spec-writer.
- **Nothing in this round re-opens D7 or D8.** The window between the library half and the cutover remains
  accepted in writing, precondition 4 remains the act that makes the mint real, `HAL9000_PARITY_ANCHOR`
  remains a pin rather than a monitor, and the write door remains the open slug rule with `PARITY_KINDS`
  gating nothing.

```verdict
gate: architect
verdict: PROMOTE
date: 2026-09-28
model: claude-opus-5
note: The AC red-team's person-axis finding is closed with a planted discriminant rather than a promise — AC-2 now plants two person notes and asserts scoping in both directions on both people PLUS invariance to B's removal, which is what it takes to kill the union build and the read-one-fixed-note build (a pair of those three clauses would not have), and the read route is stated in `## Approach`, A1 and example-of-done 1 and is buildable on code that exists (`_source_path` at `models.py:53` stamped by `parser.py:250-252`, `parse_body_sections` at `body_sections.py:39`); nothing structural is open and my two residual findings are corners that cannot ship a cross-attributing library under any reading.
```

## AC Red-Team — 2026-09-28 (round 2)

Re-spawned to verify the round-4 architectural fold of my own round-1 finding (AC-2's person axis was
undiscriminated). Re-read `## Intent`, `### Examples of done`, the 2026-09-28 `## Ruling`, and the
Exploration Notes before re-reading AC-2's current text, per the role's Step 2 — not just the architect's
round-4 narrative of the fold.

### The fold, re-read against the document itself

**CLOSED.** AC-2's `desc` now plants a second person note, B, with its own well-formed `intro-by` entry
whose counterparty, day, and `source` bytes all differ from A's, and states the oracle for both: exactly
one record for A carrying A's own counterparty/day/`source`, and no record carrying B's counterparty or
day. AC-2(a2) asserts scoping in BOTH directions — `introduced_by(A)` is exactly A's record (never B's
alone, never the union), `introduced_by(B)` is exactly B's — and adds the invariance run: the same
`introduced_by(A)` call over a temp vault with B's note removed returns the IDENTICAL list.

I checked this is actually sufficient rather than trusting the architect's own count: the union build
(read all `intro-by` markers vault-wide) is caught by the A-direction assertion with B present; the
read-one-fixed-note build is caught by the B-direction assertion (if the fixed/first note happens to be
A, every A-side clause still passes, so only checking A's side would have missed it); the invariance run
is what rules out "filters a vault-wide read by something" as opposed to "reads that person's own note" —
a build that reads the whole vault and filters by an argument-derived predicate could still pass the
both-directions check but would return a DIFFERENT list once B's note is removed only if its filter
degenerately depended on B's presence, which the invariance clause forecloses directly. All three
specimens are needed and present; no single one of them would have closed my original finding alone.

The read route is now also stated in prose in the three places a builder reads (`## Approach:553-556`,
A1, example-of-done 1): the accessor loads that person's own body through `parse_body_sections`, from the
note the person was parsed from, never a vault-wide scan.

### Independent verification of the mechanisms the fold leans on

I did not take the architect's round-4 code citations on faith; re-read each at its cited location:

- `models.py:53` — `_source_path: Optional[Path] = PrivateAttr(default=None)`, confirmed a `PrivateAttr`
  on `BaseEntity`, with the docstring at `:45-52` stating it is unwritable through `extra="allow"` by
  construction. Matches the claim.
- `parser.py:250-252` — `if entity is not None: entity._source_path = file_path`, confirmed as the one
  stamp site, inside `parse_markdown_file`. Matches the claim.
- `body_sections.py:39` — `def parse_body_sections(body: str) -> OrderedDict[str, str]`, confirmed as a
  plain heading-keyed parse with no entity knowledge, matching A2's rejection rationale. Matches the claim.
- `person.py:1489-1493` — `append_to_timeline` resolves `self._resolve_write_target(person)` first, falls
  back to `self.get_file_path(person.name)`, confirmed — this is the same two-step order the fold's
  read-route prose says the accessor should mirror.
- `person.py:1502` — `if deduplicate_key and deduplicate_key in content:`, confirmed as a whole-file
  substring test (P2), unrelated to the current fold but re-checked since it underlies D1/D2/AC-1(d)/(e).
- `person.py:1543-1545` — confirmed prepend-after-marker (P3).
- `name_gate.py:359`, `:373`, `:364-368`, `:400` — confirmed exactly as the P10 premise states: the
  undeclared-refusal rule speaks only to `name:` (`:359-360`); the declared-non-person early return is
  guarded by `declared_type is not None` with the comment at `:364-368` stating verbatim why that half is
  load-bearing; the person body opens with `result = dict(introduced)` at `:400`. Matches AC-3(a)'s
  placement claim.
- Grep for `<!--`/`-->` across every `*.py` in the tree: zero matches (P9 holds), and no
  `timeline_entry.py` exists anywhere in the tree yet (P1 holds) — both premises the fold's reasoning and
  AC-2(e)'s scan depend on are still true at this re-read.

Every premise the fold's closure depends on re-verified true independently; none was taken from the
architect's narrative alone.

### Fresh sweep of AC-1, AC-3, AC-4 for anything the fold disturbed

Re-attacked the other three criteria against the Intent once more rather than assuming the fold was
scoped only to AC-2. AC-1(a)–(f) still ground their oracle in the precondition file's own declared
samples rather than a re-typed literal, with (a4)'s planted out-of-table kind still the falsifiable
discriminant between the open and closed kind-table readings. AC-3(a)/(b) still rest on the measured P10
placement and the arm-sweep set equality, unaffected by the AC-2 fold. AC-4(a)-(f) still separate positive
detection (planted vault) from negative silence (frozen corpus, itself now containing zero timeline
entries either way), so a no-op detector still fails the positive half. Nothing in AC-1, AC-3, or AC-4
depends on AC-2's fixture cardinality, and I found no new gameable AC on this pass.

### What I did not re-litigate

The architect's round-4 non-blocking notes (a provenance-less `Person`'s three-way ambiguity; the
anchored-dedupe read-vs-write-path wording; round 3's two open reifications on AC-1(a2)/(c2)) are
corner-case wording notes on a document still explicitly marked DRAFT, none of which can ship a
cross-attributing or otherwise Intent-violating library under any of their stated readings. I re-read them
and agree they are spec-writer material, not red-team material — raising them again here would be the
regress signature the role warns against (findings drifting from the system under review to the
machinery reviewing it), not a second attack.

```verdict
gate: ac-red-team
verdict: PROMOTE
date: 2026-09-28
model: claude-sonnet-5
note: Round-1's AC-2 finding (person axis undiscriminated) is closed — the fold plants a second person note with a differing counterparty/day/source, asserts scoping in both directions on both people, and adds an invariance-to-removal run, which together kill both the union build and the read-one-fixed-note build; independently re-verified every code citation the fold leans on (models.py:53, parser.py:250-252, body_sections.py:39, person.py:1489-1493/1502/1543-1545, name_gate.py:359-400) plus P1/P9 by fresh grep, all holding, and a fresh sweep of AC-1/AC-3/AC-4 found nothing new.
```

## AC Sign-off

```verdict
gate: ac-signoff
verdict: PROMOTE
date: 2026-09-28
reviewer: dave
channel: conversational
signed_at: 2026-09-28T10:52:08+01:00
provenance: verified
signoff_escalation: ESC-WI-033-exploring-awaiting-ac-signoff-3326b5a4
ac_hash: a2bb3913f2c8
intent_hash: beab28f263a8
ac_hash_AC-1: c6ef8476f351
ac_hash_AC-2: 6535ee8af9f4
ac_hash_AC-3: c198dfc5612c
ac_hash_AC-4: f9d4f2dffcaf
artifact: docs/spec-reviews/WI-033-dave-review-2026-09-28.md
```

## Data Audit — 2026-09-28

**Recommendation: PROMOTE to specced**

### Trigger check

**Class 1 AND Class 2, both firing, and the item is unusually premise-heavy for this tree.**

*Class 1 (data-distribution / field-presence).* Four quantified or existence claims about live data are
load-bearing: the population an unconditional `introduced_by` ban could brick is EMPTY; legacy `[intro]`
entries number 86 with only 22 marker-bearing (the 22/86 rate is what makes AC-2(c)'s narrowing arm honest
rather than convenient); the legacy heading grammars are three, in the proportion 43 / 38 / 5 (AC-4(a)
plants all three because a detector written against one would be silent on nearly half the corpus); and
the three new detectors have an expected live yield (86 / 0 / 0).

*Class 2 (rule-effect-against-existing-corpus).* Three of the four criteria introduce a rule whose
correctness depends on its effect against what exists TODAY, not only on hypothesised inputs: the gate's
retired-key refusal (AC-3) runs against every note any arm writes; the three `lint_vault` detectors (AC-4)
run against the whole live vault and the whole frozen corpus; and the marker-anchored dedupe narrowing
(AC-1(d)/(e)) changes a door six production call sites reach. The item also rests on a fourth premise class
this gate treats as Class 1 by analogy — an EXTERNAL CONTRACT, HAL9000's shipped renderer and validator,
whose bytes are the meaning of the word "relocate" (`### Constraints discovered`).

*Universal quantifier present,* so the counterexample hunt below is owed and run: `## Intent` quantifies
over "**every** timeline entry **any writer** puts on a vault note" and over "**any** consumer".

### Premises, and where each is grounded

Every premise is grounded in a COMMITTED artifact this document declares in `## Write Targets`, or in this
tree at HEAD `133c27a`. Nothing load-bearing rests on a recollection. Listed with what I did to it.

**Re-run by this gate, in-tree, at this HEAD** (Read / Grep / Glob only — no shell, no live vault, and the
floor is hermetic by WI-031 clause (v), so the live half is read from the committed census and never
re-measured):

- **P1 — the vocabulary exists nowhere here.** `**/timeline_entry*.py` over the whole tree → **no files**.
  So "relocates INTO the library" is a genuine addition and AC-2(e)'s one-definition scan starts from zero.
- **P4 — the frozen corpus contains ZERO timeline entries.** `^### |<!-- ` over
  `tests/fixtures/vault/` → **0 matches across 0 files**. This is the premise that GOVERNS every other
  criterion: the corpus cannot tell a right accessor from a wrong-but-present one, so sampling is not an
  option that exists and every discriminating member — both kinds and both PERSONS — is necessarily planted
  (WI-286). Re-verified rather than taken from three architect rounds, because if it had drifted, AC-2's
  entire fixture posture would be wrong.
- **P5 / AC-3(c) — exactly one fixture carrier, and the swap has a real referent.** `introduced_by` over
  `**/*.md` → exactly one note under `tests/fixtures/vault/` (`@Morvette Harkwell.md`); the manifest
  declaration is the single `undeclared={"introduced_by": "Voxleaf"}` at `tests/fixture_vault.py:325`; and
  `docs/vault-fixtures.md:279` does read "a `manager:` or `introduced_by:` key", so AC-3(c)'s
  documentation clause points at text that exists and the `manager:` swap is the corpus's own co-equal
  specimen rather than a new invention.
- **P8 — one rule lands in one place.** Exactly six `gate_write(` call sites, matching AC-3(b) verbatim:
  `writer.py:252`, `:385`, `:443`, `:494`, `repositories/base.py:728`, `repositories/person.py:1270`.
  `writer.py:494` is literally `gate_write({}, declared_type=None, whole_record=False)`, so AC-3(b)'s
  excluded-set EQUALITY is true as stated and the other five are all driven.
- **P9 — the scan population is zero, so "exactly one definition" is a claim about a file that does not
  exist yet.** `<!--` / `-->` over every `*.py` in the tree → **zero matches**; `introduced_by` over every
  `*.py` → **one hit**, the fixture manifest line above. So nothing under `obsidian_schemas/**` or
  `scripts/**` defines the marker grammar today, `intro_not_symmetric`'s prose regex falls outside AC-2(e)'s
  predicate by construction rather than by exemption, and AC-3's refusal has no existing in-package reader
  to break.
- **The derived instruments both criteria lean on exist.** `tests/derivations.py:185 python_files_under`
  (parameterized over roots, so AC-2(e)'s widened `obsidian_schemas/** + scripts/**` scan needs no new
  walker) and `tests/derivations.py:1054 gate_call_declarations` (the derivation AC-3(b)'s arm sweep
  extends). Both "derived rather than hand-listed" clauses are buildable, not aspirational.

**Grounded by committed precondition, read end-to-end and checked for internal consistency against the
criteria that consume it:**

- **Precondition 1 — `docs/wi-033-hal9000-timeline-entry-capture.md` (the external contract).** This is
  the strongest artifact of the four and it clears the bar the role sets for an external premise: every
  `rendered` block and every `verdict` was produced by RUNNING HAL9000's code under HAL9000's own venv, not
  by reading it, and the generator is reproduced verbatim so a re-run is one command. It carries part 1
  (verbatim source with line ranges), part 2 (**six INPUT→OUTPUT parity samples** across five kinds, each
  with `when` PINNED as an ISO string, `discriminator` explicit-`null` where absent, and `rendered` as a
  literal block scalar), part 3 (**29 INPUT→VERDICT probes** over `kind` / `text` / `discriminator`), and
  the 40-hex staleness anchor `d54430da9547a93525c6cc1b20cf781c9a63f82e` that AC-1(a3) machine-checks and
  D7's cutover re-entry condition diffs against. AC-1(a)'s oracle is therefore EXECUTABLE — both sides read
  from the file, no literal re-typed — which is what round 1's finding 2 was about.
- **Precondition 2 — `docs/wi-033-intro-corpus-baseline.md` (the live distribution).** Counts and shapes
  only, no note name and no identifier, with the literal predicates declared, the command given, the
  machine-readable YAML snapshot and the verbatim JSON output both present, and `census.py` appended
  verbatim. The numbers: **5664 markdown files scanned, 1314 person notes, 0 undecodable**;
  **`introduced_by` frontmatter carriers = 0**; legacy `intro` **86 entries, 22 well-formed markers**,
  grammars **43 `Month D, YYYY` / 38 ISO-with-time / 5 bare ISO**; `intro-by` **1 entry, 1 marked, on 1
  note**; `intro-to` **0**; every timeline heading found sits inside a `## Timeline` section and **no marker
  anywhere carries a kind different from its own heading** (`marker_kind_mismatch_by_kind` all zero). Every
  number the ruling asserted in prose is now a dated, re-runnable snapshot, and they AGREE — the ruling's
  86 / 22 / 43 / 38 / 5 and its "readback: `^introduced_by:` = 0" all reproduce.
- **Precondition 3 — `docs/wi-033-consumer-audit.md` (the rule's blast radius).** The estate-wide sweep the
  WI-032 scar demands: 36 repos under `~/Workspaces` plus `~/.claude/skills` and `~/.claude/agents`, one
  literal pattern sweep per repo with a 40-hex HEAD and dirty count each, every production hit read at its
  call site, and the load-bearing column present — whether a call passes a dedupe key that DISAGREES with
  the marker it writes. Result: **six production `append_to_timeline` call sites, all passing a `str`**, so
  the typed overload has ZERO callers on the day and the marker-anchored narrowing touches no live call;
  three of the six pass a prose key while writing NO marker and are named as the ones that must not be
  migrated blindly; **`introduced_by` as a frontmatter key has ZERO readers and ZERO writers in code
  estate-wide**. It also CORRECTS a claim this document had carried: exocortex's WI-006 is email ingestion,
  not parked relationship edges, and the measured waiting consumers are HAL9000 WI-078 and orchestrator
  WI-194. That correction is already folded into `## Problem / Motivation` and `### Dependencies`.
- **Precondition 4 — `docs/wi-033-hal9000-cutover-followup.md` (the second half is an act).** Records a
  performed mint: **HAL9000 WI-082**, `docs/timeline-entry-cutover-to-library.md`, stage `idea`, through
  workshop's locked mint CLI with the readback pasted (`next_id` advanced to 83), plus the one-line scope,
  D7's three re-entry clauses verbatim, and the drift-window command a later reader can run. Disclosed
  honestly: the mint lives in HAL9000's WORKING TREE, uncommitted there, and committing it is HAL9000's act.
  That is a real residual but not this gate's axis — the id exists and cannot be re-issued.

### Counterexample hunt (WI-293) — the Intent's two universals

**Domain enumerated:** every writer that puts a `### …` entry into a vault note's `## Timeline`, and every
reader of "who introduced this person", across the whole estate. **Predicate that enumerated it:**
precondition 3's per-repo sweep — the literal
`append_to_timeline|append_timeline_entry|TimelineEntry|timeline_entry|/timeline|## Timeline|introduced_by|introduced-by|intro-by|intro-to|\[intro\]|deduplicate_key`
pattern over 36 repos plus `~/.claude/skills` and `~/.claude/agents`, with every production hit read at its
call site rather than inferred from the grep line, widened per repo where the first sweep was thin. I could
not re-run that sweep (no shell, and other repos are out of this spawn's scope), so I read its site tables
and cross-repo reading in full and hunted them for members the universal is FALSE about by design, at each
member's own declared granularity rather than by its filename. **Three classes found. All three are
dispositioned — but two of the three are dispositioned in the PRECONDITION and not in this document.**

- **Class A — the SECOND timeline door, `section-append`, and its four hand-composing callers.**
  `routers/entities.py:350` reaches `append_to_body_section` with `section` as a VARIABLE, so any HTTP
  client may hand-compose a `### …` entry into `Timeline` without touching the renderer at all. Its callers
  are instruction-driven, not code: orchestrator `roles/enricher.yaml:108-116`,
  `~/.claude/skills/new-person/SKILL.md:103-109`, `~/.claude/agents/scheduler.md:171-177`,
  personal-assistant `channels/obsidian.md:100-104`. All four write KINDLESS month or `Month D, YYYY`
  headings with no marker. *Disposition:* a NAMED EXCLUSION — `## Approach` and `### What this item does NOT
  do` already state that `append_to_body_section` is untouched, and precondition 3's cross-repo reading
  item 4 names this class explicitly as "a hole in the 'one vocabulary' claim" and states the behavioural
  requirement (`parse_markers()` / `introduced_by()` must return nothing for them; the three new checks
  must not flag them). AC-4(d) and AC-2(d) assert exactly that silence on planted equivalents.
- **Class B — writers that never reach either library primitive.** HAL9000 `backend/core/writer.py:120-150`
  (raw `open r+`, five callers, heading `### YYYY-MM-DD HH:MM:SS [<type>]`, kinds including `intro`);
  exocortex `ingestion/stages/company.py:300-346` (raw `write_text`, company notes); orchestrator
  `bin/batch-contact-context.py:256` (regex splice); and **this tree's own**
  `scripts/lint_vault.py:1176-1192` fixer, which APPENDS a fifth heading shape to the end of `## Timeline`.
  *Disposition:* a NAMED EXCLUSION, same referent — precondition 3 item 4 counts the linter's fixer as the
  fifth shape and requires the new detectors not to flag it; AC-4(d)'s both-directions silence is where that
  lands.
- **Class C — the highest-volume writer is kindless and must STAY on the loose path.** exocortex
  `ingestion/stages/note.py:375` writes a kindless `### Month D, YYYY` meeting line for every transcript
  and every attendee, deduping on a bare meeting stem matched WHOLE-FILE. *Disposition:* a DECLARED OUTCOME
  CLASS rather than an exclusion — AC-1(f) pins the string+key path byte-for-byte INCLUDING its whole-file
  substring looseness precisely because this caller depends on it, and precondition 3's cross-repo reading
  item 2 states that migrating it to the typed path without a marker would duplicate a meeting line on every
  hourly re-run. The three retired `[intro]` writers (HAL9000 `routers/introductions.py:433`,
  `skills/introductions_skill.py:134`, `backend/chat/commands/introduction_commands.py:88,93`) belong to the
  same class and are dispositioned the same way, plus A5 and `legacy_intro_entry`.

**On the kind axis the hunt was already run, by precondition 1, and it found a member.** Enumerating
HAL9000's renderer by CODE PRODUCER yields four kinds; the live census yields seven kinds on disk. The
capture dispositions each difference rather than filing it in the biggest bucket: `merge` (3 on disk, in
this renderer's exact shape with a well-formed marker, **no code producer anywhere in the estate** — an
ad-hoc HTTP-door caller) is ADMITTED to `PARITY_KINDS` with a sample whose `text` is declared synthetic;
`meeting` (1) and `email` (1) are EXCLUDED BY NAME with a stated reason — bare-ISO headings, no marker, a
pre-WI-058 writer's shape and not this renderer's. That is the shape this rule asks for, done before I got
here.

**Nothing found on the person axis that the AC red-team had not already found and the round-4 fold not
already closed** (AC-2(a2)'s both-directions plus invariance-to-removal assertions). I re-read that fold
against P4 and agree it is forced: a corpus with zero entries can supply a second PERSON no more than a
second KIND, so planting is the only instrument available.

### Rule-effect against the current corpus (the Class-2 half, stated as numbers)

- **The gate's unconditional refusal (AC-3):** live colliding population **0** carriers over 5664 files /
  1314 person notes, and **0** readers or writers of the key in code estate-wide. So D3's "the population is
  emptied rather than exempted" is true by MEASUREMENT on both halves — live by precondition 2, fixture by
  the one-note re-key AC-3(c) performs — and the DELTA doctrine's objection (P6) is void by measurement
  rather than by argument. Re-verified in-tree that the fixture carrier is exactly one note and one manifest
  line, so the swap's cost is what D3 claims.
- **The three detectors (AC-4):** expected live yield `legacy_intro_entry` **86**,
  `intro_by_without_marker` **0**, `retired_key_introduced_by` **0**. The zeros are not vacuous — the first
  is zero because the single live `intro-by` entry IS marked, which is the same fact that makes AC-2(c)'s
  narrowing arm a real population claim (22/86) rather than a hypothetical. Over the frozen corpus all three
  are silent by construction (P4: no entries at all; AC-3(c): no `introduced_by` after the swap), which is
  why AC-4(d) correctly derives its baseline in the same run instead of pointing at
  `docs/lint-vault-live-baseline.md`, which is the LIVE bracket.
- **The dedupe narrowing (AC-1(d)/(e)):** **zero** live callers affected on landing — all six production
  sites pass a `str` and stay on the unchanged path. The three key/marker-disagreeing sites are named, and
  their latent migration hazard is recorded in precondition 3 rather than discovered later.
- **Refusal parity (AC-1(c2)), and this is a data fact only the capture could settle.** Round 3 and the
  red-team both flagged that the guard-set EQUALITY reads as unsatisfiable if the left side is taken over
  all guard classes. The capture's 29 probes resolve it in the accept direction: HAL9000 itself REFUSES a
  delimiter-bearing `kind` (slug regex) and a delimiter-bearing `discriminator`, so those are not
  capture-ACCEPTED and cannot sit on the left. The capture-ACCEPTED inputs the library deliberately refuses
  are therefore exactly **five** — `text` containing `-->`, `text` containing `<!--`, and a discriminator
  that is empty, whitespace-only, or `:`-bearing — which is precisely AC-1(c)'s enumerated guard set. The
  reification round 3 asked for is not merely available; the capture names its five members. I record them
  here so the spec-writer does not have to re-derive the equality's left-hand side.

### Residuals — disclosed, neither blocking, each with the predicate that would close it

Two, which is at the role's cap of OPEN questions and deliberately under it: neither governs a criterion,
and neither can make the built thing wrong.

1. **"All 86 legacy `[intro]` entries are OUTBOUND" is the one live claim precondition 2 does not carry.**
   Ruling §2 and A5 rest on it ("not one is an introduced-by fact", so the legacy kind buys the accessor
   nothing and rewriting them is a separate migration), but the census is counts-and-shapes only by design,
   so the DIRECTION split stands on the ruling's same-day hand read of all 86 rather than on a re-runnable
   predicate. Why it is not blocking: no acceptance criterion reads it — AC-2's `[intro]`-yields-nothing
   assertion is planted and true by rule whichever direction the live entries face, and AC-4(a) reports all
   86 regardless, so any inbound stragglers are VISIBLE in the linter rather than silently lost. What it
   would change if false is the VALUE of a deferred migration (A5), which is a later, separately-bracketed
   decision. The closing predicate is counts-only and fits precondition 2's own no-identifier rule: split
   the 86 by body prose, `^Introduced by ` versus `^Introduced to `, and report the two counts. Worth
   running at build-start re-grounding (WI-022), not worth a round here.
2. **HAL9000 WI-082's mint is uncommitted in HAL9000's working tree.** Precondition 4 says so itself. The id
   is issued and `next_id` advanced, so the id cannot be re-used and the record in this tree's HEAD is
   truthful; committing it is HAL9000's act on Dave's word. Named so a later reader does not mistake it for
   a clean two-repo state.

### Conclusion

Both trigger classes fire, and every load-bearing premise is grounded against real data by a predicate a
later reader can re-run: the external contract by a capture produced by RUNNING HAL9000's code at a pinned
40-hex HEAD with input→output and input→verdict pairs; the live distribution by a dated counts-only census
with its script appended verbatim; the blast radius by an estate-wide sweep that CORRECTED one of this
document's own claims rather than confirming it; and the second half of the relocation by a performed mint
with an id. I re-ran the six in-tree premises the criteria bind to (P1, P4, P5, P8, P9 and both derived
instruments) at this HEAD and all six hold. The counterexample hunt over the Intent's universals found
three false-by-design writer classes, all already dispositioned — two of them in precondition 3 rather than
in this document's own `### What this item does NOT do`, which is thin but is a disposition in a committed
artifact this document declares, not an absence. No premise is contradicted by the data; the one live claim
that lacks a re-runnable predicate governs a deferred migration's value and no criterion.

```verdict
gate: data-premise
verdict: PROMOTE
date: 2026-09-28
model: claude-opus-5
note: Class 1 and Class 2 both fire and both are grounded — precondition 1 pins HAL9000's contract with six input→output render samples and 29 input→verdict probes produced by RUNNING its code at a 40-hex HEAD (which also settles AC-1(c2)'s guard set at exactly five capture-accepted members), precondition 2 turns every prose number into a dated counts-only census (5664 files, 1314 person notes, introduced_by carriers 0, legacy intro 86/22 marked, grammars 43/38/5, intro-by 1, intro-to 0), precondition 3 sweeps 36 repos and finds all six live append_to_timeline callers pass a str so the narrowing breaks nothing on landing, precondition 4 records a performed mint (HAL9000 WI-082); I re-ran P1/P4/P5/P8/P9 and both derived instruments in-tree at HEAD 133c27a and all hold, and the counterexample hunt over `## Intent`'s "every writer" found three false-by-design classes (the section-append door's four hand-composing callers, four raw-file writers including this tree's own linter fixer, and exocortex's kindless high-volume meeting writer) all already dispositioned as named exclusions or as AC-1(f)'s declared outcome class; the two residuals — the 86-entries-all-outbound direction split is not in the census, and WI-082's mint is uncommitted in HAL9000's tree — govern no criterion and are recorded with the counts-only predicate that closes the first at build-start re-grounding.
```
