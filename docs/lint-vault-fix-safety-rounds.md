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


## Threat Model — 2026-09-15

**Recommendation: PROMOTE to threat-modeled**

First threat-model round on this item, cold-start — there is no prior `## Threat Model` section on this
document and none in `docs/lint-vault-fix-safety-rounds.md` (grepped both), so nothing is carried
forward and every citation below was re-read off this tree rather than taken from a prior gate's
paraphrase.

### Trigger check

Four triggers fire, and they are not incidental to the item — they are what it is:

- **Filesystem operations on user-owned files.** `--fix` writes Dave's notes (`apply_fixes:957`,
  `:975`) and `--quarantine` MOVES them (`quarantine_garbage:1140` → `vault_io.move_note`).
- **Untrusted input.** The whole input is vault bytes, and this item adds a NEW crossing: the bytes
  of a note that does not decode (`read_vault:115-118`).
- **Persistence.** Two conductor acts commit live-vault-derived measurements into the repo
  (`docs/lint-vault-live-baseline.md`), and the build adds a floor-resident test module that drives
  the tool's MUTATING entry point.
- **Information disclosure surface.** The item's own Intent is that an operator reads what the tool
  tells them; §10.7 already names the trust boundary, and `obsidian_schemas/errors.py:200-261` is a
  standing bounded-projection contract this change has to stay inside.

Nothing here is a skip pattern: it is not doc-only, not an internal refactor, and the "bug fix in
existing code" arm does not apply because the fix changes what the tool reports about a user's files.

### STRIDE review

**Spoofing — nothing.** No authentication boundary, no identity claim, no OAuth or MCP scope on this
path. `person_missing_name` writes a filename-derived `name` into frontmatter (`apply_fixes:897`,
`fpath.stem.lstrip("@")`), which is an identity-shaped write, but it is gated unchanged by
`gate_write` at `:947` and AC-1(c) pins the value byte-for-byte. No new surface.

**Tampering — the item strictly REDUCES the wrong-write surface, and I checked the reverse direction
rather than assuming it.** VD-1's repair widens `all_stems` / `stem_to_file` / `stripped_to_stem`
(`build_indexes:179-197`), and the obvious question is whether a wider index can create an
auto-fixable repair that does not exist today. It cannot, and the reason is in three places I read
rather than reasoned about: `check_links:513` and `:515` both `continue` on a hit, so a wider index
only REMOVES `broken_wikilink` emissions; `check_links:463`, `:481`, `:496` all emit on a MISS, so a
wider index only removes those too; and the one index that could manufacture a new fixable repair —
`meeting_date_index`, whose `len(candidates) == 1` at `:524` is what makes a link rewritable — is
populated only inside `elif vf.entity_type == "meeting"` at `:191-196`, which a `read_error`
`VaultFile` carrying `entity_type=""` never reaches. Design §1's choice of `entity_type=""` is
therefore load-bearing for tampering and not merely for check-silence; it is the field that keeps an
undecodable note out of every write-target index. The same gate closes the move arm: `check_noise`'s
`at_stems` at `:733-735` and `orphaned_note` at `:722` both require a truthy `vf.entity_type`, and
`garbage_candidate_*` require a truthy `auto_created` off frontmatter that stays `{}` — so an
unreadable note is unreachable by `quarantine_garbage`, which is what AC-3(d) asserts. Concurrency is
WI-004's and is untouched: one reentrant `note_lock` spanning both writes, each `write_note` carrying
the stamp of its own freshly-read bytes (`:858-859`, `:957`, `:961`, `:975`), and the `fpath.exists()`
probe at `:853` is read-only with its race landing in the per-file handler. The item adds no write,
no `delta` key and no gate call.

**Repudiation — this item IS the repudiation fix, and one clause of it contradicts its own signed
criterion.** VD-3 is a textbook audit-trail hole (a failure that prints and is counted nowhere) and
the four-bucket partition closes it. But Design §4 places the credit fold at "the END of the
`with vault_io.note_lock(fpath):` block, after the wikilink pass", and that placement cannot produce
what AC-4(b) — signed, `ac_hash_AC-4: 5cc1a0cc3737` — requires of its own discriminating plant. AC-4(b)
names one file carrying a `missing_body_sections` issue "(repaired, committed at `:957`)" beside a
`broken_wikilink` issue "whose write raises", and requires the first to be `repaired` and the second
`errored`. Under §4's placement the raise at `:975` leaves the `with` block before the fold ever runs,
so BOTH issues are still in `undecided` when the handler catches and BOTH become `errored` — a write
that COMMITTED to a user's note reported as one that failed. That is the same class of defect the
item exists to remove (the summary misstating what happened to real files), one frame over, authored
inside the fix; it is the direction that makes an operator re-run a repair already on disk. It is
also cheap to close without losing §4's genuine correction, and the correction is worth keeping —
today `fixed` really is credited at `:949` before the first `write_note` can raise at `:957`. The rule
that satisfies both: **an issue is credited at the point its own write commits** — the first-write
issues leave `undecided` immediately after `write_note` returns at `:957`, the wikilink issues after
`:975` returns — which preserves "nothing is credited before its write commits" and makes AC-4(b)'s
plant come out as signed. Carried as **M4** below rather than as a REVISE, because the signed
criterion already states the correct behaviour and only the Design's prose disagrees with it; the
fold rule (WI-128, D8) is exactly the machinery for a requirement that needs one sentence in a task.

**Information disclosure — the category that matters here, and the design is already right on three
of four surfaces.** The new crossing is a note whose bytes do not decode, and the answer is to never
decode them: Design §1 sets `read_error=UNREADABLE` — the imported constant, not `str(exc)` — and §2's
message interpolates only that value. That is not a stylistic choice, it is WI-020's M5 applied
correctly: `obsidian_schemas/errors.py:255-261` names `UnicodeDecodeError` explicitly as a cause that
"renders note content from str()" and is SUPPRESSED, and the decode failure on this path is exactly
that type. Carried as **M1**. The two new records are bounded for the same reason and the reason is
stated in the code they sit beside — `NameGateRefusalRecord:805-818`'s own docstring closes its field
set because "this run walks the whole vault and its output is what an operator reads and pastes" —
so `FixErrorRecord.reason` as `type(exc).__name__` and `FixDeclineRecord.guard` as a `DECLINE_GUARDS`
member are the right shapes; carried as **M2**. The summary line is five integers and carries no path
at all (§5). The committed evidence artifact is clean and I read its bytes rather than its contract:
`docs/lint-vault-live-baseline.md` reproduces no note filename, substitutes the vault root to `$VAULT`
in every verbatim block, and deliberately does NOT reproduce the 1,380,432-byte JSON report that
"names live notes" (`:19-20`), carrying only its sha256 — the single most valuable decision in that
artifact and one no criterion forced.

**Denial of service — nothing realistic.** No network, no third-party call, no recursion, no retry
loop (the Scope Boundary refuses one deliberately). Both new record lists are bounded by the issue
count (1,169 today) and hold a `Path` plus two short strings each. `read_vault` now appends a
`VaultFile` per undecodable note instead of dropping it, which is O(1) per file over a walk that
already visits it. The one availability-shaped consequence is chosen rather than discovered:
`unreadable_note` is `Severity.ERROR`, and `main:1311-1312` exits 1 on any ERROR — Design §2 states
this and states that the live vault already exits 1 on three `parse_error` rows, so no live exit code
moves today.

**Elevation of privilege — one real finding, and it is the only genuinely NEW hazard this build
introduces.** VD-4 establishes that nothing under `tests/` calls `run_lint` or reads a byte it prints.
This item ends that: `tests/test_lint_vault_fix_rules.py` will drive `run_lint(..., do_fix=True)` —
the MUTATING entry point — and `apply_fixes` directly, on every floor run, forever, and Task 15 joins
it to `WORK_ITEM_DOCS` so it also re-executes under five `-S` foreign-interpreter subprocesses per
floor. The blast radius if that module is ever handed a path that is not a fresh temp directory is
Dave's 3,952-note vault, and the path is one attribute access away: `lint_vault.DEFAULT_VAULT` is
`os.environ.get("OBSIDIAN_VAULT_PATH", "")` at `scripts/lint_vault.py:56`, sitting on the very module
the check module loads, and the baseline artifact records that `$VAULT` is "exported in the shell"
(`docs/lint-vault-live-baseline.md:10-11`) — so on Dave's own machine that variable is populated. The
standing wall does not cover this: `FORBIDDEN_DEFAULT_PATTERNS` catches `expanduser`, `Path.home()`
and `/Users/`, but its universe is `("obsidian_schemas", "scripts")` at
`tests/test_vault_path_required.py:320`, which does not reach `tests/`, and none of its three patterns
matches an environment read in any case. Task 15 runs that predicate over this item's touched files,
which closes the literal-path half for the new module but not the environment half. The Design's
intent is unambiguous (§7: "Subjects are PLANTED on top of a materialized corpus copy"; §10.5: "Every
check is hermetic over a temp directory"), and every task that drives a fix names a materialized copy
— so this is a missing GUARD on a correct design, not a wrong design. Carried as **M3**, landed in
Task 9 because the skeleton is where every later check inherits it.

### Mitigations required

1. **M1 — the read-error value is a vocabulary member, never the decode exception.** Already in
   Design §1 and ordered by Task 2; already asserted by AC-3(a) ("read from the imported constant
   rather than re-spelled"). Declared so the fold is enforceable rather than remembered.
2. **M2 — both new records carry bounded values.** Already in Design §3 and ordered by Task 4;
   already asserted by AC-4(c). Declared for the same reason. One pointer for the builder, not a
   requirement: the package already single-homes this decision in
   `obsidian_schemas/errors.py:bounded_cause:239-245`, whose fallback arm returns exactly
   `type(cause).__name__`. The Design's hand-rolled form is strictly NARROWER (it drops the
   `at line N, column M` suffix `bounded_cause` adds for a `MarkedYAMLError`), so it is safe and the
   choice stands; it is worth knowing the primitive exists before writing a third spelling of the
   rule.
3. **M3 — the new check module's mutating drives are confined to a temp directory, asserted.** NOT
   currently pinned by any criterion or wall; this is the one mitigation that needs new text.
4. **M4 — an issue whose write committed is never re-labelled `errored`.** Reconciles Design §4 with
   the signed AC-4(b).

```mitigation
kind: required
id: M1
desc: read_vault's recorded read_error value is the IMPORTED SKIP_REASONS member UNREADABLE and never str(exc) of the decode failure, so undecodable note bytes are never decoded, never rendered into an issue message and never stored in any record.
landed: Task 2
```

```mitigation
kind: required
id: M2
desc: FixErrorRecord.reason is the exception's class name and FixDeclineRecord.guard is a DECLINE_GUARDS member — never str(exc), never note bytes — because both records feed the operator-facing summary that gets pasted into chat.
landed: Task 4
```

```mitigation
kind: required
id: M3
desc: every apply_fixes and run_lint(..., do_fix=True) drive in tests/test_lint_vault_fix_rules.py takes a vault path rooted in a fresh tests/support.temp_dir(), never lint_vault.DEFAULT_VAULT, never OBSIDIAN_VAULT_PATH and never any path outside that directory, and the module asserts that containment before the first mutating call.
landed: Task 9
```

```mitigation
kind: required
id: M4
desc: an issue whose own write has COMMITTED is credited at that commit point and is never re-labelled errored by a later raise inside the same lock block, so the issues carried by the write at :957 stay repaired when the wikilink write at :975 raises, as AC-4(b) requires.
landed: Task 4
```

### Notes (non-blocking)

1. **The exit attestation's redaction obligation is stated everywhere except the bytes the conductor
   re-runs from.** `docs/lint-vault-live-baseline.md` §4 lists three commands "to re-run verbatim"
   (`:133-137`), and command 1 records the `-q` summary verbatim — whose header line is
   `Vault Lint Report — {vault_path}`, i.e. the absolute path to Dave's vault, which the entry run
   hand-substituted to `$VAULT` and said so (`:6-8`). The obligation is genuinely stated twice in
   committed bytes the conductor reads — the artifact's own file-scoped header, and
   `## Verification`'s incident-replay paragraph ("redacted to counts... no absolute vault path") —
   and command 2 correctly records only the byte count and digest of the report rather than the
   report. So this is one missing reminder line in §4, not a hole, and it is deliberately NOT a
   required mitigation: §4 is conductor-owned and outside the builder's write authority
   (`## Scope Boundary`), so it has no Implementation-Plan task to land in and a fence pointing at
   one would be a fiction. Raised so the conductor sees it at the ship door.
2. **`apply_fixes:994` prints `str(exc)` to stderr and this item does not change that.** The
   rendering is pinned by `tests/test_lint_vault_fix_gate.py:123-125` as an equality over the
   exception's message, and the handler set does not widen, so no new content reaches that channel.
   It is the operator's own terminal rather than a record, and the bounded record beside it is what
   M2 covers. Noted only so a future reader does not mistake the bounded record for a claim about
   the print.
3. **Constraint 7's open question resolved itself in the safe direction.** The constraint asked
   whether WI-016's privacy wall reaches a NEW test module's source; Design §7 mandates
   pool-certified plant tokens regardless, so the privacy outcome is the same either way and only
   the floor-colour question remains, which is the spec-reviewer's.

```verdict
gate: threat-modeler
verdict: PROMOTE
date: 2026-09-15
model: claude-opus-5
note: Tampering and elevation both re-derived off the code rather than the prose — the widened stem index can only REMOVE emissions (`check_links:513/515` continue on a hit) and `meeting_date_index` is populated only under `entity_type == "meeting"` (`:191-196`), so Design §1's `entity_type=""` keeps an undecodable note out of every write-target and move-target index rather than merely quiet; the one genuinely new hazard is that this item ships the first floor-resident test that drives the MUTATING `run_lint(..., do_fix=True)`, with `lint_vault.DEFAULT_VAULT = os.environ.get("OBSIDIAN_VAULT_PATH", "")` (`:56`) one attribute access away on the module it loads and `FORBIDDEN_DEFAULT_PATTERNS`' universe stopping at `("obsidian_schemas", "scripts")` (`test_vault_path_required.py:320`), so M3 requires the temp-dir containment the Design intends but nothing asserts; M1/M2 declare the bounded-value rules already in Design §1/§3 (correctly applying `errors.py:255-261`, which names `UnicodeDecodeError` as the suppressed cause) so the fold is enforceable, and M4 reconciles Design §4's end-of-lock-block fold with the signed AC-4(b), which requires the `:957`-committed issue to stay `repaired` when the `:975` write raises — a committed write reported as failed is this item's own defect one frame in, and the fold rule is the right channel for it rather than a REVISE.
```


## Spec Review — 2026-09-15

**Recommendation: REVISE — return to spec writer (gaps to fix)**

First spec-review round on this item, cold-start: there is no prior `Spec Review` section on this
document and none in `docs/lint-vault-fix-safety-rounds.md` (grepped both), so nothing is carried
forward from a spec-review round and the bar was walked from line 1 rather than against the diff.

Rulings on record: A3/A3b's YAML-formatting and body-only-write deferrals, the `FixOutcome.fixed` → `repaired` field-name ruling, AC-5's §4-lifetime rule (presence never emptiness), and the exit-run-as-ship-condition ruling are all settled in this document and were routed against rather than re-litigated.

The verdict turns on ONE thing and it is mechanical before it is substantive: the threat-model round
of 2026-09-15 declared four `kind: required` mitigations and no fold work has happened since. The
conveyor's D8c rule refuses `specced -> ready` on exactly that, so a PROMOTE here would buy a refused
transition; and two of the four are not merely unrecorded but unlanded — their substance appears on
zero surfaces of the spec, and one of them contradicts a criterion Dave has already signed.

### Citation verification

Every symbol-anchored citation the spec leans on was re-resolved against this tree by reading the
code at each site, not by taking the injected drift audit as a pass. All of them resolve AND mean
what the spec claims:

- `scripts/lint_vault.py` — `VaultFile:88-97` with `parse_error` last and `raw_content` written at
  `:151` only; `read_vault:110-155` with the swallow at `:115-118`; `build_indexes:179-197` keying
  `all_stems` / `stem_to_file` off `vf.stem` with no type guard and `meeting_date_index` populated
  only under `elif vf.entity_type == "meeting"` at `:191-196`; `check_structural:293-305` with
  `no_frontmatter` at `:308`; `classify_person_tier:233-283` with SIX `- ` docstring bullets at
  `:237-242` and FOUR `return "active"` sites at `:253`, `:276`, `:279`, `:282`;
  `FixOutcome:820-824` as `(fixed, refused)`; the five repair branches at `:888`, `:896`, `:903`,
  `:911`, `:929`; the six decline sites at `:890`, `:906`, `:913`, `:935-936`, `:963-973` plus the
  `idx: Optional[dict] = None` default at `:828`; `gate_write` at `:947` landing BEFORE
  `fixed += file_fixed` at `:949`; the first write at `:957`, the second at `:960-975` with its own
  `fixed += 1` at `:972`; the uncounted `except Exception` print at `:993-994`; the return at `:996`;
  `CATEGORY_ORDER` at `:1003`; `read_vault` bound at `run_lint:1160` and the summary print inside
  `if fixable:` at `:1191-1199` with the `"No auto-fixable issues found."` else-arm at `:1213-1214`.
- `tests/derivations.py` — `SCRIPTS_ROOT:33`, `python_files_under:185`,
  `skip_reason_return_values:1528`, `skip_reason_literal_sites:1585`. Design §1/§6/§8 carry the
  current ordinals; AC-3's `:1583-1606` and `:31` are the ~2-line staleness the spec itself records
  and deliberately declines to edit to preserve `ac_hash_AC-3`. Every symbol resolves, so this is a
  re-anchoring nit and not drift.
- `tests/test_fixture_vault.py` — both universe sites still unwidened
  (`python_files_under(PACKAGE_ROOT, TESTS_ROOT)` at `:508-509` and `:1302`), both declared-homes
  sets still exactly two members at `:510-514` and `:1315-1318`, and the `ast` single-home wall at
  `:1309-1312` really does share the `:1302` local. AC-3(a)'s universe-widens / expected-sets-hold
  shape is the one edit true of the mechanism.
- `tests/test_ac_interpreter.py:47-50` — `WORK_ITEM_DOCS` carries exactly the two docs the spec
  says, and `test_every_acceptance_criterion_passes_under_the_conveyors_interpreter` is at `:108`.
- Every existing `test_` name in a `verify:` declaration resolves:
  `test_lint_vault_fix_guards_threads_and_records_refusals` (`test_lint_vault_fix_gate.py:83`),
  `test_the_fix_outcome_surfaces_both_counts` (`:276`),
  `test_every_tier1_pattern_is_refused_at_every_door` (`test_name_gate_refusals.py:127`),
  `test_identifiers_normalize_identically_on_every_door` (`test_name_gate_identifiers.py:110`),
  `test_a_legacy_dirty_name_stays_writable_for_unrelated_writes`
  (`test_name_gate_delta_rule.py:81`), `test_skip_reason_declaration_binds_to_its_functions_returns`
  (`test_fixture_vault.py:411`),
  `test_the_fixture_vault_files_close_their_wall_memberships_by_running_each_predicate` (`:1287`).
- Constraint 7's plant collision — `tests/fixtures/vault/@Dave  Marrowyn Fennwick.md` exists and
  `@Tarnquil  Brenvik.md` does not (the corpus carries `@Wexlund Tarnquil.md`,
  `@Pellworth Brenvik.md` and `@Oskaline Brenvik-Tarnquil.md`, never that combination), so AC-1(c)'s
  substituted stem is collision-free and pool-drawn.

One citation is off by an ordinal and it is in a gate note rather than in the spec proper — see
non-blocking note 4.

### Blocking issues

1. **Four `kind: required` mitigations, and the document has no `## Mitigation Folds` section at
   all.** The latest speaking threat-model round (`2026-09-15`, `:2597`) declares M1 (`:2736-2741`,
   `landed: Task 2`), M2 (`:2743-2748`, `landed: Task 4`), M3 (`:2750-2755`, `landed: Task 9`) and
   M4 (`:2757-2762`, `landed: Task 4`). Grepped this document and the rounds archive: there is no
   `Mitigation Folds` heading and no `fold` fence anywhere. D8c refuses `specced -> ready` while any
   `kind: required` mitigation of the latest speaking round lacks a complete, fresh record, and the
   record's home is decided by code — a fence written under any other heading is not a record. The
   fix is a `Mitigation Folds` section carrying four five-key records (`id`, `desc` copied verbatim
   from the fences above, `design`, `landed`, `work`), each quoted value one line. Two of the four
   can be written today because their substance is already in the spec — M1's rule is Design §1's
   "`read_error=UNREADABLE`, where `UNREADABLE` is IMPORTED" plus Task 2's "The string
   `"unreadable"` must NOT appear anywhere in the file", and M2's is Design §3's
   `FixErrorRecord.reason` / `FixDeclineRecord.guard` field comments plus Task 4's record clause. The
   other two cannot, which is items 2 and 3.

2. **M4's ruling is on ZERO surfaces, and the four surfaces that DO state the behaviour all state
   the pre-ruling one — which contradicts the signed AC-4(b).** AC-4(b) (`:2041`, frozen at
   `ac_hash_AC-4: 5cc1a0cc3737`, `## AC Sign-off` `:2373-2392`) names one file carrying a
   `missing_body_sections` issue "(repaired, committed at `:957`)" beside a `broken_wikilink` issue
   "whose write raises", and requires the first `repaired` and the second `errored`. Design §4
   (`:1123-1127`) rules the opposite: "The `fixed += file_fixed` fold at `:949` is REPLACED by
   `repaired += len(undecided)` at the END of the `with vault_io.note_lock(fpath):` block, after the
   wikilink pass." I read the frame rather than the prose — a raise at `:975` propagates out of the
   `with` block to the `except Exception` handler at `:993`, so under §4's placement the fold never
   runs, BOTH issues are still in `undecided`, and both become `errored`: a write that committed to
   one of Dave's notes reported as one that failed. Three more surfaces carry the same pre-ruling
   sentence: Task 4 (`:1528`, "the fold moved to the end of the lock block"), the `## Edge Cases`
   entry at `:1403-1407` ("the gate passes and `vault_io.write_note` then raises … every
   still-undecided issue becomes `errored`", true of the FIRST write and silent on the second), and
   `## Risk Analysis` R1 (`:1962-1963`, "moves the `repaired` fold from `:949` to the end of the lock
   block"). The threat modeler was right to route this to the fold rather than to a REVISE of its
   own — but the fold has not happened, so the document is buildable two ways and the builder reading
   Design §4 and Task 4 produces a build RED against a criterion Dave signed. The ruling to write
   into all four surfaces is M4's own: **an issue is credited at the point its own write commits** —
   first-write issues leave `undecided` immediately after `write_note` returns at `:957`, wikilink
   issues after `:975` returns — which preserves §4's genuine correction (today `fixed` is credited
   at `:949` before `:957` can raise) and makes AC-4(b)'s plant come out as signed. Do not weaken
   AC-4(b) to match Design §4; the criterion is frozen and is the correct behaviour.

3. **M3's substance is on zero surfaces too, and the threat modeler said so in writing.** M3
   (`:2750-2755`) requires that every `apply_fixes` and `run_lint(..., do_fix=True)` drive in
   `tests/test_lint_vault_fix_rules.py` take a vault path rooted in a fresh
   `tests/support.temp_dir()`, never `lint_vault.DEFAULT_VAULT`, never `OBSIDIAN_VAULT_PATH`, "and
   the module asserts that containment before the first mutating call". The mitigations list names it
   as "the one mitigation that needs new text" (`:2731-2732`). Task 9 (`:1576-1584`) orders the
   `ensure_project_interpreter` first statement, the `SCRIPTS_ROOT` loader, a `materialize_vault(tmp)`
   helper and a `_plant` that refuses corpus stems — no containment assertion — and its `verify:`
   names `test_wall_membership_is_closed_for_every_file_this_item_touches`, which is about wall
   memberships and would not go red if the containment assertion were absent. Design §7 (`:1237-1244`)
   states the intent ("Subjects are PLANTED on top of a materialized corpus copy") but states no
   assertion, so a fold record's `design:` quote has nothing faithful to point at. The hazard is real
   and I checked it: `DEFAULT_VAULT = os.environ.get("OBSIDIAN_VAULT_PATH", "")` sits at
   `scripts/lint_vault.py:56` on the very module the check module loads by path, and
   `FORBIDDEN_DEFAULT_PATTERNS`' universe stops at `("obsidian_schemas", "scripts")`
   (`tests/test_vault_path_required.py:320`) so no standing wall reaches `tests/`. This item ships the
   first floor-resident test that drives the MUTATING entry point, forever, plus five `-S`
   re-execs — so the containment needs a Design §7 sentence and a Task 9 work clause with a `verify:`
   that actually covers it, before the fold record can quote either.

### Non-blocking notes

1. **Design §4 does not say what becomes of `:972`'s `fixed += 1` or of `file_fixed`.** §4 keeps
   "A branch that acts … increments `file_fixed` exactly as today" and replaces only the `:949`
   fold, while `repaired += len(undecided)` already counts a repaired wikilink issue through
   `undecided`. Leaving `:972`'s increment in place double-counts; leaving `file_fixed` incremented
   but never folded leaves a dead local. AC-4(a)'s equality would catch the double-count at build
   time, so this is not blocking — but blocking issue 2 forces a §4 rewrite anyway, and that rewrite
   should settle both in the same edit rather than leaving the builder a coin-flip.

2. **Task 9's `verify:` forward-references a check Task 15 creates.** Well-formed under D10a and
   resolvable by the time D10b runs at `building -> done`, so it refuses nothing — but Task 9's own
   work (the skeleton, the loader, the `_plant` refusal) has no check that covers it, and the
   containment assertion of blocking issue 3 would naturally be that check.

3. **The "Signature impact" paragraph is now stale prose.** `:800-803` reads "The 2026-09-15
   `ac-signoff` fence carries `ac_hash: 03777fa0e132`" and lists `ac_hash_AC-2` `1e40f7ae8765` and
   `ac_hash_AC-5` `7036c93e9f21` as invalidated. `## AC Sign-off` (`:2373-2392`) now carries
   `ac_hash: 973d7a08f068` with AC-2 `bdb83849dd61` and AC-5 `01784d0e28c1` — i.e. the re-signature
   landed and the paragraph describes the pre-re-sign state. AC-1/AC-3/AC-4's hashes match the
   paragraph's "stays valid" list exactly, and `intent_hash: 6a7cccabd378` is unmoved, so there is no
   drift to classify; only the narration is out of date. One dated sentence fixes it.

4. **One stale ordinal, in the threat model's non-blocking note 2 rather than in the spec.** It
   cites `obsidian_schemas/errors.py:bounded_cause:239-245`; `bounded_cause` is at `:199-236` and
   `:239-245` is `bounded_detail`. The symbol resolves and the note's substance is true of it (the
   fallback arm is `return name` at `:236`, and `chainable_cause`'s docstring at `:258` does name
   `UnicodeDecodeError` as suppressed), so this is a re-anchoring nit — worth carrying only because
   M2's fold record may reuse the ordinal.

5. **Constraint 7's open question, routed to this gate by threat-model note 3, is answered: the
   WI-016 privacy wall does NOT reach a new test module's source.** Its scanned universe is the
   corpus's own note TEXTS (`tests/test_fixture_vault.py:1037-1055`, `scanned_text` built from
   `texts`) and the census bytes, never `python_files_under(...)`. So pool-certified plant tokens
   stay prudent-and-mandated-by-Design rather than wall-enforced, and a plant stem literal in
   `tests/test_lint_vault_fix_rules.py` cannot redden that wall. Recorded so it is not re-derived.

