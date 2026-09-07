---
id: WI-016
title: "Frozen anonymized real-data fixture vault"
project: obsidian-schemas
stage: specced
created: 2026-03-22
last_touched: 2026-09-07
stage_changed: 2026-09-07
touched_by: spec-writer
tags: [testing, real-data-fixtures]
depends_on: []
round_budget: 12
transitions: ["idea>exploring@2026-09-07@porter", "exploring>specced@2026-09-07@porter"]
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
`_plant`, `_rich_note`, `_plant_company_note`, `_plant_carrier`. Nine helpers, thirteen files, one
job.

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
| P10 | `rg 'José\|García\|Anne-Sophie\|Legrain\|Moises\|Vetup\|Sören'` over the tree | **38 hits across 8 files** — 35 in code: `test_wi126_body_preservation.py` 12, `test_repositories.py` 9, `test_name_validation.py` 5, `test_identity_index.py` 5, `test_name_cleaning.py` 4, `obsidian_schemas/name_cleaning.py` 1. The corruption corpus exists; it is just scattered and invisible to any test that did not type it. |
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
  `@*.md` (`base.py:196-198` — neither subclass overrides it), meeting declares `Meeting *.md`
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
person and company both inherit the default `@*.md` (`base.py:196-198`; neither subclass overrides),
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
the conductor to certify that `Ltd` occurs zero times in a vault of 2,159 company notes. Reading that
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
no fixture module may name it. Migration of existing tests is
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

```writes
path: obsidian_schemas/repositories/base.py
why: Task 2 — the module-level SKIP_REASONS frozenset (this item's ONLY package change) plus the three module-level reason constants _skip_reason returns by name, per AC-4's "create the declaration rather than keep transcribing it" fold; inside write_authority (P7).
```

```writes
path: tests/derivations.py
why: Task 2 — skip_reason_return_values, the one syntax scan binding SKIP_REASONS to _skip_reason's own returns. It lands HERE and nowhere else because `ast` is single-homed to this module by a standing set-EQUALITY wall over python_files_under(PACKAGE_ROOT, TESTS_ROOT), asserted twice (tests/test_name_gate_wall.py:1136 and tests/test_loud_fail_harness.py:103), so a syntax-reading predicate has exactly one legal home (P9).
```

