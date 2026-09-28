---
id: WI-033
title: TimelineEntry relocates into the library, with a derived introduced_by accessor
project: obsidian-schemas
stage: exploring
created: 2026-09-26
last_touched: 2026-09-28
stage_changed: 2026-09-28
touched_by: session
tags: []
depends_on: []
transitions: ["idea>exploring@2026-09-28@session"]
---

# TimelineEntry relocates into the library, with a derived introduced_by accessor

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

## Write Targets

Four `kind: precondition` artifacts, declared HERE so the drive pauses for the conductor's commits
BEFORE the acceptance-criteria frame is presented (WI-300). The builder is caged and this reader has no
shell: none of the four is reachable from inside the tree, and each settles a premise an AC or a stated
scope boundary below rests on. The spec-writer EXTENDS this section at `exploring → specced` with the
builder's own write targets; these four are never replaced.

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

## Architectural Review — 2026-09-28

**Recommendation: REVISE — return to exploration.** The approach is very close and most of it is right;
three of its load-bearing statements are unbuildable or self-contradictory as written, and all three are
cheap to close inside this document.

### Trigger check

Fires: creates a new module (`obsidian_schemas/timeline_entry.py`); touches >3 files in different concerns
(`timeline_entry.py`, `repositories/person.py`, `name_gate.py`, `scripts/lint_vault.py`,
`tests/fixture_vault.py` + the corpus); establishes a new persistent read contract over vault bytes (the
marker grammar); cross-system integration (a door four repos call, an accessor a fifth is parked on);
effort > 1 day. Review run in full.

### What verified clean

Every premise this reader could re-run at HEAD `bc2f11e` holds. **P1** — no module under
`obsidian_schemas/**` defines an entry kind, marker grammar or render; `body_sections.py:1-24` is
documented entity-agnostic with entity knowledge deferred to the repository layer, so A2's rejection is
correct on the module's own stated contract. **P2** — `person.py:1502` is literally
`if deduplicate_key and deduplicate_key in content` over the whole note including frontmatter; the key and
the written entry are unrelated arguments. **P3** — `person.py:1543-1545` prepends. **P4** — `^### |<!-- `
over `tests/fixtures/vault/` returns zero matches across the corpus, so the planted-fixture posture (D6)
and AC-2's "nothing here is sampled" are forced, not chosen. **P5/P6** —
`tests/fixtures/vault/@Morvette Harkwell.md:16` carries `introduced_by: "Voxleaf"`, declared at
`fixture_vault.py:320-326`; `Person` is `extra="allow"` (`models.py:34-40`); the entity arm hands the whole
projection to the gate with `whole_record=True` (`writer.py:229-233`, `:252-253`); the gate is DECLARE-only
(`name_gate.py:22-29`). **P7** — `scripts/lint_vault.py:814-834` is the live prose-parsing specimen, and
it is report-only. **P8** — exactly six `gate_write` call sites, matching the list in AC-3(b).

**Fit / boundaries.** A leaf module importing `errors` only mirrors `name_gate.py:14-20`'s discipline and
keeps the gate's import graph acyclic. **Determinism boundary:** correct and it is the design's best move —
the counterparty and day are already mechanically present in the marker slot, so the accessor reads them
rather than having a reader (regex or LLM) infer them from prose; D1 states that as a rule so nobody
"improves" it later. **Reversibility:** additive module, additive overload, report-only detectors, one gate
rule; the only sticky step is the `CORPUS_DIGEST` regeneration, which is one line. **D3's inverted trade**
is argued honestly and it is not novel in this tree — `person.py:1238-1244` already ships the identical
asymmetry for WI-032 (whole-record re-serialization refuses, the three DELTA arms stay open), so the
retired-key ban lands on an established precedent rather than inventing one. **D4** is right:
`_refuse`'s rule 2 (`name_gate.py:174-186`) exists precisely to keep a note-derived person name out of the
refusal, and the key is a constant that identifies the fault completely.

### Blocking issues

**1 — The Intent promises ONE definition; the Approach ships a SECOND copy and never says so.**
`## Intent` says the vocabulary "lives in the library every writer already installs", and
`## Problem / Motivation` says "`TimelineEntry` RELOCATES from HAL9000 ... so the library owns the
vocabulary and HAL9000 imports it". Nothing in `## Approach`, in AC-1..AC-4, or in the `## Write Targets`
fences performs or schedules that cutover. `## Dependencies` states "HAL9000's WI-058 door and WI-077
router become importers rather than owners" as a future fact with no owner, no work item and no acceptance
criterion, and precondition 3 *measures* consumers rather than moving them. `### What this item does NOT do`
enumerates five absences and omits this one — which is the WI-144 shape the role asks me to scan for: the
document is buildable two ways, and a builder reading the Intent could reasonably believe the item is not
done until HAL9000 imports.

