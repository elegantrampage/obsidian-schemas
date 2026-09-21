---
id: WI-031
title: Close the third live-vault source in the WI-026 containment wall
project: obsidian-schemas
stage: idea
created: 2026-09-21
last_touched: 2026-09-21
stage_changed: 2026-09-21
touched_by: session
tags: []
depends_on: []
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