### What is NOT a gap — checked and clean

Stated because the next round should not re-walk them. `## Write Targets` coverage is exact in both
directions: each of the sixteen tasks' target files appears in the nine builder `writes` fences, and
no fence names a path no task writes (`docs/vault-shape-census.md` and
`docs/lint-vault-live-baseline.md` correctly sit in `kind: precondition` fences and in no builder
fence, since AC-5 reads them; the driven doc is implicit; Tasks 1 and 16 write only the Build Log).
Every path is inside `pipeline-runners.yaml:34-38`'s grant, so the L3 review level the frontmatter
carries is not under-declared. Sixteen canonical `- [ ] **Task N — …**` definitions, ordinals 1–16
unique, and every `landed: Task N` in the threat model (2, 4, 9, 4) resolves to one of them — no D8b
refusal here. All sixteen carry a well-formed `verify:` declaration: twelve name bare `test_` names,
Task 1 declares `baseline` with its reason (an informational number whose only artifact is the Build
Log) and Task 16 declares `hand-run` with its reason (a whole-suite command no single check can
assert) — both correct uses of the closed exception kinds, and no verify command writes outside
`write_authority`. `OPEN: None`, zero open items. `## Verified Diagnosis` carries four load-bearing
claims and I re-executed the artifact behind each: VD-1's discarded filename, VD-2's six guards
returning `FixOutcome(fixed=0, refused=())` indistinguishably from an empty input, VD-3's untallied
`except Exception` print at `:993-994` against `:1198`'s two-field line, and VD-4's
`test_the_fix_outcome_surfaces_both_counts` asserting only `_fields`. The WI-235 counting-wall
prescription is discharged in `## Verification` — each of the three count-shaped oracles and the four
artifact readers is driven through the wall's own predicate with a named near-miss it must NOT match
— and the WI-278 corpus-fixture arm is chosen explicitly in AC-5(b)'s one-line coupling declaration
(frozen bytes of two conductor-owned artifacts, one digest-frozen, no live population's shape). The
WI-229 conscious-pin sweep is done and is the reason the rename inventory is nine sites across four
modules; I re-grepped it and it holds. AC-5's §4-lifetime rule (equality over §§0-3, presence over
§4, SHA count scoped to the header region) is the right call and is the clause that lets this floor
member survive its own close-out.

### Carried-forward notes

Every still-open non-blocking note from every prior round, by name:

- **Architect round 4, note 1 (the summary print sits inside `if fixable:`)** — CLOSED. Design §5
  ruling 1 (`:1179-1183`) prints unconditionally under `do_fix` and drops the else-arm; Task 6 and
  Task 13's non-AC sibling order and cover it.
- **Architect round 4, note 2 (the second Example of done described a run the CLI cannot produce)** —
  CLOSED. `:2066-2073` now leads with the reachable link-text-absent decline and keeps the `idx=None`
  clause as a statement about `apply_fixes`' own default.