The durable outcome as scoped is two implementations of one grammar in two repos, with the library's copy
pinned by a byte-parity test against a capture of the other frozen at one HEAD. That capture cannot detect
drift: if HAL9000 adds a kind or changes the heading grammar tomorrow, AC-1(a) stays green (it compares
against the frozen file), and AC-2's tests stay green too because they plant entries with the *library's
own* renderer — so the accessor could silently return `[]` against real HAL9000 bytes with a green floor.
This is LESSONS #4 verbatim, including its named scar: "exocortex keeping its own copy of the name-prefix
regexes that won't inherit fixes to the canonical validator", and the rule it carries — "when you're about
to write a second implementation, the work is to route to the first, not to copy it."

Library-first sequencing is a legitimate answer; leaving the second half unnamed is not. Concretely, and
all of it inside this document (no other repo is touched):
(i) add the cutover to `### What this item does NOT do` in the same voice as the other five;
(ii) mint the HAL9000 cutover as a named follow-up with a stated re-entry condition, in the same ruling —
the conductor mints it exactly as the three preconditions are conductor-committed — rather than leaving it
as a sentence in `### Dependencies`;
(iii) state what stands guard in the window between the two: precondition 1 already pins a 40-hex HEAD, so
say in `## Approach` that the capture's HEAD is the staleness anchor and name who re-runs it, or accept in
writing that divergence is undetected until the cutover lands.

**2 — AC-1(a)'s oracle is not executable against the precondition as that precondition is specified.**
AC-1(a) requires `render()` output to be byte-identical to "the corresponding rendered sample committed in
`docs/wi-033-hal9000-timeline-entry-capture.md`", read from the file and "never a literal re-typed into the
test". To construct the entry whose render is compared, the test needs that sample's INPUTS — kind, text,
`when`, discriminator. Precondition 1's `why` asks only for "at least one RENDERED OUTPUT SAMPLE per kind,
produced by running that code". `when` is injectable and appears in both the heading and the marker's day
slot, so without a pinned `when` no sample is reproducible at all, and the builder is forced into exactly
the re-typed literal the criterion forbids — the failure landing AFTER the conductor's commit pause, which
is the expensive place for it.

Two further clauses of the same gap: the capture's `why` declares no machine-readable form (the test must
parse this document, so the fence/table shape is part of the contract, as `lint-vault-live-baseline.md`'s
declared headings already are for WI-026); and AC-1(a) sweeps "every kind in the declared table", which is
the LIBRARY's table, while the capture holds HAL9000's — so a kind the library declares and HAL9000 never
rendered makes the criterion unsatisfiable by construction. Amend precondition 1's `why` to require
input→output PAIRS in a named machine-readable shape with `when` pinned per sample, and state in AC-1(a)
which side's table governs the sweep.

**3 — AC-2(e)'s boundary scan excludes the one directory where the second copy has already appeared, and
where this item is about to add marker-reading code.** AC-2(e) asserts "a derived scan over
`obsidian_schemas/**` finds the marker regex defined in exactly one module". But P7's existing specimen is
in `scripts/lint_vault.py:816`, not under `obsidian_schemas/**`, and AC-4(b)'s new `intro_by_without_marker`
detector — which must recognise a well-formed marker — lands in that same file. `lint_vault` already
imports from the library at `scripts/lint_vault.py:38-60` (including `body_sections` and `gate_write`), so
importing the marker regex is available and cheap. As written, a builder who writes a second marker regex in
`scripts/lint_vault.py` satisfies AC-2(e) and violates the Intent in the same commit. Widen the scan to
`scripts/**` as well, phrased to permit an IMPORT and forbid a re-definition.

### Non-blocking notes for the spec-writer

- `IntroRecord`'s third field is named three times ("source", "source marker") in `## Approach` and AC-2's
  `desc`, but no clause pins its value — AC-2's stated oracle checks only counterparty and day, so a build
  that ships it as `None` is green. Either pin it or drop it from the tuple.
- AC-4(d) asserts silence "as a set equality against the corpus's existing issue baseline". The committed
  baseline in this tree is `docs/lint-vault-live-baseline.md` (`tests/test_lint_vault_fix_rules.py:113`),
  which is the LIVE-vault bracket, not a fixture-corpus issue set. Name the artifact or the derivation the
  set equality is taken against, or the clause has no referent.
- AC-3(b) drives "each [arm] that can carry a person frontmatter delta". `writer.py:494` is
  `gate_write({}, declared_type=None, whole_record=False)` — a call site that structurally cannot carry one.
  Worth one clause saying the derived set is filtered rather than leaving a reader to wonder whether the
  sweep is incomplete.
- `## Problem / Motivation` cites `repositories/person.py:1371-1415` for `append_to_timeline`; the method is
  at `:1452-1557`, as the sharpened paragraph below it correctly says. Stale line range in the older half.

### Prior art (outside view)

Not a constraint-compensation item: nothing here works around a subtracted capability. The shape — one
library owning a serialization vocabulary that every service imports, with the consuming services cut over
in a following change — is the ordinary answer (a shared schema package), and the standard practice this
item is missing is exactly the one finding 1 names: the world pairs "publish the library" with a scheduled
consumer cutover and a drift check, it does not leave the original implementation in place indefinitely
behind a frozen snapshot test.

