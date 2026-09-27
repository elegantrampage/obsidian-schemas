---
id: WI-032
title: Validate the WhatsApp JID shape at the person boundary
project: obsidian-schemas
stage: done
created: 2026-09-21
last_touched: 2026-09-27
stage_changed: 2026-09-27
touched_by: session
tags: []
depends_on: []
transitions: ["idea>exploring@2026-09-27@session", "exploring>specced@2026-09-27@porter", "specced>ready@2026-09-27@porter", "ready>building@2026-09-27@porter", "building>done@2026-09-27@porter"]
---

# Validate the WhatsApp JID shape at the person boundary

### Archived Rounds

<!-- archive-split: machine-maintained pointer; do not edit -->
Settled gate rounds for this item live in `docs/whatsapp-jid-value-type-rounds.md` — every round at a conveyor door
this item has already advanced past, byte-for-byte, append-only, never rewritten. READ ON DEMAND
ONLY: each gate's latest standing round is still in this document, so nothing needed to advance this
item is in the drawer. Open it only to read a settled round's full reasoning.

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
| AC-1 "`_remove_entity_from_indexes` is the exact inverse over the same table, so a refresh leaves no orphan key" | every cell of the six-cell table | none — total, and `## Design` §5 makes it total by DERIVING both directions from one projection | row added (spec-writer, 2026-09-27) |
| AC-1 "the corpus must hold NO class-A and NO class-C member on `@Thrandell Ibberly.md`" | the one person `roundtrip_representative` | none — total over a one-member population asserted unique at `tests/test_fixture_vault.py:689-695` | row added (spec-writer, 2026-09-27) |
| AC-4 (a) "all present the empty collection" | the three class-Ø READ spellings (empty value, absent key, bare valueless key) | none — total; `[]` is the fourth spelling and is already the empty collection | row added (spec-writer, 2026-09-27) |
| AC-5 (d) "ONLY values whose `phone_digits` is non-empty are ever rewritten" | every value the repair pass considers | none — total, and it is what keeps class E out of the repair | row added (spec-writer, 2026-09-27) |

**The four rows above were added by the spec-writer** (architect round-9 note 5): the sweep's 27 original
rows covered every absolute that carries a residual, which is where the defect class lives, and these four
sit inside AC descs and were read against the partition and found TOTAL over their stated population. They
are stated so an unswept absolute is not mistaken for a clean one — nothing about any build changes, and no
criterion text moved.

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
- **It must declare NO `shape_classes`/`verdict`.** The census verdict loop reaches the gated door on ONE
  of its three arms — corrected 2026-09-27, one word narrower than this leg first stated it: the loop
  iterates every shape-class specimen (`tests/test_fixture_vault.py:856-861`) but only the
  `verdict.kind == "refusal"` arm writes the whole declared field set through `write_markdown_file` and
  asserts `exc.pattern == verdict.pattern` (`:866-878`), while the `cleaned` arm calls
  `clean_person_name` and touches no note and the `loads` arm re-parses the corpus note without writing
  (`:879-887`). A non-storable `whatsapp` on a REFUSAL specimen makes the refusal that fires depend on
  where the new gate arm is placed relative to the name arm — today the name refusal is step 3 of
  `gate_write` and precedes every address arm (`name_gate.py:348-368`), so the assertion would still
  pass, but "passes because the new arm was placed second" is not a property to leave resting on a
  builder's choice of insertion point. **The constraint stays scoped to EVERY shape-class specimen
  rather than being narrowed to the refusal arm, and the narrowing is declined deliberately:**
  `spec.verdict` is asserted non-None for every shape-class specimen (`:859-861`) and which arm a
  specimen takes is ANOTHER item's declaration — a `loads` specimen re-declared as a `refusal` would put
  the insertion-point question straight back without touching this document. So the conservative
  reading is the one the WHERE clause carries, and AC-1's frozen desc states it un-narrowed for the same
  reason; a receiver with no verdict at all makes the question unaskable under either reading.

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

**RULED — Dave, 2026-09-27 (in-session: "proceed with A", i.e. the recommendation).** The recommended arm: two predicates on one type — `parse` unchanged for reach, a derived STORABLE property (`jid_domain` in the closed set `{s.whatsapp.net, lid}`) read only by the write door. A bare telephone number is refused at every write arm and still resolves on lookup. The census (`docs/wi-032-whatsapp-corpus-census.md`) prices it: 82 bare numbers live today, every one repaired key-preservingly by the migration under Ruling B, so the door refuses nothing on the live vault on the day it lands. The ACs stand on this arm — frozen by Dave's signature in the same move (ac_hash `dd772c1183de`). Landed by the conductor.

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

> **SUPERSEDED AS A TOUCH LIST — read `## Write Targets` for the binding one (spec-writer, 2026-09-27).**
> Everything below stands as effort, dependency and constraint reasoning, and the constraints it carries
> (the prose freeze, the three walls the new modules join, the `_project_identifiers` iteration trap, the
> one-frame phone-pivot rule, the itemized fixture work) are folded into `## Design` and the
> Implementation Plan. What is NOT binding is its "expected touch list", which the spec resolved FOUR ways
> it did not anticipate, each for a reason stated where it lands: **`README.md` is off the list entirely** —
> the project root is outside this project's `write_authority` (`pipeline-runners.yaml:32-33`), it is
> conductor-owned session-end work, and nothing in the build depends on it, because `:52` is a field-NAME
> list the type change does not touch and `:238`'s documented `get_by_phone` route still works
> (Prerequisite 5); **`tests/test_identity_index.py`, `tests/test_repositories.py` and
> `tests/test_parser.py` are PREDICTED GREEN and run rather than edited** — the tolerant reader accepts
> their scalar `whatsapp` fixtures and both stored class-C values are phone-bearing, so they still pivot
> (`## Verification`, Integration); and **the "migration entry point" is a named file with a declared
> home**, `scripts/migrate_whatsapp_to_list.py`, chosen for two measured wall reasons rather than by
> convention (`## Design` §7). And the list names no `tests/derivations.py`, which IS a write target: the
> containment wall AC-5 requires is VACUOUS over a new module until `MUTATING_DRIVE_VAULT_POSITIONS` names
> its mutating entry point (`## Design` §8). Do not reconstruct the touch list from this bullet — count
> nothing here and read the `writes` fences, which are what the driver probes and the review-level selector
> reads.

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

**And the WIDER disclosure, which is the CARDINALITY break rather than the refusal break** (data-audit note
(ii), folded by the spec-writer into the ship condition where it belongs — the audit measured and sequenced
it, and this paragraph disclosed only the refusal half). The consumer audit's ordered break list is SEVEN
sites (`docs/wi-032-consumer-audit.md:227-239`), all of them tripped by the VALUE becoming a list and none of
them by the door refusing anything; the first THREE are the ones the bracket's entry row names individually:
`orchestrator/src/invariants.py:663-665` goes red vault-wide, `HAL9000/.../contacts.py:41,50` starts 500ing,
and `orchestrator/bin/merge-duplicate-persons.py:380-384` regex-reads the `whatsapp` LINE, merges scalars and
re-emits `whatsapp: "<v>"` through `Path.write_text` — bypassing `PersonRepository` and therefore the gate
entirely, which is the one site that can collapse a migrated list back to a single scalar or clear it to `""`
when its single-line regex misses a block list. That site is a NAMED EXCLUSION from `## Intent`'s "Every
writer refuses it at the boundary" (the absolutes sweep scopes that universal to the package's own arms) and
it is already on the WI-029 divergence-generator list, so it is not this repo's to fix. It IS a sequencing
fact the live run has to carry: the breaks land the moment notes change shape, so they belong in
`docs/wi-032-whatsapp-live-baseline.md`'s ENTRY row, in front of Dave, BEFORE the write — named, with the
consumer audit's pinned HEADs beside them, so the go/no-go is taken with the blast radius on paper. **And the
third of them is stated as its OWN `DATA-LOSS HOLD` row rather than as the third item of one list**
(threat-model M3, folded by the spec-writer into `## Design` §10(c)): the other two announce themselves the
instant they break and are self-limiting, while this one is silent and destroys exactly the value this item
exists to protect, so a flat list of three makes it read as the third annoyance. Items 4–7 of the audit's list
are carried as a one-line pointer to the audit rather than re-listed. Zero
criteria move and the AC frame stays frozen; this is a disclosure, not an assertion.

**(3) One resolution door.** A public `get_by_identifier(Identifier)` plus a `whatsapp_jid` step in the
cascade reads the `jid:<lid>` keys the index already holds, with the new label added to
`_RESOLVE_CASCADE_ORDER` (`person.py:145`) so it does not rank last by accident (F15). And
`_index_entity` stops feeding a lid's digits into `_phone_index` — only a JID whose `phone_digits` is
non-empty pivots to a phone — with `_remove_entity_from_indexes` moving in lockstep (F5, F11, and the
defect in `## Problem / Motivation` item 3).

