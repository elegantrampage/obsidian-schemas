---
id: WI-026
title: "lint_vault.py --fix safety: route through the guarded primitive + a test floor for scripts"
project: obsidian-schemas
stage: specced
created: 2026-07-05
last_touched: 2026-09-15
stage_changed: 2026-09-15
touched_by: spec-writer
tags: [scripts, write-safety, testing]
depends_on: ["WI-004", "WI-020"]
transitions: ["idea>exploring@2026-09-10@porter", "exploring>specced@2026-09-15@porter"]
review_level: L3
review_level_provenance: selector
---

# lint_vault.py --fix safety

### Archived Rounds

<!-- archive-split: machine-maintained pointer; do not edit -->
Settled gate rounds for this item live in `docs/lint-vault-fix-safety-rounds.md` — every round at a conveyor door
this item has already advanced past, byte-for-byte, append-only, never rewritten. READ ON DEMAND
ONLY: each gate's latest standing round is still in this document, so nothing needed to advance this
item is in the drawer. Open it only to read a settled round's full reasoning.


> **Model routing** (2026-07-05 campaign, `docs/backlog-campaign-2026-07-05.md`; self-sufficient):
> - **Explore: —. Spec: Sonnet / medium. Spec-review: Opus / medium. Build: Sonnet / medium** + Opus code-review (standing rule).
> - Sequencing: Phase 4, after WI-004 (the primitive it must route through) and WI-020 (the malformed-YAML semantics it must respect).

## Problem / Motivation

`scripts/lint_vault.py` (1,198 LOC, zero tests — the largest untested file in the repo) mutates the whole real vault under `--fix`, and its write path shares WI-020's root cause: it reads via `parse_frontmatter`, mutates, and rewrites directly (lint_vault.py:869-875), bypassing the WI-126 body-shrink guard entirely. On a malformed-YAML note where a fix fires (e.g. `person_missing_name`, lint_vault.py:828-832, with `fm={}` and body = the whole raw file), `--fix` writes a file that **drops the original frontmatter** — the C2 corruption, gated only by a manual flag. It also re-serializes YAML across every touched file (rewriting hand-formatting) and silently skips unreadable files (`read_vault:112 except Exception: continue`). `scripts/migrate_person_to_discuss.py` (216 LOC, one-shot, already run) needs no investment beyond a header marking it historical. (2026-07-05 review finding H2 + test-suite risks #2/#3.)

## Intent

`--fix` cannot produce a write the library's own guards would refuse: it routes through the WI-004 primitive, refuses malformed-parse rewrites per WI-020, and carries a fixture-vault test for every fix rule it ships.

*Sharpened at exploring, 2026-09-10 — the sentence above is the frozen anchor and is reproduced
verbatim; these two are ADDED, and they narrow the outcome to what is still missing rather than
restating the two clauses the estate has since closed.* Two of that sentence's three clauses are now
true and walled by standing tests, so the outcome this item still owes is the third: an operator can
run `--fix` over a real vault and know, from what the tool tells them, exactly what it repaired, what
it declined, and what it could not read — with every repair rule proved against real-shaped notes
before it touches theirs. Nothing `--fix` cannot account for may leave the run silently, and no note
may disappear from the report just because its bytes would not decode.

## Currency note — 2026-08-11 (queue review) — premise HALF-CLOSED by WI-004, re-scope at spec time

WI-004 routed lint_vault's writes through vault_io (lock + read_note + write_note-with-
precondition at lint_vault.py:819-900; quarantine's mkdir via ensure_dir at :1043): the C2
mechanical hazard this doc leads with — direct rewrite bypassing the WI-126 guard, frontmatter
drop on malformed YAML — is now door-guarded, and WI-020's parse semantics apply at the door.
File is now 1,221 LOC; every line citation above is stale. REMAINING scope for this item:
(1) a fixture-vault test floor for the fix RULES themselves (zero tests today — pairs with
WI-016); (2) the silent skip of unreadable files (`except Exception: continue`, now :116) made
loud per WI-020; (3) the YAML re-serialization of hand formatting concern. Deps (WI-004,
WI-020) both done. The spec-writer should treat this doc's Problem section as historical and
re-audit before writing.

## Currency audit — 2026-09-10 (ideation, cold-start, `involvement: null` → approval-only)

Every number below was READ off this tree as this drive seeded it (HEAD `d6fbbb3` plus the seeded
uncommitted delta), with the predicate stated so a later reader re-runs it rather than trusting it.
This gate's granted tools are Read/Grep/Glob/Edit and no shell, so a premise needing EXECUTION is
marked as such and is never asserted as measured.

**The 2026-08-11 currency note is itself now half-stale.** WI-021 landed on this file after it was
written. `scripts/lint_vault.py` is 1,317 LOC (not 1,221), and every line citation in the Problem
section AND in the currency note is stale again — `except Exception: continue` is at **:117-118**,
not :116.

| Claim carried by this doc | Status on 2026-09-10 | Predicate |
|---|---|---|
| C2 hazard: `--fix` rewrites directly, bypassing the WI-126 guard | **CLOSED** | `apply_fixes` :858-975 — one `vault_io.note_lock`, `vault_io.read_note`, `vault_io.write_note(..., precondition=_stamp)`; quarantine via `vault_io.ensure_dir` :1134 + `vault_io.move_note` :1140 |
| …and it is WALLED, not merely fixed | **NEW since the note** | `tests/test_write_routing.py:91,370` and `tests/test_name_gate_wall.py:131` both scan `python_files_under(PACKAGE_ROOT, SCRIPTS_ROOT)`; `SCRIPTS_ROOT` is `tests/derivations.py:31`. A direct `write_text` reintroduced in this script is RED without anyone remembering it exists |
| Malformed-YAML rewrite drops the frontmatter | **CLOSED TWICE** | `parse_frontmatter` raises (WI-020), and the raise lands in `apply_fixes`' per-file handler :993 — no write. Upstream, `read_vault` :132-140 records `parse_error` and every check either `continue`s on it (:372, :455, :671) or emits the non-fixable `parse_error` issue and `continue`s (:297-305), so a malformed note produces no auto-fixable issue to begin with |
| "zero tests — the largest untested file in the repo" | **FALSE as written** | `tests/test_lint_vault_fix_gate.py` (WI-021 Task 10, 282 lines) plus `test_name_gate_delta_rule.py:182`, `test_name_gate_refusals.py:263,308,394`, `test_name_gate_identifiers.py:407`, `test_concurrent_access.py:599` (quarantine), `test_vault_path_required.py:344-368` (CLI) |
| …but the FIX RULES and the CHECK functions are still untested | **TRUE, and it is the item** | see the two tables below |

**The five auto-fixable rules, and what each has today.** The emitter set (a `LintIssue(...)`
construction carrying `auto_fixable=True`) and the branch set (a `issue.check == "…"` comparison
inside `apply_fixes`) are two hand-kept lists that happen to agree at five members. Nothing binds
them.

| rule id | emitter | fix branch | repair test today | live count (census, 2026-09-07) |
|---|---|---|---|---|
| `field_type_mismatch` | :341-347 | :888-894 | incidental — `test_lint_vault_fix_gate.py:185` asserts `"auto_created: true" in …` on the true-arm only | 19 |
| `person_missing_name` | :386-392 | :896-901 | incidental — `:186` asserts `"name: Alice Example" in …` | **0** |
| `missing_body_sections` | :357-363 | :903-909 | **none** | **821** |
| `meeting_missing_from_timeline` | :596-602 | :911-927 | **none** | **315** |
| `broken_wikilink` | :530-538 | :929-936 | **none** | **0** |

The live counts are the census's, not mine: `docs/vault-shape-census.md:272-281`, measured
2026-09-07 by the conductor with `scripts/lint_vault.py --vault $VAULT --report`, and charged into
that artifact FOR this item by WI-016's own precondition fence ("because the conductor is already in
the vault and WI-026 declares `needs: WI-016` … the shapes lint_vault's five auto-fixable rules fire
on, so that item does not require a second census pass" — `docs/vault-fixtures.md:1292`). It is
digest-frozen into `CENSUS_DIGEST`, so it cannot be edited under the criteria that read it.

**The five CHECK functions have no test of their own at all.** `check_structural`,
`check_completeness`, `check_links`, `check_timeline`, `check_noise` are reached by
`test_name_gate_refusals.py:394-401`, which runs two of them to source names for a gate sweep and
asserts nothing about what they decided. This is the half that matters most and the doc has never
named it: **a detector that mis-fires produces a wrong FIX, and `--quarantine` MOVES files off the
back of the same issue list** (:1218 → `quarantine_garbage` :1112-1144). The repair arm is the
audited one; the arm that decides WHAT gets repaired is the blind one.

**What the frozen corpus (WI-016, 53 notes) actually exercises.** Grep-settled, this tree:

- `field_type_mismatch` — **0 subjects**. `auto_created` occurs zero times in
  `tests/fixtures/vault/` (grep over the corpus: no matches).
- `person_missing_name` — **0 subjects**. Every person NoteSpec in `tests/fixture_vault.py` declares
  a non-empty `name`, and AC-2 of WI-016 binds those declarations to the bytes.
- `missing_body_sections` — **0 subjects**. Per-file `^## ` counts equal
  `ENTITY_BODY_CONFIG`'s expected counts for every typed member (person 3, company 4, meeting 6,
  book 2, exploration 6; `body_sections.py:303-324`). The `watch`/`explore`/`gift-idea` notes carry
  one heading each and `get_expected_sections` returns `[]` for them, so they are not subjects.
- `broken_wikilink` — **0 subjects**. There is exactly ONE `[[` in the whole corpus and it is in
  FRONTMATTER (`Harkwell Tessamund.md:7`, `related:`), which `check_links` never scans — it reads
  `vf.body`.
- `meeting_missing_from_timeline` — **THE ONE RULE THE CORPUS FIRES**. Five well-formed meetings
  declare 8 attendee entries between them (the sixth meeting file is the malformed-frontmatter skip
  specimen, so it never enters the `meetings` index), every named attendee has a person note, and
  every person note's `## Timeline` is empty. Count read off the manifest and `check_timeline`'s own
  predicate; **not executed** — the build's first run confirms it.

That 4-of-5-at-zero result is a finding, not a disappointment: it is what makes the corpus a
FALSE-POSITIVE floor (53 real-shaped notes on which four detectors must stay silent) and it is why
the discriminating specimens have to be PLANTED rather than sampled (WI-286).

**The silent skip, and why it is not a logging cosmetic.** `read_vault` :115-118 drops an unreadable
file with `except Exception: continue`. The file's BYTES are lost — that is unavoidable — but its
FILENAME is discarded with them, and five checks are keyed on the stem index built at :179-197:
`broken_wikilink` (:513), `meeting_attendee_not_found` (:482), `person_company_not_found` (:463),
`company_people_link_broken` (:497) and `orphaned_note` (:722). So one unreadable note makes the
report LIE about other notes, and one of those lies (`broken_wikilink` with a unique same-date
meeting candidate) is auto-fixable — it rewrites a live link away from a target that exists. The
corpus already carries the specimen: `@Isolde Varnholt.md` is the one non-UTF-8 member
(`fixture_vault.py:472-478`), so `read_vault` silently scans 52 of 53 notes today.

Two smaller swallows found in the same pass, named so nobody re-finds them: `apply_fixes` :935-936
(`except (json.JSONDecodeError, KeyError): pass` — drops a wikilink repair whose `suggested_fix` will
not parse) and the per-file handler :993-994, which PRINTS an IO/parse failure but counts it nowhere,
so the summary line at :1198 ("Fixed N issues, refused M") can be printed by a run in which every
single file failed.

## Exploration Notes

### The problem, restated after the audit

The item was minted as a write-safety item and it is not one any more. WI-004 and WI-021 closed and
then WALLED the write path; what is left is an **accounting and evidence** item, and the pain has
three halves — two of them accounting defects one level apart, which is why the third was missed on
the first pass through this section and is named separately now:

1. **Nobody has ever proved what a `--fix` rule does, or what a detector decides.** Three of five
   repair branches have no test; the two that do are asserted incidentally, as plumbing for the
   WI-021 gate. All seven DETECTORS have none — the five that decide which notes get WRITTEN, and
   the two `garbage_candidate_*` checks that decide which notes get MOVED under `--quarantine`
   (`check_noise` :673-719, driving `quarantine_garbage` :1112-1144 → `vault_io.move_note` :1140).
   The predicate behind the move arm is `classify_person_tier` (:233-283), a six-arm disjunction
   with zero tests and the largest blast radius in the file: a note it mis-classifies as `stub` is
   RELOCATED. The tool's whole value proposition is that it is safe to point at 4,730 issues across a
   real vault, and that claim currently rests on nobody having noticed a wrong repair or a wrong move.
2. **A run's output does not add up, at the FRAME level.** A note can leave the run in states the
   summary does not model: repaired, refused by the gate, failed on IO/parse, or never read at all.
   Only the first two are counted. The third prints (`:993-994`) and is tallied nowhere; the fourth
   is invisible AND corrupts the stem index other checks read.
3. **…and it does not add up at the ISSUE level either — the SILENT DECLINE.** An auto-fixable issue
   can reach its repair branch, hit that branch's own guard, and be dropped with no raise, no record
   and no count: `isinstance(raw, str)` (:890), `if expected` (:906), `if mstem and mstem in
   meetings` (:913 — which is EVERY `meeting_missing_from_timeline` issue, 315 live, whenever
   `apply_fixes` is called without `idx`, its own signature default at :828), the
   `except (json.JSONDecodeError, KeyError): pass` at :935-936, and the wikilink arm's no-match fall-
   through at :963-973 where neither `[[old]]` nor `[[old|` is present in the file. `changed` stays
   False, nothing is written, nothing is recorded. This is the SAME defect as half 2 one level in,
   and it is the harder one: half 2's third state at least PRINTS. This one is indistinguishable
   from a clean repair in every channel the tool has. It is also exactly what the Intent forbids —
   "nothing `--fix` cannot account for may leave the run silently" — and the two-sided emitter≡branch
   equality in A4 does not reach it, because that catches the STATIC version (a branch that does not
   exist), never the dynamic one (a branch that exists and declined).

Who feels it: Dave, directly and only — this is an operator tool he points at his own vault. Nothing
imports it (`scripts/` is not a package; `WI-030 lint-vault-package-export` is the item that would
change that, and it is at `idea`).

### Where the structure lives (the Phase-3 rule, applied)

The draft this doc arrived with reads as "make the skip loud" — i.e. print something at the point of
failure. That is the downstream workaround. The structure being discarded is the **filename**, at the
seam, in the `except` at :117: `read_vault`'s contract is "return a `VaultFile` per note" and it
quietly narrows that to "per note I could decode", while every consumer downstream is written against
the wider contract. The fix is at the seam — a `VaultFile` that carries a `read_error` the way it
already carries a `parse_error` (:97, and the four `if vf.parse_error: continue` guards that already
handle exactly this shape) — and then the stem index stops lying with no special case in any of the
five stem-keyed checks. A per-check `if this stem might be an unreadable file` patch would be five
homes for one fact.

The same reasoning decides the vocabulary. WI-020 already answered "what does a batch loader do with
a note it cannot load": it exposes a **queryable skip surface** with a fixed reason set —
`repositories/base.py:41-48`, `SKIP_REASONS = {MALFORMED_FRONTMATTER, SCHEMA_DRIFT, UNREADABLE}`,
already exported and already bound to `_skip_reason`'s own returns by two syntax scans
(`derivations.py:1526,1583`). lint_vault imports those constants; it does not spell `"unreadable"`
again. (WI-016 Task 11 made exactly this move for three hand-typed sites in `tests/`.)

### Approaches considered

**A1 — raise on an unreadable file (the literal reading of "loud-fail"). REJECTED.** This is a batch
tool over a whole vault: one undecodable byte would take out the entire report for 4,730 issues.
WI-021 made this exact call one frame lower, and its reasoning is quoted in `errors.py:106-134` — a
handler that RE-RAISES may filter on the hierarchy root, a handler that ABSORBS (records, counts,
continues) filters on its exact type and keeps going. `read_vault` is an absorbing frame. It records.

**A2 — put the auto-fixable specimens INTO the frozen corpus. REJECTED as the primary mechanism.**
The corpus is frozen by `CORPUS_DIGEST` behind a privacy wall (`NAME_POOL` / `CONNECTIVE_SET` /
`PROSE_ALLOWLIST`, and `CENSUS_DIGEST` over the census's own bytes), so every added specimen costs a
digest regeneration AND a pool-table row that only the conductor can certify against the live vault —
a paired edit across the cage boundary, which is the cost WI-016's own fence argues for avoiding.
**CHOSEN instead:** `materialize_vault(tmp)` and then PLANT on top of the materialized copy. Its
docstring blesses precisely this ("ADDS, never empties: … leaves everything else in that directory
alone", `fixture_vault.py:626-641`), the corpus stays byte-frozen, and the planted notes are where the
discriminators have to live anyway. The corpus is not decoration in this design: it is the
false-positive floor for the four rules that must fire zero times on it.

**A3 — preserve hand-formatted YAML (the currency note's third item). REJECTED, and this is the
pushback.** The concern is real but it is not lint_vault's: `apply_fixes` re-serializes through
`writer.write_frontmatter` → `yaml.dump`, and so does every other write path in the package
(`write_markdown_file`, every `repo.save`). A formatting policy implemented in the script would be a
second home for a package-wide rule, and the fix that would actually work (a comment-preserving YAML
round-trip, i.e. `ruamel.yaml`) is a dependency change with blast radius across HAL9000, exocortex
and orchestrator. If Dave wants it, it is its own item against `writer.py`, not a clause here. Worth
recording for that item: the loss is comments, quoting style and flow style — PyYAML's emitter quotes
any scalar that would otherwise re-resolve to another type, so a `date: "2026-01-04"` does not become
a `datetime.date` on the round trip. That last sentence is READ from PyYAML's behaviour, not
executed; the spec-writer has a shell and should confirm it with one round trip over a corpus note
before relying on it.

**A3b — the narrow version: skip the frontmatter rewrite when the fix was body-only. DEFERRED, with
the reason, so it is not re-explored.** `changed` is set by all five branches, and the write at
:951-957 always re-emits `---\n{yaml_str}---\n{body}` — so the two rules with the largest live
footprint (`missing_body_sections` 821, `meeting_missing_from_timeline` 315) reformat frontmatter they
never touched. Tempting, one-line-looking, and it is not: dropping that `write_frontmatter` call on a
branch REMOVES a member from `derivations.frontmatter_write_arms`, which two standing walls pin by
EQUALITY (`test_name_gate_wall.py` pins the six edited functions' arm counts; `test_company_name_contract.py:533`
carries `ArmId("scripts/lint_vault.py", "apply_fixes", 1)` in a hand-kept disposition table). A
cosmetic optimisation that drags two frozen wall sets with it does not belong inside a test-floor
item.

**A4 — a hand-listed table of the five rule ids in the test module. REJECTED (WI-131's
single-literal gap).** A sixth rule added next year joins the untested set silently. The class is
DERIVABLE from the script's own syntax — the `auto_fixable=True` emitters and the `issue.check ==`
comparisons are both readable with `ast` — and the derivation lands in `tests/derivations.py`,
because `ast` is single-homed there by a standing set-equality wall
(`test_wall_membership_is_closed_by_running_each_walls_predicate`). Deriving BOTH sides also buys the
invariant nothing holds today: emitter set ≡ branch set, so an emitter with no repair (a rule
advertised as auto-fixable that silently does nothing) and a branch with no emitter (dead repair
code) are each RED.

**A5 — and a derived sweep proves MEMBERSHIP, not correctness (WI-286).** Sweeping the five rules
is satisfiable by a stub that reports every rule "tested" while asserting nothing about the bytes. So
each rule carries a **correctness oracle whose expected value comes from a definition stated in this
document**, and each carries a member the live corpus cannot supply — planted on purpose:
- `field_type_mismatch` → the parsed value is the BOOL, per :891's own truth set. Discriminator: the
  FALSE arm (`auto_created: "no"` → `False`), which an "always True" implementation fails and which
  the corpus cannot supply at all (zero subjects).
- `person_missing_name` → the written name is `fpath.stem.lstrip("@")` **byte-for-byte**, NOT the
  cleaned form. Discriminator: a stem carrying the corpus's whitespace-damage shape — a double space
  — which `clean_person_name` would collapse (`name_cleaning.py:197`, `\s{2,}`) and which the gate
  passes untouched. The stem must be a NEW one (`@Tarnquil  Brenvik.md`, pool-certified tokens in a
  combination no corpus file uses), never the corpus's own `@Dave  Marrowyn Fennwick.md`: that file
  exists, carries a well-formed `name:`, and planting over it would destroy a corpus member and
  remove the note that proves the rule stays SILENT on a healthy double-spaced stem — see constraint
  7. `gate_write` is a predicate on `name`, not a transform
  (`name_gate.py:366-367`). An implementation that "helpfully" cleans is RED.
- `missing_body_sections` → every expected heading present, in `get_expected_sections` order, with
  pre-existing content under the sections that already existed still there. Discriminator: a note
  with SOME sections and real content under them (an implementation that writes the default body
  wholesale is RED, and that is the WI-126 shape).
- `meeting_missing_from_timeline` → the appended entry is exactly `_build_timeline_entry`'s declared
  format. Discriminators: a meeting with FOUR topics (proves the `[:3]` truncation), one with none
  (proves the no-suffix arm), and a person whose Timeline already holds an entry (proves append, not
  replace).
- `broken_wikilink` → `[[old]]` and `[[old|alias]]` both retarget; a link whose date matches TWO
  meetings is NOT rewritten (`len(candidates) == 1` at :523). The ambiguous case is the discriminator
  and is pure plant.

**A6 — the accounting invariant, and it is PER ISSUE over FOUR buckets.** Rather than adding a third
counter and hoping, the property worth asserting is a PARTITION. Two things about its shape were
wrong in the first draft of this section and are decided here:

*It is per ISSUE, not per file.* A file-keyed partition forces a "fixed-files" notion the code does
not have. `FixOutcome.fixed` counts ISSUES, and the wikilink arm increments the run counter directly
at `:972`, outside `file_fixed` entirely — so a file repaired ONLY by a link rewrite has
`file_fixed == 0`, and a build computing "fixed files" from the outcome would drop that file out of
every bucket while the equality still balanced. Per-issue is what the code already counts, it keeps
the equality total, and a declined COUNT is something an operator can act on where a declined FILE is
not.

*There are four buckets, not three.* {repaired, gate-refused, errored} is a partition of a
four-state space, and the missing state is half 3 above: an issue whose branch guard declined. Adding
the third bucket and calling the space closed would ship a criterion whose own `why` claims it makes
the uncounted state unrepresentable while the most common uncounted state walks straight through it.
So: **every auto-fixable issue handed to `apply_fixes` ends as `repaired`, `refused`, `errored` or
`declined`**, the four sets are pairwise disjoint and their union is the input, and the CLI's summary
prints all four counts plus the unreadable-note count from AC-3.

*The attribution rule, because two of the buckets are raised at FRAME level over a file that holds
several issues.* An issue's bucket is decided at the point the write carrying it commits, never by
its file's terminal state. The gate raises at `:947` BEFORE `fixed += file_fixed` at `:949`, so every
issue on a refused file is `refused` and none is `repaired` — that much is already true today and the
comment at `:878-882` says why it was built that way. But the SECOND write is not covered by it: the
wikilink pass at `:960-975` runs after `fixed += file_fixed` has already landed, so a file that
raises there has issues that ARE repaired and issues that are NOT, and a build that labels files
rather than issues will produce an off-by-N here. Name it in the spec so it is designed rather than
discovered.

*And the tie-break the rule needs to be decidable, decided here.* "Decided where the write carrying
it commits" has no answer for an issue that never reached a write: a decline happens inside the
per-issue loop, and the gate raises once, after that loop, at `:947` — so one file can hold a
declined issue AND a gate refusal, and pairwise disjointness is satisfied by two incompatible
labelings. **A decline is attributed at its BRANCH and is never re-labeled by a later frame-level
outcome on the same file** — it stays `declined` under a gate refusal at `:947` and under an IO
failure caught at `:993`. The reason is the frame's own shape rather than a preference: a declined
issue contributed nothing to `delta`, so it was not in the refused write and not in the errored one,
and its guard id is the only true statement available about it. The alternative — "every issue on a
refused file is refused" — attributes it to a gate that never saw it and turns the refusal count into
something an operator cannot act on. Left unstated, this is not a spec detail but an AC that pins
whichever reading the builder picked, which is why it is written into AC-4(b) with a plant carrying
both.

*Where the declined branch is recorded.* A closed record beside `NameGateRefusalRecord`, matching its
two-field discipline (`:805-818`) — the path, the issue's `check` id, and a guard id drawn from a
DECLARED closed set of the six decline sites named in half 3. Bounded values only: never `str(exc)`,
never note bytes, because this walks into an operator-facing summary that gets pasted into chat,
which is the channel `errors.py`'s bounded-message contract exists to close.

It extends `FixOutcome` (`:820-825`, already a record WI-021 introduced for exactly this reason)
rather than inventing a parallel channel. Its first field is named `fixed` today (`:823`) and the
four buckets are spelled `repaired / refused / errored / declined` everywhere in this document, so
the rename is a decision and not a detail — **ruled in the `## Write Targets` handoff note: the field
becomes `repaired`, one spelling for one bucket across the record, the printed labels and the guard
vocabulary**, because `fixed` is the very word whose issues-versus-files ambiguity forced the
per-file partition above to be withdrawn. `test_lint_vault_fix_gate.py:279` pins `FixOutcome._fields`
by EQUALITY and goes red by construction either way; the rename moves five more assertions in that
module and three in modules nobody had counted (`test_name_gate_refusals.py:275`,
`test_name_gate_identifiers.py:425`, `test_name_gate_delta_rule.py:203`). Nine sites, enumerated in
the handoff note; declare all nine as write targets at spec time.

*And the buckets have to reach the PRINT, which is a separate thing the buckets existing does not
buy.* Four fields on a record is the computation; the operator's only channel is the one `print` at
`:1198`, and a build can land the record, get every bucket right, and leave that line saying
`Fixed 0 issues, refused 0`. That is not hypothetical — the module above already contains the shape:
`test_the_fix_outcome_surfaces_both_counts` (`:276-281`) has a docstring claiming "the CLI surfaces
the refusal count beside the fixed count" and asserts only `_fields`, and NO test under `tests/`
calls `run_lint` or captures its stdout at all. So a fourth site in that module wants attention
alongside the three assertions: a docstring that describes a check nobody wrote. The criterion that
closes this has to read the printed bytes (AC-4(d)), and the mechanism is `redirect_stdout` around
`run_lint(..., do_fix=True)` — the zero-arg battery has no `capsys`, and `redirect_stderr` is already
the idiom two functions up (`:260-261`). Worth knowing before the spec: the summary goes to STDOUT
while the refusal and error prints go to STDERR (`:992`, `:994`), and the unreadable figure the line
must carry is the one from the PRE-fix `read_vault` at `:1160`, since `run_lint` re-reads the vault
at `:1201` after the fixes the line is announcing.

**A7 — the acceptance cannot be 100% hermetic, and the mechanism for that is a live-vault
BRACKET.** The first draft of this exploration proposed four `kind: test` criteria over a
materialized 53-note copy and nothing else, which is LESSONS #27 re-incurred and the WI-064 scar
verbatim: five green hermetic tests, an independent reviewer clear, and both real defects surfaced
only when the tool ran over real data. `lint_vault.py` is the canonical instance of "a tool whose job
is the whole corpus" — its correctness is DEFINED by its behaviour on 4,730 live issues, and a
linter's characteristic failure is the false positive on the shape nobody drew a fixture from, which
lives precisely in the tail no 53-note fixture contains. The comparable products agree with the scar
rather than with the first draft: ruff and ESLint each pair a fixture corpus with an ecosystem run
over real repositories, and shipping only the first half is the known-incomplete design.

This is not a frame problem — the project already owns the mechanism (a `kind: precondition` fence,
used exactly this way by WI-016 and WI-022) and the caged builder's blindness is a solved constraint.
The bracket is two runs of ONE command, `scripts/lint_vault.py --vault $VAULT --report`:

- **Entry (pre-build, a conductor act, in HEAD before the criteria are frozen).** The baseline the
  post-build delta is read against: the five auto-fixable counts (cross-checked against the census's
  own five rows), the counts of the five STEM-KEYED checks this change moves (`person_company_not_found`
  :463, `meeting_attendee_not_found` :482, `company_people_link_broken` :497, `broken_wikilink` :513,
  `orphaned_note` :722), and a standalone counting scan for notes `read_vault` cannot decode. Only
  the entry run can capture the OLD code's numbers; after the build they are gone. It also settles
  Open Question 1 outright, which is why that question is struck below rather than routed to Dave —
  Dave cannot know how many of his notes are undecodable, and one command can.
- **Exit (post-build, a conductor act at the ship boundary).** The same command re-run, appended to
  the same artifact as an attestation. `--report` and NOT `--fix`: this change alters what
  `read_vault` returns, so it moves the live counts of all five stem-keyed checks, and THAT DELTA is
  the acceptance evidence. Obtaining it must not require mutating Dave's vault, which is a separate
  authorization the item does not ask for and should not smuggle.

Two mechanisms for the EXIT half were considered and rejected, recorded so nobody re-explores them:
a `kind: precondition` fence (a category error — `VALID_WRITE_KINDS`' precondition is probed for git-
HEAD membership BEFORE the build spawn, `work_item_linter.py:167-171`, so it cannot carry an act that
by definition happens after), and a `kind: command` AC (`VALID_CRITERIA_KINDS` is `{test, command}`
and the battery skips unregistered ids, so this would mint a workshop command-registry entry from
inside a project item, and it would point an automated battery at Dave's live vault on a path he did
not authorize per-run). What is left is the shape WI-022 already used and this item copies: the
conductor's post-build attestation appended to the item's own evidence artifact
(`docs/company-name-corpus-audit.md:30-38` is the precedent, "post-build, at the quiesce"), declared
in `## Write Targets` and stated as a ship condition in `## Approach`. The ENTRY half IS fence-typed
and IS AC-enforced (AC-5); the exit half's wall is the conductor's ship door, and this document says
so plainly rather than pretending a wall it does not have.

**A7b — put the unreadable-note count in the CENSUS. REJECTED, with the cost the review did not
price.** `docs/vault-shape-census.md` is byte-frozen by `CENSUS_DIGEST` (WI-016 AC-3(iv)), so
appending a row to it reddens WI-016's own fixity check until the digest is regenerated in
`tests/fixture_vault.py` — a paired conductor/builder edit straddling the cage boundary, for a
measurement that is this item's evidence and not a census shape row. **CHOSEN instead:** a new
per-item evidence doc, `docs/lint-vault-live-baseline.md`, following the
`docs/wi-024-consumer-audit.md` / `docs/company-name-corpus-audit.md` precedent. The census stays
frozen and stays the authority for the five auto-fixable counts; the new artifact cross-checks
against it, so a live vault that has drifted since 2026-09-07 goes RED at AC-5 instead of being
silently trusted.

### Constraints discovered

1. **`scripts/` is not a package.** Tests load the CLI by path from `SCRIPTS_ROOT`
   (`test_lint_vault_fix_gate.py:37-51`). Reuse that loader — do not write a second one. It is also
   the coupling `WI-030 lint-vault-package-export` would change; that item's spec should expect to
   repoint it.
2. **`ast` is single-homed to `tests/derivations.py`** by a standing wall. The rule-set derivation
   lands there or the floor goes red for the wrong reason.
3. **The corpus is byte-frozen.** Mutation tests materialize into a temp dir; nothing may write into
   `tests/fixtures/vault/`.
4. **These criteria EXECUTE the library**, so the check module calls
   `ac_interpreter.ensure_project_interpreter(__file__)` as its first statement, ahead of every
   package import — WI-021's first build attempt drew five-of-five reds without it
   (`tests/ac_interpreter.py:1-44`).
5. **Write authority covers everything this needs** (`pipeline-runners.yaml:34-38` —
   `obsidian_schemas/**`, `tests/**`, `scripts/**`, `docs/**`), so nothing here is unbuildable by
   construction.
6. **Checks are zero-arg top-level `def test_*` that signal by raising** (`tests/support.py:1-19`).
7. **A PLANT MAY NOT REUSE A CORPUS FILENAME.** `materialize_vault`'s "leaves everything else in that
   directory alone" protects files the plant does not name; it does NOT protect a file the plant
   overwrites. The 53 corpus stems are the reserved set (`tests/fixtures/vault/`). The first draft of
   AC-1(c) tripped this: it named `Dave  Marrowyn Fennwick` as the whitespace-damage stem, and
   `tests/fixtures/vault/@Dave  Marrowyn Fennwick.md` already exists carrying a well-formed `name:` —
   planting it would have silently destroyed a corpus member AND removed the very note that proves
   `person_missing_name` stays silent on a healthy double-spaced stem. Plants should draw their
   tokens from the census's certified identity pool (`docs/vault-shape-census.md` → `census-pool`
   rows, each certified zero-hit against the live vault) in combinations no corpus file uses;
   `@Tarnquil  Brenvik.md` is one such stem and is the concrete substitute AC-1(c) now names. The
   spec-writer should also confirm whether the WI-016 privacy wall's universe reaches a NEW test
   module's source or only the corpus and census bytes — if it reaches the module, pool-certified
   tokens are mandatory rather than merely prudent.
8. **The skip-reason vocabulary wall has TWO hand-typed call sites, and both must move together —
   the UNIVERSE moves and the EXPECTED SETS DO NOT.** `skip_reason_literal_sites`
   (`tests/derivations.py:1583-1606`) already accepts an arbitrary `files` iterable, so the DERIVATION
   needs nothing. What pins the universe is `python_files_under(PACKAGE_ROOT, TESTS_ROOT)`, typed by
   hand at `tests/test_fixture_vault.py:508-509` and again at `:1302` (feeding the deliberate re-run
   at `:1315-1318`). Extending one and not the other leaves a half-extended wall that reads green.
   **The direction of the edit is the trap and it caught this document for two rounds:** the
   derivation reports a file IFF one of its parsed `ast.Constant` nodes is a `str` equal to a
   vocabulary member, so a file that IMPORTS `SKIP_REASONS` is never reported — growing the
   two-member expected sets at `:510-514` / `:1315-1318` by `scripts/lint_vault.py` makes the wall RED
   for exactly as long as the script behaves, and green only once someone hand-types `"unreadable"`
   there. The correct state is universe = `python_files_under(PACKAGE_ROOT, TESTS_ROOT, SCRIPTS_ROOT)`
   with both expected sets unchanged at `{base.py, test_fixture_vault.py}`, plus a non-vacuity
   assertion that the script is actually in the widened universe. Two facts make that safe on this
   tree and both were read rather than assumed: `scripts/` holds no literal equal to any `SKIP_REASONS`
   member today, and `scripts/` uses `ast` nowhere — so the `ast` single-home wall at `:1309-1312`,
   which shares the `universe` local at `:1302`, is strengthened by the same widening rather than
   reddened.

### Dependencies

- **WI-016 (done)** — the corpus, `materialize_vault`, and the census that grounds the live rule
  counts. This item's `needs: WI-016` in `state/manifests/queue-2026-09-06.yaml:52-54` is discharged.
- **WI-004 / WI-020 / WI-021 (all done)** — the routing, the parse semantics and the gate this item
  now only has to keep proved.
- **Downstream: WI-030** (`docs/lint-vault-package-export.md`, `idea`) would move this surface into
  the package; the path-loader in constraint 1 is the seam it touches.
- `scripts/migrate_person_to_discuss.py` (216 LOC, one-shot, already run) — the Problem section asks
  for a header marking it historical. Out of scope here and not worth an AC; fold it into WI-030 or
  leave it.

### One open question for Dave at sign-off

*(A second question — "does the live vault contain any note `read_vault` cannot decode?" — was
STRUCK. It is a measurement, not a judgement call: Dave cannot know the answer and one command can,
so routing it to a sign-off turn was the wrong channel. It is now the entry half of A7's bracket,
declared as the second `kind: precondition` fence below and read back by AC-5. The answer changes
nothing about whether AC-3 ships — the defect AC-3 closes is the report LYING about OTHER notes, the
corpus already carries the specimen for free, and "zero today" is a property of one snapshot of a
vault that churns — it changes only whether the criterion is prophylactic or load-bearing on day one,
and the artifact will say which.)*

1. **A3/A3b — is the YAML reformatting worth its own item?** A `--fix` run over the live vault today
   canonicalizes the frontmatter of every note carrying one of those 1,136 body-only issues. I have
   argued it out of THIS item on solve-in-one-place grounds; if it bothers Dave, it is a `writer.py`
   item with consumer blast radius, and it should be minted as one rather than smuggled in here.

### Revision — 2026-09-10, answering the architect's REVISE

Six changes, three blocking and three from the notes. Every citation below was re-read off this tree
(HEAD `d6fbbb3` plus the seeded uncommitted delta) rather than taken from the review.

1. **The acceptance was 100% hermetic (blocking 1).** Conceded in full — it is LESSONS #27 and the
   WI-064 scar, and the mechanism to fix it already exists in this project. A7 adds the live-vault
   bracket; a second `kind: precondition` fence declares `docs/lint-vault-live-baseline.md` with a
   stated shape contract; AC-5 reads it back and cross-checks §1 against the frozen census. Two
   places where this revision does NOT follow the review's own prescription, with reasons: the exit
   run is a declared SHIP CONDITION rather than a fence, because `kind: precondition` is HEAD-probed
   before the build spawn (`work_item_linter.py:167-171`) and so cannot by construction carry a
   post-build act, and `VALID_CRITERIA_KINDS` is `{test, command}` with the battery running pre-ship
   — the alternatives are recorded and rejected in A7 rather than left as a silent divergence; and
   the entry measurement goes in a NEW per-item evidence doc rather than being appended to the
   census, because the census is byte-frozen by `CENSUS_DIGEST` and appending to it would redden
   WI-016's fixity check pending a paired conductor/builder digest edit across the cage boundary
   (A7b). The baseline also captures more than the review asked for, and the addition is the point:
   the five STEM-KEYED check counts, which only the pre-change run can measure and which are the
   figures this change actually moves.
2. **AC-2 argued a scope it excluded (blocking 2).** Conceded — the review is right that
   `garbage_candidate_*` are INFO, sit outside an `auto_fixable=True` table, and drive the only arm
   that MOVES a file. Taken the widening arm rather than the narrowing one, because the move is the
   worst write on this file: the pinned set is now the SEVEN write-causing checks, and a new leg (c)
   pins `classify_person_tier` arm by arm against its own docstring definition with a syntax binding
   on the arm count, so a seventh arm cannot join untested. Verified while widening: both garbage ids
   pin at zero on the corpus for a structural reason, not by luck — `auto_created` appears nowhere in
   the 53 notes and both arms gate on it being truthy (`:245-253`, `:691-694`).
3. **AC-4's partition was three buckets over four states (blocking 3).** Conceded, and the review's
   per-ISSUE remedy adopted verbatim — `FixOutcome.fixed` does count issues and the wikilink arm does
   increment outside `file_fixed` at `:972`, both confirmed. Two additions from re-reading the frame:
   a FIFTH decline site the review did not list (`:963-973`, a wikilink replacement whose `old` text
   is not present falls through incrementing nothing), and an ATTRIBUTION RULE with its own leg,
   because the second write at `:960-975` runs AFTER `fixed += file_fixed` at `:949` — so a file can
   hold both a repaired issue and an errored one, and a build that labels files gets an off-by-N that
   no amount of per-file care fixes. The declined record's guard id comes from a declared closed set.
4. **AC-3(a) named the wrong artifact (note).** Corrected: the derivation already takes an arbitrary
   `files` iterable; what moves is the two hand-typed universe sites, `tests/test_fixture_vault.py:508-509`
   and `:1302`, and the criterion now asserts on both so a half-extended wall cannot read green.
   Recorded as constraint 8.
5. **The `person_missing_name` plant collided with a corpus file (note).** Confirmed —
   `tests/fixtures/vault/@Dave  Marrowyn Fennwick.md` exists with a well-formed `name:`. Substituted
   `@Tarnquil  Brenvik.md` (pool-certified tokens, no corpus collision) and generalised the trap into
   constraint 7, since every plant in AC-1 through AC-4 is exposed to it.
6. **`test_lint_vault_fix_gate.py` moves three assertions, not one (note).** Recorded in the Write
   Targets handoff note: `:279`'s `_fields` equality plus the numeric `outcome.fixed` assertions at
   `:166` and `:201`. AC-3's leg (c) now also says which checks need a guard (`no_frontmatter` at
   `:308`) and which are safe by construction (`orphaned_note` `:722`, `possible_duplicate` `:734`,
   both gating on `vf.entity_type`), so the build does not add guards it does not need.

The trigger-check observation is also accepted: `## Approach`'s routing line read the table the wrong
way and now routes to architect with the reasons stated.

### Revision — 2026-09-10 (round 2), answering the AC red-team's REVISE

Three findings, all conceded, all in the criteria text and none in the approach. Every citation below
was re-read off this tree rather than taken from the review. Two of the three land on clauses the
architect's round-2 non-blocking notes had also flagged for the spec-writer; the red-team is right
that "the spec-writer will fix it" is the wrong resting place for a wrong-as-written clause, because
what Dave signs at D4a is this text and not the spec that follows it.

1. **AC-4's accounting never had to reach the printed line (critical).** Conceded, and it is the
   sharpest of the three: legs (a)–(c) all drive `apply_fixes` directly, so a build could land four
   correct buckets and leave `:1198` printing `Fixed N issues, refused M` — the exact line an
   operator reads. The precedent is in the file this item edits and it is not a hypothetical shape:
   `test_the_fix_outcome_surfaces_both_counts` (`test_lint_vault_fix_gate.py:276-281`) claims the CLI
   surfaces both counts and asserts only `FixOutcome._fields`; grepped this tree to confirm the wider
   claim — nothing under `tests/` calls `run_lint` or captures its stdout. Leg (d) is rewritten to
   capture real stdout from `run_lint(..., do_fix=True, quiet=True)` under `redirect_stdout` (the
   zero-arg battery has no `capsys`; `redirect_stderr` is already the idiom at `:260-261`), parse it
   structurally into five labelled integers, and bind each to the figure the same run computed via an
   independent `apply_fixes` over a second materialization — plus a two-sided variation requirement
   across at least two planted vaults so a constant in any position is RED. Two additions the finding
   did not ask for, both from re-reading the frame: the unreadable figure must come from the PRE-fix
   `read_vault` at `:1160` and not the post-fix re-scan at `:1201`, and the leg states honestly that
   `errored` is NOT producible end-to-end through `run_lint`'s own issue list (a corrupt fence emits
   only the non-fixable `parse_error` and never enters `apply_fixes`, `:297-305`) so it is asserted
   format-only there and by value at the `apply_fixes` frame — an unsatisfiable "one of each of the
   five, end to end" would have been the next round's finding. The other four ARE producible and the
   plants are named, including a decline reachable through the real check pipeline that nobody had
   spotted: an inner-trailing-space wikilink (`[[Meeting 20260104 Nonexistent ]]`) which
   `check_links:510` strips before emitting, so the repair's `old` text is absent from the file and
   falls through `:963-973`.
