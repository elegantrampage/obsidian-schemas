# TimelineEntry relocates into the library, with a derived introduced_by accessor — archived gate rounds

<!-- archive-split:v1 — IMMUTABLE APPEND-ONLY ARCHIVE. Written only by src/archive_split.py at a
completed conveyor transition; appended to, never edited, reordered or rewritten. It
carries no work-item frontmatter by design, so it is invisible to find_work_items and to
find_corrupt_work_item_docs. Living spec: docs/timeline-entry-relocation.md -->

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


## Threat Model — 2026-09-29

**Recommendation: PROMOTE to threat-modeled**, with ONE required mitigation (M1) declared below and
landed by the conveyor's D8 rule on Task 2.

Cold-start read at HEAD `be6e2fe`. Carry-forward read in full before reviewing: the architect's round-4
PROMOTE, the AC red-team's round-2 PROMOTE, the `ac-signoff` fence (`ac_hash a2bb3913f2c8` — `## Intent`
and all four criteria are FROZEN), and the data-premise PROMOTE. The 2026-09-28 threat-model round timed
out at the gate's flat timeout and persisted nothing into this document, so this is a first round with no
fold to re-read; I derived every finding from the spec and the tree rather than from a recollection of
it. Every `file:line` below was READ at its cited symbol this round.

### Trigger check

Five of the nine triggers fire; the review is run in full.

