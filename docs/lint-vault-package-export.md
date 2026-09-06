---
id: WI-030
title: Export the lint_vault surface from the installed package
project: obsidian-schemas
stage: idea
created: 2026-09-06
last_touched: 2026-09-06
stage_changed: 2026-09-06
touched_by: session
tags: []
depends_on: []
---

# Export the lint_vault surface from the installed package (or publish a CLI)

## Problem / Motivation

`scripts/lint_vault.py` holds the vault-walking and lint core — `read_vault`, `build_indexes`, `run_lint`, the `VaultFile` record and the `Severity` enum — but it is not part of the installed `obsidian_schemas` package (only `vault_io` is), and this repo publishes no CLI for it. So orchestrator reaches it by sibling path: `bin/vault-health-check.py:21` imports `read_vault`, `build_indexes`, `run_lint`, `Severity`, and `bin/batch-contact-context.py:29` imports `read_vault`, `VaultFile`, both from `scripts.lint_vault`. That is a violation of the one boundary that has held across every repo — cross-project access goes through an installed package, an HTTP API, or a published CLI, never a sibling path.

Orchestrator's WI-159 (boundary lint, by hand on Dave's word 2026-09-06) found both reaches. Workshop allowlists them at its next quiesce with a reason that names this item as the durable fix. When this ships, orchestrator re-points its two imports to the exported surface and the two allowlist entries come out. Requested by the factory session on 2026-09-06; the queue slot is Dave's call.

## Intent

Anything another project needs from lint_vault should be reachable through the installed `obsidian_schemas` package or a published CLI, so no consumer has to import this repo's `scripts/` by path and the boundary lint can stay clean without allowlist exceptions.
