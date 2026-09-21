---
id: WI-031
title: Close the third live-vault source in the WI-026 containment wall
project: obsidian-schemas
stage: building
created: 2026-09-21
last_touched: 2026-09-21
stage_changed: 2026-09-21
touched_by: session
tags: [scripts, write-safety, testing]
depends_on: ["WI-026"]
transitions: ["idea>exploring@2026-09-21@session", "exploring>specced@2026-09-21@session", "specced>ready@2026-09-21@session", "ready>building@2026-09-21@session"]
---

# Close the third live-vault source in the WI-026 containment wall

## Problem / Motivation

WI-026 (shipped 2026-09-16) built a containment wall around `tests/test_lint_vault_fix_rules.py` so
no drive in that module can reach Dave's live vault: a syntax half over the module's `ast` (spelling,
non-vacuity, provenance, and clause (iv) — the module names neither `lint_vault.DEFAULT_VAULT` nor
`OBSIDIAN_VAULT_PATH` outside `_temp_vault`) plus a runtime door. Threat-model round 5 found a THIRD
source the wall does not grade: `obsidian_schemas`' own `_resolve_vault_path` falls back to
`os.environ.get("OBSIDIAN_VAULT_PATH")` inside the library, so `repo = PersonRepository()` beside
`read_vault(repo.vault_path)` names neither token, passes every clause with the runtime door
executed, and rewrites the live vault on any machine where the variable is exported — which is where
the floor is hand-run. It is an OMISSION shape, not deliberate-act residue.

