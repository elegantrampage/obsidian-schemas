# Frozen anonymized real-data fixture vault — archived gate rounds

<!-- archive-split:v1 — IMMUTABLE APPEND-ONLY ARCHIVE. Written only by src/archive_split.py at a
completed conveyor transition; appended to, never edited, reordered or rewritten. It
carries no work-item frontmatter by design, so it is invisible to find_work_items and to
find_corrupt_work_item_docs. Living spec: docs/vault-fixtures.md -->

## AC Red-Team

Read order followed per the role contract: `## Intent`, `### Examples of done`, `## Problem /
Motivation` and Exploration Notes, then the draft `## Acceptance Criteria`, then the cited code
(`name_gate.py`, `repositories/base.py`, `writer.py`, `body_sections.py`) insofar as needed to judge
satisfiability. This is a cold-start first pass — no prior AC Red-Team round exists on this item.

### What I attacked and what held

AC-1's byte-copy / digest / planted-discriminator legs: looked for a route where a builder games
"frozen" or dodges the gate via the materializer — none found. Leg (c)'s requirement that
`repo.save()` / `write_markdown_file` / `create_stub` raise `NameGateRefusal` on the planted
discriminator closes the obvious "just use the repository API" shortcut. **Held.**

AC-2's derived sweep and hand-written oracle: tried the sweep-proves-membership-only shape (WI-280 /
WI-185) — closed by leg (b)'s hand-written-never-parser-derived requirement and by deriving the
sweep from `set(TYPE_TO_MODEL)` rather than a maintained list. **Held.**

AC-4's per-repository equality and planted double-ownership discriminators: re-derived the
`_owns(None)` / `_note_skip` rule independently against the four `file_pattern`s (matches the
architect's round-2 verification) and looked for a per-repository build that satisfies the equality
vacuously on an empty corpus slice — leg (b)'s two planted discriminators under each owning glob plus
book's asserted-empty mapping close that. **Held.**

### Findings

**AC-5 — CRITICAL.** AC-5's containment wall scans the corpus for email-shaped, phone-shaped and
profile-URL-shaped tokens and asserts each is inside a reserved range. `## Intent` states plainly
that "None of Dave's contacts' real names, emails or numbers go into this repository" — three named
categories. AC-5 builds a structural, machine-checked wall for two of the three (plus a bonus,
profile URLs) and contains **no check on the third and most sensitive one: names.** Failure scenario:
a census pass (or a build) correctly pseudonymizes a specimen's email under `@example.com` and its
phone into a reserved range, but transcribes the live vault's actual `name:` value verbatim — the
exact field D1's amendment says "is precisely the field whose shape the corpus exists to carry."
AC-1 through AC-5 all pass: the digest is frozen over whatever bytes exist, AC-2's manifest declares
whatever name is present as the "expected" value, AC-3's per-specimen verdicts test refusal/cleaning
behaviour rather than identity, and AC-5's scanner finds no email/phone/URL violation. A real
contact's real name commits to permanent git history — the exact irreversible harm the 07-05 routing
note and AC-5's own `why:` field exist to prevent — with every criterion green. AC-5's `why:` field
explicitly claims the containment rule "holds even if the census specimens were pseudonymized
imperfectly"; that claim is false for the one field the whole census exists to carry shapes for. What
would have to change: extend AC-5 (or add a leg/criterion) with a machine check specific to names —
e.g. a manifest-declared pseudonym-provenance field per specimen, or an assertion that no corpus name
token matches an entry on a reserved/synthetic name list — or, if no structural check is possible for
free-text names, the AC set should say so explicitly and name the actual mitigating control (e.g. a
required human review step tied to a criterion) rather than leaving D4's "reviewable by eye" aside as
an unstated assumption nothing in the criteria enforces.

**AC-3 / `### Examples of done` — MATERIAL.** AC-3's draft class list is: diacritics,
hyphenated/multi-part surnames, RFC 2822 leak forms, arrow-connective descriptors, `Me to ` prefixes,
whitespace damage, stem/name divergence, same-name collision, path-hostile characters. `### Examples
of done` — Dave's own prose picture of the finished thing, read second only to `## Intent` per this
gate's Step 2 — names a specimen that is not on that list: "an address that leaked into a name
field." None of the nine draft classes is that shape (the nearest, RFC 2822 leak forms, is
email-header-shaped text like `Dave -> Thomas Gatten (Adzact)`, not a postal address). AC-3 is
explicit that its list is provisional and "confirmed or corrected by the census," which is the right
place to settle it — but the census's charge in `## Write Targets` names only the
collision-vs-divergence question for the conductor to rule on; it does not tell the census to
specifically look for the address-in-name-field shape Dave asked for by name. A census run that
(correctly, per its own charge) records whatever classes it happens to observe could omit this one,
AC-3 would still pass (its equality is against whatever the census declares, not against Examples of
done), and Dave's own example-of-done specimen silently never ships. What would have to change: name
the address-leaked-into-a-name-field shape explicitly in `## Write Targets`'s census charge, alongside
the collision-vs-divergence question already added there, so it is either confirmed present with a
specimen or the census states affirmatively that it does not occur in the live vault.

```verdict
gate: ac-red-team
verdict: REVISE
date: 2026-09-06
model: claude-sonnet-5
targets: AC-5, AC-3, #intent
prior: none
basis: original
findings: 2/2
note: AC-5's containment wall covers emails/phones/URLs but never names — the one field the census exists to carry shapes for — so a real name can ride through pseudonymized email/phone fields with every AC green; separately AC-3's draft class list has no shape for Examples of done's "address that leaked into a name field" and the census's charge never names one to look for.
```


## AC Red-Team — 2026-09-06 (round 2)

**Recommendation: REVISE — round 1's fold closes the letter of both findings but not their
substance. The mechanism it added to AC-5 is unsatisfiable for a specimen AC-3 itself mandates and
carries an unbounded escape hatch that re-opens the exact leak the fold was written to close; the
mechanism it added to AC-3/`## Write Targets` now makes the two documents assert opposite verdicts
for the same class.**

This is a re-verify of my own round-1 fold (findings on AC-5 and AC-3, both folded into the current
draft). Per the role contract I re-read against the seeded tree rather than trusting the fold's
prose, and independently verified the underlying code claims rather than relying on the intervening
architect round's text.

### What I re-verified and what held

AC-1, AC-2 and AC-4 are untouched by this fold and outside its reach — the fold only added AC-5 legs
(b)/(c), AC-3's tenth class, and two obligations in `## Write Targets`'s census charge. I re-checked
AC-1's byte-copy/digest/discriminator legs and AC-4's per-repository ownership rule against
`repositories/base.py` independently of the architect's round-2/round-3 verification and found no
new issue in either; they hold, unchanged. AC-2's derived sweep and hand-written-oracle requirement
likewise hold.

### Findings