```verdict
gate: architect
verdict: REVISE
date: 2026-09-28
model: claude-opus-5
note: The Intent promises one definition of the vocabulary but nothing in the Approach, the ACs or the preconditions cuts HAL9000 over, leaving two copies with a frozen-snapshot parity test that cannot detect drift (LESSONS #4); AC-1(a)'s oracle is unexecutable because precondition 1 captures outputs without the inputs or the pinned `when` that produced them; AC-2(e)'s one-copy scan excludes `scripts/`, where the existing prose-parser specimen lives and where AC-4's new marker-reading detector lands.
targets: AC-1, AC-2, AC-4, #intent, #approach, #write-targets
prior: none
basis: original
findings: 3/7
```

## Architectural Review — 2026-09-28 (round 2)

**Recommendation: REVISE — return to exploration.** All three of round 1's blocking findings are CLOSED,
and the folds are better than the remedies I asked for. One new blocking issue, and it lives in the fold:
AC-1(a2) — this round's new material — machine-checks a reading of "declared kind table" that
`## Approach` and A1 contradict, which leaves the write door buildable two ways with different live
consequences. It is one or two sentences to close.

### Trigger check

Unchanged from round 1 and still firing: new module, >3 files in different concerns, a new persistent read
contract over vault bytes, cross-system integration, effort > 1 day. Review run in full.

### Round 1's findings, re-read

**Finding 1 — CLOSED, and overtaken.** I asked for three things and the document does all three, plus one
I did not ask for. (i) `### What this item does NOT do` now opens with the cutover in the same voice as the
other five (`:377-380`). (ii) The follow-up is minted as its own section with a scope, a home, an owner and
a verbatim three-clause re-entry condition (`:329-346`) — and, better than a paragraph, **precondition 4**
(`:458-462`) makes the mint an ACT the drive pauses for, so the item cannot reach its criteria frame while
the second half is still a sentence. (iii) The window's guard is stated three times and, crucially, stated
as what it *is not*: `HAL9000_PARITY_ANCHOR` is "a pin, not a monitor", asserted by **AC-1(a3)**, with
drift during the window "accepted in writing, not mitigated". **D7** records all three options and why (b)
was taken. The role's own blocking condition on a deferred option — that the deferral mint its probe item
in the same ruling or be written as REJECT — is satisfied by the D7 + precondition 4 pair.

**Finding 2 — CLOSED.** Precondition 1's `why` now requires INPUT→OUTPUT PAIRS with `when` pinned per
sample, in a declared machine-readable shape (one `yaml` fence per sample under a `## Parity samples`
heading, keys `kind`/`text`/`when`/`discriminator`/`rendered`) — and it names the precedent correctly:
`tests/test_lint_vault_fix_rules.py:113` is indeed `docs/lint-vault-live-baseline.md`, parsed by declared
headings. AC-1(a) now reads BOTH sides from the file and lets the CAPTURE's sample set govern the sweep,
with **AC-1(a2)** asserting the two tables coincide — which is the right answer to the unsatisfiable-by-
construction half of the finding.

**Finding 3 — CLOSED, and grounded by a premise that did not exist last round.** AC-2(e) now scans
`obsidian_schemas/**` AND `scripts/**`, permits an IMPORT, forbids a RE-DEFINITION, and names
`scripts/lint_vault.py`'s new detector as the specific file the clause is about. **P9** is newly MEASURED
and I re-ran it: grep for `<!--` or `-->` over every `.py` in the tree returns zero matches, so the scan
starts from zero and `intro_not_symmetric`'s prose regex falls outside the predicate by construction
rather than by exemption — which is a cleaner closure than the exemption I would have accepted.

**All four non-blocking notes taken.** `IntroRecord.source` is pinned to the verbatim marker bytes with a
stated failure mode (AC-2); AC-4(d)'s baseline is now a same-run second computation with the wrong referent
explicitly disowned; AC-3(b)'s filter is asserted as a set equality; the stale `append_to_timeline` range
in `## Problem / Motivation` is corrected to `:1452-1557`.

### What verified clean this round