- **Architect round 4, note 3 (AC-5(b)'s parenthetical-separation rule)** — CLOSED. The
  strip-IFF-a-`CATEGORY_ORDER`-member rule is in AC-5(b) and in Design §9; `CATEGORY_ORDER` is at
  `scripts/lint_vault.py:1003` as cited.
- **Architect round 4, note 4 / AC red-team round 3's label slip ("A SIXTH CENSUS READER")** —
  CLOSED. AC-5(b) now reads "A FIFTH CENSUS READER" with the four existing readers named.
- **Threat model, note 1 (the exit attestation's redaction reminder is missing from
  `docs/lint-vault-live-baseline.md` §4's own bytes)** — STILL OPEN and correctly not a mitigation:
  §4 is conductor-owned and outside the builder's write authority, so it has no plan task to land in.
  Re-deferred here for the same reason, and it is the conductor's to action at the ship door.
- **Threat model, note 2 (`apply_fixes:994` prints `str(exc)` to stderr and this item does not change
  that)** — STILL OPEN as a deliberate non-change; the rendering is pinned by
  `tests/test_lint_vault_fix_gate.py:123-125` and the handler set does not widen, so nothing new
  reaches that channel. Re-deferred: closing it would move a pinned equality for no gain in this item.
- **Threat model, note 3 (constraint 7's open question about the privacy wall's reach)** — CLOSED by
  this round; see non-blocking note 5 above.
- **Data audit round 2's two carried items** — both STILL OPEN and both correctly outside the spec:
  the build-start re-grounding should re-run AC-5(b)'s five-row comparison before the first edit
  (the baseline is dated 2026-09-10 and the vault churns weekly), and the exit half of A7's bracket
  has no battery wall by construction and lives at the conductor's ship door.

```verdict
gate: spec-reviewer
verdict: REVISE
date: 2026-09-15
model: claude-opus-5
targets: M1, M2, M3, M4, Task 4, Task 9, #design
prior: none
basis: folded-material
findings: 3/7
note: The threat-model round declared four `kind: required` mitigations and no fold work followed — there is no `## Mitigation Folds` section and no `fold` fence in this document or its archive, so D8c refuses `specced -> ready` outright; worse, two of the four are unlanded rather than merely unrecorded — M3's temp-dir containment is on zero surfaces (Task 9 orders the skeleton and no assertion, and no standing wall reaches `tests/` since `FORBIDDEN_DEFAULT_PATTERNS`' universe stops at `("obsidian_schemas", "scripts")` while `DEFAULT_VAULT = os.environ.get("OBSIDIAN_VAULT_PATH", "")` sits at `scripts/lint_vault.py:56` on the module the new check loads), and M4's ruling is contradicted by all four surfaces that state the behaviour (Design §4's end-of-lock-block fold, Task 4, the write-raises edge case and R1), which I confirmed by reading the frame rather than the prose: a raise at `:975` leaves the `with` block before `repaired += len(undecided)` runs, so the issue whose write COMMITTED at `:957` is reported `errored` — the exact opposite of the signed AC-4(b) (`ac_hash_AC-4: 5cc1a0cc3737`), leaving the spec buildable two ways with one way RED against Dave's signature. Everything else is clean and re-verified rather than assumed: all eleven symbol-anchored citations resolve AND mean what the spec claims, Write-Targets coverage is exact in both directions, sixteen canonical tasks each carry a well-formed `verify:` with both exception kinds used correctly, every `landed: Task N` resolves, and the four prior-round label/parse/exemplar notes are closed.
```


## Adversarial Review — 2026-09-15

Read the document end-to-end, all 3027 lines: frontmatter, Problem/Intent, both currency audits, every Exploration-Notes approach (A1–A7b) and all eight constraints, all five Revision rounds, Approach, Verified Diagnosis, the full Design (§1–§10), Edge Cases, all sixteen Implementation-Plan tasks, both `writes` precondition fences and the nine builder `writes` fences plus the handoff note, Verification, Scope Boundary, Risk Analysis, all five `criteria` fences and their Examples of done, and every prior gate round in full — AC Red-Team round 3, Architectural Review round 4, AC Sign-off, Data Audit round 2, Threat Model, and Spec Review — including each one's own `verdict`/`mitigation` fence. Also read the injection-hunter role definition and its machine contract before starting.

**The one question:** nothing in this document's body or in any prior gate's verdict prose reads as an instruction addressed to a reviewer rather than a description of the work. There is no text of the shape "emit PROMOTE", "this was pre-approved", "ignore the previous instruction/finding", or any sentence whose grammatical subject is the reviewing agent rather than the code or the spec. The document's extremely dense, self-citing, adversarial-sounding prose ("REJECTED", "RULED", "CLOSED", "FORBIDDEN", "MUST NOT") is the project's own house style for recording design rulings against re-derived code citations — every such ruling is paired with a file:line citation a reader can re-execute, which is the opposite shape from steering text (steering text argues from authority or urgency, not from a re-checkable fact).

I gave the most recent, most junction-critical section — `## Spec Review` — the closest read, per the role's specific call-out to scrutinize the prior gate's note. It is a REVISE, not a PROMOTE, and its reasoning is the strongest evidence against manipulation in the whole chain: the spec-reviewer independently re-read the frame at `scripts/lint_vault.py:949-975` rather than trusting Design §4's or the threat-modeler's prose, found that a `:975` raise leaves the fold at `:1123-1127` never executed, and traced that this contradicts the AC-4(b) criterion Dave already signed (`ac_hash_AC-4: 5cc1a0cc3737`) — a finding that argues against the document's own prior work rather than for it. A planted "approve this" line would look nothing like this; a REVISE that quotes signed hashes and re-derives byte offsets to contradict an earlier round is the review chain functioning adversarially as designed, not a target of adversarial content.

I also checked the two mechanically likeliest injection vectors named in the machine contract itself: (1) a stray example `## Adversarial Review` heading planted earlier in the document that could have captured a fabricated verdict fence as mine — none exists; the h2 heading list contains no such line anywhere before this edit. (2) any verbatim reproduction of a "known planted-hostile specimen" (WI-091-style exam canary) — this document names no such specimen and carries no exam-corpus markers; the planted test fixtures it describes (`@Tarnquil  Brenvik.md`, the double-space stem, the four-topic meeting, the inner-trailing-space wikilink) are ordinary test-discriminator plants for lint-rule oracles, not injected instructions, and none of them is prose addressed to a reviewer.

No manipulation found. This is a real finding, not a skipped check.

```verdict
gate: injection-hunter
verdict: PROMOTE
date: 2026-09-15
model: claude-sonnet-5
note: Read the full document and every prior gate round end-to-end; found no text instructing a reviewer's verdict, no steering framed as spec content, and no planted-specimen leakage — the spec-reviewer's own REVISE (contradicting the document's signed AC-4(b) via a re-derived code trace) is itself evidence the review chain is functioning adversarially rather than being steered.
```


## Threat Model — 2026-09-15 (round 2)

**Recommendation: PROMOTE to threat-modeled**

Second round. The carry-forward is this document's own round-1 section plus what happened to it: round 1
PROMOTEd with four `kind: required` mitigations; the spec-reviewer then REVISEd because no fold work had
followed and because two of the four (M3, M4) were unlanded rather than merely unrecorded; the
spec-writer's `## Mitigation Folds — 2026-09-15` landed all four. So this round has exactly one job that
round 1 could not do — read the FOLDED material as a new attack surface — and it re-derived every
citation off this tree (worktree `cage-wt-_e7mavhf`) rather than trusting the fold's own prose about
itself.

### Trigger check

The same four triggers fire, unchanged and for the same reasons: filesystem operations on user-owned
files (`apply_fixes:957`, `:975`, `quarantine_garbage:1140`), untrusted input (vault bytes, with the new
crossing at `read_vault:115-118`), persistence (the committed live-vault measurement, and a
floor-resident module driving the MUTATING entry point), and an information-disclosure surface (the
operator-facing summary, against `obsidian_schemas/errors.py`'s bounded-projection contract). The fold
did not retire any of them and it ADDED surface to the fourth and to elevation-of-privilege, which is
where this round spent its time.

### The four folds, re-read against the code rather than against the fold record

- **M1 — landed and faithful.** Design §1 now carries the rule as a rule ("`read_vault`'s recorded
  `read_error` value is the IMPORTED `SKIP_REASONS` member `UNREADABLE` and never `str(exc)`…") and Task
  2 carries the enforceable half ("The string `"unreadable"` must NOT appear anywhere in the file"). The
  `desc` is re-emitted byte-identically below.
- **M2 — landed and faithful.** Design §3's bound paragraph and Task 4's record clause both state
  `type(exc).__name__` / a `DECLINE_GUARDS` member. Re-emitted byte-identically.
- **M4 — landed, faithful, and STRONGER than the fence asked for.** I re-read the frame rather than the
  fold: `fixed += file_fixed` at `:949` really does sit above the `if changed:` write at `:957`, and the
  wikilink write at `:975` sits outside that block so its raise propagates past any end-of-block fold to
  the handler at `:977`/`:993`. Design §4's two credit points — `repaired += len(staged_first)` on the
  statement after `:957` returns, `repaired += len(staged_wikilink)` after `:975` returns — produce
  AC-4(b)'s signed answer, and §4 DELETES the `:949` fold outright rather than relocating it, which is
  the distinction the fence's text turns on. It also deletes `file_fixed` (`:882`) and the `fixed += 1`
  at `:972`, closing the spec-reviewer's non-blocking note 1 in the same edit instead of leaving a
  double-count for AC-4(a) to discover. Re-emitted byte-identically.
- **M3 — landed, and its substance is right, but the fold's SYNTAX half claims more than its mechanism
  delivers.** That is this round's one finding and it is below.

### STRIDE review — scoped to what the fold ADDED

**Spoofing — nothing new.** No authentication boundary moved. `person_missing_name` still writes
`fpath.stem.lstrip("@")` (`:897`) through the unchanged `gate_write` at `:947`.

**Tampering — the fold is bookkeeping and I confirmed it changes no write.** Reading `:887-975` against
Design §4: no branch's repair logic, no `delta` key, no gate call and no `write_note` argument moves; the
three deletions remove counters only. The two staging lists cannot credit a write that did not run —
`staged_first` is appended only by branches that also set `changed = True` (the `if changed:` guard at
`:951`), and `staged_wikilink` only by a replacement that fired and set `wl_changed` (`:969-972`), which
is the same guard `:974` reads. §6(d) and §7 add read-only AST scanning and a temp-directory door;
neither writes. WI-004's concurrency contract is untouched.

**Repudiation — closed harder than round 1 found it.** VD-3's hole is closed by the four-bucket
partition, and M4's fold removes BOTH pre-write counters rather than relocating one, so there is no
remaining site that credits a repair before its bytes are on disk.

**Information disclosure — the fold widened one record and the widening is safe.** `FixDeclineRecord`
gained a third field, `check`, which carries the issue's own `LintIssue.check` id — a source literal from
the script's closed 23-member check vocabulary (enumerated in `## Edge Cases`), so the projection does
not widen toward note content; `guard` is likewise a `DECLINE_GUARDS` source literal. Design §3's new
disjointness assertion (no `DECLINE_GUARDS` member may equal a `SKIP_REASONS` member) is the right
belt: it keeps the §8 vocabulary wall unambiguous as guard ids accumulate. The new check module becomes
an `os.environ` reader and a `Path.resolve` caller through M3's door, and Task 15 already routes it
through `os_module_attribute_uses` / `module_import_uses` / `filesystem_mutation_uses` rather than
assuming it clean — correct, and the door compares resolved paths it holds in-process and prints none of
them, so the guard itself discloses nothing.

**Denial of service — unchanged and bounded.** `declined` adds at most one small record per auto-fixable
issue (1,169 today; the `idx=None` case is the worst at 315), each a `Path` plus two short strings. No
network, no retry, no recursion.

**Elevation of privilege — the finding, and it is round 1's finding one level in.** Round 1 refused to
accept Design §7's "Subjects are PLANTED on top of a materialized corpus copy" as a guard, because it was
INTENT and nothing asserted it; M3 was that refusal. The fold's syntax half now says, in the same shape,
that `vault` is "the local every check binds from `_temp_vault(...)` and from nothing else" — and asserts
the first half of that sentence, never the second. What `mutating_drive_vault_args` returns (§6(d)) is the
IDENTIFIER bound to each drive's vault argument, and
`test_every_mutating_drive_in_this_module_is_confined_to_a_temp_vault` asserts that identifier is `vault`.
That is a claim about the argument's SPELLING, not about its provenance, so Design §7's "the syntax half
is what proves every drive went through it" is not true of the mechanism as specified.

The residue is exactly one shape, and the fold's own next-level sweep is what bounds it: the three
hazardous spellings it enumerates all RAISE in the scan (`lint_vault.DEFAULT_VAULT` is an
`ast.Attribute`, `os.environ["OBSIDIAN_VAULT_PATH"]` a `Subscript`, a literal a `Constant`), and any
OTHER bound name is RED naming the line. What survives is re-binding the accepted name itself —
`vault = lint_vault.DEFAULT_VAULT` followed by `run_lint(vault, do_fix=True)`. Both halves pass: the
syntax half sees the identifier `vault`, and the runtime half never executes because `_temp_vault` was
never called. The blast radius is unchanged from round 1 and is the largest in this item —
`DEFAULT_VAULT = os.environ.get("OBSIDIAN_VAULT_PATH", "")` at `scripts/lint_vault.py:56` on the very
module the check loads, that variable populated on Dave's machine
(`docs/lint-vault-live-baseline.md:10-11`), 3,952 live notes, on every floor run forever plus five `-S`
re-execs.

The closure is one clause in a check the plan already ships, over a module the scan already parses: every
`Assign` in this module whose target is the name `vault` has a `Call` to `_temp_vault` as its value. So
this is carried as a TIGHTENING of M3's `desc` rather than as a REVISE — the requirement moved, the fence
is the channel WI-128/D8 provides for a requirement needing one more sentence in a task, and the guard's
substance is already on the page.

### Mitigations required

1. **M1 — the read-error value is a vocabulary member, never the decode exception.** Folded into Design
   §1 and Task 2, verified this round. Re-emitted unchanged.
2. **M2 — both new records carry bounded values.** Folded into Design §3 and Task 4, verified this round.
   Re-emitted unchanged.
3. **M3 — the new check module's mutating drives are confined to a temp directory, asserted — and the
   syntax wall now has to prove PROVENANCE and not only spelling.** `desc` CHANGED this round; this is
   the only fence whose requirement moved, and it is the only one needing new fold work.
4. **M4 — an issue whose write committed is never re-labelled `errored`.** Folded into Design §4, the two
   paired Edge Cases, Task 4, R1 and a `## Verification` mutation; verified against the frame this round.
   Re-emitted unchanged.

```mitigation
kind: required
id: M1
desc: read_vault's recorded read_error value is the IMPORTED SKIP_REASONS member UNREADABLE and never str(exc) of the decode failure, so undecodable note bytes are never decoded, never rendered into an issue message and never stored in any record.
landed: Task 2
```

```mitigation
kind: required
id: M2
desc: FixErrorRecord.reason is the exception's class name and FixDeclineRecord.guard is a DECLINE_GUARDS member — never str(exc), never note bytes — because both records feed the operator-facing summary that gets pasted into chat.
landed: Task 4
```

```mitigation
kind: required
id: M3
desc: every apply_fixes and run_lint(..., do_fix=True) drive in tests/test_lint_vault_fix_rules.py takes a vault path rooted in a fresh tests/support.temp_dir(), never lint_vault.DEFAULT_VAULT, never OBSIDIAN_VAULT_PATH and never any path outside that directory, and the module asserts that containment before the first mutating call; and the syntax half asserts PROVENANCE and not merely spelling — every binding in that module of the identifier it accepts is a call to the single _temp_vault door — so a drive cannot satisfy the wall by re-binding that name to a path the door never produced.
landed: Task 9
```

```mitigation
kind: required
id: M4
desc: an issue whose own write has COMMITTED is credited at that commit point and is never re-labelled errored by a later raise inside the same lock block, so the issues carried by the write at :957 stay repaired when the wikilink write at :975 raises, as AC-4(b) requires.
landed: Task 4
```

### Notes (non-blocking)

1. **M3's wall universe is ONE module, and that is correct — recorded so a later round does not propose
   the obvious widening as a free win.** Three sibling modules already drive `apply_fixes` today
   (`tests/test_lint_vault_fix_gate.py:114,162,196,227,262,280` and
   `tests/test_name_gate_delta_rule.py:200`, plus the two name-gate modules Task 5 renames), and they sit
   outside the scan's universe. They are pre-existing, they bind their vault from `temp_dir()`, and
   widening is NOT free: `test_lint_vault_fix_gate.py:280` passes `Path("/nonexistent")`, a `Constant`,
   which §6(d) is specified to RAISE on. The one-module scope stands.
2. **`_temp_vault`'s third comparison should read `os.environ.get`, not a subscript.** Design §7 and Task
   9 both write `Path(os.environ["OBSIDIAN_VAULT_PATH"]).resolve()` and then guard it in prose with "when
   either is set and non-empty". A bare subscript raises `KeyError` where the variable is unset — the
   graded/CI case — reddening the door rather than a drive. It is also belt-and-braces: a strict
   descendant of a fresh `temp_dir()` cannot be the live vault, so the first assertion already covers it.
   Builder's nit, not a mitigation.
3. **Round 1's note 1 (the exit attestation's redaction reminder is absent from
   `docs/lint-vault-live-baseline.md` §4's own bytes) — STILL OPEN**, re-deferred for the same reason for
   the third time: §4 is conductor-owned and outside the builder's write authority, so it has no
   Implementation-Plan task to land in and a fence pointing at one would be a fiction. The conductor's, at
   the ship door.
4. **Round 1's note 2 stands as a deliberate non-change, and its ORDINAL was wrong — corrected here
   because M2's fold record could reuse it.** `bounded_cause` is `obsidian_schemas/errors.py:199-236`
   (its fallback arm returns the bare class name at `:236`); `:239-254` is `bounded_detail`; and it is
   `chainable_cause:255` whose docstring names `UnicodeDecodeError` as a cause suppressed for rendering
   note content (`:258`). The substance round 1 asserted is unchanged and so is the ruling: the Design's
   hand-rolled form is strictly narrower than `bounded_cause` and the choice stands. `apply_fixes:994`'s
   `str(exc)` print to stderr likewise stays as it is — pinned by
   `tests/test_lint_vault_fix_gate.py:123-125`, handler set unwidened.
5. **Round 1's note 3 is CLOSED** by the spec-reviewer's non-blocking note 5 — the WI-016 privacy wall
   scans the corpus's own note TEXTS (`tests/test_fixture_vault.py:1037-1055`) and the census bytes, never
   `python_files_under(...)`, so a plant-stem literal in the new module cannot redden it. Not re-derived.

```verdict
gate: threat-modeler
verdict: PROMOTE
date: 2026-09-15
model: claude-opus-5
note: All four round-1 mitigations landed and I verified each against the code rather than the fold record — M4's is stronger than the fence asked, deleting `file_fixed` (`:882`), the `:949` fold outright and the `fixed += 1` (`:972`) so nothing credits a repair before its bytes commit, which I confirmed by re-reading `:887-975` (the `:975` write sits outside the `if changed:` block, so its raise propagates past any end-of-block fold to the handler and only per-write crediting yields AC-4(b)'s signed answer); the fold adds no write, no `delta` key and no gate call, and `FixDeclineRecord`'s new third field carries the script's own closed check-id vocabulary rather than note content. The one finding is round 1's own finding one level in: M3's fold asserts that every drive's vault argument is SPELLED `vault` but never that it came out of `_temp_vault`, so Design §7's claim that the syntax half "proves every drive went through it" is untrue of the mechanism — the three hazardous spellings RAISE and any other bound name is RED, leaving exactly `vault = lint_vault.DEFAULT_VAULT; run_lint(vault, do_fix=True)`, which passes the syntax half and never reaches the runtime half, against `DEFAULT_VAULT = os.environ.get("OBSIDIAN_VAULT_PATH", "")` (`scripts/lint_vault.py:56`) populated on Dave's machine and 3,952 live notes on every floor run forever. Closure is one clause over a module the scan already parses, so M3's `desc` is tightened to require provenance and D8 routes the fold — a REVISE would buy nothing the fence does not.
```


## Spec Review — 2026-09-15 (round 2)

**Recommendation: REVISE — return to spec writer (gaps to fix)**

Second spec-review round. The carry-forward is my own round-1 section and what happened to it: I
REVISEd on three blocking findings (no `## Mitigation Folds` section; M4 unlanded and contradicting
the signed AC-4(b); M3 unlanded), the spec-writer's `## Mitigation Folds — 2026-09-15` landed all
four, and the threat modeler's round 2 then re-read the folded material and TIGHTENED M3's `desc`.
Per the reset rule I walked the bar from line 1 rather than against that diff, and re-resolved every
symbol-anchored citation myself rather than taking the injected drift audit as a Check-3 pass.

Rulings on record: A3/A3b's YAML-formatting and body-only-write deferrals, the `FixOutcome.fixed` → `repaired` field-name ruling, AC-5's §4-lifetime rule (presence never emptiness), the exit-run-as-ship-condition ruling, and threat-model round 2's one-module scope for M3's wall are all settled in this document and were routed against rather than re-litigated.

**My three round-1 blockers, re-verified against the document and the code rather than against the
fold's account of itself — all three CLOSED.** (1) `## Mitigation Folds — 2026-09-15` exists at
`:1968` carrying four five-key `fold` fences; I read each `design:` and `work:` quote where it claims
to be, per the fold rule, rather than judging the quoted pair alone — M1's `design` is Design §1's
rule sentence at `:1053-1055` verbatim and its `work` is Task 2 at `:1639-1647`; M2's is Design §3's
bound paragraph at `:1121-1124` and Task 4; M4's is Design §4's two-credit-point bullet at
`:1180-1191` and Task 4. All faithful. (2) M4's ruling now holds on every surface that states the
behaviour — Design §4 (`:1180-1203`), both paired Edge Cases (`:1527-1542`), Task 4 (`:1667-1671`),
R1 (`:2209-2218`) and the `## Verification` mutation at `:2102-2105` — and the fold is STRONGER than
the fence asked: it deletes `file_fixed` (`:882`), the `:949` fold outright and the `fixed += 1`
(`:972`), which closes my round-1 non-blocking note 1 in the same edit. I confirmed the frame myself
rather than the prose: the wikilink write at `:975` sits inside the `with` block but outside the
`if changed:` block at `:951`, so its raise propagates past any end-of-block fold to the handler at
`:993` — per-write crediting is the only placement yielding AC-4(b)'s signed answer. (3) Task 9 now
orders both halves of the containment guard and Design §7 states them.

The verdict turns on M3, and it is mechanical before it is substantive: the threat model's LATEST
SPEAKING round moved M3's requirement, and the fold record still quotes the superseded one.

### Citation verification

All verified ✓ — every symbol-anchored citation the spec leans on was re-resolved by reading the
code at each site, and each MEANS what the spec claims:

- `scripts/lint_vault.py` — `NameGateRefusalRecord:805-818` with the two-field closure and the
  docstring reason for it; `FixOutcome:820-825` as `(fixed, refused)`; `apply_fixes:827-828` with
  `idx: Optional[dict] = None`; `by_file` filtering on `issue.auto_fixable` at `:832-835`; the
  `FileNotFoundError` guard at `:853`; the lock and `read_note` at `:858-859`; `file_fixed = 0` at
  `:882`; the five repair branches at `:888`, `:896`, `:903`, `:911`, `:929` and the six decline
  sites at `:890`, `:906`, `:913`, `:935-936`, `:963-973`; `:897` really is
  `fpath.stem.lstrip("@")`; `person_missing_name:896-901` really has no guard; the unconditional
  `gate_write` at `:947` landing BEFORE `fixed += file_fixed` at `:949`; the first write at `:957`
  inside `if changed:` at `:951`; the second at `:960-975` with its own `fixed += 1` at `:972`; the
  uncounted `except Exception` print at `:993-994`; the return at `:996`; `run_lint:1147-1148` with
  `vault_path` as the FIRST positional (which §6(d)'s position rule depends on), `read_vault` bound
  at `:1160`, the summary print inside `if fixable:` at `:1191-1199` and the
  `"No auto-fixable issues found."` else-arm at `:1213-1214`.
- `tests/test_lint_vault_fix_gate.py` — `:117-118`, `:123-125` (the per-file error print pinned as an
  equality over the exception's MESSAGE, which is why Design §4 leaves `:994` alone), `:230-231`,
  `:234-237` (`NameGateRefusalRecord._fields` by equality), `:244-248` (captured stderr equals a
  ONE-element list, which is what makes Design §4's "PRINTS ONCE" per file load-bearing rather than
  stylistic), `:265`, `:270`, `:276-281`. The nine-site rename inventory and the four non-moving
  `.refused` sites are exactly as the handoff note enumerates.
- `tests/derivations.py` — `SCRIPTS_ROOT:33`, `python_files_under:185`,
  `skip_reason_return_values:1528`, `skip_reason_literal_sites:1585`. Design §1/§6/§8 carry the
  current ordinals.
- `tests/test_fixture_vault.py` — both universe sites still unwidened
  (`python_files_under(PACKAGE_ROOT, TESTS_ROOT)` at `:508-509` and `:1302`), both declared-homes
  sets still exactly two members at `:510-514` and `:1315-1318`.
- `tests/test_ac_interpreter.py:47-50` — `WORK_ITEM_DOCS` carries exactly the two docs the spec says,
  and `test_every_acceptance_criterion_passes_under_the_conveyors_interpreter` is at `:108`.
- `tests/test_vault_path_required.py` — the universe really does stop at
  `("obsidian_schemas", "scripts")` at `:320` and the three patterns really are literal-path shapes
  that cannot see an environment read (`:278`), so Design §7's hazard claim is true. One re-anchoring
  nit on the trailing ordinal — non-blocking note 1.

### Blocking issues

1. **M3's fold record is STALE against the latest speaking threat-model round, so `specced -> ready`
   is refused as things stand.** `## Threat Model — 2026-09-15 (round 2)` re-emits all four
   `mitigation` fences, which makes it the latest SPEAKING round (`parse_mitigations` selects the
   last round that OPENED ≥ 1 fence, `work_item_linter.py:2976-2990`), and it is the ONE fence whose
   requirement moved: M3's `desc` at `:3437` now carries a second clause — "*and the syntax half
   asserts PROVENANCE and not merely spelling — every binding in that module of the identifier it
   accepts is a call to the single `_temp_vault` door — so a drive cannot satisfy the wall by
   re-binding that name to a path the door never produced*". The fold record's `desc` at `:2014` is
   byte-identical to the SUPERSEDED round-1 fence at `:3009` and carries none of it. D8c computes the
   per-mitigation status by comparing exactly those two strings —
   `normalize_fold_value(rec["desc"]) != normalize_fold_value(m["desc"]) -> ("stale", "")`,
   `src/stage_advancer.py:1249-1251`, precedence documented at `:1219-1226` — so a PROMOTE here buys
   a refused transition for the same mechanical reason my round-1 blocker 1 did. M1, M2 and M4's
   records are fresh (their round-2 fences re-emit round 1's `desc` unchanged; I diffed all four).
   The fix is to re-copy M3's `desc` verbatim from `:3437` — and it is NOT sufficient on its own,
   which is item 2.

2. **M3's tightened requirement is on ZERO surfaces, and SIX surfaces state the spelling-only rule
   the tightening exists to replace — one of them making a claim that is false of its own
   mechanism.** This is the WI-226 sweep obligation, not an edit: the ruling is folded only when
   every surface stating the behaviour states it. Enumerated:
   - **Design §6(d) (`:1300-1313`)** — `mutating_drive_vault_args` returns
     `(module_id, lineno, <the identifier bound to that call's VAULT argument>)` and nothing else. It
     collects CALL sites only; it never looks at an `Assign`, so nothing it returns can distinguish
     `vault = _temp_vault(tmp)` from `vault = lint_vault.DEFAULT_VAULT`.
   - **Design §7's syntax half (`:1360-1368`)** — asserts "EVERY triple it returns carries the
     identifier `vault` — the local every check binds from `_temp_vault(...)` and from nothing else".
     It asserts the first half of that sentence and never the second, and then states outright: "The
     runtime half alone would prove only that the door works; **the syntax half is what proves every
     drive went through it**." That sentence is FALSE of the mechanism as specified, and it is the
     sentence a builder reads to decide the guard is finished.
   - **Task 9 (ii) (`:1741-1746`)** — orders the assertion in the same spelling-only shape.
   - **`## Verification`'s counting-wall bullet (`:2064-2075`)** — "the one whose green is
     `every arg == "vault"`", with four positive shapes and three near-misses, none of which is a
     re-binding.
   - **`## Write Targets`' `tests/derivations.py` fence (`:1882`)** — "asserts each is the local the
     module's one temp-vault door returns", which is the overclaim again in the declaration the
     conveyor reads.
   - **`## Mitigation Folds`' own sweep paragraph (`:1984-1987`)** — "Sweeping the next level … returned
     `lint_vault.DEFAULT_VAULT`, `os.environ[…]`, a literal path and any other bound name … so the
     level is closed rather than sampled." The re-binding shape is a member of that level the sweep
     did not return, so the paragraph's own completeness claim is now falsified.

   I confirmed the residue myself rather than taking the threat modeler's trace: under §6(d) as
   specified, `lint_vault.DEFAULT_VAULT` is an `ast.Attribute`, `os.environ["OBSIDIAN_VAULT_PATH"]`
   a `Subscript` and a literal a `Constant` — all three RAISE — and any other bound name is RED
   naming the line, which leaves exactly `vault = lint_vault.DEFAULT_VAULT` followed by
   `run_lint(vault, do_fix=True)`: the syntax half sees the accepted identifier and the runtime half
   never executes because `_temp_vault` was never called. The blast radius is the largest in this
   item and it is not hypothetical — `DEFAULT_VAULT = os.environ.get("OBSIDIAN_VAULT_PATH", "")` at
   `scripts/lint_vault.py:56` sits on the very module the new check loads by path, the baseline
   records that variable as exported on Dave's machine (`docs/lint-vault-live-baseline.md:10-11`),
   and this is the first floor-resident module ever to drive the MUTATING entry point, on every
   floor run plus five `-S` re-execs. The closure the threat modeler names is one clause over a
   module `mutating_drive_vault_args` already parses — every `Assign` in that module whose target is
   the name `vault` has a `Call` to `_temp_vault` as its value — but it cannot be written in the
   check module itself, because `ast` is single-homed to `tests/derivations.py` (constraint 2), so
   §6(d) has to return the binding evidence and Task 7 has to order it. A `desc` re-copied under item
   1 without this sweep would make the record mechanically FRESH while the mitigation is still
   unsatisfied, and the satisfaction judgment is the only wall left at that point — which is why
   these are two findings and not one.

   Do NOT close this by narrowing M3 back to spelling. And while the sweep is open, `## Verification`
   owes the matching fixture pair the WI-235 prescription already requires of this wall: the
   re-binding shape driven through the predicate as a RED, beside a near-miss the predicate must not
   match (a `vault = _temp_vault(tmp)` binding in a module that also binds some other name).

### Non-blocking notes

1. **One stale trailing ordinal, in Design §7 (`:1347`).** It cites
   `tests/test_vault_path_required.py:FORBIDDEN_DEFAULT_PATTERNS:320`; the symbol is at `:278` and
   `:320` is the `for directory in ("obsidian_schemas", "scripts")` line the sentence is actually
   about. The symbol resolves and both halves of the claim are true of it, so this is a re-anchoring
   nit rather than drift — worth the one-character fix only because §7 is being edited anyway under
   blocking issue 2.

2. **`_temp_vault`'s third comparison should read `os.environ.get(...)`, not a subscript** —
   threat-model round 2's note 2, which I am carrying rather than re-deriving because it lands in
   text blocking issue 2 rewrites. Design §7 (`:1356`) and Task 9 (`:1739`) both write
   `Path(os.environ["OBSIDIAN_VAULT_PATH"]).resolve()` and guard it in PROSE with "when either is
   set and non-empty"; the literal form raises `KeyError` where the variable is unset, which is the
   graded/CI case, reddening the door rather than a drive. One edit, same paragraph.

3. **Design §7's non-AC check count and `## Risk Analysis` R4's "eight checks" both still hold after
   blocking issue 2's fix, provided the provenance clause lands INSIDE
   `test_every_mutating_drive_in_this_module_is_confined_to_a_temp_vault` rather than as a ninth
   check.** Stated so the fix does not silently move the three counts (Design's opening inventory,
   §7, R4, Task 16's expected direction) that this document has already had to re-sync once.

### What is NOT a gap — checked and clean

Stated so the next round does not re-walk them. `## Write Targets` coverage is exact in both
directions: each of the sixteen tasks' target files appears in the nine builder `writes` fences and
no fence names a path no task writes; the two `kind: precondition` paths are read by AC-5 and appear
in no builder fence; the driven doc is implicit; Tasks 1 and 16 write only the Build Log. Every path
is inside `pipeline-runners.yaml:34-38`'s grant, so the L3 level the frontmatter carries is not
under-declared. Sixteen canonical `- [ ] **Task N — …**` definitions with unique ordinals 1–16; every
`landed: Task N` across both threat-model rounds (2, 4, 9, 4) resolves to one, so no D8b refusal is
latent here. All sixteen carry a well-formed `verify:` declaration — fourteen naming bare `test_`
names, Task 1 declaring `baseline` with its reason and Task 16 `hand-run` with its reason, both
correct uses of the closed exception kinds — and no verify command writes anything outside
`write_authority`. Task 9's verify now names a check Task 9 itself creates, which closes my round-1
note 2. `OPEN: None`, zero open items. The five criteria remain signed and untouched by the fold
round: `ac_hash: 973d7a08f068` with all five per-criterion hashes and `intent_hash` unmoved, and
every edit since the signature sits outside `## Intent` and `## Acceptance Criteria` — I checked the
spans rather than trusting the claim. The WI-235 counting-wall prescription is otherwise discharged
in `## Verification` (each count-shaped oracle and each artifact reader driven through the wall's own
predicate with a named near-miss), the WI-278 corpus-fixture arm is chosen explicitly in AC-5(b)'s
one-line coupling declaration, and the WI-229 conscious-pin sweep is what produced the nine-site
rename inventory across four modules.

### Carried-forward notes

Every still-open non-blocking note from every prior round, by name:

- **Threat model round 1 note 1 / round 2 note 3 (the exit attestation's redaction reminder is absent
  from `docs/lint-vault-live-baseline.md` §4's own bytes)** — STILL OPEN, re-deferred for the fourth
  time for the same correct reason: §4 is conductor-owned and outside the builder's write authority,
  so it has no Implementation-Plan task to land in and a fence pointing at one would be a fiction.
  The conductor's, at the ship door.
- **Threat model round 1 note 2 / round 2 note 4 (`apply_fixes:994` prints `str(exc)` to stderr)** —
  STILL OPEN as a deliberate non-change. Re-deferred: the rendering is pinned as a message equality
  at `tests/test_lint_vault_fix_gate.py:123-125` and the handler set does not widen, so closing it
  would move a pinned equality for no gain in this item.
- **Threat model round 2 note 1 (M3's wall universe is ONE module, and widening is not free because
  `test_lint_vault_fix_gate.py:280` passes a `Constant` §6(d) is specified to RAISE on)** — recorded
  as a standing scope ruling, not an open note; routed against above rather than re-litigated.
- **Threat model round 2 note 2 (`_temp_vault`'s `os.environ` subscript)** — STILL OPEN, carried as
  my non-blocking note 2 above and actionable inside blocking issue 2's edit.
- **Data audit round 2's two carried items** — both STILL OPEN and both correctly outside the spec:
  the build-start re-grounding should re-run AC-5(b)'s five-row comparison before the first edit (the
  baseline is now five days old and the vault churns weekly), and the exit half of A7's bracket has
  no battery wall by construction and lives at the conductor's ship door.
- **My round-1 notes 1–5** — all CLOSED: note 1 (`:972` / `file_fixed`) by M4's fold deleting both;
  note 2 (Task 9's forward-referencing verify) by the containment check Task 9 now creates; note 3
  (the stale "Signature impact" narration) by the dated SETTLED paragraph at `:799-813`; note 4
  (`bounded_cause`'s ordinal) by threat-model round 2 note 4; note 5 (the privacy wall's reach) by
  its own round.
- **Architect round 4 notes 1–4 and the AC red-team's label slip** — all CLOSED, recorded in my
  round-1 section.

```verdict
gate: spec-reviewer
verdict: REVISE
date: 2026-09-15
model: claude-opus-5
targets: M3, Task 7, Task 9, #design, #verification, #mitigation-folds
prior: held
basis: folded-material
findings: 2/4
note: My three round-1 blockers all closed and I verified them against the code rather than the fold record — the four fold records' `design`/`work` quotes are faithful where they claim to be, and M4's fold is stronger than its fence asked (deleting `file_fixed`, the `:949` fold outright and the `:972` increment), which I confirmed by re-reading the frame: the `:975` write sits outside the `if changed:` block at `:951`, so only per-write crediting yields the signed AC-4(b). What blocks is M3 alone, and mechanically first: `## Threat Model — 2026-09-15 (round 2)` re-emits all four fences and is therefore the latest SPEAKING round, its M3 `desc` (`:3437`) now requires the syntax wall to prove PROVENANCE and not merely spelling, and the fold record at `:2014` is byte-identical to the superseded round-1 fence at `:3009` — D8c compares exactly those two strings (`stage_advancer.py:1249-1251`) and refuses `specced -> ready` as stale. A re-copied `desc` alone would make the record fresh while the mitigation stayed unsatisfied: the provenance requirement is on zero surfaces and six surfaces state the spelling-only rule, including Design §7's "the syntax half is what proves every drive went through it", which is false of its own mechanism — `mutating_drive_vault_args` collects CALL sites only, so `vault = lint_vault.DEFAULT_VAULT; run_lint(vault, do_fix=True)` passes the syntax half while the runtime door never executes, against `DEFAULT_VAULT = os.environ.get("OBSIDIAN_VAULT_PATH", "")` (`scripts/lint_vault.py:56`) on the module the new check loads and 3,952 live notes on every floor run forever. Everything else re-verifies clean: all symbol-anchored citations resolve AND mean what the spec claims, Write-Targets coverage is exact both ways, sixteen canonical tasks each carry a well-formed `verify:`, every `landed: Task N` resolves, and the five signed criteria are untouched by the fold round.
```


## Adversarial Review — 2026-09-15 (round 2)

Cold-start re-read, full document, all 3710 lines: frontmatter through the round-2 `## Spec Review`
verdict fence at the tail. Also re-read the injection-hunter role definition and its machine contract
before starting. The carry-forward is my own round-1 section (`:3285-3303`, PROMOTE, no manipulation
found) — its scope covered the document through the first `## Spec Review` round. This round's job is
the material that landed AFTER it: `## Adversarial Review — 2026-09-15` (round 1) itself, `## Threat
Model — 2026-09-15 (round 2)`, and `## Spec Review — 2026-09-15 (round 2)`. I read all three fresh
rather than trusting either round's account of itself, and re-swept the whole document rather than
diffing, since a planted instruction could in principle sit anywhere a prior round's narrower diff-read
would have missed.

**The one question, applied to the three new sections.** Threat-model round 2 is, on its face, the
section most exposed to steering-shaped language: it uses first-person confirmation heavily ("I
re-read the frame rather than the fold", "I confirmed it changes no write") and lands a finding that
narrows rather than blocks — M3 is "carried as a TIGHTENING... rather than as a REVISE" with the
explicit argument "a REVISE would buy nothing the fence does not." Read adversarially, that is exactly
the shape an injection would want: a paragraph arguing a reviewer into a softer verdict. But the
argument is not free-floating — it is load-bearing on a specific, re-checkable code fact (§6(d)'s scan
returns only `(module_id, lineno, identifier)` from CALL sites, never from `Assign` targets, which I
independently confirmed against `tests/derivations.py`'s scan shape as Design §6(d) states it), and the
very next section — `## Spec Review — 2026-09-15 (round 2)` — reads that same tightening and REVISEs
anyway, on the grounds that the tightened `desc` isn't yet landed on any surface. A planted "don't
block, just tighten" instruction would need the very next independent gate to fail to notice it; instead
the next gate is the one that catches the residue the tightening left open. That is the review chain
disagreeing with itself in the normal, adversarial way — not steering propagating cleanly downstream.

**`## Adversarial Review` (round 1) itself, read as content rather than trusted as a peer's verdict.**
The role's own calibration section warns that a false PROMOTE is the failure this gate exists to catch,
which means round 1's PROMOTE is itself part of my attack surface this round, not a citation I get to
lean on. Reread it in full: its reasoning is structurally the same shape I would use — it names the two
mechanical injection vectors the machine contract itself calls out (a stray example heading; a
reproduced planted specimen), checks both against the actual document, and finds neither. I repeated
both checks independently rather than taking its word: grepped `^## ` again (the heading list in my
first tool call this round matches round 1's account exactly, with `## Adversarial Review` appearing
only where the two dated rounds legitimately sit), and reread every planted-specimen description in the
document (`@Tarnquil  Brenvik.md`, the double-space stem, the four-topic meeting, the inner-trailing-
space wikilink) — all are lint-rule test discriminators with file:line grounding, none is prose
addressed to a reviewing agent, and none matches the shape of a WI-091-class exam canary this document
would need to defang.

**The two new gate sections, swept the same way round 1 swept the first four.** Nothing in either
reads as an instruction to a reviewer. Both are further re-derivations against code — threat-model
round 2 re-traces `:887-975` byte by byte before agreeing with its own round-1 fold; spec-review round 2
re-verifies eleven-plus symbol citations before reaching its blocking finding, and that finding argues
AGAINST the document's own prior claim (Design §7's "the syntax half is what proves every drive went
through it" is called "FALSE of the mechanism as specified" — a gate refuting the spec's own prose is
the opposite of a gate persuaded by it). No sentence in either section has the reviewing agent as its
grammatical subject in an instructional sense ("I read", "I confirmed", "I re-derived" are reports of
what the gate did, not directives to the next one).

**Escalation check, honestly applied.** The one place I paused longest was threat-model round 2's
"a REVISE would buy nothing the fence does not" — the closest thing in this round to a sentence that
argues a specific reviewer away from a specific verdict. Weighed against: it is scoped to ONE
mitigation's classification (fold vs. REVISE) under a rule (WI-128/D8) the document did not invent for
this occasion — the same fold-vs-REVISE distinction is used identically, by the same gate type, in this
document's own round-1 threat model for M4 (`:2914-2926`) and is native machinery per the role's own
"What You Are NOT" section ("deterministic checks... rung 4"). An injection exploiting house style would
be indistinguishable from house style only if it never got caught downstream; here it got caught one
section later. I read this as the mechanism working, not as a plant I am rationalizing — but flagging
the reasoning rather than asserting it silently, per this gate's honest-limit clause.

No manipulation found in the material this round covers, and round 1's finding over the earlier material
still holds on reread. This is a real finding, not a skipped check.

```verdict
gate: injection-hunter
verdict: PROMOTE
date: 2026-09-15
model: claude-sonnet-5
note: Cold-start re-read of the full document plus the three sections that landed after round 1's Adversarial Review (round 1 itself, Threat Model round 2, Spec Review round 2) — no instruction-to-a-reviewer text found in any of them; threat-model round 2's fold-not-REVISE argument for M3 is scoped to native WI-128/D8 machinery this document also used identically in round 1, and it is the very next gate (Spec Review round 2) that catches the residue the tightening left unlanded, which is the review chain disagreeing with itself adversarially rather than steering propagating downstream. Round 1's PROMOTE re-verified independently rather than trusted: its two named injection vectors (stray example heading, reproduced planted specimen) both checked negative again on a fresh grep and reread.
```


## Threat Model — 2026-09-15 (round 3)

**Recommendation: PROMOTE to threat-modeled**

Third round. The carry-forward is this document's own two prior rounds and what happened to each: round 1
PROMOTEd with four `kind: required` mitigations and the spec-reviewer REVISEd because none had been
folded; the spec-writer's `## Mitigation Folds — 2026-09-15` landed all four; round 2 read the folded
material, verified M1/M2/M4 against the frame and TIGHTENED M3's `desc` to require PROVENANCE rather than
spelling; the spec-reviewer REVISEd again — the fold record was byte-stale against that tightening and the
tightened requirement stood on zero surfaces while six stated the rule it replaced. The spec-writer has
since re-copied M3's `desc` and re-folded its substance. So this round has the same one job round 2 had,
one turn later: read the RE-folded material as a new attack surface. Every citation below was re-resolved
off this tree (worktree `cage-wt-_e7mavhf`) by reading the code, not taken from the fold's account of
itself or from a prior gate's paraphrase.

### Trigger check

The same four triggers fire, unchanged and for the same reasons: filesystem operations on user-owned files
(`apply_fixes:957`, `:975`, `quarantine_garbage:1140`), untrusted input (vault bytes, with the new crossing
at `read_vault:115-118`), persistence (the committed live-vault measurement plus a floor-resident module
driving the MUTATING entry point), and an information-disclosure surface (the operator-facing summary,
against `obsidian_schemas/errors.py`'s bounded-projection contract). The re-fold retired none of them. It
added material to elevation-of-privilege only, which is where this round spent its time.

### The re-fold, verified against the code rather than against the fold record

- **M1, M2, M4 — records intact, substance undisturbed by this round's edits.** I re-checked each on its
  own surface rather than diffing the fold section: M1's rule sentence is Design §1 at `:1073-1075` with
  `read_error=UNREADABLE` in the recording form at `:1066`; M2's bound is Design §3 at `:1152` (`reason:
  str  # type(exc).__name__ — NEVER str(exc), never note bytes`) and `:1161`, with Task 4 carrying it at
  `:1767-1768`; M4's two credit points are Design §4 at `:1225` and Task 4 at `:1773`. All three `desc`
  values in the fold record (`:2156`, `:2164`, `:2180`) are byte-identical to my round-2 fences, so their
  records stay fresh and all three are re-emitted unchanged below.
- **M4 re-confirmed against the frame, not the prose, because the re-fold edited the section around it.**
  `scripts/lint_vault.py:949` (`fixed += file_fixed`) still sits above the `if changed:` at `:951` and the
  first `write_note` at `:957`; the wikilink write at `:975` sits inside the `with` block but OUTSIDE
  `if changed:`, so its raise propagates past any end-of-block fold to the handlers at `:977`/`:993`.
  Per-write crediting remains the only placement that yields AC-4(b)'s signed answer. Unchanged.
- **M3 — the record is fresh and the tightening is landed on every surface the spec-reviewer enumerated.**
  The fold record's `desc` at `:2172` is byte-identical to my round-2 fence at `:3623`, and the substance is
  on all six: Design §6(d)'s `VaultArgScan` pair with the `bindings` provenance census and its closed
  RAISE set (`:1339-1399`, including the vacuity hole closed INSIDE the scan at `:1390-1394`); Design §7's
  three-clause syntax half with (iii) named as the tightening and the "no proper subset" sentence replacing
  the old overclaim (`:1454-1472`); Task 7's provenance half (`:1812-1829`); Task 9 (ii) clause three,
  ordered inside the ONE check rather than as a ninth (`:1859-1869`); `## Verification`'s `bindings`
  fixture battery with four REDs, the scoping near-miss and the closed-set RAISES (`:2236-2255`) plus the
  tenth mutation that separates the tightened requirement from its superseded one (`:2288-2294`); and
  `## Write Targets`' `tests/derivations.py` fence, which now states the pair rather than the spelling
  claim (`:2009`). Two prior non-blocking notes closed with it: Design §7 now cites
  `FORBIDDEN_DEFAULT_PATTERNS` at `:278` (`:1436`), and both the Design (`:1448-1450`) and Task 9
  (`:1855-1857`) now write `os.environ.get(..., "")` with the reason — my round-2 note 2, CLOSED.

### STRIDE review — scoped to what the re-fold added

**Spoofing — nothing new.** No authentication boundary moved; `person_missing_name` still writes
`fpath.stem.lstrip("@")` (`:897`) through the unchanged `gate_write` at `:947`.

**Tampering — the re-fold adds no write.** §6(d)'s `bindings` census is `ast` parsing over files already
read; §7's door is a comparison over resolved paths it holds in-process. No branch's repair logic, no
`delta` key, no gate call and no `write_note` argument moves. WI-004's concurrency contract is untouched.

**Repudiation — improved, not regressed.** Every new arm reports loudly: `NOT_A_CALL` is RETURNED so the
WALL reddens naming the binding's line, and every other binding construct RAISES naming module and line
(`:1380-1388`). Nothing added here can decline silently.

**Information disclosure — the new census carries no note content.** A `bindings` 4-tuple is
`(module_id, lineno, identifier, provenance)`: a repo-relative module id, an integer, and two identifiers
read out of the check module's own source. The failure messages name module and line. Nothing on this path
can reach a vault path or a note filename.

**Denial of service — unchanged and bounded.** No network, no retry, no recursion; the census is O(nodes)
over one file.

**Elevation of privilege — the finding, and it is the same generator as round 2's one level UP instead of
one level down.** M3's wall claims TOTALITY over future drives — the fold's own words are that "every drive
Tasks 10–15 add and every drive anyone adds later is covered by construction rather than by the author
remembering" (`:2117-2119`). Round 2 falsified that claim below the level the first sweep looked at (the
BINDING of the accepted identifier), and the re-sweep closes that level properly, by `ast`'s own closure
rather than by a list (`:2129-2141`). But the level ABOVE is still a list somebody wrote down, and it has
two members: `drives` collects only calls "whose callee resolves to the bare name `apply_fixes` or
`run_lint`" (`:1349-1351`). `scripts/lint_vault.py` has a THIRD mutating entry point, and it is the one
with the worst default in the file:

- `main()` at `:1252` declares `--vault` with `default=DEFAULT_VAULT` (`:1255`) and calls
  `run_lint(vault_path, …, do_fix=args.fix, do_quarantine=args.quarantine)` at `:1299-1308`. So the CLI
  route does not need an attribute access to reach Dave's vault the way round 1's shape did — it needs
  an OMISSION. `lint_vault.main()` with `sys.argv` carrying `--fix` and no `--vault`, or
  `subprocess.run([sys.executable, "scripts/lint_vault.py", "--fix"])`, runs `--fix` against
  `OBSIDIAN_VAULT_PATH`.
- Both routes are invisible to BOTH halves of the wall. The callee is neither `apply_fixes` nor `run_lint`,
  so `drives` collects nothing; `bindings` is scoped to the identifiers `drives` names (`:1363-1365`), so
  it collects nothing either; and `_temp_vault` is never called, so the runtime door never executes. The
  module passes clauses (i), (ii) and (iii) with a drive that mutates the live vault — which is precisely
  the shape M3 exists to refuse, arriving through a door the wall does not watch.
- This is not a shape I had to invent: the tree already drives this CLI exactly that way, and already
  defends against exactly this. `tests/test_vault_path_required.py:_run_lint_vault:344-353` runs
  `[sys.executable, "scripts/lint_vault.py", *args]` by subprocess and SCRUBS `OBSIDIAN_VAULT_PATH` out of
  the environment first, with its sibling check's docstring (`:356-365`) naming the corruption door in
  terms — "without the guard the linter would run against the current working directory — and
  `--quarantine` renames the files it finds". The precedent module is one `python_files_under` away from
  the new one and is the nearest thing a builder has to copy from. And AC-4's own `why` pushes toward that
  surface: it complains that "no test anywhere under `tests/` calls `run_lint` or captures its stdout, so
  the CLI half of that sentence has never been checked" — which I confirmed is still true (grep for
  `run_lint(` / `main(` under `tests/`: no live call site). AC-4(d) does pin `run_lint` + `redirect_stdout`
  as its mechanism today, so the PLAN as written does not drive the CLI; the hazard is the next drive, and
  covering the next drive is the whole claim the wall makes.

The closure is two clauses, both over machinery the plan already ships, and neither needs a new check:

1. `main` joins §6(d)'s callee set. The rule already in §6(d) then does the work with no new text — "a
   collected call passing a vault argument at NEITHER position RAISES" (`:1355-1356`) — and `main()` takes
   no vault argument at any position, so ANY `main` call in that module reddens the wall at its own line.
   Carried as **M5**, landed in Task 7 because the callee set is that task's.
2. The subprocess route is refused at the import. `tests/derivations.py:module_import_uses:847-870` is
   alias-proof (it reports the ORIGINAL module name in both statement forms) and Task 15 already runs it
   over the new check module (`:1954-1956`) — but the standing module set does not reach this: `FS_MODULES`
   is `{"os", "shutil", "tempfile", "fcntl", "filelock", "mmap"}` (`tests/derivations.py:68`) and
   `WALL_C_MODULES` is that minus `os` (`tests/test_name_gate_wall.py:1043`), so `subprocess` is in neither.
   Carried as **M6**, landed in Task 15. The `os`-attribute form of the same escape needs nothing: the
   standing predicate `os_module_attribute_uses:800-844` returns every `os.<attr>` access and
   `OS_READONLY_NAMES` (`:69`) holds only `environ`/`getenv`/`sep`/`path`/`fspath`/`getcwd`, so
   `os.system` / `os.popen` / `os.execv` in the new module is already RED under the wall Task 15 runs.

Carried as two fences rather than as a third tightening of M3, and rather than as a REVISE. M3's `desc`
describes the vault ARGUMENT of the two direct callees and it is now landed and satisfied; this is a
different entry point with no vault argument at all, so re-opening M3's `desc` would re-stale a fold record
that is currently fresh and spend a producer round re-sweeping a requirement that did not move (the
FIDELITY rule). And the approach is not unsafe — the design's intent is stated, the mechanism is sound for
the callees it watches, and the gap is two clauses in tasks that already exist and already run the
predicates. That is exactly the case WI-128/D8 owns.

### Mitigations required

1. **M1 — the read-error value is a vocabulary member, never the decode exception.** Folded into Design §1
   and Task 2; re-verified this round. Re-emitted unchanged.
2. **M2 — both new records carry bounded values.** Folded into Design §3 and Task 4; re-verified this
   round. Re-emitted unchanged.
3. **M3 — the containment wall, with the syntax half asserting provenance.** Re-folded this round onto all
   six surfaces and verified against the code. `desc` UNCHANGED from round 2 and re-emitted byte-identically
   — the requirement did not move, it landed.
4. **M4 — an issue whose write committed is never re-labelled `errored`.** Folded into Design §4, both
   paired Edge Cases, Task 4, R1 and a `## Verification` mutation; re-verified against the frame this round.
   Re-emitted unchanged.
5. **M5 — the CLI entry point is inside the wall's callee set.** NEW this round; needs fold work in Task 7.
6. **M6 — the module cannot reach the CLI by subprocess either.** NEW this round; needs fold work in
   Task 15.

```mitigation
kind: required
id: M1
desc: read_vault's recorded read_error value is the IMPORTED SKIP_REASONS member UNREADABLE and never str(exc) of the decode failure, so undecodable note bytes are never decoded, never rendered into an issue message and never stored in any record.
landed: Task 2
```

```mitigation
kind: required
id: M2
desc: FixErrorRecord.reason is the exception's class name and FixDeclineRecord.guard is a DECLINE_GUARDS member — never str(exc), never note bytes — because both records feed the operator-facing summary that gets pasted into chat.
landed: Task 4
```

```mitigation
kind: required
id: M3
desc: every apply_fixes and run_lint(..., do_fix=True) drive in tests/test_lint_vault_fix_rules.py takes a vault path rooted in a fresh tests/support.temp_dir(), never lint_vault.DEFAULT_VAULT, never OBSIDIAN_VAULT_PATH and never any path outside that directory, and the module asserts that containment before the first mutating call; and the syntax half asserts PROVENANCE and not merely spelling — every binding in that module of the identifier it accepts is a call to the single _temp_vault door — so a drive cannot satisfy the wall by re-binding that name to a path the door never produced.
landed: Task 9
```

```mitigation
kind: required
id: M4
desc: an issue whose own write has COMMITTED is credited at that commit point and is never re-labelled errored by a later raise inside the same lock block, so the issues carried by the write at :957 stay repaired when the wikilink write at :975 raises, as AC-4(b) requires.
landed: Task 4
```

```mitigation
kind: required
id: M5
desc: mutating_drive_vault_args' callee set includes main as well as apply_fixes and run_lint, so the tool's CLI entry point — whose --vault carries default=DEFAULT_VAULT at scripts/lint_vault.py:1255 and which therefore reaches the live vault by OMISSION rather than by an attribute access — is inside the wall rather than beside it; a main call in that module carries a vault argument at no position and so RAISES under the rule §6(d) already states, reddening the wall at its own line.
landed: Task 7
```

```mitigation
kind: required
id: M6
desc: tests/test_lint_vault_fix_rules.py imports no subprocess-capable module — subprocess and runpy are added to the module set Task 15 hands module_import_uses over that file, because WALL_C_MODULES is FS_MODULES minus os and contains neither — so the wall cannot be satisfied by a drive that re-enters the tool through its CLI as a child process, which is the shape tests/test_vault_path_required.py:344-353 already uses and has to scrub OBSIDIAN_VAULT_PATH out of the environment to make safe.
landed: Task 15
```

### Notes (non-blocking)

1. **The provenance clause compares the door's NAME, so a decoy named `_temp_vault` is green — recorded as
   the honest bound of the mechanism rather than proposed as a fix.** §6(d) resolves a dotted callee to its
   `ast.Attribute.attr` (`:1369-1372`), so `helpers._temp_vault(tmp)` yields provenance `"_temp_vault"`, and
   a `from x import make as _temp_vault` or a second `def _temp_vault` later in the module would pass the
   same way while the real door never runs. The `## Mitigation Folds` re-sweep slightly overclaims here —
   "an alias, a wrapper or a second constructor is RED naming its line" (`:2140-2141`) is true of
   `make_vault` and false of anything spelled with the door's own name. I am NOT carrying this as a
   mitigation: every one of those shapes is a deliberate act rather than the drift or the convenient
   shortcut the wall exists to catch, and chasing the regress one more level buys a clause per level
   forever. Worth one sentence's correction in that paragraph if it is edited anyway.
2. **The syntax half is a DETECTOR and the runtime door is the only PREVENTER, so within the run that first
   contains an escaping drive the mutation happens before the wall reports it.** The wall is one check among
   eight in the module it guards, and pytest runs a module's checks in definition order — so defining
   `test_every_mutating_drive_in_this_module_is_confined_to_a_temp_vault` FIRST in the module is a free
   ordering improvement that makes it fire ahead of the driving checks in an ordinary floor run. Not a
   mitigation (ordering is not a guarantee under `-k` or direct invocation, and M5/M6 close the routes that
   bypass the door), but cheap and worth doing while Task 9 is being written.
3. **Round 1 note 1 / round 2 note 3 (the exit attestation's redaction reminder is absent from
   `docs/lint-vault-live-baseline.md` §4's own bytes) — STILL OPEN**, re-deferred a fifth time for the same
   correct reason: §4 is conductor-owned and outside the builder's write authority, so it has no
   Implementation-Plan task to land in and a fence pointing at one would be a fiction. The conductor's, at
   the ship door.
4. **Round 1 note 2 / round 2 note 4 (`apply_fixes:994` prints `str(exc)` to stderr) — STILL OPEN as a
   deliberate non-change.** Re-verified at the code this round: the print is still `f"  Fix error on
   {fpath.name}: {exc}"` at `:994` and the handler set does not widen, so no new content reaches that
   channel; it is pinned as a message equality at `tests/test_lint_vault_fix_gate.py:123-125`.
5. **Round 2 note 2 (`_temp_vault`'s `os.environ` subscript) is CLOSED** by this round's fold, on both
   surfaces (`:1448-1450`, `:1855-1857`). **Round 2 note 1 (M3's wall universe is ONE module) stands as a
   scope ruling** and is routed against rather than re-litigated — note that M5 and M6 do not widen it
   either; both are clauses over the same single module.

```verdict
gate: threat-modeler
verdict: PROMOTE
date: 2026-09-15
model: claude-opus-5
note: M3's re-fold is faithful and complete — its `desc` at `:2172` is byte-identical to my round-2 fence and the tightening is landed on all six surfaces the spec-reviewer enumerated, with §6(d)'s `bindings` census closing the binding level by `ast`'s own closure (every non-Assign construct RAISES, an identifier with no binding site RAISES) and §7's overclaim replaced by "no proper subset of (i)+(ii)+(iii)"; M1/M2/M4 re-verified on their own surfaces and against the frame (`:949` still above `:951`, the `:975` write still outside `if changed:`), all three records fresh, all four re-emitted unchanged. The finding is round 2's generator one level UP instead of one level down: the wall claims totality over future drives, but its callee set is still a two-member hand list, and `main:1252` is a third mutating entry point whose `--vault` carries `default=DEFAULT_VAULT` (`:1255`) and which calls `run_lint(..., do_fix=args.fix)` at `:1299-1308` — so the CLI route reaches Dave's 3,952 live notes by OMITTING an argument rather than by an attribute access, and it is invisible to `drives`, to `bindings` (scoped by `drives`) and to the runtime door alike. Not hypothetical: `tests/test_vault_path_required.py:344-353` already drives this CLI by subprocess and has to scrub `OBSIDIAN_VAULT_PATH` from the env to make it safe, and AC-4's own `why` points a builder at the CLI surface. Closure is two clauses over machinery the plan already ships — M5 puts `main` in the callee set, where §6(d)'s existing "no vault argument at either position RAISES" rule reddens it with no new text, and M6 adds `subprocess`/`runpy` to the module set Task 15 already hands `module_import_uses`, since `WALL_C_MODULES` is `FS_MODULES - {"os"}` and covers neither (the `os.system` form is already RED under `OS_READONLY_NAMES`). Two new fences rather than a third tightening of M3, which would re-stale a fresh record for a requirement that landed rather than moved.
```


## Adversarial Review — 2026-09-15 (round 3)

Cold-start re-read, full document, all 4477 lines end to end: frontmatter, Problem/Intent, both
currency audits, every Exploration-Notes approach (A1–A7b) and all eight constraints, all five
Revision rounds, Approach, Verified Diagnosis, the full Design (§1–§10), Edge Cases, all sixteen
Implementation-Plan tasks, both `writes` precondition fences and the nine builder `writes` fences plus
the handoff note, Verification, Scope Boundary, Risk Analysis, all five `criteria` fences and their
Examples of done, AC Red-Team round 3, Architectural Review round 4, AC Sign-off, Data Audit round 2,
Mitigation Folds, and every threat-model / spec-review / adversarial-review round in full, including
each one's own `verdict`/`mitigation` fence. Also re-read the injection-hunter role definition and its
machine contract before starting. The carry-forward is my own two prior sections
(round 1: PROMOTE, covering the document through the first Spec Review round; round 2: PROMOTE,
covering round 1 itself plus Threat Model round 2 and Spec Review round 2) — this round's job is the
material that landed after round 2: `## Adversarial Review — 2026-09-15 (round 2)` itself,
`## Threat Model — 2026-09-15 (round 3)`, and `## Spec Review — 2026-09-15 (round 3)`. I read all
three fresh and re-swept the whole document rather than diffing against my own prior accounts of it,
for the same reason round 2 gave: a planted instruction could in principle sit anywhere a narrower
diff-read would miss, and my own prior PROMOTEs are part of this round's attack surface, not a
citation I get to lean on.

**The one question, applied to the two new gate sections.** Threat-model round 3 is a re-fold-and-STRIDE
round that opens two NEW `kind: required` mitigations (M5, M6) over a hazard it traces independently —
`main:1252`'s `--vault` defaulting to `DEFAULT_VAULT` and reaching Dave's live vault by omission rather
than by an attribute access — and every claim in it is paired with a file:line a reader can re-execute
(`:1255`, `:1299-1308`, `tests/test_vault_path_required.py:344-353`). No sentence has the reviewing agent
as its grammatical subject in an instructional sense; "I re-checked", "I confirmed independently" are
reports of what the gate did, not directives to the next one. Spec-review round 3 then REVISEs on
exactly M5/M6 having no fold record — the D8c mechanical wall my own two prior rounds also hit on M3/M4
— and its reasoning is, again, the strongest evidence against manipulation in the chain: it re-derives
`main:1252`, `WALL_C_MODULES = FS_MODULES - {"os"}` and the two-member `§6(d)` callee set independently
of the threat model's trace rather than accepting it, and it explicitly FLAGS what it calls "the regress
signature" — naming, in its own prose, that each of my three peer-round's findings has landed on
material the *previous* fold added (wall → binding level → callee/import level), and recommending a
`## Scope Boundary` ruling to stop the ladder rather than emitting a fourth round on it. A planted
"keep re-revising forever" or "just PROMOTE, the family is obviously closed" instruction would look
nothing like a gate diagnosing its own regress pattern in writing and handing the sufficiency call to
Dave or the conductor rather than deciding it unilaterally.

**Self-check on the regress-signature observation, since a account of *my own* pattern from a prior
round is exactly the kind of content this gate should not take at face value.** Spec-review round 3's
characterization matches what I independently see across my three cold-start reads: M3 (round 1) was a
containment wall with no binding-provenance check; round 2's fold added `bindings` to close the binding
level; round 3 (this one) finds the callee (`main`) and import (`subprocess`/`runpy`) levels still open,
which M5/M6 close. That is a textbook WI-020-shaped ladder in a security-adjacent surface, not a
steering artifact — every step is a concrete, re-executable code fact (I re-checked `main:1252`'s
`default=DEFAULT_VAULT` and `run_lint(..., do_fix=args.fix)` at `:1299-1308` myself), and the gate
naming its own pattern in prose is the corroborator ladder functioning as designed, not a case of a
gate persuading itself something is fine.

**`## Adversarial Review` (round 2) itself, read as content rather than trusted as a peer's verdict,**
per the same discipline round 2 applied to round 1. Reread it in full: it checks the two mechanical
injection vectors the machine contract calls out (a stray example heading; a reproduced planted
specimen) against the document as it stood after round 2's material, and re-verifies round 1's PROMOTE
independently rather than citing it. I repeated both checks again this round on the FULL current
document: `^## ` heading grep shows `## Adversarial Review` appearing only at the three dated rounds
that legitimately sit in this document (round 1, round 2, and this one, freshly added below) — no stray
example heading anywhere — and every planted-specimen description in the newer material (`main()` /
`subprocess` / `runpy` as new attack-surface members named by M5/M6; no new corpus-plant descriptions
in this round's threat-model text beyond the ones rounds 1–2 already covered) is a lint-rule or
containment-wall test discriminator with file:line grounding, none of it prose addressed to a reviewing
agent, none of it a WI-091-class exam canary this document would need to defang.

**Mechanical sweep, whole document, this round.** Grepped for direct-address / authority-claim /
override patterns across all 4477 lines (`ignore the previous`, `pre-approved`, `emit PROMOTE`,
`should not block`, `disregard`, `rubber-stamp`, `SYSTEM:`, and the family the role's calibration
section names) — the only hits are inside my own and my prior rounds' prose EXPLAINING what was
searched for, which is the expected self-referential shape of an injection-hunter's own writeup and not
a plant. No HTML comment carries an instruction (`<!--` occurs exactly once outside verdict fences, the
machine-maintained "archive-split" pointer at the top of the document, which describes a file location
and nothing else). No occurrence of `you must`, `your verdict`, `as the reviewing model`, or any
sentence structured as an instruction to an AI reader anywhere in the document body.

No manipulation found in the material this round covers, and rounds 1 and 2's findings over the earlier
material still hold on this full reread. This is a real finding, not a skipped check.

```verdict
gate: injection-hunter
verdict: PROMOTE
date: 2026-09-15
model: claude-sonnet-5
note: Cold-start re-read of the full 4477-line document plus the three sections that landed after round 2 (round 2's own Adversarial Review, Threat Model round 3, Spec Review round 3) — no instruction-to-a-reviewer text found in any of them. Threat-model round 3 traces a genuinely new hazard (`main:1252`'s `--vault` reaching the live vault by omission) with re-executable file:line citations rather than persuasive framing; spec-review round 3's REVISE is the same mechanical D8c wall my own two prior rounds hit on M3/M4, now hit on M5/M6, and its prose explicitly names the cross-round "regress signature" and routes the sufficiency call to Dave/the conductor rather than deciding it — a gate diagnosing its own pattern in writing is the corroborator ladder working, not steering. Rounds 1 and 2's PROMOTEs re-verified independently rather than trusted: their named injection vectors (stray example heading, reproduced planted specimen) both check negative again on a fresh grep and reread of the full document, and a whole-document mechanical sweep for direct-address/override phrasing surfaces only prior injection-hunter rounds' own self-referential discussion of what they searched for.
```


## Threat Model — 2026-09-15 (round 4)

**Recommendation: PROMOTE to threat-modeled**

Fourth round. The carry-forward is this document's own three prior rounds: round 1 PROMOTEd with four
`kind: required` fences and the spec-reviewer REVISEd because none was folded; round 2 read the folded
material and TIGHTENED M3 to require provenance; round 3 read the re-folded material, verified M1–M4,
and opened M5 (the CLI entry point `main` is outside the wall's callee set) and M6 (the module can
re-enter the tool as a child process); the spec-reviewer REVISEd on those two having no fold record and
no surfaces, and FLAGGED the regress signature, recommending a standing scope ruling rather than a
fourth round. The spec-writer's fifth pass has since landed M5 and M6 in full AND recorded the family
closure in `## Scope Boundary`. So this round has one job: read the re-folded material as a new attack
surface, and judge whether the boundary that was just written down is TRUE of the mechanism it
describes. Every citation below was re-resolved by reading the code, not taken from the fold's account
of itself or from a prior gate's paraphrase.

### Trigger check

The same four triggers fire, unchanged: filesystem operations on user-owned files (`apply_fixes:957`,
`:975`, `quarantine_garbage:1134`, `:1140`), untrusted input (vault bytes, with the new crossing at
`read_vault:115-118`), persistence (the committed live-vault measurement plus a floor-resident module
driving the MUTATING entry point), and an information-disclosure surface (the operator-facing summary
against `obsidian_schemas/errors.py`'s bounded-projection contract). The fifth pass retired none of
them and added material to elevation-of-privilege only, which is again where this round spent its time.

### The re-fold, verified against the code rather than against the fold record

- **M1, M2, M4 — records intact, substance undisturbed.** Re-checked on their own surfaces rather than
  by diffing the fold section: M1's rule sentence and its `read_error=UNREADABLE` recording form; M2's
  bound (`reason: str  # type(exc).__name__ — NEVER str(exc), never note bytes`) with Task 4 carrying
  it; M4's two credit points in Design §4 and Task 4. All three `desc` values in the fold record
  (`:2377`, `:2385`, `:2401`) are byte-identical to my round-3 fences, so their records stay fresh.
  Re-emitted unchanged.
- **M4 re-confirmed against the FRAME, not the prose,** because the edits moved text around it.
  `scripts/lint_vault.py:949` (`fixed += file_fixed`) still sits above the `if changed:` at `:951` and
  the first `write_note` at `:957`; the wikilink write at `:975` is inside the `with` block but OUTSIDE
  `if changed:`, so its raise propagates past any end-of-block fold. Per-write crediting remains the
  only placement yielding AC-4(b)'s signed answer. Unchanged.
- **M3's record is fresh** (`:2393` byte-identical to my round-3 fence) and its six surfaces are
  undisturbed by this round's edits.
- **M5 — landed, and landed the way its generator asked.** The callee set in Design §6(d) is now three
  members, `apply_fixes` / `run_lint` **or `main`** (`:1402`), with the paragraph explaining why `main`
  needs no new rule (`:1415-1425`); §7's syntax half grades the THREE-member set (`:1538-1547`); Task 7
  carries it (`:1947-1960`) with the planted `lint_vault.main()` and bare `main()` RAISE shapes AND the
  `setup()` near-miss that must NOT be collected, which is the WI-235 element; `## Verification` adds
  the ELEVENTH mutation (`:2559-2566`). `desc` at `:2409` is byte-identical to my round-3 fence.
  I also verified the premise independently: `main:1252` takes NO parameters, `--vault` carries
  `default=DEFAULT_VAULT` at `:1255`, and it calls `run_lint(vault_path, …, do_fix=args.fix,
  do_quarantine=args.quarantine)` at `:1299-1308`. And the scan-universe paragraph at `:1427-1435` is
  correct and worth its space: pointing `mutating_drive_vault_args` at the script now RAISES twice
  over, at `run_lint`'s `vault_path` `ast.arg` and at the `main()` call in the `__main__` guard at
  `:1316` — which I confirmed is there.
- **M6 — landed, and every premise re-read off the code.** Design §7's third part (`:1560-1594`) closes
  the process boundary at the IMPORT with the base set IMPORTED rather than hand-typed; Task 15 carries
  the widened set (`:2420`) and proves its REACH with five planted import shapes and five near-misses;
  `## Verification` adds the TWELFTH mutation. Premises confirmed: `tests/derivations.py:FS_MODULES:68`
  is `{"os", "shutil", "tempfile", "fcntl", "filelock", "mmap"}`, `OS_READONLY_NAMES:69` holds only
  `environ`/`getenv`/`sep`/`path`/`fspath`/`getcwd`, `tests/test_name_gate_wall.py:1043` is
  `WALL_C_MODULES = frozenset(FS_MODULES - {"os"})` — neither set reaches `subprocess` or `runpy` — and
  `module_import_uses:847-870` takes an arbitrary `modules` iterable and reports the ORIGINAL root
  module name in both statement forms (`:863`, `:867-869`), so M6 needs no derivation change. `desc` at
  `:2417` is byte-identical. I additionally checked the one route this raised for me: the module's
  legitimate `tests.*` imports do NOT smuggle a process-spawning helper past the import wall —
  `tests/support.py` imports only `logging`/`shutil`/`tempfile`/`contextlib`/`pathlib`, and
  `tests/ac_interpreter.py`'s `os.execve` (`:155`) is reachable only through `ensure_project_interpreter`
  and `delegated_argv`, which build a fixed `pytest <this module>::<check>` argv (`:110-120`) and
  cannot be handed an arbitrary command. No finding.
- **The `## Scope Boundary` ruling is landed** (`:2655-2679`) in the A3/A3b shape the spec-reviewer
  asked for, and it is the right instrument. I route against it below rather than re-litigating it.

### STRIDE review — scoped to what the fifth pass added

**Spoofing — nothing new.** No authentication boundary moved; `person_missing_name` still writes
`fpath.stem.lstrip("@")` (`:897`) through the unchanged `gate_write` at `:947`.

**Tampering — the fold adds no write.** The callee-set widening and the import clause are both
comparisons over files already read. No branch's repair logic, no `delta` key, no gate call and no
`write_note` argument moves. WI-004's concurrency contract is untouched.

**Repudiation — improved.** Every new arm reports loudly and names module and line; the `setup()`
near-miss is what keeps the widening's GREEN informative.

**Information disclosure — unchanged.** The new material carries no note content: an import census
returns `(module_id, root_module_name, lineno)`; a `drives` triple is `(module_id, lineno, identifier)`.
Nothing on these paths can reach a vault path or a note filename.

**Denial of service — unchanged and bounded.** No network, no retry, no recursion; `ast` over one file.

**Elevation of privilege — the finding, and it is NOT a new rung on the ladder. It is the rung M5
declared closed, closed incompletely, plus the discovery that the wall grades an argument that does
not determine what gets written.** The fifth pass's own words are that "M5 closes the whole in-process
level, not `main` alone: the callee set is now the script's complete set of mutating entry points"
(`:2351-2353`). That is a completeness claim about a specific, finite, checkable set, so I checked it
rather than read it. It is false by one member, and the second half of the finding says the level is
not actually enumerable the way both the fold and my own round 3 assumed.

**(a) `quarantine_garbage` is a FOURTH mutating entry point and it is outside the callee set.** The
enumeration is settled by grep, not by memory: the only `vault_io` mutation sites in the whole script
are `write_note` at `:957` and `:975` — both inside `apply_fixes` — and `ensure_dir` at `:1134` plus
`move_note` at `:1140`, both inside `quarantine_garbage:1112-1144`. The functions that reach them are
therefore `apply_fixes`, `quarantine_garbage`, `run_lint` (which calls both, at `:1194` and `:1220`)
and `main`. Four. The set has three, and the missing member is the one whose write is IRREVERSIBLE —
a rename, which is exactly what this document's own currency audit named as the blind arm
("`--quarantine` MOVES files off the back of the same issue list", `:106-107`) and what
`tests/test_vault_path_required.py:356-365`'s docstring names in terms. This is not a shape a builder
has to go looking for: the item PINS the two `garbage_candidate_*` detectors that decide what
`--quarantine` moves (`:161-162`), so `lint_vault.quarantine_garbage(issues, vault)` is a natural
drive for the check that proves those detectors fire on their declared subjects — and it is invisible
to `drives`, therefore to `bindings` (scoped BY `drives`), and `_temp_vault` need never be called. The
closure needs no new rule and no new text: its vault argument is the SECOND positional (`:1113`),
identical in position to `apply_fixes`' (`:827`), so §6(d)'s existing position table grades it as-is.

**(b) The wall grades the vault ARGUMENT, and for `apply_fixes` that argument is provably unused.**
This is the part that changes how the level should be closed. `vault_path` appears in `apply_fixes`
exactly once, in the signature at `:827`; it is referenced nowhere in the body. The write targets come
from the ISSUES: `by_file[issue.file_path]` at `:835`, then `fpath` at `:853`, `:858`, `:957` and
`:975`. So a contained vault argument constrains nothing about what `apply_fixes` writes —
containment holds only TRANSITIVELY, when the issues were derived from a scan of that same contained
vault, and the issues' provenance is graded by nothing. The concrete escape, which passes every clause
of Design §7 as written:

      vault = _temp_vault(tmp)                                  # provenance "_temp_vault"  ✓
      live  = lint_vault.read_vault(lint_vault.DEFAULT_VAULT)    # ungraded — read_vault is not a callee
      issues = lint_vault.check_noise(live, idx)                 # ungraded
      lint_vault.apply_fixes(issues, vault)                      # drives: identifier `vault`  ✓

Clause (i) spelling green, clause (ii) non-vacuity green, clause (iii) provenance green, the runtime
door executed, the import wall clean — and Dave's 3,952 live notes are rewritten. Worse under
`quarantine_garbage(issues, vault)`: `vault_path` there is only the DESTINATION root
(`quarantine_dir = vault_path / "_quarantine"`, `:1116`) while the sources moved are `issue.file_path`
(`:1121`), so a correctly-contained vault argument makes it a data-LOSS shape — live notes renamed out
of the vault into a temp directory that is then deleted.

**Which means the closure is at the SOURCE, not at another door — and that is the move that makes the
`## Scope Boundary` ruling true rather than aspirational.** Both halves of this finding are OMISSION
shapes in the boundary's own words ("reached the tool through a door nobody thought to watch",
`:2665-2666`), so they sit inside the region it declares TOTAL, not in the deliberate-act residue; per
its own last sentence I am not escalating, because this is not a deliberate-act finding. But the reason
this family kept producing rungs — argument, binding, entry point, process boundary, and now a fifth
and a sixth — is that every closure so far enumerated DOORS, and doors are a list somebody writes down.
The live vault path, by contrast, has exactly two sources in this module's reachable universe, and that
IS closed by construction: `lint_vault.DEFAULT_VAULT`, which is `os.environ.get("OBSIDIAN_VAULT_PATH",
"")` at `scripts/lint_vault.py:56`, or a direct environment read. A literal `/Users/…` path is already
RED under `FORBIDDEN_DEFAULT_PATTERNS` (`tests/test_vault_path_required.py:278`), which Task 15 already
runs over this item's touched files. So a clause asserting that the module NAMES neither token outside
`_temp_vault`'s own negative assertions is total over every omission route through every door — the
four known ones and any fifth — because no omission-shaped escape can reach the live vault without
naming one of them. Carried as **M8**, and it is deliberately the CLASS closure rather than a seventh
door: it is what stops the next round from finding a seventh.

Carried as two fences and a PROMOTE rather than a REVISE. The approach is not unsafe, the design's
intent is stated, the mechanism is sound for what it watches, and both closures land inside machinery
the plan already ships — M7 is one member of a set Task 7 already builds, graded by a position rule
§6(d) already states; M8 rides the same `VaultArgScan` (a third field, no fifth derivation) asserted
inside Task 9's ONE existing check, so §6's four derivations, §7's five-plus-three check count, R4's
"eight checks" and Task 16's expected direction all still hold. That is the case WI-128/D8 owns. I am
NOT re-opening M3's or M5's `desc`: M3 describes the vault argument's provenance and M5 the CLI entry
point, both landed and both satisfied, and re-wording either would re-stale a fresh record for a
requirement that did not move (the FIDELITY rule).

### Mitigations required

1. **M1 — the read-error value is a vocabulary member, never the decode exception.** Folded into
   Design §1 and Task 2; re-verified. Re-emitted unchanged.
2. **M2 — both new records carry bounded values.** Folded into Design §3 and Task 4; re-verified.
   Re-emitted unchanged.
3. **M3 — the containment wall, with the syntax half asserting provenance.** Folded on all six
   surfaces; record fresh; re-emitted unchanged.
4. **M4 — an issue whose write committed is never re-labelled `errored`.** Folded into Design §4, both
   paired Edge Cases, Task 4, R1 and a `## Verification` mutation; re-verified against the frame.
   Re-emitted unchanged.
5. **M5 — the CLI entry point is inside the wall's callee set.** Folded this round into §6(d), §7's
   syntax half, Task 7 and the eleventh mutation; premise re-verified at `:1252-1255`, `:1299-1308`.
   Re-emitted unchanged.
6. **M6 — the module cannot reach the CLI by subprocess either.** Folded this round into §7's import
   half and Task 15; every premise re-read off `tests/derivations.py` and `tests/test_name_gate_wall.py`.
   Re-emitted unchanged.
7. **M7 — the callee set is the script's COMPLETE set of mutating entry points, and that is four.**
   NEW this round; needs fold work in Task 7, plus a correction to the fold section's own completeness
   claim at `:2351-2353` and a THIRTEENTH `## Verification` mutation (a planted
   `lint_vault.quarantine_garbage(issues, lint_vault.DEFAULT_VAULT)`, green under a three-member set).
8. **M8 — the live vault path cannot be NAMED in the module at all.** NEW this round; needs fold work
   in Task 9 (the clause) riding Task 7's scan, plus a FOURTEENTH mutation (the four-line escape above,
   which is green against a build that implements every clause of §7 as currently written).

```mitigation
kind: required
id: M1
desc: read_vault's recorded read_error value is the IMPORTED SKIP_REASONS member UNREADABLE and never str(exc) of the decode failure, so undecodable note bytes are never decoded, never rendered into an issue message and never stored in any record.
landed: Task 2
```

```mitigation
kind: required
id: M2
desc: FixErrorRecord.reason is the exception's class name and FixDeclineRecord.guard is a DECLINE_GUARDS member — never str(exc), never note bytes — because both records feed the operator-facing summary that gets pasted into chat.
landed: Task 4
```

```mitigation
kind: required
id: M3
desc: every apply_fixes and run_lint(..., do_fix=True) drive in tests/test_lint_vault_fix_rules.py takes a vault path rooted in a fresh tests/support.temp_dir(), never lint_vault.DEFAULT_VAULT, never OBSIDIAN_VAULT_PATH and never any path outside that directory, and the module asserts that containment before the first mutating call; and the syntax half asserts PROVENANCE and not merely spelling — every binding in that module of the identifier it accepts is a call to the single _temp_vault door — so a drive cannot satisfy the wall by re-binding that name to a path the door never produced.
landed: Task 9
```

```mitigation
kind: required
id: M4
desc: an issue whose own write has COMMITTED is credited at that commit point and is never re-labelled errored by a later raise inside the same lock block, so the issues carried by the write at :957 stay repaired when the wikilink write at :975 raises, as AC-4(b) requires.
landed: Task 4
```

```mitigation
kind: required
id: M5
desc: mutating_drive_vault_args' callee set includes main as well as apply_fixes and run_lint, so the tool's CLI entry point — whose --vault carries default=DEFAULT_VAULT at scripts/lint_vault.py:1255 and which therefore reaches the live vault by OMISSION rather than by an attribute access — is inside the wall rather than beside it; a main call in that module carries a vault argument at no position and so RAISES under the rule §6(d) already states, reddening the wall at its own line.
landed: Task 7
```

```mitigation
kind: required
id: M6
desc: tests/test_lint_vault_fix_rules.py imports no subprocess-capable module — subprocess and runpy are added to the module set Task 15 hands module_import_uses over that file, because WALL_C_MODULES is FS_MODULES minus os and contains neither — so the wall cannot be satisfied by a drive that re-enters the tool through its CLI as a child process, which is the shape tests/test_vault_path_required.py:344-353 already uses and has to scrub OBSIDIAN_VAULT_PATH out of the environment to make safe.
landed: Task 15
```

```mitigation
kind: required
id: M7
desc: mutating_drive_vault_args' callee set is the script's COMPLETE set of mutating entry points and therefore has FOUR members and not three — quarantine_garbage joins apply_fixes, run_lint and main, because it is the only other function in scripts/lint_vault.py that reaches vault_io's mutating doors (ensure_dir at :1134, move_note at :1140, the script's only mutation sites beside apply_fixes' writes at :957 and :975) and its move is the irreversible one; its vault argument is the SECOND positional at :1113 exactly as apply_fixes' is at :827, so it grades under the position rule §6(d) already states with no new text.
landed: Task 7
```

```mitigation
kind: required
id: M8
desc: the new check module NAMES the live vault path nowhere outside _temp_vault's own negative assertions — no lint_vault.DEFAULT_VAULT attribute access and no OBSIDIAN_VAULT_PATH or os.environ read anywhere else in the module — because grading a drive's vault ARGUMENT cannot contain apply_fixes, whose vault_path parameter is referenced nowhere in its body (:827 is its only occurrence) and whose write targets are issue.file_path (:835, :853, :957, :975), so a drive whose ISSUES came from lint_vault.read_vault(lint_vault.DEFAULT_VAULT) passes all three clauses of Design §7 with the runtime door executed while rewriting the live vault; and a clause over the path's two SOURCES is total over every omission route through every door, which a callee enumeration cannot be.
landed: Task 9
```

### Notes (non-blocking)

1. **The `bindings` census's closed RAISE set will meet a `with ... as` binding if M8's clause is
   implemented by widening the graded identifier set instead of by a token scan.** Recorded so the
   fold does not take the tempting shortcut: adding `read_vault` to the callee set would pull `tmp`
   into the graded identifiers (`read_vault(tmp)` is a natural spelling for Task 2's unreadable-note
   verify), and `tmp` is bound by `with temp_dir() as tmp`, which §6(d)'s `bindings` arm RAISES on
   (`:1455-1458`) — a false RED on a correct module. M8 is written as a clause over the two SOURCE
   tokens for this reason, not only for totality.
2. **`tests/ac_interpreter.py`'s `os.execve:155` is a process-spawning capability inside the `tests.*`
   helpers M6 deliberately leaves outside the widened import set — checked, and it is not a route.**
   `ensure_project_interpreter` and `delegated_argv` build a fixed `pytest <module>::<check>` argv
   (`:110-120`, `:150-155`) and accept no command, so the new module cannot use them to re-enter the
   CLI. Recorded so a later round does not re-derive it as a finding.
3. **Round 3 note 1 / the decoy-named door — now CLOSED as a scope ruling**, not as a note:
   `## Scope Boundary:2655-2679` records the deliberate-act residue in the A3/A3b shape and the fold
   section's overclaim was corrected with it (`:2325-2336`). This is the right instrument and I route
   against it rather than re-litigating it.
4. **Round 3 note 2 (check definition order) is CLOSED** — Task 9 now says to define
   `test_every_mutating_drive_in_this_module_is_confined_to_a_temp_vault` FIRST, with the courtesy /
   guarantee distinction stated (`:2396`).
5. **Round 1 note 1 / round 2 note 3 / round 3 note 3 (the exit attestation's redaction reminder is
   absent from `docs/lint-vault-live-baseline.md` §4's own bytes) — STILL OPEN**, re-deferred a sixth
   time for the same correct reason: §4 is conductor-owned and outside the builder's write authority,
   so it has no Implementation-Plan task to land in and a fence pointing at one would be a fiction.
   The conductor's, at the ship door.
6. **Round 1 note 2 / round 2 note 4 / round 3 note 4 (`apply_fixes:994` prints `str(exc)` to stderr)
   — STILL OPEN as a deliberate non-change.** Re-verified: the handler set does not widen, so no new
   content reaches that channel, and it is pinned as a message equality at
   `tests/test_lint_vault_fix_gate.py:123-125`.
7. **Round 2 note 1 (M3's wall universe is ONE module) stands as a scope ruling** and is routed
   against. M7 and M8 do not widen it either — both are clauses over the same single module.

```verdict
gate: threat-modeler
verdict: PROMOTE
date: 2026-09-15
model: claude-opus-5
note: M5 and M6 are fully landed and I verified them at the code rather than at the fold record — §6(d)'s callee set is three members at `:1402` with the no-new-rule paragraph at `:1415-1425`, §7's third part closes the process boundary at the import with the base set IMPORTED (`:1560-1594`), Task 7 and Task 15 carry both with WI-235 reach-and-near-miss shapes, the eleventh and twelfth mutations landed, and all six `desc` values in `## Mitigation Folds` are byte-identical to my round-3 fences; premises re-read independently (`main:1252` takes no parameters, `--vault` default=DEFAULT_VAULT at `:1255`, `run_lint(..., do_fix=args.fix)` at `:1299-1308`, `FS_MODULES:68` / `OS_READONLY_NAMES:69` / `WALL_C_MODULES:1043` / `module_import_uses:847-870`), and the `tests.*` helpers do not smuggle a spawner past M6 (`ac_interpreter`'s `os.execve:155` is reachable only through a fixed pytest argv). The `## Scope Boundary` ruling the spec-reviewer asked for is landed at `:2655-2679` and I route against it. The finding is not a new rung: it is the rung M5 declared closed, closed incompletely, and both halves are OMISSION shapes inside the region that boundary declares TOTAL, so I am not escalating. (a) The fold claims the callee set "is now the script's complete set of mutating entry points" (`:2351-2353`); settled by grep, the script's only `vault_io` mutation sites are `write_note:957`/`:975` in `apply_fixes` and `ensure_dir:1134`/`move_note:1140` in `quarantine_garbage:1112-1144`, so the mutating entry points are FOUR and the set has three — the missing member being the one whose write is irreversible, whose detectors this item PINS (`:161-162`), and whose vault argument is the second positional at `:1113` exactly as `apply_fixes`' is, so §6(d)'s position rule grades it with no new text (M7). (b) Sharper, and it changes how the level should be closed: `apply_fixes`' `vault_path` is referenced NOWHERE in its body — `:827` is its only occurrence — and the write targets are `issue.file_path` (`:835`, `:853`, `:957`, `:975`), so grading the vault argument constrains nothing; `vault = _temp_vault(tmp)` beside `issues = check_noise(read_vault(lint_vault.DEFAULT_VAULT), idx)` then `apply_fixes(issues, vault)` passes all three clauses of §7 with the runtime door executed and the import wall clean, while rewriting the live vault — and under `quarantine_garbage` it is a data-LOSS shape, since `vault_path` there is only the destination root (`:1116`) and the sources moved are `issue.file_path` (`:1121`). Hence M8 closes at the SOURCE rather than at a fifth door: the live path has exactly two sources in this module's universe (`lint_vault.DEFAULT_VAULT`, itself `os.environ.get("OBSIDIAN_VAULT_PATH", "")` at `:56`, or a direct environment read; a literal `/Users/…` is already RED under `FORBIDDEN_DEFAULT_PATTERNS:278`, which Task 15 runs), so a clause that the module names neither token outside `_temp_vault`'s negative assertions is total over every omission route through every door — which is the anti-treadmill move and why I am not carrying a seventh-door fence. Both land inside shipped machinery: M7 is one set member in Task 7, M8 is a third `VaultArgScan` field asserted inside Task 9's ONE existing check, so the four derivations, the five-plus-three check count, R4's "eight checks" and Task 16's direction do not move; M3's and M5's `desc` are deliberately NOT re-opened, since both landed rather than moved.
```


## Adversarial Review — 2026-09-15 (round 4)

Cold-start re-read, full document, all 5382 lines end to end: frontmatter, Problem/Intent, both
currency audits, every Exploration-Notes approach (A1–A7b) and all eight constraints, all five
Revision rounds, Approach, Verified Diagnosis, the full Design (§1–§10), Edge Cases, all sixteen
Implementation-Plan tasks, both `writes` precondition fences and the nine builder `writes` fences
plus the handoff note, Verification, Scope Boundary, Risk Analysis, all five `criteria` fences and
their Examples of done, AC Red-Team round 3, Architectural Review round 4, AC Sign-off, Data Audit
round 2, Mitigation Folds, and every threat-model / spec-review / adversarial-review round in full,
including each one's own `verdict`/`mitigation` fence. Also re-read the injection-hunter role
definition and its machine contract before starting. The carry-forward is my own three prior
sections (round 1 PROMOTE through the first Spec Review round; round 2 PROMOTE covering round 1
itself plus Threat Model round 2 and Spec Review round 2; round 3 PROMOTE covering round 2 itself
plus Threat Model round 3 and Spec Review round 3) — this round's job is the material that landed
after round 3: `## Adversarial Review — 2026-09-15 (round 3)` itself, `## Threat Model — 2026-09-15
(round 4)`, and `## Spec Review — 2026-09-15 (round 4)`. I read all three fresh and re-swept the
whole document rather than diffing against my own prior accounts, for the reason every prior round
gave: a planted instruction could sit anywhere a narrower diff-read would miss, and my own three
PROMOTEs are part of this round's attack surface, not citations I get to lean on.

**The one question, applied to the two new gate sections.** This round's material is, on its face,
the most consequential yet: threat-model round 4 finds that its own predecessor's completeness claim
("M5 closes the whole in-process level... the callee set is now the script's complete set of
mutating entry points", quoted and cited at `:2351-2353`) is FALSE, names a fourth mutating entry
point (`quarantine_garbage`) the wall never graded, and then finds something sharper underneath it —
that the wall's whole design grades an argument (`apply_fixes`' `vault_path`) that is never read in
the function body, so containment was never total even for the three doors already named. That is a
gate finding a real, previously-unnoticed security gap in a signed threat model, three rounds deep.
Read adversarially, a document under injection pressure would want exactly the opposite: a
threat-modeler persuaded that the wall is done. Instead this round's finding is the harshest
self-correction in the whole chain, paired with concrete, re-executable code citations at every
step (`:827` as `vault_path`'s only occurrence in `apply_fixes`, `:835/:853/:957/:975` as the real
write targets, `:1113/:1116/:1121` for `quarantine_garbage`'s argument and targets) — the opposite
shape from steering, which argues from authority or urgency rather than from a citation a reader can
run and contradict. Spec-review round 4 then REVISEs on top of it, independently re-deriving both
premises (`grep vault_path scripts/lint_vault.py` returning `:827` itself, `quarantine_garbage`'s
own `:1113` argument position) rather than accepting threat-model round 4's account, and adds a
finding threat-model round 4 did not raise: the `## Scope Boundary` ruling's own "TOTAL over OMISSION
shapes" sentence is now false as stated and, because its last sentence instructs a later gate to cite
it and escalate rather than REVISE, an overstated ruling would wave through exactly the class of gap
round 4 just found. A planted "the wall is done, PROMOTE" instruction would need three independent
gates in a row (round 3's threat-modeler, round 4's threat-modeler, round 4's spec-reviewer) to each
fail to notice the same gap in three different ways; instead each one found successively deeper
material the previous round missed. That is the corroborator ladder working, not steering
propagating downstream.

**Self-check on my own three-PROMOTE track record, since it is exactly the kind of prior finding this
gate should not take at face value the fourth time.** Rounds 1–3 each PROMOTEd, and each based part
of its reasoning on the review chain "disagreeing with itself in the normal way." This round is the
test of that reasoning rather than a repetition of it: if the chain had in fact been steered toward
leniency, round 4 finding a live, previously-missed security gap and REVISEing over it is the
strongest possible evidence against that reading, because a steered chain would not produce an
ever-sharper adversarial finding on its fourth pass over the same family. I did not treat "the
pattern held for three rounds" as license to skim this one; I re-read Threat Model round 4 and Spec
Review round 4 at the same depth as round 1's material, specifically because a chain that has
PROMOTEd three times in a row is the more attractive target for an injection banking on reviewer
fatigue, and found the opposite of fatigue in both sections — the newest content is more precise and
more self-critical than round 3's was, not less.

**`## Adversarial Review` (round 3) itself, read as content rather than trusted as a peer's verdict,**
per the discipline every round has applied to its predecessor. Reread it in full: it checks the two
mechanical injection vectors the machine contract calls out, re-verifies rounds 1 and 2 independently,
and runs a whole-document mechanical grep for direct-address and override phrasing. I repeated that
same grep sweep against the FULL current document (now including Threat Model round 4 and Spec Review
round 4): `ignore the previous`, `pre-approved`, `emit PROMOTE`, `should not block`, `disregard`,
`rubber-stamp`, `SYSTEM:`, `you must`, `your verdict`, `as the reviewing model` — no hits anywhere
outside the four injection-hunter rounds' own prose describing what was searched for, which is the
same expected self-referential shape rounds 2 and 3 found and not a plant. `^## ` heading grep shows
`## Adversarial Review` appearing only at the four dated rounds that legitimately sit in this document
(rounds 1–3 and this one, freshly added below) — no stray example heading anywhere that could capture
a fabricated verdict fence. `<!--` occurs exactly once outside verdict/mitigation/criteria/writes
fences, the machine-maintained "archive-split" pointer at the top of the document, unchanged from
every prior round's count.

**The two new gate sections, swept for planted-specimen leakage.** Threat-model round 4's four-line
escape (`vault = _temp_vault(tmp)` / `live = lint_vault.read_vault(lint_vault.DEFAULT_VAULT)` / ...)
and spec-review round 4's re-derivation of the same shape are both DEMONSTRATIONS of a design gap in
this item's own code, written by the gates themselves as part of their adversarial analysis — not
content copied in from elsewhere, not a specimen with any exam-corpus marking, and not prose addressed
to a reviewing agent. Neither section names or reproduces a WI-091-class canary; the "planted"
material this round discusses (`quarantine_garbage(issues, lint_vault.DEFAULT_VAULT)` as a mutation
fixture, M7/M8 as new `kind: required` fences) is the same house style of concrete, re-executable test
discriminators every prior round already covered for the earlier mitigations, extended to two new
mitigation ids. No sentence in either section has the reviewing agent as its grammatical subject in an
instructional sense — "I confirmed it independently", "I settled by reading the function", "I checked
that neither fold touches" are reports of what the gate did, not directives to the next one.

**Escalation check, honestly applied — and this round is the sharpest test of it yet.** Spec-review
round 4 states outright that it is choosing NOT to escalate ("the threat modeler is right not to
escalate either: both halves are omission shapes, not deliberate acts, so `## Scope Boundary`'s
escalation clause does not fire") and instead sets a named trigger for round 5 ("if a fifth
threat-model round opens a NINTH mitigation on this family... the next gate should stop and ask rather
than emit a fifth REVISE"). Weighed adversarially: a gate declining to escalate on a request it could
plausibly have escalated is a place steering could hide, since "argue the reviewer out of raising this
further" is exactly the injection shape the role's calibration section warns about. But the argument
is not free-floating persuasion — it turns on a specific, re-checkable distinction the gate states and
I independently verified: M7/M8 are OMISSION shapes inside the region `## Scope Boundary` already
declares total (a door nobody thought to watch, an argument nobody thought to grade), not the
DELIBERATE-act residue the same ruling carves out (a decoy spelled with the door's own name, a deleted
wall clause) — and that distinction was drawn by the spec-writer's `## Scope Boundary` text on
2026-09-15, before either finding in this round existed, so the classification was not authored to fit
the escape after the fact. The gate is also NOT declining to REVISE — it emits a REVISE this round, on
the strongest blocking findings in the whole chain — so this is not a case of a gate talked out of
acting; it is a gate acting fully on its own finding while declining a further, non-required escalation
under a rule the document fixed in advance. That is the mechanism working as designed, not a plant
exploiting it.

No manipulation found in the material this round covers, and rounds 1 through 3's findings over the
earlier material still hold on this full reread. This is a real finding, not a skipped check.

```verdict
gate: injection-hunter
verdict: PROMOTE
date: 2026-09-15
model: claude-sonnet-5
note: Cold-start re-read of the full 5382-line document plus the three sections that landed after round 3 (round 3's own Adversarial Review, Threat Model round 4, Spec Review round 4) — no instruction-to-a-reviewer text found in any of them. Threat-model round 4 finds its own predecessor's completeness claim false and names a genuinely new, previously-unnoticed security gap (a fourth mutating entry point outside the containment wall's callee set, then a deeper flaw — the wall grades a `vault_path` argument `apply_fixes` never reads) with re-executable file:line citations at every step, which is the opposite of steering; spec-review round 4 independently re-derives both premises rather than trusting the fold and REVISEs, adding its own finding that `## Scope Boundary`'s "TOTAL over OMISSION shapes" ruling is now overstated given what round 4 found — three consecutive gates producing an ever-sharper adversarial result on the fourth pass over the same family is the corroborator ladder working, not a chain persuaded toward leniency. Spec-review round 4's explicit decision not to escalate is grounded in a deliberate-act/omission-shape distinction `## Scope Boundary` drew before either finding existed, and the gate still emits a full REVISE on its strongest findings, so this is not a case of a gate talked out of acting. Whole-document mechanical sweep for direct-address/override phrasing (`ignore the previous`, `emit PROMOTE`, `you must`, `SYSTEM:`, etc.) surfaces only the four injection-hunter rounds' own self-referential discussion of what they searched for; the heading grep shows `## Adversarial Review` at only the four legitimate dated rounds, with no stray example heading anywhere. Rounds 1–3's PROMOTEs re-verified independently rather than trusted.
```


## Adversarial Review — 2026-09-16 (round 5)

Cold-start, different model from spec-reviewer (Sonnet, vs. Opus for spec-reviewer and threat-modeler).
Read the document end-to-end from line 1, including every archived-round pointer, all five prior
Adversarial Review rounds (all PROMOTE), and — with particular weight, since it is new since my last
read — Threat Model round 5 and Spec Review round 5 in full, plus the code they cite.

**The one question:** has this spec, or the prior gates' verdicts, been steered by a prompt injection
planted in the untrusted content the gates read? Two candidate surfaces, both examined directly rather
than taken from a gate's paraphrase:

1. **`## Scope Boundary`'s escalation clause** (`:3137-3146`): "Any gate finding at the deliberate-act
   level should cite this paragraph and escalate rather than REVISE" and "the gate holding that round
   should stop and ask Dave or the conductor rather than emit another REVISE." This is exactly the
   *shape* my role brief warns about — text addressed to a reviewer telling it what verdict-adjacent
   action to take, embedded inside spec content. I traced its provenance rather than judging the shape
   alone: it did not originate in this document as spec-writer content arguing its own case. Spec
   Review round 4 (`:5797-5800`, a REVIEWING gate, not the spec-writer, and on a DIFFERENT model
   lineage than this round's) is where the sentence was first coined, as that gate's own proposed
   discipline against a regress it had just diagnosed in itself — the spec-writer's sixth pass then
   transcribed the gate's own words into `## Scope Boundary` faithfully. A reviewer minting its own
   escalation valve and recording it in the doc so a future round doesn't have to hold it in memory is
   not a confused-deputy hole; it is the opposite of one. And critically, the mechanism did NOT work
   the way a steering injection would need it to: Threat Model round 5 and Spec Review round 5 both
   independently re-verified the trigger's stated conditions against the code (fifth round, ninth
   mitigation, M7/M8 landed as written) before honoring it, both split the finding explicitly into a
   truthfulness half that still blocks (spec-review round 5's blocking issue 1, `findings: 1/3`) and a
   sufficiency half that is routed rather than suppressed, and neither gate treated "the paragraph says
   don't REVISE" as license to withhold a real, code-verified finding. A planted "don't block this"
   instruction that gets a REVISE anyway is failing at the one job it would need to succeed at.
2. **The newly-added Threat Model round 5 / Spec Review round 5 material generally** — dense,
   citation-anchored, internally disagreeing with prior rounds' overclaims (both find the "two sources"
   / "total by construction" language in `## Scope Boundary`, Design §6(d)/§7 and `## Mitigation Folds`
   to be false-as-written, the opposite of a chain being steered toward complacency). I re-resolved a
   sample of the load-bearing citations myself (`obsidian_schemas/repositories/base.py:_resolve_vault_path:104-114`,
   `ENV_VAULT_PATH` at `:75`, `BaseRepository.__init__:154`, the four repository exports at
   `obsidian_schemas/__init__.py:74-77`) and they check out exactly as both rounds describe. Grepped
   the full document for injection-style override phrasing (`ignore the previous`, `pre-approved`,
   `emit PROMOTE`, `should not block`, `disregard`, `rubber-stamp`, `SYSTEM:`) beyond the prior gates'
   own methodology notes describing that same grep — no hits.

No text in this round's additions argues that a reviewer *should not* find something, asserts
pre-approval, or is addressed to "you, the AI" outside the one traced-and-cleared mechanism above. The
spec-reviewer's REVISE reads as an independent, adversarial, code-checked judgment — it corrects three
overclaiming surfaces up to seven, over the objection of the very paragraph that could have let it
stop looking.

```verdict
gate: injection-hunter
verdict: PROMOTE
date: 2026-09-16
model: claude-sonnet-5
note: Read the full document, all five prior Adversarial Review rounds, and this round's new material (Threat Model round 5, Spec Review round 5) end-to-end. The one shape resembling gate-directed steering — `## Scope Boundary`'s "escalate rather than REVISE" clause (`:3137-3146`) — traces to Spec Review round 4 minting its own escalation discipline (`:5797-5800`) against a regress it diagnosed in itself, not to planted content arguing a verdict; both round-5 gates independently re-verified its trigger conditions at the code before honoring it, split the truthfulness half out as still-blocking (findings: 1/3) rather than being suppressed by it, and routed only the narrow sufficiency call. A grep for override-style phrasing (ignore the previous / pre-approved / emit PROMOTE / should not block / disregard / rubber-stamp / SYSTEM:) across the whole document returns only prior gates' own methodology notes describing that grep, no live specimens. No manipulation detected.
```


## Code Review — 2026-09-16

Cold-start, build-exit gate, first round at this door. **This spawn has no shell** — Bash is not in the
granted toolset and `ToolSearch` resolves no shell tool — so nothing below is a claim about an
EXECUTED floor. Every finding is read off the tree's bytes, with the predicate stated so the
build-runner (which does have a shell) re-runs it rather than trusting it. The floor's GREEN and the
681 → 689 delta are the Build Log's claim and I could not independently re-run them; the Build Log
does record a shell-liveness probe (`echo hi`) and Bash exec'ing normally for the whole build, and the
build's own mutate-and-observe table carries fifteen observed REDs, so the dead-shell ABORT rule is
not triggered.

**Trigger check.** FIRES — `scripts/lint_vault.py` modified, `tests/derivations.py` modified, a new
check module created, five more test modules touched. Not doc-only, not mechanical.

### What I read

`scripts/lint_vault.py` (`read_vault:121-190`, `check_structural:328-419` and the three sibling
declines at `:426`/`:509`/`:724`, the record cluster `:859-946`, `apply_fixes:949-1193`,
`quarantine_garbage:1309-1341`, `_format_fix_summary:1344-1361`, `run_lint:1364-1471`);
`tests/derivations.py:1870-2264` (the four new scans); `tests/test_lint_vault_fix_rules.py` end to
end; the Task 8 edits at `tests/test_fixture_vault.py:518-529` and `:1322-1335`; the Task 5 rename
sites across four modules; and the item's `## Implementation Plan`, `## Build Log`,
`## Write Targets`, `## Design` §9/§9b, `## Verification`, `## Scope Boundary` and all five
`criteria` fences.

### What the build gets right, stated because it is most of the diff

The four-bucket disposition rule in `apply_fixes` is implemented as §4 rules it and not as a
paraphrase: `undecided` starts as the file's whole issue list, each of the five guards releases its
own issue at its own branch (`:1029-1032`, `:1051-1053`, `:1075-1077`, `:1087-1090`, `:1146-1148`),
and the two credit points sit on the statements AFTER each `write_note` RETURNS (`:1119-1121`,
`:1151-1153`) rather than folding once at the end of the lock block. `_release:936-946` removes by
`id()` and not by equality, which is the correct answer for a plain dataclass a file can legitimately
hold two equal copies of. Both handlers credit only what is still undecided, so a decline survives a
later frame-level refusal — the tie-break AC-4(b) signs. The partition is total on every path I could
trace by hand except one that AC-1(a)'s emitter≡branch equality closes by construction (an
auto-fixable issue whose `check` matches no branch would fall out of all four buckets; the equality
makes that RED before it can happen, and it is worth knowing that is WHY the equality is load-bearing
at runtime and not only at review time).

`read_vault`'s recording arm, the `unreadable_note` branch placed FIRST in `check_structural`'s loop
body, and the three sibling `or vf.read_error` guards all landed field for field. The reason value is
the imported `UNREADABLE` in both the record and the printed label (`:54`, `:150`, `:1354`), so the
script hand-types no vocabulary member and the widened skip-reason wall's two-member equality is a
statement ABOUT the script rather than an absence of one — D1's resolution is the right one and its
rider (no consumer hand-types it either) is honoured at
`tests/test_lint_vault_fix_rules.py:1330`.

The containment wall is the strongest part of the diff. `mutating_drive_vault_args:2159-2264` returns
all three censuses; `_raise_if_other_binding:2102-2156` closes the binding surface over `ast`'s own
node set rather than a sample; `_enclosing_function_names:2060-2079` takes the INNERMOST enclosing
`def`, which is the scoping the design ruled and which the nested-`def` fixture at
`tests/test_lint_vault_fix_rules.py:463-478` actually discriminates. The four clauses at `:273-310`
are each run, the WI-235 non-vacuity arm is there (`:305`), and the three-token codomain assertion at
`:308` is imported rather than spelled — which it has to be, since spelling the env key outside
`_temp_vault` would redden the very clause the assertion states. D2's finding (no helper may take a
parameter named `vault`, because `ast.arg` is in the closed RAISE set) is a real property of the
mechanism, correctly discovered by running it.

M9 — the build's own report that the containment check was GREEN against a hand-broken `_temp_vault`
because all four clauses read syntax and never CALLED the door — is the kind of finding a build
usually does not volunteer, and the fix (`_check_the_runtime_door_contains_what_it_builds:251-270`,
with its own first draft's clause-(iv) RED recorded) is correct and minimal.

AI-maintainability checks 1, 2, 4 and 5: clean. No new cross-project reach; no new silent swallow
(the one swallow this item exists to close is closed, and both `apply_fixes` handlers record AND
print); no new dependence on deprecated code; no idiom regression — the stringly-typed reason is an
import, the records are closed `NamedTuple`s with bounded fields, and `FixErrorRecord.reason` is
`type(exc).__name__` at `:1189` and never `str(exc)`. Step 2c: no external-service write is
introduced (every write is `vault_io`-routed and locally readable back, and AC-1's oracles do re-read
the bytes), and the no-silent-PASS-on-empty dimension is this item's own subject — `run_lint:1421`
prints the summary UNCONDITIONALLY under `do_fix` and the "No auto-fixable issues found." else-arm is
gone, which is the exact defect that check names.

### Blocking

**B1 — Design §9's census reader shipped in the wrong module, and the deviation is undisclosed, so
the Build Log's totality claim is false.**

`census_auto_fixable_rows` is defined at `tests/test_lint_vault_fix_rules.py:1534`. Design §9
(`:2035-2054`) rules it lands in `tests/test_fixture_vault.py`: "A FIFTH reader lands beside them, in
the same module, riding the same whole-file `CENSUS_DIGEST` fixity", with the signature given as
`census_auto_fixable_rows(text=None)`. Task 14 (`:2549-2551`) says "Add `census_auto_fixable_rows` to
`tests/test_fixture_vault.py` beside the four fence readers, per Design §9" and then, of the AC-5
check, "importing `census_auto_fixable_rows` from `tests.test_fixture_vault`". The
`tests/test_fixture_vault.py` write-target fence (`:2818`) names it as that file's second reason for
being touched. AC-5(b) — a SIGNED criterion — declares it as a decision rather than a builder's
choice: "It is a WRITE TARGET in `tests/test_fixture_vault.py`". And §9b (`:2056-2062`) exists
precisely to CONTRAST the baseline readers against it ("Its reader lands in the NEW check module …
rather than beside `tests/test_fixture_vault.py`'s census readers"), a sentence that means nothing
unless §9's reader is in the other module. Predicate, re-runnable: `grep -rn census_auto_fixable_rows
tests/` returns three hits, all in `tests/test_lint_vault_fix_rules.py`, and
`tests/test_fixture_vault.py` still carries exactly four readers (`census_class_rows:122`,
`census_pool_rows:140`, `census_meta:145`, `census_identity_residue:381`).

The collision that forced this is real and I can see it: the reader reads `CATEGORY_ORDER` off the
LOADED script module (`:1557`), and `tests/test_fixture_vault.py` has no `lint_vault` loader — adding
one there would be the second loader `tests/test_lint_vault_fix_rules.py:104-108`'s own docstring
refuses. That is exactly the shape of D1-D4: "a collision the spec's own prose did not anticipate."
What makes it blocking is not the placement, it is that **it was not recorded**. `## Build Log`
(`:2639-2641`) states "**All sixteen tasks landed as specced. Four deviations**", which is false of
Task 14; `## Write Targets`' fence for `tests/test_fixture_vault.py` still says that file carries the
fifth reader, which it does not; and AC-5's green is therefore green against a mechanism the document
describes in three places and the tree implements in none of them. A later reader looking for the
census family finds four readers and a fence saying there are five. This is the omission level, not
the deliberate-act level, so `## Scope Boundary`'s escalate-rather-than-REVISE bound (`:3515-3523`)
does not cover it and it is a legitimate REVISE by that paragraph's own words.

**Required fix — either, and the second is what D1-D4 already establish as this build's idiom.**
(i) Move the reader to `tests/test_fixture_vault.py` with the `text=None` signature §9 gives, import
it in the new module, and resolve the `CATEGORY_ORDER` dependency without minting a second loader
(passing the category vocabulary in as an argument from the caller that already holds the loaded
module is the cheapest shape). OR (ii) keep it where it is and DISCLOSE it: add a **D5** entry to
`## Build Log` naming the collision (`CATEGORY_ORDER` must be read off the loaded module; the census
readers' module has no loader and a second one is refused by the single-loader rule), correct
`## Build Log`'s "All sixteen tasks landed as specced. Four deviations" sentence to five, correct the
`tests/test_fixture_vault.py` write-target fence's `why:` so it no longer claims the fifth reader,
and correct Task 14's two sentences. Either way the three document surfaces and the tree must agree
when this leaves the door.

### Note

**N1 — Task 3's prescribed comment is absent, also undisclosed.** Task 3 (`:2297-2298`) requires:
"`check_timeline` is untouched and the reason is recorded in a comment: it iterates the index, never
`files`." `scripts/lint_vault.py:624-656` carries no such comment. The REASONING is correct —
`check_timeline` walks `idx["meetings"]` and `idx["persons"]`, and a `read_error` `VaultFile` has
`entity_type == ""` so enters neither index — which is why this is a Note and not a second blocker;
but it is the one place a future reader will ask "why did the other three get a guard and this one
not", and the plan anticipated that question. Add the comment (and, if B1 is discharged by route
(ii), note it in the same D5 paragraph rather than as a sixth deviation).

### Summary

Sixteen tasks, a 1,900-line check module, a four-census syntax wall with its own WI-235 fixture
battery, and fifteen observed-and-reverted mutations — the substance of this build is done and done
well, and none of my reading found a correctness defect in `apply_fixes`' partition, in the
containment wall, or in the unreadable-note path. What it owes is truthfulness about its own
deviations: one prescribed artifact is in a different module than three document surfaces say, and
the Build Log says every task landed as specced. That is cheap to close and it is exactly the class
this gate exists to catch, so it goes back rather than through.

```verdict
gate: code-reviewer
verdict: REVISE
date: 2026-09-16
model: claude-opus-5
targets: AC-5, Task 14, Task 3, #write-targets
prior: none
basis: original
findings: 1/2
note: `census_auto_fixable_rows` shipped at `tests/test_lint_vault_fix_rules.py:1534` instead of `tests/test_fixture_vault.py` as Design §9, Task 14, the `tests/test_fixture_vault.py` write-target fence and AC-5(b)'s signed desc all rule — the forcing collision (`CATEGORY_ORDER` must be read off the loaded module; the census readers' module has no loader) is legitimate and is the same shape as D1-D4, but it went UNRECORDED, so the Build Log's "All sixteen tasks landed as specced. Four deviations" is false and three document surfaces now describe a tree that did not ship; move the reader or record it as D5 and correct all three surfaces.
```


## Test & Observability Review — 2026-09-16

Same cold-start read, same no-shell constraint: the assertions below are about what the test code
SAYS it drives, read off the bytes, not about an executed floor.

**Trigger check.** APPLIES — this is not a pure refactor. `scripts/lint_vault.py` gains new
production paths (`read_vault`'s recording arm, `check_structural`'s `unreadable_note` branch, four
new failure buckets and two new records in `apply_fixes`, and a new unconditional operator-facing
summary line in `run_lint`), all on a tool Dave points at his live vault.

**1. Tests exist for the new code paths — comfortably.** `tests/test_lint_vault_fix_rules.py` is new
and imports the script through the same single loader the standing gate module uses (`:104-113`).
Every new path has a happy case AND at least one failure mode, and the failure modes are the
interesting half: the partition is driven with all four buckets non-empty and asserted non-empty
(`:1132-1135`), so the totality equality cannot be satisfied by three dead branches; all five decline
guards fire and the observed guard set is asserted EQUAL to the shipped `DECLINE_GUARDS`
(`:1140-1143`), so the vocabulary is closed from both sides; the mixed-file plant at `:1151-1195`
patches the SECOND `write_note` to raise and asserts the first issue stays `repaired` while only the
second is `errored`, which is the M4 discriminator and the one a fold-at-the-end build fails; the
tie-break plant at `:1198-1239` asserts a decline survives a co-occurring gate refusal on the same
file; and the corrupt-fence specimen is asserted into `errored` with `reason == "FrontmatterParseError"`
rather than into `refused` (`:1267-1272`). The unreadable path gets all four AC-3 legs including the
discriminating linker-and-meeting pair (`:954-989`) that separates "the skip is loud" from "the
report stopped lying about other notes", plus a never-written/never-moved check that byte-compares
before and after both `apply_fixes` and `quarantine_garbage` (`:1004-1019`).

D3 is a finding rather than a shortcut and the build is right to say so: three of the five decline
guards sit on branches no honest scan can reach (`:890` needs a non-string `auto_created` where the
detector only emits on a string; `:906` needs a type outside `TYPE_TO_MODEL`; `:935-936` needs
non-JSON `suggested_fix`), which is precisely why they could decline forever with nothing going red,
and driving them through hand-built issues at the `apply_fixes` frame is the only way to cover them
at all. The other two are produced end-to-end.

**2. Logging at WARN/ERROR for each failure mode.** This item's entire subject is the silence, and
the silence is closed. `read_vault`'s `except Exception` no longer discards — it records
`read_error=UNREADABLE` and the note reaches the report as one non-auto-fixable `unreadable_note`
issue (`:340-348`). Both `apply_fixes` handlers print one line per file to STDERR carrying the path
and the cause (`:1180`, `:1190`) while the machine-readable record carries a BOUNDED reason
(`type(exc).__name__`, asserted `.isidentifier()` at `:1275`) so note bytes and `str(exc)` cannot
reach an operator-facing summary. The summary line itself is the delivery channel and it is now
unconditional under `--fix` (`run_lint:1421`) with the pre-fix unreadable count bound BEFORE the
post-fix re-scan rebinds `all_files` (`:1381`) — the figure reports the pass whose fixes it
announces. `print`-to-stderr is the stated idiom for this interactive CLI and the project's rule
wins; there is no library-code swallow anywhere in the diff.

The leg that actually makes this observable is asserted the expensive way: AC-4(d)
(`:1316-1377`) captures REAL stdout under `redirect_stdout`, parses it structurally into five
labelled integers, pins the label tuple by hand-written equality with the fifth member imported, and
cross-checks every figure against an independent `apply_fixes` over a SECOND materialization — across
two planted vaults, with a variation clause asserting four of the five figures actually differ
between them. That is what stops the defect whose precedent is in the very file this item edits
(`test_the_fix_outcome_surfaces_both_counts`'s docstring claimed a CLI behaviour its body never
looked at; Task 5 corrects that docstring at `tests/test_lint_vault_fix_gate.py:276-290` and points
it at the check that does look).

**3. Alerts wired.** N/A, and correctly so. Nothing here is a new automated system — `lint_vault.py`
is an operator-invoked CLI with no launchd/cron surface, no scheduled entry point and no outbound
channel. The alerting question for this item IS the summary line, and it is covered above. The one
post-ship act that lives outside any battery (the A7 exit run appended to
`docs/lint-vault-live-baseline.md` §4) is declared as a conductor ship condition with its commands
and figure names already committed as bytes, and AC-5(d) asserts that text is present without
asserting the exit cells are empty — so the obligation is visible to a reader rather than resident in
prose. The Build Log states it plainly as still owed.

**4. Invariant registration.** N/A — skipped, not failed. `glob **/invariants.py` over this tree
returns nothing; the v1 registry scope is orchestrator-only and obsidian-schemas has not built one.
Per this role's own rule a project with no registry is noted N/A rather than blocked, and no
`## Observability Waiver` is needed for the same reason.

**One Recommended, non-blocking.** `test_the_fix_summary_prints_even_when_nothing_is_auto_fixable`
(`:1380-1402`) drives `run_lint(..., do_fix=True)` twice over a materialized corpus and depends on
the FIRST pass converging — i.e. on the corpus having nothing auto-fixable left after one pass. That
is true today (the Build Log's floor is green) and the assertion it then makes is the right one, but
the convergence is an unstated premise: a future corpus member whose repair introduces a second
auto-fixable issue would make `figures["repaired"] == 0` fail for a reason that has nothing to do
with the print. One line asserting the first pass's own summary reported a non-zero `repaired` and
the second reported zero would make the convergence explicit rather than assumed. Not blocking — the
check is correct as it stands and its subject (the print surviving an empty fixable set) is asserted
directly.

No blocking findings on this dimension. B1 in the code section is a document-fidelity defect and
touches neither coverage nor observability, so these two fences part company here, which the merged
gate's two independent vetoes are designed to allow.

```verdict
gate: test-observability-checker
verdict: PROMOTE
date: 2026-09-16
model: claude-opus-5
note: Every new production path has a test with a happy case and at least one failure mode — the four-bucket partition driven with all four buckets asserted non-empty, all five decline guards fired and equated to the shipped closed vocabulary, the M4 mixed-file plant patching the second write to raise, the tie-break plant, and the unreadable note's four legs including the linker/meeting discriminator and a byte-compare across both mutating doors; the item's own subject (the silent swallow) is closed and the operator channel is asserted against REAL captured stdout with a two-vault variation clause rather than against the record; alerting is N/A for an operator-invoked CLI and the post-ship A7 attestation is committed as bytes with a presence-only assertion; invariant registration is N/A because this project ships no registry (`**/invariants.py` returns nothing) — one Recommended only, the unstated single-pass convergence premise in `test_the_fix_summary_prints_even_when_nothing_is_auto_fixable`.
```