**AC-5 — CRITICAL.** The NAME CLOSURE leg's pool (AC-5(b)) declares `Me`, `to`, `->`, `Re`, `Fwd`
as CONNECTIVE pool members, and the POOL PROVENANCE leg (AC-5(c)) requires the census to record, for
**every** pool token including those, a non-occurrence scan "showing zero hits as a name token
anywhere in the vault." But AC-3's own draft list requires a specimen for the "`Me to ` prefixes"
class, and that class is not hypothetical: I grepped `name_validation.py:241` and confirmed it
carries `specimen="Me to David Field"` as a Tier-1 branch's own documented case — i.e. this exact
shape is a real, previously-observed corruption pattern in the live vault, which is *why* the branch
and the class exist at all. So the honest census entry for `Me` is a **non-zero** count in the very
artifact AC-3's fold now requires the census to produce, not the zero AC-5(c) demands. Concrete
failure scenario: a builder writes the AC-3-mandated `Me to <pseudonym>` specimen, then faces a
criterion with no honest way through — record a truthful non-zero count for `Me` and AC-5(c) is RED
on that token, or fabricate a zero-hit row to pass AC-5(c) and the provenance ledger this leg exists
to make trustworthy now contains a false statement, or drop `Me` from the pool/connective set and
either lose AC-5(b)'s own "every pool entry occurs somewhere in the reach" direction or drop the
class entirely and silently reopen my own round-1 AC-3 finding. Every path either fails a criterion
honestly or corrupts the ledger the criterion exists to protect. What would have to change: split the
flat pool into a NAME sub-pool (subject to AC-5(c)'s zero-hit provenance obligation) and a CONNECTIVE
sub-set (exempt — non-identifying furniture, not subject to a non-occurrence claim), and scope
AC-5(c)'s equality and zero-hit requirement to the NAME sub-pool only.

**AC-5 — CRITICAL.** Independent of the above, the leg's "declared PROSE allowlist of the ordinary
vocabulary the note bodies and YAML keys need" is unbounded, carries no census obligation, and is
checked against the same undifferentiated byte/token scan that also covers `name:` values and
filename stems — the exact positions the leg exists to police. Concrete failure scenario: a build
transcribes the live vault's real surname into a fixture's `name:` field (the scenario my round-1
finding was raised over); AC-5(b)'s closure assertion goes RED; the cheapest available fix under the
criterion as worded is not building the NAME-pool provenance row the fold requires, but adding the
surname to the allowlist, which the text permits with no gate, no census row, and no distinction that
the token sits in an identity field rather than free prose. The reach was also extended to
`tests/fixture_vault.py` itself — a Python module whose class/exception names and cross-reference
prose (`SkippedNote`, `NameGateRefusal`, `UnicodeDecodeError`, `AC-`/`WI-` references) all need a home
in that same allowlist on day one — which normalizes exactly the kind of large, unreviewed,
heterogeneous growth a real name would hide inside. What would have to change: split the scan by
POSITION rather than by an open-ended second bucket — identity-bearing positions (filename stems, and
the manifest's declared values for `name`/`aliases`/title fields) assert against the NAME sub-pool
only with the allowlist unreachable from them; free prose (note bodies, module docstrings/identifiers)
gets the allowlist, declared as a fixed literal constant with no path back into an identity field.

**AC-3 / `## Write Targets` — MATERIAL.** The two documents now assert opposite verdicts for a class
the census rules absent. `## Write Targets`'s fold requires "a class measured at ZERO is a row the
conductor writes, not a row that may be left out," so a class the census correctly rules absent (the
address-in-name-field class, say, if it occurs zero times) still becomes a row in
`docs/vault-shape-census.md`'s class table. AC-3's own text both states "a class in the census with
no specimen is RED" and states the criterion is "RED only when manifest and census disagree, never
for holding nine classes rather than ten... if the address shape is ruled absent too" — i.e. a
ruled-absent class is explicitly declared NOT a failure. A census that obeys `## Write Targets` (and
writes the zero row) hands AC-3 a class with no specimen, which AC-3's own first clause marks RED; a
census that omits the row to keep AC-3 green violates `## Write Targets`'s explicit instruction and
silently reopens the exact omission risk my round-1 AC-3 finding was raised to close. Concrete
failure scenario: the census correctly determines the address-in-name-field class occurs zero times,
writes the required zero row; AC-3's test, applying "a class in the census with no specimen is RED"
literally, goes RED on a correctly-authored, honest census — a false block, or worse, a lesson for the
next builder that quietly dropping the zero row is how to keep the suite green, which reopens the
silent-omission risk this finding series exists to close. What would have to change: give the
census's class table an explicit count/status column, and state in one place that AC-3's
both-directions equality runs over specimen-bearing (count > 0) rows only, while a ruled-absent row
is checked against a separate, weaker shape (count, command, and an affirmative absent ruling — no
specimen required).

```verdict
gate: ac-red-team
verdict: REVISE
date: 2026-09-06
model: claude-sonnet-5
targets: AC-5, AC-3, #write-targets
prior: mixed
basis: folded-material
findings: 3/3
note: Round 1's fold nominally closes both prior findings but the mechanism it added is broken — AC-5(c) demands a zero-hit census row for pool token `Me`, which name_validation.py:241's own specimen shows is a real non-zero corruption pattern AC-3's `Me to ` class must specimen; AC-5(b)'s unbounded, uncensused prose allowlist is reachable from identity fields and lets a real name skip the pool entirely (the original AC-5 leak, reopened); and AC-3 now contradicts `## Write Targets` on whether a census's zero-measured class row is RED.
```


## AC Red-Team — 2026-09-06 (round 3)

**Recommendation: REVISE — architect round 4's diagnosis is independently correct on every arm I checked
against the code, and I am not asking for a fifth fold of the same shape. This is the fourth
consecutive round landing on AC-5's provenance/closure MACHINERY rather than the Intent it exists to
serve, and that pattern is named, not iterated, per this gate's own regress-signature rule.**

Read order followed per the role contract: `## Intent`, `### Examples of done`, `## Problem /
Motivation` and Exploration Notes, then the current draft `## Acceptance Criteria`, then the cited
code, insofar as needed to judge satisfiability independently rather than trust the architect's prose.

### What I re-verified and what held

AC-1, AC-2 and AC-4 are untouched since architect round 2's PROMOTE and my own round-1 pass. I
re-read all three against the current fences and found no new issue in any of them — **held,
unchanged.**

My own round-2 findings (the flat pool's unsatisfiable non-occurrence obligation on `Me`, the
unbounded prose-allowlist bypass, and the AC-3/`## Write Targets` zero-row contradiction) are
**closed** in the current draft, and I verified this myself rather than accepting the architect's
round-4 summary of it: AC-5(b) now declares `NAME_POOL` and `CONNECTIVE_SET` as two separate literal
frozensets with the provenance obligation scoped to `NAME_POOL` alone; the scan is split by POSITION
with `PROSE_ALLOWLIST` asserted unreachable from and disjoint against identity positions; and AC-3 /
`## Write Targets` now carry explicit `count`/`status` columns with the equality scoped to MEASURED
rows and the DRAFT CLASS FLOOR asserting presence at either status. All three routes through my
round-2 scenarios are closed as drafted.

### Findings

I independently re-derived each of architect round 4's four blocking issues against the code myself
(not merely reading their citations) before treating them as material. All four check out.

**AC-5(b) — CRITICAL.** `CONNECTIVE_SET` is frozen at exactly `{"Me", "Re", "Fwd", "Fw"}`, and the
same leg requires every member to be non-vacuous (occur as an extracted token in ≥1 identity
position). I grepped the whole tree for `Fwd`, `Fw` and `Re:` myself: the only hits anywhere are
inside this document, entered as prose in round 3 — nowhere in `obsidian_schemas/` or `tests/` does
any Tier-1 branch, recovery regex, or AC-3 census class produce or expect an `Re:`/`Fwd:`/`Fw:`
prefix. Failure scenario: to discharge non-vacuity the builder must invent identity-position
specimens carrying those prefixes, and those specimens belong to no measured census class — the exact
"a specimen belonging to no measured census class is RED" violation AC-3(i) exists to forbid — or the
set's own non-vacuity clause stays permanently RED. What would have to change: enumerate
`CONNECTIVE_SET` from vocabulary the package's own code actually produces (`Me`, `My`, and whichever
leading label the corpus's own measured arrow/calendar-prefix specimens carry) and tie each member to
a MEASURED census class, so non-vacuity and AC-3(i) agree by construction.

**AC-5(c) — CRITICAL.** The leg asserts `NAME_POOL` and the census's pool table are equal **both
directions**. `docs/vault-shape-census.md` is declared a `kind: precondition` fence in `## Write
Targets`, landing in HEAD "at exploring rather than at ready" — before Dave signs these criteria and
long before any build exists — while `NAME_POOL` is a set "the caged builder" declares, during the
build the census precedes. A both-directions equality asks the pre-build artifact to predict the
exact token set a not-yet-written build will consume. Failure scenario: the census certifies one
token the eventual build does not end up using — a wholly reasonable outcome for an artifact written
before the corpus it describes — and the build goes RED with no in-cage remedy except inventing a
consuming specimen (reproducing the prior finding's shape) or breaking the equality. What would have
to change: make the relation a one-directional containment, `NAME_POOL` ⊆ the census pool table,
keeping non-vacuity, the per-row shape assertion and the `CONNECTIVE_SET` disjointness intact.

**AC-5(b) — MATERIAL.** The identity-position list names `name`, `aliases`, and "the company/meeting
title fields." I read `models.py:79-85` directly: `Person` declares `company: str = ""` at line 84,
distinct from `title: str = ""` at line 85, and a person note's `company:` carries a real
organisation's name — one that is itself a live entity in this vault (2,159 company notes per
`docs/company-name-corpus-audit.md`). `company` is not on the identity-position list, so it is scored
as free prose. Failure scenario: a person specimen keeps a real employer's name in `company:`; the
identity-position scan never reaches it; one `PROSE_ALLOWLIST` entry makes it green with no
`NAME_POOL` provenance row — the exact escape hatch this gate's round-1 and round-2 findings exist to
close, reopened one field over. What would have to change: add each note's declared `company` value
to the identity-position list; leave `Person.title` out, since a job title carries no identity and
forcing it into `NAME_POOL` would manufacture the prior finding's shape on purpose.

**AC-3(ii) / AC-5(c) — MATERIAL.** Both legs require a scan's "verbatim stdout" to be **non-empty**,
including on a zero-result (ABSENT row / zero-hit provenance) scan. A genuine non-occurrence search
that finds nothing writes nothing to stdout — the honest, verbatim capture of "zero hits" is empty by
construction, independent of which tool runs it. Failure scenario: the conductor runs the real,
correctly-specified predicate on a class or a name token that truly does not occur; the honest
verbatim result is empty; recording it verbatim fails the "non-empty stdout" assertion, so the only
routes through are fabricating non-verbatim text in the one artifact whose entire job is to be the
trustworthy ledger, or leaving an honest, correctly-ruled-absent row permanently RED. What would have
to change: require the recorded command to emit a COUNT rather than raw match lines, so a zero result
records verbatim as `0` and the "non-empty stdout" assertion is checked against a command that always
produces something.

### Why this is REVISE and not a fifth round of the same shape

Tracing AC-5 alone: round 1 (mine) found the Intent-level gap — no name check existed at all. Every
round since — round 2 (mine), round 3 (architect), round 4 (architect), and now this round —
has found defects entirely inside the MACHINERY the first fold built to close that gap, not in the
Intent, the approach, or anything outside AC-5's own closure mechanism. Each fold has individually
been presented as closing the mechanism, and the next independent read has found the mechanism still
broken, on a different axis every time: unsatisfiable non-occurrence obligation → pool/allowlist
structure → (now) ungrounded set members, a cross-boundary equality direction, a missing identity
field, and an unsatisfiable stdout assertion. This is this gate's own charter's regress signature —
"each fix creating the surface the next finding lands on" — named here rather than iterated past.

I am not recommending the mechanism be abandoned: architect round 4's fixes are generator-level, not
instance patches (drop or correctly scope non-vacuity, make the pool relation a containment), and if
folded as stated they close the family rather than trading it for a fifth member. But three folds have
each already claimed closure and been wrong on the next independent read, so the sufficiency question
— is a fully structural, machine-checked name-closure wall still the right bar for this criterion, or
does AC-5 fall back to the simpler mitigating control this gate's own round-1 finding named as the
alternative when no structural check is possible ("a required human review step tied to a criterion")
— is one for Dave to rule on before a fifth fold is spent, not one this gate can settle by finding a
fifth set of concrete defects and hoping the next fold is the last. Recording that ruling in this
document, once made, is what lets a later cold-start gate route against it rather than re-litigating
it, per this role's own scope-boundary instruction.

The four findings above stand on their own regardless of that recommendation — the current draft is
not signable as written, independent of whether the next fold takes the structural or the fallback
path.

```verdict
gate: ac-red-team
verdict: REVISE
date: 2026-09-06
model: claude-sonnet-5
targets: AC-5, AC-3, #write-targets
prior: held
basis: folded-material
findings: 4/4
note: Architect round 4's four findings are independently verified against the code (grepped the tree myself: `Fwd`/`Fw`/`Re:` occur nowhere outside this document; confirmed `Person.company` at models.py:84 sits outside AC-5's identity-position list) and are real and blocking; this is also the fourth straight round landing on AC-5's closure machinery rather than the Intent, which is this gate's own regress signature — recommend Dave rule on sufficiency (keep hardening the structural pool/closure wall vs. fall back to a declared human-review control) before a fifth fold is spent chasing the same generator's next member.
```


## AC Red-Team — 2026-09-06 (round 4)

**Recommendation: REVISE — architect round 5's blocking finding is independently correct on every
arm I re-derived against the code myself, and I judge it a finite, closable content gap rather than
a re-run of the closure-machinery regress this gate named at round 3.**

Read order followed per the role contract: `## Intent`, `### Examples of done`, `## Problem /
Motivation` and Exploration Notes, then the current draft `## Acceptance Criteria`, then
`obsidian_schemas/models.py` and `name_cleaning.py` directly, rather than trusting the architect's
citations.

### What I re-verified and what held

My own rounds 1–3 findings (the missing name check, the flat-pool `Me` non-occurrence
contradiction, the unbounded prose-allowlist bypass, the AC-3/`## Write Targets` zero-row
contradiction, `CONNECTIVE_SET`'s ungrounded members, the cross-boundary pool equality direction,
and `Person.company`'s omission) are all **closed** in the current draft — re-checked myself against
the text rather than accepted from the architect's round-4/round-5 summaries: `CONNECTIVE_SET` is
`{"Me", "My", "Dave"}` with no non-vacuity clause, AC-5(c) is a one-directional containment
(`NAME_POOL` ⊆ the census pool table), `Person.company` (`models.py:84`) is on the identity-position
list, and `## Write Targets` requires every recorded scan command to emit a count. AC-1, AC-2, AC-3
and AC-4 are untouched since my round-3 pass and I re-read all four against the current fences —
**held, unchanged**, no new issue found in any of them.

### Findings

**AC-5(b) — CRITICAL.** I read `models.py` field by field myself, independent of the architect's
round-5 table, before comparing against AC-5(b)'s enumerated identity-position list. The stated
generating rule is "a field is an identity position iff its value names a PERSON or an
ORGANISATION." The enumerated list does not match that rule's output, and the gap that costs
something is an omission on the one entity type this item exists to stop being invisible:
`Exploration.related` (`models.py:299`) is a `List[str]` whose own docstring at `:280` glosses it as
`[[Other Exploration]], [[Person]], etc.` — a frontmatter field the model itself documents as
sometimes holding a wikilink to a person — and it is not on AC-5(b)'s list. Concrete failure
scenario: AC-2's sweep is derived from `set(TYPE_TO_MODEL)` (`models.py:309-318`), `exploration` is
one of its 8 members, and `## Problem / Motivation` P4 already establishes that `exploration` has
**zero** test references anywhere in the tree today — so this corpus is guaranteed to contain the
first `exploration` fixture note anyone has ever had to author, hand-written from the live shape
rather than copied from an existing test. If that note's `related:` list is written from a live
`Exploration` note's actual content, the real person name inside it lands in a field AC-5(b) scores
as free prose; the cheapest green under the criterion as worded is one `PROSE_ALLOWLIST` entry, with
no `NAME_POOL` membership and no census provenance row — the exact escape hatch this gate's rounds 1
and 2 and the architect's rounds 3 and 4 were each raised to close, open again one field over on the
one type nobody has ever exercised.

Two further fields the rule does not decide, and the fact that they are undecided is itself the
defect (a criterion whose own stated rule does not determine its own enumerated answer is buildable
two ways — the WI-144 shape): `Watch.streaming_service` (`:199`) names an organisation exactly as
`Book.publisher` (`:166`) does, and `publisher` is listed while `streaming_service` is not, with no
argued exclusion for either the way `Person.title` and `Meeting.topics` carry one. `GiftIdea.source`
(`:243`) is the unglossed sibling of `Explore.source` (`:224`, glossed "where you found it / who
mentioned it" and listed); a gift-idea's `source:` plausibly names whoever suggested it, and nothing
in AC-5(b) rules on it either way. And I confirmed `model_config = ConfigDict(extra="allow", ...)`
myself at `models.py:31-32`: any undeclared frontmatter key on a schema-drift specimen — a `manager:`
or `introduced_by:` value, say — is a manifest-declared value the current wording scores as free
prose by construction, with no rule in AC-5(b) that reaches it at all.

Separately, and in the opposite direction: the list includes `Book.title` (`:160`), `Watch.title`
(`:193`), `Explore.title` (`:222`) and `Exploration.title` (`:295`) as identity positions, and none of
the four names a person or an organisation under the rule as stated — a film, a book, a link and a
living document's title are not people or organisations. AC-5(b) itself instructs that the list is
"reconciled against the schema BEFORE origination," i.e. a later reader is meant to re-derive it from
the rule; applying the rule as written would delete these four and add the omissions above, so the
criterion's own reconciliation instruction produces a different list than the one currently written
down.

What would have to change: add `Exploration.related` to the identity-position list; rule explicitly
on `Watch.streaming_service` and `GiftIdea.source` (list them, or give each the one-line exclusion
argument already used for `Person.title`/`Meeting.topics`); state how a manifest-declared value for
an `extra="allow"` key is classified; and reconcile the rule with the four title fields — either widen
the rule's wording to cover a free-text field a real specimen could carry a name in, or state plainly
that the four titles are a deliberate, argued over-constraint so the pre-origination reconciliation
does not delete them on the rule's own authority.

### Why this is REVISE and not the regress signature this gate named at round 3

Round 3 flagged four consecutive rounds landing on AC-5's *closure machinery* — the pool/connective
structure, the provenance direction, the non-vacuity obligation — as this gate's own regress
signature, and asked Dave to rule on sufficiency before a fifth fold of that shape. I checked whether
this finding is a fifth instance of that same family before writing it up: it is not. Nothing here
touches `NAME_POOL`, `CONNECTIVE_SET`, `PROSE_ALLOWLIST` or the pool-table relation — the machinery
architect round 4 rebuilt is intact and I found no defect in it. This finding is about the
**enumerated content** of one field-by-field list against its own stated rule, over a fixed,
enumerable surface (every field of every `TYPE_TO_MODEL` member) — the kind of gap that is exhausted
once every field has actually been read, not one that regenerates itself the way a mandatory
obligation over a builder-unauthored set did. I independently re-derived the architect's full
reconciliation table against `models.py` myself, field by field, rather than trusting its citations,
and found it complete and correctly classified against the stated rule for every field of all eight
types — so folding the concrete fix above should close this criterion rather than open a seventh
round on the same shape. If a future round finds another field the rule does not decide, that would
be the signal this gate's round-3 concern still applies; today's finding is not that signal.

```verdict
gate: ac-red-team
verdict: REVISE
date: 2026-09-06
model: claude-sonnet-5
targets: AC-5
prior: held
basis: folded-material
findings: 1/1
note: Independently re-derived (read models.py field by field myself before comparing): AC-5(b)'s identity-position list is not its stated rule's output in either direction — it omits Exploration.related (models.py:299, docstring :280 names [[Person]]) on the one type AC-2's own sweep guarantees a hand-authored, never-before-tested fixture for, leaves Watch.streaming_service, GiftIdea.source and extra="allow" keys undecided, and includes four title fields the rule excludes — greenable today via a single PROSE_ALLOWLIST entry with no NAME_POOL or census row. This is a finite enumeration gap over the closure machinery, not a repeat of round 3's regress signature.
```


## AC Red-Team — 2026-09-06 (round 5)

**Reading order followed:** `## Intent`, `### Examples of done`, `## Problem / Motivation`, `## Exploration Notes` in full — including all five prior revision narratives, the AC-5 sufficiency question and its recorded recommendation, and the fourteen data premises — then `## Acceptance Criteria` (AC-1 through AC-5) last, and the Architectural Review round 6 fence directly above as the most recent carry-forward. I did not stop at the gates' prose: I re-read `obsidian_schemas/name_validation.py` (both Tier-1 tables, lines 190-309 and 371-438) and `obsidian_schemas/name_cleaning.py:1-58` myself, and grepped every real committed specimen for the two branches at issue across `tests/test_name_validation.py`, `tests/test_name_gate.py` and `tests/test_name_cleaning.py`.

**What I attacked and what held.** AC-1 through AC-4 are unchanged since the round-4/5 folds and I found no new issue in any of them: the frozen-digest-plus-byte-copy split (AC-1) still needs both legs (an edit to committed bytes vs. a lossy materializer); the `set(TYPE_TO_MODEL)`-derived sweep with the `watch`/`explore`/`gift-idea` body-marker narrowing (AC-2) is still a derived sweep with a hand-written oracle, not a self-agreement check; AC-3's class-table equality is still correctly scoped to `status == MEASURED` so an honest `ABSENT` ruling cannot go RED; AC-4's skip-mapping equality is still per-repository with the double-ownership of the two untyped classes stated as expected rather than discovered. Round 4's finding — AC-5(b)'s identity-position enumeration missing `Exploration.related`, `Watch.streaming_service`, `GiftIdea.source` — is CLOSED: I independently re-read every field of every `TYPE_TO_MODEL` member against `models.py` rather than against P14's prose, and the current AC-5(b) text lists all three, states the three-clause rule, and both cite corrections (`_ME_TO_PREFIX_RE` carries no `Dave` alternative; the package compares suffixes with `str.lower()`, never `casefold`) check out at the cited lines. I found no tautological AC, no gameable single-literal pair, no drift from Intent, and the byte-copy/write-door split (AC-1(c), AC-2's `roundtrip_representative` naming) still correctly forces the corruption specimens through the refusing gate rather than around it.

**Finding — AC-5, MATERIAL.** The Architectural Review round 6 fence above raises a real gap: `CONNECTIVE_SET` is enumerated from three of `name_cleaning.py`'s five prefix/suffix regexes (`:46`, `:54`, `:55`) and omits the other two (`:56` `_ARCHIVE_PREFIX_RE`, `:57` `_UNKNOWN_CONTACT_SUFFIX_RE`). But its proposed fix — add `"Archived"`, `"Unknown"`, `"Contact"` to the frozen set — is not yet safe to fold as written, because AC-5(b)'s own extractor definition is ambiguous in exactly the way its own non-blocking note 2 already names, and that ambiguity does not merely affect ordinary surnames (`McDonald`, `d'Angelo`) — it decides whether architect's own proposed fix is correct, over-broad, or wrong.

*Failure scenario.* AC-5(b)'s extractor is "decode every byte... then take each run whose FIRST character is an uppercase or non-ASCII letter, over letters, marks, apostrophes and hyphens." Under the plain reading of "run" — a maximal contiguous span of that character class — `"zArchived"` is ONE run (no separator between `z` and `Archived`) whose first character is lowercase `z`, so the whole run is excluded from extraction and yields NO token at all. Every real `archive_prefix` specimen already committed in this repository is spelled exactly this way, with nothing separating the `z` from the capital that follows — `tests/test_name_validation.py:229` (`"zArchived - Rosie Samuels"`), `:235` (`"zzArchived - Someone"`), `tests/test_name_gate.py:94` (`"zArchived Dave Smith"`), `tests/test_name_cleaning.py:131` — with zero exceptions anywhere in the tree. Under that reading, which every committed real specimen for this exact branch is consistent with, `archive_prefix` forces no `CONNECTIVE_SET` member at all, directly contradicting the premise architect's fix rests on; only under the OTHER reading architect's own note 2 declines to adopt (restart-scanning at each internal capital, i.e. camelCase splitting) does `"Archived"` get extracted. `unknown_contact` is genuinely less clear-cut than I first read it: this repository already commits BOTH a lowercase-suffix form (`tests/test_name_validation.py:248,254` — `"219945292038370 unknown contact"`, `"Jane Doe unknown contact"`, matching the regex's own "WhatsApp scanner artifact" comment at `name_validation.py:112` and its `re.IGNORECASE` flag) AND a capitalized standalone form (`tests/test_name_gate.py:96` — `"Unknown Contact Zeta-9"`, echoing the `TIER1_BRANCHES` table's own `specimen=` field at `name_validation.py:274`) — so unlike `archive_prefix`, the evidence does not point one way, and I am not asserting this branch forces zero tokens. What both branches share is the actual defect: the correct `CONNECTIVE_SET` membership fix is a function of a "run" definition the criterion has never pinned down, and for at least one of the two branches architect's literal proposal is contradicted by every real specimen this package has ever committed for it.

*What would have to change.* Fold AC-5(b) in two steps, not one: first state, in the criterion itself, which "run" reading the extractor uses — the plain maximal-contiguous-span reading is the one every already-committed `archive_prefix` specimen in this repository is consistent with, and it is also the reading that resolves architect's own note 2 the same way for `McDonald`/`d'Angelo`. Only then determine, from that stated rule applied to a specimen built from the package's own observed forms (not read off the `TIER1_BRANCHES` display field alone), whether `archive_prefix` and `unknown_contact` force any `CONNECTIVE_SET` member, and which. Folding architect's literal three-member proposal first risks landing exactly the ungrounded-literal-in-a-frozen-set pattern round 4's fold removed the generator for — this time authored by a gate's fold rather than a builder's shortcut — because a human reviewing `CONNECTIVE_SET` for "is every member real furniture" has no way to tell, from the criterion text alone, that `"Archived"` was never checked against this repository's own real `archive_prefix` specimens, all of which are spelled in the one form the stated extractor would not extract it from.

**On the sufficiency question recorded above:** I am not ruling on it — Dave owns it. I note for the record that this finding is narrower than rounds 4-6's shape: it does not require a corpus surface to be re-read exhaustively again, it requires one sentence pinning down an extraction rule the document already states but never disambiguates. I read that as a closable gap in the criterion's own determinism rather than a new instance of the round-4 generator family, so I am not flagging the regress signature on it.

I have not touched `## Acceptance Criteria`, `## Intent`, or any other gate's section, and I have originated no AC text — the above is a defect description for `ideation-partner` to fold, not a fix I am applying myself.

```verdict
gate: ac-red-team
verdict: REVISE
date: 2026-09-06
model: claude-sonnet-5
targets: AC-5
prior: held
basis: folded-material
findings: 1/1
note: AC-5(b)'s "run" extraction rule is undefined between two readings that disagree on whether "zArchived" yields any token, and every real archive_prefix specimen already committed (tests/test_name_validation.py:229,235; tests/test_name_gate.py:94; tests/test_name_cleaning.py:131) is spelled in the one form that yields NOTHING under the plain reading — so architect round 6's proposed CONNECTIVE_SET fix (add "Archived","Unknown","Contact") is contradicted by this package's own real specimens for at least one of its two target branches and must not be folded until the rule is pinned down.
```


## AC Red-Team — 2026-09-07 (round 6)

**Reading order followed:** `## Intent`, `### Examples of done`, `## Problem / Motivation`, `## Exploration Notes` in full — all seven revision narratives, the AC-5 sufficiency question with its recorded recommendation and round-6 datum, and the sixteen data premises — then `## Acceptance Criteria` (AC-1 through AC-5) last, then the Architectural Review round 7 fence directly above as the most recent carry-forward. I did not stop at the fold's or the architect's prose: I read `obsidian_schemas/name_validation.py:148-320` myself and enumerated `TIER1_BRANCHES` by hand before reading AC-3's floor text against it.

**What I attacked and what held.** AC-1, AC-2 and AC-4 drew no finding from me — the frozen-digest/materializer split, the `TYPE_TO_MODEL`-derived round-trip sweep with its hand-written oracle and repository-less-type narrowing, and the per-repository skip-mapping equality with double ownership declared expected are all unchanged since round 5 and I found no new gap in any of them. Round 5's finding against AC-5(b)'s undefined "run" is CLOSED, and I re-verified the closure independently rather than trusting the fold's prose or the architect's round-7 re-verification of it: `_ARCHIVE_PREFIX_RE` is `^z+Archived\s*-\s*` (`name_cleaning.py:56`) / `^z+Archived\b` (`name_validation.py:110`) — one lowercase-initial run under the now-pinned maximal-span rule, yielding no token — `CONNECTIVE_SET = {Dave, Me, My}` is correctly unchanged, the four worked consequences are checkable and correct (`McDonald` one token, `d'Angelo` none, `Zeta-9`→`Zeta`, `zArchived` none), and I found no fifth instance of round 4's removed generator anywhere in AC-5.

**Finding — AC-3, MATERIAL.** The DRAFT CLASS FLOOR is a hand-transcribed list quantifying over `TIER1_BRANCHES` ∪ `COMPANY_TIER1_BRANCHES` — an iterable, uniquely-keyed-by-`branch_id` surface this package exports at `name_validation.py:190-309` and `:371-438` — and the list is wrong. I enumerated the tuple myself: ten `branch_id`s (`email_chars`, `rfc2822_leak`, `arrow_connective`, `calendar_prefix`, `me_to_prefix`, `path_hostile`, `archive_prefix`, `unknown_contact`, `pure_digit`, `empty`). AC-3's floor maps to exactly six of them (`rfc2822_leak`, `arrow_connective`, `me_to_prefix`, `path_hostile`, `archive_prefix`, `unknown_contact`); its own `why:` asserts the pre-round-6 floor covered "eight of the ten" — also wrong, the true prior count was four. `calendar_prefix`, `email_chars`, `pure_digit` and `empty` are absent from the floor.

*Failure scenario.* AC-3's three assertions check the census and the manifest against EACH OTHER; none of the three reads the package's branch table. A conductor authoring the census works from AC-3's own eleven-plus-one class list — the document both Dave and the conductor read — and that list gives no prompt to look for a `Dave -`/`Me -` calendar-prefix specimen as a class distinct from the arrow-connective one it sits beside in the code, nor for a pure-digit-as-a-name specimen, nor an email-chars-as-a-name one, nor the `empty` name this item's own write path introduces (`create_stub`'s guard means `empty` has never fired in production before now). The census writes its rows for the eleven-plus-one named classes, assertions (i)-(iii) all pass, AC-5 passes, the floor runs green, and the corpus ships with zero specimens for four of the package's ten live refusal branches — exactly the "a class measured at zero is a row the conductor writes, not a row that may be omitted" property assertion (iii) exists to guarantee, defeated because the floor never named the shape for the census to measure in the first place. `calendar_prefix` carries a consequence beyond coverage: AC-5(c)'s provenance ledger justifies `CONNECTIVE_SET`'s frozen `Dave` member by citing `name_validation.py:226-236`'s `Dave - Thomas Gatten` specimen as "live prefix vocabulary this vault actually produces" — if the census never measures that class as such, the corpus can ship with no specimen exercising the one branch that member's own justification names.

*What would have to change.* Split the floor: derive the branch-keyed half at test time from `{b.branch_id for b in TIER1_BRANCHES + COMPANY_TIER1_BRANCHES}` — the same move AC-2 already makes against `TYPE_TO_MODEL` and AC-4 against `_skip_reason`'s codomain — and keep only the six shape classes that have no branch (diacritics, hyphenated surnames, whitespace damage, stem/name divergence, same-name collision, postal-address leak) as a hand list, since there is nothing to derive them from. Key on `branch_id`, not `pattern`: `arrow_connective`, `calendar_prefix` and `me_to_prefix` all raise the shared pattern `calendar_prefix` (`:216`, `:228`, `:240`), so a pattern-keyed derivation would silently re-merge three classes AC-3 itself treats as separate. Correct the `why:`'s "eight of the ten" to four. This is a criterion-text-only fix — the existing MEASURED/ABSENT split already lets a branch the live vault does not carry discharge honestly with no specimen — so it costs one edit now against a re-sign later.

**On the regress signature: I read the pattern and am not flagging it as one requiring escalation past Dave's pending sufficiency question.** This is the third consecutive round in which an enumeration in this document turned out not to be its own named surface's output (round 5: AC-5(b)'s identity-position list vs. `models.py`; round 6: `CONNECTIVE_SET` vs. the regex surface; this round: AC-3's floor vs. `TIER1_BRANCHES`), and architect round 7 already named that plainly and recorded both readings for Dave rather than ruling on it. I concur with the architect's own distinction rather than re-litigating the open question: this instance sits in AC-3, which the recorded middle path (demoting AC-5(b)/(c) to a declared human-review criterion) would not have touched, and the fix on offer is mechanical and generator-removing — a runtime read of an already-exported tuple, identical in shape to AC-2's and AC-4's existing derivations — not new machinery for a later round to trip on. That is what keeps this an ordinary REVISE rather than the shape my own instructions ask me to escalate instead of fold: the fix closes the family everywhere it can recur in this document rather than relocating it.

I have not touched `## Acceptance Criteria`, `## Intent`, or any other gate's section, and I have originated no AC text — the above is a defect description for `ideation-partner` to fold.

```verdict
gate: ac-red-team
verdict: REVISE
date: 2026-09-07
model: claude-sonnet-5
targets: AC-3
prior: held
basis: folded-material
findings: 1/1
note: AC-3's DRAFT CLASS FLOOR is hand-transcribed against TIER1_BRANCHES/COMPANY_TIER1_BRANCHES (name_validation.py:190-309, :371-438) and covers only 6 of the 10 branch_ids, silently omitting calendar_prefix (the sole cited source of CONNECTIVE_SET's frozen Dave member), email_chars, pure_digit and empty, while its own why: claims "eight of the ten" (true prior count was four); fix is to derive the branch-keyed half of the floor from the tuples' branch_id at test time exactly as AC-2 derives from TYPE_TO_MODEL and AC-4 from _skip_reason, keyed on branch_id not pattern since three branches share the raised pattern calendar_prefix.
```


## AC Red-Team — 2026-09-07 (round 7)

**Read order followed:** `## Intent`, `### Examples of done`, `## Problem / Motivation`, `## Exploration Notes` in full — all seven revision narratives, the AC-5 sufficiency question, the eighteen data premises, `## Constraints discovered`, `## Approach`, `## Write Targets` — then the current draft `## Acceptance Criteria` (AC-1 through AC-5) last, then Architectural Review round 8 and AC Red-Team round 6 as the most recent carry-forward. I read `obsidian_schemas/name_validation.py:190-438`, `body_sections.py:303-324`, `models.py:309-318` and `name_gate.py:319-344` myself before treating any prior gate's citation as settled, and I additionally verified the pipeline tooling itself — `pipeline-runners.yaml`, `src/cage.py`, `src/ac_signoff.py` and `src/stage_advancer.py` — rather than reasoning about the census artifact's protection from this document's prose alone.

### What I attacked and what held

AC-1's byte-copy / digest / planted-discriminator mechanism: unchanged since round 1, no new route found. **Held.**

AC-4's per-repository equality, derived repository set and planted double-ownership discriminators: unchanged since round 7's fold, re-verified against `repositories/__init__.py` and `base.py`'s `_owns`/`_note_skip`. **Held.** (Architect round 8's note 1 — the asymmetry clause `A - B == A - B` is a tautology — is real but is not my shape: it costs nothing, since AC-4's legs (a)-(c) carry the actual oracle, and a tautological restatement no builder can exploit for a shortcut is a wording note, not a criterion a corner-cutting builder could satisfy while the Intent goes unserved.)

Round 6's AC-3 branch-floor finding: **closed**, verified myself against the raw tuples rather than accepted from P18 or the architect's round-8 re-verification — `TIER1_BRANCHES` (`name_validation.py:190-309`) and `COMPANY_TIER1_BRANCHES` (`:371-438`) grep to exactly the ten and five `branch_id`s the current AC-3 text reads at test time.

Architect round 8's finding (AC-2's two remaining hand-transcribed enumerations): confirmed real against the code (`body_sections.py:303-324` vs `models.py:309-318`; `name_gate.py:340-341`/`:361-363`), but it is the architect's finding, already blocking every transition via U1, and it is explicitly not my shape: the architect's own text states neither instance has a green-over-wrong route — both fail LOUD, for the wrong reason, never a false PROMOTE. That is a maintenance/consistency defect, not a criterion a corner-cutting or honestly-misreading builder could satisfy while leaving the Intent unserved. I am not re-raising it.

### Findings

**AC-3 / AC-5(c) / `## Write Targets` — CRITICAL. The census artifact both criteria trust as ground truth has no integrity check anywhere in this pipeline once it lands, and the AC set does not supply one either.**

`docs/vault-shape-census.md` is the ONLY place the claims AC-3(iii)'s floor and AC-5(c)'s pool provenance depend on can be settled — the suite is hermetic and cannot read the live vault itself (`## Constraints discovered`), so both criteria's oracle for "this class occurs N times in the real vault" and "this name-token occurs zero times in the real vault" is entirely delegated to what that one file says. `## Write Targets`'s fence frames it as a `kind: precondition` artifact precisely because it must land in HEAD, authored by "the conductor" with real vault access, *before* Dave signs and *before* any builder starts — a framing that implicitly assumes the file stays what the conductor wrote. Nothing enforces that assumption once the build begins.

I checked this against the pipeline tooling rather than this document's prose about it. `pipeline-runners.yaml:34-38` declares `write_authority: [obsidian_schemas/**, tests/**, scripts/**, docs/**]` — `docs/**` in full, no carve-out for a landed precondition file — and `cage.DENY_PATHS` (`src/cage.py:204`) covers only `state/**`, `.git/**` and unseeded dependency directories, not this path, so `cage.classify_change` treats a builder edit to `docs/vault-shape-census.md` as an ordinary allowed write. The build-spawn precheck (`cage.py`'s `tracked_in_head`, invoked from `src/pipeline_orchestrator.py` around line 3185) and WI-300's grounding-ordering backstop (`src/ac_signoff.py:1896-1943`) both check only that the file is *some* committed blob in HEAD at a single moment before the build starts — neither records nor later compares its content. The one real merge-boundary integrity wall in this pipeline, `_forged_nondriven_docs` (`src/stage_advancer.py:653-675`), is explicitly scoped to docs carrying work-item frontmatter (`is_work_item_doc`, `:660-661`, `:671-673`) and by its own design treats an edit to a shared, non-work-item doc as ordinary legitimate build traffic — exactly what `docs/vault-shape-census.md` is, since it carries no `id: WI-*` frontmatter of its own. A builder spawn can therefore open `docs/vault-shape-census.md` and rewrite any row in it, and nothing between D4a and Dave's own later reading of the diff notices.

*Failure scenario, concrete and specific to the criteria as drafted.* AC-3(iii)'s floor requires a row of either status for all ten `branch_id`s; suppose the conductor's real census measured `calendar_prefix` as MEASURED with a genuine specimen, but that specimen is awkward to author faithfully (its character-profile requirements are among the densest in this document). A builder under schedule pressure edits the row in place to `status: ABSENT`, `count: 0`, and a scan command/stdout pair typed to look plausible, and drops the specimen from the corpus. AC-3(i)'s equality is scoped to MEASURED rows only, so the now-ABSENT row exits the equality entirely; AC-3(ii)'s per-row shape check is satisfied by construction, since the builder wrote exactly the shape it demands; nothing re-derives the count from the live vault, because nothing in the suite — or the pipeline — can. The floor, whose declared purpose is "a class measured at zero is a row the conductor writes, not a row that may be omitted," is defeated by exactly the means it exists to prevent, and every AC-3 assertion is green. AC-5(c) is worse, because its claim is the privacy wall's actual load-bearing one: a builder who wants a convenient, easy-to-spell `NAME_POOL` token — one that happens to collide with a real name in the live vault the builder cannot see and has no way to check — adds a pool-table row in `docs/vault-shape-census.md` asserting a non-occurrence scan that was never run, with fabricated command/stdout text satisfying AC-5(c)'s only checks (non-empty command, non-empty stdout, containment, disjointness from `CONNECTIVE_SET`). `## Intent`'s one sentence this whole item exists to satisfy — "None of Dave's contacts' real names, emails or numbers go into this repository" — has no machine check standing behind it at all in this scenario, because the one artifact meant to carry that check independently of the builder is, structurally, the builder's own write surface.

This is not a process gap outside the document's own stated concerns — it is the same shape AC-5 has been hardened against for five straight rounds (a wall whose closure turns out to have an unguarded escape hatch), one layer out: the escape hatch this time is not a clause inside `fixture_vault.py`, it is the ground-truth artifact `fixture_vault.py`'s clauses are checked against.

*What would have to change.* This item's own AC-1(a) already states the fix for exactly this problem, applied to the wrong artifact: "Frozen without a mechanism is a wish — nothing otherwise stops a future test from editing a fixture to make itself pass." `docs/vault-shape-census.md` needs the identical mechanism AC-1(a) gives the corpus: a digest computed over the census at the moment it lands as the WI-300 precondition and recorded in the fence or the manifest, asserted equal to a freshly-computed digest at test time — hermetic, no shell, no live-vault read, the same `sha256`-over-bytes move AC-1(a) already performs. AC-3 and AC-5(c) should both gain a leg (or share one new leg) asserting this. Absent it, the census's trustworthiness rests entirely on a human noticing an unexpected diff to a shared, non-work-item doc during code review — precisely the "reviewable by eye" aside AC-5's own `why:` already argues is not a control worth relying on for this item's privacy property.

I have not touched `## Acceptance Criteria`, `## Intent`, or any other gate's section, and I have originated no AC text — the above is a defect description for `ideation-partner` to fold, not a fix I am applying myself.

```verdict
gate: ac-red-team
verdict: REVISE
date: 2026-09-07
model: claude-sonnet-5
targets: AC-3, AC-5, #write-targets
prior: held
basis: original
findings: 1/1
note: docs/vault-shape-census.md is AC-3(iii)'s and AC-5(c)'s sole ground truth for live-vault facts the hermetic suite cannot check itself, but nothing in this pipeline (write_authority includes docs/** per pipeline-runners.yaml:34-38; the only integrity wall, _forged_nondriven_docs at stage_advancer.py:653-675, explicitly excludes non-work-item docs by design) or in the AC set freezes its content once landed, so a builder can silently edit a MEASURED row to ABSENT or fabricate a pool-table non-occurrence scan and every AC-3/AC-5(c) assertion still goes green; fix is the same frozen-digest mechanism AC-1(a) already gives the corpus, applied to the census.
```


## AC Red-Team — 2026-09-07 (round 8)

**Read order followed:** `## Intent`, `### Examples of done`, `## Problem / Motivation`, `##
Exploration Notes` in full (all nine revision narratives, the AC-5 sufficiency question, the
nineteen data premises, `## Constraints discovered`, `## Approaches considered and rejected`,
`## Where the structure lives`, `## Convergence`), then `## Approach`, `## Write Targets`, and the
current draft `## Acceptance Criteria` (AC-1 through AC-5) last, then Architectural Review round 9
as the most recent carry-forward — its fold has not yet landed in the criteria text below, so this
round reviews the same draft round 9 reviewed, not a folded successor of it.

### What I attacked and verified myself, and what held

I did not accept any prior gate's code citation without re-reading it. AC-1's byte-copy /
frozen-digest / planted-discriminator mechanism (unchanged since round 1): no new route found.
**Held.** AC-2's derived population and narrowing arm: `models.py:309-318` keys exactly the eight
`TYPE_TO_MODEL` types I read myself; `body_sections.py:303-324` keys exactly `person`, `company`,
`meeting`, `book`, `exploration` — five, confirmed by direct read, not by trusting the fold's
count — so the narrowing arm's `set(TYPE_TO_MODEL) - set(ENTITY_BODY_CONFIG)` is exactly `{watch,
explore, gift-idea}`. **Held.** AC-2 leg (c)'s GATE-CLEAN door predicate: read `name_gate.py:315-344`
directly — line 319 branches on `declared_type is not None and declared_type != PERSON_TYPE`, the
company arm calls `validate_strict(..., branches=COMPANY_TIER1_BRANCHES)` at `:340-341` for its raise
behaviour only, and every non-person/company type falls to the shared `return dict(introduced)` at
`:344`, matching the criterion's claim exactly. **Held.** AC-3's branch-floor population: grepped
`branch_id="..."` directly in `name_validation.py` myself rather than trusting P18 — ten distinct ids
in `TIER1_BRANCHES` (`:190-309`) and five in `COMPANY_TIER1_BRANCHES` (`:371-438`, all five already
members of the person ten) — the union is exactly the ten the criterion's floor asserts. **Held.**
AC-3(iv)/AC-5(c)'s census-fixity legs (my own round-7 finding): both are present in the current AC-3
and AC-5 text with the `CENSUS_DIGEST` value living in the signed criterion rather than in
`fixture_vault.py`, and architect round 9 independently re-attacked the mechanism on a lifecycle case
(a post-landing conductor refresh) I had not tried and reported it survives. **Held**, and I did not
re-derive round 9's lifecycle check myself — recorded here as inherited rather than re-verified, so a
later reader knows which half of that claim is mine. AC-4's derived repository set and ownership
mechanism: I read `repositories/__init__.py` directly — imports end at line 12, `__all__` is
`:14-21` and contains `VaultPathNotConfiguredError` alongside the four concrete repositories, matching
architect round 8's note 2 exactly — and `repositories/base.py:258-265`'s `_owns` (`declared_type ==
self.type_name` when legible, else `Path(self.file_pattern).stem != "*"`) and `:267-275`'s
`_note_skip` match the criterion's double-ownership claim. **Held.**

### Finding

**AC-4 — CRITICAL. Converges independently with architect round 9: the `_skip_reason` codomain AC-4
calls "derived" is hand-transcribed, and the criterion states a consequence only a real derivation
would deliver.**

I read this before I read round 9's section, then read round 9's section and found we had located
the identical defect from the same code read — recorded as independent confirmation rather than
inherited, since the AC set has not been folded since round 9 ran and the defect is still live in the
text I was asked to attack. AC-4's text: "`_skip_reason` (`repositories/base.py:41-47`) yields
exactly `{"malformed-frontmatter", "schema-drift", "unreadable"}` … the UNION over the four declared
per-repository mappings' reasons is asserted EQUAL to that codomain … a fourth reason added to the
package later fails until it has a specimen." I grepped `repositories/base.py` for the three strings
myself: they occur at `:37` (a type comment on `SkippedNote.reason`), and at `:44`, `:46`, `:47` as
bare return-statement literals inside `_skip_reason`'s `isinstance` chain. No frozenset, tuple, dict
or `Enum` exports them anywhere in the package — unlike `TYPE_TO_MODEL` (a dict AC-2 reads), the
`branch_id` union (two exported tuples AC-3 reads) and the repository set (`__all__` AC-4 itself
reads two paragraphs earlier), there is nothing here to read.

**Concrete failure scenario.** A builder later adds a fourth arm to `_skip_reason` — say a
`PermissionError` distinguished as `"unreadable-permission"` — for a real reason (WI-020's own
`base.py:29-34` note already distinguishes "vanished at DEBUG" incidents by cause). AC-4's harness
computes its "declared" expected set the same way it always has: by hand-typing the three strings
into the test, because that is the only thing anyone has ever been able to do with this codomain —
`tests/test_loud_fail_load.py:187` already does exactly this today. The corpus carries no specimen
producing the new reason; the manifest declares no repository mapping containing it; the hand-typed
"codomain" constant is never touched because it was never connected to `_skip_reason` in the first
place. AC-4's equality — both sides now hand-computed — holds trivially. **The criterion is GREEN**
while a new skip-reason class joins the corpus's blind spot with nothing in the suite able to notice,
which is precisely the "an unloadable note vanishes silently" failure WI-020 built `SkippedNote` to
eliminate (`## AC Red-Team`'s own `why:` for this criterion, and `base.py:29-34`), reappearing one
layer up from the layer WI-020 originally fixed it at. A builder who wrote the fixture corpus
correctly for today's three reasons would ship this AC set having implemented no actual regression
protection for the fourth reason at all — an honest builder is caught by nothing, which is the AC
red-team's own failure mode (satisfiable-with-nothing-real-behind-it), not merely an architect's
tidiness complaint.