- **External input.** The typed door's `text` and `discriminator` originate, in the item's own motivating
  flow, in an INBOUND third-party introduction (`## Problem / Motivation`), and both new readers
  (`parse_markers`, `parse_entries`) run over untrusted vault bytes — 5,664 files
  (`docs/wi-033-intro-corpus-baseline.md`), into which HAL9000's `routers/entities.py:350` HTTP door and
  four instruction-driven writers can author arbitrary body content (the data-premise hunt's Class A).
- **Persistence.** Every write lands in a vault note through `vault_io`.
- **Trust-boundary crossing.** The one the item names itself (§1.4): the PROSE channel (`text`) and the
  MACHINE channel (the marker) are rendered into one contiguous block in one note.
- **Filesystem operations on user-owned files.** The accessor resolves a path and reads a note; the door
  writes one.
- **Access-control modification, weak sense.** `gate_write` — the package's one semantic write gate —
  gains a refusal arm (§4).

Not firing: no secrets, credentials, tokens or OAuth scopes anywhere in the item; no MCP scope; no
outbound API call and no network at all (§8.2, and the floor is hermetic by WI-031 clause (v)); no
external message.

### STRIDE review

**Spoofing.** The marker is an UNAUTHENTICATED channel and the accessor's answer is only as trustworthy
as the writer that authored the bytes. Anyone who can write the vault — including a reachable HAL9000
`routers/entities.py:350` client hand-composing a body section, and every raw-string caller of
`append_to_timeline`, which AC-1(f) deliberately preserves — can plant
`<!-- intro-by:{day}:{name} -->` and make `introduced_by()` assert an introducer that never existed.
This is not a boundary the item breaches: the vault is a trusted store on Dave's own filesystem and the
grammar was never an authentication mechanism. Two things make it an acceptable residual rather than a
gap: the item is a RELOCATION of a claim HAL9000 already publishes, so no new authority is minted; and
`IntroRecord.source` is pinned to the verbatim bytes on the page (§1.3, AC-2), so a consumer that
disagrees with the accessor has the exact substring to audit rather than a reconstructed claim. No
mitigation required.

**Tampering.** This is where the one material finding sits, and it is M1 below. Everything else on this
axis verified clean. The typed branch's dedupe reads and writes inside ONE `note_lock` with
`precondition=_stamp` (`obsidian_schemas/repositories/person.py:1498-1546`), so the check-then-write gap
is closed by the stamp, not by a check — the TOCTOU shape does not exist here. The accessor's unlocked
read is sanctioned by `vault_io.read_note:641-663` in its own contract and `write_note` is atomic, so a
concurrent writer yields old bytes or new bytes and never torn ones. The forgery guards of §1.4 close
the marker channel COMPLETELY for the fields they cover: `kind` cannot carry `:` or a delimiter (the
slug rule), and `discriminator` is refused for `-->`, `<!--`, `\n`, `\r`, emptiness and the `:`
separator — so no value a caller supplies can mint a second marker or re-split an existing key.

The gap is that the guards cover the MARKER channel and not the SECTION channel, which this item newly
depends on. `text` is accepted by HAL9000 on nothing but `isinstance(str) and text.strip()`
(`docs/wi-033-hal9000-timeline-entry-capture.md:97`), and the capture's probe set records a multi-line
`text` as ACCEPTED (`:412-418`). So a `text` containing a line `## Notes` is legal at both doors, and
because `render` prepends the whole block immediately after the heading
(`obsidian_schemas/repositories/person.py:1543-1545`), that injected line TERMINATES the span — the
section delimiter is `^## (.+)$` under `re.MULTILINE`
(`obsidian_schemas/body_sections.py:SECTION_HEADING_PATTERN:36`), and `parse_body_sections` keys an
`OrderedDict` by heading text, so an injected duplicate `## Timeline` heading additionally shadows the
real span. Three consumers this item builds read through exactly that span and all three go quiet
together: the accessor (§3 step 3), the marker-anchored dedupe (§2 branch 2, AC-1(e)) and both new
detectors (§5). The effect is not a crash but a SILENT NARROWING — every older `intro-by` entry on that
note disappears from `introduced_by()`, `intro_by_without_marker` does not report them because they are
outside the span it scans, and the dedupe stops matching so the same event appends without limit. The
item's own §1.4 rationale is that "the machine channel must not be writable from the prose channel";
the section heading is the second machine channel and it is currently writable from `text`. A related
and milder shape — an injected `### … [intro-by]` line, which re-attributes a marker to a forged entry
in `parse_entries` and suppresses the `intro_by_without_marker` report — is closed by the same guard.
Live exposure today is nil (precondition 3: all six production callers pass a `str` and stay on the
unchanged branch, so the typed door has zero callers on the day), which is why this is a mitigation to
fold rather than a reason to bounce the spec; the first typed caller is HAL9000 post-cutover, on the
inbound-introduction path where the counterparty string is third-party-supplied.

**Repudiation.** No gap. Every refusal on both new paths is LOUD and raises — the gate arm
(`obsidian_schemas/name_gate.py` section 3c) and `TimelineEntryRefusal`, both `LoudFailError` leaves, so
`except LoudFailError` still means "this package refused" and every absorbing handler names the leaf
(`obsidian_schemas/errors.py:NameGateRefusal:106-143`). The door's existing INFO/WARNING logging is
unchanged. `retired_key_introduced_by` at ERROR is the standing record for a key that lands by
hand-edit, in the tool Dave actually runs — which is the only instrument over live data, since the floor
cannot reach the vault. Nothing security-relevant happens silently.

**Information disclosure.** Verified in place, and the design is already stricter than it needs to be.
`TimelineEntryRefusal` declares no `__init__` and passes NO note-derived value to the constructor (§1.4);
its `pattern` is a module-level source literal set as an attribute AFTER construction, so it reaches no
message and no traceback. That is enforced rather than asserted: `bounded_message` refuses any reason
outside `REASONS` with `from None` suppression (`obsidian_schemas/errors.py:177-196`), and the item adds
exactly one new enumerated literal. The gate arm's `refused_value` carries the constant key
`"introduced_by"` and never the key's value (D4), which is correct because at that arm the value is a
person's name — the exact case `_refuse`'s rule 2 exists for
(`obsidian_schemas/name_gate.py:174-192`). `retired_key_introduced_by`'s message names the key and never
its value (§5), which is TIGHTER than the shipped sibling `stem_name_divergence`, whose message already
renders a stored person name (`scripts/lint_vault.py:466-473`) — so no new class of content enters the
report. `IntroRecord.source` returns bytes the caller could already read from the note it named. One
forward-looking note for consumers, non-blocking and outside this tree: `IntroRecord.introducer` is an
attacker-influenceable string returned VERBATIM, so a consumer rendering it into HTML (HAL9000 serves
this over HTTP) escapes it as it would any vault-derived string; the library correctly does not
sanitize on a consumer's behalf.

**Denial of service.** No realistic vector. Both new patterns are line-anchored under `re.MULTILINE`
with no nested quantifier — `MARKER_PATTERN`'s `(?P<discriminator>.+)` backtracks linearly from the end
of one line, and `HEADING_PATTERN`'s lazy `(?P<date>.+?)` advances one position at a time against a
literal, so neither is a ReDoS shape even on a hostile single-line note. The readers are total: §1.3
rules that a malformed day yields no `Marker` and raises nothing, which is the correct direction for a
scan over 5,664 untrusted files and is the deliberate, justified departure from the loud-fail idiom. The
linter's new arms sit after the `read_error` and `parse_error` guards, both of which `continue`
(`scripts/lint_vault.py:378-397`), so an undecodable note cannot enter them, and `VaultFile.body` is a
non-optional `str` bound to the raw text even on a parse error (`:116`, `:180`) — so there is no `None`
body to crash the new arms on. The self-inflicted availability risk — the gate's unconditional refusal
making a note that regains the key unwritable — is already surfaced in `## Risk Analysis` with the right
answer (the population is EMPTIED, measured at 0 live carriers over 5,664 files and one fixture note
re-keyed, so no exemption arm exists to widen) and needs nothing from me. No rate limit, quota or cost
ceiling is owed: nothing here calls a paid or remote service.

**Elevation of privilege.** No gap, and the one question worth asking resolved cleanly on a read. The
accessor turns a `Person` into a file read, and a `Person` can be hand-constructed by a consumer from
untrusted input — so I checked whether a crafted `name` can escape the vault. It cannot, on both legs of
§3 step 1: `_resolve_write_target` returns a path only when `candidate.resolve().is_relative_to(
self.vault_path.resolve())` (`obsidian_schemas/repositories/base.py:406-414`), and `get_file_path` is a
dict lookup into `self._file_map` over notes the repository already loaded
(`base.py:379-390`) — neither joins a caller string onto a path, so `../` is inert at both. Mirroring
the door's own two-step (R5) is therefore also the containment-preserving choice, not just the
provenance-consistent one. Nothing is interpolated into a shell, a query or a path; the capture parser
uses `yaml.safe_load` and not `yaml.load` (§11.1), which is the right call and is worth keeping through
the fold; the gate arm grants no new capability and only refuses; and the three detectors are
report-only with `auto_fixable` at its default, so none of them can reach `apply_fixes`.

### Mitigations verified in place

1. **Marker-channel forgery closed at construction** — §1.4 guards 1–4, pinned by AC-1(c) and enumerated
   as a set equality by AC-1(c2), on inputs HAL9000 itself accepts
   (`docs/wi-033-hal9000-timeline-entry-capture.md:400-404`: HAL9000 accepts a `text` of
   `<!-- forged -->` today). The relocation closes an open forgery hole rather than inheriting one.
2. **Refusals carry no note-derived content** — §1.4 and D4, enforced by `bounded_message`'s enumerated
   reasons (`obsidian_schemas/errors.py:177-188`) and by `_refuse`'s rules 1–3
   (`obsidian_schemas/name_gate.py:160-192`).
3. **Fail-closed on the write path, total on the read path** — validation is in `__post_init__`, so a
   refusal fires before the object the door receives exists (`## Edge Cases`, Partial failure), and
   AC-3(b) asserts NO FILE CHANGED at all five driven gate arms.
4. **Path containment on the new read** — `base.py:406-414` and `base.py:379-390`, as above.
5. **Atomicity and lock discipline unchanged** — one `note_lock` spanning read/dedupe/write with a stamp
   precondition (`person.py:1498-1546`); the accessor's unlocked read is sanctioned and non-torn
   (`vault_io.py:641-663`).
6. **Untrusted-byte readers raise nothing and build nothing** — §1.3, §8.4, with the linter's triage
   order preserved by placement (`scripts/lint_vault.py:378-397`) and asserted by AC-4(f).

### Required mitigation

```mitigation
kind: required
id: M1
desc: TimelineEntry refuses a `text` carrying a line that matches `^#{2,3} `, because a markdown heading in the prose channel truncates or shadows the `## Timeline` span that the accessor (§3), the marker-anchored dedupe (AC-1(e)) and both new detectors (§5) all read through, silently hiding every older entry from all three; the guard refuses no probe the capture records as accepted, so AC-1(c2)'s set equality and the signed criteria frame are unmoved.
landed: Task 2
```

**Why this lands on Task 2 and needs no re-signature.** Task 2 builds §1.4's guard table, and its
`verify:` already points at Task 3's capture-driven check, so the fold carries the oracle with it. The
compatibility argument is the load-bearing half and I checked it rather than assuming it: AC-1(c2) is a
set equality over the probes the capture records as ACCEPTED (R1's reified form — capture `accept`
probes filtered by this document's guard predicates), and NO accept-probe carries a `^## ` or `^### `
line: the only multi-line text probe is `'line one\n\nline two'`
(`docs/wi-033-hal9000-timeline-entry-capture.md:412-418`). A fifth guard therefore adds no member to
either side of the equality and leaves the assertion green, so the mitigation is a §1.4 table row plus a
clause in Task 3's check — it does not touch a frozen fence and must not be folded by editing one. The
predicate itself is not invented here: `^#{2,3} ` is the body boundary §1.3 already declares for
`parse_entries`, so the module gains no second grammar.

### Notes (non-blocking)

- **The honesty invariant has a residual hole that M1 does not close: an `intro-by` entry that is ALREADY
  outside a `## Timeline` span** — written through the raw-string branch AC-1(f) preserves, or hand-edited
  in Obsidian — is invisible to the accessor AND to `intro_by_without_marker`, which only scans inside
  the span. I am not requiring a mitigation because the exposure is MEASURED at zero: precondition 2
  reports that every timeline heading found in the live vault sits inside a `## Timeline` section, and
  that census predicate is re-runnable. Worth the cutover item's attention if the typed door ever gains a
  caller before that measurement is refreshed.
- **`IntroRecord.introducer` is attacker-influenceable and returned verbatim** — a consumer rendering it
  into HTML must escape it. Correctly not the library's job; recorded so the two waiting consumers
  (HAL9000 WI-078, orchestrator WI-194) inherit the fact rather than discover it.
- **The window D7 accepts in writing has a security reading as well as a drift reading.** Until the
  cutover lands, HAL9000's own door keeps accepting a `text` that forges a marker
  (`capture:400-404`) — so the forgery guard protects only callers that route through this library. That
  is the correct sequencing and the right scope; it is simply worth stating that the hole does not close
  estate-wide until HAL9000 WI-082 ships.
- **Two OPEN security questions is the role's cap; I am at zero.** Both of the above are observations
  with stated dispositions, not open questions.

```verdict
gate: threat-modeler
verdict: PROMOTE
date: 2026-09-29
model: claude-opus-5
note: The design's security posture is sound and six mitigations verified in place on a read (marker-forgery guards that close a hole HAL9000 itself still has, content-free refusals enforced by bounded_message, fail-closed writes, path containment at both legs of the accessor's resolution, unchanged lock/stamp discipline, total non-raising readers) — the one material finding is that §1.4 guards the MARKER channel but not the SECTION channel, so a capture-accepted `text` carrying a `## ` line truncates or shadows the `## Timeline` span that the accessor, the marker-anchored dedupe and both new detectors all read through, silently hiding every older entry from all three; that is a mitigation to fold (M1, Task 2), not a spec gap, because live exposure is nil today (all six production callers stay on the string branch) and the guard refuses no capture-accepted probe, so AC-1(c2)'s set equality and the signed criteria frame are unmoved.
```


## Adversarial Review — 2026-09-29

**Recommendation: PROMOTE (injection axis only)** — no planted steering found. This is the injection-hunter's
narrow question, not a second spec review: the spec-reviewer's standing verdict on this document is REVISE
on three concrete blocking findings, and nothing here overrides, softens or substitutes for it.

Cold-start read of the whole document, line 1 to its last line, including every prior gate's prose and
verdict fence, plus the four committed precondition artifacts (`docs/wi-033-hal9000-timeline-entry-capture.md`,
`docs/wi-033-intro-corpus-baseline.md`, `docs/wi-033-consumer-audit.md`, `docs/wi-033-hal9000-cutover-followup.md`)
and the archived rounds file `docs/timeline-entry-relocation-rounds.md`, which the archive pointer says holds
settled rounds.

**What I hunted, and what came back.**

- **Text arguing for a verdict, or addressed to a gate.** A pattern sweep over the item doc, the rounds
  archive, the four preconditions and Dave's review artifact for approval-steering phrasing (pre-approval
  claims, "do not block", "ignore prior", verdict-emission instructions, system-prompt talk) returned only
  legitimate `verdict:` fence lines: the architect, ac-red-team, ac-signoff, data-premise and threat-modeler
  PROMOTEs and the spec-reviewer REVISE in this document, one in the archive, and one inside Dave's
  review artifact. The imperative-mood text in `docs/wi-033-consumer-audit.md` is verbatim grep output
  quoting other projects' agent instructions as consumer evidence, addressed to those agents, and inert
  here.
- **Spec-shaped sections whose effect is to steer.** `## Ruling`, `## Design` §0 (the five reifications), D7's
  declined drift checker, D8, the M1 fold and the Risk Analysis all argue for their own design, which is the
  calibrated "spec making its own case" and not an injection. §0's claim that the M1 fold leaves the signed
  frame unmoved is a substantive argument with a re-runnable predicate, and the spec-reviewer independently
  re-derived it from the capture's own probes rather than taking it on the modeler's narrative.
- **Prior PROMOTEs that read as steered.** The architect, red-team, data-premise and threat-modeler notes each
  cite code they re-read and premises they re-ran, and their reasoning is decorrelated from one another
  (each found something the previous round missed). The one gate that returned REVISE, the spec-reviewer, did
  so on findings that point at real pins and would be odd output from a steered chain. The verdict history
  shows independent judgement, not a uniform lean.
- **The `writes` fence naming another item's tracked document (WI-245).** `docs/vault-fixtures.md` is WI-016's
  document and is declared as `kind: precondition`, not as a builder write. The spec states in three places
  (§6, the fence's `why`, and `## Write Targets`' extension note) that the caged builder is NOT its author, that
  the edit replaces prose and would be refused at the merge boundary, that WI-016's signed AC-5 fence at
  `:1434` is out of scope and must not be touched, and that the conductor commits it before the build. That is a
  disclosed, narrowly-scoped, conductor-owned precondition and not a build-authored cross-doc authorization.
  I still flag it for the human who lands it: land only the one sentence at `:279` and nothing else in that
  file, per the fence's own text.
- **The quoted and captured material.** The capture, corpus baseline and cutover record are machine-shaped
  artifacts (YAML fences, verbatim source, command output) whose `verdict:` keys are HAL9000
  accept/refuse probe results and not gate verdicts. I found no embedded instruction in them.

**Honest limit, carried.** I read the same bytes the other gates did and could be fooled the same way; my
value is a different model and a narrower question. The document is unusually self-referential (long, densely
cross-cited, with several rounds of folds), which is the shape in which a plant would hide, so I read the fold
records and the archive pointer specifically for text that changes what a gate should do rather than what the
system does. None does.

```verdict
gate: injection-hunter
verdict: PROMOTE
date: 2026-09-29
model: claude-sonnet-5-5
note: No planted steering anywhere in the item doc, its archived rounds, the four committed preconditions or Dave's review artifact — verdict-shaped lines are only genuine gate fences, the prior PROMOTEs cite re-run evidence and the spec-reviewer independently returned REVISE on real pins, and the one cross-doc `writes` fence (docs/vault-fixtures.md) is a disclosed conductor-owned precondition and not a build-authored merge authorization; this clears the injection question only and leaves the spec-reviewer's three blocking findings standing.
```


## Threat Model — 2026-09-29 (round 2)

**Recommendation: PROMOTE to threat-modeled**, with the SAME one required mitigation (M1) re-emitted
below — unchanged in what it requires, still landed on Task 2.

Round 2, cold-start at HEAD `be6e2fe` with the working tree carrying the spec-writer's 2026-09-29 fold of
the spec review's three blocking findings. Carry-forward read in full before reviewing: my own round-1
section, the `## Mitigation Folds` record, the spec review's REVISE, the injection-hunter's PROMOTE, and
behind those the architect's round 4, the AC red-team's round 2, the `ac-signoff` fence
(`ac_hash a2bb3913f2c8`) and the data-premise PROMOTE. Round 1's single finding is CLOSED, and I found it
closed by re-reading the design surfaces rather than by taking the fold record's word. Every `file:line`
I newly lean on was READ at its symbol this round.

### Trigger check

Unchanged and still firing — five of nine: external input (`text`/`discriminator` originate in an inbound
third-party introduction; both new readers run over 5,664 untrusted vault files), persistence (every write
lands in a note through `vault_io`), trust-boundary crossing (the prose channel and the machine channels
rendered into one contiguous block), filesystem operations on user-owned files, and access control in the
weak sense (`gate_write` gains a refusal arm). Still not firing: no secrets, credentials, tokens or OAuth
scopes; no MCP scope; no network at all; no external message. Review run in full.

### Round 1's finding, re-read

**CLOSED, and closed as a write-door refusal rather than as a sentence.** Guard 5 is in the validation
table at `## Design` §1.4 with the two silent effects named (an injected `## `-prefixed line TERMINATES
the `## Timeline` span; an injected duplicate `## Timeline` heading SHADOWS it), it is written in Task 2
and not deferred to a later one, and Task 3's clause (c3) ships four claimed shapes, five near-misses and
the span-loss CONSEQUENCE itself by string surgery outside the door — which is the WI-235 form rather than
a refusal count. Two properties I re-derived rather than inherited:

- **The predicate really does cover every shape the three consumers route on.** `SECTION_HEADING_PATTERN`
  is `re.compile(r'^## (.+)$', re.MULTILINE)` (`obsidian_schemas/body_sections.py:36`, read this round),
  and `^#{2,3} ` covers it, covers `HEADING_PATTERN`, and covers `parse_entries`' own body boundary —
  which is the same constant by construction, so the door refuses precisely the line the reader treats as
  a boundary. §1.1's restatement of the bound as a strict SUPERSET rather than an exact union is the
  security-correct direction: a superset over-refuses two inert shapes (a title-less `## ` line, a
  kind-less `### ` line) and under-refuses nothing, so the coverage claim guard 5 rests on is now true as
  written instead of true-in-effect. The `# ` / `#### ` complement is genuinely outside all four patterns
  (each needs a space at a fixed offset that a third or fifth `#` occupies), so neither truncates a span
  nor forges an entry and neither is refused.
- **Guard 5 still adds a PREDICATE and no MEMBER to AC-1(c2)'s equality, and I enumerated the capture
  myself rather than reading §0 R1's claim about it.** The 29 probes at
  `docs/wi-033-hal9000-timeline-entry-capture.md:293-467` accept five `text` values
  (`Met for coffee`, `see --> here`, `<!-- forged -->`, the `Introduced by [[…]] via gmail` sentence, and
  the one multi-line probe `'line one\n\nline two'` at `:413-417`); none carries a `^#{2,3} ` line. The
  capture-ACCEPTED inputs this library refuses are therefore exactly `text` = `see --> here`, `text` =
  `<!-- forged -->`, and `discriminator` = `''`, `'   '`, `a:b` — five, before and after the fold. So the
  signed frame is unmoved on a read, and M1 remains a table row plus a check clause rather than anything
  that needs a re-signature.

### What this round's new material does to the security posture

The fold touched eight surfaces. Seven are security-neutral or security-positive, and I say which is
which rather than waving at the set: §0 R6 / §6 / Task 7's narrowing of the `docs/vault-fixtures.md`
oracle from a whole-file absence pin to a positive, section-scoped read is a test-oracle change with no
threat surface (and it is strictly stronger — a deletion of the sentence now fails); Task 12's narrowing
drops no security check, since all four of this item's AC checks, including AC-1(c), AC-1(c2), AC-3(b) and
AC-4(f), remain its obligation; §1.3's `_compose_key` / `Marker.key` / `dedupe_probe` reconciliation makes
the door's dedupe comparand single and live, and the two forms it reconciles are equivalent on the read
side (`MARKER_PATTERN` admits only `<!-- {key} -->`, so `source` and `key` are in bijection for any marker
the reader yields) — no collision path is opened or closed; `get_section` named as one import addition,
the `:113` re-anchoring to `baseline_sections:1518` / `fenced_blocks:1550`, and §9's `CORPUS_PINNED_ISSUES`
row are all buildability, not security.

**The eighth is security-relevant and the fold moves it the right way.** Task 2 now owns the edit to
`tests/test_name_gate.py:124` in the same task that adds the `REASONS` member, and §9 carries
`obsidian_schemas/errors.py:REASONS:152` as a third countable corpus. `REASONS` is not an incidental
count: it is the information-disclosure choke point of the whole error hierarchy. `bounded_message`
refuses any reason outside the set and does so `from None`, with the comment at
`obsidian_schemas/errors.py:183-188` stating that the suppression exists because the refusal fires
"while a note-content-bearing original is in flight" — so the enumeration is what keeps a composed,
content-bearing string from having a constructor to enter. The pin over it is deliberate and is an
EQUALITY (`assert len(REASONS) == 16` at `tests/test_name_gate.py:124`, with the comment at `:121-122`
declaring the equality the right pin). Before the fold that RED had no owner and would have surfaced at
the last task; now the obligation is stated as a predicate (the set grows by exactly one and every pin
over it moves with it) with the target value named, and the new leaf's own hierarchy assertions land in
the same check — including that a non-member reason is refused as a BARE `ValueError` outside the
hierarchy. That extends mitigation 2's enforcement to `TimelineEntryRefusal` instead of leaving it
asserted only for `NameGateRefusal`. The one new reason literal,
`"a timeline entry field this package refuses"`, is a constant carrying no note-derived content, and it
is per-DOOR rather than per-guard with `pattern` distinguishing the faults — so guard 5 adds no message
surface either.

### STRIDE re-read — deltas only

Rounds are cheap to pad and I am not padding: the five axes round 1 verified clean verified clean again
on the same reads and I record only what the fold changed.

**Tampering.** Round 1's gap is closed at the write door by guard 5 and the door is now TOTAL over the
generator §1.4's field sweep declares — `text` is the only input that can introduce a line, since
`KIND_PATTERN` admits `[a-z0-9_-]` only and the discriminator is refused for `\n`/`\r` and renders inside
a line where a `## ` is inert. The lock discipline is untouched by the fold: one `note_lock` spanning
read, dedupe and write with `precondition=_stamp` (`obsidian_schemas/repositories/person.py:1498-1546`),
so the check-then-write gap is closed by the stamp and the TOCTOU shape still does not exist. The
reconciled dedupe comparand does not widen what a hostile note can suppress — a false dedupe hit still
requires the exact marker line to be present inside the span, which is the contract.

**Information disclosure.** Strengthened, per the section above; nothing weakened. `refused_value` still
carries the constant key and never a person's name (D4, `obsidian_schemas/name_gate.py:_refuse:174-192`),
and the detector messages still name the key and the heading and never a stored value.

**Spoofing, Repudiation, Denial of service, Elevation of privilege.** Unchanged and unchallenged by the
fold. The marker remains an unauthenticated channel over a trusted store with `IntroRecord.source` pinned
to the bytes on the page as the audit route; every refusal on both new paths is loud; both patterns are
line-anchored with no nested quantifier and the readers are total over 5,664 files; and the accessor's
path resolution is contained on both legs (`repositories/base.py:406-414`'s `is_relative_to` check and
`:379-390`'s dict lookup — neither joins a caller string onto a path).

### Mitigations verified in place

The standing set, re-verified this round. 1. Marker-channel forgery closed at construction (§1.4 guards
1–4, pinned by AC-1(c) and enumerated as a set equality by AC-1(c2), on inputs HAL9000 itself accepts —
`capture:401-403` accepts a `text` of `<!-- forged -->` today, so the relocation closes an open hole
rather than inheriting one). 2. Refusals carry no note-derived content (§1.4, D4), enforced by
`bounded_message`'s enumerated reasons and its `from None` suppression
(`obsidian_schemas/errors.py:177-188`) and by `_refuse`'s rules 1–3 — and now extended to the new leaf by
Task 2's assertions. 3. Fail-closed on the write path, total on the read path (validation in
`__post_init__`, so a refusal fires before the object the door receives exists; AC-3(b) asserts NO FILE
CHANGED at all five driven arms). 4. Path containment on the new read (`base.py:406-414`, `:379-390`).
5. Atomicity and lock discipline unchanged (`person.py:1498-1546`; the accessor's unlocked read sanctioned
and non-torn, `vault_io.py:641-663`). 6. Untrusted-byte readers raise nothing and build nothing (§1.3,
§8.4), with the linter's triage order preserved by placement (`scripts/lint_vault.py:378-397`) and
asserted by AC-4(f). 7. The section channel closed at the write door — M1, folded into §1.1, §1.4 guard 5,
Task 2 and Task 3 clause (c3) since my round 1, and re-emitted below because a later declaration
supersedes an earlier one and silence would leave the set unstated.

### Required mitigation

```mitigation
kind: required
id: M1
desc: TimelineEntry refuses a `text` carrying a line that matches `^#{2,3} `, because a markdown heading in the prose channel truncates or shadows the `## Timeline` span that the accessor (§3), the marker-anchored dedupe (AC-1(e)) and both new detectors (§5) all read through, silently hiding every older entry from all three; the guard refuses no probe the capture records as accepted, so AC-1(c2)'s set equality and the signed criteria frame are unmoved.
landed: Task 2
```

Re-emitted byte-identically because what the mitigation REQUIRES has not moved — §1.1's restatement of
the pattern's bound as a strict superset strengthens the coverage claim the guard rests on and changes no
requirement — and `landed: Task 2` is still the task that writes the guard.

### Notes (non-blocking)

- **The `REASONS` pin must move as an EQUALITY, not be loosened.** The only way Task 2's new obligation
  goes wrong on a security axis is a builder under cap pressure satisfying
  `tests/test_name_gate.py:124` by rewriting `== 16` as `>= 16` or deleting it, which would silently
  retire the size bound on the enumeration that keeps composed, note-content-bearing strings out of the
  hierarchy. Not a required mitigation, because the document already names the target value (`17`),
  Scope Boundary bounds the edit to exactly that line plus assertions inside the existing check, and §9
  states the obligation as the predicate. Recorded so the reviewer who reads the diff knows which of the
  two legal-looking edits is the wrong one.
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
- **Two OPEN security questions is the role's cap; I am at zero.** All four notes above are observations
  with stated dispositions.

```verdict
gate: threat-modeler
verdict: PROMOTE
date: 2026-09-29
model: claude-opus-5
note: Round 1's one finding is CLOSED and I re-derived the closure rather than inheriting it — guard 5 lands in §1.1/§1.4/Task 2/Task 3(c3), `^#{2,3} ` covers `SECTION_HEADING_PATTERN` (`body_sections.py:36`, read this round), `HEADING_PATTERN` and `parse_entries`' shared boundary while the `# `/`#### ` complement is genuinely outside all of them, and I enumerated the capture's 29 probes myself to confirm the five capture-accepted refusals are unmoved (no accept-probe carries a `^#{2,3} ` line, the only multi-line one being `'line one\n\nline two'` at capture:413-417), so AC-1(c2) and the signed frame stay green; of the spec-review fold's eight surfaces seven are security-neutral or strictly stronger and the eighth is security-POSITIVE — Task 2 now owns the `len(REASONS) == 16` → `17` equality pin and the new leaf's hierarchy assertions, which extends the information-disclosure choke point (`bounded_message`'s enumerated reasons with `from None` suppression, `errors.py:177-188`) to `TimelineEntryRefusal` instead of leaving it asserted for `NameGateRefusal` alone; M1 re-emitted byte-identically on Task 2, six prior mitigations re-verified in place, zero open security questions.
```


## Adversarial Review — 2026-09-29 (round 2)

**Recommendation: PROMOTE (injection axis only)** — no planted steering found. This is the narrow injection
question, not a third spec review: the spec-reviewer's standing round-2 verdict is REVISE on two concrete
blocking findings (Task 7's wrap-sensitive phrase, Task 3's selector contract), and nothing here overrides,
softens or substitutes for it.

Cold-start re-read after the 2026-09-29 spec-review fold, with the material added since my round 1 read
closely: the `## Mitigation Folds` record, the threat modeler's round 2, the spec-reviewer's round 2, and the
fold's new surfaces (§0 R6, Task 12's narrowing, the `REASONS` obligation and §9 rows).

