---
id: WI-026
title: "lint_vault.py --fix safety: route through the guarded primitive + a test floor for scripts"
project: obsidian-schemas
stage: done
created: 2026-07-05
last_touched: 2026-09-16
stage_changed: 2026-09-16
touched_by: spec-writer
tags: [scripts, write-safety, testing]
depends_on: ["WI-004", "WI-020"]
transitions: ["idea>exploring@2026-09-10@porter", "exploring>specced@2026-09-15@porter", "specced>ready@2026-09-16@porter", "ready>building@2026-09-16@porter", "building>done@2026-09-16@porter"]
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

**Signature impact — SETTLED 2026-09-15 by Dave's re-signature; the paragraph below is the
pre-re-sign narration and is kept as the record of what was asked for.** The `ac-signoff` fence at
`## AC Sign-off` now carries `ac_hash: 973d7a08f068` with `ac_hash_AC-2: bdb83849dd61` and
`ac_hash_AC-5: 01784d0e28c1` — the two hashes the round below invalidated, re-signed against the
edited text — while `ac_hash_AC-1` (`23030080e7eb`), `ac_hash_AC-3` (`9bd601c3a0d4`),
`ac_hash_AC-4` (`5cc1a0cc3737`) and `intent_hash` (`6a7cccabd378`) stand exactly as the paragraph
predicted they would. So there is no open signature ask and no drift to classify here; only this
narration was out of date, and the spec-review round of 2026-09-15 named it. **AND THE ROUND THAT
FOLLOWED THE SIGNATURE TOUCHES NO SIGNED SPAN:** the 2026-09-15 mitigation folds edit Design §§1,
3, 4, 6, 7, the Edge Cases, Tasks 4/7/9/16, two `## Write Targets` `why:` values, `## Verification`,
`## Risk Analysis` and the new `## Mitigation Folds` section — every one of them outside `## Intent`
and outside `## Acceptance Criteria`, so all five per-criterion hashes and `ac_hash` stay valid and
nothing above needs Dave again. That is deliberate rather than lucky: M4's fold moves the DESIGN to
agree with AC-4(b) rather than moving AC-4(b) to agree with the Design, because the signed criterion
already states the correct behaviour.

The pre-re-sign narration, kept verbatim: the 2026-09-15 `ac-signoff` fence carries
`ac_hash: 03777fa0e132` over the whole `## Acceptance
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

**Third pass — 2026-09-15, the mitigation folds.** A FIFTH question arrived with the threat model
and is the one that drove this round: *"On a file whose first write committed and whose second write
then raised, what is the first issue?"* — Design §4's credit-at-the-commit-point rule, the two credit
points at `:957` and `:975`, and the Edge Cases pair that states both directions; `repaired`, never
`errored`, which is what AC-4(b) was already signed to require. A SIXTH: *"What stops this module
from ever pointing the mutating entry point at Dave's real vault?"* — Design §7's two halves, the
`_temp_vault` door and the §6(d) syntax wall over the module's own source, ordered together in Task
9. Then swept the document for what this round's claims contradict, and found four, all fixed in the
same edit rather than left: Task 4 still said "the fold moved to the end of the lock block"; the
`## Edge Cases` write-raises entry described only the first write and was silent on the second;
`## Risk Analysis` R1 still said "moves the `repaired` fold from `:949` to the end of the lock
block"; and three counts moved with the fourth derivation and the eighth check (Design's opening
inventory, §6's heading, §7's non-AC count, Task 16's expected direction, R4's disclosed cost).
Non-blocking note 1 of the spec-review round is settled inside that same rewrite rather than
separately: `file_fixed` at `:882` and the `fixed += 1` at `:972` are DELETED, not left to the
builder as a coin-flip, because `staged_first` and `staged_wikilink` are what the credit points
count and leaving either increment would double-count a wikilink repair against AC-4(a)'s equality.

**Fourth pass — 2026-09-15, M3's provenance tightening (spec-review round 2, blocking issues 1 and
2).** A SEVENTH question arrived with the two gate rounds and it is the one that drove this pass:
*"What stops a drive from satisfying the containment wall by RE-BINDING the accepted name?"* —
nothing did, and both gates said so independently. Design §7's syntax half asserted that every
mutating drive's vault argument is SPELLED `vault` and called that "what proves every drive went
through it", which is false of the mechanism: §6(d) collected CALL sites only, so
`vault = lint_vault.DEFAULT_VAULT` followed by `run_lint(vault, do_fix=True)` presented the accepted
spelling at the only place the wall looked while `_temp_vault` was never called. The answer now is
§6(d)'s second census: `mutating_drive_vault_args` returns a `VaultArgScan` pair, and the wall's
third clause asserts that every BINDING of the accepted identifier in that module has provenance
`_temp_vault`. The fix is one clause over a module the scan already parses, exactly as threat-model
round 2 said, and it lands INSIDE the existing check rather than as a ninth one, so Design's opening
inventory (three code changes, FOUR derivations, ONE new module, SIX edited modules), §7's
five-plus-three check count, R4's "eight checks" and Task 16's expected direction all still hold —
the four counts this document has already had to re-sync once do not move again.
Then swept the document for what this pass's claims contradict, and found SIX surfaces stating the
superseded spelling-only rule, every one of them rewritten in this same edit rather than noted:
Design §6(d), Design §7's syntax half, Task 7, Task 9 (ii), `## Verification`'s counting-wall
bullet, the `tests/derivations.py` `## Write Targets` fence, and `## Mitigation Folds`' own sweep
paragraph — whose first-level sweep result was FALSIFIED by the re-binding shape and is re-swept and
corrected in place rather than quietly replaced. Two carried non-blocking notes are actioned in the
same text because they live inside it: `_temp_vault`'s third comparison is
`os.environ.get("OBSIDIAN_VAULT_PATH", "")` and never a subscript (a `KeyError` in the graded and CI
environments would redden the door itself), in Design §7 and Task 9 both; and §7's citation of
`tests/test_vault_path_required.py:FORBIDDEN_DEFAULT_PATTERNS` is re-anchored from `:320` to the
symbol's real line `:278`, with `:320` named separately as the universe line the sentence's second
half is about. Both halves of that claim were re-read against the file this pass: the three patterns
really are `expanduser` / `Path.home()` / `/Users/`, none of which can see an environment read, and
the sweep really does stop at `("obsidian_schemas", "scripts")`.
`## Verification` gains what WI-235 already owed this wall now that the claim has a second half: the
re-binding shape driven through the predicate itself as a RED with three siblings, the near-miss it
must NOT match (a correct `vault = _temp_vault(tmp)` in a module that also binds other names, none
of which may appear in `bindings` at all), the closed-set RAISES, and a TENTH mutation — re-bind and
drive — which is green against a build that ships `drives` and skips `bindings`, which is what makes
it worth running. Nothing in `## Intent` or `## Acceptance Criteria` is touched by this pass, so
`ac_hash: 973d7a08f068` and all five per-criterion hashes stay valid: M3 is a guard over the check
module's own source and no criterion states it.

**Fifth pass — 2026-09-15, M5 and M6 (threat-model round 3's two new fences, and spec-review round 3's
two blocking issues).** An EIGHTH question arrived with threat-model round 3 and it is the same
question as the seventh, asked one level UP: *"What stops a drive from reaching the live vault without
presenting a path for any census to grade AT ALL?"* — nothing did. Two routes, and enumerating the
question rather than its first answer is what makes this fold close the level instead of its first
member. **In-process:** §6(d)'s `drives` callee set was a two-member hand list (`apply_fixes`,
`run_lint`) while `scripts/lint_vault.py` has THREE mutating entry points, and the third is the worst —
`main:1252` declares `--vault` with `default=DEFAULT_VAULT` (`:1255`) and calls
`run_lint(vault_path, …, do_fix=args.fix, …)` (`:1299-1308`), so `lint_vault.main()` under an `sys.argv`
carrying `--fix` runs `--fix` against `OBSIDIAN_VAULT_PATH` while `drives` collects nothing, `bindings`
(scoped BY `drives`) collects nothing, and `_temp_vault` is never called. M5 puts `main` in the set,
where §6(d)'s existing "a vault argument at NEITHER position RAISES" rule grades it with no new text,
because `main` has no vault-argument position at all. **Out-of-process:** a child process is unreadable
to any in-process census by construction — the path is a string in an argv list — so M6 refuses the
CAPABILITY at the import: `subprocess` and `runpy` join the module set Task 15 hands
`module_import_uses` over the new check module, since `WALL_C_MODULES` is `FS_MODULES - {"os"}`
(`tests/test_name_gate_wall.py:1043`, `tests/derivations.py:68`) and reaches neither. Neither needs new
machinery: M5 rides Task 7's callee set (no fifth derivation) and M6 rides Task 15's existing
`test_wall_membership_is_closed_for_every_file_this_item_touches` with a widened `modules` argument (no
ninth check, and `module_import_uses:847-870` already takes an arbitrary iterable and reports the
ORIGINAL module name), so Design's opening inventory, §7's five-plus-three check count, R4's "eight
checks" and Task 16's expected direction all still hold — the four counts do not move a third time.
Then swept the document for what this pass's claims contradict, and found SEVEN surfaces, every one
rewritten in this same edit rather than noted: Design §6(d)'s callee set (plus a new paragraph on why
the scan's universe must stay the new check module alone, since `main`'s membership makes the scan RAISE
over the script's own `main()` at `:1316` — correct behaviour, not a defect to exempt); Design §7's
"two halves" framing, now THREE routes with the import half written out; Task 7's work and verify; Task
9's "both halves" phrase and its authoring constraints; Task 15's `module_import_uses` call and verify;
`## Verification`'s counting-wall bullet (M5's two RAISE shapes with a `setup()` / `helpers.main_menu()`
near-miss, and a new bullet for the widened import set with five claimed shapes and five near-misses
drawn from the module's own legitimate imports — WI-235, since a zero-import wall's green is the
cheapest of all to satisfy by a set that reaches nothing); the `tests/derivations.py` and
`tests/test_lint_vault_fix_rules.py` `## Write Targets` fences; and `## Mitigation Folds`' own sweep
paragraph and opening declaration. TWO mutations join the mutate-and-observe list (ten → TWELVE), each
chosen for the property that makes it worth running — each is GREEN against a build that folded its
mitigation's words and not its substance. Two carried non-blocking notes are actioned in the same text:
the sweep paragraph's "an alias, a wrapper or a second constructor is RED naming its line" OVERCLAIMED
(true of `make_vault`, false of `helpers._temp_vault(tmp)`, of `from x import make as _temp_vault` and
of a second `def _temp_vault`, all of which resolve to the door's own name and are GREEN), corrected in
place; and Task 9 now orders the containment check DEFINED FIRST in the module, an ordering courtesy
that is free at authoring time and expensive to retrofit. And the arc itself is closed rather than left
to a fourth round: spec-review round 3 named the regress signature — three monotone rounds, each
finding landing on the surface the previous fold added — and recommended the family be closed as a
standing ruling. It is, in `## Scope Boundary`, in the A3/A3b shape: **the containment-wall family is
CLOSED at the OMISSION level and is NOT total over deliberate acts**, with both known residues named
(a decoy spelled with the door's own name; deleting a clause of the wall) as the mechanism's honest
bound. *(Quoted and dated rather than deleted — **"CLOSED at the OMISSION level" is FALSE as written**,
falsified by threat-model round 5 on 2026-09-16: the wall reaches omission shapes that NAME the live
path and not ones that OBTAIN it without naming it, and
`obsidian_schemas/repositories/base.py:_resolve_vault_path:104-114` is exactly the second kind. See
the seventh-pass note below and `## Scope Boundary`.)* That is a SUFFICIENCY call, which belongs to Dave or the conductor, so it is written as a bound
a later gate routes against and overrides in one explicit act — not as a spec-writer's ruling. Nothing
in `## Intent` or `## Acceptance Criteria` is touched by this pass, so `ac_hash: 973d7a08f068` and all
five per-criterion hashes stay valid: M5 and M6 are clauses of a guard over the check module's own
source and imports, and no criterion states either.

**Sixth pass — 2026-09-15, M7 and M8 (threat-model round 4's two new fences, and spec-review round 4's
two blocking issues).** A NINTH question arrived with threat-model round 4 and it is not the eighth
asked one level up — it is a fact about `scripts/lint_vault.py` that has been true since before this
item was minted: *"What does the vault ARGUMENT this wall grades actually determine?"* — nothing, for
the drive that matters. `vault_path` appears in `apply_fixes` exactly once, in the signature at
`:827`, and nowhere in the body; the write targets come from the issues (`by_file[issue.file_path]`
at `:835`, then `fpath` at `:853`, `:858`, `:957`, `:975`). Re-read off this tree this pass rather
than taken from the round: `grep vault_path scripts/lint_vault.py` returns `:827` as its only
occurrence inside that function. So every rung of this ladder so far graded the wrong thing, and the
four-line escape — `vault = _temp_vault(tmp)` beside
`issues = lint_vault.check_noise(lint_vault.read_vault(lint_vault.DEFAULT_VAULT), idx)` then
`lint_vault.apply_fixes(issues, vault)` — passes clause (i) spelling, clause (ii) non-vacuity and
clause (iii) provenance with the runtime door EXECUTED and the import wall clean, while rewriting
the live vault. Under `quarantine_garbage` it is worse than a wrong write: `vault_path` there is only
the destination root (`:1116`) while the sources moved are `issue.file_path` (`:1121`), so a
correctly-contained vault argument renames live notes into a temp directory that is then deleted.
**M8 is therefore folded as a SOURCE clause and not as a fifth door**, which is what makes it the
fold that closes the NAMING half of this family rather than one more door — **corrected 2026-09-16
(seventh pass) after threat-model round 5 falsified the previous sentence, which read "which is what
makes it the fold that ENDS this family rather than extending it: the live vault path has exactly two
sources in this module's universe, so a clause that the module NAMES neither outside `_temp_vault`'s
own body is total over every omission route through every door"**: the clause is total over the
omission shapes that NAME the path, at the three token shapes it closes, and it does NOT reach an
omission shape that OBTAINS the path without naming it —
`obsidian_schemas/repositories/base.py:_resolve_vault_path:104-114` falls back to
`os.environ.get(ENV_VAULT_PATH)` INSIDE the library, so `repo = PersonRepository()` beside
`read_vault(repo.vault_path)` is a THIRD source the module never spells (the seventh-pass note below
states the whole correction, and `## Scope Boundary` holds the routed sufficiency call). Its mechanism is RULED here rather than left to
the builder, because the spec-review round is right that `desc` does not state one and the three
readings fail differently: the exemption is scoped by INNERMOST enclosing `FunctionDef` name — never
a line range (rots on the first edit), never an allowed-occurrence count (greenable by moving the
escape INTO `_temp_vault`) — and it is stated identically in Design §6(d), Design §7's SOURCE half
and Task 9's clause (iv) so those three cannot disagree. Two constraints ride with it, both from the
threat model's own notes and both in the fold's text: M8 must NOT be implemented by widening the
graded IDENTIFIER set (adding `read_vault` to the callee set pulls `tmp` into `bindings`, and
`with temp_dir() as tmp` RAISES there — a false RED on a correct module, round 4 note 1), and M8 and
M6 are ONE rule about `_temp_vault` at two levels (M6 leaves `os` legal BY NAME at the import so the
door may read `os.environ`; M8 scopes that read to the door's body), so "tidying" either reddens the
door itself. **M7** is the same round's other half and is one member of a set Task 7 already builds:
the callee set was three where the script has FOUR functions reaching a `vault_io` mutating door —
settled this pass by reading the mutation sites rather than the names (`write_note:957`/`:975` in
`apply_fixes`, `ensure_dir:1134`/`move_note:1140` in `quarantine_garbage:1112-1144`) — and
`quarantine_garbage`'s vault argument is the SECOND positional at `:1113`, identical in position to
`apply_fixes`' at `:827`, so §6(d)'s position rule grades it with no new text. The lasting fix is not
the member but the SET'S DEFINITION: §6(d) now states the callee set as a derived predicate over
mutation sites rather than as N names. Both folds ride shipped machinery, so §6's FOUR derivations,
§7's five-plus-three check count, R4's "eight checks" and Task 16's expected direction do not move.

**Spec-review round 4's blocking issue 2, and it is the WI-226 half of this fold.** Three surfaces
asserted a completeness round 4 falsified, and all three are corrected in THIS edit rather than
noted: `## Mitigation Folds`' upward-sweep paragraph (its "the script's complete set of mutating
entry points" and "empty of omission shapes" claims), Design §7's framing sentence ("THREE routes …
and the trio is what makes the guard total" — its NECESSITY companion, "a guard missing any one of
the three is satisfiable by a drive that mutates the live vault", was TRUE and is kept, widened to
four), and most importantly `## Scope Boundary`'s standing ruling, whose bound is RESTATED rather
than retracted: the instrument is right, the wording overstated its own scope, and its last sentence
instructs a later gate to CITE and escalate rather than REVISE — so an overstated bound there would
have waved through exactly the class it names. The restated bound says what the mechanism will
actually be once M7 and M8 land (total over omission shapes BY CONSTRUCTION, at the two source
tokens, with the door census as belt-and-braces), records round 4 in the arc, and names the one
residue M8 inherits rather than removes — an author who writes the escape inside `_temp_vault`'s own
body, which the mandatory by-function exemption permits. *(That parenthesis is quoted and dated
rather than deleted: **"total over omission shapes BY CONSTRUCTION, at the two source tokens, with
the door census as belt-and-braces" is FALSE as written** — there is a third source, the clause is
total only over omission shapes that NAME the path, and with the source half not total the door
census (M5, M7) and the import wall (M6) are LOAD-BEARING rather than belt-and-braces. Corrected on
every surface by the seventh pass below; the bound `## Scope Boundary` now carries is the corrected
one.)* The spec-review round's escalation trigger
is written into that paragraph too, so it is not a gate's memory: a FIFTH threat-model round opening
a NINTH `kind: required` fence on this family, after M7 and M8 land as written, is Dave's or the
conductor's sufficiency call and the gate holding it should ask rather than emit another REVISE. The
round's non-blocking note 1 is actioned in the same edit — §6(d)'s scan-universe paragraph gains
`quarantine_garbage`'s own `vault_path` `ast.arg` at `:1113` as a third raise site and the
`quarantine_garbage(garbage, vault_path)` call at `run_lint:1220` beside the `apply_fixes` call at
`:1194`, and the list is labelled an ENUMERATION rather than a total, since mistaking one for the
other is the reading habit this document has now been bitten by twice. The drift audit's one finding
is archival only and no re-anchoring is owed: the LIVE citation in Design §7 already reads
`tests/test_vault_path_required.py:FORBIDDEN_DEFAULT_PATTERNS:278`, confirmed at the file this pass
(`FORBIDDEN_DEFAULT_PATTERNS = ["expanduser", "Path.home()", "/Users/"]` at `:278`), with `:320`
named separately as the universe line (`for directory in ("obsidian_schemas", "scripts")`), also
confirmed — and that universe NOT reaching `tests/` is why Task 15's own re-run of those patterns
over this item's touched files is load-bearing rather than redundant, which is now stated where M8
relies on it.

Then swept the document for what this pass's claims contradict, and found FIVE surfaces, every one
rewritten in this same edit rather than noted: Design §6(d)'s `drives` paragraph and its M5
paragraph's "THIRD member" phrasing (with M5's fold `design:` re-quoted to the edited sentence, since
a fold's `design` must quote the sentence that NOW carries it); Design §7's syntax half, its part
count and its closing necessity sentence; Task 7's work and verify; Task 9's "both halves" framing,
its clause count and its verify list (with M3's fold `work:` re-quoted to the edited task); and the
two `## Write Targets` `why:` values for `tests/derivations.py` and
`tests/test_lint_vault_fix_rules.py`. TWO mutations join the mutate-and-observe list (twelve →
FOURTEEN), each chosen for the property that makes it worth running, and the THIRTEENTH was
deliberately re-chosen while writing it: the obvious M7 mutation
(`quarantine_garbage(issues, lint_vault.DEFAULT_VAULT)`) is RED under clause (iv) whether or not M7
landed, so it discriminates nothing about the callee set — the mutation shipped instead passes `tmp`,
names no live-path token, and is therefore RED only because the callee set reaches
`quarantine_garbage`. One more contradiction the same sweep turned up and fixed: the `bindings`
near-miss battery legitimately PLANTS text spelling `lint_vault.DEFAULT_VAULT` and
`os.environ[...]`, which reads as a collision with clause (iv) until one notices those are fixture
STRINGS handed to the predicate rather than lines of this module's source — so both the battery and
the `live_path_names` near-miss list now say so, the Constant arm is stated as EQUALITY and never
containment, and the one real build constraint that falls out (a BARE `"OBSIDIAN_VAULT_PATH"`
Constant outside `_temp_vault` — e.g. in an environment-scrub helper copied from
`tests/test_vault_path_required.py:344-353` — IS a match and IS red) is written down rather than left
to be discovered. Nothing in `## Intent` or `## Acceptance Criteria` is touched by this pass, so
`ac_hash: 973d7a08f068` and all five per-criterion hashes stay valid: M7 is a member of a derived
set and M8 is a guard over the check module's own source, and no criterion states either.

### Revision — 2026-09-16 (spec-writer, seventh pass), answering spec-review round 5's blocking issue 1 — the truthfulness sweep

**Seventh pass — 2026-09-16. NO mechanism moves in this pass; what moves is what the document SAYS
about the mechanism it already has.** Threat-model round 5 and spec-review round 5 both found the
same thing and neither found a new escape to close: the sentence M8 rests on — *"a drive can only
reach the live vault by NAMING it"* — is false, so every sentence resting on it is false with it. I
re-verified the factual half at the code rather than taking it from either round.
`obsidian_schemas/repositories/base.py:_resolve_vault_path:104-114` is
`for candidate in (vault_path, os.environ.get(ENV_VAULT_PATH))`, raising only when BOTH are
unconfigured; `ENV_VAULT_PATH = "OBSIDIAN_VAULT_PATH"` at `:75`; `_is_unconfigured:86-101` counts
`None`, blank, whitespace-only and `Path(".")` as unconfigured; `BaseRepository.__init__:154` calls
it, so all four repositories exported at `obsidian_schemas/__init__.py:74-77` carry it. The env read
happens INSIDE the library, so

    repo   = PersonRepository()                       # names no clause-(iv) token
    issues = lint_vault.check_noise(lint_vault.read_vault(repo.vault_path), idx)
    lint_vault.apply_fixes(issues, vault)             # vault from _temp_vault  ✓

is GREEN on clause (i) spelling, (ii) non-vacuity, (iii) provenance AND (iv) source, with the runtime
door executed, the import wall clean (`obsidian_schemas` is in neither `WALL_C_MODULES` nor
`{"subprocess", "runpy"}`), `os_module_attribute_uses` clean and `FORBIDDEN_DEFAULT_PATTERNS` clean —
and it rewrites the live vault on any machine where `OBSIDIAN_VAULT_PATH` is exported, which is where
`CLAUDE.md`'s floor command is hand-run. The module is REQUIRED to import from `obsidian_schemas`
(M1's verify reads `SKIP_REASONS` from `repositories.base`, and the module is forbidden to hand-type a
member), so the import is not an exotic addition to it.

**The generator, and the class closed in one fold rather than the instances two gates listed
(WI-226).** What generates these findings is not "another door" — it is *a level declared closed BY
CONSTRUCTION where the construction is an enumeration of the TOKENS THE MODULE'S OWN TEXT SPELLS*.
M8's "two sources" is a three-token enumeration wearing the word *sources*, exactly as M5's "three
entry points" was a three-name enumeration wearing the word *complete*. So the fold is not three
edits, and it is not the seven surfaces spec-review round 5 enumerated either. **The correction
stated once, and every surface below now says exactly this:** clause (iv) is TOTAL over omission
shapes that NAME the live path — the three token shapes, at every site outside `_temp_vault`'s own
body — and it is NOT total over omission shapes that OBTAIN the path without naming it; the library's
own `OBSIDIAN_VAULT_PATH` fallback is a THIRD source; that residue is an OMISSION shape and NOT
deliberate-act residue, so `## Scope Boundary`'s deliberate-act closure does not cover it; and
because the source half is not total, the DOOR census (M5, M7) and the import wall (M6) are
LOAD-BEARING again rather than "belt-and-braces over the routes".

**The sweep at source returned TWELVE live surfaces, not the three round 5 named or the seven the
review enumerated** — run by grepping the claim's own vocabulary (`two sources`, `total over`,
`omission`, `every door`, `belt-and-braces`, `no third`, `by construction`) across the document and
reading every hit, rather than by working the review's list. Numbered so the next round can check the
sweep instead of re-running it, with the five the review did not name marked:
(1) `## Exploration Notes`' fifth-pass note, the "CLOSED at the OMISSION level" sentence **[unnamed]**;
(2) its sixth-pass M8 paragraph; (3) its sixth-pass blocking-issue-2 paragraph, the "belt-and-braces"
parenthesis **[unnamed]**; (4) Design §6(d)'s "exactly TWO sources … closed by construction";
(5) Design §6(d)'s M8 RULE sentence (whose quote in M8's fold `design:` moves with it);
(6) Design §7's OPENING summary **[unnamed]**; (7) Design §7's four-parts framing clause, "the two
tokens the live path can only come from" **[unnamed]**; (8) Design §7's SOURCE-half bullet;
(9) Design §7's four-parts closing; (10) `## Write Targets`' `tests/test_lint_vault_fix_rules.py`
`why:` **[unnamed]**; (11) `## Mitigation Folds`' "closed at the SOURCE" bullet; and
(12) `## Mitigation Folds`' level-above paragraph, whose *"There is no third, because a call in this
module either names its arguments in this module's `ast` or leaves the process"* is the sharpest of
the twelve and is exactly what the finding falsifies. Every one is corrected IN PLACE with the
falsified wording quoted and dated, never deleted. `## Scope Boundary`'s restated bound is the
thirteenth edit and is the one that matters most, for the reason the review gives: its closing
sentences instruct a later gate to CITE it and escalate rather than REVISE, so a bound with a false
stated reason waves through exactly the class it names — that instruction is now scoped explicitly to
the DELIBERATE-ACT level, and the demotion of M5/M6/M7 to "belt-and-braces" is out. Two of these
surfaces carry the claim in a HEADING as well as in a body sentence — `## Mitigation Folds`' upward-
sweep heading ("the whole of that level is closed in one fold") and the `## Scope Boundary` bullet's
own title ("past the OMISSION level — the family is CLOSED there") — and both are qualified in the
same edit, because a corrected body under an uncorrected heading is the half-fix this round is about.
Gate-round sections are append-only records and are NOT edited; their own text already dates what it
claimed.

**The next level of the ladder, swept and DECLARED rather than left for round 6.** With the generator
in hand the question one level up is *what can hand this module the live path without the module's
own text naming it*, and that is a set with a declaring act: an in-process callable the module may
invoke that resolves a vault from the environment rather than from its argument. Swept today by
grepping `OBSIDIAN_VAULT_PATH|ENV_VAULT_PATH|os\.environ|os\.getenv` across `obsidian_schemas/**`,
`scripts/**` and `tests/**` and reading every hit: the sweep returns exactly ONE member —
`_resolve_vault_path`, reached through any of the four repository constructors. The near members are
all closed and are named so they are not re-derived: `obsidian_schemas/vault_io.py:_env_setting:103-116`
is the package's other env reader and resolves LOCK and write-guard settings, never a vault path;
`tests/fixture_vault.py:materialize_vault:626` and `tests/identity_fixture.py:seed_vault:85-100` both
REQUIRE a destination (and the second plants a hard refusal whose docstring names
`_resolve_vault_path` and the `tests/` blind spot in terms); `scripts/lint_vault.py:DEFAULT_VAULT:56`
and `main:1252` are the already-graded token and the already-graded entry point. **That census is an
ENUMERATION measured on 2026-09-16 and never a total** — a callable added later that resolves a vault
from the environment joins this class silently, which is precisely the property that makes the level
worth stating rather than declaring closed.

**What this pass does NOT do, and whose call that is.** It does not add a ninth mitigation, a fifth
derivation, a new check or a count. Whether to CLOSE the third source is a SUFFICIENCY call, and
`## Scope Boundary` assigns sufficiency to Dave or the conductor; its recorded trigger — a fifth
threat-model round opening a ninth `kind: required` fence on this family after M7 and M8 land as
written — FIRED on 2026-09-16, threat-model round 5 declined to force it through D8 and emitted eight
fences, and spec-review round 5 routed it the same way. The spec-writer does not get to make that
call in either direction, so it is recorded in `## Scope Boundary` as OPEN and routed, with the cost
estimate the round assembled (one more CLOSED shape in the census Task 7 already builds — a callee
resolving to an identifier ending `Repository`, graded by Task 9's EXISTING clause (iv), the
requirement being ZERO repository constructions in the module rather than "no no-arg construction",
since `_is_unconfigured` swallows blank, whitespace-only and `"."`; the import-allowlist shortcut
cannot work, because `module_import_uses:847` reports the ROOT module and cannot tell
`from obsidian_schemas.repositories.base import SKIP_REASONS` from
`from obsidian_schemas import PersonRepository`). The correction above is owed whichever way that
call goes, and MORE owed if it goes "stop", because `## Scope Boundary`'s closing sentences instruct
a later gate to CITE that paragraph and escalate rather than REVISE.

**Two mechanical riders, both honoured.** M8's `desc` does NOT move: threat-model round 5 ruled
explicitly (its FIDELITY note) that the now-overstated rationale clause stays, because `desc` is the
only machine-anchored field, the REQUIREMENT did not move, and re-wording it would re-stale a fresh
fold record into a D8c refusal. All eight `desc` values in `## Mitigation Folds` remain byte-identical
to round 5's fences. M8's fold `design:` is NOT machine-anchored and DID move, in the same edit as
Design §6(d)'s M8 rule sentence it quotes, so the record stays a faithful quote. And nothing in this
pass touches `## Intent` or `## Acceptance Criteria` — no criterion states the wall's totality, which
I re-checked against all five — so `ac_hash: 973d7a08f068` and all five per-criterion hashes stay
valid and no re-sign is owed. `## Mitigation Folds`' opening sentence is re-pointed at the latest
speaking round (round 5, 2026-09-16) in the same edit, per the review's non-blocking note 1. The
review's non-blocking note 2 is CARRIED and deliberately not actioned: AC-3's `derivations.py:31`
(the symbol is at `:33`) and AC-5's "A SIXTH CENSUS READER" label both sit inside signed criteria,
neither changes what a builder implements, and neither is worth invalidating a set Dave signed on
2026-09-15.

Then swept this pass's own claims for what they contradict, and the answer is the ten surfaces above
plus nothing else: no Implementation-Plan task, no `criteria` fence, no `## Verification` fixture and
no `mitigation` or `fold` `desc` asserts the wall's totality — Tasks 7 and 9 and the `live_path_names`
battery state the MECHANISM (three token shapes, innermost-`FunctionDef` scoping, the non-vacuity
arm), and the mechanism is unchanged and still correctly described.

## Approach

Keep the write-safety clauses closed and prove the repair layer. Three changes to
`scripts/lint_vault.py`, one new test module, FOUR new derivations in `tests/derivations.py` (the
count Design §6 carries — this sentence said "one" from the draft that predated three of them), and a
live-vault bracket around the build:

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
accounting, the operator's summary line), FOUR new derivations in `tests/derivations.py`, ONE new
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

**The rule the first of those bullets states, in one sentence, because it is a required mitigation
and not a style note (M1):** `read_vault`'s recorded `read_error` value is the IMPORTED
`SKIP_REASONS` member `UNREADABLE` and never `str(exc)` of the decode failure, so undecodable note
bytes are never decoded, never rendered into an issue message and never stored in any record.
`obsidian_schemas/errors.py:chainable_cause` already names `UnicodeDecodeError` as a cause whose
`str()` renders note content and suppresses it for exactly this reason; this is that same rule one
frame further out, at the seam where the bytes first fail to decode.

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

**The bound on those two fields, in one sentence, because it is a required mitigation and not a
comment (M2):** `FixErrorRecord.reason` is the exception's class name and `FixDeclineRecord.guard`
is a `DECLINE_GUARDS` member — never `str(exc)`, never note bytes — because both records feed the
operator-facing summary that gets pasted into chat, which is the same reason
`NameGateRefusalRecord`'s own docstring gives for closing its field set at two.

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
recorded AT THE BRANCH with its guard id); the `write_note` call carrying its repair RETURNS
(→ `repaired`, credited AT THAT COMMIT POINT); or the frame it is still undecided in raises
`NameGateRefusal` (→ `refused`) or raises anything else (→ `errored`).**

Concretely, inside the per-file body:

    undecided = list(file_issues)           # every issue on this file
    staged_first: list[LintIssue] = []      # issues whose repair rides the write at `:957`
    staged_wikilink: list[LintIssue] = []   # issues whose repair rides the write at `:975`

- A branch that declines appends `FixDeclineRecord(fpath, issue.check, <its guard id>)` to the
  RUN-LEVEL `declined` list and removes the issue from `undecided`, immediately, inside the loop.
  Run-level and not file-local is the tie-break: a declined issue contributed nothing to `delta`,
  so it was in neither the write the gate refused nor the write that errored, and no later
  frame-level outcome on the same file may re-label it.
- A branch that ACTS appends its issue to `staged_first` and leaves it in `undecided`. The per-file
  `file_fixed` counter at `:882` is DELETED and `staged_first` replaces it: the list IS the counter,
  and a repair is counted by the issues riding a write rather than by a number incremented before
  that write exists. No branch keeps an increment of its own.
- `broken_wikilink` is the two-stage one. At `:929-936` an unparsable `suggested_fix` declines with
  `GUARD_UNPARSABLE_SUGGESTED_FIX`; a parsed one queues `(issue, old_link, new_link)` — the queue
  gains the ISSUE as its first element so the second stage can name it — and stays undecided. At
  `:963-973`, a replacement that FIRES appends its issue to `staged_wikilink` and leaves it
  undecided; one that matches neither `[[old]]` nor `[[old|` declines with
  `GUARD_LINK_TEXT_ABSENT`. The `fixed += 1` at `:972` is DELETED for the same reason `file_fixed`
  is: that issue is credited by `staged_wikilink` after its own write commits, and leaving the
  increment in place would credit it twice.
- **AN ISSUE IS CREDITED AT THE POINT ITS OWN WRITE COMMITS (M4).** The `fixed += file_fixed` fold
  at `:949` is DELETED OUTRIGHT — it is not moved to the end of the lock block, and a build that
  moves it there is wrong in the way this bullet exists to forbid. In its place there are TWO credit
  points, each on the statement immediately AFTER the `write_note` call whose bytes carry the issues
  it credits, both still inside the same `with vault_io.note_lock(fpath):` block: after
  `vault_io.write_note(fpath, content, precondition=_stamp)` RETURNS at `:957`,
  `repaired += len(staged_first)` and every member of `staged_first` is removed from `undecided`;
  after `vault_io.write_note(fpath, content, precondition=_stamp)` RETURNS at `:975`,
  `repaired += len(staged_wikilink)` and every member of `staged_wikilink` is removed from
  `undecided`. Neither credit point can be skipped while its list is non-empty, and neither list is
  non-empty when its write does not run: only an acting first-write branch sets `changed = True`,
  and only a replacement that actually fired appends to `staged_wikilink` and sets `wl_changed`.
- Why the credit point and not either end of the frame, stated because BOTH ends are wrong and each
  is wrong in a different direction. Crediting at `:949` as the code does today credits before the
  first `write_note` can raise at `:957`, so a repair that never committed is reported as one —
  that is the defect §4 corrects, and moving the credit AFTER the write is the correction. Folding
  once at the END of the lock block over-corrects into the mirror-image defect: a raise at `:975`
  propagates out of the `with` block to the handler at `:993`, so the end-of-block fold never runs,
  the issues whose write ALREADY COMMITTED at `:957` are still in `undecided`, and a committed write
  is reported as `errored`. That is this item's own defect one frame in — the summary misstating
  what happened to a real file, in the direction that makes an operator re-run a repair already on
  disk — and it is what AC-4(b)'s discriminating plant forbids. Per-write crediting satisfies both
  ends: on AC-4(b)'s file the `missing_body_sections` issue is `repaired` the instant `:957`
  returns, and the `broken_wikilink` issue whose `:975` write raises is `errored`, exactly as signed.
- `except NameGateRefusal as exc:` appends ONE `NameGateRefusalRecord(path=fpath,
  pattern=exc.pattern)` PER ISSUE still in `undecided`, and PRINTS ONCE. The gate raises at `:947`,
  which is BEFORE either credit point, so nothing on a refused file has been credited and every
  non-declined issue on it is still undecided — which is AC-4(b)'s first sentence, unchanged. The
  print stays exactly one
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

### §6. Four new derivations in `tests/derivations.py`

`ast` is single-homed there by two standing set-equality walls
(`tests/test_loud_fail_harness.py:103`, `tests/test_name_gate_wall.py:1136`) and a third in
`tests/test_fixture_vault.py:1309-1312`, so all four land there or the floor reddens for the wrong
reason. All four follow `tests/derivations.py:skip_reason_return_values:1528`'s loud-fail
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

**(d) `mutating_drive_vault_args(files) -> VaultArgScan`** — the scan M3's containment wall runs,
and the reason it is a DERIVATION rather than a hand list is that the property it holds is a TOTAL
one over a module that grows. It returns THREE sets and not one, because the requirement has three
halves and no one of them can express another (threat-model round 2: a drive's argument SPELLING is
not its PROVENANCE; threat-model round 4: neither one is what determines the bytes written):

    class VaultArgScan(NamedTuple):
        drives: frozenset      # (module_id, lineno, identifier)              — one per mutating call
        bindings: frozenset    # (module_id, lineno, identifier, provenance)  — one per binding site
        live_path_names: frozenset  # (module_id, lineno, token, enclosing)   — one per live-path NAMING site

**`drives` — the call census, over the script's FOUR mutating entry points and not three.** For every
`ast.Call` whose callee resolves to the bare name `apply_fixes`, `quarantine_garbage`, `run_lint`
**or `main`** — matched as
an `ast.Name` `id` OR as an `ast.Attribute` `attr`, so `lint_vault.run_lint(...)`,
`mod.apply_fixes(...)`, `lint_vault.quarantine_garbage(...)`, `lint_vault.main()` and an unqualified
call are all collected — it
records `(module_id, lineno, <the identifier bound to that call's VAULT argument>)`. The vault
argument is the SECOND positional for `apply_fixes` **and for `quarantine_garbage`** and the FIRST for
`run_lint` (their signatures
at `scripts/lint_vault.py:apply_fixes:827-828`, `quarantine_garbage:1112-1113` and
`run_lint:1147-1148`), or the `vault_path=`
keyword when the call passes it by name; a collected call passing a vault argument at NEITHER
position RAISES, and so does one whose vault argument is not a plain `ast.Name` — because the claim
the wall makes is that every mutating drive's path came out of the module's ONE door, and an
expression the scan cannot reduce to a bound name is precisely the case that must not pass silently.
The recorded identifier is the `ast.Name.id` itself, not `ast.unparse` of an arbitrary expression,
so there is exactly one spelling to compare against.

**`quarantine_garbage`'s membership needs no new rule either, and the census that decides the set is
the MUTATION SITES rather than a list of names (M7).** The `drives` callee set is the script's COMPLETE set of functions that reach a `vault_io` mutating door, and that set is FOUR — `apply_fixes`, `quarantine_garbage`, `run_lint` and `main` — because the script's only mutation sites are `write_note` at `:957` and `:975` inside `apply_fixes` and `ensure_dir` at `:1134` plus `move_note` at `:1140` inside `quarantine_garbage:1112-1144`, and `quarantine_garbage`'s vault argument is the SECOND positional at `:1113` exactly as `apply_fixes`' is at `:827`, so §6(d)'s existing position rule grades it with no new text.
The reason the missing member mattered is that its write is the IRREVERSIBLE one: `quarantine_garbage`
RENAMES live notes, this item PINS the two `garbage_candidate_*` detectors that decide what
`--quarantine` moves (AC-2's pinned set), and `lint_vault.quarantine_garbage(issues, vault)` is
therefore the natural drive for AC-2's leg (b) — a drive that, under a three-member callee set, is
invisible to `drives`, therefore to `bindings` (which is scoped BY `drives`), with `_temp_vault`
never called. The set is DERIVED from the mutation-site census and not from memory, which is why it
is stated as "the functions that reach a `vault_io` mutating door" rather than as four names: a
fifth such function added to the script later is a member of the stated set, and the WI-235 fixture
battery in `## Verification` is what proves the scan's reach over every member the set names today.

**`main`'s membership needs no new rule, and that is why it is a member of the set rather than a
clause of its own (M5).** `main` is a member of the `drives` callee set and needs no new rule to grade, because it has NO vault-argument position at all — `scripts/lint_vault.py:main:1252` takes no parameters — so EVERY collected `main` call, with or without arguments, falls into the arm above that already RAISES on a call passing a vault argument at neither position, naming module and line.
The reason `main` belongs in the set is that it is the one mutating entry point that reaches the live
vault by OMISSION rather than by an expression a scan can see: its `--vault` carries
`default=DEFAULT_VAULT` (`:1255`) and it calls
`run_lint(vault_path, …, do_fix=args.fix, do_quarantine=args.quarantine)` at `:1299-1308`, so
`lint_vault.main()` under an `sys.argv` carrying `--fix` runs `--fix` against
`OBSIDIAN_VAULT_PATH` while presenting no argument for either census to grade. With a callee set that
omits it, that drive passes clauses (i), (ii) and (iii) of Design §7 unseen — `drives` collects
nothing, `bindings` is scoped BY `drives` so it collects nothing either, and `_temp_vault` is never
called so the runtime door never executes. With `main` inside the set, it is RED at its own line.

**The scan's universe is the new check module alone, and the callee set's membership is a second
reason it must stay that way.** `mutating_drive_vault_args` is called only as
`mutating_drive_vault_args([Path(__file__)])` from inside
`tests/test_lint_vault_fix_rules.py` (Design §7's syntax half); no wall points it at
`scripts/lint_vault.py`, and pointing it there RAISES — already before M5, at `run_lint`'s own
`vault_path` parameter, which is an `ast.arg` and therefore a closed-set RAISE under `bindings`;
additionally at the `main()` call in the `if __name__ == "__main__":` guard at `:1316`; and now, with
M7's fourth member, additionally at `quarantine_garbage`'s own `vault_path` parameter at `:1113`,
another `ast.arg`, while the `quarantine_garbage(garbage, vault_path)` call at `run_lint:1220` joins
the collected set beside the `apply_fixes(fixable, vault_path, idx)` call at `:1194`. That list of
reasons is an ENUMERATION of what raises today and never a total — the point is the CONCLUSION,
which is unchanged and does not depend on how many raise sites there are: the scan's universe stays
the new check module alone. That is
correct behaviour for a scan whose whole claim is about a TEST module's drives, and it is not a
defect to be "fixed" by exempting the script.

**`bindings` — the PROVENANCE census, and it is what makes the wall a claim about where the path
CAME FROM rather than how it is spelled.** For every identifier appearing as the third element of a
`drives` triple, EVERY binding site of that identifier in the SAME module is recorded as
`(module_id, lineno, identifier, provenance)`. Identifiers no drive names are not scanned at all —
a module may bind whatever else it likes, which is the near-miss `## Verification` drives. Three
arms, and the third is where the totality comes from:

- A single-target `ast.Assign` whose target is that `ast.Name` and whose value is an `ast.Call`:
  `provenance` is the callee's OWN name — the `ast.Name.id`, or the `ast.Attribute.attr` for a
  dotted callee, resolved exactly as `drives` resolves a callee, so `vault = _temp_vault(tmp)`
  yields `"_temp_vault"` and `vault = helpers.make_vault(tmp)` yields `"make_vault"`.
- A single-target `ast.Assign` whose value is ANY other expression — `ast.Attribute`
  (`vault = lint_vault.DEFAULT_VAULT`), `ast.Subscript` (`vault = os.environ[...]`), `ast.Constant`
  (a literal path), a bare `ast.Name` (`vault = other`), a comprehension, a ternary — yields the
  module-level sentinel `NOT_A_CALL`. It is RETURNED rather than raised, deliberately: the scan
  reports and the WALL goes red naming the line, which is the same division of labour the spelling
  clause already has, and it keeps the hazardous shape drivable as a `## Verification` fixture
  instead of only as an exception.
- ANY OTHER binding construct RAISES with module and line named: an `ast.arg` (a parameter or a
  lambda parameter), a tuple / starred / attribute / subscript assignment target, an `ast.AugAssign`,
  an `ast.AnnAssign`, a `for` or `async for` target, a `with ... as` / `async with ... as`, an
  `ast.NamedExpr` walrus, an `except ... as`, an `ast.alias` (`import x as vault`,
  `from m import vault`), a `FunctionDef` / `AsyncFunctionDef` / `ClassDef` of that name, and an
  `ast.Global` / `ast.Nonlocal` declaration of it. That enumeration is CLOSED because `ast` closes
  it — it is Python's whole binding surface, not a sample of the shapes anyone thought of — and each
  member raises rather than yielding a sentinel because provenance for it cannot be read off one
  expression, so a sentinel would be a guess the wall then grades.

And the vacuity hole is closed inside the scan rather than left to the assertion: an identifier a
`drives` triple names that has NO binding site in that module RAISES too. A drive whose vault
argument arrives from outside the module's own text is exactly the case the provenance claim cannot
cover, and a scan that returned an empty `bindings` set for it would make the wall's
"every binding came from the door" true by having found no bindings.

**`live_path_names` — the SOURCE census, and it is the one that grades what actually determines the
bytes written (M8).** The two censuses above grade a drive's vault ARGUMENT, and for the drive that
matters most that argument is provably inert: `vault_path` appears in `apply_fixes` exactly once, in
the signature at `scripts/lint_vault.py:827`, and is referenced NOWHERE in the body — the write
targets come from the issues (`by_file[issue.file_path]` at `:835`, then `fpath` at `:853`, `:858`,
`:957`, `:975`). So a contained vault argument constrains nothing about what `apply_fixes` writes;
containment holds only TRANSITIVELY, through the issues' provenance, which neither `drives` nor
`bindings` can see. The four-line escape that passes every argument-side clause is:

    vault = _temp_vault(tmp)                                   # provenance "_temp_vault"  ✓
    live  = lint_vault.read_vault(lint_vault.DEFAULT_VAULT)    # ungraded by drives/bindings
    issues = lint_vault.check_noise(live, idx)                 # ungraded
    lint_vault.apply_fixes(issues, vault)                      # drives: identifier `vault`  ✓

— spelling green, non-vacuity green, provenance green, the runtime door EXECUTED, the import wall
clean, and Dave's live vault rewritten. Under `quarantine_garbage(issues, vault)` the same shape is
worse than a wrong write: `vault_path` there is only the DESTINATION root
(`quarantine_dir = vault_path / "_quarantine"`, `:1116`) while the sources moved are
`issue.file_path` (`:1121`), so a correctly-contained vault argument turns it into live notes renamed
into a temp directory that is then deleted.

So the third census closes at the path's NAMED sources rather than at a fifth door, and that choice
is why it is the clause that closes the naming half of the family instead of adding one more door:
every closure so far enumerated doors, and doors are a list somebody writes down, whereas the tokens
a module can SPELL the live vault path with are three shapes `ast` closes. **Corrected 2026-09-16
after threat-model round 5 falsified the previous sentence, which read "whereas the live vault path
has exactly TWO sources in this module's universe and that set is closed by construction":** the set
that is closed is the set of SPELLINGS, not the set of SOURCES. A path the module never spells is
outside it, and there is one in the tree today —
`obsidian_schemas/repositories/base.py:_resolve_vault_path:104-114` resolves
`for candidate in (vault_path, os.environ.get(ENV_VAULT_PATH))` INSIDE the library
(`ENV_VAULT_PATH:75`; `_is_unconfigured:86-101` counting `None`, blank, whitespace-only and
`Path(".")` as unconfigured; `BaseRepository.__init__:154` carrying it for all four repositories
exported at `obsidian_schemas/__init__.py:74-77`), so `repo = PersonRepository()` beside
`read_vault(repo.vault_path)` is a THIRD source that names none of the three token shapes below and
is GREEN on all four clauses while rewriting the live vault wherever `OBSIDIAN_VAULT_PATH` is
exported. That residue is an OMISSION shape rather than deliberate-act residue, it is NOT closed by
this census, and whether to close it is the sufficiency call `## Scope Boundary` routes to Dave or
the conductor — OPEN as of 2026-09-16. Because the source half is therefore not total, the door
census (M5, M7) and the import wall (M6) are LOAD-BEARING and not belt-and-braces. The rule, in one
sentence:

The new check module NAMES the live vault path nowhere outside the body of `_temp_vault` — no `DEFAULT_VAULT` reference, no `OBSIDIAN_VAULT_PATH` string and no `os.environ` / `os.getenv` read anywhere else in the module — so no escape that NAMES the live path can reach it through any door, the four the callee census enumerates or any door it does not; an escape that OBTAINS the path without naming it is outside this clause, which is why the door census (M5, M7) and the import wall (M6) stay load-bearing beside it.

`live_path_names` is what makes that checkable. For every node in the scanned module it records
`(module_id, lineno, token, enclosing)` at each of three CLOSED shapes, and nothing else:

- an `ast.Attribute` whose `attr` is `DEFAULT_VAULT`, or a bare `ast.Name` whose `id` is
  `DEFAULT_VAULT` (which covers `from lint_vault import DEFAULT_VAULT`) → token `"DEFAULT_VAULT"`;
- an `ast.Constant` `str` equal to `"OBSIDIAN_VAULT_PATH"` → token `"OBSIDIAN_VAULT_PATH"`;
- an `ast.Attribute` whose `attr` is `environ` or `getenv`, or a bare `ast.Name` whose `id` is
  `environ` or `getenv` (which covers `from os import environ`) → token `"os.environ"`.

**`enclosing` is the name of the INNERMOST enclosing `FunctionDef` / `AsyncFunctionDef`, or the
module-level sentinel `MODULE_LEVEL` when the site sits at module scope — and the choice of
by-function scoping over the two alternatives is RULED here rather than left to the builder, because
the three readings have three different failure modes.** A LINE RANGE rots on the first edit to the
module and is silently wrong thereafter. An ALLOWED-OCCURRENCE COUNT is greenable by moving the
escape INTO `_temp_vault`, which is the one thing the exemption must not license. By-function
scoping has neither failure: it is the same idiom §6(d)(b) already uses (the branch census is scoped
to the enclosing `FunctionDef` named `apply_fixes`), it survives every edit that does not move the
site out of the door's own body, and taking the INNERMOST def means a nested `def` written inside
`_temp_vault` reports its own name and is RED — so the exemption is the door's body and not the
door's neighbourhood.

The exemption is MANDATORY rather than incidental, which is why it is a named scope and not a
tolerance: Design §7's runtime half and Task 9 both ORDER `_temp_vault` to compare the vault it
built against `Path(lint_vault.DEFAULT_VAULT).resolve()` and
`Path(os.environ.get("OBSIDIAN_VAULT_PATH", "")).resolve()`, so a flat "the module names neither
token" clause would be RED against the module this document prescribes. Those three negative
assertions inside `_temp_vault` are also what closes the vacuity hole from inside the scan rather
than from the assertion: `live_path_names` must be NON-EMPTY for this module, so a scan that resolves
none of the three shapes — the cheapest possible way to satisfy a zero-outside-the-door wall — is RED
rather than green, and the WI-235 fixture battery in `## Verification` drives every claimed shape and
its near-miss through the predicate itself.

Two things this census deliberately does NOT do, both recorded because the tempting shortcut is worse
than the rule. It does NOT widen the graded IDENTIFIER set to reach `read_vault` — adding `read_vault`
to the `drives` callee set would pull `tmp` into `bindings` (`read_vault(tmp)` is a natural spelling
for Task 2's unreadable-note verify) and `tmp` is bound by `with temp_dir() as tmp`, which
`bindings`' closed RAISE set fires on: a false RED on a correct module (threat-model round 4, note 1).
And it does NOT duplicate the literal-path arm: a hard-coded `/Users/…` vault path in this module is
already RED under `FORBIDDEN_DEFAULT_PATTERNS` (`tests/test_vault_path_required.py:FORBIDDEN_DEFAULT_PATTERNS:278`),
which Task 15 RUNS over this item's touched files via that module's `_code_lines` — a run that is
load-bearing precisely because the standing wall's own universe stops at
`("obsidian_schemas", "scripts")` (`:320`) and does not reach `tests/`.

**And M8 and M6 are ONE rule about `_temp_vault`, stated at two different levels, not two clauses
that happen not to collide.** M6 leaves `os` legal BY NAME — `WALL_C_MODULES` is `FS_MODULES - {"os"}`
(`tests/test_name_gate_wall.py:WALL_C_MODULES:1043`) — precisely so `_temp_vault` may read
`os.environ`; M8 then scopes that read to `_temp_vault`'s own body. The import level says the
capability may exist in the module; the use-site level says it may be exercised in exactly one
function. A builder who "tidies" either into the other breaks the door: widening the import set to
`FS_MODULES | {"subprocess", "runpy"}` reddens `_temp_vault`'s environment read, and dropping M8's
by-function scope in favour of a flat token ban reddens it too.

Why all three ride `mutating_drive_vault_args` rather than landing as a FIFTH derivation: the three
censuses are one property — `bindings` is scoped BY `drives`, and `live_path_names` is what makes the
other two mean anything about the bytes written, so no one of them is a claim on its own — and `ast`
is single-homed to this module either way. So §6 still ships FOUR derivations and this round moves
none of the counts this document has already had to re-sync: §7's five-plus-three check count, R4's
"eight checks" and Task 16's expected direction are all unchanged, because M7 is one member of a set
Task 7 already builds and M8 is a third field asserted inside Task 9's ONE existing check.

### §7. The new check module `tests/test_lint_vault_fix_rules.py`

Five zero-argument top-level `def test_*` checks that signal by raising (`tests/support.py:1-19`),
one per criterion, plus three non-AC checks the plan adds (§5's unconditional print, M3's
temp-vault containment wall, and the WI-301 wall-membership closure). Its first statement is
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

**Every mutating drive's vault path is CONFINED to a fresh temp directory, the module asserts that
containment before the first mutating call, and the syntax half asserts PROVENANCE and not merely
spelling — every binding in that module of the identifier it accepts is a call to the single
`_temp_vault` door, so a drive cannot satisfy the wall by re-binding that name to a path the door
never produced (M3); the callee set the syntax half grades includes the CLI entry point `main`, so a
drive that reaches the live vault by OMITTING a vault argument is inside the wall rather than beside
it (M5); the callee set is the script's COMPLETE set of functions reaching a `vault_io` mutating door,
which is FOUR and includes the irreversible one, `quarantine_garbage` (M7); and the module imports no
subprocess-capable module, so the tool cannot be re-entered as a
child process where no in-process wall can see it at all (M6). And because grading a drive's vault
ARGUMENT cannot contain `apply_fixes` at all, the module NAMES the live vault path nowhere outside
`_temp_vault`'s own body (M8), which closes every omission route that SPELLS the path rather than
adding one more door — and not the routes that OBTAIN it without spelling it, which is why the three
clauses above remain load-bearing (corrected 2026-09-16; the previous wording read "which is the
clause that closes every omission route through every door rather than one more door").** This module is the first thing under
`tests/` that ever drives `run_lint(..., do_fix=True)` and `apply_fixes` (VD-4), it will do so on
every floor run for the life of the repo plus five `-S` re-execs (Task 15), and the path that must
never reach it is one attribute access away: `scripts/lint_vault.py:DEFAULT_VAULT:56` is
`os.environ.get("OBSIDIAN_VAULT_PATH", "")` on the very module the loader returns, and on Dave's
machine that variable is populated (`docs/lint-vault-live-baseline.md:10-11`). No standing wall
reaches this — `tests/test_vault_path_required.py:FORBIDDEN_DEFAULT_PATTERNS:278` is three literal
PATH shapes (`expanduser`, `Path.home()`, `/Users/`), none of which can see an environment read, and
the sweep that runs it stops its universe at `("obsidian_schemas", "scripts")` (`:320`), which the
new check module is not in — so the Design states the guard and the plan ships it. FOUR parts, and
the fourth is the one that carries the totality claim the other three cannot — **corrected
2026-09-15 after threat-model round 4 falsified the previous sentence, which read "THREE routes …
and the trio is what makes the guard total".** The first three grade a drive's vault ARGUMENT and its
route in, so they are each NECESSARY and jointly are NOT sufficient: round 4's four-line escape
satisfies all three with the runtime door executed and the import wall clean, and rewrites the live
vault, because `apply_fixes` ignores its `vault_path` and takes its write targets from the issues
(`:827` is that parameter's only occurrence; `by_file[issue.file_path]` at `:835`). The path can
arrive through the ARGUMENT of a drive (the runtime and syntax halves), through an ENTRY POINT that
needs no argument at all (the syntax half's callee set, M5 and M7), through the PROCESS BOUNDARY, where
no in-process wall can see it (the import half, M6) — or through the ISSUES a drive is handed, which
no argument-side clause grades at all, and which the SOURCE half closes at the three token shapes a
module can SPELL the live path with (M8, corrected 2026-09-16 from "the two tokens the live path can
only come from" — a path this module obtains without spelling it is outside the clause):

- **The RUNTIME half — ONE door, asserting before it returns.** `_temp_vault(tmp)` is the module's
  only constructor of a vault path. It calls `materialize_vault(tmp)` and then, BEFORE returning,
  asserts that `Path(vault).resolve()` is a strict descendant of `Path(tmp).resolve()` (via
  `relative_to`, which RAISES `ValueError` when it is not), that `tmp` is a directory this process
  obtained from `tests.support.temp_dir()`, and that the resolved vault equals neither
  `Path(lint_vault.DEFAULT_VAULT).resolve()` nor
  `Path(os.environ.get("OBSIDIAN_VAULT_PATH", "")).resolve()` — each compared only when that value
  is non-empty. `.get(..., "")` and never a subscript: `OBSIDIAN_VAULT_PATH` is UNSET in the graded
  and CI environments, where a bare `os.environ[...]` raises `KeyError` and reddens the door itself
  rather than a drive (threat-model round 2, note 2). The comparison is between RESOLVED paths the
  check itself holds — never a path prefix, a `cage-wt-` substring or a `/tmp` layout, which is
  WI-149's scar and is false in the graded environment.
- **The SYNTAX half — and it is what makes the door mandatory rather than a convention.**
  `test_every_mutating_drive_in_this_module_is_confined_to_a_temp_vault` runs §6(d)'s
  `mutating_drive_vault_args` over `[Path(__file__)]` and asserts FOUR things over the one
  `VaultArgScan` it returns — three of them stated here and the fourth, clause (iv), stated in the
  SOURCE half below, all four inside that ONE check and never as a ninth one — and the callee set that scan grades is §6(d)'s FOUR-member one,
  `apply_fixes` / `quarantine_garbage` / `run_lint` / `main`, so the entry point that needs no argument
  and the entry point whose write is irreversible are both graded by the same
  clauses rather than by a clause of its own (M5, M7). (i) SPELLING: every triple in `scan.drives` carries
  the identifier
  `vault`, and a drive passing `lint_vault.DEFAULT_VAULT`, a literal, an `os.environ` read or any
  other non-`Name` expression never reaches the assertion at all because §6(d) RAISES on it, while
  one passing some other bound name is RED naming the line. A `main` call — `lint_vault.main()`, a
  bare `main()`, or `main` with any argument at all — also never reaches the assertion, because `main`
  has no vault-argument position and §6(d) RAISES on it; the whole of M5 is that the callee set now
  contains it. A `quarantine_garbage` call is graded by the SAME clause with no new text, because its
  vault argument is the SECOND positional exactly as `apply_fixes`' is — the whole of M7 is that the
  callee set is the mutation-site census rather than a hand list, and it is the member whose write is
  irreversible. (ii) NON-VACUITY: `scan.drives` is
  NON-EMPTY, so a module that stopped driving the tool cannot pass by having nothing to grade.
  (iii) PROVENANCE: every 4-tuple in `scan.bindings` carries the provenance `"_temp_vault"` —
  i.e. every binding of `vault` anywhere in this module is a call to the one door, so the accepted
  identifier cannot be re-bound to a path the door never produced. Clause (iii) is why the third
  bullet exists rather than being folded into (i): (i) and (ii) alone are satisfied exactly by
  `vault = lint_vault.DEFAULT_VAULT` followed by `run_lint(vault, do_fix=True)` — the argument is
  spelled `vault`, the drive set is non-empty, and the runtime half never executes because
  `_temp_vault` was never called, which is the shape threat-model round 2 found and the reason M3's
  `desc` moved. With (iii) that same pair is RED at the BINDING's line with provenance `NOT_A_CALL`,
  and a re-binding through any other helper is RED naming that helper. The runtime half proves the
  door works; clauses (i)+(ii)+(iii) together are what prove every IN-PROCESS drive went through it,
  and no proper subset of them does.
- **The IMPORT half — and it is what closes the one route no in-process clause can see (M6).** Every
  clause above reads this module's own `ast` and grades the calls it makes IN THIS PROCESS. A drive
  that re-enters the tool as a CHILD PROCESS is graded by none of them: the callee is
  `subprocess.run` or `runpy.run_path`, not a name in §6(d)'s set, so `drives` collects nothing;
  `bindings` is scoped BY `drives`, so it collects nothing either; and `_temp_vault` is never called,
  so the runtime door never executes. The vault path is then a STRING inside an argv list, and
  omitting it altogether is enough — `[sys.executable, "scripts/lint_vault.py", "--fix"]` runs
  `--fix` against `OBSIDIAN_VAULT_PATH` via `main`'s `default=DEFAULT_VAULT` (`:1255`). So the route
  is refused at the IMPORT rather than at the call: `tests/test_lint_vault_fix_rules.py` names no
  subprocess-capable module, asserted by Task 15 handing `module_import_uses` the set
  `WALL_C_MODULES | {"subprocess", "runpy"}` over this file — `tests/derivations.py:FS_MODULES:68` is
  `{"os", "shutil", "tempfile", "fcntl", "filelock", "mmap"}` and
  `tests/test_name_gate_wall.py:WALL_C_MODULES:1043` is that minus `os`, so the standing set reaches
  NEITHER and the widening is the whole of M6. **The base set is IMPORTED, never hand-typed:**
  `from tests.test_name_gate_wall import WALL_C_MODULES`, then `| {"subprocess", "runpy"}`. Writing the
  members out (`{"shutil", "tempfile", "fcntl", "filelock", "mmap", "subprocess", "runpy"}`) would be a
  second home for a set `FS_MODULES` owns, and it would silently stop tracking the standing wall the
  day `FS_MODULES` gains a member — the same defect class as hand-typing a `SKIP_REASONS` member, which
  this module is already forbidden to do. The import is the tree's own idiom for this: four check
  modules already import from `tests.test_name_gate_wall`
  (`tests/test_company_name_contract.py:64`, `tests/test_name_gate_refusals.py:61`,
  `tests/test_address_splitter.py:53`, `tests/test_name_gate_delta_rule.py:55`). Two more facts make it
  cheap, read off the code rather than
  assumed: `tests/derivations.py:module_import_uses:847-870` already takes an arbitrary `modules`
  iterable and reports the ORIGINAL module name in both statement forms, so no derivation changes;
  and this is not a hypothetical shape — `tests/test_vault_path_required.py:_run_lint_vault:344-353`
  drives this very CLI by subprocess today and has to SCRUB `OBSIDIAN_VAULT_PATH` out of the
  environment to make it safe, which is the nearest precedent a builder would copy from. The
  `os`-attribute form of the same escape needs nothing added: `os_module_attribute_uses:800-844`
  returns every `os.<attr>` access and `OS_READONLY_NAMES:69` holds only
  `environ`/`getenv`/`sep`/`path`/`fspath`/`getcwd`, so `os.system` / `os.popen` / `os.execv` in this
  module is already RED under the wall Task 15 runs. This module's legitimate imports are outside the
  widened set by construction and were checked against it: `importlib.util`, `contextlib`, `io`,
  `pathlib`, `os` (`os` is excluded from `WALL_C_MODULES` by name, which is what lets `_temp_vault`
  read `os.environ`), plus the in-tree `tests.*` helpers.
- **The SOURCE half — and it is what closes the route the other three grade nothing about (M8).**
  Clauses (i)–(iii) grade a drive's vault ARGUMENT and the import half grades its process, and
  neither reaches the ISSUES a drive is handed — which is what `apply_fixes` actually writes from.
  So clause (iv) is asserted over §6(d)'s third census, inside the SAME check:
  **every 4-tuple in `scan.live_path_names` carries `enclosing == "_temp_vault"`, and
  `scan.live_path_names` is NON-EMPTY.** In words:
  the new check module NAMES the live vault path nowhere outside the body of `_temp_vault` — no `DEFAULT_VAULT` reference, no `OBSIDIAN_VAULT_PATH` string and no `os.environ` / `os.getenv` read anywhere else in the module.
  The scoping is by ENCLOSING FUNCTION and never by line range or occurrence count, for the reasons
  §6(d) rules; the non-emptiness is not decoration but the WI-235 element, since a zero-outside-the-door
  wall's cheapest green is a matcher that resolves nothing, and `_temp_vault`'s own three negative
  assertions are what make the non-empty arm true of a correct module. Clause (iv) is why this bullet
  exists rather than being folded into the syntax half: (i)+(ii)+(iii) are satisfied EXACTLY by
  `vault = _temp_vault(tmp)` beside `apply_fixes(lint_vault.check_noise(lint_vault.read_vault(lint_vault.DEFAULT_VAULT), idx), vault)`
  — correct spelling, correct provenance, non-empty drive set, the runtime door executed, the import
  wall clean, and the live vault rewritten. With (iv) that module is RED at the
  `lint_vault.DEFAULT_VAULT` reference's own line, with `enclosing` naming the check it sits in. It is
  a CLASS closure over SPELLINGS and not a fifth door: the shapes this module can NAME the live path
  with are three, closed by `ast` (`DEFAULT_VAULT`, itself `os.environ.get("OBSIDIAN_VAULT_PATH", "")`
  at `scripts/lint_vault.py:DEFAULT_VAULT:56`; the `"OBSIDIAN_VAULT_PATH"` string; a direct
  environment read — a literal `/Users/…` path being RED under the `FORBIDDEN_DEFAULT_PATTERNS` run
  Task 15 performs over this item's touched files), so no escape that SPELLS the path can reach it
  through any door, the four the census enumerates or a fifth nobody has thought of. **Corrected
  2026-09-16 after threat-model round 5 falsified the previous wording, which read "the live path has
  exactly two sources in this module's universe … so no omission-shaped escape can reach it through
  any door":** an omission shape that OBTAINS the path without naming it is outside clause (iv), and
  there is one — `obsidian_schemas/repositories/base.py:_resolve_vault_path:104-114` falls back to
  `os.environ.get(ENV_VAULT_PATH)` inside the library (`ENV_VAULT_PATH:75`, `_is_unconfigured:86-101`,
  `BaseRepository.__init__:154`, the four repositories at `obsidian_schemas/__init__.py:74-77`), so
  `repo = PersonRepository()` beside `read_vault(repo.vault_path)` passes (i)–(iv) and rewrites the
  live vault wherever that variable is exported. It is an OMISSION shape and not deliberate-act
  residue; closing it is the sufficiency call `## Scope Boundary` routes to Dave or the conductor, and
  it is OPEN.

The four parts answer four different questions and none of them answers another's: the runtime half
proves the door produces a contained path, the syntax half proves every in-process drive's ARGUMENT
came out of that door, the import half proves there is no out-of-process drive to grade, and the
source half proves the module cannot NAME the live path outside the door's own body. **Corrected
2026-09-16: the previous sentence continued "— which is the only one of the four that is total over
omission shapes, because the other three grade routes and a route is a list somebody wrote down", and
that is false.** The source half is total over the omission shapes that SPELL the path and not over
the ones that obtain it unspelled (the library's own `OBSIDIAN_VAULT_PATH` fallback, bulleted above),
so no part of the guard is total on its own and the other three are LOAD-BEARING rather than
belt-and-braces over it. A guard
missing any one of the four is satisfiable by a drive that mutates the live vault.

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

> **Build note — 2026-09-16 (build-runner).** Landed as ruled: the reader is
> `tests/test_fixture_vault.py:166`, fifth beside the four fence parsers, under the same whole-file
> `CENSUS_DIGEST` fixity. ONE deviation from the signature above, recorded as **Build Log D5** —
> it is `census_auto_fixable_rows(text=None, *, categories)`, because `CATEGORY_ORDER` must be read
> off the LOADED script module and this module has no `lint_vault` loader (a second one is refused
> by the single-loader rule), so the caller that holds the loaded module injects it. `(text=None)`
> keeps its position and meaning; a DEFAULT for `categories` would be the re-spelling this design
> forbids.

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

- **Case:** the gate passes and the FIRST `vault_io.write_note` at `:957` then raises (a stale
  precondition, a lock timeout). **Decision:** every still-undecided issue becomes `errored` —
  nothing on that file has been credited, because the first credit point is the statement after
  `:957` returns and it never ran. **Reasoning:** this is the behaviour CHANGE §4 names — today
  `fixed` was already credited at `:949` and a repair that never committed is reported as one. No
  standing test covers the old behaviour; AC-4(a)'s equality requires the new one.

- **Case:** the first write at `:957` COMMITS and the SECOND write at `:975` then raises — one file,
  a `missing_body_sections` issue and a `broken_wikilink` issue. **Decision:** the first issue is
  `repaired` and only the second is `errored`. The raise leaves the `with` block for the handler at
  `:993`, but the first issue left `undecided` on the statement after `:957` returned, so the
  handler cannot reach it; only `staged_wikilink`'s member is still undecided. **Reasoning:** this
  is M4 and it is the pair to the case above, so the two are stated as two. A single fold at the end
  of the lock block gets the case above right and this one exactly backwards — it reports a write
  that COMMITTED to one of Dave's notes as one that failed, which sends the operator to re-run a
  repair already on disk. AC-4(b)'s discriminating plant is this file.

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

- [x] **Task 1 — Capture the pre-build floor baseline.** Before the first edit, run the floor
  command (`/Users/davewascha/Workspaces/obsidian-schemas/.venv/bin/python -m pytest <worktree>/tests
  -q`, cwd-independent, the worktree's own path) and record BOTH the pass/fail verdict and the case
  count in the Build Log. Nothing is edited in this task. **Verify:** the Build Log carries a number
  and a verdict taken before any file changed; Task 16's delta is read against it.
  verify: baseline — the number is informational and its only artifact is the Build Log; no check asserts it.

- [x] **Task 2 — `VaultFile` gains `read_error` and `read_vault` records instead of discarding.**
  Edit `scripts/lint_vault.py`: add `read_error: Optional[str] = None` as the LAST field of
  `VaultFile:88-97`; add `from obsidian_schemas.repositories.base import UNREADABLE` beside the
  existing package imports at `:38-50`; replace the `except Exception: continue` at `:115-118` with
  the recording form in Design §1, field for field. The string `"unreadable"` must NOT appear
  anywhere in the file. **Verify:** `read_vault` over a directory containing one non-UTF-8 `.md`
  returns a `VaultFile` for it whose `read_error` is in `SKIP_REASONS`, and
  `build_indexes(...)["all_stems"]` contains that note's stem.
  verify: test_an_unreadable_note_is_reported_indexed_and_never_silently_dropped

- [x] **Task 3 — `check_structural` reports the unreadable note; the three sibling walks decline
  it.** Edit `scripts/lint_vault.py`: insert the `unreadable_note` arm as the FIRST branch of
  `check_structural`'s loop body, above the `parse_error` arm at `:297-305`, per Design §2; change
  `check_completeness:372`, `check_links:455` and `check_noise:670` from `if vf.parse_error:` to
  `if vf.parse_error or vf.read_error:`. `check_timeline` is untouched and the reason is recorded in
  a comment: it iterates the index, never `files`. **Verify:** a materialized corpus copy with a
  planted non-UTF-8 note produces exactly ONE issue at that path, it is not auto-fixable, and its
  message carries the imported reason value.
  verify: test_an_unreadable_note_is_reported_indexed_and_never_silently_dropped

- [x] **Task 4 — `FixOutcome` becomes four buckets; the two records and `DECLINE_GUARDS` land; each
  issue is credited where its own write commits.** Edit `scripts/lint_vault.py`: replace
  `FixOutcome:820-825` with the four-field form; add `FixErrorRecord`, `FixDeclineRecord` and the
  five `GUARD_*` constants plus `DECLINE_GUARDS` beside `NameGateRefusalRecord:805-818`, with
  `FixErrorRecord.reason` carrying `type(exc).__name__` and `FixDeclineRecord.guard` carrying a
  `DECLINE_GUARDS` member — never `str(exc)`, never note bytes, because both records feed the
  operator-facing summary (Design §3). Implement the §4 disposition rule inside `apply_fixes`:
  `undecided`, `staged_first` and `staged_wikilink` per file; a decline recorded at each of the five
  branches, removing the issue from `undecided` there; DELETE the `file_fixed` counter at `:882`,
  DELETE the `fixed += file_fixed` fold at `:949` outright rather than moving it, and DELETE the
  `fixed += 1` at `:972`; credit `repaired += len(staged_first)` on the statement after the
  `write_note` at `:957` RETURNS and `repaired += len(staged_wikilink)` on the statement after the
  `write_note` at `:975` RETURNS, each removing its list's members from `undecided`; one record per
  still-undecided issue in each handler and exactly ONE print per file.
  `NameGateRefusalRecord`'s field set does not move. **Verify:** the standing WI-021 battery still
  passes with only the field rename applied to it (Task 5); the four-bucket equality holds over a
  planted vault; and on ONE planted file carrying a `missing_body_sections` issue whose `:957` write
  commits beside a `broken_wikilink` issue whose `:975` write raises, the first comes back
  `repaired` and only the second `errored` — a build that folds once at the end of the lock block
  returns BOTH as `errored` and is red on that plant.
  verify: test_lint_vault_fix_guards_threads_and_records_refusals test_the_fix_outcome_surfaces_both_counts test_every_auto_fixable_issue_is_accounted_for_and_the_printed_summary_says_so

- [x] **Task 5 — The `fixed` → `repaired` rename across nine assertion sites in four modules.**
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

- [x] **Task 6 — The summary line: five labelled figures, printed on every `--fix` run.** Edit
  `scripts/lint_vault.py`: add `FIX_SUMMARY_LABELS` and `_format_fix_summary` per Design §5; bind
  `unreadable` from the PRE-fix `read_vault` at `run_lint:1160`; restructure `:1191-1199` so the
  summary prints unconditionally under `do_fix`, `"Re-scanning...\n"` is its own print inside
  `if fixable:`, and the `"No auto-fixable issues found."` else-arm is dropped. **Verify:**
  `run_lint(vault, do_fix=True, quiet=True)` over a planted vault prints one line carrying all five
  labels with integers, and over a vault with nothing auto-fixable prints the same line with
  `repaired 0`.
  verify: test_every_auto_fixable_issue_is_accounted_for_and_the_printed_summary_says_so test_the_fix_summary_prints_even_when_nothing_is_auto_fixable

- [x] **Task 7 — The four new scans in `tests/derivations.py`.** Add
  `auto_fixable_emitter_checks`, `auto_fixable_branch_checks`, `person_tier_arm_counts` and
  `mutating_drive_vault_args` per Design §6, each raising on a node it cannot resolve to a literal
  (or, for the fourth, to a bound `ast.Name`) rather than skipping it, each documented with the
  near-miss it must NOT match. The fourth returns the `VaultArgScan` TRIPLE of Design §6(d) — the
  `drives` call census, the `bindings` provenance census AND the `live_path_names` source census —
  and the second and third are the ones this
  task must not skip, because they are M3's and M8's requirements and the spelling census alone is
  satisfied by the very drive the wall exists to catch: for each identifier a `drives` triple names,
  every binding site of it in that module is recorded with a provenance (the callee name for a
  single-target `ast.Assign` of an `ast.Call`, the sentinel `NOT_A_CALL` for a single-target
  `ast.Assign` of any other expression), every OTHER binding construct in `ast`'s closed set RAISES
  naming module and line, and an identifier with no binding site in that module RAISES. The `drives`
  callee set is FOUR members and not two or three — `apply_fixes`, **`quarantine_garbage`**,
  `run_lint` and **`main`** — and it is the script's COMPLETE set of functions reaching a `vault_io`
  mutating door rather than a hand list, settled by the mutation-site census: the script's only
  mutation sites are `write_note` at `scripts/lint_vault.py:957` and `:975` inside `apply_fixes` and
  `ensure_dir` at `:1134` plus `move_note` at `:1140` inside `quarantine_garbage:1112-1144`. `main`
  is the entry point that reaches the live vault by OMISSION rather than by an expression a scan can
  see (`--vault` carries `default=DEFAULT_VAULT` at `scripts/lint_vault.py:1255` and it calls
  `run_lint(vault_path, …, do_fix=args.fix, …)` at `:1299-1308`), and it needs NO new rule: `main`
  has no vault-argument position at all, so every collected `main` call falls into the arm that
  already RAISES on a call passing a vault argument at neither position (M5). `quarantine_garbage` is
  the member whose write is IRREVERSIBLE — a rename — and this item PINS the two
  `garbage_candidate_*` detectors that decide what it moves, so a drive of it is a natural way to
  discharge AC-2's leg (b); it too needs NO new rule, because its vault argument is the SECOND
  positional at `:1113` exactly as `apply_fixes`' is at `:827` and §6(d)'s existing position table
  grades it as-is (M7). THIRD, `live_path_names`: every site in the scanned module naming the live
  vault path is recorded as `(module_id, lineno, token, enclosing)` at exactly three closed shapes —
  a `DEFAULT_VAULT` attribute or bare name, an `"OBSIDIAN_VAULT_PATH"` string Constant, and an
  `environ` / `getenv` attribute or bare name — with `enclosing` the INNERMOST enclosing
  `FunctionDef` / `AsyncFunctionDef` name or the sentinel `MODULE_LEVEL` at module scope, which is
  the scoping Design §6(d) rules and NOT a line range and NOT an occurrence count (M8). Nothing else
  in the module changes. **Verify:** over
  `[SCRIPTS_ROOT / "lint_vault.py"]` the two rule scans each return a five-member set and the two
  sets are equal; `person_tier_arm_counts` returns `(6, 4)` for that module; and
  `mutating_drive_vault_args` over a planted module carrying `apply_fixes(issues, vault, idx)`,
  `run_lint(vault, do_fix=True)`, `lint_vault.run_lint(vault_path=vault)` and
  `run_lint(lint_vault.DEFAULT_VAULT)` returns `vault` in `drives` for the first three and RAISES on
  the fourth, while ignoring a call to any other callee; a planted `lint_vault.main()` and a planted
  bare `main()` each RAISE naming their own line (M5's shapes — the callee set reaches them and `main`
  has no vault-argument position), while a planted call to some other zero-argument callee such as
  `setup()` is NOT collected at all, which is what proves the widening reaches `main` rather than
  every argument-free call; a planted `lint_vault.quarantine_garbage(issues, vault)` and a planted
  bare `quarantine_garbage(issues, vault)` each return `vault` in `drives` (second positional, the
  same arm `apply_fixes` grades under) while a planted
  `lint_vault.quarantine_garbage(issues, lint_vault.DEFAULT_VAULT)` RAISES naming its own line —
  M7's shapes, all three of which are collected by NOTHING under a three-member callee set — and, on
  the provenance half, a planted
  module binding `vault = _temp_vault(tmp)` returns provenance `"_temp_vault"` while one binding
  `vault = lint_vault.DEFAULT_VAULT` returns `NOT_A_CALL` and one binding it as a `for` target or a
  function parameter RAISES; and on the SOURCE half, a planted module carrying
  `lint_vault.DEFAULT_VAULT` inside `def _temp_vault(...)`, a second one carrying it inside
  `def test_x(...)`, a third carrying the string `"OBSIDIAN_VAULT_PATH"` at module scope and a fourth
  carrying `os.environ.get(...)` inside a `def` NESTED in `_temp_vault` return
  `enclosing` values `"_temp_vault"`, `"test_x"`, `MODULE_LEVEL` and the nested def's own name
  respectively — the fourth being what proves the scoping takes the INNERMOST def rather than the
  outermost (M8's shapes).
  verify: test_every_auto_fixable_rule_repairs_to_its_declared_oracle test_every_write_causing_detector_fires_exactly_on_its_declared_subjects test_every_mutating_drive_in_this_module_is_confined_to_a_temp_vault

- [x] **Task 8 — Widen the skip-reason wall's universe at BOTH call sites; hold both declared-homes
  sets at two.** Edit `tests/test_fixture_vault.py`: `:508-509` and `:1302` become
  `python_files_under(PACKAGE_ROOT, TESTS_ROOT, SCRIPTS_ROOT)`; the expected sets at `:510-514` and
  `:1315-1318` are UNCHANGED at two members. Add a non-vacuity assertion at each site that
  `scripts/lint_vault.py` is IN the universe the call returns. Editing one site and not the other
  leaves a half-extended wall that reads green (constraint 8). **Verify:** both walls green with the
  script in scope; the `ast` single-home wall at `:1309-1312`, which shares the `:1302` local, still
  answers `{"tests/derivations.py"}` over the larger universe.
  verify: test_skip_reason_declaration_binds_to_its_functions_returns test_the_fixture_vault_files_close_their_wall_memberships_by_running_each_predicate

- [x] **Task 9 — The new check module's skeleton, loader, temp-vault door and planting helpers.**
  Create `tests/test_lint_vault_fix_rules.py` with the `ensure_project_interpreter(__file__)` first
  statement, the `SCRIPTS_ROOT`-derived loader reusing
  `tests/test_lint_vault_fix_gate.py:_load_lint_vault:37-48`'s shape, and a
  `_plant(vault, stem, body)` that REFUSES a stem already in the corpus (raising with the stem
  named) so constraint 7 cannot be tripped silently. Ship the containment guard IN THIS TASK,
  because the skeleton is where every later check inherits it — THREE of Design §7's FOUR parts land
  here: the runtime half and the syntax half (M3), and the SOURCE half (M8) as clause (iv) inside the
  syntax half's ONE check, never as a check of its own; §7's remaining part, the import half (M6), is
  asserted by Task 15
  and constrains this module's imports rather than adding code here. (i) The
  RUNTIME half: `_temp_vault(tmp)` is the module's ONLY constructor of a vault path — it calls
  `materialize_vault(tmp)` and, before returning, asserts the resolved vault is a strict descendant
  of the resolved `tmp` (`Path(vault).resolve().relative_to(Path(tmp).resolve())`, which raises
  `ValueError` when it is not), that `tmp` is a directory this process took from
  `tests.support.temp_dir()`, and that the resolved vault equals neither
  `Path(lint_vault.DEFAULT_VAULT).resolve()` nor
  `Path(os.environ.get("OBSIDIAN_VAULT_PATH", "")).resolve()`, each compared only when that value is
  non-empty — `.get(..., "")` and NEVER a subscript, which raises `KeyError` in the graded and CI
  environments where the variable is unset and reddens the door rather than a drive; every
  comparison is between resolved paths the check itself
  holds and never a path prefix, a `cage-wt-` substring or a `/tmp` layout (WI-149). (ii) The SYNTAX
  half: add `test_every_mutating_drive_in_this_module_is_confined_to_a_temp_vault`, which runs Task
  7's `mutating_drive_vault_args` over `[Path(__file__)]` and asserts, over the ONE `VaultArgScan`
  it returns and inside this ONE check (never as a ninth check, which would move three counts this
  document has already re-synced once), all FOUR clauses of Design §7: every triple in
  `scan.drives` carries the identifier `vault`; `scan.drives` is NON-EMPTY, so a module that stopped
  driving the tool cannot pass by vacuity; every 4-tuple in `scan.bindings` carries the
  provenance `"_temp_vault"`, so every binding of that identifier in this module came out of the one
  door and a drive cannot satisfy the wall by re-binding the accepted name; and **every 4-tuple in
  `scan.live_path_names` carries `enclosing == "_temp_vault"`, with `scan.live_path_names` NON-EMPTY
  (M8)** — i.e. this module NAMES the live vault path nowhere outside `_temp_vault`'s own body. The third clause is M3's
  tightening and is not optional: without it `vault = lint_vault.DEFAULT_VAULT` followed by
  `run_lint(vault, do_fix=True)` passes clauses one and two while the runtime door never executes.
  **The FOURTH clause is M8's and is the one that is not optional for a different reason: the first
  three grade the vault ARGUMENT, and `apply_fixes` ignores its `vault_path` entirely** (`:827` is
  that parameter's only occurrence in the function; the write targets are `issue.file_path` at
  `:835`, `:853`, `:957`, `:975`), so a check binding `vault = _temp_vault(tmp)` and then handing
  `apply_fixes` an issue list built from `lint_vault.read_vault(lint_vault.DEFAULT_VAULT)` passes
  clauses one through three with the runtime door EXECUTED and the import wall clean, and rewrites
  Dave's live vault — and under `quarantine_garbage`, whose `vault_path` is only the destination root
  at `:1116` while the sources moved are `issue.file_path` at `:1121`, the same shape is data LOSS.
  **THE EXEMPTION'S MECHANISM IS RULED HERE AND THE BUILDER MUST NOT PICK ONE:** the scope is the
  INNERMOST enclosing `FunctionDef` / `AsyncFunctionDef` name, never a line range (which rots on the
  first edit) and never an allowed-occurrence count (which is greenable by moving the escape INTO
  `_temp_vault`), and it is the idiom Design §6(d)(b)'s branch census already uses. The exemption is
  MANDATORY rather than incidental, and this task's own runtime half is why: `_temp_vault` is ORDERED
  above to compare against `Path(lint_vault.DEFAULT_VAULT).resolve()` and
  `Path(os.environ.get("OBSIDIAN_VAULT_PATH", "")).resolve()`, so a flat "the module names neither
  token" clause would be RED against the module this very task prescribes — and the NON-EMPTY arm is
  what turns those three negative assertions into the wall's own WI-235 proof that the matcher
  resolves anything at all. M8 and M6 are ONE rule about `_temp_vault` at two levels and must be
  implemented as one: M6 leaves `os` legal BY NAME at the import (`WALL_C_MODULES` is
  `FS_MODULES - {"os"}`) precisely so this door may read `os.environ`, and M8 scopes that read to this
  door's body — so "tidying" the widened import set into `FS_MODULES | {"subprocess", "runpy"}`, or
  dropping M8's by-function scope for a flat token ban, reddens the door itself either way. Do NOT
  implement M8 by widening the graded IDENTIFIER set instead: adding `read_vault` to the `drives`
  callee set pulls `tmp` into `bindings` (`read_vault(tmp)` is a natural spelling for Task 2's
  verify) and `tmp` is bound by `with temp_dir() as tmp`, which `bindings`' closed RAISE set fires
  on — a false RED on a correct module (threat-model round 4, note 1).
  Every `apply_fixes(...)`, `quarantine_garbage(...)` and `run_lint(..., do_fix=True)` this module
  adds in Tasks 10-15
  takes its vault argument from that local, and that local is bound by `_temp_vault(...)` and by
  nothing else; and every issue list any of them is handed is built from a scan of THAT vault, which
  is what clause (iv) enforces by leaving the module no way to name any other one. The module must not name `ast`, must not hand-type
  any `SKIP_REASONS` member, and must import NO subprocess-capable module — neither `subprocess` nor
  `runpy`, in either statement form and under any alias, which is the PROCESS-BOUNDARY route of Design §7 and is
  asserted by Task 15 (M6); its legitimate imports are `importlib.util`, `contextlib`, `io`,
  `pathlib`, `os` and the in-tree `tests.*` helpers, all outside the widened set. DEFINE
  `test_every_mutating_drive_in_this_module_is_confined_to_a_temp_vault` FIRST among this module's
  checks: pytest runs a module's checks in definition order, so the detector then fires ahead of every
  driving check in an ordinary floor run. It is an ordering COURTESY and not a guarantee — `-k`
  selection and direct invocation bypass it, and the guarantee is the runtime door plus M5/M6/M7/M8
  closing
  the routes that avoid the door — but it costs nothing at authoring time and cannot be retrofitted
  cheaply (threat-model round 3, note 2). **Verify:** the module imports under the floor; its plant helper raises
  on `@Dave  Marrowyn Fennwick`; the containment check is green and goes RED when one drive is
  hand-edited to pass `lint_vault.DEFAULT_VAULT` (observed and reverted), RED again when a check is
  hand-edited to re-bind `vault = lint_vault.DEFAULT_VAULT` before an otherwise correctly-spelled
  drive — the provenance clause naming that binding's line (observed and reverted) — RED again
  when `_temp_vault` is hand-edited to return a path outside `tmp` (observed and reverted), and RED
  again when a check is hand-edited to build its issue list from
  `lint_vault.read_vault(lint_vault.DEFAULT_VAULT)` while still passing the correctly-bound `vault`
  to `apply_fixes` — clause (iv) naming that reference's line with `enclosing` naming the check, and
  clauses (i)-(iii) all staying GREEN on it, which is what proves the source half is load-bearing
  rather than a restatement of the argument half (observed and reverted).
  verify: test_every_mutating_drive_in_this_module_is_confined_to_a_temp_vault test_wall_membership_is_closed_for_every_file_this_item_touches

- [x] **Task 10 — AC-1's check: the derived rule set, the total oracle table, the five oracles.**
  Add `test_every_auto_fixable_rule_repairs_to_its_declared_oracle` per AC-1's three legs — the
  two-sided emitter≡branch equality driven through Task 7's scans, an oracle table whose key set
  EQUALS the derived set, and the five per-rule oracles with their planted discriminators (the FALSE
  boolean arm; the byte-for-byte `@Tarnquil  Brenvik` stem; the some-but-not-all-sections note with
  real content; the four-topic, no-topic and already-populated-Timeline meetings; the ambiguous
  two-candidate link). **Verify:** the check is green, and mutating any one oracle's expected value
  by hand turns it red (observed and reverted).
  verify: test_every_auto_fixable_rule_repairs_to_its_declared_oracle

- [x] **Task 11 — AC-2's check: seven write-causing detectors, both directions, plus the arm
  table.** Add `test_every_write_causing_detector_fires_exactly_on_its_declared_subjects` per AC-2's
  three legs — the false-positive table over the unplanted corpus keyed `(path, check) -> issue
  COUNT` (8 issues over 5 distinct person notes for `meeting_missing_from_timeline`, zero for the
  other six), one planted subject per pinned member, and `classify_person_tier`'s six-arm table
  bound to BOTH numbers Task 7's `person_tier_arm_counts` returns. **Verify:** green; and an arm
  table declaring five rows is red against the code-side count of 4 `return "active"` sites plus the
  6 docstring bullets.
  verify: test_every_write_causing_detector_fires_exactly_on_its_declared_subjects

- [x] **Task 12 — AC-3's check: reported, indexed, quiet, never written.** Add
  `test_an_unreadable_note_is_reported_indexed_and_never_silently_dropped` per AC-3's four legs,
  including the discriminating second plant that LINKS to the unreadable stem and the planted
  meeting that lists it as an attendee — the pair that separates "the skip is loud" from "the report
  stopped lying about other notes". The reason is read from the imported `SKIP_REASONS`, never
  spelled. **Verify:** green; and reverting Task 2's `files.append(...)` to `continue` turns legs
  (a) and (b) red (observed and reverted).
  verify: test_an_unreadable_note_is_reported_indexed_and_never_silently_dropped

- [x] **Task 13 — AC-4's check: the partition, the tie-break, the records, the printed bytes.** Add
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

- [x] **Task 14 — The TWO readers (census table, baseline artifact) and AC-5's check.** Add
  `census_auto_fixable_rows` to `tests/test_fixture_vault.py` beside the four fence readers, per
  Design §9 — keyed on the message SHAPE, stripping a trailing parenthetical IFF its content is a
  member of `scripts/lint_vault.py:CATEGORY_ORDER:1003`, read off the loaded module and DISCARDED.
  LANDED at `tests/test_fixture_vault.py:166`, fifth among the census readers as specced; its
  signature is `(text=None, *, categories)` rather than §9's `(text=None)`, because the census
  readers' module has no `lint_vault` loader and may not mint a second one, so the vocabulary is
  injected by the caller that holds the loaded module — recorded as **Build Log D5**.
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

- [x] **Task 15 — Join the foreign-interpreter wall and close the inbound wall memberships.** Add
  `ROOT / "docs" / "lint-vault-fix-safety.md"` to `WORK_ITEM_DOCS` in
  `tests/test_ac_interpreter.py:47-50` — the tuple whose own docstring says an item whose criteria
  EXECUTE the library "joins the wall that already exists" rather than writing a second copy of it.
  Then add `test_wall_membership_is_closed_for_every_file_this_item_touches` to the new module,
  modelled on `tests/test_name_gate_wall.py:test_wall_membership_is_closed_by_running_each_walls_predicate:1057-1075`:
  declare this item's touched-file tuples and RUN each standing wall's own shipped predicate on
  their final text — `filesystem_mutation_uses` / `os_module_attribute_uses` / `module_import_uses`
  over the script AND over the new check module (which M3's runtime door makes an `os.environ`
  reader and a `Path.resolve` caller, so it is inside those predicates' reach and must be run rather
  than assumed clean). **`module_import_uses` over the new check module takes the WIDENED module set
  `WALL_C_MODULES | {"subprocess", "runpy"}` and asserts it returns NOTHING (M6)** — the standing set
  reaches neither, because `tests/derivations.py:FS_MODULES:68` is
  `{"os", "shutil", "tempfile", "fcntl", "filelock", "mmap"}` and
  `tests/test_name_gate_wall.py:WALL_C_MODULES:1043` is `frozenset(FS_MODULES - {"os"})`, so without
  the widening the module could re-enter the CLI as a child process and satisfy every in-process
  clause of Design §7 while mutating the live vault. IMPORT the base set —
  `from tests.test_name_gate_wall import WALL_C_MODULES` — and never hand-type its members: a written-out
  copy stops tracking `FS_MODULES` the day it gains one, and four check modules already import from that
  module (`tests/test_company_name_contract.py:64`, `tests/test_name_gate_refusals.py:61`,
  `tests/test_address_splitter.py:53`, `tests/test_name_gate_delta_rule.py:55`). No derivation changes:
  `tests/derivations.py:module_import_uses:847-870` already takes an arbitrary `modules` iterable and
  reports the ORIGINAL module name in both statement forms, so an aliased `import subprocess as sp` is
  reported as `subprocess`. Over `scripts/lint_vault.py` the set stays the STANDING `WALL_C_MODULES`,
  which is the universe the routing wall already grades that file under; read off the code rather than
  assumed, the script imports neither `subprocess` nor `runpy` (`:20-31`, `:36-50`), so the asymmetry
  costs nothing today and exists only so this task does not silently re-scope a standing wall. Then
  `frontmatter_write_arms` (whose `ArmId("scripts/lint_vault.py", "apply_fixes", 1)`
  is pinned by a two-sided equality at `tests/test_company_name_contract.py:602-616`),
  `character_class_strip_sites`, `address_splitting_implementations`, `modules_using_ast` over
  `python_files_under(PACKAGE_ROOT, TESTS_ROOT)`, `skip_reason_literal_sites` over the WIDENED
  universe, `FORBIDDEN_DEFAULT_PATTERNS` via `tests/test_vault_path_required.py:_code_lines`, and
  `criterion_checks` resolving all five check names uniquely through `check_module`. Anything the
  RUN returns that this spec did not name is recorded in the Build Log and satisfied — never worked
  around, and never satisfied by narrowing a wall. The widened set's REACH is proved in this SAME
  check rather than assumed from a zero (WI-235 — `matches == 0` is satisfied identically by a matcher
  that resolves every claimed shape and by one that resolves none), and inside it rather than as a
  ninth check: drive `module_import_uses` under `WALL_C_MODULES | {"subprocess", "runpy"}` over
  planted text carrying `import subprocess`, `import subprocess as sp`,
  `from subprocess import run`, `import runpy` and `from runpy import run_path` — all five must be
  FOUND and each must report the ORIGINAL module name (`subprocess` / `runpy`), never the alias — and
  over planted text carrying this module's own legitimate imports `import importlib.util`,
  `from contextlib import redirect_stdout`, `import io` and `from tests.support import temp_dir` plus
  the STRING `"subprocess"` in a docstring, none of which may be found. **Verify:** green, and the
  item's five criteria each exit 0 under the `-S` foreign interpreter having actually delegated; the
  widened set is proved reaching by the five planted import shapes and proved non-total by the five
  planted near-misses; and adding `import subprocess` to the new check module by hand turns the check
  RED naming that line (observed and reverted).
  verify: test_wall_membership_is_closed_for_every_file_this_item_touches test_every_acceptance_criterion_passes_under_the_conveyors_interpreter

- [x] **Task 16 — Run the floor and record the delta against Task 1.** Run the floor command and
  record the verdict and case count in the Build Log beside Task 1's baseline. The assertion is the
  PROPERTY (GREEN, and the count is not LOWER than the baseline — a drive that lands fewer cases has
  silently lost a test file), never a hardcoded number: the count moves with every sibling ship and
  CLAUDE.md says never to trust a number written down. Expected direction: up by the new module's
  eight checks. **Verify:** floor GREEN; the two numbers are both in the Build Log; any RED is
  reported with its output rather than summarised.
  verify: hand-run — the floor is a whole-suite command whose GREEN and case count are recorded in the Build Log, not a standing artifact any single check can assert.

## Build Log — 2026-09-16 (build-runner, cold-start)

**Floor bracket (Tasks 1 and 16).** Baseline, taken before the first edit:
**681 passed, GREEN**. Final, after all sixteen tasks: **689 passed, GREEN** — up 8, which is exactly
`tests/test_lint_vault_fix_rules.py`'s eight checks, and the direction Task 16 predicted. No RED at
any point that is not recorded below. Shell liveness was probed first (`echo hi`) per the abort
protocol's step 0; Bash exec'd normally for the whole build.

**All sixteen tasks landed as specced. Five deviations, each forced by a collision the spec's own
prose did not anticipate, each resolved in the direction that keeps BOTH colliding requirements
rather than trading one off.** (D5 was added on 2026-09-16, answering the build-exit code review's
B1: the deviation was real and legitimate, the FAILURE was that it went unrecorded while three
document surfaces went on describing a tree that had not shipped. The count in this sentence is part
of what B1 falsified, so it moves with the entry.)

**D1 — `FIX_SUMMARY_LABELS`' fifth member is the IMPORTED `UNREADABLE`, not the literal Design §5
spells.** Design §5 gives the tuple as
`("repaired", "refused", "errored", "declined", "unreadable")`, and Design §8 / AC-3(a) require the
script to contain no `ast.Constant` equal to a `SKIP_REASONS` member once the wall's universe reaches
`scripts/`. Those are the same string. Landing §5 verbatim made `skip_reason_literal_sites` report
`scripts/lint_vault.py` as a THIRD hand-typed home and turned both of Task 8's walls RED — observed,
not reasoned about. Resolved as `(..., UNREADABLE)`: **the printed bytes are unchanged** (`unreadable`
is still the fifth label an operator reads and still what AC-4(d) parses), the script hand-types no
vocabulary member, and the printed word and the recorded reason are now provably the same word. The
rider is that no consumer may hand-type it either, so AC-4(d)'s tuple pin reads
`("repaired", "refused", "errored", "declined", UNREADABLE)` with the fifth member imported — still a
hand-written equality pinning all five positions, per Task 13.

**D2 — no helper in the new check module may take a parameter named `vault`.** M3's `bindings` census
RAISES on any binding of a graded identifier that is not a single-target `Assign`, and an `ast.arg` is
one of those shapes. The first draft passed the vault path into thirteen helpers as a parameter and was
correctly RED at the first one. Every helper now takes the temp ROOT and binds `vault = _temp_vault(root)`
itself, which is what Task 9 actually prescribes ("that local is bound by `_temp_vault(...)` and by
nothing else") — so the door is called once per helper rather than once per check. Same rule inside
`_temp_vault`: it binds its own result as `built`, because `vault = materialize_vault(tmp)` would be a
binding with provenance `"materialize_vault"` and RED at clause (iii).

**D3 — three of the five decline sites are unreachable through the real check pipeline, so their
subjects are HAND-BUILT issues.** `:890` needs a `field_type_mismatch` issue on a note whose
`auto_created` is already a bool, and `check_structural:338` emits that issue only when the value IS a
string; `:906` needs a `missing_body_sections` issue on a type `get_expected_sections` returns `[]`
for, and `check_structural` only reaches that branch for a type in `TYPE_TO_MODEL`. `:935-936` is the
same shape. That is not a shortcut — it is the finding: those three guards sit on branches an honest
scan cannot reach, which is precisely why they could decline forever with nothing going red, and
AC-4(a) drives `apply_fixes` directly for exactly this reason. The other two (`:913` under the
signature default, `:963-973` via the inner-trailing-space link `check_links:510` strips) ARE produced
end-to-end and are planted as the spec names them.

**D4 — two wall re-runs in Task 15 are SCOPED, with the scope stated rather than an exception list.**
Task 15 says to run each standing wall's own predicate over this item's touched files and to satisfy
anything the RUN returns rather than work around it. Two returned pre-existing, legitimate members,
because their walls' own universe is `(PACKAGE_ROOT, SCRIPTS_ROOT)` and does not reach `tests/`:
`address_splitting_implementations` returns `tests/test_name_gate_refusals.py:_d8_constructible`, and
`FORBIDDEN_DEFAULT_PATTERNS` via `_code_lines` returns `tests/test_fixture_vault.py:1121` — which is
that module's own PRIVACY assertion, a line that FORBIDS `/Users/` and therefore necessarily contains
it, which is a limitation of a text scan and not a default resolved anywhere. Neither is anything this
item introduced and neither is narrowable without an exception list. So the address/character-class
walls run over the touched files that are INSIDE the routing universe (the script), and the
forbidden-path patterns run over the two files this item AUTHORS (the script and the new check module)
— which is the scope Design §7 names when it says the re-run exists so "a hard-coded `/Users/…` vault
path in this module is already RED". Both scopings are stated in the check's own comments with their
reason. Two of the item's own would-be offenders were fixed rather than exempted: the
`bind_literal` fixture now spells `/somewhere/else/vault` (it drives the `NOT_A_CALL` provenance arm,
and the path shape was never the point), and AC-5(c)'s privacy assertion reads the imported
`FORBIDDEN_DEFAULT_PATTERNS` instead of spelling a member — which is strictly better, since it now
tracks that list.

**D5 — `census_auto_fixable_rows` takes the category vocabulary as a REQUIRED KEYWORD, so its
signature is `(text=None, *, categories)` and not Design §9's `(text=None)`.** Design §9, Task 14,
the `tests/test_fixture_vault.py` write-target fence and AC-5(b)'s signed desc all rule that the
fifth census reader lands BESIDE WI-016's four, in `tests/test_fixture_vault.py`, under the same
whole-file `CENSUS_DIGEST` fixity — and it does (`tests/test_fixture_vault.py:166`, fifth in a file
that now carries `census_class_rows:122`, `census_pool_rows:140`, `census_meta:145`,
`census_auto_fixable_rows:166`, `census_identity_residue:432`). The collision is one level in, at
the SIGNATURE: the reader must read its category vocabulary off the LOADED script module rather than
re-spell it (§9, AC-5(b): "read from the loaded module rather than re-spelled"), and the census
readers' module has no `lint_vault` loader. Minting one there would be a THIRD loader in this tree
and is refused by `tests/test_lint_vault_fix_rules.py:_load_lint_vault`'s own docstring rule ("the
SAME shape `tests/test_lint_vault_fix_gate.py:_load_lint_vault` already carries, never a second
loader"); giving `categories` a DEFAULT in the census module would be precisely the re-spelling
AC-5(b) forbids, one file over. So the vocabulary is INJECTED by the caller that already holds the
loaded module — `tests/test_lint_vault_fix_rules.py:_census_rows`, the single line that holds this
seam, passing `lint_vault.CATEGORY_ORDER` — and it is keyword-ONLY and default-LESS so that no
future caller can silently supply a hand-typed vocabulary. `(text=None)` keeps its position and its
meaning, so the reader is still driven the way its four siblings are.

The deviation is BOUNDED and not load-bearing on any signed promise: AC-5(b)'s three requirements of
this reader — that it lands in `tests/test_fixture_vault.py`, that it rides `CENSUS_DIGEST`, and
that it reads `CATEGORY_ORDER` off the loaded module rather than re-spelling it — are all TRUE of
what shipped; what moved is one parameter in a signature the criterion does not pin. **Observed,
not reasoned about (mutation 15):** with the reader in its new home, inverting its strip rule so the
category is never removed turns
`test_the_live_vault_baseline_is_committed_shaped_and_agrees_with_the_census` RED at its own WI-235
fixture (`Left contains 1 more item: {'Missing sections: … (structural)': 821}`), which is what
proves the check drives the MOVED reader and not a stale copy. The floor is GREEN at 689 both before
and after the move — the reader changed module, not behaviour.

**Task 3's prescribed comment landed on 2026-09-16, answering the same review's N1.** Task 3 requires
that `check_timeline` be left without an `or vf.read_error` guard *and that the reason be recorded in
a comment*; the first pass did the former and not the latter, which left the one question a future
reader is most likely to ask — why three sibling walks got a guard and this one did not — answered
nowhere. `scripts/lint_vault.py:624-631` now carries it. The reasoning was correct and is unchanged:
`check_timeline` never iterates `files` at all (it walks `idx["meetings"]` and `idx["persons"]`), and
a `read_error` `VaultFile` keeps `entity_type == ""` so `build_indexes` admits it to neither index.
This is a task artifact that was MISSING and is now present, not a deviation, so it gets no D-number.

**One defect in this build's own wall, found by mutate-and-observe and fixed (M9).** Hand-editing
`_temp_vault` to return a path outside its `tmp` left
`test_every_mutating_drive_in_this_module_is_confined_to_a_temp_vault` GREEN: its four clauses read
SYNTAX and never CALL the door, so the runtime half was only exercised by whichever driving check ran
first. The full floor caught it a few checks later, but the containment check is defined FIRST
precisely so the detector fires ahead of the drives — and it could not do that for the one clause that
needs the door to run. `_check_the_runtime_door_contains_what_it_builds` now exercises the door inside
that first check. Its own first draft re-asserted the door's live-path comparisons and was RED on
clause (iv) — correctly, since naming either token outside `_temp_vault`'s body is exactly what that
clause forbids; the comparisons stay the door's own and the helper asserts containment only.

**Mutate-and-observe: SIXTEEN mutations, every one observed RED and reverted, none leaving a plant
behind.** The `## Verification` section names fourteen; #7b is M4's exact discriminating
shape, which the first pass mis-applied (it DELETED a credit point rather than relocating it, which is
red for a different reason) and which is the one that matters most, so both are recorded; #15 is the
2026-09-16 revision round's, proving the moved census reader's seam (D5).
`OBSIDIAN_VAULT_PATH` was scrubbed from every mutation run's child environment, and the three
mutations that name the live path were driven under a `-k` selection that executes only the
containment check — so no mutation could reach the live vault even by accident.

| # | mutation | observed RED at |
|---|---|---|
| 1 | revert `read_vault`'s `files.append` to a bare `continue` | AC-3(b) — "the unreadable note's STEM is gone from the index" |
| 2 | `person_missing_name` writes `clean_person_name(stem)` | AC-1 — "the repair wrote 'Tarnquil Brenvik'; the oracle is the stem byte-for-byte" |
| 3 | drop the `meeting_missing_from_timeline` repair branch | AC-1(a) — emitter≡branch equality, `emitters-only [...]` |
| 4 | hard-code the fifth figure in `_format_fix_summary` | AC-4(d) — printed line vs computed figures |
| 5 | delete one `return "active"` arm from `classify_person_tier` | AC-2(c) — "has 3 `return \"active\"` sites; the arm table was written against 4" |
| 6 | match the baseline's headings by EQUALITY instead of prefix | AC-5(a) — RED on §1's trailing qualifier |
| 7 | delete credit point 1 outright | AC-4(a) — "18 auto-fixable issues in, 15 accounted for" |
| 7b | **collapse BOTH credit points into one fold at the END of the lock block** | AC-4(b) — "the issue whose write COMMITTED must stay repaired; got 0", with BOTH issues in `errored`. This is M4's discriminator and the mirror-image defect §4 argues against |
| 8 | a drive passes `lint_vault.DEFAULT_VAULT` | containment (i) — the scan RAISES on the non-`Name` argument |
| 9 | `_temp_vault` returns a path outside its `tmp` | containment RUNTIME half — `ValueError: ... is not in the subpath of ...` |
| 10 | re-bind `vault = lint_vault.DEFAULT_VAULT` before a correctly-spelled drive | containment (iii) ONLY — "(i)" and "(ii)" stay green, which is what makes this the mutation that separates `drives` from `bindings` |
| 11 | plant `lint_vault.main()` in a check the selection does not execute | containment — "drives `main()` with a vault argument at neither its declared position" (M5) |
| 12 | `import subprocess` in the new check module | wall membership — the widened `module_import_uses` set (M6) |
| 13 | `lint_vault.quarantine_garbage(garbage, tmp)`, naming no live token | containment — `bindings` RAISES on the `with ... as tmp` binding (M7). Collected by NOTHING under a three-member callee set |
| 14 | issue list from `read_vault(lint_vault.DEFAULT_VAULT)`, drive still correctly bound | containment (iv) ONLY — "(i)"–"(iii)" green and the door EXECUTED, which is what proves the source half is load-bearing (M8) |
| 15 | invert `census_auto_fixable_rows`' strip rule IN ITS NEW HOME so the category is never removed | AC-5 — its own WI-235 fixture, `Left contains 1 more item: {'Missing sections: … (structural)': 821}`. Proves the check drives the reader that now lives in `tests/test_fixture_vault.py` rather than a stale copy in the check module (D5) |

**The counting walls ship their claimed shapes (WI-235).** Every one of the five count-oracles drives
its claimed match-shapes AND its near-misses through the wall's own predicate as a standing fixture:
`drives` (four collected spellings, M5's two RAISE shapes with the `setup()` / `helpers.main_menu()`
near-miss, M7's three), `bindings` (five provenance shapes, the honest-module near-miss, seven
closed-set RAISES), `live_path_names` (three tokens × two spellings, the four scoping shapes including
the nested-`def` one an occurrence-count reading is green on, six near-misses, and the non-vacuity
arm), `module_import_uses` under the widened set (five import shapes all reported under the ORIGINAL
module name, five near-misses drawn from this module's own legitimate imports), and the AC-5 readers
— `baseline_sections` (prefix match plus the unmatched-ordinal RAISE), `is_argv_fence` (both arms),
the `_HEX40` delimited matcher (the 64-hex near-miss), `baseline_auto_fixable_rows` (the bold totals
row skipped by its own property) and §9's `census_auto_fixable_rows`, which since D5 lives in
`tests/test_fixture_vault.py` and is driven here THROUGH THE IMPORT, so the fixture grades the
shipped reader rather than a copy. Every fixture is planted TEXT handed to the predicate, never a line of the module's own
source — which is why they may legally spell tokens clause (iv) forbids, the Constant arm being
EQUALITY and never containment.

**Facts measured rather than carried forward.** The corpus's pinned-detector output was EXECUTED, not
trusted: `meeting_missing_from_timeline` fires **8 times over 5 distinct person notes**
(`@Thrandell Ibberly` 2, `@Isolde Quenlaw` 2, `@Morvette Harkwell` 2, `@Caldreth Zebrant` 1,
`@Elowick Varnholt` 1), and the other six pinned checks fire ZERO times across all 53 notes — exactly
the figure AC-2(a) declares. `auto_fixable_emitter_checks` and `auto_fixable_branch_checks` each
return the same five members. `person_tier_arm_counts` returns `(6, 4)`. `frontmatter_write_arms` still
reports exactly `ArmId("scripts/lint_vault.py", "apply_fixes", 1)` — the `write_frontmatter` call did
not move. `read_vault` now returns 53 files where it returned 52, and `@Isolde Varnholt.md` is
reported as one non-auto-fixable `unreadable_note` issue. AC-5 is GREEN against HEAD with no edit to
either artifact (821/835 delta `+14`, 315/315, 19/19, 0/0, 0/0). All five criteria exit 0 under the
`-S` foreign interpreter **having actually delegated** — the wall now runs 15 criteria per floor, up
from 10, which is the five re-execs `## Write Targets` disclosed.

**Standing equalities deliberately not disturbed.** `NameGateRefusalRecord._fields` is still
`("path", "pattern")` — per-issue refusal counting is obtained by emitting one record per refused
issue, never by widening the record. `apply_fixes` still has exactly ONE frontmatter write arm. The
`delta` key set is still closed at `{auto_created, name}`. The `ast` capability is still single-homed
to `tests/derivations.py`, and the skip-reason vocabulary still has exactly TWO declared homes with
`scripts/` inside the scanned universe.

**Out of scope and untouched, as `## Scope Boundary` rules.** The YAML re-serialization (A3/A3b), the
`--quarantine` decision logic, the package export (WI-030), and the routed sufficiency call on the
library's own `OBSIDIAN_VAULT_PATH` fallback — which remains OPEN with Dave or the conductor and is
DECLARED, not closed. Nothing under `obsidian_schemas/**` changed.

**Still owed by the conductor, outside the cage.** The EXIT half of A7's bracket:
`scripts/lint_vault.py --vault "$VAULT" --report` re-run on the post-build tree, appended to
`docs/lint-vault-live-baseline.md` §4 whose commands and figure names are already committed as bytes.
`--report` and never `--fix`. It is a declared ship condition of this item and a caged builder cannot
perform it — a builder's write outside its worktree is reverted at the merge boundary, so a plan-task
replay would change nothing and report success.

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
why: Task 7 — `auto_fixable_emitter_checks`, `auto_fixable_branch_checks`, `person_tier_arm_counts` and `mutating_drive_vault_args` (the fourth is the containment wall, and it returns a TRIPLE because the requirement has three halves: `drives`, every `apply_fixes` / `quarantine_garbage` / `run_lint` / `main` call's vault argument in the new check module, which the wall asserts is the identifier `vault`; `bindings`, every binding site of that identifier in the same module with the provenance of each, which the wall asserts is a call to the one temp-vault door — the spelling census alone is satisfied by `vault = lint_vault.DEFAULT_VAULT; run_lint(vault, do_fix=True)`, which is the drive M3 exists to catch; and `live_path_names`, every site NAMING the live vault path with the innermost enclosing function of each, which the wall asserts is `_temp_vault` — because both argument censuses grade a `vault_path` that `apply_fixes` never reads, so a correctly-contained drive handed issues scanned from `lint_vault.read_vault(lint_vault.DEFAULT_VAULT)` passes both while rewriting the live vault, M8). The callee set is FOUR members and it is the script's COMPLETE set of functions reaching a `vault_io` mutating door rather than a hand list: `main` is in it (M5) because it is the entry point that reaches the live vault by OMISSION — `--vault` carries `default=DEFAULT_VAULT` at `scripts/lint_vault.py:1255` — and it needs no new rule, having no vault-argument position at all; `quarantine_garbage` is in it (M7) because it is the only other function reaching a mutating door (`ensure_dir:1134`, `move_note:1140`) and its write is the irreversible one, and it needs no new rule either, its vault argument being the SECOND positional at `:1113` exactly as `apply_fixes`' is at `:827`. `module_import_uses` is NOT touched by this item: M6 rides it with a widened `modules` argument from Task 15, and the predicate already takes an arbitrary iterable (`:847-870`). They land here and nowhere else because `ast` is single-homed to this module by three standing set-equality walls (`tests/test_loud_fail_harness.py:103`, `tests/test_name_gate_wall.py:1136`, `tests/test_fixture_vault.py:1309-1312`); a private copy in the check module is red on all three before it asserts anything (constraint 2).
```

```writes
path: tests/test_lint_vault_fix_rules.py
why: Tasks 9-15 — the new check module. Five zero-argument `def test_*` criteria checks plus `test_the_fix_summary_prints_even_when_nothing_is_auto_fixable` (Design §5 ruling 1), `test_every_mutating_drive_in_this_module_is_confined_to_a_temp_vault` (M3's syntax half over this module's own source, defined FIRST in the module so the detector fires ahead of the driving checks, grading the FOUR-member callee set that includes the CLI entry point `main` — M5 — and the irreversible `quarantine_garbage` — M7 — and carrying as its clause (iv) the SOURCE half that refuses this module any mention of the live vault path outside `_temp_vault`'s own body — M8, which closes every omission route that SPELLS the live path rather than adding one more door, and not the routes that OBTAIN it unspelled, which is why M5, M6 and M7 stay load-bearing beside it rather than belt-and-braces) and `test_wall_membership_is_closed_for_every_file_this_item_touches` (the WI-301 inbound half, which also hands `module_import_uses` the widened set `WALL_C_MODULES | {"subprocess", "runpy"}` over this file — M6, the reason this module may name neither in any statement form or alias); the `_temp_vault(tmp)` door that is the module's only constructor of a vault path and asserts containment before returning (M3's runtime half, Design §7); and the four baseline readers of Design §9b (`baseline_sections`, `fenced_blocks`, `is_argv_fence`, `baseline_auto_fixable_rows`), which land HERE rather than beside the census readers because `docs/lint-vault-live-baseline.md` is this item's own evidence and nothing else in the tree reads it; they use no `ast`, so constraint 2 does not reach them. Created, so no symbol anchor.
```

```writes
path: tests/test_fixture_vault.py
why: Tasks 8 and 14 — the skip-reason wall's universe widened at BOTH call sites (`:508-509` and `:1302`) with both declared-homes expected sets held at two members and a non-vacuity clause added at each, plus the fifth census reader `census_auto_fixable_rows` beside the four existing `census-*` fence parsers. One site without the other is a half-extended wall that reads green (constraint 8). LANDED as specced at `:166`, between `census_meta` and `census_identity_residue`; its signature is `(text=None, *, categories)` and not Design §9's `(text=None)` — the category vocabulary is injected by `tests/test_lint_vault_fix_rules.py`, which holds the loaded script module, because this module has no `lint_vault` loader and may not mint a second one (Build Log D5).
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

## Mitigation Folds — 2026-09-15

This section is restated IN PLACE, against the LATEST SPEAKING round — which since 2026-09-16 is
`## Threat Model — 2026-09-16 (round 5)`, not round 4 and not any earlier one: round 5 emits EIGHT
`kind: required` fences, so it is the round `parse_mitigations` selects and the round every `desc`
below is copied from. Round 5 re-emitted all EIGHT of round 4's `desc` values BYTE-IDENTICALLY —
including M8's, whose rationale clause round 5 itself falsified and deliberately did not re-word
under its FIDELITY note, because `desc` is the only machine-anchored field and the REQUIREMENT did
not move — so every record below is carried forward verbatim rather than re-copied, and the
2026-09-16 truthfulness correction lands in this section's PROSE and in `## Design`, never in a
`desc`. SIX of the eight had already re-emitted their prior `desc` byte-identically at round 4 (M1,
M2, M3, M4, M5, M6 — round 4 states this of each and the spec-reviewer independently diffed the first
four), and the substance behind each was
re-verified on its own surface. TWO were NEW at round 4: **M7** (the callee set is the script's
COMPLETE set of mutating entry points and that is FOUR, `quarantine_garbage` being the missing
member) and **M8** (the module may not NAME the live vault path at all outside `_temp_vault`), each
opened by round 4 after the fifth pass's last turn, each with its `desc` copied verbatim from that
round's fence and its substance folded in the SAME edit as the record.

Each of the eight is folded into `## Design` AND the Implementation-Plan task its fence names, in the
same edit as this record. Two were already carried by the Design's substance and needed a sentence
stating the RULE rather than the decision (M1 in §1, M2 in §3), so each got one and the fold quotes
it; two were on zero surfaces when they first landed and are new material (M3 in §7 plus §6(d) plus
Task 9, M4 in §4 plus the Edge Cases plus Task 4); two landed one round ago on the surfaces their
own generator names (M5 in §6(d)'s callee set plus §7's syntax half plus Task 7, M6 in §7's
import half plus Task 15); and the two new ones land the same way — M7 in §6(d)'s callee set plus
§7's syntax half plus Task 7 plus the `drives` fixture battery, M8 in §6(d)'s new `live_path_names`
census plus §7's new SOURCE half plus Task 9's clause (iv) — each riding machinery the plan already
ships, so no derivation and no
check is added and the four counts this document has re-synced once do not move again.

**What the class-shaped sweep found, declared rather than left implicit (WI-226).** The two unlanded
mitigations share a generator — *a rule this document states as INTENT somewhere and binds nowhere*
— so the fold for each closes the class rather than the instance, and then the next level of the
ladder was swept and the result is stated here so the next round does not rediscover it. For M3 the
class is "a mutating drive reaching a path this module did not create", and the instance-shaped fold
would have been one `assert` inside one check; the class-shaped fold is ONE door plus a SYNTAX wall
over the module's own source, so every drive Tasks 10–15 add and every drive anyone adds later is
covered by construction rather than by the author remembering. That totality claim is the one round 2
and round 3 each falsified one level at a time, and it is now BOUNDED where it is made rather than
left absolute: it holds over OMISSION shapes at all three levels the ladder below reaches — the
argument, the binding, and the entry point / process boundary (M5, M6) — and it does NOT hold over
deliberate acts of disguise, which `## Scope Boundary` records as the mechanism's honest bound.

**M3's ladder, re-swept on 2026-09-15 after round 2 found the level BELOW the one the first sweep
declared closed — and the correction is recorded rather than the first result quietly replaced.**
The first sweep asked "what else in this module can reach a path it did not create" and answered at
the ARGUMENT level: `lint_vault.DEFAULT_VAULT`, `os.environ["OBSIDIAN_VAULT_PATH"]`, a literal path
and any other bound name, each RAISING or RED at the call site. Every one of those answers is still
true, and the level was still not closed, because the generator sits one level down: the wall reads
the argument EXPRESSION at the call, so the hazard simply moves out of the call and into the
BINDING — `vault = lint_vault.DEFAULT_VAULT` followed by `run_lint(vault, do_fix=True)` presents the
accepted identifier at every site the sweep looked at. The re-sweep therefore enumerates the level
that actually generates the class, which is *where the accepted identifier can come from*, and
`ast` closes that enumeration for us rather than leaving it to memory: a name in this module is
bound by an `Assign`, an `AnnAssign`, an `AugAssign`, a `for` target, a `with ... as`, a walrus, an
`except ... as`, a parameter, an import alias, a `def`/`class` of that name, a `global`/`nonlocal`
declaration — or by nothing at all, which is its own case. §6(d)'s `bindings` census reads the
provenance of the ONE shape that carries a readable one (a single-target `Assign`, whose provenance
is the callee name or the sentinel `NOT_A_CALL`) and RAISES on every other member and on the
no-binding case, so the level is closed by `ast`'s own closure and not by a list anybody wrote down.
Sweeping the level BELOW that one — the intersections, i.e. a binding whose provenance is a call to
something that merely LOOKS like the door — closes ONE side of that level and not both, and the
earlier draft of this sentence overclaimed it, so it is corrected here rather than carried: the
provenance compared is the callee's OWN NAME against `"_temp_vault"`, so a DIFFERENTLY-NAMED wrapper
is RED naming its line (`vault = make_vault(tmp)` yields provenance `"make_vault"`) while anything
spelled with the door's own name is GREEN — `helpers._temp_vault(tmp)` resolves to
`ast.Attribute.attr` and yields `"_temp_vault"`, and so do a `from x import make as _temp_vault` and a
second `def _temp_vault` later in the module, each of which would pass while the real door never runs.
That residue is DELIBERATE and is recorded as the mechanism's honest bound in `## Scope Boundary`
rather than chased: every one of those three shapes is a deliberate act of disguise, not the drift or
the convenient shortcut this wall exists to catch, and the runtime half still holds the door that IS
called. Nothing in this
re-sweep is deferred, and the superseded first answer is left above rather than deleted because the
shape of the miss — a sweep that closes the level it was looking at and not the level generating it
— is the reusable finding.

**M3's ladder, swept UPWARD this round after round 3 found the level ABOVE the one the re-sweep
closed — and the whole of that level is closed in one fold rather than its first member (WI-226).**
*(Heading qualified 2026-09-16: "the whole of that level" was true of the level's IN-PROCESS and
OUT-OF-PROCESS members and false of a third the sweep did not find — see the correction at the end of
this paragraph.)*
The two levels above are declared here so the next round does not rediscover them one at a time. The
generator is no longer *where the accepted identifier comes from* but *how the tool can be reached
without presenting an identifier for any census to grade*, and enumerating THAT question rather than
its first answer yields exactly two routes, because there are exactly two ways to call code:
IN-PROCESS, where the callee is a name in this module's own `ast`, and OUT-OF-PROCESS, where it is a
string in an argv list. In-process, the census graded two of the script's mutating entry points
— `main:1252` was outside the callee set and reaches the live vault by OMITTING `--vault`
(`default=DEFAULT_VAULT`, `:1255`), so it presented nothing to `drives`, nothing to `bindings` (scoped
BY `drives`) and never called `_temp_vault`. M5 puts `main` inside the set, where §6(d)'s existing
"a vault argument at NEITHER position RAISES" rule grades it with no new text. Out-of-process
is closed at the IMPORT rather than at the call, because the call is unreadable by construction — no
`ast` census can see a path that is a string in a list — so M6 refuses the CAPABILITY: `subprocess`
and `runpy` join the module set Task 15 hands `module_import_uses` over this file. The `os`-attribute
form of the same escape needed nothing: `os_module_attribute_uses:800-844` returns every `os.<attr>`
access and `OS_READONLY_NAMES:69` holds only `environ`/`getenv`/`sep`/`path`/`fspath`/`getcwd`, so
`os.system` / `os.popen` / `os.execv` in this module is ALREADY RED under the wall Task 15 runs — that
is a member of this level the sweep found already closed, and it is named rather than silently
counted.

**AND THE CLAIM THIS PARAGRAPH MADE NEXT WAS FALSE, which is corrected in place rather than quietly
replaced, because the shape of the miss is the reusable finding for the third time running.** It said
that "M5 closes the whole in-process level, not `main` alone: the callee set is now the script's
complete set of mutating entry points", and that the level above was "empty of omission shapes" with
"all three entry points and both process boundaries closed". That is a completeness claim about a
finite, checkable set, and threat-model round 4 checked it rather than reading it. It was false by
one member and false in kind:

- **False by one member.** The script's mutating entry points are FOUR, not three. Settled by the
  MUTATION-SITE census rather than by a list of names: the only `vault_io` mutation sites in the
  whole script are `write_note` at `:957` and `:975` inside `apply_fixes` and `ensure_dir` at `:1134`
  plus `move_note` at `:1140` inside `quarantine_garbage:1112-1144`, so the functions reaching them
  are `apply_fixes`, `quarantine_garbage`, `run_lint` and `main`. The missing member is the one whose
  write is IRREVERSIBLE, and this item PINS the detectors that decide what it moves — so a drive of
  it is natural rather than exotic. M7 closes it at no cost: its vault argument is the SECOND
  positional at `:1113` exactly as `apply_fixes`' is at `:827`. The lasting correction is not the
  member but the SET'S DEFINITION: §6(d) now states the callee set as "the script's complete set of
  functions reaching a `vault_io` mutating door", which is a derived predicate a fifth such function
  would join, rather than as N names somebody counted.
- **False in kind, and this is the half that matters.** Enumerating entry points cannot close this
  level at all, because the argument these censuses grade does not determine what gets written:
  `apply_fixes`' `vault_path` is referenced NOWHERE in its body (`:827` is its only occurrence) and
  its write targets are `issue.file_path` (`:835`, `:853`, `:957`, `:975`). So a correctly-contained
  vault argument beside an issue list built from `lint_vault.read_vault(lint_vault.DEFAULT_VAULT)`
  passes every clause the three-part guard had, with the runtime door EXECUTED and the import wall
  clean, and rewrites the live vault — and under `quarantine_garbage`, whose `vault_path` is only the
  destination root (`:1116`) while the sources moved are `issue.file_path` (`:1121`), it is data
  LOSS rather than a wrong write. **So this level is closed at the SOURCE and not by a fifth door
  (M8) — and the claim this bullet made next was FALSE, corrected 2026-09-16 rather than quietly
  replaced, which makes it the fourth time the same shape of miss is the reusable finding.** It read:
  *"and that is the only closure here that is total by construction rather than by enumeration: the
  live vault path has exactly TWO sources in this module's universe — `DEFAULT_VAULT`, itself
  `os.environ.get("OBSIDIAN_VAULT_PATH", "")` at `scripts/lint_vault.py:DEFAULT_VAULT:56`, or a
  direct environment read … — so a clause that the module NAMES neither token outside `_temp_vault`'s
  own body is total over every omission route through every door."* The construction closes the
  SPELLINGS, not the SOURCES: the three token shapes are closed by `ast`, and a path the module never
  spells is outside them. Threat-model round 5 found one such source in the tree —
  `obsidian_schemas/repositories/base.py:_resolve_vault_path:104-114` falls back to
  `os.environ.get(ENV_VAULT_PATH)` INSIDE the library (`ENV_VAULT_PATH:75`, `_is_unconfigured:86-101`
  counting `None`/blank/whitespace-only/`Path(".")`, `BaseRepository.__init__:154`, the four
  repositories exported at `obsidian_schemas/__init__.py:74-77`) — so `repo = PersonRepository()`
  beside `read_vault(repo.vault_path)` passes clauses (i)–(iv) with the runtime door executed and the
  import wall clean, and rewrites the live vault wherever `OBSIDIAN_VAULT_PATH` is exported. What M8
  therefore IS: a clause total over every omission route that SPELLS the live path, through the four
  doors the census enumerates and any fifth nobody has thought of. What it is NOT: total over a route
  that obtains the path unspelled. That residue is an OMISSION shape, NOT the deliberate-act residue
  the paragraph above records, so `## Scope Boundary`'s deliberate-act closure does not cover it; and
  because the source half is not total, the door census (M5, M7) and the import wall (M6) are
  LOAD-BEARING here rather than belt-and-braces. Whether to close it is a SUFFICIENCY call routed to
  Dave or the conductor and OPEN as of 2026-09-16 — see `## Scope Boundary`.

Then the level above THAT was swept, with the enumeration-versus-construction distinction in hand
rather than another door list, and here is what it found — declared rather than left for a fifth
round. The generator one level up is *what a drive can reach that this module's own text does not
name*, and it has exactly two members, both already closed and neither by enumeration: the ISSUES a
drive is handed (closed by M8, because an issue list can only come from a scan of a path the module
named) and the PROCESS it runs in (closed by M6 at the import). There is no third, because a call in
this module either names its arguments in this module's `ast` or leaves the process, and both are
graded.

**THAT SWEEP'S RESULT WAS WRONG, and this is the sharpest of the 2026-09-16 corrections because it
is the sentence that most directly told a later reader to stop looking.** *"There is no third,
because a call in this module either names its arguments in this module's `ast` or leaves the
process, and both are graded"* is false: a call in this module can also be handed a value COMPUTED by
a callee that reads the environment itself, and that value is neither named in this module's `ast`
nor outside the process. There IS a third member — a callable the module invokes that resolves the
live vault from `OBSIDIAN_VAULT_PATH` rather than from its argument — and the tree has exactly one
today, `obsidian_schemas/repositories/base.py:_resolve_vault_path:104-114`, reached through any of
the four repository constructors (`BaseRepository.__init__:154`;
`obsidian_schemas/__init__.py:74-77`). The level's correct enumeration is therefore THREE members:
the issues (M8, for the spellings), the process (M6), and the unspelled resolve — the third CLOSED by
nothing today. That census was run on 2026-09-16 by grepping
`OBSIDIAN_VAULT_PATH|ENV_VAULT_PATH|os\.environ|os\.getenv` across `obsidian_schemas/**`,
`scripts/**` and `tests/**` and reading every hit (the near members, named so they are not
re-derived: `obsidian_schemas/vault_io.py:_env_setting:103-116` resolves lock and write-guard
settings and never a vault path; `tests/fixture_vault.py:materialize_vault:626` and
`tests/identity_fixture.py:seed_vault:85-100` both REQUIRE a destination), and it is an ENUMERATION
measured at a date and never a total — a callable added later that resolves a vault from the
environment joins this member silently. Closing it is a SUFFICIENCY call routed to Dave or the
conductor (`## Scope Boundary`), OPEN as of 2026-09-16, and it is deliberately NOT folded here as a
ninth mitigation.

What remains after that is NOT an omission shape at all — it is the deliberate-disguise
residue named in the paragraph above, a decoy spelled with the door's own name, and now one sibling
of it that M8 inherits rather than removes: an author who writes the escape INSIDE `_temp_vault`'s
own body, which the by-function exemption permits by construction and which no mechanism short of
re-implementing Python's name resolution would catch. That residue is a SCOPE BOUNDARY rather than a
gap, and `## Scope Boundary` states it in the ruling shape with its bound corrected to what the
mechanism will actually be once M7 and M8 land.

For M4 the class is "an issue credited at a frame boundary rather than at its own
write", and the instance-shaped fold would have been a special case for AC-4(b)'s two-issue file;
the class-shaped fold is the credit-at-the-commit-point rule, total over both writes and therefore
over every issue on every file. Sweeping ITS next level — the other places an issue's bucket could
be decided at the wrong moment — returned `file_fixed` at `:882` and the `fixed += 1` at `:972`,
both of which credit before a write exists and both of which are DELETED by the same fold rather
than left as the spec-review round's coin-flip. Nothing in either sweep is deferred.

```fold
id: M1
desc: read_vault's recorded read_error value is the IMPORTED SKIP_REASONS member UNREADABLE and never str(exc) of the decode failure, so undecodable note bytes are never decoded, never rendered into an issue message and never stored in any record.
design: `read_vault`'s recorded `read_error` value is the IMPORTED `SKIP_REASONS` member `UNREADABLE` and never `str(exc)` of the decode failure, so undecodable note bytes are never decoded, never rendered into an issue message and never stored in any record.
landed: Task 2
work: Edit `scripts/lint_vault.py`: add `read_error: Optional[str] = None` as the LAST field of `VaultFile:88-97`; add `from obsidian_schemas.repositories.base import UNREADABLE` beside the existing package imports at `:38-50`; replace the `except Exception: continue` at `:115-118` with the recording form in Design §1, field for field. The string `"unreadable"` must NOT appear anywhere in the file. **Verify:** `read_vault` over a directory containing one non-UTF-8 `.md` returns a `VaultFile` for it whose `read_error` is in `SKIP_REASONS`, and `build_indexes(...)["all_stems"]` contains that note's stem. verify: test_an_unreadable_note_is_reported_indexed_and_never_silently_dropped
```

```fold
id: M2
desc: FixErrorRecord.reason is the exception's class name and FixDeclineRecord.guard is a DECLINE_GUARDS member — never str(exc), never note bytes — because both records feed the operator-facing summary that gets pasted into chat.
design: `FixErrorRecord.reason` is the exception's class name and `FixDeclineRecord.guard` is a `DECLINE_GUARDS` member — never `str(exc)`, never note bytes — because both records feed the operator-facing summary that gets pasted into chat, which is the same reason `NameGateRefusalRecord`'s own docstring gives for closing its field set at two.
landed: Task 4
work: Edit `scripts/lint_vault.py`: replace `FixOutcome:820-825` with the four-field form; add `FixErrorRecord`, `FixDeclineRecord` and the five `GUARD_*` constants plus `DECLINE_GUARDS` beside `NameGateRefusalRecord:805-818`, with `FixErrorRecord.reason` carrying `type(exc).__name__` and `FixDeclineRecord.guard` carrying a `DECLINE_GUARDS` member — never `str(exc)`, never note bytes, because both records feed the operator-facing summary (Design §3). Implement the §4 disposition rule inside `apply_fixes`: `undecided`, `staged_first` and `staged_wikilink` per file; a decline recorded at each of the five branches, removing the issue from `undecided` there; DELETE the `file_fixed` counter at `:882`, DELETE the `fixed += file_fixed` fold at `:949` outright rather than moving it, and DELETE the `fixed += 1` at `:972`; credit `repaired += len(staged_first)` on the statement after the `write_note` at `:957` RETURNS and `repaired += len(staged_wikilink)` on the statement after the `write_note` at `:975` RETURNS, each removing its list's members from `undecided`; one record per still-undecided issue in each handler and exactly ONE print per file. `NameGateRefusalRecord`'s field set does not move. **Verify:** the standing WI-021 battery still passes with only the field rename applied to it (Task 5); the four-bucket equality holds over a planted vault; and on ONE planted file carrying a `missing_body_sections` issue whose `:957` write commits beside a `broken_wikilink` issue whose `:975` write raises, the first comes back `repaired` and only the second `errored` — a build that folds once at the end of the lock block returns BOTH as `errored` and is red on that plant. verify: test_lint_vault_fix_guards_threads_and_records_refusals test_the_fix_outcome_surfaces_both_counts test_every_auto_fixable_issue_is_accounted_for_and_the_printed_summary_says_so
```

```fold
id: M3
desc: every apply_fixes and run_lint(..., do_fix=True) drive in tests/test_lint_vault_fix_rules.py takes a vault path rooted in a fresh tests/support.temp_dir(), never lint_vault.DEFAULT_VAULT, never OBSIDIAN_VAULT_PATH and never any path outside that directory, and the module asserts that containment before the first mutating call; and the syntax half asserts PROVENANCE and not merely spelling — every binding in that module of the identifier it accepts is a call to the single _temp_vault door — so a drive cannot satisfy the wall by re-binding that name to a path the door never produced.
design: Every mutating drive's vault path is CONFINED to a fresh temp directory, the module asserts that containment before the first mutating call, and the syntax half asserts PROVENANCE and not merely spelling — every binding in that module of the identifier it accepts is a call to the single `_temp_vault` door, so a drive cannot satisfy the wall by re-binding that name to a path the door never produced (M3).
landed: Task 9
work: Create `tests/test_lint_vault_fix_rules.py` with the `ensure_project_interpreter(__file__)` first statement, the `SCRIPTS_ROOT`-derived loader reusing `tests/test_lint_vault_fix_gate.py:_load_lint_vault:37-48`'s shape, and a `_plant(vault, stem, body)` that REFUSES a stem already in the corpus (raising with the stem named) so constraint 7 cannot be tripped silently. Ship the containment guard IN THIS TASK, because the skeleton is where every later check inherits it — THREE of Design §7's FOUR parts land here: the runtime half and the syntax half (M3), and the SOURCE half (M8) as clause (iv) inside the syntax half's ONE check, never as a check of its own; §7's remaining part, the import half (M6), is asserted by Task 15 and constrains this module's imports rather than adding code here. (i) The RUNTIME half: `_temp_vault(tmp)` is the module's ONLY constructor of a vault path — it calls `materialize_vault(tmp)` and, before returning, asserts the resolved vault is a strict descendant of the resolved `tmp` (`Path(vault).resolve().relative_to(Path(tmp).resolve())`, which raises `ValueError` when it is not), that `tmp` is a directory this process took from `tests.support.temp_dir()`, and that the resolved vault equals neither `Path(lint_vault.DEFAULT_VAULT).resolve()` nor `Path(os.environ.get("OBSIDIAN_VAULT_PATH", "")).resolve()`, each compared only when that value is non-empty — `.get(..., "")` and NEVER a subscript, which raises `KeyError` in the graded and CI environments where the variable is unset and reddens the door rather than a drive; every comparison is between resolved paths the check itself holds and never a path prefix, a `cage-wt-` substring or a `/tmp` layout (WI-149). (ii) The SYNTAX half: add `test_every_mutating_drive_in_this_module_is_confined_to_a_temp_vault`, which runs Task 7's `mutating_drive_vault_args` over `[Path(__file__)]` and asserts, over the ONE `VaultArgScan` it returns and inside this ONE check (never as a ninth check, which would move three counts this document has already re-synced once), all FOUR clauses of Design §7: every triple in `scan.drives` carries the identifier `vault`; `scan.drives` is NON-EMPTY, so a module that stopped driving the tool cannot pass by vacuity; every 4-tuple in `scan.bindings` carries the provenance `"_temp_vault"`, so every binding of that identifier in this module came out of the one door and a drive cannot satisfy the wall by re-binding the accepted name; and every 4-tuple in `scan.live_path_names` carries `enclosing == "_temp_vault"`, with `scan.live_path_names` NON-EMPTY (M8) — i.e. this module NAMES the live vault path nowhere outside `_temp_vault`'s own body. The third clause is M3's tightening and is not optional: without it `vault = lint_vault.DEFAULT_VAULT` followed by `run_lint(vault, do_fix=True)` passes clauses one and two while the runtime door never executes. The FOURTH clause is M8's and is not optional for a different reason: the first three grade the vault ARGUMENT, and `apply_fixes` ignores its `vault_path` entirely (`:827` is that parameter's only occurrence in the function; the write targets are `issue.file_path` at `:835`, `:853`, `:957`, `:975`), so a check binding `vault = _temp_vault(tmp)` and then handing `apply_fixes` an issue list built from `lint_vault.read_vault(lint_vault.DEFAULT_VAULT)` passes clauses one through three with the runtime door EXECUTED and the import wall clean, and rewrites Dave's live vault — and under `quarantine_garbage`, whose `vault_path` is only the destination root at `:1116` while the sources moved are `issue.file_path` at `:1121`, the same shape is data LOSS. THE EXEMPTION'S MECHANISM IS RULED HERE AND THE BUILDER MUST NOT PICK ONE: the scope is the INNERMOST enclosing `FunctionDef` / `AsyncFunctionDef` name, never a line range (which rots on the first edit) and never an allowed-occurrence count (which is greenable by moving the escape INTO `_temp_vault`), and it is the idiom Design §6(d)(b)'s branch census already uses; the exemption is MANDATORY rather than incidental, because this task's own runtime half ORDERS `_temp_vault` to compare against `Path(lint_vault.DEFAULT_VAULT).resolve()` and `Path(os.environ.get("OBSIDIAN_VAULT_PATH", "")).resolve()`, so a flat token clause would be RED against the module this task prescribes, and the NON-EMPTY arm is what turns those three negative assertions into the wall's own WI-235 proof that the matcher resolves anything at all; M8 and M6 are ONE rule about `_temp_vault` at two levels and must be implemented as one, since M6 leaves `os` legal BY NAME at the import (`WALL_C_MODULES` is `FS_MODULES - {"os"}`) precisely so this door may read `os.environ` while M8 scopes that read to this door's body; and M8 must NOT be implemented by widening the graded IDENTIFIER set, because adding `read_vault` to the `drives` callee set pulls `tmp` into `bindings` and `tmp` is bound by `with temp_dir() as tmp`, which `bindings`' closed RAISE set fires on (threat-model round 4, note 1). Every `apply_fixes(...)`, `quarantine_garbage(...)` and `run_lint(..., do_fix=True)` this module adds in Tasks 10-15 takes its vault argument from that local, and that local is bound by `_temp_vault(...)` and by nothing else; and every issue list any of them is handed is built from a scan of THAT vault, which is what clause (iv) enforces by leaving the module no way to name any other one. The module must not name `ast`, must not hand-type any `SKIP_REASONS` member, and must import NO subprocess-capable module — neither `subprocess` nor `runpy`, in either statement form and under any alias, which is asserted by Task 15 (M6); its legitimate imports are `importlib.util`, `contextlib`, `io`, `pathlib`, `os` and the in-tree `tests.*` helpers, all outside the widened set. DEFINE `test_every_mutating_drive_in_this_module_is_confined_to_a_temp_vault` FIRST among this module's checks: pytest runs a module's checks in definition order, so the detector then fires ahead of every driving check in an ordinary floor run; it is an ordering COURTESY and not a guarantee — `-k` selection and direct invocation bypass it, and the guarantee is the runtime door plus M5/M6/M7/M8 closing the routes that avoid the door — but it costs nothing at authoring time and cannot be retrofitted cheaply. **Verify:** the module imports under the floor; its plant helper raises on `@Dave  Marrowyn Fennwick`; the containment check is green and goes RED when one drive is hand-edited to pass `lint_vault.DEFAULT_VAULT` (observed and reverted), RED again when a check is hand-edited to re-bind `vault = lint_vault.DEFAULT_VAULT` before an otherwise correctly-spelled drive — the provenance clause naming that binding's line (observed and reverted) — RED again when `_temp_vault` is hand-edited to return a path outside `tmp` (observed and reverted), and RED again when a check is hand-edited to build its issue list from `lint_vault.read_vault(lint_vault.DEFAULT_VAULT)` while still passing the correctly-bound `vault` to `apply_fixes` — clause (iv) naming that reference's line with `enclosing` naming the check, and clauses (i)-(iii) all staying GREEN on it, which is what proves the source half is load-bearing rather than a restatement of the argument half (observed and reverted). verify: test_every_mutating_drive_in_this_module_is_confined_to_a_temp_vault test_wall_membership_is_closed_for_every_file_this_item_touches
```

```fold
id: M4
desc: an issue whose own write has COMMITTED is credited at that commit point and is never re-labelled errored by a later raise inside the same lock block, so the issues carried by the write at :957 stay repaired when the wikilink write at :975 raises, as AC-4(b) requires.
design: In its place there are TWO credit points, each on the statement immediately AFTER the `write_note` call whose bytes carry the issues it credits, both still inside the same `with vault_io.note_lock(fpath):` block: after `vault_io.write_note(fpath, content, precondition=_stamp)` RETURNS at `:957`, `repaired += len(staged_first)` and every member of `staged_first` is removed from `undecided`; after `vault_io.write_note(fpath, content, precondition=_stamp)` RETURNS at `:975`, `repaired += len(staged_wikilink)` and every member of `staged_wikilink` is removed from `undecided`.
landed: Task 4
work: Edit `scripts/lint_vault.py`: replace `FixOutcome:820-825` with the four-field form; add `FixErrorRecord`, `FixDeclineRecord` and the five `GUARD_*` constants plus `DECLINE_GUARDS` beside `NameGateRefusalRecord:805-818`, with `FixErrorRecord.reason` carrying `type(exc).__name__` and `FixDeclineRecord.guard` carrying a `DECLINE_GUARDS` member — never `str(exc)`, never note bytes, because both records feed the operator-facing summary (Design §3). Implement the §4 disposition rule inside `apply_fixes`: `undecided`, `staged_first` and `staged_wikilink` per file; a decline recorded at each of the five branches, removing the issue from `undecided` there; DELETE the `file_fixed` counter at `:882`, DELETE the `fixed += file_fixed` fold at `:949` outright rather than moving it, and DELETE the `fixed += 1` at `:972`; credit `repaired += len(staged_first)` on the statement after the `write_note` at `:957` RETURNS and `repaired += len(staged_wikilink)` on the statement after the `write_note` at `:975` RETURNS, each removing its list's members from `undecided`; one record per still-undecided issue in each handler and exactly ONE print per file. `NameGateRefusalRecord`'s field set does not move. **Verify:** the standing WI-021 battery still passes with only the field rename applied to it (Task 5); the four-bucket equality holds over a planted vault; and on ONE planted file carrying a `missing_body_sections` issue whose `:957` write commits beside a `broken_wikilink` issue whose `:975` write raises, the first comes back `repaired` and only the second `errored` — a build that folds once at the end of the lock block returns BOTH as `errored` and is red on that plant. verify: test_lint_vault_fix_guards_threads_and_records_refusals test_the_fix_outcome_surfaces_both_counts test_every_auto_fixable_issue_is_accounted_for_and_the_printed_summary_says_so
```

```fold
id: M5
desc: mutating_drive_vault_args' callee set includes main as well as apply_fixes and run_lint, so the tool's CLI entry point — whose --vault carries default=DEFAULT_VAULT at scripts/lint_vault.py:1255 and which therefore reaches the live vault by OMISSION rather than by an attribute access — is inside the wall rather than beside it; a main call in that module carries a vault argument at no position and so RAISES under the rule §6(d) already states, reddening the wall at its own line.
design: `main` is a member of the `drives` callee set and needs no new rule to grade, because it has NO vault-argument position at all — `scripts/lint_vault.py:main:1252` takes no parameters — so EVERY collected `main` call, with or without arguments, falls into the arm above that already RAISES on a call passing a vault argument at neither position, naming module and line.
landed: Task 7
work: Add `auto_fixable_emitter_checks`, `auto_fixable_branch_checks`, `person_tier_arm_counts` and `mutating_drive_vault_args` to `tests/derivations.py` per Design §6, each raising on a node it cannot resolve to a literal (or, for the fourth, to a bound `ast.Name`) rather than skipping it, each documented with the near-miss it must NOT match; the fourth returns the `VaultArgScan` TRIPLE — the `drives` call census, the `bindings` provenance census AND the `live_path_names` source census — and the `drives` callee set is FOUR members and not two or three, `apply_fixes`, `quarantine_garbage`, `run_lint` and `main`, the script's COMPLETE set of functions reaching a `vault_io` mutating door, because `main` is the entry point that reaches the live vault by OMISSION rather than by an expression a scan can see (`--vault` carries `default=DEFAULT_VAULT` at `scripts/lint_vault.py:1255` and it calls `run_lint(vault_path, …, do_fix=args.fix, …)` at `:1299-1308`), and it needs NO new rule: `main` has no vault-argument position at all, so every collected `main` call falls into the arm that already RAISES on a call passing a vault argument at neither position (M5). Nothing else in the module changes. **Verify:** over `[SCRIPTS_ROOT / "lint_vault.py"]` the two rule scans each return a five-member set and the two sets are equal; `person_tier_arm_counts` returns `(6, 4)`; and `mutating_drive_vault_args` over a planted module returns `vault` in `drives` for the correct drive shapes and RAISES on `run_lint(lint_vault.DEFAULT_VAULT)`, while a planted `lint_vault.main()` and a planted bare `main()` each RAISE naming their own line (M5's shapes — the callee set reaches them and `main` has no vault-argument position) and a planted call to some other zero-argument callee such as `setup()` is NOT collected at all, which is what proves the widening reaches `main` rather than every argument-free call. verify: test_every_auto_fixable_rule_repairs_to_its_declared_oracle test_every_write_causing_detector_fires_exactly_on_its_declared_subjects test_every_mutating_drive_in_this_module_is_confined_to_a_temp_vault
```

```fold
id: M6
desc: tests/test_lint_vault_fix_rules.py imports no subprocess-capable module — subprocess and runpy are added to the module set Task 15 hands module_import_uses over that file, because WALL_C_MODULES is FS_MODULES minus os and contains neither — so the wall cannot be satisfied by a drive that re-enters the tool through its CLI as a child process, which is the shape tests/test_vault_path_required.py:344-353 already uses and has to scrub OBSIDIAN_VAULT_PATH out of the environment to make safe.
design: So the route is refused at the IMPORT rather than at the call: `tests/test_lint_vault_fix_rules.py` names no subprocess-capable module, asserted by Task 15 handing `module_import_uses` the set `WALL_C_MODULES | {"subprocess", "runpy"}` over this file — `tests/derivations.py:FS_MODULES:68` is `{"os", "shutil", "tempfile", "fcntl", "filelock", "mmap"}` and `tests/test_name_gate_wall.py:WALL_C_MODULES:1043` is that minus `os`, so the standing set reaches NEITHER and the widening is the whole of M6.
landed: Task 15
work: Add `ROOT / "docs" / "lint-vault-fix-safety.md"` to `WORK_ITEM_DOCS` in `tests/test_ac_interpreter.py:47-50`, then add `test_wall_membership_is_closed_for_every_file_this_item_touches` to the new module and RUN each standing wall's own shipped predicate on this item's touched files' final text — `filesystem_mutation_uses` / `os_module_attribute_uses` / `module_import_uses` over the script AND over the new check module, where **`module_import_uses` over the new check module takes the WIDENED module set `WALL_C_MODULES | {"subprocess", "runpy"}` and asserts it returns NOTHING (M6)**, because the standing set reaches neither (`FS_MODULES:68` is `{"os","shutil","tempfile","fcntl","filelock","mmap"}` and `WALL_C_MODULES:1043` is `frozenset(FS_MODULES - {"os"})`) and without the widening the module could re-enter the CLI as a child process and satisfy every in-process clause of Design §7 while mutating the live vault; IMPORT the base set (`from tests.test_name_gate_wall import WALL_C_MODULES`) and never hand-type its members, since a written-out copy stops tracking `FS_MODULES` the day it gains one and four check modules already import from that module; no derivation changes, since `module_import_uses:847-870` already takes an arbitrary `modules` iterable and reports the ORIGINAL module name in both statement forms, and over `scripts/lint_vault.py` the set stays the STANDING `WALL_C_MODULES` (the script imports neither module today, `:20-31` / `:36-50`, so the asymmetry costs nothing and exists only so this task does not silently re-scope a standing wall); plus `frontmatter_write_arms`, `character_class_strip_sites`, `address_splitting_implementations`, `modules_using_ast`, `skip_reason_literal_sites` over the WIDENED universe, `FORBIDDEN_DEFAULT_PATTERNS` and `criterion_checks`, with anything the RUN returns that the spec did not name recorded in the Build Log and satisfied. The widened set's REACH is proved in this SAME check rather than assumed from a zero (WI-235): planted `import subprocess`, `import subprocess as sp`, `from subprocess import run`, `import runpy` and `from runpy import run_path` must all be FOUND under the original module name, and planted `import importlib.util`, `from contextlib import redirect_stdout`, `import io`, `from tests.support import temp_dir` and the STRING `"subprocess"` in a docstring must NOT be. **Verify:** green, and the item's five criteria each exit 0 under the `-S` foreign interpreter having actually delegated; the widened set is proved reaching by the five planted import shapes and proved non-total by the five planted near-misses; and adding `import subprocess` to the new check module by hand turns the check RED naming that line (observed and reverted). verify: test_wall_membership_is_closed_for_every_file_this_item_touches test_every_acceptance_criterion_passes_under_the_conveyors_interpreter
```

```fold
id: M7
desc: mutating_drive_vault_args' callee set is the script's COMPLETE set of mutating entry points and therefore has FOUR members and not three — quarantine_garbage joins apply_fixes, run_lint and main, because it is the only other function in scripts/lint_vault.py that reaches vault_io's mutating doors (ensure_dir at :1134, move_note at :1140, the script's only mutation sites beside apply_fixes' writes at :957 and :975) and its move is the irreversible one; its vault argument is the SECOND positional at :1113 exactly as apply_fixes' is at :827, so it grades under the position rule §6(d) already states with no new text.
design: The `drives` callee set is the script's COMPLETE set of functions that reach a `vault_io` mutating door, and that set is FOUR — `apply_fixes`, `quarantine_garbage`, `run_lint` and `main` — because the script's only mutation sites are `write_note` at `:957` and `:975` inside `apply_fixes` and `ensure_dir` at `:1134` plus `move_note` at `:1140` inside `quarantine_garbage:1112-1144`, and `quarantine_garbage`'s vault argument is the SECOND positional at `:1113` exactly as `apply_fixes`' is at `:827`, so §6(d)'s existing position rule grades it with no new text.
landed: Task 7
work: Add `auto_fixable_emitter_checks`, `auto_fixable_branch_checks`, `person_tier_arm_counts` and `mutating_drive_vault_args` to `tests/derivations.py` per Design §6, each raising on a node it cannot resolve to a literal (or, for the fourth, to a bound `ast.Name`) rather than skipping it, each documented with the near-miss it must NOT match; the fourth returns the `VaultArgScan` TRIPLE of Design §6(d) — the `drives` call census, the `bindings` provenance census AND the `live_path_names` source census — and the `drives` callee set is FOUR members and not two or three, `apply_fixes`, `quarantine_garbage`, `run_lint` and `main`, and it is the script's COMPLETE set of functions reaching a `vault_io` mutating door rather than a hand list, settled by the mutation-site census: the script's only mutation sites are `write_note` at `scripts/lint_vault.py:957` and `:975` inside `apply_fixes` and `ensure_dir` at `:1134` plus `move_note` at `:1140` inside `quarantine_garbage:1112-1144`. `main` is the entry point that reaches the live vault by OMISSION and needs no new rule, having no vault-argument position at all (M5); `quarantine_garbage` is the member whose write is IRREVERSIBLE — a rename — and this item PINS the two `garbage_candidate_*` detectors that decide what it moves, so a drive of it is a natural way to discharge AC-2's leg (b), and it too needs NO new rule, because its vault argument is the SECOND positional at `:1113` exactly as `apply_fixes`' is at `:827` and §6(d)'s existing position table grades it as-is (M7). Nothing else in the module changes. **Verify:** over `[SCRIPTS_ROOT / "lint_vault.py"]` the two rule scans each return a five-member set and the two sets are equal; `person_tier_arm_counts` returns `(6, 4)` for that module; and `mutating_drive_vault_args` over a planted module returns `vault` in `drives` for the correct drive shapes and RAISES on `run_lint(lint_vault.DEFAULT_VAULT)`, a planted `lint_vault.main()` and a planted bare `main()` each RAISE naming their own line while a planted `setup()` is NOT collected at all (M5's shapes), and a planted `lint_vault.quarantine_garbage(issues, vault)` and a planted bare `quarantine_garbage(issues, vault)` each return `vault` in `drives` (second positional, the same arm `apply_fixes` grades under) while a planted `lint_vault.quarantine_garbage(issues, lint_vault.DEFAULT_VAULT)` RAISES naming its own line — M7's shapes, all three of which are collected by NOTHING under a three-member callee set. verify: test_every_auto_fixable_rule_repairs_to_its_declared_oracle test_every_write_causing_detector_fires_exactly_on_its_declared_subjects test_every_mutating_drive_in_this_module_is_confined_to_a_temp_vault
```

```fold
id: M8
desc: the new check module NAMES the live vault path nowhere outside _temp_vault's own negative assertions — no lint_vault.DEFAULT_VAULT attribute access and no OBSIDIAN_VAULT_PATH or os.environ read anywhere else in the module — because grading a drive's vault ARGUMENT cannot contain apply_fixes, whose vault_path parameter is referenced nowhere in its body (:827 is its only occurrence) and whose write targets are issue.file_path (:835, :853, :957, :975), so a drive whose ISSUES came from lint_vault.read_vault(lint_vault.DEFAULT_VAULT) passes all three clauses of Design §7 with the runtime door executed while rewriting the live vault; and a clause over the path's two SOURCES is total over every omission route through every door, which a callee enumeration cannot be.
design: The new check module NAMES the live vault path nowhere outside the body of `_temp_vault` — no `DEFAULT_VAULT` reference, no `OBSIDIAN_VAULT_PATH` string and no `os.environ` / `os.getenv` read anywhere else in the module — so no escape that NAMES the live path can reach it through any door, the four the callee census enumerates or any door it does not; an escape that OBTAINS the path without naming it is outside this clause, which is why the door census (M5, M7) and the import wall (M6) stay load-bearing beside it.
landed: Task 9
work: Create `tests/test_lint_vault_fix_rules.py` with the `ensure_project_interpreter(__file__)` first statement, the `SCRIPTS_ROOT`-derived loader and a `_plant(vault, stem, body)` that REFUSES a corpus stem; ship the containment guard IN THIS TASK, THREE of Design §7's FOUR parts landing here — the runtime half and the syntax half (M3), and the SOURCE half (M8) as clause (iv) inside the syntax half's ONE check, never as a check of its own. (i) The RUNTIME half: `_temp_vault(tmp)` is the module's ONLY constructor of a vault path and asserts containment before returning, comparing resolved paths the check itself holds against `Path(lint_vault.DEFAULT_VAULT).resolve()` and `Path(os.environ.get("OBSIDIAN_VAULT_PATH", "")).resolve()` — `.get(..., "")` and NEVER a subscript. (ii) The SYNTAX half: `test_every_mutating_drive_in_this_module_is_confined_to_a_temp_vault` runs Task 7's `mutating_drive_vault_args` over `[Path(__file__)]` and asserts all FOUR clauses of Design §7 inside this ONE check — every triple in `scan.drives` carries the identifier `vault`; `scan.drives` is NON-EMPTY; every 4-tuple in `scan.bindings` carries the provenance `"_temp_vault"`; and every 4-tuple in `scan.live_path_names` carries `enclosing == "_temp_vault"`, with `scan.live_path_names` NON-EMPTY (M8), i.e. this module NAMES the live vault path nowhere outside `_temp_vault`'s own body. The FOURTH clause is not optional because the first three grade the vault ARGUMENT and `apply_fixes` ignores its `vault_path` entirely (`:827` is that parameter's only occurrence; the write targets are `issue.file_path` at `:835`, `:853`, `:957`, `:975`), so a check binding `vault = _temp_vault(tmp)` and handing `apply_fixes` an issue list built from `lint_vault.read_vault(lint_vault.DEFAULT_VAULT)` passes clauses one through three with the runtime door EXECUTED and the import wall clean and rewrites the live vault — and under `quarantine_garbage`, whose `vault_path` is only the destination root at `:1116` while the sources moved are `issue.file_path` at `:1121`, the same shape is data LOSS. THE EXEMPTION'S MECHANISM IS RULED HERE AND THE BUILDER MUST NOT PICK ONE: the scope is the INNERMOST enclosing `FunctionDef` / `AsyncFunctionDef` name, never a line range (which rots on the first edit) and never an allowed-occurrence count (which is greenable by moving the escape INTO `_temp_vault`), and it is the idiom Design §6(d)(b)'s branch census already uses; the exemption is MANDATORY rather than incidental because this task's own runtime half ORDERS `_temp_vault` to name both tokens, so a flat token clause would be RED against the module this task prescribes, and the NON-EMPTY arm is what turns those negative assertions into the wall's own WI-235 proof that the matcher resolves anything at all; M8 and M6 are ONE rule about `_temp_vault` at two levels and must be implemented as one, since M6 leaves `os` legal BY NAME at the import (`WALL_C_MODULES` is `FS_MODULES - {"os"}`) precisely so this door may read `os.environ` while M8 scopes that read to this door's body; and M8 must NOT be implemented by widening the graded IDENTIFIER set, because adding `read_vault` to the `drives` callee set pulls `tmp` into `bindings` and `tmp` is bound by `with temp_dir() as tmp`, which `bindings`' closed RAISE set fires on (threat-model round 4, note 1). Every `apply_fixes(...)`, `quarantine_garbage(...)` and `run_lint(..., do_fix=True)` this module adds in Tasks 10-15 takes its vault argument from that local, bound by `_temp_vault(...)` and nothing else, and every issue list any of them is handed is built from a scan of THAT vault, which is what clause (iv) enforces by leaving the module no way to name any other one. **Verify:** the module imports under the floor; its plant helper raises on `@Dave  Marrowyn Fennwick`; the containment check is green and goes RED when one drive is hand-edited to pass `lint_vault.DEFAULT_VAULT`, RED again on a re-binding of `vault`, RED again when `_temp_vault` returns a path outside `tmp`, and RED again when a check is hand-edited to build its issue list from `lint_vault.read_vault(lint_vault.DEFAULT_VAULT)` while still passing the correctly-bound `vault` to `apply_fixes` — clause (iv) naming that reference's line with `enclosing` naming the check, and clauses (i)-(iii) all staying GREEN on it, which is what proves the source half is load-bearing rather than a restatement of the argument half (each observed and reverted). verify: test_every_mutating_drive_in_this_module_is_confined_to_a_temp_vault test_wall_membership_is_closed_for_every_file_this_item_touches
```

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

**The counting wall ships its claimed match-shapes as fixtures (WI-235).** Four of this item's
oracles are COUNTS of structural matches over its four new derivations, and M6 adds a FIFTH over a
STANDING one — the widened module set Task 15 hands `module_import_uses`, a zero-import wall whose
zero is satisfied identically by a set that reaches `subprocess` and by one that reaches nothing.
A count says nothing about its matcher's reach:
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
- `mutating_drive_vault_args` (M3's wall, and the one whose green is `every drive's arg == "vault"`
  AND `every binding's provenance == "_temp_vault"` AND `every live-path name's enclosing ==
  "_temp_vault"` — the shape a narrow matcher satisfies most
  cheaply, by collecting nothing). All THREE censuses ship their claimed shapes.
  **`drives`:** a planted module carrying
  `apply_fixes(issues, vault, idx)` (second positional), `run_lint(vault, do_fix=True)` (first
  positional), `lint_vault.run_lint(vault_path=vault)` (attribute callee, keyword arg) and
  `mod.apply_fixes(issues, vault)` must ALL be found and all return `vault` — four shapes, because
  the callee reaches the module by two spellings and the argument by two positions, and a matcher
  that handles only the bare-name positional form is green on a module full of the other three.
  Near-misses that must NOT be found: a call to `run_lint_report(...)`, a call to any other callee
  taking a `vault` argument, and the STRING `"run_lint"` in a docstring or comment. And a planted
  `run_lint(lint_vault.DEFAULT_VAULT)`, a planted `apply_fixes(issues, Path("/tmp/x"), idx)` and a
  planted `run_lint()` with no vault argument at either position must each RAISE rather than be
  skipped — an under-reading scan here is green against precisely the drive it exists to catch.
  **The CALLEE-SET half (M5's shapes), whose claimed reach is the entry point that carries no vault
  argument at all:** a planted `lint_vault.main()` (attribute callee) and a planted bare `main()` must
  each RAISE naming their own line, because `main` is in the callee set and has no vault-argument
  position — those two shapes are the whole of M5 and a two-member callee set is green on a module
  containing them. And the NEAR-MISS that stops the widening from being satisfiable by matching every
  argument-free call: a planted `setup()` and a planted `helpers.main_menu()` must be collected by
  NOTHING and must not RAISE, so the set is proved to reach `main` rather than to reach anything
  shaped like it.
  **The CALLEE-SET half again (M7's shapes), whose claimed reach is the entry point whose write is
  IRREVERSIBLE:** a planted `lint_vault.quarantine_garbage(issues, vault)` (attribute callee, second
  positional) and a planted bare `quarantine_garbage(issues, vault)` must each be FOUND and return
  `vault`, and a planted `lint_vault.quarantine_garbage(issues, lint_vault.DEFAULT_VAULT)` must
  RAISE naming its own line. All three are collected by NOTHING under a three-member callee set, so
  the trio is the whole of M7 and no smaller set distinguishes it — and the third is worth running
  precisely because it is GREEN (as in: silently uncollected) under the set this document carried
  before round 4. The near-miss is the one already stated: a call to any other callee taking a
  `vault` argument stays uncollected, so the widening is proved to reach `quarantine_garbage` rather
  than every two-argument call.
  **`bindings` — the provenance half, whose claimed shapes are the ones the spelling census cannot
  see (M3's tightening, threat-model round 2):** the RED that matters is a planted module carrying
  `vault = lint_vault.DEFAULT_VAULT` followed by `run_lint(vault, do_fix=True)` — a drive whose
  spelling is correct, whose `drives` triple is `(..., "vault")` and which therefore passes the
  spelling clause; the predicate must return a binding whose provenance is `NOT_A_CALL` at the
  ASSIGNMENT's lineno, and the wall must be red on it. Beside it, three more REDs of the same class,
  each a different re-binding route to the same escape: `vault = os.environ["OBSIDIAN_VAULT_PATH"]`
  and `vault = "/Users/x/vault"` (both `NOT_A_CALL`), and `vault = make_vault(tmp)` (provenance
  `"make_vault"`, a call to something that is not the door). And the NEAR-MISS the predicate must
  NOT match, which is what stops the provenance clause from being satisfiable by matching every
  assignment: a planted module whose only drive binds `vault = _temp_vault(tmp)` — provenance
  `"_temp_vault"`, GREEN — *in a module that also binds other names*, `other = lint_vault.DEFAULT_VAULT`
  and `path = os.environ["OBSIDIAN_VAULT_PATH"]` among them, neither of which may appear in
  `bindings` at all, because the census is scoped to the identifiers `drives` names and a scan that
  collected every assignment would redden every honest module. (Every shape in this battery is
  PLANTED TEXT handed to the predicate — a temp file or a string the fixture parses — and never a
  line of the check module's own source, which is why fixtures may legally spell
  `lint_vault.DEFAULT_VAULT` and `os.environ[...]` while clause (iv), which grades only
  `[Path(__file__)]`, stays green. A builder who plants these as literal module-level code rather
  than as fixture text reddens the module's own wall, correctly.) Plus the closed-set RAISES, one per
  binding construct that carries no readable provenance: `def check(vault):` (an `ast.arg`),
  `for vault in vaults:`, `with make(tmp) as vault:`, `vault, other = pair`, `vault += "x"`,
  `import mod as vault`, and a drive naming an identifier the module never binds at all — each must
  RAISE naming module and line rather than be skipped, which is the only reading under which
  "every binding came from the door" is a claim about ALL of them.
  **`live_path_names` — the source half, whose claimed shapes are the ones NEITHER argument census
  can see (M8, threat-model round 4):** the RED that matters is the four-line escape itself — a
  planted module carrying `vault = _temp_vault(tmp)` (provenance `"_temp_vault"`, GREEN) beside
  `issues = lint_vault.check_noise(lint_vault.read_vault(lint_vault.DEFAULT_VAULT), idx)` and
  `lint_vault.apply_fixes(issues, vault)` — every clause of the argument half GREEN, and clause (iv)
  RED at the `lint_vault.DEFAULT_VAULT` reference's own line with `enclosing` naming the enclosing
  check. Beside it, four more claimed shapes that must ALL be found, because the census claims three
  tokens through two spellings each and a matcher reaching only the dotted form is green on a module
  full of the rest: an attribute `lint_vault.DEFAULT_VAULT` and a bare `DEFAULT_VAULT` (after
  `from lint_vault import DEFAULT_VAULT`), both token `"DEFAULT_VAULT"`; a Constant
  `"OBSIDIAN_VAULT_PATH"`; and an attribute `os.environ` plus a bare `getenv`, both token
  `"os.environ"`. The SCOPING shapes, which are what make the exemption checkable rather than a
  tolerance: the same `lint_vault.DEFAULT_VAULT` reference planted inside `def _temp_vault(...)`
  returns `enclosing == "_temp_vault"` (GREEN), planted inside `def test_x(...)` returns `"test_x"`
  (RED), planted at module scope returns `MODULE_LEVEL` (RED), and planted inside a `def` NESTED
  within `_temp_vault` returns that nested def's OWN name (RED) — the last being the shape that
  separates INNERMOST scoping from outermost and the one an occurrence-count reading is green on.
  And the NEAR-MISSES the predicate must NOT match, which stop clause (iv) from being satisfiable by
  matching every name in sight: a local variable named `default_vault`, an attribute
  `lint_vault.DEFAULT_CATEGORIES`, the string `"OBSIDIAN_VAULT_PATH_OLD"`, a longer string that
  merely CONTAINS the token (a prose docstring sentence, or the fixture text
  `'path = os.environ["OBSIDIAN_VAULT_PATH"]'` this very battery plants), and
  `os.path` / `os.sep` (which are `OS_READONLY_NAMES` members but not environment reads) — none of
  which may appear in `live_path_names` at all. The Constant arm is EQUALITY and never containment,
  which is what makes the fixture texts above legal inside this module; the flip side is a build
  constraint worth stating rather than discovering — a BARE `"OBSIDIAN_VAULT_PATH"` Constant outside
  `_temp_vault`, for instance in an environment-scrub helper copied from
  `tests/test_vault_path_required.py:_run_lint_vault:344-353`, IS a match and is RED, which is the
  correct answer, since this module has no business scrubbing an environment it may not read. Finally the NON-VACUITY shape, which is the WI-235
  element proper: a planted module naming NONE of the three tokens anywhere must make the wall RED
  for emptiness rather than green, so a matcher that resolves nothing cannot satisfy a
  zero-outside-the-door clause.
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
- `module_import_uses` under the WIDENED module set `WALL_C_MODULES | {"subprocess", "runpy"}`
  (M6's wall, whose green is a zero and is therefore the cheapest of all of these to satisfy by a set
  that reaches nothing). Driven inside Task 15's own check, over planted text, through the STANDING
  predicate and never a re-implementation. Claimed shapes that must ALL be found, each reported under
  the ORIGINAL module name rather than the local alias (which is the property
  `module_import_uses:847-870`'s docstring states and the reason no derivation changes):
  `import subprocess`, `import subprocess as sp`, `from subprocess import run`, `import runpy`,
  `from runpy import run_path`. Near-misses that must NOT be found, and they are deliberately this
  module's OWN imports so the wall cannot pass by matching every import and then be narrowed back with
  nothing checking the narrowing: `import importlib.util`, `from contextlib import redirect_stdout`,
  `import io`, `from tests.support import temp_dir`, and the STRING `"subprocess"` inside a docstring.
  Two of those are load-bearing rather than decorative — `import importlib.util` is a DOTTED import
  whose root (`importlib`) the predicate must split off correctly, and `os` stays legal by name
  (`WALL_C_MODULES` is `FS_MODULES - {"os"}`) because `_temp_vault` reads `os.environ`, so a builder
  who "tidies" the widened set into `FS_MODULES | {"subprocess", "runpy"}` reddens the door itself.

**Mutate-and-observe, as the complementary half and never as the whole (WI-235).** FOURTEEN mutations,
each observed RED and reverted, each recorded in the Build Log: revert `read_vault`'s append to
`continue` (AC-3 legs (a) and (b) red); make `person_missing_name` write `clean_person_name(stem)`
(AC-1's double-space discriminator red); drop the `meeting_missing_from_timeline` arm from the
`elif` ladder (AC-1(a)'s emitter≡branch equality red); hard-code any one figure in
`_format_fix_summary` (AC-4(d)'s two-vault variation clause red); delete one `return "active"` arm
from `classify_person_tier` (AC-2(c) red on the code-side count AND on that arm's planted specimen);
and match the baseline's section headings by EQUALITY instead of by prefix (AC-5(a) red on §1 and
§2, which carry trailing qualifiers) — the mutation that proves the prefix rule is load-bearing
rather than decorative, and the one whose absence is why the first pass at this correction shipped a
leg that was still RED against the committed artifact. THREE MORE landed with this round's folds and
each targets a fold rather than a criterion: collapse §4's two credit points into a single
`repaired += len(undecided)` at the END of the lock block (M4 — AC-4(b)'s mixed plant goes RED with
BOTH issues reported `errored`, which is the exact defect the fold refuses, and this is the mutation
that proves the fold is a behaviour rule and not a paraphrase of the old one); hand-edit one drive
in the new module to pass `lint_vault.DEFAULT_VAULT` (M3's syntax half RED naming the line); and
hand-edit `_temp_vault` to return a path outside its `tmp` (M3's runtime half RED at the door,
before any mutating call runs). A TENTH landed with this round and it is the one that separates M3's
tightened requirement from its superseded one: hand-edit one check in the new module to re-bind
`vault = lint_vault.DEFAULT_VAULT` and then drive `run_lint(vault, do_fix=True)` — the argument's
SPELLING is untouched, so the syntax half's first two clauses stay green and the runtime door is
never called; only the provenance clause is RED, at the binding's own line. A build that implements
§6(d)'s `drives` census and skips its `bindings` census is green on this mutation, which is exactly
what makes it the mutation worth running.

An ELEVENTH and a TWELFTH land with this round, one per new mitigation, and each is chosen for the
same property as the tenth — it is GREEN against a build that folded the mitigation's words and not
its substance. **ELEVENTH (M5):** add `lint_vault.main()` to one check in the new module and observe
`test_every_mutating_drive_in_this_module_is_confined_to_a_temp_vault` RED naming that line. Nothing
about the module's own drives is touched, so every clause of Design §7 stays green
under a callee set that omits `main` — the call is invisible to `drives`, therefore to `bindings`,
`_temp_vault` is never involved, and the module names no live path outside the door — which is what
makes this the mutation that separates a callee set containing `main` from one without it.
**TWELFTH (M6):** add `import subprocess` to the new module and
observe `test_wall_membership_is_closed_for_every_file_this_item_touches` RED naming that line. Under
the STANDING `WALL_C_MODULES` that import is legal (`FS_MODULES - {"os"}` holds neither `subprocess`
nor `runpy`), so a build that runs Task 15's wall with the un-widened set is green on this mutation
while the module can re-enter the CLI as a child process. Both are observed and reverted; neither
leaves a plant behind.

A THIRTEENTH and a FOURTEENTH land with THIS round, one per new mitigation, chosen for the same
property again — each is GREEN against a build that folded the mitigation's words and not its
substance, and the fourteenth is green against a build that implements every clause of Design §7 as
it read before round 4. **THIRTEENTH (M7):** add
`lint_vault.quarantine_garbage(issues, tmp)` to one check in the new module — the `tmp` from that
check's own `with temp_dir() as tmp`, so the mutation NAMES no live-path token and clause (iv) stays
green on it, which is what makes it a clean discriminator for the callee set rather than for M8 —
and observe `test_every_mutating_drive_in_this_module_is_confined_to_a_temp_vault` RED naming that
line, clause (i) on the identifier `tmp` and `bindings` RAISING on the `with ... as tmp` binding.
Under a THREE-member callee set the call is collected by nothing — invisible to `drives`, therefore
to `bindings`, with `_temp_vault` uninvolved — so every clause stays green while a drive of the
script's IRREVERSIBLE write sits ungraded; that is what makes it the mutation separating a
four-member callee set from a three-member one, and the same drive written with
`lint_vault.DEFAULT_VAULT` in place of `tmp` is what a rename of Dave's live notes would look like.
**FOURTEENTH (M8):** hand-edit one check in
the new module to keep its correctly-bound `vault = _temp_vault(tmp)` drive EXACTLY as it is and to
build the issue list it passes from
`lint_vault.check_noise(lint_vault.read_vault(lint_vault.DEFAULT_VAULT), idx)`; observe the same
check RED, at the `lint_vault.DEFAULT_VAULT` reference's own line, with clauses (i), (ii) and (iii)
all still GREEN and the runtime door still EXECUTED. This is the mutation that proves clause (iv) is
load-bearing rather than a restatement — the argument half cannot see it by construction, because
`apply_fixes` never reads its `vault_path` — and it is the shape threat-model round 4 found. Both are
observed and reverted; neither leaves a plant behind.

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
- **Chasing the containment-wall family past the omission shapes that NAME the live path — the family
  is CLOSED over those, the deliberate-act residue is the mechanism's honest bound rather than an open
  gap, and the ONE omission residue that remains (the library's own `OBSIDIAN_VAULT_PATH` fallback) is
  DECLARED below and routed to Dave or the conductor rather than chased by a gate.** *(Bullet title
  corrected 2026-09-16; it previously read "past the OMISSION level — the family is CLOSED there",
  which round 5 falsified.)*
  Recorded here in the A3/A3b shape, because it is the kind of ruling that evaporates when it lives
  only in a gate round's non-blocking note and is then rediscovered as the next round's finding. The
  arc it closes is FIVE rounds long and monotone: threat-model round 1 asked for a containment wall
  (M3); round 2 falsified it at the BINDING level and §6(d)'s `bindings` census closed that level by
  `ast`'s own closure; round 3 falsified it at the ENTRY-POINT level (`main` reaches the live vault by
  omitting `--vault`) and at the PROCESS-BOUNDARY level (a child process is unreadable to any
  in-process census), and M5 and M6 close both; and round 4 falsified the version of THIS PARAGRAPH
  that ended at round 3, twice over — the entry-point level was closed by one member short
  (`quarantine_garbage`, whose write is the irreversible one, M7), and, more importantly, an
  enumeration of doors cannot close the level at all, because `apply_fixes` ignores its `vault_path`
  and writes from `issue.file_path`, so M8 closes at the SOURCE tokens instead. And round 5 falsified
  the version of THIS PARAGRAPH that ended at round 4, on its load-bearing PREMISE rather than on a
  mechanism: the 2026-09-15 wording read *"the wall is TOTAL over OMISSION shapes by CONSTRUCTION and
  not by enumeration … because a drive can only reach the live vault by NAMING it, and clause (iv)
  (M8) leaves the module no place outside `_temp_vault`'s own body to name it; the DOOR census (M5,
  M7) and the import wall (M6) are then belt-and-braces over the routes, not the load-bearing half"*,
  and a drive can ALSO reach the live vault without naming it —
  `obsidian_schemas/repositories/base.py:_resolve_vault_path:104-114` falls back to
  `os.environ.get(ENV_VAULT_PATH)` INSIDE the library (`ENV_VAULT_PATH:75`, `_is_unconfigured:86-101`,
  `BaseRepository.__init__:154`, the four repositories exported at
  `obsidian_schemas/__init__.py:74-77`), so `repo = PersonRepository()` beside
  `read_vault(repo.vault_path)` passes all four clauses with the runtime door executed and the import
  wall clean, and rewrites the live vault wherever that variable is exported — which is Dave's own
  machine, where `CLAUDE.md`'s floor command is hand-run. **The rule, RESTATED 2026-09-16 to what the
  mechanism actually is, stated as a bound and not as a promise:
  the wall is TOTAL over the OMISSION shapes that NAME the live path — a drive that reaches the live
  vault because somebody forgot to pass a path, forgot which entry point defaults to
  `OBSIDIAN_VAULT_PATH`, reached the tool through a door nobody thought to watch, or handed a
  correctly-contained drive an issue list scanned from a path the module SPELLS — because clause (iv)
  (M8) leaves the module no place outside `_temp_vault`'s own body to spell it, at three token shapes
  `ast` closes. It is NOT total over an omission shape that OBTAINS the path without spelling it, of
  which the library's own `OBSIDIAN_VAULT_PATH` fallback is one and is OPEN (below); and because the
  source half is therefore not total, the DOOR census (M5, M7) and the import wall (M6) are
  LOAD-BEARING and not belt-and-braces. And it is still NOT total over
  DELIBERATE ACTS.** The known residues are named rather than hidden, and M8 adds one rather than
  removing any: a decoy spelled with the door's own name
  (`helpers._temp_vault(tmp)`, `from x import make as _temp_vault`, a second `def _temp_vault` later in
  the module) is GREEN because §6(d) compares the callee's NAME
  (`ast.Attribute.attr`, §6(d)'s resolution rule); an author who writes the escape INSIDE
  `_temp_vault`'s own body is GREEN because the by-function exemption permits it by construction, and
  that exemption is mandatory because the door's own negative assertions must name both tokens; and
  nothing stops an author from deleting a clause
  of the wall itself. All three are acts of disguise rather than the drift or the convenient shortcut this
  wall exists to catch, and a mechanism that defended against the module's own author would have to
  re-implement Python's name resolution — a clause per level, forever, which is what stopped WI-020's
  equivalent ladder only when someone wrote the boundary down. **Why this is a scope boundary rather
  than a spec-writer's judgement:** this is a SUFFICIENCY call, and sufficiency belongs to Dave or the
  conductor. It is stated here so a later gate ROUTES AGAINST it instead of re-deriving it, and so
  that overriding it is one explicit act — if Dave or the conductor wants the deliberate-act level
  closed too, that is a new clause (or its own work item) and this paragraph is what it overrides. Any
  gate finding at the DELIBERATE-ACT level should cite this paragraph and escalate rather than REVISE
  — and that instruction is scoped to that level and to nothing else: a finding at the OMISSION level
  is NOT covered by this bound, is a legitimate REVISE, and the one time this paragraph's stated
  reason was broader than its mechanism (the 2026-09-15 "a drive can only reach the live vault by
  NAMING it") it would have waved through exactly the class it names, which is why the correction
  above was worth a round on its own.
  **And the sufficiency trigger the spec-review round names, recorded here so it is not a gate's
  memory:** a FIFTH threat-model round opening a NINTH `kind: required` mitigation on this family
  after M7 and M8 land as written is the signal that the family's cost has outrun its value, and the
  gate holding that round should stop and ask Dave or the conductor rather than emit another REVISE.
  **THAT TRIGGER FIRED on 2026-09-16 and the call is OPEN with its owner.** Threat-model round 5 took
  the instrument at its word — it emitted EIGHT fences and not nine, and routed the mechanism here;
  spec-review round 5 routed it the same way; the seventh spec-writer pass made the premise
  correction above and did NOT decide the mechanism, because sufficiency is not the spec-writer's to
  call in either direction. **The question, stated so the ruling is cheap to make:** should the check
  module be forbidden to construct an `obsidian_schemas` repository at all, closing the library's
  `OBSIDIAN_VAULT_PATH` fallback as a third source? *For:* it is a real route, it is an OMISSION shape
  rather than a disguise (the no-argument form is the library's own documented convenience form), this
  tree has been bitten by the identical generator and guards it twice under `tests/`
  (`tests/identity_fixture.py:seed_vault:85-100`, whose docstring names `_resolve_vault_path` and the
  `tests/` blind spot in terms; `tests/record_identity_golden.py:28,89`), no standing wall reaches a
  `.py` file under `tests/` (`tests/test_vault_path_required.py:NO_ARG_CONSTRUCTION:382` runs over
  MARKDOWN only with `DOC_SCAN_EXCLUDED:387` excluding `docs`, and
  `test_no_implicit_vault_path_defaults` stops its universe at `("obsidian_schemas", "scripts")` at
  `:320`), and the failure mode is green-in-the-cage / live-vault-write-on-the-author's-laptop.
  *Against:* it is materially less likely than M8's route — `scripts/lint_vault.py` names no
  repository anywhere and every repository construction under `tests/` passes an explicit vault — and
  it is the sixth round on one family. *Cost if closed:* one more CLOSED shape in the census Task 7
  already builds — a callee resolving (by the same `ast.Name.id` / `ast.Attribute.attr` rule `drives`
  and `bindings` use) to an identifier ending `Repository`, recorded as
  `(module_id, lineno, token, enclosing)` like the other three and graded by Task 9's EXISTING clause
  (iv): no new check, no fifth derivation, no count moved. The requirement would be ZERO repository
  constructions in the module rather than "no no-arg construction", because `_is_unconfigured:86-101`
  swallows blank, whitespace-only and `"."` as well; the import-allowlist shortcut cannot work,
  because `tests/derivations.py:module_import_uses:847` reports the ROOT module and so cannot
  distinguish `from obsidian_schemas.repositories.base import SKIP_REASONS` — which M1's verify NEEDS
  — from `from obsidian_schemas import PersonRepository`; and a global `os.environ` scrub at module
  import is refused as unscoped shared state in a pytest process where
  `tests/test_identity_endgame.py:330` and `tests/test_vault_path_required.py:84` both manipulate that
  same variable. Until the ruling lands, this residue is DECLARED and not closed, and no gate should
  read it as covered by the deliberate-act bound above.

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
DELETES the `:949` fold (and `file_fixed`, and the `:972` increment) and credits each issue on the
statement after its OWN `write_note` returns — at `:957` for the first write, at `:975` for the
wikilink write — and adds a per-branch decline record; all of it is bookkeeping, and no branch's
repair logic, no `delta` key, no gate call and no `write_note` argument changes. The one thing the
bookkeeping must not get wrong is WHICH end of the frame it credits at, and both wrong ends
misreport a real note: crediting before the write (today's `:949`) reports an uncommitted repair as
done, and folding once at the end of the lock block reports a COMMITTED repair as `errored` when the
second write raises. M4 is that ruling and AC-4(b)'s mixed plant is what holds it. *Mitigation:* the WI-021 battery
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
WI-023), and the new module adds eight checks, most of which materialize 53 notes into a temp
directory (M3's containment check and the wall-membership check read source instead and materialize
nothing).
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

## Spec Review — 2026-09-15 (round 3)

**Recommendation: REVISE — return to spec writer (gaps to fix)**

Third spec-review round. The carry-forward is my own two prior sections and what happened to each:
round 1 REVISEd on three blockers (no `## Mitigation Folds` section; M4 unlanded and contradicting
the signed AC-4(b); M3 unlanded), round 2 REVISEd on two (M3's fold record byte-stale against the
tightened fence; the tightened requirement on zero surfaces while six stated the rule it replaced).
The spec-writer's fourth pass answered both, and `## Threat Model — 2026-09-15 (round 3)` then read
the re-folded material and PROMOTEd — while opening TWO NEW `kind: required` fences. Per the reset
rule I walked the bar from line 1 rather than against that diff, and re-resolved every
symbol-anchored citation by reading the code rather than treating the injected drift audit as a
Check-3 pass.

Rulings on record: A3/A3b's YAML-formatting and body-only-write deferrals, the `FixOutcome.fixed` → `repaired` field-name ruling, AC-5's §4-lifetime rule (presence never emptiness), the exit-run-as-ship-condition ruling, and threat-model round 2's one-module scope for M3's wall are all settled in this document and were routed against rather than re-litigated.

**Both round-2 blockers CLOSED, verified against the code and the fences rather than against the
fourth pass's account of itself.** (1) M3's fold record `desc` at `:2172` is byte-identical to the
round-3 fence at `:4135`, and I diffed all four carried records against their round-3 fences
(`:2156`/`:4121`, `:2164`/`:4128`, `:2172`/`:4135`, `:2180`/`:4142`) — all four fresh. (2) The
provenance tightening is on every surface I enumerated last round: Design §6(d)'s `VaultArgScan`
pair with the `bindings` census and its closed RAISE set (`:1339-1399`, vacuity closed INSIDE the
scan at `:1390-1394`), Design §7's three-clause syntax half with the "no proper subset" sentence
replacing the old overclaim (`:1454-1472`), Task 7 (`:1812-1829`), Task 9 (ii) inside the ONE check
(`:1859-1869`), `## Verification`'s `bindings` fixture battery with four REDs, the scoping near-miss
and the closed-set RAISES (`:2236-2255`) plus the tenth mutation (`:2288-2294`), and the
`tests/derivations.py` `## Write Targets` fence (`:2009`). My round-2 notes 1 and 2 closed with it
(`:1436` now anchors `FORBIDDEN_DEFAULT_PATTERNS` at `:278`; `:1448-1450` and `:1855-1857` now write
`os.environ.get(..., "")` with the reason). The three counts note 3 warned about did not move.

The verdict turns entirely on the two mitigations the threat model opened AFTER the spec-writer's
last turn, and it is mechanical before it is substantive.

### Citation verification

All verified ✓ — re-resolved by reading the code at each site, and each MEANS what the spec claims.
The injected drift audit's one finding is a narration ordinal, not a live citation: `:895` and
`:3815` are prior rounds recording the old `:320` suffix, and the LIVE citation at `:1436` already
reads `FORBIDDEN_DEFAULT_PATTERNS:278`, which is correct (`tests/test_vault_path_required.py:278` is
`["expanduser", "Path.home()", "/Users/"]`, and `:320` really is the
`for directory in ("obsidian_schemas", "scripts")` universe line the sentence's second half is
about). Re-read this round:

- `scripts/lint_vault.py` — the `apply_fixes` frame entire: `NameGateRefusalRecord:805-818` with the
  two-field closure; `FixOutcome:820-825` as `(fixed, refused)`; `apply_fixes:827-828` with
  `idx: Optional[dict] = None`; `by_file` filtering on `issue.auto_fixable` at `:832-835`; the
  `FileNotFoundError` guard at `:853`; lock + `read_note` at `:858-859`; `file_fixed` at `:882`; the
  five branches at `:888`, `:896`, `:903`, `:911`, `:929` and the six decline sites at `:890`,
  `:906`, `:913`, `:935-936`, `:963-973`; `:897` really is `fpath.stem.lstrip("@")`;
  `person_missing_name:896-901` really has no guard; `gate_write` at `:947` landing BEFORE
  `fixed += file_fixed` at `:949`; the first write at `:957` inside `if changed:` at `:951`; the
  wikilink pass at `:960-975` with `fixed += 1` at `:972` and its write at `:975` **inside the `with`
  block but outside `if changed:`**, which is what makes per-write crediting the only placement
  yielding AC-4(b)'s signed answer — M4 re-confirmed against the frame, not the prose.
- `read_vault:110-118` — `except Exception: continue` at `:117-118`, VD-1 exact.
  `run_lint:1191-1199` — the summary print inside `if fixable:` at `:1193`, `idx` passed at `:1194`,
  the `"No auto-fixable issues found."` else-arm at `:1213-1214`, the re-scan rebinding `all_files`
  at `:1201`. Design §5's three rulings are true of that frame.
- The five emitters at `:341`, `:357`, `:386`, `:530`, `:596`, each passing `check` POSITIONALLY as
  `args[1]` (which is the form §6(a)'s scan rule depends on) — and `person_missing_name`'s category
  really is `"completeness"` at `:388`, so AC-5(b)'s `(structural)` mis-join trap is real.
  `CATEGORY_ORDER:1003` is the five-member list §9's strip rule reads.
- `main:1252` with `--vault` carrying `default=DEFAULT_VAULT` at `:1255` and
  `run_lint(vault_path, …, do_fix=args.fix, do_quarantine=args.quarantine)` at `:1299-1308` — M5's
  premise, confirmed independently of the threat model's trace.
- `tests/derivations.py` — `FS_MODULES:68` is `{"os","shutil","tempfile","fcntl","filelock","mmap"}`
  and `OS_READONLY_NAMES:69` holds only `environ`/`getenv`/`sep`/`path`/`fspath`/`getcwd`;
  `tests/test_name_gate_wall.py:1043` is `WALL_C_MODULES = frozenset(FS_MODULES - {"os"})`. Neither
  set holds `subprocess` or `runpy` — M6's premise, confirmed. `module_import_uses:847-870` takes an
  arbitrary `modules` iterable and reports the ORIGINAL module name in both statement forms, so M6
  needs no derivation change.
- `tests/test_fixture_vault.py` — both universe sites still unwidened at `:508-509` and `:1302`,
  both declared-homes sets still exactly two members at `:510-514` and `:1315-1318`.
- The two precondition artifacts, re-read against AC-5's predicates rather than trusted: the census
  table really is at `docs/vault-shape-census.md:275-281` carrying 821/315/19/0/0 with the three
  category parentheticals all `CATEGORY_ORDER` members; `docs/lint-vault-live-baseline.md` carries
  its one 40-hex HEAD SHA at `:12` in the header, §0's argv fences at `:22-24` and `:30-32` with the
  stdout fence at `:34-70` (first non-empty line `Vault Lint Report — $VAULT`, not an interpreter
  path), §1's six-row table at `:77-84` with the bold totals row, §1 and §2 carrying NO fence, §3's
  argv fence at `:111-117` and stdout fence at `:119-122` (`paths walked: 3952` / `undecodable: 0`),
  and §4 at `:135-158`. AC-5(a)'s narrowed shape contract and AC-5(b)'s tolerance are both GREEN
  against HEAD as written — 821/835 delta `+14`, 315/315, 19/19, 0/0, 0/0.

### Blocking issues

1. **M5 and M6 have NO fold record, so `specced -> ready` is refused as things stand.**
   `## Threat Model — 2026-09-15 (round 3)` opens SIX `mitigation` fences (`:4118-4158`), which makes
   it the latest SPEAKING round, and two of the six are new: **M5** (`:4146-4151`, `landed: Task 7`)
   and **M6** (`:4153-4158`, `landed: Task 15`). `## Mitigation Folds — 2026-09-15` carries exactly
   four `fold` fences (M1, M2, M3, M4) and its own opening paragraph declares itself restated against
   **round 2** (`:2097-2099`) — which was correct when it was written and is now one round stale. The
   D8c rule refuses the transition while any `kind: required` mitigation of the latest speaking round
   lacks a complete, fresh fold record, so a PROMOTE here buys a refused transition for the same
   mechanical reason my round-1 blocker 1 and round-2 blocker 1 did. The mechanical half of the fix
   is two more five-key `fold` fences in that section carrying `desc` copied verbatim from `:4149`
   and `:4156`, plus a one-line correction to the section's opening paragraph naming round 3 as the
   round it is restated against. It is NOT sufficient on its own, which is item 2. M1–M4's records
   stay fresh and need no re-copy — I diffed all four against round 3's re-emitted fences.

2. **M5's and M6's substance is on ZERO surfaces, and the surfaces that state the behaviour still
   state the pre-M5/M6 rule.** This is the WI-226 sweep obligation, not an edit, and it is the half
   that makes a record mean something: a `desc` copied under item 1 without this sweep makes the
   record mechanically FRESH while the mitigation is unsatisfied, and the satisfaction judgment is
   then the only wall left. Enumerated, so the sweep is executable rather than remembered:

   **M5 — `main` joins §6(d)'s callee set.**
   - **Design §6(d) (`:1349-1351`)** — "For every `ast.Call` whose callee resolves to the bare name
     `apply_fixes` or `run_lint`". A two-member hand list; `main` is absent. Note that §6(d)'s
     EXISTING rule then does the work with no new text once `main` is in the set — "a collected call
     passing a vault argument at NEITHER position RAISES" (`:1355-1356`), and `main()` takes no vault
     argument at any position — so the edit is the callee set alone.
   - **Task 7 (`:1808-1830`)** — its work clause and its `Verify:` name four planted drive shapes
     (`apply_fixes(issues, vault, idx)`, `run_lint(vault, do_fix=True)`,
     `lint_vault.run_lint(vault_path=vault)`, `run_lint(lint_vault.DEFAULT_VAULT)`); none is a `main`
     call. This is the task M5's fence names, so the ordinal resolves but the work does not carry it.
   - **`## Verification`'s `drives` counting-wall bullet (`:2225-2235`)** — four positive shapes,
     three near-misses (`run_lint_report(...)`, another callee taking a `vault` argument, the STRING
     `"run_lint"` in a docstring) and three RAISE shapes. WI-235's prescription is that the spec
     names the match-shapes the matcher must resolve: a widened callee set owes a planted
     `lint_vault.main()` and a bare `main()` that must each RAISE, beside the near-miss that must NOT
     match (a call to some other zero-argument callee, e.g. `setup()`), without which the widening's
     GREEN is uninformative either way.
   - **`## Write Targets`' `tests/derivations.py` fence (`:2009`)** — "`drives`, every `apply_fixes` /
     `run_lint` call's vault argument in the new check module". The declaration the conveyor reads
     still states the two-member set.

   **M6 — the new module cannot re-enter the CLI as a child process.**
   - **Task 15 (`:1947-1966`)** — hands `module_import_uses` over the script and the new check module
     but names no module set, so it inherits the standing one; `WALL_C_MODULES` is
     `FS_MODULES - {"os"}` and holds neither `subprocess` nor `runpy`, which is exactly the hole M6
     names. This is the task M6's fence names.
   - **Design §7 (`:1426-1440`, `:1472`)** — its "two halves, and the pair is what makes it total"
     claim is the sentence a builder reads to decide the guard is finished, and the subprocess route
     is a third route it does not mention. Design §7 currently closes with "no proper subset of
     (i)+(ii)+(iii)" — true of the callee-argument surface and silent on the import surface.
   - **`## Verification`** — the same WI-235 question: a planted `import subprocess` and a planted
     `from runpy import run_path` driven through `module_import_uses` under the widened set as REDs,
     beside the near-miss it must NOT match (the module's own legitimate `importlib.util` /
     `contextlib` / `io` imports, none of which may appear), so the widened set is proved to be
     reaching rather than a no-op.
   - Design §7's note that the new module must not name `ast` and must not hand-type a `SKIP_REASONS`
     member (`:1472-1473`, and Task 9 at `:1872-1873`) is the natural home for the companion
     sentence, since it is the module's existing "what this module may not contain" list.

   **Land both inside machinery the plan already ships, and the four counts do not move.** M5 rides
   `mutating_drive_vault_args`' callee set (no fifth derivation) and M6 rides Task 15's existing
   `test_wall_membership_is_closed_for_every_file_this_item_touches` (no ninth check), which is what
   the threat model itself prescribes (`:4078-4092`). Stated explicitly because this document has
   already had to re-sync them once: Design's opening inventory (three code changes, FOUR
   derivations, ONE new module, SIX edited modules, `:1033-1038`), §7's five-plus-three check count
   (`:1403-1405`), R4's "eight checks" (`:2430`) and Task 16's expected direction (`:1972-1973`) all
   still hold under that shape and must not move.

### The regress signature — flagged, with a sufficiency ruling recommended rather than a fourth round

Naming this rather than emitting the next single-site REVISE, because the arc across my three rounds
is monotone — every objection closed and stayed closed — and the material each new finding lands on
is the material the previous fold ADDED:

- Round 1: four mitigations unfolded, one of them (M3) a containment wall over the new check module.
- Round 2: M3's wall proved insufficient at the BINDING level; the fold added §6(d)'s `bindings`
  census to close it.
- Round 3 (this one): the same wall proved insufficient at the CALLEE level and at the IMPORT level;
  M5 and M6 close those.
- And threat-model round 3's own note 1 (`:4162-4171`) already identifies the NEXT level and declines
  to chase it — a decoy spelled `_temp_vault` is green, because §6(d) resolves a dotted callee to its
  `ast.Attribute.attr` (`:1369-1372`). I confirmed that independently: `helpers._temp_vault(tmp)`
  and `from x import make as _temp_vault` both yield provenance `"_temp_vault"`.

That is the WI-020 regress signature: the findings have shifted from the thing under review (does
`--fix` repair correctly and account for every issue — AC-1 through AC-5, all five signed and all
five untouched since) to the machinery checking the thing (can the check module itself reach Dave's
vault), and each fix creates the surface the next finding lands on. The threat modeler drew a
principled line — omission and drift shapes are in, deliberate acts are out — but that line lives in
a non-blocking note of a gate round, where the next cold-start gate will not route against it.

**So the recommendation attached to this REVISE is that the same pass which lands M5 and M6 also
records the family closure as a standing ruling in `## Scope Boundary`,** in the shape this document
already uses for A3/A3b: the containment-wall family is closed at the OMISSION level (an entry point
reachable without naming a vault, an import that re-enters the tool as a child process), with the
deliberate-act residue — a decoy or a second `def` spelled with the door's own name — recorded as the
honest bound of the mechanism rather than as an open gap. That converts the next level from a finding
into a scope boundary a later round routes against, which is what stopped WI-020's equivalent ladder.
It is a ruling only Dave or the conductor can make stick; I am recommending it, not making it.

### Non-blocking notes

1. **`## Mitigation Folds`' M3 re-sweep paragraph overclaims, and the paragraph is being edited
   anyway under blocking issue 2.** `:2138-2141` reads "an alias, a wrapper or a second constructor
   is RED naming its line". Verified against §6(d)'s own resolution rule at `:1369-1372`: that is
   true of `vault = make_vault(tmp)` (provenance `"make_vault"`, RED) and FALSE of
   `helpers._temp_vault(tmp)` or `from x import make as _temp_vault` (both resolve to provenance
   `"_temp_vault"`, GREEN). Same defect class as my round-2 blocking issue 2 — a sweep paragraph
   claiming a completeness its mechanism lacks — but non-blocking here because it is sweep narration
   rather than a builder instruction or a criterion clause, and because the residue is the one the
   threat model has consciously ruled acceptable. One sentence, in the edit that is already happening;
   raised by threat-model round 3 note 1 and confirmed here independently, and a note deferred twice
   is a note that evaporates.

2. **Threat-model round 3 note 2 (definition order) is free and worth taking while Task 9 is
   written.** Defining `test_every_mutating_drive_in_this_module_is_confined_to_a_temp_vault` FIRST
   in the new module makes the detector fire ahead of the driving checks in an ordinary floor run.
   Not a guarantee under `-k` or direct invocation, and M5/M6 close the routes that bypass the door,
   so this is an ordering courtesy rather than a mitigation — but it costs nothing at authoring time
   and cannot be retrofitted cheaply.

### What is NOT a gap — checked and clean

Stated so round 4 does not re-walk them. `## Write Targets` coverage is exact in both directions:
each of the sixteen tasks' target files appears in the nine builder `writes` fences, no fence names a
path no task writes, the two `kind: precondition` paths are read by AC-5 and appear in no builder
fence, the driven doc is implicit, and Tasks 1 and 16 write only the Build Log — **and M5's and M6's
fold work adds no target**, landing in `tests/derivations.py` and `tests/test_lint_vault_fix_rules.py`
respectively, both already declared. Every path is inside `pipeline-runners.yaml:34-38`'s grant, so
the L3 level the frontmatter carries is not under-declared. Sixteen canonical
`- [ ] **Task N — …**` definitions with unique ordinals 1–16 (counted: 16), and every `landed: Task N`
across all three threat-model rounds — 2, 4, 9, 4, **7 (M5), 15 (M6)** — resolves to one, so no D8b
refusal is latent. All sixteen carry a well-formed `verify:` declaration (counted: 16) — fourteen
naming bare `test_` names, Task 1 `baseline` and Task 16 `hand-run`, both correct uses of the closed
exception kinds — and no verify command writes anything outside `write_authority`. `OPEN: None`, zero
open items. The five criteria remain signed and untouched: `ac_hash: 973d7a08f068` with all five
per-criterion hashes and `intent_hash` unmoved, and every edit since the signature sits outside
`## Intent` and `## Acceptance Criteria` — I checked the spans rather than trusting the claim, and
M5/M6's fold work is likewise outside both (neither criterion states the wall). Check 11 is satisfied
by `## Verified Diagnosis`' four falsifiable claims, each of which I re-executed against the code
above. The WI-235 counting-wall prescription is discharged for every count-shaped oracle EXCEPT the
two M5/M6 widen, which is blocking issue 2's last two bullets; the WI-278 corpus-fixture arm is
chosen explicitly in AC-5(b)'s one-line coupling declaration; and the WI-229 conscious-pin sweep is
what produced the nine-site rename inventory across four modules, which I re-confirmed against
`tests/test_lint_vault_fix_gate.py`'s eight field-touch sites and the three outside it.

### Carried-forward notes

Every still-open non-blocking note from every prior round, by name:

- **Threat model round 1 note 1 / round 2 note 3 / round 3 note 3 (the exit attestation's redaction
  reminder is absent from `docs/lint-vault-live-baseline.md` §4's own bytes)** — STILL OPEN,
  re-deferred for the fifth time for the same correct reason: §4 is conductor-owned and outside the
  builder's write authority, so it has no Implementation-Plan task to land in and a fence pointing at
  one would be a fiction. The conductor's, at the ship door.
- **Threat model round 1 note 2 / round 2 note 4 / round 3 note 4 (`apply_fixes:994` prints
  `str(exc)` to stderr)** — STILL OPEN as a deliberate non-change. Re-verified at the code this
  round: the print is still `f"  Fix error on {fpath.name}: {exc}"` at `:994` and the handler set
  does not widen, so no new content reaches that channel; it is pinned as a message equality at
  `tests/test_lint_vault_fix_gate.py:123-125` and closing it would move a pinned equality for no gain
  in this item.
- **Threat model round 2 note 1 (M3's wall universe is ONE module)** — a standing scope ruling, not
  an open note; routed against rather than re-litigated. M5 and M6 do not widen it either — both are
  clauses over the same single module.
- **Threat model round 3 note 1 (the decoy-named door)** — raised as my non-blocking note 1 above and
  actionable inside blocking issue 2's edit; its wider shape is the regress-signature ruling I
  recommend.
- **Threat model round 3 note 2 (check definition order)** — carried as my non-blocking note 2 above.
- **Data audit round 2's two carried items** — both STILL OPEN and both correctly outside the spec:
  the build-start re-grounding should re-run AC-5(b)'s five-row comparison before the first edit (the
  baseline is now five days old and the vault churns weekly — I re-confirmed it is still GREEN
  against HEAD this round, which is a snapshot fact and not a standing one), and the exit half of
  A7's bracket has no battery wall by construction and lives at the conductor's ship door.
- **My round-1 notes 1–5** — all CLOSED (recorded in my round-2 section).
- **My round-2 notes 1–3** — all CLOSED: note 1 (`FORBIDDEN_DEFAULT_PATTERNS`' trailing ordinal) by
  the re-anchor to `:278` at `:1436`; note 2 (`_temp_vault`'s `os.environ` subscript) by
  `:1448-1450` and `:1855-1857`; note 3 (the three counts) by the fold landing inside the existing
  check, which I re-verified holds.
- **Architect round 4 notes 1–4 and the AC red-team's label slip** — all CLOSED, recorded in my
  round-1 section.

```verdict
gate: spec-reviewer
verdict: REVISE
date: 2026-09-15
model: claude-opus-5
targets: M5, M6, Task 7, Task 15, #mitigation-folds, #design, #verification
prior: held
basis: folded-material
findings: 2/3
note: Both round-2 blockers closed and I verified them at the code rather than at the fold record — M3's `desc` at `:2172` is byte-identical to the round-3 fence at `:4135`, all four carried records diff clean against their re-emitted fences, and the provenance tightening is landed on all six surfaces I enumerated. What blocks is new material the threat model opened after the spec-writer's last turn: `## Threat Model — 2026-09-15 (round 3)` emits SIX `kind: required` fences and is therefore the latest SPEAKING round, but `## Mitigation Folds` carries four and declares itself restated against round 2 (`:2097-2099`), so M5 (`:4149`, `landed: Task 7`) and M6 (`:4156`, `landed: Task 15`) have no record at all and D8c refuses `specced -> ready` — the same mechanical wall as my two prior rounds. A copied `desc` alone is insufficient: both mitigations are on zero surfaces. §6(d)'s callee set is still the two-member hand list `apply_fixes`/`run_lint` (`:1349-1351`), and I confirmed `main:1252` independently — `--vault` carries `default=DEFAULT_VAULT` (`:1255`) and it calls `run_lint(..., do_fix=args.fix)` at `:1299-1308`, so the CLI reaches the live vault by OMITTING an argument, invisible to `drives`, to `bindings` (scoped by `drives`) and to the runtime door alike; and Task 15 hands `module_import_uses` the standing set, where `WALL_C_MODULES = FS_MODULES - {"os"}` (`tests/test_name_gate_wall.py:1043`, `tests/derivations.py:68`) holds neither `subprocess` nor `runpy`. Four surfaces owe M5 (§6(d), Task 7, `## Verification`'s `drives` battery, the `tests/derivations.py` Write-Targets fence) and three owe M6 (Task 15, Design §7, `## Verification`), each with the WI-235 shapes the widened matchers must and must not resolve; both land inside machinery the plan ships, so the four counts this document has re-synced once do not move. I am also FLAGGING THE REGRESS SIGNATURE rather than emitting round 4 on it: my three rounds are monotone but each finding lands on the surface the previous fold added — wall, then binding level, now callee and import level — and threat-model round 3's own note 1 identifies the next level (a decoy spelled `_temp_vault` is green, which I confirmed against §6(d)'s `ast.Attribute.attr` resolution at `:1369-1372`) and declines to chase it in a place no later gate routes against. The pass that lands M5/M6 should record that line as a standing `## Scope Boundary` ruling — family closed at the omission level, the deliberate-act residue recorded as the mechanism's honest bound — which is a sufficiency call for Dave or the conductor, not mine. Everything else re-verifies clean: every symbol-anchored citation resolves AND means what the spec claims (the drift audit's one finding is a narration ordinal; the live cite at `:1436` already reads `:278`), Write-Targets coverage is exact both ways and M5/M6 add no target, sixteen canonical tasks each carry a well-formed `verify:`, every `landed: Task N` including 7 and 15 resolves, and the five signed criteria are untouched with AC-5 still GREEN against the committed baseline and census (821/835 delta `+14`, 315/315, 19/19, 0/0, 0/0).
```

## Spec Review — 2026-09-15 (round 4)

**Recommendation: REVISE — return to spec writer (gaps to fix)**

Cold-start re-read from line 1, full document, not a diff read of the fifth pass. Every citation
below was resolved by opening the file and reading the lines, never by trusting the drift audit,
the fold record's account of itself, or threat-model round 4's paraphrase.

Rulings on record: A3/A3b (the YAML-reformat family, argued out on solve-in-one-place grounds), threat-model round 2 note 1 (M3's wall universe is ONE module), and the containment-family closure at `## Scope Boundary:2655-2679` — I route against all three rather than re-litigating them, and blocking issue 2 is NOT a re-litigation of the third but a correction to a factual claim inside it that has since been falsified at the code.

### Citation verification

All live symbol-anchored citations resolve AND mean what the spec claims. The injected drift
audit's one finding is not a live defect: `tests/test_vault_path_required.py:FORBIDDEN_DEFAULT_PATTERNS:320`
occurs at `:4117`, inside my own round-2 section's archival finding text; the LIVE cite at
`:1514` already reads `:278`, which I confirmed by reading the file — `FORBIDDEN_DEFAULT_PATTERNS =
["expanduser", "Path.home()", "/Users/"]` is at `tests/test_vault_path_required.py:278` — and `:320`
is correctly named separately at `:1516` as the universe line, which I also confirmed
(`for directory in ("obsidian_schemas", "scripts")` at `:320`). No re-anchoring is owed.

Re-read at the code this round rather than carried forward: `apply_fixes:827-828` (signature, vault
argument SECOND positional); `grep vault_path scripts/lint_vault.py` returning `:827` as its only
occurrence in that function; `FixOutcome:820-825`; the five decline sites `:890`, `:906`, `:913`,
`:935-936`, `:963-973`; the gate at `:947`, the fold at `:949`, the writes at `:957` and `:975`;
`quarantine_garbage:1112-1144` with its vault argument SECOND positional at `:1113`,
`quarantine_dir = vault_path / "_quarantine"` at `:1116` and the moved sources `issue.file_path` at
`:1121`, reaching `vault_io.ensure_dir:1134` and `vault_io.move_note:1140`; `run_lint:1147-1156`,
its `apply_fixes` call at `:1194`, its `quarantine_garbage` call at `:1220`, the summary print at
`:1198-1199` inside `if fixable:` at `:1193` with the `"No auto-fixable issues found."` else-arm at
`:1214`, the pre-fix `read_vault` at `:1160` and the post-fix re-scan at `:1201`; `main:1252` taking
no parameters with `--vault` carrying `default=DEFAULT_VAULT` at `:1255`.

### Blocking issues

**1. The latest SPEAKING threat-model round is round 4, and two of its eight `kind: required`
mitigations have no fold record and no surfaces — D8c refuses `specced -> ready`.** This is the
third consecutive round on the same mechanical wall, and the mechanics are not in doubt:
`## Threat Model — 2026-09-15 (round 4)` (`:4864`) emits EIGHT `kind: required` fences, M1 through
M8 (`:5049-5103`), so it is the round `parse_mitigations` selects. `## Mitigation Folds`
(`:2272`) carries SIX records and declares itself in its own opening sentence restated against
`## Threat Model — 2026-09-15 (round 3)` (`:2274-2276`) — a sentence that is now false as written.
M7 (`:5091-5096`, `landed: Task 7`) and M8 (`:5098-5103`, `landed: Task 9`) have no `fold` fence at
all. Both ordinals resolve to real canonical tasks, so no D8b refusal is latent; what refuses is
D8c.

A copied `desc` will not discharge this, because the substance of both is on ZERO surfaces and I
verified each premise at the code rather than accepting round 4's account:

*(a) M7 — the callee set is three members and the script has four mutating entry points.* Design
§6(d)'s `drives` census is `apply_fixes` / `run_lint` / `main` (`:1402`). The script's only
`vault_io` mutation sites are `write_note` at `:957` and `:975` (both in `apply_fixes`) and
`ensure_dir` at `:1134` plus `move_note` at `:1140` (both in `quarantine_garbage:1112-1144`), which
I settled by reading the function, so the mutating entry points are `apply_fixes`,
`quarantine_garbage`, `run_lint` and `main`. The missing member is the one whose write is
IRREVERSIBLE, and it is not a shape a builder has to go looking for: this item PINS the two
`garbage_candidate_*` detectors that decide what `--quarantine` moves (AC-2's pinned set), so
`lint_vault.quarantine_garbage(issues, vault)` is the natural drive for AC-2's leg (b) and is
invisible to `drives`, therefore to `bindings` (scoped BY `drives`), with `_temp_vault` never
called. The closure needs no new text — `quarantine_garbage`'s vault argument is the SECOND
positional at `:1113`, identical in position to `apply_fixes`' at `:827`, so §6(d)'s existing
position table grades it as-is. Four surfaces owe it: §6(d)'s callee set (`:1401-1425`), §7's
syntax half (`:1538-1547`), Task 7's work and verify (`:1947-1967`), and `## Verification`'s
`drives` battery (`:2462-2483`), the last needing the WI-235 pair — a planted
`lint_vault.quarantine_garbage(issues, lint_vault.DEFAULT_VAULT)` that must RAISE, and it is worth
running precisely because it is GREEN under the three-member set.

*(b) M8 — the wall grades an argument that provably does not determine what gets written, and this
is the half that matters.* I confirmed it independently: `vault_path` appears in `apply_fixes`
exactly once, in the signature at `:827`, and is referenced nowhere in the body; the write targets
come from the issues (`by_file[issue.file_path]` at `:835`, then `fpath` at `:853`, `:858`, `:957`,
`:975`). So a contained vault ARGUMENT constrains nothing about what `apply_fixes` writes —
containment holds only transitively, through the issues' provenance, which Design §7 grades
nowhere. The four-line escape in round 4's finding passes clause (i) spelling, clause (ii)
non-vacuity and clause (iii) provenance with the runtime door EXECUTED and the import wall clean,
while rewriting the live vault; under `quarantine_garbage` it is worse than a wrong write, because
`vault_path` there is only the destination root (`:1116`) while the sources moved are
`issue.file_path` (`:1121`), so a correctly-contained vault argument turns it into live notes
renamed into a temp directory that is then deleted. M8's source-side clause is the right instrument
and is the reason this is a fold that can END the family rather than a seventh door: the live path
has exactly two sources in this module's universe, and `## Scope Boundary` already says the
mechanism's job is omission shapes.

*And one thing the M8 fold must PRESCRIBE rather than leave to the builder, which is mine and not
round 4's.* M8's `desc` exempts "`_temp_vault`'s own negative assertions" but names no mechanism
for the exemption, and the exemption is mandatory rather than incidental: Design §7's runtime half
(`:1523-1534`) and Task 9 (`:1988-1998`) both ORDER `_temp_vault` to compare against
`Path(lint_vault.DEFAULT_VAULT).resolve()` and `Path(os.environ.get("OBSIDIAN_VAULT_PATH", "")).resolve()`,
so a flat "the module names neither token" clause is RED against the module this spec prescribes.
Scoping it by enclosing `FunctionDef` name, by line range, and by an allowed-occurrence count are
three readings with three different failure modes — an occurrence count is greenable by moving the
escape INTO `_temp_vault`, a line range rots on the first edit — and the build-runner would have to
pick one. Rule it in the fold, and state it on the same surfaces, so §7's authoring constraints and
Task 9's clause cannot disagree. Note also that M6 deliberately leaves `os` legal by name
(`WALL_C_MODULES` is `FS_MODULES - {"os"}`, `tests/test_name_gate_wall.py:1043`, which I confirmed)
precisely so `_temp_vault` may read `os.environ` — so M8 and M6 must be stated as one consistent
rule about that one function rather than as two clauses that happen not to collide.

Both folds land inside machinery the plan already ships — M7 is one member of a set Task 7 builds,
M8 rides the same `VaultArgScan` asserted inside Task 9's ONE existing check — so §6's FOUR
derivations, §7's five-plus-three check count, R4's "eight checks" and Task 16's expected direction
do not move, and I checked that neither fold touches `## Intent` or `## Acceptance Criteria`:
`ac_hash: 973d7a08f068` and all five per-criterion hashes stay valid, no criterion states the wall.

**2. Three surfaces assert a completeness that is now false at the code, and the worst of them is
the standing ruling later gates are instructed to route AGAINST rather than re-derive (WI-226).**
A ruling folded into one surface leaves the others describing the pre-ruling world, and here the
pre-ruling world is a claim that the level is CLOSED. All three must be corrected in the same edit
as the M7/M8 folds, not noted:

- `## Mitigation Folds`' upward-sweep paragraph, `:2348` ("the script's THREE mutating entry
  points") and `:2351-2353` ("M5 closes the whole in-process level, not `main` alone: the callee set
  is now the script's complete set of mutating entry points"), and its closing `:2361-2364` ("the
  level above THAT was swept and it is empty of omission shapes: with all three entry points and
  both process boundaries closed"). That is a completeness claim about a finite, checkable set and
  it is false by one member. The sweep's own stated discipline — record the correction rather than
  quietly replace the first result, which is how `:2308-2339` handled the round-2 miss — applies to
  this one too.
- Design §7's framing sentence at `:1517-1521`: "THREE routes to the live vault and therefore three
  parts, and the trio is what makes the guard total." Round 4's escape satisfies all three parts
  and mutates the live vault, so the trio is precisely what does NOT make the guard total. (The
  companion sentence at `:1596-1599` — "a guard missing any one of the three is satisfiable by a
  drive that mutates the live vault" — remains TRUE and needs no edit; it is the totality claim, not
  the necessity claim, that is falsified. Worth stating so the edit is surgical.)
- `## Scope Boundary:2655-2679`, the ruling my own round 3 recommended and the fifth pass landed.
  Its arc narration enumerates rounds 1–3 and calls the arc "four rounds long and monotone", and its
  operative sentence declares the wall "TOTAL over OMISSION shapes — a drive that reaches the live
  vault because somebody forgot to pass a path, forgot which entry point defaults to
  `OBSIDIAN_VAULT_PATH`, or reached the tool through a door nobody thought to watch". Two omission
  shapes were then found inside that declared-total region. This one is blocking for a reason the
  other two are not: the paragraph's last sentence instructs a later gate to CITE it and escalate
  rather than REVISE, so a ruling that overstates its own scope will make the next gate wave through
  exactly the class it names. The fix is not to retract the ruling — the instrument is right — but
  to restate the bound as what the mechanism will actually be after M7 and M8 land (omission shapes
  reachable through a DOOR the census enumerates, plus every omission route through any door, closed
  at the two SOURCE tokens), and to record round 4 in the arc rather than leaving the narration at
  three rounds.

### Non-blocking notes

1. **Design §6(d)'s scan-universe paragraph (`:1427-1435`) becomes an incomplete enumeration once
   M7 lands, and one clause fixes it.** It currently says that pointing `mutating_drive_vault_args`
   at `scripts/lint_vault.py` RAISES "at `run_lint`'s own `vault_path` parameter" and "at the
   `main()` call in the `__main__` guard at `:1316`". With `quarantine_garbage` in the callee set
   there is a third raise site — its own `vault_path` parameter at `:1113`, an `ast.arg` — and the
   `quarantine_garbage(garbage, vault_path)` call at `run_lint:1220` joins the collected set beside
   the `apply_fixes` call at `:1194`. The paragraph's CONCLUSION is unchanged and still correct
   (the scan's universe stays the new check module alone); only its list of reasons is short. Worth
   a clause so a later reader does not mistake the enumeration for a total, which is the exact
   reading habit this document has now been bitten by twice.

### What is NOT a gap — checked and clean

Stated so round 5, if there is one, does not re-walk them. Sixteen canonical `- [ ] **Task N — …**`
definitions with unique ordinals 1–16 (counted on this tree: 16), each carrying a well-formed
lowercase `verify:` declaration (counted: 16) — fourteen naming bare `test_` names, Task 1
`baseline` and Task 16 `hand-run`, both correct uses of the closed exception kinds — and no verify
command writes anything outside `write_authority` (WI-238). Every `landed: Task N` across all four
threat-model rounds — 2, 4, 9, 4, 7, 15, and round 4's **7 (M7)** and **9 (M8)** — resolves to a
defined ordinal, so no D8b refusal is latent; what refuses is D8c alone. `## Write Targets`
coverage is exact in both directions: each task's target file appears in the nine builder `writes`
fences, no fence names a path no task writes, the two `kind: precondition` paths are READ by AC-5
and appear in no builder fence, the driven doc is implicit, Tasks 1 and 16 write only the Build
Log — **and M7's and M8's fold work adds no target**, landing in `tests/derivations.py` and
`tests/test_lint_vault_fix_rules.py` respectively, both already declared, so the L3 level the
frontmatter carries is not under-declared. `OPEN: None`, zero open items. Check 11 is satisfied by
`## Verified Diagnosis`' four falsifiable claims, each of which I re-executed against the code this
round — VD-2's six decline sites and VD-4's "nothing under `tests/` calls `run_lint`" both still
hold. The five criteria remain signed and untouched, and AC-5 is still GREEN against the committed
baseline and census (821/835 delta `+14`, 315/315, 19/19, 0/0, 0/0). The WI-278 corpus-fixture arm
is chosen explicitly in AC-5(b)'s one-line coupling declaration. The WI-229 conscious-pin sweep is
discharged by the nine-site rename inventory across four modules.

**On the arc, stated because it is the judgement only this gate can make and because my round 3
flagged the regress signature.** This is my fourth round and the fourth on one family. My prior
three were monotone and each finding landed on the surface the previous fold added, which is why
round 3 stopped emitting single-site REVISEs and recommended the standing ruling instead — and that
ruling landed and is the right instrument. Round 4 is NOT that pattern repeating, and the
distinction is worth being precise about rather than pattern-matching: finding (b) is not a new rung
built on folded material, it is a fact about `scripts/lint_vault.py` that has been true since before
this item was minted — `apply_fixes` ignores its `vault_path` — and it means every rung so far
graded the wrong thing. M8 is the answer that ends the ladder rather than extending it, because it
closes at the two SOURCE tokens instead of enumerating a fifth door. So I am emitting this round
rather than escalating, and the threat modeler is right not to escalate either: both halves are
omission shapes, not deliberate acts, so `## Scope Boundary`'s escalation clause does not fire.
**The escalation trigger I would name for whoever holds round 5:** if a fifth threat-model round
opens a NINTH mitigation on this family after M7 and M8 land as written, that is the sufficiency
ruling Dave or the conductor owns, and the next gate should stop and ask rather than emit a fifth
REVISE.

### Carried-forward notes

Every still-open non-blocking note from every prior round, by name:

- **Threat model round 1 note 1 / round 2 note 3 / round 3 note 3 / round 4 note 5 (the exit
  attestation's redaction reminder is absent from `docs/lint-vault-live-baseline.md` §4's own
  bytes)** — STILL OPEN, re-deferred for the sixth time for the same correct reason: §4 is
  conductor-owned and outside the builder's write authority, so it has no Implementation-Plan task
  to land in and a fence pointing at one would be a fiction. The conductor's, at the ship door.
- **Threat model round 1 note 2 / round 2 note 4 / round 3 note 4 / round 4 note 6
  (`apply_fixes:994` prints `str(exc)` to stderr)** — STILL OPEN as a deliberate non-change.
  Re-verified at the code this round: the print is still `f"  Fix error on {fpath.name}: {exc}"` at
  `:994`, the handler set does not widen, and it is pinned as a message equality at
  `tests/test_lint_vault_fix_gate.py:123-125`.
- **Threat model round 2 note 1 / round 4 note 7 (M3's wall universe is ONE module)** — a standing
  scope ruling, not an open note; routed against rather than re-litigated. M7 and M8 do not widen it
  either — both are clauses over the same single module.
- **Threat model round 4 note 1 (M8 must not be implemented by widening the graded identifier set,
  because `read_vault(tmp)` would pull `tmp` into `bindings` and `with temp_dir() as tmp` RAISES
  there)** — NEW and OPEN, and it is a real constraint on the M8 fold rather than a preference; it
  belongs in the fold's own text beside my blocking-1 scoping requirement, since both are about how
  the clause is mechanised.
- **Threat model round 4 note 2 (`tests/ac_interpreter.py`'s `os.execve:155` is not a route past
  M6)** — CLOSED on arrival; recorded so no later round re-derives it as a finding.
- **Data audit round 2's two carried items** — both STILL OPEN and both correctly outside the spec:
  the build-start re-grounding should re-run AC-5(b)'s five-row comparison before the first edit
  (the baseline is five days old and the vault churns weekly — still GREEN against HEAD this round,
  which is a snapshot fact and not a standing one), and the exit half of A7's bracket has no battery
  wall by construction and lives at the conductor's ship door.
- **My round-1 notes 1–5, my round-2 notes 1–3, my round-3 notes 1–2** — all CLOSED. Round-3 note 1
  (the M3 re-sweep paragraph's alias/wrapper overclaim) by the in-place correction at `:2325-2336`,
  which I re-read and which now states the residue correctly; round-3 note 2 (check definition
  order) by Task 9's "DEFINE … FIRST" clause at `:2016-2021` with the courtesy/guarantee distinction
  stated.
- **Threat model round 3 notes 1–2 and architect round 4 notes 1–4 and the AC red-team's label
  slip** — all CLOSED, recorded in my prior sections.

```verdict
gate: spec-reviewer
verdict: REVISE
date: 2026-09-15
model: claude-opus-5
targets: M7, M8, Task 7, Task 9, #design, #mitigation-folds, #scope-boundary, #verification
prior: held
basis: folded-material
findings: 2/3
note: Round 3's two blockers closed and stayed closed — M5 and M6 are landed on every surface I enumerated last round and their fold records at `:2407-2421` carry `desc` values byte-identical to the round-3 fences, the M3 re-sweep overclaim is corrected in place at `:2325-2336`, Task 9 defines the containment check FIRST at `:2016-2021`, and the `## Scope Boundary` ruling I recommended landed at `:2655-2679`. What blocks is `## Threat Model — 2026-09-15 (round 4)` (`:4864`), which emits EIGHT `kind: required` fences and is therefore the latest SPEAKING round, while `## Mitigation Folds` carries six and declares itself restated against round 3 (`:2274-2276`) — so M7 (`landed: Task 7`) and M8 (`landed: Task 9`) have no record and D8c refuses `specced -> ready`, and the substance of both is on zero surfaces. I verified both premises at the code rather than at the fence: `quarantine_garbage:1112-1144` is a FOURTH mutating entry point outside §6(d)'s three-member callee set at `:1402` — the script's only `vault_io` mutation sites are `write_note:957`/`:975` in `apply_fixes` and `ensure_dir:1134`/`move_note:1140` in it — and its vault argument is the SECOND positional at `:1113`, identical in position to `apply_fixes`' at `:827`, so the position rule grades it with no new text (M7); and `grep vault_path scripts/lint_vault.py` returns `:827` as that parameter's ONLY occurrence in `apply_fixes`, whose write targets are `issue.file_path` (`:835`, `:853`, `:957`, `:975`), so the wall grades an argument that provably does not determine what gets written and the four-line escape passes all three clauses of Design §7 with the runtime door executed and the import wall clean while rewriting the live vault — worse under `quarantine_garbage`, where `vault_path` is only the destination root (`:1116`) and the moved sources are `issue.file_path` (`:1121`), making it a data-LOSS shape (M8). The M8 fold owes one thing its `desc` does not state and the builder must not have to invent: the MECHANISM of the `_temp_vault` exemption, since Design §7 (`:1523-1534`) and Task 9 (`:1988-1998`) both ORDER that function to name `lint_vault.DEFAULT_VAULT` and `os.environ.get("OBSIDIAN_VAULT_PATH", "")`, so a flat token clause is RED against the module this spec prescribes and by-function / by-line-range / by-occurrence-count are three readings with three different failure modes. Blocking issue 2 is the WI-226 sweep the folds owe: three surfaces assert a completeness round 4 falsified — the folds' upward sweep at `:2348` and `:2351-2353` and `:2361-2364` ("the script's complete set of mutating entry points", "empty of omission shapes"), Design §7's "the trio is what makes the guard total" at `:1517-1521` (its necessity companion at `:1596-1599` stays true and needs no edit), and most importantly `## Scope Boundary:2655-2679`, whose "TOTAL over OMISSION shapes" bound is the standing ruling a later gate is instructed to cite and route against, so an overstated scope there will wave through exactly the class it names. Both folds land inside shipped machinery — M7 is one set member in Task 7, M8 rides the same `VaultArgScan` inside Task 9's ONE existing check — so §6's four derivations, §7's five-plus-three check count, R4's "eight checks" and Task 16's direction do not move, and neither touches `## Intent` or `## Acceptance Criteria`, so `ac_hash: 973d7a08f068` and all five per-criterion hashes stay valid. On the arc: I flagged the regress signature last round and the ruling it asked for landed, and round 4 is NOT that pattern repeating — finding (b) is a fact about the script that predates this item and means every prior rung graded the wrong thing, and M8 closes at the two SOURCE tokens rather than enumerating a fifth door, so it is the fold that ends the family rather than extends it. If a FIFTH threat-model round opens a ninth mitigation on this family after M7 and M8 land as written, that is the sufficiency ruling Dave or the conductor owns and the next gate should escalate rather than emit a fifth REVISE. Everything else re-verifies clean: sixteen canonical tasks each with a well-formed `verify:`, every `landed: Task N` resolving, Write-Targets coverage exact both ways with M7/M8 adding no target, the drift audit's one finding archival only (the live cite at `:1514` already reads `:278`, confirmed at `tests/test_vault_path_required.py:278`, with `:320` correctly named as the universe line), and AC-5 still GREEN against the committed baseline and census (821/835 delta `+14`, 315/315, 19/19, 0/0, 0/0).
```

## Threat Model — 2026-09-16 (round 5)

**Recommendation: PROMOTE to threat-modeled**

Fifth round, cold-start. The carry-forward is this document's four prior threat-model rounds and the
four spec-review rounds answering them: round 1 opened M1–M4; round 2 tightened M3 to provenance;
round 3 opened M5 (the CLI entry point) and M6 (the process boundary); round 4 opened M7 (the callee
set is short by `quarantine_garbage`) and M8 (the wall grades an argument `apply_fixes` never reads,
so close at the SOURCE instead). Spec-review round 4 REVISEd on M7/M8 having no fold record and on
three surfaces asserting a completeness round 4 had falsified, and recorded a sufficiency trigger.
The sixth spec-writer pass has since landed all of it. Every citation below was re-resolved by
opening the code, never taken from the fold's account of itself or from a prior gate's paraphrase.

### Trigger check

The same four triggers fire, unchanged: filesystem operations on user-owned files (`apply_fixes:957`,
`:975`, `quarantine_garbage:1134`, `:1140`), untrusted input (vault bytes), persistence (a
floor-resident module driving the MUTATING entry point of a tool whose default target is Dave's live
vault), and an information-disclosure surface (the operator-facing summary against
`obsidian_schemas/errors.py`'s bounded-projection contract). The sixth pass retired none of them.

### The re-fold, verified against the code rather than against the fold record

- **M1, M2, M4 — records intact, substance undisturbed.** Re-checked on their own surfaces; all three
  `desc` values in `## Mitigation Folds` (`:2736`, `:2744`, `:2760`) are byte-identical to my round-4
  fences. M4 re-confirmed against the FRAME rather than the prose: `scripts/lint_vault.py:949`
  (`fixed += file_fixed`) still sits above the `if changed:` at `:951` and the first `write_note` at
  `:957`, and the wikilink write at `:975` is inside the `with` block but outside `if changed:`, so
  per-write crediting remains the only placement yielding AC-4(b)'s signed answer. Re-emitted unchanged.
- **M3, M5, M6 — records fresh** (`:2752`, `:2768`, `:2776` byte-identical) and their surfaces
  undisturbed. Premises re-read independently this round rather than carried: `FS_MODULES` at
  `tests/derivations.py:68` is `{"os", "shutil", "tempfile", "fcntl", "filelock", "mmap"}`,
  `OS_READONLY_NAMES:69` holds only `environ`/`getenv`/`sep`/`path`/`fspath`/`getcwd`,
  `tests/test_name_gate_wall.py:1043` is `WALL_C_MODULES = frozenset(FS_MODULES - {"os"})` — neither
  set reaches `subprocess` or `runpy` — `module_import_uses` is at `:847` and
  `os_module_attribute_uses` at `:800`, and `main:1252` takes no parameters with `--vault` carrying
  `default=DEFAULT_VAULT` at `:1255`.
- **M7 — landed, and its completeness claim is TRUE, which I settled by census rather than by
  reading it.** A grep for `vault_io.` over the whole script returns exactly seven sites:
  `note_lock:858`, `read_note:859`, `write_note:957`, `read_note:961`, `write_note:975`,
  `ensure_dir:1134`, `move_note:1140`. Three are non-mutating; the four mutating ones sit in
  `apply_fixes` and `quarantine_garbage:1112-1144`, so the functions reaching them are those two plus
  `run_lint` (calling both at `:1194` and `:1220`) and `main`. FOUR, and there is no fifth.
  `quarantine_garbage`'s vault argument is the SECOND positional at `:1113` exactly as `apply_fixes`'
  is at `:827`, `quarantine_dir = vault_path / "_quarantine"` is at `:1116` and the moved sources are
  `src = issue.file_path` at `:1121` — so the position rule grades it with no new text and the
  data-LOSS shape round 4 described is real. Landed in §6(d) (`:1497-1526`), §7's syntax half
  (`:1764-1767`), Task 7 (`:2195-2196`), the §6(d) scan-universe clause (`:1545-1548`) and the
  THIRTEENTH mutation (`:3000-3010`), with the mutation deliberately written as
  `quarantine_garbage(issues, tmp)` so it discriminates the callee set and not M8 — which is the right
  choice and is recorded as such at `:3001-3003`. `desc` at `:2784` is byte-identical. Re-emitted.
- **M8 — landed on all of its surfaces.** §6(d)'s third census (`:1589-1648`), §7's fourth part
  (`:1815-1836`), Task 9's clause (iv), the by-function exemption RULED rather than left to the builder
  (`:1627-1637`, answering spec-review round 4's blocking-1 rider), the `read_vault`-widening
  shortcut refused with its reason (`:1650-1654`, answering my round-4 note 1), the M6/M8
  one-rule-two-levels paragraph (`:1661-1668`), and the FOURTEENTH mutation (`:3011-3018`). `desc` at
  `:2792` is byte-identical. Its core premise re-verified: `grep vault_path scripts/lint_vault.py`
  returns `:827` as that parameter's ONLY occurrence in `apply_fixes`, the next hit being
  `print_summary:1013`, so the argument really is inert and the write targets really are
  `issue.file_path`. Re-emitted unchanged — see the FIDELITY note below.
- **Spec-review round 4's blocking issue 2 is discharged on all three surfaces.** The folds' upward
  sweep now records the correction in place rather than replacing it (`:2675-2709`), §7's framing
  sentence reads "FOUR parts" with the falsified "trio … total" wording quoted and dated
  (`:1724-1727`) while its necessity companion at `:1843-1844` is correctly left standing, and
  `## Scope Boundary:3103-3146` restates the bound and records the arc at five rounds.

### STRIDE review — scoped to what the sixth pass added

**Spoofing, Tampering, Repudiation, Information disclosure, Denial of service — nothing new.** The
sixth pass adds one `ast` census over the check module's own text and one set member; no branch's
repair logic, no `delta` key, no gate call and no `write_note` argument moves, and WI-004's
concurrency contract is untouched. `live_path_names` returns `(module_id, lineno, token, enclosing)`
— four values that cannot reach a vault path or a note filename, so the bounded-projection contract
holds. No network, no retry, no recursion.

**Elevation of privilege — one finding, and it is on `## Scope Boundary`'s load-bearing premise
rather than on a mechanism.** The restated ruling makes the wall's totality rest on one sentence
(`:3122-3124`): *"because a drive can only reach the live vault by NAMING it, and clause (iv) (M8)
leaves the module no place outside `_temp_vault`'s own body to name it."* That is the whole reason the
sixth pass could demote the door census and the import wall to "belt-and-braces over the routes, not
the load-bearing half" (`:3124-3125`), and the reason §6(d) can say the live path "has exactly TWO
sources in this module's universe" (`:1612-1613`). It is a completeness claim about a specific,
finite, checkable set, so I checked it instead of reading it. **There is a third source, it is in the
library this module tests, and the module names nothing when it uses it.**

`obsidian_schemas/repositories/base.py:_resolve_vault_path:104-114` resolves a repository's vault as
`for candidate in (vault_path, os.environ.get(ENV_VAULT_PATH))` and raises only when BOTH are
unconfigured, where `ENV_VAULT_PATH = "OBSIDIAN_VAULT_PATH"` at `:75` and `_is_unconfigured:86-101`
counts `None`, blank, whitespace-only and `Path(".")` as unconfigured. `BaseRepository.__init__:154`
calls it, so every concrete repository — `PersonRepository`, `CompanyRepository`, `BookRepository`,
`MeetingRepository`, all four exported from `obsidian_schemas/__init__.py:73-79` — carries it. The
env read happens INSIDE the library, so the escape names none of clause (iv)'s three token shapes:

      vault  = _temp_vault(tmp)                                  # provenance "_temp_vault"  ✓
      repo   = PersonRepository()                                # no DEFAULT_VAULT, no "OBSIDIAN_VAULT_PATH",
                                                                 # no os.environ / os.getenv  → clause (iv) GREEN
      issues = lint_vault.check_noise(lint_vault.read_vault(repo.vault_path), idx)
      lint_vault.apply_fixes(issues, vault)                      # drives: identifier `vault`  ✓

Clause (i) spelling green, (ii) non-vacuity green, (iii) provenance green, **(iv) source green**, the
runtime door EXECUTED, the import wall clean (`obsidian_schemas` is in neither `WALL_C_MODULES` nor
`{"subprocess", "runpy"}`), `os_module_attribute_uses` clean (no `os.<attr>` appears),
`FORBIDDEN_DEFAULT_PATTERNS` clean (no `expanduser`, no `Path.home()`, no `/Users/`) — and Dave's
live notes are rewritten. Under `quarantine_garbage` the same shape is the rename.

**Four things make this an OMISSION shape rather than the deliberate-disguise residue, which is what
decides whether `## Scope Boundary` already covers it.** (1) A no-argument repository construction is
the library's own documented convenience form, not a disguise — it is literally the first clause of
the ruling's declared-total region, "somebody forgot to pass a path". (2) This tree has already been
bitten by the identical generator and guarded it twice under `tests/`:
`tests/identity_fixture.py:seed_vault:85-100` plants a hard refusal whose docstring states the reason
in terms — "`base.py:_resolve_vault_path` takes the explicit argument OR `OBSIDIAN_VAULT_PATH` and
raises only when BOTH are unconfigured, that variable IS set on the machine this fixture is authored
on, and the standing wall that forbids caller-independent defaults never reaches `tests/`. A seeder
handed a swallowed `dest` writes ten notes into the live vault" — and `tests/record_identity_golden.py:28,89`
records it again. (3) The repo has a NAMED pattern for the antipattern,
`tests/test_vault_path_required.py:NO_ARG_CONSTRUCTION:382` = `r"\w+Repository\(\s*\)"`, but
`test_docs_do_not_advertise_no_arg_construction:436-460` runs it over MARKDOWN only and
`DOC_SCAN_EXCLUDED:387` excludes `docs`, while `test_no_implicit_vault_path_defaults:312-331` stops
its universe at `("obsidian_schemas", "scripts")` (`:320`) — so no standing wall reaches a `.py` file
under `tests/`, which is exactly the blind spot §7 already cites for `FORBIDDEN_DEFAULT_PATTERNS`.
(4) The asymmetry is the dangerous way round: §7's runtime half is correct that `OBSIDIAN_VAULT_PATH`
is UNSET in the graded and CI environments, where `_resolve_vault_path` raises
`VaultPathNotConfiguredError` and the escape is safe — but the floor command in `CLAUDE.md` is run BY
HAND on Dave's machine, where `docs/lint-vault-live-baseline.md:10-11` records `$VAULT` as "exported
in the shell". A check module that is green in the cage and rewrites the live vault on the author's
laptop is the worst available failure mode, and it is the one this document has spent five rounds
building a wall against.

**What is and is not owed, stated as two separate things because they have two different owners.**
The finding has a factual half and a mechanism half, and conflating them is what would make this
round a treadmill rung:

**(a) The premise correction, and it is owed regardless of how the sufficiency call goes.** "A drive
can only reach the live vault by NAMING it" is false, and so is "exactly TWO sources in this module's
universe … closed by construction" (`:1612-1613`), and so is §7's "no omission-shaped escape can
reach it through any door" (`:1835-1836`). The third source exists whether or not anyone chooses to
close it. This is not a mechanism question and it is not chasing the family: `## Scope Boundary`'s
last operative sentences instruct a later gate to CITE the paragraph and escalate rather than REVISE
(`:3141-3142`), so a bound whose stated reason is false will make the next gate wave through exactly
the class it names — which is the harm spec-review round 4 identified when it made the same call its
own blocking issue 2. If the sufficiency ruling in (b) comes back "stop", this correction becomes MORE
owed, not less, because the bound is then the only thing standing between a future gate and this
class. This is a document-truthfulness sweep (WI-226) and it sits in the spec-reviewer's lane, not
behind a `mitigation` fence, which is why I am not carrying one for it.

**(b) The mechanism is a SUFFICIENCY call, and this document assigns it to Dave or the conductor — so
I am routing it there rather than forcing it, and I am emitting EIGHT fences and not nine.**
`## Scope Boundary:3143-3146` records the trigger in the document's own bytes rather than leaving it
to a gate's memory: "a FIFTH threat-model round opening a NINTH `kind: required` mitigation on this
family after M7 and M8 land as written is the signal that the family's cost has outrun its value, and
the gate holding that round should stop and ask Dave or the conductor rather than emit another
REVISE." I am the fifth round, this would be the ninth, M7 and M8 landed as written. The trigger
fires exactly as specified, and the instrument exists precisely so that this decision is made once,
explicitly, by its owner — so I take it at its word. A ninth fence would be me making the sufficiency
call unilaterally through D8, which is the one thing the paragraph was written to prevent.

**What the ruling-holder needs, so the decision is cheap to make.** My own read, offered as input and
not as the ruling: this is a REAL route but a materially less likely one than M8's, and I would
probably close it anyway because it is nearly free. Less likely, because `scripts/lint_vault.py`
names no repository anywhere (grep: zero occurrences of `Repository`), so the check module has no
motive to construct one, and all twenty-odd repository constructions under `tests/` pass an explicit
vault (`tests/test_resolve_or_create.py`, `tests/test_wi126_body_preservation.py`,
`tests/test_loud_fail_write.py:44`) — the no-arg spelling is against the tree's uniform idiom. Nearly
free, because the closure is one more CLOSED shape in a census Task 7 already builds: a call whose
callee resolves (Name `id` or Attribute `attr`, the same resolution rule `drives` and `bindings`
already use) to an identifier ending `Repository`, recorded as `(module_id, lineno, token, enclosing)`
like the other three — whereupon Task 9's existing clause (iv) grades it with NO new text, no new
check, no fifth derivation, and none of the counts this document has re-synced twice. That is the same
no-new-rule economy M7 got. Note also that the requirement is ZERO repository constructions in the
module and not "no no-arg construction": `_is_unconfigured:86-101` swallows blank, whitespace-only and
`"."` too, so a spelling-shaped rule (including `NO_ARG_CONSTRUCTION`'s regex, which sees only the
literal `Repository()`) is a partial closure, and the module needs no repository at all.

**And one shortcut the fold must NOT take if the ruling is "close it", recorded now so it is not
rediscovered.** The tempting move is to make §7's prose list of legitimate imports (`:1811-1814`,
Task 9's `:2755`) an ENFORCED allowlist instead of adding a use-site shape. It cannot work at this
granularity: `module_import_uses:847-870` reports the ROOT module name, so
`from obsidian_schemas.repositories.base import SKIP_REASONS` — which M1's verify needs, since the
module is forbidden to hand-type a `SKIP_REASONS` member — and `from obsidian_schemas import
PersonRepository` are indistinguishable to it, both reporting `obsidian_schemas`. The use-site level
is the only one that separates them, which is the same argument the M6/M8 one-rule-two-levels
paragraph at `:1661-1668` already makes. A global `os.environ` scrub at module import is the other
tempting shape and is worse: it is unscoped shared state across a pytest process in which
`tests/test_identity_endgame.py:330` and `tests/test_vault_path_required.py:84` both manipulate that
same variable, and I have no shell in this gate and therefore cannot verify a floor run — so I am not
prescribing it.

**On the arc, since it is the judgement only this gate can make.** This is the fifth round and the
fifth on one family, and I want to be precise rather than pattern-match. Each prior round's finding
landed on material the previous fold added; this one does not — `_resolve_vault_path`'s env fallback
has been in the library since WI-024 and is older than this item. But the SHAPE is now unmistakable
and is the reusable finding for the fourth time: every round has ended by declaring a level closed by
construction, and every following round has found the enumeration inside the construction. M8's token
list is a three-member enumeration wearing the word "sources". That is exactly why the sufficiency
instrument exists and why I am using it instead of adding a rung: the question is no longer "is there
another route" (there will usually be one) but "is this wall good enough", and only Dave or the
conductor can answer that. What I can say is that the wall as specced is sound for what it watches,
every one of its eight mitigations is landed on every surface its generator named, and nothing here
makes the approach unsafe — hence PROMOTE.

### Mitigations required

1. **M1 — the read-error value is a vocabulary member, never the decode exception.** Folded into
   Design §1 and Task 2; re-verified. Re-emitted unchanged.
2. **M2 — both new records carry bounded values.** Folded into Design §3 and Task 4; re-verified.
   Re-emitted unchanged.
3. **M3 — the containment wall, with the syntax half asserting provenance.** Folded on all six
   surfaces; record fresh; re-emitted unchanged.
4. **M4 — an issue whose write committed is never re-labelled `errored`.** Re-verified against the
   frame at `:949`/`:951`/`:957`/`:975`. Re-emitted unchanged.
5. **M5 — the CLI entry point is inside the wall's callee set.** Premises re-read at `:1252`, `:1255`.
   Re-emitted unchanged.
6. **M6 — the module cannot reach the CLI by subprocess either.** Every premise re-read off
   `tests/derivations.py:68-69` and `tests/test_name_gate_wall.py:1043`. Re-emitted unchanged.
7. **M7 — the callee set is the script's COMPLETE set of mutating entry points, and that is four.**
   Landed on all five surfaces; the completeness claim independently settled by the seven-site
   `vault_io.` census. Re-emitted unchanged.
8. **M8 — the live vault path cannot be NAMED in the module at all.** Landed on all six surfaces with
   the exemption's mechanism ruled and both round-4 shortcuts refused by name. Re-emitted unchanged.

**FIDELITY, stated explicitly because M8's `desc` contains a clause this round falsified.** Its last
clause reads "a clause over the path's two SOURCES is total over every omission route through every
door, which a callee enumeration cannot be" — and that rationale is now known to be overstated. I am
re-emitting `desc` BYTE-IDENTICALLY anyway, because what M8 REQUIRES has not moved one character: the
module must still name the live vault path nowhere outside `_temp_vault`'s body, and that requirement
is as necessary today as it was yesterday. Re-wording a rationale would re-stale a fresh record and
spend a producer-fix round on a requirement that did not move, which is the exact failure the rule
names. The overstatement belongs in `## Scope Boundary`'s prose and in §6(d)'s and §7's, where
finding (a) puts it — not in a machine-compared anchor.

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

1. **The finding above is the one thing in this round that is not already settled, and it is recorded
   as TWO items on purpose.** Half (a) — the false premise on three surfaces — is a WI-226
   truthfulness sweep and the spec-reviewer's to make blocking if it agrees; half (b) — the ninth
   mechanism — is the sufficiency ruling `## Scope Boundary:3143-3146` assigns to Dave or the
   conductor, and I have not forced it with a fence. A gate reading only the verdict line should not
   collapse the two: the trigger covers (b), never (a).
2. **The THIRTEENTH mutation's choice of `tmp` over `lint_vault.DEFAULT_VAULT` is right and I checked
   it rather than assumed it** (`:3000-3010`). Passing the live constant would have made the mutation
   RED under clause (iv) even with a three-member callee set, so it would have discriminated M8 and
   not M7. The spec-writer's note recording that it was "deliberately re-chosen while writing it"
   (`:1040-1042`) is accurate.
3. **`tests/derivations.py:SCRIPTS_ROOT` is at `:33`, not `:31`.** The stale cite sits only in the
   2026-09-10 currency audit (`:77`), which is archival ideation text rather than a live design
   surface; §6's and Task 9's live uses name the symbol without a line. Recorded so no later round
   re-derives it as drift.
4. **Round 1 note 1 / round 2 note 3 / round 3 note 3 / round 4 note 5 (the exit attestation's
   redaction reminder is absent from `docs/lint-vault-live-baseline.md` §4's own bytes) — STILL
   OPEN**, re-deferred a seventh time for the same correct reason: §4 is conductor-owned and outside
   the builder's write authority, so it has no Implementation-Plan task to land in and a fence
   pointing at one would be a fiction. The conductor's, at the ship door. Re-read `:1-16` this round
   and confirmed the artifact's own privacy wall is stated at `:6-8`.
5. **Round 1 note 2 / round 2 note 4 / round 3 note 4 / round 4 note 6 (`apply_fixes:994` prints
   `str(exc)` to stderr) — STILL OPEN as a deliberate non-change.** The handler set does not widen,
   so no new content reaches that channel, and it is pinned as a message equality at
   `tests/test_lint_vault_fix_gate.py:123-125`.
6. **Round 2 note 1 / round 4 note 7 (M3's wall universe is ONE module) stands as a scope ruling** and
   is routed against rather than re-litigated. Nothing this round widens it.
7. **Round 4 notes 1 and 2 are both CLOSED.** Note 1 (M8 must not be implemented by widening the
   graded identifier set, because `read_vault(tmp)` pulls `tmp` into `bindings` where
   `with temp_dir() as tmp` RAISES) is folded verbatim into §6(d) at `:1650-1654` and into Task 9.
   Note 2 (`tests/ac_interpreter.py`'s `os.execve` is not a route past M6) was closed on arrival.
8. **Round 3 notes 1–2 are CLOSED** and were re-confirmed on their surfaces: the M3 re-sweep's
   alias/wrapper overclaim is corrected in place at `:2638-2652`, and Task 9 defines the containment
   check FIRST with the courtesy/guarantee distinction stated.

```verdict
gate: threat-modeler
verdict: PROMOTE
date: 2026-09-16
model: claude-opus-5
note: The sixth pass landed M7 and M8 in full and I verified both at the code rather than at the fold record — M7's completeness claim settled by census (a `vault_io.` grep over the script returns exactly seven sites, `note_lock:858`/`read_note:859`/`write_note:957`/`read_note:961`/`write_note:975`/`ensure_dir:1134`/`move_note:1140`, so the four mutating ones give FOUR entry points and no fifth), `quarantine_garbage`'s vault argument confirmed the SECOND positional at `:1113` with `quarantine_dir` at `:1116` and moved sources `src = issue.file_path` at `:1121`, and M8's premise confirmed by `grep vault_path scripts/lint_vault.py` returning `:827` as that parameter's only occurrence in `apply_fixes`. All eight `desc` values in `## Mitigation Folds` are byte-identical to my round-4 fences, the exemption's mechanism is RULED by enclosing-FunctionDef at `:1627-1637`, both round-4 shortcuts are refused by name at `:1650-1654` and `:1661-1668`, the thirteenth and fourteenth mutations landed, and spec-review round 4's blocking issue 2 is discharged on all three surfaces. Re-emitting all eight unchanged. The finding is on the restated ruling's LOAD-BEARING PREMISE, not on a mechanism: `## Scope Boundary:3122-3124` rests the wall's totality on "a drive can only reach the live vault by NAMING it", and §6(d):1612-1613 on "exactly TWO sources in this module's universe" — both false by one, because `obsidian_schemas/repositories/base.py:_resolve_vault_path:104-114` falls back to `os.environ.get(ENV_VAULT_PATH)` INSIDE the library (`ENV_VAULT_PATH = "OBSIDIAN_VAULT_PATH"` at `:75`, `_is_unconfigured:86-101` swallowing None/blank/"." too, `BaseRepository.__init__:154` calling it for all four repositories exported at `obsidian_schemas/__init__.py:73-79`), so `repo = PersonRepository()` beside `read_vault(repo.vault_path)` passes clause (iv) and clauses (i)-(iii) with the runtime door executed, the import wall clean (`obsidian_schemas` is in neither `WALL_C_MODULES` nor `{subprocess, runpy}`) and `FORBIDDEN_DEFAULT_PATTERNS` clean — and rewrites the live vault. It is an OMISSION shape inside the region the ruling declares total, not deliberate-act residue: the no-arg form is the library's documented convenience form, this tree has guarded the identical generator twice under `tests/` (`identity_fixture.py:seed_vault:85-100`, whose docstring names `_resolve_vault_path` and the `tests/` blind spot in terms, and `record_identity_golden.py:28,89`), the repo's own `NO_ARG_CONSTRUCTION` regex at `tests/test_vault_path_required.py:382` runs over MARKDOWN only with `DOC_SCAN_EXCLUDED` excluding `docs`, and the env var is UNSET in the cage but exported on Dave's machine (`docs/lint-vault-live-baseline.md:10-11`) where `CLAUDE.md`'s floor command is hand-run — green in the graded environment, live-vault write on the author's laptop. TWO OWNERS, deliberately not conflated: (a) the premise correction on `## Scope Boundary`, §6(d) and §7's `:1835-1836` is owed regardless and is a WI-226 truthfulness sweep in the spec-reviewer's lane, and it matters MORE if (b) is declined, because `:3141-3142` instructs later gates to cite that paragraph and escalate rather than REVISE, so a bound with a false stated reason will wave through exactly the class it names; (b) the ninth mechanism is the SUFFICIENCY call that `## Scope Boundary:3143-3146` assigns to Dave or the conductor in the document's own bytes, naming precisely this situation — a fifth threat-model round, a ninth mitigation, M7 and M8 landed as written — so I take the instrument at its word, emit EIGHT fences and route (b) there rather than making that call unilaterally through D8. For the ruling-holder: it is a real route but materially less likely than M8's (the script names no repository at all and every `tests/` construction passes an explicit vault), and if closed it costs one more CLOSED shape in the census Task 7 already builds — a callee resolving to a name ending `Repository`, graded by Task 9's existing clause (iv) with no new text, no new check and no count moves — with the requirement being ZERO constructions rather than "no no-arg construction", since `_is_unconfigured` swallows blank and `"."`; the import-allowlist shortcut cannot work (`module_import_uses` reports the ROOT module, so `obsidian_schemas.repositories.base` for `SKIP_REASONS` and `obsidian_schemas` for `PersonRepository` are indistinguishable) and I am not prescribing a global `os.environ` scrub, which is unscoped shared state in a process where two other modules manipulate that variable and which I have no shell to verify. M8's `desc` is re-emitted byte-identically despite carrying the falsified "total over every omission route" rationale, because what it REQUIRES has not moved and re-wording a rationale would re-stale a fresh record under the FIDELITY rule.
```

## Spec Review — 2026-09-16 (round 5)

**Recommendation: REVISE — return to spec writer (gaps to fix)**

Cold-start re-read from line 1, full document. Every citation below was resolved by opening the
file and reading the lines — never from the injected drift audit, never from a fold record's
account of itself, and never from threat-model round 5's paraphrase, including the code claims
that carry this round's blocking finding.

Rulings on record: A3/A3b (the YAML-reformat family, argued out on solve-in-one-place grounds), threat-model round 2 note 1 (M3's wall universe is ONE module), and `## Scope Boundary`'s containment-family closure with its deliberate-act/omission-shape distinction — I route against all three; this round's blocking issue is not a re-litigation of the third but the WI-226 correction to false premises INSIDE it, which is the same lane my round 4 used for its blocking issue 2.

### Citation verification

All live symbol-anchored citations resolve AND mean what the spec claims. Re-read at the code this
round rather than carried forward:

- `obsidian_schemas/repositories/base.py:_resolve_vault_path:104-114` — `for candidate in
  (vault_path, os.environ.get(ENV_VAULT_PATH))`, raising only when both are unconfigured;
  `ENV_VAULT_PATH = "OBSIDIAN_VAULT_PATH"` at `:75`; `_is_unconfigured:86-101` returning True for
  `None`, blank, whitespace-only and `Path(".")`; `BaseRepository.__init__:154` calling it;
  `PersonRepository` / `CompanyRepository` / `BookRepository` / `MeetingRepository` exported at
  `obsidian_schemas/__init__.py:74-77`. All confirmed.
- The `vault_io.` census over `scripts/lint_vault.py` — exactly seven sites, `note_lock:858`,
  `read_note:859`, `write_note:957`, `read_note:961`, `write_note:975`, `ensure_dir:1134`,
  `move_note:1140`. M7's completeness claim is TRUE and I settled it the same way round 5 did,
  independently. `DEFAULT_VAULT:56` is `os.environ.get("OBSIDIAN_VAULT_PATH", "")`;
  `apply_fixes:827`; `quarantine_garbage:1112`; `run_lint:1147`; `main:1252`.
- `tests/derivations.py` — `PACKAGE_ROOT:31`, `TESTS_ROOT:32`, `SCRIPTS_ROOT:33`, `FS_MODULES:68`
  `= frozenset({"os","shutil","tempfile","fcntl","filelock","mmap"})`, `OS_READONLY_NAMES:69`,
  `os_module_attribute_uses:800`, `module_import_uses:847`, `skip_reason_return_values:1528`,
  `skip_reason_literal_sites:1585`. `tests/test_name_gate_wall.py:WALL_C_MODULES:1043` is
  `frozenset(FS_MODULES - {"os"})`. Neither set reaches `subprocess` or `runpy`; M6's premise holds.
- `tests/test_fixture_vault.py:508-509` and `:1302` are still unwidened
  (`python_files_under(PACKAGE_ROOT, TESTS_ROOT)`) with both expected sets at exactly two members
  (`:510-514`, `:1315-1318`) and the `ast` single-home wall sharing the `:1302` local at
  `:1309-1312`. Task 8 describes a real pending edit, and its "expected sets stay at two" clause is
  the one that is true of `skip_reason_literal_sites`' predicate.
- `tests/test_vault_path_required.py:FORBIDDEN_DEFAULT_PATTERNS:278` = `["expanduser",
  "Path.home()", "/Users/"]`, with the universe `("obsidian_schemas", "scripts")` at `:320`;
  `NO_ARG_CONSTRUCTION:382` = `r"\w+Repository\(\s*\)"` with `DOC_SCAN_EXCLUDED:387` excluding
  `docs` and its only runner scanning MARKDOWN. `tests/identity_fixture.py:seed_vault:85-100`
  carries the refusal whose docstring names `_resolve_vault_path` and the `tests/` blind spot in
  terms. All confirmed.

**The injected drift audit's one finding is archival, re-confirmed rather than carried.**
`tests/test_vault_path_required.py:FORBIDDEN_DEFAULT_PATTERNS:320` occurs only inside my own
round-2 section's archived finding text; the LIVE cite at `:1656` already reads `:278`, which
matches the file, and `:320` is correctly named separately at `:1659` as the universe line. No
re-anchoring is owed.

### Blocking issues

**1. The WI-226 truthfulness sweep threat-model round 5 handed to this lane is owed — and its
surface list is SEVEN, not the three that round named.** The finding's factual half I verified
myself at the code rather than accepting: `_resolve_vault_path` falls back to
`os.environ.get("OBSIDIAN_VAULT_PATH")` INSIDE the library, every repository carries it through
`BaseRepository.__init__:154`, and the new check module is REQUIRED to import from
`obsidian_schemas` (M1's verify reads `SKIP_REASONS` from `repositories.base`), so
`repo = PersonRepository()` beside `read_vault(repo.vault_path)` names none of clause (iv)'s three
token shapes. Clause (i) spelling, (ii) non-vacuity, (iii) provenance and (iv) source are all GREEN,
the runtime door EXECUTES, `module_import_uses` under `WALL_C_MODULES | {"subprocess", "runpy"}`
is clean, `os_module_attribute_uses` is clean, `FORBIDDEN_DEFAULT_PATTERNS` is clean — and the live
vault is rewritten on a machine where `OBSIDIAN_VAULT_PATH` is exported, which is where CLAUDE.md's
floor command is hand-run. There is a THIRD source, and it is inside the library this module tests.

So every sentence in this document asserting that the live path has TWO sources, or that the source
half is total over omission shapes, is false as written. **The obligation is the sweep, not the
three edits** — a partial correction here reproduces exactly the shape my round 4 blocked on, where
a ruling was folded into one surface and the others kept describing the pre-ruling world. Round 5
named three; the enumeration at source returns seven:

1. `## Exploration Notes` `:977-980` (the sixth pass's own revision note) — "the live vault path has
   exactly two sources in this module's universe, so a clause that the module NAMES neither outside
   `_temp_vault`'s own body is total over every omission route through every door."
2. Design §6(d) `:1610-1614` — "the live vault path has exactly TWO sources in this module's
   universe and that set is closed by construction."
3. Design §6(d) `:1616` — the M8 RULE sentence, "…so no omission-shaped escape can reach the live
   vault at all, through any door the callee census enumerates or any door it does not." This one is
   quoted verbatim as the M8 fold record's `design:` value at `:2793`, so the two move together (see
   the mechanical rider below).
4. Design §7 `:1830-1836` — "It is a CLASS closure and not a fifth door: the live path has exactly
   two sources… so no omission-shaped escape can reach it through any door."
5. Design §7 `:1841-1843` — "the source half proves the module cannot NAME the live path at all —
   which is the only one of the four that is total over omission shapes."
6. `## Mitigation Folds` `:2702-2709` ("the only closure here that is total by construction rather
   than by enumeration… exactly TWO sources") **and** `:2711-2718` ("it has exactly two members…
   **There is no third**, because a call in this module either names its arguments in this module's
   `ast` or leaves the process, and both are graded"). `:2716` is the sharpest of the seven and round
   5 did not name it: a call in this module can hand a drive a live path the module's text never
   names, which is the whole of the finding.
7. `## Scope Boundary` `:3119-3125` — the restated bound, "TOTAL over OMISSION shapes by
   CONSTRUCTION and not by enumeration… because a drive can only reach the live vault by NAMING it,
   and clause (iv) (M8) leaves the module no place outside `_temp_vault`'s own body to name it; the
   DOOR census (M5, M7) and the import wall (M6) are then belt-and-braces over the routes, not the
   load-bearing half."

Surface 7 is why this is blocking rather than a note, and the reason is the one I gave last round
for the same paragraph: its closing sentences instruct a later gate to CITE it and escalate rather
than REVISE (`:3141-3142`). A standing ruling whose stated reason is false will wave through exactly
the class it names, and it has now demoted the door census and the import wall to "belt-and-braces"
on the strength of that false reason — so the paragraph is weaker than the mechanism it describes,
in the direction that costs a future gate its finding.

*What the correction owes, stated so the spec-writer does not have to guess and does not have to
wait on blocking issue 2's owner.* The truth is statable today and is unchanged by how the
sufficiency call goes: the wall is total over omission shapes that NAME the path, at the three token
shapes clause (iv) closes; a path obtained from the library's own environment fallback is not named
by the module and is not caught; that residue is a THIRD source, it is an omission shape and not
deliberate-act residue, and whether to close it is routed to Dave or the conductor (issue 2). Round
5 is right that this correction is owed MORE if the answer is "stop", not less. Every one of the
seven surfaces states it, and the demotion of M5/M6/M7 to "belt-and-braces" at `:3124-3125` comes
back out, because with the source half not total the door census and the import wall are load-bearing
again.

*Two mechanical riders the edit must respect, both cheap to get wrong.* **M8's `desc` does NOT
move.** Round 5 re-emitted all eight fences byte-identically and ruled explicitly (its FIDELITY
note) that M8's `desc` keeps its now-overstated rationale clause because the REQUIREMENT did not
move; `desc` is the only machine-anchored field, so re-wording it re-stales a fresh fold record and
D8c refuses `specced -> ready` on a requirement nobody changed. I route against that ruling rather
than re-litigating it — it is the threat modeler's call about its own fence and the reasoning is
sound. The fold's `design:` value at `:2793` is NOT machine-anchored and must move with surface 3,
or the record stops being a faithful quote of the sentence it claims. **And nothing in the
correction touches `## Intent` or `## Acceptance Criteria`** — no criterion states the wall's
totality — so `ac_hash: 973d7a08f068` and all five per-criterion hashes stay valid and no re-sign is
owed. I checked each of the seven surfaces against the criteria to confirm that.

**2. The mechanism half is a SUFFICIENCY call and it is NOT the spec-writer's to make — it is routed
to Dave or the conductor, and it should be put to them in parallel with pass seven rather than
after it.** `## Scope Boundary:3143-3146` records the trigger in the document's own bytes, and the
situation matches it on every element: a fifth threat-model round, on this family, with M7 and M8
landed as written, and a ninth `kind: required` mitigation as the thing being weighed. Round 5
declined to force it through D8 and emitted eight fences, which is correct and is what the
instrument was minted for. I am not reopening it and I am not deciding it.

What the ruling-holder needs is already assembled in round 5's own text and I re-verified the parts
that decide the cost: closing it is one more CLOSED shape in the census Task 7 already builds — a
callee resolving (by the same `ast.Name.id` / `ast.Attribute.attr` rule `drives` and `bindings`
already use) to an identifier ending `Repository`, recorded as `(module_id, lineno, token,
enclosing)` like the other three, graded by Task 9's EXISTING clause (iv) with no new check, no
fifth derivation and none of the counts this document has re-synced twice. The requirement would be
ZERO repository constructions in the module rather than "no no-arg construction" —
`_is_unconfigured:86-101` swallows blank, whitespace-only and `"."`, so a spelling-shaped rule
including `NO_ARG_CONSTRUCTION`'s own regex is a partial closure. The import-allowlist shortcut
genuinely cannot work at this granularity, which I confirmed at `module_import_uses:847`: it reports
the ROOT module, so `from obsidian_schemas.repositories.base import SKIP_REASONS` — which M1's
verify NEEDS, because the module is forbidden to hand-type a `SKIP_REASONS` member — and
`from obsidian_schemas import PersonRepository` are indistinguishable to it. If the answer arrives
before pass seven lands, both halves ship in one pass; if it does not, issue 1 stands alone and this
item can still come back for round 6 on that basis.

**On the arc, because it is the judgement only this gate can make, and this is the fifth round.**
The regress signature is present and I am naming it rather than iterating it: every threat-model
round since round 1 has ended by declaring a level closed BY CONSTRUCTION, and every following round
has found the enumeration hiding inside the construction — M8's "two sources" is a two-member
enumeration wearing the word *sources*, exactly as M5's "three entry points" was a three-member
enumeration wearing the word *complete*. That is why the sufficiency instrument exists and why
issue 2 goes to its owner instead of becoming my finding. But issue 1 is categorically NOT another
rung on that ladder: it adds no mechanism, no derivation, no check and no count; it is the
document telling the truth about the mechanism it already has, and it is what makes the escalation
in issue 2 sound rather than self-undermining. A REVISE that adds a rung and a REVISE that corrects
a bound have opposite meanings for this arc, and this is the second kind. My prior round's findings
all closed and stayed closed, which I verified surface by surface below.

### Non-blocking notes

1. **`## Mitigation Folds`' opening sentence (`:2583-2584`) names the wrong latest-speaking round.**
   It reads "restated IN PLACE, against the LATEST SPEAKING round — which since 2026-09-15 is
   `## Threat Model — 2026-09-15 (round 4)`". Round 5 (2026-09-16) now speaks, and it re-emitted all
   eight `desc` values byte-identically, so D8c passes on the mechanics and this is not blocking —
   but it is the same sentence whose staleness produced my round-4 D8c refusal, and the next pass is
   editing that section anyway for surface 6. One line, in the same edit.
2. **Two stale bare-line cites live inside SIGNED criteria and therefore cannot be fixed without a
   re-sign.** AC-3's desc says `SCRIPTS_ROOT` is `derivations.py:31`; it is `:33` (round 5's note 3
   found the sibling instance in the archival currency audit at `:77`, and this is the one that
   matters more because it is frozen). AC-5's desc still carries the AC red-team's "A SIXTH CENSUS
   READER" label against a body that correctly says "a fifth reader beside them". Both are
   re-anchoring nits under WI-215, neither changes what a builder implements, and neither is worth a
   re-sign of a set Dave signed on 2026-09-15 — recorded so no later round re-derives them as drift
   and then discovers the re-sign cost.

### What is NOT a gap — checked and clean

Stated so round 6, if there is one, does not re-walk them. Sixteen canonical
`- [ ] **Task N — …**` definitions with unique ordinals 1–16 (counted on this tree: 16), each
carrying exactly one well-formed lowercase `verify:` declaration (counted: 16) — fourteen naming
bare `test_` names, Task 1 `baseline` and Task 16 `hand-run`, both correct uses of the closed
exception kinds — and no verify command writes anything outside `write_authority` (WI-238). Every
`landed: Task N` in round 5's eight fences (2, 4, 9, 4, 7, 15, 7, 9) resolves to a defined ordinal,
so no D8b refusal is latent. All eight fold records are present in `## Mitigation Folds` with
`desc` values I diffed against round 5's fences and found byte-identical, and I read each `design:`
and `work:` quote where it claims to sit rather than judging the pair alone — every one is faithful
to the `## Design` sentence and the named task's own text. `## Write Targets` coverage is exact in
both directions: nine builder fences, every plan task's target inside them, no fence naming a path
no task writes, the two `kind: precondition` paths READ by AC-5 and in no builder fence, Tasks 1 and
16 writing only the Build Log, and **the sixth pass's M7/M8 material adding no new target** —
`live_path_names` lands in the already-declared `tests/derivations.py` and clause (iv) in the
already-declared `tests/test_lint_vault_fix_rules.py` — so the L3 level the frontmatter carries is
not under-declared. `OPEN: None`, zero open items. Check 11 is satisfied by `## Verified Diagnosis`'
four falsifiable claims, VD-2's six decline sites and VD-4's "nothing under `tests/` invokes
`run_lint`" both re-confirmed. The WI-235 counting-wall question is answered for all five of this
item's count-oracles, each with its claimed shapes AND a near-miss shipped as fixtures — including
`live_path_names`' non-vacuity arm and the innermost-def scoping shape, which is the one an
occurrence-count reading is green on. The WI-278 corpus-fixture arm is chosen explicitly in
AC-5(b)'s one-line coupling declaration. The WI-229 conscious-pin sweep is discharged by the
nine-site rename inventory across four modules.

**Round 4's two blocking issues both closed and stayed closed**, verified surface by surface rather
than from the fold's account: M7 and M8 carry fold records (`:2782-2796`); §6(d)'s callee set is
four with the set stated as a derived predicate rather than N names (`:1497-1526`); §7's syntax half
grades `quarantine_garbage` under the existing position rule (`:1764-1767`); Task 7 ships M7's three
`drives` shapes and M8's four scoping shapes (`:2193-2237`); the exemption's mechanism is RULED as
INNERMOST enclosing `FunctionDef` on all three surfaces that state it (`:1627-1637`, `:1822-1823`,
`:2292-2295`); the `read_vault`-widening shortcut is refused with its reason (`:1650-1654`); M6 and
M8 are stated as one rule about `_temp_vault` at two levels (`:1661-1668`); §7 reads "FOUR parts"
with the falsified "trio … total" wording quoted and dated rather than deleted (`:1724-1727`) while
its necessity companion at `:1843-1844` is correctly left standing; the folds' upward sweep records
the correction in place (`:2675-2709`); and the THIRTEENTH and FOURTEENTH mutations landed, the
thirteenth correctly written with `tmp` so it discriminates the callee set and not clause (iv).

### Carried-forward notes

Every still-open non-blocking note from every prior round, by name:

- **Threat model round 1 note 1 / round 2 note 3 / round 3 note 3 / round 4 note 5 / round 5 note 4
  (the exit attestation's redaction reminder is absent from `docs/lint-vault-live-baseline.md` §4's
  own bytes)** — STILL OPEN, re-deferred a seventh time for the same correct reason: §4 is
  conductor-owned and outside the builder's write authority, so it has no Implementation-Plan task
  to land in and a fence pointing at one would be a fiction. The conductor's, at the ship door.
- **Threat model round 1 note 2 / round 2 note 4 / round 3 note 4 / round 4 note 6 / round 5 note 5
  (`apply_fixes:994` prints `str(exc)` to stderr)** — STILL OPEN as a deliberate non-change. The
  handler set does not widen, so no new content reaches that channel, and it is pinned as a message
  equality at `tests/test_lint_vault_fix_gate.py:123-125`.
- **Threat model round 2 note 1 / round 4 note 7 / round 5 note 6 (M3's wall universe is ONE
  module)** — a standing scope ruling, not an open note; routed against rather than re-litigated.
  Nothing in this round widens it, and blocking issue 2's candidate closure would not either.
- **Threat model round 5 note 3 (`SCRIPTS_ROOT` is `:33`, not `:31`)** — OPEN, and extended by my
  non-blocking note 2: the same stale line also sits inside signed AC-3, where it cannot be fixed
  without a re-sign, so it is carried rather than actioned.
- **Data audit round 2's two carried items** — both STILL OPEN and both correctly outside the spec:
  the build-start re-grounding should re-run AC-5(b)'s five-row comparison before the first edit
  (the baseline is six days old and the vault churns weekly — still GREEN against HEAD this round,
  which is a snapshot fact and not a standing one), and the exit half of A7's bracket has no battery
  wall by construction and lives at the conductor's ship door.
- **My round-4 non-blocking note 1 (§6(d)'s scan-universe paragraph became an incomplete enumeration
  once M7 landed)** — CLOSED. `:1545-1548` now names `quarantine_garbage`'s own `vault_path`
  parameter at `:1113` as a third raise site and the `quarantine_garbage(garbage, vault_path)` call
  at `run_lint:1220` beside the `apply_fixes` call at `:1194`, and `:1549-1551` explicitly labels
  the list an ENUMERATION rather than a total while keeping the conclusion.
- **Threat model round 4 notes 1 and 2, round 5 note 2, round 3 notes 1–2, architect round 4 notes
  1–4, the AC red-team's label slip, and my own round-1 notes 1–5 / round-2 notes 1–3 / round-3
  notes 1–2** — all CLOSED, each recorded in the round that closed it; the AC red-team's label slip
  is re-carried above as non-blocking note 2 only because it sits inside a signed criterion.

```verdict
gate: spec-reviewer
verdict: REVISE
date: 2026-09-16
model: claude-opus-5
targets: M8, #design, #scope-boundary, #mitigation-folds, #exploration-notes
prior: held
basis: folded-material
findings: 1/3
note: Round 4's two blockers closed and stayed closed — M7 and M8 carry fold records whose `desc` values I diffed byte-for-byte against round 5's fences, the exemption's mechanism is RULED as innermost-enclosing-`FunctionDef` on all three surfaces stating it, §7 reads "FOUR parts" with the falsified trio wording quoted and dated, and the folds' upward sweep records its correction in place. What blocks is the WI-226 truthfulness sweep threat-model round 5 handed to this lane, and I verified its factual half at the code rather than at the fence: `obsidian_schemas/repositories/base.py:_resolve_vault_path:104-114` falls back to `os.environ.get(ENV_VAULT_PATH)` INSIDE the library (`ENV_VAULT_PATH:75`, `_is_unconfigured:86-101` swallowing None/blank/`"."`, `BaseRepository.__init__:154` carrying it for all four repositories exported at `obsidian_schemas/__init__.py:74-77`), and the new check module MUST import from `obsidian_schemas` because M1's verify reads `SKIP_REASONS` from `repositories.base` — so `repo = PersonRepository()` beside `read_vault(repo.vault_path)` names none of clause (iv)'s three token shapes and passes (i)-(iv) with the runtime door executed, the import wall clean, `os_module_attribute_uses` clean and `FORBIDDEN_DEFAULT_PATTERNS:278` clean, while rewriting the live vault on the machine where `CLAUDE.md`'s floor command is hand-run. There is a THIRD source, so every sentence claiming the live path has TWO or that the source half is total over omission shapes is false. My contribution over round 5's account is the ENUMERATION: it named three surfaces, the sweep at source returns SEVEN — Exploration Notes `:977-980`, §6(d) `:1610-1614` and the M8 rule sentence `:1616` (quoted as the fold's `design:` at `:2793`, which moves with it), §7 `:1830-1836` and `:1841-1843`, `## Mitigation Folds` `:2702-2709` and `:2711-2718` (whose "There is no third, because a call in this module either names its arguments in this module's `ast` or leaves the process" is the sharpest of the seven and is exactly what the finding falsifies), and `## Scope Boundary` `:3119-3125`. A three-of-seven correction reproduces the shape my round 4 blocked on. Surface 7 is why this is blocking rather than a note: its closing sentences instruct a later gate to CITE the paragraph and escalate rather than REVISE, and it has now demoted the door census and the import wall to "belt-and-braces" on the strength of a false reason — so the ruling is weaker than the mechanism it describes, in the direction that costs the next gate its finding, and the demotion comes back out with the correction. Two mechanical riders: M8's `desc` does NOT move (round 5's FIDELITY ruling is sound — `desc` is the only machine-anchored field, the requirement did not move, and re-wording re-stales a fresh record into a D8c refusal), while the fold's `design:` at `:2793` is not machine-anchored and must move with §6(d) `:1616`; and nothing in the correction touches `## Intent` or `## Acceptance Criteria` — no criterion states the wall's totality — so `ac_hash: 973d7a08f068` and all five per-criterion hashes stay valid and no re-sign is owed. The MECHANISM half is NOT mine and is NOT the spec-writer's: `## Scope Boundary:3143-3146` assigns it to Dave or the conductor and the situation matches the trigger on every element (fifth threat-model round, this family, M7 and M8 landed as written, a ninth mitigation the thing being weighed); round 5 correctly declined to force it through D8, I am not deciding it either, and it should be put to its owner in PARALLEL with pass seven rather than after it, since issue 1 is statable and owed whichever way it goes — more owed if the answer is "stop". On the arc: the regress signature IS present and I am naming it rather than iterating it — every round has declared a level closed BY CONSTRUCTION and the next has found the enumeration inside the construction, M8's "two sources" being a two-member enumeration wearing the word *sources* exactly as M5's "three entry points" wore *complete* — which is precisely why issue 2 goes to its owner; but issue 1 adds no mechanism, no derivation, no check and no count, it is the document telling the truth about the wall it already has, and it is what makes that escalation sound rather than self-undermining. Everything else re-verifies clean: sixteen canonical tasks each with one well-formed `verify:`, every `landed: Task N` resolving, all eight fold `design`/`work` quotes read where they claim to sit and faithful, Write-Targets coverage exact both ways with the sixth pass adding no target, the drift audit's one finding archival (the live cite at `:1656` already reads `:278`, with `:320` correctly named as the universe line at `:1659`), the WI-235 shapes shipped for all five count-oracles including `live_path_names`' non-vacuity and innermost-def scoping, and AC-5 still GREEN against the committed baseline and census (821/835 delta `+14`, 315/315, 19/19, 0/0, 0/0).
```

## Threat Model — 2026-09-16 (round 6)

**Recommendation: PROMOTE to threat-modeled**

Sixth round, cold-start. The carry-forward is this document's five prior threat-model rounds and the
five spec-review rounds answering them. My round 5 PROMOTEd on eight fences and deliberately split its
finding in two: **(a)** the premise correction — "a drive can only reach the live vault by NAMING it"
is false — routed to the spec-reviewer's WI-226 lane and carried behind no fence; and **(b)** the
ninth mechanism, routed to Dave or the conductor under the sufficiency trigger `## Scope Boundary`
records in the document's own bytes. Spec-review round 5 took (a) as its blocking issue, verified the
factual half independently at the code rather than at my fence, and enumerated SEVEN surfaces where I
had named three. The seventh spec-writer pass has since landed it. Every citation below was
re-resolved by opening the file or the code, never taken from the pass's account of itself and never
from spec-review round 5's paraphrase.

### Trigger check

The same four triggers fire, unchanged: filesystem operations on user-owned files
(`apply_fixes:957`, `:975`, `quarantine_garbage:1134`, `:1140`), untrusted input (vault bytes),
persistence (a floor-resident module driving the MUTATING entry point of a tool whose default target
is Dave's live vault), and an information-disclosure surface (the operator-facing summary against
`obsidian_schemas/errors.py`'s bounded-projection contract). The seventh pass retires none of them and
adds none, because it moves no mechanism.

### What the seventh pass did, checked at the bytes rather than at the pass note

- **The correction landed, and the sweep is WIDER than the one it was handed.** The pass ran the
  claim's own vocabulary as a grep rather than working spec-review round 5's list, and returned TWELVE
  live surfaces plus `## Scope Boundary` as the thirteenth, marking the five the review had not named.
  I spot-checked six at their own bytes rather than accepting the enumeration: `## Exploration Notes`
  `:982-992` and its belt-and-braces parenthesis `:1026-1032`; Design §6(d) `:1754-1769` (the "set that
  is closed is the set of SPELLINGS, not the set of SOURCES" replacement) and the M8 RULE sentence at
  `:1772`; Design §7 `:1868-1873`, `:1990-2005` and `:2010-2017`; and `## Mitigation Folds`
  `:2882-2904` plus `:2915-2935`. Every one states the SAME correction — clause (iv) is total over
  omission shapes that NAME the path and not over those that OBTAIN it unnamed; the library fallback
  is a THIRD source; the residue is an OMISSION shape and so NOT covered by the deliberate-act bound;
  and M5/M6/M7 are LOAD-BEARING again — with the falsified wording quoted and dated in place rather
  than deleted. The sharpest of the thirteen, `## Mitigation Folds`' *"There is no third, because a
  call in this module either names its arguments in this module's `ast` or leaves the process"*, is
  corrected at `:2915-2926` with its own result labelled WRONG in terms.
- **The two surfaces that carried the claim in a HEADING are qualified too**, which is the half-fix
  this round would otherwise have found: the `## Scope Boundary` bullet title at `:3322-3327` and the
  folds' upward-sweep framing.
- **All eight `desc` values are byte-identical to my round-5 fences.** I diffed each fold record
  against the round-5 fence rather than against the pass's claim — `:2955`/`6475`, `:2963`/`6482`,
  `:2971`/`6489`, `:2979`/`6496`, `:2987`/`6503`, `:2995`/`6510`, `:3003`/`6517`, `:3011`/`6524`. M8's
  still carries the rationale clause my round-5 FIDELITY note ruled must not move, which is correct.
- **M8's fold `design:` DID move and is a faithful quote.** `:3012` is character-for-character the
  §6(d) rule sentence at `:1772` it claims to quote, so the record did not stop being a quote when the
  sentence was corrected.
- **`## Mitigation Folds`' opening now names round 5 as the latest speaking round** (`:2756-2757`),
  closing spec-review round 5's non-blocking note 1 — the same sentence whose staleness produced a
  D8c refusal two rounds ago.
- **The escalation instruction is now SCOPED, which was the load-bearing half.** `:3378-3383` reads
  "Any gate finding at the DELIBERATE-ACT level should cite this paragraph and escalate rather than
  REVISE — and that instruction is scoped to that level and to nothing else: a finding at the OMISSION
  level is NOT covered by this bound, is a legitimate REVISE". That is the repair that matters: the
  2026-09-15 wording would have waved through exactly the class it names.
- **Every `landed:` ordinal still resolves.** Sixteen canonical task definitions with ordinals 1–16
  counted on this tree (`:2281`–`:2627`); the fences name 2, 4, 9, 4, 7, 15, 7, 9. No D8b refusal is
  latent.

### STRIDE review — scoped to what the seventh pass added

**Spoofing, Tampering, Repudiation, Information disclosure, Denial of service, Elevation of
privilege — nothing new, and for once the reason is structural rather than a judgement.** The seventh
pass adds no derivation, no check, no clause, no count, no `delta` key, no gate call and no
`write_note` argument; it edits prose only, which I confirmed by re-reading Tasks 7, 9 and 15 and the
`live_path_names` specification and finding the mechanism unchanged from round 5. There is therefore
no new code surface to walk, and the STRIDE findings from round 5 stand unaltered. The one
security-relevant CHANGE the pass makes is in the opposite direction: a standing ruling that
previously mis-stated its own scope now states it correctly, which strictly increases what a later
gate will catch.

### The one new finding this round, and it is NON-BLOCKING because it is not an omission route

The seventh pass declares the next level of the ladder rather than leaving it for me (`:1142-1157`,
restated at `:2906-2935`): the class is *an in-process callable the module may invoke that resolves
the live vault from the environment rather than from its argument*, and the census "returns exactly
ONE member — `_resolve_vault_path`", with near members named so they are not re-derived. That is a
completeness claim about a finite checkable set, and this document's four-round pattern is that such
claims are short by one, so I re-ran the census myself rather than reading it — the same grep over
`obsidian_schemas/**`, `scripts/**` and `tests/**`.

**The census is short by one, and the missing member is `scripts/migrate_person_to_discuss.py:main`.**
`def main():` at `:158` takes no parameters; its `--vault` carries
`default=os.environ.get('OBSIDIAN_VAULT_PATH', '')` at `:165`; it resolves that value at `:174`
(`parser.parse_args()`) and `:181`; and it reaches `vault_io.write_note` at `:109`. It resolves the
live vault from the environment rather than from an argument, it mutates notes, it sits inside the
swept universe (`scripts/**`), the grep hits it at `:165` — and it appears in neither the near-member
list at `:2928-2931` nor the one at `:1149-1154`, both of which name `lint_vault`'s already-graded
token and entry point but not this script's. It is also NOT in the graded callee set: M5 and M7 grade
`lint_vault`'s four functions, so `migrate_person_to_discuss.main()` in the check module carries no
clause-(iv) token and is collected by nothing.

**It is nevertheless not a route, and that is the finding rather than a hedge on it.** Reaching a live
write through it requires TWO deliberate acts, not an omission. First, `main()` reads `sys.argv`
through `parse_args()` at `:174`; under the floor command that argv is pytest's own, so an accidental
call exits at argparse rather than reaching a vault, and getting past it means constructing an argv on
purpose. Second, `:186` sets `dry_run = not args.apply` and both `migrate_vault:121` and
`migrate_person_file:40` default `dry_run=True` with the write at `:109` behind an `if dry_run:` guard
at `:105` — so a run that somehow got past argparse still writes NOTHING without an explicit
`--apply`. Direct calls to `migrate_vault(vault_path, …)` take an explicit path and are not env
resolvers at all. Two deliberate acts put this squarely in the residue `## Scope Boundary:3362-3373`
already records as the mechanism's honest bound, and the check module has zero motive to import a
one-shot migration script the same section declares out of scope at `:3318-3319`.

**Why I am recording it rather than folding it, and why it is material to the routed ruling.** The
census at `:2931-2933` is explicitly labelled "an ENUMERATION measured at a date and never a total",
which is the honest framing this document spent five rounds earning — so a missed member is a factual
nit inside a correctly-bounded claim, not another false totality. But it carries one thing the
ruling-holder should have: this is the FIRST time the enumeration-short-by-one pattern has produced a
member that is not a live route. Rounds 2 through 5 each found a missing member that WAS reachable by
omission; this one is reachable only by deliberate act. That is evidence the family is bottoming out
rather than continuing, and it belongs in the "Against" column of the question `## Scope Boundary`
`:3392-3418` puts to its owner. Note also that the candidate closure being costed there — zero
repository constructions in the module — would not close this member, and does not need to.

### The routed sufficiency call is still OPEN, so I emit EIGHT fences and not nine

`## Scope Boundary:3388-3391` records the trigger as FIRED on 2026-09-16 with the call OPEN with its
owner, and nothing in this tree answers it. Round 5 declined to force it through D8, spec-review round
5 routed it the same way, and the seventh pass correctly refused to decide it in either direction. My
position is unchanged and I am not using a sixth round to convert a routed decision into a fence by
attrition: a ninth `kind: required` mitigation would be me making the sufficiency call unilaterally
through D8, which is the one thing the instrument was minted to prevent. The residue is DECLARED on
every surface, correctly characterised as an OMISSION shape that the deliberate-act bound does NOT
cover (`:2900-2904`, `:3417-3418`), and costed for the ruling-holder. A declared-and-routed open
decision with a named owner is not a spec gap, and I hold no security finding that makes the approach
unsafe — hence PROMOTE.

### Mitigations required

1. **M1 — the read-error value is a vocabulary member, never the decode exception.** Folded into
   Design §1 and Task 2; record fresh. Re-emitted unchanged.
2. **M2 — both new records carry bounded values.** Folded into Design §3 and Task 4; record fresh.
   Re-emitted unchanged.
3. **M3 — the containment wall, with the syntax half asserting provenance.** Folded on all six
   surfaces; record fresh. Re-emitted unchanged.
4. **M4 — an issue whose write committed is never re-labelled `errored`.** Frame re-checked at
   `:949`/`:951`/`:957`/`:975`; unmoved. Re-emitted unchanged.
5. **M5 — the CLI entry point is inside the wall's callee set.** Premises re-read at `:1252`, `:1255`.
   Re-emitted unchanged.
6. **M6 — the module cannot reach the CLI by subprocess either.** `FS_MODULES` and
   `OS_READONLY_NAMES` re-read at `tests/derivations.py:68-69`, `WALL_C_MODULES` at
   `tests/test_name_gate_wall.py:1043`; neither set reaches `subprocess` or `runpy`. Re-emitted
   unchanged.
7. **M7 — the callee set is the script's COMPLETE set of mutating entry points, and that is four.**
   Landed on all five surfaces; completeness claim still settled by the seven-site `vault_io.` census.
   Re-emitted unchanged.
8. **M8 — the live vault path cannot be NAMED in the module at all.** Landed on all six surfaces, with
   the correction landing in the PROSE around it and not in the requirement. Re-emitted unchanged.

**FIDELITY.** M8's `desc` still carries the clause round 5 falsified ("a clause over the path's two
SOURCES is total over every omission route through every door"). I re-emit it BYTE-IDENTICALLY for the
third time, for the reason round 5 gave and spec-review round 5 routed against rather than
re-litigated: what M8 REQUIRES has not moved one character — the module must name the live vault path
nowhere outside `_temp_vault`'s body — and `desc` is the only machine-compared anchor, so re-wording a
rationale would re-stale a fresh record and spend a producer-fix round on a requirement that did not
move. The overstatement now lives, corrected and dated, in the thirteen prose surfaces where it
belongs.

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

1. **The `migrate_person_to_discuss.main` census member (above) is recorded, not actioned.** It is a
   second member of the class `:2920-2933` enumerates, it is unreachable except by two deliberate acts
   (a constructed `sys.argv` past `parse_args:174`, then an explicit `--apply` to clear the
   `dry_run` default at `:186`/`:105`), and it is therefore inside the deliberate-act bound rather
   than beside it. Written down so round 7, if there is one, checks the census instead of re-deriving
   it and then discovering it is not a route. No fence: folding a non-route would spend a
   producer-fix round on a threat that does not exist.
2. **Round 1 note 1 / round 2 note 3 / round 3 note 3 / round 4 note 5 / round 5 note 4 (the exit
   attestation's redaction reminder is absent from `docs/lint-vault-live-baseline.md` §4's own
   bytes) — STILL OPEN**, re-deferred an eighth time for the same correct reason: §4 is
   conductor-owned and outside the builder's write authority, so it has no Implementation-Plan task to
   land in and a fence pointing at one would be a fiction. The conductor's, at the ship door.
3. **Round 1 note 2 / round 2 note 4 / round 3 note 4 / round 4 note 6 / round 5 note 5
   (`apply_fixes:994` prints `str(exc)` to stderr) — STILL OPEN as a deliberate non-change.** The
   handler set does not widen, so no new content reaches that channel, and it is pinned as a message
   equality at `tests/test_lint_vault_fix_gate.py:123-125`.
4. **Round 2 note 1 / round 4 note 7 / round 5 note 6 (M3's wall universe is ONE module) stands as a
   scope ruling** and is routed against rather than re-litigated. Nothing this round widens it.
5. **Round 5 note 3 (`tests/derivations.py:SCRIPTS_ROOT` is at `:33`, not `:31`) — CARRIED, and
   correctly not actioned.** Spec-review round 5's non-blocking note 2 established that the live uses
   name the symbol without a line and that the one stale bare cite sits inside signed AC-3, where
   fixing it would invalidate a set Dave signed on 2026-09-15 for a change no builder reads. Same for
   AC-5's "A SIXTH CENSUS READER" label. Both are WI-215 re-anchoring nits.
6. **Nothing in this round touches `## Intent` or `## Acceptance Criteria`.** I re-checked all five
   criteria against this round's material: none states the wall's totality and none names the census,
   so `ac_hash: 973d7a08f068` and the five per-criterion hashes stay valid and no re-sign is owed.

```verdict
gate: threat-modeler
verdict: PROMOTE
date: 2026-09-16
model: claude-opus-5
note: The seventh pass landed the truthfulness correction in full and wider than it was handed — spec-review round 5 enumerated seven surfaces, the pass swept its own claim's vocabulary and returned TWELVE plus `## Scope Boundary` as the thirteenth, and I spot-checked six at their own bytes rather than accepting the list (`## Exploration Notes` `:982-992` and `:1026-1032`, Design §6(d) `:1754-1769` and the M8 rule sentence `:1772`, Design §7 `:1868-1873`/`:1990-2005`/`:2010-2017`, `## Mitigation Folds` `:2882-2904` and `:2915-2935`). Every one states the same correction with the falsified wording quoted and dated in place rather than deleted: clause (iv) is total over omission shapes that NAME the path and not over those that OBTAIN it unnamed, the library's `_resolve_vault_path` fallback is a THIRD source, that residue is an OMISSION shape so the deliberate-act bound does NOT cover it, and M5/M6/M7 are LOAD-BEARING again rather than belt-and-braces. The two HEADINGS carrying the claim are qualified too, and the repair that actually mattered landed: `:3378-3383` now scopes the escalate-rather-than-REVISE instruction to the deliberate-act level explicitly and states that an omission-level finding is NOT covered and IS a legitimate REVISE — which is what stops a bound with a false stated reason waving through the class it names. All eight `desc` values diffed byte-for-byte against my round-5 fences (`:2955`/`:2963`/`:2971`/`:2979`/`:2987`/`:2995`/`:3003`/`:3011` against `6475`/`6482`/`6489`/`6496`/`6503`/`6510`/`6517`/`6524`) and all eight hold; M8's fold `design:` at `:3012` correctly DID move and is a character-for-character quote of the corrected `:1772`; `## Mitigation Folds`' opening now names round 5 as the latest speaking round, closing the D8c staleness; and all sixteen task ordinals resolve, so the fences' 2/4/9/4/7/15/7/9 leave no D8b refusal latent. STRIDE is unchanged for a structural reason rather than a judgement: the pass moves no derivation, check, clause, count, `delta` key, gate call or `write_note` argument — I re-read Tasks 7, 9 and 15 and the `live_path_names` spec to confirm the mechanism is identical to round 5 — so there is no new surface to walk, and the one security-relevant change strictly increases what a later gate catches. My one new finding is the seventh pass's own next-level census (`:1142-1157`, `:2906-2935`), which claims the class of in-process callables resolving a vault from the environment has "exactly ONE member"; I re-ran the grep rather than reading it and it is short by one — `scripts/migrate_person_to_discuss.py:main:158` takes no parameters, defaults `--vault` to `os.environ.get('OBSIDIAN_VAULT_PATH', '')` at `:165`, and reaches `vault_io.write_note` at `:109`, yet appears in neither near-member list and is in no graded callee set. It is NOT a route and that is the finding rather than a hedge: reaching a write needs two deliberate acts, a constructed `sys.argv` past `parse_args:174` (pytest's own argv exits at argparse) and an explicit `--apply` to clear the `dry_run=True` default at `:186`/`:121`/`:40` guarding the write at `:105`, so it sits inside the deliberate-act bound at `:3362-3373`, and the check module has zero motive to import a one-shot script `:3318-3319` declares out of scope. It is a factual nit inside a claim the pass had already correctly bounded as "an ENUMERATION measured at a date and never a total" (`:2931-2933`) — not another false totality — and it carries one thing the ruling-holder should have: this is the FIRST time the enumeration-short-by-one pattern produced a member that is unreachable by omission, where rounds 2–5 each found one that was reachable, which is evidence the family is bottoming out and belongs in the Against column of the question at `:3392-3418`. I therefore emit EIGHT fences and not nine: `## Scope Boundary:3388-3391` records the sufficiency trigger as FIRED with the call OPEN with Dave or the conductor, nothing in this tree answers it, and I will not use a sixth round to convert a routed decision into a fence by attrition — a ninth mitigation would be me making that call unilaterally through D8, the one thing the instrument was minted to prevent. A declared, correctly-characterised and costed open decision with a named owner is not a spec gap; every one of the eight mitigations is landed on every surface its generator names, and I hold no finding that makes the approach unsafe.
```

## Spec Review — 2026-09-16 (round 6)

**Recommendation: PROMOTE to ready**

Cold-start re-read from line 1, full document, walking the bar from scratch rather than from my
round-5 gaps list. Every citation below was resolved by opening the file and reading the lines —
never from the injected drift audit, never from a fold record's account of itself, and never from
threat-model round 6's paraphrase, including the two claims this round finds false.

Rulings on record: A3/A3b (the YAML-reformat family, argued out on solve-in-one-place grounds), threat-model round 2 note 1 (M3's wall universe is ONE module), and `## Scope Boundary`'s containment-family bound as RESTATED on 2026-09-16 — total over omission shapes that NAME the path, not total over ones that OBTAIN it unnamed, not total over deliberate acts, with the escalation instruction now scoped explicitly to the deliberate-act level; I route against all three.

### Citation verification

All live symbol-anchored citations resolve AND mean what the spec claims. Re-read at the code this
round rather than carried forward:

- `obsidian_schemas/repositories/base.py:_resolve_vault_path:104-114` — `for candidate in
  (vault_path, os.environ.get(ENV_VAULT_PATH))` at `:111`, raising only when both are unconfigured;
  `ENV_VAULT_PATH = "OBSIDIAN_VAULT_PATH"` at `:75`; `_is_unconfigured:86-101` returning True for
  `None`, blank, whitespace-only and `Path(".")`. This is the factual half of my round-5 blocker and
  I re-grounded it at the bytes rather than treating it as settled.
- `scripts/lint_vault.py` — the whole `apply_fixes` frame the disposition rule turns on, read as one
  block at `:876-980`: `file_fixed = 0` at `:882`; the five decline sites at `:890`, `:906`, `:913`,
  `:935-936` and the replacement fall-through at `:963-973`; `person_missing_name:896-901` carrying
  NO guard, exactly as §4's totality argument requires; `gate_write` at `:947`; `fixed +=
  file_fixed` at `:949`; the first `write_note` at `:957`; the second at `:975`; `fixed += 1` at
  `:972`. Design §4 describes this frame correctly, line for line.
- `scripts/lint_vault.py:DEFAULT_VAULT:56` = `os.environ.get("OBSIDIAN_VAULT_PATH", "")`;
  `VaultFile:89`; `read_vault:110` with `except Exception:` at `:117`; `FixOutcome:820`;
  `CATEGORY_ORDER:1003` = `["completeness", "links", "timeline", "noise", "structural"]`, which is
  what makes Design §9's strip rule fire on all five census rows and on neither shape-internal
  parenthesis; `main`'s `--vault ... default=DEFAULT_VAULT` at `:1255`.
- `tests/derivations.py` — `PACKAGE_ROOT:31`, `TESTS_ROOT:32`, `SCRIPTS_ROOT:33`, `FS_MODULES:68` =
  `frozenset({"os","shutil","tempfile","fcntl","filelock","mmap"})`, `OS_READONLY_NAMES:69`. Neither
  set reaches `subprocess` or `runpy`; M6's premise holds.
- `tests/test_fixture_vault.py:508-509` is still `python_files_under(PACKAGE_ROOT, TESTS_ROOT)` with
  the expected set at exactly two members at `:510-514`, so Task 8 describes a real pending edit and
  its hold-at-two clause is the one true of `skip_reason_literal_sites`' predicate.
- All eight verify-declaration test names that already exist resolve uniquely:
  `test_lint_vault_fix_guards_threads_and_records_refusals:83` and
  `test_the_fix_outcome_surfaces_both_counts:276` in `tests/test_lint_vault_fix_gate.py`,
  `test_every_tier1_pattern_is_refused_at_every_door:127`,
  `test_identifiers_normalize_identically_on_every_door:110`,
  `test_a_legacy_dirty_name_stays_writable_for_unrelated_writes:81`,
  `test_skip_reason_declaration_binds_to_its_functions_returns:411`,
  `test_the_fixture_vault_files_close_their_wall_memberships_by_running_each_predicate:1287`,
  `test_every_acceptance_criterion_passes_under_the_conveyors_interpreter:108`.
- The plant-collision constraint re-checked on disk: `tests/fixtures/vault/@Dave  Marrowyn
  Fennwick.md` EXISTS (constraint 7's trap is live) and no corpus stem matches `@Tarnquil  Brenvik`
  (the nearest members are `@Wexlund Tarnquil.md` and `@Oskaline Brenvik-Tarnquil.md`, neither a
  collision), so AC-1(c)'s substitute stem is still free. `@Isolde Varnholt.md` exists — VD-1's
  specimen.
- AC-5 is still GREEN against HEAD, re-derived rather than carried: census `:277-281` reads
  821 / 315 / 19 / 0 / 0 and baseline `:79-83` reads 835 / 315 / 19 / 0 / 0 with delta column
  `+14 / 0 / 0 / 0 / 0`. Both zero rules still zero (strict arm), three non-zero still non-zero
  (sign arm), every computed `baseline − census` equal to the artifact's own delta cell. AC-5(a)'s
  shape predicates also re-run against the committed bytes: one delimited 40-hex SHA in the header
  region at `:12`, §0's 64-hex sha256 at `:26`, argv fences at `:22-24` and `:30-32`, the five
  headings present with §1 and §2 carrying trailing qualifiers at `:72` and `:91` — so the
  prefix-match rule is load-bearing rather than decorative, exactly as the leg says.

**The injected drift audit's three findings are all archival and no re-anchoring is owed.** All
three name `tests/test_vault_path_required.py:FORBIDDEN_DEFAULT_PATTERNS:320`, and all three
occurrences in this document sit inside append-only gate-round sections (`:4856` my round 2,
`:5898` my round 4, `:6618` my round 5). The LIVE cites in Design §7 read `:278` for the symbol and
name `:320` separately as the universe line, and both match the file.

### Bar check

Walked every check of `docs/spec-quality-bar.md` (the doc's own list is the count — never hardcode
it). Spec satisfies the bar.

**My round-5 blocking issue 1 is CLOSED and closed WIDER than it was raised.** I enumerated seven
surfaces; the seventh pass swept its own claim's vocabulary instead of working my list and returned
twelve plus `## Scope Boundary` as the thirteenth. I re-read eight at their own bytes rather than
accepting the enumeration — `## Exploration Notes` `:955-959` and `:1026-1032`, Design §6(d)
`:1754-1769` and the M8 rule sentence `:1772`, Design §7 `:1868-1873`, `:1994-2005` and `:2010-2017`,
`## Mitigation Folds` `:2882-2904` and `:2915-2935`, `## Write Targets`' check-module `why:` at
`:2673`, and `## Scope Boundary` `:3322-3327` / `:3351-3361`. Every one states the same correction
with the falsified wording quoted and dated in place rather than deleted: clause (iv) is total over
omission shapes that NAME the path and not over ones that OBTAIN it unnamed; `_resolve_vault_path`
is a THIRD source; the residue is an OMISSION shape so the deliberate-act bound does NOT cover it;
M5/M6/M7 are LOAD-BEARING again. The two HEADINGS carrying the claim are qualified too. And the
repair that actually mattered landed: `:3378-3383` now scopes the escalate-rather-than-REVISE
instruction to the deliberate-act level and states in terms that an omission-level finding is not
covered and IS a legitimate REVISE — which is what stops a bound with a false stated reason waving
through the class it names.

**The routed sufficiency call is OPEN and does not block, which my round 5 pre-committed to.** My
round-5 text says "if it does not [arrive], issue 1 stands alone and this item can still come back
for round 6 on that basis", and that is exactly the tree I am reading. The residue is DECLARED on
every surface, correctly characterised as an omission shape outside the deliberate-act bound, and
costed for its owner at `:3405-3418` — one more CLOSED shape in the census Task 7 already builds, a
callee resolving to an identifier ending `Repository`, graded by Task 9's EXISTING clause (iv): no
new check, no fifth derivation, no count moved. I confirmed the two cost claims that decide it:
`module_import_uses:847` reports the ROOT module, so it genuinely cannot separate
`from obsidian_schemas.repositories.base import SKIP_REASONS` — which M1's verify needs — from
`from obsidian_schemas import PersonRepository`; and `_is_unconfigured:86-101` swallows blank,
whitespace-only and `"."`, so the requirement has to be zero repository constructions rather than
"no no-arg construction". A declared, correctly-bounded, costed decision with a named owner is a
scope boundary, not a spec gap — and because the closure is a clause inside machinery this plan
already ships, a "close it" answer arriving after promotion is a one-clause amendment rather than a
re-spec.

**Mechanical checks, re-run rather than inherited.** Sixteen canonical `- [ ] **Task N — …**`
definitions with unique ordinals 1–16 (counted on this tree: 16) and exactly sixteen well-formed
lowercase `verify:` declarations (counted: 16) — fourteen naming bare `test_` names, Task 1
`baseline` and Task 16 `hand-run`, both correct uses of the closed exception kinds, neither an
illustrative declaration opening its segment. No verify command writes anything outside
`write_authority` (WI-238): every one is a test name or a read-only floor run. `## Write Targets`
coverage is exact in BOTH directions — nine builder fences, every plan task's target inside them
(Tasks 1 and 16 write only the Build Log), no fence naming a path no task writes, and the two
`kind: precondition` paths READ by AC-5 and in no builder fence; both precondition paths are in git
HEAD and I read them. `OPEN: None`. Check 12 does not fire on anything: I read all five criteria
in full this round and none states the wall's totality, names the census, or mentions `_temp_vault`
— so `ac_hash: 973d7a08f068` and the five per-criterion hashes stay valid and no re-sign is owed.

**Fold records — I diffed all eight against the LATEST SPEAKING round, which is now round 6, and
they hold.** `## Mitigation Folds`' prose still names round 5, but D8c compares `desc` against the
latest speaking round's fences and round 6 re-emitted all eight byte-identically; I compared
`:2955`/`:2963`/`:2971`/`:2979`/`:2987`/`:2995`/`:3003`/`:3011` against `:7058`/`:7065`/`:7072`/
`:7079`/`:7086`/`:7093`/`:7100`/`:7107` and every pair matches, M8's contested rationale clause
included. So the stale pointer is a prose defect and not a latent D8c refusal (non-blocking note 3).
Every `landed:` ordinal (2, 4, 9, 4, 7, 15, 7, 9) resolves to a defined task, so no D8b refusal is
latent. I read each `design:` and `work:` quote where it claims to sit rather than judging the pairs
alone: M1 at Design §1 `:1380-1385`, M2 at §3 `:1447-1451`, M3 at §7 `:1859-1873`, M4 at §4
`:1507-1518`, M5 at §6(d) `:1668-1669`, M6 at §7's import half `:1946-1952`, M7 at §6(d)
`:1656-1657`, M8 at §6(d) `:1772`. All eight are faithful, and M8's `design:` correctly MOVED with
the corrected sentence it quotes while its `desc` correctly did not — which is the rider I asked for
last round, honoured exactly.

**The WI-235 counting-wall question is answered for all five count-oracles**, each with its claimed
shapes AND a near-miss shipped as standing fixtures driven through the wall's own predicate —
including `live_path_names`' non-vacuity arm and the innermost-def scoping shape, which is the one
an occurrence-count reading is green on. The WI-278 corpus-fixture arm is chosen explicitly in
AC-5(b)'s one-line coupling declaration (frozen committed text, no module behaviour, no live
population shape). The WI-229 conscious-pin sweep is discharged by the nine-site rename inventory
across four modules, with the two standing equalities it must not disturb named. Check 11 is
satisfied: VD-1 through VD-4 each cite a falsifiable artifact and each artifact supports its claim —
including VD-4, whose claim I grounded independently below despite its stated grep result being
wrong.

### Build-runner dry-run

Walked all sixteen tasks as the builder; no judgment-call gaps detected. The three questions I
arrived with are each answered without leaving the document: *"Where exactly do I credit an issue,
and what do I delete?"* — Design §4's two credit points with the three deletions named by line
(`:882`, `:949`, `:972`), the two wrong ends argued in both directions, and Task 4's mixed plant as
the discriminator. *"What does clause (iv) exempt, and by what mechanism?"* — innermost enclosing
`FunctionDef`, ruled identically on all three surfaces that state it (Design §6(d) `:1783-1793`,
Design §7's SOURCE half `:1981-1983`, Task 9 `:2465-2468`), with both rejected readings and their
distinct failure modes. *"Which walls does my new module join, and how do I prove membership?"* —
Task 15 runs each standing wall's own shipped predicate over the item's touched files, with the
widened import set IMPORTED rather than hand-typed and its reach proved by five planted shapes and
five near-misses. A fourth question a builder would plausibly ask arrived while reading Task 9 and
is also answered: *"May my fixtures spell `lint_vault.DEFAULT_VAULT`?"* — yes, as fixture TEXT
handed to the predicate, never as module source, stated at `:3103-3108` with the one real build
constraint that falls out (a bare `"OBSIDIAN_VAULT_PATH"` Constant outside `_temp_vault` IS a match
and IS red) written down rather than left to be discovered.

### Minor notes (non-blocking)

1. **VD-4's falsifiable artifact states a grep result that is false, and it contradicts Design §7's
   own citation — the CLAIM is true and I grounded it myself.** `## Verified Diagnosis`
   `:1310-1311` reads "`grep -rn "run_lint" tests/` returns nothing (re-run 2026-09-15 on this
   tree)". Re-run on this tree it returns TWO hits, both in `tests/test_vault_path_required.py` —
   `def _run_lint_vault(*args):` at `:344` and its call at `:367` — because `run_lint` is a
   substring of `_run_lint_vault`. That is the very helper Design §7's import half cites by name at
   `:1963-1966` and M6's fold record repeats, so two live surfaces of this document disagree about
   what the same grep returns. I resolved it by reading the code rather than by preferring one
   surface: `_run_lint_vault` subprocesses `scripts/lint_vault.py` with `OBSIDIAN_VAULT_PATH`
   scrubbed (`:346-353`) and asserts only on `returncode` and `stderr` (`:370-375`), and all three
   of its invocations exit at `main`'s no-vault guard before `run_lint` is reached — so **no test
   under `tests/` invokes the `run_lint` function or reads a byte the summary line prints, exactly
   as VD-4, A6 `:357` and AC-4's `why` all assert.** The diagnosis stands; only the parenthetical
   is wrong, and the honest repair is one clause naming the two substring hits and why neither
   counts. Non-blocking because nothing a builder does turns on it: AC-4(d) orders the stdout
   capture on its own terms, VD-4 grounds no task, and the surface a builder actually copies from
   (`:1963-1966`) describes `_run_lint_vault` correctly. Recorded rather than waved because five
   prior review rounds — including my own round-5 "what is NOT a gap" list, which re-confirmed
   VD-4 — missed it, which is the re-review anchoring failure the role brief warns about, and
   because the point of a Check-11 artifact is that a reader can re-run it.
2. **The seventh pass's next-level census claims "exactly ONE member" and is short by one; the
   missing member is not a route, and it routes against the deliberate-act bound.** `:1146-1157`
   (restated at `:2906-2935`) declares the class *an in-process callable the module may invoke that
   resolves the live vault from the environment rather than from its argument* and reports the sweep
   returning exactly one member. Threat-model round 6 found a second and I verified it at the code
   rather than at its fence: `scripts/migrate_person_to_discuss.py:main:158` takes no parameters,
   its `--vault` carries `default=os.environ.get('OBSIDIAN_VAULT_PATH', '')` at `:165`, and it
   reaches `vault_io.write_note` at `:109` — a member of the stated class, inside the swept universe
   (`scripts/**`), and in neither near-member list. It is nevertheless NOT a route, which I also
   confirmed: `parse_args()` at `:174` reads `sys.argv`, which under the floor command is pytest's
   own, and `dry_run = not args.apply` at `:186` with the write behind `if dry_run:` at `:105` means
   even a constructed argv writes nothing without an explicit `--apply`. Two deliberate acts puts it
   squarely inside `## Scope Boundary`'s deliberate-act bound, whose closing instruction — now
   correctly scoped — tells me to cite and escalate rather than REVISE, so I do. It is a factual nit
   inside a claim the pass had already bounded honestly as "an ENUMERATION measured on 2026-09-16
   and never a total", and it materially strengthens the *Against* column of the routed question at
   `:3403-3405`: this is the first time the enumeration-short-by-one pattern has produced a member
   unreachable by omission, where rounds 2–5 each produced one that was reachable. If any later pass
   touches `## Scope Boundary` for another reason, folding that sentence into the Against column is
   the cheap moment; it does not earn a pass of its own.
3. **`## Mitigation Folds`' opening pointer is stale again, and the fix is to stop naming a round
   number.** `:2756-2757` reads "the LATEST SPEAKING round — which since 2026-09-16 is
   `## Threat Model — 2026-09-16 (round 5)`"; round 6 now speaks. Harmless this time — I diffed all
   eight `desc` values against round 6's fences and they are byte-identical, so D8c passes — but
   this is the third round in which that one sentence has been stale, and it produced a real D8c
   refusal two rounds ago. The durable repair is a round-agnostic sentence ("the latest speaking
   `## Threat Model` round, whichever that is") plus the byte-identity claim, rather than a round
   number that every subsequent threat-model round invalidates. Same class as WI-131's
   single-literal gap, one document over.

### Carried-forward notes

Every still-open non-blocking note from every prior round, by name:

- **Threat model round 1 note 1 / round 2 note 3 / round 3 note 3 / round 4 note 5 / round 5 note 4
  / round 6 note 2 (the exit attestation's redaction reminder is absent from
  `docs/lint-vault-live-baseline.md` §4's own bytes)** — STILL OPEN, re-deferred for the same
  correct reason: §4 is conductor-owned and outside the builder's write authority, so it has no
  Implementation-Plan task to land in and a fence pointing at one would be a fiction. The
  conductor's, at the ship door.
- **Threat model round 1 note 2 / round 2 note 4 / round 3 note 4 / round 4 note 6 / round 5 note 5
  / round 6 note 3 (`apply_fixes:994` prints `str(exc)` to stderr)** — STILL OPEN as a deliberate
  non-change. The handler set does not widen, so no new content reaches that channel, and it is
  pinned as a message equality at `tests/test_lint_vault_fix_gate.py:123-125`.
- **Threat model round 2 note 1 / round 4 note 7 / round 5 note 6 / round 6 note 4 (M3's wall
  universe is ONE module)** — a standing scope ruling, not an open note; routed against rather than
  re-litigated. Nothing in this round widens it.
- **Threat model round 5 note 3 / round 6 note 5 and my own round-5 non-blocking note 2 (the two
  stale bare-line cites inside SIGNED criteria: AC-3's `derivations.py:31` where `SCRIPTS_ROOT` is
  at `:33`, and AC-5's "A SIXTH CENSUS READER" label against a body that says "a fifth reader")** —
  STILL OPEN and correctly not actioned. I re-confirmed `SCRIPTS_ROOT` is at `:33` this round. Both
  are WI-215 re-anchoring nits, neither changes what a builder implements, and fixing either would
  invalidate a set Dave signed on 2026-09-15.
- **Data audit round 2's two carried items** — both STILL OPEN and both correctly outside the spec:
  the build-start re-grounding should re-run AC-5(b)'s five-row comparison before the first edit
  (the baseline is now six days old and the vault churns weekly — I re-ran the comparison against
  HEAD this round and it is GREEN, which is a snapshot fact and not a standing one), and the exit
  half of A7's bracket has no battery wall by construction and lives at the conductor's ship door.
- **The routed sufficiency call (`## Scope Boundary` `:3384-3418`)** — OPEN with Dave or the
  conductor, carried forward past promotion. It is a declared, bounded, costed scope decision, not a
  spec gap; if the answer is "close it", the closure is one more CLOSED shape in Task 7's existing
  census graded by Task 9's existing clause (iv), with no new check, no fifth derivation and no
  count moved.
- **This round's three minor notes above** — new, and the first is the one worth actioning if any
  later pass opens this document for another reason.
- **All other prior notes** — my round-1 notes 1–5, round-2 notes 1–3, round-3 notes 1–2, round-4
  note 1; threat-model round 3 notes 1–2 and round 4 notes 1–2; architect round 4 notes 1–4; the AC
  red-team's label slip — all CLOSED, each in the round that closed it, with the label slip
  re-carried above only because it sits inside a signed criterion.

```verdict
gate: spec-reviewer
verdict: PROMOTE
date: 2026-09-16
model: claude-opus-5
note: Round 5's blocking issue is CLOSED and closed wider than raised — I enumerated seven surfaces, the seventh pass swept its own claim's vocabulary and returned twelve plus `## Scope Boundary` as the thirteenth, and I re-read eight at their own bytes rather than accepting the list; every one states that clause (iv) is total over omission shapes that NAME the path and not over ones that OBTAIN it unnamed, that `_resolve_vault_path:104-114` (re-grounded at `:111`, `ENV_VAULT_PATH:75`, `_is_unconfigured:86-101`) is a THIRD source, that the residue is an omission shape the deliberate-act bound does NOT cover, and that M5/M6/M7 are load-bearing again — with the falsified wording quoted and dated in place, the two HEADINGS carrying the claim qualified, and, decisively, the escalate-rather-than-REVISE instruction at `:3378-3383` now scoped to the deliberate-act level and stating in terms that an omission-level finding is a legitimate REVISE. The routed sufficiency call remains OPEN with Dave or the conductor and does not block: my round 5 pre-committed to exactly that ("issue 1 stands alone and this item can still come back for round 6 on that basis"), the residue is declared on every surface and costed at `:3405-3418`, and I confirmed the two facts that decide the cost (`module_import_uses:847` reports the ROOT module so the import-allowlist shortcut genuinely cannot separate M1's required `SKIP_REASONS` import from a repository import; `_is_unconfigured` swallows blank/whitespace/`"."` so the rule must be zero constructions) — a declared, bounded, costed decision with a named owner is a scope boundary, and because the closure is one clause inside machinery Task 7 already ships, a "close it" answer arriving later is an amendment rather than a re-spec. Mechanics re-run rather than inherited: sixteen canonical tasks with unique ordinals 1-16 and sixteen well-formed `verify:` declarations (fourteen test names, Task 1 `baseline`, Task 16 `hand-run`), no verify command writing outside write_authority, Write-Targets coverage exact both ways across nine builder fences with both precondition paths in HEAD and read, `OPEN: None`, all eight fold `desc` values diffed byte-for-byte against the LATEST SPEAKING round — which is now round 6, not the round 5 the folds' prose names — and all eight matching, every `landed:` ordinal resolving, and all eight `design`/`work` quotes read where they claim to sit and found faithful, with M8's `design:` correctly moved while its `desc` correctly did not. Nothing touches `## Intent` or `## Acceptance Criteria`, which I re-read in full, so `ac_hash: 973d7a08f068` stands and no re-sign is owed; AC-5 re-derived GREEN against HEAD (821/835 delta `+14`, 315/315, 19/19, 0/0, 0/0) with AC-5(a)'s shape predicates re-run against the committed bytes. Three non-blocking notes, and the first is a fresh find five rounds missed: VD-4's falsifiable artifact says `grep -rn "run_lint" tests/` returns nothing, and it returns two hits — `tests/test_vault_path_required.py:_run_lint_vault:344` and its call at `:367` — which is the very helper Design §7 `:1963-1966` cites by name, so two live surfaces disagree about one grep. I resolved it at the code instead of preferring a surface: that helper subprocesses the script with `OBSIDIAN_VAULT_PATH` scrubbed and asserts only on returncode and stderr, and all three invocations exit at `main`'s no-vault guard before `run_lint` runs, so VD-4's CLAIM is true and I grounded it — only the parenthetical is wrong, it grounds no task, and AC-4(d) orders the stdout capture on its own terms. Note 2 is the seventh pass's next-level census, which claims exactly one member and is short by one: I verified `scripts/migrate_person_to_discuss.py:main:158` takes no parameters, defaults `--vault` to `os.environ.get('OBSIDIAN_VAULT_PATH','')` at `:165` and reaches `vault_io.write_note` at `:109`, and equally that it is NOT a route — `parse_args:174` reads pytest's own argv and `dry_run = not args.apply` at `:186` guards the write at `:105` — so it sits inside the deliberate-act bound and I cite and escalate rather than REVISE, exactly as that paragraph now correctly instructs; it belongs in the Against column of the routed question as the first short-by-one member unreachable by omission. Note 3 is the folds' round-number pointer going stale a third time, harmless here and repairable once by making the sentence round-agnostic. I PROMOTE rather than emit a sixth REVISE because all three remaining findings are dated prose measurements that decide nothing a builder does, because the regress signature I named last round is the reason to stop rather than to take the next rung, and because the one substantive question left is not mine or the spec-writer's and is already routed to its owner with its cost on the table.
```

## Adversarial Review — 2026-09-16 (round 6)

Cold-start, different model from spec-reviewer (Sonnet, vs. Opus for spec-reviewer and threat-modeler).
Read the document end-to-end from line 1, including every archived-round pointer, all six prior
Adversarial Review rounds (all PROMOTE), and — with particular weight, since it is new since my last
read — Threat Model round 6 and Spec Review round 6 in full, plus `## Scope Boundary` as the seventh
spec-writer pass left it, read directly rather than through either gate's paraphrase.

**The one question:** has this spec, or the prior gates' verdicts, been steered by a prompt injection
planted in the untrusted content the gates read? Two surfaces carried forward from my own round-5
finding, both re-examined at the current bytes rather than assumed settled:

1. **`## Scope Boundary`'s escalation clause, now restated** (`:3373-3383`). Round 5 traced this
   clause's origin to Spec Review round 4 minting its own discipline against a regress it diagnosed in
   itself — not planted steering — and found the mechanism worked correctly (round 5's gates verified
   the trigger at the code before honoring it, and split the finding rather than being suppressed by
   it). The seventh pass edited the clause since then, and I re-read the edit directly at `:3378-3383`
   rather than trusting threat-model round 6's or spec-review round 6's characterization of it: it now
   reads "Any gate finding at the DELIBERATE-ACT level should cite this paragraph and escalate rather
   than REVISE — and that instruction is scoped to that level and to nothing else: a finding at the
   OMISSION level is NOT covered by this bound, is a legitimate REVISE." This edit *narrows* the
   clause's reach rather than widening it, and it does so by naming the exact class of finding
   (omission-level) that the untouched 2026-09-15 wording would have wrongly suppressed — the opposite
   of what a steering injection would do to itself once caught. Both round-6 gates then demonstrated
   the narrowing works as written: threat-model round 6 found a second census member
   (`scripts/migrate_person_to_discuss.py:main`) and *did* cite-and-escalate rather than REVISE, but
   only after independently checking it was deliberate-act-shaped (two acts: a constructed `sys.argv`
   past `parse_args:174`, then an explicit `--apply` against the `dry_run=True` default) — i.e. it
   applied the clause's own stated test rather than treating the clause as a blanket instruction to
   stand down.
2. **This round's new material generally** — Threat Model round 6 and Spec Review round 6, both dense
   and citation-anchored. I re-resolved a sample of the load-bearing claims myself rather than taking
   either gate's word: `scripts/migrate_person_to_discuss.py:main:158` takes no parameters, defaults
   `--vault` to `os.environ.get('OBSIDIAN_VAULT_PATH', '')` at `:165`, and reaches `vault_io.write_note`
   at `:109` — matching both gates' description exactly, including the two-deliberate-acts argument for
   why it is not a route. Grepped the full document again for injection-style override phrasing
   (`ignore the previous`, `pre-approved`, `emit PROMOTE`, `should not block`, `disregard`,
   `rubber-stamp`, `SYSTEM:`) — the only hits are at `:4516`, `:5583-5584`, `:6187-6188` and
   `:6875-6876`, all prior gates' own methodology notes describing that same grep (mine included), none
   a live specimen addressed to a reviewer.

Neither this round's spec-writer edits nor either gate's verdict prose argues that a reviewer *should
not* find something, asserts pre-approval, or is addressed to "you, the AI" outside the one
already-traced mechanism above — which this round's edit made narrower, not broader. The spec-reviewer's
PROMOTE reads as an independent, code-checked judgment: it found and disclosed a fresh defect on its own
initiative (VD-4's grep claim is false even though the underlying diagnosis holds) and a second
short-by-one census member, neither of which a steered reviewer angling for PROMOTE would have surfaced.

```verdict
gate: injection-hunter
verdict: PROMOTE
date: 2026-09-16
model: claude-sonnet-5
note: Read the full document, all six prior Adversarial Review rounds, and this round's new material (Threat Model round 6, Spec Review round 6, and `## Scope Boundary` as the seventh pass left it) end-to-end at the current bytes. The one surface my own round-5 review traced as injection-shaped — `## Scope Boundary`'s escalate-rather-than-REVISE clause — was edited this round to narrow rather than widen its reach (`:3378-3383` now scopes it explicitly to the deliberate-act level and states an omission-level finding "is a legitimate REVISE"), and threat-model round 6 demonstrated the narrowed clause working as written by applying its own test (two deliberate acts) before citing-and-escalating on a fresh census member rather than treating the clause as a stand-down order. A repeat grep for override-style phrasing (ignore the previous / pre-approved / emit PROMOTE / should not block / disregard / rubber-stamp / SYSTEM:) across the whole document returns only prior gates' own methodology notes describing that grep, no live specimens. Spec-review round 6's PROMOTE self-disclosed a fresh defect (VD-4's grep claim) and a second short-by-one census member rather than suppressing them, which is the opposite of steered behavior. No manipulation detected.
```

## Code Review — 2026-09-16 (round 2)

Cold-start, build-exit gate, SECOND round at this door — the first round's section is above and its two
findings (B1 blocking, N1 a Note) are the carry-forward. **This spawn also has no shell** (Bash is not
granted and `ToolSearch` resolves no shell tool), so nothing below is a claim about an EXECUTED floor;
every statement is read off the tree's bytes with its predicate stated. The Build Log's 689-at-both-ends
claim for the revision round and mutation 15's observed RED are the build's, re-runnable but not re-run
here.

**Trigger check.** FIRES — `scripts/lint_vault.py`, `tests/test_fixture_vault.py` and
`tests/test_lint_vault_fix_rules.py` all changed since the previous round. Not doc-only.

### B1 — CLOSED, by the stronger of the two routes offered

The fold took route (i) — the reader MOVED — and then disclosed the one thing route (i) could not
absorb. Every predicate the round-1 finding named, re-run by hand:

- `census_auto_fixable_rows` is defined at `tests/test_fixture_vault.py:166`, fifth among the census
  readers in the module Design §9, Task 14, the write-target fence and AC-5(b) all name
  (`census_class_rows:122`, `census_pool_rows:140`, `census_meta:145`,
  `census_auto_fixable_rows:166`, `census_identity_residue:432` — D5's own list, checked member by
  member). `grep census_auto_fixable_rows tests/` now returns one definition and four use sites, none
  of them a second copy.
- The `CATEGORY_ORDER` collision I identified as real was resolved the way I suggested was cheapest —
  injected from the caller that already holds the loaded module
  (`tests/test_lint_vault_fix_rules.py:_census_rows:1548-1550`, the single line holding the seam) —
  and the residual deviation it forces, the keyword-only `categories` parameter, is recorded as
  **D5** rather than left silent. That is the discipline B1 was actually about.
- The three document surfaces now agree with the tree: the Build Log's totality sentence reads
  "Five deviations" (`:2652`), Task 14 states the landing site AND the signature deviation
  (`:2561-2564`), the `tests/test_fixture_vault.py` write-target fence says LANDED with the signature
  named (`:2879`), and Design §9 carries a build note rather than being retro-edited (`:2056-2063`) —
  which is the right treatment, matching how D1 leaves Design §5's literal tuple standing.
- D5's claim that the deviation touches no signed promise is TRUE and I checked it against the fence
  rather than the prose: AC-5(b) requires the reader to land in `tests/test_fixture_vault.py`, to ride
  `CENSUS_DIGEST`, and to read `CATEGORY_ORDER` "from the loaded module rather than re-spelled". All
  three hold; the criterion pins no signature, and a `categories` DEFAULT in the census module would
  have been the re-spelling it forbids. Keyword-only and default-less is the stronger answer.

### N1 — CLOSED

`scripts/lint_vault.py:625-630` carries the comment Task 3 prescribed, and its reasoning matches the
code: `check_timeline` walks `idx["meetings"]` / `idx["persons"]` (`:638`, `:666`) and never `files`,
and a `read_error` `VaultFile` keeps `entity_type == ""`. The Build Log records it as a missing task
artifact rather than inflating the deviation count — correct.

### What the fold itself landed on, checked for its own defects

The new cross-module import (`tests/test_lint_vault_fix_rules.py:100`) is the fold's only structural
addition, so I ran the two walls it could plausibly weaken. It does not: `tests/test_fixture_vault.py`
names neither `subprocess` nor `runpy` in any form, so M6's import clause is unweakened even
transitively, and every module it does import (`tests.ac_interpreter`, `tests.derivations`,
`tests.fixture_vault`, `tests.support`) was already a DIRECT import of the check module — the fold
opens no capability that was not already reachable. The import is also safe under the conveyor's
foreign `-S` interpreter: `ensure_project_interpreter` re-execs at
`tests/test_lint_vault_fix_rules.py:60` before line 100 is reached, and in the delegated child
`runtime_deps_importable()` is true, so `tests/test_fixture_vault.py:27`'s own call is a no-op rather
than a second hop. The reader's strip rule survives the move unchanged and I traced it against all
five census shapes: the regex anchors the parenthetical OUTSIDE the backticked span, so
`Empty name (suggest: '…')` and `[[…]] doesn't resolve (fixable → [[…]])` keep their own parentheses
while `(structural)` / `(timeline)` / `(links)` come off, and a non-category trailing group is
re-appended rather than dropped. Task 8's two skip-reason wall sites both survived the +51-line shift
intact, still at two declared homes with their non-vacuity clauses (`:569-580`, `:1388-1395`).

I also re-read the parts of the build the fold did not touch but could have disturbed —
`read_vault:121-190`, the record cluster `:865-952`, `apply_fixes:955-1199`, `FIX_SUMMARY_LABELS` and
`run_lint:1370-1442` — and they are byte-for-byte the design I signed off on in substance last round:
the two credit points still sit AFTER their own `write_note` returns (`:1126`, `:1158`), `_release` is
still by `id()`, both handlers still iterate `undecided`, and the summary print is still unconditional
under `do_fix` with the pre-fix `unreadable_count` bound before the re-scan rebinds `all_files`.

### Note

**N2 — a line citation the build's own edits invalidated, in shipped bytes.**
`tests/test_lint_vault_fix_rules.py:98-99` says "`tests/test_fixture_vault.py` already carries a
cross-module test import of this shape (`:1296`)". Line 1296 of that file is a comment inside the
phone-literal battery; the cross-module test imports are at `:1362`, `:1363`, `:1448` and `:1482`. The
substantive claim is TRUE (the precedent exists, four times over), and the citation was almost
certainly accurate when Task 14 wrote it (`:2571-2572` carries the same number) — this item's own
+51-line insertion into that file is what moved it. Worth one edit to the comment and to Task 14's
parenthetical when something else is open; not worth a round on its own, which is why it is a Note and
not a blocker.

### Summary

The revision round did exactly what B1 asked and chose the harder half of it: the prescribed artifact
moved to the prescribed module, the collision that forced the move was resolved without minting the
second loader the tree forbids, the one residue that could not be absorbed is recorded as D5 with its
own mutate-and-observe row, and the four surfaces that described a tree which had not shipped now
describe the one that did. No blocking finding survives, and the fold introduced no new one — the only
thing it left behind is a stale line number in a comment.

```verdict
gate: code-reviewer
verdict: PROMOTE
date: 2026-09-16
model: claude-opus-5
note: B1 is closed by the stronger route — `census_auto_fixable_rows` now lives at `tests/test_fixture_vault.py:166`, fifth among the census readers, imported by the check module and graded through that import, with the forced signature residue (`categories` keyword-only, no default) disclosed as D5 and the Build Log's count, Task 14, the write-target fence and Design §9 all corrected so the four surfaces and the tree agree; N1 is closed at `scripts/lint_vault.py:625-630`; the fold itself opens no hole I could find — the new cross-module import names no subprocess-capable module and adds no transitive capability the check module did not already import directly, the strip rule and Task 8's two wall sites survived the move intact, and AC-5(b) pins no signature so D5 touches no signed promise — leaving one Note only, a stale `:1296` cite in the new import comment that this item's own line shift invalidated.
```

## Test & Observability Review — 2026-09-16 (round 2)

Same cold-start, same no-shell constraint: what follows is about what the test code SAYS it drives,
read off the bytes. Round 1's fence on this dimension was PROMOTE with one Recommended; this round
re-reads the fold for anything that moved coverage or the operator channel.

**Trigger check.** APPLIES — still not a pure refactor; the production paths round 1 enumerated
(`read_vault`'s recording arm, `check_structural`'s `unreadable_note` branch, `apply_fixes`' four
buckets and two records, `run_lint`'s unconditional summary) are unchanged and still ship on a tool
pointed at a live vault.

**1. Tests exist — and the fold kept the grading honest rather than merely green.** The one way this
move could have cost coverage is the obvious one: a reader that relocates while the fixture keeps
driving a stale copy. It does not. `_check_the_reader_predicates_reach_their_claimed_shapes`
(`tests/test_lint_vault_fix_rules.py:1702-1745`) drives the moved reader THROUGH THE IMPORT at `:1731`
and its docstring says so, and `_census_rows:1539-1550` — the only other call — does the same, so
there is no second implementation for a mutation to miss. The build proved that the expensive way
rather than asserting it: mutation 15 inverts the strip rule IN ITS NEW HOME and reports the exact
`Left contains 1 more item: {'Missing sections: … (structural)': 821}` that the `:1737` equality would
produce — a discriminating RED, not a generic one. Everything round 1 credited still stands: four
buckets driven non-empty and asserted non-empty, the observed decline-guard set equated to the shipped
`DECLINE_GUARDS`, the M4 mixed-file plant patching the SECOND write to raise, the tie-break plant, the
unreadable note's four legs with the linker/meeting discriminator and the never-written/never-moved
byte-compare across both mutating doors.

**2. Logging at WARN/ERROR.** Unchanged and still closed: `read_vault`'s `except Exception` records
`read_error=UNREADABLE` and surfaces one non-auto-fixable issue; both `apply_fixes` handlers print one
line per file to stderr (`:1186`, `:1196`) while the machine-readable records carry bounded reasons
(`type(exc).__name__`); the delivery line is unconditional under `--fix` (`run_lint:1427`) with
`unreadable_count` bound at `:1387`, before the re-scan. The fifth label is still the imported
`UNREADABLE` (`:1360`), so the printed word and the recorded reason remain provably the same word.
AC-4(d) still asserts against REAL captured stdout across two planted vaults with a variation clause.

**3. Alerts wired.** N/A and unchanged — an operator-invoked CLI with no launchd/cron surface and no
outbound channel. The post-ship A7 exit run remains the one act outside any battery, declared as a
conductor ship condition with its commands and figure names committed as bytes and asserted
presence-only by `_check_the_exit_obligation_is_committed_as_text` (`:1674-1699`), which is correctly
silent about the `exit` cells the conductor fills at close-out.

**4. Invariant registration.** N/A, skipped rather than failed — `**/invariants.py` still returns
nothing in this tree; v1 registry scope is orchestrator-only and this project ships no registry, so no
`## Observability Waiver` is owed.

**One Recommended, carried forward unchanged and still non-blocking.**
`test_the_fix_summary_prints_even_when_nothing_is_auto_fixable` (`:1385-1407`) still drives
`run_lint(..., do_fix=True)` twice and still depends on the first pass converging; the fold added a
`# converges` comment at `:1394` but no assertion, so the premise is now stated rather than asserted.
One line checking that the first pass's own summary reported a non-zero `repaired` would close it. The
check's subject — the print surviving an empty fixable set — remains directly asserted, and the
`unreadable` figure assertion at `:1405` is the part that matters most, so this does not block.

No blocking findings on this dimension, and the fold moved nothing here that was not strengthened by
being driven through an import instead of a local definition.

```verdict
gate: test-observability-checker
verdict: PROMOTE
date: 2026-09-16
model: claude-opus-5
note: The fold's only coverage risk — a relocated reader graded against a stale copy — is closed by construction and proved by mutation 15's discriminating RED: `census_auto_fixable_rows` has exactly one definition and both its WI-235 fixture and its production caller reach it through the import; every production path still carries a happy case plus at least one failure mode, the item's own subject (the silent swallow) stays closed with a bounded-reason record and an unconditional operator line asserted against real captured stdout, alerting is N/A for an operator-invoked CLI with the post-ship A7 attestation committed as bytes and asserted presence-only, and invariant registration is N/A for a project with no registry — the single Recommended (the still-unasserted single-pass convergence premise, now commented at `:1394` but not checked) is carried forward and does not block.
```

## Retrospective — 2026-09-16

### Was the spec accurate?
Mostly, but it took real work to get there: 5 spec-review REVISE rounds (plus earlier AC Red-Team
and Architectural Review bounces) before PROMOTE, tracing one escalating containment-wall gap
(M5 → M6 → M7 → M8) and one genuine truthfulness error (round 1's AC-4(b) contradicting Dave's own
signed criterion). Once frozen, the build tracked the spec closely — 16/16 tasks landed as specced —
but five forced deviations (D1–D5) surfaced collisions the spec's prose hadn't anticipated, and one
of those (D5, a module-placement collision) was *initially left unrecorded*, triggering a code-review
REVISE of its own.

### Edge cases that surprised us
- **D3**: 3 of the 5 "decline" guard branches turned out unreachable through the real detector
  pipeline — only found by trying to drive them end-to-end, not flagged in the spec's Edge Cases.
- **M9**: the containment mutation-testing wall was itself blind to one mutation class — a hand-broken
  `_temp_vault` door stayed green because the check read syntax only and never executed the door.
- **Round 5's `OBSIDIAN_VAULT_PATH` finding**: `obsidian_schemas`' own env-var fallback is a live route
  to the real vault that bypasses the entire containment wall without ever naming it — found deep into
  threat-modeling, not anticipated by the original Edge Cases, and left explicitly OPEN (routed to
  Dave/conductor) rather than force-closed under a 9th mitigation.
- **D5**: the census reader's home collided with a "no second `lint_vault` loader" rule the spec's
  Design §9 hadn't foreseen, and shipping it in the wrong module was the code review's one blocking
  finding.

### What would have shortened the build?
- The AC-4(b) contradiction (round 1: design's stated mechanism disagreed with the criterion Dave had
  signed) should have been caught at AC sign-off, not the first spec-review pass — a
  signed-AC-vs-mechanism cross-check before freeze would save a round.
- A firmer Design §9 module-placement rule for new test-support readers (name the home explicitly,
  the way it names everything else) would have prevented D5/B1.
- The containment-wall threat-model arc (M5–M8) reads like a pattern worth generalizing: each round
  found "the next level of the same escape" rather than a new threat. A dedicated "where can the live
  vault path enter — argument, default, env var, subprocess boundary" checklist item in the spec-writer
  or threat-model role could shortcut the round-by-round discovery next time this shape recurs.

### Recommended follow-ups
- Consider a work item (or a threat-model-role instruction update) generalizing the M5–M8 pattern into
  a standing checklist: "enumerate every route a live-path string can reach a write (arg default, env
  fallback, subprocess boundary, disguised binding name) before declaring containment total" — this is
  the second time this class of escape has been found late (the doc cites this tree having been "bitten
  by the identical generator... twice under `tests/`" already).
- The open `OBSIDIAN_VAULT_PATH` sufficiency question is routed to Dave/conductor per the Scope Boundary
  ruling — worth confirming it gets picked up rather than silently dropped, since it's a real live-vault
  escape route this item found but did not close.
- No demo section exists in this document (it goes straight from Code Review / Test & Observability
  round 2 PROMOTE to `stage: done`). Worth flagging to the conductor as a process gap rather than
  assuming it happened elsewhere.

### Did the build serve the original intent, or the spec's drift of it?
Serves the intent. The Intent's sharpened 2026-09-10 form — an operator must know, from what the tool
tells them, exactly what it repaired, declined, and could not read, with every rule proved against
real-shaped notes first — is what AC-3 and AC-4 directly discharge, and the shipped `--fix` path
(bounded `UNREADABLE` reporting, kept-in-index unreadable notes, four-bucket per-issue accounting,
an unconditional cross-checked summary line, a derived and mutation-tested rule set) matches it point
for point. No drift found between what was signed and what shipped.

### Post-done defects
None. The document reaches `done` cleanly after both round-2 gates PROMOTE. Two items are explicitly
left open past `done` as declared ship conditions rather than defects: the A7 exit obligation (conductor
must re-run `--report` on the live vault and fill the baseline doc), and the `OBSIDIAN_VAULT_PATH`
sufficiency question. Neither warrants an eval-ledger defect record — both are tracked, not discovered.

No build-earned lesson proposed for `LESSONS.html` this round — the build's own scars (D1–D5, M9) are
real but ordinary spec-vs-implementation friction, not a corruption or a lost-time incident; the closest
candidate (the env-var containment escape) is already captured in-document as an open Scope Boundary
item rather than a shipped defect, so it doesn't clear the "cost real time or shipped real corruption"
bar on its own.
