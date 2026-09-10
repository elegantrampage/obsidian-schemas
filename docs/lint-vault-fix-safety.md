---
id: WI-026
title: "lint_vault.py --fix safety: route through the guarded primitive + a test floor for scripts"
project: obsidian-schemas
stage: exploring
created: 2026-07-05
last_touched: 2026-09-10
stage_changed: 2026-09-10
touched_by: session
tags: [scripts, write-safety, testing]
depends_on: ["WI-004", "WI-020"]
transitions: ["idea>exploring@2026-09-10@porter"]
review_level: L3
review_level_provenance: selector
---

# lint_vault.py --fix safety

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
why: A7 — this item's acceptance was 100% hermetic in its first draft, which is LESSONS #27 and the WI-064 scar (five green fixture tests, an independent reviewer clear, and both real defects surfacing only on real data). `lint_vault.py` is the canonical instance of a tool whose job is the whole corpus: a linter's characteristic failure is the false positive on the shape nobody drew a fixture from, and that shape lives in the tail no 53-note fixture contains. This fence is the ENTRY half of the bracket that fixes it, and entry is the half that can only be captured NOW: this item changes what `read_vault` RETURNS, so it moves the live counts of all five stem-keyed checks (`person_company_not_found` :463, `meeting_attendee_not_found` :482, `company_people_link_broken` :497, `broken_wikilink` :513, `orphaned_note` :722), and after the build the old code's numbers no longer exist to be measured. It also settles the question this document previously routed to Dave as a sign-off judgement call, which was the wrong channel — Dave cannot know how many of his notes are undecodable and one command can. THE ARTIFACT DOES NOT YET EXIST; this is a MEASUREMENT the conductor performs, not a verification of something already in HEAD. SHAPE CONTRACT, on the `docs/company-name-corpus-audit.md` precedent — every block a complete, self-contained, re-runnable command with its literal argv, its verbatim stdout, and the tree's 40-hex HEAD SHA, so any reader can re-execute it and contradict it: (i) `## 0. The run` — `scripts/lint_vault.py --vault $VAULT --report` on the current vault, verbatim; (ii) `## 1. The five auto-fixable counts` — one row per rule, to be compared against `docs/vault-shape-census.md:272-281` (821 / 315 / 19 / 0 / 0 as measured 2026-09-07); a divergence is not an error, it is the staleness signal AC-5 exists to raise; (iii) `## 2. The five stem-keyed check counts` — the pre-change baseline for each of the five checks listed above; (iv) `## 3. The undecodable scan` — a standalone count of paths under `read_vault`'s own walk (`vault_path.rglob("*.md")` minus `should_skip`) for which `read_text(encoding="utf-8")` raises, with the count and NOTHING ELSE (no filenames, no bytes — the privacy wall reaches this artifact the way it reaches the census); (v) `## 4. Post-build attestation` — declared here as a NAMED EMPTY SECTION carrying the exact command and the exact figure names the exit run must fill, so the conductor's ship act is one command rather than a design question. THE EXIT HALF IS A SHIP CONDITION, NOT A FENCE, and deliberately so: `kind: precondition` is probed for git-HEAD membership BEFORE the build spawn (`work_item_linter.py:167-171`), so it cannot by construction carry an act that happens after the build, and a `kind: command` AC would mint a workshop command-registry entry from inside a project item and point an automated battery at Dave's live vault. The exit run is therefore the conductor's act at `ready → done`, appended to this same file as an attestation on the WI-022 precedent (`docs/company-name-corpus-audit.md:30-38`, "post-build, at the quiesce"), and this item is not done without it. `--report` and never `--fix` on both runs: mutating Dave's vault is a separate authorization this item does not ask for.
```

**Handoff note on builder write targets (the spec-writer types the `kind: file` fences).** Beyond
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
desc: EVERY DETECTOR THAT CAUSES A WRITE is pinned, in both directions, against the frozen corpus and against planted subjects — and the pinned set is the SEVEN write-causing checks, not the five auto-fixable ones. THE PINNED SET, stated once: the five members of AC-1's derived auto-fixable set, PLUS `garbage_candidate_person` (`:673-683`) and `garbage_candidate_company` (`:685-719`), which are INFO and NOT auto-fixable but are the sole input to `quarantine_garbage` (`:1218` → `:1112-1144` → `vault_io.move_note` `:1140`) and therefore the checks that RELOCATE a note. Three legs. (a) NO FALSE POSITIVES ON REAL-SHAPED DATA — running the full battery (`read_vault` → `build_indexes` → all five `check_*` functions) over a materialized copy of the frozen corpus with NOTHING planted, the set of `(filename, check)` pairs whose check is in the pinned set equals a declared table in the test module, and that table's only non-empty member class today is `meeting_missing_from_timeline`, one issue per (meeting, attendee) pair the manifest declares — so the other SIX are asserted to fire ZERO times across all 53 notes, INCLUDING the three skip specimens and the diacritic, hyphenated, postal-address, digit-named and stem-divergent members. The two `garbage_candidate_*` zeroes are real rather than accidental: `auto_created` occurs nowhere in the corpus and both arms gate on a truthy `auto_created` (`:245-253`, `:691-694`). (b) EVERY MEMBER OF THE PINNED SET FIRES ON ITS OWN PLANTED SUBJECT — one planted specimen per member producing exactly one issue carrying that check id at exactly that path, including a planted `auto_created: true` stub person and a planted `auto_created: true` company with no website, no industry, no Notes, no People links, no referencing person and no timeline meeting; so leg (a)'s six zeroes are proved to be silence rather than blindness. (c) THE MOVE PREDICATE IS PINNED ARM BY ARM — `classify_person_tier` (`:233-283`) decides which person notes leg (b)'s quarantine arm relocates, and its definition is the SIX disjuncts its own docstring states (`:236-242`): auto_created false or missing; ≥2 meeting wikilinks in Timeline; non-empty To Discuss or Notes; ≥1 meeting AND a non-empty `emails`; ≥1 meeting AND a non-empty `company`; ≥2 `^### ` headings in Timeline. The test module declares one planted specimen per disjunct that is `active` BY THAT DISJUNCT ALONE — every other disjunct false — plus one specimen satisfying none, which must be `stub`; an implementation missing any arm returns `stub` for that specimen and is RED, which is the mis-classification that MOVES a live note. The enumeration is a declared NARROWING, not a derivation (the disjunction is four `if` statements over six conditions and has no table to iterate), so it is BOUND to the stated definition by syntax ON BOTH SIDES — the docstring alone does not hold the property this leg needs. A scan in `tests/derivations.py` returns TWO numbers for `classify_person_tier`: the count of `- ` bullets in its own docstring Constant (SIX today, `:236-242`) and the count of `return "active"` sites in its body (FOUR today, `:253`, `:276`, `:279`, `:282`), and the criterion asserts BOTH against the numbers the test module's arm table declares. The code-side count is the load-bearing half: a seventh arm added as a fifth `if …: return "active"` moves it whether or not the author touches the docstring, which the bullet count alone cannot see — the bullets stay at 6, the table stays at 6, and the untested arm ships. The bullet count is the other direction: a disjunct documented but never implemented. WHAT THIS BINDING DOES NOT CATCH, stated so the criterion promises only what it delivers: an arm added by widening an EXISTING `if`'s condition (`if meeting_count >= 2 or has_manual or fm.get("vip")`) moves neither number, because it adds no `return` site and no bullet. That residue is the price of a narrowing over a hand-written disjunction and it is bounded — six documented conditions across four returns — where the alternative is a derivation this shape does not admit. THE EQUALITY IN (a) IS OVER THE PINNED SET ONLY — the INFO/WARNING issues the corpus legitimately raises (`orphaned_note`, `person_no_email`, `person_not_in_company_people`, `parse_error` and the rest) are outside it, because pinning those would couple this criterion to every check in the file rather than to the seven that cause a write.
why: This is the half the item has never named and the half that can lose data. A detector that mis-fires does not produce a wrong report, it produces a wrong WRITE — and the worst of those writes is not a repair, it is a MOVE. That is exactly why the pinned set is seven and not five: the first draft of this criterion rested its whole justification on `--quarantine` relocating files off the same issue list, and then pinned only `auto_fixable=True` pairs — which excludes both `garbage_candidate_*` checks and leaves `classify_person_tier`, the predicate that decides which person notes get relocated, ending this item exactly as untested as it started. A criterion frozen by signature whose stated reason for existing is a hazard it does not cover is worse than one that admits the gap. Widening costs almost nothing: both garbage ids pin at zero on the corpus today for a structural reason, so leg (a) grows by two rows, and leg (b) by two plants. All seven check functions have zero tests today; the two reached at all are reached by a gate sweep that asserts nothing about what they decided. Leg (a) is the only assertion in the suite that would notice a detector that started firing on notes it should ignore, and the frozen corpus is the right subject for it: 53 notes whose shapes were MEASURED from the live vault rather than invented, carrying exactly the accents, hyphens, address-in-a-name and stem/name divergences that make a naive check over-fire. Leg (b) is what stops (a) being satisfiable by a build in which the checks return nothing at all — an empty issue set passes any "these six fire zero times" assertion, and the pairing is what makes the zeroes mean something. Leg (c) is the same argument one level down: leg (b) proves the quarantine check fires on an obvious stub, which a `return "stub"` implementation also satisfies; only the per-arm table can tell a correct classifier from a wrong-but-self-consistent one, and the cost of getting it wrong is a real note in `_quarantine/`. Its syntax binding is two-sided for a reason found by attacking the criterion's own wording: an earlier draft counted only the docstring's bullets and then claimed "a seventh arm added with or without a docstring line is RED", which is false of that mechanism — an arm added as a fifth `if …: return "active"` with no bullet leaves every number in the assertion unchanged, and the arm with the largest blast radius in the file would ship untested behind a green criterion. Counting the `return "active"` sites from the same scan is one more line and closes exactly that hole; the widened-condition residue that remains is named in the desc rather than papered over, because a criterion frozen by signature must not promise a guarantee its mechanism lacks — that is the same defect as blocking 2 above, one level in from scope and down at wording.
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
desc: The LIVE-VAULT BASELINE is committed, shaped, and cross-checked against the frozen census — the entry half of A7's bracket, read back off the tree rather than trusted. Four legs, all over `docs/lint-vault-live-baseline.md` (the second `kind: precondition` fence in `## Write Targets`, a conductor measurement that must be in git HEAD before the criteria are frozen). (a) PRESENT AND SHAPED — the file exists and carries the five sections the fence's `why:` names (`## 0. The run`, `## 1. The five auto-fixable counts`, `## 2. The five stem-keyed check counts`, `## 3. The undecodable scan`, `## 4. Post-build attestation`), and each of §0–§3 carries a `Command:` line, a fenced block holding the literal argv, a fenced block holding verbatim stdout, and a 40-hex tree SHA — the `docs/company-name-corpus-audit.md` shape, whose whole point is that any reader can re-execute the block and contradict it rather than take a number on trust. (b) CROSS-CHECKED AGAINST THE FROZEN CENSUS — §1's five counts are compared rule by rule against `docs/vault-shape-census.md:272-281` under `CENSUS_DIGEST`, so the ledger cannot be rewritten by the party it audits. Equal is green. A divergence is RED, naming the rules and BOTH numbers, and it is a staleness signal rather than a defect: it means the live vault moved since 2026-09-07 and this document's live-count argument needs re-reading before ship. TWO THINGS THIS LEG NEEDS THAT DO NOT EXIST YET, declared here as decisions rather than left as the builder's discoveries. FIRST, A SIXTH CENSUS READER: WI-016's four typed readers are `census_class_rows` (`tests/test_fixture_vault.py:121`), `census_pool_rows` (`:139`), `census_meta` (`:144`) and `census_identity_residue` (`:380`), and every one of them parses a `census-*` FENCE — none reads the auto-fixable table, which is a plain markdown table at `:275-281`. So this leg ships a fifth reader beside them, in the same module, parsing that table's rows into `(message shape, int)` pairs and raising on a non-integer count or a duplicate shape exactly as `census_class_rows` does; it rides the same whole-file `CENSUS_DIGEST` fixity, which is over the file's bytes and is unaffected by a new reader, so this is an addition and not a design question. It is a WRITE TARGET in `tests/test_fixture_vault.py`, which constraint 8 already makes a paired target for two other reasons. SECOND, A DECLARED SHAPE→RULE-ID MAPPING, because that table's key column is a MESSAGE SHAPE and not a rule id, so "compared rule by rule" has no join without one: `Missing sections: …` → `missing_body_sections` (emitter `:357-363`), `Attended [[…]] but it's not in Timeline` → `meeting_missing_from_timeline` (`:596-602`), `auto_created is string '…' instead of bool` → `field_type_mismatch` (`:341-347`), `Empty name (suggest: '…')` → `person_missing_name` (`:386-392`), `[[…]] doesn't resolve (fixable → [[…]])` → `broken_wikilink` (`:530-538`). Five hand-kept rows, which is acceptable at that size, and they are BOUND rather than merely written: the mapping's VALUE set must equal AC-1(a)'s derived rule set, so a sixth auto-fixable rule reddens this leg until someone decides whether the census covers it. THE MAPPING IS KEYED ON THE MESSAGE SHAPE AND NEVER ON THE TABLE'S PARENTHETICAL CATEGORY, and that is a finding rather than a preference: the census annotates `Empty name (suggest: '…')` as `(structural)` while the emitter's own category field is `"completeness"` (`:388`) and its check function is `check_completeness` — a mapping keyed on the parenthetical would mis-join that row. The census is digest-frozen, so the annotation is NOT to be corrected there; the counts are what the row carries and what this leg reads. (c) THE UNDECODABLE COUNT IS PRESENT, TYPED AND CLEAN — §3 carries an integer ≥ 0, and its STDOUT block contains no `/Users/` path and no `.md` filename, because the privacy wall reaches this artifact the way it reaches the census: the count is the finding, the filenames are the operator's business and never the repo's. (d) THE EXIT OBLIGATION IS COMMITTED AS TEXT — §4 exists and carries the verbatim command the post-build run must use and the literal names of the figures it must fill. Its VALUES are empty at battery time by construction, and the criterion asserts the section and its declared figure names are PRESENT, never that they are filled — the filling is the conductor's `ready → done` act, not the builder's.
why: This is the criterion that stops the acceptance set from being 100% hermetic, which is what the first draft of this document shipped and what LESSONS #27 and the WI-064 scar say never survives contact with real data. `lint_vault.py`'s correctness is DEFINED by its behaviour on 4,730 live issues across a real vault, and the failure that matters for a linter — the false positive on the shape nobody drew a fixture from — lives in the tail no 53-note fixture contains; ruff and ESLint both pair a fixture corpus with an ecosystem run for exactly this reason and this design was shipping only the first half. Leg (b) is the load-bearing one and it is not ceremony: this document's ENTIRE argument for covering all five rules rather than only the ones that fire rests on a five-row table measured on one day in a vault that churns, and nothing currently re-reads it. Leg (b) makes a drifted vault a RED with two numbers on the screen instead of a premise quietly rotting under a signature — the WI-042 staleness class, closed by a comparison rather than by remembering to look. It also names the two things it needs and does not have — a reader for the census's markdown table (the four existing readers are all fence-parsers) and a shape→rule-id mapping, since the table is keyed on message shapes — because an earlier draft of this leg said "read through WI-016's own census reader" and no such reader reaches that table; a criterion frozen by signature that names a mechanism which does not exist is a build-time discovery, and this one comes with a live trap worth spending three lines on: the census annotates the `Empty name` row `(structural)` while that emitter's own category is `"completeness"`, so a mapping keyed on the parenthetical instead of the shape mis-joins one row in five and the count it cross-checks is the wrong rule's. Leg (c) is why the artifact can exist in the repo at all. Leg (d) exists because an exit act that lives only in prose evaporates: committing the command and the figure names as bytes turns the ship step into a re-run, and its absence into something a reader can see. The entry measurement also settles, by execution, the question this document previously routed to Dave as a sign-off judgement call — how many of his notes are undecodable — which is AC-3's whole subject population and which no human can answer from memory.
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

**Given** a run in which every single `meeting_missing_from_timeline` repair quietly did nothing
because the caller never passed the meeting index — **when** the run finishes — **then** the summary
says "declined 315" and names the reason, instead of printing "Fixed 0 issues, refused 0", which is
byte-identical to what a vault with nothing to fix prints today.

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


