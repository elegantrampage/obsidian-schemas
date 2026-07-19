---
id: WI-024
title: "Remove the hardcoded live-vault default path (loud-fail when unconfigured)"
project: obsidian-schemas
stage: specced
created: 2026-07-05
last_touched: 2026-07-19
stage_changed: 2026-07-19
touched_by: spec-writer
tags: [loud-fail, configuration, small-mechanical]
depends_on: []
transitions: ["idea>exploring@2026-07-19@session", "exploring>specced@2026-07-19@session"]
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

Load-bearing **in this tree**? No — verified, not assumed. `DEFAULT_VAULT_PATH` is not re-exported from `repositories/__init__.py`; it has no importer anywhere in the tree; no test references it; and there is **no no-arg repository construction anywhere in this repo** (`grep -n 'Repository(\s*)'` returns exactly one hit, the prose example at `CLAUDE.md:18`). Every one of the four subclasses (`person.py:173`, `company.py:58`, `meeting.py:34`, `book.py:34`) forwards `vault_path` straight to `super().__init__`, so the predicate lives in exactly one place. The single internal repository-constructing call site, `person.py:1150` (`CompanyRepository(self.vault_path)`), passes an explicit path.

**Scope correction (2026-07-19, after the consumer audit landed — architect + data-premise gates both flagged the original wording).** The sentence above is true *of this tree* and **false of production**. `docs/wi-024-consumer-audit.md` records **18 no-arg hits in orchestrator, 16 of them live code** (`src/invariants.py` ×4, `src/queue_writer.py:784`, `src/contact_normalizer.py:510`, plus 10 in `bin/`), and records that `OBSIDIAN_VAULT_PATH` was set **nowhere** at scan time — so today those 16 sites resolve through `DEFAULT_VAULT_PATH`. HAL9000 and Exocortex scan clean. Do not carry "nothing depends on it" forward as a global claim: it is a claim about *this repo's* code only. The blast radius is measured, sized, and remediated (see Prerequisites & Assumptions, P3).

**Verdict: REMOVE.** Uncontested — the predicate is fail-open by construction and nothing *in this repo* depends on it; the out-of-repo dependents are the measured blast radius the audit exists to bound, not a reason to keep the fallback.

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

## Design

### Correction to the Approach's stated mechanism (read this first)

The Approach paragraph says: *"`str(vault_path).strip()` (or equivalent) is what gets tested, so `Path("")` — which `pathlib` has already collapsed to `Path(".")` — is caught alongside `""`."* **That mechanism does not work, and a builder who implements it literally ships a green suite with the door still open.**

`pathlib` collapses `Path("")` to `Path(".")` at the caller's construction, so by the time `__init__` sees it the value stringifies to `"."` — which is one character long and survives `.strip()` intact:

```python
>>> str(Path(""))
'.'
>>> bool(str(Path("")).strip())
True          # <-- a blank-string guard waves it straight through
```

A blank check alone therefore catches `""`, `"   "`, and `Path("   ")` (which pathlib does *not* normalise — it stays literal whitespace) but **not** `Path("")`. Since `Path("")` is precisely the shape AC-1 names as a required test input, and precisely the shape that binds to cwd, the guard needs a **second clause**: a normalised value equal to `Path(".")` is unconfigured. That clause is what makes AC-1's closing sentence — *"Never resolves to `Path(".")`"* — actually true rather than aspirational.

Consequence worth stating plainly, because it is a deliberate behaviour change beyond the blank doors: **an explicit `Repository(".")` or `Repository(Path("."))` also raises.** Binding a write-capable repository to the current working directory is never a thing anyone means to do, and permitting it would leave the `Path("")` door open by definition (the two are indistinguishable after normalisation). A caller who genuinely wants cwd passes `Path.cwd()` — an absolute path, which resolves fine.

### Data model

No new entities, files, or schemas. One new exception type, one new module-private helper, one deleted constant.

**New public exception**, in `obsidian_schemas/repositories/base.py`, defined immediately after the imports and before `ENV_VAULT_PATH`:

```python
class VaultPathNotConfiguredError(ValueError):
    """Raised when a repository is constructed with no usable vault path.

    Loud-fail at the boundary (WI-024): the library has no default vault, so a
    caller that supplies neither an explicit ``vault_path`` nor a non-blank
    ``OBSIDIAN_VAULT_PATH`` is misconfigured and must be told at construction —
    not silently bound to some machine's live vault or to the current working
    directory.

    Subclasses ``ValueError`` so a consumer's existing ``except ValueError``
    still catches: the break degrades to a message change, not an uncaught
    escape.
    """
```

`ValueError` as the base is the repo's established convention for boundary exceptions — `IdentifierError(ValueError)` (`identifier.py:58`), `NameValidationError(ValueError)` (`name_validation.py:125`), `WeakIdentityError(ValueError)` (`name_validation.py:140`). (`BodyTruncationError(Exception)` at `writer.py:30` is the one that deviates; do not follow it here — the `except ValueError` compatibility argument is the whole reason the base class was chosen.)

**Deleted:** `DEFAULT_VAULT_PATH` (`base.py:21`) and the comment above it (`base.py:20`). `ENV_VAULT_PATH = "OBSIDIAN_VAULT_PATH"` (`base.py:22`) **stays** — it is the surviving configuration route.

### Flow

`BaseRepository.__init__` (`base.py:41-62`) today reads, verbatim:

```python
    def __init__(
        self,
        vault_path: Optional[str | Path] = None,
        auto_load: bool = True,
    ):
        ...
        if vault_path is None:
            vault_path = os.environ.get(ENV_VAULT_PATH, DEFAULT_VAULT_PATH)

        self.vault_path = Path(vault_path)
```

The signature is unchanged. Lines 55-56 are replaced by a call to a module-level helper, and line 58 consumes its return value:

```python
def _is_unconfigured(value: object) -> bool:
    """True when *value* names no vault at all.

    A value is unconfigured if it is absent, blank/whitespace-only, or
    normalises to the current directory. The check is on the NORMALISED
    string form, never on ``isinstance(value, str)`` — ``base.py``'s own
    signature accepts ``str | Path`` and ``person.py:1150`` really does pass
    a ``Path``, so a type-gated guard would fail exactly where the library
    calls itself.
    """
    if value is None:
        return True
    text = str(value).strip()
    if not text:
        return True
    return Path(text) == Path(".")


def _resolve_vault_path(vault_path: Optional[str | Path]) -> Path:
    """Resolve the effective vault path, or raise.

    Precedence: explicit argument, then OBSIDIAN_VAULT_PATH. An unconfigured
    argument falls through to the env var (AC-1's conjunction); an
    unconfigured env var after that is the error.
    """
    for candidate in (vault_path, os.environ.get(ENV_VAULT_PATH)):
        if not _is_unconfigured(candidate):
            return Path(str(candidate).strip())
    raise VaultPathNotConfiguredError(UNCONFIGURED_VAULT_MESSAGE)
```

and in `__init__`, replacing lines 55-58:

```python
        self.vault_path = _resolve_vault_path(vault_path)
```

**The message**, a module-level constant so the test can assert against one string rather than a substring guess:

```python
UNCONFIGURED_VAULT_MESSAGE = (
    "No Obsidian vault configured. Pass an explicit vault_path "
    "(e.g. PersonRepository('/path/to/vault')) or set the "
    "OBSIDIAN_VAULT_PATH environment variable. A missing, blank, "
    "whitespace-only, or current-directory ('.') value counts as "
    "unconfigured."
)
```

It contains the literal tokens `vault_path` and `OBSIDIAN_VAULT_PATH`, which is what AC-1 requires ("The message names both routes").

**Branch enumeration** — every path through `_resolve_vault_path`, with the argument shape on the left and env state across the top. `raise` means `VaultPathNotConfiguredError`; a path means `self.vault_path` binds to it.

| `vault_path` argument | env unset / blank / `"."` | env `"/vault"` |
|---|---|---|
| omitted (`None`) | raise | `Path("/vault")` |
| `""` | raise | `Path("/vault")` |
| `"   "` | raise | `Path("/vault")` |
| `Path("")` (≡ `Path(".")`) | raise | `Path("/vault")` |
| `Path("   ")` | raise | `Path("/vault")` |
| `"."` / `Path(".")` | raise | `Path("/vault")` |
| `"/vault"` / `Path("/vault")` | `Path("/vault")` | `Path("/vault")` (argument wins) |
| `" /vault "` | `Path("/vault")` (stripped) | `Path("/vault")` |
| `"./sub"` (≡ `Path("sub")`) | `Path("sub")` | `Path("sub")` (relative but not cwd — allowed) |

