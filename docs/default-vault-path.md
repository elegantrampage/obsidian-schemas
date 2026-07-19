---
id: WI-024
title: "Remove the hardcoded live-vault default path (loud-fail when unconfigured)"
project: obsidian-schemas
stage: exploring
created: 2026-07-05
last_touched: 2026-07-19
stage_changed: 2026-07-19
touched_by: session
tags: [loud-fail, configuration, small-mechanical]
depends_on: []
transitions: ["idea>exploring@2026-07-19@session"]
---

# Remove the hardcoded live-vault default path

> **Model routing** (2026-07-05 campaign, `docs/backlog-campaign-2026-07-05.md`; self-sufficient):
> - **Explore: —. Spec: —** (this doc + a consumer audit list is the spec: grep HAL9000/exocortex/orchestrator for no-arg repository construction before flipping). **Spec-review: Opus / low. Build: Sonnet / low** + Opus code-review (standing rule).
> - Sequencing: Phase 1 (protect the floor). **Dave signed off 2026-07-05** on the breaking change (campaign session). Build prerequisite stands: audit and fix any no-arg repository construction in all 3 consumers before flipping the loud-fail.

## Problem / Motivation

`DEFAULT_VAULT_PATH = "/Users/davewascha/Documents/Obsidian/DaveRemoteVault"` (base.py:21) is the fallback whenever a repository is constructed with no path and `OBSIDIAN_VAULT_PATH` is unset — a machine-specific absolute path baked into a library three repos install, pointing at the **live vault**. Any consumer that forgets configuration silently reads and writes Dave's real data; no test asserts the fallback (tests always pass explicit paths), so nothing would catch a misconfigured caller. Duplicated at `scripts/lint_vault.py:50`. (2026-07-05 review findings H1 + test-suite risk #1.)

**Sharpened by exploration (2026-07-19).** The defect is not "a hardcoded path" — it is that the **library's default binding is write-capable and fail-open**. Three facts, verified in the current tree, are what make it corruption-class rather than untidy:

1. The fallback is reached by *omission*, not by intent: `if vault_path is None` (base.py:55) fires for any caller on any machine, in CI, in a scratch script — not just for Dave.
2. The binding it produces can **create**: `save()` builds `self.vault_path / filename` (base.py:202) and the writer materialises missing parents (`writer.py` `mkdir(parents=True, exist_ok=True)`). A wrong binding doesn't just read wrong, it writes.
3. Nothing observes it. `load()` on a non-existent vault logs a WARNING and returns 0 (base.py:96-99) — the repository then presents as a legitimately empty vault, so `resolve()` misses and stub-creation proceeds.

There is a **second, narrower door of the same shape** that the original framing missed: `Repository("")` / `Repository("   ")` skips the `is None` test at base.py:55 entirely and lands on `Path("")` → `Path(".")` at base.py:58 — binding the repository to the current working directory. Likewise `OBSIDIAN_VAULT_PATH=""` (set-but-empty, a *more* common misconfiguration than unset, because that is what a broken `.env` or an unexpanded shell variable produces). Blank-string handling is in scope; it is the same accident-of-omission, one layer down.

And the blank door is **not string-shaped only**. The signature is `vault_path: Optional[str | Path] = None` (base.py:43) — `Path` is an accepted *and actually used* input type: the one internal repository-constructing call site, `person.py:1150` (`CompanyRepository(self.vault_path)`), passes a `Path`, because `self.vault_path` is one (base.py:58). `pathlib.Path("")` normalises to `Path(".")` at *its own* construction, before `__init__` ever sees it, so a caller that wraps before passing — `PersonRepository(Path(os.environ.get("SOME_VAR", "")))` — hands in an already-cwd-equivalent `Path` that any `isinstance(str)`-shaped blank check waves through. The property in scope is therefore **"the argument is missing, or reduces to an empty/whitespace path, whatever type it arrives as"** — not an enumeration of blank string literals. Stating it as a list of doors is what let this fifth one stay open through two AC drafts.

## Intent

It is impossible to touch the live vault — or the current working directory — by accident of omission. A repository constructed without an explicit path, and a vault-touching script run without one, loud-fail immediately and say which of the two configuration routes to use. Configuration becomes a thing you did, not a thing that happened to you.

## Exploration Notes

Cold-start exploration, 2026-07-19. All code claims below read from the current tree at the file:line cited.

### REMOVE-audit (subtraction item — WI-123 rule: quote the trigger predicate, not the name or the effect)

Two mechanisms are proposed for removal. Each is classified on its **invoking code condition**, read from the tree.

**Mechanism A — `DEFAULT_VAULT_PATH` fallback (`obsidian_schemas/repositories/base.py:21`, consumed at :55-56).**

Trigger predicate, verbatim:

```python
# base.py:55-56
if vault_path is None:
    vault_path = os.environ.get(ENV_VAULT_PATH, DEFAULT_VAULT_PATH)
```

The predicate is **"the caller omitted an argument."** It is not conditioned on the machine, the user, the environment, or interactivity. The docstring's story ("Falls back to `OBSIDIAN_VAULT_PATH` env var, then default" — base.py:50-51) and the comment's story ("Default vault path - can be overridden" — base.py:20) both describe an *effect*; neither is a predicate that distinguishes Dave's laptop from a CI runner. The two diverge completely: the name says "sensible default", the predicate says "silently bind any forgetful caller anywhere to one specific absolute path, with write capability".