**Why this is mine to raise independently rather than only inherited from round 9.** My role is to
find whether a builder — corner-cutting or honestly misreading — could satisfy this AC while the
Intent goes unserved, and this is exactly that: nothing about implementing AC-4 as currently worded
requires connecting the harness's hand-typed set to the package's actual codomain, so a build that
passes every leg as written has NOT built the regression protection the criterion's own prose claims
it has. That the architect found the identical code fact from a duplication/maintenance angle does
not make it any less an AC red-team finding; the two framings are the same defect looked at from two
directions, and this document's own convergence record (round 7 AC-3/AC-5(c), round 8 AC-2, round 9
AC-4 — three consecutive rounds where the same family of defect surfaced in a part of the document
the standing sufficiency-question "middle path" does not touch) is stronger with a second, decorrelated
confirmation than with one.

**What would have to change.** Either export the codomain — a module-level `SKIP_REASONS` frozenset
in `repositories/base.py` whose members `_skip_reason` returns, read by AC-4 at test time exactly as
AC-2 reads `TYPE_TO_MODEL` — or keep the set hand-written and say so: delete "a fourth reason added to
the package later fails until it has a specimen" and move this set into the explicitly-hand-declared
residue list beside AC-4's own (deliberately hand-written) ownership oracle. I did not write either
fix into `## Acceptance Criteria` myself; the fold is `ideation-partner`'s.

