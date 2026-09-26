---
id: WI-032
title: Validate the WhatsApp JID shape at the person boundary
project: obsidian-schemas
stage: idea
created: 2026-09-21
last_touched: 2026-09-26
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

A WhatsApp identifier that is not a WhatsApp JID never reaches a person note. "A JID" means it
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
  `.is_storable`. The SPELLING is the spec-writer's; the closed-set READING is not. **An earlier draft
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

| class | predicate result | exemplar |
|---|---|---|
| **Ø** | introduces NO identifier — not a parse outcome; classified before `parse` is called, and ACCEPTED at every write arm | key absent, `""`, `None` |
| **A** | parses, `phone_digits` non-empty, storable | `447700900123@s.whatsapp.net` |
| **B** | parses, `phone_digits == ""`, storable | `<digits>@lid` |
| **C** | parses, `phone_digits` non-empty, NOT storable — the Kim Faura class | `"+44 7739 341679"`, `447700900789@example.com` |
| **D** | NON-EMPTY and does not parse | `"n/a"`, `"ask Kate"`, `"notaphone@s.whatsapp.net"` |
| **E** | parses via the `@lid` SUBSTRING, `phone_digits == ""`, NOT storable | `447700900456@lid.example.com` (the red-team's minimal form is `123@lid.example.com`) |

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

The exemplar the plants use is the PHONE-DIGIT-BEARING variant `447700900456@lid.example.com` rather
than the red-team's minimal `123@lid.example.com`, deliberately: both are class E, but only the first
discriminates "took the `@lid` branch" from "fell through to `normalize_phone`" — the short form carries
fewer than `Phone.MIN_DIGITS` digits before the `@`, so a build that lost the `@lid` branch entirely
raises on it and would look correct for the wrong reason, while the long form silently acquires a phone
key. E's behaviour is fully determined by the
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
(`tests/fixture_vault.py:21-25`, `:44`) and, if the plant declares a new class, a census row
(`tests/fixture_vault.py:70-71`). That cost is the spec-writer's choice against an inline temp-vault
note, not an open question for Dave.
**AMENDED by F12 — and the news is good.** Re-read against the class table, Thrandell's
`447700900789@example.com` is not "an accepted value whose domain is irrelevant" but a class **C**
member: it parses, it is phone-bearing, and it carries no JID domain (its `jid_domain` is
`"example.com"`, not in the closed set). The frozen corpus therefore already supplies the Kim Faura
class for free. E is the plant the WI-286 rule most obviously demands, because its live population is
expected to be zero and a corpus-trusting test would therefore never see the cell at all. The plant must
KEEP Thrandell's value rather than tidy it — it is the discriminating member.
**AMENDED AGAIN, with the class-Ø fold, and this time it corrects a COUNT rather than a reading.** The
plant list this finding carried (B, D, E) was short by one and long by none: the 22 matching lines are 21
`whatsapp: ""` plus Thrandell's single non-empty value, so the corpus supplies class **Ø** (21 members,
no plant needed — it is the corpus's dominant cell and the reason F16 exists) and class **C** (one
member, Thrandell) and supplies NO member of A, B, D or E. Class **A** — a storable phone-bearing JID,
`447700900123@s.whatsapp.net` — has no corpus member either, which the earlier list missed because it
read the corpus for `@lid` and for unparseables and not for the happy path. So the plant list is
**A, B, D and E**: four raw values, with Ø and C free. AC-1 asserts every cell non-empty, so a missing
class-A plant is RED rather than silent — but it is cheaper to list it here than to find it in a build.
Predicate, re-run for this fold: `rg -n -i 'whatsapp' tests/fixtures/vault` → 22 lines, enumerated above.
One consequence to check
at build time rather than assert here: after Ruling A,
`PersonRepository.save(<Thrandell>)` REFUSES (F13), so any existing test that round-trips a fixture
person through `save` needs re-reading. The granted tools here are Read/Grep/Glob with no shell, so
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
confirm (`yaml.dump({"whatsapp": [WhatsAppJID.parse("447700900123@s.whatsapp.net")]})`) which the spec
should do before Task 1 rather than after.
**AMENDED by F13: the projection task is DELETED from scope.** Keeping the stored field `List[str]`
means nothing dataclass-shaped is ever in `model_fields`, so there is nothing for `writer.py` to
project and the hazard is closed by construction rather than by a step that could be forgotten. The
assertion survives anyway as a cheap guard (AC-4 leg (b): no `!!python/object` tag anywhere in the
written bytes), because it catches the mistake whichever way an implementation goes — and it is now
the ONLY thing standing between a future "let's annotate it properly" change and unreadable notes.

**F9 — The linter's report surface comes free, with one condition.** `lint_vault._gate_refusal_pattern`
runs the door over a note's WHOLE stored record purely to REPORT its refusal pattern
(`scripts/lint_vault.py:334-352`), while `apply_fixes` gates only the DELTA (`whole_record=False`,
`:1181`). So a refusing whatsapp arm gives the linter a report path over the live corpus with no new
detector, AND does not make a malformed-JID note unfixable — PROVIDED the refusal carries its own
`pattern` value, so a bad JID is never reported as a bad name.

**F10 — Where the structure lives (the Phase-3 question).** The bridge store holds both a phone-JID and
an `@lid` for the same person; the note holds one string. The structure is discarded at the WRITE seam
by whatever sync collapses two identifiers into a scalar — not at read time. So the first task is the
field's cardinality and the write door, and there is no read-time reconstruction to design. That is
also why the WI-035 lid→phone pivot (`identifier.py:24-25`) is NOT this item's mechanism: the pivot
exists to recover a phone the note never stored, and the fix is to store both.

**F11 — `PersonRepository.save` has a rider that must grow one line, and it is caller-visible.** The
rider writes the gate's normalized containers back onto the model (`person.py:1190-1194`,
`entity.emails`/`phones`/`aliases`). A gated `whatsapp` needs the same write-back, which is a NEW
in-place mutation a caller holding a `Person` will observe — the same class of disclosure WI-021 made
for `phones[]` (`person.py:1180-1184`). Also `_remove_entity_from_indexes` (`person.py:412-416`) mirrors
the defective index insert and moves with it.
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
  data loss, on exactly the population this item exists for, and it also destroys the evidence F9's
  linter report path is meant to surface. Unacceptable, and not a thing to discover from a build.
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
   whose domain is not a real JID domain, both reported by the linter and left for hand repair. The hand
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
  refusing the empty value). (3) The migration REPAIRS class C key-preservingly
  (`"+44 7739 341679"` → `"447739341679@s.whatsapp.net"`,
  same `phone:` key) and repairs ONLY phone-bearing values, which is what reduces the refusal population
  to class D plus class E — non-empty digit-less junk plus (expected zero) `@lid`-substring values with a
  non-JID domain — and keeps (2) affordable.
- **What going the other way costs.** Keeping a literal `list[WhatsAppJID]` annotation means either
  erasure (unacceptable) or a union type the YAML writer then has to special-case — F8's hazard back
  from the dead. Declining part (3) is defensible: it means the migration only REPORTS class C and N
  notes stay unsaveable until hand repair, where N is the census's class-C count. That is a
  do-I-want-my-values-rewritten question, so it is Dave's.