2. **AC-4(b)'s disjointness had no tie-break (material).** Conceded — a decline inside the per-issue
   loop and a gate refusal at `:947` can co-occur on one file, and both labelings satisfy pairwise
   disjointness, so the criterion pinned whichever the builder chose. RULED: a decline is attributed
   at its branch and is never re-labeled by a later frame-level outcome, refusal or IO failure alike,
   because a declined issue put nothing in `delta` and so was in neither write. Stated in AC-4(b), in
   A6, and given a discriminating plant carrying both (a `meeting_missing_from_timeline` declining at
   `:913` under `idx=None` beside a `person_missing_name` whose Tier-1-dirty path-derived name raises
   the gate).
3. **AC-2(c) promised what its mechanism could not deliver (material).** Conceded without
   qualification — counting docstring bullets cannot see a seventh arm added as a fifth
   `if …: return "active"`, so "with or without a docstring line is RED" was false of the described
   binding. Taken the strengthening arm rather than the narrowing one: the scan now returns BOTH the
   bullet count (6 today, `:236-242`) and the `return "active"` site count (4 today, re-verified at
   `:253`, `:276`, `:279`, `:282`), and the criterion asserts both. The residue that remains is named
   in the desc rather than left implicit — an arm added by widening an existing `if`'s condition moves
   neither number — because the defect being fixed here is a criterion claiming a guarantee it lacks,
   and replacing one overclaim with a smaller one would repeat it.

Nothing in `## Approach`, `## Write Targets` or the two `kind: precondition` fences changes. AC-1,
AC-3 and AC-5 are untouched; AC-2's `why` and AC-4's `why` grow the rationale for the two rulings,
and AC-4's `check:` is renamed to `test_every_auto_fixable_issue_is_accounted_for_and_the_printed_summary_says_so`
so the function's name states the half that was missing.

### Revision — 2026-09-10 (round 3), answering the AC red-team's and the architect's REVISE

Both gates raised the SAME blocking finding independently, on AC-3(a), and both are right. It is
conceded without qualification. Every citation below was re-read off this tree (HEAD `d6fbbb3` plus
the seeded uncommitted delta) rather than taken from either review — including the derivation's own
body, which is what settles the finding.

1. **AC-3(a)'s closing clause could only be greened by committing the drift the leg forbids
   (critical, both gates).** The leg required the reason to be read from the imported constant AND
   required both declared-homes equalities to "grow the script's path". Those are contradictory, and
   the contradiction is decidable from `skip_reason_literal_sites`' body rather than from either
   gate's paraphrase: it walks parsed nodes and adds a file IFF one of its `ast.Constant` nodes is a
   `str` equal to a vocabulary member (`tests/derivations.py:1597-1606`), so an `import` and a
   `SKIP_REASONS.UNREADABLE` attribute access contribute nothing and a correctly-written script is
   never in the reported set. A builder discharging the old clause literally would have found both
   walls red and greened them the only way available — `reason = "unreadable"` hand-typed in
   `scripts/lint_vault.py` — shipping the fourth spelling the leg's own `why` cites WI-016 Task 11 as
   having spent three edits removing, with every wall in the suite green. RULED, and the remedy is the
   one both gates converged on: **the UNIVERSE widens at both call sites, the two declared-homes
   EXPECTED SETS do not move, and the assertion is that the two-member equality STILL HOLDS with
   `scripts/` inside the universe** — which is the statement that actually proves the script imports
   rather than transcribes. Adding the script's path to either expected set is now explicitly RED in
   the criterion text, so the wrong edit is refused rather than merely un-suggested. Two additions
   neither gate asked for, both from re-reading the wall rather than the reviews: a NON-VACUITY clause
   (a universe widened to a mistyped root is green for the wrong reason, so the criterion asserts
   `scripts/lint_vault.py` is IN the universe `python_files_under` returns), and the two facts that
   make the widening green TODAY, read off the tree so the builder is not widening blind — `scripts/`
   holds no string literal equal to any `SKIP_REASONS` member (case-insensitive grep for
   `unreadable` / `schema-drift` / `malformed-frontmatter` over `scripts/`: no matches) and `scripts/`
   uses `ast` nowhere, so the `ast` single-home wall at `tests/test_fixture_vault.py:1309-1312`, which
   shares the `universe` local at `:1302`, is STRENGTHENED by the same edit. Constraint 8 is rewritten
   to carry the direction of the edit, since it was the constraint that recorded the trap backwards.
2. **AC-5(b) named a census reader that does not exist, and the table is not keyed the way the leg
   assumed (architect note 1).** Confirmed on both halves. The four typed readers
   (`census_class_rows` `:121`, `census_pool_rows` `:139`, `census_meta` `:144`,
   `census_identity_residue` `:380`) are all `census-*` FENCE parsers, and the auto-fixable table at
   `docs/vault-shape-census.md:275-281` is a plain markdown table none of them reaches. Both gaps are
   now decisions in the criterion rather than discoveries at build time: a fifth reader beside the
   four, riding the same whole-file `CENSUS_DIGEST` fixity, and a declared five-row shape→rule-id
   mapping whose VALUE set is bound to AC-1(a)'s derived rule set so a sixth rule reddens the leg.
   One finding of our own while writing the mapping, and it is the reason the mapping is keyed on the
   message SHAPE: the census annotates `Empty name (suggest: '…')` as `(structural)`, but that
   emitter's own category is `"completeness"` (`lint_vault.py:388`, emitted by `check_completeness`) —
   a mapping keyed on the parenthetical mis-joins one row in five. The census is digest-frozen, so
   the annotation stays as it is and the mapping does not read it.
3. **The `test_lint_vault_fix_gate.py` inventory was offered as precise and was not — and the real
   answer turns on a naming question nobody had answered (architect note 2).** Both halves conceded,
   and the naming question is RULED here rather than deferred, because an unanswered field name is
   what made the inventory unanswerable: **`FixOutcome`'s first field becomes `repaired`**, one
   spelling for one bucket across the record, the labels AC-4(d) parses and the guard vocabulary —
   `fixed` being the exact word whose issues-versus-files ambiguity forced A6's per-file partition to
   be withdrawn, and a two-spelling join sitting inside the one leg that binds a printed label to a
   computed figure is where that ambiguity would land next. The cheaper alternative (keep `fixed`;
   one assertion moves) is recorded in the handoff note with its cost so it can be re-opened rather
   than silently re-decided. The inventory that ruling implies was then READ rather than estimated,
   and it is larger than the review's in a direction the review did not look: six of the eight
   field-touch sites in `test_lint_vault_fix_gate.py` move, and **three more live outside that module
   entirely** — `test_name_gate_refusals.py:275`, `test_name_gate_identifiers.py:425` and
   `test_name_gate_delta_rule.py:203` each assert on `outcome.fixed`. Nine sites across four modules,
   enumerated in the handoff note.
4. **AC-3(d) cited the wrong leg (architect note 3).** Corrected to AC-4(d), which is the leg that
   prints the unreadable count; AC-4(c) is the two-new-records leg and counts nothing. Worth the edit
   for the reason the note gives — AC-3(d)'s whole job is to place the unreadable note OUTSIDE AC-4's
   partition, so its pointer must land on the leg that does count it.

Nothing in `## Approach`, the two `kind: precondition` fences, AC-1, AC-2 or AC-4's legs changes.
AC-3(a) and AC-3(d) are rewritten, AC-3's and AC-5's `why` grow the rationale for the two rulings,
AC-5(b) gains the reader and the mapping, constraint 8 is rewritten, and A6 plus the handoff note
carry the field-name ruling and the nine-site inventory.

### Revision — 2026-09-15 (spec-writer), answering the data-premise REVISE and the architect's round-4 notes

The spec proper is written this round: `## Verified Diagnosis`, `## Design`, `## Edge Cases & Open
Questions`, `## Implementation Plan` (sixteen canonical tasks, each with a `verify:` declaration),
the nine builder `writes` fences, `## Verification`, `## Scope Boundary` and `## Risk Analysis`.
Every citation below and in those sections was re-read off THIS tree (worktree `cage-wt-ecmquixm`,
HEAD `09ebc1c`) rather than carried forward from any gate's paraphrase, because WI-023 shipped on
2026-09-11 and the document was written against `d6fbbb3`.

**The data-premise gate's three required groundings, all conceded, all folded into the criteria
rather than into the spec body — because what Dave signed is the criterion text, and a clause that
is wrong there stays wrong however carefully the Design compensates for it.**

1. **AC-5(b) was RED by construction against the artifact already in HEAD (blocking).** Conceded
   without qualification, and the gate is right that this is the WI-042 staleness class with a
   five-day fuse: AC-5 was drafted on 2026-09-10 as the fold answering the architect's blocking
   finding 1, describing an artifact that did not exist yet, and `docs/lint-vault-live-baseline.md`
   landed afterwards carrying `missing_body_sections` 835 against the frozen census's 821. Nobody
   re-read the criterion against the bytes that arrived. RULED, with the numbers in front of the
   ruling as the gate asked: a rule whose census count is ZERO must still be zero (strict — AC-1's
   "no live subject" argument and AC-2's false-positive floor both lean on those two zeroes); a rule
   whose census count is NON-ZERO must still be non-zero (sign pinned, magnitude free — the vault
   churns weekly); and in both directions the computed `baseline − census` must EQUAL the delta
   column the artifact's own §1 table carries, which is the clause that stops a pure tolerance from
   letting a mis-stated delta through with two legal endpoints. Verified green against HEAD without
   editing either file: 821/835 (delta `+14`), 315/315, 19/19, 0/0, 0/0.
2. **AC-5(a)'s shape contract was not satisfied by three of four sections (blocking).** Conceded.
   Read against the committed artifact: §0 has two argv fences and a stdout fence but no line
   reading `Command:` and no per-section SHA; §1 and §2 have none of the four elements at all; §3
   has both fences and neither of the other two; the file's one 40-hex tree SHA is global, at `:12`,
   and the hex at `:26` is a sha256 of stdout. The artifact is not defective — §1 and §2 are DERIVED
   from §0's single report and re-running a command per section would be a second walk of Dave's
   vault for numbers §0 already holds. The leg described a different artifact. NARROWED, in two
   passes within this round — the first pass kept the `Command:` element and was therefore STILL RED
   against §3, which has no such line, so the second pass stopped prescribing elements and ran a
   predicate against the committed bytes for every clause it kept: the SHA is file-level, asserted
   ONCE and matched DELIMITED so §0's 64-hex sha256 is not a second match; the five sections are
   matched by heading PREFIX, because §1's and §2's headings carry a trailing qualifier; MEASURED
   sections (§0, §3) carry at least two fenced blocks, an ARGV fence whose first non-empty line is
   an absolute interpreter path and a LAST fence holding verbatim stdout, and NO `Command:` line is
   required of either; DERIVED sections (§1, §2) carry no fence at all, one table, and a derivation
   sentence naming the §0 report. The same narrowing is written into the second `kind: precondition`
   fence's `why:`, as the gate required, so the leg and the fence cannot disagree.
3. **AC-2(a)'s vehicle could not express its own subject count (material).** Conceded. The gate
   EXECUTED what the 2026-09-10 exploration marked NOT EXECUTED and it is 8 issues over 5 DISTINCT
   person notes — `check_timeline:578-602` emits per (meeting, attendee) pair keyed on `pvf.path`,
   and `@Thrandell Ibberly`, `@Isolde Quenlaw` and `@Morvette Harkwell` each sit in two meetings
   (re-derived here off `tests/fixture_vault.py:361-382`). A set of `(filename, check)` pairs cannot
   hold 8 entries with 5 distinct values, so a build emitting one issue per person was green while
   dropping three. The leg now collapses to a mapping `(filename, check) -> ISSUE COUNT` and the
   8-over-5 figure is written into the desc, not left to the build's first run.

**What was GENERATING those findings, closed as a class rather than as three instances — and the
sweep of the next level, declared with what it found.** All three groundings share one generator: a
criterion clause written from what the artifact OUGHT to hold, never executed against the bytes that
exist. The first pass at this round closed the three instances and reproduced the generator inside
its own fix — the narrowed AC-5(a) kept the `Command:` element the gate had just shown to be absent
from §3, so the leg was still RED against a correct, committed file. So the class is closed here by
a RULE rather than by three edits: **every clause of every criterion that reads a committed artifact
or the frozen corpus carries a predicate that was RUN against those bytes before the clause was
written, and a clause that cannot be run is not written.** Applying it swept three more clauses in
AC-5 that no gate had raised — heading EQUALITY (two of the five headings carry a trailing
qualifier), an undelimited 40-hex SHA scan (twenty-five matches inside §0's own 64-hex sha256), and
a privacy scan wider than §3's stdout fence (the argv fence legitimately carries `rglob('*.md')`,
and §0 plus the header carry an absolute `/Users/…` interpreter path) — each of which would have
been a later round's finding. A FOURTH came out of the same sweep once the question was asked about
the artifact's LIFETIME rather than its current bytes, and it is the one this pass is most glad to
have caught: §4 is filled by the conductor at `ready → done`, adding a second real 40-hex SHA and
values in the `exit` column, while this check sits on the FLOOR and runs for good — so a
file-scoped SHA count, or the "exit cells are empty" clause this pass had itself drafted, would go
RED the day the item closes, on an artifact completed exactly as this document prescribes. That is
AC-5(b)'s original defect one artifact over, authored fresh inside its own fix. AC-5(a) is now
scoped to the header region and AC-5(d) asserts presence only, and the rule behind both is written
into Design §9b so a later clause about this file inherits it. Then the NEXT LEVEL of the ladder, the other four criteria, swept the
same way, and this is what that sweep found: **AC-1** — the five emitters (`:341`, `:357`, `:386`,
`:530`, `:596`) and five branches (`:888`, `:896`, `:903`, `:911`, `:929`) re-resolved, the plant
stem `@Tarnquil  Brenvik.md` absent from the corpus and `@Dave  Marrowyn Fennwick.md` present, no
clause changed; **AC-2** — the 8-over-5 figure executed (grounding 3 above) and
`classify_person_tier`'s two numbers RE-EXECUTED off `scripts/lint_vault.py:233-283` this pass, SIX
docstring bullets at `:237-242` and FOUR `return "active"` sites at `:253`, `:276`, `:279`, `:282`,
exactly as the criterion declares, no clause changed; **AC-3** — both universe sites, both
two-member expected sets, and `scripts/` free of any `SKIP_REASONS` literal and of `ast`, no clause
changed, but ONE courtesy drift recorded rather than edited: `tests/derivations.py` has moved ~2
lines since the criterion was written (`SCRIPTS_ROOT` is at `:33`, `skip_reason_literal_sites` at
`:1585-1608`, `python_files_under` at `:185-202`), every symbol resolves, Design §1 and §8 carry the
current numbers the builder reads, and AC-3 is deliberately NOT edited for a navigation ordinal
because that would invalidate `ac_hash_AC-3` (`9bd601c3a0d4`) and cost Dave a re-signature for
nothing; **AC-4** — the six decline sites and the `:947` / `:949` / `:960-975` ordering the
attribution rule turns on, all re-resolved, no clause changed.

**The architect's round-4 notes, all three actioned, none of them in a criterion.** Note 1 (the
summary print sits inside `if fixable:` at `:1191-1199`, so a run with nothing fixable prints no
line) is RULED in Design §5: the five-figure line prints unconditionally under `do_fix`, the
`"No auto-fixable issues found."` else-arm is dropped, and Task 13 adds
`test_the_fix_summary_prints_even_when_nothing_is_auto_fixable` as a NON-AC check — deliberately not
a new clause in AC-4, whose `ac_hash` this round leaves valid. Note 2 (the second Example of done
describes a run the CLI cannot produce, because `run_lint` passes `idx` at `:1194`) is corrected to
the reachable decline — the link-text-absent fall-through at `:963-973` — with the `idx=None`
condition kept as a true statement about `apply_fixes`' own default rather than about a CLI run.
Notes 3 and 4 (the parenthetical-separation rule, and the "SIXTH"/"fifth" census-reader label) are
both folded into AC-5(b): the reader strips a trailing parenthetical IFF its content is a member of
`scripts/lint_vault.py:CATEGORY_ORDER:1003`, read from the loaded module rather than re-spelled.

**One finding of the spec-writer's own, which no gate has named and which is a Write Target nobody
had declared.** `tests/test_ac_interpreter.py:47-50` holds `WORK_ITEM_DOCS`, a hand-kept tuple of
the work-item docs whose every `criteria` fence's `check:` is re-run under an `-S` foreign
interpreter on every floor run — and that module's own docstring rules that an item whose criteria
must EXECUTE the library "joins the wall that already exists" rather than writing a second copy of
the loop. All five of this item's checks execute the library, so `docs/lint-vault-fix-safety.md`
joins that tuple (Task 15), and the disclosed cost is five more subprocess re-execs per floor. It
was found by the WI-301 inbound sweep — asking which STANDING walls sweep the files this item ADDS,
rather than which modules assert into the surfaces it edits — and that sweep's full result is the
Regression paragraph in `## Verification`, stated as a FLOOR measured on 2026-09-15 and never as a
total. Its companion finding: WI-016 wrote its OWN copy of that loop
(`tests/test_fixture_vault.py:1368-1398`), which is the precedent this item does NOT follow.