Load-bearing? No — verified, not assumed. `DEFAULT_VAULT_PATH` is not re-exported from `repositories/__init__.py`; it has no importer anywhere in the tree; no test references it; and there is **no no-arg repository construction anywhere in the tree** (`grep -n 'Repository(\s*)'` returns exactly one hit, the prose example at `CLAUDE.md:18`). Every one of the four subclasses (`person.py:173`, `company.py:58`, `meeting.py:34`, `book.py:34`) forwards `vault_path` straight to `super().__init__`, so the predicate lives in exactly one place. The single internal repository-constructing call site, `person.py:1150` (`CompanyRepository(self.vault_path)`), passes an explicit path.

**Verdict: REMOVE.** Uncontested — the predicate is fail-open by construction and nothing depends on it.

**Mechanism B — `DEFAULT_VAULT` in `scripts/lint_vault.py:48-51`, consumed at :1146.**

Trigger predicate, verbatim:

```python
# lint_vault.py:48-51 (module import time)
DEFAULT_VAULT = os.environ.get(
    "OBSIDIAN_VAULT_PATH",
    os.path.expanduser("~/Documents/Obsidian/DaveRemoteVault"),
)
# lint_vault.py:1146
"--vault", type=str, default=DEFAULT_VAULT,
```

The predicate is **"`--vault` was not passed on the command line."** This is *materially a different mechanism from A*, and the original framing ("duplicated at lint_vault.py:50") conflates them. Three differences that matter:

- `expanduser("~")` resolves against **the running user's** home, not Dave's. On any other machine it names a path that does not exist, and `main()` already loud-fails on it: `if not vault_path.exists(): ... sys.exit(1)` (lint_vault.py:1174-1176). **Mechanism B is already fail-closed everywhere except Dave's own laptop; Mechanism A is fail-open everywhere.**
- The env read happens at **import time**, so `os.environ` mutated after import is ignored — a latent bug, but independent of this item.
- lint_vault is a vault *tool*; touching the vault is its purpose. The hazard is not that it has a vault, it is that it can pick one implicitly *and then mutate it*: `--fix` (:1163) rewrites frontmatter and bodies, `--quarantine` (:1165) **renames live notes** (`src.rename(dest)`, :1037).

**Verdict: DEMOTE, not REMOVE-by-the-same-argument.** The implicit default goes and the env var is still honoured — but the justification is "an implicit vault plus a mutating flag", not "a hardcoded Dave path". Recording the distinction matters because WI-026 (lint_vault `--fix` safety) will re-open this file and must not inherit a wrong story about why line 48 changed.

**In-tree precedent for the replacement shape — do not invent one.** `scripts/migrate_person_to_discuss.py:160,171-174` already implements exactly the target behaviour: env-var default of `''`, an explicit guard, and an error message naming both routes. Mechanism B should be made to match it.

### Approaches considered

**A1 — raise at construction (`BaseRepository.__init__`). CHOSEN.** Solves it in one place: the predicate exists at exactly one line and all four subclasses forward through it. Fails at the moment the mistake is made, with the stack pointing at the offending caller rather than at some later `resolve()` that returned `None`. Matches the Intent's wording ("loud-fails at construction").

**A2 — raise lazily at first I/O (`_ensure_loaded` / `load` / `save`).** Rejected. It would let a misconfigured repository be constructed, passed around, and stored on some service object, only to blow up later at a call site that has nothing to do with the bug. It also splits the check across three doors. Worse diagnostics, more surface, no benefit.

**A3 — keep `DEFAULT_VAULT_PATH` but make it opt-in (`Repository(use_default=True)`).** Rejected. It preserves the machine-specific absolute path in a library three repos install — the constant is itself the defect, not merely its wiring. And an opt-in flag is a second door that will eventually be passed by a caller who "just wants it to work".

**A4 — warn loudly instead of raising (deprecation period).** Rejected. Warnings are exactly the failure mode this item exists to kill: `load()` already warns on a non-existent vault (base.py:96-99) and that warning has never stopped anything. A breaking change with a clear message is honest; a warning is the silent degrade wearing a hat. Dave signed off on the break on 2026-07-05.

**A5 — validate that the configured path exists / looks like a vault.** Rejected **for this item**, deliberately — see Non-goals. It is a different predicate (accident of *commission*, not omission) and it belongs with WI-020's loud-fail boundary work.

### Constraints discovered

- **One place to change.** The predicate is base.py:55-56 and nothing else; all subclasses forward. Do not add per-subclass checks.
- **The floor command must stay green and hermetic.** `563 passed` from a foreign cwd (CLAUDE.md). There is **no `conftest.py`** — tests supply `tmp_path` explicitly (every vault-touching test in `tests/`), and **zero tests reference `OBSIDIAN_VAULT_PATH`** today. That is the property to preserve; but see the wording trap in the red-team section — the invariant test itself *must* manipulate the env var via `monkeypatch`, or it will fail on any machine where the var is legitimately set.
- **The stale editable install is load-bearing.** `_obsidian_schemas.pth` points at a dead path; the suite works because pytest prepends its rootdir. This change lives entirely inside `obsidian_schemas/` and does not touch that — confirmed, not assumed.
- **Exception type.** The repo's convention is named exceptions at boundaries (`writer.py:46`, `name_validation.py:134,160`, `identifier.py:67`). Use `VaultPathNotConfiguredError` subclassing `ValueError`, so a consumer's existing `except ValueError` still catches it and the break degrades to a message change rather than an uncaught escape.
- **Breaking change, three consumers.** Standing build prerequisite from the 2026-07-05 campaign: audit and fix any no-arg repository construction in HAL9000, Exocortex, and orchestrator *before* flipping. This exploration is scoped to this tree and did **not** perform that audit — it remains open.