#### Ruling C — scope (unchanged from the previous round)

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
  accessor — Ruling B), `name_gate.py` (the arm), `repositories/person.py` (`_index_entity`,
  `_remove_entity_from_indexes`, `_project_identifiers`, `resolve_all` + `_RESOLVE_CASCADE_ORDER` at
  `:145`, the public `get_by_identifier`, the `save` rider), `scripts/lint_vault.py` (pattern routing
  only), `README.md:52` and `:238`, `tests/test_identity_index.py` (its `_note` helper writes
  `whatsapp:` as a scalar, and `:80`'s premise per F12), `tests/test_repositories.py:33` (same),
  `tests/test_identifier.py:119-143` (the `WhatsAppJID` block gains the storable predicate),
  `tests/fixture_vault.py:94` (added with the class-Ø fold, round-3 note 4: the frozen corpus's declared
  person oracle hand-transcribes `models.py`'s defaults including `whatsapp: ""`, and that default becomes
  `[]` — machinery that moves with the field rather than a plant, and easy to miss because it is not in
  `obsidian_schemas/`), plus a
  migration entry point, the fixture plant (classes A, B, D and E — Ø and C come free, F6 as re-counted)
  and `docs/wi-032-whatsapp-live-baseline.md` for the bracketed live run. `writer.py` is OFF the list —
  F8's projection is deleted by F13 leg 1.

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
bad JID is never routed as a bad name (F9).

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
reconcile across dry run, write and readback or the run exits non-zero. This is WI-010's un-park
criterion, met once, properly.

**And the live run is a SHIP CONDITION, not effort** (round-2 note 4, carried through round 3, folded
here). A migration whose only acceptance is the corpus it was written against is a specimen in a jar:
AC-5 is hermetic by necessity and the census is the audit-before-patching half, but the item ships against
the real vault, in WI-029's exact shape — entry numbers committed to
`docs/wi-032-whatsapp-live-baseline.md`, the dry run read and shown to Dave, his go, the write, then exit
numbers in the same doc's §5 (`docs/stem-divergence-live-baseline.md` is the precedent to copy literally).
The exit numbers that matter: zero notes left in the scalar shape, the class-C repair count equal to the
census's class-C row, the D+E residual reported and byte-identical, and the identifier-key multiset
unchanged corpus-wide.

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
why: AC-3 makes the door refuse a value the STORABLE predicate rejects and AC-5 migrates and repairs every stored value, so both rest on a population nobody has measured for this field. The closest committed figure (`docs/identity-cutover-corpus-audit.md:132`) is dated 2026-09-06, pools `phones` with `whatsapp`, and counts no `@lid`. REVISED THIS ROUND - the earlier version of this line asked for "values `WhatsAppJID.parse` REFUSES", which F12 shows is the wrong population, since that parser accepts a bare phone number and so refuses only digit-less junk. Needed, counts only and no live identifier, one row per cell of the SIX-cell class table in `## Exploration Notes` - class Ø, the notes with no `whatsapp` identifier at all (an absent key, `""` or `None`), which the write door ALWAYS accepts and which is the corpus's dominant cell (21 of the 22 `whatsapp`-carrying fixture notes, F6) so its count is the denominator the other five rows are read against, and which is also the count of notes the migration converts SHAPE-ONLY; class A, a storable phone-bearing JID; class B, a storable `@lid`; class C, parses and is phone-bearing but carries no JID domain from the closed set (this is the Kim Faura population and the number that decides whether the door's refusal needs the migration's repair pass first, so it is the load-bearing row); class D, NON-EMPTY and does not parse at all - the emptiness carve-out matters to this row specifically, because `WhatsAppJID.parse` raises on `""` and `None` through the same lines it raises on `"n/a"` (`identifier.py:271-275`), so a census that files every raising value as D would report ~the whole corpus as a defect population and misprice Ruling B leg 2 by three orders of magnitude; class E, added this round, contains the `@lid` substring but its domain after the last `@` is not in the closed set, so it parses with empty `phone_digits` and is not storable (`123@lid.example.com` shape) - D and E TOGETHER are the residual population for which `PersonRepository.save` will refuse after the migration, since neither is repairable, so they are the rows that price Ruling B leg 2 and E is expected to be ZERO, which is itself the answer worth having on paper rather than assumed. Plus the count of people the bridge store shows holding more than one JID (the premise paragraph's 51, re-measured) and the count of lids whose digits `phones_match` would tie to a stored phone (the false-positive population the resolution fix retires). Privacy wall and shape precedent - `docs/stem-divergence-live-baseline.md`.
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

