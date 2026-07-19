# WI-024 consumer audit — no-arg repository construction

Conductor-performed scan of the three consumer repos (2026-07-19), committed as the
`kind: precondition` write fence for WI-024's build. The caged builder cannot reach these
repos; this artifact is the evidence the flip's blast radius was measured before merge.
Shape contract: per repo — literal scan command, verbatim stdout, 40-hex HEAD SHA (AC-6).

## HAL9000

Command:

```
grep -rnE --include='*.py' --exclude-dir=.venv '\w+Repository\(\s*\)' /Users/davewascha/Workspaces/HAL9000
```

Output: **no matches** (grep exit 1).

HEAD: `8ee5bf2a3c8a1c74a332fb91db030104bc3152e8`

## Exocortex

Command:

```
grep -rnE --include='*.py' --exclude-dir=.venv '\w+Repository\(\s*\)' /Users/davewascha/Workspaces/exocortex
```

Output: **no matches** (grep exit 1).

HEAD: `75763aa92ead4f6962b55136735c8e4ae4641702`

## orchestrator

Command:

```
grep -rnE --include='*.py' --exclude-dir=.venv '\w+Repository\(\s*\)' /Users/davewascha/Workspaces/orchestrator
```

Output (verbatim):

```
/Users/davewascha/Workspaces/orchestrator/bin/invoke-ghostwriter.py:95:        repo = PersonRepository()
/Users/davewascha/Workspaces/orchestrator/bin/repair-field-rfc2822.py:55:    repo = PersonRepository()
/Users/davewascha/Workspaces/orchestrator/bin/repair-person-names.py:510:    repo = PersonRepository()
/Users/davewascha/Workspaces/orchestrator/bin/apply-vault-review.py:63:    return gen_ns["build_payload"](PersonRepository())
/Users/davewascha/Workspaces/orchestrator/bin/apply-vault-review.py:120:    repo = PersonRepository()
/Users/davewascha/Workspaces/orchestrator/bin/identity-parity-replay.py:66:    real = PersonRepository()  # default/env vault, read-only — input set only
/Users/davewascha/Workspaces/orchestrator/bin/wi120-merge-dups.py:213:    repo = PersonRepository()
/Users/davewascha/Workspaces/orchestrator/bin/wi120-merge-dups.py:357:    repo = PersonRepository()
/Users/davewascha/Workspaces/orchestrator/bin/generate-vault-review.py:694:    repo = PersonRepository()
/Users/davewascha/Workspaces/orchestrator/bin/mine-voice-profiles.py:155:    return PersonRepository()
/Users/davewascha/Workspaces/orchestrator/tests/test_invariants.py:907:    """Redirect the invariant's PersonRepository() at a temp vault."""
/Users/davewascha/Workspaces/orchestrator/tests/test_lint_vault_writers.py:113:        "repo = PersonRepository()\n"
/Users/davewascha/Workspaces/orchestrator/src/contact_normalizer.py:510:    repo = PersonRepository()
/Users/davewascha/Workspaces/orchestrator/src/invariants.py:487:        repo = PersonRepository()
/Users/davewascha/Workspaces/orchestrator/src/invariants.py:655:        repo = PersonRepository()
/Users/davewascha/Workspaces/orchestrator/src/invariants.py:906:        repo = PersonRepository()
/Users/davewascha/Workspaces/orchestrator/src/invariants.py:1009:        repo = PersonRepository()
/Users/davewascha/Workspaces/orchestrator/src/queue_writer.py:784:        repo = PersonRepository()
```

HEAD: `114b258cd900075f5505b942835be230e9a2fb39`

## Reading + remediation

- 16 of the 18 hits are live code (10 in `bin/`, 6 in `src/`); 2 are test-file strings
  (a docstring and a generated-source literal) whose tests already monkeypatch the vault.
- All 16 live sites are the *no-arg + env-var* pattern — they survive the flip iff
  `OBSIDIAN_VAULT_PATH` is set in their execution context. As of this scan the variable was
  set **nowhere** (shell profile, both launchd plists, crontab all checked — 2026-07-19).
- **Remediation (Dave-approved 2026-07-19):** `export OBSIDIAN_VAULT_PATH=
  "/Users/davewascha/Documents/Obsidian/DaveRemoteVault"` in `~/.zshenv`, covering every
  shell-launched context — which is every context that runs orchestrator code (the only
  launchd jobs on this machine are HAL9000 and exocortex-doctor, and both those repos scan
  clean above; crontab is empty). **Merge gate: confirm the export is live
  (`zsh -c 'echo $OBSIDIAN_VAULT_PATH'`) before merging WI-024's build.**
- Residual risk, accepted: a future non-shell context (new launchd job, IDE runner) that
  invokes orchestrator code without the env var will loud-fail at construction — which is
  WI-024's designed behaviour, not a regression.

## remediation_confirmed — 2026-07-19

The Dave-approved remediation is live. Export appended to `~/.zshenv` by Dave in-session
(the conductor's own write was classifier-refused, both sessions — shell-startup files
need the human), then verified in a fresh shell by the workshop conductor session:

```
$ zsh -c 'echo $OBSIDIAN_VAULT_PATH'
/Users/davewascha/Documents/Obsidian/DaveRemoteVault
```

Non-empty, matches the vault path verified to exist on disk. The AC-6 merge gate above is
satisfied; the build leg may proceed.