- **The consumer audit cannot be an acceptance criterion, and must not be dressed as one.** This is the constraint that reshaped AC-5/AC-6, and it is structural rather than a matter of effort. Three doors were checked and all three are shut:
  1. **`kind: test`** — this repo's floor is hermetic (`563 passed`, ~1s, CLAUDE.md). A test that reaches `/Users/davewascha/Workspaces/HAL9000` is a caller-independent absolute path resolved at test time: it fails on every other machine, and it is the *exact* defect AC-2 forbids. The item cannot ship a test that violates its own criterion.
  2. **`kind: command`** — this doc's `created: 2026-07-05` is **on** `COMMAND_REGISTRY_EPOCH` (`work_item_linter.py:371`), so a `kind: command` `check` must name a registered id. The registry holds exactly two — `lint-project` and `lint-boundary-reaches` (`work_item_linter.py:114-123`) — and neither scans a consumer repo. An unregistered id is a lint ERROR at spec-time *and* a U3 block at `building → done` (`work_item_linter.py:1868-1870`). Registering a third id is a workshop change, not an obsidian-schemas leaf build.
  3. **Prose in this doc** — fabricable by one string literal. That is the shape the red-team correctly killed.

  **Where it actually goes: a `kind: precondition` write fence (WI-156).** The pipeline already types this exact situation — "a path a NON-BUILDER actor must have COMMITTED before the build spawn; a cage-denied path the builder is design-forbidden from authoring", probed for git-HEAD membership by `drive()` before the builder is armed (`work_item_linter.py:57-61`, `VALID_WRITE_KINDS` at :61). The audit fits it precisely: the caged builder *cannot* reach three sibling repos, so the conductor performs the scan and commits `docs/wi-024-consumer-audit.md`, and the conveyor refuses to arm the build until that file is in HEAD. **Note for the spec-writer: this is a `## Write Targets` declaration and therefore yours, not the ideation gate's** — the fence shape is fixed in code at `PRECONDITION_FENCE_SHAPE` (`work_item_linter.py:100-102`); write it verbatim rather than paraphrasing.

  The division of labour that results: **the precondition fence enforces that the audit happened** (code refuses the build without it), **AC-6 enforces that what was committed has audit shape** (per-repo command + verbatim output + scanned SHA), and **AC-5 claims only what a doc scan can see.** No criterion asserts something its check cannot reach.

### Non-goals (named so they are not re-explored, and not scope-crept into a Sonnet/low leaf build)

- **"Configured but wrong" paths.** A typo'd `OBSIDIAN_VAULT_PATH` still binds silently: `load()` warns and returns 0 (base.py:96-99), the repo presents as empty, and stub creation will then `mkdir` a bogus tree. This is real and it is the biggest remaining hole — but it is accident of *commission* and it is the same class as WI-020's silent-degrade boundaries. **Route it to WI-020**, do not grow this item.
- **`person.py:1147-1160`'s bare `except Exception`** would swallow the new error if that call site ever stopped passing an explicit path. Its predicate cannot fire today. Bare-except narrowing is WI-020's territory — solve in one place.
- **lint_vault's import-time env read** (:48) — latent, out of scope, note it for WI-026.

### Red-team on the draft ACs (subtraction-item rule)

A cold-start decorrelated red-team was run against the draft criteria before sign-off, per the WI-123 rule that a capture-time audit is a hypothesis rather than evidence. It landed four hits that changed the set:

1. **The original AC2 was vacuous.** "grep for `/Users/davewascha` returns nothing" **already passes today** — lint_vault.py:50 uses `~`, not the literal. It would also keep passing if someone reintroduced `expanduser("~/Documents/Obsidian/DaveRemoteVault")`. The criterion tested a string, not the property. Replaced with a property-shaped check: no caller-independent filesystem path (`expanduser`, `Path.home`, a literal `/Users/`) resolved as a default anywhere in `obsidian_schemas/` or `scripts/`.
2. **Blank-string arguments were uncovered** — only the env var was. Folded into AC-1; it drove the Problem-section addition above.
3. **"No test touches `OBSIDIAN_VAULT_PATH`" self-contradicts.** As written it forbids the very mechanism (`monkeypatch.delenv` / `setenv("")`) that the invariant test needs. The real property is *no test depends on ambient environment*. Reworded.
4. **AC-4's crash mode.** If `DEFAULT_VAULT` merely becomes `None`, argparse yields `args.vault is None` and `Path(args.vault)` at lint_vault.py:1173 raises `TypeError` — a crash, not a message naming both routes. The guard must precede line 1173.

Two red-team proposals were **rejected** as scope creep on a leaf build and rerouted rather than adopted: an AC requiring construction against a non-existent path to raise, and an AC narrowing `person.py:1150`'s bare `except`. Both are recorded under Non-goals with their destination items.

5. **AC-5 asserted a thing its own check could not see (second red-team pass, 2026-07-19 — see `## AC Red-Team`).** The fold described above was wrong: bundling the three-repo consumer audit into `test_docs_do_not_advertise_no_arg_construction` meant the item's *breaking-change safety gate* was dischargeable by adding one sentence to this doc, since a hermetic in-repo pytest cannot reach HAL9000, Exocortex, or orchestrator. The gate that mattered most was the one nothing looked at. **Split, and the audit re-homed out of the AC system entirely** — see the "cannot be an acceptance criterion" constraint above for why all three AC kinds are structurally shut and why the `kind: precondition` write fence is the mechanism. AC-5 now claims only the doc scan; AC-6 pins the audit artifact's shape; the fence supplies the teeth. The general lesson, worth carrying: *folding* a criterion is not free — it silently widens the `desc` past what the named `check` can observe, and a criterion whose desc outruns its check is indistinguishable from a green one.

