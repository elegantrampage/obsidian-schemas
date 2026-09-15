# lint_vault.py --fix safety — archived gate rounds

<!-- archive-split:v1 — IMMUTABLE APPEND-ONLY ARCHIVE. Written only by src/archive_split.py at a
completed conveyor transition; appended to, never edited, reordered or rewritten. It
carries no work-item frontmatter by design, so it is invisible to find_work_items and to
find_corrupt_work_item_docs. Living spec: docs/lint-vault-fix-safety.md -->

## Architectural Review — 2026-09-10

**Recommendation: REVISE — return to exploration**

### Trigger check

Fired, despite `## Approach`'s closing line ("Hand off to **spec-writer**, not architect"): the item
touches more than three files across different concerns — `scripts/lint_vault.py`, a new
`tests/test_lint_vault_fix_rules.py`, a new scan in `tests/derivations.py`, two universe sites in
`tests/test_fixture_vault.py` (`:509`, `:1302`) and the pinned `FixOutcome._fields` equality in
`tests/test_lint_vault_fix_gate.py:279` — and it extends two persistent in-repo records (`VaultFile`
gains `read_error`, `FixOutcome` gains a bucket) plus mints a new derived-wall class. Not blocking on
its own; recorded because the doc's own routing sentence reads the trigger table the other way.

The audit itself is in excellent shape and I re-ran its citations rather than trusting them. Every
load-bearing one holds: `except Exception: continue` at `lint_vault.py:117-118`; the five
`auto_fixable=True` emitters at `:344,360,389,533,599` and exactly five `issue.check ==` branches
inside `apply_fixes` at `:888,896,903,911,929` (the only other two, `:1125,1127`, are
`quarantine_garbage`'s, correctly outside AC-1's scope); `FixOutcome` two-field at `:820-825`;
`NameGateRefusalRecord` closed at `:805-818`; the uncounted print at `:993-994`; the summary at
`:1198`; `SKIP_REASONS` at `repositories/base.py:41-48`; the name-is-a-predicate emit at
`name_gate.py:366-367` — and the discriminator that rests on it survives, because none of the ten
Tier-1 branches (`name_validation.py:192-301`) is a whitespace rule while `clean_person_name`
collapses `\s{2,}` at `name_cleaning.py:197`. The corpus claims settle too: zero `auto_created`
anywhere under `tests/fixtures/vault/`, exactly one `[[` and it is frontmatter
(`Harkwell Tessamund.md:7`), the non-UTF-8 member declared at `fixture_vault.py:472-478`, and the
census's five rows live at `docs/vault-shape-census.md:272-281`, charged there by
`docs/vault-fixtures.md:1292`. A3's and A3b's rejections are sound — `frontmatter_write_arms` really
is pinned by equality over `python_files_under(PACKAGE_ROOT, SCRIPTS_ROOT)`
(`test_company_name_contract.py:603,609`), so A3b would drag two frozen wall sets.

The findings below are about what the criteria do NOT reach, not about what they got wrong.

### Blocking issues