Everything the folds newly assert, re-run at HEAD `bc2f11e`. **P9** — zero `<!--`/`-->` in any `.py`
(above). **P8 / AC-3(b)'s arm list** — exactly six `gate_write` call sites, matching the document
verbatim: `writer.py:252`, `:385`, `:443`, `:494`, `base.py:728`, `person.py:1270`. **AC-3(b)'s excluded
set** — `writer.py:494` is literally `gate_write({}, declared_type=None, whole_record=False)`, with
`:477-493` explaining why, so the equality the clause asserts is true and the other five all take a real
delta (`:386` and `:444` pass `frontmatter.get("type")`, `base.py:729` passes `self.type_name`,
`person.py:1270` the projection). The derivation to extend exists — `tests/derivations.py:1054`
`gate_call_declarations` and `:1027` `_declaration_class` — so "derived rather than hand-listed" is
buildable, not aspirational. **AC-2(e)'s instrument** — `tests/derivations.py:185` `python_files_under(*roots)`
is parameterized over roots by design (`:188-196`), so the widened scan needs no new walker.
**AC-4(b)'s import is cheap** — `scripts/lint_vault.py:38-60` already imports `body_sections`, `gate_write`,
`identifier` and `vault_io` from the library. **AC-3(c)'s swap is sound and complete** — `Person` declares
no `manager` field, `docs/vault-fixtures.md:279` names `manager:` and `introduced_by:` as co-equal members
of the undeclared-key class, the manifest declaration is the single `undeclared={"introduced_by": "Voxleaf"}`
at `tests/fixture_vault.py:325`, and `docs/vault-shape-census.md` never names the key — so the swap costs
the note, the manifest line and one `CORPUS_DIGEST`, exactly as claimed, with no census row to chase.
**WI-034's handoff doc agrees** — `docs/wi033-slug-handoff-intro-by-intro-to.md:23,27` states the same two
slugs, the same `{kind}:{day}:{counterparty}` key and the same "never by parsing the sentence" rule, so the
fold in ruling §2 leaves nothing contradicting it in this tree.

**Prior art, re-asked of the fold.** D7(b) is the standard shape (publish the shared schema package, cut
consumers over in a following change) and the follow-up now supplies the scheduled cutover the world pairs
it with. The one half the world also buys — a standing drift check — is deliberately declined in writing
rather than overlooked, which is the option I offered last round; see the first non-blocking note.

### Blocking issue

**1 — "Declared kind table" means two different write doors, and this round's fold machine-checks one of
them while `## Approach` states the other.** Three places say the module holds **kind-SLUG validation** — a
PATTERN over an open set: `## Problem / Motivation:19` ("the kind-slug validation"), A1 (`:222`, "kind-slug
and discriminator validation"), `## Approach:404` ("its kind-slug and discriminator validation"), and
precondition 1's `grounds:440` ("kind-slug rule"). But AC-1's `desc` requires "a declared kind table", and
**AC-1(a2)** — new this round — asserts that table "equals the set of kinds the capture holds, as a SET
EQUALITY", with "a kind the library declares that HAL9000 never rendered is RED". AC-2 then iterates that
same table as its sweep space. Nothing in the document says whether a kind that satisfies the slug rule but
is absent from the table is ACCEPTED or REFUSED, and the two answers are different doors:

- *Closed table (an enum that refuses an unlisted kind).* Then AC-1(a2)'s `why` is true as written — "this
  item introduces no library-only kind" really is enforced — but the library becomes STRICTER than the code
  it is relocating: `TimelineEntry` refuses any kind the capture's author did not sample, and post-cutover
  a HAL9000 call that writes today raises. It also contradicts the item's own named consumer:
  example-of-done 3 (`:519-524`) promises "orchestrator or any new writer that installs this library"
  can build a `TimelineEntry` and hand it to the door, which a table frozen to HAL9000's sampled kinds
  forbids for anything new.
- *Open slug rule (the table is only the parity/sweep universe).* Then the prose is right, nothing is
  over-refused — but AC-1(a2) polices a constant that gates no write, and its `why`'s claim to enforce
  rather than trust is false; the only real guard left on kinds is the accessor's filter, which AC-2(a)
  already covers independently.

This is the WI-144 shape: the item is buildable two ways, and the reading the fold's own justification
presumes is the one the Approach text denies. It matters now rather than at build time because AC-1(a2) is
machine-checked and the criteria frame is about to be signed.

*Second clause, same root — parity is pinned for RENDER only, and the item's own standard is broader.*
`### Constraints discovered:356` states "byte parity with HAL9000 is the meaning of 'relocate'", and
precondition 1 captures HAL9000's kind-slug validation and forgery guard as SOURCE. But no criterion pins
the library's REFUSAL SET against it: **AC-1(c)** states the library's own rules independently (empty,
whitespace-only, or key-separator-bearing discriminators refused), and a capture whose samples are all
valid inputs cannot detect a library that refuses an input HAL9000 accepts. AC-1(a2) does exactly this job
for the kind set; the analogous assertion for the validation surface is absent.

*Remedy, all of it inside this document.* (i) State in `## Approach` and in AC-1's `desc` which door the
kind table is — closed-and-refusing, or an open slug rule with the table as the parity universe — and make
AC-1(a2)'s `why` match the answer. (ii) If closed, say what a new writer's new kind costs (an entry in the
table plus, presumably, a capture sample it cannot have) so example-of-done 3 stays true. (iii) Add one
clause to AC-1(c), or one line to precondition 1's `why`, pinning the refusal surface: the capture declares
HAL9000's kind-slug and discriminator rules, and the library's are asserted to be no STRICTER than them —
or state in writing that refusal parity is out of scope and the cutover item owns it, as D7 already does
for drift.

### Non-blocking notes for the spec-writer

- **The declined drift check is declined against this project's own pattern, and one line should say why.**
  D7 accepts that HAL9000's drift is undetected because "the floor cannot reach another repo (WI-031 clause
  (v))" — correct about the FLOOR. But AC-4's `why` argues, in this same document, that "the linter is the
  only standing instrument over live data" precisely because the hermetic floor cannot watch the vault: a
  report-only tool OUTSIDE the floor is this tree's established answer to exactly this shape of blindness.
  The symmetric instrument here is a `scripts/`-resident parity re-check that re-runs the capture and diffs
  against `HAL9000_PARITY_ANCHOR` — the cutover item's first act, made runnable on demand instead of only
  once. I am not re-opening finding 1 over this (accepting the window in writing was the option I offered,
  and the item took it); but the asymmetry between the two paragraphs is worth one sentence, either
  adopting the instrument or naming why the vault case and the repo case differ.