6. **AC-1/AC-3 enumerated only string-shaped blank doors (third red-team pass, 2026-07-19).** The four-doors wording ("no arg, `""`, `"   "`, env blank") is satisfiable by `if vault_path is None or (isinstance(vault_path, str) and not vault_path.strip())` — which passes every named test case while letting `PersonRepository(Path(""))` through to `Path(".")` and a cwd binding. Not hypothetical: `base.py:43` accepts `str | Path` and `person.py:1150` actually passes a `Path`, so the uncovered shape is the one the library uses on itself. AC-1 is now stated as a property of the *normalised* path regardless of arrival type, with `Path("")`/`Path("   ")` named as required test inputs, and AC-3 now iterates every shape across all four subclasses instead of only the no-arg case. This is the *same* failure as hit #1 (AC-2's literal-vs-property) recurring one criterion over — the pattern to watch is that an enumeration of literals is always gameable by a value one shape removed from the list, so an AC that lists inputs is a smell unless it also states the property those inputs sample.
7. **AC-5's citation was stale (same pass).** `README.md:227,408` were named as sites advertising no-arg construction; at current tree state neither does (`README.md:228` already passes an explicit path; `408-409` already shows the env-var route). Only `CLAUDE.md:18` does. Corrected in AC-5 and in the Approach, with the check pinned as a general pattern scan so it does not depend on the line numbers at all.

## Approach

Delete `DEFAULT_VAULT_PATH` and replace the fallback at `base.py:55-56` with a single resolution step in `BaseRepository.__init__` that treats *both* a missing/blank `vault_path` argument and a missing/blank `OBSIDIAN_VAULT_PATH` as unconfigured, and raises `VaultPathNotConfiguredError(ValueError)` naming both routes. "Blank" is a property of the *normalised* value, not of its type: `str(vault_path).strip()` (or equivalent) is what gets tested, so `Path("")` — which `pathlib` has already collapsed to `Path(".")` — is caught alongside `""`; an `isinstance(str)`-gated guard is explicitly the wrong shape here, because the library's own `person.py:1150` call passes a `Path`. One place, one predicate, all four subclasses inherit it. `scripts/lint_vault.py` gets the same treatment in the shape its sibling `scripts/migrate_person_to_discuss.py:171-174` already uses — `--vault` defaults to the env var or `''`, and an explicit guard fires *before* `Path(args.vault)` at :1173 — demoted for its own reason (implicit vault + mutating `--fix`/`--quarantine`), not by inheritance from the base.py argument. An invariant test pins unconfigured and blank construction across all four repositories, using `monkeypatch` so the suite stays invariant to the developer's environment. Docs that currently advertise no-arg construction are corrected in the same change — a repo-wide grep for `\w+Repository\(\s*\)` finds exactly one live site, `CLAUDE.md:18`; `README.md:228` already passes an explicit path and `README.md:408-409` already uses the env-var route, so the doc fix is smaller than the earlier framing suggested and the check must be a pattern scan rather than a line-targeted edit list. **Build prerequisite, unchanged and still open — but now mechanised rather than remembered:** the no-arg-construction audit of HAL9000, Exocortex, and orchestrator is performed by the conductor (not the caged builder, which cannot reach those repos) and committed as `docs/wi-024-consumer-audit.md` — one entry per repo carrying the literal scan command, its verbatim output, and the scanned HEAD SHA. The spec-writer declares that path as a `kind: precondition` write fence, so `drive()` refuses to arm the build until the artifact is in git HEAD; AC-6 then pins its shape. See the "cannot be an acceptance criterion" constraint for why no AC kind can carry this obligation directly.

## Acceptance Criteria

Draft — originated cold-start (no Dave in the loop this session) and red-teamed as recorded above. **Not yet frozen:** `ac-signoff` still requires Dave's signature via `bin/review-spec-helper.py originate --wi-id WI-024 --project <path>`.

```criteria
id: AC-1
desc: BaseRepository.__init__ raises VaultPathNotConfiguredError (a ValueError subclass) whenever the effective vault path is unconfigured — i.e. the vault_path argument is absent, or reduces to an empty/whitespace string REGARDLESS OF WHETHER IT ARRIVES AS str OR Path (base.py:43 accepts str | Path; Path("") is already Path(".") before __init__ sees it) — AND OBSIDIAN_VAULT_PATH is unset or blank. The message names both routes ("vault_path" and "OBSIDIAN_VAULT_PATH"). The guard is a property check on the normalised path, not an isinstance(str)-gated one. Test inputs must include at minimum: no arg, "", "   ", Path(""), Path("   "), and env set to "" or whitespace. Never resolves to Path(".").
kind: test
check: test_unconfigured_vault_path_raises
```

why: this is the item — omission (and its blank twin, in either accepted type) must be unable to bind a write-capable repository to anything at all, least of all cwd or the live vault; the enumerated-literals wording this replaces was satisfiable by an `isinstance(vault_path, str)` guard that let `PersonRepository(Path(""))` through the door it had just shut.

