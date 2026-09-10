---
id: WI-016
title: "Frozen anonymized real-data fixture vault"
project: obsidian-schemas
stage: done
created: 2026-03-22
last_touched: 2026-09-10
stage_changed: 2026-09-10
touched_by: spec-writer
tags: [testing, real-data-fixtures]
depends_on: []
round_budget: 12
transitions: ["idea>exploring@2026-09-07@porter", "exploring>specced@2026-09-07@porter", "specced>ready@2026-09-08@porter", "ready>building@2026-09-10@session", "building>done@2026-09-10@session"]
---

# Frozen anonymized real-data fixture vault

### Archived Rounds

<!-- archive-split: machine-maintained pointer; do not edit -->
Settled gate rounds for this item live in `docs/vault-fixtures-rounds.md` — every round at a conveyor door
this item has already advanced past, byte-for-byte, append-only, never rewritten. READ ON DEMAND
ONLY: each gate's latest standing round is still in this document, so nothing needed to advance this
item is in the drawer. Open it only to read a settled round's full reasoning.

## Problem / Motivation

*(Rewritten at ideation, 2026-09-06, cold-start, approval-only. The March framing led with
performance and property-based testing; both were measured below and neither is the live pain. The
2026-07-05 reslice above is closer and is kept. What follows is the re-measured version.)*

**There are zero fixture data files in this repository.** `tests/` holds 32 files, every one of them
`.py`; there is no `tests/fixtures/`, no `conftest.py` anywhere in the tree, and no `.md`, `.yaml` or
`.json` note under `tests/` at all. Every test that needs a vault therefore *builds one inline*, and
there are 83 hand-typed `type: <entity>` frontmatter literals across 13 test files to prove it, each
planted by that file's own private helper — `temp_vault`, `vault(tmp_path)`, `_note`, `_seed`,
`_plant`, `_rich_note`, `_plant_company_note`, `_plant_carrier`, `_write`. Nine are named here, and a
sweep of `tests/` for private note-planting helpers returns more of them (`plant_note`,
`_plant_dirty`, `_seeded_person`, `_typed_note_without_a_name`, `_write_multi_section_person`, …).
**The number is deliberately not pinned and nothing here rests on it** — an earlier draft wrote "Nine
helpers" above a list of eight, which is the shape this document has now corrected in four places.
The claim is the PREDICATE: thirteen files, one job, and no two of them share a corpus.

The consequence is not "the fixtures are small". It is that **every property this package has learned
the hard way lives in exactly one test's private literal, and nothing makes the next test inherit
it.** The corruption forms that motivated the workspace real-data-fixtures rule — diacritics, RFC
2822 leak strings, arrow-connective and `Me to ` descriptors, the triple-name collision — are 35
literals scattered across five test files (`test_repositories.py`, `test_wi126_body_preservation.py`,
`test_name_validation.py`, `test_identity_index.py`, `test_name_cleaning.py`) plus one in
`obsidian_schemas/name_cleaning.py`. A new test about a new write arm starts from an Alice/Bob vault
because that is the cheapest thing to type, and the corpus that would have caught the bug is three
files away in someone else's `_seed`.

Three specific holes fall out of that, all measured:

1. **`Exploration` is committed and completely untested.** The model is at `models.py:266`, wired
   into `EntityType` (`:306`) and `TYPE_TO_MODEL` (`:317`), and given a body-section config at
   `body_sections.py:320-323`. The token `Exploration` appears at 13 sites in the package and **zero
   sites under `tests/`.** No parse, no round-trip, no repository. WI-008's premise note already
   folds the missing model test into this item.
2. **The type registry has no total coverage anywhere.** `TYPE_TO_MODEL` declares 8 types;
   `ENTITY_BODY_CONFIG` declares 5. Nothing in the suite sweeps either, so `watch`, `explore` and
   `gift-idea` are in the same position `Exploration` is, and a ninth type would join them silently.
3. **The skip surface has no corpus.** `SkippedNote` / `_skip_reason` (`repositories/base.py:28-47`)
   is a three-valued classification — `malformed-frontmatter`, `schema-drift`, `unreadable` — and
   WI-020 built it precisely so an unloadable note stops vanishing at DEBUG. There is no vault on
   disk that contains one of each and declares which is which.

And the reason a *frozen* corpus rather than a live-vault read: the live vault churns. The
2026-09-06 queue review recorded both of WI-021's sentinel stubs turning over inside 25 days. A test
that reads the real vault is a test whose meaning changes without anyone editing it.

## Intent

Every test in this package should be able to reach for the same vault — one frozen sample whose
shapes came from the real thing, not from Alice and Bob — instead of typing its own notes and
quietly starting from a corpus that has never broken anything. The shapes that actually break this
code (accents, hyphenated surnames, addresses leaking into name fields, the same person three times,
notes that will not parse at all) should live in one place that every later name-and-identity change
gets to regress against, and the entity types nobody has ever tested should stop being invisible.
None of Dave's contacts' real names, emails or numbers go into this repository to get it.

## Exploration Notes

Explored 2026-09-06, cold-start, **approval-only** (`involvement: null` in `state/work-items.json`
:1823). The approach below is re-derived from the frozen `## Intent`; the mint's named mechanism —
"take a ~50-note slice of the real vault and anonymize it" — is treated as a hypothesis and is
**amended** in D1 below rather than inherited.

**Revised 2026-09-06 after the architect round (REVISE, verdict fence at the foot of this doc).** The
approach was found sound and stands unchanged; two criteria were underdetermined against one fact of
the code — the repositories' shared `@*.md` glob over a single flat directory. Both blocking issues
are resolved above and below: the flat single-directory layout is now stated in `## Approach` and in
"Constraints discovered" with the reason it is load-bearing, AC-4 names the DOMAIN of each of its
equalities (per repository, with the two untyped skip classes' double-ownership declared expected and
a planted discriminator for it), AC-3 carries the collision-vs-divergence question as one the census
rules, AC-2 names its round-trip subject and its write door, and the census's charge in
`## Write Targets` is extended to settle the class question. The four non-blocking notes are folded
too: the `unreadable` specimen's one viable spelling (invalid UTF-8 bytes, never `chmod`), the digest
regeneration recipe, and WI-030's differing scope. No premise moved and no criterion was weakened.

**Revised again 2026-09-06 after the AC red-team round (REVISE, verdict fence at the foot of this
doc; two findings, both folded).** *AC-5 — critical.* The containment wall covered emails, phones and
profile URLs — two of the three categories `## Intent` names, plus a bonus — and left NAMES, the one
field D1's amendment says the corpus exists to carry the shape of, with no machine check at all: a
specimen correctly pseudonymized on email and phone but carrying the live vault's actual `name:`
passed all five criteria green. AC-5 now carries a NAME CLOSURE leg (the corpus's whole name
vocabulary is a declared identity pool, asserted both directions, over the corpus bytes *and* the
manifest module that restates them) and a POOL PROVENANCE leg (the census commits a per-token
live-vault non-occurrence scan and the test asserts pool ⇄ table equality). Two things are said
plainly rather than assumed: a denylist of real names is REJECTED — committing one would be the leak
it prevents — and the ground truth of non-occurrence is the conductor's recorded scan, not an
in-suite assertion, because the suite is hermetic. That is the mitigating control, now tied to a
criterion instead of living in D4's "reviewable by eye" aside; what a human reviews is a few hundred
declared tokens once rather than fifty notes of free text on every change. *AC-3 — material.* `###
Examples of done` names "an address that leaked into a name field" and none of AC-3's nine draft
classes was that shape; since AC-3's equality is against whatever the census declares, the specimen
Dave asked for by name could have gone missing with every criterion green. The class is added as a
tenth draft class and the census's charge in `## Write Targets` now requires it to be confirmed with
a specimen or ruled absent affirmatively — with the general rule attached that a class measured at
ZERO is a row the conductor writes, not a row that may be omitted (which also folds the architect's
round-2 note 4). No premise moved and no criterion was weakened; AC-5 gained two legs and AC-3 gained
a class and a census obligation.

**Revised a third time 2026-09-06 after AC red-team round 2 and architect round 3 (both REVISE,
fences at the foot of this doc; three findings, agreed by both gates, all folded).** The previous
fold aimed right and was not satisfiable as written. *Finding 1 — AC-5(c) named a target it made
impossible.* The pool was one flat set holding NAME tokens and CONNECTIVE tokens (`Me`, `to`, `->`,
`Re`, `Fwd`) alike, and (c) demanded a zero-hit live-vault row for **every** member — while AC-3
charges the same census with measuring `Me to ` prefixes as a live, non-zero corruption class
(`name_validation.py:238-248` carries `specimen="Me to David Field"` on its `me_to_prefix` Tier-1
branch, verified in the seeded tree). Every route through was either a RED criterion or a false row
in the ledger the criterion exists to make trustworthy. The pool is now split in two: a `NAME_POOL`
carrying the provenance obligation, and a `CONNECTIVE_SET` frozen by ENUMERATION IN THE CRITERION
ITSELF (`Me`, `Re`, `Fwd`, `Fw`), exempt from provenance because a non-occurrence claim about
non-identifying furniture is unmakeable — and safe to exempt only because it cannot grow without an
AC change. The lowercase and punctuation connectives (`to`, `->`, `→`) are not set members at all:
they are outside the stated extractor's domain by construction, so declaring them would have created
members the closure could never exercise. *Finding 2 — the PROSE allowlist re-opened the leak the
fold closed.* It was unbounded, uncensused, and checked against one undifferentiated byte scan that
covered `name:` values and filename stems too, so the cheapest green for a specimen carrying the live
vault's real surname was to add the surname to the allowlist. The scan is now split by POSITION
rather than by bucket: identity-bearing positions (filename stems, and the manifest's declared
`name` / `aliases` / title values) assert against `NAME_POOL ∪ CONNECTIVE_SET` with the allowlist not
a term in the assertion and asserted DISJOINT from those tokens; free prose gets the allowlist as a
literal frozenset. The cheaper alternative — putting the census obligation on the allowlist instead —
is named and REJECTED in AC-5's `why:`: it collapses the allowlist into the pool and taxes every
docstring word with a conductor scan. *Finding 3 — `## Write Targets` and AC-3 asserted opposite
verdicts for a ruled-absent class.* The census's class table now carries explicit `count` and
`status` columns; AC-3's both-directions equality runs over specimen-bearing (count > 0) rows only,
its per-row shape assertion is conditional on status, and it gains a DRAFT CLASS FLOOR so the
no-silent-omission intent behind the zero-row rule is machine-checked rather than left as prose to
the conductor. Two non-blocking notes are folded with them: AC-5(d) no longer claims `normalize_phone`
emits E.164 (it strips every non-digit — `phone_normalization.py:39-55` — so `+44 7700 900123` yields
`447700900123`, and the leg now asserts the digits-only value plus `phones_match` over its variants),
and the non-UTF-8 member's declared hex literal is specified LOWERCASE so it yields no extracted token
and cannot become a reason to grow the allowlist. No premise moved, no criterion was weakened, and
the approach is untouched — both gates said so explicitly.

**Revised a fourth time 2026-09-06 after architect round 4 and AC red-team round 3 (both REVISE,
fences at the foot of this doc; four findings, agreed by both gates, all folded — and this fold
REMOVES the generator both gates named rather than pruning its fourth instance).** Architect round 4
named the shared root of three consecutive folds' worth of defects: *a mandatory NON-VACUITY clause
over a set the builder does not author*. Every declared set added since round 2 produced at least one
member the corpus cannot exercise (`to`/`->`/`→` in round 3, `Re`/`Fwd`/`Fw` now), and each fold
patched the instance and kept the generator. This fold takes the generator out. Net effect on AC-5:
one clause deleted, one relation weakened from an equality to a containment, one vague field phrase
replaced by an enumerated list read off `models.py`, and one derived (not declared) admission added.
The criterion is strictly smaller in what it demands and strictly more precise in where it demands
it.

*Finding 1 — `CONNECTIVE_SET`'s members were grounded in nothing, and non-vacuity made the corpus owe
each one an identity-position specimen. Both halves fixed.* Verified here independently rather than
taken from the gates' prose: a Grep for `Fwd|Fw:|Re:|\bFw\b` over the whole seeded tree returns
**one file — this document.** Nowhere in `obsidian_schemas/` or `tests/` does any Tier-1 branch,
recovery regex or census class produce a mail-header prefix. The package's actual connective
vocabulary is `Dave|Me|My` (`name_cleaning.py:46` `_CALENDAR_PREFIX_RE`, `:54` `_ARROW_PREFIX_RE`,
`:55` `_ME_TO_PREFIX_RE`). So the set is re-enumerated from that code as exactly `{"Me", "My",
"Dave"}` — **and its NON-VACUITY CLAUSE IS DROPPED OUTRIGHT.** Dropping it costs nothing the wall was
getting: what stops `CONNECTIVE_SET` becoming the allowlist's escape hatch is that it is frozen by
literal enumeration IN the criterion and asserted equal to it, never that the corpus exercises it —
and coverage of whatever connective the live vault actually produces is already guaranteed by AC-3(i),
which requires a specimen for every MEASURED census class and cannot demand one for a class the vault
does not have. `Dave` is furniture rather than identity here (it is the vault owner's own calendar
label, already in the tree at `name_cleaning.py:46`), and its provenance exemption is `Me`'s: a
non-occurrence claim about it is unmakeable, not merely tedious. `NAME_POOL` KEEPS its non-vacuity,
because the builder authors `NAME_POOL` and satisfies it by declaring only the tokens the corpus
actually uses — the generator only bites on sets the builder does not author.

*Finding 2 — AC-5(c)'s pool relation crossed the conductor/builder boundary in a direction that
boundary does not carry.* `docs/vault-shape-census.md` is a PRECONDITION landing in HEAD before Dave
signs; `NAME_POOL` is declared in-cage during a build that has not happened. A both-directions
equality asked the earlier artifact to predict the later one's exact token set. The relation is now a
one-directional **containment**: `NAME_POOL` ⊆ the census's pool table. Closure is not weakened by a
byte — an uncertified token still cannot enter an identity position, which is the entire property —
and a surplus certified row costs nothing, because every row carries its own scan and a token nobody
used is not a leak. It also removes the paired-edit-across-a-cage-boundary ceremony round 3 flagged as
this item's dominant recurring cost.

*Finding 3 — `Person.company` sat outside the identity positions, and the same read found the phrase
that let it happen.* Confirmed at `models.py:84` (`company: str = ""`, distinct from `title: str = ""`
at `:85`). But reading the models field by field rather than fixing the one field named shows the
gap was generated by the phrase "the company/meeting title fields", which is wrong in both halves:
**`Meeting` declares no `title` at all** (`models.py:259-263` — `date`, `attendees`, `topics`,
`meeting_id`), so the list named a field the schema does not have; and it omitted
`Meeting.attendees` (`:261`), a list of *people's names*, plus `Book.author` (`:161`),
`Watch.director` (`:195`), `Watch.recommended_by` (`:200`), `Explore.source` (`:224`, "who mentioned
it") and `GiftIdea.for_person` (`:242`, alias `for`) — every one of them a real person's name in a
type nobody has ever tested. Patching `company` alone would have left six more doors of the same
shape. AC-5(b) therefore now states the RULE — *a field is an identity position iff its value names a
PERSON or an ORGANISATION* — and enumerates the current answer field by field with line cites, to be
reconciled against the schema before origination exactly as AC-3's DRAFT CLASS FLOOR is. `Person.title`
(`:85`) is deliberately excluded and the exclusion is argued: a job title carries no identity, and
forcing `Director` into a pool that owes a zero-hit live-vault row would manufacture finding 1's shape
on purpose. A meeting's title is not lost — it lives only in the filename (`Meeting <date> - <title>.md`),
which the stem scan already reaches.

*Finding 4 — both criteria demanded non-empty verbatim stdout from scans whose honest zero-result
output is empty.* Fixed where the cause is rather than where it fires: `## Write Targets` now requires
every recorded scan command to emit a COUNT (`rg -c`, `rg --count-matches`, `| wc -l` — the artifact
names its own form), so a true zero records verbatim as `0` and the criteria's non-empty-stdout
assertions are checked against a command that always writes something. Nothing has to be typed into a
field labelled verbatim, which was the objectionable part.

*One derived admission, added because finding 3's fix makes it bite, and DERIVED on purpose.* With
`Person.company` and `Book.publisher` in identity positions, a specimen written as `Voxleaf Ltd` puts
`Ltd` in an identity position, and `Ltd` cannot honestly carry a zero-hit row in a vault of 2,159
company notes (`docs/company-name-corpus-audit.md`) — finding 1's shape again, one fold later. The
admission is therefore read from the package rather than hand-declared: an identity-position token
whose casefold is in `name_cleaning._GENERIC_ORG_SUFFIXES` (`name_cleaning.py:58`, and compared
casefolded by the package itself at `:148`, `:185`, `:191`) is admissible and owes no pool row. A
fourth hand-written literal set is exactly what the generator eats; a set read off the package cannot
be padded by a builder looking for the cheapest green, and none of its eight members
(`support`, `ltd`, `inc`, `corp`, `group`, `team`, `limited`, `llc`) can hide a person.

*And one place the machine stops, said plainly rather than papered over.* The extractor's domain is
runs beginning with an uppercase or non-ASCII letter, so an all-lowercase identity value yields no
token and is outside the wall — the same reasoning that (correctly) kept `to`, `->` and `→` out of
`CONNECTIVE_SET` in round 3. A "make it lowercase" dodge is not closed by machine and deliberately is
not chased with another clause: it destroys the shape the specimen exists to carry, so AC-2's declared
oracle and AC-3's declared verdict both notice, and the residue is what the census's pool table and
its one-time human review cover. Naming the residue is cheaper and more honest than a fifth clause.

No premise moved, no criterion was weakened, and the approach is untouched.

**Revised a fifth time 2026-09-06 after architect round 5 and AC red-team round 4 (both REVISE, fences
at the foot of this doc; ONE finding, raised independently by both gates against the same criterion,
folded — and the finding is of a DIFFERENT family from the four before it, which is the item's own
falsification test coming back clean).** Both gates confirmed round 4's four findings closed and its
generator gone: no declared set now carries an obligation over members the builder does not author,
and both looked for a fifth instance specifically before reporting. What they found instead is
narrower and finite: **AC-5(b) stated a one-line generating rule and then enumerated a list that rule
does not generate, in both directions** — and since the criterion instructs a later reader to
reconcile the list against the schema by applying the rule, it was buildable two ways by its own
instructions (the WI-144 shape).

*The direction that cost something.* `Exploration.related` (`models.py:299`) — a `List[str]` whose own
docstring at `:280` glosses its members as `[[Other Exploration]], [[Person]], etc.` — was NOT on the
identity-position list, so a real contact's name written there was scored FREE PROSE, and the cheapest
green was one `PROSE_ALLOWLIST` entry with no `NAME_POOL` membership and no census row: the exact
bypass rounds 1–4 were each raised to close, open one field over. Verified here against the code
rather than taken from the gates: the field and its docstring gloss are as cited. And it is live for
this corpus specifically rather than hypothetical — AC-2 derives its sweep from `set(TYPE_TO_MODEL)`,
`exploration` is a member, and P4 measures **zero** `exploration` references anywhere under `tests/`,
so this corpus is guaranteed to carry the first `exploration` fixture anyone has authored, written
from a live note's shape by an author with no existing fixture to copy — and `related:` is the field
that shape hangs on. Two siblings the rule left UNDECIDED are decided rather than deferred, because
undecided is what produced the finding: `Watch.streaming_service` (`:199`) names an organisation
exactly as the listed `Book.publisher` (`:166`) does, and `GiftIdea.source` (`:243`) is the unglossed
sibling of the listed `Explore.source` (`:224`, "who mentioned it") — both are now listed, since the
same value kind must not get opposite answers inside one enumeration.

*The other direction, and the door no enumeration could reach.* The list included `Book.title`
(`:160`), `Watch.title` (`:193`), `Explore.title` (`:222`) and `Exploration.title` (`:295`), none of
which names a person or an organisation, so the reconciliation instruction would have DELETED them on
the rule's own authority. They are kept and the keeping is now DECLARED: clause 2 states them as a
deliberate over-constraint with its reason, so a later reader preserves them instead of pruning them.
Separately, `model_config = ConfigDict(extra="allow", ...)` (`:31-32`, read here) means a specimen may
carry frontmatter keys no model declares — a `manager:` or `introduced_by:` on a schema-drift or
forward-compatibility note — which every enumeration over DECLARED fields misses by construction;
clause 3 makes any manifest-declared value for an undeclared key an identity position by DEFAULT, with
no manifest flag to opt out, because a builder-settable exemption is the escape hatch this criterion
has already been folded for twice. That default is satisfiable by construction, not a new instance of
the generator: the corpus author chooses both which undeclared keys exist and what they hold.

*What was NOT done, and why the fold is smaller than the previous four.* No fifth clause was bolted on
to close free prose. `Exploration.origin` (`:300`, "What sparked this") and `Meeting.topics` (`:262`)
stay excluded on the argument `Person.title` already carries: they are sentences, not names, and
clause 1 is deliberately "IS a name" rather than "could contain one" — the second reading obliges the
conductor to certify ordinary English with zero-hit rows, which is finding 1's shape rebuilt on
purpose. `Exploration.graduated_to` (`:301`, `[[Project]]`) is excluded for the same reason. The
residue is stated in AC-5's `why:` beside the extractor-domain residue rather than papered over: a
name in a prose field or a note body is walled by the allowlist and the pool's human review, not by the
closure. That has been true of note bodies since round 1; what this fold guarantees is the LINE's
placement — no field whose value IS a name sits on the prose side of it. Two cite errors inside AC-5(b)
were corrected while it is still a draft (both verified here): `_ME_TO_PREFIX_RE` (`name_cleaning.py:55`)
matches `^(Me|My)\s+to\s+` and carries no `Dave` alternative, so it is the UNION of `:46`, `:54` and
`:55` that equals `{Dave, Me, My}`; and the package compares `_GENERIC_ORG_SUFFIXES` with `str.lower()`
at `:148`, `:185` and `:191`, never `casefold` — which matters because the corpus deliberately carries
non-ASCII specimens, so the criterion now names the operation its own test performs. P13 is corrected
and P14 records the complete field-by-field reconciliation so this family is exhausted rather than
sampled. No premise moved, no criterion was weakened, the approach is untouched, and AC-1 through AC-4
were re-read by both gates with no new finding.

**Revised a sixth time 2026-09-06 after architect round 6 and AC red-team round 5 (both REVISE, fences
at the foot of this doc; ONE defect, reached from opposite directions by the two gates, whose halves
CONTRADICTED each other — and the fold is the sequencing that resolves them, not a compromise between
them).** Architect round 6 found `CONNECTIVE_SET` enumerated from three of the five prefix/suffix
regexes in `name_cleaning.py:46-57`, omitting `_ARCHIVE_PREFIX_RE` (`:56`) and
`_UNKNOWN_CONTACT_SUFFIX_RE` (`:57`) — the recovery arms of the only two live person Tier-1 branches
AC-3's draft class floor also omitted — and proposed adding `Archived`, `Unknown` and `Contact`. The
AC red-team, reading the same code, found that literal fix contradicted by this repository's own
specimens: AC-5(b)'s extractor said "each run whose FIRST character is an uppercase or non-ASCII
letter" and never said what a RUN is, and under the plain maximal-span reading `zArchived` is ONE run
beginning with a lowercase `z` that yields no token at all — so `Archived` would be an unexercisable
literal planted in a frozen set, which is round 4's defect with a gate's fold as its author instead of
a builder's shortcut. **Both halves are right and the order is the whole fix: the membership question
is not answerable until the extraction rule is.** So the rule is pinned FIRST — a run is a maximal
contiguous span over letters, marks, apostrophes and hyphens, bounded only by a character outside that
class and never restarted at an internal capital, extracted iff its first character is uppercase or
non-ASCII, with leading/trailing `'` and `-` trimmed — with four worked consequences written into the
criterion (`McDonald` is one token; `d'Angelo` yields none; `Zeta-9` yields `Zeta`; `zArchived` yields
nothing) so a later reader checks the rule rather than interprets it. The maximal reading is chosen on
evidence rather than by default: **P15 measures every `archive_prefix` specimen this repository has
ever committed — five distinct strings across eight sites — and every single one puts the `z`/`zz`
immediately against the capital, with zero exceptions**, so it is the only reading all of them are
consistent with, and it is also the reading an ordinary hyphenated or Mc-prefixed surname needs.
THEN the surface is re-enumerated by applying it, exhaustively rather than by sampling: **P16 records
all sixteen regexes in the two files — the eleven in `name_validation.py` and the five in
`name_cleaning.py`, plus both Tier-1 tables — and the union of extracted furniture tokens is exactly
`{Dave, Me, My}`. `CONNECTIVE_SET` does not move.** `archive_prefix` contributes nothing under the
pinned rule; `unknown_contact` contributes nothing from the code, both of its regexes spelling the
literal in lowercase. What the exhaustive pass did buy is the one genuinely undecided cell being NAMED
instead of guessed: `re.IGNORECASE` on `name_validation.py:113` puts the live `unknown contact` form's
letter-case in the vault's hands rather than the code's, and this repository commits it BOTH ways —
the lowercase suffix form six times over, matching the recovery regex's own `\s+unknown\s+contact\b`
shape and the branch's "WhatsApp scanner artifact" comment, and a capitalized standalone form
(`Unknown Contact Zeta-9`) three times, including as a `REFUSED_STEM` in
`tests/test_lint_vault_fix_gate.py:58` and as the branch's own display `specimen=`. No amount of
reading `obsidian_schemas/` settles that cell, so it gets AC-3's own remedy rather than a guess frozen
by signature: **`CONNECTIVE_SET` now carries the one-time pre-origination reconciliation instruction
the DRAFT CLASS FLOOR already had** — reconciled once against the census's measured character
profiles before Dave signs (if the census measures the capitalized form, `Unknown` and `Contact` are
added in the criterion; if the lowercase form, they are not), frozen exactly as now thereafter. That
is deliberately not the round-4 generator returning: the generator was a mandatory obligation over a
set the builder does not author, and this set still carries no occurrence obligation of any kind —
what it carries is a one-time author-side edit against an artifact that exists by then. The census is
charged in `## Write Targets` to record each furniture literal in its MEASURED casing rather than
paraphrased, since that is the input the reconciliation reads, and told not to write a pool row for
any capitalized furniture run (`Contact` has no honest zero-hit row here any more than `Ltd` does).
Architect's non-blocking note 1 is folded with it: **`archive_prefix` and `unknown_contact` join AC-3's
draft class floor**, taking it from ten classes to twelve — one omission with two symptoms, both
closed by the same read. Two of the round-2 notes carried open since are also closed while they are
cheap, because both are the same determinism family this round's finding is: AC-2(c) now NAMES its
equality (re-parse the written file and compare its frontmatter mapping to the manifest's declared
values — leg (b)'s oracle — never byte-equality against the original, whose fixity is AC-1(a)'s
digest), and AC-2 now states at its real size what leg (c) proves per type (`gate_write` returns
`dict(introduced)` unchanged for the six declared types that are neither person nor company,
`name_gate.py:319-344`, so leg (c) proves the gated door for two and proves the pass-through is a
pass-through for six). The third round-2 note is left open ON PURPOSE rather than by oversight, and
the disposition is recorded so a seventh round does not re-raise it: AC-4(c)'s "declared loadable
count" IS a third quantity distinct from corpus size and glob-match count, and that is the criterion
working rather than a gap — it is DECLARED in the manifest precisely so leg (c) is an oracle a
miscounting load fails, instead of an arithmetic identity every implementation satisfies by
construction. The general rule both this closure and round 5's needed, attached here so a
seventh round does not have to rediscover it: **every set AC-5 declares is enumerated by APPLYING a
stated rule to a NAMED, ENUMERABLE surface** — round 5 needed `models.py` read field by field, this
round needed the sixteen regexes read one by one, and both defects were "enumerated by sampling"
rather than by the rule. No premise moved, no criterion was weakened, the approach is untouched, and
AC-1 and AC-4 drew no finding from either gate.

**Revised a seventh time 2026-09-07 after architect round 7 and AC red-team round 6 (both REVISE,
fences at the foot of this doc; ONE finding, raised independently by both gates against the same
criterion, folded — and it is in AC-3, not in AC-5, which is the fact that decides what it means).**
Both gates confirmed round 6's finding closed and re-verified the closure against the code rather
than against the fold's prose: the pinned run rule does decide `zArchived` (one lowercase-initial run,
no token), `CONNECTIVE_SET` correctly stays `{Dave, Me, My}`, the four worked consequences are
checkable and correct, and neither gate found a fifth instance of round 4's removed generator. AC-1,
AC-2 and AC-4 drew no finding from either. What both found instead is that **AC-3's DRAFT CLASS FLOOR
was a hand-transcribed list quantifying over a surface the package declares as an iterable with unique
ids, and the transcription was wrong.** Verified here independently rather than taken from the gates,
and recorded as P18: the union of `TIER1_BRANCHES` (`name_validation.py:190-309`) and
`COMPANY_TIER1_BRANCHES` (`:371-438`) is exactly ten `branch_id`s; the floor mapped to SIX of them
(`rfc2822_leak`, `arrow_connective`, `me_to_prefix`, `path_hostile`, `archive_prefix`,
`unknown_contact`), omitting `calendar_prefix`, `email_chars`, `pure_digit` and `empty` — and round 6's
own `why:` claimed the pre-fold floor covered "eight of the ten" when the true prior count was four.

*Why the omission had teeth rather than being a tidiness complaint.* None of AC-3's three assertions
reads the package's branch table; they check the census and the manifest against EACH OTHER. So a
conductor authoring the census works from this document's own class list, never thinks to measure
`Dave -`/`Me -` calendar prefixes as a class distinct from the arrow one sitting beside it in the
code, writes rows for the classes named, and every assertion goes green over a corpus carrying no
specimen for four of the package's ten refusal branches — which is exactly the "a class measured at
zero is a row the conductor writes, not a row that may be omitted" property assertion (iii) exists to
guarantee, defeated because the floor never named the shape for the census to measure.
`calendar_prefix` carries a consequence past coverage: it is the sole source of `CONNECTIVE_SET`'s
frozen `Dave` member, which AC-5(b) justifies by citing `:226-236`'s `Dave - Thomas Gatten` specimen
as live prefix vocabulary — so the corpus could ship with nothing exercising the branch that member's
own justification names.

*The fix removes the transcription rather than pruning the fourth omission, and it is the move this
document already makes twice elsewhere.* AC-3's floor is now SPLIT: the branch half is READ at test
time from `{record.branch_id for record in TIER1_BRANCHES + COMPANY_TIER1_BRANCHES}` — the same
runtime read of an exported declaration AC-2 performs on `TYPE_TO_MODEL` and AC-4 on `_skip_reason`'s
codomain, and the same sweep unit `tests/test_name_gate.py:212` and
`tests/test_company_name_contract.py:369` already use — so a branch added to either table later joins
the floor automatically and no future round can find the floor sampling the branch table. Only the six
shape classes that have NO branch (diacritics, hyphenated surnames, whitespace damage, stem/name
divergence, same-name collision, postal-address leak) stay hand-listed, because there is nothing to
derive them from, and only those six carry the pre-origination naming reconciliation. **The key is
`branch_id` and never `pattern`**: `arrow_connective`, `calendar_prefix` and `me_to_prefix` all raise
the shared pattern `calendar_prefix` (`:216`, `:228`, `:240`, said outright in the dataclass docstring
at `:152-154`), so a pattern-keyed derivation would silently re-merge three classes AC-3 treats as
separate. This is LESSONS #45 verbatim — a registry validated only against itself is a mirror, not a
census; ship the reality-diff as a floor check — and it costs nothing in satisfiability, because the
MEASURED/ABSENT split round 3 introduced already lets a branch the live vault does not carry discharge
honestly with a zero row and no specimen. `empty` is the likely such row and is named as one: its
guard (`create_stub`'s `if name and name.strip():`) means it has never fired in production.
`## Write Targets` gains the matching charge — one class-table row per `branch_id`, with the four
previously-omitted ones spelled out, since the conductor is the reader who would otherwise not know to
look for them.

*The two non-blocking notes are folded with it, both being the same "stated number vs. actual list"
family.* P16 said "fifteen regexes — the ten in `name_validation.py` and the five in
`name_cleaning.py`" and then listed ELEVEN for `name_validation.py`; the enumeration was complete and
only the total was wrong, so the count is corrected to sixteen everywhere it appears and the union
answer is untouched. And `re.IGNORECASE` turns out to be on EIGHT of the sixteen rather than one
(`name_cleaning.py:46`, `:54`, `:55`, `:56`, `:57` and `name_validation.py:82`, `:110`, `:113`; `:74`
not), so AC-5(b)'s "the ONE branch whose answer the code does not settle" is restated as the one cell
this repository's committed SPECIMENS leave open — which is what the evidence actually shows: a
case-insensitive Grep over every `*.py` finds the three prefix branches spelled canonically in every
hit with no `ME`/`DAVE` variant anywhere, the opposite of P15's finding for `unknown_contact`. The
remedy needed no widening: AC-5(b)'s reconciliation was already written general to any furniture class
whose measured profile puts a capitalized non-name run into an identity position. P17 is added
recording, with its predicate, that no regex anywhere else in the package carries furniture — a claim
P16 asserted as prose and which is now a measured premise so a later round does not re-derive it. No
premise moved, no criterion was weakened, the approach is untouched, and AC-5 is unchanged in what it
demands.

**Revised an eighth time 2026-09-07 after architect round 8 and AC red-team round 7 (both REVISE,
fences at the foot of this doc; TWO findings, one from each gate, of DIFFERENT families and neither
overlapping the other — and one of them is the first blocking finding in this document's history that
is not about an enumeration at all).** Both gates confirmed round 7's fold closed and each
re-verified it against the code rather than against the fold's prose: the ten `branch_id`s, the
`branch_id`-not-`pattern` key and its docstring at `name_validation.py:152-154`, the four exported
`BaseRepository` subclasses and their `type_name`s, and AC-1's byte-copy / digest /
planted-discriminator mechanism, which has now drawn no finding in eight rounds. Every code fact
below was verified here independently rather than inherited from either gate's prose.

*Finding 1 (AC red-team, CRITICAL) — the artifact two criteria treat as ground truth is frozen by
nothing, and it is the first finding here that is not an enumeration defect.* AC-3(iii)'s class floor
and AC-5(c)'s pool provenance delegate their ENTIRE oracle to `docs/vault-shape-census.md`, because
the suite is hermetic and can re-derive neither a live-vault count nor a non-occurrence scan.
`## Write Targets` frames it as a WI-300 precondition landing in HEAD before Dave signs — a framing
that silently assumes it stays what the conductor wrote. Nothing enforced that. The in-tree half is
already measured and its consequence had simply never been drawn: `pipeline-runners.yaml:34-38`
declares `docs/**` writable in full, with no carve-out for a landed precondition (P7). The
out-of-repo half is recorded with its currency stated as P19 — the pipeline's one merge-boundary
integrity wall over docs is scoped BY DESIGN to files carrying work-item frontmatter and explicitly
treats a shared non-work-item doc's edit as ordinary legitimate build traffic, which this artifact is,
carrying no `id: WI-*` of its own. So a builder spawn could edit a MEASURED row in place to
`status: ABSENT` with count `0`, drop the awkward specimen, and watch every AC-3 assertion go green:
(i) is scoped to MEASURED rows so the row exits the equality, (ii) is satisfied by construction
because the builder wrote exactly the shape it demands, and nothing re-derives the count because
nothing can. AC-5(c) is the worse half — a fabricated pool row certifies a scan nobody ran, and
`## Intent`'s one sentence about Dave's contacts' real names has no machine check behind it at all.
**The fix is this item's own AC-1(a) applied to the artifact it was never applied to** — "frozen
without a mechanism is a wish" — with the one difference that decides whether it works: the expected
digest lives in the SIGNED CRITERION (AC-3(iv)'s `CENSUS_DIGEST`, filled at the same one-time
pre-origination edit that already reconciles AC-3's six shape classes and `CONNECTIVE_SET`, then
frozen by Dave's signature), never in `tests/fixture_vault.py`, because a constant the build owns is
updated in the same commit that edits the file it digests. AC-5(c) asserts the same fixity rather
than inheriting it, since each criterion's `check:` is its own test function and an unguarded AC-5 is
the worse of the two exposures. `## Write Targets` gains the matching conductor charge — land the
file, then take one digest before Dave signs — with the ordering consequence named: a correction
before the digest is free, a correction after signature costs a D4b re-sign.

*Finding 2 (architect, blocking) — round 7's document-wide sweep was itself done by SAMPLING, one
enumeration per CRITERION rather than one per ENUMERATION.* It stopped at AC-2 because AC-2's
*population* was already derived from `TYPE_TO_MODEL`; AC-2 held two more. Verified here against the
code: `ENTITY_BODY_CONFIG` (`body_sections.py:303-324`) keys exactly `person`, `company`, `meeting`,
`book`, `exploration`, so the narrowing arm's hand-listed `watch`, `explore`, `gift-idea` is exactly
`set(TYPE_TO_MODEL) - set(ENTITY_BODY_CONFIG)` and is now derived; and GATE-CLEAN was defined as four
named corruption forms when the door applies the WHOLE chain — `validate_strict` over all ten
`TIER1_BRANCHES` for `person` (`name_gate.py:361-363`) and all five `COMPANY_TIER1_BRANCHES` for
`company` (`:340-341`), a pass-through for the other six (`:319-344`) — omitting `email_chars`,
`calendar_prefix`, `archive_prefix`, `unknown_contact`, `pure_digit` and `empty`. GATE-CLEAN is now
stated as the door's own predicate (`Tier1Branch.matches`, `name_validation.py:179-184`) with the four
kept as examples. **Both instances fail LOUD with no green-over-wrong route, and that is stated
rather than inflated** — they cost a build round, not a property, which is what separates this round
from rounds 4 through 7. They are blocking anyway for the reason the architect gave, and it is the
right one: not their own cost, but the document-wide exhaustiveness claim and four-item residue list
they falsified, which Dave's pending sufficiency ruling reads as true. Both are corrected IN PLACE
above, marked as corrections rather than quietly rewritten, because a paragraph Dave's ruling rests
on should show that it was wrong once.

*Six non-blocking notes are folded with them, all one-line and all cheap while these are drafts.*
AC-4's "that asymmetry is itself checked" was a tautology — `A - B == A - B`, both sides derived, no
declared expected value — and is dropped, since a fifth repository is already caught by the derived
sweep proper and the clause was this criterion's own counterexample to the rule it states three
sentences later. AC-4 also pins WHICH read is meant (the exported names in `repositories/__init__.py`,
deterministic, never `BaseRepository.__subclasses__()`, whose answer depends on import order) and
records that `type_name` is an abstract `@property` (`base.py:189-193`) readable off an INSTANCE, so
each repository is instantiated before the manifest's key set is compared — ordering legs (a) and (c)
do anyway. AC-3's floor gains its REVERSE direction (a branch-shaped census row naming a `branch_id`
the package no longer declares is now RED rather than surviving as an ABSENT phantom — LESSONS #45
calls a deliberately one-directional check an open defect, not a note), gains one sentence naming the
recurring cross-cage cost the derived floor reintroduces (a new Tier-1 branch reddens the suite and
can only be discharged by a conductor pass; that is #45's intended friction, not weakened, but written
down so the next branch author is told rather than surprised), and drops one overclaimed word: a
deduped floor writes one row per `branch_id` and the corpus carries one specimen, whose DECLARED TYPE
decides which table `gate_write` consults, so a person-typed specimen does not "exercise the company
arm as well". That is not a coverage hole — the company table has its own in-tree refusal sweep over
every record's `specimen` and `negative_specimen` (`tests/test_company_name_contract.py:359-459`,
read here) — so the sentence now says affirmatively that the company arm is out of this corpus's
scope. And LESSONS #46 is folded across all three derived populations: `TYPE_TO_MODEL` (8), the
`branch_id` union (10) and the repository set (4) are each asserted NON-EMPTY and against their size
at the moment of writing, because a derived read returns green when it works and green when it
silently reads nothing — an empty tuple, a renamed attribute, a subclass read taken before its module
was imported — and a size assertion is the cheapest available form of having seen a derivation red.
Those sizes are the POPULATION's and never an oracle: what each member must parse to, refuse, or own
stays hand-declared, which is the line `## Where the structure lives` draws.

No premise moved, no criterion was weakened, and the approach is untouched for an eighth round. AC-1
drew no finding from either gate.

**Revised a ninth time 2026-09-07 after architect round 9 and AC red-team round 8 (both REVISE, fences
at the foot of this doc; ONE finding, found INDEPENDENTLY by both gates over the same code read — the
first time in this document's history that the two gates converged on a single defect from different
directions, which is itself the reason it is folded by creating a declaration rather than by pruning a
sentence).** Both gates confirmed round 8's fold closed and each re-verified it against the code:
`TYPE_TO_MODEL`'s eight against `ENTITY_BODY_CONFIG`'s five and the `{watch, explore, gift-idea}`
difference; the door's three arms at `name_gate.py:319`, `:340-341`, `:344` and `:361-363` with
`writer.py:252-253` reading `declared_type` off the POST-merge frontmatter; the ten `branch_id`s over
both Tier-1 tables; the four exported repositories and `_owns`/`_note_skip`'s double-ownership rule.
The architect additionally attacked round 8's own new mechanism on a lifecycle case no round had
tried — a post-landing conductor refresh of the census after WI-016 closes — and reports it survives
in both phases: `_forged_nondriven_docs` still refuses a caged builder's edit to the driven work-item
doc while leaving a shared non-work-item doc as ordinary build traffic, and the `ac_hash` currency
check is scoped to `to_stage == "ready"`, so refreshing the digest on a closed item costs no linter
RED. **That check is recorded here as INHERITED rather than re-derived** — it reads out-of-repo
pipeline tooling, which P19's currency caveat already covers — so a tenth round knows which half of
it is this document's own measurement and which half is a gate's report.

*The finding (both gates, CRITICAL/blocking) — AC-4 placed `_skip_reason`'s reason set on the DERIVED
side and stated a consequence only a derivation delivers, over a codomain the package does not
declare.* Measured here rather than taken from either gate's prose, and recorded as P20: the three
strings exist in `obsidian_schemas/` ONLY as bare return literals at `repositories/base.py:44`, `:46`
and `:47`, plus a type comment on `SkippedNote.reason` at `:37`; no frozenset, tuple, dict or `Enum`
exports them; `repositories/__init__.py`'s `__all__` carries the repositories and one exception and
nothing else. So both sides of AC-4's equality were hand-typed — the manifest's declared reasons and a
set typed into the harness, which is what `tests/test_loud_fail_load.py:187-188` already does today —
and the criterion's "a fourth reason added to the package later fails until it has a specimen" was
false. **A green-over-wrong route, which is what makes it heavier than round 8's two:** a builder adds
a fourth `_skip_reason` arm (`PermissionError` → `unreadable-permission`, say), the corpus carries no
specimen for it, the manifest declares none, the hand-typed expected set never moves, and AC-4 is
GREEN while the new failure class joins the corpus's blind spot — which is the exact vanishing note
WI-020 built `SkippedNote` to end (`base.py:29-34`), one layer above where WI-020 ended it.

*The fold, and why it is the more expensive of the two offered routes.* Both gates offered the same
pair: export the codomain, or keep it hand-written and delete the false consequence. The demotion is
rejected on the residue list's own membership test — that list is for things with NO DECLARATION TO
READ, and its other four members earn it by SUBJECT (all judgment), while which strings `_skip_reason`
can emit is mechanical. Parking a mechanical fact on the judgment list would cost this document's
organising distinction more than the fix costs. So the build CREATES the declaration: a module-level
`SKIP_REASONS` frozenset in `repositories/base.py` whose members `_skip_reason` returns by name — one
frozenset, inside `write_authority` (P7), and this item's only package change — read by AC-4 exactly
as AC-2 reads `TYPE_TO_MODEL`. **The export alone is deliberately not trusted, and that is the part of
this fold to keep.** `TYPE_TO_MODEL` cannot drift because dispatch depends on it; a `SKIP_REASONS`
nothing consumes can, and a criterion that read it and stopped would have re-created the same false
consequence in better-looking words — the fold breeding its own next finding, which this document has
recorded three times. So one `ast` scan lands in `tests/derivations.py` (the standing shared scan
module, the only file permitted to name `ast`, P9) returning the string values `_skip_reason`'s own
body can return, asserted EQUAL to `SKIP_REASONS` — equality rather than containment, because that is
what makes the scan's own silent under-read report RED instead of green (LESSONS #46). The residue
list and `## Approach`'s derived-side list are corrected in place to match, and the round-8
falsification condition is flagged as having FIRED, with the three counter-considerations recorded
beside it, in the marked blockquotes above.

*Two non-blocking notes are folded with it.* AC-3(iv)'s "exactly ONE such declaration was found" is
now FENCE-SCOPED rather than file-wide — every gate section in this document quotes the criterion text
it reviews, so once `CENSUS_DIGEST` holds a real 64-hex value a single later quotation would turn a
file-wide uniqueness read RED and the only remedy would be editing a historical gate section. And
AC-4's `repositories/__init__.py:8-20` cite was off (imports end at `:12`, `__all__` is `:14-21`); it
is corrected, with one clause saying the export list is FILTERED rather than iterated whole, because
`__all__` also carries `VaultPathNotConfiguredError` — an exception, not a repository.

No premise moved, no criterion was weakened, and the approach is untouched for a ninth round. AC-1 has
now drawn no finding in nine rounds, and AC-5 none in five.

### The AC-5 sufficiency question — recorded for Dave's ruling at sign-off

AC red-team round 3 declined to spend a fifth fold without a ruling from Dave, and it is right that
the question belongs to him rather than to a gate. Recorded here so a later cold-start gate routes
against the ruling instead of re-litigating it. **The question:** is a fully structural,
machine-checked name-closure wall the right bar for AC-5, or should AC-5 fall back to the simpler
mitigating control the red-team's own round-1 finding named as the alternative — a required human
review step tied to a criterion?

**The recommendation, for Dave to accept or overrule: keep the structural wall, because the two
options are not actually alternatives.** AC-5's ground truth has been the human control since the
round-1 fold: the suite is hermetic and cannot read the live vault, so what certifies that a token
names no real person is the conductor's recorded scan and a person's one-time review of a few hundred
declared tokens. The structural wall is not a substitute for that review — it is what forces every
name in the corpus THROUGH it, and its measurable value is the shrink: a reviewer reads a few hundred
declared identity tokens once, rather than fifty notes of free text on every change. Drop the wall and
the review does not get simpler; it gets bigger and recurring, and it becomes the "reviewable by eye"
aside that the red-team's round-1 finding was raised against in the first place.

**What has to be true for that recommendation to hold, stated so it is falsifiable.** The four rounds
of defects have all been in one family — a mandatory obligation over a set the builder does not
author — and this fold removes the family's generator rather than its latest member. If a fifth
independent round finds a defect of the SAME family after this fold, the recommendation is wrong and
the fallback should be taken. If it finds something else, that is ordinary criterion review. Dave may
also rule the middle path: freeze AC-5 at legs (a), (d) and (e) — the reserved-range, phone-property
and hermeticity walls, none of which has ever been found defective — and demote (b) and (c) to a
declared human-review criterion. That is a smaller, certainly-satisfiable AC set; the cost is that a
real name entering an identity position becomes a thing a person has to notice rather than a thing
the floor goes RED on.

**The test has now been run, and it came back clean — recorded here because the recommendation above
staked itself on it.** Two independent cold-start rounds (architect 5, AC red-team 4) went looking for
a fifth instance of the family — a mandatory obligation over a set the builder does not author — and
both reported there is none: `CONNECTIVE_SET` is frozen by literal enumeration with no occurrence
demanded, `NAME_POOL`'s non-vacuity is over a set the builder authors, `PROSE_ALLOWLIST` carries only
a disjointness constraint, the org-suffix admission imposes nothing, and the census tables are now read
by containment or by status-conditional assertions. What they found instead was one enumeration that
did not match its own stated rule — a finite gap over a fixed, enumerable surface (every field of every
`TYPE_TO_MODEL` member), now exhausted by P14 rather than sampled. Under the falsification condition as
written, that is ordinary criterion review and the recommendation stands: keep the structural wall.
Dave still owns the ruling, and the middle path (freeze AC-5 at legs (a), (d), (e) and demote (b)/(c)
to a declared human-review criterion) remains available and is the thing to take if a later round finds
another field the rule does not decide — that, and not this round's finding, would be the signal.

**Round 6's datum, recorded honestly and including the part that cuts against the recommendation.**
Both gates declined to rule and both were right to; both left a datum. *Architect's* is the harder
one and is not softened here: this is now the **second consecutive round** in which a set AC-5 declares
was "enumerated by sampling rather than by its own rule" — round 5 in the identity-position list over
`models.py`, round 6 in `CONNECTIVE_SET` over the furniture regexes — and each was closed only when
its surface was read exhaustively. That is a second instance of a family, which is the shape the
falsification condition was written to watch for, even though it is not the family the condition
NAMES (round 4's generator: a mandatory obligation over a set the builder does not author, which both
rounds again confirmed absent). *The AC red-team's* is the mitigating one and is also not
overstated: it declined to flag the regress signature, reading round 6's defect as narrower than
rounds 4-5's — not a surface needing exhaustive re-reading, but **one sentence pinning down an
extraction rule the document already stated and never disambiguated**, a closable gap in the
criterion's own determinism. Both readings survive the fold, so both are recorded rather than
reconciled. **What is done about it, and it is the only thing a gate can do:** the rule both closures
needed is now written INTO AC-5 as a standing instruction — every set AC-5 declares is enumerated by
applying a stated rule to a NAMED, ENUMERABLE surface — and the two surfaces are now exhausted and
recorded as P14 (every declared field of every `TYPE_TO_MODEL` member) and P16 (all sixteen regexes,
both Tier-1 tables), so a seventh round has nothing left to discover on either. **What that means for
Dave's ruling, stated plainly:** the recommendation above still stands on its own argument — the wall
and the human review are not alternatives, and the wall's value is the shrink in what a person reads —
but the honest count is now four rounds of the removed generator plus two of "sampled, not derived",
and if a seventh independent round finds a third instance of the second family, the middle path
(freeze AC-5 at legs (a), (d), (e); demote (b) and (c) to a declared human-review criterion) is the
one to take. Two rounds of a family that is finite over surfaces now exhausted is not that signal
yet; a third, over a surface this document claims to have exhausted, would be.

**Round 7 IS the predicate that paragraph named, and both halves of what that means are recorded
here rather than resolved, because the ruling is Dave's.** *The half that supports taking the middle
path:* this is a third consecutive round in which an enumeration in this document turned out not to
be its own named surface's output — round 5 the identity-position list over `models.py`, round 6
`CONNECTIVE_SET` over the furniture regexes, round 7 AC-3's class floor over the Tier-1 branch
tables — and the third arrived over a surface P16 had claimed to exhaust, found by re-reading
`TIER1_BRANCHES` rather than by reading the fold. Both gates named the pattern plainly and neither
ruled on it. *The half that cuts the other way, and it is not a softening:* **this instance is in
AC-3, and the middle path would not have touched it.** The option offered to Dave — freeze AC-5 at
legs (a), (d), (e) and demote (b) and (c) to a declared human-review criterion — removes nothing
that was defective this round. AC-5 drew no finding: both of the architect's AC-5 observations were
non-blocking notes about a stated count and a flag's reach, both folded, neither changing what the
criterion demands. So the honest reading is that the family was never AC-5's specifically. It is
this document's habit of HAND-TRANSCRIBING an enumeration that the tree DECLARES, and cutting AC-5's
scope does not touch that habit anywhere it lives.

**What was done about it, and it is structural rather than another instance-prune.** The standing
instruction AC-5 already carried — every set is enumerated by APPLYING a stated rule to a NAMED,
ENUMERABLE surface — was applied in ONE pass to every enumeration in this document that quantifies
over a declared, in-tree surface, instead of one per round: AC-3's class floor is now a runtime read
of `branch_id` over both Tier-1 tables; AC-4's repository set is now a runtime read of the exported
`BaseRepository` subclasses, an instance NEITHER GATE NAMED and which was found by asking the
question of every criterion rather than of the one under review; AC-2 was already derived from
`TYPE_TO_MODEL`, and AC-4's reason set was taken to be already derived from `_skip_reason`'s codomain
— **FALSE, found at round 9 and corrected in the second blockquote below: there is no declared
codomain to derive from (P20), so that clause named the one population on this list that had never
been derived at all**; and the org-suffix admission
was already read from the package. **What remains hand-written is now exactly the set of things with
no declaration to read**, and each is named so a later round can check the claim instead of
rediscovering it: AC-3's six shape classes (diacritics, hyphenated surnames, whitespace damage,
stem/name divergence, same-name collision, postal-address leak — no branch declares any of them),
AC-5(b)'s identity positions (whether a field's value IS a person's or an organisation's name is a
judgment, not a declaration — reconciled field by field and recorded as P14), `CONNECTIVE_SET` (the
regexes declare patterns, not token lists — the rule is applied by hand and recorded as P16/P17),
and AC-4's ownership oracle (hand-written ON PURPOSE, because an expected value read from the code
under test agrees with the regression it exists to catch). Three of those four are on the judgment
side of the determinism boundary by construction and the fourth is a deliberate oracle; none is a
transcription of a list the tree holds.

> **CORRECTED AT ROUND 8, and the correction is recorded in place because Dave's pending
> sufficiency ruling reads this paragraph as true.** The claim above is FALSE as written, and the
> reason is that the "ONE pass over every enumeration" was itself done by SAMPLING: it swept one
> enumeration PER CRITERION and stopped at AC-2 because AC-2's *population* was already derived from
> `TYPE_TO_MODEL`. AC-2 held two more hand-transcribed enumerations over surfaces the tree declares
> — its narrowing arm hand-listed `watch`, `explore`, `gift-idea` where
> `set(TYPE_TO_MODEL) - set(ENTITY_BODY_CONFIG)` computes it, and it defined GATE-CLEAN as four
> named corruption forms where the door applies all ten `TIER1_BRANCHES` for `person` and all five
> `COMPANY_TIER1_BRANCHES` for `company`. So the residue was SIX things, not four, and two of them
> did have a declaration to read. Both are folded (round 8, below) and the four-item list above is
> now true of the document as it stands; it was not true when it was written.

> **CORRECTED AGAIN AT ROUND 9, and this correction is different IN KIND from round 8's — recorded
> in place for the same reason, that Dave's pending sufficiency ruling reads this paragraph as
> true.** There was a SEVENTH: `_skip_reason`'s reason set, which `## Approach` listed on the DERIVED
> side beside `TYPE_TO_MODEL` and the repository set, and over which AC-4 asserted "the sweep stays
> derived from the classification's own codomain". **The package declares no such codomain** — the
> three strings are bare return literals at `repositories/base.py:44`, `:46`, `:47` plus a type
> comment at `:37`, and nothing anywhere exports them (P20, measured this round; both round-9 gates
> found the same fact independently, from a duplication angle and from a
> satisfiable-with-nothing-real-behind-it angle). So it was MISFILED rather than merely missed: as
> the list was then framed it belonged on neither side. Both sides of AC-4's equality were hand-typed,
> which made its stated consequence — "a fourth reason added to the package later fails until it has
> a specimen" — false; and unlike round 8's two instances this one had a GREEN-over-wrong route, since
> a fourth `_skip_reason` arm would have left every leg green with the new failure class sitting in
> the corpus's blind spot, which is WI-020's own `SkippedNote` failure reappearing one layer above
> where WI-020 closed it.
>
> **The disposition is what changes the shape of the list, so it is stated rather than left to be
> inferred.** The other four residue members earn their place by SUBJECT — whether a field's value IS
> a name, what a shape class should be called, what a repository OUGHT to own — all judgment, all on
> the far side of the determinism boundary. Which strings `_skip_reason` can emit is MECHANICAL, so
> demoting it into the residue and deleting the false consequence — the honest cheap option, and the
> one both round-9 gates offered — would have parked a mechanical fact on the judgment list and left
> this document's organising distinction meaning less than it says. It is fixed the other way instead:
> **this item's build CREATES the missing declaration** — a `SKIP_REASONS` frozenset in
> `repositories/base.py`, the item's one line of package change, bound to `_skip_reason`'s own returns
> by a single `ast` scan in `tests/derivations.py` so the export cannot drift from the function — and
> AC-4 then reads it as AC-2 reads `TYPE_TO_MODEL`. After that fold the residue is again the FOUR
> named above, and the sentence they qualify is now true in a stronger sense than before: what remains
> hand-written is the set of things with no declaration to read AND none worth creating.

**What that means for the ruling, stated so Dave can overrule it in one sentence.** The
recommendation still stands on its own argument — the wall and the human review are not
alternatives, and the wall's value is the shrink in what a person reads — and the count is now four
rounds of the removed generator, plus three of "hand-transcribed, not derived", of which the third
was outside AC-5 entirely and the remedy for which is now applied across the whole document rather
than to the criterion that happened to carry the instance. If Dave takes the middle path anyway,
**this round's fix still has to be folded**, because AC-3 and AC-4 are not the parts the middle path
removes. And the falsification condition worth carrying forward is now sharper than the one written
at round 4: the signal to watch is not another finding in AC-5, it is a NEW hand-transcribed
enumeration appearing in this document over a surface the tree declares — which, after this pass,
there is no remaining instance of to find.

> **CORRECTED AT ROUND 8.** The clause after the dash was wrong: there were two remaining
> instances, both in AC-2, found by asking the question of every ENUMERATION rather than of every
> CRITERION. The falsification condition itself is kept — it is the right thing to watch — but the
> claim of exhaustion attached to it is withdrawn and replaced by a checkable one: the round-8 pass
> enumerated the enumerations, criterion by criterion and clause by clause, and the residue is the
> six things named in the corrected paragraph above. A ninth round finding a seventh is the signal;
> that the claim of exhaustion has now been wrong once is itself a datum for Dave, recorded in the
> sufficiency section rather than argued here.

> **THE SIGNAL FIRED, ROUND 9, AND IT IS FLAGGED HERE RATHER THAN BURIED SO DAVE'S RULING IS NOT
> LOOKING FOR IT.** The ninth round found a seventh, both gates found it independently, and the
> falsification condition this document set for itself is therefore MET on its own terms — the
> claim of exhaustion has now been wrong twice. Three things about the seventh are recorded beside
> that, because they are what the condition could not encode and they cut in the other direction.
> (1) It is not the same defect the previous six were: those were enumerations TRANSCRIBED from a
> declaration the tree already held, and this one had no declaration to transcribe from — it is the
> only member of the family whose remedy is to WRITE the declaration, so the "look for another
> hand-transcription" search is genuinely exhausted even though this instance existed. (2) It is in
> AC-4, which is the THIRD consecutive round (7 in AC-3, 8 in AC-2, 9 in AC-4) in which the family
> surfaced in a part of the document the middle path does not touch — AC-5 has now drawn no blocking
> finding for five consecutive rounds. (3) Seventeen gate rounds have produced no finding against the
> APPROACH; every one has been against criterion text or the evidence under it, and both gates have
> ruled the approach sound at every pass. The item's declared `round_budget` is 12 and sixteen have
> run. The ruling is Dave's and nothing here pre-empts it; what this fold does is take the one-line
> fix rather than buy a tenth round hunting an eighth instance.

**Round 8's datum, recorded in both directions like every round before it, and it is the roundest
one yet.** *The half that supports the middle path:* this is a FOURTH consecutive round in which an
enumeration in this document turned out not to be its own named surface's output, and the first in
which the missed enumeration sat inside the pass that claimed to have swept them all — the sweep was
itself a sample. That is the second time an exhaustion claim in this document has been wrong, and it
is fair for Dave to weigh that the claim of exhaustion is the thing that keeps not holding. *The half
that cuts against it, and it is larger this round than at any point before:* (a) both enumeration
instances are in AC-2, which the middle path does not touch at all, so for the SECOND consecutive
round the family surfaced outside the part that option removes — which is the strongest available
evidence that the family was never AC-5's; (b) **both fail LOUD, with no green-over-wrong route** —
a first, since every prior instance of this family let a green suite ship something wrong, while
these cost a build round; and (c) both sit in ORIGINAL criterion text no fold has ever touched, so
this round is not a fold breeding its own next finding — the folds have converged and what is left is
the original draft's residue. *And a datum of a different kind, which is the one worth Dave's
attention most:* **round 8's critical finding was not an enumeration defect at all.** It was that the
artifact AC-3 and AC-5(c) both trust as ground truth had no integrity check anywhere in this
pipeline, which is a wall-with-an-unguarded-escape-hatch of the shape AC-5 has been hardened against
five times — one layer out, in the ground truth rather than in a clause. That finding argues FOR
keeping the structural wall rather than against it: the middle path demotes exactly legs (b) and (c),
and (c) is the leg whose ground truth this round turned out to be forgeable. Demoting it to human
review would have left the forgeable ledger in place with nothing but a reader's attention behind it —
which is the "reviewable by eye" control AC-5's own `why:` was raised against at round 1. On this
round's evidence the recommendation is unchanged and slightly stronger: keep the structural wall, and
note that the fix it needed came from applying this item's OWN AC-1(a) mechanism to an artifact
nobody had pointed it at. The ruling remains Dave's, the middle path remains available, and if he
takes it, round 8's fixes still have to be folded — AC-2, AC-3(iv) and AC-4 are not what it removes.

**Round 9's datum, recorded in both directions like every round before it, and it is the one that
closes the series.** *The half that supports the middle path:* the falsification condition round 8
wrote for itself — "a ninth round finding a seventh is the signal" — FIRED, and the claim of
exhaustion has now been wrong twice. Dave asked for a checkable condition, and it is fair to hold the
document to it as written. *The half that cuts against it, and it is the strongest it has been:*
(a) the seventh instance is in AC-4, making it the THIRD consecutive round in which the family
surfaced outside the part the middle path removes — round 7 in AC-3, round 8 in AC-2, round 9 in
AC-4 — which is now decisive evidence that the family was never AC-5's, and cutting AC-5's scope
buys nothing against it; (b) AC-5 has drawn no blocking finding in five consecutive rounds; and
(c) the seventh is not the same defect as the previous six. Those six were transcriptions of lists
the tree already declared, and the search for another such transcription really is exhausted — this
one had NO declaration to transcribe, which is a different failure needing a different remedy (write
the declaration) and not a further instance of the search that keeps coming up short. *And the datum
of a different kind:* both gates found this defect INDEPENDENTLY, from a duplication angle and from a
satisfiable-with-nothing-real-behind-it angle, which is the first decorrelated confirmation in
seventeen gate rounds (architect ×9, AC red-team ×8). Across all seventeen, every finding has been against criterion text or the
evidence under it and NONE against the approach, which both gates have ruled sound at every pass. The
declared `round_budget` is 12 and sixteen have run. On this round's evidence the recommendation is
unchanged — keep the structural wall — and the cheapest remaining path is to take this fold and
originate rather than to buy a tenth round hunting an eighth instance.

### Data premises, measured (predicate + currency stated so each is re-runnable)

Currency for P1–P18 and P20: **the tree as this drive seeded it** — git HEAD `821177f` plus the seeded
uncommitted delta (WI-022's build: `name_gate.py`, `name_validation.py`, `repositories/company.py`,
`tests/test_name_gate.py`, `tests/test_company_name_contract.py`, `tests/derivations.py`), at
`/…/cage-wt-pul8uspy/tree`. Reader tools: Read / Grep / Glob, no shell. **P19 is the one premise
whose subject is NOT this tree** and its currency is stated in its own row, because the pipeline
tooling it measures lives outside this repository and pins to no HEAD a later reader of this document
can re-run against; its in-tree half is P7, which is re-runnable here and is what the fix actually
rests on.

| # | Predicate | Result |
|---|---|---|
| P1 | `Glob tests/**` and `Glob tests/**/*.{md,yaml,yml,json,txt}` | 32 files, **all `.py`**; the second glob returns **nothing**. Zero fixture data files, no `tests/fixtures/` directory. |
| P2 | `Glob **/conftest.py` | **None anywhere in the tree.** `tests/derivations.py:11-12` states this as load-bearing. Every vault is built by a per-file private helper. |
| P3 | `rg 'type: (person\|company\|meeting\|book\|watch\|explore\|gift-idea\|exploration)'` over `tests/` | **83 occurrences across 13 files.** Anchored at line start (`^type:`) it is 26 across 3 — `test_repositories.py` 15, `test_parser.py` 7, `test_writer.py` 4; the other 57 sit indented inside triple-quoted heredocs. |
| P4 | `rg 'Exploration\|exploration'` over `*.py` | **13 hits, all in the package** (`models.py`, `__init__.py`, `body_sections.py`). **Zero under `tests/`.** The model is committed, wired and untested. |
| P5 | `TYPE_TO_MODEL` vs `ENTITY_BODY_CONFIG` membership | **8 vs 5.** `models.py:309-318` declares person, company, book, watch, explore, gift-idea, meeting, exploration; `body_sections.py:303-324` omits `watch`, `explore`, `gift-idea`, so `get_default_body` returns `""` for those three by construction (`:337-338`). |
| P6 | `_skip_reason` codomain | Exactly three, derived from the error TYPE: `malformed-frontmatter`, `schema-drift`, `unreadable` (`repositories/base.py:41-47`), surfaced by `skipped_notes()` / `skipped_count` (`:248-256`). **How that codomain is SPELLED — and whether anything declares it — is P20, added round 9; this row states the three members and was read as if it were a declaration, which it is not.** |
| P7 | `pipeline-runners.yaml:34-38` write_authority | `obsidian_schemas/**`, `tests/**`, `scripts/**`, `docs/**`. **`tests/fixtures/**` is builder-writable; a top-level `fixtures/` would NOT be** and would be silently reverted after the spawn. |
| P8 | `pyproject.toml:38-39` wheel packages | `packages = ["obsidian_schemas"]` — `tests/` is not packaged, so a corpus living there is **unreachable by HAL9000 / Exocortex / orchestrator** even after this ships. Consumers install `-e`, so they can reach the path on disk, but not by import. |
| P9 | Which walls a fixture module would disturb | The filesystem-single-homing wall scans `python_files_under(PACKAGE_ROOT, SCRIPTS_ROOT)` only (`tests/test_write_routing.py:91`) — **`tests/` is out of its scope**, so a byte-copy materializer under `tests/` is legal. But `ast` **is** single-homed across `obsidian_schemas/` and `tests/` to `tests/derivations.py` (`:14-17`, asserted by `tests/test_name_gate_wall.py`), so no fixture module may name it. |
| P10 | `rg 'José\|García\|Anne-Sophie\|Legrain\|Moises\|Vetup\|Sören'` over the tree | **38 hits across 8 files**, of which **36 are in `*.py`**: `test_wi126_body_preservation.py` 12, `test_repositories.py` 9, `test_name_validation.py` 5, `test_identity_index.py` 5, `test_name_cleaning.py` 4, `obsidian_schemas/name_cleaning.py` 1. (Corrected 2026-09-07: the summary previously read "35 in code" against a list summing to 36 — 35 is the five TEST files and the package hit makes 36. The per-file enumeration was and is exact; the data audit flagged the summary, and `## Problem / Motivation`'s own "35 literals scattered across five test files … plus one in `obsidian_schemas/name_cleaning.py`" was already correct.) The corruption corpus exists; it is just scattered and invisible to any test that did not type it. |
| P11 | `Grep 'Fwd\|Fw:\|Re:\|\bFw\b'` over the whole seeded tree (added round 4) | **One file: `docs/vault-fixtures.md`.** Zero hits in `obsidian_schemas/` and zero in `tests/`. Mail-header connectives are grounded in nothing in this repository; the package's connective vocabulary is `Dave\|Me\|My` (`name_cleaning.py:46`, `:54`, `:55`). This is why `CONNECTIVE_SET` is re-enumerated and its non-vacuity clause dropped. |
| P12 | Which model fields carry a PERSON or ORGANISATION name (`models.py`, read field by field, added round 4 — **partial; superseded by P14**, which is the complete pass over every declared field and adds `Watch.streaming_service` `:199`, `GiftIdea.source` `:243` and `Exploration.related` `:299`) | `Person.name` `:79`, `Person.aliases` `:80`, `Person.company` `:84`; `Company.name` `:128`; `Book.author` `:161`, `Book.publisher` `:166`; `Watch.director` `:195`, `Watch.recommended_by` `:200`; `Explore.source` `:224`; `GiftIdea.for_person` `:242` (alias `for`); `Meeting.attendees` `:261`. **`Meeting` declares NO `title` field** (`:259-263`) — AC-5(b)'s prior phrase "the company/meeting title fields" named a field the schema does not have. `Person.title` `:85` is a JOB title and carries no identity. `BaseEntity` adds only `type` and `tags` (`:39-40`). |
| P13 | `_GENERIC_ORG_SUFFIXES` and how the package compares it (added round 4, **corrected round 5**) | Exactly eight members — `support`, `ltd`, `inc`, `corp`, `group`, `team`, `limited`, `llc` (`name_cleaning.py:58`). The comparison is `words[-1].lower() in _GENERIC_ORG_SUFFIXES` at `:148`, `:185` and `:191` — `str.lower()`, **not** `str.casefold()`; round 4 wrote "casefolded", which the package nowhere does. The eight members are ASCII so the two agree on them, but the corpus carries non-ASCII specimens deliberately, so AC-5(b) now names `str.lower()` as the operation its own test performs. Derivable either way, so the org-suffix admission stays read from the package rather than hand-declared. |
| P14 | Every DECLARED field of every `TYPE_TO_MODEL` member classified against AC-5(b)'s rule (`models.py` read field by field, added round 5 — this is the reconciliation AC-5(b) instructs a later reader to perform, done once and recorded) | **`BaseEntity`**: `type` `:39`, `tags` `:40` — neither. **`Person`**: `name` `:79` ID, `aliases` `:80` ID, `company` `:84` ID; `emails` `:81` / `phones` `:82` / `whatsapp` `:83` / `linkedin` `:86` / `slack` `:87` → AC-5(a)'s reserved-range leg, not the name closure; `title` `:85` excluded (argued); `roles` `:88`, `birthday` `:89`, `created` `:90` — none. **`Company`**: `name` `:128` ID; `website` `:129` / `linkedin` `:131` → leg (a); `industry` `:130` NOT identity (a sector word — forcing it in manufactures the unsatisfiable-row shape); `created` `:132`. **`Book`**: `title` `:160` ID **by clause 2**, `author` `:161` ID, `publisher` `:166` ID; `isbn` `:165` / `source_url` `:168` → leg (a); `description` `:162` prose; `status` `:163`, `rating` `:164`, `publication_year` `:167`, `date_added` `:169`, `date_finished` `:170` — none. **`Watch`**: `title` `:193` ID by clause 2, `director` `:195` ID, **`streaming_service` `:199` ID (ORG — added this round)**, `recommended_by` `:200` ID; `media_type` `:194`, `year` `:196`, `status` `:197`, `rating` `:198`, `date_added` `:201`, `date_watched` `:202` — none. **`Explore`**: `title` `:222` ID by clause 2, `source` `:224` ID; `url` `:223` → leg (a); `subtype` `:221`, `status` `:225`, `created` `:226` — none. **`GiftIdea`**: `for_person` `:242` ID, **`source` `:243` ID (added this round, as `Explore.source`'s unglossed sibling)**; `date_added` `:244` — none. **`Meeting`**: `attendees` `:261` ID; `topics` `:262` excluded (argued); `date` `:260`, `meeting_id` `:263` — none; **no `title` field exists** (`:259-263`). **`Exploration`**: `title` `:295` ID by clause 2, **`related` `:299` ID — added this round; its docstring at `:280` glosses the list as `[[Other Exploration]], [[Person]], etc.`**; `origin` `:300` excluded (argued — a sentence, gloss at `:281`), `graduated_to` `:301` excluded (argued — `[[Project]]`, gloss at `:282`); `status` `:296`, `created` `:297`, `updated` `:298`, `abandoned_reason` `:302` — none. **Undeclared keys are outside this table by construction**: `model_config = ConfigDict(extra="allow", ...)` (`:31-32`) admits frontmatter keys no model declares, which is why AC-5(b) carries clause 3. `models.py` is the single home CLAUDE.md declares, so this is the whole declared surface. |
| P15 | `Grep -i '[Aa]rchived\|unknown\s+contact\|Unknown Contact'` over every `*.py` in the seeded tree — how does this package actually SPELL the two furniture literals AC-5(b)'s enumeration had sampled past? (added round 6) | **`archive_prefix`: five distinct specimen strings across eight sites, and every one of them puts the `z`/`zz` IMMEDIATELY against the capital with nothing between** — `"zArchived - Rosie Samuels"` (`tests/test_name_validation.py:229`, `:444`; `tests/test_name_cleaning.py:131`; `obsidian_schemas/name_cleaning.py:78` docstring), `"zzArchived - Someone"` (`:235`), `"zArchived Dave Smith"` (`tests/test_name_gate.py:94`; `name_validation.py:263` `specimen=`), `"Dave zArchived"` (`test_name_gate.py:95`, the `.match`-not-`.search` negative), `"zArchived Acme Corp"` (`name_validation.py:416` `specimen=`, company table). **Zero exceptions anywhere in the tree.** Under AC-5(b)'s pinned run rule that is one lowercase-initial run yielding NO token, so `archive_prefix` forces no `CONNECTIVE_SET` member and `Archived` is not one. **`unknown_contact`: BOTH casings are committed, and this is the one cell the code does not settle** — lowercase suffix form, six distinct strings (`test_name_validation.py:248`, `:254`, `:452`; `test_name_cleaning.py:135`, `:140`; `test_name_gate.py:97`; `name_cleaning.py:79` docstring), matching the recovery regex's own `\s+unknown\s+contact\b` shape (`:57`) and the branch's "WhatsApp scanner artifact" comment (`name_validation.py:112`); capitalized standalone form, one string across three sites (`test_name_gate.py:96`, `tests/test_lint_vault_fix_gate.py:58` as `REFUSED_STEM`, and `name_validation.py:274`'s own `specimen=`). Both branch regexes carry `re.IGNORECASE` (`name_validation.py:110`, `:113`), so the live vault — not the code — decides the casing, which is why AC-5(b) reconciles this one cell against the census rather than guessing it. |
| P16 | The COMPLETE furniture surface — every regex in this package that recognizes corruption furniture — with AC-5(b)'s pinned run rule applied to the literal spelling each one carries (added round 6; **count corrected round 7**, and this is the enumeration AC-5(b) previously sampled at three of sixteen) | **SIXTEEN regexes in two files, and there is no third table and no other recovery regex.** The round-6 draft of this premise said "fifteen — the ten in `name_validation.py` and the five in `name_cleaning.py`" and then listed ELEVEN for `name_validation.py`; the enumeration was complete and only the total was wrong, corrected here because a later reader checking "is this surface exhausted?" counts the list against the stated number. **`re.IGNORECASE` IS CARRIED BY EIGHT OF THE SIXTEEN, NOT BY ONE** (recorded because AC-5(b) called `unknown_contact` "the ONE branch whose answer the code does not settle", which is true of the COMMITTED SPECIMENS and not of the flag): all five of `name_cleaning.py`'s (`:46`, `:54`, `:55`, `:56`, `:57`) and three of `name_validation.py`'s (`:82` `_ME_TO_PREFIX_RE`, `:110` `_ARCHIVE_PREFIX_RE`, `:113` `_UNKNOWN_CONTACT_RE`) — while `name_validation.py:74` `_CALENDAR_PREFIX_RE` does NOT. So the code pins the live casing of `Me`/`My`/`Dave` furniture no more tightly than it pins `unknown contact`'s. What separates them is the corpus, not the flag, and it is measured: a case-insensitive Grep for `\b(me|my|dave)\s*(to |- |-> |→)` over every `*.py` in the seeded tree returns the canonical spelling in EVERY hit and **no `ME`/`MY`/`DAVE` variant anywhere** — the opposite of what P15 found for `unknown_contact`, which this repo commits both ways. AC-5(b)'s remedy needs no widening for it in any case: the reconciliation it carries is already general to "any other furniture class whose measured profile would put a capitalized non-name run into an identity position", and `## Write Targets` requires the census to record EACH class's furniture literal in its MEASURED casing, so a live `ME - X` form would be absorbed at the same one-time edit. `name_cleaning.py` (the recovery pass, five): `:46` `_CALENDAR_PREFIX_RE` `^(Dave\|Me\|My)\s*[-/]\s+` → `Dave`, `Me`, `My`; `:54` `_ARROW_PREFIX_RE` `^(Dave\|Me\|My)\s*[→⟶⇒➜↦⇨]\s*` → same three; `:55` `_ME_TO_PREFIX_RE` `^(Me\|My)\s+to\s+` → `Me`, `My` (no `Dave` alternative, P13); `:56` `_ARCHIVE_PREFIX_RE` `^z+Archived\s*-\s*` → **none** (lowercase-initial run); `:57` `_UNKNOWN_CONTACT_SUFFIX_RE` `\s+unknown\s+contact\b` → **none** (literal spelled lowercase). `name_validation.py` (the reject gate, **eleven**): `:66` `_RFC2822_LEAK_RE` → none (its run anchor requires `[a-z]`); `:74` `_CALENDAR_PREFIX_RE` `^(Dave\|Me\|My)\s*[-/]\s+\w+` → `Dave`, `Me`, `My`; `:82` `_ME_TO_PREFIX_RE` `^(Me\|My)\s+to\b` → `Me`, `My`; `:101` `_ARROW_CONNECTIVE_RE` → none (arrows and `->` are outside the extractor's class); `:107` `_PATH_HOSTILE_RE` `/` → none; `:110` `_ARCHIVE_PREFIX_RE` `^z+Archived\b` → **none**; `:113` `_UNKNOWN_CONTACT_RE` `unknown\s+contact` → **none from the code** (see P15 for the `IGNORECASE` residue); `:120` `_EMAIL_CHARS_RE` `[@]` → none; `:123` `_PURE_DIGIT_RE` → none; `:351` `_COMPANY_PATH_HOSTILE_RE` → none; `:445` `_DOUBLE_SPACE_RE` → none. The two Tier-1 tables carry no literal the regexes do not: `TIER1_BRANCHES` (`:190-309`, ten person branches) and `COMPANY_TIER1_BRANCHES` (`:371-438`, five — `email_chars`, `arrow_connective`, `path_hostile`, `archive_prefix`, `empty`, with `unknown_contact` EXPLICITLY excluded at `:369` as a person-path artifact), and `Corp` in `zArchived Acme Corp` is already admitted by the derived org-suffix rule (P13). **UNION: exactly `{Dave, Me, My}`** — `CONNECTIVE_SET` does not move, and the one undecided cell is P15's. |
| P17 | `Grep 're\.compile\|re\.IGNORECASE'` over all of `obsidian_schemas/` — is the furniture surface really confined to the two files P16 enumerates? (added round 7, recording as a measured premise what P16 asserted as prose, so a later round does not re-derive it) | **Confirmed: every `re.compile` in the package is in five files and only two of them carry furniture.** The complete list: `body_sections.py:36`, `:360`; `name_cleaning.py:46`, `:54`, `:55`, `:56`, `:57`; `name_gate.py:90` (`_PARENS_ADDRESS_RE`); `name_validation.py`'s eleven (`:66`, `:74`, `:82`, `:101`, `:107`, `:110`, `:113`, `:120`, `:123`, `:351`, `:445`); `repositories/person.py:114` (`_TRAILING_PAREN_RE`). None of the four outside the two named files carries a capitalized furniture literal — they are section headings, a parenthesised-email splitter and a trailing-paren splitter, all character classes and structure. P16's "there is no third table and no other recovery regex" is TRUE; it had simply never been recorded with its predicate. |
| P18 | Enumerate `TIER1_BRANCHES` and `COMPANY_TIER1_BRANCHES` by `branch_id` — what population does AC-3's class floor actually quantify over? (added round 7; this is the derivation AC-3 now performs at test time rather than transcribing) | **Ten distinct ids in the union.** `TIER1_BRANCHES` (`name_validation.py:190-309`): `email_chars` `:192`, `rfc2822_leak` `:203`, `arrow_connective` `:215`, `calendar_prefix` `:227`, `me_to_prefix` `:239`, `path_hostile` `:250`, `archive_prefix` `:261`, `unknown_contact` `:272`, `pure_digit` `:284`, `empty` `:301`. `COMPANY_TIER1_BRANCHES` (`:371-438`) adds NONE that is new — `email_chars` `:373`, `arrow_connective` `:385`, `path_hostile` `:398`, `archive_prefix` `:414`, `empty` `:429` — and `:365-370` records why the other five are excluded by `branch_id`. `branch_id` is unique in each tuple and is "the sweep's unit" by the dataclass docstring at `:152`; `pattern` is deliberately NOT unique — `arrow_connective` `:216`, `calendar_prefix` `:228` and `me_to_prefix` `:240` all raise `calendar_prefix`, so a pattern-keyed sweep sees eight classes where there are ten. Both tuples are importable and already swept this way in the tree (`tests/test_name_gate.py:212`, `tests/test_company_name_contract.py:369`). AC-3's floor as hand-transcribed covered SIX of the ten (`rfc2822_leak`, `arrow_connective`, `me_to_prefix`, `path_hostile`, `archive_prefix`, `unknown_contact`), omitting `calendar_prefix`, `email_chars`, `pure_digit` and `empty`; before round 6 it covered four, not the "eight of the ten" that round's fold claimed. |
| P19 | Once `docs/vault-shape-census.md` lands in HEAD as the WI-300 precondition, does anything stop a caged build from rewriting it? (added round 8; **this is the one premise whose subject is out-of-repo** — the workshop pipeline tooling, read at `/Users/davewascha/Workspaces/workshop-stable/src` on 2026-09-07, which pins to no HEAD this document's reader can re-run against, so it is recorded with that caveat rather than as a tree measurement) | **No.** The IN-TREE half is re-runnable and is what AC-3(iv) actually rests on: `pipeline-runners.yaml:34-38` declares `write_authority` as `obsidian_schemas/**`, `tests/**`, `scripts/**`, `docs/**` — `docs/**` in full, **no carve-out for a landed precondition file** (this is P7, whose consequence had never been drawn). The out-of-repo half, read once and reported as such: the merge-boundary integrity wall over docs (`stage_advancer.py:653-675`) is scoped to files carrying work-item frontmatter — its own docstring says a SHARED non-work-item doc "is a recurring LEGIT build write … → NOT flagged" — and `docs/vault-shape-census.md` carries no `id: WI-*`, so it is exactly that case. The DRIVEN work-item doc is the protected one: `:666` exempts it from that wall precisely because it is per-spawn fence-checked during the drive (`pipeline_orchestrator._tampered_prior_fences`, `:12048`), and the signed `ac-signoff` fence carries a whole-section `ac_hash` plus per-criterion `ac_hash_AC-N` keys (`ac_signoff.py:1817`, `:1503`) which the linter re-checks byte-intact (`work_item_linter.py:4129-4143`). **That asymmetry is the whole design of AC-3(iv):** the expected digest is put where the machine already freezes text — the signed criterion — rather than in `tests/fixture_vault.py`, which the build owns and can update in the same commit that edits the census. |
| P20 | Does the package DECLARE its skip-reason codomain anywhere a test could read, as `TYPE_TO_MODEL` and the Tier-1 tables declare theirs? `Grep 'malformed-frontmatter\|schema-drift\|unreadable\|SKIP_REASON'` over the whole seeded tree, then a read of `repositories/base.py:27-47` and `repositories/__init__.py` (added round 9, after two independent gate reads found AC-4 asserting a consequence only a declaration delivers) | **No — there is nothing to read, and this is the one population in this document with no declaration behind it.** In `obsidian_schemas/` the three strings occur ONLY as bare return-statement literals inside `_skip_reason`'s `isinstance` chain — `"malformed-frontmatter"` `:44`, `"schema-drift"` `:46`, `"unreadable"` `:47` — plus a type comment on `SkippedNote.reason` at `:37` and an unrelated prose mention at `errors.py:112`. **No frozenset, tuple, dict, `Enum` or module constant exports them, and `repositories/__init__.py`'s `__all__` (`:14-21`) carries only the four repositories, `BaseRepository` and `VaultPathNotConfiguredError`.** The consequence: transcription is today's ONLY available idiom and the tree already uses it — `tests/test_loud_fail_load.py:187-188` hand-types the same three literals as its expected set. So AC-4's pre-round-9 claim that "a fourth reason added to the package later fails until it has a specimen" was FALSE: both sides of its equality were hand-typed, and a fourth `_skip_reason` arm would have left every leg green with the new class uncovered. **Contrast, and it is what makes this a defect rather than a fact of life:** every other population this document derives IS exported — `TYPE_TO_MODEL` (`models.py:309-318`), `ENTITY_BODY_CONFIG` (`body_sections.py:303-324`), `TIER1_BRANCHES` / `COMPANY_TIER1_BRANCHES` (`name_validation.py:190-309`, `:371-438`), `_GENERIC_ORG_SUFFIXES` (`name_cleaning.py:58`), `__all__` — so this is the one classification vocabulary that never got the module-level-literal treatment, which is why AC-4 now adds it rather than transcribing around it. |

**Not settled here, and deliberately so.** *Which* note shapes actually occur in the live vault and
at what frequency — the only thing that can tell a corpus that covers the estate from a corpus that
covers what one author happened to think of — is out-of-repo. It is not routed away as
unreachable-because-forbidden (the gate spawn arms no read sandbox and I could open the vault); it is
routed away because **an answer read there pins to no HEAD and the next reader cannot re-run it.**
That is the grounding artifact declared under `## Write Targets`, and AC-3 gives it teeth in the
suite.

### Constraints discovered

- **Half the corpus's value is notes the write door now refuses to create.** WI-021's `gate_write` is
  a predicate on every frontmatter-writing arm, and WI-022 (in the seeded delta) extends it to
  companies. A specimen carrying a path-hostile name, an RFC 2822 leak or an arrow-connective
  descriptor **cannot be planted through `repo.save()` or `write_markdown_file`** — that is the whole
  point of the gate. So the corpus must be materialized by **byte copy**, never by a repository
  write. This is not an optimization; it is the only mechanism that can carry the specimens.
- **The vault is ONE FLAT DIRECTORY partitioned by filename glob, and that decides more of this
  design than it looks** (surfaced by the 2026-09-06 architect round; verified in the seeded tree).
  `load()` globs non-recursively from a single `vault_path` (`repositories/base.py:231`) and the four
  repositories partition that one directory by pattern: person and company BOTH inherit the default
  `@*.md` (`base.py:195-198`, the whole `file_pattern` property — neither subclass overrides it; the
  span is aligned here 2026-09-08 with `## Approach` and `## Verified Diagnosis` D-7, which is where
  a review round found this site and AC-4's `desc` still carrying the narrower `:196-198`. **AC-4 is
  SIGNED and is deliberately NOT edited for it:** the narrower span resolves, cites the same
  property and supports the same claim, so moving it would buy a D4b re-sign for a navigational nit
  — recorded so a later round can tell the divergence was checked rather than missed),
  meeting declares `Meeting *.md`
  (`meeting.py:51-54`), book declares the catch-all `*.md` (`book.py:50-53`), and `save()` writes
  `vault_path / f"@{name}.md"` (`base.py:381-383`). Three things follow. (i) A subdirectory-per-type
  corpus — the tidy default — is globbed by NOTHING, so every repository-level criterion passes
  vacuously on zero notes; the corpus must be flat. (ii) Skip OWNERSHIP is a joint function of the
  FILENAME and the error's `declared_type`, not of the note: `_owns(None)` returns
  `Path(file_pattern).stem != "*"` (`base.py:258-265`), so an untyped failure — `FrontmatterParseError`,
  whose `declared_type` is always `None` (`errors.py:65-67`), and `UnicodeDecodeError`, which has no
  such attribute — is recorded by BOTH `@*.md` repositories at once, by meeting when the filename
  matches its glob, and by book NEVER (its catch-all stem is exactly `*`). That makes "the skip
  mapping" ambiguous unless the domain is named, which is why AC-4 is per repository. (iii) A
  same-name collision in a flat directory is several FILENAMES sharing one stored `name:`, which is
  structurally the divergence class — the census rules whether the vault separates them.
- **The expectations cannot be computed by the code under test.** A round-trip test that derives its
  "expected" values by parsing the fixture with the parser it is testing asserts that the parser
  agrees with itself. The corpus's oracle has to be a **declared** manifest — hand-written from the
  model definitions — sitting beside the bytes, and frozen with them.
- **"Frozen" needs a mechanism or it is a wish.** Nothing stops a future test from editing a fixture
  note to make itself pass, and the whole corpus then silently drifts for everyone else. A content
  digest over the corpus, asserted against a constant in the manifest, is what makes an edit loud.
- **And the same is true of the CENSUS, which is the constraint round 8 discovered.** The corpus is
  not the only frozen thing this design leans on: `docs/vault-shape-census.md` is the sole oracle for
  every claim about the live vault the hermetic suite cannot re-derive, and nothing in this pipeline
  protects it once it lands — `docs/**` is builder-writable in full (P7) and the only merge-boundary
  integrity wall over docs is scoped by design to work-item docs, which the census is not (P19). So
  the census needs the corpus's mechanism too, with one difference that decides whether it works:
  the corpus's digest constant may live in `tests/fixture_vault.py`, because the corpus and the
  constant are written by the same author in the same act — but the census is written by the
  CONDUCTOR and checked against by the BUILD, so its expected digest must live where the build cannot
  reach, which is the criterion Dave signs.
- **The suite is hermetic and ~1s, and must stay that way.** `pipeline-runners.yaml:7-8` makes the
  floor command the AC battery's own interpreter. No network, no live-vault read, no subprocess.
- **Real personal data in a tracked repo is irreversible.** This package installs `-e` into three
  consumer repos and its history is permanent. The 07-05 routing note already flags it: a bad frame
  leaks personal data into git history. Note P10 honestly — the repo *already* carries 35
  real-looking name literals. This item does not retro-scrub them (out of the frozen Intent); it
  declines to add more, and a sibling should decide about the existing ones.
- **Effort budget.** One focused build for corpus + manifest + materializer + the four sweeps, plus
  one conductor act (the census) that cannot happen inside the cage. Migrating all 13 files' inline
  literals is **not** in that budget — see D5.
- **Dependencies.** Nothing blocks this. `WI-026` (lint_vault `--fix` safety) declares `needs: WI-016`
  in `state/manifests/queue-2026-09-06.yaml:52-54` and its remaining scope *is* a fixture-vault floor,
  so the census should capture the shapes its five auto-fixable rules fire on while the conductor is
  already in the vault — one pass instead of two.

### Approaches considered and rejected

**D1 — Take a ~50-note slice of the live vault and anonymize it in place (the mint's named
mechanism). AMENDED, and the amendment is the design.** The mechanism is right about *where the
shapes come from* and wrong about *what crosses into git*. "Anonymize" as usually built means "swap
the names and keep the bytes", and the names are precisely the field whose shape the corpus exists to
carry — so a swap either destroys the shape class (`José García` → `Test Person 3`, and the corpus is
Alice and Bob with extra steps) or preserves it so faithfully that it is still the person. Neither is
acceptable. The amendment: **sample the SHAPE distribution from the live vault, synthesize the
identities.** A conductor pass censuses the vault and records, per shape class, its live count and a
*pseudonymous* specimen carrying the same character profile — same script, same diacritic pattern,
same punctuation, same whitespace damage, same field presence/absence — under reserved-for-testing
domains and phone ranges. The bytes committed are new; the distribution they are drawn from is
measured. This is the honest reading of the workspace real-data-fixtures rule (LESSONS #9): its scar
is that *synthetic fixtures verify code-correctness, not data-correctness*, and what fixes that is
sampling reality's shapes, not shipping reality's people.

**D2 — Synthesize the corpus from shapes read out of the existing test literals. REJECTED, and
LESSONS #27 is why.** It is the cheapest thing available — P10 says the corruption forms are already
in the tree, so a builder could assemble a corpus with no conductor act at all. But a fixture drawn
from fixtures is *a specimen you chose because you already understand it*: it certifies the cases the
last five authors thought of and is structurally blind to the tail, which is the only thing a corpus
buys over a literal. The census is the entire difference between this item and a tidy-up, and
removing it to save a turnaround removes the item's reason to exist.

**D3 — Point the tests at the real vault behind an env var. REJECTED.** It breaks hermeticity
(`pipeline-runners.yaml`'s floor is the AC battery's own interpreter, and the suite runs in a
detached worktree with no vault), and it makes every test's meaning a function of a corpus that
churned two sentinel stubs in 25 days. The frozen-ness is not incidental to the ask; it is half of it.

**D4 — Lead with property-based testing (Hypothesis) and/or a performance corpus. REJECTED as the
core, kept as a named follow-on.** The 07-05 reslice already demoted Hypothesis to a stretch and this
exploration agrees for a sharper reason: a property test needs a *generator*, and the honest
generator for this domain is the shape census — so Hypothesis is a consumer of this item's output,
not a peer of it. Ordering them the other way builds the generator from imagination. Performance is
rejected on evidence rather than taste: the queue review re-measured the live load at **1,147 people
in 1.26s**, which is the number that has kept the perf items parked; a ~50-note corpus cannot say
anything about scale, and a corpus large enough to try would stop being reviewable-by-eye, which is
the property that makes committing it safe.

**D5 — Migrate all 83 inline literals across the 13 files onto the corpus. OUT OF SCOPE, named so it
is not lost.** Each of those literals encodes a property its test author chose, and a mechanical
rewrite loses exactly the ones nobody wrote a comment about — the WI-131 shape. The item lands the
corpus and migrates a **named proof set** (the three `^type:`-literal files: `test_repositories.py`,
`test_parser.py`, `test_writer.py`) to demonstrate the surface is usable; the rest migrate when their
own tests are next touched. Cost of deferring: the duplication persists for a while longer, which is
what it has been doing since March.

**D6 — Ship the corpus to HAL9000 / Exocortex as a shared fixture surface (the 07-05 routing note's
"coordinate with exocortex WI-034 — one shared design"). DEFERRED, with the blocker measured.** P8 is
the hard fact: the wheel packages `obsidian_schemas` only, so nothing under `tests/` is importable by
a consumer no matter how well designed it is. Making it shared is an *export-surface* item and that
is WI-030's exact shape (already minted, 2026-09-06, for the `lint_vault` surface). The 2026-09-06
queue review ruled the same way — "slice to THIS repo first; 'shared with consumers' is an
open-space promise". Designing for it costs nothing here and is taken: the corpus is bytes plus a
declared manifest, both of which travel, and the layout is a plain vault directory rather than a
Python API. Cost of deferring: exocortex WI-034 duplicates the census if it moves before the export
surface exists — which is an argument for the census artifact being a *document*, readable from any
repo, rather than a fixture-only asset. **And the deferral does not ride WI-030**: that item was minted
2026-09-06 for `lint_vault`'s export surface (`read_vault`, `build_indexes`, `run_lint`, `VaultFile`,
`Severity`) and its declared scope is that symbol set, not this corpus. D6 re-enters only when
someone explicitly re-opens it — either by widening WI-030's premise to carry the fixture corpus or
by minting a new export item. Naming it plainly here is cheaper than an assumed dependency: the cost
of the difference is exocortex WI-034 duplicating the census, which is the reason the census is a
document readable from any repo in the first place.

**D7 — Reuse the corpus as WI-026's acceptance for `lint_vault --fix`. PARKED, and LESSONS #27 says
why it must be.** `lint_vault.py` is a tool whose job is the whole corpus, and #27's rule is that
such a tool's acceptance runs over the real corpus, not over crafted fixtures — hermetic fixtures
certify the specimen, not the production surface. So this item unblocks WI-026 by giving it a *floor*
(regression-locking, fast, in-suite) and explicitly **does not** give it an acceptance. Recording it
here so WI-026's spec does not read "WI-016 landed, therefore the fixtures are the acceptance".

### Where the structure lives

The one question this exploration kept returning to: *why does a test have to type a vault at all?*
The answer is that the structure — "what a real note of type T looks like, and what it should parse
to" — exists in the live vault and in the model definitions, and it survives to neither place the
tests can reach. `TYPE_TO_MODEL` knows the class; nothing enumerates it. `_skip_reason` knows the
failure classification; nothing has one of each on disk — and, uniquely on this list, it does not
even DECLARE the classification for anything to read (P20), which is why this item's one line of
package change is the frozenset that makes it declarable. `TIER1_BRANCHES` knows the refusal surface,
one unique `branch_id` per class; nothing on disk carries a specimen of each. `repositories/__init__`
knows which repositories partition the vault; nothing declares what each should own. The census knows
the shape distribution; it has never been written down. This item's job is to make those declarations
reach the suite, and that is why every criterion below is a **derived sweep with a declared oracle**
rather than a bigger pile of fixtures: the pile is the symptom. It is also why, whenever a criterion
here has quantified over one of those surfaces, the population has to be READ from the declaration and
never copied into the criterion — three rounds of findings have been exactly that copy going stale,
and the standing rule that falls out is the one to keep: **the population is derived, the oracle is
hand-declared.** Derive the oracle too and the criterion becomes a mirror of the code it is checking;
transcribe the population and it silently stops covering the thing it names.

### Convergence

D1-as-amended: a frozen, in-repo, ~50-note vault whose shapes are sampled from a conductor-run census
of the live vault and whose identities are synthetic and provably non-identifying, carried by a
declared manifest that states each note's expected parse, and materialized into a temp directory by
byte copy — **flat**, mirroring the live vault, because the repositories partition one directory by
filename glob. Ready to spec. The architect's triggers did fire (a new shared test surface every
later item builds on, plus a new artifact convention) and the gates have now run seventeen rounds
between them — architect ×9 and AC red-team ×8. **Every finding across all seventeen was against a
criterion's declared domains or the evidence they rest on, never against the approach**, which both
gates have ruled sound and standing at each pass. Four of those rounds landed on AC-5's own closure machinery, each on machinery the round
before had ADDED, and the red-team correctly named that pattern rather than iterating it: the fourth
fold's answer was to REMOVE the generator both gates identified — a mandatory obligation over a set
the builder does not author — rather than prune its fourth instance, and to replace the phrase that
bred the second family (an identity-position list named by category) with an enumeration read off
`models.py`. Round 5 tested that removal from both gates independently and found no fifth instance,
which is the item's own falsification condition coming back clean; what it found instead was the
second family's residue — an enumeration that was not its own stated rule's output in either
direction — closed here by stating the rule in three clauses (naming, declared over-constraint,
undeclared `extra="allow"` keys), by adding the three fields the rule decides and the criterion had
missed (`Exploration.related`, `Watch.streaming_service`, `GiftIdea.source`), and by recording the
complete field-by-field reconciliation as P14 so the surface is exhausted rather than sampled. Round 6
found the same "enumerated by sampling" shape in the set next door and the two gates reached it from
opposite directions with CONTRADICTORY fixes — architect wanting three literals added to
`CONNECTIVE_SET`, the red-team showing that every real specimen this repository commits for one of the
two branches makes one of those literals unexercisable — and the resolution is an ORDER rather than a
compromise: pin the extractor's "run" first (the criterion now states it, with four worked
consequences, choosing the maximal reading on the evidence of P15's five specimens), then apply it to
the whole surface, which P16 records as all sixteen regexes and both Tier-1 tables and which returns
`{Dave, Me, My}` unchanged. The one cell the code genuinely does not decide — `re.IGNORECASE` leaving
the live `unknown contact` casing to the vault — gets AC-3's own one-time pre-origination
reconciliation rather than a guess frozen by signature, and AC-3's class floor gains the two branches
whose omission was the same read's other symptom. Round 7 moved the finding OUT of AC-5 for the first
time since round 1 and, in doing so, identified what the family actually was: not AC-5's closure
machinery but this document's habit of HAND-TRANSCRIBING an enumeration the tree DECLARES. AC-3's
class floor was such a transcription — six of the ten `branch_id`s in `TIER1_BRANCHES` ∪
`COMPANY_TIER1_BRANCHES`, silently missing `calendar_prefix` (the sole cited source of
`CONNECTIVE_SET`'s frozen `Dave` member), `email_chars`, `pure_digit` and `empty`, with the previous
fold's own count of it wrong by two — and the fix is the one this item already applies twice
elsewhere: derive the branch half at test time and hand-list only the six shape classes no branch
declares. The same question asked of every OTHER criterion then found a fourth instance neither gate
raised — AC-4's four repositories, likewise derivable from the package's exported
`BaseRepository` subclasses — so it was folded in the same pass rather than left for a round 8, and
what remains hand-written is now exactly the four things with no declaration to read (AC-3's six
shape classes, AC-5(b)'s identity positions, `CONNECTIVE_SET`, and AC-4's deliberately hand-declared
ownership oracle), each named in the sufficiency section so the claim is checkable — **and it was
checked, twice, and was wrong both times before it came true: round 8 found two more instances inside
that same sweep, and round 9 found a seventh thing that was neither derived nor on the list; both
corrections are recorded in place beside the claim, and the four-item residue is accurate only as of
the round-9 fold below.** AC-5
is still smaller in what it demands than at any point since round 1 and more precise in where it
demands it, and round 7 did not change what it demands at all: one clause deleted, one equality
weakened to a containment, one admission derived from the package instead of declared, one rule that
generates its own list, an extraction rule determinate enough that the list can only be generated one
way, and now two corrected statements of fact (the furniture surface is sixteen regexes, not fifteen;
`re.IGNORECASE` is on eight of them, so `unknown_contact` is the cell the committed SPECIMENS leave
open rather than the only place the flag appears). The sufficiency
question the red-team raised is not for a gate to settle and is recorded above for Dave's ruling at
sign-off, with a recommendation, with what would falsify it, with the result of the test it named,
with round 6's split datum recorded honestly, and now with round 7 recorded as the predicate that
datum named — a third instance of the second family, but one sitting OUTSIDE the part the middle path
would remove, which is the fact that decides what it means and which is stated for Dave rather than
ruled on here. Round 8 closed that habit's last two instances — AC-2's narrowing arm and its
GATE-CLEAN gloss, both of which round 7's per-criterion sweep had walked past because AC-2's
POPULATION was already derived — and, separately, produced the first blocking finding in the item's
history that is not an enumeration defect at all: `docs/vault-shape-census.md`, the artifact AC-3(iii)
and AC-5(c) both delegate their entire oracle to, was frozen by nothing once it landed, because
`docs/**` is builder-writable in full (P7) and the pipeline's only merge-boundary wall over docs is
scoped by design to work-item docs (P19). The remedy is this item's own AC-1(a) pointed at the
artifact nobody had pointed it at — a digest, with the expected value in the SIGNED criterion rather
than in the module the build owns — and it argues for the structural wall rather than against it,
since the leg whose ground truth turned out forgeable is exactly the one the middle path would demote
to human review. What moved: AC-4's equality domain, its derived repository set and the tautology it
carried; the flat layout; AC-3's status scoping, its class floor's derivation, its reverse direction
and now the fixity of the artifact it reads; AC-2's two derived enumerations; and AC-5's growth from
a two-category containment scan into a position-split name closure with a census-backed provenance
ledger, then its deliberate simplification, its rule/enumeration reconciliation, its pinned extractor,
and now a fixity assertion under the ledger. Round 9 is where the habit's story ends rather than
continues, and the ending has a different shape from the eight folds before it: both gates,
independently and from different angles, found that AC-4 had placed `_skip_reason`'s reason set on the
DERIVED side of the residue and claimed a consequence only a derivation delivers, while the package
declares no such set anywhere (P20 — three bare return literals and a type comment). Every earlier
instance of this family was a list COPIED from a declaration the tree already held, and the remedy was
always to read the declaration instead; this one had nothing to read, so the remedy is the opposite
move — the build WRITES the declaration (`SKIP_REASONS` in `repositories/base.py`, this item's only
package change) and binds it to `_skip_reason`'s own returns by a single `ast` scan in the module that
already single-homes that capability, so the export cannot drift into decoration. It is folded that way
rather than by the cheaper demotion both gates also offered, because the residue list is for things
with no declaration to read and its other four members are judgment by subject, while this one is
mechanical — and a mechanical fact carried by a transcription is the defect this whole document is
organised against. What never moved: D1's amendment, the byte-copy rule,
the derived sweeps, and the census as the item's reason to exist. Next stop
is the spec-writer, after the census lands, its digest is taken, and Dave signs the criteria.

## Approach

Land `tests/fixtures/vault/` — a **frozen corpus of ~50 markdown notes** covering all 8 members of
`TYPE_TO_MODEL`, the corruption forms the census records, and at least one specimen per `_skip_reason`
class. **The corpus is ONE FLAT DIRECTORY, mirroring the live vault, and this is load-bearing rather
than cosmetic:** the repositories partition a single directory by FILENAME GLOB and walk it
non-recursively — `load()` calls `self.vault_path.glob(self.file_pattern)` (`repositories/base.py:231`),
person and company both inherit the default `@*.md` (`base.py:195-198`, the whole `file_pattern`
property; neither subclass overrides — the same span `## Verified Diagnosis` D-7 cites, aligned here
2026-09-08 after a review round found the two differing by one line),
meeting declares `Meeting *.md` (`meeting.py:51-54`), book declares `*.md` (`book.py:50-53`), and
`save()` writes to `self.vault_path / f"@{name}.md"` (`base.py:381-383`). A tidy
subdirectory-per-entity-type layout — the obvious choice for a spec-writer who has not read that glob
— is a corpus against which every repository globs ZERO notes, so AC-4 passes vacuously on `0 == 0`
and AC-2's repository-level legs certify nothing. Two consequences follow from flatness and are
stated here so they are settled at spec rather than discovered at build: the four types with **no
repository at all** (`watch`, `explore`, `gift-idea`, `exploration`) have no glob, so their fixtures
are exercised at the PARSER level by AC-2 and are outside AC-4's repository-level counts entirely;
and a same-name collision cannot be three notes sharing a filename in one flat directory — it must be
three distinct filenames sharing one stored `name:`, which may be the same specimen as the
"filename-stem-does-not-equal-stored-name divergence" class, so **whether those are one class or two
is a question the census rules on**, not the builder (see `## Write Targets`).

The corpus sits beside `tests/fixture_vault.py`, which holds three things and no test logic: the **declared
manifest** (per note: its type, its expected parsed field values written by hand from the model
definitions, or its expected skip reason — never values produced by running the parser; skips are
declared per OWNING REPOSITORY, `{repository_type: {path: reason}}`, because ownership is a function
of the note's filename and the error's `declared_type`, not of the note alone — see AC-4), a **frozen
digest** over the corpus bytes so an edit to a fixture is RED rather than silent (with the one-line
recipe for regenerating that constant stated in the module docstring, so the friction stays a
deliberate speed bump rather than a puzzle), and `materialize_vault(dest)`, which **byte-copies** the
flat corpus into a caller-supplied temp directory — same flat shape, same bytes — and
never routes through `write_markdown_file` or a repository, because a large share of the specimens
are notes the WI-021/WI-022 gate exists to refuse to create. One member of the corpus is deliberately
**not valid UTF-8**: that is the only spelling of the `unreadable` skip class that survives git
(`parser.py:238` reads with `read_text(encoding="utf-8")` unwrapped, so invalid bytes raise
`UnicodeDecodeError`, which is neither `FrontmatterParseError` nor `SchemaDriftError` and falls to
`_skip_reason`'s third arm), and it is why the digest and the containment scan are both over BYTES
and never over decoded text. A `chmod`-based unreadable specimen is not reached for; git would not
carry it. The corpus's *content* is not invented:
a conductor pass censuses the live vault and commits `docs/vault-shape-census.md`, recording per shape
class its live count, the scan command and stdout, and a **pseudonymous specimen** with the same
character profile — same script and diacritic pattern, same punctuation, same whitespace damage, same
field presence/absence — under RFC 2606 reserved domains and reserved fictional phone ranges, so the
distribution is measured while the identities are synthetic and no real contact enters git history.
Names have no reserved namespace to fall back on, so the census also commits an **identity pool
table**: every NAME token the corpus is permitted to use, the shape class it is built to carry, and
the conductor's live-vault scan showing that token occurs there zero times. That table is the only
place the claim can be settled — the suite is hermetic and cannot read the vault — and AC-5 turns it
into a wall by requiring every token in an IDENTITY-BEARING POSITION to be **drawn from** that pool
(a containment, not an equality: the pre-build census may certify a token the build does not end up
using, and a certified-but-unused token is not a leak), or to be a member of a small CONNECTIVE set
frozen by enumeration in the criterion itself. **Identity-bearing positions are enumerated field by
field against `models.py` rather than gestured at**, because the phrase they replace ("the
company/meeting title fields") both named a field `Meeting` does not have and missed six fields that
carry a real person's name — `Person.company`, `Meeting.attendees`, `Book.author`,
`Watch.director`, `Watch.recommended_by`, `Explore.source` and `GiftIdea.for_person` (P12), and
because the one-line rule that replaced it did not itself generate the list written under it —
a fifth read added `Watch.streaming_service`, `GiftIdea.source` and, the one that mattered,
`Exploration.related`, whose docstring glosses its members as `[[Other Exploration]], [[Person]],
etc.` (`models.py:280`, field at `:299`) on the one entity type with zero test references anywhere
today (P4). The rule is therefore stated in THREE CLAUSES so a ninth type, a new field or an
undeclared key is classified rather than missed: a field is an identity position (1) iff its value
IS a person's or an organisation's name — the whole scalar, or each list element, or a wikilink to a
note holding one — deliberately not "could contain one", which would sweep ordinary English into a
pool that owes zero-hit live-vault rows; (2) plus the four entity `title` fields, which the first
clause does not reach and which are included as a DECLARED over-constraint so a later reconciliation
preserves them rather than pruning them; and (3) plus any manifest-declared value for a frontmatter
key the note's model does not declare, since `extra="allow"` (`models.py:31-32`) puts those outside
every enumeration over declared fields. The complete field-by-field reconciliation is P14, done once
and recorded so the next reader checks it rather than re-derives it. The connectives — `Me`, `My` and `Dave`,
the package's own calendar/arrow prefix vocabulary, plus the
non-token furniture `to`, `->`, `→` which the extractor cannot produce and which are therefore not
members at all — are the shapes the corruption classes are made of, and they carry no provenance row
on purpose. **That set is enumerated by applying a stated rule to the whole furniture surface, not by
sampling it**: the extractor's notion of a "run" is pinned in the criterion to the maximal contiguous
span (no camelCase restart, first character decides, trailing `'`/`-` trimmed) — because two readings
of it disagreed on `zArchived`, and the maximal one is what all five committed `archive_prefix`
specimens support (P15) — and the rule is then applied to all sixteen regexes across
`name_validation.py` and `name_cleaning.py` plus both Tier-1 tables, which returns exactly
`{Dave, Me, My}` (P16): the archive prefix contributes nothing because `zArchived` is one
lowercase-initial run, and `unknown contact` contributes nothing because both its regexes spell the
literal lowercase. The single cell the code does not settle is that `re.IGNORECASE` leaves the live
`unknown contact` form's casing to the vault, and this repo commits both — so the set carries the same
one-time pre-origination reconciliation against the census that AC-3's class floor does, and is frozen
by literal enumeration thereafter, exactly as before. The connectives' provenance exemption is unchanged: `Me` is a live stored-name form here (it is why `name_validation.py:238-248` carries
`specimen="Me to David Field"`), so a zero-hit row for it would be a lie in the ledger. What makes
that exemption safe is that the set cannot grow without an AC change — not that the corpus exercises
it, which is why the set carries no non-vacuity obligation and whatever connective the vault actually
produces is covered by AC-3(i) instead. Ordinary English prose gets a third, separate allowlist that
is **not reachable from an identity position at all** — the split is by POSITION rather than by
bucket, because a bucket the scan consults everywhere is a bypass, not a wall — and generic
organisation suffixes are admitted in identity positions from a set DERIVED from the package
(`name_cleaning._GENERIC_ORG_SUFFIXES`, `:58`), never hand-declared, so `Voxleaf Ltd` does not oblige
the conductor to certify that `Ltd` occurs zero times in a vault whose company notes the landed census
now MEASURES at 659 live and 2,160 whole-vault (`docs/vault-shape-census.md`'s `census-meta` header,
`vault_notes_company: 659`, with the whole-vault figure in the prose beneath it; an earlier draft wrote
"2,159" from the 2026-07 company-name corpus audit and the argument holds identically at any of the
three, which is why nothing rests on the number — corrected 2026-09-08 now that this item's own
artifact is the source). Reading that
set from the package is what stops a builder padding it, and it has one property worth writing down
rather than leaving to be discovered: it makes a name-CLEANING set a load-bearing dependency of a
PRIVACY wall, so a future edit there — made by someone not thinking about this corpus, with no AC
change — widens AC-5(b)'s admission. It is small (the members are org suffixes by construction and
`name_cleaning.py`'s own tests constrain them) and it is not a reason to hand-declare instead, but
`fixture_vault.py`'s module docstring names `name_cleaning.py:58` as a load-bearing dependency of
AC-5 so the reader of that file in six months is told.
Four derived sweeps then close the classes the tree already declares, and every population they
quantify over is READ from the declaration rather than transcribed into a criterion — which is the
discipline `## Where the structure lives` names and the one this item has had to re-apply most often:
`TYPE_TO_MODEL` (8 members,
set-equality against the manifest, with the types `ENTITY_BODY_CONFIG` omits derived at test time as
`set(TYPE_TO_MODEL) - set(ENTITY_BODY_CONFIG)` and asserted against `get_default_body`'s declared
`""` marker rather than an invented section list, and with round-trip GATE-CLEANLINESS stated as the
door's own predicate — no record of `TIER1_BRANCHES` matching for a person representative, none of
`COMPANY_TIER1_BRANCHES` for a company one, vacuous for the six pass-through types — rather than as a
list of corruption forms transcribed into the criterion), `_skip_reason`'s
three-valued codomain — the one population on this list that HAS no declaration today and is
therefore GIVEN one by this item rather than transcribed: the build adds a module-level
`SKIP_REASONS` frozenset to `repositories/base.py` whose members `_skip_reason` returns by name (its
three reasons are bare return literals at `:44`/`:46`/`:47` and a type comment at `:37` today, with
no set exported anywhere, P20), a single `ast` scan in `tests/derivations.py` asserts that frozenset
EQUALS the string values `_skip_reason`'s own body can return so the export cannot drift from the
function, and AC-4 then reads the frozenset the way AC-2 reads `TYPE_TO_MODEL` — with the mapping
equality run both ways against the manifest and asserted PER REPOSITORY over
a repository set itself read from the names the package's `repositories/__init__.py` exports and
keyed by `type_name`, so a fifth repository cannot join the corpus's blind spot silently, the
census's class table — whose branch-backed rows are floored by `{record.branch_id for record in
TIER1_BRANCHES + COMPANY_TIER1_BRANCHES}` read at test time, keyed on `branch_id` and never on the
deliberately non-unique `pattern`, asserted in both directions, with only the six shape classes no
branch declares left hand-listed, so the artifact can neither be discharged as prose nor quietly omit
a refusal branch the package has — and, because the whole class table and the pool table are trusted
as ground truth a hermetic suite cannot re-derive, **the census itself is frozen by digest** exactly
as the corpus is under AC-1(a), with the expected value written into the signed criterion rather than
into the module the build owns, since `docs/**` is builder-writable in full (P7) and a constant the
build owns is updated in the same commit that edits the file it digests —
and a **containment wall** asserting that every
email, phone and profile URL found anywhere in the corpus bytes is inside a reserved range AND that
every name-shaped token in an identity-bearing position — across the corpus bytes and the manifest
module, which restates them — is drawn from the census-certified NAME pool or the enumerated
connective set, which is what makes a leak structurally impossible rather than merely intended for
all three of the categories `## Intent` names rather than only the two that have RFCs.
**The build touches exactly two files outside `tests/fixtures/` and `tests/fixture_vault.py`, both
named here so the scope is not discovered at build time:** `obsidian_schemas/repositories/base.py`
gains the `SKIP_REASONS` declaration described above — the item's only package change, one frozenset,
inside `write_authority` (P7) — and `tests/derivations.py` gains the one syntax scan that binds it to
`_skip_reason`'s returns, which is where it has to live because `ast` is single-homed there (P9) and
no fixture module may name it. *(Two spec-time amendments, 2026-09-07, recorded here rather than
silently diverging in `## Design`. The two files are still the only NON-TEST files the build touches
and the package change is still one frozenset — plus the three named constants it is built from —
but: `base.py` gains four module-level names rather than one, and `tests/derivations.py` gains TWO
scans rather than one, the second being `skip_reason_literal_sites`, the wall that closes the
hand-typed-literal class instead of its three current instances (§4). The TEST files the build
touches are five beyond the two new ones, all of them authorised by D5 or by §4's disposition table
and all declared in `## Write Targets`.)* *(A third spec-time amendment, 2026-09-08, folding the
threat model's M1: **the containment wall's reach is the corpus bytes, the manifest module AND
`docs/vault-shape-census.md`'s own bytes** — the artifact this whole approach delegates its privacy
ground truth to sat outside every check in this document, including the one it grounds, so its prose
could carry a real live-vault name with everything green and two signed criteria then asserting those
bytes immutable. The census is still READ and never written by the build; what changes is that its
whole byte stream now faces §6.1's extractor and the same four admissions the corpus's identity
positions face, with the same predicate run one build phase earlier as a refusal in the precondition
abort gate. §6.5 and `## Mitigation Folds` carry it.)* Migration of existing tests is
limited to the three `^type:`-literal files as proof the surface is usable; the other ten migrate when
next touched (D5).

## Write Targets

```writes
kind: precondition
path: docs/vault-shape-census.md
grounds: Which note shapes the frozen corpus must cover, measured from the live vault rather than remembered
why: AC-2's totality claim, AC-3's per-class specimen list and the whole D1-vs-D2 distinction rest on the live vault's shape distribution, which is out-of-repo and which a caged builder cannot read — so a builder-authored corpus would be invented, not sampled, and would be exactly the D2 fixture-drawn-from-fixtures this item rejects (the WI-024 fabrication precedent). The artifact's CLASS TABLE carries, per shape class, SIX columns — a stable class id, the `count` of live notes matching, a `status` of MEASURED or ABSENT (ABSENT exactly when the count is zero), the scan command run against the live vault, its verbatim stdout, and — for a MEASURED row only — ONE pseudonymous specimen carrying the same character profile — same script and diacritic pattern, same punctuation, same whitespace damage, same field presence/absence — with emails under RFC 2606 reserved domains and phones in reserved fictional ranges, so the committed bytes are synthetic while the distribution they are drawn from is measured; EVERY RECORDED SCAN COMMAND IN THIS ARTIFACT — class-table row or pool-table row — MUST EMIT A COUNT rather than raw match lines (`rg -c`, `rg --count-matches`, a `| wc -l` pipe; the artifact states which form it used), because a search that finds nothing writes NOTHING to stdout, so a verbatim capture of an honest zero result would be empty and would fail AC-3(ii)'s and AC-5(c)'s non-empty-stdout assertions — leaving no route through except typing non-verbatim prose into the one field in this document whose entire value is that it is verbatim; with a counting command a true zero records verbatim as `0` and honesty and the assertion agree; EVERY PSEUDONYMOUS SPECIMEN'S IDENTITY-POSITION TOKENS MUST BE CONSTRUCTED STRINGS, not ordinary vocabulary, because AC-5(b) puts each of them in the pool and AC-5(c) makes the conductor certify it occurs zero times in the live vault: a naturally-worded meeting title, a company name carrying a real-word element, or the street and locality words of the address-in-a-name-field specimen all land in an identity position, and a token like `London` or `Group` cannot honestly carry a zero-hit row in this vault (generic organisation suffixes are the one exception and need no pool row at all — AC-5(b) admits them from `name_cleaning._GENERIC_ORG_SUFFIXES`, `:58`, read from the package rather than declared here); the identity positions AC-5(b) enumerates reach further than the obvious `name:` fields and the specimen author should read that list before writing one — the WIKILINK TARGETS inside an `exploration` note's `related:` list (`models.py:299`, glossed `[[Other Exploration]], [[Person]], etc.` at `:280`), a `watch` note's `streaming_service:` and a `gift-idea`'s `source:`, the four entity `title` fields, and the value of ANY frontmatter key no model declares (`extra="allow"`, `:31-32`) are all identity positions, so each of their tokens needs a pool row exactly as a `name:` does; an ABSENT row carries its count, command and stdout plus an affirmative ruling that the shape does not occur, and carries NO specimen, because there is nothing to specimen. It also carries the vault's snapshot date and total note count per entity type, and — because the conductor is already in the vault and WI-026 declares `needs: WI-016` (state/manifests/queue-2026-09-06.yaml:52-54) — the shapes lint_vault's five auto-fixable rules fire on, so that item does not require a second census pass. The census also carries the IDENTITY POOL TABLE that AC-5(c) reads: one row per token the corpus is CERTIFIED to use in an identity position — giving the token, the shape class it is constructed to carry, and the conductor's live-vault NON-OCCURRENCE scan for it: the counting command run and its verbatim stdout, showing `0` hits as a name token anywhere in the vault. That table is the only place the "these names are not real people's names" claim can be settled, because the suite is hermetic and cannot read the vault; AC-5(b)'s closure then makes that pool the sole name vocabulary an identity-bearing position in the corpus may use, so a real name cannot enter any of the identity fields AC-5(b) enumerates, nor a filename stem, without first appearing here. THE RELATION AC-5(c) ASSERTS IS A CONTAINMENT AND NOT AN EQUALITY, AND THE CONDUCTOR SHOULD READ THAT AS PERMISSION TO CERTIFY GENEROUSLY: this artifact lands in HEAD before Dave signs the criteria and long before the corpus exists, so it cannot be expected to predict the exact token set a not-yet-written build will consume; the builder's `NAME_POOL` must be a SUBSET of this table, a table row nobody ends up using is not a failure and not a leak (it carries its own scan), and the only thing that is ever RED is a token in an identity position with no row here. A table written to be exactly the corpus's vocabulary would make every later corpus edit a paired edit across the cage boundary, which is the cost this fence's WI-281 argument exists to avoid — so err long. The pool table's scope is identity tokens and the conductor must NOT write a row for a CONNECTIVE token: AC-5(b) fixes that set by enumeration at exactly `Me`, `My` and `Dave` — the package's own calendar/arrow prefix vocabulary (`obsidian_schemas/name_cleaning.py:46`, `:54`, `:55`) — and AC-5(c) asserts the table is disjoint from it, because these are the corruption classes' own furniture rather than identities and their live counts are NON-ZERO by construction: `Me to ` prefixes is one of the class table's own candidate rows, so a zero-hit provenance row for `Me` would be a false statement inside the artifact whose entire job is to be the trustworthy ledger. AND BECAUSE AC-5(b)'s `CONNECTIVE_SET` IS RECONCILED ONCE AGAINST THIS ARTIFACT BEFORE DAVE SIGNS, THE CLASS TABLE MUST RECORD EACH CORRUPTION CLASS'S FURNITURE LITERAL IN ITS MEASURED LETTER-CASE RATHER THAN PARAPHRASED: for `archive_prefix` and `unknown_contact` specifically, the live vault decides a spelling the code does not, because both branches' regexes carry `re.IGNORECASE` (`obsidian_schemas/name_validation.py:110`, `:113`) and this repository already commits the `unknown contact` literal BOTH lowercase (`tests/test_name_validation.py:248`, `:254`) and capitalized (`tests/test_name_gate.py:96`), so the pseudonymous specimen must reproduce the measured casing and the row must make that casing legible — whether `Unknown` and `Contact` become members of a set frozen by signature is a function of exactly it. If a furniture class's measured form does put a capitalized non-name run into an identity position, the conductor writes NO pool row for it — AC-5(c) asserts the pool table is disjoint from `CONNECTIVE_SET`, and `Contact` has no honest zero-hit row in this vault any more than `Ltd` does — it becomes a `CONNECTIVE_SET` member at reconciliation instead. Nor should the conductor write pool rows for generic organisation suffixes; AC-5(b) admits those from the package's own `_GENERIC_ORG_SUFFIXES` and `Ltd` has no honest zero-hit row here either. The census carries TWO explicit RULINGS the builder must not make for itself. FIRST, the live vault is a single flat directory, so a same-name collision is necessarily several distinct FILENAMES sharing one stored `name:`, which is structurally the same shape as "filename stem does not equal stored name" — the census must state, from the measured distribution, whether these are ONE class or TWO (do the vault's collisions co-occur with stem/name divergence, and does divergence occur on its own?), because AC-3's both-directions equality between the census's class list and the manifest's covered classes is unsatisfiable if two class rows cannot have distinct specimens. SECOND, the census must specifically LOOK FOR a postal address leaked into a name field — `### Examples of done` names that specimen by name and it is not any of AC-3's other draft classes — and must either confirm it present with a count and a pseudonymous specimen or state affirmatively that it does not occur in the live vault. It is charged rather than left to observation because AC-3's equality is against whatever the census declares: a census that recorded only the classes it happened to trip over could omit this one and every criterion would still be green while the shape Dave asked for silently never ships. The same instruction applies to any of AC-3's other floor classes the census cannot find — a class measured at ZERO is a row the conductor writes with `status: ABSENT`, not a row that may be left out. THIRD, AND IT IS WHAT DECIDES WHICH ROWS GET WRITTEN AT ALL: the class table must carry ONE ROW PER REFUSAL BRANCH THE PACKAGE DECLARES, keyed by that branch's `branch_id` and named with it, because AC-3's floor no longer transcribes a class list — it READS `{record.branch_id for record in TIER1_BRANCHES + COMPANY_TIER1_BRANCHES}` (`obsidian_schemas/name_validation.py:190-309`, `:371-438`) at test time and asserts a row of either status for each. The ten today are `email_chars`, `rfc2822_leak`, `arrow_connective`, `calendar_prefix`, `me_to_prefix`, `path_hostile`, `archive_prefix`, `unknown_contact`, `pure_digit` and `empty`, and FOUR OF THEM ARE CLASSES A CENSUS AUTHOR WOULD NOT OTHERWISE THINK TO MEASURE, so they are named here: `calendar_prefix` is the `Dave - X` / `Me - X` calendar-title prefix and is a SEPARATE class from `arrow_connective`'s `Dave -> X` and from `me_to_prefix`'s `Me to X` — all three raise the same `pattern` and must NOT be merged into one row, because their character profiles differ and `calendar_prefix` is the branch AC-5(b) cites as the source of `CONNECTIVE_SET`'s `Dave` member, so a corpus with no specimen for it leaves that frozen member unexercised; `email_chars` is an email stored as the whole `name:` value (`dave@example.com`, `:194`) as against `rfc2822_leak`'s at-mangled address fused onto a real name; `pure_digit` is a phone string stored as a name (`447700900123`, `:286`, the WI-083 sentinel shape — note its specimen sits in the same reserved UK range AC-5(a) mandates, so the pseudonymous specimen is nearly free); and `empty` is a whitespace-only or absent name, which `create_stub`'s `if name and name.strip():` guard has kept from ever firing in production (`:295-299`) and which this item introduces on the write path — a live vault plausibly holds none, in which case the honest discharge is an ABSENT row with count `0`, and that is a satisfied floor rather than a failure. Beyond those ten, the table carries the six shape classes AC-3 hand-lists because they have no branch to derive from (diacritics, hyphenated/multi-part surnames, whitespace damage, stem/name divergence, same-name collision, postal-address leak); those six are the only rows whose naming AC-3 reconciles before origination. Those two obligations are reconciled by the `count`/`status` columns and must stay that way: an ABSENT row is a first-class row of the class table (AC-3's CLASS FLOOR asserts it is PRESENT — for a branch-backed class by reading `branch_id` off the package, for one of the six shape classes from AC-3's hand list — so the shape Dave named cannot silently not-ship, and a refusal branch the live vault happens not to carry is discharged honestly with a zero row rather than omitted), and it is simultaneously outside AC-3's both-directions equality against the manifest's covered classes, which runs over MEASURED rows only (so a correctly-authored, honest census that rules a shape absent is never RED for it). Writing a zero row is therefore always the right move and never the cause of a failure — if a future edit makes those two obligations disagree again, this sentence is the one that was broken. It is declared HERE, at exploring rather than at ready, because it settles a premise the acceptance criteria are ABOUT: if the census shows a shape class nobody anticipated, or shows one of the classes named below occurring zero times, that is one line edited in a draft AC now, versus a D4b re-sign and a second interruption of Dave after origination (the WI-281 shape). `docs/**` is inside this project's write_authority (pipeline-runners.yaml:34-38), so the fence kind here is about EVIDENCE the caged builder cannot see, not about path permission. AND BECAUSE `docs/**` IS BUILDER-WRITABLE IN FULL — no carve-out for a landed precondition, and the pipeline's one merge-boundary integrity wall over docs is scoped by design to files carrying work-item frontmatter, which this artifact does not — THIS FILE IS FROZEN BY DIGEST ONCE IT LANDS, and the freezing is a step in the same one-time pre-origination edit that reconciles AC-3's six hand-listed shape classes and AC-5(b)'s `CONNECTIVE_SET`: after the artifact is committed to HEAD and before Dave signs, `sha256` over its bytes is computed once and written into AC-3(iv)'s `CENSUS_DIGEST` declaration, where the signature freezes it and where no build can reach it. THE ORDER IS LOAD-BEARING AND HAS ONE CONSEQUENCE THE CONDUCTOR SHOULD PLAN FOR: any correction to this artifact after the digest is taken but before signature costs a re-taken digest (one line, free while the criteria are drafts), and any correction AFTER signature costs a D4b re-sign — so the artifact should be complete and read once more before the digest is computed, not amended afterwards. This is not bureaucracy over an evidence file; it is what makes the artifact ground truth at all. AC-3(iii)'s class floor and AC-5(c)'s pool provenance both delegate their entire oracle to what this file says — the suite is hermetic and can re-derive not one of these counts or non-occurrence scans — so an unfrozen census is a ledger the party it audits can rewrite: a MEASURED row edited in place to `status: ABSENT` with count `0` drops the awkward specimen and leaves every AC-3 assertion green, and a fabricated pool row certifies a scan nobody ran while satisfying every check AC-5(c) makes. The conductor's part is small and is only this: land the file, then compute one digest before Dave signs.
```

*Extended at speccing, 2026-09-07. The precondition fence above is the ideation-partner's and is
reproduced byte-for-byte — not one character of it is edited (WI-300); the builder write targets
below are ADDED, never substituted. Every path is inside this project's `write_authority`
(`pipeline-runners.yaml:write_authority`, `:34-38` — `obsidian_schemas/**`, `tests/**`,
`scripts/**`, `docs/**`), so nothing here is unbuildable by construction (D7b), and the census fence
above is the only `kind: precondition` this item carries.*

**One thing the precondition fence describes in PROSE that two actors would implement differently,
pinned here at spec time because it costs one paragraph now and a build round later.** The fence
charges the conductor with a class table of six columns and a pool table of four, and AC-3 and
AC-5(c) both PARSE that artifact at test time — but nothing said in what SYNTAX. A GFM pipe table
cannot carry a scan command containing `|` (every counting form the fence names — `rg -c`,
`rg --count-matches`, a `| wc -l` pipe — contains one or is a pipe), and a conductor writing pipe
tables against a builder writing a fence reader is a RED floor against two correct artifacts. The
census's rows are therefore **flat `key: value` fences in the grammar this pipeline already uses for
`criteria`, `writes` and `fold`** — one ```census-class fence per class row, one ```census-pool
fence per pool row, one ```census-meta fence for the snapshot header, every value on ONE line.
`§2` of `## Design` gives the exact keys, the exact status vocabulary and the exact reader. This
adds no obligation the fence did not already impose: every column it names is a key, and no column
it names is dropped.

**A SECOND thing the fence leaves to two readings, pinned here for the same reason and at the same
cost — WHAT A POOL ROW'S SUBJECT IS.** The fence charges the conductor that "EVERY PSEUDONYMOUS
SPECIMEN'S IDENTITY-POSITION TOKENS MUST BE CONSTRUCTED STRINGS" and that each "needs a pool row
exactly as a `name:` does", and never says whether a TOKEN is a WORD or is whatever AC-5(b)'s pinned
run rule extracts. The two disagree on exactly the shapes this corpus exists to carry. **A pool row's
subject is an EXTRACTED TOKEN under §6.1's run rule and never a word a reader would separate** — a run
is maximal over {Unicode letters, combining marks, `'`, `-`} and is never restarted at an internal
capital or split at an internal hyphen, so `Anne-Sophie Legrain` yields `{Anne-Sophie, Legrain}` and
NOT `{Anne, Sophie, Legrain}`, and a specimen carrying a hyphen-fused pair owes a pool row for the
COMPOUND as well as (optionally) for its halves. Certifying the halves alone leaves the compound
uncertified, AC-5(b) then refuses it in an identity position, AC-5(c) cannot be satisfied by adding a
row (`## Scope Boundary` forbids the builder writing the census), and the build reddens on a wholly
correct corpus with no in-cage remedy — the R10 shape, one artifact out. The landed census satisfies
this: its Method section states the granularity in as many words, and `Brenvik-Tarnquil` and
`Pellworth-Wexlund` each carry their own row beside `Brenvik`/`Tarnquil` and `Pellworth`/`Wexlund`.
**M2's abort gate is what keeps it satisfied for every later census pass** — the gate refuses when the
artifact carries an identity-position token its own pool table does not certify, run through
`identity_tokens` rather than through a reader's idea of a word (§6.5, Task 3). This adds no
obligation the fence did not already impose either; it settles which of two readings of its own
sentence the machine takes.

```writes
path: obsidian_schemas/repositories/base.py
why: Task 2 — the module-level SKIP_REASONS frozenset (this item's ONLY package change) plus the three module-level reason constants _skip_reason returns by name, per AC-4's "create the declaration rather than keep transcribing it" fold; inside write_authority (P7).
```

```writes
path: tests/derivations.py
why: Task 2 — TWO syntax scans: skip_reason_return_values, binding SKIP_REASONS to _skip_reason's own returns, and skip_reason_literal_sites, the class-closing wall returning every file whose parsed syntax carries a str Constant equal to a SKIP_REASONS member (§4). Both land HERE and nowhere else because `ast` is single-homed to this module by a standing set-EQUALITY wall over python_files_under(PACKAGE_ROOT, TESTS_ROOT), asserted twice (tests/test_name_gate_wall.py:_check_the_ast_capability_stays_single_homed:1132, live assertion at :1136, and tests/test_loud_fail_harness.py:103), so a syntax-reading predicate has exactly one legal home (P9). Reading syntax rather than source text is what lets base.py:37's `#` type comment and errors.py:112's prose docstring stay untouched with no exception carved for either.
```

```writes
path: tests/fixtures/vault
why: Tasks 3-4 — the frozen corpus DIRECTORY, ~50 flat markdown notes. The directory is declared rather than its members because the members' FILENAMES are a function of the census's measured shape classes and pool tokens, and the census is a precondition that does not exist yet: enumerating fifty concrete paths here would be inventing the artifact's content, which is the D2 fixture-drawn-from-fixtures this item rejects. The filename GRAMMAR is pinned in Design §1.2 so the set is derivable rather than arbitrary, and `tests/**` is inside write_authority (P7) so every member is writable whatever it is called.
```

```writes
path: tests/fixture_vault.py
why: Tasks 4-8 — the declared manifest (NOTES / SKIPS / LOADABLE / RESOLVABLE / IDENTITY_FIELDS), the frozen CORPUS_DIGEST with its regeneration recipe in the module docstring, materialize_vault's byte copy, and AC-5's three literal frozensets. No test logic lives here. It imports MALFORMED_FRONTMATTER / SCHEMA_DRIFT / UNREADABLE from obsidian_schemas.repositories.base for SKIPS's reason values rather than re-spelling them, because §4's skip_reason_literal_sites wall sweeps this file too; it is NOT a check module and must not carry the interpreter bridge (§3.1).
```

```writes
path: tests/test_fixture_vault.py
why: Tasks 2 and 4-9 and 12 — the five acceptance checks, the SKIP_REASONS binding test with its planted-shape battery and the one hand-typed spelling pin, the identity-token extractor's claimed-match-shape battery (WI-235), the census fence reader, the threat model's M1 scan over the census's own bytes plus the CENSUS_PROSE_ALLOWLIST frozenset it needs (§6.5 — declared HERE and not in the manifest, because AC-5(b) is signed text naming fixture_vault.py's frozensets as exactly three), and the wall-membership + battery-parity runs. New module; every `check:` name AC-1 through AC-5 declares resolves here and nowhere else, which is the uniqueness rule tests/test_ac_interpreter.py:76-87 states for this project. It OPENS with `from tests.ac_interpreter import ensure_project_interpreter` and `ensure_project_interpreter(__file__)` as its first executable statement, ahead of every package import, exactly as this project's six other library-executing check modules do (§3.1) — all five of this item's checks execute the library behind pydantic, and tests/ac_interpreter.py:7-25 records the five-of-five ModuleNotFoundError battery that convention exists to prevent.
```

```writes
path: tests/test_parser.py
why: Task 10 — D5's proof set. TestParseMarkdownFile.test_parse_file's inline heredoc is deleted and replaced by top-level test_corpus_person_note_parses_to_its_declared_values, which parses a materialized corpus note against the manifest's declared oracle.
```

```writes
path: tests/test_writer.py
why: Task 10 — D5's proof set. TestRoundtrip.test_roundtrip_preserves_data's inline heredoc is deleted and replaced by top-level test_corpus_note_round_trips_through_the_write_door.
```

```writes
path: tests/test_repositories.py
why: Task 10 — D5's proof set, ADDITIVE only: top-level test_corpus_vault_loads_through_every_repository. The temp_vault fixture at :15-263 is deliberately NOT repointed — see Design §9.1 for the argument and the cost of deferring.
```

```writes
path: tests/test_loud_fail_load.py
why: Task 11 — the TWO hand-typed sites in this module, not one. :187-188 transcribes the whole codomain and reads SKIP_REASONS instead, which is strictly stronger (a fourth reason with no specimen in that module's matrix vault goes RED where the hand-typed set stays green); :209 re-spells "unreadable" twenty-two lines below it, inside the same function, and reads the UNREADABLE constant instead. Both are named because §4's skip_reason_literal_sites wall asserts set EQUALITY over the vocabulary's legal homes and would be RED with either left in place.
```

```writes
path: tests/test_name_gate.py
why: Task 11 — the third hand-typed site, `assert _skip_reason(exc) == "unreadable"` at :152, which reads the UNREADABLE constant instead. One line and one import; nothing else in this module is touched, and its own assertions are unaffected because the constant's value is the same string. Declared as a write target rather than left out of scope because §4's wall is a set EQUALITY over the whole of python_files_under(PACKAGE_ROOT, TESTS_ROOT) — an unrepointed site here is RED, so "leave it" was not an available arm.
```

## Acceptance Criteria

Originated cold-start, approval-only, re-derived from the frozen `## Intent`. **FROZEN — Dave signed
these criteria on 2026-09-08 (`## AC Sign-off`, `signed_at: 2026-09-08T01:14:48+01:00`), and the
frozen text is `docs/spec-reviews/WI-016-dave-review-2026-09-08.md`.** This preamble read "Draft …
Not yet frozen" until 2026-09-08; it was true when written and is corrected here rather than left,
because it is the sentence a later gate reads to decide whether the quality bar's Check 12 fires and
it had come to say the opposite of the truth. Every remaining correction to a criterion's own text is
now a D4b re-sign, not a word in a draft — §10 P-2 records the one such correction already made
(AC-3(iv)'s re-taken `CENSUS_DIGEST`) and the single re-sign it owes. Every `check` is a top-level
zero-argument `def test_*(` that signals failure by raising, per the battery's direct-invocation
contract (`tests/support.py:1-19`).

```criteria
id: AC-1
desc: A frozen corpus exists at `tests/fixtures/vault/` holding at least 50 notes, and it is materialized by BYTE COPY rather than by any write door. Three legs. (a) FROZEN — `tests/fixture_vault.py` declares a digest constant computed over the corpus as `sha256` of the sorted sequence of (CORPUS-RELATIVE POSIX path, file bytes), each field NUL-framed, and the digest recomputed at test time EQUALS it, so editing, adding or deleting any fixture note without updating the constant is RED. THE KEY IS CORPUS-RELATIVE AND NEVER REPO-RELATIVE, AND THAT WORD IS LOAD-BEARING RATHER THAN PEDANTIC: the corpus is ONE FLAT DIRECTORY (`## Approach`), so a corpus-relative path IS the bare filename — exactly the `path.name` §5.2's walk hashes — while a repo-relative key would make leg (b) UNSATISFIABLE BY CONSTRUCTION, because the materialized tree lives under a caller-supplied temp directory that has no repo-relative path at all. An earlier draft said "repo-relative" here and left the item buildable two ways, since §5.2's code keys on the name; the two coincide once the word is corpus-relative, and fixing it while these criteria are drafts costs one word where fixing it after signature costs a D4b re-sign. (b) FAITHFUL — `materialize_vault(dest)` into a fresh empty directory reproduces the corpus byte-for-byte: the same relative path set and the same per-file bytes, with the digest over the materialized tree equal to the same constant — which is a real assertion only because the digest's key is the filename and therefore travels with the bytes. AND THE SECOND CALL IS ASSERTED TOO, NOT ONLY THE FIRST: `materialize_vault` is re-invoked against that SAME `dest` after a foreign file has been placed in it, and the leg asserts that every corpus member is overwritten with identical bytes, that the digest over the corpus members is unchanged, and that the FOREIGN FILE SURVIVES — `materialize_vault` adds, it never empties a caller-supplied directory. The oracle for the second call is deliberately the corpus members and NOT `corpus_digest(dest)` over the whole directory, because the foreign file is a member of that tree and not of the corpus. Without this the idempotency and no-clean rules `## Edge Cases` decides are resolved in prose with nothing exercising them, and a future `shutil.rmtree(dest)` added "for cleanliness" would destroy a caller's directory with every criterion still green. (c) THE DISCRIMINATOR — the corpus contains at least one note whose stored `name:` matches a live Tier-1 branch (an arrow-connective descriptor and a path-hostile name are both present, named in the manifest as such), and materialization of the WHOLE corpus succeeds with those notes present and byte-identical. A build that materializes via `repo.save()`, `write_markdown_file` or `create_stub` raises `NameGateRefusal` on exactly those members and is RED on this leg.
why: "Frozen" without a mechanism is a wish — nothing otherwise stops a future test from editing a fixture to make itself pass, and the corpus then drifts silently for every other test that trusted it. Legs (a) and (b) are separate on purpose: (a) catches an edit to the checked-in bytes, (b) catches a materializer that transforms on the way out (normalizing line endings, re-serializing YAML, dropping a note it cannot parse) — a corpus whose specimens are cleaned up in transit is the Alice/Bob corpus wearing the real one's name. Leg (c) is the planted discriminating member (WI-286): byte-copy is not a performance choice, it is the ONLY mechanism that can carry these specimens, because WI-021's gate is a predicate on every frontmatter-writing arm and WI-022 extends it to companies — the gate exists precisely to make these notes uncreatable through the package. Without leg (c) a builder reaches for the repository API (the obvious, idiomatic thing), the refused specimens get quietly dropped from the corpus, and the corruption corpus this item is FOR is the part that silently does not ship.
check: test_fixture_vault_is_frozen_and_materialized_by_byte_copy
kind: test
```

```criteria
id: AC-2
desc: Every entity type the package declares has at least one fixture note, and each round-trips against a DECLARED oracle. The sweep is derived from the class's own declaration — the set of type strings covered by the manifest is asserted EQUAL to `set(TYPE_TO_MODEL)` (`models.py:309-318`, 8 members today), so a hand-listed sample is RED and a ninth type added later joins the sweep automatically and fails until it has a fixture. For EVERY member: (a) parsing its fixture note yields an instance of that member's model class; (b) the parsed instance's field values equal the manifest's DECLARED expected values for that note — values hand-written from the model definition, never produced by running the parser and recorded (a manifest generated by the code under test asserts only that the parser agrees with itself); and (c) writing the parsed model back reproduces the note's frontmatter — AND THE KIND OF EQUALITY IS NAMED RATHER THAN LEFT TO THE BUILDER: the written file is RE-PARSED and its frontmatter MAPPING is asserted equal to the manifest's DECLARED expected values, the same oracle leg (b) uses, never byte-equal to the original file, because YAML key order, quoting style and list style are serializer choices this corpus does not exist to pin, while byte-level fixity of the checked-in bytes is already AC-1(a)'s digest; leg (c) is not thereby redundant with leg (b), because it is parse→write→parse and its job is to catch a field the WRITE path drops or mangles. THE ROUND-TRIP SUBJECT AND ITS DOOR ARE NAMED, NOT LEFT TO THE BUILDER: the manifest declares for each of the 8 types exactly ONE note as that type's `roundtrip_representative`, and that note must be GATE-CLEAN — WHICH IS THE DOOR'S OWN PREDICATE READ FROM THE PACKAGE, NEVER A LIST OF CORRUPTION FORMS TRANSCRIBED HERE: for a `person` representative, NO record of `TIER1_BRANCHES` matches its stored name (`Tier1Branch.matches`, `name_validation.py:179-184` — the same test the chain applies, and the same sweep unit `tests/test_name_gate.py:212` already uses); for a `company` representative, no record of `COMPANY_TIER1_BRANCHES` matches; and for the other six types `gate_write` is a pass-through (`name_gate.py:319-344`) so the condition is VACUOUS and nothing is asserted. Arrow-connective descriptors, `Me to ` prefixes, path-hostile characters and RFC 2822 leaks are four of the ten branches and are useful as EXAMPLES, but the four-item list they came from was neither the predicate nor a complete gloss on it — it omitted `email_chars`, `calendar_prefix`, `archive_prefix`, `unknown_contact`, `pure_digit` and `empty`, so a representative tripping any of those six would be refused by the very door leg (c) writes it through; leg (c) writes it through `write_markdown_file` — the GATED door, which calls `gate_write` on the assembled payload before serializing (`writer.py:252-253`), as against the bare `write_frontmatter` serializer — into a temp directory, so leg (c) additionally proves the clean representatives are creatable through the real write door. WHAT THAT PROVES DIFFERS BY TYPE BY DESIGN, AND IS CLAIMED AT ITS REAL SIZE RATHER THAN OVERCLAIMED: `gate_write` returns `dict(introduced)` unchanged for every declared type that is neither person nor company (`name_gate.py:319-344` — the company arm calls `validate_strict` against `COMPANY_TIER1_BRANCHES` for its raise behaviour and discards the repaired string, then falls to the same return), so for `person` and `company` leg (c) proves the gated door accepts a clean representative, and for the other six it proves the pass-through is a pass-through — which is the correct claim for a package whose gate is deliberately typed, not a gap in the criterion. The corruption specimens are NEVER a `roundtrip_representative`; their expected behaviour is AC-1(c)'s and AC-3's, and a build that picks one of them as its `person` representative discovers leg (c) refusing with `NameGateRefusal` rather than passing. Note the ASYMMETRY this criterion carries alone: `watch`, `explore`, `gift-idea` and `exploration` have no repository and therefore no filename glob, so all three legs for those four members are PARSER-level (`parse_markdown_file` / `write_markdown_file` against a path), and they are outside AC-4's repository-level surface entirely. `exploration` is named explicitly as a member: today it has zero test references anywhere under `tests/` (P4), and this criterion is where that ends. THE NARROWING ARM, AND ITS POPULATION IS DERIVED RATHER THAN NAMED: the types with no body config are read at test time as `set(TYPE_TO_MODEL) - set(ENTITY_BODY_CONFIG)` (`models.py:309-318`, `body_sections.py:303-324` — `watch`, `explore` and `gift-idea` today, the config declaring 5 of the 8), and for exactly those members the body expectation asserted is `get_default_body(<type>) == ""` — the declared marker, stated as by-design — with no section list invented for them; for each member of the INTERSECTION the assertion is that config's declared sections. Both sides are dict literals the package exports and this criterion already reads one of them, so a ninth type with no config joins the narrowing arm automatically and adding a `watch` entry to `ENTITY_BODY_CONFIG` moves it to the other arm without an AC edit — where the hand-listed three went RED against a change that was correct.
why: A derived sweep proves MEMBERSHIP, never correctness (WI-286): a sweep that only asserts "a fixture exists for each type and it parses" is passed by a corpus of eight empty notes and by a parser that returns a default-constructed model for anything. Leg (b) is the oracle that separates a right answer from a wrong-but-self-consistent one, and it is the reason the expected values must be hand-written — the single most likely shortcut here is generating the manifest by parsing the corpus, which produces a green suite that has verified nothing at all. Deriving from `TYPE_TO_MODEL` rather than listing the types is what closes the class in the WI-185 sense; three of the eight (`watch`, `explore`, `gift-idea`) are in the same untested position `exploration` is, and a hand-list is exactly how they stayed there. The narrowing arm exists because for those three there IS no right body-section answer to assert — `get_default_body` returns `""` for them by construction — and inventing one would be a fixture asserting a fact about the corpus that the code does not hold; naming the marker keeps the sweep total without manufacturing an oracle. Naming the round-trip SUBJECT and its DOOR closes the last cell a builder could fill two ways: `write_markdown_file` is the gated door — it calls `gate_write` on the assembled payload before serializing (`writer.py:252-253`) — while `write_frontmatter` (`writer.py:134`) is the bare YAML serializer carrying no gate of its own, and the two disagree on precisely the notes this corpus exists to carry — so an unnamed "write it back" either quietly picks the ungated serializer, in which case leg (c) says nothing about the write door, or picks a corruption specimen as some type's representative, in which case the criterion goes RED for a reason that has nothing to do with round-tripping and the build spends a round rediscovering the gate. Stating the parser-level asymmetry for the four repository-less types is the same economy: it is the difference between a spec that knows those four are AC-2's alone and a build that goes looking for a `WatchRepository` that has never existed. THE NARROWING ARM'S POPULATION AND THE GATE-CLEAN PREDICATE ARE BOTH DERIVED NOW, AND THE REASON THEY WERE NOT IS THE ONE WORTH RECORDING. This criterion's own POPULATION was derived from `TYPE_TO_MODEL` from round 1, which is exactly why the round-7 sweep — the pass that applied "derive, never transcribe" to every criterion at once — marked AC-2 done and moved on: it swept one enumeration per criterion rather than one per enumeration, and AC-2 held two more. The narrowing arm hand-listed `watch`, `explore`, `gift-idea` where `set(TYPE_TO_MODEL) - set(ENTITY_BODY_CONFIG)` computes it, and GATE-CLEAN was defined as four named corruption forms where the door applies all ten `TIER1_BRANCHES` for `person` and all five `COMPANY_TIER1_BRANCHES` for `company`. NEITHER HAD A GREEN-OVER-WRONG ROUTE and that is stated rather than inflated: both fail LOUD, costing a build round rather than a property — a ninth type with no config makes the sweep raise on a missing `ENTITY_BODY_CONFIG` key that reads as a missing fixture, and a representative tripping one of the six unlisted branches is refused by `write_markdown_file` and reddens leg (c) for a reason that has nothing to do with round-tripping, which is the outcome this criterion's own naming of the door exists to prevent, left open one clause later. They are fixed anyway because the fix is one line of draft text now against a signed criterion later, because each removes a paired edit that fires whenever the package gains a type, a body config or a refusal branch, and because the four-item gloss sat beside a rule stated correctly next to it ("the corruption specimens are NEVER a `roundtrip_representative`"), which is precisely the shape that goes stale unnoticed. AND EACH DERIVED POPULATION IS ASSERTED NON-EMPTY AND AGAINST ITS SIZE AT THE MOMENT OF WRITING (LESSONS #46 — a green check is evidence only after it has been seen red): `set(TYPE_TO_MODEL)` is asserted to hold exactly 8 members and the narrowing arm's difference exactly 3, because a derived sweep returns green when it works and green when it silently reads nothing — an import resolving to an empty dict, a renamed attribute — and a size assertion is the cheapest available form of having seen it red. The sizes are the population's, never the oracle's: what each member must PARSE TO stays hand-declared in the manifest.
check: test_every_entity_type_round_trips_against_declared_values
kind: test
```

```criteria
id: AC-3
desc: Every corruption shape class the census MEASURED has a specimen in the corpus, every specimen has a declared verdict, and every class the census RULED ABSENT is on the record rather than missing. The class table is read from `docs/vault-shape-census.md` (the precondition artifact), whose rows carry a class id, a `count`, a `status` of MEASURED or ABSENT, the scan command, its stdout and — for MEASURED rows only — a specimen. THE THREE ASSERTIONS ARE SCOPED BY STATUS, WHICH IS WHAT KEEPS THIS CRITERION AND `## Write Targets` FROM CONTRADICTING EACH OTHER. (i) EQUALITY, over MEASURED rows only: `{class id : status == MEASURED}` EQUALS the manifest's covered classes, both directions — a measured class with no specimen in the corpus is RED, and a specimen belonging to no measured census class is RED. An ABSENT row is outside this equality entirely and is never RED for having no specimen. (ii) PER-ROW SHAPE, conditional on status: a MEASURED row must carry a count > 0, a non-empty command, non-empty stdout and a specimen; an ABSENT row must carry a count of exactly 0, a non-empty command, non-empty stdout and an affirmative absent ruling, and must NOT carry a specimen — so a class cannot be hidden by leaving its status blank, and an "absent" ruling cannot be asserted without the scan that supports it. THE NON-EMPTY-STDOUT ASSERTION IS SATISFIABLE AT BOTH STATUSES ONLY BECAUSE OF A CONSTRAINT ON THE COMMAND, AND THAT CONSTRAINT IS PART OF THIS CRITERION RATHER THAN AN ASSUMPTION IT MAKES ABOUT THE CONDUCTOR: `## Write Targets` requires every recorded scan command to emit a COUNT rather than raw match lines, so a true zero result records verbatim as `0`. Asserted against a bare match-listing scan this leg would be unsatisfiable by construction on exactly the honest ABSENT row it exists to police — a search that finds nothing writes nothing — and the only routes through would be typing non-verbatim prose into the ledger or leaving a correctly-ruled-absent class permanently RED. (iii) THE CLASS FLOOR — DERIVED FOR THE HALF THAT HAS A DECLARATION, HAND-LISTED ONLY FOR THE HALF THAT DOES NOT. The ids below are asserted PRESENT in the table as rows of EITHER status, which is the machine-checked form of `## Write Targets`'s "a class measured at ZERO is a row the conductor writes": it is what stops a census from silently omitting a shape, rather than trusting prose to the conductor. **THE BRANCH HALF IS READ FROM THE PACKAGE AT TEST TIME AND IS NOT TRANSCRIBED INTO THIS CRITERION AT ALL** — the floor includes `{record.branch_id for record in TIER1_BRANCHES + COMPANY_TIER1_BRANCHES}` (`name_validation.py:190-309` and `:371-438`), the same runtime read of an exported declaration AC-2 makes against `TYPE_TO_MODEL` and AC-4 against `_skip_reason`'s codomain, and the same sweep unit `tests/test_name_gate.py:212` and `tests/test_company_name_contract.py:369` already use — so the census's class table must carry a row for EVERY refusal branch this package declares, and a branch added to either table later joins the floor automatically instead of waiting for someone to notice. Ten ids today, and THE DERIVED SET IS ASSERTED NON-EMPTY AND OF EXACTLY THAT SIZE (LESSONS #46: a derived read returns green when it works and green when it silently reads nothing — an import resolving to an empty tuple, a renamed `branch_id` attribute — so the size at the moment of writing is the cheapest available form of having seen the derivation red; it is the POPULATION's size and never an oracle, since what each specimen must produce stays hand-declared): `email_chars`, `rfc2822_leak`, `arrow_connective`, `calendar_prefix`, `me_to_prefix`, `path_hostile`, `archive_prefix`, `unknown_contact`, `pure_digit`, `empty`. THE FLOOR IS ASSERTED IN BOTH DIRECTIONS OVER BRANCH-KEYED ROWS, not only as census ⊇ derived: every census row whose id is branch-shaped must also be IN the derived set, so a row naming a `branch_id` the package no longer declares is RED rather than surviving as a phantom — assertion (i) supplies the reverse direction for MEASURED rows only, which leaves exactly the ABSENT phantom uncovered, and LESSONS #45 says a check documented as deliberately one-directional is an open defect rather than a note. THE COMPANY ARM IS OUT OF THIS CORPUS'S SCOPE, STATED AFFIRMATIVELY RATHER THAN CLAIMED AS A SIDE EFFECT: five ids appear in both tables (`email_chars`, `arrow_connective`, `path_hostile`, `archive_prefix`, `empty`) but a deduped floor writes ONE census row per `branch_id` and the corpus carries ONE specimen, whose DECLARED TYPE decides which table `gate_write` consults (`name_gate.py:329-343` vs `:361-363`) — so a person-typed `path_hostile` specimen exercises the person arm ONLY, and an earlier draft's "those specimens exercise the company arm as well" was one word too strong. That is not a coverage hole and no company-typed specimen is required here: the company table already has its own in-tree refusal sweep over every one of its records' `specimen` and `negative_specimen` (`tests/test_company_name_contract.py:359-459`), which is the WI-022 surface this item does not duplicate. THE CLASS TABLE'S ROW ID FOR A BRANCH-BACKED CLASS IS THE `branch_id` ITSELF, so those ten need no naming reconciliation before origination and cannot drift apart from the package. THE KEY IS `branch_id` AND NEVER `pattern`: `arrow_connective`, `calendar_prefix` and `me_to_prefix` all RAISE the shared pattern `calendar_prefix` (`:216`, `:228`, `:240`, stated outright in the dataclass docstring at `:152-154`), so a pattern-keyed floor would silently re-merge three classes this criterion treats as separate — `Dave -> Thomas Gatten`, `Dave - Thomas Gatten` and `Me to David Field` (`:217`, `:229`, `:241`) are three distinct character profiles the census must measure one at a time, and the census must be authored against those profiles rather than against a paraphrase of them. **THE HAND-LISTED HALF IS THE SIX SHAPE CLASSES THAT HAVE NO BRANCH**, where there is no declaration to derive from and this list is the only available statement of intent: diacritics, hyphenated/multi-part surnames, whitespace damage (double-space / leading-trailing — Tier 2, `_DOUBLE_SPACE_RE` `:445`, no Tier-1 branch), filename-stem-does-not-equal-stored-name divergence, a same-name collision of at least three notes, and A POSTAL ADDRESS LEAKED INTO A NAME FIELD, which `### Examples of done` names by name and which no branch is (the nearest, `rfc2822_leak`, is an at-mangled address FUSED ONTO a name — its own specimen is `Naomi Pavie naomipavieatspeechmaticscom`, `:202-205` — not a postal address), so the census is charged in `## Write Targets` with either confirming that one present with a MEASURED row and a specimen or writing an ABSENT row that states affirmatively it does not occur in the live vault. RECONCILED 2026-09-07 against `docs/vault-shape-census.md`, whose six hand-listed ids are `diacritics`, `hyphenated_surname`, `whitespace_damage`, `stem_name_divergence`, `same_name_collision`, `postal_address_in_name` (the ONE-or-TWO ruling: TWO classes — collision ABSENT, divergence MEASURED). ONLY THOSE SIX are reconciled to the census's own naming BEFORE origination — the artifact is a precondition and lands in HEAD while these criteria are still drafts (WI-300), so a shape class the census names differently costs one edit here rather than a re-sign. For each class on the floor, the manifest declares the verdict the specimen must produce and the test asserts it: either a refusal (`NameGateRefusal` — the WI-021 leaf, never the `LoudFailError` root — carrying the named `pattern` on its `.pattern` attribute when the specimen's name is re-introduced through a write arm), or a declared cleaned form (`clean_person_name` output asserted equal to a hand-written string), or a declared successful byte-identical load. SOME BRANCHES WILL PLAUSIBLY DISCHARGE AS ABSENT, AND THAT IS THE FLOOR WORKING RATHER THAN AN OBLIGATION THE CORPUS CANNOT MEET: `empty` above all — `create_stub` guards its validator call with `if name and name.strip():`, so the branch has never fired in production and this item is what introduces it on the write path (`name_validation.py:295-299`) — and a live vault holding no empty-named note gets an ABSENT row with its count, command and stdout, satisfies assertion (iii), never enters assertion (i)'s equality, and obliges no specimen. Both discharges satisfy assertion (iii) and only the MEASURED one enters assertion (i)'s equality, so a class ruled absent is on the record and is not a failure. TWO OF THE HAND-LISTED SIX MAY ALSO BE ONE: the corpus is a single flat directory (see `## Approach`), so a same-name collision is necessarily several distinct filenames sharing one stored `name:` — structurally the divergence class — and the CENSUS rules whether the live vault separates them. If it rules them ONE class, it writes one row whose id the floor accepts for both members of the pair, and the manifest's covered-class set FOLLOWS that ruling; assertion (i) is RED only when manifest and census disagree over MEASURED rows, never for the table holding fifteen class rows rather than sixteen. (iv) CENSUS FIXITY — THE ARTIFACT THIS CRITERION TREATS AS GROUND TRUTH IS FROZEN BY THE SAME MECHANISM AC-1(a) GIVES THE CORPUS, AND ITS EXPECTED VALUE HAS NO IN-CAGE HOME. `sha256` over the bytes of `docs/vault-shape-census.md`, recomputed at test time, EQUALS a 64-character lowercase hex literal — and THE LITERAL LIVES IN THIS CRITERION'S OWN TEXT, filled in at the same one-time pre-origination edit that reconciles this criterion's six hand-listed shape classes and AC-5(b)'s `CONNECTIVE_SET`: the census lands in HEAD as the WI-300 precondition BEFORE Dave signs, so its digest is knowable exactly then, and the signature freezes it. The test READS that literal out of the AC-3 `criteria` fence in `docs/vault-fixtures.md` — a plain in-tree file read, the same hermetic move this criterion already makes on the census, no subprocess and no vault call — rather than comparing against a constant declared in `tests/fixture_vault.py`, and the reason is the whole point of the leg: `docs/**` is builder-writable in full (`pipeline-runners.yaml:34-38`, P7 — no carve-out for a landed precondition), so a constant the build owns can be updated in the same commit that edits the census, and the check certifies nothing. `fixture_vault.py` MAY restate the digest for readability, but the value ASSERTED AGAINST is the one in the signed criterion. The leg additionally asserts that exactly ONE such declaration was found WITHIN THE AC-3 `criteria` FENCE and that it is well-formed 64-character lowercase hex, so a reader helper that finds nothing is RED rather than vacuously green (LESSONS #46 again). THE UNIQUENESS IS FENCE-SCOPED AND NEVER FILE-WIDE, AND THAT SCOPE IS LOAD-BEARING RATHER THAN TIDY: every gate section in this document quotes the criterion text it reviews, so once `CENSUS_DIGEST` carries a real 64-hex value, ONE round-10 quotation of the filled declaration would turn a file-wide uniqueness assertion RED — and its only remedy would be editing a historical gate section, which is the one edit this document's whole carry-forward convention exists to forbid. The read is therefore bounded to the fence the signature freezes, which is the same text the assertion is about. THE DECLARATION, FILLED AT THE 2026-09-07 PRE-ORIGINATION EDIT ONCE THE CENSUS WAS IN HEAD (re-taken 2026-09-08 after the M1 prose remediation and the compound-token pool rows), IS `CENSUS_DIGEST = sha256:4cb7945f643415b7fba9347f2f0ecee30a3b054bb9aa1ba875e2551b93b599cb`; origination must not proceed while a placeholder stands, which is the same door AC-3's class-naming and AC-5(b)'s `CONNECTIVE_SET` reconciliation already pass through and costs no extra interruption of Dave. The test reads both artifacts, asserts assertions (i)–(iv) over their parsed rows and text, and makes no subprocess, network or live-vault call.
why: This criterion is what makes the corpus a corruption corpus rather than a tidy sample, and reading the class list FROM the census is what gives the precondition artifact teeth inside the suite: without it the census can be discharged as one hand-waved prose paragraph and the corpus quietly reverts to D2, a fixture drawn from the fixtures that already exist — which LESSONS #27 says is structurally blind to exactly the tail the corpus is for. Equality in both directions is deliberate: one direction stops the corpus under-covering the measured estate, the other stops it accumulating specimens nobody measured, which is how a corpus starts asserting things about a vault that no longer holds. Declaring a verdict per specimen rather than merely holding the bytes is the WI-286 oracle again — a corpus that only CONTAINS `"Dave -> Thomas Gatten (Adzact)"` proves nothing about whether anything refuses it, and the classes listed are precisely the forms this package has already been burned by, so each one having a stated expected answer is what lets the next name-touching change regress against them instead of rediscovering them. Naming the address-leaked-into-a-name-field class explicitly closes the one gap between this list and Dave's own picture of done: assertion (i)'s equality is against whatever the census DECLARES, not against `### Examples of done`, so a census that recorded only the classes it happened to trip over could have dropped the one specimen Dave asked for by name and left every criterion green. DERIVING THE BRANCH HALF OF THE FLOOR RATHER THAN TRANSCRIBING IT IS THE ONE THING TO KEEP IF THIS CRITERION IS EVER EDITED AGAIN, AND THE HISTORY IS THE ARGUMENT. This floor has been hand-corrected twice and been wrong both times: round 3 added it, round 6 added `archive_prefix` and `unknown_contact` and asserted it then covered "eight of the ten live person Tier-1 branches", and a seventh read of `TIER1_BRANCHES` itself found the real prior count was FOUR (`rfc2822_leak`, `arrow_connective`, `me_to_prefix`, `path_hostile`) rising to six, with `calendar_prefix`, `email_chars`, `pure_digit` and `empty` all still missing. `calendar_prefix` was the expensive one: it is a live branch with its own id, its own specimen (`Dave - Thomas Gatten`, `:229`), its own recovery arm (`name_cleaning.py:46`, stripped at `:121`) and it is the sole source of `CONNECTIVE_SET`'s frozen `Dave` member — AC-5(b) justifies that member by citing exactly this branch — while this criterion's own parenthetical named it as a class distinct from the arrow one in the same breath that the floor omitted it. Nothing in assertions (i)–(iii) reads the package's branch table, so a conductor authoring the census works from this list, never thinks to measure `Dave -`/`Me -` prefixes as a class of their own, and every assertion stays green over a corpus with no specimen for four of the package's ten refusal branches — which is precisely the silent omission assertion (iii) exists to make impossible, defeated because the floor never named the shape for the census to measure. That is LESSONS #45 exactly: a registry validated only against itself is a mirror, not a census, and the remedy is to derive the actual population from the source and assert set-equality with the registry. So the fix removes the hand-transcription rather than pruning its third instance — the branch half is now a runtime read of two tuples the package exports and whose `branch_id` is unique by its own docstring, and only the six classes with no declaration to read stay hand-listed. Keying on `branch_id` rather than `pattern` is load-bearing and not a detail: three branches deliberately raise the shared pattern `calendar_prefix`, so a pattern-keyed derivation would re-merge the three classes this criterion separates and reintroduce the same gap by another route. It stays a FLOOR rather than a promise: if the live vault carries no archived or scanner-artifact names, the census writes each an ABSENT row with its count, command and stdout, assertion (iii) is satisfied, assertion (i) never sees them, and nothing is RED. Scoping the three assertions BY STATUS is what makes that fix hold without turning honesty into a failure: the previous draft charged the conductor to write a zero row and then, in the same breath, marked a class with no specimen RED — so a correct, honest census was a false block and the cheapest way back to green was to delete the row, which is exactly the silent omission the fix was for. Splitting them gives each obligation its own assertion: (iii) makes the row's PRESENCE mandatory (the machine-checked form of the prose charge, so no shape can vanish), (i) makes only MEASURED rows owe a specimen, and (ii) stops either from being discharged with a blank cell — a status left empty, a count with no scan behind it, an absent ruling with no command. The floor being reconciled before origination is the WI-300 ordering doing its job: the census lands in HEAD while these are still drafts, so a class the artifact names differently is one line edited here rather than a frozen criterion and a second interruption of Dave. ASSERTION (iv) EXISTS BECAUSE EVERY OTHER ASSERTION IN THIS CRITERION TRUSTS AN ARTIFACT NOTHING IN THIS PIPELINE FREEZES, AND THAT WAS THE LAST UNGUARDED ESCAPE HATCH IN THE SET. The suite is hermetic and cannot read the live vault, so the census is the ONLY place "this class occurs N times in the real vault" can be settled — and its content is entirely unprotected once it lands: `docs/**` is in this project's `write_authority` in full with no carve-out for a landed precondition (`pipeline-runners.yaml:34-38`, P7), the build-spawn precheck and WI-300's grounding-ordering backstop check only that the path is SOME committed blob in HEAD at one moment before the build starts and never compare its content afterwards, and the pipeline's one merge-boundary integrity wall over docs is scoped BY DESIGN to files carrying work-item frontmatter — a shared non-work-item doc's edit is declared legitimate build traffic there, which `docs/vault-shape-census.md` is, carrying no `id: WI-*` of its own. The concrete route it closes, and it is not hypothetical for either criterion that reads the artifact: a builder facing a MEASURED row whose character profile is awkward to author faithfully edits that row in place to `status: ABSENT`, `count: 0`, with a plausible command/stdout pair typed in, and drops the specimen — assertion (i) is scoped to MEASURED rows so the row exits the equality entirely, assertion (ii)'s per-row shape check is satisfied by construction because the builder wrote exactly the shape it demands, nothing re-derives the count because nothing can, and the floor whose declared purpose is "a class measured at zero is a row the conductor writes, not a row that may be omitted" is defeated by precisely the means it exists to prevent, every assertion green. AC-5(c) is the worse half of the same hole and is why the leg is asserted there too: a builder wanting a convenient `NAME_POOL` token that happens to collide with a real name in a vault it cannot see adds a pool-table row with a fabricated non-occurrence scan, and `## Intent`'s one sentence about Dave's contacts' real names has no machine check behind it at all. This criterion's own AC-1(a) already states the remedy applied to the wrong artifact — "frozen without a mechanism is a wish" — and the fix is that identical `sha256`-over-bytes move, with the one difference that decides whether it works: the expected value lives in the SIGNED CRITERION rather than in a module the build owns, because a digest constant a builder can edit in the same commit as the file it digests is not a wall. Absent this leg the census's trustworthiness rests on a human noticing an unexpected diff to a shared doc during code review — which is exactly the "reviewable by eye" control AC-5's own `why:` argues is not good enough for this item's privacy property. ONE RECURRING COST IS NAMED HERE RATHER THAN DISCOVERED BY WHOEVER PAYS IT: because the branch half of the floor is derived, a new Tier-1 branch added to either table reddens this criterion immediately, and discharging it needs a census row carrying a count, a scan command and verbatim stdout — all of which need the live vault, which no caged builder can read — so a routine package change (WI-022 just added a whole company table) is blocked on a conductor pass, and under (iv) that pass now also re-freezes the digest. That is LESSONS #45's intended friction and it is not weakened here; it is written down because round 4 weakened AC-5(c) to a containment specifically to remove paired edits across the cage boundary, and the derived floor reintroduces one in the other direction, so the next branch author should be told rather than surprised.
check: test_every_census_corruption_class_has_a_specimen_with_a_verdict
kind: test
```

```criteria
id: AC-4
desc: Loading the materialized corpus through the repositories produces exactly the declared skip surface, asserted PER REPOSITORY. THE DOMAIN OF EVERY EQUALITY IN THIS CRITERION IS ONE REPOSITORY, NEVER A UNION ACROSS THEM — the manifest declares `{repository_type: {path: reason}}`, keyed by each repository's own `type_name` (`repositories/base.py:191`). THE SET OF REPOSITORIES IS DERIVED, NOT LISTED: the sweep takes the concrete `BaseRepository` subclasses the package exports (`obsidian_schemas/repositories/__init__.py`'s `__all__`, `:14-21` — the imports end at `:12`, and an earlier draft's `:8-20` cite spanned both and matched neither; excluding `BaseRepository` itself) and asserts the manifest declares a mapping for exactly that set, keyed by `type_name` — the same runtime read of an exported declaration AC-2 makes against `TYPE_TO_MODEL` and AC-3 against the Tier-1 tables' `branch_id`, applied here because a hand-written "the four repositories are person, company, meeting, book" is the same transcription that let AC-3's floor sample its own branch table, and a fifth repository added later would otherwise join the corpus's blind spot silently instead of failing until it has declared skips and a declared loadable count. WHICH READ IS MEANT IS PINNED, BECAUSE THE TWO AVAILABLE ONES ARE NOT EQUIVALENT: the sweep iterates the names `obsidian_schemas/repositories/__init__.py` EXPORTS (`__all__`, `:14-21`) and keeps those that are concrete `BaseRepository` subclasses — deterministic, and a fixed list the package authors — never `BaseRepository.__subclasses__()`, whose answer depends on which modules happen to have been imported. THAT EXPORT LIST IS FILTERED, NEVER ITERATED WHOLE, because it is not homogeneous: `__all__` also carries `VaultPathNotConfiguredError` (`:16`), an EXCEPTION rather than a repository, which the concrete-`BaseRepository`-subclass filter drops — the filter as stated already handles it, and saying so here is what saves the build a round spent discovering that a six-name export list does not mean six repositories. And one implementability detail is settled here rather than at build time: `type_name` is an abstract `@property` (`base.py:189-193`), readable off an INSTANCE and not off the class, so each repository must be instantiated against the materialized vault before the manifest's key set can be compared — which legs (a) and (c) do anyway, so this is ordering rather than a gap. Four today — `person`, `company`, `meeting`, `book` — and the derived set is asserted NON-EMPTY and of exactly that size (LESSONS #46, for the same reason AC-2's and AC-3's derivations are: a read that silently resolves to nothing is green, and the size at the moment of writing is the cheapest form of having seen it red). The other four `TYPE_TO_MODEL` members have no repository at all, so they are AC-2's parser-level business alone — and that asymmetry FOLLOWS from the two derivations rather than being separately checked, which is what an earlier draft claimed. Saying it was "itself checked" described an assertion of the form `A - B == A - B`: with both sides derived and no expected value declared, it passes for any package and asserts nothing. It costs nothing to drop, because a fifth repository is already caught by the derived sweep proper — which demands a declared mapping and a declared loadable count for it — and keeping it would have made this criterion its own counterexample to the governing rule it states three sentences later. WHAT IS DERIVED IS THE POPULATION AND NEVER THE ORACLE, AND THE LINE MATTERS: which repositories exist is a fact the package declares and must be read from it, while WHAT each one is expected to own — the globs and the ownership outcomes spelled out below — is the hand-written expected value a wrong-but-self-consistent implementation must MISMATCH (WI-286), so reading those from the code under test would turn this criterion into a mirror of it. THE SKIP-REASON CODOMAIN IS MADE READABLE BY THIS ITEM AND IS THEN READ, BECAUSE TODAY THERE IS NOTHING TO READ AND AN EARLIER DRAFT OF THIS CRITERION CLAIMED OTHERWISE: `_skip_reason` (`repositories/base.py:41-47`) returns three BARE STRING LITERALS — `:44`, `:46`, `:47` — with a type comment on `SkippedNote.reason` at `:37`, and the package exports no frozenset, tuple, dict or enum of them anywhere, so unlike `TYPE_TO_MODEL` (a dict AC-2 reads), the `branch_id` union (two exported tuples AC-3 reads) and this criterion's own repository set (`__all__`), there is no declaration here at all and the only thing anyone has ever been able to do with this codomain is hand-transcribe it, which THREE hand-typed sites do today (P20, corrected — the enumeration was short by two until a grep for the three literals over every `*.py` in this worktree was actually run, and §4's disposition table now carries all of them with a ruling each): `tests/test_loud_fail_load.py:187-188` transcribes the WHOLE codomain, `tests/test_loud_fail_load.py:209` re-spells `unreadable` twenty-two lines below it inside the same function, and `tests/test_name_gate.py:152` re-spells `unreadable` in a module that was not previously a write target. All three are closed by Task 11 and `tests/test_name_gate.py` gains a `## Write Targets` fence for the third. Two sites are deliberately NOT closed and are kept unchanged, because neither is a transcription of the vocabulary: the `#` type comment on `SkippedNote.reason` (`base.py:37`), which documents the declaration two lines beneath it, and the running-prose docstring sentence at `errors.py:112`. SO THE FIX IS TO CREATE THE DECLARATION RATHER THAN TO KEEP TRANSCRIBING IT, AND IT IS ONE LINE OF PACKAGE CHANGE INSIDE THIS ITEM'S BUILD: `repositories/base.py` gains a module-level `SKIP_REASONS` frozenset whose members `_skip_reason` returns BY NAME rather than as re-spelled literals (`obsidian_schemas/**` is in this project's `write_authority`, P7), and this criterion reads it at test time exactly as AC-2 reads `TYPE_TO_MODEL`. AN EXPORT ON ITS OWN WOULD BE DECORATION — NOTHING WOULD MAKE A FOURTH ARM UPDATE IT — SO IT IS TIED TO THE FUNCTION BY A SYNTAX DERIVATION IN THE ONE PLACE THIS TREE PERMITS ONE: `tests/derivations.py`, the standing shared scan module and the only file under `obsidian_schemas/` or `tests/` allowed to name `ast` (P9), gains ONE scan returning the set of string values `_skip_reason`'s own body can return — every `Return` whose value is a `str` Constant, plus every `Return` of a module-level Name bound in that file to a `str` Constant — and the criterion asserts that set EQUALS `SKIP_REASONS`. THE EQUALITY DIRECTION IS WHAT MAKES THAT WALL HOLD RATHER THAN MERELY EXIST, and it has three consequences worth stating so a builder does not weaken it to a containment: an arm added to `_skip_reason` without a matching frozenset member is RED at that equality; an arm whose return the scan CANNOT resolve to a literal makes the scan silently UNDER-read, which the equality reports RED instead of passing green (LESSONS #46 — the failure mode of every derived read in this document); and `SKIP_REASONS` is additionally asserted NON-EMPTY and of size exactly 3 at the moment of writing, which is the POPULATION's size and never an oracle, since what each specimen must produce stays hand-declared in the manifest. AND THE CLASS IS CLOSED WITH ONE RULE RATHER THAN THREE REPOINTED LINES, BECAUSE AN ENUMERATION IN PROSE GOES STALE AND A WALL DOES NOT: a SECOND syntax scan in `tests/derivations.py`, `skip_reason_literal_sites`, returns every file under `python_files_under(PACKAGE_ROOT, TESTS_ROOT)` containing a `str` Constant EQUAL to a member of `SKIP_REASONS`, and this criterion asserts that set EQUALS exactly two named homes — `obsidian_schemas/repositories/base.py`, THE DECLARATION, and `tests/test_fixture_vault.py`, THE SPELLING PIN — so a fifth hand-typed site anywhere under the package or the suite is RED with the file named and its remedy is one import. It reads parsed SYNTAX and never source text for a reason the two KEPT sites make concrete: `ast` drops `#` comments entirely, so `base.py:37`'s type comment is invisible to it, and a docstring is ONE Constant whose value is the whole docstring, so `errors.py:112`'s prose mention is not equal to any member — a text grep would have to carve an exception for both, and an exception is the escape hatch this criterion has been folded for twice. The SECOND home is not a weakening but the repair of one the fold would otherwise have caused, and it is stated so nobody removes it as untidy: `tests/test_loud_fail_load.py:187-188` is today the ONLY thing in the tree pinning the literal SPELLINGS, and once it reads `SKIP_REASONS` both sides of that comparison move together, so a rename of `"schema-drift"` — a value consumers read off `SkippedNote.reason` — would pass every check in this criterion; the spellings are therefore hand-pinned ONCE, as `SKIP_REASONS == {"malformed-frontmatter", "schema-drift", "unreadable"}` in `tests/test_fixture_vault.py`, which is the one place a rename should have to be a deliberate edit. Because that universe grows with every file this item adds, `tests/fixture_vault.py` is a member of it, which is why the manifest IMPORTS the three constants for `SKIPS`'s reason values rather than re-spelling them (§3) — and WHICH constant a filename maps to remains the hand-declared oracle, so nothing about leg (a)'s both-directions equality is read from the code under test. ON TOP OF THAT DECLARATION the criterion asserts that the corpus carries at least one specimen for each member and that the UNION over the four declared per-repository mappings' reasons is EQUAL to `SKIP_REASONS` — so a corpus missing a reason is RED, and a fourth reason added to the package later genuinely does fail until it has a specimen, which is now a property this criterion HAS rather than one it merely stated. THE DOUBLE-OWNERSHIP OF THE TWO UNTYPED CLASSES IS DECLARED EXPECTED BEHAVIOUR, NOT A BUILD-TIME SURPRISE: ownership is decided by `_note_skip` on the error's `declared_type` (`base.py:267-275`), and `FrontmatterParseError` carries `declared_type=None` always (`errors.py:65-67`) while a `UnicodeDecodeError` carries the attribute not at all, so both fall to `_owns(None)`, which returns `Path(self.file_pattern).stem != "*"` (`base.py:258-265`) — TRUE for person and company (both inherit `@*.md`, `base.py:196-198`) and for meeting (`Meeting *.md`, `meeting.py:51-54`), FALSE for book (`*.md`, the catch-all, `book.py:50-53`). Combined with the flat directory's glob partition, the manifest therefore declares, and the test asserts: a malformed-frontmatter or unreadable specimen FILENAMED `@<name>.md` appears in BOTH person's and company's mappings and in NEITHER meeting's (its glob does not match) nor book's (its glob matches but its catch-all stem declines ownership); the same specimen filenamed `Meeting <date> - <title>.md` appears in meeting's mapping ONLY; and a `schema-drift` specimen, which does carry a `declared_type` (`errors.py:70-71`), appears ONLY in the mapping of the repository whose `type_name` equals it. Three legs. (a) SKIPPED — for EACH of the four repositories independently, the mapping `{note.path: note.reason for note in repo.skipped_notes}` after loading the materialized vault EQUALS that repository's declared mapping, both directions: a malformed specimen that silently loads anyway is RED, a well-formed note a repository wrongly skips is RED, and an untyped skip that moves between owners is RED in two mappings at once. (b) THE PLANTED DISCRIMINATORS — the corpus contains an untyped specimen under EACH of the two owning globs (one `@<name>.md`, one `Meeting <date> - <title>.md`), and book's declared mapping over the untyped classes is asserted EMPTY: without the second filename a stub that records untyped skips in one repository only is indistinguishable from the real rule, and without book's empty assertion the catch-all arm of `_owns` is never exercised by anything. (c) LOADED — `len(repo.get_all())` for each of the four repositories equals that repository's declared loadable count, and the resolvable identities declared in the manifest all resolve, so a corpus whose malformed members poison the surrounding load is RED rather than merely under-reported.
why: WI-020 built `SkippedNote` because an unloadable note used to vanish at DEBUG — invisible to the cache, so `resolve()` missed it and `find_or_create_stub` minted a duplicate, the dup-proliferation class WI-119/WI-125 exist to fight (`base.py:29-34`). That surface has never had a vault on disk containing one of each and stating which is which, so nothing today would notice a regression that reclassified `schema-drift` as `unreadable` or that swallowed a malformed note without recording it. Set equality in both directions is what makes leg (a) an oracle rather than a membership check: `skipped_count >= 3` is passed by a repository that skips everything, and `skipped_count == 3` is passed by one that skips the three WRONG notes. But a both-directions equality with an UNSTATED DOMAIN is not an oracle either, and that was this criterion's real gap: a union over all repositories and a per-repository mapping are two different declared manifests, each passes its own reading, and only the per-repository one goes RED when a regression moves an untyped skip between owners — which is the exact regression this surface exists to catch, because ownership is what decides whether a bad note is VISIBLE to the repository that would otherwise mint a duplicate for it. Declaring the double-ownership rather than discovering it is the WI-144 economy: a build that meets it as a surprise reads two repositories reporting "the same" note, concludes the test is wrong, and quietly relaxes the equality to a union — losing the property. Leg (b) is WI-286's planting rule applied to this criterion's own discriminant: the corpus, not the code, has to supply the case that tells the per-repository rule apart from every cheaper approximation of it, and book's empty mapping is the only assertion in the suite that the catch-all glob DECLINES ownership by design. Leg (c) exists because the failure that actually costs data is not the skip, it is the blast radius — a parse failure that aborts the directory walk leaves the cache silently short, and the only way to see it is to declare beforehand how many notes SHOULD have loaded. DERIVING THE REPOSITORY SET RATHER THAN LISTING IT WAS ADDED IN THE SAME PASS THAT DERIVED AC-3's CLASS FLOOR, AND FOR THE SAME REASON RATHER THAN FOR SYMMETRY: this criterion's whole subject is that a note's VISIBILITY is a per-repository fact, so the one thing that must not be hand-maintained is which repositories there are — a fifth one added to the package would inherit `_owns`, take part in the same glob partition over the same flat directory, and be entirely absent from a hand-listed sweep, which is the exact silent under-coverage AC-3's floor was found doing over the branch table. It is also the cheapest possible version of the fix: the subclasses are already exported and `type_name` is already the key the manifest uses. The oracle stays hand-written on purpose and the criterion says so, because the failure this leg exists to catch is a regression in ownership, and an expected value read from the code that computes it agrees with the regression. THE SKIP-REASON CODOMAIN WAS THE SEVENTH INSTANCE OF THIS DOCUMENT'S ONE RECURRING DEFECT, AND IT IS THE FIRST THAT COULD NOT BE FIXED BY READING SOMETHING — WHICH IS WHY THE FIX CREATES A DECLARATION INSTEAD. Two independent round-9 reads — the architect's and the AC red-team's, from a duplication angle and from a satisfiable-with-nothing-real-behind-it angle — found the same fact: this criterion put `_skip_reason`'s reasons on the DERIVED side of the document's residue list and stated a consequence ("a fourth reason added to the package later fails until it has a specimen") that only a derivation delivers, while the package declares no set to read. Both sides of the equality were hand-typed, so a builder who added a fourth arm — a `PermissionError` distinguished as `unreadable-permission`, say; WI-020's own `base.py:29-34` already distinguishes skip incidents by cause — would ship a GREEN criterion with the new failure class in exactly the blind spot `SkippedNote` was built to close, one layer up from where WI-020 closed it. That is a green-over-wrong route rather than a loud one, which is what separates it from round 8's two instances and makes it worth a package change. THE ALTERNATIVE WAS OFFERED AND IS REJECTED FOR A STATED REASON: the honest cheap move was to keep the set hand-written, delete the false consequence and move it into the residue list beside this criterion's ownership oracle. It is rejected because the residue list's own membership test is "there is no declaration to read", and the other four members earn that by their SUBJECT — whether a field's value IS a name, what a shape class should be called, what a repository OUGHT to own — all judgment. Which strings `_skip_reason` can emit is not judgment, it is mechanical, and this is the determinism boundary the whole document is organised around: a mechanical fact carried by a transcription is a defect wherever it appears, and the remedy for the one classification vocabulary that never got the module-level-literal treatment the package gives `TYPE_TO_MODEL`, `TIER1_BRANCHES`, `ENTITY_BODY_CONFIG` and `_GENERIC_ORG_SUFFIXES` is to give it that treatment. It is solve-in-one-place besides, and the enumeration behind that argument is now the grep's rather than memory's: the three strings live in a return chain (`base.py:44`, `:46`, `:47`), a `#` type comment (`:37`), a running-prose docstring sentence (`errors.py:112`) and THREE hand-typed test sites — `tests/test_loud_fail_load.py:187-188` (the whole codomain), `tests/test_loud_fail_load.py:209` and `tests/test_name_gate.py:152` (one member each) — and the criterion would have added a seventh. An earlier draft of this sentence named only the first, the second and one of the three test sites; the short list mattered because it was the ARGUMENT, and because it left the builder a judgment the spec had not made — repointing `:187-188` puts `:209` on the same screen with nothing saying whether it is in scope. §4 now carries a disposition table naming every site with a ruling, Task 11 closes all three test sites, and the two kept sites are kept for a stated reason rather than by omission. AND THE EXPORT IS DELIBERATELY NOT TRUSTED ON ITS OWN, WHICH IS THE PART TO KEEP IF THIS CRITERION IS EDITED AGAIN. `TYPE_TO_MODEL` cannot silently fall out of step with the package because dispatch depends on it; a `SKIP_REASONS` frozenset nothing consumes CAN, and a criterion that read it and stopped there would have re-created the same false consequence in a nicer-looking form — the fold breeding its own next finding, which this document has recorded three times. Binding it to `_skip_reason`'s own returns by a syntax scan in `tests/derivations.py` is what closes that, it needs no new machinery (the module exists, is importable, and single-homes `ast` by a standing wall), and asserting EQUALITY rather than containment is what makes the scan's own under-read — the LESSONS #46 failure every derived read in this document shares — report RED instead of green.
check: test_the_skip_surface_over_the_corpus_equals_its_declared_reasons
kind: test
```

```criteria
id: AC-5
desc: No corpus note can carry a live identifier — an email, a phone number, a profile URL OR A NAME — asserted structurally rather than by inspection. THE REACH OF EVERY LEG IS every file under `tests/fixtures/vault/` PLUS `tests/fixture_vault.py` itself, because the manifest restates each specimen's field values as AC-2's declared oracle and a wall that scanned only the corpus would miss a real name typed into the oracle. Five legs. (a) RESERVED RANGES, derived not hand-listed — the test scans those bytes for every email-shaped, phone-shaped and profile-URL-shaped token and asserts each one is inside a reserved range: emails only under RFC 2606 / RFC 6761 reserved names (`example.com`, `example.net`, `example.org`, or a `.test` / `.invalid` / `.example` TLD); phones only inside reserved fictional ranges (UK `+44 7700 900xxx` — the Ofcom drama block, IN EITHER OF ITS TWO SPELLINGS, the international `447700900xxx` and the national `07700900xxx`, which are ONE range and not two, because `normalize_phone` strips the `+` and keeps the leading `0`; NANP `555-01xx`); profile URLs only under a declared placeholder form. The scan is over ALL bytes in reach rather than a field list, so it needs no enumeration to be total — but the fields that carry these shapes are named for the corpus author's benefit, since every one of them must be constructed: `Person.emails` (`models.py:81`), `Person.phones` (`:82`), `Person.whatsapp` (`:83`, a JID whose digits `normalize_phone` splits at the `@` — `phone_normalization.py:39-55`), `Person.linkedin` (`:86`), `Person.slack` (`:87`), `Company.website` (`:129`), `Company.linkedin` (`:131`), `Book.isbn` (`:165`), `Book.source_url` (`:168`) and `Explore.url` (`:223`). AND THE MANIFEST'S OWN DECLARED HEX LITERALS ARE EXCISED FROM THE TEXT BEFORE THE SPAN WALK, DECIDED HERE FOR THE SAME REASON §6.4 DECIDES THE ISBN AND IN THE SAME BREATH, BECAUSE WITHOUT IT THIS LEG IS RED BY CONSTRUCTION OVER A WHOLLY CORRECT CORPUS. The reach includes `tests/fixture_vault.py`, which BY §3's OWN DESIGN carries `CORPUS_DIGEST` (64 lowercase hex) and, for the single non-UTF-8 member, `NoteSpec.raw_bytes_hex` — that note's COMPLETE bytes in lowercase hex, which leg (b) requires to be declared there and asserted byte-equal — and printable ASCII hex-encodes to bytes whose FIRST NIBBLE IS `2`–`7`, always a digit, so a nine-digit run inside such a literal is STRUCTURAL rather than unlucky: the five bytes of `type:` encode to `747970653a`, whose first nine characters are the phone-shaped run `747970653`, and `normalize_phone("747970653")` matches neither reserved pattern. A 64-character sha256 hex literal is a smaller instance of the same class — it carries a ≥9-digit run often enough that a merely RE-TAKEN digest could redden the leg on nothing but a legitimate corpus edit. THE EXCISED SET IS THEREFORE EXACTLY THE MANIFEST'S DECLARED HEX LITERALS, BY NAME AND NEVER BY SHAPE: `CORPUS_DIGEST`, every non-`None` `NoteSpec.raw_bytes_hex`, and the optional restatement of AC-3(iv)'s `CENSUS_DIGEST` that AC-3(iv) permits `fixture_vault.py` to carry for readability — and nothing else. Each is asserted FIRST to be well-formed lowercase hex of even length (`CORPUS_DIGEST` exactly 64 characters, a restated `CENSUS_DIGEST` exactly 64). AND THE PRESENCE ASSERTION'S DOMAIN IS THE REACH, NEVER THE INDIVIDUAL FILE, WHICH IS STATED HERE BECAUSE THE TWO READINGS DIFFER BY ~50 REDs OVER A WHOLLY CORRECT CORPUS: each declared literal is asserted to OCCUR SOMEWHERE IN THE REACH — the union of the bytes of every file this leg scans, tested ONCE against that union — while the EXCISION is applied to EVERY file's text independently, whether or not that file contains the literal, an excision of an absent substring being a no-op that costs nothing. The per-file reading is the harmful one and is excluded by name: `CORPUS_DIGEST` and every `NoteSpec.raw_bytes_hex` live in `tests/fixture_vault.py` BY §3's OWN DESIGN and appear in no corpus note at all, so a per-file presence assertion would hold for exactly one of the ~51 files in reach and be RED on the other ~50, on a corpus with nothing wrong with it — the same criterion-versus-code fork the word "corpus-relative" closed in AC-1(a), with the same absence of any in-cage remedy once these criteria are signed (the builder facing it could only narrow a signed criterion or delete the assertion). The union domain is what the anti-hiding-place argument actually wants and loses nothing: an exemption declared for a literal that occurs NOWHERE in reach is still RED rather than free, so the exemption still cannot become a hiding place. The three surfaces that restate this — `## Design` §6.4, Task 8, and `## Edge Cases`'s "A declared hex literal read as a phone" — say the same thing in the same words. It is an author-declared, named exemption asserted by equality exactly as `RESERVED_ISBN` is, so it can no more be padded than that one can: any other ≥9-digit run anywhere in reach is still scored as a phone and still RED. The excision is scoped to THIS leg's shape scan alone — leg (b)'s token scan is unaffected (a lowercase hex literal yields no extracted token, which is why leg (b) already requires that casing) and leg (e)'s absolute-path scan is unaffected. (b) NAME CLOSURE, SPLIT BY POSITION AND BY TOKEN KIND — THE SPLIT IS THE WALL. `fixture_vault.py` declares THREE literal frozensets and no computed membership: `NAME_POOL` (the constructed given names, surnames and company words the specimens are built from), `CONNECTIVE_SET` (the corruption classes' own non-identifying furniture, FIXED BY ENUMERATION AT EXACTLY `{"Me", "My", "Dave"}` — the package's OWN calendar/arrow/transcript prefix vocabulary, whose union across the three prefix regexes that spell a capitalized alternative is exactly that set: `name_cleaning.py:46` `_CALENDAR_PREFIX_RE` matches `^(Dave|Me|My)\s*[-/]\s+` and `:54` `_ARROW_PREFIX_RE` matches `^(Dave|Me|My)\s*[→⟶⇒➜↦⇨]\s*`, while `:55` `_ME_TO_PREFIX_RE` matches `^(Me|My)\s+to\s+` and carries NO `Dave` alternative — an earlier draft of this criterion said all three matched `(Dave|Me|My)`, which is wrong about `:55` and right about the union, and the union is what the set is; the test asserts that equality against the literal set written into this criterion, so the set cannot grow without an AC change and is never a build-time choice; the lowercase and punctuation connectives the classes also need, `to`, `->` and `→`, are NOT members, because the stated extractor cannot produce them and a member the closure can never exercise is a declaration that lies, and the mail-header prefixes `Re`, `Fwd` and `Fw` are NOT members for the harder version of the same reason — a Grep over the whole tree finds them in no Tier-1 branch, no recovery regex and no candidate census class, so no census row could ever measure one and no corpus specimen could ever honestly carry one, P11; AND THE SET IS ENUMERATED FROM THE WHOLE FURNITURE SURFACE RATHER THAN SAMPLED FROM THREE REGEXES OF ONE FILE — that surface is SIXTEEN regexes in two files and there is no third — the eleven of `name_validation.py` (`:66`, `:74`, `:82`, `:101`, `:107`, `:110`, `:113`, `:120`, `:123`, `:351`, `:445`) and the five prefix/suffix regexes of `name_cleaning.py` (`:46`, `:54`, `:55`, `:56`, `:57`) — plus both Tier-1 tables, the ten person branches (`name_validation.py:190-309`) and the five company ones (`:371-438`), with P16 recording the complete pass and P17 recording that no regex anywhere else in the package carries furniture. APPLYING THE RUN RULE THIS CRITERION PINS DOWN BELOW TO THE LITERAL SPELLING EACH REGEX CARRIES, THE UNION OF EXTRACTED FURNITURE TOKENS IS EXACTLY `{Me, My, Dave}` AND NO MEMBER IS ADDED — the two branches the earlier sampling omitted are the reason the rule had to be pinned first, and neither adds one. `archive_prefix` (`name_validation.py:110`, `^z+Archived\b`; recovery arm `name_cleaning.py:56`, `^z+Archived\s*-\s*`) contributes NOTHING, because `zArchived`/`zzArchived` is one run beginning lowercase and the run rule yields no token from it; that is not a reading chosen for convenience, since all five real specimens this repository commits for the branch spell it exactly that way with no exception (P15), so `Archived` is NOT a member and putting it in would plant an unexercisable literal in a frozen set — round 4's defect authored by a fold instead of by a builder. `unknown_contact` (`name_validation.py:113`, `unknown\s+contact` under `re.IGNORECASE`; recovery arm `name_cleaning.py:57`, `\s+unknown\s+contact\b`) contributes nothing FROM THE CODE either, both regexes spelling the literal lowercase — but it is the one branch whose answer THIS REPOSITORY'S COMMITTED SPECIMENS leave open, because `IGNORECASE` hands the letter-case to the live vault and this repository commits BOTH forms: the lowercase suffix form the branch's own "WhatsApp scanner artifact" comment describes (`tests/test_name_validation.py:248`, `:254`; `tests/test_name_cleaning.py:135`, `:140`) and a capitalized standalone form (`tests/test_name_gate.py:96`; `tests/test_lint_vault_fix_gate.py:58`; and the branch's own display `specimen=` field at `name_validation.py:274`). THE FLAG ITSELF IS NOT WHAT MAKES THAT CELL SPECIAL, AND SAYING SO KEEPS THIS SENTENCE HONEST: `re.IGNORECASE` is carried by EIGHT of the sixteen regexes (P17 — all five of `name_cleaning.py`'s and `name_validation.py`'s `:82`, `:110`, `:113`; `:74` does not carry it), so the code pins the live casing of `Me`/`My`/`Dave` no more tightly than `unknown contact`'s. What separates them is the CORPUS: every committed specimen of the three prefix branches spells them canonically with no `ME`/`DAVE` variant anywhere in the tree (P16), while `unknown_contact` is committed both ways. The reconciliation instruction below is written general for exactly that reason and needs no widening — if the census measures a live `ME - X` form, it is absorbed at the same one-time edit. THAT ONE RESIDUAL DEGREE OF FREEDOM IS CLOSED BY RECONCILIATION RATHER THAN BY A GUESS: `CONNECTIVE_SET` therefore carries the SAME ONE-TIME PRE-ORIGINATION RECONCILIATION INSTRUCTION AC-3's CLASS FLOOR CARRIES FOR ITS HAND-LISTED HALF (the branch half of that floor needs none, being read from the package at test time; this set needs one for the same reason those six shape classes do — the regexes declare patterns, not token lists, so there is no declaration to read) — before Dave signs, this literal set is reconciled ONCE against the census's measured character profiles, so that if the census measures the live `unknown_contact` form as capitalized then `Unknown` and `Contact` are added HERE, in this criterion, and if it measures the lowercase suffix form they are not; the same reconciliation runs for any other furniture class whose measured profile would put a capitalized non-name run into an identity position. AFTER THAT ONE EDIT THE SET IS FROZEN EXACTLY AS IT IS NOW — asserted equal to the literal written in this criterion, unable to grow without an AC change — so the safety property is untouched, and the instruction adds NO obligation over members the builder does not author, because the set still carries no non-vacuity clause of any kind. THE CHEAPER ALTERNATIVE IS NAMED AND REJECTED so a builder does not reach for it: authoring the specimen in the lowercase form whatever the census measured would hold the set at three members for free, but it destroys the character profile the specimen exists to carry, which is the same argument that keeps the "lowercase it for green" dodge out of AC-2's declared oracle and AC-3's declared verdict), and `PROSE_ALLOWLIST` (the ordinary English of the note bodies plus this module's own identifiers, docstring and comment vocabulary). THE EXTRACTOR IS STATED ONCE AND ITS "RUN" IS PINNED TO ONE READING, BECAUSE TWO READINGS OF IT RETURN DIFFERENT ANSWERS ON THE SAME BYTES AND THE DIFFERENCE DECIDES A FROZEN SET'S OWN MEMBERSHIP: decode every byte in reach with `errors="replace"`; a RUN is a MAXIMAL contiguous span of characters drawn from the class {Unicode letters, combining marks, `'`, `-`} — maximal meaning the span is bounded only by a character OUTSIDE that class (whitespace, a digit, any other punctuation, or the end of input) and NEVER restarted at an internal capital, so there is no camelCase splitting; a run is EXTRACTED as a token iff its FIRST character is an uppercase or non-ASCII letter; and an extracted run has leading and trailing `'` and `-` trimmed before it is compared against any set. FOUR WORKED CONSEQUENCES, WRITTEN OUT SO THE RULE IS CHECKABLE RATHER THAN INTERPRETABLE: `McDonald` is ONE token `McDonald`, never `Mc` plus `Donald`; `d'Angelo` is ONE run beginning with the lowercase `d` and therefore yields NO token (the extractor-domain residue already named in `why:`, not a new hole); `Zeta-9` yields `Zeta` (the run is `Zeta-`, trimmed); and — the consequence that settles `CONNECTIVE_SET`'s membership above — `zArchived` and `zzArchived` are each ONE run beginning with the lowercase `z` and yield NO TOKEN AT ALL. The maximal reading is chosen over the capital-restarting one for two stated reasons rather than by default: it is the reading that every real specimen this repository has ever committed for the `archive_prefix` branch is consistent with, all five of them spelling the prefix with nothing between the `z` and the capital (P15), and it is the reading that gives an ordinary hyphenated or Mc-prefixed surname the one answer a name needs. It is applied to two DISJOINT POSITION SETS with different rules. ONE ADMISSION IS DERIVED FROM THE PACKAGE RATHER THAN DECLARED HERE: an identity-position token whose `str.lower()` is a member of `name_cleaning._GENERIC_ORG_SUFFIXES` (`name_cleaning.py:58` — exactly `support`, `ltd`, `inc`, `corp`, `group`, `team`, `limited`, `llc`) is admissible with no `NAME_POOL` membership and no census row. THE COMPARISON OPERATION IS NAMED RATHER THAN DESCRIBED: the test lowercases with `str.lower()`, which is what the package itself does at `:148`, `:185` and `:191` — an earlier draft said "casefolded", which the package nowhere does; the eight members are ASCII so `lower` and `casefold` agree on them, but the corpus deliberately carries non-ASCII specimens and the criterion should name the operation its own test performs. It is READ from the package rather than written into `fixture_vault.py` precisely so a builder looking for the cheapest green cannot pad it, and it exists because the identity-position list below now reaches `Person.company` and `Book.publisher`: a specimen written `Voxleaf Ltd` would otherwise oblige the conductor to certify that `Ltd` occurs zero times in a vault of 2,159 company notes, which is not a claim anyone can honestly make, and none of the eight members can hide a person. **IDENTITY POSITIONS — ENUMERATED FIELD BY FIELD AGAINST `models.py`, NEVER NAMED BY CATEGORY, AND THE ENUMERATION IS ITS OWN RULE'S OUTPUT.** The rule is stated in THREE CLAUSES so a ninth entity type or a new field is CLASSIFIED rather than missed — and stated in three rather than one because a single "iff its value names a PERSON or an ORGANISATION" did not generate the list written under it in either direction, which is a criterion that is buildable two ways by its own reconciliation instruction. **CLAUSE 1 — NAMING.** A declared field is an identity position iff its VALUE IS a person's or an organisation's name: the whole scalar, or each element of the list, being such a name or a wikilink to a note that holds one. It is deliberately "IS a name", not "COULD CONTAIN one": the second reading sweeps every free-text field into the pool and obliges the conductor to certify ordinary English words with zero-hit live-vault rows, which is finding 1's unsatisfiable-obligation shape rebuilt on purpose. **CLAUSE 2 — DECLARED OVER-CONSTRAINT, so reconciliation does not delete it.** Plus the four entity `title` fields — `Book.title` (`:160`), `Watch.title` (`:193`), `Explore.title` (`:222`), `Exploration.title` (`:295`). A book, a film, a link and a living document are not people or organisations, so clause 1 does NOT reach them; they are in the list ON PURPOSE and this clause is the authority a later reconciliation reads before removing them. The reason: a title is the human-written display string of a note whose live original the corpus author is copying a character profile from, so transcribing a real one is the same slip as transcribing a real name, and it costs nothing extra — `## Write Targets` already requires every identity-position token in a specimen to be a constructed string, naming "a naturally-worded meeting title" as the example. **CLAUSE 3 — UNDECLARED KEYS, BY DEFAULT AND WITH NO OPT-OUT.** `BaseEntity` sets `model_config = ConfigDict(extra="allow", ...)` (`models.py:31-32`), so a corpus note may carry frontmatter keys no model declares — a `manager:` or `introduced_by:` on a forward-compatibility or schema-drift specimen — and clauses 1 and 2, being enumerations over DECLARED fields, cannot reach them at all. Any manifest-declared value for a key the note's model class does not declare is therefore an IDENTITY POSITION, full stop: there is no manifest flag that marks one prose, because a builder-settable exemption is the escape hatch this criterion has now been folded for twice. The default is satisfiable by construction rather than being an obligation over a set nobody authors — the corpus author chooses both which undeclared keys exist and what they hold, and the only cost of the default is that those values must be short constructed tokens rather than sentences. **THE CURRENT ANSWER**, reconciled field by field against every member of `TYPE_TO_MODEL` (the full pass is P14): every corpus filename stem (with the declared filename grammar's `@` sigil and `Meeting <date> - ` prefix stripped), plus the manifest's declared values for `Person.name` (`models.py:79`), `Person.aliases` (`:80`), `Person.company` (`:84`), `Company.name` (`:128`), `Book.title` (`:160`), `Book.author` (`:161`), `Book.publisher` (`:166`), `Watch.title` (`:193`), `Watch.director` (`:195`), `Watch.streaming_service` (`:199`), `Watch.recommended_by` (`:200`), `Explore.title` (`:222`), `Explore.source` (`:224` — "where you found it / who mentioned it"), `GiftIdea.for_person` (`:242`, frontmatter alias `for`), `GiftIdea.source` (`:243`), `Meeting.attendees` (`:261`), `Exploration.title` (`:295`) and `Exploration.related` (`:299`), plus every undeclared key's declared value under clause 3. **FOUR EXCLUSIONS, EACH ARGUED, AND ONE CORRECTION.** `Person.title` (`:85`) is EXCLUDED: it is a JOB title, it names nobody, and forcing `Director` into a pool that owes a zero-hit live-vault row would manufacture an unsatisfiable obligation on purpose — `Person.company` (`:84`) and `Person.title` (`:85`) are different fields and only the first carries identity. `Meeting.topics` (`:262`) is EXCLUDED as free prose for the same reason. `Exploration.origin` (`:300`, glossed "What sparked this - problem, article, conversation" at `:281`) is EXCLUDED on the same argument and it is the closest call in the list: it is a SENTENCE rather than a name, so clause 1 does not reach it and clause 1's "could contain" reading is the one that breaks the criterion — the residue is stated plainly below rather than closed by a fifth clause. `Exploration.graduated_to` (`:301`, glossed `[[Project]]` at `:282`) is EXCLUDED: a project is neither a person nor an organisation, and a constructed project name like `Q3 Migration` would put ordinary words into a pool owing zero-hit rows — finding 1's shape again. And `Meeting` DECLARES NO `title` FIELD AT ALL (`:259-263` — `date`, `attendees`, `topics`, `meeting_id`; `BaseEntity` adds only `type` and `tags`, `:39-40`), so the phrase this list replaced named a field the schema does not have; a meeting's title is not lost, because it lives only in the filename and the stem scan already reaches it. The list is reconciled against the schema BY APPLYING ALL THREE CLAUSES, BEFORE origination, exactly as AC-3's CLASS FLOOR reconciles its hand-listed half, so a field added to a model costs one edit here rather than a re-sign. IT IS HAND-LISTED RATHER THAN DERIVED FOR A STATED REASON AND NOT BY OVERSIGHT: `models.py` declares the FIELDS but nothing in it declares which of them hold a person's or an organisation's name, so unlike AC-2's `TYPE_TO_MODEL`, AC-3's `branch_id`s and AC-4's repository set there is no population to read — the classification is judgment, which is why it sits with a stated rule, a recorded field-by-field pass (P14) and a reconciliation instruction instead of a runtime read. Every token extracted from an identity position MUST be in `NAME_POOL ∪ CONNECTIVE_SET` or be an admitted org suffix. `PROSE_ALLOWLIST` IS NOT A TERM IN THIS ASSERTION and is structurally unreachable from it; the test additionally asserts `PROSE_ALLOWLIST` is DISJOINT from the identity-position token set, so no token can hold both roles and adding a surname to the allowlist buys nothing whatsoever for a `name:` value, an `aliases` entry, a title field or a filename stem. **FREE-PROSE POSITIONS** — everything else in reach: note bodies, non-identity frontmatter values, and `fixture_vault.py`'s own source. Tokens here must be in `NAME_POOL ∪ CONNECTIVE_SET ∪ PROSE_ALLOWLIST`. **NON-VACUITY, `NAME_POOL` ONLY** — every `NAME_POOL` entry occurs as an extracted token in at least one IDENTITY position; "somewhere in the reach" is deliberately NOT the bar, because a pool padded through a note body would satisfy it. It is scoped to `NAME_POOL` because `NAME_POOL` is the one declared set THE BUILDER AUTHORS, so it is satisfiable by construction — declare only what the corpus uses. **`CONNECTIVE_SET` CARRIES NO NON-VACUITY OBLIGATION, AND ITS ABSENCE IS A FIX RATHER THAN A RELAXATION.** A mandatory occurrence clause over a set the builder does NOT author is the defect generator this criterion has now bred three times (`to`/`->`/`→`, then `Re`/`Fwd`/`Fw`): every such set has produced at least one member the corpus cannot exercise, and each earlier fold pruned the member and kept the clause. Nothing is lost by dropping it, because exercising the furniture was never the wall — what stops `CONNECTIVE_SET` becoming a second escape hatch is that it is frozen by literal enumeration IN this criterion and asserted equal to it, and coverage of whatever connective the live vault actually produces is already guaranteed by AC-3(i), which requires a specimen for every MEASURED census class and, correctly, can never demand one for a class the vault does not have. The single corpus member that is not valid UTF-8 is exempt from the token scan and instead has its COMPLETE bytes declared in the manifest as a LOWERCASE hex literal and asserted byte-equal — reviewed rather than silently skipped past the wall, and lowercase so the literal yields no extracted token and can never itself become a reason to grow the allowlist. (c) POOL PROVENANCE — SCOPED TO `NAME_POOL` ALONE, AND A CONTAINMENT RATHER THAN AN EQUALITY. `docs/vault-shape-census.md` carries a pool table whose rows each give a certified token, the shape class it is constructed to carry, and the conductor's live-vault non-occurrence scan for it (the command run and its verbatim stdout, showing `0` hits as a name token anywhere in the vault — `## Write Targets` requires that command to emit a COUNT, so an honest zero result records verbatim as `0` rather than as nothing). The test asserts that `NAME_POOL` ⊆ the census's pool table — ONE DIRECTION, and the direction matters — that every row carries a non-empty command and a non-empty stdout, and that the table's token set is DISJOINT from `CONNECTIVE_SET`. AND IT ASSERTS CENSUS FIXITY FIRST, BEFORE IT TRUSTS ANY ROW OF THAT TABLE: `sha256` over `docs/vault-shape-census.md`'s bytes equals the `CENSUS_DIGEST` literal declared in AC-3(iv) and frozen by the same signature that freezes this criterion. This leg is asserted HERE as well as in AC-3 and not merely inherited from it, because each criterion's `check:` is its own test function and an unguarded AC-5 is the worse of the two exposures: the pool table is where this criterion's entire ground truth lives, the suite cannot re-derive a single one of its non-occurrence claims, and `docs/**` is builder-writable in full (`pipeline-runners.yaml:34-38`, P7), so without the fixity assertion a builder who wants a convenient, easy-to-spell pool token — one that may collide with a real name in a vault the builder cannot see and has no way to check — adds a row asserting a scan that was never run, with fabricated command and stdout text satisfying every other check this leg makes (non-empty command, non-empty stdout, containment, disjointness), and `## Intent`'s sentence about Dave's contacts' real names has no machine check standing behind it at all. THE VALUE'S LOCATION IS THE WALL, not the digest: it is read from the signed AC-3 fence in `docs/vault-fixtures.md`, never from a constant in `tests/fixture_vault.py`, because a constant the build owns is updated in the same commit that edits the file it digests. The residue is stated rather than papered over: a build that deletes the assertion outright is the ordinary "did not implement the criterion" exposure every AC here carries — caught by the battery and by code review — and is not a bypass of this leg, whose subject is the expected value's home. THE DIRECTION IS NOT A WEAKENING AND THE REASON IS AN ORDERING FACT ABOUT THIS PIPELINE, NOT A PREFERENCE: the census is a PRECONDITION that lands in HEAD before Dave signs these criteria and long before any corpus exists, while `NAME_POOL` is declared in-cage by a build that has not happened, so a both-directions equality would ask the earlier artifact to predict the later one's exact token set — and a census that certifies one token the build does not end up using would go RED with no in-cage remedy except inventing a note to consume it. Closure is not weakened by a byte: a token with no row still cannot enter an identity position, which is the entire property, and a certified-but-unused row is not a leak because it carries its own scan. It also removes this item's dominant recurring cost — under an equality every corpus edit is a paired edit across the cage boundary, and under a containment it is not. The leg is the same read-the-artifact-and-assert-its-shape move AC-3 makes: hermetic, no subprocess and no vault read. The connectives are exempt from provenance because a non-occurrence claim about them is unmakeable, not merely tedious: `Me`, `My` and `Dave` are the live stored-name prefix forms this vault actually produces — `name_validation.py:238-248` carries `specimen="Me to David Field"` on its `me_to_prefix` Tier-1 branch, `:226-236` carries `Dave - Thomas Gatten` on `calendar_prefix`, and `name_cleaning.py:46`/`:54`/`:55` strip exactly `(Dave|Me|My)` — so a zero-hit row for any of them would be a false statement inside the artifact whose whole job is to be the trustworthy ledger. The exemption's ground is the code's own vocabulary and NOT a guarantee about the census's counts: an earlier draft justified it by saying AC-3 requires the census to report `Me to ` prefixes with a non-zero count, which AC-3 no longer promises now that any class may be ruled ABSENT. It does not need to promise it — `Dave|Me|My` being live prefix vocabulary in this package is a fact about `name_cleaning.py`, readable without the census, and it is what makes the non-occurrence claim unmakeable whatever the census measures. (d) THE PROPERTY IS NOT PAID FOR — every reserved phone in the corpus still normalizes through `normalize_phone` to a stable digits-only value (`phone_normalization.py:39-55` splits off the WhatsApp JID suffix and then strips every non-digit, so `+44 7700 900123` yields `447700900123`; the package emits E.164 nowhere and none is asserted here), and `phones_match` (`:58-90`) still matches that value against the reserved number's `0`-prefixed and `+44`-prefixed variants, so the reservation does not cost the shape the fixture exists to exercise. (e) HERMETIC — materialization writes only underneath the caller's `dest`, and the corpus contains no absolute filesystem path: no occurrence of `/Users/`, and no live vault path in any note or in the manifest.
why: This package installs `-e` into three consumer repos and its git history is permanent — a real address, number, profile URL or NAME committed here is not meaningfully retractable, which is why the 2026-07-05 routing note put this item on Opus in the first place. Legs (b) and (c) exist because the first draft of this criterion walled two of the three categories `## Intent` names and left the third — and names are the field D1's amendment says the corpus exists to carry the shape of, so the uncovered category was the likeliest one to be transcribed verbatim: a specimen whose email is correctly moved under `@example.com` and whose phone is correctly moved into the drama range, but whose `name:` is still the live vault's, passes AC-1 (the digest freezes whatever bytes exist), AC-2 (the manifest declares whatever name is present as "expected"), AC-3 (per-specimen verdicts test refusal behaviour, not identity) and the old AC-5 (no email/phone/URL violation) all green. Names have no RFC 2606, so the wall cannot be a reserved-range rule and CANNOT be a denylist either — committing a list of real names to catch real names would be the leak it is meant to prevent. Closure is the available structural form: every name-shaped token in an IDENTITY position must have been deliberately added to a declared pool, which turns "transcribed by accident" into "typed the real name into the pool and the census's provenance table as well". THE POSITION SPLIT IS WHAT MAKES THAT CLOSURE REAL, and it is the correction of a first attempt that failed on its own terms. That attempt ran ONE undifferentiated scan over the whole reach and offered two buckets — the pool, or a prose allowlist "of the ordinary vocabulary the note bodies and YAML keys need". The allowlist was unbounded, owed no census row, and was consulted from the same positions the wall exists to police, so the cheapest green for a specimen carrying the live vault's real surname was to type the surname into the allowlist, where a real name is not visibly out of place: the wall's bypass was larger, cheaper and more heterogeneous than the wall, which is not closure. The reach makes that worse rather than better, and the reach is still right — `fixture_vault.py` is a Python module and every capitalized identifier in it (`Path`, `SkippedNote`, `NameGateRefusal`, `UnicodeDecodeError`, the `AC-`/`WI-` prose) is an extracted token, so an allowlist covering it must be large and heterogeneous on day one. Splitting by POSITION rather than by bucket makes the size of the allowlist stop mattering: it is reachable only from free prose and is asserted disjoint from every identity token, so it can grow to whatever the module's vocabulary needs without ever being able to admit a token into the field that carries identity. TWO CHEAPER ALTERNATIVES ARE REJECTED HERE so a builder does not rediscover them. Putting the census provenance obligation on the allowlist too collapses it into the pool — it taxes every docstring word with a conductor scan and doubles the two-artifact join for no privacy gain, since prose is not where identity lives. Dropping the allowlist entirely and forcing all prose through the pool is the same move by another name and makes the pool table unreviewable, which destroys the mitigating control's own premise: what a human reviews is a few hundred declared IDENTITY tokens once. Likewise the CONNECTIVE split: a first draft put connectives and names in one pool under a type tag and then demanded a zero-hit live-vault row for every member, which is unsatisfiable by construction for `Me` — AC-3 charges the same artifact with reporting `Me to ` prefixes as a measured, non-zero class — so every route through it was either a RED criterion or a fabricated row. Connectives are exempt from provenance because non-occurrence is not a claim that can honestly be made about them; the exemption is safe ONLY because the set is frozen by enumeration in the criterion, which is what stops it becoming the same escape hatch the allowlist was, and it is asserted disjoint from the census table so nothing can be smuggled across the boundary in either direction. THE FOURTH FOLD REMOVED THE GENERATOR RATHER THAN ITS LATEST INSTANCE, AND THAT IS THE ONE THING TO KEEP IF THIS CRITERION IS EVER EDITED AGAIN. Three consecutive independent reads found a defect of a single family: a mandatory obligation over a declared set THE BUILDER DOES NOT AUTHOR — first a non-occurrence row demanded of `Me`, then an occurrence demanded of `to`/`->`/`→`, then an occurrence demanded of `Re`/`Fwd`/`Fw`, tokens that a Grep shows occur nowhere in this repository outside this document (P11). Each earlier fold pruned the member and kept the clause, which is why the family kept producing. Dropping `CONNECTIVE_SET`'s non-vacuity and making (c)'s pool relation a CONTAINMENT removes both surviving instances of the pattern at once, and the property they were nominally protecting is not lost: padding is prevented by the literal enumeration and by the per-token census scan, not by exercise. The same reading is why the identity-position list is now ENUMERATED against `models.py` with line cites instead of named by category — the previous phrase, "the company/meeting title fields", is exactly how `Person.company` was missed, and reading the models field by field showed it had also named a field `Meeting` does not have (`:259-263`) while missing `Meeting.attendees` (`:261`), `Book.author` (`:161`), `Watch.director` (`:195`), `Watch.recommended_by` (`:200`), `Explore.source` (`:224`) and `GiftIdea.for_person` (`:242`). Patching the one field named would have left six doors of the same shape one entity type over; stating the generating rule and the enumeration closes the family the way dropping non-vacuity closes the other one. THE FIFTH FOLD IS WHY THAT RULE IS NOW THREE CLAUSES INSTEAD OF ONE, AND THE LESSON IS NARROWER THAN THE FOURTH FOLD'S. Stating a one-line rule and then enumerating under it is not the same as enumerating BY it: two independent reads applied the single rule to `models.py` field by field and got a list that differed from the written one in both directions — it omitted `Exploration.related` (`:299`), whose own docstring (`:280`) glosses its members as `[[Other Exploration]], [[Person]], etc.`, and it included four media-`title` fields the rule plainly excludes. The omission was the expensive direction, because `related` is a field whose value IS a person link and the criterion scored it free prose: a real contact's name written there went RED once on the free-prose leg and the cheapest green was ONE `PROSE_ALLOWLIST` entry — no pool membership, no census row — which is the exact bypass rounds 1 through 4 were each raised to close. And it was live rather than theoretical for this corpus specifically: AC-2 derives its sweep from `set(TYPE_TO_MODEL)`, `exploration` is a member, P4 measures ZERO `exploration` references anywhere under `tests/`, so this corpus is guaranteed to contain the first `exploration` fixture anyone has authored — hand-written from a live note's shape, by an author with nothing to copy from, and `related:` is the field that shape hangs on. The inclusion direction cost nothing yet but was the same defect: a criterion whose own reconciliation instruction ("reconciled against the schema BEFORE origination") tells a later reader to re-derive the list from the rule, while the rule as written deletes four listed fields, is buildable two ways — the WI-144 shape. Clause 2 fixes that by making the over-constraint DECLARED rather than accidental, so the reconciliation preserves it instead of pruning it on the rule's own authority; clause 3 reaches the one door no enumeration over declared fields can, since `extra="allow"` (`:31-32`) means a specimen may carry keys no model declares. The two undecided siblings are decided rather than left: `Watch.streaming_service` (`:199`) names an organisation exactly as `Book.publisher` (`:166`) does and is now listed with it, and `GiftIdea.source` (`:243`) is listed alongside its glossed sibling `Explore.source` (`:224`) because a gift idea's source is plausibly whoever suggested it — the same value kind must not get opposite answers inside one enumeration, which is what produced this finding. AND THE THIRD PLACE THE MACHINE STOPS IS NOW NAMED WITH THE OTHER TWO, because clause 1's "IS a name, not COULD CONTAIN one" is what buys the criterion its satisfiability: a real name written into `Exploration.origin` (`:300`), `Meeting.topics` (`:262`) or a note body is walled by the free-prose leg and the pool's human review, not by the closure, and one allowlist entry is its cheapest green. That residue is not new and is not a regression — note BODIES have been on that side since round 1 and always will be, because prose cannot be closed against a pool without taxing every English word with a conductor scan (the alternative rejected two paragraphs above). What the fold guarantees is the line's PLACEMENT: no field whose value IS a name sits on the prose side of it, which is what `Exploration.related` was doing. The org-suffix admission is derived from `name_cleaning._GENERIC_ORG_SUFFIXES` rather than hand-declared for the same discipline: a fourth hand-written literal set is what the generator eats, and a set read from the package cannot be padded by whoever is looking for the cheapest green. Say plainly where the machine stops: the suite is hermetic and cannot read the live vault, so the GROUND TRUTH that a pool token does not name a real contact is the conductor's recorded scan in the census, not an in-suite assertion — leg (c) asserts that the scan was run and recorded for every token, and the census's re-runnable command is what a later reader checks it against. That is the mitigating control, named and tied to a criterion rather than left as D4's unstated "reviewable by eye" aside — and it is a real reduction, because what a human now reviews is a few hundred declared tokens once, not fifty notes of free text every time the corpus changes. THE SECOND PLACE THE MACHINE STOPS IS THE EXTRACTOR'S OWN DOMAIN, and it is named here rather than chased with another clause. The extractor takes runs beginning with an uppercase or non-ASCII letter, so an identity value written entirely in lowercase yields no token and is outside the wall — the same fact that (correctly) keeps `to`, `->` and `→` out of `CONNECTIVE_SET`. A deliberate "lowercase it to get green" dodge is therefore not closed by machine, and deliberately is not: it destroys the character profile the specimen exists to carry, so AC-2(b)'s hand-written declared oracle and AC-3's declared per-specimen verdict both go RED on it, and the residue is covered by the same one-time human review of the pool table. A fifth clause bolted on to close it would be a mandatory obligation over something the criterion cannot see — the shape of every finding this criterion has produced so far. THE SIXTH FOLD PINNED THE EXTRACTOR'S "RUN" AND THEN RE-ENUMERATED THE FURNITURE SURFACE IN THAT ORDER, AND THE ORDER IS THE WHOLE LESSON. The finding arrived as two halves that disagreed: one read said `CONNECTIVE_SET` was sampled from three of the five prefix/suffix regexes in `name_cleaning.py` and should gain `Archived`, `Unknown` and `Contact`; the other said that literal fix is contradicted by this repository's own specimens, because the criterion's extractor never said what a "run" is and, under the plain maximal-span reading, `zArchived` yields no token at all — so `Archived` would be an unexercisable literal in a frozen set, which is exactly the round-4 defect with a gate's fold as its author instead of a builder. Both halves are right and the resolution is sequencing, not a compromise: the membership question is not answerable until the extraction rule is, so the rule is stated first (maximal span, no camelCase restart, first character decides, trim `'`/`-`), with four worked examples so it is checked rather than interpreted, and only THEN is the surface re-enumerated by applying it. Done in that order the answer is that the set does not move: the fifteen regexes' own literal spellings extract to exactly `{Me, My, Dave}`, `archive_prefix` contributes nothing under the reading every committed specimen for it supports (P15, five specimens, no exceptions), and `unknown_contact` contributes nothing from the code because both its regexes spell the literal lowercase. What the re-enumeration did buy is the one genuinely undecided cell being named instead of guessed: `re.IGNORECASE` on `name_validation.py:113` puts the letter-case of the live `unknown contact` form in the vault's hands rather than the code's, and this repository already commits it BOTH ways, so no amount of reading `obsidian_schemas/` settles it. That cell gets AC-3's own remedy — a one-time pre-origination reconciliation against the census, which lands in HEAD while these are still drafts — rather than a fifth hand-written literal or a guess frozen by signature. It is worth being explicit that the reconciliation instruction is NOT the round-4 generator returning: the generator was a mandatory obligation over a set the builder does not author, and this set still carries no occurrence obligation at all; what it now carries is a one-time edit, made by the author before signature, against an artifact that exists by then, after which the set is as frozen as it was before. The general rule the two closures share, and the one to attach if this criterion is edited again: EVERY SET AC-5 DECLARES IS ENUMERATED BY APPLYING A STATED RULE TO A NAMED, ENUMERABLE SURFACE — round 5 needed `models.py` read field by field, this round needed the sixteen regexes read one by one, and both defects were "enumerated by sampling" rather than by the rule. Leg (d) is the honest cost check: a reserved-range rule that broke `normalize_phone`'s own fixtures would have bought privacy by deleting the property, and the UK drama range and NANP 555-01xx are chosen precisely because they are well-formed dialable-shaped numbers that will never ring. The leg names the digits-only output rather than E.164 because that is what the function actually produces — it strips every non-digit (`phone_normalization.py:39-55`), so the leading `+` does not survive and nothing in this package emits E.164; asserting E.164 would have been a criterion the corpus cannot satisfy no matter how well the reserved ranges were chosen, and `phones_match`'s `44`/`0` and `1`/10-digit arms (`:58-90`) are the property worth protecting anyway. Leg (e) keeps the corpus portable — a fixture carrying `/Users/davewascha/...` is both a small leak and a note that means something different on any other machine, and D6's eventual export to the consumer repos depends on the bytes travelling unchanged.
check: test_no_corpus_note_carries_a_live_identifier
kind: test
```

### Examples of done

**Given** someone writes a new test that needs a vault — **when** they call
`materialize_vault(tmp_path)` — **then** they get ~50 notes with accents, hyphenated surnames, an
address that leaked into a name field, the same person three times, notes that will not parse, and
one of every entity type, without typing a single note. **And** the bug their change would have
shipped is caught by a corpus they did not have to think of, which is the whole reason it is there.

**Given** a future change to the parser that quietly breaks `Exploration` — **when** the floor runs —
**then** it goes RED, because `exploration` is a member of `TYPE_TO_MODEL` and the sweep is derived
from that map rather than from a list someone maintains. **And when** a ninth entity type is added
with no fixture, the same sweep fails for the same reason, rather than the type joining `watch`,
`explore` and `gift-idea` in the untested set.

**Given** a fixture note someone edits to make their own test pass — **when** the floor runs —
**then** the frozen digest mismatches and says so. **And given** an attempt to plant the corpus
through `repo.save()` instead of copying bytes, **then** the arrow-connective and path-hostile
specimens are refused by the gate and the corpus is provably incomplete — the two failures the word
"frozen" is doing work against.

**Given** the corpus is read by anyone, anywhere — **when** they look for a real person — **then**
every address is `@example.com`, every number is a range that will never ring, every name in a field
that carries identity — a `name:`, an alias, a person's `company:`, a meeting's attendee, a book's
author, a gift idea's `for:`, an exploration's `related:` link, a frontmatter key no model even
declares, a filename — is a token from a pool the census certifies does not occur
in the live vault, and the shapes are still the ones the live vault actually
contains, because the census measured the distribution and the committed bytes are synthetic. **And
given** someone adds a note to the corpus whose `name:` is not in that pool, **then** the floor goes
RED — and the only way to green is the pool and the census's provenance row, because the prose
allowlist that keeps ordinary English quiet is not consulted for a name field at all. A real name
cannot arrive by accident; only by being typed into the pool and the ledger as well.

## Verified Diagnosis

Every load-bearing claim this spec makes about how the package behaves TODAY, with the artifact that
falsifies it. All were re-run in THIS worktree (`cage-wt-do7tmnmo`, the WI-022 delta committed) by
the 2026-09-07 data-premise round; the five below were additionally re-read here by the spec-writer
rather than inherited from that round's prose.

| # | Claim | Falsifiable artifact | Verified |
|---|---|---|---|
| D-1 | The repository holds ZERO fixture data files and no `conftest.py`, so every test that needs a vault builds one inline. | `Glob tests/**` returns 32 entries, all `.py`; `Glob **/conftest.py` returns nothing; `tests/derivations.py:9-12` states the absence as load-bearing. | P1, P2; re-run by the data audit. |
| D-2 | `Exploration` is committed, wired into dispatch, and has ZERO test references. | `models.py:266-302` declares it; `models.py:306` puts it in `EntityType`; `models.py:317` puts it in `TYPE_TO_MODEL`; `body_sections.py:320-323` gives it a section config; a scan of `tests/` for `[Ee]xploration` returns nothing. | P4; re-run by the data audit. |
| D-3 | Nothing in the suite sweeps the type registry, so three further types are in `Exploration`'s position by construction. | `TYPE_TO_MODEL` (`models.py:309-318`) declares 8; `ENTITY_BODY_CONFIG` (`body_sections.py:303-324`) declares 5; `get_default_body` returns `""` for a missing key (`:337-338`), so `watch`, `explore` and `gift-idea` have no asserted body answer anywhere. | P5; re-read here. |
| D-4 | The skip surface has no corpus: no vault on disk carries one note of each `_skip_reason` class and declares which is which. | `_skip_reason` (`repositories/base.py:41-47`) returns three strings derived from the error TYPE; the only tests naming `skipped_notes` / `SkippedNote` anywhere in the tree are `tests/test_loud_fail_load.py` and `tests/test_name_gate.py`, and both plant their own ad-hoc vault. | P6; re-read here. |
| D-5 | The skip-reason vocabulary is the one classification in this package that is DECLARED nowhere a test can read. | `repositories/base.py:44`, `:46`, `:47` are bare return literals; `:37` is a type comment; `repositories/__init__.py:14-21` exports four repositories, `BaseRepository` and `VaultPathNotConfiguredError` and nothing else. Contrast `TYPE_TO_MODEL` (`models.py:309-318`), `ENTITY_BODY_CONFIG` (`body_sections.py:303-324`), `TIER1_BRANCHES` / `COMPANY_TIER1_BRANCHES` (`name_validation.py:190-309`, `:371-438`), `_GENERIC_ORG_SUFFIXES` (`name_cleaning.py:58`) — every one of them a module-level literal. | P20; re-read here, both files in full. |
| D-6 | Half the corpus is notes the write door now REFUSES to create, so byte copy is the only mechanism that can carry them. | `writer.py:252-253` calls `gate_write` on the assembled payload before serializing; `name_gate.py:361-363` runs `validate_strict` over `TIER1_BRANCHES` for `person` and `:340-341` over `COMPANY_TIER1_BRANCHES` for `company`; `Tier1Branch.matches` (`name_validation.py:179-184`) is the predicate. A note whose `name:` is `Dave -> Thomas Gatten (Adzact)` cannot be written through that door. | Re-read here. |
| D-7 | A corpus laid out one-subdirectory-per-type is globbed by NOTHING. | `load()` calls `self.vault_path.glob(self.file_pattern)` — non-recursive (`repositories/base.py:231`); `person.py` and `company.py` declare no `file_pattern` and inherit `@*.md` (`base.py:195-198`); `meeting.py:51-54` declares `Meeting *.md`; `book.py:50-53` declares `*.md`. | Re-read here; the data audit ran the same read. |
| D-8 | The conveyor does NOT necessarily run a `kind: test` check under this project's interpreter, so a check module that executes the library and lacks the bridge reports `ModuleNotFoundError` against a floor that is green in the same tree. | `tests/ac_interpreter.py:7-25` states the mechanism and records the observed outcome ("five-of-five criteria, with a floor that was green in the same tree"); `:123-130` is the no-op fast path, `:150-155` the `os.execve` delegation, `:136-148` the fail-closed raises; six modules call it as their first statement (`tests/test_company_name_contract.py:25`, `tests/test_address_splitter.py:38`, `tests/test_name_gate_identifiers.py:41`, `tests/test_name_gate_refusals.py:41`, `tests/test_name_gate_wall.py:40`, `tests/test_name_gate_delta_rule.py:37`); `tests/test_ac_interpreter.py:40` scopes the standing wall to `docs/write-door-bypasses.md`, so this item is outside it; `docs/identity-engine-endgame.md:2742-2746` prices the scar. | Read here in full, all nine files. |
| D-9 | The three skip-reason strings are hand-typed at THREE test sites, not one; and printable ASCII hex-encodes to digit-first nibbles, so a hex literal in reach carries phone-shaped runs by construction. | A grep for the three literals over every `*.py` in this worktree returns `obsidian_schemas/repositories/base.py:37`, `:44`, `:46`, `:47`, `obsidian_schemas/errors.py:112`, `tests/test_loud_fail_load.py:188`, `:209` and `tests/test_name_gate.py:152` — eight sites, of which three are hand-typed test comparisons. For the hex half: the five bytes of `type:` encode to `747970653a`, whose first nine characters are the ≥9-digit run `747970653`, and §6.4's phone predicate matches any maximal `[0-9+()\-. ]` span with ≥9 digits. | Grep run and every site read here; the hex encoding is arithmetic, not a measurement. |
**Not a diagnosis and marked as such.** "A frozen corpus would have caught bug X" is nowhere in this
spec, because no such bug is on the record. The item's warrant is D-1 through D-7, which are facts
about absence and about mechanism, not about a breakage anyone has observed. That also decides
Verification's incident-replay question — see `## Verification`. **D-8 and D-9 are a different kind
and are separated here rather than counted with the seven:** they are load-bearing claims about how
the BUILD PIPELINE and this spec's own predicates behave, added when a review round found each one
about to cost a build attempt, and neither is an incident this package suffered. They do not make
this an incident-class item (WI-173) — WI-021's battery, which D-8 cites, is another item's incident,
already closed by another item's shipped bridge, and this item's obligation is to CALL that bridge
rather than to replay anything.

---

## Design

### §0. The change in one paragraph

Land a flat, frozen, ~50-note markdown corpus at `tests/fixtures/vault/`, beside a declaring module
`tests/fixture_vault.py` that holds the corpus's hand-written expected values, a `sha256` over its
bytes, and a `materialize_vault(dest)` that BYTE-COPIES it into a caller-supplied directory. The
corpus's *shapes* come from a conductor-run census of the live vault
(`docs/vault-shape-census.md`, the declared precondition); its *identities* are constructed tokens
the census certifies occur nowhere in that vault. Five checks in one new module
`tests/test_fixture_vault.py` then close five classes the tree already declares — the type registry,
the Tier-1 refusal branches, the repository partition, the skip-reason codomain and the
identifier-containment wall — each sweeping a population READ from its declaration and comparing it
against an oracle HAND-DECLARED in the manifest. One line of package change makes the fifth
population readable: a `SKIP_REASONS` frozenset in `obsidian_schemas/repositories/base.py`, bound to
`_skip_reason`'s own returns by a syntax scan in `tests/derivations.py`.

### §1. Data model — the corpus on disk

#### §1.1 Layout

`tests/fixtures/vault/` is **ONE FLAT DIRECTORY**. No subdirectories, ever. This is load-bearing,
not cosmetic: `load()` globs non-recursively from a single `vault_path`
(`repositories/base.py:231`) and the four repositories partition that one directory by filename
pattern, so a subdirectory-per-type corpus is globbed by nothing and AC-4 passes vacuously on
`0 == 0` (D-7).

Every member is a regular file directly under that directory. `materialize_vault` and
`corpus_digest` both walk it with `sorted(CORPUS_ROOT.iterdir())` and skip non-files, so a stray
directory is silently excluded from both — which is why the corpus carries none and why Task 4's
digest is taken over the same walk the materializer performs.

#### §1.2 Filename grammar

The stem is an identity position under AC-5(b), so the grammar is pinned here and every variable
part is a constructed token from `NAME_POOL`:

| Type | Filename | Source |
|---|---|---|
| `person`, `company` | `@<Name>.md` | `save()` writes `vault_path / f"@{name}.md"` (`base.py:381-383`); both repositories glob `@*.md` (`base.py:195-198`) |
| `meeting` | `Meeting <YYYYMMDD> - <Title>.md` | `MeetingRepository.file_pattern` is `Meeting *.md` (`meeting.py:51-54`) |
| `book` | `<Title> - <Author>.md` | `BookRepository.file_pattern` is the catch-all `*.md` (`book.py:50-53`) |
| `watch`, `explore`, `gift-idea`, `exploration` | `<Title>.md` | No repository, therefore no glob — AC-2 exercises these at the PARSER level and they are outside AC-4 entirely |

The stem-normalisation AC-5(b) names is exactly: strip a leading `@`; strip a leading
`Meeting <digits> - ` prefix; drop the `.md` suffix. What remains is tokenised by §6's extractor and
must be drawn from the pool. Meeting titles, book titles and authors are therefore CONSTRUCTED
tokens and never naturally-worded English — `Meeting 20260104 - Voxleaf Kelmarra.md`, never
`Meeting 20260104 - Quarterly Sales Review.md`, because `Quarterly`, `Sales` and `Review` cannot
carry an honest zero-hit live-vault row and `## Write Targets` says so in as many words.

#### §1.3 Composition — the rules, not a list of fifty filenames

The specific notes are a function of the census, which does not exist yet. What is fixed here is
the RULE SET a corpus must satisfy, so the builder assembles rather than invents:

1. **Type totality.** Every member of `set(TYPE_TO_MODEL)` (8 today) has at least one note, and
   exactly one of that type's notes is the manifest's `roundtrip_representative` — which must be
   GATE-CLEAN in the door's own sense (§5.3).
2. **Class coverage.** Every census class row with `status: MEASURED` has at least one specimen
   note, carrying that row's character profile. **A note is the SPECIMEN for a class iff it DECLARES
   that class id in its `NoteSpec.shape_classes`, and that declaration is the only thing AC-3(i)'s
   equality reads** — so a note whose `shape_classes` is `()` is the specimen of nothing, is outside
   assertion (i) in both directions, and is not a criterion violation. Most corpus members are in
   exactly that position already (the eight type representatives, the skip specimens, the collision
   members), and rule 7's two discriminators join them. Against the LANDED census this rule names
   SIX classes and no others: `diacritics`, `hyphenated_surname`, `whitespace_damage`,
   `stem_name_divergence`, `postal_address_in_name`, `pure_digit`. The other ten rows are ABSENT and
   oblige no specimen; declaring one of them in any note's `shape_classes` is RED under AC-3(i),
   which is scoped to MEASURED rows.
   *One shape the census records with NO class row and therefore NO specimen owed, named so a
   builder does not plant one:* an emoji-only stored name (`✨🌙 ✨`), which the census's prose files
   under `diacritics`' seventh non-ASCII name and rules out of the class floor because nothing in the
   package refuses it. It is recorded there for WI-026, not for this corpus.
3. **Skip coverage.** Every member of `SKIP_REASONS` has at least one specimen, and the two untyped
   classes are planted TWICE — once as `@<Name>.md`, once as `Meeting <date> - <Title>.md` — which
   is AC-4(b)'s discriminator (§5.4).
4. **The one non-UTF-8 member.** Exactly one file is deliberately not valid UTF-8. That is the only
   spelling of the `unreadable` class that survives git: `parse_markdown_file` reads with
   `read_text(encoding="utf-8")` unwrapped (`parser.py:238`), so invalid bytes raise
   `UnicodeDecodeError`, which is neither `FrontmatterParseError` nor `SchemaDriftError` and falls
   to `_skip_reason`'s third arm (`base.py:47`). A `chmod`-based specimen is NOT reached for; git
   does not carry a mode that makes a file unreadable to its owner.
5. **The collision.** At least three distinct filenames share one stored `name:`. **The CENSUS has
   now ruled, and the ruling changes what this note is DECLARED as rather than whether it is
   planted.** The landed artifact rules `same_name_collision` ABSENT (count 0 — the largest live
   collision is two) and `stem_name_divergence` MEASURED (count 8), so they are TWO classes and only
   the second is on AC-3(i)'s MEASURED side. The three-filename collision is STILL PLANTED — §3's
   `LOADABLE` arithmetic depends on it, and it is the only thing in the corpus that exercises
   `_get_cache_key`'s collapse — but it is declared under `shape_classes = ("stem_name_divergence",)`
   (structurally, a flat corpus's collision IS a divergence, which is the census's own reading at its
   ONE-or-TWO ruling) and **never as a `same_name_collision` specimen, which would be RED against that
   ABSENT row.** An earlier draft of this rule left the naming to "the CENSUS's ruling" while the
   ruling did not yet exist; it exists now and is written in rather than pointed at.
6. **Size.** ~50 notes. The number is an approximation and no criterion asserts it; rules 1-7 are
   what the corpus must satisfy, and if the census measures more classes than fifty notes can carry
   comfortably, the corpus grows and nothing in this spec moves.
7. **The two AC-1(c) discriminators — MANDATORY MEMBERS THAT ARE THE SPECIMEN OF NO CLASS, and this
   rule is the reason they can exist at all.** AC-1(c) obliges the corpus to carry at least one note
   whose stored `name:` matches a live Tier-1 branch, with "an arrow-connective descriptor and a
   path-hostile name … both present, named in the manifest as such". The landed census rules
   `arrow_connective` (count 0) and `path_hostile` (count 0) BOTH ABSENT, so neither is a MEASURED
   class and neither may be declared in any note's `shape_classes` without breaking AC-3(i)'s
   both-directions equality. The two obligations are reconciled by giving them DIFFERENT manifest
   fields: the two notes carry `shape_classes = ()` and are named by `NoteSpec.discriminator`, a
   dedicated field holding the `branch_id` of the live branch their `name:` trips (§3). "Named in the
   manifest as such" is satisfied by that field — AC-1(c)'s test reads `discriminator`, never
   `shape_classes` (Task 4) — and AC-3(i)'s covered-class set never sees them. Both notes are
   `person`-typed, neither is any type's `roundtrip_representative` (rule 1 forbids it: the door
   refuses them), and their identity tokens are constructed from `NAME_POOL` like every other
   specimen's. The corpus is buildable exactly ONE way as a result; before this rule it was buildable
   two, and one of the two was RED with no in-cage remedy once these criteria were signed.

#### §1.4 What is NOT in the corpus

No real email, phone, profile URL or name — that is AC-5, asserted structurally over the corpus
bytes AND over `tests/fixture_vault.py`. No absolute filesystem path and no occurrence of `/Users/`
(AC-5(e)). No string matching `\w+Repository\(\s*\)`, because the corpus's `.md` files join a
standing repo-wide markdown scan — see §11, W-8.

### §2. Data model — the census artifact's machine-readable shape

`docs/vault-shape-census.md` is written by the CONDUCTOR and PARSED by the suite. Its prose is the
conductor's; its machine-readable rows are three fence kinds, in the flat `key: value` grammar this
pipeline already uses for `criteria`, `writes` and `fold`. **Every value is ONE line.** A fence with
an unrecognised key, a missing required key, or a `status` outside the two-member vocabulary is a
LOUD parse failure, never a skipped row (§5.5).

**Class row** — one per shape class, `id` unique in the document:

```
    ```census-class
    id: rfc2822_leak
    count: 12
    status: MEASURED
    command: rg -c '\bat[a-z]+(com|org|net)\b' "$VAULT"/*.md | wc -l
    stdout: 12
    specimen: Naomi Pavie naomipavieatspeechmaticscom
    ```
```

- `id` — for a branch-backed class this is the package's own `branch_id` and nothing else (AC-3's
  floor reads `{record.branch_id for record in TIER1_BRANCHES + COMPANY_TIER1_BRANCHES}` at test
  time). For one of the six shape classes with no branch, it is the id AC-3 reconciles against
  before origination.
- `count` — a non-negative integer.
- `status` — exactly `MEASURED` or `ABSENT`. `ABSENT` iff `count` is `0`.
- `command` — the scan run against the live vault. It MUST emit a COUNT, per the precondition
  fence, so an honest zero result is printable.
- `stdout` — that command's verbatim output. Non-empty at both statuses, which is only satisfiable
  because of the counting constraint on `command`.
- `specimen` — present iff `status: MEASURED`; the pseudonymous specimen carrying the class's
  character profile. Absent on an `ABSENT` row.
- `ruling` — present iff `status: ABSENT`; the affirmative statement that the shape does not occur.

**Pool row** — one per certified identity token:

```
    ```census-pool
    token: Voxleaf
    class: company-name
    command: rg -c -i -w 'Voxleaf' "$VAULT" | wc -l
    stdout: 0
    ```
```

**Header** — exactly one, carrying the snapshot's currency:

```
    ```census-meta
    snapshot: 2026-09-07
    vault_notes_person: 1150
    vault_notes_company: 659
    ```
```

`census-meta` keys beyond `snapshot` are free-form `vault_notes_<type>` counts; the reader requires
`snapshot` and ignores the rest, so the conductor can record per-type totals without a paired spec
edit. The three values above are the LANDED artifact's own, quoted rather than invented — an earlier
draft of this example carried a guessed date and a company figure taken from the 2026-07 corpus
audit, which is a stated-number-versus-actual-artifact divergence in an illustrative block and is
aligned here because this document's examples are read as descriptions of the file the build parses.

**These three fences are the artifact's whole machine surface.** Everything else in the file — the
`lint_vault` auto-fix shapes the precondition fence asks for, the ONE-class-or-TWO ruling, the
postal-address ruling — is prose the conductor writes and a human reads. Nothing in the suite parses
it, and nothing in the suite may start to: the digest (AC-3(iv)) is what makes the prose trustworthy,
not a parser.

**"Outside the PARSER" is not "outside every check", and the distinction is M1's whole subject —
stated here so the sentence above is not read as forbidding the fold.** The rule above is about
STRUCTURE: no assertion may depend on the meaning, ordering or presence of a prose bullet, because
prose is where the conductor writes what no schema anticipated. M1 adds an assertion that depends on
none of those things — it decodes the WHOLE file, prose and fences alike, as a byte stream and runs
§6.1's identity-token extractor over it (§6.5). The file's prose is therefore outside the suite's
parser and INSIDE the suite's identity scan, which is the only way the artifact the privacy wall
depends on can itself be inside that wall. A conductor may rewrite any prose bullet freely; what
they may not do is put an uncertified identity token in one.

### §3. Data model — the manifest module `tests/fixture_vault.py`

Three things and no test logic. Imports: `hashlib`, `dataclasses`, `pathlib`,
`typing`, plus ONE package import — `from obsidian_schemas.repositories.base import
MALFORMED_FRONTMATTER, SCHEMA_DRIFT, UNREADABLE` — because `SKIPS`'s reason values are those
constants and never re-spelled literals (§4's single-home rule; a manifest that re-spells them is a
member of the wall's population and re-opens the transcription this item closes). **It must not name
`ast`** (§11, W-1) and must contain no URL and no absolute path. **`unicodedata` is deliberately NOT
in that list, and its absence is the module's boundary rather than an oversight:** the only consumer
is the identity-token extractor's `_runs` (§6.1), which lives in `tests/test_fixture_vault.py` with
the rest of the test logic — an unused `unicodedata` here would invite a builder to put the extractor
in the manifest, which `## Approach`'s "three things and no test logic" forbids. §6.1, Task 8 and the
Self-Review Dry Run all place it in the check module; P-7 lists the item's whole stdlib surface across
both modules. That package import is why this module is
no longer stdlib-only, and it is also why nothing about the bridge below changes for it: this module
is never a check module, and every module that imports it either runs under the floor or opens with
the bridge itself.

```python
"""The frozen fixture corpus and its DECLARED oracle (WI-016).

CORPUS_COUPLING: this module is the sole reader of `tests/fixtures/vault/`; it
pins nothing in `docs/**` and derives no member by proxy — the manifest names
every note by its exact filename and the digest is over frozen bytes.

Load-bearing external dependency: AC-5(b) admits an identity-position token
whose `str.lower()` is in `obsidian_schemas.name_cleaning._GENERIC_ORG_SUFFIXES`
(name_cleaning.py:58) with no pool row. An edit THERE widens this module's
privacy admission with no AC change. Read that set before adding to it.

Regenerating CORPUS_DIGEST after a deliberate corpus edit — one line, from the
repo root, and deliberately a speed bump rather than a puzzle:

    .venv/bin/python -c "import sys; sys.path.insert(0, '.'); \
        from tests.fixture_vault import corpus_digest; print(corpus_digest())"
"""

CORPUS_ROOT = Path(__file__).resolve().parent / "fixtures" / "vault"
CORPUS_DIGEST = "<64 lowercase hex, filled at Task 4>"

@dataclass(frozen=True)
class Verdict:
    kind: str            # "refusal" | "cleaned" | "loads"
    pattern: str = ""    # kind == "refusal": the NameGateRefusal.pattern expected
    cleaned: str = ""    # kind == "cleaned": clean_person_name's expected output

@dataclass(frozen=True)
class NoteSpec:
    declared_type: Optional[str]        # the note's `type:` value; None when nothing legible
    fields: Optional[dict]              # DECLARED expected parsed values; None for a skip specimen
    undeclared: dict                    # values for keys the model does not declare (extra="allow")
    shape_classes: tuple                # census class ids this note is the specimen for; () for a
                                        # note that is the specimen of no class — the ONLY field
                                        # AC-3(i)'s covered-class equality reads
    discriminator: str = ""             # AC-1(c) ONLY: the branch_id of the live Tier-1 branch this
                                        # note's `name:` trips. "" for every other note. Read by
                                        # AC-1(c) and by NOTHING else — never by AC-3
    verdict: Optional[Verdict]
    roundtrip_representative: bool
    raw_bytes_hex: Optional[str]        # ONLY the non-UTF-8 member; lowercase hex, complete bytes

NOTES: dict[str, NoteSpec]              # keyed by filename, corpus-relative, no directory part
SKIPS: dict[str, dict[str, str]]        # {repository type_name: {filename: reason}}; the reason
                                        # values are the imported constants, never re-spelled
                                        # literals — WHICH constant a given filename maps to stays
                                        # the hand-declared oracle (§4)
LOADABLE: dict[str, int]                # {repository type_name: expected len(repo.get_all())}
RESOLVABLE: tuple                       # ((query, expected Person.name), ...) for PersonRepository.resolve
IDENTITY_FIELDS: dict[str, tuple]       # {entity type: field names that are identity positions}
NAME_POOL: frozenset
CONNECTIVE_SET = frozenset({"Me", "My", "Dave"})
PROSE_ALLOWLIST: frozenset
RESERVED_ISBN: str                      # the ONE ISBN placeholder the corpus uses, §6.4

def materialize_vault(dest) -> Path
def corpus_digest(root: Path = CORPUS_ROOT) -> str
```

**`fields` is HAND-WRITTEN from the model definitions and never produced by running the parser.**
That is the whole of AC-2's oracle: a manifest generated by parsing the corpus asserts that the
parser agrees with itself. The reviewer's cheapest tell that this rule was broken is a `fields`
mapping that reproduces the parser's normalisations (dates coerced to strings by
`_normalize_frontmatter`, `parser.py:111-134`) on a note whose frontmatter does not show them.

**`discriminator` and `shape_classes` are two fields because AC-1(c) and AC-3(i) ask two different
questions, and one field could not answer both.** AC-1(c) asks "is a note whose `name:` trips a live
Tier-1 branch present, and is it NAMED as such in the manifest?" — a question about the DOOR's
behaviour, which is a fact about the package and is true whatever the live vault contains. AC-3(i)
asks "does the corpus's declared class coverage equal the census's MEASURED rows?" — a question about
the VAULT's distribution. The landed census answers the second with `arrow_connective: ABSENT` and
`path_hostile: ABSENT` while the first still obliges both notes, so a single field naming the class
would satisfy AC-1(c) and break AC-3(i)'s equality, and an empty single field would satisfy AC-3(i)
and leave AC-1(c)'s "named as such" satisfied by nothing the manifest declares. Two fields, read by
two criteria, and neither criterion's text moves. **The discriminator value is a `branch_id` and is
asserted to be one:** AC-1(c)'s test checks each non-empty `discriminator` is a member of
`{record.branch_id for record in TIER1_BRANCHES + COMPANY_TIER1_BRANCHES}` — the same runtime read
AC-3(iii) makes — so the field cannot be padded with a free-text label, and it names the same
vocabulary the census's branch rows are keyed on without joining that criterion's equality.

**AND `Verdict.pattern` IS THE OTHER VOCABULARY OF THE SAME DECLARATION — the rule is stated once,
here, because `Tier1Branch` carries two same-shaped string fields and this document had them
crossed.** *A declared refusal `Verdict`'s `pattern` is the RECORD'S `pattern` FIELD, never its
`branch_id`.* `Tier1Branch`'s own docstring settles it (`name_validation.py:152-154`): `branch_id`
"is the sweep's unit and is unique in the tuple", while `pattern` "is the stable key the branch
RAISES and is deliberately not unique". `branch_id` is therefore what a POPULATION is keyed on —
AC-3(iii)'s floor, the census's branch-row ids, `NoteSpec.discriminator` — and `pattern` is what an
EXCEPTION carries, which is the only thing a `Verdict` of `kind="refusal"` asserts. The two disagree
on real records and the disagreement is silent: `pure_digit` raises `pure_digit_name`
(`name_validation.py:284-285`), and `arrow_connective`, `calendar_prefix` and `me_to_prefix` all
raise the shared `calendar_prefix` (`:216`, `:228`, `:240`). **That non-uniqueness is why a
`Verdict.pattern` cannot be read as naming a branch and is not asked to:** which branch a specimen is
the specimen OF is answered by `shape_classes` (AC-3) or by `discriminator` (AC-1(c)), both keyed on
`branch_id`; `Verdict.pattern` answers only "what does the refusal this specimen produces carry?".

**The WI-226 sweep this rule closes, run over the whole class rather than the instance in front of
it, and DECLARED so the next reader checks it instead of repeating it.** The generator is *a
literal this spec pins that must come from a NAMED FIELD of a NAMED in-tree declaration, where the
declaration carries more than one field of that shape.* Every such pin in this document, swept one
at a time:

1. **`Verdict.pattern`** → `Tier1Branch.pattern`. **The instance: it was pinned from `branch_id` and
   is corrected in §5.3, Task 6 and `## Self-Review Dry Run` in this edit.**
2. **`NoteSpec.discriminator`** → `Tier1Branch.branch_id`. Its two values, `arrow_connective`
   (`:215`) and `path_hostile` (`:250`), are branch ids, and Task 4 asserts membership in the derived
   `branch_id` set rather than trusting the spelling. Correct.
3. **`shape_classes` and the census's class-row ids** → the census's `census-class.id`, which AC-3
   fixes to be the `branch_id` itself for a branch-backed row. The six MEASURED ids of §1.3 rule 2
   include `pure_digit`, which is a `branch_id` and so a correct class id. Correct — **and this is
   exactly why the instance was invisible: the same word is right one field over.**
4. **`SKIPS`'s reason values** → `_skip_reason`'s own return literals (`base.py:44`, `:46`, `:47`),
   imported as constants and pinned once by spelling in Task 2. Correct.
5. **`SKIPS`'s and `LOADABLE`'s keys** → `BaseRepository.type_name`'s returns (`person.py:190`,
   `company.py:68`, `meeting.py:49`, `book.py:48`), never the class names. Correct.
6. **`CONNECTIVE_SET`** → the prefix regexes' own alternatives (P16). Correct.
7. **Task 12's W-1 expected set** → `modules_using_ast`'s return, which is a list of USE records
   whose `.module` is the id (`tests/derivations.py:630`, projected as `{use.module for use in live}`
   by the shipped wall at `tests/test_name_gate_wall.py:1136-1138`). **The NEXT LEVEL of the ladder,
   found by this sweep and closed in the same edit: right declaration, right field, wrong PROJECTION
   of the return.** Task 12 stated the call unprojected and is corrected there.

`RESERVED_ISBN`, §6.4's phone patterns and §1.2's filename grammar are author-declared and draw on no
upstream vocabulary, so they are not members. **The sub-cell the ladder ends at, declared because it
is the one a later reader would re-derive:** a pinned value can be correct and still not identify its
source record, because `pattern` is deliberately non-unique — which is a reason to key populations on
`branch_id` and never a reason to spell a `Verdict` with one.

**`SKIPS` is keyed by repository, never a union.** Ownership is a joint function of the FILENAME and
the error's `declared_type` (§5.4), so the same untyped specimen legitimately appears in two
repositories' mappings at once and in neither of the other two's. A union manifest cannot express
that and cannot go red when a regression moves a skip between owners.

**`LOADABLE` is `len(repo.get_all())`, not the file count and not `load()`'s return.** `load()`
counts FILES that produced an entity (`base.py:230-245`) while `get_all()` returns
`list(self._cache.values())` (`base.py:334-342`), and the cache is keyed by
`_get_cache_key` — `name.lower()` for person and company (`base.py:309-311`), `meeting_id` for
meeting (`meeting.py:56-62`), `title.lower()` for book (`book.py:55-57`). §1.3's three-way name
collision therefore contributes THREE to `load()` and ONE to `get_all()`. This is the single most
likely place a builder declares a number that is off by two, so it is stated here rather than
discovered at build; AC-4(c)'s "declared loadable count" is the `get_all()` quantity.

#### §3.1 The CHECK module's preamble — `tests/test_fixture_vault.py` opens with the interpreter bridge

**This is the single highest-cost thing to get wrong in the whole plan, it is invisible from inside
the floor, and this project already paid for it once.** `tests/test_fixture_vault.py` hosts all five
`kind: test` checks, and every one of them EXECUTES the library: they import `TYPE_TO_MODEL`,
`ENTITY_BODY_CONFIG`, `TIER1_BRANCHES` / `COMPANY_TIER1_BRANCHES`, `parse_markdown_file`,
`write_markdown_file`, all four repositories, `normalize_phone`, `clean_person_name` and the new
`SKIP_REASONS` — every one of them behind `pydantic`. The conveyor does NOT run a check under this
project's interpreter by default: `tests/ac_interpreter.py:7-25` records the mechanism in as many
words — the battery discovers the check by source scan and runs `<some python> -c "<importlib
bootstrap>" <module path> <check name>`, and that interpreter "defaults to the ADVANCER's
`sys.executable` and is only this project's venv when the driver passes `--ac-python`". When it is
not, `import pydantic` fails at the check module's very first package import and every criterion of
the item reports `exit 1: ModuleNotFoundError` — "the exact battery output WI-021's first build
attempt drew, on five-of-five criteria, with a floor that was green in the same tree."

So `tests/test_fixture_vault.py` opens exactly as this project's six other library-executing check
modules do — `tests/test_company_name_contract.py:25`, `tests/test_address_splitter.py:38`,
`tests/test_name_gate_identifiers.py:41`, `tests/test_name_gate_refusals.py:41`,
`tests/test_name_gate_wall.py:40`, `tests/test_name_gate_delta_rule.py:37` — with the bridge as its
FIRST executable statement, ahead of every package import:

```python
"""… module docstring, including the CORPUS_COUPLING: line …"""

# FIRST, ahead of every package import: the conveyor may run this module's check
# under an interpreter that is not this project's, where the imports below cannot
# resolve. A no-op under the floor command and under CI (WI-021; see
# `tests/ac_interpreter.py` for the failure this closes).
from tests.ac_interpreter import ensure_project_interpreter

ensure_project_interpreter(__file__)

import hashlib  # noqa: E402 — everything below runs only once the interpreter is right
…
from obsidian_schemas.models import TYPE_TO_MODEL
from tests.fixture_vault import CORPUS_DIGEST, NOTES, materialize_vault
```

**What the call does, stated precisely, because P-4 asserts this suite makes no subprocess.** It is a
NO-OP whenever the running interpreter can import the package's runtime deps —
`runtime_deps_importable()` is a `find_spec("pydantic")` and returns before anything else happens
(`tests/ac_interpreter.py:123-130`), so under the floor command and under CI the collected module
imports and runs byte-identically to a module with no bridge at all. Only under a FOREIGN interpreter
does it act, and even then it does not spawn a child: it `os.execve`s, REPLACING this process with
the same one check under `<root>/.venv/bin/python` (`:150-155`). It never degrades to a skip or a
green — an unrecognized invocation shape, a missing interpreter, or a delegation that still cannot
import the deps RAISES with the command a human can run by hand (`:136-148`).

**Why nothing else in this item catches its absence, which is the reason it is prescribed here rather
than left to the builder's judgment.** The FLOOR runs under `.venv/bin/python` and stays green with
or without the bridge — that is the split `tests/ac_interpreter.py:30-33` names. The standing wall
over the bridge, `tests/test_ac_interpreter.py`, derives its criterion set from
`docs/write-door-bypasses.md` (`:40`), WI-021's doc, so this item's checks are outside its population
(§11, W-10 states this correctly). And §11's own sweep predicate — modules that READ the text of
files they did not name — structurally cannot reach a capability-injection convention. Task 12
therefore closes it by RUNNING the parity check rather than by asserting the source text (§11, W-16):
for EVERY check name this document's own `criteria` fences declare — derived with
`tests/test_ac_interpreter.py`'s shipped, fence-scoped `criterion_checks` (`:57-73`), never a hand
list — the check is resolved to its module with that module's shipped `check_module` (`:76-87`) and
run in the conveyor's exact shape under `sys.executable -S` with that module's shipped `run_foreign`
(`:90-95`), and must exit 0 AND carry the `[ac_interpreter]` delegation marker on stderr — both
halves of the shipped wall's own oracle (`tests/test_ac_interpreter.py:111-115` and `:116-120`),
because `-S` strips `site` and not an ambient install, so exit 0 alone is green over a child that
imported the project's deps and proved nothing. Three shipped predicates, no re-implementation, and a
sixth criterion
added later joins the sweep on the day it is written. Per-CHECK rather than per-module on purpose:
a missing preamble is a module-scoped failure, but a check that reaches for something the delegated
path lacks is not, and the per-check form is the one that catches both. The cost is six foreign
runs — one per criterion plus the nonexistent-check near-miss that module also ships (`:126-138`) —
which is the shape `tests/test_ac_interpreter.py` already performs on every floor run today
(P-4b).

**The manifest module needs no bridge and must not grow one.** `tests/fixture_vault.py` is not a
check module — no `check:` name resolves to it, and it defines no `test_*` function — so it is never
the target of the conveyor's bootstrap and has no single check to delegate; `ensure_project_interpreter`
would RAISE there under a foreign interpreter rather than help (`:142-148`). It is reached only
through a module that already opened with the bridge, or under the floor.

### §4. The one package change — `SKIP_REASONS` and its binding

In `obsidian_schemas/repositories/base.py`, immediately above `_skip_reason`:

```python
MALFORMED_FRONTMATTER = "malformed-frontmatter"
SCHEMA_DRIFT = "schema-drift"
UNREADABLE = "unreadable"

#: The complete codomain of `_skip_reason` — the classification `SkippedNote.reason`
#: carries. Declared so a consumer can read it instead of re-spelling it (WI-016);
#: bound to the function's own returns by tests/derivations.py:skip_reason_return_values.
SKIP_REASONS = frozenset({MALFORMED_FRONTMATTER, SCHEMA_DRIFT, UNREADABLE})
```

and `_skip_reason` returns those names rather than re-spelled literals. The docstring of
`SkippedNote.reason` (`base.py:37`) keeps its type comment; nothing else in the package changes.

**The export alone is deliberately not trusted.** `TYPE_TO_MODEL` cannot drift because dispatch
depends on it; a `SKIP_REASONS` nothing consumes can. So `tests/derivations.py` gains the FIRST of
its two new scans (the second, `skip_reason_literal_sites`, is below) — and both land there and
nowhere else because `ast` is single-homed to that module by a standing set equality (§11, W-1):

```python
def skip_reason_return_values(path: Path, func_name: str = "_skip_reason") -> set:
    """Every string value `func_name`'s OWN BODY can return, resolved from syntax.

    Two arms, and an unresolvable return is LOUD rather than dropped:
      (1) `return "<literal>"`            — ast.Return of a str ast.Constant
      (2) `return NAME`                   — ast.Return of an ast.Name bound at
                                            MODULE level in this same file to a
                                            str ast.Constant
    Anything else raises AssertionError naming module, function and lineno. An
    under-generating scan that returned silently would be green against the very
    drift this exists to catch (LESSONS #46).
    """
```

It reuses the module's existing plumbing — `_parse` (`:213`), `_iter_functions` (`:217`),
`_own_body_nodes` (`:243`) — exactly as `falsy_returns_in` (`:1366`) and
`parse_frontmatter_exit_sites` (`:543`) already do. It is a new shared derivation but does NOT join
`tests/test_loud_fail_harness.py`'s `six` dict (`:79-87`, with `len(six) == 6` at `:88` and the
homing loop at `:93-97`), which that module's own docstring declares a REQUIRED SUBSET rather than a
cardinality bound (`:18-20`) — checked, not assumed.

AC-4 then asserts `skip_reason_return_values(base.py) == SKIP_REASONS`. **Equality, never
containment** — that is what makes the scan's own silent under-read report RED.

**Every home the vocabulary has, enumerated by GREP rather than by memory, with a ruling on each —
and no count in the heading, because the enumeration is what set Task 11's scope and a count is what
went wrong.** Earlier drafts of this section and of AC-4's `why:` said "a return chain, a type
comment and `tests/test_loud_fail_load.py:187-188`", which is short by two hand-typed test sites. A
grep for the three literals over every `*.py` in this worktree returns exactly these, and the table
rules on each:

| Site | Shape | Disposition |
|---|---|---|
| `obsidian_schemas/repositories/base.py:44`, `:46`, `:47` | the return chain | becomes the three named constants (Task 2). This is the DECLARATION |
| `obsidian_schemas/repositories/base.py:37` | `reason: str  # "malformed-frontmatter" \| "schema-drift" \| "unreadable"` — a `#` comment | kept, unchanged. A comment is invisible to `ast` and to every scan below; it is documentation of the declaration two lines under it |
| `obsidian_schemas/errors.py:112` | a docstring sentence mentioning `_skip_reason`'s `"unreadable"` in running prose | kept, unchanged, and `obsidian_schemas/errors.py` stays on `## Scope Boundary`'s unchanged list. The string constant is the whole docstring, not the member, so it is not a transcription of the vocabulary and no scan matches it |
| `tests/test_loud_fail_load.py:187-188` | `{n.reason for n in repo.skipped_notes} == {"malformed-frontmatter", "schema-drift", "unreadable"}` — the whole codomain, hand-typed | CLOSED by Task 11: reads `SKIP_REASONS` |
| `tests/test_loud_fail_load.py:209` | `[n for n in repo.skipped_notes if n.reason == "unreadable"]` — ONE member, hand-typed, inside the very function Task 11 edits, twenty-two lines below the line it repoints | CLOSED by Task 11: reads `UNREADABLE`. Leaving it would put an unrepointed copy on the same screen as a repointed one and hand the next reader a judgment the spec declined to make |
| `tests/test_name_gate.py:152` | `assert _skip_reason(exc) == "unreadable"` — ONE member, hand-typed, in a module that was not previously a write target | CLOSED by Task 11: reads `UNREADABLE`. `tests/test_name_gate.py` therefore gains a `## Write Targets` fence |

Neither of the two newly-named sites carried a green-over-wrong route — both fail LOUD on a rename —
which is why this is a correction rather than a redesign. It is recorded at this length because the
short enumeration is the document's own recurring family (round 7's "eight of the ten", round 8's
four-item residue, the data audit's P10) landing in the spec-writer's text, and because the SHORT
LIST WAS THE ARGUMENT: §4's solve-in-one-place case and AC-4's `why:` both rested on it.

**So the fold closes the CLASS, not the three instances — the enumeration above can go stale again
and a wall cannot (WI-226).** What GENERATES this family is that a consumer wanting one of these
strings has nothing to import, so it types the string; and after Task 2 it has something to import.
`tests/derivations.py` therefore gains a SECOND scan beside the first:

```python
def skip_reason_literal_sites(files, reasons) -> set:
    """Every file under `files` containing a `str` Constant EQUAL to a member of
    `reasons`, as repo-relative module ids.

    Read off parsed syntax, never source text, for the reason the disposition
    table gives: a text grep cannot tell a declaration from the `#` comment two
    lines above it or from a docstring sentence that merely mentions the word,
    and both of those are legitimate and must stay. `ast` drops comments
    entirely, and a docstring is ONE Constant whose value is the whole docstring
    — so equality against a member matches neither.
    """
```

and AC-4 asserts

```python
skip_reason_literal_sites(python_files_under(PACKAGE_ROOT, TESTS_ROOT), SKIP_REASONS) == {
    "obsidian_schemas/repositories/base.py",   # THE declaration
    "tests/test_fixture_vault.py",             # THE spelling pin, below
}
```

**Set EQUALITY over two named homes, and each home has a stated job.** A fifth site typed anywhere
under `obsidian_schemas/` or `tests/` is RED with the file named, and the remedy is one import. The
universe GROWS with every file this item adds, so `tests/fixture_vault.py` is a member of it — which
is exactly why §3 has that module import the constants rather than re-spell them, and why the
manifest's declared reason VALUES are the constants while WHICH constant a given filename maps to
stays the hand-declared oracle AC-4(a) needs.

**The second home exists because the fold would otherwise DELETE a property, and that is worth
stating rather than discovering.** Today `tests/test_loud_fail_load.py:187-188` is the only thing in
the tree pinning the literal SPELLINGS of the three reasons — `SkippedNote.reason` is a value
consumers read, and a rename from `"schema-drift"` to `"schema_drift"` is a contract break. Repoint
that line at `SKIP_REASONS` and both sides of the comparison move together, so nothing catches the
rename any more; `skip_reason_return_values == SKIP_REASONS` does not either, for the same reason.
So the spellings are pinned ONCE, by hand, in `tests/test_fixture_vault.py`'s Task 2 test —
`SKIP_REASONS == {"malformed-frontmatter", "schema-drift", "unreadable"}` — which is the one place a
rename should have to be a deliberate edit, and it is the second legal home the wall names. Pinning
it there rather than back in `test_loud_fail_load.py` keeps the declaration and its pin in the two
files this item owns.

### §5. Flow — what happens in what order, and every branch

#### §5.1 `materialize_vault(dest)`

```python
def materialize_vault(dest) -> Path:
    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    for src in sorted(CORPUS_ROOT.iterdir()):
        if src.is_file():
            (dest / src.name).write_bytes(src.read_bytes())
    return dest
```

Input: a caller-supplied directory (a `tmp_path`, or `tests/support.temp_dir()` for a zero-argument
AC check). Output: that directory, holding the same flat filename set with the same bytes. No
branch reads, transforms or re-serialises anything: not `shutil.copy2` (which carries mode and
mtime the corpus does not declare), not `read_text`/`write_text` (which would raise on the non-UTF-8
member and would normalise line endings on the others), and never `write_markdown_file`,
`write_frontmatter`, `repo.save()` or `create_stub` — those route through `gate_write`
(`writer.py:252-253`) and are exactly what refuses half the corpus (D-6).

**Idempotent, and it never empties.** A second call against the same `dest` overwrites each corpus
member with identical bytes and leaves everything else in that directory alone — there is no
`rmtree`, no `glob`-and-unlink, no "clean first" branch, and none may be added. AC-1(b) asserts both
halves by calling `materialize_vault` twice with a foreign file planted between the calls (Task 4),
so the rule `## Edge Cases` decides is exercised rather than only written down.

`write_bytes` and `mkdir` are members of `PATH_MUTATION_NAMES` (`tests/derivations.py:50-53`), but
the filesystem-single-homing wall's universe is `python_files_under(PACKAGE_ROOT, SCRIPTS_ROOT)`
(`tests/test_write_routing.py:91`) — `tests/` is out of its scope, so a byte-copy materializer under
`tests/` is legal (P9). Verified, not assumed.

#### §5.2 `corpus_digest(root)`

```python
def corpus_digest(root: Path = CORPUS_ROOT) -> str:
    h = hashlib.sha256()
    for path in sorted((p for p in root.iterdir() if p.is_file()),
                       key=lambda p: p.name):
        h.update(path.name.encode("utf-8"))
        h.update(b"\x00")
        h.update(path.read_bytes())
        h.update(b"\x00")
    return h.hexdigest()
```

The NUL framing is not decoration: without a separator, a rename that moves bytes between the name
and the content field produces the same digest. The walk is the SAME walk `materialize_vault`
performs, which is what lets AC-1(b) assert the digest over the materialized tree equals the digest
over the corpus with no second traversal rule to keep in step.

**The criterion and this code name the SAME key, and they now say so in the same words.** AC-1(a)
reads "corpus-relative POSIX path", which in one flat directory is exactly this `path.name`. That is
the whole of the agreement, and it is stated because the criterion's earlier draft said
"repo-relative": under that reading leg (b) is unsatisfiable — the materialized tree sits under a
caller-supplied temp directory with no repo-relative path — so a builder following the criterion and
a builder following this code would have shipped two different digests. Nothing else about the walk
changes.

#### §5.3 AC-2's round trip, per `TYPE_TO_MODEL` member

For each of the 8 members, against a freshly materialized vault:

1. **(a) Parse.** `parse_markdown_file(dest / filename, TYPE_TO_MODEL[t])` → assert
   `isinstance(doc.entity, TYPE_TO_MODEL[t])`.
2. **(b) Oracle.** Every key of that note's declared `fields` equals the corresponding attribute of
   `doc.entity`. Hand-written values, compared by equality.
3. **(c) Round trip, through the GATED door.** `write_markdown_file(fresh_dir / filename,
   entity=doc.entity)` — which builds the payload with `model_to_frontmatter` (emitting field
   ALIASES, `writer.py:112-117`, so `GiftIdea.for_person` survives as `for`) and calls
   `gate_write(fm, declared_type=fm.get("type"), whole_record=True)` at `writer.py:252-253`. Then
   `parse_markdown_file` the written file and assert its frontmatter MAPPING equals the same
   declared `fields` — never byte-equality against the original, whose fixity is AC-1(a)'s digest.

The subject of (c) is the type's single `roundtrip_representative`, which must be GATE-CLEAN in the
door's own terms: for `person`, no record of `TIER1_BRANCHES` `matches` its stored name
(`name_validation.py:179-184`); for `company`, no record of `COMPANY_TIER1_BRANCHES` does; for the
other six types `gate_write` returns `dict(introduced)` unchanged (`name_gate.py:319-344`) so the
condition is vacuous and nothing is asserted.

**One narrowing, recorded because the data-premise round found it and no criterion states it.** The
person arm passes `allow_phone_sentinel` when `phones` is non-empty and the name is all digits
(`name_gate.py:355-358`), so a digit-named note WITH phones is not refused. AC-2's GATE-CLEAN
predicate — "no record matches" — is therefore strictly stricter than the door for that one case.
It is a conservative over-constraint on a representative that must be clean regardless, so it costs
nothing; the corpus simply must not pick the `pure_digit` specimen as its `person` representative,
which rule 1 of §1.3 already forbids.

**And the same narrowing BITES on AC-3's side, where it decides a declared value rather than merely
over-constraining one — so it is pinned here rather than left to the builder.** The landed census
rules `pure_digit` MEASURED (count 2, specimen `447700900123`), so §1.3 rule 2 obliges a specimen and
Task 6 obliges a declared `Verdict` for it. Which verdict is correct is a function of a field the
corpus author chooses: `allow_phone_sentinel` is `bool(introduced.get("phones")) and
name_text.strip().lstrip("+").isdigit()` (`name_gate.py:355-358`), so a digit-named note that ALSO
declares `phones` is passed by the door and its verdict would be `loads`, not `refusal`. **The
corpus's `pure_digit` specimen declares NO `phones`**, and its manifest `Verdict` is therefore
`kind="refusal"` with `pattern="pure_digit_name"`. That is the profile the census measured — its two
live members are a phone stored as the whole name on a note with nothing else in that field — and it
is the only choice under which the specimen exercises the branch it is the specimen OF. Its stored
`name:` carries the `+` (`+447700900123`), which is the measured profile the census's prose records
and which leg (a) still accepts: the phone span normalizes to `447700900123` and matches
`^447700900\d{3}$` (§6.4) with or without it.

**The `pattern` VALUE is `pure_digit_name` and not `pure_digit`, corrected 2026-09-08 after a review
round drove this literal through the code that raises it — and the correction is recorded rather than
quietly applied, because this is the ONE value the paragraph above tells the builder they are not
free to choose.** Traced end to end: the record at `name_validation.py:283-294` carries
`branch_id="pure_digit"` (`:284`) and `pattern="pure_digit_name"` (`:285`); `_raise_on_tier1` raises
`NameValidationError(branch.pattern, branch.detail(name))` (`:678`), whose `__init__` binds
`self.pattern = pattern` (`:463`); the gate's person arm catches it and re-raises through the single
`_refuse` construction site as `NameGateRefusal(exc.pattern)` (`name_gate.py:365`, site at `:142`).
So the object Task 6 catches carries `.pattern == "pure_digit_name"`, which is what §3's
`Verdict.pattern` field means in as many words ("`kind == "refusal"`: the `NameGateRefusal.pattern`
expected"). The earlier draft pinned `pure_digit`, which is the record's `branch_id`; a builder
trusting it would have authored a wholly correct corpus and reddened Task 6 with the spec against
them, in the one paragraph that removes their judgment. §3 states the general rule this instance is
a member of, and the sweep that closed the class is there too.

**The narrowing arm.** The types with no body config are read at test time as
`set(TYPE_TO_MODEL) - set(ENTITY_BODY_CONFIG)` — `{watch, explore, gift-idea}` today, asserted to
have exactly 3 members — and for exactly those the assertion is `get_default_body(t) == ""`
(`body_sections.py:337-338`), the declared marker. For each member of the intersection the assertion
is that config's declared `sections`.

**Repository-less types.** `watch`, `explore`, `gift-idea` and `exploration` have no repository and
no glob, so all three legs are parser-level for them and they are outside AC-4 entirely.
`exploration` is the one with zero test references in the tree today (D-2); its fixture is the first
anyone has authored, and its `related:` list is an identity position (§6.2).

#### §5.4 AC-4's skip surface, per repository

The repository set is derived: iterate the names `obsidian_schemas/repositories/__init__.py`
exports (`__all__`, `:14-21`), keep those that are concrete `BaseRepository` subclasses — which
FILTERS OUT `VaultPathNotConfiguredError` at `:16`, an exception rather than a repository — and
assert the result is non-empty and of size exactly 4. Never
`BaseRepository.__subclasses__()`, whose answer depends on import order. Each is then instantiated
against the materialized vault, because `type_name` is an abstract `@property`
(`base.py:189-193`) readable off an INSTANCE, and `SKIPS`'s key set is compared to
`{repo.type_name for repo in repos}`.

Ownership, which the manifest declares and the test asserts, is the code's actual behaviour
(`base.py:258-275`, re-read here):

| Specimen | person `@*.md` | company `@*.md` | meeting `Meeting *.md` | book `*.md` |
|---|---|---|---|---|
| malformed frontmatter, filename `@X.md` (`declared_type` always `None`, `errors.py:65-67`) | OWNED | OWNED | glob misses | `_owns(None)` False — catch-all stem is `*` |
| non-UTF-8, filename `@X.md` (`UnicodeDecodeError` carries no `declared_type`) | OWNED | OWNED | glob misses | False |
| malformed frontmatter, filename `Meeting D - T.md` | glob misses | glob misses | OWNED | False |
| `schema-drift`, `type: person` (`declared_type` present, `errors.py:70-71`) | OWNED | not ours | glob misses | not ours |

Three legs: **(a)** `{note.path.name: note.reason for note in repo.skipped_notes}` equals that
repository's declared mapping, both directions, per repository; **(b)** the planted discriminators —
an untyped specimen under each of the two OWNING globs, and book's declared mapping over the untyped
classes asserted EMPTY, which is the only assertion anywhere that the catch-all glob declines
ownership by design; **(c)** `len(repo.get_all())` equals `LOADABLE[type_name]` and every
`RESOLVABLE` pair resolves through `PersonRepository.resolve`.

#### §5.5 AC-3's census read

Read `docs/vault-shape-census.md` from disk (`REPO_ROOT / "docs" / "vault-shape-census.md"`,
derived from `Path(__file__)`, never from cwd). Assert `sha256` over its bytes equals the
`CENSUS_DIGEST` value declared inside the AC-3 `criteria` fence of `docs/vault-fixtures.md` — read
FENCE-SCOPED, asserting exactly one such declaration inside that fence and that it is well-formed
64-character lowercase hex. Then parse the three fence kinds of §2 and run assertions (i), (ii) and
(iii). Assertion (iii)'s branch half is `{record.branch_id for record in
TIER1_BRANCHES + COMPANY_TIER1_BRANCHES}`, asserted non-empty and of size exactly 10, in BOTH
directions against the branch-shaped census rows.

**Assertion (i)'s MANIFEST side is exactly `{c for spec in NOTES.values() for c in
spec.shape_classes}` and nothing else.** It is a union over a DECLARED field, so a note with
`shape_classes = ()` contributes nothing and is outside the equality in both directions — which is
what lets the corpus carry mandatory members that are the specimen of no class: the eight type
representatives, the skip specimens, and §1.3 rule 7's two AC-1(c) discriminators, whose branches the
landed census rules ABSENT. `NoteSpec.discriminator` is NOT read here and must not be: it names a
branch, not a census class, and folding it into this set would put an ABSENT id on the MEASURED side
and redden a wholly correct corpus. Against the landed census the equality's expected value is the
six MEASURED ids named in §1.3 rule 2.

The fixity assertion runs FIRST, before any row of either table is trusted. AC-5's check re-asserts
it independently rather than inheriting it, because each `check:` is its own test function invoked
directly by the battery (`tests/support.py:1-19`) and there is no shared setup between them.

### §6. The identity-token extractor and the position split (AC-5)

#### §6.1 The extractor

Reach: every file under `tests/fixtures/vault/` plus `tests/fixture_vault.py`. Decode each with
`errors="replace"`. A **run** is a maximal contiguous span over {Unicode letters, combining marks,
`'`, `-`}, bounded only by a character outside that class and never restarted at an internal
capital. A run is **extracted** iff its FIRST character is an uppercase or non-ASCII letter, and an
extracted run has leading and trailing `'` and `-` trimmed before comparison.

```python
def _runs(text):
    cur = []
    for ch in text:
        if ch in "'-" or unicodedata.category(ch)[0] in ("L", "M"):
            cur.append(ch)
        else:
            if cur:
                yield "".join(cur)
                cur = []
    if cur:
        yield "".join(cur)

def identity_tokens(text):
    out = set()
    for run in _runs(text):
        first = run[0]
        if first.isupper() or ord(first) > 127:
            trimmed = run.strip("'-")
            if trimmed:
                out.add(trimmed)
    return out
```

The four worked consequences AC-5(b) states hold under this code and are the extractor's own shape
battery (Task 9): `McDonald` is one token; `d'Angelo` yields none; `Zeta-9` yields `Zeta`;
`zArchived` and `zzArchived` yield nothing. A fifth consequence the criterion does not state and the
code decides, recorded here so the builder does not decide it twice: **the first character is read
BEFORE trimming**, so a run beginning with `'` or `-` — `-Voxleaf` with no separating space — yields
no token. That is safe and not a new hole: in a YAML sequence the `- ` marker is followed by a
space, which ends the run, so `  - Johnny` yields `Johnny`; a leading hyphen fused to a name is a
shape no corpus note carries and the census's pool review is what covers the residue, exactly as it
covers the all-lowercase dodge AC-5's `why:` already names.

#### §6.2 The position split

**IDENTITY positions** — three sources, unioned:

1. Every corpus filename stem, normalised per §1.2.
2. For each note, the manifest's declared values for that note's type's identity fields, read from
   `IDENTITY_FIELDS`. Scalars contribute their own text; list fields contribute each element;
   a wikilink contributes the text inside `[[…]]`. `IDENTITY_FIELDS` is the field-by-field answer
   AC-5(b) enumerates and P14 records — hand-declared, because `models.py` declares FIELDS and
   nothing in it declares which of them hold a person's or an organisation's name.
3. Every value in every note's `undeclared` mapping — clause 3's `extra="allow"` default
   (`models.py:31-32`), with no manifest flag to opt out.

**FREE-PROSE positions** — everything else in reach: note bodies, non-identity frontmatter values,
and `fixture_vault.py`'s own source, docstring and comments.

Implementation: `all_tokens = identity_tokens(every byte in reach)`;
`id_tokens = identity_tokens(the concatenation of the three identity sources)`;
`prose_tokens = all_tokens - id_tokens`.

Assertions:

- `id_tokens ⊆ NAME_POOL ∪ CONNECTIVE_SET ∪ {t for t in id_tokens if t.lower() in _GENERIC_ORG_SUFFIXES}`.
- `prose_tokens ⊆ NAME_POOL ∪ CONNECTIVE_SET ∪ PROSE_ALLOWLIST`.
- `PROSE_ALLOWLIST` is DISJOINT from `id_tokens`. This is what makes adding a surname to the
  allowlist buy nothing for a `name:` value, an alias, a title field or a filename stem.
- `CONNECTIVE_SET == frozenset({"Me", "My", "Dave"})` — the literal written into AC-5(b), so the set
  cannot grow without an AC change.
- Every `NAME_POOL` entry occurs as an extracted token in at least one IDENTITY position.
  `NAME_POOL` only; `CONNECTIVE_SET` carries no such obligation and that absence is the round-4 fix.

The org-suffix admission is READ from `obsidian_schemas.name_cleaning._GENERIC_ORG_SUFFIXES`
(`:58`) and compared with `str.lower()` — the operation the package itself performs at `:148`,
`:185` and `:191`, never `str.casefold()`.

The non-UTF-8 member is EXEMPT from the token scan and instead has its complete bytes declared in
`NoteSpec.raw_bytes_hex` as a LOWERCASE hex literal and asserted byte-equal — reviewed rather than
skipped past the wall, and lowercase so the literal itself yields no extracted token.

**THE GRANULARITY OF A POOL ROW IS THE EXTRACTOR'S, NOT A READER'S — stated here because §6.3's
containment is unsatisfiable if the two artifacts disagree about what a token is.** `identity_tokens`
never splits a run at an internal hyphen or an internal capital, so a hyphen-fused pair is ONE token:
`Anne-Sophie Legrain` yields `{Anne-Sophie, Legrain}`, and Task 9's shape battery asserts exactly
that. A specimen carrying such a pair therefore needs the COMPOUND certified in the census's pool
table; certifying `Anne` and `Sophie` separately certifies two tokens the extractor never produces
and leaves the one it does produce uncertified. Two of the landed census's six MEASURED specimens
carry this profile by construction — `hyphenated_surname`'s `Oskaline Brenvik-Tarnquil` and
`postal_address_in_name`'s `25 Corvallen Ravensby-3rd Pellworth-Wexlund 8`, whose extracted tokens are
`{Oskaline, Brenvik-Tarnquil}` and `{Corvallen, Ravensby, Pellworth-Wexlund}` respectively (the `-`
before `3rd` is trimmed and `rd` begins lowercase, so it yields nothing) — and dropping the hyphen
would destroy the character profile each specimen exists to carry, so the compound row is the only
available arm. The landed artifact certifies both compounds alongside their halves; `## Write
Targets`'s extension states the rule for every later census pass, and M2's abort gate (§6.5, Task 3)
is what enforces it before a single corpus byte is authored.

#### §6.3 Pool provenance (leg c)

`NAME_POOL ⊆ {row.token for row in census pool rows}` — a CONTAINMENT, one direction. Every pool row
carries a non-empty `command` and non-empty `stdout`. The pool table's token set is DISJOINT from
`CONNECTIVE_SET`. And census fixity is asserted here too, before any row is trusted (§5.5).

#### §6.4 Reserved ranges (leg a), and the one thing the criterion's field list makes ambiguous

The scan is over ALL bytes in reach rather than a field list, so it needs no enumeration to be
total — precisely, over `excise(text, DECLARED_HEX_LITERALS)` for each file in reach, the excision
being the named, author-declared exemption argued three paragraphs down. **Two domains, and they are
different on purpose (AC-5(a)):** the EXCISION is per file — applied to every file's text whether or
not that file contains the literal, an excision of an absent substring being a no-op — while the
PRESENCE assertion that keeps the exemption honest is over the REACH, asserted once against the union
of every scanned file's bytes. Per-file presence would be RED on the ~50 corpus notes, none of which
carries `CORPUS_DIGEST` or a `raw_bytes_hex`.

- **Email-shaped:** `[\w.+-]+@[\w.-]+\.\w+`. Its domain must be `example.com`, `example.net` or
  `example.org`, or carry a `.test` / `.invalid` / `.example` TLD (RFC 2606 / RFC 6761).
- **URL-shaped:** `https?://[^\s"'<>)]+`. Its HOST must satisfy the same reserved rule. That is the
  concrete reading of AC-5(a)'s "a declared placeholder form": the declared form IS "host under a
  reserved name", which reuses one rule instead of minting a second and cannot be padded.
- **Phone-shaped:** a maximal contiguous span over `[0-9+()\-. ]` whose digit count is ≥ 9. Its
  `normalize_phone` value (`phone_normalization.py:39-55`) must match ONE OF THREE patterns —
  `^447700900\d{3}$` or `^07700900\d{3}$` (the UK Ofcom drama range `+44 7700 900000-900999`, in its
  international and its national spelling; `normalize_phone` strips every non-digit, so the `+` is
  gone and the national form keeps its leading `0`) or `^1?\d{3}55501\d{2}$` (NANP `555-01xx`, with
  the optional country code). **Both UK spellings are admitted because they are ONE range, and the
  block is pinned to `900xxx` exactly rather than to `90xxxx`:** a stored `07700 900456` is the
  ordinary national spelling of a drama number and would be RED under an international-only rule
  while being exactly as unreachable, and a `\d{4}` tail would have quietly admitted
  `+44 7700 901234`, which is a live allocatable number and not reserved at all. Task 9 drives all
  four accepted spellings and that near-miss through this predicate.

**Each of the three is ONE named function in `tests/test_fixture_vault.py`, and that is a WI-235
requirement rather than a style note.** `reserved_email_violations(text)`,
`reserved_url_violations(text)` and `reserved_phone_violations(text)` each take a string and return
the offending tokens; leg (a) calls exactly these three over `excise(text, DECLARED_HEX_LITERALS)`
for every file in reach, and Task 9 drives its planted battery through the SAME three objects — never
a re-implementation, never a regex re-typed into the fixture test. A fixture battery driving a
private copy of the predicate proves the copy, which is the failure WI-235 exists to name.

**The ISBN, decided here because leg (a) names `Book.isbn` (`models.py:165`) among the fields that
carry these shapes and an ISBN-13 is a 13-digit run that the phone predicate matches.** An ISBN is
not a phone and has no reserved range to move into. So the corpus carries exactly ONE ISBN value,
declared as `RESERVED_ISBN` in `fixture_vault.py`, and a phone-shaped run whose text equals that
literal is asserted EQUAL to it and is not scored as a phone. It is a one-member author-declared
literal, asserted by equality rather than membership, so it cannot be padded and it imposes no
obligation over anything the builder does not author — the exemption is not a reappearance of the
generator round 4 removed. The corpus's `date:`, `created:` and `Meeting <YYYYMMDD>` values are
8-digit runs and are below the threshold by construction; a `.md` file with any other ≥9-digit run
is RED, which is the property.

**The manifest's own hex literals, decided in the same place and by the same rule — and this is the
second instance of the ISBN's class, not a new question.** The reach is the corpus PLUS
`tests/fixture_vault.py`, and §3 puts two hex literals in that module on purpose: `CORPUS_DIGEST`,
and `NoteSpec.raw_bytes_hex` for the one non-UTF-8 member, whose COMPLETE bytes §6.2 requires to be
declared there in lowercase hex and asserted byte-equal. Hex is not phone-safe: printable ASCII
encodes to bytes whose first nibble is `2`–`7`, always a digit, and `a`–`f` are the only characters
that break a digit span — so `type:` alone encodes to `747970653a`, giving the nine-digit run
`747970653`, which `normalize_phone` maps to neither reserved pattern. Leg (a) would therefore be RED
on a corpus that is entirely correct, and a re-taken `CORPUS_DIGEST` could redden it again at random
(a 64-character sha256 hex string carries a ≥9-digit run roughly a third of the time). **The
decision:** before the span walk, the scan EXCISES the manifest's declared hex literals from the text
— `CORPUS_DIGEST`, every non-`None` `raw_bytes_hex`, and the optional `CENSUS_DIGEST` restatement
AC-3(iv) permits — each asserted first to be well-formed lowercase hex of even length (64 for either
digest) and asserted to occur SOMEWHERE IN THE REACH, once against the union of every scanned file's
bytes rather than once per file. Named literals, asserted by equality,
authored by the builder: the same three properties that keep `RESERVED_ISBN` from being a padding
surface, and the reason neither exemption is the generator round 4 removed. Concretely, the leg
scans `excise(text, DECLARED_HEX_LITERALS)` rather than `text`, where
`DECLARED_HEX_LITERALS = {CORPUS_DIGEST} | {s.raw_bytes_hex for s in NOTES.values() if s.raw_bytes_hex}`
plus the restatement when it exists. Legs (b) and (e) scan the UNEXCISED text: a lowercase hex
literal yields no extracted token and contains no absolute path, so neither needs the exemption and
neither gets it.

**Leg (d), the cost check.** For every reserved phone in the corpus, `normalize_phone` still yields
the digits-only value (`+44 7700 900123` → `447700900123`; the package emits E.164 nowhere and none
is asserted), and `phones_match` (`:58-90`) still matches it against the number's `0`-prefixed and
`+44`-prefixed variants. **Leg (e), hermeticity.** `materialize_vault` writes only underneath the
caller's `dest`; no file in reach contains `/Users/` or any absolute filesystem path.

#### §6.5 The census's own bytes are inside the wall — the 2026-09-08 threat model's M1 and M2

The threat model found the one place nineteen gate rounds of enumeration review never pointed the
wall: **the wall's own REACH.** AC-5's declared reach is `tests/fixtures/vault/` plus
`tests/fixture_vault.py`; `docs/vault-shape-census.md` is neither, §2 puts its prose outside the
suite's parser, `## Write Targets`'s constructed-token charge is scoped by its own words to the
specimen and pool columns, and the tree has no repo-wide markdown scan over `docs/` at all
(`tests/test_vault_path_required.py:387` excludes it by name). The conductor wrote two real
live-vault values into the one part of the artifact the spec left uncharged, exactly as the spec
permitted — and AC-3(iv) and AC-5(c) would then have asserted those bytes IMMUTABLE. The instance is
closed (the conductor re-authored the prose against the constructed specimens already beside it, and
AC-3(iv)'s digest was re-taken); what follows closes the CLASS, so the next census refresh cannot
reopen it with nothing to notice.

**M1 — the standing assertion (Task 8).** *AC-5's check additionally scans the WHOLE of
`docs/vault-shape-census.md` — its prose as well as its fence rows — with §6.1's `identity_tokens`,
and asserts every token it yields is in that artifact's own certified pool table, in
`CONNECTIVE_SET`, or admitted by `str.lower() in _GENERIC_ORG_SUFFIXES`, with the residue in a
declared `CENSUS_PROSE_ALLOWLIST` frozenset asserted DISJOINT from the pool table, so the artifact
the privacy wall depends on is itself inside the wall.*

Six things about that sentence, each decided here rather than at build time:

1. **The subject is the file's WHOLE bytes**, decoded once with `errors="replace"` exactly as §6.1
   decodes the corpus — prose bullets, the Method section, the `lint_vault` table and every fence
   alike. There is no position split here and none is wanted: the census has no field whose value is
   declared prose, so every extracted token faces the same four buckets.
2. **The four admissions are the artifact's OWN pool table, `CONNECTIVE_SET`, the derived org-suffix
   set, and `CENSUS_PROSE_ALLOWLIST`** — the first three exactly as §6.2 admits them for the corpus's
   identity positions, so no new admission rule is minted. The pool table is read from the same
   parsed `census-pool` rows §6.3 reads; `CONNECTIVE_SET` is the frozen `{"Me", "My", "Dave"}`, which
   is why the `whitespace_damage` specimen's `Dave` and the Method section's `Dave` both pass.
3. **`CENSUS_PROSE_ALLOWLIST` lives in `tests/test_fixture_vault.py`, NOT in the manifest**, and the
   placement is load-bearing rather than tidy: AC-5(b) is signed text and says `fixture_vault.py`
   "declares THREE literal frozensets and no computed membership", naming them. A fourth frozenset
   there would make a signed sentence false. It is also the honest home — the set is the census's
   ordinary technical vocabulary (`MEASURED`, `ABSENT`, `Ofcom`, `Unicode`, `Templates`, `Python`,
   `LIVE`, the `WI`/`AC` prose, the `TIER1_BRANCHES`-style symbol names the Method section cites),
   which is a property of the ARTIFACT the check reads and not of the corpus the manifest declares.
   **ITS MEMBERSHIP IS AUTHORED AGAINST THE LANDED ARTIFACT AND NOT AGAINST THE LIST ABOVE, and that
   is a rule rather than a caveat:** the set is exactly the RESIDUE Task 8's scan returns over
   `docs/vault-shape-census.md` AS IT STANDS — every token `identity_tokens` yields that is not a
   pool row, not a `CONNECTIVE_SET` member and not an admitted org suffix — so the builder reads the
   list above as an EXAMPLE of the kind and the artifact as the source of the members. The landed
   census already needs at least two the list does not name, both in one Method bullet at
   `docs/vault-shape-census.md:17` (`DaveRemoteVault`, the vault folder's name, and `Obsidian`), and
   a builder treating the list as a specification hits them at Task 8 and cannot tell an omission
   from a leak. Nothing else moves with this clause: the four admissions are unchanged and the
   DISJOINTNESS assertion of item 4 is what keeps the residue honest whatever it turns out to hold —
   an uncertified token the builder cannot recognise as technical vocabulary is M2's abort at Task 3
   and a conductor pass, never a member added to make a red go away.
4. **The disjointness assertion is what stops it becoming the bypass** `PROSE_ALLOWLIST` was found to
   be at round 2: `CENSUS_PROSE_ALLOWLIST ∩ {row.token for row in census pool rows} == ∅`, so no token
   can hold both roles, and a name cannot be quietly moved from the certified table into the
   allowlist. It is not a claim that a real name CANNOT be typed into the allowlist — it is the same
   bar AC-5(b) sets for the corpus: a real name can only arrive by someone deliberately typing it
   into a declared set that a human reviews, never by transcription.
5. **The scan does NOT extend leg (e)'s no-absolute-path rule to this file**, and that is the threat
   model's own ruling routed against rather than an omission: it recorded the Method section's vault
   path as a NON-blocking note, on the ground that it names no person and is what makes every command
   re-runnable. (The conductor's re-author removed it anyway, and the census now says so at its own
   Method bullet; nothing here asserts either way.)
6. **The coupling is declared, not implied (WI-278).** This is a third property consumed from
   `docs/vault-shape-census.md` by `tests/test_fixture_vault.py`, and the file is pinned by DIGEST —
   AC-3(iv)'s fixity assertion runs first, before any of these tokens is trusted, exactly as it does
   for the class and pool tables. The module's `CORPUS_COUPLING:` line names it; `## Verification`
   carries the same sentence.

**M2 — the early half (Task 3).** *The Implementation Plan's precondition abort gate additionally
REFUSES, before any corpus byte is authored, when running §6.1's `identity_tokens` over
`docs/vault-shape-census.md` yields a token that the artifact's own pool table does not certify and
that is neither a `CONNECTIVE_SET` member nor an admitted `_GENERIC_ORG_SUFFIXES` member.*

The gate is the same predicate one build phase earlier, run by the builder as an inspection and
recorded in the Build Log, and it catches TWO distinct leaks with one read — which is why the threat
model asked for it and why the spec-review round's third finding folds into it rather than beside it:

- **A leaking census** (M1's subject): a real live-vault value in a prose bullet or a specimen column
  is an uncertified token, so the gate stops the build at Task 3 instead of at Task 8, before ~50
  notes have been authored against an artifact that will have to be re-authored anyway.
- **A census whose pool table is certified at the WRONG GRANULARITY** (§6.2's compound-token rule):
  a specimen carrying `Brenvik-Tarnquil` whose table certifies only `Brenvik` and `Tarnquil` yields
  an uncertified compound under `identity_tokens`, which the gate names. Without the gate that
  divergence surfaces at Task 8 as a RED leg over a wholly correct corpus, with every authorised
  remedy closed — the census is unwritable by the builder (`## Scope Boundary`), digested by two
  signed criteria, and the specimen's hyphen is the profile it exists to carry.

The gate's output is a REFUSAL and never a repair: the builder does not author, amend or normalise a
byte of the census, does not add a pool row, and does not drop the hyphen. It STOPS under the Abort
Protocol with the offending tokens named in the Build Log, and the remedy is a conductor pass — one
census edit, one re-taken digest, one AC-3(iv) edit, one D4b re-sign. That cost is the reason the
gate exists at Task 3 rather than the reason to skip it.

### §7. Integration points

| Surface | Today | After | Who reads it |
|---|---|---|---|
| `obsidian_schemas/repositories/base.py` | three bare return literals, no declaration (D-5) | `SKIP_REASONS` + three named constants; `_skip_reason` returns them by name | AC-4; `tests/fixture_vault.py`'s `SKIPS`; and the three sites Task 11 repoints — `tests/test_loud_fail_load.py:187-188`, `:209`, `tests/test_name_gate.py:152` (§4's disposition table). The `#` type comment at `:37` and `errors.py:112`'s prose stay as they are |
| `tests/derivations.py` | 14+ shared scans, `ast` single-homed (`:14-17`, `:24`) | TWO more scans — `skip_reason_return_values` (binding) and `skip_reason_literal_sites` (the class-closing wall, §4) | AC-4 |
| `tests/test_loud_fail_load.py`, `tests/test_name_gate.py` | three hand-typed spellings of `_skip_reason`'s codomain | all three import the declared constants | the floor; and §4's wall, which is RED if any is left |
| `docs/vault-shape-census.md` | the conductor's landed precondition (2026-09-07, prose re-authored 2026-09-08) | UNCHANGED — READ, never written, by this build (`## Scope Boundary`) | `tests/test_fixture_vault.py`: the digest (AC-3(iv), AC-5(c)), the `census-class` and `census-pool` fences (AC-3, AC-5(c)), and — NEW, M1 — the whole file's bytes through `identity_tokens` (§6.5). Three properties, one file, one digest |
| `tests/fixtures/vault/` | does not exist (D-1) | the corpus | `tests/fixture_vault.py` only |
| `tests/fixture_vault.py` | does not exist | manifest + digest + materializer; imports the three reason constants | the five checks, and every later test that wants a vault |
| `tests/ac_interpreter.py` | the shipped interpreter bridge, used by six check modules (`:123`) | UNCHANGED — this item is its seventh caller | `tests/test_fixture_vault.py`'s first statement (§3.1) |
| `tests/test_ac_interpreter.py` | WI-021's battery-parity wall, scoped to `docs/write-door-bypasses.md` (`:40`) | UNCHANGED — its `criterion_checks` (`:57-73`), `check_module` (`:76-87`) and `run_foreign` (`:90-95`) are IMPORTED and driven over this item's own `criteria` fences | Task 12's parity run (§11, W-16) |
| `tests/test_fixture_vault.py` | does not exist | the five checks + four batteries, opening with the interpreter bridge | the conveyor's AC battery, and the floor |
| `tests/test_parser.py`, `tests/test_writer.py`, `tests/test_repositories.py` | a private vault helper per file, thirteen files, no shared corpus (D-1) | three of them gain a corpus-backed top-level test; two lose an inline heredoc | the floor |

**Nothing outside this repository changes.** `pyproject.toml:38-39` packages `obsidian_schemas`
only, so `tests/fixture_vault.py` is not importable by HAL9000, Exocortex or orchestrator even after
this ships (P8) — which is D6's measured deferral, not a regression. The one package change is
purely additive: four new module-level names (`MALFORMED_FRONTMATTER`, `SCHEMA_DRIFT`, `UNREADABLE`,
`SKIP_REASONS`), no signature change, and no behaviour change — `_skip_reason` returns the same three
strings by a different spelling of the same values — so the three consumers' `-e` installs pick up
constants nobody yet calls.

### §8. Configuration

There is none. No env var, no toggle, no threshold, no default to pick. The two constants that exist
are both frozen values with declared homes and no valid range: `CORPUS_DIGEST` in
`tests/fixture_vault.py` (regenerated by the recipe in that module's docstring, a deliberate speed
bump), and the `CENSUS_DIGEST` value inside AC-3(iv)'s `criteria` fence — which the BUILD never
writes, because a constant the build owns is updated in the same commit that edits the file it
digests.

### §9. Named exclusions and narrowed quantifiers

**§9.1 D5's proof set, scoped at spec time — and this NARROWS D5's literal wording, so it is flagged
rather than folded in silently.** D5 says the item "migrates a named proof set (the three
`^type:`-literal files) to demonstrate the surface is usable". Read against the files, "migrate
`tests/test_repositories.py`" means repointing the `temp_vault` fixture (`:15-263`, twelve of the
file's fifteen `^type:` literals), on whose exact names, emails, phone and company values the
remaining ~1,950 lines of that file assert directly. A mechanical repoint loses precisely the
properties nobody wrote a comment about — which is the WI-131 shape D5 exists to prevent, reproduced
by D5's own instruction. So the proof set is scoped to what actually proves usability:

- `tests/test_parser.py` — `TestParseMarkdownFile.test_parse_file` (`:213-241`) is DELETED and
  replaced by top-level `test_corpus_person_note_parses_to_its_declared_values`.
- `tests/test_writer.py` — `TestRoundtrip.test_roundtrip_preserves_data` (`:296-…`) is DELETED and
  replaced by top-level `test_corpus_note_round_trips_through_the_write_door`.
- `tests/test_repositories.py` — ADDITIVE only: top-level
  `test_corpus_vault_loads_through_every_repository`. `temp_vault` is untouched.

Cost of the narrowing, stated so it can be weighed: `test_repositories.py` keeps its twelve inline
literals and the duplication P3 measures shrinks by two rather than by fifteen. What is bought is
that no assertion in the largest test file in the suite is rewritten against different data in the
same build that introduces the data. D5's "the rest migrate when their own tests are next touched"
covers the remainder and is unchanged.

**§9.2 Out of AC-4 by construction.** `watch`, `explore`, `gift-idea` and `exploration` have no
repository, so they appear in no `SKIPS` mapping and in no `LOADABLE` entry. That FOLLOWS from the
two derivations rather than being separately asserted.

**§9.3 The company Tier-1 arm is out of this corpus's scope, affirmatively.** Five `branch_id`s
appear in both tables, but a deduped floor writes one census row per `branch_id` and the corpus
carries one specimen, whose DECLARED TYPE decides which table `gate_write` consults
(`name_gate.py:329-343` vs `:361-363`). A person-typed `path_hostile` specimen exercises the person
arm only. That is not a coverage hole: the company table has its own in-tree refusal sweep over
every record's `specimen` and `negative_specimen` (`tests/test_company_name_contract.py:359-459`),
which this item does not duplicate.

**§9.4 `empty` will plausibly discharge ABSENT.** `create_stub` guards its validator call with
`if name and name.strip():` (`repositories/person.py:1327`), so the branch has never fired in
production. An `ABSENT` row with count `0` satisfies assertion (iii), never enters assertion (i)'s
equality, and obliges no specimen. Writing the zero row is always right and never the cause of a
failure.

**§9.5 The extractor's domain, and the places the machine stops.** An identity value written
entirely in lowercase yields no token and is outside the wall; a real name written into
`Exploration.origin`, `Meeting.topics` or a note body is walled by the free-prose leg and the pool's
one-time human review, not by the closure. Both are named in AC-5's `why:` and neither is closed by
a further clause, deliberately. **M1 adds a third of the same kind and it is stated here with them
rather than claimed away:** a name typed deliberately into `CENSUS_PROSE_ALLOWLIST` passes the census
scan, exactly as a name typed deliberately into `NAME_POOL` and the census's pool table passes the
corpus scan. The disjointness assertion stops the allowlist being used to launder a token that is
also a certified pool row, and nothing stops someone typing a real name into a declared set that a
human reads — which is the bar AC-5(b) has set since round 2 and the most a hermetic suite can assert
about a value it cannot check against a vault it cannot read. What M1 removes is the case that needed
no deliberation at all: transcription into prose nobody was scanning.

### §10. Prerequisites & Assumptions

**P-1 — `docs/vault-shape-census.md` is in git HEAD before the builder is armed.** It is the
declared `kind: precondition`; the WI-156 driver probe tests the path for membership in HEAD (never
its CONTENT) immediately before the spawn and refuses the drive if it is absent. Its content is a
conductor act the cage cannot perform: the suite is hermetic and no caged builder can read the live
vault.

**P-2 — the one-time pre-origination edit HAS HAPPENED, and the window it opened is CLOSED. Written
in the past tense as of 2026-09-08, because every sentence of this prerequisite that still reads as
an instruction is a sentence a later gate would price as free when it is not.** Dave signed on
2026-09-08 (`## AC Sign-off`, `signed_at: 2026-09-08T01:14:48+01:00`). The three things the edit
settled, each recorded with its outcome rather than as a pending act:

- **(a) AC-3(iv)'s `CENSUS_DIGEST` was filled** with the `sha256` of the landed census's bytes. The
  placeholder is gone and no origination waited on it.
- **(b) AC-3's SIX hand-listed shape classes were reconciled** against the census's own naming, and
  AC-3 records the result in place: `diacritics`, `hyphenated_surname`, `whitespace_damage`,
  `stem_name_divergence`, `same_name_collision`, `postal_address_in_name`, with the ONE-or-TWO
  ruling settled as TWO (collision ABSENT, divergence MEASURED).
- **(c) AC-5(b)'s `CONNECTIVE_SET` was reconciled** against the census's measured character profiles.
  The artifact measures the lowercase `unknown contact` suffix form and no capitalized standalone
  one, and no `ME -` / `DAVE -` variant anywhere, so **the set stays exactly `{"Me", "My", "Dave"}`**
  and `Unknown` / `Contact` were NOT added. The question that had been open since round 6 is answered
  by the artifact rather than by a guess.

**Architect round 10's note 2 rode along and the ride EXPIRED rather than being taken, which is
recorded rather than left to be rediscovered.** That note observes that AC-4's "`_skip_reason`
returns them BY NAME rather than as re-spelled literals" is prose the first arm of
`skip_reason_return_values` cannot discriminate, since that scan resolves a module-level `str` Name
and a bare literal to the same value. The note was routed to this one-time edit; the edit is past, and
the clause was not added. **It stays NON-BLOCKING and is re-deferred deliberately:** §4 and Task 2
prescribe the by-name form explicitly, no safety property depends on the spelling, and the wall that
matters — `skip_reason_literal_sites`, W-15's set equality over the vocabulary's legal homes — is
unaffected either way, because `base.py` is a declared home under both spellings. Closing it now
would be a D4b re-sign bought for a clause with no red behind it.

**What the window's closure means for every OTHER correction, and it is the fact findings 2 and 3 of
the 2026-09-08 spec review turn on.** A criterion correction is no longer a word in a draft: it
invalidates the `ac-signoff` hash (D4b) and costs a re-sign and a second interruption of Dave. So a
defect found after this point is fixed in `## Design`, `## Implementation Plan` or `## Write Targets`
wherever that is possible, and escalated to Dave only when it genuinely is not. §1.3 rule 7 and §3's
`NoteSpec.discriminator` are exactly that move: AC-1(c) and AC-3(i) were reconciled by giving them two
manifest fields rather than by editing either criterion.

**One correction WAS made inside the signed span after signature, and the single re-sign it owes is
named here so it is not discovered by a linter.** The threat model's M1 remediation and the spec
review's compound-token finding both required conductor edits to `docs/vault-shape-census.md`; both
landed in one census pass, one digest was re-taken over the corrected bytes, and AC-3(iv)'s declared
`CENSUS_DIGEST` moved with it (from the `585d639` value frozen in
`docs/spec-reviews/WI-016-dave-review-2026-09-08.md` to the value AC-3(iv) now carries). That edit is
the reason `## Acceptance Criteria`'s frozen-preamble correction was taken in the same breath rather
than deferred: **the span is already dirty and owes exactly ONE re-sign**, which covers the AC-3(iv)
digest, the preamble's now-false "Not yet frozen" sentence, and nothing else — no AC's promise,
actor, scope, oracle or exception has moved, which is what a Check 12 diff classification will find.
No further edit inside `## Intent` or `## Acceptance Criteria` is authorised by this spec.

**As of 2026-09-08 that re-sign is still UNTAKEN, and the classification a reviewing gate has already
run is recorded here so granting it is cheap rather than a fresh audit.** `## AC Sign-off` carries
`ac_hash: 2696ecd667a7` and `ac_hash_AC-3: eab359ff9e39`; both are stale against the section as it
now stands, and the conveyor refuses `specced → ready` on the `ac_hash` currency check whatever any
gate recommends — so this stands between the item and `ready` and no amount of spec-writing
discharges it. The 2026-09-08 spec review round 5 compared the evolved `## Acceptance Criteria`
against the frozen text at `docs/spec-reviews/WI-016-dave-review-2026-09-08.md` criterion by
criterion and found AC-1, AC-2, AC-4 and AC-5 unchanged and AC-3's only diff to be the
`CENSUS_DIGEST` literal (`625efeee…` at `:377` → `4cb7945f…` now). Under Check 12's taxonomy that is
an evidence-pointer update forced by a conductor remediation: **not strength-weakening, not
actor-swap, not scope-narrowing, not oracle-swap, and not exception-carving-by-addition.** It is a
conductor/Dave act and is named here rather than left for a linter; §10 P-10 records the two other
conductor acts that should ride the same pass, since a further census correction re-takes the digest
and one re-sign covers all of it.

**P-3 — atomic landing, checked against the PRE-DRIVE floor.** The census lands ALONE in the live
tree, before the build worktree exists, and the floor must be green at that moment. It is: the only
repo-wide markdown scan excludes `docs` (`tests/test_vault_path_required.py:387`), and the only two
modules that read a named doc name `docs/write-door-bypasses.md`
(`tests/test_ac_interpreter.py:40`) and `docs/company-name-corpus-audit.md`
(`tests/test_company_name_contract.py:855`) — neither is the census. So the census participates in
no bijection or symmetry the pre-drive floor enforces, and a lone precondition commit is safe. The
BUILDER's own changes are a different matter: `SKIP_REASONS`, `skip_reason_return_values` and AC-4's
check are three halves of one invariant and land in ONE commit.

**P-4 — the suite stays hermetic, and the AC battery reaches this project's interpreter through the
BRIDGE rather than through a YAML comment.** No network and no live-vault read anywhere. No
subprocess in any of the five `kind: test` CHECKS — and that promise now has the one clause it needs
to be true: `ensure_project_interpreter(__file__)`, which each check module must open with, is a
`find_spec("pydantic")` and returns immediately under the floor command and under CI
(`tests/ac_interpreter.py:123-130`), and under a FOREIGN interpreter it does not spawn a child either
— it `os.execve`s, replacing the process with the same one check under `<root>/.venv/bin/python`
(`:150-155`). The one place this item does make subprocesses is Task 12's battery-parity test, which
is a floor-graded test and not an AC check, and which runs the same shape
`tests/test_ac_interpreter.py` already runs on every floor run today.

**An earlier draft of this prerequisite asserted the opposite premise and it is corrected here rather
than quietly dropped.** It read "`pipeline-runners.yaml:7-8` makes the floor command the AC battery's
own interpreter", which takes a comment in that YAML as a guarantee. It is not one:
`tests/ac_interpreter.py:14-20` says in as many words that the battery's interpreter "defaults to the
ADVANCER's `sys.executable` and is only this project's venv when the driver passes `--ac-python`",
and that when it is not, every criterion of the item reports `ModuleNotFoundError` against a floor
that is green in the same tree. This item's five checks are the most library-executing set this repo
has shipped, so the bridge is load-bearing rather than ceremonial; §3.1 prescribes it.
`seed_deps: [.venv]` (`pipeline-runners.yaml:18-19`) is what puts `<root>/.venv/bin/python` in the
battery's worktree for the bridge to delegate TO, which is the real thing that YAML contributes here.

**P-4b — the floor's wall-clock, stated as a property and not a number.** CLAUDE.md's "~1s" is an
anchor, not an invariant, and Task 1's baseline is what this build measures against. The six foreign
runs Task 12 adds — one per `check:` name, plus the near-miss control — are the same shape
`tests/test_ac_interpreter.py` already performs inside
today's measured floor, so the marginal cost is known rather than estimated; if it is material it is
visible in Task 12's recorded floor run beside Task 1's, which is the instrument.

**P-5 — every `check:` is a top-level zero-argument `def test_*(` that signals failure by RAISING.**
The battery invokes it as `getattr(mod, name)()` with no fixture machinery
(`tests/support.py:1-19`). A check needing a temp directory uses `tests/support.temp_dir()`, not
`tmp_path`. A returned `False` exits 0 and reads as PASS.

**P-6 — each check name resolves to exactly ONE `tests/test_*.py`.** That is the conveyor's
discovery rule and this project asserts it (`tests/test_ac_interpreter.py:76-87`, a `def <name>(`
substring scan over `TESTS_ROOT.glob("test_*.py")`). All five `check:` names live in
`tests/test_fixture_vault.py` and appear as a top-level `def` nowhere else — including in no
docstring or comment of another test module. **The rule binds more than the five, and Task 12
therefore DERIVES the list rather than counting it.** Every top-level `def test_` this item writes is
subject to the same uniqueness scan, not only the ones an AC names: `tests/test_fixture_vault.py`
gains the five checks plus Task 2's binding test, Task 9's extractor battery and Task 12's own three
tests, and Task 10 adds three more in three other modules. Stating a number in the OBLIGATION is how
a plan drifts from itself — an earlier draft of Task 12 said "the six new check names" against a plan
that already defined twice that many, and the figure moved again when Task 12 gained its third test —
so the obligation is written as a predicate over the modules' own `def test_` sets and no count
appears in it. A count DOES appear in the dated sweep below, and the two are different things: the
sweep is a measurement taken on a day and labelled with it, while the obligation is what Task 12 runs.
`tests/fixture_vault.py` deliberately defines none: it is not collected (`pyproject.toml:41-43`)
and is not a check module (§3.1).

**And the obligation was CHECKED against the tree's EXISTING `def <name>(` set, not only within this
item's own additions — because a name is unique only relative to what is already there, and this
paragraph previously asserted the rule while checking one side of it.** `check_module` is a
`def <name>(` SUBSTRING scan over `TESTS_ROOT.glob("test_*.py")` that RAISES on anything but exactly
one match (`tests/test_ac_interpreter.py:76-87`), so the collision this rule must survive is with a
name ANOTHER item already shipped, which no sweep confined to this plan can see. The sweep, run in
this worktree 2026-09-08 over every `def <name>(` occurrence in the tree — not only top-level
definitions, because the scan is a substring scan and a docstring or comment spelling the same form
would count too — for all THIRTEEN top-level `def test_` names this item adds (Task 2's binding test;
Tasks 4-9's six; Task 10's three; Task 12's three): **twelve resolve to zero existing occurrences and
one collided.** Task 12's wall test was named
`test_wall_membership_is_closed_by_running_each_walls_predicate`, which
`tests/test_name_gate_wall.py:1057` has defined since WI-022 — the CALLER, at `:1073`, of the
`_check_the_ast_capability_stays_single_homed` helper (`:1132`) §11's W-1 anchors on, and named as
that item's Task 16 `verify:` at `docs/write-door-bypasses.md:4593`. Under the old name this item's own
uniqueness assertion would have raised `resolves to 2 module(s)` over this item's own file, and Task
12's `verify:` declaration would not have resolved under the conveyor's D10b rule. It is renamed
inside this item to
`test_the_fixture_vault_files_close_their_wall_memberships_by_running_each_predicate` (Task 12),
which the same sweep returns zero occurrences for; repointing from the other side is forbidden by
`## Scope Boundary`, which puts `tests/test_name_gate_wall.py` on the unchanged list. The collision
was CONCEPTUAL as well as lexical — WI-022's function runs every standing wall's predicate over ITS
item's final text, which is the same sentence this item's test would have carried — so the rename
names the item rather than merely disambiguating the string.

**The authoring-time sweep is not the wall; it is the same rule read one build earlier.** Task 12's
derived obligation runs `check_module` over every top-level `def test_` this item's write targets
define, from those modules' own source at test time, so a collision introduced after this paragraph
was written — by this item's builder or by a sibling item landing first — is RED at the build's last
task with the two modules named, rather than at the conveyor. Nothing here relies on the sweep above
being repeated by hand.

**P-7 — Python ≥ 3.10 (`pyproject.toml:11`), stdlib only.** `hashlib`, `unicodedata`, `pathlib`,
`dataclasses`, `fnmatch` — across BOTH new modules, split as §3 gives it: `unicodedata` is the
extractor's and `fnmatch` is Task 12's W-14 arm's, so both belong to `tests/test_fixture_vault.py`
alone; the rest to the manifest. No new dependency. **The ≥ 3.10 floor is load-bearing in exactly one
place and it is stated rather than discovered at build time:** `tomllib` is 3.11-only, so Task 12's
W-14 arm must not reach for it and reads `pyproject.toml`'s two declared keys with a helper that
RAISES rather than defaults (§11, W-14).

**P-8 — trust boundary.** The corpus is untrusted-shaped input by design (that is the point) but is
IN-REPO and never crosses a network. The one boundary that matters is the reverse direction: real
personal data crossing INTO permanent git history, which AC-5 makes structurally impossible rather
than intended.

**P-9 — `## Threat Model` sections DO exist on this document (2026-09-08, rounds 1 and 2), ROUND 2 is
the latest speaking round, and both of its `kind: required` mitigations are FOLDED.** This
prerequisite read "no `## Threat Model` section exists … and this spec authors no
`## Mitigation Folds` section"
through ten gate rounds; it was true when written and the 2026-09-08 threat model is what ended it,
which is why it is rewritten in place rather than annotated. The state now: round 1 returned REVISE
with `M1` (`landed: Task 8`) and `M2` (`landed: Task 3`), and **round 2 confirmed both folded and
RE-EMITTED the two `mitigation` fences BYTE-IDENTICALLY**, so the latest speaking round's required
set is the same two ids with the same `desc` text and the fold records stay fresh without being
re-quoted. M1 is folded into `## Design` §6.5 and Task
8, M2 into §6.5 and the Implementation Plan's precondition abort gate as re-run by Task 3; both are
recorded in `## Mitigation Folds` with the `desc` copied verbatim, the exact Design sentence, the
`Task N` ordinal and that task's own work and verify text. **Round 2's own blocking finding minted no
M3 and says so:** its subject is this document's gate prose rather than the build, no
Implementation-Plan task can carry a redaction of a settled gate section, and the round explicitly
declines to ask for a machine wall over `docs/vault-fixtures.md` — so its two halves are §10 P-10(a)
and `## Scope Boundary`'s standing authoring rules, neither of which is a fold. **The conveyor's D8c rule refuses
`specced → ready` while any required mitigation of the latest speaking round lacks a complete, fresh
fold record, and a `fold` fence written outside `## Mitigation Folds` is not a record** — the section
is a `##` sibling of `## Threat Model` and nothing about the landing lives inside the modeler's own
round, which is append-only and carries fences the conveyor routes on. If a LATER threat-model round
runs, its required mitigations must be folded the same way and `## Mitigation Folds` restated in
place, since that section carries no rounds and two records for one id are dropped as an unresolvable
contradiction.

**One thing M1's fold deliberately does NOT do, named because it would be the wrong reading of it:
`docs/vault-shape-census.md` does not become a write target.** M1 asks the SUITE to scan the
artifact's bytes; it asks nobody to edit them. The file stays on `## Scope Boundary`'s unchanged list
and stays the `kind: precondition` fence's subject in `## Write Targets`, the builder READS it and
never writes it, and M2's gate is a refusal rather than a repair. Turning it into a builder-writable
path would hand the build the very ledger AC-3(iv) exists to put out of its reach.

**P-10 — the CONDUCTOR acts this item still owes, one of them done and two outstanding, recorded in
one place because none is the spec-writer's to take and a gate that finds them scattered re-raises
them.** Everything below is outside `## Design`, `## Implementation Plan` and `## Write Targets`,
which is the test §10 P-2 sets for what may be fixed here versus escalated.

- **(a) The gate-round redaction — DONE, and the closure is recorded rather than assumed.** Threat
  model round 2's blocking finding was that round 1's remediation of `docs/vault-shape-census.md`
  moved two novel live-vault values into THIS document rather than out of the repository: four prose
  positions in `## Threat Model — 2026-09-08`'s finding and one inside that round's verdict `note:`.
  A conductor pass has since replaced all five in place with a bracketed redaction naming each
  value's LOCATION (its census row) and CHARACTER PROFILE, leaving the finding legible and
  re-checkable — which is the shape both gates asked for. **One thing this document CANNOT settle
  from inside the cage and says so rather than implying otherwise:** no gate or spec-writer here has
  a shell, so whether the round-1 section was already in a commit before the redaction — and
  therefore whether this was prevention or damage limitation — is a one-command question for the
  conductor and is not answered here. The durable half of that finding IS the spec-writer's and is
  landed: `## Scope Boundary`'s standing authoring rules.
- **(b) The `ac-signoff` re-sign — OUTSTANDING.** Exactly one, its scope and its Check 12
  classification recorded in P-2 above. It is what the conveyor's `ac_hash` currency check refuses
  `specced → ready` on.
- **(c) `docs/vault-shape-census.md:19`'s Method bullet — OUTSTANDING, and it should ride (b).** The
  bullet reads that the absolute vault path "is deliberately not recorded here (AC-5(e)'s
  no-absolute-path rule, **extended to this artifact by M1**)". It is not extended: §6.5 item 5 and
  Task 8 both say in terms that M1's scan does NOT extend leg (e) to the census, routing against the
  threat model round 1's own recorded ruling that the path is machine-local, names no person and is
  non-blocking. Nothing leaks today — the path is gone — but the artifact asserts a wall that does
  not exist, and a later census refresh re-adding the path would pass M1 green with its own Method
  bullet claiming otherwise. **The fix is one line in the census (drop the M1 citation, or state the
  omission as the conductor's own convention), and it belongs in the same pass as (b) because a
  census edit re-takes the digest and AC-3(iv) moves with it — bundled it costs nothing extra;
  taken separately it costs a second re-sign.** It is NOT closed by widening M1's scan, which would
  reverse a ruling two threat-model rounds have kept.
- **(d) The rounds-drawer copy — UNBLOCKED, and the ORDER is why it is recorded here.** Architect
  round 10's note 3 asks the conductor to move this document's settled rounds into
  `docs/vault-fixtures-rounds.md`. That drawer is byte-for-byte, append-only and never rewritten, so
  a copy taken BEFORE (a) would have put the two values past the reach of any redaction. (a) is done,
  so the copy is now safe to take. Two things it does not disturb, checked rather than assumed:
  AC-3(iv)'s `CENSUS_DIGEST` read is FENCE-SCOPED, and Task 12's "exactly five `check:` names" pin
  reads `criteria` fences only, of which this document holds five and all inside
  `## Acceptance Criteria`.

### §11. Standing walls this item's files join, and what each requires (WI-301)

Derived, not remembered. The sweep: every module under `tests/` that READS — in its own text or
through a helper it calls under the same root — the text of files it did not name at authoring time.
Run over `tests/*.py` in this worktree, that returns fourteen modules; each was read at FILE
granularity and noise discarded by reading. **This census is a FLOOR measured 2026-09-07, never a
total** — this derivation has under-reached at its reading step every time it has been run, which is
why Task 12's obligation is to RUN each predicate against the final text and NAME in the Build Log
anything the run returns that this table did not.

| # | Wall (check → predicate) | Universe | What it requires of this item's files |
|---|---|---|---|
| W-1 | `_check_the_ast_capability_stays_single_homed` (`tests/test_name_gate_wall.py:_check_the_ast_capability_stays_single_homed:1132`, live assertion at `:1136-1138`) → `modules_using_ast` | `python_files_under(PACKAGE_ROOT, TESTS_ROOT)` — GROWS with every file this item adds | set EQUALITY to `{"tests/derivations.py"}` over the PROJECTED module ids — `modules_using_ast` returns USE RECORDS (`tests/derivations.py:630`) and the shipped assertion projects them as `{use.module for use in live}` (`:1136-1138`), which is the form Task 12 must call. `tests/fixture_vault.py` and `tests/test_fixture_vault.py` must NOT import or attribute-access `ast`; `skip_reason_return_values` lands in `derivations.py` for exactly this reason (§4) |
| W-2 | `test_derivations_are_single_sourced` (`tests/test_loud_fail_harness.py:65`, live assertion at `:103`) | same | the IDENTICAL live assertion, re-run from a second module. Also asserts the `six` dict's six names are six distinct objects homed in `tests.derivations` (`:79-97`) — a REQUIRED SUBSET by `:18-20`, so the new scan does not join it and `len(six) == 6` does not move |
| W-3 | `test_filesystem_mutation_is_single_homed` (`tests/test_write_routing.py:87`) | `python_files_under(PACKAGE_ROOT, SCRIPTS_ROOT)` | `repositories/base.py` is a member and must gain no filesystem-mutation capability. A frozenset and three string constants introduce none. `tests/` is OUT of this universe, which is what makes `materialize_vault`'s `write_bytes` legal (§5.1) |
| W-4 | `test_every_derived_loader_records_a_derivation_stamp` (`tests/test_write_routing.py:361`) → `base_repository_subclasses` / `functions_calling` | `python_files_under(PACKAGE_ROOT)` and `(PACKAGE_ROOT, SCRIPTS_ROOT)` | `base.py` must gain no `parse_markdown_file` call. It gains none |
| W-5 | `test_committing_doors_never_return_falsy` (`tests/test_write_routing.py:461`) → `falsy_returns_in` | `python_files_under(PACKAGE_ROOT)` | no falsy return from a `COMMIT_FUNCTION_NAMES` member. `_skip_reason` is not one and returns a non-empty string on every arm |
| W-6 | `test_batch_load_survives_and_surfaces_only_owned_bad_notes` (`tests/test_loud_fail_load.py:76`) → `base_repository_subclasses` | `python_files_under(PACKAGE_ROOT)` | `discovered == set(matrix)` at four classes (`:121`). This item adds no repository, so it holds — asserted, not assumed |
| W-7 | `test_skip_surface_detail_is_bounded` (`tests/test_loud_fail_load.py:167`) | its own planted vault | asserts the observed reason set at `:187-188`. Task 11 repoints that literal at `SKIP_REASONS`, which is strictly stronger: a fourth reason with no specimen in THAT module's matrix vault goes RED where the hand-typed set stays green |
| W-8 | `test_docs_do_not_advertise_no_arg_construction` (`tests/test_vault_path_required.py:436`) → `_scanned_markdown_files` (`:421`) | every `*.md` under the repo root EXCEPT `.git`, `.venv`, `docs`, `state`, `node_modules` (`:387`) — **GROWS with every corpus note** | **the one wall the corpus itself joins, and the one no prior item in this repo has had to satisfy.** Every one of the ~50 notes is scanned for `\w+Repository\(\s*\)` (`:382`); none may contain it. The non-UTF-8 member is safe because the read is `errors="replace"` (`:451`) — verified, not assumed |
| W-9 | `test_no_implicit_vault_path_defaults` (`tests/test_vault_path_required.py:312`) | `obsidian_schemas/**` + `scripts/**`, code lines only | no absolute user path on an executable line of `base.py`. It gains none. `tests/` is out of this universe, so `fixture_vault.py`'s `Path(__file__)` derivation is unaffected — but AC-5(e) asserts the same property over it anyway |
| W-10 | `check_module` uniqueness (`tests/test_ac_interpreter.py:76-87`) | `TESTS_ROOT.glob("test_*.py")` — GROWS with the new module | each of this item's five `check:` names must appear as `def <name>(` in EXACTLY ONE module. `test_ac_interpreter.py`'s own live assertions name `docs/write-door-bypasses.md` (`:40`), not this doc, so this item's ACs do not join that battery — but the uniqueness RULE binds them, and P-6 carries it |
| W-11 | `test_the_tier1_surface_is_reified_totally…` (`tests/test_name_gate.py`) → `vars(name_validation)` `*_RE` census | `name_validation.py`'s module namespace | this item adds no regex and no branch. Green, and named so the next reader can tell it was checked |
| W-12 | `tests/test_lint_vault_fix_gate.py` | derives from `SCRIPTS_ROOT` but NAMES `lint_vault.py` (`:44`) | universe does not grow. Not a member |
| W-13 | `tests/test_company_name_contract.py:855` | NAMES `docs/company-name-corpus-audit.md` | universe does not grow. Not a member |
| W-14 | pytest collection (`pyproject.toml:41-43`) — **the ONE row with no callable predicate, declared LOUDLY rather than skipped (WI-301)** | `testpaths = ["tests"]`, `python_files = ["test_*.py"]` | `tests/fixture_vault.py` is not collected (no `test_` prefix) and `tests/fixtures/vault/*.md` is not collected (not `.py`). No `conftest.py` is added — P2 records its absence as load-bearing. pytest ships no importable "would this path be collected" membership function in the build profile and `tomllib` is 3.11-only against P-7's ≥ 3.10 floor, so Task 12 drives the CONFIG'S OWN declared `python_files` globs — read from `pyproject.toml` by a helper that RAISES rather than defaults — through `fnmatch`, with `tests/test_fixture_vault.py`'s own name as the positive control that stops the matcher passing by matching nothing |
| W-15 | `skip_reason_literal_sites` (§4) — **MINTED BY THIS ITEM**, Tasks 2 and 11 | `python_files_under(PACKAGE_ROOT, TESTS_ROOT)` — GROWS with every file this item adds | set EQUALITY to `{"obsidian_schemas/repositories/base.py", "tests/test_fixture_vault.py"}`. So `tests/fixture_vault.py` must IMPORT the three reason constants rather than re-spell them (§3), `tests/test_fixture_vault.py` carries the one hand-typed spelling pin and nothing else, and Task 11's three repointed sites are obligations of this row rather than tidying |
| W-16 | battery parity under the conveyor's interpreter — `criterion_checks` (`tests/test_ac_interpreter.py:57-73`), `check_module` (`:76-87`), `run_foreign` (`:90-95`), **IMPORTED and driven over THIS document's `criteria` fences**, Task 12 | this item's five `check:` names | each must exit 0 under `sys.executable -S` in the conveyor's argv shape **AND have got there by DELEGATING — `"[ac_interpreter]" in proc.stderr` — which is the shipped wall's own second clause and not an embellishment**: the shipped `test_every_acceptance_criterion_passes_under_the_conveyors_interpreter` asserts both (`tests/test_ac_interpreter.py:111-115` for the exit code, `:116-120` for the marker, whose failure message is "exited 0 WITHOUT delegating — the foreign interpreter imported the project's deps, so this run proves nothing about the battery's conditions"), and it ships a near-miss control beside it (`test_a_failing_delegated_check_is_red_not_silently_green`, `:126-138`) proving a nonexistent check is RED under the same shape. Exit 0 ALONE is a wall-shaped no-op here, because `-S` strips `site` but not an ambient or CI install: on any interpreter where the runtime deps survive `-S`, every check exits 0 without ever delegating, the parity test is green, and `## Verification`'s mutation 9 — the only mutation whose GREEN half is the finding — never fires, leaving R9 uncovered by the one thing this document says can cover it (§3.1 is invisible to the floor by design, W-10's population does not reach this item, and this sweep's own predicate structurally cannot see a capability injection). Both clauses are true only if `tests/test_fixture_vault.py` opens with `ensure_project_interpreter(__file__)` (§3.1). `tests/test_ac_interpreter.py`'s OWN live assertions are scoped to `docs/write-door-bypasses.md` (`:40`), so this item is outside its population and must run the parity itself — the wall is real but its universe does not reach here, which is why this row exists rather than a claim that W-10 covers it |

**Checked and cleared, so the next reader can tell they were checked rather than missed.** The
repo-wide markdown scan (W-8) excludes `docs`, so neither this document nor the census joins it.
**That exclusion is the measurement behind the 2026-09-08 threat model's finding and is repeated here
with its consequence rather than left as a clearance:** there is no standing wall of ANY kind over
`docs/` in this repository, which is why the census's prose could carry a real live-vault value with
every check in this document green, and why M1's scan (§6.5, Task 8) is a wall this item MINTS rather
than a membership it joins. It is not a `## Write Targets` obligation on the census either — the scan
reads that file and never writes it, so no row of this table moves and the file stays on
`## Scope Boundary`'s unchanged list.
There is no `docs/**`-globbing fixture wall in this project (the local convention is the
`CORPUS_COUPLING:` docstring line, `tests/test_company_name_contract.py:15` and
`tests/test_ac_interpreter.py:23`, which §3 and the new test module both carry) — so WI-278's
corpus-coupling rule is discharged by DECLARATION here rather than by a standing sweep, and the
declaration names what each module pins and what property it consumes. **The interpreter bridge is
the other project convention with no standing sweep behind it**, and it is the one this item was
about to miss: six check modules call `ensure_project_interpreter(__file__)` as their first statement
(`tests/test_company_name_contract.py:25`, `tests/test_address_splitter.py:38`,
`tests/test_name_gate_identifiers.py:41`, `tests/test_name_gate_refusals.py:41`,
`tests/test_name_gate_wall.py:40`, `tests/test_name_gate_delta_rule.py:37`) and nothing sweeps for
its absence, because this sweep's own predicate — modules that READ the text of files they did not
name — structurally cannot reach a capability INJECTION. `tests/test_fixture_vault.py` is the seventh
caller (§3.1) and W-16 is how membership is closed by RUNNING rather than by reading.

**The four modules this sweep RETURNED and the table does not otherwise name, recorded so
"read and discarded" is distinguishable from "not reached".** The predicate returns fourteen
modules; the rows above name nine of them plus `tests/derivations.py`. The remaining four are
`tests/test_loud_fail_write.py`, `tests/test_loud_fail_parse.py`, `tests/test_address_splitter.py`
and `tests/test_concurrent_access.py`. Each was read at FILE granularity: every one of them sweeps
`python_files_under(PACKAGE_ROOT)`, which contains the edited `repositories/base.py`, and none is
disturbed by a frozenset plus three string constants and three return statements that now name them.
The one worth spelling out is `tests/test_concurrent_access.py:1077-1089`, which carries FOUR
hardcoded count pins over package-derived populations —
`len(functions_reserializing_parsed_frontmatter(files)) == 4` (`:1077`),
`len(non_completed_write_sites(files)) == 8` (`:1085`),
`len(base_repository_subclasses(files)) == 4` (`:1088`) and
`len(load_file_implementations(...)) == 3` (`:1089`) — the WI-229 count-pin shape exactly. None
moves: this item adds no function that reserializes parsed frontmatter, no falsy return in a write
path (`_skip_reason` returns a non-empty string on every arm, W-5), no `BaseRepository` subclass and
no `_load_file` implementation. That is asserted here and RE-ASSERTED by running: those four modules
are in Task 12's floor run, and the floor is where a moved pin shows up.

---

## Edge Cases & Open Questions

**Empty / null / malformed input.** *Case:* a corpus note with no frontmatter, unparseable YAML, or
bytes that are not UTF-8. *Decision:* these are not edge cases, they are DELIVERABLES — §1.3 rule 3
requires one specimen per `SKIP_REASONS` member and rule 4 requires the non-UTF-8 one. Each is
declared in `SKIPS` under its owning repositories and asserted both directions by AC-4(a).
*Reasoning:* the surface exists precisely because an unloadable note used to vanish at DEBUG
(`base.py:29-34`).

**Race conditions / concurrent access.** *Case:* two tests materialize the corpus at once. *Decision:*
each caller supplies its own `dest`; `materialize_vault` never writes to `CORPUS_ROOT` and never to
a shared location. The corpus itself is read-only at run time. *Reasoning:* the only shared mutable
state a fixture vault could introduce is a shared destination, and the signature makes one
impossible. AC-5(e) asserts writes land only under `dest`.

**External dependency failure.** *Case:* `docs/vault-shape-census.md` is missing or its digest does
not match. *Decision:* both AC-3 and AC-5 RAISE naming the file and the mismatch — never skip, never
degrade to a weaker assertion. A missing precondition is caught earlier still, by the WI-156 driver
probe before the builder is armed. *Reasoning:* an "if the census exists" guard would make the
oracle optional, which is the whole failure AC-3(iv) was added to close.

**First-run vs subsequent-run.** *Case:* nothing differs. `materialize_vault` into a fresh directory
is the only mode; there is no cache, no lazily-built artifact and no first-run migration.
*Reasoning:* the corpus is committed bytes.

**Migration / backfill.** *Case:* thirteen test files hold 83 inline `type:` literals. *Decision:*
three files gain a corpus-backed test and two of them lose an inline heredoc (§9.1); the other ten
migrate when their own tests are next touched (D5). *Reasoning:* stated at length in §9.1 — a
mechanical repoint of `temp_vault` rewrites ~1,950 lines of value assertions in the same build that
introduces the values.

**Idempotency.** *Case:* `materialize_vault` called twice against the same `dest`. *Decision:*
`mkdir(parents=True, exist_ok=True)` then `write_bytes` per file — the second call overwrites with
identical bytes and the result is identical. A `dest` containing FOREIGN files is not cleaned:
`materialize_vault` adds, it does not empty. *Reasoning:* emptying a caller-supplied directory is a
destructive act a fixture helper has no business performing; every caller in this build supplies a
fresh temp directory, and AC-1(b)'s "fresh empty directory" is stated in the criterion.

**Retry semantics.** *Case:* none apply. No network, no subprocess, no lock contention outside
`write_markdown_file`'s own `note_lock`, which AC-2(c) exercises against a fresh temp path.

**Partial failure.** *Case:* materialization fails halfway (disk full, permission). *Decision:* the
exception propagates; there is no partial-state cleanup and none is wanted, because the destination
is a temp directory the caller owns and discards. *Reasoning:* a half-materialized vault that
silently continued would be a corpus that quietly under-covers, which is the failure AC-1(b)'s
digest-over-the-materialized-tree catches.

**Error propagation.** *Case:* what a caller sees. *Decision:* `parse_markdown_file` over a corrupt
specimen raises `FrontmatterParseError` / `SchemaDriftError` / `UnicodeDecodeError` exactly as it
does over any note; `repo.load()` never propagates — it records a `SkippedNote` and logs a WARNING
(`base.py:267-275`); a re-introduction of a corruption specimen through a write arm raises
`NameGateRefusal` carrying `.pattern`. Every AC test names the LEAF it means — `NameGateRefusal`,
never the `LoudFailError` root — per CLAUDE.md's loud-fail idiom.

**Trust boundary crossings.** *Case:* the corpus is the untrusted side by design. *Decision:* no
sanitisation, ever — sanitising the specimens destroys the shapes they exist to carry. The boundary
that IS enforced is the outbound one, AC-5. *Reasoning:* D-6.

**A specimen the census measures that the corpus cannot legally hold.** *Case:* a census class whose
faithful specimen would put a real-word token into an identity position (a `London`, a `Group`).
*Decision:* the specimen is constructed, not transcribed — `## Write Targets` charges the CONDUCTOR
with writing constructed identity tokens into the class table's specimen column, so the corpus
copies a character profile and never a vocabulary. If a landed census row violates that, the builder
ABORTS under the Implementation Plan's precondition gate rather than inventing a substitute.

**Two census rows that cannot have distinct specimens.** *Case:* same-name collision and stem/name
divergence are structurally the same shape in a flat directory. *Decision:* the CENSUS rules whether
they are one class or two; if one, it writes one row, the manifest's covered-class set follows, and
AC-3(i) is satisfied by a fifteen-row table as readily as a sixteen-row one. **RULED, 2026-09-07:
TWO classes** — `same_name_collision` ABSENT (count 0; the largest live collision is two notes) and
`stem_name_divergence` MEASURED (count 8). *Consequence, which is a change to what the corpus
DECLARES and not to what it holds:* §1.3 rule 5's three-filename collision is still planted, because
§3's `LOADABLE` arithmetic and `_get_cache_key`'s collapse depend on it, but it is declared under
`shape_classes = ("stem_name_divergence",)` and never as a `same_name_collision` specimen, which
would be RED against that ABSENT row under AC-3(i).

**A criterion that obliges a specimen for a class the census rules ABSENT.** *Case:* AC-1(c) obliges
an arrow-connective and a path-hostile `name:` specimen "named in the manifest as such"; the landed
census rules both classes ABSENT, and AC-3(i)'s reverse direction makes a specimen belonging to no
MEASURED class RED. *Decision:* the two obligations are answered by two DIFFERENT manifest fields —
`shape_classes = ()` and `NoteSpec.discriminator = "<branch_id>"` (§1.3 rule 7, §3, Task 4). *Reasoning:*
the questions are different in kind. AC-1(c) is about the DOOR's behaviour, which is a fact about the
package and true whatever the vault holds; AC-3(i) is about the VAULT's distribution. One field
cannot answer both, and both criteria are signed, so the reconciliation had to land in the manifest
rather than in either criterion. Exercised by Verification mutation 15 in both directions.

**An identity token in the CENSUS itself.** *Case:* the artifact AC-3 and AC-5(c) delegate their
entire oracle to carries a real live-vault name — in a prose bullet, which no fence parses and which
`## Design` §2 puts outside the suite's parser. *Decision:* the census's whole byte stream is inside
the identity closure it certifies (M1, §6.5, Task 8), and the same predicate runs one build phase
earlier as a REFUSAL in the precondition abort gate (M2, Task 3). Neither authorises the builder to
edit the artifact: the gate STOPS and the remedy is a conductor pass. *Reasoning:* AC-3(iv) and
AC-5(c) digest this file, so without the closure the build does not merely ship such a leak, it
asserts it immutable — and the census refresh R7 names as certain-eventually would reopen it with
nothing to notice. The residue is the same one AC-5(b) carries and is not enlarged: a name typed
deliberately into `CENSUS_PROSE_ALLOWLIST` is a name a human reviews, which is the most a structural
wall can do about a value the hermetic suite cannot check against the vault.

**A ninth entity type, a fifth repository, an eleventh Tier-1 branch, a fourth skip reason.**
*Case:* the package grows after this lands. *Decision:* each is RED immediately and by design —
AC-2's `set(TYPE_TO_MODEL)` equality, AC-4's derived repository set, AC-3's derived branch floor,
AC-4's `SKIP_REASONS` union equality. *Reasoning:* that is the item's purpose. The recurring cost is
named rather than discovered: a new Tier-1 branch needs a census row (a live-vault act no caged
builder can perform) and, under AC-3(iv), a re-taken census digest — LESSONS #45's intended
friction, written down so the next branch author is told rather than surprised.

**A run beginning with `'` or `-`.** *Case:* `-Voxleaf`. *Decision:* the first character is read
BEFORE trimming, so it yields no token (§6.1). *Reasoning:* stated in §6.1 with the YAML-sequence
argument; the residue is what the pool's one-time human review covers.

**An ISBN read as a phone.** *Case:* `Book.isbn` is a 13-digit run and the phone predicate matches
≥9 digits. *Decision:* one author-declared `RESERVED_ISBN` literal, asserted by equality (§6.4).
*Reasoning:* an ISBN is not a phone and has no reserved range; equality against a one-member literal
cannot be padded and imposes no obligation over anything the builder does not author.

**A declared hex literal read as a phone — the ISBN's own class, closed at the second member rather
than at the first.** *Case:* leg (a)'s reach includes `tests/fixture_vault.py`, which by §3's design
carries `CORPUS_DIGEST` and `NoteSpec.raw_bytes_hex` (a full note's bytes in lowercase hex).
Printable ASCII hex-encodes to first nibbles `2`–`7`, all digits, so `type:` alone yields the
nine-digit run `747970653` and the leg is RED on a wholly correct corpus; a re-taken 64-character
digest can redden it again at random. *Decision:* the scan excises the manifest's DECLARED hex
literals — `CORPUS_DIGEST`, every non-`None` `raw_bytes_hex`, and AC-3(iv)'s optional `CENSUS_DIGEST`
restatement — before the span walk, each asserted well-formed lowercase hex of even length and
asserted to OCCUR SOMEWHERE IN THE REACH, once against the union of the scanned files' bytes rather
than once per file, while the excision runs per file regardless (§6.4, AC-5(a), Task 8). *Reasoning:* the ISBN
decision was correct and stopped one instance short, in the same document that had already introduced
two longer hex literals of its own. Excision by NAME keeps the exemption author-declared and
equality-asserted, so it cannot be padded; excision by SHAPE (a "hex-looking run" rule) would have
been the padding surface, because a builder could then spell any awkward run as hex. Legs (b) and (e)
scan the unexcised text and are unaffected.

**OPEN: None.**

---

## Implementation Plan

Tasks 5 through 9 are independent of one another once Tasks 1-4 have landed and may be written in
any order; everything else is strictly ordered by dependency.

**Precondition gate — read this BEFORE Task 3, and ABORT rather than fabricate.** Immediately after
Task 1's baseline capture, open `docs/vault-shape-census.md` and confirm it satisfies §2 and P-1:
exactly one ```census-meta fence carrying `snapshot`; one ```census-class fence per shape class,
each with `id`, `count`, `status` in `{MEASURED, ABSENT}`, a non-empty COUNTING `command`, a
non-empty `stdout`, and a `specimen` iff MEASURED / a `ruling` iff ABSENT; one ```census-class row
for every `branch_id` in `TIER1_BRANCHES + COMPANY_TIER1_BRANCHES`; and one ```census-pool fence per
certified token, each with `token`, `class`, a counting `command` and a `stdout` of `0`. Also confirm
AC-3(iv)'s `CENSUS_DIGEST` declaration inside the AC-3 `criteria` fence of `docs/vault-fixtures.md`
holds a real 64-character lowercase hex value and not the placeholder, and that `sha256` over the
census's bytes EQUALS it. **AND — the threat model's M2, and the last thing checked because it needs
the parsed pool table the checks above establish — run §6.1's `identity_tokens` over the WHOLE of
`docs/vault-shape-census.md`, prose and fences alike, and confirm every token it yields is in that
artifact's own `census-pool` token set, in `CONNECTIVE_SET` (`{"Me", "My", "Dave"}`), or admitted by
`str.lower() in name_cleaning._GENERIC_ORG_SUFFIXES`, with any remainder being ordinary technical
vocabulary the census's prose needs** (§6.5). Two failures this one read catches, and both are RED at
Task 8 with no in-cage remedy if it is skipped: a real live-vault name transcribed into a prose
bullet or a specimen column, and a pool table certified at WORD granularity where the extractor
produces a hyphen-fused COMPOUND (`Brenvik-Tarnquil`, `Pellworth-Wexlund` — §6.2). **If any of that
is absent, STOP at Task 2 under the Abort Protocol and hand off to the conductor** — record in the
Build Log exactly which fence, key or digit is missing, and for the M2 arm the exact uncertified
tokens and where in the file each occurs.
Do NOT author or amend a single byte of the census, do NOT fill the digest, and do NOT narrow any
task's assertions to fit the artifact as found: the evidence is a live-vault execution the cage
cannot perform, so anything written there would be fabrication (the D2 rejection, and the WI-024
precedent). The WI-156 driver probe checks only that the path is in HEAD, never its content — this
paragraph is the only thing standing between an incomplete census and a burned build attempt.

- [x] **Task 1 — Capture the pre-build baseline.** Run the floor command
  (`/Users/davewascha/Workspaces/obsidian-schemas/.venv/bin/python -m pytest
  /Users/davewascha/Workspaces/obsidian-schemas/tests -q`, absolute per CLAUDE.md, adjusted to the
  worktree root) and record in the Build Log: the passing case count, and `git rev-parse HEAD` for
  the seeded worktree. These are informational — no later check asserts either number, and the floor
  invariant is DIRECTIONAL (a later run landing fewer cases without explanation has lost a test
  file).
  **Verify:** both values are in the Build Log before any file is edited.
  verify: baseline — the pre-edit floor case count and the worktree HEAD, recorded in the Build Log; no later check asserts either value, and this item's own tasks move the count.

- [x] **Task 2 — Declare the skip-reason codomain and BIND it to the function.** In
  `obsidian_schemas/repositories/base.py`, add the three module-level reason constants and the
  `SKIP_REASONS` frozenset exactly as §4 gives, and change `_skip_reason`'s three arms to return
  those names. Leave the `#` type comment at `:37` exactly as it is. In `tests/derivations.py`, add
  BOTH scans per §4 — `skip_reason_return_values` and `skip_reason_literal_sites` — reusing `_parse`
  (`:213`), `_iter_functions` (`:217`) and `_own_body_nodes` (`:243`); an unresolvable return raises
  `AssertionError` naming module, function and lineno. Create `tests/test_fixture_vault.py`, and its
  FIRST executable statement is the interpreter bridge, ahead of every package import, exactly as
  §3.1 gives it and exactly as `tests/test_name_gate_wall.py:38-40` does: `from tests.ac_interpreter
  import ensure_project_interpreter` then `ensure_project_interpreter(__file__)`, with `# noqa: E402`
  on the first import below it. All five of this item's checks execute the library behind pydantic
  and the conveyor does not necessarily run them under this project's interpreter
  (`tests/ac_interpreter.py:7-25`); the floor cannot see the omission, so it is written here rather
  than left to judgment. Then the module docstring (including its `CORPUS_COUPLING:` line naming
  `docs/vault-shape-census.md` and `docs/vault-fixtures.md` and the properties it consumes from each)
  and ONE test, `test_skip_reason_declaration_binds_to_its_functions_returns`, which (a) asserts
  `skip_reason_return_values(PACKAGE_ROOT / "repositories" / "base.py") == SKIP_REASONS`, (b)
  asserts `SKIP_REASONS` is non-empty and of size exactly 3, (c) carries the ONE hand-typed spelling
  pin the vocabulary keeps — `SKIP_REASONS == {"malformed-frontmatter", "schema-drift",
  "unreadable"}` — which is this module's membership of W-15 and the reason the wall's expected set
  has two homes rather than one, and (d) drives PLANTED source
  through the SAME predicates the live assertions call — never a re-implementation — written under
  `tests/support.temp_dir()`. Shapes that MUST resolve for `skip_reason_return_values`:
  `return "literal"`; `return NAME` where `NAME` is a module-level `str` constant; two arms in one
  function; an arm inside an `if` and one inside a `for`. Shapes that must RAISE rather than be
  silently dropped: `return name_var` where `name_var` is a local; `return f"{x}"`;
  `return CHOICES[0]`. A near-miss that must NOT contribute: a `return` of a string inside a NESTED
  function of the same name. `skip_reason_literal_sites` gets its planted battery HERE too, while the
  LIVE set-equality that consumes it waits for Task 11 — the predicate is proven in this sitting, the
  wall it feeds is asserted in the sitting that makes it true, and neither task is verified against a
  red. Shapes that MUST be returned by `skip_reason_literal_sites`: a bare
  `x = "unreadable"`; a member inside a set/list/dict literal; a member as a call argument; a member
  in an `==` comparison. Near-misses it must NOT return: a `#` comment naming all three (the
  `base.py:37` shape); a docstring whose PROSE contains the word (the `errors.py:112` shape); a
  string that merely CONTAINS a member as a substring; the constant NAMES `UNREADABLE` /
  `SCHEMA_DRIFT` / `MALFORMED_FRONTMATTER` used as identifiers.
  verify: test_skip_reason_declaration_binds_to_its_functions_returns

- [x] **Task 3 — Run the precondition abort gate, INCLUDING its M2 arm, then author the corpus.**
  **FIRST, before a single corpus byte is written, re-run the precondition gate above in full and run
  its M2 arm — the threat model's `M2`, folded here (§6.5).** Apply §6.1's run rule to the WHOLE of
  `docs/vault-shape-census.md`, prose and fences alike (an ad-hoc one-liner or a REPL paste of §6.1's
  `identity_tokens` is the right instrument at this task — the standing form of the same predicate
  lands at Task 8), and confirm every token it yields is in the artifact's own `census-pool` token
  set, in `CONNECTIVE_SET` (`{"Me", "My", "Dave"}`), or admitted by `str.lower() in
  name_cleaning._GENERIC_ORG_SUFFIXES`, the remainder being ordinary technical vocabulary. **If any
  identity-shaped token is uncertified — a real live-vault name transcribed into a prose bullet, or a
  hyphen-fused compound whose halves alone are certified — STOP under the Abort Protocol with those
  exact tokens and their locations in the Build Log.** Do not author, amend or normalise a byte of the
  census, do not add a pool row, do not drop a hyphen, and do not author a corpus against an artifact
  that will have to be re-authored: the remedy is a conductor pass (one census edit, one re-taken
  digest, one AC-3(iv) edit, one D4b re-sign), and the whole value of running this at Task 3 rather
  than discovering it at Task 8 is that ~50 notes have not yet been written against it.
  **THEN** create `tests/fixtures/vault/` and write the ~50 notes per
  §1.1-§1.4, assembled from the landed census: one note per `TYPE_TO_MODEL` member with exactly one
  `roundtrip_representative` each; one specimen per MEASURED census class carrying that row's
  character profile with CONSTRUCTED identity tokens, declared in `shape_classes` — the SIX MEASURED
  ids and no others (§1.3 rule 2); one specimen per `SKIP_REASONS` member with
  the two untyped classes planted under BOTH owning globs; exactly one member that is not valid
  UTF-8; at least three filenames sharing one stored `name:`, declared under
  `shape_classes = ("stem_name_divergence",)` and NEVER as a `same_name_collision` specimen, which
  the census rules ABSENT (§1.3 rule 5); the TWO AC-1(c) discriminator members — one
  arrow-connective, one path-hostile — carrying `shape_classes = ()` and their `branch_id` in
  `NoteSpec.discriminator` (§1.3 rule 7, §3); the `pure_digit` specimen declaring NO `phones`, so its
  declared `Verdict` is the refusal rather than a load (§5.3); every email under an RFC 2606 domain,
  every phone in `447700900xxx` / `07700900xxx` (the same drama block in either spelling, §6.4) or
  NPA-`555-01xx`, every URL host reserved, and the single
  `RESERVED_ISBN`. No note may contain `\w+Repository\(\s*\)` (§11, W-8). Record in the Build Log
  the M2 gate's result, the file count, the per-type and per-census-class tally, and the confirmation
  that exactly one member raises `UnicodeDecodeError` under `read_text(encoding="utf-8")`.
  **Verify:** the M2 gate's result and the tallies are in the Build Log; the corpus's first standing
  artifact is Task 4's digest and M2's standing form is Task 8's M1 assertion.
  verify: hand-run — the M2 abort gate is a pre-authoring inspection whose whole point is to run BEFORE any artifact exists, and the corpus is inert bytes with no standing check until Task 4 lands the digest and the manifest; both acts are recorded in the Build Log (the gate's uncertified-token result, the file count, the per-type and per-class tally, and the one-member UTF-8 probe), and the standing form of the same predicate is Task 8's M1 assertion.

- [x] **Task 4 — Land the manifest module and AC-1.** Create `tests/fixture_vault.py` exactly as §3
  gives — docstring with the `CORPUS_COUPLING:` line, the load-bearing `name_cleaning.py:58`
  dependency note and the digest-regeneration recipe; `CORPUS_ROOT`; `Verdict`; `NoteSpec`; `NOTES`
  filled for every corpus member with HAND-WRITTEN `fields`; `materialize_vault` (§5.1) and
  `corpus_digest` (§5.2). Compute `CORPUS_DIGEST` with the recipe and paste it in. It must not name
  `ast`, must contain no URL and no absolute path. Then add
  `test_fixture_vault_is_frozen_and_materialized_by_byte_copy` to `tests/test_fixture_vault.py`:
  leg (a) recomputes the digest and compares — the digest's key is the FILENAME (`path.name`), which
  is what AC-1(a)'s "corpus-relative POSIX path" means in a flat directory and what makes leg (b)
  satisfiable at all; leg (b) materializes into a fresh `tests/support.temp_dir()` and asserts the
  same relative name set, the same per-file bytes and the same digest, THEN writes a foreign file
  into that same `dest`, calls `materialize_vault(dest)` a SECOND time, and asserts that every corpus
  member is still byte-identical, that the digest over the corpus members is unchanged, and that the
  foreign file is still there — the idempotency and no-clean rules `## Edge Cases` decides, exercised
  rather than only written down, and the assertion that would go RED if a later "clean the
  destination first" branch were added; leg (c) asserts the corpus holds at least one arrow-connective and one path-hostile
  `name:` specimen NAMED as such in the manifest, that materialization succeeds with them present
  and byte-identical, and — the planted discriminator — that a write through the gated door refuses
  them.
  **"NAMED as such in the manifest" is read off `NoteSpec.discriminator` and NEVER off
  `shape_classes`, which is §1.3 rule 7 and is the one place this leg could be built two ways.** The
  test asserts `{spec.discriminator for spec in NOTES.values() if spec.discriminator} ⊇
  {"arrow_connective", "path_hostile"}`, that every non-empty `discriminator` is a member of
  `{record.branch_id for record in TIER1_BRANCHES + COMPANY_TIER1_BRANCHES}` (so the field cannot be
  padded with a free-text label), and that both those notes carry `shape_classes == ()`. Reading
  `shape_classes` here instead would put two ids the landed census rules ABSENT into AC-3(i)'s
  covered-class set and redden AC-3 over a wholly correct corpus, with no in-cage remedy now that
  both criteria are signed (§3 argues the two-field split; §5.5 states which field AC-3 reads).
  Then, on those same members,
  `write_markdown_file(<fresh dir> / <that specimen's filename>,
  frontmatter=<that specimen's declared frontmatter>)` raises `NameGateRefusal` on exactly those
  members. **The first argument is the note's own FILE path, never the directory** — `writer.py:160-169`
  takes `file_path` first and `:205` uses `Path(file_path)` as the note's path, which is the shape
  §5.3 already gives (`write_markdown_file(fresh_dir / filename, entity=doc.entity)`); an earlier
  draft of this leg passed the directory and is corrected here rather than left for the builder to
  reconcile against §5.3. The `frontmatter=` arm rather than `entity=` is deliberate and its refusal
  is reached, not assumed: it enters at `writer.py:234-238` with `gate_whole_record = False`, and the
  ONE `gate_write` call at `writer.py:252-253` passes `declared_type=fm.get("type")` — so a `person`
  specimen reaches `name_gate.py`'s person arm at `:349-365`, whose `NameValidator().validate_strict`
  refusal is re-raised as `NameGateRefusal` by the single `_refuse` site (`name_gate.py:142`). That
  path never reads `whole_record`, so the discriminator holds on this arm and does not depend on
  constructing a model for a name the gate exists to refuse.
  verify: test_fixture_vault_is_frozen_and_materialized_by_byte_copy

- [x] **Task 5 — AC-2: the type-registry sweep.** Add
  `test_every_entity_type_round_trips_against_declared_values`. Derive the population as
  `set(TYPE_TO_MODEL)`, asserted non-empty and of size exactly 8, and assert it EQUALS the manifest's
  covered type set. Run legs (a), (b) and (c) per §5.3 for every member, with leg (c) writing through
  `write_markdown_file` (the gated door) and re-parsing. Derive the narrowing arm as
  `set(TYPE_TO_MODEL) - set(ENTITY_BODY_CONFIG)`, asserted of size exactly 3, and assert
  `get_default_body(t) == ""` for those and the config's declared `sections` for the intersection.
  Assert every `roundtrip_representative` is GATE-CLEAN by the door's own predicate
  (`Tier1Branch.matches`), person against `TIER1_BRANCHES` and company against
  `COMPANY_TIER1_BRANCHES`, vacuous for the other six.
  verify: test_every_entity_type_round_trips_against_declared_values

- [x] **Task 6 — AC-3: the census reader and the class floor.** Add the three-fence reader per §2 to
  `tests/test_fixture_vault.py` (LOUD on an unknown key, a missing required key or a `status` outside
  `{MEASURED, ABSENT}`), plus the fence-scoped reader that recovers the `CENSUS_DIGEST` value from
  the AC-3 `criteria` fence of `docs/vault-fixtures.md`, asserting exactly one such declaration
  WITHIN that fence and well-formed 64-character lowercase hex. Add
  `test_every_census_corruption_class_has_a_specimen_with_a_verdict` running assertion (iv) FIRST
  (census fixity), then (i) the both-directions equality over MEASURED rows against the manifest's
  covered classes, (ii) the per-row shape check conditional on status, and (iii) the class floor —
  branch half derived as `{record.branch_id for record in TIER1_BRANCHES + COMPANY_TIER1_BRANCHES}`,
  asserted non-empty and of size exactly 10 and in BOTH directions over branch-keyed rows, plus the
  six hand-listed shape classes. For each floor class WHOSE CENSUS ROW IS `MEASURED`, assert the
  manifest's declared `Verdict`: a `NameGateRefusal` carrying the named `.pattern` when the
  specimen's name is re-introduced through a write arm, or `clean_person_name` output equal to the
  declared string, or a declared successful byte-identical load. **The `MEASURED` qualifier is
  load-bearing and not a hedge:** AC-3(iii) makes the floor a check on the ROW's presence at either
  status, and AC-3 says in as many words that "a live vault holding no empty-named note gets an
  ABSENT row … and obliges no specimen" — so an ABSENT class has no specimen and therefore no
  `Verdict` to declare, and demanding one would redden the honest census this criterion exists to
  reward. §9.4 names `empty` as the likely ABSENT row, so the case is expected rather than
  hypothetical. An ABSENT row's obligations are assertion (ii)'s alone: count exactly 0, a non-empty
  command, non-empty stdout, an affirmative ruling, and NO specimen. **Against the LANDED census the
  MEASURED set is exactly six** — `diacritics`, `hyphenated_surname`, `whitespace_damage`,
  `stem_name_divergence`, `postal_address_in_name`, `pure_digit` — so those six carry a declared
  `Verdict` and the other ten rows carry none. **The one whose verdict is not free to choose is
  `pure_digit`, and §5.3 pins it:** `allow_phone_sentinel` (`name_gate.py:355-358`) passes a
  digit-named note that ALSO declares `phones`, so the corpus's `pure_digit` specimen declares no
  `phones` and its declared `Verdict` is `kind="refusal"`, `pattern="pure_digit_name"`. **That value
  is the RECORD'S `pattern` FIELD and not its `branch_id`, which is the rule §3 states for every
  declared refusal `Verdict` in this manifest and is not a spelling choice here:**
  `name_validation.py:284-285` gives the record `branch_id="pure_digit"` and
  `pattern="pure_digit_name"`, `:678` raises `NameValidationError(branch.pattern, …)`, `:463` binds
  it, and `name_gate.py:365` re-raises it through the single `_refuse` site — so the
  `NameGateRefusal` this assertion catches carries `.pattern == "pure_digit_name"`. An earlier draft
  of this task pinned `pure_digit` and would have been RED against a wholly correct corpus.
  Assertion (i)'s manifest side is the union of `shape_classes` over `NOTES` and reads no other
  field — in particular NOT `NoteSpec.discriminator`, whose two values name branches the census rules
  ABSENT (§5.5, §1.3 rule 7); note that `shape_classes` legitimately carries the string `pure_digit`
  for this same specimen, because a census class id for a branch-backed row IS the `branch_id`, which
  is the adjacency that hid the defect.
  verify: test_every_census_corruption_class_has_a_specimen_with_a_verdict

- [x] **Task 7 — AC-4: the skip surface, per repository.** Fill `SKIPS`, `LOADABLE` and `RESOLVABLE`
  in the manifest per §3 and §5.4 — `LOADABLE` being the `get_all()` quantity, with the collision
  arithmetic stated in §3 applied. Add
  `test_the_skip_surface_over_the_corpus_equals_its_declared_reasons`: derive the repository set
  from `repositories.__all__` filtered to concrete `BaseRepository` subclasses, assert it non-empty
  and of size exactly 4, instantiate each against a materialized vault and assert `SKIPS`'s key set
  equals `{repo.type_name}`; assert `skip_reason_return_values(...) == SKIP_REASONS` and
  `SKIP_REASONS` non-empty of size 3; assert the union of the four mappings' reasons EQUALS
  `SKIP_REASONS` and that each member has at least one specimen; then legs (a), (b) and (c) of §5.4.
  verify: test_the_skip_surface_over_the_corpus_equals_its_declared_reasons

- [x] **Task 8 — AC-5: the containment wall.** Add `NAME_POOL`, `CONNECTIVE_SET`, `PROSE_ALLOWLIST`,
  `IDENTITY_FIELDS` and `RESERVED_ISBN` to the manifest, and the extractor of §6.1 to
  `tests/test_fixture_vault.py`. Add `test_no_corpus_note_carries_a_live_identifier` asserting
  census fixity first, then legs (a) through (e) per §6.2-§6.4 over the full reach (every file under
  `tests/fixtures/vault/` plus `tests/fixture_vault.py`): reserved ranges, whose scan runs over
  `excise(text, DECLARED_HEX_LITERALS)` and NOT over the raw text — `DECLARED_HEX_LITERALS` being
  `{CORPUS_DIGEST} | {s.raw_bytes_hex for s in NOTES.values() if s.raw_bytes_hex}` plus the optional
  `CENSUS_DIGEST` restatement, each asserted first to be well-formed lowercase hex of even length
  (64 for either digest) and asserted to OCCUR SOMEWHERE IN THE REACH — the union of every scanned
  file's bytes, asserted ONCE against that union and NEVER per file, while the excision itself runs
  over every file's text whether or not that file holds the literal — so an exemption declared for a
  literal absent from the whole reach is RED while the ~50 corpus notes that legitimately carry none
  of them are not (§6.4, AC-5(a); without the excision the leg is RED by construction, because
  `type:` hex-encodes to `747970653a` and its first nine characters are a phone-shaped run); the
  position-split name
  closure with `PROSE_ALLOWLIST` asserted DISJOINT from the identity token set and not a term in the
  identity assertion; `CONNECTIVE_SET` asserted equal to the literal in AC-5(b); `NAME_POOL`
  non-vacuity over IDENTITY positions only; `NAME_POOL ⊆` the census pool table with the table
  disjoint from `CONNECTIVE_SET`; the non-UTF-8 member's declared lowercase hex bytes asserted
  byte-equal; `normalize_phone` / `phones_match` still holding over every reserved number; and no
  `/Users/` and no absolute path anywhere in reach.
  **THEN, IN THE SAME CHECK, THE THREAT MODEL'S `M1` — THE CENSUS'S OWN BYTES JOIN THE CLOSURE THEY
  CERTIFY (§6.5).** Add a `CENSUS_PROSE_ALLOWLIST` frozenset to `tests/test_fixture_vault.py` — NOT
  to the manifest, whose three literal frozensets AC-5(b) names and freezes — holding the census's
  ordinary technical vocabulary and nothing else. **Author its members from the LANDED artifact and
  never from §6.5 item 3's illustrative list: the set is exactly this scan's own residue over
  `docs/vault-shape-census.md` as it stands** (the landed file needs at least `DaveRemoteVault` and
  `Obsidian`, both at `:17`, which no surface in this document names), and a token you cannot place
  as the census's technical vocabulary is M2's abort at Task 3 rather than a member added here.
  Then, after the census-fixity assertion has already
  run and before any of the artifact's rows is trusted, decode the WHOLE of
  `docs/vault-shape-census.md` with `errors="replace"`, run the SAME `identity_tokens` object leg (b)
  calls over prose and fences alike, and assert that every token it yields is in the artifact's own
  `{row.token for row in census pool rows}`, in `CONNECTIVE_SET`, admitted by `str.lower() in
  _GENERIC_ORG_SUFFIXES`, or in `CENSUS_PROSE_ALLOWLIST` — and that `CENSUS_PROSE_ALLOWLIST` is
  DISJOINT from that pool-row token set, which is what stops it becoming the bypass AC-5(b)'s own
  `PROSE_ALLOWLIST` was found to be at round 2. Assert the pool-row token set is NON-EMPTY first
  (LESSONS #46: a reader that finds nothing admits everything). This scan does NOT extend leg (e)'s
  absolute-path rule to the census, which the threat model recorded rather than folded and which is
  routed against here rather than re-decided. The census is READ and never written: it stays on
  `## Scope Boundary`'s unchanged list and this task adds no `## Write Targets` path for it (§10 P-9).
  verify: test_no_corpus_note_carries_a_live_identifier

- [x] **Task 9 — Drive the extractor's claimed shapes through the extractor (WI-235).** AC-5's whole
  wall is a token count, and `matches == 0` is satisfied identically by an extractor that resolves
  every claimed shape and by one that resolves almost none. Add
  `test_the_identity_token_extractor_resolves_its_claimed_shapes`, driving PLANTED strings through
  the SAME `identity_tokens` function the live legs call, never a re-implementation. Shapes that MUST
  yield the stated tokens: `McDonald` → `{McDonald}`; `Zeta-9` → `{Zeta}`; `José García` →
  `{José, García}`; `Anne-Sophie Legrain` → `{Anne-Sophie, Legrain}`; `Dave -> Thomas Gatten` →
  `{Dave, Thomas, Gatten}`; `Me to David Field` → `{Me, David, Field}`; a `[[Voxleaf Kelmarra]]`
  wikilink → `{Voxleaf, Kelmarra}`. Near-misses that must NOT yield a token: `d'Angelo`;
  `zArchived - Rosie` → `{Rosie}` and never `Archived`; `zzArchived`; `-Voxleaf`;
  `447700900123`; `dave@example.com` → `{}` from its lowercase runs.
  **And the SAME treatment for leg (a)'s reserved-range predicate, because §6.4's hex excision is a
  NARROWING and WI-235's rule is that a narrowing nobody drives can silently swallow the claimed
  shapes.** In the same test, drive planted strings through the SAME phone/email/URL predicates the
  live leg calls — `reserved_phone_violations`, `reserved_email_violations` and
  `reserved_url_violations` by name (§6.4), the same function OBJECTS leg (a) calls and never a
  re-typed regex. **Every literal below was worked through §6.4's three phone patterns by hand, and
  the earlier draft's phone battery did not survive that pass — two of its six fixtures were RED
  against fully correct code, which is the WI-149 shape and is recorded rather than quietly fixed.**
  It listed `(555) 015-0123` as ACCEPTED (`normalize_phone` → `5550150123`, which fails
  `^1?\d{3}55501\d{2}$`: the NANP fictional form is NPA-555-01XX, so the `555` must be the EXCHANGE
  and not the area code) and `+1 415 555 0199` as REFUSED (→ `14155550199`, which MATCHES that
  pattern through the `1?` arm — `555-0199` is squarely inside the fictional block). The corrected
  battery, each fixture given with the digits-only value the predicate actually sees. Must be SCORED
  and ACCEPTED: `+44 7700 900123` (→ `447700900123`), `07700 900456` (→ `07700900456`, the national
  spelling of the SAME drama block and the reason §6.4 carries two UK patterns rather than one),
  `(415) 555-0123` (→ `4155550123`) and `+1 415 555 0199` (→ `14155550199`, the
  optional-country-code arm). Must be SCORED and REFUSED (so the wall is not vacuous):
  `+44 7700 901234` (→ `447700901234` — the near-miss ONE digit outside the drama block, and
  exactly the shape §6.4's earlier `^44770090\d{4}$` tail would have admitted, so this fixture is
  what holds the tightening in place), `+44 20 7946 0958` (→ `442079460958`),
  `t.kelmarra@voxleaf.co` and `https://linkedin.com/in/someone`. Must be EXCISED rather than scored:
  the exact `CORPUS_DIGEST` string, the exact `raw_bytes_hex` string. Must still be SCORED even
  though it looks like the exempt class: a ≥9-digit run that is a PREFIX or SUFFIX of no declared
  literal, and a lowercase-hex-shaped run that is not one of the declared literals — the excision is
  by NAME and by equality, never by shape, and this is the near-miss that proves it.
  **On the planted literals themselves, because `## Scope Boundary` says this item "declines to add
  more" real-looking data and `tests/test_fixture_vault.py` is the ONE new module AC-5's reach
  deliberately excludes — so nothing walls what is typed here.** The two fixtures that were
  real-looking identifiers rather than package vocabulary are GONE from the list above:
  `naomi@speechmatics.com` (a real-looking address at a real company, already in the tree at
  `tests/test_name_validation.py:268`, `:274`, `:453`) is replaced by `t.kelmarra@voxleaf.co`, and
  `+44 7911 123456` (a live allocatable UK mobile prefix, in the tree nowhere) by
  `+44 20 7946 0958`, which is Ofcom's reserved London drama block — it can never ring AND it is
  outside every range leg (a) admits, so it proves refusal strictly better than a number that might
  belong to someone. `voxleaf` and `kelmarra` are this document's own constructed vocabulary and name
  no real person or organisation. **The NAME fixtures stay, and that is the deliberate reading rather
  than an oversight:** `José García`, `Anne-Sophie Legrain`, `Dave -> Thomas Gatten`, `Me to David
  Field` and `zArchived - Rosie` are the PACKAGE'S OWN declared specimens — `name_validation.py:217`
  and `:241` carry two of them verbatim in their branches' `specimen=` fields, and the rest are the
  shape examples `tests/test_name_validation.py:363`, `:377`, `:442`, `:446` and
  `tests/test_name_cleaning.py:35` already commit — and the extractor's whole job is to resolve
  exactly the shapes this package declares, so a constructed substitute would test a shape the
  package does not have. Re-typing a literal already committed in this tree adds no personal data
  and is what "declines to add MORE" means; introducing a new real-looking identifier is what it
  forbids, and the two above were the only instances.
  verify: test_the_identity_token_extractor_resolves_its_claimed_shapes

- [x] **Task 10 — D5's proof set.** Per §9.1: in `tests/test_parser.py` delete
  `TestParseMarkdownFile.test_parse_file` and add top-level
  `test_corpus_person_note_parses_to_its_declared_values`, which materializes the corpus into
  `tests/support.temp_dir()`, parses the declared `person` representative and asserts the manifest's
  declared `fields`. In `tests/test_writer.py` delete `TestRoundtrip.test_roundtrip_preserves_data`
  and add top-level `test_corpus_note_round_trips_through_the_write_door`. In
  `tests/test_repositories.py` ADD top-level `test_corpus_vault_loads_through_every_repository`
  asserting each repository's `LOADABLE` count over a materialized corpus; do NOT touch `temp_vault`.
  verify: test_corpus_person_note_parses_to_its_declared_values test_corpus_note_round_trips_through_the_write_door test_corpus_vault_loads_through_every_repository

- [x] **Task 11 — Close the skip-reason vocabulary's other homes, ALL THREE, and land the wall that
  keeps them closed.** §4's disposition table is the scope and it is a grep's output, not a memory's.
  (a) In `tests/test_loud_fail_load.py`, replace the hand-typed three-string set at `:187-188` with
  `SKIP_REASONS` — strictly stronger, not merely tidier (a fourth reason with no specimen in that
  module's matrix vault goes RED where the hand-typed set stays green). (b) In the SAME function,
  twenty-two lines down, `:209`'s `n.reason == "unreadable"` reads the `UNREADABLE` constant. (c) In
  `tests/test_name_gate.py:152`, `assert _skip_reason(exc) == "unreadable"` reads `UNREADABLE`. All
  three import from `obsidian_schemas.repositories.base`; no assertion changes meaning, because each
  constant's value is the string it replaces. Leave `base.py:37`'s `#` type comment and
  `errors.py:112`'s prose docstring untouched — §4 rules both KEPT, and the wall below cannot see
  either. (d) Then add the LIVE set-equality to
  `test_skip_reason_declaration_binds_to_its_functions_returns`:
  `skip_reason_literal_sites(python_files_under(PACKAGE_ROOT, TESTS_ROOT), SKIP_REASONS) ==
  {"obsidian_schemas/repositories/base.py", "tests/test_fixture_vault.py"}`. It lands in THIS sitting
  rather than Task 2's because this is the sitting that makes it true, so no task is ever verified
  against a red; Task 2 already proved the predicate against planted shapes. This is the fold that
  closes the CLASS rather than the three instances (§11, W-15): a fifth hand-typed site anywhere
  under `obsidian_schemas/` or `tests/` is RED with the file named, and its remedy is one import.
  verify: test_skip_surface_detail_is_bounded test_skip_reason_declaration_binds_to_its_functions_returns

- [x] **Task 12 — Run every wall's own predicate against the final text, and the floor.** For each
  row of §11 whose universe GROWS with this item's files (W-1, W-2, W-8, W-10, W-14, W-15), CALL that
  wall's own shipped predicate on the final bytes rather than reasoning about which shapes match, and
  **every one of the six rows below either names the callable it calls or declares that it has none,
  because "the scan must return zero offenders" is a reasoning-about-shapes instruction wearing a
  predicate's clothes — the class this round closes, not the two rows that raised it:**
  `{use.module for use in modules_using_ast(python_files_under(PACKAGE_ROOT, TESTS_ROOT))}` must
  equal `{"tests/derivations.py"}`, which is W-1 AND W-2 in one call because W-2's row is the
  IDENTICAL live assertion re-run from a second module (§11) and re-typing it here would be the
  re-implementation this task exists to forbid. **The PROJECTION is part of the call and not
  shorthand for it, corrected 2026-09-08:** `modules_using_ast` returns a list of USE RECORDS, not
  module ids (`tests/derivations.py:630`), and the shipped wall this row anchors on projects them
  itself — `homes = {use.module for use in live}` at
  `tests/test_name_gate_wall.py:_check_the_ast_capability_stays_single_homed:1136-1138`. An earlier
  draft wrote the call unprojected, comparing a list of records against a set of strings, which is
  the one row of the six whose stated form does not typecheck in the task whose whole subject is
  CALLING predicates rather than reasoning about them; for W-8, import `_scanned_markdown_files` and `NO_ARG_CONSTRUCTION`
  from `tests/test_vault_path_required.py` (`:421` and `:382`, private and imported by name on
  purpose — this is the wall's OWN generator and matcher, and the alternative is re-rolling its
  exclusion set) and assert first that the generator's output INTERSECTED with
  `tests/fixtures/vault/` is non-empty and equals the corpus's own file set — the non-vacuity clause,
  without which "zero offenders" is satisfied identically by a scan that never reaches the corpus —
  and then that `NO_ARG_CONSTRUCTION.search` finds nothing in any of them, read with
  `errors="replace"` exactly as `:451` does; `skip_reason_literal_sites` must return the two declared
  homes. **W-14 is the one row with no callable predicate, and it is declared LOUDLY here rather than
  skipped or quietly reasoned (WI-301).** pytest ships no importable "would this path be collected"
  membership function in the build profile, and `tomllib` is 3.11-only against P-7's ≥ 3.10 floor, so
  the strongest available arm is to drive the CONFIG'S OWN declared values: a module-level helper
  `_declared_pytest_python_files()` reads `pyproject.toml`'s text, locates
  `[tool.pytest.ini_options]` and returns the `python_files` list, RAISING `AssertionError` naming the
  file when the section, the key, or a parseable bracketed list of quoted globs is absent — it must
  never default to `test_*.py`, because a silent default is a green over a config that moved. Then
  assert with `fnmatch.fnmatch(path.name, pattern)` that NO path under `tests/fixtures/vault/` and not
  `tests/fixture_vault.py` matches any declared glob, that `tests/` gained no `conftest.py`, and — the
  near-miss control that stops the matcher passing by matching nothing (WI-235) — that
  `tests/test_fixture_vault.py`'s own name DOES match one of them. **W-10's arm is the paragraph that
  follows, and its callable is `check_module` — six rows, five shipped callables and one declared
  absence, with nothing left to reason about. The check-name uniqueness
  obligation is DERIVED, never counted:**
  for every top-level `def test_` this item's write targets define — read from those modules' own
  source at test time, never from a list in this plan — `tests/test_ac_interpreter.py`'s shipped
  `check_module` (`:76-87`) must resolve it to exactly one `tests/test_*.py`. That covers this item's
  five `check:` names and every other test it adds with one predicate, and an earlier draft of this
  task said "the six new check names" against a plan that defines twice that many — the drift a count
  invites and a predicate cannot, which is why no number is written here even now that this round has
  added one more test to this very task. Add
  `test_the_fixture_vault_files_close_their_wall_memberships_by_running_each_predicate` recording
  those runs as standing assertions. **Its name says WHOSE walls it grades, and that is a correction
  rather than a style choice:** an earlier draft of this task called it
  `test_wall_membership_is_closed_by_running_each_walls_predicate`, which
  `tests/test_name_gate_wall.py:1057` has defined since WI-022 (that item's Task 16 `verify:`,
  `docs/write-door-bypasses.md:4593`) — and it is the CALLER, at `:1073`, of the very
  `_check_the_ast_capability_stays_single_homed` helper (`:1132`) §11 W-1 anchors on. `check_module` is a
  `def <name>(` SUBSTRING scan that RAISES on anything but exactly one match
  (`tests/test_ac_interpreter.py:76-87`), so the old name would have made THIS task's own derived
  uniqueness assertion raise `resolves to 2 module(s)` over THIS task's own file, and its `verify:`
  declaration irresolvable under the conveyor's D10b rule — with the only other remedy sitting in
  another item's shipped wall, which `## Scope Boundary` forbids touching. The collision was also
  conceptual, not merely lexical: WI-022's function runs every standing wall's predicate over ITS
  item's final text, so both names must say whose. P-6 carries the sweep that found it.
  **Then close W-16 by RUNNING it, which is the only thing that can prove §3.1's bridge
  is actually there:** add `test_this_items_checks_pass_under_the_conveyors_interpreter`, which takes
  the check names from `criterion_checks(<repo root from this module's own __file__> / "docs" /
  "vault-fixtures.md")` — the shipped, fence-scoped reader at `tests/test_ac_interpreter.py:57-73`,
  imported from that module along with `check_module` and `run_foreign`, the root derived from
  `Path(__file__).resolve().parent.parent` exactly as `tests/derivations.py:28` and
  `tests/test_ac_interpreter.py:38` derive theirs and never from the cwd, so only `check:` keys
  inside a
  ```criteria fence are read and this document's gate sections cannot contribute — asserts the list
  is non-empty and of size exactly 5 (LESSONS #46: a fence reader that finds nothing is green), and
  for EACH name runs the shipped `run_foreign(check_module(name), name)` (`:90-95`) and asserts
  BOTH HALVES OF THE SHIPPED ORACLE, not exit 0 alone: `proc.returncode == 0` AND
  `"[ac_interpreter]" in proc.stderr`, failing with the child's captured stdout and stderr. **The
  delegation marker is the half that makes the run mean anything and it is copied from the wall this
  task imports, not invented here** — `tests/test_ac_interpreter.py:111-115` asserts the exit code
  and `:116-120` the marker, the latter's own message being "exited 0 WITHOUT delegating — the
  foreign interpreter imported the project's deps, so this run proves nothing about the battery's
  conditions". `-S` strips `site`, not an ambient or CI install, so on an interpreter where pydantic
  survives `-S` every check exits 0 having never delegated; asserting exit 0 alone would make this
  test green over a run that proves nothing and would stop mutation 9 from ever firing, which is a
  count-of-exit-codes oracle with no shape and no near-miss (WI-235). **And add the near-miss the
  shipped module carries, as its own check:** `test_a_nonexistent_check_is_red_under_the_conveyors_interpreter`,
  which takes `criterion_checks(...)[0]`, resolves its module with `check_module`, calls
  `run_foreign(module, "test_this_check_does_not_exist_anywhere")` and asserts the return code is
  NON-zero AND that `"[ac_interpreter]"` is in the child's stderr — so the bridge cannot pass by
  exiting 0 whatever the child did, and the failing run is proven to have gone through the bridge
  rather than around it. That is `tests/test_ac_interpreter.py:126-138`'s own shape driven over this
  document's fences; both additions are the shipped module's own assertions, so neither is a
  re-implementation and neither adds a predicate. Three shipped predicates, no
  re-implementation. **Anything the RUN returns that §11 did not name is NAMED in the Build Log and
  SATISFIED — never worked around, and never satisfied by narrowing the wall.** Then run the floor
  command and record the passing case count and the wall-clock beside Task 1's baseline; it must be
  GREEN and the count must be higher.
  verify: test_the_fixture_vault_files_close_their_wall_memberships_by_running_each_predicate test_this_items_checks_pass_under_the_conveyors_interpreter test_a_nonexistent_check_is_red_under_the_conveyors_interpreter

---

## Verification

**Happy path — the smoke test.** From the repo root, the floor command
(`.venv/bin/python -m pytest tests -q`) is GREEN, with a case count higher than Task 1's baseline.
The count is INFORMATIONAL and no check asserts it; the invariant asserted is the property (GREEN,
zero errors), because a hardcoded number is a value nobody recorded by the time the assertion runs.
The single-sentence functional smoke: a new test calls `materialize_vault(tmp_path)` and gets ~50
notes carrying accents, hyphenated surnames, an address in a name field, the same person three
times, notes that will not parse, and one of every entity type, without typing a note.

**Failure modes that must fail LOUDLY and be seen to.** Each is a mutate-and-observe act recorded in
the Build Log, and each mutation is REVERTED:

1. Edit one byte of one corpus note → AC-1(a) RED with the digest mismatch named.
2. Delete a corpus note → AC-1(a) RED, and AC-2 or AC-3 or AC-4 RED depending on what it carried.
3. Replace `materialize_vault`'s `write_bytes` with `write_text` → RED on the non-UTF-8 member with
   a `UnicodeDecodeError`, which is leg (b)'s point.
4. Point `materialize_vault` at `repo.save()` → `NameGateRefusal` on the arrow-connective and
   path-hostile members — §1.3 rule 7's two `discriminator` members, which carry
   `shape_classes = ()` and are named by `NoteSpec.discriminator` — AC-1(c) RED.
5. Add a fourth arm to `_skip_reason` without a `SKIP_REASONS` member → AC-4 RED at the scan
   equality. Add the member without a corpus specimen → AC-4 RED at the union equality.
6. Edit one byte of `docs/vault-shape-census.md` → AC-3(iv) AND AC-5(c) both RED. Both, not one:
   that is why the leg is asserted twice.
7. Flip a MEASURED census row to `status: ABSENT` with `count: 0` and drop its specimen → RED at
   AC-3(iv) before any row is read, which is the exact forgery round 8 found unguarded.
8. Put a token in a `name:` that is not in `NAME_POOL` → AC-5(b) RED, and adding it to
   `PROSE_ALLOWLIST` does not clear it (the disjointness assertion).
9. **Delete `ensure_project_interpreter(__file__)` from `tests/test_fixture_vault.py` → the FLOOR
   STAYS GREEN, and `test_this_items_checks_pass_under_the_conveyors_interpreter` goes RED with the
   child's `ModuleNotFoundError: No module named 'pydantic'` on five of five checks.** This is the
   most important mutation in the list and the only one whose green half is the finding: the floor
   cannot see this defect, which is why §3.1 exists and why W-16 is closed by running rather than by
   reading source text. **It fires only because that check asserts the DELEGATION MARKER as well as
   the exit code** (Task 12, §11 W-16): on an interpreter where the project's deps survive `-S` — an
   ambient or CI install rather than a venv — the mutated module still exits 0, and an exit-code-only
   oracle would report this mutation GREEN. The marker is what proves the child actually lacked
   pydantic, so it is what makes this line an observation rather than a claim.
10. Hand-type `"unreadable"` into any module under `obsidian_schemas/` or `tests/` → W-15 RED naming
    that file. Put it in a `#` comment or in running docstring prose instead → still GREEN, which is
    the discrimination §4 requires and the reason the wall reads syntax rather than text.
11. Add `shutil.rmtree(dest)` to the top of `materialize_vault` → AC-1(b) RED on the surviving
    foreign file, which is the no-clean rule that had no test before this round.
12. Remove §6.4's hex excision → AC-5(a) RED on `747970653` inside `raw_bytes_hex`, over a corpus
    that is entirely correct. Widen the excision from named literals to a hex-SHAPED rule → Task 9's
    near-miss (a lowercase-hex-shaped run that is not a declared literal) goes RED, which is what
    stops the exemption becoming a padding surface.
13. **M1.** Add an uncertified identity token to `docs/vault-shape-census.md`'s PROSE — a plausible
    surname in a bullet beneath a class row, which no fence parses and which every check in this
    document passed before this round → AC-5 RED naming that token, and AC-3(iv)/AC-5(c) RED first at
    the digest. Add it to `CENSUS_PROSE_ALLOWLIST` instead → still RED, if the token is also a
    pool-table row (the disjointness assertion); and if it is not, the token is now typed into a
    declared set a human reviews, which is the bar AC-5(b) sets for the corpus and the most a
    structural wall can do about a value nobody can check against a vault the suite cannot read.
14. **M1's own vacuity.** Point the census scan at a file with no `census-pool` fences → RED at the
    non-empty pool-row assertion rather than green, because an empty admitted set admits nothing and
    a scan over a file with no tokens admits everything (LESSONS #46).
15. **The two-field split (spec review round 4, finding 2).** Move the two AC-1(c) discriminators'
    branch ids from `NoteSpec.discriminator` into `shape_classes` → AC-3(i) RED, because
    `arrow_connective` and `path_hostile` are ABSENT rows and the covered-class set now exceeds the
    MEASURED set. Empty `discriminator` on both instead → AC-1(c) RED at the `⊇` assertion. The
    corpus is buildable exactly one way, which is the point of the split.

**Mutate-and-observe is not sufficient and Task 9 is the complementary half.** The mutations above
are authored from the same mental model as the code; the extractor's claimed match-shapes are driven
through the extractor's OWN predicate as GREEN fixtures on every floor run, with near-misses that
must NOT match, so the wall cannot pass by matching everything and then be narrowed back with nothing
checking that the narrowing kept the claimed shapes.

**Integration — what downstream must still work.** `obsidian_schemas` gains one module-level
constant and no signature change, so HAL9000, Exocortex and orchestrator (all `-e` installs) are
unaffected; `pyproject.toml:38-39` packages `obsidian_schemas` only, so nothing under `tests/`
reaches them either way (P8). No consumer smoke test is prescribed, because there is no change for
one to exercise.

**Regression — DERIVED from the edited surfaces, not inherited, and THE PREDICATE IS STATED BEFORE ITS
OUTPUT because an earlier draft's did not generate the list written under it.** The predicate is
"modules AFFECTED BY AN EDIT to this `## Write Targets` path", which has three arms and needs all
three — a module can be affected without naming the path: (A) it NAMES the path or IMPORTS the
module in its own text; (B) it reaches the path through a DIRECTORY SWEEP it did not name the file
in (`python_files_under(PACKAGE_ROOT, …)`); (C) it EXERCISES the edited code at run time. Every
module below was placed by reading it, and each row says which arm put it there. Every one must still
pass:

- `obsidian_schemas/repositories/base.py` → **arm A, the six that name it** (`repositories/base.py`,
  `repositories.base` or `from …repositories import base` in their own text):
  `tests/test_vault_path_required.py`, `tests/test_name_gate_wall.py`, `tests/test_name_gate.py`,
  `tests/test_loud_fail_parse.py`, `tests/test_loud_fail_load.py`,
  `tests/test_company_name_contract.py`. **Arm B, two more:** `tests/test_write_routing.py`
  (`python_files_under(PACKAGE_ROOT, SCRIPTS_ROOT)` at `:91` and `:370`) and
  `tests/test_concurrent_access.py` (`python_files_under(PACKAGE_ROOT)` at `:1074`), both of which
  grade `base.py` without ever naming it — this is the arm that makes the four count pins at
  `:1077-1089` (§11) part of this item's regression surface. **Arm C, one:**
  `tests/test_repositories.py`, which instantiates every `BaseRepository` subclass and is also a
  Task 10 target.
- `tests/derivations.py` → **arm A, and the count is TEN, not twelve — this is the sweep's actual
  output rather than a remembered list.** The ten modules carrying `from tests.derivations import`:
  `tests/test_write_routing.py` (`:22`), `tests/test_name_gate_wall.py` (`:57`),
  `tests/test_loud_fail_write.py` (`:23`), `tests/test_loud_fail_parse.py` (`:43`),
  `tests/test_loud_fail_load.py` (`:23`), `tests/test_loud_fail_harness.py` (`:23`),
  `tests/test_lint_vault_fix_gate.py` (`:33`), `tests/test_company_name_contract.py` (`:55`),
  `tests/test_address_splitter.py` (`:44`) and `tests/test_concurrent_access.py` (`:1064`, a
  function-local import inside `test_wi020_derivations_survive_the_routing`). **The two an earlier
  draft listed here do NOT belong to this row and the correction is recorded rather than silently
  applied:** `tests/test_vault_path_required.py` contains no occurrence of the string `derivations`
  at all, and `tests/test_name_gate.py`'s single occurrence is the one-line docstring mention at
  `:15`. Neither imports the module. Both are already in the `base.py` row above, correctly, so the
  error cost nothing at build — it is corrected because this paragraph advertises itself as derived
  and `## Intent`'s exhaustion claims are read as true, which is the standard the fifth instance of
  this document's stated-number-versus-actual-list family has to be held to.
- `tests/derivations.py`, second arm — **the six test modules that NAME the path in a one-line
  single-homing declaration without importing it**, whose declaration this item's edit to
  `derivations.py` must leave true: `tests/test_name_gate.py` (`:15`),
  `tests/test_name_gate_identifiers.py` (`:32`), `tests/test_name_gate_refusals.py` (`:32`),
  `tests/test_name_gate_delta_rule.py` (`:28`), `tests/test_phone_normalization.py` (`:22`) and
  `tests/test_ac_interpreter.py` (`:29`). Two non-test modules under the same root carry the same
  sentence — `tests/support.py` (`:17`) and `tests/ac_interpreter.py` (`:23`) — and are named here
  for the same reason. Adding two scans to `derivations.py` keeps every one of those declarations
  true, because the new capability lands in the single home they name rather than beside it.
- `tests/test_parser.py`, `tests/test_writer.py`, `tests/test_repositories.py`,
  `tests/test_loud_fail_load.py`, `tests/test_name_gate.py` → themselves, in full. The last two are
  Task 11's targets: `test_skip_surface_detail_is_bounded` (`tests/test_loud_fail_load.py:167`, the
  function that holds both `:187-188` and `:209`) and
  `test_name_gate_refusal_is_a_loud_fail_leaf_carrying_a_pattern`
  (`tests/test_name_gate.py:109`, which holds `:152`) must still pass with the constants in place,
  and they must, because each constant's value is the literal it replaces.
- **Read but not written, and named because a regression there is this item's fault too:**
  `tests/test_ac_interpreter.py` — Task 12 IMPORTS its `criterion_checks`, `check_module` and
  `run_foreign` rather than re-implementing them, and `tests/ac_interpreter.py`'s
  `ensure_project_interpreter` is called by the new check module. **`tests/test_vault_path_required.py`
  joins this row for the same reason:** Task 12's W-8 arm imports its `_scanned_markdown_files`
  (`:421`) and `NO_ARG_CONSTRUCTION` (`:382`) so the wall is closed by calling the wall's own
  generator and matcher rather than by re-rolling its exclusion set — which makes a rename of either
  private name this item's red, and is why the module is BOTH here and on `## Scope Boundary`'s
  unchanged list. It is already in the `base.py` row above under arm A, so this is a second reason
  rather than a new module. None of the three files is edited (none is a `## Write Targets` path),
  and every one of their own tests must still pass unchanged. `pyproject.toml` is read by the same
  task's W-14 arm and is likewise unwritten; it carries no tests of its own.

**No incident replay (WI-173), and the reason rather than an omission.** This item is greenfield
against absence: `## Verified Diagnosis` records that no observed breakage is load-bearing anywhere
in this spec, and D-1 through D-7 are facts about what does not exist and about mechanism. There is
no incident to replay and manufacturing one to satisfy the rule would be worse than skipping it. The
one live act this item DOES depend on — the census scan against the real vault — is the conductor's
precondition and is verified by the Implementation Plan's abort gate, not by a close-out replay.

**Corpus-fixture coupling (WI-278).** Every test that reads a file at run time declares which arm it
takes. `tests/fixture_vault.py` reads `tests/fixtures/vault/` and carries FROZEN BYTES with a digest
— arm two, no derivation and no proxy selection. `tests/test_fixture_vault.py` reads
`docs/vault-shape-census.md` and `docs/vault-fixtures.md` and pins them by DIGEST and by fence
grammar respectively, declaring both in its `CORPUS_COUPLING:` line with the property each supplies.
Neither selects a member by size, name or position, and neither rolls a membership glob a leaf
already declares. **M1 adds a THIRD property consumed from `docs/vault-shape-census.md` — its whole
byte stream, prose included, run through this module's own `identity_tokens` (§6.5) — and it is on
the SAME arm by the same mechanism:** the file is frozen bytes as far as this suite is concerned,
pinned by the `CENSUS_DIGEST` assertion that runs before it, so the scan cannot be moved underneath
by an ordinary ship. The `CORPUS_COUPLING:` line names all three properties. It is worth being
explicit that this is not the WI-267 hazard the rule exists for: the docs splitter rewrites
work-item docs on ordinary ships, and the census carries no `id: WI-*` and is not one — and if it
ever were rewritten, AC-3(iv) is RED before this scan runs, which is the loud outcome rather than the
silent one. **Task 12's parity test adds a THIRD read of `docs/vault-fixtures.md` — and its near-miss control
`test_a_nonexistent_check_is_red_under_the_conveyors_interpreter` a fourth, through the same call and
so on the same arm — and takes the
same arm by a stronger route:** it does not roll its own fence reader, it calls
`tests/test_ac_interpreter.py`'s shipped `criterion_checks` (`:57-73`) — the probe whose behaviour
the test consumes — so the coupling is to that leaf's own predicate rather than to a glob or a
layout. Its one live-population assertion, "exactly five `check:` names", is pinned by equality
because this document's `criteria` fences are a FROZEN population once Dave signs (WI-295): a
criterion added later is an AC edit and a re-sign, not ordinary drift. The one way it goes RED for a
non-defect is a future gate round quoting a WHOLE ```criteria fence into this document, and the
remedy is the convention this document already depends on for AC-3(iv) — gate sections quote
criterion TEXT, never a whole fence. Named here so the next gate is told rather than surprised.

---

## Scope Boundary

**What we are NOT doing.**

- **Not migrating the other ten files' inline literals, nor `test_repositories.py`'s `temp_vault`.**
  D5, and §9.1 for the narrowing and its cost.
- **Not shipping the corpus to HAL9000 / Exocortex / orchestrator.** D6, blocked by
  `pyproject.toml:38-39` (P8). Designing for it costs nothing and is taken — the corpus is bytes plus
  a declared manifest, both of which travel — but no export surface is built here.
- **Not property-based testing (Hypothesis).** D4. The honest generator for this domain IS the shape
  census, so Hypothesis is a consumer of this item's output, not a peer of it.
- **Not a performance corpus.** D4, rejected on evidence: the live load is 1,147 people in 1.26s, and
  a corpus large enough to say anything about scale would stop being reviewable by eye, which is the
  property that makes committing it safe.
- **Not WI-026's acceptance.** D7 — `lint_vault.py` is a tool whose job is the whole corpus, and
  LESSONS #27 says such a tool's acceptance runs over the real corpus. This item gives WI-026 a
  FLOOR, not an acceptance.
- **Not retro-scrubbing the 35 real-looking name literals already in the tree (P10).** Out of the
  frozen `## Intent`; this item declines to add more and a sibling should decide about the existing
  ones.
- **Not touching the company Tier-1 arm.** §9.3 — WI-022 shipped its own refusal sweep and this item
  does not duplicate it.
- **Not rewriting the two KEPT skip-reason mentions.** `base.py:37`'s `#` type comment documents the
  declaration two lines beneath it, and `errors.py:112`'s docstring sentence mentions `"unreadable"`
  in running prose. Neither is a transcription of the vocabulary, W-15 reads syntax and so matches
  neither, and `obsidian_schemas/errors.py` stays on the unchanged list below. §4's disposition table
  is the authority; a builder who "finishes the job" by editing them is doing work this spec ruled
  out.
- **Not widening the interpreter bridge beyond this item's own check module.** `tests/test_name_gate.py`
  is a Task 11 write target for one line and does not carry `ensure_project_interpreter`; adding one
  there is a different item's decision and is out of scope here.
- **Not adding a `conftest.py`.** P2 records its absence as load-bearing
  (`tests/derivations.py:9-12`), and `tests/support.py` already supplies the fixture-free equivalents
  a zero-argument check needs.
- **Not renaming, extending or otherwise touching WI-022's
  `test_wall_membership_is_closed_by_running_each_walls_predicate`
  (`tests/test_name_gate_wall.py:1057`).** It is that item's Task 16 `verify:`
  (`docs/write-door-bypasses.md:4593`) and grades ITS item's final text. This item's wall test carried
  the same name in an earlier draft; the collision is resolved from THIS side by the rename in Task 12
  (P-6 carries the sweep), because the other three arms — renaming theirs, extending theirs, or
  widening their module to cover this item — each edit another item's shipped wall.

**Standing authoring rules for this item's own DOCUMENTS, added 2026-09-08 at the threat model round
2's instruction — and stated as ONE class rather than as the two instances that raised them, because
the two are the same generator one surface apart.** *The generator: an identity-shaped value entering
one of this item's artifacts through a surface no wall reaches.* The corpus is walled by AC-5(b); the
census is walled by M1 and M2. What is left over is every OTHER artifact this item writes, and none
of them is walled by anything — `tests/test_vault_path_required.py:387` excludes `docs` from the only
repo-wide markdown scan, and AC-5's reach is `tests/fixtures/vault/` plus `tests/fixture_vault.py`
and nothing else. **These rules are the whole of the closure for that residue and they bind every
actor who writes here — conductor, gate and builder alike. They are outside the hash-signed span and
cost no re-sign.**

- **A gate reporting a LEAKED IDENTIFIER in this item's documents names the value's LOCATION and
  CHARACTER PROFILE, never the value.** A file-and-line citation plus the constructed specimen
  already declared beside it in the census leaves the finding fully legible and fully re-checkable,
  which is what round 1 itself demanded of the census and what the landed census demonstrates is
  practicable — its `stem_name_divergence` bullet describes eight live shapes and quotes none. The
  scar is precise: threat model round 1 found two novel live-vault values in
  `docs/vault-shape-census.md` and, in reporting them, quoted both into `docs/vault-fixtures.md` at
  four prose positions and once inside its own verdict `note:` — so the remediation moved the leak
  one artifact over rather than ending it, and the values were then measured by round 2 as occurring
  in exactly one file in the worktree, which is the same test round 1 used to call them NEW. The
  conductor has since redacted all five positions in place; this rule is what stops the next gate
  re-deriving the mistake with the same good intentions.
- **The same rule binds `tests/test_fixture_vault.py`, which is the ONE module this item adds that
  AC-5's reach deliberately excludes** (it quotes refused fixtures, corruption specimens and
  pre-existing tree literals by design, so an identity scan over it is RED by construction and a
  fourth declared exemption is not worth minting — threat model rounds 1 and 2 both ruled so). Its
  planted literals are governed by hand: **re-typing an identifier ALREADY COMMITTED in this tree
  adds no personal data and is permitted; introducing a NEW real-looking identifier is not.** Task 9
  applies this to the two instances it found and records the reading; the rule is stated here so it
  covers every literal a later task or a later item plants in that module, not only those two.
- **And the rule follows a round into the drawer.** `### Archived Rounds` sends settled gate rounds
  to `docs/vault-fixtures-rounds.md` byte-for-byte, append-only, **never rewritten**, so a value that
  reaches the drawer is past the reach of any redaction. The ORDER is therefore load-bearing and is
  recorded in §10 P-10: redact first, copy second.

**Unchanged files — the builder must not touch these.** `obsidian_schemas/models.py`,
`obsidian_schemas/name_validation.py`, `obsidian_schemas/name_cleaning.py`,
`obsidian_schemas/name_gate.py`, `obsidian_schemas/parser.py`, `obsidian_schemas/writer.py`,
`obsidian_schemas/body_sections.py`, `obsidian_schemas/phone_normalization.py`,
`obsidian_schemas/vault_io.py`, `obsidian_schemas/errors.py`, every repository module except
`base.py`, `scripts/lint_vault.py`, `pyproject.toml`, `pipeline-runners.yaml`, `CLAUDE.md`,
`README.md`, `SESSION_LOG.md`, `state/**`, `docs/vault-shape-census.md` — the last being the
conductor's precondition, which the builder READS and never writes, **and which NEITHER 2026-09-08
threat-model round changes — not round 1's M1 and M2, and not round 2, whose finding asks for no
builder act at all: M1 has the SUITE scan that file's bytes and M2 has the BUILDER refuse
on what it finds there, and neither authorises an edit. If M2's gate fires, the builder STOPS under
the Abort Protocol and hands off; it does not add a pool row, re-word a prose bullet, drop a hyphen
or re-take a digest. Handing the build write access to the ledger AC-3(iv) exists to put out of its
reach would defeat both criteria that read it** — `tests/ac_interpreter.py`
plus `tests/test_ac_interpreter.py`, both of which this item IMPORTS FROM and neither of which it
edits, `tests/test_name_gate_wall.py`, whose `:1057` name this item renames AROUND rather than into
(the "Not renaming, extending or otherwise touching WI-022's …" bullet in the list above), and
`tests/test_vault_path_required.py`, from which Task 12 IMPORTS
`_scanned_markdown_files` and `NO_ARG_CONSTRUCTION` and which it must not edit to make the import
public. **Two files on this list are READ by the build and reading is not touching:**
`docs/vault-shape-census.md` as above, and `pyproject.toml`, whose `[tool.pytest.ini_options]` keys
Task 12's W-14 arm parses — that arm exists precisely so the config is not restated in a test, and a
builder who "fixes" a red there by editing the config has inverted the wall. The tempting
"while I'm here" edits this list exists to stop: widening
`_GENERIC_ORG_SUFFIXES` to make an identity token admissible (§6.2 says why that set is read from the
package and not declared); narrowing a Tier-1 regex to make a specimen behave; and — the new one,
because Task 12 puts the file under the builder's nose — widening
`tests/test_ac_interpreter.py`'s `WORK_ITEM_DOC` (`:40`) from `docs/write-door-bypasses.md` to cover
this item as well. That is another item's wall with another item's scope; this item runs the parity
itself, in its own module, from the shipped predicates (§11, W-16).

---

## Mitigation Folds

**`## Threat Model — 2026-09-08 (round 2)` is the LATEST SPEAKING ROUND on this document**, and it
re-emitted round 1's two `kind: required` mitigation fences BYTE-IDENTICALLY — same ids, same `desc`
text, same `landed:` ordinals — which is why the two records below are unchanged in `desc` and are
fresh against that round rather than against round 1. Each mitigation is folded into `## Design` §6.5
AND into the Implementation-Plan task its fence names. This section carries no rounds, holds exactly
one record per id, and is restated IN PLACE whenever a later threat model runs or a folded task's own
text moves — which it did this round: Task 8's body gained the `CENSUS_PROSE_ALLOWLIST` authoring
clause, so M1's `work:` quote moved with it in the same edit. Round 2's own blocking finding mints no
third mitigation and the round says why: its subject is a settled gate section of this document, no
plan task can carry that remedy, and a `landed: Task N` for it would be false.

```fold
id: M1
desc: Every identity-shaped token in docs/vault-shape-census.md's own bytes — its prose as well as its fence rows — is asserted to be in that artifact's certified pool table, CONNECTIVE_SET, or an admitted _GENERIC_ORG_SUFFIXES member, with any residue in a declared allowlist asserted DISJOINT from the pool table, so the artifact the privacy wall depends on is itself inside the wall.
design: AC-5's check additionally scans the WHOLE of `docs/vault-shape-census.md` — its prose as well as its fence rows — with §6.1's `identity_tokens`, and asserts every token it yields is in that artifact's own certified pool table, in `CONNECTIVE_SET`, or admitted by `str.lower() in _GENERIC_ORG_SUFFIXES`, with the residue in a declared `CENSUS_PROSE_ALLOWLIST` frozenset asserted DISJOINT from the pool table, so the artifact the privacy wall depends on is itself inside the wall.
landed: Task 8
work: THEN, IN THE SAME CHECK, THE THREAT MODEL'S `M1` — THE CENSUS'S OWN BYTES JOIN THE CLOSURE THEY CERTIFY (§6.5). Add a `CENSUS_PROSE_ALLOWLIST` frozenset to `tests/test_fixture_vault.py` — NOT to the manifest, whose three literal frozensets AC-5(b) names and freezes — holding the census's ordinary technical vocabulary and nothing else. Author its members from the LANDED artifact and never from §6.5 item 3's illustrative list: the set is exactly this scan's own residue over `docs/vault-shape-census.md` as it stands (the landed file needs at least `DaveRemoteVault` and `Obsidian`, both at `:17`, which no surface in this document names), and a token you cannot place as the census's technical vocabulary is M2's abort at Task 3 rather than a member added here. Then, after the census-fixity assertion has already run and before any of the artifact's rows is trusted, decode the WHOLE of `docs/vault-shape-census.md` with `errors="replace"`, run the SAME `identity_tokens` object leg (b) calls over prose and fences alike, and assert that every token it yields is in the artifact's own `{row.token for row in census pool rows}`, in `CONNECTIVE_SET`, admitted by `str.lower() in _GENERIC_ORG_SUFFIXES`, or in `CENSUS_PROSE_ALLOWLIST` — and that `CENSUS_PROSE_ALLOWLIST` is DISJOINT from that pool-row token set, which is what stops it becoming the bypass AC-5(b)'s own `PROSE_ALLOWLIST` was found to be at round 2. Assert the pool-row token set is NON-EMPTY first (LESSONS #46: a reader that finds nothing admits everything). This scan does NOT extend leg (e)'s absolute-path rule to the census, which the threat model recorded rather than folded and which is routed against here rather than re-decided. The census is READ and never written: it stays on `## Scope Boundary`'s unchanged list and this task adds no `## Write Targets` path for it (§10 P-9). verify: test_no_corpus_note_carries_a_live_identifier
```

```fold
id: M2
desc: The Implementation Plan's precondition abort gate additionally REFUSES when docs/vault-shape-census.md carries an identity-position token its own pool table does not certify, so a leaking census stops the build before any corpus byte is authored rather than at the last task.
design: The Implementation Plan's precondition abort gate additionally REFUSES, before any corpus byte is authored, when running §6.1's `identity_tokens` over `docs/vault-shape-census.md` yields a token that the artifact's own pool table does not certify and that is neither a `CONNECTIVE_SET` member nor an admitted `_GENERIC_ORG_SUFFIXES` member.
landed: Task 3
work: FIRST, before a single corpus byte is written, re-run the precondition gate above in full and run its M2 arm — the threat model's `M2`, folded here (§6.5). Apply §6.1's run rule to the WHOLE of `docs/vault-shape-census.md`, prose and fences alike, and confirm every token it yields is in the artifact's own `census-pool` token set, in `CONNECTIVE_SET` (`{"Me", "My", "Dave"}`), or admitted by `str.lower() in name_cleaning._GENERIC_ORG_SUFFIXES`, the remainder being ordinary technical vocabulary. If any identity-shaped token is uncertified — a real live-vault name transcribed into a prose bullet, or a hyphen-fused compound whose halves alone are certified — STOP under the Abort Protocol with those exact tokens and their locations in the Build Log. Do not author, amend or normalise a byte of the census, do not add a pool row, do not drop a hyphen, and do not author a corpus against an artifact that will have to be re-authored: the remedy is a conductor pass (one census edit, one re-taken digest, one AC-3(iv) edit, one D4b re-sign), and the whole value of running this at Task 3 rather than discovering it at Task 8 is that ~50 notes have not yet been written against it. THEN create `tests/fixtures/vault/` and write the ~50 notes per §1.1-§1.4, assembled from the landed census, with the SIX MEASURED ids and no others in `shape_classes`, the three-filename collision declared under `stem_name_divergence`, the TWO AC-1(c) discriminators carrying `shape_classes = ()` and their `branch_id` in `NoteSpec.discriminator`, and the `pure_digit` specimen declaring no `phones`. verify: hand-run — the M2 abort gate is a pre-authoring inspection whose whole point is to run BEFORE any artifact exists, and the corpus is inert bytes with no standing check until Task 4 lands the digest and the manifest; both acts are recorded in the Build Log (the gate's uncertified-token result, the file count, the per-type and per-class tally, and the one-member UTF-8 probe), and the standing form of the same predicate is Task 8's M1 assertion.
```

**Why the pair rather than either one alone, stated so the next reader can see the fold is not
duplicated work.** M1 is the STANDING assertion and is what makes the closure durable — it fires on
every floor run, so the census refresh R7 names as certain-eventually cannot reopen this with nothing
to notice. M2 is the SAME predicate one build phase earlier and is what makes the failure affordable:
without it a leaking or wrongly-granular census is discovered at Task 8, after ~50 notes have been
authored against an artifact that must be re-authored, and with every in-cage remedy closed (the
builder may not write the census, and two signed criteria digest it). Neither replaces the other, and
the threat model asked for both for exactly that reason.

**And the second thing M2's arm catches was found by a different gate, which is why the two folds
land together.** The 2026-09-08 spec review's third finding is that the census's pool table certified
identity tokens at WORD granularity while AC-5(b)'s pinned run rule emits hyphen-joined COMPOUND
tokens, so two MEASURED specimens the corpus is obliged to carry could not satisfy AC-5(b) and (c) at
all. Run through `identity_tokens`, M2's gate is precisely the check that catches that — the
uncertified token it names is the compound — so the granularity rule is stated once in `## Write
Targets` and §6.2 and enforced once, here, rather than given a wall of its own.

---

## Risk Analysis

| # | What could go wrong | Likelihood / impact | Mitigation |
|---|---|---|---|
| R1 | **A real person's name enters permanent git history.** The corpus is authored from live-vault shapes; a moment's transcription puts a real surname in a `name:`. | Low / **irreversible** — this package installs `-e` into three repos and its history is permanent. | AC-5(b)'s position-split closure makes it structurally impossible rather than intended: an identity-position token must be in `NAME_POOL`, and `NAME_POOL ⊆` the census's pool table, every row of which carries a conductor-run zero-hit scan. The prose allowlist is unreachable from an identity position and asserted disjoint from it. Residue (all-lowercase values, note bodies, prose fields) is named in §9.5 and covered by the pool table's one-time human review. **AND THE WALL'S REACH NOW INCLUDES THE ARTIFACT THE WALL DEPENDS ON, which is where this risk actually fired (threat model, 2026-09-08):** the census's own prose sat outside AC-5's declared reach, outside §2's parser rule and outside `## Write Targets`'s constructed-token charge, and two real live-vault values were written there — then digested by two signed criteria, so the build would not merely have shipped the leak, it would have asserted it immutable. The instance is closed by a conductor re-author; the CLASS is closed by M1's standing scan over the census's whole byte stream and M2's abort gate one build phase earlier (§6.5, `## Mitigation Folds`), so the next census refresh cannot reopen it with nothing to notice. **AND A SECOND MEMBER OF THE SAME CLASS FIRED ONE ARTIFACT OVER, found by threat model round 2 and recorded here because this cell's "irreversible" rating is one of the three self-descriptions it falsified:** round 1's remediation removed the two values from the census by QUOTING them into this document's own gate prose — four positions plus a verdict `note:` — where no wall of any kind reaches, since `tests/test_vault_path_required.py:387` excludes `docs` from the only repo-wide markdown scan. The instance is closed by the conductor's 2026-09-08 redaction of all five positions in place (§10 P-10(a)); the CLASS is closed by `## Scope Boundary`'s standing authoring rules, which bind every actor writing to this item's documents and to `tests/test_fixture_vault.py` — the one module AC-5's reach deliberately excludes — and which state the ordering that keeps the append-only rounds drawer from freezing a leak past redaction. Those rules are prose rather than a wall on purpose and the reason is stated rather than assumed: this document quotes REFUSED fixtures, corruption specimens and four pre-existing tree literals by design, so an identity scan over it is RED by construction and both threat-model rounds declined to ask for one. |
| R2 | **The census is edited by the build to make a check pass.** `docs/**` is builder-writable in full (P7) and the pipeline's only merge-boundary wall over docs is scoped to work-item docs (P19). | Medium / high — it defeats the ledger AC-3 and AC-5 both delegate their entire oracle to. | AC-3(iv): `sha256` over the census's bytes equals a literal in the SIGNED criterion, which the build cannot reach; AC-5(c) asserts it independently rather than inheriting it. Verification's mutation 7 exercises exactly this route. |
| R3 | **The corpus is authored from the existing test literals instead of the census** — the D2 shortcut, which needs no conductor act and is the cheapest thing available. | Medium / high — the corpus certifies only what the last five authors thought of and is structurally blind to the tail, which is the item's whole reason to exist. | AC-3(i)'s both-directions equality against the census's MEASURED rows; the Implementation Plan's abort gate; and the fact that the census must be in HEAD before the builder is armed (P-1). |
| R4 | **The manifest is generated by parsing the corpus**, so AC-2 asserts the parser agrees with itself. | Medium / high — a green suite that has verified nothing. | Stated in §3 as the rule and in AC-2's `why:` as the single most likely shortcut; the reviewer's tell is a `fields` mapping reproducing the parser's own normalisations. Not machine-checkable, and said so rather than claimed otherwise. |
| R5 | **`LOADABLE` is declared as the file count or `load()`'s return**, and AC-4(c) is off by two because of the three-way name collision. | High / low — it fails LOUD at build, costing a round. | §3 states the arithmetic with the three cache-key rules cited, which is exactly the "declared rather than discovered" economy. |
| R6 | **The census lands in a syntax the reader does not parse** — pipe tables against fences, or a `command` containing `\|`. | Was HIGH before this spec / medium impact. | §2 pins the fence grammar and the `## Write Targets` extension says so above the fences, so the conductor and the builder read one specification. |
| R7 | **A later branch, type, repository or skip reason reddens the floor with no in-cage remedy** — a new Tier-1 branch needs a census row, which needs the live vault. | Certain, eventually / low-to-medium | Named in AC-3's `why:`, in §5.3 and in Edge Cases rather than discovered by whoever pays it. It is LESSONS #45's intended friction and is not weakened here. |
| R8 | **The suite stops being ~1s and hermetic.** ~50 notes byte-copied per materializing test, over five AC checks plus three migrated tests, plus Task 12's SIX foreign-interpreter runs — one per `check:` name plus the near-miss control. | Low / medium | Byte copy of ~50 small files is microseconds; no AC CHECK makes a subprocess, network or live-vault call (P-4). Those six foreign runs are the shape `tests/test_ac_interpreter.py` already performs on every floor run, so the marginal cost is known rather than estimated (P-4b), and Task 12 records the wall-clock beside Task 1's baseline. If a later test materializes in a loop, that is the thing to notice — the floor's wall-clock is the instrument. |
| R9 | **The AC battery reports five-of-five `ModuleNotFoundError` against a green floor.** All five checks execute the library behind pydantic, and the conveyor's interpreter defaults to the ADVANCER's `sys.executable` unless the driver passes `--ac-python` (`tests/ac_interpreter.py:14-20`). | Was CERTAIN before this round / a burned build attempt — WI-021 drew exactly this output, and `docs/identity-engine-endgame.md:2744` records the cost as "a build-exit round bought for nothing". | §3.1 prescribes `ensure_project_interpreter(__file__)` as the check module's first statement, the convention six sibling modules already follow; §11 W-16 and Task 12 close it by RUNNING each check under `sys.executable -S` in the conveyor's shape, because the floor is structurally blind to it (Verification mutation 9). The run asserts BOTH halves of the shipped wall's oracle — exit 0 AND the `[ac_interpreter]` delegation marker (`tests/test_ac_interpreter.py:111-115`, `:116-120`) — plus that module's own nonexistent-check near-miss (`:126-138`), because `-S` strips `site` and not an ambient install: exit-code-only parity is green over a run that never delegated, and this risk would be back untouched. |
| R10 | **A leg goes RED on a wholly correct corpus.** AC-5(a)'s ≥9-digit phone predicate runs over `tests/fixture_vault.py`, which by design carries full-file and digest hex literals; hex-encoded printable ASCII is a digit run. | Was CERTAIN before this round / low impact but a build round each time, and no in-cage remedy the document authorised. | §6.4's named-literal excision, asserted well-formed and asserted present SOMEWHERE IN THE REACH — the union of the scanned files' bytes, never per file, since no corpus note carries a digest and a per-file presence assertion would rebuild this exact risk on ~50 correct notes — with Task 9's near-miss battery stopping it from widening into a shape rule. Same class as the ISBN decision, closed at both members this time rather than at the first. The phone predicate itself is the third member and is closed in the same place: §6.4 admits the drama block in both its spellings, so a note storing the ordinary national `07700 900456` is not RED. **TWO FURTHER MEMBERS OF THIS EXACT CLASS WERE FOUND 2026-09-08 BY THE ONE READ NO PRIOR ROUND HAD DONE — walking the SIGNED criteria against the LANDED census's actual rows rather than against the code — and both are closed in `## Design` rather than by an AC edit, which is the only affordable arm now that the criteria are frozen.** (a) AC-1(c) obliges an arrow-connective and a path-hostile specimen "named in the manifest as such" while the census rules both classes ABSENT, so naming them in `shape_classes` breaks AC-3(i)'s equality and leaving it empty leaves "named as such" unsatisfied: closed by §1.3 rule 7 and `NoteSpec.discriminator`, two manifest fields for two questions, no criterion text touched. (b) The census's pool table certified at WORD granularity while AC-5(b)'s run rule emits hyphen-fused COMPOUNDS, so two obliged MEASURED specimens could satisfy neither AC-5(b) nor AC-5(c): closed by one conductor pass adding the compound rows, by the granularity rule stated in `## Write Targets` and §6.2, and by M2's abort gate catching it before a corpus byte is authored. **The generator behind all four members is one thing and it is named here rather than left for a fifth: a criterion clause whose satisfiability depends on an artifact the criterion cannot see, frozen by signature before anyone walked it against that artifact's actual rows.** The sweep that generalisation demands was run this round over every clause in AC-1 through AC-5 that quantifies over the census, and `## Self-Review Dry Run` records what it found — including one member neither gate raised (§1.3 rule 5's collision, which the census rules ABSENT). |

**Migration path / rollback.** Everything is additive except three one-line constant substitutions:
a new directory, two new modules, one frozenset and three named constants, TWO scan functions, three
test additions, two test deletions, and the three repointed skip-reason literals of Task 11.
Rollback is `git revert` of one commit, and no consumer, no persisted state and no live vault is
touched. There is no shadow mode and none is needed, because nothing in production reads any of it.

---

## Self-Review Dry Run

**Walked the plan top-to-bottom as the builder.** Every task names its files, its exact insertion
points and a runnable check; Task 3's is an inspection and says so with its reason, which is the one
task whose artifact has no standing check until the next task lands. Task 1's floor command is
absolute per CLAUDE.md. No task requires a decision this document does not make.

**Three questions a cold-start builder would plausibly ask, and where each is answered.**

1. *"What exactly do I put in the fifty notes?"* — §1.3's six rules plus the landed census's class
   table and pool table. The spec deliberately does not list fifty filenames, because the list is a
   function of an artifact that does not exist yet; §1.2 pins the grammar so the set is derivable.
   If the census is incomplete, the abort gate says STOP rather than invent.
2. *"Is `LOADABLE` the number of files, or `load()`'s return, or `get_all()`?"* — §3, with the
   three cache-key rules cited and the collision arithmetic worked.
3. *"Where does the `SKIP_REASONS` scan live, and why can't I just put it in the test module?"* —
   §4 and §11 W-1: `ast` is single-homed to `tests/derivations.py` by a set EQUALITY asserted from
   two modules, so a syntax-reading predicate anywhere else is RED by construction.

**Three more, added 2026-09-07 because the first spec-review round asked exactly them and this
document did not answer any of them.** They are recorded here rather than only fixed, because each
was a build round and two had no in-cage remedy:

4. *"Does this check module need the interpreter bridge the other six check modules open with?"* —
   YES, and it is the first executable statement: §3.1 gives the exact preamble, P-4 and P-4b give
   what it does and what it costs, D-8 grounds the claim, §11 W-16 and Task 12 close it by RUNNING
   each check the way the conveyor does. The floor cannot see its absence, which is why no earlier
   round caught it.
5. *"Leg (a) is RED on a nine-digit run inside my own `raw_bytes_hex` literal — is that a corpus
   defect or a criterion I should exempt?"* — Neither: it is a NAMED excision the criterion itself
   authorises. AC-5(a) and §6.4 give the excised set (`CORPUS_DIGEST`, every `raw_bytes_hex`, the
   optional `CENSUS_DIGEST` restatement), the well-formedness and presence assertions that keep it
   from becoming a hiding place — the presence one taken over the REACH and not per file, see
   question 7 — and Task 9's near-miss battery that keeps it from widening into a
   shape rule.
6. *"Do I key the digest on the repo-relative path AC-1(a) names, or on the file name §5.2 hashes?"*
   — On the FILENAME, and both texts now say so. AC-1(a) reads "corpus-relative", which in one flat
   directory is `path.name`; the earlier "repo-relative" wording made leg (b) unsatisfiable, and
   §5.2 records the correction so the agreement is checkable from either end.

**Three more, added 2026-09-07 because the SECOND spec-review round asked exactly them — and two of
the three land on text the first round's own folds added, which is this document's recorded
fold-breeds-its-next-finding shape rather than a re-opening.**

7. *"`CORPUS_DIGEST` is in no corpus note — do I assert the excised literal is present in EACH file,
   or somewhere in the reach?"* — SOMEWHERE IN THE REACH, asserted once against the union of the
   scanned files' bytes, while the excision runs per file regardless. AC-5(a) says it in the text
   that gets signed, and §6.4, Task 8 and `## Edge Cases`'s hex entry repeat it in the same words.
   The per-file reading would be RED on ~50 wholly correct notes and, once these criteria were
   signed, would have had no in-cage remedy except narrowing a signed criterion.
8. *"The shipped wall I am importing from fails a check that exits 0 without delegating — do I
   assert that too, or only the exit code?"* — BOTH, plus the near-miss. Task 12 and §11 W-16 name
   `proc.returncode == 0` AND `"[ac_interpreter]" in proc.stderr`
   (`tests/test_ac_interpreter.py:111-115`, `:116-120`), and add
   `test_a_nonexistent_check_is_red_under_the_conveyors_interpreter` mirroring `:126-138`. Exit code
   alone is a wall-shaped no-op wherever the deps survive `-S`, and it would silently disarm
   Verification's mutation 9 — the one mutation whose GREEN half is the finding.
9. *"The regression list says `tests/test_vault_path_required.py` imports `derivations.py`, and it
   does not name the module at all — which of the two is wrong?"* — The list was. `## Verification`'s
   regression paragraph now states its predicate in three arms before its output and gives the
   sweep's actual result: TEN importers of `tests/derivations.py`, not twelve, with the two
   over-listed modules named and their correct rows given. It cost nothing at build — both were
   already in the `base.py` row — and is corrected because the paragraph advertises itself as derived
   and this document's exhaustion claims are read as true.

**Three more, added 2026-09-08 because the THIRD spec-review round asked exactly them — and unlike
rounds 1 and 2, none of the three lands on folded material. They are in plan text that has stood
since the Design first landed, which is the reason the third is recorded as a rule change rather than
a fix.**

10. *"Task 12 tells me to add `test_wall_membership_is_closed_by_running_each_walls_predicate`, and
    `tests/test_name_gate_wall.py:1057` already has one — do I rename mine, rename theirs, or extend
    the existing test?"* — RENAME MINE, and the plan now carries the renamed name rather than the
    question. Task 12's wall test is
    `test_the_fixture_vault_files_close_their_wall_memberships_by_running_each_predicate`; renaming
    WI-022's is forbidden by `## Scope Boundary`, which puts `tests/test_name_gate_wall.py` on the
    unchanged list, and extending it would put this item's assertions in another item's module.
    P-6 carries the sweep that found the collision and the reason the rename names the item: the
    collision was conceptual as well as lexical, since WI-022's function grades ITS item's final text
    with the same sentence.
11. *"Task 12 says CALL each wall's own shipped predicate — what do I call for W-8 and W-14?"* — For
    W-8, `_scanned_markdown_files` and `NO_ARG_CONSTRUCTION`, imported by name from
    `tests/test_vault_path_required.py` (`:421`, `:382`), with the non-vacuity clause first. For
    W-14 there is NO callable, and Task 12 and §11's W-14 row now say so in as many words rather than
    leaving the builder to infer it: pytest ships no importable collection-membership function in the
    build profile, so the arm is the config's own declared `python_files` globs driven through
    `fnmatch`, read by a helper that raises rather than defaults, with a positive control. Two of the
    task's six rows previously read as predicates and were reasoning.
12. *"Is a name unique because this plan uses it once, or because the tree does not already have
    it?"* — Because the TREE does not. P-6 stated the uniqueness rule correctly and checked it only
    within this item's own additions, which is the one side of the rule that cannot find a collision.
    It now records the sweep run against every `def <name>(` occurrence already in the tree for all
    thirteen names this item adds, and names the one that collided.

**Three more, added 2026-09-08 after the FOURTH spec-review round and the item's first threat model.
All three are of one family, and the family is different from every family before it: none is an
enumeration defect, and none was findable by reading the code. Each is a SIGNED criterion clause
meeting the LANDED census's actual rows for the first time.**

13. *"Task 8 and Task 3 are named as `landed:` sites for M1 and M2 and neither task mentions them —
    do I invent the fold, or am I reading the pre-threat-model plan?"* — Neither: both are folded.
    §6.5 carries the Design half of each with the exact sentence, Task 8 carries M1's standing scan
    and the `CENSUS_PROSE_ALLOWLIST` it needs, Task 3 carries M2's abort-gate arm ahead of its first
    authored byte, and `## Mitigation Folds` records both with `desc` copied verbatim. §10 P-9, which
    asserted for ten rounds that no threat model existed, is rewritten rather than annotated.
14. *"The census rules `arrow_connective` and `path_hostile` ABSENT and AC-1(c) tells me to plant both
    and name them in the manifest — which criterion do I redden?"* — NEITHER. §1.3 rule 7 and §3's
    `NoteSpec.discriminator` give the two obligations two fields: `shape_classes = ()` keeps them out
    of AC-3(i)'s covered-class equality, and `discriminator` — asserted to hold a real `branch_id`, so
    it cannot be padded — satisfies "named in the manifest as such". Task 4 reads `discriminator`,
    §5.5 states that AC-3 reads `shape_classes` and nothing else, and Verification mutation 15 drives
    both wrong answers.
15. *"`identity_tokens` gives me `Brenvik-Tarnquil` and the pool table certifies `Brenvik` and
    `Tarnquil` separately — do I add a row to a file I am forbidden to touch, or drop the hyphen the
    class is named for?"* — Neither, and the question no longer arises: the conductor's 2026-09-08
    census pass added the compound rows, `## Write Targets`'s extension and §6.2 state that a pool
    row's subject is an EXTRACTED token under §6.1's rule with `Anne-Sophie` as the worked case, and
    M2's abort gate refuses at Task 3 rather than reddening at Task 8 if a later pass regresses. If
    the gate ever fires, the answer is STOP — never a pool row the builder writes, never a dropped
    hyphen.

**The WI-226 sweep, run because findings 14 and 15 share a GENERATOR and closing them one at a time
would have left the next member for the next round.** The generator: *a criterion clause whose
satisfiability depends on the census, frozen by signature before anyone walked it against the
census's actual rows.* So every clause in AC-1 through AC-5 that quantifies over the landed artifact
was walked against it, one at a time, rather than only the two the review named. **The sweep found
one member neither gate raised**, and it is closed in the same edit: **§1.3 rule 5's mandated
three-filename collision.** The census rules `same_name_collision` ABSENT (largest live collision:
two) and `stem_name_divergence` MEASURED, so a note declaring `shape_classes =
("same_name_collision",)` is RED under AC-3(i) exactly as an `arrow_connective` declaration would be
— and rule 5 previously deferred the naming to "the CENSUS's ruling", which had not yet been made.
Rule 5 now says the collision is still planted (§3's `LOADABLE` arithmetic needs it) and is declared
under `stem_name_divergence`. The rest of the sweep, declared so the next reader can check it rather
than repeat it: AC-3(iii)'s floor resolves to sixteen rows and the artifact carries sixteen fences;
AC-3(i)'s expected covered set is the SIX MEASURED ids, named in §1.3 rule 2 and in Task 6;
AC-3(ii)'s non-empty-stdout leg is satisfiable at both statuses because every landed command emits a
count; AC-3(iv)'s digest is filled and re-taken; AC-5(b)'s `CONNECTIVE_SET` reconciliation is settled
by the artifact at `{Me, My, Dave}` (P-2(c)); AC-5(c)'s disjointness holds, the landed pool table
writing no row for any connective by design; AC-5(a)'s reserved ranges hold over every landed
specimen, including `pure_digit`'s `447700900123`; and AC-2 quantifies over `TYPE_TO_MODEL` alone and
touches the census nowhere. **The next level of the ladder, swept and declared:** the same question
asked of the OTHER artifact these criteria read — `docs/vault-fixtures.md` itself, via AC-3(iv)'s
fence-scoped digest read and Task 12's `criterion_checks` — returns the "exactly five `check:` names"
pin, which `## Verification`'s corpus-coupling paragraph already prices as a FROZEN population with
its one non-defect RED named. No third artifact is read by any criterion.

**Three more, added 2026-09-08 after the FIFTH spec-review round and the item's SECOND threat model.
They are a third distinct family: not an enumeration defect, not a signed clause meeting the census
for the first time, but a spec-pinned LITERAL never driven through the code that produces it — plus
one gate finding whose remedy was never the spec-writer's at all.**

16. *"Task 6 tells me the `pure_digit` specimen's declared `Verdict` is `pattern="pure_digit"`, and
    the refusal I catch carries `pattern="pure_digit_name"` — is my specimen wrong, is the manifest
    wrong, or is the assertion wrong?"* — **The SPEC was wrong, and it is fixed rather than left to
    the builder's judgment**, which is the whole point: this is the one paragraph in the document
    that tells the builder which verdict they are not free to choose. §5.3 and Task 6 now pin
    `pattern="pure_digit_name"`, traced through `name_validation.py:284-285` → `:678` → `:463` →
    `name_gate.py:365`; §3 states the general rule (a declared refusal `Verdict`'s `pattern` is the
    record's `pattern` field, never its `branch_id`) and carries the seven-item sweep that closed
    the class it belongs to. The defect was invisible because the same word is CORRECT one field
    over: `pure_digit` is the right value for `shape_classes` and for `discriminator`, both of which
    key on `branch_id`.
17. *"The threat model's latest round returned REVISE over a leak in this document and nothing in
    the spec answers it — am I reading a plan that has been superseded?"* — **No, and the plan was
    never the subject.** Threat model round 2's finding was about this document's own gate prose, and
    its remedy had two halves belonging to two different actors: the conductor's redaction (done —
    §10 P-10(a)) and a standing authoring rule (landed — `## Scope Boundary`'s three bullets, stated
    as one class covering the census, this document, `tests/test_fixture_vault.py` and the rounds
    drawer). Neither half touches a task. What DOES stand between this item and `ready` is the
    untaken `ac-signoff` re-sign, which is P-2's and P-10(b)'s and is a Dave act.
18. *"Task 12's W-1 row tells me `modules_using_ast(...)` must return a set of module ids and it
    returns use records — do I project it, or am I calling the wrong predicate?"* — **PROJECT it, and
    the task now says so in the call it prescribes**:
    `{use.module for use in modules_using_ast(python_files_under(PACKAGE_ROOT, TESTS_ROOT))}`, which
    is the shipped wall's own line at `tests/test_name_gate_wall.py:1136-1138`. §11's W-1 row carries
    the same projection. It is the same generator as question 16 one level up — right declaration,
    right field, wrong shape of its return — and is closed in the same sweep.

**Scanned the rest of the document for what these claims now contradict.** Three places needed
reconciling when the Design first landed, the second review round added four more, the third added
three, the fourth added six, and this round adds five. All are reconciled in place rather than left
to a reviewer:

- **The `pure_digit` `Verdict` literal moved in THREE places and nowhere else**, found by searching
  the document for `pattern="` rather than by remembering: §5.3's pinning paragraph, Task 6's
  MEASURED-verdict paragraph, and this section's own reconciliation bullet. §3's `Verdict` field
  comment ("the `NameGateRefusal.pattern` expected") was already right and is what the correction is
  measured against. **AC-3's signed text does NOT move and must not:** it says only "carrying the
  named `pattern` on its `.pattern` attribute", which is true of `pure_digit_name` and was always
  the criterion's own wording — the defect was entirely in `## Design` and `## Implementation Plan`,
  which is why it costs no re-sign. AC-3's capitalised "THE KEY IS `branch_id` AND NEVER `pattern`"
  is about the class FLOOR's key and is likewise untouched and still correct; §3's new rule is its
  complement rather than its contradiction, and both cite the same docstring at
  `name_validation.py:152-154`.
- **`## Scope Boundary` gained three standing authoring bullets and they are declared as covering a
  CLASS, so nothing else in the document has to carry a copy.** Task 9's paragraph about its own
  planted literals is the instance the second bullet generalises and is left in place unchanged —
  it applies the rule and records the two fixtures it moved, which is the reading the rule now makes
  standing. §9.5's "places the machine stops" is unaffected: those are residues AC-5 cannot close by
  machine, while these are rules for surfaces AC-5 does not reach at all.
- **§10 gained P-10 and P-2 gained a paragraph, and between them every act this item owes that is
  NOT the spec-writer's is in one place.** Nothing in `## Design`, `## Implementation Plan` or
  `## Write Targets` moves for any of them — checked, because P-2's own test for what may be fixed
  here rather than escalated is exactly that. The rounds-drawer bullet is the only one with an
  ORDERING constraint and it is now satisfiable in either order, since the redaction is done.
- **`CENSUS_PROSE_ALLOWLIST`'s membership rule is stated in TWO places and they use one wording**
  (§6.5 item 3, Task 8), and Task 8's `work:` quote in `## Mitigation Folds` moved with it in the
  same edit — a fold record whose `work:` no longer reproduces its task's text is stale, and the
  conveyor's D8c rule reads it. M1's `desc` and `design:` are untouched, because the rule narrows how
  the residue set is AUTHORED and changes nothing the mitigation asserts.
- **`base.py:195-198` is now the span at three of the four sites that cite it** — `## Approach`,
  D-7 and `### Constraints discovered` — and AC-4's `desc` deliberately keeps `:196-198`, with the
  reason recorded at the Constraints site so a later round reads a decision rather than a
  divergence. Both spans resolve to the same `file_pattern` property and support the same claim.

- **`CENSUS_PROSE_ALLOWLIST` is declared in `tests/test_fixture_vault.py` and NOT in the manifest,
  and that placement is forced by a signed sentence.** AC-5(b) says `fixture_vault.py` "declares
  THREE literal frozensets and no computed membership" and names them; a fourth there would make
  signed text false and cost a re-sign for a set that is a property of the census rather than of the
  corpus. §3's import list, §6.5 item 3, `## Write Targets`'s `tests/fixture_vault.py` fence ("AC-5's
  three literal frozensets") and its `tests/test_fixture_vault.py` fence all now say the same thing.
  W-15 is unaffected: the extractor only yields runs beginning with an uppercase or non-ASCII letter,
  so no `SKIP_REASONS` member — all three lowercase — can be a member of this set, and the wall's
  two declared homes do not move.
- **§10 P-9 is rewritten from "no `## Threat Model` exists" to the fold's state, and nothing else in
  the document asserted that absence** — checked by searching for the claim rather than by
  remembering. The three earlier spec-review rounds each recorded it in their own gate sections,
  which are settled rounds and are not edited.
- **M1 makes `tests/test_fixture_vault.py` read `docs/vault-shape-census.md` for a THIRD property, so
  `## Verification`'s WI-278 paragraph and §7's integration table both moved with it.** The arm does
  not change: the file is pinned by digest and the fixity assertion runs first. §11's cleared
  paragraph now records that there is no standing wall over `docs/` at all — the measurement behind
  the threat model's finding — and that M1 is a wall this item MINTS rather than one it joins.
- **`## Write Targets` gains no path from either fold, and that is asserted rather than assumed.** M1
  and M2 both READ the census; §10 P-9, Task 8, Task 3 and `## Scope Boundary` each say the builder
  never writes it, and the `kind: precondition` fence is untouched. The two folds' write surface is
  `tests/test_fixture_vault.py`, already declared.
- **`### Examples of done` was NOT edited and its third paragraph is still true.** It says the
  arrow-connective and path-hostile specimens "are refused by the gate", which is AC-1(c)'s
  discriminator property and is exactly what Task 4 asserts; it says nothing about which manifest
  field names them. It sits inside the hash-signed `## Acceptance Criteria` span, so editing it would
  have cost a per-section hash for no correction. `## Design` §5.1's byte-copy argument is likewise
  untouched and untouchable by this fold: it is about the door refusing the specimens, not about how
  the manifest labels them.
- **The `pure_digit` specimen's declared `Verdict` is pinned in TWO places and they agree.** §5.3
  states the `allow_phone_sentinel` narrowing and its AC-3 consequence; Task 6 states the resulting
  declaration (`refusal` / `pattern="pure_digit_name"`, no `phones` on the specimen); Task 3 states
  the authoring rule. Before this round §5.3 stated the narrowing only for AC-2's GATE-CLEAN
  predicate, where it is a harmless over-constraint, and said nothing where it decides a declared
  value. **The VALUE was `pure_digit` until 2026-09-08 and was wrong — the record's `branch_id`
  where its `pattern` was meant — and both sites moved in one edit along with the rule §3 now states
  and the sweep that closed its class.**

- **Task 12's wall test is renamed and NOTHING else in the document moves with it**, checked by
  searching for the old string rather than by remembering: the only two live occurrences were Task
  12's body and Task 12's `verify:` line. `## Verification`'s mutation list, `## Write Targets`, §11
  and the AC fences never named it — every name an AC or a downstream paragraph DOES depend on is
  untouched: the five `check:` names, plus
  `test_this_items_checks_pass_under_the_conveyors_interpreter` and
  `test_a_nonexistent_check_is_red_under_the_conveyors_interpreter`, which mutation 9 and the
  corpus-coupling paragraph name respectively. The rename adds NO `## Write Targets` path: `tests/test_name_gate_wall.py` stays
  unwritten, which is the arm to take, because repointing from that side would edit another item's
  shipped wall.
- **Task 12's W-14 arm introduces the item's first `fnmatch` use and P-7 had to move with it.** P-7's
  stdlib list now carries `fnmatch`, assigns it to `tests/test_fixture_vault.py` alongside
  `unicodedata`, and states the one place the ≥ 3.10 floor is load-bearing — `tomllib` is 3.11-only,
  so the W-14 arm may not reach for it. P-4's hermeticity split is unaffected: the arm reads a file
  and matches strings, and makes no subprocess.
- **Task 4's leg (c) call shape now agrees with §5.3.** Both say the first argument is the note's own
  file path (`<dir> / <filename>`), which is what `writer.py:160-169` takes and what `:205` turns into
  the note's path; the earlier "`<fresh dir>`" spelling left the plan and the design disagreeing about
  a signature, which is the buildable-two-ways shape. The `frontmatter=` arm is kept and its refusal
  path is now traced to `name_gate.py:349-365` and the single `_refuse` site at `:142`, so AC-1(c)'s
  discriminator is grounded rather than assumed.

- `## Approach` says `fixture_vault.py` holds "three things and no test logic". §3 keeps that: the
  census reader, the extractor and every assertion live in `tests/test_fixture_vault.py`, and the
  manifest module gains only declarations plus the two functions `## Approach` already names.
- `## Approach` fixes the package-side scope at exactly two files. §7 and `## Write Targets` name
  FIVE test files beyond the two new ones (`test_parser`, `test_writer`, `test_repositories`,
  `test_loud_fail_load`, `test_name_gate`); none is a package file, so the two-file claim is
  untouched, and D5 already authorises the first three. The last two are Task 11 — three one-line
  constant substitutions, taken because §4's wall asserts set EQUALITY over the vocabulary's legal
  homes and an unrepointed site is RED, so "leave it" was not an available arm. `## Approach` now
  carries a dated amendment saying so, rather than diverging quietly from `## Design`.
- AC-3(iv)'s uniqueness read is FENCE-SCOPED, so this spec's several mentions of the
  `CENSUS_DIGEST` declaration — all outside the AC-3 `criteria` fence — cannot turn it RED. Checked
  deliberately, because a file-wide read would have been broken by this section.
- **`## Approach`'s "three things and no test logic" now has ONE package import in it** (§3), because
  W-15 sweeps `tests/fixture_vault.py` and a re-spelled reason literal there would redden the wall.
  The claim survives: an import is not test logic, and the module still declares and materializes
  and asserts nothing.
- **P-4's hermeticity claim is now split** between the five AC CHECKS (no subprocess, unchanged) and
  Task 12's battery-parity tests (six subprocesses across two floor-graded tests, neither a check).
  R8 carries
  the cost and P-4b says where it is measured. The earlier flat "no subprocess in any check" would
  have contradicted Task 12 the moment it was written.
- **AC-1(b)'s reach grew by one call** — the second `materialize_vault` with a foreign file planted
  — which is why `## Edge Cases`'s idempotency entry no longer resolves a rule nothing exercises,
  and why Verification gained mutation 11. §5.1 states the no-clean rule at the code, so the
  criterion, the design and the edge case now say one thing in three places.
- **`## Verified Diagnosis` gained D-8 and D-9 and its closing paragraph had to move with them**:
  the "D-1 through D-7 are facts about absence" sentence was true and would have read as a claim
  about NINE rows. The paragraph now separates the two kinds and says why neither new row makes this
  an incident-class item.
- **The hex excision's presence domain is stated in FOUR places and they now use one wording**:
  AC-5(a), §6.4, Task 8 and `## Edge Cases`'s hex entry all say "somewhere in the reach, once against
  the union, excision applied per file regardless". R10's mitigation cell carries the same sentence,
  because it was the cell claiming this risk closed.
- **§6.4's phone predicate moved and three things had to move with it.** It now admits the drama
  block in BOTH spellings (`^447700900\d{3}$`, `^07700900\d{3}$`) and pins the block to `900xxx`
  rather than `90xxxx`. AC-5(a)'s parenthetical names both spellings as one range; Task 3's authoring
  rule names both; Task 9's battery is re-derived against the three regexes literal by literal, which
  is what found that two of its six earlier fixtures were RED against correct code. Nothing else in
  the document quotes a phone pattern — `447700900123` at `## Exploration Notes` and in Task 9's
  extractor near-misses is a VALUE and is still accepted by the tightened rule.
- **`unicodedata` left §3's import list and P-7 had to say where it went.** §3 now states its absence
  as the manifest module's boundary, P-7 splits the item's stdlib surface across the two modules, and
  §6.1 — which was always the extractor's home — is unchanged. `## Approach`'s "three things and no
  test logic" is what the correction protects.
- **Task 12 gained a THIRD test and four cost sentences had to move with it.** The new
  `test_a_nonexistent_check_is_red_under_the_conveyors_interpreter` is a top-level `def test_` in a
  declared write target, so W-10's uniqueness rule binds it and Task 12's own derived uniqueness
  predicate covers it without an edit; its name is in the task's `verify:` line. It also makes the
  foreign-run count SIX rather than five, which is stated in §3.1's cost sentence, P-4b, R8 and this
  section's own P-4 reconciliation — every place the old number appeared, found by searching for it
  rather than by remembering. And it adds no `criteria` fence, so the "exactly five `check:`
  names" pin does not move.
- **Task 6 gained the `MEASURED` qualifier and it agrees with AC-3 rather than narrowing it.** AC-3
  already said an ABSENT row "obliges no specimen"; the plan task said "for each floor class" and
  read as demanding a `Verdict` for a class that has none. §9.4 names `empty` as the likely ABSENT
  row, so the qualifier is exercised rather than decorative.

**Bar check.** Design cites `file:line` and quotes the code at every integration point; every
population a criterion sweeps is READ from its declaration and every oracle is hand-declared;
`## Verified Diagnosis` grounds NINE claims in falsifiable artifacts — D-1 through D-7 about this
package, D-8 and D-9 about the build pipeline and this spec's own predicates, separated in the
section's closing paragraph because only the first seven bear on whether the item is worth doing;
Edge Cases covers all ten categories with `OPEN: None`; every plan task carries a canonical ordinal,
a checkbox and a lowercase `verify:` declaration; `## Write Targets` names every path the build
touches and nothing else, and extends the ideation-authored precondition fence rather than replacing
it. **Check 8 (mitigations) is discharged for the first time on this item:** the 2026-09-08 threat
model is the latest and only speaking round, both of its `kind: required` mitigations are folded into
`## Design` §6.5 AND into the Implementation-Plan task each fence names, and `## Mitigation Folds`
carries one `fold` fence per id with `desc` copied verbatim from that round, the exact Design
sentence, the `Task N` ordinal and that task's own work and verify text — which is what the
conveyor's D8c rule reads and what §10 P-9 now describes instead of denying. **The 2026-09-08 threat
model ROUND 2 is now the latest speaking round and it re-emitted M1 and M2 byte-identically, so the
two fold records stay fresh against it; `## Mitigation Folds` is restated in place as that section's
rule requires, and this round's only change to it is Task 8's `work:` quote moving with Task 8's own
text.** Round 2's blocking finding minted no M3 — it says so itself, and for a stated reason: no
Implementation-Plan task can carry a redaction of a settled gate section, so a `landed: Task N` would
be false. Its two halves are §10 P-10(a) (conductor, done) and `## Scope Boundary`'s standing
authoring rules (spec-writer, landed this round). **Check 12 (AC drift)
fires and the answer is unchanged in substance:** no criterion's promise, actor, scope, oracle or
exception has moved this round either — **this round's blocking criterion-versus-code finding was
resolved entirely in `## Design` and `## Implementation Plan`, because AC-3's own wording ("carrying
the named `pattern`") was correct and only the Design's pinned value was not.** Two edits inside the
hash-signed span exist and both are declared in
§10 P-2 — AC-3(iv)'s `CENSUS_DIGEST`, re-taken by the conductor over the corrected census, and this
section's own preamble sentence, which had come to assert the criteria were unfrozen. They owe ONE
re-sign between them, it is still UNTAKEN, and P-2 records the diff classification a reviewing gate
has already run against the frozen artifact so granting it costs no fresh audit. Everything the two blocking criterion-versus-artifact findings needed was
landed in `## Design`, `## Implementation Plan` and `## Write Targets` precisely so no third edit was
required. **Check 4's test-coupling clause is now discharged for every resolved edge case:** the
idempotency and no-clean rules are asserted by AC-1(b)'s second `materialize_vault` call, the ISBN
and hex-literal collisions by Task 9's near-miss battery, and the `-Voxleaf` run rule by Task 9's
shape battery — the three that previously resolved in prose with nothing exercising them.

## Architectural Review — 2026-09-06 (round 6)

**Recommendation: REVISE — one blocking finding, and it is the round-5 family recurring in the
NEIGHBOURING set.** Round 5's finding is closed and I verified the closure field by field against
`models.py` rather than against the fold's prose: the identity-position enumeration is now complete
and is its own rule's output. But round 5 exhausted ONE surface (`models.py`'s declared fields) and
the criterion carries a second enumeration over a second surface — `CONNECTIVE_SET` over the
package's corruption-furniture vocabulary — which is still a SAMPLE of three of the five recovery
regexes in one block of one file, and which fails the membership test AC-5(b) itself states two
sentences later. The consequence is round 3's exact shape (a RED criterion or a false row in the
ledger), not a leak. I exhaust the furniture surface below — all ten person Tier-1 branches and all
five `name_cleaning.py` prefix/suffix regexes — so the fix has nothing left to discover, and I
record plainly that this is the second consecutive round of "enumerated by sampling rather than by
its own rule", which is a datum Dave's pending sufficiency ruling should have.

### Trigger check

The same three fire, unchanged by the fold: a new shared test surface every later item builds on
(`tests/fixture_vault.py` plus `tests/fixtures/vault/`); a new artifact convention
(`docs/vault-shape-census.md`, machine-read by AC-3 and AC-5(c)); new persistent state in the repo
(~50 committed notes plus a frozen digest). Effort over a day. Review re-run against the seeded tree.

### What this round re-read, and what held

Round 5's single finding is **closed**, verified against the code and not against the fold:

- `Exploration.related` (`models.py:299`) is on AC-5(b)'s identity-position list, and its docstring
  gloss at `:280` is exactly `[[Other Exploration]], [[Person]], etc.` as cited.
- `Watch.streaming_service` (`:199`) and `GiftIdea.source` (`:243`) are both listed, and
  `Explore.source`'s gloss at `:224` ("where you found it / who mentioned it") is as cited.
- Clause 3 reaches `extra="allow"` keys by default with no manifest opt-out; `model_config` is at
  `models.py:31-32` as cited.
- Clause 2 declares the four `title` fields a deliberate over-constraint, so the pre-origination
  reconciliation preserves them instead of pruning them on the rule's authority — which is the
  WI-144 half of the finding.
- Both cite corrections landed and both are right: `_ME_TO_PREFIX_RE` (`name_cleaning.py:55`) is
  `^(Me|My)\s+to\s+` with no `Dave` alternative, and the package compares `_GENERIC_ORG_SUFFIXES`
  with `str.lower()` at `:148`, `:185` and `:191`, never `casefold`.

**P14 is complete and correct.** I read every declared field of every `TYPE_TO_MODEL` member off
`models.py` myself before comparing: `BaseEntity` `:39-40`, `Person` `:78-90`, `Company` `:127-132`,
`Book` `:159-170`, `Watch` `:192-202`, `Explore` `:220-226`, `GiftIdea` `:240-244`, `Meeting`
`:259-263` (no `title`, as stated), `Exploration` `:294-302`. Every field is classified, the line
cites are right, and `TYPE_TO_MODEL` at `:309-318` has the 8 members named. That surface is
exhausted, not sampled.

AC-1, AC-2, AC-3 and AC-4 are untouched by this fold and I found no new issue in them. AC-4's
ownership rule still matches the code arm for arm. No premise moved, the approach is untouched, and
nothing below asks for a different mechanism.

### Blocking issues

**1. `CONNECTIVE_SET` states a membership test and enumerates a set that test does not generate —
and the omission makes AC-3(i) and AC-5(b) jointly unsatisfiable for two of the package's own
Tier-1 corruption classes.**

AC-5(b) freezes `CONNECTIVE_SET` at `{"Me", "My", "Dave"}` and grounds it in "the package's OWN
calendar/arrow/transcript prefix vocabulary, whose UNION across the three regexes is exactly that
set". The union claim is true of `name_cleaning.py:46`, `:54` and `:55`. But the criterion then
states its actual membership test, in the sentence excluding `Re`/`Fwd`/`Fw`: a token is not a
member because "a Grep over the whole tree finds them in no Tier-1 branch, no recovery regex and no
candidate census class". Applied as written, that test admits two more literals the enumeration does
not carry:

- **`unknown_contact`** — a live person-side Tier-1 branch (`obsidian_schemas/name_validation.py:271-282`),
  whose own declared specimen is `Unknown Contact Zeta-9` and whose regex is
  `_UNKNOWN_CONTACT_RE = re.compile(r"unknown\s+contact", re.IGNORECASE)` (`:113`), with the paired
  recovery arm at `name_cleaning.py:57` (`_UNKNOWN_CONTACT_SUFFIX_RE`, stripped at `:127`) and live
  specimens in the suite at `tests/test_name_validation.py:248` and `:254`.
- **`archive_prefix`** — likewise (`name_validation.py:260-270`, specimen `zArchived Dave Smith`,
  regex `^z+Archived\b` at `:110`), recovery arm at `name_cleaning.py:56`, stripped at `:115`,
  suite specimens at `tests/test_name_validation.py:229` and `:235`. It appears in the COMPANY
  table too (`:414-419`, specimen `zArchived Acme Corp`), which now matters because `Person.company`
  is an identity position.

The failure scenario is round 3's, exactly, one furniture family over. `## Write Targets` charges
the census to measure the live vault's shape classes and AC-3's draft list is explicitly "each to be
confirmed or corrected by the census", so a census that measures an `unknown_contact` class writes a
MEASURED row; AC-3(i)'s both-directions equality then REQUIRES a specimen for it; the specimen must
carry the same character profile as the measured form, and the package's own picture of that form is
capitalized. Its `name:` is an identity position, and `Unknown` and `Contact` are (i) not in
`NAME_POOL` in any honest way — AC-5(c) would make the conductor certify a zero-hit live-vault row
for `Contact`, which is the unmakeable claim the `Me` exemption exists for; (ii) not in
`CONNECTIVE_SET`, which is frozen by enumeration and, by design, "cannot grow without an AC change";
and (iii) not admitted by `name_cleaning._GENERIC_ORG_SUFFIXES`. Every route through is a RED
criterion or a false row in the ledger whose entire job is to be trustworthy — the sentence AC-5's
`why:` already uses about `Me`.

Two sets that must agree flex on **different schedules**, and that is the root rather than the two
missing literals: AC-3's DRAFT CLASS FLOOR and AC-5(b)'s identity-position list both carry an
explicit "reconciled before origination against the census / the schema" instruction, while
`CONNECTIVE_SET` deliberately carries none — its safety property is that it cannot move. Nothing
ties the frozen set to the census output it has to be able to absorb.

*Concrete fix, and it is one edit to one criterion.* Re-enumerate `CONNECTIVE_SET` from the whole
furniture surface rather than three of five regexes, and give it the same one-time pre-origination
reconciliation instruction AC-3's floor already has (reconciled once against the census, before Dave
signs — after which it is frozen exactly as now, so the safety property is untouched). The
exhaustion is below so the fold does not have to sample again.

**The complete furniture reconciliation.** Every person Tier-1 branch (`name_validation.py:190-309`),
with the capitalized tokens a faithful specimen puts in an identity position:

| Branch (line) | Declared specimen | Furniture tokens extracted | Admissible today? |
|---|---|---|---|
| `email_chars` `:191-201` | `dave@example.com` | none (all lowercase) | n/a — leg (a) |
| `rfc2822_leak` `:202-213` | `Naomi Pavie naomipavieatspeechmaticscom` | none (mangled run is lowercase) | yes |
| `arrow_connective` `:214-225` | `Dave -> Thomas Gatten` | `Dave` | yes |
| `calendar_prefix` `:226-237` | `Dave - Thomas Gatten` | `Dave` | yes |
| `me_to_prefix` `:238-248` | `Me to David Field` | `Me` | yes |
| `path_hostile` `:249-259` | `Bausch/Lomb` | none beyond the name itself | yes |
| `archive_prefix` `:260-270` | `zArchived Dave Smith` | `Archived`, **or none** | **undecided — see note 2** |
| `unknown_contact` `:271-282` | `Unknown Contact Zeta-9` | `Unknown`, `Contact` | **NO — blocking** |
| `pure_digit` `:283-294` | `447700900123` | none (digits) | yes |
| `empty` `:300-308` | `""` | none | yes |

The COMPANY table (`:373-437`) adds no new literal: its five branches are `email_chars`,
`arrow_connective`, `path_hostile`, `archive_prefix` (`zArchived Acme Corp`) and `empty`, and `Corp`
is already admitted by the derived org-suffix rule. `name_cleaning.py`'s five prefix/suffix regexes
(`:46`, `:54`, `:55`, `:56`, `:57`) contribute the same two literals and nothing else. That is the
whole surface — there is no third table and no other recovery regex — so this family is exhausted
here rather than sampled, and the answer is exactly two literals.

### Review

**Fit.** Unchanged and still harmonizing. The four derived sweeps remain this repo's standing move
(`tests/derivations.py` is the established home for the idiom). The finding is about one declared
set's membership, not about the idiom — and the fix makes the set MORE derived from the package,
which is the direction rounds 4 and 5 already moved `_GENERIC_ORG_SUFFIXES` and the identity list.

**Duplication.** Still none. The fold added no surface; nothing in the tree materializes a vault
from committed bytes and the nine private helpers P3 counts all synthesize.

**Boundaries.** Clean and unchanged: bytes own the specimens, the manifest owns the oracle, the
census owns the distribution and the "certifiably not a real person" ruling. The blocking finding is
inside AC-5's own declared surface, not a boundary dispute — though it is a scheduling mismatch
ACROSS the conductor/builder boundary (the census may measure a class the frozen builder-side set
cannot absorb), which is the same boundary round 4's containment fix was about.

**Determinism boundary (LLM vs code).** Correctly placed and unchanged. Judgment (which shapes
exist, which tokens name nobody) is the conductor's recorded scan; the mechanical part (is every
token in the declared set, does the digest hold) is code. The finding is squarely mechanical — which
literals the package's own corruption tables carry is answerable by reading two files, and this is
the second fold to answer it by sampling.

**Reversibility.** Unchanged and high. Additive throughout, and AC-5 keeps the one irreversible edge
(real data in permanent git history) machine-checkable. This finding does not open that edge — it
closes a route to GREEN, which is why it is a satisfiability finding and not a leak finding.

**Generalization.** Unchanged. D5, D6 and D7 still decline to generalize on measured grounds
(`pyproject.toml:38-39` packages `obsidian_schemas` only), and this fold widened nothing.

**Cost & maintenance.** Unchanged by the fold and unchanged by the fix: re-enumerating a frozen
literal set from two files the criterion already cites costs nothing recurring, and the
reconciliation instruction is one-time and pre-signature. AC-5 still demands strictly less than it
did at round 2.

**Build vs extend vs integrate.** Unchanged — build, with nothing to extend. P1/P2 measure zero
fixture data files and no `conftest.py` anywhere.

**Prior art (outside view).** Non-blocking and unchanged. This builds no machinery around a
subtracted capability; a frozen committed corpus plus a snapshot digest is the standard answer (Go
`testdata/`, pytest data directories, golden-file testing), and a closure against a declared
vocabulary with a small enumerated exemption list is the standard answer for scrubbing a corpus
where no reserved namespace exists. The standard answer derives the exemption list from the
producer's own vocabulary, which is what the fix asks for.

**LESSONS.** #31 is the live one for a fourth round running and the finding sits inside its
statement — a wall the spec can name is a wall the spec-time check must derive, and prose review
does not catch the mechanically checkable class. Which literals are corruption furniture is
answerable by reading `TIER1_BRANCHES` and `name_cleaning.py:46-57`; two consecutive folds answered
it from memory of three regexes. #9 still reads correctly against D1's amendment and #27 against
D7's park; the fold re-incurs neither.

### Notes (non-blocking)

1. **AC-3's draft class list omits the two classes this finding is about, so they have no floor.**
   The ten draft classes cover `rfc2822_leak`, `arrow_connective`, `calendar_prefix`/`me_to_prefix`,
   `path_hostile` and the shapes around them, but neither `archive_prefix` nor `unknown_contact` —
   two of the ten live person Tier-1 branches, each with a dedicated recovery arm. AC-3(i) would
   still catch them IF the census measures them, so this is a floor gap rather than a leak; but the
   DRAFT CLASS FLOOR exists precisely so a shape cannot silently not-ship, and these two are the
   nearest neighbours of the classes already listed. Adding both class ids when the floor is
   reconciled against the census costs one line and is the same read the blocking fix requires.
2. **The extractor's run definition decides whether `zArchived` yields a token, and the criterion
   does not say which.** AC-5(b) says "each run whose FIRST character is an uppercase or non-ASCII
   letter, over letters, marks, apostrophes and hyphens". Under a maximal-letter-run reading,
   `zArchived` is one run beginning lowercase and yields NOTHING; under a
   `[A-Z…][letters…]*`-scanning reading it yields `Archived`, which is unpoolable. The same
   ambiguity decides several ordinary specimens (`McDonald`, `d'Angelo`), so it is worth one clause
   either way — and naming it is cheaper than a build discovering that two readings of one sentence
   give opposite verdicts on the same bytes.
3. **Round 2's notes 1–3 remain open and remain correctly non-blocking**, carried forward for a
   sixth round so they are not buried: AC-2(c)'s kind of equality (bytes vs re-parsed dict) is still
   unnamed; `gate_write` is still a pass-through for six of the eight types — I re-verified the
   branch at `obsidian_schemas/name_gate.py:319-344`, which returns `dict(introduced)` unchanged for
   every declared type that is neither person nor company — so AC-2(c)'s write-door claim is
   substantive for two representatives and nominal for six; and AC-4(c)'s "declared loadable count"
   is still a third quantity distinct from corpus size and glob-match count.
4. **On the sufficiency question recorded for Dave, this round is a second datum and it points the
   other way from round 5's.** Round 5 reported the round-4 generator gone and I confirm that
   independently: no declared set now carries an obligation over members the builder cannot author.
   But round 5's own family — an enumeration that is not its stated rule's output — has now recurred
   once, in the set next door, after round 5 closed it by exhausting `models.py` alone. That is not
   the falsification condition as the item wrote it (which names round 4's generator), and the fix
   here is finite and now exhausted over a surface of fifteen regexes in two files. I am not ruling
   on sufficiency — it is Dave's — but the honest datum is: two consecutive rounds, same defect
   shape, different surface, each closed only when the surface was read exhaustively. If Dave wants
   the middle path (freeze AC-5 at legs (a), (d), (e) and demote (b)/(c) to a declared human-review
   criterion), this is a reasonable place to take it; if he keeps the structural wall, the rule to
   attach is that every set AC-5 declares must be reconciled against a NAMED, ENUMERABLE surface
   before origination, which is the one discipline both closures needed and neither had.

### Suggested adjustments

- Re-enumerate `CONNECTIVE_SET` against the whole furniture surface — the ten person Tier-1 branches
  (`name_validation.py:190-309`), the five company ones (`:373-437`) and all five prefix/suffix
  regexes in `name_cleaning.py:46-57` — and give it AC-3's pre-origination reconciliation
  instruction so a census-measured furniture class can be absorbed once, before signature, without
  changing that the set is frozen thereafter.
- Add `archive_prefix` and `unknown_contact` to AC-3's draft class list, so the two shapes the
  package carries dedicated branches for cannot silently not-ship.
- Say which run definition the AC-5(b) extractor uses, so `zArchived`, `McDonald` and `d'Angelo`
  have one answer rather than two.

### Notes on process

Advancing the stage is the conveyor's — `python src/stage_advancer.py advance WI-016 --to architected
--project <path> --actor architect`. I have edited no frontmatter and no `state/work-items.json`, and
the stage stays at `idea` on this REVISE.

I raise no OPEN architectural question. The single blocking finding carries its own concrete fix and
its own exhaustive reconciliation, no premise moved, the approach is untouched, and nothing is
weakened — the fix widens one frozen literal set by two members and adds one one-time reconciliation
instruction. The reason this is REVISE rather than PROMOTE-with-a-note is the ordering the item
declares in `## Convergence`: Dave signs the criteria before the spec-writer runs, and this finding
is a criterion that goes unsatisfiable the moment the census — a PRECONDITION that lands before the
signature — measures a class the frozen set cannot absorb. That costs one line now and a re-sign
later, which is the same economy that made rounds 4 and 5 blocking.

```verdict
gate: architect
verdict: REVISE
date: 2026-09-06
model: claude-opus-5
targets: AC-5, AC-3
prior: held
basis: folded-material
findings: 1/3
note: Round 5's finding is closed and I re-verified P14 field by field against models.py, but the SAME defect shape recurs in the neighbouring set — CONNECTIVE_SET is enumerated from three of the five prefix/suffix regexes in name_cleaning.py:46-57 and fails the membership test AC-5(b) itself states (in a Tier-1 branch, a recovery regex or a candidate census class), omitting the `unknown_contact` branch's `Unknown Contact` (name_validation.py:271-282, specimen "Unknown Contact Zeta-9", recovery arm name_cleaning.py:57) and `archive_prefix`'s `zArchived` (:260-270, :56), so a census that MEASURES either class makes AC-3(i)'s mandatory specimen unsatisfiable under AC-5(b) — every route is a RED criterion or a false zero-hit row, round 3's shape one furniture family over; the root is that AC-3's floor and AC-5(b)'s field list both reconcile against the census before origination while CONNECTIVE_SET is frozen with no such instruction, and I exhaust all fifteen branches/regexes in the section so the fix samples nothing.
```

## Architectural Review — 2026-09-07 (round 8)

**Recommendation: REVISE — one blocking finding. Round 7's fold is correct and I verified every
part of it against the code; but the fold's document-wide sweep — the thing that made it more than
an instance-prune — was itself done by sampling. It swept ONE enumeration per criterion and stopped,
and AC-2 carries TWO more hand-transcribed enumerations over surfaces the tree declares. The
approach is untouched and sound for an eighth round.**

The finding matters less for the two clauses than for the sentence they falsify. `## Exploration
Notes` now states, as the sharpened falsification condition Dave's pending ruling is staked on:
"the signal to watch is not another finding in AC-5, it is a NEW hand-transcribed enumeration
appearing in this document over a surface the tree declares — which, after this pass, there is no
remaining instance of to find." There are two, both in AC-2, one of them over `TIER1_BRANCHES` —
the identical tuple round 7's finding was about, one criterion away. I report that plainly and do
not rule on it; the ruling is Dave's. I also state the respect in which this round's instances are
weaker than every prior one, because that is the part a count alone would hide.

### Trigger check

The same three fire, unchanged by the seventh fold: a new shared test surface every later item
builds on (`tests/fixture_vault.py` plus `tests/fixtures/vault/`); a new artifact convention
(`docs/vault-shape-census.md`, machine-read by AC-3 and AC-5(c)); new persistent state in the repo
(~50 committed notes plus a frozen digest). Effort over a day. Review re-run against the seeded
tree (HEAD `821177f` plus the WI-022 delta).

### What this round re-read, and what held

Round 7's blocking finding is **closed**, and I verified the closure against the code rather than
against the fold's prose:

- I enumerated `TIER1_BRANCHES` myself (`name_validation.py:190-309`): ten records, `branch_id`s
  `email_chars` `:192`, `rfc2822_leak` `:203`, `arrow_connective` `:215`, `calendar_prefix` `:227`,
  `me_to_prefix` `:239`, `path_hostile` `:250`, `archive_prefix` `:261`, `unknown_contact` `:272`,
  `pure_digit` `:284`, `empty` `:301`. `COMPANY_TIER1_BRANCHES` (`:371-438`) adds none that is new.
  P18 is correct in every cell.
- The `branch_id`-not-`pattern` key is right and the docstring says so verbatim at `:152-154`
  ("`branch_id` is the sweep's unit and is unique in the tuple; `pattern` … is deliberately not
  unique (three branches share `calendar_prefix`)"), confirmed at `:216`, `:228`, `:240`. AC-3's
  derived floor keys on the right field.
- AC-3's `why:` no longer claims "eight of the ten"; it now records the true prior count of four
  and names the four omissions. Corrected.
- P16's count is corrected to sixteen and the `re.IGNORECASE` distribution is recorded as eight of
  sixteen; P17 is added with its predicate. Both of my round-7 notes are folded as written.
- **AC-4's newly derived repository set is correct, and I checked it because no gate asked for it.**
  `obsidian_schemas/repositories/__init__.py:8-21` exports exactly four concrete `BaseRepository`
  subclasses; their `type_name`s are `person` (`person.py:189-190`), `company`
  (`company.py:67-68`), `book` (`book.py:47-48`), `meeting` (`meeting.py:48-49`); neither person
  nor company overrides `file_pattern`, so both inherit `@*.md` (`base.py:196-198`), meeting
  declares `Meeting *.md` (`meeting.py:52-54`) and book the catch-all `*.md` (`book.py:51-53`).
  The set difference against `set(TYPE_TO_MODEL)` (`models.py:309-318`) is exactly
  `{watch, explore, gift-idea, exploration}`, as AC-4 states.
- AC-2's `gate_write` claims still hold at their stated size: `name_gate.py:319-344` returns
  `dict(introduced)` for every declared type that is neither person nor company, with the company
  arm calling `validate_strict(..., branches=COMPANY_TIER1_BRANCHES)` at `:340-341` for its raise
  behaviour; the person arm calls `validate_strict` at `:361-363`; `writer.py:252-253` is the gated
  door. AC-1 drew no finding from me.

No premise moved, and nothing below asks for a different mechanism, a different layout, a different
artifact or a weaker criterion.

### Blocking issue

**1. The round-7 fold's document-wide sweep was itself done by sampling: it checked ONE enumeration
per criterion. AC-2 carries two more hand-transcribed enumerations over declared, enumerable
in-tree surfaces, and the residue list that closes `## Exploration Notes` is therefore false.**

The fold's own account of what it did (`## Exploration Notes`) is: "AC-3's class floor is now a
runtime read of `branch_id` over both Tier-1 tables; AC-4's repository set is now a runtime read of
the exported `BaseRepository` subclasses …; **AC-2 was already derived from `TYPE_TO_MODEL`** and
AC-4's reason set from `_skip_reason`'s codomain; and the org-suffix admission was already read
from the package. **What remains hand-written is now exactly the set of things with no declaration
to read.**" The bolded step is where the sweep stopped: AC-2's *population* is derived, so AC-2 was
marked done. AC-2 contains two further enumerations, neither of which is its population.

*Instance A — AC-2's NARROWING ARM hand-lists `set(TYPE_TO_MODEL) - set(ENTITY_BODY_CONFIG)`.* The
criterion reads: "`watch`, `explore` and `gift-idea` have no `ENTITY_BODY_CONFIG` entry
(`body_sections.py:303-324` declares 5 of the 8), so for exactly those three the body expectation
asserted is `get_default_body(<type>) == ""` … the other five assert their config's declared
sections." Both sides are dict literals the package exports and the test already reads one of them:
`ENTITY_BODY_CONFIG` (`body_sections.py:303-324`) keys `person`, `company`, `meeting`, `book`,
`exploration`; `TYPE_TO_MODEL` (`models.py:309-318`) keys those five plus `watch`, `explore`,
`gift-idea`. The difference is computable in one expression and is exactly the hand-listed three
today. The written list is a transcription of a derivable set, in the same criterion whose own
population is derived two clauses earlier.

*Instance B — AC-2's definition of GATE-CLEAN hand-lists four of the ten Tier-1 branches, over the
same tuple round 7's finding was about.* The criterion reads: "that note must be GATE-CLEAN (no
arrow-connective descriptor, no `Me to ` prefix, no path-hostile character, no RFC 2822 leak)".
Gate-cleanliness is not a four-condition property: for a `person` representative it is exactly
"`validate_strict` does not raise" (`name_gate.py:361-363`, the full ten-branch chain), and for a
`company` representative exactly "`validate_strict(..., branches=COMPANY_TIER1_BRANCHES)` does not
raise" (`:340-341`, five branches). The list names `arrow_connective`, `me_to_prefix`,
`path_hostile` and `rfc2822_leak`; it omits `email_chars`, `calendar_prefix`, `archive_prefix`,
`unknown_contact`, `pure_digit` and `empty`. `Tier1Branch.matches` (`:179-184`) makes the
derivation available directly, and `tests/test_name_gate.py:212` already sweeps the tuple this way.

*Failure scenario, stated at its real size rather than inflated.* Both instances fail LOUD, and
that is the material difference from every prior blocking finding in this document. Instance A: a
ninth `TYPE_TO_MODEL` member with no body config falls into the "other five" arm, the test reads
`ENTITY_BODY_CONFIG[<ninth>]`, and the sweep raises — RED, but RED reading as a missing fixture
rather than as a missing config entry, so the build spends a round on it. Add a `watch` entry to
`ENTITY_BODY_CONFIG` and `get_default_body("watch") == ""` goes RED against a change that was
correct. Instance B: a representative that trips one of the six unlisted branches is refused by
`gate_write` and leg (c) goes RED — which is precisely the outcome AC-2's own `why:` says the
naming exists to prevent ("the criterion goes RED for a reason that has nothing to do with
round-tripping and the build spends a round rediscovering the gate"), one clause after the sentence
that leaves it open. **Neither instance has a green-over-wrong route**, which is what separates
this round from rounds 4 through 7: AC-3's floor let a green suite ship an incomplete corpus, and
these two cost build rounds instead of properties. Instance B is further softened by AC-2's own
general rule sitting beside it — "The corruption specimens are NEVER a `roundtrip_representative`"
— which catches the realistic case; the four-item list is a redundant and incomplete gloss on a
rule stated correctly next to it, which is exactly the shape that goes stale unnoticed.

*Why it is nevertheless blocking rather than a note.* Not for the two clauses' own cost, which is
small and loud. For the sentence they falsify. `## Exploration Notes` closes with a
document-wide exhaustiveness claim and a four-item residue list ("AC-3's six shape classes,
AC-5(b)'s identity positions, `CONNECTIVE_SET`, and AC-4's ownership oracle … none is a
transcription of a list the tree holds"), and the sufficiency section stakes Dave's pending ruling
on that claim being true. It is not: there are six such things, and two of them do have a
declaration to read. Round 7 blocked on a count that was wrong by two in a `why:`; this is the same
defect one level up, in the paragraph Dave reads to decide whether to keep or cut AC-5. Leaving it
would hand the spec-writer a document whose `## Exploration Notes` asserts a closure that my own
section three screens below contradicts — the WI-144 shape at document scale, and the one thing
this gate is asked not to pass through.

*Concrete fix — three edits, all mechanical, none of which changes what any criterion demands.*
(1) AC-2's narrowing arm: replace the hand-listed three with the derived set, e.g. "for each member
of `set(TYPE_TO_MODEL) - set(ENTITY_BODY_CONFIG)` (`models.py:309-318`, `body_sections.py:303-324`
— `watch`, `explore`, `gift-idea` today) the body expectation is `get_default_body(<type>) == ""`;
for each member of the intersection, the config's declared sections." (2) AC-2's gate-clean
predicate: replace the four negatives with the predicate the door actually applies — "GATE-CLEAN
means `gate_write` accepts it: for `person`, no branch of `TIER1_BRANCHES` matches
(`Tier1Branch.matches`, `name_validation.py:179-184`); for `company`, no branch of
`COMPANY_TIER1_BRANCHES`; for the other six types `gate_write` is a pass-through and the condition
is vacuous" — keeping the four examples as examples if they are useful. (3) Correct the residue
list and the falsification sentence in `## Exploration Notes` to record that the round-7 sweep was
per-criterion rather than per-enumeration, and that the two AC-2 instances were the remainder. Each
is one line of draft criterion text now, against a signed AC re-grounded after origination.

### Review

**Fit.** Still harmonizing, and both fixes move with the grain: they are the same runtime read of an
exported declaration that AC-2 already performs on `TYPE_TO_MODEL`, AC-3 on `branch_id` and AC-4 on
`_skip_reason`'s codomain and the exported subclasses. `tests/derivations.py:1-22` remains the
repo's standing home for the idiom, and both reads are runtime dict/tuple reads rather than syntax
scans, so neither needs nor may name `ast` (P9's single-homing wall, `tests/test_name_gate_wall.py`).

**Duplication.** Still none at the artifact level — nothing in the tree materializes a vault from
committed bytes, and P3's nine private helpers all synthesize. The finding is itself a duplication
finding of the small kind: instance B duplicates, in prose, a predicate the package computes
(`validate_strict`), and instance A duplicates a set the package computes. Solve-in-one-place says
read them.

**Boundaries.** Clean and unchanged: bytes own the specimens, the manifest owns the oracle, the
census owns the distribution and the not-a-real-person ruling. Both fixes improve a boundary in the
same direction round 7's did — today AC-2 asks a builder to know the package's body-config map and
its refusal surface from lists a gate transcribed; derived, the package tells the suite.

**Determinism boundary (LLM vs code).** This is the dimension the finding sits on, for the fourth
consecutive round. Which types have a body config, and which names the gate refuses, are both
MECHANICAL facts sitting in exported declarations; both are being carried by human-transcribed
lists in a criterion. Judgment — which shapes the live vault holds, at what frequency, what a
faithful pseudonymous specimen is, and whether a field's value IS a person's name — correctly stays
with the census and with AC-5(b)'s argued hand list. The boundary is drawn in the right place
everywhere it was examined; the finding is that two clauses were never examined.

**Reversibility.** Unchanged and high. Additive throughout; AC-5 keeps the one irreversible edge
(real data in permanent git history) machine-checkable, and this finding opens no leak — it is a
build-friction and document-consistency finding, not a privacy one.

**Generalization.** Unchanged and right-sized. D5, D6 and D7 still decline to generalize on
measured grounds (P8: `pyproject.toml:38-39` packages `obsidian_schemas` only). The fix generalizes
two enumerations and nothing else.

**Cost & maintenance.** Both fixes REDUCE recurring cost — each removes a paired edit that fires
whenever the package gains a type, a body config or a refusal branch. Round 7's AC-3 fix carries a
cost in the other direction that is worth naming (note 2 below), but it is the intended friction
of LESSONS #45 rather than a defect.

**Build vs extend vs integrate.** Unchanged — build, with nothing to extend. P1/P2 still measure
zero fixture data files and no `conftest.py` anywhere in the tree.

**Prior art (outside view).** Non-blocking and unchanged. Nothing here builds machinery around a
subtracted capability: a frozen committed corpus plus a snapshot digest is the standard answer (Go
`testdata/`, pytest data directories, golden-file testing), and deriving a coverage floor from the
producer's own registry rather than from a hand list is likewise the standard answer, not a
divergence needing a cited execution.

**LESSONS.** #45 is still the live one and I read it rather than quoting the fold: "when a registry
claims to enumerate a population, ship the reality-diff as a floor check: derive the actual
population from the source … and assert set-equality with the registry — both directions." AC-3's
new floor is the right move and satisfies the first half; see note 3 for the second half. #46 ("a
green check is evidence only after it has been seen red") is newly relevant now that three
criteria derive their populations at runtime and is note 4. #9 still reads correctly against D1's
amendment, #27 against D2's rejection and D7's park, and #31 against the derive-don't-describe
discipline. The fixes re-incur none of them; AC-2 as written re-incurs #45 twice.

### Notes (non-blocking)

1. **AC-4's "that asymmetry is itself checked rather than assumed" is a tautology as written.** The
   clause says "the derived repository set and `set(TYPE_TO_MODEL)` are both read at test time and
   the four repository-less types are exactly their difference." If both sides are derived and no
   expected value is declared, the assertion is `A - B == A - B` and passes for any package. It
   costs nothing — a fifth repository is already caught by the derived sweep proper, which demands
   a declared mapping and loadable count for it — but AC-4 states the governing rule three
   sentences later ("WHAT IS DERIVED IS THE POPULATION AND NEVER THE ORACLE") and this clause is
   the criterion's own counterexample to it. Either declare the four repository-less types as a
   hand-written oracle, or drop the clause and say plainly that the asymmetry follows from the two
   derivations rather than being checked.
2. **AC-3's derived floor makes adding a Tier-1 branch redden the suite with no in-cage remedy, and
   that cost is not named anywhere.** A new `branch_id` joins the floor automatically (correct, and
   the point), but discharging it needs a census row carrying a count, a scan command and verbatim
   stdout — all of which require the live vault, which no caged builder can read. So a routine
   package change (WI-022 just added a whole company table) is blocked on a conductor pass. That is
   LESSONS #45's intended friction and I am not asking for it to be weakened; it is worth one
   sentence in AC-3's `why:` so the next branch author is told, given that round 4 weakened
   AC-5(c) to a containment specifically to remove "paired edits across the cage boundary" and this
   fold reintroduces one in the other direction.
3. **AC-3's floor is one-directional, and #45's rule calls that out by name.** The floor asserts
   census ⊇ derived `branch_id`s. Nothing asserts the reverse, so a branch-named census row for a
   `branch_id` the package no longer declares survives; if its declared verdict is a cleaned form
   or a successful load rather than a refusal, nothing reddens. Assertion (i) supplies the other
   direction over MEASURED rows only. #45 says "treat any check documented as deliberately
   one-directional as an open defect, not a note" — I am recording it as a note because the
   uncovered cell is narrow (an ABSENT phantom row) and the fix is one clause: assert every
   branch-keyed census row's id is in the derived set.
4. **Three criteria now derive their populations at runtime and none of the derivations has been
   seen red (LESSONS #46).** AC-2's `TYPE_TO_MODEL` sweep, AC-3's `branch_id` floor and AC-4's
   exported-subclass sweep all return green when they work and green when they silently read
   nothing — an import that resolves to an empty tuple, a `__subclasses__()` read taken before the
   subclass modules are imported, a `branch_id` attribute renamed. Worth one line in the spec: each
   derived population is asserted non-empty and against its known size at the moment of writing
   (8, 10, 4), which is the cheapest available form of "seen red" for a derivation.
5. **One implementability detail the spec-writer should not discover at build time.** `type_name`
   is an abstract `@property` (`base.py:189-193`), so it is readable off an INSTANCE and not off
   the class. AC-4's "derive the classes, key by `type_name`" therefore requires instantiating each
   repository before the manifest's key set can be compared — which AC-4 does anyway in legs (a)
   and (c), so this is ordering, not a gap. Also worth pinning which read is meant: iterating the
   exported names in `repositories/__init__.py` is deterministic, `BaseRepository.__subclasses__()`
   depends on what has been imported.
6. **AC-3's parenthetical about the company table overclaims by one word.** It says the five
   `branch_id`s shared by both tables mean "those specimens exercise the company arm as well". A
   deduped floor writes ONE census row per `branch_id` and the corpus needs ONE specimen, whose
   declared type decides which table `gate_write` consults (`name_gate.py:329-343` vs `:361-363`) —
   so a person-typed `path_hostile` specimen exercises the person arm only. The company arm already
   has its own sweep at `tests/test_company_name_contract.py:369`, so this is not a coverage hole;
   the sentence should either require a company-typed specimen for the shared five or say
   affirmatively that the company arm is out of this corpus's scope because that sweep covers it.

### On the sufficiency question recorded for Dave

I do not rule on it and I record the datum in both directions, as rounds 6 and 7 did.

*The half that supports the middle path:* this is the FOURTH consecutive round in which an
enumeration in this document turned out not to be its own named surface's output, and the first in
which the missed enumeration sits inside the pass that claimed to have swept them all. The sweep
was itself a sample.

*The half that cuts against it, and it is larger this round than last:* (a) both instances are in
AC-2, which the middle path (freeze AC-5 at legs (a), (d), (e); demote (b) and (c) to a declared
human-review criterion) does not touch — so for the second consecutive round the family has
surfaced outside the part that option removes, which is the strongest available evidence that the
family was never AC-5's; (b) **both instances fail LOUD**, with no green-over-wrong route, which is
a first — every prior instance of this family let a green suite ship something wrong, and these two
cost a build round; and (c) the instances are in ORIGINAL criterion text that no fold has ever
touched, not in folded material, so this round is not a fold breeding its own next finding. The
honest summary is that the folds have converged and what is left is the original draft's own
residue. On the evidence I would keep the structural wall and fix the two clauses; the ruling is
Dave's and the middle path remains available, but on this round's datum it would remove the one
part of the document that has now drawn no finding for four rounds while leaving the part that
drew this one.

### Notes on process

Advancing the stage is the conveyor's — `python src/stage_advancer.py advance WI-016 --to
architected --project <path> --actor architect`. I have edited no frontmatter field and no
`state/work-items.json`; `last_touched` was already today's date. The stage stays at `idea` on this
REVISE.

I raise no OPEN architectural question. The single blocking finding carries its own concrete fix
and its own reconciliation of the surfaces it is about, no premise moved, the approach is untouched,
and nothing is weakened — both edits replace hand-typed lists with reads of declarations the
package already exports, and neither changes what any criterion demands. It is REVISE rather than
PROMOTE-with-notes for one reason and I want that reason to be checkable: not the two clauses,
whose own cost is a build round, but the document-wide exhaustiveness claim they falsify, which is
frozen into `## Exploration Notes` and which Dave's pending sufficiency ruling reads as true.

```verdict
gate: architect
verdict: REVISE
date: 2026-09-07
model: claude-opus-5
targets: AC-2, AC-3, AC-4, #exploration-notes
prior: held
basis: original
findings: 1/6
note: Round 7's finding is closed and I verified every part of it against the code (TIER1_BRANCHES' ten branch_ids at name_validation.py:190-309, the branch_id/pattern docstring at :152-154, the four exported BaseRepository subclasses and their type_names at repositories/__init__.py:8-21, name_gate.py:319-344 and writer.py:252-253) — but the fold's document-wide sweep was itself done by sampling, one enumeration per criterion, and stopped at AC-2 because AC-2's POPULATION is derived: AC-2 still hand-lists `watch, explore, gift-idea` where `set(TYPE_TO_MODEL) - set(ENTITY_BODY_CONFIG)` is computable (models.py:309-318, body_sections.py:303-324) and still defines GATE-CLEAN as four named corruption forms where the door applies all ten TIER1_BRANCHES for person (name_gate.py:361-363) and all five COMPANY_TIER1_BRANCHES for company (:340-341), omitting email_chars, calendar_prefix, archive_prefix, unknown_contact, pure_digit and empty; both fail LOUD with no green-over-wrong route, so the block is not their own cost but the sentence they falsify — `## Exploration Notes` closes with a document-wide exhaustiveness claim and a four-item residue list that Dave's pending sufficiency ruling is staked on, and there are six, two of which do have a declaration to read.
```

## Architectural Review — 2026-09-07 (round 9)

**Recommendation: REVISE — one blocking finding, in AC-4, and unlike round 8's two it HAS a
green-over-wrong route. Round 8's fold is correct and I verified every part of it against the code
and against the out-of-repo pipeline tooling it rests on, including by attacking the new mechanism
from an angle no gate has tried. What I found is a SEVENTH hand-written enumeration, which is
exactly the predicate round 8's corrected falsification sentence names as the signal for Dave's
ruling. The approach is untouched and sound for a ninth round.**

### Trigger check

The same three fire, unchanged by the eighth fold: a new shared test surface every later item builds
on (`tests/fixture_vault.py` plus `tests/fixtures/vault/`); a new artifact convention
(`docs/vault-shape-census.md`, now machine-read AND digest-frozen by AC-3 and AC-5(c)); new
persistent state in the repo (~50 committed notes plus two frozen digests). Effort over a day.
Re-run against the seeded tree (HEAD `821177f` plus the WI-022 delta).

### What this round re-read, and what held

Round 8's blocking finding and its six notes are **closed**, and I verified each closure against the
code rather than against the fold's prose:

- `TYPE_TO_MODEL` (`models.py:309-318`) keys exactly the eight; `ENTITY_BODY_CONFIG`
  (`body_sections.py:303-324`) keys exactly `person`, `company`, `meeting`, `book`, `exploration`;
  the difference is exactly `{watch, explore, gift-idea}` and `get_default_body` returns `""` for
  them at `:337-338`. AC-2's narrowing arm is now that expression. Instance A closed.
- GATE-CLEAN is now the door's own predicate. Verified at the door: `name_gate.py:319` branches on
  `declared_type is not None and declared_type != PERSON_TYPE`, the company arm calls
  `validate_strict(..., branches=COMPANY_TIER1_BRANCHES)` at `:340-341` for its raise behaviour and
  falls to the shared `return dict(introduced)` at `:344`; the person body calls `validate_strict`
  at `:361-363`. `writer.py:252-253` is the gated door and reads `declared_type` off the POST-merge
  `fm.get("type")`, so a fixture's own `type:` selects the arm — which is what makes AC-2 leg (c)'s
  per-type claim implementable as stated. Instance B closed.
- AC-4's tautology is dropped; the `__all__` read is pinned; `type_name` is recorded as an abstract
  `@property` (`base.py:189-193`) needing an instance. All three verified. AC-3 gained its reverse
  direction, its recurring-cost sentence and the corrected company-arm word. Notes 1-6 folded.
- The LESSONS #46 size anchors (8, 10, 4) are on all three derived populations and are declared as
  the POPULATION's size, never an oracle. Correct as written.

**I attacked round 8's new mechanism rather than accepting it, and it holds — recorded so round 10
does not re-derive it.** AC-3(iv) puts `CENSUS_DIGEST` in the signed criterion because the build
cannot reach there. I tested the LIFECYCLE case no round has: what happens at the census's first
legitimate extension after WI-016 closes (a new Tier-1 branch joins AC-3's derived floor; WI-026
consumes the artifact; D6 names exocortex WI-034). The answer is that the asymmetry survives both
phases. `_forged_nondriven_docs` (`stage_advancer.py:653-675`, read here) flags any non-driven
work-item doc in a drive's payload and by its own docstring does NOT flag a shared non-work-item doc
— so post-landing a caged builder still cannot touch `docs/vault-fixtures.md` while the census stays
ordinary build traffic. And the conductor's route is open rather than blocked: the `ac_hash`
currency check is scoped to `to_stage == "ready"` (`work_item_linter.py:4311-4330`), so refreshing
the digest on a closed item costs no linter RED. The mechanism is right and its maintenance path
exists.

No premise moved, and nothing below asks for a different mechanism, layout, artifact or a weaker
criterion.

### Blocking issue

**1. AC-4's skip-reason set is hand-transcribed, the package declares no set to read, and the
criterion states a consequence only a derivation would deliver.**

AC-4 reads: "The sweep stays derived from the classification's own codomain: `_skip_reason`
(`repositories/base.py:41-47`) yields exactly `{"malformed-frontmatter", "schema-drift",
"unreadable"}` … the UNION over the four declared per-repository mappings' reasons is asserted EQUAL
to that codomain — so a corpus missing a reason is RED and **a fourth reason added to the package
later fails until it has a specimen**."

*There is nothing to read.* I grepped the whole package for those three strings: they occur at
`repositories/base.py:44`, `:46` and `:47` as return-statement literals inside `_skip_reason`'s
`isinstance` chain, plus a type comment on `SkippedNote.reason` (`:37`). No frozenset, tuple, dict
or enum exports them. Unlike `TYPE_TO_MODEL` (a dict), the `branch_id` union (records in two
exported tuples) and the repository set (`repositories/__init__.py:14-21`'s `__all__`), this
codomain is recoverable only by transcribing it or by a source scan — and P9 records that `ast` is
single-homed to `tests/derivations.py`, which no fixture module may name. The tree confirms the
transcription is today's only idiom: `tests/test_loud_fail_load.py:187` already writes the same
three literals by hand.

*Why the claim is false rather than merely imprecise.* Both sides of the asserted equality are the
manifest's declared reasons and a set typed into the harness. Add a fourth arm to `_skip_reason` and
neither side moves: the corpus carries no specimen producing it, the manifest declares none, the
hand-typed expected set still holds three, and the criterion is **GREEN** while the new failure
class joins the corpus's blind spot. That is the precise silent under-coverage round 7 found AC-3's
floor doing over the branch table, over the one surface AC-4 exists to protect — WI-020 built
`SkippedNote` because an unloadable note used to vanish at DEBUG (`base.py:29-34`), and a reason
class with no specimen is that note vanishing again one level up. **This is a green-over-wrong
route**, which is what makes it heavier than round 8's two instances, both of which failed loud.

*Why it is blocking and not a note.* Two reasons, and the second is round 8's own. (a) The criterion
would ship a stated safety property it does not have — the thing this gate exists to catch before a
signature freezes it. (b) It falsifies, for the third time, a document-wide exhaustiveness claim
Dave's pending sufficiency ruling reads as true: `## Exploration Notes` closes with a residue of six
hand-written things "with no declaration to read" and `## Approach` lists this set on the DERIVED
side beside `TYPE_TO_MODEL` and the repository set. There are seven, and this one is misfiled.

*Concrete fix — two routes, both small, and the first is better.* (1) Export the codomain: a
module-level `SKIP_REASONS` frozenset in `repositories/base.py` whose members `_skip_reason` returns,
read at test time exactly as AC-2 reads `TYPE_TO_MODEL`. One line in the package, it makes the
claimed property real, and it is solve-in-one-place for a vocabulary that is currently duplicated
across a return chain, a type comment and `test_loud_fail_load.py:187`. Or (2) keep it hand-written
and say so: move it into the residue list beside AC-4's ownership oracle, and DELETE the sentence
about a fourth reason failing automatically. Either way the residue list in `## Exploration Notes`
and the derived-side list in `## Approach` need correcting to match.

### Review

**Fit.** Still harmonizing. Fix (1) moves with the grain — the package already publishes its
populations as module-level literals (`TYPE_TO_MODEL`, `TIER1_BRANCHES`, `ENTITY_BODY_CONFIG`,
`_GENERIC_ORG_SUFFIXES`, `__all__`), and this is the one classification vocabulary that never got
that treatment. `tests/derivations.py:1-22` remains the standing home for the idiom; a frozenset read
needs no scan and so does not touch the `ast` single-homing wall.

**Duplication.** None at the artifact level — P1/P2 still measure zero fixture data files and no
`conftest.py`. The finding is a duplication finding: three strings live in three places today, and
the criterion adds a fourth. Solve-in-one-place says export them once.

**Boundaries.** Clean and unchanged. Bytes own the specimens, the manifest owns the oracle, the
census owns the distribution and the not-a-real-person ruling, and round 8's digest put the census's
expected value on the only side of the cage the build cannot write. Fix (1) improves one boundary in
the same direction: today AC-4 asks the harness to know a classification the package keeps private.

**Determinism boundary (LLM vs code).** The dimension the finding sits on for a fifth round, and the
answer is the same: which reasons `_skip_reason` can emit is MECHANICAL and is being carried by a
transcription. Judgment — the shape distribution, a faithful pseudonymous specimen, whether a field's
value IS a name, and AC-4's deliberately hand-written ownership oracle — correctly stays where it is.
AC-4's oracle in particular must NOT be derived and the criterion says so; the finding is about its
population, never its oracle.

**Reversibility.** Unchanged and high. Additive throughout. AC-5 keeps the one irreversible edge
(real data in permanent git history) machine-checked, and this finding opens no leak.

**Generalization.** Right-sized. D5, D6 and D7 still decline on measured grounds (P8:
`pyproject.toml:38-39` packages `obsidian_schemas` only). Fix (1) generalizes one vocabulary.

**Cost & maintenance.** Fix (1) removes a paired edit that fires whenever the package gains a skip
class. Separately, and it is worth stating once at round nine: this document is now 3,537 lines
specifying a single build, and each round adds narrative every later reader must traverse. The
document's own size has become a real maintenance cost of the item, and it should weigh in Dave's
ruling.

**Build vs extend vs integrate.** Unchanged — build, with nothing to extend.

**Prior art (outside view).** Non-blocking and unchanged. A frozen committed corpus plus a snapshot
digest is the standard answer (Go `testdata/`, pytest data directories, golden-file testing), and
deriving a coverage floor from the producer's own registry is likewise standard. Nothing here builds
machinery around a subtracted capability, so no cited execution is owed.

**LESSONS.** #45 is the live one again and the finding is its text: a registry validated only against
itself is a mirror, not a census. #46's new size anchors are correct. #9 still reads right against
D1's amendment, #27 against D2 and D7, #31 against the derive-don't-describe discipline. The fixes
re-incur none; AC-4 as written re-incurs #45.

### Notes (non-blocking)

1. **AC-3(iv)'s "exactly ONE such declaration was found" is asserted over a file whose culture is to
   quote criterion text verbatim.** Every gate section in this document quotes the criteria it
   reviews. Once `CENSUS_DIGEST` carries a real 64-hex value, one round-10 quotation of the filled
   declaration turns the floor RED, and the remedy is editing a historical gate section. The
   criterion already half-scopes the read ("out of the AC-3 `criteria` fence"); make the uniqueness
   assertion carry the same scope explicitly, so the reader is fence-bounded rather than file-wide.
2. **AC-4's `repositories/__init__.py:8-20` cite is off by two lines and the export list is not
   homogeneous.** The imports end at `:12`; `__all__` is `:14-21`, which the criterion also cites
   correctly elsewhere. More useful to the builder: `__all__` contains `VaultPathNotConfiguredError`,
   which is an exception rather than a repository — the criterion's "concrete `BaseRepository`
   subclasses" filter handles it, but one clause saying the export list is filtered rather than
   iterated whole saves a build round.
3. **Round 8's census-fixity fix survives the lifecycle attack, recorded affirmatively** so a tenth
   round spends its budget elsewhere: see "What this round re-read" above for the two tooling reads
   (`stage_advancer.py:653-675`, `work_item_linter.py:4311-4330`).

### On the sufficiency question recorded for Dave

I do not rule on it. I record the datum in both directions as rounds 6, 7 and 8 did, and this round
the two directions are sharper than they have been.

*The half that supports the middle path, and it is the predicate this document itself named.* Round
8 wrote: "the round-8 pass enumerated the enumerations, criterion by criterion and clause by clause,
and the residue is the six things named … A ninth round finding a seventh is the signal." This is the
ninth round and there is a seventh. It is also the SECOND time an exhaustion claim in this document
has been made and been wrong, and the first instance of this family since round 3 that has a
green-over-wrong route rather than failing loud. Dave asked for a falsifiable condition and it has
now been met on its own terms.

*The half that cuts against it, and it is not a softening.* The instance is in AC-4, which the middle
path (freeze AC-5 at legs (a), (d), (e); demote (b) and (c) to a declared human-review criterion)
does not touch. That is now the THIRD consecutive round in which the family has surfaced outside the
part that option removes — round 7 in AC-3, round 8 in AC-2, round 9 in AC-4 — which is strong
evidence that the family was never AC-5's and that cutting AC-5's scope buys nothing against it.
AC-5 has now drawn no blocking finding for five consecutive rounds. And the approach itself has
drawn none in nine.

*One datum of my own, offered because nine rounds is itself information.* Every finding across
sixteen gate rounds has been against criterion text or the evidence it rests on, never against the
approach, which both gates have ruled sound at every pass. The item's declared budget is twelve
rounds and sixteen have run. If Dave's ruling is that the structural wall stays, the cheapest
remaining path is to take fix (1) — one line in `repositories/base.py` — and originate, rather than
to buy a tenth round hunting an eighth instance of a family whose instances now cost a line of draft
text each.

### Notes on process

Advancing the stage is the conveyor's — `python src/stage_advancer.py advance WI-016 --to
architected --project <path> --actor architect`. I have edited no frontmatter field and no
`state/work-items.json`; `last_touched` already carries today's date. The stage stays at `idea` on
this REVISE.

I raise no OPEN architectural question. The single blocking finding carries two concrete fixes, no
premise moved, the approach is untouched, and nothing is weakened. It is REVISE rather than
PROMOTE-with-notes for one reason I want checkable: AC-4 would be signed carrying a stated safety
property it does not have, over the exact surface it was written to protect.

```verdict
gate: architect
verdict: REVISE
date: 2026-09-07
model: claude-opus-5
targets: AC-4, #exploration-notes, #approach
prior: held
basis: original
findings: 1/3
note: Round 8's fold is closed and I verified it against the code (TYPE_TO_MODEL's 8 at models.py:309-318 vs ENTITY_BODY_CONFIG's 5 at body_sections.py:303-324; the door's three arms at name_gate.py:319/:340-341/:344/:361-363; writer.py:252-253 reading declared_type off the post-merge fm) and attacked its new census-digest mechanism on the lifecycle case no round had tried, which it survives (_forged_nondriven_docs at stage_advancer.py:653-675 still refuses a caged builder post-landing, while the ac_hash currency check at work_item_linter.py:4311-4330 is scoped to to_stage == "ready" so a conductor can refresh the digest on a closed item) — but AC-4 places `_skip_reason`'s reason set on the DERIVED side of this document's residue list and claims "a fourth reason added to the package later fails until it has a specimen", and the package declares NO set to read: the three strings exist only as return literals at repositories/base.py:44/:46/:47 plus a type comment at :37, so both sides of the equality are hand-typed, a fourth arm added to _skip_reason leaves the criterion GREEN with the new class in the corpus's blind spot, and that is a green-over-wrong route over the very surface WI-020 built SkippedNote to close; fix is one line — export a SKIP_REASONS frozenset from repositories/base.py and read it as AC-2 reads TYPE_TO_MODEL — or keep it hand-written and delete the false consequence.
```

## Architectural Review — 2026-09-07 (round 10)

**Recommendation: PROMOTE to architected.** Round 9's fold is closed and I verified every code fact
it rests on by my own read rather than from either gate's prose. I attacked the fold's ONE new
mechanism — the `SKIP_REASONS` declaration plus its `ast` binding — on the dimension it is most
exposed on, and it holds. I then attacked the one lifecycle question no round has asked about
AC-3(iv): whether the in-tree file its test reads has a stable address in this project. It does, and
the answer is recorded affirmatively below so round 11 does not spend budget re-deriving it. **Three
non-blocking notes, none of which changes what any criterion demands, and no OPEN architectural
question.** The approach draws no finding for a tenth round.

### Trigger check

The same three fire, unchanged by the ninth fold: a new shared test surface every later item builds
on (`tests/fixture_vault.py` plus `tests/fixtures/vault/`); a new artifact convention
(`docs/vault-shape-census.md`, machine-read and digest-frozen by AC-3(iv) and AC-5(c)); new
persistent state in the repo (~50 committed notes plus two frozen digests). Effort over a day. The
ninth fold adds a fourth, small: one line of package change in `obsidian_schemas/repositories/base.py`.
Re-run against the seeded tree (HEAD `821177f` plus the WI-022 delta).

### What I verified myself, and what held

Every fact below is my own read of the seeded tree, not an inheritance.

- **P20 holds exactly as written.** `repositories/base.py:41-47` is `_skip_reason`; the three strings
  are bare return-statement literals at `:44`, `:46`, `:47`, plus the type comment on
  `SkippedNote.reason` at `:37`. Nothing in the package exports them as a frozenset, tuple, dict or
  `Enum`. `repositories/__init__.py`'s imports end at `:12` and `__all__` is `:14-21`, carrying
  `VaultPathNotConfiguredError` at `:16` beside the four concrete repositories — so AC-4's corrected
  cite and its "FILTERED, never iterated whole" clause are both right.
- **The fold's new scan needs no new machinery, and that is the strongest thing about it.**
  `tests/derivations.py` already single-homes `ast` (docstring `:14-17`) and already carries the exact
  idiom twice: `parse_frontmatter_exit_sites` (`:543`) is a Return-collecting scan keyed on
  `fid.name`, and `falsy_returns_in` (`:1366`) is the same shape parameterized by function name, with
  `_is_falsy_return` (`:620`) reading `ast.Constant` off a `Return` value. `_iter_functions` (`:217`)
  and `_own_body_nodes` (`:243`) are the shared plumbing both use. AC-4's scan is a fifteenth function
  in an established form, not a new capability — which is what keeps a one-line package change from
  dragging a harness redesign behind it.
- **The claimed property is real under both spellings, which is what I attacked it for.** A fourth
  `_skip_reason` arm whose member is not added to `SKIP_REASONS` is RED at the scan equality; a fourth
  member added to `SKIP_REASONS` with no specimen and no manifest mapping is RED at the union
  equality; a scan that silently resolves nothing is RED against a non-empty set of size 3. All three
  routes close, and the equality-not-containment direction is what closes the third — the failure mode
  every derived read in this document shares.
- **Both files the build touches are writable.** `pipeline-runners.yaml:34-38` declares
  `obsidian_schemas/**`, `tests/**`, `scripts/**`, `docs/**`. P7 holds; `obsidian_schemas/repositories/base.py`
  and `tests/derivations.py` are both inside it.
- **P1/P2 still measure what the Problem section says.** `tests/` holds 32 files and every one is
  `.py`; there is no `tests/fixtures/`, and no `conftest.py` exists anywhere in the tree (the grep hits
  are prose and JSONL mentions, not files). `models.py:309-318` keys the eight `TYPE_TO_MODEL` types.
  The item's premise is intact.

**The lifecycle attack, and it is a new one.** AC-3(iv) has the suite read `docs/vault-fixtures.md`
at test time to recover the signed digest literal, which makes this package's floor depend on a
work-item doc's ADDRESS surviving the item's own closure. No round has asked whether this project
moves such a doc when an item closes. It does not: `docs/` is flat and closed items' docs stay put
(`loud-fail-boundaries.md` is WI-020's, `write-door-bypasses.md` is WI-021's). What this project DOES
move is the gate-round records, by hand, into a sibling `-rounds.md` drawer — `docs/write-door-bypasses-rounds.md:1-13`
records the convention, its `archive-split:v1` marker and Dave's split-first ruling (workshop WI-267),
and `docs/company-stub-parity-rounds.md` is the second use. That split moves gate sections only and
leaves `## Acceptance Criteria` in the living doc, so AC-3(iv)'s read survives it — **and round 9's
note-1 fence-scoping is exactly what makes the drawer's verbatim quotations harmless in either
direction.** The two fixes are consistent with each other, which is not something either round could
have checked alone. Recorded affirmatively.

### Review

**Fit.** Harmonizing, and the ninth fold improves the fit rather than straining it. The package's
convention is to publish each population as a module-level literal — `TYPE_TO_MODEL` (`models.py:309-318`),
`ENTITY_BODY_CONFIG` (`body_sections.py:303-324`), `TIER1_BRANCHES` / `COMPANY_TIER1_BRANCHES`,
`_GENERIC_ORG_SUFFIXES`, `__all__` — and the skip-reason vocabulary is the one that never got it.
`SKIP_REASONS` closes that gap rather than working around it.

**Duplication.** The item's own premise is a duplication finding (P1/P2/P10: nine private vault
helpers over thirteen files, 35 scattered corruption literals) and it still measures true. On the
fold: the three strings live in a return chain and `tests/test_loud_fail_load.py:187-188` today; the
fold adds a declaration and binds the return chain to it, and does not close the test's copy. That is
note 1 below — a note rather than a finding, because that copy fails LOUD.

**Boundaries.** Clean and unchanged for a tenth round. Bytes own the specimens, the manifest owns the
oracle, the census owns the distribution and the not-a-real-person ruling, and round 8's digest put
the census's expected value on the only side of the cage a build cannot write. The fold moves one
boundary in the right direction: AC-4 no longer asks the harness to know a classification the package
keeps private. The `ast` capability stays single-homed, so the scan has exactly one legal address.

**Determinism boundary (LLM vs code).** This is the dimension the last five findings have sat on and
the fold is the correct answer to it: which strings `_skip_reason` can emit is MECHANICAL, and it is
being made a declaration and read rather than carried by a transcription. The judgment side is
correctly left where it is — the shape distribution, the faithfulness of a pseudonymous specimen,
whether a field's value IS a name, and AC-4's deliberately hand-written ownership oracle, which must
NOT be derived and which the criterion says so in as many words. The line between derived POPULATION
and hand-declared ORACLE is stated in `## Where the structure lives` and is now held at all four
criteria.

**Reversibility.** High and unchanged. Everything is additive: a new fixture directory, a new test
module, a frozenset, a scan function. The one irreversible edge — real personal data in permanent git
history — is the thing AC-5 makes structurally impossible rather than merely intended, and nothing in
the ninth fold touches it.

**Generalization.** Right-sized. D5 (migrate all 83 literals), D6 (export to consumers) and D7
(WI-026 acceptance) still decline on measured grounds rather than taste — P8's `pyproject.toml:38-39`
packaging `obsidian_schemas` only is the hard blocker on D6, and LESSONS #27 is the argument on D2 and
D7. The fold generalizes exactly one vocabulary and stops.

**Cost & maintenance.** The build is one focused pass plus one conductor act (the census), and the
fold adds one line to it. Two recurring costs are named in the criteria rather than discovered by
whoever pays them — a new Tier-1 branch reddens AC-3 until a conductor pass supplies its census row,
and a new skip reason reddens AC-4 until it has a specimen. Both are LESSONS #45's intended friction.
The real maintenance cost I would flag is the document itself, and the project already owns the
remedy — note 3.

**Build vs extend vs integrate.** Build, with nothing to extend. There is no fixture corpus to extend
(P1), no `conftest.py` to hang one off (P2), and no third-party fixture-vault library for an Obsidian
frontmatter estate. The one "extend" available is the harness module, and the fold takes it —
`tests/derivations.py` gains a function instead of a new scan module being born.

**Prior art (outside view).** Non-blocking and unchanged. A frozen committed corpus with a snapshot
digest is the standard answer everywhere (Go `testdata/`, pytest data directories, golden-file
testing), deriving a coverage floor from the producer's own registry is standard, and exporting a
classification's codomain as a module constant is the ordinary shape of the thing. Nothing here builds
machinery around a subtracted capability or compensates for a limit, so no cited execution is owed on
this dimension.

**LESSONS.** #45 is the one the ninth fold serves — a registry validated only against itself is a
mirror, and the fold makes the mirror a census by creating the thing to compare against. #46 is on all
four derived populations with size anchors declared as the POPULATION's and never as an oracle. #9
reads right against D1's amendment, #27 against D2 and D7, #31 against the derive-don't-describe
discipline. The design re-incurs none of them.

### Notes (non-blocking)

1. **`tests/test_loud_fail_load.py:187-188` stays a hand-typed second home after the fold.** It
   asserts `{n.reason for n in repo.skipped_notes} == {"malformed-frontmatter", "schema-drift",
   "unreadable"}` — the exact copy the fold's own solve-in-one-place argument cites as the reason to
   create the declaration. Reading `SKIP_REASONS` there instead is one line. It is a NOTE and not a
   finding because that assertion fails LOUD on a fourth reason rather than passing green, and because
   `## Approach` deliberately fixes the package-side scope at two files; D5's "migrate when next
   touched" already covers it. Worth doing in the same build only if it is free.

2. **AC-4's "whose members `_skip_reason` returns BY NAME rather than as re-spelled literals" is
   prose with no check behind it.** The scan's first arm — every `Return` whose value is a `str`
   Constant — resolves the re-spelled form too, so the equality is green under both spellings and a
   builder who adds the frozenset while leaving the literals in the return chain satisfies the
   criterion while leaving two homes inside one file. **The safety property is unaffected either way**
   (a fourth arm is RED under both spellings), which is why this is a note: what is unchecked is only
   the within-file duplication the fold argues against, not the regression protection it claims. One
   clause settles it in either direction — say the two arms are both legal and by-name is a
   preference, or drop the by-name phrase and keep the scan. This is one line of draft text at the
   same pre-origination edit that already fills `CENSUS_DIGEST` and reconciles AC-3's six shape
   classes.

3. **The rounds drawer exists in this project and this document has not used it.** Round 9 flagged
   the document's size as a real maintenance cost of the item and did not name the remedy; the remedy
   is in-tree, is Dave-ruled, and has been used twice — `docs/write-door-bypasses-rounds.md` (WI-021,
   19 gate rounds moved out by hand) and `docs/company-stub-parity-rounds.md` (WI-022). This doc is
   now roughly 4,000 lines for one build, with ten architect and eight red-team records inline. It is
   a CONDUCTOR act, not a gate's and not a builder's, it touches no criterion, and per the drawer's own
   header the line-number citations inside moved records are left as they were. It is worth doing
   before origination so the spec-writer reads a living doc rather than a transcript, and AC-3(iv)'s
   fence-scoped read survives it unchanged.

### On the sufficiency question recorded for Dave

I do not rule on it, and PROMOTE does not pre-empt it — the `ac-signoff` fence is written only after
Dave's review, so the ruling still happens at its own door and the middle path is still available
there. Two data points from this round, recorded in both directions as rounds 6 through 9 did.

*The half that supports the middle path:* nothing new. The falsification condition fired at round 9
and that fact stands as written; I am not softening it.

*The half that cuts against it, and this round adds to it:* the ninth fold's finding was the last
member of the family with anywhere left to go — every earlier instance was a list copied from a
declaration the tree held, and that one had none, which is why its remedy was to WRITE the
declaration. I looked for an eighth instance and there is none: after the fold, all four populations
this document quantifies over are runtime reads of exported declarations, and the four hand-written
residue members are hand-written by SUBJECT (three are judgment, one is a deliberate oracle). AC-5 has
now drawn no blocking finding in six consecutive rounds, and this is the FOURTH consecutive round in
which the family surfaced outside the part the middle path would remove. **And the approach has drawn
no finding in eighteen gate rounds.** The declared `round_budget` is 12 and eighteen have run; this
round's three notes cost a line of draft text each and none is a safety property. On that evidence the
cheapest remaining path is to originate, and if Dave takes the middle path anyway, rounds 8 and 9's
fixes still have to stand — AC-2, AC-3(iv) and AC-4 are not what it removes.

### Notes on process

Advancing the stage is the conveyor's: `python src/stage_advancer.py advance WI-016 --to architected
--project <path> --actor architect`. I have no shell in this cage and cannot run it, so the advance is
OWED and is the conductor's next act on this item. I have edited no frontmatter field and no
`state/work-items.json`; `last_touched` already carries today's date. I have originated no AC text,
touched no other gate's section, and changed nothing in `## Acceptance Criteria`, `## Approach`,
`## Write Targets` or `## Intent`.

I raise no OPEN architectural question. Two doors remain open ahead of origination and both are
already declared rather than being findings of mine: the census must land in HEAD, and the one-time
pre-origination edit must fill AC-3(iv)'s digest declaration and reconcile AC-3's six hand-listed
shape classes and AC-5(b)'s `CONNECTIVE_SET` against the landed artifact. Note 2 is one more line at
that same edit.

```verdict
gate: architect
verdict: PROMOTE
date: 2026-09-07
model: claude-opus-5
note: Round 9's fold is closed and I verified it by my own read (P20 exact — _skip_reason at repositories/base.py:41-47 with bare literals at :44/:46/:47 and the type comment at :37, nothing exporting them; __all__ at :14-21 carrying VaultPathNotConfiguredError; write_authority at pipeline-runners.yaml:34-38 covering both touched files), the SKIP_REASONS mechanism closes all three routes I attacked it on (unlisted arm RED at the scan equality, unspecimened member RED at the union equality, silent under-read RED because the relation is equality not containment), and it adds no new harness capability — tests/derivations.py already single-homes ast and already carries the same Return-keyed scan shape twice at :543 and :1366; I additionally attacked AC-3(iv) on a lifecycle case no round had tried, whether the doc its test reads keeps a stable address after close, and it does (docs/ is flat, closed items' docs stay put, and the project's -rounds.md drawer convention moves only gate sections, which round 9's fence-scoped uniqueness makes harmless) — so with eighteen gate rounds having produced no finding against the approach, four consecutive rounds' findings landing outside the part Dave's middle path would remove, and this round's three findings all non-blocking one-liners that change no criterion's demands, the item is architecturally ready and the remaining doors are the already-declared census landing and the one-time pre-origination edit.
```

## AC Red-Team — 2026-09-07 (round 9)

**Read order followed per the role contract:** `## Intent`, `### Examples of done`, `## Problem /
Motivation` and `## Exploration Notes`, `## Acceptance Criteria` (AC-1 through AC-5 in full, including
`## Write Targets`'s census precondition, which AC-3 and AC-5 both delegate ground truth to), then this
document's own carry-forward — all eight prior AC Red-Team sections and all ten Architectural Review
sections, to read the series rather than the latest fold in isolation.

**What I did that no prior round's carry-forward shows being done: ran the empirical premises rather
than trusting the prose or the code citations.** `## Problem / Motivation` makes several claims about
this tracked tree's current state that are exactly the "empirical premise" class this gate's own
charter says is mine to RUN, not reason about. Against the seeded tree (HEAD `821177f` plus the WI-022
delta, same snapshot round 10 cites):

- **"tests/ holds 32 files, every one of them .py."** Verified exact — a glob over `tests/**` returns
  32 entries, all `.py`, including today's uncommitted `tests/test_company_name_contract.py` (the
  claim's currency is the tree as seeded, uncommitted delta included, exactly as the corpus-audit
  convention this document itself cites requires).
- **"there is no `tests/fixtures/`, no `conftest.py` anywhere in the tree."** Verified — no match for
  either anywhere in the repository.
- **"83 hand-typed `type: <entity>` frontmatter literals across 13 test files."** Verified exact — a
  scan for `type: <entity-name>` literals returns 83 occurrences across exactly 13 files, and the file
  set matches the ones this section and AC-3's `why:` name.
- **The `Exploration` model's wiring** (`models.py:266`, `EntityType` at `:306`, `TYPE_TO_MODEL` at
  `:317`, `body_sections.py:320-323`'s config entry, "13 sites in the package and zero sites under
  `tests/`"). Verified exact on every count, including the body-section config — my first
  case-sensitive scan missed it because the key is lowercased (`"exploration":`, `:320`), which the
  claim's own wording ("13 sites") already accounts for and a case-sensitive-only check would not have.
  This is also AC-2's narrowing-arm claim (`ENTITY_BODY_CONFIG` declares 5 of 8, `exploration` is one of
  the 5) checked against the tree rather than trusted from the criterion's own citation.

All four premises hold exactly as stated. This is not a rubber stamp of round 10's "architecturally
ready" — it is the one check available to a decorrelated reader with no shell that neither gate's prior
rounds record having done against this section, and it came back clean.

**One immaterial inconsistency, noted and not raised as a finding.** `## Problem / Motivation` names
eight helpers by backtick — `temp_vault`, `vault(tmp_path)`, `_note`, `_seed`, `_plant`, `_rich_note`,
`_plant_company_note`, `_plant_carrier` — then says "Nine helpers, thirteen files." A `def` scan over
those eight names across `tests/` finds 15 definition sites (several files privately redefine `vault`,
`_note`, `_seed` and `_plant` under the same name) but only eight distinct NAMES, never nine. This is
narrative scene-setting in `## Problem / Motivation`, not a premise any `check:` reads or any AC
quantifies over — AC-2's sweep derives from `TYPE_TO_MODEL`, AC-3's floor from the Tier-1 tables, AC-4's
from `__all__`, none from this sentence — so it fails the materiality bar (an AC a builder could green
without doing the work, or an absence no criterion covers) and I am not treating it as a finding, per
this gate's own calibration guidance against grading prose.

**Re-attacked the five criteria fresh, read Intent-first per the role contract, against the checklist
of failure classes this gate's charter lists.** Tautological ACs, zero-implementation satisfiability,
single-literal gameability, uncovered invocation layers, mocked oracles at the integration seam,
mutually unsatisfiable pairs, scope drift from Intent, class-closing ACs with hand-picked fixtures,
derived sweeps with no per-member oracle, trivial fixtures on production-varying dimensions, hand-built
rows at a store boundary, and unrunnable `check:` keys. I found no new instance of any of them:

- AC-1's byte-copy discriminator (leg c) still closes the exact route — materializing via `repo.save()`
  or `write_markdown_file` — that a builder reaching for the idiomatic repository API would otherwise
  take, and still reddens correctly on it.
- AC-2's sweep is still derived from `TYPE_TO_MODEL` (8, asserted non-empty and sized) with a
  hand-written per-type oracle (leg b) that a self-consistent-but-wrong parser cannot pass by
  construction, and the narrowing arm's population (`set(TYPE_TO_MODEL) - set(ENTITY_BODY_CONFIG)`) is
  itself a derived read I independently confirmed evaluates to `{watch, explore, gift-idea}` against
  the tree, not a hand list.
- AC-3's class floor still reads `TIER1_BRANCHES`/`COMPANY_TIER1_BRANCHES` at test time rather than
  transcribing them, and the status-scoped assertions (i)-(iii) still let an honestly-ABSENT row stay
  green — I checked the scoping holds together rather than re-deriving the branch set myself, since P16
  already records that pass and no round since has found a gap in it.
- AC-4's `SKIP_REASONS` derivation (this document's own round-8/9/10 subject) still ties the frozenset
  to `_skip_reason`'s actual returns by the `tests/derivations.py` syntax scan rather than leaving it as
  an unconsumed export, which is what stops it decorating rather than binding.
- AC-5's position split (identity vs. free-prose vs. connective) still keeps `PROSE_ALLOWLIST`
  structurally unreachable from any identity-position token, and `CONNECTIVE_SET`'s non-vacuity is still
  dropped rather than reintroducing the mandatory-obligation-over-an-unauthored-set family this
  criterion's own `why:` records having bred three times.

**On the standing "middle path" sufficiency question: I decline to rule on it, same as the last several
rounds, and for the same stated reason — it is Dave's.** I looked for a fifth instance of the family
that would falsify the recommendation to keep AC-5's structural wall (a mandatory obligation over a
set the builder does not author) and found none; AC-5 draws no finding this round, which is now five
consecutive rounds since the family's last confirmed instance. I am not escalating this as the regress
signature: the last four rounds' material-finding count has been falling (1/1, 1/1, 1/1, then round
10's zero blocking), the findings have kept landing on distinct, nameable surfaces rather than on
machinery a prior fold invented, and this round adds a fifth clean, independently-run check rather than
another layer of self-referential apparatus. That is the shape of a converging arc, not a treadmill.

**No line above touches `## Acceptance Criteria`, `## Approach`, `## Write Targets`, `## Intent`, or any
other gate's section.** I originate no AC text and pre-clear nothing — D4a remains Dave's alone.

```verdict
gate: ac-red-team
verdict: PROMOTE
date: 2026-09-07
model: claude-sonnet-5
note: Attacked all five criteria fresh against the full failure-class checklist and independently ran (rather than trusted) four empirical premises in Problem/Motivation against the seeded tree — the 32-file/all-.py count, the absent conftest.py/fixtures dir, the 83-literal/13-file count, and Exploration's 13-site wiring including the lowercased body_sections.py:320 config entry — all four verified exact; found no new instance of the mandatory-obligation-over-an-unauthored-set family (AC-5 draws no finding, fifth consecutive clean round), no tautology, no zero-implementation route, and no unrunnable check; the "nine helpers" vs. eight-named count in Problem/Motivation is a real but immaterial prose slip feeding no AC. Nothing material survives; the middle-path sufficiency ruling remains Dave's and pending.
```

## Data Audit — 2026-09-07

**Recommendation: PROMOTE to specced**

First data-premise round on this item, cold-start. No prior `data-premise` fence exists on this
document or in `docs/vault-fixtures-rounds.md`, so there is no carry-forward of my own to re-read;
what I carry forward is the architect's ten rounds and the AC red-team's nine, both of which closed
at PROMOTE, and the P1–P20 premise table those rounds built.

### Trigger check

**Class 1 AND Class 2 both fire; this is not a Class-0 pass.** Class 1 — the Problem statement is
built entirely on quantified claims about corpus state (zero fixture data files, 83 frontmatter
literals across 13 files, `Exploration` at zero test sites, 8 declared types against 5 body
configs), and `## Approach` rests on structural facts about the live vault (one flat directory, glob
partition, note counts). Class 2 — every one of the five criteria is a NEW RULE whose correctness
depends on its effect against what exists today: AC-2 sweeps `TYPE_TO_MODEL`, AC-3 derives its floor
from both Tier-1 tables at test time, AC-4 derives its repository set from `__all__` and its reason
set from a `SKIP_REASONS` frozenset this item's build creates, and AC-5 reads
`_GENERIC_ORG_SUFFIXES` out of the package. A rule reasoned about and never run against the current
package is the exact WI-040 miss this gate exists for.

### Premise

The load-bearing empirical premises split cleanly in two, and the split is what decides this
verdict.

**(A) The IN-TREE premises — P1 through P20 — which every criterion's satisfiability rests on.**
These were measured, per the table's own currency note, in a DIFFERENT worktree
(`cage-wt-pul8uspy`) against HEAD `821177f` plus an uncommitted WI-022 delta. I am in
`cage-wt-do7tmnmo` and that delta is now committed here, so the currency statement is stale on its
face and every premise owed a re-run rather than a re-read. That is the whole of my Class-2
obligation and I discharged it below.

**(B) The OUT-OF-REPO premise — which note shapes occur in the live vault and at what frequency.**
The document declares this unsettled ("Not settled here, and deliberately so") and routes it to a
conductor precondition, `docs/vault-shape-census.md`. I confirmed by Glob that the artifact does not
exist in this tree today.

### Predicate + result — the in-tree premises, re-run in THIS worktree

Reader tools only (Read / Grep / Glob); this spawn arms no shell, so nothing below is a subprocess
or a live-vault call. Every row is a predicate I ran here, not a row I read off the table.

| Premise | Predicate re-run | Result in this tree |
|---|---|---|
| P1 | `Glob tests/**` | **32 files, all `.py`.** No `tests/fixtures/`, no data file of any extension. HOLDS. |
| P2 | `Glob **/conftest.py` | **None anywhere.** HOLDS. |
| P3 | `rg 'type: (person\|company\|…)'` over `tests/` | **Exactly 83 across exactly 13 files.** HOLDS to the digit. |
| P4 | `rg '[Ee]xploration'` over `tests/` | **Zero occurrences, zero files.** The committed-and-untested claim HOLDS. |
| P5 | Read `models.py:309-318` vs `body_sections.py:303-324` | **8 vs 5**, config keys `person`/`company`/`meeting`/`book`/`exploration`, so the difference is exactly `{watch, explore, gift-idea}` — AC-2's derived narrowing arm computes the three it names. `get_default_body` returns `""` for a missing key at `:337-338`. HOLDS. |
| P6 / P20 | Read `repositories/base.py:27-47` and `repositories/__init__.py` in full | **Three bare return literals at `:44`, `:46`, `:47`; type comment at `:37`; no frozenset, tuple, dict or Enum anywhere.** `__all__` is `:14-21` and imports end at `:12` — AC-4's round-9 cite correction is right and the pre-correction `:8-20` would have matched neither. HOLDS, and P20's "there is nothing to read" is the fact this item's one package change exists to end. |
| P7 | Read `pipeline-runners.yaml:34-38` | `obsidian_schemas/**`, `tests/**`, `scripts/**`, **`docs/**` in full, no carve-out.** HOLDS — and it is what makes AC-3(iv)'s digest necessary rather than ceremonial. |
| P8 | Read `pyproject.toml:39` | `packages = ["obsidian_schemas"]`. HOLDS; D6's deferral is grounded. |
| P9 | `rg 'ast'` over `tests/derivations.py` | `import ast` at `:24` with the single-homing rationale stated at `:15`; the module is the only home. HOLDS — AC-4's syntax scan has a legal place to live and no fixture module may name `ast`. |
| P10 | `rg 'José\|García\|Anne-Sophie\|Legrain\|Moises\|Vetup\|Sören'` over `*.py` | **36 across 6 files** — `test_wi126` 12, `test_repositories` 9, `test_name_validation` 5, `test_identity_index` 5, `test_name_cleaning` 4, `name_cleaning.py` 1. The per-file enumeration is exact; **the row's summary "35 in code" is one short of its own list** (35 is the five TEST files; the package hit makes 36). See the non-blocking note below. |
| P18 | `rg 'branch_id='` over `name_validation.py` | **Ten ids in `TIER1_BRANCHES` at the ten cited lines, five in `COMPANY_TIER1_BRANCHES` at `:373`–`:429`, union exactly ten.** `COMPANY_TIER1_BRANCHES` is present and committed in this tree at `:371`. HOLDS — AC-3's derived floor reads a real population of the stated size. |
| Flat-glob constraint | Read `base.py:189-198`, `:231`, `:258-275`, `:381-383`; Grep `file_pattern` across `repositories/` | **`person.py` and `company.py` declare no `file_pattern` at all**, so both inherit the default `@*.md` (`:196-198`); `meeting.py:52` and `book.py:51` declare theirs; `load()` globs at `:231`; `_owns` is `Path(self.file_pattern).stem != "*"` at `:265`; `_note_skip` reads `declared_type` at `:268`; `save()` writes `@{name}.md` at `:381-383`. **AC-4's double-ownership rule is the code's actual behaviour**, not an inference. HOLDS. |
| Repository set | `rg 'class \w+\(BaseRepository'` + Glob `repositories/*.py` | **Exactly four concrete subclasses, all four exported**, no fifth anywhere in the package. AC-4's derived set of size 4 is the real population. HOLDS. |
| Gate arms | Read `name_gate.py:315-368`, `writer.py:252` | `:319` is the non-person branch, the company judgement is nested at `:329-343` calling `validate_strict(…, branches=COMPANY_TIER1_BRANCHES)` at `:340-341`, `:344` returns `dict(introduced)` unchanged, the person arm is `:361-363`; `writer.py:252` calls `gate_write(fm, declared_type=fm.get("type"), …)`. **All four cites AC-2 leans on are exact.** HOLDS. |
| Live-vault numbers the document asserts | Grep the landed audits | **2,159 company notes** is grounded in `docs/company-stub-parity.md` (a landed, digest-anchored audit), not remembered; **1,147 person notes** is corroborated by `docs/identity-engine-endgame.md:3162`'s own data audit ("1147; skip surface 0"); the sentinel-stub churn claim is in `state/manifests/queue-2026-09-06.yaml:39`. HOLD. |
| WI-026 linkage | Read `state/manifests/queue-2026-09-06.yaml:52-54` | `needs: WI-016` present at exactly those lines. HOLDS. |

**Nothing rotted.** Twenty premises re-derived in a worktree the table was not written in, and every
load-bearing one reproduces exactly — including the three counts (83/13, 8-vs-5, ten `branch_id`s)
that three separate criteria quantify over. The one discrepancy is a summary integer, recorded
below.

### Counterexample hunt (WI-293)

`## Intent` and the criteria quantify universally over four enumerable domains, so a census of
shapes is not the deliverable here — the deliverable is the member classes each universal is FALSE
about by design, read off declarations rather than off filenames.

**Domain 1 — `set(TYPE_TO_MODEL)`, walked by reading `models.py:309-318` and then each model class
field by field.** AC-2 says every member has a fixture that round-trips through the real write door.
Three false-by-design classes exist and all three are ALREADY DISPOSITIONED in the document, which
is why I name them rather than raise them: (a) `watch`/`explore`/`gift-idea` have no
`ENTITY_BODY_CONFIG` entry, so their body expectation is `""` BY CONSTRUCTION — dispositioned as
AC-2's derived narrowing arm; (b) those three plus `exploration` have no repository and no glob, so
they are false-by-design members of AC-4's repository-level surface — dispositioned as a declared
exclusion, parser-level in AC-2 alone; (c) all six non-person, non-company types hit `gate_write`'s
pass-through at `name_gate.py:319-344`, so for them leg (c) proves a pass-through and not a gate —
dispositioned as a narrowed claim ("claimed at its real size").

**The two candidates I tested independently, because a legitimate exception is built to look
canonical.** `GiftIdea.for_person` (`models.py:242`) is the one field in the package with a
frontmatter alias (`for`), which would make `gift-idea` a member whose round-trip is false by
construction if the write path serialized by field name. It does not: `writer.py:112-117` reads
`field_info.alias` and emits the alias, so the key survives the round trip. **Not a counterexample —
`gift-idea` is an ordinary member.** Second, I looked for a concrete `BaseRepository` subclass
outside `repositories/__init__.py`'s `__all__` — the shape that would make AC-4's derived set
silently partial. There is none; four classes, four exports. **Neither candidate survived.**

**Domain 2 — the `branch_id` union, walked by `rg 'branch_id='` over both tables.** AC-3's floor
demands a census row per branch. One member is false-by-design and the document names it as such:
`empty` cannot occur in the live vault because `create_stub` guards its validator call with
`if name and name.strip():` — **verified at `repositories/person.py:1327`**, exactly as
`name_validation.py:298`'s comment claims. Dispositioned as a new declared outcome class (an
`ABSENT` row with count `0`, satisfying assertion (iii), outside assertion (i)). One further member
is worth recording because it is a *narrowing* nobody has stated: the person arm passes
`allow_phone_sentinel` (`name_gate.py:355-358`) when `phones` is non-empty, so a digit-named note
with phones is NOT refused — AC-2's GATE-CLEAN predicate is therefore strictly stricter than the
door for that one case. It is a conservative over-constraint on a `roundtrip_representative`, which
must be clean regardless, so it costs nothing and I raise it as a datum, not a finding.

**Domain 3 — the four exported repositories, walked by `__all__` and the subclass grep.** The
false-by-design member is `BookRepository`: its catch-all `*.md` stem makes `_owns(None)` return
False, so it owns NO untyped skip while the other three do. Already dispositioned as AC-4(b)'s
planted discriminator with an explicitly EMPTY declared mapping.

**Domain 4 — AC-5's reach, "every file under `tests/fixtures/vault/` plus `tests/fixture_vault.py`".**
The false-by-design member is the deliberately non-UTF-8 note, which no token extractor can walk.
Dispositioned as a named exclusion with a replacement obligation (complete bytes declared as a
lowercase hex literal, asserted byte-equal).

**Result: four domains walked, five false-by-design member classes found, all five already carrying
a disposition, and the two undispositioned candidates I constructed specifically to falsify the
universals both came back clean.** I record the domains and predicates rather than only the verdict,
per WI-293.

### The out-of-repo premise, and why it is a PROMOTE rather than a REVISE

`docs/vault-shape-census.md` does not exist, and the shape distribution it will carry is the premise
D1's whole amendment turns on. A gate that stopped here would be reading the situation backwards, so
I state the reasoning rather than just the call.

**No criterion asserts a live-vault fact.** I checked each of the five for a claim the census could
falsify and found none. AC-3's equality runs against *whatever the census declares*, scoped to
MEASURED rows, with ABSENT rows first-class; its floor is read from the package, not from the vault.
AC-5(c) is a CONTAINMENT precisely so the earlier artifact need not predict the later corpus. The
criteria are agnostic to what the census measures BY CONSTRUCTION — which is the opposite of the
20%-vs-65% failure this gate exists to catch, where a criterion hard-codes a number nobody ran. The
one thing the census could invalidate is corpus SIZE (a vault with forty measured shape classes
obliges more than ~50 notes), and "~50" appears only in the reslice and `## Approach` as an
approximation, never in a criterion.

**The premise is not deferred, it is SEQUENCED, and the sequencing has teeth.** The artifact is a
declared precondition landing in HEAD before Dave signs; AC-3(iv) then freezes it by digest with the
expected value in the SIGNED criterion rather than in a build-owned module — which matters exactly
because P7 (re-verified above) makes `docs/**` builder-writable in full. An unlanded artifact with a
machine-checked shape, a stated ordering and a fixity mechanism is grounding deferred to the only
actor who can perform it, not grounding skipped. Requiring the census before `specced` would invert
the pipeline's own ordering and buy nothing, since the spec-writer's job does not read a census row.

**Where the machine stops, said plainly.** My verdict grounds the premises the SPEC rests on. It
does not and cannot ground the census's contents — that is the conductor's act, and this document's
own build-start re-grounding hook (WI-022 absorption) is what re-checks it if it rots between now
and build.

### Non-blocking note — one summary integer, recorded rather than folded

P10 reads "**38 hits across 8 files — 35 in code**" and then enumerates six files summing to **36**.
The enumeration is exact (I reproduced all six counts); the summary is one short, because 35 is the
count in the five TEST files and the `name_cleaning.py` hit makes the code total 36. `## Problem /
Motivation`'s own phrasing — "35 literals scattered across five test files … plus one in
`obsidian_schemas/name_cleaning.py`" — is CORRECT, so this is P10's summary alone and the Problem
statement does not inherit the error. It is the same "stated number vs. actual list" family the
document has already corrected twice (P16's fifteen-vs-sixteen at round 7), it is non-blocking on
the same reasoning those were, and nothing rests on it: no criterion quantifies over P10, whose role
is to establish that the corruption corpus already exists and is scattered — a claim 36 supports as
well as 35. I do not fold it myself; a gate does not edit another section's evidence, and the next
hand on this document can correct it in one word.

### Conclusion

Every empirical premise the spec's correctness rests on is grounded, and I re-ran the predicates in
a worktree the premise table was not written in rather than trusting a currency note I could see was
stale. Twenty premises, three of them populations that criteria derive over at test time, all
reproduce exactly. The four universals were walked to their false-by-design members and every one of
those members already carries a disposition. The single out-of-repo premise is unsettled by design,
asserted nowhere, and sequenced behind a precondition with a digest. The one defect I found is a
summary integer that feeds nothing. This item is grounded and ready to be specced.

```verdict
gate: data-premise
verdict: PROMOTE
date: 2026-09-07
model: claude-opus-5
note: First data-premise round; Class 1+2 both fire and I re-ran P1–P20's predicates in THIS worktree rather than trusting the table's stale currency note (measured in cage-wt-pul8uspy, WI-022 delta now committed here) — all reproduce exactly, including the three derived populations criteria quantify over (83/13 literals, 8-vs-5 type/body-config, ten branch_ids) and the flat-glob ownership rule AC-4 declares, which is the code's actual behaviour at base.py:196-198/:265/:268. Counterexample hunt over four enumerable domains found five false-by-design member classes, all already dispositioned, and the two candidates I constructed to falsify the universals (GiftIdea's `for` alias round-trip; a concrete repository outside `__all__`) both came back clean — writer.py:112-117 emits the alias, four subclasses and four exports. The live-vault shape distribution is unsettled BY DESIGN and no criterion asserts it: AC-3 runs against whatever the census declares with ABSENT first-class, AC-5(c) is a containment for exactly that ordering reason, so this is grounding sequenced behind a digest-frozen precondition, not grounding skipped. One non-blocking defect: P10's "35 in code" is one short of its own six-file enumeration (36); the Problem statement's own phrasing is correct and nothing quantifies over it.
```

## Spec Review — 2026-09-07 (round 2)

**Recommendation: REVISE — return to spec writer (gaps to fix)**

Rulings on record: the AC-5 structural-wall-vs-middle-path sufficiency question is Dave's and is recorded above for sign-off; the census's absence from HEAD is SEQUENCING rather than a grounding gap (data audit, 2026-09-07); WI-020's specification-altitude and fold-and-close closures — I route against all three and nothing below re-litigates any of them.

Read from line 1 in full and walked the bar from scratch rather than against round 1's gap list. Round 1's four findings are all closed and I verified each closure against the tree rather than against the fold's prose: §3.1 prescribes `ensure_project_interpreter(__file__)` and the six sibling callers are at exactly the cited lines; §6.4 carries the hex excision; AC-1(a) and §5.2 now both say the key is the filename; §4's disposition table names all eight sites a grep returns and Task 11 closes all three hand-typed test ones. Round 1's three non-blocking notes are closed too (Task 12 derives its check-name list, §11 records the four discarded modules with `test_concurrent_access.py:1077-1089`'s count pins, AC-1(b) exercises the second `materialize_vault` call), as are both navigational nits.

Two of the three blocking findings below land on the text those closures ADDED — the hex excision's own presence assertion, and the W-16 parity wall — which is the fold-breeding-its-own-next-finding shape this document has recorded three times, not a re-opening. The third is a claim about this tree that does not hold.

### Citation verification

Every `file:line` this round's new material leans on was read at its cited lines in this worktree. **All verified ✓.** Specifically re-read and confirmed exact, none inherited from round 1's list: `tests/ac_interpreter.py:7-25` (the mechanism, verbatim), `:14-20` (the `--ac-python` clause), `:30-33`, `:123-130` (`ensure_project_interpreter`'s `find_spec` fast path), `:136-148` and `:142-148` (the two fail-closed raises), `:150-155` (`os.execve`). `tests/test_ac_interpreter.py:23` (CORPUS_COUPLING), `:38` (ROOT from `Path(__file__).resolve().parent.parent`), `:40` (`WORK_ITEM_DOC` = `docs/write-door-bypasses.md`), `:57-73` (`criterion_checks`, fence-scoped, opener matched as exactly the bare fence word), `:76-87` (`check_module`), `:90-95` (`run_foreign` under `sys.executable -S`). The six bridge callers at `test_company_name_contract.py:25`, `test_address_splitter.py:38`, `test_name_gate_identifiers.py:41`, `test_name_gate_refusals.py:41`, `test_name_gate_wall.py:40`, `test_name_gate_delta_rule.py:37`. `tests/support.py:1-19` and `temp_dir` at `:30-37`. `tests/derivations.py:9-12`, `:14-17`, `:24`, `:28`, `:50-53`, `:183-206` (`python_files_under`, recursive `rglob`), `:213`, `:217`, `:243`, `:543`, `:1366`. `tests/test_name_gate_wall.py:_check_the_ast_capability_stays_single_homed:1132` with the live equality at `:1136-1138`; `tests/test_loud_fail_harness.py:18-20` (the required-subset sentence), `:65`, `:79-87`, `:88`, `:93-97`, `:103`. `tests/test_concurrent_access.py:1077`, `:1085`, `:1088`, `:1089` — all four count pins, none moved by this item. `tests/test_vault_path_required.py:382`, `:387`, `:421`, `:436`, `:451` (the `errors="replace"` read that makes the non-UTF-8 corpus member safe under W-8). `tests/test_loud_fail_load.py:167`, `:187-188`, `:209`; `tests/test_name_gate.py:109`, `:152`. `obsidian_schemas/repositories/base.py:37`/`:41-47`/`:189-198`/`:231`/`:258-265`/`:267-275`/`:301-307`/`:309-311`/`:334-342`; `repositories/__init__.py:8-12` imports and `:14-21` `__all__` with `VaultPathNotConfiguredError` at `:16`; `book.py:50-53`/`:55-57`/`:59-87`; `errors.py:65-67`/`:70-72`/`:112`. `name_gate.py:319`/`:329-343`/`:340-341`/`:344`/`:355-358`/`:361-363`. `writer.py:89`/`:134`/`:160-169` — `write_markdown_file` takes BOTH `entity=` and `frontmatter=`, so §5.3's and Task 4's two different call shapes are each legal. `pyproject.toml:38-39`/`:41-43`.

**Two independent structural re-runs, because §4's argument and Task 12's pin are both counts.** A grep for the three reason literals over every `*.py` in this worktree returns exactly the eight sites §4's disposition table names and no ninth — the round-1 correction is complete, and the two non-literal near-misses the wall must not match (`base.py:299`'s prose comment, `test_loud_fail_load.py:210`'s local variable) are both outside it. A grep for `^```criteria` over this document returns exactly five, all inside `## Acceptance Criteria`, so Task 12's "exactly 5" pin is true today.

### Blocking issues

**1. AC-5(a)'s hex-excision presence assertion is applied PER FILE and no corpus note contains any declared hex literal — so the leg round 1 fixed is RED by construction again, on ~50 wholly correct notes.** §6.4 states the implementation as "over `excise(text, DECLARED_HEX_LITERALS)` **for each file in reach**", and AC-5(a) then says each declared literal is "asserted FIRST to be well-formed lowercase hex of even length … **and asserted to OCCUR in the text it is excised from**, so the exemption cannot become a hiding place and an exemption declared for a literal that is not present is RED rather than free." Under the stated per-file excision, "the text it is excised from" is one corpus note's bytes — and `CORPUS_DIGEST` and `NoteSpec.raw_bytes_hex` live in `tests/fixture_vault.py`, never in a corpus note. So the presence assertion holds for exactly one of the ~51 files in reach and fails for every other. The alternative reading — presence over the REACH, i.e. the union — is satisfiable and is plainly what the anti-hiding-place argument wants, but nothing in the document says which, and the harmful reading is the literal one. This is the same shape as round 1's finding 3 (AC-1(a)'s "repo-relative", where the criterion's literal reading made leg (b) unsatisfiable), reproduced by the fold written to close round 1's finding 2, and it has no in-cage remedy once the criterion is signed: the builder facing ~50 REDs on a correct corpus must either narrow a signed criterion or delete the assertion. **Fix:** state the presence assertion's domain — that each declared literal must occur somewhere in the reach, and the excision is applied to every file's text whether or not that file contains it. Say it in AC-5(a), because that is the text that gets signed, and reconcile the three surfaces that repeat the phrase: `## Design` §6.4, Task 8, and `## Edge Cases`'s "A declared hex literal read as a phone" entry.

**2. §11's W-16 row and Task 12 prescribe a parity wall that is green over a run proving nothing — the shipped sibling wall this item copies rejects exactly that, in two clauses the spec drops.** Task 12 says the parity test "for EACH name runs the shipped `run_foreign(check_module(name), name)` (`:90-95`) and asserts exit 0". `tests/test_ac_interpreter.py`'s own use of those predicates asserts two things, not one: exit 0 (`:111-115`) **and** `"[ac_interpreter]" in proc.stderr` (`:116-120`), whose failure message is "exited 0 WITHOUT delegating — the foreign interpreter imported the project's deps, so this run proves nothing about the battery's conditions". It also ships a near-miss control (`test_a_failing_delegated_check_is_red_not_silently_green`, `:126-138`) proving a nonexistent check is RED under the same shape. The spec imports the three predicates and re-implements the test around them with half its oracle. The consequence is concrete rather than theoretical: `-S` strips `site`, so the delegation marker is what proves the child actually LACKED pydantic, and on any interpreter where the runtime deps survive `-S` (an ambient/CI install rather than a venv) every check exits 0 without delegating, `test_this_items_checks_pass_under_the_conveyors_interpreter` is green, and Verification's mutation 9 — "the most important mutation in the list", the one whose green half is the finding — does not fire. That leaves R9 (a burned build attempt, five-of-five `ModuleNotFoundError`) uncovered by the only thing the spec says can cover it: §3.1 is invisible to the floor by design, W-10's population does not reach this item, and §11's sweep predicate structurally cannot see a capability injection. This is also WI-235's rule on the wall's own terms — the check's oracle is a count of exit codes, and the spec names neither a shape the wall must resolve nor a near-miss it must not. **Fix:** in Task 12 and §11 W-16, assert the delegation marker alongside exit 0, and add the near-miss the shipped module carries (one nonexistent check name through the same `run_foreign`, asserted non-zero AND delegated). Both are the shipped module's own assertions, so this adds no re-implementation.

**3. `## Verification`'s regression enumeration is not its own named sweep's output — "the twelve modules that import `tests/derivations.py`" names twelve and ten import it.** The paragraph opens "**Regression — DERIVED from the edited surfaces, not inherited.** Sweeping the resolved test root for modules that name each `## Write Targets` path returns…". Run here: `tests/test_vault_path_required.py` contains **no occurrence of the string `derivations` at all** — it neither imports the module nor names it — and `tests/test_name_gate.py`'s single occurrence is the docstring line at `:15` ("that capability is single-homed in `tests/derivations.py`"), not an import. The real importer set is exactly ten: `test_write_routing`, `test_name_gate_wall`, `test_loud_fail_write`, `test_loud_fail_parse`, `test_loud_fail_load`, `test_loud_fail_harness`, `test_lint_vault_fix_gate`, `test_concurrent_access`, `test_company_name_contract`, `test_address_splitter`. (Four further modules — `test_name_gate`, `test_name_gate_identifiers`, `test_name_gate_refusals`, `test_name_gate_delta_rule` — plus `test_phone_normalization` carry the same one-line docstring mention and import nothing.) **This costs nothing at build and I say so plainly:** the direction of the error is over-listing, and both spurious members are already in the `base.py` row (correctly) and so get run anyway. It is blocking on the accuracy rule rather than on buildability — the paragraph asserts a falsifiable fact about this tree that does not hold, in a section that advertises itself as derived, and it is the fifth instance of this document's own "stated number vs. actual list" family (P16's fifteen-vs-sixteen at round 7, round 8's four-item residue, the data audit's P10 35-vs-36, round 1's skip-reason enumeration short by two). Dave's pending sufficiency ruling reads this document's exhaustion claims as true, which is the reason to fix it rather than note it. **Fix:** replace the count and the list with the sweep's actual output — ten modules — or state the predicate as "modules affected by an edit to this path" and keep the two, which is defensible for the `base.py` row's three members (`test_write_routing`, `test_repositories`, `test_concurrent_access` sweep `python_files_under(PACKAGE_ROOT)` without naming the path) but is not what the sentence says.

### Non-blocking notes

- **Task 6 reads as demanding a `Verdict` for an ABSENT floor class, which AC-3 says obliges none.** Task 6: "For each floor class, assert the manifest's declared `Verdict`." AC-3(iii) carries both "For each class on the floor, the manifest declares the verdict the specimen must produce" and, three sentences later, "a live vault holding no empty-named note gets an ABSENT row … and obliges no specimen". The criterion's own ABSENT sentence resolves it and a builder would almost certainly read it that way, so this is a clause rather than a finding — but §9.4 names `empty` as the likely ABSENT row, so the case will actually arise. One qualifier in Task 6 ("for each MEASURED floor class") closes it.
- **§3's import list for `tests/fixture_vault.py` includes `unicodedata`, which nothing in that module uses.** The extractor `_runs`/`identity_tokens` is the only consumer and §6.1, Task 8 and the Self-Review Dry Run all place it in `tests/test_fixture_vault.py`. Harmless, but §3's list is the module's prescribed contents and an unused stdlib import there invites a builder to put the extractor in the manifest module, which `## Approach`'s "three things and no test logic" forbids.
- **Task 9's negative fixtures plant real-looking identifiers into the one new module AC-5's reach deliberately excludes.** The battery prescribes `naomi@speechmatics.com`, `+44 7911 123456`, `https://linkedin.com/in/someone`, `José García`, `Anne-Sophie Legrain`, `Dave -> Thomas Gatten` and `Me to David Field` in `tests/test_fixture_vault.py`, whose reach under AC-5 is the corpus plus `tests/fixture_vault.py` only. Every one of those literals already exists in the tree (`tests/test_name_validation.py:268`, `:274`, `:453` carry the address verbatim), so this adds copies rather than new personal data — but `## Constraints discovered` says in as many words that this item "declines to add more", and a constructed non-reserved domain and a constructed non-drama number prove leg (a)'s refusal arm exactly as well. Worth one sentence either way: change the fixtures, or record that duplicating an existing in-tree literal is the deliberate reading of "declines to add more".

### Carried-forward notes

- **Architect round 10, note 2** (AC-4's "returns BY NAME rather than as re-spelled literals" is prose the scan's first arm cannot discriminate) — still OPEN and re-deferred for the stated reason: §4 now prescribes the by-name form and §10 P-2 routes the one settling clause to the one-time pre-origination edit, where it costs nothing. The safety property is unaffected under either spelling, which is why it stays a note.
- **Architect round 10, note 3** (this document should use the project's rounds drawer) — still PARTIALLY actioned. `docs/vault-fixtures-rounds.md` exists and the `### Archived Rounds` pointer is in place, and I re-confirmed the drawer is harmless to AC-3(iv) (fence-scoped) and to Task 12's `criterion_checks` pin (which reads this document only). The live doc is now ~4,350 lines carrying architect rounds 6, 8, 9 and 10, red-team round 9, the data audit and two spec reviews inline; the conductor act the note asks for is still unfinished.
- **Data audit, 2026-09-07** (P10's "35 in code" against a six-file enumeration summing to 36) — CLOSED. P10 now carries the correction in place with the reason, and `## Problem / Motivation`'s own phrasing was already correct.
- **AC red-team round 9** (`## Problem / Motivation`'s "Nine helpers" against eight backticked names) — CLOSED. The list now names nine (`_write` added, and it exists — `tests/test_loud_fail_load.py:174`) and the sentence declares the number explicitly non-load-bearing.
- **Round 1's three non-blocking notes** (Task 12's "six" check names; §11's four undeclared discards; the untested idempotency rule) — all CLOSED, and each was verified rather than taken from the fold: Task 12 now derives the uniqueness obligation as a predicate over the modules' own `def test_` sets, §11 names all four discarded modules with `test_concurrent_access.py`'s four count pins read here, and AC-1(b) plus Verification mutation 11 now exercise the second `materialize_vault` call and the no-clean rule.

### Bar check

Walked every check of `docs/spec-quality-bar.md`. Satisfied: Check 2 (§10's P-1…P-9 enumerate the prerequisites, the trust boundary and the WI-300 ordering; P-4's premise is now the bridge rather than the YAML comment, and I confirmed `tests/ac_interpreter.py:14-20` says exactly what P-4 now quotes), Check 4 (all ten categories resolved, `OPEN: None`, and the three previously prose-only resolutions — idempotency/no-clean, the ISBN, the `-Voxleaf` run — now each carry an exercising assertion), Check 5 (twelve canonical `- [ ] **Task N — …**` definitions, ordinals unique and contiguous, every one carrying a well-formed lowercase `verify:` declaration — ten `test_` arms whose names all resolve inside this item's write targets, one `baseline` and one `hand-run`, each with its reason; no `verify:` is a command and none writes), Check 6 (WI-235's shape controls are Task 2's two planted batteries and Task 9's shape + near-miss batteries, all driving the live predicates; WI-278's arm is declared per reader with the `CORPUS_COUPLING:` line; WI-173 correctly does not fire), Check 7, Check 9 (ten concrete rows, R9 and R10 both carrying the round-1 findings), Check 10 (five well-formed fences, all `kind: test`, each `check:` a bare name resolving to `tests/test_fixture_vault.py` alone), Check 11 (D-1…D-9; I re-read D-5, D-6, D-7, D-8 and D-9's artifacts here and each supports its specific claim — D-9's eight-site grep reproduces exactly). Check 12 does not fire: the ACs are drafts and no `ac-signoff` fence exists. Check 1 carries finding 3; Check 3 and Check 8 carry findings 1 and 2.

**Write-Targets coverage (WI-132), run task by task.** Every file a task names is declared: Task 2 → `obsidian_schemas/repositories/base.py`, `tests/derivations.py`, `tests/test_fixture_vault.py`; Task 3 → `tests/fixtures/vault`; Tasks 4–9 → `tests/fixture_vault.py`, `tests/test_fixture_vault.py`; Task 10 → `tests/test_parser.py`, `tests/test_writer.py`, `tests/test_repositories.py`; Task 11 → `tests/test_loud_fail_load.py`, `tests/test_name_gate.py`; Task 12 → `tests/test_fixture_vault.py`. No fence declares a path no task writes, and `tests/ac_interpreter.py` / `tests/test_ac_interpreter.py` are correctly READ-only and named on `## Scope Boundary`'s unchanged list. Every declared path is inside `write_authority` (`pipeline-runners.yaml:34-38`, re-read), so the D7b axis and the WI-290 level selector both read the item's real touch surface. The conscious-pin sweep found no moved pin: `test_concurrent_access.py`'s four, `test_name_gate.py:172`'s `len(TIER1_BRANCHES) == 10`, `test_name_gate.py:124`'s `len(REASONS) == 16`, `test_loud_fail_harness.py:88`'s `len(six) == 6` and `test_name_gate_wall.py:1161`'s `len(sites) == 8` are each unmoved by a frozenset, three string constants and two new scans, and §4's decision not to join the `six` dict is correct against `:18-20`.

There is no `## Threat Model` on this document — I confirmed it against the section list, as §10 P-9 states — so no `kind: required` mitigation is outstanding and the absence of `## Mitigation Folds` is correct.

### Build-runner dry-run

Walked the Implementation Plan top-to-bottom as the builder. The precondition abort gate remains the strongest thing in the plan. Tasks 1–12 each name their files and insertion points; §1.2's grammar, §1.3's six rules, §3's `LOADABLE` arithmetic, §5.1/§5.2's two walks, §5.4's ownership table and §6.1's extractor leave no decision open, and I confirmed the ownership table is the code's actual behaviour including the one arm no criterion states outright — `BookRepository._load_file` (`book.py:59-87`) reads bytes itself at `:71`, so the non-UTF-8 member reaches its own `except` and is declined by `_owns(None)` rather than never being read, which is what makes AC-4(b)'s "book's mapping is EMPTY" true rather than accidental.

Three questions a cold-start builder would ask that the document does not answer, and they are findings 1, 2 and 3: *"`CORPUS_DIGEST` is not in any corpus note — do I assert the excised literal is present in each file, or somewhere in the reach?"*; *"the shipped wall I am importing from fails a check that exits 0 without delegating — do I assert that too, or only exit 0?"*; *"the regression list tells me `test_vault_path_required.py` imports `derivations.py`, and it does not name it at all — which of the two is wrong?"* The first has no in-cage remedy once AC-5 is signed; the second is the difference between a wall and a wall-shaped no-op.

```verdict
gate: spec-reviewer
verdict: REVISE
date: 2026-09-07
model: claude-opus-5
targets: AC-5, Task 8, Task 12, #verification, #design
prior: held
basis: folded-material
findings: 3/6
note: Round 1's four findings all close and I verified each closure against the tree rather than the fold's prose (the six bridge callers at their cited lines, §6.4's excision, AC-1(a)/§5.2 now agreeing on the filename key, and §4's eight-site disposition table reproduced exactly by an independent grep); its three non-blocking notes close too. Three blocking, and TWO of them land on the text those closures added, which is the fold-breeding-its-own-next-finding shape rather than a re-opening: (1) AC-5(a)'s new hex excision asserts each declared literal is "asserted to OCCUR in the text it is excised from" while §6.4 applies the excision "for each file in reach" — CORPUS_DIGEST and raw_bytes_hex live only in tests/fixture_vault.py, so under the literal per-file reading the leg is RED on all ~50 correct corpus notes, which is the same criterion-vs-code fork as round 1's repo-relative finding and has no in-cage remedy after signature; (2) §11 W-16 and Task 12 assert only exit 0 from the shipped run_foreign, dropping the two clauses tests/test_ac_interpreter.py:116-120 and :126-138 carry — the delegation-marker check whose own message is "exited 0 WITHOUT delegating … proves nothing about the battery's conditions", and the nonexistent-check near-miss — so on any interpreter where the deps survive -S the parity wall is green over a run that proves nothing and Verification's mutation 9, the one the spec calls the most important in the list, never fires (WI-235: a count-of-exit-codes oracle with no shape and no near-miss); (3) `## Verification`'s "DERIVED, not inherited" regression enumeration names "the twelve modules that import tests/derivations.py" and ten do — tests/test_vault_path_required.py contains no occurrence of the string at all and tests/test_name_gate.py's only one is the docstring line at :15 — which costs nothing at build (both are already in the base.py row) but is a falsifiable claim about this tree that fails, and is the fifth instance of the stated-number-vs-actual-list family whose exhaustion claims Dave's pending sufficiency ruling reads as true. Nothing here touches the approach, the census sequencing, or AC-5's scope question.
```

## AC Sign-off

```verdict
gate: ac-signoff
verdict: PROMOTE
date: 2026-09-08
reviewer: dave
channel: conversational
signed_at: 2026-09-08T07:44:54+01:00
provenance: attested
ac_hash: 3d15772495dc
intent_hash: a488ac920361
ac_hash_AC-1: ec400d9c340f
ac_hash_AC-2: 1b36bfaf4234
ac_hash_AC-3: 1ec178617d40
ac_hash_AC-4: a82228579211
ac_hash_AC-5: 1a884834e329
artifact: docs/spec-reviews/WI-016-dave-review-2026-09-08-2.md
```

## Threat Model — 2026-09-08 (round 3)

**Recommendation: PROMOTE to threat-modeled**

Third round. Re-read cold from line 1, plus `docs/vault-shape-census.md` end to end, plus the four
surfaces round 2's finding landed in (`## Scope Boundary`'s standing authoring rules, §10 P-9 as
rewritten, the new §10 P-10, R1's cell), plus `## Mitigation Folds` and §6.5 re-read at their bytes,
plus — new this round — the two artifact surfaces no threat-model round has swept: the rounds drawer
and this item's `docs/spec-reviews/` review artifacts. Rulings I route against rather than
re-litigate, unchanged across all three rounds: AC-5's structural-wall-vs-middle-path sufficiency
question is Dave's and is recorded for sign-off; the census's sequencing is settled by the data audit;
D1's amendment, the byte-copy rule and the derived sweeps have now drawn no finding in twenty-three
gate rounds and draw none here. Spec review round 5's findings 2 and 3 are that gate's and I do not
re-judge them — I record only that finding 2 has landed, since it moved a literal I would otherwise
have had to re-derive (§5.3 and Task 6 now read `pattern="pure_digit_name"`, `:2155`, `:2162-2170`,
`:3258-3264`).

### Round 2's findings, re-measured rather than read off the fold

**The blocking finding is CLOSED, and I verified the closure by re-running the measurement rather
than reading the remediation's prose.** Round 2 found that round 1's census remediation had moved two
novel live-vault values into this document — four prose positions in `## Threat Model — 2026-09-08`
plus one inside that round's verdict `note:`, five in all. A sweep for the redaction marker now
returns **exactly five positions, in exactly the one file, and nowhere else in the worktree**:
`docs/vault-fixtures.md:5785`, `:5788`, `:5791` and twice at `:5881` (the verdict `note:`). Each
carries the value's LOCATION (its census row) and its CHARACTER PROFILE and no value — reported here
by the same rule, which is now this item's own. The finding's argument survives the redaction intact:
the class ids, the line citations and the constructed specimens beside them still carry it, which is
exactly what round 1 demanded of the census and what round 2 argued was practicable here.

**The ordering held, and this is the half that could not have been recovered.** Round 2's urgency
argument was structural rather than rhetorical: `### Archived Rounds` declares
`docs/vault-fixtures-rounds.md` byte-for-byte, append-only and **never rewritten**, so a drawer copy
taken before the redaction would have put both values past the reach of any correction. I checked the
drawer rather than assuming: it carries AC red-team rounds 1–8 and architect rounds 1–7+ and **no
`## Threat Model` section at all**. The copy has not been taken. Redact-first-copy-second was
observed, and §10 P-10(d) now records the ordering as the reason the copy is only now unblocked.

**The durable half landed, and it landed as a CLASS rather than as the two instances.** `##
Scope Boundary` (`:3729-3763`) now carries three standing authoring rules under a stated generator —
*an identity-shaped value entering one of this item's artifacts through a surface no wall reaches* —
with the residue named exactly (`tests/test_vault_path_required.py:387` excludes `docs` from the only
repo-wide markdown scan, re-read here at `:382-387`; AC-5's reach is the corpus plus the manifest and
nothing else). The three: a gate reporting a leaked identifier names its location and character
profile, never the value; the same rule binds `tests/test_fixture_vault.py`, the one module AC-5
deliberately excludes, with the already-committed-versus-novel test stated as a standing constraint
rather than as Task 9's two hand-corrected instances; and the rule follows a round into the drawer,
with the ordering recorded. They bind conductor, gate and builder alike and sit outside the
hash-signed span. **This is what I asked for and it is stronger than what I asked for** — I asked for
one sentence and for the `tests/test_fixture_vault.py` note to ride it; the writer stated the
generator and closed the residue as a set.

**Round 2's non-blocking note 2 (the `tests/test_fixture_vault.py` authoring constraint, twice
deferred) is CLOSED** by the second of those bullets. **Note 1 is NOT closed** and is carried forward
below — but it is no longer merely un-actioned: §10 P-10(c) records it as an outstanding CONDUCTOR
act, with the fix, the reason it must not be closed by widening M1's scan, and the instruction to
bundle it with the owed re-sign so it costs no second digest. A note routed with its cost is a
different thing from a note dropped.

### The sweep this round adds — the wall's reach, one step further out

The one thing three rounds of this finding have taught is that the leak travels to whichever of this
item's artifacts no wall reaches, so I stopped chasing the instance and swept the residue the standing
rules now name. Two surfaces have never been examined by any threat-model round, and both are about
to enter permanent history.

**The `docs/spec-reviews/` review artifacts — `WI-016-dave-review-2026-09-08.md` and
`-2.md`, both currently untracked.** These are written by `bin/review-spec-helper.py`, carry the
FROZEN `## Acceptance Criteria` text the `ac-signoff` fence hashes, and are named by that fence's
`artifact:` key, so they are committed evidence rather than scratch. Swept for identity-shaped
content: they carry class ids, constructed specimens, and one real-looking name — the `rfc2822_leak`
branch's own specimen at `-2.md:334-335` — which is a verbatim re-typing of
`obsidian_schemas/name_validation.py:205`. Pre-existing tree literal, permitted by Task 9's recorded
reading. **Clean.**

**The rounds drawer.** Its identity-shaped hits are the same `rfc2822_leak` specimen (`:1353`) and a
`name_cleaning.py:76` calendar-prefix literal (`:1753`), both pre-existing. **Clean.**

**And an independent identity sweep over `docs/vault-fixtures.md` itself**, run because the standing
rules are new and nothing has yet swept the document they govern. Every phone-shaped literal in the
document is reserved by construction — Ofcom's drama range (`07700 900xxx`, `+44 7700 900123` and the
`900000-900999` band statement) or NANP 555 — so none can reach a live subscriber. Of the three
email-shaped literals, one is RFC 2606, one is a constructed pseudonymous domain round 1 already
identified as a deliberately non-reserved REFUSED fixture in leg (a)'s battery, and the third is a
real-looking address at a real company (`:3367`, and re-typed by two gate sections). **I measured that
third one rather than ruling on it by eye, because it is the only member whose character profile would
make it a finding if it were novel:** it is already committed in this tree at
`tests/test_name_validation.py:268` and `:274` (both re-read here at their lines), at
`tests/test_resolve_or_create.py:133` and `:176`, and at `obsidian_schemas/repositories/person.py:730`.
Pre-existing, so Task 9's reading permits it — and the document already says so in place at `:3367`
rather than leaving a later gate to re-derive it. I cite it by location rather than re-typing it into
a new prose position, which is the rule this round is testing. **No third member of the class exists.**

### Trigger check

The same four triggers fire and none has moved: *persists data* (a ~50-note corpus, a manifest module
and a census document, all committed); *filesystem operations on user-owned files*
(`materialize_vault(dest)`); *crosses a trust boundary* (§10 P-8 — real personal data crossing INTO
permanent git history); *handles input from an external source* (the live vault, transcribed by the
conductor). Still not fired: no secrets, credentials, tokens or OAuth scopes; no MCP scope or tool
permission; no network and no outbound message; no access-control change. `## Acceptance Criteria`
still carries five fences, every one `kind: test` and none `kind: command`, so the battery opens no
unsandboxed shell.

### STRIDE re-review, scoped to what moved

Nothing that moved this round is code. The redaction, the standing authoring rules, P-9's rewrite,
P-10 and R1's extended cell are all prose in this document; §5.3 and Task 6's corrected literal
changes an expected `.pattern` value and adds no surface. I re-walked each category against that
rather than assuming.

**Spoofing.** Unchanged and no finding — no authentication boundary anywhere in this item.

**Tampering.** Improves again, and this is the round it becomes durable rather than promised. The
artifact that grounds the privacy wall is inside it on every floor run (M1, Task 8, after the fixity
assertion), the same predicate runs one build phase earlier as a fail-closed refusal (M2, Task 3), and
the residue those two do not reach — this item's other documents, and the one module AC-5 excludes —
is now closed by a stated authoring rule instead of by two hand-corrections. The digests still bind:
AC-3(iv) and AC-5(c) each assert `sha256` over the census independently, and I cannot recompute either
from inside this cage, which is right — a wrong constant is RED at Task 3 before a corpus byte is
authored. No finding.

**Repudiation.** Unchanged. Every census row still carries its command and verbatim stdout under a
counting constraint; Tasks 1 and 12 bracket the build with recorded floor runs; §10 P-10 is new and
improves the audit trail rather than harming it, by putting the three outstanding conductor acts in
one place with their costs instead of scattered across gate rounds. `SkippedNote.detail` is still
`bounded_detail(error)` and "never the raw rendering" (`repositories/base.py:38`, re-read here with
`:36-38` and `:41-47`), so a malformed specimen's contents do not reach a WARNING line when AC-4 loads
the corpus through four repositories. No finding.

**Information disclosure.** The subject of all three rounds, and the first round in which it draws no
finding. The instance is redacted, the ordering held, the class is closed by a rule that binds every
actor writing here, and my sweep of the two remaining unwalled artifact surfaces plus the document
itself returns no member. The two declared residuals are unchanged and both are honest rather than
hidden: a real name can still be *deliberately typed* into `CENSUS_PROSE_ALLOWLIST` or into `NAME_POOL`
(§6.5 item 4 says so in terms, and the disjointness assertion closes only the quiet-move bypass), and
the pool table's non-occurrence ground truth is the conductor's recorded scan rather than an in-suite
assertion, because the suite is hermetic. That is the same bar AC-5(b) sets for the corpus and it is
the subject of the sufficiency question already on record for Dave. Routing against it, not
re-opening it. No finding.

**Denial of service.** Unchanged. No network, no live-vault read, no subprocess in any of the five
`kind: test` checks. M1's scan adds one decode of one committed file to a check that already decodes
~50; M2's is a builder inspection. No finding.

**Elevation of privilege.** Unchanged, and I re-checked the one thing that could have moved: neither
fold turns `docs/vault-shape-census.md` into a write target. M1 has the SUITE read it, M2 has the
BUILDER refuse on what it finds, `## Scope Boundary` keeps it on the unchanged list, and §10 P-9's
closing paragraph states the wrong reading and rejects it. `materialize_vault` is untouched since
round 1's attacker read — bare `src.name` into `dest`, no `rmtree`, no `unlink`, no mode change, and
AC-1(b) still asserts positively that a foreign file planted in `dest` SURVIVES a second call. No
finding.

### Mitigations verified in place

1. **M1 — the census's own bytes inside the closure they certify.** §6.5 with six decisions taken at
   spec rather than build time, and Task 8 (`:3306-3320`) with the scan ordered AFTER the fixity
   assertion, the pool-row set asserted NON-EMPTY first (LESSONS #46), `CENSUS_PROSE_ALLOWLIST` kept
   out of the manifest so AC-5(b)'s signed "three literal frozensets" sentence stays true, its
   membership authored against the LANDED artifact rather than §6.5's illustrative list, and the
   disjointness assertion that closes the quiet-move bypass. Verified in place, re-read at its bytes.
2. **M2 — the same predicate one build phase earlier, fail-closed.** §6.5 and Task 3 (`:3142`) under
   the Abort Protocol, with the no-repair rule stated at §6.5, Task 3, `## Scope Boundary` and §10
   P-9. Verified in place.
3. **The residue neither mitigation reaches** — this item's other documents and
   `tests/test_fixture_vault.py` — is closed by `## Scope Boundary`'s standing authoring rules
   (`:3729-3763`). This is prose rather than a wall on purpose, and the reason is stated rather than
   assumed: this document quotes REFUSED fixtures, corruption specimens and pre-existing tree literals
   by design, so an identity scan over it is RED by construction and would need a fourth declared
   exemption. All three rounds declined to ask for one and I decline again.

`## Mitigation Folds` is fresh against this round: M1 and M2 are re-emitted below BYTE-IDENTICALLY in
`desc`, same ids, same `landed:` ordinals, so the two fold records stand unchanged and nothing needs
re-quoting.

### Notes (non-blocking)

- **Carried forward, and the only one still open: the census's Method bullet claims a protection M1
  does not provide.** `docs/vault-shape-census.md:19` still reads that the absolute vault path "is
  deliberately not recorded here (AC-5(e)'s no-absolute-path rule, **extended to this artifact by
  M1**)"; §6.5 item 5 and Task 8 both say in terms that the scan does NOT extend leg (e) to the
  census. Re-verified at both ends this round. Nothing leaks today — the path is gone — but the
  artifact asserts a wall that does not exist, and a later refresh re-adding the path would pass M1
  green with its own Method bullet claiming otherwise. **Re-deferred rather than raised, for the
  ruling round 1 made and both later rounds kept:** the subject names no person and is machine-local.
  §10 P-10(c) now records it correctly, including that it must NOT be closed by widening M1's scan
  and that bundling it with the owed re-sign costs nothing extra. Three rounds is enough deferral for
  a one-line edit whose window is a conductor pass that is already owed.
- **The `ac-signoff` re-sign (§10 P-10(b)) is outstanding and is what the conveyor's `ac_hash`
  currency check refuses on.** Not a security matter and not mine — recorded only because my PROMOTE
  must not be read as saying the item is clear to advance. It is clear of security gaps; the door has
  its own lock.

```verdict
gate: threat-modeler
verdict: PROMOTE
date: 2026-09-08
model: claude-opus-5
note: Round 2's blocking finding is CLOSED and I verified it by re-running the measurement rather than reading the fold — the redaction marker now returns exactly five positions in exactly one file (docs/vault-fixtures.md:5785/:5788/:5791 and twice at :5881), each carrying the value's location and character profile and no value, and the finding's argument survives intact. The ordering held, which is the half that could not have been recovered: the drawer carries AC red-team and architect rounds and NO Threat Model section at all, so the append-only copy was not taken before the redaction. The durable half landed stronger than asked — Scope Boundary :3729-3763 states the GENERATOR (an identity-shaped value entering one of this item's artifacts through a surface no wall reaches) and closes the residue as a class in three standing rules binding conductor, gate and builder, outside the signed span; round 2's note 2 closes with it, and note 1 is re-deferred but now routed with its cost at §10 P-10(c). I stopped chasing the instance and swept the residue the new rules name, including the two artifact surfaces no threat-model round has examined: the docs/spec-reviews artifacts the ac-signoff fence names and the rounds drawer are both clean (their only real-looking name is the rfc2822_leak specimen, a verbatim re-typing of name_validation.py:205), every phone-shaped literal in this document is Ofcom drama-range or NANP 555, and the one email-shaped literal whose profile would make it a finding if novel is already committed at tests/test_name_validation.py:268/:274, tests/test_resolve_or_create.py:133/:176 and repositories/person.py:730 — measured, not ruled on by eye, and cited by location rather than re-typed. No third member of the class exists. STRIDE re-walked against material that is entirely prose this round: spoofing, repudiation, DoS and EoP unchanged with no finding (materialize_vault untouched since round 1's attacker read; neither fold makes the census a write target, and §10 P-9 states that wrong reading and rejects it); tampering improves durably (M1 standing after the fixity assertion, M2 fail-closed one phase earlier, the unwalled residue closed by authoring rule); information disclosure draws no finding for the first time in three rounds. Both declared residuals are unchanged and honest — a name deliberately typed into a reviewed set, and pool provenance grounded in the conductor's recorded scan because the suite is hermetic — and both belong to AC-5's sufficiency question, which is Dave's and on record. M1 and M2 verified in place at §6.5, Task 8 and Task 3 and re-emitted byte-identically. Two non-blocking notes, one of them the outstanding re-sign, which is the conveyor's lock rather than a security gap: PROMOTE means clear of security gaps, not clear to advance.
```

```mitigation
kind: required
id: M1
desc: Every identity-shaped token in docs/vault-shape-census.md's own bytes — its prose as well as its fence rows — is asserted to be in that artifact's certified pool table, CONNECTIVE_SET, or an admitted _GENERIC_ORG_SUFFIXES member, with any residue in a declared allowlist asserted DISJOINT from the pool table, so the artifact the privacy wall depends on is itself inside the wall.
landed: Task 8
```

```mitigation
kind: required
id: M2
desc: The Implementation Plan's precondition abort gate additionally REFUSES when docs/vault-shape-census.md carries an identity-position token its own pool table does not certify, so a leaking census stops the build before any corpus byte is authored rather than at the last task.
landed: Task 3
```

## Spec Review — 2026-09-08 (round 6)

**Recommendation: PROMOTE to ready**

Rulings on record: the AC-5 structural-wall-vs-middle-path sufficiency question is Dave's and is recorded above for sign-off; the census's absence from HEAD is SEQUENCING rather than a grounding gap (data audit, 2026-09-07); WI-020's specification-altitude and fold-and-close closures; and the 2026-09-08 threat model round 1's ruling that leg (e)'s no-absolute-path rule is NOT extended to the census, kept by rounds 2 and 3 — I route against all of them and nothing below re-litigates any.

Read from line 1 in full, plus `docs/vault-shape-census.md` end to end, plus `docs/spec-reviews/WI-016-dave-review-2026-09-08-2.md`, then walked the bar from scratch rather than against round 5's gap list.

### Round 5's three blocking findings, each re-measured rather than read off the fold

- *Finding 1 (the leak in this document's own gate prose, and the missing durable rule).* **CLOSED.** The five positions round 5 measured now carry a bracketed redaction naming each value's census row and character profile and no value; threat model round 3 re-ran that measurement independently and reports the same. The durable half landed as a CLASS rather than as the two instances: `## Scope Boundary` (`:3729-3763`) states the generator and three standing authoring rules binding conductor, gate and builder, outside the signed span. I checked the ordering claim myself rather than trusting it — `docs/vault-fixtures-rounds.md` carries AC red-team and architect rounds and no threat-model section, so the append-only copy was not taken ahead of the redaction and nothing needing correction is frozen there.
- *Finding 2 (the `pure_digit` `Verdict` literal).* **CLOSED, and I drove the literal through the code rather than reading the fix.** `name_validation.py:283-288` carries `branch_id="pure_digit"` (`:284`) and `pattern="pure_digit_name"` (`:285`); `:678` raises `NameValidationError(branch.pattern, …)`, `:463` binds it, `name_gate.py:365` re-raises through the single `_refuse` site at `:142`. §5.3 (`:2162-2175`) and Task 6 (`:3255-3265`) now pin `pattern="pure_digit_name"`, §3 states the general rule (a declared refusal `Verdict`'s `pattern` is the record's `pattern` field, never its `branch_id`) and carries a seven-item sweep of every pin of that class. AC-3's signed text did not move and did not need to.
- *Finding 3 (the untaken re-sign).* **CLOSED — and it is the one whose closure inverted a claim this document still makes; see minor note 1.** `## AC Sign-off` now carries `signed_at: 2026-09-08T07:44:54+01:00`, `ac_hash: 3d15772495dc`, `ac_hash_AC-3: 1ec178617d40` and `artifact: docs/spec-reviews/WI-016-dave-review-2026-09-08-2.md`. I verified the signature is over the section AS IT NOW STANDS rather than assuming it: that artifact's `frozen_acceptance_criteria` carries AC-3(iv)'s re-taken digest (`-2.md:396`), the corrected "FROZEN — Dave signed" preamble (`:24-51`), AC-1(a)'s "corpus-relative POSIX path", AC-4's `__all__` / `:14-21` cite, AC-5(b)'s "THREE literal frozensets" and `### Examples of done` (`:1319`) — the whole span, including both edits round 5 priced at one re-sign, and no AC has been edited since. Stated as a limit rather than implied: I have no shell and cannot recompute the hash, so the currency check itself remains the conveyor's to run.

### Citation verification

Every `file:line` this round leans on was read at its cited lines in this worktree. **All verified ✓**, none inherited from the injected drift audit, which proves only that a symbol still exists.

Re-read and confirmed exact: `repositories/base.py:27-38` (`SkippedNote`, the `#` type comment at `:37`, `detail` as `bounded_detail(error)` at `:38`) and `:41-47` (the three bare return literals at `:44`/`:46`/`:47`). `name_validation.py` — every `branch_id=` one by one, ten in `TIER1_BRANCHES` (`:192`, `:203`, `:215`, `:227`, `:239`, `:250`, `:261`, `:272`, `:284`, `:301`) and five in `COMPANY_TIER1_BRANCHES` (`:373`, `:385`, `:398`, `:414`, `:429`) adding no new id, so AC-3(iii)'s derived floor is ten and the census's ten branch rows are exactly it; `:284-285` for finding 2. `writer.py:160-169` (the signature takes `file_path` first, then `entity=`, then `frontmatter=`), `:205`, `:229-247` (the three arms and `gate_whole_record`), `:252-253` (the ONE `gate_write` call, `declared_type=fm.get("type")` read POST-merge) — Task 4's `frontmatter=` arm and §5.3's `entity=` arm are both real signatures and both reach the gate. `tests/ac_interpreter.py:1-40`, `:118-120` (the delegated argv is a one-node `pytest` run under the project venv), `:123-130`, `:136-148`, `:150-155`. `tests/test_ac_interpreter.py:36-40` (`WORK_ITEM_DOC` is `docs/write-door-bypasses.md`), `:57-73` (`criterion_checks`, fence-scoped by an exact `==` on the fence opener), `:76-87` (`check_module`, a `def <name>(` substring scan raising on anything but one match), `:90-95` (`run_foreign`, `sys.executable -S` in the conveyor's argv shape), `:111-115`, `:116-120` (the delegation-marker clause and its message), `:126-138` (the near-miss, named `test_a_failing_delegated_check_is_red_not_silently_green` — distinct from the name Task 12 adds). `tests/test_vault_path_required.py:382` (`NO_ARG_CONSTRUCTION`), `:387` (the five excluded parts), `:390-418` (`_temp_root_inside_repo`, which cannot reach `tests/fixtures/vault/`), `:421-433` (`_scanned_markdown_files`, an `rglob` from `REPO_ROOT` — so the corpus IS reached and Task 12's non-vacuity clause is satisfiable), `:436`, `:451` (`errors="replace"`, which is what makes the non-UTF-8 member safe in that walk). `tests/test_name_gate_wall.py:1057` and `:1073` (WI-022's colliding name and its call site), `:1132` and `:1136-1145` (`_check_the_ast_capability_stays_single_homed`, whose live line IS `{use.module for use in live}` — Task 12's corrected projection is the shipped wall's own), `:1161`. `tests/derivations.py:630` (`modules_using_ast` returns USE records, so the projection is required). `tests/test_loud_fail_harness.py:18-20` (the `six` dict declared a REQUIRED SUBSET rather than a cardinality bound), `:79-88`, `:93-97`, `:103-105`. `tests/test_loud_fail_load.py:167` (`test_skip_surface_detail_is_bounded`, Task 11's `verify:` name), `:187-188`, `:209-210`. `tests/test_name_gate.py:152`. `tests/support.py:1-19` and `:30-37` (`temp_dir` is a context manager). `pipeline-runners.yaml:7-8`, `:18-19`, `:34-38`. `pyproject.toml:38-39`, `:41-43` (`testpaths` and `python_files` are both declared, so Task 12's W-14 arm has the two keys its raising helper requires).

`docs/vault-shape-census.md` re-read and structurally re-counted rather than inherited: **sixteen** `census-class` fences, **six MEASURED** (`pure_digit` 2, `diacritics` 6, `hyphenated_surname` 29, `whitespace_damage` 7, `stem_name_divergence` 8, `postal_address_in_name` 1) and **ten ABSENT** with count 0 and a `ruling`, one `census-meta` (`snapshot: 2026-09-07`, person 1150, company 659), **forty-two** `census-pool` rows. The six MEASURED ids are exactly §1.3 rule 2's and Task 6's list; the ten ABSENT ids are exactly the ten `branch_id`s I enumerated above, so AC-3(iii)'s both-directions branch assertion resolves with no phantom and no gap, and `arrow_connective` / `path_hostile` / `same_name_collision` are ABSENT exactly as §1.3 rules 5 and 7 assume.

**The fence-scoped digest read is load-bearing and is already earning it, which I checked rather than assumed.** The `CENSUS_DIGEST` declaration form occurs TWICE in this document — once inside the AC-3 `criteria` fence (`:1418`) and once in round 5's finding 3, which quotes the superseded value (`:6173`). A file-wide uniqueness read would be RED today; fence-scoped it is unique and well-formed 64-character lowercase hex. Relatedly, `criterion_checks` over this document returns exactly five `check:` keys, all inside `## Acceptance Criteria`: the only other line opening with the fence marker followed by `criteria` is Task 12's own prose at `:3483`, which that reader's exact `==` test correctly declines to open a fence on. Task 12's "exactly five" pin therefore holds with six spec reviews, a sign-off and three threat-model rounds inline.

### Bar check

Walked every check of `docs/spec-quality-bar.md` (the doc's own list is the count). **Check 1** — self-contained against the codebase alone; the one exception is minor note 1, which is narration about the pipeline rather than instruction to the builder. **Check 2** — §10's P-1…P-10 enumerate the prerequisites, the trust boundary, the stdlib surface split across both new modules, the ≥3.10 floor's one load-bearing consequence, and the WI-300 ordering; P-3's atomic-landing claim against the PRE-DRIVE floor is right, re-verified at `tests/test_vault_path_required.py:387` and at the only two modules that name a doc. **Check 3** — every load-bearing claim about package behaviour re-read at its code; the one this round drove end to end is finding 2's, now correct. **Check 4** — all ten categories resolved, `OPEN: None`, and every resolved rule carries an exercising assertion (idempotency and no-clean by AC-1(b)'s second `materialize_vault` call with a foreign file planted between, the ISBN and hex collisions by Task 9's near-miss battery, the two-field split by mutation 15, the `-Voxleaf` run rule by Task 9's shape battery). **Check 5** — twelve canonical `- [ ] **Task N — …**` definitions, ordinals unique and contiguous 1–12, twelve well-formed lowercase `verify:` declarations (ten `test_` arms, one `baseline`, one `hand-run`, each exception carrying its reason); no `verify:` is a command and none writes, so WI-238 draws nothing. Both `landed: Task N` ordinals resolve (D8b clean). **Check 6** — WI-235's shape controls are Task 2's two planted batteries with their near-misses and Task 9's four, all driving the LIVE predicate objects by name; WI-278's arm is declared per reader with the `CORPUS_COUPLING:` line and M1's third property sits on the same arm behind the same digest; WI-173 correctly does not fire on an item whose warrant is absence. **Check 7**. **Check 9** — ten rows; R1 carries the threat model's finding and R10 the four members of its class. **Check 10** — five well-formed `criteria` fences, all `kind: test`, no `kind: command` and so no unsandboxed-shell exposure. **Check 11** — D-1…D-9 re-read at their artifacts, each supporting its own specific claim, with the closing paragraph correctly separating the seven package facts from the two pipeline ones (one count inside D-9 is off by one — minor note 3). **Check 8** — `## Mitigation Folds` holds one `fold` fence per id; I compared each `desc` character by character against the LATEST SPEAKING round's `mitigation` fences, which is now threat model **round 3** rather than round 2, and both are byte-identical, so the records are fresh against the round that actually speaks and D8c is satisfied. Both `design:` quotes are where they claim to be (§6.5's M1 and M2 sentences) and both `work:` quotes reproduce their task's own text (Task 8's body including the `CENSUS_PROSE_ALLOWLIST` authoring clause, Task 3's opening). Satisfaction is mine and not mechanical: M1's Task-8 scan runs the SAME `identity_tokens` object leg (b) calls, over the whole decoded file, ordered after the fixity assertion, with the pool-row set asserted non-empty first and the allowlist asserted disjoint from it; M2 is that predicate one build phase earlier, fail-closed, with the no-repair rule stated at four sites. Both satisfied. **Check 12 fires and is clean**: the evolved `## Acceptance Criteria` and the frozen text at `-2.md` agree across all five criteria — no strength-weakening, actor-swap, scope-narrowing, oracle-swap or exception-carving-by-addition — and unlike round 5 the signed hashes are no longer stale.

**Write-Targets coverage (WI-132), run task by task rather than inherited.** Task 1 → none (baseline); Task 2 → `obsidian_schemas/repositories/base.py`, `tests/derivations.py`, `tests/test_fixture_vault.py`; Task 3 → `tests/fixtures/vault`; Tasks 4–9 → `tests/fixture_vault.py`, `tests/test_fixture_vault.py`; Task 10 → `tests/test_parser.py`, `tests/test_writer.py`, `tests/test_repositories.py`; Task 11 → `tests/test_loud_fail_load.py`, `tests/test_name_gate.py`; Task 12 → `tests/test_fixture_vault.py`. Every one is declared by a `writes` fence and no fence declares a path no task writes. The five READ-but-unwritten modules (`tests/ac_interpreter.py`, `tests/test_ac_interpreter.py`, `tests/test_vault_path_required.py`, `tests/test_name_gate_wall.py`, `pyproject.toml`) plus `docs/vault-shape-census.md` are correctly absent from `## Write Targets` and named on `## Scope Boundary`'s unchanged list with the reason. Every declared path is inside `write_authority` (`pipeline-runners.yaml:34-38`), so D7b holds and the WI-290 selector reads the item's real touch surface with nothing over-declared.

**The conscious-pin sweep found no moved pin**, re-run rather than inherited over the corpora this change alters — the `branch_id` union, `TYPE_TO_MODEL`, the exported repository set, the skip-reason vocabulary, and `tests/derivations.py`'s scan set. `tests/test_concurrent_access.py:1077`/`:1085`/`:1088`/`:1089`, `tests/test_name_gate_wall.py:1161`, `tests/test_name_gate.py:172` and `tests/test_loud_fail_harness.py:88` are each unmoved by a frozenset, three string constants, two new scans and three repointed literals; the last of those I checked at its own docstring (`:18-20`) rather than at the spec's claim about it, and it is a declared REQUIRED SUBSET, so two new derivations genuinely do not move `len(six) == 6`.

### Build-runner dry-run

Walked the Implementation Plan top-to-bottom as the builder. Every task names its files, its insertion points and a runnable check; §1.2's grammar, §1.3's seven rules, §3's `LOADABLE` arithmetic with the collision's contribution worked, §3's two-field split, §4's disposition table, §5.1/§5.2's two identical walks, §5.4's ownership table (re-traced against `base.py:258-275`), §6.1's extractor with its fifth stated consequence, §6.4's three named predicates and the named excision, and §6.5's six decisions leave no judgment call open. The precondition gate with its M2 arm is still the strongest thing in the plan and now fires one phase before the expensive work. Task 3's `hand-run` declaration is the one task whose artifact has no standing check until the next task lands, and it says so with its reason.

Three questions a cold-start builder would plausibly ask, and where each is answered: *"which manifest field names the two AC-1(c) discriminators?"* — `NoteSpec.discriminator`, never `shape_classes`, argued in §3, prescribed in Task 4, restated in §5.5 and driven both wrong ways by mutation 15. *"do I project `modules_using_ast`'s return?"* — yes, and Task 12 now prescribes the projection the shipped wall itself performs. *"what do I call for W-14, which has no importable predicate?"* — nothing; the config's own declared `python_files` globs, read by a helper that raises rather than defaults, driven through `fnmatch`, with `tests/test_fixture_vault.py`'s own name as the positive control. All three are answered in the document, which is the difference between this round and rounds 3 through 5.

### Minor notes (non-blocking)

1. **Every place this document narrates its own GATE STATE is now stale, because the acts round 5 asked for were taken.** `## AC Sign-off` carries the re-sign; §10 P-2 still reads "As of 2026-09-08 that re-sign is still UNTAKEN" and quotes `ac_hash: 2696ecd667a7` / `ac_hash_AC-3: eab359ff9e39`, neither of which is in the document any more; §10 P-10(b) reads "OUTSTANDING"; §10 P-9 names rounds 1 and 2 and calls round 2 the latest speaking round; `## Mitigation Folds`' preamble and `## Self-Review Dry Run`'s bar check say the same. All five are false and all five sit outside the signed span, so the whole correction is free. **It is a note and not a finding, and the reason is the shape rather than the size:** I verified the two things that could have BLOCKED — that the signature is over the current section, and that the fold records are byte-fresh against round 3 rather than round 2 — and both hold, so nothing machine-read acts on the stale prose. **The one place it does cost something is P-10(c)**, which routes the census Method-bullet fix to "ride (b)" and prices it at "nothing extra, bundled": (b) is taken, so that bundling is gone and the edit now costs its own re-sign. Worth one sentence whenever P-2 and P-10 are next touched. **And it is worth naming what GENERATES it, so the factory does not buy a round on the next turn of the crank:** this document records its own pipeline state in prose, and every gate round and conductor act invalidates that prose — round 5's finding 3 was this class, its remediation created this instance, and a seventh round would find whatever this round's remediation creates. That is the WI-020 regress signature, sitting in the narration rather than in the spec. The durable answer is not another correction pass but to let the fences be the record: `## AC Sign-off`'s own keys ARE the sign-off state and `## Threat Model`'s latest round IS the speaking round, both machine-read, so §10's prose should point at them rather than restate them.
2. **The `## Acceptance Criteria` preamble points at the SUPERSEDED frozen artifact**, naming `signed_at: 2026-09-08T01:14:48+01:00` and `docs/spec-reviews/WI-016-dave-review-2026-09-08.md` where `## AC Sign-off` names 07:44:54 and `-2.md`. It is inside the hash-signed span and was signed as it stands, so **it should NOT be edited** — a third re-sign bought for a pointer is not worth it. Recorded so a later Check-12 gate does not follow the preamble to the older artifact, diff AC-3(iv)'s digest against it and re-raise round 5's finding 3 forever: the authoritative referent is the `artifact:` key of the `## AC Sign-off` fence.
3. **§4's disposition table and D-9 both claim a complete grep and are short by one site.** Re-run here over every `*.py` in this worktree, the three literals occur at `errors.py:112`, `base.py:37`, `:44`, `:46`, `:47`, **`base.py:299`**, `test_loud_fail_load.py:188`, `:209` and `test_name_gate.py:152` — nine, not the eight D-9 states, with `base.py:299`'s `# unreadable note.` comment absent from the table. **Consequence is nil and that is why it is a note:** it is a `#` comment, invisible to `ast` and therefore to W-15, in a file that is a declared legal home either way, and §4 already rules that exact shape KEPT at `:37`. It is recorded because §4's own heading argues that the enumeration rather than a count is what set Task 11's scope, and because this is the same stated-number-versus-actual-list family the document has corrected five times — the sixth instance is in the paragraph that closed the fifth.
4. `base.py:196-198` survives at one site (AC-4's `desc`) where the rest of the document now says `:195-198`. AC-4 is signed, both spans resolve to the same `file_pattern` property and support the same claim, and the divergence is already recorded in `### Constraints discovered` as checked rather than missed. No action.

### Carried-forward notes

- **Threat model round 2 note 1 / round 3's only open note — `docs/vault-shape-census.md:19` claims a protection M1 does not provide.** Re-verified at both ends this round: the Method bullet still reads that the absolute vault path "is deliberately not recorded here (AC-5(e)'s no-absolute-path rule, extended to this artifact by M1)", while §6.5 item 5 and Task 8 both say in terms that the scan does NOT extend leg (e) to the census. Nothing leaks today; the artifact asserts a wall that does not exist, and a later refresh re-adding the path would pass M1 green with its own bullet claiming otherwise. **Still OPEN and re-deferred, for the ruling three threat-model rounds have kept** — the subject names no person and is machine-local — and routed correctly at §10 P-10(c) with its fix and its "must not be closed by widening M1's scan" rule. The only thing that has changed is its price, per minor note 1: it no longer rides an owed re-sign.
- **Architect round 10 note 2 — AC-4's "`_skip_reason` returns them BY NAME" is prose the first arm of `skip_reason_return_values` cannot discriminate**, since that scan resolves a module-level `str` Name and a bare literal to the same value. Still OPEN. Re-deferred, and I checked the argument rather than accepting it: §4 and Task 2 prescribe the by-name form explicitly, no safety property depends on the spelling, and W-15's set equality is unaffected either way because `base.py` is a declared home under both spellings. Closing it buys a re-sign for a clause with no red behind it.
- **Architect round 10 note 3 — the rounds drawer.** Still PARTIALLY actioned and now UNBLOCKED: the drawer holds no threat-model section, so the redaction preceded any copy and the append-only rule has frozen nothing that needed correcting. §10 P-10(d) records it. I re-confirmed the two reads a copy could have disturbed: AC-3(iv)'s digest read is fence-scoped, and `criterion_checks` still returns exactly five names, all inside `## Acceptance Criteria`.
- Rounds 1–4's non-blocking notes, the data audit's P10 count, and AC red-team round 9's "Nine helpers" — all closed at earlier rounds and re-confirmed here. Round 5's four notes are closed: the W-1 projection is in Task 12 and §11, the `CENSUS_PROSE_ALLOWLIST` authoring clause is in §6.5 item 3 and Task 8 with the two landed-artifact tokens named, the `:195-198` alignment is taken everywhere it was free, and AC-5(b)'s company figure is correctly left alone as signed text nothing rests on.

Nothing this round touches the approach, D1's amendment, the byte-copy rule, the derived sweeps, the census's sequencing, or AC-5's pending sufficiency question — which remains Dave's and is recorded above for sign-off. Twenty-five gate rounds have now produced no finding against the approach.

```verdict
gate: spec-reviewer
verdict: PROMOTE
date: 2026-09-08
model: claude-opus-5
note: All three of round 5's blocking findings CLOSE and each was re-measured rather than read off the fold — the five redacted positions carry location and character profile and no value, with the rounds drawer confirmed to hold no threat-model section so the redact-first ordering held; the pure_digit Verdict now reads pattern="pure_digit_name", which I traced name_validation.py:284-285 -> :678 -> :463 -> name_gate.py:365/:142 rather than reading the fix; and the re-sign is TAKEN (signed_at 07:44:54, ac_hash 3d15772495dc, artifact -2.md) over the section as it now stands, verified by finding AC-3(iv)'s re-taken digest at -2.md:396, the corrected preamble at :24-51 and Examples of done at :1319 inside the frozen text. Check 8 draws no finding: the latest speaking round is now threat model ROUND 3, which re-emitted M1 and M2 byte-identically, so both fold records are fresh against the round that actually speaks, both design/work quotes are where they claim to be, and I judge both mitigations satisfied on my own read of the quoted text. Census re-counted end to end — 16 class fences, 6 MEASURED / 10 ABSENT, 42 pool rows — and the ten ABSENT branch ids are exactly the ten branch_ids I enumerated one by one across both Tier-1 tables, so AC-3(iii) resolves with no phantom and no gap. Twelve canonical tasks with contiguous ordinals and twelve well-formed verify declarations, both landed ordinals resolving, Write-Targets coverage run task by task with nothing over- or under-declared, no moved count pin, and the fence-scoped digest read already earning its scope (the declaration form occurs twice in this document and a file-wide read would be RED today). Four minor notes, none blocking, and the largest is named as a CLASS rather than a fix list: every place this document narrates its own gate state in prose — P-2, P-9, P-10(b), the Mitigation Folds preamble, the Self-Review bar check — is now false precisely because the acts round 5 asked for were taken; its one real cost is that P-10(c)'s census fix no longer rides an owed re-sign; and it is the WI-020 regress signature in the narration rather than in the spec, since round 5's finding created this instance and a seventh round would find whatever fixing it creates. The durable answer is to let the AC Sign-off and Threat Model fences be the record instead of restating them. I verified the two things that could have blocked — signature currency and fold freshness — and both hold. Nothing here touches the approach, the byte-copy rule, the derived sweeps, the census sequencing or AC-5's sufficiency question, which is Dave's and on record.
```

---

## Build Log

**Built 2026-09-10, cold-start, driven.** Twelve tasks, all landed. Floor GREEN at 678 cases
(baseline 667), 9.91s. Below: the numbers Task 1 and Task 12 owe, the precondition gate's result,
every place the build learned something the spec did not say, and the mutate-and-observe battery
with what each mutation actually did.

### Task 1 — the baseline (the `verify: baseline` this task declares)

- Floor before any edit: **667 passed in 10.21s** — `.venv/bin/python -m pytest <worktree>/tests -q`.
- Worktree HEAD: `f0166ecd8ba6d8719f117decbb63bcd4ba76c89f`.
- Floor after Task 12: **678 passed in 9.91s**. Directionally higher, as the invariant requires; the
  wall-clock did not move materially, which is P-4b's instrument reporting that Task 12's six foreign
  runs cost about what `tests/test_ac_interpreter.py`'s already-measured ones do (the three new
  subprocess-making tests account for ~2.4s of the module's own 2.6s, absorbed inside a floor that
  got no slower overall).

### The precondition gate, including its M2 arm — PASSED, and what it measured

Run before a byte of Task 2 and re-run before a byte of Task 3, against
`docs/vault-shape-census.md` as it stands in HEAD.

- **Structure.** One `census-meta` fence carrying `snapshot: 2026-09-07`. **16** `census-class`
  fences, ids unique; **6 MEASURED** (`diacritics`, `hyphenated_surname`, `whitespace_damage`,
  `stem_name_divergence`, `postal_address_in_name`, `pure_digit`) and **10 ABSENT**. Every row's
  `status`/`count` agreement, counting `command`, non-empty `stdout`, and
  specimen-iff-MEASURED / ruling-iff-ABSENT checked one row at a time. **42** `census-pool` fences,
  every one carrying `token`/`class`/`command`/`stdout: 0` and nothing else.
- **The branch floor.** `{record.branch_id for record in TIER1_BRANCHES + COMPANY_TIER1_BRANCHES}`
  is the ten ids §11 names, and the class table carries a row for every one — no missing branch, no
  phantom.
- **The digest.** `sha256` over the census's bytes is
  `4cb7945f643415b7fba9347f2f0ecee30a3b054bb9aa1ba875e2551b93b599cb`, which EQUALS the value
  AC-3(iv) declares, read fence-scoped from the single AC-3 `criteria` fence. No placeholder stood.
- **M2, the arm that decides whether ~50 notes get written.** `identity_tokens` over the WHOLE file
  yielded **161** tokens; **45** were certified pool rows, `CONNECTIVE_SET` members or admitted org
  suffixes, and the **116**-token residue was read one token at a time and is entirely the census's
  own technical vocabulary — section headings and emphasis caps (`MEASURED`, `ABSENT`, `ONE-or-TWO`,
  …), symbol and tool names the Method section cites (`PersonRepository`, `DaveRemoteVault`,
  `Obsidian`, `Templates`, `Python`), and the street-kind words and character-class fragments quoted
  inside the scan commands themselves (`Street`, `Avenue`, `A-Za-z`, …). **No uncertified
  identity-shaped token, and no granularity divergence:** the two hyphen-fused compounds the
  extractor produces, `Brenvik-Tarnquil` and `Pellworth-Wexlund`, each carry their own pool row
  beside their halves, so the R10 shape §6.2 warns about does not arise. The gate did not fire and
  nothing in the census was touched — this build read that file and never wrote it.

### Task 3 — the corpus, and its tallies

**53 notes**, one flat directory, ≥ 50 as AC-1 requires.

| | |
|---|---|
| person | 22 loadable files (20 cache keys — the three-filename collision collapses under `_get_cache_key`) |
| company | 6 |
| meeting | 5 loadable + 1 malformed |
| book | 4 |
| watch / explore / gift-idea / exploration | 3 each — parser-level only, outside AC-4 |
| skip specimens | `@Halvorne Sennaby.md` (malformed), `Meeting 20260212 - Zebrant Dalquest.md` (malformed, the second owning glob), `@Ferrigan Ostrakine.md` (schema-drift), `@Isolde Varnholt.md` (non-UTF-8) |

Per census class: one specimen each for the six MEASURED ids and none for the ten ABSENT ones.
Exactly one member raises `UnicodeDecodeError` under `read_text(encoding="utf-8")` — confirmed by
running that read over all 53 and counting the raises. The two AC-1(c) discriminators carry
`shape_classes = ()` and their `branch_id` in `NoteSpec.discriminator`, per §1.3 rule 7. The
`pure_digit` specimen declares no `phones`, so `allow_phone_sentinel` cannot pass it.

### What the build learned that the spec did not say

1. **`skip_reason_return_values` needed a nesting guard, and Task 2's own planted battery is what
   found it — before the live assertion ever ran.** `_iter_functions` yields a nested
   `def _skip_reason` under the qualname `outer.<locals>._skip_reason`, and `FunctionId.name` is the
   last dotted segment, so the first cut attributed a nested function's returns to the module-level
   one. The spec names that exact near-miss ("a `return` of a string inside a NESTED function of the
   same name") and the plant went RED on it; the fix is one clause,
   `"<locals>" not in fid.qualname`, with the reason written into the docstring. Recorded because it
   is WI-235 working in the direction that matters: the battery caught the predicate, not the
   predicate the battery.
2. **`NoteSpec.raw_bytes_hex` must be ONE unbroken source literal.** Written as three
   implicitly-concatenated fragments for line length, the value exists at run time but never appears
   contiguously in the file — so AC-5(a)'s "occurs somewhere in the reach" assertion is RED and its
   excision is a no-op that leaves `747970653` behind. It is now a single line with a `# noqa: E501`
   and a comment saying why. The criterion is right and the shape it implies is not obvious; a later
   corpus edit that re-wraps that literal will go RED at the presence assertion, which is the
   assertion doing its job.
3. **`tests/fixture_vault.py` carries no URL, so the URL-bearing fields moved OFF the round-trip
   representatives.** §3 forbids a URL in the manifest and AC-2 wants each representative's whole
   field set declared; the two collide on `Person.linkedin`, `Company.website`, `Book.source_url`
   and `Explore.url`. Resolved in the CORPUS rather than in either rule: the four representatives
   carry those fields empty and four non-representative notes carry the URLs, so leg (a) still scans
   real reserved-host URLs in the corpus bytes and the manifest still has none. No criterion moved.
4. **`Person.whatsapp` is email-shaped as well as phone-shaped.** A real JID
   (`<digits>@s.whatsapp.net`) is scored by `reserved_email_violations` against a domain no RFC
   reserves, so the corpus's JID is spelled `447700900789@example.com` — reserved on both
   predicates, and `normalize_phone` still splits it at the `@` to the reserved digits, which is
   what leg (d) asserts.
5. **`Book.isbn` must be QUOTED in the corpus.** Unquoted, YAML parses `9780000000001` as an int and
   `Book.isbn: str` refuses it. Not a spec gap — a byte-level consequence of the ISBN decision.

Nothing else deviated. The approach, the byte-copy rule, the derived sweeps and the census's
sequencing are as specced; no criterion was narrowed and no assertion was relaxed to fit what was
found. **`docs/vault-shape-census.md` was READ and never written** (`## Scope Boundary`), and no
out-of-authority path was needed.

**Doc-sync check (2b/2d): CLAUDE.md needs no edit and that is a finding rather than an omission.**
Walked its assertions one at a time. Its test-count sentence explicitly refuses to carry a number
("never trust a number written here — run the floor command"), so 667 → 678 falsifies nothing. Its
loud-fail section sends the reader to `obsidian_schemas.__all__` at run time, and `SKIP_REASONS`
lives in `repositories.base` and does not join `__all__`. Its "Key Files" table is a pointer list
rather than a manifest, and the two new files are additions to the tree rather than corrections to
it. `P2`'s load-bearing "no `conftest.py` anywhere" is still true — Task 12 asserts it. No claim this
build falsified is written there, so nothing is edited, and CLAUDE.md is outside this build's write
authority in any case.

### Mutate-and-observe — every mutation run, observed and REVERTED

`## Verification`'s fifteen, run one at a time against a green tree, each reverted and the module
re-run green before the next.

| # | Mutation | Observed |
|---|---|---|
| 1 | one byte appended to `@Isolde Quenlaw.md` | AC-1 RED, digest mismatch named |
| 2 | `@Søréna Kelmarrä.md` deleted | AC-1 RED **and** AC-3 RED (its `diacritics` specimen went with it) |
| 3 | `write_bytes` → `write_text` in `materialize_vault` | AC-1 RED — `UnicodeDecodeError` on the non-UTF-8 member, which is leg (b)'s point |
| 4 | plant the discriminators through `repo.save()` | `NameGateRefusal` on both — `arrow_connective` carrying `pattern='calendar_prefix'`, `path_hostile` carrying `'path_hostile_char'`. Also a STANDING assertion inside AC-1(c) rather than only a mutation |
| 5 | fourth `_skip_reason` arm with no `SKIP_REASONS` member | AC-4 RED at the scan equality **and** at the union. Member added without a specimen → AC-4 RED at the union alone. Both halves fire |
| 6 | one byte appended to the census | AC-3(iv) **and** AC-5(c) both RED — both, not one, which is why the leg is asserted twice |
| 7 | `postal_address_in_name` flipped to `ABSENT`/`count: 0`, specimen dropped for a `ruling` | AC-3 RED at the fixity assertion, before a single row was read — the exact forgery round 8 found unguarded |
| 8 | `Thornbury` planted in a `company:` **with the corpus digest re-taken** | AC-5 RED naming the token. Adding `Thornbury` to `PROSE_ALLOWLIST` → **still RED** at the disjointness assertion, which is the whole of the position split |
| 9 | `ensure_project_interpreter(__file__)` deleted | **The finding is the green half.** 676 of 678 cases stayed GREEN — every pre-existing test, and this item's own eight non-parity checks — while `test_this_items_checks_pass_under_the_conveyors_interpreter` went RED with the child's `ModuleNotFoundError: No module named 'pydantic'` on five of five checks. The floor cannot see this defect; only W-16's own run can, and only because it asserts the `[ac_interpreter]` DELEGATION MARKER as well as exit 0 |
| 10 | `_WI016_MUTATION = "unreadable"` in `obsidian_schemas/parser.py` | W-15 RED naming that file. The same three words in a `#` comment and in running docstring prose instead → **GREEN**, which is the discrimination §4 requires and the reason the wall reads syntax |
| 11 | `shutil.rmtree(dest)` at the top of `materialize_vault` | AC-1(b) RED on the surviving foreign file — the no-clean rule, which had no test before this round |
| 12 | hex excision removed | AC-5(a) RED on `raw_bytes_hex` over a wholly correct corpus. Excision widened from named literals to a hex-SHAPED rule → Task 9's near-miss RED, which is what stops the exemption becoming a padding surface |
| 13 | an uncertified surname planted in the census's PROSE, under no fence | AC-3(iv)/AC-5(c) RED first at the digest; with the digest updated, M1 RED naming **both** tokens by name. The token added to `CENSUS_PROSE_ALLOWLIST` instead is then a name a human reviews, which is the bar and the residue §9.5 states |
| 14 | the census scan pointed at a file with no `census-pool` fences | RED at the non-empty pool-row assertion rather than green — an empty admitted set admits nothing and a scan over a file with no tokens admits everything |
| 15 | the two discriminators' branch ids moved into `shape_classes` | AC-3(i) RED (two ABSENT ids on the MEASURED side) **and** AC-1(c) RED. Empty `discriminator` on both instead → AC-1(c) RED at the `⊇` assertion. The corpus is buildable exactly one way, which is the point of the split |

### Task 12 — the walls, RUN rather than reasoned about

Every §11 row whose universe grows was closed by calling that wall's own shipped predicate on the
final bytes: `modules_using_ast` projected as `{use.module for use in live}` (W-1 and W-2 in one
call), `skip_reason_literal_sites` (W-15, the row this item mints),
`_scanned_markdown_files` + `NO_ARG_CONSTRUCTION` imported by name from
`tests/test_vault_path_required.py` with the non-vacuity clause asserting the generator reaches all
53 corpus notes first (W-8), `check_module` over every top-level `def test_` this item's six write
targets define (W-10), and `criterion_checks` / `check_module` / `run_foreign` driven over this
document's own five `check:` names with BOTH halves of the shipped oracle (W-16). W-14 is the one
row with no callable predicate and is declared as such: the config's own `python_files` globs are
read from `pyproject.toml` by a helper that RAISES rather than defaulting, driven through `fnmatch`,
with this module's own name as the positive control.

**The run returned nothing §11 did not name.** Every row behaved as the table predicted, and the
four modules the sweep returned but the table does not otherwise name
(`test_loud_fail_write.py`, `test_loud_fail_parse.py`, `test_address_splitter.py`,
`test_concurrent_access.py`) are green — including `test_concurrent_access.py:1077-1089`'s four
hardcoded count pins over package-derived populations, none of which moved, because this item adds
no function that reserializes parsed frontmatter, no falsy return in a write path, no
`BaseRepository` subclass and no `_load_file` implementation.

### One thing a later reader should be told rather than surprised by

`PROSE_ALLOWLIST` and `CENSUS_PROSE_ALLOWLIST` are each the RESIDUE of their own scan over the file
they cover, authored against the artifact as it stands — which is what §6.5 item 3 instructs for the
second and what AC-5(b) describes for the first. The consequence is that **editing
`tests/fixture_vault.py`'s prose can redden AC-5**, and the remedy is to add the new ordinary word
to `PROSE_ALLOWLIST`, which the disjointness assertion keeps honest: a token that is also an
identity token cannot be admitted that way. That is the friction working, not a defect — but it is
friction nobody meets until they touch the manifest's docstring, so it is written down here.

---

## Code Review — 2026-09-10

Cold-start, hand-run (no return channel named). The reviewing spawn has NO shell, so nothing below
is a re-run of the floor; every claim is from reading the final bytes of the diff surface against the
signed criteria, `## Design`, `## Write Targets`, `## Scope Boundary` and §11.

### Trigger check — FIRES

Not doc-only. The diff carries one package change (`obsidian_schemas/repositories/base.py`), two new
modules (`tests/fixture_vault.py`, `tests/test_fixture_vault.py`), 53 new fixture files under
`tests/fixtures/vault/`, two new scans in `tests/derivations.py` and five edited test modules. No
dependency and no build/CI configuration change.

### Write-authority and scope

Every written path is a declared `## Write Targets` path. `docs/vault-shape-census.md` is READ and
not written — confirmed by reading it nowhere on a write arm: `tests/test_fixture_vault.py` opens it
with `read_text` / `read_bytes` at `:122`, `:140`, `:148`, `:196` and `:389` and never writes. The
`## Scope Boundary` unchanged list holds: `models.py`, `name_gate.py`, `parser.py`, `writer.py`,
`errors.py`, `pyproject.toml`, `CLAUDE.md`, `tests/ac_interpreter.py`, `tests/test_ac_interpreter.py`,
`tests/test_name_gate_wall.py` and `tests/test_vault_path_required.py` are all unmodified, and the
last two are IMPORTED FROM rather than edited (`test_fixture_vault.py:1295-1300`), which is the arm
the boundary named. `tests/test_name_gate_wall.py:1057`'s name is renamed AROUND, not into: this
item's wall test is
`test_the_fixture_vault_files_close_their_wall_memberships_by_running_each_predicate` (`:1287`).
No `conftest.py` was added, and `:1355` asserts its continued absence. The two out-of-scope working-tree
docs (`docs/identity-engine-endgame.md` and its new rounds drawer) are WI-023's machine-maintained
archive split — that file carries `id: WI-023` and the `archive-split` pointer — not this build's
traffic. No `cage-reverted writes` block was supplied, so there is nothing on that arm to check and
none is manufactured.

### The five AI-maintainability checks

1. **New cross-project reach — NONE.** Every root is derived from `__file__`
   (`fixture_vault.py:39`, `test_fixture_vault.py:69`, `derivations.py:28-31`). No `sys.path.insert`
   in shipped code, no sibling-repo path, no foreign `.env` or state read. The one `sys.path.insert`
   is inside the digest-regeneration recipe in a docstring (`fixture_vault.py:24`), which is a
   documented one-liner for a human at the repo root, not an import-time act.
2. **New silent swallow — NONE.** The two `except` blocks in the new test module are assertion
   plumbing that re-raises on the wrong outcome (`:466-474` asserts on the caught `AssertionError`;
   `:608-616` and `:1027-1035` raise `AssertionError` on the `else` arm). `skip_reason_return_values`
   RAISES on an unresolvable return (`derivations.py:1574-1578`) rather than under-reading, and its
   planted battery drives all three unresolvable shapes.
3. **Docs made false — NO.** Walked `CLAUDE.md` assertion by assertion and agree with the Build Log's
   reading rather than taking it: the test-count sentence explicitly refuses to carry a number, the
   loud-fail section routes the reader to `obsidian_schemas.__all__` at run time and `SKIP_REASONS`
   does not join `__all__`, the Key Files table is a pointer list rather than a manifest, and P2's
   "no `conftest.py` anywhere" is still true and now asserted. The stale-`.pth` note stays true and
   the regeneration recipe is written to survive it.
4. **New dependence on deprecated code — NONE.** No import from an archive or deprecated module.
5. **Idiom regression — NONE.** The `ast` capability stays single-homed in `tests/derivations.py`
   (W-1/W-2, re-run at `:1309-1312`); the skip-reason vocabulary moves from three hand-typed sites to
   a declaration plus one deliberate spelling pin (W-15, `:1315-1318`); the interpreter bridge is the
   module's first executable statement, ahead of every package import (`:25-27`), which is the
   convention six sibling check modules already follow.
6. **A build declared from source-reads with a dead shell — NO.** The Build Log carries executed
   numbers rather than claims: a pre-edit floor of 667 in 10.21s against worktree HEAD `f0166ec`, a
   post-Task-12 floor of 678 in 9.91s, a census read yielding 16 class fences / 42 pool fences / a
   161-token M2 sweep with a named 116-token residue, and fifteen mutations each with a distinct
   observed failure mode (including mutation 9, whose finding is the GREEN half — 676 of 678 staying
   green while only the parity check reddens). That is not a shape a source-read build produces.

### Step 2c — data-quality discipline

6. **Readback — SATISFIED, and it is the item's own subject.** The only writes are
   `materialize_vault`'s `write_bytes` into a caller-supplied temp directory (`fixture_vault.py:647`)
   and the test-local write-door calls. Both are read back and asserted: AC-1(b) re-reads every
   materialized member and compares bytes, recomputes the digest over the materialized tree, and
   re-invokes against the same `dest` to assert overwrite-with-identical-bytes plus foreign-file
   survival (`test_fixture_vault.py:549-572`). AC-2(c) re-PARSES what the write door produced and
   compares the frontmatter mapping to the declared oracle (`:687-695`). No external service is
   touched, so there is no outbound write without a readback.
7. **No-silent-PASS-on-empty — SATISFIED, and unusually thoroughly.** Every derived population
   carries a non-empty plus a size assertion at the moment of writing: `_branch_ids` (`:527-528`),
   `TYPE_TO_MODEL` (`:643-644`), the narrowing arm's difference (`:699`), `_exported_repositories`
   (`:852-853`), `SKIP_REASONS` (`:423-424`), the census class rows (`:726`), the pool rows
   (`:1071`, re-asserted at `:1124`), the declared-check population (`:1374`) and W-8's
   reached-equals-corpus clause (`:1327`). The fence readers are LOUD on an unknown key, a missing
   required key, a duplicate key, a non-integer count, a status outside the two-member vocabulary and
   a duplicated id (`:100-136`); `declared_census_digest` is RED on zero matches as well as on many
   (`:182-186`); `_declared_pytest_python_files` RAISES on a missing section, a missing key or an
   unparseable list rather than defaulting to `test_*.py` (`:1274-1283`); and W-14 carries a positive
   control so the matcher cannot pass by matching nothing (`:1352`). The one place a scan could
   silently under-read — `skip_reason_return_values` — is bound by set EQUALITY rather than
   containment, which converts an under-read into RED.

### Criterion-by-criterion conformance (read, not re-run)

- **AC-1.** Digest is over sorted `(bare filename, bytes)` NUL-framed on both sides, and the walk is
  literally the walk `materialize_vault` performs (`fixture_vault.py:645-667`), so leg (b)'s
  digest-over-the-materialized-tree is a real assertion rather than a tautology. The second-call arm
  asserts overwrite, digest-unchanged over corpus members only, and foreign-file survival — the oracle
  is correctly the members and not `corpus_digest(dest)`. Leg (c) reads "named as such" off
  `NoteSpec.discriminator`, validates the value against the package's own `branch_id` union so the
  field cannot be padded with free text, and requires `shape_classes == ()` on both — which is the
  R10(a) closure, implemented as specced.
- **AC-2.** Population read from `TYPE_TO_MODEL`; gate-clean read from `TIER1_BRANCHES` /
  `COMPANY_TIER1_BRANCHES` via `Tier1Branch.matches` rather than a transcribed corruption list; leg
  (c) goes through `write_markdown_file` (the gated door) and compares the RE-PARSED mapping, with
  `_frontmatter_key` correctly resolving `GiftIdea.for_person` to its `for` alias. The narrowing arm's
  population is `set(TYPE_TO_MODEL) - set(ENTITY_BODY_CONFIG)`, computed rather than listed.
- **AC-3.** Fixity first (`:723`), then the MEASURED-only equality whose manifest side deliberately
  reads `shape_classes` and never `discriminator` (`:734`), then the status-conditional row shape,
  then the floor with the branch half derived and asserted in BOTH directions (`:765-772`) and the six
  branchless classes hand-listed. Per-specimen verdicts are declared and asserted three ways
  (refusal with the `pattern` attribute, `clean_person_name` output, byte-identical load).
- **AC-4.** Domain is one repository throughout; the repository set is the `__all__` export filtered
  to concrete `BaseRepository` subclasses (never `__subclasses__()`), which correctly drops
  `VaultPathNotConfiguredError`; the double-ownership of the two untyped classes is declared in
  `SKIPS` and book's mapping is asserted disjoint from the untyped set — the only exercise of the
  catch-all `_owns(None)` arm in the suite. `LOADABLE` is the CACHE quantity with the three-filename
  collision collapsing person to 20, which is exactly R5's predicted off-by-two, declared rather than
  discovered.
- **AC-5.** Reach is corpus plus manifest. The hex exemption is by NAME and by equality, asserted
  well-formed, asserted present against the UNION and excised per file — the two readings the criterion
  distinguishes are implemented on the correct sides (`:978-1000`). The position split holds: the
  identity leg admits only `NAME_POOL ∪ CONNECTIVE_SET ∪ _GENERIC_ORG_SUFFIXES` and
  `PROSE_ALLOWLIST` is asserted DISJOINT from the identity token set, so an allowlist entry buys
  nothing for a name field. `CONNECTIVE_SET` is asserted equal to the literal AC-5(b) freezes.
  Provenance is a containment in the stated direction with the disjointness and non-empty clauses.
  M1 scans the census's whole byte stream through the SAME `identity_tokens` object and asserts
  `CENSUS_PROSE_ALLOWLIST` disjoint from the pool table. I re-derived the non-vacuity clause by hand:
  all 42 `NAME_POOL` members occur in at least one identity position (name, alias, company, stem,
  attendee, author, publisher, director, streaming service, source, `for`, `related` wikilink or
  undeclared key), so the clause is satisfiable rather than merely asserted.

### Findings

**Blocking: none.**

**Note 1 — the declared-value oracle binds 8 notes, and AC-5(b)'s identity set inherits that.**
AC-2's per-note oracle runs over the eight `roundtrip_representative` notes; a filler note such as
`@Isolde Quenlaw.md` has declared `fields` that nothing compares against its bytes (AC-3's verdict arm
covers only notes carrying `shape_classes`). AC-5(b) then builds `id_tokens` from the MANIFEST's
declared values plus filename stems (`test_fixture_vault.py:928-950`), so a divergence between a
filler note's stored `name:` and its manifest entry lands in the free-prose leg, whose cheapest green
is a `PROSE_ALLOWLIST` entry. This is the signed criteria implemented faithfully — AC-5(b) defines
identity positions as "the manifest's DECLARED values", and AC-5's `why:` already names the free-prose
residue — and the filename stem, which comes from the real file, is walled. Recorded so a later item
can decide whether to widen leg (b)'s identity source to each note's own parsed frontmatter; it is not
a build defect and no criterion asks for it.

**Note 2 — the corpus's non-ASCII filenames are compared as checked-out bytes.**
`@Søréna Kelmarrä.md` and `@Oskaline Brenvik-Tarnquil.md` are matched by `set(members) == set(NOTES)`
(`:538`) and hashed by `corpus_digest`'s `path.name.encode("utf-8")` (`fixture_vault.py:663`). On a
filesystem that normalises to NFD, both would redden against a wholly correct tree. Harmless on APFS
and on ext4, and out of this item's stated scope — noted only because D6 designs the corpus to travel
to three consumer repos, so it is the kind of thing the export item should be told rather than
surprised by.

**Note 3 — W-10's inner loop is vacuous if a module defines no top-level check.** `:1361-1365`
iterates `re.findall(r"^def (test_\w+)\(", ...)` over six modules; a module contributing zero matches
contributes zero assertions silently. Every one of the six does contribute today, and the surrounding
row is non-vacuous, so nothing is currently unguarded. Mentioned for completeness against the
non-vacuity discipline the rest of the module holds itself to.

**One thing verified rather than assumed.** The corpus's 53 `.md` files JOIN W-8's repo-wide markdown
scan (`docs` is excluded, `tests/fixtures` is not), and that scan's read is
`read_text(encoding="utf-8", errors="replace")` at `tests/test_vault_path_required.py:451` — I read
that line rather than trusting §11's citation, because the non-UTF-8 member would otherwise crash a
shipped wall this item does not own.

**Summary.** A faithful, unusually disciplined implementation of five signed criteria and two folded
mitigations, with no cross-project reach, no silent swallow, no falsified doc claim, external writes
read back by construction, and no path where empty or absent input passes by default. Blocking: none.

```verdict
gate: code-reviewer
verdict: PROMOTE
date: 2026-09-10
model: claude-opus-5
note: Every write is a declared target, the census is read and never written, all six AI-maintainability and both Step-2c checks pass on a read of the final bytes, and the five criteria are implemented as signed — three non-blocking notes, zero Blocking.
```

---

## Retrospective — 2026-09-10

### Was the spec accurate?
Yes at build time — but it took 9 REVISE rounds (plus separate Spec Review and
Architectural Review tracks bouncing to rounds 6 and 10 respectively) to get there.
Once signed, the build log is explicit that "no criterion was narrowed and no
assertion was relaxed to fit what was found" — build only surfaced 5 small
implementation-level discoveries (nesting-guard for `<locals>` qualnames, hex-literal
literal-form requirement, moving URL-bearing fields off round-trip representatives,
reserving WhatsApp JIDs on two predicates, YAML-quoting `Book.isbn`), none of which
required a spec change. Code review and test/observability review both PROMOTEd on
first try. So: accurate at build, but expensive to reach.

### Edge cases that surprised us
None during build — the 5 discoveries above were implementation mechanics, not
uncovered edge cases; the spec's Edge Cases section (empty/malformed input, corpus
trust boundary, ambiguous census rows, a run beginning with `'`/`-`, ISBN-as-phone,
hex-literal-as-phone, etc.) held up and nothing outside it forced a build-log
deviation.

### What would have shortened the build?
The build itself was fast and clean (12 tasks, one pass, floor GREEN at 678). The
real cost was upstream, in spec review: **9 of the ~10 REVISE rounds were the same
underlying defect recurring in different clothes** — a hand-built/hand-transcribed
set (name pools, allowlists, skip-reason lists) presented as if derived, when it
wasn't actually generated by applying a stated rule to a named, enumerable code
surface. Round 7 named this root cause explicitly; rounds 8 and 9 (census fixity via
`CENSUS_DIGEST`, and `SKIP_REASONS` becoming a real package export instead of a
hand-typed mirror) were the only rounds that found a *different* class of defect.
A spec-writer/AC-red-team check that asks "is this set enumerated by a rule over a
named surface, or just typed out?" earlier in the loop would likely have collapsed
rounds 3–7 (and possibly 9) into one round.

### Did the build serve the original intent? (WI-061 check)
Yes. The Intent (one frozen, real-shaped vault so every later name/identity change
regresses against it, no live Dave-identifiers, previously-untested entity types made
visible) matches what AC-1 through AC-5 signed and what the build delivered: a
53-note byte-copied corpus, round-trips for all 8 entity types, a census-backed
corruption-class floor, a skip-surface equality check, and an identifier-freedom
check. No drift between signed intent and shipped build was found.

### Recommended follow-ups
- Consider a spec-writer / AC-red-team bar update: when an AC declares a *set*
  (allowlist, name pool, corruption-class list, skip-reason list), require the spec
  to name the enumerable code surface and the rule applied to it, rather than
  accepting a hand-transcribed list — this one check would have addressed the
  pattern behind the majority of this item's REVISE rounds. Dave's call whether this
  is worth a standing bar rule or was specific enough to this item's domain
  (identity/name-shape fixtures) to leave as-is.
- No post-done defect surfaced — nothing to record in the eval ledger for this item.



### Trigger filter — PARTIALLY APPLIES, and the applying half is stated

This build adds no production path, no automation, no persistence, no integration, no role or routine
and no skill or agent taking user input. The single package change is a module-level frozenset plus
three string constants in `obsidian_schemas/repositories/base.py:41-48`, with `_skip_reason`'s three
arms returning those names instead of re-spelled literals — same values, same control flow, no new
failure mode and no new caller. Everything else is test infrastructure. So Checks 2 and 3 self-declare
N/A below with the reason, and Check 1 applies in full because the item's whole deliverable IS the
test surface.

### Check 1 — Tests exist for the new code paths: PASS

- **The package change is bound rather than merely exported.** `SKIP_REASONS` is tied to
  `_skip_reason`'s own returns by a syntax scan asserted as set EQUALITY
  (`test_fixture_vault.py:417-420`), so an arm added without a member, or a return the scan cannot
  resolve, is RED rather than green. Both halves are exercised: Verification mutation 5 records the
  fourth-arm case reddening at the scan equality AND the member-without-specimen case reddening at
  AC-4's union.
- **The two new `derivations.py` scans have a planted battery, driven through the SAME function
  objects the live legs call.** `skip_reason_return_values` gets four must-resolve shapes (literal
  return, module-level `str` Name, two arms in one function, arms under `if` and `for`), three
  must-raise shapes (local variable, f-string, subscript) and the nested-function near-miss;
  `skip_reason_literal_sites` gets four must-match shapes and four must-NOT-match near-misses (a `#`
  comment naming all three, a prose docstring, a substring, and the constant NAMES as identifiers) —
  `:437-503`. That is happy path plus failure mode plus discrimination, which is the bar.
- **The five acceptance checks are each a top-level zero-argument `def test_*`** matching the
  battery's direct-invocation contract, and each is the `check:` name its criterion declares.
- **Failure modes are exercised, not reasoned about.** Fifteen mutate-and-observe acts are recorded
  with a DISTINCT observed failure per mutation, each reverted. Two of them are the ones worth having:
  mutation 9, whose finding is that 676 of 678 cases stay GREEN while only the parity check reddens
  (the floor is structurally blind to a missing interpreter bridge), and mutation 14, which points the
  census scan at a file with no pool fences and confirms RED rather than a vacuous green.
- **Walls are closed by RUNNING each wall's own shipped predicate on the final bytes**, not by
  reasoning about which shapes match: `modules_using_ast` projected as the shipped assertion projects
  it, `skip_reason_literal_sites` over the live universe, `_scanned_markdown_files` and
  `NO_ARG_CONSTRUCTION` imported by name from the wall's own module with a non-vacuity clause,
  `check_module` over every top-level check the six write targets define, and `criterion_checks` /
  `run_foreign` over this document's five names asserting BOTH halves of the shipped oracle — exit 0
  AND the delegation marker — plus the nonexistent-check near-miss control (`:1287-1414`). W-14, the
  one row with no callable predicate, is declared as such and driven through the config's own values
  by a helper that raises rather than defaults.
- **Regression surface.** The five edited test modules are additive or one-line repoints whose
  constants carry the same values, so the named regression rows hold; the four count pins at
  `tests/test_concurrent_access.py:1077-1089` are over populations this item does not move (no new
  reserializing function, no falsy return in a write path, no `BaseRepository` subclass, no
  `_load_file`). Floor moved 667 → 678, directionally correct as the invariant requires.

### Check 2 — Logging at WARN/ERROR for each failure mode: N/A, with the reason

There is no new failure mode to log. `_skip_reason` is a pure classifier over an exception type whose
three arms return the same three strings as before; the existing `SkippedNote` surface, its
`bounded_detail` and the repositories' skip logging are untouched. The new modules are test-time only
and signal failure by raising with a message that names the offending file, token, row or repository —
which is the correct instrument at this layer. No silent failure mode is introduced.

### Check 3 — Alerts wired for new automated systems: N/A, with the reason

No new automated system, launchd unit, cron entry, endpoint or scheduled job. The failure channel for
everything here is the floor command going RED, which is the pipeline's own alarm. The one operational
cost worth recording is R8's: the new module makes six foreign-interpreter subprocess runs per floor
run. Task 12 measured it against Task 1's baseline rather than estimating — the module's own 2.6s, of
which ~2.4s is the three subprocess-making tests, absorbed inside a floor whose wall clock did not
move (10.21s → 9.91s). That is the instrument R8 named, read.

### Check 4 — Invariant registration: SKIPPED (no registry in this project)

`obsidian-schemas` ships no invariant registry: there is no `src/invariants.py` anywhere in the tree
(the v1 registry scope is orchestrator-only). Per this role's rule that dimension is skipped, not
failed, and no `## Observability Waiver` is owed. Noted rather than silently passed so a later reader
can tell the grep was run.

### Findings

**Blocking: none. Recommended: none.**

**Note — the observability that matters here is friction, and it is already written down.** Both
allowlists are the residue of their own scan over the artifact they cover, so editing
`tests/fixture_vault.py`'s docstring can redden AC-5 and a census refresh reopens M1 with a conductor
pass as the only remedy. The build recorded this in `## Build Log`'s closing section rather than
leaving the next author to discover it, which is the right disposition; the disjointness assertion is
what keeps the remedy honest. No action.

```verdict
gate: test-observability-checker
verdict: PROMOTE
date: 2026-09-10
model: claude-opus-5
note: The package change is bound to its function by a set-equality syntax wall with a planted must-resolve/must-raise battery, all five criteria checks plus fifteen reverted mutations and six shipped-predicate wall runs are in place, and Checks 2-4 are N/A or skipped for stated reasons — no new prod path, no new failure mode, no registry in this project.
```