```writes
path: tests/fixtures/vault
why: Tasks 3-4 — the frozen corpus DIRECTORY, ~50 flat markdown notes. The directory is declared rather than its members because the members' FILENAMES are a function of the census's measured shape classes and pool tokens, and the census is a precondition that does not exist yet: enumerating fifty concrete paths here would be inventing the artifact's content, which is the D2 fixture-drawn-from-fixtures this item rejects. The filename GRAMMAR is pinned in Design §1.2 so the set is derivable rather than arbitrary, and `tests/**` is inside write_authority (P7) so every member is writable whatever it is called.
```

```writes
path: tests/fixture_vault.py
why: Tasks 4-8 — the declared manifest (NOTES / SKIPS / LOADABLE / RESOLVABLE / IDENTITY_FIELDS), the frozen CORPUS_DIGEST with its regeneration recipe in the module docstring, materialize_vault's byte copy, and AC-5's three literal frozensets. No test logic lives here.
```

```writes
path: tests/test_fixture_vault.py
why: Tasks 2 and 4-9 and 12 — the five acceptance checks, the SKIP_REASONS binding test with its planted-shape battery, the identity-token extractor's claimed-match-shape battery (WI-235), the census fence reader, and the wall-membership run. New module; every `check:` name AC-1 through AC-5 declares resolves here and nowhere else, which is the uniqueness rule tests/test_ac_interpreter.py:76-87 states for this project.
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
why: Task 11 — the one line at :187-188 that hand-types the same three skip-reason strings the fold's own solve-in-one-place argument cites; it reads SKIP_REASONS instead, which is strictly stronger (a fourth reason with no specimen in that module's matrix vault goes RED where the hand-typed set stays green).
```

## Acceptance Criteria

Draft — originated cold-start, approval-only, re-derived from the frozen `## Intent`. **Not yet
frozen:** the `ac-signoff` fence is written by `bin/review-spec-helper.py` only after Dave's review,
never by hand. Every `check` is a top-level zero-argument `def test_*(` that signals failure by
raising, per the battery's direct-invocation contract (`tests/support.py:1-19`).

```criteria
id: AC-1
desc: A frozen corpus exists at `tests/fixtures/vault/` holding at least 50 notes, and it is materialized by BYTE COPY rather than by any write door. Three legs. (a) FROZEN — `tests/fixture_vault.py` declares a digest constant computed over the corpus as `sha256` of the sorted sequence of (repo-relative POSIX path, file bytes), and the digest recomputed at test time EQUALS it, so editing, adding or deleting any fixture note without updating the constant is RED. (b) FAITHFUL — `materialize_vault(dest)` into a fresh empty directory reproduces the corpus byte-for-byte: the same relative path set and the same per-file bytes, with the digest over the materialized tree equal to the same constant. (c) THE DISCRIMINATOR — the corpus contains at least one note whose stored `name:` matches a live Tier-1 branch (an arrow-connective descriptor and a path-hostile name are both present, named in the manifest as such), and materialization of the WHOLE corpus succeeds with those notes present and byte-identical. A build that materializes via `repo.save()`, `write_markdown_file` or `create_stub` raises `NameGateRefusal` on exactly those members and is RED on this leg.
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
desc: Every corruption shape class the census MEASURED has a specimen in the corpus, every specimen has a declared verdict, and every class the census RULED ABSENT is on the record rather than missing. The class table is read from `docs/vault-shape-census.md` (the precondition artifact), whose rows carry a class id, a `count`, a `status` of MEASURED or ABSENT, the scan command, its stdout and — for MEASURED rows only — a specimen. THE THREE ASSERTIONS ARE SCOPED BY STATUS, WHICH IS WHAT KEEPS THIS CRITERION AND `## Write Targets` FROM CONTRADICTING EACH OTHER. (i) EQUALITY, over MEASURED rows only: `{class id : status == MEASURED}` EQUALS the manifest's covered classes, both directions — a measured class with no specimen in the corpus is RED, and a specimen belonging to no measured census class is RED. An ABSENT row is outside this equality entirely and is never RED for having no specimen. (ii) PER-ROW SHAPE, conditional on status: a MEASURED row must carry a count > 0, a non-empty command, non-empty stdout and a specimen; an ABSENT row must carry a count of exactly 0, a non-empty command, non-empty stdout and an affirmative absent ruling, and must NOT carry a specimen — so a class cannot be hidden by leaving its status blank, and an "absent" ruling cannot be asserted without the scan that supports it. THE NON-EMPTY-STDOUT ASSERTION IS SATISFIABLE AT BOTH STATUSES ONLY BECAUSE OF A CONSTRAINT ON THE COMMAND, AND THAT CONSTRAINT IS PART OF THIS CRITERION RATHER THAN AN ASSUMPTION IT MAKES ABOUT THE CONDUCTOR: `## Write Targets` requires every recorded scan command to emit a COUNT rather than raw match lines, so a true zero result records verbatim as `0`. Asserted against a bare match-listing scan this leg would be unsatisfiable by construction on exactly the honest ABSENT row it exists to police — a search that finds nothing writes nothing — and the only routes through would be typing non-verbatim prose into the ledger or leaving a correctly-ruled-absent class permanently RED. (iii) THE CLASS FLOOR — DERIVED FOR THE HALF THAT HAS A DECLARATION, HAND-LISTED ONLY FOR THE HALF THAT DOES NOT. The ids below are asserted PRESENT in the table as rows of EITHER status, which is the machine-checked form of `## Write Targets`'s "a class measured at ZERO is a row the conductor writes": it is what stops a census from silently omitting a shape, rather than trusting prose to the conductor. **THE BRANCH HALF IS READ FROM THE PACKAGE AT TEST TIME AND IS NOT TRANSCRIBED INTO THIS CRITERION AT ALL** — the floor includes `{record.branch_id for record in TIER1_BRANCHES + COMPANY_TIER1_BRANCHES}` (`name_validation.py:190-309` and `:371-438`), the same runtime read of an exported declaration AC-2 makes against `TYPE_TO_MODEL` and AC-4 against `_skip_reason`'s codomain, and the same sweep unit `tests/test_name_gate.py:212` and `tests/test_company_name_contract.py:369` already use — so the census's class table must carry a row for EVERY refusal branch this package declares, and a branch added to either table later joins the floor automatically instead of waiting for someone to notice. Ten ids today, and THE DERIVED SET IS ASSERTED NON-EMPTY AND OF EXACTLY THAT SIZE (LESSONS #46: a derived read returns green when it works and green when it silently reads nothing — an import resolving to an empty tuple, a renamed `branch_id` attribute — so the size at the moment of writing is the cheapest available form of having seen the derivation red; it is the POPULATION's size and never an oracle, since what each specimen must produce stays hand-declared): `email_chars`, `rfc2822_leak`, `arrow_connective`, `calendar_prefix`, `me_to_prefix`, `path_hostile`, `archive_prefix`, `unknown_contact`, `pure_digit`, `empty`. THE FLOOR IS ASSERTED IN BOTH DIRECTIONS OVER BRANCH-KEYED ROWS, not only as census ⊇ derived: every census row whose id is branch-shaped must also be IN the derived set, so a row naming a `branch_id` the package no longer declares is RED rather than surviving as a phantom — assertion (i) supplies the reverse direction for MEASURED rows only, which leaves exactly the ABSENT phantom uncovered, and LESSONS #45 says a check documented as deliberately one-directional is an open defect rather than a note. THE COMPANY ARM IS OUT OF THIS CORPUS'S SCOPE, STATED AFFIRMATIVELY RATHER THAN CLAIMED AS A SIDE EFFECT: five ids appear in both tables (`email_chars`, `arrow_connective`, `path_hostile`, `archive_prefix`, `empty`) but a deduped floor writes ONE census row per `branch_id` and the corpus carries ONE specimen, whose DECLARED TYPE decides which table `gate_write` consults (`name_gate.py:329-343` vs `:361-363`) — so a person-typed `path_hostile` specimen exercises the person arm ONLY, and an earlier draft's "those specimens exercise the company arm as well" was one word too strong. That is not a coverage hole and no company-typed specimen is required here: the company table already has its own in-tree refusal sweep over every one of its records' `specimen` and `negative_specimen` (`tests/test_company_name_contract.py:359-459`), which is the WI-022 surface this item does not duplicate. THE CLASS TABLE'S ROW ID FOR A BRANCH-BACKED CLASS IS THE `branch_id` ITSELF, so those ten need no naming reconciliation before origination and cannot drift apart from the package. THE KEY IS `branch_id` AND NEVER `pattern`: `arrow_connective`, `calendar_prefix` and `me_to_prefix` all RAISE the shared pattern `calendar_prefix` (`:216`, `:228`, `:240`, stated outright in the dataclass docstring at `:152-154`), so a pattern-keyed floor would silently re-merge three classes this criterion treats as separate — `Dave -> Thomas Gatten`, `Dave - Thomas Gatten` and `Me to David Field` (`:217`, `:229`, `:241`) are three distinct character profiles the census must measure one at a time, and the census must be authored against those profiles rather than against a paraphrase of them. **THE HAND-LISTED HALF IS THE SIX SHAPE CLASSES THAT HAVE NO BRANCH**, where there is no declaration to derive from and this list is the only available statement of intent: diacritics, hyphenated/multi-part surnames, whitespace damage (double-space / leading-trailing — Tier 2, `_DOUBLE_SPACE_RE` `:445`, no Tier-1 branch), filename-stem-does-not-equal-stored-name divergence, a same-name collision of at least three notes, and A POSTAL ADDRESS LEAKED INTO A NAME FIELD, which `### Examples of done` names by name and which no branch is (the nearest, `rfc2822_leak`, is an at-mangled address FUSED ONTO a name — its own specimen is `Naomi Pavie naomipavieatspeechmaticscom`, `:202-205` — not a postal address), so the census is charged in `## Write Targets` with either confirming that one present with a MEASURED row and a specimen or writing an ABSENT row that states affirmatively it does not occur in the live vault. ONLY THOSE SIX are reconciled to the census's own naming BEFORE origination — the artifact is a precondition and lands in HEAD while these criteria are still drafts (WI-300), so a shape class the census names differently costs one edit here rather than a re-sign. For each class on the floor, the manifest declares the verdict the specimen must produce and the test asserts it: either a refusal (`NameGateRefusal` — the WI-021 leaf, never the `LoudFailError` root — carrying the named `pattern` on its `.pattern` attribute when the specimen's name is re-introduced through a write arm), or a declared cleaned form (`clean_person_name` output asserted equal to a hand-written string), or a declared successful byte-identical load. SOME BRANCHES WILL PLAUSIBLY DISCHARGE AS ABSENT, AND THAT IS THE FLOOR WORKING RATHER THAN AN OBLIGATION THE CORPUS CANNOT MEET: `empty` above all — `create_stub` guards its validator call with `if name and name.strip():`, so the branch has never fired in production and this item is what introduces it on the write path (`name_validation.py:295-299`) — and a live vault holding no empty-named note gets an ABSENT row with its count, command and stdout, satisfies assertion (iii), never enters assertion (i)'s equality, and obliges no specimen. Both discharges satisfy assertion (iii) and only the MEASURED one enters assertion (i)'s equality, so a class ruled absent is on the record and is not a failure. TWO OF THE HAND-LISTED SIX MAY ALSO BE ONE: the corpus is a single flat directory (see `## Approach`), so a same-name collision is necessarily several distinct filenames sharing one stored `name:` — structurally the divergence class — and the CENSUS rules whether the live vault separates them. If it rules them ONE class, it writes one row whose id the floor accepts for both members of the pair, and the manifest's covered-class set FOLLOWS that ruling; assertion (i) is RED only when manifest and census disagree over MEASURED rows, never for the table holding fifteen class rows rather than sixteen. (iv) CENSUS FIXITY — THE ARTIFACT THIS CRITERION TREATS AS GROUND TRUTH IS FROZEN BY THE SAME MECHANISM AC-1(a) GIVES THE CORPUS, AND ITS EXPECTED VALUE HAS NO IN-CAGE HOME. `sha256` over the bytes of `docs/vault-shape-census.md`, recomputed at test time, EQUALS a 64-character lowercase hex literal — and THE LITERAL LIVES IN THIS CRITERION'S OWN TEXT, filled in at the same one-time pre-origination edit that reconciles this criterion's six hand-listed shape classes and AC-5(b)'s `CONNECTIVE_SET`: the census lands in HEAD as the WI-300 precondition BEFORE Dave signs, so its digest is knowable exactly then, and the signature freezes it. The test READS that literal out of the AC-3 `criteria` fence in `docs/vault-fixtures.md` — a plain in-tree file read, the same hermetic move this criterion already makes on the census, no subprocess and no vault call — rather than comparing against a constant declared in `tests/fixture_vault.py`, and the reason is the whole point of the leg: `docs/**` is builder-writable in full (`pipeline-runners.yaml:34-38`, P7 — no carve-out for a landed precondition), so a constant the build owns can be updated in the same commit that edits the census, and the check certifies nothing. `fixture_vault.py` MAY restate the digest for readability, but the value ASSERTED AGAINST is the one in the signed criterion. The leg additionally asserts that exactly ONE such declaration was found WITHIN THE AC-3 `criteria` FENCE and that it is well-formed 64-character lowercase hex, so a reader helper that finds nothing is RED rather than vacuously green (LESSONS #46 again). THE UNIQUENESS IS FENCE-SCOPED AND NEVER FILE-WIDE, AND THAT SCOPE IS LOAD-BEARING RATHER THAN TIDY: every gate section in this document quotes the criterion text it reviews, so once `CENSUS_DIGEST` carries a real 64-hex value, ONE round-10 quotation of the filled declaration would turn a file-wide uniqueness assertion RED — and its only remedy would be editing a historical gate section, which is the one edit this document's whole carry-forward convention exists to forbid. The read is therefore bounded to the fence the signature freezes, which is the same text the assertion is about. THE DECLARATION, WITH ITS VALUE STILL TO BE FILLED, IS `CENSUS_DIGEST = sha256:<PENDING — 64 lowercase hex, written here at the one-time pre-origination edit once `docs/vault-shape-census.md` is in HEAD, and NEVER by the build>`; origination must not proceed while the placeholder stands, which is the same door AC-3's class-naming and AC-5(b)'s `CONNECTIVE_SET` reconciliation already pass through and costs no extra interruption of Dave. The test reads both artifacts, asserts assertions (i)–(iv) over their parsed rows and text, and makes no subprocess, network or live-vault call.
why: This criterion is what makes the corpus a corruption corpus rather than a tidy sample, and reading the class list FROM the census is what gives the precondition artifact teeth inside the suite: without it the census can be discharged as one hand-waved prose paragraph and the corpus quietly reverts to D2, a fixture drawn from the fixtures that already exist — which LESSONS #27 says is structurally blind to exactly the tail the corpus is for. Equality in both directions is deliberate: one direction stops the corpus under-covering the measured estate, the other stops it accumulating specimens nobody measured, which is how a corpus starts asserting things about a vault that no longer holds. Declaring a verdict per specimen rather than merely holding the bytes is the WI-286 oracle again — a corpus that only CONTAINS `"Dave -> Thomas Gatten (Adzact)"` proves nothing about whether anything refuses it, and the classes listed are precisely the forms this package has already been burned by, so each one having a stated expected answer is what lets the next name-touching change regress against them instead of rediscovering them. Naming the address-leaked-into-a-name-field class explicitly closes the one gap between this list and Dave's own picture of done: assertion (i)'s equality is against whatever the census DECLARES, not against `### Examples of done`, so a census that recorded only the classes it happened to trip over could have dropped the one specimen Dave asked for by name and left every criterion green. DERIVING THE BRANCH HALF OF THE FLOOR RATHER THAN TRANSCRIBING IT IS THE ONE THING TO KEEP IF THIS CRITERION IS EVER EDITED AGAIN, AND THE HISTORY IS THE ARGUMENT. This floor has been hand-corrected twice and been wrong both times: round 3 added it, round 6 added `archive_prefix` and `unknown_contact` and asserted it then covered "eight of the ten live person Tier-1 branches", and a seventh read of `TIER1_BRANCHES` itself found the real prior count was FOUR (`rfc2822_leak`, `arrow_connective`, `me_to_prefix`, `path_hostile`) rising to six, with `calendar_prefix`, `email_chars`, `pure_digit` and `empty` all still missing. `calendar_prefix` was the expensive one: it is a live branch with its own id, its own specimen (`Dave - Thomas Gatten`, `:229`), its own recovery arm (`name_cleaning.py:46`, stripped at `:121`) and it is the sole source of `CONNECTIVE_SET`'s frozen `Dave` member — AC-5(b) justifies that member by citing exactly this branch — while this criterion's own parenthetical named it as a class distinct from the arrow one in the same breath that the floor omitted it. Nothing in assertions (i)–(iii) reads the package's branch table, so a conductor authoring the census works from this list, never thinks to measure `Dave -`/`Me -` prefixes as a class of their own, and every assertion stays green over a corpus with no specimen for four of the package's ten refusal branches — which is precisely the silent omission assertion (iii) exists to make impossible, defeated because the floor never named the shape for the census to measure. That is LESSONS #45 exactly: a registry validated only against itself is a mirror, not a census, and the remedy is to derive the actual population from the source and assert set-equality with the registry. So the fix removes the hand-transcription rather than pruning its third instance — the branch half is now a runtime read of two tuples the package exports and whose `branch_id` is unique by its own docstring, and only the six classes with no declaration to read stay hand-listed. Keying on `branch_id` rather than `pattern` is load-bearing and not a detail: three branches deliberately raise the shared pattern `calendar_prefix`, so a pattern-keyed derivation would re-merge the three classes this criterion separates and reintroduce the same gap by another route. It stays a FLOOR rather than a promise: if the live vault carries no archived or scanner-artifact names, the census writes each an ABSENT row with its count, command and stdout, assertion (iii) is satisfied, assertion (i) never sees them, and nothing is RED. Scoping the three assertions BY STATUS is what makes that fix hold without turning honesty into a failure: the previous draft charged the conductor to write a zero row and then, in the same breath, marked a class with no specimen RED — so a correct, honest census was a false block and the cheapest way back to green was to delete the row, which is exactly the silent omission the fix was for. Splitting them gives each obligation its own assertion: (iii) makes the row's PRESENCE mandatory (the machine-checked form of the prose charge, so no shape can vanish), (i) makes only MEASURED rows owe a specimen, and (ii) stops either from being discharged with a blank cell — a status left empty, a count with no scan behind it, an absent ruling with no command. The floor being reconciled before origination is the WI-300 ordering doing its job: the census lands in HEAD while these are still drafts, so a class the artifact names differently is one line edited here rather than a frozen criterion and a second interruption of Dave. ASSERTION (iv) EXISTS BECAUSE EVERY OTHER ASSERTION IN THIS CRITERION TRUSTS AN ARTIFACT NOTHING IN THIS PIPELINE FREEZES, AND THAT WAS THE LAST UNGUARDED ESCAPE HATCH IN THE SET. The suite is hermetic and cannot read the live vault, so the census is the ONLY place "this class occurs N times in the real vault" can be settled — and its content is entirely unprotected once it lands: `docs/**` is in this project's `write_authority` in full with no carve-out for a landed precondition (`pipeline-runners.yaml:34-38`, P7), the build-spawn precheck and WI-300's grounding-ordering backstop check only that the path is SOME committed blob in HEAD at one moment before the build starts and never compare its content afterwards, and the pipeline's one merge-boundary integrity wall over docs is scoped BY DESIGN to files carrying work-item frontmatter — a shared non-work-item doc's edit is declared legitimate build traffic there, which `docs/vault-shape-census.md` is, carrying no `id: WI-*` of its own. The concrete route it closes, and it is not hypothetical for either criterion that reads the artifact: a builder facing a MEASURED row whose character profile is awkward to author faithfully edits that row in place to `status: ABSENT`, `count: 0`, with a plausible command/stdout pair typed in, and drops the specimen — assertion (i) is scoped to MEASURED rows so the row exits the equality entirely, assertion (ii)'s per-row shape check is satisfied by construction because the builder wrote exactly the shape it demands, nothing re-derives the count because nothing can, and the floor whose declared purpose is "a class measured at zero is a row the conductor writes, not a row that may be omitted" is defeated by precisely the means it exists to prevent, every assertion green. AC-5(c) is the worse half of the same hole and is why the leg is asserted there too: a builder wanting a convenient `NAME_POOL` token that happens to collide with a real name in a vault it cannot see adds a pool-table row with a fabricated non-occurrence scan, and `## Intent`'s one sentence about Dave's contacts' real names has no machine check behind it at all. This criterion's own AC-1(a) already states the remedy applied to the wrong artifact — "frozen without a mechanism is a wish" — and the fix is that identical `sha256`-over-bytes move, with the one difference that decides whether it works: the expected value lives in the SIGNED CRITERION rather than in a module the build owns, because a digest constant a builder can edit in the same commit as the file it digests is not a wall. Absent this leg the census's trustworthiness rests on a human noticing an unexpected diff to a shared doc during code review — which is exactly the "reviewable by eye" control AC-5's own `why:` argues is not good enough for this item's privacy property. ONE RECURRING COST IS NAMED HERE RATHER THAN DISCOVERED BY WHOEVER PAYS IT: because the branch half of the floor is derived, a new Tier-1 branch added to either table reddens this criterion immediately, and discharging it needs a census row carrying a count, a scan command and verbatim stdout — all of which need the live vault, which no caged builder can read — so a routine package change (WI-022 just added a whole company table) is blocked on a conductor pass, and under (iv) that pass now also re-freezes the digest. That is LESSONS #45's intended friction and it is not weakened here; it is written down because round 4 weakened AC-5(c) to a containment specifically to remove paired edits across the cage boundary, and the derived floor reintroduces one in the other direction, so the next branch author should be told rather than surprised.
check: test_every_census_corruption_class_has_a_specimen_with_a_verdict
kind: test
```

```criteria
id: AC-4
desc: Loading the materialized corpus through the repositories produces exactly the declared skip surface, asserted PER REPOSITORY. THE DOMAIN OF EVERY EQUALITY IN THIS CRITERION IS ONE REPOSITORY, NEVER A UNION ACROSS THEM — the manifest declares `{repository_type: {path: reason}}`, keyed by each repository's own `type_name` (`repositories/base.py:191`). THE SET OF REPOSITORIES IS DERIVED, NOT LISTED: the sweep takes the concrete `BaseRepository` subclasses the package exports (`obsidian_schemas/repositories/__init__.py`'s `__all__`, `:14-21` — the imports end at `:12`, and an earlier draft's `:8-20` cite spanned both and matched neither; excluding `BaseRepository` itself) and asserts the manifest declares a mapping for exactly that set, keyed by `type_name` — the same runtime read of an exported declaration AC-2 makes against `TYPE_TO_MODEL` and AC-3 against the Tier-1 tables' `branch_id`, applied here because a hand-written "the four repositories are person, company, meeting, book" is the same transcription that let AC-3's floor sample its own branch table, and a fifth repository added later would otherwise join the corpus's blind spot silently instead of failing until it has declared skips and a declared loadable count. WHICH READ IS MEANT IS PINNED, BECAUSE THE TWO AVAILABLE ONES ARE NOT EQUIVALENT: the sweep iterates the names `obsidian_schemas/repositories/__init__.py` EXPORTS (`__all__`, `:14-21`) and keeps those that are concrete `BaseRepository` subclasses — deterministic, and a fixed list the package authors — never `BaseRepository.__subclasses__()`, whose answer depends on which modules happen to have been imported. THAT EXPORT LIST IS FILTERED, NEVER ITERATED WHOLE, because it is not homogeneous: `__all__` also carries `VaultPathNotConfiguredError` (`:16`), an EXCEPTION rather than a repository, which the concrete-`BaseRepository`-subclass filter drops — the filter as stated already handles it, and saying so here is what saves the build a round spent discovering that a six-name export list does not mean six repositories. And one implementability detail is settled here rather than at build time: `type_name` is an abstract `@property` (`base.py:189-193`), readable off an INSTANCE and not off the class, so each repository must be instantiated against the materialized vault before the manifest's key set can be compared — which legs (a) and (c) do anyway, so this is ordering rather than a gap. Four today — `person`, `company`, `meeting`, `book` — and the derived set is asserted NON-EMPTY and of exactly that size (LESSONS #46, for the same reason AC-2's and AC-3's derivations are: a read that silently resolves to nothing is green, and the size at the moment of writing is the cheapest form of having seen it red). The other four `TYPE_TO_MODEL` members have no repository at all, so they are AC-2's parser-level business alone — and that asymmetry FOLLOWS from the two derivations rather than being separately checked, which is what an earlier draft claimed. Saying it was "itself checked" described an assertion of the form `A - B == A - B`: with both sides derived and no expected value declared, it passes for any package and asserts nothing. It costs nothing to drop, because a fifth repository is already caught by the derived sweep proper — which demands a declared mapping and a declared loadable count for it — and keeping it would have made this criterion its own counterexample to the governing rule it states three sentences later. WHAT IS DERIVED IS THE POPULATION AND NEVER THE ORACLE, AND THE LINE MATTERS: which repositories exist is a fact the package declares and must be read from it, while WHAT each one is expected to own — the globs and the ownership outcomes spelled out below — is the hand-written expected value a wrong-but-self-consistent implementation must MISMATCH (WI-286), so reading those from the code under test would turn this criterion into a mirror of it. THE SKIP-REASON CODOMAIN IS MADE READABLE BY THIS ITEM AND IS THEN READ, BECAUSE TODAY THERE IS NOTHING TO READ AND AN EARLIER DRAFT OF THIS CRITERION CLAIMED OTHERWISE: `_skip_reason` (`repositories/base.py:41-47`) returns three BARE STRING LITERALS — `:44`, `:46`, `:47` — with a type comment on `SkippedNote.reason` at `:37`, and the package exports no frozenset, tuple, dict or enum of them anywhere, so unlike `TYPE_TO_MODEL` (a dict AC-2 reads), the `branch_id` union (two exported tuples AC-3 reads) and this criterion's own repository set (`__all__`), there is no declaration here at all and the only thing anyone has ever been able to do with this codomain is hand-transcribe it, which `tests/test_loud_fail_load.py:187-188` does today (P20). SO THE FIX IS TO CREATE THE DECLARATION RATHER THAN TO KEEP TRANSCRIBING IT, AND IT IS ONE LINE OF PACKAGE CHANGE INSIDE THIS ITEM'S BUILD: `repositories/base.py` gains a module-level `SKIP_REASONS` frozenset whose members `_skip_reason` returns BY NAME rather than as re-spelled literals (`obsidian_schemas/**` is in this project's `write_authority`, P7), and this criterion reads it at test time exactly as AC-2 reads `TYPE_TO_MODEL`. AN EXPORT ON ITS OWN WOULD BE DECORATION — NOTHING WOULD MAKE A FOURTH ARM UPDATE IT — SO IT IS TIED TO THE FUNCTION BY A SYNTAX DERIVATION IN THE ONE PLACE THIS TREE PERMITS ONE: `tests/derivations.py`, the standing shared scan module and the only file under `obsidian_schemas/` or `tests/` allowed to name `ast` (P9), gains ONE scan returning the set of string values `_skip_reason`'s own body can return — every `Return` whose value is a `str` Constant, plus every `Return` of a module-level Name bound in that file to a `str` Constant — and the criterion asserts that set EQUALS `SKIP_REASONS`. THE EQUALITY DIRECTION IS WHAT MAKES THAT WALL HOLD RATHER THAN MERELY EXIST, and it has three consequences worth stating so a builder does not weaken it to a containment: an arm added to `_skip_reason` without a matching frozenset member is RED at that equality; an arm whose return the scan CANNOT resolve to a literal makes the scan silently UNDER-read, which the equality reports RED instead of passing green (LESSONS #46 — the failure mode of every derived read in this document); and `SKIP_REASONS` is additionally asserted NON-EMPTY and of size exactly 3 at the moment of writing, which is the POPULATION's size and never an oracle, since what each specimen must produce stays hand-declared in the manifest. ON TOP OF THAT DECLARATION the criterion asserts that the corpus carries at least one specimen for each member and that the UNION over the four declared per-repository mappings' reasons is EQUAL to `SKIP_REASONS` — so a corpus missing a reason is RED, and a fourth reason added to the package later genuinely does fail until it has a specimen, which is now a property this criterion HAS rather than one it merely stated. THE DOUBLE-OWNERSHIP OF THE TWO UNTYPED CLASSES IS DECLARED EXPECTED BEHAVIOUR, NOT A BUILD-TIME SURPRISE: ownership is decided by `_note_skip` on the error's `declared_type` (`base.py:267-275`), and `FrontmatterParseError` carries `declared_type=None` always (`errors.py:65-67`) while a `UnicodeDecodeError` carries the attribute not at all, so both fall to `_owns(None)`, which returns `Path(self.file_pattern).stem != "*"` (`base.py:258-265`) — TRUE for person and company (both inherit `@*.md`, `base.py:196-198`) and for meeting (`Meeting *.md`, `meeting.py:51-54`), FALSE for book (`*.md`, the catch-all, `book.py:50-53`). Combined with the flat directory's glob partition, the manifest therefore declares, and the test asserts: a malformed-frontmatter or unreadable specimen FILENAMED `@<name>.md` appears in BOTH person's and company's mappings and in NEITHER meeting's (its glob does not match) nor book's (its glob matches but its catch-all stem declines ownership); the same specimen filenamed `Meeting <date> - <title>.md` appears in meeting's mapping ONLY; and a `schema-drift` specimen, which does carry a `declared_type` (`errors.py:70-71`), appears ONLY in the mapping of the repository whose `type_name` equals it. Three legs. (a) SKIPPED — for EACH of the four repositories independently, the mapping `{note.path: note.reason for note in repo.skipped_notes}` after loading the materialized vault EQUALS that repository's declared mapping, both directions: a malformed specimen that silently loads anyway is RED, a well-formed note a repository wrongly skips is RED, and an untyped skip that moves between owners is RED in two mappings at once. (b) THE PLANTED DISCRIMINATORS — the corpus contains an untyped specimen under EACH of the two owning globs (one `@<name>.md`, one `Meeting <date> - <title>.md`), and book's declared mapping over the untyped classes is asserted EMPTY: without the second filename a stub that records untyped skips in one repository only is indistinguishable from the real rule, and without book's empty assertion the catch-all arm of `_owns` is never exercised by anything. (c) LOADED — `len(repo.get_all())` for each of the four repositories equals that repository's declared loadable count, and the resolvable identities declared in the manifest all resolve, so a corpus whose malformed members poison the surrounding load is RED rather than merely under-reported.
why: WI-020 built `SkippedNote` because an unloadable note used to vanish at DEBUG — invisible to the cache, so `resolve()` missed it and `find_or_create_stub` minted a duplicate, the dup-proliferation class WI-119/WI-125 exist to fight (`base.py:29-34`). That surface has never had a vault on disk containing one of each and stating which is which, so nothing today would notice a regression that reclassified `schema-drift` as `unreadable` or that swallowed a malformed note without recording it. Set equality in both directions is what makes leg (a) an oracle rather than a membership check: `skipped_count >= 3` is passed by a repository that skips everything, and `skipped_count == 3` is passed by one that skips the three WRONG notes. But a both-directions equality with an UNSTATED DOMAIN is not an oracle either, and that was this criterion's real gap: a union over all repositories and a per-repository mapping are two different declared manifests, each passes its own reading, and only the per-repository one goes RED when a regression moves an untyped skip between owners — which is the exact regression this surface exists to catch, because ownership is what decides whether a bad note is VISIBLE to the repository that would otherwise mint a duplicate for it. Declaring the double-ownership rather than discovering it is the WI-144 economy: a build that meets it as a surprise reads two repositories reporting "the same" note, concludes the test is wrong, and quietly relaxes the equality to a union — losing the property. Leg (b) is WI-286's planting rule applied to this criterion's own discriminant: the corpus, not the code, has to supply the case that tells the per-repository rule apart from every cheaper approximation of it, and book's empty mapping is the only assertion in the suite that the catch-all glob DECLINES ownership by design. Leg (c) exists because the failure that actually costs data is not the skip, it is the blast radius — a parse failure that aborts the directory walk leaves the cache silently short, and the only way to see it is to declare beforehand how many notes SHOULD have loaded. DERIVING THE REPOSITORY SET RATHER THAN LISTING IT WAS ADDED IN THE SAME PASS THAT DERIVED AC-3's CLASS FLOOR, AND FOR THE SAME REASON RATHER THAN FOR SYMMETRY: this criterion's whole subject is that a note's VISIBILITY is a per-repository fact, so the one thing that must not be hand-maintained is which repositories there are — a fifth one added to the package would inherit `_owns`, take part in the same glob partition over the same flat directory, and be entirely absent from a hand-listed sweep, which is the exact silent under-coverage AC-3's floor was found doing over the branch table. It is also the cheapest possible version of the fix: the subclasses are already exported and `type_name` is already the key the manifest uses. The oracle stays hand-written on purpose and the criterion says so, because the failure this leg exists to catch is a regression in ownership, and an expected value read from the code that computes it agrees with the regression. THE SKIP-REASON CODOMAIN WAS THE SEVENTH INSTANCE OF THIS DOCUMENT'S ONE RECURRING DEFECT, AND IT IS THE FIRST THAT COULD NOT BE FIXED BY READING SOMETHING — WHICH IS WHY THE FIX CREATES A DECLARATION INSTEAD. Two independent round-9 reads — the architect's and the AC red-team's, from a duplication angle and from a satisfiable-with-nothing-real-behind-it angle — found the same fact: this criterion put `_skip_reason`'s reasons on the DERIVED side of the document's residue list and stated a consequence ("a fourth reason added to the package later fails until it has a specimen") that only a derivation delivers, while the package declares no set to read. Both sides of the equality were hand-typed, so a builder who added a fourth arm — a `PermissionError` distinguished as `unreadable-permission`, say; WI-020's own `base.py:29-34` already distinguishes skip incidents by cause — would ship a GREEN criterion with the new failure class in exactly the blind spot `SkippedNote` was built to close, one layer up from where WI-020 closed it. That is a green-over-wrong route rather than a loud one, which is what separates it from round 8's two instances and makes it worth a package change. THE ALTERNATIVE WAS OFFERED AND IS REJECTED FOR A STATED REASON: the honest cheap move was to keep the set hand-written, delete the false consequence and move it into the residue list beside this criterion's ownership oracle. It is rejected because the residue list's own membership test is "there is no declaration to read", and the other four members earn that by their SUBJECT — whether a field's value IS a name, what a shape class should be called, what a repository OUGHT to own — all judgment. Which strings `_skip_reason` can emit is not judgment, it is mechanical, and this is the determinism boundary the whole document is organised around: a mechanical fact carried by a transcription is a defect wherever it appears, and the remedy for the one classification vocabulary that never got the module-level-literal treatment the package gives `TYPE_TO_MODEL`, `TIER1_BRANCHES`, `ENTITY_BODY_CONFIG` and `_GENERIC_ORG_SUFFIXES` is to give it that treatment. It is solve-in-one-place besides — the three strings live in a return chain, a type comment and `tests/test_loud_fail_load.py:187-188` today, and the criterion would have added a fourth home. AND THE EXPORT IS DELIBERATELY NOT TRUSTED ON ITS OWN, WHICH IS THE PART TO KEEP IF THIS CRITERION IS EDITED AGAIN. `TYPE_TO_MODEL` cannot silently fall out of step with the package because dispatch depends on it; a `SKIP_REASONS` frozenset nothing consumes CAN, and a criterion that read it and stopped there would have re-created the same false consequence in a nicer-looking form — the fold breeding its own next finding, which this document has recorded three times. Binding it to `_skip_reason`'s own returns by a syntax scan in `tests/derivations.py` is what closes that, it needs no new machinery (the module exists, is importable, and single-homes `ast` by a standing wall), and asserting EQUALITY rather than containment is what makes the scan's own under-read — the LESSONS #46 failure every derived read in this document shares — report RED instead of green.
check: test_the_skip_surface_over_the_corpus_equals_its_declared_reasons
kind: test
```

```criteria
id: AC-5
desc: No corpus note can carry a live identifier — an email, a phone number, a profile URL OR A NAME — asserted structurally rather than by inspection. THE REACH OF EVERY LEG IS every file under `tests/fixtures/vault/` PLUS `tests/fixture_vault.py` itself, because the manifest restates each specimen's field values as AC-2's declared oracle and a wall that scanned only the corpus would miss a real name typed into the oracle. Five legs. (a) RESERVED RANGES, derived not hand-listed — the test scans those bytes for every email-shaped, phone-shaped and profile-URL-shaped token and asserts each one is inside a reserved range: emails only under RFC 2606 / RFC 6761 reserved names (`example.com`, `example.net`, `example.org`, or a `.test` / `.invalid` / `.example` TLD); phones only inside reserved fictional ranges (UK `+44 7700 900xxx`, NANP `555-01xx`); profile URLs only under a declared placeholder form. The scan is over ALL bytes in reach rather than a field list, so it needs no enumeration to be total — but the fields that carry these shapes are named for the corpus author's benefit, since every one of them must be constructed: `Person.emails` (`models.py:81`), `Person.phones` (`:82`), `Person.whatsapp` (`:83`, a JID whose digits `normalize_phone` splits at the `@` — `phone_normalization.py:39-55`), `Person.linkedin` (`:86`), `Person.slack` (`:87`), `Company.website` (`:129`), `Company.linkedin` (`:131`), `Book.isbn` (`:165`), `Book.source_url` (`:168`) and `Explore.url` (`:223`). (b) NAME CLOSURE, SPLIT BY POSITION AND BY TOKEN KIND — THE SPLIT IS THE WALL. `fixture_vault.py` declares THREE literal frozensets and no computed membership: `NAME_POOL` (the constructed given names, surnames and company words the specimens are built from), `CONNECTIVE_SET` (the corruption classes' own non-identifying furniture, FIXED BY ENUMERATION AT EXACTLY `{"Me", "My", "Dave"}` — the package's OWN calendar/arrow/transcript prefix vocabulary, whose union across the three prefix regexes that spell a capitalized alternative is exactly that set: `name_cleaning.py:46` `_CALENDAR_PREFIX_RE` matches `^(Dave|Me|My)\s*[-/]\s+` and `:54` `_ARROW_PREFIX_RE` matches `^(Dave|Me|My)\s*[→⟶⇒➜↦⇨]\s*`, while `:55` `_ME_TO_PREFIX_RE` matches `^(Me|My)\s+to\s+` and carries NO `Dave` alternative — an earlier draft of this criterion said all three matched `(Dave|Me|My)`, which is wrong about `:55` and right about the union, and the union is what the set is; the test asserts that equality against the literal set written into this criterion, so the set cannot grow without an AC change and is never a build-time choice; the lowercase and punctuation connectives the classes also need, `to`, `->` and `→`, are NOT members, because the stated extractor cannot produce them and a member the closure can never exercise is a declaration that lies, and the mail-header prefixes `Re`, `Fwd` and `Fw` are NOT members for the harder version of the same reason — a Grep over the whole tree finds them in no Tier-1 branch, no recovery regex and no candidate census class, so no census row could ever measure one and no corpus specimen could ever honestly carry one, P11; AND THE SET IS ENUMERATED FROM THE WHOLE FURNITURE SURFACE RATHER THAN SAMPLED FROM THREE REGEXES OF ONE FILE — that surface is SIXTEEN regexes in two files and there is no third — the eleven of `name_validation.py` (`:66`, `:74`, `:82`, `:101`, `:107`, `:110`, `:113`, `:120`, `:123`, `:351`, `:445`) and the five prefix/suffix regexes of `name_cleaning.py` (`:46`, `:54`, `:55`, `:56`, `:57`) — plus both Tier-1 tables, the ten person branches (`name_validation.py:190-309`) and the five company ones (`:371-438`), with P16 recording the complete pass and P17 recording that no regex anywhere else in the package carries furniture. APPLYING THE RUN RULE THIS CRITERION PINS DOWN BELOW TO THE LITERAL SPELLING EACH REGEX CARRIES, THE UNION OF EXTRACTED FURNITURE TOKENS IS EXACTLY `{Me, My, Dave}` AND NO MEMBER IS ADDED — the two branches the earlier sampling omitted are the reason the rule had to be pinned first, and neither adds one. `archive_prefix` (`name_validation.py:110`, `^z+Archived\b`; recovery arm `name_cleaning.py:56`, `^z+Archived\s*-\s*`) contributes NOTHING, because `zArchived`/`zzArchived` is one run beginning lowercase and the run rule yields no token from it; that is not a reading chosen for convenience, since all five real specimens this repository commits for the branch spell it exactly that way with no exception (P15), so `Archived` is NOT a member and putting it in would plant an unexercisable literal in a frozen set — round 4's defect authored by a fold instead of by a builder. `unknown_contact` (`name_validation.py:113`, `unknown\s+contact` under `re.IGNORECASE`; recovery arm `name_cleaning.py:57`, `\s+unknown\s+contact\b`) contributes nothing FROM THE CODE either, both regexes spelling the literal lowercase — but it is the one branch whose answer THIS REPOSITORY'S COMMITTED SPECIMENS leave open, because `IGNORECASE` hands the letter-case to the live vault and this repository commits BOTH forms: the lowercase suffix form the branch's own "WhatsApp scanner artifact" comment describes (`tests/test_name_validation.py:248`, `:254`; `tests/test_name_cleaning.py:135`, `:140`) and a capitalized standalone form (`tests/test_name_gate.py:96`; `tests/test_lint_vault_fix_gate.py:58`; and the branch's own display `specimen=` field at `name_validation.py:274`). THE FLAG ITSELF IS NOT WHAT MAKES THAT CELL SPECIAL, AND SAYING SO KEEPS THIS SENTENCE HONEST: `re.IGNORECASE` is carried by EIGHT of the sixteen regexes (P17 — all five of `name_cleaning.py`'s and `name_validation.py`'s `:82`, `:110`, `:113`; `:74` does not carry it), so the code pins the live casing of `Me`/`My`/`Dave` no more tightly than `unknown contact`'s. What separates them is the CORPUS: every committed specimen of the three prefix branches spells them canonically with no `ME`/`DAVE` variant anywhere in the tree (P16), while `unknown_contact` is committed both ways. The reconciliation instruction below is written general for exactly that reason and needs no widening — if the census measures a live `ME - X` form, it is absorbed at the same one-time edit. THAT ONE RESIDUAL DEGREE OF FREEDOM IS CLOSED BY RECONCILIATION RATHER THAN BY A GUESS: `CONNECTIVE_SET` therefore carries the SAME ONE-TIME PRE-ORIGINATION RECONCILIATION INSTRUCTION AC-3's CLASS FLOOR CARRIES FOR ITS HAND-LISTED HALF (the branch half of that floor needs none, being read from the package at test time; this set needs one for the same reason those six shape classes do — the regexes declare patterns, not token lists, so there is no declaration to read) — before Dave signs, this literal set is reconciled ONCE against the census's measured character profiles, so that if the census measures the live `unknown_contact` form as capitalized then `Unknown` and `Contact` are added HERE, in this criterion, and if it measures the lowercase suffix form they are not; the same reconciliation runs for any other furniture class whose measured profile would put a capitalized non-name run into an identity position. AFTER THAT ONE EDIT THE SET IS FROZEN EXACTLY AS IT IS NOW — asserted equal to the literal written in this criterion, unable to grow without an AC change — so the safety property is untouched, and the instruction adds NO obligation over members the builder does not author, because the set still carries no non-vacuity clause of any kind. THE CHEAPER ALTERNATIVE IS NAMED AND REJECTED so a builder does not reach for it: authoring the specimen in the lowercase form whatever the census measured would hold the set at three members for free, but it destroys the character profile the specimen exists to carry, which is the same argument that keeps the "lowercase it for green" dodge out of AC-2's declared oracle and AC-3's declared verdict), and `PROSE_ALLOWLIST` (the ordinary English of the note bodies plus this module's own identifiers, docstring and comment vocabulary). THE EXTRACTOR IS STATED ONCE AND ITS "RUN" IS PINNED TO ONE READING, BECAUSE TWO READINGS OF IT RETURN DIFFERENT ANSWERS ON THE SAME BYTES AND THE DIFFERENCE DECIDES A FROZEN SET'S OWN MEMBERSHIP: decode every byte in reach with `errors="replace"`; a RUN is a MAXIMAL contiguous span of characters drawn from the class {Unicode letters, combining marks, `'`, `-`} — maximal meaning the span is bounded only by a character OUTSIDE that class (whitespace, a digit, any other punctuation, or the end of input) and NEVER restarted at an internal capital, so there is no camelCase splitting; a run is EXTRACTED as a token iff its FIRST character is an uppercase or non-ASCII letter; and an extracted run has leading and trailing `'` and `-` trimmed before it is compared against any set. FOUR WORKED CONSEQUENCES, WRITTEN OUT SO THE RULE IS CHECKABLE RATHER THAN INTERPRETABLE: `McDonald` is ONE token `McDonald`, never `Mc` plus `Donald`; `d'Angelo` is ONE run beginning with the lowercase `d` and therefore yields NO token (the extractor-domain residue already named in `why:`, not a new hole); `Zeta-9` yields `Zeta` (the run is `Zeta-`, trimmed); and — the consequence that settles `CONNECTIVE_SET`'s membership above — `zArchived` and `zzArchived` are each ONE run beginning with the lowercase `z` and yield NO TOKEN AT ALL. The maximal reading is chosen over the capital-restarting one for two stated reasons rather than by default: it is the reading that every real specimen this repository has ever committed for the `archive_prefix` branch is consistent with, all five of them spelling the prefix with nothing between the `z` and the capital (P15), and it is the reading that gives an ordinary hyphenated or Mc-prefixed surname the one answer a name needs. It is applied to two DISJOINT POSITION SETS with different rules. ONE ADMISSION IS DERIVED FROM THE PACKAGE RATHER THAN DECLARED HERE: an identity-position token whose `str.lower()` is a member of `name_cleaning._GENERIC_ORG_SUFFIXES` (`name_cleaning.py:58` — exactly `support`, `ltd`, `inc`, `corp`, `group`, `team`, `limited`, `llc`) is admissible with no `NAME_POOL` membership and no census row. THE COMPARISON OPERATION IS NAMED RATHER THAN DESCRIBED: the test lowercases with `str.lower()`, which is what the package itself does at `:148`, `:185` and `:191` — an earlier draft said "casefolded", which the package nowhere does; the eight members are ASCII so `lower` and `casefold` agree on them, but the corpus deliberately carries non-ASCII specimens and the criterion should name the operation its own test performs. It is READ from the package rather than written into `fixture_vault.py` precisely so a builder looking for the cheapest green cannot pad it, and it exists because the identity-position list below now reaches `Person.company` and `Book.publisher`: a specimen written `Voxleaf Ltd` would otherwise oblige the conductor to certify that `Ltd` occurs zero times in a vault of 2,159 company notes, which is not a claim anyone can honestly make, and none of the eight members can hide a person. **IDENTITY POSITIONS — ENUMERATED FIELD BY FIELD AGAINST `models.py`, NEVER NAMED BY CATEGORY, AND THE ENUMERATION IS ITS OWN RULE'S OUTPUT.** The rule is stated in THREE CLAUSES so a ninth entity type or a new field is CLASSIFIED rather than missed — and stated in three rather than one because a single "iff its value names a PERSON or an ORGANISATION" did not generate the list written under it in either direction, which is a criterion that is buildable two ways by its own reconciliation instruction. **CLAUSE 1 — NAMING.** A declared field is an identity position iff its VALUE IS a person's or an organisation's name: the whole scalar, or each element of the list, being such a name or a wikilink to a note that holds one. It is deliberately "IS a name", not "COULD CONTAIN one": the second reading sweeps every free-text field into the pool and obliges the conductor to certify ordinary English words with zero-hit live-vault rows, which is finding 1's unsatisfiable-obligation shape rebuilt on purpose. **CLAUSE 2 — DECLARED OVER-CONSTRAINT, so reconciliation does not delete it.** Plus the four entity `title` fields — `Book.title` (`:160`), `Watch.title` (`:193`), `Explore.title` (`:222`), `Exploration.title` (`:295`). A book, a film, a link and a living document are not people or organisations, so clause 1 does NOT reach them; they are in the list ON PURPOSE and this clause is the authority a later reconciliation reads before removing them. The reason: a title is the human-written display string of a note whose live original the corpus author is copying a character profile from, so transcribing a real one is the same slip as transcribing a real name, and it costs nothing extra — `## Write Targets` already requires every identity-position token in a specimen to be a constructed string, naming "a naturally-worded meeting title" as the example. **CLAUSE 3 — UNDECLARED KEYS, BY DEFAULT AND WITH NO OPT-OUT.** `BaseEntity` sets `model_config = ConfigDict(extra="allow", ...)` (`models.py:31-32`), so a corpus note may carry frontmatter keys no model declares — a `manager:` or `introduced_by:` on a forward-compatibility or schema-drift specimen — and clauses 1 and 2, being enumerations over DECLARED fields, cannot reach them at all. Any manifest-declared value for a key the note's model class does not declare is therefore an IDENTITY POSITION, full stop: there is no manifest flag that marks one prose, because a builder-settable exemption is the escape hatch this criterion has now been folded for twice. The default is satisfiable by construction rather than being an obligation over a set nobody authors — the corpus author chooses both which undeclared keys exist and what they hold, and the only cost of the default is that those values must be short constructed tokens rather than sentences. **THE CURRENT ANSWER**, reconciled field by field against every member of `TYPE_TO_MODEL` (the full pass is P14): every corpus filename stem (with the declared filename grammar's `@` sigil and `Meeting <date> - ` prefix stripped), plus the manifest's declared values for `Person.name` (`models.py:79`), `Person.aliases` (`:80`), `Person.company` (`:84`), `Company.name` (`:128`), `Book.title` (`:160`), `Book.author` (`:161`), `Book.publisher` (`:166`), `Watch.title` (`:193`), `Watch.director` (`:195`), `Watch.streaming_service` (`:199`), `Watch.recommended_by` (`:200`), `Explore.title` (`:222`), `Explore.source` (`:224` — "where you found it / who mentioned it"), `GiftIdea.for_person` (`:242`, frontmatter alias `for`), `GiftIdea.source` (`:243`), `Meeting.attendees` (`:261`), `Exploration.title` (`:295`) and `Exploration.related` (`:299`), plus every undeclared key's declared value under clause 3. **FOUR EXCLUSIONS, EACH ARGUED, AND ONE CORRECTION.** `Person.title` (`:85`) is EXCLUDED: it is a JOB title, it names nobody, and forcing `Director` into a pool that owes a zero-hit live-vault row would manufacture an unsatisfiable obligation on purpose — `Person.company` (`:84`) and `Person.title` (`:85`) are different fields and only the first carries identity. `Meeting.topics` (`:262`) is EXCLUDED as free prose for the same reason. `Exploration.origin` (`:300`, glossed "What sparked this - problem, article, conversation" at `:281`) is EXCLUDED on the same argument and it is the closest call in the list: it is a SENTENCE rather than a name, so clause 1 does not reach it and clause 1's "could contain" reading is the one that breaks the criterion — the residue is stated plainly below rather than closed by a fifth clause. `Exploration.graduated_to` (`:301`, glossed `[[Project]]` at `:282`) is EXCLUDED: a project is neither a person nor an organisation, and a constructed project name like `Q3 Migration` would put ordinary words into a pool owing zero-hit rows — finding 1's shape again. And `Meeting` DECLARES NO `title` FIELD AT ALL (`:259-263` — `date`, `attendees`, `topics`, `meeting_id`; `BaseEntity` adds only `type` and `tags`, `:39-40`), so the phrase this list replaced named a field the schema does not have; a meeting's title is not lost, because it lives only in the filename and the stem scan already reaches it. The list is reconciled against the schema BY APPLYING ALL THREE CLAUSES, BEFORE origination, exactly as AC-3's CLASS FLOOR reconciles its hand-listed half, so a field added to a model costs one edit here rather than a re-sign. IT IS HAND-LISTED RATHER THAN DERIVED FOR A STATED REASON AND NOT BY OVERSIGHT: `models.py` declares the FIELDS but nothing in it declares which of them hold a person's or an organisation's name, so unlike AC-2's `TYPE_TO_MODEL`, AC-3's `branch_id`s and AC-4's repository set there is no population to read — the classification is judgment, which is why it sits with a stated rule, a recorded field-by-field pass (P14) and a reconciliation instruction instead of a runtime read. Every token extracted from an identity position MUST be in `NAME_POOL ∪ CONNECTIVE_SET` or be an admitted org suffix. `PROSE_ALLOWLIST` IS NOT A TERM IN THIS ASSERTION and is structurally unreachable from it; the test additionally asserts `PROSE_ALLOWLIST` is DISJOINT from the identity-position token set, so no token can hold both roles and adding a surname to the allowlist buys nothing whatsoever for a `name:` value, an `aliases` entry, a title field or a filename stem. **FREE-PROSE POSITIONS** — everything else in reach: note bodies, non-identity frontmatter values, and `fixture_vault.py`'s own source. Tokens here must be in `NAME_POOL ∪ CONNECTIVE_SET ∪ PROSE_ALLOWLIST`. **NON-VACUITY, `NAME_POOL` ONLY** — every `NAME_POOL` entry occurs as an extracted token in at least one IDENTITY position; "somewhere in the reach" is deliberately NOT the bar, because a pool padded through a note body would satisfy it. It is scoped to `NAME_POOL` because `NAME_POOL` is the one declared set THE BUILDER AUTHORS, so it is satisfiable by construction — declare only what the corpus uses. **`CONNECTIVE_SET` CARRIES NO NON-VACUITY OBLIGATION, AND ITS ABSENCE IS A FIX RATHER THAN A RELAXATION.** A mandatory occurrence clause over a set the builder does NOT author is the defect generator this criterion has now bred three times (`to`/`->`/`→`, then `Re`/`Fwd`/`Fw`): every such set has produced at least one member the corpus cannot exercise, and each earlier fold pruned the member and kept the clause. Nothing is lost by dropping it, because exercising the furniture was never the wall — what stops `CONNECTIVE_SET` becoming a second escape hatch is that it is frozen by literal enumeration IN this criterion and asserted equal to it, and coverage of whatever connective the live vault actually produces is already guaranteed by AC-3(i), which requires a specimen for every MEASURED census class and, correctly, can never demand one for a class the vault does not have. The single corpus member that is not valid UTF-8 is exempt from the token scan and instead has its COMPLETE bytes declared in the manifest as a LOWERCASE hex literal and asserted byte-equal — reviewed rather than silently skipped past the wall, and lowercase so the literal yields no extracted token and can never itself become a reason to grow the allowlist. (c) POOL PROVENANCE — SCOPED TO `NAME_POOL` ALONE, AND A CONTAINMENT RATHER THAN AN EQUALITY. `docs/vault-shape-census.md` carries a pool table whose rows each give a certified token, the shape class it is constructed to carry, and the conductor's live-vault non-occurrence scan for it (the command run and its verbatim stdout, showing `0` hits as a name token anywhere in the vault — `## Write Targets` requires that command to emit a COUNT, so an honest zero result records verbatim as `0` rather than as nothing). The test asserts that `NAME_POOL` ⊆ the census's pool table — ONE DIRECTION, and the direction matters — that every row carries a non-empty command and a non-empty stdout, and that the table's token set is DISJOINT from `CONNECTIVE_SET`. AND IT ASSERTS CENSUS FIXITY FIRST, BEFORE IT TRUSTS ANY ROW OF THAT TABLE: `sha256` over `docs/vault-shape-census.md`'s bytes equals the `CENSUS_DIGEST` literal declared in AC-3(iv) and frozen by the same signature that freezes this criterion. This leg is asserted HERE as well as in AC-3 and not merely inherited from it, because each criterion's `check:` is its own test function and an unguarded AC-5 is the worse of the two exposures: the pool table is where this criterion's entire ground truth lives, the suite cannot re-derive a single one of its non-occurrence claims, and `docs/**` is builder-writable in full (`pipeline-runners.yaml:34-38`, P7), so without the fixity assertion a builder who wants a convenient, easy-to-spell pool token — one that may collide with a real name in a vault the builder cannot see and has no way to check — adds a row asserting a scan that was never run, with fabricated command and stdout text satisfying every other check this leg makes (non-empty command, non-empty stdout, containment, disjointness), and `## Intent`'s sentence about Dave's contacts' real names has no machine check standing behind it at all. THE VALUE'S LOCATION IS THE WALL, not the digest: it is read from the signed AC-3 fence in `docs/vault-fixtures.md`, never from a constant in `tests/fixture_vault.py`, because a constant the build owns is updated in the same commit that edits the file it digests. The residue is stated rather than papered over: a build that deletes the assertion outright is the ordinary "did not implement the criterion" exposure every AC here carries — caught by the battery and by code review — and is not a bypass of this leg, whose subject is the expected value's home. THE DIRECTION IS NOT A WEAKENING AND THE REASON IS AN ORDERING FACT ABOUT THIS PIPELINE, NOT A PREFERENCE: the census is a PRECONDITION that lands in HEAD before Dave signs these criteria and long before any corpus exists, while `NAME_POOL` is declared in-cage by a build that has not happened, so a both-directions equality would ask the earlier artifact to predict the later one's exact token set — and a census that certifies one token the build does not end up using would go RED with no in-cage remedy except inventing a note to consume it. Closure is not weakened by a byte: a token with no row still cannot enter an identity position, which is the entire property, and a certified-but-unused row is not a leak because it carries its own scan. It also removes this item's dominant recurring cost — under an equality every corpus edit is a paired edit across the cage boundary, and under a containment it is not. The leg is the same read-the-artifact-and-assert-its-shape move AC-3 makes: hermetic, no subprocess and no vault read. The connectives are exempt from provenance because a non-occurrence claim about them is unmakeable, not merely tedious: `Me`, `My` and `Dave` are the live stored-name prefix forms this vault actually produces — `name_validation.py:238-248` carries `specimen="Me to David Field"` on its `me_to_prefix` Tier-1 branch, `:226-236` carries `Dave - Thomas Gatten` on `calendar_prefix`, and `name_cleaning.py:46`/`:54`/`:55` strip exactly `(Dave|Me|My)` — so a zero-hit row for any of them would be a false statement inside the artifact whose whole job is to be the trustworthy ledger. The exemption's ground is the code's own vocabulary and NOT a guarantee about the census's counts: an earlier draft justified it by saying AC-3 requires the census to report `Me to ` prefixes with a non-zero count, which AC-3 no longer promises now that any class may be ruled ABSENT. It does not need to promise it — `Dave|Me|My` being live prefix vocabulary in this package is a fact about `name_cleaning.py`, readable without the census, and it is what makes the non-occurrence claim unmakeable whatever the census measures. (d) THE PROPERTY IS NOT PAID FOR — every reserved phone in the corpus still normalizes through `normalize_phone` to a stable digits-only value (`phone_normalization.py:39-55` splits off the WhatsApp JID suffix and then strips every non-digit, so `+44 7700 900123` yields `447700900123`; the package emits E.164 nowhere and none is asserted here), and `phones_match` (`:58-90`) still matches that value against the reserved number's `0`-prefixed and `+44`-prefixed variants, so the reservation does not cost the shape the fixture exists to exercise. (e) HERMETIC — materialization writes only underneath the caller's `dest`, and the corpus contains no absolute filesystem path: no occurrence of `/Users/`, and no live vault path in any note or in the manifest.
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

**Not a diagnosis and marked as such.** "A frozen corpus would have caught bug X" is nowhere in this
spec, because no such bug is on the record. The item's warrant is D-1 through D-7, which are facts
about absence and about mechanism, not about a breakage anyone has observed. That also decides
Verification's incident-replay question — see `## Verification`.

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
   note, carrying that row's character profile.
3. **Skip coverage.** Every member of `SKIP_REASONS` has at least one specimen, and the two untyped
   classes are planted TWICE — once as `@<Name>.md`, once as `Meeting <date> - <Title>.md` — which
   is AC-4(b)'s discriminator (§5.4).
4. **The one non-UTF-8 member.** Exactly one file is deliberately not valid UTF-8. That is the only
   spelling of the `unreadable` class that survives git: `parse_markdown_file` reads with
   `read_text(encoding="utf-8")` unwrapped (`parser.py:238`), so invalid bytes raise
   `UnicodeDecodeError`, which is neither `FrontmatterParseError` nor `SchemaDriftError` and falls
   to `_skip_reason`'s third arm (`base.py:47`). A `chmod`-based specimen is NOT reached for; git
   does not carry a mode that makes a file unreadable to its owner.
5. **The collision.** At least three distinct filenames share one stored `name:` — the same-name
   collision class. Whether that is one class or two with stem/name divergence is the CENSUS's
   ruling, not the builder's (`## Approach`).
6. **Size.** ~50 notes. The number is an approximation and no criterion asserts it; rules 1-5 are
   what the corpus must satisfy, and if the census measures more classes than fifty notes can carry
   comfortably, the corpus grows and nothing in this spec moves.

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
    snapshot: 2026-09-08
    vault_notes_person: 1147
    vault_notes_company: 2159
    ```
```

`census-meta` keys beyond `snapshot` are free-form `vault_notes_<type>` counts; the reader requires
`snapshot` and ignores the rest, so the conductor can record per-type totals without a paired spec
edit.

**These three fences are the artifact's whole machine surface.** Everything else in the file — the
`lint_vault` auto-fix shapes the precondition fence asks for, the ONE-class-or-TWO ruling, the
postal-address ruling — is prose the conductor writes and a human reads. Nothing in the suite parses
it, and nothing in the suite may start to: the digest (AC-3(iv)) is what makes the prose trustworthy,
not a parser.

### §3. Data model — the manifest module `tests/fixture_vault.py`

Three things and no test logic. Imports: `hashlib`, `unicodedata`, `dataclasses`, `pathlib`,
`typing`. **It must not name `ast`** (§11, W-1) and must contain no URL and no absolute path.

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
    shape_classes: tuple                # census class ids this note is the specimen for
    verdict: Optional[Verdict]
    roundtrip_representative: bool
    raw_bytes_hex: Optional[str]        # ONLY the non-UTF-8 member; lowercase hex, complete bytes

NOTES: dict[str, NoteSpec]              # keyed by filename, corpus-relative, no directory part
SKIPS: dict[str, dict[str, str]]        # {repository type_name: {filename: reason}}
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
depends on it; a `SKIP_REASONS` nothing consumes can. So `tests/derivations.py` gains ONE scan —
and it lands there and nowhere else because `ast` is single-homed to that module by a standing set
equality (§11, W-1):

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
`tests/test_loud_fail_harness.py`'s `six` dict (`:79-88`), which that module's own docstring
declares a REQUIRED SUBSET rather than a cardinality bound (`:18-20`) — checked, not assumed.

AC-4 then asserts `skip_reason_return_values(base.py) == SKIP_REASONS`. **Equality, never
containment** — that is what makes the scan's own silent under-read report RED.

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

#### §6.3 Pool provenance (leg c)

`NAME_POOL ⊆ {row.token for row in census pool rows}` — a CONTAINMENT, one direction. Every pool row
carries a non-empty `command` and non-empty `stdout`. The pool table's token set is DISJOINT from
`CONNECTIVE_SET`. And census fixity is asserted here too, before any row is trusted (§5.5).

#### §6.4 Reserved ranges (leg a), and the one thing the criterion's field list makes ambiguous

The scan is over ALL bytes in reach rather than a field list, so it needs no enumeration to be
total:

- **Email-shaped:** `[\w.+-]+@[\w.-]+\.\w+`. Its domain must be `example.com`, `example.net` or
  `example.org`, or carry a `.test` / `.invalid` / `.example` TLD (RFC 2606 / RFC 6761).
- **URL-shaped:** `https?://[^\s"'<>)]+`. Its HOST must satisfy the same reserved rule. That is the
  concrete reading of AC-5(a)'s "a declared placeholder form": the declared form IS "host under a
  reserved name", which reuses one rule instead of minting a second and cannot be padded.
- **Phone-shaped:** a maximal contiguous span over `[0-9+()\-. ]` whose digit count is ≥ 9. Its
  `normalize_phone` value (`phone_normalization.py:39-55`) must match `^44770090\d{4}$` (the UK
  Ofcom drama range, `+44 7700 900000-900999`) or `^1?\d{3}55501\d{2}$` (NANP `555-01xx`).

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

**Leg (d), the cost check.** For every reserved phone in the corpus, `normalize_phone` still yields
the digits-only value (`+44 7700 900123` → `447700900123`; the package emits E.164 nowhere and none
is asserted), and `phones_match` (`:58-90`) still matches it against the number's `0`-prefixed and
`+44`-prefixed variants. **Leg (e), hermeticity.** `materialize_vault` writes only underneath the
caller's `dest`; no file in reach contains `/Users/` or any absolute filesystem path.

### §7. Integration points

| Surface | Today | After | Who reads it |
|---|---|---|---|
| `obsidian_schemas/repositories/base.py` | three bare return literals, no declaration (D-5) | `SKIP_REASONS` + three named constants; `_skip_reason` returns them by name | AC-4; `tests/test_loud_fail_load.py:187-188` |
| `tests/derivations.py` | 14+ shared scans, `ast` single-homed (`:14-17`, `:24`) | one more scan, `skip_reason_return_values` | AC-4 |
| `tests/fixtures/vault/` | does not exist (D-1) | the corpus | `tests/fixture_vault.py` only |
| `tests/fixture_vault.py` | does not exist | manifest + digest + materializer | the five checks, and every later test that wants a vault |
| `tests/test_fixture_vault.py` | does not exist | the five checks + three batteries | the conveyor's AC battery, and the floor |
| `tests/test_parser.py`, `tests/test_writer.py`, `tests/test_repositories.py` | nine private vault helpers over thirteen files (D-1) | three of them gain a corpus-backed top-level test; two lose an inline heredoc | the floor |

**Nothing outside this repository changes.** `pyproject.toml:38-39` packages `obsidian_schemas`
only, so `tests/fixture_vault.py` is not importable by HAL9000, Exocortex or orchestrator even after
this ships (P8) — which is D6's measured deferral, not a regression. The one package change is
purely additive: a new module-level name, no signature change, no behaviour change, so the three
consumers' `-e` installs pick up a constant nobody yet calls.

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

**§9.5 The extractor's domain, and the two places the machine stops.** An identity value written
entirely in lowercase yields no token and is outside the wall; a real name written into
`Exploration.origin`, `Meeting.topics` or a note body is walled by the free-prose leg and the pool's
one-time human review, not by the closure. Both are named in AC-5's `why:` and neither is closed by
a further clause, deliberately.

### §10. Prerequisites & Assumptions

**P-1 — `docs/vault-shape-census.md` is in git HEAD before the builder is armed.** It is the
declared `kind: precondition`; the WI-156 driver probe tests the path for membership in HEAD (never
its CONTENT) immediately before the spawn and refuses the drive if it is absent. Its content is a
conductor act the cage cannot perform: the suite is hermetic and no caged builder can read the live
vault.

**P-2 — the one-time pre-origination edit has happened, and it is THREE things in one edit.** After
the census lands and BEFORE Dave signs: (a) AC-3(iv)'s `CENSUS_DIGEST` declaration is filled with
the `sha256` of the landed file's bytes; (b) AC-3's SIX hand-listed shape classes are reconciled
against the census's own naming; (c) AC-5(b)'s `CONNECTIVE_SET` is reconciled once against the
census's measured character profiles — if the census measures a capitalized `unknown contact` form,
`Unknown` and `Contact` are added to the literal set in the criterion; if the lowercase suffix form,
they are not. Architect round 10's note 2 rides along: one clause settling whether `_skip_reason`
returning re-spelled literals is legal, which this spec answers by prescribing the by-name form
(§4). **Origination must not proceed while AC-3(iv)'s placeholder stands.** A correction before the
digest is taken is free; a correction after signature costs a D4b re-sign.

**P-3 — atomic landing, checked against the PRE-DRIVE floor.** The census lands ALONE in the live
tree, before the build worktree exists, and the floor must be green at that moment. It is: the only
repo-wide markdown scan excludes `docs` (`tests/test_vault_path_required.py:387`), and the only two
modules that read a named doc name `docs/write-door-bypasses.md`
(`tests/test_ac_interpreter.py:40`) and `docs/company-name-corpus-audit.md`
(`tests/test_company_name_contract.py:855`) — neither is the census. So the census participates in
no bijection or symmetry the pre-drive floor enforces, and a lone precondition commit is safe. The
BUILDER's own changes are a different matter: `SKIP_REASONS`, `skip_reason_return_values` and AC-4's
check are three halves of one invariant and land in ONE commit.

**P-4 — the suite stays hermetic and ~1s.** No network, no live-vault read, no subprocess in any
check. `pipeline-runners.yaml:7-8` makes the floor command the AC battery's own interpreter, and
`seed_deps: [.venv]` (`:18-19`) is what puts it in the worktree.

**P-5 — every `check:` is a top-level zero-argument `def test_*(` that signals failure by RAISING.**
The battery invokes it as `getattr(mod, name)()` with no fixture machinery
(`tests/support.py:1-19`). A check needing a temp directory uses `tests/support.temp_dir()`, not
`tmp_path`. A returned `False` exits 0 and reads as PASS.

**P-6 — each check name resolves to exactly ONE `tests/test_*.py`.** That is the conveyor's
discovery rule and this project asserts it (`tests/test_ac_interpreter.py:76-87`). All five names
live in `tests/test_fixture_vault.py` and appear as a top-level `def` nowhere else — including in
no docstring or comment of another test module.

**P-7 — Python ≥ 3.10 (`pyproject.toml:11`), stdlib only.** `hashlib`, `unicodedata`, `pathlib`,
`dataclasses`. No new dependency.

**P-8 — trust boundary.** The corpus is untrusted-shaped input by design (that is the point) but is
IN-REPO and never crosses a network. The one boundary that matters is the reverse direction: real
personal data crossing INTO permanent git history, which AC-5 makes structurally impossible rather
than intended.

**P-9 — no `## Threat Model` section exists on this document**, so no `kind: required` mitigation is
outstanding and this spec authors no `## Mitigation Folds` section. Checked rather than assumed: the
standing gate rounds are architect ×10, AC red-team ×9 and data-premise ×1, none of them a threat
model. If a threat-modeler runs before `→ ready`, its required mitigations must be folded into
`## Design` and the Implementation Plan and recorded there before the transition.

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
| W-1 | `_check_the_ast_capability_stays_single_homed` (`tests/test_name_gate_wall.py:1136`) → `modules_using_ast` | `python_files_under(PACKAGE_ROOT, TESTS_ROOT)` — GROWS with every file this item adds | set EQUALITY to `{"tests/derivations.py"}`. `tests/fixture_vault.py` and `tests/test_fixture_vault.py` must NOT import or attribute-access `ast`; `skip_reason_return_values` lands in `derivations.py` for exactly this reason (§4) |
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
| W-14 | pytest collection (`pyproject.toml:41-43`) | `testpaths = ["tests"]`, `python_files = ["test_*.py"]` | `tests/fixture_vault.py` is not collected (no `test_` prefix) and `tests/fixtures/vault/*.md` is not collected (not `.py`). No `conftest.py` is added — P2 records its absence as load-bearing |

**Checked and cleared, so the next reader can tell they were checked rather than missed.** The
repo-wide markdown scan (W-8) excludes `docs`, so neither this document nor the census joins it.
There is no `docs/**`-globbing fixture wall in this project (the local convention is the
`CORPUS_COUPLING:` docstring line, `tests/test_company_name_contract.py:15` and
`tests/test_ac_interpreter.py:23`, which §3 and the new test module both carry) — so WI-278's
corpus-coupling rule is discharged by DECLARATION here rather than by a standing sweep, and the
declaration names what each module pins and what property it consumes.

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
AC-3(i) is satisfied by a fifteen-row table as readily as a sixteen-row one.

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
census's bytes EQUALS it. **If any of that is absent, STOP at Task 2 under the Abort Protocol and
hand off to the conductor** — record in the Build Log exactly which fence, key or digit is missing.
Do NOT author or amend a single byte of the census, do NOT fill the digest, and do NOT narrow any
task's assertions to fit the artifact as found: the evidence is a live-vault execution the cage
cannot perform, so anything written there would be fabrication (the D2 rejection, and the WI-024
precedent). The WI-156 driver probe checks only that the path is in HEAD, never its content — this
paragraph is the only thing standing between an incomplete census and a burned build attempt.

- [ ] **Task 1 — Capture the pre-build baseline.** Run the floor command
  (`/Users/davewascha/Workspaces/obsidian-schemas/.venv/bin/python -m pytest
  /Users/davewascha/Workspaces/obsidian-schemas/tests -q`, absolute per CLAUDE.md, adjusted to the
  worktree root) and record in the Build Log: the passing case count, and `git rev-parse HEAD` for
  the seeded worktree. These are informational — no later check asserts either number, and the floor
  invariant is DIRECTIONAL (a later run landing fewer cases without explanation has lost a test
  file).
  **Verify:** both values are in the Build Log before any file is edited.
  verify: baseline — the pre-edit floor case count and the worktree HEAD, recorded in the Build Log; no later check asserts either value, and this item's own tasks move the count.

- [ ] **Task 2 — Declare the skip-reason codomain and BIND it to the function.** In
  `obsidian_schemas/repositories/base.py`, add the three module-level reason constants and the
  `SKIP_REASONS` frozenset exactly as §4 gives, and change `_skip_reason`'s three arms to return
  those names. In `tests/derivations.py`, add `skip_reason_return_values` per §4, reusing `_parse`
  (`:213`), `_iter_functions` (`:217`) and `_own_body_nodes` (`:243`); an unresolvable return raises
  `AssertionError` naming module, function and lineno. Create `tests/test_fixture_vault.py` with its
  module docstring (including its `CORPUS_COUPLING:` line naming `docs/vault-shape-census.md` and
  `docs/vault-fixtures.md` and the properties it consumes from each) and ONE test,
  `test_skip_reason_declaration_binds_to_its_functions_returns`, which (a) asserts
  `skip_reason_return_values(PACKAGE_ROOT / "repositories" / "base.py") == SKIP_REASONS`, (b)
  asserts `SKIP_REASONS` is non-empty and of size exactly 3, and (c) drives PLANTED source through
  the SAME predicate the live assertion calls — never a re-implementation — written under
  `tests/support.temp_dir()`. Shapes that MUST resolve: `return "literal"`; `return NAME` where
  `NAME` is a module-level `str` constant; two arms in one function; an arm inside an `if` and one
  inside a `for`. Shapes that must RAISE rather than be silently dropped: `return name_var` where
  `name_var` is a local; `return f"{x}"`; `return CHOICES[0]`. A near-miss that must NOT contribute:
  a `return` of a string inside a NESTED function of the same name.
  verify: test_skip_reason_declaration_binds_to_its_functions_returns

- [ ] **Task 3 — Author the corpus.** Create `tests/fixtures/vault/` and write the ~50 notes per
  §1.1-§1.4, assembled from the landed census: one note per `TYPE_TO_MODEL` member with exactly one
  `roundtrip_representative` each; one specimen per MEASURED census class carrying that row's
  character profile with CONSTRUCTED identity tokens; one specimen per `SKIP_REASONS` member with
  the two untyped classes planted under BOTH owning globs; exactly one member that is not valid
  UTF-8; at least three filenames sharing one stored `name:`; every email under an RFC 2606 domain,
  every phone in `447700900xxx` or `555-01xx`, every URL host reserved, and the single
  `RESERVED_ISBN`. No note may contain `\w+Repository\(\s*\)` (§11, W-8). Record in the Build Log
  the file count, the per-type and per-census-class tally, and the confirmation that exactly one
  member raises `UnicodeDecodeError` under `read_text(encoding="utf-8")`.
  **Verify:** the tallies are in the Build Log; the corpus's first standing artifact is Task 4's
  digest.
  verify: hand-run — the corpus is inert bytes with no standing check until Task 4 lands the digest and the manifest; the act is an inspection recorded in the Build Log (file count, per-type and per-class tally, and the one-member UTF-8 probe).

- [ ] **Task 4 — Land the manifest module and AC-1.** Create `tests/fixture_vault.py` exactly as §3
  gives — docstring with the `CORPUS_COUPLING:` line, the load-bearing `name_cleaning.py:58`
  dependency note and the digest-regeneration recipe; `CORPUS_ROOT`; `Verdict`; `NoteSpec`; `NOTES`
  filled for every corpus member with HAND-WRITTEN `fields`; `materialize_vault` (§5.1) and
  `corpus_digest` (§5.2). Compute `CORPUS_DIGEST` with the recipe and paste it in. It must not name
  `ast`, must contain no URL and no absolute path. Then add
  `test_fixture_vault_is_frozen_and_materialized_by_byte_copy` to `tests/test_fixture_vault.py`:
  leg (a) recomputes the digest and compares; leg (b) materializes into a fresh
  `tests/support.temp_dir()` and asserts the same relative name set, the same per-file bytes and the
  same digest; leg (c) asserts the corpus holds at least one arrow-connective and one path-hostile
  `name:` specimen NAMED as such in the manifest, that materialization succeeds with them present
  and byte-identical, and — the planted discriminator — that
  `write_markdown_file(<fresh dir>, frontmatter=<that specimen's declared frontmatter>)` raises
  `NameGateRefusal` on exactly those members.
  verify: test_fixture_vault_is_frozen_and_materialized_by_byte_copy

- [ ] **Task 5 — AC-2: the type-registry sweep.** Add
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

- [ ] **Task 6 — AC-3: the census reader and the class floor.** Add the three-fence reader per §2 to
  `tests/test_fixture_vault.py` (LOUD on an unknown key, a missing required key or a `status` outside
  `{MEASURED, ABSENT}`), plus the fence-scoped reader that recovers the `CENSUS_DIGEST` value from
  the AC-3 `criteria` fence of `docs/vault-fixtures.md`, asserting exactly one such declaration
  WITHIN that fence and well-formed 64-character lowercase hex. Add
  `test_every_census_corruption_class_has_a_specimen_with_a_verdict` running assertion (iv) FIRST
  (census fixity), then (i) the both-directions equality over MEASURED rows against the manifest's
  covered classes, (ii) the per-row shape check conditional on status, and (iii) the class floor —
  branch half derived as `{record.branch_id for record in TIER1_BRANCHES + COMPANY_TIER1_BRANCHES}`,
  asserted non-empty and of size exactly 10 and in BOTH directions over branch-keyed rows, plus the
  six hand-listed shape classes. For each floor class, assert the manifest's declared `Verdict`:
  a `NameGateRefusal` carrying the named `.pattern` when the specimen's name is re-introduced through
  a write arm, or `clean_person_name` output equal to the declared string, or a declared successful
  byte-identical load.
  verify: test_every_census_corruption_class_has_a_specimen_with_a_verdict

- [ ] **Task 7 — AC-4: the skip surface, per repository.** Fill `SKIPS`, `LOADABLE` and `RESOLVABLE`
  in the manifest per §3 and §5.4 — `LOADABLE` being the `get_all()` quantity, with the collision
  arithmetic stated in §3 applied. Add
  `test_the_skip_surface_over_the_corpus_equals_its_declared_reasons`: derive the repository set
  from `repositories.__all__` filtered to concrete `BaseRepository` subclasses, assert it non-empty
  and of size exactly 4, instantiate each against a materialized vault and assert `SKIPS`'s key set
  equals `{repo.type_name}`; assert `skip_reason_return_values(...) == SKIP_REASONS` and
  `SKIP_REASONS` non-empty of size 3; assert the union of the four mappings' reasons EQUALS
  `SKIP_REASONS` and that each member has at least one specimen; then legs (a), (b) and (c) of §5.4.
  verify: test_the_skip_surface_over_the_corpus_equals_its_declared_reasons

- [ ] **Task 8 — AC-5: the containment wall.** Add `NAME_POOL`, `CONNECTIVE_SET`, `PROSE_ALLOWLIST`,
  `IDENTITY_FIELDS` and `RESERVED_ISBN` to the manifest, and the extractor of §6.1 to
  `tests/test_fixture_vault.py`. Add `test_no_corpus_note_carries_a_live_identifier` asserting
  census fixity first, then legs (a) through (e) per §6.2-§6.4 over the full reach (every file under
  `tests/fixtures/vault/` plus `tests/fixture_vault.py`): reserved ranges; the position-split name
  closure with `PROSE_ALLOWLIST` asserted DISJOINT from the identity token set and not a term in the
  identity assertion; `CONNECTIVE_SET` asserted equal to the literal in AC-5(b); `NAME_POOL`
  non-vacuity over IDENTITY positions only; `NAME_POOL ⊆` the census pool table with the table
  disjoint from `CONNECTIVE_SET`; the non-UTF-8 member's declared lowercase hex bytes asserted
  byte-equal; `normalize_phone` / `phones_match` still holding over every reserved number; and no
  `/Users/` and no absolute path anywhere in reach.
  verify: test_no_corpus_note_carries_a_live_identifier

- [ ] **Task 9 — Drive the extractor's claimed shapes through the extractor (WI-235).** AC-5's whole
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
  verify: test_the_identity_token_extractor_resolves_its_claimed_shapes

- [ ] **Task 10 — D5's proof set.** Per §9.1: in `tests/test_parser.py` delete
  `TestParseMarkdownFile.test_parse_file` and add top-level
  `test_corpus_person_note_parses_to_its_declared_values`, which materializes the corpus into
  `tests/support.temp_dir()`, parses the declared `person` representative and asserts the manifest's
  declared `fields`. In `tests/test_writer.py` delete `TestRoundtrip.test_roundtrip_preserves_data`
  and add top-level `test_corpus_note_round_trips_through_the_write_door`. In
  `tests/test_repositories.py` ADD top-level `test_corpus_vault_loads_through_every_repository`
  asserting each repository's `LOADABLE` count over a materialized corpus; do NOT touch `temp_vault`.
  verify: test_corpus_person_note_parses_to_its_declared_values test_corpus_note_round_trips_through_the_write_door test_corpus_vault_loads_through_every_repository

- [ ] **Task 11 — Close the skip-reason vocabulary's second home.** In `tests/test_loud_fail_load.py`
  replace the hand-typed three-string set at `:187-188` with `SKIP_REASONS`, imported from
  `obsidian_schemas.repositories.base`. This is the copy §4's own solve-in-one-place argument names,
  and the change is strictly stronger, not merely tidier.
  verify: test_skip_surface_detail_is_bounded

- [ ] **Task 12 — Run every wall's own predicate against the final text, and the floor.** For each
  row of §11 whose universe GROWS with this item's files (W-1, W-2, W-8, W-10, W-14), CALL that
  wall's own shipped predicate on the final bytes rather than reasoning about which shapes match:
  `modules_using_ast(python_files_under(PACKAGE_ROOT, TESTS_ROOT))` must return
  `{"tests/derivations.py"}`; the repo-wide markdown scan must return zero offenders over
  `tests/fixtures/vault/`; each of the six new check names must resolve to exactly one
  `tests/test_*.py`; pytest must collect no corpus file. Add
  `test_wall_membership_is_closed_by_running_each_walls_predicate` recording those runs as standing
  assertions. **Anything the RUN returns that §11 did not name is NAMED in the Build Log and
  SATISFIED — never worked around, and never satisfied by narrowing the wall.** Then run the floor
  command and record the passing case count beside Task 1's baseline; it must be GREEN and the count
  must be higher.
  verify: test_wall_membership_is_closed_by_running_each_walls_predicate

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
   path-hostile members, AC-1(c) RED.
5. Add a fourth arm to `_skip_reason` without a `SKIP_REASONS` member → AC-4 RED at the scan
   equality. Add the member without a corpus specimen → AC-4 RED at the union equality.
6. Edit one byte of `docs/vault-shape-census.md` → AC-3(iv) AND AC-5(c) both RED. Both, not one:
   that is why the leg is asserted twice.
7. Flip a MEASURED census row to `status: ABSENT` with `count: 0` and drop its specimen → RED at
   AC-3(iv) before any row is read, which is the exact forgery round 8 found unguarded.
8. Put a token in a `name:` that is not in `NAME_POOL` → AC-5(b) RED, and adding it to
   `PROSE_ALLOWLIST` does not clear it (the disjointness assertion).

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

**Regression — DERIVED from the edited surfaces, not inherited.** Sweeping the resolved test root for
modules that name each `## Write Targets` path returns, and every one of these must still pass:

- `obsidian_schemas/repositories/base.py` → `tests/test_loud_fail_load.py`,
  `tests/test_loud_fail_parse.py`, `tests/test_name_gate.py`, `tests/test_name_gate_wall.py`,
  `tests/test_vault_path_required.py`, `tests/test_company_name_contract.py`,
  `tests/test_write_routing.py`, `tests/test_repositories.py`, `tests/test_concurrent_access.py`.
- `tests/derivations.py` → the twelve modules that import it:
  `tests/test_write_routing.py`, `tests/test_vault_path_required.py`, `tests/test_name_gate_wall.py`,
  `tests/test_name_gate.py`, `tests/test_loud_fail_write.py`, `tests/test_loud_fail_parse.py`,
  `tests/test_loud_fail_load.py`, `tests/test_loud_fail_harness.py`,
  `tests/test_lint_vault_fix_gate.py`, `tests/test_concurrent_access.py`,
  `tests/test_company_name_contract.py`, `tests/test_address_splitter.py`.
- `tests/test_parser.py`, `tests/test_writer.py`, `tests/test_repositories.py`,
  `tests/test_loud_fail_load.py` → themselves, in full.

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
already declares.

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
- **Not adding a `conftest.py`.** P2 records its absence as load-bearing
  (`tests/derivations.py:9-12`), and `tests/support.py` already supplies the fixture-free equivalents
  a zero-argument check needs.

**Unchanged files — the builder must not touch these.** `obsidian_schemas/models.py`,
`obsidian_schemas/name_validation.py`, `obsidian_schemas/name_cleaning.py`,
`obsidian_schemas/name_gate.py`, `obsidian_schemas/parser.py`, `obsidian_schemas/writer.py`,
`obsidian_schemas/body_sections.py`, `obsidian_schemas/phone_normalization.py`,
`obsidian_schemas/vault_io.py`, `obsidian_schemas/errors.py`, every repository module except
`base.py`, `scripts/lint_vault.py`, `pyproject.toml`, `pipeline-runners.yaml`, `CLAUDE.md`,
`README.md`, `SESSION_LOG.md`, `state/**`, and `docs/vault-shape-census.md` — the last being the
conductor's precondition, which the builder READS and never writes. The tempting "while I'm here"
edits this list exists to stop: widening `_GENERIC_ORG_SUFFIXES` to make an identity token admissible
(§6.2 says why that set is read from the package and not declared), and narrowing a Tier-1 regex to
make a specimen behave.

---

## Risk Analysis

| # | What could go wrong | Likelihood / impact | Mitigation |
|---|---|---|---|
| R1 | **A real person's name enters permanent git history.** The corpus is authored from live-vault shapes; a moment's transcription puts a real surname in a `name:`. | Low / **irreversible** — this package installs `-e` into three repos and its history is permanent. | AC-5(b)'s position-split closure makes it structurally impossible rather than intended: an identity-position token must be in `NAME_POOL`, and `NAME_POOL ⊆` the census's pool table, every row of which carries a conductor-run zero-hit scan. The prose allowlist is unreachable from an identity position and asserted disjoint from it. Residue (all-lowercase values, note bodies, prose fields) is named in §9.5 and covered by the pool table's one-time human review. |
| R2 | **The census is edited by the build to make a check pass.** `docs/**` is builder-writable in full (P7) and the pipeline's only merge-boundary wall over docs is scoped to work-item docs (P19). | Medium / high — it defeats the ledger AC-3 and AC-5 both delegate their entire oracle to. | AC-3(iv): `sha256` over the census's bytes equals a literal in the SIGNED criterion, which the build cannot reach; AC-5(c) asserts it independently rather than inheriting it. Verification's mutation 7 exercises exactly this route. |
| R3 | **The corpus is authored from the existing test literals instead of the census** — the D2 shortcut, which needs no conductor act and is the cheapest thing available. | Medium / high — the corpus certifies only what the last five authors thought of and is structurally blind to the tail, which is the item's whole reason to exist. | AC-3(i)'s both-directions equality against the census's MEASURED rows; the Implementation Plan's abort gate; and the fact that the census must be in HEAD before the builder is armed (P-1). |
| R4 | **The manifest is generated by parsing the corpus**, so AC-2 asserts the parser agrees with itself. | Medium / high — a green suite that has verified nothing. | Stated in §3 as the rule and in AC-2's `why:` as the single most likely shortcut; the reviewer's tell is a `fields` mapping reproducing the parser's own normalisations. Not machine-checkable, and said so rather than claimed otherwise. |
| R5 | **`LOADABLE` is declared as the file count or `load()`'s return**, and AC-4(c) is off by two because of the three-way name collision. | High / low — it fails LOUD at build, costing a round. | §3 states the arithmetic with the three cache-key rules cited, which is exactly the "declared rather than discovered" economy. |
| R6 | **The census lands in a syntax the reader does not parse** — pipe tables against fences, or a `command` containing `\|`. | Was HIGH before this spec / medium impact. | §2 pins the fence grammar and the `## Write Targets` extension says so above the fences, so the conductor and the builder read one specification. |
| R7 | **A later branch, type, repository or skip reason reddens the floor with no in-cage remedy** — a new Tier-1 branch needs a census row, which needs the live vault. | Certain, eventually / low-to-medium | Named in AC-3's `why:`, in §5.3 and in Edge Cases rather than discovered by whoever pays it. It is LESSONS #45's intended friction and is not weakened here. |
| R8 | **The suite stops being ~1s and hermetic.** ~50 notes byte-copied per materializing test, over five AC checks plus three migrated tests. | Low / medium | Byte copy of ~50 small files is microseconds; no check makes a subprocess, network or live-vault call, and P-4 states it. If a later test materializes in a loop, that is the thing to notice — the floor's wall-clock is the instrument. |

**Migration path / rollback.** Everything is additive: a new directory, two new modules, one
frozenset, one scan function, three test additions and two test deletions. Rollback is `git revert`
of one commit, and no consumer, no persisted state and no live vault is touched. There is no shadow
mode and none is needed, because nothing in production reads any of it.

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

**Scanned the rest of the document for what these claims now contradict.** Three places needed
reconciling and all three are reconciled in place rather than left to a reviewer:

- `## Approach` says `fixture_vault.py` holds "three things and no test logic". §3 keeps that: the
  census reader, the extractor and every assertion live in `tests/test_fixture_vault.py`, and the
  manifest module gains only declarations plus the two functions `## Approach` already names.
- `## Approach` fixes the package-side scope at exactly two files. §7 and `## Write Targets` name
  four TEST files beyond the new ones (`test_parser`, `test_writer`, `test_repositories`,
  `test_loud_fail_load`); none is a package file, so the two-file claim is untouched, and D5 already
  authorises the first three. `test_loud_fail_load.py` is the fourth and is Task 11, taken on
  architect round 10's note 1 because it is one line and closes the copy §4's own argument cites.
- AC-3(iv)'s uniqueness read is FENCE-SCOPED, so this spec's several mentions of the
  `CENSUS_DIGEST` declaration — all outside the AC-3 `criteria` fence — cannot turn it RED. Checked
  deliberately, because a file-wide read would have been broken by this section.

**Bar check.** Design cites `file:line` and quotes the code at every integration point; every
population a criterion sweeps is READ from its declaration and every oracle is hand-declared;
`## Verified Diagnosis` grounds seven claims in falsifiable artifacts; Edge Cases covers all ten
categories with `OPEN: None`; every plan task carries a canonical ordinal, a checkbox and a
lowercase `verify:` declaration; `## Write Targets` names every path the build touches and nothing
else, and extends the ideation-authored precondition fence rather than replacing it.

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
