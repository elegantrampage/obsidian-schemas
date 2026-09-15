schema_version: 1
wi_id: WI-026
spec_path: docs/lint-vault-fix-safety.md
spec_stage_at_review: exploring
reviewed_at: '2026-09-15T10:59:30+01:00'
reviewer: dave
signoff:
  verdict: PROMOTE
  channel: cli
  provenance: verified
  signoff_escalation: ESC-WI-026-exploring-awaiting-ac-signoff-b7c2f389
  comments: wi-026 acs approved.
  ac_hash: 03777fa0e132
  intent_hash: 6a7cccabd378
  ac_item_hashes:
    AC-1: 23030080e7eb
    AC-2: 1e40f7ae8765
    AC-3: 9bd601c3a0d4
    AC-4: 5cc1a0cc3737
    AC-5: 7036c93e9f21
  frozen_acceptance_criteria: '

    Draft, originated cold-start in approval-only mode, re-derived from the frozen
    `## Intent`. **NOT

    yet frozen** — they are frozen by Dave''s review and signature through the `/review-spec`
    surface

    (`bin/review-spec-helper.py review --wi-id WI-026 --project <path>`), which is
    what writes the

    `ac-signoff` fence. Every `check` is a top-level zero-argument `def test_*(` in

    `tests/test_lint_vault_fix_rules.py` that signals failure by raising, per the
    battery''s

    direct-invocation contract (`tests/support.py:1-19`), and that module calls

    `ac_interpreter.ensure_project_interpreter(__file__)` as its first statement because
    all five

    EXECUTE the library.


    AC-1 through AC-4 are hermetic by necessity (the caged builder must be able to
    discharge them);

    AC-5 is the criterion that stops the SET from being hermetic, by reading back
    the conductor''s

    live-vault measurement. The exit half of that bracket is a declared ship condition
    rather than a

    sixth criterion, for the reason A7 gives — no criteria kind exists that can carry
    a post-build act,

    and inventing one would point an automated battery at Dave''s vault.


    ```criteria

    id: AC-1

    desc: EVERY auto-fixable rule the script ships repairs to a declared oracle, and
    the rule set is DERIVED from the script''s own syntax rather than listed. Three
    legs. (a) THE DERIVATION, and it is TWO-SIDED — a new scan in `tests/derivations.py`
    (the single legal home for `ast` in this tree) returns the set of `check` string
    literals passed to a `LintIssue(...)` construction that also passes `auto_fixable=True`
    (the EMITTERS, `lint_vault.py:341,357,386,530,596`) and, separately, the set of
    string literals compared against `issue.check` inside `apply_fixes` (the BRANCHES,
    `:888,896,903,911,929`); the criterion asserts those two sets are EQUAL and NON-EMPTY,
    so an emitter advertising a repair no branch performs, and a branch no emitter
    can reach, are each RED — neither is detectable today, and the equality is the
    invariant this leg ships. (b) THE ORACLE TABLE IS TOTAL OVER THAT SET — the test
    module declares one entry per rule id and asserts its key set EQUALS the derived
    set, so a sixth rule added later fails this criterion until someone writes its
    oracle rather than joining the untested set silently. (c) EVERY RULE REPAIRS TO
    ITS DECLARED VALUE, driven through `apply_fixes` against a `materialize_vault()`
    copy of the frozen corpus with specimens planted on top, each rule''s expected
    post-fix state read from the definition stated HERE and NEVER from a second reading
    of the implementation: `field_type_mismatch` — the reparsed `auto_created` is
    the BOOL of `:891`''s own truth set, asserted on BOTH arms (`"yes"` → `True` AND
    `"no"` → `False`, the false arm being the member the corpus cannot supply and
    the one an always-True stub fails); `person_missing_name` — the written `name`
    is `fpath.stem.lstrip("@")` BYTE-FOR-BYTE and not a cleaned form, discriminated
    by a planted stem carrying the corpus''s whitespace-damage shape, a DOUBLE SPACE,
    which `clean_person_name` collapses (`name_cleaning.py:197`) and which `gate_write`
    passes untouched because it is a predicate on `name` and not a transform (`name_gate.py:366-367`)
    — and the planted stem is a NEW one (`@Tarnquil  Brenvik.md`, pool-certified tokens
    in a combination no corpus file uses) and NEVER the corpus''s own `@Dave  Marrowyn
    Fennwick.md`, which exists, carries a well-formed `name:`, and would be destroyed
    by the plant along with the evidence that this rule stays silent on a healthy
    double-spaced stem (constraint 7); `missing_body_sections` — every heading `get_expected_sections(type)`
    names is present in that order AND the content already sitting under the sections
    that already existed is still there byte-for-byte, discriminated by a planted
    note carrying some-but-not-all sections with real content under them (a build
    that writes the default body wholesale is RED, which is the WI-126 shape); `meeting_missing_from_timeline`
    — the appended entry equals `_build_timeline_entry`''s declared format (`### <%B
    %-d, %Y of the meeting''s date>` then `[[<stem>|Meeting]]`, with ` - ` and the
    first THREE topics joined by `, ` and a trailing `.` when the meeting declares
    topics and neither when it declares none), discriminated by a planted meeting
    with FOUR topics, one with none, and a person whose Timeline already holds an
    entry that must survive; `broken_wikilink` — both `[[old]]` and `[[old|alias]]`
    retarget to the resolved stem, and a link whose date matches TWO meetings is NOT
    rewritten (`:523`''s `len(candidates) == 1`), the ambiguous case being pure plant.

    why: The item''s whole remaining promise is "a fixture-vault test for every fix
    rule it ships", and both halves of that sentence are load-bearing in a way a hand-written
    list cannot deliver. A list of five ids is the WI-131 single-literal gap wearing
    a test''s clothes: the sixth rule someone adds next year joins the untested set
    and nothing goes red. Deriving the class from the script''s own syntax makes future
    members join automatically — and deriving it from BOTH sides catches a defect
    class nothing in this repo can see today, because the emitter list and the branch
    list are two hand-kept sets that agree at five members purely by luck. Leg (c)
    exists because a derived sweep proves MEMBERSHIP and never correctness (WI-286):
    a stub that reports every rule "covered" while asserting nothing about the bytes
    satisfies (a) and (b) completely. So every rule gets an oracle whose expected
    value comes from a definition this document states, and every rule gets a member
    the live corpus cannot supply — the false arm of the boolean, the name that must
    NOT be cleaned, the sections that must NOT be flattened, the fourth topic, the
    ambiguous link. Four of the five rules have ZERO subjects in the frozen corpus
    (audited above), so "plant the discriminating member" is not belt-and-braces here,
    it is the only way any of them is exercised at all.

    check: test_every_auto_fixable_rule_repairs_to_its_declared_oracle

    kind: test

    ```


    ```criteria

    id: AC-2

    desc: EVERY DETECTOR THAT CAUSES A WRITE is pinned, in both directions, against
    the frozen corpus and against planted subjects — and the pinned set is the SEVEN
    write-causing checks, not the five auto-fixable ones. THE PINNED SET, stated once:
    the five members of AC-1''s derived auto-fixable set, PLUS `garbage_candidate_person`
    (`:673-683`) and `garbage_candidate_company` (`:685-719`), which are INFO and
    NOT auto-fixable but are the sole input to `quarantine_garbage` (`:1218` → `:1112-1144`
    → `vault_io.move_note` `:1140`) and therefore the checks that RELOCATE a note.
    Three legs. (a) NO FALSE POSITIVES ON REAL-SHAPED DATA — running the full battery
    (`read_vault` → `build_indexes` → all five `check_*` functions) over a materialized
    copy of the frozen corpus with NOTHING planted, the set of `(filename, check)`
    pairs whose check is in the pinned set equals a declared table in the test module,
    and that table''s only non-empty member class today is `meeting_missing_from_timeline`,
    one issue per (meeting, attendee) pair the manifest declares — so the other SIX
    are asserted to fire ZERO times across all 53 notes, INCLUDING the three skip
    specimens and the diacritic, hyphenated, postal-address, digit-named and stem-divergent
    members. The two `garbage_candidate_*` zeroes are real rather than accidental:
    `auto_created` occurs nowhere in the corpus and both arms gate on a truthy `auto_created`
    (`:245-253`, `:691-694`). (b) EVERY MEMBER OF THE PINNED SET FIRES ON ITS OWN
    PLANTED SUBJECT — one planted specimen per member producing exactly one issue
    carrying that check id at exactly that path, including a planted `auto_created:
    true` stub person and a planted `auto_created: true` company with no website,
    no industry, no Notes, no People links, no referencing person and no timeline
    meeting; so leg (a)''s six zeroes are proved to be silence rather than blindness.
    (c) THE MOVE PREDICATE IS PINNED ARM BY ARM — `classify_person_tier` (`:233-283`)
    decides which person notes leg (b)''s quarantine arm relocates, and its definition
    is the SIX disjuncts its own docstring states (`:236-242`): auto_created false
    or missing; ≥2 meeting wikilinks in Timeline; non-empty To Discuss or Notes; ≥1
    meeting AND a non-empty `emails`; ≥1 meeting AND a non-empty `company`; ≥2 `^###
    ` headings in Timeline. The test module declares one planted specimen per disjunct
    that is `active` BY THAT DISJUNCT ALONE — every other disjunct false — plus one
    specimen satisfying none, which must be `stub`; an implementation missing any
    arm returns `stub` for that specimen and is RED, which is the mis-classification
    that MOVES a live note. The enumeration is a declared NARROWING, not a derivation
    (the disjunction is four `if` statements over six conditions and has no table
    to iterate), so it is BOUND to the stated definition by syntax ON BOTH SIDES —
    the docstring alone does not hold the property this leg needs. A scan in `tests/derivations.py`
    returns TWO numbers for `classify_person_tier`: the count of `- ` bullets in its
    own docstring Constant (SIX today, `:236-242`) and the count of `return "active"`
    sites in its body (FOUR today, `:253`, `:276`, `:279`, `:282`), and the criterion
    asserts BOTH against the numbers the test module''s arm table declares. The code-side
    count is the load-bearing half: a seventh arm added as a fifth `if …: return "active"`
    moves it whether or not the author touches the docstring, which the bullet count
    alone cannot see — the bullets stay at 6, the table stays at 6, and the untested
    arm ships. The bullet count is the other direction: a disjunct documented but
    never implemented. WHAT THIS BINDING DOES NOT CATCH, stated so the criterion promises
    only what it delivers: an arm added by widening an EXISTING `if`''s condition
    (`if meeting_count >= 2 or has_manual or fm.get("vip")`) moves neither number,
    because it adds no `return` site and no bullet. That residue is the price of a
    narrowing over a hand-written disjunction and it is bounded — six documented conditions
    across four returns — where the alternative is a derivation this shape does not
    admit. THE EQUALITY IN (a) IS OVER THE PINNED SET ONLY — the INFO/WARNING issues
    the corpus legitimately raises (`orphaned_note`, `person_no_email`, `person_not_in_company_people`,
    `parse_error` and the rest) are outside it, because pinning those would couple
    this criterion to every check in the file rather than to the seven that cause
    a write.

    why: This is the half the item has never named and the half that can lose data.
    A detector that mis-fires does not produce a wrong report, it produces a wrong
    WRITE — and the worst of those writes is not a repair, it is a MOVE. That is exactly
    why the pinned set is seven and not five: the first draft of this criterion rested
    its whole justification on `--quarantine` relocating files off the same issue
    list, and then pinned only `auto_fixable=True` pairs — which excludes both `garbage_candidate_*`
    checks and leaves `classify_person_tier`, the predicate that decides which person
    notes get relocated, ending this item exactly as untested as it started. A criterion
    frozen by signature whose stated reason for existing is a hazard it does not cover
    is worse than one that admits the gap. Widening costs almost nothing: both garbage
    ids pin at zero on the corpus today for a structural reason, so leg (a) grows
    by two rows, and leg (b) by two plants. All seven check functions have zero tests
    today; the two reached at all are reached by a gate sweep that asserts nothing
    about what they decided. Leg (a) is the only assertion in the suite that would
    notice a detector that started firing on notes it should ignore, and the frozen
    corpus is the right subject for it: 53 notes whose shapes were MEASURED from the
    live vault rather than invented, carrying exactly the accents, hyphens, address-in-a-name
    and stem/name divergences that make a naive check over-fire. Leg (b) is what stops
    (a) being satisfiable by a build in which the checks return nothing at all — an
    empty issue set passes any "these six fire zero times" assertion, and the pairing
    is what makes the zeroes mean something. Leg (c) is the same argument one level
    down: leg (b) proves the quarantine check fires on an obvious stub, which a `return
    "stub"` implementation also satisfies; only the per-arm table can tell a correct
    classifier from a wrong-but-self-consistent one, and the cost of getting it wrong
    is a real note in `_quarantine/`. Its syntax binding is two-sided for a reason
    found by attacking the criterion''s own wording: an earlier draft counted only
    the docstring''s bullets and then claimed "a seventh arm added with or without
    a docstring line is RED", which is false of that mechanism — an arm added as a
    fifth `if …: return "active"` with no bullet leaves every number in the assertion
    unchanged, and the arm with the largest blast radius in the file would ship untested
    behind a green criterion. Counting the `return "active"` sites from the same scan
    is one more line and closes exactly that hole; the widened-condition residue that
    remains is named in the desc rather than papered over, because a criterion frozen
    by signature must not promise a guarantee its mechanism lacks — that is the same
    defect as blocking 2 above, one level in from scope and down at wording.

    check: test_every_write_causing_detector_fires_exactly_on_its_declared_subjects

    kind: test

    ```


    ```criteria

    id: AC-3

    desc: A note whose bytes cannot be decoded is REPORTED, stays in the INDEX, and
    is never repaired or moved. Four legs, all driven by a planted non-UTF-8 note
    in a materialized corpus copy. (a) REPORTED — the run emits exactly one issue
    for that note, it is NOT auto-fixable, and its message carries a reason value
    that IS one of `obsidian_schemas.repositories.base.SKIP_REASONS` (specifically
    `UNREADABLE`), read from the imported constant rather than re-spelled as a literal
    in the script or in the test; and the vocabulary wall''s UNIVERSE is widened to
    reach the script WHILE ITS TWO DECLARED-HOMES SETS STAY AT TWO MEMBERS — the two-member
    equality holding WITH `scripts/` inside the universe is the assertion, and it
    is the one that actually proves the script IMPORTS the reason rather than transcribing
    it. What gets edited is NOT the derivation — `skip_reason_literal_sites` (`tests/derivations.py:1583-1606`)
    already accepts an arbitrary `files` iterable and needs no change — but the TWO
    hand-typed call sites that pin the universe as `python_files_under(PACKAGE_ROOT,
    TESTS_ROOT)`: `tests/test_fixture_vault.py:508-509` and `:1302` (whose `universe`
    local feeds the deliberate re-run at `:1315-1318`). BOTH move to `python_files_under(PACKAGE_ROOT,
    TESTS_ROOT, SCRIPTS_ROOT)`; BOTH expected sets stay EXACTLY `{"obsidian_schemas/repositories/base.py",
    "tests/test_fixture_vault.py"}` (`:510-514` and `:1315-1318`). ADDING THE SCRIPT''S
    PATH TO EITHER EXPECTED SET IS FORBIDDEN BY THIS LEG AND IS ITSELF RED, and the
    reason is the derivation''s own predicate: it reports a file IFF one of its parsed
    `ast.Constant` nodes is a `str` EQUAL to a vocabulary member, so an `import` of
    `SKIP_REASONS` and an attribute access `SKIP_REASONS.UNREADABLE` contribute no
    such Constant and a CORRECTLY-written `scripts/lint_vault.py` is ABSENT from the
    reported set — a three-member equality would be greenable only by hand-typing
    `"unreadable"` in the script, which is the exact drift the first half of this
    leg forbids, so the criterion must not be dischargeable that way. NON-VACUITY,
    because a universe widened to nothing is green for the wrong reason: the criterion
    also asserts `scripts/lint_vault.py` is IN the universe both call sites pass (`python_files_under`
    walks `rglob("*.py")` on disk, `derivations.py:183-197`; `SCRIPTS_ROOT` is `:31`).
    Extending one call site and not the other leaves a half-extended wall that reads
    green, so the criterion asserts on both. TWO FACTS THAT MAKE THE WIDENING SAFE
    TODAY, both read off this tree so the builder is not widening blind — `scripts/`
    holds no string literal equal to any `SKIP_REASONS` member (case-insensitive grep
    over `scripts/` for `unreadable`, `schema-drift`, `malformed-frontmatter`: no
    matches), so the two-member equality is green BEFORE the `read_error` path lands
    and becomes load-bearing after it; and `:1302`''s `universe` local also feeds
    the `ast` single-home wall at `:1309-1312`, where `scripts/` contains no `ast`
    use at all (grep over `scripts/`: no matches), so the same widening STRENGTHENS
    that wall — `{"tests/derivations.py"}` stays the answer with two more files in
    scope — rather than reddening it. The shared local is therefore an asset, not
    a hazard. (b) INDEXED — the note''s STEM is present in `build_indexes(...)["all_stems"]`,
    and the discriminator is a second planted note whose BODY carries `[[<that stem>]]`
    plus a planted meeting listing that person as an attendee: today both produce
    issues (`broken_wikilink`, `meeting_attendee_not_found`) and after this change
    neither does, which is the leg that separates "the skip is loud" from "the report
    stopped lying about OTHER notes" — a build that prints a warning and still drops
    the file is RED here and green on (a). (c) QUIET OTHERWISE — no other check emits
    any issue for that path. Exactly ONE of those is a real risk and the criterion
    says which, so the build adds the guard it needs and not the four it does not:
    `no_frontmatter` (`:308`) fires on `vf.is_at_prefixed and not vf.frontmatter`,
    and a `read_error` `VaultFile` carrying `{}` frontmatter with an `@`-prefixed
    stem lands on it unless `check_structural` handles the read error ABOVE it — the
    same position and shape as the existing `if vf.parse_error: … continue` at `:297-305`.
    By contrast `orphaned_note` (`:722`), `possible_duplicate` (`:734`) and every
    completeness check are already safe BY CONSTRUCTION, because each gates on `vf.entity_type`,
    which stays `""` for a note whose bytes never parsed; the criterion asserts their
    silence without the build guarding for it. (d) NEVER WRITTEN — the unreadable
    note appears in no `--fix` target and in no `--quarantine` move. It carries no
    auto-fixable issue at all, so it never enters `apply_fixes` and sits OUTSIDE AC-4''s
    per-issue partition by construction; it is accounted for by AC-4(d)''s separate
    unreadable-note count, which is the FIFTH PRINTED FIGURE on the summary line and
    not a fifth bucket — AC-4(d) is the leg that counts it, and this pointer names
    that leg rather than AC-4(c), which is the two-new-records leg and counts nothing.

    why: `except Exception: continue` at `:117-118` is the last silent swallow on
    this path, and the currency note is right that it needs closing — but the reason
    it needs closing is not tidiness. The bytes are unrecoverable; the FILENAME is
    not, and it is discarded with them, so five checks keyed on the stem index (`broken_wikilink
    :513`, `meeting_attendee_not_found :482`, `person_company_not_found :463`, `company_people_link_broken
    :497`, `orphaned_note :722`) start reporting phantom breakage about notes that
    are perfectly fine. One of those phantoms is auto-fixable: a broken wikilink with
    a unique same-date meeting candidate gets REWRITTEN, moving a live link off a
    target that exists. That is why leg (b) is the criterion''s centre of gravity
    and why the discriminating specimen is planted rather than sampled — the corpus''s
    own non-UTF-8 member (`@Isolde Varnholt.md`) is linked to by nothing, so the corpus
    alone cannot tell a build that indexes the stem from one that does not. Leg (a)
    reuses WI-020''s vocabulary rather than inventing a parallel one because `SKIP_REASONS`
    is already the answer to "what does a batch loader do with a note it cannot load",
    already exported, and already bound to its own function''s returns by two syntax
    scans; a fourth spelling of "unreadable" in this repo is the drift WI-016 Task
    11 spent three edits removing. And the SHAPE of leg (a)''s wall edit — universe
    widened, expected sets held at two — is the whole point rather than a detail,
    because the earlier draft of this leg got it backwards and would have shipped
    a criterion whose only green ran through the defect: it told the builder to grow
    both declared-homes equalities by the script''s path, which `skip_reason_literal_sites`
    can only report once the script hand-types the literal, so a builder who imported
    correctly failed a criterion Dave had signed and a builder who typed `reason =
    "unreadable"` passed every wall in the suite. That is LESSONS #46 at design time
    — a check reachable two ways, one of them the defect, is not evidence about the
    defect — and it is worse than a check that is merely weak, because it INSTRUCTS
    the regression. Holding the expected sets at two while the universe grows inverts
    it: the equality is now a statement ABOUT the script (it is scanned and it is
    not a home), it is green today for a reason this leg states rather than by accident,
    and the only edit that reddens it is the one the leg exists to catch.

    check: test_an_unreadable_note_is_reported_indexed_and_never_silently_dropped

    kind: test

    ```


    ```criteria

    id: AC-4

    desc: A `--fix` run ACCOUNTS for every auto-fixable ISSUE it was handed — the
    four per-ISSUE outcomes PARTITION, and the operator''s summary line shows all
    of them. Four legs. (a) THE PARTITION IS PER ISSUE AND OVER FOUR BUCKETS — {repaired,
    refused, errored, DECLINED}, `declined` being an issue whose repair branch was
    reached and whose own guard chose not to act. Driven over a planted vault carrying
    a subject for each: one repairable note; one note the semantic gate refuses (the
    `unknown_contact` stem shape WI-021''s own fixture uses); one note whose frontmatter
    fence does not close (a `FrontmatterParseError`, the near-miss that is NOT a gate
    refusal); one issue whose target was deleted between the walk and the pass (the
    `FileNotFoundError` guard at `:853`); and one subject per DECLINE SITE, all five
    of which are named here so the plant set is closed rather than sampled — `field_type_mismatch`
    whose `auto_created` is already a bool so `isinstance(raw, str)` is False (`:890`);
    `missing_body_sections` on a type `get_expected_sections` returns `[]` for (`:906`);
    `meeting_missing_from_timeline` driven through `apply_fixes` with `idx=None`,
    the signature''s OWN DEFAULT at `:828`, which declines every such issue at `:913`
    (315 live if any caller ever takes that default); `broken_wikilink` whose `suggested_fix`
    is not JSON (`:935-936`); and `broken_wikilink` whose `old` link text appears
    nowhere in the file, which falls through `:963-973` incrementing nothing. THE
    ASSERTION: the number of auto-fixable issues handed in EQUALS repaired + refused
    + errored + declined, the four sets are pairwise disjoint BY ISSUE IDENTITY (the
    tie-break that makes disjointness decidable is leg (b)''s, and it is stated there
    rather than left to the builder), and each is non-empty in this run. (b) THE ATTRIBUTION
    RULE, BECAUSE TWO BUCKETS ARE RAISED AT FRAME LEVEL OVER A FILE HOLDING SEVERAL
    ISSUES — an issue''s bucket is decided where the write carrying it commits, never
    by its file''s terminal state. The gate raises at `:947` before `fixed += file_fixed`
    at `:949`, so every issue on a refused file is `refused` and none is `repaired`.
    The SECOND write is not covered by that ordering: the wikilink pass at `:960-975`
    runs after the fold, so the discriminating plant is ONE file carrying both a `missing_body_sections`
    issue (repaired, committed at `:957`) and a `broken_wikilink` issue whose write
    raises — the first is `repaired`, the second is `errored`, and a build that labels
    FILES rather than issues gets this wrong by construction. THE TIE-BREAK, STATED
    SO TWO INTERNALLY-CONSISTENT BUILDS CANNOT DISAGREE: **a DECLINE is attributed
    at its BRANCH, at the moment its own guard chose not to act, and is NEVER re-labeled
    by a later frame-level outcome on the same file** — so an issue that declined
    at `:890`/`:906`/`:913`/`:935-936`/`:963-973` stays `declined` even when a sibling
    issue''s delta then makes the gate raise at `:947`, and it stays `declined` when
    the per-file handler at `:993` catches an IO failure instead. The reason is not
    convention: a declined issue contributed NOTHING to `delta`, so it is not in the
    write the gate refused and not in the write that errored, and its guard id — the
    record leg (c) requires — is the only true statement anyone can make about why
    it did not repair. Calling it `refused` would attribute it to a gate that never
    saw it and would make "refused N" un-actionable. The DISCRIMINATING PLANT is one
    file carrying BOTH: a `meeting_missing_from_timeline` issue driven with `idx=None`
    so it declines at `:913`, AND a `person_missing_name` issue whose path-derived
    name is Tier-1 dirty so `gate_write` raises at `:947` — the first issue must land
    in `declined` with its guard id and the second in `refused`, and a build whose
    attribution rule reads "every issue on a refused file is refused" is RED on this
    file rather than silently pinning a different partition than the one signed here.
    (c) THE TWO NEW RECORDS ARE TYPED LIKE THEIR SIBLING — both are closed records
    matching `NameGateRefusalRecord`''s discipline at `:805-818` and the message bound
    `errors.py` states. The error record carries the path and a BOUNDED reason (the
    exception''s class name or a `SKIP_REASONS` member), never `str(exc)` of an arbitrary
    exception and never note bytes. The declined record carries the path, the issue''s
    `check` id, and a GUARD ID drawn from a declared CLOSED SET whose members are
    exactly the five decline sites in leg (a) — so "declined 315" resolves to `meeting_missing_from_timeline
    / no-meeting-index` and is something an operator can act on. And the refusal bucket
    keeps its exact-type filter, so the corrupt-fence specimen lands in ERRORED and
    NOT in refused — the near-miss `test_lint_vault_fix_gate.py:251-274` already asserts
    where it did not go, now extended to say where it DID. (d) THE OPERATOR SEES IT,
    AND THE CRITERION READS THE PRINTED BYTES — the summary line at `:1198` carries
    all four counts plus the count of notes skipped as unreadable (AC-3), and this
    leg is discharged ONLY by CAPTURING REAL STDOUT, never by inspecting `FixOutcome`''s
    fields. THE MECHANISM, stated because the cheap read of this leg is what leaves
    the print uncovered: the check calls `run_lint(vault_path=<a materialized+planted
    copy>, do_fix=True, quiet=True)` inside `contextlib.redirect_stdout(io.StringIO())`
    — `redirect_*` and not `capsys`, because the battery''s checks are zero-argument
    functions with no pytest fixtures (`tests/support.py:1-19`), and `redirect_stderr`
    is already this neighbourhood''s idiom (`test_lint_vault_fix_gate.py:260-261`);
    stderr is captured too and kept separate, because the refusal and error prints
    go to STDERR (`:992`, `:994`) while the summary goes to STDOUT. THE ASSERTION
    IS A STRUCTURAL PARSE AND A CROSS-CHECK, not a substring match: the captured stdout
    is parsed into a mapping of five declared labels → integers, all five labels must
    be present, and the five integers must EQUAL the figures the same run computed
    — the four bucket sizes obtained by driving `apply_fixes` over an identical SECOND
    materialization of the same planted vault through the issue list `run_lint` itself
    builds (`read_vault` → `build_indexes` → the five `check_*` fns → the `auto_fixable`
    filter, exactly `:1160-1192`), plus AC-3''s unreadable count, which is the one
    from the PRE-fix `read_vault` at `:1160` and not from the post-fix re-scan at
    `:1201`, because the line reports the pass whose fixes it is announcing. TWO-SIDED,
    over a SET of at least two planted vaults with different figure vectors: each
    of `repaired`, `refused`, `declined` and `unreadable` must take at least two DIFFERENT
    values across the set and match the cross-check every time, so a hard-coded line,
    a line that prints only two of the five, and a line whose fifth figure is a constant
    are each RED. Every one of those four is producible END-TO-END through `run_lint`''s
    own issue list and the plants are named so the set is closed rather than hoped
    for: `repaired` — any `missing_body_sections` subject; `refused` — an active person
    note with an empty `name` whose stem is Tier-1 dirty, so `check_completeness:382`
    emits and `gate_write` raises; `declined` — an `@`-prefixed note whose body carries
    `[[Meeting 20260104 Nonexistent ]]` with an INNER TRAILING SPACE while exactly
    one meeting file bears date `20260104`, so `check_links:510` strips the target
    and emits a fixable repair whose `old` text (`Meeting 20260104 Nonexistent`) then
    appears nowhere in the file and falls through `:963-973` incrementing nothing;
    `unreadable` — AC-3''s planted non-UTF-8 note. WHAT THIS LEG DOES NOT REACH, stated
    so the criterion is satisfiable and honest: `errored` cannot be produced through
    `run_lint`''s own issue list at all — a corrupt-fence note emits the non-fixable
    `parse_error` issue and never enters `apply_fixes` (`:297-305`), and the `FileNotFoundError`
    guard at `:853` needs a deletion between the walk and the pass — so for `errored`
    this leg asserts only that its LABEL is present carrying an integer (0 is a legal
    value), and its VALUE is covered at the `apply_fixes` frame by legs (a)–(c).

    why: A `--fix` pass can end an issue''s life in four ways and counts one and a
    half of them. The IO/parse failures print (`:993`) and are tallied nowhere, so
    "Fixed 0 issues, refused 0" is exactly what an operator sees when every note errored
    — the summary lies by omission, in the direction that reads as success. The DECLINED
    bucket is the one this criterion originally missed and the one that matters most:
    three buckets over a four-state space is not a partition, and the state left out
    is the only one that produces no output at all. Every one of the five branches
    has a guard; an issue that hits one raises nothing, refuses nothing, repairs nothing,
    `changed` stays False and no count moves — indistinguishable in every channel
    the tool has from a clean repair. That is precisely what the Intent forbids, and
    AC-1(a)''s two-sided emitter≡branch equality does not reach it, because that catches
    a branch that does not EXIST, never a branch that exists and declined. Stating
    the partition PER ISSUE rather than per file is the second correction and it is
    not cosmetic: `FixOutcome.fixed` counts issues (the field this item renames to
    `repaired`, ruled in the `## Write Targets` handoff note precisely because that
    name''s issues-versus-files ambiguity is what produced this correction), and the
    wikilink arm increments the run counter at `:972` outside `file_fixed` entirely,
    so a file repaired only by a link rewrite has `file_fixed == 0` and any build
    computing "fixed files" from the outcome drops that file out of every bucket while
    the equality still balances. Per-issue is what the code already counts, it keeps
    the equality total, and it is the only framing under which leg (b)''s mixed file
    is expressible at all. Leg (c) exists because the cheap way to build (a) is a
    bucket of stringified exceptions, which walks note content straight into an operator-facing
    summary that gets pasted into chat — the exact channel `errors.py`''s bounded-message
    contract exists to close — and because WI-021 chose a closed record here for reasons
    that have not changed; the declined record''s guard id is bounded for the same
    reason and is what turns a number into an action. Leg (b)''s TIE-BREAK is the
    third correction and it exists because two internally-consistent builds disagreed
    on it: a decline and a gate refusal can co-occur on ONE file, the decline having
    happened inside the per-issue loop and the refusal at `:947` after it, and nothing
    in the earlier text said whether that issue keeps its `declined` label or is swept
    into `refused` by an attribution rule reading "every issue on a refused file is
    refused". Both readings satisfy pairwise disjointness, so the criterion would
    have pinned whichever the builder happened to choose — and a `check:` written
    by the same hand would agree with it either way. Attributing the decline at its
    branch is the reading the guard-id record already implies and the only one that
    is TRUE of the frame: the declined issue put nothing in `delta`, so it was never
    in the write the gate refused. Leg (d) is what makes any of it reach the human,
    and it is the leg most easily written so that it does not: a count that exists
    only in a returned tuple is not accounting, it is bookkeeping. The precedent for
    getting this exactly wrong is already in the file this item edits — `test_lint_vault_fix_gate.py:276-281`''s
    `test_the_fix_outcome_surfaces_both_counts` carries a docstring saying "the CLI
    surfaces the refusal count beside the fixed count" and then asserts `FixOutcome._fields
    == ("fixed", "refused")` and nothing else; no test anywhere under `tests/` calls
    `run_lint` or captures its stdout, so the CLI half of that sentence has never
    been checked. A leg (d) written to inspect the record rather than the printed
    bytes reproduces that gap under a signature: four green buckets, and an operator
    staring at a real `--fix` run sees a line indistinguishable from today''s. The
    Intent''s promise is "know, FROM WHAT THE TOOL TELLS THEM", and the print at `:1198`
    is the only channel that phrase has — which is why this leg captures stdout, parses
    it structurally, and binds every figure to the number the same run computed rather
    than to a sentence someone wrote.

    check: test_every_auto_fixable_issue_is_accounted_for_and_the_printed_summary_says_so

    kind: test

    ```


    ```criteria

    id: AC-5

    desc: The LIVE-VAULT BASELINE is committed, shaped, and cross-checked against
    the frozen census — the entry half of A7''s bracket, read back off the tree rather
    than trusted. Four legs, all over `docs/lint-vault-live-baseline.md` (the second
    `kind: precondition` fence in `## Write Targets`, a conductor measurement that
    must be in git HEAD before the criteria are frozen). (a) PRESENT AND SHAPED —
    the file exists and carries the five sections the fence''s `why:` names (`## 0.
    The run`, `## 1. The five auto-fixable counts`, `## 2. The five stem-keyed check
    counts`, `## 3. The undecodable scan`, `## 4. Post-build attestation`), and each
    of §0–§3 carries a `Command:` line, a fenced block holding the literal argv, a
    fenced block holding verbatim stdout, and a 40-hex tree SHA — the `docs/company-name-corpus-audit.md`
    shape, whose whole point is that any reader can re-execute the block and contradict
    it rather than take a number on trust. (b) CROSS-CHECKED AGAINST THE FROZEN CENSUS
    — §1''s five counts are compared rule by rule against `docs/vault-shape-census.md:272-281`
    under `CENSUS_DIGEST`, so the ledger cannot be rewritten by the party it audits.
    Equal is green. A divergence is RED, naming the rules and BOTH numbers, and it
    is a staleness signal rather than a defect: it means the live vault moved since
    2026-09-07 and this document''s live-count argument needs re-reading before ship.
    TWO THINGS THIS LEG NEEDS THAT DO NOT EXIST YET, declared here as decisions rather
    than left as the builder''s discoveries. FIRST, A SIXTH CENSUS READER: WI-016''s
    four typed readers are `census_class_rows` (`tests/test_fixture_vault.py:121`),
    `census_pool_rows` (`:139`), `census_meta` (`:144`) and `census_identity_residue`
    (`:380`), and every one of them parses a `census-*` FENCE — none reads the auto-fixable
    table, which is a plain markdown table at `:275-281`. So this leg ships a fifth
    reader beside them, in the same module, parsing that table''s rows into `(message
    shape, int)` pairs and raising on a non-integer count or a duplicate shape exactly
    as `census_class_rows` does; it rides the same whole-file `CENSUS_DIGEST` fixity,
    which is over the file''s bytes and is unaffected by a new reader, so this is
    an addition and not a design question. It is a WRITE TARGET in `tests/test_fixture_vault.py`,
    which constraint 8 already makes a paired target for two other reasons. SECOND,
    A DECLARED SHAPE→RULE-ID MAPPING, because that table''s key column is a MESSAGE
    SHAPE and not a rule id, so "compared rule by rule" has no join without one: `Missing
    sections: …` → `missing_body_sections` (emitter `:357-363`), `Attended [[…]] but
    it''s not in Timeline` → `meeting_missing_from_timeline` (`:596-602`), `auto_created
    is string ''…'' instead of bool` → `field_type_mismatch` (`:341-347`), `Empty
    name (suggest: ''…'')` → `person_missing_name` (`:386-392`), `[[…]] doesn''t resolve
    (fixable → [[…]])` → `broken_wikilink` (`:530-538`). Five hand-kept rows, which
    is acceptable at that size, and they are BOUND rather than merely written: the
    mapping''s VALUE set must equal AC-1(a)''s derived rule set, so a sixth auto-fixable
    rule reddens this leg until someone decides whether the census covers it. THE
    MAPPING IS KEYED ON THE MESSAGE SHAPE AND NEVER ON THE TABLE''S PARENTHETICAL
    CATEGORY, and that is a finding rather than a preference: the census annotates
    `Empty name (suggest: ''…'')` as `(structural)` while the emitter''s own category
    field is `"completeness"` (`:388`) and its check function is `check_completeness`
    — a mapping keyed on the parenthetical would mis-join that row. The census is
    digest-frozen, so the annotation is NOT to be corrected there; the counts are
    what the row carries and what this leg reads. (c) THE UNDECODABLE COUNT IS PRESENT,
    TYPED AND CLEAN — §3 carries an integer ≥ 0, and its STDOUT block contains no
    `/Users/` path and no `.md` filename, because the privacy wall reaches this artifact
    the way it reaches the census: the count is the finding, the filenames are the
    operator''s business and never the repo''s. (d) THE EXIT OBLIGATION IS COMMITTED
    AS TEXT — §4 exists and carries the verbatim command the post-build run must use
    and the literal names of the figures it must fill. Its VALUES are empty at battery
    time by construction, and the criterion asserts the section and its declared figure
    names are PRESENT, never that they are filled — the filling is the conductor''s
    `ready → done` act, not the builder''s.

    why: This is the criterion that stops the acceptance set from being 100% hermetic,
    which is what the first draft of this document shipped and what LESSONS #27 and
    the WI-064 scar say never survives contact with real data. `lint_vault.py`''s
    correctness is DEFINED by its behaviour on 4,730 live issues across a real vault,
    and the failure that matters for a linter — the false positive on the shape nobody
    drew a fixture from — lives in the tail no 53-note fixture contains; ruff and
    ESLint both pair a fixture corpus with an ecosystem run for exactly this reason
    and this design was shipping only the first half. Leg (b) is the load-bearing
    one and it is not ceremony: this document''s ENTIRE argument for covering all
    five rules rather than only the ones that fire rests on a five-row table measured
    on one day in a vault that churns, and nothing currently re-reads it. Leg (b)
    makes a drifted vault a RED with two numbers on the screen instead of a premise
    quietly rotting under a signature — the WI-042 staleness class, closed by a comparison
    rather than by remembering to look. It also names the two things it needs and
    does not have — a reader for the census''s markdown table (the four existing readers
    are all fence-parsers) and a shape→rule-id mapping, since the table is keyed on
    message shapes — because an earlier draft of this leg said "read through WI-016''s
    own census reader" and no such reader reaches that table; a criterion frozen by
    signature that names a mechanism which does not exist is a build-time discovery,
    and this one comes with a live trap worth spending three lines on: the census
    annotates the `Empty name` row `(structural)` while that emitter''s own category
    is `"completeness"`, so a mapping keyed on the parenthetical instead of the shape
    mis-joins one row in five and the count it cross-checks is the wrong rule''s.
    Leg (c) is why the artifact can exist in the repo at all. Leg (d) exists because
    an exit act that lives only in prose evaporates: committing the command and the
    figure names as bytes turns the ship step into a re-run, and its absence into
    something a reader can see. The entry measurement also settles, by execution,
    the question this document previously routed to Dave as a sign-off judgement call
    — how many of his notes are undecodable — which is AC-3''s whole subject population
    and which no human can answer from memory.

    check: test_the_live_vault_baseline_is_committed_shaped_and_agrees_with_the_census

    kind: test

    ```


    ### Examples of done


    **Given** Dave points `--fix` at the live vault and 1,136 of the auto-fixable
    issues are body-only

    repairs across hundreds of notes — **when** the run finishes — **then** the summary
    says how many it

    repaired, how many the name gate declined, how many failed, how many it looked
    at and decided not to

    touch, and how many notes it could not read at all, and the first four add up
    to exactly the issues

    it set out to fix. **And** if the number that failed is "all of them", the line
    looks nothing like

    the line a clean run prints. **And** the floor proves that by running the tool
    and reading the line

    it actually printed — not by looking at the numbers inside the code, which is
    how the existing check

    in this area got to claim the CLI shows something it has never once looked at.


    **Given** a run in which every single `meeting_missing_from_timeline` repair quietly
    did nothing

    because the caller never passed the meeting index — **when** the run finishes
    — **then** the summary

    says "declined 315" and names the reason, instead of printing "Fixed 0 issues,
    refused 0", which is

    byte-identical to what a vault with nothing to fix prints today.


    **Given** an auto-created person note with one meeting and a real email address
    — **when**

    `--quarantine` runs — **then** the note stays where it is, because that combination
    is one of the six

    things the classifier calls "active"; and the floor goes RED if a future edit
    drops that arm, because

    each arm has a planted note that is active by that arm alone. **And given** someone
    later adds a

    seventh way to be "active" and never touches the docstring — **then** the floor
    still goes RED,

    because the count of `return "active"` sites in the code moved even though the
    documentation did not.


    **Given** one note that needs two repairs — one the tool looks at and decides
    not to touch, and one

    whose name the gate refuses — **when** the run finishes — **then** the summary
    counts the first as

    declined and the second as refused, not both as refused, because the tool says
    why each individual

    issue ended where it did rather than labelling the whole file by whatever happened
    last.


    **Given** the build lands and the conductor re-runs `lint_vault --report` over
    the real vault —

    **then** the five auto-fixable counts match the baseline captured before the change,
    the stem-keyed

    check counts have moved by exactly what the newly-indexed unreadable notes explain,
    and both numbers

    are written down next to each other in a file anyone can re-derive with the command
    printed above

    them. **And** if they do not match, the item does not ship on the strength of
    53 green fixture notes.


    **Given** a note in the vault that some other tool wrote in a non-UTF-8 encoding,
    and three notes

    that link to it — **when** the linter runs — **then** it says it could not read
    that one note, and

    it does NOT report the three healthy notes as carrying broken links to a file
    that is sitting right

    there. **And** `--fix` never rewrites those three links, which is what today''s
    run does when the

    unreadable note''s date collides with another meeting''s.


    **Given** the linter now has to say the word for "I could not read this" — **when**
    the floor runs —

    **then** it passes only if the script gets that word by importing it from the
    one place the library

    declares it, and goes RED the day someone types it out by hand in the script instead.
    The check does

    that by putting the script inside the scan''s reach while the list of places allowed
    to spell the word

    stays at two — so "green" means "the script was looked at and is not one of them",
    never "nobody

    looked".


    **Given** someone adds a sixth auto-fixable rule to `lint_vault.py` next year
    and ships it with no

    test — **when** the floor runs — **then** it goes RED, naming the rule id, because
    the rule set is

    read out of the script''s own syntax rather than from a list they would have had
    to remember to

    update. **And given** they wire the emitter but forget the repair branch (or the
    reverse), the same

    check goes red for that reason instead, which nothing in the repo can see today.


    **Given** a future "helpful" edit that makes `person_missing_name` clean the name
    it derives from the

    filename — **when** the floor runs — **then** the planted double-spaced stem goes
    RED, because the

    oracle says the repair writes the stem byte-for-byte and the gate is a predicate
    rather than a

    transform.

    '
  frozen_intent: '

    `--fix` cannot produce a write the library''s own guards would refuse: it routes
    through the WI-004 primitive, refuses malformed-parse rewrites per WI-020, and
    carries a fixture-vault test for every fix rule it ships.


    *Sharpened at exploring, 2026-09-10 — the sentence above is the frozen anchor
    and is reproduced

    verbatim; these two are ADDED, and they narrow the outcome to what is still missing
    rather than

    restating the two clauses the estate has since closed.* Two of that sentence''s
    three clauses are now

    true and walled by standing tests, so the outcome this item still owes is the
    third: an operator can

    run `--fix` over a real vault and know, from what the tool tells them, exactly
    what it repaired, what

    it declined, and what it could not read — with every repair rule proved against
    real-shaped notes

    before it touches theirs. Nothing `--fix` cannot account for may leave the run
    silently, and no note

    may disappear from the report just because its bytes would not decode.

    '
  note: null