```criteria
id: AC-2
desc: No caller-independent filesystem path survives as a default in obsidian_schemas/ or scripts/ — no os.path.expanduser, Path.home(), or literal "/Users/" resolved into a default vault binding outside docstrings. DEFAULT_VAULT_PATH no longer exists.
kind: test
check: test_no_implicit_vault_path_defaults
```

why: the property is "the vault is always supplied by the caller or the environment", not "one particular string is absent" — the `~` form at lint_vault.py:50 passes a literal-string grep today and would pass it again if reintroduced.

```criteria
id: AC-3
desc: All four repositories (Person, Company, Meeting, Book) raise VaultPathNotConfiguredError, with no env var set, for EACH unconfigured argument shape AC-1 defines — no arg, "", "   ", Path(""), Path("   ") — not the no-arg case alone. The raise happens at construction, before any glob or read of the filesystem.
kind: test
check: test_all_repositories_raise_when_unconfigured
```

why: the predicate lives once in the shared base but the blast radius is per-subclass, so the pin must prove it through every door a consumer actually calls — and per-subclass matters most for the Path-typed shape, since the tree's own repository-to-repository call (person.py:1150 → CompanyRepository) passes a Path, so a str-only guard would fail exactly where the library calls itself; "at construction" is what makes the stack trace point at the bug rather than at a later resolve() that returned None.

```criteria
id: AC-4
desc: scripts/lint_vault.py run with neither --vault nor OBSIDIAN_VAULT_PATH exits non-zero with a message naming both routes, and the guard executes BEFORE Path(args.vault) at line 1173 (no TypeError crash path). Mirrors the existing scripts/migrate_person_to_discuss.py:171-174 shape.
kind: test
check: test_lint_vault_requires_explicit_vault
```

why: this is the higher-blast-radius door — `--fix` rewrites bodies and `--quarantine` renames live notes — so an implicitly chosen vault here mutates real data, and a crash instead of a message would leave the operator guessing which route to use.

```criteria
id: AC-5
desc: No in-repo documentation advertises no-arg repository construction. Implemented as a general pattern scan over this repo's tracked .md files (AC-2's model), NOT a literal check against named lines. The one live site at time of writing is CLAUDE.md:18 (`repo = PersonRepository()`); a repo-wide grep for `\w+Repository\(\s*\)` returns that single hit — README.md:228 already passes an explicit path and README.md:408-409 already shows the env-var route, so neither needs changing. README.md:227's comment ("or uses OBSIDIAN_VAULT_PATH env var") should read as required-one-of-two rather than optional. Scoped to this repo's own tracked .md files; says nothing about the consumer repos (see AC-6).
kind: test
check: test_docs_do_not_advertise_no_arg_construction
```

why: the Quick Start is the most-copied line in the repo — leaving `PersonRepository()` in it after the break turns a clear error into a documentation bug; and this check can only read files inside this repo, so that is all it is permitted to claim.

```criteria
id: AC-6
desc: docs/wi-024-consumer-audit.md exists and carries, for EACH of HAL9000, Exocortex, and orchestrator, three fields — the literal scan command run, that command's verbatim stdout (empty output recorded as an explicit "no matches" marker, not an absent field), and the 40-char git HEAD SHA of the repo as scanned. The test asserts this shape per repo and fails on a missing repo, a missing field, or a SHA that is not 40 hex chars. It does NOT re-run the scan.
kind: test
check: test_consumer_audit_artifact_is_complete
```

why: the audit's teeth are the precondition fence, not this test — this pins the artifact's SHAPE so an audit recorded as one hand-waved prose sentence fails, and the per-repo commit SHA makes the claim re-checkable by anyone with the three repos on disk (which this hermetic suite, by design, is not).

### Examples of done

**Given** a fresh shell with `OBSIDIAN_VAULT_PATH` unset, **when** Dave opens a python REPL and types `PersonRepository()`, **then** it raises immediately with a message telling him to pass a path or set the env var — instead of quietly handing back a repository wired to his real vault.

**Given** a `.env` that sets `OBSIDIAN_VAULT_PATH=` with nothing after the `=`, **when** any of the three consumers constructs a repository, **then** it raises the same error — rather than binding to the current working directory and creating `@Someone.md` files wherever the process happened to start.

**Given** a cron job that runs `python scripts/lint_vault.py --quarantine` and whose environment lost the env var, **when** it fires, **then** it exits non-zero having read nothing and moved nothing — rather than renaming notes in whichever vault the default guessed.

## Relationship to other work

