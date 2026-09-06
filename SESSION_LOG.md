# Session Log

## 2026-09-06

### Queue review ruled; the next manifest written (not launched)

`/review-queue` after WI-021's ship, every open premise re-verified against the tree and the live
vault (load re-measured: 1,147 people in 1.26s — perf un-park criteria still unmet). Dave: "I agree
with your logic. log the new queue ordering." **New `queue_order`: WI-022, WI-016, WI-023, WI-028,
WI-026, WI-025, WI-011, WI-009.** WI-022 leads as a live hourly LEAK (company.py:171's mangler +
the gate passing declared non-person types untouched; exocortex's transcript cron writes Company
entities). Staleness recommendations awaiting Dave's word: close WI-001 and WI-014 (superseded by
HAL9000 WI-061's vault-tracking shared repository), close WI-015 (superseded by WI-004's stamps +
`ExternalWriteConflict`), rewrite WI-007/WI-008's premises (their models exist, repositories do
not), and mint a small repair item for the three live notes whose filename stem ≠ stored name
(WI-021's parked defect 1; G4(b)). **Manifest** `state/manifests/queue-2026-09-06.yaml` — WI-022,
WI-016, WI-023 (no `needs`, so its D4a parks beside the others), WI-026 (needs WI-016); WI-028
deliberately held for the manifest after WI-023 ships. Validated with `load_manifest`; the
convention invocation resolves (bare `-m pytest` = 657, ac_python = the project venv). Launch
command in the file header; not launched. The WI-021 rounds drawer got the `archive-split:v1`
mark (workshop's adoption answer) — never run archive-split on WI-021.

**Staleness rulings executed (Dave: "close the items you suggest closing…").** WI-001 and WI-014
CLOSED as superseded by HAL9000 WI-061; WI-015 CLOSED as superseded by WI-004 — each carries a
dated Status line naming the superseding ship; stage stays `parked` because the pipeline has no
closed stage. WI-007's premise rewritten (the `Watch` model exists; the repository does not);
WI-008's Problem corrected ("hasn't been committed" → committed at `models.py:266`). **WI-029
minted** via the locked mint CLI: filename/name divergence repair — rename the three forked stems
through `vault_io.move_note` with the old stem as an alias, pin the stem/name invariant over the
corpus, and carry WI-021's booked hand repairs (the mis-typed book note, four untyped notes, three
unparseable fences). Queued after WI-011 per the review's ranking; Dave may move it.

### Manifest launched on Dave's word; WI-022 parked at D4a; WI-016 killed by a WI-327 grounds line

Launched `state/manifests/queue-2026-09-06.yaml` from `workshop-stable` through
`with-session-auth` (foreman pid 31828, own session, run record
`obsidian-schemas-queue-2026-09-06-2026-09-06T064158Z`). **WI-022 leg: 6 spawns, ideation → ac-red-team
3 rounds → PROMOTE → parked at D4a** (`ESC-WI-022-exploring-awaiting-ac-signoff-340c47f6`, four ACs
drafted in `docs/company-stub-parity.md`). The leg's `## Write Targets` fence declared the WI-300
grounding artifact `docs/company-name-corpus-audit.md` — with a **590-character `grounds:` line**.
That is workshop WI-327's shape exactly: the linter floor went RED (1 error), and the foreman's next
entry, WI-016, died at the Step-0 pre-flight floor with 0 spawns as a `tooling-fault`; run status
`faulted-stop`. Conductor hand-fix per the WI-327 idiom: `grounds:` shortened to 110 chars, every
dropped word moved into the fence's `why:`; linter back to 0 errors, floor 657 green. The
tooling-fault record answered ("Investigate the fault", note names the cause) and dismissed so the
next pass is not blocked; specimen reported to the factory session for WI-327's count.

**Conductor grounding act (WI-300, before the AC frame): `docs/company-name-corpus-audit.md`
written.** Live vault walked read-only: 2,160 `type: company` notes (2,159 live + the template).
**No proposed Tier-1 branch — including the widened path-hostile set — refuses a single live
name**, so AC-2's membership and AC-1/AC-4's "no legitimate name becomes unwritable" premise hold on
the whole corpus. Mangler census: `&` in 8 names, `.` in 3 — the classes AC-1's table must preserve.
D4 sized: 7 double-space residue notes (3 live, 3 quarantined, 1 merged-dupe) plus 2 quarantined
truncations. Consumer scan (verbatim stdout + 40-hex HEADs in the artifact): HAL9000's generic
`POST /api/entities/company` route is the only live caller of `CompanyRepository.create_stub`;
**exocortex carries its own byte-identical copy of the mangler** (`ingestion/stages/company.py:157`)
and writes company notes via `write_markdown_file`, never via create_stub — so the "stray `@Bausch/`
directory" leak is not reachable from exocortex today (its copy strips `/`), the hourly leak it does
have is `&`/`.` stripping, and deleting the mangler here does not touch it. Named as the follow-on
that actually stops the leak (exocortex-side, outside this project's write authority); WI-022's
scope unchanged.

**WI-030 minted** (idea) on the factory session's request: export the lint_vault surface
(`read_vault`, `build_indexes`, `run_lint`, `VaultFile`, `Severity`) from the installed package or
publish a CLI — orchestrator's `bin/vault-health-check.py:21` and `bin/batch-contact-context.py:29`
reach `scripts.lint_vault` by sibling path (orchestrator WI-159's boundary lint); workshop allowlists
the two reaches citing WI-030. Minted at the quiesce, after the foreman exited. Not in `queue_order`;
Dave's word for its slot.

Open: Dave's D4a on WI-022 (the artifact must be in HEAD first — WI-300's door), then relaunch the
manifest so WI-016 resumes and WI-023 reaches its own D4a.

---

## 2026-09-05

### WI-021 shipped idea→done (dark-factory drive #4, the long one) — the semantic write gate

`obsidian_schemas/name_gate.py`: one gate, HANDED its declaration (DECLARE), routed at eight arms
across six functions plus the `PersonRepository.save` rider, hoisted above `note_lock` at the three
writer arms (no stray `@Dave/` directory), in-lock at D4/D5/D6/D8; `NameGateRefusal(LoudFailError)`
carrying the pattern key; rule (ii) refuses undeclared name writes; Tier-1 surface reified;
address splitter single-homed on `Email.parse`; `normalize_phone`/`phones_match` relocated to
`phone_normalization.py` (compat re-export kept — two consumers import it); `lint_vault --fix`
gains an existence guard and a counted, typed refusal record; derived AST wall
(arms/declarations/placement, `{D7}` the one literal) in `tests/derivations.py`; AC battery bridged
to the project interpreter (`tests/ac_interpreter.py`). Floor 637→657; consumers green
(exocortex 641, HAL9000 602, orchestrator 1396). Ship `04d0305`.

The drive: resumed from the 2026-08-11 spawn-budget park on Dave's go after the pre-spawn hand
work (Finding B inversion repaired, G7 = 0, consumer audit re-run: eight files). AC-1–AC-5
re-originated from the brief and SIGNED (WI-268 witness, `ac_hash 92a58783c84f`), then held
byte-identical to `done`. Verify rounds 15–20: each of rounds 16–18 found one rule stated in
disagreeing registers (merge idiom, association vs placement at D7, D7's declaration literal) —
all hand-resolved at zero spawns; G8/G9/G10/G11/G12 run by the conductor's shell (G8: both live
sentinel stubs phone-bearing; G11: count 3 = 79/2/77 unchanged, live non-sentinel 0; G12: five
`+`/no-`+` phone duplicates → Dave's ruling 4, E.164 wins). Ready gates (threat model, spec
review, adversarial) three rounds each in one leg; build two legs (a CLAUDE.md write-authority
pause landed by hand); exit reviewers PROMOTE unforced. Budgets: spawns 52→65→80→95 (Dave's word
each time), rounds 16→18→20. Two factory defects recorded from this drive: the zero-blocking
REVISE treadmill (rounds 18–19; specimen in the eval ledger, workshop minting the lane) and the
missing `--ac-python` on hand launches. One conductor scar: a ledger append during a leg tripped
fence-tamper; restored from evidence bytes, rule adopted. Doc archive-split by hand at wrap-up
(the tool refuses the hand-made August drawer): living 7,2xx lines, drawer 12,5xx. Retrospective
appended. WI-028 (person-resolution policy into the library) minted 08-31, committed today.
Consumer gitignore completed for the factory's lock-sentinel family.

---

## 2026-08-11 (later)

### Queue review + curation (post-WI-004)

Full staleness pass at Dave's word: every queued premise re-verified against the post-WI-004
tree, live-vault load as reality test. Queue reordered by value: **WI-021 head** (semantic
write-door layer; premise verified live, unblocked), WI-016 promoted (fixture vault enabler),
WI-026 currency-noted as HALF-CLOSED by WI-004's routing (re-scope at spec time), WI-011
noted partially superseded by WI-020. **7 parked with written un-park criteria**
(WI-001/002/003/012/013 perf speculation — measured baseline 1.27s / 1,129 people; WI-010
first-real-migration; WI-006 owner-elsewhere = exocortex graph). Linter 0 errors; the 150
stale-suffix warnings are WI-004's frozen build-time citations, deliberately unrefreshed
(fence-tamper lesson). **Live-vault finding: ~70 identity-reconciliation conflicts + 2
invalid person notes** — minted as **orchestrator/WI-173** (gated 0-driver mint, at-rest
verified). Ship: `821bc67`, pushed.

---

## 2026-08-11

### WI-004 shipped idea→done (dark-factory drive #3) — the write-safety primitive

`vault_io.py`: every vault write now walks one door — atomic fd+fsync+`os.replace`,
per-file `filelock`, derivation-stamp preconditions (`StaleEntityWrite` /
`NoteAlreadyExists` / `ExternalWriteConflict`). AC 18/18 unforced; floor 617→637; ship
`b87fb77`, pushed. The drive: 8-round exploring arc closed by measured-not-asserted
reframing + audit folds; Dave rulings mid-drive (A′ stamp corpus, module-attribute doors,
(β) battery re-admission, filelock, door 2c); live-vault obligations grounded in a
conductor sitting (APFS-local positive; Obsidian truncate-in-place observed — residual
restated); build-runner tooling-fault (HQ-fixed upstream) + fence-tamper true positive
(builder citation-refresh inside frozen fences) both absorbed. Post-merge: HAL9000 456
green, exocortex 531 + designed taxonomy tripwire (handoff:
`~/scratch/exocortex-roster-amendment-handoff.md`), orchestrator 1250 green after
`filelock` venv install (+ its 4 pre-existing WI-171 reds). filelock>=3.12 is a new
runtime dep — declared in pyproject.toml, installed in all four venvs.

---

## 2026-08-09

### Hygiene & housekeeping (pre-WI-004)

Catch-up session before the next drive, at Dave's word. Linter 10 warnings → **0 errors, 0
warnings**: two driver-gate `touched_by` values normalised to `session`, one citation
line-range fixed to EOF, done-stage sections added to the three pre-pipeline docs as honest
pointers (WI-018/019 → orchestrator's `find-or-create-stub.md`; WI-017's design carried by
its own Verified diagnosis/Approach). `queue_order` trimmed of shipped items. This log
back-filled for the two July drives below (neither drive wrote an entry — driver commits +
work-item docs were the record). Obsolete scratch handoff note retired. Orchestrator's 4
pre-existing red tests (found during WI-024 consumer verification, unrelated to the flip):
two mints into orchestrator reported success and were **silently reverted** by concurrent
WI-166 drive legs (the cage reverts mid-spawn live-tree deltas — 2-for-2 reproduction,
second-precise ledger evidence); a third mint, gated on a 0-driver check both sides and
at-rest verified, landed as **orchestrator/WI-171**. Defect report for workshop:
`~/scratch/mint-vs-cage-defect-2026-08-09.md` (fix: the quiesce refusal belongs inside the
mint CLI, fail-closed). Second specimen of the cross-session collision class (first: the
07-19 driver kills). Floor 617 green. Remaining linter NOTE (WI-004 missing
Exploration Notes, going cold) self-resolves when WI-004 is driven — next up.

---

## 2026-07-24

### WI-020 shipped idea→done (dark-factory drive #2)

Loud-fail hardening across parse/guard/write-return boundaries: parse raises, loads
surface, guards refuse, writes never lie. New `obsidian_schemas/errors.py` exception API.
The hardest drive yet — 27+ review rounds with repeated Dave-ruled audit-folds (the reason
channel closed as a class, exception surface completed class-by-class, definition-site
uniqueness proofs) before `building→done` closed unforced. One write-authority fork
(conductor precondition: CLAUDE.md floor line de-drifted to run-to-check form — hardcoded
counts are the drift they warn about). Floor 607 → 617. Record: `docs/loud-fail-boundaries.md`
+ the 2026-07-24 commit train ending `8ccb3e6` (retrospective).

---

## 2026-07-19

### Factory readiness + WI-024 shipped idea→done (first drive on this repo)

Morning (parallel setup session): WI-148 readiness — `pipeline-runners.yaml` declaration
(write_authority incl. `scripts/**` for WI-026; seed_deps `.venv`) resolver-verified, floor
recorded absolute/cwd-independent (563 baseline), report at
`~/scratch/obsidian-schemas-readiness-report.md` (risk 1: three consumers' editable installs
point at this checkout — every core merge is live everywhere immediately).

Afternoon (this session): WI-024 driven idea→done in one day. No default vault —
`VaultPathNotConfiguredError` on unconfigured/blank construction (incl. the `Path("")`→cwd
door the red-team found), `lint_vault.py` demoted to explicit-vault, docs corrected.
D4a/D4b conversational sign-offs (`bcc5e03b3564`); consumer audit committed as the
`kind: precondition` fence (orchestrator: 16 live no-arg sites; remediation =
`OBSIDIAN_VAULT_PATH` in `~/.zshenv`, readback-verified). Post-merge: all three consumer
suites hand-run — HAL9000 432 green, exocortex 433 green, orchestrator 1073 green + 4
pre-existing unrelated failures. Floor 563 → 607. Conductor scars (fence-commit trap,
`confirm --sign`, cross-session driver kills) in session memory + `~/scratch/` incident note.

---

## 2026-07-05

### Backlog campaign (Fable review)

Full project review (architecture / code health / test suite / work-item corpus, four parallel agents, corruption-class claims spot-verified) + campaign-style curation. Artifact: `docs/backlog-campaign-2026-07-05.md` — state of play, curation table, phased queue with per-stage model/effort routing.

- **Suite verified: 563 tests, green, hermetic, 1.09s** (CLAUDE.md said "195+" — fixed to a run-to-check instruction).
- **Curation:** WI-004 resliced (concurrent & external write safety; absorbs WI-015, parked→merged); WI-014 parked (premise eroded, HAL9000-owned); WI-016 resliced (frozen anonymized fixture vault); WI-008 premise fixed (Exploration model IS committed); WI-017 doc stage corrected specced→done. 8 new items opened from review findings: WI-020 loud-fail boundaries, WI-021 write-door bypasses, WI-022 company stub parity, WI-023 identity engine endgame, WI-024 remove live-vault default path, WI-025 person.py decomposition, WI-026 lint_vault --fix safety, WI-027 needs_resolution flip (unqueued). Queue: 10 items across 5 phases; routing per stage in each doc. State file rewritten + readback-verified (27 items, next_id 28).
- **Headline code findings** (ticketed, not fixed — campaign is read-only on code): malformed-YAML silent degrade × rebuild paths destroys frontmatter (parser.py:78-80); WI-126 guard self-disables on read error (writer.py:189-190); no locking/atomic writes anywhere; Company create_stub still runs the mangler regex Person deleted; hardcoded live-vault default (base.py:21).
- **Hygiene:** BACKLOG.archive.md → docs/; CLAUDE.md stale claims fixed (docs/ "empty", test count, Key Files, orchestrator as consumer); the long-uncommitted March entry below + docs/ + state bootstrap finally committed this session.

**Gap note:** SESSION_LOG has no entries for the June identity-engine arc (WI-105→WI-126, 15 commits, 2026-06-13→15) — that work was driven and logged from orchestrator sessions; git log + orchestrator docs are the record.

---

## 2026-03-15

### Auto-alias on name change + cache key fix

**Problem:** When enriching a stub contact (e.g. updating `name` from "Bruno" to "Bruno Haag"), the file stays at `@Bruno.md` but the old name becomes unresolvable — breaking wikilinks and any code referencing the old name.

**Fix 1 — Auto-alias (new):** `BaseRepository.update_fields()` now automatically adds the old filename stem to `aliases` when the `name` field changes. Entity remains resolvable by its former name.

**Fix 2 — Stale cache key (pre-existing bug):** Changing the `name` field left a stale cache entry under the old key. Now properly removes old key + file map entry before inserting under the new key.

**Files modified:**
- `obsidian_schemas/repositories/base.py` — auto-alias logic + cache key cleanup in `update_fields()`
- `tests/test_repositories.py` — 4 new tests (`TestAutoAliasOnNameChange`)

**Tests:** 204/204 passing

---

## 2026-02-14

### CLAUDE.md and README.md Cleanup
- Fixed file paths and doc reference updates across project documentation

---

## 2026-02-08

### Fix Substring False Positives in PersonRepository.resolve()
- Committed fix for substring matching producing false positive results in person resolution

---

## 2026-01-26

### Slack Field Addition
- Added `slack: str = ""` field to Person model for Slack user ID/handle storage
- Updated Person docstring template to include slack field
- Added 4 tests for slack field (default, user ID, handle, all fields)
- Added slack indexing to PersonRepository:
  - `_slack_index: Dict[str, str]` for O(1) lookup
  - `get_by_slack(slack_id)` method with @ prefix normalization
  - Updated `_index_entity()`, `_clear_indexes()`, `_remove_entity_from_indexes()`
- Added 4 repository tests for slack lookup
- Updated README with slack in Person fields list
- Total: 195 tests passing

**Downstream updates:**
- HAL9000: Added `slack` to ContactInfo dataclass and `from_person()` method
- Exocortex: Added `slack` to ContactInfo dataclass and `from_person()` method
- Obsidian vault: Updated person.md template, added slack to @Emma Roberts.md

---

## 2026-01-19

### Birthday Field Addition
- Added `birthday: str = ""` field to Person model (DD-MM-YYYY or DD-MM format)
- Updated docstring with birthday format documentation
- Added 4 regression tests for birthday field
- Commit: `d075018` pushed to main

---

## 2026-01-11

### Entity CRUD System - BookRepository & MeetingRepository

- Added `BookRepository` (`repositories/book.py`, 346 lines)
  - Custom indexes: `_author_index`, `_isbn_index`
  - Methods: `get_by_author()`, `get_by_status()`, `get_by_isbn()`, `resolve()`
  - Overrode `_load_file()` to filter by `type: book` in frontmatter
  - Overrode `save()` to use "Title - Author.md" filename format
  - 15 tests

- Added `MeetingRepository` (`repositories/meeting.py`, 415 lines)
  - Custom indexes: `_meeting_id_index`, `_date_index`, `_attendee_index`, `_topic_index`
  - Methods: `get_by_meeting_id()`, `get_by_date()`, `get_by_date_range()`, `get_by_attendee()`, `get_by_topic()`, `resolve()`
  - 19 tests

- Made repo public for HAL9000 CI access
- PR #1 merged
- Total: 183 tests passing

---

### To Discuss Feature (continued from previous session)

- Created `remind-to-discuss` Claude Code skill at `~/.claude/skills/remind-to-discuss/SKILL.md`
  - Parses natural language "remind me to discuss X with Y"
  - Uses PersonRepository to resolve contacts
  - Calls `add_to_discuss_item()` to add items with auto-dating
- Tested skill end-to-end: created Emma Roberts @ Kato contact, added to-discuss item

### Previous session (same day)
- Completed Phase 0-6 of To Discuss implementation
- Added body_sections module for parsing/manipulating markdown sections
- Added ToDiscussItem dataclass and repository methods
- Created migration script, ran on vault (207 files updated)
- Updated README with full documentation

---

## 2026-01-10

- Created GitHub repo (elegantrampage/obsidian-schemas)
- Initial commit pushed to main branch
- Added Person Schema enhancement idea to FUTURE.md:
  - `profession` field (engineer, designer, PM, etc.)
  - `seniority` field (junior through C-level)
  - Use case: match job opportunities to people in network

---

## 2026-01-06

- Created CLAUDE.md entry point
- (FUTURE.md already exists as backlog)