**Two standing equalities the Design is explicitly shaped around, recorded so the build does not
trip them.** `frontmatter_write_arms` must still report exactly ONE arm for `apply_fixes` — pinned
twice, by `EDITED_FUNCTION_ARM_COUNTS` at `tests/test_name_gate_wall.py:108` and by the two-sided
`ARM_LEGS` equality at `tests/test_company_name_contract.py:602-616` with
`ArmId("scripts/lint_vault.py", "apply_fixes", 1)` classified `"excluded"` at `:533` — so the
`write_frontmatter` call at `:953-955` stays exactly where it is. And `NameGateRefusalRecord._fields`
must still equal `{path, pattern}` (`tests/test_lint_vault_fix_gate.py:234-237`), which is why
per-ISSUE refusal counting is obtained by emitting one record per refused issue rather than by
widening that record — a design decision forced by a wall, and the better one anyway.

**Signature impact, stated plainly because it is Dave's call and not the spec-writer's.** The
2026-09-15 `ac-signoff` fence carries `ac_hash: 03777fa0e132` over the whole `## Acceptance
Criteria` body plus five per-criterion hashes. This round edits AC-2's `desc` and `why`, AC-5's
`desc` and `why`, and the second `### Examples of done` scenario — so `ac_hash`, `ac_hash_AC-2`
(`1e40f7ae8765`) and `ac_hash_AC-5` (`7036c93e9f21`) are INVALIDATED and need Dave's re-signature.
The second pass described above re-edits AC-5's `desc` and `why` and the second `kind: precondition`
fence's `why:` (which sits outside every hashed span), so the invalidated set is UNCHANGED by it:
no criterion joins it and none leaves it, and AC-3 was deliberately left untouched for exactly that
reason where its only defect is a stale navigation ordinal.
`ac_hash_AC-1` (`23030080e7eb`), `ac_hash_AC-3` (`9bd601c3a0d4`) and `ac_hash_AC-4`
(`5cc1a0cc3737`) are untouched and stay valid; `intent_hash` (`6a7cccabd378`) is untouched —
nothing in `## Intent` moved. Every edit is a REFINEMENT bound to the spirit of the frozen
original: two criteria that could not be discharged green by a correct build are made dischargeable
without weakening what they promise, one assertion vehicle is strengthened from membership to
count, and one exemplar is corrected from an unreachable run to a reachable one. No promise is
weakened, no exception is carved into an original by an addition, and nothing is rewritten silently
— each change carries its own "corrected 2026-09-15, because…" sentence in the criterion's own text
so the diff is legible to the classifier without reference to this note.

**Self-review dry run.** Walked the sixteen tasks as the builder. Three questions a cold-start
builder would plausibly ask, and where each is answered: *"When exactly does an issue become
`refused` versus `declined` on a file that has both?"* — Design §4's one-sentence disposition rule
and the `undecided` list, with AC-4(b)'s discriminating plant. *"Do I add `scripts/lint_vault.py`
to the skip-reason wall's expected homes?"* — no, and Design §8 plus AC-3(a) say that edit is itself
RED, with the mechanism (`ast.Constant` equality) that makes it so. *"Where does the `unreadable`
figure on the summary line come from?"* — Design §5 ruling 2: the PRE-fix `read_vault` at
`run_lint:1160`, bound before the re-scan at `:1201` rebinds `all_files`. Then swept the document
for what this round's new claims contradict: the only collision found was the second Example of
done, which described an unreachable run and is corrected above; the currency note's and Problem
section's line citations remain stale by their own admission and are marked historical by the
2026-08-11 and 2026-09-10 audits, which is where a reader is sent. A FOURTH question arrived with
the second pass and is answered the same way: *"How do I read the baseline artifact — what shape is
it?"* — Design §9b names the four readers, the row facts of §1's table and the three predicates
AC-5(a)/(c) run, and Task 14 orders them. The second pass's own contradiction sweep found two more
and both are fixed rather than noted: this revision note's `NARROWED:` sentence still prescribed the
`Command:` element its own findings paragraph had just falsified, and Design §6 said "both" of three
scans while citing `skip_reason_return_values` at `:1570-1582` where it stands at `:1528`.

## Approach

Keep the write-safety clauses closed and prove the repair layer. Three changes to
`scripts/lint_vault.py`, one new test module, one new derivation, and a live-vault bracket around the
build:

`read_vault` stops discarding a file it cannot decode: it records the failure on a `VaultFile` that
carries the note's stem and an empty body — a `read_error` sibling to the existing `parse_error` —
so the stem index stays honest and the five stem-keyed checks stop reporting phantom breakage.
`check_structural` reports it as its own non-fixable issue whose reason is imported from
`repositories.base.SKIP_REASONS`, and every other check declines it exactly as it already declines a
parse error. `FixOutcome` grows from two buckets to four so that every auto-fixable ISSUE handed to
`apply_fixes` partitions into repaired / gate-refused / errored / declined (A6) — a decline attributed
at its own branch and never re-labeled by a later gate refusal or IO failure on the same file — with
the declining branch named in a closed record beside `NameGateRefusalRecord`, and the CLI's summary
line at `:1198` prints all four counts plus the unreadable-note count. That last clause is a code
change AND a covered one: the acceptance captures `run_lint`'s real stdout and binds every figure on
the line to the number the same run computed, because the record existing is the computation and the
print is the only channel the operator has — today nothing under `tests/` invokes `run_lint` or reads
a byte it prints. Then the floor: a derived sweep in
`tests/derivations.py` reads the script's own syntax for the set of auto-fixable rule ids — from BOTH
the emitters and the repair branches, whose equality is itself the invariant — and a new
`tests/test_lint_vault_fix_rules.py` drives every member of that set through `apply_fixes` over a
`materialize_vault` copy of the frozen corpus with discriminating specimens planted on top, against a
per-rule oracle stated in the acceptance criteria. The corpus's own contribution is the
false-positive floor.

**The detector half covers all SEVEN checks that cause a write on this file, not the five that fix.**
The two `garbage_candidate_*` checks are INFO and not auto-fixable, but they drive
`quarantine_garbage` → `vault_io.move_note`, and `classify_person_tier`'s six-arm disjunction is the
predicate that decides which person notes are RELOCATED. Pinning only the auto-fixable five would
ship a criterion whose stated reason for existing (a mis-firing detector produces a wrong WRITE) is a
hazard it does not cover. Both `garbage_candidate_*` ids pin at ZERO on the frozen corpus today —
`auto_created` occurs nowhere in it, and both arms gate on a truthy `auto_created` (`:245-253`,
`:691-694`) — so widening the false-positive table is nearly free, and each gets a planted stub for
the fires-on-its-own-subject leg.

**The build is BRACKETED by two conductor runs of `scripts/lint_vault.py --vault $VAULT --report`
against the live vault (A7).** The entry run lands in `docs/lint-vault-live-baseline.md` in git HEAD
BEFORE the criteria are frozen — it is a `kind: precondition` fence below and AC-5 reads it back. The
exit run is a **declared ship condition on this item**: at the `ready → done` boundary the conductor
re-runs the same command on the post-build tree and appends the attestation to the same artifact,
and the item is not done without it. What the diff must show, stated now so the ship act is one
command and not a design question: the five auto-fixable counts unchanged from the baseline; the five
stem-keyed check counts moved by exactly the amount the newly-indexed unreadable stems explain; the
new unreadable-skip count equal to the baseline's undecodable scan; and the summary line carrying all
five figures. This half is NOT battery-enforceable and this document does not pretend otherwise — the
battery runs pre-ship, a `kind: precondition` is HEAD-probed pre-build, and a `kind: command` AC would
point an automated battery at Dave's vault. Its wall is the conductor's ship door, on the WI-022
post-build-attestation precedent.

One session for the build. No package code changes, no consumer blast radius, no new dependency; two
one-command conductor acts outside the cage.

**Routing: architect, and the trigger table is why — the first draft of this line read it the other
way and was wrong.** The item touches more than three files across different concerns
(`scripts/lint_vault.py`, a new `tests/test_lint_vault_fix_rules.py`, a new scan in
`tests/derivations.py`, the two universe sites in `tests/test_fixture_vault.py`, three assertions in
`tests/test_lint_vault_fix_gate.py`, and a new `docs/lint-vault-live-baseline.md`), it extends two
persistent in-repo records (`VaultFile` gains `read_error`, `FixOutcome` goes from two buckets to
four plus a new closed record type), and it mints a new derived-wall class. The architect gate has
since run against this document and its findings are folded above; the spec-writer inherits both.

## Verified Diagnosis

Four load-bearing claims about how the current code behaves incorrectly. Each is grounded in an
artifact a reader can re-execute; nothing below is reasoned from. Every citation was re-read off
this tree on 2026-09-15 (worktree `cage-wt-ecmquixm`, HEAD `09ebc1c`), which is the tree the
data-premise gate also measured, so the two agree by construction rather than by luck.

**VD-1 — `read_vault` discards the FILENAME of a note it cannot decode, and five stem-keyed checks
then report phantom breakage about healthy notes.** `scripts/lint_vault.py:read_vault:115-118` is
`try: raw = md.read_text(encoding="utf-8") / except Exception: continue` — the file never reaches
`files`, so `scripts/lint_vault.py:build_indexes:179-197` never adds its stem to `all_stems` /
`stem_to_file`. Five checks read that index and emit on a miss:
`check_links:person_company_not_found:463`, `check_links:meeting_attendee_not_found:482`,
`check_links:company_people_link_broken:497`, `check_links:broken_wikilink:513` and
`check_noise:orphaned_note:722`. One of the five is auto-fixable: `check_links:527-538` emits a
`broken_wikilink` with `auto_fixable=True` whenever `MEETING_DATE_PATTERN` matches and the date
index holds exactly one candidate (`:524`), so `--fix` rewrites a live link off a target that is
sitting on disk. Falsifiable artifact: the frozen corpus already carries the specimen —
`tests/fixture_vault.py:472-478` declares `@Isolde Varnholt.md` with `raw_bytes_hex` ending
`fffefd`, so `read_vault` scans 52 of the corpus's 53 notes today and says nothing about the 53rd.

**VD-2 — an auto-fixable issue can reach its repair branch, be declined by that branch's own guard,
and leave the run with no raise, no record and no count.** Six sites, all inside
`scripts/lint_vault.py:apply_fixes`: `isinstance(raw, str)` at `:890`; `if expected` at `:906`;
`if mstem and mstem in meetings` at `:913`, which declines EVERY `meeting_missing_from_timeline`
issue whenever the caller takes the signature's own default `idx: Optional[dict] = None` at `:828`;
`except (json.JSONDecodeError, KeyError): pass` at `:935-936`; and the replacement fall-through at
`:963-973`, where neither `[[old]]` nor `[[old|` is present so `wl_changed` stays False. In all
six `changed` stays False for that issue, nothing is written, and `FixOutcome(fixed, refused)`
(`scripts/lint_vault.py:FixOutcome:820-825`) has no field that can hold it. Falsifiable artifact:
`apply_fixes([_issue(p, "meeting_missing_from_timeline")], vault)` with `idx` omitted returns
`FixOutcome(fixed=0, refused=())` — byte-identical to the return for an empty issue list already
asserted at `tests/test_lint_vault_fix_gate.py:280-281`.

**VD-3 — the per-file IO/parse failure is PRINTED and counted nowhere, so the operator's summary
line is byte-identical between a clean run and a run in which every file failed.**
`scripts/lint_vault.py:apply_fixes:993-994` is `except Exception as exc: print(f"  Fix error on
{fpath.name}: {exc}", file=sys.stderr)` with no tally, and
`scripts/lint_vault.py:run_lint:1198-1199` prints `f"Fixed {outcome.fixed} issues, refused
{len(outcome.refused)}. Re-scanning...\n"`. Falsifiable artifact: the standing check
`tests/test_lint_vault_fix_gate.py:_check_the_near_miss_produces_no_refusal_record:251-274` drives
exactly this — a note whose fence does not close — and asserts `outcome.refused == ()` and
`outcome.fixed == 0`, which is the same pair a vault with nothing to fix returns.

**VD-4 — no test anywhere under `tests/` invokes `run_lint` or reads a byte it prints, and the one
check whose docstring claims otherwise asserts only a field tuple.**
`tests/test_lint_vault_fix_gate.py:test_the_fix_outcome_surfaces_both_counts:276-281` carries the
docstring "the CLI surfaces the refusal count beside the fixed count" and its body is
`assert lint_vault.FixOutcome._fields == ("fixed", "refused")` plus a two-line empty-input probe.
Falsifiable artifact: `grep -rn "run_lint" tests/` returns nothing (re-run 2026-09-15 on this
tree), so the CLI half of that docstring has never been executed by the floor.

**Not diagnosed — the three detector claims are absences, not defects.** That the seven
write-causing checks and `classify_person_tier` have no test of their own is a coverage fact, read
off the tree by the 2026-09-10 currency audit's two tables and re-confirmed by the data-premise
gate's counterexample hunt (four mutation sites, `:957`, `:975`, `:1134`, `:1140`, and no fifth).
It is stated as a gap, never as an assertion that any of them currently mis-fires.

## Design

The item ships THREE code changes to `scripts/lint_vault.py` (the `read_vault` seam, the four-bucket
accounting, the operator's summary line), THREE new derivations in `tests/derivations.py`, ONE new
check module, and edits to SIX existing test modules (`test_fixture_vault`, `test_lint_vault_fix_gate`,
`test_name_gate_refusals`, `test_name_gate_identifiers`, `test_name_gate_delta_rule`,
`test_ac_interpreter` — the last found by the WI-301 inbound sweep, not by memory, and the reason
this count reads six rather than the five an earlier draft carried). Nothing in `obsidian_schemas/**` changes; no
new dependency; no consumer blast radius. Sections §1–§5 are the script; §6–§9 are the harness;
§10 is what must be true before any of it runs.

### §1. `VaultFile` gains `read_error`, and the seam stops narrowing its own contract

`scripts/lint_vault.py:VaultFile:88-97` is a nine-field dataclass whose last field is
`parse_error: Optional[str] = None`. It gains ONE field, in the same position and shape:

    read_error: Optional[str] = None    # a SKIP_REASONS member, or None

The field is LAST so every positional construction in the file keeps working; the two constructions
are `read_vault`'s existing one at `:143-154` and the new one below.

`read_vault`'s swallow becomes a record. The replacement for `:115-118`:

    try:
        raw = md.read_text(encoding="utf-8")
    except Exception:
        files.append(
            VaultFile(
                path=md,
                stem=md.stem,
                frontmatter={},
                body="",
                entity_type="",
                is_at_prefixed=md.stem.startswith("@"),
                raw_content="",
                read_error=UNREADABLE,
            )
        )
        continue

Four field values are decisions, not defaults:

- `read_error=UNREADABLE`, where `UNREADABLE` is IMPORTED — `from obsidian_schemas.repositories.base
  import UNREADABLE` beside the existing package imports at `scripts/lint_vault.py:38-50`. The
  script must never contain the string literal. That is not style: `tests/derivations.py:
  skip_reason_literal_sites:1585-1608` reports a file iff one of its parsed `ast.Constant` nodes is
  a `str` equal to a vocabulary member, and §8 widens that scan's universe to reach `scripts/`
  while holding its declared-homes set at two — so a hand-typed `"unreadable"` here is the one edit
  that reddens it.
- `body=""` and `raw_content=""`. `raw_content` (`:96`) is WRITTEN at `:151` and read nowhere else
  in the file, so it has no second consumer; `body=""` means `build_indexes:198-202` finds no
  wikilink in it and the note contributes no outgoing links, which is the truthful answer for bytes
  nobody could decode.
- `entity_type=""`. This is what makes `check_timeline` (index-driven over `meetings` / `persons`
  only), `check_noise:orphaned_note:722` and `check_noise:possible_duplicate:733-735` silent BY
  CONSTRUCTION — all three gate on `vf.entity_type` — so the build adds no guard for them.
- `is_at_prefixed` truthfully. It is a filename fact, and the one check that would then fire on it,
  `check_structural:no_frontmatter:308` (`vf.is_at_prefixed and not vf.frontmatter`), is handled in
  §2 above that branch rather than by lying about the stem.

`build_indexes` is UNCHANGED. It keys `all_stems` and `stem_to_file` off `vf.stem` at `:179-197`
with no type guard, so a `read_error` file joins both the moment `read_vault` returns it — which is
the whole of VD-1's repair. No stem-keyed check needs a special case.

### §2. `check_structural` reports it; the other three file-walking checks decline it

`check_structural:293-305` opens with `if vf.parse_error:` → emit → `continue`. The read-error arm
goes ABOVE it, first in the loop body, in the same shape:

    if vf.read_error:
        issues.append(
            LintIssue(
                vf.path, "unreadable_note", Severity.ERROR,
                f"Could not read note bytes: {vf.read_error}",
                "structural",
            )
        )
        continue

`auto_fixable` is left at its `False` default (`LintIssue:84`), so the note never enters
`apply_fixes` and sits OUTSIDE §4's per-issue partition by construction. The message carries the
reason value, so AC-3(a) can read it back and compare against `SKIP_REASONS` without a second
spelling anywhere.

The three other checks that iterate `files` already carry `if vf.parse_error: continue` —
`check_completeness:372`, `check_links:455`, `check_noise:670`. Each becomes
`if vf.parse_error or vf.read_error: continue`. `check_timeline:570-661` needs nothing: it iterates
`idx["meetings"]` and `idx["persons"]`, and a `read_error` file is in neither.

Severity is ERROR, matching `parse_error:300`. Consequence, stated so it is chosen rather than
discovered: `main:1311-1312` exits 1 when any ERROR is present, which it already does on the live
vault (3 `parse_error` rows in `docs/lint-vault-live-baseline.md:65`), and the live undecodable
count is 0 (`docs/lint-vault-live-baseline.md:120-122`), so this changes no live exit code today.

### §3. `FixOutcome` becomes a four-bucket partition, and two closed records join `NameGateRefusalRecord`

`scripts/lint_vault.py:FixOutcome:820-825` is replaced field-for-field:

    class FixOutcome(NamedTuple):
        repaired: int
        refused: tuple      # tuple[NameGateRefusalRecord, ...], ONE PER ISSUE
        errored: tuple      # tuple[FixErrorRecord, ...],        ONE PER ISSUE
        declined: tuple     # tuple[FixDeclineRecord, ...],      ONE PER ISSUE

`_fields` is exactly `("repaired", "refused", "errored", "declined")`. The first field is renamed
from `fixed` — ruled in the `## Write Targets` handoff note, one spelling per bucket across the
record, the printed labels and the guard vocabulary.

Two new records beside `NameGateRefusalRecord:805-818`, matching its closed-field discipline and
the bounded-message contract `obsidian_schemas/errors.py` states:

    class FixErrorRecord(NamedTuple):
        path: Path
        reason: str      # `type(exc).__name__` — NEVER `str(exc)`, never note bytes

    class FixDeclineRecord(NamedTuple):
        path: Path
        check: str       # the issue's own `LintIssue.check` id
        guard: str       # a member of DECLINE_GUARDS

`NameGateRefusalRecord`'s own field set does NOT move. It stays `{path, pattern}`, pinned by
equality at `tests/test_lint_vault_fix_gate.py:234-237`, and per-ISSUE counting is obtained by
emitting one record per refused issue rather than by widening the record — which is the reason that
equality survives this item untouched.

`DECLINE_GUARDS` is a module-level `frozenset` declared beside the records, with one member per
decline site VD-2 enumerates, so the check module reads it instead of re-spelling it:

    GUARD_AUTO_CREATED_NOT_A_STRING = "auto-created-not-a-string"   # :890
    GUARD_NO_EXPECTED_SECTIONS      = "no-expected-sections"        # :906
    GUARD_NO_MEETING_INDEX          = "no-meeting-index"            # :913
    GUARD_UNPARSABLE_SUGGESTED_FIX  = "unparsable-suggested-fix"    # :935-936
    GUARD_LINK_TEXT_ABSENT          = "link-text-absent"            # :963-973

    DECLINE_GUARDS = frozenset({...the five above...})

No member of `DECLINE_GUARDS` may equal a member of `SKIP_REASONS` — the five above do not, and the
check module asserts the disjointness so a future guard id cannot silently join the vocabulary the
§8 wall polices.

### §4. The disposition rule — where each issue's bucket is decided, and by what

This is the part a builder must not have to invent, because two internally-consistent readings
disagree (AC-4(b)'s tie-break). ONE rule, total over the input:

**Every auto-fixable issue handed to `apply_fixes` starts UNDECIDED. It leaves UNDECIDED exactly
once, at the first of these that happens to it: its own branch guard declines it (→ `declined`,
recorded AT THE BRANCH with its guard id); or the frame it is still undecided in reaches its end
(→ `repaired`), raises `NameGateRefusal` (→ `refused`), or raises anything else (→ `errored`).**

Concretely, inside the per-file body:

    undecided = list(file_issues)      # per file, beside the existing `file_fixed`

- A branch that declines appends `FixDeclineRecord(fpath, issue.check, <its guard id>)` to the
  RUN-LEVEL `declined` list and removes the issue from `undecided`, immediately, inside the loop.
  Run-level and not file-local is the tie-break: a declined issue contributed nothing to `delta`,
  so it was in neither the write the gate refused nor the write that errored, and no later
  frame-level outcome on the same file may re-label it.
- A branch that acts leaves the issue in `undecided` and increments `file_fixed` exactly as today.
- `broken_wikilink` is the two-stage one. At `:929-936` an unparsable `suggested_fix` declines with
  `GUARD_UNPARSABLE_SUGGESTED_FIX`; a parsed one queues `(issue, old_link, new_link)` — the queue
  gains the ISSUE as its first element so the second stage can name it — and stays undecided. At
  `:963-973`, a replacement that matches neither `[[old]]` nor `[[old|` declines with
  `GUARD_LINK_TEXT_ABSENT`.
- The `fixed += file_fixed` fold at `:949` is REPLACED by `repaired += len(undecided)` at the END of
  the `with vault_io.note_lock(fpath):` block, after the wikilink pass. The move is deliberate and
  is a behaviour correction: today `fixed` is credited at `:949` and the first `write_note` can then
  raise at `:957`, so a repair that never committed is reported as one. Under the new rule those
  issues are still undecided when the handler catches, and they become `errored`.
- `except NameGateRefusal as exc:` appends ONE `NameGateRefusalRecord(path=fpath,
  pattern=exc.pattern)` PER ISSUE still in `undecided`, and PRINTS ONCE. The print stays exactly one
  line per file: `tests/test_lint_vault_fix_gate.py:244-248` asserts the captured stderr equals a
  ONE-element list, so a build that moved the print inside the record loop is red there.
- `except Exception as exc:` appends ONE `FixErrorRecord(path=fpath, reason=type(exc).__name__)` PER
  ISSUE still in `undecided`, and PRINTS ONCE, unchanged in text — `:994`'s rendering is pinned by
  `tests/test_lint_vault_fix_gate.py:123-125` as an equality over the exception's MESSAGE.
  `undecided` here covers issues on a file that raised BEFORE the per-issue loop ran at all (a
  corrupt fence at `:860`, the `FileNotFoundError` guard at `:853`), which is what keeps the
  partition total.
- The exact-type filter on the refusal handler does not move. A corrupt fence is a
  `FrontmatterParseError`, a sibling leaf, and lands in `errored` — never in `refused`. The standing
  near-miss at `tests/test_lint_vault_fix_gate.py:251-274` asserts where it did NOT go; AC-4(c)
  extends it to say where it DID.

The equality this buys, and it is the one AC-4(a) asserts:
`len([i for i in issues if i.auto_fixable]) == outcome.repaired + len(outcome.refused) +
len(outcome.errored) + len(outcome.declined)`, with the four sets pairwise disjoint by issue
identity.

Two total-ness facts the rule rests on, both read off the tree: `person_missing_name:896-901` has NO
guard, so it never declines and correctly has no `DECLINE_GUARDS` member; and `by_file:832-835`
filters on `issue.auto_fixable`, so the partition's left-hand side is the filtered list and not the
raw argument.

### §5. The operator's line — five labelled figures, printed unconditionally under `--fix`

The computation existing is not the delivery. `scripts/lint_vault.py:run_lint:1191-1199` gains a
declared format and loses its guard:

    FIX_SUMMARY_LABELS = ("repaired", "refused", "errored", "declined", "unreadable")

    def _format_fix_summary(outcome: FixOutcome, unreadable: int) -> str:
        figures = (outcome.repaired, len(outcome.refused), len(outcome.errored),
                   len(outcome.declined), unreadable)
        return "Fix summary: " + ", ".join(
            f"{label} {value}" for label, value in zip(FIX_SUMMARY_LABELS, figures))

and the call site:

    if do_fix:
        fixable = [i for i in all_issues if i.auto_fixable]
        outcome = (apply_fixes(fixable, vault_path, idx) if fixable
                   else FixOutcome(0, (), (), ()))
        print(_format_fix_summary(outcome, unreadable))
        if fixable:
            print("Re-scanning...\n")
            ... the existing re-scan, unchanged ...

Three rulings inside those nine lines:

1. **The line prints on EVERY `--fix` run**, including one with zero auto-fixable issues. Today the
   print sits inside `if fixable:` (`:1193`) and the else-arm says `"No auto-fixable issues found."`
   — so the figure an operator most needs on a bad run (`unreadable`) is absent exactly when nothing
   was fixable. The else-arm's sentence is dropped; the summary line replaces it. (Architect round-4
   note 1, ruled here rather than inherited.)
2. **`unreadable` is the PRE-fix figure.** It is `sum(1 for vf in all_files if vf.read_error)`,
   computed immediately after `read_vault` at `run_lint:1160` and bound to a local BEFORE the re-scan
   at `:1201` rebinds `all_files`. The line reports the pass whose fixes it is announcing.
3. **`"Re-scanning...\n"` becomes its own print.** The summary line must be one parseable line, and
   AC-4(d) reads its bytes.

Channels are unchanged and separate: the summary goes to STDOUT, the refusal (`:992`) and error
(`:994`) lines to STDERR.

### §6. Three new derivations in `tests/derivations.py`

`ast` is single-homed there by two standing set-equality walls
(`tests/test_loud_fail_harness.py:103`, `tests/test_name_gate_wall.py:1136`) and a third in
`tests/test_fixture_vault.py:1309-1312`, so all three land there or the floor reddens for the wrong
reason. All three follow `tests/derivations.py:skip_reason_return_values:1528`'s loud-fail
discipline: a node the scan cannot resolve to a literal RAISES, never skips.

**(a) `auto_fixable_emitter_checks(files) -> set[str]`.** Every `check` string literal passed to a
`LintIssue(...)` call that ALSO passes `auto_fixable=` a `Constant` `True`. `check` is read
positionally as `args[1]` when the call is positional (the script's own form, e.g. `:340-347`) and
from `keywords["check"]` otherwise (the form `tests/test_lint_vault_fix_gate.py:63-70` uses), so the
scan is total over both. A `LintIssue(...)` whose `check` argument is not a `Constant` `str`, or
whose `auto_fixable=` value is not a `Constant`, RAISES with the module and line named.

**(b) `auto_fixable_branch_checks(files) -> set[str]`.** Every string literal compared with `==`
against an `ast.Attribute` whose `attr` is `"check"`, SCOPED to the enclosing `FunctionDef` named
`apply_fixes`. The scoping is load-bearing: `quarantine_garbage:1125,1127` carries two more
`issue.check ==` comparisons that are correctly outside this set. A comparison inside `apply_fixes`
whose comparator is not a `Constant` `str` RAISES.

**(c) `person_tier_arm_counts(files) -> dict[str, tuple[int, int]]`,** keyed by `module_id`, value
`(docstring_bullets, return_active_sites)` for the `FunctionDef` named `classify_person_tier`:
bullets are lines of its docstring `Constant` whose stripped form starts with `- ` (SIX today,
`scripts/lint_vault.py:236-242`); return sites are `ast.Return` nodes in its body whose value is
`Constant("active")` (FOUR today, `:253`, `:276`, `:279`, `:282`). A module with no such function
contributes no key; a function with no docstring RAISES.

### §7. The new check module `tests/test_lint_vault_fix_rules.py`

Five zero-argument top-level `def test_*` checks that signal by raising (`tests/support.py:1-19`),
one per criterion, plus two non-AC checks the plan adds (§5's unconditional print, and the WI-301
wall-membership closure). Its first statement is
`from tests.ac_interpreter import ensure_project_interpreter` followed by
`ensure_project_interpreter(__file__)`, AHEAD of every package import — the idiom every executing
check module in this tree already uses (`tests/test_identity_endgame.py:40-42`,
`tests/test_fixture_vault.py:25-27`), and the thing whose absence drew five-of-five reds on WI-021's
first build attempt.

The module loads the CLI through the EXISTING loader rather than a second one: it imports
`SCRIPTS_ROOT` from `tests.derivations` and uses the `importlib.util.spec_from_file_location` shape
`tests/test_lint_vault_fix_gate.py:_load_lint_vault:37-48` already carries. `scripts/` is not a
package (constraint 1); `WI-030 lint-vault-package-export` is the item that would change that.

**Subjects are PLANTED on top of a materialized corpus copy, never into the corpus.**
`tests/fixture_vault.py:materialize_vault:626-648` byte-copies the 53 notes into a caller-supplied
directory and "ADDS, never empties"; each check takes its own `tests/support.temp_dir()` and
materializes into it. Nothing may write into `tests/fixtures/vault/` (constraint 3), and no plant
may reuse a corpus stem (constraint 7) — the reserved set is the 53 filenames, and
`@Dave  Marrowyn Fennwick.md` is the specific trap. Plant stems draw their tokens from the census's
certified identity pool (`docs/vault-shape-census.md` → `census-pool` rows) in combinations no
corpus file uses.

### §8. The skip-reason wall's universe widens; its declared homes do not

`tests/derivations.py:skip_reason_literal_sites:1585-1608` needs NO change — it already takes an
arbitrary `files` iterable. What moves is the two hand-typed call sites that pin the universe:

- `tests/test_fixture_vault.py:test_skip_reason_declaration_binds_to_its_functions_returns:508-509`
- `tests/test_fixture_vault.py:test_the_fixture_vault_files_close_their_wall_memberships_by_running_each_predicate:1302`
  (whose `universe` local feeds the deliberate re-run at `:1315-1318`)

Both become `python_files_under(PACKAGE_ROOT, TESTS_ROOT, SCRIPTS_ROOT)`. BOTH expected sets stay
EXACTLY `{"obsidian_schemas/repositories/base.py", "tests/test_fixture_vault.py"}` (`:510-514`,
`:1315-1318`). Adding the script's path to either expected set is FORBIDDEN and is itself the
defect: the derivation reports a file iff it hand-types the literal, so a three-member equality is
greenable only by writing `"unreadable"` into `scripts/lint_vault.py`.

Two facts make the widening safe today, read off this tree rather than assumed: `scripts/` holds no
string literal equal to any `SKIP_REASONS` member (case-insensitive grep for `unreadable` /
`schema-drift` / `malformed-frontmatter` over `scripts/`: no matches), and `scripts/` uses `ast`
nowhere — so the `ast` single-home wall at `tests/test_fixture_vault.py:1309-1312`, which shares the
`:1302` local, is STRENGTHENED by the same edit rather than reddened.

### §9. The census's auto-fixable table gains its first reader

WI-016's four typed readers (`tests/test_fixture_vault.py:census_class_rows:121`,
`census_pool_rows:139`, `census_meta:144`, `census_identity_residue:380`) are all `census-*` FENCE
parsers; the five-row auto-fixable table at `docs/vault-shape-census.md:275-281` is a plain markdown
table none of them reaches. A FIFTH reader lands beside them, in the same module, riding the same
whole-file `CENSUS_DIGEST` fixity (which is over the file's bytes and is unaffected by a new
reader):

    def census_auto_fixable_rows(text=None) -> dict[str, int]

It parses the table's rows into `{message_shape: count}`, raising on a non-integer count or a
duplicate shape exactly as `census_class_rows:129-135` does. The KEY is the message shape with any
TRAILING parenthetical STRIPPED IFF that parenthetical's content is a member of
`scripts/lint_vault.py:CATEGORY_ORDER:1003` — which is what separates the category annotation from
the two shapes that legitimately carry their own parentheses, `Empty name (suggest: '…')` and
`[[…]] doesn't resolve (fixable → [[…]])`. The category is read and DISCARDED, never joined on: the
census annotates the `Empty name` row `(structural)` while that emitter's own category is
`"completeness"` (`scripts/lint_vault.py:388`), so a mapping keyed on the parenthetical mis-joins
one row in five. The census is digest-frozen, so the annotation stays as it is.

### §9b. The baseline artifact's reader, and the shape predicates AC-5(a)/(c)/(d) run

AC-5 reads a second committed artifact, `docs/lint-vault-live-baseline.md`, and it is NOT shaped
like the census: it is prose plus fences plus two derived tables. Its reader lands in the NEW check
module (`tests/test_lint_vault_fix_rules.py`) rather than beside `tests/test_fixture_vault.py`'s
census readers, because the baseline is this item's own evidence and nothing else in the tree reads
it. It uses no `ast`, so constraint 2 does not reach it. Four small functions, and every predicate
below was RUN against the committed bytes on 2026-09-15 before it was written here — which is the
discipline the data-premise gate's two blocking findings exist to install:

    def baseline_sections(text) -> dict[str, str]
    def fenced_blocks(section_text) -> list[str]
    def is_argv_fence(block) -> bool
    def baseline_auto_fixable_rows(text) -> dict[str, tuple[int, int, int]]

- **`baseline_sections`** splits on lines starting `## ` and keys each section by the ordinal prefix
  of its heading (`0`…`4`), matching the five declared headings as a PREFIX of the heading line and
  never by equality: `## 1. …` is followed by ` (vs …, measured 2026-09-07)` and `## 2. …` by
  ` (pre-change baseline)` in the committed file (`:72`, `:91`). A missing ordinal, a duplicate one
  or a heading whose prefix does not match RAISES with the heading quoted.
- **`fenced_blocks`** returns the triple-backtick-delimited blocks of one section, in order. MEASURED sections
  (§0, §3) must return ≥ 2 and DERIVED sections (§1, §2) exactly 0 — the committed counts are 3, 0,
  0, 2 and §4 is exempt (its commands are inline code spans at `:135-137`, not a fence).
- **`is_argv_fence`** is true when the block's first non-empty line starts with `/` and names a
  python interpreter. It is the leg's re-executability element, and it is what replaced the
  `Command:` line the artifact does not carry: §0's introduction reads `Command (the JSON report;
  …):` (`:19`) and §3 has no such line at all. In each measured section at least one block must
  satisfy it and the LAST block must not — that last block is the verbatim stdout (`:34-70`,
  `:119-122`).
- **`baseline_auto_fixable_rows`** parses §1's four-column table (`:77-84`) into
  `{rule_id: (census_count, today_count, delta)}`. Three row facts are decisions rather than
  discoveries, all read off the bytes: the SIXTH row is a TOTALS row (`**total auto-fixable**`,
  `**1,155 of 4,730**`) carrying no rule id and is SKIPPED — a reader that parses it meets
  `1,155 of 4,730` where it expects an integer; the rule id is the FIRST backticked span of column 1,
  which tolerates row five's trailing "(the fixable → sub-case)"; and the census cell is the LEADING
  integer before its parenthetical message shape (`821 (…)` → 821). Integers are parsed with `,`
  removed. A non-integer cell, a duplicate rule id, and a row whose first column carries a backticked
  identifier that is not a member of AC-1(a)'s derived rule set each RAISE in the READER — the totals
  row is not one of those, because it carries no backticked identifier at all and is skipped by that
  same test rather than by a hardcoded row index; the `today − census == delta` equality is the CHECK's assertion and not
  the reader's, so a mis-stated delta fails naming the rule and both numbers rather than dying
  inside a parse.

The privacy assertion AC-5(c) makes is scoped to §3's STDOUT block alone and the scoping is
load-bearing: §3's argv fence carries `rglob('*.md')` and `/usr/bin/python3`, and §0's fences plus
the file header carry the project interpreter's own absolute `/Users/…` path by design, so a
section-wide or file-wide scan for `.md` or `/Users/` is RED against a correct artifact. The
HEAD SHA AC-5(a) counts is matched DELIMITED at both ends by a non-hex character and is counted
ONLY in the HEADER region above `## 0. The run`: §0's 64-hex `sha256` (`:26`) would otherwise
contribute twenty-five undelimited matches, and §4's `post-build HEAD` row (`:158`) acquires a
SECOND real 40-hex SHA when the conductor fills the exit column at `ready → done` — this module
sits on the floor and runs for good, so a file-scoped count would redden it the day this item
closes. One assertion, one region, one lifetime.