- **WI-020 (loud-fail boundaries)** — owns the two rerouted findings: the "configured but wrong path" silent degrade (base.py:96-99 + the writer's `mkdir(parents=True)`) and the bare `except Exception` at person.py:1147-1160. This item deliberately stops at accident-of-omission.
- **WI-026 (lint_vault `--fix` safety)** — will re-open `scripts/lint_vault.py`. Two notes for it: the DEMOTE reasoning above (the change at :48 is about implicit-vault-plus-mutation, not about a hardcoded Dave path), and the latent import-time env read.
- **Campaign** — Phase 1 item 2 of `docs/backlog-campaign-2026-07-05.md`; the campaign's hermeticity rider ("no test may ever touch `OBSIDIAN_VAULT_PATH` — and after WI-024, no code can by accident") is restated correctly here as *no test depends on ambient environment*; the invariant test must monkeypatch the var, and the rider's literal wording would forbid that.

## AC Red-Team — 2026-07-19

Cold-start, decorrelated attack on the draft AC set. Read order followed Step 2: `## Intent` → `### Examples of done` → `## Problem / Motivation` + Exploration Notes → `## Acceptance Criteria` last. Code read to check satisfiability: `obsidian_schemas/repositories/base.py` (full), `scripts/lint_vault.py:44-51,1140-1180`, `obsidian_schemas/repositories/person.py:165-180,1140-1160`, `README.md:220-235,398-410`, `CLAUDE.md:18`, `scripts/migrate_person_to_discuss.py:150-190`, `docs/backlog-campaign-2026-07-05.md` (full). All file:line claims in the doc under attack were spot-checked against the current tree and hold.

### Attacked and held

AC-1/AC-3's four-blank-doors + raise-before-filesystem-access framing is genuinely satisfiable only by doing the work: `base.py:55-56` is confirmed the single predicate site, all four subclasses forward `vault_path` verbatim (verified at `person.py:173-174`; the doc's grep claim for the other three was not independently re-run but the forwarding pattern is uniform and low-risk). AC-4's line-1173 crash-mode citation is accurate — `Path(args.vault)` at `lint_vault.py:1173` runs before any vault-path guard exists today, so the ordering requirement is real and not tautological. AC-2's pattern list (`expanduser`, `Path.home()`, literal `/Users/`) has exactly one live match in the tree (`lint_vault.py:50`) and no other legitimate use that a blanket scan would falsely flag — checked via repo-wide grep. None of AC-1/2/3/4 pass on current, unmodified state (verified by reading `base.py:55-58` as it stands today — the fallback is still live), so none are the WI-130 "satisfiable with zero implementation" shape.

### CRITICAL — AC-5 bundles the breaking-change safety gate into a check that cannot verify it

AC-5's `desc` asserts two distinct success conditions under one `check: test_docs_do_not_advertise_no_arg_construction`:

(a) no in-repo doc advertises no-arg repository construction, and
(b) "The pre-merge consumer audit for no-arg construction in HAL9000, Exocortex, and orchestrator is recorded in this doc before the build lands."