- **The undeclared route past AC-3 is unstated.** AC-3(a) scopes the refusal to "a `person`-declared
  payload" and AC-3(d) exempts `company` and `book`. The five driven arms derive `declared_type` from the
  note's own `type:` (`writer.py:386`, `:444`) or the repository's (`base.py:729`), so a person note
  missing `type:` reaches the gate UNDECLARED — and `name_gate.py:364-368` documents that an undeclared
  write introducing no `name:` falls THROUGH to the person body. Both placements of the new rule satisfy
  every AC-3 clause as written, so say which: in the person body (undeclared writes covered too) or keyed
  on `declared_type == PERSON_TYPE` (undeclared exempt).
- **Two doc sentences describe the key as a legitimate specimen after AC-3(c) retires it.**
  `docs/vault-fixtures.md:279` and `docs/vault-fixtures-rounds.md:1498` both offer "a `manager:` or
  `introduced_by:` key" as the undeclared-key example. They stay literally true (both are named), but the
  first is the fixture corpus's own documentation and one word there keeps a later reader from re-planting
  a key the gate now refuses.
- **P5's incidental detail, for the swap's author.** The retired key's fixture value is `"Voxleaf"`, which
  is also the corpus's company stem (`@Voxleaf Ltd.md`, `tests/fixture_vault.py:367`). Nothing depends on
  it, but if the swapped `manager:` value is chosen fresh rather than carried over, keep it a name the
  identifier index cannot resolve, for the same reason the note declares no `shape_classes`.

```verdict
gate: architect
verdict: REVISE
date: 2026-09-28
model: claude-opus-5
note: All three round-1 findings closed and the folds exceed what I asked; one new blocking issue in the fold itself — "declared kind table" is a closed refusing enum in AC-1(a2) (new this round) and an open kind-SLUG rule in `## Approach`, A1 and precondition 1, which are two different write doors with different post-cutover consequences, and the same root leaves the library's refusal surface unpinned against HAL9000's while the item's stated meaning of "relocate" is byte parity.
targets: AC-1, AC-3, #approach
prior: held
basis: folded-material
findings: 1/4
```

## Architectural Review — 2026-09-28 (round 3)

**Recommendation: PROMOTE to architected.** Round 2's blocking finding is CLOSED in both of its clauses,
and closed in the direction the code supports rather than the direction that was cheapest to write. The
write door is now stated once, ruled once (**D8**) and made FALSIFIABLE once (**AC-1(a4)**'s planted
out-of-table kind) — which is the difference between a document that says which reading it means and one a
build can only satisfy one way. Nothing structural is left open. My one remaining finding is a
test-assertion reification the spec-writer takes in place; it is recorded below as non-blocking for a
reason I state rather than assert.

### Trigger check

Unchanged from rounds 1 and 2 and still firing: a new module (`obsidian_schemas/timeline_entry.py`); >3
files in different concerns (`timeline_entry.py`, `repositories/person.py`, `name_gate.py`,
`scripts/lint_vault.py`, `tests/fixture_vault.py` + the corpus); a new persistent read contract over vault
bytes (the marker grammar); cross-system integration (a door four repos call, an accessor a fifth is parked
on); effort > 1 day. Review run in full.

### Round 2's finding, re-read

**Clause 1 — the two write doors — CLOSED, and closed the right way.** **D8** rules the OPEN SLUG RULE as
the door and demotes `PARITY_KINDS` to a parity/sweep universe that gates nothing, on three grounds I agree
with and would have argued in the same order: this item RELOCATES rather than tightens; a closed table
locks out example-of-done 3's "any new writer that installs this library"; and the closed reading buys no
parity for new kinds, it merely forbids them. I re-grepped the document for the contradictory phrasing:
every live occurrence of "declared kind table" is now inside D8, inside this fold's own narrative, or
inside rounds 1–2's archived review text. The four normative surfaces agree — AC-1's `desc` ("an OPEN
kind-SLUG RULE as the write door ... GATES NO WRITE"), A1, the `## Approach` paragraph, and precondition
1's `grounds`. And crucially the reading is not merely STATED: **AC-1(a4)** plants a slug-valid kind absent
from the table and asserts it constructs, renders and round-trips, so a closed-enum build is RED. That is
the planted discriminant P4 forces (the corpus has zero entries, so nothing on disk can tell the doors
apart), and it is what I would have asked for had the fold only written prose.

