---
id: WI-033
title: TimelineEntry relocates into the library, with a derived introduced_by accessor
project: obsidian-schemas
stage: building
created: 2026-09-26
last_touched: 2026-09-29
stage_changed: 2026-09-29
touched_by: session
tags: []
depends_on: []
transitions: ["idea>exploring@2026-09-28@session", "exploring>specced@2026-09-28@porter", "specced>ready@2026-09-29@session", "ready>building@2026-09-29@session"]
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
forgery inputs and the empty / whitespace-only / key-separator discriminators of AC-1(c); the threat
model's M1 added a FIFTH guard predicate on 2026-09-29 — a `text` line matching `^#{2,3} ` — which adds
no MEMBER to either side, because no capture-accepted probe carries that shape, §0 R1) so a build cannot
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
so this item ships no closed kind enum and adds no refusal HAL9000 does not already have beyond the five
guards §1.4 names — the four AC-1(c) enumerates and M1's structural-line guard, which refuses nothing the
capture records HAL9000 accepting; **it does not validate on HAL9000's behalf** —
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
library is no STRICTER than the INPUT→VERDICT boundary precondition 1's part 3 captures, with its five
deliberate guards (§1.4 — the fifth is M1's, folded 2026-09-29, and refuses no captured-accepted input)
enumerated as a set equality so the exception cannot be widened — over a probe population asserted to have
been read WHOLE, which is M2, folded 2026-09-29 (§12 Rule 3, §0 R7): an equality over a silently narrowed
probe set holds over any subset and retires the ratchet while the floor stays green. Being LOOSER than HAL9000
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

**Revised 2026-09-29 after the spec review's three blocking findings, at HEAD `be6e2fe`.** Where each
landed, so a re-reader does not have to diff. **Finding 1** (`errors.py:REASONS` grows by one while
`tests/test_name_gate.py:124` pins its SIZE by equality, owned by nobody) → §9 gains a wall row for the
pin, a second row for the two walls that already sweep that file, and a THIRD countable corpus in the
conscious-pin sweep — which also names `CORPUS_PINNED_ISSUES:809`, the reviewer's zero-cost note of the
same class; Task 2 owns the edit in the SAME task that adds the member and declares a second `verify:`
check; `tests/test_name_gate.py` is a declared write target; Task 11 RUNS the four predicates over it; and
`## Verification`'s Regression enumeration for `errors.py` is RE-SWEPT (it named four modules and the
sweep returns sixteen, with two of the four wrong). **Finding 2** (Task 12's verify was the whole project
floor, WI-314) → Task 12 keeps the pin accounting and this item's own four AC checks and drops the floor
run, with each pin re-read now discharged by a standing check rather than a hand reading; Task 1's
baseline capture is unchanged and stays informational. **Finding 3** (AC-3(c)'s oracle was a whole-file
absence pin over another item's splitter-mutable document, WI-278) → §0 R6, §6 and Task 7 narrow it to a
POSITIVE, section-scoped read, and `## Verification` carries the one-line coupling declaration beside
AC-1's. The six non-blocking notes are taken too: `:113` re-anchored to `baseline_sections:1518` +
`fenced_blocks:1550` (§10, §11.1, Task 3); §1.3 and §2 reconciled on ONE dedupe comparand
(`dedupe_probe`); `_compose_key` + `Marker.key` added so the key grammar is spelled once (§1.2, §1.3, Task
3(b)); `get_section` named as one addition to `lint_vault.py`'s existing import list (§5);
`STRUCTURAL_LINE_PATTERN`'s bound restated as a strict SUPERSET with its extra members declared inert
(§1.1); and `CORPUS_PINNED_ISSUES` named in the pin sweep. No signed fence is edited — §0 is where the
oracle reification lives.

**Revised again 2026-09-29 after the spec review's ROUND 2, whose two blocking findings the reviewer
named as ONE CLASS — and they are closed as a class (WI-226), not as two cases.** The generator: *a
check this plan orders derives a textual oracle from a markdown file the conductor commits and the caged
builder cannot edit, stated BY REFERENCE — to a shipped symbol, or to a phrase quoted from the
sentence's sense rather than the file's bytes — without anyone having read the target at the granularity
the oracle consumes.* The whole surface is enumerated at source in the new **§12** (four oracles over
three files, one of which — AC-3(c)'s live-half read of `docs/wi-033-intro-corpus-baseline.md` — this
sweep ADDED, since no earlier draft treated it as an oracle at all), closed by two rules made total over
it, and its next level swept and declared. Where each finding landed: **finding 1** (Task 7's PRESENT
phrase spans the hard wrap at `docs/vault-fixtures.md:279-280`, so a literal substring test is RED
against a correct conductor edit) → §12 Rule 2 — *every* phrase oracle compares whitespace-normalized
text against a whitespace-normalized phrase — restated in Task 7, §0 R6, §6 and `## Verification`'s
reader 2, with the precondition fence now quoting the file's own bytes, naming the exact deletion, and
saying in writing that the conductor is NOT asked to re-wrap. **Finding 2** (Task 3 prescribed
`baseline_sections:1518`, a TOTAL parse that raises on the capture's three undeclared headings, one of
them the `## Part 1` echo at `:587` inside the Appendix's `python` fence) → §12 Rule 1 — the selector is
spelled in its own terms as `select_sections(text, names)` and `baseline_sections` is named as the
RAISING DISCIPLINE to copy rather than a function to transplant — restated in Task 3, Task 7 (which
imports the same helper), §10, §11.1 and reader 1. The next level is swept in §12 and two dimensions it
returned are folded rather than left: AC-1(a3)'s HEAD read becomes a SET-singleton assertion (the
capture declares the same 40-hex four times, so "the first match" would be green on a capture declaring
two), and Rule 1's deliberate fence-unawareness is declared as a MEASURED residual in both coupling
declarations rather than argued away. The three non-blocking notes are taken too: the `REASONS` pin's
adjacent comment at `tests/test_name_gate.py:121-122` is admitted into Task 2's bounded edit (§9's row,
Task 2, `## Scope Boundary`, the write-target fence); the "key" paraphrase is reconciled against the
file's bytes in §6, §0 R6 and the precondition fence; and the fenced-`## ` residual is recorded with its
measurement. No signed fence is edited this round either.

**Revised a third time 2026-09-29, folding the threat model's round-3 required mitigation M2 — and the
finding lands inside the previous round's own fold, which is why it is closed one LEVEL up rather than as
a clause.** M2's substance: §12's next-level sweep declared that a truncated span "would redden this item"
uniformly, and that is false for `## Validation boundary`, where a PARTIAL truncation leaves AC-1(c2)'s
guard-set equality satisfied over a subset and silently retires the anti-widening ratchet §1.4, R1 and
`## Risk Analysis` row 2 all name. Where it landed: **§12 gains RULE 3** — every oracle derived from a
selected span either fails on a truncation by construction (and this document names the assertion that
does it) or carries an explicit completeness assertion, which for the capture's two spans is the
whole-file `yaml`-fence accounting — plus **dimension (vii) FAIL DIRECTION**, answered per span for all
four selected spans, and **the level BELOW (vii)** swept and declared: nine run-time-derived populations
this plan quantifies over, of which eight were already non-vacuous and the ninth, Task 7's
emptied-population absence scan, is closed in this same edit by a member pin. **Task 3** asserts the
accounting before any sample or probe is read; **§0 gains R7**; §12's fence-extraction paragraph and
Task 3 now require the ONE deviation the mechanism turns on — `select_fenced_blocks` RETAINS the info
string, which `fenced_blocks:1550` discards at `:1554-1559`, read at its symbol this round — and Task 3's
WI-235 battery is extended to that helper's reach, which is what Rule 3's accounting now rests on. Rule 3
is asserted, not merely written, and no signed fence is edited this round either: the accounting adds no
member to either side of AC-1(c2)'s equality, it asserts that the population both sides are drawn FROM was
read whole.

### §0 — Where this spec's refinements live, and why not in the fences

`hash_section` freezes the WHOLE body of `## Intent` and `## Acceptance Criteria`, nested `###`
subsections included, and `docs/spec-reviews/WI-033-dave-review-2026-09-28.md` records the frozen bytes:
they include the section's `**DRAFT — not frozen.**` preamble and all of `### Examples of done`. So every
byte of that span is a signed artifact now, the preamble's own sentence included — it is left
byte-identical deliberately, and the `ac-signoff` fence beneath it is the operative status. One
consequence governs this whole section: **the five residual notes rounds 3 and 4 left for the spec-writer
— plus R6, the spec review's 2026-09-29 finding 3, and R7, the threat model's round-3 finding M2, both on
a signed clause's ORACLE rather than on its text —
are resolved HERE, in unsigned prose the builder reads, rather than by editing a signed fence.** A
within-spirit edit would invalidate the signature and buy a re-sign for text that changes no behaviour;
the builder executes `## Design` and `## Implementation Plan`, so a resolution stated here is binding
where it is needed. Nothing below weakens, rewrites or excepts a criterion; each entry says which clause
it reifies and the reifications are asserted, not merely written.

- **(R1) AC-1(c2)'s guard-set EQUALITY is reified (round 3 note 1, round 4 note 3).** Read literally the
  clause cannot hold: the `-->`/`<!--` guard is HAL9000's own, so those probes sit on the capture's
  REFUSE side and cannot appear in "capture-ACCEPTED". The operative form, and the one the builder
  implements: **both sides are derived from the capture, and the right-hand side is the capture's
  `accept` probes FILTERED by this document's guard predicates** (§1.4, now FIVE of them — M1 added the
  fifth) — never a typed list. The
  assertion is `{p for p in accept_probes if library_refuses(p)} == {p for p in accept_probes if
  guarded(p)}`, with a non-vacuity assertion that the second set is non-empty. At the capture's HEAD that
  set has exactly FIVE members and the data-premise gate already named them (`text` containing `-->`,
  `text` containing `<!--`, and a discriminator that is empty, whitespace-only or `:`-bearing); five is
  recorded here as INFORMATIONAL and is never a pinned count, because a re-run capture may probe more
  boundary values and the filter is what makes the clause survive that.
  **The FILTER is what makes M1 free of a re-signature, and the point is worth being exact about since
  the two counts coincide.** The guard PREDICATE list grew from four to five; the filtered SET's
  membership did not move, because no probe the capture records as ACCEPTED carries a line matching
  `^#{2,3} ` — the only multi-line `text` probe is `'line one\n\nline two'`
  (`docs/wi-033-hal9000-timeline-entry-capture.md:413-418`), and that was read at its lines this round,
  not inherited from the threat model's narrative. So both sides of the equality hold exactly the same
  five probes after the fold as before it, AC-1(c2) stays green as SIGNED, and the builder registers the
  fifth predicate in the filter for REACH (a sixth guard added later against a capture that does probe
  the shape must show up on both sides, which a four-predicate filter would hide).
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
- **(R6) AC-3(c)'s `docs/vault-fixtures.md` clause is asserted POSITIVELY and SECTION-SCOPED, never as a
  whole-file absence pin (spec review 2026-09-29, finding 3).** The signed clause asks that the sentence at
  `docs/vault-fixtures.md:279` "is updated to name `manager:` alone". The earlier draft's oracle for it was
  the absence of the phrase `` `introduced_by:` `` from that whole file outside its `criteria` fences —
  which is the WI-278 failure shape twice over: it pins a LIVE population's shape over another item's
  6,200-line tracked document, and it would have been satisfied by DELETING the sentence outright. The
  operative form, which Task 7 implements: select that file's `## Exploration Notes` section by the same
  `select_sections` helper AC-1 uses over the capture (§12 Rule 1), then assert the CORRECTED sentence is
  PRESENT in it and the stale two-key phrase is ABSENT from that same selected text. This is strictly
  STRONGER than the absence pin (a deletion now fails it), it is narrower (the section, not the file), and
  it needs no rolled `criteria`-fence scan at all: WI-016's signed AC-5 fence at `:1434` lives under
  `## Acceptance Criteria`, a different section, so the heading selection excludes it STRUCTURALLY rather
  than by a predicate no leaf in this tree declares. Measured this round rather than assumed: the string
  `introduced_by` occurs in that file exactly TWICE — `:279` (inside `## Exploration Notes`, spanning
  `:83-1119`) and `:1434` (inside the signed fence). The one-line WI-278 coupling declaration rides with it
  in `## Verification`, beside AC-1's.
  **Two further reifications of the same clause, added 2026-09-29 after the spec review's round 2, and
  both are about the clause's ORACLE rather than its promise.** First, **both comparisons run over
  whitespace-NORMALIZED text** (`" ".join(s.split())` on the selected section and on each phrase alike),
  because `docs/vault-fixtures.md` hard-wraps and the corrected sentence spans `:279-280` — so a literal
  substring test would be RED against a correct conductor edit, in a file the builder cannot touch. §12
  Rule 2 states it as a rule over every phrase oracle in the item rather than as a patch to this one.
  Second, the signed clause PARAPHRASES the target sentence as "a `manager:` or `introduced_by:` key",
  and the file's actual bytes carry no "key": they read "a `manager:` or `introduced_by:` on a
  schema-drift or forward-compatibility note". The signed text names the right sentence and asks for the
  right change — `manager:` alone — and the OPERATIVE phrases are the file's own bytes, quoted verbatim
  in Task 7, in §6 and in the precondition fence. The paraphrase is carried in two further places and
  both are correctly left alone: AC-3's own signed `desc`, which may not be edited, and the data-premise
  gate's round record (`## Data Audit — 2026-09-28`, "does read …"), which is another gate's append-only
  section — its substance is right (the sentence exists and names both keys) and only its last word is a
  gloss. Neither reification weakens the criterion: one makes a
  correct edit pass that would otherwise fail, the other makes the test quote the file rather than the
  paraphrase.
- **(R7) AC-1(c2)'s equality is asserted over a population read WHOLE (threat model round 3, M2).** The
  clause and R1's reified form both quantify over "the capture's `accept` probes", and that set is
  DERIVED from a selected markdown span — so the promise is only as good as the selection. A partial
  truncation of `## Validation boundary` leaves the equality true over a SUBSET, which retires the
  anti-widening ratchet the clause exists to BE while the floor stays green; the non-vacuity assertions
  R1 already carries catch a TOTAL loss only. The operative form, which Task 3 implements and §12 Rule 3
  states as a rule over every selected span in the item: the probe span's COMPLETENESS is asserted first,
  by the whole-file `yaml`-fence accounting, before any probe is read. This adds no member to either side
  of the equality — it asserts that the population both sides are drawn FROM was read whole — so no
  re-signature is owed, exactly as M1's fifth predicate owed none (R1's own argument, one level out).

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
STRUCTURAL_LINE_PATTERN = re.compile(r"^#{2,3} ", re.MULTILINE)
```

`KIND_PATTERN` is HAL9000's, verbatim from the capture's part 1
(`KIND_PATTERN = re.compile(r"^[a-z][a-z0-9_-]{0,31}$")`) — the OPEN slug rule D8 rules as the write
door. `MARKER_PATTERN`'s shape is the capture's `render` output read back: `<!-- {key} -->` on its own
line, `(?P<discriminator>.+)` non-empty. `HEADING_PATTERN` is date-AGNOSTIC — it captures the date text
and never parses it, which is the whole of why the three legacy heading grammars (43 `Month D, YYYY` /
38 ISO-with-time / 5 bare ISO, `docs/wi-033-intro-corpus-baseline.md`) cost this item nothing.

`STRUCTURAL_LINE_PATTERN` has exactly TWO readers and they are deliberately the same constant: §1.4's
guard 5 (M1) on the write door, and `parse_entries`' body boundary on the read side (§1.3). Sharing it is
the point — the door refuses precisely the line the reader treats as a boundary, so the two cannot drift
apart, and the module gains no second grammar. Nothing else consults it: not `render`, not `dedupe_key`,
not `parse_markers`, not the accessor. Its bound is DERIVED rather than chosen, and the derivation is a
STRICT SUPERSET rather than an exact union — stated precisely because the earlier wording claimed the
union and that claim is false: `^#{2,3} ` COVERS every line-anchored markdown-heading pattern this item's
readers route on — `body_sections.py`'s section delimiter `^## (.+)$`
(`obsidian_schemas/body_sections.py:SECTION_HEADING_PATTERN:36`, read this round), this module's own
`HEADING_PATTERN` (`^### … [kind]`), and `parse_entries`' body boundary — and it additionally matches two
shapes NEITHER reader accepts: a title-less `## ` line (`^## (.+)$` needs a non-empty title) and a
kind-less `### ` line (`HEADING_PATTERN` needs a ` [kind]` suffix). **Those extra members are INERT and
their refusal is harmless**, and the property that matters is stated as the falsifiable one: every shape a
reader routes on IS refused (coverage, which is what closes the generator), and the two extra members cost
nothing because nobody may plausibly need a bare `## ` line inside an entry's prose. The complement is
declared with it, because a guard that refuses more than its readers route on is an over-refusal AC-1(c2)
would have to carry: `# ` and `#### ` match NONE of the three reader patterns AND none of
`^#{2,3} ` (`^## (.+)$` needs a space at offset 2, which `####` does not supply; `^#{2,3} ` likewise), so
neither truncates a span nor forges an entry, and neither is refused. The two inert extra members move
NEITHER side of AC-1(c2)'s equality, for the same reason guard 5 as a whole does not: no probe the capture
records as ACCEPTED carries a `^#{2,3} ` line at all (R1).

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

    @property
    def key(self) -> str:
        return _compose_key(self.kind, self.day, self.discriminator)   # §1.3

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
def _compose_key(kind: str, day: date, discriminator: str) -> str
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

**The key grammar is spelled in exactly ONE expression, `_compose_key`, and every other route to a key
delegates to it.** `_compose_key(kind, day, discriminator)` is `f"{kind}:{day:%Y-%m-%d}:{discriminator}"`,
discriminator VERBATIM (no slug, no case-fold — the capture's own rule, "or `Sören Winter` and
`Søren Winter` would collide"). `dedupe_key(entry)` is `_compose_key(entry.kind, entry.when.date(),
entry.discriminator)`, `None` when there is no discriminator. `Marker.key` (§1.2) is
`_compose_key(self.kind, self.day, self.discriminator)`. `dedupe_probe(entry)` is the delimited form
`f"<!-- {dedupe_key(entry)} -->"`, `None` when the key is.

Stating the single composer is not tidiness — it is what makes the one-definition promise LITERAL where
AC-2(e)'s scan cannot reach. The key format carries no `<!--`/`-->` delimiter, so a second spelling of
`{kind}:{day}:{disc}` at the door or in a test is outside AC-2(e)'s predicate by construction and NO check
in this item would catch it. `_compose_key` closes that gap by construction instead.

`dedupe_probe` is the ONE string the door's dedupe test compares, and §2 branch 2 says so in the same
terms: the door's test is `any(m.source == dedupe_probe(entry) for m in parse_markers(timeline))`, because
`Marker.source` is the verbatim `<!-- {key} -->` line the same `render` emits. A key that is passed can
therefore never fail to be the key that was embedded. `Marker.key` exists for the READING side — it is what
AC-1(b)'s "`dedupe_key(entry)` equals that marker's reconstructed key" asserts against, and because both
sides go through `_compose_key` the assertion tests the round trip rather than two copies of one grammar
agreeing.

`parse_markers` is a flat `MARKER_PATTERN.finditer` in DOCUMENT ORDER, which is newest-first for stored
entries (P3: `append_to_timeline` prepends). It yields a `Marker` only when the day slot parses through
`date.fromisoformat`; an impossible date (`2026-13-45`) is a marker the library does not recognise, and
it is REPORTED by the linter's `intro_by_without_marker` rather than raised on. That direction is
deliberate and is the one place this module departs from the package's loud-fail idiom: the write door
refuses loudly (§1.4), and a READER over arbitrary vault bytes must not let one bad note poison a whole
scan — `lint_vault` walks 5,664 files.

`parse_entries` is the heading-anchored reader the linter needs: `HEADING_PATTERN.finditer` for the
heading, the body running to the next line matching `STRUCTURAL_LINE_PATTERN` — the `^#{2,3} ` the
census itself used as its body definition, written once in §1.1 and shared with guard 5 so the
"one grammar" claim is literal rather than approximate — and
`marker` = the FIRST `Marker` that `parse_markers` returns over that body, or `None`. It calls
`parse_markers` rather than re-matching, so "well-formed" is ONE predicate in this module and
`intro_by_without_marker` reports exactly the entries the accessor cannot see. It exists so
`scripts/lint_vault.py` can ask "this heading's entry has no marker" without owning a grammar.

`Marker.source` is the regex match's own text — `m.group(0)`, the marker line WITHOUT its trailing
newline, since `$` is zero-width. Stated because AC-2 pins `source` byte-for-byte against "the marker
substring present in that note's own text".

#### §1.4 Validation — HAL9000's rules, plus exactly FIVE declared guards

Reproduced from HAL9000 (capture part 1), refusing on the same inputs:

| Field | Refused when |
| --- | --- |
| `kind` | not a `str`, or does not match `KIND_PATTERN` |
| `text` | not a `str`, or empty after `.strip()` |
| `discriminator` | not a `str` and not `None`; or contains `-->`, `<!--`, `\n` or `\r` |

The library's FIVE OWN guards — the complete set of inputs HAL9000 accepts and the library refuses, which
is the enumerated exception AC-1(c2) asserts as an equality (guard 5 is M1's, folded 2026-09-29; it adds
a PREDICATE to that filter and no MEMBER to either side of the equality, because no capture-accepted
probe carries the shape — see R1). **That equality is the ANTI-WIDENING RATCHET over this set, so its
probe population is asserted to have been read WHOLE — M2, folded 2026-09-29 (§12 Rule 3, §0 R7).** The
set equality holds over any SUBSET of the `accept` probes, so a probe span silently narrowed by a
truncating `## ` line would retire the ratchet with the floor green and let a sixth guard land one case at
a time; Task 3 therefore asserts the span's completeness by the capture's whole-file `yaml`-fence
accounting before it reads a probe. Guard BEHAVIOUR is pinned twice more, independently of the probe span
— AC-1(c) asserts each of the five raises with its named pattern, and Task 3's (c3) ships guard 5's reach
as fixtures — which is why a narrowed span would be a ratchet loss rather than a guard loss:

1. `text` contains `-->` — it would terminate the comment the entry's own marker opens.
2. `text` contains `<!--` — it would forge a second marker through the prose channel, which is the one
   place a text channel can corrupt a machine channel.
3. `discriminator` is empty or whitespace-only — the rendered marker would either be unreadable by
   `MARKER_PATTERN` (empty) or would key every same-kind, same-day entry onto a blank counterparty
   (whitespace). Either way the entry the door writes is one the accessor cannot honestly answer from.
4. `discriminator` contains `:` — the key separator. `parse_markers` still READS such a marker off disk
   (the pattern takes the rest of the line), so nothing on disk becomes invisible; what is refused is
   MINTING a new key that a consumer splitting on `:` reads as a different kind/day/counterparty triple.
5. **`text` contains a line matching `STRUCTURAL_LINE_PATTERN` (`^#{2,3} `) — a markdown heading in the
   prose channel truncates or shadows the `## Timeline` span that the accessor (§3), the marker-anchored
   dedupe (§2 branch 2) and both new detectors (§5) all read through, so it would silently hide every
   older entry on that note from all three.** The line may be the text's first (the render puts it
   immediately after the heading) or follow any `\n` inside it, so the test is the MULTILINE pattern over
   the whole string and never `text.startswith`. This is M1, and it is the same rule as guards 1 and 2
   applied to the second machine channel: §1.4's own rationale is that the machine channel must not be
   writable from the prose channel, and the section heading is a machine channel this item newly depends
   on. Two effects, both silent rather than loud, are what make it a refusal: an injected `## Anything`
   TERMINATES the span, and an injected duplicate `## Timeline` SHADOWS it, since `parse_body_sections`
   keys an `OrderedDict` by heading text; an injected `### {date} [{kind}]` re-attributes a marker to a
   forged entry in `parse_entries` and suppresses the `intro_by_without_marker` report that is the
   accessor's honesty invariant.

**The rule total behind guard 5, and the sweep of the next level, DECLARED (WI-226).** Guard 5 is not
"the heading case" — closing one line grammar would leave the next one as the next round's finding. The
GENERATOR is: *a line-anchored structural pattern this item's readers route on, writable from the prose
channel because `render` places `text` verbatim on its own lines inside the note body.* Enumerated at
source, the surface is closed by the guard set rather than case by case:

- **Members — every line-anchored pattern in play, and the guard that owns each.** The marker line
  (`MARKER_PATTERN`) is owned by guards 1–2, which are SUBSTRING-wide and therefore strictly stronger
  than a line-anchored test. The section delimiter (`^## (.+)$`) and the entry heading (`^### … [kind]`)
  are owned by guard 5, whose pattern is their union (§1.1). There is no third grammar: `parse_markers`,
  `parse_entries` and `get_section` are the only readers this item builds or newly depends on, and §1.1
  declares every pattern they use.
- **Next level — the FIELD dimension: which inputs can introduce a line at all.** Swept rather than
  assumed, and the answer is exactly one. `text` is rendered verbatim and is the only multi-line field.
  `kind` cannot: `KIND_PATTERN` admits `[a-z0-9_-]` only, so no `#`, no space, no newline. `discriminator`
  cannot: HAL9000's own rule refuses `\n` and `\r`, so it can never open a line, and it renders INSIDE
  the marker line where a `## ` is inert. `when` is a `datetime` rendered through `strftime`. So the
  write door is TOTAL over this generator once `text` is guarded — that is the claim, and it is the one
  Task 3 makes falsifiable rather than merely stated.
- **Next level again — the READ side, declared as an accepted residual rather than closed.** A note that
  ALREADY carries such a line (hand-edited in Obsidian, or written through the raw-string branch AC-1(f)
  deliberately preserves) is outside any write guard, and the readers must stay total and non-raising
  (§1.3) rather than grow a repair. The exposure is MEASURED at zero, not argued: precondition 2 reports
  every timeline heading in the live vault sitting inside a `## Timeline` section, and that predicate is
  re-runnable. `intro_by_without_marker` is the standing instrument if it ever stops being zero.

The guard is on CONSTRUCTION only. Stating that split matters: the library is stricter than HAL9000 at
the write door and exactly as permissive as the census at the read door.