**1. A corpus tool's acceptance is entirely hermetic — LESSONS #27, re-incurred (`## Approach`,
`## Write Targets`, AC-3).** `lint_vault.py` is the canonical instance of "a tool whose job is the
whole corpus": its correctness is defined by its behaviour on 4,730 live issues across Dave's vault,
and the failure mode that matters for a linter — the false positive on the shape nobody drew a
fixture from — lives precisely in the tail no fixture contains. All four criteria are `kind: test`
over a materialized 53-note copy with plants on top. The single `writes` fence is a *verification*
of an artifact already in HEAD ("The conductor's act here is therefore a VERIFICATION, not a
measurement"), so nothing in this item ever points the changed code at the real vault. That is the
WI-064 scar verbatim: five green hermetic tests, an independent reviewer cleared it, and both
defects — a dropped allowlist entry and a classifier firing on a docstring — surfaced only when the
lint ran over a real sibling repo. Prior art agrees with the scar rather than with the doc: the
comparable products (ruff, ESLint) pair a fixture corpus with an ecosystem run over real
repositories, and this design ships only the first half. It is not a frame problem — the project
already owns the mechanism (`kind: precondition`, used exactly this way by WI-016) and the caged
builder's blindness to the live vault is a solved constraint, not a new one.

Concretely, two acts belong in a fence, and both are cheap:
- **Entry:** one counting scan for notes `read_vault` cannot decode, appended to the census under
  the rules that governed the first pass. This settles Open Question 1 — which is a *measurement*
  routed to a human as a judgement call; Dave cannot know the answer and one command can, and AC-3's
  whole subject population is what it grounds.
- **Exit:** after the build lands, `scripts/lint_vault.py --vault $VAULT --report` on the live vault,
  with the five auto-fixable counts diffed against `docs/vault-shape-census.md:272-281` and the new
  unreadable-skip count and summary line read. `--report` and not `--fix`: this item changes what
  `read_vault` returns, so it changes the live issue counts for all five stem-keyed checks
  (`:463,482,497,513,722`), and that delta is the acceptance evidence — obtaining it must not require
  mutating Dave's vault, which is a separate authorization.

**2. AC-2's justification argues a scope AC-2 excludes — the detector that MOVES files stays
unpinned (AC-2).** The criterion's `why` rests its weight on data loss: "a detector that mis-fires
does not produce a wrong report, it produces a wrong WRITE — and `--quarantine` MOVES files off the
back of the very same issue list (`:1218` → `quarantine_garbage`)." But leg (a) pins "the set of
`(filename, check)` pairs carrying `auto_fixable=True`", and `garbage_candidate_person` /
`garbage_candidate_company` are INFO and NOT auto-fixable — so the two checks that actually drive
`vault_io.move_note` (`:1140`) are outside the pinned set, and `classify_person_tier` (`:233-283`),
the predicate that decides which person notes get moved, ends this item exactly as untested as it
started. The closing clause "the five that WRITE" is the contradiction in one phrase: six checks
cause a write on this file, and the sixth is the one that relocates the note. Either widen leg (a)'s
table to include the two `garbage_candidate_*` ids and give leg (b) a planted stub — nearly free,
since no corpus note carries `auto_created` at all, so both pin at zero on the corpus today — or
strike the quarantine argument from the `why` and say in `## Approach` that the quarantine detector
is deliberately deferred, and to which item. What must not ship is a criterion frozen by signature
whose stated reason for existing is a hazard it does not cover.

**3. AC-4's partition is three buckets over a four-state space — the silent no-op survives it
(AC-4).** The `why` claims the partition "makes the uncounted state unrepresentable rather than
merely populated today" and that "the equality goes red the moment a file falls into none of the
three". It does not, because a *fourth* per-file outcome already exists and the criterion's planted
vault cannot produce it: a file whose every auto-fixable issue hits a branch guard that declines to
act. All five branches have one — `isinstance(raw, str)` (`:890`), `if expected` (`:906`),
`if mstem and mstem in meetings` (`:913`, which is *every* `meeting_missing_from_timeline` issue —
315 live — whenever `apply_fixes` is called without `idx`, the signature's own default at `:828`),
and the `except (json.JSONDecodeError, KeyError): pass` at `:935-936` that this document already
found and filed under "named so nobody re-finds them". Such a file raises nothing, refuses nothing
and repairs nothing: `changed` stays False, no write, no record, no count. That is precisely the
Intent's "nothing `--fix` cannot account for may leave the run silently", and AC-1(a)'s two-sided
emitter≡branch equality catches only the *static* version of it (a branch that does not exist), never
this dynamic one (a branch that exists and declined).

The remedy also dissolves a second ambiguity in the same criterion. State the partition **per
ISSUE**, not per file: every auto-fixable issue handed to `apply_fixes` ends as repaired,
gate-refused, errored, or **declined** (with the declining branch named). Per-file forces a
"fixed-files" notion the code does not have — `FixOutcome.fixed` counts *issues*, and the wikilink
arm increments the run counter at `:972` outside `file_fixed` entirely, so a file repaired only by a
link rewrite has `file_fixed == 0` and a builder computing "fixed-files" from it would drop that file
out of every bucket. Per-issue is exact, it keeps leg (a)'s equality total, and it makes the declined
count something an operator can act on.

### Suggested adjustments

- `## Write Targets`: add the entry/exit real-vault acts as a fence, per finding 1. Fold Open
  Question 1 into it and drop it from the two questions for Dave — it is settleable by one command
  and should not consume a sign-off turn.
- AC-2: widen leg (a)'s pinned table to the six checks that cause a write, or narrow the `why`.
- AC-4: re-state the partition per issue with a fourth `declined` bucket, and say where the branch
  id is recorded.
- `## Exploration Notes`: the two-half framing in "The problem, restated after the audit" should
  carry the declined-repair as a named third half or be folded into half 2 — it is the same
  accounting defect one level in from the ones already listed.

### Notes (non-blocking)

- **AC-3(a)'s "the `skip_reason_literal_sites` derivation is extended to cover `SCRIPTS_ROOT`" names
  the wrong artifact.** The derivation (`tests/derivations.py:1583`) already takes an arbitrary
  `files` iterable; what needs extending is the two hand-typed *call sites* that pin the universe as
  `python_files_under(PACKAGE_ROOT, TESTS_ROOT)` — `tests/test_fixture_vault.py:508-514` and
  `:1315-1318`, the second being the same wall deliberately re-run from a second module. Both are
  write targets, and missing one leaves a half-extended wall that reads as green.
- **The `person_missing_name` plant collides with a real corpus filename.** AC-1(c) names the
  whitespace-damage stem `Dave  Marrowyn Fennwick`, and `tests/fixtures/vault/@Dave  Marrowyn
  Fennwick.md` already exists with a well-formed `name:`. Planting that exact stem onto a
  materialized copy overwrites a corpus member — `materialize_vault`'s "leaves everything else in
  that directory alone" does not protect a name the plant reuses. Spec-time fix: a distinct stem
  carrying the same shape.
- **`test_lint_vault_fix_gate.py:279` goes red on AC-4 by construction** (`_fields == ("fixed",
  "refused")`, an equality). The doc already flags it; keep it explicit in the write targets, and
  note that `_check_the_delta_carries_only_the_keys_the_branches_assigned` (`:166`) and
  `_check_a_refusal_is_recorded_counted_and_the_run_continues` (`:201`) assert on `outcome.fixed`
  numerically, so any change to what `fixed` counts moves three assertions, not one.
- AC-3's leg (c) is right to name `no_frontmatter` at `:308`: a `read_error` `VaultFile` carrying
  `{}` frontmatter and an `@`-prefixed stem lands on that branch unless `check_structural` handles
  the read error above it. `orphaned_note` (`:722`) and `possible_duplicate` (`:734`) are already
  safe by construction — both gate on `vf.entity_type`, which stays `""` — which is worth saying so
  the build does not add guards it does not need.

```verdict
gate: architect
verdict: REVISE
date: 2026-09-10
model: claude-opus-5
targets: AC-2, AC-3, AC-4, #approach, #write-targets
prior: none
basis: original
findings: 3/6
note: A whole-vault lint's acceptance is 100% hermetic (LESSONS #27, the WI-064 scar), AC-2's quarantine rationale argues past the auto-fixable-only scope it declares, and AC-4's three-bucket partition leaves the silent declined-repair — the very class the Intent names — uncounted.
```


## Architectural Review — 2026-09-10 (round 2)

**Recommendation: PROMOTE to architected**

### Trigger check

Fired again for the same reasons round 1 recorded, and the doc's own routing sentence now reads the
trigger table the right way (`## Approach`, the "Routing: architect" paragraph). Nothing turns on it
this round.

### The round-1 findings, re-read against this tree

All three blocking findings are CLOSED, and two of the three are closed *better* than I prescribed.
I re-executed the citations the revision added rather than accepting them.

**Blocking 1 — hermetic acceptance. Closed, and my own prescription was wrong on the mechanism.** I
asked for the entry and exit acts "in a fence, and both are cheap". The exit act cannot be a fence
and the doc proves it rather than asserting it: `work_item_linter.py:167-170` says in as many words
that `drive()` probes a `kind: precondition` path "for git-HEAD membership **before arming the
builder**", and `VALID_CRITERIA_KINDS = {"test", "command"}` at `:158` closes the other route. A
post-build act has no fence kind, so A7's split — entry fence-typed and AC-enforced, exit a declared
ship condition on the WI-022 precedent — is the only correct shape, and `docs/company-name-corpus-audit.md:30-38`
really does carry that precedent verbatim ("Conductor attestation — 2026-09-06, post-build, at the
quiesce"). A7b's second divergence holds too: the new fence carries `grounds:`, which is the WI-300
grounding discriminator, and that key's own contract is "a grounding artifact lands in HEAD before
the AC frame is presented, not before the build" (`work_item_linter.py:427`, `GROUNDS_KEY` at `:442`)
— exactly the ordering AC-5 needs. Recording both rejections in A7/A7b rather than diverging silently
is the right move and is what let me check them. The baseline also captures more than I asked for —
the five stem-keyed counts (`:463,482,497,513,722`) — which is the figure set this change actually
moves and which only the pre-change run can take.

**Blocking 2 — AC-2's scope. Closed by widening, which was the better of the two options I offered.**
`classify_person_tier` is at `:233-283` as claimed, its docstring states exactly six disjuncts at
`:236-242`, and the implementation is four `if` statements over those six conditions (`:252`, `:275`,
`:278`, `:281`) — so the "declared NARROWING, not a derivation" framing in leg (c) is honest about
what it is. The zero-on-the-corpus claim for both `garbage_candidate_*` ids is structural, not lucky:
`auto_created` appears nowhere under `tests/fixtures/vault/` and both arms gate on it being truthy.

**Blocking 3 — AC-4's partition. Closed per-issue over four buckets, and the revision found a decline
site I missed.** Every line citation re-verified: `idx` defaults to `None` in the signature at `:828`;
the five guards at `:890`, `:906`, `:913`, `:935-936` and the fall-through at `:963-973`; the gate
raising at `:947` *before* `fixed += file_fixed` at `:949`; the second write at `:960-975` running
after that fold with its own `fixed += 1` at `:972`, outside `file_fixed` entirely; the uncounted
print at `:993-994`. `FixOutcome` is still two-field at `:820-825` and `NameGateRefusalRecord` still
closed at `:805-818`, so the "extend the existing record, match its discipline" instinct is right.
The fifth site (`:963-973`) is real and I did not list it.

The four non-blocking notes are all actioned. The plant-collision note in particular: `@Tarnquil  Brenvik.md`
does not collide — the corpus carries `@Pellworth Brenvik.md` (`fixture_vault.py:334`),
`@Wexlund Tarnquil.md` (`:336`) and `@Oskaline Brenvik-Tarnquil.md` (`:240`) but no such stem — and
both tokens are `NAME_POOL` members (`:569`, `:574`), so the substitute is pool-clean as well as
collision-clean. Generalising the trap into constraint 7 is the right level to have fixed it at.

### Review

**Fit:** The design now moves with the estate rather than beside it on every axis the project has an
established answer for. The seam fix is `VaultFile` gaining a `read_error` sibling to the existing
`parse_error` (`lint_vault.py:97`, with the four `if vf.parse_error: … continue` guards already
written against that shape) — the same widening the file already knows how to consume. The vocabulary
is imported from `repositories/base.py:41-48` rather than re-spelled, which is the answer WI-020 gave
to "what does a batch loader do with a note it cannot load". `ast` lands in `tests/derivations.py`,
its single legal home, pinned by the live wall at `tests/test_fixture_vault.py:1309-1312`. The new
records match `NameGateRefusalRecord`'s closed-field discipline. Nothing here fights a pattern.

**Duplication:** Actively removed rather than added. A fourth spelling of `"unreadable"` is refused by
extending an existing wall's universe instead of writing a new check; the rule set is derived from the
script's syntax instead of re-listed; A3/A3b are both rejected on solve-in-one-place grounds with the
second home named (`writer.py`'s `yaml.dump`, shared by every `repo.save`), and A3b's rejection is
load-bearing — `frontmatter_write_arms` really is pinned by equality over
`python_files_under(PACKAGE_ROOT, SCRIPTS_ROOT)`, so dropping a `write_frontmatter` call would drag
two frozen wall sets for a cosmetic win.

**Boundaries:** The Phase-3 question is answered correctly and it is the strongest single decision in
the document. The structure being discarded is the FILENAME, at `read_vault:117-118`, where the
contract "a `VaultFile` per note" silently narrows to "per note I could decode" while five stem-keyed
consumers are written against the wider one. The fix is at the seam that discards it, not at the five
consumers that would each need to reconstruct it. `scripts/` stays a script (nothing imports it), and
the coupling `WI-030` would change is named as constraint 1 rather than pre-emptively refactored.

**Determinism boundary:** No capability is handed to an LLM here, so the dimension applies in its
sibling form — mechanical work must not rest on a *human* remembering either. AC-1(a) is that move
made twice: the rule set is read out of the script's own syntax rather than typed, and read from BOTH
sides so the emitter/branch agreement stops being a coincidence two hand-kept lists happen to have.
AC-2(c) is the one place the document knowingly stays on the narrowing side of that line, and it says
so ("a declared NARROWING, not a derivation") — see note 2 below for what its binding does and does
not buy.

**Reversibility:** High. The script is operator-invoked, nothing imports it, and the two record
extensions are additive. The one irreversible act in the neighbourhood — `quarantine_garbage` →
`vault_io.move_note` (`:1140`) — is the thing this item pins rather than touches. Both live runs are
`--report` and never `--fix`, which keeps the acceptance evidence obtainable without a separate
authorization to mutate Dave's vault; that restraint is stated twice and is correct both times.

**Generalization:** Calibrated. The derived rule set generalizes to rule six; the `classify_person_tier`
table deliberately does not, and pays for it with a syntax binding instead of pretending. A3's
YAML-formatting concern is pushed out to its own item with the blast radius priced (HAL9000,
exocortex, orchestrator) rather than smuggled in — that is the right call and the remaining open
question is the right one to leave for Dave.

**Cost & maintenance:** One session, no package code, no consumer blast radius, no new dependency,
two one-command conductor acts outside the cage. The maintenance cost that matters is the one this
item *creates*: a new derived-wall class plus a hand-kept arm table. The derived half maintains
itself; the hand-kept half is bounded at six rows and bound to a stated definition, which is about as
cheap as a narrowing gets.

**Build vs extend vs integrate:** Extend, throughout — `FixOutcome`, the `parse_error` shape, the
`skip_reason_literal_sites` universe, the corpus via `materialize_vault` rather than by growing it
(A2, which correctly prices the digest-plus-pool-row paired edit across the cage boundary). Nothing
new is built that an existing thing could carry.

**Prior art (outside view):** The item builds machinery around a constraint — the caged builder cannot
see the live vault — so this dimension is live, and the revision now answers it in writing. The
comparable products are the right ones and they cut against the first draft rather than for it: ruff
and ESLint each pair a fixture corpus with an ecosystem run over real repositories, and a design
shipping only the fixture half is the known-incomplete one. The divergence that remains — the exit run
is a conductor ship condition rather than an automated wall — is justified by a CITED CODE FACT
(`work_item_linter.py:167-170`, `:158`), not by reasoning, which is what LESSONS #19/#26 ask for at
design time. No deferral in this document hides behind an unnamed re-entry condition: A3 names the
target file for its own item, A3b states the two wall sets that make it not-a-one-liner, and the two
rejected exit mechanisms are recorded with the code that rejects them.

### Notes (non-blocking)

Four for the spec-writer. The first two are wrong-as-written clauses in criteria that are otherwise
right, and both are one-clause corrections — they are here rather than in a fourth round because the
approach is settled and neither changes it, but neither should survive to the signature.

1. **AC-3(a)'s closing clause inverts the wall it declares.** The leg says "BOTH move to
   `python_files_under(PACKAGE_ROOT, TESTS_ROOT, SCRIPTS_ROOT)` **and both declared-homes equalities
   grow the script's path**". Only the first half is right. `skip_reason_literal_sites`
   (`tests/derivations.py:1583-1606`) reports a file iff it contains a hand-typed `str` Constant EQUAL
   to a vocabulary member; the same leg requires the script to read the reason "from the imported
   constant rather than re-spelled as a literal", so `scripts/lint_vault.py` will never be a home. Add
   its path to the expected sets at `tests/test_fixture_vault.py:510-514` and `:1315-1318` and the
   equality goes RED, and the only way to green it is to hand-type `"unreadable"` in the script — the
   exact drift the leg exists to forbid. Correct edit: widen the UNIVERSE at `:508-509` and `:1302`,
   leave both declared-homes sets at their two members. Verified safe as a side effect: `:1302`'s
   `universe` local also feeds the `ast` single-home wall at `:1309-1312`, and `scripts/` contains no
   `ast` use at all, so that assertion is strengthened rather than reddened — worth saying in the spec
   so the builder does not treat the shared local as a hazard.

2. **AC-2(c)'s syntax binding is to the docstring, not to the code, so it does not hold the property
   the criterion claims for it.** The leg promises "a seventh arm added with or without a docstring
   line is RED". Counting `- ` bullets in `classify_person_tier`'s docstring Constant catches a
   seventh arm added *with* a docstring line (bullets 7 ≠ table 6) and misses one added *without* —
   the bullet count stays 6, the table stays 6, the assertion stays green, the new arm is untested,
   and that is the WI-131 single-literal gap this document invokes against a hand-listed rule set two
   criteria earlier. Cheapest honest fix: pair the docstring count with a code-side count from the
   same scan — `classify_person_tier` has exactly four `return "active"` sites (`:253`, `:276`,
   `:279`, `:282`), so asserting that count too makes a seventh arm added as a fifth `if` RED
   regardless of the docstring. Failing that, narrow the claim to what the binding delivers.

3. **AC-4(b)'s attribution rule does not resolve one crossing it makes possible.** An issue whose
   branch guard DECLINED sits on a file whose gate then refuses at `:947` — it has no write "carrying
   it" to be decided at, so it is both `declined` and on a refused file, and leg (a)'s pairwise
   disjointness needs a stated tie-break. Either say declines are attributed at the branch (so a
   decline on a refused file stays `declined`, which is the reading the guard-id record implies) or
   design the plant set so the two never co-occur on one file, and say which.

4. **AC-5(b)'s "WI-016's own census reader" does not currently reach the table it needs.** The typed
   readers are `census_class_rows` (`tests/test_fixture_vault.py:121`), `census_pool_rows` (`:139`),
   `census_meta` (`:144`) and `census_identity_residue` (`:380`) — none parses the five-row
   auto-fixable table at `docs/vault-shape-census.md:272-281`. A sixth reader is needed; the
   `CENSUS_DIGEST` fixity it rides on is over the whole file's bytes and is unaffected, so this is a
   small addition rather than a design question, but it is a write target nobody has declared yet.

```verdict
gate: architect
verdict: PROMOTE
date: 2026-09-10
model: claude-opus-5
note: All three round-1 blockers close on re-read, two of them better than prescribed and grounded in cited code (a precondition is HEAD-probed pre-build, so the exit run is correctly a ship condition, not a fence); the seam fix sits where the structure is discarded, the vocabulary and the `ast` home are reused rather than re-spelled, and the four residual findings are single-clause criterion corrections that speccing resolves without reopening the approach.
```


## AC Red-Team — 2026-09-10

**Referent read first:** the frozen `## Intent` sentence plus its 2026-09-10 sharpening — the outcome still owed is the third clause, "an operator can run `--fix` over a real vault and know, from what the tool tells them, exactly what it repaired, what it declined, and what it could not read" — then `### Examples of done`, then `## Problem / Motivation` and both currency audits, then the five `criteria` fences, then the cited code. Every load-bearing line citation in AC-1 through AC-5 was re-verified against this tree rather than trusted: the five emitters at `:341,357,386,530,596`, the five branches at `:888,896,903,911,929`, the five decline sites at `:890,906,913,935-936,963-973`, `FixOutcome` two-field at `:820-825`, `NameGateRefusalRecord` closed at `:805-818`; none of the ten Tier-1 branches in `name_validation.py:190-309` is a whitespace rule, and `name_gate.py:366-367`'s accept path really does emit `name` byte-for-byte. All hold.

Two of the three findings below land on the same clauses the 2026-09-10 architect round-2 review's own non-blocking notes named. I derived them independently before checking whether they'd already been raised, and I am escalating them anyway because the calibration question here differs from the architect's: not whether the approach needs reopening, but whether this exact candidate text is safe to present at Dave's D4a signature. A false claim about a wall's own guarantee, and an accounting invariant with an unresolved tie-break, are both live in the frozen candidate text right now.

**1. AC-4 — CRITICAL. The four-bucket accounting is never required to reach the thing a human reads.** Failure scenario: a builder implements `FixOutcome` with four fields and gets legs (a)-(c) fully green by driving `apply_fixes` directly against a planted vault — exactly as those legs are worded to require, and exactly as the existing precedent already does — while leaving `run_lint`'s summary print at `lint_vault.py:1198` unchanged (`f"Fixed {outcome.fixed} issues, refused {len(outcome.refused)}."`), or changing it and never checking it. AC-4(d)'s desc states only what must be true in prose; none of the four legs commits the `check:` to capturing real stdout from `run_lint(..., do_fix=True)` or `main()`. The live precedent for exactly this gap already exists in this file: `tests/test_lint_vault_fix_gate.py:276-281`'s `test_the_fix_outcome_surfaces_both_counts` carries a docstring claiming "the CLI surfaces the refusal count beside the fixed count" and then asserts only `FixOutcome._fields == ("fixed", "refused")` — never a single byte of printed output (confirmed: no test anywhere under `tests/` calls `run_lint` or captures stdout). A leg (d) written the same way is green while an operator staring at a real `--fix` run sees a line indistinguishable from today's. This is the uncovered-invocation-layer shape by name: AC-1 through AC-4 cover the functions that compute the four buckets; nothing covers the print statement that is the ONLY channel the Intent's "know, from what the tool tells them" promise reaches. What would have to change: leg (d)'s `check:` must capture actual stdout from `run_lint` (or `main()`) over a fixture exercising at least one of each of the five outcomes (repaired/refused/errored/declined/unreadable) and assert the printed line names all five by structural parse — not merely inspect the `FixOutcome`/declined-record types.

**2. AC-4(b) — MATERIAL. The per-issue partition's pairwise-disjointness has no stated tie-break for an issue that is both `declined` and on a gate-refused file.** Failure scenario: `apply_fixes`'s per-issue loop can hit one of the five decline guards (e.g. `meeting_missing_from_timeline`'s `mstem not in meetings` at `:913`) for one issue on a file, while a different issue on the SAME file (e.g. `person_missing_name`) later feeds `gate_write` a delta that raises `NameGateRefusal` — the raise happens once, after the per-issue loop, at `:947`, before `fixed += file_fixed` at `:949`. AC-4(a) demands the four sets be "pairwise disjoint BY ISSUE IDENTITY," but nothing in the text says whether the declined issue keeps its `declined` label or is swept into `refused` by an attribution rule written to say "every issue on a refused file is refused." Two internally-consistent implementations disagree here, and each will pass a `check:` written by the same hand that picked the rule — the AC pins whichever the builder happens to choose, not Dave's actual expectation. What would have to change: state the tie-break explicitly (e.g. "a decline is attributed at the branch and is never re-labeled by a later gate refusal on the same file") and add a planted file carrying both, so the rule is testable rather than merely assumed.

**3. AC-2(c) — MATERIAL. The desc asserts a guarantee its own described mechanism does not deliver.** `classify_person_tier`'s docstring (`lint_vault.py:236-242`) states six disjuncts; the code implements them as four `if ...: return "active"` statements (`:253,276,279,282`, re-verified). AC-2(c)'s text reads: "...the criterion asserts that count equals the number of arms the table declares, so a seventh arm added with or without a docstring line is RED." The clause "with or without a docstring line" is false of the mechanism actually described: a seventh arm added as a new `if ...: return "active"` with no new docstring bullet leaves the bullet count at 6, the table at 6, the assertion green — and the new arm, which AC-2's own `why` calls "the largest blast radius in the file," ships untested. Concrete scenario: a future edit adds `if fm.get("vip"): return "active"`; AC-2(c) stays green; a real person note is later relocated to `_quarantine/` on a classifier path nothing has ever exercised. What would have to change: bind the count to a code-side signal too (the `return "active"` site count, via the same `ast` scan), or drop the "with or without a docstring line" clause so the frozen text does not promise a guarantee the mechanism lacks.

Nothing else in the set failed the attack. AC-1's oracle table is total and two-sided over emitters and branches, each of its five per-rule oracles carries a planted discriminator the corpus cannot supply, and the `person_missing_name`/name-gate interaction was independently verified against `name_validation.py` and `name_gate.py` rather than trusted. AC-2(a)'s zero-counts are structural (`auto_created` occurs nowhere in the 53-note corpus) and re-verified. AC-3's four legs correctly separate "the skip is loud" from "the report stops lying about other notes," and its stem-index discriminator is real. AC-5's shape contract is falsifiable and its census cross-check is the right defense against the hermetic-acceptance trap the architect round already fixed at the `## Approach` level.

```verdict
gate: ac-red-team
verdict: REVISE
date: 2026-09-10
model: claude-sonnet-5
targets: AC-4, AC-2
prior: none
basis: folded-material
findings: 3/3
note: AC-4's four-bucket accounting is never required to reach the printed CLI summary (the WI-099/WI-100 uncovered-invocation-layer shape, with a live precedent of the exact gap already in tests/test_lint_vault_fix_gate.py), AC-4(b)'s pairwise-disjointness has no stated tie-break for a declined issue on a gate-refused file, and AC-2(c)'s desc claims a guarantee ("with or without a docstring line") its docstring-bullet-count mechanism does not deliver.
```


## Architectural Review — 2026-09-10 (round 3)

**Recommendation: REVISE — return to exploration**

### Trigger check

Fired for the reasons rounds 1 and 2 recorded; `## Approach`'s "Routing: architect" paragraph now
reads the table correctly. Nothing turns on it this round.

### The red-team fold, re-read against this tree — it is clean, and that matters for where my findings land

I re-executed the fold's citations rather than accepting them, because a fold that breeds its own next
finding and a fold that closes are opposite situations downstream. This one closes.

**Red-team 1 (AC-4(d), the print).** The mechanism the fold chose is real and correctly reasoned.
`redirect_stderr` really is this neighbourhood's idiom (`tests/test_lint_vault_fix_gate.py:260-261`)
and the battery's checks really are zero-argument with no fixtures, so `redirect_stdout` and not
`capsys` is right. The four end-to-end plants are producible, including the `declined` one nobody had
spotted, which I traced arm by arm rather than trusting: `WIKILINK_PATTERN` (`:60`) captures
`Meeting 20260104 Nonexistent ` with the inner trailing space, `check_links:510` strips it,
`MEETING_DATE_PATTERN` (`:158`, `^Meeting (\d{8})\b`) matches the stripped form, `:524`'s unique
candidate emits an auto-fixable repair whose `old` is the STRIPPED text — and neither
`[[Meeting 20260104 Nonexistent]]` nor `[[Meeting 20260104 Nonexistent|` is then present in the file,
so `:963-973` falls through incrementing nothing. The honesty clause about `errored` is also correct
rather than defensive: a corrupt fence emits the non-fixable `parse_error` at `:297-305` and
`continue`s, so it never reaches `apply_fixes` through `run_lint`'s own list.

**Red-team 2 (AC-4(b), the tie-break).** Ruled the only way the frame permits, and the frame really
does permit only that: the gate raises once at `:947`, after the per-issue loop, before
`fixed += file_fixed` at `:949`, and `idx` defaults to `None` in the signature at `:828` — so a
decline at `:913` and a refusal at `:947` genuinely co-occur on one file, and a declined issue put
nothing in `delta`. Attributing at the branch is the only statement that is true of the frame, and the
discriminating plant carries both.

**Red-team 3 (AC-2(c), the two counts).** Both numbers verified: the docstring states six disjuncts
(`:237-242`) and the body carries exactly four `return "active"` sites (`:253`, `:276`, `:279`,
`:282`). Naming the widened-condition residue in the desc rather than replacing one overclaim with a
smaller one is the right instinct and is the reason this fold does not need a fourth round on AC-2.

My round-2 notes 2 and 3 are the same two clauses and are closed with them. Notes **1 and 4 are not** —
the fold's own closing paragraph says so in as many words ("AC-1, AC-3 and AC-5 are untouched"). That
is what the finding below is about, and it is about a standard this document adopted THIS round.

### Blocking issue

**1. AC-3(a)'s closing clause instructs the wall state that only the forbidden literal can green — a
criterion greenable by committing the drift it exists to forbid (AC-3).** The leg opens by requiring
the reason be read "from the imported constant rather than re-spelled as a literal in the script or in
the test" and closes with: "BOTH move to `python_files_under(PACKAGE_ROOT, TESTS_ROOT, SCRIPTS_ROOT)`
**and both declared-homes equalities grow the script's path**." Those two halves cannot both be
satisfied. `skip_reason_literal_sites` (`tests/derivations.py:1583-1606`) reports a file **iff** it
contains a hand-typed `str` Constant equal to a vocabulary member — equality over parsed syntax, so an
import contributes nothing. The two declared-homes equalities
(`tests/test_fixture_vault.py:510-514`, and `:1315-1318` fed by the `universe` local at `:1302`) each
assert the reported set EQUALS a two-member set. Add `scripts/lint_vault.py` to those expected sets and
the wall is RED for as long as the script does the right thing, and the one edit that greens it is
hand-typing `"unreadable"` in `scripts/lint_vault.py` — the fourth spelling whose removal this leg's
own `why` says WI-016 Task 11 spent three edits on.

Failure scenario, and it ends GREEN, which is why it is blocking rather than a wording nit: a builder
discharging AC-3(a) literally adds the script's path to both expected sets, finds both walls red, and
resolves the red the way the criterion's last clause tells them to — `reason = "unreadable"` in the
script. Every wall in the suite is then green, AC-3(a) reads satisfied, and the vocabulary has the
fourth hand-typed home the criterion was written to make impossible. That is LESSONS #46 at design
time: a check whose green is reachable two ways, one of them the defect, is not evidence about the
defect. The correct edit is one clause — widen the UNIVERSE at `:508-509` and `:1302`, leave both
expected home sets at their two members, and assert the two-member equality still holds with the
script in the universe, which is the assertion that actually proves the script imports rather than
transcribes. Verified as a free side effect: `:1302`'s `universe` local also feeds the `ast`
single-home wall at `:1309-1312`, and `scripts/` contains no `ast` use at all (grep over
`scripts/`: no matches), so widening strengthens that wall rather than reddening it — worth stating in
the criterion so the shared local does not read as a hazard.

**Why this blocks now when the identical clause was a note in round 2, stated plainly rather than
dressed up as a new discovery.** Two things changed between rounds, both inside this document. First,
the standard: the red-team escalated on the ground that "what Dave signs at D4a is this text and not
the spec that follows it," and the fold conceded it in writing (`### Revision — 2026-09-10 (round
2)`, opening paragraph) — this clause is the same class as the AC-2(c) overclaim that concession was
made about, one criterion over. Second, the evidence: a note-only disposition has now been tried on
this exact clause for one full round and produced no edit, by explicit decision. Under the standard
the fold adopted, a clause that would make Dave's signature endorse "hand-type the literal" is not
speccing's to resolve. The remedy is two sentences of criterion text and I am asking for nothing else
architectural.

### Suggested adjustments

- AC-3(a): widen the universe at both sites; leave both declared-homes expected sets at two members;
  say that the two-member equality holding WITH `scripts/` in the universe is the assertion, and note
  the `ast` wall is strengthened by the same widening.
- AC-5(b) and the `## Write Targets` handoff note: declare the census reader the criterion needs
  (note 1 below) and correct the `test_lint_vault_fix_gate.py` inventory (note 2).
- AC-3(d): one-word citation fix (note 3).

### Notes (non-blocking)

1. **AC-5(b) still names a reader that does not exist, and the table it must read is not keyed the way
   the criterion assumes.** Re-confirmed this tree: the typed census readers are `census_class_rows`
   (`tests/test_fixture_vault.py:121`), `census_pool_rows` (`:139`), `census_meta` (`:144`) and
   `census_identity_residue` (`:380`) — none parses the five-row auto-fixable table at
   `docs/vault-shape-census.md:272-281`. A sixth reader is a small addition riding the same
   whole-file `CENSUS_DIGEST` fixity, so this is not a design question; it is a write target in a file
   that is ALREADY a paired target for two other reasons (constraint 8), and it is still undeclared.
   The second half is new since round 2 and is why the reader is not purely mechanical: that table's
   key column is a MESSAGE SHAPE (`Missing sections: …`, `Attended [[…]] but it's not in Timeline`,
   `auto_created is string '…' instead of bool`, …), not a rule id, so AC-5(b)'s "compared rule by
   rule" needs a declared shape→rule-id mapping. Declare it in the criterion or in the test module —
   wherever it lands it is a five-row hand-kept table, which is acceptable at that size but should be
   a decision rather than a discovery.
2. **The `test_lint_vault_fix_gate.py` write-target inventory says three assertions and there are
   more, and which of them move turns on a naming question nobody has answered.** The handoff note
   names `:279` (`_fields`) plus the numeric `outcome.fixed` assertions at `:166` and `:201`. The
   module actually touches those fields at `:117-118`, `:166`, `:200-201`, `:230-231`, `:265`, `:270`,
   `:279` and `:281`. Only `:279` goes red by construction — **if** `FixOutcome` keeps the field names
   `fixed` and `refused` and merely gains two. But A6, AC-4(a) and the `## Approach` paragraph all
   spell the buckets `repaired / refused / errored / declined`, and the field is `fixed` (`:823`); if
   the builder follows the prose and renames, five more assertions move. Decide the field name at
   spec time and make the inventory match it. The inventory was offered as the precise list, which is
   exactly the kind of number a builder trusts instead of re-deriving.
3. **AC-3(d) cites the wrong leg of AC-4.** It says the unreadable note "is accounted for by
   AC-4(c)'s separate unreadable-note count". AC-4(c) is the two-new-records leg; the unreadable count
   is AC-4(d)'s fifth printed figure. One-word fix, and worth making because AC-3(d)'s whole job is to
   place the unreadable note OUTSIDE AC-4's partition, so the pointer that says where it IS counted
   should land on the leg that counts it.

```verdict
gate: architect
verdict: REVISE
date: 2026-09-10
model: claude-opus-5
targets: AC-3, AC-5, #write-targets
prior: mixed
basis: folded-material
findings: 1/4
note: The red-team fold is clean and closes all three of its findings (mechanism, citations and plants re-executed), but AC-3(a)'s untouched closing clause requires the two declared-homes equalities to gain the script's path — and `skip_reason_literal_sites` reports a file only if it hand-types the literal, so the criterion's own remedy is the fourth spelling of `"unreadable"` it exists to forbid, greenable and wrong; the fold itself adopted the standard that a wrong-as-written clause must not reach Dave's signature, and one note-only round on this clause produced no edit.
```


## AC Red-Team — 2026-09-10 (round 2)

**Referent read first, cold-start:** the frozen `## Intent` sentence and its 2026-09-10 sharpening,
`### Examples of done`, both currency audits, `## Exploration Notes`, all three architect rounds and
my own round-1 section, then the five `criteria` fences as they stand in this tree now, then the
cited code — read fresh rather than assumed from the prior round's memory of it.

**My round-1 fold, re-verified against the actual code rather than trusted from the revision's
prose.** All three CLOSED and held.
- **AC-4(d) (the print).** `scripts/lint_vault.py:1198-1199` is still the bare
  `f"Fixed {outcome.fixed} issues, refused {len(outcome.refused)}."` — unchanged, which is exactly
  why the fold's leg (d) now captures real `run_lint` stdout rather than inspecting `FixOutcome`.
  Confirmed `apply_fixes` still returns a two-field `FixOutcome(fixed=fixed, refused=tuple(refused))`
  at `:996`, and every cited decline site is real: `isinstance(raw, str)` at `:890`, `if expected` at
  `:906`, `if mstem and mstem in meetings` at `:913` with `idx: Optional[dict] = None` at `:828`,
  `except (json.JSONDecodeError, KeyError): pass` at `:935-936`, and the fall-through at `:963-973`
  where neither `[[old]]` nor `[[old|` matching leaves `wl_changed` False and increments nothing.
- **AC-4(b) (the tie-break).** Confirmed the frame forces the co-occurrence the tie-break resolves:
  `fm.update(gate_write(...))` at `:947` runs, and only if it does not raise does `fixed += file_fixed`
  execute at `:949` — so a decline inside the per-issue loop and a gate refusal on the same file are
  both live possibilities, and attributing the decline at its branch (never re-labeled) is the only
  statement true of this frame.
- **AC-2(c) (the two counts).** Read `classify_person_tier` directly (`lint_vault.py:233-283`): the
  docstring states six disjuncts (`:236-242`) and the body has exactly four `return "active"` sites
  (`:252-253`, `:275-276`, `:278-279`, `:281-282`). Both numbers the fold added are correct, and
  binding both is what makes a widened-condition seventh arm (no new bullet, no new `return`) the
  named, bounded residue rather than a silent hole.

So: `prior: held`.

**New finding, independently derived before reading the architect's round-3 verdict, then cross-checked
against it — it agrees, and I re-verified the code myself rather than taking either the architect's or
the document's word for it.**

**AC-3(a) — CRITICAL. The leg's own remedy is greenable only by committing the drift it exists to
forbid.** Failure scenario: a builder implements `read_vault`'s new `read_error` path correctly —
importing `SKIP_REASONS.UNREADABLE` from `obsidian_schemas.repositories.base` and using the imported
name, never a bare string — and then discharges AC-3(a)'s literal closing instruction: widen the
universe at `tests/test_fixture_vault.py:508-509` and `:1302` to include `scripts/lint_vault.py`, and
make "both declared-homes equalities grow the script's path" (i.e. the two-member expected sets at
`:510-514` and `:1315-1318` gain a third member for the script). I read `skip_reason_literal_sites`
itself (`tests/derivations.py:1583-1606`) rather than trusting either gate's paraphrase of it: it walks
parsed `ast.Constant` nodes and reports a file iff one of them is a **string literal equal to** a
`SKIP_REASONS` member — an import statement or a `SKIP_REASONS.UNREADABLE` attribute access contributes
no such Constant. So a correctly-written `lint_vault.py` is *absent* from the derivation's returned set,
the widened three-member equality the leg demands is RED, and the only edit that makes it green is
`reason = "unreadable"` hand-typed in the script — the exact fourth spelling this leg's own `why` cites
WI-016 Task 11 as having spent three edits removing. A builder following AC-3(a) to a green check
therefore ships the regression the criterion was written to make impossible, and a builder who does the
right thing instead fails a criterion Dave signed. This is the "check that cannot execute [correctly]"
class one level down: not an absent `check:`, but a `check:` whose only passing path runs through the
defect. What would have to change: widen the UNIVERSE at both call sites to include `scripts/`, but
leave both declared-homes EXPECTED sets at their current two members, and assert that the two-member
equality still holds *with the script in the universe* — that is the assertion that actually proves
the script imports rather than transcribes. (Free side effect, also independently confirmed: `:1302`'s
`universe` local also feeds the `ast` single-home wall at `:1309-1312`, and a repo-wide grep finds no
`ast` usage under `scripts/`, so the same widening strengthens that wall instead of reddening it.)

I am escalating this as my own finding, on the same footing as my round-1 findings, rather than
deferring to the architect's round-3 verdict: the calibration question for this gate is whether this
exact candidate text is safe to present at Dave's D4a signature, and it is not — a criterion a
correct implementation cannot pass is the sharpest form of "satisfied while the Intent goes unserved"
this document currently contains.

Nothing else in the set failed a fresh attack. AC-1's oracle table is total, two-sided, and its five
per-rule plants were re-checked against the actual branch code above — each still has the corpus-absent
discriminator it claims. AC-2(a)'s zero-counts are structural (`auto_created` appears nowhere under
`tests/fixtures/vault/`) and AC-2(c)'s two-count binding is confirmed correct against the live function.
AC-3(b)–(d) are unchanged from my round-1 pass and I found nothing new in them beyond the architect's
already-recorded citation nit at (d). AC-4's four-bucket partition, its attribution tie-break, and its
stdout cross-check are all held per above. AC-5's shape contract is unchanged and its open
implementation gap (a census reader that does not yet exist) is a write-target completeness question
for the spec-writer, not a criterion that can be satisfied by a wrong implementation — it does not meet
this gate's bar for a finding.

```verdict
gate: ac-red-team
verdict: REVISE
date: 2026-09-10
model: claude-sonnet-5
targets: AC-3
prior: held
basis: original
findings: 1/1
note: AC-3(a)'s closing clause is greenable only by hand-typing a SKIP_REASONS literal in scripts/lint_vault.py — the exact drift the leg exists to forbid — because skip_reason_literal_sites (tests/derivations.py:1583-1606) matches string-literal Constants only, so a correct import-based fix cannot pass the widened declared-homes equality the leg's own closing sentence demands; independently re-derived and confirmed against the code, not taken from the architect's round-3 verdict. My round-1 findings (AC-4(d), AC-4(b), AC-2(c)) all re-verify as held.
```


## Data Audit — 2026-09-15

**Recommendation: REVISE — return to spec writer / ideation**

### Trigger check

**Class 1 AND Class 2, both fired, and neither is marginal.** Class 1: this document's criteria rest
on quantified claims about two corpora — the frozen 53-note fixture vault (which rules fire on it and
at what multiplicity) and Dave's live vault (five auto-fixable counts, five stem-keyed counts, the
undecodable count). Class 2: AC-5 is a rule whose correctness is defined entirely by its effect
against an artifact that ALREADY EXISTS IN HEAD — `docs/lint-vault-live-baseline.md`, committed
2026-09-10 — so "does this criterion pass against what is on the tree today" is a question with a
measurable answer, and it is the WI-040/`--enforce` shape verbatim: a rule reasoned about for a
future build but never run against the state that exists.

Every predicate below was executed against THIS tree today (worktree `cage-wt-ecmquixm`, HEAD
`09ebc1c`). This gate's granted tools are Read/Grep/Glob/Edit and no shell, so every claim is read off
bytes; nothing is estimated and nothing is carried forward from a prior gate's paraphrase.

### What holds — the citation frame, re-ground rather than trusted

The document was written against HEAD `d6fbbb3` on 2026-09-10; WI-023 shipped on 2026-09-11, so the
whole citation frame was re-run rather than assumed stable. It holds, at the byte level:

- The five `auto_fixable=True` emitters are at `:344, :360, :389, :533, :599` with their check
  literals at `:341, :357, :386, :530, :596` (both spellings in this doc are correct — AC-1 cites the
  literal lines, the architect cited the flag lines), and the five `issue.check ==` branches are at
  `:888, :896, :903, :911, :929`. The only other two comparisons (`:1125, :1127`) are
  `quarantine_garbage`'s. The two sets AC-1(a) asserts equal ARE equal at five members today, and the
  derivation domain is CLOSED: `auto_fixable` appears at exactly nine sites in the script and every
  constructing one is the literal `auto_fixable=True` — no variable form exists for the `ast` scan to
  miss.
- `except Exception: continue` at `:115-118`; `VaultFile` at `:88-97` with `parse_error` last;
  `build_indexes`' stem keying at `:179-197`; `NameGateRefusalRecord` closed at `:805-818`;
  `FixOutcome(fixed, refused)` at `:820-825`; `apply_fixes`' `idx=None` default at `:828`; the five
  decline sites at `:890`, `:906`, `:913`, `:935-936` and the fall-through at `:963-973`; the
  unconditional `gate_write` at `:947` landing before `fixed += file_fixed` at `:949`; the second
  write at `:960-975` with its own `fixed += 1` at `:972` outside `file_fixed`; the uncounted print at
  `:993-994`; `FixOutcome(...)` at `:996`; the summary print at `:1198` inside `if fixable:`
  (`:1191-1199`); `read_vault` pre-fix at `:1160`, `idx` passed at `:1194`, re-scan at `:1201`.
  `person_missing_name` at `:896-901` really has no guard, and `:897` really is
  `fpath.stem.lstrip("@")`.
- The nine `.fixed` assertion sites the handoff note enumerates are all exactly where it says:
  `test_lint_vault_fix_gate.py:117, :166, :201, :270, :279, :281` plus
  `test_name_gate_refusals.py:275`, `test_name_gate_delta_rule.py:203`,
  `test_name_gate_identifiers.py:425`. `FixOutcome._fields == ("fixed", "refused")` at `:279`.
- Both universe sites are unwidened and both expected sets are two-member:
  `tests/test_fixture_vault.py:508-509` / `:510-514` and `:1302` / `:1315-1318`, with the `ast`
  single-home wall sharing the `:1302` local at `:1309-1312`. AC-3(a)'s safety facts re-verify: a
  case-insensitive grep of `scripts/` for `unreadable` / `schema-drift` / `malformed-frontmatter`
  returns nothing, and `scripts/` uses `ast` nowhere — so the widening strengthens both walls.
- Corpus premises: 53 `.md` files; zero occurrences of `auto_created` anywhere under
  `tests/fixtures/vault/`; `@Dave  Marrowyn Fennwick.md` EXISTS (constraint 7 is real) and
  `@Tarnquil  Brenvik.md` does NOT (the substituted plant stem is collision-free); the non-UTF-8
  member is `@Isolde Varnholt.md`. The census's five rows are at `docs/vault-shape-census.md:272-281`
  carrying 821 / 315 / 19 / 0 / 0, and the `Empty name` row really is annotated `(structural)` while
  its emitter's category at `:388` is `"completeness"` — AC-5(b)'s mis-join finding is real.

Two harmless citation drifts, recorded so a later reader is not confused rather than as findings:
`tests/derivations.py` has moved ~2 lines since the document was written — `SCRIPTS_ROOT` is at `:33`
(doc says `:31`), `skip_reason_literal_sites` at `:1585-1608` (doc says `:1583-1606`),
`python_files_under` at `:185-202` (doc says `:183-197`). The mechanisms are exactly as described; only
the ordinals moved.

### Counterexample hunt — the write-causing domain

The Intent and AC-2 quantify universally over an enumerable domain ("EVERY DETECTOR THAT CAUSES A
WRITE", pinned at seven members), so the universal was walked for members that are false by design
rather than merely counted.

**DOMAIN:** every vault-mutating call site in `scripts/lint_vault.py`. **PREDICATE:** grep for
`vault_io\.` / `write_text` / `\.rename\(` / `shutil\.` / `os\.replace` / `mkdir` over the whole file,
then trace each hit back to the check id that drives it.

**Result — the domain is closed at exactly four mutation sites and the seven-member set is COMPLETE.**
`vault_io.write_note` at `:957` and `:975` (both inside `apply_fixes`, reachable only from the five
auto-fixable branches) and `vault_io.ensure_dir` at `:1134` + `vault_io.move_note` at `:1140` (both
inside `quarantine_garbage`, reachable only from `garbage_candidate_company` `:1125` and
`garbage_candidate_person` `:1127`). `vault_io.read_note` at `:859` and `:961` is not a mutation.
There is no fifth writer, no scheduled or external one, and no opt-in-gated arm. **No false-by-design
member found**, and AC-2's widening from five to seven — the fold that answered the architect's
blocking 2 — is exactly right rather than accidentally right.

One member of a NEIGHBOURING universal IS false by design and is already correctly narrowed, recorded
so nobody reads it as a gap: the Intent's "no note may disappear from the report just because its
bytes would not decode" does not reach `should_skip` (`:105-107`), which drops six whole directories
(`.obsidian`, `Templates`, `src`, `.trash`, `_quarantine`, `_merged_dupes`) by declared design. The
Intent's own `because` clause already excludes them; AC-3 inherits that narrowing correctly.

### Premise vs reality — the three findings

**FINDING 1 (BLOCKING). AC-5(b) is RED BY CONSTRUCTION against the artifact already in HEAD.** The leg
reads: "§1's five counts are compared rule by rule against `docs/vault-shape-census.md:272-281` …
Equal is green. A divergence is RED". The artifact it reads was committed on 2026-09-10 and its own §1
table ALREADY CARRIES A DIVERGENCE, which it states openly:

| rule | census 2026-09-07 | baseline 2026-09-10 | delta |
|---|---|---|---|
| `missing_body_sections` | 821 | **835** | **+14** |
| `meeting_missing_from_timeline` | 315 | 315 | 0 |
| `field_type_mismatch` | 19 | 19 | 0 |
| `person_missing_name` | 0 | 0 | 0 |
| `broken_wikilink` (fixable sub-case) | 0 | 0 | 0 |

Both numbers were read off the bytes (`docs/vault-shape-census.md:277` = 821;
`docs/lint-vault-live-baseline.md:79` = 835, and its `:84` totals 1,169 of 4,764 against the census's
1,155 of 4,730). The baseline's own prose calls the +14 "three days of vault growth … the staleness
signal AC-5 exists to raise, not an error in either measurement" — and that is the defect. AC-5 is
`kind: test`; a `check` that goes RED is a FAILING acceptance criterion, not a signal on a dashboard.
As written, the builder cannot discharge AC-5 green against an artifact that is frozen, correct, and
already committed, and the battery runs pre-ship. The criterion's intent ("a drifted vault is visible
rather than silently trusted") is right; its mechanism confuses *reporting* a divergence with
*failing* on one. It needs a tolerance rule that is decided here rather than at build time — the
natural one, and the one the data supports, is that a rule whose census count is ZERO must still be
zero (the two zeroes are what AC-1's "no live subject" argument leans on) while a non-zero rule may
drift, with the delta REPORTED and the run date recorded. That is a ruling only this gate has the
numbers to make, and it must be made before the criterion is built against.

**FINDING 2 (BLOCKING). AC-5(a)'s per-section shape contract is not satisfied by the artifact in
HEAD, in three of four sections.** The leg requires that "each of §0–§3 carries a `Command:` line, a
fenced block holding the literal argv, a fenced block holding verbatim stdout, and a 40-hex tree SHA".
Read against `docs/lint-vault-live-baseline.md` as committed:

- `## 0. The run` — has two fenced argv blocks and one fenced stdout block, but no line reading
  `Command:` (it reads "Command (the JSON report; …):") and no per-section 40-hex SHA. The one 40-hex
  tree SHA in the file is global, at `:12`; the hex at `:26` is a 64-hex sha256 of stdout, not a tree
  SHA.
- `## 1. The five auto-fixable counts …` — a derived markdown table. **No command line, no argv fence,
  no stdout fence, no SHA.** None of the four elements.
- `## 2. The five stem-keyed check counts …` — same: **none of the four elements.**
- `## 3. The undecodable scan` — has an argv fence and a stdout fence, but no `Command:` line and no
  SHA.

So zero of four sections satisfy the contract as written, and two of four satisfy none of it. This is
not a defect in the artifact: §1 and §2 are DERIVED from §0's single report and re-running a command
for each would be a second walk of Dave's vault to produce numbers §0 already contains. The artifact
made the right call and the criterion describes a different artifact. The shape contract in the fence's
`why:` and the leg that reads it back must be narrowed to what a derived section can carry — a stated
derivation from §0's report — or §1/§2 must be declared exempt from the four-element rule by name. As
it stands a builder discharging AC-5(a) literally would have to edit the frozen entry measurement,
which is the one artifact this item is not allowed to reshape after the fact.

Both findings land on the same criterion and both have the same origin: AC-5 was written on 2026-09-10
as the fold answering the architect's blocking finding 1, describing an artifact that did not yet
exist, and the conductor's measurement landed afterwards. Nobody re-read the criterion against the
bytes that arrived. That is precisely the WI-042 staleness class, and it is the reason this gate
stands between `exploring` and `specced`.

**FINDING 3 (material, non-blocking). AC-2(a)'s corpus multiplicity is 8 issues over 5 distinct
`(filename, check)` pairs, and the leg's assertion vehicle cannot express the 8.** The document's
exploration section states "Five well-formed meetings declare 8 attendee entries between them" and
marks the count NOT EXECUTED ("the build's first run confirms it"). It is now executed, by reading the
corpus: `Meeting 20260104` (Thrandell Ibberly, Isolde Quenlaw), `20260118` (Thrandell Ibberly),
`20260205` (Morvette Harkwell, Caldreth Zebrant), `20260301` (Elowick Varnholt), `20260315` (Isolde
Quenlaw, Morvette Harkwell) = **8 pairs**; `Meeting 20260212` is the malformed-frontmatter specimen
whose `fm={}` leaves `entity_type == ""`, so it never enters the `meetings` index (`:187-192`) ✓. All
five named attendees have person notes and every one of their `## Timeline` sections is empty (spot-read
`@Thrandell Ibberly.md:20`), and `check_timeline` `:578-602` emits one issue PER PAIR keyed on
`pvf.path`. But three of the five people attend two meetings each, so those 8 issues collapse to **5
distinct `(filename, check)` pairs**. AC-2(a) asserts "the set of `(filename, check)` pairs … equals a
declared table" and then describes that table as holding "one issue per (meeting, attendee) pair" — a
set of pairs cannot hold 8 entries with 5 distinct values. A build that declares a 5-row table is green
while emitting only one issue per person, dropping three; the over/under-fire class the criterion
exists to catch is exactly what slips through. One clause fixes it (count issues per `(path, check)`,
not membership), and the number to write down is 8-over-5.

### Not findings, but the audit's other measured results

- **The live undecodable count is ZERO** (`docs/lint-vault-live-baseline.md:120-122`, 3,952 paths
  walked). AC-3's live subject population is empty on this snapshot. This does not weaken AC-3 — the
  document argued this case in advance and the frozen corpus carries the specimen — but it should be
  read as: AC-3 is PROPHYLACTIC on day one, and the exit half of the bracket can only confirm the count
  stays 0. The struck Open Question was answered correctly by execution rather than by a sign-off turn.
- **`docs/lint-vault-live-baseline.md` IS in HEAD**, so the second `kind: precondition` fence's
  HEAD-membership probe passes and the ordering promise ("in HEAD before the criteria are frozen") was
  kept — the artifact predates the 2026-09-15 sign-off by five days. The fence's `grounds:` is
  discharged; only the leg that READS it back is wrong.
- Minor imprecision, not worth a criterion edit: the exploration says "there is exactly ONE `[[` in the
  whole corpus". There are two, on one frontmatter line (`Harkwell Tessamund.md:7`,
  `related: ["[[Voxleaf Kelmarra]]", "[[Thrandell Ibberly]]"]`). `check_links` reads `vf.body`, so the
  conclusion — zero `broken_wikilink` subjects in the corpus — is unchanged.

### Required grounding

1. **Rule AC-5(b)'s tolerance.** Decide, with the +14 in front of you, what a divergence DOES: report
   with both numbers and the run date, versus fail the check. The zero-count rules should almost
   certainly stay strict (AC-1's "no live subject" argument leans on them) while non-zero rules
   tolerate drift. Whatever is chosen, the criterion must be green against
   `docs/lint-vault-live-baseline.md` as committed, without editing that file.
2. **Narrow AC-5(a)'s shape contract to what §1 and §2 actually are** — derived tables over §0's single
   report — or name them exempt from the four-element rule. Correct the same contract in the second
   `kind: precondition` fence's `why:`, since the leg and the fence must not disagree.
3. **Write 8-over-5 into AC-2(a)** and make the assertion count issues per `(path, check)` rather than
   asserting set membership, so a build emitting 5 of the 8 is RED.

These are three clause-level edits to two criteria; nothing in `## Approach`, `## Intent`, the write
targets, AC-1, AC-3 or AC-4 is touched, and no approach decision reopens. Note for the conductor: AC-2
and AC-5 carry frozen `ac_hash` values from the 2026-09-15 sign-off (`1e40f7ae8765`, `7036c93e9f21`), so
the re-signature is Dave's call and not the spec-writer's.

```verdict
gate: data-premise
verdict: REVISE
date: 2026-09-15
model: claude-opus-5
targets: AC-5, AC-2
prior: none
basis: folded-material
findings: 2/3
note: AC-5 is RED by construction against the very artifact it reads — `docs/lint-vault-live-baseline.md` has been in HEAD since 2026-09-10 carrying `missing_body_sections` 835 against the frozen census's 821, and leg (b) says a divergence is RED while leg (a) demands a Command line, an argv fence, a verbatim-stdout fence and a 40-hex tree SHA in each of §0–§3 where §1 and §2 are derived tables carrying none of the four; the criterion was written as a fold describing an artifact that did not yet exist and nobody re-read it against the bytes that arrived, which is the WI-042 staleness class exactly. Separately AC-2(a)'s corpus multiplicity is 8 issues over 5 distinct (filename, check) pairs — three of the five attendees sit in two meetings each — so its set-membership vehicle cannot express the 8 and a build emitting 5 is green. Everything else re-grounds: all five emitter/branch pairs, the nine `.fixed` sites, both universe sites and their two-member expected sets, the census rows, the zero-`auto_created` corpus, the collision-free plant stem, and a counterexample hunt over every vault-mutating call site (`:957`, `:975`, `:1134`, `:1140`) that finds AC-2's seven-member write-causing set complete with no false-by-design member.
```