**Clause 2 — the unpinned refusal surface — CLOSED, and closed in the only direction that can break a
caller.** Precondition 1 gains **part 3**: a `## Validation boundary` section of INPUT→VERDICT pairs with a
declared per-probe key shape, produced by RUNNING HAL9000's validation rather than by reading its regex —
which is LESSONS #19/#26 applied at capture time, and is the same discipline part 2 already carried for the
render samples. **AC-1(c2)** then asserts the ACCEPT direction only, with the loose direction declined IN
WRITING and routed to the cutover item exactly as D7 routes drift. Restricting the assertion to
over-refusal is the correct asymmetry and the document argues it correctly: over-refusal is the failure
this item can CAUSE (its first victim post-cutover is HAL9000's own caller), under-refusal cannot break a
caller that works today, and the library's own guards are pinned independently by AC-1(c).

**Round 2's four non-blocking notes all taken.** The D7 addendum answers the drift-check asymmetry rather
than absorbing it, and the answer is right on its own terms: the vault is this library's OWN data domain
with an unbounded window and a standing instrument already in place, while HAL9000's source is another
project's code behind a window ONE scheduled item closes — and a checker here reading a sibling repo's
absolute path would re-open the out-of-tree path dependency WI-031 clause (v) closed. AC-3(a)'s placement
is now a measured fact (**P10**) rather than a build-time coin flip. AC-3(c) folds in the corpus
documentation update. D3 picks the swapped `manager:` value fresh, as a name the identifier index cannot
resolve.

### What verified clean this round

Only the newly asserted material; rounds 1–2 verified the rest at the same HEAD.

**P10 — verified, and it is the sharpest new premise in the fold.** `gate_write`'s prologue reads exactly
as claimed. `name_gate.py:359-360` is `if "name" in introduced and declared_type is None` — it speaks ONLY
to `name:`. `name_gate.py:373` is `if declared_type is not None and declared_type != PERSON_TYPE:`,
returning `dict(introduced)` at `:398`, and the comment at `:364-368` states verbatim that the `is not
None` half is load-bearing precisely so "an UNDECLARED write that introduces identifiers but NO `name:`
must fall THROUGH and normalize exactly as a declared one". The person body opens at `:400`. So AC-3(a)'s
ruling — the rule lands in the person body, NOT keyed on `declared_type == PERSON_TYPE` — is the placement
that covers a person note missing its `type:` while keeping AC-3(d)'s company/book exemption for free. Both
placements satisfied every other AC-3 clause, which is exactly why naming it was worth a premise.

**AC-3(c)'s documentation clause — verified, and correctly scoped to one of the two files round 2 named.**
`docs/vault-fixtures.md:279` does offer "a `manager:` or `introduced_by:`" as the undeclared-key example
and is in scope. `docs/vault-fixtures-rounds.md` is NOT, and the fold is right to leave it: that drawer is
declared "byte-for-byte, append-only and never rewritten" by `docs/vault-fixtures.md:3761`, so editing it
would violate a shipped invariant to fix a sentence that stays literally true.

**AC-1(a4) and AC-2's instruments exist.** `tests/derivations.py:185` `python_files_under(*roots)` is still
the parameterized walker AC-2(e)'s widened scan needs, and `:1054` `gate_call_declarations` is still the
derivation AC-3(b)'s arm sweep extends — so both "derived rather than hand-listed" clauses remain
buildable rather than aspirational.

### Review

**Fit.** A leaf module importing `errors` only matches `name_gate.py:14-20`'s discipline and keeps the
gate's import graph acyclic; A2's rejection of `body_sections.py` still stands on that module's own stated
entity-agnostic contract (`body_sections.py:6-9`). The report-only detector posture matches WI-026's and
WI-032's shipped precedent, and D3's inverted trade lands on an established asymmetry
(`person.py:1238-1244`) rather than inventing one.

**Duplication.** This is the dimension the item exists to serve, and AC-2(e) is now the predicate that
enforces it: one DEFINITION of the marker grammar, imports everywhere else, over `obsidian_schemas/**` AND
`scripts/**`. P9 makes the scan start from zero, so `intro_not_symmetric`'s prose regex
(`scripts/lint_vault.py:814-834`) falls outside the predicate by construction rather than by exemption.

**Boundaries.** The WI-185 seam question is answered rather than worked around: the counterparty and day
already survive into the marker slot, so the accessor reads structure instead of reconstructing it, and D1
freezes that as a rule. The one place structure IS discarded — `append_to_timeline`'s unrelated
string-and-key arguments (P2) — is fixed at the door by AC-1(d)/(e), which is the rule applied where it
bites.

**Determinism boundary.** Correct, and unchanged from round 1: nothing mechanical is handed to a judgement
channel. The day and counterparty come from slots; the prose is never read, by rule and by AC-2(d)'s
assertion.

**Reversibility.** Additive module, additive overload, three report-only detectors, one gate rule. The one
sticky step remains the `CORPUS_DIGEST` regeneration, paid once. The un-undoable half is the one this item
does NOT do — and D7 keeps it that way deliberately.

**Generalization.** D8 is where this dimension was actually decided, and it went the right way: the door
generalizes (any slug-valid kind works immediately), while the PARITY CLAIM stays bounded to captured bytes
and grows only when the capture grows. That split — an open mechanism with a narrow, falsifiable claim — is
the shape that avoids both over-fitting to HAL9000's sampled kinds and over-claiming parity nobody measured.

**Cost & maintenance.** The recurring cost is one capture artifact whose staleness is machine-anchored
(AC-1(a3)) and whose re-run is the named first act of a minted follow-up. That is cheaper than the standing
cross-repo checker the item declines, and the decline is now argued from ownership rather than from
convenience.

**Build vs extend vs integrate.** Extend, and the alternatives are recorded with their trigger predicates
(A2–A6). Nothing external is pulled in.

**Prior art (outside view).** Re-asked of the round-3 fold. The shape — publish a shared schema package,
cut consumers over in a following change, pin the publisher against captured bytes in the interim — is the
ordinary industry answer, and after round 1's fold this item now carries the scheduled cutover the world
pairs it with (D7 + precondition 4). The one half the world also buys, a standing drift check, is declined
IN WRITING with a stated ownership argument and the runnable form recorded for the holder of the second
copy. That satisfies the role's blocking condition on a deferred option: the deferral mints its probe item
in the same ruling rather than leaving a re-entry condition floating. Not a constraint-compensation item —
nothing here builds machinery around a subtracted capability.

### Notes (non-blocking) for the spec-writer

- **AC-1(c2)'s set equality needs one reification, or it is RED by this document's own premises.** The
  clause asserts "the set of capture-ACCEPTED inputs the library refuses equals exactly that enumerated
  guard set". But the `-->`/`<!--` forgery guard is HAL9000's — `## Problem / Motivation` and precondition
  1 part 1 both describe it as part of what RELOCATES from there — so the capture will record HAL9000
  REFUSING the forgery probes, which puts them outside "capture-ACCEPTED" on the left while the enumerated
  guard classes name them on the right. Read literally, the equality cannot hold. The operative intent is
  already stated in the same sentence ("so any other over-refusal is RED"), which is the ⊆ direction, and
  AC-1(c) independently pins that the library DOES refuse every guard member — so the fix is to reify the
  right-hand side as *the guard-class probes the capture records as ACCEPTED*, or to state the clause as a
  subset with AC-1(c) carrying the other direction. **Why this is not blocking, stated rather than
  assumed:** unlike round 1's finding 2 (which forced a re-typed literal — a wrong ORACLE that would ship
  green) and round 2's finding (two different write DOORS — a different shipped system), neither reading
  here ships a wrong library. The charitable reification is correct behaviour; the literal one is a red
  test at test-writing time, the cheap place, before any conductor commit and with no precondition change
  on either path. The criteria frame is explicitly DRAFT until Dave signs it, and this is precisely the
  surface the spec-writer refines in place.