The named check — the only thing a hermetic `obsidian_schemas` pytest run (this project's floor command, per `CLAUDE.md`) can execute — can only test (a): a text/pattern scan over this repo's own `CLAUDE.md` and `README.md`. It has no way to reach into HAL9000, Exocortex, or orchestrator (three separate repos, outside this repo's test path and this gate's scope) to confirm the audit was actually performed. It can at most confirm that *some sentence claiming the audit happened* exists in this doc.

**Concrete failure scenario:** a builder (or a careless AC-set fold) adds one line to this doc — e.g. "Consumer audit: verified, no no-arg construction found in HAL9000/Exocortex/orchestrator" — without opening any of the three repos. `test_docs_do_not_advertise_no_arg_construction` still passes: the sentence contains no `Repository()`-shaped literal, and `CLAUDE.md:18`/`README.md:227,408` are already fixed. AC-5 goes green, and with it all five ACs. The item is "done." This exploration itself records that the audit "remains open" and was explicitly not performed here (Constraints discovered, line ~102) — so today, right now, nothing in the tree establishes whether any of the three consumers constructs a repository with no arguments. If one does, flipping `base.py:55-56` from fail-open to a raise breaks that consumer against Dave's live vault path in production — precisely the consequence the campaign flags this item as gating ("breaking for any lazy consumer," `docs/backlog-campaign-2026-07-05.md` line 98) and the reason Dave's sign-off was conditioned on the audit (`docs/backlog-campaign-2026-07-05.md` line 48: "Dave sign-off — breaking change; audit no-arg constructions in all 3 consumers first"). The AC set that is supposed to be this item's machine-checkable definition of done never actually looks.

This is the WI-099/WI-100 "uncovered invocation layer" specimen from the role's record: the ACs cover the function (`base.py`, `lint_vault.py`) but not the surface that calls it across the three consumer repos, so the wiring can be silently broken and every AC still passes green.

**What would have to change:** split (a) and (b) into separate criteria, or narrow AC-5's `desc` to only what `test_docs_do_not_advertise_no_arg_construction` can prove. The audit needs its own falsifiable check in the spirit of the spec-quality-bar's Check 11 (a load-bearing claim needs a falsifiable artifact, not a sentence) — e.g. a recorded scan command and its literal output for each of the three consumer repos, cited by `file:line` in this doc, or a `kind: command` criterion that re-runs the scan at verification time. As drafted, "the audit is recorded" is satisfiable by one unverified string literal — the exact WI-131 gameable-by-a-single-string-literal shape, applied to the item's own breaking-change gate rather than to the code under test.

```verdict
gate: ac-red-team
verdict: REVISE
date: 2026-07-19
model: claude-sonnet-5
note: AC-5 folds the 3-repo consumer-audit build prerequisite into a check that can only scan this repo's own docs — the breaking-change safety gate is satisfiable by a fabricated audit sentence and is never actually verified.
```

## AC Red-Team — 2026-07-19

Re-verify pass, decorrelated cold-start (second spawn of this gate on this doc). Read order per Step 2: Intent → Examples of done → Problem/Motivation + Exploration Notes (including the prior `## AC Red-Team — 2026-07-19` section above, read as carry-forward) → Acceptance Criteria last. Code re-read to check current-state claims: `obsidian_schemas/repositories/base.py` (full), `obsidian_schemas/repositories/{person,company,meeting,book}.py` (`__init__`/forwarding), `scripts/lint_vault.py:1140-1180`, `scripts/migrate_person_to_discuss.py:150-190`, `README.md:215-245,395-410`, `CLAUDE.md:18`, and `/Users/davewascha/Workspaces/workshop/src/work_item_linter.py` (`VALID_WRITE_KINDS`, `PRECONDITION_FENCE_SHAPE`, `COMMAND_REGISTRY_EPOCH`, the AC-red-team `VALID_GATES` entry).

### What changed since the prior fence: the CRITICAL fold held

The prior verdict's finding — AC-5 bundling the unauditable 3-repo consumer-audit claim into a check that can only scan this repo's own docs — is fixed, not just reworded. Independently verified, not taken on the doc's word:

- AC-5 now claims only the in-repo doc scan (`test_docs_do_not_advertise_no_arg_construction`), and its `desc` explicitly disclaims the consumer repos ("says nothing about the consumer repos (see AC-6)").
- AC-6 pins the audit artifact's *shape* only (three fields per repo, 40-hex SHA), and its own `why` line self-discloses "the audit's teeth are the precondition fence, not this test" — an honest, checkable disclaimer rather than an overclaim.
- The actual enforcement this depends on — a `kind: precondition` write-fence that `drive()` checks for git-HEAD membership before arming the builder, authored by the conductor (who, unlike the caged builder, can reach the three sibling repos) — is real code, not aspirational: verified at `work_item_linter.py:57-61` (`VALID_WRITE_KINDS`) and `:100-102` (`PRECONDITION_FENCE_SHAPE`). The doc correctly defers writing that fence to the spec-writer stage ("this is a `## Write Targets` declaration and therefore yours, not the ideation gate's"), consistent with this item's own "three AC-kind doors are shut" analysis — not something this gate should pre-empt.

This is a genuine fix, not a relabeling: the AC set no longer claims to verify something it structurally cannot see.

### MATERIAL — AC-1/AC-3 enumerate blank *string* doors only; a blank *Path*-typed argument is a real, uncovered fifth door of the identical shape

`BaseRepository.__init__`'s signature is `vault_path: Optional[str | Path] = None` (`base.py:43`) — `Path` is an explicitly accepted, and actually-used, input type: `person.py:1150` constructs `CompanyRepository(self.vault_path)`, passing a `Path` object, not a string, into exactly this constructor. `pathlib.Path("")` normalizes to `Path(".")` at construction, independent of anything `BaseRepository.__init__` does — so a caller (inside this repo, or one of the three consumers this item cannot audit) that computes a vault path and passes it in already-wrapped, e.g. `PersonRepository(Path(os.environ.get("SOME_VAR", "")))`, hands `__init__` an already-`Path`-typed, already-cwd-equivalent value that a string-only blank check will not catch.

AC-1's `desc` enumerates exactly four doors — "no arg, `\"\"`, `\"   \"`, and env set to `\"\"` or whitespace" — all string-shaped. AC-3 inherits this via "constructed with no vault_path and no env var" (the no-arg case only). Neither names a `Path`-typed blank argument. A builder implementing the minimal guard that satisfies the four *named* test cases — the natural shape is `if vault_path is None or (isinstance(vault_path, str) and not vault_path.strip()):` — passes `test_unconfigured_vault_path_raises` and `test_all_repositories_raise_when_unconfigured` in full, while `PersonRepository(Path(""))` or `PersonRepository(Path("   "))` sails through the `isinstance(str)` guard untouched, reaches `self.vault_path = Path(vault_path)` at `base.py:58`, and binds to the current working directory (or a bogus literal-whitespace path) — the exact accident-of-omission this item exists to close, reopened one type-hint away from the door it just shut.

**Concrete failure scenario:** the test suite as literally specified by AC-1/AC-3 goes fully green; `PersonRepository(Path(""))` still silently constructs a repository bound to cwd, with write capability intact (`save()` still builds `self.vault_path / filename` and `mkdir(parents=True)`s missing parents) — the Intent's own worked example ("a repository constructed without an explicit path... loud-fails") is violated by an input one property-check away from what's actually tested, and no criterion catches it.

**What would have to change:** reword AC-1 (and AC-3's inherited coverage) from an enumerated literal list to a property — "vault_path is missing, or reduces to an empty/whitespace string regardless of whether it arrives as `str` or `Path`" — and add `Path("")`/`Path("   ")` as explicit test inputs alongside the four already named. This is the same str-literal-vs-property lesson AC-2 already learned once in the first red-team pass (a literal-enumeration check is gameable by a value one shape removed from the named literals); it needs applying inside AC-1 too, not just at AC-2.

### MINOR — AC-5's own citation is stale

AC-5's `desc` names `README.md:227,408` as sites needing an update to "show an explicit path or the env var as required, not optional." Re-read at current tree state: `README.md:228` already reads `repo = PersonRepository("/path/to/vault")` (explicit path) and `README.md:408-409` shows `# Use OBSIDIAN_VAULT_PATH environment variable` / `python scripts/migrate_person_to_discuss.py --apply` (a script that already loud-fails per its own existing guard at `migrate_person_to_discuss.py:171-174`). Neither line advertises no-arg *repository* construction; only `CLAUDE.md:18` does (repo-wide grep for `\w+Repository\(\s*\)` confirms exactly one hit, in `CLAUDE.md`). This doesn't threaten the check's discriminating power if `test_docs_do_not_advertise_no_arg_construction` is built as a general pattern scan (AC-2's already-established model) rather than a literal check against these two specific lines — but the citation is simply wrong and should be corrected before freeze so it doesn't send a builder looking for a fix that isn't there.

```verdict
gate: ac-red-team
verdict: REVISE
date: 2026-07-19
model: claude-sonnet-5
note: Prior CRITICAL (AC-5 unauditable audit claim) fold verified and holds; new MATERIAL finding - AC-1/AC-3 enumerate only string-typed blank doors, leaving a Path("")/Path("   ") door of the identical accident-of-omission shape uncovered (person.py:1150 shows Path-typed args are a real call shape).
```

## AC Red-Team — 2026-07-19

Third pass, decorrelated cold-start (third spawn of this gate on this doc). Read order per Step 2: Intent → Examples of done → Problem/Motivation + Exploration Notes (including both prior `## AC Red-Team — 2026-07-19` sections above, read as carry-forward) → Acceptance Criteria last. Independently re-derived rather than trusted from the prior rounds' citations: re-ran the AC-2 pattern scan (`expanduser`, `Path.home()`, `/Users/`) over `obsidian_schemas/` and `scripts/` myself — exactly one hit in each, `base.py:21` and `lint_vault.py:50`; re-read all four subclass `__init__` methods (`person.py:173`, `company.py:58`, `meeting.py:34`, `book.py:34`) and confirmed each forwards `vault_path` verbatim to `super().__init__`; re-confirmed `person.py:1150` passes `self.vault_path` (a `Path`, per `base.py:58`) into `CompanyRepository(...)` — the concrete site that makes the Path-typed door real rather than hypothetical; re-read `base.py` in full, `lint_vault.py:1140-1180`, and `migrate_person_to_discuss.py:153-179`.

### Both prior folds verified to hold

Round 2's MATERIAL finding (AC-1/AC-3 covered only string-typed blank doors) is fixed in the current text, not merely reworded: AC-1 now states the property "REGARDLESS OF WHETHER IT ARRIVES AS str OR Path" and names `Path("")`/`Path("   ")` as required test inputs; AC-3 explicitly inherits "for EACH unconfigured argument shape AC-1 defines... not the no-arg case alone." Round 2's MINOR finding (AC-5's stale `README.md:227,408` citation) is also fixed: AC-5 now correctly states `README.md:228` already passes an explicit path and `README.md:408-409` already shows the env-var route, with the check pinned as a general pattern scan rather than a line-targeted edit — matching what I independently re-verified by reading those lines. Round 1's CRITICAL fold (AC-5's unauditable 3-repo claim, resolved by re-homing the audit obligation to a `kind: precondition` write fence + AC-6 shape check) still holds; re-examined fresh rather than re-trusted.

### Attacked and held: AC-6's shape-only check

AC-6 pins only the artifact's shape (three fields, 40-hex SHA) and explicitly disclaims truthfulness ("the audit's teeth are the precondition fence, not this test"). Considered whether this is still gameable — e.g. a fabricated audit file with a dummy all-zero SHA passing the format check, or the caged builder later overwriting a genuine conductor-committed audit with fabricated content since `docs/**` is generally builder-writable. Both concerns dissolve on the doc's own terms: the precondition-fence mechanism gates arming on git-HEAD membership *before* the builder starts (so a missing/fabricated audit blocks the build outright rather than being gameable post-hoc), and the doc explicitly frames `kind: precondition` paths as "cage-denied... the builder is design-forbidden from authoring" — a pipeline-level guarantee, not an AC-level one. Whether that cage guarantee is airtight is a question about the workshop pipeline's own enforcement, out of scope for this leaf item's AC set and already the subject of two prior rounds' scrutiny; re-litigating it here would be redesigning settled architecture rather than attacking this item's ACs.

### Attacked and held: lint_vault whitespace-argument edge

Considered whether AC-4 needed the same string-vs-property widening just applied to AC-1/AC-3 — e.g. `--vault "   "` or `OBSIDIAN_VAULT_PATH="   "` slipping past a naive `if not args.vault:` guard (the shape of the in-tree precedent, `migrate_person_to_discuss.py:171`, which is itself only a falsy-check, not a `.strip()`). Traced it through: unlike `Path("")`, `Path("   ")` does not normalize to cwd — it is a literal relative path that will almost never exist, so it still falls through to the pre-existing `vault_path.exists()` check at `lint_vault.py:1174-1176` and exits non-zero regardless. That is a worse error message, not a silent-success corruption path, so it does not meet the bar this gate polices. By contrast the empty-string case (`Path("")` → `Path(".")`, which *always* exists) is the real risk, and AC-4's explicit requirement that the guard run "BEFORE `Path(args.vault)` at line 1173" already closes exactly that door.

No new material or critical finding.

```verdict
gate: ac-red-team
verdict: PROMOTE
date: 2026-07-19
model: claude-sonnet-5
note: Third pass - both prior folds (Path-typed blank door on AC-1/AC-3; stale AC-5 citation) independently re-verified against current tree; no new material finding after attacking AC-6's shape-only audit check and AC-4's lint_vault whitespace edge, both of which dissolve on inspection.
```

## AC Sign-off

```verdict
gate: ac-signoff
verdict: PROMOTE
date: 2026-07-19
reviewer: dave
channel: conversational
signed_at: 2026-07-19T11:46:12+01:00
ac_hash: 7a5468f98ac9
intent_hash: da32901f3c7f
ac_hash_AC-1: b051e2f15439
ac_hash_AC-2: eb365b438852
ac_hash_AC-3: 7854f12b9b4d
ac_hash_AC-4: f981c6f66257
ac_hash_AC-5: f6ec5002fe0d
ac_hash_AC-6: b1674c34084d
artifact: docs/spec-reviews/WI-024-dave-review-2026-07-19.md
```