**A NOTE FOR ANY LATER CLAUSE ABOUT THIS ARTIFACT, because the trap is general.** The baseline is a
LIVING file in exactly one place: §4's `exit` column and its `post-build HEAD` row are filled by the
conductor at `ready → done`, after the criteria are frozen and after most of the floor runs this
check will ever have. So a clause about §§0-3 may assert equality, and a clause about §4 asserts
PRESENCE only — never emptiness, never a count over the whole file. AC-5(a) and AC-5(d) are both
written to that rule.

### §10. Prerequisites & Assumptions

1. **`docs/vault-shape-census.md` is in git HEAD carrying the five-row table at `:275-281`** — the
   first `kind: precondition` fence. Verified, not measured: it has been in HEAD since WI-016.
2. **`docs/lint-vault-live-baseline.md` is in git HEAD** — the second `kind: precondition` fence.
   Committed 2026-09-10, five days before the 2026-09-15 sign-off, so the ordering promise held.
3. **Write authority covers everything** — `pipeline-runners.yaml:34-38` grants
   `obsidian_schemas/**`, `tests/**`, `scripts/**`, `docs/**`. Every path in `## Write Targets` is
   inside it; nothing here is unbuildable by construction (constraint 5).
4. **The cage seeds `.venv`** (`pipeline-runners.yaml:18-19`), which is what `ac_interpreter`'s
   delegation target resolves to. The editable install is stale by design — see CLAUDE.md — so the
   floor command is the only supported way to run the suite.
5. **No service need be running and no credential is used.** Every check is hermetic over a temp
   directory except AC-5, which READS two committed markdown files and executes nothing.
6. **The live vault is never touched by the build.** Both conductor runs are outside the cage and
   are `--report`, never `--fix`.
7. **Trust boundary.** The only untrusted input is vault bytes, and the one new crossing is a note
   whose bytes do not decode — handled by never decoding them (`body=""`, `raw_content=""`) and by
   emitting a BOUNDED message that names a vocabulary member, never the bytes. The two new records
   are bounded for the same reason: the summary is what an operator pastes into chat.
8. **`WI-016` is done** and its `materialize_vault` / corpus / census are the fixture substrate.
   `WI-004`, `WI-020`, `WI-021` are done and this item only keeps their guarantees proved.

## Edge Cases & Open Questions

- **Case:** `read_vault` hits a note whose bytes decode but whose YAML does not parse.
  **Decision:** unchanged — `parse_error` is set at `:129` or `:139` and `read_error` stays `None`.
  The two are siblings, never both. **Reasoning:** the decode and the parse are two different
  failures with two different reasons in `SKIP_REASONS`, and WI-020 already ruled the parse half.

- **Case:** a note is unreadable AND `@`-prefixed AND would otherwise trip `no_frontmatter`.
  **Decision:** `check_structural`'s read-error arm sits ABOVE the `parse_error` arm and `continue`s,
  so exactly one issue is emitted. **Reasoning:** `no_frontmatter:308` fires on
  `is_at_prefixed and not frontmatter`, which a `read_error` file satisfies; the guard goes at the
  one place that owns structural triage rather than by falsifying `is_at_prefixed`.

- **Case:** empty / null input to `apply_fixes` — an empty issue list, or a list with no
  `auto_fixable` member. **Decision:** returns `FixOutcome(0, (), (), ())`; the partition equality
  holds vacuously at 0 == 0. `run_lint` prints the summary line anyway (§5 ruling 1).
  **Reasoning:** `tests/test_lint_vault_fix_gate.py:280-281` already pins the empty-input return,
  and a run with nothing fixable is exactly when the `unreadable` figure matters most.