- **Text arguing for a verdict or addressed to a gate.** Two sweeps over the item doc, the rounds archive and
  the four committed preconditions (approval-steering phrasing; text addressed to a reviewer, gate or agent,
  or declaring a verdict already settled) returned nothing beyond the genuine `verdict:` fences of the
  architect, red-team, sign-off, data-premise, threat-modeler and spec-reviewer rounds. Every fence sits at a
  gate's own section end, and each `gate:` matches the section that carries it.
- **The fold's new material.** R6, the `REASONS` pin obligation and Task 12's narrowing are substantive
  design and test-oracle argument with re-runnable predicates. The threat modeler's note that the `REASONS`
  pin must move as an equality is a warning to the diff reviewer, not steering of a gate. The spec-reviewer
  reached its REVISE by re-reading files the fold cited and finding real defects, which is not what a steered
  chain produces; the verdict series (REVISE, PROMOTE, REVISE) shows independent judgement.
- **The `writes` fence naming another item's tracked document (WI-245).** Unchanged from round 1: the
  `docs/vault-fixtures.md` edit is a disclosed, conductor-owned precondition, not a build-authored merge
  authorization. The fold narrowed the oracle that reads it (positive, section-scoped) without adding a
  builder write. I repeat the flag for whoever lands it: land only the one sentence and drop nothing else
  into that file.
- **Quoted and captured material.** The capture and baseline artifacts remain machine-shaped output whose
  `verdict:` keys are HAL9000 accept/refuse probe results, not gate verdicts. Nothing embedded in them
  addresses a gate.

**Honest limit, carried.** I read the same bytes the other gates did and could be fooled the same way; my
value is a different model and a narrower question. The document is long and densely cross-cited, and I read
the fold-added material specifically for text that changes what a gate should do rather than what the system
does. None does.

```verdict
gate: injection-hunter
verdict: PROMOTE
date: 2026-09-29
model: claude-sonnet-5-5
note: Re-read after the spec-review fold finds no planted steering in the item doc, its rounds archive or the four committed preconditions — verdict-shaped lines are only genuine gate fences, the fold-added material (R6, the REASONS pin obligation, Task 12's narrowing) is ordinary spec argument with re-runnable predicates, the spec-reviewer's REVISE-PROMOTE-REVISE series reflects independent judgement on real defects, and the one cross-doc writes fence stays a disclosed conductor-owned precondition; this clears the injection question only and leaves the spec-reviewer's two blocking findings standing.
```