Dave ruled CLOSE on 2026-09-16 (revise-cap round-5 answer note, commit `d27f36d`: "ZERO repository
constructions anywhere in the module"). The round-6 spec-writer pass did not act on it — it recorded
the question as OPEN with its owner in `## Scope Boundary` ("sufficiency is not the spec-writer's to
call in either direction"), spec-review round 6 PROMOTEd on that basis, and the item shipped with the
residue DECLARED and not closed. The shipped module constructs no repository today, so there is no
live hazard in HEAD; the wall simply does not forbid the next author from adding one. The ruling in
an escalation answer note evidently does not reach the resumed spec-writer as an instruction — a
factory gap worth reporting to workshop separately.

Cost, per the spec's own costing (`docs/lint-vault-fix-safety.md` `## Scope Boundary`, the routed
question): one more CLOSED shape in `mutating_drive_vault_args`' census in `tests/derivations.py` —
a callee resolving (by the same `ast.Name.id` / `ast.Attribute.attr` rule `drives` and `bindings`
use) to an identifier ending `Repository`, recorded `(module_id, lineno, token, enclosing)` like the
other three and graded by the existing clause (iv) in
`test_every_mutating_drive_in_this_module_is_confined_to_a_temp_vault`. The requirement is ZERO
repository constructions, not "no no-arg construction" (`_is_unconfigured` swallows blank,
whitespace and `"."`); the import-allowlist shortcut cannot work (`module_import_uses` reports the
root module, and M1's verify needs `repositories.base.SKIP_REASONS`); no global `os.environ` scrub.
No new check, no fifth derivation, no count moves. Retire the OPEN paragraph in `## Scope Boundary`
and re-sweep the surfaces that say the residue is declared-not-closed. A planted
`PersonRepository()` escape joins `## Verification` as a RED.

## Intent

A test module that drives `lint_vault`'s mutating entry points must have no route to my live vault
that the wall does not grade — including the library's own environment fallback, which reaches the
vault without ever naming it. I ruled this closed on 2026-09-16; the ruling should be in the code,
not declared open in prose.

## Approach

Hand build, 2026-09-21, conductor session, on Dave's word ("let's build wi-031 please"). The factory's
fast lane is not shipped (WI-290 descoped L0/L1 to WI-317; workshop WI-349's `hand-build.py` lever is
at `specced`, its module absent from the blessed tree), and a full L3 drive for a one-census change
that Dave has already ruled on is the overkill WI-290 exists to name. The doors crossed by hand are
recorded in `## Build Log`; the one human door — the AC signature — is Dave's own in-session word
through `review-spec-helper.py present` → word → `originate --channel conversational`.

## Design

One census, one clause, one battery — inside machinery WI-026 already ships. Nothing new is derived,
no check is added, and the counts WI-026's spec re-synced twice (four derivations, five-plus-three
checks) do not move.

1. **`tests/derivations.py`** — `VaultArgScan` gains a fourth field, `repository_constructions`
   (`(module_id, lineno, callee, enclosing)`), and `mutating_drive_vault_args` fills it: every
   `ast.Call` whose callee resolves by the existing `_call_callee_name` rule (bare or attribute
   spelling) to a name ending `REPOSITORY_CALLEE_SUFFIX` (`"Repository"`), with ANY arguments, in
   ANY scope — no `_temp_vault` exemption, because a construction inside the door hands the module a
   path its text never spells just the same. Callee names, never imports: `module_import_uses`
   reports the ROOT module and cannot separate `from obsidian_schemas.repositories.base import
   SKIP_REASONS` (which M1's verify needs) from `from obsidian_schemas import PersonRepository`.
2. **`tests/test_lint_vault_fix_rules.py`** — clause (v) inside the ONE wall check
   (`test_every_mutating_drive_in_this_module_is_confined_to_a_temp_vault`): the census over the
   module's own source is EMPTY. The rule is zero, not "no no-arg construction": `_is_unconfigured`
   swallows blank, whitespace-only and `"."` as well, so a spelling-shaped rule (the standing
   `NO_ARG_CONSTRUCTION` regex in `tests/test_vault_path_required.py`, which in any case scans
   markdown only) is a partial closure. The module needs no repository. Non-vacuity of the matcher
   is proved by the WI-235 battery, never by the module's own zero: the escape itself (clauses
   (i)–(iv) GREEN, `live_path_names` EMPTY, clause (v) RED at line 2), both spellings with explicit
   and keyword arguments and a construction inside a planted `_temp_vault` (all four recorded, the
   last with `enclosing == "_temp_vault"`), and the near-misses (a bare name, a Constant, a
   lower-case helper, `RepositoryError`, `PersonRepositoryFactory`, a method call on a repository
   object, a docstring) all invisible.
3. **Prose that would otherwise be false.** The module docstring's part list goes from four to
   five and its "DECLARED … routed to Dave" paragraph is replaced; WI-026's `## Scope Boundary` OPEN
   paragraph gets a dated CLOSED paragraph beneath it (the surfaces above it that say "declared, not
   closed" are archival by date and superseded by that paragraph — a done item's rounds are not
   rewritten). `tests/test_ac_interpreter.py:WORK_ITEM_DOCS` gains this document so AC-1 joins the
   foreign-interpreter battery.

The deliberate-act bound WI-026 recorded is unchanged: a class named to dodge the suffix, or an
aliased import of a repository, is a disguise and outside every clause of this wall by design.

## Edge Cases & Open Questions

- A helper whose name ENDS `Repository` but is not a repository (`make_Repository()`) is recorded and
  RED. Conservative on purpose; the module has no such helper and a rename is the fix, never an
  exemption.
- `get_repository()` / `repository = …` / `RepositoryError(…)` / `PersonRepositoryFactory()` are
  near-misses and invisible (suffix match on the callee name, case-sensitive, end-anchored).
- The census runs over `files` generally, but its only consumer asserts zero over the check module
  alone; it is NOT a repo-wide wall (`tests/identity_fixture.py` and `tests/record_identity_golden.py`
  construct repositories with explicit vaults and legitimately so).

## Implementation Plan

- [x] **Task 1 — The census.** `REPOSITORY_CALLEE_SUFFIX`, the fourth `VaultArgScan` field, the walk
  arm in `mutating_drive_vault_args`, docstrings.
  verify: test_every_mutating_drive_in_this_module_is_confined_to_a_temp_vault
- [x] **Task 2 — Clause (v) and its battery.** In the ONE wall check; the escape, the claimed shapes,
  the near-misses; module docstring parts 4/5 rewritten.
  verify: test_every_mutating_drive_in_this_module_is_confined_to_a_temp_vault
- [x] **Task 3 — Truthful prose + battery registration.** WI-026 `## Scope Boundary` CLOSED
  paragraph; `WORK_ITEM_DOCS` gains this document.
  verify: test_every_acceptance_criterion_passes_under_the_conveyors_interpreter

## Acceptance Criteria

```criteria
id: AC-1
desc: The containment wall over tests/test_lint_vault_fix_rules.py has a FIFTH clause and it is total over the library route. (a) ZERO — `mutating_drive_vault_args([that module]).repository_constructions` is empty, where the census collects every call whose callee resolves by the wall's ONE callee-name rule (bare or attribute spelling) to a name ending `Repository`, with any arguments, in any scope including `_temp_vault`'s own body. (b) REACH (WI-235) — over planted text the census records the escape (`vault = _temp_vault(tmp)` / `repo = PersonRepository()` / `read_vault(repo.vault_path)` / `apply_fixes(issues, vault)`) at its construction line with clauses (i)–(iv) GREEN and `live_path_names` EMPTY, records both spellings with positional and keyword arguments and a construction inside a planted `_temp_vault` (enclosing recorded as that name), and records NONE of: a bare name `repository`, a string Constant, a lower-case `get_repository(...)`, `RepositoryError(...)`, `PersonRepositoryFactory()`, a method call on a repository-shaped object, a docstring mention. (c) ONE CHECK — clauses (i)–(v) and every battery run inside `test_every_mutating_drive_in_this_module_is_confined_to_a_temp_vault`; no new `def test_`, no new derivation, and the `ast` single-home equality still returns `{"tests/derivations.py"}`.
why: Dave ruled this closed on 2026-09-16 and the ruling shipped unapplied. The library's environment fallback is the one omission route WI-026's four clauses cannot see, because it obtains the live path without spelling it; on the machine where the floor is hand-run that variable is exported, so the failure mode is green-in-the-cage, live-vault-write-on-the-laptop. A zero over a matcher nobody proved reaches anything is the WI-235 shape, hence (b); and (c) is what keeps WI-026's re-synced counts true.
check: test_every_mutating_drive_in_this_module_is_confined_to_a_temp_vault
kind: test
```

## Build Log — 2026-09-21 (hand build, conductor session)

- Doors crossed by hand, recorded rather than faked: ideation, architect, data-premise, threat-model,
  spec-review, injection-hunter, code-review, test-observability — none spawned. The Design is the
  WI-026 spec's own costing of this closure (its `## Scope Boundary`, the routed question), written
  by six gate rounds already; the threat model is WI-026's rounds 5–6; the code review is the floor
  plus Dave's read of the diff at sign-off.
- Tasks 1–3 landed in the live tree (no cage — a hand build). Verify: the WI-026 check module green
  (8 checks), the full floor green (directional count unchanged — one check gained clause (v) and a
  battery; no `def test_` added), the work-item linter at 0 errors.
- AC-1 signed by Dave in-session (the `## AC Sign-off` fence below is the record).
- **Intent check — NOT by hand after all (corrected 2026-09-21, later the same day).** The first
  version of this entry recorded the D6 violation (`building -> done` requires an intent-check PROMOTE
  verdict) as informational. It is not: the driver's floor runs the linter WITH `--enforce`, so the
  hand-advanced `done` turned this project's floor RED and killed the WI-029 launch at step 0
  (tooling-fault). Repair: the item is REWOUND to `building` (the `building>done@session` transition
  removed) and re-driven for its exit half — build-runner over the already-landed, checked tasks,
  then code-reviewer, test-observability and intent-check as REAL verdicts — the WI-023 precedent
  ("re-driven from building → done in one leg"). The conductor's own answer to the intent question
  stays below as context for that gate, not as its verdict. The conductor's own answer to the
  gate's question, so the record is not empty: the frozen `## Intent` asks that the test module have
  NO route to Dave's live vault the wall does not grade, including the library's environment
  fallback, and that the 2026-09-16 ruling live in code rather than prose. The build lands exactly
  that route as clause (v) with a proven-reaching matcher, and nothing else; no drift from the intent
  and no scope beyond it. Ordinary lint: 0 errors.
- Mutate-and-observe, 2026-09-21: a planted `PersonRepository()` inside a never-called `def` in the
  check module turned the wall RED naming the line and the enclosing function; restored
  byte-identical, GREEN. Floor 689 → 689 (no `def test_` added, by AC-1(c)).

## AC Sign-off

```verdict
gate: ac-signoff
verdict: PROMOTE
date: 2026-09-21
reviewer: dave
channel: conversational
signed_at: 2026-09-21T08:03:38+01:00
provenance: attested
ac_hash: 490edae35c1a
intent_hash: ab39c2f99e93
ac_hash_AC-1: 7bbd9b8c2006
artifact: docs/spec-reviews/WI-031-dave-review-2026-09-21.md
```
