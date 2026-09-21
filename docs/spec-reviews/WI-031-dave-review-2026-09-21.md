schema_version: 1
wi_id: WI-031
spec_path: docs/lint-vault-wall-third-source.md
spec_stage_at_review: exploring
reviewed_at: '2026-09-21T08:03:38+01:00'
reviewer: dave
signoff:
  verdict: PROMOTE
  channel: conversational
  provenance: attested
  signoff_escalation: null
  comments: proceed
  ac_hash: 490edae35c1a
  intent_hash: ab39c2f99e93
  ac_item_hashes:
    AC-1: 7bbd9b8c2006
  frozen_acceptance_criteria: '

    ```criteria

    id: AC-1

    desc: The containment wall over tests/test_lint_vault_fix_rules.py has a FIFTH
    clause and it is total over the library route. (a) ZERO — `mutating_drive_vault_args([that
    module]).repository_constructions` is empty, where the census collects every call
    whose callee resolves by the wall''s ONE callee-name rule (bare or attribute spelling)
    to a name ending `Repository`, with any arguments, in any scope including `_temp_vault`''s
    own body. (b) REACH (WI-235) — over planted text the census records the escape
    (`vault = _temp_vault(tmp)` / `repo = PersonRepository()` / `read_vault(repo.vault_path)`
    / `apply_fixes(issues, vault)`) at its construction line with clauses (i)–(iv)
    GREEN and `live_path_names` EMPTY, records both spellings with positional and
    keyword arguments and a construction inside a planted `_temp_vault` (enclosing
    recorded as that name), and records NONE of: a bare name `repository`, a string
    Constant, a lower-case `get_repository(...)`, `RepositoryError(...)`, `PersonRepositoryFactory()`,
    a method call on a repository-shaped object, a docstring mention. (c) ONE CHECK
    — clauses (i)–(v) and every battery run inside `test_every_mutating_drive_in_this_module_is_confined_to_a_temp_vault`;
    no new `def test_`, no new derivation, and the `ast` single-home equality still
    returns `{"tests/derivations.py"}`.

    why: Dave ruled this closed on 2026-09-16 and the ruling shipped unapplied. The
    library''s environment fallback is the one omission route WI-026''s four clauses
    cannot see, because it obtains the live path without spelling it; on the machine
    where the floor is hand-run that variable is exported, so the failure mode is
    green-in-the-cage, live-vault-write-on-the-laptop. A zero over a matcher nobody
    proved reaches anything is the WI-235 shape, hence (b); and (c) is what keeps
    WI-026''s re-synced counts true.

    check: test_every_mutating_drive_in_this_module_is_confined_to_a_temp_vault

    kind: test

    ```

    '
  frozen_intent: '

    A test module that drives `lint_vault`''s mutating entry points must have no route
    to my live vault

    that the wall does not grade — including the library''s own environment fallback,
    which reaches the

    vault without ever naming it. I ruled this closed on 2026-09-16; the ruling should
    be in the code,

    not declared open in prose.

    '
  note: null