I have not touched `## Acceptance Criteria`, `## Intent`, or any other gate's section, and I have
originated no AC text.

```verdict
gate: ac-red-team
verdict: REVISE
date: 2026-09-07
model: claude-sonnet-5
targets: AC-4
prior: held
basis: original
findings: 1/1
note: Independently re-derived the same defect architect round 9 found (not yet folded): AC-4 claims its skip-reason codomain is derived from `_skip_reason`, but repositories/base.py exports no such set — the three strings are bare return literals at :44/:46/:47 plus a type comment at :37 — so both sides of AC-4's equality are hand-typed and a real fourth skip-reason class added later leaves the criterion GREEN with the new class silently unprotected, the exact WI-020 failure mode one layer up; fix is a one-line SKIP_REASONS export read the way AC-2 reads TYPE_TO_MODEL, or an honest demotion to the hand-written residue list.
```


## Architectural Review — 2026-09-06

**Recommendation: REVISE — two criteria are underdetermined against one fact of the code, and the
approach itself is sound and stands.**

### Trigger check

Fires on three: a new shared test surface every later item builds on (`tests/fixture_vault.py` plus
`tests/fixtures/vault/`); a new artifact convention (`docs/vault-shape-census.md`, machine-read by
AC-3); establishes new persistent state in the repo (~50 committed notes plus a frozen digest).
Effort is over a day. Review run.

### Review

**Fit.** Harmonizes. The four derived sweeps are the shape this repo already uses — `tests/derivations.py:1-22`
is the standing "derive the sweep from the class's own declaration" module, and AC-2's
`set(TYPE_TO_MODEL)` equality and AC-4's `_skip_reason` codomain equality are the same move against
runtime declarations rather than syntax. Byte-copy materialization is correct and P9 holds as
written: the filesystem-mutation walls scan `python_files_under(PACKAGE_ROOT, SCRIPTS_ROOT)` only
(`tests/test_write_routing.py:91`, `:370`), so `tests/` is outside them; the `ast` single-homing wall
scans `PACKAGE_ROOT, TESTS_ROOT` (`tests/test_name_gate_wall.py:1136`), so `fixture_vault.py` must
name no `ast` — which nothing in the design needs.

**Duplication.** No overlap found. Nothing in the tree materializes a vault from committed bytes;
the nine private helpers P3 counts all synthesize. `tests/derivations.py` is the syntax-scan home and
this item's sweeps read runtime objects and file bytes, so they do not belong there and would not
be a second `ast` home.

**Boundaries.** Ownership is clean: bytes own the specimens, the manifest owns the oracle, the census
owns the distribution. The one boundary the design does not model is the repository glob partition —
see Blocking issues 1 and 2.

**Determinism boundary (LLM vs code).** Correctly placed. The judgment half (which shape classes
exist, what a faithful pseudonymous specimen is) is the conductor's census; the mechanical half
(does this specimen actually refuse, is every token in a reserved range, does the digest hold) is
code, and AC-3's per-specimen declared verdict is what stops the census being discharged as prose.
No mechanically-available value is left to LLM compliance.

**Reversibility.** High. Additive — a new directory, a new module, three migrated test files. The
one genuinely irreversible edge is real data in git history, and AC-5 makes it structurally
checkable rather than a matter of care, which is the right shape for an irreversible risk.

**Generalization.** Right-sized. D5 and D6 both decline to generalize on measured grounds (P8:
`pyproject.toml:38-39` packages `obsidian_schemas` only, so nothing under `tests/` is importable by a
consumer), and the layout chosen — plain vault directory plus a declared manifest — is the one that
travels if the export surface ever lands.

**Cost & maintenance.** The recurring cost is the digest constant: every legitimate corpus edit
requires regenerating it, and no tool for that is named. That is the intended friction, but it wants
a one-line regeneration recipe in the module docstring or the cost falls on whoever is surprised by
it in six months.

**Build vs extend vs integrate.** Build is right. There is nothing to extend — P1/P2 measure zero
fixture data files and no `conftest.py` anywhere — and no library supplies a corpus of this vault's
own corruption shapes.

**Prior art (outside view).** The approach does not build machinery around a subtracted capability,
so this dimension is not blocking. A frozen committed corpus plus a snapshot digest is the standard
answer everywhere (Go's `testdata/`, pytest data directories, golden-file testing), and the
byte-copy rule is not a workaround for the write gate — it is how one tests a refusal surface at
all. The census-as-precondition is this pipeline's own established idiom with in-repo precedent
committed nine days ago (`docs/company-name-corpus-audit.md`, WI-300, grounding WI-022's company
Tier-1 table at `obsidian_schemas/name_validation.py:344-351`), not novel compensation.

**LESSONS.** #9 is honoured rather than gestured at: it asks for "a ~50-record frozen real-data
fixture per entity type" and names `José García`, `Sören Winter`, `Dave -> Thomas Gatten (Adzact)`,
`Me to David Field` — the exact set P10 finds scattered. D1's amendment (sample the shape
distribution, synthesize the identities) is a defensible reading of "anonymized", and AC-3's
per-specimen declared verdict is what keeps it from collapsing into D2, because a specimen that does
not actually fire its class's refusal is RED. D7's park of WI-026's acceptance is a correct
application of #27. No scar is re-incurred.

### Blocking issues

**1. AC-4's skip mapping is buildable two ways, and the two catch different regressions.**
`PersonRepository` and `CompanyRepository` both inherit the default `file_pattern` of `@*.md`
(`obsidian_schemas/repositories/base.py:196-198`; neither `person.py` nor `company.py` overrides it)
and both resolve to the same flat vault directory (`person.py:1410` writes
`self.vault_path / f"@{clean_name}.md"`). `_note_skip` decides ownership on the error's
`declared_type` (`base.py:267-275`), and `errors.py:65-67` states that for `FrontmatterParseError`
"declared_type is always None — nothing was legible"; `_owns(None)` then returns
`Path("@*.md").stem != "*"`, which is True (`base.py:258-265`). So **one** `malformed-frontmatter`
specimen is recorded in **both** repositories' `skipped_notes`, and the same holds for `unreadable`,
whose `UnicodeDecodeError` carries no `declared_type` either — while `schema-drift` carries one
(`errors.py:70-71`) and is recorded only by its owner. AC-4 leg (a) says "the mapping `{path: reason}`
built from `skipped_notes()`" without saying whose, and leg (b) says "for each repository". A union
over all repositories and a per-repository mapping produce different declared manifests, both pass
their own reading, and only the per-repository one goes RED when a regression moves an untyped skip
between owners. The criterion whose entire point is a both-directions equality cannot leave the
domain of the equality unstated (WI-144). *Concrete fix:* state that the manifest declares
`{repository_type: {path: reason}}` and that AC-4(a)'s equality is asserted per repository, with the
double-ownership of the two untyped classes declared as expected rather than discovered.

**2. The corpus's on-disk layout is unstated, and the repository glob partition makes it
load-bearing — the tidy choice breaks AC-4 outright.** The live vault is ONE flat directory
partitioned by filename glob: `@*.md` for person and company, `Meeting *.md` for meetings
(`repositories/meeting.py:51-54`), book's own, and `load()` globs non-recursively from a single
`vault_path` (`base.py:231`). The `## Approach` says "`tests/fixtures/vault/` — a frozen corpus of
~50 markdown notes" and says nothing more. A spec-writer reaching for the obvious tidy layout —
subdirectory per entity type — writes a corpus against which AC-4 loads **zero** notes and passes
vacuously on `0 == 0`, and that is a redesign discovered at build rather than a detail settled at
spec. Two further consequences follow from flatness and want stating now, while the criteria are
still draft: the four types with no repository (`watch`, `explore`, `gift-idea`, `exploration`) have
no glob at all, so AC-2's fixtures for them are parser-level only while AC-4's counts are
repository-level; and AC-3's "same-name collision of at least three notes" cannot be three notes
sharing a filename in one flat directory — it must be three filenames sharing one stored `name:`,
which is the *same specimen* as the listed "filename-stem-does-not-equal-stored-name divergence"
class, so two of the nine draft classes may be unable to have distinct specimens and the census must
rule on whether they are one class or two. *Concrete fix:* declare the corpus a single flat
directory mirroring the live vault, in the `## Approach`, and name the collision/divergence question
as one the census settles.

### Notes (non-blocking)

- **The `unreadable` specimen has exactly one spelling, and it is not obvious — it is worth naming
  before a builder concludes the class is unreachable from committed bytes.** `parser.py:238` calls
  `file_path.read_text(encoding="utf-8")` unwrapped, so a note carrying invalid UTF-8 raises
  `UnicodeDecodeError`, which is neither `FrontmatterParseError` nor `SchemaDriftError` and so falls
  to `_skip_reason`'s third arm (`base.py:41-47`). That makes AC-4's three-way set equality
  satisfiable by byte copy — verified, not assumed — but it also means one corpus member is not
  valid text, which is precisely why AC-1's digest and AC-5's token scan must both be over BYTES and
  never over decoded text. A `chmod`-based `unreadable` specimen would not survive git and must not
  be reached for.
- **AC-2(c) names no write mechanism, and the two candidates differ.** `write_markdown_file` is a
  gated door — `gate_write` is called from every frontmatter write arm (the eight arms
  `tests/derivations.py:977-1008` derives) — while `write_frontmatter` is the bare serializer. For
  the eight clean per-type fixtures either works, but the manifest should state which, so a builder
  cannot pick the arrow-connective or path-hostile specimen as its `person` representative and then
  discover AC-2(c) refuses it.
- **D6's re-entry rides an item whose declared scope is a different symbol set.** WI-030 was minted
  2026-09-06 for `lint_vault`'s export surface (`read_vault`, `build_indexes`, `run_lint`,
  `VaultFile`, `Severity`), not for this corpus. The deferral is measured and correctly ruled, and I
  am not treating it as blocking, but the spec should either widen WI-030's premise by one line to
  carry the fixture corpus or say plainly that D6 re-enters only when someone re-opens it — the
  cost of the difference is exocortex WI-034 duplicating the census, which D6 already anticipates.
- **The digest constant wants a stated regeneration recipe** in `fixture_vault.py`'s docstring. The
  friction is the feature; being unable to discharge it legitimately is not.

### Suggested adjustments

- Reconsider the `## Approach` sentence that introduces `tests/fixtures/vault/`: it should state the
  flat single-directory layout and why (the repositories partition one directory by filename glob),
  because every one of AC-2, AC-3 and AC-4 reads that layout differently if it is left open.
- Amend AC-4's two legs to name the domain of each equality (per repository), and record the
  double-ownership of `malformed-frontmatter` and `unreadable` across the two `@*.md` repositories as
  declared expected behaviour rather than as a surprise the build discovers.
- Add the collision-vs-divergence question to the census's charge in `## Write Targets`, so the
  artifact rules on it rather than the builder.

Nothing else in the item needs to move. The problem statement is measured, D1's amendment is the
right call and is argued from the code rather than from taste, the precondition fence is correctly
placed at exploring, and the five criteria are unusually well-oracled for a draft. Two edits and this
is ready to spec.

```verdict
gate: architect
verdict: REVISE
date: 2026-09-06
model: claude-opus-5
targets: AC-4, AC-3, AC-2, #approach
prior: none
basis: original
findings: 2/6
note: The approach is sound and stands; AC-4 leaves the domain of its both-directions equality unstated and the corpus's flat-vs-nested layout is unstated, and the repositories' shared `@*.md` glob over one flat directory makes both decide whether AC-4 runs at all or passes vacuously.
```


## Architectural Review — 2026-09-06 (round 2)

**Recommendation: PROMOTE to architected**

### Trigger check

Same three as round 1 and all still fire: a new shared test surface every later item builds on
(`tests/fixture_vault.py` plus `tests/fixtures/vault/`); a new artifact convention
(`docs/vault-shape-census.md`, machine-read by AC-3); new persistent state in the repo (~50 committed
notes plus a frozen digest). Effort over a day. Review re-run in full against the seeded tree, not
merely diffed against the fold.

### Both blocking issues closed — verified arm by arm against the code, not against the fold's prose

