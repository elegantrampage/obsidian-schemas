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