```criteria
id: AC-1
desc: A JID's digits enter `_phone_index` IF AND ONLY IF `WhatsAppJID.parse` gives it a non-empty `phone_digits`, and the discriminating member is PLANTED rather than hoped for. The fixture space is a table of raw values the test classifies BY CALLING the two predicates of `## Exploration Notes` - `WhatsAppJID.parse` and the STORABLE property - yielding the SIX cells of that table: Ø (introduces NO identifier - an absent key, `""` or `None` - filed BEFORE either predicate is called), plus the five classes of a NON-EMPTY value, A (parses, phone-bearing, storable), B (parses, `@lid`, `phone_digits == ""`, storable), C (parses, phone-bearing, NOT storable), D (NON-EMPTY and does not parse) and E (parses via the `@lid` SUBSTRING, `phone_digits == ""`, NOT storable - the `447700900456@lid.example.com` shape, whose `jid_domain` is `lid.example.com` and so is not in the closed set), with each cell asserted non-empty so a cell that loses its only member is RED rather than vacuously green. The classification ORDER is asserted, not merely the classification - an emptiness test precedes both predicate calls, proven by the classifier filing `""` and `None` as Ø rather than as D, because `WhatsAppJID.parse` raises on them through the same two lines it raises on `"n/a"` with (`identifier.py:271-275`, no blank branch) and so a classifier that asks the predicates first files the corpus's dominant value as a defect class (F16). The EXHAUSTIVENESS claim is stated at the reach it actually has, which is the correction the previous round made - the classifier is a TOTAL function with NO fall-through bucket, so a raw value matching no declared cell RAISES rather than being silently filed, and it is asserted total over (i) the enumerated raw-value table, (ii) every `whatsapp` value in the fixture corpus, classified without exception, and (iii) a named boundary-probe list that includes `447700900456@lid.example.com`, `123@lid.example.com`, `notaphone@s.whatsapp.net`, `447700900789@example.com`, the bare `"+44 7739 341679"`, and - added with class Ø - `""`, `None`, a whitespace-only `"   "` and an absent key. It is NOT claimed over every string in the language - that was the four-cell table's false promise, and class E was the counterexample: it parsed, carried no phone digits and was not storable, so it belonged to no cell while every planted exemplar still went green. Per member the oracle is the predicate results themselves, never a restated shape. Classes A and C, the index key is exactly `phone_digits` and `get_by_phone(<that number>)` returns this person - C is in the phone arm deliberately, because a bare number in the field IS a stored phone number and resolution stays liberal (F12), and the test states that as the expected answer rather than leaving it to inference. Classes B and E, NO key derived from the value's digits exists in `_phone_index` at all, and the falsifying member is planted and named - a lid whose digits are an 11-digit string beginning with `1` on a vault where NOBODY holds the corresponding 10-digit number, for which `get_by_phone(<the 10-digit form>)` must return None (today it returns the lid's owner, via the permanent fuzzy arm at `person.py:494-496`). E is planted with its digits in the ≥ `Phone.MIN_DIGITS` range for the same reason, so a build that lost the `@lid` branch and fell through to `normalize_phone` produces a phone key and is RED rather than raising for an unrelated reason. Class D, the NARROWING arm - there is no right phone for a value the parser refuses, so the assertion is the declared marker - no `_phone_index` entry, no exception out of the load, and the note still loads. Class Ø, the same NARROWING arm and for the same reason, plus one more assertion that distinguishes it from D - no `_phone_index` entry, no `jid:` entry, NO identifier of any kind projected from the field (the `_project_identifiers` output for that note carries no `whatsapp_jid` member at all), and the note loads clean; a build that filed Ø as D would satisfy the no-key half and fail nothing else in this criterion, which is why the no-identifier-projected half is stated. The two predicates are asserted INDEPENDENT in BOTH directions on planted members - `notaphone@s.whatsapp.net` carries a JID domain and is class D, and class E parses while carrying a domain that is not one - so a build that implemented storability as "parses", or parsing as "has a suffix", or storability as "contains `@lid`", is RED. `_remove_entity_from_indexes` is asserted to be the exact inverse over the same table, so a refresh leaves no orphan key.
why: A lid is an opaque WhatsApp-internal id, so indexing its digits as a telephone number invents an identity claim the data never made, and `phones_match`'s US arm turns that into a false-positive answer for a number nobody has - the corruption shape with a real victim. The class table is derived by CALLING the type rather than hand-listed, so widening the storable domain set or adding a third accepted parse form later joins the sweep automatically. The plants are required because the frozen corpus has zero `@lid`, zero unparseable and zero storable-JID members and would green a build that changed nothing - the plant list is A, B, D and E, since the corpus supplies Ø (21 notes) and C (`@Thrandell Ibberly.md:7`) for free (F6, re-counted this round: 22 matching lines, 21 of them `whatsapp: ""`). The ORDER assertion is new and is the cheapest line in the criterion: absence is not malformation, every other part of the library already draws that line before parsing (`person.py:318-320`), and a build that draws it after refuses the model's own default at every dict door while passing every other leg here (F16). The independence assertion exists because conflating the two predicates is the cheapest wrong build available and every other leg of this criterion would still pass. The exhaustiveness wording is scoped rather than universal because the universal version was FALSE as written - class E is a real input with no cell in the four-cell table - and a criterion that claims a totality its predicate table cannot deliver is the same defect one level up from the thing it is guarding: the no-fall-through classifier is what converts a future sixth shape from a silent mis-file into a failing test, which is the strongest honest form of the claim.
check: test_lid_digits_never_enter_the_phone_index
kind: test
```

```criteria
id: AC-2
desc: Every PARSEABLE JID form has exactly ONE public resolution door and the answer is the person carrying it. Over the same derived SIX-cell table as AC-1, a public `get_by_identifier(Identifier)` and the `resolve`/`resolve_all` cascade both answer, with the expected entity computed from `WhatsAppJID.parse(v).key` plus the fixture's own note-to-value map. Classes A and C resolve to their note through the `phone:` key, unifying with a bare `phones[]` entry for the same number exactly as `tests/test_identity_index.py` already pins - class C is asserted to RESOLVE even though AC-3 refuses to STORE it, which is the reach-versus-storable split made executable, and a build that made resolution strict is RED here. Classes B and E resolve to their note through the `jid:<value>` key the index ALREADY builds (`person.py:330-331`) - today the same query answers None or, worse, the wrong person. E is named alongside B rather than treated as a refusal case, because resolution keys on `parse` and E parses: a build that wired the STORABLE predicate into the resolver makes E (and C) unresolvable and is RED on this leg, which is the same reach-versus-storable split the class-C clause pins from the phone side. Classes D and Ø take the NARROWING arm - None, no exception, and no candidate above the cascade's noise floor; for Ø the query is not constructible as a typed `Identifier` at all (`WhatsAppJID.parse("")` raises), so the leg is stated over the CASCADE with a blank query string and asserts it neither raises nor returns a person who merely has an empty `whatsapp:` field - which 21 of 22 fixture notes do, making a blank query the one input that could match ~the whole corpus if the step compared stored values instead of keys. Three guards - the lid answer is asserted to come from the identifier index and NOT from a phone lookup (a build that resolved lids by re-normalizing digits is RED); the new cascade label is asserted PRESENT in `_RESOLVE_CASCADE_ORDER` (`person.py:145`) and ranked ahead of `phone`, proven by a tie between a lid hit and a fuzzy phone hit resolving to the lid's owner (an unranked label sorts last at `person.py:190-197`, so omitting it is silently wrong); and `README.md:238`'s documented behaviour of looking a phone-bearing JID up through `get_by_phone` still holds, so the fix does not silently retract a published API.
why: The index is already right and nothing public reads it - the gap is a door, not data (F5), and a resolution step is the half of the Intent the mint left implicit. Asserting WHERE the lid answer comes from is what stops the cheap wrong build - re-normalizing a lid's digits in the resolver would green an answer-shaped test while preserving exactly the phone-confusion AC-1 removes. Class C is asserted resolvable because the one real risk of adding a storable predicate is that someone wires it into the resolver too, which would break lookups that work today (F12), and the cascade-label guard is here because it is one line, invisible when wrong, and produces a wrong ANSWER rather than an error.
check: test_whatsapp_jid_resolution_door_over_every_accepted_form
kind: test
```

```criteria
id: AC-3
desc: Every write arm that can introduce a `whatsapp` value refuses a NON-EMPTY value that is not STORABLE - classes C, D and E, so the refused set is defined by the STORABLE predicate over the non-empty values, never by "does not parse" and never over the absence case - in BOTH shapes, with nothing written. The refused population is NON-EMPTY by construction and this is a scoping clause rather than a softening one: class Ø (an absent key, `""`, `None`, whitespace-only) introduces no identifier, is never judged by either predicate, and is ACCEPTED at every arm, which leg (v) pins - `WhatsAppJID.parse` raises on `""` and `None` through the same lines it raises on `"n/a"` with (`identifier.py:271-275`), so a door built to refuse "everything the parser refuses" refuses the model's own default (`models.py:94`) and the corpus's dominant value at every dict door (F16). The arm set is DERIVED from the tree by the existing WI-021 sweep in `tests/derivations.py` (never hand-listed), asserted in scope by EQUALITY, with any arm that cannot introduce the field excluded for a stated structural reason, PLUS one arm the derivation cannot supply - `PersonRepository.save`, which the WI-021 wall deliberately excludes as a rider (`person.py:1162-1163`) and whose gate call runs over a WHOLE-RECORD PROJECTION (`person.py:1190-1191`); the derived set already contains the OTHER whole-record-projection arm, the exported `write_markdown_file(entity=…)` (`writer.py:229-233`, which `BaseRepository.save` delegates into at `base.py:462-465`), and the criterion names it so the two are pinned as ONE class of arm rather than as `save` plus an accident - `whole_record` is not the discriminant, the payload containing the key is (`name_gate.py:289-294`). Per arm, two shapes - a bare scalar `str` (the shape every live caller uses and the shape `_shaped` passes through untouched today - F2) and a list containing one bad member among good ones. Per arm, three conjuncts - (1) REFUSED with a leaf of `LoudFailError` carrying the offending raw value as an ATTRIBUTE and NOT in its message, and carrying its own stable `pattern` value distinct from every `NameValidator` pattern; (2) the target note is byte-identical afterwards, and a target that did not exist is not created; (3) a storable value in the same payload is accepted and stored in the list shape. `"+44 7739 341679"` is named as a REQUIRED class-C member at every arm, because it is the value the item was minted for and the value a parse-only door accepts, and `447700900456@lid.example.com` is a REQUIRED class-E member at every arm, because it is the value a door that asked "contains `@lid`?" instead of "is the domain in the closed set?" would accept. The `save` arm is pinned in BOTH directions over an entity loaded from a note whose STORED value is class C, D or E - (i) `save()` REFUSES with that same pattern and the note is byte-identical, and (ii) the value is STILL PRESENT on the model and in the note afterwards, never silently emptied, which is the assertion an erasing build fails while passing every other leg here. Plus the near-miss control - the same note stays writable through a delta arm for a write that does not re-introduce the field (the delta-not-record rule, `name_gate.py:31-36`), so the remedy is not the disease, and that asymmetry between the whole-record arms and the delta arms is asserted rather than assumed. THE CLEARING LEG, which is the one this round adds and the one that makes the design's own repair promise buildable - over a note whose STORED value is class C, D or E, CLEARING the field SUCCEEDS through the delta arms in both of the package's spellings, `update_frontmatter_field(path, "whatsapp", "")` and `update_fields(person, {"whatsapp": None})`, with the note afterwards carrying the empty collection and the unstorable value GONE because a caller asked for it to go; asserted at every delta arm, not just one, because there is no delete or remove affordance anywhere in the writer (`writer.py:333-337` sets a value) and so this IS the hand-repair path Ruling B leg 2 and AC-5 leg (e) commit to for the D+E residual. THE CLASS-Ø LEG - at every arm in the derived set, in every spelling (absent key, `""`, `None`, whitespace-only, `[]`) and in both shapes, a write carrying class Ø is ACCEPTED, the note is written, and nothing is refused; a build that refuses blank fails here and nowhere else in this set, which is exactly why the leg exists. And one consequence pinned where it is free - `lint_vault` REPORTS such a note through `_gate_refusal_pattern` under that distinct pattern, and `--fix` still repairs the note's other issues.
why: The Intent's "every writer refuses it at the boundary" is only true if the refusal sits on the surface all writers share - a field type cannot see `update_frontmatter_field(path, "whatsapp", "+44 7739 341679")`, which is legal today (F1, `docs/write-door-bypasses.md:3993`) - and it is only true of the value that MOTIVATED the item if the door asks the storable question, since `WhatsAppJID.parse` accepts that exact string (F12). Both shapes are required because an arm copied from `emails`/`phones` is silent for scalars and every live value is a scalar. `save` must be named explicitly because the derivation that proves no arm routes around the gate excludes it by design, and it is an arm where a value the note already stores is re-introduced and therefore judged (F13) - the build that ships an erasing reader is green on every other criterion in this set; naming `write_markdown_file(entity=…)` alongside it is what keeps the disclosure honest, since the refusal surface is "re-serializing a whole stored person record", not one method (F11's correction). The attribute-not-message rule is the WI-021 refusal contract (`name_gate.py:142-174`) and the way to honour "naming the value" without rendering note bytes in tracebacks (F4). A distinct `pattern` is what keeps a bad JID from being reported and routed as a bad name (F9). The CLEARING and CLASS-Ø legs are the round's material addition and neither is defensive padding: refusing class Ø is a SELF-CONSISTENT build that passes every other leg here and every leg of AC-4 and AC-5, because the entity path never hands the gate a literal `""` (the `[]` default has no member to judge) and no drafted member was blank - so two honest implementers reading the earlier text diverged on whether writing `""` succeeds, and the losing one bricked the only repair channel the residual population has while breaking every producer that clears the field (F16). The legs are stated at EVERY delta arm rather than one because the repair is done by whichever door the repairer happens to hold.
check: test_whatsapp_refusal_at_every_derived_write_arm
kind: test
```

```criteria
id: AC-4
desc: Both stored shapes load, nothing stored is dropped, exactly one shape is written, and nothing dataclass-shaped reaches YAML. Four legs, over every cell of AC-1's SIX-cell table. (a) TOLERANT READ - a note carrying `whatsapp: "<value>"` and a note carrying `whatsapp: ["<value>"]` both load with NO `SchemaDriftError` and present the same field value; a note with an empty value and a note with the key absent both present the empty collection - that is class Ø on the READ side, and it is the SAME rule AC-3's CLASS-Ø leg states on the WRITE side, asserted as one rule over one cell rather than as a read-side convenience: the leg is stated so that a build accepting empty on read while refusing it on write fails HERE too (the round-3 and red-team-round-2 contradiction, F16), by round-tripping the empty note through a gated delta write and back. (b) NO SILENT DROP - for every NON-STORABLE member (classes C, D and E) the RAW stored string is still present on the loaded model, asserted by equality against the note's bytes, and the derived typed accessor exposes the PARSEABLE members only (so class D appears in the raw field and not in the typed view, while classes C and E appear in both - they parse, they are merely unstorable, and a build that filtered the typed view on STORABILITY instead of on parseability is RED here) - a reader that filtered unparseable values out of the stored field fails too, and this is the leg that makes AC-3's `save` arm reachable at all. (c) ONE WRITTEN SHAPE - after any gated write the note's bytes carry the LIST form, re-`yaml.safe_load` cleanly, and contain no `!!python/object` tag anywhere; a scalar-carrying note written for an unrelated reason is NOT silently rewritten unless the write introduces the field (delta rule). (d) ROUND TRIP - load, save, load again is a fixed point on the field for every member the door accepts, so a second save produces byte-identical frontmatter (the idempotence the gate already requires of itself); for members the door refuses, the fixed point is AC-3's refusal with the bytes unchanged.
why: The vault is shared mutable state, so the reader must accept both shapes for as long as any consumer may be running older code - and an un-migrated note does not merely look odd, it raises `SchemaDriftError` and lands on the load skip surface, invisible to every consumer (F7, F14). Leg (b) is the anti-erasure wall and it is new this round - a literal `list[WhatsAppJID]` annotation cannot hold a value the type refuses, so the natural build drops it, and since `model_to_frontmatter` emits every declared field unconditionally the next `save()` writes the drop back to disk (F13). Asserting the raw string survives is what makes that build RED before it reaches the live vault. Leg (c) exists because `model_to_frontmatter` hands field values straight to `yaml.dump` with the default `Dumper` while the reader is `yaml.safe_load` (F8) - a typed object in `model_fields` would write notes this package cannot read, and "no `!!python/object` in the bytes" is the one assertion that catches it whichever way the implementation goes. Leg (a)'s class-Ø round trip is the cross-check the earlier draft lacked: the read side already said empty means absence and the write side said empty is refused, and because the entity path never constructs a literal `""` for the gate to judge, NOTHING in the suite made the two sides meet - which is how a build could satisfy both sentences at once and still be wrong.
check: test_whatsapp_read_write_shape_and_no_silent_drop
kind: test
```

```criteria
id: AC-5
desc: The migration is a dry run, then a gated write, then a readback - and it proves no identifier moved. Driven in tests against a COPY of the fixture corpus, planted with at least one note per NON-Ø cell of AC-1's table - A, B, C, D and E - plus one note carrying TWO JIDs (a phone-bearing one and an `@lid`); class Ø needs no plant, the corpus's own 21 `whatsapp: ""` notes being its members and the population the migration converts SHAPE-ONLY. All of it under the containment wall that proves the module drives only a temp vault (`tests/derivations.py:mutating_drive_vault_args`). Five legs. (a) DRY RUN - reports counts per cell of AC-1's table and leaves the tree byte-identical, asserted by a digest over the materialized tree before and after. (b) WRITE - every write goes through `vault_io` and through the gate (no direct `write_text`), asserted structurally rather than by observing the result. (c) READBACK ORACLE, stated over KEYS, computed over the PARSEABLE values ONLY, and read from the note BYTES - for every note, the MULTISET of `WhatsAppJID.parse(v).key` over the post-migration values equals the multiset computed the same way from the pre-migration value or values, where BOTH multisets range over exactly those values for which `WhatsAppJID.parse` does not raise (classes A, B, C and E). The post-migration values come from a RE-READ: the note's bytes, parsed by a repository or a load that did not exist before the write, never through the migrating process's own repository - which holds a process-local cache and re-indexes the entity it just wrote (`person.py:257-284` plus the save rider), so an oracle computed through it compares the model against itself and is green by construction whatever the bytes say. The oracle NEVER calls `.parse` on a value the parser refuses - the parseable/unparseable split is itself computed by CALLING `parse` and catching `IdentifierError`, never from a hand-kept list, so a class-D value (`"n/a"`, `"ask Kate"`) contributes no key to either side instead of making the check RAISE, and a class-Ø value contributes none because there is no value. A class-D value's guarantee is BYTE-IDENTITY, not key equality - asserted per note against the pre-migration bytes, which is leg (e)'s clause and is where the coverage for D lives. Class Ø's guarantee is the shape conversion and nothing else: `""` becomes `[]`, no key on either side, and the note is otherwise byte-stable. Alongside the key multiset, TWO counts per note are asserted unchanged: the number of PARSEABLE values (so a dropped JID fails) and the TOTAL number of values including the unparseable ones (so a run that quietly deleted the class-D junk it was told to leave alone fails too, even though that value never had a key). A migration that dropped a person's second JID FAILS this while remaining self-consistent, and a migration that invented one fails it too. Keys rather than whole parsed objects, deliberately - leg (d) rewrites a raw spelling on purpose and `.jid` legitimately changes while `.key` must not. (d) CLASS-C REPAIR, counted as its own class, and guarded on PHONE-BEARING - a class-C value is rewritten to its canonical `<digits>@s.whatsapp.net` form and ONLY values whose `WhatsAppJID.parse(v).phone_digits` is non-empty are ever rewritten, asserted key-preserving by leg (c) over exactly those notes. The guard is asserted, not assumed: applying the repair to a phone-less unstorable value (class E) would write `"@s.whatsapp.net"`, which `parse` then refuses, so a build without the guard converts a leave-alone note into one the readback cannot even classify - the test plants a class-E note and asserts it is byte-identical after a repair-enabled run. So the population `PersonRepository.save` will refuse afterwards is class D plus class E, not class D alone. The count of repairs is reported separately from the count of shape-only conversions, and a run invoked with repair disabled leaves class C untouched and reports it (Ruling B's alternative arm, so the criterion holds either way Dave rules). (e) COUNTS RECONCILE - the dry run's per-cell counts, the number of notes the write commits, the repair count, and the readback's counts all agree, with zero notes left in the scalar shape; a disagreement is REPORTED loudly and the run exits non-zero rather than finishing quietly. A class-D or class-E value is never dropped and never rewritten - it is reported as needing repair and its note's `whatsapp` bytes are asserted byte-identical. And the residual's repair path is asserted to exist rather than promised: after the run, a class-D note is cleared through a delta arm and a class-E note is rewritten through one, both SUCCEED (AC-3's CLEARING and CLASS-Ø legs are what make that true), so "reported and left for hand repair" names a door this suite has opened rather than a door the write gate refuses (F16).
why: This is WI-010's stated un-park criterion (`docs/migration-support.md:20-22`) and the first real schema migration in this repo, so the discipline it establishes is reused. The readback oracle is the point - a one-off script over ~1,170 notes with only a success count cannot distinguish "migrated" from "migrated and lost the second JID", which is precisely the data this item exists to start storing. It is stated over `.key` and a count because that is what "no identifier moved" MEANS to every index and resolver in the package, and because leg (d) changes raw spellings by design - an oracle over the parsed dataclass would refuse the repair the design depends on, which is the kind of contradiction that is free to fix now and costs a re-sign later. The PARSEABLE-ONLY scoping of leg (c) is the round's material correction and it is stated INSIDE the criterion on purpose - the earlier wording said the multiset ran over "the pre-migration raw value or values" while this same AC mandates a class-D plant, so an author implementing the sentence literally called `.parse("n/a")` and the oracle RAISED instead of passing or failing: it errored out before either a correct or a wrong build could be judged. The correct exclusion was inferable from other paragraphs, which is exactly the problem - the frozen criterion is what a builder builds against, and every real vault carries some unrepaired junk, so two honest implementers reading the old sentence would have diverged on whether the readback ran at all. The TOTAL-count arm is what stops the scoping from becoming a licence to delete the values it excludes from the key check. Leg (d) is what makes AC-3's `save` refusal affordable rather than a field of unsaveable notes (F13 leg 3), and it is split out as its own count because rewriting stored values is a disclosure Dave is ruling on, not a silent side effect; its phone-bearing guard exists because "class C is always phone-bearing" is only true once class E is carved out of it. Leg (a)'s digest and the containment wall exist because a migration that writes during its dry run has already spent the only cheap chance to be wrong. Two additions this round. The RE-READ clause in leg (c) closes a reading under which the whole oracle is vacuous rather than wrong: the repository re-indexes what it just wrote, so a readback taken through the migrating process is a comparison of a private replica with itself - verify-by-readback means a re-READ or it means nothing, and the wrong reading passes silently on a migration that wrote nothing at all. And leg (e)'s repair-path assertion is what stops "reported and left for hand repair" from being a phrase: the whole class-Ø fold exists because that sentence was, under the earlier AC-3 text, a promise the item's own write door refused (F16), so the criterion now exercises the door instead of naming it.
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
The note still loads, the value is still there, the linter names it instead of nobody noticing until a
hand repair, and the note stays editable for everything else. What refuses until the value is fixed is
re-serializing the WHOLE stored person record — saving the person through the repository, or writing the
entity through `write_markdown_file` — and it says so. **And** when somebody goes to FIX it, that works:
clearing the field, or writing a properly spelled JID over it, succeeds through any of the package's
doors. Emptying `whatsapp:` is always allowed, everywhere, because an empty field claims no identity and
there is nothing to validate — which is also why a person note created from the template, with
`whatsapp:` unset, is written without complaint. "Reported and left for hand repair" has to name a repair
somebody can actually do.

**Given** the live vault on the day the migration runs — **when** it runs the first time, **then** it
PRINTS what it would change and changes nothing; **when** it runs for real, **then** every person is
reachable by exactly the same WhatsApp identities as before — a bare number that becomes a properly
spelled JID still answers to the same number, and nobody loses a second identity — and the readback
reports zero notes left in the old shape and zero notes whose identities moved. **And** if any of those
numbers disagree, the run says so and exits non-zero rather than finishing quietly.

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

## AC Red-Team — 2026-09-26

Round 1, no prior `ac-red-team` verdict on this document. Read in the prescribed order: `## Intent`,
`### Examples of done`, `## Problem / Motivation` and the exploration sections, then `##
Acceptance Criteria` last. Re-verified every code citation below at this worktree's HEAD
(`c93006a` plus the seeded uncommitted delta) rather than trusting the architect rounds' prior
reads.

The Intent's referent is narrow and testable: a value carrying a WhatsApp JID domain is
storable, a value that merely parses is not thereby storable, nothing already stored is dropped,
and resolution stays liberal. Measured against that referent, AC-1 through AC-4 hold up under
attack — the class table is derived by calling the two predicates rather than hand-listed, the
plants are named and unhoped-for (AC-1's negative-control lid, AC-3's required class-C literal at
every arm), and the anti-erasure and anti-projection legs (AC-3's two-directional `save` pin,
AC-4 leg (b) and leg (c)) each close a specific silent-corruption branch a builder could otherwise
ship. One AC does not survive the attack: AC-5's own oracle is unsatisfiable over the fixture the
same AC mandates.

**AC-5 — MATERIAL. The readback oracle in leg (c) raises an exception on the class-D member
leg's own fixture description requires it to plant, rather than passing or failing.**

Failure scenario: AC-5's desc requires the migration test's corpus be "planted with at least one
note per AC-1 class" — A, B, C, and D, where D is defined (AC-1, and `identifier.py:269-281`,
re-verified this round) as "does not parse": `WhatsAppJID.parse` raises `IdentifierError` for
`None`, empty, and any non-`@lid` string whose `normalize_phone` output carries fewer than
`Phone.MIN_DIGITS == 7` digits — e.g. `"n/a"`. Leg (c)'s oracle is stated as: "for every note, the
MULTISET of `WhatsAppJID.parse(v).key` over the post-migration values equals the multiset computed
from the pre-migration raw value or values." A test author implementing that sentence literally
calls `.parse(v).key` on the pre-migration raw value of every planted note, including the
mandatory class-D one — and `.parse("n/a")` raises. The oracle as worded cannot execute over its
own required fixture; it does not merely fail on a correct-vs-wrong build, it errors out before
either build gets judged. The document elsewhere states the CORRECT behavior for class D
elsewhere in the same AC ("A class-D value is never dropped and never rewritten — it is reported
as needing repair and left byte-identical") and in `## Approach` step (4) ("class D is reported
and left untouched"), but leg (c)'s oracle sentence itself does not say "over the parseable
values, with class D covered by byte-identical instead" — so the correct exclusion is nowhere
in the frozen criterion text a test author is meant to build against; it exists only as an
inference from other paragraphs plus the architect's round-2 note 3, which the AC text has not
absorbed. What changes: leg (c) needs its own sentence stating the multiset equality holds over
the PARSEABLE values only, with class D covered by the leg (a)/(e) byte-identical and
reported-and-left clauses instead of by the same oracle — the fix is one sentence, but it is a
frozen-AC-text fix, not a build-runner inference, because two honest implementers reading only
the criterion as currently worded would diverge on whether the readback check runs at all for a
corpus containing unrepaired junk (every real vault has some).

**AC-1 — MINOR, non-blocking. The four-class partition is not provably exhaustive over the
domain `parse` actually accepts, and the gap sits exactly on the `@lid` boundary the criterion
depends on for its guards.** `parse` tests for the SUBSTRING `"@lid"` anywhere in the value
(`identifier.py:276`), not a `@lid` suffix. A value like `"123@lid.example.com"` therefore parses
via that branch (`phone_digits == ""`), which is neither A nor C (both require non-empty
`phone_digits`); under the STORABLE predicate's stated closed set `{"s.whatsapp.net", "lid"}`
its domain (the text after the last `@`, i.e. `"lid.example.com"`) is not a member, so it is also
not storable, ruling out B (which requires storable). It parses, so it is not D either. This
input has no cell in the declared four-class table, so AC-1's "classification asserted exhaustive"
is false for it — a property-level assertion over arbitrary strings would find this counterexample;
an assertion scoped only to the planted exemplars would never see it and would go green while
silently leaving this slice of the input space unclassified. Not blocking on its own (the live
corpus has zero `@lid`-bearing values today per F6, so the population is very likely empty, and
the document's other guards — the independence assertion on `notaphone@s.whatsapp.net` — already
probe the adjacent boundary), but it is the same shape of gap AC-5 has, one level up: a criterion
claims a totality property the declared predicate table does not actually cover. What would have
to change: either state the table has a fifth (empty-by-construction) cell for "parses via `@lid`
substring, not storable" and assert it stays empty, or scope the "exhaustive" claim explicitly to
the domain the corpus and the plants exercise rather than to "every value."

```verdict
gate: ac-red-team
verdict: REVISE
date: 2026-09-26
model: claude-sonnet-5
note: AC-5 leg (c)'s readback oracle calls `WhatsAppJID.parse(v).key` over every planted note's pre-migration value, but AC-5's own fixture mandate requires a class-D (unparseable) note, which makes `.parse` raise rather than let the oracle pass or fail — the exclusion lives in other paragraphs, not in leg (c) itself.
targets: AC-5, AC-1
prior: none
basis: original
findings: 1/2
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

## AC Red-Team — 2026-09-26 (round 2)

Round 2 for this gate. Round 1 (above) found AC-5 leg (c)'s oracle unsatisfiable over its own
mandated class-D fixture and an AC-1 exhaustiveness gap at the `@lid`-substring boundary; both were
folded (class E entered the table, AC-1's classifier gained the no-fall-through assertion, AC-5 leg
(c) was rescoped to the parseable values). Re-verified this round rather than carried: `parse`'s
`@lid` branch runs before the digit test and `phone_normalization.py` splits at the first `@`
(re-read at `identifier.py:270-281`, `phone_normalization.py:52`), so the five-cell table is now an
actual partition of `parse`'s outcome space and AC-1's independence legs still hold on
`notaphone@s.whatsapp.net` (pinned at `tests/test_identifier.py:140`, re-read). **Round-1 findings:
HELD.**

Between round 1 and this round, the architect ran two further rounds on this same document (rounds
2 and 3, both present above). Round 3's blocking finding lands on `AC-3`/`AC-4`, inside my gate's
scope, and it is ORIGINAL text — the class table's placement of `""`/`None` under class D predates
every fold this document has undergone. I re-derived it independently rather than trusting the
architect's fence, because a defect two gates find the same way is stronger evidence than one gate's
say-so, and because my job is to attack the frozen criteria, not the other gate's prose.

**AC-3 / AC-4 — CRITICAL. AC-3, read literally, requires refusing the one value that is simultaneously the model default, the person template's value, 21 of 22 `whatsapp`-carrying fixture notes, and the only spelling this package has for "clear the field" — which makes the design's own promised repair path for classes C/D/E unbuildable, and the contradiction is invisible to every test AC-3 through AC-5 currently name.**

Failure scenario: a builder implements AC-3's desc exactly as worded — "Every write arm that can
introduce a `whatsapp` value refuses a value that is not STORABLE - classes C, D and E ... in BOTH
shapes, with nothing written." The class table (`## Exploration Notes`) lists `""` and `None` as
class-D exemplars alongside `"n/a"`, and I re-verified `WhatsAppJID.parse` treats them identically:
`identifier.py:273-275` — `if not s: raise IdentifierError(...)` — fires for `""` exactly as it does
for `"n/a"`; there is no branch that special-cases blank. So a `gate_write` arm built to AC-3's
letter refuses `whatsapp: ""` through every dict door with the same `pattern` and the same
"nothing written" guarantee it applies to `"n/a"`.

That build is self-consistent and passes AC-3 as drafted — AC-3 never names an empty-string case as
a required member at any arm, positive or negative, so nothing forces a test author to notice the
collision. It also passes AC-4(a) as drafted, because AC-4(a) is a READ-side assertion ("a note with
an empty value... present the empty collection") and the entity-shaped arms AC-4/AC-5 exercise never
construct a literal `""` payload for the gate to judge: with the stored field `List[str]` and a
model default of `[]` (`models.py:94` today; `[]` post-migration per the fold), `model_to_frontmatter`
emits `[]`, and an empty list has no member for a per-element arm to refuse — confirmed by re-reading
`writer.py:112-117`. Only the three dict arms (`writer.py:385`, `writer.py:443`, `base.py:728`) ever
receive a bare `""`, and none of AC-3's required members (`"+44 7739 341679"`, class-E's
`447700900456@lid.example.com`) is blank, so the whole AC-3 through AC-5 suite is green on a build
that refuses blank.

The break this produces is two-fold and both halves are load-bearing, not decorative: (1) Ruling B
leg 2 and AC-5 leg (e) both promise that the class-D/E residual is "reported and left for hand
repair" — but the package's only clearing doors are `update_frontmatter_field(path, "whatsapp", "")`
and `update_fields(person, {"whatsapp": None})` (re-verified: `writer.py:333-337` sets a field value,
there is no delete/remove affordance anywhere in the writer), and both hand the gate an empty or
`None` value, which a build honoring AC-3's letter refuses. The one repair channel the design commits
to elsewhere in the same document is therefore unbuildable under AC-3 as currently worded. (2) Any
producer that writes the template's own default — HAL9000's PATCH door clearing the field, `new-person`
minting a stub with `whatsapp` unset — starts being refused on the single most common value in the
corpus (21 of 22 `whatsapp`-carrying fixture notes per F6, re-verified by `rg -n -i 'whatsapp'
tests/fixtures/vault`), which is a materially larger consumer-visible break than the C+D+E population
the census precondition is scoped to measure.

This is the "mutually unsatisfiable ACs" failure class in the role's own hunt list: AC-3's literal
refusal population and AC-4(a)'s treatment of empty-as-absence, combined with Ruling B/AC-5's
repair-path promise, cannot all hold under one build, and no criterion states the resolving rule
("absent/empty/None introduces no identifier and is therefore never refused — the refused population
is the NON-empty unparseable/unstorable values") in the frozen text itself.

What would have to change (matches the fold the architect round-3 fence already proposes, verified
independently rather than copied): AC-3's desc needs one clause scoping its refusal population to
NON-EMPTY values that fail STORABLE, plus a new leg asserting that clearing the field (writing `""`
or `None`) through a delta arm SUCCEEDS even when the note's stored value is class C, D or E — since
that is precisely the hand-repair path AC-5/Ruling B depend on. The class table's D exemplars should
drop `""`/`None` (or the table should state explicitly that absence is a separate, always-accepted
case, matching `_project_identifiers`'s own `add()`, which returns on a None/blank raw before parsing
at all — re-verified at `person.py:318-320`). This is a frozen-AC-text fix, not a build-runner
inference: two honest implementers reading AC-3 as currently worded diverge on whether writing `""`
should succeed, and the criteria exist precisely so that question is not left to whoever builds first.

No other material defect survived this round's attack on AC-1, AC-2, AC-4(b)-(d), or AC-5(a)-(d):
the plants are named and unhoped-for, the anti-erasure and anti-projection legs each pin a specific
silent-corruption branch, the `check:` keys all name bare test function names a battery can discover,
and the empirical premises (F6's corpus count, the derivation citations) were re-run rather than
trusted this round.

```verdict
gate: ac-red-team
verdict: REVISE
date: 2026-09-26
model: claude-sonnet-5
note: AC-3 read literally refuses `""`/`None` (class D) at every write arm, but that is the model default, the template value, and 21/22 fixture notes, and it is also the only spelling the package has for clearing a field — so the hand-repair path AC-5/Ruling B promise for the C/D/E residual is unbuildable, and no AC-3 through AC-5 test as drafted would ever exercise the collision; independently re-derived, converges with the architect's round-3 finding.
targets: AC-3, AC-4, #exploration-notes
prior: held
basis: original
findings: 1/1
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

## AC Red-Team — 2026-09-26 (round 3)

Round 3 for this gate. Rounds 1 and 2 (above) found AC-5 leg (c)'s oracle unsatisfiable over its
own mandated class-D fixture plus an AC-1 exhaustiveness gap (round 1, folded: class E entered the
table, AC-5 leg (c) rescoped to parseable values), and independently re-derived the class-Ø
contradiction between AC-3's refusal population and AC-4(a)'s empty-as-absence reading (round 2,
folded: class Ø entered the table as its own cell, AC-3 gained its CLEARING and CLASS-Ø legs).
Re-verified this round rather than carried: the current AC-3 desc now reads "THE CLEARING LEG...
THE CLASS-Ø LEG" with both asserted at every delta arm, and AC-5 leg (c) now reads "computed over
the PARSEABLE values ONLY" with the parseable split computed by calling `parse` and catching
`IdentifierError`. **Both prior rounds' findings: HELD.**

Between round 2 and this round, the architect ran a fourth round on this same document (present
above), landing two blocking findings on the fixture-plant plan that sit inside criteria this gate
signs off on — AC-1's `why:`, AC-3's required members, and AC-5's plant list. I re-derived both
independently against this tree's code rather than trusting the architect's fence, because my job
is to attack the frozen criteria text, not the other gate's prose, and because a defect two
decorrelated gates find the same way is stronger evidence than one gate's say-so. Both hold.

**AC-1 / AC-3 — CRITICAL. AC-1's own `why:` clause asserts `@Thrandell Ibberly.md` supplies class C
"for free," but that note is the corpus's sole `roundtrip_representative` for `person`, and two
in-tree tests already write it through the gated whole-record entity door asserting NO refusal —
so a build that correctly implements AC-3 makes both tests fail, and the self-consistent "fix" is
to delete the repo's only proof that a full person field set survives the write door.**

Failure scenario: I re-read `tests/fixture_vault.py:219-233` — `@Thrandell Ibberly.md` carries
`whatsapp="447700900789@example.com"` and `roundtrip_representative=True`.
`tests/test_fixture_vault.py:689-695`'s `_representative` helper asserts there is EXACTLY ONE such
note per `declared_type`, so this is not one specimen among several — it is the note. Two tests
then write that entity through `write_markdown_file(entity=…)`, the whole-record-projection arm
AC-3 itself names as a refusal surface: `tests/test_writer.py:404-428`, specifically line 421
(`write_markdown_file(out / name, entity=doc.entity, body=doc.body)`) followed by an assertion at
`:424-427` that every declared field — `whatsapp` among them — round-trips unchanged, with no
`NameGateRefusal` anywhere in the test; and `tests/test_fixture_vault.py:705-761`'s AC-2
type-registry sweep, which at `:726-732` asserts the person representative is "GATE-CLEAN by the
DOOR's own predicate." Under the STORABLE predicate's closed set `{"s.whatsapp.net", "lid"}`,
`447700900789@example.com` parses (phone-bearing, `phones_match` digits `447700900789`) and is NOT
storable — it is a class-C value by this document's own table. So a builder who implements AC-3's
"whole-record arms refuse classes C, D and E" correctly makes both of these tests raise
`NameGateRefusal` where they currently assert a clean round trip. The branch a builder reaches for
when the battery goes red is "the round trip now legitimately refuses, so change the test to expect
that" — a build that takes it is self-consistent and green on every AC in this set, and it silently
trades away the repo's only assertion that a whole person field set survives the write door, in
exchange for nothing this item asked for. AC-1's `why:` (`"the corpus supplies Ø (21 notes) and C
(`@Thrandell Ibberly.md:7`) for free"`) is the sentence that licenses this: it tells a spec-writer
the class-C member costs nothing to plant, when in fact planting it on THIS note costs the
round-trip representative's own invariant. What would have to change: AC-1's `why:` stops calling
Thrandell's value "free"; the representative's `whatsapp` moves to a value AC-3 accepts (class Ø or
a storable class-B `@lid`), and the class-C exemplar (`447700900789@example.com`, or an equivalent
wall-clean spelling) moves onto a plant on a non-representative note.

**AC-3 / AC-5 — MATERIAL. Two of the literal plant values these criteria require — the class-A and
class-E exemplars — cannot be planted inside the frozen fixture corpus's own reach without
violating the WI-016 privacy wall that same corpus enforces on itself, and neither AC nor `##
Exploration Notes` says where they go instead.**

Failure scenario: I re-read `tests/test_fixture_vault.py:302-319` — `RESERVED_EMAIL_DOMAINS =
{"example.com", "example.net", "example.org"}` is matched by EQUALITY, `RESERVED_TLDS = (".test",
".invalid", ".example")` by suffix, and `_host_is_reserved` accepts only those two routes; `reach_files()`
at `:386-392` scopes the check to every file under `tests/fixtures/vault/` plus
`tests/fixture_vault.py` itself. AC-3 names `447700900456@lid.example.com` as "a REQUIRED class-E
member at every arm," and AC-5 requires a plant for every non-Ø cell including class A (the
`## Exploration Notes` table's own exemplar for class A is `447700900123@s.whatsapp.net`). Neither
domain clears `_host_is_reserved`: `s.whatsapp.net` is not an exact member of the reserved set and
carries no reserved TLD, and `lid.example.com` is a SUBDOMAIN of `example.com`, which the equality
check does not match. A spec-writer who follows F6's own instruction ("the plant must KEEP
Thrandell's value" implies corpus-resident plants generally, and nothing in the document says
otherwise for A and E) and plants either literal as a fixture-corpus note makes the frozen corpus's
own privacy-wall leg fail — a test this document did not write and cannot touch, since `## Write
Targets` and the ACs treat the corpus's existing walls as fixed ground. There is no declared
exemption for either domain anywhere in this document (contrast `RESERVED_ISBN`, which the wall
already carries as a named, equality-pinned exception) — so the AC frame as currently worded is
unsatisfiable for these two cells by any build that keeps the corpus's privacy wall green, and the
class-D exemplar (`notaphone@s.whatsapp.net`) has the same problem IF it is ever planted in the
corpus rather than kept in a fresh test module's own literals, which AC-1's independence leg needs
it to be. What would have to change: state explicitly, in `## Exploration Notes` (F6) or in AC-1/
AC-3/AC-5 directly, that the class-A and class-E storable-form plants live in the new test module's
own temporary vault rather than the frozen corpus, and respell the class-E exemplar's domain to a
reserved-TLD-safe form (e.g. `447700900456@lid.example`) so it stays wall-clean while remaining the
same cell — a subdomain of a reserved TLD, still outside the closed set `{"s.whatsapp.net",
"lid"}`.

No other material defect survived this round's attack on AC-2 or on AC-4's legs (a)-(d): the
class-Ø round trip in AC-4(a) still meets AC-3's CLASS-Ø leg on the write side exactly as round 2's
fold intended, the anti-erasure and anti-projection legs still pin a specific silent-corruption
branch each, and the `check:` keys still name bare test function names. Rulings A, B and C are
untouched by both findings above — neither reopens a question for Dave; both are corrections to
this document's own fixture plan.

```verdict
gate: ac-red-team
verdict: REVISE
date: 2026-09-26
model: claude-sonnet-5
note: AC-1's `why:` calls `@Thrandell Ibberly.md`'s whatsapp value a free class-C plant, but that note is the corpus's sole person round-trip representative and two tests write it through the gated whole-record door asserting no refusal — and separately, AC-3/AC-5's required class-A/class-E literals (`@s.whatsapp.net`, `@lid.example.com`) fail the frozen corpus's own privacy wall if planted in its reach; both independently re-derived, converge with the architect's round-4 findings.
targets: AC-1, AC-3, AC-5, #exploration-notes
prior: held
basis: folded-material
findings: 2/2
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