**Blocking issue 1 (AC-4's unstated equality domain) — CLOSED.** AC-4 now declares
`{repository_type: {path: reason}}`, names the four repositories in scope, asserts each equality per
repository, and states the double-ownership as expected behaviour with a planted discriminator under
each owning glob plus book's asserted-empty mapping. I re-derived the rule the criterion now declares
and it is exactly what the code does, at every arm:

- `_owns(None)` returns `Path(self.file_pattern).stem != "*"` (`obsidian_schemas/repositories/base.py:258-265`).
  Person and company both inherit the default `@*.md` (`base.py:196-198`; I grepped the repositories
  package for `file_pattern` overrides — only `meeting.py:52-54` and `book.py:51-53` declare one, and
  `company.py` and `person.py` declare none), so `Path("@*.md").stem == "@*"` → owns. Meeting's
  `Path("Meeting *.md").stem == "Meeting *"` → owns, but its glob does not match `@<name>.md`. Book's
  `Path("*.md").stem == "*"` → declines, though its glob matches everything. The declared
  BOTH/NEITHER/ONLY pattern in AC-4 is correct as written.
- `FrontmatterParseError.declared_type` is `None` always (`obsidian_schemas/errors.py:65-67`), and a
  `UnicodeDecodeError` carries no such attribute — `_note_skip` reads it through
  `getattr(error, "declared_type", None)` (`base.py:268`), so both land on the `_owns(None)` arm.
  `SchemaDriftError` carries the note's own raw type (`errors.py:70-71`), so `_owns` compares it to
  `type_name` and exactly one repository records it.
- Meeting and book override `_load_file` but both end in `self._note_skip(file_path, e)`
  (`meeting.py:87-91`, `book.py:83-87`), so the skip surface is uniform across all four and the
  per-repository mappings AC-4 declares are all reachable.

**Blocking issue 2 (unstated on-disk layout) — CLOSED.** The `## Approach` now opens with the flat
single-directory rule, cites the glob partition, and carries both consequences forward: the four
repository-less types are AC-2's parser-level business and outside AC-4's counts, and the
collision-vs-divergence question is routed to the census. `## Write Targets` extends the census's
charge with that ruling in terms it can actually answer (do the vault's collisions co-occur with
stem/name divergence, and does divergence occur alone), and AC-3 now says plainly that eight classes
rather than nine is not a failure. The load-bearing claim behind all of it holds: `load()` calls
`self.vault_path.glob(self.file_pattern)` — non-recursive, one directory (`base.py:231`) — and
`save()` writes `self.vault_path / f"@{name}.md"` (`base.py:381-383`).

All four round-1 non-blocking notes are folded, and folded with their reasons rather than as
stipulations: the `unreadable` specimen's one viable spelling and the never-`chmod` rule are in
`## Approach` with the byte-scan consequence attached (`parser.py:238` really is an unwrapped
`read_text(encoding="utf-8")`); AC-2 names `write_markdown_file` as the gated door against
`write_frontmatter` as the bare serializer, which the code bears out — the gate call is
`writer.py:252-253`, above the lock, and `write_frontmatter` at `writer.py:134-157` is `yaml.dump`
and nothing else; the digest regeneration recipe is required in the module docstring; and D6's
re-entry no longer rides WI-030's premise.

### Review

**Fit.** Unchanged and still harmonizing. The four derived sweeps are this repo's standing move, and
the fold did not soften any of them — AC-2 still derives from `set(TYPE_TO_MODEL)` (8 members,
`models.py:309-318`), AC-4 still derives from `_skip_reason`'s codomain (`base.py:41-47`), and both
gained precision rather than latitude. The AC-2 narrowing arm is right against the code:
`ENTITY_BODY_CONFIG` declares five entries (`body_sections.py:303-324`) and `get_default_body`
returns `""` for anything absent (`:337-338`), so asserting that marker for `watch`, `explore` and
`gift-idea` is the honest oracle rather than an invented section list.

**Duplication.** Still none. No new surface was introduced by the fold; the manifest gained a key
shape, not a second home for anything.

**Boundaries.** The boundary round 1 said the design did not model — the repository glob partition —
is now modelled in three places that agree with each other: `## Approach`, AC-4's ownership rule and
AC-3's collision clause. Ownership across the artifacts is unchanged and clean: bytes own the
specimens, the manifest owns the oracle, the census owns the distribution.

**Determinism boundary (LLM vs code).** Unchanged and still correctly placed. The fold moved work
toward code, not away from it: the collision-vs-divergence class count is now a census RULING the
suite reads, and AC-4's ownership table is a declared mapping the test asserts rather than a builder's
inference.

**Reversibility.** Unchanged — additive, and AC-5 keeps the one irreversible edge (real data in git
history) machine-checkable.

**Generalization.** Unchanged. D6's amendment makes the deferral cheaper to reverse, not harder: it
now says in the document what would have to happen for the corpus to become a shared surface, rather
than implying an item that would carry it.

**Cost & maintenance.** The digest's recurring cost is now paid for by the required regeneration
recipe. No new recurring cost was introduced by the fold; AC-4's per-repository manifest is more
declaration to write once, not more to maintain.

**Build vs extend vs integrate.** Unchanged — build, with nothing to extend.

**Prior art (outside view).** Unchanged and still non-blocking: this builds no machinery around a
subtracted capability, and a frozen committed corpus plus a snapshot digest is the standard answer
(Go `testdata/`, pytest data directories, golden-file testing).

**LESSONS.** Re-checked #9 in the live log — it names `Sören Winter`, `José García`,
`Dave -> Thomas Gatten (Adzact)`, `Me to David Field` and says an Alice/Bob suite is green while
production mangles half its records, which is precisely what AC-3's per-specimen declared verdict
converts into a test. D1's amendment and D7's park still read correctly against #9 and #27. No scar
is re-incurred and the fold introduced none.

### Notes (non-blocking)

1. **AC-2(c) says "reproduces the note's frontmatter" without naming the KIND of equality, and the
   two candidate readings are not both satisfiable.** `model_to_frontmatter` emits every declared
   model field unconditionally, in definition order (`obsidian_schemas/writer.py:112-117`), and
   `write_frontmatter` re-serializes through `yaml.dump(..., sort_keys=False)`
   (`writer.py:152-157`) — so a fixture note that omits an optional field cannot round-trip
   BYTE-identically, while equality of the re-parsed frontmatter dict (or of the re-parsed model)
   round-trips cleanly. I am not blocking on it because both readings fail LOUDLY rather than passing
   vacuously — the byte reading goes RED on the first representative, so the build discovers it in a
   minute, not in a redesign — but the spec should name one, and note the tension if it picks bytes:
   a fixture hand-authored to match the writer's own canonical output is uncomfortably close to the
   generated-oracle shortcut AC-2(b) exists to forbid. The dict reading has neither problem.
2. **The gate is a pass-through for six of the eight types, so AC-2(c)'s write-door claim carries
   real weight for two of them.** `gate_write` returns `dict(introduced)` untouched for any declared
   type that is neither `person` nor `company` (`obsidian_schemas/name_gate.py:319-344`), and the
   company arm judges `name` only. So "leg (c) additionally proves the clean representatives are
   creatable through the real write door" is a substantive claim for the person and company
   representatives and a pass-through for `book`, `meeting`, `watch`, `explore`, `gift-idea` and
   `exploration`. Nothing is wrong — the criterion is satisfiable for all eight, and requiring
   gate-cleanliness of all eight representatives is harmless over-constraint — but the spec should
   not read the leg as eight proofs of the gate when it is two.
3. **AC-4(c)'s "declared loadable count" is neither the corpus size nor the glob-match count, and the
   third quantity has no name in the criterion yet.** A note under a repository's glob whose declared
   type is not that repository's raises NOTHING: `parse_to_model` returns `(None, frontmatter)` for
   an unowned type (`obsidian_schemas/parser.py:203-211`), so `_load_file` returns `None` with no
   skip recorded, and meeting/book short-circuit on `frontmatter.get("type")` before parsing at all
   (`meeting.py:79-81`, `book.py:74-76`). A flat corpus of ~50 notes therefore gives person a
   loadable count of "person-typed `@*.md` notes", not 50 and not the `@*.md` count — and the same
   note is invisible to person's skip surface, which is correct and is worth the manifest saying out
   loud so the count is declared rather than discovered.
4. **AC-3's both-directions equality is satisfiable by a census with zero class rows.** The exposure
   is bounded — AC-1(c) independently requires an arrow-connective and a path-hostile specimen to be
   present, so the corpus cannot become Alice and Bob by the census under-reporting — but the census
   charge in `## Write Targets` could cheaply say the artifact must account for at least the classes
   P10 already proves are in this tree, so "measured zero" is a finding the conductor has to write
   rather than a row that can be omitted.

### Notes on process

Advancing the stage is the conveyor's — `python src/stage_advancer.py advance WI-016 --to architected
--project <path> --actor architect`. I have edited no frontmatter and no `state/work-items.json`.

The item is ready to spec. Nothing above changes a premise, a criterion or the approach; all four
notes are things a spec-writer should carry, not things an explorer needs to go back and settle. The
census is still the outstanding precondition and Dave's AC sign-off is still ahead of the spec, both
exactly as `## Convergence` says.

```verdict
gate: architect
verdict: PROMOTE
date: 2026-09-06
model: claude-opus-5
note: Round 1's two blocking issues are closed and I re-verified the rule AC-4 now declares arm by arm against `_owns`/`_note_skip`/the four `file_pattern`s rather than against the fold's prose; the flat layout is stated with its glob reason, all four notes are folded, no premise moved and no criterion was weakened.
```


## Architectural Review — 2026-09-06 (round 3)

**Recommendation: REVISE — the approach is unchanged and still sound, and the red-team fold moved in
the right direction, but the machinery it added is not satisfiable as written and it re-opens the
leak path it was folded to close.**

### Trigger check

The same three fire and are unchanged by the fold: a new shared test surface every later item builds
on (`tests/fixture_vault.py` plus `tests/fixtures/vault/`); a new artifact convention
(`docs/vault-shape-census.md`, now machine-read by AC-3 *and* AC-5(c)); new persistent state in the
repo. Effort over a day. Review re-run against the seeded tree.

### What this round re-read, and what held

This is the round after an AC red-team REVISE, so the target is the material the fold ADDED — AC-5's
new legs (b) and (c), AC-3's tenth class, and the two obligations added to the census's charge in
`## Write Targets`. I re-verified that the fold disturbed nothing round 2 closed. AC-4 is untouched
and its ownership rule still matches the code arm for arm: `_owns(None)` returns
`Path(self.file_pattern).stem != "*"` (`obsidian_schemas/repositories/base.py:258-265`),
`_note_skip` reads `getattr(error, "declared_type", None)` (`base.py:268`),
`FrontmatterParseError.declared_type` is "always None — nothing was legible"
(`obsidian_schemas/errors.py:65-67`), and `SchemaDriftError` carries the note's own raw type
(`errors.py:70-71`). The flat-layout rule in `## Approach` is untouched. AC-1 and AC-2 are untouched.
No premise moved.

The fold's DIRECTION is right and I want that on the record before the findings: names are the
category `## Intent` names and the old AC-5 did not wall, a denylist of real names is correctly
rejected as being the leak it prevents, and closure-plus-recorded-provenance is the only structural
form available to a hermetic suite. Nothing below asks for a different mechanism. All three findings
are about the mechanism's declared membership rules being unsatisfiable or unbounded, and all three
have one-line fixes.

### Blocking issues

**1. AC-5(c) requires a zero-hit live-vault scan for every pool token, and AC-5(b) puts tokens in
that pool which occur in the live vault BY CONSTRUCTION — the wall names a target it makes
impossible.** AC-5(b) declares the identity pool as a flat set holding NAME tokens *and* CONNECTIVE
tokens, and names the connectives: `Me`, `to`, `->`, `Re`, `Fwd`. AC-5(c) then requires
`docs/vault-shape-census.md` to carry "one row per pool token" whose content is a non-occurrence scan
"showing zero hits as a name token anywhere in the vault", and the test asserts pool ⇄ table equality
both directions. Those two clauses cannot both hold. `Me` is a live stored-name form in this vault —
it is why `name_validation.py:241` carries `Me to David Field` as that branch's own specimen, and why
`name_cleaning.py:117` and `:54` strip `Me to X` and `Me → X` prefixes; AC-3 lists "`Me to ` prefixes"
as a corruption class precisely because the census will MEASURE it. So the conductor is charged with
recording a zero-hit scan for a token whose live count the same artifact is charged with reporting as
non-zero, and the only ways to discharge it are to write a false row or to drop the connective from
the pool — at which point AC-5(b)'s first direction goes RED on the `Me to ` specimen, which is a
required member. Two smaller arms of the same defect: `to` and `->` can never be produced by the
extractor AC-5(b) states (first character an uppercase or non-ASCII letter), so (b)'s second
direction — "every pool entry actually occurs somewhere in the reach" — is unsatisfiable for them
under the natural reading and silently means raw-substring under a second undeclared one. This is
LESSONS #31 at authoring time: an artifact naming targets the wall it quotes in the same document
makes impossible by construction, catchable now for one cheap REVISE and otherwise discovered by a
caged builder burning attempts against it. *Concrete fix:* split the pool into two declared sets
rather than one flat set with a type tag — a NAME pool, closed, whose domain is exactly the
extractor's output and each of whose members carries a census provenance row; and a CONNECTIVE set,
closed and small, carrying NO provenance obligation because non-identifying furniture is the point of
it, with its members exempted from the extractor's closure by name. AC-5(c)'s equality is then against
the NAME pool only.

**2. The PROSE allowlist is an unbounded second bucket carrying no provenance obligation, and it is
applied over the same undifferentiated byte scan as `name:` values and filename stems — so the exact
failure the red-team folded AC-5 to close walks back in one keystroke.** AC-5(b) asserts that every
extracted token "is in the pool or in a declared PROSE allowlist of the ordinary vocabulary the note
bodies and YAML keys need". Nothing constrains what may enter that allowlist, nothing requires the
census to certify it, and the scan does not distinguish WHERE a token sits. The red-team's own
scenario is therefore reachable again: a specimen carrying the live vault's real `name:` value goes
RED once, and the cheapest green — cheaper than the pool, which drags a conductor census row behind
it — is to add the surname to the allowlist. A real surname is not visibly out of place in a list
whose stated purpose is ordinary vocabulary. Two forces make that the path of least resistance rather
than a hypothetical. First, the reach was extended to `tests/fixture_vault.py` itself, which is a
Python module: every capitalized identifier in it is an extracted token (`Path`, `SkippedNote`,
`TYPE_TO_MODEL`, `NameGateRefusal`, `UnicodeDecodeError`, the `AC`/`RFC`/`WI` prose of the docstring),
and none of those is "note bodies and YAML keys" — so the allowlist's declared scope does not cover
the reach it is applied to and must grow large and heterogeneous on day one. Second, AC-5(b)'s own
exemption feeds it: the non-UTF-8 member's complete bytes are declared "as a hex literal", and an
uppercase-leading hex run is itself an extracted token with nowhere to go but the allowlist. A wall
whose bypass is larger, more heterogeneous and cheaper to extend than the wall is not closure. *Concrete
fix:* split the scan by POSITION rather than giving one undifferentiated byte scan two buckets.
Identity-bearing positions — filename stems, and the manifest's declared values for identity fields
(`name`, `aliases`, company/meeting title fields) — are asserted against the NAME pool ONLY, with no
allowlist reachable; free prose (note bodies, the module's docstrings and identifiers) gets the
allowlist, declared as a literal constant. That makes the escape hatch structurally unable to admit a
token into the field that carries identity, which is what finding AC-5 was about. The cheaper
alternative — putting the same census provenance obligation on the allowlist — collapses it into the
pool and should be named as rejected rather than left as the thing a builder discovers.

**3. `## Write Targets` and AC-3 now contradict each other on what a zero-measured class row does, and
the two readings differ on whether the criterion runs or is RED by construction.** The fold added to
the census's charge: "a class measured at ZERO is a row the conductor writes, not a row that may be
left out." AC-3 reads the class list from that artifact and asserts it EQUAL to the manifest's covered
classes both directions, with "a class in the census with no specimen is RED", and its test "asserts
its SHAPE — failing on a class row with no count, no command or no specimen". But AC-3 also says the
criterion is "never RED for holding nine classes rather than ten (or eight, if the address shape is
ruled absent too)" — which is only true if a ruled-absent class is NOT on the list the equality reads.
So a census that obeys `## Write Targets` and writes the zero row hands AC-3 a tenth class with no
specimen, which its own text says is RED twice over; a census that obeys AC-3 omits the row, which
`## Write Targets` forbids. This is the WI-144 shape the item has already been folded for once, and it
was introduced by the fold that closed the red-team's AC-3 finding — the finding's intent (the address
class cannot silently not-ship) is correct and I am not asking for it back. *Concrete fix:* give the
census's class table an explicit count and status per row, and state in AC-3 that its both-directions
equality is over rows with a specimen (equivalently, count > 0) while its shape assertion is per-row
conditional: a measured row must carry count, command and specimen; a zero row must carry count,
command and an affirmative absent ruling and must NOT carry a specimen. One sentence in each place and
both obligations survive intact.

### Review

**Fit.** Unchanged and still harmonizing — the four derived sweeps are this repo's standing move, and
the fold added a fifth derived closure (the pool) in the same idiom rather than a special case. The
findings above are about that closure's declared domains, not about the idiom.

**Duplication.** Still none. The fold introduced no second home for anything; the census gained a
table, not a competing oracle.

**Boundaries.** Ownership across the three artifacts is unchanged and clean — bytes own the specimens,
the manifest owns the oracle, the census owns the distribution — and AC-5(c) extends the census's
ownership to "which tokens are certifiably not real people", which is the right owner: it is the only
party that can read the live vault. Finding 2 is a boundary defect inside that split rather than a
challenge to it: the allowlist is a third, uncharted owner of the same question.

**Determinism boundary (LLM vs code).** Correctly placed and improved by the fold. The judgment
(which tokens are safe, which classes exist) is the conductor's recorded scan; the mechanical part
(is every token in the declared set, do the two declarations agree) is code. The item says plainly
where the machine stops and why — the suite is hermetic — instead of implying an in-suite proof it
cannot have. No mechanically-available value is left to LLM compliance.

**Reversibility.** Unchanged and high. Additive throughout. The one irreversible edge is real data in
git history, and the fold is a genuine reduction on it even in its current form — findings 1 and 2 are
about the wall being unsatisfiable and porous, not about it being absent.

**Generalization.** Unchanged. D5, D6 and D7 all still decline to generalize on measured grounds, and
the fold widened nothing.

**Cost & maintenance.** The fold adds one real recurring cost that is worth naming for the
spec-writer: the pool and its census provenance table are a two-artifact join that must be kept equal
by hand, and AC-5(c) makes an edit to either without the other RED. That is the intended friction and
it is proportionate, but it doubles the ceremony of adding a fixture note — which is a further reason
finding 2's cheaper bucket must not exist.

**Build vs extend vs integrate.** Unchanged — build, with nothing to extend.

**Prior art (outside view).** Non-blocking; unchanged. This builds no machinery around a subtracted
capability. Frozen corpus plus snapshot digest is the standard answer (Go `testdata/`, pytest data
directories, golden-file testing), and closure-against-a-declared-vocabulary is the standard answer
for scrubbing corpora where no reserved namespace exists.

**LESSONS.** #31 is the live one and finding 1 is squarely inside it — a wall named in the same
document as the targets it makes impossible, mechanically checkable at authoring time, not caught by
prose review at n=6 gate passes. #9 still reads correctly against D1's amendment and #27 against D7's
park; the fold re-incurs neither.

### Notes (non-blocking)

1. **AC-5(d) asserts a property of `normalize_phone` that the function does not have.** The leg reads
   "every reserved phone in the corpus still round-trips through `normalize_phone` to a well-formed
   E.164 value", but `normalize_phone` strips the JID suffix and then everything non-digit
   (`obsidian_schemas/phone_normalization.py:51-55`), so `+44 7700 900123` yields `447700900123` —
   digits, not E.164, which requires the leading `+`. Nothing in this package emits E.164. The leg's
   intent is sound and satisfiable as written for `phones_match` (`:58-90` handles the `44`/`0` and
   `1`/10-digit variants the reserved ranges will exercise); only the named output format is wrong,
   and it fails loudly on the first assertion, so I am not blocking. The spec should say "normalizes
   to a stable digits-only value and `phones_match` matches its `0`-prefixed and `+44`-prefixed
   variants".
2. **Round 2's notes 1, 2 and 3 are still open and still correctly non-blocking**, and the red-team
   fold did not touch them: AC-2(c)'s kind of equality (bytes vs re-parsed dict) is still unnamed, the
   gate is still a pass-through for six of eight types (`name_gate.py:319-344`), and AC-4(c)'s
   "declared loadable count" is still a third quantity distinct from corpus size and glob-match count.
   Carrying them forward so the fold's arrival does not bury them.
3. **AC-5(b)'s reach extension to `tests/fixture_vault.py` is the right call and should survive the
   fix to finding 2.** The manifest restates every specimen's field values as AC-2's declared oracle,
   so a wall over the corpus alone would miss a real name typed into the oracle. Whatever position
   split lands, the module stays in reach.

### Suggested adjustments

- Split AC-5(b)'s pool into a NAME pool (closed, extractor-domain-equal, one census provenance row
  each) and a CONNECTIVE set (closed, exempt, no provenance row), and scope AC-5(c)'s equality and
  zero-hit obligation to the NAME pool.
- Split AC-5(b)'s scan by position: identity-bearing positions against the NAME pool only, free prose
  against a declared literal allowlist, with the allowlist unreachable from a `name:` value or a
  filename stem.
- Add a count and status column to the census's class table in `## Write Targets`, and state in AC-3
  that the both-directions equality is over specimen-bearing rows while the per-row shape assertion is
  conditional on that count.

### Notes on process