- **Case:** two `broken_wikilink` issues on one file naming the SAME `old` link.
  **Decision:** the first repairs; the second declines with `GUARD_LINK_TEXT_ABSENT`, because the
  text it is looking for is no longer in the content. Both are accounted for and the equality holds
  at 2. **Reasoning:** today the second silently increments nothing (VD-2's fifth site); the honest
  answer is a decline with a guard id, not a second repair.

- **Case:** a file holds one declined issue and one issue the name gate then refuses.
  **Decision:** the declined issue stays `declined` with its guard id; the other becomes `refused`.
  **Reasoning:** the tie-break in §4 — a declined issue put nothing in `delta`, so it was not in the
  write the gate refused. Labelling it `refused` would attribute it to a gate that never saw it.
  AC-4(b) carries a plant holding both.

- **Case:** the gate passes and `vault_io.write_note` then raises (a stale precondition, a lock
  timeout). **Decision:** every still-undecided issue becomes `errored`. **Reasoning:** this is the
  behaviour CHANGE §4 names — today `fixed` was already credited at `:949` and a repair that never
  committed is reported as one. No standing test covers the old behaviour; AC-4(a)'s equality
  requires the new one.

- **Case:** concurrent access — two `--fix` runs, or an Obsidian save mid-run.
  **Decision:** unchanged. `apply_fixes` holds one reentrant `vault_io.note_lock(fpath)` across both
  writes and each `write_note` carries the stamp of its own freshly-read bytes (`:858-859`,
  `:957`, `:961`, `:975`). A lost race surfaces as a commit failure, which is now `errored` and
  COUNTED rather than merely printed. **Reasoning:** WI-004 owns this and the item adds no write.

- **Case:** external dependency failure — the vault path is missing or unreadable.
  **Decision:** unchanged; `main:1292-1294` exits 1 before `run_lint`. A directory that becomes
  unreadable mid-walk raises out of `rglob`, which this item does not catch. **Reasoning:** widening
  `read_vault`'s absorb to directory-level failures would hide a broken mount, which is the opposite
  of what the item is for.

- **Case:** first run vs subsequent run. **Decision:** no difference. There is no state, no cache
  and no file the tool creates on first use. **Reasoning:** `--fix` is idempotent-by-convergence
  (below) and nothing persists between runs.

- **Case:** idempotency — re-running `--fix`. **Decision:** safe. A repaired note no longer emits
  the issue that repaired it, so a second run's `repaired` is 0 for those issues; `declined` is
  stable (a guard that declined declines again); `unreadable` is stable. **Reasoning:** the checks
  are pure functions of the notes' current bytes.

- **Case:** migration / backfill. **Decision:** none needed. No persisted schema, no stored record
  and no on-disk artifact changes shape. `VaultFile` and `FixOutcome` are in-process only.
  **Reasoning:** the only cross-run artifact is the vault's own notes, and their format is untouched.

- **Case:** retry semantics. **Decision:** none added. `apply_fixes` makes exactly one attempt per
  file and records the outcome; the operator re-runs the command. **Reasoning:** a batch repair tool
  that retries inside its own loop hides the transient/permanent distinction the four buckets exist
  to expose.

- **Case:** partial failure — the run dies after repairing 400 of 1,169 issues.
  **Decision:** unchanged. Each file's repair is committed under its own lock and precondition, so
  the vault is consistent at every point; the summary line is not printed and the operator re-runs.
  **Reasoning:** there is no transaction spanning files and inventing one is out of scope.

- **Case:** error propagation — what the caller sees. **Decision:** `apply_fixes` never raises out
  of its per-file loop (both handlers absorb, record and continue); `run_lint` returns the post-fix
  issue list; `main` exits 1 if any ERROR issue remains. **Reasoning:** A1's ruling — `read_vault`
  and `apply_fixes` are ABSORBING frames over a whole vault, so they filter on the exact type and
  keep going (`obsidian_schemas/errors.py:106-134`).

- **Case:** trust-boundary crossing — a note whose stem is adversarial, or whose bytes are hostile.
  **Decision:** the stem reaches `gate_write` as `name` exactly as today (`:897`) and the gate
  refuses it if it is Tier-1 dirty; bytes that do not decode are never decoded, never printed and
  never stored in a record. **Reasoning:** WI-021 owns the name half; the byte half is the new
  crossing and the answer is to carry a vocabulary member instead of the bytes.

- **Case:** the new `unreadable_note` check id collides with an existing one.
  **Decision:** it does not — the script's check ids are `parse_error`, `no_frontmatter`,
  `missing_type`, `field_type_mismatch`, `missing_body_sections`, `person_missing_name`,
  `person_no_email`, `person_no_company`, `person_no_linkedin`, `company_no_website`,
  `person_company_not_found`, `meeting_attendee_not_found`, `company_people_link_broken`,
  `broken_wikilink`, `person_not_in_company_people`, `meeting_missing_from_timeline`,
  `timeline_meeting_not_found`, `meeting_empty_content`, `intro_not_symmetric`,
  `garbage_candidate_person`, `garbage_candidate_company`, `orphaned_note`, `possible_duplicate`.
  **Reasoning:** `quarantine_garbage:1119` moves any issue whose check `startswith
  "garbage_candidate_"`, so the one naming rule that MATTERS is that the new id must not carry that
  prefix. It does not.

- **Case:** the census's live counts have drifted since 2026-09-07.
  **Decision:** they HAVE — `missing_body_sections` is 821 in the census and 835 in the baseline.
  AC-5(b)'s tolerance rule is ruled in this round: a rule whose census count is ZERO must still be
  zero (strict), a rule whose census count is non-zero must still be non-zero (sign preserved,
  magnitude free), and the delta is asserted against the artifact's own delta column.
  **Reasoning:** the data-premise gate's blocking finding 1 — a `kind: test` criterion that goes RED
  on a correct, frozen, already-committed artifact is a failing criterion, not a dashboard signal.
  The zeroes stay strict because AC-1's "this rule has no live subject" argument leans on them.

- **Case:** the conductor fills `docs/lint-vault-live-baseline.md` §4 at `ready → done`, and AC-5's
  check then keeps running on every floor run for the life of the repo.
  **Decision:** AC-5 asserts EQUALITY only over §§0-3, which the exit act does not touch, and
  PRESENCE only over §4; the header's 40-hex SHA count is scoped to the region above `## 0. The run`
  rather than to the file. **Reasoning:** the exit act adds a second real 40-hex SHA (the
  `post-build HEAD` row, `:158`) and fills the `exit` column, so a file-scoped SHA count or an
  "exit cells are empty" assertion would go RED the day this item closes — on an artifact completed
  exactly as this document prescribes. This check is a floor member, not a one-shot ship gate, and a
  criterion that cannot survive its own close-out is the same defect as AC-5(b)'s original
  "a divergence is RED" one artifact over.

OPEN: None. *(The 2026-09-10 open question — "is the YAML reformatting worth its own item?" — is
not an edge case of this build and is unchanged: A3 argues it out on solve-in-one-place grounds and
names `obsidian_schemas/writer.py` as the file its own item would target. It blocks nothing here.)*

## Implementation Plan

Sixteen tasks, ordered by dependency, each completable in one sitting. Tasks 9–13 may be done in
any order once Tasks 2–8 have landed; everything else is strictly sequential.

- [ ] **Task 1 — Capture the pre-build floor baseline.** Before the first edit, run the floor
  command (`/Users/davewascha/Workspaces/obsidian-schemas/.venv/bin/python -m pytest <worktree>/tests
  -q`, cwd-independent, the worktree's own path) and record BOTH the pass/fail verdict and the case
  count in the Build Log. Nothing is edited in this task. **Verify:** the Build Log carries a number
  and a verdict taken before any file changed; Task 16's delta is read against it.
  verify: baseline — the number is informational and its only artifact is the Build Log; no check asserts it.

- [ ] **Task 2 — `VaultFile` gains `read_error` and `read_vault` records instead of discarding.**
  Edit `scripts/lint_vault.py`: add `read_error: Optional[str] = None` as the LAST field of
  `VaultFile:88-97`; add `from obsidian_schemas.repositories.base import UNREADABLE` beside the
  existing package imports at `:38-50`; replace the `except Exception: continue` at `:115-118` with
  the recording form in Design §1, field for field. The string `"unreadable"` must NOT appear
  anywhere in the file. **Verify:** `read_vault` over a directory containing one non-UTF-8 `.md`
  returns a `VaultFile` for it whose `read_error` is in `SKIP_REASONS`, and
  `build_indexes(...)["all_stems"]` contains that note's stem.
  verify: test_an_unreadable_note_is_reported_indexed_and_never_silently_dropped

- [ ] **Task 3 — `check_structural` reports the unreadable note; the three sibling walks decline
  it.** Edit `scripts/lint_vault.py`: insert the `unreadable_note` arm as the FIRST branch of
  `check_structural`'s loop body, above the `parse_error` arm at `:297-305`, per Design §2; change
  `check_completeness:372`, `check_links:455` and `check_noise:670` from `if vf.parse_error:` to
  `if vf.parse_error or vf.read_error:`. `check_timeline` is untouched and the reason is recorded in
  a comment: it iterates the index, never `files`. **Verify:** a materialized corpus copy with a
  planted non-UTF-8 note produces exactly ONE issue at that path, it is not auto-fixable, and its
  message carries the imported reason value.
  verify: test_an_unreadable_note_is_reported_indexed_and_never_silently_dropped

- [ ] **Task 4 — `FixOutcome` becomes four buckets; the two records and `DECLINE_GUARDS` land.**
  Edit `scripts/lint_vault.py`: replace `FixOutcome:820-825` with the four-field form; add
  `FixErrorRecord`, `FixDeclineRecord` and the five `GUARD_*` constants plus `DECLINE_GUARDS` beside
  `NameGateRefusalRecord:805-818`; implement the §4 disposition rule inside `apply_fixes` —
  `undecided` per file, a decline recorded at each of the five branches, the fold moved to the end
  of the lock block, one record per undecided issue in each handler and exactly ONE print per file.
  `NameGateRefusalRecord`'s field set does not move. **Verify:** the standing WI-021 battery still
  passes with only the field rename applied to it (Task 5), and the four-bucket equality holds over
  a planted vault.
  verify: test_lint_vault_fix_guards_threads_and_records_refusals test_the_fix_outcome_surfaces_both_counts

- [ ] **Task 5 — The `fixed` → `repaired` rename across nine assertion sites in four modules.**
  Edit `tests/test_lint_vault_fix_gate.py` at `:117`, `:166` (the `.fixed` half only), `:201`,
  `:270`, `:279` (the `_fields` equality, which becomes
  `("repaired", "refused", "errored", "declined")`) and `:281` (the `empty.fixed` half, extended to
  assert `empty.errored == ()` and `empty.declined == ()`); `tests/test_name_gate_refusals.py:275`;
  `tests/test_name_gate_identifiers.py:425`; `tests/test_name_gate_delta_rule.py:203`. FOUR sites in
  the first module do NOT move — `:118`, `:200`, `:230-231` and `:265` all read `.refused`, which
  keeps its name, and `:234-235` is `NameGateRefusalRecord`'s own closure. Also correct
  `test_the_fix_outcome_surfaces_both_counts`'s docstring at `:277-278`, which claims a CLI
  behaviour its body never reads, to describe what it actually asserts. **Verify:** all four modules
  green; no occurrence of `outcome.fixed` or `empty.fixed` remains under `tests/`.
  verify: test_lint_vault_fix_guards_threads_and_records_refusals test_the_fix_outcome_surfaces_both_counts test_every_tier1_pattern_is_refused_at_every_door test_identifiers_normalize_identically_on_every_door test_a_legacy_dirty_name_stays_writable_for_unrelated_writes

- [ ] **Task 6 — The summary line: five labelled figures, printed on every `--fix` run.** Edit
  `scripts/lint_vault.py`: add `FIX_SUMMARY_LABELS` and `_format_fix_summary` per Design §5; bind
  `unreadable` from the PRE-fix `read_vault` at `run_lint:1160`; restructure `:1191-1199` so the
  summary prints unconditionally under `do_fix`, `"Re-scanning...\n"` is its own print inside
  `if fixable:`, and the `"No auto-fixable issues found."` else-arm is dropped. **Verify:**
  `run_lint(vault, do_fix=True, quiet=True)` over a planted vault prints one line carrying all five
  labels with integers, and over a vault with nothing auto-fixable prints the same line with
  `repaired 0`.
  verify: test_every_auto_fixable_issue_is_accounted_for_and_the_printed_summary_says_so test_the_fix_summary_prints_even_when_nothing_is_auto_fixable

- [ ] **Task 7 — The three new scans in `tests/derivations.py`.** Add
  `auto_fixable_emitter_checks`, `auto_fixable_branch_checks` and `person_tier_arm_counts` per
  Design §6, each raising on a node it cannot resolve to a literal rather than skipping it, each
  documented with the near-miss it must NOT match. Nothing else in the module changes. **Verify:**
  over `[SCRIPTS_ROOT / "lint_vault.py"]` the two rule scans each return a five-member set and the
  two sets are equal; `person_tier_arm_counts` returns `(6, 4)` for that module.
  verify: test_every_auto_fixable_rule_repairs_to_its_declared_oracle test_every_write_causing_detector_fires_exactly_on_its_declared_subjects

- [ ] **Task 8 — Widen the skip-reason wall's universe at BOTH call sites; hold both declared-homes
  sets at two.** Edit `tests/test_fixture_vault.py`: `:508-509` and `:1302` become
  `python_files_under(PACKAGE_ROOT, TESTS_ROOT, SCRIPTS_ROOT)`; the expected sets at `:510-514` and
  `:1315-1318` are UNCHANGED at two members. Add a non-vacuity assertion at each site that
  `scripts/lint_vault.py` is IN the universe the call returns. Editing one site and not the other
  leaves a half-extended wall that reads green (constraint 8). **Verify:** both walls green with the
  script in scope; the `ast` single-home wall at `:1309-1312`, which shares the `:1302` local, still
  answers `{"tests/derivations.py"}` over the larger universe.
  verify: test_skip_reason_declaration_binds_to_its_functions_returns test_the_fixture_vault_files_close_their_wall_memberships_by_running_each_predicate

- [ ] **Task 9 — The new check module's skeleton, loader and planting helpers.** Create
  `tests/test_lint_vault_fix_rules.py` with the `ensure_project_interpreter(__file__)` first
  statement, the `SCRIPTS_ROOT`-derived loader reusing
  `tests/test_lint_vault_fix_gate.py:_load_lint_vault:37-48`'s shape, a `materialize_vault(tmp)`
  helper, and a `_plant(vault, stem, body)` that REFUSES a stem already in the corpus (raising with
  the stem named) so constraint 7 cannot be tripped silently. The module must not name `ast` and
  must not hand-type any `SKIP_REASONS` member. **Verify:** the module imports under the floor and
  its plant helper raises on `@Dave  Marrowyn Fennwick`.
  verify: test_wall_membership_is_closed_for_every_file_this_item_touches

- [ ] **Task 10 — AC-1's check: the derived rule set, the total oracle table, the five oracles.**
  Add `test_every_auto_fixable_rule_repairs_to_its_declared_oracle` per AC-1's three legs — the
  two-sided emitter≡branch equality driven through Task 7's scans, an oracle table whose key set
  EQUALS the derived set, and the five per-rule oracles with their planted discriminators (the FALSE
  boolean arm; the byte-for-byte `@Tarnquil  Brenvik` stem; the some-but-not-all-sections note with
  real content; the four-topic, no-topic and already-populated-Timeline meetings; the ambiguous
  two-candidate link). **Verify:** the check is green, and mutating any one oracle's expected value
  by hand turns it red (observed and reverted).
  verify: test_every_auto_fixable_rule_repairs_to_its_declared_oracle

- [ ] **Task 11 — AC-2's check: seven write-causing detectors, both directions, plus the arm
  table.** Add `test_every_write_causing_detector_fires_exactly_on_its_declared_subjects` per AC-2's
  three legs — the false-positive table over the unplanted corpus keyed `(path, check) -> issue
  COUNT` (8 issues over 5 distinct person notes for `meeting_missing_from_timeline`, zero for the
  other six), one planted subject per pinned member, and `classify_person_tier`'s six-arm table
  bound to BOTH numbers Task 7's `person_tier_arm_counts` returns. **Verify:** green; and an arm
  table declaring five rows is red against the code-side count of 4 `return "active"` sites plus the
  6 docstring bullets.
  verify: test_every_write_causing_detector_fires_exactly_on_its_declared_subjects

- [ ] **Task 12 — AC-3's check: reported, indexed, quiet, never written.** Add
  `test_an_unreadable_note_is_reported_indexed_and_never_silently_dropped` per AC-3's four legs,
  including the discriminating second plant that LINKS to the unreadable stem and the planted
  meeting that lists it as an attendee — the pair that separates "the skip is loud" from "the report
  stopped lying about other notes". The reason is read from the imported `SKIP_REASONS`, never
  spelled. **Verify:** green; and reverting Task 2's `files.append(...)` to `continue` turns legs
  (a) and (b) red (observed and reverted).
  verify: test_an_unreadable_note_is_reported_indexed_and_never_silently_dropped

- [ ] **Task 13 — AC-4's check: the partition, the tie-break, the records, the printed bytes.** Add
  `test_every_auto_fixable_issue_is_accounted_for_and_the_printed_summary_says_so` per AC-4's four
  legs, and add the non-AC sibling `test_the_fix_summary_prints_even_when_nothing_is_auto_fixable`
  that drives `run_lint(..., do_fix=True)` over a materialized copy with NOTHING auto-fixable and
  asserts the five-label line is still printed (Design §5 ruling 1). Leg (d) captures real stdout
  under `contextlib.redirect_stdout` — never `capsys`, because the battery's checks take no fixtures
  — parses it into the five labelled integers using `FIX_SUMMARY_LABELS` read off the script, pins
  that tuple by a hand-written equality in the test, and cross-checks every figure against an
  independent `apply_fixes` over a SECOND materialization, across at least two planted vaults with
  different figure vectors. **Verify:** green; and hard-coding any one figure in
  `_format_fix_summary` turns the two-vault variation clause red (observed and reverted).
  verify: test_every_auto_fixable_issue_is_accounted_for_and_the_printed_summary_says_so test_the_fix_summary_prints_even_when_nothing_is_auto_fixable

- [ ] **Task 14 — The TWO readers (census table, baseline artifact) and AC-5's check.** Add
  `census_auto_fixable_rows` to `tests/test_fixture_vault.py` beside the four fence readers, per
  Design §9 — keyed on the message SHAPE, stripping a trailing parenthetical IFF its content is a
  member of `scripts/lint_vault.py:CATEGORY_ORDER:1003`, read off the loaded module and DISCARDED.
  Add the four baseline readers of Design §9b — `baseline_sections` (heading PREFIX match, because
  §1's and §2's headings carry a trailing qualifier), `fenced_blocks`, `is_argv_fence` and
  `baseline_auto_fixable_rows` (skip the bold totals row; rule id = first backticked span; census
  cell = leading integer before its parenthetical; `,` stripped) — to the new module, not beside the
  census readers. Then add
  `test_the_live_vault_baseline_is_committed_shaped_and_agrees_with_the_census` per AC-5's four
  legs, importing `census_auto_fixable_rows` from `tests.test_fixture_vault` (the cross-module test
  import `tests/test_fixture_vault.py:1296` already uses). The shape predicates are AC-5(a)'s as
  narrowed this round — five sections by heading prefix, ONE delimited 40-hex file-level SHA (§0's
  64-hex sha256 is not a second match), measured sections carrying ≥2 fences with an argv fence and
  a last stdout fence, derived sections carrying NO fence — and NO `Command:` line is looked for,
  because §3 carries none. The tolerance rule is AC-5(b)'s: census-zero rules strict,
  census-non-zero rules sign-preserving, the delta asserted against the artifact's own delta column.
  AC-5(c)'s privacy scan is scoped to §3's STDOUT fence only (its argv fence legitimately carries
  `rglob('*.md')`). **Verify:** green against `docs/lint-vault-live-baseline.md` AS COMMITTED, with
  no edit to that file or to the census; and mutating the reader to match headings by EQUALITY
  instead of by prefix turns it red on §1 (observed and reverted), which is the clause that proves
  the prefix rule is load-bearing rather than decorative.
  verify: test_the_live_vault_baseline_is_committed_shaped_and_agrees_with_the_census

- [ ] **Task 15 — Join the foreign-interpreter wall and close the inbound wall memberships.** Add
  `ROOT / "docs" / "lint-vault-fix-safety.md"` to `WORK_ITEM_DOCS` in
  `tests/test_ac_interpreter.py:47-50` — the tuple whose own docstring says an item whose criteria
  EXECUTE the library "joins the wall that already exists" rather than writing a second copy of it.
  Then add `test_wall_membership_is_closed_for_every_file_this_item_touches` to the new module,
  modelled on `tests/test_name_gate_wall.py:test_wall_membership_is_closed_by_running_each_walls_predicate:1057-1075`:
  declare this item's touched-file tuples and RUN each standing wall's own shipped predicate on
  their final text — `filesystem_mutation_uses` / `os_module_attribute_uses` / `module_import_uses`
  over the script, `frontmatter_write_arms` (whose `ArmId("scripts/lint_vault.py", "apply_fixes", 1)`
  is pinned by a two-sided equality at `tests/test_company_name_contract.py:602-616`),
  `character_class_strip_sites`, `address_splitting_implementations`, `modules_using_ast` over
  `python_files_under(PACKAGE_ROOT, TESTS_ROOT)`, `skip_reason_literal_sites` over the WIDENED
  universe, `FORBIDDEN_DEFAULT_PATTERNS` via `tests/test_vault_path_required.py:_code_lines`, and
  `criterion_checks` resolving all five check names uniquely through `check_module`. Anything the
  RUN returns that this spec did not name is recorded in the Build Log and satisfied — never worked
  around, and never satisfied by narrowing a wall. **Verify:** green, and the item's five criteria
  each exit 0 under the `-S` foreign interpreter having actually delegated.
  verify: test_wall_membership_is_closed_for_every_file_this_item_touches test_every_acceptance_criterion_passes_under_the_conveyors_interpreter

- [ ] **Task 16 — Run the floor and record the delta against Task 1.** Run the floor command and
  record the verdict and case count in the Build Log beside Task 1's baseline. The assertion is the
  PROPERTY (GREEN, and the count is not LOWER than the baseline — a drive that lands fewer cases has
  silently lost a test file), never a hardcoded number: the count moves with every sibling ship and
  CLAUDE.md says never to trust a number written down. Expected direction: up by the new module's
  seven checks. **Verify:** floor GREEN; the two numbers are both in the Build Log; any RED is
  reported with its output rather than summarised.
  verify: hand-run — the floor is a whole-suite command whose GREEN and case count are recorded in the Build Log, not a standing artifact any single check can assert.

## Write Targets

```writes
kind: precondition
path: docs/vault-shape-census.md
grounds: Which of lint_vault's five auto-fixable rules fire on real vault data, and at what multiplicity
why: AC-1's per-rule oracle set and AC-2's false-positive floor both rest on knowing which rules have live subjects and which have none — the frozen corpus fires exactly ONE of the five (`meeting_missing_from_timeline`), so without a measured live distribution a reader cannot tell "this rule has no corpus subject" from "this rule is dead", and the criteria would either over-promise (an oracle for a rule nobody can trigger) or under-promise (dropping the two rules that carry 1,136 live issues between them). The live vault is out-of-repo and this gate has no shell, so the premise is settleable only by a run someone else performs. THE ARTIFACT ALREADY EXISTS AND IS ALREADY IN HEAD: WI-016's own precondition fence charged its conductor with measuring exactly this for this item ("because the conductor is already in the vault and WI-026 declares `needs: WI-016` … the shapes lint_vault's five auto-fixable rules fire on, so that item does not require a second census pass", `docs/vault-fixtures.md:1292`), and it was measured on 2026-09-07 and committed at `docs/vault-shape-census.md:272-281` — `Missing sections` 821, `Attended [[…]] but it's not in Timeline` 315, `auto_created is string` 19, `Empty name` 0, `[[…]] doesn't resolve (fixable →)` 0, out of 1,155 auto-fixable issues in 4,730 total. It is declared HERE anyway rather than merely cited, for two reasons: the WI-300 door then pauses on a path that is already present and passes immediately at zero cost, and the premise gets a named, digest-frozen source (the file's bytes are pinned by WI-016 AC-3(iv)'s `CENSUS_DIGEST`, so the ledger cannot be rewritten by the party it audits) instead of a cross-item memory that a future reader would have to re-derive. The conductor's act here is therefore a VERIFICATION, not a measurement: confirm the path is in HEAD and that :272-281 still carries the five-row table before the criteria are presented. If it does not, the fallback is one command — `scripts/lint_vault.py --vault $VAULT --report` on the current vault, with the five counts appended to the census by the same rules that governed the first pass — and AC-1's oracle set is unaffected either way, because it derives the rule set from the script's syntax and never from these counts; what the counts ground is the ARGUMENT for covering all five rather than only the ones that fire.
```

```writes
kind: precondition
path: docs/lint-vault-live-baseline.md
grounds: What today's `read_vault` reports over the live vault, which is the only baseline the post-build delta can be read against
why: A7 — this item's acceptance was 100% hermetic in its first draft, which is LESSONS #27 and the WI-064 scar (five green fixture tests, an independent reviewer clear, and both real defects surfacing only on real data). `lint_vault.py` is the canonical instance of a tool whose job is the whole corpus: a linter's characteristic failure is the false positive on the shape nobody drew a fixture from, and that shape lives in the tail no 53-note fixture contains. This fence is the ENTRY half of the bracket that fixes it, and entry is the half that can only be captured NOW: this item changes what `read_vault` RETURNS, so it moves the live counts of all five stem-keyed checks (`person_company_not_found` :463, `meeting_attendee_not_found` :482, `company_people_link_broken` :497, `broken_wikilink` :513, `orphaned_note` :722), and after the build the old code's numbers no longer exist to be measured. It also settles the question this document previously routed to Dave as a sign-off judgement call, which was the wrong channel — Dave cannot know how many of his notes are undecodable and one command can. THE ARTIFACT DID NOT YET EXIST WHEN THIS FENCE WAS WRITTEN; it was a MEASUREMENT the conductor performs, not a verification of something already in HEAD. DISCHARGED — the conductor measured it on 2026-09-10 and committed it, five days before the 2026-09-15 sign-off, so the `grounds:` ordering promise ("in HEAD before the criteria are frozen") was kept and the WI-156 build-spawn probe passes; what remains for the builder is to READ it, never to write it (2026-09-15, spec-writer, confirming the data-premise gate's own measured result). SHAPE CONTRACT, on the `docs/company-name-corpus-audit.md` precedent and NARROWED 2026-09-15 by the spec-writer to what the committed artifact actually is (the data-premise gate's blocking finding 2: the original wording demanded four elements of every section and §1/§2 are DERIVED tables carrying none of them, so a builder discharging it literally would have had to edit the frozen entry measurement) — the artifact carries the tree's 40-hex HEAD SHA ONCE, file-level, in the header above §0, matched DELIMITED at both ends by a non-hex character so §0's 64-hex `sha256` of the report's stdout is not a second one; its five sections are matched by HEADING PREFIX, never by heading equality, because §1's and §2's headings carry a trailing qualifier; each MEASURED section (§0, §3) carries AT LEAST TWO fenced blocks — an ARGV fence whose first non-empty line is an absolute path to a python interpreter, and a LAST fence holding verbatim stdout — so any reader can re-execute it and contradict it, and NOT a `Command:` line, which §3 does not carry at all and which §0 spells `Command (the JSON report; …):` (this clause was narrowed a SECOND time on 2026-09-15 by the spec-writer against the committed bytes: the first pass kept the `Command:` element from the original wording, where it was still RED for §3); each DERIVED section (§1, §2) carries NO fenced block at all and instead a stated derivation naming the §0 run its numbers come from, plus its own table, because re-running a command per section would be a second walk of Dave's vault for numbers §0 already holds: (i) `## 0. The run` — `scripts/lint_vault.py --vault $VAULT --report` on the current vault, verbatim; (ii) `## 1. The five auto-fixable counts` — one row per rule, to be compared against `docs/vault-shape-census.md:272-281` (821 / 315 / 19 / 0 / 0 as measured 2026-09-07); a divergence is not an error, it is the staleness signal AC-5 exists to raise; (iii) `## 2. The five stem-keyed check counts` — the pre-change baseline for each of the five checks listed above; (iv) `## 3. The undecodable scan` — a standalone count of paths under `read_vault`'s own walk (`vault_path.rglob("*.md")` minus `should_skip`) for which `read_text(encoding="utf-8")` raises, with the count and NOTHING ELSE (no filenames, no bytes — the privacy wall reaches this artifact the way it reaches the census); (v) `## 4. Post-build attestation` — declared here as a NAMED EMPTY SECTION carrying the exact command and the exact figure names the exit run must fill, so the conductor's ship act is one command rather than a design question. THE EXIT HALF IS A SHIP CONDITION, NOT A FENCE, and deliberately so: `kind: precondition` is probed for git-HEAD membership BEFORE the build spawn (`work_item_linter.py:167-171`), so it cannot by construction carry an act that happens after the build, and a `kind: command` AC would mint a workshop command-registry entry from inside a project item and point an automated battery at Dave's live vault. The exit run is therefore the conductor's act at `ready → done`, appended to this same file as an attestation on the WI-022 precedent (`docs/company-name-corpus-audit.md:30-38`, "post-build, at the quiesce"), and this item is not done without it. `--report` and never `--fix` on both runs: mutating Dave's vault is a separate authorization this item does not ask for.
```

### Builder write targets — 2026-09-15 (spec-writer)

The nine paths the caged build-runner creates or modifies while executing the Implementation Plan.
The driven doc (`docs/lint-vault-fix-safety.md`) is implicit and is not declared. Every path is
inside `pipeline-runners.yaml:34-38`'s grant (`obsidian_schemas/**`, `tests/**`, `scripts/**`,
`docs/**`), so nothing here is unbuildable by construction. `docs/vault-shape-census.md` and
`docs/lint-vault-live-baseline.md` are READ by AC-5 and are NOT written — they keep their
`kind: precondition` fences above and appear in no fence below.

```writes
path: scripts/lint_vault.py
why: Tasks 2, 3, 4 and 6 — `VaultFile.read_error` and `read_vault`'s recording arm, `check_structural`'s `unreadable_note` branch plus the three sibling declines, `FixOutcome`'s four buckets with `FixErrorRecord` / `FixDeclineRecord` / `DECLINE_GUARDS` and the §4 disposition rule inside `apply_fixes`, and `FIX_SUMMARY_LABELS` / `_format_fix_summary` with the unconditional print at `run_lint:1191-1199`. AC-4(d) asserts on the printed bytes, so the summary line's format is a contract rather than a message.
```

```writes
path: tests/derivations.py
why: Task 7 — `auto_fixable_emitter_checks`, `auto_fixable_branch_checks` and `person_tier_arm_counts`. They land here and nowhere else because `ast` is single-homed to this module by three standing set-equality walls (`tests/test_loud_fail_harness.py:103`, `tests/test_name_gate_wall.py:1136`, `tests/test_fixture_vault.py:1309-1312`); a private copy in the check module is red on all three before it asserts anything (constraint 2).
```

```writes
path: tests/test_lint_vault_fix_rules.py
why: Tasks 9-15 — the new check module. Five zero-argument `def test_*` criteria checks plus `test_the_fix_summary_prints_even_when_nothing_is_auto_fixable` (Design §5 ruling 1) and `test_wall_membership_is_closed_for_every_file_this_item_touches` (the WI-301 inbound half), and the four baseline readers of Design §9b (`baseline_sections`, `fenced_blocks`, `is_argv_fence`, `baseline_auto_fixable_rows`), which land HERE rather than beside the census readers because `docs/lint-vault-live-baseline.md` is this item's own evidence and nothing else in the tree reads it; they use no `ast`, so constraint 2 does not reach them. Created, so no symbol anchor.
```

```writes
path: tests/test_fixture_vault.py
why: Tasks 8 and 14 — the skip-reason wall's universe widened at BOTH call sites (`:508-509` and `:1302`) with both declared-homes expected sets held at two members and a non-vacuity clause added at each, plus the fifth census reader `census_auto_fixable_rows` beside the four existing `census-*` fence parsers. One site without the other is a half-extended wall that reads green (constraint 8).
```

```writes
path: tests/test_lint_vault_fix_gate.py
why: Task 5 — six of the eight `FixOutcome` field-touch sites move with the `fixed` -> `repaired` rename (`:117`, `:166`, `:201`, `:270`, `:279`, `:281`), `:279`'s `_fields` equality becomes the four-member tuple, `:281` grows two empty-bucket assertions, and `test_the_fix_outcome_surfaces_both_counts`'s docstring at `:277-278` is corrected to describe what its body actually asserts. Four sites do NOT move — `:118`, `:200`, `:230-231`, `:265` read `.refused`, which keeps its name.
```

```writes
path: tests/test_name_gate_refusals.py
why: Task 5 — one assertion, `outcome.fixed` at `:275` inside `test_every_tier1_pattern_is_refused_at_every_door`, renamed to `outcome.repaired`. Nothing else in the module changes.
```

```writes
path: tests/test_name_gate_identifiers.py
why: Task 5 — one assertion, `outcome.fixed` at `:425` inside `test_identifiers_normalize_identically_on_every_door`, renamed to `outcome.repaired`. Nothing else in the module changes.
```

```writes
path: tests/test_name_gate_delta_rule.py
why: Task 5 — one assertion, `outcome.fixed` at `:203` inside `test_a_legacy_dirty_name_stays_writable_for_unrelated_writes`, renamed to `outcome.repaired`. Nothing else in the module changes.
```

```writes
path: tests/test_ac_interpreter.py
why: Task 15 — `docs/lint-vault-fix-safety.md` joins the `WORK_ITEM_DOCS` tuple at `:47-50`. This item's five criteria EXECUTE the library, and that module's own docstring rules that such an item "joins the wall that already exists" rather than writing a second copy of the loop (which is what `tests/test_fixture_vault.py:1368-1398` did for WI-016). Disclosed cost, stated because the wall itself discloses it: five more `-S` subprocess re-execs on every floor run.
```

**Handoff note on builder write targets — DISCHARGED 2026-09-15.** The fences above are the ones
this note asked for; it is kept below as the reasoning that produced them, not as outstanding work.
One target it did not anticipate is `tests/test_ac_interpreter.py`, derived at spec time by the
WI-301 inbound sweep rather than by memory. Beyond
`scripts/lint_vault.py`, the new `tests/test_lint_vault_fix_rules.py` and the new scan in
`tests/derivations.py`, three existing files move and each is easy to miss:
`tests/test_fixture_vault.py` at BOTH `:508-509` and `:1302` (constraint 8 — one without the other is
a half-extended wall that reads green, and the edit widens the UNIVERSE only: both expected sets stay
at two members); `tests/test_lint_vault_fix_gate.py`, whose inventory is given exactly below because
the earlier draft of this note offered "three assertions" as a precise list and it is not one; and
`tests/fixture_vault.py` only if the corpus manifest gains anything, which the
plant-on-a-materialized-copy design (A2) is chosen precisely to avoid. Three further targets the
criteria now imply and nobody has typed: `scripts/lint_vault.py`'s summary print at `:1198` (AC-4(d)
asserts on its bytes, so its format is a contract and not a message); the `tests/derivations.py` scan
AC-2(c) needs, which returns TWO numbers for `classify_person_tier` — the docstring bullet count and
the `return "active"` site count — rather than the one the earlier draft asked for; and the FIFTH
CENSUS READER plus the shape→rule-id mapping AC-5(b) needs, both landing in
`tests/test_fixture_vault.py` beside the four fence readers that cannot reach the markdown table at
`docs/vault-shape-census.md:275-281`.

**The `FixOutcome` FIELD NAME, ruled here so the inventory below is exact.** The four buckets are
spelled `repaired / refused / errored / declined` in A6, AC-4 and `## Approach`, and the record's
first field is `fixed` (`:823`) — so whether the rename happens decides how many assertions move, and
nobody had answered it. **RULED: the field is `repaired`, one spelling for one bucket across the
record's fields, the printed labels AC-4(d) parses, and the guard-id vocabulary.** The reason is the
one this document already paid for: `fixed` is the word whose issues-versus-files ambiguity produced
the per-file partition A6 had to withdraw, and leaving it on the record while the print and the prose
say `repaired` puts a two-spelling join inside the one leg (AC-4(d)) that binds a printed LABEL to a
computed FIGURE. The alternative — keep `fixed`, move exactly one assertion — is cheaper by eight
lines and is recorded here rather than left implicit, so a spec-writer who disagrees can re-open it
with the costs in front of them.

**The inventory that ruling implies, read off this tree rather than estimated.** In
`tests/test_lint_vault_fix_gate.py` the two fields are touched at `:117-118`, `:166`, `:200-201`,
`:230-231`, `:265`, `:270`, `:279` and `:281`. SIX move: `:117`, `:166` (its `.fixed` half), `:201`,
`:270`, `:279` (`FixOutcome._fields == ("fixed", "refused")`, an equality that goes red by
construction under A6 whatever the name), and `:281` (its `.fixed` half). FOUR do not: `:118`,
`:200`, `:230-231` and `:265` all read `.refused`, which keeps its name, and `:234-235`'s
`record._fields` is `NameGateRefusalRecord`'s two-field closure, a different record this item does
not touch. **And the rename reaches THREE MODULES OUTSIDE that file, which no gate has named and
which the "three assertions" figure silently excluded** — `tests/test_name_gate_refusals.py:275`,
`tests/test_name_gate_identifiers.py:425` and `tests/test_name_gate_delta_rule.py:203` each assert on
`outcome.fixed`. Nine assertion sites across four modules, all mechanical, all inside the item's
write authority (`tests/**`). Plus one site that is not an assertion at all:
`test_the_fix_outcome_surfaces_both_counts`'s docstring at `:277-278` claims "the CLI surfaces the
refusal count beside the fixed count" while the body never looks at printed output, so that sentence
should be corrected or the check folded into AC-4(d)'s once the real stdout assertion exists.

## Verification

**Happy path (the smoke test).** `run_lint(vault_path=<a materialized corpus copy with the AC-4
plants on top>, do_fix=True, quiet=True)` under `contextlib.redirect_stdout` prints ONE line reading
`Fix summary: repaired N, refused N, errored N, declined N, unreadable N`, every figure equal to the
number an independent `apply_fixes` over a second materialization of the same planted vault
computes, and the four bucket figures summing to the count of auto-fixable issues handed in.

**Failure modes that must degrade gracefully, each with its planted subject.** A note whose bytes do
not decode → reported as one non-auto-fixable `unreadable_note` issue, indexed, never repaired, never
moved. A note the semantic gate refuses → recorded once, printed once to stderr, the run continues
to the next file. A note whose frontmatter fence does not close → `errored`, NOT `refused`, and the
near-miss at `tests/test_lint_vault_fix_gate.py:251-274` still asserts where it did not go. A note
deleted between the walk and the pass → `errored` via the `FileNotFoundError` guard at `:853`, with
no sentinel directory minted at the vanished path. An issue whose branch guard declines → `declined`
with a `DECLINE_GUARDS` member naming which guard, and never re-labelled by a later frame-level
outcome on the same file.

**The counting wall ships its claimed match-shapes as fixtures (WI-235).** Three of this item's
oracles are COUNTS of structural matches, and a count says nothing about its matcher's reach:
`matches == 0` is satisfied identically by a predicate that resolves every claimed shape and by one
that resolves almost none. So each is driven through the wall's OWN predicate — never a
re-implementation — as a GREEN fixture on every floor run, each with a NEAR-MISS the predicate must
NOT match:

- `auto_fixable_emitter_checks` / `auto_fixable_branch_checks`: planted modules carrying a
  POSITIONAL `LintIssue("p", "x", S, "m", "c", auto_fixable=True)`, a KEYWORD
  `LintIssue(check="y", auto_fixable=True, ...)`, and an `issue.check == "z"` inside a function named
  `apply_fixes` — all three must be found. Near-misses that must NOT be found: `auto_fixable=False`;
  a `LintIssue(...)` with no `auto_fixable` keyword at all; an `issue.check == "q"` inside a function
  named anything else (the live instance of which is `quarantine_garbage:1125,1127`); the string
  `"field_type_mismatch"` in a comment or a docstring. And a planted `auto_fixable=SOME_NAME` must
  RAISE rather than be skipped.
- `person_tier_arm_counts`: a planted `classify_person_tier` with seven docstring bullets and five
  `return "active"` sites returns `(7, 5)`; one with a `return "stub"` and a `return SOME_NAME` does
  not count either as an active site; one with no docstring RAISES.
- The AC-5 readers (`baseline_sections`, `is_argv_fence`, `baseline_auto_fixable_rows`,
  `census_auto_fixable_rows`), whose oracles are match-shape claims over two committed artifacts and
  which fail the same way a count does when the matcher is narrower than its claim. Each is driven
  over the real committed bytes AND over planted text carrying the claimed shapes: a heading with a
  trailing qualifier matched by PREFIX; a fence whose first non-empty line is an absolute
  interpreter path recognised as ARGV; a bold totals row SKIPPED; a category parenthetical stripped.
  Near-misses each predicate must NOT match: a heading with a different ordinal; a stdout fence
  whose first line is `paths walked: 3952`; a 64-hex sha256 offered to the 40-hex delimited matcher;
  and `(suggest: '…')` offered to the category strip, which is not a `CATEGORY_ORDER` member and
  must survive as part of the key.
- `skip_reason_literal_sites` over the WIDENED universe: the near-miss battery at
  `tests/test_fixture_vault.py:487-503` already proves a comment, a prose docstring, a substring and
  an identifier are each invisible to it, and Task 8's non-vacuity clause proves
  `scripts/lint_vault.py` is actually IN the universe rather than the widening being a no-op.

**Mutate-and-observe, as the complementary half and never as the whole (WI-235).** Six mutations,
each observed RED and reverted, each recorded in the Build Log: revert `read_vault`'s append to
`continue` (AC-3 legs (a) and (b) red); make `person_missing_name` write `clean_person_name(stem)`
(AC-1's double-space discriminator red); drop the `meeting_missing_from_timeline` arm from the
`elif` ladder (AC-1(a)'s emitter≡branch equality red); hard-code any one figure in
`_format_fix_summary` (AC-4(d)'s two-vault variation clause red); delete one `return "active"` arm
from `classify_person_tier` (AC-2(c) red on the code-side count AND on that arm's planted specimen);
and match the baseline's section headings by EQUALITY instead of by prefix (AC-5(a) red on §1 and
§2, which carry trailing qualifiers) — the mutation that proves the prefix rule is load-bearing
rather than decorative, and the one whose absence is why the first pass at this correction shipped a
leg that was still RED against the committed artifact.

**Integration — downstream consumers that must still work.** None import this script (`scripts/` is
not a package and nothing in `obsidian_schemas/**` reaches it), so the consumer surface is the
package, which this item does not touch. The three consumer suites (HAL9000, exocortex,
orchestrator) are therefore NOT expected to move and are not part of this item's verification; the
conductor's ordinary cutover check remains available if the ship wants one.

**Regression — the enumeration, DERIVED from the edited surfaces rather than inherited (WI-238).**
Sweeping the resolved test roots for modules that name each `## Write Targets` path or the symbols
it exports returns, at FILE granularity: `tests/test_lint_vault_fix_gate.py` (loads the script by
path and asserts on `FixOutcome`); `tests/test_name_gate_refusals.py`,
`tests/test_name_gate_identifiers.py`, `tests/test_name_gate_delta_rule.py` (each asserts on
`outcome.fixed`); `tests/test_name_gate_wall.py` (pins `ArmId("scripts/lint_vault.py",
"apply_fixes", 1)` at `:96` and that function's arm COUNT at 1 at `:108`, and re-runs the `ast`
single-home wall at `:1136`); `tests/test_company_name_contract.py` (two-sided equality over
`frontmatter_write_arms(python_files_under(PACKAGE_ROOT, SCRIPTS_ROOT))` at `:602-616`, with the
script's arm classified `"excluded"` at `:533`); `tests/test_write_routing.py` (Walls A/B/C over the
same universe at `:91` and the loader wall at `:370`); `tests/test_address_splitter.py:102`
(address-splitting single-homed over the same universe);
`tests/test_vault_path_required.py` (the `obsidian_schemas`/`scripts` rglob for forbidden default
paths at `:321`, and the CLI subprocess battery at `:344-375`); `tests/test_identity_endgame.py`
(`:590`, `:782`, `:867`, `:1126-1173` — zero-site literal walls over
`python_files_under(PACKAGE_ROOT, TESTS_ROOT)`, which the new module JOINS);
`tests/test_loud_fail_harness.py:103` and `tests/test_fixture_vault.py:1309-1312` (the `ast`
single-home equality, which the new module joins); `tests/test_fixture_vault.py:508-514` and
`:1315-1318` (the skip-reason equality, which the new module joins AND whose universe Task 8 widens);
`tests/test_ac_interpreter.py:108-136` (every criterion of every doc in `WORK_ITEM_DOCS` re-run under
the `-S` foreign interpreter, which this item's five checks join at Task 15);
`tests/test_concurrent_access.py:599` (quarantine behaviour). Every one of these is a FLOOR measured
on 2026-09-15 and never a total — the derivation has under-reached at its reading step every time it
has been run, so anything Task 15's RUN returns that this paragraph did not name is NAMED in the
Build Log and satisfied, never worked around and never satisfied by narrowing a wall.

**Two standing equalities this design deliberately does not disturb, stated so a builder does not
trip them while "tidying".** `frontmatter_write_arms` must still report EXACTLY ONE arm for
`apply_fixes` — so the `write_frontmatter` call at `:953-955` stays where it is and no branch
acquires its own (A3b's rejection, re-stated as a build constraint). And
`NameGateRefusalRecord._fields` must still equal `{path, pattern}` — per-issue counting is obtained
by emitting one record per issue, never by widening that record.

**The incident replay — a CLOSE-OUT step, run outside the cage, not a plan task.** This item exists
because a real tool mis-reports on a real vault, so a fixture battery is not the whole of
verification. At `ready -> done` the conductor re-runs `scripts/lint_vault.py --vault $VAULT --report`
(and the `-q` summary) on the post-build tree and appends the result to
`docs/lint-vault-live-baseline.md` §4, whose command list and figure names are already committed as
bytes. `--report` and never `--fix`: mutating Dave's vault is a separate authorization this item does
not ask for, so the replay drains no production state. It is prescribed as a ship condition and NOT
as a plan task for the reason the cage makes structural — a caged builder's writes outside its
worktree are reverted at the merge boundary, so a plan-task replay would change nothing and report
success. What the diff must show: the five auto-fixable counts unchanged from the entry run; the
five stem-keyed counts moved by exactly what the newly-indexed unreadable stems explain (zero
movement is the expected result on a snapshot whose undecodable count is 0, and a movement without
that explanation is the finding); the `unreadable` figure equal to the entry run's undecodable scan;
and the summary line carrying all five figures. The unmuted output is redacted to counts before it
is recorded, exactly as the entry run was — no filenames, no note bytes, no absolute vault path.

## Scope Boundary

**What we are NOT doing.**

- **Preserving hand-formatted YAML.** `apply_fixes` re-serializes frontmatter through
  `obsidian_schemas/writer.py:write_frontmatter` -> `yaml.dump`, and so does every other write path
  in the package. A formatting policy implemented in this script would be a second home for a
  package-wide rule, and the fix that would actually work — a comment-preserving round-trip — is a
  dependency change with blast radius across HAL9000, exocortex and orchestrator. It is its own item
  against `writer.py` (A3), and Dave's sign-off question 1 is whether to mint it.
- **Skipping the frontmatter rewrite on a body-only fix.** Tempting and one-line-looking, and it is
  not: dropping the `write_frontmatter` call on a branch REMOVES a member from
  `frontmatter_write_arms`, which two frozen wall sets pin by equality (A3b). Deferred with its
  reason so it is not re-explored.
- **Fixing `parse_error` notes, or widening the auto-fixable set.** The five rules the script ships
  are the five this item proves; a sixth is what AC-1(a)'s derived equality exists to catch, not
  something this build adds.
- **Making `--quarantine` safer.** The item PINS `classify_person_tier` and the two
  `garbage_candidate_*` detectors against their declared definitions; it does not change what they
  decide, and `vault_io.move_note` at `:1140` is untouched.
- **Turning `scripts/lint_vault.py` into a package export.** That is `WI-030
  lint-vault-package-export` (at `idea`), and constraint 1 names the path-loader as the seam it will
  repoint.
- **Adding a header to `scripts/migrate_person_to_discuss.py`.** The Problem section asks for it;
  it is one-shot, already run, and worth no AC here. Fold it into WI-030 or leave it.
- **Retries, transactions, or a resume file for a partial `--fix` run.** Named so the four buckets
  are not mistaken for the beginning of a job queue.

**Unchanged files — the builder should not touch these.** Everything under `obsidian_schemas/**`
(the package gains nothing and loses nothing; `SKIP_REASONS` is IMPORTED, never extended);
`tests/fixtures/vault/**` and `tests/fixture_vault.py` (the corpus is byte-frozen behind
`CORPUS_DIGEST` and the plant-on-a-materialized-copy design exists precisely to avoid a digest
regeneration paired with a pool-table row across the cage boundary — A2);
`docs/vault-shape-census.md` (byte-frozen by `CENSUS_DIGEST`; AC-5 READS it, and the `(structural)`
annotation on the `Empty name` row stays as it is — the mapping is keyed on the message shape
instead); `docs/lint-vault-live-baseline.md` (the conductor's entry measurement; the builder reads
it and the conductor fills §4 at ship); `pipeline-runners.yaml`, `CLAUDE.md`, `SESSION_LOG.md` and
`state/**` (outside the cage's allowlist, conductor-owned).

## Risk Analysis

This is an operator tool Dave points at his own vault, so the risk register is short but the top
entry is real.

**R1 — the four-bucket refactor changes what `apply_fixes` does to a note, not just what it
counts.** *Likelihood: low. Impact: high — a wrong repair on a live note.* The disposition rule
moves the `repaired` fold from `:949` to the end of the lock block and adds a per-branch decline
record; both are bookkeeping, and no branch's repair logic, no `delta` key, no gate call and no
`write_note` argument changes. *Mitigation:* the WI-021 battery
(`tests/test_lint_vault_fix_gate.py`, five checks over guard / delta / refusal / two-equalities /
near-miss) runs unchanged except for the field rename, so any behavioural drift in that frame is red
there before AC-4 is written; and the `delta` key set stays closed at `{auto_created, name}`, which
`:169-182` asserts from the captured call rather than from the spec. *Rollback:* the whole item is
additive to a script nothing imports — reverting the commit restores the current behaviour with no
migration.

**R2 — a `read_error` `VaultFile` reaches a consumer written against the wider contract and
mis-fires.** *Likelihood: low. Impact: medium — a spurious issue on a healthy note, i.e. the defect
this item exists to remove, re-introduced one level over.* The triage is exact and is in the design
rather than in the build: `no_frontmatter:308` is the ONE real risk and is handled above it;
`orphaned_note:722`, `possible_duplicate:733-735` and every completeness check gate on
`vf.entity_type`, which stays `""`; `check_timeline` never iterates `files`. *Mitigation:* AC-3(c)
asserts the silence of all of them rather than only the guarded one, so a fourth consumer nobody
triaged is red.

**R3 — the live vault has drifted since the baseline, and the item ships on stale premises.**
*Likelihood: certain in one rule and already measured — `missing_body_sections` is 821 in the census
and 835 in the baseline. Impact: low, once the drift is visible.* *Mitigation:* AC-5(b)'s tolerance
rule, ruled this round — census-zero rules strict, census-non-zero rules sign-preserving, the delta
asserted against the artifact's own delta column — makes drift a number on the screen rather than a
premise rotting under a signature, and the exit half of the bracket re-measures at ship.

**R4 — the floor gets slower.** *Likelihood: certain. Impact: low and disclosed.* Joining
`WORK_ITEM_DOCS` adds five `-S` subprocess re-execs per floor run (six exist today for WI-021 and
WI-023), and the new module adds seven checks that each materialize 53 notes into a temp directory.
The floor is ~10s today. *Mitigation:* none sought — the wall's own docstring discloses this cost as
the price of proving the bridge by execution, and the alternative (a second copy of the loop, which
WI-016 wrote) is worse.

**Migration path.** None. Nothing persists between runs, no on-disk format changes, and the vault's
notes are written in exactly the shape they are written today.

## Acceptance Criteria

Draft, originated cold-start in approval-only mode, re-derived from the frozen `## Intent`. **NOT
yet frozen** — they are frozen by Dave's review and signature through the `/review-spec` surface
(`bin/review-spec-helper.py review --wi-id WI-026 --project <path>`), which is what writes the
`ac-signoff` fence. Every `check` is a top-level zero-argument `def test_*(` in
`tests/test_lint_vault_fix_rules.py` that signals failure by raising, per the battery's
direct-invocation contract (`tests/support.py:1-19`), and that module calls
`ac_interpreter.ensure_project_interpreter(__file__)` as its first statement because all five
EXECUTE the library.

AC-1 through AC-4 are hermetic by necessity (the caged builder must be able to discharge them);
AC-5 is the criterion that stops the SET from being hermetic, by reading back the conductor's
live-vault measurement. The exit half of that bracket is a declared ship condition rather than a
sixth criterion, for the reason A7 gives — no criteria kind exists that can carry a post-build act,
and inventing one would point an automated battery at Dave's vault.

```criteria
id: AC-1
desc: EVERY auto-fixable rule the script ships repairs to a declared oracle, and the rule set is DERIVED from the script's own syntax rather than listed. Three legs. (a) THE DERIVATION, and it is TWO-SIDED — a new scan in `tests/derivations.py` (the single legal home for `ast` in this tree) returns the set of `check` string literals passed to a `LintIssue(...)` construction that also passes `auto_fixable=True` (the EMITTERS, `lint_vault.py:341,357,386,530,596`) and, separately, the set of string literals compared against `issue.check` inside `apply_fixes` (the BRANCHES, `:888,896,903,911,929`); the criterion asserts those two sets are EQUAL and NON-EMPTY, so an emitter advertising a repair no branch performs, and a branch no emitter can reach, are each RED — neither is detectable today, and the equality is the invariant this leg ships. (b) THE ORACLE TABLE IS TOTAL OVER THAT SET — the test module declares one entry per rule id and asserts its key set EQUALS the derived set, so a sixth rule added later fails this criterion until someone writes its oracle rather than joining the untested set silently. (c) EVERY RULE REPAIRS TO ITS DECLARED VALUE, driven through `apply_fixes` against a `materialize_vault()` copy of the frozen corpus with specimens planted on top, each rule's expected post-fix state read from the definition stated HERE and NEVER from a second reading of the implementation: `field_type_mismatch` — the reparsed `auto_created` is the BOOL of `:891`'s own truth set, asserted on BOTH arms (`"yes"` → `True` AND `"no"` → `False`, the false arm being the member the corpus cannot supply and the one an always-True stub fails); `person_missing_name` — the written `name` is `fpath.stem.lstrip("@")` BYTE-FOR-BYTE and not a cleaned form, discriminated by a planted stem carrying the corpus's whitespace-damage shape, a DOUBLE SPACE, which `clean_person_name` collapses (`name_cleaning.py:197`) and which `gate_write` passes untouched because it is a predicate on `name` and not a transform (`name_gate.py:366-367`) — and the planted stem is a NEW one (`@Tarnquil  Brenvik.md`, pool-certified tokens in a combination no corpus file uses) and NEVER the corpus's own `@Dave  Marrowyn Fennwick.md`, which exists, carries a well-formed `name:`, and would be destroyed by the plant along with the evidence that this rule stays silent on a healthy double-spaced stem (constraint 7); `missing_body_sections` — every heading `get_expected_sections(type)` names is present in that order AND the content already sitting under the sections that already existed is still there byte-for-byte, discriminated by a planted note carrying some-but-not-all sections with real content under them (a build that writes the default body wholesale is RED, which is the WI-126 shape); `meeting_missing_from_timeline` — the appended entry equals `_build_timeline_entry`'s declared format (`### <%B %-d, %Y of the meeting's date>` then `[[<stem>|Meeting]]`, with ` - ` and the first THREE topics joined by `, ` and a trailing `.` when the meeting declares topics and neither when it declares none), discriminated by a planted meeting with FOUR topics, one with none, and a person whose Timeline already holds an entry that must survive; `broken_wikilink` — both `[[old]]` and `[[old|alias]]` retarget to the resolved stem, and a link whose date matches TWO meetings is NOT rewritten (`:523`'s `len(candidates) == 1`), the ambiguous case being pure plant.
why: The item's whole remaining promise is "a fixture-vault test for every fix rule it ships", and both halves of that sentence are load-bearing in a way a hand-written list cannot deliver. A list of five ids is the WI-131 single-literal gap wearing a test's clothes: the sixth rule someone adds next year joins the untested set and nothing goes red. Deriving the class from the script's own syntax makes future members join automatically — and deriving it from BOTH sides catches a defect class nothing in this repo can see today, because the emitter list and the branch list are two hand-kept sets that agree at five members purely by luck. Leg (c) exists because a derived sweep proves MEMBERSHIP and never correctness (WI-286): a stub that reports every rule "covered" while asserting nothing about the bytes satisfies (a) and (b) completely. So every rule gets an oracle whose expected value comes from a definition this document states, and every rule gets a member the live corpus cannot supply — the false arm of the boolean, the name that must NOT be cleaned, the sections that must NOT be flattened, the fourth topic, the ambiguous link. Four of the five rules have ZERO subjects in the frozen corpus (audited above), so "plant the discriminating member" is not belt-and-braces here, it is the only way any of them is exercised at all.
check: test_every_auto_fixable_rule_repairs_to_its_declared_oracle
kind: test
```

```criteria
id: AC-2
desc: EVERY DETECTOR THAT CAUSES A WRITE is pinned, in both directions, against the frozen corpus and against planted subjects — and the pinned set is the SEVEN write-causing checks, not the five auto-fixable ones. THE PINNED SET, stated once: the five members of AC-1's derived auto-fixable set, PLUS `garbage_candidate_person` (`:673-683`) and `garbage_candidate_company` (`:685-719`), which are INFO and NOT auto-fixable but are the sole input to `quarantine_garbage` (`:1218` → `:1112-1144` → `vault_io.move_note` `:1140`) and therefore the checks that RELOCATE a note. Three legs. (a) NO FALSE POSITIVES ON REAL-SHAPED DATA, COUNTED PER PAIR AND NOT MERELY MEMBERSHIP — running the full battery (`read_vault` → `build_indexes` → all five `check_*` functions) over a materialized copy of the frozen corpus with NOTHING planted, the MULTISET of `(filename, check)` pairs whose check is in the pinned set is collapsed to a mapping `(filename, check) -> ISSUE COUNT` and that MAPPING equals a declared table in the test module. The vehicle is a count and not a set because the corpus's one firing rule is many-to-one and a set cannot express it: `check_timeline:578-602` emits one issue per (meeting, attendee) pair keyed on `pvf.path`, the five well-formed meetings declare EIGHT attendee entries between them, and three of the five named attendees sit in two meetings each — so the corpus fires `meeting_missing_from_timeline` **8 TIMES OVER 5 DISTINCT PERSON NOTES** (`@Thrandell Ibberly` 2, `@Isolde Quenlaw` 2, `@Morvette Harkwell` 2, `@Caldreth Zebrant` 1, `@Elowick Varnholt` 1; `Meeting 20260212 - Zebrant Dalquest.md` is the malformed-frontmatter specimen, so `fm={}` leaves `entity_type == ""` and it never enters the `meetings` index at `:187-192`). A build emitting one issue per PERSON rather than per PAIR drops three issues and is green against a set-of-pairs assertion — which is exactly the over/under-fire class this criterion exists to catch — and is RED against the count. The other SIX pinned checks are asserted to fire ZERO times across all 53 notes, INCLUDING the three skip specimens and the diacritic, hyphenated, postal-address, digit-named and stem-divergent members. The 8-over-5 figure is a property of the frozen corpus, whose bytes are pinned by `CORPUS_DIGEST`, so it moves only when that digest does. The two `garbage_candidate_*` zeroes are real rather than accidental: `auto_created` occurs nowhere in the corpus and both arms gate on a truthy `auto_created` (`:245-253`, `:691-694`). (b) EVERY MEMBER OF THE PINNED SET FIRES ON ITS OWN PLANTED SUBJECT — one planted specimen per member producing exactly one issue carrying that check id at exactly that path, including a planted `auto_created: true` stub person and a planted `auto_created: true` company with no website, no industry, no Notes, no People links, no referencing person and no timeline meeting; so leg (a)'s six zeroes are proved to be silence rather than blindness. (c) THE MOVE PREDICATE IS PINNED ARM BY ARM — `classify_person_tier` (`:233-283`) decides which person notes leg (b)'s quarantine arm relocates, and its definition is the SIX disjuncts its own docstring states (`:236-242`): auto_created false or missing; ≥2 meeting wikilinks in Timeline; non-empty To Discuss or Notes; ≥1 meeting AND a non-empty `emails`; ≥1 meeting AND a non-empty `company`; ≥2 `^### ` headings in Timeline. The test module declares one planted specimen per disjunct that is `active` BY THAT DISJUNCT ALONE — every other disjunct false — plus one specimen satisfying none, which must be `stub`; an implementation missing any arm returns `stub` for that specimen and is RED, which is the mis-classification that MOVES a live note. The enumeration is a declared NARROWING, not a derivation (the disjunction is four `if` statements over six conditions and has no table to iterate), so it is BOUND to the stated definition by syntax ON BOTH SIDES — the docstring alone does not hold the property this leg needs. A scan in `tests/derivations.py` returns TWO numbers for `classify_person_tier`: the count of `- ` bullets in its own docstring Constant (SIX today, `:236-242`) and the count of `return "active"` sites in its body (FOUR today, `:253`, `:276`, `:279`, `:282`), and the criterion asserts BOTH against the numbers the test module's arm table declares. The code-side count is the load-bearing half: a seventh arm added as a fifth `if …: return "active"` moves it whether or not the author touches the docstring, which the bullet count alone cannot see — the bullets stay at 6, the table stays at 6, and the untested arm ships. The bullet count is the other direction: a disjunct documented but never implemented. WHAT THIS BINDING DOES NOT CATCH, stated so the criterion promises only what it delivers: an arm added by widening an EXISTING `if`'s condition (`if meeting_count >= 2 or has_manual or fm.get("vip")`) moves neither number, because it adds no `return` site and no bullet. That residue is the price of a narrowing over a hand-written disjunction and it is bounded — six documented conditions across four returns — where the alternative is a derivation this shape does not admit. THE EQUALITY IN (a) IS OVER THE PINNED SET ONLY — the INFO/WARNING issues the corpus legitimately raises (`orphaned_note`, `person_no_email`, `person_not_in_company_people`, `parse_error` and the rest) are outside it, because pinning those would couple this criterion to every check in the file rather than to the seven that cause a write.
why: This is the half the item has never named and the half that can lose data. A detector that mis-fires does not produce a wrong report, it produces a wrong WRITE — and the worst of those writes is not a repair, it is a MOVE. That is exactly why the pinned set is seven and not five: the first draft of this criterion rested its whole justification on `--quarantine` relocating files off the same issue list, and then pinned only `auto_fixable=True` pairs — which excludes both `garbage_candidate_*` checks and leaves `classify_person_tier`, the predicate that decides which person notes get relocated, ending this item exactly as untested as it started. A criterion frozen by signature whose stated reason for existing is a hazard it does not cover is worse than one that admits the gap. Widening costs almost nothing: both garbage ids pin at zero on the corpus today for a structural reason, so leg (a) grows by two rows, and leg (b) by two plants. All seven check functions have zero tests today; the two reached at all are reached by a gate sweep that asserts nothing about what they decided. Leg (a) is the only assertion in the suite that would notice a detector that started firing on notes it should ignore, and the frozen corpus is the right subject for it: 53 notes whose shapes were MEASURED from the live vault rather than invented, carrying exactly the accents, hyphens, address-in-a-name and stem/name divergences that make a naive check over-fire. Leg (b) is what stops (a) being satisfiable by a build in which the checks return nothing at all — an empty issue set passes any "these six fire zero times" assertion, and the pairing is what makes the zeroes mean something. Leg (c) is the same argument one level down: leg (b) proves the quarantine check fires on an obvious stub, which a `return "stub"` implementation also satisfies; only the per-arm table can tell a correct classifier from a wrong-but-self-consistent one, and the cost of getting it wrong is a real note in `_quarantine/`. Its syntax binding is two-sided for a reason found by attacking the criterion's own wording: an earlier draft counted only the docstring's bullets and then claimed "a seventh arm added with or without a docstring line is RED", which is false of that mechanism — an arm added as a fifth `if …: return "active"` with no bullet leaves every number in the assertion unchanged, and the arm with the largest blast radius in the file would ship untested behind a green criterion. Counting the `return "active"` sites from the same scan is one more line and closes exactly that hole; the widened-condition residue that remains is named in the desc rather than papered over, because a criterion frozen by signature must not promise a guarantee its mechanism lacks — that is the same defect as blocking 2 above, one level in from scope and down at wording. Leg (a)'s VEHICLE was corrected on 2026-09-15 by the spec-writer, answering the data-premise gate's finding 3, and the correction is a STRENGTHENING rather than a change of promise: the leg always meant "these detectors fire exactly on their declared subjects and nowhere else", and a set of `(filename, check)` pairs cannot say that about a rule whose emission is many-to-one. The gate EXECUTED the corpus rather than trusting the exploration's own NOT-EXECUTED note and found 8 issues over 5 distinct person notes — three attendees sit in two meetings each — so under the old vehicle a build emitting one issue per person instead of one per pair satisfied the criterion while dropping three issues, which is the precise failure the leg's `why` claims to catch. The number is written into the desc rather than left to the build's first run, because a count nobody recorded is a value the check does not hold.
check: test_every_write_causing_detector_fires_exactly_on_its_declared_subjects
kind: test
```

```criteria
id: AC-3
desc: A note whose bytes cannot be decoded is REPORTED, stays in the INDEX, and is never repaired or moved. Four legs, all driven by a planted non-UTF-8 note in a materialized corpus copy. (a) REPORTED — the run emits exactly one issue for that note, it is NOT auto-fixable, and its message carries a reason value that IS one of `obsidian_schemas.repositories.base.SKIP_REASONS` (specifically `UNREADABLE`), read from the imported constant rather than re-spelled as a literal in the script or in the test; and the vocabulary wall's UNIVERSE is widened to reach the script WHILE ITS TWO DECLARED-HOMES SETS STAY AT TWO MEMBERS — the two-member equality holding WITH `scripts/` inside the universe is the assertion, and it is the one that actually proves the script IMPORTS the reason rather than transcribing it. What gets edited is NOT the derivation — `skip_reason_literal_sites` (`tests/derivations.py:1583-1606`) already accepts an arbitrary `files` iterable and needs no change — but the TWO hand-typed call sites that pin the universe as `python_files_under(PACKAGE_ROOT, TESTS_ROOT)`: `tests/test_fixture_vault.py:508-509` and `:1302` (whose `universe` local feeds the deliberate re-run at `:1315-1318`). BOTH move to `python_files_under(PACKAGE_ROOT, TESTS_ROOT, SCRIPTS_ROOT)`; BOTH expected sets stay EXACTLY `{"obsidian_schemas/repositories/base.py", "tests/test_fixture_vault.py"}` (`:510-514` and `:1315-1318`). ADDING THE SCRIPT'S PATH TO EITHER EXPECTED SET IS FORBIDDEN BY THIS LEG AND IS ITSELF RED, and the reason is the derivation's own predicate: it reports a file IFF one of its parsed `ast.Constant` nodes is a `str` EQUAL to a vocabulary member, so an `import` of `SKIP_REASONS` and an attribute access `SKIP_REASONS.UNREADABLE` contribute no such Constant and a CORRECTLY-written `scripts/lint_vault.py` is ABSENT from the reported set — a three-member equality would be greenable only by hand-typing `"unreadable"` in the script, which is the exact drift the first half of this leg forbids, so the criterion must not be dischargeable that way. NON-VACUITY, because a universe widened to nothing is green for the wrong reason: the criterion also asserts `scripts/lint_vault.py` is IN the universe both call sites pass (`python_files_under` walks `rglob("*.py")` on disk, `derivations.py:183-197`; `SCRIPTS_ROOT` is `:31`). Extending one call site and not the other leaves a half-extended wall that reads green, so the criterion asserts on both. TWO FACTS THAT MAKE THE WIDENING SAFE TODAY, both read off this tree so the builder is not widening blind — `scripts/` holds no string literal equal to any `SKIP_REASONS` member (case-insensitive grep over `scripts/` for `unreadable`, `schema-drift`, `malformed-frontmatter`: no matches), so the two-member equality is green BEFORE the `read_error` path lands and becomes load-bearing after it; and `:1302`'s `universe` local also feeds the `ast` single-home wall at `:1309-1312`, where `scripts/` contains no `ast` use at all (grep over `scripts/`: no matches), so the same widening STRENGTHENS that wall — `{"tests/derivations.py"}` stays the answer with two more files in scope — rather than reddening it. The shared local is therefore an asset, not a hazard. (b) INDEXED — the note's STEM is present in `build_indexes(...)["all_stems"]`, and the discriminator is a second planted note whose BODY carries `[[<that stem>]]` plus a planted meeting listing that person as an attendee: today both produce issues (`broken_wikilink`, `meeting_attendee_not_found`) and after this change neither does, which is the leg that separates "the skip is loud" from "the report stopped lying about OTHER notes" — a build that prints a warning and still drops the file is RED here and green on (a). (c) QUIET OTHERWISE — no other check emits any issue for that path. Exactly ONE of those is a real risk and the criterion says which, so the build adds the guard it needs and not the four it does not: `no_frontmatter` (`:308`) fires on `vf.is_at_prefixed and not vf.frontmatter`, and a `read_error` `VaultFile` carrying `{}` frontmatter with an `@`-prefixed stem lands on it unless `check_structural` handles the read error ABOVE it — the same position and shape as the existing `if vf.parse_error: … continue` at `:297-305`. By contrast `orphaned_note` (`:722`), `possible_duplicate` (`:734`) and every completeness check are already safe BY CONSTRUCTION, because each gates on `vf.entity_type`, which stays `""` for a note whose bytes never parsed; the criterion asserts their silence without the build guarding for it. (d) NEVER WRITTEN — the unreadable note appears in no `--fix` target and in no `--quarantine` move. It carries no auto-fixable issue at all, so it never enters `apply_fixes` and sits OUTSIDE AC-4's per-issue partition by construction; it is accounted for by AC-4(d)'s separate unreadable-note count, which is the FIFTH PRINTED FIGURE on the summary line and not a fifth bucket — AC-4(d) is the leg that counts it, and this pointer names that leg rather than AC-4(c), which is the two-new-records leg and counts nothing.
why: `except Exception: continue` at `:117-118` is the last silent swallow on this path, and the currency note is right that it needs closing — but the reason it needs closing is not tidiness. The bytes are unrecoverable; the FILENAME is not, and it is discarded with them, so five checks keyed on the stem index (`broken_wikilink :513`, `meeting_attendee_not_found :482`, `person_company_not_found :463`, `company_people_link_broken :497`, `orphaned_note :722`) start reporting phantom breakage about notes that are perfectly fine. One of those phantoms is auto-fixable: a broken wikilink with a unique same-date meeting candidate gets REWRITTEN, moving a live link off a target that exists. That is why leg (b) is the criterion's centre of gravity and why the discriminating specimen is planted rather than sampled — the corpus's own non-UTF-8 member (`@Isolde Varnholt.md`) is linked to by nothing, so the corpus alone cannot tell a build that indexes the stem from one that does not. Leg (a) reuses WI-020's vocabulary rather than inventing a parallel one because `SKIP_REASONS` is already the answer to "what does a batch loader do with a note it cannot load", already exported, and already bound to its own function's returns by two syntax scans; a fourth spelling of "unreadable" in this repo is the drift WI-016 Task 11 spent three edits removing. And the SHAPE of leg (a)'s wall edit — universe widened, expected sets held at two — is the whole point rather than a detail, because the earlier draft of this leg got it backwards and would have shipped a criterion whose only green ran through the defect: it told the builder to grow both declared-homes equalities by the script's path, which `skip_reason_literal_sites` can only report once the script hand-types the literal, so a builder who imported correctly failed a criterion Dave had signed and a builder who typed `reason = "unreadable"` passed every wall in the suite. That is LESSONS #46 at design time — a check reachable two ways, one of them the defect, is not evidence about the defect — and it is worse than a check that is merely weak, because it INSTRUCTS the regression. Holding the expected sets at two while the universe grows inverts it: the equality is now a statement ABOUT the script (it is scanned and it is not a home), it is green today for a reason this leg states rather than by accident, and the only edit that reddens it is the one the leg exists to catch.
check: test_an_unreadable_note_is_reported_indexed_and_never_silently_dropped
kind: test
```

```criteria
id: AC-4
desc: A `--fix` run ACCOUNTS for every auto-fixable ISSUE it was handed — the four per-ISSUE outcomes PARTITION, and the operator's summary line shows all of them. Four legs. (a) THE PARTITION IS PER ISSUE AND OVER FOUR BUCKETS — {repaired, refused, errored, DECLINED}, `declined` being an issue whose repair branch was reached and whose own guard chose not to act. Driven over a planted vault carrying a subject for each: one repairable note; one note the semantic gate refuses (the `unknown_contact` stem shape WI-021's own fixture uses); one note whose frontmatter fence does not close (a `FrontmatterParseError`, the near-miss that is NOT a gate refusal); one issue whose target was deleted between the walk and the pass (the `FileNotFoundError` guard at `:853`); and one subject per DECLINE SITE, all five of which are named here so the plant set is closed rather than sampled — `field_type_mismatch` whose `auto_created` is already a bool so `isinstance(raw, str)` is False (`:890`); `missing_body_sections` on a type `get_expected_sections` returns `[]` for (`:906`); `meeting_missing_from_timeline` driven through `apply_fixes` with `idx=None`, the signature's OWN DEFAULT at `:828`, which declines every such issue at `:913` (315 live if any caller ever takes that default); `broken_wikilink` whose `suggested_fix` is not JSON (`:935-936`); and `broken_wikilink` whose `old` link text appears nowhere in the file, which falls through `:963-973` incrementing nothing. THE ASSERTION: the number of auto-fixable issues handed in EQUALS repaired + refused + errored + declined, the four sets are pairwise disjoint BY ISSUE IDENTITY (the tie-break that makes disjointness decidable is leg (b)'s, and it is stated there rather than left to the builder), and each is non-empty in this run. (b) THE ATTRIBUTION RULE, BECAUSE TWO BUCKETS ARE RAISED AT FRAME LEVEL OVER A FILE HOLDING SEVERAL ISSUES — an issue's bucket is decided where the write carrying it commits, never by its file's terminal state. The gate raises at `:947` before `fixed += file_fixed` at `:949`, so every issue on a refused file is `refused` and none is `repaired`. The SECOND write is not covered by that ordering: the wikilink pass at `:960-975` runs after the fold, so the discriminating plant is ONE file carrying both a `missing_body_sections` issue (repaired, committed at `:957`) and a `broken_wikilink` issue whose write raises — the first is `repaired`, the second is `errored`, and a build that labels FILES rather than issues gets this wrong by construction. THE TIE-BREAK, STATED SO TWO INTERNALLY-CONSISTENT BUILDS CANNOT DISAGREE: **a DECLINE is attributed at its BRANCH, at the moment its own guard chose not to act, and is NEVER re-labeled by a later frame-level outcome on the same file** — so an issue that declined at `:890`/`:906`/`:913`/`:935-936`/`:963-973` stays `declined` even when a sibling issue's delta then makes the gate raise at `:947`, and it stays `declined` when the per-file handler at `:993` catches an IO failure instead. The reason is not convention: a declined issue contributed NOTHING to `delta`, so it is not in the write the gate refused and not in the write that errored, and its guard id — the record leg (c) requires — is the only true statement anyone can make about why it did not repair. Calling it `refused` would attribute it to a gate that never saw it and would make "refused N" un-actionable. The DISCRIMINATING PLANT is one file carrying BOTH: a `meeting_missing_from_timeline` issue driven with `idx=None` so it declines at `:913`, AND a `person_missing_name` issue whose path-derived name is Tier-1 dirty so `gate_write` raises at `:947` — the first issue must land in `declined` with its guard id and the second in `refused`, and a build whose attribution rule reads "every issue on a refused file is refused" is RED on this file rather than silently pinning a different partition than the one signed here. (c) THE TWO NEW RECORDS ARE TYPED LIKE THEIR SIBLING — both are closed records matching `NameGateRefusalRecord`'s discipline at `:805-818` and the message bound `errors.py` states. The error record carries the path and a BOUNDED reason (the exception's class name or a `SKIP_REASONS` member), never `str(exc)` of an arbitrary exception and never note bytes. The declined record carries the path, the issue's `check` id, and a GUARD ID drawn from a declared CLOSED SET whose members are exactly the five decline sites in leg (a) — so "declined 315" resolves to `meeting_missing_from_timeline / no-meeting-index` and is something an operator can act on. And the refusal bucket keeps its exact-type filter, so the corrupt-fence specimen lands in ERRORED and NOT in refused — the near-miss `test_lint_vault_fix_gate.py:251-274` already asserts where it did not go, now extended to say where it DID. (d) THE OPERATOR SEES IT, AND THE CRITERION READS THE PRINTED BYTES — the summary line at `:1198` carries all four counts plus the count of notes skipped as unreadable (AC-3), and this leg is discharged ONLY by CAPTURING REAL STDOUT, never by inspecting `FixOutcome`'s fields. THE MECHANISM, stated because the cheap read of this leg is what leaves the print uncovered: the check calls `run_lint(vault_path=<a materialized+planted copy>, do_fix=True, quiet=True)` inside `contextlib.redirect_stdout(io.StringIO())` — `redirect_*` and not `capsys`, because the battery's checks are zero-argument functions with no pytest fixtures (`tests/support.py:1-19`), and `redirect_stderr` is already this neighbourhood's idiom (`test_lint_vault_fix_gate.py:260-261`); stderr is captured too and kept separate, because the refusal and error prints go to STDERR (`:992`, `:994`) while the summary goes to STDOUT. THE ASSERTION IS A STRUCTURAL PARSE AND A CROSS-CHECK, not a substring match: the captured stdout is parsed into a mapping of five declared labels → integers, all five labels must be present, and the five integers must EQUAL the figures the same run computed — the four bucket sizes obtained by driving `apply_fixes` over an identical SECOND materialization of the same planted vault through the issue list `run_lint` itself builds (`read_vault` → `build_indexes` → the five `check_*` fns → the `auto_fixable` filter, exactly `:1160-1192`), plus AC-3's unreadable count, which is the one from the PRE-fix `read_vault` at `:1160` and not from the post-fix re-scan at `:1201`, because the line reports the pass whose fixes it is announcing. TWO-SIDED, over a SET of at least two planted vaults with different figure vectors: each of `repaired`, `refused`, `declined` and `unreadable` must take at least two DIFFERENT values across the set and match the cross-check every time, so a hard-coded line, a line that prints only two of the five, and a line whose fifth figure is a constant are each RED. Every one of those four is producible END-TO-END through `run_lint`'s own issue list and the plants are named so the set is closed rather than hoped for: `repaired` — any `missing_body_sections` subject; `refused` — an active person note with an empty `name` whose stem is Tier-1 dirty, so `check_completeness:382` emits and `gate_write` raises; `declined` — an `@`-prefixed note whose body carries `[[Meeting 20260104 Nonexistent ]]` with an INNER TRAILING SPACE while exactly one meeting file bears date `20260104`, so `check_links:510` strips the target and emits a fixable repair whose `old` text (`Meeting 20260104 Nonexistent`) then appears nowhere in the file and falls through `:963-973` incrementing nothing; `unreadable` — AC-3's planted non-UTF-8 note. WHAT THIS LEG DOES NOT REACH, stated so the criterion is satisfiable and honest: `errored` cannot be produced through `run_lint`'s own issue list at all — a corrupt-fence note emits the non-fixable `parse_error` issue and never enters `apply_fixes` (`:297-305`), and the `FileNotFoundError` guard at `:853` needs a deletion between the walk and the pass — so for `errored` this leg asserts only that its LABEL is present carrying an integer (0 is a legal value), and its VALUE is covered at the `apply_fixes` frame by legs (a)–(c).
why: A `--fix` pass can end an issue's life in four ways and counts one and a half of them. The IO/parse failures print (`:993`) and are tallied nowhere, so "Fixed 0 issues, refused 0" is exactly what an operator sees when every note errored — the summary lies by omission, in the direction that reads as success. The DECLINED bucket is the one this criterion originally missed and the one that matters most: three buckets over a four-state space is not a partition, and the state left out is the only one that produces no output at all. Every one of the five branches has a guard; an issue that hits one raises nothing, refuses nothing, repairs nothing, `changed` stays False and no count moves — indistinguishable in every channel the tool has from a clean repair. That is precisely what the Intent forbids, and AC-1(a)'s two-sided emitter≡branch equality does not reach it, because that catches a branch that does not EXIST, never a branch that exists and declined. Stating the partition PER ISSUE rather than per file is the second correction and it is not cosmetic: `FixOutcome.fixed` counts issues (the field this item renames to `repaired`, ruled in the `## Write Targets` handoff note precisely because that name's issues-versus-files ambiguity is what produced this correction), and the wikilink arm increments the run counter at `:972` outside `file_fixed` entirely, so a file repaired only by a link rewrite has `file_fixed == 0` and any build computing "fixed files" from the outcome drops that file out of every bucket while the equality still balances. Per-issue is what the code already counts, it keeps the equality total, and it is the only framing under which leg (b)'s mixed file is expressible at all. Leg (c) exists because the cheap way to build (a) is a bucket of stringified exceptions, which walks note content straight into an operator-facing summary that gets pasted into chat — the exact channel `errors.py`'s bounded-message contract exists to close — and because WI-021 chose a closed record here for reasons that have not changed; the declined record's guard id is bounded for the same reason and is what turns a number into an action. Leg (b)'s TIE-BREAK is the third correction and it exists because two internally-consistent builds disagreed on it: a decline and a gate refusal can co-occur on ONE file, the decline having happened inside the per-issue loop and the refusal at `:947` after it, and nothing in the earlier text said whether that issue keeps its `declined` label or is swept into `refused` by an attribution rule reading "every issue on a refused file is refused". Both readings satisfy pairwise disjointness, so the criterion would have pinned whichever the builder happened to choose — and a `check:` written by the same hand would agree with it either way. Attributing the decline at its branch is the reading the guard-id record already implies and the only one that is TRUE of the frame: the declined issue put nothing in `delta`, so it was never in the write the gate refused. Leg (d) is what makes any of it reach the human, and it is the leg most easily written so that it does not: a count that exists only in a returned tuple is not accounting, it is bookkeeping. The precedent for getting this exactly wrong is already in the file this item edits — `test_lint_vault_fix_gate.py:276-281`'s `test_the_fix_outcome_surfaces_both_counts` carries a docstring saying "the CLI surfaces the refusal count beside the fixed count" and then asserts `FixOutcome._fields == ("fixed", "refused")` and nothing else; no test anywhere under `tests/` calls `run_lint` or captures its stdout, so the CLI half of that sentence has never been checked. A leg (d) written to inspect the record rather than the printed bytes reproduces that gap under a signature: four green buckets, and an operator staring at a real `--fix` run sees a line indistinguishable from today's. The Intent's promise is "know, FROM WHAT THE TOOL TELLS THEM", and the print at `:1198` is the only channel that phrase has — which is why this leg captures stdout, parses it structurally, and binds every figure to the number the same run computed rather than to a sentence someone wrote.
check: test_every_auto_fixable_issue_is_accounted_for_and_the_printed_summary_says_so
kind: test
```

```criteria
id: AC-5
desc: The LIVE-VAULT BASELINE is committed, shaped, and cross-checked against the frozen census — the entry half of A7's bracket, read back off the tree rather than trusted. Four legs, all over `docs/lint-vault-live-baseline.md` (the second `kind: precondition` fence in `## Write Targets`, a conductor measurement that must be in git HEAD before the criteria are frozen). (a) PRESENT AND SHAPED, WITH MEASURED AND DERIVED SECTIONS HELD TO DIFFERENT CONTRACTS, AND EVERY PREDICATE BELOW EXECUTED AGAINST THE COMMITTED BYTES BEFORE IT WAS WRITTEN — the file exists and carries FIVE sections, matched by HEADING PREFIX and never by heading equality, because two of the five headings carry a trailing qualifier the artifact is entitled to: `## 0. The run`, `## 1. The five auto-fixable counts` (followed by ` (vs …, measured 2026-09-07)`), `## 2. The five stem-keyed check counts` (followed by ` (pre-change baseline)`), `## 3. The undecodable scan`, `## 4. Post-build attestation`. It carries the tree's 40-hex HEAD SHA EXACTLY ONCE IN ITS HEADER — the region ABOVE the `## 0. The run` heading (`docs/lint-vault-live-baseline.md:12`) — with the match DELIMITED at both ends by a non-hex character, and the ONCE is scoped to that region rather than to the file for two reasons that are both properties of bytes this document can already see: §0 carries a 64-hex `sha256` of the report's stdout (`:26`), inside which an undelimited `[0-9a-f]{40}` finds twenty-five matches, so an undelimited scan reads RED against a correct file; and §4's figures table reserves a `post-build HEAD` row (`:158`) that the conductor FILLS with a second 40-hex SHA at `ready → done`, so a file-scoped ONCE would go RED on every floor run after this item's own close-out — and this check runs on every floor run forever, not once at the ship. Each MEASURED section (§0 and §3) carries AT LEAST TWO fenced blocks: at least one ARGV fence, whose first non-empty line is an absolute path to a python interpreter — that is the element carrying the re-executability this contract is actually about, the `docs/company-name-corpus-audit.md` shape, so any reader can run it and contradict the number rather than take it on trust — and a LAST fence holding verbatim stdout, whose first non-empty line is NOT such a path (§0: argv `:22-24`, argv `:30-32`, stdout `:34-70`; §3: argv `:111-117`, stdout `:119-122`). NEITHER MEASURED SECTION IS REQUIRED TO CARRY A `Command:` LINE AND THIS LEG MUST NOT LOOK FOR ONE — §0 spells its introduction `Command (the JSON report; …):` and §3 carries no such line at all, so that element, kept from the original wording by this round's first pass, was ITSELF still RED against the committed artifact and is dropped here rather than left for the build to discover. And each DERIVED section (§1 and §2) carries NO fenced block at all, ONE markdown table, and a derivation sentence above that table naming the report its numbers come from (§1 `:74-75`, "Derived from the JSON report …"; §2 `:93-95`, "… from the same report"). THE SPLIT IS THE POINT AND IT IS A CORRECTION, ruled 2026-09-15 by the spec-writer against the artifact as committed rather than against the artifact this leg was drafted to imagine: §1 and §2 hold no command, no argv fence, no stdout fence and no per-section SHA, because they are read off §0's single JSON report, and re-running a command for each would be a second walk of Dave's vault for numbers §0 already contains. The artifact made the right call; the leg described a different artifact, and a builder discharging the old wording literally would have had to edit the frozen entry measurement — the one file this item is not allowed to reshape after the fact. (b) CROSS-CHECKED AGAINST THE FROZEN CENSUS, UNDER A STATED TOLERANCE — §1's five counts are compared rule by rule against `docs/vault-shape-census.md:272-281` under `CENSUS_DIGEST`, so the ledger cannot be rewritten by the party it audits. THE TOLERANCE, ruled 2026-09-15 with the measured drift in front of the ruling rather than deferred to build time: a rule whose CENSUS count is ZERO must still be ZERO in §1 — strict equality, because AC-1's "this rule has no live subject" argument and AC-2's false-positive floor both lean on those two zeroes, and a rule that acquired a live subject falsifies an argument this document makes; a rule whose census count is NON-ZERO must still be NON-ZERO — the SIGN is pinned and the magnitude is free, because a vault that churns moves those counts weekly and a rule that fell to zero would falsify the other half of the same argument; and in BOTH directions the DELTA is asserted rather than merely tolerated — the leg computes `baseline − census` per rule and requires it to EQUAL the delta column the artifact's own §1 table carries, so a drift silently mis-stated in the artifact is RED even when both endpoint numbers are legal. Any failure names the rules and BOTH numbers and both measurement dates. AS THIS RULE STANDS AGAINST HEAD IT IS GREEN, and that is the test of the ruling rather than a happy accident: `docs/vault-shape-census.md:277` carries 821 and `docs/lint-vault-live-baseline.md:79` carries 835 for `missing_body_sections` (both non-zero, delta column `+14`), 315/315, 19/19, 0/0 and 0/0 for the rest. A `kind: test` criterion that goes RED against a frozen, correct, already-committed artifact is a FAILING acceptance criterion and not a dashboard signal, which is what the earlier "a divergence is RED" wording made it — the criterion's intent was always "a drifted vault is VISIBLE rather than silently trusted", and reporting a divergence and failing on one are two different mechanisms for it. TWO THINGS THIS LEG NEEDS THAT DO NOT EXIST YET, declared here as decisions rather than left as the builder's discoveries. FIRST, A FIFTH CENSUS READER: WI-016's four typed readers are `census_class_rows` (`tests/test_fixture_vault.py:121`), `census_pool_rows` (`:139`), `census_meta` (`:144`) and `census_identity_residue` (`:380`), and every one of them parses a `census-*` FENCE — none reads the auto-fixable table, which is a plain markdown table at `:275-281`. So this leg ships a fifth reader beside them, in the same module, parsing that table's rows into `(message shape, int)` pairs and raising on a non-integer count or a duplicate shape exactly as `census_class_rows` does; it rides the same whole-file `CENSUS_DIGEST` fixity, which is over the file's bytes and is unaffected by a new reader, so this is an addition and not a design question. It is a WRITE TARGET in `tests/test_fixture_vault.py`, which constraint 8 already makes a paired target for two other reasons. SECOND, A DECLARED SHAPE→RULE-ID MAPPING, because that table's key column is a MESSAGE SHAPE and not a rule id, so "compared rule by rule" has no join without one: `Missing sections: …` → `missing_body_sections` (emitter `:357-363`), `Attended [[…]] but it's not in Timeline` → `meeting_missing_from_timeline` (`:596-602`), `auto_created is string '…' instead of bool` → `field_type_mismatch` (`:341-347`), `Empty name (suggest: '…')` → `person_missing_name` (`:386-392`), `[[…]] doesn't resolve (fixable → [[…]])` → `broken_wikilink` (`:530-538`). Five hand-kept rows, which is acceptable at that size, and they are BOUND rather than merely written: the mapping's VALUE set must equal AC-1(a)'s derived rule set, so a sixth auto-fixable rule reddens this leg until someone decides whether the census covers it. THE MAPPING IS KEYED ON THE MESSAGE SHAPE AND NEVER ON THE TABLE'S PARENTHETICAL CATEGORY, and that is a finding rather than a preference: the census annotates `Empty name (suggest: '…')` as `(structural)` while the emitter's own category field is `"completeness"` (`:388`) and its check function is `check_completeness` — a mapping keyed on the parenthetical would mis-join that row. The census is digest-frozen, so the annotation is NOT to be corrected there; the counts are what the row carries and what this leg reads. AND THE RULE THAT SEPARATES THE TWO, because two of the five shapes carry parentheses of their own (`Empty name (suggest: '…')`, `[[…]] doesn't resolve (fixable → [[…]])`) and "never on the parenthetical" is undecidable without it: the reader strips a TRAILING parenthetical group IFF its content is a member of `scripts/lint_vault.py:CATEGORY_ORDER:1003` — the script's own five-member category vocabulary, read from the loaded module rather than re-spelled — and strips nothing otherwise, so `(structural)`, `(timeline)` and `(links)` come off while `(suggest: '…')` and `(fixable → [[…]])` stay as part of the key. The stripped category is DISCARDED and never joined on, which is what makes the `Empty name` mis-join impossible rather than merely unlikely. Two facts about that table were read off the census's committed bytes rather than assumed and make the rule well-defined: in every one of the five rows the category parenthetical sits OUTSIDE the backticked shape span (`` `Missing sections: …` `` then ` (structural)`), so stripping it can never truncate a shape; and `structural`, `timeline` and `links` — the three categories the five rows use — are all members of `CATEGORY_ORDER` (`scripts/lint_vault.py:1003`), so all five strips fire and none of the two shape-internal parentheses does. THIRD, A READER FOR THE BASELINE'S OWN §1 TABLE, whose row shape is NOT the census's and was likewise read off the committed bytes: the table at `docs/lint-vault-live-baseline.md:77-84` has four columns (rule, census count, today's count, delta) and SIX rows, the last of which is a TOTALS row (`**total auto-fixable**` / `**1,155 of 4,730**` / `**1,169 of 4,764**` / `+14 / +34`) carrying no rule id, which MUST be skipped rather than parsed — a reader that takes every row meets `1,155 of 4,730` where it expects an integer and is RED against a correct artifact — and it is skipped BY THAT PROPERTY, its first column carrying no backticked identifier, never by a hardcoded row index, so a sixth rule row inserted above it cannot shift the skip onto a real rule. The rule id is the FIRST backticked span in column 1, which tolerates the fifth row's trailing "(the fixable → sub-case)" annotation; the census cell is the LEADING integer before its parenthetical message shape (`821 (…)` → 821); today's cell is an integer; the delta cell is a signed integer (`+14`, `0`); and every integer is parsed with `,` removed, because the artifact writes thousands separators in that totals row and in §2. This reader lands in the new check module rather than beside the census readers, because the baseline is this item's own evidence and nothing else reads it. ITS COUPLING, DECLARED IN ONE LINE because this check reaches into `docs/**` at run time: it pins the committed TEXT of two conductor-owned artifacts — one of them digest-frozen — and consumes no behaviour of any module and no shape of any live population, so an ordinary ship cannot move what it reads. (c) THE UNDECODABLE COUNT IS PRESENT, TYPED AND CLEAN — §3 carries an integer ≥ 0, read from the `undecodable: <n>` line of its STDOUT FENCE (`:121`, 0 today), and that FENCE contains no `/Users/` path and no `.md` filename, because the privacy wall reaches this artifact the way it reaches the census: the count is the finding, the filenames are the operator's business and never the repo's. THE SCAN IS THAT FENCE AND NEVER THE SECTION OR THE FILE, and the reason is in the committed bytes rather than in taste: §3's ARGV fence legitimately carries `rglob('*.md')` and `/usr/bin/python3`, and §0's fences and the file header carry the project interpreter's own absolute `/Users/…` path by design — so a section-wide or file-wide scan for `.md` or for `/Users/` is RED against a correct artifact, while what the privacy wall actually forbids is a vault path or a note filename in a captured OUTPUT, which is exactly what the stdout fence holds. (d) THE EXIT OBLIGATION IS COMMITTED AS TEXT — §4 exists and carries the commands the post-build run must use and the literal names of the figures it must fill, in the shape the artifact actually committed: THREE numbered re-run commands as INLINE code spans (`:135-137` — the `-q` summary, the `--report` run and the §3 one-liner) and NOT a fenced block, so §4 is neither a MEASURED nor a DERIVED section under leg (a) and this leg must not demand a fence of it; and a three-column figures table (`:141-158`) whose `figure` column names every figure §§1-3 measured — the assertion is that every member of AC-1(a)'s derived rule set appears in that column and that `paths walked` and `undecodable` do too, so a rule added later cannot slip out of the exit obligation — and whose third column is the `exit` column the conductor fills. THE LEG ASSERTS PRESENCE AND NEVER EMPTINESS — the section, its three commands and its figure names must be PRESENT; the `exit` cells are unasserted in both directions. That is a decision and not an omission: the exit column is empty at battery time by construction, but the conductor FILLS it at `ready → done` on this very item, so a leg asserting emptiness would go RED at its own close-out, on an artifact that had just been completed exactly as this document prescribes — the same defect shape as leg (b)'s "a divergence is RED", one artifact over, and it is refused here rather than discovered there.
why: This is the criterion that stops the acceptance set from being 100% hermetic, which is what the first draft of this document shipped and what LESSONS #27 and the WI-064 scar say never survives contact with real data. `lint_vault.py`'s correctness is DEFINED by its behaviour on 4,730 live issues across a real vault, and the failure that matters for a linter — the false positive on the shape nobody drew a fixture from — lives in the tail no 53-note fixture contains; ruff and ESLint both pair a fixture corpus with an ecosystem run for exactly this reason and this design was shipping only the first half. Leg (b) is the load-bearing one and it is not ceremony: this document's ENTIRE argument for covering all five rules rather than only the ones that fire rests on a five-row table measured on one day in a vault that churns, and nothing currently re-reads it. Leg (b) makes a drifted vault a RED with two numbers on the screen instead of a premise quietly rotting under a signature — the WI-042 staleness class, closed by a comparison rather than by remembering to look. It also names the two things it needs and does not have — a reader for the census's markdown table (the four existing readers are all fence-parsers) and a shape→rule-id mapping, since the table is keyed on message shapes — because an earlier draft of this leg said "read through WI-016's own census reader" and no such reader reaches that table; a criterion frozen by signature that names a mechanism which does not exist is a build-time discovery, and this one comes with a live trap worth spending three lines on: the census annotates the `Empty name` row `(structural)` while that emitter's own category is `"completeness"`, so a mapping keyed on the parenthetical instead of the shape mis-joins one row in five and the count it cross-checks is the wrong rule's. Leg (c) is why the artifact can exist in the repo at all. Leg (d) exists because an exit act that lives only in prose evaporates: committing the command and the figure names as bytes turns the ship step into a re-run, and its absence into something a reader can see. The entry measurement also settles, by execution, the question this document previously routed to Dave as a sign-off judgement call — how many of his notes are undecodable — which is AC-3's whole subject population and which no human can answer from memory. BOTH OF THIS CRITERION'S MECHANISMS WERE CORRECTED ON 2026-09-15 by the spec-writer, answering the data-premise gate's two blocking findings, and the shape of the defect they shared is worth naming because it is the reason that gate stands between `exploring` and `specced`: AC-5 was WRITTEN as the fold answering the architect's round-1 blocker, describing an artifact that did not yet exist, and the conductor's measurement landed afterwards — nobody re-read the criterion against the bytes that arrived. That is the WI-042 staleness class with a five-day fuse. Leg (a)'s four-element rule was never satisfied by §1 and §2, which are derived tables and carry none of it, so the leg described a different artifact and its only literal discharge was editing the frozen entry measurement. AND THE FIRST PASS AT THAT CORRECTION DID NOT FINISH IT, which is recorded here rather than quietly fixed because it is the same generator one turn later: narrowing the leg to "MEASURED sections carry a command line, an argv fence and a verbatim-stdout fence" kept the `Command:` element the gate had just shown to be absent — §3 has no such line and §0 spells it `Command (the JSON report; …):` — so the leg was still RED against the committed bytes for a third section. What produced BOTH misses is the same habit: the leg was written from what the contract OUGHT to require instead of from what the file HOLDS. So this pass stopped prescribing elements and instead executed a predicate against the committed bytes for every clause it kept, and swept the rest of the criterion the same way rather than stopping at the element in front of it — which is what turned up three more clauses nobody had raised: the heading match (two of five headings carry a trailing qualifier, so heading EQUALITY is RED), the SHA count (an undelimited 40-hex scan finds twenty-five matches inside §0's 64-hex sha256), and leg (c)'s privacy scan (§3's argv fence carries `rglob('*.md')` and the header carries an absolute `/Users/…` interpreter path, so any scope wider than the stdout fence is RED). Each of those would have been the next round's finding, and each is now a predicate this document states and has run. Leg (b)'s "a divergence is RED" was RED BY CONSTRUCTION the day it was signed: `missing_body_sections` is 821 in the census and 835 in the baseline, three days of ordinary vault growth, correctly recorded and openly labelled in the artifact's own prose. Neither correction weakens a promise. Leg (a) still requires every measured number to be re-executable and contradictable by a reader, and now says truthfully which sections are measured and which are derived from a measured one. Leg (b) still makes drift VISIBLE and now makes it ASSERTED — the strict arm on the two zero-count rules is new and is strictly stronger than the old wording's uniform equality was in practice, because the old wording could not survive its first ship and would have been relaxed at build time by whoever met it; and requiring the computed delta to equal the artifact's own delta column closes the gap a pure tolerance would have opened, where both endpoints are legal and the number the reader sees is wrong.
check: test_the_live_vault_baseline_is_committed_shaped_and_agrees_with_the_census
kind: test
```

### Examples of done

**Given** Dave points `--fix` at the live vault and 1,136 of the auto-fixable issues are body-only
repairs across hundreds of notes — **when** the run finishes — **then** the summary says how many it
repaired, how many the name gate declined, how many failed, how many it looked at and decided not to
touch, and how many notes it could not read at all, and the first four add up to exactly the issues
it set out to fix. **And** if the number that failed is "all of them", the line looks nothing like
the line a clean run prints. **And** the floor proves that by running the tool and reading the line
it actually printed — not by looking at the numbers inside the code, which is how the existing check
in this area got to claim the CLI shows something it has never once looked at.

**Given** a broken link the tool worked out the repair for and then quietly did not apply, because
the text it went looking for is not in the file the way the tool spelled it — **when** the run
finishes — **then** the summary counts that issue as `declined` and names the guard that declined
it, instead of printing "Fixed 0 issues, refused 0", which is byte-identical to what a vault with
nothing to fix prints today. **And** the same accounting covers the worst version of this: a caller
that takes `apply_fixes`' own default and passes no meeting index declines every one of the 315
live `meeting_missing_from_timeline` repairs at once, and that run says so rather than reporting a
clean pass over 315 notes it never touched.

**Given** an auto-created person note with one meeting and a real email address — **when**
`--quarantine` runs — **then** the note stays where it is, because that combination is one of the six
things the classifier calls "active"; and the floor goes RED if a future edit drops that arm, because
each arm has a planted note that is active by that arm alone. **And given** someone later adds a
seventh way to be "active" and never touches the docstring — **then** the floor still goes RED,
because the count of `return "active"` sites in the code moved even though the documentation did not.

**Given** one note that needs two repairs — one the tool looks at and decides not to touch, and one
whose name the gate refuses — **when** the run finishes — **then** the summary counts the first as
declined and the second as refused, not both as refused, because the tool says why each individual
issue ended where it did rather than labelling the whole file by whatever happened last.

**Given** the build lands and the conductor re-runs `lint_vault --report` over the real vault —
**then** the five auto-fixable counts match the baseline captured before the change, the stem-keyed
check counts have moved by exactly what the newly-indexed unreadable notes explain, and both numbers
are written down next to each other in a file anyone can re-derive with the command printed above
them. **And** if they do not match, the item does not ship on the strength of 53 green fixture notes.

**Given** a note in the vault that some other tool wrote in a non-UTF-8 encoding, and three notes
that link to it — **when** the linter runs — **then** it says it could not read that one note, and
it does NOT report the three healthy notes as carrying broken links to a file that is sitting right
there. **And** `--fix` never rewrites those three links, which is what today's run does when the
unreadable note's date collides with another meeting's.

**Given** the linter now has to say the word for "I could not read this" — **when** the floor runs —
**then** it passes only if the script gets that word by importing it from the one place the library
declares it, and goes RED the day someone types it out by hand in the script instead. The check does
that by putting the script inside the scan's reach while the list of places allowed to spell the word
stays at two — so "green" means "the script was looked at and is not one of them", never "nobody
looked".

**Given** someone adds a sixth auto-fixable rule to `lint_vault.py` next year and ships it with no
test — **when** the floor runs — **then** it goes RED, naming the rule id, because the rule set is
read out of the script's own syntax rather than from a list they would have had to remember to
update. **And given** they wire the emitter but forget the repair branch (or the reverse), the same
check goes red for that reason instead, which nothing in the repo can see today.

**Given** a future "helpful" edit that makes `person_missing_name` clean the name it derives from the
filename — **when** the floor runs — **then** the planted double-spaced stem goes RED, because the
oracle says the repair writes the stem byte-for-byte and the gate is a predicate rather than a
transform.

## AC Red-Team — 2026-09-10 (round 3)

**Referent read first, cold-start:** the frozen `## Intent` sentence and its 2026-09-10 sharpening,
`### Examples of done`, both currency audits, `## Exploration Notes` including A1–A7b and the eight
numbered constraints, all four architect rounds, my own round-1 and round-2 sections, the `### Revision
— round 3` note answering both gates, then the five `criteria` fences as they stand in this tree now,
then the cited code — read fresh rather than assumed from either prior round's memory of it.

**My rounds 1–2 folds, re-verified against the actual code rather than trusted from the revision's
prose — all held, plus the round-3 revision's fix for my own round-2 finding, independently
re-derived rather than accepted on the fold's word:**

- **AC-3(a) (the wall-direction trap).** The current text (`scripts/lint_vault.py` is not yet touched,
  so this is read against the criterion and the pre-build test file) now reads: both call sites move
  to `python_files_under(PACKAGE_ROOT, TESTS_ROOT, SCRIPTS_ROOT)`, both expected sets STAY at their
  current two members, and adding the script's path to either expected set is stated as itself RED. I
  re-read `skip_reason_literal_sites` myself (`tests/derivations.py:1583-1606`, plus its own docstring
  and the near-miss test at `tests/test_fixture_vault.py:487-503`, which asserts a comment/docstring/
  substring/identifier are each invisible to the scan): it reports a file iff a parsed `ast.Constant`
  string equals a vocabulary member, so an import or an attribute access contributes nothing, and the
  criterion's remedy is now the one edit that is actually true of the mechanism. Confirmed the two
  call sites are still unwidened on this tree (`tests/test_fixture_vault.py:508-509`, `:1302`,
  `:1315-1318`), so the criterion describes a real pending edit and not one already done.
- **AC-3(d) (the citation).** Now points at AC-4(d), the leg that prints the unreadable count, not
  AC-4(c) (the two-new-records leg, which counts nothing) — confirmed against AC-4(c)'s and AC-4(d)'s
  current text.
- **AC-5(b) (the reader and the mapping).** Both gaps the architect's round-3 non-blocking notes named
  are now declared in the criterion: a new census-table reader beside the four existing `census-*`
  fence parsers (re-confirmed `census_class_rows` `:121`, `census_pool_rows` `:139`, `census_meta`
  `:144`, `census_identity_residue` `:380` are all fence parsers, none reaching the plain markdown
  table at `docs/vault-shape-census.md:272-281`), and a declared five-row shape→rule-id mapping keyed
  on message shape rather than the table's parenthetical category. I independently re-verified the
  mis-join finding that motivates keying on shape: `person_missing_name`'s emitter sits in
  `check_completeness` and carries category `"completeness"` (`scripts/lint_vault.py:386-392`), while
  the census row annotates it `(structural)` (`docs/vault-shape-census.md:280`) — a mapping keyed on
  the parenthetical would misjoin exactly that row. The other four rows' categories match their
  parentheticals (`field_type_mismatch` and `missing_body_sections` are genuinely `"structural"` at
  `:341,357`; `meeting_missing_from_timeline` is `"timeline"` at `:596`), so this is a real single-row
  trap and not a made-up one. Confirmed the five census counts (821/315/19/0/0) and message shapes
  match `docs/vault-shape-census.md:275-281` byte for byte against what AC-5(b) quotes.
- **My round-1 findings (AC-4(d)'s print, AC-4(b)'s tie-break, AC-2(c)'s two-count binding)** — spot
  re-verified again this round rather than assumed stable: `:1198`'s print is still the bare two-field
  format, `apply_fixes` still raises the gate at `:947` before folding `fixed` at `:949`, and
  `classify_person_tier`'s docstring still states six disjuncts (`:236-242`) against four
  `return "active"` sites (`:253,276,279,282`). All held.

So: **prior held, on every clause across two prior rounds** — nothing reopened.

**Fresh attack this round, treating the round-3 revision's own new prose as unverified rather than
trusting the fold.** I re-derived, independently and against the actual code rather than the document's
narrative, the load-bearing citations across all five criteria that neither prior round had reason to
re-check because the text had not moved there: AC-1's five emitter/branch line numbers (`:341,357,386,
530,596` and `:888(≈890 mismatch branch),896,903,911,929` — all confirmed against the actual `elif`
ladder in `apply_fixes`), `_build_timeline_entry`'s exact format string including the `topics[:3]`
truncation and the with/without-topics branch (`:782-802`, byte-exact match to AC-1(a)'s prose),
`WIKILINK_PATTERN`'s and `check_links`'s strip-then-match behavior that makes the inner-trailing-space
wikilink a real decline plant (`:60,495,509-524` — traced the capture group through `.strip()` at `:510`
myself rather than accepting the architect's trace), both `garbage_candidate_*` sites and their shared
`auto_created`-truthy gate (`:673-719`), `quarantine_garbage`'s move path (`:1112-1144`), and
`NameGateRefusalRecord`'s closed two-field shape as the sibling AC-4(c)'s new records must match
(`:805-818`). Every one is accurate. Nothing in this pass surfaced a citation drift, a wall-direction
trap, or a criterion satisfiable by a wrong-but-plausible implementation that the prior two rounds had
not already found and the fold had not already closed.

One thing noticed and judged non-material: AC-5's desc labels the new reader "A SIXTH CENSUS READER" in
its own header phrase, then immediately describes it as "a fifth reader beside them" (WI-016's four
existing fence readers plus this one is five, not six) in the very next sentence — an internal
off-by-one in the desc's own wording. It does not affect what a builder implements: the operative
instruction ("ships a fifth reader beside them... parsing that table's rows... rides the same whole-file
`CENSUS_DIGEST` fixity") is unambiguous on its own, and nothing in AC-5(b)'s testable assertion turns on
the miscounted label. Flagging it so a future spec-writer pass can clean it up, not raising it as a
finding — this is the "worded imperfectly" case the calibration section says to let through, not the
"satisfiable while the Intent goes unserved" case this gate exists to block.

Nothing else in the set failed a fresh attack. AC-1's oracle table remains total, two-sided, and its
five per-rule plants were re-traced against the live branch code above. AC-2(a)'s zero-counts remain
structural and re-confirmed (`auto_created` absent from the corpus; both `garbage_candidate_*` gate on
it). AC-2(c)'s two-count binding is confirmed correct against the live function, including the
widened-condition residue named and bounded rather than hidden. AC-3(a)'s remedy is now the one edit
true of the mechanism, and AC-3(b)–(d) are otherwise unchanged from my prior passes. AC-4's four-bucket
partition, its attribution tie-break, its closed-record shapes, and its stdout cross-check (including
the newly-traced `declined` plant) all hold. AC-5's shape contract, its census cross-check, and its two
previously-missing mechanisms (reader, mapping) are now declared and internally consistent modulo the
cosmetic label noted above.

```verdict
gate: ac-red-team
verdict: PROMOTE
date: 2026-09-10
model: claude-sonnet-5
note: Third red-team pass, cold-start — re-derived every load-bearing citation across all five criteria against the live code myself rather than trusting the fold; the round-3 revision correctly implements the AC-3(a) wall-direction fix, the AC-3(d) citation fix and the AC-5(b) reader+mapping declaration that closed my round-2 and the architect's round-3 findings, and a fresh attack surfaced nothing material — only a cosmetic "sixth reader"/"fifth reader" label slip in AC-5's desc that does not affect what is built.
```

## Architectural Review — 2026-09-10 (round 4)

**Recommendation: PROMOTE to architected**

### Trigger check

Fired for the reasons rounds 1–3 recorded, and `## Approach`'s "Routing: architect" paragraph reads
the trigger table correctly. Nothing turns on it this round.

### My round-3 blocker, re-read against this tree — CLOSED, and closed on the mechanism rather than on the paraphrase

I read `skip_reason_literal_sites` myself (`tests/derivations.py:1583-1606`) rather than re-checking
the fold's account of it. Its body is the whole finding: it walks `ast.walk(tree)` and adds
`module_id(path)` **iff** a node is an `ast.Constant` whose `.value` is a `str` *in* the wanted set
(`:1601-1605`) — equality over parsed syntax, so an `import` and a `SKIP_REASONS.UNREADABLE`
attribute access contribute no such Constant, and its own near-miss battery
(`tests/test_fixture_vault.py:487-503`) proves the point four ways. The rewritten AC-3(a) is now the
one edit that is true of that mechanism, and it is right on all four sub-claims I checked:

- Both universe sites are still unwidened on this tree and are exactly where the leg says:
  `python_files_under(PACKAGE_ROOT, TESTS_ROOT)` at `tests/test_fixture_vault.py:508-509` and again
  at `:1302`.
- Both declared-homes equalities are two-member and are the sets the leg says must NOT move:
  `:510-514` and `:1315-1318`, each `{obsidian_schemas/repositories/base.py, tests/test_fixture_vault.py}`.
- The leg now states that adding the script's path to either expected set is ITSELF red. That is the
  clause that converts my finding from "un-suggested" to "refused", and it is the difference between
  a criterion that merely stops instructing the regression and one that catches it.
- The two safety facts are real, and I re-ran both greps rather than trusting them: a
  case-insensitive scan of `scripts/` for `unreadable` / `schema-drift` / `malformed-frontmatter`
  returns nothing, and `scripts/` uses `ast` nowhere — so the shared `universe` local at `:1302`
  carries the widening into the `ast` single-home wall at `:1309-1312` as a strengthening
  (`{tests/derivations.py}` stays the answer over a larger universe), exactly as the leg claims. The
  non-vacuity clause is the right addition and neither gate asked for it.

My three round-3 notes are all actioned, and note 2's answer is better than the note: the field-name
question I flagged as unanswered is RULED (`FixOutcome.fixed` → `repaired`) with the cheaper
alternative recorded rather than silently dropped, and the inventory that ruling implies was READ
rather than estimated. I re-derived it independently and it holds — `.fixed` is touched at
`test_lint_vault_fix_gate.py:117`, `:166`, `:201`, `:270`, `:279` and `:281` (the last being
`empty.fixed`, which a grep for `outcome.fixed` misses, and the note catches it), plus
`test_name_gate_refusals.py:275`, `test_name_gate_identifiers.py:425` and
`test_name_gate_delta_rule.py:203`. Nine sites across four modules, all inside `tests/**`. The AC-5(b)
mis-join that motivates keying the census mapping on the message shape is also real and I confirmed
it at the emitter: `person_missing_name` carries category `"completeness"`
(`scripts/lint_vault.py:388`) while `docs/vault-shape-census.md:280` annotates that row
`(structural)`.

### The frame, re-checked cold rather than assumed stable across three rounds

The seam and the accounting are the two load-bearing claims and both re-verify at the byte level.
`VaultFile` is `:88-97` with `parse_error` last; the swallow is `except Exception: continue` at
`:115-118`; `build_indexes` keys `all_stems` / `stem_to_file` / the three type indexes / the meeting
date index off `vf.stem` at `:179-197`, which is why the discarded filename — not the discarded bytes
— is the defect. One fact worth recording that no round has: `raw_content` (`:96`) is WRITTEN at
`:151` and read nowhere else in the file, so a `read_error` `VaultFile` carrying an empty
`raw_content` has no second consumer to break. AC-3(c)'s guard triage is exact: `no_frontmatter`
(`:308`) fires on `is_at_prefixed and not frontmatter` and is the one real risk, while
`orphaned_note` (`:722`) and `possible_duplicate` (`:734`) both gate on `vf.entity_type` and are safe
by construction — and `check_structural`'s `parse_error` arm at `:297-305` is the position and shape
the new guard mirrors. On the accounting side: the five branches at `:888/896/903/911/929`, five
decline guards at `:890`, `:906`, `:913`, `:935-936` and the fall-through at `:963-973`, the
unconditional `gate_write` at `:947` landing before `fixed += file_fixed` at `:949`, the second write
at `:960-975` with its own `fixed += 1` at `:972` outside `file_fixed`, the uncounted print at
`:993-994`, and `FixOutcome(fixed=..., refused=...)` at `:996`. `person_missing_name` at `:896-901`
has no guard at all, which is why it correctly does not appear in AC-4(a)'s decline set, and `:897`
really is `fpath.stem.lstrip("@")` — the byte-for-byte oracle AC-1(c) pins.

### Review

**Fit:** Unchanged from round 2 and re-confirmed rather than carried forward. The seam fix is a
`read_error` sibling to `parse_error` on a dataclass that already has four consumers written against
that shape; the vocabulary is imported from `repositories/base.py:41-48`; `ast` stays single-homed to
`tests/derivations.py`; the two new records match `NameGateRefusalRecord`'s closed-field discipline
(`:805-818`). The round-3 field rename is the same instinct applied to naming: one spelling per
bucket across the record, the print and the guard vocabulary, paid for in nine mechanical edits
inside the item's own write authority.

**Duplication:** Still actively removed. The `"unreadable"` fourth spelling is now refused by an
edit whose only red state IS the drift — which is a stronger position than round 2's, where the same
leg would have instructed it.

**Boundaries:** The Phase-3 answer holds and is the document's best decision. The structure discarded
is the filename at `read_vault:115-118`, where "a `VaultFile` per note" narrows to "per note I could
decode" while five stem-keyed consumers are written against the wider contract; the fix is at the
seam, not at the five reconstructions. `scripts/` stays a script and the `WI-030` coupling stays
named as constraint 1 rather than pre-emptively refactored.

**Determinism boundary:** No LLM capability here, so the sibling reading applies — mechanical work
must not rest on a human remembering. AC-1(a) derives the rule set from both sides of the script's
own syntax; AC-2(c) now binds its one knowing narrowing to TWO code-side numbers and names the
widened-condition residue in the desc rather than overclaiming. That last move is the right shape:
replacing an overclaim with a smaller overclaim would have been the same defect one round later.

**Reversibility:** High and unchanged. Operator-invoked script, nothing imports it, both record
changes additive, and the one irreversible act in the neighbourhood (`quarantine_garbage` →
`vault_io.move_note`, `:1140`) is pinned rather than touched. Both live runs are `--report` and never
`--fix`.

**Generalization:** Calibrated. The derived rule set generalizes to rule six; the `classify_person_tier`
arm table deliberately does not and pays a two-sided syntax binding instead of pretending. A3's
YAML-formatting concern stays out with its blast radius priced.

**Cost & maintenance:** One session, no package code, no consumer blast radius, no new dependency,
two one-command conductor acts. The rename adds nine mechanical edits and the census reader adds one
parser beside four siblings — both bounded, both inside `tests/**`.

**Build vs extend vs integrate:** Extend throughout — `FixOutcome`, the `parse_error` shape, the
`skip_reason_literal_sites` universe, the census readers, and the corpus via `materialize_vault`
rather than by growing it.

**Prior art (outside view):** Answered in writing since round 2 and unchanged: ruff and ESLint each
pair a fixture corpus with an ecosystem run, and A7's bracket is what stops this design shipping only
the first half. The one divergence — the exit run is a conductor ship condition, not an automated
wall — rests on a cited code fact (`work_item_linter.py:167-171`, `:158`) rather than on reasoning,
and both rejected alternatives are recorded with the code that rejects them. No deferral hides behind
an unnamed re-entry condition.

### Notes (non-blocking)

Three, none wrong-as-written, all resolvable in speccing without reopening anything. Stating that
explicitly because rounds 3 and 2 both escalated a note on the standard that a clause which is FALSE
of its own mechanism must not reach Dave's signature — none of these is that. They are an
under-specified parse, an unreachable exemplar, and a label.

1. **The summary print sits inside `if fixable:` (`scripts/lint_vault.py:1191-1199`), so a `--fix`
   run with zero auto-fixable issues prints no line at all.** AC-4(d)'s two-vault variation
   requirement forces every planted vault to carry at least one fixable issue, so the leg is green
   without ever exercising that path — and a build that leaves the guard where it is passes. This is
   not a hole in the Intent: an unreadable note is reported as its own issue by AC-3(a), so it does
   not vanish from the report when the summary does not print. But the spec should decide
   deliberately whether the five-figure line prints unconditionally under `do_fix`, rather than
   inheriting the guard by accident.

2. **The second Example of done describes a run the CLI cannot produce.** `run_lint` passes `idx`
   at `:1194`, so `:913`'s `mstem in meetings` decline never fires through the CLI and no real run
   prints "declined 315". The document is scrupulous about exactly this class one criterion over —
   AC-4(d) states in writing that `errored` is not producible end-to-end and asserts it format-only —
   and half 3 states the `idx=None` condition correctly. The exemplar is the one place the condition
   is dropped. The criteria are unaffected (AC-4(d)'s reachable `declined` plant is the
   inner-trailing-space wikilink, which I traced through `:509-524` → `:963-973` and which does fire
   through `run_lint`), so this is a one-clause exemplar fix, not a criterion defect.

3. **AC-5(b)'s reader has to separate the message shape from the category annotation on rows where
   the shape itself carries parentheses**, and the leg does not say how. Two of the five rows are
   like this — `Empty name (suggest: '…')` and `[[…]] doesn't resolve (fixable → [[…]])`
   (`docs/vault-shape-census.md:280-281`) — so "keyed on the message shape and never on the
   parenthetical category" needs a rule for which parenthetical is the category. It is decidable
   (the trailing group is always a member of the check-category vocabulary), which is why this is a
   note and not the round-3 class, but the leg's own lesson was that an undeclared mechanism becomes
   a build-time discovery. One sentence.

4. Cosmetic, and the red-team's round-3 pass flagged it too: AC-5(b) labels the new parser "A SIXTH
   CENSUS READER" and then calls it "a fifth reader beside them" one sentence later. Four exist
   (`tests/test_fixture_vault.py:121`, `:139`, `:144`, `:380`), so "fifth" is the right word.

```verdict
gate: architect
verdict: PROMOTE
date: 2026-09-10
model: claude-opus-5
note: My round-3 blocker closes on the mechanism rather than the paraphrase — `skip_reason_literal_sites` reports a file only on a string-literal Constant, so AC-3(a)'s rewritten universe-widens/expected-sets-hold shape is the one edit true of it, and naming the wrong edit as itself RED converts the leg from not-instructing the drift to catching it; the field-name ruling, the nine-site inventory and the census mis-join all re-derive correctly off this tree, the seam and accounting frames re-verify at the byte level, and the three residual findings are an under-specified parse, an unreachable exemplar and a label — none false of its own mechanism, so a fifth round buys nothing the spec-writer cannot.
```

## AC Sign-off

```verdict
gate: ac-signoff
verdict: PROMOTE
date: 2026-09-15
reviewer: dave
channel: cli
signed_at: 2026-09-15T14:23:24+01:00
provenance: verified
signoff_escalation: ESC-WI-026-specced-awaiting-ac-signoff-c376d8f5
ac_hash: 973d7a08f068
intent_hash: 6a7cccabd378
ac_hash_AC-1: 23030080e7eb
ac_hash_AC-2: bdb83849dd61
ac_hash_AC-3: 9bd601c3a0d4
ac_hash_AC-4: 5cc1a0cc3737
ac_hash_AC-5: 01784d0e28c1
artifact: docs/spec-reviews/WI-026-dave-review-2026-09-15-2.md
```

## Data Audit — 2026-09-15 (round 2)

**Recommendation: PROMOTE to specced**

### Trigger check

**Class 1 AND Class 2 again, unchanged from round 1.** Class 1: the criteria still quantify over two
corpora — the frozen 53-note fixture vault and Dave's live vault. Class 2: AC-5 is still a rule whose
correctness is defined by its effect against artifacts that ALREADY EXIST IN HEAD
(`docs/lint-vault-live-baseline.md`, `docs/vault-shape-census.md`), so "does this criterion discharge
green against the bytes on the tree today" has a measurable answer and it was measured rather than
reasoned about.

Round 1 raised three required groundings (2 blocking, 1 material). This round's job is the re-read:
did the fold close them, and did the fold's own new material — an entire spec body written this round
(`## Verified Diagnosis`, `## Design`, `## Implementation Plan`, `## Verification`, nine `writes`
fences) — introduce a fresh empirical defect. Every predicate below was executed against THIS tree
(worktree `cage-wt-ecmquixm`, HEAD `09ebc1c`); this gate has Read/Grep/Glob/Edit and no shell, so
every claim is read off bytes and nothing is estimated.

### Prior round's findings — each re-run against the bytes, all three CLOSED

**Grounding 1 (was blocking) — AC-5(b)'s tolerance. CLOSED, and green against HEAD.** The ruling is
the one the numbers support: census-zero rules strict, census-non-zero rules sign-preserving,
`baseline − census` asserted to EQUAL the artifact's own delta column. Re-executed rule by rule off
`docs/vault-shape-census.md:277-281` and `docs/lint-vault-live-baseline.md:79-83`:

| rule | census | baseline | computed delta | artifact's delta cell | verdict |
|---|---|---|---|---|---|
| `missing_body_sections` | 821 | 835 | +14 | `+14` | green (non-zero → non-zero) |
| `meeting_missing_from_timeline` | 315 | 315 | 0 | `0` | green |
| `field_type_mismatch` | 19 | 19 | 0 | `0` | green |
| `person_missing_name` | 0 | 0 | 0 | `0` | green (zero → zero, strict) |
| `broken_wikilink` (fixable sub-case) | 0 | 0 | 0 | `0` | green (strict) |

The delta-column clause is the part that earns its place: a pure tolerance would have passed a
mis-stated delta with two legal endpoints, and this does not.

**Grounding 2 (was blocking) — AC-5(a)'s shape contract. CLOSED, and the second pass inside the
round is what closed it.** Round 1's finding was that §1 and §2 satisfy none of the four demanded
elements. The narrowed leg was then re-run, clause by clause, against the committed bytes:

- FIVE sections by heading PREFIX — `:17`, `:72`, `:91`, `:104`, `:128`. §1's heading carries
  ` (vs …, measured 2026-09-07)` and §2's ` (pre-change baseline)`, so heading EQUALITY really would
  be RED and PREFIX really is load-bearing. ✓
- ONE 40-hex SHA, DELIMITED, in the HEADER region above `## 0. The run` — `:12`,
  `e0ffbe860937ec775d286521181358ccdd2aec06`, backtick-delimited at both ends, and it is the only
  40-hex run in `:1-16`. §0's 64-hex `sha256` at `:26` is outside the scoped region, which is what
  stops the twenty-five-match problem. ✓
- MEASURED sections carry ≥2 fences, an argv fence and a LAST stdout fence — §0 has three (`:22-24`,
  `:30-32`, `:34-70`), §3 has two (`:111-117`, `:119-122`). Each section's first fence opens with an
  absolute interpreter path (`/Users/…/.venv/bin/python`, `/usr/bin/python3`); each LAST fence's first
  NON-EMPTY line is not one (`Vault Lint Report — $VAULT` — note `:35` is blank, so "first non-empty"
  is the clause that saves it — and `paths walked: 3952`). ✓
- The `Command:` element is GONE, which is the specific thing round 1's finding could not have caught
  because the first pass at the fix re-introduced it: §0 spells it `Command (the JSON report; …):`
  (`:19`) and §3 carries no such line at all. ✓
- DERIVED sections carry NO fence, ONE table, and a derivation sentence naming §0's report — §1
  `:74-75` + table `:77-84`; §2 `:93-95` + table `:96-102`; zero fences in either. ✓
- §4 is neither MEASURED nor DERIVED and leg (d) demands no fence of it — its three commands are
  inline code spans at `:135-137` and its figures table is `:141-158`. ✓ The lifetime clause is also
  green as stated: `post-build HEAD` (`:158`) is the second 40-hex SHA the conductor will add, and it
  lives outside the header region the count is scoped to, so this floor member survives its own
  close-out.
- Leg (d)'s figure-column assertion — every member of AC-1(a)'s derived rule set plus `paths walked`
  and `undecodable` appears in that column: `:146`, `:147`, `:148`, `:149`, `:150`/`:154`, `:156`,
  `:157`. ✓
- Leg (c)'s privacy scan scoped to §3's STDOUT fence — `:119-122` holds `paths walked: 3952` and
  `undecodable: 0` and carries no `/Users/` and no `.md`; the argv fence above it legitimately carries
  both, so the scoping is load-bearing rather than fussy. ✓
- AC-5(b)'s two readers, run against the bytes they will parse: the census table at
  `docs/vault-shape-census.md:275-281` has its category parenthetical OUTSIDE the backticked shape in
  all five rows, and `structural` / `timeline` / `links` are all members of
  `scripts/lint_vault.py:CATEGORY_ORDER:1003` while `(suggest: '…')` and `(fixable → [[…]])` are not
  — so all five strips fire and neither shape-internal parenthesis does. The baseline's §1 table is
  four columns over six rows whose last is `**total auto-fixable**` carrying no backticked identifier
  (so the skip-by-property rule, not by index, is correct), row five's first backticked span is
  `broken_wikilink` ahead of its `` `fixable →` `` annotation (so "first backticked span" is correct),
  and the census cells are `821 (…)`-shaped (so "leading integer before the parenthetical" is
  correct). ✓

**Grounding 3 (was material) — AC-2(a)'s vehicle. CLOSED.** The leg now collapses to
`(filename, check) -> ISSUE COUNT` and writes the figure into the desc. Re-derived independently off
`tests/fixture_vault.py:361-382`: attendee entries 2 + 1 + 2 + 1 + 2 = **8**, over Thrandell Ibberly
(2), Isolde Quenlaw (2), Morvette Harkwell (2), Caldreth Zebrant (1), Elowick Varnholt (1) = **5
distinct person notes**. `Meeting 20260212` is the malformed-frontmatter specimen and never enters the
`meetings` index. The desc's roster matches mine name for name and count for count.

### The fold's own new material, swept for the defect the fold was fixing

The generator round 1 named was "a clause written from what the artifact OUGHT to hold, never
executed against the bytes that exist". The fold declares it closed by a RULE. That rule was tested
by re-running the other criteria's clauses rather than by trusting the sweep the fold reports:

- **The six zeroes AC-2(a) asserts.** `auto_created` appears zero times under `tests/fixtures/vault/`,
  and both `garbage_candidate_*` arms gate on a truthy `auto_created` (`:674-683`, `:689-694`), so
  both are zero structurally. `missing_body_sections` zero re-checked at the level that matters —
  not heading COUNTS but heading NAMES: per-file `^## ` counts are 3 / 4 / 6 / 2 / 6 / 1 across the
  53 notes, and spot-reads confirm the names are exactly `ENTITY_BODY_CONFIG`'s
  (`body_sections.py:303-324`) — `@Thrandell Ibberly.md:18-22` is To Discuss / Timeline / Notes,
  `@Voxleaf Ltd.md:11-17` is People / Timeline / Documents / Notes. A count-only check would have
  passed a note with three WRONG headings; this one does not.
- **The post-change corpus, which nobody had to look at before.** After Tasks 2–3 land, the corpus's
  own `@Isolde Varnholt.md` stops being dropped and becomes a `read_error` `VaultFile` inside the
  battery AC-2(a) runs. Walked every pinned check against it: `check_structural` emits
  `unreadable_note` and `continue`s (outside the pinned set); `check_completeness:372`,
  `check_links:455` and `check_noise:670` decline it under the widened guard;
  `orphaned_note:722` and `possible_duplicate:733-735` gate on `vf.entity_type`, which stays `""` —
  and `possible_duplicate` sits OUTSIDE the `:670` loop guard, so `entity_type` is the only thing
  protecting it, which is exactly what AC-3(c) claims and why that triage is right rather than
  lucky. Its stem joining `all_stems` moves no pinned count (the corpus has no body wikilink and
  Isolde Varnholt attends nothing). AC-2(a)'s table survives the change this item makes to the very
  battery it runs.
- **AC-4(d)'s `declined` plant, traced end to end rather than taken on the fold's word.**
  `[[Meeting 20260104 Nonexistent ]]` in an `@`-prefixed body: `check_links:509-510` finds the raw
  target and STRIPS it, `:513`/`:515` miss, `MEETING_DATE_PATTERN` matches, `meeting_date_idx["20260104"]`
  holds exactly one candidate (the corpus's five well-formed meetings carry five distinct dates), so
  `:523-524` sets `correct_stem` and `:530-537` emits a fixable repair whose `old` is the STRIPPED
  text — which then appears nowhere in the file, so `:963-973` falls through incrementing nothing.
  The plant is reachable and is a genuine decline.
- **AC-4(d)'s `refused` plant.** A person note with no `auto_created` classifies `active` at
  `:252-253`, an empty `name` reaches `check_completeness:382` and emits `person_missing_name`
  auto_fixable at `:386-392`, and `apply_fixes:897` derives the name from the Tier-1-dirty stem.
  Reachable.
- **The nine rename sites.** Grepped rather than counted from the note: `.fixed` at
  `test_lint_vault_fix_gate.py:117, :166, :201, :270, :281`, `test_name_gate_identifiers.py:425`,
  `test_name_gate_delta_rule.py:203`, `test_name_gate_refusals.py:275`, plus the `_fields` equality
  at `:279`. Nine, across four modules, exactly as the handoff note enumerates — and the four
  non-moving `.refused` sites (`:118`, `:200`, `:230-231`, `:265`) really do read `.refused`.
- **The rest of the citation frame the spec body newly leans on**, re-resolved: `VaultFile:88-97`
  with `parse_error` last and `raw_content` written at `:151` and read at no other site in the repo;
  `read_vault:115-118`; `check_structural:297-305`/`:308`; the five decline sites and the
  `:947` → `:949` → `:960-975` ordering; `run_lint:1160`, `:1191-1199` with the print inside
  `if fixable:` at `:1193` and the `"No auto-fixable issues found."` else-arm at `:1213-1214`;
  `classify_person_tier:233-283` with SIX `- ` docstring bullets at `:237-242` and FOUR
  `return "active"` sites at `:253`, `:276`, `:279`, `:282`; nine `auto_fixable` sites in the script
  of which exactly five are constructing and all five are the literal `True`; both universe sites
  (`tests/test_fixture_vault.py:508-509`, `:1302`) still unwidened with both expected sets still at
  two members and the `ast` wall sharing the `:1302` local at `:1309-1312`; `SCRIPTS_ROOT` at
  `tests/derivations.py:33`, `python_files_under` at `:185`, `skip_reason_return_values` at `:1528`,
  `skip_reason_literal_sites` at `:1585`; `WORK_ITEM_DOCS` at `tests/test_ac_interpreter.py:47-50`
  carrying two docs today; `ArmId("scripts/lint_vault.py", "apply_fixes", 1)` at
  `tests/test_company_name_contract.py:533`; `EDITED_FUNCTION_ARM_COUNTS` and the wall-membership
  model at `tests/test_name_gate_wall.py:102`/`:1057`. Nothing moved, nothing means something else.

The fold's own courtesy note about `tests/derivations.py` drifting ~2 lines is accurate and AC-3 was
correctly left unedited for it — a navigation ordinal is not worth invalidating `ac_hash_AC-3`.

### Counterexample hunt — the section-contract domain, and the one member that is false by design

AC-5(a) quantifies universally over an enumerable domain: the sections of
`docs/lint-vault-live-baseline.md`, each held to a MEASURED or a DERIVED contract.

**DOMAIN:** every `## ` heading in that file — `:17`, `:72`, `:91`, `:104`, `:128`, five members.
**PREDICATE:** for each, count fenced blocks, count markdown tables, test the first non-empty line of
each fence for an absolute interpreter path, and read the section's declared role from its own prose.

**Result — one member IS false by design, and the fold found it and dispositioned it before I did.**
§4 satisfies NEITHER contract: it carries zero fences (so it is not MEASURED) and its commands are
inline code spans at `:135-137` (so it is not DERIVED either, and a "no fence ⇒ derived" reading would
demand a derivation sentence it does not have). It is false by design because it is the one LIVING
region of the artifact — the conductor fills its `exit` column and its `post-build HEAD` row at
`ready → done`, after the criteria are frozen and after almost every floor run this check will ever
have. The disposition is a NAMED EXCLUSION plus a narrowed quantifier: AC-5(a)'s measured/derived
split names §0/§3 and §1/§2 explicitly and reaches §4 not at all, AC-5(d) asserts PRESENCE and never
emptiness, and the SHA count is scoped to the header region rather than the file. That is the correct
disposition, and it is worth recording that it was reached by asking about the artifact's LIFETIME
rather than its current bytes — the member would have been filed silently in the "sections that
obviously comply" bucket by any census that only read what is there today.

**No second false-by-design member found in that domain.** §0 and §3 are both genuinely measured with
their own argv and stdout fences; §1 and §2 are both genuinely derived with no fence, one table and a
naming sentence. Round 1's hunt over the write-causing domain (four mutation sites, `:957`, `:975`,
`:1134`, `:1140`, no fifth writer, no scheduled or opt-in-gated arm) is re-affirmed unchanged — the
grep returns the same four and `apply_fixes` grew no write this round because the Design deliberately
leaves `write_frontmatter` at `:953-955` where the two frozen arm-count walls pin it.

### Conclusion

All three of round 1's required groundings are closed by predicates I re-ran rather than by prose I
read, and the closures are green against HEAD without either conductor-owned artifact being edited —
which was the constraint round 1 imposed and the one the first pass at the fix failed. The fold's new
material introduced no fresh empirical defect that I could produce: the sweep it reports having run
over AC-1 through AC-4 reproduces under independent execution, the post-change behaviour of the
battery AC-2(a) runs was checked against the corpus member this item stops dropping, and both of
AC-4(d)'s reachability claims trace end to end through the real check pipeline. The live premises
remain dated and honest — the undecodable count is 0 on the 2026-09-10 snapshot, so AC-3 is
prophylactic on day one and says so, and `missing_body_sections` will keep drifting, which is now an
asserted delta rather than a premise rotting under a signature.

Two things carried forward for the build, neither a finding: the build-start re-grounding (WI-022)
should re-run AC-5(b)'s five-row comparison before the first edit, because the baseline is five days
old and the vault churns weekly; and the exit half of A7's bracket has no battery wall by
construction, so it lives or dies at the conductor's ship door exactly as `## Approach` says.

```verdict
gate: data-premise
verdict: PROMOTE
date: 2026-09-15
model: claude-opus-5
note: All three round-1 groundings re-executed and CLOSED against HEAD without editing either conductor-owned artifact — AC-5(b)'s tolerance is green rule by rule (821/835 delta +14 matching the artifact's own delta cell, 315/315, 19/19, and the two zeroes strict), AC-5(a)'s narrowed shape contract now runs clean over the committed bytes (five headings by PREFIX because two carry qualifiers, one delimited 40-hex SHA scoped to the header at `:12`, §0 and §3 measured at 3 and 2 fences with argv-first and stdout-last, §1 and §2 derived with zero fences, and the `Command:` element the first pass re-introduced is gone), and AC-2(a) now counts issues per `(path, check)` carrying the 8-over-5 figure I re-derived independently off `tests/fixture_vault.py:361-382`. The fold's new spec body introduced no fresh empirical defect I could produce: AC-4(d)'s `declined` and `refused` plants both trace end to end through the real pipeline, the nine rename sites grep exactly as enumerated, `missing_body_sections` is zero on the corpus by heading NAME and not merely by count, and AC-2(a)'s table survives the change this item makes to its own battery because `@Isolde Varnholt` reaches every pinned check behind either the widened `parse_error` guard or an `entity_type` gate. Counterexample hunt over the section-contract domain found exactly one false-by-design member, §4, already dispositioned as a named exclusion with presence-only assertions because the conductor fills it at `ready → done` while this check sits on the floor for good.
```