The raise happens before `self.auto_load`, `self._cache`, `self._file_map`, and `self._loaded` are assigned, and therefore before any glob, `exists()`, or read — which is AC-3's "at construction, before any glob or read of the filesystem." No filesystem call occurs anywhere in the resolution path.

### Integration points

| File | Change | Detail |
|---|---|---|
| `obsidian_schemas/repositories/base.py` | modify | Delete `DEFAULT_VAULT_PATH` (`:20-21`); add `VaultPathNotConfiguredError`, `UNCONFIGURED_VAULT_MESSAGE`, `_is_unconfigured`, `_resolve_vault_path`; replace `:55-58` with the one-line call; update the `vault_path` docstring at `:50-51` (it currently promises "Falls back to `OBSIDIAN_VAULT_PATH` env var, then default" — the "then default" clause becomes a lie). |
| `obsidian_schemas/repositories/__init__.py` | modify | Add `VaultPathNotConfiguredError` to the `from .base import ...` line (`:8`) and to `__all__` (`:14-20`). |
| `obsidian_schemas/__init__.py` | modify | Re-export `VaultPathNotConfiguredError`, following the existing pattern for `BodyTruncationError` (`:44`, `:108`) and `IdentifierError` (`:70`, `:133`). Consumers catch from the top-level package. |
| `obsidian_schemas/repositories/{person,company,meeting,book}.py` | **unchanged** | All four forward `vault_path` positionally and verbatim: `person.py:173-174`, `company.py:58-59`, `meeting.py:34-35`, `book.py:34-35` — each `super().__init__(vault_path, **kwargs)`. They inherit the guard. Do **not** add per-subclass checks. |
| `obsidian_schemas/repositories/person.py:1150` | **unchanged** | `CompanyRepository(self.vault_path)` — `self.vault_path` is an already-validated `Path` (set by `_resolve_vault_path`), so it re-resolves cleanly. This is the call site that makes the `Path`-typed door real; it is also the reason a `isinstance(str)` guard is forbidden. |
| `scripts/lint_vault.py` | modify | `DEFAULT_VAULT` (`:48-51`) loses `expanduser`; guard added in `main()` before `Path(args.vault)` at `:1173`; module usage docstring (`:7`) updated. |
| `tests/test_vault_path_required.py` | **new** | All six AC tests. |
| `CLAUDE.md`, `README.md`, `docs/wi-024-consumer-audit.md` | **conductor precondition** | Outside the builder's write authority (root files) or evidence the builder must not author (the audit). See Write Targets. |

**`scripts/lint_vault.py` — the demoted mechanism.** This is a *different* mechanism from the base.py one and is changed for its own reason: an implicitly-chosen vault combined with mutating flags (`--fix` at `:1163` rewrites frontmatter and bodies; `--quarantine` at `:1165` renames live notes via `src.rename(dest)` at `:1037`). It is **not** "the same duplication as base.py" — `expanduser("~")` resolves against the *running* user, so B is already fail-closed everywhere except Dave's own laptop while A is fail-open everywhere. Carry that story to WI-026 verbatim.

Current state, verbatim:

```python
# lint_vault.py:48-51
DEFAULT_VAULT = os.environ.get(
    "OBSIDIAN_VAULT_PATH",
    os.path.expanduser("~/Documents/Obsidian/DaveRemoteVault"),
)
# lint_vault.py:1146
        "--vault", type=str, default=DEFAULT_VAULT,
# lint_vault.py:1171-1176
    args = parser.parse_args()

    vault_path = Path(args.vault)
    if not vault_path.exists():
        print(f"Error: vault not found: {vault_path}", file=sys.stderr)
        sys.exit(1)
```

Target state — the shape its sibling `scripts/migrate_person_to_discuss.py:160,171-174` already uses (env-var default of `''`, explicit guard, message naming both routes), **plus** a `.strip()` the sibling lacks:

```python
# replaces :48-51
DEFAULT_VAULT = os.environ.get("OBSIDIAN_VAULT_PATH", "")

# in main(), replacing :1173 and preceding it
    if not args.vault or not args.vault.strip():
        print("Error: no vault path provided.", file=sys.stderr)
        print(
            "Use --vault /path/to/vault or set the OBSIDIAN_VAULT_PATH "
            "environment variable.",
            file=sys.stderr,
        )
        sys.exit(1)

    vault_path = Path(args.vault.strip())
```

The guard **must precede** `Path(args.vault)`. If `DEFAULT_VAULT` merely became `None`, argparse would yield `args.vault is None` and `Path(None)` raises `TypeError` — a traceback, not a message naming both routes (AC-4). The `.strip()` matters for the same reason it does in the library: `--vault ""` gives `Path("")` → `Path(".")` → `exists()` is True → lint runs against the current working directory, and with `--quarantine` it would rename files there. `--vault "   "` is caught by the strip; even without it, `Path("   ")` does not normalise to cwd and would fall through to the pre-existing `exists()` check — a worse message, not a corruption path.

Message text is written to **stderr** (matching the existing `:1175` convention) and exits `1`. It differs from `migrate_person_to_discuss.py:172-173`, which prints to stdout — follow lint_vault's own local convention, not the sibling's, since the surrounding error at `:1175` already uses stderr.

Note deliberately **not** changed: `DEFAULT_VAULT`'s import-time `os.environ` read means a var mutated after import is ignored. Latent, real, out of scope — routed to WI-026 (see Non-goals).

### Configuration

| Setting | Where | Default | Valid range |
|---|---|---|---|
| `OBSIDIAN_VAULT_PATH` | process environment | **none** (previously `/Users/davewascha/Documents/Obsidian/DaveRemoteVault`) | any non-blank path string that does not normalise to `.` |
| `vault_path` constructor argument | caller code | `None` | `str` or `Path`; same non-blank, non-`.` rule |
| `--vault` | `scripts/lint_vault.py` CLI | `os.environ.get("OBSIDIAN_VAULT_PATH", "")` | same |

There is no toggle, no feature flag, and no opt-in escape hatch. A3 (`Repository(use_default=True)`) was rejected during exploration precisely because an opt-in flag is a second door someone eventually walks through.

### Prerequisites & Assumptions

Explicit, and each one is a real gate on this build:

- **P1 — Python ≥ 3.10.** `base.py:43` already uses `str | Path` in an annotation evaluated at runtime, so the floor predates this item. No new requirement.
- **P2 — the consumer-audit artifact is in git HEAD before the builder is armed.** `docs/wi-024-consumer-audit.md` is a `kind: precondition` write target; `drive()` probes HEAD membership and refuses the drive if it is absent. It is currently committed (`c64e054`). The caged builder cannot reach HAL9000, Exocortex, or orchestrator, so it can neither perform nor amend this audit.
- **P3 — the orchestrator remediation is live, and recorded in the audit artifact, before merge.** This is the one prerequisite that is about Dave's *machine*, not about any file in this repo, and it is the only load-bearing premise no gate has been able to verify (data-premise gate, carry-forward flag 2). The audit records that `OBSIDIAN_VAULT_PATH` was set **nowhere** at scan time and that 16 live orchestrator sites construct repositories with no argument — so absent the remediation, this build breaks orchestrator the moment it merges. The remediation is `export OBSIDIAN_VAULT_PATH="/Users/davewascha/Documents/Obsidian/DaveRemoteVault"` in `~/.zshenv`. **The conductor must amend `docs/wi-024-consumer-audit.md` with a `remediation_confirmed` record — the literal `zsh -c 'echo $OBSIDIAN_VAULT_PATH'` command and its verbatim non-empty output — and commit it before the builder is armed.** AC-6 tests for that record; if it is missing, the AC battery fails loudly at `building → done` and the build does not land. The builder cannot fix this: it must not fabricate an assertion about Dave's shell environment.
- **P4 — no service must be running.** This is a pure library + script change. HAL9000 and Exocortex need not be up; nothing is called over a network; no credentials, OAuth scopes, or MCP permissions are involved.
- **P5 — the test suite is hermetic and must stay so.** There is no `conftest.py` in the repo (verified) and zero tests reference `OBSIDIAN_VAULT_PATH` (verified). The new tests **must** use `monkeypatch.delenv(..., raising=False)` / `monkeypatch.setenv(...)` so they pass identically on a machine where the variable is legitimately set — which, after P3, is Dave's. The campaign's rider ("no test may ever touch `OBSIDIAN_VAULT_PATH`") is a wording trap: the real property is *no test depends on ambient environment*, and monkeypatching is how you get it.
- **P6 — the stale editable install is load-bearing and untouched.** `_obsidian_schemas.pth` points at a dead path; a bare `import obsidian_schemas` fails; the suite works because pytest prepends its rootdir. Nothing in this change touches packaging. Do not "fix" the `.pth`. Under the cage this is *correct*: the suite imports the worktree's `obsidian_schemas`, so the build tests the code it just wrote (`pipeline-runners.yaml:10-17`).
- **P7 — trust boundary.** The vault path is configuration, not user input: it arrives from the caller's own code or the process environment, both of which are already inside the trust boundary. This change does not introduce a new boundary — it *closes* one, by removing the case where the library supplies a filesystem path nobody asked for. No escaping, sanitisation, or path-traversal defence is in scope; the value is used as a path, exactly as it is today.
- **P8 — no state is migrated and no data is written.** The change adds a refusal; it never creates, moves, or deletes a vault file.