Refusals raise `TimelineEntryRefusal`, a new leaf of `LoudFailError` added to
`obsidian_schemas/errors.py` beside `NameGateRefusal` (`errors.py:NameGateRefusal:106`), declaring no
`__init__` — the hierarchy's one constructor is what bounds the message — and carrying a `pattern`
attribute set AFTER construction, exactly as `NameGateRefusal.pattern` is. It needs ONE new member in
`errors.py:REASONS:152`, because `bounded_message` refuses any reason that is not an enumerated literal
(`errors.py:bounded_message:177-188`): `"a timeline entry field this package refuses"`. That ONE member
covers guard 5 as well — the reason is per-DOOR, not per-guard, and `pattern` is what distinguishes the
faults. The refusal
`pattern` values are module-level literals in `timeline_entry.py` — `KIND_PATTERN_KEY = "kind_not_a_slug"`,
`TEXT_EMPTY_KEY`, `TEXT_FORGERY_KEY`, `TEXT_STRUCTURAL_LINE_KEY` (guard 5), `DISCRIMINATOR_TYPE_KEY`,
`DISCRIMINATOR_FORGERY_KEY`,
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
   MARKER-ANCHORED and compares exactly ONE string, `probe`: inside the lock, read the note, split the
   fence (`person.py:_split_frontmatter_fence:96`), take `get_section(body, "Timeline")`, and skip iff
   `any(m.source == probe for m in parse_markers(timeline))` — `Marker.source` being the verbatim
   `<!-- {key} -->` line the same `render` emits (§1.3), so `probe` is live in the flow and is the only
   comparand. Written this way rather than as a `Marker.key == dedupe_key(entry)` comparison because
   `dedupe_probe` is §1.3's declared door string and a second comparand here is the disagreement this
   branch exists to remove; the two forms are equivalent by construction, since both compose through
   `_compose_key`. Not a
   substring test at all: a `## Notes` line quoting the key verbatim is outside the span, and a quoted
   key inside the span that is not a well-formed marker line does not match. A `None` key — an entry with
   no discriminator — means NO DEDUPE (the capture's own rule: a free-text note has no event identity, and
   inventing one would suppress a second, genuinely intended note), so AC-1(d)'s "the same entry twice
   writes once" is about a DISCRIMINATOR-BEARING entry and two identical `note` entries legitimately write
   twice. `get_section` is `parse_body_sections` one frame in
   (`obsidian_schemas/body_sections.py:get_section:137`), which is what AC-1(e)'s span wording and
   AC-2(a2)'s `parse_body_sections` wording both name.
3. **A `str`** — byte-for-byte today's behaviour, INCLUDING the whole-file substring dedupe at
   `person.py:1502`. **§1.4's guards, guard 5 (M1) included, are on `TimelineEntry` CONSTRUCTION, so
   this branch is unguarded by design and not by omission:** it takes a string nobody typed, exactly as
   it does today, and narrowing it would change six live callers AC-1(f) exists to leave alone. The
   residual is the modeler's own first non-blocking note and is measured at zero (precondition 2: every
   live timeline heading sits inside a `## Timeline` section); `intro_by_without_marker` is what would
   make it visible. That looseness is load-bearing for a live caller: precondition 3's cross-repo
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
timeline detectors call `parse_entries(get_section(vf.body, "Timeline") or "")` — and **`get_section` is
ONE NAME ADDED to the `from obsidian_schemas.body_sections import (...)` list the script already carries
at `lint_vault.py:38-43`**, which today imports `ENTITY_BODY_CONFIG`, `ensure_sections_exist`,
`get_expected_sections` and `parse_body_sections` but not `get_section` (read this round). Said explicitly
because the alternative spelling `parse_body_sections(vf.body).get("Timeline")` would work identically and
a builder guessing between them is a builder guessing; the import is chosen so §2, §3 and §5 all reach the
span through the same one call. The script defines NO
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

**`docs/vault-fixtures.md:279` is a CONDUCTOR-COMMITTED PRECONDITION, not a builder write.** The file's
bytes at `:279-280` read "a `manager:` or `introduced_by:` on a schema-drift or forward-compatibility
note" — quoted from the file rather than from AC-3(c)'s paraphrase, which renders it "a `manager:` or
`introduced_by:` key"; there is no "key" in the sentence, and the test quotes the bytes (§0 R6). It must
read `manager:` alone, i.e. the substring `` or `introduced_by:` `` is deleted and nothing else moves
(AC-3(c)). That file is ANOTHER item's tracked work-item document (WI-016, `id: WI-016`
in its frontmatter), and since WI-245 the merge boundary admits a declared cross-doc edit only when it is
**additive prose outside every fence**. This edit REPLACES prose, so a caged builder's write to it is
refused at the merge boundary — the failure WI-245 says costs a conductor hand-landing plus a relaunch.
Declared instead as a fifth `kind: precondition` fence in `## Write Targets`. Two things make that safe
rather than a hope: the same sentence is also inside WI-016's SIGNED AC-5 fence at `:1434`, which is
**not** in scope and must not be touched (moving a typed parse of another item's doc is exactly what the
merge rule forbids, and it is another item's signed criterion); and the PRE-DRIVE floor check (WI-156 /
WI-164) is clean — no test in this tree reads `:279`'s prose TODAY, so the doc edit participates in no
bijection or symmetry invariant and needs no atomic landing with the builder's re-key. AC-3(c)'s own
check is what makes the edit verifiable at all, since a precondition probe reads presence and the file is
already in HEAD.

**And that check's ORACLE is a positive, section-scoped, WRAP-INSENSITIVE read — never a whole-file
absence pin and never a literal substring test (§0 R6, §12).** Task 7 selects this file's
`## Exploration Notes` section (which spans `:83-1119` and holds `:279`) with the same
`select_sections` helper Task 3 writes, NORMALIZES the selected text and each phrase through
`" ".join(s.split())`, then asserts inside that section only: the corrected phrase PRESENT, the stale
two-key phrase ABSENT. The normalization is what makes the PRESENT half executable at all — the file
hard-wraps and the corrected sentence spans `:279-280`, so the phrase contains a newline in the file no
matter how the paragraph is filled, and re-wrapping is deliberately NOT asked of the conductor (§12 Rule
2). Three further properties make this the right arm and each is measured rather than argued. It is STRONGER: an absence pin passes when the sentence is deleted
outright, which is the opposite of what AC-3(c) asks for. It is NARROWER: `introduced_by` occurs in that
file exactly twice — `:279` and `:1434` — and `:1434` sits under `## Acceptance Criteria`, so the heading
selection excludes WI-016's signed fence STRUCTURALLY and the test rolls no `criteria`-fence scan, a
predicate no leaf in this tree declares. And it is DURABLE against the machine that mutates this corpus:
the archive-split leaf rewrites gate-ROUND sections (`docs/vault-fixtures.md:3761` declares the drawer),
not `## Exploration Notes`, so somebody else's correct ship no longer reddens this item. The one-line
WI-278 coupling declaration lives in `## Verification` beside AC-1's.

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
   total over the three fields (§1.4) AND over the one generator by which the prose channel could write
   a machine channel — the marker delimiters (guards 1–2) and the heading line (guard 5, M1), `text`
   being the only field that can introduce a line at all. Nothing is interpolated into a shell, a query
   or an error message.
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
measured on 2026-09-28, RE-RUN and grown by three rows on 2026-09-29, and never a total** — the 09-29
rows (`REASONS`' size pin, `__all__`'s membership pins, and the two walls that already sweep
`tests/test_name_gate.py`) are the proof of the sentence that follows, since each was reachable by the
09-28 derivation and none was named: this derivation has under-reached at its reading step every
time it has been run in this factory, which is why Task 11 RUNS each predicate on the files' FINAL text
rather than reasoning about which shapes match, and why anything the run returns that this table does not
name is NAMED in the Build Log and satisfied, never worked around and never satisfied by narrowing the
wall.

| Wall (its own shipped predicate) | What it requires of this item's files |
| --- | --- |
| `modules_using_ast` == `{"tests/derivations.py"}` — asserted from `tests/test_fixture_vault.py:1383`, `test_name_gate_wall.py:1136`, `test_lint_vault_fix_rules.py:1957`, `test_loud_fail_harness.py:103` | NO new file may import or use `ast`. All FOUR additions to `tests/derivations.py` live there — `gate_call_sites` (Task 6), `marker_grammar_sites` (Task 10), and `select_sections` + `select_fenced_blocks` (Task 3, neither of which touches `ast` at all and so cannot move this equality either way); the new test modules call them and never parse source themselves. |
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
| **`tests/test_name_gate.py:124` — `assert len(REASONS) == 16`, an EQUALITY pin over `obsidian_schemas/errors.py:REASONS:152`, declared deliberate by its own comment at `:121-122` ("REASONS is a FROZEN population, so equality is the right pin"). The module imports `REASONS` from `obsidian_schemas.errors` directly (`tests/test_name_gate.py:24-25`), so the pin sits in a check — `test_name_gate_refusal_is_a_loud_fail_leaf_carrying_a_pattern:109` — that never calls the declaring symbol.** | Task 2 adds ONE member to `REASONS`, so this pin MOVES to `17` IN THE SAME TASK — together with the two numbers in its own comment at `:121-122` ("fifteen … sixteen" → "sixteen … seventeen"), which is inside the bounded edit rather than beside it, since a comment that outlives its assertion is the next reader's wrong premise — and `TimelineEntryRefusal`'s own leaf assertions land beside `NameGateRefusal`'s in that check. `tests/test_name_gate.py` is a declared `## Write Targets` path for exactly this obligation — this is WI-202's founding shape (a pin in a file the sweep reached, in a function that never names the declaring symbol), and the whole point of naming it here is that the floor otherwise finds it at the LAST task with nothing owning the edit. |
| `tests/test_name_gate.py:156` — `"NameGateRefusal" in obsidian_schemas.__all__`, over `obsidian_schemas/__init__.py` | MEMBERSHIP, not size: no pin anywhere counts `__all__`'s length (swept below), so Task 2's additions to `__all__` move NOTHING and this row needs naming but no edit. |
| **The two walls that already SWEEP `tests/test_name_gate.py`, now that Task 2 edits it.** Found by the same derivation, keyed on the act rather than on a declaring symbol: `tests/test_name_gate_wall.py:TOUCHED_TEST_FILES:1029` names it at `:1033` and feeds `_check_the_ast_capability_stays_single_homed` inside `test_wall_membership_is_closed_by_running_each_walls_predicate:1057`; `tests/test_fixture_vault.py:_item_test_modules:1315` names it at `:1323` and feeds `test_the_fixture_vault_files_close_their_wall_memberships_by_running_each_predicate:1353`, which RUNS `modules_using_ast`, `check_module`, `NO_ARG_CONSTRUCTION` / `_scanned_markdown_files` and the declared pytest `python_files` globs over it. | FOUR requirements of Task 2's edit, all satisfiable and each stated so Task 11's RUN can falsify it: (1) the edit must name no `ast` capability — `modules_using_ast` is a set EQUALITY whose universe these lists grow, and a new member would redden it; (2) it must add NO new top-level `def test_` — `check_module` is a `def <name>(` SUBSTRING scan that raises on anything but exactly one match tree-wide, so the new assertions go INSIDE `test_name_gate_refusal_is_a_loud_fail_leaf_carrying_a_pattern:109` rather than into a sibling check; (3) it must construct no repository with no argument (`NO_ARG_CONSTRUCTION`); (4) the file keeps its `test_*.py` name, so the collection globs are unmoved. Note what these two lists are NOT: they are the FROZEN touched-file lists of WI-021 and WI-016 respectively, so this item joins neither — it inherits their predicates' verdicts over a file they already grade. |

**The conscious-pin sweep (WI-229).** THREE countable corpora, not two — the earlier draft named only the
first two and finding 1 of the 2026-09-29 spec review is what the omission cost:

1. **The lint check-id set.** Declaring symbols `tests/derivations.py:auto_fixable_emitter_checks`,
   `auto_fixable_branch_checks`, `scripts/lint_vault.py:CATEGORY_ORDER`. Reading every file those reach at
   FILE granularity returns `test_lint_vault_fix_rules.py:822`'s `len(pinned) == 7` and
   `:1703-1708,1775`'s `CENSUS_SHAPE_TO_RULE` / baseline rows — both rows above.
