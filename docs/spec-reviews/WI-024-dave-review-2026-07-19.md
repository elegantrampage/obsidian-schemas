schema_version: 1
wi_id: WI-024
spec_path: docs/default-vault-path.md
spec_stage_at_review: exploring
reviewed_at: '2026-07-19T11:46:12+01:00'
reviewer: dave
signoff:
  verdict: PROMOTE
  channel: conversational
  comments: both approved
  ac_hash: 7a5468f98ac9
  intent_hash: da32901f3c7f
  ac_item_hashes:
    AC-1: b051e2f15439
    AC-2: eb365b438852
    AC-3: 7854f12b9b4d
    AC-4: f981c6f66257
    AC-5: f6ec5002fe0d
    AC-6: b1674c34084d
  frozen_acceptance_criteria: '

    Draft — originated cold-start (no Dave in the loop this session) and red-teamed
    as recorded above. **Not yet frozen:** `ac-signoff` still requires Dave''s signature
    via `bin/review-spec-helper.py originate --wi-id WI-024 --project <path>`.


    ```criteria

    id: AC-1

    desc: BaseRepository.__init__ raises VaultPathNotConfiguredError (a ValueError
    subclass) whenever the effective vault path is unconfigured — i.e. the vault_path
    argument is absent, or reduces to an empty/whitespace string REGARDLESS OF WHETHER
    IT ARRIVES AS str OR Path (base.py:43 accepts str | Path; Path("") is already
    Path(".") before __init__ sees it) — AND OBSIDIAN_VAULT_PATH is unset or blank.
    The message names both routes ("vault_path" and "OBSIDIAN_VAULT_PATH"). The guard
    is a property check on the normalised path, not an isinstance(str)-gated one.
    Test inputs must include at minimum: no arg, "", "   ", Path(""), Path("   "),
    and env set to "" or whitespace. Never resolves to Path(".").

    kind: test

    check: test_unconfigured_vault_path_raises

    ```


    why: this is the item — omission (and its blank twin, in either accepted type)
    must be unable to bind a write-capable repository to anything at all, least of
    all cwd or the live vault; the enumerated-literals wording this replaces was satisfiable
    by an `isinstance(vault_path, str)` guard that let `PersonRepository(Path(""))`
    through the door it had just shut.


    ```criteria

    id: AC-2

    desc: No caller-independent filesystem path survives as a default in obsidian_schemas/
    or scripts/ — no os.path.expanduser, Path.home(), or literal "/Users/" resolved
    into a default vault binding outside docstrings. DEFAULT_VAULT_PATH no longer
    exists.

    kind: test

    check: test_no_implicit_vault_path_defaults

    ```


    why: the property is "the vault is always supplied by the caller or the environment",
    not "one particular string is absent" — the `~` form at lint_vault.py:50 passes
    a literal-string grep today and would pass it again if reintroduced.


    ```criteria

    id: AC-3

    desc: All four repositories (Person, Company, Meeting, Book) raise VaultPathNotConfiguredError,
    with no env var set, for EACH unconfigured argument shape AC-1 defines — no arg,
    "", "   ", Path(""), Path("   ") — not the no-arg case alone. The raise happens
    at construction, before any glob or read of the filesystem.

    kind: test

    check: test_all_repositories_raise_when_unconfigured

    ```


    why: the predicate lives once in the shared base but the blast radius is per-subclass,
    so the pin must prove it through every door a consumer actually calls — and per-subclass
    matters most for the Path-typed shape, since the tree''s own repository-to-repository
    call (person.py:1150 → CompanyRepository) passes a Path, so a str-only guard would
    fail exactly where the library calls itself; "at construction" is what makes the
    stack trace point at the bug rather than at a later resolve() that returned None.


    ```criteria

    id: AC-4

    desc: scripts/lint_vault.py run with neither --vault nor OBSIDIAN_VAULT_PATH exits
    non-zero with a message naming both routes, and the guard executes BEFORE Path(args.vault)
    at line 1173 (no TypeError crash path). Mirrors the existing scripts/migrate_person_to_discuss.py:171-174
    shape.

    kind: test

    check: test_lint_vault_requires_explicit_vault

    ```


    why: this is the higher-blast-radius door — `--fix` rewrites bodies and `--quarantine`
    renames live notes — so an implicitly chosen vault here mutates real data, and
    a crash instead of a message would leave the operator guessing which route to
    use.


    ```criteria

    id: AC-5

    desc: No in-repo documentation advertises no-arg repository construction. Implemented
    as a general pattern scan over this repo''s tracked .md files (AC-2''s model),
    NOT a literal check against named lines. The one live site at time of writing
    is CLAUDE.md:18 (`repo = PersonRepository()`); a repo-wide grep for `\w+Repository\(\s*\)`
    returns that single hit — README.md:228 already passes an explicit path and README.md:408-409
    already shows the env-var route, so neither needs changing. README.md:227''s comment
    ("or uses OBSIDIAN_VAULT_PATH env var") should read as required-one-of-two rather
    than optional. Scoped to this repo''s own tracked .md files; says nothing about
    the consumer repos (see AC-6).

    kind: test

    check: test_docs_do_not_advertise_no_arg_construction

    ```


    why: the Quick Start is the most-copied line in the repo — leaving `PersonRepository()`
    in it after the break turns a clear error into a documentation bug; and this check
    can only read files inside this repo, so that is all it is permitted to claim.


    ```criteria

    id: AC-6

    desc: docs/wi-024-consumer-audit.md exists and carries, for EACH of HAL9000, Exocortex,
    and orchestrator, three fields — the literal scan command run, that command''s
    verbatim stdout (empty output recorded as an explicit "no matches" marker, not
    an absent field), and the 40-char git HEAD SHA of the repo as scanned. The test
    asserts this shape per repo and fails on a missing repo, a missing field, or a
    SHA that is not 40 hex chars. It does NOT re-run the scan.

    kind: test

    check: test_consumer_audit_artifact_is_complete

    ```


    why: the audit''s teeth are the precondition fence, not this test — this pins
    the artifact''s SHAPE so an audit recorded as one hand-waved prose sentence fails,
    and the per-repo commit SHA makes the claim re-checkable by anyone with the three
    repos on disk (which this hermetic suite, by design, is not).


    ### Examples of done


    **Given** a fresh shell with `OBSIDIAN_VAULT_PATH` unset, **when** Dave opens
    a python REPL and types `PersonRepository()`, **then** it raises immediately with
    a message telling him to pass a path or set the env var — instead of quietly handing
    back a repository wired to his real vault.


    **Given** a `.env` that sets `OBSIDIAN_VAULT_PATH=` with nothing after the `=`,
    **when** any of the three consumers constructs a repository, **then** it raises
    the same error — rather than binding to the current working directory and creating
    `@Someone.md` files wherever the process happened to start.


    **Given** a cron job that runs `python scripts/lint_vault.py --quarantine` and
    whose environment lost the env var, **when** it fires, **then** it exits non-zero
    having read nothing and moved nothing — rather than renaming notes in whichever
    vault the default guessed.

    '
  frozen_intent: '

    It is impossible to touch the live vault — or the current working directory —
    by accident of omission. A repository constructed without an explicit path, and
    a vault-touching script run without one, loud-fail immediately and say which of
    the two configuration routes to use. Configuration becomes a thing you did, not
    a thing that happened to you.

    '
  note: null