Advancing the stage is the conveyor's — `python src/stage_advancer.py advance WI-016 --to architected
--project <path> --actor architect`. I have edited no frontmatter and no `state/work-items.json`, and
the stage stays at `idea` on this REVISE.

I raise no OPEN architectural question: every finding above carries its own concrete fix, none moves a
premise, none touches the approach, and none weakens a criterion. This is one fold from ready.

```verdict
gate: architect
verdict: REVISE
date: 2026-09-06
model: claude-opus-5
targets: AC-5, AC-3, #write-targets
prior: mixed
basis: folded-material
findings: 3/3
note: The red-team fold aims right but is unsatisfiable as written — AC-5(c) demands a zero-hit live-vault row for pool tokens like `Me` that the census must simultaneously measure as a live corruption class (LESSONS #31), AC-5(b)'s unbounded prose allowlist re-admits the very leak it folded to close, and `## Write Targets`'s new zero-row rule contradicts AC-3's equality and shape assertions.
```


## Architectural Review — 2026-09-06 (round 4)

**Recommendation: REVISE — all three of round 3's findings are closed and I verified each against the
code rather than the fold's prose. The approach is unchanged and still sound. But the fold's own
machinery has bred a fourth generation of membership defects, and this round I can name their
GENERATOR rather than only their instances: AC-5's two NON-VACUITY clauses require the corpus to
exercise every member of sets the builder does not author, and every declared set added since round 2
has produced at least one member it cannot exercise.**

### Trigger check

The same three fire, unchanged by the fold: a new shared test surface every later item builds on
(`tests/fixture_vault.py` plus `tests/fixtures/vault/`); a new artifact convention
(`docs/vault-shape-census.md`, machine-read by AC-3 and AC-5(c)); new persistent state in the repo.
Effort over a day. Review re-run against the seeded tree.

### What this round re-read, and what held

Round 3's three findings are CLOSED, each verified independently:

- **Finding 1 (pool split) — closed.** AC-5(b) now declares `NAME_POOL` and `CONNECTIVE_SET` as
  separate literal frozensets, AC-5(c)'s provenance obligation is scoped to `NAME_POOL` alone, and
  the two are asserted disjoint. `Me` no longer owes a zero-hit row it could never honestly carry —
  which the code still bears out: `name_validation.py:240-241` carries `specimen="Me to David Field"`
  on its `calendar_prefix` branch and `name_cleaning.py:55` strips `^(Me|My)\s+to\s+`, so `Me` is
  live vocabulary in this vault. The exclusion of `to`, `->` and `→` from the set, on the stated
  ground that the extractor cannot produce them, is the right reasoning — see blocking issue 1 for
  where that same reasoning was not carried through.
- **Finding 2 (allowlist bypass) — closed for the four fields it names.** The scan is now split by
  POSITION, `PROSE_ALLOWLIST` is explicitly not a term in the identity-position assertion, and it is
  asserted DISJOINT from the identity token set. I walked the red-team's scenario through the new
  wording: a real surname typed into a manifest `name` value goes RED on the identity assertion, and
  adding it to `PROSE_ALLOWLIST` then goes RED on the disjointness assertion. There is no route
  through for the fields the criterion lists. Blocking issue 3 is about a field it does not list.
- **Finding 3 (zero-row contradiction) — closed.** `## Write Targets` and AC-3 now agree through
  explicit `count`/`status` columns: equality over MEASURED rows only, per-row shape conditional on
  status, and the DRAFT CLASS FLOOR asserting presence at either status. The two obligations no
  longer contradict, and AC-3's `why:` states the reconciliation in the one place a future edit would
  have to break it.

Both round-3 non-blocking notes are folded correctly. AC-5(d) no longer claims E.164 — verified:
`normalize_phone` splits the JID suffix and then `re.sub(r"\D", "", phone)`
(`obsidian_schemas/phone_normalization.py:51-55`), so `+44 7700 900123` yields `447700900123` with no
leading `+`, and `phones_match`'s `44`/`0` and `1`/10-digit arms (`:76-88`) are exactly what the leg
now names. The non-UTF-8 member's hex literal is specified lowercase.

AC-1, AC-2 and AC-4 are untouched by this fold and I found no new issue in them. AC-4's ownership rule
still matches the code arm for arm (`repositories/base.py:258-265`, `:268`; `errors.py:65-67`,
`:70-71`). The flat-layout rule in `## Approach` is untouched. No premise moved, the approach is
untouched, and nothing below asks for a different mechanism.

### Blocking issues

**1. Three of `CONNECTIVE_SET`'s four members are grounded in nothing in this repository, and AC-5(b)'s
NON-VACUITY clause makes the corpus owe each of them an identity-position specimen.** AC-5(b) freezes
the set at exactly `{"Me", "Re", "Fwd", "Fw"}` and asserts that equality against the literal written
into the criterion, "so the set cannot grow without an AC change" — which means it cannot shrink
without one either. It then requires that "every `CONNECTIVE_SET` entry occurs as an extracted token
in at least one IDENTITY position." I grepped the whole tree for `Fwd`, `Fw:` and `Re: `: the only
occurrences anywhere are inside this document, and they entered it at line 924 — round 3's own
restatement of a then-draft list — not from the code. The package's actual connective vocabulary is
`Dave|Me|My` with `-`, `→` and ` to ` (`obsidian_schemas/name_cleaning.py:46,54,55`), matched by
`name_validation.py:217` (`Dave -> Thomas Gatten`), `:229` (`Dave - Thomas Gatten`) and `:241`
(`Me to David Field`). No Tier-1 branch refuses a mail-header prefix, no recovery regex strips one,
and no AC-3 draft class covers one — so no census row can MEASURE one. Failure scenario: the builder
must plant `Re:`-, `Fwd:`- and `Fw:`-prefixed values in identity positions to satisfy non-vacuity;
those specimens belong to no measured census class, which is the invented-specimen shape AC-3(i)'s
second direction exists to forbid ("a specimen belonging to no measured census class is RED") and the
D2 corpus-drawn-from-imagination this item rejects — or the builder leaves them out and goes RED on a
set that costs a re-sign to change, after Dave has signed. This is LESSONS #31 exactly: a wall the
spec names, whose membership is mechanically checkable at authoring time (one grep), passed through
three prose rounds. The same defect makes AC-5(c)'s `why:` false as written — it asserts "AC-3
requires the same census to report `Me to ` prefixes with a NON-ZERO count", but post-fold AC-3
permits any class to be ABSENT, so the exemption's stated ground is a guarantee AC-3 no longer gives.
*Concrete fix:* enumerate `CONNECTIVE_SET` from the package's own vocabulary (`Me`, `My`, and the
leading label of the calendar/arrow prefix forms if the corpus carries one), and state that each
member must be the leading token of a specimen belonging to a MEASURED census class — which makes
non-vacuity and AC-3(i) agree by construction instead of by coincidence.

**2. AC-5(c)'s pool equality is BOTH-DIRECTIONS across the conductor/builder ordering boundary, and
combined with non-vacuity it is RED with no in-cage fix.** `docs/vault-shape-census.md` is a
PRECONDITION: the conductor writes the pool table before origination, before the corpus exists.
`NAME_POOL` is declared by the caged builder. AC-5(c) asserts the two are "EQUAL both directions",
and AC-5(b) requires every `NAME_POOL` member to occur in an identity position. So the conductor must
predict the exact token set a build that has not happened yet will consume: certify one token more
than the corpus ends up using and the build is RED, with the only in-cage remedies being to invent a
note that consumes the surplus token (blocking issue 1's failure again) or to drop the row and break
the equality. Neither is available to a caged builder, so the real cost is a second conductor pass
mid-build — precisely the cost `## Write Targets` invokes the WI-281 shape to avoid, arriving through
a different door. *Concrete fix:* make the containment ONE-DIRECTIONAL — `NAME_POOL` ⊆ the census's
pool table — keeping non-vacuity over `NAME_POOL`, the per-row command/stdout shape assertion, and
the disjointness from `CONNECTIVE_SET`. Closure is not weakened by one byte: an uncertified token
still cannot enter an identity position, which is the whole property. A surplus certified row costs
nothing, because every row carries its own scan and a token nobody used is not a leak.
**The shared root, and the reason this round names a generator rather than three instances:** issues
1 and 2 are the same defect — a mandatory non-vacuity clause over a set the builder does not author.
Every declared set added since round 2 has produced at least one member the corpus cannot exercise
(`to`/`->`/`→` in round 3, `Re`/`Fwd`/`Fw` now), and each round has fixed the instance and kept the
generator. Dropping non-vacuity, or scoping it to sets the builder authors, closes the family; the
padded-pool risk it defends against is not a leak and is already priced by the per-token census scan.

**3. `Person.company` is outside the identity-position set, so a real employer name is greenable by
one `PROSE_ALLOWLIST` entry — round 3's finding 2, still open for the field most likely to be
transcribed alongside a real name.** AC-5(b) lists the identity fields as `name`, `aliases` and "the
company/meeting title fields". `Person` declares `name` (`obsidian_schemas/models.py:79`), `aliases`
(`:80`), `company` (`:84`) and `title` (`:85`), and a person note's `company:` carries a real
organisation's name — one that is itself an entity in this vault, with 2,159 live company notes per
`docs/company-name-corpus-audit.md`. Under the current wording it is a "non-identity frontmatter
value", i.e. a FREE-PROSE position, so a specimen copied from a live person note keeps its real
employer and the cheapest green is one allowlist entry, where an organisation name is not visibly out
of place. The asymmetry inside the same fold makes it plainer: a company note's own `name:` IS an
identity position and must be pool-drawn, while the identical string in a person's `company:` need
not be. AC-5(b) already defines `NAME_POOL` as including "company words", so the pool side is
designed for this and only the position list omits it. *Concrete fix:* add each note's declared
`company` value to the identity-position list. Do NOT add `Person.title` (`:85`) — it is a job title,
carries no identity, and forcing "Engineering" or "Director" into a pool that owes a zero-hit
live-vault row would manufacture blocking issue 1's shape on purpose.

**4. AC-3(ii) and AC-5(c) both require "non-empty stdout" from scans whose honest verbatim output on
a zero result is EMPTY, so the cheapest green is to type prose into a field labelled verbatim.**
AC-5(c) requires every pool row to carry "the command run and its verbatim stdout, showing zero hits",
and asserts "every row carries a non-empty command and a non-empty stdout". AC-3(ii) requires the same
of an ABSENT row — count exactly 0, non-empty command, non-empty stdout. A non-occurrence scan
(`rg <token> <vault>`) that finds nothing writes nothing to stdout and exits 1. So the honest capture
is empty and fails the assertion, and the available remedies are to record something that is not the
command's output — inside the artifact whose entire job is to be the trustworthy ledger — or to leave
the census RED for a build that cannot re-run it. It is satisfiable, but only by a command neither
criterion names. *Concrete fix:* one clause in `## Write Targets` requiring the recorded command to
emit a COUNT (so a zero result records verbatim as `0`), and the criteria then assert non-empty
stdout against a command that always produces some.

### Review

**Fit.** Unchanged and still harmonizing. The four derived sweeps remain this repo's standing move
(`tests/derivations.py` is the established home for the idiom), and the position split added by the
fold is a sharpening of the same closure pattern rather than a special case. All four findings are
about declared membership, not about the idiom.

**Duplication.** Still none. The fold introduced no second home for anything; `PROSE_ALLOWLIST` is a
third declared set but it is asserted disjoint from the other two and reachable from one position set
only, so it is a partition rather than a duplicate owner — which was round 3's finding 2 and is why
that finding is closed.

**Boundaries.** Ownership across the three artifacts is unchanged and clean. Blocking issue 2 is a
boundary defect of a kind this round is the first to see clearly: the census (conductor, pre-build)
and the manifest (builder, in-cage) are now joined by a both-directions equality, which is a two-way
coupling across a boundary that only carries traffic one way. Making it a containment restores the
direction the boundary actually has.

**Determinism boundary (LLM vs code).** Correctly placed and unchanged. The judgment (which shapes
exist, which tokens are safe) is the conductor's recorded scan; the mechanical part (is every token
in the declared set, do the declarations agree) is code. Blocking issue 4 is inside that split rather
than against it: it asks the mechanical assertion to be checkable against what the conductor's tool
actually emits.

**Reversibility.** Unchanged and high. Additive throughout, and the fold is a genuine reduction on
the one irreversible edge even in its current form — every finding above is about the wall being
unsatisfiable or one field short, not about it being absent.

**Generalization.** Unchanged. D5, D6 and D7 still decline to generalize on measured grounds and the
fold widened nothing.

**Cost & maintenance.** The two-artifact join's ceremony is now the item's dominant recurring cost,
and blocking issue 2's fix reduces it without weakening it: a containment lets the conductor certify
a slightly generous pool once, where a both-directions equality makes every corpus edit a paired edit
across a cage boundary. Worth taking for that reason alone.

**Build vs extend vs integrate.** Unchanged — build, with nothing to extend.

**Prior art (outside view).** Non-blocking and unchanged. This builds no machinery around a
subtracted capability; frozen corpus plus snapshot digest is the standard answer (Go `testdata/`,
pytest data directories, golden-file testing), and closure against a declared vocabulary is the
standard answer for scrubbing a corpus where no reserved namespace exists. The standard answer also
runs its closure one-directionally — a scrubbing allowlist certifies what may appear, it does not
require every certified term to appear — which is independent support for blocking issue 2's fix.

**LESSONS.** #31 is the live one for a second round running and blocking issue 1 is squarely inside
it: "a wall the spec can name is a wall the spec-time linter must check — prose review does not catch
the mechanically checkable class." `Re`/`Fwd`/`Fw` are checkable by one grep and survived three prose
rounds. #9 still reads correctly against D1's amendment and #27 against D7's park; the fold
re-incurs neither.

### Notes (non-blocking)

1. **`NAME_POOL` tokens must be CONSTRUCTED strings, not ordinary words, and the identity-position
   list makes that bite in places the spec has not yet noticed.** Every token in an identity position
   owes a zero-hit live-vault row, and identity positions now include meeting titles (via the
   filename stem with the `Meeting <date> - ` prefix stripped) and, if blocking issue 3 is taken,
   person `company:` values. A naturally-worded meeting title or a company name carrying `Ltd`,
   `Group` or `Team` will have a non-zero live count in a vault of 2,159 company notes — and
   `name_cleaning.py:58` treats exactly those as generic org suffixes. The same applies to the
   address-in-name-field specimen if the census measures it: its street and city words land in an
   identity position too. Saying so in the spec costs a sentence and saves the conductor authoring a
   pool row that cannot be written.
2. **AC-3's parenthetical mischaracterizes its own `rfc2822_leak` class against the code.** It says
   "the nearest, RFC 2822 leak forms, is email-header-shaped text like `Dave -> Thomas Gatten
   (Adzact)`" — but that string is the `calendar_prefix` branch's specimen
   (`obsidian_schemas/name_validation.py:216-217`), which AC-3 lists separately as "arrow-connective
   descriptors". The `rfc2822_leak` branch's own specimen is `Naomi Pavie naomipavieatspeechmaticscom`
   (`:204-205`) — an at-mangled address fused onto a name. The class list keeps them separate so no
   criterion is wrong, but the census will be authored against this prose and needs the right
   character profile. One incidental convenience worth keeping: that mangled run is lowercase, so it
   yields no extracted token and owes no pool row.
3. **Round 2's notes 1–3 remain open and remain correctly non-blocking**, untouched by this fold:
   AC-2(c)'s kind of equality (bytes vs re-parsed dict) is still unnamed, `gate_write` is still a
   pass-through for six of the eight types (`obsidian_schemas/name_gate.py:319-344`), and AC-4(c)'s
   "declared loadable count" is still a third quantity distinct from corpus size and glob-match
   count. Carrying them forward so four rounds of folds do not bury them.

### Suggested adjustments

- Drop AC-5(b)'s NON-VACUITY clause for `CONNECTIVE_SET`, or prune the set to members the package's
  own connective vocabulary grounds and tie each to a MEASURED census class.
- Make AC-5(c)'s pool relation a CONTAINMENT (`NAME_POOL` ⊆ the census pool table) rather than a
  both-directions equality, keeping non-vacuity over `NAME_POOL`, the per-row shape assertion and the
  disjointness from `CONNECTIVE_SET`.
- Add each note's declared `company` value to AC-5(b)'s identity-position list; leave `Person.title`
  out, and say why.
- Require in `## Write Targets` that every recorded scan command emit a count, so a zero result has a
  verbatim non-empty stdout.

### Notes on process

Advancing the stage is the conveyor's — `python src/stage_advancer.py advance WI-016 --to architected
--project <path> --actor architect`. I have edited no frontmatter and no `state/work-items.json`, and
the stage stays at `idea` on this REVISE.

I raise no OPEN architectural question: every finding carries its own concrete fix, none moves a
premise, none touches the approach, and none weakens a criterion — issues 2 and 3 make AC-5 both
cheaper and stricter at once. The reason I am not promoting with notes is the ordering the item
itself declares in `## Convergence`: Dave signs the criteria BEFORE the spec-writer runs, so this
gate is the last place a criterion can be edited for one line rather than a re-sign. That is the same
WI-281 economy `## Write Targets` and AC-3 both invoke in their own defence.

```verdict
gate: architect
verdict: REVISE
date: 2026-09-06
model: claude-opus-5
targets: AC-5, AC-3
prior: held
basis: folded-material
findings: 4/7
note: Round 3's three findings are closed and verified against the code, but AC-5's two NON-VACUITY clauses are the generator that keeps breeding them — `CONNECTIVE_SET` freezes `Re`/`Fwd`/`Fw`, which occur nowhere in this tree outside this document and which no Tier-1 branch, recovery regex or census class can ground (LESSONS #31), and AC-5(c)'s both-directions pool equality asks a pre-build conductor artifact to predict the caged builder's exact token set; separately `Person.company` (models.py:84) sits outside the identity positions so a real employer name is still greenable by one allowlist entry, and both criteria demand non-empty stdout from scans whose honest zero-hit output is empty.
```


## Architectural Review — 2026-09-06 (round 5)

**Recommendation: REVISE — one blocking finding, and the news that matters more than the finding is
what it is NOT.** Round 4's generator (a mandatory obligation over a set the builder does not author)
is GONE: I checked every declared set in the current draft for one and there is none left. The
falsification test the item wrote for its own recorded recommendation — "if a fifth independent round
finds a defect of the SAME family after this fold, the recommendation is wrong" — is passed. The one
blocking finding is the OTHER family round 4 opened and claimed to close in the same breath: AC-5(b)'s
identity-position enumeration is not the output of AC-5(b)'s own generating rule, in both directions,
and the direction that costs something is a live leak door on the one entity type this whole item
exists to stop being invisible. It is one line to fix, and this round closes the family by exhausting
`models.py` field by field below rather than naming the field and leaving the next reader to find the
one after it.

### Trigger check

The same three fire, unchanged by the fold: a new shared test surface every later item builds on
(`tests/fixture_vault.py` plus `tests/fixtures/vault/`); a new artifact convention
(`docs/vault-shape-census.md`, machine-read by AC-3 and AC-5(c)); new persistent state in the repo
(~50 committed notes plus a frozen digest). Effort over a day. Review re-run against the seeded tree.

### What this round re-read, and what held

Round 4's four findings are CLOSED, each verified against the code rather than against the fold's
prose:

- **Finding 1 (`CONNECTIVE_SET` grounded in nothing + non-vacuity over it) — closed, and closed at the
  generator.** The set is re-enumerated as `{"Me", "My", "Dave"}` and the non-vacuity clause is gone.
  The re-enumeration is right against the package: `_CALENDAR_PREFIX_RE` is
  `^(Dave|Me|My)\s*[-/]\s+` (`obsidian_schemas/name_cleaning.py:46`), `_ARROW_PREFIX_RE` is
  `^(Dave|Me|My)\s*[→⟶⇒➜↦⇨]\s*` (`:54`) and `_ME_TO_PREFIX_RE` is `^(Me|My)\s+to\s+` (`:55`) — the
  union of the three alternations is exactly `Dave|Me|My` and nothing else.