- **AC-1(a2)'s "the set of kinds the capture holds" is loose by one word.** The capture will hold kinds in
  BOTH sections after precondition 1 part 3, and part 3 deliberately probes "a kind HAL9000's slug rule
  accepts that no sample renders" — which must NOT be in `PARITY_KINDS`, or (a2)'s own "a member with no
  sample is RED" fires. Three surrounding statements disambiguate it correctly (AC-1(a) parses the
  `## Parity samples` section; D8 says "a committed byte-parity SAMPLE"), so this is wording, not design:
  say "the kinds the `## Parity samples` section holds".
- **One corner AC-3 leaves unstated, and it is the mirror of the route P10 closes.** Writing the rule into
  the person body means an UNDECLARED write on a note that is semantically a company would also be refused
  for carrying `introduced_by` — it falls through `:373` exactly as an undeclared person write does. The
  live exposure is nil (the five driven arms all derive a declaration: `writer.py:386`, `:444`,
  `base.py:729`), and the trade is the right one — covering the undeclared person route matters more than
  exempting an undeclared company one for a key nothing may carry. Worth one clause in AC-3(d) so a reader
  does not discover it as an inconsistency with that clause's company/book exemption.
- **Nothing in this round re-opens D7.** The window between the library half and the cutover remains
  accepted in writing, precondition 4 remains the act that makes the mint real, and `HAL9000_PARITY_ANCHOR`
  remains a pin rather than a monitor — all three stated as what they are NOT, which is why I am not
  raising them again.

```verdict
gate: architect
verdict: PROMOTE
date: 2026-09-28
model: claude-opus-5
note: Round 2's finding is closed in both clauses and closed structurally rather than in prose — D8 rules the write door OPEN and AC-1(a4) plants the out-of-table kind that makes a closed-enum build RED, while precondition 1 part 3 plus AC-1(c2) pin the refusal surface in the only direction that can break a caller; P10 re-verified at `name_gate.py:359-400`, and the one residual finding is a test-assertion reification in AC-1(c2) that cannot ship a wrong system under either reading, so it is a spec-writer note rather than a fourth round.
```