2. **The frozen fixture corpus.** Declaring symbols `tests/fixture_vault.py:NOTES` / `CORPUS_DIGEST`.
   FILE-granularity reading returns `CORPUS_DIGEST` itself AND
   `tests/test_lint_vault_fix_rules.py:CORPUS_PINNED_ISSUES:809` — a hardcoded per-note issue-COUNT pin
   whose own comment at `:802-808` binds it explicitly to `CORPUS_DIGEST` ("The figure is a property of
   bytes pinned by CORPUS_DIGEST, so it moves only when that digest does"). Task 7 moves that digest, so the
   pin is IN the sweep's reach and is named here rather than left to the floor. Read: the re-key changes no
   `meeting_missing_from_timeline` count on any of its five notes, so it is UNMOVED and needs no edit —
   which is what makes clause (2)'s predicate below checkable rather than merely asserted.
3. **`obsidian_schemas/errors.py:REASONS:152`, the enumerated-reason set.** Declaring symbol `REASONS`
   itself; Task 2 adds one member because `bounded_message` refuses any non-enumerated reason
   (`errors.py:bounded_message:177-188`). Swept by grepping the declaring symbol over the whole tree and
   then reading every file it reaches at FILE granularity: the ONLY size pin is
   `tests/test_name_gate.py:124`, and the only other references are the membership assertion at `:123`
   (unmoved — it names a different literal), `bounded_message`'s own guard, and four prose mentions in
   `errors.py`, `vault_io.py:97` and `name_gate.py:70`/`:174` that count nothing. No derived population of
   `LoudFailError` leaves exists anywhere in `tests/` (checked: the only `issubclass(..., LoudFailError)` is
   `test_name_gate.py:114`, and the one source-derived class sweep, `test_loud_fail_load.py:97-101`, is over
   `base_repository_subclasses` and not over error leaves), so the new leaf joins no counted set.
4. **`obsidian_schemas/__init__.py:__all__`** is swept for completeness and is NOT a counted corpus: the
   only assertions over it are membership (`tests/test_name_gate.py:156`; `tests/test_fixture_vault.py:905`,
   `:913` are over `repositories.__all__`, a different object). Task 2's additions move nothing.

The obligations are stated as predicates and never as numbers: **the auto-fixable rule set does not
change; the digest changes exactly once and every pin bound to it is re-read; and the enumerated-reason set
grows by exactly one, with every pin over it moving with it in the same task.**

### §10 — Pattern consistency

Every piece has a model in this tree: the leaf module's import discipline is `name_gate.py:14-20`; the
refusal leaf and its pattern literal are `NameGateRefusal` + `WHATSAPP_PATTERN`; the report-only detector
is `whatsapp_not_storable` (`lint_vault.py:475-503`); the gate arm's placement argument is `3b`'s own;
the accessor's note resolution is `append_to_timeline:1489-1493`; the new check modules' shape — the
interpreter shim first, one `def test_*` calling `_check_*` helpers, the containment wall defined first
where the module drives the linter — is `tests/test_stem_name_divergence_detector.py`; the capture-parsing
test's shape is `tests/test_lint_vault_fix_rules.py:baseline_sections:1518` for its RAISING DISCIPLINE
ONLY — a selector that finds nothing is RED, never an empty dict — and NOT as a function to transplant,
because it is a TOTAL parse of `docs/lint-vault-live-baseline.md`'s five declared headings that raises on
any heading outside its table, which the capture carries three of (§12 Rule 1 states the contract this
item's own `select_sections` implements instead); plus
`tests/test_lint_vault_fix_rules.py:fenced_blocks:1550` (the triple-backtick blocks of one section, in
order), whose SHAPE is copied with one declared deviation — the info string is RETAINED, because that
function discards it at `:1554-1559` and both the `yaml`-only filter and §12 Rule 3's accounting need it.
Both are corrected from the earlier `:113`, which is only that
module's `BASELINE` path constant and gives a builder nothing to model. And the two new `docs/**` readers' coupling
declarations follow the shipped `CORPUS_COUPLING:` docstring convention at module granularity
(`tests/test_fixture_vault.py:3`) and at check granularity
(`tests/test_lint_vault_fix_rules.py:1639`). The one deviation from a shipped pattern is §1.3's
non-raising reader, justified there.

### §11 — Mechanics a builder would otherwise have to guess

Four, each with the shipped thing to copy rather than a description:

1. **Parsing the capture.** Select the section by its declared `## ` heading through this item's own
   `select_sections` helper (§12 Rule 1, whose contract is written out in full there and in Task 3), take
   every fenced block whose info string is `yaml` inside that section, and `yaml.safe_load` each one — the
   capture was produced with `yaml.safe_dump`, so the round trip is exact and the `rendered` block
   scalar's single trailing newline is the renderer's own. `yaml` is importable because the interpreter
   shim re-execs under the project interpreter (§8.3); under the conveyor's bare `-S` interpreter it is
   not, which is the whole reason the shim is the module's first statement. Shapes to copy, by SYMBOL,
   and what each is copied FOR — the distinction is load-bearing:
   `tests/test_lint_vault_fix_rules.py:baseline_sections:1518` supplies the RAISING DISCIPLINE (a
   selector that finds nothing is RED, never an empty dict) and is NOT transplanted, because it is a
   total parse that raises `unnumbered section heading` on any `## ` line outside its own declared table
   and the capture carries three such lines (`## Part 1` at `:57` and at `:587`, `## Appendix` at
   `:470`); `tests/test_lint_vault_fix_rules.py:fenced_blocks:1550` returns one section's fenced blocks
   in order and is the SHAPE copied, into `tests/derivations.py` as `select_fenced_blocks(section_text)`
   beside `select_sections`, so Tasks 3 and 7 share one copy and the shipped helper is not re-homed (§12
   says why that second spelling is accepted rather than removed) — **with the one deviation §12 states:
   the INFO STRING IS RETAINED**, because `fenced_blocks` discards it (the opening line is consumed by the
   triple-backtick branch at `:1554-1559` and never appended), so a copy taken as written could not
   satisfy the "whose info string is `yaml`" filter this very bullet asks for, nor express Rule 3's
   whole-file accounting. The helper returns `(info, block)` pairs and consumers filter on
   `info == "yaml"`. (Not `:113`: that is the module's
   `BASELINE` path constant, and a builder who opens it finds a `Path` binding.)
2. **Planting source files for the two WI-235 batteries.** `tests/support.py:temp_dir` for the scratch
   root, plus a four-line local `_plant_source(root, name, source)` that writes `root/name` and returns
   the path — the shape `tests/test_lint_vault_fix_rules.py:_plant_source:586` already carries (read at
   its symbol this round; the `:352` this document previously carried was a CALL SITE, not the def). The
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

### §12 — Every textual oracle over a committed markdown file: its contract in its own terms, and the bytes it was measured against

Written 2026-09-29 after the spec review's ROUND 2. Both of that round's findings were one class and the
reviewer said so; this section closes the class rather than the two instances (WI-226).

**THE GENERATOR, named at source.** *A check this plan orders derives a TEXTUAL oracle from a markdown
file the conductor commits and the caged builder cannot edit, and the oracle is stated BY REFERENCE — to
a shipped symbol, or to a phrase quoted from the sentence's sense rather than from the file's bytes —
without anyone having read the target at the GRANULARITY the oracle actually consumes.* Both findings
arrived exactly that way: Task 3 named `tests/test_lint_vault_fix_rules.py:baseline_sections:1518` as the
selector without reading what that TOTAL parse does to a file carrying undeclared headings, and Task 7
named a phrase without reading that the file is hard-wrapped and the sentence spans a line break. The
damage shape is the same in both and is worse than an ordinary RED: **the two halves sit on opposite
sides of the cage.** The builder owns the assertion and cannot touch the file; the conductor owns the
file and was never told which of its incidental properties — a wrap column, an extra heading — were
load-bearing. So the surface is enumerated and closed with three rules that are TOTAL over it, and the
incidental properties are named as NOT load-bearing in writing. (Rules 1 and 2 close the two findings that
named the generator; **Rule 3 closes the FAIL-DIRECTION dimension the first sweep of this section's next
level did not turn** — the threat model's round-3 finding, M2, which landed inside this section's own
material and is the reason this list is three rules rather than two.)

**MEMBERS — the whole surface, enumerated by predicate rather than recalled.** Predicate: *a check this
plan orders that opens a `docs/**` file at run time and derives an oracle from its text.* It returns
FOUR oracles over THREE files:

| # | Task / clause | File | What the oracle consumes |
| --- | --- | --- | --- |
| 1 | Task 3 — AC-1(a), (a2), (b), (c2) | `docs/wi-033-hal9000-timeline-entry-capture.md` | the `yaml` fences of `## Parity samples` and of `## Validation boundary` |
| 2 | Task 3 — AC-1(a3) | the same file | the 40-hex HEAD the capture declares |
| 3 | Task 7 — AC-3(c), doc clause | `docs/vault-fixtures.md` | one phrase PRESENT and one phrase ABSENT inside `## Exploration Notes` |
| 4 | Task 7 — AC-3(c), live-half clause | `docs/wi-033-intro-corpus-baseline.md` | `introduced_by_frontmatter_carriers` from the `## Counts` section's one `yaml` fence |

Row 4 is what the sweep ADDED: AC-3(c) says the live half is "the committed count … read by the test as
a premise rather than re-measured", which is a machine read of a committed markdown file and therefore a
member of this exact class, and no earlier draft treated it as one. It is stated here so it takes the
same three rules as the other three rather than being invented at build time.

**RULE 1 — THE SECTION SELECTOR IS SPELLED IN ITS OWN TERMS, AND `baseline_sections` IS A DISCIPLINE TO
COPY, NEVER A FUNCTION TO TRANSPLANT.** ONE helper, written once in `tests/derivations.py` (Task 3) and
IMPORTED by the other reader (Task 7) — the tree's shared home for test-side derivations, chosen so this
item does not spell a markdown selector twice, which is the duplication this section exists to prevent.
Its contract:

> `select_sections(text, names) -> dict[str, str]`. For each NAME in `names`, find the lines of `text`
> for which `line.rstrip() == name` — an exact, line-start, whole-line match. RAISE if a name matches
> ZERO lines or MORE THAN ONE. A section's text runs from the line after its heading to the line before
> the next line whose `line.startswith("## ")` is true, **whatever that heading is** — or to end of file.
> Every `## ` line the `names` list does not mention is IGNORED as a selection candidate and HONOURED as
> a boundary.

Three things are true of that contract and each was measured this round rather than assumed:

- **A total parse RAISES on the capture, so the transplant reading is unbuildable.** `baseline_sections`
  walks every `line.startswith("## ")` and raises `unnumbered section heading` for any heading outside
  its declared `BASELINE_HEADINGS` table (`tests/test_lint_vault_fix_rules.py:1528-1536`) and
  `duplicate section ordinal` on a repeat (`:1537-1538`). It is correct for
  `docs/lint-vault-live-baseline.md`, a five-section machine artifact whose every heading is declared.
  The capture is not that shape: its line-start `## ` headings are
  `## Part 1 — source (verbatim, with line ranges)` (`:57`), `## Parity samples` (`:223`),
  `## Validation boundary` (`:290`), `## Appendix — the generator, verbatim` (`:470`), and
  **`## Part 1 — source (verbatim, with line ranges)` a SECOND time at `:587`** — that one at line start
  INSIDE the Appendix's `python` fence, where the generator's own triple-quoted literal emits the
  heading. A faithful copy of `baseline_sections` therefore sees four unmatched headings and one
  duplicate and raises before it reaches a single `yaml` fence. What is worth copying from it is the
  RAISING DISCIPLINE — a selector that finds nothing is RED, never an empty dict — which Rule 1 carries.
- **The two NAMED headings are each unique at line start, so the narrow reading is total over what it
  needs.** Measured: `^## Parity samples$` occurs once (`:223`) and `^## Validation boundary$` once
  (`:290`). `## Exploration Notes` occurs once in `docs/vault-fixtures.md` (`:83`) and `## Counts` once
  in `docs/wi-033-intro-corpus-baseline.md` (`:56`). The duplicate the file DOES carry is on a heading
  no `names` list mentions, which is precisely the case Rule 1 ignores.
- **The spans are exact, because no line-start `## ` sits inside any span this item selects.** Measured
  per file: in the capture, the next line-start `## ` after `:223` is `:290` and after `:290` is `:470`,
  so the two selected spans are `:224-289` and `:291-469` and neither contains a `## ` line at all — every
  rendered entry heading inside them is `### `, which `startswith("## ")` does not match (it requires a
  space at offset 2). In `docs/vault-fixtures.md` the next line-start `## ` after `:83` is `## Approach`
  at `:1120`, so the selected span is `:84-1119` and holds `:279`. In
  `docs/wi-033-intro-corpus-baseline.md` the next after `:56` is `## Verbatim output` at `:117`, so the
  span is `:57-116` and holds exactly one fenced block, the `yaml` one at `:61-115`.
  **Rule 1 is deliberately fence-UNAWARE**, exactly as the tree's one shipped section selector
  (`baseline_sections`) is, and the residual that buys is DECLARED rather than hidden: a line-start `## `
  introduced inside a fence anywhere in a selected span would truncate that span early. **What that
  truncation DOES is Rule 3's subject, and it is NOT uniform across the spans** — the earlier draft of
  this bullet said such a line "would redden this item", which is true of three of the four selected
  spans and FALSE of the probe span, where a PARTIAL truncation leaves AC-1(c2)'s set equality satisfied
  over a subset of the `accept` probes (the threat model's round-3 finding, M2; dimension (vii) below
  answers it per span). The measurements above are what say there is no such line today, they
  ride in the coupling declarations in `## Verification`, and a fence-aware boundary is deliberately not
  built — it would be a second markdown grammar this tree does not have, for a case measured at zero
  across all three files and all four selected spans. Rule 3 is what makes the residual's realization
  LOUD rather than resting on that measurement alone.

Fence extraction inside a selected span is `fenced_blocks:1550`'s own shape — toggle on any line whose
`startswith("```")` is true, blocks in order — which is safe on all three spans for the same measured
reason: the `rendered` and `value` block scalars are indented two spaces, so no line inside a fence
begins a fence (measured over `## Parity samples`' six fences and `## Validation boundary`'s probes). The
`yaml` blocks are then `yaml.safe_load`ed; the capture was produced with `yaml.safe_dump`, so the round
trip is exact.
**ONE deviation from a verbatim copy, and it is load-bearing: the INFO STRING IS RETAINED.**
`fenced_blocks:1550` DISCARDS it — the opening fence line is consumed by the triple-backtick
`startswith` branch at `:1554-1559` and never appended to the block — so a copy taken as written cannot
tell a `yaml` fence from a `python` one, while §11.1 and Task 3 both ask for "every fenced block whose
info string is `yaml`" and Rule 3's whole-file leg cannot be expressed without it. So the helper returns
`(info, block)` PAIRS — `select_fenced_blocks(section_text) -> list[tuple[str, str]]`, `info` being the
opening fence line with its leading backticks and surrounding whitespace stripped (`""` for a fence
opened with no info string) — and every consumer filters on `info == "yaml"`. That discard was read in
the shipped function's own control flow this round rather than inherited from any account of it.
It rides in `tests/derivations.py` beside `select_sections`, as `select_fenced_blocks(section_text)`,
for the same reason the selector does: TWO readers need it (Tasks 3 and 7) and neither may spell it
twice. The SHIPPED `fenced_blocks:1550` stays exactly where it is and is not re-homed — it is
`tests/test_lint_vault_fix_rules.py`'s own private helper, and moving another item's module member is
work this item has no reason to do. So there are two spellings of a four-line fence walk in the tree
after this item and that is DECLARED rather than glossed: the alternative is editing a module Task 9
only appends to, and §12's one-definition argument is about the oracles THIS item ships, not a
tree-wide de-duplication it was not asked for.

**RULE 2 — EVERY PHRASE ORACLE COMPARES WHITESPACE-NORMALIZED TEXT AGAINST A WHITESPACE-NORMALIZED
PHRASE, SO NO ASSERTION DEPENDS ON A WRAP COLUMN.** Both sides go through `" ".join(s.split())` before
the containment test — the selected section's text and the phrase alike. This is not a convenience; it
is what makes the oracle STATEABLE at all. `docs/vault-fixtures.md` hard-wraps at ~100 columns and the
sentence AC-3(c) is about spans `:279-280`:

    carry frontmatter keys no model declares — a `manager:` or `introduced_by:` on a schema-drift or
    forward-compatibility note — which every enumeration over DECLARED fields misses by construction;

(an indented block, so the two lines above are the file's bytes and not this document's wrapping.)
After the conductor's one-sentence edit (delete `` or `introduced_by:` `` and nothing else), the phrase
`` a `manager:` on a schema-drift or forward-compatibility note `` still CONTAINS THE NEWLINE — it ends
`:279` at "or" and resumes `:280` at "forward-compatibility" — so a literal substring test is RED against
a correct edit. Re-wrapping to the file's own fill moves the break to a different word; it does not
remove it. The only wrapping under which a literal test passes is a deliberate line JOIN nothing asks the
conductor to perform. Normalizing both sides removes the dependency by construction, and it is stated as
a RULE rather than a patch to one assertion because the ABSENCE half is contiguous on `:279` TODAY — the
defect is one-sided, which is exactly what hid it, and the next phrase anyone adds inherits the fix.

**And the incidental properties are declared NOT load-bearing, in the place the conductor reads.** The
precondition fence for `docs/vault-fixtures.md` in `## Write Targets` says it in its own terms: the edit
is a deletion of `` or `introduced_by:` `` on `:279` and nothing else, the conductor is NOT obliged to
re-wrap, re-flow or preserve any column, and no assertion in this item depends on where the line breaks
fall. Same for the capture: nothing here pins its heading count, its wrap, its probe count or the position
of any section. What it DOES require of the capture is two structural properties, stated so a conductor
regenerating it at the cutover is not left to discover them — the two named headings exist exactly once
each at line start, and **every `yaml` fence in the file sits inside one of those two sections** (Rule 3's
accounting is that sum). A regenerated capture may hold any number of samples and probes; it may not park
a `yaml` fence in a third section, and its Appendix's `python` fence may not contain a line-start
triple-backtick.

**RULE 3 — A SELECTED SPAN'S COMPLETENESS IS ASSERTED, NOT ASSUMED, WHEREVER A TRUNCATED SELECTION WOULD
LEAVE AN ASSERTION GREEN OVER A NARROWED POPULATION (the threat model's round-3 finding, M2).** Rule 1
declares fence-unawareness as a measured residual; Rule 3 is what makes that residual's realization LOUD.
Stated over the whole member set rather than over the one span that failed it:
*every oracle this item derives from a selected span either FAILS on a truncation of that span by construction — and this document names the assertion that does it — or carries an explicit completeness assertion, and for the capture's two spans the completeness assertion is the whole-file accounting: the number of `yaml`-info fences `select_fenced_blocks` returns over `## Parity samples` PLUS the number it returns over `## Validation boundary` EQUALS the number it returns over the whole file's text, with all three counts asserted non-zero.*

Why that expression and not another — each property counted against the capture's own bytes this round
rather than taken from the finding's narrative. It is **position-free** and **count-pin-free**: no literal
is typed, so it says nothing about where the two sections sit or how many probes they hold. It **moves
with a re-run capture**, which D7 has already scheduled as HAL9000 WI-082's first act — both sides grow
together when the regenerated capture probes more boundary values, which is precisely why R1 refuses a
pinned probe count. And it is **RED on a truncation of EITHER span whether the truncating `## ` line sits
inside a fence or outside one**: an injected `## ` line is not a fence line, so the whole-file count is
unmoved while the truncated span's count drops. Counted at source: the capture's line-start `yaml` fences
are SIX inside `## Parity samples` (`:225`, `:236`, `:247`, `:258`, `:269`, `:279`) and TWENTY-NINE inside
`## Validation boundary` (`:292` through `:462`), thirty-five in the file and none anywhere else — Part
1's three fences (`:61`, `:173`, `:181`) and the Appendix's one (`:474`, closed at `:603`, with the
`## Part 1` echo at `:587` inside it) are `python`. So the accounting is exact today, and the one further
measurement the whole-file leg needs is also true today: no line-start triple-backtick sits inside any
fence in the file, so the toggle walk over the whole text is well-formed. Should a future capture's
Appendix ever carry one, the walk desynchronizes and the equality BREAKS — a false RED, never a silent
pass — which is why that is declared here rather than closed with a second markdown grammar.

What Rule 3 requires of the other two selected spans is that this document SAY which assertion fails on a
truncation, and dimension (vii) below does. Neither is given an accounting: adding an assertion where the
existing one already fails is cost with no coverage.

**NEXT LEVEL — the dimensions swept, and what the sweep FOUND.** Closing "the selector" and "the phrase"
would leave the next dimension as the next round's finding, so the axes an oracle over committed markdown
can turn on are enumerated and each is answered above or answered here: (i) HEADING SELECTION — Rule 1,
plus the measured uniqueness of all four named headings; (ii) SPAN BOUNDARY — Rule 1's "any `## ` line",
plus the measured absence of a fenced `## ` inside every selected span, declared as a residual rather
than closed; (iii) LINE WRAPPING through a quoted phrase — Rule 2, total over both halves and over any
phrase added later; (iv) FENCE EXTRACTION — `fenced_blocks:1550`'s shape, with the measured two-space
indentation of every block scalar that could otherwise forge a fence; (v) TOKEN EXTRACTION FROM PROSE,
which is oracle #2 and is the one axis neither rule reaches, so it gets its own derivation: the capture
declares its 40-hex HEAD FOUR times (`:7`, `:59`, `:171`, `:179`), all the same value, so AC-1(a3)'s
oracle is **the SET of 40-hex tokens in the whole file (matched with non-hex boundaries, as
`tests/test_lint_vault_fix_rules.py:_HEX40:1515` does), asserted to be a SINGLETON, with
`HAL9000_PARITY_ANCHOR` asserted equal to its one member** — never "the first match", which would be
green against a capture that declared two different HEADs, and never a pinned occurrence count, which a
re-run capture legitimately moves. (vi) ENCODING and line endings are not a dimension here: all three
files are committed UTF-8 with `\n` endings and are read through `Path.read_text()`, and no oracle is
anchored to `$` or to a line end. **(vii) FAIL DIRECTION — the dimension this sweep's FIRST pass did not
turn**, added after the threat model's round 3 named it, and answered PER SPAN rather than per section
because per-section is exactly where the uniformity claim broke. `## Exploration Notes` (oracle 3) cannot
be narrowed silently: a truncation before `:279` drops the sentence and the PRESENT half fails, and a
truncation after it leaves both halves answering over the bytes they are about, because `introduced_by`
occurs in that file exactly twice and the second occurrence (`:1434`) is outside the span either way.
`## Counts` (oracle 4) fails because Task 7 asserts the span yields EXACTLY ONE `yaml` fence before
reading it, so a truncated span yields zero and RAISES. `## Parity samples` (oracle 1's sample half) fails
on AC-1(a2)'s set equality against the frozen five-member `PARITY_KINDS` — INCIDENTAL protection, named as
such rather than relied on, since a capture that legitimately grew a sixth kind would move the constant
with it and nothing says (a2) owns the span's completeness. And `## Validation boundary` (oracle 1's
refusal half, AC-1(c2)) does NOT fail on a PARTIAL truncation: the non-vacuity clauses catch a TOTAL loss,
but `{p in accept if library_refuses(p)} == {p in accept if guarded(p)}` holds over any SUBSET of the
probes, so a truncation dropping some-but-not-all of the five guarded accept probes retires the
anti-widening ratchet §1.4, R1 and `## Risk Analysis` row 2 all name, while the floor stays green. Rule 3
closes that, over both capture spans in one expression.

**AND THE LEVEL BELOW (vii), swept and DECLARED — because a fold that closes only the current level leaves
the next level as the next round's finding (WI-226).** Generalize the generator one notch: a markdown span
is only one POPULATION an assertion quantifies over, so the defect shape is *an assertion of the form
`∀p∈P …` or `{p∈P : f(p)} == {p∈P : g(p)}` whose P is DERIVED at run time, which a silently shrunken P
satisfies vacuously or narrowly.* Sweep predicate: every assertion this plan orders whose quantified
population is computed rather than typed. It returns NINE, each answered here instead of at build time.
(1) AC-1(c2)'s `accept` probes — closed by Rule 3. (2) AC-1(a2)'s sample set — closed by Rule 3
non-incidentally, and by the frozen-constant equality incidentally. (3) AC-1(b)'s iterated `PARITY_KINDS`
— the population is the module's own constant plus a planted member, and (a2) binds that constant to the
capture's samples, so (1) and (2) carry it. (4) Task 6's drive table asserted TOTAL
(`covered ∪ excluded == gate_call_sites(files)`) — non-vacuous by MEMBER pins: the excluded set is asserted
to equal exactly one NAMED site and the other five are each driven through a named public door, so a
shrunken site set is RED on a missing member rather than green. (5) Task 10's `marker_grammar_sites`
module-set equality — a shrunken universe yields an EMPTY module set, which is `!=` the asserted singleton;
it fails by construction. (6) Task 9's AC-4(d) `(note, rule_id)` set equality — both sides are computed in
the SAME run over a digest-frozen corpus, and `CORPUS_DIGEST` plus
`test_fixture_vault_is_frozen_and_materialized_by_byte_copy` pin the population itself. (7) Task 11's
wall-membership RUN — already carries "a non-vacuity assertion first that the universe actually reaches
the new files". (8) The three WI-235 batteries (Tasks 3, 6, 10) — each drives PLANTED shapes the test
itself composes, so the population is the test's own literal and cannot shrink. (9) **Task 7's
emptied-population scan — the one member this sweep found UNGUARDED, closed in the same edit.** "No file
under `tests/fixtures/vault/` and no `NoteSpec.undeclared` key in `tests/fixture_vault.py:NOTES` names
`introduced_by`" is an ABSENCE over two walked populations, and a walk that returns nothing satisfies it
vacuously — the same shape as a truncated span, one level up. Task 7 now pins both populations by the
MEMBER that matters before asserting the absence: the file walk is asserted to REACH
`@Morvette Harkwell.md` and that note's text to carry `manager: "Oskaline Thrandell"`, and the `NOTES` walk
to reach that note's own `NoteSpec` with `undeclared` carrying `manager`. A member pin rather than a size
pin, because the corpus is a population WI-016 is entitled to grow.

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
  a marker through the `text` channel; a caller TRUNCATING or SHADOWING the `## Timeline` span through
  the same channel with a markdown heading (M1). *Decision:* the readers are regex matchers over text,
  build no path and execute nothing; the marker channel is closed at construction by guards 1 and 2 of
  §1.4 and the SECTION channel by guard 5, which together are total over the generator — `text` is the
  only field that can introduce a line (§1.4's field sweep). *Reasoning:* the machine channels (the
  marker, and the heading the accessor, the dedupe and both detectors route on) must not be writable from
  the prose channel, which is the one crossing this item creates; both effects of the unguarded case are
  SILENT narrowings rather than errors, which is what makes a refusal the right instrument.
  *Test:* AC-1(c), AC-1(c2), and Task 3's clause (c3) for the claimed shapes, the near-misses and the
  span-loss consequence.
- **A kind nobody captured.** *Case:* a new writer builds `TimelineEntry(kind="deal-closed", …)`.
  *Decision:* it constructs, renders and round-trips; the library makes no byte-parity CLAIM about it;
  the accessor returns no record for it and does not raise. *Reasoning:* D8 — this item relocates and
  does not tighten. *Test:* AC-1(a4), AC-2(a).
- **A locale whose `%B` is not English.** *Case:* the heading's month name changes. *Decision:* accepted
  and unguarded: both HAL9000's renderer and the library's call `strftime('%B')`, so a locale moves both
  identically and parity is preserved; the on-disk corpus is English. *Reasoning:* pinning a month table
  in the library would make it DIFFER from the code it is relocating — the one thing §1 must not do.
  *Test:* AC-1(a) proves the equality under the build environment's own locale.
- **A committed oracle file whose selected span silently TRUNCATES (M2).** *Case:* a later, correct ship
  introduces a line-start `## ` inside a fenced block in one of the four `docs/**` spans this item selects,
  so §12 Rule 1's fence-unaware boundary ends the span early. *Decision:* RED in every case, and the
  assertion that makes it RED is named per span (§12 dimension (vii)): the capture's two spans by the
  whole-file `yaml`-fence accounting Task 3 asserts before it reads a sample or a probe (§12 Rule 3),
  `## Exploration Notes` by its PRESENT phrase failing, `## Counts` by its exactly-one-`yaml`-fence clause
  raising. NOT by a fence-aware boundary, which is declined deliberately. *Reasoning:* a truncation is an
  oracle NARROWING and not an error, so the failure that matters is the one that would stay GREEN —
  AC-1(c2)'s set equality holds over any SUBSET of the `accept` probes, so a partial truncation of the probe
  span would retire the anti-widening ratchet §1.4 and `## Risk Analysis` row 2 name while the floor passes.
  The accounting is preferred over a pinned count because the cutover re-runs the capture and legitimately
  probes more boundary values; both sides move together. *Test:* AC-1's check (the accounting clause),
  AC-3's check (the exactly-one-fence clause).

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

- [ ] **Task 2 — The leaf module, its refusal leaf and the package exports, with the prose channel
  unable to write either machine channel (M1).** Create
  `obsidian_schemas/timeline_entry.py` exactly as §1 specifies: `_KIND_BODY`, the three patterns and
  `STRUCTURAL_LINE_PATTERN` (§1.1), the four types plus `Marker.key` (§1.2), the SIX functions
  (§1.3 — `_compose_key` is the FIRST of them and is the single spelling of the `{kind}:{day}:{disc}`
  grammar: `dedupe_key` and `Marker.key` both delegate to it, so no second copy of the key format exists
  anywhere in the module, at the door or in a test, which matters because the key carries no `<!--`/`-->`
  delimiter and is therefore outside AC-2(e)'s scan by construction), the validation
  table and the FIVE guards with
  their pattern literals (§1.4), `PARITY_KINDS`, `HAL9000_PARITY_ANCHOR` and the three kind constants
  (§1.5). **Guard 5 is M1 and is written in this task, not a later one:** `TimelineEntry.__post_init__`
  refuses a `text` containing a line matching `STRUCTURAL_LINE_PATTERN` (`^#{2,3} `, tested MULTILINE
  over the whole string — never `startswith`) with `pattern` `TEXT_STRUCTURAL_LINE_KEY`, because such a
  line truncates or shadows the `## Timeline` span the accessor, the marker-anchored dedupe and both new
  detectors all read through. `STRUCTURAL_LINE_PATTERN` has exactly two readers — this guard and
  `parse_entries`' body boundary (§1.3), deliberately the same constant so door and reader cannot drift
  — and `# `/`#### ` are outside it by construction (§1.1). Add
  `TimelineEntryRefusal` to `obsidian_schemas/errors.py` beside `NameGateRefusal`, declaring
  no `__init__` and carrying `pattern: Optional[str] = None`, plus ONE new member in `REASONS`:
  `"a timeline entry field this package refuses"` (one member for the whole door, guard 5 included).
  Export all of §3's names from
  `obsidian_schemas/__init__.py` and add each to `__all__`.
  **THE COUNT PIN OVER `REASONS` MOVES IN THIS TASK, NOT A LATER ONE (§9's third countable corpus).**
  `tests/test_name_gate.py:124` is `assert len(REASONS) == 16`, an EQUALITY pin its own comment at
  `:121-122` declares deliberate, sitting inside
  `test_name_gate_refusal_is_a_loud_fail_leaf_carrying_a_pattern:109` — a check that never calls the
  declaring symbol, which is why the sweep has to name it. Edit it to `17` in the SAME task that adds the
  member, and add `TimelineEntryRefusal`'s own leaf assertions to that check beside `NameGateRefusal`'s,
  mirroring the four it already makes: a leaf of `LoudFailError` DIRECTLY and not of `NoteParseError`
  (`:114-115`), `"__init__" not in TimelineEntryRefusal.__dict__` (`:119`), the new reason literal is a
  `REASONS` member and a non-member reason is refused as a BARE `ValueError` outside the hierarchy
  (`:130-138`), and `pattern` defaults to `None` on both the class and an instance (`:127-128`). The
  obligation is the predicate, never the number: **the enumerated-reason set grows by exactly one and
  every pin over it moves with it.** §9's sweep records that `tests/test_name_gate.py:124` is the ONLY size
  pin over `REASONS` in the tree and that `__all__` carries membership assertions only, so nothing else
  moves. **The pin's own adjacent comment moves with it and is IN the bounded edit**, not a "while I'm
  here" touch: `tests/test_name_gate.py:121-122` reads "REASONS is a FROZEN population, so equality is
  the right pin: fifteen members before this item, sixteen after", which is wrong in both halves the
  moment the number moves. Update those two numbers (and only those) so the comment still says what the
  assertion beneath it does; leave the first sentence — the reason equality is the right pin — as it is. **Verify:** Task 3's check is the oracle for the module — its clause (c3) is guard 5's; the second
  named check is the pin and the new leaf's hierarchy assertions. This task is done when the module imports
  under the project interpreter, the new leaf is constructible, and both checks are green.
  verify: test_timeline_entry_reproduces_hal9000_render_and_validation_boundary test_name_gate_refusal_is_a_loud_fail_leaf_carrying_a_pattern

- [ ] **Task 3 — The parity and validation-boundary check, driven by the committed capture.** Create
  `tests/test_timeline_entry.py` (interpreter shim first, per §8.3; module docstring carrying a
  `CORPUS_COUPLING:` line in the shipped form — `tests/test_fixture_vault.py:3` and
  `tests/test_ac_interpreter.py:23` are the models — naming the two heading names and the declared keys it
  pins in `docs/wi-033-hal9000-timeline-entry-capture.md` and the property it consumes, per
  `## Verification`'s reader-1 declaration) defining
  `test_timeline_entry_reproduces_hal9000_render_and_validation_boundary`, which parses
  `docs/wi-033-hal9000-timeline-entry-capture.md` — the `## Parity samples` and `## Validation boundary`
  sections, one `yaml` fence per record.
  **THE SELECTOR IS SPELLED IN ITS OWN TERMS, NOT BY TRANSPLANT (§12, RULE 1).** Write
  `select_sections(text, names)` in `tests/derivations.py` — the tree's one home for shared test-side
  derivations, and the reason Task 7's check can import the SAME helper instead of a second copy (a
  markdown selector spelled twice is the very duplication §12 exists to prevent; it uses no `ast`, so
  §9's single-homing row is unmoved). Its contract: for each NAME, find the lines whose `line.rstrip()`
  EQUALS it — exact, line-start, whole-line — and RAISE if a name matches zero lines or more than one;
  the section's text runs from the line after its heading to the line before the next line whose
  `line.startswith("## ")` is true (whatever heading that is) or to end of file; every `## ` line the
  `names` list does not mention is IGNORED as a selection candidate and HONOURED as a boundary.
  `tests/test_lint_vault_fix_rules.py:baseline_sections:1518` is the RAISING DISCIPLINE to copy — a
  selector that finds nothing must be RED, never an empty dict — and NOT a function to transplant: it is
  a TOTAL parse that raises on any heading outside its own declared table (`:1528-1536`), and this
  capture carries three headings no `names` list mentions — `## Part 1 — source (verbatim, with line
  ranges)` at `:57` and AGAIN at `:587` inside the Appendix's `python` fence, and
  `## Appendix — the generator, verbatim` at `:470` — so a faithful copy would raise before reaching a
  single `yaml` fence. `tests/test_lint_vault_fix_rules.py:fenced_blocks:1550` IS the shape to copy for
  the per-section fence walk (toggle on any `line.startswith("```")`, blocks in order), applied to one
  selected section's text — copied into `tests/derivations.py` as `select_fenced_blocks(section_text)`
  beside `select_sections`, again so Task 7 imports it rather than spelling it a third time; the shipped
  `fenced_blocks` is left exactly where it is (§12 says why). **With ONE deviation from a verbatim copy,
  and it is load-bearing: RETAIN THE INFO STRING.** `fenced_blocks` discards it — the opening fence line
  is consumed by the triple-backtick branch at `:1554-1559` and never appended to the block — so
  `select_fenced_blocks` returns `(info, block)` PAIRS, `info` being the opening fence line with its
  leading backticks and surrounding whitespace stripped (`""` for a fence opened with no info string).
  Both consumers filter on `info == "yaml"`, and §12 Rule 3's whole-file accounting cannot be expressed
  without it — the capture's four `python` fences are exactly what the accounting must exclude.
  `yaml.safe_load` each `yaml` block.
  **Ship the WI-235 battery for `select_sections` too — its REACH is exactly what both of the spec
  review's round-2 findings turned on, and a selector that "works on the capture" says nothing about it.**
  Drive plain in-test strings through the derivation ITSELF, never a re-implementation: the CLAIMED
  shapes — a named heading selected; a `## ` heading the `names` list does not mention IGNORED as a
  candidate but HONOURED as a boundary (the `## Part 1` / `## Appendix` case); a named heading whose span
  runs to end of file; a duplicate of a heading that is NOT named, which must NOT raise (the `:587` echo
  case). Then the NEAR-MISSES it must not match, each asserted: `### Foo` is neither a selection
  candidate nor a boundary; an indented `  ## Foo` is neither; `## Foo bar` does not satisfy the name
  `## Foo` (whole-line equality, not prefix — this is the one place it deliberately differs from
  `baseline_sections`, which matches by prefix because its artifact's headings carry qualifiers). And the
  RAISING discipline asserted in both directions: a name matching zero lines RAISES, and a name matching
  two lines RAISES.
  **Ship the SAME battery for `select_fenced_blocks`, whose reach now carries §12 Rule 3's accounting.**
  Drive plain in-test strings through that derivation ITSELF: a text holding one `yaml` fence and one
  `python` fence, asserted to return two `(info, block)` pairs whose infos are `"yaml"` and `"python"` in
  that order and whose bodies contain NEITHER delimiter line; a fence opened with no info string, asserted
  to yield `info == ""`; two consecutive fences, asserted to yield two blocks in order. Then the
  near-miss: an INDENTED triple-backtick line, which the toggle must NOT treat as a delimiter (the shipped
  shape is `line.startswith`, never `line.strip().startswith`), asserted by the block count it does not
  change. The info string is the whole reason this helper deviates from `fenced_blocks:1550`, so it is
  asserted rather than assumed. Then assert, with every oracle read from the
  file and NO literal re-typed into the test:
  (a) for every sample, `render(TimelineEntry(kind=…, text=…, when=datetime.fromisoformat(…),
  discriminator=…))` is byte-identical to that sample's `rendered` block;
  (a2) `PARITY_KINDS == {s["kind"] for s in samples}` — the `## Parity samples` section's kinds, per R2;
  (a3) `HAL9000_PARITY_ANCHOR` equals the 40-hex HEAD the capture declares — and the oracle is the SET,
  never the first match (§12, dimension (v)): collect every 40-hex token in the WHOLE file with non-hex
  boundaries on both sides (`tests/test_lint_vault_fix_rules.py:_HEX40:1515` is the shape), assert the
  set is a SINGLETON, and assert `HAL9000_PARITY_ANCHOR` equals its one member. The capture declares the
  same HEAD four times (`:7`, `:59`, `:171`, `:179`), so "the first match" would be green against a
  capture that declared two DIFFERENT HEADs; the singleton assertion is what makes that RED. Pin no
  occurrence count — a re-run capture legitimately moves it;
  (a4) a PLANTED slug-valid kind absent from `PARITY_KINDS` (`deal-closed`) constructs, renders and
  round-trips, and `PARITY_KINDS` is asserted not to be consulted — the planted kind's own round trip is
  the discriminant;
  (b) for every member of `PARITY_KINDS` iterated (never a hand list) plus the planted kind,
  `parse_markers(render(entry))` returns exactly one `Marker` whose `kind`, `day` and `discriminator`
  equal the entry's, and `dedupe_key(entry) == marker.key` — the `Marker.key` property §1.2 declares,
  which composes through the same `_compose_key` as `dedupe_key`, so the assertion tests the RENDER →
  PARSE round trip rather than two hand-kept copies of the `{kind}:{day}:{disc}` grammar agreeing with
  each other. Also assert `marker.source == dedupe_probe(entry)`, the ONE string §2 branch 2's dedupe
  compares, so the door's comparand is pinned here rather than only described;
  (c) each of §1.4's five guards raises `TimelineEntryRefusal` with the pattern this document names;
  (c2) R1's reified equality — the set of `accept` probes the library REFUSES equals the set of `accept`
  probes matching this document's five guard predicates, with that second set asserted non-empty, and
  every `accept` probe outside it asserted to CONSTRUCT. Registering the fifth predicate in the filter is
  what keeps the two sides derived rather than hand-kept; it adds no member here, and R1 says why;
  (c3) GUARD 5's REACH, SHIPPED AS FIXTURES RATHER THAN INFERRED FROM A REFUSAL COUNT (WI-235, M1) —
  drive every shape this document CLAIMS the guard covers through the module's own construction, each
  asserted to raise `TimelineEntryRefusal` with `TEXT_STRUCTURAL_LINE_KEY`: a `text` whose FIRST line is
  `## Notes`; one whose SECOND line is (`"ok\n## Notes"`, the `startswith` discriminant); a duplicate
  `## Timeline`; and an `### {date} [intro-by]` entry-heading line. Then the NEAR-MISSES the predicate
  must NOT match, each asserted to CONSTRUCT and render: `# h1`, `#### h4`, a `#` mid-line
  (`"see # here"`), an indented `"  ## x"`, and the capture's own multi-line accept probe read from the
  file (`'line one\n\nline two'`) — the last is the direct proof that (c2)'s equality is unmoved.
  Then the CONSEQUENCE the guard exists to prevent, asserted rather than argued, and built WITHOUT the
  door so the guard cannot suppress its own demonstration: compose a body holding `## Timeline` followed
  by two rendered entries, record `len(parse_markers(get_section(body, "Timeline")))` as the oracle the
  test itself holds (WI-149 — never a literal `2`), then splice the line `## Notes` between the two
  entries by plain string surgery and assert the same expression now returns strictly fewer markers; do
  the same with a spliced duplicate `## Timeline` line for the shadowing half. This is what makes a
  build that drops guard 5 RED on the DAMAGE rather than only on a missing raise;
  **COMPLETENESS FIRST, THEN NON-VACUITY (§12 RULE 3, M2).** Before any assertion above reads a sample or
  a probe, assert the WHOLE-FILE ACCOUNTING over the capture: the number of `yaml`-info fences
  `select_fenced_blocks` returns over the selected `## Parity samples` text PLUS the number it returns over
  the selected `## Validation boundary` text EQUALS the number it returns over the whole file's text, with
  all three counts asserted non-zero — so a span truncated by a line-start `## ` introduced inside a fence
  is RED rather than green over a narrowed population. Type NO literal count and pin no occurrence figure:
  a re-run capture legitimately probes more boundary values and both sides of the accounting move with it
  (R1's own reason for refusing a probe count). This is the clause that keeps AC-1(c2)'s set equality from
  being satisfied over a SUBSET of the `accept` probes — the non-vacuity clauses below do not catch that,
  because they catch a TOTAL loss only and the equality holds over any subset — and it is therefore what
  holds the anti-widening ratchet `## Risk Analysis` row 2 names. THEN non-vacuity: assert the sample set
  and the probe set are non-empty and that the probes carry both
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
  `introduced_by` afterwards; and the swapped value's extracted tokens are all in `NAME_POOL`.
  **PIN BOTH WALKED POPULATIONS BY THEIR ONE LOAD-BEARING MEMBER BEFORE ASSERTING THE ABSENCE (§12's
  level-below-(vii) sweep, member 9).** An absence over a walked population is satisfied VACUOUSLY by a
  walk that returns nothing — the same defect shape as a truncated span, one level up — so assert FIRST
  that the file walk REACHES `tests/fixtures/vault/@Morvette Harkwell.md` and that that note's text carries
  `manager: "Oskaline Thrandell"`, and that the `NOTES` walk reaches that note's own `NoteSpec` with
  `undeclared` carrying `manager`. A MEMBER pin and never a size pin: the corpus is a population WI-016 is
  entitled to grow, so a count would be somebody else's ratchet.
  **THE `docs/vault-fixtures.md` CLAUSE IS A POSITIVE, SECTION-SCOPED, WRAP-INSENSITIVE READ — NOT A
  WHOLE-FILE ABSENCE PIN AND NOT A LITERAL SUBSTRING TEST (§0 R6, §12, WI-278).** Select that file's
  `## Exploration Notes` section with the SAME `select_sections(text, names)` helper Task 3 adds to
  `tests/derivations.py` (§12 Rule 1: exact whole-line heading match, RAISE on zero or more than one,
  span to the next line-start `## ` whatever it is) — IMPORTED, never re-written here, so the two
  readers cannot drift. Then **normalize the selected text AND each phrase the same way,
  `" ".join(s.split())`**, and assert over THAT SECTION'S NORMALIZED TEXT ONLY, nothing else in the file:
  (i) the corrected phrase `` a `manager:` on a schema-drift or forward-compatibility note `` is PRESENT
  — which a deletion of the sentence fails, where the absence pin would have passed; and (ii) the stale
  phrase `` a `manager:` or `introduced_by:` `` is ABSENT from the same normalized text.
  **The normalization is load-bearing and is not optional (§12 Rule 2):** the file hard-wraps at ~100
  columns and the target sentence spans `:279-280`, so after the conductor's one-sentence deletion the
  corrected phrase still contains a NEWLINE (it ends `:279` at "or" and resumes `:280` at
  "forward-compatibility") and a literal `in` test is RED against a correct edit — while the ABSENCE
  half is contiguous on `:279` today and would have passed, which is what hides the defect. Do not
  "fix" this by asking the conductor to re-wrap: nothing in the precondition asks for it, re-wrapping
  only moves the break to a different word, and no assertion in this item may depend on a wrap column.
  The section selection is what keeps WI-016's SIGNED AC-5 fence at `:1434` out of reach — it sits under
  `## Acceptance Criteria` — so the test rolls NO `criteria`-fence scan and pins no predicate this tree
  has no leaf for. **The live half of AC-3(c) takes the same three rules (§12, oracle #4):** read
  `introduced_by_frontmatter_carriers` from the ONE `yaml` fence of
  `docs/wi-033-intro-corpus-baseline.md`'s `## Counts` section, selected by the same `select_sections`
  and walked by the same `select_fenced_blocks` Task 3 homes in `tests/derivations.py` — both IMPORTED —
  and assert it is `0`: a premise READ, never a vault re-measured. Assert the section yields EXACTLY ONE
  `yaml`-info fence first — the info string `select_fenced_blocks` retains (§12) — so a capture that grew a
  second block is RED rather than silently taking the first. That one assertion is also what makes this
  oracle FAIL on a truncated span rather than narrow silently, which is why §12 dimension (vii) gives it no
  accounting of its own.
  The one-line coupling declaration lives in `## Verification` beside AC-1's AND in the
  code: add a `CORPUS_COUPLING:` line to
  `test_the_write_gate_refuses_the_retired_introduced_by_key`'s own docstring in the shipped CHECK-granular
  form (`tests/test_lint_vault_fix_rules.py:1639` and `tests/test_whatsapp_migration.py:1114` are the
  models), naming BOTH `docs/**` reads this check makes — the ONE heading and the ONE phrase it pins in
  `docs/vault-fixtures.md`, and the ONE heading and ONE key it pins in
  `docs/wi-033-intro-corpus-baseline.md` — and the property each consumes, exactly as
  `## Verification`'s reader 2 states them.
  **Verify:** as declared — the corpus walls and the gate check together.
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
  non-vacuity assertion first that the universe actually reaches the new files. **`tests/test_name_gate.py`
  is in that file set** (Task 2 edits it, §9's new inbound row), so the run includes its four stated
  requirements: `modules_using_ast` returns it NOT; `check_module` on every `def test_` name in it resolves
  to exactly one module; `NO_ARG_CONSTRUCTION` finds nothing; and the declared pytest globs still collect
  it. Those are the predicates
  `tests/test_name_gate_wall.py:test_wall_membership_is_closed_by_running_each_walls_predicate:1057` and
  `tests/test_fixture_vault.py:test_the_fixture_vault_files_close_their_wall_memberships_by_running_each_predicate:1353`
  already run over that file from their own items' frozen lists — this check calls them on the FINAL text
  so a violation surfaces here rather than in somebody else's module. In the same check, call
  `tests/test_ac_interpreter.py:check_module` on all four of this item's AC check names and assert each
  resolves to exactly one module — the conveyor's own discovery rule, which raises on a duplicate name.
  Anything the run returns that §9's table did not name is NAMED in the Build Log and satisfied there,
  never by narrowing a wall. **Verify:** as declared.
  verify: test_the_wi033_files_close_their_wall_memberships_by_running_each_predicate

- [ ] **Task 12 — This item's own checks green, and the pins re-read rather than edited.** **The whole
  project floor is NOT this task's obligation (WI-314) and is deliberately not ordered here:** the
  drive-end floor and the battery at every cap-bind already own it, so a plan task that runs it spends a
  build window per attempt on a run the builder can neither shorten nor fix, and converts any unrelated
  red into this item's build-attempt cap. What this task owns is what it can actually fix — this item's
  own four AC checks green, plus the pin accounting, each discharged by a STANDING check rather than by a
  hand read: `tests/test_lint_vault_fix_rules.py:822`'s `len(pinned) == 7` is asserted by
  `test_every_write_causing_detector_fires_exactly_on_its_declared_subjects:818`;
  `CENSUS_SHAPE_TO_RULE`'s value-set equality against the derived auto-fixable set AND
  `docs/lint-vault-live-baseline.md`'s §1/§4 rows are asserted by
  `test_the_live_vault_baseline_is_committed_shaped_and_agrees_with_the_census:1634` (`:1698-1710`), which
  also proves the baseline document needed no edit; and §9's third corpus is asserted by
  `test_name_gate_refusal_is_a_loud_fail_leaf_carrying_a_pattern:109`, whose `REASONS` pin Task 2 moved.
  Read `tests/test_lint_vault_fix_rules.py:CORPUS_PINNED_ISSUES:809` and confirm it needed no edit (§9's
  sweep: the re-key moves no `meeting_missing_from_timeline` count). Record in the Build Log: the six
  named checks' results and the `CORPUS_PINNED_ISSUES` reading. No number is asserted anywhere here — Task
  1's baseline stays informational (WI-238) and nothing pins it. **Verify:** as declared.
  verify: test_timeline_entry_reproduces_hal9000_render_and_validation_boundary test_introduced_by_reads_only_this_persons_intro_by_markers test_the_write_gate_refuses_the_retired_introduced_by_key test_lint_vault_reports_the_intro_legacy_shapes_and_never_repairs_them test_every_write_causing_detector_fires_exactly_on_its_declared_subjects test_the_live_vault_baseline_is_committed_shaped_and_agrees_with_the_census

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
root, `bin/**` or `state/**`, and no task's verify command writes anything at all — every task's verify
is a named check or a read, all read-only over the tree (WI-238), and no task orders the whole project
floor (WI-314; Task 12's narrowing).

**Extended again 2026-09-29** after the spec review's finding 1: `tests/test_name_gate.py` is added as a
builder write target. It is not a "while I'm here" edit — Task 2 adds a member to
`obsidian_schemas/errors.py:REASONS:152` and that module's `:124` pins the set's SIZE by equality, so the
edit is owed by construction. §9 names the pin, its check and the predicate it discharges.

**Round 2 of the spec review, 2026-09-29, added NO path.** Its two findings were oracle-shape defects
(§12), not new write surfaces: `select_sections` and `select_fenced_blocks` land in
`tests/derivations.py`, already declared for
Tasks 6 and 10 — that fence's `why` now names them — and everything else this round moved is prose in
sections the builder reads. The precondition fence for `docs/vault-fixtures.md` is unchanged in KIND and
PATH; only its `why` gained the file's own bytes, the exact deletion, and the explicit statement that
re-wrapping is not asked for.

```writes
kind: precondition
path: docs/wi-033-hal9000-timeline-entry-capture.md
grounds: Whether the library's relocated renderer, kind-slug rule, marker grammar and dedupe contract reproduce HAL9000's shipped ones — byte-for-byte on what they RENDER and no stricter on what they REFUSE — including WI-077's two intro kinds and its `{kind}:{day}:{counterparty}` key format
why: "Relocate" means byte parity or it means nothing — 22 marker-bearing legacy entries and every WI-077 entry are already on disk, and a renderer that differs by one space stops round-tripping them while every hermetic test stays green. The caged builder cannot read HAL9000, and this reader's answer from there would have no HEAD to pin a re-run to, so the bytes must be IN the tree. Contents, part 1 — verbatim source of `backend_fastapi/core/timeline_entry.py` (the `TimelineEntry` class, its render, the kind-slug validation, the `-->`/`<!--` forgery guard, the dedupe-by-discriminator contract) and the two kind constants plus the key format from `routers/introduce.py` (`OBSERVED_KIND_ON_INTRODUCEE`, `OBSERVED_KIND_ON_INTRODUCER`, WI-077 note 6); each with a 40-hex HEAD, path and line range. Contents, part 2, and this is the half a source dump does not give — PARITY SAMPLES, which are INPUT→OUTPUT PAIRS and not outputs alone: an output whose inputs are absent is not reproducible, and a builder handed one is forced into exactly the re-typed literal AC-1(a) forbids. Shape, declared so the test can parse it deterministically rather than guessing (the precedent is `docs/lint-vault-live-baseline.md`, whose declared headings `tests/test_lint_vault_fix_rules.py:113` already parses): a single `## Parity samples` section holding one fenced block per sample, each a YAML code fence (info string `yaml`) with exactly the keys `kind`, `text`, `when` (a pinned absolute timestamp, because `when` is injectable and feeds BOTH the heading and the marker's day slot, so an unpinned sample reproduces nothing), `discriminator` (explicit `null` where the shipped call passes none), and `rendered` (a YAML block scalar holding the verbatim bytes that code emitted for those inputs). One sample per kind HAL9000 renders, INCLUDING the legacy `intro` kind, produced by RUNNING that code and not by reading it. Contents, part 3, and this is the surface render samples structurally cannot reach (D8) — THE VALIDATION BOUNDARY, as INPUT→VERDICT pairs: a `## Validation boundary` section holding one `yaml` fence per probe with exactly the keys `field` (`kind`, `text` or `discriminator`), `value` (the literal probe string; explicit `null` where the probe is an absent discriminator) and `verdict` (the literal `accept` or `refuse`), produced by RUNNING HAL9000's validation on that value and not by reading its regex. Every sample here is a VALID input, so a capture of samples alone cannot detect a library that REFUSES an input HAL9000 accepts — a divergence invisible to this tree's hermetic floor and visible only after the cutover, when the caller it breaks is HAL9000's own. Probe both verdicts and include, at minimum: a kind HAL9000's slug rule accepts that no sample renders; a kind it refuses (uppercase, a space, an empty string); a discriminator that is absent, empty, whitespace-only, and one containing the `:` key separator; and a kind, a text and a discriminator each containing `-->` and `<!--`. AC-1(c2) reads every pair and asserts the library is NO STRICTER in the ACCEPT direction, with the four deliberate over-refusals enumerated in AC-1(c) asserted as a set EQUALITY so the exception cannot be widened; the loose direction is out of scope by D8. Also declare, in prose beside the samples, the 40-hex HEAD once as the artifact's staleness anchor — AC-1(a) asserts the module's `HAL9000_PARITY_ANCHOR` equals it, and D7's cutover re-entry condition diffs against it. TWO STRUCTURAL PROPERTIES THE CHECK RELIES ON, named here rather than left as incidental (§12 Rules 1 and 3, M2), and BOTH HOLD OF THE FILE AS ALREADY COMMITTED — measured this round, so no conductor act is owed now and this is written for whoever REGENERATES it at the cutover: each of `## Parity samples` and `## Validation boundary` occurs exactly ONCE at line start, and every `yaml` fence in the file sits inside one of those two sections (today: six and twenty-nine, thirty-five in the file, the other four fences `python` — Part 1's three and the Appendix's one). A regenerated capture may hold any number of samples and probes, and neither count is pinned; what it may not do is park a `yaml` fence in a third section, or let its Appendix's `python` fence contain a line-start triple-backtick. Nothing else about the file is load-bearing: not its wrap, not its heading count, not the position of any section. Precedents: `docs/wi-024-consumer-audit.md`, `docs/wi-029-consumer-audit.md`.
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
why: Task 7 / AC-3(c) — the conductor commits this one-sentence edit, because the caged builder cannot be its author. The file is ANOTHER item's tracked work-item document (`id: WI-016`), and since WI-245 the merge boundary admits a declared cross-doc edit only when it is ADDITIVE PROSE outside every fence; AC-3(c)'s edit REPLACES prose at `:279`, so a caged write to it is refused at the merge boundary and costs a conductor hand-landing plus a relaunch. THE EDIT, IN THE FILE'S OWN BYTES, so no reader has to re-derive it: `:279-280` currently read "a `manager:` or `introduced_by:` on a schema-drift or forward-compatibility note" (AC-3(c)'s `desc` paraphrases this as "a `manager:` or `introduced_by:` key" — the word "key" is not in the file; the bytes above are the target). DELETE the substring `` or `introduced_by:` `` from `:279` and change NOTHING else. WHAT IS NOT ASKED FOR, stated because the earlier draft's oracle silently depended on it: the conductor is NOT obliged to re-wrap, re-flow or re-join the paragraph, and NO assertion in this item depends on where the line breaks fall — Task 7's two phrase tests run over whitespace-NORMALIZED text (§12 Rule 2), which is what makes a hard-wrapped sentence spanning `:279-280` testable at all. The same phrase inside WI-016's SIGNED AC-5 `criteria` fence at `:1434` is explicitly OUT of scope and must not be touched — moving a typed parse of another item's document is what the merge rule forbids, and that fence is another item's signed criterion. Checked against the PRE-DRIVE floor (WI-156, WI-164): no test in this tree reads `:279`'s prose and the file participates in no bijection or symmetry invariant the floor enforces, so this lands independently of the builder's fixture re-key and no atomic landing is required. Presence alone is not the evidence — the file is already in HEAD, so the WI-156 probe is trivially satisfied and AC-3(c)'s own check is what makes the edit verifiable.
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
why: Tasks 6 and 10 — `gate_call_sites` and `marker_grammar_sites`, the single home of `ast` in this tree; plus Task 3's `select_sections(text, names)` and `select_fenced_blocks(section_text)` (§12 Rule 1), homed here so Tasks 3 and 7 import ONE markdown-section selector and ONE fence walk instead of spelling each twice. `select_fenced_blocks` returns `(info, block)` PAIRS — the one declared deviation from `fenced_blocks:1550`, which discards the info string at `:1554-1559` — because both readers filter on `info == "yaml"` and §12 Rule 3's whole-file accounting (M2) cannot be expressed without it. Neither uses `ast`, so §9's single-homing row is unmoved.
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
path: tests/test_name_gate.py
why: Task 2 — the `len(REASONS) == 16` equality pin at `:124` moves to 17 because Task 2 adds one member to `errors.py:REASONS`, its own adjacent comment's two numbers at `:121-122` move with it, and `TimelineEntryRefusal`'s leaf assertions land beside `NameGateRefusal`'s in the same check (§9's third countable corpus).
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

**The counting walls ship their claimed shapes as fixtures (WI-235).** SIX oracles in this item have a
COUNT or a matcher's reach behind them, and each ships its claimed match-shapes through the wall's
OWN predicate plus a
near-miss the predicate must not match. The fifth and sixth were both added 2026-09-29 — the fifth after
the spec review's round 2, the sixth when the threat model's round-3 mitigation M2 made a second helper's
reach load-bearing. Fifth:
**`select_sections`' reach** — the markdown section selector §12 Rule 1 defines, whose claimed shapes
(a named heading selected; an unnamed `## ` ignored as a candidate but honoured as a boundary; a span
running to EOF; a duplicate of an UNNAMED heading not raising) and near-misses (`### Foo`, an indented
`  ## Foo`, `## Foo bar` against the name `## Foo`) are driven through the derivation itself in Task 3,
with the RAISE asserted in both directions. It earns the battery because the two findings this round
closed were both about a selector's or a matcher's reach over a file nobody read at that granularity,
and "it parses the capture" is satisfied identically by a selector that honours the rules above and by
one that honours almost none of them. Sixth: **`select_fenced_blocks`' reach, and specifically its INFO
STRING** — §12 Rule 3's whole-file accounting is a `yaml`-versus-`python` discrimination over the capture's
thirty-nine fences, and the shipped `fenced_blocks:1550` this helper copies DISCARDS the info string
(`:1554-1559`), so "the accounting holds on the capture" says nothing about whether the discrimination
works. Its claimed shapes (a `yaml` fence and a `python` fence in one text returning their two infos in
order with neither delimiter line in either body; a fence opened with no info string returning `""`; two
consecutive fences returning two blocks in order) and its near-miss (an INDENTED triple-backtick line,
which `line.startswith` must not treat as a delimiter) are driven through the derivation itself in Task 3.
The other four: AC-2(e)'s "exactly one definition of the grammar" drives five
planted source shapes through `marker_grammar_sites` (Task 10); AC-3(b)'s "the excluded set is exactly
one site" drives four planted call shapes, aliased import included, through `gate_call_sites` (Task 6);
AC-4(d)'s "silent over the frozen corpus" is a SET EQUALITY of `(note, rule_id)` pairs computed twice in
the same run rather than a zero, so a new issue that displaces an old one cannot cancel out (Task 9); and
M1's guard 5 — whose oracle is otherwise a refusal COUNT, satisfied identically by a predicate that
reaches every claimed heading shape and by one that reaches almost none — drives four claimed shapes and
five near-misses through the module's own construction, plus the span-loss consequence itself, in Task
3's clause (c3). Mutate-and-observe is used as the complementary half only — Task 3's one-space mutation
— and never as the proof.

**The delta assertion captures its baseline first (WI-238) — and no plan task asserts on it (WI-314).**
Task 1 records the pre-edit floor count, the pre-edit `CORPUS_DIGEST` and the pre-edit `len(pinned)`
reading in the Build Log before any file is edited, and that recording is INFORMATIONAL: nothing in the
plan pins it. Task 12 was narrowed on 2026-09-29 to drop the whole-floor run it previously ordered — the
floor is the DRIVE's obligation (the drive-end run and the battery at every cap-bind), and a plan task
that orders it spends a build window per attempt on a run the builder cannot shorten while converting any
unrelated red into this item's build-attempt cap. What Task 12 asserts now is this item's own four AC
checks plus two STANDING checks that carry the pin accounting
(`test_every_write_causing_detector_fires_exactly_on_its_declared_subjects` for `len(pinned) == 7`,
`test_the_live_vault_baseline_is_committed_shaped_and_agrees_with_the_census` for
`CENSUS_SHAPE_TO_RULE`'s value set and the live baseline's rows) — properties, never numbers.

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
`obsidian_schemas/errors.py` — **RE-SWEPT 2026-09-29, because the earlier paragraph named a SAMPLE of
four `tests/test_loud_fail_*.py` modules and that is precisely how finding 1's pin was missed.** The
predicate is "modules under the resolved test root that NAME this path" — for this file, the spelling
`obsidian_schemas.errors` — and it returns SIXTEEN: `tests/test_name_gate.py` (the one carrying the
`REASONS` size pin, and now a declared write target), `tests/test_name_gate_wall.py`,
`tests/test_name_gate_refusals.py`, `tests/test_name_gate_identifiers.py`,
`tests/test_name_gate_delta_rule.py`, `tests/test_loud_fail_parse.py`, `tests/test_loud_fail_write.py`,
`tests/test_writer.py`, `tests/test_repositories.py`, `tests/test_concurrent_access.py`,
`tests/test_provenance_write_seam.py`, `tests/test_phone_normalization.py`, `tests/test_fixture_vault.py`,
`tests/test_whatsapp_write_door.py`, `tests/test_whatsapp_migration.py`,
`tests/test_whatsapp_jid_storage.py`. Two corrections ride with the re-sweep: `tests/test_loud_fail_load.py`
does NOT name `obsidian_schemas.errors` (it names the package, so it belongs to the row below) and
`tests/test_loud_fail_harness.py` names NEITHER (it is a `tests/derivations.py` consumer, covered by that
row) — the old paragraph asserted both. For
`obsidian_schemas/__init__.py` — the same predicate over `from obsidian_schemas import` /
`import obsidian_schemas` returns `tests/test_name_gate.py`, `tests/test_loud_fail_parse.py`,
`tests/test_loud_fail_load.py`, `tests/test_loud_fail_write.py`, `tests/test_writer.py`,
`tests/test_repositories.py`, `tests/test_concurrent_access.py`, `tests/test_provenance_write_seam.py`,
`tests/test_write_target_seam_wall.py`, `tests/test_wi126_body_preservation.py`,
`tests/test_whatsapp_migration.py`, `tests/test_vault_path_required.py`,
`tests/test_resolve_or_create.py`, `tests/test_identity_index.py`, `tests/test_identity_endgame.py`,
`tests/test_fixture_vault.py`, `tests/test_company_name_contract.py`, plus the two non-check helpers
`tests/derivations.py` and `tests/record_identity_golden.py`, which discharge by importing cleanly; for
`scripts/lint_vault.py` — `tests/test_lint_vault_fix_rules.py`, `tests/test_lint_vault_fix_gate.py`,
`tests/test_stem_name_divergence_detector.py`, `tests/test_write_routing.py`; for
`tests/derivations.py` — every module in §9's table, since each imports from it; for
`tests/fixture_vault.py` and the corpus note — `tests/test_fixture_vault.py`,
`tests/test_parser.py`, `tests/test_writer.py`, `tests/test_repositories.py`,
`tests/test_vault_path_required.py`, and every module that materializes the corpus
(`tests/test_lint_vault_fix_rules.py`, `tests/test_stem_name_divergence_detector.py`,
`tests/test_whatsapp_migration.py`, `tests/test_whatsapp_write_door.py`,
`tests/test_whatsapp_jid_storage.py`, `tests/test_provenance_write_seam.py`); and for the path this
document ADDED on 2026-09-29, `tests/test_name_gate.py` — the predicate returns TWO modules, both of
which name it in a list and RUN their predicates over its text, so the edit is not free and §9's new
inbound row states what each requires: `tests/test_name_gate_wall.py:TOUCHED_TEST_FILES:1029` (member at
`:1033`) and `tests/test_fixture_vault.py:_item_test_modules:1315` (member at `:1323`). Its own three
checks staying green is carried by Task 2's second named check and Task 12's re-read. The list is a
SWEEP's output at 2026-09-29 and the obligation is the whole floor being GREEN, not this enumeration being
complete — the floor belongs to the DRIVE (WI-314), not to a plan task.

**No incident replay is owed (WI-173).** This is not an incident-class item: nothing broke in production
and this spec asserts no live failure. The four diagnostic claims in `## Verified Diagnosis` are about
code shapes, each falsifiable by a read, and the one live fact that could have been an incident — the
single stored `introduced_by` value — was already converted and read back by the conductor on 2026-09-28
(ruling §1) before this item. No incident is manufactured to satisfy the check, and no plan task drains
live state.

**A corpus fixture derives or freezes (WI-278 analogue).** This item ships TWO check modules that read
`docs/**` at run time — the artifact class WI-031 clause (v) keeps out of the floor's path — across
THREE files and FOUR oracles, enumerated by predicate in `## Design` §12. Each names its arm and its
coupling in one falsifiable line, and every one of them takes §12's three rules: the section selector is
spelled in its own terms and RAISES rather than returning empty (Rule 1), every phrase comparison
runs over whitespace-normalized text (Rule 2), and every span-derived oracle either FAILS on a truncation
of its span by construction — with the assertion that does it NAMED — or asserts that span's completeness
(Rule 3, the threat model's M2; the capture's two spans take the whole-file `yaml`-fence accounting, the
other two spans are answered by dimension (vii)). Both modules join
`tests/test_corpus_fixture_coupling.py`'s derived population the moment they land.

*Reader 1 — AC-1's capture read (Task 3). FROZEN-BYTES arm.*
`docs/wi-033-hal9000-timeline-entry-capture.md` is a conductor-committed, machine-shaped artifact whose
fences are the oracle, selected by its DECLARED headings (`## Parity samples`, `## Validation boundary`)
— never by a glob, a size, a position or a live population's shape. The selection is `select_sections`
(§12 Rule 1), which copies `tests/test_lint_vault_fix_rules.py:baseline_sections:1518`'s RAISING
discipline and NOT its total-parse behaviour: that function raises on any heading outside its own
declared table, and this capture carries `## Part 1` at `:57` and again at `:587` inside the Appendix's
`python` fence plus `## Appendix` at `:470`, so a transplant would raise before reaching a fence.
The coupling, in one line: **AC-1's check pins those two heading names and the five/three declared keys
per fence, and consumes the property that every `rendered` block and every `verdict` was produced by
RUNNING HAL9000's code at `HAL9000_PARITY_ANCHOR`.** Two measurements ride with it as the declaration's
own disclosure, because §12 Rule 1 is deliberately fence-UNAWARE: each named heading occurs EXACTLY ONCE
at line start, and neither selected span (`:224-289`, `:291-469`) contains a line-start `## ` line at
all, so the spans are exact today and a fenced `## ` introduced inside one later would truncate it — the
named residual, measured at zero, not a closed case. **What that truncation now COSTS is bounded by an
assertion rather than by the measurement alone (§12 Rule 3, M2):** this check asserts the whole-file
accounting — the `yaml`-info fence count of `## Parity samples` plus that of `## Validation boundary`
equals the file's own — BEFORE it reads a sample or a probe, so a truncation of either span is RED instead
of leaving AC-1(c2)'s guard-set equality green over a subset of the `accept` probes. The accounting pins no
number: a re-run capture that probes more boundary values moves both sides together. Its own residual,
measured and disclosed for the same reason: the whole-file leg is a toggle walk, so it needs no line-start
triple-backtick to sit inside any fence in the file, which holds today (the Appendix's `python` fence at
`:474-603` carries none) and whose violation is a false RED, never a silent pass.
AC-1(a3)'s HEAD read is the fourth oracle's sibling
and takes §12 dimension (v)'s derivation: the SET of 40-hex tokens in the file is asserted to be a
singleton (it holds four identical occurrences today) rather than the first match being taken.

**Where the declaration LIVES in the code, not only here (the shipped convention).** Every module in this
tree that reads a file it did not author carries a `CORPUS_COUPLING:` line in its docstring naming what it
pins and what property it consumes — `tests/fixture_vault.py:3`, `tests/test_fixture_vault.py:3`,
`tests/test_ac_interpreter.py:23`, `tests/test_company_name_contract.py:15`,
`tests/test_identity_endgame.py:10`, and at CHECK granularity where only one leg reads a corpus
(`tests/test_lint_vault_fix_rules.py:1639`, `tests/test_whatsapp_migration.py:1114`). Both readers below
carry one in the same form: `tests/test_timeline_entry.py`'s at MODULE granularity (the whole module rests
on the capture) and Task 7's at CHECK granularity inside
`test_the_write_gate_refuses_the_retired_introduced_by_key` (only that clause reads `docs/**`). Tasks 3
and 7 order it. There is no wall enforcing the marker in this tree — `tests/test_corpus_fixture_coupling.py`
is workshop's, not this project's — so this is pattern consistency and reviewer-legible disclosure, which
is exactly what WI-278's third arm asks for.

*Reader 2 — AC-3(c)'s two reads (Task 7). NARROWED, then DECLARED (§0 R6, added 2026-09-29 after the
spec review's finding 3; its ORACLE made wrap-insensitive and its second file named after round 2's
findings).* Neither WI-278 arm is fully available for the `docs/vault-fixtures.md` half: the sentence
is prose in another item's tracked document, so there is no callable to probe and no frozen-bytes artifact
to carry. The draft's oracle — the absence of `` `introduced_by:` `` from that whole file outside its
`criteria` fences — was the failure shape the rule exists for, and worse, a deletion of the sentence would
have SATISFIED it. So the assertion is narrowed to the nearest available approximation of the derive arm
and then declared: it selects the `## Exploration Notes` section with the same `select_sections` helper
reader 1 uses (§12 Rule 1 — RAISING on a missing or duplicated heading, so a selector that finds nothing
is RED), normalizes whitespace on both sides (§12 Rule 2), and asserts POSITIVELY inside that section
only. The coupling, in one line: **Task 7's check pins ONE heading name (`## Exploration Notes`) and the
presence of ONE whitespace-normalized phrase inside it
(`` a `manager:` on a schema-drift or forward-compatibility note ``) plus that phrase's stale two-key
predecessor's absence from the same normalized text, and it consumes the property that
`docs/vault-fixtures.md`'s undeclared-key example names the key the gate still permits.** And the same
check makes a SECOND `docs/**` read, which round 2's sweep named as a member of the same class rather
than leaving it to build time — **it pins ONE heading name (`## Counts`) and ONE key
(`introduced_by_frontmatter_carriers`) in the one `yaml` fence of
`docs/wi-033-intro-corpus-baseline.md`, and consumes the property that the fence is a dated snapshot of
the live vault produced by the committed census command, read as AC-3(c)'s premise and never
re-measured.** What that buys, stated so the next reader can weigh it: the archive-split leaf rewrites
GATE-ROUND `##` sections (`docs/vault-fixtures.md:3761` declares the drawer, and
`docs/vault-fixtures-rounds.md` exists) and not `## Exploration Notes`, so the pinned section is not the
splitter's target; and anything else anyone adds anywhere in that 6,200-line file — including a new
round, a retrospective, or a second mention of the retired key — no longer reddens this item, which the
whole-file pin could not survive. The residual the durability argument does NOT cover, disclosed here
rather than discovered later: §12 Rule 1 is fence-unaware, so a line-start `## ` introduced inside a
fenced block anywhere in `:84-1119` would truncate the selected span early.
MEASURED at zero — the next line-start `## ` after `:83` is `## Approach`
at `:1120` — and the same measurement holds for `## Counts`'s span (`:57-116`, next heading
`## Verbatim output` at `:117`). A fence-aware boundary is declined deliberately (§12): it would be a
second markdown grammar for a case measured at zero across all three files. **And what each of these two
spans DOES on a truncation is stated rather than assumed uniform (§12 dimension (vii), M2), because that
assumption is exactly what round 3 falsified for a third span.** `## Exploration Notes` cannot be narrowed
silently: a truncation before `:279` drops the sentence and the PRESENT half FAILS, while a truncation
after it leaves both halves answering over the bytes they are about, since `introduced_by` occurs in that
file exactly twice and `:1434` is outside the span either way. `## Counts` RAISES, because this check
asserts the span yields exactly ONE `yaml` fence before reading it. So neither needs a completeness
accounting, and neither is given one — an assertion added where the existing one already fails is cost with
no coverage.

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
  (Task 12), and each re-read is discharged by a STANDING check rather than by a hand reading.
- **No whole-floor run ordered by a plan task (WI-314).** Task 12 asserts this item's own four AC checks
  plus the two standing checks carrying the pin accounting. The floor is the DRIVE's obligation; a task
  that ordered it would convert any unrelated red into this item's build-attempt cap.
- **Exactly ONE edit to `tests/test_name_gate.py`, and it is bounded.** Task 2 moves
  `len(REASONS) == 16` to `17`, updates the two numbers in that pin's own adjacent comment at `:121-122`
  ("fifteen … sixteen" → "sixteen … seventeen", the sentence's first half untouched) so the comment does
  not outlive its assertion, and adds `TimelineEntryRefusal`'s hierarchy assertions INSIDE the existing
  `test_name_gate_refusal_is_a_loud_fail_leaf_carrying_a_pattern`. The comment IS inside the bound — a
  literal reading that forbade it would leave the file asserting one number and explaining a different
  one. No new `def test_` in that module (the
  `check_module` uniqueness wall), no `ast`, no repository construction, and none of its other two checks
  touched — §9's inbound row states all four requirements and Task 11 RUNS them.
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
| **The library refuses an input HAL9000 accepts, and the first victim is HAL9000's own caller — after the cutover, when this tree's floor no longer watches it.** The five guards of §1.4 are deliberate over-refusals. | Low for `text` (a note name or a rendered sentence containing `-->` or `<!--`), very low for the discriminator cases (a counterparty name that is empty, whitespace or contains `:`), and lower still for M1's guard 5 (a `text` whose own line opens `## ` or `### ` — a sentence does not, and the one multi-line probe the capture accepts does not). | A HAL9000 write that succeeds today would raise post-cutover. | The guard set is pinned as a SET EQUALITY against the capture's `accept` probes (AC-1(c2), R1), so the exception cannot be widened one case at a time — and since M2 the PROBE SET ITSELF is pinned WHOLE, because an equality over a silently narrowed population retires this ratchet while the floor stays green: Task 3 asserts the `## Validation boundary` span's completeness by the whole-file `yaml`-fence accounting before reading a probe (§12 Rule 3, §0 R7), which matters because the cutover re-runs the capture. Each guard also has a stated reason (§1.4); guard behaviour is pinned twice more independently of the probe span (AC-1(c) per-guard, Task 3(c3)'s reach fixtures); the refusal is LOUD, never a silent drop; and the cutover item's first act re-runs the capture and diffs it, which is where a newly-diverging input surfaces. |
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

## Mitigation Folds — 2026-09-29

The current set, restated in place. TWO `kind: required` mitigations stand in the latest speaking
`## Threat Model` round (2026-09-29, round 3) — M1, re-emitted byte-identically on Task 2, and M2, new on
Task 3 — and both are folded below.

**M1.** The substance landed in the SAME edit as
this record (WI-142): `## Design` §1.1 declares `STRUCTURAL_LINE_PATTERN` with its bound derived and its
complement named, §1.4 carries it as guard 5 plus the rule total and the next-level sweep the generator
demanded (WI-226), Task 2 writes it, and Task 3's new clause (c3) ships the claimed match-shapes and the
near-misses through the module's own construction (WI-235) rather than resting on a refusal count.
*Restated 2026-09-29* after the spec review: the `work:` value is re-quoted from Task 2's current text,
which gained the `REASONS` pin obligation and a second `verify:` check name. Nothing about the mitigation
moved — §1.1's derivation is now stated as a strict SUPERSET rather than an exact union (the reviewer's
non-blocking note), which STRENGTHENS the coverage claim guard 5 rests on and adds no member to either
side of AC-1(c2)'s equality.
*Re-verified after the spec review's ROUND 2, and the record is unchanged because nothing it quotes
moved.* That round's two findings were both textual oracles over committed markdown (Task 7's phrase,
Task 3's selector) and are closed in the new §12; neither touches guard 5, `STRUCTURAL_LINE_PATTERN`,
§1.4 or Task 3's clause (c3). The `work:` value below was re-read against Task 2's CURRENT bytes this
round: Task 2's guard-5 paragraph and its Verify sentence are byte-identical to the quote, and this
round's only Task 2 edit — admitting the `REASONS` pin's adjacent comment at
`tests/test_name_gate.py:121-122` into the bounded edit — sits in a DIFFERENT paragraph the quote does
not reach. So the record stands as written rather than being re-cut.

```fold
id: M1
desc: TimelineEntry refuses a `text` carrying a line that matches `^#{2,3} `, because a markdown heading in the prose channel truncates or shadows the `## Timeline` span that the accessor (§3), the marker-anchored dedupe (AC-1(e)) and both new detectors (§5) all read through, silently hiding every older entry from all three; the guard refuses no probe the capture records as accepted, so AC-1(c2)'s set equality and the signed criteria frame are unmoved.
design: `text` contains a line matching `STRUCTURAL_LINE_PATTERN` (`^#{2,3} `) — a markdown heading in the prose channel truncates or shadows the `## Timeline` span that the accessor (§3), the marker-anchored dedupe (§2 branch 2) and both new detectors (§5) all read through, so it would silently hide every older entry on that note from all three.
landed: Task 2
work: Guard 5 is M1 and is written in this task, not a later one: `TimelineEntry.__post_init__` refuses a `text` containing a line matching `STRUCTURAL_LINE_PATTERN` (`^#{2,3} `, tested MULTILINE over the whole string — never `startswith`) with `pattern` `TEXT_STRUCTURAL_LINE_KEY`, because such a line truncates or shadows the `## Timeline` span the accessor, the marker-anchored dedupe and both new detectors all read through; `STRUCTURAL_LINE_PATTERN` has exactly two readers — this guard and `parse_entries`' body boundary (§1.3), deliberately the same constant so door and reader cannot drift — and `# `/`#### ` are outside it by construction (§1.1). Verify: Task 3's check is the oracle for the module — its clause (c3) is guard 5's; the second named check is the `REASONS` pin and the new leaf's hierarchy assertions, and this task is done when the module imports under the project interpreter, the new leaf is constructible, and both checks are green, verify: test_timeline_entry_reproduces_hal9000_render_and_validation_boundary test_name_gate_refusal_is_a_loud_fail_leaf_carrying_a_pattern
```

**What the M1 fold does NOT claim, stated because the modeler's own round already names the residual.** The
guard is on the WRITE door and is total there over its generator (§1.4's field sweep: `text` is the only
input that can introduce a line). A note that ALREADY carries such a line — hand-edited, or written
through the raw-string branch AC-1(f) preserves — remains invisible to the accessor and to
`intro_by_without_marker`, exactly as the modeler's first non-blocking note records; the exposure is
measured at zero by precondition 2 and the re-runnable predicate, not the fold, is what keeps it honest.

**M2, folded 2026-09-29, substance in the SAME edit as this record (WI-142).** The finding lands inside the
previous round's own fold — §12's next-level sweep declared a truncated span would "redden this item"
uniformly, and that is FALSE for `## Validation boundary`, where a PARTIAL truncation leaves AC-1(c2)'s
guard-set equality satisfied over a subset and silently retires the anti-widening ratchet §1.4, R1 and
`## Risk Analysis` row 2 all name. So it is closed one LEVEL up rather than as a clause (WI-226): §12 gains
**RULE 3** — every oracle derived from a selected span either fails on a truncation by construction, with
this document naming the assertion that does it, or carries an explicit completeness assertion — plus
**dimension (vii) FAIL DIRECTION** answered per span for all four selected spans, and **the level BELOW
(vii)** swept and declared (nine run-time-derived populations this plan quantifies over; eight were already
non-vacuous and the ninth, Task 7's emptied-population absence scan, is closed in this same edit by a member
pin). Task 3 asserts the accounting before any sample or probe is read; §0 gains **R7**; §1.4 and
`## Risk Analysis` row 2 now say that the ratchet's population is pinned whole; and the ONE byte-level
mechanism the modeler named is folded rather than left to build time — `select_fenced_blocks` RETAINS the
info string, because `fenced_blocks:1550` discards it at `:1554-1559` (read at its symbol this round) and
the whole-file leg must tell the capture's thirty-five `yaml` fences from its four `python` ones. That
retention's own reach is shipped as the sixth WI-235 battery in Task 3, since the accounting now rests on
it. The counts behind the expression were re-counted at source this round rather than carried: six
line-start `yaml` fences in `## Parity samples`, twenty-nine in `## Validation boundary`, thirty-five in the
file, the other four `python` — and no literal count is typed into the check, so a re-run capture that
probes more boundary values moves both sides together.

```fold
id: M2
desc: Task 3 asserts the COMPLETENESS of the `## Validation boundary` span it selects from the capture, so a truncated selection is RED rather than green over a narrowed probe set; today's non-vacuity clauses catch only a TOTAL loss, and a partial one leaves AC-1(c2)'s guard-set equality satisfied over a subset, silently retiring the anti-widening ratchet §1.4, R1 and Risk Analysis row 2 all name as what stops the over-refusal exception being widened one case at a time.
design: every oracle this item derives from a selected span either FAILS on a truncation of that span by construction — and this document names the assertion that does it — or carries an explicit completeness assertion, and for the capture's two spans the completeness assertion is the whole-file accounting: the number of `yaml`-info fences `select_fenced_blocks` returns over `## Parity samples` PLUS the number it returns over `## Validation boundary` EQUALS the number it returns over the whole file's text, with all three counts asserted non-zero.
landed: Task 3
work: COMPLETENESS FIRST, THEN NON-VACUITY (§12 RULE 3, M2). Before any assertion above reads a sample or a probe, assert the WHOLE-FILE ACCOUNTING over the capture: the number of `yaml`-info fences `select_fenced_blocks` returns over the selected `## Parity samples` text PLUS the number it returns over the selected `## Validation boundary` text EQUALS the number it returns over the whole file's text, with all three counts asserted non-zero — so a span truncated by a line-start `## ` introduced inside a fence is RED rather than green over a narrowed population. Type NO literal count and pin no occurrence figure: a re-run capture legitimately probes more boundary values and both sides of the accounting move with it (R1's own reason for refusing a probe count). This is the clause that keeps AC-1(c2)'s set equality from being satisfied over a SUBSET of the `accept` probes — the non-vacuity clauses below do not catch that, because they catch a TOTAL loss only and the equality holds over any subset — and it is therefore what holds the anti-widening ratchet `## Risk Analysis` row 2 names. Verify: the check raises when any sample's bytes are altered by one space (observe by hand-mutating a copy of the parsed dict in a scratch run, then revert), verify: test_timeline_entry_reproduces_hal9000_render_and_validation_boundary
```

**What the M2 fold does NOT claim.** The accounting pins the two spans of ONE file — the capture. It says
nothing about `docs/vault-fixtures.md`'s or `docs/wi-033-intro-corpus-baseline.md`'s spans, and those are
deliberately given no accounting: dimension (vii) states which assertion in each already FAILS on a
truncation (the PRESENT phrase, and the exactly-one-`yaml`-fence clause), and adding an assertion where the
existing one already fails is cost with no coverage. And the accounting's own residual is declared rather
than closed: the whole-file leg is a toggle walk, so it needs no line-start triple-backtick inside any fence
in the file — true today (the Appendix's `python` fence at `:474-603` carries none), and its violation is a
false RED, never a silent pass.

## Spec Review — 2026-09-29

**Recommendation: REVISE — return to spec writer (gaps to fix)**

Cold-start read at HEAD `be6e2fe`, from line 1, in full. Rulings on record: D3's inverted stored-dirty
trade, D7's accepted drift window and declined standing cross-repo checker, D8's open slug door with
`PARITY_KINDS` gating nothing, and §0's five reifications of the signed frame — each is a scope boundary I
route against and none is re-litigated below. This is the first spec-review round on this item; the
architect, AC red-team, data-premise and threat-model rounds carried forward from the document and from
`docs/timeline-entry-relocation-rounds.md` were read before I read the spec.

This is a strong document. The three findings below are all in the same narrow place — the INBOUND wall /
pin accounting around the files the item edits, and the shape of the tasks that close it — not in the
design, which I could not fault.

### Citation verification

Every `file:line` and symbol-anchored citation in `## Design`, `## Verified Diagnosis`, `## Implementation
Plan`, `§9` and `## Write Targets` was read at its cited location this round. All resolve and all quote
accurately. Spot-list of the load-bearing ones confirmed: `person.py:append_to_timeline:1452`,
`:1489-1493`, `:1499`, `:1502` (whole-file substring), `:1512-1537` (the string-insertion accommodation and
its round-trip warning), `:1543-1545` (prepend), `person.py:_split_frontmatter_fence:96`, `person.py:61`
(`get_section` already imported), `person.py:1270-1271`; `body_sections.py:4-9`,
`:SECTION_HEADING_PATTERN:36`, `:parse_body_sections:39`, `:get_section:137`; `name_gate.py:14-20`,
`:22-29`, `:31-36`, `:_refuse:174-192`, `:gate_write:359-360`, `:364-368`, `:373`, `:398`, `:400`,
`:WHATSAPP_PATTERN:90`, `3b` at `:437-446`, section 4 at `:448`; `errors.py:NameGateRefusal:106`,
`:122-128`, `:130-134`, `:REASONS:152`, `:bounded_message:177-188`; `models.py:34-35`, `:45-53`, `:53`,
`:56+`; `vault_io.py:read_note:641`; `writer.py:252`, `:385`, `:443`, `:494` (literally
`gate_write({}, declared_type=None, whole_record=False)`, inside `roundtrip_file:463` — so AC-3(b)'s
excluded-set equality and Task 6's `writer.py:roundtrip_file` anchor are both true as stated);
`lint_vault.py:38-60`, `:check_structural:366`, `:378-397`, `:399`, `:466-473`, `:475-503`,
`:check_timeline:740-745`, `:816`, `VaultFile.body` at `:116`/`:180`; `derivations.py:python_files_under:185`,
`:gate_call_declarations:1054`, `:_import_aliases:890`, `:_resolves_to:908`, `:modules_using_ast:632`,
`:frontmatter_write_arms:979`, `:skip_reason_literal_sites:1585`, `:character_class_strip_sites:1486`,
`:address_splitting_implementations:1338`; `fixture_vault.py:21-25`, `:44`, `:62-83`, `:320-326`, `:323-324`,
`:325`, `:353-359`, `:367`, `:NAME_POOL:591`, `:PROSE_ALLOWLIST:615`; `test_fixture_vault.py:_identity_text:994`,
`:1027-1036`, `:reach_files:386`, `:1353`, `:1383`, `:1392`, `:1414`; `test_lint_vault_fix_rules.py:252`,
`:288`, `:586`, `:818-822`, `:1703-1710`, `:1775`; `test_ac_interpreter.py:check_module:95-106`;
`test_stem_name_divergence_detector.py:38-40`; `pipeline-runners.yaml` (`seed_deps: [.venv]`,
`write_authority` = the four trees, no `commands:`, no `ac_runner:` — §8.3 is exactly right).

I also re-read the code for the PROPERTY each claim asserts rather than for the symbol's existence, per the
injected audit's own floor. Four results worth recording because they are the ones a wrong reading would
have shipped:

- **§1.3's `%-d` substitution is byte-identical.** `capture:150-167` is
  `f"### {entry.when.strftime('%B %-d, %Y')} [{entry.kind}]\n"`, and `%-d` is the no-pad day, which is
  `.day`. `%B` stays on both sides, so the locale note in `## Edge Cases` is correct rather than convenient.
- **AC-1(c2)'s guard set really has exactly five members, and M1 adds none.** I enumerated the capture's 29
  probes myself (14 `kind` / 7 `text` / 8 `discriminator`). The capture-ACCEPTED inputs this library
  refuses are `text` = `see --> here` and `<!-- forged -->`, and `discriminator` = `''`, `'   '`, `a:b` —
  five, exactly §0 R1's list. No accepted probe carries a `^#{2,3} ` line (the only multi-line one is
  `'line one\n\nline two'`, `capture:413-417`), so guard 5 adds a predicate and no member. M1's
  no-re-signature argument holds on a read, not on the modeler's narrative.
- **`PARITY_KINDS` equals the sample kinds.** Six samples across `{intro, intro-by, intro-to, note, merge}`
  (`capture:223-289`), and `HAL9000_PARITY_ANCHOR` equals the capture's declared HEAD at `capture:7`. R2's
  reification is the only satisfiable reading — `## Validation boundary` deliberately probes `deal-closed`.
- **The kind bound agrees.** `KIND_PATTERN` is `^[a-z][a-z0-9_-]{0,31}$` verbatim (`capture:62`), and the
  capture probes a 32-char kind ACCEPT and a 33-char kind REFUSE, so §1.1's 32-character bound is HAL9000's
  own and not a tightening.

Precondition 2's numbers all reproduce in the artifact (5664 files, 1314 person notes,
`introduced_by_frontmatter_carriers: 0`, legacy `intro` 86 with 22 marked, grammars 43/38/5, `intro-by` 1,
`intro-to` 0, `inside_timeline_section_by_kind` total, `marker_kind_mismatch_by_kind` all zero). All five
declared precondition paths are present in git HEAD. `docs/vault-fixtures.md:279` still reads "a `manager:`
or `introduced_by:` on a schema-drift or forward-compatibility note", so the fifth precondition's edit is
correctly still pending at the conductor's pause and `:1434`'s signed fence is untouched.

### Bar check

Walked every check of `docs/spec-quality-bar.md` (the doc's own list is the count). Checks 1, 2, 3, 4, 6,
7, 8, 9, 10, 11 and 12 are satisfied; Check 5 fails on two counts (findings 1 and 2), and Check 6's
WI-278 clause fails on one (finding 3).

Recorded because each was a live risk on this item and each came back clean:

- **Check 12 (AC drift).** The four `criteria` fences and `## Intent` are byte-identical to the frozen
  bytes in `docs/spec-reviews/WI-033-dave-review-2026-09-28.md`, preamble included, and I classified all
  five of §0's reifications against the taxonomy independently. None is strength-weakening (R1 keeps the
  set EQUALITY and adds a non-vacuity assertion; the signed four-predicate reading and the built
  five-predicate reading produce the same five probes on both sides, so the clause is green as SIGNED),
  none is an actor-swap, none narrows scope (R2 picks the only satisfiable of two readings — a member with
  no sample is RED either way), none swaps an oracle weaker, and R3/R4/R5 are additive statements that
  widen coverage rather than except an original. No escalation owed.
- **Check 11.** All four `## Verified Diagnosis` claims re-read and each artifact supports its specific
  claim, not merely the code's existence.
- **Check 4.** Thirteen edge-case categories resolved with Case/Decision/Reasoning, each carrying a named
  test. `OPEN: None`.
- **Check 3's WI-226 ruling sweep for M1.** The guard-5 ruling is stated on `## Design` §1.1, §1.4, the
  `## Approach` paragraph, Task 2, Task 3 clause (c3), `## Edge Cases`' trust-boundary decision,
  `## Risk Analysis` row 2, `### What this item does NOT do`, §8.4 and the fold record. No surface still
  asserts the four-guard behaviour. This is the most complete ruling sweep I have read on this item.
- **Write-Targets coverage (per-task extraction).** I extracted every task's targets and they are all
  declared, and every declared path has a task: T2 → `timeline_entry.py`/`errors.py`/`__init__.py`;
  T3, T4, T11 → `tests/test_timeline_entry.py`; T4, T5 → `repositories/person.py`; T5, T10 →
  `tests/test_introduced_by_accessor.py`; T6 → `name_gate.py`; T6, T10 → `tests/derivations.py`; T6, T7 →
  `tests/test_retired_key_gate_rule.py`; T7 → `fixture_vault.py` + `@Morvette Harkwell.md`; T8 →
  `scripts/lint_vault.py`; T9 → `tests/test_lint_vault_fix_rules.py`. No task's verify command writes
  anything. The one absent target is finding 1's, and it is absent because no task names the work at all.
- **Fold record M1.** `desc` is verbatim against the latest speaking `## Threat Model` round. I found both
  quotes where they claim to be and read the surrounding text: `design` is §1.4's guard-5 sentence
  faithfully, and `work` is Task 2's guard-5 paragraph faithfully. The mitigation is genuinely satisfied —
  Task 2 writes the guard and Task 3(c3) ships four claimed shapes, five near-misses and the span-loss
  consequence itself, which is the WI-235 form rather than a refusal count.
- **D9's fixture-pool constraint.** `Oskaline` and `Thrandell` are both existing `NAME_POOL` members
  (`fixture_vault.py:595`, `:598`), and the PAIR "Oskaline Thrandell" is no corpus note's name, stem, alias
  or title (grep over the tree), so it resolves to nothing and needs no census row. `Voxleaf` stays used by
  `@Voxleaf Ltd.md`, so the non-vacuity clause is unaffected. This was the most likely place for the
  fixture re-key to go wrong and the spec got it right.

### Blocking issues

1. **Task 2 adds a member to `errors.py:REASONS`, and `tests/test_name_gate.py:124` pins that population's
   SIZE by equality — the pin is named nowhere, the file is not a declared write target, and no task owns
   the edit.** §1.4 and Task 2 both require "ONE new member in `REASONS`"
   (`"a timeline entry field this package refuses"`), because `bounded_message` refuses any non-enumerated
   reason. `tests/test_name_gate.py:124` is literally `assert len(REASONS) == 16`, with the comment at
   `:121-122` declaring the pin deliberate: *"REASONS is a FROZEN population, so equality is the right pin:
   fifteen members before this item, sixteen after."* That module imports `REASONS` from
   `obsidian_schemas.errors` directly (`tests/test_name_gate.py:24-25`). So the moment Task 2 lands, this
   check is RED — and the document is wrong about it in three places at once:
   - §9's wall table names no row for `errors.py` or `REASONS`.
   - §9's conscious-pin sweep declares the countable corpora this item touches to be "the lint check-id set
     and the frozen fixture corpus" and states the obligation as "the auto-fixable rule set does not change,
     and the digest changes exactly once." `REASONS` is a third countable corpus this item alters, with a
     hardcoded count pin over it, and it is absent from that sweep.
   - `## Verification`'s derived Regression enumeration lists `tests/test_name_gate.py` among the modules
     that "must still pass" — filed under `obsidian_schemas/name_gate.py`, not under
     `obsidian_schemas/errors.py`, whose row returns only the four `tests/test_loud_fail_*.py` modules. The
     sweep's own predicate ("modules that name each `## Write Targets` path") reaches this module for
     `errors.py`; the paragraph asserts it stays green, and as specced it cannot.

   This is WI-202's founding shape exactly: a pin in a file the sweep reached, sitting in a function that
   never calls the declaring symbol, missed, and surfacing as floor RED at the last task with nothing in
   the document naming the work as owed. **Concrete fix:** add `tests/test_name_gate.py` as a `writes`
   fence; give Task 2 (or Task 12) the explicit obligation to move `len(REASONS) == 16` to `17` and to add
   the new leaf's own assertions beside `NameGateRefusal`'s; add a `§9` row for `errors.py:REASONS` naming
   that pin; widen `§9`'s conscious-pin sweep to declare `REASONS` (and `obsidian_schemas/__init__.py`'s
   `__all__`, whose pins I checked are membership-only — `tests/test_name_gate.py:156` — so it needs naming
   but no edit); and correct the Regression paragraph's `errors.py` row. State the obligation as a
   predicate, per the rule: *the enumerated-reason set grows by exactly one and every pin over it moves with
   it.*

2. **Task 12's verify step is the project's whole floor (WI-314).** Task 12 is "Run the floor command.
   Confirm it is GREEN with a case count no lower than Task 1's baseline", and its declaration is
   `verify: hand-run — … the whole-suite run plus three pin re-reads is an act recorded in the Build Log.`
   A whole-floor run is the DRIVE's obligation — the drive-end floor and the battery-at-every-cap-bind
   already own it — so the most a plan's last task may order is the item's OWN checks green. As written the
   task spends a build window per attempt on a run the builder can neither shorten nor fix, and it converts
   any unrelated red into this item's build-attempt cap. It also compounds finding 1: the `REASONS` RED
   arrives here, inside a task whose only remedy is a file the plan never authorised.

   **Concrete fix:** keep Task 12, drop the floor run from it, and narrow it to what it can actually own —
   the three pin RE-READS (`tests/test_lint_vault_fix_rules.py:822` still reads `len(pinned) == 7`,
   `CENSUS_SHAPE_TO_RULE`'s value set still equals the derived auto-fixable set,
   `docs/lint-vault-live-baseline.md` needed no edit) plus this item's own four AC checks green, declared as
   those check names rather than as `hand-run`. Task 1's baseline capture stays exactly as it is: WI-238
   asks for precisely that earlier task, and a baseline recording is not a floor assertion.

3. **Task 7 / AC-3(c) orders a fixture that reads the live `docs/**` corpus at run time and the spec names
   neither WI-278 arm nor the coupling (WI-278).** The assertion is that
   "`docs/vault-fixtures.md` … names `manager:` alone in the sentence at its undeclared-key example,
   asserted by the absence of the phrase `` `introduced_by:` `` outside that file's `criteria` fences."
   That is a whole-file ABSENCE pin over another item's tracked work-item document — one the archive-split
   leaf rewrites on ordinary ships (that same file declares its own drawer at
   `docs/vault-fixtures.md:3761`, and `docs/vault-fixtures-rounds.md` exists). It neither derives what it
   needs from the corpus's own code nor carries frozen bytes, and no leaf in this tree declares "text
   outside `criteria` fences", so the test rolls its own fence scan over a live population's shape. The
   failure mode is the one the rule exists for: green on the day it ships, RED weeks later on somebody
   else's entirely correct ship — and this item is the one that would be blamed.

   The document is otherwise scrupulous here: `## Verification`'s WI-278 paragraph declares the FROZEN-BYTES
   arm for AC-1's read of the capture in one falsifiable line. This second `docs/**` reader has no such
   line. **Concrete fix:** either narrow the assertion to a POSITIVE read of the `:279` sentence inside its
   own `## `-delimited section (derived by the same declared-heading selection AC-1 uses, not a whole-file
   scan), or keep the absence pin and add the one-line coupling declaration beside AC-1's, naming the
   predicate it pins (whole-file phrase absence outside `criteria` fences in
   `docs/vault-fixtures.md`) and the property it consumes.

### Non-blocking notes

- **`tests/test_lint_vault_fix_rules.py:113` is the `BASELINE` path constant, not the declared-headings
  parse the spec points a builder at.** §10, §11.1, Task 3 and AC-4(d) all cite `:113` as "its
  declared-headings parse of `docs/lint-vault-live-baseline.md`". The shape to copy is
  `baseline_sections` (`:1518`) plus `fenced_blocks` (`:1550`). Re-anchor to those symbols; a builder who
  opens `:113` finds a `Path` binding and has to hunt.
- **§1.3 and §2 disagree about which string the door's dedupe compares.** §1.3 says `dedupe_probe` "is the
  ONE string the door's dedupe test uses"; §2 branch 2 binds `probe = dedupe_probe(entry)` and then skips
  "iff any `Marker` … has a key equal to `dedupe_key(entry)`", leaving `probe` dead in the flow as written.
  Both readings behave identically, so nothing wrong can ship — but the reconciling implementation is worth
  naming outright: `any(m.source == dedupe_probe(entry) for m in parse_markers(timeline))`, since
  `Marker.source` is the canonical `<!-- {key} -->` line the same renderer emits.
- **Nothing in §1.3 returns "the key of a `Marker`", yet §2 and AC-1(b) both need one.** AC-1(b) asserts
  "`dedupe_key(entry)` equals that marker's reconstructed key", so as specced the `{kind}:{day}:{disc}`
  grammar gets re-spelled at the door AND in the test. A `Marker.key` property (or the `source ==
  dedupe_probe` route above) keeps the one-definition promise literal rather than approximate. It is
  outside AC-2(e)'s predicate either way — the key format carries no delimiter — which is exactly why no
  check would catch it.
- **§5 has the detectors call `get_section(vf.body, "Timeline")` but `scripts/lint_vault.py:38-43` imports
  `parse_body_sections` and not `get_section`.** One name to add to an existing import list; say so, or
  spell the call as `parse_body_sections(vf.body).get("Timeline")`.
- **`STRUCTURAL_LINE_PATTERN`'s bound is a strict SUPERSET of its readers' patterns, not "the exact
  union".** `^#{2,3} ` matches a bare `## ` or `### ` line, which `SECTION_HEADING_PATTERN` (`^## (.+)$`,
  needs a non-empty title) and `HEADING_PATTERN` (needs ` [kind]`) both reject. Immaterial to AC-1(c2) —
  no capture-accepted probe carries either shape, so neither side of the equality moves — and immaterial to
  the guard's purpose, since refusing a title-less heading line is harmless. But §1.1 states the claim as
  falsifiable and it is false as written; call it a superset whose extra members are inert, and the
  `# `/`#### ` complement argument (which I verified IS correct) survives unchanged.
- **§9's conscious-pin sweep does not name `tests/test_lint_vault_fix_rules.py:CORPUS_PINNED_ISSUES:809`.**
  It is a hardcoded per-note issue-count pin over the frozen corpus whose own comment at `:802-808` binds
  it to `CORPUS_DIGEST` — which Task 7 moves. I checked it: the re-key changes no
  `meeting_missing_from_timeline` count, so it is unmoved and needs no edit. Naming it is what makes the
  sweep's "the digest changes exactly once" predicate checkable rather than asserted. Same class as
  finding 1, at zero cost.

### Carried-forward notes

- **Architect round 4, note 1 (provenance-less `Person`)** — CLOSED by §0 R5 and §3 step 1 (mirror the
  door's two-step, refuse third). Verified the mirrored expression matches `person.py:1489-1493`.
- **Architect round 4, note 2 (anchored dedupe must be a READ)** — CLOSED by §0 R4 and §2 branch 4.
- **Architect round 4, note 3 / round 3 notes 1–2 (AC-1(c2)'s guard-set RHS; AC-1(a2)'s "kinds the capture
  holds")** — CLOSED by §0 R1 and R2, and I verified both reifications against the capture's own bytes
  rather than against the notes.
- **Threat modeler, note 1 (an `intro-by` entry ALREADY outside a `## Timeline` span is invisible to both
  the accessor and `intro_by_without_marker`)** — STILL OPEN as a deliberately accepted residual, recorded
  in §1.4's next-level sweep, in the fold record's "what the fold does NOT claim", and in `## Edge Cases`.
  Re-deferred because the exposure is measured at zero by precondition 2's re-runnable predicate and the
  standing instrument is named; the closing act belongs to whoever refreshes that measurement, and the
  typed door has zero callers until HAL9000 WI-082.
- **Threat modeler, note 2 (`IntroRecord.introducer` is attacker-influenceable and returned verbatim, so a
  consumer rendering it into HTML must escape it)** — STILL OPEN and correctly out of this tree. Re-deferred
  because the library must not sanitize on a consumer's behalf; it is recorded for HAL9000 WI-078 and
  orchestrator WI-194 to inherit.
- **Threat modeler, note 3 (the D7 window has a security reading: HAL9000's own door keeps accepting a
  marker-forging `text` until the cutover)** — STILL OPEN by D7's standing ruling. Re-deferred as ruled
  scope, not as a gap.
- **Data-premise residual 1 ("all 86 legacy `[intro]` entries are OUTBOUND" has no re-runnable
  predicate)** — STILL OPEN, governs no criterion. Re-deferred with the closing predicate already named
  (split the 86 by `^Introduced by ` versus `^Introduced to `, counts only), to be run at build-start
  re-grounding rather than bought as a round here.
- **Data-premise residual 2 (HAL9000 WI-082's mint is uncommitted in HAL9000's working tree)** — STILL
  OPEN and outside this tree. Re-deferred: the id is issued and `next_id` advanced, so precondition 4's
  record in this tree's HEAD is truthful; committing it is HAL9000's act.

```verdict
gate: spec-reviewer
verdict: REVISE
date: 2026-09-29
model: claude-opus-5
targets: Task 2, Task 12, Task 7, AC-3, #write-targets, #design
prior: none
basis: original
findings: 3/9
note: Task 2 adds a member to errors.py:REASONS while tests/test_name_gate.py:124 pins that population's SIZE by equality (`assert len(REASONS) == 16`, deliberate per its own comment) — the pin is in no §9 row, `REASONS` is absent from §9's conscious-pin sweep whose declared corpora are only the lint check-id set and the fixture corpus, the file is in no `writes` fence and no task owns the edit, and `## Verification`'s derived Regression paragraph asserts that very module stays green while filing it under name_gate.py rather than under errors.py, which its own sweep predicate reaches; Task 12's verify step is the whole project floor (WI-314), which is the drive's obligation and is also where finding 1's RED lands with no authorised remedy; and Task 7/AC-3(c) orders a whole-file absence pin over `docs/vault-fixtures.md` — another item's splitter-mutable tracked document — naming neither WI-278 arm nor the one-line coupling declaration it gives AC-1's capture read. Everything else verified clean: all 33 symbol citations re-read for the property each claim asserts, the five-member guard set and M1's zero-member addition enumerated from the capture's own 29 probes, `PARITY_KINDS` equal to the sample kinds, the anchor equal to the capture's HEAD, the AC frame byte-identical to the signed artifact with all five §0 reifications classified non-drifting, and D9's fixture-pool tokens confirmed in NAME_POOL.
```

## Spec Review — 2026-09-29 (round 2)

**Recommendation: REVISE — return to spec writer (gaps to fix)**

Cold-start read at HEAD `be6e2fe` with the working tree's 2026-09-29 fold, from line 1, in full.
Rulings on record: D3's inverted stored-dirty trade, D7's accepted drift window and declined standing
cross-repo checker, D8's open slug door with `PARITY_KINDS` gating nothing, §0's six reifications of the
signed frame, and round 1's own disposition of Task 1 (a baseline capture is not a floor assertion, WI-238)
— each is a scope boundary I route against and none is re-litigated below.

Round 1's three findings are all CLOSED, and I found each closed by re-reading the surfaces and the code
rather than by reading the fold's account of itself. Both findings below land in the material the fold
ADDED, and they are one class: **a textual oracle prescribed against a markdown file whose actual bytes
were not read at the granularity the oracle needs.** Neither is in the design, which I again could not
fault.

### Citation verification

Every `file:line` and symbol-anchored citation in `## Design`, `§9`, `## Implementation Plan`,
`## Verification` and `## Write Targets` was read at its cited location this round, and read for the
PROPERTY each claim asserts rather than for the symbol's existence. All resolve; all quote accurately.
The ones this round's fold newly depends on, confirmed:

- `tests/test_name_gate.py:124` is literally `assert len(REASONS) == 16`, inside
  `test_name_gate_refusal_is_a_loud_fail_leaf_carrying_a_pattern:109`, with the deliberate-equality
  comment at `:121-122` and the direct import at `:24-25`. §9's new row and Task 2's obligation are exact.
- **§9's "the ONLY size pin over `REASONS` in the tree" re-run, not accepted.** Grepping `REASONS` over
  every `*.py` returns `:124` as the one size pin; every other hit is `SKIP_REASONS` (a different object),
  the membership assertion at `:123`, `errors.py:152`/`:181-182`'s own guard, or prose. Confirmed.
- `tests/test_name_gate_wall.py:TOUCHED_TEST_FILES:1029` names `tests/test_name_gate.py` at `:1033` and
  feeds `_check_the_ast_capability_stays_single_homed` from
  `test_wall_membership_is_closed_by_running_each_walls_predicate:1057`;
  `tests/test_fixture_vault.py:_item_test_modules:1315` names it at `:1323` and feeds `:1353`, whose own
  docstring states the `def <name>(` substring rule §9's requirement (2) rests on. Both rows exact.
- **The `errors.py` Regression re-sweep is right and the old paragraph was wrong.** Running the
  paragraph's own predicate — modules under `tests/` naming `obsidian_schemas.errors` — returns exactly
  the SIXTEEN modules now listed, and `test_loud_fail_load.py` / `test_loud_fail_harness.py` are correctly
  absent.
- `tests/test_lint_vault_fix_rules.py`: `baseline_sections:1518`, `fenced_blocks:1550`,
  `CORPUS_PINNED_ISSUES:809` (with its `CORPUS_DIGEST`-binding comment at `:802-808`),
  `test_every_write_causing_detector_fires_exactly_on_its_declared_subjects:818` carrying
  `len(pinned) == 7` at `:822` and consuming `CORPUS_PINNED_ISSUES` through
  `_check_the_corpus_is_a_false_positive_floor:832`,
  `test_the_live_vault_baseline_is_committed_shaped_and_agrees_with_the_census:1634`, and the five
  containment clauses at `:287-336`. Task 12's "discharged by a STANDING check rather than a hand
  reading" is true of all three pins.
- The containment wall does NOT forbid a second `vault` binding — clause (iii) requires every binding's
  source to be `_temp_vault` (`:304`) — so §9's row and Task 9's additions agree with the shipped
  predicate.
- `obsidian_schemas/body_sections.py:SECTION_HEADING_PATTERN:36`, `:parse_body_sections:39`,
  `:get_section:137`; `person.py:append_to_timeline:1452`, `:1489-1493`, `:1499`, `:1502`, `:1507`,
  `:1512-1537`, `:1543-1545`, and `get_section` already imported at `person.py:61`;
  `scripts/lint_vault.py:38-43` importing `ENTITY_BODY_CONFIG`/`ensure_sections_exist`/
  `get_expected_sections`/`parse_body_sections` and NOT `get_section`;
  `lint_vault.py:check_structural:366` with the `read_error`/`parse_error` `continue` guards at
  `:378-397` and `no_frontmatter` at `:399-400`, and `VaultFile.frontmatter`/`.body` non-optional at
  `:115-116` — so §5's stated position is executable exactly as written.
- `CORPUS_COUPLING:` exists in the six shipped forms §10 names, at module granularity
  (`fixture_vault.py:3`, `test_fixture_vault.py:3`, `test_ac_interpreter.py:23`,
  `test_company_name_contract.py:15`, `test_identity_endgame.py:10`) and at check granularity
  (`test_lint_vault_fix_rules.py:1639`, `test_whatsapp_migration.py:1114`).
- `docs/vault-fixtures.md`: `## Exploration Notes` occurs exactly once (`:83`) and its span runs to
  `## Approach` at `:1120`, so `:279` is inside it; `introduced_by` occurs in that file exactly TWICE,
  `:279` and `:1434`; `:1434` is AC-5's `desc` under `## Acceptance Criteria` (`:1387`) and carries the
  same two-key phrase, so §0 R6's structural-exclusion argument is correct and load-bearing rather than
  decorative. The fifth precondition's edit is correctly still pending.

### Bar check

Walked every check of `docs/spec-quality-bar.md` (the doc's own list is the count). Checks 1, 2, 4, 7, 8,
9, 10, 11 and 12 are satisfied. Check 3 and Check 6's WI-278 clause fail on findings 1 and 2; Check 5's
build-runner-dry-run clause fails on both, since each leaves the builder a judgment call whose wrong
branch is RED against a file the cage cannot edit.

Recorded because each was a live risk and each came back clean:

- **Check 12 (AC drift).** The four `criteria` fences and `## Intent` are still byte-identical to the
  frozen bytes; §0 gained R6 and I classified it independently against the taxonomy. R6 is not
  strength-weakening — it replaces a whole-file ABSENCE pin with a POSITIVE section-scoped presence plus
  absence, which a deletion of the sentence now fails and the old oracle would have passed — not an
  actor-swap, not scope-narrowing in the criterion's sense (the criterion asks the sentence be UPDATED;
  the narrower oracle asserts more of that), and not an oracle-swap weaker. R1's five-predicate filter
  over the same five probes is unchanged. No escalation owed.
- **Check 3's WI-226 ruling sweep, run for all three of this round's folds.** Task 12's narrowing is
  stated in Task 12, `## Verification` and `## Scope Boundary`; the `REASONS` obligation in §9's table,
  §9's third corpus, Task 2, Task 11, `## Write Targets` and the Regression paragraph; R6's oracle in §0,
  §6, Task 7 and `## Verification`'s reader 2. I hunted for a surface still asserting a pre-fold
  behaviour and found none.
- **Write-Targets coverage (per-task extraction, re-run from scratch).** Every task's targets are
  declared and every declared path has a task, `tests/test_name_gate.py` now included. No verify command
  writes anything, and no plan task orders the whole floor.
- **Verify-declaration shape.** All twelve canonical tasks carry exactly one well-formed `verify:`; every
  check-arm name resolves to a real or plan-created check; Task 1's `baseline` and its reason are
  in-bounds; no `cmd:` arm is used, correctly, since `pipeline-runners.yaml` registers none.
- **Fold record M1.** `desc` is verbatim against the latest speaking `## Threat Model` round; I found
  `design` in §1.4 and `work` in Task 2 and read the surrounding text, and both quotes are faithful. The
  re-quote after the fold is accurate to Task 2's current bytes.
- **§9's third corpus and `CORPUS_PINNED_ISSUES`.** Both named, and the claim that the re-key moves no
  `meeting_missing_from_timeline` count is true — that detector reads Timeline-versus-attendees, not
  frontmatter keys, and `@Morvette Harkwell.md`'s pinned figure of 2 is untouched by an undeclared-key
  rename.

### Blocking issues

1. **Task 7's PRESENT assertion names a phrase that does not exist as a contiguous substring, because
   `docs/vault-fixtures.md` is hard-wrapped and the sentence spans a line break — and whether it ever
   becomes contiguous depends on a re-wrap nobody has been asked for.** Task 7 orders: assert the phrase
   `` a `manager:` on a schema-drift or forward-compatibility note `` is PRESENT in the selected section.
   The file's bytes at `docs/vault-fixtures.md:279-280` are:

   > `carry frontmatter keys no model declares — a `manager:` or `introduced_by:` on a schema-drift or`
   > `forward-compatibility note — which every enumeration over DECLARED fields misses by construction;`

   Deleting `` or `introduced_by:` `` — which is the whole of the precondition's instruction, and the
   instruction correctly says the edit is "ONE sentence and nothing else" — leaves
   `` a `manager:` on a schema-drift or `` at the end of `:279` and `forward-compatibility note` at the
   start of `:280`. The named phrase therefore contains a newline in the file and a literal substring test
   is RED. Re-wrapping the paragraph to the file's ~100-column fill moves the break to a different word;
   it does not remove it. The only wrapping under which the assertion passes is a deliberate line JOIN
   that nothing in §6, §0 R6, Task 7 or the precondition fence asks the conductor to perform.

   This is worse than an ordinary RED because the two halves sit on opposite sides of the cage: the
   builder owns the assertion and cannot touch the file, the conductor owns the file and is not told the
   wrapping is load-bearing, and the builder's only in-cage remedies are to weaken a spec-prescribed
   oracle or to burn attempts. Note the ABSENCE half is fine — `` a `manager:` or `introduced_by:` `` is
   contiguous on `:279` today — so the defect is one-sided and easy to miss by reading only the stale
   phrase.

   **Concrete fix (one clause, and it closes the class rather than the case):** state that both tests run
   over the selected section's text with runs of whitespace collapsed to a single space
   (`" ".join(section.split())`), with the two phrases normalized the same way — or, equivalently, drop
   the sentence-shaped phrases and assert the two tokens: `` `manager:` `` PRESENT and `` `introduced_by:` ``
   ABSENT within the selected section. Either is wrap-insensitive by construction and neither can be
   satisfied by deleting the sentence.

2. **Task 3 prescribes a selector shape that RAISES by construction on the very file it is pointed at.**
   Task 3 says the capture's two sections are selected "by the same declared-heading selection
   `tests/test_lint_vault_fix_rules.py:baseline_sections:1518` uses … (RAISING on a missing, duplicate or
   unmatched heading rather than returning an empty dict)". I read `baseline_sections` at its symbol: it
   is a TOTAL parse that walks every `line.startswith("## ")`, raises `unnumbered section heading` on any
   heading outside its declared table (`:1528-1536`), and raises `duplicate section ordinal` on a repeat
   (`:1537-1538`). It is correct for `docs/lint-vault-live-baseline.md`, a five-section machine artifact
   whose every heading is declared.

   `docs/wi-033-hal9000-timeline-entry-capture.md` is not that shape. Its line-start `## ` headings are
   `## Part 1 — source (verbatim, with line ranges)` (`:57`), `## Parity samples` (`:223`),
   `## Validation boundary` (`:290`), `## Appendix — the generator, verbatim` (`:470`) and
   **`## Part 1 — source (verbatim, with line ranges)` a second time at `:587`** — the latter at line
   start INSIDE the Appendix's `python` fence, where the generator's own triple-quoted literal emits the
   heading. `baseline_sections` is fence-unaware by design, so a faithful copy of it sees four unmatched
   headings and one duplicate and raises before it ever reaches a `yaml` fence. The two declared headings
   themselves are each present exactly once at line start, so the NARROW reading — locate only the named
   headings, ignore every other `## ` line, raise iff a named heading is absent or occurs more than once —
   works, and Task 7's own wording ("match the heading text exactly, RAISE if it is missing or
   duplicated") is already that narrow reading with "unmatched" dropped. Two tasks, two readings, one
   shipped symbol that implements the wrong one: the builder picks, and one of the two picks is RED
   against a conductor-committed file it cannot edit.

   This is the same class as finding 1 and it arrived the same way — last round's non-blocking note asked
   for a better symbol to copy, the fold supplied one, and the supplied symbol's actual behaviour was not
   checked against the target file's actual headings.

   **Concrete fix:** state the selector's contract in Task 3 in its own terms rather than by reference —
   *locate each NAMED heading by exact line-start match, raise if it is absent or occurs more than once,
   take its text to the next line-start `## `, and ignore every heading the section list does not name* —
   and say that `baseline_sections:1518` is the shape to copy for the RAISING discipline and
   `fenced_blocks:1550` for the per-section fence walk, not a function to transplant. Naming the capture's
   `## Part 1` / `## Appendix` headings and the `## Part 1` echo at `:587` in one parenthesis is what makes
   the narrowing checkable instead of a reader's inference. Task 7's wording already states the right
   contract and should be the one Task 3 mirrors, not the reverse.

### Non-blocking notes

- **The `REASONS` pin's own comment goes stale the moment Task 2 moves the number.**
  `tests/test_name_gate.py:121-122` reads "fifteen members before this item, sixteen after"; after Task 2
  it is wrong in both halves. `## Scope Boundary` bounds the edit to "`len(REASONS) == 16` to `17` … and
  no new `def test_`", which a literal builder reads as forbidding the comment touch. One sentence
  admitting the adjacent comment into the bounded edit removes the ambiguity; nothing machine-checked
  moves either way.
- **The precondition-5 fence and §6 quote the target sentence in words the file does not use.** Both
  render it as "a `manager:` or `introduced_by:` key"; the file says
  "a `manager:` or `introduced_by:` on a schema-drift or forward-compatibility note" — there is no "key".
  Task 7 quotes it correctly. Since that fence is the conductor's hand-edit instruction, it is the one
  place the quote most needs to be the file's bytes.
- **Task 7's section boundary is durable against the splitter but not against a fenced `## ` line.** §0 R6
  and `## Verification`'s reader 2 argue durability from the archive-split leaf's target
  (gate-round sections, not `## Exploration Notes`), which I verified. The residual the argument does not
  cover is finding 2's shape one file over: a line-start `## ` inside a fenced block anywhere in
  `:83-1119` would truncate the selected text early and redden this item on somebody else's correct ship.
  There is none today (the next line-start `## ` after `:83` is `## Approach` at `:1120`). A fence-aware
  boundary, or one line recording the measured absence as part of the coupling declaration, closes it at
  the same cost as the declaration already being written.

### Carried-forward notes

- **Round 1, note 1 (`:113` is a `Path` constant, not the declared-headings parse)** — CLOSED in §10,
  §11.1 and Task 3, re-anchored to `baseline_sections:1518` + `fenced_blocks:1550`, both of which I read
  at their symbols. The re-anchoring is correct; what it now needs is finding 2's contract.
  AC-4(d)'s surviving `:113` citation is signed text and is CORRECT as used there — it names the baseline
  document's path constant, which is exactly what that clause is disclaiming.
- **Round 1, note 2 (§1.3 and §2 disagreed on the dedupe comparand)** — CLOSED. §2 branch 2 now binds and
  compares `dedupe_probe(entry)` against `Marker.source`, and AC-1(b) pins that equality.
- **Round 1, note 3 (no route from a `Marker` to its key)** — CLOSED by `_compose_key` + `Marker.key`
  (§1.2, §1.3, Task 3(b)), with the one-expression argument stated where AC-2(e)'s scan cannot reach.
- **Round 1, note 4 (`get_section` not imported by `lint_vault.py`)** — CLOSED in §5, and I confirmed the
  import list at `lint_vault.py:38-43` is exactly the four names §5 says it is.
- **Round 1, note 5 (`STRUCTURAL_LINE_PATTERN`'s bound is a superset, not the union)** — CLOSED in §1.1,
  with the two inert extra members and the `# `/`#### ` complement both stated; the threat modeler's
  round 2 independently agreed this strengthens guard 5's coverage claim.
- **Round 1, note 6 (`CORPUS_PINNED_ISSUES` unnamed in the pin sweep)** — CLOSED in §9's second corpus
  and Task 12.
- **Architect round 4, notes 1–3 / round 3 notes 1–2** — remain CLOSED by §0 R1–R5; re-verified R1's
  five-member filtered set against the capture's probes and R2's sample-kind reading against
  `## Parity samples`.
- **Threat modeler, note 1 (an `intro-by` entry ALREADY outside a `## Timeline` span is invisible to both
  the accessor and `intro_by_without_marker`)** — STILL OPEN as a deliberately accepted residual.
  Re-deferred: exposure measured at zero by precondition 2's re-runnable predicate, the standing
  instrument is named, and the typed door has zero callers until HAL9000 WI-082.
- **Threat modeler, note 2 (`IntroRecord.introducer` is attacker-influenceable and returned verbatim)** —
  STILL OPEN and correctly outside this tree. Re-deferred: the library must not sanitize for a consumer;
  recorded for HAL9000 WI-078 and orchestrator WI-194.
- **Threat modeler, note 3 (the D7 window's security reading)** — STILL OPEN by D7's standing ruling.
  Re-deferred as ruled scope.
- **Threat modeler round 2, note 1 (the `REASONS` pin must move as an EQUALITY, never be loosened to
  `>=` or deleted)** — STILL OPEN as a disclosure for whoever reads the diff. Re-deferred: the document
  names the target value and states the obligation as a predicate, so the note's job is to tell a reviewer
  which of two legal-looking edits is the wrong one. I am restating it here so it survives into the build
  review.
- **Data-premise residual 1 ("all 86 legacy `[intro]` entries are OUTBOUND" has no re-runnable
  predicate)** — STILL OPEN, governs no criterion. Re-deferred with its closing predicate already named,
  to be run at build-start re-grounding.
- **Data-premise residual 2 (HAL9000 WI-082's mint is uncommitted in HAL9000's working tree)** — STILL
  OPEN and outside this tree. Re-deferred: the id is issued and `next_id` advanced, so precondition 4's
  record is truthful; committing it is HAL9000's act.

```verdict
gate: spec-reviewer
verdict: REVISE
date: 2026-09-29
model: claude-opus-5
targets: Task 7, Task 3, #design
prior: held
basis: folded-material
findings: 2/5
note: Round 1's three findings are all CLOSED and I verified each against the code rather than the fold's account (the `REASONS` size pin at tests/test_name_gate.py:124 is now owned by Task 2 with a write target, three §9 rows and a re-swept sixteen-module Regression row I re-ran; Task 12 drops the floor and its three pins are each discharged by a standing check I confirmed consumes them; AC-3(c)'s oracle is now positive and section-scoped). Both new findings land in the fold's own material and are one class — a textual oracle prescribed against a markdown file whose bytes were not read at the granularity the oracle needs. Task 7 asserts the phrase "a `manager:` on a schema-drift or forward-compatibility note" is PRESENT, but docs/vault-fixtures.md is hard-wrapped and that sentence spans :279-280, so after the conductor's one-sentence deletion the phrase still contains a newline and the literal test is RED, with the builder unable to edit the file and the conductor never told the wrapping is load-bearing (the ABSENCE half is contiguous on :279 and fine, which is what hides it). And Task 3 prescribes the `baseline_sections:1518` selector, which I read at its symbol: it is a TOTAL heading parse that raises on any heading outside its declared table, while the capture carries `## Part 1` at :57 and again at :587 inside the Appendix's python fence plus `## Appendix` at :470 — so a faithful copy raises before reaching a yaml fence, and Task 7's narrower wording of the same instrument is the reading that works, leaving the builder to pick between two tasks. Everything else verified clean: all citations re-read for the property each asserts, REASONS confirmed to carry exactly one size pin tree-wide, the containment wall confirmed to permit a second `vault` binding from the one door, the signed frame byte-identical with R6 classified non-drifting, and the M1 fold's two quotes confirmed faithful where they claim to be.
```

## Threat Model — 2026-09-29 (round 3)

**Recommendation: PROMOTE to threat-modeled**, with M1 re-emitted UNCHANGED on Task 2 and ONE new
required mitigation, M2, on Task 3. Both are declared below; a later declaration supersedes an earlier
one, so this round's pair is the operative set.

Round 3, cold-start at HEAD `be6e2fe` with the working tree carrying the spec-writer's SECOND 2026-09-29
fold — the spec review's round-2 findings, closed as one class in the new §12. Carry-forward read in full
before reviewing: my own rounds 1 and 2, the `## Mitigation Folds` record, both spec-review rounds, both
injection-hunter rounds, and behind those the architect's round 4, the AC red-team's round 2, the
`ac-signoff` fence (`ac_hash a2bb3913f2c8` — `## Intent` and all four criteria still FROZEN) and the
data-premise PROMOTE. **Disclosure about method:** this cage grants no shell, so I could not diff the
working tree against HEAD. I read the fold's new material at source instead — §12 end to end, the
restatements in Tasks 3, 7 and 12, §0 R6, reader 1 and reader 2 — and I re-read the capture's own
heading and fence structure rather than taking any round's account of it. That is the stronger read for
this round's finding, which is about bytes nobody had counted.

### Trigger check

Unchanged and still firing — five of nine: external input (`text`/`discriminator` originate in an inbound
third-party introduction; both new readers run over 5,664 untrusted vault files), persistence (every write
lands in a note through `vault_io`), trust-boundary crossing (the prose channel and the machine channels
rendered into one contiguous block), filesystem operations on user-owned files, and access control in the
weak sense (`gate_write` gains a refusal arm). Still not firing: no secrets, credentials, tokens or OAuth
scopes; no MCP scope; no network at all; no external message. Review run in full.

### M1, re-read: STILL CLOSED, and nothing in this fold went near it

I re-read the four surfaces that carry guard 5 rather than trusting the fold record's claim that they did
not move, and they are unmoved. `STRUCTURAL_LINE_PATTERN` is still `re.compile(r"^#{2,3} ", re.MULTILINE)`
(§1.1), still declared with exactly two readers and still a strict SUPERSET whose two extra members are
inert; §1.4's guard 5 still carries both silent effects (an injected `## `-prefixed line TERMINATES the
span, an injected duplicate heading SHADOWS it) plus the field sweep that makes the door TOTAL over its
generator; Task 2 still writes it and has not been deferred; Task 3's clause (c3) still ships four claimed
shapes, five near-misses and the span-loss CONSEQUENCE by string surgery outside the door. The
`## Mitigation Folds` record's own re-verification is therefore correct, and M1's `desc` is re-emitted
byte-identically because what it REQUIRES has not moved.

One property I re-derived this round rather than carrying: the near-miss set and the guard's reach still
agree with the readers. An indented `  ## x` is asserted to CONSTRUCT in (c3), and it is correctly a
near-miss on both sides — `SECTION_HEADING_PATTERN` (`^## (.+)$`) and §12 Rule 1's boundary test
(`line.startswith("## ")`) are each line-anchored, so an indented heading truncates nothing. The `# ` /
`#### ` complement is likewise still outside all of them.

### What this fold's new material does to the security posture

The fold's substance is §12: a per-oracle enumeration of every textual read this item makes over a
committed markdown file, plus two rules made total over that surface. Most of it is test-oracle
engineering with no threat surface, and I say which is which rather than waving at the set.

- **Rule 2 (whitespace normalization of every phrase oracle) is security-neutral and strictly stronger as
  a test.** Its only failure direction is a false RED — normalization can join unrelated text across a
  paragraph boundary, never delete a phrase that is present — and the ABSENT half it protects still pins
  the conductor's edit, since `introduced_by` occurs in `docs/vault-fixtures.md` exactly twice (`:279`,
  `:1434`) and `:1434` is excluded STRUCTURALLY by the section selection.
- **Rule 1's new helpers land in the containment-preserving shape.** `select_sections(text, names)` and
  `select_fenced_blocks(section_text)` take TEXT, not paths, so no file I/O enters `tests/derivations.py`
  — the module every check in §9's table imports — and the read stays in the check modules. Neither uses
  `ast`, so §9's single-homing row is unmoved, and Task 11 RUNS `modules_using_ast` over the final text of
  every edited file, which makes that machine-closed rather than asserted.
- **No new denial-of-service or disclosure surface.** Both helpers are single-pass line walks; `_HEX40`
  (`tests/test_lint_vault_fix_rules.py:1515`, read at its symbol this round) is a fixed-width class
  between lookarounds and backtracks nowhere. The RAISE messages Rule 1 prescribes quote a heading name
  from a conductor-committed document — no vault bytes, no note-derived identity, so mitigation 2's
  content-free-refusal property is untouched on the test side as well.
- **Task 12's narrowing still drops no security check.** All four of this item's AC checks remain its
  obligation, AC-1(c), AC-1(c2), AC-3(b) and AC-4(f) included.
- **AC-1(a3)'s HEAD read moved the right way.** A SET-singleton assertion over the file's 40-hex tokens is
  strictly stronger than "the first match": the capture declares the same HEAD four times (`:7`, `:59`,
  `:171`, `:179`), and a re-run capture that declared TWO different HEADs — the exact shape a botched
  staleness refresh produces — is now RED instead of green on whichever came first.

### The one new finding: the probe span's completeness is unasserted, and its loss is SILENT

This is M2. It lands in the fold's own material — §12's next-level sweep — and it is the FAIL-DIRECTION
dimension that sweep did not turn: *when a selected span truncates, is the check RED, or is it green over
a narrowed oracle?* §12 answers it once, uniformly, and the answer is right for three of the four oracles
and wrong for the fourth.

§12's Rule 1 declares its fence-unawareness as a residual and states the consequence generally: a
line-start `## ` introduced inside a fence in a selected span "would truncate that span early **and redden
this item** on somebody else's correct ship." I checked that claim per span rather than per section, and
it does not hold uniformly:

- **`## Exploration Notes` (oracle 3) — REDDENS.** Truncation drops the sentence, the PRESENT half fails.
  Fail-safe.
- **`## Counts` (oracle 4) — REDDENS.** Task 7 asserts the span yields EXACTLY ONE fence first, so a
  truncated span yields zero and is RED. Fail-safe, and it is the only oracle that already carries an
  explicit completeness assertion.
- **`## Parity samples` (oracle 1) — REDDENS, and not by accident.** AC-1(a2) asserts
  `PARITY_KINDS == {s["kind"] for s in samples}` against a frozen five-member constant, so a sample set
  short by one kind is RED. The sample span is protected by a criterion written for a different purpose.
- **`## Validation boundary` (oracle 1's refusal half, AC-1(c2)) — does NOT redden on a partial
  truncation.** Task 3's non-vacuity assertions are that the probe set is non-empty, that both verdict
  values are present, and that the guarded set is non-empty. Those catch a TOTAL loss. They do not catch a
  PARTIAL one: the equality `{p in accept if library_refuses(p)} == {p in accept if guarded(p)}` holds
  over any SUBSET of the probes, so a truncation that removes some but not all of the five guarded accept
  probes leaves AC-1(c2) green over a narrowed population.

**Why that is a security finding and not a tidiness one.** AC-1(c2) is not an ordinary parity test — it is
the ANTI-WIDENING RATCHET over the forgery guard set, and the document names it as such in three places:
§1.4 calls the equality the reason "the exception cannot be widened"; R1 says the FILTER is what makes a
sixth guard "show up on both sides"; and `## Risk Analysis` row 2 names it verbatim as what holds the
over-refusal risk — *"pinned as a SET EQUALITY against the capture's `accept` probes (AC-1(c2), R1), so the
exception cannot be widened one case at a time."* A silently narrowed probe set retires that ratchet while
the floor stays green, and the failure it would let through is the one row 2 describes: a library guard
that refuses an input HAL9000 accepts, whose first victim is HAL9000's own caller post-cutover, on the
inbound-introduction path where the counterparty string is third-party-supplied.

**The trigger is scheduled, not hypothetical.** D7's cutover item (HAL9000 WI-082) has as its FIRST ACT
"re-run the capture at HAL9000's then-HEAD, diff against the anchor" — so this artifact is certain to be
regenerated, and R1 correctly refuses a pinned probe count precisely because a re-run capture legitimately
probes more boundary values. The condition remains unlikely: `yaml.safe_dump` indents block scalars, so no
line inside a `yaml` fence begins at column 0, which is the structural reason §12's measurement holds
rather than a property of today's bytes. That is why this is a mitigation to fold and not a reason to
bounce the spec — and why I am requiring it rather than leaving a note, since the cost is one derived
assertion and the alternative is a stated control that weakens silently at a moment already on the
calendar.

**The closing shape, measured against the capture's bytes this round rather than prescribed by
reference** — which is the discipline §12 exists to enforce, and it would be a poor finding that violated
it. I counted the capture's line-start fences and headings myself. Its line-start yaml-info fences
are SIX inside `## Parity samples` (`:225`, `:236`, `:247`, `:258`, `:269`, `:279`) and TWENTY-NINE inside
`## Validation boundary` (`:292` through `:462`), thirty-five in the file and none anywhere else: Part 1's
three fences are `python` (`:61`, `:173`, `:181`) and the Appendix's one is `python` (`:474`, closed at
`:603`, with the `## Part 1` echo at `:587` inside it). So a whole-file accounting is available and exact
— *the two selected spans' yaml-fence counts SUM to the file's own line-start yaml-fence count* — and it
is position-free, wrap-insensitive, count-pin-free, and RED on a truncation of EITHER span whether the
truncating `## ` line sits inside a fence or outside one. It also survives a re-run capture that adds
probes, because both sides of the accounting move together. The requirement is the property; the spec
writer owns the expression. **One byte-level caveat the mechanism turns on, so it is not discovered at
build time:** `fenced_blocks:1550` DISCARDS the info string — the opening fence line is consumed by the
triple-backtick `startswith` branch at `:1554-1559` and never appended — so a `select_fenced_blocks` copied as
written cannot tell a `yaml` fence from a `python` one. §11.1 nonetheless asks for "every fenced block
whose info string is `yaml`". That is inert inside the two selected spans, where every fence is `yaml`,
but the whole-file leg of this accounting needs the info string, so it must be retained or taken by a
separate line-anchored match.

### STRIDE re-read — deltas only

The five axes rounds 1 and 2 verified clean verified clean again on the same reads; I record only what
this fold changed.

**Tampering.** Unchanged on the product. Guard 5 still closes the section channel at the write door and
the door is still TOTAL over §1.4's field generator. The lock discipline is untouched: one `note_lock`
spanning read, dedupe and write with `precondition=_stamp`
(`obsidian_schemas/repositories/person.py:1498-1546`), so the TOCTOU shape still does not exist. What this
fold touches on this axis is the INTEGRITY OF THE PIN over the guard set, which is M2 — the finding is
about the assurance artifact, not about a path an attacker walks, and I say so plainly rather than dressing
it as a product tampering vector.

**Repudiation.** Unchanged and slightly better served: the `REASONS` obligation Task 2 now owns is
stated as a predicate with the target value named, and Task 12 re-reads the pins through STANDING checks
rather than a hand reading, so the pin accounting is itself recorded rather than attested.

**Information disclosure.** Unchanged. `refused_value` still carries the constant key and never a
person's name (D4, `obsidian_schemas/name_gate.py:_refuse:174-192`); the three detector messages still
name the key or the heading and never a stored value; and the new test-side helpers introduce no message
carrying vault content.

**Spoofing, Denial of service, Elevation of privilege.** Unchanged and unchallenged by the fold. The
marker remains an unauthenticated channel over a trusted store with `IntroRecord.source` pinned to the
bytes on the page as the audit route; both module patterns stay line-anchored with no nested quantifier
and the readers stay total over 5,664 files; and the accessor's path resolution is contained on both legs
(`repositories/base.py:406-414`'s `is_relative_to` check and `:379-390`'s dict lookup — neither joins a
caller string onto a path).

### Mitigations verified in place

The standing set, re-verified this round. 1. Marker-channel forgery closed at construction (§1.4 guards
1–4, pinned by AC-1(c) and enumerated as a set equality by AC-1(c2), on inputs HAL9000 itself accepts).
2. Refusals carry no note-derived content (§1.4, D4), enforced by `bounded_message`'s enumerated reasons
and its `from None` suppression (`obsidian_schemas/errors.py:177-188`) and by `_refuse`'s rules 1–3,
extended to the new leaf by Task 2's hierarchy assertions. 3. Fail-closed on the write path, total on the
read path (validation in `__post_init__`; AC-3(b) asserts NO FILE CHANGED at all five driven arms).
4. Path containment on the new read (`base.py:406-414`, `:379-390`). 5. Atomicity and lock discipline
unchanged (`person.py:1498-1546`; the accessor's unlocked read sanctioned and non-torn,
`vault_io.py:641-663`). 6. Untrusted-byte readers raise nothing and build nothing (§1.3, §8.4), with the
linter's triage order preserved by placement (`scripts/lint_vault.py:378-397`) and asserted by AC-4(f).
7. The section channel closed at the write door — M1, re-emitted below.

Note which of these M2 protects rather than adds to: mitigation 1's guard set is verified in place on a
READ, and AC-1(c2) is what keeps it from being WIDENED later. M2 is about that second property only.
Guard behaviour itself is pinned twice more, independently of the probe span — AC-1(c) asserts each of the
five guards raises with its named pattern, and Task 3's (c3) ships guard 5's reach as fixtures — which is
why a narrowed (c2) is a ratchet loss rather than a loss of the guards.

### Required mitigations

```mitigation
kind: required
id: M1
desc: TimelineEntry refuses a `text` carrying a line that matches `^#{2,3} `, because a markdown heading in the prose channel truncates or shadows the `## Timeline` span that the accessor (§3), the marker-anchored dedupe (AC-1(e)) and both new detectors (§5) all read through, silently hiding every older entry from all three; the guard refuses no probe the capture records as accepted, so AC-1(c2)'s set equality and the signed criteria frame are unmoved.
landed: Task 2
```

```mitigation
kind: required
id: M2
desc: Task 3 asserts the COMPLETENESS of the `## Validation boundary` span it selects from the capture, so a truncated selection is RED rather than green over a narrowed probe set; today's non-vacuity clauses catch only a TOTAL loss, and a partial one leaves AC-1(c2)'s guard-set equality satisfied over a subset, silently retiring the anti-widening ratchet §1.4, R1 and Risk Analysis row 2 all name as what stops the over-refusal exception being widened one case at a time.
landed: Task 3
```

M1 is re-emitted byte-identically and stays on Task 2, the task that writes guard 5. M2 lands on Task 3
because Task 3 is where `select_sections` and `select_fenced_blocks` are written and where the capture's
two spans are consumed; the sibling assertion already exists one clause away, in Task 7's "assert the
section yields EXACTLY ONE fence first", so the fold is a clause in a check this task already ships and
touches no frozen fence. It needs no re-signature for the same reason M1 did not: AC-1(c2) is a set
equality over the capture's accept probes and a completeness assertion adds no member to either side of
it — it asserts that the population both sides are drawn FROM was read whole.

### Notes (non-blocking)

- **`## Parity samples`' protection against the same truncation is incidental, and worth knowing is
  incidental.** AC-1(a2)'s set equality catches a short sample set only because `PARITY_KINDS` is a frozen
  five-member constant; if a future capture legitimately added a sample for a sixth kind and the constant
  moved with it, the coincidence still holds, but nothing in the document says the sample span's
  completeness is (a2)'s job. M2's accounting covers both spans in one expression, which is why I
  specified it over both rather than over the probe span alone.
- **The `REASONS` pin must move as an EQUALITY, not be loosened.** Carried from round 2 and restated
  because the build has not happened yet: satisfying `tests/test_name_gate.py:124` by rewriting `== 16` as
  `>= 16`, or deleting it, would silently retire the size bound on the enumeration that keeps composed,
  note-content-bearing strings out of the hierarchy (`bounded_message`'s `from None` suppression fires
  "while a note-content-bearing original is in flight", `obsidian_schemas/errors.py:183-188`). Not a
  required mitigation: the document names the target value `17`, `## Scope Boundary` bounds the edit to
  that line plus the adjacent comment plus assertions inside the existing check, and §9 states the
  obligation as a predicate. Recorded so the reviewer reading the diff knows which of two legal-looking
  edits is the wrong one.
- **The honesty invariant's residual is unchanged and still not closed by M1**: an `intro-by` entry
  ALREADY outside a `## Timeline` span — hand-edited, or written through the raw-string branch AC-1(f)
  preserves — is invisible to the accessor AND to `intro_by_without_marker`, which only scans inside the
  span. Still not requiring a mitigation: the exposure is MEASURED at zero (precondition 2 reports every
  live timeline heading sitting inside a `## Timeline` section) and the predicate is re-runnable. Worth
  the cutover item's attention if the typed door gains a caller before that measurement is refreshed.
- **`IntroRecord.introducer` is attacker-influenceable and returned verbatim** — a consumer rendering it
  into HTML must escape it. Correctly not the library's job; recorded so HAL9000 WI-078 and orchestrator
  WI-194 inherit the fact rather than discover it.
- **The D7 window's security reading stands.** Until HAL9000 WI-082 ships, HAL9000's own door keeps
  accepting a `text` that forges a marker (`capture:401-403`), so the forgery guards protect only callers
  routing through this library. Correct sequencing and ruled scope; the hole does not close estate-wide
  until the cutover.
- **Two OPEN security questions is the role's cap; I am at zero.** Every note above carries a stated
  disposition, and this round's one finding is a declared required mitigation rather than an open
  question.

```verdict
gate: threat-modeler
verdict: PROMOTE
date: 2026-09-29
model: claude-opus-5
note: M1 re-read and STILL CLOSED on the surfaces themselves (§1.1's pattern, §1.4's guard 5 with both silent effects, Task 2, Task 3(c3)) and re-emitted byte-identically on Task 2; of the fold's new material §12 is security-neutral-to-positive on every axis I could check — Rule 2 can only false-RED, Rule 1's helpers take TEXT not paths so no file I/O enters tests/derivations.py and no `ast` moves, the RAISE messages quote conductor-committed headings and never vault bytes, Task 12's narrowing drops no security check, and AC-1(a3)'s SET-singleton HEAD read is strictly stronger than the first match. The one new finding is the FAIL-DIRECTION dimension §12's next-level sweep did not turn: it declares span truncation would "redden this item" uniformly, and I checked that per span rather than per section — true for `## Exploration Notes` (the PRESENT half fails), `## Counts` (one-fence assertion) and `## Parity samples` (AC-1(a2)'s set equality, incidentally), but FALSE for `## Validation boundary`, where the non-vacuity clauses catch only a TOTAL loss and a partial truncation leaves AC-1(c2)'s equality satisfied over a subset — silently retiring the anti-widening ratchet §1.4, R1 and Risk Analysis row 2 all name as what stops the over-refusal exception being widened, on a regeneration D7 has already scheduled as the cutover item's first act. That is M2 on Task 3, a mitigation to fold rather than a spec gap: the guards themselves stay pinned by AC-1(c) and (c3) so it is a ratchet loss not a guard loss, safe_dump's block-scalar indentation keeps the condition unlikely, and the closing shape is one derived assertion I measured against the capture's own bytes (six yaml fences in the sample span, twenty-nine in the probe span, thirty-five in the file, the other four fences `python`) rather than prescribed by reference — with the caveat that `fenced_blocks:1550` discards the info string at `:1554-1559`, which the whole-file leg needs. Seven prior mitigations re-verified in place, zero open security questions.
```

## Spec Review — 2026-09-29 (round 3)

**Recommendation: PROMOTE to ready**

Cold-start read at HEAD `be6e2fe` with the working tree carrying the spec-writer's THIRD 2026-09-29
fold (the threat model's round-3 M2), from line 1, in full. Rulings on record: D3's inverted
stored-dirty trade, D7's accepted drift window and declined standing cross-repo checker, D8's open slug
door with `PARITY_KINDS` gating nothing, §0's seven reifications of the signed frame, round 1's
disposition of Task 1 (a baseline capture is not a floor assertion, WI-238), and §12's deliberate
declining of a fence-aware span boundary — each is a scope boundary I route against and none is
re-litigated below.

Round 2's two findings are CLOSED, and I found each closed by reading the target files at the
granularity the oracle consumes rather than by reading the fold's account of itself. I found no
blocking gap this round.

### Citation verification

Every `file:line` and symbol-anchored citation in `## Design`, `§9`, `§12`, `## Implementation Plan`,
`## Verification` and `## Write Targets` was read at its cited location, and read for the PROPERTY each
claim asserts rather than for the symbol's existence. All resolve; all quote accurately. The injected
drift audit reported 0 findings over 75 citations, which I treated as a floor rather than a pass.

The measurements this round's fold newly rests on, **re-counted at source rather than carried from any
round's narrative** — this is the discipline §12 exists to enforce and a review that took the numbers on
trust would be the same defect one level out:

- **§12 Rule 3's accounting is exact against the capture's bytes.** Line-start fences in
  `docs/wi-033-hal9000-timeline-entry-capture.md`: `yaml` opens at `:225`, `:236`, `:247`, `:258`,
  `:269`, `:279` (SIX, all inside `## Parity samples`) and at `:292`…`:462` (TWENTY-NINE, all inside
  `## Validation boundary`) — thirty-five in the file — with the other four opens `python` (`:61`,
  `:173`, `:181`, and the Appendix's `:474`, closed at `:603`). Thirty-nine fences, seventy-eight
  line-start delimiters, strictly alternating, so the whole-file toggle walk is well-formed and
  `6 + 29 == 35` holds as stated. I also confirmed the assertion actually FAILS the way Rule 3 claims:
  an injected line-start `## ` is not a fence line, so a truncated span's count drops while the
  whole-file count does not.
- **The capture's headings are what Rule 1 says.** `## Part 1 …` at `:57` and AGAIN at `:587` (inside the
  Appendix's `python` fence), `## Parity samples` at `:223`, `## Validation boundary` at `:290`,
  `## Appendix …` at `:470`. Each of the two NAMED headings occurs exactly once at line start, and
  neither selected span (`:224-289`, `:291-469`) contains a line-start `## ` line — so the narrow
  selector is total over what it needs and `baseline_sections`' total parse would indeed raise before
  reaching a fence.
- **`fenced_blocks:1550` really does discard the info string.** Read at its symbol: the opening line is
  consumed by the `line.startswith("```")` branch at `:1554-1559` and never appended to the block. So
  §12's one declared deviation — `select_fenced_blocks` returning `(info, block)` PAIRS — is load-bearing
  rather than decorative, and Rule 3's whole-file `yaml`-versus-`python` leg is inexpressible without it.
  `baseline_sections:1518` raises `unnumbered section heading` at `:1530` and on a non-matching declared
  prefix at `:1533-1536`, and `duplicate section ordinal` at `:1538`; `_HEX40:1515` is
  `(?<![0-9a-fA-F])[0-9a-f]{40}(?![0-9a-fA-F])`, the shape AC-1(a3)'s singleton assertion copies.
- **The other two oracle files hold their claimed shapes.** `docs/vault-fixtures.md`:
  `## Exploration Notes` once at `:83`, next line-start `## ` is `## Approach` at `:1120` (span
  `:84-1119`, holding `:279`), first line-start fence in the whole file at `:1288` — so the fenced-`## `
  residual is measured at zero as declared; `introduced_by` occurs exactly TWICE (`:279`, `:1434`); and
  `:279-280` still read verbatim "a `manager:` or `introduced_by:` on a schema-drift or /
  forward-compatibility note", so the wrap really does split the corrected phrase and Rule 2's
  normalization is what makes the PRESENT half executable. `docs/wi-033-intro-corpus-baseline.md`:
  `## Counts` at `:56`, `## Verbatim output` at `:117`, span `:57-116` holding exactly ONE fenced block
  (the `yaml` one at `:61-115`) — so Task 7's exactly-one-fence clause is satisfiable and is genuinely
  what makes that oracle RED on a truncation.
- **The product-side citations the plan writes against.** `person.py:append_to_timeline:1452` with
  `formatted_entry = entry if entry.startswith("\n") else f"\n{entry}"` at `:1510` (so `render`'s
  `### `-leading bytes take the same one-newline prefix every live caller gets, and the marker still
  lands alone on its line), `:1489-1493`, `:1502`, `:1512-1537`, `:1543-1545`;
  `person.py:_split_frontmatter_fence:96` returning `(raw_frontmatter, raw_body)` and raising
  `FrontmatterParseError` — which `append_to_timeline`'s own `except LoudFailError: raise` at `:1551`
  re-raises unwrapped, so §2 branch 2's new read does not get laundered into `WriteFailedError`;
  `body_sections.py:get_section:137` as `parse_body_sections` one frame in.
- **The fixture re-key's constraints.** `tests/fixtures/vault/@Morvette Harkwell.md:16` is
  `introduced_by: "Voxleaf"` and the note's body is the default three sections (so P4's zero-entries
  premise still holds); `tests/fixture_vault.py:320-326` is the single `undeclared` declaration with the
  AC-5(b) comment at `:323-324`; `Oskaline` (`:595`) and `Thrandell` (`:598`) are both `NAME_POOL`
  members and the PAIR is no corpus note's name, stem, alias or title, so D9's constraint holds and no
  census row is owed.
- **`tests/test_name_gate.py`** is `assert len(REASONS) == 16` at `:124` inside
  `test_name_gate_refusal_is_a_loud_fail_leaf_carrying_a_pattern:109`, with the "fifteen … sixteen"
  comment at `:121-122` and the membership assertion at `:123` and `__all__` membership at `:156`. Task
  2's obligation and §9's rows are exact.
- **The two new derivations move no wall.** `tests/test_loud_fail_harness.py:79-88`'s `six` dict is a
  REQUIRED SUBSET by its own docstring at `:18-20` ("not a cardinality bound on the module"), so four
  additions to `tests/derivations.py` leave `len(six) == 6` untouched; the binding assertion is
  `modules_using_ast(python_files_under(PACKAGE_ROOT, TESTS_ROOT)) == {"tests/derivations.py"}` at
  `:103-113`, which §9 row 1 names and Task 11 RUNS. Neither helper touches `ast`.

### Bar check

Walked every check of `docs/spec-quality-bar.md` (the doc's own list is the count). All twelve are
satisfied. Recorded because each was a live risk on this item and each came back clean:

- **Check 12 (AC drift).** The four `criteria` fences and `## Intent` are unedited this round — AC-1(c)
  still names FOUR guards and AC-1(c2) still names the same four-member exception, with guard 5 and the
  completeness assertion carried entirely in unsigned prose; spot-compared AC-1(c2) and AC-3(c) against
  `docs/spec-reviews/WI-033-dave-review-2026-09-28.md:78-82` and `:329-333` and both are byte-faithful.
  I classified the NEW reification, **R7**, independently against the taxonomy: it is not
  strength-weakening (it adds a completeness precondition to an equality that keeps its form), not an
  actor-swap, not scope-narrowing, not an oracle-swap weaker (it is strictly stronger — the old clause
  was green over a narrowed population), and not exception-carving-by-addition. No escalation owed.
- **Check 5's class-fold clause (WI-226), which is the one this round turns on.** M2's finding landed
  inside §12 — the previous round's own fold — and the writer closed it ONE LEVEL UP rather than as a
  clause: §12 gains Rule 3 stated over the whole member set, dimension **(vii) FAIL DIRECTION** answered
  PER SPAN for all four selected spans, and **the level below (vii)** swept and declared (nine
  run-time-derived populations, eight already non-vacuous, the ninth — Task 7's emptied-population
  absence scan — closed in the same edit by a MEMBER pin rather than a size pin). That is the enumerate-
  then-sweep-the-next-level shape the rule asks for, and the sweep DECLARED what it found rather than
  reporting a clean census.
- **Check 3's WI-226 ruling sweep, run for this round's fold.** The pre-fold claim — that a truncated
  span "would redden this item" uniformly — is corrected on every surface that stated it: §12 Rule 1's
  bullet, §12 dimension (ii) and (vii), `## Verification`'s reader 1 and reader 2, `## Risk Analysis`
  row 2, §1.4, §0 R7, `## Edge Cases`' new truncation bullet, Task 3 and the `## Mitigation Folds`
  record. I hunted for a surface still asserting the uniform reading and found none. Same for the
  `select_fenced_blocks` deviation: §11.1, §12, §10, Task 3, Task 7 and the `tests/derivations.py`
  `writes` fence all say PAIRS, and none still describes a bare-block copy.
- **Check 5's fold records (WI-216).** Both `kind: required` mitigations of the latest speaking round
  (round 3: M1 on Task 2, M2 on Task 3) carry complete records. Both `desc` values are byte-identical to
  the round-3 `mitigation` fences. I found each `design` and `work` quote WHERE it claims to be and read
  the surrounding text: M1's `design` is §1.4's guard-5 sentence and its `work` is Task 2's guard-5
  paragraph; M2's `design` is §12 Rule 3's stated rule at its own line and its `work` is Task 3's
  COMPLETENESS-FIRST paragraph with that task's verify text appended. Both mitigations are genuinely
  satisfied, not merely recorded — and M2's satisfaction is what I re-derived from the capture's bytes
  above rather than from the fold's claim.
- **Check 5's WI-314 clause.** No plan task orders the whole floor. Task 12 asserts this item's own four
  AC checks plus two STANDING checks carrying the pin accounting, and I confirmed both consume the pins
  they are claimed to (`…fires_exactly_on_its_declared_subjects:818` reaching `len(pinned) == 7` at
  `:822`, and `…baseline_is_committed_shaped_and_agrees_with_the_census:1634`).
- **Check 5's WI-238 clause.** No task's verify writes: every declaration is a check name or a `baseline`
  reason, and the two `docs/**` readers are reads.
- **Check 6's WI-235 clause.** SIX counting walls, each shipping its claimed shapes through the wall's
  OWN predicate plus a near-miss. The sixth — `select_fenced_blocks`' INFO STRING — is the one this round
  added, and it earns the battery for exactly the reason the document gives: the accounting is a
  `yaml`-versus-`python` discrimination and "it works on the capture" is satisfied identically by a
  helper that discriminates and one that returns every fence, since every fence in both selected spans
  is `yaml`. The INDENTED triple-backtick near-miss is the right one, because the shipped shape is
  `line.startswith`, not `line.strip().startswith`.
- **Check 6's WI-278 clause.** Four oracles over three files, enumerated by predicate in §12, each
  naming its arm and carrying a coupling declaration in `## Verification` and in the code (module
  granularity for `tests/test_timeline_entry.py`, check granularity inside
  `test_the_write_gate_refuses_the_retired_introduced_by_key`), both in shipped forms I confirmed exist.
- **Check 6's WI-254 clause.** The family — this tree's fence walks — is named, and the member left alone
  (`fenced_blocks:1550`, another module's private helper) is named with its reason rather than glossed.
- **Write-Targets coverage (per-task extraction, re-run from scratch).** Every task's target is declared
  and every declared path has a task; this round added no path, correctly, since `select_sections` and
  `select_fenced_blocks` land in an already-declared `tests/derivations.py`. The fifth
  `kind: precondition` fence carries no `grounds:` line and owes none — it declares a DELIVERABLE the
  conductor lands, not evidence a premise rests on, and the linter's `grounds:` rules fire only on a
  present-but-malformed value or on a non-precondition fence.
- **Verify-declaration shape.** All twelve canonical tasks carry exactly one well-formed `verify:`; Task
  1's `baseline` reason is 159 characters and in-bounds; the longest check arm is Task 12's six names;
  no `cmd:` arm is used, correctly, since `pipeline-runners.yaml` registers none.
- **Review level.** The fences name the real touch surface — five conductor paths plus thirteen builder
  paths, and nothing in the plan writes outside them.

### Build-runner dry-run

Walked the Implementation Plan top-to-bottom. Tasks 1–12 each name concrete files, concrete symbols and
a runnable verify. Three questions I wrote down before checking whether the document answers them:

1. *"The accounting clause tells me to count `yaml`-info fences over the whole file — with what?"* —
   answered: `select_fenced_blocks` over `Path.read_text()`, filtering `info == "yaml"`, no literal typed.
2. *"`select_sections` raises on a duplicate NAMED heading — does the capture's `## Part 1` echo at `:587`
   make it raise?"* — answered explicitly in Rule 1 and in Task 3's battery, which asserts a duplicate of
   an UNNAMED heading must NOT raise.
3. *"Which arm of AC-3(c) reads `docs/wi-033-intro-corpus-baseline.md`, and what if the `## Counts` span
   holds two fences?"* — answered: Task 7 asserts exactly one `yaml`-info fence BEFORE reading it.

No judgment-call gap detected. The three residual ambiguities I did find are below and none of them can
ship a wrong library under either reading.

**On the arc, since it is the factory's own question and this is round 3.** The series is round 1 on
original material (3 findings), round 2 on the fold's material (2 findings), and the threat model's round
3 inside §12 itself (M2). That is a ladder climbing toward the machinery, and a fourth round landing on
the accounting's expression would have been the regress signature rather than progress. I looked for one
specifically — Rule 3's fail direction, its behaviour under a legitimately regenerated capture, and the
level below it — and found it sound: the expression is position-free, count-pin-free, RED on a truncation
of either span inside or outside a fence, and it moves with the re-run capture D7 has already scheduled.
The ladder is closed, not paused.

### Minor notes (non-blocking)

- **§2 branch 1's `BOTH_ENTRY_AND_KEY_KEY` has no declared home.** §1.4 enumerates eight `pattern`
  literals as module-level constants in `timeline_entry.py` and this ninth appears only in §2, raised
  from the door rather than from the module; its `REASONS` reason ("a timeline entry field this package
  refuses") is also a slight stretch for a two-arguments fault rather than a field one. Nothing asserts
  the literal — `## Verification`'s failure-mode line pins only that it raises — so nothing wrong can
  ship; one clause naming the module would remove a builder guess.
- **§2 branch 2 does not state the no-`## Timeline` case.** `get_section(body, "Timeline")` returns
  `None` on a note with no such section, and branch 4's create-at-end-of-file arm forces the behaviour
  (nothing to dedupe against, so write), while §5 already spells the `or ""` idiom for the detectors.
  Inferable rather than ambiguous, but §3 states its own `None` arm explicitly and this branch could say
  the same in five words.
- **Task 5's fixture cannot host AC-2(b) and (c) as written without a second arrangement.** A's plant is
  one entry per `PARITY_KINDS` member plus the out-of-table kind, which is exactly ONE `intro-by` — the
  main oracle depends on that — while (b) needs two on one person's own note and (c) needs a markerless
  `intro-by` heading, and putting either on B would break (a2)'s "exactly B's one record". A third
  planted note or a second temp vault satisfies both and the clauses state their own oracles, so this is
  ordinary test composition rather than a decision; one sentence would save the builder the derivation.

### Carried-forward notes

- **Round 2, note 1 (the `REASONS` pin's adjacent comment goes stale)** — CLOSED. Task 2, §9's row and
  `## Scope Boundary` all admit `tests/test_name_gate.py:121-122`'s two numbers into the bounded edit.
- **Round 2, note 2 (the precondition fence and §6 quoted the sentence in words the file does not use)**
  — CLOSED. Both now quote `:279-280`'s bytes and name the paraphrase as a paraphrase; AC-3(c)'s own
  signed `desc` and the data-premise round's record are correctly left alone.
- **Round 2, note 3 (Task 7's span is not durable against a fenced `## ` line)** — CLOSED, and closed
  harder than the note asked: reader 2 records the measured absence in the coupling declaration, and §12
  dimension (vii) now states which assertion fails on a truncation for that span instead of assuming it.
- **Round 1's six notes** — all CLOSED (confirmed in round 2, re-confirmed here at their symbols).
- **Architect round 4 notes 1–3 / round 3 notes 1–2** — remain CLOSED by §0 R1–R5.
- **Threat modeler round 3, note 1 (`## Parity samples`' truncation protection via AC-1(a2) is
  INCIDENTAL)** — CLOSED by §12 Rule 3, whose accounting covers BOTH capture spans non-incidentally, with
  the incidental-ness of (a2)'s coverage recorded rather than relied on.
- **Threat modeler round 1, note 1 (an `intro-by` entry ALREADY outside a `## Timeline` span is invisible
  to both the accessor and `intro_by_without_marker`)** — STILL OPEN as a deliberately accepted residual.
  Re-deferred: the exposure is measured at zero by precondition 2's re-runnable predicate, the standing
  instrument is named, and the typed door has zero callers until HAL9000 WI-082.
- **Threat modeler round 1, note 2 (`IntroRecord.introducer` is attacker-influenceable and returned
  verbatim, so a consumer rendering it into HTML must escape it)** — STILL OPEN and correctly outside
  this tree. Re-deferred: the library must not sanitize on a consumer's behalf; recorded for HAL9000
  WI-078 and orchestrator WI-194 to inherit.
- **Threat modeler round 1, note 3 (the D7 window's security reading — HAL9000's own door keeps accepting
  a marker-forging `text` until the cutover)** — STILL OPEN by D7's standing ruling. Re-deferred as ruled
  scope, not a gap.
- **Threat modeler round 2 note 1 / round 3 note 2 (the `REASONS` pin must move as an EQUALITY, never be
  loosened to `>=` or deleted)** — STILL OPEN as a disclosure for whoever reads the build diff. Re-deferred
  because the document names the target value `17` and states the obligation as a predicate; restated
  here so it survives into the build review, since the wrong edit looks as legal as the right one.
- **Data-premise residual 1 ("all 86 legacy `[intro]` entries are OUTBOUND" has no re-runnable
  predicate)** — STILL OPEN, governs no criterion. Re-deferred with its closing predicate already named
  (split the 86 by `^Introduced by ` versus `^Introduced to `, counts only), to be run at build-start
  re-grounding.
- **Data-premise residual 2 (HAL9000 WI-082's mint is uncommitted in HAL9000's working tree)** — STILL
  OPEN and outside this tree. Re-deferred: the id is issued and `next_id` advanced, so precondition 4's
  record in this tree's HEAD is truthful; committing it is HAL9000's act.

```verdict
gate: spec-reviewer
verdict: PROMOTE
date: 2026-09-29
model: claude-opus-5
note: Round 2's two findings are CLOSED and I verified each by reading the target files at the granularity the oracle consumes — §12 Rule 1 now spells the selector in its own terms with `baseline_sections:1518` named as a raising discipline rather than a transplant (confirmed: it raises on any heading outside its declared table, and the capture carries `## Part 1` at :57 and again at :587 inside the Appendix's python fence plus `## Appendix` at :470), and Rule 2 makes every phrase oracle whitespace-normalized (confirmed: docs/vault-fixtures.md:279-280 still splits the corrected sentence at a line break, so a literal test would be RED against a correct conductor edit). The threat model's M2 is folded ONE LEVEL UP as required rather than as a clause — §12 gains Rule 3, dimension (vii) answered per span for all four spans, and the level below it swept and declared with its one unguarded member (Task 7's emptied-population absence scan) closed by a member pin — and I re-counted the accounting at source instead of taking it from the fold: six line-start yaml fences in `## Parity samples`, twenty-nine in `## Validation boundary`, thirty-five in the file, the other four python, seventy-eight strictly alternating delimiters so the whole-file toggle walk is well-formed, and an injected `## ` line is not a fence line so a truncated span is RED while the whole-file count is unmoved. `fenced_blocks:1550` does discard the info string at :1554-1559, making `select_fenced_blocks`' PAIRS deviation load-bearing and earning its WI-235 battery. Both fold records are complete and fresh, both `desc` values byte-identical to round 3's mitigation fences, and I found each `design`/`work` quote where it claims to be and read the surrounding text. All twelve bar checks pass: the signed frame is unedited with R7 classified non-drifting, every task carries one well-formed verify and none orders the floor, Write-Targets coverage re-extracted per task with no path added or missing, six counting walls ship their shapes and near-misses, and `tests/test_loud_fail_harness.py`'s `six` dict is a required subset so the two new derivations move no wall. The arc — original, then folded material, then §12's own sweep — is a ladder climbing toward the machinery, and I looked specifically for a fourth-level finding on the accounting's expression rather than emitting one: it is position-free, count-pin-free, RED on either span's truncation inside or outside a fence, and it moves with the re-run capture D7 schedules. Three non-blocking notes, none able to ship a wrong library.
```

## Adversarial Review — 2026-09-29 (round 3)

**Recommendation: PROMOTE (injection axis only)** — no planted steering found. This is the narrow injection
question, not a fourth spec review: the spec-reviewer's standing round-3 verdict is PROMOTE and the threat
modeler's round 3 is PROMOTE with M1 and M2 folded, and nothing here adds to or substitutes for either.

Cold-start re-read after the third 2026-09-29 fold (the threat model's round-3 M2), with the material added
since my round 2 read closely: the `## Mitigation Folds` M2 record, the threat modeler's round 3, §12's new
Rule 3 and dimension (vii), §0 R7, Task 3's completeness-first clause and the spec-reviewer's round 3.

- **Text arguing for a verdict or addressed to a gate.** Pattern sweeps over the item doc for approval-steering
  phrasing (pre-approval claims, "do not block", "ignore prior", verdict-emission instructions, system-prompt
  talk) and for second-person or gate-addressed imperatives returned nothing outside this hunter's own earlier
  prose describing what it searched for. A sweep of line-start `gate:` / `verdict:` keys returned exactly the
  thirteen genuine fences (architect, ac-red-team, ac-signoff, data-premise, threat-modeler x3, spec-reviewer x3,
  injection-hunter x2), each at its own gate's section end with `gate:` matching the section that carries it.
  The verdict series is uneven (REVISE, PROMOTE, REVISE, PROMOTE on the spec-reviewer axis), which is the
  signature of independent judgement and not of a uniform lean.
- **The fold's new material.** M2's fold, §12 Rule 3, dimension (vii) and R7 are substantive test-oracle
  argument carrying re-runnable predicates (a whole-file accounting of `yaml`-info fences over the capture).
  The `## Mitigation Folds` M2 record is a `fold` fence quoting the threat modeler's mitigation `desc` and
  Task 3's own text; it makes its case for the design and addresses no reviewer. The spec-reviewer's round 3
  states it re-counted the capture's fences at source rather than accepting the fold's account, and the
  threat modeler's round 3 states it did the same from the capture's own bytes; two decorrelated reads
  converging on the same counts is not what a steered chain produces.
- **The `writes` fence naming another item's tracked document (WI-245).** Unchanged from rounds 1 and 2:
  `docs/vault-fixtures.md` is WI-016's document, declared as `kind: precondition` with the deletion spelled in
  the file's own bytes, the caged builder stated NOT to be its author, and WI-016's signed AC-5 fence at
  `:1434` stated out of scope. This round added no path and no builder write to that fence; the M2 fold moved
  only the capture's `why` (two structural properties named for whoever regenerates it), which is a
  precondition already conductor-owned. I repeat the flag for whoever lands it: land only the one substring
  deletion at `:279` and drop nothing else into that file.
- **Quoted and captured material.** The capture, corpus baseline, consumer audit and cutover record remain
  machine-shaped artifacts whose `verdict:` keys are HAL9000 accept/refuse probe results, not gate verdicts.
  I found nothing embedded in the item doc that addresses a gate.

**Honest limit, carried.** I read the same bytes the other gates did and could be fooled the same way; my
value is a different model and a narrower question. The document is now very long and densely cross-cited,
the shape in which a plant would hide, so I read the fold-added material and every verdict-shaped line
specifically for text that changes what a gate should do rather than what the system does. None does.

```verdict
gate: injection-hunter
verdict: PROMOTE
date: 2026-09-29
model: claude-sonnet-5-5
note: Re-read after the threat model's round-3 M2 fold finds no planted steering in the item doc — pattern sweeps for approval-steering and gate-addressed imperatives come back empty, the thirteen line-start gate/verdict keys are all genuine fences at their own gate's section end, the fold-added material (M2 record, §12 Rule 3 and dimension (vii), R7, Task 3's completeness clause) is ordinary spec argument with re-runnable predicates independently re-counted by two other gates, and the one cross-doc writes fence (docs/vault-fixtures.md) is unchanged as a disclosed conductor-owned precondition; this clears the injection question only.
```