## Edge Cases & Open Questions

- **Empty / null / malformed input** — **Case:** `vault_path` arrives as `None`, `""`, `"   "`, `Path("")`, `Path("   ")`, `"."`, `Path(".")`, or `OBSIDIAN_VAULT_PATH` is unset / `""` / `"   "` / `"."`. **Decision:** every one raises `VaultPathNotConfiguredError` with `UNCONFIGURED_VAULT_MESSAGE`; the branch table above enumerates all of them. **Reasoning:** this is the item. The property is stated on the *normalised* value regardless of arrival type, not as an enumeration of literals — an enumeration is always gameable by a value one shape removed from the list, which is how the `Path("")` door survived two AC drafts. *Tested by:* `test_unconfigured_vault_path_raises`, `test_all_repositories_raise_when_unconfigured`.
  A malformed-but-non-blank path (`"/does/not/exist"`, `"\x00"`) is **out of scope** — accident of *commission*, routed to WI-020. `Path("\x00")` raises `ValueError` from pathlib itself on use, which is loud enough.

- **Race conditions / concurrent access** — **Not applicable.** `_resolve_vault_path` is a pure function of its argument and one `os.environ.get`; it holds no lock, mutates no shared state, and touches no file. Two threads constructing repositories concurrently cannot interfere. The only shared mutable state in the neighbourhood is `os.environ` itself, and reading it is atomic at the granularity that matters here.

- **External dependency failure** — **Not applicable.** No API, no service, no network. The nearest thing to an external dependency is `os.environ`, whose failure mode (unset) *is* the handled case.

- **First-run vs subsequent-run** — **Not applicable.** Construction is stateless with respect to prior runs. There is no cache file, no marker, no bootstrap.

- **Migration / backfill** — **Case:** 16 live orchestrator call sites currently resolve through `DEFAULT_VAULT_PATH` and will raise after the flip. **Decision:** migrate the *environment*, not the code — `export OBSIDIAN_VAULT_PATH` in `~/.zshenv`, per P3 and the audit's remediation section. No code in any consumer changes; no data is backfilled. **Reasoning:** those 16 sites are already written in the no-arg + env-var idiom, so supplying the env var makes them correct rather than merely working. Relocating machine-specific configuration to the machine is the point of the item. *Tested by:* `test_consumer_audit_artifact_is_complete` (pins that the remediation was confirmed, not merely planned).

- **Idempotency** — **Case:** the change is re-applied, or a repository is constructed twice with the same input. **Decision:** both are safe. `_resolve_vault_path` is pure and referentially transparent; constructing N repositories yields N identical bindings and no side effects. The edit itself is a deletion plus a guard — re-running the build against an already-built tree is a no-op. **Reasoning:** nothing is written, so there is nothing to make non-idempotent.

- **Retry semantics** — **Case:** a caller catches the error and retries. **Decision:** the failure is **permanent, never transient** — retrying without changing the argument or the environment raises again, identically and immediately. Callers must not retry-with-backoff. **Reasoning:** a configuration error has no time dimension; presenting it as retryable would invite exactly the retry loop that makes misconfiguration look like flakiness.

- **Partial failure** — **Case:** the change lands in `base.py` but not in `lint_vault.py` (or vice versa), e.g. an aborted build resumed mid-plan. **Decision:** the two are independent and each is individually correct; there is no intermediate state in which the tree is *worse* than today. Task ordering (base first, script second) is chosen so the higher-blast-radius library change is complete and tested before the script is touched. The Implementation Plan's checkboxes are the resume point. **Reasoning:** no shared state couples the two changes — they share only the `OBSIDIAN_VAULT_PATH` name, which is a string constant in each.

- **Error propagation** — **Case:** what does an existing caller see? **Decision:** `VaultPathNotConfiguredError`, which **is a `ValueError`** — so a consumer's existing `except ValueError:` still catches it and the break degrades to a message change rather than an uncaught escape. The traceback's innermost repo frame is `_resolve_vault_path`, one frame below the caller's own `PersonRepository(...)` line, so the stack points at the offending caller. **Reasoning:** A2 (raise lazily at first I/O) was rejected exactly here — it would let a misconfigured repository be constructed, stored on a service object, and blow up later at a call site with nothing to do with the bug. *Tested by:* `test_unconfigured_vault_path_raises` asserts `issubclass(VaultPathNotConfiguredError, ValueError)` and that `pytest.raises(ValueError)` catches it.
  **Known interaction, deliberately not fixed here:** `person.py:1147-1160`'s bare `except Exception` would swallow the new error if that call site ever stopped passing an explicit path. Its predicate cannot fire today (`:1150` passes `self.vault_path`, always validated). Bare-except narrowing is WI-020's territory — solve in one place.

- **Trust boundary crossings** — **Not applicable** in the input-validation sense; see P7. The vault path is configuration from inside the trust boundary, and this change reduces the surface by removing a path the library invented on its own.