## AC Red-Team — 2026-09-28

Attacked the DRAFT AC set (AC-1 – AC-4) fresh, reading `## Intent`, `### Examples of done`,
`## Problem / Motivation`, the 2026-09-28 `## Ruling`, and the Exploration Notes before the criteria,
per the role's Step 2. Three architect rounds have already hardened this document on fit, duplication,
boundaries and the write-door design; my pass is the lens they don't run — could a builder satisfy each
AC while doing as little real work as possible, or while honestly misreading it, and would satisfying it
mean the Intent was actually served?

### What I attacked and what held

- **AC-1(a)/(a2)/(a3)/(a4)** — the parity sweep is a genuine external oracle: both inputs and expected
  output are read from a committed precondition file, never a literal retyped into the test, and the
  open-vs-closed kind-table question is machine-checked by a planted out-of-table kind (a4) rather than
  merely asserted in prose — a closed-enum build is RED. Held.
- **AC-1(b)** — fixture space is `PARITY_KINDS` iterated plus the planted kind, never a hand list; the
  per-member oracle is the entry's own field values, not a totality stub, so a wrong-but-self-consistent
  build (the WI-280/WI-212 shape) mismatches instead of agreeing with itself. Held.
- **AC-1(c)/(c2)** — forgery and validation-boundary refusal are pinned in the one direction that can
  break a caller (no stricter than HAL9000, ACCEPT direction only). I independently re-read round 3's own
  non-blocking note on the guard-set equality's literal wording (the forgery guard is HAL9000's own, so it
  can't sit on both the "capture-accepted" side and the enumerated-exception side as literally phrased) and
  concur with the architect's read: charitably reified it is correct behaviour, the literal reading is a
  red test at write-time rather than a wrong shipped system, and the criteria frame is still explicitly
  DRAFT. Not material on its own — not raised as a separate finding here.
- **AC-2(a)** — the sweep plants `intro-to`, legacy `intro`, and the out-of-table kind specifically to
  catch a `"intro" in kind` substring implementation. Held — a cheapest-wrong build mismatches the stated
  per-member oracle.
- **AC-3(a)/(b)** — the gate-rule placement is a measured fact (P10), not a coin flip, and the arm sweep
  is derived with the excluded arm named as a set equality rather than left to trust. Held.
- **AC-4** — positive detection ((a)-(c), on a planted vault) and negative silence ((d), on the frozen
  corpus) are asserted separately, so a no-op implementation of the three detectors fails (a)-(c) rather
  than sliding through on (d)'s trivially-empty-corpus baseline. Held.

### Finding

**AC-2 — MATERIAL. Nothing plants a second person, so nothing proves `introduced_by(person)` is scoped
to that person's own note rather than to the vault at large.**

AC-2's `desc` plants "one entry per member on **one** person note" and its oracle covers kind-filtering
(a), plurality/order within that one note (b), the markerless narrowing arm (c), and silence on other
channels (d) — every dimension of *what* is on the note, none of *whose* note it is. Example of done 1
repeats the same single-person shape. Nowhere in AC-2, its `why`, or the examples does a second person
note carrying its OWN distinct `intro-by` entry (a different counterparty, a different day) get planted,
and nowhere is it asserted that calling the accessor on person A excludes person B's record.

Failure scenario: implement `introduced_by(person)` to glob every note under the vault for `intro-by`
markers (or to read a fixed/first note) instead of loading `person`'s own body via `parse_body_sections`
and reading only its `## Timeline`. Against AC-2's own fixture — a vault containing exactly one person
note with any `intro-by` data — that implementation returns exactly the one record the oracle expects,
and every clause (a)-(e) plus example 1 goes green, because the vault never contains a second person's
entry to wrongly include or a first person's entry to wrongly exclude. Shipped against the live vault —
over a thousand person notes, each with its own `## Timeline` — `introduced_by(@Alice)` could silently
return `@Bob`'s introducer, or the union of everyone's `intro-by` records, with this criterion fully
satisfied throughout and `## Intent`'s "who introduced this person" answered for the wrong person.

This is the same shape AC-2(a) already defends against on the KIND axis — planting `intro-to`, legacy
`intro` and the out-of-table kind specifically because a corpus with only one member can't discriminate a
substring match from a correct filter (P4's WI-286 reasoning) — applied to the PERSON axis the accessor's
own first argument selects on, for which the criterion never plants a second member.

What would have to change: plant at least two person notes in the temp vault, each carrying its own
`intro-by` entry with a different counterparty and day, and add a clause asserting `introduced_by` on one
returns only that person's record — never the other's alone, and never the union.

```verdict
gate: ac-red-team
verdict: REVISE
date: 2026-09-28
model: claude-sonnet-5
note: AC-2 plants intro-by data on only one person note, so nothing asserts `introduced_by(person)` reads that person's own `## Timeline` rather than the whole vault — a build that globs all notes for `intro-by` markers passes every clause and could silently cross-attribute introductions in production.
targets: AC-2
prior: none
basis: original
findings: 1/1
```

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
