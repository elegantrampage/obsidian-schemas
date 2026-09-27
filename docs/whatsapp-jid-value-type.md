---
id: WI-032
title: Validate the WhatsApp JID shape at the person boundary
project: obsidian-schemas
stage: exploring
created: 2026-09-21
last_touched: 2026-09-27
stage_changed: 2026-09-27
touched_by: session
tags: []
depends_on: []
transitions: ["idea>exploring@2026-09-27@session"]
---

# Validate the WhatsApp JID shape at the person boundary

### Archived Rounds

<!-- archive-split: machine-maintained pointer; do not edit -->
Settled gate rounds for this item live in `docs/whatsapp-jid-value-type-rounds.md` — every round at a conveyor door
this item has already advanced past, byte-for-byte, append-only, never rewritten. READ ON DEMAND
ONLY: each gate's latest standing round is still in this document, so nothing needed to advance this
item is in the drawer. Open it only to read a settled round's full reasoning.


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

**Sharpened at `exploring` (2026-09-26).** The paragraph above names a value type as the fix, and the
value type has shipped since WI-125 (`identifier.py:258-298`) — so the mint's mechanism was never the
gap and the problem is four narrower things, all downstream of that type existing (item 4 added in the
2026-09-26 architect round, and it is the one that decides whether the item closes the case it was
minted for):

1. **No writer uses it.** `Person.whatsapp` is a bare `str` (`models.py:94`) and the ONE surface every
   writer shares — the WI-021 semantic gate — excludes the field by name:
   `_CONTAINER_KEYS = ("emails", "phones", "aliases")` (`name_gate.py:84`), and `rg -n 'whatsapp'
   obsidian_schemas/name_gate.py` returns nothing. A malformed JID has no door that refuses it, and
   `rg -n 'whatsapp' scripts/lint_vault.py` returns nothing either, so nothing REPORTS one after the
   fact. The Kim Faura repair was hand work because there was no other kind available.
2. **One string cannot hold the data.** A person now has a phone-JID *and* a newer `@lid`; the field
   holds one scalar, so the sync collapses two identifiers into one and the other is lost at the write
   seam. This is a cardinality defect, not a validation one.
3. **A stored `@lid` is actively mis-resolved.** `_index_entity` (`person.py:266-270`) feeds
   `normalize_phone(entity.whatsapp)` into `_phone_index` unconditionally, and `normalize_phone` splits
   at the `@` and keeps the digits (`phone_normalization.py:52-55`) — so a lid's opaque internal digits
   are indexed as a telephone number, and `get_by_phone`'s permanent fuzzy arm (`person.py:494-496`,
   `phones_match` strips a leading US `1`) can return that person for a number nobody in the vault
   holds. Meanwhile the lid IS indexed correctly under `jid:<lid>` by `_project_identifiers`
   (`person.py:330-331`) and NOTHING public reads that key. So the field is simultaneously
   over-resolved as a phone and unreachable as a JID.
4. **And the type a writer would reach for does not refuse the value that caused this item.**
   `WhatsAppJID.parse` never looks for a JID suffix at all: anything containing `@lid` is a lid, and
   anything else whose `normalize_phone` output carries at least `Phone.MIN_DIGITS == 7` digits is
   accepted as phone-bearing (`identifier.py:269-281`). So `WhatsAppJID.parse("+44 7739 341679")` —
   the Kim Faura value, and the same bare-phone bypass recorded at
   `docs/write-door-bypasses.md:3994` — SUCCEEDS, with `phone_digits == "447739341679"` and
   `key == "phone:447739341679"`. A door wired to that parser refuses only digit-less junk (`"n/a"`,
   `"ask Kate"`) and would ship GREEN while the motivating defect still writes cleanly through the
   PATCH door. See F12: the parser is a REACH predicate built for resolution, and storage needs a
   second, narrower question asked of the SAME type.

So the item is: the field's cardinality, one write boundary that asks the STORABLE question (not
merely the parseable one), one resolution door, and the migration that moves ~1,170 notes onto the
new shape without losing an identifier — and without silently dropping the values that are already
wrong.

## Intent

A WhatsApp identifier that is not a WhatsApp JID never reaches a person note — that promise is about
arrival, so it ranges over WRITES from the day this lands and not over the values already on disk, which
the third paragraph below owns and which the migration REPORTS and LEAVES rather than converting. "A JID" means it
carries a WhatsApp JID domain — `@s.whatsapp.net` or `@lid`, where the domain is the text after the
LAST `@`, so `447700900456@lid.example.com` does not qualify and neither does `…@example.com` — so a
bare telephone number typed into
`whatsapp:` is refused rather than stored, which is precisely the value that caused this item. Every
writer refuses it at the boundary, loudly and naming the value on the error, and the one definition
lives in obsidian-schemas so no consumer carries its own copy.

And the other half, which the mint left implicit: a JID that IS on a note resolves to its person —
both forms of it, and a person who has two of them keeps both — and it is never mistaken for a
telephone number. Resolution stays LIBERAL where storage is strict: asking with a bare number still
finds the person, because a lookup is not a write.

And the condition on all of it: nothing already written on a note is silently dropped to make the
above true. A value that is already wrong is reported and left, never erased — and it stays FIXABLE, by
hand, through the ordinary doors: an empty `whatsapp:` field claims no identity, so emptying the field is
always allowed and strictness never lands on the absence of a value.

*(Sentence one states Ruling A's recommended arm — the STORABLE predicate. If Dave rules the other
way, this is the sentence that changes, and it is a one-line edit while the ACs are still drafts.)*

## Exploration Notes

Mode: **approval-only** (`involvement: null` in `state/work-items.json:3167`), so the approach below is
re-derived from the frozen `## Intent` and the mint's named mechanism was treated as a hypothesis
(WI-146 tweak 11). It did not survive: see the sharpening in `## Problem / Motivation`. Dave's
2026-09-26 rulings in the premise paragraph are treated as given, with THREE questions sent back to him
(`### OPEN RULINGS for Dave`, below) rather than decided here. Two of those are new in the 2026-09-26
architect round: the type's shipped behaviour is wider than his ruling (1) describes it (F12), and the
literal field annotation his ruling (2) names cannot hold a value the door refuses without erasing it
(F13). Both are stated as recommendation-plus-cost so they are a short agree/tweak rather than a
re-derivation, and both are upstream of the AC frame — which is why they are here and not in the spec.
**Still three, after the class-Ø fold** (architect round 3 and AC red-team round 2, both finding the same
defect independently): that fold NARROWS the refused population to what Dave's ruling (1) already
describes, so it is a correction to this document rather than a fourth question for him (F16).
**Still three after the fixture-plant fold too** (architect round 4 and AC red-team round 3, again
converging independently): the frozen corpus's round-trip representative and its privacy wall each
forbid part of the plant plan the earlier folds wrote, which changes WHERE the discriminating members
live and not WHAT any criterion asserts (F17). Neither leg reopens a ruling.
**Still three after the fold that finished the sweep** (architect round 5 and AC red-team round 4): the
fixture-and-cost plan carried one instruction priced against an artifact whose contract nobody had read —
`docs/vault-shape-census.md`, which this item may not edit at all — and AC-5's one required plant with no
pinned literal was the two-JID note, the exact member F17 leg 3's trap reaches next. Both are corrections
to this document; F18 carries them and runs the plant-literal × corpus-contract matrix to its end so the
next unswept wall is not the sixth round's finding.
**Still three after the REPORT fold** (architect round 6 and AC red-team round 5), and this one came from
outside the fixture class the previous two folds closed: F9 priced the linter's report surface at ZERO off
a function's docstring without reading its one call site, so the "reported and left" half of the design —
promised in `## Intent`, F13 leg 3, Ruling B leg 2, AC-5 leg (e) and `### Examples of done` — had no
mechanism and no `check:` behind it. F19 carries it. The one thing in it that COULD have been a fourth
question for Dave is the branch this fold declines: withdrawing the word "reported" instead of building the
detector (rejected item 13). The detector is one report-only arm copied from WI-029's own, so the promise is
kept and the rulings are untouched.
**Still three after the PROSE fold** (architect round 7 and AC red-team round 6), and this one is about the
package file this item edits most rather than about a fixture, a detector or a criterion's reach:
`obsidian_schemas/repositories/person.py`'s comment and docstring TEXT is a frozen fixture of WI-024, and
`PersonRepository.save` — the frame F11 makes this item's write-back disclosure home and F13 makes its
refusal surface — is not one of the thirteen owners that wall authorizes to change. So the document told a
builder WHERE to write a disclosure without telling them the one property that keeps writing it free.
F20 carries it: the disclosures land APPEND-ONLY in that frame, and the two builds that resolve the red
otherwise are rejected items 15 and 16. No ruling is touched — what moves is where a disclosure's TEXT may
be written, not what any arm does.
**Still three after the TERMINAL-STATE fold** (architect round 8 and AC red-team round 7, converged
independently from the criteria text alone), and this one is not another artifact whose contract nobody
read — it is a contradiction between two conjuncts this document has carried since its first draft. AC-3
refuses a class-D or class-E value in BOTH shapes and AC-5 leg (b) routes every migration write through the
gate, so a shape conversion — which re-introduces the field — is refused for exactly those notes and they
are TERMINALLY SCALAR; yet AC-5 leg (e), `## Approach` step (4)'s exit numbers and `### Examples of done`
all promised "zero notes left in the scalar shape" in the same breath as "the D+E residual reported and
byte-identical", and AC-5's own mandated class-D plant collides them on the hermetic suite. F21 carries it.
The fold makes the exit number a PARTITION rather than an absolute (**THE TERMINAL-STATE PARTITION**, below,
restated in all four places that state an exit figure), adds the conjunct that keeps the erase-to-convert
build red BY INTENT rather than by side effect, and corrects AC-5 leg (d)'s claim to hold "either way Dave
rules" — under Ruling B's alternative arm class C joins the residual and the scalar count Dave is shown
changes, which is a number he is entitled to when he rules. No ruling is reopened: nothing about what the
migration DOES to any cell moves, only what this document tells Dave and the live-bracket conductor the
vault looks like when the run has finished.

**The definition every criterion below computes against — TWO predicates over ONE type, in ONE
module, with ONE precondition ahead of both (the third bullet is not a third predicate).** Both live on `WhatsAppJID` in `identifier.py`; no section of this document restates a shape
that is not declared there, and no consumer asks either question for itself.

- **REACH — `WhatsAppJID.parse(v)` (`identifier.py:269-281`), today's behaviour, UNCHANGED.** Accepts
  any `v` containing `@lid` — `phone_digits == ""`, `key == "jid:<v stripped and lowercased>"`;
  accepts any `v` whose `normalize_phone` output carries at least `Phone.MIN_DIGITS == 7` digits —
  `phone_digits ==` those digits, `key == "phone:<digits>"`; refuses everything else with
  `IdentifierError`, which carries `.kind`/`.raw`/`.detail`. This is the RESOLUTION and INDEXING
  predicate and it stays liberal on purpose (F12; rejected item 7 prices making it strict instead).
- **STORABLE — new, one derived property on the same frozen dataclass.** A parsed JID is storable
  when the raw value's JID DOMAIN — the text after the LAST `@`, `""` when there is no `@` — is a member
  of the closed set `{"s.whatsapp.net", "lid"}`
  declared on the type. This is the WRITE-DOOR predicate and nothing else reads it. Recommended
  spelling: `WhatsAppJID.jid_domain` (the text after the LAST `@`, `""` when there is none) plus
  `.is_storable`. The SPELLING is the spec-writer's; the closed-set READING is not. **One fact makes the
  recommended spelling the only buildable one, and it closes a latitude the phrase "the raw value's JID
  domain" leaves open** (architect round-8 note): the frozen dataclass holds NO raw value — `parse` stores
  the NORMALIZED string, `str(raw).strip().lower()` (`identifier.py:266`, `:273`, `:277`, `:281`) — so
  `jid_domain` is computed off `self.jid`, which makes it case-insensitive for free and
  `447700900321@S.WHATSAPP.NET` storable without a second rule. There is no second place to read the domain
  from, so no build has to choose. **An earlier draft
  of this bullet also licensed a bare "has a non-empty suffix" test as an equivalent option, and that
  licence is DELETED** (architect round-2 note 1, and class E below is what depends on it): under the
  bare-suffix reading Thrandell's `447700900789@example.com` becomes storable, class C empties, class E
  ceases to exist and the census measures a different population — so the reading changes the class
  table's MEMBERSHIP rather than its wording, which makes it this document's call rather than a latitude
  to hand on. Widening the SET later is still free and still joins the sweep automatically, because the
  ACs call the predicate rather than restating its membership.
- **ABSENCE — asked BEFORE either predicate, and never refused.** An absent key, `""` and `None` all
  introduce NO identifier, so neither predicate is ever called on them and neither can refuse them. This
  is not a third predicate and not a concession — it is the package's own existing convention
  (`_project_identifiers`'s `add()` returns on a `None` or blank raw BEFORE parsing, `person.py:318-320`),
  stated here because leaving it implicit made the refused population read as including it (F16). **The
  refused population is the NON-EMPTY values that fail STORABLE**, and no arm in this document ever
  refuses the absence case.

Each AC's expected value comes from those two calls — with the emptiness test ahead of them — and never
from a literal a test author read off the
same source as the implementation. The table has SIX cells: the absence case **Ø**, settled before either
predicate runs, plus the FIVE classes of a NON-EMPTY value, which partition `parse`'s outcome space. Two
of the six arrived as corrections rather than as design — class E after the AC red-team's round-1 minor
finding and the architect's round-2 note 2, and class Ø after the architect's round-3 finding and the AC
red-team's round-2 finding, which independently found `""`/`None` mis-filed under D (F16):

| class | predicate result | exemplar | where its member can live (F17) |
|---|---|---|---|
| **Ø** | introduces NO identifier — not a parse outcome; classified before `parse` is called, and ACCEPTED at every write arm | key absent, `""`, `None`, YAML null | frozen corpus (21 notes, free) |
| **A** | parses, `phone_digits` non-empty, storable | `447700900321@s.whatsapp.net` | test module's temp vault ONLY |
| **B** | parses, `phone_digits == ""`, storable | `15555550142@lid` | frozen corpus (the person representative) |
| **C** | parses, `phone_digits` non-empty, NOT storable — the Kim Faura class | `"+44 7739 341679"`, `447700900789@example.com` | frozen corpus (a NON-representative note) |
| **D** | NON-EMPTY and does not parse | `"n/a"`, `"ask Kate"`, `"notaphone@s.whatsapp.net"` | test module's temp vault ONLY |
| **E** | parses via the `@lid` SUBSTRING, `phone_digits == ""`, NOT storable | `447700900654@lid.example` (the red-team's minimal form is `123@lid.example.com`) | test module's temp vault |

**The fourth column is not bookkeeping — two cells are INADMISSIBLE in the frozen corpus and one exemplar
had to be respelled to stay admissible anywhere (F17).** WI-016's privacy wall scores every email-shaped
token in the corpus's reach against RFC 2606 / RFC 6761 and `s.whatsapp.net` is a real domain no RFC
reserves, so no class-A member — and no `@s.whatsapp.net`-spelled class-D member — can exist in
`tests/fixtures/vault/` or in `tests/fixture_vault.py` at all. That is not a spelling accident a different
exemplar fixes: STORABLE is membership of the closed set `{"s.whatsapp.net", "lid"}`, so a phone-bearing
storable value carries exactly that domain by definition. Class E's earlier exemplar
`447700900456@lid.example.com` was wall-RED for a different reason — `lid.example.com` is a SUBDOMAIN of
`example.com` and the reserved-domain frozenset matches by EQUALITY — and respelling it to a reserved TLD
keeps it the same cell. Every digit run above is an UNUSED member of the Ofcom drama block or of NANP
555-01xx, which the wall's phone predicate reserves and the corpus does not already claim (F17 leg 3).
One plant is not a cell of this table and is easy to lose for that reason: AC-5 also requires a note
carrying TWO JIDs — one class-A value and one class-B value on the SAME note — which is what proves a
person keeps both identifiers across the migration. It lives in the test module's temp vault like every
class-A member, and its pair is pinned to its own unused runs, `447700900987@s.whatsapp.net` and
`15555550163@lid`, rather than reusing the exemplars above: two entities in one materialized vault
sharing a `phone:`/`jid:` key mint a conflict `_index_identifiers` does not raise on (F17 leg 3,
extended).

**Class Ø is a CELL of the table rather than a footnote to it, deliberately.** It is the most populated
cell in the corpus by an order of magnitude (21 of the 22 `whatsapp`-carrying fixture notes, F6) and it is
the one cell the classifier must file WITHOUT calling `parse` — because `parse` raises on `""` and `None`
exactly as it raises on `"n/a"` (`identifier.py:271-275`, re-read this round; `if not s: raise` has no
blank branch), so a classifier that asks the predicates first files the whole corpus as class D. The
ORDERING is therefore the entire content of the cell, which is why it is asserted (AC-1) rather than
described.

**Why E exists, and why a four-cell table was not a partition.** `parse` tests for the SUBSTRING
`"@lid"` anywhere in the value, not for an `@lid` SUFFIX (`identifier.py:276`, re-read this round). So
`"123@lid.example.com"` returns `WhatsAppJID(jid="123@lid.example.com", phone_digits="")` with
`key == "jid:123@lid.example.com"`, while its `jid_domain` — the text after the last `@` — is
`"lid.example.com"`, not a member of the closed set. It parses (so not D), has no phone digits (so
neither A nor C, both of which require non-empty `phone_digits`) and is not storable (so not B). The
four-cell table had nowhere to put it, which made AC-1's "classification asserted exhaustive" false for
that input while every planted exemplar still went green.

The exemplar the plants use is the PHONE-DIGIT-BEARING variant `447700900654@lid.example` rather
than the red-team's minimal `123@lid.example.com`, deliberately: both are class E, but only the first
discriminates "took the `@lid` branch" from "fell through to `normalize_phone`" — the short form carries
fewer than `Phone.MIN_DIGITS` digits before the `@`, so a build that lost the `@lid` branch entirely
raises on it and would look correct for the wrong reason, while the long form silently acquires a phone
key. The domain is `lid.example` rather than `lid.example.com` because the second is wall-RED
(`example.com` is matched by EQUALITY, so a subdomain of it is not reserved) while the first ends in the
reserved TLD `.example` — the SAME cell either way, since what makes it class E is that the domain after
the LAST `@` is outside the closed set while the `@lid` substring is present (F17 leg 2). E's behaviour
is fully determined by the
design as it already stands — no new mechanism: it is indexed like B (no `_phone_index` entry, because
`phone_digits` is empty), resolved like B (through its `jid:` key, because it parses), REFUSED at the
write door like C (because it is not storable) and left byte-identical by the migration like D (because
it is not repairable — there are no phone digits to spell as a JID). **Its live population is expected
to be zero** (F6 measures zero `@lid`-bearing values of any kind in the fixture corpus; the census
precondition says what the live vault holds) — and it is ASSERTED rather than assumed, because "very
likely empty" is exactly the kind of cell that stays green while unclassified.

Four properties of that table are load-bearing and none is arbitrary. **Class Ø is not a refusal class**:
it is the ONE cell whose members every arm accepts, which is what makes clearing the field a legal write
and therefore what makes the D+E residual repairable at all (F16). **Class C is always
phone-bearing**, by construction and now by E's carve-out: a value with no `@lid` substring parses only
via its digits, so every class-C value has a non-empty `phone_digits` and therefore a `key` of
`phone:<digits>` — which is why C is REPAIRABLE key-preservingly (F13 leg 3). E is the case that used to
dent this claim, and separating it is what restores it: E is not a class-C member, is not repairable,
and therefore the refusal population that persists after the migration is **D plus E**, not D alone.
**Class D is not a subset of "has no suffix"**: `"notaphone@s.whatsapp.net"` carries a JID domain and
still fails `parse` (pinned today at `tests/test_identifier.py:140`), so the two predicates are
genuinely independent and a build that conflated them is RED. And **"not storable" is not a synonym for
"does not parse", in either direction**: C and E parse and are not storable, D does neither, and a value
can carry a JID domain and still fail `parse` — which is why every criterion below names the CLASS it
means and never "valid" or "malformed".

**THE TERMINAL-STATE PARTITION — what the vault looks like when the migration has SUCCEEDED, stated once
here and restated in the four places that carry an exit figure (F21).** Every previous draft answered this
with an absolute — "zero notes left in the scalar shape" — and that absolute is unreachable by
construction, because a shape conversion is a write that RE-INTRODUCES `whatsapp` and AC-3 refuses a
non-storable value at every arm in both shapes. So:

After the migration every `whatsapp`-carrying note is in exactly ONE of three parts, and the three are
what every exit figure ranges over:

1. **MIGRATED** — the note's value or values are in the LIST shape. This part contains every class-Ø note
   (`""` → `[]`, shape-only), every class-A and class-B note, and every class-C note the repair pass
   rewrote key-preservingly.
2. **RESIDUAL R** — the notes whose stored NON-EMPTY value the STORABLE predicate refuses and which
   therefore cannot be converted at all: each is REPORTED (by the run's own per-cell counts and,
   persistently, by AC-3's REPORT-LEG detector) and left BYTE-IDENTICAL, which means it stays in the SCALAR
   shape BY DESIGN rather than by omission. **R's membership is per Ruling B's arm** — D + E under the
   recommended arm (class C repaired), **C + D + E under the alternative arm** (repair declined) — and
   `|R|` EQUALS the census's class-D plus class-E rows, plus its class-C row under the alternative arm.
3. **Nothing else** — the count of notes left in the scalar shape OUTSIDE R is ZERO. That is the honest
   form of the old absolute, and it is still an oracle and still falsifiable, with the detector's issue
   count for R as an independent second witness rather than the migrating process reporting on itself.

Two conjuncts travel with the partition because without them it is satisfiable by harm. **The migration
NEVER CLEARS a value to make a note convert.** Emptying a class-D value would move it out of R and into
part 1 and would reach zero-outside-R trivially — silent data loss on exactly the population the item
exists to preserve. It is already red on AC-5 leg (c)'s TOTAL-value count (1 → 0), but that guard catches it
as a side effect; stated here and asserted in leg (e) it is red BY INTENT. Clearing is a hand repair a
person ASKS for through the delta arms (AC-3's CLEARING leg), never something the run does. And **the
reconciliation identity holds over the TRIPLE, not over one number**: the dry run's counts, the write's
counts and the readback's counts agree part-for-part across (scalar-outside-R = 0, migrated, R), or the run
reports loudly and exits non-zero.

**One consequence, stated while the fold is open because it is the honest form of F7's "refusing the scalar
form is a separate item or never".** The tolerant reader can never be CONTRACTED while any member of R
survives: expand → migrate → contract is a three-phase pattern and this item ships the first two, with the
third gated on R reaching zero by HAND repair, not on this item and not on any schedule this item can
promise. That is a fact about the design rather than a debt this item incurs — the alternative is refusing
the scalar at read time, which rejected item 3 already priced as converting an un-migrated note into an
invisible one.

**THE ABSOLUTES SWEEP (F21's class closure), declared here as the conductor note requires.** The generator
of this round's defect is an ABSOLUTE promise — "zero", "every", "all", "never" — stated over a population
that another criterion carves a residual out of. Every absolute in the AC descs, `## Intent`, `## Approach`
and `### Examples of done` was read this round and given its population and its excluded residual. The
sweep found ONE unsatisfiable absolute, stated in THREE places (the zero-scalar exit number — AC-5 leg (e),
`## Approach` step (4) and `### Examples of done`, all three replaced by the partition), and FOUR absolutes
that were true but SILENT about their scope (all four scoped by this fold; none of them changes what any
build does). The rest are total over their stated population with no residual, and they are listed so an
unswept absolute is not mistaken for a clean one:

| absolute | population it ranges over | residual excluded | this fold |
|---|---|---|---|
| `## Intent` "never reaches a person note" | WRITES arriving at any arm after this lands | values ALREADY on notes — sentence three owns those, and they are R | scoping clause added |
| `## Intent` "Every writer refuses it at the boundary" | AC-3's DERIVED arm set plus the two whole-record-projection arms | none | unchanged |
| `## Intent` "nothing already written is silently dropped" / "never erased" | every note, every cell | none — total, and it is what CREATES R | unchanged |
| `## Intent` "emptying the field is always allowed" | every arm, every class-Ø spelling | none — total | unchanged |
| `## Intent` "a person who has two of them keeps both" | PARSEABLE stored values (AC-5 leg (c)'s oracle scope) | class D, whose guarantee is byte-identity instead | already scoped by leg (c) |
| `## Intent` "never mistaken for a telephone number" | values whose `phone_digits` is EMPTY (classes B and E) | classes A and C, where the digits ARE a phone number and pivot on purpose | already scoped in AC-1 |
| `## Approach` step (4) "zero notes left in the scalar shape" | — | — | **UNSATISFIABLE (1 of 3); replaced by the partition** |
| AC-5 (e) "with zero notes left in the scalar shape" | — | — | **UNSATISFIABLE (2 of 3); replaced by the partition** |
| `### Examples of done` "the readback reports zero notes left in the old shape" | — | — | **UNSATISFIABLE (3 of 3); replaced by the partition** |
| `## Approach` step (4) / AC-5 (e) "counts reconcile or exit non-zero" | the TRIPLE above | none | restated over three parts |
| AC-1 "each cell asserted non-empty", "NO fall-through bucket" | the enumerated table, the corpus, the named probe list | not claimed over every string in the language (class E was the counterexample) | already scoped |
| AC-3 "every write arm refuses" | NON-EMPTY values failing STORABLE | class Ø, accepted at every arm | already scoped |
| AC-3 REPORT LEG "never travels as `NOT_RENAMEABLE_MARKER`" | every issue the new check emits | none — total | unchanged |
| AC-3 APPEND-ONLY "every Cut-0 pair present" | `PersonRepository.save`'s 29 recorded pairs | none — total | unchanged |
| AC-4 (b) "for every NON-STORABLE member the RAW string survives" | classes C, D, E | none — total | unchanged |
| AC-4 (c) "after any gated write the bytes carry the LIST form" | writes that SUCCEED and introduce the field | R, where no such write exists — the delta rule already carves the unrelated write, and R's notes keep the scalar spelling because the introducing write is REFUSED, not because the leg is violated | scoping clause added |
| AC-4 (d) "a fixed point for every member the door accepts" | accepted members; refused members get the refusal-with-unchanged-bytes fixed point | already partitioned | unchanged |
| AC-5 (a) "leaves the tree byte-identical" | the dry run, whole materialized tree | none — total | unchanged |
| AC-5 (b) "every write goes through `vault_io` and the gate" | every write the migration makes | none — total, and it is the second half of what forces R | unchanged |
| AC-5 (c) key multiset unchanged | PARSEABLE values only | class D (no key) and class Ø (no value) | already scoped |
| `### Examples of done` "returns that person and only that person" | the two JIDs on the two-JID note, both parseable | none over that population | unchanged |
| `### Examples of done` "the lid is never answered back as a phone number" | values whose `phone_digits` is empty | classes A and C, which pivot on purpose | already scoped in AC-1 |
| `### Examples of done` "then all three refuse" | the three doors it names (PATCH, the skill, a bare `update_frontmatter_field`) — an instance of AC-3's derived arm set, not a claim about all arms | none | unchanged |
| `### Examples of done` "nothing erases it" / "every time the linter runs" | every note in R, every linter invocation | none — total, and the detector's `auto_fixable is False` is what keeps it true under `--fix` | unchanged |
| `### Examples of done` "every person reachable by exactly the same identities" | parseable values | class D, never reachable before or after | scoping clause added |
| `### Examples of done` "succeeds through any of the package's doors" | the door judges the value the WRITE carries, so a repaired payload lands everywhere | a re-save that re-introduces the UNREPAIRED value still refuses — that is AC-3's `save` arm, not an exception to the repair | scoping clause added |

Whether the STORABLE predicate exists at all is **Ruling A** below. It is Dave's call, not the
spec-writer's, because it touches his ruling (1).

### Findings (each with the predicate it was settled by)

Currency for every in-tree predicate below: this worktree as the drive seeded it — git HEAD `c93006a`
plus the seeded uncommitted delta — using the granted tools (Read, Grep, Glob; no shell). Re-run any of
them to contradict a number.

**F1 — A pydantic field type cannot satisfy the Intent. This is the load-bearing finding.** "Every
writer refuses it at the boundary" is a claim about doors, and three of them never touch a model:
`update_frontmatter_field(path, "whatsapp", "+44 7739 341679")` (`writer.py:385`),
`update_frontmatter_fields` (`writer.py:443`) and `update_fields(person, {"whatsapp": …})`
(`base.py:728`) each hand a caller's untyped value to `gate_write` and then to `write_frontmatter`. The
first of those is already recorded as a live bypass (`docs/write-door-bypasses.md:3993-3996`, parked
defect 5). The one surface all of them share is the semantic gate, and `tests/test_name_gate_wall.py`
already proves BY DERIVATION that no frontmatter-writing arm routes around it. **So the enforcement
point is `gate_write`, and the model's field type is a convenience for typed consumers — not the
wall.** Predicate: `rg -n 'gate_write' --glob '*.py'` (23 sites, one per arm plus the walls);
`rg -n 'whatsapp' obsidian_schemas/name_gate.py` → 0 matches.

**F2 — The gate arm must judge TWO shapes, and an arm copied from `emails`/`phones` would be inert.**
The container rule is `_shaped` — a POSITIVE predicate, `isinstance(value, list) and all(isinstance(m,
str))` (`name_gate.py:181-198`) — under which a bare `str` falls to pass-through untouched, by design.
Every `whatsapp` value on disk today is a bare `str`. An arm modelled on the existing containers would
therefore be structurally silent for exactly the population this item exists for. The whatsapp arm
judges a scalar `str` AND a list of `str`.

**F3 — Refuse, not keep-verbatim; and the gate's own two precedents are the reason.** `emails[]`
normalizes and keeps an entry no parser accepts VERBATIM (`name_gate.py:399-403`); `name` REFUSES
(`:359-365`). The containers keep-verbatim because a measured live population of unparseable entries
exists and discarding it would be data loss; `name` can refuse because the gate judges the DELTA and
never the merged record, so a stored-dirty note stays writable for every write that does not
re-introduce the dirty field (`name_gate.py:31-36`). `whatsapp` sits with `name`: refusal is what the
Intent asks for, and the delta rule is what makes it survivable. Whether refusal is AFFORDABLE against
the live corpus is the first precondition's question — the closest committed figure, 276 phone/whatsapp
values with 0 refused by `Phone.parse` (`docs/identity-cutover-corpus-audit.md:132`), is dated
2026-09-06, does not separate `whatsapp` from `phones`, and counts no `@lid` at all.
**AMENDED by F12, F13 and F16, three times.** (i) The population refusal must be affordable against is
class **C + D + E**, not "values `Phone.parse` refuses" — and C is the big one, because every bare number
in the field is a C. (ii) The delta rule makes refusal survivable at the three dict arms and NOT at the
whole-record-projection arms (`PersonRepository.save` and `write_markdown_file(entity=…)`, F11's
correction); so where affordability actually bites is those arms, and it is F13's subject rather than this
finding's. (iii) The population is NON-EMPTY: class Ø is accepted everywhere, so the affordability
question is never asked of the 21-of-22 population that carries no identifier at all (F16). Getting that
wrong does not merely misprice the answer — it prices the wrong question.

**F4 — "Naming the value" collides with the gate's refusal contract, and `IdentifierError` already
shows the way through.** `_refuse` admits NO note-derived value into the exception it constructs
(`name_gate.py:142-174`) — not the path, not the declared type, not the cause — because refusal
messages render in tracebacks over private notes. `IdentifierError` puts only `detail` in its message
and carries `.kind`/`.raw`/`.detail` as ATTRIBUTES (`identifier.py:76-80`). So the Intent's "loudly and
naming the value" is satisfied by an attribute on the refusal, never by its message. Decided, not open.

**F5 — A lid string has no resolution door at all.** `resolve_all`'s cascade (`person.py:628-690`) has
no `whatsapp_jid` step: step 2 routes an `@`-bearing query to `get_by_email`, and `Email.parse("…@lid")`
refuses (no dot in the domain, `identifier.py:167-168`); step 4 normalizes to digits and reaches the
phone door — wrongly when the lid has ≥7 digits, not at all when it has fewer. The `jid:<lid>` key is
read by exactly one frame, `_resolve_identifier` (`person.py:902-908`), reachable only from
`resolve_or_create` by a caller who already holds a typed `Identifier`. A public
`get_by_identifier(Identifier)` plus a cascade step is the missing half — NOT a new index.

**F6 — The fixture corpus cannot tell a correct build from a wrong one here, so the discriminating
members must be PLANTED (WI-286).** Predicates: `rg -n -i 'whatsapp' tests/fixtures/vault` and
`rg -c '^type: person' tests/fixtures/vault`. Result: 22 of the 25 `type: person` notes carry a
`whatsapp:` key; 21 of those are `""`; exactly ONE is non-empty —
`tests/fixtures/vault/@Thrandell Ibberly.md:7`, `447700900789@example.com`, which `WhatsAppJID.parse`
ACCEPTS as phone-bearing (the anonymized domain is irrelevant: `normalize_phone` splits at the `@`).
Zero `@lid` values, zero list-shaped values, zero values the parser refuses. `rg -n -i 'whatsapp'
docs/vault-shape-census.md` → 0 matches, so the digest-frozen ground truth says nothing about this
field either. Cost of planting inside the frozen corpus: one `CORPUS_DIGEST` regeneration
(`tests/fixture_vault.py:21-25`, `:44`) — and NOTHING in `docs/vault-shape-census.md`, which this item
does not touch at all (F18 leg 1 carries the derivation; the earlier text of this sentence priced "if
the plant declares a new class, a census row" as a free build-side edit and that was wrong on both
halves). That cost is the spec-writer's choice against an inline temp-vault
note, not an open question for Dave.
**AMENDED by F12 — a reading correction.** Re-read against the class table, Thrandell's
`447700900789@example.com` is not "an accepted value whose domain is irrelevant" but a class **C**
member: it parses, it is phone-bearing, and it carries no JID domain (its `jid_domain` is
`"example.com"`, not in the closed set). E is the plant the WI-286 rule most obviously demands, because
its live population is expected to be zero and a corpus-trusting test would therefore never see the cell
at all.
**AMENDED AGAIN, with the class-Ø fold, and this time it corrects a COUNT rather than a reading.** The
plant list this finding carried (B, D, E) was short by one: the 22 matching lines are 21
`whatsapp: ""` plus Thrandell's single non-empty value, so the corpus supplies class **Ø** (21 members,
no plant needed — it is the corpus's dominant cell and the reason F16 exists) and supplies NO member of
A, B, D or E. Class **A** — a storable phone-bearing JID — has no corpus member either, which the
earlier list missed because it read the corpus for `@lid` and for unparseables and not for the happy
path. Predicate, re-run for this fold: `rg -n -i 'whatsapp' tests/fixtures/vault` → 22 lines, enumerated
above.
**AMENDED A THIRD TIME, and this one retracts a claim rather than extending it: class C was never FREE,
and "plant it in the corpus" is not available to every cell.** Two prior folds of this finding said the
corpus supplies class C at no cost and left the plant-versus-temp-vault choice to the spec-writer as a
matter of taste. Both are wrong, and F17 carries the derivation: Thrandell is the corpus's SOLE person
`roundtrip_representative` and two in-tree tests write it through the gated whole-record door asserting
NO refusal, so keeping a class-C value there makes a correct build red and invites a builder to delete the
repo's only proof that a whole person field set survives the write door; and WI-016's privacy wall makes
classes A and D structurally inadmissible ANYWHERE in the corpus's reach, which is itself why the corpus's
one JID is spelled `@example.com` and therefore class C in the first place. **The corrected accounting:
class Ø is free (21 notes); classes B and C are corpus EDITS, not free members — B replaces the
representative's value, C moves onto a non-representative note; classes A, D and E are plants in the new
test module's own temp vault and never enter the frozen corpus.** So the earlier instruction "the plant
must KEEP Thrandell's value rather than tidy it" is superseded: the VALUE is kept, the NOTE it sits on
changes. The cost of the corpus edits is the one already priced here — a `CORPUS_DIGEST` regeneration
(`tests/fixture_vault.py:21-25`, `:44`) plus the manifest overrides that move with the values
(`tests/fixture_vault.py:225`, whose declared value becomes the LIST form, `:94`'s default, and the
receiving note's spec) — **and NO census row, because `docs/vault-shape-census.md` is not this item's to
edit: its digest is asserted against a literal inside WI-016's SIGNED AC-3 criterion and its row
vocabulary has no cell a `whatsapp` value could occupy (F18 leg 1, which retracts the clause this
sentence used to carry).** One consequence to check
at build time rather than assert here: after Ruling A,
`PersonRepository.save(<a class-C note>)` REFUSES (F13), which is precisely why the class-C value must
not sit on the representative. The granted tools here are Read/Grep/Glob with no shell, so
the suite cannot be run from inside this cage; this is named as a spec-writer check, not a measured
claim.

**F7 — The scalar→list flip has NO atomic window, so the reader accepts both shapes.** HAL9000 and
exocortex install this package `-e` (`CLAUDE.md`, "Both HAL9000 and Exocortex will pick up the
change"), so the new schema is live for them the moment the commit lands in the main checkout, while
every un-migrated note still carries a scalar. And an un-migrated note does not degrade gracefully: a
`type: person` note that fails `model_validate` raises `SchemaDriftError` (`parser.py:203-208`), which
the load path records as a SKIP — the note becomes INVISIBLE to every consumer rather than oddly
shaped. Expand → migrate → (optionally, later) contract is therefore forced: the reader accepts scalar
and list from the day the field changes, every write emits the list form, and refusing the scalar form
is a separate item or never.
**AMENDED by F14 — do not carry this finding's ARGUMENT forward, only its conclusion.** Grounding "no
atomic window" on `-e` installs invites the counter "then pin a version", which fixes nothing. The
packaging-independent reason is that the VAULT is shared mutable state: any consumer running older code
against a migrated note breaks however the package is installed. F14 also points the hazard backwards,
which is where the back-out lives.

**F8 — A typed value object sitting in `model_fields` would corrupt every note it is written to — and
this is one of the two reasons the stored field is NOT `list[WhatsAppJID]` (F13).**
`model_to_frontmatter` hands `getattr(entity, field_name)` straight through (`writer.py:112-117`) and
`write_frontmatter` calls `yaml.dump` with PyYAML's default `Dumper` (`writer.py:152`), while
`parse_frontmatter` reads with `yaml.safe_load` (`parser.py:101`). A frozen dataclass on a model field
therefore serializes under a `!!python/object:` tag that this package's own reader cannot load. So "the
field's type IS `WhatsAppJID`" is honoured at the BOUNDARY — parsed on the way in, projected back to
its stored string on the way out — unless the writer gains an explicit projection step for identifier
values. The two citations are read facts; the tag text is an inference, and it is a one-line run to
confirm (`yaml.dump({"whatsapp": [WhatsAppJID.parse("447700900321@s.whatsapp.net")]})`) which the spec
should do before Task 1 rather than after.
**AMENDED by F13: the projection task is DELETED from scope.** Keeping the stored field `List[str]`
means nothing dataclass-shaped is ever in `model_fields`, so there is nothing for `writer.py` to
project and the hazard is closed by construction rather than by a step that could be forgotten. The
assertion survives anyway as a cheap guard (AC-4 leg (b): no `!!python/object` tag anywhere in the
written bytes), because it catches the mistake whichever way an implementation goes — and it is now
the ONLY thing standing between a future "let's annotate it properly" change and unreadable notes.

**F9 — RETRACTED, AND REPLACED BY F19: the linter's report surface does NOT come free, because
`_gate_refusal_pattern` is not a detector and its one call site never reads `whatsapp`.** The two read
facts this finding was built on are true — `_gate_refusal_pattern` runs the door over a note's WHOLE
stored record purely to REPORT its refusal pattern (`scripts/lint_vault.py:334-352`), and `apply_fixes`
gates only the DELTA (`whole_record=False`, `:1181`) — but the CONCLUSION drawn from them was taken from
that function's docstring without reading where the function is CALLED, and both halves of it are wrong.
(i) The report path does not exist: `_gate_refusal_pattern` has exactly ONE call site (`:450`), inside
`check_structural`'s `stem_name_divergence` arm and behind `stem != stored` (`:449`), and its return
value is spliced into THAT issue's message as a marker (`:451-454`) — it emits no `LintIssue` of its own,
and `rg -n 'whatsapp' scripts/lint_vault.py` is still 0 matches. (ii) The `--fix` half is true for a
different reason than this finding gave: what keeps a malformed-JID note fixable is that no auto-fixable
rule's DELTA contains `whatsapp` at all, not the refusal carrying its own `pattern`. The `pattern`
requirement survives on F18 leg 4's reasoning instead — it is what stops a bad JID being routed as a bad
name — and the report surface is a NEW report-only detector arm, which F19 derives and prices. This
finding is kept in place rather than deleted because five other passages in this document cite it for a
guarantee it cannot deliver, and a reader who follows one of them has to land on the retraction.

**F10 — Where the structure lives (the Phase-3 question).** The bridge store holds both a phone-JID and
an `@lid` for the same person; the note holds one string. The structure is discarded at the WRITE seam
by whatever sync collapses two identifiers into a scalar — not at read time. So the first task is the
field's cardinality and the write door, and there is no read-time reconstruction to design. That is
also why the WI-035 lid→phone pivot (`identifier.py:24-25`) is NOT this item's mechanism: the pivot
exists to recover a phone the note never stored, and the fix is to store both.

**F11 — `PersonRepository.save` has a rider that must grow one line, and it is caller-visible.** The
rider writes the gate's normalized containers back onto the model (`person.py:1190-1194`,
`entity.emails`/`phones`/`aliases`). A gated `whatsapp` needs the same write-back, which is a NEW
in-place mutation a caller holding a `Person` will observe — the same CLASS of disclosure WI-021 made
for `phones[]` (`person.py:1180-1184`). **That citation names the disclosure's SHAPE and its neighbourhood,
never a paragraph to extend: every line of `save`'s docstring is frozen verbatim by WI-024's prose wall and
this item's disclosure is APPEND-ONLY in that frame — new paragraphs, the existing lines byte-identical
(F20, which is a constraint on this finding's remedy rather than a correction to the finding).** Also
`_remove_entity_from_indexes` (`person.py:412-416`) mirrors the defective index insert and moves with it.
**AMENDED by F13.** That rider is not only a disclosure about in-place mutation. `save`'s gate call runs
over `model_to_frontmatter(entity)` (`person.py:1190-1191`), so it is an arm where a value the note
ALREADY stores is re-introduced by the projection and therefore judged — which makes `save` a REFUSAL
surface, not just a normalization rider. F13 owns that. **CORRECTED (architect round-3 note 2, re-read
this round):** `save` is not the ONLY such arm and `whole_record` is not the discriminant.
`writer.py:229-233` — the ENTITY arm of the exported `write_markdown_file` (`__init__.py:119`) — passes
`whole_record=True` too, and it is the arm `BaseRepository.save` delegates into (`base.py:462-465`), which
is why one `PersonRepository.save` gates TWICE by design (`name_gate.py:296-299`). What makes a stored
value judged is that the PAYLOAD CONTAINS THE KEY — `gate_write`'s own docstring says the flag "makes the
dict-shaped arms `False` even when their payload happens to be the whole note" (`name_gate.py:289-294`),
and all the flag itself enables is the two cross-field migrations (`name_gate.py:385`). The substance of
F13 survives whole; the HANDLE is "any arm whose payload is a whole-record projection", which is `save`
AND `write_markdown_file(entity=…)`. AC-3's coverage is unaffected — `frontmatter_write_arms`
(`tests/derivations.py`) already sweeps the writer entity arm, so the derived-by-equality set contains it.

**F12 — The parser is a REACH predicate, and "the field's type IS `WhatsAppJID`" therefore does not
by itself refuse a bare telephone number. Ruling (1) rests on a description of the type that the type
does not honour.** Predicate: read `identifier.py:269-281`; `parse` tests for `@lid`, then for
`normalize_phone(s)` yielding ≥ `Phone.MIN_DIGITS == 7` digits, and tests for a JID suffix NOWHERE.
So `WhatsAppJID.parse("+44 7739 341679")` returns `WhatsAppJID(jid="+44 7739 341679",
phone_digits="447739341679")`, `key == "phone:447739341679"`. Its whole refusal yield over realistic
data is digit-less junk.

The reason this is not simply "the ruling is wrong" is worth stating precisely, because it decides who
owns the fix. Dave's ruling (1) describes the type as accepting "`<digits>@s.whatsapp.net` (pivots to
`.phone`, keys `phone:<digits>`) AND `<digits>@lid`" — i.e. exactly the two SUFFIXED forms. That
description is the STORABLE predicate. The code is wider than the description. So the ruling and the
code disagree on a fact, and the honest move is to hand Dave the disagreement (Ruling A) rather than
pick a side inside a document he is about to sign.

Why a derived property on the same type is the recommended arm rather than narrowing `parse` — the
blast radius, measured in-tree:

- `parse_identifiers(..., jid=…)` defaults to `strict=True` and re-raises (`identifier.py:443-481`);
  it is the declared "seed of the Phase-4 adapter (`find_or_create_stub` will call it)", so a strict
  `parse` turns a bare number handed by a phone-only channel from "resolves" into "raises".
- The WI-035 pivot reads `isinstance(i, WhatsAppJID) and i.phone_digits` (`person.py:832`) and
  `_resolve_identifier` branches on the same type (`person.py:902`). Both want maximum reach — their
  job is to FIND a person, and a caller holding a bare WhatsApp number is the normal case.
- Two in-tree tests store a bare number in `whatsapp:` on purpose and assert it unifies with
  `phones[]`: `tests/test_repositories.py:33` (`whatsapp: "447990558521"`, read by
  `test_get_by_phone_whatsapp_jid` at `:316`) and `tests/test_identity_index.py:80`
  (`whatsapp="447990558521"`, asserting ONE `phone:447990558521` key and no conflict). The second is
  the nastier cost: under a strict `parse` its assertion still PASSES — the key comes from `phones[]`
  alone — so the test silently stops testing the thing its name claims.

Two predicates on one type is still ONE authority: one module, one parser, no consumer asking the
question for itself. Liberal in what you accept for LOOKUP, conservative in what you STORE, with both
halves declared in the same twelve lines of `identifier.py`. That is what the ruling's "no second
spelling anywhere" is protecting, and this arm does not violate it — whereas a suffix regex written
inside `name_gate.py` would.

**F13 — What the model holds for a stored value the door would refuse is the design's real fork, and
one branch is silent data loss. This settles the field's annotation, which touches ruling (2).**
Predicates: `person.py:1190-1191` (`gate_write(model_to_frontmatter(entity), …, whole_record=True)`) and
`writer.py:229-233` (the exported `write_markdown_file`'s entity arm, the second such call and the one
`BaseRepository.save` delegates into at `base.py:462-465` — see F11's correction; the discriminant is that
the payload is a WHOLE-RECORD PROJECTION, not the flag); `writer.py:112-117` (`model_to_frontmatter` emits
EVERY declared field unconditionally, so `whatsapp` is always re-introduced); `writer.py:385`,
`writer.py:443`, `base.py:728` (all `whole_record=False` and all caller dicts, so the delta rule covers
them).

The fork, and why it cannot be left to the build:

- **If the reader DROPS a non-storable value (class C, D or E)** — which a literal `whatsapp: list[WhatsAppJID]`
  annotation forces, since an unstorable string has no inhabitant of that type — then the model holds
  `[]`, `model_to_frontmatter` emits `[]`, and the next `save()` ERASES the value from the note. Silent
  data loss, on exactly the population this item exists for, and it also destroys the evidence the
  linter's report arm exists to surface (AC-3's REPORT LEG — F9 claimed that arm already existed; F19
  retracts it and the arm is now built, which does not change this leg's conclusion, only what it cites).
  Unacceptable, and not a thing to discover from a build.
- **If it survives as a raw string**, `save()` REFUSES, and every note carrying a non-storable value —
  class C, D or E — is unsaveable through the repository's own door, which `create_stub`,
  `find_or_create_stub` and `_writeback_identifier` all route through.

Three decisions fall out, and only the first is Dave's:

1. **The stored field is `List[str]`, not `list[WhatsAppJID]`; typed access is a DERIVED accessor.**
   This is the only shape under which nothing is dropped at read time, and it also dissolves F8. It is
   the repo's own three-day-old precedent: WI-033 was minted on 2026-09-26 with "a derived
   `PersonRepository.introduced_by` accessor (no stored field)". It also keeps `whatsapp` shaped like
   its siblings — `emails`/`phones` are `List[str]` and typed at the identifier layer, not at the
   model. Ruling (2)'s INTENT — cardinality plus typed access — is served whole; the literal
   annotation is what changes, which is why it goes to Dave as **Ruling B** rather than to the
   spec-writer.
2. **`save()` refuses on a stored non-storable value — class C, D or E — and never erases it; and
   CLEARING the field is never a refusal, because class Ø is accepted everywhere (F16).** Those two
   halves are one decision: a refusal surface that also refused the blank value would leave the residual
   population with no repair door at all, since clearing is the only repair a class-D value has. The
   estate has already
   accepted refusal at `save` against a measured small population: the gate is a PREDICATE on `name`
   (`name_gate.py:38-46`) and the delta rule exists precisely so that the OTHER arms stay writable for a
   stored-dirty note (`name_gate.py:31-36`) — which is only a distinction worth drawing if the
   whole-record arm does refuse. That last step is an INFERENCE from two read facts rather than an
   executed check (this cage has no shell); the spec should confirm it by running a `save` over a note
   with a Tier-1 dirty stored name before leaning on the precedent, the same way F8's tag text wants a
   one-liner. Both directions get pinned by AC regardless — no erasure, and the refusal asserted rather
   than implied — because the two wrong builds are each individually self-consistent.
3. **Therefore the migration REPAIRS class C, which is what makes (2) affordable — and it repairs
   ONLY values whose `phone_digits` is non-empty.** Every class-C value is phone-bearing by
   construction (class E carves out the parseable-but-phone-less case that used to dent that claim), so
   `"+44 7739 341679"` → `"447739341679@s.whatsapp.net"` is key-preserving: `WhatsAppJID.parse` gives
   `phone:447739341679` for both spellings (`normalize_phone` splits at the `@`), so the identifier index
   is byte-stable across the repair and AC-5's readback oracle — stated over `.key`, see AC-5 — passes.
   The phone-bearing GUARD is not decoration: a repair applied to a class-E value would write
   `"@s.whatsapp.net"` (empty digits plus the suffix), which `parse` then REFUSES, turning a note the
   migration was supposed to leave alone into one nothing can read back. After the migration the
   `save`-refusal population is class **D plus class E** — digit-less junk plus any `@lid`-substring value
   whose domain is not a real JID domain, both reported by the linter and left for hand repair. **"Reported
   by the linter" is AC-3's REPORT LEG and nothing else** — a new report-only detector arm this item
   BUILDS, not a surface that already exists: the function this clause used to lean on,
   `_gate_refusal_pattern`, has one call site, behind a filename/stored-name divergence whose live
   population is zero, and it emits no issue of its own (F19, which retracts F9).
   The hand
   repair is a real door and not a phrase: for class E it is rewriting the value, for class D it is
   CLEARING the field, and both go through the delta arms, which accept class Ø (F16) and stay open for a
   stored-dirty note by the delta rule. Without F16's carve-out the sentence "left for hand repair" would
   have named a path the item's own door refuses.
   (Previous rounds said "class D alone"; that was the four-cell table's gap, not a change of design.)
   Whether to repair C during the migration or only report it is the second half of **Ruling B**:
   repairing it rewrites stored values (asserting a JID spelling for a number the note already claimed),
   and reporting it leaves N notes unsaveable until someone fixes them by hand.

**F14 — The back-out of a migrated corpus is not a library revert, and the tolerant reader is forced
by the SHARED VAULT rather than by `-e`.** Two corrections to F7, one of them to its argument and one
to its coverage. (i) F7 grounds "no atomic window" on `-e` installs, which invites "then pin a
version". The packaging-independent reason is that the VAULT is shared mutable state: any consumer
running older code against migrated notes breaks however the package is installed. State it that way
or the reader reaches for a version pin that fixes nothing. (ii) F7's hazard runs backwards too —
after the live migration, reverting this library is NOT a back-out, because a list-shaped note against
pre-WI-032 code fails `model_validate` and `parse_to_model` raises `SchemaDriftError`
(`parser.py:203-208`), making the note INVISIBLE rather than oddly shaped. So the back-out has to be
stated as a reverse migration through the same door, and it is EXACT only while no note has gained a
second JID — after that, list→scalar loses one by definition, and the position is forward-only. This
item does not itself populate second JIDs (that is HAL9000 WI-075 / orchestrator WI-192-193), so the
exact-reverse window is real and worth naming in the live bracket.

**F15 — One line that is easy to miss: the new cascade label needs a rank.**
`_RESOLVE_CASCADE_ORDER = ("exact-name", "alias", "email", "phone")` (`person.py:145`), and
`select_resolution`'s `rank` gives an unknown label `len(_RESOLVE_CASCADE_ORDER)` — last
(`person.py:190-197`). So a `whatsapp_jid` step that does not add its label ranks BELOW `phone` among
equal-confidence ties, which is the wrong answer when a lid and a fuzzy phone match tie. Pinned by
AC-2.
**AMENDED (architect round 7, note 1) — there is a SECOND `whatsapp_jid` ordering in the file and this
item does not touch it, which is worth stating because the item's own principle is "no second spelling
anywhere".** `_IDENTIFIER_PRIORITY = {"email": 0, "phone": 1, "whatsapp_jid": 1}` (`person.py:778`,
read this round) TIES whatsapp_jid with phone, and the class-body comment above it (`:772-777`) gives the
reason: "A phone-bearing WhatsAppJID resolves like a Phone (same number → same person), so it shares
phone's priority." The two orderings own different frames and both are right for theirs: `_IDENTIFIER_PRIORITY`
ranks the Branch-A BEST HIT among typed identifiers a caller already holds inside `resolve_or_create`, where
a phone-bearing JID and a phone are the SAME key and a tie is the correct answer; `_RESOLVE_CASCADE_ORDER`
ranks CASCADE LABELS in `select_resolution`, where the competing hits are an exact `jid:` key against a
FUZZY phone match and the exact one must win. So this item changes the cascade ordering (AC-2) and leaves
`_IDENTIFIER_PRIORITY` alone — which is also the cheaper reading, because that dict's explaining comment is
owned by the class `PersonRepository` and therefore frozen by the same wall F20 describes
(`prose_surface_cut0.json:1680-1683`): editing the tie would mean editing the sentence that justifies it,
which is not free. Stated here rather than asserted, because nothing changes.

**F16 — ABSENCE IS NOT MALFORMATION, and the reason it is a finding rather than a wording tidy-up is
that the refusal of `""` bricks this design's only repair channel. Class Ø exists because of this.**
Two gates found it independently (architect round 3, AC red-team round 2) in text no fold had touched;
every fact below was re-read in code for this fold rather than carried from either fence.

The mechanism: `WhatsAppJID.parse` refuses `""` and `None` through the SAME two lines it refuses `"n/a"`
with — `if raw is None: raise` then `s = str(raw).strip().lower(); if not s: raise`
(`identifier.py:271-275`) — and has no branch that special-cases blank. So a class table that files
"does not parse" as class D files `""` and `None` there, and a write arm built to refuse class D refuses
the blank value at every dict door.

Why that is a defect and not a strict-and-therefore-safe choice, in three steps:

1. **It is the corpus.** `whatsapp: ""` is the model's own default (`models.py:94`), the person
   template's value, the declared person oracle hand-transcribed into the frozen fixture corpus
   (`tests/fixture_vault.py:94`), and the value on 21 of the 22 `whatsapp`-carrying fixture notes (F6's
   predicate, re-run). So the consumer-visible break is against ~the whole corpus rather than against
   the C+D+E population the census is scoped to price — which changes what Ruling B leg 2 COSTS, not
   merely how it reads.
2. **It is the only clearing door the package has.** `writer.py:333-337`'s
   `update_frontmatter_field(path, field, value)` SETS a value; there is no delete or remove affordance
   anywhere in the writer, and `update_fields(person, {"whatsapp": None})` is the entity-side spelling of
   the same thing. Both hand the gate a class-Ø value. Ruling B leg 2 and AC-5 leg (e) both promise the
   D+E residual is "reported and left for hand repair", and for a class-D value there is nothing to
   repair TO — `"n/a"` and `"ask Kate"` carry no digits and no domain — so clearing the field IS the
   repair. An arm that refuses blank makes the one repair channel this document commits to unbuildable:
   remedy-is-the-disease, at exactly the delta arms `name_gate.py:31-36` exists to keep open.
3. **And no test in the drafted set would have noticed.** The entity path never constructs a literal
   `""` for the gate to judge: the stored field is `List[str]` with a `[]` default, `model_to_frontmatter`
   emits `[]` (`writer.py:112-117`), and an empty list has no member for a per-element arm to refuse. Only
   the three dict arms ever see a bare `""`, and none of AC-3's required members was blank. So the refusing
   build shipped GREEN on the whole suite — which is the buildable-two-ways condition, and the reason this
   is a frozen-AC-text fix rather than a build-runner inference.

The resolving rule is the package's own, not an invention for this item: `_project_identifiers`'s `add()`
returns on a `None` or blank raw BEFORE calling any parser (`person.py:318-320`), so absence already
introduces no identifier everywhere else in the library. The gate's `emails[]` arm draws the same line by
falsiness — a blank member is neither parsed nor kept (`name_gate.py:399`, the `elif entry and …` guard) —
so "blank introduces nothing" is the container precedent as well as the identifier one. Class Ø is that
rule promoted to a cell of the table so a classifier has somewhere to put it, and it is asserted at the
arms (AC-3's CLEARING and CLASS-Ø legs) because the refusing build is self-consistent.

One consequence worth stating so it is not rediscovered: this NARROWS the refused population to exactly
what Dave's ruling (1) describes, so it touches neither Ruling A nor Ruling B. It is a correction to this
document, not a question for him.

**F17 — THE FROZEN CORPUS IS NOT A BLANK PAGE WITH A DIGEST ON IT. It carries two live contracts of its
own, and the fixture-plant plan the earlier folds wrote was never checked against either. Both
collisions are corrections to this document's plant list; neither touches a ruling.** Two gates found
this independently in the same round (architect round 4, AC red-team round 3), and every fact below was
re-read in code for this fold rather than carried from either fence. This finding OWNS the fourth column
of the class table and the plant accounting in F6's third amendment.

**Leg 1 — the note the earlier folds appointed as the free class-C member is the corpus's ONE person
round-trip representative, and two in-tree tests write it through the gated whole-record arm asserting
NO refusal.** `@Thrandell Ibberly.md` carries `whatsapp="447700900789@example.com"` and
`roundtrip_representative=True` (`tests/fixture_vault.py:219-233`, re-read); `_representative` asserts
there is EXACTLY ONE such note per `declared_type` (`tests/test_fixture_vault.py:689-695`), so this is
not one specimen among several — it is THE note, and the flag's declared contract is that those notes
"declare their model's whole field set, which is what makes AC-2's round trip total for them"
(`tests/fixture_vault.py:13-14`). Two tests then write that entity through
`write_markdown_file(entity=…)` — the second whole-record-projection arm F11's correction added
(`writer.py:229-233`), which AC-3 names as a refusal surface:

- `tests/test_writer.py:404-428`, `test_corpus_note_round_trips_through_the_write_door` — the write is
  at `:421` and the assertion that every declared field survives, `whatsapp` among them, is at
  `:424-427`, with no `NameGateRefusal` anywhere in the test;
- `tests/test_fixture_vault.py:705-761`, the AC-2 type-registry sweep — the same write at `:753`, the
  declared-oracle comparison at `:755-761`, and at `:726-732` an assertion that the person
  representative is GATE-CLEAN "by the DOOR's own predicate".

Under the STORABLE predicate, `447700900789@example.com` parses (phone-bearing, digits `447700900789`)
and is not storable — class C by this document's own table — so a build that implements AC-3 correctly
makes both tests raise where they currently assert a clean round trip. That is blocking rather than a
build-time surprise because of the branch a builder reaches for when the battery goes red: "the round
trip now legitimately refuses, so change the test to expect that." That build is self-consistent and
green on every AC in this set, and it trades away the repo's only assertion that a whole person field
set survives the write door, in exchange for nothing this item asked for — licensed by an AC `why:` that
told the builder the class-C member was free.

**And this corpus has already solved this exact collision once, which is the fold.**
`docs/vault-fixtures.md:5938-5943` (WI-016's own build log, deviation 3) records the identical shape — a
representative must declare every field, a wall forbids the realistic value for one of them — and
resolves it IN THE CORPUS rather than in either rule: "the four representatives carry those fields empty
and four non-representative notes carry the URLs … No criterion moved." Fold the same way here: the
representative's `whatsapp` becomes a value the door ACCEPTS, and the class-C value moves onto a
non-representative note. Class A is not available to the representative (leg 2), so the accepting value
is class B or class Ø; **class B is recommended** — it keeps the representative's round trip carrying a
real value for this field rather than an empty collection, and it is wall-clean in the one spelling
below. The manifest override moves with the value as well as the field's shape:
`tests/fixture_vault.py:225` alongside `:94`, because `tests/test_fixture_vault.py:745-748` compares the
parsed attribute against the declared scalar.

**Leg 2 — two of the class table's exemplars cannot be planted ANYWHERE in the corpus's reach, and for
class A that is structural rather than a spelling accident.** WI-016's privacy wall:
`EMAIL_SHAPED = [\w.+-]+@[\w.-]+\.\w+`, `RESERVED_EMAIL_DOMAINS = frozenset({"example.com",
"example.net", "example.org"})` matched by EQUALITY, `RESERVED_TLDS = (".test", ".invalid", ".example")`
matched by suffix, and `_host_is_reserved` accepts only those two routes
(`tests/test_fixture_vault.py:302-319`, re-read); the live leg asserts zero violations per file and the
reach is every file under `tests/fixtures/vault/` PLUS the manifest module `tests/fixture_vault.py`
itself (`reach_files()`, `:386-392`). Applied to the literals:

- **class A — RED, and structurally so.** `s.whatsapp.net` is neither exact-reserved nor under a
  reserved TLD. STORABLE is membership of the closed set `{"s.whatsapp.net", "lid"}`, so a
  phone-bearing storable value carries exactly that domain BY DEFINITION — no class-A member can exist
  in the corpus's reach, and the representative therefore cannot be made class A.
  `docs/vault-fixtures.md:5944-5948` records this constraint already paid for: "A real JID
  (`<digits>@s.whatsapp.net`) is scored by `reserved_email_violations` against a domain no RFC reserves,
  so the corpus's JID is spelled `447700900789@example.com`" — which is the decision that made Thrandell
  class C in the first place.
- **class E — RED as previously spelled, cheap to fix, same cell.** `lid.example.com` is a SUBDOMAIN of
  `example.com`, which the frozenset matches by equality only, and ends in none of the three reserved
  TLDs. `…@lid.example` is wall-clean and still class E: it contains the `@lid` substring so it parses
  with empty `phone_digits`, and its domain after the LAST `@` is `lid.example`, outside the closed set.
- **class D — RED if planted in the reach**, by the same mechanism as class A, for the
  `notaphone@s.whatsapp.net` member specifically. It is admissible in a test module's own literals,
  which is where AC-1's independence leg needs it.
- **class B — admissible, with a constraint nobody had stated.** `@lid` carries no dot after the `@`, so
  it is not email-shaped and the email wall never sees it — but `reserved_phone_violations` does
  (`:342-361`), and it demands a match against the drama block or NANP 555-01xx
  (`RESERVED_PHONE_PATTERNS`, `:308-312`). `15555550142@lid` passes the third pattern, and its 10-digit
  form `5555550142` is exactly the counterpart AC-1's class-B falsifying control needs — an 11-digit lid
  beginning with `1` whose 10-digit form nobody in the corpus holds. An arbitrary 11-digit lid is RED on
  the phone wall, so the control would have been discovered unplantable at build time.

**The decision this forces, and it is decided HERE rather than handed on.** Two arms were available:
(a) the inadmissible members live in the new test module's own temp vault, and WI-286's
reach-for-the-corpus-first rule yields to WI-016's privacy wall; or (b) this item declares a named
`s.whatsapp.net` exemption in that wall the way `RESERVED_ISBN` is declared
(`tests/fixture_vault.py:46-50`, "asserted by EQUALITY against a one-member literal so it cannot be
padded"). **Arm (a), and it is the plant list the class table's fourth column now states.** Arm (b) is
defensible on the merits — `s.whatsapp.net` is a protocol constant, not an identifying host — but it
widens ANOTHER item's privacy wall to admit a real domain, and (a) buys the same coverage while leaving
that wall alone. Rejected item 11 records (b) so nobody re-derives it. Note that AC-5's plants already
land in a materialized COPY of the corpus rather than in `tests/fixtures/vault/`, so they were never in
the wall's reach; what this leg forces is that they must not be promoted into the frozen corpus to
"save a plant", and that AC-1's boundary probes are test-module literals.

**Leg 3 — a plant has to pick an UNUSED member of a reserved block, not merely a reserved-looking one.**
Predicate, run for this fold: `rg -n '7700 ?900\d{3}|55501\d{2}'` over `tests/fixture_vault.py` and
`tests/fixtures/vault/` → the drama-block members already claimed are `447700900123` (Thrandell's
`phones`, `:224`, AND the pure-digit-name note `@+447700900123.md`, `:288-290`), `447700900456`
(`@Elowick Varnholt.md`'s phone, `:323`, and the resolution pool row at `:533`) and `447700900789`
(Thrandell's `whatsapp`, `:225`); NANP 555-01xx has no member in the corpus at all. The earlier class-A
exemplar `447700900123@s.whatsapp.net` reused Thrandell's own phone digits, so in any vault holding both
it would key `phone:447700900123` onto a second entity and mint an identifier conflict
(`_index_identifiers`, `person.py:336-366`) — and nothing in the battery pins the corpus's conflict set,
so it would not go red, it would just be wrong. The table's exemplars are now `447700900321` (class A),
`447700900654` (class E) and `15555550142` (class B), all unclaimed; class C keeps `447700900789`, which
travels with the value to its new note and stays unique.

**Leg 3, EXTENDED — the seventh plant had no digits of its own, which is the same trap one member
further along.** AC-5 requires one more note than the six-cell sweep does: a note carrying TWO JIDs, a
phone-bearing one and an `@lid`, which is the plant that proves a person keeps both identifiers across
the migration. Alone among that criterion's required members it pinned NO literal, and the values
printed two sentences earlier are the ones a test author reaches for — so building it out of
`447700900321@s.whatsapp.net` and `15555550142@lid` plants a SECOND entity in the same materialized copy
carrying the class-A plant's `phone:447700900321` and the representative's `jid:15555550142@lid`,
which is verbatim the mechanism above: `_index_identifiers` (`person.py:336-366`) does not raise on the
collision, so AC-5's own readback oracle — a `.key` multiset per note, the criterion whose entire point
is proving no identifier moved — would be computed against an ambiguous index for that note, silently.
Its pair is therefore pinned in AC-5 as `447700900987@s.whatsapp.net` (the phone-bearing half, class A)
and `15555550163@lid` (the `@lid` half, class B). Predicate, run for this fold over the whole tree:
`rg -n '900987|5550163|900321|5550142|900654'` → 31 hits, every one of them inside this document, and
zero anywhere under `tests/` or `obsidian_schemas/` — so both new runs are unclaimed, and so are the
three the previous fold minted. Both are reserved-block members by the wall's own patterns
(`tests/test_fixture_vault.py:308-312`): `447700900987` matches `^447700900\d{3}$` and `15555550163`
matches `^1?\d{3}55501\d{2}$`, and neither the corpus nor its manifest holds any 555-01xx member at all
(the tree's one other 555-01xx literal is `2125550147` at `tests/test_identity_endgame.py:274`, outside
the corpus and outside this item's vaults). The 10-digit counterpart `5555550163` is held by nobody,
exactly as AC-1's class-B control requires of `5555550142`. Eight literals are now pinned where the
first fold pinned three, and the discipline is the same one every other required member already got.

**F18 — THE MATRIX, RUN TO THE END: every plant literal and every fixture edit this document names,
against every wall that reads the frozen corpus, its manifest, or the package declarations those walls
derive from. F17 swept three of them; this sweeps the rest, states the results that found NOTHING as
well as the two that bit, and is what closes this class rather than its next member.** Six legs. Only
legs 1 and 2 change the document's instructions; legs 3–6 are stated because an unstated clean result
is indistinguishable from an unswept wall, and this is the fifth round in which the next unswept
contract supplied the finding. Predicate currency for all six: this worktree as the drive seeded it —
git HEAD `c93006a` plus the seeded uncommitted delta, read with Read/Grep/Glob and no shell.

**Leg 1 — `docs/vault-shape-census.md` is NOT touched by this item, and the instruction that said it
gains a row was wrong on both halves.** F6's cost sentence and its third amendment priced "a census row
per newly declared class, and its own digest follows" as a free build-side edit. Three facts, each read
this round:

- **The digest has no build-owned home.** `assert_census_is_frozen()` compares `sha256` over the
  census's bytes against `declared_census_digest()`, which reads the value out of the **`AC-3` `criteria`
  fence of `docs/vault-fixtures.md`** (`tests/test_fixture_vault.py:217-254`) — WI-016's criteria, signed
  2026-09-08, in a document that states "every remaining correction to a criterion's own text is now a
  D4b re-sign" (`docs/vault-fixtures.md:1389-1396`), with the value standing at `CENSUS_DIGEST =
  sha256:4cb7945f…` inside that fence (`:1418`). So "its own digest follows" names an edit that does not
  exist on this item's side, and the assertion runs in TWO places
  (`tests/test_fixture_vault.py:789` and `:1031`), so a census edit reddens the floor the moment it lands.
- **The row vocabulary is name-corruption classes, not field-value cells.** `census_class_rows`
  (`tests/test_fixture_vault.py:122-138`) reads `census-class` fences whose ids are either a `branch_id`
  derived from `TIER1_BRANCHES + COMPANY_TIER1_BRANCHES` — asserted in BOTH directions at `:830-838` —
  or one of the six hand-listed shape classes (`:842-848`, ids `diacritics` … `postal_address_in_name`).
  `count` is a LIVE-VAULT count, `specimen` is a name string, and there is no cell for "a `whatsapp`
  value that parses and is not storable".
- **And the MEASURED leg is an EQUALITY, so the row that matters is unsatisfiable anyway.** `{MEASURED
  row ids}` must equal `{union of NOTES[...].shape_classes}` (`:800-803`), and any note declaring a
  `shape_class` must also declare a `Verdict` (`:856-891`) from a three-member vocabulary every arm of
  which is evaluated against that note's **`name`**. A class-A row could never acquire a corpus specimen
  (F17 leg 2 makes class A inadmissible in the reach at all), and class Ø's 21 members are not corruption
  specimens and have no verdict to declare.

Why this was blocking rather than a build-time surprise: `docs/**` is builder-writable in full, so a
builder who follows the old cost line, sees two tests go red and reaches for the shortest green has two
self-consistent routes — amend WI-016's SIGNED AC-3 fence to re-freeze the digest, or write the new rows
as `status: ABSENT, count: 0` with a plausible command/stdout pair — and the second is verbatim the
false-ledger route that criterion's own `why:` says leg (iv) exists to close, over the artifact this repo
designates as the sole oracle for every live-vault claim its hermetic suite cannot re-derive. **The fold:
the census-row cost is deleted from F6, from its third amendment and from `### Effort` item (iv), and item
(iv) now states affirmatively that the file is untouched.** WI-032's six per-cell counts already have a
home — `docs/wi-032-whatsapp-corpus-census.md`, the precondition declared in `## Write Targets`, whose
`why:` asks for exactly "one row per cell of the SIX-cell class table". If a later reader decides this
item DOES owe a row in WI-016's census, that is a conductor pass plus a D4b re-sign of another item's
signed criterion and it goes in front of Dave — never into a cost line here.

**Leg 2 — the note that RECEIVES the class-C value is constrained, and the constraint was unstated.**
AC-1's WHERE clause said "any note whose `whatsapp` is currently `""` will do", subject only to the
phone-key uniqueness F17 leg 3 measured. Two more conditions, both read this round:

- **It must be a note that LOADS.** AC-1's class-C arm asserts `get_by_phone("447700900789")` returns
  that person, so the receiving note cannot be one of the three declared person skip specimens
  (`@Halvorne Sennaby.md`, `@Isolde Varnholt.md`, `@Ferrigan Ostrakine.md`, `tests/fixture_vault.py:490-494`)
  — on any of those the value would be planted onto a note nothing can load and the leg would be
  vacuous rather than red.
- **It must declare NO `shape_classes`/`verdict`.** The census verdict loop writes EVERY shape-class
  specimen's whole declared field set through the gated door and asserts `exc.pattern ==
  verdict.pattern` (`tests/test_fixture_vault.py:856-878`). A non-storable `whatsapp` on such a note
  makes the refusal that fires depend on where the new gate arm is placed relative to the name arm —
  today the name refusal is step 3 of `gate_write` and precedes every address arm
  (`name_gate.py:348-368`), so the assertion would still pass, but "passes because the new arm was
  placed second" is not a property to leave resting on a builder's choice of insertion point.
  A receiver with no verdict makes the question unaskable.

Both are satisfied with room to spare: `@Isolde Quenlaw.md`, `@Tessamund Ferrigan.md`,
`@Ravensby Ostrivane.md`, `@Skarnell Dalquest.md`, `@Pellworth Brenvik.md`, `@Wexlund Tarnquil.md`,
`@Kelmarra Marrowyn.md` and `@Fennwick Drostane.md` are plain loading person notes with no
`shape_classes`, no verdict, no identifiers and `whatsapp: ""` (`tests/fixture_vault.py:326-341`).
**`@Fennwick Drostane.md` is the recommended receiver** — named so the choice is not re-derived, and
carried into AC-1's WHERE clause as the constraint rather than as a preference.

**Leg 3 — the skip surface, the loadable counts and the resolution pool: CLEAN, and stated rather than
left unsaid.** `test_the_skip_surface_over_the_corpus_equals_its_declared_reasons`
(`tests/test_fixture_vault.py:923-977`) drives `SKIPS`, `LOADABLE` and `RESOLVABLE`. The tolerant reader
(F7) adds no skip for either stored shape, so `SKIPS` (`tests/fixture_vault.py:489-512`) is unchanged;
`LOADABLE`'s four counts (`:520-525`) are cache quantities unaffected by a field's value; and
`RESOLVABLE` (`:529-534`) carries queries for a name, an alias, an email and `+447700900456` — **no
`447700900789` query at all**, so relocating the class-C value changes no declared resolution answer.
Also clean and worth naming because it is the one a widening would break: leg (d) of the privacy wall
sweeps `spec.fields.get("phones", ())` only (`tests/test_fixture_vault.py:1151-1168`) and never reads
`whatsapp`, so the two manifest overrides do not enter it.

**Leg 4 — where the refusal `pattern` is DECLARED, which AC-3 required to be distinct and did not
require to be HOMED.** `_refuse` takes a plain `pattern_key: str` and admits no note-derived value
(`name_gate.py:142-174`), so a gate-local literal satisfies AC-3 for free. The gap is what AC-3 did not
forbid: a builder who declares the whatsapp refusal as a `NameValidator` Tier-1 branch record — because
that is where every other pattern lives — reddens WI-016's AC-3 floor immediately, since that floor is
DERIVED from `{record.branch_id for record in TIER1_BRANCHES + COMPANY_TIER1_BRANCHES}` and asserted in
both directions (`tests/test_fixture_vault.py:830-838`), and discharging it needs a live-vault count, a
scan command, verbatim stdout and a re-taken digest — a conductor pass, pre-priced by that criterion's
own `why:`. **Folded into AC-3 as one clause**: the pattern is a gate-local literal and this item
declares no new Tier-1 branch record.

**Leg 5 — the three set-equality walls the NEW TEST MODULE joins the moment it exists.** All three are in
one test (`tests/test_fixture_vault.py:1353-1442`) whose universe is
`python_files_under(PACKAGE_ROOT, TESTS_ROOT, SCRIPTS_ROOT)`, so a new file under `tests/` is inside it
by construction: (i) `ast` is asserted single-homed to `tests/derivations.py` (`:1383-1386`) — honoured by
design, since AC-3's and AC-5's derivations already route through that module; (ii) the legal homes for a
`SKIP_REASONS` string literal are pinned to exactly two files by EQUALITY (`:1392-1395`), so AC-4(a)'s
skip-surface assertions must IMPORT the reason from `obsidian_schemas/repositories/base.py` rather than
typing it — this is the one that bites; (iii) every top-level `def test_` must resolve uniquely through
`check_module`, a `def <name>(` substring scan over all of `tests/test_*.py` that raises on anything but
exactly one match (`tests/test_ac_interpreter.py:95-106`, exercised at
`tests/test_fixture_vault.py:1438-1442` and by this item's own five `check:` names), so the new module's
test names must be globally unique across the suite. Carried into the touch list rather than left for a
red.

**Leg 6 — the NEXT-LEVEL sweep over every OTHER literal the ACs name, with its result stated even where
it found nothing.** Predicate: each literal read against `reserved_email_violations`,
`reserved_url_violations`, `reserved_phone_violations`, `identity_tokens`/`NAME_POOL` and
`reach_files()` (`tests/test_fixture_vault.py:302-392`, `:1027-1133`).

- `notaphone@s.whatsapp.net` (class D) — email-shaped, host not reserved: RED in the reach, admissible
  as a test-module literal. Already stated (F17 leg 2); re-confirmed.
- `123@lid.example.com` (class E's minimal boundary probe) — email-shaped, host is a SUBDOMAIN of
  `example.com` which the frozenset matches by EQUALITY: RED in the reach, admissible as a test-module
  literal. It is a probe only and is never planted.
- `"n/a"`, `"ask Kate"`, `"   "`, `""`, `None`, YAML null, `[]` (class D and class Ø) — no email shape,
  no URL, no ≥9-digit run, no uppercase-initial run outside `NAME_POOL` (`Kate` is furniture in a
  quoted junk value, not an identity position, and it is a test-module literal in any case): clean
  everywhere, and this is the one row of the sweep that found nothing at all.
- `"+44 7739 341679"` — the Kim Faura value, and the only literal in the set that is a REAL identifier.
  It carries 12 digits and matches no reserved pattern, so it is RED anywhere in `reach_files()` and is
  admissible ONLY as a test-module literal, which is where AC-3 requires it. It introduces no new
  disclosure: it is already committed in this tree at `docs/write-door-bypasses.md:3994` and in this
  document, and WI-016's own module states the convention for literals outside the wall's reach —
  re-typing one already committed here adds no personal data, introducing a NEW real-looking identifier
  does not happen (`tests/test_fixture_vault.py:1212-1221`). **It must never be moved into
  `tests/fixtures/vault/` or `tests/fixture_vault.py`**, which is now said rather than assumed.
- `5555550142` (AC-1's class-B falsifying control) and `5555550163` (the two-JID lid's counterpart) —
  10-digit NANP 555-01xx members, reserved by pattern 3, held by nobody in the corpus: clean in the
  reach and clean as test-module literals.
- `447700900321`, `447700900654`, `447700900987`, `15555550142`, `15555550163` — the five runs this
  document mints: all reserved-block members, all unclaimed (F17 leg 3 extended, predicate re-run this
  round).
- `@s.whatsapp.net`, `@lid`, `lid.example` as bare domain literals — `@lid` and `@s.whatsapp.net`
  carry no dot-bearing local+host pair on their own so `EMAIL_SHAPED` does not fire on the fragment;
  the RULE that matters is the one F17 leg 2 already states about whole values, and no additional wall
  reads a bare suffix.

Nothing else in the criteria names a literal. The matrix is therefore complete over the walls that read
the corpus, the manifest and the declarations they derive from; the two members that bit are folded above
and neither touches Ruling A, B or C.

**F19 — THE REPORT HALF OF THE DESIGN WAS NEVER BUILT. This document promises in five places that a value
the door refuses is "reported and left", and the only mechanism any of them names is a function with ONE
call site that never reads `whatsapp` and whose live population WI-029 closed to zero five days ago. So
as specced the residual is left and NOT reported, and two of the three self-consistent builds ship
silent.** Two gates found this independently in the same round (architect round 6, AC red-team round 5),
in F9 — ORIGINAL text that predates every fold and that no round, either gate's included, had re-read
against the tool's call graph. Every fact below was read in code for this fold. Currency: this worktree as
the drive seeded it, git HEAD `c93006a` plus the seeded uncommitted delta, Read/Grep/Glob and no shell.

**Leg 1 — the mechanism. `_gate_refusal_pattern` is a MARKER helper inside one detector, not a detector.**
Defined at `scripts/lint_vault.py:334-352`; `rg -n '_gate_refusal_pattern' scripts/lint_vault.py` returns
exactly two lines, the `def` and one call at `:450`. That call sits in `check_structural`'s
`stem_name_divergence` arm, behind `vf.entity_type == "person"` (`:433`) AND `isinstance(stored, str) and
stored.strip() and stem != stored` (`:449`) — a filename/stored-name divergence, which has nothing to do
with this field. Its return value becomes a MARKER spliced into that ERROR's message (`:451-462`); it
emits no `LintIssue` of its own. `rg -n 'whatsapp' scripts/lint_vault.py` → 0 matches, re-run this round,
and none of the five check functions (`:355`, `:496`, `:577`, `:698`, `:798`) reads the field —
`field_type_mismatch` is about `auto_created` (`:464-465`).

**Leg 2 — and that one route is taken ZERO times on today's vault.**
`docs/stem-divergence-live-baseline.md:191` records WI-029's exit figure for the arm's own population:
divergent live person notes, **8 → 0**, conductor-performed 2026-09-26, five days after this item was
minted. So it is not a narrow report surface that happens to miss most notes; it is an empty one.

**Leg 3 — why this was blocking rather than a build-time surprise: three builds satisfy every `check:` in
the frozen criteria and only one keeps the promise.** AC-3's closing clause used to read "one consequence
pinned where it is FREE — `lint_vault` REPORTS such a note through `_gate_refusal_pattern` under that
distinct pattern", and `### Effort` priced `scripts/lint_vault.py` as "(pattern routing only)". No leg of
AC-1 through AC-5 asserted that a class-C/D/E note produces ANY lint output, so the clause was phrased as
already-true scenery rather than as a requirement — a clause with no `check:` attached to it at all,
riding on AC-3's write-door test.

- **Build A — a new report-only detector arm.** Correct, and the only one the Intent's "reported and left"
  survives. Not priced anywhere in the document as it stood.
- **Build B — widen the existing `stem_name_divergence` marker so a non-storable `whatsapp` turns it on.**
  Green on every criterion, and wrong twice: the marker's own text says "this divergence is not repaired by
  renaming the file to the stored name; repair the field" (`:451-454`), which is a false statement about a
  divergence whose actual defect is a FILENAME; and it would move live rows from UNMARKED to MARKED against
  a bracket that records "divergent rows the WRITE DOOR refuses (b3): 0 of 8"
  (`docs/stem-divergence-live-baseline.md:124`), flipping WI-029's own figure for the wrong reason.
  Rejected item 14.
- **Build C — read "pinned where it is free" as already-true and touch the tool not at all.** Green on
  every criterion, and the residual is silent. This is the reading the clause most invited.

**Leg 4 — the fold, and its cost is MEASURED rather than assumed, because this repo has already built
exactly this detector once.** Add ONE report-only arm to `check_structural`: fires on a stored `whatsapp`
that is NON-EMPTY and not STORABLE, `Severity.ERROR`, category `structural`, its own check name,
`auto_fixable` left at its `False` default (`scripts/lint_vault.py:96`). WI-029's own `stem_name_divergence`
is the precedent to copy literally (ERROR, `structural`, never auto-fixable, `:417-462`). Which walls it
joins, each read this round:

- **It owes NO repair oracle.** `tests/test_lint_vault_fix_rules.py:596-624`'s oracle-table equality is
  scoped to `auto_fixable_emitter_checks([LINT_VAULT_PATH])` (`:599`, `:621-624`), so a report-only rule
  is outside the derived set by construction and the WI-026 floor is satisfied without a fifth oracle.
- **It disturbs no set equality in the divergence module.** `_divergence_issues` filters on
  `issue.check == DIVERGENCE_CHECK` (`tests/test_stem_name_divergence_detector.py:283-289`), so a new
  check name is invisible to that module's four assertions — PROVIDED the report never travels as
  `NOT_RENAMEABLE_MARKER`, which is Build B's harm and is now an AC-3 conjunct.
- **`--fix` is untouched for the reason F9 should have given.** `apply_fixes` gates the DELTA
  (`whole_record=False`, `:1181`) and the five auto-fixable rules are `field_type_mismatch`,
  `person_missing_name`, `missing_body_sections`, `meeting_missing_from_timeline`, `broken_wikilink`
  (`tests/test_lint_vault_fix_rules.py:614-620`) — none of whose deltas contains `whatsapp` — so the
  refusal bucket never fires for this field from either direction.
- **It must judge BOTH stored shapes, for F2's reason one tool over.** The linter reads raw frontmatter
  (`vf.frontmatter`), and during the migration window a note carries a scalar `str` or a list, so an arm
  that only inspects lists is silent for exactly the population it exists for.

Folded: AC-3's closing clause becomes a REPORT LEG with four assertions and AC-3's `check:` is renamed for
both surfaces; `### Effort` carries `scripts/lint_vault.py` as a DETECTOR; F13 leg 3, Ruling B leg 2, AC-5
leg (e) and `### Examples of done` point at that leg instead of at F9. **`## Intent` is UNCHANGED**: its
"reported and left, never erased" is now true by construction rather than by citation, and the alternative
the architect named — deleting the word "reported" everywhere and letting the migration's own report be the
only discovery channel — is a promise being WITHDRAWN, which would be Dave's call and not a build's.
Rejected item 13 records it so it is withdrawn in writing if it is ever withdrawn at all.

**Leg 5 — one receiver constraint this finding adds to AC-1, and it is the same unread call site read from
the other end.** AC-1's WHERE clause admitted any non-representative person note that LOADS and declares
no `shape_classes`/`verdict`. Two notes satisfy all three and are still wrong receivers:
`@Perrowin Tessamund Drostane.md` and `@Yolvenna Brindlecote Skarnell.md` declare `shape_classes=()` and
no `verdict` — they carry a `discriminator` instead (`tests/fixture_vault.py:294-306`, re-read) — and they
are the corpus's two MARKER-BEARING stem-divergent notes, asserted by EQUALITY at
`tests/test_stem_name_divergence_detector.py:341-345` with their patterns pinned individually at
`:346-352`. A non-storable `whatsapp` on either makes the pattern `_gate_refusal_pattern` returns — and
therefore that marked-set equality — depend on where the new gate arm sits relative to the name arm,
which is the same question F18 leg 2 removed for census specimens. So the WHERE clause gains **"and is not
STEM-DIVERGENT"** as a constraint, not merely a named note: `@Fennwick Drostane.md` (the receiver) is not
divergent, but the CONSTRAINT is what a builder reasons from when the named note stops being available.
Stated as clean while here: all four divergent corpus notes carry `whatsapp: ""` via `_person`'s declared
defaults (`tests/fixture_vault.py:85-105`, `:94`), so they stay class Ø under the two corpus edits and that
marked-set equality is untouched by the edits themselves. (`@Quillam Ostrivane.md` and
`@Quillam Lumbrek.md`, whose `patterns[...] is None` is asserted at `:353-354`, were already excluded by
the `shape_classes` clause.)

**Leg 6 — a third in-tree reader of the representative's declared `whatsapp`, missing from the touch
list.** F17 leg 1 names `tests/test_writer.py:404-428` and `tests/test_fixture_vault.py:705-761`.
`tests/test_parser.py:248-264` (`test_corpus_person_note_parses_to_its_declared_values`) is a third: it
selects the person `roundtrip_representative` and compares `getattr(doc.entity, attribute)` against
`spec.fields` for every declared field (`:263-266`). It stays GREEN under the fold — the tolerant reader
gives `["15555550142@lid"]`, which is what `:225` will declare — but a builder who changes `:225` to a
scalar sees it red in a module `### Effort` does not mention. Carried into the touch list.

**Leg 7 — carried, not re-raised.** Rulings A, B and C are untouched: the refused population, the repair
door and the migration's repair pass are all unchanged, and only the REPORT half moves. This finding is
upstream of the census FREEZE and downstream of the rulings. Nothing here reopens a question for Dave; the
one thing that WOULD have — withdrawing the "reported" promise — is the branch this fold declines.

**F20 — `PersonRepository.save`'s DOCSTRING IS A FROZEN FIXTURE OF ANOTHER ITEM, and it is exactly where
this item's two disclosures have to land. The package file WI-032 edits most was priced as ordinary code;
its comment and docstring TEXT is a wall.** Two gates found this independently in the same round (architect
round 7, AC red-team round 6), against F11's and `### Examples of done`'s ORIGINAL text — the first two
folds closed the fixture-plant class and the third closed the report surface, and this is neither: it is a
PROSE fixture over the module those folds kept citing. Every fact below was read in code for this fold.
Currency: this worktree as the drive seeded it, git HEAD `c93006a` plus the seeded uncommitted delta,
Read/Grep/Glob and no shell.

**Leg 1 — the wall, and the one number the arriving fences got wrong.** `prose_lines`
(`tests/derivations.py:1773`) records EVERY comment line and EVERY docstring line of a file with its owning
definition's qualname (`ProseLine`, `:1644`). `tests/fixtures/identity_endgame/prose_surface_cut0.json` is
that surface over `person.py` recorded at Cut 0 and never re-recorded (`tests/test_identity_endgame.py:402`).
Clause **(e1)** of `test_strangler_prose_class_is_closed_in_the_package` (`:1008-1019`) then asserts on every
floor run that every Cut-0 `(owner, text)` pair whose owner is NOT in `AUTHORIZED_PROSE_OWNERS` is still
present in the final text — compared on `(owner, text)` and never on line numbers, so an APPEND is free and
an edit or a deletion of an existing line is not. `AUTHORIZED_PROSE_OWNERS` (`:359-373`) is thirteen members
(`<module>`, `__init__`, `_index_entity`, `_project_identifiers`, `_index_identifiers`,
`_remove_entity_from_indexes`, `get_by_phone`, `resolve`, `resolve_all`, `find_or_create_stub`, the deleted
legacy stub, `resolve_or_create`, `_resolve_identifier`) and **`PersonRepository.save` is not among them.**
Predicate, run for this fold: `rg -c '"owner": "PersonRepository\.save"'
tests/fixtures/identity_endgame/prose_surface_cut0.json` → **29** — not the 31 both arriving fences state,
which is the one figure of theirs this fold corrects and which changes nothing about the conclusion. The 29
records sit at `prose_surface_cut0.json:2400-2544`, carrying pre-cut line numbers 1215–1253, and their text
is byte-identical to today's `person.py:1158-1189` (the docstring) plus `:1195-1196` (the two trailing
comment lines). The wall is green now and goes red on an edit to any one of them.

**Leg 2 — three of those 29 lines are the frames this item's own findings point at.**

- `person.py:1174-1178` — "The write-back is the IDENTIFIER fields ONLY and never `name`", the paragraph
  that enumerates what the rider writes back (`entity.emails`/`phones`/`aliases`, `:1192-1194`). F11
  requires that write-back to grow `whatsapp`, so the enumeration becomes incomplete.
- `person.py:1180-1184` — the `phones[]` in-place-mutation disclosure, ending "Stated because it is one
  field wider than the consumer audit's grep list was written against." **F11 cited this exact range as the
  model for WI-032's disclosure**, and the natural way to honour "the same class of disclosure" is to extend
  that paragraph, which rewrites its lines.
- `person.py:1169-1172` — `whole_record=True`'s consequence, "both cross-field migrations run here exactly
  as they ran before". Under Ruling B leg 2 there is a third consequence — a REFUSAL — and this is the
  sentence that would state it.

A fourth line is frozen on this item's turf for the same reason one frame out: the class-body comment
explaining `_IDENTIFIER_PRIORITY`'s phone/whatsapp_jid tie is owned by the bare qualname
`PersonRepository` (`prose_surface_cut0.json:1680-1683` ≙ `person.py:774-775`), which is also not an
authorized owner — see F15's amendment, and it is the second reason that dict is left alone.

**Leg 3 — why this was blocking rather than a build-time surprise: three builds, all green on every
`check:` this document names, and two of them harmful.** No leg of AC-1 through AC-5 asserted anything about
`person.py`'s prose; AC-3's `save` arm asserts refusal BEHAVIOUR only, and it has no reason to test a
docstring.

- **Build A — APPEND ONLY.** Add each disclosure as a NEW paragraph and leave all 29 Cut-0 lines
  byte-identical. Correct, green and free, because (e1) is a PRESENCE test and not an equality over the
  whole surface. Nothing in the document said this was the constraint.
- **Build B — add `PersonRepository.save` to `AUTHORIZED_PROSE_OWNERS`.** This is the move (e1)'s own failure
  message invites ("either it is a member the plan missed … or revert it"), and it is worse than widening
  another item's wall: clause **(e2)** (`:1021-1030`) asserts that every AUTHORIZED owner has at least one
  Cut-0 line MISSING from the final text, so authorizing `save` is RED until one of its 29 lines is DELETED.
  Buying the green costs a mandatory prose deletion. Rejected item 15.
- **Build C — revert the prose.** Green on (e1) and on every criterion, and it ships a `save` whose docstring
  enumerates a write-back that has grown a field and explains a `whole_record=True` that has grown a refusal,
  silently withdrawing `### Examples of done`'s "and it says so" — the same defect SHAPE F19 closed one
  artifact over, arriving through a docstring instead of through a detector. Rejected item 16.

**Leg 4 — the fold, and it is a clause plus a touch-list line.** AC-3's `save` arm gains an APPEND-ONLY
clause; `## Approach` step (2) states it where it instructs the disclosure; `### Effort` states that
`person.py`'s prose surface is frozen for every owner outside WI-024's thirteen, that `save` and the bare
class `PersonRepository` are such owners, and carries `tests/test_identity_endgame.py` as a wall this item
JOINS rather than a file it edits — `AUTHORIZED_PROSE_OWNERS` and `prose_surface_cut0.json` untouched. This
is the WI-016 privacy-wall precedent applied to a third frozen artifact (arm (a): leave the other item's wall
alone, rejected item 11) and the same instruction F18 leg 1 gives for the census digest.

**Leg 5 — the rest of that suite, swept over every frame this item edits, with the CLEAN results stated so
an unswept wall is not mistaken for a clean one.** All in `tests/test_identity_endgame.py` unless noted.

- **The Cut-0 resolve golden — CLEAN, and it was the likeliest to bite.**
  `test_resolve_is_one_cascade_and_matches_the_pre_cut_golden` (`:672-729`) replays every golden query
  through `repo.resolve` over a roster-seeded vault and asserts no answer moved, with an exception list the
  item declares CLOSED. AC-1 changes what enters `_phone_index` and AC-2 inserts a cascade step, either of
  which could move an answer — but the roster carries no `whatsapp` at all: predicate, run for this fold,
  `rg -i -c 'whatsapp' tests/fixtures/identity_endgame/` → 6 hits, ALL of them inside
  `prose_surface_cut0.json` (recorded prose text), and none in `roster.json`. Every seeded note is class Ø,
  contributes no phone-index entry from this field and no `jid:` key, so the golden cannot move. Worth
  naming because the remedy a builder reaches for if it ever did — re-recording the golden — is the one
  thing that oracle declares fatal.
- **The wall-membership rows — CLEAN, conditionally.** `ITEM_EDITED_QUALNAMES` (`:1065-1080`) includes the
  four frames this item edits — `_index_entity`, `_project_identifiers`, `_remove_entity_from_indexes` and
  `resolve_all` — and the rows assert none of its members joins the falsy-return write universe
  (`:1139-1141`) and that `frontmatter_write_arms([person_path]) == []` (`:1156`). Both hold as long as this
  item adds no write capability and no frontmatter payload binding to `person.py`, which the design does
  not: the gate call and the writer delegation are already there. Named so it stays true rather than being
  discovered.
- **`resolve`'s no-index-reads clause — CLEAN, and it is the guard that would catch the wrong door.**
  `:692-698` asserts `PersonRepository.resolve` reads none of `_cache`, `_alias_index`, the email index or
  `_phone_index` directly. AC-2's new cascade step lands in `resolve_all` and the new public door is its own
  method, so the clause is untouched — but a builder who put `get_by_identifier`'s lookup INSIDE `resolve`
  reddens it, which is the right outcome and is worth knowing in advance.
- **`phone_index_iteration_sites` — CLEAN, with one constraint to carry.** `:642-644` asserts every
  phone-index iteration site in the package is classified `materialized`. `_index_entity`'s change is an
  insert, not an iteration, so nothing moves — but a builder who adds a loop over `self._phone_index` while
  making `_remove_entity_from_indexes` its exact inverse (AC-1) must wrap the iterable in one of
  `MATERIALIZING_WRAPPERS = {"list", "tuple", "sorted", "frozenset", "dict"}` (`tests/derivations.py:1620`,
  classified at `:1678-1684`). One line in the touch list.
- **The `ast` single-home equality — CLEAN, and now known to be asserted TWICE.** `:1134-1135` asserts it
  over package + tests, which is the same requirement F18 leg 5 carried from
  `tests/test_fixture_vault.py:1383-1386`. The new test module satisfies both by routing its derivations
  through `tests/derivations.py`. No new obligation.
- **`tests/test_phone_normalization.py:105-119` — CLEAN by Ruling A's recommended arm.** It pins
  `WhatsAppJID.parse` over `447990558521@s.whatsapp.net`, `12345@lid` and the raising
  `12345@s.whatsapp.net` — the `MIN_DIGITS` boundary. The recommended arm leaves `parse` untouched, so the
  module needs no edit; it is named because it is the module that goes red if Ruling A's alternative (b) is
  ever taken, and rejected item 7's cost line ("four call sites plus two test premises") does not count it.

**Leg 6 — carried, not re-raised.** Rulings A, B and C are untouched: the refused population, the repair
door, the migration's repair pass and the report arm are all unchanged, and what moves is only where a
disclosure's TEXT may be written. This finding is upstream of the census FREEZE and downstream of the
rulings, and it reopens no question for Dave.

**F21 — THE MIGRATION'S TERMINAL STATE WAS PROMISED AS A NUMBER THE DESIGN FORBIDS. AC-3 refuses a
class-D/E value in BOTH shapes and AC-5 leg (b) routes every migration write through that gate, so those
notes are TERMINALLY SCALAR — and three places promised "zero notes left in the scalar shape" alongside
"the D+E residual reported and byte-identical". AC-5's own mandated plants collide the two conjuncts, so
no build passed the criterion as written.** Two gates found this independently in the same round (architect
round 8, AC red-team round 7), both reaching it from the criteria text alone rather than from another
module — which is why it is `basis: original` and why the three closed artifact classes (fixture plants
F17/F18, the report surface F19, the prose surface F20) could not have surfaced it: it is not a fourth
artifact whose contract nobody read, it is a contradiction between two conjuncts this document has carried
since its first draft, made visible by asking what the vault looks like after a SUCCESSFUL run. F14 asked
the mirror question (what does a back-out look like) and answered it correctly; nobody asked this one.
Currency: this worktree as the drive seeded it, git HEAD `8b9b95e` plus the seeded uncommitted delta,
Read/Grep/Glob and no shell.

**Leg 1 — the mechanism, in four facts and one step.**

- A shape conversion is a write that INTRODUCES `whatsapp`. For a class-D note the payload is
  `{"whatsapp": ["n/a"]}` — the list shape with one non-storable member, which is verbatim one of the two
  shapes AC-3 names per arm ("a list containing one bad member among good ones") and refuses with **nothing
  written**.
- No arm escapes it. AC-5 leg (b) asserts STRUCTURALLY that every migration write goes through `vault_io`
  *and through the gate*, with no direct `write_text`, so there is no carve-out the migration could use.
- The delta rule does not help either, and this is the fact that closes the last route. `name_gate.py:31-36`
  keeps a stored-dirty note writable only for writes that do NOT re-introduce the field ("A stored-dirty
  note stays writable for every write that does not re-introduce its name", read this round) — and
  re-introducing the field is the ENTIRE CONTENT of a shape conversion.
- So the migration leaves every class-D and class-E note in the scalar shape, NECESSARILY. That is not a
  build choice; it is forced by AC-3 plus AC-5 leg (b), and this document already said as much in two
  places while promising the opposite in three: class E is "left byte-identical by the migration like D"
  (the class table's discussion) and AC-5 leg (e) asserts "its note's `whatsapp` bytes are asserted
  byte-identical".

**Leg 2 — and the collision is inside the hermetic suite by MANDATE, not only on the live vault.** AC-5's
`desc` requires a plant per NON-Ø cell — "A, B, C, D and E" — and leg (d) requires a planted class-E note
asserted byte-identical after a repair-ENABLED run. So the class-D and class-E plants are scalar when the
run ends, and the old leg (e)'s zero-scalar conjunct was RED on the suite this same criterion mandates,
regardless of what the live census reports. The live population is separately non-guaranteed-zero: the
census precondition treats every class's count as open and unmeasured, expecting zero only for E.

**Leg 3 — why this was blocking rather than a build-time surprise: all four routes out are red, which is
worse than buildable-two-ways.** Enumerated because the sweep is what shows the criterion UNSATISFIABLE
rather than merely ambiguous.

- **(a) Let the gate accept class D/E for the conversion.** Red on AC-3, and it retires the item's own
  refusal — i.e. it retires the item.
- **(b) Bypass the gate for the conversion.** Red on AC-5 leg (b), which asserts the route structurally
  rather than by observing the result.
- **(c) CLEAR the D/E values so the notes convert as class Ø.** The ONE route that reaches a flat
  zero-scalar vault, and it is silent data loss on exactly the population the item exists to preserve —
  rejected item 8's harm arriving through the migration instead of through the reader. It is caught today
  only by AC-5 leg (c)'s TOTAL-value count per note (1 → 0), a guard added in the first red-team round for a
  different reason: so that leg (c)'s parseable-only scoping could not become a licence to delete what it
  excludes. That guard is load-bearing and, on this reading, was the only thing standing between this
  criterion's own contradiction and erasure — which is why the fold adds the never-clears conjunct and makes
  the route red BY INTENT. Rejected item 17.
- **(d) Honour byte-identity and report the residual.** The CORRECT build — and red on the old leg (e)'s
  zero-scalar conjunct.

So the build-runner's real exits were to amend a FROZEN criterion (a D4b re-sign after Dave's signature,
the exact cost this document refuses to defer everywhere else) or to reinterpret "zero notes left in the
scalar shape" as "zero of the notes the write COMMITS" — the charitable reading, which is correct and which
NOTHING in the text licenses. That second exit is the same defect SHAPE F19 closed one artifact over: a
clause satisfied by a reader's generosity rather than by construction, riding on a neighbouring assertion.
It is worse here, because the clause is also an EXIT NUMBER: `## Approach` step (4) commits it to the live
bracket and `### Examples of done` promises it to Dave, so a conductor performing the bracket against a
non-zero class-D census row could not produce the figure the item ships against and would be left
adjudicating it in prose — the one thing the entry/exit discipline exists to prevent. And if the live
population happened to be zero the figure would work by LUCK, which is the "stays green while unclassified"
shape this document refuses everywhere else (it is the stated reason class E is asserted rather than
assumed).

**Leg 4 — it also corrects a claim about Ruling B, which is why it is not purely editorial.** AC-5 leg (d)'s
closing clause said a run invoked with repair disabled "leaves class C untouched and reports it (Ruling B's
alternative arm, so the criterion holds either way Dave rules)". It did not hold either way. Under the
alternative arm class C is ALSO unstorable at the gate, so class C joins the terminally-scalar residual:
`|R|` grows by the census's class-C row — the row this document itself calls the load-bearing one — and N
notes end the migration BOTH scalar AND unsaveable through the whole-record arms. Dave is entitled to that
number when he rules on the repair, and the document was telling him the criterion was indifferent to his
answer. Ruling B is not REOPENED by this — what the migration does to class C under each arm is unchanged —
but its cost line now states the consequence.

**Leg 5 — the fold, and it is one partition stated once and restated in four places plus two conjuncts.**
`## Exploration Notes` gains **THE TERMINAL-STATE PARTITION** (three parts: scalar-outside-R = 0, migrated,
R; R's membership per Ruling B's arm; `|R|` equal to the census's corresponding rows), the never-clears
conjunct and the triple-reconciliation identity. AC-5 leg (e) is rewritten to the partition, leg (d)'s
arm-agnostic sentence is corrected and asserted over BOTH arms, `## Approach` step (4)'s exit numbers and the
live bracket's exit row become the partition's three counts, and `### Examples of done` says the same thing in
plain terms. AC-4 leg (c)'s "after any gated write the bytes carry the LIST form" is scoped in the same move,
because it is the same absolute one criterion over: on a residual note no succeeding introducing write exists,
so the leg is silent about it rather than violated by it. The partition is still an ORACLE and still
falsifiable — `|R|` is taken twice by different tools, once off the run's own counts and once off the
`lint_vault` detector AC-3's REPORT LEG builds, and they must agree, which is the independent second witness
that report arm was built to buy.

**Leg 6 — the class, and the sweep that closes it.** The generator is an ABSOLUTE promise — "zero", "every",
"all", "never" — stated over a population that ANOTHER criterion carves a residual out of. The sweep is
declared in `## Exploration Notes` as a table naming, for every absolute in the five AC descs, `## Intent`,
`## Approach` and `### Examples of done`, the population it ranges over and the residual it excludes. Result:
one unsatisfiable absolute (the zero-scalar exit number, in three places), two that were true but silent
about their scope (AC-4 leg (c) and two `### Examples of done` clauses, all scoped without changing what any
build does), and the rest total over their stated population with no residual — stated as clean so an
unswept absolute is not mistaken for a swept one.

**Leg 7 — carried, not re-raised.** Rulings A, B and C are Dave's and untouched: nothing about what the
migration DOES to any cell moves. What moves is what this document CLAIMS the vault looks like when the run
has finished, plus the corrected cost line on Ruling B's alternative arm. This finding is upstream of the
census FREEZE and downstream of the rulings, and it reopens no question for Dave.

### Rejected — and why (so nobody re-explores these)

1. **A pydantic validator on `Person.whatsapp` as the enforcement point.** Rejected by F1: it cannot
   see the three dict-shaped doors, which is exactly the class the Kim Faura value arrived through. It
   would be a fourth spelling of "well-formed" that three doors bypass.
2. **A `_whatsapp_index` per-kind dict.** Rejected: WI-023 spent a whole item DELETING the legacy
   per-kind email dict so email resolution has ONE authority (`CLAUDE.md`, the WI-125 identifier
   index). The lid is already in that index under `jid:<lid>`; the gap is a public reader, not a
   second index.
3. **Contract before migrate — refuse the scalar at parse time.** Rejected by F7 as amended by F14:
   the vault is shared mutable state, so there is no window in which the library holds a new shape
   privately (a version pin does not create one), and `SchemaDriftError` converts an un-migrated note
   into a skipped note — invisible, not merely odd.
4. **Teaching `normalize_phone` about `@lid`.** Rejected: it is a stdlib-only leaf whose two consumers
   both WANT the naive split (`phone_normalization.py:11-27`), and the frame that must stop treating a
   lid's digits as a phone is `_index_entity`, which already has the typed answer available
   (`WhatsAppJID.parse(v).phone_digits`). Fix the caller, not the leaf.
5. **Provenance (`source`/`observed_at`/`corroboration`) on the note.** Out by Dave's 2026-09-26 ruling
   (2) — the writer keeps its own ledger, keyed by value. Nothing to build here; named so a later
   reader does not re-derive it as a gap.
6. **A one-off migration script.** Out by Dave's ruling (4) and by this repo's own discipline: dry run
   reporting counts, the write through `vault_io`, then a readback count.
7. **Narrowing `WhatsAppJID.parse` itself so there is literally one predicate.** Rejected by F12's
   measured blast radius, not by taste: `parse_identifiers` is `strict=True` by default and is the
   declared Phase-4 adapter seed, so a bare number from a phone-only channel would start RAISING; the
   WI-035 pivot (`person.py:832`) and `_resolve_identifier` (`person.py:902`) both want maximum reach
   because their job is to FIND a person; and `tests/test_identity_index.py:80` would keep passing
   while silently ceasing to test its own name. Named here rather than settled — it is Ruling A's
   losing arm, and if Dave picks it anyway the cost is the four sites above plus two test premises,
   which is affordable, just larger.
8. **Dropping a stored value the door refuses, at read time, so the model can hold a clean typed
   list.** Rejected by F13 leg 1: `model_to_frontmatter` emits every declared field unconditionally
   and `save` judges the whole record, so a dropped value is ERASED from the note by the next save.
   Named explicitly because it is the branch a build reaches by default — annotate the field
   `list[WhatsAppJID]`, parse leniently, skip what fails — and it is silent data loss on the exact
   population the item was minted for.
9. **A `writer.py` projection step for identifier values.** Was in scope as F8's remedy; DELETED by
   F13 leg 1. With the stored field `List[str]` nothing dataclass-shaped is ever in `model_fields`, so
   there is no projection to write. The `no !!python/object in the bytes` assertion stays (AC-4 leg b)
   as the guard that keeps it true.
10. **"The field is either absent or a valid JID" — i.e. refusing every value `WhatsAppJID.parse`
    refuses, blank included.** This is the shape the drafted ACs read as having, and it is the reason
    class Ø now exists: rejected by F16, and rejected on cost rather than on taste. It refuses the model's
    own default (`models.py:94`), the person template's value, 21 of the 22 `whatsapp`-carrying fixture
    notes, and — the fatal one — the only spelling this package has for CLEARING a field, since the writer
    has no delete affordance (`writer.py:333-337`). So it makes the hand repair of the D+E residual
    unbuildable while the design simultaneously promises it, and it does so INVISIBLY: the entity path
    never hands the gate a literal `""`, so the whole drafted suite is green on it. Named here because it
    is the branch a build reaches by DEFAULT — the parser already raises on blank, so "refuse what the
    parser refuses" is the shortest correct-looking implementation — and because two independent gates
    reached it from the frozen text, which is as strong a signal as this pipeline produces that a third
    reader would too.
11. **Declaring an `s.whatsapp.net` exemption in WI-016's privacy wall so class A can be planted in the
    frozen corpus.** Rejected by F17 leg 2, and on cost rather than on merit: the merit is real —
    `s.whatsapp.net` is a WhatsApp protocol constant carrying no identifying host, which is the same
    argument `RESERVED_ISBN` already won (`tests/fixture_vault.py:46-50`, exempted by EQUALITY against a
    one-member literal so it cannot be padded). But it widens ANOTHER item's wall to admit a real
    domain, and the alternative buys identical coverage for nothing: class A, class D's
    `@s.whatsapp.net` member and class E live in the new test module's own temp vault, which is outside
    `reach_files()` (`tests/test_fixture_vault.py:386-392`) and outside the digest. Named here because
    it is the move a builder reaches for on discovering the wall mid-build, and because doing it
    silently would widen a privacy wall as a side effect of a fixture convenience.
12. **Keeping the class-C member on `@Thrandell Ibberly.md` and re-expecting the refusal in the two
    round-trip tests.** Rejected by F17 leg 1. It is the self-consistent build — every AC in this set
    goes green — and it deletes the repo's only assertion that a whole person field set survives the
    write door (`tests/test_writer.py:404-428`, `tests/test_fixture_vault.py:705-761`) in exchange for
    nothing this item asked for. Named explicitly because it is what a builder does when the battery
    goes red and the AC text told them the member was free.
13. **Withdrawing the report promise instead of building the report surface — i.e. deleting the word
    "reported" from `## Intent`, F13 leg 3, Ruling B leg 2, AC-5 leg (e) and `### Examples of done`, and
    letting the migration's own run report be the only channel by which a D+E value is ever discovered.**
    Rejected by F19 leg 4, and rejected on ownership rather than on cost: it is cheaper than the detector
    (zero code), and it is defensible on the merits, because the migration DOES print per-cell counts and
    a one-off discovery is better than none. But it is a promise being WITHDRAWN from five places at once,
    and the thing withdrawn is the difference between "somebody notices this note before the next hand
    repair" and "nobody notices until someone trips over it" — which is Dave's call, not a build's and not
    this document's. Named here so that if it is ever taken it is taken in writing, at the signature, with
    the five sentences edited in the same move; the detector is one report-only arm in a tool this repo has
    already built the identical arm for once (WI-029), so the price of keeping the promise is small enough
    that withdrawing it should have to be argued.
14. **Widening `stem_name_divergence`'s existing `NOT_RENAMEABLE_MARKER` so a non-storable `whatsapp`
    turns it on, rather than emitting a new check.** Rejected by F19 leg 3 as Build B. It is the build a
    builder reaches for by following the old AC-3 clause's citation literally, and it is green on every
    criterion in this set. Two harms: the marker's own message says "this divergence is not repaired by
    renaming the file to the stored name; repair the field" (`scripts/lint_vault.py:451-454`), which
    becomes a false statement about a note whose actual defect is its FILENAME; and because the arm is
    gated on `stem != stored`, widening the marker moves live rows from UNMARKED to MARKED against
    WI-029's own committed figure, "divergent rows the WRITE DOOR refuses (b3): 0 of 8"
    (`docs/stem-divergence-live-baseline.md:124`) — flipping another item's bracket for a reason that has
    nothing to do with what that bracket measures. A new check name is free of both
    (`tests/test_stem_name_divergence_detector.py:283-289` filters on the check).
15. **Adding `PersonRepository.save` to WI-024's `AUTHORIZED_PROSE_OWNERS` so this item's disclosures can be
    written into its existing docstring paragraphs.** Rejected by F20 leg 3 as Build B, and rejected on cost
    rather than on merit — the merit is arguable, since this item genuinely does change what that docstring
    describes. But it is the move clause (e1)'s own failure message invites, and it is strictly worse than
    the widen-another-item's-wall move rejected item 11 already refused for the privacy wall: clause (e2)
    (`tests/test_identity_endgame.py:1021-1030`) asserts that every AUTHORIZED owner has at least one Cut-0
    line MISSING from the final text, so authorizing `save` is RED until one of its 29 recorded lines is
    DELETED. The fix for one wall assertion would be a mandatory prose deletion — buying a green by
    destroying the disclosure surface this item is trying to extend. Build A (append a new paragraph, leave
    all 29 lines byte-identical) buys the identical coverage for nothing.
16. **Reverting the prose instead — leaving `save`'s docstring exactly as Cut 0 recorded it and shipping the
    behaviour change undisclosed.** Rejected by F20 leg 3 as Build C. It is green on clause (e1), green on
    every criterion in this set, and free — and it ships a `save` whose docstring enumerates a write-back
    that has grown a field (`person.py:1174-1178`) and explains a `whole_record=True` that has grown a
    REFUSAL (`:1169-1172`), while `### Examples of done` promises of the new refusal surface that "it says
    so". That is the same defect shape as rejected item 13 one artifact over — a promise withdrawn by
    silence rather than in writing — and it is why the APPEND-ONLY clause is stated in AC-3 rather than left
    as a build note: both wrong builds are individually self-consistent and neither reddens anything this
    document names.
17. **CLEARING a class-D or class-E value during the migration so the note converts as class Ø, thereby
    reaching a flat "zero notes left in the scalar shape".** Rejected by F21 leg 3 as route (c). It is the
    ONLY build that reaches the absolute the document used to promise, which is precisely what made the
    promise dangerous: a builder who takes "zero notes left in the scalar shape" at its word and finds the
    gate refusing the conversion has exactly one route to green, and it is silent erasure of the population
    this item exists to preserve — rejected item 8's harm arriving through the migration instead of through
    the reader. It is red today only via AC-5 leg (c)'s TOTAL-value count (1 → 0), a guard added in the first
    red-team round for an unrelated reason, so it was red by accident rather than by intent. The fold makes
    it red on purpose: leg (e) now asserts the run NEVER clears a value to make a note convert, and the exit
    figure it was buying no longer exists. Clearing stays the residual's repair door — asked for by a person
    through a delta arm (AC-3's CLEARING leg), never decided by the run.

### OPEN RULINGS for Dave — three. The first two are new this round and both touch his 2026-09-26 rulings

Each states the question, the recommendation, and what it costs to go the other way. All three are
cheap NOW and cost a D4b re-sign after the signature.

#### Ruling A — does a STORABLE predicate exist, or is a bare phone number an acceptable `whatsapp:` value?

The fact that forces this: `WhatsAppJID.parse("+44 7739 341679")` SUCCEEDS (F12). So a door wired to
the parser refuses only digit-less junk, and the Kim Faura value — the one that caused this item —
still writes cleanly. Dave's ruling (1) says the field's type IS `WhatsAppJID`, "both forms; no second
spelling of 'well-formed' anywhere" — and his own description of those forms (`<digits>@s.whatsapp.net`
and `<digits>@lid`) is the STORABLE predicate, narrower than the code. The ruling and the code disagree
on a fact; that is why it is here.

- **Recommended: two predicates on one type (F12).** `parse` unchanged for reach; one derived
  `is_storable`/`jid_domain` on the same dataclass, in the same module, read only by the write door.
  One authority, no consumer re-implementing anything, zero blast radius on resolution. Closes the
  minted defect.
- **Alternative (a): keep the wide definition.** Then `whatsapp:` accepts bare phone numbers, and the
  honest statement to Dave is that the motivating defect is RETIRED rather than fixed — the item ships
  cardinality, resolution and the migration, and "a malformed JID never reaches a note" becomes "an
  unparseable value never reaches a note". `## Intent` sentence 1 and Example 2 change; AC-3's refused
  population collapses from C+D+E to D alone (class E's non-storability is the only thing distinguishing
  it from B, so the cell folds into B as well); the census's class-C row becomes informational. Class Ø
  survives this arm untouched and still must not be refused — under it the refused population is the
  NON-EMPTY unparseables, which is exactly why F16's carve-out is upstream of Ruling A rather than
  contingent on it: whichever arm Dave picks, the door must not refuse the model's own default.
- **Alternative (b): narrow `parse`.** Rejected item 7 prices it: four call sites plus two test
  premises, and resolution loses reach it currently has by design.

This is upstream of the census as well as of the ACs — until it is settled, the census cannot know
whether to count class C as a defect population or as normal data.

#### Ruling B — what does the model hold for a value the door would refuse, and does the migration repair it?

**RULED — Dave, 2026-09-27 (in-session, one word: "repair").** The recommended arm, all three parts: `List[str]` stored with a derived typed accessor; `save` refuses a stored unstorable value and never erases it, clearing stays legal everywhere, the residual is reported by the new `lint_vault` detector; the migration REPAIRS class C key-preservingly. The ACs below already stand on this arm — no text changes. Landed by the conductor at the grounding door (the drive was live when the word was given).

The fact that forces this: `save` gates a WHOLE-RECORD PROJECTION and `model_to_frontmatter`
re-introduces `whatsapp` on every save (F13; the second such arm is `write_markdown_file(entity=…)`, per
F11's correction — the handle is the projection, not the `whole_record` flag). So the two candidate builds
ship opposite harms — silent erasure, or a class of unsaveable notes — and neither is a thing to find out
from a build.

- **Recommended, three parts.** (1) The stored field is `List[str]` with a DERIVED typed accessor, not
  `list[WhatsAppJID]` — the only shape that cannot erase, and WI-033's own precedent from the same
  week. This amends the letter of ruling (2) while serving its intent (cardinality + typed access)
  whole. (2) `save()` REFUSES on a stored unstorable value and never erases it — the `name` precedent —
  while CLEARING the field stays legal at every door, which is what makes the residual repairable by hand
  and is a correction to this leg rather than an addition to it (F16; two gates found the earlier text
  refusing the empty value); **and the residual is REPORTED, by a new report-only `lint_vault` detector
  arm this item builds (AC-3's REPORT LEG)** — stated here rather than assumed, because the surface this
  leg used to lean on does not exist: `_gate_refusal_pattern` has one call site, gated on a
  filename/stored-name divergence whose live population WI-029 closed to zero, and it emits no issue of
  its own (F19, which retracts F9). Declining the detector is a real option and it is rejected item 13 —
  but it is the word "reported" being withdrawn from this leg, so it is a ruling and not a build choice.
  (3) The migration REPAIRS class C key-preservingly
  (`"+44 7739 341679"` → `"447739341679@s.whatsapp.net"`,
  same `phone:` key) and repairs ONLY phone-bearing values, which is what reduces the refusal population
  to class D plus class E — non-empty digit-less junk plus (expected zero) `@lid`-substring values with a
  non-JID domain — and keeps (2) affordable.
- **What going the other way costs.** Keeping a literal `list[WhatsAppJID]` annotation means either
  erasure (unacceptable) or a union type the YAML writer then has to special-case — F8's hazard back
  from the dead. Declining part (3) is defensible: it means the migration only REPORTS class C and N
  notes stay unsaveable until hand repair, where N is the census's class-C count. That is a
  do-I-want-my-values-rewritten question, so it is Dave's. **One number was missing from that cost line
  until this round and it is stated now rather than discovered at the bracket (F21 leg 4):** those same N
  notes also stay in the SCALAR shape, because a shape conversion re-introduces the field and the door
  refuses a class-C value in both shapes — so declining part (3) moves class C into the migration's residual
  R, `|R|` becomes the census's class-C plus class-D plus class-E rows, and the exit figure the live bracket
  reports changes with the ruling. AC-5 leg (d) now states that instead of claiming the criterion holds
  "either way" unchanged, and asserts both arms.

#### Ruling C — scope (unchanged from the previous round)

**RULED — Dave, 2026-09-27 (in-session: "whatsapp only").** WI-032 ships the `whatsapp` axis whole and nothing else; the `emails`/`phones`/`linkedin` element-typing is minted as its own item, framed as derived typed accessors alongside the stored `List[str]`, per the recommendation below. The ACs below already stand on this scope — no text changes. Landed by the conductor at the grounding door.

Dave's ruling (2) says the other identifier fields become typed lists too. Two axes hide inside that
one sentence and they cost very different amounts:

- **Cardinality (scalar → list).** Only `whatsapp`, `linkedin` and `slack` are scalars today
  (`models.py:94-98`); `emails` and `phones` are ALREADY `List[str]`. The measured pressure for
  cardinality is the ~51 people holding both a phone-JID and an `@lid` — a `whatsapp` fact.
- **Element type (`str` → `Identifier`).** This is the estate rule, and it is where the blast radius
  is: `emails[]`/`phones[]` are read as strings by the gate's own splitter and dedupe
  (`name_gate.py:374-404`), by the save rider (`person.py:1192-1194`), by `lint_vault`, by
  `README.md:52` and `:238`, and by both consumer repos' `ContactInfo` mirrors.
- **`slack` cannot be typed in this item at all.** `SlackUserId.parse` requires a workspace the
  frontmatter does not carry, which `_project_identifiers` records as an explicit UNBLOCK over a
  2-note population (`person.py:305-312`). Typing it means inventing the missing half.
- **Strict element types fight the repair tool.** A strictly-typed stored field makes a note carrying a
  malformed value unloadable (F7's `SchemaDriftError` route), and `lint_vault` — the thing whose job is
  to find and repair malformed values — cannot report a note it cannot load. That argument does not
  bite `whatsapp` (its refusal lives at the write door per F1/F3, and the reader stays tolerant per
  F7), but it bites any future strict typing of `emails[]`.

**Recommendation:** WI-032 ships the `whatsapp` axis whole — cardinality, the gate arm, the resolution
door, the migration — and the `emails`/`phones`/`linkedin` element-typing is minted as its own item,
gated on this one's migration discipline having been proven once. The ACs below are drafted to that
scope. If Dave wants the wider shape in one item, the AC frame widens BEFORE it is frozen; after the
signature the same widening costs a D4b re-sign.

**One update from Ruling B.** The element-typing axis just got cheaper to defer and harder to do: F13
shows that a strictly-typed stored field cannot hold a value the door refuses without either erasing it
or making the note unsaveable. That is the same argument as the fourth bullet above (strict element
types fight `lint_vault`), now with a second mechanism behind it. So the follow-on item is not "annotate
`emails: list[Email]`" — it is "add derived typed accessors alongside the stored `List[str]`", which is
what this item does for `whatsapp` and what WI-033 does for timeline entries. Worth saying out loud so
the follow-on mint does not inherit the annotation framing. **And the mint happens WHEN Dave rules, in the
same move** (round-2 note 6): a deferral that is only recommended evaporates into a queue nobody re-reads,
and this one now carries a specific framing worth preserving. A third input the follow-on inherits: the
class-Ø rule generalizes — `emails`/`phones` already draw it by falsiness at `name_gate.py:399`, so
whatever typed accessors that item adds, absence stays absence and is never a refusal.

### Effort, dependencies, blast radius

- **Effort:** one build plus a conductor-run live migration bracketed entry/exit, the shape WI-029 used
  (`docs/stem-divergence-live-baseline.md`). The library change is small; the migration is the item. That
  bracketed run is stated as the item's SHIP CONDITION in `## Approach` step (4), not merely as effort
  (round-2 note 4, carried through round 3) — a migration whose only acceptance is the corpus it was
  written against is a specimen in a jar.
- **Un-parks WI-010.** `docs/migration-support.md:20-22` states its un-park criterion as "the first
  real schema migration that must walk the vault" — this is that migration. Whether WI-010 then
  un-parks as a generic `schema_version` mechanism or is closed as answered is a queue question.
- **Downstream:** HAL9000 WI-075 depends on this and it gates orchestrator WI-192/193 (per the premise
  paragraph; out-of-tree, not re-verified from inside the cage — that is the consumer-audit
  precondition's job).
- **Expected touch list for the spec-writer** (revised this round): `identifier.py` (the STORABLE
  property and its domain set — Ruling A), `models.py` (`whatsapp: List[str]` plus the derived typed
  accessor — Ruling B), `name_gate.py` (the arm, plus its refusal `pattern` as a GATE-LOCAL literal —
  `_refuse` takes a plain `pattern_key: str` (`:142-174`), and declaring the pattern as a `NameValidator`
  Tier-1 branch record instead would redden WI-016's derived AC-3 branch floor and cost a conductor pass,
  F18 leg 4), `repositories/person.py` (`_index_entity`,
  `_remove_entity_from_indexes`, `_project_identifiers`, `resolve_all` + `_RESOLVE_CASCADE_ORDER` at
  `:145`, the public `get_by_identifier`, the `save` rider — **and in `_project_identifiers`, ITERATE the
  list and never hand the list itself to `parse`**, which is the one frame of the three where the
  cardinality flip turns a LOUD failure into a SILENT wrong answer and is worth one clause here because the
  diagnosis costs more (architect round-8 note 1): `_index_entity` (`:266-270`) and
  `_remove_entity_from_indexes` (`:412-416`) both call `normalize_phone(entity.whatsapp)`, which does
  `phone.split("@")` (`phone_normalization.py:52`) and so raises `AttributeError` on a list — fine, it fails
  loudly — while `_project_identifiers` guards with `if entity.whatsapp:` and makes ONE
  `add(WhatsAppJID.parse, entity.whatsapp)` call (`:330-331`) whose blank guard tests `isinstance(raw, str)`
  (`:319`, a list passes it) and whose `parse` does `s = str(raw).strip().lower()` (`identifier.py:273`), so
  `parse(["447700900321@s.whatsapp.net"])` SUCCEEDS with `phone_digits == "447700900321"` — `normalize_phone`
  splits at the FIRST `@` and strips non-digits, recovering the same digits out of the list's repr. A build
  that forgets the loop therefore produces the CORRECT `phone:` key for a single phone-bearing value and
  passes AC-1's and AC-2's class-A legs; what catches it is the `jid:`-keyed cells (B and E key
  `jid:['15555550142@lid']`) and AC-5's two-JID note (one identifier where two are asserted). The suite does
  go red, which is why this is a touch-list clause and not a criterion), **`scripts/lint_vault.py` — a NEW REPORT-ONLY
  DETECTOR ARM in `check_structural`, plus a test module of its own for it, NOT "pattern routing only"
  (F19: `_gate_refusal_pattern` has one call site, behind `stem_name_divergence`'s `stem != stored` guard
  at `:449-450`, and emits no issue; the arm copies WI-029's own detector shape at `:417-462` — ERROR,
  `structural`, `auto_fixable` at its `False` default — and because it is report-only it owes no repair
  oracle in `tests/test_lint_vault_fix_rules.py:596-624`, whose table is scoped to
  `auto_fixable_emitter_checks`)**, `README.md:52` and `:238`, `tests/test_identity_index.py` (its `_note` helper writes
  `whatsapp:` as a scalar, and `:80`'s premise per F12), `tests/test_repositories.py:33` (same),
  `tests/test_identifier.py:119-143` (the `WhatsAppJID` block gains the storable predicate),
  `tests/fixture_vault.py:94` (added with the class-Ø fold, round-3 note 4: the frozen corpus's declared
  person oracle hand-transcribes `models.py`'s defaults including `whatsapp: ""`, and that default becomes
  `[]` — machinery that moves with the field rather than a plant, and easy to miss because it is not in
  `obsidian_schemas/`), `tests/test_parser.py:248-264` (added with the F19 fold, leg 6: a THIRD in-tree
  reader of the representative's declared `whatsapp` alongside `tests/test_writer.py:404-428` and
  `tests/test_fixture_vault.py:705-761` — it compares every declared field against `spec.fields`, so it
  stays green under the LIST declaration and goes red for a builder who changes `:225` to a scalar), plus a
  migration entry point and `docs/wi-032-whatsapp-live-baseline.md` for the bracketed live run.
  `writer.py` is OFF the list — F8's projection is deleted by F13 leg 1.
- **ONE frame owns the phone-pivot rule, and the spec says which — otherwise it is written three times**
  (architect round-8 note 2, folded because the item's own principle is "no second spelling anywhere").
  After AC-1, three frames each decide independently what a `whatsapp` value contributes to `_phone_index`:
  `_index_entity` (`person.py:266-270`), `_remove_entity_from_indexes` (`:412-416`) and
  `_project_identifiers` (`:330-331`), and all three need the SAME rule (only a non-empty `phone_digits`
  pivots). `_index_identifiers` already runs at the END of `_index_entity` (`:283-284`) over
  `_project_identifiers`' typed output, so the phone-index insert can be DERIVED from the projected
  identifiers rather than re-parsed beside them — one call, one rule, and `_remove_entity_from_indexes`'s
  inverse derives from the same projection. AC-1's inverse-over-the-same-table assertion pins the BEHAVIOUR
  either way, which is why this is a note rather than a criterion; what it buys is that the next item to
  widen the rule finds one spelling instead of finding two and missing the third.
- **`repositories/person.py`'s PROSE is not ordinary material, and this is a constraint on HOW that file is
  edited rather than another file to edit (F20).** WI-024 froze every comment line and every docstring line
  of that module at Cut 0 (`tests/fixtures/identity_endgame/prose_surface_cut0.json`), and clause (e1) of
  `test_strangler_prose_class_is_closed_in_the_package` (`tests/test_identity_endgame.py:1008-1019`)
  asserts on every floor run that each Cut-0 `(owner, text)` pair belonging to an owner OUTSIDE the thirteen
  in `AUTHORIZED_PROSE_OWNERS` (`:359-373`) is still present. **`PersonRepository.save` is such an owner (29
  recorded lines, `prose_surface_cut0.json:2400-2544` ≙ `person.py:1158-1189` and `:1195-1196`) and so is
  the bare class `PersonRepository` (which owns the `_IDENTIFIER_PRIORITY` comment, `:1680-1683`).** So
  F11's write-back disclosure and F13's refusal disclosure land **APPEND-ONLY** in that frame: new
  paragraphs only, every existing Cut-0 line byte-identical, `AUTHORIZED_PROSE_OWNERS` and
  `prose_surface_cut0.json` untouched. `tests/test_identity_endgame.py` is therefore on this list as a wall
  the item JOINS, never as a file it edits — the same "leave the other item's wall alone" instruction this
  document already gives for WI-016's privacy wall (rejected item 11) and for the census digest (F18 leg 1),
  applied to a third frozen artifact. Authorizing `save` and reverting the prose are rejected items 15 and
  16. One more line from the same sweep, cheap and easy to trip: if the `_remove_entity_from_indexes`
  inverse (AC-1) is written as a LOOP over `self._phone_index`, its iterable must be wrapped in one of
  `MATERIALIZING_WRAPPERS = {"list", "tuple", "sorted", "frozenset", "dict"}` (`tests/derivations.py:1620`),
  because `tests/test_identity_endgame.py:642-644` asserts every phone-index iteration site in the package is
  classified `materialized`. `_IDENTIFIER_PRIORITY` (`person.py:778`) is NOT edited — it is a different
  frame's ordering and it is right as it stands (F15's amendment).
- **The fixture work, corrected by F17 and F18 and now itemized rather than called "the fixture plant",**
  because two of its five lines are edits to the FROZEN corpus and were previously mispriced as free
  members — and because item (iv) used to name an edit this item may not make:
  (i) `tests/fixtures/vault/@Thrandell Ibberly.md:7` and its manifest override
  `tests/fixture_vault.py:225` — the person round-trip representative's `whatsapp` becomes the storable
  class-B value `15555550142@lid`, because a class-C value there makes a correct build red at
  `tests/test_writer.py:421` and `tests/test_fixture_vault.py:753`. **The DECLARED SHAPE moves with the
  value, not just the string** (architect round-5 note 2): the corpus note keeps the scalar spelling while
  `:225`'s declared value becomes the LIST `["15555550142@lid"]` and `:94`'s person default becomes `[]`,
  because `tests/test_fixture_vault.py:745-748` compares `getattr(doc.entity, attribute)` against the
  declared literal and `:755-761` compares the RE-PARSED frontmatter MAPPING against the same literal —
  the tolerant reader (F7) is what makes the scalar note and the list declaration agree, and a builder
  reading this line as "change the string" gets it half right and red;
  (ii) the class-C value
  `447700900789@example.com` moves onto a NON-representative `type: person` corpus note (and its manifest
  spec gains the override) — a note whose `whatsapp` is currently `""`, which LOADS (never one of the
  three declared person skip specimens) and which declares NO `shape_classes`/`verdict` (never a census
  specimen, whose whole field set is written through the gated door with its refusal `pattern` asserted),
  subject to the constraint that the resulting `phone:447700900789` key collides with no phone already in
  the corpus, which F17 leg 3 measured as true today; **`@Fennwick Drostane.md` is the recommended
  receiver** and F18 leg 2 carries the derivation and the seven other admissible notes;
  (iii) `CORPUS_DIGEST` (`tests/fixture_vault.py:44`) regenerated
  by the one-line command in that module's docstring (`:21-25`); **(iv) `docs/vault-shape-census.md` is
  NOT touched by this item — no row, no digest, no edit.** Its class table is WI-016's name-corruption
  vocabulary (`branch_id`s derived from the Tier-1 tables plus six hand-listed shape classes, with
  live-vault counts and name specimens, `tests/test_fixture_vault.py:122-138`, `:830-848`), its MEASURED
  rows are an EQUALITY against the manifest's `shape_classes` with a per-note `Verdict` over `name`
  (`:800-803`, `:856-891`), and its digest is asserted against a literal inside WI-016's SIGNED AC-3
  `criteria` fence (`:217-254`, `docs/vault-fixtures.md:1418`) — so a `whatsapp` cell has no row to
  occupy and the digest has no build-owned home. This item's per-cell counts belong in its own
  precondition, `docs/wi-032-whatsapp-corpus-census.md`. If a later reader concludes a row IS owed there,
  that is a conductor pass plus a D4b re-sign of another item's signed criterion, in front of Dave
  (F18 leg 1, which retracts the old item (iv) and the F6 clause behind it);
  (v) classes A, D and E are plants in the
  NEW TEST MODULE's own temp vault and never touch `tests/fixtures/vault/` — A and the
  `notaphone@s.whatsapp.net` member of D are inadmissible in the corpus's reach by WI-016's privacy wall,
  and E joins them so the frozen corpus declares no class whose live population this item expects to be
  zero. `tests/test_fixture_vault.py` itself is NOT on the touch list: no wall of it is widened, weakened
  or exempted, which is the point of arm (a) (rejected item 11).
- **Three walls the NEW TEST MODULE joins by existing, carried here so they are not discovered as a red**
  (F18 leg 5, all in `tests/test_fixture_vault.py:1353-1442`, whose universe is every `*.py` under the
  package, the suite and `scripts/`): it names `ast` nowhere (single-homed to `tests/derivations.py`); it
  IMPORTS any skip reason from `obsidian_schemas/repositories/base.py` rather than typing the literal
  (the legal homes are pinned to exactly two files by EQUALITY, and AC-4(a)'s skip assertions are where
  the temptation is); and every top-level `def test_` it defines carries a name unique across all of
  `tests/test_*.py`, because `check_module` is a `def <name>(` substring scan that raises on anything but
  exactly one match (`tests/test_ac_interpreter.py:95-106`).

## Approach

Keep ONE authority for the shape where it already is — `WhatsAppJID` in `identifier.py` — give it the
second question storage needs, then add the three things that were missing around it and migrate the
corpus onto the new shape. Step (0) is new this round and everything after it is unchanged in intent.

**(0) Two predicates, one type (Ruling A).** `WhatsAppJID.parse` is unchanged: it is the REACH
predicate, liberal by design, and resolution and indexing keep using it exactly as they do today. The
type gains one derived property — does the raw value carry a WhatsApp JID domain, from a closed set
declared on the type — and that STORABLE predicate is read by the write door and by nothing else. This
is what makes the Intent's first sentence true: `"+44 7739 341679"` parses (so a lookup with it still
finds its person) and is not storable (so the PATCH door refuses to write it). One module, one parser,
no consumer asking the question for itself.

**(1) Cardinality, read tolerantly, and nothing typed in `model_fields`.** `whatsapp` becomes
list-shaped in storage; the reader accepts BOTH a scalar and a list indefinitely, because the VAULT is
shared mutable state — any consumer running older code against migrated notes breaks however the
package is installed, so a version pin is not an alternative (F14) — and because a refusing reader
raises `SchemaDriftError` and skips un-migrated notes out of existence (F7). The stored field is
`List[str]` holding the raw strings, with typed access as a DERIVED accessor (Ruling B, F13 leg 1,
WI-033's precedent). Two things follow for free: a value the door would refuse is never dropped at read
time, so it cannot be erased by the next save; and nothing dataclass-shaped is ever handed to
`yaml.dump`, so F8's `!!python/object` hazard is closed by construction rather than by a projection step
someone has to remember.

**(2) One write boundary, and the whole-record arms are among its arms.** `gate_write` gains a `whatsapp`
arm that
runs every introduced value through `WhatsAppJID.parse` and then the STORABLE predicate — judging a bare
`str` as well as a list, unlike the existing containers (F2) — and REFUSES on failure, carrying the
offending value as an attribute rather than in its message (F3, F4) under its own `pattern` value so a
bad JID is never routed as a bad name (F18 leg 4).

**And a REPORT arm beside the refusal arm, because the door only sees writes.** A door that refuses a value
says nothing about the values already on disk, and the whole design rests on the D+E residual being
"reported and left" — so `scripts/lint_vault.py` gains ONE report-only detector arm in `check_structural`
that fires on a stored `whatsapp` which is non-empty and not storable, in either stored shape, under its
own check name and with `auto_fixable` at its `False` default. This is a NEW arm and not a consequence: the
document previously priced it at zero on the strength of `_gate_refusal_pattern`, which has one call site,
behind `stem_name_divergence`'s `stem != stored` guard, emits no issue of its own, and whose live
population WI-029 closed to zero (F19, retracting F9). WI-029's own detector is the shape to copy —
ERROR, `structural`, never auto-fixable — and the arm must never report through that detector's
`NOT_RENAMEABLE_MARKER`, which would put a false "repair the field" message on a filename defect and move
another item's committed bracket (rejected item 14). Pinned by AC-3's REPORT LEG.

**And the arm's population is the NON-EMPTY values.** An absent key, `""` and `None` are class Ø: they
introduce no identifier, the predicates are never called on them, and every arm ACCEPTS them. This is not
leniency bolted on — it is the rule `_project_identifiers` already follows (`person.py:318-320`) and the
rule the gate's own `emails[]` arm follows by falsiness (`name_gate.py:399`) — and it is what keeps
CLEARING the field a legal write. That matters because clearing is the only repair a class-D value has,
and the design promises the D+E residual is left for hand repair; an arm that refused blank would refuse
that repair, and would additionally refuse the model's own default on every dict door (F16). Pinned by
AC-3's CLEARING and CLASS-Ø legs rather than described, because the refusing build is self-consistent and
green on everything else.

The `save` rider grows the matching write-back (F11), and because a whole-record projection re-introduces
the stored value it is also a refusal surface: a note whose
STORED value is unstorable cannot be saved through the repository until it is repaired, while the three
delta arms leave it writable for every write that does not re-introduce the field. Two arms carry that
projection, not one — `PersonRepository.save` and the exported `write_markdown_file(entity=…)`, which
`BaseRepository.save` delegates into (F11's correction) — so the disclosure is "re-serializing a whole
stored person record refuses", not "`save` refuses". That asymmetry is
deliberate and it is the `name` precedent; it is pinned in both directions by AC because the two wrong
builds — erase, or refuse everywhere — are each internally consistent (F13).

**And both of those disclosures are written APPEND-ONLY, which is a property of the FRAME they land in
rather than of what they say (F20).** `save`'s docstring is a frozen fixture of WI-024: all 29 of its Cut-0
lines belong to an owner outside `AUTHORIZED_PROSE_OWNERS` and must survive VERBATIM
(`tests/test_identity_endgame.py:1008-1019`, `:359-373`). So the write-back disclosure and the refusal
disclosure are NEW PARAGRAPHS beside `person.py:1174-1184` and `:1169-1172` — never extensions of them —
with `AUTHORIZED_PROSE_OWNERS` and `prose_surface_cut0.json` left alone, the same way this item leaves
WI-016's privacy wall and WI-016's census digest alone. It is stated here as an instruction AND asserted as
a clause in AC-3's `save` arm, because the two other ways to resolve the red an in-place edit produces are
each green on every `check:` this document names: authorizing `save` (which clause (e2) at `:1021-1030`
then makes red until one of its lines is DELETED) and reverting the disclosure (which withdraws
`### Examples of done`'s "and it says so" in silence). Rejected items 15 and 16.

**Disclosed, because it is a consumer-visible behaviour change of the class Dave required disclosed on
WI-029** (round-2 note 5, folded here rather than left inside a precondition's `why:`): a producer that
today writes a bare telephone number into `whatsapp:` — the class-C population, which includes whatever
sync wrote the Kim Faura value — starts being REFUSED the day this lands. That is the Intent working as
designed rather than a regression, but it is a break in somebody else's code path and it belongs in front
of Dave at the signature. `docs/wi-032-consumer-audit.md` is what turns "whatever sync" into a named list.
The class-Ø rule above is what keeps the break to that population instead of extending it to every
producer that clears the field.

**(3) One resolution door.** A public `get_by_identifier(Identifier)` plus a `whatsapp_jid` step in the
cascade reads the `jid:<lid>` keys the index already holds, with the new label added to
`_RESOLVE_CASCADE_ORDER` (`person.py:145`) so it does not rank last by accident (F15). And
`_index_entity` stops feeding a lid's digits into `_phone_index` — only a JID whose `phone_digits` is
non-empty pivots to a phone — with `_remove_entity_from_indexes` moving in lockstep (F5, F11, and the
defect in `## Problem / Motivation` item 3).

**(4) The migration, which is the item.** A dry run that reports per-cell counts over the six-cell class
table and writes nothing; the write through `vault_io` and through the gate; a readback whose oracle is
the set of `.key` values per note — unchanged, and the identifier COUNT per note unchanged, so a run
that dropped a person's second JID fails while a key-preserving spelling repair passes. The readback is a
RE-READ from the note bytes by a load that did not exist before the write (round-3 note 3): the repository
holds a process-local cache and re-indexes the entity it just wrote (`person.py:257-284` plus the save
rider), so a "readback" computed through the migrating process's own repository compares the model against
itself and is green by construction — the private-stale-replica shape, and the reason verify-by-readback
means a re-READ. That oracle is
computed over the PARSEABLE stored values only (classes A, B, C, E); a class-D value has no `.key` to
compare, because `WhatsAppJID.parse` RAISES on it, so its guarantee is the byte-identical one instead —
stated in AC-5 leg (c) rather than left for a test author to infer. Class Ø is a SHAPE-ONLY conversion
(`""` → `[]`), contributes no key to either side, and is the corpus's dominant cell. It carries the
class-C repair
(`"+44 7739 341679"` → `"447739341679@s.whatsapp.net"`, same `phone:` key) as its own counted class,
repairing ONLY values whose `phone_digits` is non-empty, which is what reduces the `save`-refusal
population to class D plus class E; **classes D and E are reported and left byte-identical** — E
because repairing a phone-less value would write `"@s.whatsapp.net"`, which `parse` then refuses. Counts
reconcile across dry run, write and readback or the run exits non-zero, and they reconcile over the TRIPLE
of `## Exploration Notes`' TERMINAL-STATE PARTITION rather than over one absolute — part-for-part across
(scalar-outside-R = 0, migrated, R) — because a note in the residual R cannot be converted at all: the
conversion is a write that RE-INTRODUCES the field and step (2)'s door refuses it in both shapes, so R is
terminally scalar BY DESIGN. **The run therefore never CLEARS a value to make a note convert** — that would
move a class-D note out of R and reach the zero trivially by erasing the population this item exists to
preserve; clearing is a hand repair somebody ASKS for through a delta arm, never something the run does.
This is WI-010's un-park criterion, met once, properly.

**And the live run is a SHIP CONDITION, not effort** (round-2 note 4, carried through round 3, folded
here). A migration whose only acceptance is the corpus it was written against is a specimen in a jar:
AC-5 is hermetic by necessity and the census is the audit-before-patching half, but the item ships against
the real vault, in WI-029's exact shape — entry numbers committed to
`docs/wi-032-whatsapp-live-baseline.md`, the dry run read and shown to Dave, his go, the write, then exit
numbers in the same doc's §5 (`docs/stem-divergence-live-baseline.md` is the precedent to copy literally).
**The exit numbers that matter are the TERMINAL-STATE PARTITION's three parts, counts only, stated in the
bracket's exit row exactly as `## Exploration Notes` states them** (F21 — the earlier wording promised "zero
notes left in the scalar shape" alongside "the residual reported and byte-identical", which no run can
produce once the residual is non-empty, so a conductor performing the bracket against a non-zero census row
was left adjudicating the figure in prose): (1) notes left in the scalar shape OUTSIDE the residual R —
ZERO; (2) `|R|` — the notes whose value the STORABLE predicate refuses, each reported and byte-identical,
equal to the census's class-D plus class-E rows, plus its class-C row if Dave declines the repair (Ruling B's
alternative arm); (3) the class-C repair count equal to the census's class-C row under the recommended arm,
and zero under the alternative arm with those notes counted in `|R|` instead. Plus the identifier-key
multiset unchanged corpus-wide, and no value cleared by the run. **One of those numbers is now readable off a tool rather than off the migration's
own stdout**, which is what the report arm buys the bracket: after the run, `scripts/lint_vault.py`'s new
detector reports exactly the members of R over the live vault — the detector fires on classes C, D and E, so
its issue set IS R under either arm of Ruling B — and the exit figure for part (2) is that check's issue count
compared against the census's class-D and class-E rows (plus class C under the alternative arm). An
independent second witness to the residual rather than the migrating process reporting on itself, which is
the same verify-by-readback reasoning AC-5 leg (c) applies to the keys (F19), and the reason the partition's
zero-outside-R figure is falsifiable rather than a promise: the two counts are taken by different tools and
must agree.

**Back-out (F14).** Reverting the library is NOT a back-out: a list-shaped note against pre-WI-032 code
fails `model_validate` and `parse_to_model` raises `SchemaDriftError`, making the note invisible rather
than oddly shaped. The back-out is a REVERSE migration through the same door, and it is exact only while
no note carries a second JID — which is true on the day this ships, because this item makes the shape
available and does not itself populate second JIDs (that is HAL9000 WI-075 / orchestrator WI-192-193).
Once a second JID exists anywhere, list→scalar loses one by definition and the position is forward-only
with the tolerant reader kept. The live run is bracketed entry/exit the way
`docs/stem-divergence-live-baseline.md` brackets WI-029's, and the exit entry records the window closing.

## Write Targets

Two conductor-committed grounding artifacts. Both must be in the tree's git HEAD BEFORE the acceptance
criteria are presented for signature (WI-300). Neither is producible from inside the cage: one needs
the live vault and the WhatsApp bridge store, the other needs three repositories outside this
project's write authority. The spec-writer EXTENDS this section at `exploring → specced`; these two
fences are never replaced — their `grounds:` ordering is what makes the AC frame correct.

One artifact is deliberately NOT a precondition here: `docs/wi-032-whatsapp-live-baseline.md`, the
entry/exit bracket for the live run. It is a DELIVERABLE of the ship condition (`## Approach` step (4)),
written during the drive the way `docs/stem-divergence-live-baseline.md` was, not evidence a criterion's
premise rests on beforehand — so it belongs in the spec-writer's extension of this section, not in a
`kind: precondition` fence the AC frame waits on.

```writes
kind: precondition
path: docs/wi-032-whatsapp-corpus-census.md
grounds: Whether a refusing write door and a scalar-to-list migration are affordable against the live person corpus as it stands today
why: AC-3 makes the door refuse a value the STORABLE predicate rejects and AC-5 migrates and repairs every stored value, so both rest on a population nobody has measured for this field. The closest committed figure (`docs/identity-cutover-corpus-audit.md:132`) is dated 2026-09-06, pools `phones` with `whatsapp`, and counts no `@lid`. REVISED THIS ROUND - the earlier version of this line asked for "values `WhatsAppJID.parse` REFUSES", which F12 shows is the wrong population, since that parser accepts a bare phone number and so refuses only digit-less junk. Needed, counts only and no live identifier, one row per cell of the SIX-cell class table in `## Exploration Notes` - class Ø, the notes with no `whatsapp` identifier at all (an absent key, `""`, YAML null or `None`), which the write door ALWAYS accepts and which is the corpus's dominant cell (21 of the 22 `whatsapp`-carrying fixture notes, F6) so its count is the denominator the other five rows are read against, and which is also the count of notes the migration converts SHAPE-ONLY - and this row specifically MUST be counted off the note BYTES rather than off loaded models, because a note carrying a bare valueless `whatsapp:` key loads as YAML null, `_normalize_frontmatter` passes `None` through untouched (`parser.py:118-132`), `whatsapp: str` (`models.py:94`) rejects it and the owned note therefore raises `SchemaDriftError` onto the load skip surface (`parser.py:203-208`), so a model-based count omits exactly the bare-key notes it most needs to find; class A, a storable phone-bearing JID; class B, a storable `@lid`; class C, parses and is phone-bearing but carries no JID domain from the closed set (this is the Kim Faura population and the number that decides whether the door's refusal needs the migration's repair pass first, so it is the load-bearing row); class D, NON-EMPTY and does not parse at all - the emptiness carve-out matters to this row specifically, because `WhatsAppJID.parse` raises on `""` and `None` through the same lines it raises on `"n/a"` (`identifier.py:271-275`), so a census that files every raising value as D would report ~the whole corpus as a defect population and misprice Ruling B leg 2 by three orders of magnitude; class E, added this round, contains the `@lid` substring but its domain after the last `@` is not in the closed set, so it parses with empty `phone_digits` and is not storable (`123@lid.example.com` shape) - D and E TOGETHER are the residual population for which `PersonRepository.save` will refuse after the migration, since neither is repairable, so they are the rows that price Ruling B leg 2 and E is expected to be ZERO, which is itself the answer worth having on paper rather than assumed. These two rows are also the rows the live bracket's EXIT figure is compared against, which is what makes them counts rather than commentary: the residual R of `## Exploration Notes`' TERMINAL-STATE PARTITION is terminally SCALAR - a conversion re-introduces the field and the door refuses it in both shapes - so `|R|` must equal class D plus class E here, plus class C if Dave declines the repair (Ruling B's alternative arm), and a disagreement between this census and the `lint_vault` detector's post-run issue count is the bracket's failure signal (F21). Plus the count of people the bridge store shows holding more than one JID (the premise paragraph's 51, re-measured) and the count of lids whose digits `phones_match` would tie to a stored phone (the false-positive population the resolution fix retires). Privacy wall and shape precedent - `docs/stem-divergence-live-baseline.md`.
```

```writes
kind: precondition
path: docs/wi-032-consumer-audit.md
grounds: Whether any consumer reads or writes `Person.whatsapp` as a scalar string, and so what the scalar-to-list flip breaks outside this repository the moment it lands
why: The vault is shared mutable state, so any consumer running older code against a migrated note breaks however the package is installed (F14 corrects F7's `-e` framing, which invited the useless counter "then pin a version"); a scalar reader in HAL9000 or exocortex breaks when the notes change, not at a deploy. Wanted per repo - 40-hex HEAD, dirty count, the literal commands, verbatim matching lines for `.whatsapp`, `"whatsapp"`, `'whatsapp'` and the `ContactInfo` mirrors, and each site classified on THREE axes, not two - READ or WRITE; scalar-assuming or shape-agnostic; and whether it assumes the ELEMENT type, since a shape-agnostic site like `list(person.whatsapp)` survives the cardinality flip and would still break if elements stopped being `str`. Under Ruling B's recommendation the elements stay `str` and that third axis should come back empty, which is the point of asking - an audit that finds element-type assumptions is evidence FOR keeping the stored field `List[str]`. Also whether any consumer feeds a JID to `get_by_phone`, which `README.md:238` currently documents as the way to look one up, and whether any consumer writes a bare phone number into the field (the class-C producers, who will start being refused - the disclosed break in `## Approach` step (2)). Two more questions added with the class-Ø fold and the F11 correction, both cheap to ask and expensive to discover: does any consumer CLEAR the field (writing `""` or `None`, e.g. HAL9000's PATCH door emptying it or a template-shaped create), since class Ø must keep succeeding and a refusing build would break every one of those sites; and does any consumer write a Person entity through `save` or through the exported `write_markdown_file(entity=...)`, or otherwise re-serialize a whole stored person record, since those are the whole-record-projection arms where a STORED unstorable value is re-introduced and therefore refused, which is a wider surface than `save` alone. Precedent and shape - `docs/wi-029-consumer-audit.md`, `docs/wi-024-consumer-audit.md`; code paths only, no vault note name, no live identifier.
```

## Acceptance Criteria

Drafted at `exploring` for Dave to agree or tweak, then FROZEN by his signature through
`/review-spec` (`bin/review-spec-helper.py review --wi-id WI-032 --project <path>`) — code writes the
`ac-signoff` fence, never this document's author. Five criteria; each computes its expected value by
CALLING the two predicates stated at the top of `## Exploration Notes` — never from a literal read off
the same source as the implementation, and never from a restated shape.

**Read the three rulings first.** These five are drafted to the recommended arm of each. Ruling A
decides whether AC-3's refused population is C + D + E or class D alone — that is the difference
between closing the minted defect and retiring it. Ruling B decides AC-4 leg (b) and AC-3's `save` arm,
and AC-5 leg (d) is written to hold either way he rules on the repair. All three are a one-line edit
now and a D4b re-sign after the signature. **None of them is touched by the class-Ø fold below**, which
narrows the refused population to exactly what Dave's ruling (1) already describes.

**What the AC red-team round changed (2026-09-26), so a reader can see the delta without diffing.** Two
things, both inside the criterion text rather than in a paragraph a builder has to infer from. (i) AC-5
leg (c)'s readback oracle now states that the key multiset ranges over the PARSEABLE values only, with
the parseable/unparseable split computed by calling `parse` and catching `IdentifierError`, and class D's
guarantee named as byte-identity instead — the old wording ranged over "the pre-migration raw value or
values" while the same AC mandates a class-D plant, so the oracle RAISED on its own fixture rather than
passing or failing. A total-value count was added alongside the key count so the exclusion cannot become
a licence to delete what it excludes. (ii) The class table gained **class E** — parses via the `@lid`
SUBSTRING, no phone digits, not storable — which is the cell the four-cell table was missing and the
counterexample to its "exhaustive" claim; AC-1's exhaustiveness is now scoped to the enumerated table,
the corpus and a named boundary-probe list, with the classifier asserted to have NO fall-through bucket,
and every downstream statement of "class D alone" became "class D plus class E". The architect's
round-2 notes 1 and 2 are absorbed in the same move: the STORABLE predicate's closed-set reading is
pinned (the bare-suffix licence is deleted, because it changes which cell Thrandell's value falls in),
and AC-5 leg (d)'s repair is guarded on `phone_digits` being non-empty.

**What the SECOND AC red-team round and the architect's third round changed (2026-09-26), same
convention.** Both gates found the same defect independently in text no earlier fold had touched: the
class table filed `""` and `None` under class D, and AC-3 refuses class D at every arm — so the door
refused the model's own default, the value on 21 of the 22 `whatsapp`-carrying fixture notes, and the only
spelling this package has for CLEARING a field, which made the hand-repair path AC-5 leg (e) and Ruling B
leg 2 promise for the D+E residual unbuildable. Nothing in the drafted suite would have caught it, because
the entity path never hands the gate a literal `""`. The fold: (i) **class Ø** enters the table as a cell
of its own — absence introduces no identifier, is classified BEFORE either predicate is called, and is
ACCEPTED at every arm (F16, which carries the derivation and the citations); (ii) class D's exemplars lose
`""`/`None` and its definition gains NON-EMPTY; (iii) AC-3's refusal population is scoped to the non-empty
values that fail STORABLE, and it gains a **CLEARING leg** — clearing the field succeeds even when the
stored value is class C, D or E, which is the residual's actual repair door — and a **CLASS-Ø leg**, that
class accepted at every arm in every spelling; (iv) AC-1 asserts the classification ORDER rather than only
its totality, because a classifier that asks the predicates first files the whole corpus as D; (v)
AC-4(a)'s empty-as-absence clause is cross-referenced to the CLASS-Ø leg so the read and write sides state
one rule instead of two. Three of
the architect's non-blocking notes are folded in the same pass: the `whole_record` handle corrected to
"whole-record projection" with `write_markdown_file(entity=…)` named as the second such arm (F11, AC-3,
`### Examples of done`), AC-5's readback pinned as a RE-READ from note bytes rather than through the
migrating process's own cache, and `tests/fixture_vault.py:94` added to the touch list.

**What the THIRD AC red-team round and the architect's fourth round changed (2026-09-26), same
convention — and this one changes WHERE the discriminating members live, not WHAT anything asserts.**
Both gates, again independently, attacked the fixture-plant plan the previous folds had written and
found it had never been checked against the frozen corpus's own two contracts. (i) `@Thrandell
Ibberly.md` is the corpus's SOLE person `roundtrip_representative` and two in-tree tests write it
through the gated whole-record arm asserting NO refusal, so AC-1's `why:` calling its class-C value
"free" licensed a build that turns both tests red and then "fixes" them by deleting the repo's only
proof that a whole person field set survives the write door. (ii) The class-A and class-D
`@s.whatsapp.net` literals and the class-E `…@lid.example.com` literal are all RED on WI-016's privacy
wall if planted in the frozen corpus's reach — structurally so for class A, since STORABLE is
membership of `{"s.whatsapp.net", "lid"}`, which is itself why the corpus's one JID is spelled
`@example.com` and therefore class C at all. The fold, all of it inside criterion text: the class table
gains a fourth column saying where each cell's member can physically live; AC-1 gains a WHERE CLAUSE
(A, D, E and every boundary probe are test-module literals; B replaces the representative's value with
the storable `15555550142@lid`; C moves to a non-representative corpus note keeping
`447700900789@example.com`) and asserts the representative is storable-clean; AC-1's `why:` retracts
the "free" claim; AC-3's required class-E member is respelled `447700900654@lid.example` (same cell,
wall-clean) and its `why:` names the re-expect-the-refusal branch as forbidden; AC-5 states that its
plants land in the MATERIALIZED COPY only; and every planted digit run is now an UNUSED member of a
reserved block, because the old class-A exemplar reused Thrandell's own phone digits and would have
minted a silent identifier conflict. F17 carries the derivation and the citations; rejected items 11
and 12 record the two branches not taken. Three of the architect's non-blocking notes land in the same
pass: AC-2's class-Ø cascade leg restated as a pin on the blank-query guard's POSITION (the behaviour is
already true at `person.py:606-611`, so the leg now guards the new step being inserted BELOW it),
AC-4(a) naming YAML null as a class-Ø read spelling, and the census's class-Ø row required to be
counted off note BYTES. **No ruling is touched, and no criterion's assertion changed** — which is the
test this fold had to pass, since the previous round's text was already signed off on by two gates on
every other axis.

**What the FOURTH AC red-team round and the architect's fifth round changed (2026-09-26) — and this one
finishes the sweep rather than adding another member to it.** Both gates went one level past the previous
fold and found the two places it had stopped short. (i) AC-5 required a plant "one note carrying TWO
JIDs" and, ALONE among that criterion's required members, pinned no literal for it — so the values a test
author reaches for are the class-A and class-B ones printed two sentences earlier, which puts a second
entity carrying `phone:447700900321` or `jid:15555550142@lid` into the same materialized copy and mints
the silent identifier conflict F17 leg 3 had already found and priced ("it would not go red, it would
just be wrong"), on the one note whose entire purpose is proving a person keeps BOTH identifiers.
(ii) `### Effort` item (iv) and F6 still priced "a census row per newly declared class, and its own digest
follows" as free build-side work, but `docs/vault-shape-census.md` is digest-frozen against a literal
inside WI-016's SIGNED AC-3 criterion and its row vocabulary is name-corruption `branch_id`s with
live-vault counts and name specimens — so the two cheapest greens were amending another item's signed
criterion or writing a false `ABSENT/0` row, which is verbatim the route that criterion exists to close.
The fold: AC-5's desc pins `447700900987@s.whatsapp.net` and `15555550163@lid` for the two-JID note (both
unused reserved-block members, both unclaimed tree-wide); `### Effort` item (iv) now states
affirmatively that the census is NOT touched and F6 and its third amendment drop the row clause; and F18
runs the plant-literal × corpus-contract MATRIX to its end, stating the walls that came back clean as
well as the ones that bit — the skip surface, `LOADABLE` and `RESOLVABLE`; the census verdict loop, which
adds a receiver constraint to AC-1's WHERE clause (`@Fennwick Drostane.md`); where the refusal `pattern`
is DECLARED, now a clause in AC-3 rather than an inference; the three set-equality walls the new test
module joins, one of which lands as a clause in AC-4(a); and a literal-by-literal sweep whose one empty
row is stated as empty. **No ruling is touched and every criterion's assertions are the same ones** —
what changed is which literal, which note and which artifact the criteria name.

**What the FIFTH AC red-team round and the architect's sixth round changed (2026-09-26) — and this one
ADDS an assertion rather than relocating a literal, which is what makes it different from the four folds
above.** Both gates, independently again, left the fixture-plant class (which they agree is closed) and
attacked F9 — ORIGINAL text no fold had touched — finding that the linter's report surface does not exist.
`_gate_refusal_pattern` has exactly ONE call site (`scripts/lint_vault.py:450`), inside
`check_structural`'s `stem_name_divergence` arm and behind `stem != stored`, where it splices a MARKER
into that issue's message and emits no `LintIssue` of its own; `rg -n 'whatsapp' scripts/lint_vault.py` is
0 matches; and WI-029 closed that arm's live population to ZERO five days before this item was minted
(`docs/stem-divergence-live-baseline.md:191`). So the "reported and left" promise that `## Intent`, F13
leg 3, Ruling B leg 2, AC-5 leg (e) and `### Examples of done` all make had, as its only named mechanism,
AC-3's closing clause — a sentence that called the consequence FREE, carried no `check:` of its own, and
was therefore satisfied by three different builds, two of them silent. The fold: **AC-3's closing clause
becomes a REPORT LEG with five assertions** — a new report-only detector arm in `check_structural`, its own
check name, ERROR/`structural`, `auto_fixable` at its `False` default, firing on classes C/D/E in BOTH
stored shapes, silent on class Ø and on storable values, and never reporting through
`stem_name_divergence`'s `NOT_RENAMEABLE_MARKER` — and **AC-3's `check:` is renamed to name both
surfaces**, because a write-door test has no reason to assert anything about a lint tool unless the
criterion says so. AC-1's WHERE clause gains its third receiver constraint, NOT STEM-DIVERGENT, which the
first two do not imply (two marker-bearing divergent notes satisfied the old clause); AC-5 leg (e)'s
"reported" names the detector; `### Effort` carries `scripts/lint_vault.py` as a DETECTOR plus a test
module instead of "pattern routing only", and gains `tests/test_parser.py:248-264` as a third reader of the
representative's declared value; F9 is RETRACTED in place and F19 carries the derivation, the three-build
argument and the measured cost. **`## Intent` is unchanged** — its promise is now true by construction, and
the alternative of deleting the word "reported" from five places is a promise being withdrawn, which is
Dave's call and is recorded as rejected item 13 rather than taken here. No ruling is touched.

**What the SIXTH AC red-team round and the architect's seventh round changed (2026-09-26) — one clause, on
the PACKAGE file this item edits most, which is the artifact class no round had opened.** Both gates,
independently again, left the two closed classes (fixture plants, the report surface) and read the walls
that sweep `obsidian_schemas/repositories/person.py` itself. WI-024 froze that module's comment and
docstring TEXT at Cut 0, and clause (e1) of `test_strangler_prose_class_is_closed_in_the_package`
(`tests/test_identity_endgame.py:1008-1019`) asserts on every floor run that every Cut-0 `(owner, text)`
pair of an owner outside the thirteen in `AUTHORIZED_PROSE_OWNERS` (`:359-373`) survives verbatim —
and `PersonRepository.save`, the frame F11 makes this item's write-back disclosure home and F13 makes its
refusal surface, is such an owner, with 29 recorded lines (`prose_surface_cut0.json:2400-2544`, count
re-run for this fold; both arriving fences say 31). So F11's accurate citation of `person.py:1180-1184` as
the disclosure's model invited the one edit that reddens it, and the red resolves three ways, all green on
every `check:` in this set: append (correct and free), authorize `save` (then clause (e2) at `:1021-1030`
demands one of its lines be DELETED), or revert the disclosure (silently withdrawing `### Examples of
done`'s "and it says so"). The fold: **AC-3's `save` arm gains an APPEND-ONLY clause with three conjuncts**
— the Cut-0 pairs survive, `AUTHORIZED_PROSE_OWNERS` and `prose_surface_cut0.json` are untouched (the
conjunct WI-024's own clauses cannot supply, since authorize-and-delete satisfies both), and the disclosure
demonstrably LANDED — and AC-3's `check:` is renamed for the third surface it now asserts. `## Approach`
step (2) states the same constraint as an instruction, `### Effort` carries `person.py`'s prose surface and
`tests/test_identity_endgame.py` as a wall the item JOINS, F11 is amended so its citation names a shape
rather than a paragraph to extend, and rejected items 15 and 16 record the two branches not taken. F20
carries the derivation and sweeps the rest of that suite against every frame this item edits, stating the
five CLEAN results (the Cut-0 resolve golden, the wall-membership rows, `phone_index_iteration_sites` with
its materializing-wrapper constraint, the `ast` single-home, and `tests/test_phone_normalization.py`'s
`parse` boundary) as well as the one that bit. The architect's note on `_IDENTIFIER_PRIORITY` — a SECOND
`whatsapp_jid` ordering this document never cited — lands as an amendment to F15: different frame, right as
it stands, not edited. **No ruling is touched and no arm's behaviour changed** — what moves is where a
disclosure's TEXT may be written.

**What the SEVENTH AC red-team round and the architect's eighth round changed (2026-09-27) — and this one is
the first that made a criterion UNBUILDABLE rather than wrong about a fixture, a tool or a frame.** Both
gates, independently again, left all three closed artifact classes and asked a question no round had asked:
what does the vault LOOK LIKE when the migration has succeeded? AC-3 refuses a class-D/E value in both
shapes and AC-5 leg (b) routes every migration write through that gate, so a shape conversion — a write that
RE-INTRODUCES the field, which the delta rule therefore cannot excuse (`name_gate.py:31-36`) — is refused for
those notes and they are TERMINALLY SCALAR. Yet AC-5 leg (e), `## Approach` step (4)'s exit numbers and
`### Examples of done` all promised "zero notes left in the scalar shape" in the same breath as "the D+E
residual reported and byte-identical", and AC-5's own mandated class-D and class-E plants make that population
non-zero in the hermetic suite — so no build passed, and all four routes out were red (accept → AC-3, bypass →
leg (b), CLEAR the values → leg (c)'s total-value count and silent erasure, honour byte-identity → the old
leg (e)). The fold: **the exit figure becomes a PARTITION rather than an absolute** — `## Exploration Notes`
declares THE TERMINAL-STATE PARTITION once (scalar-outside-the-residual = 0; MIGRATED; the RESIDUAL R,
reported and byte-identical, its membership per Ruling B's arm and `|R|` equal to the census's corresponding
rows) and AC-5 leg (e), `## Approach` step (4), the live bracket's exit row and `### Examples of done` restate
it; **leg (e) gains the never-clears conjunct**, so the erase-to-convert route is red BY INTENT rather than as
a side effect of a guard added for another reason (rejected item 17); **leg (d)'s "either way Dave rules"
claim is corrected** and asserted over BOTH arms, because under Ruling B's alternative arm class C joins R and
the number Dave is shown changes; **AC-4 leg (c) is scoped** to writes that succeed and introduce the field,
the same absolute one criterion over. And the class is CLOSED by a declared sweep in `## Exploration Notes`:
every absolute — "zero", "every", "all", "never" — in the five AC descs, `## Intent`, `## Approach` and
`### Examples of done`, with the population it ranges over and the residual it excludes, the clean rows stated
as clean. F21 carries the derivation. **No ruling is reopened and nothing about what the migration does to any
cell moves** — what moves is what this document claims the vault looks like afterwards, plus the cost line
Ruling B's alternative arm was missing.

```criteria
id: AC-1
desc: A JID's digits enter `_phone_index` IF AND ONLY IF `WhatsAppJID.parse` gives it a non-empty `phone_digits`, and the discriminating member is PLANTED rather than hoped for. The fixture space is a table of raw values the test classifies BY CALLING the two predicates of `## Exploration Notes` - `WhatsAppJID.parse` and the STORABLE property - yielding the SIX cells of that table: Ø (introduces NO identifier - an absent key, `""` or `None` - filed BEFORE either predicate is called), plus the five classes of a NON-EMPTY value, A (parses, phone-bearing, storable), B (parses, `@lid`, `phone_digits == ""`, storable), C (parses, phone-bearing, NOT storable), D (NON-EMPTY and does not parse) and E (parses via the `@lid` SUBSTRING, `phone_digits == ""`, NOT storable - the `447700900654@lid.example` shape, whose `jid_domain` is `lid.example` and so is not in the closed set), with each cell asserted non-empty so a cell that loses its only member is RED rather than vacuously green. The classification ORDER is asserted, not merely the classification - an emptiness test precedes both predicate calls, proven by the classifier filing `""` and `None` as Ø rather than as D, because `WhatsAppJID.parse` raises on them through the same two lines it raises on `"n/a"` with (`identifier.py:271-275`, no blank branch) and so a classifier that asks the predicates first files the corpus's dominant value as a defect class (F16). The EXHAUSTIVENESS claim is stated at the reach it actually has, which is the correction the previous round made - the classifier is a TOTAL function with NO fall-through bucket, so a raw value matching no declared cell RAISES rather than being silently filed, and it is asserted total over (i) the enumerated raw-value table, (ii) every `whatsapp` value in the fixture corpus, classified without exception, and (iii) a named boundary-probe list, held as literals in the NEW TEST MODULE (never in the frozen corpus - see the WHERE clause below), that includes `447700900654@lid.example`, `123@lid.example.com`, `notaphone@s.whatsapp.net`, `447700900789@example.com`, the bare `"+44 7739 341679"`, and - added with class Ø - `""`, `None`, YAML null, a whitespace-only `"   "` and an absent key. It is NOT claimed over every string in the language - that was the four-cell table's false promise, and class E was the counterexample: it parsed, carried no phone digits and was not storable, so it belonged to no cell while every planted exemplar still went green. Per member the oracle is the predicate results themselves, never a restated shape. Classes A and C, the index key is exactly `phone_digits` and `get_by_phone(<that number>)` returns this person - C is in the phone arm deliberately, because a bare number in the field IS a stored phone number and resolution stays liberal (F12), and the test states that as the expected answer rather than leaving it to inference. Classes B and E, NO key derived from the value's digits exists in `_phone_index` at all, and the falsifying member is planted and named - a lid whose digits are an 11-digit string beginning with `1` on a vault where NOBODY holds the corresponding 10-digit number, for which `get_by_phone(<the 10-digit form>)` must return None (today it returns the lid's owner, via the permanent fuzzy arm at `person.py:494-496`). That member is spelled `15555550142@lid` and its 10-digit counterpart is `5555550142`, which is not a free choice of digits: a class-B member sits in the frozen corpus (the WHERE clause below), where `reserved_phone_violations` scores every ≥9-digit span against the drama block or NANP 555-01xx (`tests/test_fixture_vault.py:308-312`, `:342-361`), so an arbitrary 11-digit lid is RED on that wall and the control would be discovered unplantable at build time; `15555550142` matches the 555-01xx pattern and no member of that block appears anywhere in the corpus today (F17 leg 3). E is planted with its digits in the ≥ `Phone.MIN_DIGITS` range for the same reason, so a build that lost the `@lid` branch and fell through to `normalize_phone` produces a phone key and is RED rather than raising for an unrelated reason. Class D, the NARROWING arm - there is no right phone for a value the parser refuses, so the assertion is the declared marker - no `_phone_index` entry, no exception out of the load, and the note still loads. Class Ø, the same NARROWING arm and for the same reason, plus one more assertion that distinguishes it from D - no `_phone_index` entry, no `jid:` entry, NO identifier of any kind projected from the field (the `_project_identifiers` output for that note carries no `whatsapp_jid` member at all), and the note loads clean; a build that filed Ø as D would satisfy the no-key half and fail nothing else in this criterion, which is why the no-identifier-projected half is stated. The two predicates are asserted INDEPENDENT in BOTH directions on planted members - `notaphone@s.whatsapp.net` carries a JID domain and is class D, and class E parses while carrying a domain that is not one - so a build that implemented storability as "parses", or parsing as "has a suffix", or storability as "contains `@lid`", is RED. THE WHERE CLAUSE, which is part of the criterion and not a build note, because two of these members are inadmissible in the frozen corpus and a build that plants them there turns ANOTHER item's green wall red: classes A, D and E - and every literal of the boundary-probe list - live in the NEW TEST MODULE's own temp vault and are never written into `tests/fixtures/vault/` or declared in `tests/fixture_vault.py`; class Ø is the corpus's own 21 `whatsapp: ""` notes; class B is the person round-trip representative's value; class C is a non-representative corpus note carrying `447700900789@example.com` - and WHICH note that is carries THREE constraints of its own rather than being free choice among the 21: it must be a note that LOADS, so never one of the three declared person skip specimens (`tests/fixture_vault.py:490-494`), because this criterion's class-C arm asserts `get_by_phone` returns that person and on a skipped note the leg is vacuous rather than red; it must declare NO `shape_classes`/`verdict`, because the census verdict loop writes every shape-class specimen's whole declared field set through the gated door and asserts the refusal `pattern` equals the DECLARED name pattern (`tests/test_fixture_vault.py:856-878`), so a non-storable `whatsapp` there makes which refusal fires depend on where the new gate arm sits relative to the name arm; and it must NOT BE STEM-DIVERGENT, which is the constraint this round adds and which the first two do not imply - `@Perrowin Tessamund Drostane.md` and `@Yolvenna Brindlecote Skarnell.md` LOAD and declare `shape_classes=()` with no verdict (they carry a `discriminator` instead, `tests/fixture_vault.py:294-306`) and so satisfied the WHERE clause as it stood, while being the corpus's two MARKER-BEARING divergent notes, asserted by EQUALITY at `tests/test_stem_name_divergence_detector.py:341-345` with their patterns pinned individually at `:346-352`: a non-storable `whatsapp` on either routes through `_gate_refusal_pattern` (`scripts/lint_vault.py:450`) and makes that other item's marked-set equality depend on the new gate arm's insertion point, the same question the second constraint removes for census specimens. `@Fennwick Drostane.md` is the receiver, one of eight plain loading notes that satisfy all three (F18 leg 2, F19 leg 5), and the constraint is stated as well as the note because the constraint is what a builder reasons from when the named note stops being available. All four divergent corpus notes carry `whatsapp: ""` by `_person`'s declared defaults (`tests/fixture_vault.py:85-105`), so they stay class Ø under the two corpus edits and that marked set is untouched by the edits themselves. The corpus must hold NO class-A and NO class-C member on `@Thrandell Ibberly.md`, and that is asserted rather than left to review: the test reads `NOTES` and fails if the person `roundtrip_representative`'s declared `whatsapp` is not accepted by the STORABLE predicate, and WI-016's own privacy-wall leg (`tests/test_fixture_vault.py:302-319`, reach at `:386-392`) stays green untouched - no exemption added, no pattern widened. `_remove_entity_from_indexes` is asserted to be the exact inverse over the same table, so a refresh leaves no orphan key.
why: A lid is an opaque WhatsApp-internal id, so indexing its digits as a telephone number invents an identity claim the data never made, and `phones_match`'s US arm turns that into a false-positive answer for a number nobody has - the corruption shape with a real victim. The class table is derived by CALLING the type rather than hand-listed, so widening the storable domain set or adding a third accepted parse form later joins the sweep automatically. The plants are required because the frozen corpus has zero `@lid`, zero unparseable and zero storable-JID members and would green a build that changed nothing. Only class Ø is FREE (21 notes); the other five cost something, and the WHERE clause is where they cost it - a claim this criterion made wrongly for two rounds and which F17 corrects. Classes A, D and E are temp-vault plants because WI-016's privacy wall makes `@s.whatsapp.net` inadmissible anywhere in the corpus's reach - which is structural for A, since STORABLE is membership of `{"s.whatsapp.net", "lid"}` - and because the wall is another item's green invariant, not this item's to widen (rejected item 11). Classes B and C are corpus EDITS: the earlier text called C free because `@Thrandell Ibberly.md:7` already carries a class-C value, but that note is the corpus's SOLE person `roundtrip_representative` (`tests/fixture_vault.py:219-233`, `tests/test_fixture_vault.py:689-695`) and two tests write it through the gated whole-record arm asserting no refusal (`tests/test_writer.py:421`, `tests/test_fixture_vault.py:753`) - so a build implementing AC-3 correctly turns both red, and the self-consistent repair is to delete the repo's only proof that a whole person field set survives the write door (rejected item 12). Hence B replaces the representative's value and C moves to a non-representative note, which is WI-016's own deviation-3 fold for the identical collision (`docs/vault-fixtures.md:5938-5943`). The digits are pinned rather than illustrative for the same class of reason: the old class-A exemplar reused Thrandell's own phone digits and would have minted a silent identifier conflict, and an arbitrary class-B lid is RED on the corpus's phone wall (F17 leg 3). The RECEIVER is named for the same reason one level further out - "any note whose `whatsapp` is `""` will do" was true of the bytes and false of THREE contracts those notes carry: a skip specimen cannot answer `get_by_phone` at all; a census specimen's declared refusal pattern is asserted by another item's green test, so putting an unstorable value there makes that assertion depend on where a builder inserts the new gate arm (F18 leg 2); and a MARKER-BEARING stem-divergent note routes its whole record through `_gate_refusal_pattern` and puts the same insertion-point question inside a THIRD item's set equality (F19 leg 5) - which is why the clause now states a property and not only a filename, since the receiver is a fixture that can be renamed while the contracts cannot. The ORDER assertion is new and is the cheapest line in the criterion: absence is not malformation, every other part of the library already draws that line before parsing (`person.py:318-320`), and a build that draws it after refuses the model's own default at every dict door while passing every other leg here (F16). The independence assertion exists because conflating the two predicates is the cheapest wrong build available and every other leg of this criterion would still pass. The exhaustiveness wording is scoped rather than universal because the universal version was FALSE as written - class E is a real input with no cell in the four-cell table - and a criterion that claims a totality its predicate table cannot deliver is the same defect one level up from the thing it is guarding: the no-fall-through classifier is what converts a future sixth shape from a silent mis-file into a failing test, which is the strongest honest form of the claim.
check: test_lid_digits_never_enter_the_phone_index
kind: test
```

```criteria
id: AC-2
desc: Every PARSEABLE JID form has exactly ONE public resolution door and the answer is the person carrying it. Over the same derived SIX-cell table as AC-1, a public `get_by_identifier(Identifier)` and the `resolve`/`resolve_all` cascade both answer, with the expected entity computed from `WhatsAppJID.parse(v).key` plus the fixture's own note-to-value map. Classes A and C resolve to their note through the `phone:` key, unifying with a bare `phones[]` entry for the same number exactly as `tests/test_identity_index.py` already pins - class C is asserted to RESOLVE even though AC-3 refuses to STORE it, which is the reach-versus-storable split made executable, and a build that made resolution strict is RED here. Classes B and E resolve to their note through the `jid:<value>` key the index ALREADY builds (`person.py:330-331`) - today the same query answers None or, worse, the wrong person. E is named alongside B rather than treated as a refusal case, because resolution keys on `parse` and E parses: a build that wired the STORABLE predicate into the resolver makes E (and C) unresolvable and is RED on this leg, which is the same reach-versus-storable split the class-C clause pins from the phone side. Classes D and Ø take the NARROWING arm - None, no exception, and no candidate above the cascade's noise floor; for Ø the query is not constructible as a typed `Identifier` at all (`WhatsAppJID.parse("")` raises), so the leg is stated over the CASCADE with a blank query string and asserts it neither raises nor returns a person who merely has an empty `whatsapp:` field - which 21 of 22 fixture notes do, making a blank query the one input that could match ~the whole corpus if the step compared stored values instead of keys. Stated as a POSITION pin rather than as a behaviour claim, because the behaviour is already true and so could not fail for the reason it names: `resolve_all` bails out on a blank or whitespace-only query BEFORE step 1 runs (`person.py:606-611`, read this round), so what this leg actually guards is that the new `whatsapp_jid` step is inserted BELOW that guard and never above it - the one thing adding a step can break - and the assertion is that the blank-query bail-out still precedes every cascade step including the new one. Three guards - the lid answer is asserted to come from the identifier index and NOT from a phone lookup (a build that resolved lids by re-normalizing digits is RED); the new cascade label is asserted PRESENT in `_RESOLVE_CASCADE_ORDER` (`person.py:145`) and ranked ahead of `phone`, proven by a tie between a lid hit and a fuzzy phone hit resolving to the lid's owner (an unranked label sorts last at `person.py:190-197`, so omitting it is silently wrong); and `README.md:238`'s documented behaviour of looking a phone-bearing JID up through `get_by_phone` still holds, so the fix does not silently retract a published API.
why: The index is already right and nothing public reads it - the gap is a door, not data (F5), and a resolution step is the half of the Intent the mint left implicit. Asserting WHERE the lid answer comes from is what stops the cheap wrong build - re-normalizing a lid's digits in the resolver would green an answer-shaped test while preserving exactly the phone-confusion AC-1 removes. Class C is asserted resolvable because the one real risk of adding a storable predicate is that someone wires it into the resolver too, which would break lookups that work today (F12), and the cascade-label guard is here because it is one line, invisible when wrong, and produces a wrong ANSWER rather than an error.
check: test_whatsapp_jid_resolution_door_over_every_accepted_form
kind: test
```

```criteria
id: AC-3
desc: Every write arm that can introduce a `whatsapp` value refuses a NON-EMPTY value that is not STORABLE - classes C, D and E, so the refused set is defined by the STORABLE predicate over the non-empty values, never by "does not parse" and never over the absence case - in BOTH shapes, with nothing written. The refused population is NON-EMPTY by construction and this is a scoping clause rather than a softening one: class Ø (an absent key, `""`, `None`, whitespace-only) introduces no identifier, is never judged by either predicate, and is ACCEPTED at every arm, which leg (v) pins - `WhatsAppJID.parse` raises on `""` and `None` through the same lines it raises on `"n/a"` with (`identifier.py:271-275`), so a door built to refuse "everything the parser refuses" refuses the model's own default (`models.py:94`) and the corpus's dominant value at every dict door (F16). The arm set is DERIVED from the tree by the existing WI-021 sweep in `tests/derivations.py` (never hand-listed), asserted in scope by EQUALITY, with any arm that cannot introduce the field excluded for a stated structural reason, PLUS one arm the derivation cannot supply - `PersonRepository.save`, which the WI-021 wall deliberately excludes as a rider (`person.py:1162-1163`) and whose gate call runs over a WHOLE-RECORD PROJECTION (`person.py:1190-1191`); the derived set already contains the OTHER whole-record-projection arm, the exported `write_markdown_file(entity=…)` (`writer.py:229-233`, which `BaseRepository.save` delegates into at `base.py:462-465`), and the criterion names it so the two are pinned as ONE class of arm rather than as `save` plus an accident - `whole_record` is not the discriminant, the payload containing the key is (`name_gate.py:289-294`). Per arm, two shapes - a bare scalar `str` (the shape every live caller uses and the shape `_shaped` passes through untouched today - F2) and a list containing one bad member among good ones. Per arm, three conjuncts - (1) REFUSED with a leaf of `LoudFailError` carrying the offending raw value as an ATTRIBUTE and NOT in its message, and carrying its own stable `pattern` value distinct from every `NameValidator` pattern - DECLARED AS A GATE-LOCAL LITERAL and never as a new `NameValidator` Tier-1 branch record, which is a clause about WHERE and not only about distinctness: `_refuse` takes a plain `pattern_key: str` (`name_gate.py:142-174`) so a gate-local literal needs no record anywhere, while a branch record would join WI-016's AC-3 class floor, which is DERIVED by equality from `{record.branch_id for record in TIER1_BRANCHES + COMPANY_TIER1_BRANCHES}` and asserted in both directions (`tests/test_fixture_vault.py:830-838`) - reddening another item's signed criterion whose only discharge is a live-vault count, a scan command, verbatim stdout and a re-taken census digest, i.e. a conductor pass, for a refusal that is not a name judgement at all (F18 leg 4); (2) the target note is byte-identical afterwards, and a target that did not exist is not created; (3) a storable value in the same payload is accepted and stored in the list shape. `"+44 7739 341679"` is named as a REQUIRED class-C member at every arm, because it is the value the item was minted for and the value a parse-only door accepts, and `447700900654@lid.example` is a REQUIRED class-E member at every arm, because it is the value a door that asked "contains `@lid`?" instead of "is the domain in the closed set?" would accept - respelled this round from `447700900456@lid.example.com`, which is the SAME cell but is RED on WI-016's privacy wall if it ever lands in the corpus's reach, since `example.com` is matched by EQUALITY and a subdomain of it is not reserved (F17 leg 2). Every member named in this criterion is a literal of the new test module, not a corpus note; the class-C and class-E values a WRITE arm is handed are constructed in the test, and the corpus's own class-C member (`447700900789@example.com`, moved off the round-trip representative per F17 leg 1) is what the `save` arm below loads from a note. The `save` arm is pinned in BOTH directions over an entity loaded from a note whose STORED value is class C, D or E - (i) `save()` REFUSES with that same pattern and the note is byte-identical, and (ii) the value is STILL PRESENT on the model and in the note afterwards, never silently emptied, which is the assertion an erasing build fails while passing every other leg here. Plus the near-miss control - the same note stays writable through a delta arm for a write that does not re-introduce the field (the delta-not-record rule, `name_gate.py:31-36`), so the remedy is not the disease, and that asymmetry between the whole-record arms and the delta arms is asserted rather than assumed. AND THE APPEND-ONLY CLAUSE, which is about WHERE the `save` arm's disclosure may be written rather than about what the arm does, and is a criterion rather than a build note because the two builds it forbids are green on every other `check:` in this document: `PersonRepository.save`'s docstring is a frozen fixture of WI-024 - all 29 of its Cut-0 `(owner, text)` pairs (`tests/fixtures/identity_endgame/prose_surface_cut0.json:2400-2544`) belong to an owner OUTSIDE `AUTHORIZED_PROSE_OWNERS` (`tests/test_identity_endgame.py:359-373`) and clause (e1) (`:1008-1019`) requires each to survive VERBATIM - so this item's write-back disclosure (F11) and refusal disclosure (F13) land as NEW PARAGRAPHS and never as edits to `person.py:1169-1184`. Three conjuncts, computed through `prose_lines` (`tests/derivations.py:1773`) so the new module names no `ast` of its own (F18 leg 5): (1) every Cut-0 pair owned by `PersonRepository.save` is present in the final surface - which WI-024's own (e1) also asserts, restated HERE because this is the criterion whose build would break it; (2) `AUTHORIZED_PROSE_OWNERS` still has exactly its thirteen declared members and `prose_surface_cut0.json` is byte-identical to its pre-build bytes, which is the conjunct (e1) and (e2) CANNOT supply - a build that authorizes `save` and then deletes one of its 29 lines to satisfy (e2) is green on both of WI-024's clauses and is rejected item 15; and (3) the final surface for that owner carries at least one line that is NOT a Cut-0 member, i.e. the disclosure actually LANDED - the conjunct that fails rejected item 16, the build that buys its green by writing no disclosure at all while `### Examples of done` promises the refusal surface "says so". THE CLEARING LEG, added by the class-Ø fold and the leg that makes the design's own repair promise buildable - over a note whose STORED value is class C, D or E, CLEARING the field SUCCEEDS through the delta arms in both of the package's spellings, `update_frontmatter_field(path, "whatsapp", "")` and `update_fields(person, {"whatsapp": None})`, with the note afterwards carrying the empty collection and the unstorable value GONE because a caller asked for it to go; asserted at every delta arm, not just one, because there is no delete or remove affordance anywhere in the writer (`writer.py:333-337` sets a value) and so this IS the hand-repair path Ruling B leg 2 and AC-5 leg (e) commit to for the D+E residual. THE CLASS-Ø LEG - at every arm in the derived set, in every spelling (absent key, `""`, `None`, whitespace-only, `[]`) and in both shapes, a write carrying class Ø is ACCEPTED, the note is written, and nothing is refused; a build that refuses blank fails here and nowhere else in this set, which is exactly why the leg exists. THE REPORT LEG, which this round adds and which replaces a clause that called the same consequence FREE and was therefore satisfied by silence - `scripts/lint_vault.py` gains a REPORT-ONLY DETECTOR ARM in `check_structural` that fires on a note whose STORED `whatsapp` is NON-EMPTY and not STORABLE (classes C, D and E), emitting its OWN `LintIssue` under its OWN check name, `Severity.ERROR`, category `structural`, with `auto_fixable` left at its `False` default (`scripts/lint_vault.py:96`) so the note never enters `apply_fixes` and `--fix`'s four-bucket delta contract is untouched while it still repairs that note's OTHER issues. Five conjuncts, every one an assertion rather than a consequence: (1) it FIRES on classes C, D and E - over a materialized copy of the frozen corpus this check's issue set is EXACTLY the one non-representative note carrying `447700900789@example.com` (AC-1's WHERE clause), and over the new test module's temp-vault plants it fires on a class-D value and on `447700900654@lid.example`; (2) it is SILENT on class Ø in every spelling (absent key, `""`, `None`, YAML null, `[]`) and on every STORABLE value, so the person round-trip representative's `15555550142@lid` and the corpus's 21 `whatsapp: ""` notes produce no issue of this check at all - the leg that a detector keyed on "does not parse" fails; (3) it judges BOTH stored shapes, a bare scalar `str` and a list with one bad member among good ones, because `lint_vault` reads RAW frontmatter and both shapes exist on disk throughout the migration window - F2's inert-arm trap one tool over; (4) `auto_fixable is False` on every issue it emits, asserted per issue, and this check is NOT a member of `auto_fixable_emitter_checks` - which is also why it owes no repair oracle in `tests/test_lint_vault_fix_rules.py:596-624`, whose table is scoped to that derived set (`:599`, `:621-624`); and (5) the report NEVER travels as `stem_name_divergence`'s `NOT_RENAMEABLE_MARKER` - asserted by that module's own marked-set equality staying green and untouched (`tests/test_stem_name_divergence_detector.py:341-345`, which filters on `issue.check` at `:283-289`), because the build that widens the existing marker instead is green on everything else in this set while putting a false "repair the field" message onto a defect that is a FILENAME (`scripts/lint_vault.py:451-454`) and moving live rows against WI-029's committed "divergent rows the WRITE DOOR refuses (b3): 0 of 8" (`docs/stem-divergence-live-baseline.md:124`). This leg is covered by THIS criterion's `check:`, which is named for all THREE surfaces it now asserts - the write door, the lint tool and the frozen prose frame - for exactly that reason: a write-door test has no reason to assert anything about a lint tool, or about another item's prose fixture, unless the criterion says it does.
why: The Intent's "every writer refuses it at the boundary" is only true if the refusal sits on the surface all writers share - a field type cannot see `update_frontmatter_field(path, "whatsapp", "+44 7739 341679")`, which is legal today (F1, `docs/write-door-bypasses.md:3993`) - and it is only true of the value that MOTIVATED the item if the door asks the storable question, since `WhatsAppJID.parse` accepts that exact string (F12). Both shapes are required because an arm copied from `emails`/`phones` is silent for scalars and every live value is a scalar. `save` must be named explicitly because the derivation that proves no arm routes around the gate excludes it by design, and it is an arm where a value the note already stores is re-introduced and therefore judged (F13) - the build that ships an erasing reader is green on every other criterion in this set; naming `write_markdown_file(entity=…)` alongside it is what keeps the disclosure honest, since the refusal surface is "re-serializing a whole stored person record", not one method (F11's correction). The attribute-not-message rule is the WI-021 refusal contract (`name_gate.py:142-174`) and the way to honour "naming the value" without rendering note bytes in tracebacks (F4). A distinct `pattern` is what keeps a bad JID from being reported and routed as a bad name, and F18 leg 4 is why it is a GATE-LOCAL literal. The APPEND-ONLY clause is this round's material addition and it is a frozen-AC-text gap rather than a build-runner inference: F11's citation of `person.py:1180-1184` as "the same class of disclosure" is ACCURATE and naming it is right, but the paragraph it names is one of 29 lines WI-024 froze for an owner it did not authorize, so the natural reading - extend the paragraph that already carries this disclosure shape - turns `test_strangler_prose_class_is_closed_in_the_package` red with a failure message that names exactly two exits, "name it in the Build Log" (authorize the owner) or "revert it", and BOTH are green on every `check:` this document names while one destroys prose to buy a green (clause (e2) demands an authorized owner LOSE a Cut-0 line, rejected item 15) and the other silently withdraws a promise `### Examples of done` makes (rejected item 16). Only the third build - append, leave all 29 lines byte-identical - is both correct and free, and nothing in this set said so; conjunct (2) is the one that does work WI-024's own wall cannot, because the authorize-and-delete build satisfies (e1) and (e2) together. This is the same "leave the other item's wall alone" instruction this document already gives for WI-016's privacy wall (rejected item 11) and for the census digest (F18 leg 1), now for a third frozen artifact - and it is the PACKAGE file this item edits most, which is why it was priced as ordinary material for seven rounds (F20). The REPORT LEG is this round's material addition and it is a correction to frozen criterion text rather than a build-runner inference, because the sentence it replaces was satisfied by SILENCE: `_gate_refusal_pattern` has exactly ONE call site (`scripts/lint_vault.py:450`), inside the `stem_name_divergence` arm and behind `stem != stored` (`:449`), splicing a MARKER into that issue's message and emitting no issue of its own, while `rg -n 'whatsapp' scripts/lint_vault.py` is 0 matches and WI-029 closed that arm's live population to ZERO (`docs/stem-divergence-live-baseline.md:191`) - so the surface `## Intent`, F13 leg 3, Ruling B leg 2, AC-5 leg (e) and `### Examples of done` all promise did not exist, and THREE self-consistent builds satisfied every `check:` in this set: leave the tool alone (residual silent), widen the existing marker (silent about its own defect and false about the other one, rejected item 14), or add a real detector (the only one that keeps the promise, and the one nothing priced). A clause phrased as a CONSEQUENCE is what let three gate rounds read it as already-true; phrased as five assertions under a check named for the surface, it is buildable exactly one way (F19). The detector is cheap for a measured reason rather than an assumed one - report-only rules are outside the WI-026 oracle table's derived set and a new check name is invisible to the divergence module's set equalities - which is the accounting F9 skipped by pricing the surface off a docstring. The CLEARING and CLASS-Ø legs were the class-Ø fold's material addition and neither is defensive padding: refusing class Ø is a SELF-CONSISTENT build that passes every other leg here and every leg of AC-4 and AC-5, because the entity path never hands the gate a literal `""` (the `[]` default has no member to judge) and no drafted member was blank - so two honest implementers reading the earlier text diverged on whether writing `""` succeeds, and the losing one bricked the only repair channel the residual population has while breaking every producer that clears the field (F16). The legs are stated at EVERY delta arm rather than one because the repair is done by whichever door the repairer happens to hold. One thing this criterion must NOT be allowed to buy, stated here because it is the cheapest way to make the battery green: turning the whole-record arms into refusal surfaces collides with the frozen corpus, which today stores a class-C value on the SOLE person round-trip representative and writes it through that exact arm expecting no refusal (`tests/test_writer.py:421`, `tests/test_fixture_vault.py:753`). The resolution is the corpus edit AC-1's WHERE clause pins - the representative takes a storable value, the class-C member moves to a non-representative note - and NOT re-expecting a refusal in those two tests, which would delete the repo's only assertion that a whole person field set survives the write door (F17 leg 1, rejected item 12).
check: test_whatsapp_refused_at_every_write_arm_reported_by_lint_vault_and_disclosed_append_only
kind: test
```

```criteria
id: AC-4
desc: Both stored shapes load, nothing stored is dropped, exactly one shape is written, and nothing dataclass-shaped reaches YAML. Four legs, over every cell of AC-1's SIX-cell table. (a) TOLERANT READ - a note carrying `whatsapp: "<value>"` and a note carrying `whatsapp: ["<value>"]` both load with NO `SchemaDriftError` and present the same field value; a note with an empty value, a note with the key absent, and a note carrying a BARE valueless `whatsapp:` key (which YAML loads as null) all present the empty collection - that is class Ø on the READ side, and the bare-key spelling is named explicitly because it is the one that does not work today and the one a build will miss: `_normalize_frontmatter` passes `None` through untouched (`parser.py:118-132`) and `whatsapp: str` (`models.py:94`) rejects it, so such a note currently raises `SchemaDriftError` and lands on the load skip surface (`parser.py:203-208`) - INVISIBLE rather than empty - and where this leg names a skip REASON it IMPORTS the constant from `obsidian_schemas/repositories/base.py` rather than typing the string, because the legal homes for a `SKIP_REASONS` literal are pinned to exactly two files by EQUALITY (`tests/test_fixture_vault.py:1392-1395`) and a hand-typed member in the new test module is RED on another item's wall (F18 leg 5) - and the post-migration annotation must coerce null to the empty collection or the clearing spelling's own residue is unreadable, and it is the SAME rule AC-3's CLASS-Ø leg states on the WRITE side, asserted as one rule over one cell rather than as a read-side convenience: the leg is stated so that a build accepting empty on read while refusing it on write fails HERE too (the round-3 and red-team-round-2 contradiction, F16), by round-tripping the empty note through a gated delta write and back. (b) NO SILENT DROP - for every NON-STORABLE member (classes C, D and E) the RAW stored string is still present on the loaded model, asserted by equality against the note's bytes, and the derived typed accessor exposes the PARSEABLE members only (so class D appears in the raw field and not in the typed view, while classes C and E appear in both - they parse, they are merely unstorable, and a build that filtered the typed view on STORABILITY instead of on parseability is RED here) - a reader that filtered unparseable values out of the stored field fails too, and this is the leg that makes AC-3's `save` arm reachable at all. (c) ONE WRITTEN SHAPE - after any gated write that SUCCEEDS and introduces the field the note's bytes carry the LIST form, re-`yaml.safe_load` cleanly, and contain no `!!python/object` tag anywhere; a scalar-carrying note written for an unrelated reason is NOT silently rewritten unless the write introduces the field (delta rule). The population is named rather than left as "any gated write" because the terminal-state partition carves a residual out of it (F21): on a note in the residual R - a stored non-empty value the STORABLE predicate refuses - there IS no succeeding write that introduces the field, since AC-3 refuses it in both shapes, so such a note keeps the SCALAR spelling indefinitely and this leg is SILENT about it rather than violated by it. Asserted both ways over a planted class-D note: an unrelated delta write leaves its scalar `whatsapp` bytes untouched, and a write that re-introduces the field is refused with the bytes unchanged, so no build can read "one written shape" as a licence to convert it. (d) ROUND TRIP - load, save, load again is a fixed point on the field for every member the door accepts, so a second save produces byte-identical frontmatter (the idempotence the gate already requires of itself); for members the door refuses, the fixed point is AC-3's refusal with the bytes unchanged.
why: The vault is shared mutable state, so the reader must accept both shapes for as long as any consumer may be running older code - and an un-migrated note does not merely look odd, it raises `SchemaDriftError` and lands on the load skip surface, invisible to every consumer (F7, F14). Leg (b) is the anti-erasure wall and it is new this round - a literal `list[WhatsAppJID]` annotation cannot hold a value the type refuses, so the natural build drops it, and since `model_to_frontmatter` emits every declared field unconditionally the next `save()` writes the drop back to disk (F13). Asserting the raw string survives is what makes that build RED before it reaches the live vault. Leg (c) exists because `model_to_frontmatter` hands field values straight to `yaml.dump` with the default `Dumper` while the reader is `yaml.safe_load` (F8) - a typed object in `model_fields` would write notes this package cannot read, and "no `!!python/object` in the bytes" is the one assertion that catches it whichever way the implementation goes. Leg (a)'s class-Ø round trip is the cross-check the earlier draft lacked: the read side already said empty means absence and the write side said empty is refused, and because the entity path never constructs a literal `""` for the gate to judge, NOTHING in the suite made the two sides meet - which is how a build could satisfy both sentences at once and still be wrong. Leg (c)'s population is named this round for the same reason one level out: "after ANY gated write the bytes carry the LIST form" is an absolute over a population AC-3 carves a residual out of, and read literally it says a residual note must end up list-shaped - which AC-3 forbids and AC-5 leg (e) guarantees against. The clause does not change what any build does; it stops the absolute from being the second place a builder finds the contradiction F21 removed from the first (the absolutes sweep in `## Exploration Notes` is why it was looked for here at all).
check: test_whatsapp_read_write_shape_and_no_silent_drop
kind: test
```

```criteria
id: AC-5
desc: The migration is a dry run, then a gated write, then a readback - and it proves no identifier moved. Driven in tests against a COPY of the fixture corpus, planted with at least one note per NON-Ø cell of AC-1's table - A, B, C, D and E - plus one note carrying TWO JIDs — a phone-bearing one and an `@lid`, and THEIR LITERALS ARE PINNED HERE like every other required member of this criterion: `447700900987@s.whatsapp.net` (the phone-bearing half, class A) and `15555550163@lid` (the `@lid` half, class B), both UNUSED members of the reserved blocks and both distinct from every other run this document spends. That pinning is the criterion's own business and not a build note: this was the ONE required member with no literal, and the values printed two sentences above are what a test author reaches for — building the note out of `447700900321@s.whatsapp.net` and `15555550142@lid` plants a SECOND entity in the same materialized copy carrying the class-A plant's `phone:447700900321` and the representative's `jid:15555550142@lid`, which is verbatim the mechanism F17 leg 3 already priced: `_index_identifiers` (`person.py:336-366`) does not raise on the collision, nothing in the battery pins the corpus's conflict set, so this criterion's own readback oracle would be computed against an ambiguous index for that note and it would not go red, it would just be wrong. Both new runs are wall-clean by the reserved patterns (`447700900987` matches `^447700900\d{3}$`, `15555550163` matches `^1?\d{3}55501\d{2}$`, `tests/test_fixture_vault.py:308-312`) and unclaimed anywhere in the tree (F18 leg 6). Class Ø needs no plant, the corpus's own 21 `whatsapp: ""` notes being its members and the population the migration converts SHAPE-ONLY. The plants land in the MATERIALIZED COPY and never in `tests/fixtures/vault/` itself, which is what keeps this leg compatible with the corpus's own privacy wall: `447700900321@s.whatsapp.net` (class A) and `notaphone@s.whatsapp.net` (class D) are RED on that wall in the frozen corpus's reach and admissible only outside it (`tests/test_fixture_vault.py:302-319`, reach at `:386-392`; F17 leg 2), so a build that "saves a plant" by promoting either into the frozen corpus turns another item's green invariant red. Class E's plant is `447700900654@lid.example`, respelled from `447700900456@lid.example.com` for the same wall and the same cell. The class-B and class-C members come from the corpus edits AC-1's WHERE clause pins (`15555550142@lid` on the person round-trip representative, `447700900789@example.com` on a non-representative note) and so arrive in the copy for free; every planted digit run is an UNUSED member of a reserved block, which is not decoration - the earlier class-A exemplar reused Thrandell's own phone digits and would have keyed `phone:447700900123` onto two entities in the copy, minting an identifier conflict nothing in the battery pins (F17 leg 3). All of it under the containment wall that proves the module drives only a temp vault (`tests/derivations.py:mutating_drive_vault_args`). Five legs. (a) DRY RUN - reports counts per cell of AC-1's table and leaves the tree byte-identical, asserted by a digest over the materialized tree before and after. (b) WRITE - every write goes through `vault_io` and through the gate (no direct `write_text`), asserted structurally rather than by observing the result. (c) READBACK ORACLE, stated over KEYS, computed over the PARSEABLE values ONLY, and read from the note BYTES - for every note, the MULTISET of `WhatsAppJID.parse(v).key` over the post-migration values equals the multiset computed the same way from the pre-migration value or values, where BOTH multisets range over exactly those values for which `WhatsAppJID.parse` does not raise (classes A, B, C and E). The post-migration values come from a RE-READ: the note's bytes, parsed by a repository or a load that did not exist before the write, never through the migrating process's own repository - which holds a process-local cache and re-indexes the entity it just wrote (`person.py:257-284` plus the save rider), so an oracle computed through it compares the model against itself and is green by construction whatever the bytes say. The oracle NEVER calls `.parse` on a value the parser refuses - the parseable/unparseable split is itself computed by CALLING `parse` and catching `IdentifierError`, never from a hand-kept list, so a class-D value (`"n/a"`, `"ask Kate"`) contributes no key to either side instead of making the check RAISE, and a class-Ø value contributes none because there is no value. A class-D value's guarantee is BYTE-IDENTITY, not key equality - asserted per note against the pre-migration bytes, which is leg (e)'s clause and is where the coverage for D lives. Class Ø's guarantee is the shape conversion and nothing else: `""` becomes `[]`, no key on either side, and the note is otherwise byte-stable. Alongside the key multiset, TWO counts per note are asserted unchanged: the number of PARSEABLE values (so a dropped JID fails) and the TOTAL number of values including the unparseable ones (so a run that quietly deleted the class-D junk it was told to leave alone fails too, even though that value never had a key). A migration that dropped a person's second JID FAILS this while remaining self-consistent, and a migration that invented one fails it too. Keys rather than whole parsed objects, deliberately - leg (d) rewrites a raw spelling on purpose and `.jid` legitimately changes while `.key` must not. (d) CLASS-C REPAIR, counted as its own class, and guarded on PHONE-BEARING - a class-C value is rewritten to its canonical `<digits>@s.whatsapp.net` form and ONLY values whose `WhatsAppJID.parse(v).phone_digits` is non-empty are ever rewritten, asserted key-preserving by leg (c) over exactly those notes. The guard is asserted, not assumed: applying the repair to a phone-less unstorable value (class E) would write `"@s.whatsapp.net"`, which `parse` then refuses, so a build without the guard converts a leave-alone note into one the readback cannot even classify - the test plants a class-E note and asserts it is byte-identical after a repair-enabled run. So the population `PersonRepository.save` will refuse afterwards is class D plus class E, not class D alone. The count of repairs is reported separately from the count of shape-only conversions, and a run invoked with repair disabled leaves class C untouched and reports it - which is Ruling B's alternative arm, and the criterion holds under it with ONE stated difference rather than unchanged, because the earlier claim that it "holds either way Dave rules" was false in a way Dave is entitled to see before he rules: class C is unstorable at the gate, so under the alternative arm class C JOINS the residual R of leg (e) - the notes stay scalar AND unsaveable through the whole-record arms until hand repair - and `|R|` grows by the census's class-C row, the row this document calls the load-bearing one. The test asserts BOTH arms: with repair enabled R is the class-D and class-E plants, with repair disabled R is those plus the class-C note, and the class-C note is byte-identical under the disabled run. (e) COUNTS RECONCILE OVER THE TERMINAL-STATE PARTITION, which is this round's material correction and is a three-part oracle rather than one absolute (F21) - the dry run's per-cell counts, the number of notes the write commits, the repair count and the readback's counts all agree PART FOR PART over the three parts `## Exploration Notes` declares: (1) notes left in the SCALAR shape OUTSIDE the residual R - ZERO; (2) MIGRATED - every class-Ø, class-A, class-B and repaired class-C note, in the list shape; (3) the RESIDUAL R itself - the notes whose stored non-empty value the STORABLE predicate refuses and which therefore CANNOT be converted, since a conversion re-introduces the field and AC-3 refuses it in both shapes, so each one is REPORTED and left BYTE-IDENTICAL and stays scalar BY DESIGN, with R's membership per Ruling B's arm (class D plus class E under the recommended arm, class C plus D plus E under the alternative) and `|R|` equal to the census's corresponding rows. The old wording asserted "zero notes left in the scalar shape" full stop, alongside this same leg's byte-identity guarantee for classes D and E, and this criterion's own mandated class-D and class-E plants make those two conjuncts unsatisfiable on the hermetic suite - so the criterion as previously drafted could not be written green by any build, and the only exits were amending a frozen criterion or silently narrowing the absolute to "the notes the write COMMITS" with nothing licensing the narrowing. A disagreement in ANY part is REPORTED loudly and the run exits non-zero rather than finishing quietly. And one conjunct that keeps the erase-to-convert build red BY INTENT rather than as a side effect of the total-value count: THE RUN NEVER CLEARS A VALUE TO MAKE A NOTE CONVERT - asserted per plant, since emptying the class-D plant would move it out of R into part (2) and reach zero-outside-R trivially by deleting the population this item exists to preserve; clearing is a repair somebody ASKS for through a delta arm and never something the run does. A class-D or class-E value is never dropped and never rewritten - it is reported as needing repair, by the run's own per-cell counts AND, persistently after the run has finished, by the `lint_vault` detector AC-3's REPORT LEG requires, which is a surface this item BUILDS and not one it inherits (F19 retracts the F9 claim that the report path came free) - and its note's `whatsapp` bytes are asserted byte-identical. And the residual's repair path is asserted to exist rather than promised: after the run, a class-D note is cleared through a delta arm and a class-E note is rewritten through one, both SUCCEED (AC-3's CLEARING and CLASS-Ø legs are what make that true), so "reported and left for hand repair" names a door this suite has opened rather than a door the write gate refuses (F16).
why: This is WI-010's stated un-park criterion (`docs/migration-support.md:20-22`) and the first real schema migration in this repo, so the discipline it establishes is reused. The readback oracle is the point - a one-off script over ~1,170 notes with only a success count cannot distinguish "migrated" from "migrated and lost the second JID", which is precisely the data this item exists to start storing. It is stated over `.key` and a count because that is what "no identifier moved" MEANS to every index and resolver in the package, and because leg (d) changes raw spellings by design - an oracle over the parsed dataclass would refuse the repair the design depends on, which is the kind of contradiction that is free to fix now and costs a re-sign later. The PARSEABLE-ONLY scoping of leg (c) is the round's material correction and it is stated INSIDE the criterion on purpose - the earlier wording said the multiset ran over "the pre-migration raw value or values" while this same AC mandates a class-D plant, so an author implementing the sentence literally called `.parse("n/a")` and the oracle RAISED instead of passing or failing: it errored out before either a correct or a wrong build could be judged. The correct exclusion was inferable from other paragraphs, which is exactly the problem - the frozen criterion is what a builder builds against, and every real vault carries some unrepaired junk, so two honest implementers reading the old sentence would have diverged on whether the readback ran at all. The TOTAL-count arm is what stops the scoping from becoming a licence to delete the values it excludes from the key check. Leg (d) is what makes AC-3's `save` refusal affordable rather than a field of unsaveable notes (F13 leg 3), and it is split out as its own count because rewriting stored values is a disclosure Dave is ruling on, not a silent side effect; its phone-bearing guard exists because "class C is always phone-bearing" is only true once class E is carved out of it. Leg (a)'s digest and the containment wall exist because a migration that writes during its dry run has already spent the only cheap chance to be wrong. Two additions this round. The RE-READ clause in leg (c) closes a reading under which the whole oracle is vacuous rather than wrong: the repository re-indexes what it just wrote, so a readback taken through the migrating process is a comparison of a private replica with itself - verify-by-readback means a re-READ or it means nothing, and the wrong reading passes silently on a migration that wrote nothing at all. And leg (e)'s repair-path assertion is what stops "reported and left for hand repair" from being a phrase: the whole class-Ø fold exists because that sentence was, under the earlier AC-3 text, a promise the item's own write door refused (F16), so the criterion now exercises the door instead of naming it. One addition in the round after that, and it is a containment clause rather than a new assertion: the plant list now says the plants land in the MATERIALIZED COPY and names the literals, because two of them are RED on WI-016's privacy wall in the frozen corpus's reach and the shortest way to satisfy "plant a member per cell" is to write them into `tests/fixtures/vault/` - which would turn another item's green invariant red as a side effect of a fixture convenience, and which nothing in THIS criterion would have caught (F17 leg 2). The unused-digits clause is the same shape of trap one level down: `447700900123@s.whatsapp.net` is a reserved-LOOKING literal that is already Thrandell's phone, so it would key one phone identifier onto two entities in the copy and nothing in the battery pins the corpus's conflict set - it would not go red, it would just be wrong (F17 leg 3). One addition in the round after THAT, and it is the same trap reaching its next member rather than a new kind: the two-JID note was the only required plant in this criterion carrying no literal of its own, while every other member had a hard-pinned reserved-block value two sentences away - so the cheapest way to satisfy "a phone-bearing one and an `@lid`" was to reuse the class-A and class-B values already printed, which mints exactly the silent conflict the clause above exists to close, on the ONE note whose whole purpose is proving a person keeps BOTH identifiers across the migration. Pinning `447700900987@s.whatsapp.net` and `15555550163@lid` costs nothing - the fixture is free, the digits are unclaimed - and leaving them unstated invited the one mistake this criterion had already paid a finding to learn. And the addition in the round after THAT is the only one so far that made this criterion UNBUILDABLE rather than wrong in a fixture: leg (e) promised "zero notes left in the scalar shape" while leg (d) and leg (e) both guarantee the class-D and class-E residual is left BYTE-IDENTICAL, and AC-3 refuses a class-D or class-E value at every write arm in both shapes with leg (b) asserting structurally that the migration's own writes go through that gate - so those notes cannot be converted, and this criterion's own required plants guarantee the population is non-zero in the hermetic suite. All four routes out were red: let the gate accept them (red on AC-3, and it retires the item's own refusal), bypass the gate (red on leg (b)), CLEAR the values so the notes convert as class Ø (red on leg (c)'s total-value count, and it is silent data loss on the population the item exists to preserve - rejected item 8's harm arriving through the migration instead of through the reader), or honour byte-identity and report the residual (the correct build, red on the old leg (e)). So the real exits were amending a criterion after Dave's signature or quietly reinterpreting the exit number the live bracket ships against - a clause satisfied by a reader's generosity rather than by construction, the same defect SHAPE F19 closed one artifact over, and worse here because the same absolute was also an exit figure a conductor has to produce in front of Dave. The partition is the fix and it costs nothing: it is still an oracle, still falsifiable, and now backed by the `lint_vault` detector's issue count as an independent second witness to `|R|` - which is what AC-3's REPORT LEG was built to buy. The never-clears conjunct is stated because the erase route was caught only as a side effect of a guard added for a different reason, and a guard that holds by accident is the thing this document declines everywhere else. Leg (d)'s arm-agnostic sentence is corrected in the same move rather than left: it told Dave the criterion was indifferent to his repair ruling while the alternative arm moves N notes - the census's class-C row - into a state where they are BOTH scalar and unsaveable through the whole-record arms, which is exactly the number he should have when he rules.
check: test_whatsapp_migration_dry_run_then_write_then_readback
kind: test
```

### Examples of done

**Given** someone in the vault has two WhatsApp identities — an old phone-JID and the newer `@lid`
WhatsApp now sends — **when** the sync writes both, **then** the note carries both under `whatsapp:`,
and looking up either one returns that person and only that person. **And** the lid is never answered
back as a phone number: asking for a telephone number nobody in the vault holds returns nothing, where
today it can return whoever happens to own a lid with those digits.

**Given** anything tries to write a bare telephone number into `whatsapp:` — `"+44 7739 341679"`,
the Kim Faura value, through HAL9000's PATCH door, through the `new-person` skill, or through a bare
`update_frontmatter_field(path, "whatsapp", …)` that skips the repository entirely — **then** all three
refuse, because a phone number is not a JID; the refusal says which value it refused (on the error, not
in a traceback full of note content); and the note on disk is byte-identical afterwards. **And** asking
the vault about that same number still finds the person — refusing to STORE it never means refusing to
LOOK IT UP.

**Given** a note that already holds a value the door would now refuse — **then** nothing erases it.
The note still loads, the value is still there, the linter names it — under its own check, in its own
line of the report, every time the linter runs and not only if that note's filename happens to be wrong
too — instead of nobody noticing until a hand repair, and the note stays editable for everything else. What refuses until the value is fixed is
re-serializing the WHOLE stored person record — saving the person through the repository, or writing the
entity through `write_markdown_file` — and it says so. **And** when somebody goes to FIX it, that works:
clearing the field, or writing a properly spelled JID over it, succeeds through any of the package's
doors — the door judges the value the write is CARRYING, not the value the note used to hold, so a repair
lands everywhere, while re-saving the record with the bad value still in it keeps refusing until the value
is actually fixed. Emptying `whatsapp:` is always allowed, everywhere, because an empty field claims no identity and
there is nothing to validate — which is also why a person note created from the template, with
`whatsapp:` unset, is written without complaint. "Reported and left for hand repair" has to name a repair
somebody can actually do.

**Given** the live vault on the day the migration runs — **when** it runs the first time, **then** it
PRINTS what it would change and changes nothing; **when** it runs for real, **then** every person is
reachable by exactly the same WhatsApp identities as before — a bare number that becomes a properly
spelled JID still answers to the same number, and nobody loses a second identity — and the readback
reports the vault in three parts and not one number, which is the same TERMINAL-STATE PARTITION
`## Exploration Notes` states and the same one the bracket's exit row carries, said plainly: **zero notes
left in the old shape apart from the ones it could not touch**; the notes it could not touch — the values
that are already wrong and cannot be spelled as a JID — **still there, byte for byte, each one named in the
linter's report**, with that count matching what the census said before the run; and **zero notes whose
identities moved**. It is "zero except what it reported" rather than a flat zero because a value the door
refuses cannot be rewritten into the new shape either — writing it back IS the refused write — so a run
that reached a flat zero could only have done it by DELETING those values, which is the one thing this item
exists to prevent, and the migration never does it: emptying a field is a repair somebody asks for by hand,
never something the run decides. (The identities promise ranges over the values the package can parse — a
`"n/a"` was never reachable before the run and is not after; what it gets instead is the byte-identity
guarantee.) **And** if any of those three numbers disagree, the run says so and exits non-zero rather than
finishing quietly.

## Architectural Review — 2026-09-26

**Recommendation: REVISE — two rulings to settle before the AC frame is frozen**

Cold-start read at `idea` (`state/work-items.json:3161`), round 1 — no prior gate verdict on this
document. Every in-tree citation below was re-read at this worktree's HEAD.

### Trigger check

Fired: establishes a new data model / persistent frontmatter shape (scalar → list across ~1,170 live
person notes); replaces or significantly extends a core system (the WI-021 semantic gate, the WI-125
identifier index, `resolve_all`); touches >3 files in different concerns (`models.py`, `writer.py`,
`name_gate.py`, `repositories/person.py`, `scripts/lint_vault.py`); cross-system (HAL9000 and exocortex
install `-e`); effort > 1 day. Review run.

### Review

**Fit.** Strong, and the load-bearing call is right. F1's conclusion — that the enforcement point is
`gate_write` and the model field is a convenience for typed consumers — is the project's own pattern,
not a re-derivation: `name_gate.py` is THE semantic write gate, `tests/test_name_gate_wall.py` already
proves by derivation that no frontmatter-writing arm routes around it, and the three dict arms
(`writer.py:385`, `writer.py:443`, `base.py:728`) are exactly the class a pydantic field type cannot
see. Verified: all three pass `whole_record=False` and a caller's untyped value. F2's reading of
`_shaped`/`_is_str_list` (`name_gate.py:181-198`) as a POSITIVE predicate under which a bare `str`
falls to pass-through is correct, and so is the consequence that an arm copied from `emails`/`phones`
would be inert for the whole live population.

**Duplication.** Clean. The definition stays at `WhatsAppJID.parse` (`identifier.py:269-281`); rejected
item 2 (a `_whatsapp_index`) is right and consistent with WI-023's deletion of the per-kind email dict;
rejected item 4 (teaching `normalize_phone` about `@lid`) is right — `phone_normalization.py:39-55` is a
stdlib-only leaf whose two consumers want the naive split, and the frame that must stop treating a lid's
digits as a phone (`person.py:266-270`) already has `WhatsAppJID.parse(v).phone_digits` available.
`get_by_identifier` as a public door over the existing `_resolve_identifier` (`person.py:886-909`) is
extension rather than a second authority — that frame already pivots phone-bearing JIDs and reads
`jid:<lid>` from the index, so the public door is mostly `_ensure_loaded` + `_hydrate`.

**Boundaries.** `name_gate` already imports `identifier` (`name_gate.py:60`), so a `WhatsAppJID` import
is leaf → leaf and closes no cycle; the F8 projection belongs in `writer`, which already imports the
gate. F10's Phase-3 answer is correct — the structure is discarded at the WRITE seam (a sync collapsing
two identifiers into one scalar), not reconstructed at read time, so there is no read-time workaround
being built here. Worth stating plainly for the spec: this item makes the shape available but does not
itself populate second JIDs — the producer fix is HAL9000 WI-075 / orchestrator WI-192-193, and AC-5's
readback oracle correctly asserts *no identifier moved* rather than promising to add lids.

**Determinism boundary.** No LLM anywhere in the design; the migration's oracle is computed from
`WhatsAppJID.parse` over the pre-migration raw value rather than from a success count. Right side of the
line.

**Reversibility.** Expand → migrate → (defer contract) is the correct shape and F7's argument for it
holds. One gap, non-blocking: after the live migration, reverting the library is NOT a back-out — a
list-shaped note against pre-WI-032 code fails `model_validate` and `parse_to_model` raises
`SchemaDriftError` (`parser.py:203-208`), making the note invisible rather than oddly shaped, which is
F7's own hazard pointed backwards. The spec should state the back-out explicitly (forward-only with the
tolerant reader kept, or a reverse migration through the same door), the way
`docs/stem-divergence-live-baseline.md` brackets its live run.

**Generalization.** `get_by_identifier(Identifier)` generalizes to every kind rather than minting a
whatsapp-specific getter — the right altitude. The AC-1/AC-2 class table derived by CALLING the parser,
rather than hand-listed, is the right shape and means a third accepted form joins the sweep
automatically.

**Cost & maintenance.** One build plus a conductor-run bracketed live migration; the library delta is
small and the migration is the item. Proportionate. The F6 cost accounting for planting fixture members
(one `CORPUS_DIGEST` regeneration, `tests/fixture_vault.py:44`, plus a census row if the plant declares
a new class) is accurate, and the corpus measurement behind it checks out: 22 of the `type: person`
notes carry `whatsapp:`, 21 empty, one non-empty (`@Thrandell Ibberly.md:7`), zero `@lid`.

**Build vs extend vs integrate.** Extend, everywhere, with no new dependency. Correct.

**Prior art (outside view).** Expand/migrate/contract (parallel change) is the standard industry answer
for evolving a shape across consumers, and this design lands on it rather than around it — no
compensation machinery, no divergence needing a cited execution. One sharpening for the spec: F7 grounds
the "no atomic window" claim on `-e` installs, which invites the counter "then pin a version". The
stronger and packaging-independent reason is that the VAULT is shared mutable state — any consumer
running older code against migrated notes breaks regardless of how the package is installed. The
tolerant reader is required by the shared corpus, not by the install mode.

### Blocking issues

**1. The chosen definition of "well-formed" ACCEPTS this document's own exemplar of a malformed value.
The `## Intent` and `### Examples of done` are therefore not computable from the definition `##
Exploration Notes` declares, and the item as specced does not close the case it was minted for.**

`WhatsAppJID.parse` refuses exactly three things: `None`, empty, and a non-`@lid` string whose
`normalize_phone` output carries fewer than `Phone.MIN_DIGITS == 7` digits (`identifier.py:269-281`).
It does NOT check for a JID suffix at all. So `WhatsAppJID.parse("+44 7739 341679")` — the value line
374 names as the thing all three doors must refuse, and the same value
`docs/write-door-bypasses.md:3994` records as the live bypass — is ACCEPTED, with
`phone_digits == "447739341679"` and `key == "phone:447739341679"`. Its refusal yield over real data is
only digit-less junk (`"n/a"`, `"ask Kate"`). The fixture already demonstrates this and F6 notices the
mechanism without drawing the consequence: `447700900789@example.com` is accepted because the domain is
never read (`@example.com` is not a JID domain either).

AC-3 is internally consistent — it refuses what the parser refuses — so a build-runner ships it GREEN
while `whatsapp: "+44 7739 341679"` still writes cleanly through the PATCH door. That is the
buildable-two-ways condition, and the two ways differ on whether the Kim Faura class is closed.

It also touches Dave's ruling (1), which is why it cannot be settled by the spec-writer: the ruling says
"the field's type IS `WhatsAppJID`, both forms; no second spelling of 'well-formed' anywhere", and a
door that refuses a bare phone number needs either a structural suffix test at the door (a second
spelling, which the ruling forbids) or a narrowing inside `WhatsAppJID.parse` itself (which changes a
shipped type WI-035 and `_resolve_identifier` already depend on). Fold as one of:
(a) keep the wide definition and REWRITE `## Intent` and `### Examples of done` to say plainly that a
bare phone number in `whatsapp:` is accepted and pivots to `phone:<digits>` — stating to Dave that the
motivating defect is retired rather than fixed, so he can accept that or not; or
(b) put the narrowing in `WhatsAppJID.parse` (a strict form, or `parse` gaining the suffix requirement
with today's behaviour kept for the resolution pivot) so there is still ONE definition — and price the
blast radius on `person.py:330-331` and `_resolve_identifier`.
Either way the corpus census's "values `WhatsAppJID.parse` REFUSES" row is measuring the wrong
population until this is settled, so it is upstream of the precondition as well as of the ACs.

**2. What the model holds for an ALREADY-STORED unparseable value is undesigned, and the two candidate
builds ship opposite harms — one of them silent data loss.**

AC-1's refused arm requires such a note to still LOAD; AC-5 requires the migration to leave it untouched
and report it. Neither says what `Person.whatsapp` then HOLDS, and that choice decides the behaviour of
`PersonRepository.save`, which is the one gate call in the package passing `whole_record=True` over
`model_to_frontmatter(entity)` (`person.py:1190-1191`) — a projection that emits EVERY declared field
unconditionally (`writer.py:112-117`). So `save` always re-introduces `whatsapp`:

- if the tolerant reader DROPS the unparseable value (which a strict `list[WhatsAppJID]` field forces,
  and Dave's ruling (2) asks for that field type), the next `save()` silently ERASES it from the note —
  data loss on exactly the population this item exists for, and it also erases the evidence F9's linter
  report path is supposed to surface;
- if it survives as a raw string, `save()` REFUSES, and every person note carrying a stored malformed
  value becomes unsaveable through the repository's own door — `create_stub`, `find_or_create_stub` and
  `_writeback_identifier` all route through it.

F3's "the delta rule is what makes it survivable" is true at the dict arms (`writer.py:385`,
`writer.py:443`, `base.py:728` — all `whole_record=False`, verified) and does not hold at `save`; AC-3's
near-miss control is scoped to "a delta that does not re-introduce the field", so it is not false, it
simply never reaches this arm. F11 gets closest — it names the rider that must grow a `whatsapp`
write-back — but treats it as a disclosure about in-place mutation rather than as a refusal surface.

The WI-021 precedent for `name` shows the estate WILL accept refusal at `save` against a measured small
population, so this is affordable-or-not, not right-or-wrong — but "affordable" has to be defined
against THIS arm before the census can decide it, and the erasure branch must be closed by ruling rather
than by whichever way the build goes. Fold: state in `## Approach` what the model holds for an
unparseable stored value and what `save` does with it; extend AC-3's near-miss control (or AC-4) to pin
the whole-record entity arm in both directions — no silent erasure, and the refusal outcome asserted
rather than implied. Note this may be the point at which `whatsapp: list[WhatsAppJID]` as a literal
field type cannot survive the tolerant reader, which is a ruling-(2)-touching consequence and belongs in
front of Dave before the signature, not in front of the build-runner after it.

### Suggested adjustments (non-blocking — fold if cheap, no round owed for them)

- **Back-out.** State the migrated corpus's back-out in `## Approach` (see Reversibility above). A
  library revert is not one.
- **Consumer audit scope.** `docs/wi-032-consumer-audit.md`'s question list asks for sites classified
  scalar-assuming or shape-agnostic. AC-4(a) asserts the loaded field presents "the identical typed
  value", which means consumers reading `person.whatsapp` would receive `WhatsAppJID` objects — a
  shape-agnostic site (`list(person.whatsapp)`) survives the cardinality flip and still breaks on typed
  elements. The audit should classify that third axis too; the existing `grounds:` line already covers
  it, so this needs no fence replacement.
- **Cascade label.** The new `whatsapp_jid` step needs an entry in `_RESOLVE_CASCADE_ORDER` or its
  candidates rank LAST among equal-confidence ties (`person.py:190-197`). One line, easy to miss.
- The scope recommendation in `### The one OPEN RULING for Dave` — ship the `whatsapp` axis whole and
  mint the `emails`/`phones`/`linkedin` element-typing separately — is architecturally right and I
  endorse it. `slack` genuinely cannot be typed here (`person.py:305-312` records the missing workspace
  as an explicit UNBLOCK over a 2-note population), and strict element types on `emails[]` would fight
  `lint_vault`'s ability to load the notes it exists to repair. Carry it to Dave at the signature as the
  document already plans, alongside the two rulings above.

```verdict
gate: architect
verdict: REVISE
date: 2026-09-26
model: claude-opus-5
note: `WhatsAppJID.parse` accepts "+44 7739 341679" — the doc's own exemplar of the value all three doors must refuse — so AC-3 ships green without closing the minted defect; and what the model holds for an already-stored unparseable value is undesigned, forking `save` between silent erasure and a class of unsaveable notes.
targets: AC-3, AC-4, #intent, #approach, #exploration-notes, #write-targets
prior: none
basis: original
findings: 2/5
```

## Architectural Review — 2026-09-26 (round 2)

**Recommendation: PROMOTE to architected**

Round 2, re-read at this worktree's HEAD (`c93006a` plus the seeded uncommitted delta). Both round-1
blocking findings are CLOSED, and closed at the right altitude — not papered over with an AC. Every
citation below was re-read in the code this round rather than carried from round 1.

### Trigger check

Fired for the same reasons round 1 recorded: a new persistent frontmatter shape across ~1,170 live
person notes; significant extension of three core systems (the WI-021 gate, the WI-125 identifier
index, `resolve_all`); >3 files in different concerns; cross-system consumers; effort > 1 day.

### The round-1 findings, re-read against this tree

**Finding 1 — the definition accepted the doc's own exemplar of a malformed value. CLOSED, and the
fold is better than the remedies I offered.** I gave two arms (keep the wide definition and rewrite
the Intent, or narrow `parse`). The document took a third: TWO predicates on ONE type in ONE module
(F12, `## Approach` step (0)). Re-verified the fact it rests on — `identifier.py:276-281` tests for
the `@lid` substring, then for `normalize_phone(s)` yielding ≥ `Phone.MIN_DIGITS` digits, and tests
for a JID suffix nowhere; `phone_normalization.py:52` splits at the `@`. So
`WhatsAppJID.parse("+44 7739 341679")` still succeeds, and the STORABLE predicate is what refuses it.
Re-verified the blast-radius argument that makes `parse` the wrong place to narrow: `person.py:829-834`
(the WI-035 pivot) and `person.py:902-906` (`_resolve_identifier`) both want maximum reach because
their job is to FIND a person, and `identifier.py` is a leaf, so a suffix regex in `name_gate.py`
would have been the second spelling ruling (1) forbids while a derived property on the same frozen
dataclass is not. This is the correct resolution of my finding and of Dave's ruling (1) simultaneously,
and handing him the fact-level disagreement as Ruling A rather than picking a side inside a document
he is about to sign is the right move on a rulings boundary.

The independence claim the fold rests on also holds: `notaphone@s.whatsapp.net` carries a JID domain
and still fails `parse`, pinned today at `tests/test_identifier.py:140`. So the two predicates are
genuinely orthogonal and AC-1's independence leg is not decorative.

**Finding 2 — what the model holds for an already-stored unparseable value. CLOSED.** F13 names the
fork, and re-verification confirms every fact under it: `person.py:1190-1191` is the package's only
`whole_record=True` gate call and its rider writes back `emails`/`phones`/`aliases` only
(`person.py:1192-1194`); `writer.py:112-117` emits EVERY declared field unconditionally, so `whatsapp`
is re-introduced on every save; and all three delta arms are `whole_record=False` — `writer.py:385-387`,
`writer.py:443-445`, `base.py:728-730` — so the delta rule (`name_gate.py:31-36`) covers them and does
not reach `save`. The chosen answer (stored field `List[str]`, typed access DERIVED) is right for a
reason beyond avoiding erasure: it is the only shape under which nothing dataclass-shaped ever enters
`model_fields`, which dissolves F8's `!!python/object` hazard by construction rather than by a
projection step someone must remember — and deleting that step from scope (rejected item 9) is a real
simplification, not a dodge. AC-4 leg (b) and AC-3's two-directional `save` arm pin both wrong builds,
which is what my finding asked for.

F14 is a genuine improvement on my own Reversibility note rather than a restatement of it: grounding
the tolerant reader on the SHARED VAULT instead of on `-e` installs is the packaging-independent form,
and pointing the hazard backwards is the half I missed. Re-verified: `models.py:32-33` allows extra
fields but does not loosen declared ones, so a list against a pre-WI-032 `whatsapp: str`
(`models.py:94`) fails `model_validate`, and `parser.py:186-192` makes a `type: person` note OWNED, so
`parser.py:203-208` raises `SchemaDriftError` — invisible, not oddly shaped. The forward-only position
with the exact-reverse window named while no note yet carries a second JID is the correct statement.

F15 landed too, and it is the cheapest-to-lose one: `_RESOLVE_CASCADE_ORDER` (`person.py:145`) with
`rank`'s unknown-label fallback to `len(...)` (`person.py:190-197`) means an unregistered
`whatsapp_jid` label sorts LAST among equal-confidence ties, which produces a wrong ANSWER rather than
an error. AC-2's tie guard pins it.

### Review (this round's dimensions, where the fold changed them)

**Fit.** Unchanged and still strong. Re-verified the load-bearing shape facts: `_CONTAINER_KEYS`
excludes `whatsapp` (`name_gate.py:84`); `_is_str_list`/`_shaped` are POSITIVE predicates under which
a bare `str` falls to pass-through (`name_gate.py:181-198`), so F2's "an arm copied from
`emails`/`phones` would be inert for the entire live population" is exactly right; `_refuse` admits no
note-derived value into the exception (`name_gate.py:142-174`), so F4's attribute-not-message route is
the only one available. One fit fact worth naming because the design depends on it and no finding says
it out loud: the gate's output key set is exactly its input's (`name_gate.py:48-52`, and it is forced
by `update_fields` merging by key REPLACEMENT), so a `whatsapp` arm that normalizes a scalar into the
list form stays inside that contract — the arm is legal, not merely convenient.

**Duplication.** Still clean, and the fold made it cleaner by deleting a step rather than adding one
(rejected item 9). Two predicates in twelve lines of one module is one authority; re-verified that
`_resolve_identifier` (`person.py:886-909`) already reads `jid:<lid>` and already pivots phone-bearing
JIDs, so `get_by_identifier` is a public door over an existing frame, not a second index — consistent
with WI-023's deletion of the per-kind email dict.

**Boundaries.** Unchanged. `_index_entity` (`person.py:266-270`) and `_remove_entity_from_indexes`
(`person.py:412-416`) are exact mirrors today, and AC-1's inverse-over-the-same-table assertion is the
right way to keep them mirrors. Note the narrowing is real and is disclosed: a value with 1–6 digits
gets a `_phone_index` entry TODAY and will stop getting one, which AC-1 pins as class D's declared
marker rather than leaving to inference.

**Determinism boundary.** No LLM in the design; the migration's oracle is computed from
`WhatsAppJID.parse` over the pre-migration raw value rather than from a success count. Right side of
the line, and AC-5 leg (c) is the structural form of it.

**Reversibility.** Now stated (F14 + the Back-out paragraph in `## Approach`). Closed.

**Generalization.** `get_by_identifier(Identifier)` over every kind, and a class table derived by
CALLING the type rather than hand-listed, are both the right altitude. The one place generalization is
now under-specified is the STORABLE set's membership — note 1 below.

**Cost & maintenance.** Proportionate; the fold made the library delta smaller (one derived property,
no projection step) while leaving the migration as the item. F6's amendment reduces the fixture plant
from three classes to two, which is a real cost reduction — subject to note 1.

**Build vs extend vs integrate.** Extend, everywhere, no new dependency.

**Prior art (outside view).** Expand → migrate → (defer contract) is the standard parallel-change
answer and this design lands ON it, not around it: no compensation machinery, so no cited execution is
owed. Liberal-in-what-you-accept / conservative-in-what-you-store is likewise the standard identifier
answer (Postel's split, and the same split every address library draws between a resolver and a
validator), so the two-predicate shape is the outside view rather than a local invention. Ruling C's
deferral is a scope split, not a capability worked around, so the blocking deferral clause does not
fire — but see note 4.

### Notes (non-blocking — none of these is worth a round, all are cheap before the signature)

1. **The STORABLE predicate's extension is declared twice with different reach, and the looser reading
   contradicts F6's amendment.** `## Exploration Notes` declares the set as the closed
   `{"s.whatsapp.net", "lid"}` in one sentence and then says "whether the set is an allowlist or a bare
   'has a non-empty suffix' test is the spec-writer's" in the next. Those two are not the same
   predicate: under the bare-suffix reading Thrandell's `447700900789@example.com`
   (`tests/fixtures/vault/@Thrandell Ibberly.md:7`) is STORABLE and therefore class A, which is exactly
   the opposite of what F6's amendment concludes — and F6's amendment is what reduces the fixture plant
   to B and D and what tells the census which row to count. Recommend deleting the licence and keeping
   the closed set as the definition; the item's own guard would catch the divergence anyway (AC-1
   asserts every class non-empty, so a loose spelling would empty class C and go RED), which is why
   this is a note rather than a finding — but it is cheaper to close the sentence than to discover it,
   and it is upstream of the census row `docs/wi-032-whatsapp-corpus-census.md` is asked to measure.
   Note the motivating value is safe either way: `"+44 7739 341679"` has no `@` at all, so
   `jid_domain` is `""` under both readings.
2. **One residual cell the four-class table does not have, and the "class C is always phone-bearing"
   claim is what it dents.** `parse` accepts the `@lid` SUBSTRING, not an `@lid` suffix
   (`identifier.py:276`), so `123@lid.example.com` parses with `phone_digits == ""` and — under the
   closed set — is NOT storable: a class-C member with no phone. That breaks the "by construction"
   claim in F13 leg 3 and makes AC-5 leg (d)'s repair produce `"@s.whatsapp.net"`, which `parse` then
   refuses, so leg (c)'s oracle RAISES rather than fails. The failure is loud and the population is
   almost certainly empty, which is why this is non-blocking — but the table should either carry the
   cell or state it empty-by-refusal, and leg (d) should repair only members whose `phone_digits` is
   non-empty. One sentence each.
3. **AC-5 leg (c)'s oracle is stated over `WhatsAppJID.parse(v).key` for every value, and class D does
   not parse.** As written a class-D note makes the oracle raise, not fail. State the multiset over the
   PARSEABLE values with the byte-identical clause covering the rest, so the test author is not the one
   inventing that rule after the frame is frozen.
4. **LESSONS #27 — a migration's acceptance is the real corpus, not a planted copy of the fixture
   corpus.** AC-5 is hermetic by necessity and correctly so, and the census precondition is the
   audit-before-patching half. What the document does not yet state as a SHIP CONDITION is the
   "point it at production and read what it says" pass: `### Effort` and the Back-out paragraph both
   name the bracketed live run, but as effort rather than as the condition the item ships against.
   WI-029's shape is the precedent worth copying exactly — entry numbers, Dave's go, exit numbers in
   `docs/stem-divergence-live-baseline.md` §5. Recommend the spec-writer state it that way, because a
   migration whose only acceptance is a corpus it was written against is a specimen in a jar.
5. **Disclose the producer-side break in `## Approach`, not only inside a precondition's `why:`.**
   Consumers that today write a bare number into `whatsapp:` will start being REFUSED. That is the
   Intent working as designed, but it is a consumer-visible behaviour change of the same class Dave
   required disclosed on WI-029 (the PATCH-onto-occupied-note change), and it currently lives only in
   `docs/wi-032-consumer-audit.md`'s question list. One sentence in `## Approach`, and it belongs in
   front of Dave at the signature.
6. **Ruling C's follow-on must be MINTED, not recommended.** "The `emails`/`phones`/`linkedin`
   element-typing is minted as its own item" is the right call and I endorse it again — with the Ruling
   B update, the follow-on's framing is "derived typed accessors alongside the stored `List[str]`", not
   "annotate `emails: list[Email]`", which is a genuinely better mint. Mint it when Dave rules, in the
   same move, so the deferral does not evaporate into a queue nobody re-reads.

### On the three OPEN RULINGS, and why three is not a convergence signal here

The role's cap is on OPEN questions the GATE raises; I raise none this round. All three rulings carry a
recommendation, the cost of each alternative arm, and the one-line edit that implements the other
answer — and two of the three exist because my own round-1 findings correctly refused to be settled
inside a document Dave is about to sign. What is outstanding is AUTHORIZATION on two facts (the type is
wider than his ruling (1) describes it; the literal annotation his ruling (2) names cannot hold a value
the door refuses without erasing it) plus one scope call. That is a signature boundary, not unconverged
exploration, and the ACs are drafted to one arm each with the edit priced. The ordering the document
states is the right one and should be held: settle A and B, then measure the census, then freeze the
frame.

```verdict
gate: architect
verdict: PROMOTE
date: 2026-09-26
model: claude-opus-5
note: Both round-1 findings are closed at the right altitude — two predicates on one type (reach vs storable, F12) and a `List[str]` stored field with derived typed access (F13), which also deletes the writer projection from scope; every citation re-verified in code, and what remains is Dave's authorization on Rulings A/B/C plus six cheap pre-signature notes, not unconverged approach.
```

## Architectural Review — 2026-09-26 (round 3)

**Recommendation: REVISE — one blocking finding, and the fold is one clause plus one AC leg**

Round 3, re-read at this worktree's HEAD (`c93006a` plus the seeded uncommitted delta). Every
citation below was read in the code this round. The prior rounds' findings all HELD — what this
round found sits in ORIGINAL text that three prior gate rounds, mine included, walked past: which
values class D contains.

### Trigger check

Fired for the reasons rounds 1 and 2 recorded: a new persistent frontmatter shape across ~1,170
live person notes; significant extension of three core systems (the WI-021 gate, the WI-125
identifier index, `resolve_all`); >3 files in different concerns; cross-system consumers; effort
> 1 day.

### The prior findings, re-read against this tree

**Round-1 findings 1 and 2 — still CLOSED.** Re-verified the facts under F12 and F13 rather than
carrying round 2's reads: `identifier.py:276-281` tests the `@lid` SUBSTRING and then
`normalize_phone(s)` ≥ `Phone.MIN_DIGITS == 7`, and tests for a JID suffix nowhere;
`person.py:1190-1194` is the save rider and writes back `emails`/`phones`/`aliases` only;
`writer.py:112-117` emits every declared field unconditionally.

**The AC red-team's AC-5 leg (c) finding and its AC-1 minor — both folded, and the fold is
correct at the level of fact.** Class E is a real cell, not a defensive invention: `parse`'s
`@lid` branch runs BEFORE the digit test (`identifier.py:276-281`) and `normalize_phone` splits at
the FIRST `@` (`phone_normalization.py:52`), so `447700900456@lid.example.com` returns
`phone_digits == ""` with `key == "jid:447700900456@lid.example.com"` while its domain after the
last `@` is `lid.example.com` — outside the closed set. I also checked the five cells are now an
actual partition of `parse`'s outcome space (raises → D; `@lid` present → B or E by the domain
test; otherwise → A or C by the domain test, and `domain == "lid"` cannot arise without the
substring), so AC-1's no-fall-through classifier has nothing to raise on. The repair guard is
genuinely load-bearing for the reason F13 leg 3 gives: `normalize_phone("@s.whatsapp.net")` is
`""`, so an unguarded repair of a phone-less value writes a string `parse` then refuses. And
"class C is always phone-bearing" is now true by the class definition rather than by an argument.

### Blocking issue

**1. The EMPTY value is class D, so AC-3 refuses it — which bricks the only door the D+E residual
can be repaired through, and contradicts AC-4(a) in the same frame.**

The class table lists `""` and `None` as class-D exemplars (`| **D** | does not parse |`), AC-3
refuses "classes C, D and E" at every write arm in both shapes, and AC-4(a) says a note with an
empty value and a note with the key absent both present the empty collection. So the READ side
treats empty as absence and the WRITE side refuses it, and nothing in the document reconciles
them. The estate's own convention is the read side's: `_project_identifiers`'s `add()` returns on a
None or blank raw BEFORE parsing (`person.py:318-320`) — absence is not malformation — and
`whatsapp: ""` is the model default (`models.py:94`), the person template's value, 21 of the 22
`whatsapp`-carrying fixture notes, and the declared person oracle in `tests/fixture_vault.py:94`.

The failure scenario is the residual population this design deliberately creates. F13 leg 3 and
AC-5 leg (e) leave classes D and E "reported and left for hand repair". For a class-D value there
is no JID to write — `"n/a"`, `"ask Kate"` carry no digits and no domain — so the only repair is
CLEARING the field, and the package's clearing doors are `update_frontmatter_field(path,
"whatsapp", "")` and `update_fields(person, {"whatsapp": None})`; there is no delete affordance at
all (`writer.py:333-337` sets a field, never removes one). Both hand the gate a class-D value, so
AC-3 as drafted refuses the repair of exactly the population Ruling B leg 2 leaves unrepaired,
while the no-erasure rule forbids the library from emptying it. That is the remedy-is-the-disease
outcome at the arms the delta rule exists to keep open — the same shape as `name_gate.py:31-36`'s
own scar, arriving through a different field.

A second consequence prices differently and reaches further: any producer writing the template's
empty value through a dict door — HAL9000's PATCH clearing the field, a template-shaped create —
starts being REFUSED on the most common value in the field. So the consumer-visible break is
against ~the whole corpus rather than against the C+D+E population the census is measuring, which
changes what Ruling B leg 2 costs.

What hides it is that the entity path is safe: with the stored field `List[str]` and a tolerant
reader the model default is `[]`, `model_to_frontmatter` emits `[]`, and an empty list has no
members for the arm to judge — so `save()` and every entity-shaped write pass. Only the dict arms
ever see a literal `""`, and no in-tree write puts `whatsapp: ""` through a gated door today (the
fixture notes are byte-copied, and `rg -n 'whatsapp' scripts/lint_vault.py` is still 0 matches), so
a build that refuses it ships GREEN with the whole suite passing.

**Fold.** (i) In `## Exploration Notes`, alongside the two predicates, state that an ABSENT, empty
or `None` value introduces NO identifier and is never refused — the arm's population is the
NON-EMPTY values — and correct class D's exemplars to the non-empty unparseables (`"n/a"`,
`"notaphone@s.whatsapp.net"`). (ii) Say it in `## Approach` step (2), where the arm is described.
(iii) Pin it: AC-3 gains a leg asserting that CLEARING the field through a delta arm SUCCEEDS on a
note whose stored value is class C, D or E, because that is the hand-repair path the residual
depends on and it is the leg a refusing build fails. AC-4(a)'s empty/absent clause then stops
contradicting AC-3. This touches neither Ruling A nor Ruling B: it narrows the refused population
to what Dave's ruling (1) already describes rather than widening it.

### Non-blocking findings (fold if cheap; no round is owed for them)

**2. `save` is not the package's only `whole_record=True` gate call, and `whole_record` is not the
discriminant anyway.** `writer.py:229-233` — the ENTITY arm of the exported `write_markdown_file` —
is a second one, and it is the arm `BaseRepository.save` delegates into (`base.py:462-465`), which
is why one `PersonRepository.save` gates TWICE by design (`name_gate.py:296-299`,
`person.py:1186-1188`). F13's substance survives whole, but its handle is wrong: what makes a
stored value judged is that the PAYLOAD CONTAINS the key, and `gate_write`'s own docstring says so
— the flag "makes the dict-shaped arms `False` even when their payload happens to be the whole
note" (`name_gate.py:289-294`), and all it enables is the two cross-field migrations
(`name_gate.py:385`). Two corrections follow. The parenthetical fact in F13 and in AC-3's desc;
and the disclosure — `### Examples of done`'s "saving the whole person through the repository is
the one thing that refuses" understates the surface, because a direct `write_markdown_file(path,
entity=person)` refuses too and that door is exported (`__init__.py:119`), as does any consumer
re-serializing a whole stored person record through the `frontmatter=` arm. AC-3's COVERAGE is
unaffected: `frontmatter_write_arms` (`tests/derivations.py:979-1010`) sweeps the writer entity
arm, so the derived-by-equality set already contains it. Worth one line in
`docs/wi-032-consumer-audit.md`'s question list — does any consumer write a Person entity through
`save` or `write_markdown_file(entity=…)`, or re-serialize a whole stored person record?

**3. AC-5 leg (c) does not say where the post-migration values come from, and the wrong reading is
vacuous rather than failing.** `PersonRepository` holds a process-local cache and re-indexes the
entity it just wrote (`person.py:257-284` plus the save rider), so a "readback" computed through
the migrating process's own repository compares the model against itself and is green by
construction — LESSONS #49's private-stale-replica shape, and the reason verify-by-readback means a
re-READ. Leg (e)'s byte assertions imply disk for classes D and E; the key multiset for A, B and C
is unpinned. One clause: the post-migration values are re-parsed from the note BYTES by a load that
did not exist before the write.

**4. One touch-list addition.** `tests/fixture_vault.py:94` hand-transcribes `models.py`'s person
defaults, `whatsapp: ""` among them. The default becomes `[]`, so the digest-frozen corpus's
declared oracle moves with the field — cheap, but it is machinery rather than a plant and it is not
on `### Effort`'s expected touch list.

**Carried, not re-raised.** Round-2 notes 4 (the live run stated as a SHIP CONDITION, WI-029's
bracketed shape, not as effort) and 5 (the producer-side refusal disclosed in `## Approach`, not
only inside a precondition's `why:`) still read as unfolded. They were non-blocking then and are
non-blocking now; I re-state them so the pre-signature pass has them in one place. Rulings A, B and
C are unchanged by everything above, and the ordering the document states — settle A and B, measure
the census, then freeze the frame — is still the right one.

```verdict
gate: architect
verdict: REVISE
date: 2026-09-26
model: claude-opus-5
note: The class table makes `""`/`None` class D and AC-3 refuses class D at every arm, so the only clearing doors the package has (`update_frontmatter_field`/`update_fields`; there is no delete affordance) refuse the hand repair of the very class-D/E residual the design leaves for hand repair — while AC-4(a) treats empty as absence, so the item is buildable two ways and the refusing build ships green because the entity path never sees a literal `""`.
targets: AC-1, AC-3, AC-4, AC-5, #approach
prior: held
basis: original
findings: 1/4
```

## Architectural Review — 2026-09-26 (round 4)

**Recommendation: REVISE — two blocking findings, both on the fixture-plant plan, both with a
precedent in this repo for the fold**

Round 4, re-read at this worktree's HEAD (`c93006a` plus the seeded uncommitted delta). Every
citation below was read in the code or the doc this round. **The prior rounds' findings all HELD**,
including round 3's and the AC red-team's convergent class-Ø finding, which is closed at the right
altitude. What this round found is in the material the FOLDS added: the reclassification of
`@Thrandell Ibberly.md` as the corpus's free class-C member (F6's first amendment) and the plant
list that fell out of it (F6's second) were never checked against the frozen corpus's own two
contracts — its ROUND-TRIP REPRESENTATIVE and its PRIVACY WALL. Neither touches Ruling A or Ruling
B, and I raise no new question for Dave; both are corrections to this document, and both must land
before the AC frame freezes because the frozen criterion text asserts the answers.

### Trigger check

Fired for the reasons rounds 1–3 recorded: a new persistent frontmatter shape across ~1,170 live
person notes; significant extension of three core systems (the WI-021 gate, the WI-125 identifier
index, `resolve_all`); >3 files in different concerns; cross-system consumers; effort > 1 day.

### The prior findings, re-read against this tree

**Round-1 findings 1 and 2 — still CLOSED.** Re-verified rather than carried: `identifier.py:276-281`
tests the `@lid` SUBSTRING then `normalize_phone(s)` ≥ `Phone.MIN_DIGITS == 7` and tests for a JID
suffix nowhere, so `WhatsAppJID.parse("+44 7739 341679")` still succeeds and only the STORABLE
predicate refuses it; `phone_normalization.py:52` splits at the FIRST `@`; `person.py:1190-1194` is
the save rider and writes back `emails`/`phones`/`aliases` only; `writer.py:112-117` emits every
declared field unconditionally.

**Round-3's blocking finding (class Ø) — CLOSED, and the fold is complete rather than cosmetic.**
Every leg of it is now asserted rather than described: the ABSENCE bullet ahead of both predicates in
`## Exploration Notes`, class Ø as a CELL, AC-1's ORDER assertion, AC-3's CLEARING and CLASS-Ø legs
at every arm, AC-4(a)'s round trip meeting the write side, and F16 carrying the derivation. The
mechanism re-read this round: `identifier.py:271-275` has no blank branch — and the package's own
existing test already parametrizes `None` and `""` alongside `"notaphone@s.whatsapp.net"`
(`tests/test_identifier.py:140`), which is the sharpest form of F16's point; `person.py:318-320`'s
`add()` returns on a `None`-or-blank raw before parsing; `name_gate.py:399`'s `elif entry and …`
draws the same line by falsiness; `writer.py:333-337` sets a field and there is no delete affordance
anywhere in the writer, so CLEARING really is the residual's only repair door; `models.py:94` and
`tests/fixture_vault.py:94` are the default and the transcribed oracle the refusing build would have
broken.

**Round-3's three non-blocking notes and round-2's notes 4 and 5 — all folded.** Verified the
corrections are true, not just present: `writer.py:229-233` is a second `whole_record=True` gate call
and `base.py:462-465` is the delegation, so `BaseRepository.save` reaches it and
`name_gate.py:289-294`'s docstring confirms the flag is not the discriminant — the payload containing
the key is; `frontmatter_write_arms` (`tests/derivations.py:979-1010`) derives arms off
`write_frontmatter`'s payload binding, so the writer entity arm is in the derived-by-equality set
exactly as F11's correction claims. AC-5's RE-READ clause, the live run as a SHIP CONDITION, the
producer-side disclosure in `## Approach`, and Ruling C's mint-on-ruling are all in the text.

### Review (only where this round's findings bite)

**Fit, Duplication, Boundaries, Determinism, Reversibility, Generalization, Build-vs-extend, Prior
art.** Unchanged from round 2's reads, all re-spot-checked: `_CONTAINER_KEYS` still excludes
`whatsapp` (`name_gate.py:84`), `_is_str_list`/`_shaped` are still positive predicates under which a
bare `str` falls to pass-through (`name_gate.py:181-198`), `_refuse` still admits no note-derived
value (`name_gate.py:142-174`), `_resolve_identifier` still reads `jid:<lid>` and pivots
phone-bearing JIDs (`person.py:902-908`), `_index_entity`/`_remove_entity_from_indexes` are still
exact mirrors (`person.py:266-270`, `:412-416`), and `resolve_all`'s cascade still has no
`whatsapp_jid` step (`person.py:628-651`). Liberal-for-reach / conservative-for-storage remains the
outside view rather than a local invention, so no cited execution is owed.

**Cost & maintenance — this is the dimension that moved.** F6 prices the fixture plant as "one
`CORPUS_DIGEST` regeneration … and, if the plant declares a new class, a census row", and calls the
plant-versus-inline-note choice the spec-writer's. Both findings below are that price being wrong:
the frozen corpus is not a blank page with a digest on it, it is a corpus with two live contracts,
and one of the five cells cannot be planted in it at all as the class table spells it.

### Blocking issues

**1. The note the folds appointed as the free class-C member is the corpus's ONE person round-trip
representative, and two in-tree tests write it through the gated whole-record arm asserting NO
refusal. After AC-3 both go RED, and the note is not substitutable.**

`@Thrandell Ibberly.md` carries `roundtrip_representative=True` (`tests/fixture_vault.py:219-233`),
`_representative` asserts there is EXACTLY ONE per type (`tests/test_fixture_vault.py:689-695`), and
the flag's declared contract is that those notes "declare their model's whole field set, which is
what makes AC-2's round trip total for them" (`tests/fixture_vault.py:13-14`). Two tests then write
that entity through the door:

- `tests/test_writer.py:404-428` — `test_corpus_note_round_trips_through_the_write_door` parses the
  person representative and calls `write_markdown_file(out / name, entity=doc.entity, …)` at `:421`,
  then asserts every declared field survives, `whatsapp` among them (`:424-427`);
- `tests/test_fixture_vault.py:705-761` — the AC-2 type-registry sweep does the same for every
  representative at `:753`, and at `:726-732` asserts the person representative is "GATE-CLEAN by the
  DOOR's own predicate".

That arm is `write_markdown_file(entity=…)` with `whole_record=True` (`writer.py:229-233`) — the
second whole-record-projection arm F11's own correction added — so under AC-3 a class-C stored value
is REFUSED there and both tests raise `NameGateRefusal` instead of comparing a field. F6 does name a
consequence here, but it names the wrong arm and understates the shape: it says "any existing test
that round-trips a fixture person through `save` needs re-reading", when the colliding arm is the
exported writer entity arm, the tests are the two above rather than a set to go looking for, and the
note is the corpus's unique representative rather than one specimen among several. Meanwhile F6
instructs the opposite of what the collision requires — "The plant must KEEP Thrandell's value rather
than tidy it — it is the discriminating member" — and AC-1's frozen `why:` restates it ("the corpus
supplies Ø (21 notes) and C (`@Thrandell Ibberly.md:7`) for free"). One note cannot be both the
gate-clean total round trip and the door-refused class-C specimen.

The reason this is blocking rather than a build-time surprise is the branch a builder reaches for
when the battery goes red: "the round trip now legitimately refuses, so change the test to expect a
refusal." That build is self-consistent and green, and it silently deletes the only assertion in the
repo that a whole person field set survives the write door — an existing invariant, traded away
inside a build whose AC text told the builder that C was free.

**The fold, and this corpus has already solved this exact collision once.**
`docs/vault-fixtures.md:5938-5943` (WI-016's own build log, deviation 3) records the identical shape
— a representative must declare every field, a wall forbids the realistic value for one of them —
and resolves it IN THE CORPUS rather than in either rule: "the four representatives carry those
fields empty and four non-representative notes carry the URLs … No criterion moved." Fold the same
way: the person representative's `whatsapp` becomes a value the door accepts (class Ø, or class B —
see finding 2 for why class A is not available to it), the class-C specimen moves onto a
NON-representative note keeping the `@example.com` spelling, and F6's plant accounting plus AC-1's
`why:` are corrected to say C is a plant rather than free. Also worth one line in the touch list: the
manifest's own override moves with the field's shape as well as its default —
`tests/fixture_vault.py:225` (`whatsapp="447700900789@example.com"`) alongside `:94`, because
`tests/test_fixture_vault.py:745-748` compares the parsed attribute against that declared scalar.

**2. Two of the four plant literals the class table names are inadmissible ANYWHERE in the fixture
corpus's reach, and the class-A cell is structurally inadmissible there — the corpus's one JID is
spelled `@example.com` BECAUSE of that wall, which is also why Thrandell is class C in the first
place.**

WI-016's privacy wall scores every email-shaped token in its reach against RFC 2606 / RFC 6761:
`EMAIL_SHAPED = [\w.+-]+@[\w.-]+\.\w+`, `RESERVED_EMAIL_DOMAINS = {example.com, example.net,
example.org}` as an EXACT-match frozenset, `RESERVED_TLDS = (".test", ".invalid", ".example")`, and
`_host_is_reserved` accepts only exact membership or a reserved-TLD suffix
(`tests/test_fixture_vault.py:302-325`). The live leg asserts zero violations per file
(`:1067-1069`), and the reach is every file under `tests/fixtures/vault/` PLUS the manifest module
`tests/fixture_vault.py` (`:386-392`). Applied to the literals this document freezes:

- **class A — `447700900123@s.whatsapp.net`: RED.** `s.whatsapp.net` is neither exact-reserved nor
  under a reserved TLD. And this is not a spelling accident that a different exemplar fixes: STORABLE
  is membership of the closed set `{"s.whatsapp.net", "lid"}`, so a phone-bearing STORABLE value must
  carry exactly that domain. **No class-A member can exist anywhere in the corpus's reach**, which
  also means the person representative cannot be made class A. `docs/vault-fixtures.md:5944-5948` is
  this constraint already recorded and already paid for: "A real JID (`<digits>@s.whatsapp.net`) is
  scored by `reserved_email_violations` against a domain no RFC reserves, so the corpus's JID is
  spelled `447700900789@example.com`" — the decision that makes Thrandell class C.
- **class E — `447700900456@lid.example.com`: RED.** `lid.example.com` is a SUBDOMAIN of
  `example.com`, which the frozenset matches by equality only, and it ends in none of the three
  reserved TLDs. Cheap fix, and it stays the cell it is: `447700900456@lid.example` is wall-clean
  (`.example` is a reserved TLD) and still class E — it contains the `@lid` substring so it parses
  with empty `phone_digits`, and its domain after the LAST `@` is `lid.example`, outside the closed
  set. But it is a correction to a literal three criteria name (the class table, AC-1's boundary-probe
  list, AC-3's required class-E member) plus AC-5's plant.
- **class D — `notaphone@s.whatsapp.net`: RED if planted in the reach**, same mechanism as class A.
  It is admissible in a test module's own literals, which is where AC-1's independence leg needs it.
- **class B is admissible, with a constraint nobody has stated.** `@lid` carries no dot after the
  `@`, so it is not email-shaped and the email wall never sees it — but `reserved_phone_violations`
  does (`:342-347`), and AC-1's REQUIRED negative-control lid ("11-digit string beginning with `1`")
  is satisfiable only from the NANP 555-01xx pattern: `15555550142@lid` passes
  (`RESERVED_PHONE_PATTERNS`' third member, `tests/test_fixture_vault.py:308-312`) and its 10-digit
  form `5555550142` is the `phones_match` counterpart the control needs. An arbitrary 11-digit lid is
  RED on the phone wall. Worth naming so the control is not discovered to be unplantable.
- **One more digit-level trap in the class-A exemplar even before the domain.** Thrandell's stored
  phone is `+44 7700 900123` (`tests/fixture_vault.py:224`), which normalizes to `447700900123` — the
  same digits the class-A exemplar uses — so that value would key `phone:447700900123` onto a second
  entity and mint an identifier conflict in the frozen corpus (`_index_identifiers`,
  `person.py:336-366`). Nothing in the battery pins the corpus's conflict set, so it would not go
  red; it would just be wrong. A plant has to pick an UNUSED member of a narrow reserved block, not
  merely a reserved-looking one.

So F6's cost line is short by the wall, and the choice it hands the spec-writer ("that cost is the
spec-writer's choice against an inline temp-vault note, not an open question for Dave") is FORCED for
class A rather than free. Decide it in this document, because F6 currently invokes WI-286 to argue
the opposite direction. Two arms: (a) the storable-form members live in the new test module's own
temp vault, and F6 says plainly that WI-286's reach-for-the-corpus-first rule yields here to WI-016's
privacy wall — nothing frozen is touched, and classes Ø, C and E can still come from the corpus; or
(b) this item declares a named `s.whatsapp.net` exemption in WI-016's wall the way `RESERVED_ISBN` is
declared (`tests/fixture_vault.py:46-50` — "asserted by EQUALITY against a one-member literal so it
cannot be padded"). **Recommend (a):** the exemption in (b) is defensible on the merits
(`s.whatsapp.net` is a protocol constant, not an identifying host) but it widens another item's
privacy wall to admit a real domain, and (a) buys the same coverage while leaving the wall alone.
Either way it is one sentence in F6 and a correction to AC-1's `why:`; what is not affordable is
freezing a plant list whose two storable-form members cannot be planted where the criterion says.

### Non-blocking notes (fold if cheap; no round is owed for them)

1. **AC-2's class-Ø cascade leg is satisfied today by a guard that predates this item, so it cannot
   fail for the reason it states.** `resolve_all` returns `[]` for a blank or whitespace-only query
   before step 1 runs (`person.py:606-611`), so "a blank query neither raises nor returns a person
   who merely has an empty `whatsapp:` field" is already true and stays true however the new step is
   written. Keep the leg — but state it as a pin on the guard's POSITION (the blank bail-out stays
   ABOVE the new `whatsapp_jid` step), which is the thing inserting a step can actually break.
2. **Class Ø's `None` member reaches the READER only as a bare `whatsapp:` key, and today such a note
   is INVISIBLE rather than empty.** YAML loads a valueless key as `None`,
   `_normalize_frontmatter` passes `None` through untouched (`parser.py:118-132`), and
   `whatsapp: str` (`models.py:94`) rejects it — so `model_validate` fails and the owned note raises
   `SchemaDriftError` onto the load skip surface (`parser.py:203-208`). Two cheap consequences: AC-4(a)
   should name YAML null explicitly as a class-Ø READ spelling, because the post-migration annotation
   has to coerce null → `[]` or the clearing spelling's own residue is unreadable; and the census's
   class-Ø row must be counted off the note BYTES rather than off loaded models, or it omits exactly
   the bare-key notes — a clause for `docs/wi-032-whatsapp-corpus-census.md`'s `why:`.
3. **Carried, not re-raised.** Rulings A, B and C are untouched by everything above, and the ordering
   the document states — settle A and B, measure the census, then freeze the frame — is still right.
   The two findings above are upstream of the FREEZE but downstream of the rulings, so they do not
   reopen anything Dave is being asked to sign.

```verdict
gate: architect
verdict: REVISE
date: 2026-09-26
model: claude-opus-5
note: The fold that made `@Thrandell Ibberly.md` the free class-C member collides with the frozen corpus's own two contracts — it is the ONE person round-trip representative, written through the gated whole-record arm with no refusal expected at `tests/test_writer.py:421` and `tests/test_fixture_vault.py:753`, and the class-A/class-E plant literals are unreserved hosts under the WI-016 privacy wall (`tests/test_fixture_vault.py:302-325`, reach at `:386-392`), which is itself why the corpus's one JID is `@example.com` and therefore class C at all.
targets: AC-1, AC-2, AC-3, AC-4, AC-5, #exploration-notes, #write-targets
prior: held
basis: folded-material
findings: 2/5
```

## Conductor Note — 2026-09-26 (revise-cap ESC-WI-032-idea-revise-cap-2594e354, answered by hand under the 2026-08-11 standing grant)

Read this as the instruction for the next ideation-partner round; it replaces the resume note a
grant would have carried. Nothing is signed at `idea`; Rulings A, B and C are untouched by both
gates' own statement and stay Dave's at the grounding door — do NOT reopen them.

**The generator.** The fixture-plant plan (F6, AC-1's `why:`, AC-3's required members, AC-5's plant
list) was drafted as a table of exemplar LITERALS without checking each plant against the frozen
corpus's OWN contracts. Architect round 4 and ac-red-team round 3 found the same two members
independently, and the three ac-red-team rounds before them were each one more member of the same
class (an oracle over an unparseable plant, an empty-value plant no arm agreed on, a plant on the
wrong note).

**Close the class in one fold.** Build the plant plan as a MATRIX of every plant literal (the Ø, A,
B, C, D and E exemplars) × every corpus contract: the WI-016 privacy wall
(`tests/test_fixture_vault.py:302-325`, reach at `:386-392` — equality on reserved domains, suffix on
reserved TLDs), `roundtrip_representative` uniqueness (`:689-695`) with its gate-clean assertion
(`:726-732`) and `tests/test_writer.py:404-428`, the type-registry sweep, and any other wall that
reads `tests/fixtures/vault/`. DECLARE the sweep's result in `## Exploration Notes` (F6): which
plants live in the frozen corpus, which live ONLY in the new test module's own temporary vault, and
why each cell is wall-clean.

**The mechanical folds both gates agreed on.** (1) AC-1's `why:` stops calling
`@Thrandell Ibberly.md`'s value a free class-C plant; the representative's `whatsapp` moves to a value
AC-3 accepts (class Ø, or a storable class-B `@lid`), so both round-trip tests stay green with NO
refusal; the class-C exemplar moves onto a NON-representative plant in a wall-clean spelling.
(2) The class-A (`@s.whatsapp.net`) and class-E plants live in the new test module's own temporary
vault, never in `tests/fixtures/vault/`; say so in F6 AND in AC-1/AC-3/AC-5. (3) Respell class-E to a
reserved-TLD-safe host (e.g. `447700900456@lid.example`) — same cell, still outside the closed set
`{s.whatsapp.net, lid}`. (4) The class-D exemplar (`notaphone@s.whatsapp.net`) stays a test-module
literal, per AC-1's independence leg.

**Then sweep the next level** — every OTHER literal the ACs name (phones, emails, the `check:` test
names) against the same walls — and say what that sweep found, even if it found nothing.

## Architectural Review — 2026-09-26 (round 5)

**Recommendation: REVISE — one blocking finding, and the fold is one deletion plus one sentence**

Round 5, re-read at this worktree's HEAD (`c93006a` plus the seeded uncommitted delta). Every citation
below was read in the code or the doc THIS round. **The prior rounds' findings all HELD**, including
round 4's two fixture-plant findings and the AC red-team's convergent round-3 pair, both of which are
closed at the right altitude (F17, the class table's fourth column, AC-1's WHERE clause, rejected items
11 and 12). What this round found is the NEXT member of the class the conductor note ruled must be
closed in ONE fold: the fixture-and-cost plan still carries one instruction that was never checked
against the contract of the artifact it proposes to edit. It touches no ruling, raises no new question
for Dave, and is a correction to this document.

### Trigger check

Fired for the reasons rounds 1–4 recorded: a new persistent frontmatter shape across ~1,170 live person
notes; significant extension of three core systems (the WI-021 gate, the WI-125 identifier index,
`resolve_all`); >3 files in different concerns; cross-system consumers; effort > 1 day.

### The prior findings, re-read against this tree

**Round-1 findings 1 and 2 — still CLOSED.** Re-verified rather than carried: `identifier.py:269-281`
raises on `None` and on empty through two lines with no blank branch, tests the `@lid` SUBSTRING at
`:276`, then `normalize_phone(s)` against `Phone.MIN_DIGITS` at `:278-280`, and tests for a JID suffix
nowhere — so `WhatsAppJID.parse("+44 7739 341679")` still succeeds and only the STORABLE predicate
refuses it; `phone_normalization.py:39-55` splits at the FIRST `@` and strips every non-digit;
`identifier.py:298` keys a phone-bearing JID on `phone:<digits>` and a lid on `jid:<jid>`. The
`List[str]` answer and its derived accessor are unchanged and still right.

**Round-3's class-Ø finding and round-4's two plant findings — CLOSED, and the round-4 folds check out
against the code they rest on.** Re-verified this round, not carried: `tests/fixture_vault.py:219-233`
is Thrandell's spec with `whatsapp="447700900789@example.com"` and `roundtrip_representative=True`;
`tests/test_fixture_vault.py:689-695` asserts EXACTLY ONE representative per declared type, and
`:726-732` / `:753-761` are the gate-clean assertion and the write through the whole-record entity arm;
`tests/test_writer.py:404-428` is the second such write. The privacy wall is as F17 leg 2 states —
`EMAIL_SHAPED` requires a dot after the `@` (`:302`), `RESERVED_EMAIL_DOMAINS` is matched by EQUALITY
and `RESERVED_TLDS` by suffix (`:306-319`), and `reach_files()` is the corpus directory plus
`tests/fixture_vault.py` (`:386-392`). The three respelled literals are right at the digit level too:
`15555550142` matches `RESERVED_PHONE_PATTERNS`' third member `^1?\d{3}55501\d{2}$` (`:311`) and
`normalize_phone("15555550142@lid")` is `15555550142`, so the class-B corpus plant is wall-clean on the
phone leg while being invisible to the email leg (`@lid` carries no dot); `447700900321` and
`447700900654` are unclaimed members of the drama block; and I re-ran F17 leg 3's predicate — the only
claimed members are `447700900123` (`:224`, `:288-290`), `447700900456` (`:323`, and the `RESOLVABLE`
row at `:533`) and `447700900789` (`:225`). One fact worth adding because it is the leg most likely to
have been broken by moving a value and nobody checked it: `RESOLVABLE` (`tests/fixture_vault.py:529-534`)
carries no `447700900789` query, so relocating the class-C value to a non-representative note changes no
declared resolution answer, and `LOADABLE`/`SKIPS` (`:490-525`) are untouched because the tolerant reader
adds no skip.

### Review (only where this round's finding bites)

**Fit, Duplication, Boundaries, Determinism, Reversibility, Generalization, Build-vs-extend, Prior art.**
Unchanged from rounds 2 and 4, re-spot-checked: `_refuse` still admits no note-derived value and takes a
plain `pattern_key: str` (`name_gate.py:142-174`), `_is_str_list`/`_shaped` are still positive predicates
under which a bare `str` falls to pass-through (`name_gate.py:181-198`), and `normalize_phone` is still
the stdlib-only leaf whose consumers want the naive split. Liberal-for-reach / conservative-for-storage
remains the outside view; no cited execution is owed.

**Cost & maintenance — again the dimension that moves, and for the same reason one level out.** Round 4
found the plant plan priced against the corpus's bytes rather than against the corpus's CONTRACTS. The
fold corrected that for three contracts — the round-trip representative, the privacy wall, and
identifier-conflict uniqueness. It did not sweep the rest, and one of the unswept ones is named in the
fixture cost line itself.

### Blocking issue

**1. "The census gains a row for each newly declared class, and its own digest follows" is wrong on both
halves. `docs/vault-shape-census.md` is frozen against a digest that lives inside ANOTHER work item's
SIGNED criterion, and its class-row vocabulary cannot hold a `whatsapp` cell — so following the line
lands the builder in a red whose cheapest green is amending WI-016's frozen AC-3 text or writing a false
count into the estate's shape ledger.**

The line is `### Effort`'s itemized fixture work (iv), and the claim behind it is F6's cost sentence ("if
the plant declares a new class, a census row") re-endorsed by F6's third amendment ("and one census row
per newly declared class"). Three facts, each read this round:

- **The digest has no build-owned home.** `assert_census_is_frozen()` compares `sha256` over
  `docs/vault-shape-census.md` against `declared_census_digest()`, which reads the value out of the
  `AC-3` `criteria` fence in `docs/vault-fixtures.md` (`tests/test_fixture_vault.py:217-254`). Those
  criteria are FROZEN — signed 2026-09-08, and that document states in terms that "every remaining
  correction to a criterion's own text is now a D4b re-sign" (`docs/vault-fixtures.md:1389-1396`). The
  value currently stands at `CENSUS_DIGEST = sha256:4cb7945f…` inside that fence (`:1418`). So "its own
  digest follows" names an edit that does not exist: the digest follows only by editing another item's
  signed criterion, and the assertion runs in TWO places (`tests/test_fixture_vault.py:789`, `:1031`), so
  a census edit reddens the floor the moment it lands.
- **The row vocabulary is name-corruption classes, not field-value cells.** `census_class_rows`
  (`:122-138`) reads `census-class` fences whose ids are either a `branch_id` derived from
  `TIER1_BRANCHES + COMPANY_TIER1_BRANCHES` — asserted in BOTH directions at `:830-838` — or one of the
  six hand-listed shape classes (`:842-848`), and the landed table is exactly those sixteen
  (`docs/vault-shape-census.md:62-210`, ids `email_chars` … `postal_address_in_name`). `count` is a
  LIVE-VAULT count and `specimen` is a name string. There is no cell in that table for "a `whatsapp`
  value that parses and is not storable".
- **And leg (i) is an EQUALITY, which makes a MEASURED whatsapp row unsatisfiable for the one cell that
  matters.** `{MEASURED row ids}` must equal `{union of NOTES[...].shape_classes}` (`:800-803`), and any
  note declaring a `shape_class` must also declare a `Verdict` (`:856-891`) from a three-member
  vocabulary every arm of which is evaluated against that note's `name`. Class A's live count is not
  zero, and F17 leg 2's own derivation says no class-A member can exist anywhere in the corpus's reach —
  so a MEASURED class-A row can never acquire the corpus specimen the equality demands. Class Ø's 21
  members are not corruption specimens and have no verdict to declare.

Why this is blocking rather than a build-time surprise: `docs/**` is builder-writable in full, which
WI-016's own AC-3 `why:` names as the reason leg (iv) exists. So the builder who follows item (iv), sees
two tests go red, and reaches for the shortest green has two self-consistent routes and both are green on
every criterion in THIS set — re-freeze the digest by editing WI-016's signed AC-3 fence, or write the
new rows as `status: ABSENT, count: 0` with a plausible command/stdout pair, which is verbatim the
false-ledger route that same `why:` says the leg was added to close. Neither is a thing to discover from a
build, and the second corrupts the artifact this repo designates as the sole oracle for every live-vault
claim its hermetic suite cannot re-derive.

**The fold, and it is cheaper than either wrong route.** WI-032's six cells already have a home:
`docs/wi-032-whatsapp-corpus-census.md`, the precondition this document declares in `## Write Targets`,
whose `why:` already asks for "one row per cell of the SIX-cell class table". So delete the census-row
cost from F6's original sentence and from F6's third amendment, and replace `### Effort` item (iv) with
the affirmative statement that `docs/vault-shape-census.md` is NOT touched by this item — its class table
is WI-016's name-corruption vocabulary, its digest lives in WI-016's signed AC-3 fence, and the per-cell
counts this item needs belong in its own census precondition. The fixture cost then reduces to what is
genuinely build-side: the two corpus edits, the manifest overrides, and one `CORPUS_DIGEST` regeneration,
all of which `tests/fixture_vault.py:21-25` and `:44` make a legal build-side move. If a later reader
decides WI-032 does owe a row in WI-016's census, that is a conductor pass plus a D4b re-sign of another
item's signed criterion and it goes in front of Dave — not into a cost line.

**The generator, stated so the next fold can close the class rather than the member.** The conductor note
asked for a MATRIX of every plant literal × every corpus contract, naming the privacy wall,
`roundtrip_representative` uniqueness, the type-registry sweep, "and any other wall that reads
`tests/fixtures/vault/`". F17 delivered three of those. Unswept and reading the corpus or its manifest:
`test_every_census_corruption_class_has_a_specimen_with_a_verdict` (`:783`, the one above),
`test_the_skip_surface_over_the_corpus_equals_its_declared_reasons` (`:923`, with `SKIPS`, `LOADABLE` and
`RESOLVABLE` as its declared oracles — I checked it and it is CLEAN under the corpus edits, which is
worth SAYING rather than leaving unsaid), and
`test_the_fixture_vault_files_close_their_wall_memberships_by_running_each_predicate` (`:1353`, whose
universe the new test module joins — note 3 below). The conductor also asked for a next-level sweep over
every OTHER literal the ACs name and for its result to be stated "even if it found nothing"; the document
states no such sweep. Completing the matrix over the four walls named here, and stating the next-level
result, is what makes this the last round of this class rather than the fifth.

### Non-blocking notes (fold if cheap; no round is owed for them)

1. **Say where the whatsapp refusal `pattern` is DECLARED, not only that it is distinct.** AC-3 requires
   "its own stable `pattern` value distinct from every `NameValidator` pattern", which is the right
   requirement and is satisfiable for free: `_refuse` takes a plain `pattern_key: str`
   (`name_gate.py:142-174`), so a gate-local literal needs no record anywhere. The gap is what it does
   not forbid. WI-016's AC-3 floor is DERIVED from `{record.branch_id for record in TIER1_BRANCHES +
   COMPANY_TIER1_BRANCHES}` and asserted in both directions (`tests/test_fixture_vault.py:830-838`), and
   that criterion's `why:` pre-prices the consequence by name: a new Tier-1 branch reddens it
   immediately and discharging it needs a live-vault count, a scan command and verbatim stdout plus a
   re-taken digest — a conductor pass. A builder who declares the whatsapp refusal as a
   `name_validation` record because that is where the other patterns live pays exactly that. One clause
   in AC-3 or in the touch list closes it.
2. **The class-B corpus edit changes the DECLARED SHAPE as well as the value, and the manifest override
   has to move with both.** `tests/test_fixture_vault.py:745-748` compares
   `getattr(doc.entity, attribute)` against the declared literal and `:755-761` compares the re-parsed
   frontmatter MAPPING against the same literal, so with the stored field `List[str]`,
   `tests/fixture_vault.py:225` must declare `["15555550142@lid"]` and `:94`'s default must become `[]`
   even though the corpus note itself keeps the scalar spelling (the tolerant reader is what makes that
   pair agree). The document names both lines; it does not say the declared VALUE becomes a list, and
   that is the half a builder gets wrong while reading the line as "change the string".
3. **The new test module joins three set-equality walls, all in one test.** `ast` use is asserted
   single-homed to `tests/derivations.py` (`tests/test_fixture_vault.py:1383-1386`), the legal homes for
   a `SKIP_REASONS` literal are pinned to exactly two files by EQUALITY (`:1392-1395`), and every
   top-level `def test_` in the listed modules must resolve uniquely through `check_module`
   (`:1438-1442`). AC-3 and AC-5 already route their derivations through `tests/derivations.py`, so the
   first is honoured by design; the second is the one that bites, because AC-4(a)'s skip-surface
   assertions invite typing a reason literal instead of importing it from
   `obsidian_schemas/repositories/base.py`. One line in the touch list, and it is cheaper than the red.
4. **Carried, not re-raised.** Rulings A, B and C are untouched by everything above — by both gates'
   statement and by mine — and the ordering the document states, settle A and B, measure the census,
   then freeze the frame, is still the right one. The finding above is upstream of the FREEZE and
   downstream of the rulings, so it reopens nothing Dave is being asked to sign.

```verdict
gate: architect
verdict: REVISE
date: 2026-09-26
model: claude-opus-5
note: `### Effort` item (iv) and F6 still price "a census row per newly declared class, and its own digest follows" as build-side and free, but `docs/vault-shape-census.md` is frozen against a digest that lives inside WI-016's SIGNED AC-3 fence (`tests/test_fixture_vault.py:217-254`, `docs/vault-fixtures.md:1418`) and its class-row vocabulary is name-corruption `branch_id`s with live-vault counts and name specimens, so a whatsapp cell has no row — and the two cheapest greens are amending another item's signed criterion or writing a false ABSENT/0 row, which is verbatim the route WI-016's own leg (iv) exists to close; the item's six cell counts already belong in `docs/wi-032-whatsapp-corpus-census.md`.
targets: AC-1, AC-3, AC-5, #exploration-notes
prior: held
basis: folded-material
findings: 1/4
```

## Architectural Review — 2026-09-26 (round 6)

**Recommendation: REVISE — one blocking finding, and it is NOT the plant class's next member**

Round 6, re-read at this worktree's HEAD (`c93006a` plus the seeded uncommitted delta). Every citation
below was read in the code THIS round. **The prior rounds' findings all HELD**, and the class the
conductor note ruled must be closed in ONE fold — the fixture-plant × corpus-contract matrix — IS closed:
F18's six legs check out leg by leg against the code they cite, including the three that report a clean
result. What this round found is a different generator in ORIGINAL text: F9's claim that the linter's
REPORT surface comes free. `_gate_refusal_pattern` has exactly ONE call site in the tool and that call
site was never read. It touches no ruling, raises no new question for Dave, and the fold is one detector
arm plus one AC clause.

### Trigger check

Fired for the reasons rounds 1–5 recorded: a new persistent frontmatter shape across ~1,170 live person
notes; significant extension of three core systems (the WI-021 gate, the WI-125 identifier index,
`resolve_all`); >3 files in different concerns; cross-system consumers; effort > 1 day.

### The prior findings, re-read against this tree

**Round-1 findings 1 and 2 — still CLOSED.** Re-verified rather than carried: `identifier.py:269-281`
raises on `None` and on empty through two lines with no blank branch (`:271-275`), tests the `@lid`
SUBSTRING at `:276`, then `normalize_phone(s)` against `Phone.MIN_DIGITS` at `:278-280`, and tests for a
JID suffix nowhere — so `WhatsAppJID.parse("+44 7739 341679")` still succeeds and only the STORABLE
predicate refuses it; `:298` keys a phone-bearing JID `phone:<digits>` and a lid `jid:<jid>`. One fact
worth adding because the design's shape rests on it and no finding states it: `WhatsAppJID` is a frozen
dataclass that ALREADY carries three derived `@property`s (`phone` at `:283-286`, `value` at `:288-290`,
`key` at `:292-298`), so `jid_domain`/`is_storable` is the fourth member of an existing pattern rather
than a new mechanism on the type.

**Round-3's class-Ø finding — CLOSED.** `person.py:318-320`'s `add()` returns on a `None`-or-blank raw
BEFORE parsing, re-read; `:330-331` projects `whatsapp` only when truthy; `name_gate.py:399`'s
`elif entry and …` draws the same line by falsiness; `models.py:94` is the `""` default and
`tests/fixture_vault.py:94` the hand-transcribed oracle.

**Round-4's two plant findings and round-5's census finding — CLOSED, and F18's matrix is sound where I
re-drove it.** Leg 1: `declared_census_digest()` really does read `CENSUS_DIGEST` out of the AC-3
`criteria` fence of `docs/vault-fixtures.md` (`tests/test_fixture_vault.py:217-239`), `assert_census_is_frozen()`
compares it to `sha256` over the census bytes (`:242-254`) and runs at `:789` and `:1031`;
`census_class_rows` (`:122-137`) admits only `branch_id`s from `_branch_ids()` (`:587-595`, asserted both
ways at `:830-838`) or the six hand-listed shape classes (`:842-848`), the MEASURED set is an EQUALITY
against `NOTES[...].shape_classes` (`:800-803`), and every shape-class specimen must declare a `Verdict`
evaluated against its `name` (`:856-891`). So "a `whatsapp` cell has no row and the digest has no
build-owned home" is exactly right, and item (iv)'s affirmative statement is the correct fold. Leg 2:
the eight admissible receivers are at `tests/fixture_vault.py:326-341` and `@Fennwick Drostane.md` is
`:340-341`. Leg 3: `reserved_phone_violations` sweeps `spec.fields.get("phones", ())` only
(`:1152-1168`) and never reads `whatsapp`; `RESOLVABLE` (`tests/fixture_vault.py:529-534`) carries no
`447700900789` query. Legs 5 and 6: `_temp_vault`-style walls confirmed at
`tests/test_fixture_vault.py:1353-1442`, and the three derivation hooks the ACs lean on all exist
(`tests/derivations.py:979`, `:1870`, `:2175`). The digit arithmetic checks out too: `15555550142`,
`15555550163` and `5555550142`/`5555550163` all match `^1?\d{3}55501\d{2}$` (`:311`), `447700900987`
matches `^447700900\d{3}$` (`:309`), and `@lid` carries no dot so `EMAIL_SHAPED` (`:302`) never fires on
either lid literal.

### Review (only where this round's finding bites)

**Fit, Duplication, Boundaries, Determinism, Reversibility, Generalization, Build-vs-extend, Prior art.**
Unchanged from rounds 2, 4 and 5, re-spot-checked. `_index_entity` still feeds
`normalize_phone(entity.whatsapp)` into `_phone_index` unconditionally (`person.py:266-270`);
`_index_identifiers` still records a collision to `_conflict_sets` and "never raises: a conflict is an
observability output" (`person.py:336-344`), which is the mechanism F17 leg 3 and AC-5's pinned pairs
exist to avoid; `resolve_all` still bails on a blank query BEFORE step 1 (`:608-609`) and still has no
`whatsapp_jid` step (`:628-651`); `_RESOLVE_CASCADE_ORDER` is still four labels (`:145`) with an unknown
label ranking last (`:190-197`). Liberal-for-reach / conservative-for-storage remains the outside view;
no cited execution is owed.

**Cost & maintenance — the dimension that moves again, and this time one level SIDEWAYS rather than
out.** Rounds 4 and 5 found the plant plan priced against the corpus's bytes rather than its contracts.
This round's finding is the same mistake against a different artifact: a capability the document prices
at ZERO on the strength of a function's docstring, without reading where the function is CALLED.

### Blocking issue

**1. F9's "the linter's report surface comes free" is false. `_gate_refusal_pattern` has exactly ONE call
site in the tool, inside the `stem_name_divergence` arm and behind `stem != stored` — so a note whose
`whatsapp` the door refuses is reported by `lint_vault` only if its filename ALSO disagrees with its
stored name, a live population WI-029 closed to ZERO five days ago. The item promises in five places
that the D+E residual is "reported and left"; as specced, it is left and not reported.**

The facts, each read this round:

- **One call site, and it is not a detector.** `_gate_refusal_pattern` is defined at
  `scripts/lint_vault.py:334-352` and called at `scripts/lint_vault.py:450` — the only occurrence in the
  tool. It sits inside `check_structural`'s `stem_name_divergence` arm, behind
  `if vf.entity_type == "person"` (`:433`) and `if isinstance(stored, str) and stored.strip() and stem
  != stored` (`:449`), and its return value becomes a MARKER appended to that issue's message (`:451-462`).
  It emits no `LintIssue` of its own. `rg -n 'whatsapp' scripts/lint_vault.py` is still 0 matches, and
  none of the five check functions (`:355`, `:496`, `:577`, `:698`, `:798`) reads the field —
  `field_type_mismatch` is about `auto_created` (`:464-465`).
- **The live population of that arm is zero.** `docs/stem-divergence-live-baseline.md:191` records the
  exit figure: divergent live person notes **8 → 0**, conductor-performed 2026-09-26. So on today's vault
  the one route to `_gate_refusal_pattern` is never taken at all. It is not a narrow report surface; it
  is an empty one.
- **And the `--fix` half is true for a different reason than F9 gives.** F9 says a refusing arm "does not
  make a malformed-JID note unfixable — PROVIDED the refusal carries its own `pattern` value". The
  `pattern` requirement is right, but it is not what makes that true: `apply_fixes` gates the DELTA
  (`whole_record=False`, `:1181`) and no auto-fixable rule's delta contains `whatsapp` at all — the five
  are `field_type_mismatch`, `person_missing_name`, `missing_body_sections`,
  `meeting_missing_from_timeline`, `broken_wikilink` (`tests/test_lint_vault_fix_rules.py:614-624`). So
  the refusal bucket never fires for this field either, from either direction.

**Why this is blocking rather than a build-time surprise: the item is buildable three ways and two of
them ship silent.** AC-3's closing clause reads "And one consequence pinned where it is FREE -
`lint_vault` REPORTS such a note through `_gate_refusal_pattern` under that distinct pattern", and
`### Effort`'s touch list prices `scripts/lint_vault.py` as "(pattern routing only)".

- **Build A** adds a report-only detector. Correct, and it is what the Intent needs — but it is a NEW
  detector in a tool whose changes carry a WI-026 floor, which the AC calls free and the touch list does
  not carry.
- **Build B** follows the citation literally and widens the existing marker so a non-storable `whatsapp`
  turns it on. Green on every criterion in this set, and wrong twice over: the marker's own text says
  "this divergence is not repaired by renaming the file to the stored name; repair the field"
  (`scripts/lint_vault.py:451-454`), which is a FALSE statement about a divergence whose actual defect is
  a JID; and it would flip live rows from UNMARKED to MARKED against a bracket that records "divergent
  rows the WRITE DOOR refuses (b3): 0 of 8" (`docs/stem-divergence-live-baseline.md:124`).
- **Build C** reads "pinned where it is free" as already-true and touches the tool not at all. Green on
  every criterion, and the residual is silent.

So the promise is made in `## Intent` ("A value that is already wrong is reported and left, never
erased"), in F13 leg 3 ("both reported by the linter and left for hand repair"), in Ruling B leg 2, in
AC-5 leg (e) ("reported as needing repair") and in `### Examples of done` ("the linter names it instead
of nobody noticing until a hand repair") — and the machinery behind it does not exist. This is the same
defect SHAPE the class-Ø fold closed one artifact over: a repair path the document commits to that the
item's own tooling does not provide. There the door refused the repair; here nothing reports that a
repair is owed.

**The fold, and it is cheap because this repo has already built exactly this detector once.** Add ONE
report-only arm to `scripts/lint_vault.py`'s `check_structural` — a `whatsapp` value the STORABLE
predicate rejects, `auto_fixable` left at its default so it never enters `apply_fixes`, carrying its own
check name and never the `stem_name_divergence` marker. WI-029's own detector is the precedent to copy
literally (ERROR, `structural`, never auto-fixable), and the cost is bounded and measurable rather than
assumed: the AC-1 oracle-table equality in `tests/test_lint_vault_fix_rules.py:596-624` is scoped to
`auto_fixable_emitter_checks` (`:599`), so a report-only rule does NOT join it and owes no repair oracle;
and `tests/test_stem_name_divergence_detector.py:283-289` filters on `issue.check == DIVERGENCE_CHECK`,
so a new check name disturbs none of that module's set equalities. Then: AC-3's closing clause stops
saying "free" and names the new check as an assertion (fires on class C/D/E, silent on Ø and on storable
values, `auto_fixable is False`); `### Effort`'s touch list carries `scripts/lint_vault.py` as a DETECTOR
plus a test module for it; and F9 is corrected to say the report surface is a new arm and the `--fix`
survivability comes from the delta containing no `whatsapp` key. If Dave would rather not grow the
linter, the honest alternative is to DELETE the word "reported" from the Intent, F13 leg 3, Ruling B leg
2, AC-5 leg (e) and `### Examples of done` and say the residual is discovered by the migration's own
report only — but that is a promise being withdrawn, so it should be withdrawn in writing rather than by
a build.

### Non-blocking notes (fold if cheap; no round is owed for them)

1. **AC-1's receiver constraint list is short by one class, and it is the same unread call site.** The
   WHERE clause admits any non-representative person note that LOADS and declares no
   `shape_classes`/`verdict`. Two notes satisfy all three and are still wrong receivers:
   `@Perrowin Tessamund Drostane.md` and `@Yolvenna Brindlecote Skarnell.md` declare
   `shape_classes=()` and no `verdict` — they carry a `discriminator` instead
   (`tests/fixture_vault.py:297-306`) — and they are the corpus's two MARKER-BEARING stem-divergent
   notes, asserted by EQUALITY at `tests/test_stem_name_divergence_detector.py:341-345` with their
   patterns pinned at `:346-352`. A non-storable `whatsapp` on either makes WI-029's marker set depend on
   the gate's arm ORDER, the same question F18 leg 2 removed for census specimens. The criterion NAMES
   `@Fennwick Drostane.md`, which is why this is a note and not a finding — but the CONSTRAINT should
   read "and is not stem-divergent", because the constraint is what a builder reasons from when the named
   note stops being available. (The two notes that would actually have gone RED — `@Quillam Ostrivane.md`
   and `@Quillam Lumbrek.md`, whose `patterns[...] is None` is asserted at `:353-354` — are already
   excluded by the `shape_classes` clause.)
2. **A third in-tree reader of the representative's declared `whatsapp`, not on the touch list.**
   F17 leg 1 names `tests/test_writer.py:404-428` and `tests/test_fixture_vault.py:705-761`.
   `tests/test_parser.py:248-264` (`test_corpus_person_note_parses_to_its_declared_values`) is a third:
   it selects the person `roundtrip_representative` and compares `getattr(doc.entity, attribute)` against
   `spec.fields` for every declared field. It stays GREEN under the fold — the tolerant reader gives
   `["15555550142@lid"]`, which is what `:225` will declare — but a builder who changes `:225` to a
   scalar list-member string sees it red in a module `### Effort` does not mention. One line in the touch
   list.
3. **The other four corpus-reading modules are CLEAN under the two corpus edits, stated rather than left
   unsaid** (the conductor note asked for clean sweep results to be reported). `tests/test_repositories.py:2255`
   imports `LOADABLE`/`materialize_vault` only — cache quantities, unaffected by a field's value;
   `tests/test_provenance_write_seam.py:147-171` derives its subjects from stem≠name divergence and from
   name-sharing, and neither `@Thrandell Ibberly.md` nor `@Fennwick Drostane.md` is either;
   `tests/test_stem_name_divergence_detector.py`'s four divergent members all carry `whatsapp: ""` today
   and stay class Ø under the fold, so its marker equality is untouched by the edits themselves (note 1
   is about the CONSTRAINT, not the named receiver); `tests/test_lint_vault_fix_rules.py` plants its own
   notes over a materialized copy and hands `apply_fixes` explicit issue lists, so no corpus-wide count
   moves.
4. **Carried, not re-raised.** Rulings A, B and C are untouched by everything above — the refused
   population, the repair door and the migration's repair pass are all unchanged; only the REPORT half
   moves. The ordering the document states, settle A and B, measure the census, then freeze the frame, is
   still right, and this finding is upstream of the FREEZE and downstream of the rulings.

### On the class the conductor note ruled closed

Stated explicitly, because it is the discriminant the factory reads and not a rhetorical point. The
plant class — every plant literal × every contract of the frozen corpus, its manifest and the
declarations those walls derive from — is CLOSED. I re-drove F18's six legs against the code this round
and every one of them holds, including the three that report nothing; the two corpus edits, the five
minted digit runs and the two pinned two-JID literals are all admissible where the document now puts
them, and `tests/test_fixture_vault.py` needs no widening. This round's finding is not the seventh member
of that class: its subject is `scripts/lint_vault.py`, its generator is F9 — text that predates every
fold and that no gate round, mine included, has re-read against the tool's call graph — and its fold
lands in a file the plant matrix never had reason to open.

```verdict
gate: architect
verdict: REVISE
date: 2026-09-26
model: claude-opus-5
note: F9 prices the linter's report path at zero, but `_gate_refusal_pattern` has ONE call site (`scripts/lint_vault.py:450`), inside the `stem_name_divergence` arm behind `stem != stored`, emitting a MARKER and never an issue — and WI-029 closed that live population to 0 (`docs/stem-divergence-live-baseline.md:191`), so the D+E residual that `## Intent`, F13 leg 3, Ruling B leg 2, AC-5 leg (e) and `### Examples of done` all promise is "reported and left" is left and never reported; AC-3 calls the consequence free, so two of the three self-consistent builds ship silent and one falsifies WI-029's own marker.
targets: AC-1, AC-3, AC-5, #intent, #exploration-notes
prior: held
basis: original
findings: 1/4
```

## Architectural Review — 2026-09-26 (round 7)

**Recommendation: REVISE — one blocking finding, and it is the THIRD artifact class rather than
the next member of either closed one**

Round 7, re-read at this worktree's HEAD (`c93006a` plus the seeded uncommitted delta). Every
citation below was read in the code THIS round. **The prior rounds' findings all HELD**, and both
classes the document has been closing are closed: the fixture-plant × corpus-contract matrix (F18)
and the linter's report surface (F19). What this round found is a class no round has opened: the
walls that read **`obsidian_schemas/repositories/person.py` itself** — the file this item edits
most heavily. `tests/test_identity_endgame.py` freezes that file's PROSE verbatim for every owner
outside a thirteen-member authorized list, and `PersonRepository.save` — the frame F11 and F13 make
this item's disclosure home and its refusal surface — is not on that list. The document names that
module exactly once, at `tests/test_identity_endgame.py:274`, for an unrelated phone literal (F17
leg 3 extended): it was opened for a digit grep and its walls were never read. No ruling is touched
and I raise no new question for Dave.

### Trigger check

Fired for the reasons rounds 1–6 recorded: a new persistent frontmatter shape across ~1,170 live
person notes; significant extension of three core systems (the WI-021 gate, the WI-125 identifier
index, `resolve_all`); >3 files in different concerns; cross-system consumers; effort > 1 day.

### The prior findings, re-read against this tree

**Round-1 findings 1 and 2 — still CLOSED.** Re-verified rather than carried: `identifier.py:271-275`
raises on `None` and on empty with no blank branch, `:276` tests the `@lid` SUBSTRING, `:278-280`
tests `normalize_phone(s)` against `Phone.MIN_DIGITS`, and a JID suffix is tested nowhere — so
`WhatsAppJID.parse("+44 7739 341679")` still succeeds and only STORABLE refuses it. The `List[str]`
stored field with a derived accessor is unchanged and still right.

**Round-6's finding (F19, the report surface) — CLOSED, and the fold's cost accounting is correct
where I re-drove it, including the two walls F19 does not name.** `_gate_refusal_pattern` is still
defined at `scripts/lint_vault.py:334-352` with its one call at `:450`, splicing
`NOT_RENAMEABLE_MARKER` (`:72`, `:452`) into the divergence ERROR's message and emitting no issue;
`auto_fixable: bool = False` is the dataclass default (`:96`). The new arm joins nothing it should
not: `auto_fixable_emitter_checks` collects only `LintIssue(...)` calls that pass an
`auto_fixable=` keyword and skips a construction with none at all
(`tests/derivations.py:1893-1906`), so a report-only arm is outside the WI-026 oracle table by
construction (`tests/test_lint_vault_fix_rules.py:599`, `:621-624`) exactly as F19 leg 4 claims. Two
walls F19 does not name are also clean, and I state them because an unstated clean result is
indistinguishable from an unswept one: `_check_the_corpus_is_a_false_positive_floor` filters
`observed` to the `pinned` seven before its equality against `CORPUS_PINNED_ISSUES`
(`tests/test_lint_vault_fix_rules.py:842-845`) and `set(subjects) == set(pinned)` at `:897` demands
a subject only for a pinned member — so a new check is invisible to both; and the divergence
module's own `triaged` dict over ALL structural issues (`tests/test_stem_name_divergence_detector.py:359-363`)
asserts only `@Isolde Varnholt.md`, an undecodable skip specimen carrying no frontmatter at all, so
the new arm cannot move it.

**Round-3's class-Ø finding and rounds 4–5's plant/census findings — CLOSED.** Re-verified the
load-bearing facts: `person.py:318-320`'s `add()` returns on a `None`-or-blank raw before parsing;
`writer.py:333-337` sets a field and there is no delete affordance; F18 leg 2's eight admissible
receivers are at `tests/fixture_vault.py:326-341`.

### Review (only where this round's finding bites)

**Fit, Duplication, Boundaries, Determinism, Reversibility, Generalization, Build-vs-extend, Prior
art.** Unchanged from rounds 2, 4, 5 and 6, re-spot-checked: `_index_entity` still feeds
`normalize_phone(entity.whatsapp)` into `_phone_index` unconditionally (`person.py:266-270`);
`resolve_all` still bails on a blank query before step 1 and still has no `whatsapp_jid` step;
`_RESOLVE_CASCADE_ORDER` is still four labels (`:145`) with an unknown label ranking last
(`:190-197`). Liberal-for-reach / conservative-for-storage remains the outside view; no cited
execution is owed.

**Cost & maintenance — the dimension that moves, for the third time and on the third artifact.**
Rounds 4–5 found the plan priced against the frozen corpus's bytes rather than its CONTRACTS; round
6 found a tool capability priced off a docstring rather than off a call graph. This round: the
package file the item edits most is priced as ordinary code, and it is not — its comment and
docstring text is a frozen fixture of another item.

### Blocking issue

**1. `PersonRepository.save`'s docstring is FROZEN VERBATIM by WI-024's prose wall, and it is
exactly where F11's write-back disclosure and F13's refusal disclosure have to land. The three
builds that resolve the red are all self-consistent and green on every criterion in this set; one
reverts a disclosure this document promises, and one has to DELETE prose to buy its green.**

The wall, each fact read this round. `prose_lines` (`tests/derivations.py:1773`) records EVERY
comment line and EVERY docstring line of a file with its owning definition's qualname
(`ProseLine`, `:1644-1648`). `tests/fixtures/identity_endgame/prose_surface_cut0.json` is that
surface over `person.py` recorded at Cut 0 — "Recorded ONCE, against unchanged code; never
re-recorded" (`tests/test_identity_endgame.py:402`). Clause (e1) of
`test_strangler_prose_class_is_closed_in_the_package` then asserts, on every run of the floor, that
every Cut-0 `(owner, text)` pair whose owner is NOT in `AUTHORIZED_PROSE_OWNERS` is still present in
the final text (`:1006-1019`), compared on `(owner, text)` so a reflow of the line itself is a loss.
`AUTHORIZED_PROSE_OWNERS` (`:359-373`) is thirteen members: `<module>`, `__init__`,
`_index_entity`, `_project_identifiers`, `_index_identifiers`, `_remove_entity_from_indexes`,
`get_by_phone`, `resolve`, `resolve_all`, `find_or_create_stub`, the deleted legacy stub,
`resolve_or_create`, `_resolve_identifier`. **`PersonRepository.save` is not among them, and it owns
31 Cut-0 lines** (`prose_surface_cut0.json:2401-2543`), which I compared against the file: they are
byte-identical to `person.py:1155-1196` today, so the wall is green now and goes red on an edit.

Two of those 31 lines are the frames this item's own findings point at:

- `person.py:1174-1178` / `prose_surface_cut0.json:2466-2488` — "The write-back is the IDENTIFIER
  fields ONLY and never `name`", the paragraph that enumerates what the rider writes back
  (`entity.emails`/`phones`/`aliases`, `:1192-1194`). F11 requires that write-back to grow
  `whatsapp`, so the enumeration becomes incomplete.
- `person.py:1180-1184` / `prose_surface_cut0.json:2491-2513` — the `phones[]` in-place-mutation
  disclosure, ending "Stated because it is one field wider than the consumer audit's grep list was
  written against." **F11 cites this exact range as the model for WI-032's disclosure** ("the same
  class of disclosure WI-021 made for `phones[]` (`person.py:1180-1184`)"), and `### Examples of
  done` promises of the new refusal surface that "it says so". The natural way to honour either
  sentence is to extend that paragraph, and extending it rewrites its lines.
- Also frozen and also on this item's turf: `person.py:1169-1172` explains `whole_record=True`'s
  consequence as "both cross-field migrations run here exactly as they ran before". After Ruling B
  leg 2 there is a third consequence — a REFUSAL — and this is the sentence that would state it.

**Why this is blocking rather than a build-time surprise: three routes, all green, and the AC set
cannot tell them apart.** No leg of AC-1 through AC-5 asserts anything about `person.py`'s prose;
AC-3's `save` arm asserts refusal BEHAVIOUR only.

- **Build A — append only.** Add the disclosure as a NEW paragraph and leave all 31 Cut-0 lines
  byte-identical. Correct, green, and free — (e1) is a presence test, not an equality on the whole
  surface. Nothing in the document says this is the constraint.
- **Build B — add `PersonRepository.save` to `AUTHORIZED_PROSE_OWNERS`.** This is the move a builder
  reaches for on reading (e1)'s own failure message ("either it is a member the plan missed … or
  revert it"), and it is worse than widening another item's wall: clause (e2) asserts that every
  authorized owner has at least one Cut-0 line MISSING from the final text (`:1021-1030`), so
  authorizing `save` is RED until one of its 31 lines is DELETED. Buying the green requires
  destroying prose — and it is the same widen-another-item's-wall move rejected item 11 refused for
  the privacy wall, here with a mandatory deletion attached.
- **Build C — revert the prose.** Green on (e1), green on every criterion, and it ships a `save`
  whose docstring enumerates a write-back that has grown a field and explains a `whole_record=True`
  that has grown a refusal. That silently withdraws `### Examples of done`'s "and it says so" — the
  same defect shape F19 closed one artifact over, arriving through prose instead of through a
  detector.

**The fold, and it is one clause plus one touch-list line.** State in `### Effort`'s touch list that
`person.py`'s prose surface is frozen for every owner outside WI-024's thirteen, that `save` is such
an owner, and that this item's disclosures are therefore **APPEND-ONLY in that frame** — new
paragraphs, every Cut-0 line byte-identical, `AUTHORIZED_PROSE_OWNERS` and
`prose_surface_cut0.json` untouched (the WI-016 privacy-wall precedent: arm (a), leave the other
item's wall alone). Add `tests/test_identity_endgame.py` to the touch list as a wall the item joins
rather than a file it edits. One clause in AC-3's `save` arm or in `## Approach` step (2) pins it if
the spec-writer wants it asserted rather than instructed; Build B is worth a rejected item, because
it is the move (e1)'s own message invites and the one that costs a prose deletion.

**And the class, swept to its end so this is the last round of it rather than the seventh of
something.** Every wall in the suite that reads `person.py`'s text or behaviour, against every frame
this item edits. Two bit (above); the rest are CLEAN and I state them as such:

- **The Cut-0 resolve golden — CLEAN, and this was the one most likely to bite.**
  `test_resolve_is_one_cascade_and_matches_the_pre_cut_golden` (`:672-729`) replays every golden
  query through `repo.resolve` over a roster-seeded vault and asserts NO answer moved, with an
  exception list the item declares CLOSED ("Cut 3 gets none of its own", `:722-724`). WI-032 changes
  what enters `_phone_index` (AC-1) and inserts a cascade step (AC-2), either of which could move an
  answer — but `tests/fixtures/identity_endgame/roster.json` carries no `whatsapp` at all (grep over
  `tests/fixtures` returns the field only in `tests/fixtures/vault/*.md` and in the prose surface),
  so every seeded note is class Ø, contributes no phone-index entry from this field and no `jid:`
  key. The golden cannot move, and `repo.load() == len(ROSTER_TABLE)` with `skipped_count == 0`
  (`:346-347`) survives the tolerant reader. Worth saying out loud because the remedy a builder
  would reach for — re-recording the golden — is the one `:434-436` names as "the one way this
  oracle can be defeated".
- **WI-024's item-wall membership rows — CLEAN.** `test_identity_endgame_wall_membership_is_closed`
  (`:1101`) pins `non_completed_write_sites` over `ITEM_EDITED_QUALNAMES` (`:1065-1080`, which
  contains `_index_entity`, `_project_identifiers`, `_remove_entity_from_indexes` and `resolve_all`
  — four frames this item edits) and asserts `frontmatter_write_arms([person_path]) == []`
  (`:1156`). Both hold as long as this item adds no write capability and no frontmatter payload
  binding to `person.py`, which the design does not: the gate call and the writer delegation are
  already there. Named so it stays true rather than discovered.
- **The `ast` single-home equality — CLEAN, and it has a second home.** `:1134-1135` asserts it over
  package + tests, which is the same requirement F18 leg 5 carried from
  `tests/test_fixture_vault.py:1383-1386`; the new test module satisfies both by routing derivations
  through `tests/derivations.py`. No new obligation, but the wall is now known to be asserted twice.
- **`phone_index_iteration_sites` — CLEAN, with one constraint worth carrying.** `:642-644` asserts
  every phone-index iteration site is classified `materialized`. `_index_entity`'s change is an
  insert rather than an iteration, so nothing moves — but a builder who adds a loop over
  `self._phone_index` while making `_remove_entity_from_indexes` its exact inverse (AC-1) must wrap
  it in one of `MATERIALIZING_WRAPPERS` (`tests/derivations.py:1620`). One line in the touch list.
- **`resolve`'s no-index-reads clause — CLEAN.** `:692-698` asserts `PersonRepository.resolve` reads
  none of the four indexes directly. The new cascade step lands in `resolve_all` and the new public
  door is its own method, so the clause is untouched — and it is the guard that would catch a
  builder putting `get_by_identifier`'s lookup inside `resolve`.

### Non-blocking notes (fold if cheap; no round is owed for them)

1. **`_IDENTIFIER_PRIORITY` is a SECOND ordering for `whatsapp_jid` and the document never cites
   it.** `person.py:778` declares `_IDENTIFIER_PRIORITY = {"email": 0, "phone": 1, "whatsapp_jid": 1}`
   — whatsapp_jid TIES with phone for the Branch-A best-hit — and the class-body comment above it
   (`:772-777`) explains why: "A phone-bearing WhatsAppJID resolves like a Phone (same number → same
   person), so it shares phone's priority." AC-2 requires the new cascade label ranked AHEAD of
   `phone` (F15). The two are different frames — a typed-identifier best-hit inside
   `resolve_or_create` versus a cascade-label rank in `select_resolution` — so this is not a
   contradiction, and the tie is right for its frame because a phone-bearing JID and a phone ARE the
   same key. But the item's own principle is "no second spelling anywhere", one of the two orderings
   is about to change and the other is not mentioned in the document at all, so the spec should say
   which frame owns which ordering and why they differ. Note the comment that explains the tie is
   owned by `PersonRepository` (the class, `prose_surface_cut0.json:1681-1683`) — also NOT an
   authorized owner, so it is frozen too, which is the blocking finding's second member and the
   reason this note is worth a sentence rather than nothing.
2. **One more in-tree reader of `WhatsAppJID.parse`'s boundary, not on the touch list and green by
   design.** `tests/test_phone_normalization.py:105-124` pins `parse` over
   `447990558521@s.whatsapp.net`, `12345@lid` and the raising `12345@s.whatsapp.net`, i.e. the
   `MIN_DIGITS` boundary. Ruling A's recommended arm leaves `parse` untouched, so the module stays
   green and needs no edit — worth naming only because it is the module that goes red if anyone
   revisits Ruling A's alternative (b), and rejected item 7's cost line ("four call sites plus two
   test premises") does not count it.
3. **Carried, not re-raised.** Rulings A, B and C are untouched by everything above — the refused
   population, the repair door, the migration's repair pass and the report arm are all unchanged;
   what moves is where a disclosure's TEXT may be written. The ordering the document states — settle
   A and B, measure the census, then freeze the frame — is still right, and this finding is upstream
   of the FREEZE and downstream of the rulings.

### On the two classes the document has closed, and why this is not a third instance of them

Stated explicitly because it is the discriminant the factory reads. The fixture-plant class (every
plant literal × every contract of the frozen corpus, its manifest and the declarations those walls
derive from) is closed — F18's six legs re-drove clean where I checked them. The report-surface
class is closed — F19's fold is sound and its cost accounting survives the two walls it does not
name. This round's subject is neither: it is `obsidian_schemas/repositories/person.py`, the file the
item edits most, and the wall is a PROSE fixture rather than a plant or a detector. The generator is
the same one the conductor note named — an artifact treated as ordinary material without reading the
contracts it carries — and the sweep above runs it to the end over every wall in the suite that
reads that file, stating the five clean results as well as the two that bit, so the next round has
no unopened artifact of this class to find.

```verdict
gate: architect
verdict: REVISE
date: 2026-09-26
model: claude-opus-5
note: `PersonRepository.save`'s 31-line docstring is frozen verbatim by WI-024's prose wall — clause (e1) of `test_strangler_prose_class_is_closed_in_the_package` (`tests/test_identity_endgame.py:1006-1019`) requires every Cut-0 `(owner, text)` pair of an owner outside `AUTHORIZED_PROSE_OWNERS` (`:359-373`, which omits `save`) to survive, and `prose_surface_cut0.json:2401-2543` is byte-identical to `person.py:1155-1196` today — yet F11 names `person.py:1180-1184` as the home for the new write-back disclosure and `### Examples of done` promises the refusal surface "says so"; no AC touches that prose, so all three resolving builds are green and two are harmful (revert the disclosure, or authorize `save` and delete one of its lines to satisfy (e2)).
targets: AC-2, AC-3, #exploration-notes, #approach
prior: held
basis: original
findings: 1/3
```

## Architectural Review — 2026-09-26 (round 8)

**Recommendation: REVISE — one blocking finding, and it is the MIGRATION'S TERMINAL STATE rather than
another artifact whose contract nobody read**

Round 8, cold-start re-read at this worktree's HEAD (`c93006a` plus the seeded uncommitted delta, which
carries the round-7/red-team-round-6 fold). Every citation below was read in the code THIS round. **The
prior rounds' findings all HELD** — including round 7's, whose fold (F20) not only landed but CORRECTED
both arriving fences' line count, which I re-ran and confirm. What this round found is not the eighth
member of the wall-sweeping class: it is a contradiction between two conjuncts of AC-5 and the exit
numbers `## Approach` step (4) commits to the live bracket, and it is about what the vault LOOKS LIKE
when the migration has finished. No ruling is reopened, but the finding does correct a claim this
document makes about Ruling B's alternative arm.

### Trigger check

Fired for the reasons rounds 1–7 recorded: a new persistent frontmatter shape across ~1,170 live person
notes; significant extension of three core systems (the WI-021 gate, the WI-125 identifier index,
`resolve_all`); >3 files in different concerns; cross-system consumers; effort > 1 day.

### The prior findings, re-read against this tree

**Round-1 findings 1 and 2 — still CLOSED.** Re-verified rather than carried: `identifier.py:271-275`
raises on `None` and on empty through two lines with no blank branch, `:276` tests the `@lid` SUBSTRING,
`:278-281` tests `normalize_phone(s)` against `Phone.MIN_DIGITS`, and a JID suffix is tested nowhere —
so `WhatsAppJID.parse("+44 7739 341679")` still succeeds and only STORABLE refuses it. One fact worth
adding because it closes a latitude the STORABLE bullet leaves open in its wording: `.jid` holds the
**normalized** value, `str(raw).strip().lower()` (`identifier.py:266`, `:273`, `:277`, `:281`), so a
`jid_domain` property computed off `self.jid` is case-insensitive for free and `447700900321@S.WHATSAPP.NET`
is storable without a second rule. The bullet says "the raw value's JID DOMAIN"; the type has no raw
value to read, which makes the recommended spelling the only buildable one. Nothing to change.

**Round-3's class-Ø finding — CLOSED.** `person.py:318-320`'s `add()` returns on a `None`-or-blank raw
BEFORE calling any parser; `models.py:94` is still `whatsapp: str = ""`; `writer.py:333-337` sets a field
and there is no delete affordance. The six-cell table is a genuine partition, which I checked rather than
took: over a non-empty value the three booleans (parses? / `phone_digits` empty? / storable?) have exactly
five reachable combinations and the table names all five — a value like `447700900321@lid@s.whatsapp.net`
(the `@lid` substring with a storable LAST-`@` domain) falls in B by the table's own definition rather
than off the end of it.

**Rounds 4–6's plant, census and report-surface findings — CLOSED.** `_CONTAINER_KEYS` still excludes
`whatsapp` (`name_gate.py:84`); `_index_identifiers` still records a collision to `_conflict_sets` and
"never raises" (`person.py:336-344`), which is the fact F17 leg 3's silent-conflict argument rests on;
`_RESOLVE_CASCADE_ORDER` is still four labels (`person.py:145`) with `rank`'s unknown label falling to
`len(...)` (`:190-197`).

**Round-7's prose finding (F20) — CLOSED, and its own correction of the two arriving fences is right.**
Predicate re-run this round: `rg -c '"owner": "PersonRepository\.save"'
tests/fixtures/identity_endgame/prose_surface_cut0.json` → **29**, not the 31 the round-7 architect fence
and the red-team round-6 fence both state. I also checked the mapping F20 claims rather than the count
alone: `save`'s docstring is `person.py:1158-1189`, which is 32 lines carrying 5 blanks (`:1161`, `:1168`,
`:1173`, `:1179`, `:1185`), plus the two trailing comment lines at `:1195-1196` — 27 + 2 = 29. And the
fold's load-bearing claim that APPEND is FREE is true of the clause as written: (e1) builds
`final_pairs = {(r.owner, r.text) for r in final}` and asserts `unauthorized_losses == []` over Cut-0
pairs (`tests/test_identity_endgame.py:1006-1019`) — a PRESENCE test, so a new paragraph adds a pair
nobody reads and removes none. `AUTHORIZED_PROSE_OWNERS` (`:359-373`) omits `PersonRepository.save`, and
(e2) (`:1021-1030`) does demand an authorized owner LOSE a line, so rejected item 15's cost is real.

### Review (only where this round's finding bites)

**Fit, Duplication, Boundaries, Determinism, Reversibility, Generalization, Build-vs-extend, Prior art.**
Unchanged from rounds 2, 4, 5, 6 and 7 and re-spot-checked: `_index_entity` still feeds
`normalize_phone(entity.whatsapp)` into `_phone_index` unconditionally (`person.py:266-270`) with
`_remove_entity_from_indexes` its exact mirror (`:412-416`); the gate's refusal contract still admits no
note-derived value (`name_gate.py:142-174`). Liberal-for-reach / conservative-for-storage remains the
outside view — the standard identifier answer, not local machinery — and expand → migrate → defer-contract
remains the standard parallel-change answer, so no cited execution is owed.

**Reversibility — the dimension that moves this round, and it moves FORWARD rather than back.** F14
states the back-out correctly. What no round has asked is the mirror question: what does the vault look
like when the migration has SUCCEEDED? The answer the design forces is not the answer the document
commits to Dave, and the two are written three sentences apart.

### Blocking issue

**1. The gate refuses a class-D or class-E value in EITHER shape, so the migration cannot convert those
notes' shape at all — they are terminally scalar. Yet AC-5 leg (e), `## Approach` step (4)'s exit numbers
and `### Examples of done` all commit to "zero notes left in the scalar shape" in the same breath as
"the D+E residual reported and byte-identical". Those two conjuncts cannot both hold, and AC-5 mandates
the class-D plant that makes them collide, so NO build passes the criterion as written.**

The mechanism, in four read facts and one step:

- A shape conversion is a write that introduces `whatsapp`. For a class-D note the payload is
  `{"whatsapp": ["n/a"]}` — the list shape with one non-storable member, which AC-3 names explicitly
  ("a list containing one bad member among good ones") and refuses with **nothing written**.
- There is no arm that escapes it. AC-5 leg (b) asserts STRUCTURALLY that every write goes through
  `vault_io` *and through the gate*, no direct `write_text`; and the delta rule cannot help, because the
  delta rule (`name_gate.py:31-36`) keeps a stored-dirty note writable only for writes that do NOT
  re-introduce the field — and re-introducing the field is the entire content of a shape conversion.
- So the migration leaves every class-D and class-E note in the scalar shape, necessarily. That is not a
  build choice; it is forced by AC-3 plus AC-5 leg (b), and the document says as much where it describes
  the cells: class E is "left byte-identical by the migration like D", and AC-5 leg (e) asserts "its
  note's `whatsapp` bytes are asserted byte-identical".
- And the collision is present in AC-5's own fixture by mandate, not only on the live vault: leg (d)
  requires a planted class-E note asserted byte-identical after a repair-enabled run, and the plant list
  requires "at least one note per NON-Ø cell — A, B, C, D and E". So the class-D and class-E plants are
  scalar when the run ends, and leg (e)'s zero-scalar conjunct is red on the hermetic suite regardless of
  what the live census reports.

**Why this is blocking rather than a build-time surprise: every route out is red, which is worse than
buildable-two-ways.** Enumerated, because the four-way sweep is what shows the criterion is unsatisfiable
rather than merely ambiguous:

- **(a) let the gate accept D/E for the conversion** — red on AC-3, and it retires the item's own refusal.
- **(b) bypass the gate for the conversion** — red on AC-5 leg (b), which asserts the route structurally.
- **(c) CLEAR the D/E values so the note converts as class Ø** — the one route that reaches a
  zero-scalar vault, and it is silent data loss on exactly the population the item exists to preserve:
  rejected item 8's harm arriving through the migration instead of through the reader. It is caught, and
  I want to record WHY so the fold does not re-buy the guard: leg (c)'s TOTAL-value count per note (added
  in the first red-team round precisely so the parseable-only scoping could not become a licence to delete
  what it excludes) goes 1 → 0 and fails. That guard is load-bearing and, on this reading, it is the only
  thing standing between the criterion's own contradiction and erasure.
- **(d) honour byte-identity and report the residual** — the correct build, and red on leg (e)'s
  zero-scalar conjunct.

So the build-runner's real exits are to amend a FROZEN criterion (a D4b re-sign after Dave's signature,
which is exactly the cost this document elsewhere refuses to defer) or to reinterpret "zero notes left in
the scalar shape" as "zero of the notes the write COMMITS" — the charitable reading, which is correct and
which nothing in the text licenses. That second exit is the same defect SHAPE F19 closed one artifact over:
a clause satisfied by a reader's generosity rather than by construction, riding on a neighbouring
assertion. Here it is worse than in F19's case, because the clause is also an EXIT NUMBER: `## Approach`
step (4) commits it to the live bracket ("The exit numbers that matter: zero notes left in the scalar
shape, the class-C repair count equal to the census's class-C row, the D+E residual reported and
byte-identical"), and `### Examples of done` promises "the readback reports zero notes left in the old
shape". If the live class-D population is non-zero, the conductor performing the bracket cannot produce
the figure the item ships against and is left adjudicating it in prose — which is the one thing the
entry/exit discipline exists to prevent. If it happens to be zero, the figure works by luck, which is the
"stays green while unclassified" shape this document refuses everywhere else (it is the stated reason
class E is asserted rather than assumed).

**And it touches a claim about Ruling B, which is why it is not purely editorial.** AC-5 leg (d)'s
closing clause says a run invoked with repair disabled "leaves class C untouched and reports it (Ruling
B's alternative arm, so the criterion holds either way Dave rules)". It does not hold either way: under
the alternative arm class C is also unstorable at the gate, so class C joins the terminally-scalar
residual, the zero-scalar conjunct is further out of reach by the census's class-C count — the row the
document itself calls the load-bearing one — and N notes end the migration both scalar AND unsaveable
through the whole-record arms. Dave is entitled to that number when he rules on the repair, and today
the document tells him the criterion is arm-agnostic.

**The fold, and it is one clause plus one sentence in three places.** State the terminal state instead of
a number that assumes it away: the migration's exit condition is **zero notes left in the scalar shape
EXCEPT the reported D+E residual (C+D+E under Ruling B's alternative arm), whose scalar count EQUALS the
census's class-D and class-E rows** — still an oracle, still falsifiable, and now the same number the
`lint_vault` detector reports as an independent second witness, which is what AC-3's REPORT LEG was built
to buy. Scope leg (e)'s zero-scalar conjunct to the notes the write COMMITS, and add the conjunct that
keeps route (c) red by intent rather than by side effect: the migration never CLEARS a value to make a
note convert — clearing is a hand repair a person asks for through the delta arms (AC-3's CLEARING leg),
never something the run does. Then correct leg (d)'s arm-agnostic claim, and make the same edit in
`## Approach` step (4)'s exit numbers and in `### Examples of done`'s "zero notes left in the old shape".
One consequence worth stating in `## Exploration Notes` while the fold is open, because it is the honest
form of F7's "refusing the scalar form is a separate item or never": the tolerant reader can never be
contracted while any D+E note survives, so the CONTRACT phase of expand → migrate → contract is gated on
the residual reaching zero by hand, not on this item.

### Non-blocking notes (fold if cheap; no round is owed for them)

1. **The list flip turns one of the three whatsapp frames from loud to SILENT, and the touch list names
   the frame without naming the trap.** `### Effort` lists `_index_entity`, `_remove_entity_from_indexes`
   and `_project_identifiers` as frames to edit. Two of them fail LOUDLY on the new shape, which is fine:
   `normalize_phone` does `phone.split("@")` (`phone_normalization.py:52`), so `normalize_phone(<a list>)`
   raises `AttributeError` at `person.py:268` and `:414`. The third does not. `_project_identifiers` guards
   with `if entity.whatsapp:` and makes ONE `add(WhatsAppJID.parse, entity.whatsapp)` call
   (`person.py:330-331`); `add`'s blank guard tests `isinstance(raw, str)` (`:319`) so a list passes it, and
   `parse` does `s = str(raw).strip().lower()` (`identifier.py:273`) — so
   `WhatsAppJID.parse(["447700900321@s.whatsapp.net"])` SUCCEEDS with `phone_digits == "447700900321"`,
   because `normalize_phone` splits at the first `@` and strips non-digits and recovers the same digits from
   the list's repr. A build that forgets the loop therefore produces the CORRECT `phone:` key for a
   single phone-bearing value: AC-1's and AC-2's class-A legs pass. What catches it is the `jid:`-keyed
   cells (B and E get `jid:['15555550142@lid']`) and AC-5's two-JID note (one identifier where two are
   asserted). The suite does go red, which is why this is a note — but "iterate the list; never hand the
   list to `parse`" is one clause in the touch list, and it is cheaper than the diagnosis.
2. **After the fix the phone-pivot rule is computed in three frames from three separate `parse` calls,
   and the item's own principle is "no second spelling anywhere".** `_index_entity` (`:266-270`),
   `_remove_entity_from_indexes` (`:412-416`) and `_project_identifiers` (`:330-331`) each decide
   independently what a `whatsapp` value contributes, and after AC-1 all three need the same rule (only a
   non-empty `phone_digits` pivots). `_index_identifiers` already runs at the END of `_index_entity`
   (`:283-284`) over `_project_identifiers`' typed output, so the phone-index insert can be DERIVED from
   the projected identifiers rather than re-parsed beside them. AC-1's inverse-over-the-same-table
   assertion pins the behaviour either way, which is why this is a note and not a finding — but the spec
   should say which frame owns the pivot rule, or a builder writes it three times and the next item that
   widens it finds two of them.
3. **Carried, not re-raised.** Rulings A and C are untouched by everything above. Ruling B is not
   reopened either — the blocking finding does not change what the migration DOES to any cell, it changes
   what the document claims the vault looks like afterwards and corrects a sentence that tells Dave the
   criterion is indifferent to his answer on the repair. The ordering the document states — settle A and
   B, measure the census, then freeze the frame — is still right, and this finding is upstream of the
   FREEZE and downstream of the rulings.

### On the classes this document has closed, and why this is not another instance of them

Stated because it is the discriminant the factory reads. The three classes rounds 4–7 closed are
artifacts whose CONTRACTS were unread: the frozen corpus and its manifest (F17, F18), a tool's report
capability priced off a docstring (F19), and a package file's prose surface (F20). I re-drove each where
its load-bearing facts were cheap to check and all three hold. This round's subject is not a fourth
artifact and not a fixture: it is a contradiction between two conjuncts the document has carried since
its first draft — AC-5 leg (e)'s zero-scalar exit number against the byte-identity guarantee the class
table and leg (e) itself give class D and class E — made visible by nothing more than asking what the
vault looks like after a successful run. It is reachable from the criteria text alone without opening
another module, which is why it is `basis: original` and why the sweep that closed the artifact class
could not have surfaced it.

```verdict
gate: architect
verdict: REVISE
date: 2026-09-26
model: claude-opus-5
note: AC-3 refuses a class-D/E value in BOTH shapes and AC-5 leg (b) asserts every migration write goes through the gate, so those notes are TERMINALLY SCALAR — yet AC-5 leg (e), `## Approach` step (4)'s exit numbers and `### Examples of done` all commit to "zero notes left in the scalar shape" alongside "the D+E residual reported and byte-identical", and AC-5 itself mandates the class-D plant that collides them; all four routes out are red (accept → AC-3, bypass → leg (b), clear → leg (c)'s total-value count, honour byte-identity → leg (e)), so no build passes and the real exits are a D4b re-sign or silently reinterpreting the exit number the live bracket ships against — and leg (d)'s claim to hold "either way Dave rules" is false, because under Ruling B's alternative arm class C joins the residual.
targets: AC-5, AC-3, #approach, #exploration-notes
prior: held
basis: original
findings: 1/3
```

## Conductor Note — 2026-09-27 (round-budget ESC-WI-032-idea-round-budget-9c211f1b: Dave authorized one more round window; this carries revise-cap ESC-WI-032-idea-revise-cap-1a372790's fold so the window cannot lose it)

Read this as the instruction for this round's ideation-partner. Nothing is signed at `idea`; Rulings A,
B and C stay Dave's at the grounding door — do NOT reopen them. This fold changes no ruling; it makes
the exit numbers honest under EITHER arm of Ruling B.

**The finding (architect round 8 + ac-red-team round 7, converged).** AC-3 refuses a class-D/E value in
both shapes and AC-5 leg (b) routes every migration write through the gate, so D/E notes are TERMINALLY
SCALAR — yet AC-5 leg (e), `## Approach` step (4)'s exit numbers and `### Examples of done` promise
"zero notes left in the scalar shape" AND "the D+E residual reported and byte-identical". AC-5's own
class-D plant makes both conjuncts unsatisfiable, so no build passes.

**The fold — the exit numbers become a PARTITION, not an absolute.** (i) Zero notes left in the scalar
shape OUTSIDE the residual. (ii) The residual R = the notes whose value the STORABLE predicate refuses,
each REPORTED by AC-3's detector and BYTE-IDENTICAL on readback. (iii) R's membership is per Ruling
B's arm — D+E under the recommended arm (class C repaired key-preservingly), C+D+E under the
alternative arm — and leg (d) says exactly that instead of claiming "either way" holds unchanged.
(iv) The reconciliation identity dry-run == write == readback holds over the triple
(scalar-outside-residual, migrated, residual); the run exits non-zero on any disagreement. Restate the
same partition verbatim in AC-5 leg (e), `## Approach` step (4), `### Examples of done` and the live
bracket's exit row (`docs/wi-032-whatsapp-live-baseline.md`, counts only). The class-D plant then
satisfies leg (e) as a residual member, not a violation.

**Close the class.** The generator is an ABSOLUTE promise ("zero", "every", "all", "never") stated over
a population that another criterion carves a residual out of. Sweep every absolute in every AC desc,
`## Intent`, `## Approach` and `### Examples of done`; for each, say which population it ranges over
and which residual (if any) is excluded — or scope it. DECLARE the sweep in `## Exploration Notes`.

## Architectural Review — 2026-09-27 (round 9)

Round 9 for this gate, cold-start at this worktree as the drive seeded it — git HEAD `8b9b95e` plus the
seeded uncommitted delta, which carries the round-8 architect fence, the round-7 red-team fence and the
conductor note's fold. Read with Read/Grep/Glob and no shell; re-run any predicate below to contradict a
number. Rulings A, B and C are Dave's and nothing below touches them — no finding here is a fourth
question for him.

**Verdict: PROMOTE to architected.** The round-8/red-team-7 blocking finding is CLOSED, the fold that
closed it is correct in substance at every place it lands, and the approach itself — which has not
changed since round 1 — is sound. What survives this round is five non-blocking notes, none of which
leaves the item buildable two ways and none of which the spec-writer has to redesign anything to absorb.

### Trigger check

Fires on five: it establishes a new persistent data shape (`whatsapp` scalar → list across ~1,170 live
notes); it touches far more than three files in different concerns (`identifier.py`, `models.py`,
`name_gate.py`, `repositories/person.py`, `scripts/lint_vault.py`, the reader, six test modules, two
frozen fixtures); it significantly extends a core system (the WI-021 write gate and the WI-125 identifier
index); it is a cross-system change by construction (HAL9000 and exocortex inherit the field's type); and
effort exceeds one day by a wide margin. No skip pattern applies.

### The prior findings, re-read against this tree

**Round 8's blocking finding — CLOSED, and the fold is right in all four places it had to land.** I
re-derived the defect before checking the remedy: `name_gate.py:31-36` reads verbatim "A stored-dirty note
stays writable for every write that does not re-introduce its name" (read this round), so the delta rule
cannot excuse a shape conversion, whose entire content IS re-introducing the field; AC-5 leg (b) leaves no
carve-out; so class D and class E are terminally scalar and the old absolute was unreachable. The fold:
`## Exploration Notes` declares **THE TERMINAL-STATE PARTITION** once with both travelling conjuncts
(never-clears, and reconciliation over the triple rather than one number); AC-5 leg (e) is rewritten to it
and carries the never-clears assertion per plant, so rejected item 17's erase route is red BY INTENT and
not as a side effect of leg (c)'s total-value count; leg (d) now asserts BOTH arms of Ruling B and states
that `|R|` grows by the census's class-C row under the alternative, which is the number Dave was missing;
AC-4 leg (c) is scoped to writes that SUCCEED and introduce the field, with the residual's silence
asserted both ways over a planted class-D note; `## Approach` step (4) and `### Examples of done` restate
the partition; and **THE ABSOLUTES SWEEP** declares the class closed with its clean rows stated as clean.
Checked for the failure mode a fold of this kind invites — an exit number now satisfiable but vacuous —
and it is not: part 3's zero is falsifiable, and it is taken by a different tool from `|R|` (the AC-3
detector's issue count), so the two must agree rather than one reporting on itself.

**Round 8's two non-blocking notes — both folded, both into `### Effort` where they belong.** The
`_project_identifiers` silent-wrong-answer trap is now a touch-list clause, and I re-verified the
mechanism it rests on: `add`'s blank guard is `raw is None or (isinstance(raw, str) and not raw.strip())`
(`person.py:319`, a list passes it) and `parse` does `s = str(raw).strip().lower()` (`identifier.py:273`),
so a list's repr yields the same digits through `normalize_phone`'s first-`@` split. The phone-pivot
single-spelling note is folded as a named `### Effort` bullet that says which frame should own the rule.

**Rounds 1–7's four closed classes — still HELD**, spot-checked where their load-bearing facts were cheap:
`WhatsAppJID.parse` stores the NORMALIZED string and holds no raw value (`identifier.py:266`, `:273`,
`:277`, `:281`), which is what makes `jid_domain` off `self.jid` the only buildable spelling and
case-insensitivity free; `models.py:94` is still `whatsapp: str = ""`; `_RESOLVE_CASCADE_ORDER` is still
the four labels at `person.py:145` with an unknown label ranking last at `:196`; `check_structural` is at
`scripts/lint_vault.py:355` with `auto_fixable: bool = False` at `:96` and WI-029's own arm already
carrying the "stays at its False default" comment at `:364`, so the REPORT LEG copies a shape that is
there; and `rg -c '"owner": "PersonRepository\.save"' tests/fixtures/identity_endgame/prose_surface_cut0.json`
→ **29**, confirming round 7's corrected figure against the two arriving fences' 31.

### Review (only the dimensions this round moved, plus the two my role makes blocking)

**Fit.** Unchanged and good: two predicates on one frozen dataclass in one module, the gate as the wall
(not the field type), refusal-by-attribute per the WI-021 contract, a report-only detector copied from
WI-029's, and expand→migrate→(later)contract with a tolerant reader. Every one of those is this repo's
own existing pattern rather than an import.

**Duplication.** The item's own principle — one spelling of "well-formed" — holds after the fold. The one
place it is still carried by a note rather than a criterion is the phone-pivot rule across three frames;
AC-1's inverse-over-the-same-table assertion pins the behaviour either way, so the note is the right
instrument.

**Reversibility.** F14's position is honest and the bracket is the right container. One qualifier is
missing; see note 3.

**Cost & maintenance.** This is where the item is largest and where note 4 lives. Nothing about the
library change is expensive; the migration's write population is, and the document never says so.

**Prior art (outside view) — and both of my role's blocking conditions are discharged.** The item does not
build machinery around a subtracted capability: expand → migrate → contract with a tolerant reader IS the
standard answer for a schema change over shared mutable state, and the document reaches it by the standard
reasoning rather than by working around something. The one place the world's answer differs is that the
usual companion to a tolerant reader is a VERSION STAMP on the record, so a reader knows which shape it
holds instead of sniffing. This item deliberately does not add one — and the deferral is not a bare
recommendation: WI-010 already exists, already parked, with its un-park criterion stated as "the first
real schema migration that must walk the vault" (`docs/migration-support.md:20-22`), which is this
migration. The probe item is minted and named, so condition (b) is met. On condition (a): "a live vault
migration with no atomic window" has recurred (WI-016, WI-023/125, WI-029), but this item ACCEPTS the
constraint rather than compensating for it, so recurrence does not make the dimension blocking here.

### Notes (non-blocking — fold if cheap; no round is owed for any of them)

1. **`## Approach` step (4)'s exit triple is not the partition's triple, while claiming to be it
   verbatim.** The conductor note asked for the same partition restated in four places. Three of them
   match: `## Exploration Notes` states (MIGRATED, R, zero-outside-R), and AC-5 leg (e) and step (4)'s
   reconciliation sentence both state it as (scalar-outside-R = 0, migrated, R) — a different ordering of
   the same three parts, which is fine. The fourth does not: step (4)'s "**exit numbers that matter …
   stated in the bracket's exit row exactly as `## Exploration Notes` states them**" then lists (1)
   zero-outside-R, (2) `|R|`, (3) the class-C REPAIR COUNT — which substitutes a sub-count of MIGRATED for
   MIGRATED itself and drops the count of notes the run actually converted. So the hermetic oracle
   reconciles over a triple the live bracket's exit row is told not to carry, under a sentence asserting
   they are the same triple. Non-blocking because both triples are honest, computable and
   non-contradictory, and AC-5's own text is explicit about its own — nothing is buildable two ways. The
   fix is one clause: make MIGRATED part (2) of the exit row and keep the repair count as its named
   sub-count, which is what step (4) plainly means.

2. **The census's class-Ø row is asserted to equal the shape-only conversion count, and it cannot be —
   the same shape as F21's defect, one cell over, in the artifact the live bracket is compared against.**
   `## Write Targets`' census precondition defines class Ø as "an absent key, `""`, YAML null or `None`"
   and then says of that row "which is also the count of notes the migration converts SHAPE-ONLY". But
   `## Approach` step (4) names the shape-only conversion as `""` → `[]` only, and a note with the key
   ABSENT needs no write at all (the partition's own opening sentence ranges over
   "`whatsapp`-carrying" notes, which excludes it). So the two numbers differ by the absent-key count, and
   the difference lands on a figure a conductor must produce against the census at the exit row — the
   prose-adjudication position F21 was folded to remove. It does not touch AC-5's reconciliation identity,
   which is internal to the run (dry run vs write vs readback), and only `|R|` is tied to census rows, so
   nothing is unsatisfiable. The fix is one clause in the precondition's `why:`: the class-Ø row reports
   its two spellings separately (key-present-but-empty, key-absent), and the shape-only conversion count
   is the first of them.

3. **F14's back-out exactness has a SECOND qualifier and names only the first.** F14 and `## Approach`'s
   back-out paragraph both say the reverse migration "is exact only while no note has gained a second
   JID". Under Ruling B's recommended arm there is a second inexactness present on day one: the class-C
   repair rewrites the stored spelling (`"+44 7739 341679"` → `"447739341679@s.whatsapp.net"`), so a
   list→scalar reverse returns the CANONICAL form and not the pre-migration bytes, for every note in the
   census's class-C row. The harm is semantically null — AC-5 leg (d) asserts the repair key-preserving,
   so nothing resolves differently and the reverse arguably lands on the better spelling — which is why it
   is a note. But the conductor performing the bracket is entitled to hear "exact up to the class-C
   repair, whose reverse is its canonical spelling" rather than "exact", and under Ruling B's alternative
   arm (repair declined) the qualifier disappears entirely, which is itself worth one sentence.

4. **~95% of the migration's writes are semantically empty, and the document never asks whether they
   should happen.** Class Ø is 21 of the 22 `whatsapp`-carrying fixture notes (F6), so on the live corpus
   the overwhelming majority of the ~1,170 notes the migration walks carry `whatsapp: ""`, which the
   tolerant reader ALREADY presents as the empty collection — the conversion changes no resolution, no
   key, no model value, and no consumer-visible behaviour. The partition requires it anyway (part 3's zero
   ranges over the scalar shape, and `""` is a scalar), so a build has no latitude. What that buys is
   cosmetic uniformity the tolerant reader makes invisible; what it costs is turning the riskiest step in
   the item — a write pass over the live person corpus — from tens of notes into ~1,170, plus the same
   multiple on the reverse if the back-out is ever taken. Not blocking, and deliberately not raised as a
   fourth ruling: the decision point already exists and is already load-bearing, because the census
   precondition requires the class-Ø count and `## Approach` step (4) puts the dry run in front of Dave
   before the write, so he can say "leave those alone" with the number in hand. The gap is only that the
   document never poses the question, so nobody is expecting it. One sentence in step (4) naming class Ø
   as the shape-only population and flagging it as the one part of the run with no semantic effect is
   enough; if Dave does elect to skip it, part 3's zero becomes "zero outside R and outside class Ø" and
   the tolerant reader is what makes that safe — which is a one-line consequence, not a redesign.

5. **The absolutes sweep is substantially but not literally exhaustive over the AC descs, and the
   unswept members are all clean — stated so an unswept absolute is not mistaken for a missed one.** The
   sweep's 27 rows cover `## Intent`, `## Approach`, `### Examples of done` and the AC absolutes that
   carry a residual, which is where the defect class lives. Four absolutes inside AC descs are not
   itemized: AC-1's "`_remove_entity_from_indexes` is the exact inverse over the same table, so a refresh
   leaves no orphan key" and "the corpus must hold NO class-A and NO class-C member on `@Thrandell
   Ibberly.md`"; AC-4 leg (a)'s "all present the empty collection"; and AC-5 leg (d)'s "ONLY values whose
   `phone_digits` is non-empty are ever rewritten". I read each against the partition and each is TOTAL
   over its stated population with no residual carved out by any other criterion — which is why none of
   them bit and why this is a completeness note rather than a finding. Adding the four rows costs nothing
   and makes the sweep's own claim to be a sweep true.

### On the four classes this document has closed, and why I am not opening a fifth

Stated because it is the discriminant the factory reads, and because this is the round window Dave
authorized. Rounds 4–5 closed the fixture-plant class (F17, F18), round 6 the report surface (F19), round
7 the prose surface (F20) and round 8 the absolutes class (F21). The first three were artifacts whose
contracts nobody had read; the fourth was a contradiction between two of this document's own conjuncts. I
went looking for a fifth generator of the same rank and did not find one. The five notes above are not
one: notes 1, 2 and 5 are internal-consistency gaps in the round-8 fold's OWN material — basis
`folded-material`, each a single clause, none of them changing what any build does or what any criterion
asserts; note 3 is a missing qualifier on a statement that is already correct in its conclusion; note 4 is
a cost question whose decision point the document already built. A round spent on any of them would buy
the same outcome this fence already reaches, which is the treadmill shape the `prior:`/`basis:` keys exist
to distinguish from a ladder. The right next move is not a ninth fold — it is Dave at the grounding door
on Rulings A, B and C, then the two preconditions measured, then the frame frozen. The five notes are
cheap before that signature and a D4b re-sign after it, which is exactly the window they should be folded
in, and the spec-writer is the right hand for them.

```verdict
gate: architect
verdict: PROMOTE
date: 2026-09-27
model: claude-opus-5
note: The round-8/red-team-7 blocking finding is closed correctly — the TERMINAL-STATE PARTITION replaces the unsatisfiable zero-scalar absolute in all four places, carries the never-clears and triple-reconciliation conjuncts so the erase-to-convert build is red by intent rather than by side effect, corrects AC-5 leg (d) to assert both arms of Ruling B, scopes AC-4 leg (c), and declares the absolutes class closed by sweep; I re-derived the defect from `name_gate.py:31-36` and AC-5 leg (b) before checking the remedy, re-verified rounds 1–7's four closed classes in code (including `prose_surface_cut0.json`'s 29 `save` lines and `parse`'s normalize-then-store at `identifier.py:266-281`), and found no fifth generator of that rank — the five surviving notes are single-clause consistency gaps in the fold's own material plus one unpriced cost, none of them leaving the item buildable two ways, so the right next move is Dave on Rulings A/B/C rather than a ninth fold.
```

## AC Red-Team — 2026-09-27 (round 8)

Rulings on record:
Rulings A, B and C stay Dave's, unchanged by everything below; none of it reopens a question for him.

Round 8 for this gate, cold-start at this worktree's HEAD (`8b9b95e` plus the seeded uncommitted
delta, which carries the round-7 red-team fence, the round-8 architect fence, the conductor note's
fold, and the round-9 architect fence). Read in the prescribed order: `## Intent`, `### Examples of
done`, `## Problem / Motivation` and the exploration sections, then `## Acceptance Criteria` last.

### The prior rounds' findings, re-read against this tree

**Rounds 1–6: still HELD**, spot-checked directly in code rather than carried on the strength of
earlier fences. `identifier.py:270-281` still raises on `None` and on empty through the same two
lines it raises on `"n/a"` with, tests the `@lid` SUBSTRING (not a suffix) at `:276`, and stores the
NORMALIZED string (`str(raw).strip().lower()`) with no raw value retained — which is what makes a
`jid_domain` read off `.jid` the only buildable STORABLE spelling (round-8 architect note, unchanged).
`name_gate.py:84`'s `_CONTAINER_KEYS` still excludes `whatsapp`. `person.py:145`'s
`_RESOLVE_CASCADE_ORDER` is still four labels. AC-1's WHERE clause still pins the round-trip
representative to the storable `15555550142@lid` with the class-C member on a non-representative
note. AC-3 still carries the REPORT LEG's five assertions, the CLEARING and CLASS-Ø legs, and the
APPEND-ONLY clause's three conjuncts — and I re-ran the round-7 correction myself:
`rg -c '"owner": "PersonRepository\.save"' tests/fixtures/identity_endgame/prose_surface_cut0.json`
→ **29**, confirming the figure against the two earlier fences' 31.

**Round 7's finding (the terminal-state contradiction) — CLOSED, and I re-derived the mechanism
before reading the fold rather than trusting the architect's round-9 fence.**
`name_gate.py:31-36` reads verbatim "A stored-dirty note stays writable for every write that does
not re-introduce its name" — so the delta rule cannot excuse a shape conversion, whose entire content
IS re-introducing `whatsapp`, and AC-3's refusal of a non-storable value in both shapes therefore
makes classes D and E terminally scalar exactly as claimed. Against that, the current AC text: AC-5
leg (e) is now the three-part COUNTS-RECONCILE-OVER-THE-TERMINAL-STATE-PARTITION oracle (scalar-
outside-R = 0; MIGRATED; RESIDUAL R with membership per Ruling B's arm and `|R|` tied to the census),
carries the never-clears conjunct stated as an assertion rather than a side effect of the total-value
count, and — the leg (d) correction — now states BOTH arms of Ruling B rather than "either way",
with the alternative arm's R growing by the census's class-C row. AC-4 leg (c) is scoped to writes
that succeed and introduce the field, silent (not violated) on R. `## Exploration Notes` declares
THE TERMINAL-STATE PARTITION once (verified at the text I read directly, not summarized) and THE
ABSOLUTES SWEEP table naming population and excluded residual for every absolute in the AC descs,
`## Intent`, `## Approach` and `### Examples of done`. `## Approach` step (4) and `### Examples of
done` both restate the same partition rather than the old flat "zero notes left in the scalar
shape". No route out of the four the round-7/round-8 fences enumerated (accept, bypass, clear,
honour-byte-identity-and-report) is still red on the current text — the fourth (honour byte-identity
and report) is now what leg (e) asserts, and it is buildable.

### This round's attack

Read `## Intent` first and the ACs last, per the gate's own discipline, and ran the failure-class
list against the CURRENT criteria text rather than against the history of what earlier rounds found:

- **Tautological / zero-implementation / single-literal-gameable** — none found. AC-1 through AC-5
  each compute their expected value by calling `WhatsAppJID.parse` and the STORABLE predicate against
  a table with pinned, reserved-block-clean literals per cell; the frozen corpus alone (zero `@lid`,
  zero unparseable, zero storable-JID members) would green a no-op build, which is exactly why the
  plants are mandated and pinned rather than left to a test author's choice.
- **Uncovered invocation layer** — AC-3's arm set is DERIVED from the tree by the existing WI-021
  sweep and asserted in scope by equality, plus `save` and `write_markdown_file(entity=…)` named
  explicitly as the whole-record-projection arms the derivation excludes by design. I don't see a
  door left uncovered.
- **Mocked oracle at the seam that matters** — AC-5's migration runs "through `vault_io` and through
  the gate," and leg (c)'s readback is explicitly a RE-READ from note bytes rather than through the
  migrating process's own cache. That guard is exactly the one WI-144's class warns is easy to lose;
  it is present and stated as its own clause.
- **Mutually unsatisfiable ACs** — this was round 7's finding; re-read above and closed.
- **Class-closing AC with a hand-picked fixture / derived sweep with no oracle** — these are the
  classes rounds 1, 4 and 5 closed (F16, F17, F18); re-spot-checked this round via AC-1's WHERE
  clause and AC-5's plant list, both unchanged since round 8's architect re-verification, and still
  naming per-cell reserved-block-clean literals rather than illustrative ones.
- **Drift from Intent** — `## Intent`'s four promises (refuse at the boundary; resolve both forms
  liberally; never silently drop what's already wrong; emptying is always allowed) each map onto a
  named AC leg (AC-3; AC-2; AC-4(b)/AC-3's CLEARING and REPORT legs; AC-3's CLASS-Ø leg), and THE
  ABSOLUTES SWEEP now states the population and residual for every one of those sentences rather than
  leaving the mapping to be inferred. No drift found.
- **Check that cannot execute** — all five `check:` values are bare test function names, present and
  distinct.

I looked specifically for a defect IN the round-7/round-8 fold's own new material — the shape WI-139
warns a fold can introduce — since that is where a fresh defect is likeliest to hide from a reader who
trusts the fold's own summary. The five things the architect's round-9 fence flagged as non-blocking
(the exit-triple ordering mismatch in `## Approach` step 4, the census class-Ø row's absent-key vs
empty-key conflation, the missing second back-out qualifier, the ~95%-empty-writes cost question, and
the sweep's four unitemized-but-clean absolutes) are all in prose outside the criteria text itself —
`## Approach`, `## Write Targets`' precondition `why:`, and `## Exploration Notes`' back-out
paragraph — and none of them is reachable from any AC's `check:`. I confirmed that directly rather
than taking the architect's word for it: AC-5's reconciliation identity is stated entirely in terms of
the dry run's own counts, the write's own counts and the readback's own counts, never in terms of the
`## Write Targets` census precondition or `## Approach` step (4)'s prose — so a build satisfying every
AC in this document is unaffected by any of those five notes, and none of them makes an AC gameable,
tautological, or unbuildable. They are the spec-writer's clean-up, not a red-team finding.

No other material defect survived this round's attack on AC-1, AC-2, AC-4, or the read/write and
resolution legs. Rulings A, B and C are untouched.

```verdict
gate: ac-red-team
verdict: PROMOTE
date: 2026-09-27
model: claude-sonnet-5
note: Round 7's terminal-state contradiction is closed — re-derived the mechanism independently from `name_gate.py:31-36` before reading the fold, confirmed AC-5 leg (e)'s three-part partition oracle, the never-clears conjunct, leg (d)'s both-arms correction, and AC-4 leg (c)'s scoping are all present in the current criteria text and reachable from named `check:`s; re-verified rounds 1–6's closed classes directly in code (`identifier.py:270-281`'s parse/store behavior, the 29-line `prose_surface_cut0.json` count); ran the full failure-class hunt against the current AC text and found no tautological, zero-impl-satisfiable, gameable, uncovered-layer, mocked-oracle, unsatisfiable-pair, or class-closing defect; the architect's five round-9 non-blocking notes sit in prose outside every AC's `check:` and don't touch buildability.
```
