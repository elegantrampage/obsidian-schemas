schema_version: 1
wi_id: WI-022
spec_path: docs/company-stub-parity.md
spec_stage_at_review: exploring
reviewed_at: '2026-09-06T11:56:11+01:00'
reviewer: dave
signoff:
  verdict: PROMOTE
  channel: cli
  provenance: verified
  signoff_escalation: ESC-WI-022-exploring-awaiting-ac-signoff-340c47f6
  comments: wi-022 AC's approved
  ac_hash: 71cab2dae680
  intent_hash: 41902fee91dd
  ac_item_hashes:
    AC-1: bc52957360c0
    AC-2: 2366298b900d
    AC-3: 95cb66f659d1
    AC-4: f96c089a5d0d
    AC-5: 6e2b4d29c531
  frozen_acceptance_criteria: '

    Draft — originated cold-start, approval-only mode, re-derived from the frozen
    `## Intent`. **Not yet

    frozen:** the `ac-signoff` fence is written by `bin/review-spec-helper.py` only
    after Dave''s review,

    never by hand. Every `check` is a top-level zero-argument `def test_*(` that signals
    failure by

    raising.


    *Revised 2026-09-06 (r1), AC-2 only, answering the ac-red-team findings below.*
    Both landed on the

    exclusion clause and both were confirmed against source before revising: `name_validation.py:264`
    is

    `branch_id="pure_digit"` / `pattern="pure_digit_name"`, and `:194-228` gives `arrow_connective`,

    `calendar_prefix` and `me_to_prefix` one shared `pattern="calendar_prefix"`. The
    clause now (a) names

    `.branch_id` as the keying field explicitly and cites the two divergences, (b)
    uses the real id

    `pure_digit`, (c) spells both sets literally instead of pointing at prose, and
    (d) adds a positive

    guard asserting `arrow_connective` is a company-table member carrying `.pattern
    == "calendar_prefix"`,

    so the `.pattern`-keyed reading is not merely unintended but contradicted by the
    AC''s own text. The

    same branch_id-granularity fix was pushed UPSTREAM into `## Approach` and D2,
    so the ambiguity is gone

    at its source rather than patched only where the red-team found it. AC-1, AC-3,
    AC-4 and AC-5 were

    unchanged at r1.


    *Revised 2026-09-06 (r2), AC-3 only, answering the re-verify round''s Finding
    3.* The finding is

    CONFIRMED by hand-executing the cited line rather than reading it: `person.py:1387`
    is

    `if not created_by or not isinstance(created_by, str):`, and for `"   "` both
    conjuncts are `False`, so

    Person stores three spaces verbatim — "on Person''s exact terms" was false at
    exactly the input AC-3''s

    own fixture list requires. Taking the finding''s remedy (b): `"   "` STAYS in
    the fixture list, and AC-3

    now states outright that Company''s guard is Person''s two-part check PLUS a `.strip()`-emptiness
    disjunct

    Person''s code lacks, that the widening is deliberate, and that a verbatim transcription
    of

    `person.py:1387-1393` is therefore RED on this AC by design. Remedy (a) — dropping
    `"   "` — was

    rejected: a whitespace-only label is the shape that defeats the `"unknown"` +
    WARNING sentinel most

    quietly (it looks like a value and names nobody), so the item would ship provenance
    with a hole in it to

    preserve a parity that is itself the defect. The fix was pushed UPSTREAM the same
    way r1''s was: `##

    Approach` no longer says "Person''s exact terms", P2 records the measured hole
    beside its citation, and

    new **D6** parks the Person-side repair as out-of-Intent. AC-3 also gains an explicit
    byte-identical

    clause for non-empty labels, so the `.strip()` cannot be read as licence to trim
    what is stored. AC-1,

    AC-2, AC-4 and AC-5 are unchanged at r2.


    ```criteria

    id: AC-1

    desc: The character-class mangler is gone from the package — `re.sub(r''[^\w\s-]'',
    '''', …)` and any equivalent character-class strip appears at zero live code sites
    in obsidian_schemas/ and scripts/ (asserted as a pattern scan over the tracked
    source, not a check against company.py:171 by line) — and every name in a declared
    PRESERVATION table survives a company write BYTE-IDENTICAL on both legs: the stored
    `name:` read back off disk equals the input byte-for-byte, AND the note''s filename
    stem equals `@{input}.md`. The table is a module-level object the build declares,
    and it contains at minimum one name per character class the mangler destroyed:
    apostrophe ("O''Reilly Media"), ampersand ("AT&T"), exclamation ("Yahoo!"), dot
    ("Booking.com"), comma+dot ("Alphabet, Inc."), plus a lowercase-styled brand ("wetransfer.com")
    and a Tier-2-dirty name ("Acme  Corp", double space) whose repaired form must
    appear in BOTH legs consistently — a build that repairs the name but not the filename
    is RED on the second leg. The sweep runs over the arm set `tests/derivations.py:frontmatter_write_arms`
    derives (never a hand-list), so a future arm joins it automatically.

    why: This is the item, and the two legs are what make it unfakeable. A build that
    re-adds a narrower strip passes any refusal-only oracle while still corrupting
    "AT&T"; a build that instead reaches for `NameValidator.clean`''s RETURN value
    passes the stored-name leg and fails the filename leg, which is exactly the divergence
    WI-029 exists to repair on the person side (base.py:382 binds `@{entity.name}.md`
    from the raw name one frame above every gate call and never revisits it). "wetransfer.com"
    is planted deliberately: it is the discriminating member that separates this table
    from a blind copy of TIER1_BRANCHES, whose `rfc2822_leak` branch refuses it.

    check: test_company_name_punctuation_survives_every_write_arm

    kind: test

    ```


    ```criteria

    id: AC-2

    desc: A `COMPANY_TIER1_BRANCHES` table exists in name_validation.py, built from
    the same `Tier1Branch` record as the person table and walked by the same dispatcher,
    and the fixture space is DERIVED from it (the swept set of `.branch_id` values
    asserted EQUAL to the table''s own membership, so a hand-listed sample is RED).
    EVERY set-membership assertion in this criterion is keyed on `.branch_id` and
    NEVER on `.pattern`; the two fields diverge and `.pattern` is not unique, per
    `name_validation.py:142-144`, `:194-228` (`arrow_connective`, `calendar_prefix`
    and `me_to_prefix` all carry `pattern="calendar_prefix"`) and `:263-274` (`branch_id="pure_digit"`
    carries `pattern="pure_digit_name"`). For EVERY member: (a) a company write introducing
    that record''s `specimen` is refused with a `NameGateRefusal` — the WI-021 leaf,
    never the LoudFailError root — carrying that record''s stable `pattern` on its
    `.pattern` attribute and no note content; and (b) — the correctness oracle, not
    merely membership — that record''s declared NEGATIVE specimen, a real company
    name the branch must NOT fire on, is written successfully and byte-identically.
    The record type gains that negative-specimen field for this purpose. Three membership
    assertions, all by `.branch_id`: (i) EQUALITY — `{b.branch_id for b in COMPANY_TIER1_BRANCHES}
    == {"empty", "archive_prefix", "arrow_connective", "email_chars", "path_hostile"}`,
    the set `## Approach` states and the audit artifact confirms, which by itself
    turns any of the five excluded ids into RED; (ii) NON-CONVERGENCE in the other
    direction — each of `{"rfc2822_leak", "calendar_prefix", "me_to_prefix", "unknown_contact",
    "pure_digit"}` asserted still PRESENT in `{b.branch_id for b in TIER1_BRANCHES}`,
    so a build cannot go green by subtracting those branches from the person tuple
    in place; and (iii) the SHARED-PATTERN guard — `arrow_connective` asserted a member
    of the company table AND asserted to carry `.pattern == "calendar_prefix"`, so
    excluding the `calendar_prefix` and `me_to_prefix` BRANCHES is proven not to have
    removed it.

    why: A derived sweep proves MEMBERSHIP, never correctness (WI-286): a branch implemented
    as `return True` refuses every specimen and passes leg (a) for all of them, which
    is why every member owes a negative specimen it must decline to fire on. The membership
    equality — in both directions — is the whole of "company-appropriate, not a blind
    copy": D2 measured that `rfc2822_leak` refuses "wetransfer.com", so a build that
    reuses the person table wholesale must be RED here rather than merely under-tested,
    and a build that omits the widened path-hostile set must be RED too, since that
    set is what the mangler has been silently absorbing. The keying field is named
    once and the ids are spelled literally because `branch_id` and `pattern` are different
    keys carrying overlapping tokens, and BOTH ways of confusing them fail silently.
    Keyed on `.branch_id`, the token `pure_digit_name` matches no record in either
    table, so an exclusion check written with it passes unconditionally — green whether
    or not the pure-digit branch was actually excluded, and if it was not, every all-digit
    company name (a numeric brand, a ticker-styled stub seeded from an employer field)
    is refused with no test noticing. Keyed on `.pattern`, excluding `calendar_prefix`
    is FALSE against the very table the Approach specifies, because the INCLUDED `arrow_connective`
    raises exactly that pattern — so a correct build goes RED and the only route to
    green is dropping the one connective branch that is genuinely company-appropriate,
    reopening the D2 gap. Assertion (iii) exists to make that second reading impossible
    to hold: it states the shared pattern as a POSITIVE required fact rather than
    leaving it as an absence a builder must infer.

    check: test_company_tier1_table_is_swept_and_each_branch_has_an_oracle

    kind: test

    ```


    ```criteria

    id: AC-3

    desc: `CompanyRepository.create_stub` ALWAYS writes a `created_by` frontmatter
    field. A non-empty `str` label is stored BYTE-IDENTICALLY — the value read back
    off disk equals the label passed, with no trimming, so `"  ingester  "` round-trips
    with its spaces intact. For each of the UNLABELLED shapes — `None`, `""`, `"   "`,
    `0`, `123` — the stored value is the literal `"unknown"` AND a WARNING naming
    the company is emitted. This guard is Person''s (`person.py:1387-1393`) PLUS one
    disjunct Person''s own code lacks, and the widening is DELIBERATE, not an oversight
    to be reconciled: `person.py:1387` is `if not created_by or not isinstance(created_by,
    str):`, and for `"   "` neither conjunct fires — a non-empty string is truthy,
    and it IS a `str` — so Person stores a whitespace-only label verbatim (hand-executed
    against the line; D6 parks the Person-side repair). Company''s guard is that two-part
    check with a third disjunct, emptiness AFTER `.strip()`. Consequently a verbatim
    transcription of `person.py:1387-1393` is RED on the `"   "` fixture BY DESIGN,
    and this criterion does NOT ask for byte-for-byte parity with those lines — where
    this desc and that citation disagree, this desc governs. The `.strip()` is a TEST
    on the guard, never a transform on the stored value: the byte-identical clause
    above still holds for every non-empty label. `auto_created` keeps its current
    behaviour (written only when the flag is set) and is asserted to be a SEPARATE
    field, so provenance and the workflow flag cannot be collapsed into one. The signature
    gains `created_by: Optional[str] = None` as a keyword with a default, so every
    existing call site keeps compiling.

    why: Provenance is half the frozen Intent, and "always written" is the part a
    build gets wrong by writing the field only when a label is supplied — which reads
    as green on any test that passes one. The `"unknown"` + WARNING sentinel is what
    makes an unlabelled writer findable later instead of invisible, and whitespace-only
    is the shape that defeats it most quietly: it looks like a value in the frontmatter
    and names nobody. Every one of the five shapes needs its own conjunct and none
    of the readings is sufficient alone — `if not created_by` alone lets `123` through,
    `isinstance` alone lets `""` through, and the two ANDed together, which is Person''s
    ACTUAL line and what the earlier "on Person''s exact terms" phrasing pointed a
    builder at, STILL let `"   "` through. That is why the third condition is spelled
    out here instead of delegated to a citation: the previous phrasing invited a faithful
    transcription that is RED on this AC''s own fixture, and the two halves were only
    satisfiable by silently diverging from the cited parity. Naming the divergence
    converts it from a trap into a decision — Company gets the guard Person''s comment
    already claims to have, and D6 carries the Person-side repair rather than this
    item widening into it. The byte-identical clause is what stops the fix over-reaching
    into a trimmer, which would corrupt a legitimate label the same way the mangler
    corrupts a name. Keeping `auto_created` separate is stated because the two fields
    look interchangeable and are not: one is written once at creation and never mutated,
    the other is a flag the enricher flips.

    check: test_company_stub_records_created_by_provenance

    kind: test

    ```


    ```criteria

    id: AC-4

    desc: The company name contract is homed in the GATE, not in `create_stub` — proven
    by three writes that never call `create_stub` at all, each refused identically
    with the same `pattern`: `CompanyRepository.save(Company(name=<dirty>))`; `write_markdown_file(path,
    extra_fields={"type": "company", "name": <dirty>})`, handing the writer a bare
    dict and no model; and `update_frontmatter_field(path, "name", <dirty>)` against
    an existing `type: company` note. On the two create-shaped arms the refusal lands
    BEFORE anything reaches disk: for a `/`-bearing name against a tmp vault, `<vault>/@<first-segment>`
    does not exist (which subsumes the lock home and any note inside it) and `<vault>/@<first-segment>.md`
    does not exist — artifacts named from values the test holds, never an ambient
    directory listing. THE DELTA RULE holds for companies exactly as for persons:
    a `type: company` note whose STORED name already matches a company Tier-1 branch
    stays writable for any write that does not RE-INTRODUCE the name (`update_fields`
    on `website`, `update_frontmatter_field` on `industry`, `roundtrip_file`), while
    a write setting `name` to that same stored value is refused.

    why: This is the criterion that makes D1 — the mint''s `create_stub`-only mechanism
    — unbuildable, and it is the specific hole `name_gate.py:6-8` records the person
    side having had. The no-stray-directory leg is a property of the FRAME rather
    than of the gate: `note_lock`''s outermost acquisition mkdirs a sentinel home
    defaulting to the note''s own parent, so a company check placed at the convergence
    point instead of above the lock refuses only AFTER `<vault>/@Acme/` and a `.lock`
    are already on disk. The delta rule rides here because without it this item BRICKS
    every company note already stored with a dirty name — remedy-is-the-disease —
    and those notes are the exact population D4 defers repairing, so they must stay
    writable in the meantime.

    check: test_company_name_contract_is_homed_in_the_gate_not_create_stub

    kind: test

    ```


    ```criteria

    id: AC-5

    desc: `docs/company-name-corpus-audit.md` exists and carries: the literal scan
    command run against the live vault with its verbatim stdout and the count of `type:
    company` notes scanned; ONE ROW PER MEMBER of `COMPANY_TIER1_BRANCHES` giving
    the number of live company names that branch would refuse and listing each such
    name (an empty result recorded as an explicit "no matches" marker, never an absent
    field); the count of company notes whose stored `name:` shows mangler damage,
    sizing the D4 follow-on; and, for EACH of HAL9000, Exocortex and orchestrator,
    the `CompanyRepository.create_stub` call-site scan command, its verbatim stdout,
    and that repo''s 40-char git HEAD SHA. The test asserts this SHAPE — failing on
    a missing branch row, a missing field, a SHA that is not 40 hex chars, or a branch
    present in the table with no row — and makes no subprocess, network or vault call.

    why: The membership of the table is an EMPIRICAL premise about a corpus, and settling
    it by reasoning about what company names look like is the WI-144 shape — a confident
    reading that the corpus falsified after the signature rather than before it. The
    teeth are the precondition fence, not this test; this pins the artifact''s shape
    so the audit cannot be discharged as one hand-waved prose sentence, and the per-branch
    row is what forces the answer to the only question that can make this item harmful:
    does a branch we are about to add refuse a company that is legitimately on disk
    today. The consumer rows are here because AC-3 changes a public signature and
    AC-2/AC-4 make a previously-permissive write path start refusing — a blast radius
    measured in three repos this suite is, by design, hermetic against.

    check: test_company_name_corpus_audit_is_complete

    kind: test

    ```


    ### Examples of done


    **Given** an ingester hands `create_stub` the name `"O''Reilly Media"` — **when**
    the stub is written —

    **then** the vault holds `@O''Reilly Media.md` with `name: O''Reilly Media`, byte-for-byte,
    and

    `created_by:` naming whoever wrote it. **And when** the same ingester hands it
    `"AT&T"` or

    `"Booking.com"`, **then** the answer is the same shape: nothing is stripped, and
    the person notes

    carrying `company: AT&T` resolve to that note instead of pointing at a stem that
    does not exist.


    **Given** a producer bypasses the repository entirely and calls

    `write_markdown_file(path, extra_fields={"type": "company", "name": "Acme/Corp"})`
    — **when** the

    write runs — **then** it refuses with a `NameGateRefusal` whose `pattern` is the
    path-hostile key, and

    afterwards the vault contains no `@Acme` directory, no lock home inside one, no
    `Corp.md` and no

    `@Acme.md`. Three different ways into the write door are three doors, and none
    of them is a way

    through.


    **Given** a company note already on disk stored with a dirty name from before
    this fix — **when**

    someone updates that note''s `website` or `industry`, or the linter round-trips
    it — **then** the write

    still commits, because the write did not re-introduce the name. **And when** someone
    writes that same

    dirty string back into `name:`, **then** that one is refused. The fix declines
    to create the problem;

    it does not brick the notes that already have it.

    '
  frozen_intent: '

    Company stubs get the same boundary discipline persons got: no lossy character-class
    stripping, a validating cleaning step, `created_by` provenance, and invariant
    tests on the punctuation cases the mangler destroyed.

    '
  note: null