- **Finding 2 (both-directions pool equality across the conductor/builder ordering boundary) —
  closed.** AC-5(c) is now `NAME_POOL` ⊆ the census pool table, with the disjointness from
  `CONNECTIVE_SET` and the per-row command/stdout shape assertion kept. The direction now matches the
  direction the boundary carries.
- **Finding 3 (`Person.company` outside the identity positions) — closed for that field.**
  `models.py:84` is `company: str = ""` and `:85` is `title: str = ""`; the fold adds the first,
  excludes the second with the argument stated. Blocking issue 1 below is about the enumeration that
  fix generalized into, not about `company`.
- **Finding 4 (non-empty stdout demanded of scans whose honest zero output is empty) — closed at the
  cause.** `## Write Targets` now requires every recorded scan command to emit a count, and both
  criteria assert against that.

The derived org-suffix admission checks out as described: `_GENERIC_ORG_SUFFIXES` is exactly the eight
members named (`name_cleaning.py:58`) and the package compares against it at `:148`, `:185` and `:191`.
AC-1, AC-2, AC-3 and AC-4 are untouched by this fold and I found no new issue in them; AC-4's ownership
rule still matches the code arm for arm (`repositories/base.py:258-265`, `:268`; `errors.py:65-67`,
`:70-71`). No premise moved, the approach is untouched, and nothing below asks for a different
mechanism.

**And the generator is gone, which is the load-bearing check this round owed the item.** I went
through every set the criteria declare, asking only "does this impose an obligation on a set the
builder does not author": `NAME_POOL` — builder-authored, non-vacuity satisfiable by construction;
`CONNECTIVE_SET` — frozen by literal enumeration, obligation is a one-line equality against a literal
written in the criterion, no occurrence demanded; `PROSE_ALLOWLIST` — builder-authored, only a
disjointness constraint; `_GENERIC_ORG_SUFFIXES` — an ADMISSION, imposing nothing; the census pool
table and class table — conductor-authored, and both are now read by containment or by
status-conditional assertions rather than by an equality the other side must predict. There is no
fifth instance of the family. That is the item's own falsifiable claim, tested, and it holds.

### Blocking issues

**1. AC-5(b) states a generating rule and then enumerates a list the rule does not generate — in both
directions — and the omission direction is the allowlist-greenable leak door round 4's finding 3 was
about, one entity type over.** The rule is "a field is an identity position iff its value names a
PERSON or an ORGANISATION". The enumerated answer includes four fields that name neither
(`Book.title` `models.py:160`, `Watch.title` `:193`, `Explore.title` `:222`, `Exploration.title`
`:295` — a book, a film, a link and a living document are not people or organisations) and OMITS at
least one field that does, plus two the rule leaves undecided. This matters because AC-5(b) itself
instructs that "the list is reconciled against the schema BEFORE origination", i.e. a later reader
applies the RULE to the schema — and applying the rule as written deletes the four titles and adds
the omissions, so the criterion is buildable two ways by its own instructions (the WI-144 shape this
item has now been folded for twice).

The omission that costs something: **`Exploration.related` (`models.py:299`), whose own docstring at
`:280` says its members are `[[Other Exploration]], [[Person]], etc.`** — a frontmatter list the model
documents as holding person links. Under the current enumeration it is a non-identity frontmatter
value, i.e. a FREE-PROSE position, so a real contact's name written there goes RED once on the
free-prose leg and the cheapest green is one `PROSE_ALLOWLIST` entry — no `NAME_POOL` membership, no
census provenance row, no disjointness violation, because the token never enters an identity position.
That is precisely the escape hatch AC red-team rounds 1 and 2 and architect rounds 3 and 4 exist to
close. The failure scenario is not hypothetical for this corpus specifically: AC-2 derives its sweep
from `set(TYPE_TO_MODEL)` (`models.py:309-318`), `exploration` is a member, and the item's own
`## Problem / Motivation` P4 says `exploration` has zero test references anywhere — so the corpus is
GUARANTEED to contain a hand-authored exploration note, authored from a live-vault shape, by an author
with no fixture of that type to copy from. `related:` is the field that note's shape hangs on.

Two more the rule does not decide, and undecided is what produced this finding in the first place:
**`Watch.streaming_service` (`:199`)** names an organisation as squarely as `Book.publisher` (`:166`)
does, and `publisher` is on the list while `streaming_service` is not — the same value kind, opposite
answers, in the same enumeration. **`GiftIdea.source` (`:243`)** is the unglossed sibling of
`Explore.source` (`:224`, glossed "where you found it / who mentioned it"), which IS on the list; the
gift-idea template's `source:` (`:236`) plausibly carries who suggested it. And one door the
enumeration cannot reach at all: `model_config` sets `extra="allow"` (`models.py:31-32`), so a fixture
note may carry undeclared frontmatter keys whose manifest-declared values are, under the current
wording, free prose by default — a `manager:` or `introduced_by:` key on a schema-drift specimen is
the same door again.

*Concrete fix, and it is one edit to one criterion:* add `Exploration.related` (`:299`) to the
identity-position list; rule on `Watch.streaming_service` (`:199`) and `GiftIdea.source` (`:243`) by
either listing them or giving each the one-line exclusion argument the list already carries for
`Person.title` and `Meeting.topics`; state that any manifest-declared value for an undeclared
(`extra="allow"`) key is an identity position unless the manifest declares it prose; and reconcile the
rule with the four `title` fields — either widen the rule (e.g. "…names a PERSON or an ORGANISATION,
or is a free-text field the corpus author writes and a real one could carry one") or say plainly that
the four titles are deliberate over-constraint, so the pre-origination reconciliation does not delete
them on the rule's authority. The full field-by-field pass is below so this fold has nothing left to
discover.

**The complete reconciliation, so this family closes the way round 4 closed the other one.** Every
declared field of every member of `TYPE_TO_MODEL`, read off `models.py`, with its classification under
the stated rule. `BaseEntity`: `type` `:39`, `tags` `:40` — neither. `Person`: `name` `:79` ID,
`aliases` `:80` ID, `emails` `:81` / `phones` `:82` / `whatsapp` `:83` / `linkedin` `:86` / `slack`
`:87` → leg (a)'s reserved-range wall, `company` `:84` ID, `title` `:85` excluded (argued),
`roles` `:88`, `birthday` `:89`, `created` `:90` — none. `Company`: `name` `:128` ID, `website` `:129`
/ `linkedin` `:131` → leg (a), `industry` `:130` NOT identity (a sector word; forcing it in
manufactures the unsatisfiable-row shape), `created` `:132`. `Book`: `title` `:160` (see the rule
question), `author` `:161` ID, `publisher` `:166` ID, `isbn` `:165` / `source_url` `:168` → leg (a),
`description` `:162` prose, `status` `:163` / `rating` `:164` / `publication_year` `:167` /
`date_added` `:169` / `date_finished` `:170` — none. `Watch`: `title` `:193` (rule question),
`director` `:195` ID, `recommended_by` `:200` ID, **`streaming_service` `:199` ORG — unlisted**,
`media_type` `:194` / `year` `:196` / `status` `:197` / `rating` `:198` / `date_added` `:201` /
`date_watched` `:202` — none. `Explore`: `title` `:222` (rule question), `source` `:224` ID, `url`
`:223` → leg (a), `subtype` `:221` / `status` `:225` / `created` `:226` — none. `GiftIdea`:
`for_person` `:242` ID, **`source` `:243` undecided**, `date_added` `:244` — none. `Meeting`: `date`
`:260`, `attendees` `:261` ID, `topics` `:262` excluded (argued), `meeting_id` `:263`. `Exploration`:
`title` `:295` (rule question), **`related` `:299` ID — unlisted, docstring `:280`**, `origin` `:300`
("What sparked this — problem, article, conversation", `:281`) — free text that can name a person and
wants an explicit ruling, `graduated_to` `:301` (`[[Project]]` — not a person or an organisation,
excludable in one line), `status` `:296` / `created` `:297` / `updated` `:298` / `abandoned_reason`
`:302` — none. That is the whole surface; there is no ninth model file (`models.py` is the single home
CLAUDE.md declares).

### Review

**Fit.** Unchanged and still harmonizing. The four derived sweeps remain this repo's standing move
(`tests/derivations.py` is the established home for the idiom), and nothing in the fold introduced a
special case. The finding is about one criterion's declared membership, not about the idiom.

**Duplication.** Still none. The fold removed machinery rather than adding a surface — one clause
deleted, one equality weakened to a containment, one hand-declared set replaced by a package-derived
admission. There is no second home for anything.

**Boundaries.** Improved by this fold and clean. The conductor/builder boundary now carries traffic in
the direction it actually has (containment, not equality), which was round 4's blocking issue 2, and
the census/manifest/bytes ownership split is unchanged: bytes own the specimens, the manifest owns the
oracle, the census owns the distribution and the "certifiably not a real person" ruling. Blocking
issue 1 is inside the manifest's own declared surface, not a boundary dispute.

**Determinism boundary (LLM vs code).** Correctly placed and unchanged. Judgment (which shapes exist,
which tokens name nobody) is the conductor's recorded scan; the mechanical part (is every token in the
declared set, do the declarations agree, does the digest hold) is code. Blocking issue 1 is squarely
on the mechanical side — which field is an identity position is decidable by reading `models.py`, and
this fold is the second to decide it by prose rather than by exhausting the file.

**Reversibility.** Unchanged and high. Additive throughout, and AC-5 keeps the one irreversible edge
(real data in permanent git history) machine-checkable. The finding is that one door into that edge is
still unwalled, not that the wall is absent.

**Generalization.** Unchanged. D5, D6 and D7 still decline to generalize on measured grounds
(`pyproject.toml:38-39` packages `obsidian_schemas` only, so nothing under `tests/` is importable by a
consumer), and this fold widened nothing.

**Cost & maintenance.** Genuinely reduced by this fold, which is worth recording because four rounds
of hardening had been pushing it the other way: the containment removes the paired-edit-across-the-cage
ceremony that round 3 named as the item's dominant recurring cost, and the dropped non-vacuity clause
removes an obligation the builder could not discharge. AC-5 now demands strictly less than it did at
round 2 and points it at strictly more precise places.

**Build vs extend vs integrate.** Unchanged — build, with nothing to extend. P1/P2 measure zero
fixture data files and no `conftest.py` anywhere.

**Prior art (outside view).** Non-blocking and unchanged. This builds no machinery around a subtracted
capability; a frozen committed corpus plus a snapshot digest is the standard answer (Go `testdata/`,
pytest data directories, golden-file testing), and closure against a declared vocabulary is the
standard answer for scrubbing a corpus where no reserved namespace exists. The standard answer also
runs its closure one-directionally, which is what this fold adopted.

**LESSONS.** #31 is the live one for a third round running, and blocking issue 1 sits exactly in its
statement — "a wall the spec can name is a wall the spec-time linter must check; prose review does not
catch the mechanically checkable class" (LESSONS.html:597). Which fields carry a person or an
organisation is answerable by one field-by-field read of one file, and a round that announced it had
done that read produced a list that is neither its rule's output nor complete. That is why this round
prints the whole reconciliation rather than the missing field. #9 still reads correctly against D1's
amendment (`realdata`, LESSONS.html:269) and #27 against D7's park (`corpustool`, `:549`); the fold
re-incurs neither.

### Notes (non-blocking)

1. **Two small cite inaccuracies inside AC-5(b), both harmless to the set but worth correcting before
   Dave signs, because the criterion's authority is that it was read off the code.** It says
   `name_cleaning.py:46`, `:54` and `:55` "all match `(Dave|Me|My)`" — `:55` (`_ME_TO_PREFIX_RE`)
   matches `^(Me|My)\s+to\s+` only, no `Dave`; the union across the three is still exactly the set
   declared, so the set is right and only the sentence is wrong. And it says the package compares
   `_GENERIC_ORG_SUFFIXES` "casefolded" at `:148`, `:185`, `:191` — the package uses `str.lower()` at
   all three. For the eight ASCII members `lower` and `casefold` agree, but the corpus deliberately
   carries non-ASCII specimens, so the criterion should name the operation its own test performs
   rather than describe the package's as something it is not.
2. **The derived org-suffix admission has one property a frozen set does not, and it should be
   acknowledged rather than discovered.** Reading the admission from `name_cleaning._GENERIC_ORG_SUFFIXES`
   (`:58`) correctly stops a builder padding it — that was the point — but it also means a future
   edit to a name-CLEANING set silently widens a PRIVACY wall, made by someone who is not thinking
   about this corpus and with no AC change. It is small (the members are org suffixes by construction
   and the file's own tests constrain them) and I am not blocking on it, but one sentence in
   `fixture_vault.py`'s docstring pointing at `name_cleaning.py:58` as a load-bearing dependency of
   AC-5 costs nothing and is what a reader of that file in six months needs.
3. **Round 2's notes 1–3 remain open and remain correctly non-blocking**, untouched by this fold and
   carried forward for a fifth round so they are not buried: AC-2(c)'s kind of equality (bytes vs
   re-parsed dict) is still unnamed; `gate_write` is still a pass-through for six of the eight types
   (`obsidian_schemas/name_gate.py:319-344`), so AC-2(c)'s write-door claim is substantive for two
   representatives and nominal for six; and AC-4(c)'s "declared loadable count" is still a third
   quantity distinct from corpus size and glob-match count (`parser.py:203-211` returns
   `(None, frontmatter)` for an unowned type with no skip recorded).
4. **On the sufficiency question recorded for Dave: the evidence now favours keeping the structural
   wall, and this round is the test the item asked for.** The item wrote its own falsification
   condition — a fifth independent round finding a defect of the SAME family means take the fallback.
   I looked for one specifically and there is none: the generator is gone, and AC-5 is smaller and
   more precise than at any point since round 1. What this round found is a different and shallower
   class — an enumeration that does not match its own rule — whose fix is finite and, with the full
   reconciliation above, exhausted rather than sampled. That is ordinary criterion review, which is
   the branch the item's own recommendation says to continue on. Dave still owns the ruling; this is
   the datum it asked for.

### Suggested adjustments

- Add `Exploration.related` (`models.py:299`) to AC-5(b)'s identity-position list, and rule explicitly
  on `Watch.streaming_service` (`:199`), `GiftIdea.source` (`:243`), `Exploration.origin` (`:300`) and
  `Exploration.graduated_to` (`:301`) — list them or give each the one-line exclusion argument
  `Person.title` and `Meeting.topics` already carry.
- Say how a manifest-declared value for an undeclared frontmatter key is classified, given
  `extra="allow"` (`models.py:31-32`).
- Reconcile the rule with the four `title` fields: widen the rule's wording or state that they are
  deliberate over-constraint, so the declared pre-origination reconciliation does not delete them on
  the rule's own authority.
- Fix the two cites in note 1 while the criterion is still a draft.

### Notes on process

Advancing the stage is the conveyor's — `python src/stage_advancer.py advance WI-016 --to architected
--project <path> --actor architect`. I have edited no frontmatter and no `state/work-items.json`, and
the stage stays at `idea` on this REVISE.

I raise no OPEN architectural question. The single finding carries its own concrete fix and its own
exhaustive reconciliation, no premise moved, the approach is untouched, and nothing is weakened —
the fix makes AC-5 stricter in one field and no more expensive anywhere. The reason this is REVISE
rather than PROMOTE-with-a-note is the ordering the item declares in `## Convergence`: Dave signs the
criteria before the spec-writer runs, so this gate is the last place a leak door in a signed criterion
costs one line instead of a re-sign — the same economy that made round 4's `Person.company` finding
blocking, applied consistently to the field it missed.

```verdict
gate: architect
verdict: REVISE
date: 2026-09-06
model: claude-opus-5
targets: AC-5
prior: held
basis: folded-material
findings: 1/3
note: Round 4's four findings are closed and its generator is verifiably gone (no declared set now carries an obligation the builder cannot author, so the item's own falsification test passes), but AC-5(b)'s identity-position enumeration is not its own generating rule's output in either direction — it omits `Exploration.related` (models.py:299, docstring :280 says `[[Person]]`) on the one type the corpus is guaranteed to carry and that AC-2 exists to un-blind, leaving a real name there greenable by a single `PROSE_ALLOWLIST` entry, and it leaves `Watch.streaming_service`, `GiftIdea.source` and `extra="allow"` keys undecided while including four media-title fields the rule excludes; the full field-by-field reconciliation is in the section so this fold exhausts the family rather than patching one field.
```


## Architectural Review — 2026-09-07 (round 7)

**Recommendation: REVISE — one blocking finding, and it is the THIRD instance of the family the
document itself named as its own falsification signal. The approach is untouched and sound for a
seventh round; the finding is in AC-3's class floor, not in AC-5.**

Round 6's finding is closed and I verified the closure against the code rather than against the
fold's prose. But the same fold that exhausted the furniture surface (P16) also patched AC-3's DRAFT
CLASS FLOOR by NAMING the two branches that round happened to read, and stated a count for that
floor which is wrong by two. The floor still omits `calendar_prefix` — a live person Tier-1 branch
with its own `branch_id`, its own specimen, its own dedicated recovery arm, and the sole source of
`CONNECTIVE_SET`'s `Dave` member — plus three more. This is the second family (an enumeration that
is not its own stated rule's output) recurring for the third consecutive round, this time over a
surface this document explicitly claims to have exhausted. I report that plainly because the
document staked Dave's pending ruling on exactly this predicate; I do not rule on it, and I note
below the one respect in which the datum is weaker than it looks.

### Trigger check

The same three fire, unchanged by the sixth fold: a new shared test surface every later item builds
on (`tests/fixture_vault.py` plus `tests/fixtures/vault/`); a new artifact convention
(`docs/vault-shape-census.md`, machine-read by AC-3 and AC-5(c)); new persistent state in the repo
(~50 committed notes plus a frozen digest). Effort over a day. Review re-run against the seeded tree.

### What this round re-read, and what held

Round 6's blocking finding is **closed**, and the resolution it chose — pin the extraction rule
first, then apply it — is the right one. Verified against the code, not the fold:

- The pinned run rule is stated in AC-5(b) with four worked consequences, and it does decide
  `zArchived`: `_ARCHIVE_PREFIX_RE` is `^z+Archived\s*-\s*` (`name_cleaning.py:56`) and
  `^z+Archived\b` (`name_validation.py:110`), so the literal the criterion extracts from is one
  lowercase-initial run and yields no token. `CONNECTIVE_SET` correctly does not gain `Archived`.
- P16's central claim is TRUE where it matters: I grepped every `re.compile` in `obsidian_schemas/`
  and there is no third furniture table and no other recovery regex. The only compiled patterns
  outside `name_validation.py`/`name_cleaning.py` are `body_sections.py:36`, `:360`,
  `name_gate.py:90` and `repositories/person.py:114`, none of which carries a capitalized furniture
  literal. The union `{Dave, Me, My}` stands.
- The `unknown_contact` cell is genuinely undecided by the code, as stated: `:113` carries
  `re.IGNORECASE` and this repo commits both casings. Giving it AC-3's one-time pre-origination
  reconciliation rather than a guess is correct, and it adds no obligation over a set the builder
  does not author — round 4's generator stays gone. I looked for a fifth instance of it specifically
  and there is none.
- The two round-2 notes this fold closed are closed correctly and I checked both cites. AC-2(c)'s
  named equality (re-parse and compare to the manifest's declared mapping, never byte-equality) is
  the right call, and AC-2's claim about `gate_write` is exactly right at its stated size:
  `name_gate.py:319-344` returns `dict(introduced)` for every declared type that is neither person
  nor company, with the company arm calling `validate_strict` against `COMPANY_TIER1_BRANCHES` for
  its raise behaviour at `:329-343`. `write_markdown_file` is the gated door as claimed —
  `writer.py:252-253` calls `gate_write(fm, declared_type=fm.get("type"), ...)`.
- AC-4(c)'s disposition (a declared loadable count IS a third quantity, and that is the criterion
  working) is right and I am not re-raising it. AC-1, AC-2 and AC-4 drew no finding from me.

No premise moved, and nothing below asks for a different mechanism, a different layout, or a
weaker criterion.

### Blocking issue

**1. AC-3's DRAFT CLASS FLOOR is hand-listed against a surface that is an iterable declaration with
unique ids — it omits `calendar_prefix` and three more, and the fold's own count of what it covers
is wrong by two.**

`TIER1_BRANCHES` (`obsidian_schemas/name_validation.py:190-309`) is a tuple of records whose
`branch_id` is, per the dataclass docstring at `:152`, "the sweep's unit and is unique in the
tuple". Its ten ids are `email_chars` (`:192`), `rfc2822_leak` (`:203`), `arrow_connective`
(`:215`), `calendar_prefix` (`:227`), `me_to_prefix` (`:239`), `path_hostile` (`:250`),
`archive_prefix` (`:261`), `unknown_contact` (`:272`), `pure_digit` (`:284`) and `empty` (`:301`);
`COMPANY_TIER1_BRANCHES` (`:371-437`) adds none that is new (`email_chars` `:373`,
`arrow_connective` `:385`, `path_hostile` `:398`, `archive_prefix` `:414`, `empty` `:429`).

AC-3's floor, after round 6's fold, maps to **six** of those ten — `rfc2822_leak`,
`arrow_connective`, `me_to_prefix`, `path_hostile`, `archive_prefix`, `unknown_contact` — and its
other six entries (diacritics, hyphenated surnames, whitespace damage, stem/name divergence,
same-name collision, postal-address leak) are shape classes with no branch at all. AC-3's `why:`
states that before the fold the floor "was listing eight of the ten live person Tier-1 branches
while omitting exactly the two whose furniture the AC-5(b) enumeration had also sampled past". It
was listing four. The omitted ids are `calendar_prefix`, `email_chars`, `pure_digit` and `empty`.

`calendar_prefix` is the one that bites, on three independent grounds. It is not a merge of a
listed class and the document knows it: AC-3's own parenthetical says "the arrow/calendar specimens
`Dave -> Thomas Gatten` and `Dave - Thomas Gatten` (`:214-229`) are the separate arrow-connective
and calendar-prefix classes" — it names the class as separate in the same criterion that omits it
from the floor, which is the WI-144 shape inside one criterion. It is a branch with a dedicated
recovery arm (`name_cleaning.py:46`, stripped at `:121`), which was round 6's own stated ground for
adding the other two. And it is the branch that produces `Dave`, one of `CONNECTIVE_SET`'s three
frozen members: AC-5(b) justifies that member as "live prefix vocabulary this vault actually
produces" and cites `:226-236`'s `Dave - Thomas Gatten` for it, while AC-3 lets the class that
produces it silently not-ship. The specimen `Dave - Naomi Pavie` is also one of the forms LESSONS #9
names by name and one of P10's 35 scattered literals — the corpus's whole reason to exist.

*Failure scenario, in the floor's own terms.* The floor is assertion (iii), "the machine-checked
form of `## Write Targets`'s 'a class measured at ZERO is a row the conductor writes'". A conductor
censuses the vault, records rows for the eleven classes the floor names, and does not think to
measure `Dave -`/`Me -`/`My -` calendar prefixes as a class distinct from arrows. Assertion (iii)
passes (all listed ids present), assertion (i) passes (the manifest covers exactly the MEASURED
rows), assertion (ii) passes (every row well-formed), AC-5 passes, the floor runs green — and the
corpus ships with no calendar-prefix specimen, which is precisely the "shape Dave asked for
silently never ships" outcome assertion (iii) was added to make impossible. The same route is open
for `pure_digit` (a phone string stored as a name — the WI-083 sentinel shape, `specimen=`
`447700900123` at `:284-294`, which is also the exact reserved range AC-5(a) mandates), for
`email_chars`, and for `empty`.

*The root, and it is the family rather than the four ids.* Every other totality claim in this item
is DERIVED from the class's own declaration — AC-2 from `set(TYPE_TO_MODEL)`, AC-4 from
`_skip_reason`'s codomain — and `## Where the structure lives` states that as the item's governing
idea ("every criterion below is a derived sweep with a declared oracle rather than a bigger pile of
fixtures"). AC-3's floor is the one enumeration still hand-maintained against a surface that is
enumerable at runtime, and it has now been corrected by hand twice (round 3 added it, round 6 added
two ids) and been wrong both times. Round 6 read the whole branch table to fix `CONNECTIVE_SET` and
still patched the floor by naming two branches out of that read — which is why "read the surface
exhaustively this round" has not stopped the family recurring: the surface gets exhausted, the
enumeration stays hand-copied, and the next round finds the next gap.

*Concrete fix, and it removes the generator rather than pruning instance three.* Split AC-3's floor
in two and derive the half that can be derived: (1) assert that the census class table carries a row
of EITHER status for every `branch_id` in `TIER1_BRANCHES` ∪ `COMPANY_TIER1_BRANCHES`, read from the
package at test time exactly as AC-2 reads `TYPE_TO_MODEL` — so a branch added to the package later
joins the floor automatically and no future round can find the floor sampling the branch table;
(2) keep the hand-listed floor for the six shape classes that have no branch, where there is no
declaration to derive from and the list is the only available statement of intent. Two things make
this satisfiable rather than a new obligation: the MEASURED/ABSENT status split round 3 introduced
already lets a branch the live vault does not carry (plausibly `empty`) discharge as an ABSENT row
with its count, command and stdout, so nothing is forced to have a specimen; and derive from
`branch_id`, NOT from `pattern`, because three branches deliberately share the raised pattern
`calendar_prefix` (`:216`, `:228`, `:240` — the dataclass docstring at `:152-154` says so
explicitly), and a pattern-keyed floor would silently re-merge the three classes AC-3 says are
separate.

*Cost of not doing it now:* the floor is reconciled against the census before Dave signs. One line
of criterion text today versus a signed AC re-grounded after origination — which is LESSONS #45's
scar verbatim ("the already-signed AC-4 fixture re-grounded from three members to four, a full D4b
re-sign").

### Review

**Fit.** Still harmonizing, and the fix moves WITH the grain rather than against it: deriving the
floor from `TIER1_BRANCHES` is the same move AC-2 makes on `TYPE_TO_MODEL` and AC-4 on
`_skip_reason`, and `tests/derivations.py:1-22` remains the repo's standing home for the idiom. The
derivation here is a runtime read of an exported tuple, not a syntax scan, so it neither needs nor
may name `ast` (P9's single-homing wall, `tests/test_name_gate_wall.py`).

**Duplication.** Still none. Nothing in the tree materializes a vault from committed bytes; the nine
private helpers P3 counts all synthesize. The fix adds no surface — it replaces eleven hand-typed
ids with a read of a tuple the package already exports.

**Boundaries.** Clean and unchanged: bytes own the specimens, the manifest owns the oracle, the
census owns the distribution and the not-a-real-person ruling. The finding is inside AC-3's own
declared surface. Worth noting the fix IMPROVES a boundary: today the floor asks the conductor to
know the package's branch table from a list a gate transcribed; derived, the package tells the
suite what the population is and the conductor only measures it.

**Determinism boundary (LLM vs code).** Correctly placed everywhere else, and the finding is exactly
a case of it landing on the wrong side. Which corruption classes the package declares is
MECHANICAL — `TIER1_BRANCHES` is an iterable with unique ids sitting in the tree — and it is being
carried by a human-transcribed list in a criterion, which is why three consecutive folds have
mis-transcribed it. Judgment (which shapes the live vault actually holds, at what frequency, and
what a faithful pseudonymous specimen is) correctly stays with the census.

**Reversibility.** Unchanged and high. Additive throughout; AC-5 keeps the one irreversible edge
(real data in permanent git history) machine-checkable. This finding opens no leak — it closes a
route to a green floor over an incomplete corpus, so it is a coverage finding, not a privacy one.

**Generalization.** Unchanged and right-sized. D5, D6 and D7 still decline to generalize on measured
grounds (P8: `pyproject.toml:38-39` packages `obsidian_schemas` only). The fix generalizes exactly
one enumeration and nothing else.

**Cost & maintenance.** The fix REDUCES recurring cost: a hand-listed floor is a paired edit every
time the package gains a branch, and deriving it is the edit that stops. The digest-regeneration
recipe (round 1's note) is folded and stands.

**Build vs extend vs integrate.** Unchanged — build, with nothing to extend. P1/P2 still measure
zero fixture data files and no `conftest.py` anywhere in the tree.

**Prior art (outside view).** Non-blocking and unchanged. Nothing here builds machinery around a
subtracted capability: a frozen committed corpus plus a snapshot digest is the standard answer (Go
`testdata/`, pytest data directories, golden-file testing), and deriving a coverage floor from the
producer's own registry rather than from a hand list is likewise the standard answer, not a
divergence needing a cited execution.

**LESSONS.** #45 is the live one and it is on point rather than adjacent: "a registry validated only
against itself is a mirror, not a census — when a registry claims to enumerate a population, ship
the reality-diff as a floor check: derive the actual population from the source and assert
set-equality with the registry". AC-3's class floor is precisely such a registry, claiming to
enumerate the package's refusal surface, validated so far only by gates re-reading it. #44 is its
neighbour and also applies — a wall's reach is only the shapes its matcher was tested against. #9
still reads correctly against D1's amendment, #27 against D2's rejection and D7's park, and #31
against the item's derive-don't-describe discipline. The fix re-incurs none of them; the current
floor re-incurs #45.

### Notes (non-blocking)

1. **`re.IGNORECASE` is on eight of the sixteen regexes, not on one, so AC-5(b)'s "the ONE branch
   whose answer the code does not settle" is too narrow as a statement of fact — though the fold's
   general remedy already covers the consequence.** Verified: `name_cleaning.py:46`, `:54`, `:55`,
   `:56`, `:57` ALL carry `IGNORECASE`, and so do `name_validation.py:82` (`_ME_TO_PREFIX_RE`),
   `:110` and `:113`; `name_validation.py:74` (`_CALENDAR_PREFIX_RE`) does NOT. So the code no more
   pins the live casing of `Me`/`My`/`Dave` furniture than it pins `unknown contact`'s. The reason
   this is a note and not a finding is that the fold's remedy is already general — AC-5(b) says "the
   same reconciliation runs for any other furniture class whose measured profile would put a
   capitalized non-name run into an identity position", and `## Write Targets` requires the census to
   record EACH class's furniture literal in its measured casing — so an `ME - X` or `DAVE / X`
   measured form is absorbed at the same one-time reconciliation. And by the fold's own evidentiary
   method the cells are settled in practice: every committed specimen for these three branches in
   this tree spells them `Dave`/`Me`/`My`, with no `ME`/`DAVE` variant anywhere, which is the
   opposite of what P15 found for `unknown_contact`. Worth one clause in P16 recording which regexes
   carry the flag, so a later reader is not told the residue is a single cell when it is eight.
2. **P16's arithmetic is off by one and the enumeration under it is complete.** It says "fifteen
   regexes in two files — the ten in `name_validation.py` and the five in `name_cleaning.py`" and
   then correctly lists **eleven** for `name_validation.py` (`:66`, `:74`, `:82`, `:101`, `:107`,
   `:110`, `:113`, `:120`, `:123`, `:351`, `:445`), so the true count is sixteen. The union answer is
   unaffected. Fixing the number matters only because a later reader checking "is this surface
   exhausted?" counts the list against the stated total.
3. **Nothing in `obsidian_schemas/` outside the two named files carries furniture, and it is worth
   recording as a premise so a later round does not re-derive it.** Every `re.compile` in the
   package: `body_sections.py:36`, `:360`; `name_cleaning.py:46`, `:54`, `:55`, `:56`, `:57`;
   `name_gate.py:90`; `name_validation.py`'s eleven; `repositories/person.py:114`. Four non-compiled
   inline patterns in `clean_person_name` (`:134`, `:136`, `:138`, `:197`) carry only character
   classes and digits. P16's "there is no third table and no other recovery regex" is TRUE — it just
   has never been recorded as a measured premise the way P15 and P16 were.
4. **On the sufficiency question recorded for Dave, this round is the predicate the document named,
   and I record both halves.** The document says: "if a seventh independent round finds a third
   instance of the second family, the middle path is the one to take ... a third, over a surface this
   document claims to have exhausted, would be." This IS a third consecutive instance of that family
   (round 5: the identity-position list over `models.py`; round 6: `CONNECTIVE_SET` over the
   furniture regexes; round 7: the class floor over the Tier-1 branch tables), and it is over a
   surface P16 claims to have exhausted nine days of folds ago — I found it by re-reading
   `TIER1_BRANCHES` rather than by reading the fold. The half that cuts the other way, and it is
   real: **this instance is in AC-3, not in AC-5**, and the middle path Dave was offered
   (freeze AC-5 at legs (a), (d), (e); demote (b) and (c) to a declared human-review criterion) would
   not have prevented it — AC-3's floor is untouched by that option. Round 4's generator is still
   gone; AC-5 is smaller and more precise than at any point since round 1; and both of my AC-5
   observations this round are notes, not findings. So the honest reading is that the family is not
   AC-5's specifically — it is this document's habit of hand-transcribing enumerations that the tree
   declares, and the remedy that ends it is structural rather than a scope cut: apply the standing
   instruction AC-5 already carries ("every set is enumerated by APPLYING a stated rule to a NAMED,
   ENUMERABLE surface") to ALL THREE remaining enumerations at once, in one pre-origination pass —
   AC-3's class floor (derive from `branch_id`), AC-5(b)'s identity positions (P14, done) and
   `CONNECTIVE_SET` (P16, done) — instead of one per round. Dave still owns the ruling and I am not
   making it; if he takes the middle path, this finding must still be folded, because it is not in
   the part the middle path removes.

### Suggested adjustments

- Derive AC-3's DRAFT CLASS FLOOR's branch half from `TIER1_BRANCHES` ∪ `COMPANY_TIER1_BRANCHES`
  `branch_id`s read at test time, keeping the hand list only for the six shape classes that have no
  branch; key it on `branch_id` and not on `pattern`, since three branches share `calendar_prefix`.
- Correct AC-3's `why:` — the pre-fold floor covered four of the ten branches, not eight — and add
  `calendar_prefix` (and, unless argued out in one line each, `email_chars`, `pure_digit`, `empty`)
  when the floor is reconciled against the census before origination.
- Record in P16 which regexes carry `re.IGNORECASE` and correct its count to sixteen, so AC-5(b)'s
  "one undecided cell" is stated as the one cell the COMMITTED SPECIMENS leave open rather than as
  the only place the flag appears.

### Notes on process

Advancing the stage is the conveyor's — `python src/stage_advancer.py advance WI-016 --to
architected --project <path> --actor architect`. I have edited no frontmatter field other than
`last_touched` and no `state/work-items.json`; the stage stays at `idea` on this REVISE.

I raise no OPEN architectural question. The single blocking finding carries its own concrete fix
and its own exhaustive reconciliation of the surface it is about, no premise moved, the approach is
untouched, and nothing is weakened — the fix replaces a hand-typed list with a read of a tuple the
package exports, and the MEASURED/ABSENT split already in AC-3 makes it satisfiable without
obliging a specimen for any class the vault does not hold. It is REVISE rather than
PROMOTE-with-a-note for the reason rounds 4 through 6 were: the floor is reconciled against the
census BEFORE Dave signs, so this costs one criterion edit now and a re-sign later.

```verdict
gate: architect
verdict: REVISE
date: 2026-09-07
model: claude-opus-5
targets: AC-3, AC-5
prior: held
basis: folded-material
findings: 1/3
note: Round 6's findings are closed and I re-verified them against the code (the pinned run rule does decide zArchived; no third furniture table exists anywhere in obsidian_schemas; name_gate.py:319-344 and writer.py:252-253 are as AC-2 now claims), but AC-3's DRAFT CLASS FLOOR is still hand-listed against TIER1_BRANCHES (name_validation.py:190-309), whose branch_id is by its own docstring at :152 "the sweep's unit and is unique in the tuple" — it covers six of the ten ids and omits calendar_prefix (:227, specimen "Dave - Thomas Gatten", recovery arm name_cleaning.py:46, and the sole source of CONNECTIVE_SET's frozen `Dave` member), email_chars, pure_digit and empty, while the fold's own why: claims it covered eight of ten, so a census that never measures the Dave -/Me - calendar class ships a corpus without it and every assertion stays green; fix is to derive the branch half of the floor from TIER1_BRANCHES ∪ COMPANY_TIER1_BRANCHES keyed on branch_id (not pattern — three branches share `calendar_prefix`) exactly as AC-2 derives from TYPE_TO_MODEL, which is LESSONS #45's reality-diff and removes the hand-transcription generator instead of pruning its third instance.
```