**(4) The migration, which is the item.** A dry run that reports per-cell counts over the six-cell class
table — and, for the class-C repair alone, the per-note `(stored value → proposed JID)` pair with every
member whose digits are not corroborated by its own `phones[]` printed FIRST, every field of every pair
ESCAPED so one record is one physical line whatever the note holds (threat-model M1 and M4, folded into
`## Design` §10(a) and §10(d): the counts are the right exit figure and the wrong go/no-go figure for 82
irreversible re-spellings, and a disclosure the disclosed data can reflow or forge a header inside is not a
go/no-go artifact) — and writes nothing; the write through `vault_io` and through the gate; a readback whose oracle is
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
was left adjudicating the figure in prose). **The exit row carries the partition's OWN three parts, in the
same order `## Exploration Notes` and AC-5 leg (e) state them, with the repair count as a NAMED SUB-COUNT of
part (2) rather than as part (2) itself** (architect round-9 note 1, folded by the spec-writer: the earlier
list substituted the class-C repair count for MIGRATED and so dropped the count of notes the run actually
converted, under a sentence asserting the two triples were the same triple): (1) notes left in the scalar
shape OUTSIDE the residual R — ZERO; (2) MIGRATED — the notes now carrying the LIST form, with two named
sub-counts, the SHAPE-ONLY conversions (class Ø) and the class-C REPAIRS (equal to the census's class-C row
under the recommended arm, zero under the alternative with those notes counted in `|R|` instead); (3) `|R|` —
the notes whose value the STORABLE predicate refuses, each reported and byte-identical, equal to the census's
class-D plus class-E rows, plus its class-C row if Dave declines the repair (Ruling B's alternative arm).
Plus the identifier-key multiset unchanged corpus-wide, and no value cleared by the run.

**The SHAPE-ONLY sub-count is 1025 and not 1031, and that is a distinction the census already measures**
(architect round-9 note 2, folded by the spec-writer — and the fold is smaller than the note expected,
because the artifact landed with the split already in it). Class Ø has two live spellings and only ONE of
them is a write: `docs/wi-032-whatsapp-corpus-census.md:184` reports class Ø as 1031 = **absent key 6 +
`""` 1025 + YAML null 0** (its `(c')` splits line, `:172`), and the migration converts the key-PRESENT
spelling only — `""` → `[]`. A note with the key ABSENT needs no write at all and is outside the partition's
own domain, which opens on "every `whatsapp`-carrying note". So the `whatsapp`-carrying population the
partition ranges over is 1168 (1174 person notes less the 6 absent-key notes), MIGRATED is 1168 − `|R|`, and
the shape-only sub-count is 1025.

**And that sub-count is ~88% of the run's writes with no semantic effect, which is a cost worth posing
before the write rather than after** (architect round-9 note 4, folded as a sentence rather than as a fourth
ruling because the decision point already exists). The tolerant reader ALREADY presents `whatsapp: ""` as the
empty collection, so converting those 1025 notes changes no resolution, no key, no model value and no
consumer-visible behaviour — it buys cosmetic uniformity and it costs turning the riskiest step in the item
from ~143 notes into ~1168, with the same multiple on the reverse if the back-out is ever taken. The
partition as it stands REQUIRES them (part 1's zero ranges over the scalar shape and `""` is a scalar), so
no build has latitude here. What the dry run puts in front of Dave is that number, named as the shape-only
population, so he can say "leave those alone" with it in hand; if he does, part 1's zero becomes "zero
outside R and outside class Ø" and the tolerant reader is what makes that safe — a one-line consequence in
the bracket's exit row, not a redesign, and not a change to any criterion.

**One sentence for the bracket's ENTRY row that the census's own §2 is slightly over-broad about**
(data-audit note (i), folded by the spec-writer). The census measures ZERO live collisions of the HARMFUL
shape — a query for a REAL stored number returning a lid's owner — so "the resolution fix changes no live
lookup result" is true of that row. It is over-broad for the OTHER shape `## Problem / Motivation` item 3
describes: 26 vault notes store a lid whose digits sit in `_phone_index` today (`person.py:266-270`), so a
query for a number NOBODY holds can still return one of those 26 people, and AC-1's change retires exactly
that. No consumer synthesizes such a query (orchestrator strips the JID first; HAL9000's
`resolve_by_whatsapp` has no production caller), so the live blast radius is nil — but the entry row says
"26 notes leave `_phone_index`, 0 live answers move" rather than "no lookup result changes". **One of those numbers is now readable off a tool rather than off the migration's
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
than oddly shaped. The back-out is a REVERSE migration through the same door, and it is exact **up to the
class-C repair** and then only while no note carries a second JID. **TWO qualifiers, not one** (architect
round-9 note 3, folded by the spec-writer — the earlier text named only the second). The first is present on
day ONE under Ruling B's recommended arm: the repair rewrites the stored spelling
(`"+44 7739 341679"` → `"447739341679@s.whatsapp.net"`) for all 82 census class-C notes, so a list→scalar
reverse returns the CANONICAL form and not the pre-migration bytes for every one of them. The harm is
semantically null — AC-5 leg (d) asserts the repair key-preserving, so nothing resolves differently and the
reverse arguably lands on the better spelling — but the conductor performing the bracket is entitled to hear
"exact up to 82 canonical re-spellings" rather than "exact", and under Ruling B's alternative arm (repair
declined) this qualifier disappears entirely while `|R|` grows by those same 82. The second qualifier is the
one F14 already named: the reverse is exact only while
no note carries a second JID — which is true on the day this ships, because this item makes the shape
available and does not itself populate second JIDs (that is HAL9000 WI-075 / orchestrator WI-192-193).
Once a second JID exists anywhere, list→scalar loses one by definition and the position is forward-only
with the tolerant reader kept. The live run is bracketed entry/exit the way
`docs/stem-divergence-live-baseline.md` brackets WI-029's, and the exit entry records the window closing.

## Verified Diagnosis

Four load-bearing claims about how the system behaves incorrectly TODAY. Each is grounded in code read in
this worktree (git HEAD `c7d074f` plus the seeded delta) or in a committed artifact; if any were false the
work would be invalid. Currency and predicates are re-stated here rather than inherited, because this
section is the one a reviewer falsifies first.

**VD-1 — `Person.whatsapp` is a bare `str`, so the field cannot hold the two identifiers a person now has,
and the one surface every writer shares has no rule about it.** `obsidian_schemas/models.py:Person` declares
`whatsapp: str = ""` (`models.py:94`, read this round). `obsidian_schemas/name_gate.py:_CONTAINER_KEYS` is
`("emails", "phones", "aliases")` (`name_gate.py:84`) and `gate_write` (`name_gate.py:gate_write`) evaluates
`_shaped` for exactly those three keys (`:374-376`) — `whatsapp` appears in no branch of the function.
Falsifier: `rg -n 'whatsapp' obsidian_schemas/name_gate.py` → 0 matches.

**VD-2 — the parser a writer would reach for ACCEPTS the value that caused this item.**
`obsidian_schemas/identifier.py:WhatsAppJID.parse` (`:269-281`, read this round) tests for the `@lid`
SUBSTRING (`:276`), then for `normalize_phone(s)` yielding at least `Phone.MIN_DIGITS == 7` digits
(`:278-280`), and tests for a JID domain NOWHERE. So `WhatsAppJID.parse("+44 7739 341679")` returns
`WhatsAppJID(jid="+44 7739 341679", phone_digits="447739341679")` with `key == "phone:447739341679"` — the
Kim Faura value, and the bare-phone bypass recorded at `docs/write-door-bypasses.md:3994`, parses clean. A
door wired to `parse` alone refuses only digit-less junk. Falsifier: `docs/wi-032-whatsapp-corpus-census.md`
measures **82 live person notes** whose stored `whatsapp` is a bare number with no `@` at all — 7.0% of
1174, one every ~14 notes — every one of which `parse` accepts.

**VD-3 — a stored `@lid` is indexed as a telephone number, and the correct key nothing reads.**
`obsidian_schemas/repositories/person.py:_index_entity` calls `normalize_phone(entity.whatsapp)`
unconditionally and writes the result into `_phone_index` (`person.py:266-270`, read this round);
`normalize_phone` splits at the first `@` and keeps the digits (`phone_normalization.py:52`), so a lid's
opaque internal digits become a phone key. `get_by_phone`'s fuzzy arm is PERMANENT and iterates
`_phone_index` through `phones_match` (`person.py:481-496`), so a query for a number nobody holds can return
a lid's owner. Meanwhile `_project_identifiers` indexes the same lid correctly under `jid:<lid>`
(`person.py:330-331`) and the only frame reading that key is `_resolve_identifier` (`person.py:886-909`),
reachable only from `resolve_or_create` by a caller already holding a typed `Identifier` — `resolve_all`'s
cascade (`person.py:606-690`) has no `whatsapp_jid` step at all. Falsifier: the census measures **26 vault
notes** storing a lid today, so 26 phone-index entries exist that no telephone number legitimately owns; the
HARMFUL collision shape (a query for a REAL stored number answering with a lid's owner) measures **zero**,
which is why AC-1 PLANTS the falsifying member rather than hoping for one.

**VD-4 — the report surface this design's "reported and left" half names does not exist.**
`scripts/lint_vault.py:_gate_refusal_pattern` (`:334-352`, read this round) has exactly ONE call site,
`:450`, inside `check_structural`'s `stem_name_divergence` arm and behind
`isinstance(stored, str) and stored.strip() and stem != stored` (`:449`); its return value is spliced into
THAT issue's message as a marker (`:451-462`) and it emits no `LintIssue` of its own. Falsifiers:
`rg -n '_gate_refusal_pattern' scripts/lint_vault.py` → 2 lines (the `def` and the one call);
`rg -n 'whatsapp' scripts/lint_vault.py` → 0 matches; and
`docs/stem-divergence-live-baseline.md:191` records WI-029 closing that arm's live population **8 → 0** on
2026-09-26, so the one route is taken zero times on today's vault.

**Not claimed, and deliberately.** That the scalar→list flip breaks a named consumer is NOT diagnosed here —
it is MEASURED in `docs/wi-032-consumer-audit.md` (20 production sites across three pinned repo HEADs, zero
element-type assumptions, zero whole-record projections) and the data-premise gate verified it. This section
claims only the four in-tree behaviours above.

## Design

The delta, and nothing that already works. Ten parts, each citing the frame it changes and quoting what is
there now. **Two invariants run through all ten and are what the parts are ordered around:** the STORABLE
question has exactly ONE implementation, on the type; and the "does this stored field carry something the
door refuses" question has exactly ONE implementation, `WhatsAppJID.classify_field`, which the gate arm, the
lint detector, the migration and every test call rather than re-derive.

**What the SPEC REVIEW's round 1 changed (2026-09-27), and where each fold landed — no `criteria` fence moved
and no signed span was touched.** Both blocking findings were the same shape one artifact apart: a clause an
earlier fold ADDED whose ORACLE that fold never derived, so the clause reads as already-guaranteed while two
of the three builds satisfying it do nothing. (1) AC-3's APPEND-ONLY conjunct (2) asks for a pre-build byte
comparison no post-build hermetic check has a referent for; **§6** now fixes the COMPUTABLE FORM it is
satisfied by — the 29-record count read off the artifact plus the thirteen-member equality, both at test time
— and **Task 8** orders exactly that, with the frozen criterion text left verbatim. (2) The migration's
re-run no-op was resolved in `## Edge Cases` and asserted nowhere, while the same section promises it to a
conductor mid-migration as the only retry remedy; **§7** now states the property with its discriminating
oracle (a ZERO call count on the write door, because a digest cannot tell "no write" from "re-write the same
bytes" and AC-5's two-JID plant is list-shaped from the start), **Task 10** orders it inside the check that
already drives `apply_migration`, and `## Edge Cases`' first-run, idempotency and retry entries point at it.
Five non-blocking notes landed in the same edit: a blank member inside a list is REFUSED, decided and reasoned
in **§3** and mirrored in `## Edge Cases` (the `emails[]` precedent is declined, with the two reasons); the
three imports the code blocks need are named in **§1**, **§2** and **§4**; §1's tail comment now names the
DECIDER instead of promising class D for a value that is class C; **Task 12**'s `docs/wi-032-*` count is
corrected to the one file this item writes and that run declared VOLUNTARY, since `docs/**` is outside that
scan's domain; and **F18 leg 2** is narrowed to the census verdict loop's `refusal` arm with the conservative
scoping kept and its reason stated. The review's one OBSERVATION — that Task 10 is the plan's longest
unresumable stretch and cannot be split without breaking `landed: Task 10` — is recorded rather than actioned,
and this round adds to that task, which is worth stating plainly: the re-run leg is three assertions inside a
check that task already writes, not a new artifact, and the `## Design` §6 fold adds nothing to it at all. The
preamble's part count is corrected from six to ten in the same pass (§7–§10 arrived in later folds).

### §1 Two predicates and one classifier, all on `WhatsAppJID` (`obsidian_schemas/identifier.py`)

`parse` is UNCHANGED — it is the REACH predicate and every resolution and indexing caller keeps it exactly as
it is (F12; rejected item 7 prices the alternative). Four additions to the same frozen dataclass, in the
same twelve lines, so "one authority" is literal:

```python
@dataclass(frozen=True)
class WhatsAppJID(Identifier):
    kind: ClassVar[str] = "whatsapp_jid"
    resolves: ClassVar[FrozenSet[str]] = frozenset({"person"})

    #: WI-032. The closed set of JID domains a STORABLE value may carry. Read by
    #: the WRITE DOOR and by nothing else — `parse` stays liberal for LOOKUP.
    #: Widening this set later joins every sweep automatically, because every
    #: criterion CALLS the predicate instead of restating its membership.
    STORABLE_DOMAINS: ClassVar[FrozenSet[str]] = frozenset({"s.whatsapp.net", "lid"})

    #: The six-cell storage classes, and the ONE spelling of the absent cell.
    CLASS_ABSENT: ClassVar[str] = "Ø"
    CLASSES: ClassVar[Tuple[str, ...]] = ("Ø", "A", "B", "C", "D", "E")

    jid: str           # normalized raw JID, lowercased   (UNCHANGED)
    phone_digits: str  # "" for @lid JIDs                 (UNCHANGED)

    @property
    def jid_domain(self) -> str:
        """The text after the LAST `@`; `""` when there is none.

        Computed off `self.jid` because there is nowhere else to read it from:
        this dataclass is frozen and holds no raw value — `parse` stores
        `str(raw).strip().lower()` (`identifier.py:273`, `:277`, `:281`). That is
        not a limitation, it is what makes the predicate case-insensitive for
        free, so `447700900321@S.WHATSAPP.NET` is storable with no second rule.
        """
        return self.jid.rpartition("@")[2] if "@" in self.jid else ""

    @property
    def is_storable(self) -> bool:
        """MEMBERSHIP of the closed set, never a suffix test. Under a bare
        "has a non-empty suffix" reading `447700900789@example.com` becomes
        storable, class C empties and class E ceases to exist — the reading
        changes the class table's MEMBERSHIP, so it is not a latitude."""
        return self.jid_domain in self.STORABLE_DOMAINS

    @classmethod
    def classify(cls, raw) -> str:
        """The storage class of ONE raw `whatsapp:` value. TOTAL, and loud on
        the one shape whose `str()` repr smuggles digits past `normalize_phone`.

        ORDER IS THE CONTRACT. The emptiness test precedes BOTH predicate calls,
        because `parse` raises on `""` and `None` through the same two lines it
        raises on `"n/a"` with (`identifier.py:271-275`, no blank branch) — so a
        classifier that asks the predicates first files the live corpus's 1025
        default-valued notes as a defect class.
        """
        if isinstance(raw, (list, tuple, set, dict)):
            # `parse(["447700900321@s.whatsapp.net"])` SUCCEEDS with the right
            # phone digits, recovered out of the list's repr by
            # `normalize_phone`'s first-`@` split. A container reaching a
            # per-value classifier is a CALLER bug, and it is refused rather
            # than answered.
            raise IdentifierError("whatsapp_jid", raw,
                                  "a container reached the per-value classifier")
        if raw is None:
            return cls.CLASS_ABSENT
        if isinstance(raw, str) and not raw.strip():
            return cls.CLASS_ABSENT
        try:
            parsed = cls.parse(raw)
        except IdentifierError:
            return "D"
        if parsed.is_storable and parsed.phone_digits:
            return "A"
        if parsed.is_storable and not parsed.phone_digits:
            return "B"
        if not parsed.is_storable and parsed.phone_digits:
            return "C"
        if not parsed.is_storable and not parsed.phone_digits:
            return "E"
        raise IdentifierError("whatsapp_jid", raw, "matches no declared class")

    @classmethod
    def classify_field(cls, stored) -> List[str]:
        """The stored `whatsapp:` FIELD's per-value classes, in stored order.

        THE one authority the gate arm, the lint detector, the migration and
        every test call. Accepts BOTH stored shapes, because both exist on disk
        for the whole migration window and an arm that inspects only lists is
        silent for exactly the population this item exists for (F2).

        Class Ø at the FIELD level is the EMPTY RESULT — an absent key (`None`),
        `""`, whitespace, and `[]` all introduce no identifier, so there is no
        member for any arm to judge and no arm can refuse them.
        """
        if stored is None:
            return []
        if isinstance(stored, str):
            return [] if not stored.strip() else [cls.classify(stored)]
        if isinstance(stored, (list, tuple)):
            return [cls.classify(member) for member in stored]
        return [cls.classify(stored)]   # a non-str scalar: `parse` decides the class
```

**That last line's comment names the DECIDER and not a class, because the class depends on the value and the
live shape it matters for is not D.** An unquoted `whatsapp: 447700900123` loads as a YAML `int`, falls to
this line, and `parse` does `str(raw).strip().lower()` (`identifier.py:parse`, `:273`) — so `normalize_phone`
recovers twelve digits, there is no `@` at all, and the value is class **C**: phone-bearing, not storable,
refused by the door, repaired by the migration and reported by the detector. That is threat-model note 4's new
discovery channel and it would be lost by a comment that promised D. What DOES land in D is a non-`str` scalar
whose `str()` carries fewer than `Phone.MIN_DIGITS` digits — `True` → `"true"` → none, `42` → two — and a
`date` is worth naming as the near-miss it is: `2026-09-27` normalizes to the eight-digit `20260927` and files
as **C**, not D, because `normalize_phone` keeps only digits (`phone_normalization.py:54-55`). Neither class
needs a branch — the point of routing a non-`str` scalar through `parse` is that the six-cell partition
already covers every one of them.

`classify`'s tail `raise` is unreachable against today's four-way partition, and that is the point: AC-1
requires a TOTAL function with NO fall-through bucket, so a seventh shape RAISES instead of being filed. The
container refusal is the round-8 note's trap closed at the leaf — `_project_identifiers` guards with
`if entity.whatsapp:` and its `add()` blank guard tests `isinstance(raw, str)` (`person.py:319`, a list
passes it), so a build that forgot to iterate would have produced the CORRECT `phone:` key for a single
phone-bearing value and passed AC-1's and AC-2's class-A legs.

**Nothing on `WhatsAppJID` is added to `model_fields`** — see §2. The type stays a pure value object with no
vault I/O, so `identifier.py` remains a leaf importing only `phone_normalization`.

**The one import this part adds, named so the builder is not the one to find it.** `identifier.py:36` binds
`from typing import ClassVar, FrozenSet, Optional, Tuple` and NOT `List`, which `classify_field`'s return
annotation needs. Under `from __future__ import annotations` (`:31`) the omission is invisible at runtime and
wrong for a type checker, which is the failure mode worth one line here rather than one round later. Nothing
else moves: `ClassVar`, `FrozenSet` and `Tuple` are all already bound, so the four new class attributes need
no import at all.

### §2 The model: `List[str]` stored, tolerant read, typed access DERIVED (`obsidian_schemas/models.py`)

```python
    whatsapp: List[str] = Field(default_factory=list)   # was: whatsapp: str = ""

    @field_validator("whatsapp", mode="before")
    @classmethod
    def _tolerate_scalar_whatsapp(cls, value):
        """EXPAND phase. The reader accepts BOTH shapes indefinitely, because the
        VAULT is shared mutable state: any consumer running older code against a
        migrated note breaks however the package is installed, so a version pin
        creates no private window (F14 correcting F7). And a refusing reader does
        not degrade gracefully — `parse_to_model` raises `SchemaDriftError` on an
        owned note that fails validation (`parser.py:203-208`), which the load
        path records as a SKIP, making the note INVISIBLE rather than oddly
        shaped.

        Three spellings collapse to the empty collection and none of them is a
        refusal: `None` (an absent key, and a BARE valueless `whatsapp:` key,
        which YAML loads as null and `_normalize_frontmatter` passes through
        untouched, `parser.py:118-132`), `""`, and whitespace.
        """
        if value is None:
            return []
        if isinstance(value, str):
            return [] if not value.strip() else [value]
        return value

    @property
    def whatsapp_jids(self) -> List[WhatsAppJID]:
        """The typed view — the PARSEABLE stored values, in stored order.

        Filtered on PARSEABILITY and never on storability: classes C and E parse
        and appear here (they are merely unstorable); class D does not parse and
        appears only in the raw field. A build that filtered on storability is
        RED on AC-4 leg (b).

        A `@property` and NOT a field, which is what closes F8 by construction:
        `model_to_frontmatter` iterates `model_class.model_fields`
        (`writer.py:112-117`), so nothing dataclass-shaped is ever handed to
        `yaml.dump`'s default `Dumper` (`writer.py:152`) while the reader is
        `yaml.safe_load` (`parser.py:101`). There is no projection step to
        remember, and rejected item 9 is why there is none to write.
        """
        out = []
        for raw in self.whatsapp:
            try:
                out.append(WhatsAppJID.parse(raw))
            except IdentifierError:
                continue
        return out
```

**Why the coercion lives on the model and not in `parser.py:_normalize_frontmatter`.** That function is
field-name-AGNOSTIC — it converts dates and recurses into lists and knows no field names at all
(`parser.py:111-133`). A `whatsapp` branch there would be a second spelling of this field's shape rule,
outside the annotation it belongs to, reached by only one of the two load paths. The validator travels with
the field.

**The import edges this adds — two, not one.** `models.py` gains `from .identifier import IdentifierError,
WhatsAppJID`; `identifier.py` imports only `phone_normalization`, so `models -> identifier ->
phone_normalization` closes no cycle, and `name_gate.py` still imports no `models` and must not
(`name_gate.py:14-20`). And **`field_validator` joins the pydantic import**: `models.py:21` binds
`BaseModel, ConfigDict, Field, PrivateAttr` and the module names no validator of any kind today
(`rg 'field_validator|validator' obsidian_schemas/models.py` is 0 matches), so §2's decorator is an import as
well as a method and this is the FIRST validator in the module.

### §3 The write door: one arm on the surface every writer shares (`obsidian_schemas/name_gate.py`)

Two module constants and one arm. **The refusal's `pattern` is a GATE-LOCAL LITERAL** — `_refuse` takes a
plain `pattern_key: str` (`name_gate.py:_refuse`, `:142-174`), so no record is needed anywhere, and
declaring it as a `NameValidator` Tier-1 branch record instead would join WI-016's AC-3 class floor, which
is DERIVED by equality from `{record.branch_id for record in TIER1_BRANCHES + COMPANY_TIER1_BRANCHES}` and
asserted in both directions (`tests/test_fixture_vault.py:830-838`) — a conductor pass, for a refusal that
is not a name judgement (F18 leg 4).

```python
#: WI-032. The whatsapp refusal's pattern. The gate's OWN literal, like
#: `UNDECLARED_PATTERN` above it — never a NameValidator branch record.
WHATSAPP_PATTERN: str = "whatsapp_not_a_jid"

#: The one identifier key this gate judges by VALUE rather than by container shape.
WHATSAPP_KEY: str = "whatsapp"
```

`_refuse` gains ONE keyword and keeps being the ONE construction site. **Its docstring gains a THIRD numbered
clause — appended beside rules 1 and 2, never an edit to either** (threat-model note 2, folded): the keyword
exists for the whatsapp arm, which is the one arm whose refused value is not a name, and the NAME arms
deliberately pass nothing through it — because the name a name-arm would pass IS an email address at
`contains_email_chars` and `rfc2822_leak`, which is the whole reason rule 2 exists. The channel now exists on
the site whose rule 2 keeps note bytes off it, so the note goes where the next reader looks:

```python
def _refuse(pattern_key: str, *, cause: Optional[BaseException] = None,
            refused_value=None) -> NoReturn:
    exc = NameGateRefusal(_REFUSAL_REASON)
    exc.pattern = pattern_key
    # WI-032. The Intent's "loudly and NAMING THE VALUE" — as an ATTRIBUTE, set
    # AFTER construction exactly as `pattern` is, so it reaches no message and no
    # traceback renders a note's bytes. Rule 2 above forbids a note-derived value
    # in the CONSTRUCTOR and this is not one. Set unconditionally (None where
    # there is none) so every refusal carries the attribute and no consumer has
    # to guess whether to use getattr.
    exc.refused_value = refused_value
    raise exc from (chainable_cause(cause) if cause is not None else None)
```

The arm, placed **between step 3 (name) and step 4 (addresses)**:

```python
    # ---- 3b. WhatsApp (WI-032) — a VALUE judgement, not a container shape ----
    #
    # PLACED AFTER THE NAME ARM, and the position is prescribed rather than left
    # free: several corpus notes declare a `Verdict(kind="refusal", pattern=<a
    # NAME pattern>)` whose whole declared field set is written through the gated
    # door with `exc.pattern` asserted equal to it
    # (`tests/test_fixture_vault.py:856-878`). Keeping the name refusal first
    # makes every one of those declarations true by CONSTRUCTION rather than by
    # an insertion point nobody wrote down.
    #
    # Unlike `emails`/`phones`/`aliases` this arm does NOT use `_shaped`. That
    # predicate is POSITIVE, so a bare `str` falls to pass-through untouched
    # (`_is_str_list`) — and every `whatsapp` value on disk today IS a bare str,
    # so an arm copied from the containers would be structurally silent for
    # exactly the population this item exists for.
    if WHATSAPP_KEY in introduced:
        members = introduced[WHATSAPP_KEY]
        for position, member_class in enumerate(
                WhatsAppJID.classify_field(members)):
            if member_class not in ("A", "B"):
                _refuse(WHATSAPP_PATTERN,
                        refused_value=_member_at(members, position))
        # ONE WRITTEN SHAPE: a scalar the caller handed us is emitted as a
        # one-member list, absence as `[]`, and every accepted member passes
        # through VERBATIM — the migration's repair is the only rewriter, and it
        # rewrites before the write. The key set is unchanged, so THE OUTPUT
        # NEVER GROWS still holds by construction.
        result[WHATSAPP_KEY] = _as_stored_list(members)
```

`_member_at` and `_as_stored_list` are two three-line module helpers beside `_shaped`; both read
`classify_field`'s own shape rules and neither re-derives a class.

**What the arm refuses, exactly.** The NON-EMPTY values whose class is C, D or E. Class Ø — an absent key,
`""`, whitespace, `None`, `[]` — yields no members, so the loop body never runs and the write is ACCEPTED.
That is not leniency bolted on: it is the rule `_project_identifiers`'s `add()` already follows
(`person.py:318-320`, returning on a `None` or blank raw BEFORE any parser) and the rule the gate's own
`emails[]` arm follows by falsiness (`name_gate.py:399`). It is also what keeps CLEARING the field legal —
the only repair a class-D value has, since the writer has no delete affordance at all
(`writer.py:update_frontmatter_field` SETS a value, `:333-337`).

**A BLANK MEMBER INSIDE A LIST — `{"whatsapp": [""]}` — is REFUSED, and the decision is stated here rather
than left to be discovered.** The code above already determines it: `classify_field`'s list branch maps
`classify` over the members with no falsiness filter, `classify("")` returns `CLASS_ABSENT`, and the arm
refuses every class `not in ("A", "B")` — so `[""]` is refused with the whatsapp pattern while the scalar
`""` is accepted. Nothing ships two ways and no criterion is strained: AC-3's CLASS-Ø leg enumerates the
five spellings of class Ø at the FIELD level (absent key, `""`, `None`, whitespace-only, `[]`), and `[""]`
is not one of them — it is a field with a MEMBER that carries no identifier, which is a caller defect and
not a spelling of absence. **That leg's "in both shapes" names the scalar `""` and the list `[]`, which are
the two shapes the five enumerated spellings already cover — NOT a cross product of the five with the two.**
`[""]`, `[None]` and `["   "]` are each a populated field and each is refused, and the distinction is written
down here because the test author implementing "every spelling in both shapes" is the one reader who would
otherwise reach for them and read the refusal as a defect. **And the shape is unreachable from every arm this
design owns:** the model coerces `""` to `[]` (§2), the migration writes `[]` for the whole class-Ø cell and
passes accepted members through verbatim (§7), and no corpus note or live note is list-shaped at all — so
refusing it costs nothing real and buys a closed door. The `emails[]` precedent this
document cites for the class-Ø rule takes the other arm — `name_gate.py:399`'s `elif entry and …` neither
parses nor keeps a blank member, it DROPS it — and this arm deliberately does not follow it there, for two
reasons that are this item's own. A drop is a SILENT DROP, which is the one thing AC-4 leg (b) and this
arm's "every accepted member passes through VERBATIM" comment both forbid. And filtering blanks out of
`classify_field`'s list branch would break the POSITIONAL correspondence the refusal depends on: the arm
recovers the offending raw value with `_member_at(members, position)` over `enumerate(classify_field(...))`,
which is only correct while the classifier returns exactly one class per stored member, so the cheap-looking
filter would cost the refusal its ability to name the value. Refusing fails CLOSED, loudly, naming the
value. The detector (§4) reports the same shape under the same rule, which is the one-authority invariant
holding rather than a second decision.

### §4 The report arm: `lint_vault` gains a DETECTOR, not a routing tweak (`scripts/lint_vault.py`)

VD-4 is why this is new code rather than a consequence. ONE report-only arm in `check_structural`, copying
WI-029's own detector shape literally (`scripts/lint_vault.py:417-462` — ERROR, `structural`, `auto_fixable`
left at its `False` default, `:96`), placed after the `stem_name_divergence` arm and before
`field_type_mismatch`:

```python
#: WI-032. The report-only check name. Its OWN name, never
#: `stem_name_divergence`: that arm's marker says "this divergence is not
#: repaired by renaming the file to the stored name; repair the field" (:451-454),
#: which is a false statement about a defect that is a FILENAME, and widening it
#: would move live rows against WI-029's committed "divergent rows the WRITE DOOR
#: refuses (b3): 0 of 8" (`docs/stem-divergence-live-baseline.md:124`).
WHATSAPP_CHECK = "whatsapp_not_storable"

        if vf.entity_type == "person":
            try:
                classes = [c for c in
                           WhatsAppJID.classify_field(vf.frontmatter.get("whatsapp"))
                           if c not in ("A", "B")]
            except IdentifierError:
                # A frontmatter shape the classifier refuses (a nested container
                # under `whatsapp:`). REPORTED under the SAME check rather than a
                # second one, because the repair is identical — this tool's
                # contract is that no note crashes the run.
                classes = ["unclassifiable"]
            if classes:
                issues.append(
                    LintIssue(
                        vf.path, WHATSAPP_CHECK, Severity.ERROR,
                        f"stored `whatsapp` carries {len(classes)} value(s) the "
                        f"write door refuses (class "
                        f"{', '.join(sorted(set(classes)))}); repair to a JID or "
                        f"clear the field",
                        "structural",
                    )
                )
```

The message carries a COUNT and CLASS LETTERS and no note-derived value — the same discipline `_refuse`
keeps, for the same reason.

**The import this arm needs.** `scripts/lint_vault.py` imports `NameGateRefusal` and `gate_write` and
`TYPE_TO_MODEL` (`:44-48`) and neither `WhatsAppJID` nor `IdentifierError`, both of which the arm above calls
— so the module gains `from obsidian_schemas.identifier import IdentifierError, WhatsAppJID` beside those. It
closes no cycle (`identifier.py` is a leaf) and adds no vault reach.

Three properties, each measured rather than assumed:

- **It owes NO repair oracle.** `tests/test_lint_vault_fix_rules.py:596-624`'s oracle-table equality is
  scoped to `auto_fixable_emitter_checks([LINT_VAULT_PATH])` (`:599`, `:621-624`), so a report-only rule is
  outside that derived set by construction and the WI-026 floor needs no fifth oracle.
- **It disturbs no set equality in the divergence module.** `_divergence_issues` filters on
  `issue.check == DIVERGENCE_CHECK` (`tests/test_stem_name_divergence_detector.py:283-289`), so a new check
  name is invisible to that module's four assertions.
- **`--fix` is untouched, for a reason the data-premise gate RAN rather than reasoned.** `apply_fixes` hands
  the gate the DELTA (`gate_write(delta, declared_type=fm.get("type"), whole_record=False)`,
  `scripts/lint_vault.py:1181-1182`), so a fix for an unrelated issue on a class-C-bearing note presents a
  payload with no `whatsapp` key, the new gate arm is never consulted, and the write re-serializes the
  stored value unchanged (`_wfm(fm)`, `:1194-1198`). The note's other issues still repair and the bad value
  is neither refused nor dropped.

### §5 Resolution: one phone-pivot rule, one public door, one cascade step (`repositories/person.py`)

**(a) The phone pivot is DERIVED from the projection, in ONE frame.** Three frames decide today what a
`whatsapp` value contributes to `_phone_index` and all three need the same rule. `_index_identifiers`
already runs at the end of `_index_entity` over `_project_identifiers`' typed output (`person.py:283-284`),
so the projection is the natural single source:

```python
    def _index_entity(self, entity: Person, cache_key: str) -> None:
        for phone in entity.phones:                       # UNCHANGED
            ...
        # WI-032. The whatsapp block that read `normalize_phone(entity.whatsapp)`
        # is GONE. A JID's digits enter `_phone_index` IFF its parsed form carries
        # non-empty `phone_digits`, DERIVED from the projection rather than
        # re-parsed beside it — one call, one rule, and the inverse below derives
        # from the same projection.
        identifiers = self._project_identifiers(entity)
        for ident in identifiers:
            if isinstance(ident, WhatsAppJID) and ident.phone_digits:
                self._phone_index[ident.phone_digits] = cache_key
        ...                                               # aliases, slack UNCHANGED
        self._index_identifiers(entity, cache_key, identifiers=identifiers)
```

`_index_identifiers` gains `identifiers: Optional[List[Identifier]] = None`, projecting for itself when it
is absent so every other caller is unchanged. **The two comment lines this deletes and edits —
`# Index WhatsApp number` and `# Remove WhatsApp from index` — belong to `_index_entity` and
`_remove_entity_from_indexes`, both of which ARE in WI-024's `AUTHORIZED_PROSE_OWNERS`
(`tests/test_identity_endgame.py:359-373`), so editing them is free.** §6 is where that stops being true.

**(b) The inverse, over the same projection**, so AC-1's exact-inverse assertion is true by construction:

```python
        for ident in self._project_identifiers(entity):
            if isinstance(ident, WhatsAppJID) and ident.phone_digits:
                if self._phone_index.get(ident.phone_digits) == cache_key:
                    del self._phone_index[ident.phone_digits]
```

Written as a lookup and NOT as a loop over `self._phone_index`. If a build ever writes it as a loop, the
iterable must be wrapped in one of `MATERIALIZING_WRAPPERS = {"list", "tuple", "sorted", "frozenset",
"dict"}` (`tests/derivations.py:1620`), because `tests/test_identity_endgame.py:642-644` asserts every
phone-index iteration site in the package is classified `materialized`.

**(c) `_project_identifiers` ITERATES.** `if entity.whatsapp: add(WhatsAppJID.parse, entity.whatsapp)`
becomes `for jid in (entity.whatsapp or []): add(WhatsAppJID.parse, jid)` — the same shape the `emails` and
`phones` loops two lines above already have. This is the frame where forgetting the loop turns a LOUD
failure into a SILENT wrong answer (§1's container refusal is the leaf-level guard; this is the caller-level
fix).

**(d) The public door.** One new method, delegating to the existing resolver so the WI-035 pivot is not
re-implemented:

```python
    def get_by_identifier(self, identifier: Identifier) -> Optional[Person]:
        """The public reader of the WI-125 identifier index (WI-032).

        The index was already right and nothing public read it — a lid was
        reachable only from `resolve_or_create` by a caller already holding a
        typed identifier. Delegates to `_resolve_identifier`, so a phone-bearing
        JID still pivots to `get_by_phone` and a `@lid` still reads its `jid:`
        key: one authority, no second index (rejected item 2).
        """
        self._ensure_loaded()
        return self._hydrate(self._resolve_identifier(identifier))
```

It is its OWN method and its lookup is NOT inside `resolve`, because
`tests/test_identity_endgame.py:692-698` asserts `PersonRepository.resolve` reads none of `_cache`,
`_alias_index`, the email index or `_phone_index` directly.

**(e) The cascade step and its rank.** `_RESOLVE_CASCADE_ORDER` (`person.py:145`) becomes
`("exact-name", "alias", "email", "whatsapp-jid", "phone")` — the new label inserted immediately BEFORE
`phone` so every existing relative order is byte-identical and the new one still outranks `phone`. Without
the label an unknown `matched_via` sorts LAST (`select_resolution`'s `rank`, `person.py:190-197`), which is
the wrong answer when an exact `jid:` hit ties a fuzzy phone hit. The step goes in `resolve_all`
immediately after step 4, which is BELOW the blank-query bail-out (`person.py:608-609`) — that ordering is
the one thing inserting a step can break, and AC-2 pins it:

```python
        # 4b. WhatsApp JID match (WI-032) — the `jid:` keys the identifier index
        # already holds and nothing public read. GUARDED on the absence of phone
        # digits: a phone-bearing JID is already answered by step 4 above, which
        # is the right door for it and is what keeps `README.md:238`'s documented
        # `get_by_phone("<digits>@s.whatsapp.net")` route true.
        try:
            candidate_jid = WhatsAppJID.parse(query)
        except IdentifierError:
            candidate_jid = None
        if candidate_jid is not None and not candidate_jid.phone_digits:
            person = self.get_by_identifier(candidate_jid)
            if person:
                record(person, 1.0, "whatsapp-jid")
```

`resolve_all`'s docstring may be edited — `resolve_all` IS an authorized prose owner.

**(f) `_IDENTIFIER_PRIORITY` is NOT touched.** `{"email": 0, "phone": 1, "whatsapp_jid": 1}`
(`person.py:778`) ranks the Branch-A best hit among typed identifiers a caller already holds, where a
phone-bearing JID and a phone are the SAME key and a tie is correct. Two reasons to leave it: it is right
for its frame (F15's amendment), and the class-body comment justifying it is owned by the bare qualname
`PersonRepository`, which is NOT an authorized prose owner
(`tests/fixtures/identity_endgame/prose_surface_cut0.json:1680-1683`).

### §6 `save`: a refusal surface, and two disclosures that must land APPEND-ONLY

`PersonRepository.save`'s rider gains one line beside the three it already has:

```python
        entity.emails = gated["emails"]
        entity.phones = gated["phones"]
        entity.aliases = gated["aliases"]
        entity.whatsapp = gated["whatsapp"]      # WI-032
```

Two facts make this more than a rider. `save` gates `model_to_frontmatter(entity)`
(`person.py:1190-1191`), and `model_to_frontmatter` emits EVERY declared field unconditionally
(`writer.py:112-117`) — so a value the note ALREADY stores is RE-INTRODUCED by the projection and therefore
judged. `save` is a REFUSAL surface. And it is not the only one: `write_markdown_file`'s entity arm passes
`gate_whole_record = True` over the same projection (`writer.py:229-233`) and is the arm `BaseRepository.save`
delegates into (`base.py:462-465`). **The handle is "any arm whose payload is a whole-record projection",
not the `whole_record` flag** — that flag only enables the two cross-field migrations
(`name_gate.py:289-294`, `:385`).

**The delta arms stay open, and that asymmetry is the design rather than a gap.**
`update_frontmatter_field`, `update_frontmatter_fields` and `update_fields` each gate the caller's dict with
`whole_record=False` and merge the result into the RAW parsed frontmatter
(`writer.py:385-390`, `base.py:728-735`). Two consequences fall out for free and neither needs new code:
a note whose stored value is unstorable stays writable for every write that does not re-introduce the field
(`name_gate.py:31-36`); and a scalar-carrying note written for an unrelated reason is NOT silently
rewritten, because the merge is over the raw parsed dict where `whatsapp` is still the stored scalar. AC-4
leg (c)'s "one written shape" is therefore satisfied by the existing architecture, and asserting it both
ways over a planted class-D note is what keeps it that way.

**Both disclosures are APPEND-ONLY, and that is a property of the FRAME, not of what they say.**
`prose_lines` (`tests/derivations.py:1773`) records every comment and docstring line with its owning
qualname; `tests/fixtures/identity_endgame/prose_surface_cut0.json` is that surface over `person.py` at Cut
0; clause **(e1)** of `test_strangler_prose_class_is_closed_in_the_package`
(`tests/test_identity_endgame.py:1008-1019`) asserts every Cut-0 `(owner, text)` pair whose owner is outside
`AUTHORIZED_PROSE_OWNERS` (`:359-373`) is still PRESENT in the final text — compared on `(owner, text)` and
never on line numbers, so an APPEND is free and an edit or a deletion is not. `PersonRepository.save` is
such an owner, with 29 recorded lines (`prose_surface_cut0.json:2400-2544` ≙ `person.py:1158-1189` plus
`:1195-1196`). So:

- The write-back disclosure is a NEW PARAGRAPH beside `person.py:1174-1184`, never an extension of the
  paragraph that enumerates `entity.emails`/`phones`/`aliases` and never an extension of the `phones[]`
  in-place-mutation paragraph F11 cited as its model.
- The refusal disclosure is a NEW PARAGRAPH beside `person.py:1169-1172`, never an extension of the
  `whole_record=True` sentence that says "both cross-field migrations run here exactly as they ran before".
- `AUTHORIZED_PROSE_OWNERS` and `prose_surface_cut0.json` are UNTOUCHED. Authorizing `save` is worse than
  widening another item's wall, because clause **(e2)** (`:1021-1030`) requires every authorized owner to
  have at least one Cut-0 line MISSING — so authorizing it is RED until one of the 29 is DELETED (rejected
  item 15). Reverting the disclosure is green on every check and silently withdraws
  `### Examples of done`'s "and it says so" (rejected item 16).

**THE COMPUTABLE FORM of AC-3's APPEND-ONLY conjunct (2), stated here because the frozen criterion names an
oracle a post-build hermetic check cannot take — and it is the one conjunct that criterion's own `why:` says
does work WI-024's wall cannot.** Conjunct (2) reads "`AUTHORIZED_PROSE_OWNERS` still has exactly its
thirteen declared members and `prose_surface_cut0.json` is byte-identical to its pre-build bytes". The first
half is computable: import the tuple and compare it to its members. The second half is not, twice over.
`prose_lines` (`tests/derivations.py:prose_lines`, `:1773`) reads SOURCE comments and docstrings and never
that JSON, so "computed through `prose_lines`" cannot reach it; and a check that runs AFTER the build has no
referent for "pre-build bytes" at all — the file is not a `## Write Targets` path, there is no shell in the
check, and a digest literal the build itself takes is the self-certifying constant WI-016's own AC-3(iv)
`why:` exists to refuse. Left as written it is satisfiable by SILENCE, and two of the three self-consistent
builds available to a builder do nothing: hardcode a build-taken digest (which certifies nothing), or re-read
it as a restatement of conjunct (1) (which adds no force at all, since conjunct (1) computes its expected
pairs FROM that same JSON). So the criterion's frozen text stands VERBATIM and the computable form it is
satisfied by is fixed here, in the form the document's own literals already support:

- **Read the artifact at test time, through the same reader clause (1) uses.** `_golden`
  (`tests/test_identity_endgame.py:_golden`, `:395-397`) is the reader
  `test_strangler_prose_class_is_closed_in_the_package` itself takes at `:996`; the check imports it and
  `AUTHORIZED_PROSE_OWNERS` from that module rather than re-spelling either (the cross-test-module import
  idiom already exists at `tests/test_name_gate_delta_rule.py:54-55`).
- **Assert the FROZEN POPULATION's count: the number of entries in `["lines"]` whose `owner` is
  `PersonRepository.save` is exactly 29** (`tests/fixtures/identity_endgame/prose_surface_cut0.json:2400-2544`
  ≙ `person.py:1158-1189` plus `:1195-1196`, the figure four sections of this document already print).
  Counted as a LIST LENGTH and never as the size of an `(owner, text)` SET — two identical texts collapse in
  a set and would hide exactly the deletion this conjunct exists to catch.
- **Assert `AUTHORIZED_PROSE_OWNERS` equals its thirteen declared members**, with neither
  `PersonRepository.save` nor the bare class among them (`tests/test_identity_endgame.py:359-373`).

**Why 29 may be pinned by EQUALITY, which is the WI-295 question and is answered rather than assumed.** The
figure is FROZEN, not live: `prose_surface_cut0.json` is a Cut-0 golden "recorded ONCE, against unchanged
code; never re-recorded" (`tests/test_identity_endgame.py:test_identity_goldens_are_frozen_pre_cut_data`,
`:400-402`), this item declares it as no write target and edits nothing under
`tests/fixtures/identity_endgame/`, so the item's own arc cannot append to the population the pin froze. It
is the same move F18 leg 1 prescribes for the census — assert the count of a frozen population, read from the
artifact, against a literal this document states — and it is the reason that move is available here and the
byte-identity one is not.

**What the two legs make RED, and why neither (e1) nor (e2) nor conjunct (1) can do it.** All three of those
read the tuple and the golden; none of them can witness a change TO the tuple or the golden, which is exactly
the gap AC-3's `why:` means by "the conjunct (e1) and (e2) cannot supply". Leg 1 catches the AUTHORIZATION
itself: adding `PersonRepository.save` to `AUTHORIZED_PROSE_OWNERS` is the move that makes (e1) stop
protecting its 29 lines at all, and it is RED the moment it is made rather than after the build has chosen
which line to sacrifice to (e2) (rejected item 15). Leg 2 catches the GOLDEN EDIT: removing a record from
`prose_surface_cut0.json` silently shrinks the domain that (e1) AND this criterion's own conjunct (1) both
compute their expectations from, so a build that deletes a docstring line and its record together is green on
conjunct (1) BY CONSTRUCTION — conjunct (1) is only ever as strong as the artifact it reads, and leg 2 is what
pins that artifact so conjunct (1) cannot be neutered instead of satisfied. Neither leg is inferable from the
other. The correct build — append two paragraphs, touch neither the tuple nor the golden — is green on both at
no cost.

### §7 The migration: `scripts/migrate_whatsapp_to_list.py`

**Home.** `scripts/`, beside `lint_vault.py`, and inside this project's declared `write_authority`
(`pipeline-runners.yaml:34-38`). Two reasons rather than convention: `scripts/` is swept by
`tests/test_name_gate_wall.py`'s arm wall (`python_files_under(PACKAGE_ROOT, SCRIPTS_ROOT)`,
`test_name_gate_wall.py:131`), so any frontmatter write arm the module carries must route through
`gate_write` with a resolved declaration — which is AC-5 leg (b)'s structural assertion, for free and from
a wall that was already standing; and it is OUTSIDE `tests/test_write_target_seam_wall.py`'s universe
(`python_files_under(PACKAGE_ROOT)`, `:227`), so a one-off vault walker does not have to satisfy WI-029's
loaded-entity provenance seam, which is a contract about repositories and not about a migration reading
bytes.

**Four entry points, and their NAMES are load-bearing** (see §8):

```python
def plan_migration(vault_path) -> MigrationPlan:      # READ-ONLY. The dry run.
def apply_migration(vault_path, plan, *, repair=True) -> MigrationResult
def readback_migration(vault_path, plan) -> ReadbackResult
def _cli(argv=None) -> int                             # argparse; --vault REQUIRED
```

Four ENTRY POINTS, and one further read-only formatter the M1 fold adds beside them —
`format_repair_disclosure(plan) -> str`, specified in §10(a), with its one private render helper
`_escape_for_one_line(raw) -> str` from §10(d). Neither drives anything and neither is a member of
`MUTATING_DRIVE_VAULT_POSITIONS` for the same reason `plan_migration` and `readback_migration` are not, so §8's
census and its six clauses are unchanged by both.

**No `DEFAULT_VAULT` and no env fallback.** `--vault` is `required=True` and the module names
`OBSIDIAN_VAULT_PATH` nowhere. That is not caution: `tests/test_vault_path_required.py:312-331` scans every
`.py` under `obsidian_schemas/` and `scripts/` for `FORBIDDEN_DEFAULT_PATTERNS = ["expanduser",
"Path.home()", "/Users/"]` and asserts zero live matches, and WI-031 closed the library's own env-fallback
route. A migration that can be pointed at the live vault by OMISSION is the one shape this repo has already
decided against twice.

**The per-note action, from `classify_field` and nothing else.** For each `type: person` note the run reads
RAW frontmatter (never a model — `parse_to_model` would coerce the field before the run could see its stored
shape) and takes exactly one arm:

| stored `whatsapp` | classes | action | part of the partition |
|---|---|---|---|
| key ABSENT | `[]` | **no write** — nothing to convert | outside the partition's domain |
| `""`, whitespace, YAML null, or already `[]` | `[]` | SHAPE-ONLY: write `[]` (skip if already a list) | MIGRATED (the 1025 sub-count) |
| already a list, every member in `{A,B}` | A/B | **no write** — already migrated | MIGRATED |
| scalar, member in `{A,B}` | A or B | CONVERT: write `[<member verbatim>]` | MIGRATED |
| any member class C, repair ENABLED | C | REPAIR then convert: `f"{parse(v).phone_digits}@s.whatsapp.net"` | MIGRATED (the repair sub-count) |
| any member class C, repair DISABLED | C | **no write**, reported | RESIDUAL R (Ruling B's alternative arm) |
| any member class D or E | D/E | **no write**, reported, byte-identical | RESIDUAL R |

**The repair is GUARDED on `phone_digits` being non-empty, and the guard is not decoration.** Applying it to
a phone-less unstorable value (class E) would write `"@s.whatsapp.net"`, which `parse` then REFUSES —
turning a note the run was supposed to leave alone into one nothing can read back. Every class-C value is
phone-bearing by construction once class E is carved out of it, and the census confirms all 82 live members
are bare numbers with no `@` at all, so the guard never fires negatively on a live note.

**The run NEVER CLEARS a value to make a note convert.** Emptying a class-D value would move it out of R
into MIGRATED and reach zero-outside-R trivially, by deleting the population this item exists to preserve.
Clearing is a repair somebody ASKS for through a delta arm, never something the run decides.

**The write is ONE call: `writer.update_frontmatter_field(path, "whatsapp", new_list)`.** It already takes
`vault_io.note_lock`, reads inside the lock, gates the delta with the note's own parsed `type:` and writes
under a stamp precondition (`writer.py:359-393`). So the migration introduces NO new frontmatter write arm,
adds no direct `write_text`, and AC-5 leg (b) is a STRUCTURAL claim about the module's call graph rather
than an observation about its results. A `NameGateRefusal` out of that call on a note the plan classified as
convertible is a LOUD failure that aborts the run — never caught and counted.

**The readback is a RE-READ.** `readback_migration` opens a FRESH `PersonRepository` over the vault path
itself, so the oracle is the note BYTES parsed by a load that did not exist before the write. A readback
computed through the migrating process's own repository compares a private replica with itself and is green
by construction whatever the bytes say — the repository holds a process-local cache and re-indexes the
entity it just wrote (`person.py:257-284` plus the save rider). Constructing the repository INSIDE this
module rather than in its test is also what lets the test module satisfy §8's zero-construction clause.

**The reconciliation identity is over the TRIPLE.** `plan_migration`, `apply_migration` and
`readback_migration` each report `(scalar_outside_residual, migrated, residual)`; `_cli` compares them PART
FOR PART and exits non-zero on any disagreement, naming the part that disagreed. One number agreeing is not
the check.

**THE RE-RUN IS A NO-OP, and it is ASSERTED rather than argued from the action table's shape.** A second pass
over an already-migrated vault — `plan_migration` again, then `apply_migration` with THAT fresh plan, which is
the same two steps `## Edge Cases`' retry remedy tells a conductor to take and never the first pass's stale
plan — takes the table's `already a list, every member in {A,B}` row for every converted note and the same
row's empty case for every shape-only note, so it writes NOTHING, converts nothing, repairs nothing and
reports the same residual R. That property is not decoration: it is what
`## Edge Cases`' retry remedy rests on — "a partial run leaves a vault in which the same command computes the
correct remaining work" — and it is the only remedy this design offers a conductor whose live run aborted
mid-vault, so leaving it in prose would leave the promise unpinned. Three things make the assertion honest
rather than nominal:

- **The discriminating oracle is a CALL COUNT, not a digest.** A tree digest cannot tell "no write" from
  "re-write the same bytes" — identical bytes give an identical digest — and AC-5's two-JID plant cannot
  either, since it is list-shaped from the start and so discriminates only "does not ABORT on a list". So the
  second pass is asserted to make **zero calls to `writer.update_frontmatter_field`**, counted by a wrapper
  installed with `tests/support.py`'s `patcher` for the duration of that pass, beside the digest (which still
  catches a re-write that REFORMATS) and beside the run's own reported numbers: the count of notes the write
  COMMITS is zero and the repair count is zero, while **the TRIPLE is unchanged rather than zeroed** — an
  already-list-shaped note is MIGRATED by the action table, so part (2) stays at its first-pass value and part
  (3) is the same R. "Nothing was written" and "nothing is migrated" are different claims and only the first
  one is true of a re-run.
- **The module must import the writer MODULE for that oracle to be reachable**: `from obsidian_schemas import
  writer` and a `writer.update_frontmatter_field(...)` call resolved at call time, never
  `from obsidian_schemas.writer import update_frontmatter_field`, which binds the function into the
  migration's own namespace and makes the counter blind. The ONE-CALL sentence above already spells it that
  way; this states WHY the spelling is prescribed rather than incidental.
- **The second drive is bound by §8's SPELLING clause exactly like the first.** BOTH `apply_migration(...)`
  call sites in the check pass the identifier `vault`, bound from the one `_temp_vault` door — a second drive
  spelled with any other expression is COLLECTED by the containment scan and raises there, which is the wall
  working and a confusing place to discover it.
- **A build that aborts on a list-shaped note is RED by intent** rather than by luck, because the second pass
  runs over the FIRST pass's output — every note it meets is list-shaped, and the run must complete and report
  rather than refuse.

### §8 The containment wall this item's migration joins, and the one clause it cannot take

AC-5 requires the migration driven "under the containment wall that proves the module drives only a temp
vault (`tests/derivations.py:mutating_drive_vault_args`)". That derivation collects a call only when its
callee is a member of `MUTATING_DRIVE_VAULT_POSITIONS` (`tests/derivations.py:2012-2017`, `:2230-2232`) —
today four names, all `lint_vault`'s. So the wall is VACUOUS over a new module until the dict names its
mutating entry point. One member is added:

```python
MUTATING_DRIVE_VAULT_POSITIONS = {
    "apply_fixes": 1,
    "quarantine_garbage": 1,
    "run_lint": 0,
    "main": None,
    # WI-032. `scripts/migrate_whatsapp_to_list.py`'s ONE mutating entry point.
    # `plan_migration` and `readback_migration` are read-only and are not
    # members: the census's subject is MUTATING drives. The CLI entry is named
    # `_cli` and not `main` deliberately — `main` is already a member with NO
    # vault-argument position, so a collected `main()` call RAISES, and reusing
    # the name would make this module's own CLI undrivable from a test.
    "apply_migration": 0,
}
```

The new test module then asserts, over its own source, every clause WI-029's own containment wall asserts
except ONE sub-assertion named below (`tests/test_stem_name_divergence_detector.py:141-192` is the shape to
copy literally). Six clauses plus the runtime door: SPELLING (every collected drive's vault argument is the
identifier `vault`); NON-VACUITY (the module drives something, so the wall is not empty); PROVENANCE (every
binding of that identifier is a call to the one `_temp_vault` door); SOURCE (the module names the live vault
path nowhere outside that door's own body); LIBRARY (zero `*Repository(...)` constructions anywhere in the
module — which §7's `readback_migration` design is what makes possible); IMPORT (no subprocess-capable
module, so no child process escapes the in-process clauses); and the runtime door EXERCISED rather than left
to whichever drive happens to run first.

**The one sub-assertion NOT available is inside the SOURCE clause, and it is DECLARED rather than dropped.**
WI-029's wall also asserts
`{n[2] for n in scan.live_path_names} == LIVE_PATH_TOKENS` — all three token shapes exercised inside the
door — and its door reads `lint_vault.DEFAULT_VAULT` to do it. This item's script HAS no `DEFAULT_VAULT`, by
§7's own rule. So the new module's door names TWO of the three tokens (`os.environ` and the literal
`"OBSIDIAN_VAULT_PATH"`, both inside `_temp_vault`'s body, asserting the built vault is not the live one),
and the module asserts that set by EQUALITY plus `not hasattr(migrate, "DEFAULT_VAULT")` — so the third
token's absence is a PROVEN consequence of the script's design rather than an unexplained gap in a wall.
Nothing is narrowed: the clause it replaces is strictly stronger about this module than a silent omission.

**The CLI is verified outside the hermetic suite.** `_cli` cannot be driven in-process from the graded module
(its argv path constructs a vault path the `drives` census cannot reduce to a door-bound name) and cannot be
driven as a child process (the IMPORT clause). It is exercised by the conductor in the live bracket, which is
where a CLI's real audience is anyway.

### §9 The frozen corpus: two EDITS, three plants elsewhere

Not "the fixture plant" — five itemized lines, two of which edit the frozen corpus and were mispriced as
free members for two rounds:

1. **`tests/fixtures/vault/@Thrandell Ibberly.md:7`** — `whatsapp: "447700900789@example.com"` becomes
   `whatsapp: "15555550142@lid"`. It is the corpus's SOLE person `roundtrip_representative`
   (`tests/fixture_vault.py:219-233`, uniqueness asserted at `tests/test_fixture_vault.py:689-695`) and two
   tests write it through the gated whole-record arm asserting NO refusal
   (`tests/test_writer.py:421`, `tests/test_fixture_vault.py:753`). Keeping a class-C value there makes a
   CORRECT build red and invites deleting the repo's only proof that a whole person field set survives the
   write door. Class A is structurally unavailable to it — STORABLE is membership of
   `{"s.whatsapp.net", "lid"}`, and `s.whatsapp.net` is reserved by no RFC, so WI-016's privacy wall
   (`tests/test_fixture_vault.py:302-319`, reach at `:386-392`) makes any `@s.whatsapp.net` literal RED
   anywhere in the corpus's reach. Class B it is, and `15555550142` matches the wall's third reserved phone
   pattern `^1?\d{3}55501\d{2}$` (`:308-312`) with no 555-01xx member anywhere in the corpus today.
2. **The DECLARED SHAPE moves with the value.** `tests/fixture_vault.py:225`'s override becomes
   `whatsapp=["15555550142@lid"]` — the LIST — while the NOTE keeps the scalar spelling, because
   `tests/test_fixture_vault.py:745-748` compares `getattr(doc.entity, attribute)` against the declared
   literal and `:755-761` compares the RE-PARSED frontmatter MAPPING against the same literal. The tolerant
   reader is what makes a scalar note and a list declaration agree. A builder who reads this as "change the
   string" gets it half right and red. `_person`'s default (`tests/fixture_vault.py:94`) becomes `[]` in the
   same move — machinery that travels with the field, easy to miss because it is not in `obsidian_schemas/`.
3. **`tests/fixtures/vault/@Fennwick Drostane.md:7`** receives the class-C value
   `whatsapp: "447700900789@example.com"`, with `whatsapp=["447700900789@example.com"]` added to its
   `NoteSpec` (`tests/fixture_vault.py:340-341`). The receiver is CONSTRAINED, not chosen: it must LOAD (never
   one of the three declared person skip specimens, `tests/fixture_vault.py:490-494`), declare NO
   `shape_classes`/`verdict` (the census verdict loop writes a shape-class specimen's whole declared field set
   through the gated door and asserts `exc.pattern` equals the DECLARED name pattern on its `kind == "refusal"`
   arm, `tests/test_fixture_vault.py:866-878`; see F18 leg 2 for why the constraint is stated over EVERY
   shape-class specimen and not only that arm), and NOT be stem-divergent
   (`@Perrowin Tessamund Drostane.md` and `@Yolvenna Brindlecote Skarnell.md` satisfy the first two and are
   the corpus's two MARKER-BEARING divergent notes, asserted by EQUALITY at
   `tests/test_stem_name_divergence_detector.py:341-345`). Eight notes satisfy all three;
   `@Fennwick Drostane.md` is the one, and the CONSTRAINT is what a builder reasons from when the named note
   stops being available.
4. **`CORPUS_DIGEST` (`tests/fixture_vault.py:44`) is regenerated** by the one-line command in that module's
   own docstring (`:21-25`). **`docs/vault-shape-census.md` is NOT touched — no row, no digest, no edit.**
   Its digest is asserted against a literal inside WI-016's SIGNED AC-3 `criteria` fence
   (`tests/test_fixture_vault.py:217-254`, `docs/vault-fixtures.md:1418`), its row vocabulary is
   name-corruption `branch_id`s with live-vault counts and NAME specimens, and its MEASURED rows are an
   EQUALITY against the manifest's `shape_classes` with a per-note `Verdict` over `name` — so a `whatsapp`
   value has no cell to occupy and the digest has no build-owned home. This item's per-cell counts live in
   `docs/wi-032-whatsapp-corpus-census.md`.
5. **Classes A, D and E and every boundary probe are literals of the NEW TEST MODULES' own temp vaults** and
   never enter `tests/fixtures/vault/` or `tests/fixture_vault.py`. `447700900321@s.whatsapp.net` (A) and
   `notaphone@s.whatsapp.net` (D) are wall-RED in the reach; `447700900654@lid.example` (E) is wall-clean
   only because `.example` is a reserved TLD matched by SUFFIX while `lid.example.com` is a SUBDOMAIN of
   `example.com`, which the frozenset matches by EQUALITY. `"+44 7739 341679"` — the one real identifier in
   the set, already committed at `docs/write-door-bypasses.md:3994` — must NEVER be moved into the corpus or
   its manifest. `tests/test_fixture_vault.py` is NOT a write target: no wall of it is widened, weakened or
   exempted.

### §10 The go/no-go disclosure surface: what the dry run PRINTS, and what the tracked bracket may never carry

**The FOUR `kind: required` mitigations of the threat model's two rounds — M1, M2 and M3 from
`## Threat Model — 2026-09-27` and M4 from `## Threat Model — 2026-09-27 (round 2)`, which re-emits the first
three byte-identically — folded here in one section because they share one generator.** That generator is not
a gap in the write path — the write path is `vault_io` and
the gate, and the threat model verified it. It is that the IRREVERSIBLE half of this item is authorized by a
HUMAN reading two artifacts, the migration's stdout and `docs/wi-032-whatsapp-live-baseline.md`, whose CONTENT
no section of this document specified; so every description of both defaulted to per-cell counts. Counts are
the right EXIT figure and the wrong GO/NO-GO figure, and an unspecified disclosure surface is also an
unspecified privacy surface. (a), (b) and (c) specify WHAT each surface carries and WHERE it may travel; (d),
added by round 2, specifies HOW the one surface that renders note-derived text renders it, which is the
property that makes (a) trustworthy at the moment it is read rather than merely present. Nothing here changes
what the migration writes, no `criteria` fence moves, and Rulings A, B and C are untouched.

**(a) The dry run prints the class-C repair per note, uncorroborated members first (M1).**

**`plan_migration` carries, per class-C note, a `RepairDisclosure(path, stored_value, proposed_jid, corroborated)` record whose `corroborated` is computed by `phones_match` over that note's OWN raw `phones[]`, and `format_repair_disclosure(plan)` returns one line per record with the UNCORROBORATED records FIRST under their own header, which `_cli` prints on every run BEFORE any write — so the 82 irreversible re-spellings are authorized with every stored-value → proposed-JID pair VISIBLE and the census's one uncorroborated member unmissable, never off aggregate per-cell counts.**

Four things about that sentence, because each is a decision and not a detail:

- **It is a PRINT, not a redesign.** `apply_migration(vault_path, plan)` already consumes a `MigrationPlan`
  that must hold the per-note action, so the pair is data the plan holds by §7's own construction; the record
  names it and the formatter renders it. `plan_migration` reads RAW frontmatter (§7), and `phones[]` is on the
  same mapping it already reads, so the corroboration flag costs no second read and no repository.
- **The flag, and not just the pairs, is what the census asked for.** AC-5 leg (d)'s key preservation is TRUE
  BY CONSTRUCTION of the repair spelling — the pre-migration key is `phone:<normalize_phone(v)>`, the
  post-migration key is `phone:<normalize_phone(f"{digits}@s.whatsapp.net")>`, and `normalize_phone` splits at
  the first `@` (`phone_normalization.py:52-55`), so the two are equal for ANY digit run whatsoever. A value
  carrying a number plus an extension (`"+44 20 7946 0958 x212"` → digits `442079460958212`) is class C, is
  phone-bearing, passes the guard, is rewritten into a JID belonging to nobody, and satisfies leg (c)'s
  multiset oracle and leg (d)'s key-preservation assertion identically. The readback cannot see it, by
  construction. The note's own `phones[]` is the only independent witness the corpus offers, and the census
  already computed it: `C:digits-already-in-own-phones[]` is **81** of **82**
  (`docs/wi-032-whatsapp-corpus-census.md:172`, its script at `:96-101`), so exactly one live member is
  uncorroborated and the census prescribes the remedy this fold delivers — "it is the one row worth eyeballing
  in the dry run" (`:207-208`). The disclosure recomputes the flag the SAME way the census did, by calling
  `phones_match(WhatsAppJID.parse(v).phone_digits, normalize_phone(p))` for each non-blank `p` in the note's
  raw `phones[]` — never by re-deriving an equivalence of its own.
- **The formatter RETURNS a string and does not print; `_cli` prints.** So the disclosure is asserted
  in-process without capturing stdout, and `format_repair_disclosure` is read-only — not a member of
  `MUTATING_DRIVE_VAULT_POSITIONS`, for exactly the reason `plan_migration` and `readback_migration` are not
  (§8): the containment census's subject is MUTATING drives.
- **Each rendered field is ESCAPED, and that is not a loss of fidelity — see (d).** The line carries the note
  path, the stored value and the proposed JID, each passed through `_escape_for_one_line`, so ONE PHYSICAL LINE
  PER RECORD is a property of the FORMATTER over any stored value rather than a property of the data. For the
  82 live members, all bare digit runs, the escape is the identity and the rendered line is byte-identical to a
  verbatim one — which is why nobody should later restore "verbatim" as a fidelity improvement: the escape is
  verbatim wherever verbatim is safe, and the only values it changes are the ones that would have reflowed the
  artifact or forged a header inside it.
- **The population is class C ONLY, and both arms of Ruling B print it.** Classes A and B need no repair, D
  and E are byte-identical and reach the conductor through the detector's count, and Ø is shape-only with no
  pair to show. Under `--no-repair` the same records print under a header stating that no repair will be
  attempted and that those notes join R — the conductor sees the same 82 pairs either way, which is what makes
  Ruling B's alternative arm readable rather than hypothetical.

**The three names a builder and a test have to agree on, so neither re-types a literal.** The records live on
`plan.repairs: list[RepairDisclosure]` — the same `MigrationPlan` `apply_migration` already consumes — and the
two section headers plus the alternative-arm banner are MODULE CONSTANTS the check IMPORTS rather than spells:

```python
#: WI-032 M1. The dry run's repair disclosure. Section order is the mitigation:
#: the uncorroborated members are printed FIRST because there is exactly one of
#: them on the live corpus and it is the row the census asked a human to read.
UNCORROBORATED_HEADER = "UNCORROBORATED — digits not in this note's own phones[]:"
CORROBORATED_HEADER = "CORROBORATED — digits already in this note's own phones[]:"
NO_REPAIR_BANNER = "NO REPAIR (--no-repair): these notes are NOT rewritten and join the residual R:"
```

The record carries a vault note PATH and a real stored telephone number. That is the point of it, and it is
why (b) exists in the same fold rather than after it.

**(b) That detail lives on stdout and never in a tracked document, and this item ships the wall (M2).**

**The repair pairs and the detector's per-note issue lines are STDOUT of the conductor's live run and are NEVER written into `docs/wi-032-whatsapp-live-baseline.md` or any other tracked document — which carries counts, classes and code paths only — and because `docs/**` is outside the repo-wide markdown scan's domain (`DOC_SCAN_EXCLUDED = {".git", ".venv", "docs", "state", "node_modules"}`, `tests/test_vault_path_required.py:387`, intersected against every path part at `:425`) nothing standing would catch a pasted live identifier, so this item ships that wall itself: a check over the bracket file's FINAL text asserting that no JID-shaped token and no run of nine or more digits survives outside a 40-hex commit token.**

- **Why a wall and not the instruction we already have.** Task 13 says "counts, classes and code paths only:
  no vault note name, no live identifier" and the close-out says "redact the transcript before it is recorded
  in any tracked document". Both are prose, and (a) has just made the natural conductor move — paste the
  detail you were shown into the document where you record what you decided — carry 82 real telephone numbers.
  A transparency mitigation implemented naively is an information-disclosure defect; the wall is what keeps (a)
  from becoming one.
- **The predicate, stated exactly, because its false-positive mode is MEASURED rather than imagined.** Strip
  every `\b[0-9a-f]{40}\b` token FIRST, then refuse any `\d{9,}` run, and refuse a digit immediately followed by
  `@` and a domain label. The strip is not caution: every HEAD the entry row copies is a 40-hex token, and two
  of the ones recorded in `docs/wi-032-consumer-audit.md` already carry nine-digit runs INSIDE them — `984664193`
  in `:92`'s and `588953919` in `:144`'s, which are that artifact's ONLY two nine-digit runs — so an unstripped
  scan fires on correct content, gets read as noise, and is narrowed back under pressure with nothing checking
  that the narrowing kept the claimed shapes: the WI-235 failure, closed in advance. The BARE domain literals `@s.whatsapp.net` and `@lid` are deliberately NOT refused: §2 of
  that document names them as the storable classes' domains and must keep being able to.
- **It ships its claimed match-shapes as fixtures (WI-235), driven through the same predicate.** MUST match:
  `"15555550142"`, `"123456789012@s.whatsapp.net"`, `"15555550142@lid"` — RESERVED-block and synthetic literals
  only, per threat-model note 3, because a wall over live identifiers has no business introducing one and the
  predicate cannot tell a reserved eleven-digit run from a real one. MUST NOT match:
  `27cb78cc5a2099972dccea984664193e69414def` (the real pinned HEAD carrying `984664193`), the counts
  `1168` / `1025` / `82`, the line range `663-665`, the date `2026-09-27`, and the bare `@s.whatsapp.net`. A
  wall that passes by matching nothing and a wall that passes by matching everything are both closed by that
  pair of lists.
- **Scope: all THREE `docs/wi-032-*` artifacts, and deliberately NOT this document.** The sentence above names
  the bracket because that is the file M2 names and the only one this item WRITES; the check runs the same
  predicate over the two grounding artifacts as well, which closes the class this item's docs form instead of
  the one instance. Both are clean under it today, measured in this worktree: the census carries no nine-digit
  run and no digit-before-`@` at all, and the consumer audit's ONLY two nine-digit runs are the two inside the
  pinned HEADs named in the bullet above. This document is excluded, and the exclusion is a ratified
  decision rather than an oversight: `## Design` §9 line 5 and F18 leg 6 deliberately keep `"+44 7739 341679"`
  in it, already committed twice in this tree, and threat-model note 3 re-examined that and declined to move it
  because AC-3 is frozen. A predicate run over this file would be RED against a state two gates ratified.
- **It keeps holding after the close-out.** The check asserts the §5 heading EXISTS and asserts NOTHING about
  its content — the conductor writes the exit figures there after the build, and a check pinning §5 empty would
  redden the floor at exactly the moment the item closes. The redaction predicate still holds over §5, because
  what §5 carries is the partition's three parts as counts.
- **One sentence of honesty about the detector.** Its `LintIssue` carries `vf.path` (§4), a vault note NAME —
  so "the detector reports counts" is true of the COUNT that `## Approach` step (4) uses as the independent
  second witness to `|R|`, and false of its per-issue lines. Those lines are stdout, like (a)'s pairs.

**(c) The one silent destructive consumer break is stated as its own HOLD, not as item three of a list (M3).**

**`docs/wi-032-whatsapp-live-baseline.md` §3 states the two LOUD breaks as its ordered list — `orchestrator/src/invariants.py:663-665`, a vault-wide red invariant, and `HAL9000/backend_fastapi/routers/contacts.py:41,50`, a 500ing endpoint — and states `orchestrator/bin/merge-duplicate-persons.py:380-384` in its OWN row under the heading `DATA-LOSS HOLD`, because that site regex-reads a single `whatsapp` line and re-emits a scalar through `Path.write_text` outside the package boundary, so against a migrated vault it can silently collapse a person's list to one value or blank the field — the exact harm this item exists to prevent, and the only one of the three that does not announce itself.**

- **Why the separation IS the mitigation.** Three consequences in one list read as three annoyances to be
  weighed together. Two of these announce themselves the instant they break — an invariant goes red vault-wide,
  an endpoint 500s — and are therefore self-limiting and repairable at leisure. The third is silent, is
  destructive, and destroys precisely the value this item exists to protect. A conductor reading a flat list
  cannot see that difference; a conductor reading a HOLD row cannot miss it.
- **What the HOLD row carries.** The pinned 40-hex HEAD from `docs/wi-032-consumer-audit.md`; the reaching
  callers (`bin/apply-vault-review.py:152,158`); the clearing path measured by the audit — `:383-384` emits
  `whatsapp: ""` when its single-line regex misses a block-YAML list (`docs/wi-032-consumer-audit.md:202-204`);
  and ONE instruction for the conductor, which is what makes it a hold rather than a note: after the migration,
  `merge-duplicate-persons.py` and `apply-vault-review.py` are not to be run against the vault until that
  repository's own item fixes the writer. It is not this repo's to fix (`## Scope Boundary`) and it is already
  on the WI-029 divergence-generator list; the hold is how the item declines to fix it without leaving the
  hazard un-stated.
- **The audit's list is SEVEN sites, and the entry row says so.** `docs/wi-032-consumer-audit.md:227-239`
  enumerates seven, all of them tripped by the VALUE becoming a list and none by the door refusing anything.
  The entry row names the first three individually — two loud, one held — and carries a one-line pointer to the
  audit for items 4–7 (`find-duplicate-persons.py`, `generate-vault-review.py:450`, the enricher role's PATCH
  body, and the two latent `ContactInfo` mirrors) rather than re-listing them, so the go/no-go is taken against
  the whole measured blast radius with the destructive site separated out of it.

**(d) Every field the disclosure renders goes through ONE escape, so "one line per record" is a property of the formatter and not of the data (M4).**

**`format_repair_disclosure` renders EVERY field of every `RepairDisclosure` — `path`, `stored_value` and `proposed_jid` alike — through the single module-level helper `_escape_for_one_line`, which escapes the backslash first and then renders as a visible `\xNN`/`\uNNNN` escape every character `str.splitlines()` treats as a line break and every character whose `unicodedata.category` is `Cc`, `Cf`, `Zl` or `Zp` (so the newline, the carriage return, the tab, the ANSI `\x1b` and their whole class), which makes ONE PHYSICAL LINE PER RECORD a guarantee of the formatter over ANY stored value instead of an accident of the data — and Task 10's M1 check plants an UNCORROBORATED class-C note whose stored value carries an interior newline followed by the text of `CORROBORATED_HEADER` and asserts that the output's line count still equals the record count plus the headers the formatter itself emitted, and that no output line EQUALS a header constant the formatter did not emit.**

- **Why a stored value can carry a control character at all — verified in the code, not supposed.**
  `WhatsAppJID.parse` normalizes with `str(raw).strip().lower()`
  (`obsidian_schemas/identifier.py:WhatsAppJID.parse:273`) and `.strip()` removes only LEADING and TRAILING
  whitespace, so an interior newline, carriage return, tab or ESC survives into `.jid` intact; `normalize_phone`
  then splits at the first `@` and deletes every non-digit
  (`obsidian_schemas/phone_normalization.py:normalize_phone:52-55`), so
  `"447700900321\n<any text carrying no @ and no digits>"` yields twelve digits, parses, is phone-bearing, has
  an empty `jid_domain`, and is therefore **class C** — the exact population (a) prints, and the exact
  population the repair rewrites. The doors that can produce it are the same three unvalidated ones that wrote
  the Kim Faura value, which is this item's whole premise; the census measured the 82 as bare numbers with no
  `@` and was never asked about interior control characters, so neither the census nor the corpus is evidence
  that none is there.
- **What breaks without it is not an ugly line.** Rendered raw, one record becomes two or more physical lines:
  the conductor's line count no longer equals the repair count, the UNCORROBORATED-FIRST ordering that is the
  whole point of (a) stops being visually reliable, and a stored value carrying a newline plus the text of
  `CORROBORATED_HEADER` renders a FORGED section header into the one artifact an irreversible 82-note go/no-go
  is read against — i.e. the disclosure can be steered by the very data it exists to disclose. The harm is
  legibility and forgery, not corruption: the repair itself reads only `phone_digits`, so such a value still
  repairs to a clean canonical JID and no note is damaged. That is why this is a formatter fold and not a
  change to the action table.
- **The rule is stated over the CLASS that generates the hazard, not over the four characters the finding
  named.** Escaping `\n`, `\r`, `\t` and `\x1b` alone leaves U+000B, U+000C, U+001C–U+001E, U+0085 NEL,
  U+2028 LINE SEPARATOR and U+2029 as the next round's finding — `str.splitlines()` breaks on every one of
  them, so a four-character escape still reflows the artifact. So the check DERIVES the first set instead of
  listing it: `BREAK_CODEPOINTS = frozenset(cp for cp in range(0x110000) if len(f"a{chr(cp)}b".splitlines()) > 1)`,
  computed ONCE at test-module level (~1s, which is why it is computed once and why a builder must not
  "optimize" it into a hand list — a hand list is the defect this bullet exists to prevent), and the second set
  is read from `unicodedata.category`. The assertion is then total over both derived sets rather than over a
  sample: for every codepoint in `BREAK_CODEPOINTS`, `_escape_for_one_line(f"a{chr(cp)}b").splitlines()` has
  length 1; and for every one of them plus `\x1b`, the escaped rendering contains no such raw character. A
  character in neither set is passed through unchanged — the escape narrows nothing else.
- **The two sets are ONE rule, not a union a builder has to compose.** The category set CONTAINS the break set
  — every character `str.splitlines()` breaks on is `Cc` (`\n`, `\r`, `\x0b`, `\x0c`, `\x1c`–`\x1e`, `\x85`),
  `Zl` (U+2028) or `Zp` (U+2029) — so the implementation is the CATEGORY test alone, and the derived
  `BREAK_CODEPOINTS` leg exists to prove that containment on the running interpreter rather than to add a
  second rule. If a future Python breaks on a character outside those four categories, that leg goes RED and
  says so, which is the whole point of deriving it. The rendering itself is pinned so the builder makes no
  judgment call: the backslash first as `\\`, then `f"\\x{cp:02x}"` for a codepoint below `0x100` and
  `f"\\u{cp:04x}"` for the rest.
- **It escapes the fields that are clean BY CONSTRUCTION too, and asserts the escape is a no-op on them.**
  `proposed_jid` is `f"{digits}@s.whatsapp.net"` built from `normalize_phone` output and so is digits-only
  today; `path` is a filesystem name, which on POSIX may legally contain a newline. Routing all three fields
  through one helper makes the guarantee total over the RECORD rather than over the one field the finding
  named, and it survives a future change to the repair spelling that the finding's per-field fix would not. The
  check asserts `_escape_for_one_line(x) == x` for every field of every CLEAN plant, which is simultaneously
  the fidelity leg: escaping is the identity on every value that would not have broken the render, so the 82
  live bare digit runs print exactly as a verbatim render would print them.
- **The oracle becoming TOTAL is the second thing this buys, and the reason it belongs in (a)'s own check.**
  Before the escape, "the line set is EXACTLY one line per class-C plant" held only over CLEAN plants — an
  oracle that stays green while a whole cell of its input space is unclassified, which is the shape this
  document rejects everywhere else and the stated reason class E is asserted rather than assumed. After it, the
  same assertion holds over ANY stored value, and the adversarial plant is what makes the difference
  falsifiable rather than asserted.
- **The plant is asserted to BE the shape it claims, or the leg is vacuous.** It is planted as a YAML
  double-quoted scalar carrying the `\n` escape, through the SAME `_temp_vault` door every other plant in that
  module uses (so §8's PROVENANCE clause is unaffected), and three things about it are asserted before
  anything is asserted with it: the value the migration reads back out of the note actually CONTAINS the
  planted control character (a plant that silently became clean proves nothing); `classify_field` called on it
  returns exactly `["C"]`; and `phones_match` called over that note's own `phones[]` returns False for it, so
  it lands in the UNCORROBORATED section — the section where a forged `CORROBORATED_HEADER` would do the most
  damage, by appearing to move the one row the census asked a human to read into the safe half. Its number is a
  RESERVED-block literal (`447700900321`), per threat-model note 3: a fold about rendering live identifiers has
  no business introducing one.
- **The ladder, swept, and what the sweep FOUND — because closing this instance is not the fold.** The
  generator M1, M2 and M4 share is an unspecified property of a disclosure surface. Round 1 closed WHAT and
  WHERE; this closes HOW. **Members** (the record's fields): all three escaped, above. **Dimensions** (every
  surface this item's own new code renders text into that could carry a note-derived value): the sweep returns
  six besides the formatter — five already closed, one deliberately declined. `_cli`'s other output is per-cell
  counts, class letters and the
  reconciliation's part NAMES from a fixed set, none note-derived; the non-zero exit message names the part
  that disagreed and no value; the detector's `LintIssue` message interpolates `len(classes)` and the sorted
  class letters and nothing else (§4, and its own closing sentence says so); `NameGateRefusal` carries the
  value on `.refused_value` and puts it in neither message nor traceback (§3, `## Edge Cases`' error
  propagation); and the tracked bracket is walled by (b). The ONE surface the sweep returns that is NOT closed
  here is `lint_vault`'s own per-issue rendering of `vf.path`, and this fold deliberately declines it: that is
  pre-existing `lint_vault` behaviour on every check it has ever had, (b) already discloses it honestly as
  stdout-only, and owning another tool's formatter is the widen-another-surface move rejected items 11, 14 and
  15 decline three times. **Intersections:** a value that is both control-character-bearing and NOT class C
  reaches no disclosure line at all (the population is class C only), and reaches the detector, whose message
  carries no value — so the intersection is empty by the dimensions above rather than by luck. **Sub-cells**
  (within class C): the cells are {corroborated, uncorroborated} × {clean, control-bearing}, and Task 10's M1
  check plants all four, with corroboration computed by CALLING `phones_match` and class by CALLING
  `classify_field` in every cell — never from a flag written beside the plant.
- **Cost and blast radius.** One helper in `scripts/migrate_whatsapp_to_list.py` plus the one stdlib import it
  needs (`unicodedata`, which is not subprocess-capable and so is outside §8's IMPORT clause), two more plants
  and one derived codepoint set in `tests/test_whatsapp_migration.py`. The helper is read-only and is not a
  member of `MUTATING_DRIVE_VAULT_POSITIONS`, for the same reason `format_repair_disclosure` is not (§8). No new
  `## Write Targets` path, no
  `criteria` fence moved, no signed span touched, no change to what the migration WRITES, and Rulings A, B
  and C untouched — so no D4b re-sign is implied.

**All four are asserted, and no assertion is an acceptance criterion.** (a) and (d) are Task 10's
`test_whatsapp_dry_run_discloses_each_class_c_repair_pair`; (b) and (c) are Task 13's
`test_wi032_live_baseline_row_shape_and_redaction_wall`. Both are plan-task `verify:` checks over this item's
own new modules — the five frozen `criteria` fences are untouched, which is what makes this fold additive
rather than a D4b re-sign.

### Configuration

No settings, no thresholds, no toggles in the library. Three flags, all on the migration CLI, all explicit:

| flag | default | range | where |
|---|---|---|---|
| `--vault` | **none — required** | an existing directory | `scripts/migrate_whatsapp_to_list.py:_cli` |
| `--apply` | absent (dry run) | present / absent | same |
| `--no-repair` | absent (class C IS repaired) | present / absent | same |

`--no-repair` exists because Ruling B's alternative arm must be EXECUTABLE, not hypothetical: AC-5 leg (d)
asserts both arms, and under the alternative class C joins R and `|R|` grows by the census's 82.
`STORABLE_DOMAINS` is a frozenset on the type, not configuration — widening it is a code change that joins
every sweep automatically because every criterion calls the predicate.

### Prerequisites & Assumptions

Stated, not implied. Each is either a precondition already in HEAD, a floor fact, or a named limit.

1. **Both grounding artifacts are in git HEAD before the AC frame** — `docs/wi-032-whatsapp-corpus-census.md`
   and `docs/wi-032-consumer-audit.md`. Satisfied: both landed 2026-09-27 and the data-premise gate read
   them. Their `writes` fences below are kept VERBATIM.
2. **Rulings A, B and C are RULED** (2026-09-27, in-session) and the ACs are FROZEN by Dave's signature
   (`ac_hash dd772c1183de`). The build implements the recommended arm of each. A change to any of them is a
   D4b re-sign, not a build decision.
3. **No service must be running for the build.** The hermetic suite needs no vault, no HAL9000, no
   exocortex, no WhatsApp bridge. `OBSIDIAN_VAULT_PATH` is UNSET in the graded environment and every test
   supplies its own temp vault.
4. **The floor interpreter is the project's own `.venv`.** System python has no pytest, and this `.venv`'s
   editable install is STALE by design — `import obsidian_schemas` fails under a bare interpreter and the
   suite works because pytest prepends its rootdir to `sys.path`. That is load-bearing and must not be
   "fixed" (`pipeline-runners.yaml:10-17`).
5. **`README.md` is NOT builder-writable and nothing in the build depends on it.** The project root is
   absent from `write_authority` on purpose (`pipeline-runners.yaml:32-33`) — `README.md` is conductor-owned
   session-end work. Nothing breaks: `README.md:52` is a field-NAME list the type change does not touch, and
   `README.md:238`'s `get_by_phone("447990558521@s.whatsapp.net")` still works because a phone-bearing JID
   pivots to the phone door (AC-2's third guard asserts the BEHAVIOUR, which is what the criterion is about;
   it does not ask for a README edit). The additive documentation of the list shape and of
   `get_by_identifier` is `/wrap-up` work outside the cage.
6. **Atomic landing is NOT required here, and the check was run rather than assumed.** No file this item
   writes participates in a bijection or symmetry invariant the PRE-DRIVE floor enforces against a
   consumer that lands separately. The three set-equality walls the new test modules join
   (`tests/test_fixture_vault.py:1373-1395`, `:569-580`) are satisfied by each module's own text with no
   cross-file registration; `CORPUS_DIGEST` and the two corpus notes are a bijection and they land in the
   SAME commit as each other by being the same build; `MUTATING_DRIVE_VAULT_POSITIONS` and the migration
   module likewise.
7. **Trust boundaries.** Three. Two are UNTRUSTED → TRUSTED crossings the gate now owns: a caller's
   untyped value arriving at any of the three dict-shaped write doors, and a note's own STORED value
   arriving back through a whole-record projection. `lint_vault` reads untrusted vault bytes and must not
   crash on any of them (§4's `try`). The third is UNTRUSTED → HUMAN and is added by M4's fold: a note's
   stored value RENDERED into the repair disclosure a conductor authorizes 82 irreversible re-spellings
   against, which crosses escaped so that the disclosed data cannot reflow the artifact or forge a section
   header inside it (§10(d)) — an output boundary rather than an input one, which is why it was missing from
   this list until the threat model's second round asked for it. No new outbound API, no new credential, no new
   OAuth scope, no new persisted state outside the vault notes the migration writes.
8. **The live run is a SHIP CONDITION performed by the conductor, not by the build.** The caged builder's
   vault writes are reverted at the merge boundary, so a plan-task live run changes nothing and reports
   success. `## Approach` step (4) owns it; `## Verification` prescribes it as a close-out step.
9. **This item does not populate second JIDs.** It makes the shape available; HAL9000 WI-075 and
   orchestrator WI-192/193 fill it. That is what keeps the back-out's second qualifier true on day one.

## Edge Cases & Open Questions

Each category walked. Every resolution is Case / Decision / Reasoning; the ones that do not apply say so.

**Empty / null / malformed input.**
- **Case:** a `whatsapp:` key that is absent, `""`, whitespace-only, a BARE valueless `whatsapp:` (YAML
  null), or `[]`.
- **Decision:** all five are class Ø. They introduce no identifier, neither predicate is ever called on them,
  every write arm ACCEPTS them, the reader presents the empty collection, and the migration converts only the
  key-PRESENT-but-empty spelling.
- **Reasoning:** absence is not malformation, and refusing it bricks the only repair channel this design has —
  the writer has no delete affordance, so clearing IS the repair for a class-D value. It is also the
  package's own existing convention (`person.py:318-320`, `name_gate.py:399`) and the value on 1025 of 1174
  live person notes. The bare-key spelling is the one that does NOT work today: it raises `SchemaDriftError`
  and lands on the load skip surface, INVISIBLE rather than empty.
- **Case:** `whatsapp:` holding a nested container, an int, a date, or a list with a non-`str` member.
- **Decision:** a non-`str` scalar is classified through `parse` — an unquoted number or a date lands in C
  (its `str()` carries enough digits), digit-poor junk in D; §1 states both. A CONTAINER handed to the
  per-value classifier RAISES `IdentifierError`. `lint_vault` catches that one refusal and reports the note
  under its own check; the gate does not catch it, so such a WRITE fails loudly.
- **Reasoning:** `parse(["447700900321@s.whatsapp.net"])` SUCCEEDS with the right digits, recovered out of
  the list's repr — the one shape that produces a plausible wrong answer rather than an error. A tool whose
  job is finding malformed notes must not crash on one; a door whose job is refusing bad writes must not
  silently accept a shape nobody designed.
- **Case:** `whatsapp` holding a list with a BLANK member — `[""]`, `["   "]`, or a good member beside a
  blank one.
- **Decision:** REFUSED at every write arm and REPORTED by the detector. The blank member classifies Ø
  per-VALUE, the arm accepts only A and B, and `## Design` §3 states the rule and its reasoning in full.
- **Reasoning:** class Ø is a property of the FIELD (absent key, `""`, whitespace, `None`, `[]`), not a
  licence for a blank member inside a populated field, and no arm of this design produces `[""]` — the model
  coerces `""` to `[]` and the migration writes `[]` for the whole class-Ø cell. The `emails[]` arm drops such
  a member instead (`name_gate.py:399`); this arm declines that because a drop is a silent drop and because
  filtering it would break the positional correspondence the refusal uses to name the offending value.
- **Case:** a stored `whatsapp` value carrying an INTERIOR control character — a newline, carriage return, tab,
  vertical tab, ANSI `\x1b`, U+0085 NEL or U+2028 — next to enough digits to parse.
- **Decision:** it is an ordinary member of its class and nothing special happens to it in the library: `parse`
  strips only the ends (`identifier.py:WhatsAppJID.parse:273`), `normalize_phone` deletes every non-digit
  (`phone_normalization.py:normalize_phone:52-55`), so such a value with no `@` is phone-bearing, domain-less
  and **class C** — refused by the write door like any other class C, reported by the detector, and repaired by
  the migration to a clean canonical JID off its digits. The ONE place it is handled specially is the migration's
  repair DISCLOSURE, which renders every field through `_escape_for_one_line` (`## Design` §10(d)) so one record
  is one physical line whatever it holds.
- **Reasoning:** the value is not more dangerous to the vault than any other class C — the repair reads only
  `phone_digits`, so no note is corrupted. It is dangerous to the ARTIFACT a human authorizes 82 irreversible
  re-spellings against: raw, it reflows the disclosure so the line count stops equalling the repair count, and a
  value carrying a newline plus the text of `CORROBORATED_HEADER` forges a section header into that artifact. So
  the remedy is at the render and not at the parser — changing `parse` would move a surface AC-3, AC-5 and
  Ruling A all rest on, for a hazard that is entirely one of presentation.

**Race conditions / concurrent access.**
- **Case:** two callers write the same note while the migration is walking the vault.
- **Decision:** unchanged from today — every write goes through `vault_io.note_lock` with a stamp
  precondition, taken INSIDE the door (`writer.py:368-393`). The migration adds no lock and holds none
  across notes.
- **Reasoning:** WI-004 owns this and the migration deliberately reuses the one door rather than composing a
  batch transaction. A stamp mismatch surfaces as `WriteFailedError`, which the run does not catch — it
  aborts, and the operator re-runs the dry run.
- **Case:** a concurrent refresh clears `_phone_index` while `get_by_phone`'s fuzzy arm iterates it.
- **Decision:** unchanged — that iterable is already a MATERIALIZED snapshot (`person.py:490-494`). §5(b)'s
  inverse is a lookup, not an iteration, so it adds no new site.

**External dependency failure.**
- **Case:** the vault path does not exist, or is not readable.
- **Decision:** `--vault` is required and the run fails at argument validation. The library's repositories
  already raise `VaultPathNotConfiguredError` naming both routes.
- **Case:** HAL9000 / exocortex / the WhatsApp bridge is down.
- **Decision:** does not apply to the build. Nothing in the library or the migration calls any of them; the
  consumer audit was taken read-only and is already committed.

**First-run vs subsequent-run.**
- **Case:** the migration runs twice.
- **Decision:** the second run finds every convertible note already list-shaped, classifies it MIGRATED, and
  writes nothing. The residual R is reported identically both times. **Asserted, not argued:** AC-5's check
  drives a SECOND pass over the already-migrated copy — a fresh `plan_migration`, then `apply_migration` —
  and pins zero calls to `writer.update_frontmatter_field`, a byte-identical tree digest and a triple
  unchanged from the first pass's (Task 10; the oracle, and why the call count rather than the digest is the
  discriminator, are in `## Design` §7).
- **Reasoning:** the action table keys on the STORED shape, not on a marker, so idempotence is structural
  rather than bookkept. This is also why no `schema_version` field is added — WI-010's un-park question. The
  structure is the reason the property holds; the check is why the next reader can falsify it, and it is owed
  because the retry remedy below is the only one this design offers.

**Migration / backfill.** This item IS the migration; §7 is its whole design, and `## Approach` step (4) plus
`## Exploration Notes`' TERMINAL-STATE PARTITION state the terminal state. One thing worth restating here
because it is the counter-intuitive half: the notes in R are terminally SCALAR **by design**, because a shape
conversion is a write that RE-INTRODUCES the field and the door refuses it in both shapes
(`name_gate.py:31-36` keeps a stored-dirty note writable only for writes that do NOT re-introduce the field).
On the live vault `|R| = 0` today, so the partition's part (3) is empty and the detector ships as a wall
against the next bare number rather than as a backlog — but AC-5's mandated class-D and class-E plants make
`|R|` non-empty on the hermetic suite, which is where the contradiction F21 removed used to live.

**Idempotency.** Yes, at four levels, and each is asserted rather than claimed: the dry run leaves the tree
byte-identical (a digest before and after); `gate_write` is idempotent on both values of `whole_record` and
is required to be, because one `PersonRepository.save` invokes it twice (`name_gate.py:296-299`);
load → save → load is a fixed point on the field for every member the door accepts, with the refusal plus
unchanged bytes as the fixed point for every member it refuses; and — the fourth, which this round adds
because it was the one resolved in prose and asserted nowhere — the MIGRATION'S OWN RE-RUN writes nothing
over an already-migrated vault, pinned by a zero call count on the write door plus the digest plus the triple
(`## Design` §7, Task 10).

**Retry semantics.**
- **Case:** the run aborts partway — a lock timeout, a stamp mismatch, a `NameGateRefusal` on a note the plan
  said was convertible.
- **Decision:** the run exits non-zero having written whatever it committed, and the REMEDY is to re-run the
  dry run and read the new per-cell counts. No retry loop, no resume file.
- **Reasoning:** every write is individually atomic and the action is a pure function of the stored shape, so
  a partial run leaves a vault in which the same command computes the correct remaining work. A retry loop
  would be machinery around a property the design already has — and the property is the RE-RUN NO-OP above,
  which is asserted in Task 10 rather than inferred from the action table, because this remedy is the only
  one this design offers a conductor whose live run aborted mid-vault. A `NameGateRefusal` on a supposedly
  convertible note means the plan and the door disagree, which is a defect and not a transient — it must
  abort loudly rather than be counted.

**Partial failure.**
- **Case:** note 400 of 1168 fails.
- **Decision:** the 399 committed writes stand, the reconciliation over the triple DISAGREES, and the run
  says so and exits non-zero naming the part that disagreed.
- **Reasoning:** this is exactly what the triple is for. A run that reported one number could finish quietly
  on a partial pass; three parts that must agree cannot.

**Error propagation.**
- **Case:** what does a caller see when a write is refused?
- **Decision:** `NameGateRefusal` — a leaf of `LoudFailError` (a `ValueError`) — carrying `.pattern ==
  "whatsapp_not_a_jid"` and `.refused_value` as ATTRIBUTES, with the note-derived value in NEITHER the
  message nor the traceback (`chainable_cause` suppresses the context).
- **Reasoning:** F4's contract. A handler that ABSORBS names the LEAF it means; a handler that RE-RAISES may
  filter on `LoudFailError`. The distinct `pattern` is what stops a bad JID being reported and routed as a
  bad name.
- **Case:** what does a caller see when a stored value is unstorable?
- **Decision:** the note still LOADS (the reader is tolerant and drops nothing), the raw string is still on
  the model, the typed accessor omits only what does not PARSE, and re-serializing the whole record refuses
  until the value is repaired — while every delta write still succeeds.
- **Case:** what does a caller see when the payload's `whatsapp` value is a CONTAINER (a dict, or a nested
  list) — the one shape `classify_field` refuses rather than classifies?
- **Decision:** `IdentifierError`, not `NameGateRefusal`. The gate does not catch it (decided above), so ONE
  write door raises two exception types across its arms and only one of them is reachable by the estate's
  documented `except LoudFailError` idiom — `IdentifierError` is a plain `ValueError` (`identifier.py:67`) and
  is NOT a member of the `LoudFailError` tree (`errors.py:37`, `:106`). Stated here rather than closed, per
  threat-model note 1, because it fails CLOSED (nothing written), leaks nothing (the message is
  `f"{kind}: {detail}"` with the raw value on `.raw` as an attribute, `identifier.py:76-80`), and can only
  arrive from a caller's raw dict: a STORED container is rejected by `List[str]` validation and lands on the
  load skip surface long before `save`. A consumer author wanting both arms catches `ValueError`.
- **Reasoning:** widening the hierarchy or catching-and-re-raising inside the gate are both real changes to
  another item's contract (WI-020's one-hierarchy rule) bought for a shape no writer in three repos produces
  (`docs/wi-032-consumer-audit.md`). Writing the sentence down is the whole remedy the threat model asked for.

**Trust boundary crossings.** Prerequisite 7 enumerates all three. Four properties hold across them: no
note-derived value enters any exception message; the classifier is TOTAL and loud on the one shape that
produces a plausible wrong answer; the refusal is evaluated on the value the WRITE CARRIES, never on the
value the note used to hold, which is what makes a repair land through any door; and the one surface that does
render a note-derived value for a human to read — the migration's repair disclosure, the third crossing —
renders every field ESCAPED, so the stored value cannot reflow that artifact or forge a header inside it
(`## Design` §10(d)).

**"What if" from exploration, folded here so it is not re-asked.**
- **Case:** someone wires the STORABLE predicate into the RESOLVER as well.
- **Decision:** RED on AC-2 — classes C and E are asserted resolvable. Resolution stays liberal; only the
  write door asks the storable question.
- **Case:** someone puts `get_by_identifier`'s lookup inside `resolve`.
- **Decision:** RED on `tests/test_identity_endgame.py:692-698`, which is the right outcome and is named in
  advance so it is not debugged from scratch.
- **Case:** a future item widens `STORABLE_DOMAINS`.
- **Decision:** free, and it joins every sweep automatically — the criteria CALL the predicate rather than
  restating its membership.

OPEN: None.

## Implementation Plan

Fourteen tasks, dependency-ordered, top-to-bottom. Tasks 2–4 are independent of tasks 5–9 and could be
parallelised; the serial reading is safe and is the one written. Every `verify:` check name below is a
top-level `def <name>(` taking ZERO arguments and signalling failure by RAISING — the conveyor discovers a
check by source-scanning the test roots and invokes it with no arguments, so a fixture parameter raises
`TypeError` and a `return False` exits 0 and reads as PASS. **Every one of these names must also be globally
unique across `tests/test_*.py`**, because `check_module` is a `def <name>(` SUBSTRING scan that raises on
anything but exactly one match (`tests/test_ac_interpreter.py:95-106`).

- [x] **Task 1 — Record the pre-build floor baseline.** Run the floor command
      (`.venv/bin/python -m pytest tests -q` from the worktree root) BEFORE the first edit and write the
      passing case count into the Build Log. No assertion anywhere pins the number; Task 14 compares against
      it, and the invariant is DIRECTIONAL — a later drive landing fewer cases with no explanation has
      silently lost a test file.
      verify: baseline — the pre-edit floor case count, recorded in the Build Log; Task 14 reads it and no check asserts it

- [x] **Task 2 — The two predicates and the classifier on `WhatsAppJID`.** Add `STORABLE_DOMAINS`,
      `CLASS_ABSENT`, `CLASSES`, `jid_domain`, `is_storable`, `classify` and `classify_field` to
      `obsidian_schemas/identifier.py:WhatsAppJID` exactly as `## Design` §1 states. `parse` is UNCHANGED —
      not one line. Extend `tests/test_identifier.py`'s `WhatsAppJID` block (`:119-143`) with the storable
      predicate and the classifier, and add `tests/test_whatsapp_jid_storage.py` with
      `test_whatsapp_storable_predicate_and_classifier`, which asserts: `jid_domain` off the NORMALIZED
      string (so `447700900321@S.WHATSAPP.NET` is storable), `""` for a value with no `@`, membership rather
      than suffix (`447700900789@example.com` NOT storable, `123@lid.example.com` NOT storable), the
      classification ORDER (`""` and `None` file as `Ø`, not `D`), the two predicates INDEPENDENT in both
      directions (`notaphone@s.whatsapp.net` carries a JID domain and is `D`; `447700900654@lid.example`
      parses and is not storable), the container refusal, and `classify_field` over both stored shapes with
      `[]`/`""`/`None`/whitespace all yielding `[]`. Derive every oracle by CALLING the predicates.
      verify: test_whatsapp_storable_predicate_and_classifier

- [x] **Task 3 — The model: `List[str]`, the tolerant read, the derived accessor.** Edit
      `obsidian_schemas/models.py:Person` per `## Design` §2 — `whatsapp: List[str] = Field(default_factory=list)`,
      the `mode="before"` validator, the `whatsapp_jids` property, and the `identifier` import. Add the AC-4
      check `test_whatsapp_read_write_shape_and_no_silent_drop` to
      `tests/test_whatsapp_jid_storage.py`, covering all four legs over every cell: the TOLERANT READ
      including the BARE valueless `whatsapp:` key (importing any skip reason from
      `obsidian_schemas/repositories/base.py` and never typing the literal — the legal homes are pinned to
      exactly two files by EQUALITY at `tests/test_fixture_vault.py:1392-1395`), NO SILENT DROP (the raw
      string present on the model for classes C, D, E; the typed view filtered on PARSEABILITY so C and E
      appear and D does not), ONE WRITTEN SHAPE (asserted both ways over a planted class-D note: an
      unrelated delta write leaves its scalar bytes untouched; a write re-introducing the field is refused
      with the bytes unchanged; no `!!python/object` tag anywhere in the written bytes), and ROUND TRIP as a
      fixed point. Leg (a)'s class-Ø round trip goes THROUGH a gated delta write and back, so the read side
      and the write side meet.
      verify: test_whatsapp_read_write_shape_and_no_silent_drop

- [x] **Task 4 — The gate arm, the refusal attribute, and the two helpers.** Add `WHATSAPP_PATTERN`,
      `WHATSAPP_KEY`, `_member_at`, `_as_stored_list`, the `refused_value` keyword on `_refuse`, and the
      arm between step 3 and step 4 of `gate_write`, all per `## Design` §3. Add
      `tests/test_whatsapp_write_door.py` with `test_whatsapp_refused_at_every_write_arm_reported_by_lint_vault_and_disclosed_append_only`
      — AC-3's check, named for all three surfaces it asserts. The arm set is DERIVED by
      `frontmatter_write_arms` from `tests/derivations.py` and asserted in scope by EQUALITY, plus
      `PersonRepository.save` and `write_markdown_file(entity=…)` named explicitly as the two
      whole-record-projection arms the derivation excludes by design. Per arm, both shapes (a bare scalar and
      a list with one bad member among good ones) and three conjuncts (refused with the distinct
      gate-local `pattern` and the raw value on `.refused_value` and NOT in the message; the target note
      byte-identical and an absent target not created; a storable value in the same payload accepted and
      stored in the list shape). `"+44 7739 341679"` is a required class-C member at every arm and
      `447700900654@lid.example` a required class-E member. Plus the CLEARING leg at every delta arm in both
      of the package's spellings, the CLASS-Ø leg at every arm in every spelling, and the near-miss control
      that a stored-dirty note stays writable for a write that does not re-introduce the field.
      verify: test_whatsapp_refused_at_every_write_arm_reported_by_lint_vault_and_disclosed_append_only

- [x] **Task 5 — The corpus edits and the digest.** Apply `## Design` §9 lines 1–4: Thrandell's note takes
      `whatsapp: "15555550142@lid"`, `@Fennwick Drostane.md` takes `whatsapp: "447700900789@example.com"`,
      `tests/fixture_vault.py:225` declares `["15555550142@lid"]`, Fennwick's `NoteSpec` gains
      `whatsapp=["447700900789@example.com"]`, `_person`'s default (`:94`) becomes `[]`, and `CORPUS_DIGEST`
      (`:44`) is regenerated by the one-line command in that module's docstring. `docs/vault-shape-census.md`
      and `tests/test_fixture_vault.py` are NOT edited. Verify by running the three standing corpus checks —
      the freeze/byte-copy check, the write-door round trip, and the declared-values parse — all of which
      go red on a half-done edit and green on a complete one.
      verify: test_fixture_vault_is_frozen_and_materialized_by_byte_copy test_corpus_note_round_trips_through_the_write_door test_corpus_person_note_parses_to_its_declared_values

- [x] **Task 6 — One phone-pivot rule, derived from the projection, with its exact inverse.** Apply
      `## Design` §5(a), (b) and (c) to `obsidian_schemas/repositories/person.py`: `_index_entity` projects
      ONCE and pivots only on a non-empty `phone_digits`, `_index_identifiers` takes the optional
      `identifiers`, `_remove_entity_from_indexes` derives its removal from the same projection as a lookup
      (not a loop), and `_project_identifiers` ITERATES the list. Add the AC-1 check
      `test_lid_digits_never_enter_the_phone_index` to `tests/test_whatsapp_jid_storage.py`: the six-cell
      table classified BY CALLING the predicates, each cell asserted non-empty, the classification ORDER
      asserted, the classifier asserted TOTAL with no fall-through over the table plus every corpus
      `whatsapp` value plus the named boundary-probe list, classes A and C keyed on exactly `phone_digits`
      with `get_by_phone` returning that person, classes B and E with NO phone key and
      `get_by_phone("5555550142")` returning None, class D and class Ø on the narrowing arm with class Ø
      additionally projecting NO identifier of any kind, the two predicates independent both ways, the WHERE
      clause's three receiver constraints asserted as PROPERTIES of the manifest and not only as a filename,
      the representative asserted storable-clean, and `_remove_entity_from_indexes` asserted the exact
      inverse over the same table.
      verify: test_lid_digits_never_enter_the_phone_index

- [x] **Task 7 — The public resolution door and the cascade step.** Apply `## Design` §5(d) and (e):
      `get_by_identifier`, the `whatsapp-jid` step in `resolve_all` below the blank-query bail-out, and the
      label inserted into `_RESOLVE_CASCADE_ORDER` immediately before `phone`. `_IDENTIFIER_PRIORITY` is NOT
      touched. Add the AC-2 check `test_whatsapp_jid_resolution_door_over_every_accepted_form` to
      `tests/test_whatsapp_jid_storage.py`: over the same derived table, both doors answering, expected
      entity computed from `WhatsAppJID.parse(v).key` plus the fixture's note-to-value map; classes A and C
      through the `phone:` key with class C asserted RESOLVABLE though AC-3 refuses to store it; classes B
      and E through the `jid:` key with E named alongside B; classes D and Ø on the narrowing arm, Ø stated
      as a POSITION pin — the blank-query bail-out still precedes every cascade step including the new one;
      and the three guards (the lid answer asserted to come from the identifier index and not from a phone
      lookup, the new label asserted PRESENT and ranked ahead of `phone` proven by a tie resolving to the
      lid's owner, and `README.md:238`'s documented `get_by_phone` route still holding).
      verify: test_whatsapp_jid_resolution_door_over_every_accepted_form

- [x] **Task 8 — The `save` rider and the two APPEND-ONLY disclosures.** Add
      `entity.whatsapp = gated["whatsapp"]` to `PersonRepository.save`'s rider and write the write-back and
      refusal disclosures as NEW PARAGRAPHS in its docstring, leaving all 29 Cut-0 `(owner, text)` pairs
      byte-identical (`## Design` §6). Extend AC-3's check module with the `save` arm pinned in BOTH
      directions over an entity loaded from a class-C/D/E note — refuses with the same pattern and the note
      byte-identical, AND the value still present on the model and in the note afterwards — plus the
      APPEND-ONLY clause's three conjuncts, conjuncts (1) and (3) computed through `prose_lines` (so the
      module names no `ast` of its own): every Cut-0 pair owned by `PersonRepository.save` still present;
      and at least one line for that owner that is NOT a Cut-0 member, i.e. the disclosure LANDED.
      **Conjunct (2) is built to `## Design` §6's COMPUTABLE FORM and not to its frozen wording, which names
      a pre-build byte comparison no post-build hermetic check has a referent for:** import `_golden` and
      `AUTHORIZED_PROSE_OWNERS` from `tests/test_identity_endgame.py` (the same reader and the same tuple
      WI-024's own clause (e1) uses at `:996` and `:1003`; the cross-test-module import idiom already exists
      at `tests/test_name_gate_delta_rule.py:54-55`), then assert BOTH legs — the number of entries in
      `_golden("prose_surface_cut0.json")["lines"]` whose `owner` is `PersonRepository.save` is exactly 29,
      counted as a LIST LENGTH and never as the size of an `(owner, text)` set, and
      `AUTHORIZED_PROSE_OWNERS` equals its thirteen declared members with neither `PersonRepository.save`
      nor the bare class among them. Both values are READ at test time; 29 is a frozen-population equality
      pin and §6 states why that is licensed here. Leg 1 reddens the AUTHORIZATION (rejected item 15) and
      leg 2 reddens a GOLDEN EDIT, which is the one move that would let conjunct (1) be neutered rather than
      satisfied — neither is visible to (e1), (e2) or conjunct (1), all three of which read that tuple and
      that golden.
      verify: test_whatsapp_refused_at_every_write_arm_reported_by_lint_vault_and_disclosed_append_only

- [x] **Task 9 — The report-only detector arm.** Add `WHATSAPP_CHECK` and the arm to
      `scripts/lint_vault.py:check_structural` per `## Design` §4. Add
      `test_whatsapp_not_storable_detector_reports_and_never_repairs` to `tests/test_whatsapp_write_door.py`
      with AC-3's REPORT LEG's five conjuncts: it FIRES on C, D and E — over a materialized copy of the
      corpus its issue set is EXACTLY the one non-representative note carrying `447700900789@example.com`,
      and over temp-vault plants it fires on a class-D value and on `447700900654@lid.example`; it is SILENT
      on class Ø in every spelling and on every storable value, so the representative's `15555550142@lid`
      and the corpus's 21 `whatsapp: ""` notes produce no issue of this check; it judges BOTH stored shapes;
      `auto_fixable is False` asserted PER ISSUE and this check asserted NOT a member of
      `auto_fixable_emitter_checks`; and the report NEVER travels as `NOT_RENAMEABLE_MARKER`, asserted by
      the divergence module's own marked-set equality staying green and untouched. Add a nested-container
      plant so the `except IdentifierError` arm is exercised rather than assumed.
      verify: test_whatsapp_not_storable_detector_reports_and_never_repairs

- [x] **Task 10 — The migration: plan, apply, readback, CLI.** Write
      `scripts/migrate_whatsapp_to_list.py` per `## Design` §7 — the four entry points, the seven-arm action
      table keyed on `classify_field`, the `phone_digits` guard on the repair, the single
      `update_frontmatter_field` write, the fresh-repository readback, and the triple reconciliation with a
      non-zero exit naming the part that disagreed. Add `tests/test_whatsapp_migration.py` with the AC-5
      check `test_whatsapp_migration_dry_run_then_write_then_readback`: driven against a materialized COPY
      planted with one note per non-Ø cell plus the two-JID note pinned to `447700900987@s.whatsapp.net` and
      `15555550163@lid`; five legs — the dry run byte-identical by a digest over the tree before and after;
      the write asserted STRUCTURALLY through `vault_io` and the gate with no direct `write_text`; the
      readback oracle over `.key` multisets computed from the note BYTES by a load that did not exist before
      the write, ranging over the PARSEABLE values only with the split computed by CALLING `parse` and
      catching `IdentifierError`, plus the two per-note counts (parseable values, and TOTAL values including
      unparseable ones); the class-C repair counted separately and asserted key-preserving and
      phone-bearing-guarded, with a planted class-E note asserted byte-identical after a repair-ENABLED run;
      and the counts reconciling part-for-part over the three-part partition, with the never-clears conjunct
      asserted per plant and the residual's repair path EXERCISED — a class-D note cleared and a class-E
      note rewritten through a delta arm, both succeeding. Assert BOTH arms of Ruling B: with repair
      enabled R is the class-D and class-E plants; with `--no-repair` R is those plus the class-C note,
      byte-identical.
      **And the RE-RUN leg, per `## Design` §7 — the property `## Edge Cases`' retry remedy rests on and the
      one nothing in the plan asserted:** the same check drives a SECOND pass over the already-migrated copy —
      `plan_migration` again, then `apply_migration` with that FRESH plan, never the first pass's stale one —
      and asserts three things about it: ZERO calls to
      `writer.update_frontmatter_field`, counted by a wrapper installed with `tests/support.py`'s `patcher`
      for the duration of the pass and asserted zero (the discriminator, because a digest cannot tell "no
      write" from "re-write the same bytes" and the two-JID plant is list-shaped from the start so it
      discriminates only "does not abort on a list"); the tree digest byte-identical across the pass, the same
      digest leg (a) takes (which additionally catches a re-write that REFORMATS); and the triple UNCHANGED
      part-for-part from the first pass's — not zeroed, since an already-list-shaped note is MIGRATED by the
      action table — with the count of notes the write COMMITS and the repair count both zero. Two spellings are
      prescribed rather than free: the migration imports the writer MODULE (`from obsidian_schemas import
      writer`, the call resolved at call time) and never the bare function, or the counter is blind; and BOTH
      `apply_migration(...)` call sites pass the identifier `vault` bound from the one `_temp_vault` door, or
      Task 11's SPELLING clause collects the second one and raises.
      **And the M1 RIDER — the repair disclosure, per `## Design` §10(a):** `plan_migration` carries a
      `RepairDisclosure(path, stored_value, proposed_jid, corroborated)` record per class-C note on
      `plan.repairs`, with the three header/banner literals as module constants the check IMPORTS, and with
      `corroborated` computed by calling `phones_match(WhatsAppJID.parse(v).phone_digits, normalize_phone(p))`
      over each non-blank `p` in that note's OWN raw `phones[]`; `format_repair_disclosure(plan)` RETURNS (never
      prints) one line per record carrying the note path, the stored value and the proposed JID, each field
      ESCAPED through `_escape_for_one_line` per the M4 rider below, with
      the UNCORROBORATED records first under their own header; and `_cli` prints it on every run BEFORE any
      write, including under `--apply` and under `--no-repair` (where the header states no repair will be
      attempted and those notes join R). Add
      `test_whatsapp_dry_run_discloses_each_class_c_repair_pair` to `tests/test_whatsapp_migration.py`, over a
      temp vault planted with one CORROBORATED class-C note (its digits also in its own `phones[]`), one
      UNCORROBORATED class-C note (digits in no `phones[]` entry, the live census's single such member), and one
      note per other class: the line set is EXACTLY one line per class-C plant with the expected count DERIVED
      by calling `classify_field` over the plants rather than written as a literal; each line's proposed JID is
      computed in the test by CALLING the same repair spelling on the plant's own stored value; the
      uncorroborated plant appears under the uncorroborated header and the corroborated one does not, with both
      expectations computed by calling `phones_match` over the plants' own values and never from a hardcoded
      flag; a class-A plant whose digits are absent from its `phones[]` yields NO line (the population is class C
      only, so the disclosure is not a corroboration report); and the whole disclosure is READ-ONLY, asserted by
      the same tree digest before and after that leg (a) uses. Every plant literal in this module is
      RESERVED-block or synthetic, the same clause Task 13's sibling check carries: this module introduces no
      live identifier, and the census carries none for a builder to reach for (threat-model note 3, round-2
      note 1).
      **And the M4 RIDER — the disclosure's render, per `## Design` §10(d):** add the module-level helper
      `_escape_for_one_line(raw: str) -> str` to `scripts/migrate_whatsapp_to_list.py` and route EVERY field of
      every `RepairDisclosure` through it in `format_repair_disclosure` — `path`, `stored_value` and
      `proposed_jid` alike, so the guarantee is total over the RECORD and survives a later change to the repair
      spelling. The helper escapes the backslash FIRST (so the rendering is unambiguous) and then renders as a
      visible `\xNN`/`\uNNNN` escape every character `str.splitlines()` treats as a line break and every
      character whose `unicodedata.category` is `Cc`, `Cf`, `Zl` or `Zp`; every other character passes through
      unchanged. The implementation is the CATEGORY test ALONE — that set CONTAINS the break set, which leg (1)
      proves rather than assumes — and the rendering is pinned so nothing is a judgment call: `\\` for the
      backslash, then `f"\\x{cp:02x}"` for a codepoint below `0x100` and `f"\\u{cp:04x}"` for the rest.
      Extend `test_whatsapp_dry_run_discloses_each_class_c_repair_pair` — not a new check, because
      this is the property that makes that check's own oracle total — with five legs, each oracle DERIVED and
      never listed. (1) TOTALITY: `BREAK_CODEPOINTS = frozenset(cp for cp in range(0x110000) if len(f"a{chr(cp)}b".splitlines()) > 1)`
      computed ONCE at module level (~1s; compute it once, never replace it with a hand list of characters — the
      hand list is the defect this leg exists to prevent), then for every `cp` in it
      `_escape_for_one_line(f"a{chr(cp)}b").splitlines()` has length 1, and for every `cp` in it plus `0x1b` the
      escaped rendering contains no such raw character. (2) NO-OP ON CLEAN: `_escape_for_one_line(x) == x` for
      every field of every clean plant, so the escape is the identity wherever verbatim is safe and the 82 live
      bare digit runs render exactly as a verbatim render would. (3) THE ADVERSARIAL PLANT: one more class-C
      note, planted through the SAME `_temp_vault` door as every other plant (so §8's PROVENANCE clause is
      unaffected), as a YAML double-quoted scalar carrying the `\n` escape followed by the text of
      `CORROBORATED_HEADER` imported from the module, with the RESERVED-block number `447700900321` and its
      `phones[]` holding no matching digits — asserted before it is used with: the value read back out of the
      note CONTAINS the planted control character, `classify_field` called on it returns exactly `["C"]`, and
      `phones_match` over that note's own `phones[]` returns False so it lands in the UNCORROBORATED section.
      (4) LINE COUNT STILL EQUALS RECORD COUNT: `len(format_repair_disclosure(plan).splitlines())` equals the
      record count plus the number of headers the formatter itself emitted, with BOTH terms derived — the record
      count by calling `classify_field` over the plants, the header term by calling the formatter over the same
      plan with the adversarial plant removed and counting the header lines it produced. (5) NO FORGED HEADER:
      the set of output lines EQUAL to any of the three imported header/banner constants is exactly the set that
      run produced, so a header appearing only because the data spelled one is RED. Then complete the 2×2 of
      class-C sub-cells by planting the fourth cell — a CORROBORATED control-character-bearing note — with its
      corroboration likewise computed by calling `phones_match` and never written beside the plant.
      verify: test_whatsapp_migration_dry_run_then_write_then_readback test_whatsapp_dry_run_discloses_each_class_c_repair_pair

- [x] **Task 11 — The containment wall, made non-vacuous.** Add `"apply_migration": 0` to
      `MUTATING_DRIVE_VAULT_POSITIONS` (`tests/derivations.py:2012`) with the comment `## Design` §8 states,
      and add `test_every_whatsapp_migration_drive_is_confined_to_a_temp_vault` to
      `tests/test_whatsapp_migration.py` — the six clauses §8 enumerates over the module's own source
      (SPELLING, NON-VACUITY, PROVENANCE through the one `_temp_vault` door, SOURCE outside that door, ZERO
      repository constructions, and the IMPORT refusal), plus the two-token `live_path_names` equality with
      `not hasattr(migrate, "DEFAULT_VAULT")` as the proof that the third token's absence is the script's own
      design rather than a gap, plus the runtime door EXERCISED rather than left to whichever drive runs
      first. Also plant the two match-shapes the scan must resolve — an `apply_migration(vault)` call it
      COLLECTS and a call with an unreducible vault expression it must RAISE on — so the wall cannot pass by
      matching nothing.
      verify: test_every_whatsapp_migration_drive_is_confined_to_a_temp_vault

- [x] **Task 12 — Close every wall membership by RUNNING the wall's own predicate.** Add
      `test_whatsapp_wall_membership_is_closed_by_running_each_walls_predicate` to
      `tests/test_whatsapp_migration.py`, driving each wall named in `## Verification`'s inbound census on
      this item's FINAL text — never reasoning about which shapes match. At minimum: `modules_using_ast`
      over `python_files_under(PACKAGE_ROOT, TESTS_ROOT, SCRIPTS_ROOT)` still single-homed to
      `tests/derivations.py`; `skip_reason_literal_sites` over the same universe still exactly its two
      declared homes; `check_module` resolving every top-level `def test_` this item's three new modules
      define, READ from those modules' own source at test time and never from a list in this plan;
      `frontmatter_write_arms` over `python_files_under(PACKAGE_ROOT, SCRIPTS_ROOT)` with every arm the new
      files carry routed and declared and none `absent`; `EDITED_FUNCTION_ARM_COUNTS`'s six per-function
      equalities unchanged; `phone_index_iteration_sites` over the package still all `materialized`;
      `prose_lines`-derived clause (e1) over `person.py` green; and the repo-wide markdown scan's
      `NO_ARG_CONSTRUCTION` predicate run over the ONE `docs/wi-032-*` file this item writes
      (`docs/wi-032-whatsapp-live-baseline.md` — the other two `docs/wi-032-*` artifacts are conductor
      preconditions this build does not author) plus this document. That last run is VOLUNTARY and is declared
      as such so the next reader does not read it as a membership the wall imposes: `docs` is a member of
      `DOC_SCAN_EXCLUDED` (`tests/test_vault_path_required.py:387`, intersected against every path part at
      `:425`), so no file under `docs/**` joins that scan's population at all — the same fact M2 rests on.
      Anything the RUN returns that this spec did not name is NAMED in the Build Log and
      satisfied — never worked around and never satisfied by narrowing the wall.
      verify: test_whatsapp_wall_membership_is_closed_by_running_each_walls_predicate

- [x] **Task 13 — The live bracket's ENTRY half.** Write `docs/wi-032-whatsapp-live-baseline.md` copying
      `docs/stem-divergence-live-baseline.md`'s section shape literally — §0 the measurement command, §1
      entry figures, §2 the direction per class, §3 blast radius read against the linter, §4 the booked hand
      repairs, §5 an EMPTY post-run attestation left for the conductor. §1's figures are the census's six
      rows with class Ø split into its two spellings (absent key 6, `""` 1025) and the derived partition
      figures (`whatsapp`-carrying 1168, MIGRATED 1168, shape-only 1025, repairs 82, `|R|` 0).
      **§3 is built to `## Design` §10(c) — the M3 RIDER:** its ordered list is the TWO LOUD breaks and only
      those two, `orchestrator/src/invariants.py:663-665` (red vault-wide) and
      `HAL9000/backend_fastapi/routers/contacts.py:41,50` (500ing), each with its pinned 40-hex HEAD; the
      raw-file writer at `orchestrator/bin/merge-duplicate-persons.py:380-384` stands OUTSIDE that list in its
      own row headed `DATA-LOSS HOLD`, carrying its pinned HEAD, its reaching callers
      (`bin/apply-vault-review.py:152,158`), the `whatsapp: ""` clearing path
      (`docs/wi-032-consumer-audit.md:202-204`) and the conductor instruction that neither that script nor
      `apply-vault-review.py` is run against the vault post-migration until the other repo fixes it; and a
      one-line pointer to `docs/wi-032-consumer-audit.md:227-239` for items 4–7 of its seven-site list rather
      than a re-listing. §3 also carries the 26-lid sentence `## Approach` now carries.
      **And the M2 RIDER, per `## Design` §10(b):** counts, classes and code paths ONLY — no vault note name, no
      live identifier, and specifically none of Task 10's repair pairs and none of the detector's per-note issue
      lines, both of which are stdout of the conductor's live run. Add
      `test_wi032_live_baseline_row_shape_and_redaction_wall` to `tests/test_whatsapp_migration.py`, reading the
      bracket's FINAL text, with three duties. (i) REDACTION, run over all THREE `docs/wi-032-*` artifacts (this
      bracket and both grounding artifacts) and deliberately NOT over `docs/whatsapp-jid-value-type.md`, which
      `## Design` §9 line 5 and F18 leg 6 keep one real number in on purpose: after stripping every
      `\b[0-9a-f]{40}\b` token, no `\d{9,}` run and no digit-immediately-before-`@`-and-a-domain-label survives —
      with the claimed match-shapes driven through that same predicate as fixtures and every literal
      RESERVED-block or synthetic (threat-model note 3: this module introduces no live identifier),
      `"15555550142"`, `"123456789012@s.whatsapp.net"` and `"15555550142@lid"` asserted to MATCH and
      `27cb78cc5a2099972dccea984664193e69414def` (the real pinned HEAD at `docs/wi-032-consumer-audit.md:92`,
      which carries the nine-digit run `984664193`), `1168`, `1025`, `82`, `663-665`, `2026-09-27` and a bare
      `@s.whatsapp.net` asserted NOT to. (ii) FIGURES: §1's six rows and five derived partition figures equal values DERIVED by
      parsing the census's own verbatim stdout block (`docs/wi-032-whatsapp-corpus-census.md`, its `(a)`, `(c)`
      and `(c')` lines) — never literals re-typed from this plan — so the bracket is proven to AGREE with the
      artifact it copies from; the check does not re-measure the live vault and no hermetic check can, and its
      coupling is declared in one line in the check itself: it pins that artifact's machine-output block and
      consumes the property that those three lines are its census script's stdout. (iii) SHAPE: `DATA-LOSS HOLD`
      is present, `merge-duplicate-persons.py:380-384` appears inside that row and NOT inside §3's ordered list,
      and that list has exactly two items naming the invariant and the endpoint. The check asserts the §5 HEADING
      exists and asserts NOTHING about §5's content — the conductor writes the exit figures there after the
      build, and a check pinning §5 empty would redden the floor at close-out.
      verify: test_wi032_live_baseline_row_shape_and_redaction_wall

- [x] **Task 14 — Floor green, directionally.** Run the floor command from the worktree root and confirm
      exit 0 with a case count at or above Task 1's Build Log baseline plus this item's new cases. Record
      both numbers and the delta in the Build Log. A count BELOW the baseline with no explanation means a
      test file was silently lost, not that a test was tidied.
      verify: hand-run — the floor command is run from the worktree root and its case count compared against Task 1's recorded baseline; the invariant is directional, not a pinned number

## Build Log — 2026-09-27 (build-runner, resumed after a spawn timeout)

**The resume, stated first because it decides what this log is evidence OF.** A prior build-runner spawn
timed out mid-build. It left the worktree carrying the code and tests for Tasks 2–9 and the migration
script of Task 10, and it left NO `## Build Log` and NO ticked checkbox — so the resume cursor had to be
read off the tree rather than off the document. This spawn therefore did two different things and they are
kept apart below: it VERIFIED the retained work by running it (never by reading it), and it BUILT what was
missing — Task 10's test module, Tasks 11–13's checks, Task 13's bracket document, and Tasks 1 and 14's
figures.

### The floor, both ends (Tasks 1 and 14)

| figure | value | how |
|---|---|---|
| Task 1 — pre-build baseline | **699 passed** | the floor command run against a `git archive HEAD` export of `c7d074f` in a temp tree, because the worktree was ALREADY edited when this spawn started and a baseline read off it would have been the post-edit number wearing the pre-edit name |
| the retained work alone (Tasks 2–9 + the script) | 711 passed | the floor command in the worktree, before this spawn's first edit |
| Task 14 — final | **716 passed**, exit 0 | the floor command from the worktree root |
| delta | **+17** | directional and above the baseline, which is the invariant |

699 matches CLAUDE.md's own last hand-verified anchor (`699 (2026-09-26 post-WI-029)`), which is a
corroboration of the archive-export method rather than a coincidence worth passing over.

### What the retained work needed, and what it did not

Tasks 2–9's code and tests were re-verified by RUNNING them, not by reading them: the floor at 711, then
each of the five frozen `criteria` checks individually under the conveyor's OWN foreign interpreter
(`tests/test_ac_interpreter.py:run_foreign`), which is the invocation shape that has bounced batteries
before. All five PASS. Nothing in Tasks 2–9 was re-edited, and the `## Design` blocks they implement were
compared against the tree rather than assumed.

### Deviations, surprises and things the RUN returned that the spec did not name

1. **Task 13's own FIGURES leg caught a defect in its first implementation, which is the leg working.** The
   census artifact carries its census SCRIPT above its stdout, so every `(a)`, `(c)` and `(c')` marker
   appears TWICE — once as an f-string in the source, once as the line it printed. A bare
   `re.search(r"\(c'\) splits: \{([^}]*)\}", census)` reads the SOURCE (`{dict(sorted(sub.items()))}`) and
   not the output. The fix isolates the verbatim stdout block FIRST and parses inside it, with a per-cell
   presence assertion so a parse that misses a cell is RED rather than deriving a figure from a partial
   read. Recorded because the wrong version was GREEN on the `(a)` marker by luck — `{person_notes}` is not
   `(\d+)` — and would have gone green the day someone changed the script's print.
2. **Task 5's three `verify:` names RESOLVE but cannot be RUN under the conveyor's foreign interpreter, and
   that is a property of two pre-existing modules rather than of this build.**
   `test_corpus_note_round_trips_through_the_write_door` lives in `tests/test_writer.py` and
   `test_corpus_person_note_parses_to_its_declared_values` in `tests/test_parser.py`; both modules
   `import pytest` at module scope, so `run_foreign` fails at the import before reaching the check. All
   three names resolve UNIQUELY through `check_module`, and all three are GREEN on the floor (run
   individually to confirm, not inferred from the aggregate). Satisfied, not worked around: `## Scope
   Boundary` lists both modules as walls this item JOINS and never edits, and adding a `tests/support.py`
   bridge to them would be an out-of-scope edit to another item's file to buy a green this item does not
   need. `test_fixture_vault_is_frozen_and_materialized_by_byte_copy`, the third name, DOES run foreign and
   passes.
3. **Task 12's run returned nothing the spec did not name.** All eight predicates green over the FINAL
   tree: the `ast` capability still single-homed to `tests/derivations.py` with three new test modules and a
   new script in the universe; `skip_reason_literal_sites` still exactly its two declared homes;
   `check_module` resolving every top-level `def test_` the three new modules define, read from their own
   source; `frontmatter_write_arms` + `gate_call_declarations` with `absent == set()` and the migration
   contributing ZERO arms; `EDITED_FUNCTION_ARM_COUNTS`'s six equalities unchanged;
   `phone_index_iteration_sites` all `materialized` (which is what `## Design` §5(b)'s lookup-not-loop
   instruction buys); clause (e1) over `person.py` green for every unauthorized owner, not only the `save`
   half AC-3 asserts; and the VOLUNTARY `NO_ARG_CONSTRUCTION` run over the bracket and this document, clean.
4. **The class-Ø `1031`-versus-`1025` distinction is REAL in the fixture corpus too, at 21 versus 20, and
   that was measured rather than assumed.** `@Ferrigan Ostrakine.md` is the corpus's ONE absent-key note, so
   the materialized corpus reports `class Ø: 21` while the run commits only 20 shape-only writes. The
   architect's round-9 note 2 is therefore load-bearing at fixture scale as well as at live scale, and the
   un-stubbed run below prints both numbers, which is what makes the distinction checkable rather than
   asserted.
5. **`CLAUDE.md` asserts two facts this build falsifies and this build does NOT write it.** The `Key Files`
   row for `repositories/person.py` no longer describes everything that module owns (the derived phone
   pivot, `get_by_identifier`, the `whatsapp-jid` cascade step), and the test-count archaeology anchors gain
   a `716 (2026-09-27 post-WI-032)` row. The project root is outside `write_authority` by declaration
   (`pipeline-runners.yaml`) and `## Design` Prerequisite 5 names `README.md`/`CLAUDE.md` as conductor-owned
   session-end `/wrap-up` work. NAMED here rather than escalated as out-of-authority, deliberately: an
   `out-of-authority` fence PAUSES the drive for an authorization, and nothing here is BLOCKED — the spec
   already decided the ownership. `README.md`'s two touchpoints are likewise unchanged and unbroken
   (Prerequisite 5 ran the reasoning; AC-2's third guard asserts the BEHAVIOUR instead).

### The un-stubbed end-to-end run (WI-050), and why it is a TEMP vault

`## Design` §8 states that `_cli` cannot be driven from the graded module — its argv path constructs a vault
path the containment census cannot reduce to a door-bound name, and the IMPORT clause forbids driving it as
a child process — so the CLI is verified OUTSIDE the hermetic suite. Prerequisite 8 is why that verification
is against a TEMP vault here and not the live one: a caged builder's vault writes are reverted at the merge
boundary, so a plan-task live run would change nothing and report success. Run against a materialized corpus
planted with one note per cell plus the two-JID note:

| act | exit | tree digest |
|---|---|---|
| `--vault` OMITTED | **2**, `argparse` refusing a required argument | untouched — it never reaches a filesystem |
| `--vault <a directory that does not exist>` | **2** | untouched |
| dry run | 0 | **UNCHANGED** — leg (a)'s whole point, observed at the CLI and not only in-process |
| `--apply` | 0 | changed; `committed: 23 (shape-only 20, repairs 1)`; plan, write and readback triples all `{scalar_outside_residual: 0, migrated: 24, residual: 2}`; "reconciled part-for-part" |
| `--apply` AGAIN | 0 | **UNCHANGED**; `committed: 0 (shape-only 0, repairs 0)`; the triple UNCHANGED rather than zeroed |

Two further observations from that run, both of which are the design working rather than decoration. The
re-run's per-cell counts move `A: 2 → 3` and `C: 1 → 0`, which is the class-C repair having landed and is
visible nowhere else. And `scripts/lint_vault.py --report` over the post-migration vault emits exactly TWO
`whatsapp_not_storable` issues against the run's own reported `residual: 2` — two counts taken by two
different tools, agreeing. That is the independent-second-witness mechanism `## Approach` step (4) and
AC-3's REPORT LEG exist to buy, exercised for real rather than described.

### Mutate-and-observe, on the three legs whose green could have been vacuous

WI-235's fixture rule is satisfied in the code (the containment scan's collected and unreducible shapes, the
redaction predicate's MUST/MUST-NOT lists, and M4's adversarial plant are all driven through the walls' own
predicates on every floor run). These three probes are the complementary half, run by hand and reverting
nothing because none of them edits the tree:

- **The re-run's CALL COUNTER is wired, not blind.** Installed around a pass that DOES write, it observed
  **23** calls against a reported `committed: 23`. Had the migration bound the writer function into its own
  namespace, the counter would have observed zero and the re-run leg would have been green for the wrong
  reason — which is exactly why `## Design` §7 prescribes the module import and the call-time attribute
  lookup.
- **The readback oracle SEES a dropped second JID.** Truncating the two-JID note's list to one member made
  the key multiset differ for that note and **only** that note, and the total-value count differ likewise.
  The oracle discriminates the failure it exists for and does not smear it across the corpus.
- **The never-clears conjunct SEES an erase.** Clearing the class-D plant's field drives
  `classify_field` to `[]`, which is the assertion's failing side.

### Two implementation notes a future reader needs

- **The pre-migration half of AC-5 leg (c)'s oracle is computed in the CHECK and the post-migration half
  comes out of `readback_migration`.** That asymmetry is the criterion, not an inconsistency: the BEFORE side
  cannot come from the module (the module has not run yet) and the AFTER side must not come from the check's
  own walk (the whole point is a re-READ through a load that did not exist before the write). Both sides
  compute the parseable/unparseable split by CALLING `parse` and catching, so a class-D plant contributes no
  key to either side instead of making the oracle raise on its own mandated fixture.
- **`tests/test_whatsapp_migration.py` constructs NO repository, and that is load-bearing rather than
  stylistic.** The containment wall's LIBRARY clause is zero constructions, because the library's own
  environment fallback runs inside every repository constructor — so a construction reaches the live vault
  without the module spelling any token. `readback_migration` constructing its repository INTERNALLY is what
  makes the clause satisfiable at all, which is why `## Design` §7 puts it there and not in the test.

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

**THE SPEC-WRITER'S EXTENSION (2026-09-27) — fifteen builder write targets, one per path the caged build
touches, and nothing else.** The two `kind: precondition` fences above are kept VERBATIM and are not builder
write targets. Three paths a reader will look for and NOT find, each for a stated reason: `README.md` and
every other project-root file is OUTSIDE this project's `write_authority` (`pipeline-runners.yaml:32-33`) and
is conductor-owned session-end work — nothing in the build depends on it (`## Design`, Prerequisite 5);
`docs/vault-shape-census.md` is another item's digest-frozen artifact and is not touched at all
(`## Design` §9 line 4); and `tests/test_fixture_vault.py` is a wall this item JOINS and never edits — no
privacy exemption added, no pattern widened, no expected set padded.

**One clause of the census fence above is CORRECTED downstream rather than edited in place, and the pointer
belongs here so a reader following the fence does not compute the wrong number** (architect round-9 note 2).
That fence asks for the class-Ø row and says of it "which is also the count of notes the migration converts
SHAPE-ONLY". It is not: class Ø has two live spellings and only the key-PRESENT one is a write. The fence is
left VERBATIM because it is a historical INSTRUCTION that was already carried out — and carried out
correctly, since `docs/wi-032-whatsapp-corpus-census.md:172` and `:184` report the split the clause did not
ask for (absent key **6**, `""` **1025**, YAML null **0**, class Ø **1031**). So the shape-only conversion
count is **1025**, the `whatsapp`-carrying population the TERMINAL-STATE PARTITION ranges over is **1168**,
and the 6 absent-key notes need no write and sit outside the partition's domain. `## Approach` step (4) states
this where the numbers are USED, which is the only place a conductor reads them.

```writes
path: obsidian_schemas/identifier.py
why: Task 2 — STORABLE_DOMAINS, CLASS_ABSENT, CLASSES, jid_domain, is_storable, classify, classify_field on WhatsAppJID. `parse` unchanged.
```

```writes
path: obsidian_schemas/models.py
why: Task 3 — `whatsapp: List[str]`, the tolerant `mode="before"` validator, the derived `whatsapp_jids` property, the identifier import.
```

```writes
path: obsidian_schemas/name_gate.py
why: Task 4 — WHATSAPP_PATTERN, WHATSAPP_KEY, `_member_at`, `_as_stored_list`, `_refuse`'s `refused_value` keyword, and the arm between steps 3 and 4.
```

```writes
path: obsidian_schemas/repositories/person.py
why: Tasks 6, 7, 8 — the derived phone pivot and its inverse, the iterating projection, `get_by_identifier`, the cascade step and label, the `save` rider plus its two APPEND-ONLY docstring paragraphs.
```

```writes
path: scripts/lint_vault.py
why: Task 9 — WHATSAPP_CHECK and one report-only detector arm in `check_structural`. No auto-fix rule, no change to `apply_fixes`, `_gate_refusal_pattern` untouched.
```

```writes
path: scripts/migrate_whatsapp_to_list.py
why: Task 10 — NEW. plan_migration / apply_migration / readback_migration / _cli, the action table, the repair guard, the single `update_frontmatter_field` write, the triple reconciliation, plus M1's `RepairDisclosure` record and read-only `format_repair_disclosure` (`## Design` §10(a)) and M4's `_escape_for_one_line` helper that every rendered field of that disclosure passes through (`## Design` §10(d)).
```

```writes
path: tests/derivations.py
why: Task 11 — one member added to MUTATING_DRIVE_VAULT_POSITIONS (`apply_migration`) plus its comment, so the containment wall is not vacuous over the new module.
```

```writes
path: tests/fixture_vault.py
why: Task 5 — `_person`'s whatsapp default becomes `[]`, Thrandell's override becomes the class-B LIST, Fennwick's NoteSpec gains the class-C LIST, CORPUS_DIGEST regenerated.
```

```writes
path: tests/fixtures/vault/@Thrandell Ibberly.md
why: Task 5 — the person round-trip representative's `whatsapp` becomes the storable `15555550142@lid`, so a correct build does not redden two standing round-trip tests.
```

```writes
path: tests/fixtures/vault/@Fennwick Drostane.md
why: Task 5 — receives the class-C value `447700900789@example.com`; the one corpus note satisfying all three of AC-1's receiver constraints.
```

```writes
path: tests/test_identifier.py
why: Task 2 — the WhatsAppJID block gains the storable predicate and the classifier beside its existing parse pins.
```

```writes
path: tests/test_whatsapp_jid_storage.py
why: Tasks 2, 3, 6, 7 — NEW. The predicate/classifier battery plus AC-1, AC-2 and AC-4's checks.
```

```writes
path: tests/test_whatsapp_write_door.py
why: Tasks 4, 8, 9 — NEW. AC-3's check across all three surfaces, plus the detector's own check.
```

```writes
path: tests/test_whatsapp_migration.py
why: Tasks 10, 11, 12, 13 — NEW. AC-5's check, the containment wall over its own source, the wall-membership closure, plus the two mitigation checks (M1-and-M4's repair-disclosure check, which carries M4's derived `BREAK_CODEPOINTS` set and its adversarial control-character plant, and M2/M3's bracket redaction-and-shape wall).
```

```writes
path: docs/wi-032-whatsapp-live-baseline.md
why: Task 13 — the live bracket's ENTRY half, §5 left empty for the conductor's post-run exit numbers, §3 built to `## Design` §10(c) (two loud breaks listed, the raw-file writer in its own DATA-LOSS HOLD row) and to §10(b) (counts, classes and code paths only, walled by Task 13's own check). A DELIVERABLE of the ship condition, not evidence any criterion's premise rests on.
```

## Mitigation Folds — 2026-09-27

The FOUR `kind: required` mitigations of `## Threat Model — 2026-09-27 (round 2)` — the LATEST SPEAKING
round, which re-emits round 1's M1, M2 and M3 with their `desc` byte-identical and adds M4 — each folded into
`## Design` AND the Implementation-Plan task its fence names, in the SAME edit as
this record. Every `desc` below is copied verbatim from that round's `mitigation` fence. The four share one
generator and are closed as one class in one Design subsection (§10) rather than as sentences scattered
across §7 and Task 13: the generator is that the item's irreversible half is authorized by a human reading two
artifacts — the migration's stdout and `docs/wi-032-whatsapp-live-baseline.md` — whose CONTENT no section
specified, so both defaulted to per-cell counts.

Sweeping that ladder gave the same answer twice, at two levels, which is why this section is one class and not
four instances. At the SURFACE level, the surfaces a human reads at a go/no-go are exactly three: the dry run's
stdout (M1, now specified and asserted), the tracked bracket document (M2 and M3, now specified and walled),
and the `lint_vault` detector's output, which §10(b) declares to be a COUNT in the bracket and per-note LINES
on stdout — the same partition, stated rather than left to the reader. No fourth such surface exists in this
design: `_refuse` carries its value as an attribute and reaches no message or traceback (threat model,
Information disclosure), and the two grounding artifacts are already in HEAD as counts-and-code-paths. At the
RENDER level — the next level down, which round 2 found because M1 itself created it — the question is not
which surface carries what but HOW the one surface that renders a note-derived value renders it: M4 closes that
with ONE escape helper applied to EVERY field of the record (not to the one field the finding named), stated as
a rule over the whole class of characters that can break a line or hide in one (derived by calling
`str.splitlines()` over the codepoint space, never a hand list of four), and §10(d)'s own sweep then enumerates
the dimensions, intersections and class-C sub-cells and DECLARES what it found — six further render surfaces,
five closed by construction and the sixth (`lint_vault`'s pre-existing per-issue `vf.path`) deliberately
declined rather than silently missed, an empty intersection, and a 2×2 of sub-cells all four planted.

No `## Write Targets` path was added or removed by this fold, so the item's touch surface and review level are
unchanged, and no signed span (`## Intent`, `## Acceptance Criteria`) was touched.

```fold
id: M1
desc: The DRY RUN must print the class-C repair as per-note (stored value -> proposed JID) pairs and flag every member whose digits are not already in its own `phones[]`, so the 82 irreversible re-spellings are authorized with the rewrites VISIBLE rather than off aggregate per-cell counts — AC-5 leg (d)'s key-preservation is true by construction of the repair spelling (both keys derive from the same `normalize_phone` output, `phone_normalization.py:52`) and so is not evidence the digits are the right number, and the census itself singles out the one uncorroborated member as "the one row worth eyeballing in the dry run" (`docs/wi-032-whatsapp-corpus-census.md:207-208`) while nothing in the design can show it.
design: `plan_migration` carries, per class-C note, a `RepairDisclosure(path, stored_value, proposed_jid, corroborated)` record whose `corroborated` is computed by `phones_match` over that note's OWN raw `phones[]`, and `format_repair_disclosure(plan)` returns one line per record with the UNCORROBORATED records FIRST under their own header, which `_cli` prints on every run BEFORE any write — so the 82 irreversible re-spellings are authorized with every stored-value → proposed-JID pair VISIBLE and the census's one uncorroborated member unmissable, never off aggregate per-cell counts.
landed: Task 10
work: The M1 RIDER, per `## Design` §10(a): `plan_migration` carries a `RepairDisclosure(path, stored_value, proposed_jid, corroborated)` record per class-C note on `plan.repairs`, with the three header/banner literals as module constants the check IMPORTS, and with `corroborated` computed by calling `phones_match(WhatsAppJID.parse(v).phone_digits, normalize_phone(p))` over each non-blank `p` in that note's OWN raw `phones[]`; `format_repair_disclosure(plan)` RETURNS (never prints) one line per record carrying the note path, the stored value and the proposed JID, each field ESCAPED through `_escape_for_one_line` per the M4 rider below, with the UNCORROBORATED records first under their own header; and `_cli` prints it on every run BEFORE any write, including under `--apply` and under `--no-repair` (where the header states no repair will be attempted and those notes join R). Add `test_whatsapp_dry_run_discloses_each_class_c_repair_pair` to `tests/test_whatsapp_migration.py`, over a temp vault planted with one CORROBORATED class-C note (its digits also in its own `phones[]`), one UNCORROBORATED class-C note (digits in no `phones[]` entry, the live census's single such member), and one note per other class: the line set is EXACTLY one line per class-C plant with the expected count DERIVED by calling `classify_field` over the plants rather than written as a literal; each line's proposed JID is computed in the test by CALLING the same repair spelling on the plant's own stored value; the uncorroborated plant appears under the uncorroborated header and the corroborated one does not, with both expectations computed by calling `phones_match` over the plants' own values and never from a hardcoded flag; a class-A plant whose digits are absent from its `phones[]` yields NO line (the population is class C only, so the disclosure is not a corroboration report); and the whole disclosure is READ-ONLY, asserted by the same tree digest before and after that leg (a) uses. Every plant literal in this module is RESERVED-block or synthetic, the same clause Task 13's sibling check carries: this module introduces no live identifier, and the census carries none for a builder to reach for (threat-model note 3, round-2 note 1). verify: test_whatsapp_migration_dry_run_then_write_then_readback test_whatsapp_dry_run_discloses_each_class_c_repair_pair
```

```fold
id: M2
desc: The M1 pairs and the detector's per-note issue lines stay on stdout for the go/no-go and are NEVER written into `docs/wi-032-whatsapp-live-baseline.md` or any other tracked document, which carries counts, classes and code paths only — `docs` is a member of `DOC_SCAN_EXCLUDED` (`tests/test_vault_path_required.py:387`, intersected at `:425`) so `docs/**` is outside the markdown scan's domain and nothing mechanical catches a pasted live identifier.
design: The repair pairs and the detector's per-note issue lines are STDOUT of the conductor's live run and are NEVER written into `docs/wi-032-whatsapp-live-baseline.md` or any other tracked document — which carries counts, classes and code paths only — and because `docs/**` is outside the repo-wide markdown scan's domain (`DOC_SCAN_EXCLUDED = {".git", ".venv", "docs", "state", "node_modules"}`, `tests/test_vault_path_required.py:387`, intersected against every path part at `:425`) nothing standing would catch a pasted live identifier, so this item ships that wall itself: a check over the bracket file's FINAL text asserting that no JID-shaped token and no run of nine or more digits survives outside a 40-hex commit token.
landed: Task 13
work: The M2 RIDER, per `## Design` §10(b): counts, classes and code paths ONLY — no vault note name, no live identifier, and specifically none of Task 10's repair pairs and none of the detector's per-note issue lines, both of which are stdout of the conductor's live run. Add `test_wi032_live_baseline_row_shape_and_redaction_wall` to `tests/test_whatsapp_migration.py`, reading the bracket's FINAL text, with three duties. (i) REDACTION, run over all THREE `docs/wi-032-*` artifacts (this bracket and both grounding artifacts) and deliberately NOT over `docs/whatsapp-jid-value-type.md`, which `## Design` §9 line 5 and F18 leg 6 keep one real number in on purpose: after stripping every `\b[0-9a-f]{40}\b` token, no `\d{9,}` run and no digit-immediately-before-`@`-and-a-domain-label survives — with the claimed match-shapes driven through that same predicate as fixtures and every literal RESERVED-block or synthetic (threat-model note 3: this module introduces no live identifier), `"15555550142"`, `"123456789012@s.whatsapp.net"` and `"15555550142@lid"` asserted to MATCH and `27cb78cc5a2099972dccea984664193e69414def` (the real pinned HEAD at `docs/wi-032-consumer-audit.md:92`, which carries the nine-digit run `984664193`), `1168`, `1025`, `82`, `663-665`, `2026-09-27` and a bare `@s.whatsapp.net` asserted NOT to. (ii) FIGURES: §1's six rows and five derived partition figures equal values DERIVED by parsing the census's own verbatim stdout block (`docs/wi-032-whatsapp-corpus-census.md`, its `(a)`, `(c)` and `(c')` lines) — never literals re-typed from this plan — so the bracket is proven to AGREE with the artifact it copies from; the check does not re-measure the live vault and no hermetic check can, and its coupling is declared in one line in the check itself: it pins that artifact's machine-output block and consumes the property that those three lines are its census script's stdout. (iii) SHAPE: `DATA-LOSS HOLD` is present, `merge-duplicate-persons.py:380-384` appears inside that row and NOT inside §3's ordered list, and that list has exactly two items naming the invariant and the endpoint. The check asserts the §5 HEADING exists and asserts NOTHING about §5's content — the conductor writes the exit figures there after the build, and a check pinning §5 empty would redden the floor at close-out. verify: test_wi032_live_baseline_row_shape_and_redaction_wall
```

```fold
id: M3
desc: The bracket's ENTRY row must separate `orchestrator/bin/merge-duplicate-persons.py:380-384` from the two loud consumer breaks and state it as a DATA-LOSS HOLD rather than as the third item of one list — it regex-reads a single `whatsapp` line and re-emits a scalar through `Path.write_text` outside the package boundary, so against a migrated vault it can silently drop a person's second JID or blank the field, which is the exact harm this item exists to prevent and the only one of the three measured breaks that does not announce itself.
design: `docs/wi-032-whatsapp-live-baseline.md` §3 states the two LOUD breaks as its ordered list — `orchestrator/src/invariants.py:663-665`, a vault-wide red invariant, and `HAL9000/backend_fastapi/routers/contacts.py:41,50`, a 500ing endpoint — and states `orchestrator/bin/merge-duplicate-persons.py:380-384` in its OWN row under the heading `DATA-LOSS HOLD`, because that site regex-reads a single `whatsapp` line and re-emits a scalar through `Path.write_text` outside the package boundary, so against a migrated vault it can silently collapse a person's list to one value or blank the field — the exact harm this item exists to prevent, and the only one of the three that does not announce itself.
landed: Task 13
work: §3 is built to `## Design` §10(c) — the M3 RIDER: its ordered list is the TWO LOUD breaks and only those two, `orchestrator/src/invariants.py:663-665` (red vault-wide) and `HAL9000/backend_fastapi/routers/contacts.py:41,50` (500ing), each with its pinned 40-hex HEAD; the raw-file writer at `orchestrator/bin/merge-duplicate-persons.py:380-384` stands OUTSIDE that list in its own row headed `DATA-LOSS HOLD`, carrying its pinned HEAD, its reaching callers (`bin/apply-vault-review.py:152,158`), the `whatsapp: ""` clearing path (`docs/wi-032-consumer-audit.md:202-204`) and the conductor instruction that neither that script nor `apply-vault-review.py` is run against the vault post-migration until the other repo fixes it; and a one-line pointer to `docs/wi-032-consumer-audit.md:227-239` for items 4–7 of its seven-site list rather than a re-listing. §3 also carries the 26-lid sentence `## Approach` now carries. (iii) SHAPE of Task 13's check asserts it: `DATA-LOSS HOLD` is present, `merge-duplicate-persons.py:380-384` appears inside that row and NOT inside §3's ordered list, and that list has exactly two items naming the invariant and the endpoint. verify: test_wi032_live_baseline_row_shape_and_redaction_wall
```

```fold
id: M4
desc: `format_repair_disclosure` must render each record's stored value ESCAPED rather than VERBATIM — one physical line per record, guaranteed, with newline, carriage return, tab and the ANSI escape rendered as visible escapes — and the M1 check must plant one class-C note whose stored value carries an interior newline plus the text of `CORROBORATED_HEADER` and assert the line count still equals the record count and no forged header appears: `WhatsAppJID.parse` normalizes with `str(raw).strip().lower()` (`identifier.py:273`) so an INTERIOR control character survives into `.jid` while `normalize_phone` strips every non-digit (`phone_normalization.py:52-55`), making such a value phone-bearing, domain-less and therefore class C — so the one artifact the irreversible 82-note go/no-go is read against can be reflowed or have a section header forged by the very data it describes, and the check's own "exactly one line per class-C plant" oracle is asserted only over clean plants that cannot falsify it.
design: `format_repair_disclosure` renders EVERY field of every `RepairDisclosure` — `path`, `stored_value` and `proposed_jid` alike — through the single module-level helper `_escape_for_one_line`, which escapes the backslash first and then renders as a visible `\xNN`/`\uNNNN` escape every character `str.splitlines()` treats as a line break and every character whose `unicodedata.category` is `Cc`, `Cf`, `Zl` or `Zp` (so the newline, the carriage return, the tab, the ANSI `\x1b` and their whole class), which makes ONE PHYSICAL LINE PER RECORD a guarantee of the formatter over ANY stored value instead of an accident of the data — and Task 10's M1 check plants an UNCORROBORATED class-C note whose stored value carries an interior newline followed by the text of `CORROBORATED_HEADER` and asserts that the output's line count still equals the record count plus the headers the formatter itself emitted, and that no output line EQUALS a header constant the formatter did not emit.
landed: Task 10
work: The M4 RIDER — the disclosure's render, per `## Design` §10(d): add the module-level helper `_escape_for_one_line(raw: str) -> str` to `scripts/migrate_whatsapp_to_list.py` and route EVERY field of every `RepairDisclosure` through it in `format_repair_disclosure` — `path`, `stored_value` and `proposed_jid` alike, so the guarantee is total over the RECORD and survives a later change to the repair spelling. The helper escapes the backslash FIRST (so the rendering is unambiguous) and then renders as a visible `\xNN`/`\uNNNN` escape every character `str.splitlines()` treats as a line break and every character whose `unicodedata.category` is `Cc`, `Cf`, `Zl` or `Zp`; every other character passes through unchanged. The implementation is the CATEGORY test ALONE — that set CONTAINS the break set, which leg (1) proves rather than assumes — and the rendering is pinned so nothing is a judgment call: `\\` for the backslash, then `f"\\x{cp:02x}"` for a codepoint below `0x100` and `f"\\u{cp:04x}"` for the rest. Extend `test_whatsapp_dry_run_discloses_each_class_c_repair_pair` — not a new check, because this is the property that makes that check's own oracle total — with five legs, each oracle DERIVED and never listed. (1) TOTALITY: `BREAK_CODEPOINTS = frozenset(cp for cp in range(0x110000) if len(f"a{chr(cp)}b".splitlines()) > 1)` computed ONCE at module level (~1s; compute it once, never replace it with a hand list of characters — the hand list is the defect this leg exists to prevent), then for every `cp` in it `_escape_for_one_line(f"a{chr(cp)}b").splitlines()` has length 1, and for every `cp` in it plus `0x1b` the escaped rendering contains no such raw character. (2) NO-OP ON CLEAN: `_escape_for_one_line(x) == x` for every field of every clean plant, so the escape is the identity wherever verbatim is safe and the 82 live bare digit runs render exactly as a verbatim render would. (3) THE ADVERSARIAL PLANT: one more class-C note, planted through the SAME `_temp_vault` door as every other plant (so §8's PROVENANCE clause is unaffected), as a YAML double-quoted scalar carrying the `\n` escape followed by the text of `CORROBORATED_HEADER` imported from the module, with the RESERVED-block number `447700900321` and its `phones[]` holding no matching digits — asserted before it is used with: the value read back out of the note CONTAINS the planted control character, `classify_field` called on it returns exactly `["C"]`, and `phones_match` over that note's own `phones[]` returns False so it lands in the UNCORROBORATED section. (4) LINE COUNT STILL EQUALS RECORD COUNT: `len(format_repair_disclosure(plan).splitlines())` equals the record count plus the number of headers the formatter itself emitted, with BOTH terms derived — the record count by calling `classify_field` over the plants, the header term by calling the formatter over the same plan with the adversarial plant removed and counting the header lines it produced. (5) NO FORGED HEADER: the set of output lines EQUAL to any of the three imported header/banner constants is exactly the set that run produced, so a header appearing only because the data spelled one is RED. Then complete the 2×2 of class-C sub-cells by planting the fourth cell — a CORROBORATED control-character-bearing note — with its corroboration likewise computed by calling `phones_match` and never written beside the plant. verify: test_whatsapp_migration_dry_run_then_write_then_readback test_whatsapp_dry_run_discloses_each_class_c_repair_pair
```

## Verification

How to know the whole thing works, end to end. The five `check:` names are the machine floor — plus the two
plan-task checks `## Mitigation Folds` adds, which are verification artifacts and not criteria
(`test_whatsapp_dry_run_discloses_each_class_c_repair_pair` for M1 and M4 — M4 rides the SAME check because the
escape is what makes that check's one-line-per-record oracle total rather than clean-plant-only — and
`test_wi032_live_baseline_row_shape_and_redaction_wall` for M2 and M3). This section is
what the floor is not — the smoke path, the graceful failures, the downstream consumers, the DERIVED
regression enumeration, and the one live act a cage cannot perform.

**Happy path (the smoke test).** Materialize the corpus into a temp vault, run
`plan_migration` and read its six per-cell counts; run `apply_migration`; run `readback_migration`; assert
the triple agrees part-for-part and that every person's `.key` multiset is unchanged. Run `apply_migration`
ONCE MORE over the result and assert it writes nothing — zero write-door calls, the digest unchanged, the
same triple — which is the retry remedy's own property (`## Design` §7). Then, on the same
vault: `PersonRepository(vault).get_by_identifier(WhatsAppJID.parse("15555550142@lid"))` returns Thrandell,
`repo.resolve("15555550142@lid")` returns Thrandell, `repo.get_by_phone("5555550142")` returns None, and
`repo.get_by_phone("447700900789")` returns Fennwick.

**Failure modes that must fail GRACEFULLY.** A bare number written to `whatsapp:` through any of the three
dict doors: `NameGateRefusal` with `.pattern == "whatsapp_not_a_jid"`, `.refused_value` set, the note
byte-identical, the value absent from the message and from the traceback. A `save` of a person whose STORED
value is class C/D/E: the same refusal, the value still on the model and still in the note, and the note
still writable through every delta arm. A note carrying a nested container under `whatsapp:`: `lint_vault`
reports it and does not crash. An absent or blank `--vault`: the migration exits non-zero before touching a
filesystem. A `NameGateRefusal` mid-run on a note the plan called convertible: the run ABORTS loudly — it is
a defect, not a transient, and must never be caught and counted.

**Integration — downstream consumers that must still work.** `tests/test_repositories.py` (its John Smith
fixture stores the class-C scalar `whatsapp: "447990558521"` at `:33` and `test_get_by_phone_whatsapp_jid`
at `:316-319` asserts `get_by_phone("447990558521@s.whatsapp.net")` finds him — still green, because the
tolerant reader accepts the scalar and the value is phone-bearing so it still pivots) and
`tests/test_identity_index.py` (`:76-84` asserts a `whatsapp` equal to a `phone` unifies to ONE `phone:` key
with no conflict — still green for the same reason). **Neither is a declared write target, and that is a
PREDICTION to be falsified by running them, not a conclusion:** if either goes red the cause is in the
design and the remedy is the design, not the test. The out-of-tree consumers are already measured — 20
production sites, zero element-type assumptions, zero whole-record projections
(`docs/wi-032-consumer-audit.md`) — and the cardinality breaks are disclosed in the live bracket's
entry row rather than fixed here: the first three named individually, the third of them in its own
`DATA-LOSS HOLD` row (`## Design` §10(c)), with items 4–7 carried as a pointer to the audit.

**Regression — DERIVED from the edited surfaces, not inherited.** Sweep the resolved test roots for modules
naming each `## Write Targets` path and run every module the sweep returns. The census below is a FLOOR
measured on 2026-09-27 and never a total — this derivation has under-reached at its reading step every time
anyone has run it, which is why Task 12 RUNS each predicate instead of trusting this list:

| edited surface | modules that assert into it | what each requires |
|---|---|---|
| `obsidian_schemas/identifier.py` | `tests/test_identifier.py`, `tests/test_phone_normalization.py:105-119` | the `MIN_DIGITS` boundary pins on `parse` — green because `parse` is untouched; this is the module that goes red if Ruling A's alternative (b) is ever taken |
| `obsidian_schemas/models.py` | `tests/test_parser.py:161`, `:248-264`, `tests/fixture_vault.py:85-105` | the declared person oracle hand-transcribes `models.py`'s defaults, so `whatsapp: ""` → `[]` travels with the annotation |
| `obsidian_schemas/name_gate.py` | `tests/test_name_gate.py`, `tests/test_name_gate_wall.py` (arm sweep, `EDITED_FUNCTION_ARM_COUNTS`'s six per-function equalities, the `ast` single-home) | no spurious arm; `declared_type` never `absent`; no `ast` outside `tests/derivations.py` |
| `obsidian_schemas/repositories/person.py` | `tests/test_repositories.py`, `tests/test_identity_index.py`, `tests/test_identity_endgame.py` (clause (e1) over 29 `save` lines, the Cut-0 resolve golden at `:672-729`, `ITEM_EDITED_QUALNAMES`'s rows at `:1065-1080`, `phone_index_iteration_sites` at `:642-644`, `resolve`'s no-index-reads clause at `:692-698`), `tests/test_provenance_write_seam.py`, `tests/test_write_target_seam_wall.py`, `tests/test_concurrent_access.py` | prose APPEND-ONLY; the golden cannot move (the roster carries no `whatsapp` at all); no new write capability or frontmatter payload binding; every phone-index iteration `materialized`; `resolve` reads no index directly |
| `scripts/lint_vault.py` | `tests/test_lint_vault_fix_rules.py` (the oracle table scoped to `auto_fixable_emitter_checks`, the seven write-causing detectors, the four-bucket accounting), `tests/test_lint_vault_fix_gate.py`, `tests/test_stem_name_divergence_detector.py` (the marked-set equality, `_divergence_issues`' filter on `issue.check`), `tests/test_vault_path_required.py` (the no-implicit-default scan over `scripts/**`) | a report-only rule owes no oracle; the divergence module's four assertions untouched; no forbidden default pattern |
| `scripts/migrate_whatsapp_to_list.py` | `tests/test_name_gate_wall.py` (its universe is package-and-scripts), `tests/test_vault_path_required.py:312-331`, `tests/test_address_splitter.py:102`, `tests/test_company_name_contract.py:615-621`, `tests/test_write_routing.py:91`, `:370` | every frontmatter write arm routes through `gate_write` with a resolved declaration; no `expanduser`/`Path.home()`/`/Users/`; no second address splitter; no write routing around the door |
| `tests/derivations.py` | `tests/test_lint_vault_fix_rules.py:288`, `tests/test_stem_name_divergence_detector.py:144` — the two existing consumers of `mutating_drive_vault_args` | each runs the scan over its OWN file only, neither calls `apply_migration`, so adding the member changes neither answer |
| `tests/fixture_vault.py` + the two corpus notes | `tests/test_fixture_vault.py` (the freeze, the byte-copy, the privacy wall and its reach, `roundtrip_representative` uniqueness, the type-registry sweep, the census verdict loop, the skip surface / `LOADABLE` / `RESOLVABLE` declarations), `tests/test_writer.py:404-428`, `tests/test_parser.py:248-264`, `tests/test_stem_name_divergence_detector.py:341-352` | digest regenerated; zero privacy violations with no exemption added; the representative gate-clean and storable; no declared resolution answer moved; the marked set untouched |
| every NEW `tests/test_*.py` | `tests/test_fixture_vault.py:1373-1395`, `tests/test_provenance_write_seam.py:1828-1861`, `tests/test_loud_fail_harness.py:103`, `tests/test_ac_interpreter.py:95-106` | names no `ast`; IMPORTS every skip reason rather than typing it; every top-level `def test_` globally unique |
| `docs/wi-032-whatsapp-live-baseline.md` | `tests/test_vault_path_required.py:436-450` — and, NEW this fold, `tests/test_whatsapp_migration.py`'s `test_wi032_live_baseline_row_shape_and_redaction_wall` | `docs/**` is EXCLUDED from that scan's domain (`DOC_SCAN_EXCLUDED`), so the file joins no STANDING markdown wall — which is exactly why M2 makes this item ship one: the new check is the only thing that reads this file's text, it asserts redaction, census-derived figures and §3's shape (`## Design` §10(b), §10(c)), and it asserts nothing about §5 so the conductor's exit numbers cannot redden the floor |

**Four counting walls, and each ships its claimed match-shapes as fixtures.** AC-3's derived arm set,
Task 12's wall census and — added by these folds — Task 13's redaction predicate, whose oracle is
`matches == 0` over a document's text and so is the purest member of the class, plus Task 10's repair-disclosure
LINE COUNT, whose oracle is `lines == records + headers`, are all oracles whose value is
a COUNT or a SET of structural matches, and
`matches == N` says nothing about the matcher's reach. So each claimed shape is driven through the wall's OWN
predicate — never a re-implementation — as a GREEN fixture on every floor run: for the arm set, a planted
arm that MUST be collected and a near-miss (a function that parses frontmatter and writes nothing) that must
NOT be; for the containment scan, a planted `apply_migration(vault)` call that must be collected and a
planted call with an unreducible vault expression that must RAISE; for the line count, M4's adversarial plant —
a class-C value carrying an interior newline plus the text of `CORROBORATED_HEADER` — which is the shape that
falsifies `lines == records` if the formatter does not escape, driven through `format_repair_disclosure` itself,
beside the totality leg that drives every codepoint in the DERIVED `BREAK_CODEPOINTS` set through
`_escape_for_one_line` (`## Design` §10(d)). A wall that passes by matching everything
and is then narrowed back with nothing checking the narrowing is the specific failure this buys out of; a wall
whose only inputs cannot falsify it is the same failure wearing a green tick, and the line count was one until
M4 landed.

**The live replay — a CLOSE-OUT step, outside the cage, never a plan task.** This is an incident-class item:
it exists because a malformed JID was written for a real person through HAL9000's PATCH door on 2026-09-09
and repaired by hand. A green fixture battery is not evidence that the door now refuses it. After the build
lands and before the item closes, the conductor:

1. Commits `docs/wi-032-whatsapp-live-baseline.md`'s ENTRY row (Task 13's figures) and shows Dave the two loud
   consumer breaks and, separately, the `DATA-LOSS HOLD` row with its do-not-run instruction
   (`## Design` §10(c)).
2. Runs the migration's DRY RUN against the live vault and shows Dave the six per-cell counts beside the
   census's, including the 1025 shape-only figure named as the population with no semantic effect — AND the
   repair disclosure's 82 `(stored value → proposed JID)` pairs with the uncorroborated member first
   (`## Design` §10(a)), which is the artifact the go/no-go on the irreversible re-spellings is actually taken
   against. **Read it as EXACTLY 82 record lines plus its two headers** — that equality is guaranteed by the
   render (§10(d)), so a line count that disagrees is a defect and not a long value, and any `\n`/`\x1b`-style
   visible escape in a printed value is the render doing its job rather than a corrupt note. Those pairs stay on
   the terminal: nothing from them is pasted into the bracket or any other tracked
   document (§10(b)).
3. On Dave's go, runs `--apply`, then the readback, then `scripts/lint_vault.py` and reads the new
   `whatsapp_not_storable` check's issue COUNT as an INDEPENDENT second witness to `|R|` — two counts by two
   tools that must agree, which is the whole reason that detector exists. The count is what the bracket carries;
   the detector's per-issue lines name vault notes and stay on the terminal (§10(b)).
4. **Replays the actual incident, unmuted:** attempts to write `"+44 7739 341679"` into `whatsapp:` on a
   DISPOSABLE person note through HAL9000's PATCH door and confirms the refusal, the unchanged bytes, and
   that the note is still editable for everything else. A disposable note, never Kim Faura's own and never
   any production record. **Redact the transcript before it is recorded in any tracked document** — the run
   is live, the transcript is not.
5. Writes §5's exit numbers as the partition's three parts with their two named sub-counts.

A caged builder's vault writes are reverted at the merge boundary, so any of the five run as a plan task
would change nothing and report success.

## Scope Boundary

**What we are NOT doing.**

- **Not typing `emails`, `phones`, `linkedin` or `slack`.** Ruling C: `whatsapp` only. The follow-on item is
  framed as "derived typed accessors alongside the stored `List[str]`" and NOT as
  `emails: list[Email]` — F13 shows a strictly-typed stored field cannot hold a value the door refuses
  without erasing it or making the note unsaveable, and `slack` cannot be typed at all without inventing the
  workspace the frontmatter does not carry (`person.py:305-312`). The class-Ø rule generalizes to it.
- **Not narrowing `WhatsAppJID.parse`.** Rejected item 7, on measured blast radius: `parse_identifiers` is
  `strict=True` by default and is the declared Phase-4 adapter seed, the WI-035 pivot and
  `_resolve_identifier` both want maximum reach, and `tests/test_identity_index.py:80` would keep passing
  while silently ceasing to test its own name.
- **Not CONTRACTING the tolerant reader.** Expand → migrate → contract is three phases and this item ships
  the first two. The third is gated on `|R|` reaching zero by HAND repair, on no schedule this item can
  promise. Refusing the scalar at read time converts an un-migrated note into an INVISIBLE one (rejected
  item 3).
- **Not adding a `schema_version` field.** That is WI-010's own question, which this migration un-parks by
  being the first real one. Whether WI-010 then un-parks as a generic mechanism or closes as answered is a
  queue call, not a scope creep.
- **Not touching `_IDENTIFIER_PRIORITY`.** A different frame's ordering, right as it stands, and its
  explaining comment is frozen prose (`## Design` §5(f)).
- **Not widening any other item's wall.** Not WI-016's privacy wall (rejected item 11), not WI-016's census
  digest (`## Design` §9 line 4), not WI-024's `AUTHORIZED_PROSE_OWNERS` (rejected item 15), not WI-029's
  `NOT_RENAMEABLE_MARKER` (rejected item 14), not the `SKIP_REASONS` two-home equality, not the `ast`
  single-home.
- **Not fixing `orchestrator/bin/merge-duplicate-persons.py`.** It edits frontmatter as TEXT outside the
  package boundary, so `## Intent`'s "every writer refuses it at the boundary" is false of it BY DESIGN — a
  named exclusion the absolutes sweep already scopes, and already on the WI-029 divergence-generator list.
  Disclosed in the live bracket's entry row as its own `DATA-LOSS HOLD` row (`## Design` §10(c)) carrying the
  do-not-run instruction, fixed in another repo's item. Declining the fix is not declining the disclosure.
- **Not a `_whatsapp_index`.** WI-023 spent a whole item deleting the legacy per-kind email dict so
  resolution has ONE authority. The lid is already in the WI-125 index under `jid:<lid>`; the gap was a
  public reader (rejected item 2).
- **Not provenance (`source`/`observed_at`/`corroboration`) on the note.** Out by Dave's 2026-09-26 ruling
  (2) — the writer keeps its own ledger, keyed by value (rejected item 5).

**Unchanged files — do NOT touch, and the reason for each.**

- `obsidian_schemas/writer.py` — F8's projection step is DELETED from scope by F13 leg 1: with the stored
  field `List[str]` nothing dataclass-shaped is ever in `model_fields`, so there is no projection to write
  (rejected item 9). The `no !!python/object in the bytes` assertion stays as the guard that keeps it true.
- `obsidian_schemas/parser.py` — `_normalize_frontmatter` stays field-name-AGNOSTIC; the tolerant read lives
  on the model (`## Design` §2).
- `obsidian_schemas/phone_normalization.py` — a stdlib-only leaf whose two consumers both WANT the naive
  `@`-split. Fix the caller, not the leaf (rejected item 4).
- `docs/vault-shape-census.md` and `docs/vault-fixtures.md` — another item's digest-frozen artifact and its
  signed criteria. A row here is a conductor pass plus a D4b re-sign in front of Dave, never a build edit.
- `tests/test_fixture_vault.py`, `tests/test_identity_endgame.py`,
  `tests/fixtures/identity_endgame/prose_surface_cut0.json`, `tests/test_stem_name_divergence_detector.py`,
  `tests/test_lint_vault_fix_rules.py` — walls this item JOINS and satisfies, never files it edits. Task 8's
  check IMPORTS `_golden` and `AUTHORIZED_PROSE_OWNERS` from `tests/test_identity_endgame.py` (`## Design`
  §6): reading a wall's own reader and its own tuple is how the conjunct avoids a second spelling of either,
  and it is not an edit to that module or to the JSON it reads.
- `tests/test_writer.py`, `tests/test_parser.py`, `tests/test_repositories.py`,
  `tests/test_identity_index.py`, `tests/test_phone_normalization.py` — predicted GREEN under the design and
  RUN to confirm. If one goes red, the remedy is the design; re-expecting a refusal in a round-trip test is
  rejected item 12.
- `README.md`, `CLAUDE.md`, `SESSION_LOG.md`, `pyproject.toml`, `pipeline-runners.yaml`, `state/**` — outside
  this project's `write_authority` by declaration, and nothing in the build depends on any of them.

## Risk Analysis

This touches the person corpus Dave's whole estate resolves against, so the honest accounting matters more
than the reassuring one.

| # | What could go wrong | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| 1 | The migration drops a person's second WhatsApp identity | LOW — nothing populates second JIDs yet, so the live population is zero on day one | HIGH — silent identity loss, invisible until a lookup fails | AC-5 leg (c)'s `.key` multiset oracle plus TWO per-note counts (parseable, and TOTAL including unparseable), computed from a RE-READ of the note bytes; the two-JID plant is the fixture whose whole purpose is this |
| 2 | A build erases a value the door refuses | LOW — AC-4 leg (b) is the wall | HIGH — silent data loss on exactly the population the item exists for | the stored field is `List[str]` so nothing is dropped at READ time; AC-4 leg (b) asserts the raw string survives by equality against the note's bytes; rejected item 8 names the branch a build reaches by default |
| 3 | The migration clears a class-D value to reach a flat zero | LOW now that the exit figure is a PARTITION | HIGH — same erasure, arriving through the run instead of through the reader | the never-clears conjunct is asserted PER PLANT in AC-5 leg (e), so the route is red BY INTENT and not as a side effect of leg (c)'s total-value count (rejected item 17) |
| 4 | The scalar→list flip breaks a consumer on migration day | **CERTAIN — seven measured sites** | MEDIUM — one red invariant, one 500ing endpoint, one raw-file writer that can collapse a list, four further readers | measured and pinned in `docs/wi-032-consumer-audit.md`; disclosed in the live bracket's ENTRY row in front of Dave BEFORE the write, with the raw-file writer separated into its own `DATA-LOSS HOLD` row carrying a do-not-run instruction (`## Design` §10(c)) because it is the only one of them that is silent; the tolerant reader means the LIBRARY never breaks, only code that reads the field as a string |
| 5 | A consumer writes a bare number and starts being refused | MEDIUM — 82 live notes prove the producers exist | LOW-MEDIUM — a break in somebody else's path, which is the Intent working | the migration's repair pass runs FIRST, so all 82 are key-preservingly repaired and the door refuses nothing on the live vault the day it lands; the two HAL9000 generic entity doors are named in the disclosure |
| 6 | A back-out is needed after the live run | LOW | MEDIUM — reverting the library makes every migrated note INVISIBLE, not oddly shaped | the back-out is a REVERSE migration through the same door, exact up to 82 canonical re-spellings and only while no note carries a second JID; both qualifiers are in `## Approach`'s back-out paragraph and in the bracket |
| 7 | A build turns another item's green wall red and "fixes" it there | MEDIUM — it has been the single most productive defect class across nine gate rounds | MEDIUM-HIGH — buys a green by destroying another item's evidence | four rejected items name the exact branches (11, 12, 15, 16); `## Scope Boundary`'s unchanged-files list says which files are walls; Task 12 RUNS each wall's own predicate rather than reasoning about it |
| 8 | `lint_vault` crashes on a malformed live note | LOW | MEDIUM — the repair tool is what finds malformed notes, so a crash is the worst possible failure mode | the detector's one classifier call is wrapped and reports under the same check; a nested-container plant exercises that arm rather than assuming it |
| 9 | A live identifier the new repair disclosure printed is pasted into the tracked bracket | MEDIUM — it is the natural move: record the detail you were shown in the document where you record what you decided, and this fold is what puts 82 real telephone numbers on the screen | MEDIUM — a permanent committed disclosure of real contact data, in a file `docs/**` exclusion keeps outside every standing markdown scan | the transparency mitigation ships WITH its wall rather than after it (`## Design` §10(b)): Task 13's check runs a redaction predicate over the bracket's FINAL text — no `\d{9,}` run and no JID-shaped token outside a 40-hex commit token — and ships both its match and near-miss shapes as fixtures, so it can pass neither by matching everything nor by matching nothing |
| 10 | The go/no-go is taken against a disclosure the disclosed data reflowed or forged a header into | LOW on today's corpus — the census measured all 82 as bare digit runs — but UNMEASURED, because the census was never asked about interior control characters, and the three unvalidated doors that wrote the Kim Faura value are the same three that could write one | MEDIUM-HIGH — the conductor's line count stops equalling the repair count, the UNCORROBORATED-first ordering stops being reliable, and a forged `CORROBORATED` header can move the one row the census asked a human to read into the safe half of an IRREVERSIBLE 82-note authorization; no note is corrupted either way, since the repair reads only `phone_digits` | the render is escaped at the formatter rather than the values being trusted (`## Design` §10(d)): one helper over EVERY field of the record, the rule stated over the whole class of line-breaking and invisible characters with the break set DERIVED by calling `str.splitlines()` rather than hand-listed, and the M1 check's own line-count oracle made total by an adversarial class-C plant carrying an interior newline plus the text of `CORROBORATED_HEADER` — so the assertion that used to hold only over clean plants now holds over any stored value |

**Migration path.** Expand (the tolerant reader plus the list-emitting writer, shipped in one commit) →
migrate (the conductor-run bracketed live pass, dry run in front of Dave, then `--apply`, then the readback
and the detector as two independent witnesses) → contract (NOT this item; gated on `|R|` reaching zero by
hand repair). The position is forward-only from the moment any note gains a second JID, and the bracket's
exit entry is what records that window closing.

**Rollback plan.** Before the live pass: the build is a library revert, because no note has changed shape.
After the live pass: a reverse migration through the same door — `--apply` in the other direction — never a
library revert, because a list-shaped note against pre-WI-032 code raises `SchemaDriftError` and lands on
the load skip surface, INVISIBLE rather than oddly shaped. The tolerant reader is kept either way.

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

## AC Sign-off

```verdict
gate: ac-signoff
verdict: PROMOTE
date: 2026-09-27
reviewer: dave
channel: conversational
signed_at: 2026-09-27T08:00:00+01:00
provenance: verified
signoff_escalation: ESC-WI-032-exploring-awaiting-ac-signoff-eb28d58c
ac_hash: dd772c1183de
intent_hash: 6eab0010f9ce
ac_hash_AC-1: 291f1a902f27
ac_hash_AC-2: 0f67fabf15c5
ac_hash_AC-3: 6e8ae465f384
ac_hash_AC-4: 7bfa6009474f
ac_hash_AC-5: 975c8d928253
artifact: docs/spec-reviews/WI-032-dave-review-2026-09-27.md
```

## Data Audit — 2026-09-27

**Recommendation: PROMOTE to specced**

### Trigger check

**Class 1 AND Class 2, both firing, and this is the heaviest-premise item the gate has seen on this
project.** Class 1: every criterion computes against a population nobody had measured for this field —
how many of ~1,170 person notes carry a `whatsapp` value at all, how they distribute over the six-cell
class table, how many people hold two JIDs, how many lids collide with a stored phone. Class 2: AC-3
introduces a refusing write door and a new `lint_vault` detector, and AC-5 runs a migration — three new
rules whose correctness is a claim about their effect on the corpus **as it stands today**, not on
hypothesized future inputs. The item also quantifies universally in `## Intent` ("never reaches a person
note", "Every writer refuses it at the boundary", "nothing already written is silently dropped"), so the
counterexample hunt below is a required element rather than an extra.

### Premise

Eleven load-bearing empirical claims, in the order the criteria lean on them:

1. The six-cell class distribution over the live person corpus — the denominator class Ø and the five
   non-empty classes (AC-1, AC-5, `## Approach` step (4)).
2. `|R|`, the terminal-state residual = class D + class E (+ class C under Ruling B's alternative arm) —
   the live bracket's exit figure and the population AC-3's REPORT LEG detector ships against (F21).
3. The class-C repair count, and that the repair is key-preserving on every member (AC-5 leg (d)).
4. That bare telephone numbers actually DO arrive in this field, so the door is a wall and not theatre.
5. That a person holding two JIDs is a real shape a scalar cannot hold — the premise paragraph's 51.
6. That the lid→phone mis-index has a live victim population (`## Problem / Motivation` item 3, AC-1).
7. Fixture-corpus shape: 22 `whatsapp`-carrying notes, 21 of them class Ø, one class-C value on the sole
   person `roundtrip_representative`, and an admissible non-representative, non-skip, non-census-specimen,
   non-stem-divergent receiver for it (F6, F17, F18 leg 2, F19 leg 5, AC-1's WHERE clause).
8. That every planted literal is an unused member of a reserved block and unclaimed tree-wide (F17 leg 3,
   F18 leg 6, AC-5's pinned two-JID pair).
9. That no consumer assumes the ELEMENT type — the axis that decides Ruling B's recommended arm.
10. That no consumer re-serializes a whole stored person record, so AC-3's `save`/`write_markdown_file`
    refusal arms are walls rather than incidents.
11. That `lint_vault --fix` still repairs a class-C-bearing note's OTHER issues once the gate arm exists —
    AC-3 REPORT LEG conjunct (4) asserts this and it is a rule-effect claim, not a design claim.

### Predicate + result

**Claims 1–6 are grounded in `docs/wi-032-whatsapp-corpus-census.md` (conductor-performed 2026-09-27
07:35 BST, in HEAD, one script, stdout verbatim, read-only, `$VAULT`/`$BRIDGE_DB` rendered).** Re-read
this round line by line against the predicates this document declares. The census's `classify` calls
`WhatsAppJID.parse` and computes the domain off `j.jid` — the normalized, lowercased string
(`identifier.py:266`, `:273`, re-read) — which is the reading `## Exploration Notes` pins, not a restated
shape. Its `"E" if j.phone_digits == "" else "C"` branch is EQUIVALENT to the table's definitions rather
than merely similar: `parse` yields an empty `phone_digits` only via the `@lid` substring branch
(`identifier.py:276-281`), so a non-storable value with no phone digits took that branch by construction.
The class-Ø test precedes both predicate calls, which is the ORDER AC-1 asserts.

| cell | count | of 1174 `type: person` |
|---|---|---|
| Ø (absent key 6, `""` 1025, YAML null 0) | 1031 | 87.8% |
| A (storable, phone-bearing) | 35 | 3.0% |
| B (storable `@lid`) | 26 | 2.2% |
| C (parses, phone-bearing, not storable) | 82 | 7.0% |
| D (non-empty, does not parse) | 0 | — |
| E (`@lid` substring, non-storable domain) | 0 | — |
| already list-shaped | 0 | — |

1031 + 35 + 26 + 82 = 1174, and the model-side cross-check agrees (the repository loads 1174 with a skip
surface of 0), so no note is hidden from either view. `whatsapp: str = ""` is confirmed at
`models.py:94`, which is why 1025 notes carry exactly the model's own default — F16's derivation holds on
the real numbers, not just on the argument.

- **Claim 2: `|R| = 0`** under the recommended arm Dave ruled (D + E = 0); 82 under the alternative he
  declined. So the partition's part (3) is empty on the live vault and the detector ships as a wall
  against the next bare number, not as a backlog. This does not soften anything: AC-5's mandated class-D
  and class-E plants make `|R|` non-empty on the hermetic suite, which is where F21's contradiction lived.
- **Claim 3: 82 repairs, all key-preserving.** All 82 class-C values are bare numbers with no `@` at
  all — no odd-domain spellings — so every one has non-empty `phone_digits` and AC-5 leg (d)'s
  phone-bearing guard never fires negatively on a live note. 81 of 82 already carry the same digits in
  their own `phones:`, and the 82nd keys on its own digits, so the `.key` multiset is preserved on every
  member and the readback oracle has a non-trivial population to prove "no identifier moved" against.
- **Claim 4: grounded.** 82 bare numbers, one every ~14 person notes.
- **Claim 5: grounded and reproduced exactly** — 51 bridge display names holding BOTH a phone-JID and a
  lid, against 475 distinct 1:1 names; 26 vault notes have already chosen the lid over the phone form,
  which is the scalar losing an identifier in the field.
- **Claim 6: the harmful shape is ZERO today.** None of the 172 bridge lids and none of the 26
  vault-stored lids has digits that `phones_match` any of the 141 stored phone digit-strings, so no live
  lookup for a real number returns a lid's owner. The defect is latent, which AC-1 already handles by
  PLANTING the falsifying member rather than hoping for one. See note (i) below on the census's wider
  inference.

**Claims 7 and 8 I grounded myself this round** (the census is scoped to the live vault and says so).
`rg 'whatsapp' tests/fixtures/vault/` returns exactly 22 notes; 21 carry `whatsapp: ""` and
`@Thrandell Ibberly.md:7` carries `447700900789@example.com` — F6 exact. `@Fennwick Drostane.md` exists
and carries `whatsapp: ""`, so AC-1's named receiver is available. The three reserved-phone patterns are
`^447700900\d{3}$`, `^07700900\d{3}$` and `^1?\d{3}55501\d{2}$` (`tests/test_fixture_vault.py:308-312`),
and reserved hosts are three `example.*` domains by EQUALITY plus `.test`/`.invalid`/`.example` by suffix
(`:306-307`, `:315-319`) — which confirms, structurally, that `s.whatsapp.net` is inadmissible in the
corpus's reach and that `lid.example` is admissible where `lid.example.com` is not. Every pinned literal
(`15555550142`, `15555550163`, `447700900987`, `447700900654`, `5555550142`) matches its pattern and
appears NOWHERE in the tree outside this document, its rounds drawer, the review artifact and the state
ledgers — unclaimed, as F17 leg 3 and F18 leg 6 claim. No `55501` run exists anywhere in the fixture
corpus today.

**Claims 9 and 10 are grounded in `docs/wi-032-consumer-audit.md`** (in HEAD, three repos at pinned
40-hex HEADs with dirty counts, literal commands, verbatim lines, 20 production sites on three axes).
Claim 9 comes back the way the fence hoped: **ZERO element-type assumptions** across all 20 sites — every
break is caused by the VALUE becoming a list, and each site would be equally happy with `List[str]`
elements once it indexes one. That is affirmative evidence FOR Ruling B's recommended arm rather than the
absence of evidence against it. Claim 10: **ZERO call sites** for `repo.save(person)` or
`write_markdown_file(entity=…)` in all three repos, with every field-level door enumerated — so AC-3's
whole-record refusal arms have no consumer caller today and, with `|R| = 0`, no live note to refuse.

**Claim 11 I ran as a rule-effect predicate against the code rather than accepting the criterion's
sentence.** `apply_fixes` hands the gate the DELTA, not the record — `gate_write(delta,
declared_type=fm.get("type"), whole_record=False)` at `scripts/lint_vault.py:1181-1182` — so a fix for an
unrelated issue on a class-C-bearing note presents a payload with no `whatsapp` key, the new arm is never
consulted (the delta-not-record rule), and the note's other issues still repair. The subsequent write
re-serializes the whole frontmatter (`_wfm(fm)` at `:1194-1198`) and re-emits the stored value unchanged,
so `--fix` neither refuses the note nor drops the value. AC-3 REPORT LEG conjunct (4)'s claim holds, and
it holds for a mechanical reason the document did not state.

Code mechanisms re-read directly, all as cited: `_index_entity` feeds `normalize_phone(entity.whatsapp)`
into `_phone_index` unconditionally (`person.py:266-270`); `_project_identifiers`'s `add()` returns on a
`None` or blank raw BEFORE parsing (`:318-320`), which is the existing convention class Ø rests on; and
`whatsapp` is projected through `WhatsAppJID.parse` at `:330-331`.

### Counterexample hunt (WI-293)

`## Intent` quantifies over an enumerable domain three times, and `## Exploration Notes` already carries
THE ABSOLUTES SWEEP over the document's own text. That sweep walks the DOCUMENT; this hunt walks the
ESTATE, which is the axis it cannot reach.

**Domain:** every code path in the three consumer repos plus this package that WRITES a `whatsapp` value
into a person note's frontmatter, at each candidate's own declared granularity (a raw-file writer is
judged as a raw-file writer, not by whether it imports this package). **Predicate:** does the write reach
`gate_write` — and if it does not, is it false-by-design or merely unaudited? Enumerated from the consumer
audit's per-repo sweeps (three greps per repo, `.py` and non-`.py`, tests listed separately) plus this
repo's own WI-021 derivation.

**One false-by-design member class found: writers OUTSIDE the package boundary that edit frontmatter as
text.** The member is `orchestrator/bin/merge-duplicate-persons.py:380-384` — it regex-reads the
`whatsapp` line, merges scalars, re-emits `whatsapp: "<v>"` via `_write_fm_field` and commits with
`Path.write_text`, bypassing `PersonRepository` and therefore the gate entirely. `## Intent`'s "Every
writer refuses it at the boundary" is FALSE of it by construction, and it is the one site that can
collapse a migrated list to a single scalar or clear it to `""` when the single-line regex misses a block
list. **Disposition: NAMED EXCLUSION, already filed.** The absolutes-sweep row scopes that universal to
"AC-3's DERIVED arm set plus the two whole-record-projection arms", i.e. the package's arms; the consumer
audit names this site as break #3 and relays it under "not this repo's to fix" (it is already on the
WI-029 divergence-generator list). It is not a class-C producer — it propagates whatever shape it read, it
does not synthesize a bare number — so it cannot falsify sentence one of `## Intent`. It is a
cardinality-era data-loss path, which is note (ii) below and a sequencing fact rather than a criterion
defect.

**Classes walked and found CLEAN, stated so the hunt is falsifiable:** HAL9000's two generic entity doors
(`entities.py:251` `find_or_create_stub`, `:461` `update_fields`) are gate arms, and they are the class-C
producers the disclosure paragraph names — in scope, refusing by design. The `new-person` skill and
orchestrator's `roles/enricher.yaml:163-176` both write through the PATCH door, so they are the same two
arms one level up. exocortex writes the field nowhere in production (its one site is the `ContactInfo`
mirror READ at `clients/contacts.py:74`). `lint_vault --fix` is a delta arm and was run as a predicate
above (claim 11) rather than reasoned about. Within this package, the WI-021 derivation plus
`tests/test_write_target_seam_wall.py` are the standing proof that no write site routes around the gate or
the seam. **Opt-in gating, scheduled external writers and grandfathered epochs: none found in this
domain** — there is no cron, no scheduled job and no env-gated writer of this field in any of the three
repos (the two bridge-store readers at `contact_normalizer.py:52` and `queue_writer.py:62` are READERS and
write no note; `jobs/sync_interactions.py` writes only the interactions DB).

### Conclusion

Every load-bearing empirical claim this item's five criteria and its live bracket rest on is measured,
dated today, taken read-only with the command and the verbatim stdout on paper, and both grounding
artifacts were in git HEAD before the ACs were presented for signature (the WI-300 door). The numbers
CONFIRM the design rather than merely permitting it: 1031 class-Ø notes are why the class-Ø fold (F16) was
the right correction and not defensive padding; 82 class-C notes make the door a wall against a value that
demonstrably arrives; zero element-type assumptions across 20 consumer sites is affirmative evidence for
Ruling B's recommended arm; zero whole-record projections make AC-3's `save` arms affordable; and
`|R| = 0` makes the TERMINAL-STATE PARTITION's exit row a number a conductor can produce without
adjudicating anything in prose. Nothing in the data contradicts a criterion, no premise is stale (the
oldest figure is 07:35 BST today), and the one hermetic-versus-live tension — class D and E are zero live
but mandated as plants — is exactly what F21's partition was built to hold. Two non-blocking notes, both
recorded rather than raised as OPEN questions, and neither touching a criterion or a ruling:

(i) The census §2 bullet "the resolution fix therefore changes no live lookup result on the day it lands"
is true of the harmful collision shape row (g) measures (a query for a REAL number returning a lid's
owner — population 0) and slightly over-broad for the other shape `## Problem / Motivation` item 3
describes (a query for a number nobody holds returning the lid's owner — population 26, since every
stored lid's digits sit in `_phone_index` by `person.py:266-270`). §3 scopes row (g) explicitly, the doc's
own premise plants its falsifying member rather than leaning on the census, and no consumer synthesizes
such a query (orchestrator strips the JID first; HAL9000's `resolve_by_whatsapp` has no production
caller), so the live blast radius is nil. Worth a sentence in the live bracket's entry row, not a revise.

(ii) The consumer audit's ordered break list — two hard breaks on migration day
(`orchestrator/src/invariants.py:663-665` red vault-wide, `HAL9000/.../contacts.py:41,50` 500ing) and the
raw-file write above — is measured and sequenced in the artifact, but `## Approach`'s disclosure paragraph
still discloses only the class-C producer refusal. The cardinality break is the wider disclosure, and the
live-run ship condition is where it belongs (the bracket's entry row, in front of Dave, before the write).
Flagged for the spec-writer's extension of `## Write Targets`; it changes no criterion and the AC frame is
frozen, so it is not worth an AC re-sign.

```verdict
gate: data-premise
verdict: PROMOTE
date: 2026-09-27
model: claude-opus-5
note: Both precondition artifacts in HEAD and re-read against the declared predicates — live corpus measured at 1174 person notes (Ø 1031 / A 35 / B 26 / C 82 / D 0 / E 0, so |R| = 0 and the class-C repair is 82 key-preserving re-spellings), 51 dual-JID bridge names, 0 live lid→phone collisions, 0 element-type assumptions and 0 whole-record projections across 20 consumer sites; fixture claims (22/21, Thrandell's class-C, @Fennwick Drostane, the reserved patterns, every pinned literal unclaimed) and AC-3's --fix-still-repairs rule-effect verified in-tree this round; counterexample hunt found one false-by-design writer outside the package boundary, already a named exclusion.
```

## Threat Model — 2026-09-27 (round 2)

**Recommendation: PROMOTE to threat-modeled — round 1's three mitigations all HELD and are re-emitted
unchanged, plus ONE new required mitigation on the surface round 1's own M1 created. Every one lands on an
existing Implementation-Plan task, no `criteria` fence moves, and Rulings A, B and C are untouched.**

Round 2 at this gate. Round 1 (above) raised M1/M2/M3; the spec-writer folded all three into a new
`## Design` §10 plus Task 10 and Task 13 riders, and the spec-reviewer then REVISE'd on two unpinned oracles,
which the spec-writer has also folded (`## Design` §6's COMPUTABLE FORM with Task 8's two legs, and
`## Design` §7's RE-RUN IS A NO-OP with Task 10's re-run leg). So this round's material is FOUR new things:
§10(a)/(b)/(c), §6's computable form, §7's re-run subsection, and the `## Mitigation Folds` record. I re-read
each of them and re-verified in code every claim of theirs that a security property rests on, rather than
reading the fold record and taking its word.

### What this round re-read, and what it re-verified in code

- **The three folds are faithful and their `desc` text is copied verbatim** into `## Mitigation Folds`. I did
  not judge the pairs from the fold record: I read §10(a), §10(b) and §10(c) and the Task 10 / Task 13 riders
  in place. All three are satisfied on the substance, not just quoted — §10(a) makes the per-note pair a
  `RepairDisclosure` record on the plan `apply_migration` already consumes, with `corroborated` recomputed the
  SAME way the census computed it (`phones_match` over the note's own raw `phones[]`) rather than by a second
  equivalence of its own; §10(b) ships the redaction wall itself with MUST / MUST-NOT match-shapes driven
  through its own predicate; §10(c) gives the raw-file writer its own `DATA-LOSS HOLD` row with the
  do-not-run instruction that makes it a hold.
- **`tests/support.py`'s `patcher` cannot leak.** Task 10's re-run oracle installs a call counter over
  `writer.update_frontmatter_field` through it, so I checked the undo path: `Patcher.undo` runs the stack in
  reverse inside a `finally` (`tests/support.py:67-78`), "including when the body raises". A counter that
  escaped its pass could otherwise have silently suppressed writes in whatever ran next — a false-assurance
  channel, and it is closed.
- **§6's computable form names mechanisms that exist.** `AUTHORIZED_PROSE_OWNERS`
  (`tests/test_identity_endgame.py:359`) and `_golden` (`:395`) are both where §6 and Task 8 say they are, so
  the conjunct is reachable by import rather than by re-spelling either. Security-neutral, checked because it
  is the newest material.
- **The detector opens no disclosure channel.** Re-read §4's arm: the `LintIssue` message interpolates
  `len(classes)` and the sorted CLASS LETTERS and no note-derived value (`## Design` §4, and its own closing
  sentence says so). Only `vf.path` carries a note name, which §10(b) discloses honestly as stdout-only and
  which is pre-existing `lint_vault` behaviour rather than this item's.
- **The go/no-go human step now READS the disclosure**, which is what makes M1 a mitigation rather than a
  print: `## Approach` step (4) carries it, and `## Verification`'s close-out step 2 orders the 82 pairs shown
  to Dave with the uncorroborated member first and step 3 keeps the detector's per-issue lines on the terminal.

### The three round-1 mitigations: all HELD

None is re-opened and none of the new material weakens any of them, so all three are re-emitted below with
their `desc` byte-identical. Two observations on their edges, both deliberately NOT re-raised:

- **M2's requirement is broader than M2's wall, and that asymmetry is correct.** The `desc` forbids the pairs
  in "any other tracked document" while the check ranges over the three `docs/wi-032-*` files. I considered
  extending it to `SESSION_LOG.md` — the one other tracked file the project's own close-out writes, and
  measured clean today (`rg '[0-9]{9,}' SESSION_LOG.md` → no matches, so it would be free on day one). I am
  NOT asking for it. A permanent redaction wall owned by WI-032 over an ever-growing conductor surface is
  exactly the widen-another-surface move this document declines three times (rejected items 11, 14, 15), and
  it would redden this item's floor forever for reasons with nothing to do with this item. The requirement is
  instead stated where the actor reads it — close-out step 2 ("nothing from them is pasted into the bracket or
  any other tracked document"), step 3 and step 4's redact-the-transcript line. Instruction is the right
  instrument here and a wall is the wrong one.
- **M1's check plants are unpinned literals, and that is affordable.** Task 13's check carries the clause
  "every literal RESERVED-block or synthetic" and Task 10's M1 check, in the same module, does not. It is not
  a gap worth a fence: the plants live in a temp vault outside `reach_files()`, F18 leg 6 already ratifies
  test-module literals, and a builder has no source of live numbers to reach for — the census carries none by
  construction. Noted below so the convention travels.

### STRIDE delta over the new material

Only the categories the new material moves; the rest stand as round 1 recorded them.

**Tampering — unchanged and slightly better.** §7's re-run subsection pins a property that was prose:
the second pass writes nothing, asserted by a CALL COUNT rather than by a digest, because "identical bytes
give an identical digest" — which is the right discriminator and closes a build that re-writes ~1168 live
notes on every retry. §8's SPELLING clause is correctly carried onto the SECOND `apply_migration` call site,
so the containment wall still collects both drives; a second drive spelled any other way raises there rather
than escaping. Nothing in §6 or §10 adds a write arm.

**Information disclosure — this is where the one new finding is.** §10(b) closed the WHERE of M1's
disclosure. What no section closes is the HOW, and it is the one thing that makes the disclosure trustworthy
at the moment it is read. §10(a) and Task 10 both specify that `format_repair_disclosure` returns "one line
per record carrying the note path, the stored value **VERBATIM** and the proposed JID", and the M1 check
asserts "the line set is EXACTLY one line per class-C plant". A stored value can falsify that, and I verified
the mechanism rather than supposing it: `WhatsAppJID.parse` normalizes with `str(raw).strip().lower()`
(`identifier.py:273`) — `.strip()` removes only LEADING and TRAILING whitespace, so an interior newline,
carriage return, tab or ANSI escape survives into `.jid` intact; `normalize_phone` then strips every
non-digit (`phone_normalization.py:52-55`), so `"447739341679\n<anything without an @>"` yields twelve digits,
parses, is phone-bearing, has an empty `jid_domain` and is therefore **class C** — the exact population the
disclosure prints. Rendered verbatim, one record becomes two or more lines, so the conductor's line count no
longer equals the repair count, the UNCORROBORATED-first ordering is no longer visually reliable, and a
stored value carrying a newline plus the text of `CORROBORATED_HEADER` renders a forged section header into
the one artifact an irreversible 82-note go/no-go is taken against. The plants are all clean, so the check's
own "one line per record" assertion is asserted over data that cannot falsify it — the stays-green-while-
unclassified shape this document rejects everywhere else (it is the stated reason class E is asserted rather
than assumed). Who writes such a value: the same three unvalidated doors that wrote the Kim Faura value, which
is the item's whole premise; the census measured the 82 as bare numbers with no `@` and was never asked about
interior control characters. This is M4, and it is a legibility-and-forgery mitigation rather than a
data-integrity one — the repair itself reads only `phone_digits`, so a control-character-bearing value still
repairs to a clean canonical JID and no note is corrupted. Same generator as M1 and M2: an unspecified
property of a disclosure surface. Cost: an escaping call in one formatter plus one plant.

**Spoofing, Repudiation, Denial of service, Elevation of privilege — no delta.** §6 and §7's new material
add no identity claim, no audit surface and no capability; §10's formatter is read-only and correctly kept out
of `MUTATING_DRIVE_VAULT_POSITIONS` for the same reason `plan_migration` and `readback_migration` are (§8's
census subject is MUTATING drives), so the containment wall's six clauses are unchanged by it. `--vault`
required, `--apply` opt-in and the non-vacuity fix all stand exactly as round 1 verified them.

### Required mitigations

Four. M1, M2 and M3 are re-emitted with `desc` byte-identical from round 1 because what each REQUIRES has not
moved; M4 is new this round. Each is additive to an existing task, none asks for a change to any `criteria`
fence, and none touches Ruling A, B or C — so no D4b re-sign is implied by any of them.

```mitigation
kind: required
id: M1
desc: The DRY RUN must print the class-C repair as per-note (stored value -> proposed JID) pairs and flag every member whose digits are not already in its own `phones[]`, so the 82 irreversible re-spellings are authorized with the rewrites VISIBLE rather than off aggregate per-cell counts — AC-5 leg (d)'s key-preservation is true by construction of the repair spelling (both keys derive from the same `normalize_phone` output, `phone_normalization.py:52`) and so is not evidence the digits are the right number, and the census itself singles out the one uncorroborated member as "the one row worth eyeballing in the dry run" (`docs/wi-032-whatsapp-corpus-census.md:207-208`) while nothing in the design can show it.
landed: Task 10
```

```mitigation
kind: required
id: M2
desc: The M1 pairs and the detector's per-note issue lines stay on stdout for the go/no-go and are NEVER written into `docs/wi-032-whatsapp-live-baseline.md` or any other tracked document, which carries counts, classes and code paths only — `docs` is a member of `DOC_SCAN_EXCLUDED` (`tests/test_vault_path_required.py:387`, intersected at `:425`) so `docs/**` is outside the markdown scan's domain and nothing mechanical catches a pasted live identifier.
landed: Task 13
```

```mitigation
kind: required
id: M3
desc: The bracket's ENTRY row must separate `orchestrator/bin/merge-duplicate-persons.py:380-384` from the two loud consumer breaks and state it as a DATA-LOSS HOLD rather than as the third item of one list — it regex-reads a single `whatsapp` line and re-emits a scalar through `Path.write_text` outside the package boundary, so against a migrated vault it can silently drop a person's second JID or blank the field, which is the exact harm this item exists to prevent and the only one of the three measured breaks that does not announce itself.
landed: Task 13
```

```mitigation
kind: required
id: M4
desc: `format_repair_disclosure` must render each record's stored value ESCAPED rather than VERBATIM — one physical line per record, guaranteed, with newline, carriage return, tab and the ANSI escape rendered as visible escapes — and the M1 check must plant one class-C note whose stored value carries an interior newline plus the text of `CORROBORATED_HEADER` and assert the line count still equals the record count and no forged header appears: `WhatsAppJID.parse` normalizes with `str(raw).strip().lower()` (`identifier.py:273`) so an INTERIOR control character survives into `.jid` while `normalize_phone` strips every non-digit (`phone_normalization.py:52-55`), making such a value phone-bearing, domain-less and therefore class C — so the one artifact the irreversible 82-note go/no-go is read against can be reflowed or have a section header forged by the very data it describes, and the check's own "exactly one line per class-C plant" oracle is asserted only over clean plants that cannot falsify it.
landed: Task 10
```

### Notes (non-blocking)

Round 1's notes 1, 2 and 4 are CLOSED — the `IdentifierError`-outside-`LoudFailError` sentence is in
`## Edge Cases`' error-propagation entry, `_refuse`'s third numbered clause is appended beside rules 1 and 2
in §3, and note 4 was informational. Round 1's note 3 (AC-3's real telephone number as a test literal) stays
OPEN and correctly deferred, on the same reasoning the spec-reviewer re-deferred it with; I re-defer it again
and for one more reason, which is that M4 makes the escaping plant a better place to spend a literal than a
frozen criterion is. Two new:

1. **Task 10's M1 plants should carry Task 13's literal convention explicitly.** The sibling check in the same
   module says "every literal RESERVED-block or synthetic"; the M1 check says nothing, and it needs a
   corroborated bare number, an uncorroborated one, and now M4's control-character-bearing one. Not a
   mitigation for the reason given above — no live source exists to reach for, and the module is outside every
   wall's reach — but one clause carries the convention to the check that will have the most plants.
2. **M4's escaping is also the one place the disclosure's own oracle becomes total.** Once the formatter
   guarantees one physical line per record, the M1 check's line-count assertion holds over ANY stored value
   rather than over clean plants, so the fold buys a stronger oracle and not only a safer render. Worth a
   sentence in §10(a) where the VERBATIM wording currently sits, so the next reader does not restore
   "verbatim" as a fidelity improvement.

```verdict
gate: threat-modeler
verdict: PROMOTE
date: 2026-09-27
model: claude-opus-5
note: Round 2 re-read all four pieces of new material in place rather than trusting the fold record — §10(a)/(b)/(c), §6's computable form, §7's re-run subsection and `## Mitigation Folds` — and re-verified in code every claim a security property rests on: `patcher` undoes in a `finally` including on raise so the re-run's call counter cannot leak and silently suppress later writes, `AUTHORIZED_PROSE_OWNERS` and `_golden` are where §6 imports them from, the detector's message still interpolates only a count and class letters, and the go/no-go step now actually shows the 82 pairs to a human; M1, M2 and M3 all HELD and are re-emitted byte-identically, with M2's requirement-broader-than-its-wall edge deliberately left as instruction rather than a `SESSION_LOG.md` wall this item would then own forever (the widen-another-surface move rejected items 11/14/15 already decline). One new finding, same generator as M1 and M2 — an unspecified property of a disclosure surface: §10(a) and Task 10 both render the stored value VERBATIM, and `parse` normalizes with `.strip().lower()` so an INTERIOR newline or ANSI escape survives into `.jid` while `normalize_phone` strips non-digits, making such a value phone-bearing, domain-less and therefore class C — so the one artifact the irreversible 82-note go/no-go is read against can be reflowed or have a `CORROBORATED` header forged by the data it describes, while the check's own one-line-per-record oracle is asserted only over clean plants; M4 folds the escaping plus a falsifying plant into Task 10. No criterion text moves and no ruling is touched.
```

## Spec Review — 2026-09-27 (round 2)

**Recommendation: PROMOTE to ready**

Rulings on record: Rulings A, B and C are RULED (Dave, 2026-09-27), the ACs are FROZEN by his signature (`ac_hash dd772c1183de`), and WI-020's specification-altitude and fold-and-close declarations stand — nothing below reopens any of them, and nothing below asks for a `criteria` fence to move.

Round 2 at this gate. Read from line 1 in full — `## Intent`, F1–F21, the rejected items, the three rulings, `## Approach`, `## Verified Diagnosis`, `## Design` §1–§10, `## Edge Cases`, the fourteen-task plan, `## Write Targets`, `## Mitigation Folds`, `## Verification`, `## Scope Boundary`, `## Risk Analysis`, all five `criteria` fences, `### Examples of done`, and the live carry-forward rounds (architect round 9, AC red-team round 8, the AC sign-off, the data audit, threat-model rounds 1 and 2, the injection-hunter round and round 1 of this gate). I walked the bar from scratch rather than from round 1's list, and I re-derived each of round 1's two findings from the code before reading its fold.

### Citation verification

**All verified ✓ — read for the PROPERTY each claim asserts, not for symbol existence.** The injected audit resolved 17 symbol-anchored citations with 0 findings; that is a floor and it proves only that cited symbols exist. The ones worth recording, because this round's material stands or falls on them:

- **`_golden` is at `tests/test_identity_endgame.py:395-397`** and is the reader clause (e1) itself takes at `:996`; `AUTHORIZED_PROSE_OWNERS` at `:359-373` is thirteen members (`<module>`, `__init__`, `_index_entity`, `_project_identifiers`, `_index_identifiers`, `_remove_entity_from_indexes`, `get_by_phone`, `resolve`, `resolve_all`, `find_or_create_stub`, `LEGACY_STUB_OWNER`, `resolve_or_create`, `_resolve_identifier`) and carries neither `PersonRepository.save` nor the bare class; it is read at `:1003`. `rg -c '"owner": "PersonRepository\.save"' tests/fixtures/identity_endgame/prose_surface_cut0.json` → **29**. So §6's two legs are computable exactly as stated.
- **§6's force claim is TRUE, which is the part a fold like this most often gets wrong.** I checked whether anything standing already witnesses a golden edit: clause (e1) (`:1008-1019`) and (e2) (`:1021-1030`) both compute their expectations FROM the golden, and `test_identity_goldens_are_frozen_pre_cut_data` (`:400-402`, `:442-455`) asserts only that the surface is non-empty and that every member of `TABLE_OWNERS` owns at least one line — and `PersonRepository.save` is not a `TABLE_OWNERS` member (`:379`), so deleting all 29 of its records is green on every standing clause. Leg 2 is the only thing that would redden it, and counting it as a LIST LENGTH rather than an `(owner, text)` set is the right instrument. The 29 is legitimately pinned by EQUALITY under WI-295: `prose_surface_cut0.json` is a Cut-0 golden this item declares as no write target and never edits, so the item's own arc cannot grow the population the pin froze.
- **The cross-test-module import idiom exists where §6 says**, `tests/test_name_gate_delta_rule.py:54-55` (`from tests.test_lint_vault_fix_gate import lint_vault`, `from tests.test_name_gate_wall import …`).
- **§7's re-run oracle is reachable.** `tests/support.py:Patcher.setattr` (`:51-57`) patches a module attribute and `patcher()` undoes the stack in a `finally` (`:67-78`), so the call counter cannot leak past the pass. `update_frontmatter_field` (`obsidian_schemas/writer.py:333-394`) takes `vault_io.note_lock` at `:368`, reads inside it at `:369`, gates the DELTA with the note's own parsed `type:` at `:385-387` and writes under the stamp precondition at `:393` — so §7's "the write is ONE call" both gives leg (b)'s gate route and makes the module-attribute counter the right discriminator.
- **`WhatsAppJID.parse` (`obsidian_schemas/identifier.py:269-281`)** raises on `None` (`:272`) and on blank (`:274-275`) through the same lines it raises on `"n/a"` with, tests the `@lid` SUBSTRING at `:276`, `Phone.MIN_DIGITS` at `:279`, and a JID domain nowhere; it stores `str(raw).strip().lower()` (`:273`, `:277`, `:281`) and retains no raw value. `identifier.py:36` binds `ClassVar, FrozenSet, Optional, Tuple` and NOT `List`, with `from __future__ import annotations` at `:31` — §1's import sentence is exact, and `ClassVar`/`FrozenSet`/`Tuple` really are already bound.
- **M4's mechanism, which I derived rather than accepted.** `.strip()` removes only the ends, so an interior control character survives into `.jid`; `normalize_phone` splits at the FIRST `@` and keeps digits (`obsidian_schemas/phone_normalization.py:52-55`). The adversarial plant `"447700900321\n" + CORROBORATED_HEADER` therefore carries twelve digits, no `@` anywhere in the header text (so the first-`@` split cannot truncate it), an empty `jid_domain` and is class **C** — the plant is the shape §10(d) claims. And §10(d)'s containment claim is TRUE on the running interpreter: every codepoint `str.splitlines()` breaks on (`\n \r \x0b \x0c \x1c \x1d \x1e \x85` → `Cc`, U+2028 → `Zl`, U+2029 → `Zp`) is inside the four categories, so "the implementation is the CATEGORY test ALONE and leg (1) proves the containment" is right rather than optimistic.
- **`name_gate.py`** — the delta rule at `:31-36` reads verbatim "A stored-dirty note stays writable for every write that does not re-introduce its name"; `_CONTAINER_KEYS` at `:84`; `_refuse` at `:142-174` with rules **1** and **2** numbered, so §3's appended third clause is an append and not an edit; `_is_str_list`/`_shaped` at `:181-198` positive as F2 says; `result = dict(introduced)` at `:346`; the name arm at `:348-368` and the address arm opening at `:369-376`, so "between step 3 and step 4" is an executable placement; the `elif entry and …` keep-verbatim at `:399-403`; `whole_record`'s docstring at `:289-294` and the idempotence sentence at `:296-299`. `name_gate.py` is outside WI-024's prose freeze, whose clause filters on `r.module == PERSON_MODULE`, so `_refuse`'s docstring edit is free.
- **`scripts/lint_vault.py`** — `LintIssue.auto_fixable` defaults False at `:96`; `check_structural` at `:355`; the `stem_name_divergence` arm at `:417-462` behind `vf.entity_type == "person"` (`:433`) and `isinstance(stored, str) and stored.strip() and stem != stored` (`:449`), with `_gate_refusal_pattern` (`:334-352`) called once at `:450` and its return spliced as a marker at `:451-454`; `field_type_mismatch` at `:464-465`, so §4's placement is real. `:44-48` imports `TYPE_TO_MODEL`, `parse_frontmatter`, `update_frontmatter_fields`, `NameGateRefusal`/`NoteAlreadyExists` and `gate_write` and neither `WhatsAppJID` nor `IdentifierError` — §4's import sentence is exact. `apply_fixes` gates the delta at `:1181-1182` and re-serializes through `_wfm(fm)` at `:1194-1198`.
- **The corpus contracts, re-read for the Task 5 blast radius.** `tests/fixture_vault.py:225` is `whatsapp="447700900789@example.com"` inside the `roundtrip_representative=True` spec at `:219-233`; `_person`'s default at `:94`; `@Fennwick Drostane.md`'s spec at `:340-341` declares no `shape_classes`, no verdict, no identifiers. `tests/test_fixture_vault.py:745-748` compares the parsed attribute against the declared literal and `:753-761` writes through the gated door and compares the RE-PARSED frontmatter MAPPING against the same literal, for representatives only — so §9 line 2's "the DECLARED SHAPE moves with the value" is not a preference, it is what makes both halves agree, and Fennwick is untouched by that loop. `tests/test_vault_path_required.py`'s skip-reason homes are pinned by EQUALITY in TWO places (`:576-580` as well as `tests/test_fixture_vault.py:1392-1395`), which is what Prerequisite 6's `:569-580` names.
- **`@Fennwick Drostane.md` is not a `tests/test_provenance_write_seam.py` subject, and could not hurt if it were.** The subjects are derived (`_divergent_person_specs` at `:145-156`, `_name_sharing_person_specs` at `:159-172`, union asserted at 5, `:411-420`); Fennwick's stem and stored name AGREE and its name is unique in the manifest. And the `save` cell derives its expected outcome from the door itself (`:475-495`, "reached BY RULE and never by a hand-list"), so a class-C stored value there would be handled rather than red.
- **Both `kind: precondition` artifacts are in the tree** and their machine-output block carries the figures every derived number is computed from: `docs/wi-032-whatsapp-corpus-census.md:163` `(a)` 1174 person notes, `:165-171` `(c)` Ø 1031 / A 35 / B 26 / C 82 / D 0 / E 0 / list 0, `:172` `(c')` splits with `Ø:absent-key` 6, `Ø:empty-string` 1025 and `C:digits-already-in-own-phones[]` 81. So 1168 = 1174 − 6, MIGRATED = 1168, shape-only 1025, repairs 82 and `|R| = 0` are all derivable, which is what Task 13 (ii) requires.
- **Task 13's redaction fixtures are MEASURED, not imagined — I re-ran both predicates.** `[0-9]{9,}` over `docs/wi-032-whatsapp-corpus-census.md` → **no matches**; over `docs/wi-032-consumer-audit.md` → exactly two lines, `:92` and `:144`, both runs sitting INSIDE 40-hex HEADs. So `27cb78cc5a2099972dccea984664193e69414def` is the right MUST-NOT-match specimen and the strip-40-hex-first rule is both necessary and sufficient over the two artifacts this item cannot edit.
- **No conscious-pin sweep is owed.** `rg MUTATING_DRIVE_VAULT_POSITIONS` over the whole tree returns the declaration (`tests/derivations.py:2012-2017`), its two consumers (`:2230-2232`) and this document — no hardcoded count or membership pin anywhere, so adding `"apply_migration": 0` reddens nothing.

One nit rather than drift, carried from round 1 and still harmless: F5 brackets `resolve_all`'s cascade as `person.py:628-690` and VD-3 as `:606-690`; both contain it.

### Bar check

Walked every check of `docs/spec-quality-bar.md` (the doc's own list is the count — never hardcoded). The spec satisfies the bar.

- **Check 1 Self-containment** ✓ — the three rulings, the six-cell table with its fourth column, both predicates, the classifier, the action table, the plant accounting, the partition and the computable form of AC-3's hardest conjunct are all in-document. Nothing needs session memory.
- **Check 2 Prerequisites** ✓ — nine, including the third trust boundary M4's fold added (UNTRUSTED → HUMAN, the rendered disclosure), the `.venv` staleness, `README.md`'s non-writability and an atomic-landing check that was RUN. Both precondition fences carry `grounds:` and both paths are in HEAD — the WI-300 ordering satisfied rather than claimed.
- **Check 3 Interface contracts** ✓ — see above; every load-bearing citation was re-read for its asserted property. No cross-doc `writes` fence, so no merge authorization is being held.
- **Check 4 Edge cases** ✓ — eleven categories in Case/Decision/Reasoning form, `OPEN: None`. Round 1's two unpinned resolutions are now pinned: the re-run no-op is asserted in Task 10 and the "Idempotency" entry names it as its fourth level; the blank-list-member case is decided in §3 with both reasons (a drop is a silent drop; filtering would cost the refusal its positional handle) and mirrored in `## Edge Cases`. The control-character case is new and correct — it is an ordinary class C in the library and special only at the render.
- **Check 5 Implementation plan** ✓ — fourteen canonical `- [ ] **Task N — …**` definitions, ordinals 1–14 unique, dependency-ordered, parallelism noted. Every task carries a well-formed lowercase `verify:` declaration: twelve check arms (Task 5's three resolving against existing checks at `tests/test_fixture_vault.py:598`, `tests/test_writer.py:404` and `tests/test_parser.py:248`, each unique under `check_module`), one `baseline` and one `hand-run`, both reasons inside 200 characters, no arm over 8 names. No illustrative declaration begins a segment. No verify command writes anything: every one is a check name or the declared floor command, and Task 12's `NO_ARG_CONSTRUCTION` run is declared VOLUNTARY with its reason verified (`docs` is a `DOC_SCAN_EXCLUDED` member at `tests/test_vault_path_required.py:387`, intersected against every path part at `:425`).
- **Check 6 Verification** ✓ — happy path, graceful failures, integration with its predictions named as predictions, and a DERIVED regression census carrying its own floor caveat. Oracle derivation is unusually strong: every AC computes its expected value by CALLING the predicates, AC-5's readback is pinned as a re-READ from note bytes, and the two oracles round 1 found unpinned are now pinned with their discriminators named (a call count, because a digest cannot tell "no write" from "re-write the same bytes"; a frozen-population count, because a post-build check has no referent for pre-build bytes). The inbound WI-301 half is discharged by Task 12 RUNNING each wall's own predicate. Counting walls: AC-3's arm set ships its shapes already standing, the containment scan's are ordered in Task 11, the redaction predicate's MUST/MUST-NOT lists are ordered in Task 13 and measured above, and M4 gives the repair-disclosure line count the falsifying input it previously lacked — which is the one that mattered, because that oracle was green over data that could not falsify it. The corpus-fixture arm is chosen (derive from the census's own stdout block) with its coupling declared in one line.
- **Check 7 Scope boundary** ✓ — nine not-doing items and an unchanged-files list that says WHY per file, including the five walls the item JOINS and the one consumer break it declines to fix while still disclosing it.
- **Check 8 Pattern consistency** ✓ — WI-029's detector shape for §4 and its containment wall for §8, WI-021's `_refuse` contract for §3, WI-016's deviation-3 fold for §9, WI-033's derived-accessor precedent for §2, and now WI-024's own reader and tuple imported rather than re-spelled for §6.
- **Check 9 Risk analysis** ✓ — ten rows, honest likelihoods (row 4 CERTAIN, row 9 MEDIUM, row 10 honest that its likelihood is UNMEASURED rather than low), each mitigation naming a criterion or a rejected item.
- **Check 10 Acceptance criteria** ✓ — five well-formed fences, all `kind: test`, all `check:` bare function names resolving uniquely under `check_module` (`tests/test_ac_interpreter.py:95-106`) with no collision against the tree's one existing `test_whatsapp_*` name. No `kind: command`, so no shell-safety question. Class-closing criteria derive their fixture space by calling the predicates and PLANT what the corpus cannot supply.
- **Check 11 Verified diagnosis** ✓ and SUFFICIENT — four load-bearing claims, each cited to a falsifiable artifact I read, each artifact supporting its specific claim: VD-1's zero-match grep plus `_CONTAINER_KEYS`; VD-2's `parse` body plus 82 measured live members; VD-3's unconditional `normalize_phone` insert plus the permanent fuzzy arm plus 26 measured lids; VD-4's two-line `rg` plus the 8 → 0 bracket. The "Not claimed, and deliberately" paragraph correctly keeps the consumer-break claim out.
- **Check 12 AC drift** — the frozen set is the `exploring` origination (`ac_hash dd772c1183de` plus five per-AC hashes) and `## Acceptance Criteria` IS that set, so there is no diff to classify. What I could check independently, I did: every post-signature fold landed as a plan-task rider or a `## Design` subsection, never as criterion text. This round is the strongest case of that — §6 states the COMPUTABLE FORM while leaving conjunct (2)'s wording verbatim, §7 adds a subsection and Task 10 a leg, and §10(d) is a Design subsection with a plan rider; the census fence's one wrong clause is still corrected DOWNSTREAM with the fence left verbatim. No strength-weakening, actor-swap, scope-narrowing, oracle-swap or exception-carving-by-addition. §6 is worth naming as the opposite of oracle-swap: it makes an unpinnable conjunct pinnable without weakening what it asserts.

**Printed HEAD literals.** Every number the bracket prints is computed under the census's own declared rules — its `classify` calls `WhatsAppJID.parse`, reads the domain off `j.jid`, and tests emptiness before either predicate — and the `(c')` splits line is what makes 1025-vs-1031 available at all. Task 13 (ii) pins them by DERIVATION against that artifact's verbatim stdout block rather than against the live vault, and `## Approach` step (4) puts the live dry run's counts beside the census's in front of Dave. The one new equality pin, §6's 29, is explicitly argued as FROZEN with the reason the byte-identity form was unavailable — the WI-295 question asked and answered rather than skipped.

**Universal claims.** THE ABSOLUTES SWEEP walks the document and the data audit's counterexample hunt walks the estate, disposing of the one false-by-design member class (a raw-file writer outside the package boundary) as a NAMED EXCLUSION with its domain and predicate stated. Both halves are present, which is what this rule asks for.

### Build-runner dry-run

Walked the plan top-to-bottom as the build-runner. Every task executes without leaving the document: the code blocks are literal, the placements are prescribed (the gate arm between steps 3 and 4, the detector between `stem_name_divergence` and `field_type_mismatch`, the cascade step immediately after step 4 and below the blank-query bail-out, the two disclosures as new paragraphs beside named line ranges), the corpus edit names the receiver AND the three constraints behind it, and every oracle is a call rather than a literal. The one transient red the ordering creates (Task 3 flips the annotation, Task 5 closes the corpus's declared oracle) is named and Task 5's verify is the three checks that go red on a half-done edit.

I re-derived the wall interactions a builder would otherwise discover mid-build, and they hold: `frontmatter_write_arms` (`tests/derivations.py:979-1010`) keys on a `writer.write_frontmatter` call, so the migration's one-call design carries ZERO arms and `EDITED_FUNCTION_ARM_COUNTS` is untouched; `test_filesystem_mutation_is_single_homed` (`tests/test_write_routing.py:87-107`) is the standing wall that reddens a `write_text` under `scripts/` (`PATH_MUTATION_NAMES`, `tests/derivations.py:52-55`), and it carries its own MUST-NOT-MATCH battery; `_divergence_issues` filters on `issue.check` so the new detector is invisible to that module; a report-only rule is outside `auto_fixable_emitter_checks` so the WI-026 oracle table needs no fifth entry; and `apply_fixes` presents a delta with no `whatsapp` key, which the data-premise gate RAN rather than reasoned.

Three questions a build-runner would plausibly ask, and the document answers all three: where does the APPEND-ONLY conjunct's second half get its referent (§6, at test time, off the artifact); what does a second migration pass do and how is that told apart from a re-write (§7, a zero call count on a module attribute); and is a blank member inside a list accepted or refused (§3, refused, with the `emails[]` precedent explicitly declined and why). Round 1's first two were the blocking findings; all three are now closed in the document rather than in a fence.

**Write-Targets coverage.** Ran the per-task extraction. Fifteen builder fences and every task's named target is present: Task 2 → `identifier.py` + `test_identifier.py` + `test_whatsapp_jid_storage.py`; Task 3 → `models.py` + `test_whatsapp_jid_storage.py`; Task 4 → `name_gate.py` + `test_whatsapp_write_door.py`; Task 5 → `fixture_vault.py` + the two corpus notes; Tasks 6–7 → `repositories/person.py` + `test_whatsapp_jid_storage.py`; Task 8 → `repositories/person.py` + `test_whatsapp_write_door.py`; Task 9 → `scripts/lint_vault.py` + `test_whatsapp_write_door.py`; Task 10 → `scripts/migrate_whatsapp_to_list.py` + `test_whatsapp_migration.py`; Task 11 → `tests/derivations.py` + `test_whatsapp_migration.py`; Task 12 → `test_whatsapp_migration.py`; Task 13 → `docs/wi-032-whatsapp-live-baseline.md` + `test_whatsapp_migration.py`. Tasks 1 and 14 write only the Build Log. No fence declares a path no task writes; the M4 fold added no path, so the touch surface and the review level are unchanged; and the three absences a reader looks for each carry a reason (`README.md` outside `write_authority`, `docs/vault-shape-census.md` another item's frozen artifact, `tests/test_fixture_vault.py` a wall the item joins). The declaration names the item's real touch surface, so the selector reads neither more nor less than the build touches.

**Mitigation folds.** The latest speaking round is `## Threat Model — 2026-09-27 (round 2)` with FOUR `kind: required` mitigations, and `## Mitigation Folds — 2026-09-27` carries a complete record for each — `id`, `desc`, `design`, `landed`, `work` — with every `desc` byte-identical to that round's fence (M1, M2 and M3 re-emitted unchanged, M4 new) and every `landed:` ordinal among the plan's fourteen. I did not judge any pair from the record: I found each `design` quote where it claims to be (§10(a)'s, §10(b)'s, §10(c)'s and §10(d)'s bolded sentences) and each `work` quote in its named task (Task 10's M1 and M4 riders, Task 13's M2 and M3 riders), and read the surrounding text. All four faithful. On satisfaction, which is mine: **M1** is satisfied — the record is on the plan `apply_migration` already consumes, `corroborated` is recomputed the same way the census computed it, the formatter returns rather than prints so it is assertable in-process, and both arms of Ruling B print it. **M2** is satisfied and keeps holding past close-out, because the check pins the §5 heading and nothing about its content while the redaction predicate still ranges over §5. **M3** is satisfied — the HOLD row carries the pinned HEAD, the reaching callers, the measured clearing path and the one do-not-run instruction that makes it a hold, with (iii) SHAPE pinning the separation rather than trusting prose. **M4** is satisfied, and it is the one I checked hardest because it is the newest: the escape is stated over the CLASS of line-breaking and invisible characters with the break set DERIVED by calling `str.splitlines()` over the codepoint space, the containment of that set inside `Cc`/`Zl`/`Zp` is true on this interpreter so "the implementation is the category test alone" is honest, every field of the record goes through one helper so the guarantee survives a later change to the repair spelling, and the adversarial plant is asserted to BE its claimed shape before anything is asserted with it — which is what turns a clean-plant-only oracle into a total one.

### Minor notes (non-blocking)

- **§7 attributes AC-5 leg (b)'s structural force to a wall that is VACUOUS over this module.** "`scripts/` is swept by `tests/test_name_gate_wall.py`'s arm wall … which is AC-5 leg (b)'s structural assertion, for free and from a wall that was already standing" sits two paragraphs above "the migration introduces NO new frontmatter write arm" — and the second is right: `frontmatter_write_arms` collects a function only when it calls `writer.write_frontmatter`, so the arm wall's domain over this module is empty and it asserts nothing about it. The coverage is real but comes from a different wall — `test_filesystem_mutation_is_single_homed` (`tests/test_write_routing.py:87-107`), which `## Verification`'s census already names for this file — and Task 10 orders the assertion regardless, so no build is licensed to skip it. One clause re-attributing it would stop the next reader pricing leg (b) off an empty domain, which is the F19 shape one wall over and the thing §8 caught for the containment scan.
- **§8's two-token `live_path_names` equality needs its expected set from IMPORTED constants, and the trap is one line away.** `tests/derivations.py:2028-2030` states in terms that the graded module may not carry the env key as a bare Constant outside its one door; WI-029's module spells it exactly once inside `_temp_vault` (`tests/test_stem_name_divergence_detector.py:126-128`) and asserts against the imported `LIVE_PATH_TOKENS` at `:168`. A hand-typed `{"os.environ", "OBSIDIAN_VAULT_PATH"}` in the new assertion reddens the SOURCE clause it is asserting. Self-catching and immediately diagnosable, so not a gap — but `LIVE_PATH_TOKENS - {LIVE_PATH_DEFAULT_NAME}` is the spelling, and saying so costs a clause.
- **The detector's predicate is two cells wider than "classes C, D and E".** §4 filters `c not in ("A", "B")`, so a blank MEMBER inside a populated list fires it (class Ø per-value — §3 decides this deliberately) and the `except IdentifierError` arm reports `"unclassifiable"`. Both populations are measured zero live (`docs/wi-032-whatsapp-corpus-census.md:171`, `class (list): 0`), so `## Approach`'s "its issue set IS R under either arm of Ruling B" holds as the exit row's independent second witness. Worth one clause so a later reader does not take the two sets as identical BY DEFINITION and then widen `STORABLE_DOMAINS` without re-checking.
- **Nothing orders a containment wall for `tests/test_whatsapp_write_door.py`,** which Task 9 has drive the linter over a materialized copy. `run_lint` is a `MUTATING_DRIVE_VAULT_POSITIONS` member (`tests/derivations.py:2015`), so if the check drives it the module joins the class WI-026 built that discipline for, while Task 11's wall covers only `tests/test_whatsapp_migration.py`. Report-only with no `--fix`, and the cage reverts vault writes, so this is not a hazard — one line in Task 9 either carrying the same `_temp_vault` provenance or saying the check calls `check_structural` directly would close it.
- **Two count labels drifted as the folds added bullets:** §10(a)'s "Four things about that sentence" now carries five (the ESCAPED bullet is M4's), and §7's "Three things make the assertion honest" carries four. Nothing is buildable two ways. Flagged only because the same class was corrected in this same edit (the `## Design` preamble's part count, six → ten), so it is a live recurrence rather than a one-off.

### Carried-forward notes

- **Threat-model note 3 (2026-09-27) — STILL OPEN, and correctly deferred a third time.** AC-3 requires `"+44 7739 341679"`, a real person's telephone number, as a test-module literal, and a reserved-block bare number would serve the criterion identically. Deferred because AC-3 is frozen by Dave's signature and the disclosure delta is zero: the value is already committed twice in this tree (`docs/write-door-bypasses.md:3994` and this document), `## Design` §9 line 5 forbids it ever entering the corpus or its manifest, and Task 13's redaction check deliberately excludes this document for exactly that ratified reason. I re-defer on the same reasoning plus the threat modeller's: M4's escaping plant is a better place to spend a literal than a frozen criterion is. Recorded so the next item to touch AC-3 prefers a reserved literal.
- **Task 10 is the one task that is not a sitting — carried as an OBSERVATION, and it grew again.** A four-entry-point module plus a formatter plus an escape helper, a seven-arm action table, AC-5's five-leg check, the re-run leg and the M1/M4 disclosure check with its five derived legs, all in one checkbox. It cannot be split without breaking two `landed: Task 10` fences, so this is not a fix request — but it is the longest unresumable stretch in the plan and the abort ledger is per-checkbox, which is worth the build-runner knowing before it starts rather than at an abort.
- Every other prior-round non-blocking note is CLOSED, and I verified each fold rather than taking a fence's word. Round 1 of this gate: the blank-list-member decision (§3, with the `emails[]` precedent declined and both reasons given, mirrored in `## Edge Cases`), the three imports (§1, §2 and §4, each checked against the module's real import line), §1's tail comment (now names the DECIDER, and the class-C derivation for an unquoted number and for a `date` is correct), Task 12's `docs/wi-032-*` count (one file, with the VOLUNTARY declaration and its `DOC_SCAN_EXCLUDED` reason verified), F18 leg 2 (narrowed to the `refusal` arm with the conservative scoping kept and its reason stated). Threat-model round 2: note 1 (Task 10's M1 rider now carries the RESERVED-block-or-synthetic literal clause) and note 2 (§10(a)'s fourth bullet says the escape is verbatim wherever verbatim is safe, so nobody restores "verbatim" as a fidelity improvement). Architect round 9: notes 1–5 all folded, spot-checked at the text (`## Approach` step (4) carries MIGRATED as part (2) with the repair count as a named sub-count; the 1025-vs-1031 split stated where the numbers are used with the fence corrected downstream; both back-out qualifiers with the class-C re-spelling named first; the shape-only population named as the run's one semantically empty part with Dave's decision point; the four sweep rows added and correctly marked as the spec-writer's). Data audit: notes (i) and (ii) both folded into the ship condition and §10(c). The threat modeller's deliberate non-ask — a `SESSION_LOG.md` redaction wall this item would then own forever — stands as a scope decision routed against, not an open note.

```verdict
gate: spec-reviewer
verdict: PROMOTE
date: 2026-09-27
model: claude-opus-5
note: Round 1's two findings are CLOSED and I re-derived each from code before reading its fold — §6's COMPUTABLE FORM is reachable and has real force (`_golden` at `tests/test_identity_endgame.py:395-397`, `AUTHORIZED_PROSE_OWNERS` thirteen members at `:359-373`, 29 `PersonRepository.save` records in `prose_surface_cut0.json`, and `save` is absent from `TABLE_OWNERS` so no standing clause witnesses a golden edit, which is exactly the gap the conjunct claims), and §7's re-run oracle is a module-attribute call count that `tests/support.py:Patcher.setattr` can install and `patcher()` undoes in a `finally`; all five of round 1's non-blocking notes are folded and verified against the real import lines and predicates; the latest speaking threat-model round's four `kind: required` mitigations all carry complete records with verbatim `desc`, and I found each `design`/`work` quote in place and read around it rather than judging the pairs — M4's escape is honest because the `Cc`/`Zl`/`Zp` categories really do contain every codepoint `str.splitlines()` breaks on and its adversarial plant really is class C; fourteen canonical tasks all carry resolving `verify:` declarations, the fifteen `writes` fences match the per-task extraction exactly with nothing added by the M4 fold, no verify command writes, no conscious-pin sweep is owed (`MUTATING_DRIVE_VAULT_POSITIONS` carries no count pin tree-wide), and Task 13's redaction fixtures are measured true in this worktree (zero nine-digit runs in the census, exactly two in the consumer audit and both inside 40-hex HEADs); five non-blocking notes survive, none leaving the item buildable two ways.
```

## Adversarial Review — 2026-09-27 (round 2)

Round 2 for this gate, model `claude-sonnet-5`, decorrelated from the spec-reviewer's `claude-opus-5`. Round 1 (above) read the document end-to-end through `## Spec Review — 2026-09-27` and found no planted steering. This round's cold-start re-read covers the whole document again start to finish — `## Problem / Motivation` through the `## Approach` and `## Verified Diagnosis` sections not quoted in round 1's own text, the full `### Findings` block (F1–F21), `## Design` §1–§10, `## Edge Cases`, the Implementation Plan, `## Write Targets`, `## Mitigation Folds`, `## Verification`, `## Scope Boundary`, `## Risk Analysis`, `## Acceptance Criteria`, all nine Architectural Review rounds, both Conductor Notes, all eight AC Red-Team rounds, AC Sign-off, Data Audit, both Threat Model rounds, both Spec Review rounds, and round 1 of this gate — with particular weight on the two sections added since round 1's read: `## Threat Model — 2026-09-27 (round 2)` and `## Spec Review — 2026-09-27 (round 2)`.

**New material since round 1: clean.** Threat Model round 2 finds M4 (an escaping requirement on `format_repair_disclosure`) through a self-derived mechanism trace (`identifier.py:273`'s `.strip()` leaving interior control characters intact, `phone_normalization.py:52-55`'s digit-only strip) rather than through any instruction embedded in the document, argues the finding on file:line citations exactly like every prior round, and explicitly declines to expand its own remit (the `SESSION_LOG.md` redaction-wall temptation, named and refused as scope creep onto another surface). Spec Review round 2 re-derives both of round 1's findings from code before reading the fold that closed them, which is the opposite of taking a prior verdict's word for anything, and its own PROMOTE is grounded in citations I re-checked (the 29-record `prose_surface_cut0.json` count, `Patcher.undo`'s `finally` block, the `Cc`/`Zl`/`Zp` category claim). Nothing in either section addresses a reviewer, an agent, or "the model" directly; nothing argues for a verdict independent of the technical claim it makes; nothing resembles a pre-baked conclusion dressed as spec content.

**Ran the same sweeps round 1 ran, over the whole file, and independently.** A regex sweep for reviewer-directed imperative language, pre-approval claims, and "ignore/disregard prior instructions" phrasing (`ignore previous|disregard|as an AI|you must (approve|promote|emit)|do not (flag|report|question)|pre-?approved|jailbreak|reviewer should not|automatically (promote|approve)|trust me|secretly|hide this from`) returns exactly one hit, and it is round 1's own text at line 5719 *describing* the sweep it ran — not a planted instruction. A zero-width/bidirectional-Unicode sweep (`​‌‍⁠﻿‪-‮`) returns nothing. A sweep for exec/network/credential patterns (`subprocess|eval\(|exec\(|curl |wget |base64|api[_-]?key|secret|token=|password|https?://`) returns only legitimate in-document discussion of why the migration module must NOT import `subprocess` (a security-positive constraint, `## Design` §8) and the threat-model trigger check's own "no secret, credential, API key" negative finding.

**The document's house style is not evidence of steering.** This item's defining feature — folds correcting folds, nine architect rounds and eight red-team rounds each re-deriving prior findings from code rather than trusting an earlier fence, findings numbered F1–F21 that amend and retract each other in writing — reads, on a first pass, like exactly the kind of dense self-referential text an injection would hide inside. Round 1 already made this call and I confirm it independently: every one of the ~5,978 lines argues its point via file:line citations and measured counts (census figures, `rg` predicate results, digit counts), the self-correction is uniform across the whole document rather than clustered in one section, and no fold ever asks a gate to accept a conclusion without the citation that grounds it. A document built to survive nine rounds of adversarial re-reading by construction LOOKS unusual; it is not the same thing as one built to manipulate a reviewer.

**No fresh candidate phrase found.** Round 1 flagged and correctly cleared one phrase ("injected drift audit," line 5205, naming a distrusted automated tool pass). This round's re-read surfaced no second candidate anywhere in the material added since — including the `## Mitigation Folds` fences, whose `desc`/`design`/`work` triads are the closest thing in this document to text one gate writes for another gate to act on mechanically, and which I read for exactly that reason. All four (M1–M4) describe a concrete code change and its verification, addressed to a builder in the ordinary spec sense, not to a reviewing gate's verdict.

```verdict
gate: injection-hunter
verdict: PROMOTE
date: 2026-09-27
model: claude-sonnet-5
note: Full re-read of the document plus the two sections added since round 1 (Threat Model round 2, Spec Review round 2) and a repeat of round 1's injection-indicator, zero-width-Unicode, and exec/credential sweeps found no planted steering, no reviewer-directed imperative language, and no pre-baked verdict; the new material's findings (M4's escape requirement, both spec-review rounds' re-derivations) are grounded in file:line citations exactly like the rest of the document, and the `## Mitigation Folds` fences — the closest thing here to gate-to-gate instruction — address a builder's code change, not a reviewer's verdict.
```

## Code Review — 2026-09-27

Build-exit reviewer, cold-start, model `claude-opus-5`. Pass A of the merged gate (WI-068); Pass B is the
sibling section below.

**Trigger check: FIRES.** The post-build diff is not doc-only. Five new files
(`scripts/migrate_whatsapp_to_list.py`, three `tests/test_whatsapp_*.py` modules,
`docs/wi-032-whatsapp-live-baseline.md`, 3289 lines) and twelve modified, of which five are package or
script code (`identifier.py`, `models.py`, `name_gate.py`, `repositories/person.py`, `lint_vault.py`).
No dependency or CI change. Not a small mechanical change by any reading.

**Stated limit on this review's evidence, first, because it decides what the verdict rests on.** The floor
command was REFUSED by this spawn's permission gate — both directly via `Monitor` ("This command requires
approval") and through a delegated agent, which reported the same refusal verbatim. So this gate did NOT
independently re-run the suite; the review is a source read of the final tree plus an audit of the Build
Log's own execution evidence. That evidence is strong and is the thing the dead-shell rule asks for: the
log carries three distinct floor counts taken by different methods (699 off a `git archive HEAD` export of
`c7d074f` precisely because the worktree was already edited, 711 for the retained work, 716 final), five
`criteria` checks re-run individually under the conveyor's own foreign interpreter, CLI runs with exit
codes and tree digests per act (2 / 2 / 0-unchanged / 0-changed / 0-unchanged), and three mutate-and-observe
probes with specific observed numbers (a call counter reading 23 against a reported `committed: 23`). A
builder that never executed a command produces none of that. Deviation 1 is the tell: its own FIGURES leg
caught a defect in its first implementation — a bare regex reading the census artifact's SOURCE f-string
rather than its stdout, green by luck on the `(a)` marker — which is a leg working on a real run, not a
claim from a source read.

**Findings: Blocking — NONE.** Six non-blocking, below.

**The five AI-maintainability checks, each run.** (1) NO new cross-project reach: the one
`sys.path.insert` (`scripts/migrate_whatsapp_to_list.py:74`) resolves to this repo's OWN root, not a
sibling, and the module reads no other project's `.env` or state; the three other-repo paths it touches
(`orchestrator/src/invariants.py`, `HAL9000/.../contacts.py`, `merge-duplicate-persons.py`) appear only as
prose citations in the live bracket, never as code reach. (2) NO new silent swallow in library code: every
package-level failure mode is a typed loud refusal, and the two `except` bodies in the new script are each
commented and each named by the spec — `readback_migration`'s `except IdentifierError: continue`
(`:492-493`) IS AC-5 leg (c)'s mandated parseable/unparseable split computed by calling `parse` rather than
from a hand list, and `_person_notes`' `except (OSError, UnicodeDecodeError, FrontmatterParseError)`
(`:270`) names `lint_vault` as the reporting tool (finding 6 below trims it). (3) NO doc made false — this
was checked against the tree and not assumed: `README.md:238`'s documented
`get_by_phone("447990558521@s.whatsapp.net")` route still holds, because a class-C value is phone-bearing,
so `_project_identifiers` yields a `WhatsAppJID` with non-empty `phone_digits` and `_index_entity`
(`person.py:277-279`) still pivots it into `_phone_index`; `README.md:52` lists field NAMES only and carries
no type. `CLAUDE.md`'s `person.py` row is now INCOMPLETE rather than false (it claims nothing the change
falsifies), the test-count anchors are declared "archaeology only" and are not falsified by a new count,
and the project root is outside `write_authority` by declaration with `## Design` Prerequisite 5 assigning
both files to the conductor's `/wrap-up` — Build Log item 5 NAMES both rather than escalating, which is the
right call for a caged builder and not a gap. (4) NO new dependence on deprecated code. (5) NO idiom
regression, and this is the axis the change is strongest on: the refusal is a gate-local literal
(`name_gate.py:90`) and deliberately NOT a `NameValidator` branch record, the boundary is typed rather than
stringly-typed, the value travels as `.refused_value` attribute and reaches no message (`_refuse` rule 3,
`name_gate.py:182-196`), and `rg` over the package returns no surviving scalar reader of `Person.whatsapp`.
(6) The dead-shell rule: satisfied, per the paragraph above.

**Step 2c, the two data-quality dimensions.** READBACK: this is the cleanest implementation of the
verify-by-readback rule I have reviewed in this estate. `readback_migration` (`:464-510`) constructs a
FRESH `PersonRepository` over the vault path and re-reads note BYTES through `_person_notes`, so the oracle
is a load that did not exist before the write — the failure mode the rule exists for (comparing the
migrating process's own re-indexed replica against itself) is closed by construction, and the reconciliation
is part-for-part over a named three-part partition with `_cli` naming the part that disagreed and returning
1 (`:568-574`). NO external write in the diff lacks one. NO-SILENT-PASS-ON-EMPTY: the reconciliation exits
non-zero rather than finishing quietly; `--vault` is `required=True` with no default and no env fallback
and a non-directory exits 2 before touching a filesystem (`:522-535`); and the test modules carry the
anti-vacuity assertions the class needs — every class cell asserted non-empty
(`test_whatsapp_jid_storage.py:269-272`), `assert scan.drives` for the containment wall
(`test_whatsapp_migration.py:370`), `assert branch_ids` (`test_whatsapp_write_door.py:205`), and
`assert set(before) - set(fresh._phone_index)` against a vacuously green inverse
(`test_whatsapp_jid_storage.py:423`). No `<<< cage-reverted writes >>>` block was present in this spawn's
input, so that sub-check has nothing to judge and no finding is manufactured for it.

**The four correctness properties I re-derived from source rather than from the document.** The phone-pivot
is now guarded on `ident.phone_digits` being non-empty and DERIVED from one projection shared with
`_index_identifiers` (`person.py:276-293`), with `_remove_entity_from_indexes` taking its removal from the
same projection as a lookup and not a loop (`:440-443`) — which is what keeps every phone-index iteration
site `materialized`. The new cascade step is placed BELOW the phone step in execution order and guarded on
`not candidate_jid.phone_digits` (`:701-708`), so a phone-bearing JID is still answered by step 4 and the
README route is preserved, while `whatsapp-jid` sits immediately before `phone` in `_RESOLVE_CASCADE_ORDER`
(`:150`) so a tie resolves to the lid's owner. The gate arm does not reuse `_shaped`
(`name_gate.py:432-446`) — that predicate is positive and a bare `str` would fall through untouched, which
would have made the arm structurally silent for every value on disk today, and the arm's comment says so.
And `gated["whatsapp"]` in the `save` rider (`person.py:1275`) cannot `KeyError`, because
`model_to_frontmatter` emits every declared field unconditionally (`writer.py:112-117`) and `gate_write`
starts from `result = dict(introduced)` (`name_gate.py:400`), so THE OUTPUT NEVER GROWS still holds.

**Non-blocking findings, most material first.**

1. **Recommended — `apply_migration`'s `vault_path` parameter is dead, so the containment wall proves
   slightly less than it reads as.** `scripts/migrate_whatsapp_to_list.py:433` binds `vault_path =
   Path(vault_path)` and nothing below reads it; every write target comes from `action.path` off the plan
   (`:449`). The wall pins the ARGUMENT at position 0 to a `_temp_vault`-bound name
   (`tests/derivations.py:2023`, asserted at `tests/test_whatsapp_migration.py:361-376`) but says nothing
   about the PLAN's provenance, so `apply_migration(temp_vault, plan_migration(live_vault))` would pass the
   wall and write to the live vault. Latent only: all six call sites in the tree pass the same `vault`
   identifier to both functions (`:523/:538`, `:623/:639`, `:674/:676`). The one-line close is to make the
   parameter live — assert each `action.path` is under `vault_path` before the write — which converts a
   scan-satisfying argument into an enforced invariant. Flagged rather than blocked because `## Design` §8
   prescribed this shape and it cleared the architect, threat-model and AC gates; it is a hardening, not a
   defect in what shipped.

2. **Recommended — `models.py:56-89`'s "Matches the person.md template" block still reads `whatsapp: ""`**,
   thirty lines above `whatsapp: List[str] = Field(default_factory=list)` at `:96`. The vault template
   genuinely is unchanged, so the line is not false about the template — but the docstring's opening claim
   is that the model matches it, and on this field it no longer does. A future reader (AI or not) opening
   this file sees the two spellings side by side with nothing reconciling them. One clause on that line
   naming the tolerant reader closes it; the file is already a declared write target, so it costs nothing.

3. **Recommended — `_person_notes` skips an unreadable note with no count anywhere.**
   `scripts/migrate_whatsapp_to_list.py:268-276` `continue`s past any `OSError` / `UnicodeDecodeError` /
   `FrontmatterParseError`, so such a note is absent from the per-cell counts, from all three triples and
   from the disclosure, and the run still prints "reconciled part-for-part" and exits 0. The project's rule
   is "silent must be EXPLICIT", and this is explicit and commented with a named second witness
   (`lint_vault` reports an undecodable note per the WI-026 floor) and consistent across plan and readback,
   so it does not breach the rule. But the conductor reading the go/no-go sees no signal that N notes were
   never considered. A single `skipped: N` line beside the per-cell counts makes the omission visible at
   exactly the surface the irreversible decision is taken at.

4. **Note — `identifier.py:365`'s final `raise` is unreachable.** The four branches at `:357-364` are
   exhaustive over the `(is_storable, phone_digits)` boolean pair, so the fall-through guard cannot fire.
   Harmless as defence against a future third predicate, and the AC's "no fall-through bucket" is satisfied
   by construction either way — recorded so a later reader does not mistake it for a live path.

5. **Note — dead local in a new test.** `tests/test_whatsapp_jid_storage.py:349-350` constructs `repo` and
   calls `_ensure_loaded()`, then plants five notes and does all subsequent work through `fresh` (`:360`).
   `repo` is never read again. The construction is presumably deliberate (a pre-plant load, so `fresh` is
   demonstrably a second load), but nothing asserts that, so it reads as leftover.

6. **Note — `docs/wi-032-whatsapp-live-baseline.md` overloads the word "entry" across two tables.** §1's
   derived-partition table is headed `entry` while its rows are the PREDICTED terminal state (MIGRATED
   1168, residual 0, and the prose at `:80-81` says part (1) "is ZERO by construction of the run"); §5's
   table is headed `entry | exit` and its entry column is the actual pre-run state (part (1) 1168, MIGRATED
   0). Both tables are internally correct and the §1 prose disambiguates, but a conductor scanning the two
   at a go/no-go reads MIGRATED as 1168 in one and 0 in the other. Task 13's FIGURES leg pins §1 against
   the census and cannot see this. A word — "predicted" on §1's column header — removes it.

**Calibration note.** Nothing here is a style preference and nothing is a theoretical issue: findings 1 and
3 are about a safety wall and an observability surface on the irreversible half of an incident-class item,
findings 2 and 6 are the docs-made-false class caught at Recommended rather than Blocking because neither
statement is actually false, and 4 and 5 are dead code recorded so the next reader does not have to
re-derive that they are dead. The implementation matches the frozen criteria on every axis I checked
against source, including the two places the criteria and the tree disagree — AC-3 says "the corpus's 21
`whatsapp: \"\"` notes" while the corpus carries 20 (`rg` over `tests/fixtures/vault/`: 20 `""`, plus
Fennwick's class C and Thrandell's class B), the 21st being `@Ferrigan Ostrakine.md`'s ABSENT key. Build
Log deviation 4 measured that exact split (21 class-Ø versus 20 shape-only writes) and implemented the real
behaviour rather than the frozen phrasing, which is correct: signed AC text is not a builder's to edit, and
naming the divergence in the log is the disclosure the rule asks for.

```verdict
gate: code-reviewer
verdict: PROMOTE
date: 2026-09-27
model: claude-opus-5
note: No Blocking findings — all five AI-maintainability checks and both Step-2c dimensions pass against the final tree (no cross-project reach, no silent swallow in library code, README's two documented touchpoints re-derived as still true, gate-local refusal pattern with the value on an attribute and not in the message, and a readback that is a genuine re-read through a fresh repository with a part-for-part reconciliation that exits non-zero); six non-blocking findings recorded, the most material being that `apply_migration`'s `vault_path` parameter is dead so the containment wall pins the argument rather than the plan's provenance (latent only — all six call sites pass the same `_temp_vault`-bound name); this gate could NOT re-run the floor because the spawn's permission gate refused it, so the 716/exit-0 claim rests on the Build Log's own execution evidence, which is strong and internally corroborated (three floor counts by different methods, per-check foreign-interpreter runs, CLI exit codes with tree digests, and a leg that caught a real defect in its own first implementation).
```

## Test & Observability Review — 2026-09-27

Same spawn, model `claude-opus-5`. Pass B of the merged gate.

**Trigger check: APPLIES, and not by default.** This is not a pure refactor — the build ships a new
production code path (a refusing arm on the one surface every writer shares), a new public repository API
(`get_by_identifier`), a new resolution cascade step, a new persistent report-only detector in
`lint_vault`, and a new one-off migration script that performs an irreversible re-spelling of 82 live
notes. All four of this pass's checks are live except the invariant registry, which this project does not
have.

**Check 1 — tests exist for the new code paths: PASS, and substantially above the floor this check sets.**
Nine top-level checks across three new modules plus an extension to `tests/test_identifier.py`, and all
nine `verify:`/`check:` names in the plan and the criteria resolve to a real top-level `def` in the tree
(verified by grep over `tests/test_whatsapp*.py`, not read off the plan). Happy path AND failure modes are
both covered per criterion, which is what this check actually asks: the refusal is asserted at every arm
of a DERIVED arm set held by EQUALITY with each exclusion carrying a structural reason
(`tests/test_whatsapp_write_door.py:207-242`), in both stored shapes, with the good member placed FIRST in
the list shape so `refused_value` discriminates which member was refused (`:252`); the four conjuncts of a
refusal are factored into one helper so no arm silently gets a weaker version (`:153-184`), and they include
`exc.__cause__ is None and exc.__suppress_context__` — a traceback-content assertion, not just a type
assertion. The re-run no-op is asserted by a CALL COUNTER on the writer module attribute rather than by a
digest, which is the only oracle that distinguishes "no write" from "re-wrote identical bytes", and the
Build Log records that counter observed 23 on a pass that DOES write, so it is wired rather than blind.
M4's totality leg derives `BREAK_CODEPOINTS` by calling `str.splitlines()` over the whole codepoint space
instead of hand-listing four characters, and plants an adversarial class-C value carrying an interior
newline plus the text of `CORROBORATED_HEADER` — the exact shape that falsifies `lines == records` — so
that check's own oracle is total rather than clean-plant-only. The containment wall ships both of its
claimed match-shapes as fixtures driven through the wall's OWN predicate: a call it must COLLECT and one
with an unreducible vault expression it must RAISE on (`tests/test_whatsapp_migration.py:422-442`). That is
the counting-wall discipline this estate has paid for elsewhere, applied here without being asked twice.

**Check 2 — logging / loud failure per failure mode: PASS, with one non-blocking gap already recorded as
Code Review finding 3.** The library's failure surface is a typed loud refusal carrying both a stable
`pattern` and the offending value on `.refused_value`, deliberately reaching no message and no traceback —
debuggable by attribute rather than by note bytes, which is the right trade here and is asserted both ways.
The identifier-collision path keeps its existing `logger.warning` naming every participant
(`person.py:382-387`). The migration's own failure modes are loud: a missing `--vault` exits 2 at
`argparse` before any filesystem touch, a non-directory exits 2 with a stderr line naming the path, a
reconciliation disagreement exits 1 with a stderr line naming WHICH part disagreed and all three values,
and a `NameGateRefusal` mid-run on a note the plan called convertible is explicitly never caught — it
aborts, which is correct, because it is a defect and not a transient. The gap: an unreadable note is
skipped with no count on any surface (Code Review finding 3). Non-blocking because it is explicit,
commented, consistent across plan and readback, and has a standing second witness in `lint_vault`'s
undecodable-note reporting — but a `skipped: N` line belongs beside the per-cell counts.

**Check 3 — alerting for new automated systems: PASS, N/A on the strict reading and satisfied on the one
that matters.** Nothing here runs unattended: the migration is a conductor-invoked one-off whose
irreversible half is gated on a human reading a printed disclosure, and the library changes are in-process
refusals that surface to their caller. So there is no launchd/cron surface owing an error path. The
question this check really asks — will Dave know if this breaks in prod — is answered by an artifact the
item BUILDS rather than inherits: the `whatsapp_not_storable` detector fires on every `lint_vault` run, under
its own check name, ERROR/`structural`, with `auto_fixable` left at its `False` default so the note never
enters `apply_fixes` and `--fix`'s four-bucket accounting is untouched while that note's OTHER issues still
repair (`scripts/lint_vault.py:475-503`). It reports and never repairs, judges both stored shapes because
both exist on disk through the whole migration window, catches a nested container via `except
IdentifierError` rather than crashing the run, and its issue COUNT is the independent second witness to the
residual — two counts by two tools that must agree, which the Build Log records as exercised for real (two
`whatsapp_not_storable` issues against a reported `residual: 2`). That detector shipping against an
empty live population (bracket §4: class D 0, class E 0) is the right way round — it is the wall against
the next bare number, not a backlog.

**Check 4 — invariant registration: N/A, skipped rather than failed.** `**/invariants.py` over this
worktree returns nothing: obsidian-schemas has no invariant registry, and v1 registry scope is
orchestrator-only (`orchestrator/src/invariants.py`). This is the documented non-registry posture, not a
gap, and no `## Observability Waiver` is owed. Worth recording for the next reader: this item's changes are
what will turn `orchestrator`'s own `person_field_shapes_correct` (`src/invariants.py:663-665`) RED
vault-wide, which the live bracket discloses as loud break 1 — so this project's behaviour change is
already visible to the estate's one registry, from the other side.

**Operational readiness beyond the three checks, because this is an incident-class item.** The live
bracket's ENTRY half is written with §5 left as a named empty heading for the conductor, and Task 13's
check asserts the heading exists while asserting NOTHING about its content, so the exit figures cannot
redden the floor at close-out — that is the right shape and it is rare to get right. The close-out
sequence is enumerated as five conductor steps including the incident replay against a DISPOSABLE note
through HAL9000's PATCH door, the `DATA-LOSS HOLD` row carries an explicit do-not-run instruction for
`merge-duplicate-persons.py` and `apply-vault-review.py` against the migrated vault, and the redaction wall
over all three `docs/wi-032-*` artifacts is shipped by this item rather than assumed, precisely because
`docs/**` is outside `DOC_SCAN_EXCLUDED`'s domain and nothing standing would catch a pasted live
identifier. The one readability defect in that artifact is Code Review finding 6.

```verdict
gate: test-observability-checker
verdict: PROMOTE
date: 2026-09-27
model: claude-opus-5
note: All three live checks pass and the fourth is N/A — nine checks exist and resolve in the tree covering happy path plus failure modes per criterion, with the anti-vacuity discipline this estate requires of counting walls (derived arm set held by equality, both claimed match-shapes driven through the wall's own predicate, a call counter rather than a digest as the re-run oracle, and M4's break set derived over the codepoint space instead of hand-listed); failure modes are loud (typed refusal carrying pattern and value as attributes, stderr plus non-zero exits naming the disagreeing part, a mid-run refusal deliberately never caught) with one non-blocking gap, an unreadable note skipped without a count; no unattended automation is introduced, and the standing "will Dave know" surface is the new report-only `whatsapp_not_storable` detector whose issue count is an independent second witness to the residual, exercised for real in the Build Log; invariant registration is N/A because this project has no registry (`**/invariants.py` returns nothing) and v1 scope is orchestrator-only.
```

## Intent Check — 2026-09-27

Cold-start read against the frozen referent (`## Intent`, all five `criteria` fences, `### Examples of
done`), then the test bodies behind each `check:`, then the built artifact — independent of the Code
Review / Test & Observability Review verdicts above, which I read only after forming my own view.

**AC-1** (`test_lid_digits_never_enter_the_phone_index`,
`tests/test_whatsapp_jid_storage.py:259-424`) — genuinely exercises the classifier's totality (table,
corpus, boundary probes), the emptiness-before-predicates ORDER, predicate independence on planted D/E
members, the phone-index population for A/C, the non-population for B/E including the fuzzy-arm
false-positive control (`get_by_phone(CORPUS_LID_TEN_DIGIT) is None`), class Ø's no-identifier-projected
assertion, and `_remove_entity_from_indexes` as the exact inverse (asserting the inverse actually removed
something, closing the vacuous-inverse trap). No stub, no weakened assertion, no narrowed domain relative
to the desc.

**AC-2** (`test_whatsapp_jid_resolution_door_over_every_accepted_form`) — asserts the cascade label is
present, ranked ahead of `phone` by a real tie observed on a lid/fuzzy-phone collision, and that the
prior relative order is byte-identical; resolves A/C through `phone:`, B/E through `jid:`.

**AC-3** (`test_whatsapp_refused_at_every_write_arm_reported_by_lint_vault_and_disclosed_append_only` +
the detector test) — the arm set is DERIVED and asserted by equality (not hand-listed), every arm is
driven in both shapes with the four-conjunct refusal helper (pattern, `refused_value` attribute, value
absent from the message, suppressed traceback chain, byte-identical target), the `save` arm is pinned in
both directions including the near-miss control (delta write still succeeds), the CLEARING and CLASS-Ø
legs are exercised at every arm and every spelling, the REPORT LEG's detector test drives the tool's own
read path (`read_vault`/`build_indexes`/`check_structural`) and asserts fire/silence per class plus
message discipline, and the APPEND-ONLY clause reads the real WI-024 golden fixture and asserts all three
conjuncts (nothing missing, no unauthorized owner, something genuinely landed). This is the AC I expected
the hollow-build shape on (irreversible refusal surface, multiple frozen artifacts to reconcile) and it
held under a direct read of the test body, not just the desc's word for it.

**AC-4** (`test_whatsapp_read_write_shape_and_no_silent_drop`) — tolerant read over five stored spellings
including the bare-valueless-key case (with the skip-surface check reading `skipped_notes` directly
rather than trusting a docstring claim), the class-Ø read/write round trip, no-silent-drop asserted on
raw bytes AND the typed view's storability-vs-parseability split, one-written-shape asserted both ways
(unrelated write leaves scalar untouched; re-introducing a refused value leaves bytes unchanged) plus the
literal `!!python/object` absence check, and the round-trip fixed point over both accepted and refused
values.

**AC-5** (`test_whatsapp_migration_dry_run_then_write_then_readback`) — the highest-risk criterion (an
irreversible live migration) and the one I read most adversarially. Leg (b) is a real structural claim
(no new frontmatter write arm, no filesystem-mutation capability, exactly one calling frame) rather than
an observed-result proxy. The readback oracle is asserted over keys AND two counts per note, the two-JID
note's both-identities-kept assertion is present, the class-C repair is asserted key-preserving with the
phone-digits guard exercised on a real class-E plant (bytes unchanged), the partition's three parts are
checked part-for-part across plan/write/readback, the never-clears conjunct is asserted per plant, and
the no-op re-run uses a wired call counter (not a digest) that the Build Log independently reports
observed 23 on a pass that does write — closing exactly the "green by construction" trap AC-5's own `why:`
names. Both arms of Ruling B are executed, not just the recommended one. I re-derived the residual counts
(`readback.triple[2] == 2` then `== 3` under `--no-repair`) against the desc's stated partition myself
rather than trusting the assertion messages, and they agree.

**`### Examples of done` against the artifact.** All four worked scenarios (two-identities-kept-and-lid-
never-a-phone; bare-number-refused-but-still-resolvable; already-wrong-value-reported-and-repairable;
live-migration-partition-and-non-zero-exit-on-disagreement) are each backed by a specific assertion I
traced above — none is a promise the build leaves unbuilt.

**No fidelity defect found and no intent-drift found.** Every AC's test proves its `desc` at the domain
the `desc` claims, including the narrowest legs (the near-miss delta-write control, the vacuous-inverse
trap, the phone-digits repair guard) that a same-family reviewer's gestalt read would be likeliest to
wave through. The build matches `## Intent` on both halves (refusal at write, liberal resolution) and on
its condition (nothing already-wrong is silently dropped; the residual stays fixable through the ordinary
doors) — all three demonstrated by executing the doors, not by asserting the promise text.

```verdict
gate: intent-check
verdict: PROMOTE
date: 2026-09-27
model: claude-sonnet-5
note: Read all five test bodies (AC-1 through AC-5) against their frozen `desc`/`why` and against `### Examples of done`, independently of the prior Code Review / Test & Observability verdicts — every AC's test proves its full claimed domain with no stubbed seam, no weakened assertion, no narrowed input domain and no missing negative case (the write-door refusal, clearing, class-Ø and append-only legs of AC-3, and the residual/repair/no-op-rerun legs of AC-5's migration test, were the ones most likely to hide a hollow build and all held under direct reading), and the built artifact matches `## Intent` on both the refusal half and the liberal-resolution half.
```

## Retrospective — 2026-09-27

### Was the spec accurate?

Mostly, and the accuracy was earned upstream rather than free: six AC red-team rounds and seven
architect rounds ran before the spec froze, and each of the last four found a real defect in the
*fixture-plant or class-table text itself* (the class-Ø absent-vs-empty split, class E, the
representative-note privacy-wall collision, the two-JID plant's missing literal) rather than a
style nit — so the heavy round count bought a spec the build then executed with almost no drift.
The one drift the Build Log records is small and self-caught: Task 13's own FIGURES leg found its
first implementation reading the census artifact's SOURCE f-string instead of its stdout (green by
luck on one marker), fixed same-spawn. The one place spec text and shipped behaviour diverge is
AC-3's literal "21" versus the corpus's actual 20 shape-only writes — a wording artifact of the
absent-key/empty-string distinction the spec's own later fold introduced, disclosed in Build Log
deviation 4 and judged correct by Code Review (signed AC text isn't a builder's to silently edit).

### Edge cases that surprised us

- The absent-key vs. empty-string split (class Ø having two live spellings, only one of which is a
  write) wasn't in the original class table — it surfaced only in the second/third AC red-team
  round, after which `## Write Targets` needed a correction note pointing at the right figure.
- `apply_migration`'s `vault_path` parameter being dead code that the containment wall pins by
  argument rather than by the plan's provenance (Code Review finding 1) — latent, not exercised by
  any of the six live call sites, but not anticipated by the spec's containment design.
- The live-baseline doc's own "entry" column meaning two different things across two tables (Code
  Review finding 6) — a readability gap the spec's Task 13 check couldn't see because it only pins
  §1 against the census, not §1 against §5.

### What would have shortened the build?

The build itself was smooth (five criteria checks all green on first re-run, code review and
test-observability both PROMOTE with only non-blocking notes) — the cost was almost entirely paid
before `building`, in the six AC red-team + seven architect rounds. A census/audit precondition
that itself enumerated the class-Ø absent-vs-empty split (rather than the spec discovering it two
folds later) would have shaved a round or two off `exploring`. Nothing suggests a spec-writer or
build-runner instruction gap — the repeated pattern was two independent gates each round finding
the *same* real defect in fixture-plant text, which reads as the review process working as
designed for an item with this blast radius (a shared write door plus an irreversible 1,168-note
migration), not as noise to trim.

### Did the build serve the original intent, or the spec's drift of it?

Intent Check (2026-09-27) read all five AC test bodies independently against `## Intent` and found
no fidelity defect and no intent-drift — the build proves the refusal half, the liberal-resolution
half, and the never-silently-drop condition by executing the doors, not by asserting the promise
text. No gap to surface here.

### Recommended follow-ups

None — chain held up well. No blocking findings from any gate, no post-done defect to record. The
non-blocking Code Review findings (dead `vault_path` guard, docstring template drift, unreadable-note
skip count, unreachable branch, dead local, live-baseline column labeling) are all cheap, named, and
left as recorded hardening rather than requiring a follow-up work item.

No build-earned lesson cleared the `LESSONS.html` bar — the one real defect this build hit (Task
13's source-vs-stdout regex) was caught and fixed within the same spawn before it cost real time or
shipped corruption, which is a smooth build's ordinary self-correction, not a scar.