- **What-if from exploration: a test machine where `OBSIDIAN_VAULT_PATH` is legitimately set** (which, after P3, is Dave's) — **Case:** the invariant tests assert a raise, but the ambient env var would satisfy the guard and no raise occurs. **Decision:** every test that asserts the unconfigured behaviour calls `monkeypatch.delenv("OBSIDIAN_VAULT_PATH", raising=False)` first; every test that asserts blank-env behaviour uses `monkeypatch.setenv`. **Reasoning:** this is P5, and it is the single most likely way this item's own suite goes silently wrong — a green run on a clean machine, a red run on Dave's, or worse, a test that passes for the wrong reason. *Tested by:* all of `test_unconfigured_vault_path_raises`, `test_all_repositories_raise_when_unconfigured`, `test_lint_vault_requires_explicit_vault` (the last passes a scrubbed `env` dict to `subprocess.run`).

- **What-if: the AC-2 scan false-flags a legitimate use** — **Case:** the pattern scan for `expanduser` / `Path.home()` / `/Users/` hits a line that is fine. **Decision:** the scan skips comment lines and docstrings, and after this change the tree has **zero** live matches in either directory (verified: exactly one hit each today, `base.py:21` and `lint_vault.py:50`, and both are deleted by this item). Any future hit is a genuine regression. **Reasoning:** a scan that must maintain an exception list is a scan nobody trusts; zero-match is the only maintainable resting state. *Tested by:* `test_no_implicit_vault_path_defaults`.

**OPEN: None.**

## Implementation Plan

Tasks 1–3 are strictly ordered (each depends on the previous). Tasks 4–5 (the `lint_vault.py` leg) are independent of 1–3 and may be done in parallel with them. Tasks 6–7 depend on nothing but are cheapest last. **Verify commands assume cwd is the repo root**; the floor command is absolute and cwd-independent either way.

Floor command, referenced throughout:

```bash
/Users/davewascha/Workspaces/obsidian-schemas/.venv/bin/python -m pytest \
    /Users/davewascha/Workspaces/obsidian-schemas/tests -q
```

Baseline before this work: **563 passed, exit 0**. After it: 563 + the new cases, exit 0. A run that lands *fewer* than 563 pre-existing cases means a test file was lost — stop and investigate rather than proceeding.

- [ ] **Task 1 — Add the exception, the message constant, and the resolution helpers to `base.py`.** Modify `obsidian_schemas/repositories/base.py`: delete `DEFAULT_VAULT_PATH` and its comment (`:20-21`); add `VaultPathNotConfiguredError`, `UNCONFIGURED_VAULT_MESSAGE`, `_is_unconfigured`, and `_resolve_vault_path` exactly as given in Design > Data model and Design > Flow; leave `ENV_VAULT_PATH` in place. Do not yet wire `__init__`.
  *Verify:* `/Users/davewascha/Workspaces/obsidian-schemas/.venv/bin/python -m pytest /Users/davewascha/Workspaces/obsidian-schemas/tests -q` still reports **563 passed** (nothing consumed the constant, so deleting it changes no behaviour yet), and `grep -n 'DEFAULT_VAULT_PATH' obsidian_schemas/repositories/base.py` returns nothing.

- [ ] **Task 2 — Wire the guard into `BaseRepository.__init__` and correct its docstring.** Replace `base.py:55-58` with `self.vault_path = _resolve_vault_path(vault_path)`. Update the `vault_path:` docstring line (`:50-51`) — it currently promises "Falls back to `OBSIDIAN_VAULT_PATH` env var, then default"; it must now say the argument is required unless `OBSIDIAN_VAULT_PATH` is set, and that a blank or current-directory value counts as unconfigured.
  *Verify:* floor command still **563 passed** (every existing test passes an explicit `tmp_path`), and this one-liner raises rather than returning a repository:
  ```bash
  env -u OBSIDIAN_VAULT_PATH /Users/davewascha/Workspaces/obsidian-schemas/.venv/bin/python -c \
    "import sys; sys.path.insert(0,'.'); from obsidian_schemas import PersonRepository; PersonRepository()"
  ```
  Expect a non-zero exit with `VaultPathNotConfiguredError` and both `vault_path` and `OBSIDIAN_VAULT_PATH` in the message.

- [ ] **Task 3 — Export `VaultPathNotConfiguredError` from both `__init__` files.** Add it to the `from .base import ...` line and `__all__` in `obsidian_schemas/repositories/__init__.py` (`:8`, `:14-20`), and re-export it from `obsidian_schemas/__init__.py` following the `BodyTruncationError` pattern at `:44` / `:108`.
  *Verify:*
  ```bash
  /Users/davewascha/Workspaces/obsidian-schemas/.venv/bin/python -c \
    "import sys; sys.path.insert(0,'.'); import obsidian_schemas as o; \
     assert issubclass(o.VaultPathNotConfiguredError, ValueError); print('ok')"
  ```

- [ ] **Task 4 — Demote `lint_vault.py`'s implicit vault default.** In `scripts/lint_vault.py`: replace `:48-51` with `DEFAULT_VAULT = os.environ.get("OBSIDIAN_VAULT_PATH", "")`; add the blank guard in `main()` **before** `Path(args.vault)` at `:1173` and change that line to `Path(args.vault.strip())`, exactly as given in Design > Integration points; update the module usage docstring (`:7`) so `python scripts/lint_vault.py` is no longer shown without `--vault`. Leave `argparse`'s `default=DEFAULT_VAULT` at `:1146` alone.
  *Verify:*
  ```bash
  env -u OBSIDIAN_VAULT_PATH /Users/davewascha/Workspaces/obsidian-schemas/.venv/bin/python \
      scripts/lint_vault.py; echo "exit=$?"
  ```
  Expect `exit=1` and a stderr message naming both `--vault` and `OBSIDIAN_VAULT_PATH`. Then confirm the happy path still works: `.venv/bin/python scripts/lint_vault.py --vault /tmp -q` runs the linter against an empty directory without error.

- [ ] **Task 5 — Write `tests/test_vault_path_required.py` with the four behavioural tests.** New file. `test_unconfigured_vault_path_raises` (AC-1) — parametrised over `[None-sentinel, "", "   ", Path(""), Path("   "), ".", Path(".")]` with `monkeypatch.delenv("OBSIDIAN_VAULT_PATH", raising=False)`, plus the env-blank cases (`monkeypatch.setenv("OBSIDIAN_VAULT_PATH", "")` and `"   "`) with no argument; asserts `VaultPathNotConfiguredError`, that it is caught by `pytest.raises(ValueError)`, and that `str(exc.value)` contains both `"vault_path"` and `"OBSIDIAN_VAULT_PATH"`. `test_all_repositories_raise_when_unconfigured` (AC-3) — the cross-product of `[PersonRepository, CompanyRepository, MeetingRepository, BookRepository]` × every argument shape above, env deleted; also asserts the raise happens before filesystem access by monkeypatching `pathlib.Path.glob` to a function that fails the test if called. `test_lint_vault_requires_explicit_vault` (AC-4) — `subprocess.run([sys.executable, "scripts/lint_vault.py"], env={k: v for k, v in os.environ.items() if k != "OBSIDIAN_VAULT_PATH"}, cwd=<repo root>, capture_output=True, text=True)`; asserts `returncode != 0`, and that `--vault` and `OBSIDIAN_VAULT_PATH` both appear in `stderr`. Add a fourth case in the same test for `--vault ""` asserting the same refusal (the cwd-binding door). Derive the repo root from `Path(__file__).parent.parent`, never from cwd.
  *Verify:* floor command reports **563 + new** passed, exit 0. Then run it from a foreign cwd to confirm hermeticity: `cd /tmp && /Users/davewascha/Workspaces/obsidian-schemas/.venv/bin/python -m pytest /Users/davewascha/Workspaces/obsidian-schemas/tests -q`. Then run it once with the variable deliberately set — `OBSIDIAN_VAULT_PATH=/tmp <floor command>` — and confirm the same pass count; a difference means a test is reading ambient environment (P5).

- [ ] **Task 6 — Add the two scan tests to `tests/test_vault_path_required.py`.** `test_no_implicit_vault_path_defaults` (AC-2) — walk every `*.py` under `obsidian_schemas/` and `scripts/`, skip blank/comment lines and lines inside triple-quoted blocks (track a simple in-docstring toggle on `"""` / `'''`), and assert **zero** lines contain `expanduser`, `Path.home()`, or the literal `/Users/`; additionally assert `not hasattr(obsidian_schemas.repositories.base, "DEFAULT_VAULT_PATH")`. `test_docs_do_not_advertise_no_arg_construction` (AC-5) — walk every tracked `*.md` **excluding `docs/**` and `state/**`** (those are pipeline records that quote the antipattern as evidence, not documentation that advertises it — see the AC-5 refinement note) and assert the regex `\w+Repository\(\s*\)` has zero matches. Resolve the repo root from `Path(__file__).parent.parent`.
  *Verify:* floor command green. Deliberately break each once to confirm the test discriminates — temporarily add `x = os.path.expanduser("~")` to a scanned file and confirm `test_no_implicit_vault_path_defaults` fails; temporarily add `repo = PersonRepository()` to `README.md` and confirm `test_docs_do_not_advertise_no_arg_construction` fails. **Revert both before finishing** (and note `README.md` is outside the write authority, so any accidental edit is reverted by the cage anyway).

- [ ] **Task 7 — Add the consumer-audit shape test.** `test_consumer_audit_artifact_is_complete` (AC-6) in the same file. Read `docs/wi-024-consumer-audit.md`. For each of `HAL9000`, `Exocortex`, `orchestrator`, locate the `## <repo>` section and assert three things within it: a line beginning `Command:` followed by a fenced block containing a non-empty command; an `Output` field that is either a fenced verbatim block or an explicit no-matches marker (the literal string `no matches`) — an *absent* Output field fails; and a `HEAD:` line whose value matches `^[0-9a-f]{40}$`. Then assert a `remediation_confirmed` record exists containing the literal `zsh -c 'echo $OBSIDIAN_VAULT_PATH'` and a non-empty output value. The test **does not re-run any scan** and must make no subprocess or network call.
  *Verify:* floor command green. If `remediation_confirmed` is absent the test fails — that is correct and is P3 doing its job; **do not add the record yourself**, and do not weaken the assertion. Report the failure and stop: the conductor must amend and commit the artifact.

## Write Targets

```writes
path: obsidian_schemas/repositories/base.py
why: Tasks 1-2 — delete DEFAULT_VAULT_PATH, add VaultPathNotConfiguredError + the resolution helpers, wire the guard into __init__.
```

```writes
path: obsidian_schemas/repositories/__init__.py
why: Task 3 — re-export VaultPathNotConfiguredError.
```

```writes
path: obsidian_schemas/__init__.py
why: Task 3 — top-level re-export, following the BodyTruncationError/IdentifierError pattern.
```

```writes
path: scripts/lint_vault.py
why: Task 4 — demote the implicit vault default and guard before Path(args.vault).
```

```writes
path: tests/test_vault_path_required.py
why: Tasks 5-7 — the six AC tests (new file).
```

```writes
kind: precondition
path: docs/wi-024-consumer-audit.md
why: P3 / Task 7 — the conductor performs and records the three-repo audit AND the remediation_confirmed entry; the caged builder cannot reach HAL9000/Exocortex/orchestrator and must not assert anything about Dave's shell environment, so it is design-forbidden from authoring this file.
```

```writes
kind: precondition
path: CLAUDE.md
why: AC-5 / Task 6 — CLAUDE.md:18 (`repo = PersonRepository()`) is the one live doc site and must become an explicit path, but the project root is outside this repo's write_authority (pipeline-runners.yaml:32-38), so a caged write is reverted; the conductor commits it before the build.
```

```writes
kind: precondition
path: README.md
why: AC-5 — README.md:227's comment ("or uses OBSIDIAN_VAULT_PATH env var") must read as required-one-of-two rather than optional; same root-path write_authority exclusion as CLAUDE.md, so the conductor commits it. (README.md:228 already passes an explicit path and 408-409 already show the env-var route — no code sample changes.)
```

**Why three preconditions rather than declaring the paths and hoping.** `pipeline-runners.yaml:34-38` declares this project's write authority as `obsidian_schemas/**`, `tests/**`, `scripts/**`, `docs/**`, with the comment at `:32-33` stating the root is absent on purpose ("CLAUDE.md / README.md / SESSION_LOG.md / pyproject.toml are conductor-owned session-end work outside the cage"). Declaring `CLAUDE.md` as `kind: file` would be blocked by D7b at `→ ready`; writing it anyway inside the cage would be reverted after the spawn. `docs/wi-024-consumer-audit.md` *is* inside the write authority, but is declared `precondition` for a different reason — it is evidence about three repos the builder cannot see, and a builder-authored version of it would be fabrication. That distinction is the point of the fence kind.

## Verification

**Happy path (smoke test).** With a real vault path supplied, everything behaves exactly as before:

```bash
mkdir -p /tmp/wi024-vault
/Users/davewascha/Workspaces/obsidian-schemas/.venv/bin/python -c \
  "import sys; sys.path.insert(0,'.'); from obsidian_schemas import PersonRepository; \
   r = PersonRepository('/tmp/wi024-vault'); print(r.vault_path, len(r))"
```
Expect `/tmp/wi024-vault 0` — construction succeeds, load runs, no error. Then the env-var route:
```bash
OBSIDIAN_VAULT_PATH=/tmp/wi024-vault /Users/davewascha/Workspaces/obsidian-schemas/.venv/bin/python -c \
  "import sys; sys.path.insert(0,'.'); from obsidian_schemas import PersonRepository; \
   print(PersonRepository().vault_path)"
```
Expect `/tmp/wi024-vault`.

**Failure modes — each must fail *gracefully*, i.e. a named exception or a non-zero exit with a message, never a traceback from pathlib and never a silent bind:**

| Scenario | Expected observable |
|---|---|
| `PersonRepository()` with env unset | `VaultPathNotConfiguredError`, message contains `vault_path` and `OBSIDIAN_VAULT_PATH` |
| `PersonRepository("")` / `PersonRepository("   ")` | same |
| `PersonRepository(Path(""))` / `PersonRepository(Path("   "))` | same — **this is the door the naive guard leaves open; check it explicitly** |
| `PersonRepository(".")` / `PersonRepository(Path("."))` | same |
| `OBSIDIAN_VAULT_PATH=""` + no argument | same |
| `python scripts/lint_vault.py` with env unset | exit 1, stderr names both routes, **no `TypeError`** |
| `python scripts/lint_vault.py --vault ""` | exit 1, same message — must not lint the current directory |

**Integration — downstream consumers, named.** All three install this library with `pip install -e`. Per `docs/wi-024-consumer-audit.md`: HAL9000 (HEAD `8ee5bf2a…`) and Exocortex (HEAD `75763aa9…`) have **zero** no-arg construction sites and are unaffected. orchestrator (HEAD `114b258c…`) has **16 live sites** which survive the flip **iff** `OBSIDIAN_VAULT_PATH` is exported — P3. After the export is live, confirm the highest-traffic sites still work:

```bash
zsh -c 'echo $OBSIDIAN_VAULT_PATH'        # must print a non-empty path — this IS the merge gate
zsh -c 'cd /Users/davewascha/Workspaces/orchestrator && .venv/bin/python -m pytest tests -q'
```

The orchestrator suite is the integration check; `src/invariants.py` (×4), `src/queue_writer.py:784`, and `src/contact_normalizer.py:510` are the live library-facing sites it covers. `bin/identity-parity-replay.py:66` self-documents as `# default/env vault, read-only` — after the flip it raises like the rest unless the env var is set; that is expected behaviour, not a regression, and is worth a line in the remediation record.

**Regression.** The floor command must report **563 pre-existing cases still passing**, exit 0, from a foreign cwd — the count is the tripwire for a silently lost test file. `tests/test_repositories.py` is the file most likely to be disturbed (every test there constructs repositories with an explicit `tmp_path`/`tempfile` path, so every one exercises the new happy path).

## Verified Diagnosis

Three load-bearing diagnostic claims. If any were false, the work would be invalid or wrongly shaped.

**Claim 1 — the fallback is reached by omission and is write-capable, so a forgetful caller silently binds to the live vault.** Artifact: `base.py:55-56` reads `if vault_path is None: vault_path = os.environ.get(ENV_VAULT_PATH, DEFAULT_VAULT_PATH)`, with `DEFAULT_VAULT_PATH = "/Users/davewascha/Documents/Obsidian/DaveRemoteVault"` at `base.py:21`. The predicate is the argument's absence — not the machine, the user, or the environment. Write capability: `save()` builds `file_path = self.vault_path / filename` at `base.py:202` and calls `write_markdown_file`, which creates missing parents. Nothing observes the mistake: `load()` on a non-existent vault logs a WARNING and returns 0 (`base.py:96-99`), so the repository presents as a legitimately empty vault.

**Claim 2 — a `Path`-typed blank argument reaches a cwd binding, and a blank-*string* guard does not stop it.** Artifacts: (a) the signature accepts it — `vault_path: Optional[str | Path] = None` at `base.py:43`; (b) the library really passes a `Path` into its own constructor — `person.py:1150` is `CompanyRepository(self.vault_path)`, and `self.vault_path` is a `Path` by `base.py:58`; (c) the normalisation is pathlib's, not this code's — runnable: `python -c "from pathlib import Path; print(repr(str(Path(''))), bool(str(Path('')).strip()))"` prints `'.' True`, which is the falsifiable proof that `str(x).strip()` alone does **not** catch `Path("")`. This claim is what forces the second guard clause in Design, and it is a correction to the Approach's own stated mechanism.

**Claim 3 — the flip breaks 16 live orchestrator call sites unless the environment is remediated first.** Artifact: `docs/wi-024-consumer-audit.md`, which records the literal scan command, its verbatim 18-line stdout, and HEAD `114b258cd900075f5505b942835be230e9a2fb39` for orchestrator; 16 of the 18 are live code and 2 are test-file strings (`:67-68`). The same artifact records that `OBSIDIAN_VAULT_PATH` was set nowhere at scan time (`:70-71`).
  **Sub-claim demoted — `[hypothesis — needs verification]`:** *"`OBSIDIAN_VAULT_PATH` is set nowhere on Dave's machine."* This is an assertion about a machine, not about any file in this repo, and no gate has been able to run `zsh -c 'echo $OBSIDIAN_VAULT_PATH'`, read `~/.zshenv`, or list launchd jobs. It is recorded as the audit's finding, not as verified fact, and it is dated 2026-07-19 — it can rot. It is **not load-bearing for the design**: the guard is correct whether or not the variable is set. It is load-bearing only for the *merge*, which is exactly why P3 converts it into a checkable artifact property (`remediation_confirmed`) that AC-6 tests, rather than leaving it as a prose bullet at `docs/wi-024-consumer-audit.md:76-77` that nothing observes.

**Explicitly not diagnosed here** (asserted by neither this spec nor its ACs): that a "configured but wrong" path silently degrades (`base.py:96-99`), and that `person.py:1147-1160`'s bare `except Exception` is too broad. Both are real, both are routed to WI-020, and neither is load-bearing for this item.

## Scope Boundary

**What we're NOT doing:**

- **Validating that a configured path exists or looks like a vault.** A typo'd `OBSIDIAN_VAULT_PATH` still binds silently; `load()` warns and returns 0. That is accident of *commission*, a different predicate, and the same class as WI-020's silent-degrade boundaries. **Route to WI-020.** (Rejected as approach A5 during exploration, deliberately.)
- **Narrowing `person.py:1147-1160`'s bare `except Exception`.** Its predicate cannot fire today. **WI-020.**
- **Fixing `lint_vault.py`'s import-time `os.environ` read** at `:48` — a var mutated after import is ignored. Latent, real, **WI-026**.
- **Any other `lint_vault.py` safety work** — `--fix` and `--quarantine` hardening is **WI-026**. This item touches only the vault-selection lines.
- **A deprecation period, a warning, or an opt-in flag.** A4 and A3 were rejected during exploration; Dave signed off on the break on 2026-07-05. Do not soften the raise into a warning, and do not add `use_default=True`.
- **Fixing the stale `_obsidian_schemas.pth` editable install.** Load-bearing as-is (P6). Leave it.
- **Adding a `conftest.py`.** The suite has none and its absence is part of the hermeticity property (P5). Use `monkeypatch` per-test.
- **Changing any consumer repo's code.** The remediation is an environment export, not a code change, and the three consumer repos are outside this project's scope entirely.

**Unchanged files — do not touch:**

- `obsidian_schemas/repositories/person.py`, `company.py`, `meeting.py`, `book.py` — all four already forward `vault_path` verbatim and inherit the guard. Adding a per-subclass check would violate the one-place constraint.
- `obsidian_schemas/writer.py`, `parser.py`, `models.py`, `identifier.py`, `name_validation.py`, `name_cleaning.py`, `body_sections.py` — untouched by this item.
- `scripts/migrate_person_to_discuss.py` — it is the *model* being followed, not a target.
- `tests/test_repositories.py` and every other existing test file — the new tests go in a new file; existing tests already pass explicit paths and must keep passing unmodified.
- `pipeline-runners.yaml`, `pyproject.toml`, `state/**`, `SESSION_LOG.md` — conductor-owned or pipeline-owned; `pipeline-runners.yaml` and `state/**` are cage-denied outright.
- `CLAUDE.md`, `README.md`, `docs/wi-024-consumer-audit.md` — conductor preconditions (see Write Targets). The builder reads them; it does not write them.

## Risk Analysis

This touches a library three repos install, so it qualifies as core-workflow work.

| # | What could go wrong | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R1 | orchestrator breaks on merge because the env var was never exported — 16 live sites raise on construction, and `bin/` scripts Dave runs by hand start failing. | **High if unmitigated** — the audit found the var set nowhere on 2026-07-19. | High but **loud and immediate**: a `VaultPathNotConfiguredError` at construction, not silent corruption. | P3: `~/.zshenv` export, *confirmed* via `zsh -c 'echo $OBSIDIAN_VAULT_PATH'` and recorded as `remediation_confirmed` in the audit artifact, which AC-6 tests. This converts the merge gate from a remembered prose bullet into a machine-checked artifact property — the WI-115 shape the architect gate flagged. |
| R2 | The builder implements a blank-*string* guard, the suite goes green, and `Repository(Path(""))` still binds to cwd. | **Moderate** — it is the natural minimal implementation and it survived two AC drafts. | High: the item ships believing it closed a door it left open, and cwd binding is write-capable. | The Design section leads with the correction and the runnable proof; AC-1/AC-3 name `Path("")`/`Path("   ")` as required inputs; the branch table enumerates them; Verification lists the row explicitly. |
| R3 | A new test reads ambient `OBSIDIAN_VAULT_PATH` and passes on a clean machine but fails (or passes for the wrong reason) on Dave's — which, post-P3, has the var set. | **Moderate** | Moderate: an unreliable floor is worse than a missing test. | P5 + Task 5's verify step runs the floor command a second time with `OBSIDIAN_VAULT_PATH=/tmp` and requires an identical pass count. |
| R4 | A future non-shell context — a new launchd job, an IDE test runner — invokes orchestrator code without the env var. | Low | Low, and **by design**: it loud-fails at construction. | Accepted, and recorded as residual risk in the audit artifact (`:78-80`). This is WI-024 working, not regressing. |
| R5 | The AC-5 doc scan is written against `CLAUDE.md`/`README.md` line numbers and goes stale. | Low | Low | AC-5 mandates a general pattern scan (AC-2's model), not a line-targeted check; the plan and the AC both say so. |

**Rollback.** `git revert` of the build commit. The change is a deletion plus a guard in one `__init__` plus one script guard — there is no migration to unwind, no data written, and no persisted state. The `~/.zshenv` export is independently harmless and can stay after a revert (it simply becomes redundant).

**Migration path.** Environment-first, code-never: export the variable (P3) → confirm and record it → merge the flip. The 16 orchestrator sites are already written in the no-arg + env-var idiom, so supplying the variable makes them *correct*, not merely working. No shadow mode and no feature flag — A4 was rejected on the grounds that a warning is the silent degrade wearing a hat, and the loud failure at construction is the whole product.

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
desc: No in-repo documentation advertises no-arg repository construction. Implemented as a general pattern scan over this repo's tracked .md files (AC-2's model), NOT a literal check against named lines. Scan scope excludes docs/** and state/**, which are work-item pipeline RECORDS that quote the antipattern as evidence (this doc, the audit artifact, and the spec-review artifact all contain it deliberately) — quoting a defect as evidence is not advertising it. The one live site at time of writing is CLAUDE.md:18 (`repo = PersonRepository()`); a repo-wide grep for `\w+Repository\(\s*\)` returns that single hit — README.md:228 already passes an explicit path and README.md:408-409 already shows the env-var route, so neither needs changing. README.md:227's comment ("or uses OBSIDIAN_VAULT_PATH env var") should read as required-one-of-two rather than optional. Scoped to this repo's own tracked .md files; says nothing about the consumer repos (see AC-6).
kind: test
check: test_docs_do_not_advertise_no_arg_construction
```

why: the Quick Start is the most-copied line in the repo — leaving `PersonRepository()` in it after the break turns a clear error into a documentation bug; and this check can only read files inside this repo, so that is all it is permitted to claim.

```criteria
id: AC-6
desc: docs/wi-024-consumer-audit.md exists and carries, for EACH of HAL9000, Exocortex, and orchestrator, three fields — the literal scan command run, that command's verbatim stdout (empty output recorded as an explicit "no matches" marker, not an absent field), and the 40-char git HEAD SHA of the repo as scanned. It ALSO carries a remediation_confirmed record: the literal `zsh -c 'echo $OBSIDIAN_VAULT_PATH'` command and its verbatim NON-EMPTY output, proving the export the 16 live orchestrator sites depend on is actually live and not merely planned. The test asserts this shape and fails on a missing repo, a missing field, a SHA that is not 40 hex chars, or an absent/empty remediation_confirmed. It does NOT re-run the scan and makes no subprocess or network call.
kind: test
check: test_consumer_audit_artifact_is_complete
```

why: the audit's teeth are the precondition fence, not this test — this pins the artifact's SHAPE so an audit recorded as one hand-waved prose sentence fails, and the per-repo commit SHA makes the claim re-checkable by anyone with the three repos on disk (which this hermetic suite, by design, is not); the remediation_confirmed field extends that same reasoning one step, because an audit that measures a blast radius but leaves the fix to a remembered prose bullet has proved the danger without proving the safety.

### Examples of done

**Given** a fresh shell with `OBSIDIAN_VAULT_PATH` unset, **when** Dave opens a python REPL and types `PersonRepository()`, **then** it raises immediately with a message telling him to pass a path or set the env var — instead of quietly handing back a repository wired to his real vault.

**Given** a `.env` that sets `OBSIDIAN_VAULT_PATH=` with nothing after the `=`, **when** any of the three consumers constructs a repository, **then** it raises the same error — rather than binding to the current working directory and creating `@Someone.md` files wherever the process happened to start.

**Given** a cron job that runs `python scripts/lint_vault.py --quarantine` and whose environment lost the env var, **when** it fires, **then** it exits non-zero having read nothing and moved nothing — rather than renaming notes in whichever vault the default guessed.

### AC refinement log — spec-writer, 2026-07-19

Two frozen criteria were edited in place. Both are **strengthenings**, recorded here so the spec-reviewer can classify the diff against the drift taxonomy (Check 12) without reconstructing intent. **Neither weakens a promise, swaps an actor, narrows scope, swaps an oracle, nor carves an exception into an original.** Note that touching a signed section invalidates `ac_hash` / `ac_hash_AC-5` / `ac_hash_AC-6` per D4b — a re-sign via `bin/review-spec-helper.py` is expected and is the cheap half of the asymmetry.

1. **AC-6 gained a required field** (`remediation_confirmed`). Directed by the architect gate's blocking-strength note: the audit's remediation had a merge gate living only as a prose bullet at `docs/wi-024-consumer-audit.md:76-77`, with nothing observing it — the WI-115 shape (a mechanically-checkable value left to remembered compliance). The frozen AC-6 already promised "the audit artifact has audit shape"; requiring the artifact to also record that the remediation *happened* extends that promise in its own direction. It makes the criterion **harder** to satisfy, never easier. The check name is unchanged and the mechanism (a shape assertion over an artifact the hermetic suite can read) is unchanged.

2. **AC-5 gained an explicit scan-scope exclusion** (`docs/**`, `state/**`). This is a clarification forced by implementability, not a narrowing of the promise. The frozen desc says "scoped to this repo's own tracked .md files"; taken literally, the scan would fail on *this very document*, on `docs/wi-024-consumer-audit.md`, and on `docs/spec-reviews/WI-024-dave-review-2026-07-19.md` — all of which quote `PersonRepository()` as the defect under discussion. The promise being kept is "no doc **advertises** no-arg construction"; a red-team transcript citing the antipattern as evidence is the opposite of advertising it. Verified against the tree: excluding `docs/**` and `state/**` leaves the check still catching the one real site, `CLAUDE.md:18`, and it remains a general pattern scan rather than a line-targeted edit list. If a reviewer judges this a scope-narrowing anyway, the escalation is cheap and I would rather be told.

### Self-review dry run

Three questions a cold-start builder would plausibly ask, and where the spec answers them:

1. *"`str(vault_path).strip()` is what the Approach says to write — why doesn't that catch `Path("")`?"* — Design opens with exactly this correction and a runnable one-liner proving `str(Path(""))` is `'.'`. The second guard clause (`Path(text) == Path(".")`) is the answer.
2. *"AC-6 wants a `remediation_confirmed` record that isn't in the audit file. Do I add it?"* — **No.** Task 7's verify step and P3 both say so explicitly: report the failure and stop; the conductor amends and commits. The builder must not assert anything about Dave's shell environment.
3. *"AC-5 says fix the docs, but my write to `CLAUDE.md` keeps disappearing."* — Write Targets explains it: the project root is outside this repo's `write_authority` (`pipeline-runners.yaml:32-38`), so `CLAUDE.md` and `README.md` are conductor preconditions, not builder work. If they are unfixed when the build runs, `test_docs_do_not_advertise_no_arg_construction` fails — again, report and stop.

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

## Architectural Review — 2026-07-19

**Recommendation: PROMOTE to architected**

Cold-start. Code claims below re-derived from the current tree, not carried from prior gates: `base.py:20-22,41-58,86-99` read in full; all four subclass `__init__`s re-grepped (`person.py:173-174`, `company.py:58-59`, `meeting.py:34-35`, `book.py:34-35`) — each forwards `vault_path` verbatim, positionally, to `super().__init__`; `lint_vault.py:1143-1176`; `migrate_person_to_discuss.py:153-179`; AC-2's pattern scan re-run over `obsidian_schemas/` (exactly one hit, `base.py:21`); repo-wide `\w+Repository\(\s*\)` scan (one live doc site, `CLAUDE.md:18`). `LESSONS.html` #5 (loud-fail) and #21 (a gate validates within its premise) consulted.

### Trigger check

Fires on: *replaces or significantly extends an existing core system* (the default binding of a library three repos install) and *cross-system integration* (breaking change with a measured blast radius in a sibling repo). Not a skip pattern — this is a semantic break, not a config tweak.

### Review

**Fit:** Harmonizes. The target shape already exists in-tree at `migrate_person_to_discuss.py:160,171-174` — env-var default of `''`, explicit guard, message naming both routes — and the exploration correctly adopts it rather than inventing one. Named boundary exceptions match the repo's convention (`writer.py:46`, `name_validation.py:134,160`, `identifier.py:67`), and subclassing `ValueError` is the right call: a consumer's existing `except ValueError` still catches, so the break degrades to a message change rather than an uncaught escape.

**Duplication:** None introduced, and the item correctly refuses to create some. The predicate lives at exactly one line (`base.py:55-56`) and all four subclasses forward through it — the "one place to change" constraint is verified, not assumed. The REMOVE-audit's decision to classify `lint_vault.py:48-51` as a *separate mechanism* (DEMOTE, "implicit vault + mutating `--fix`/`--quarantine`") rather than "the same duplication" is the architecturally correct read: `expanduser("~")` resolves against the running user, so B is already fail-closed everywhere except Dave's laptop while A is fail-open everywhere. Recording that distinction for WI-026 is right.

**Boundaries:** Clean. Ownership of "what vault am I bound to" moves from the library to the caller/environment — which is where machine-specific configuration belongs. A machine-specific absolute path baked into a shared library is the boundary violation; removing it restores the library's machine-agnosticism. The three rerouted findings (WI-020's configured-but-wrong path and bare-except, WI-026's import-time env read) keep this item at accident-of-omission and do not leak scope.

**Determinism boundary:** Correct on the code path — the guard is a mechanical property check in code, no judgment involved, and A2 (lazy raise at first I/O) was rightly rejected for splitting one predicate across three doors. One violation off the code path, in the merge gate; see Blocking-strength note below.

**Reversibility:** High. The change is a deletion plus a guard in one `__init__`; back-out is a revert. Independently, the runtime failure mode is a loud raise at construction, not silent corruption — a wrong call is visible in seconds, not discovered months later. A4 (warn instead of raise) was correctly rejected: `load()` already warns at `base.py:96-99` and that warning has never stopped anything.

**Generalization:** Right-sized. The guard is stated as a property of the *normalised* path rather than an enumeration of literal inputs — which is what makes it survive the `Path("")` door that `person.py:1150` (`CompanyRepository(self.vault_path)`, passing a `Path`) actually exercises. A3 (opt-in `use_default=True`) was correctly rejected as a second door. No hypothetical futures built.

**Cost & maintenance:** Low and decreasing. Net deletion of a constant plus ~5 lines of guard, one test file, one doc line. The maintenance burden it removes — a live-vault path that every consumer silently inherits — is larger than the one it adds.

**Build vs extend vs integrate:** Extend, correctly. No new module, no dependency, no abstraction. Alternatives A2–A5 are each ruled out on stated grounds that hold under inspection.

**Prior art (outside view):** The approach *subtracts* a default rather than building machinery around a constraint, so the blocking conditions of this dimension do not apply. For completeness: fail-fast-on-unconfigured is the standard answer across the ecosystem — Django's `ImproperlyConfigured` on unset settings, `pydantic-settings` raising `ValidationError` on missing required fields, 12-factor's config-in-environment. Nothing here diverges from how the world solves this; the current code is the divergence.

### Blocking-strength note for the spec-writer (does not block promotion — the Approach stands verbatim)

The consumer audit landed and it changes one factual premise the exploration text still carries. `docs/wi-024-consumer-audit.md` records **18 hits in orchestrator, 16 of them live code** (`src/invariants.py` ×4, `src/queue_writer.py:784`, `src/contact_normalizer.py:510`, plus 10 in `bin/`), and records that `OBSIDIAN_VAULT_PATH` was set **nowhere** at scan time. So the REMOVE-audit's line "Load-bearing? No — verified, not assumed… nothing depends on it" is true *of this tree* and false *of production*: today those 16 sites resolve through `DEFAULT_VAULT_PATH`. The Approach does not change — this is the blast radius the audit existed to measure, and it was measured — but the doc's prose should be reconciled so no downstream reader inherits "nothing depends on it" as a global claim.

The architectural gap that follows is one of **enforcement, not design**. The audit's remediation — export the var in `~/.zshenv` — is sound and correctly relocates machine config to the machine. But its merge gate ("confirm the export is live via `zsh -c 'echo $OBSIDIAN_VAULT_PATH'` before merging") exists **only as a prose bullet at `docs/wi-024-consumer-audit.md:76-77`**. Nothing observes it. The `kind: precondition` fence proves the audit *exists*; it does not prove the remediation *happened*. And the hermetic floor suite cannot notice, by construction — AC-1's `monkeypatch`-everything property is precisely what makes it blind to the ambient variable whose absence would break 16 live sites. The item's own correctness guarantee is what hides the breakage it causes.

That is the WI-115 shape recurring: a mechanically-checkable value (is the var exported?) left to remembered compliance at merge time, with no detecting check at all — weaker even than the detecting-check-after-the-fact that scar already condemned. It is also LESSONS #21 in miniature — every gate so far validated within a frame where the consumer audit was still open, so none could see this.

**Concrete resolution, and why it is spec-writer work rather than re-exploration:** AC-6 already pins the audit artifact's *shape*. Extend that shape by one required field — a `remediation_confirmed` entry carrying the literal `zsh -c 'echo $OBSIDIAN_VAULT_PATH'` command and its verbatim non-empty output — and the merge gate becomes an artifact property the existing `test_consumer_audit_artifact_is_complete` check already reaches, using the mechanism already in place. No word of the Approach changes; one AC `desc` gains a field. That is a speccing adjustment, not a redesign, which is why this is PROMOTE-with-notes and not REVISE.

### Notes (non-blocking)

- `identity-parity-replay.py:66` self-documents as `# default/env vault, read-only`. After the flip it raises like the rest — expected, but it is the one site whose comment asserts the removed behaviour, worth a line in the remediation record.
- AC-4's guard-before-`Path(args.vault)` ordering requirement is real and not tautological: `lint_vault.py:1173` constructs the `Path` before any vault guard exists today, so a `default=None` alone yields `TypeError`, not a message. Verified in the tree.
- The DEMOTE reasoning for `lint_vault.py:48` should travel with WI-026 as written — the change is about implicit-vault-plus-mutation, not about a hardcoded Dave path. Inheriting the wrong story there would misdirect that item's `--fix` safety work.

```verdict
gate: architect
verdict: PROMOTE
date: 2026-07-19
model: claude-opus-4-8
note: Approach is architecturally sound and minimal — one predicate, one place, in-tree precedent, fail-fast matches ecosystem norm; the consumer audit has landed and its 16 live orchestrator sites are a measured blast radius, but its merge gate lives only in prose, so the spec-writer must fold the remediation confirmation into AC-6's artifact shape.
```

## Data Audit — 2026-07-19

**Recommendation: PROMOTE to specced**

Cold-start. Every predicate below was re-run by me against the current tree; none is carried from a prior gate's citation.

### Trigger check

**Class 2 — rule-effect-against-existing-corpus.** The spec introduces a guard whose correctness depends on its effect against everything that exists today: a fail-open default becomes a raise, so the load-bearing premise is "nothing currently reaches that default." Class 1 also fires on the quantified corpus claims the AC set rests on (AC-2's "exactly one hit", AC-5's "one live doc site", the hermeticity claim "zero tests reference the env var"). Not Class 0 — these are existence and count claims about real code, and each one is an AC's discriminating power.

### Premises

1. `\w+Repository\(\s*\)` has exactly one live site in this repo's docs (`CLAUDE.md:18`), and none in code — AC-5's whole claim.
2. AC-2's pattern scan (`expanduser` / `Path.home()` / literal `/Users/`) has exactly one hit in `obsidian_schemas/` and one in `scripts/` — so the check discriminates rather than flagging legitimate uses.
3. `base.py:55-56` is the single predicate site; all four subclasses forward `vault_path` verbatim — AC-3's "one place, four doors."
4. `person.py:1150` passes a `Path`, making the `Path("")` door real rather than hypothetical — the premise behind AC-1's property wording.
5. No test depends on ambient `OBSIDIAN_VAULT_PATH`; no `conftest.py` exists — the hermeticity property the invariant test must preserve.
6. The consumer-audit artifact exists with the shape AC-6 pins.

### Predicate + result (run 2026-07-19)

| # | Predicate | Result |
|---|---|---|
| 1 | `grep -rnE '\w+Repository\(\s*\)'` over tree | **1 live doc site: `CLAUDE.md:18`.** Other hits are self-referential only — this doc, `docs/spec-reviews/WI-024-dave-review-2026-07-19.md`, the audit artifact's quoted output, and `state/*`. Zero in `obsidian_schemas/`, `scripts/`, `tests/`. |
| 2 | `grep -rnE 'expanduser\|Path\.home\(\)\|/Users/'` over `obsidian_schemas/` then `scripts/` | **Exactly one each: `base.py:21` and `lint_vault.py:50`.** No third match anywhere, so no false-flag surface. |
| 3 | subclass `__init__` scan | **All four forward verbatim, positionally:** `person.py:173-174`, `company.py:58-59`, `meeting.py:34-35`, `book.py:34-35` — each `super().__init__(vault_path, **kwargs)`. Base signature `Optional[str \| Path] = None` at `base.py:43`; fallback still live at `:55-56`; `Path(vault_path)` at `:58`. |
| 4 | `CompanyRepository(` call sites | **`person.py:1150`: `CompanyRepository(self.vault_path)`** — `self.vault_path` is a `Path` per `base.py:58`. Confirmed: the library passes a `Path` into its own constructor. |
| 5 | `grep -rn 'OBSIDIAN_VAULT_PATH\|DEFAULT_VAULT_PATH'` + `glob **/conftest.py` | **Zero hits under `tests/`. No `conftest.py` in the repo.** In-code hits are only `base.py:21,22,51,56`, `lint_vault.py:49`, `migrate_person_to_discuss.py:18,160-161,173`. |
| 6 | read `docs/wi-024-consumer-audit.md` | Present; three repos, each with literal command, verbatim stdout, 40-hex SHA. HAL9000 and Exocortex clean; **orchestrator 18 hits, 16 live code.** |

### Conclusion

Every premise the AC set rests on holds against the tree as it stands today. None of AC-1/2/3/4 passes on unmodified state (the fallback at `base.py:55-56` is still live, `DEFAULT_VAULT_PATH` still exists), so no criterion is satisfiable with zero implementation. The Class-2 question — what does the new rule do against the corpus that exists? — is answered rather than reasoned about: the flip breaks nothing in *this* tree (no no-arg construction anywhere in code), and breaks 16 live sites in orchestrator unless `OBSIDIAN_VAULT_PATH` is exported, which is exactly what the committed audit measured and what its remediation addresses. That is a known, sized, and routed blast radius, not an ungrounded assumption.

**Two carry-forward flags for the spec-writer — neither blocks promotion:**

- **Prose to reconcile (the architect flagged this; I confirm the data).** The REMOVE-audit's "Load-bearing? No — verified, not assumed… nothing depends on it" (line ~59) is true of this tree and false of production. Predicate 1 confirms zero in-tree dependents; predicate 6 confirms 16 live orchestrator dependents. Scope the sentence to this tree so no downstream reader inherits it as a global claim.
- **One premise is outside this cage's reach and therefore outside this audit's warrant.** The audit artifact's "`OBSIDIAN_VAULT_PATH` set nowhere — shell profile, both launchd plists, crontab checked" (lines 70-71) is an assertion about Dave's machine, not about any file in this repo. I could not run `zsh -c 'echo $OBSIDIAN_VAULT_PATH'`, read `~/.zshenv`, or list launchd jobs. I am not restating it as grounded; I am recording that it is the one load-bearing premise this gate did not verify, and that it is the exact premise the architect's AC-6 `remediation_confirmed` field exists to convert from prose into a checkable artifact property. That fold is the right mechanism — it is what makes this premise re-groundable at build-start when the audit's 2026-07-19 date is what tells you whether it has rotted.

```verdict
gate: data-premise
verdict: PROMOTE
date: 2026-07-19
model: claude-opus-4-8
note: All six empirical premises re-run against the tree and confirmed exactly as stated (1 doc site, 1+1 pattern hits, 4 subclasses forwarding, the Path-typed call at person.py:1150, zero ambient-env tests and no conftest, audit artifact well-shaped); Class-2 blast radius is measured not assumed, with the one unverifiable premise (env var unset on Dave's machine) flagged as the reason AC-6's remediation_confirmed fold matters.
```
