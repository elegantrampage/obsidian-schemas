schema_version: 1
wi_id: WI-016
spec_path: docs/vault-fixtures.md
doc_root: /Users/davewascha/.local/state/workshop/evidence/evidence-_1lnlmm2/tree
spec_stage_at_review: specced
reviewed_at: '2026-09-08T01:14:48+01:00'
reviewer: dave
signoff:
  verdict: PROMOTE
  channel: conversational
  provenance: attested
  signoff_escalation: null
  comments: wi-016 approved
  ac_hash: 2696ecd667a7
  intent_hash: a488ac920361
  ac_item_hashes:
    AC-1: ec400d9c340f
    AC-2: 1b36bfaf4234
    AC-3: eab359ff9e39
    AC-4: a82228579211
    AC-5: 1a884834e329
  frozen_acceptance_criteria: '

    Draft — originated cold-start, approval-only, re-derived from the frozen `## Intent`.
    **Not yet

    frozen:** the `ac-signoff` fence is written by `bin/review-spec-helper.py` only
    after Dave''s review,

    never by hand. Every `check` is a top-level zero-argument `def test_*(` that signals
    failure by

    raising, per the battery''s direct-invocation contract (`tests/support.py:1-19`).


    ```criteria

    id: AC-1

    desc: A frozen corpus exists at `tests/fixtures/vault/` holding at least 50 notes,
    and it is materialized by BYTE COPY rather than by any write door. Three legs.
    (a) FROZEN — `tests/fixture_vault.py` declares a digest constant computed over
    the corpus as `sha256` of the sorted sequence of (CORPUS-RELATIVE POSIX path,
    file bytes), each field NUL-framed, and the digest recomputed at test time EQUALS
    it, so editing, adding or deleting any fixture note without updating the constant
    is RED. THE KEY IS CORPUS-RELATIVE AND NEVER REPO-RELATIVE, AND THAT WORD IS LOAD-BEARING
    RATHER THAN PEDANTIC: the corpus is ONE FLAT DIRECTORY (`## Approach`), so a corpus-relative
    path IS the bare filename — exactly the `path.name` §5.2''s walk hashes — while
    a repo-relative key would make leg (b) UNSATISFIABLE BY CONSTRUCTION, because
    the materialized tree lives under a caller-supplied temp directory that has no
    repo-relative path at all. An earlier draft said "repo-relative" here and left
    the item buildable two ways, since §5.2''s code keys on the name; the two coincide
    once the word is corpus-relative, and fixing it while these criteria are drafts
    costs one word where fixing it after signature costs a D4b re-sign. (b) FAITHFUL
    — `materialize_vault(dest)` into a fresh empty directory reproduces the corpus
    byte-for-byte: the same relative path set and the same per-file bytes, with the
    digest over the materialized tree equal to the same constant — which is a real
    assertion only because the digest''s key is the filename and therefore travels
    with the bytes. AND THE SECOND CALL IS ASSERTED TOO, NOT ONLY THE FIRST: `materialize_vault`
    is re-invoked against that SAME `dest` after a foreign file has been placed in
    it, and the leg asserts that every corpus member is overwritten with identical
    bytes, that the digest over the corpus members is unchanged, and that the FOREIGN
    FILE SURVIVES — `materialize_vault` adds, it never empties a caller-supplied directory.
    The oracle for the second call is deliberately the corpus members and NOT `corpus_digest(dest)`
    over the whole directory, because the foreign file is a member of that tree and
    not of the corpus. Without this the idempotency and no-clean rules `## Edge Cases`
    decides are resolved in prose with nothing exercising them, and a future `shutil.rmtree(dest)`
    added "for cleanliness" would destroy a caller''s directory with every criterion
    still green. (c) THE DISCRIMINATOR — the corpus contains at least one note whose
    stored `name:` matches a live Tier-1 branch (an arrow-connective descriptor and
    a path-hostile name are both present, named in the manifest as such), and materialization
    of the WHOLE corpus succeeds with those notes present and byte-identical. A build
    that materializes via `repo.save()`, `write_markdown_file` or `create_stub` raises
    `NameGateRefusal` on exactly those members and is RED on this leg.

    why: "Frozen" without a mechanism is a wish — nothing otherwise stops a future
    test from editing a fixture to make itself pass, and the corpus then drifts silently
    for every other test that trusted it. Legs (a) and (b) are separate on purpose:
    (a) catches an edit to the checked-in bytes, (b) catches a materializer that transforms
    on the way out (normalizing line endings, re-serializing YAML, dropping a note
    it cannot parse) — a corpus whose specimens are cleaned up in transit is the Alice/Bob
    corpus wearing the real one''s name. Leg (c) is the planted discriminating member
    (WI-286): byte-copy is not a performance choice, it is the ONLY mechanism that
    can carry these specimens, because WI-021''s gate is a predicate on every frontmatter-writing
    arm and WI-022 extends it to companies — the gate exists precisely to make these
    notes uncreatable through the package. Without leg (c) a builder reaches for the
    repository API (the obvious, idiomatic thing), the refused specimens get quietly
    dropped from the corpus, and the corruption corpus this item is FOR is the part
    that silently does not ship.

    check: test_fixture_vault_is_frozen_and_materialized_by_byte_copy

    kind: test

    ```


    ```criteria

    id: AC-2

    desc: Every entity type the package declares has at least one fixture note, and
    each round-trips against a DECLARED oracle. The sweep is derived from the class''s
    own declaration — the set of type strings covered by the manifest is asserted
    EQUAL to `set(TYPE_TO_MODEL)` (`models.py:309-318`, 8 members today), so a hand-listed
    sample is RED and a ninth type added later joins the sweep automatically and fails
    until it has a fixture. For EVERY member: (a) parsing its fixture note yields
    an instance of that member''s model class; (b) the parsed instance''s field values
    equal the manifest''s DECLARED expected values for that note — values hand-written
    from the model definition, never produced by running the parser and recorded (a
    manifest generated by the code under test asserts only that the parser agrees
    with itself); and (c) writing the parsed model back reproduces the note''s frontmatter
    — AND THE KIND OF EQUALITY IS NAMED RATHER THAN LEFT TO THE BUILDER: the written
    file is RE-PARSED and its frontmatter MAPPING is asserted equal to the manifest''s
    DECLARED expected values, the same oracle leg (b) uses, never byte-equal to the
    original file, because YAML key order, quoting style and list style are serializer
    choices this corpus does not exist to pin, while byte-level fixity of the checked-in
    bytes is already AC-1(a)''s digest; leg (c) is not thereby redundant with leg
    (b), because it is parse→write→parse and its job is to catch a field the WRITE
    path drops or mangles. THE ROUND-TRIP SUBJECT AND ITS DOOR ARE NAMED, NOT LEFT
    TO THE BUILDER: the manifest declares for each of the 8 types exactly ONE note
    as that type''s `roundtrip_representative`, and that note must be GATE-CLEAN —
    WHICH IS THE DOOR''S OWN PREDICATE READ FROM THE PACKAGE, NEVER A LIST OF CORRUPTION
    FORMS TRANSCRIBED HERE: for a `person` representative, NO record of `TIER1_BRANCHES`
    matches its stored name (`Tier1Branch.matches`, `name_validation.py:179-184` —
    the same test the chain applies, and the same sweep unit `tests/test_name_gate.py:212`
    already uses); for a `company` representative, no record of `COMPANY_TIER1_BRANCHES`
    matches; and for the other six types `gate_write` is a pass-through (`name_gate.py:319-344`)
    so the condition is VACUOUS and nothing is asserted. Arrow-connective descriptors,
    `Me to ` prefixes, path-hostile characters and RFC 2822 leaks are four of the
    ten branches and are useful as EXAMPLES, but the four-item list they came from
    was neither the predicate nor a complete gloss on it — it omitted `email_chars`,
    `calendar_prefix`, `archive_prefix`, `unknown_contact`, `pure_digit` and `empty`,
    so a representative tripping any of those six would be refused by the very door
    leg (c) writes it through; leg (c) writes it through `write_markdown_file` — the
    GATED door, which calls `gate_write` on the assembled payload before serializing
    (`writer.py:252-253`), as against the bare `write_frontmatter` serializer — into
    a temp directory, so leg (c) additionally proves the clean representatives are
    creatable through the real write door. WHAT THAT PROVES DIFFERS BY TYPE BY DESIGN,
    AND IS CLAIMED AT ITS REAL SIZE RATHER THAN OVERCLAIMED: `gate_write` returns
    `dict(introduced)` unchanged for every declared type that is neither person nor
    company (`name_gate.py:319-344` — the company arm calls `validate_strict` against
    `COMPANY_TIER1_BRANCHES` for its raise behaviour and discards the repaired string,
    then falls to the same return), so for `person` and `company` leg (c) proves the
    gated door accepts a clean representative, and for the other six it proves the
    pass-through is a pass-through — which is the correct claim for a package whose
    gate is deliberately typed, not a gap in the criterion. The corruption specimens
    are NEVER a `roundtrip_representative`; their expected behaviour is AC-1(c)''s
    and AC-3''s, and a build that picks one of them as its `person` representative
    discovers leg (c) refusing with `NameGateRefusal` rather than passing. Note the
    ASYMMETRY this criterion carries alone: `watch`, `explore`, `gift-idea` and `exploration`
    have no repository and therefore no filename glob, so all three legs for those
    four members are PARSER-level (`parse_markdown_file` / `write_markdown_file` against
    a path), and they are outside AC-4''s repository-level surface entirely. `exploration`
    is named explicitly as a member: today it has zero test references anywhere under
    `tests/` (P4), and this criterion is where that ends. THE NARROWING ARM, AND ITS
    POPULATION IS DERIVED RATHER THAN NAMED: the types with no body config are read
    at test time as `set(TYPE_TO_MODEL) - set(ENTITY_BODY_CONFIG)` (`models.py:309-318`,
    `body_sections.py:303-324` — `watch`, `explore` and `gift-idea` today, the config
    declaring 5 of the 8), and for exactly those members the body expectation asserted
    is `get_default_body(<type>) == ""` — the declared marker, stated as by-design
    — with no section list invented for them; for each member of the INTERSECTION
    the assertion is that config''s declared sections. Both sides are dict literals
    the package exports and this criterion already reads one of them, so a ninth type
    with no config joins the narrowing arm automatically and adding a `watch` entry
    to `ENTITY_BODY_CONFIG` moves it to the other arm without an AC edit — where the
    hand-listed three went RED against a change that was correct.

    why: A derived sweep proves MEMBERSHIP, never correctness (WI-286): a sweep that
    only asserts "a fixture exists for each type and it parses" is passed by a corpus
    of eight empty notes and by a parser that returns a default-constructed model
    for anything. Leg (b) is the oracle that separates a right answer from a wrong-but-self-consistent
    one, and it is the reason the expected values must be hand-written — the single
    most likely shortcut here is generating the manifest by parsing the corpus, which
    produces a green suite that has verified nothing at all. Deriving from `TYPE_TO_MODEL`
    rather than listing the types is what closes the class in the WI-185 sense; three
    of the eight (`watch`, `explore`, `gift-idea`) are in the same untested position
    `exploration` is, and a hand-list is exactly how they stayed there. The narrowing
    arm exists because for those three there IS no right body-section answer to assert
    — `get_default_body` returns `""` for them by construction — and inventing one
    would be a fixture asserting a fact about the corpus that the code does not hold;
    naming the marker keeps the sweep total without manufacturing an oracle. Naming
    the round-trip SUBJECT and its DOOR closes the last cell a builder could fill
    two ways: `write_markdown_file` is the gated door — it calls `gate_write` on the
    assembled payload before serializing (`writer.py:252-253`) — while `write_frontmatter`
    (`writer.py:134`) is the bare YAML serializer carrying no gate of its own, and
    the two disagree on precisely the notes this corpus exists to carry — so an unnamed
    "write it back" either quietly picks the ungated serializer, in which case leg
    (c) says nothing about the write door, or picks a corruption specimen as some
    type''s representative, in which case the criterion goes RED for a reason that
    has nothing to do with round-tripping and the build spends a round rediscovering
    the gate. Stating the parser-level asymmetry for the four repository-less types
    is the same economy: it is the difference between a spec that knows those four
    are AC-2''s alone and a build that goes looking for a `WatchRepository` that has
    never existed. THE NARROWING ARM''S POPULATION AND THE GATE-CLEAN PREDICATE ARE
    BOTH DERIVED NOW, AND THE REASON THEY WERE NOT IS THE ONE WORTH RECORDING. This
    criterion''s own POPULATION was derived from `TYPE_TO_MODEL` from round 1, which
    is exactly why the round-7 sweep — the pass that applied "derive, never transcribe"
    to every criterion at once — marked AC-2 done and moved on: it swept one enumeration
    per criterion rather than one per enumeration, and AC-2 held two more. The narrowing
    arm hand-listed `watch`, `explore`, `gift-idea` where `set(TYPE_TO_MODEL) - set(ENTITY_BODY_CONFIG)`
    computes it, and GATE-CLEAN was defined as four named corruption forms where the
    door applies all ten `TIER1_BRANCHES` for `person` and all five `COMPANY_TIER1_BRANCHES`
    for `company`. NEITHER HAD A GREEN-OVER-WRONG ROUTE and that is stated rather
    than inflated: both fail LOUD, costing a build round rather than a property —
    a ninth type with no config makes the sweep raise on a missing `ENTITY_BODY_CONFIG`
    key that reads as a missing fixture, and a representative tripping one of the
    six unlisted branches is refused by `write_markdown_file` and reddens leg (c)
    for a reason that has nothing to do with round-tripping, which is the outcome
    this criterion''s own naming of the door exists to prevent, left open one clause
    later. They are fixed anyway because the fix is one line of draft text now against
    a signed criterion later, because each removes a paired edit that fires whenever
    the package gains a type, a body config or a refusal branch, and because the four-item
    gloss sat beside a rule stated correctly next to it ("the corruption specimens
    are NEVER a `roundtrip_representative`"), which is precisely the shape that goes
    stale unnoticed. AND EACH DERIVED POPULATION IS ASSERTED NON-EMPTY AND AGAINST
    ITS SIZE AT THE MOMENT OF WRITING (LESSONS #46 — a green check is evidence only
    after it has been seen red): `set(TYPE_TO_MODEL)` is asserted to hold exactly
    8 members and the narrowing arm''s difference exactly 3, because a derived sweep
    returns green when it works and green when it silently reads nothing — an import
    resolving to an empty dict, a renamed attribute — and a size assertion is the
    cheapest available form of having seen it red. The sizes are the population''s,
    never the oracle''s: what each member must PARSE TO stays hand-declared in the
    manifest.

    check: test_every_entity_type_round_trips_against_declared_values

    kind: test

    ```


    ```criteria

    id: AC-3

    desc: Every corruption shape class the census MEASURED has a specimen in the corpus,
    every specimen has a declared verdict, and every class the census RULED ABSENT
    is on the record rather than missing. The class table is read from `docs/vault-shape-census.md`
    (the precondition artifact), whose rows carry a class id, a `count`, a `status`
    of MEASURED or ABSENT, the scan command, its stdout and — for MEASURED rows only
    — a specimen. THE THREE ASSERTIONS ARE SCOPED BY STATUS, WHICH IS WHAT KEEPS THIS
    CRITERION AND `## Write Targets` FROM CONTRADICTING EACH OTHER. (i) EQUALITY,
    over MEASURED rows only: `{class id : status == MEASURED}` EQUALS the manifest''s
    covered classes, both directions — a measured class with no specimen in the corpus
    is RED, and a specimen belonging to no measured census class is RED. An ABSENT
    row is outside this equality entirely and is never RED for having no specimen.
    (ii) PER-ROW SHAPE, conditional on status: a MEASURED row must carry a count >
    0, a non-empty command, non-empty stdout and a specimen; an ABSENT row must carry
    a count of exactly 0, a non-empty command, non-empty stdout and an affirmative
    absent ruling, and must NOT carry a specimen — so a class cannot be hidden by
    leaving its status blank, and an "absent" ruling cannot be asserted without the
    scan that supports it. THE NON-EMPTY-STDOUT ASSERTION IS SATISFIABLE AT BOTH STATUSES
    ONLY BECAUSE OF A CONSTRAINT ON THE COMMAND, AND THAT CONSTRAINT IS PART OF THIS
    CRITERION RATHER THAN AN ASSUMPTION IT MAKES ABOUT THE CONDUCTOR: `## Write Targets`
    requires every recorded scan command to emit a COUNT rather than raw match lines,
    so a true zero result records verbatim as `0`. Asserted against a bare match-listing
    scan this leg would be unsatisfiable by construction on exactly the honest ABSENT
    row it exists to police — a search that finds nothing writes nothing — and the
    only routes through would be typing non-verbatim prose into the ledger or leaving
    a correctly-ruled-absent class permanently RED. (iii) THE CLASS FLOOR — DERIVED
    FOR THE HALF THAT HAS A DECLARATION, HAND-LISTED ONLY FOR THE HALF THAT DOES NOT.
    The ids below are asserted PRESENT in the table as rows of EITHER status, which
    is the machine-checked form of `## Write Targets`''s "a class measured at ZERO
    is a row the conductor writes": it is what stops a census from silently omitting
    a shape, rather than trusting prose to the conductor. **THE BRANCH HALF IS READ
    FROM THE PACKAGE AT TEST TIME AND IS NOT TRANSCRIBED INTO THIS CRITERION AT ALL**
    — the floor includes `{record.branch_id for record in TIER1_BRANCHES + COMPANY_TIER1_BRANCHES}`
    (`name_validation.py:190-309` and `:371-438`), the same runtime read of an exported
    declaration AC-2 makes against `TYPE_TO_MODEL` and AC-4 against `_skip_reason`''s
    codomain, and the same sweep unit `tests/test_name_gate.py:212` and `tests/test_company_name_contract.py:369`
    already use — so the census''s class table must carry a row for EVERY refusal
    branch this package declares, and a branch added to either table later joins the
    floor automatically instead of waiting for someone to notice. Ten ids today, and
    THE DERIVED SET IS ASSERTED NON-EMPTY AND OF EXACTLY THAT SIZE (LESSONS #46: a
    derived read returns green when it works and green when it silently reads nothing
    — an import resolving to an empty tuple, a renamed `branch_id` attribute — so
    the size at the moment of writing is the cheapest available form of having seen
    the derivation red; it is the POPULATION''s size and never an oracle, since what
    each specimen must produce stays hand-declared): `email_chars`, `rfc2822_leak`,
    `arrow_connective`, `calendar_prefix`, `me_to_prefix`, `path_hostile`, `archive_prefix`,
    `unknown_contact`, `pure_digit`, `empty`. THE FLOOR IS ASSERTED IN BOTH DIRECTIONS
    OVER BRANCH-KEYED ROWS, not only as census ⊇ derived: every census row whose id
    is branch-shaped must also be IN the derived set, so a row naming a `branch_id`
    the package no longer declares is RED rather than surviving as a phantom — assertion
    (i) supplies the reverse direction for MEASURED rows only, which leaves exactly
    the ABSENT phantom uncovered, and LESSONS #45 says a check documented as deliberately
    one-directional is an open defect rather than a note. THE COMPANY ARM IS OUT OF
    THIS CORPUS''S SCOPE, STATED AFFIRMATIVELY RATHER THAN CLAIMED AS A SIDE EFFECT:
    five ids appear in both tables (`email_chars`, `arrow_connective`, `path_hostile`,
    `archive_prefix`, `empty`) but a deduped floor writes ONE census row per `branch_id`
    and the corpus carries ONE specimen, whose DECLARED TYPE decides which table `gate_write`
    consults (`name_gate.py:329-343` vs `:361-363`) — so a person-typed `path_hostile`
    specimen exercises the person arm ONLY, and an earlier draft''s "those specimens
    exercise the company arm as well" was one word too strong. That is not a coverage
    hole and no company-typed specimen is required here: the company table already
    has its own in-tree refusal sweep over every one of its records'' `specimen` and
    `negative_specimen` (`tests/test_company_name_contract.py:359-459`), which is
    the WI-022 surface this item does not duplicate. THE CLASS TABLE''S ROW ID FOR
    A BRANCH-BACKED CLASS IS THE `branch_id` ITSELF, so those ten need no naming reconciliation
    before origination and cannot drift apart from the package. THE KEY IS `branch_id`
    AND NEVER `pattern`: `arrow_connective`, `calendar_prefix` and `me_to_prefix`
    all RAISE the shared pattern `calendar_prefix` (`:216`, `:228`, `:240`, stated
    outright in the dataclass docstring at `:152-154`), so a pattern-keyed floor would
    silently re-merge three classes this criterion treats as separate — `Dave -> Thomas
    Gatten`, `Dave - Thomas Gatten` and `Me to David Field` (`:217`, `:229`, `:241`)
    are three distinct character profiles the census must measure one at a time, and
    the census must be authored against those profiles rather than against a paraphrase
    of them. **THE HAND-LISTED HALF IS THE SIX SHAPE CLASSES THAT HAVE NO BRANCH**,
    where there is no declaration to derive from and this list is the only available
    statement of intent: diacritics, hyphenated/multi-part surnames, whitespace damage
    (double-space / leading-trailing — Tier 2, `_DOUBLE_SPACE_RE` `:445`, no Tier-1
    branch), filename-stem-does-not-equal-stored-name divergence, a same-name collision
    of at least three notes, and A POSTAL ADDRESS LEAKED INTO A NAME FIELD, which
    `### Examples of done` names by name and which no branch is (the nearest, `rfc2822_leak`,
    is an at-mangled address FUSED ONTO a name — its own specimen is `Naomi Pavie
    naomipavieatspeechmaticscom`, `:202-205` — not a postal address), so the census
    is charged in `## Write Targets` with either confirming that one present with
    a MEASURED row and a specimen or writing an ABSENT row that states affirmatively
    it does not occur in the live vault. RECONCILED 2026-09-07 against `docs/vault-shape-census.md`,
    whose six hand-listed ids are `diacritics`, `hyphenated_surname`, `whitespace_damage`,
    `stem_name_divergence`, `same_name_collision`, `postal_address_in_name` (the ONE-or-TWO
    ruling: TWO classes — collision ABSENT, divergence MEASURED). ONLY THOSE SIX are
    reconciled to the census''s own naming BEFORE origination — the artifact is a
    precondition and lands in HEAD while these criteria are still drafts (WI-300),
    so a shape class the census names differently costs one edit here rather than
    a re-sign. For each class on the floor, the manifest declares the verdict the
    specimen must produce and the test asserts it: either a refusal (`NameGateRefusal`
    — the WI-021 leaf, never the `LoudFailError` root — carrying the named `pattern`
    on its `.pattern` attribute when the specimen''s name is re-introduced through
    a write arm), or a declared cleaned form (`clean_person_name` output asserted
    equal to a hand-written string), or a declared successful byte-identical load.
    SOME BRANCHES WILL PLAUSIBLY DISCHARGE AS ABSENT, AND THAT IS THE FLOOR WORKING
    RATHER THAN AN OBLIGATION THE CORPUS CANNOT MEET: `empty` above all — `create_stub`
    guards its validator call with `if name and name.strip():`, so the branch has
    never fired in production and this item is what introduces it on the write path
    (`name_validation.py:295-299`) — and a live vault holding no empty-named note
    gets an ABSENT row with its count, command and stdout, satisfies assertion (iii),
    never enters assertion (i)''s equality, and obliges no specimen. Both discharges
    satisfy assertion (iii) and only the MEASURED one enters assertion (i)''s equality,
    so a class ruled absent is on the record and is not a failure. TWO OF THE HAND-LISTED
    SIX MAY ALSO BE ONE: the corpus is a single flat directory (see `## Approach`),
    so a same-name collision is necessarily several distinct filenames sharing one
    stored `name:` — structurally the divergence class — and the CENSUS rules whether
    the live vault separates them. If it rules them ONE class, it writes one row whose
    id the floor accepts for both members of the pair, and the manifest''s covered-class
    set FOLLOWS that ruling; assertion (i) is RED only when manifest and census disagree
    over MEASURED rows, never for the table holding fifteen class rows rather than
    sixteen. (iv) CENSUS FIXITY — THE ARTIFACT THIS CRITERION TREATS AS GROUND TRUTH
    IS FROZEN BY THE SAME MECHANISM AC-1(a) GIVES THE CORPUS, AND ITS EXPECTED VALUE
    HAS NO IN-CAGE HOME. `sha256` over the bytes of `docs/vault-shape-census.md`,
    recomputed at test time, EQUALS a 64-character lowercase hex literal — and THE
    LITERAL LIVES IN THIS CRITERION''S OWN TEXT, filled in at the same one-time pre-origination
    edit that reconciles this criterion''s six hand-listed shape classes and AC-5(b)''s
    `CONNECTIVE_SET`: the census lands in HEAD as the WI-300 precondition BEFORE Dave
    signs, so its digest is knowable exactly then, and the signature freezes it. The
    test READS that literal out of the AC-3 `criteria` fence in `docs/vault-fixtures.md`
    — a plain in-tree file read, the same hermetic move this criterion already makes
    on the census, no subprocess and no vault call — rather than comparing against
    a constant declared in `tests/fixture_vault.py`, and the reason is the whole point
    of the leg: `docs/**` is builder-writable in full (`pipeline-runners.yaml:34-38`,
    P7 — no carve-out for a landed precondition), so a constant the build owns can
    be updated in the same commit that edits the census, and the check certifies nothing.
    `fixture_vault.py` MAY restate the digest for readability, but the value ASSERTED
    AGAINST is the one in the signed criterion. The leg additionally asserts that
    exactly ONE such declaration was found WITHIN THE AC-3 `criteria` FENCE and that
    it is well-formed 64-character lowercase hex, so a reader helper that finds nothing
    is RED rather than vacuously green (LESSONS #46 again). THE UNIQUENESS IS FENCE-SCOPED
    AND NEVER FILE-WIDE, AND THAT SCOPE IS LOAD-BEARING RATHER THAN TIDY: every gate
    section in this document quotes the criterion text it reviews, so once `CENSUS_DIGEST`
    carries a real 64-hex value, ONE round-10 quotation of the filled declaration
    would turn a file-wide uniqueness assertion RED — and its only remedy would be
    editing a historical gate section, which is the one edit this document''s whole
    carry-forward convention exists to forbid. The read is therefore bounded to the
    fence the signature freezes, which is the same text the assertion is about. THE
    DECLARATION, FILLED AT THE 2026-09-07 PRE-ORIGINATION EDIT ONCE THE CENSUS WAS
    IN HEAD (`585d639`), IS `CENSUS_DIGEST = sha256:625efeee98c22ca77180b3601a8017096af8e0c30ddcc5d7db7470a4fff70bf9`;
    origination must not proceed while a placeholder stands, which is the same door
    AC-3''s class-naming and AC-5(b)''s `CONNECTIVE_SET` reconciliation already pass
    through and costs no extra interruption of Dave. The test reads both artifacts,
    asserts assertions (i)–(iv) over their parsed rows and text, and makes no subprocess,
    network or live-vault call.

    why: This criterion is what makes the corpus a corruption corpus rather than a
    tidy sample, and reading the class list FROM the census is what gives the precondition
    artifact teeth inside the suite: without it the census can be discharged as one
    hand-waved prose paragraph and the corpus quietly reverts to D2, a fixture drawn
    from the fixtures that already exist — which LESSONS #27 says is structurally
    blind to exactly the tail the corpus is for. Equality in both directions is deliberate:
    one direction stops the corpus under-covering the measured estate, the other stops
    it accumulating specimens nobody measured, which is how a corpus starts asserting
    things about a vault that no longer holds. Declaring a verdict per specimen rather
    than merely holding the bytes is the WI-286 oracle again — a corpus that only
    CONTAINS `"Dave -> Thomas Gatten (Adzact)"` proves nothing about whether anything
    refuses it, and the classes listed are precisely the forms this package has already
    been burned by, so each one having a stated expected answer is what lets the next
    name-touching change regress against them instead of rediscovering them. Naming
    the address-leaked-into-a-name-field class explicitly closes the one gap between
    this list and Dave''s own picture of done: assertion (i)''s equality is against
    whatever the census DECLARES, not against `### Examples of done`, so a census
    that recorded only the classes it happened to trip over could have dropped the
    one specimen Dave asked for by name and left every criterion green. DERIVING THE
    BRANCH HALF OF THE FLOOR RATHER THAN TRANSCRIBING IT IS THE ONE THING TO KEEP
    IF THIS CRITERION IS EVER EDITED AGAIN, AND THE HISTORY IS THE ARGUMENT. This
    floor has been hand-corrected twice and been wrong both times: round 3 added it,
    round 6 added `archive_prefix` and `unknown_contact` and asserted it then covered
    "eight of the ten live person Tier-1 branches", and a seventh read of `TIER1_BRANCHES`
    itself found the real prior count was FOUR (`rfc2822_leak`, `arrow_connective`,
    `me_to_prefix`, `path_hostile`) rising to six, with `calendar_prefix`, `email_chars`,
    `pure_digit` and `empty` all still missing. `calendar_prefix` was the expensive
    one: it is a live branch with its own id, its own specimen (`Dave - Thomas Gatten`,
    `:229`), its own recovery arm (`name_cleaning.py:46`, stripped at `:121`) and
    it is the sole source of `CONNECTIVE_SET`''s frozen `Dave` member — AC-5(b) justifies
    that member by citing exactly this branch — while this criterion''s own parenthetical
    named it as a class distinct from the arrow one in the same breath that the floor
    omitted it. Nothing in assertions (i)–(iii) reads the package''s branch table,
    so a conductor authoring the census works from this list, never thinks to measure
    `Dave -`/`Me -` prefixes as a class of their own, and every assertion stays green
    over a corpus with no specimen for four of the package''s ten refusal branches
    — which is precisely the silent omission assertion (iii) exists to make impossible,
    defeated because the floor never named the shape for the census to measure. That
    is LESSONS #45 exactly: a registry validated only against itself is a mirror,
    not a census, and the remedy is to derive the actual population from the source
    and assert set-equality with the registry. So the fix removes the hand-transcription
    rather than pruning its third instance — the branch half is now a runtime read
    of two tuples the package exports and whose `branch_id` is unique by its own docstring,
    and only the six classes with no declaration to read stay hand-listed. Keying
    on `branch_id` rather than `pattern` is load-bearing and not a detail: three branches
    deliberately raise the shared pattern `calendar_prefix`, so a pattern-keyed derivation
    would re-merge the three classes this criterion separates and reintroduce the
    same gap by another route. It stays a FLOOR rather than a promise: if the live
    vault carries no archived or scanner-artifact names, the census writes each an
    ABSENT row with its count, command and stdout, assertion (iii) is satisfied, assertion
    (i) never sees them, and nothing is RED. Scoping the three assertions BY STATUS
    is what makes that fix hold without turning honesty into a failure: the previous
    draft charged the conductor to write a zero row and then, in the same breath,
    marked a class with no specimen RED — so a correct, honest census was a false
    block and the cheapest way back to green was to delete the row, which is exactly
    the silent omission the fix was for. Splitting them gives each obligation its
    own assertion: (iii) makes the row''s PRESENCE mandatory (the machine-checked
    form of the prose charge, so no shape can vanish), (i) makes only MEASURED rows
    owe a specimen, and (ii) stops either from being discharged with a blank cell
    — a status left empty, a count with no scan behind it, an absent ruling with no
    command. The floor being reconciled before origination is the WI-300 ordering
    doing its job: the census lands in HEAD while these are still drafts, so a class
    the artifact names differently is one line edited here rather than a frozen criterion
    and a second interruption of Dave. ASSERTION (iv) EXISTS BECAUSE EVERY OTHER ASSERTION
    IN THIS CRITERION TRUSTS AN ARTIFACT NOTHING IN THIS PIPELINE FREEZES, AND THAT
    WAS THE LAST UNGUARDED ESCAPE HATCH IN THE SET. The suite is hermetic and cannot
    read the live vault, so the census is the ONLY place "this class occurs N times
    in the real vault" can be settled — and its content is entirely unprotected once
    it lands: `docs/**` is in this project''s `write_authority` in full with no carve-out
    for a landed precondition (`pipeline-runners.yaml:34-38`, P7), the build-spawn
    precheck and WI-300''s grounding-ordering backstop check only that the path is
    SOME committed blob in HEAD at one moment before the build starts and never compare
    its content afterwards, and the pipeline''s one merge-boundary integrity wall
    over docs is scoped BY DESIGN to files carrying work-item frontmatter — a shared
    non-work-item doc''s edit is declared legitimate build traffic there, which `docs/vault-shape-census.md`
    is, carrying no `id: WI-*` of its own. The concrete route it closes, and it is
    not hypothetical for either criterion that reads the artifact: a builder facing
    a MEASURED row whose character profile is awkward to author faithfully edits that
    row in place to `status: ABSENT`, `count: 0`, with a plausible command/stdout
    pair typed in, and drops the specimen — assertion (i) is scoped to MEASURED rows
    so the row exits the equality entirely, assertion (ii)''s per-row shape check
    is satisfied by construction because the builder wrote exactly the shape it demands,
    nothing re-derives the count because nothing can, and the floor whose declared
    purpose is "a class measured at zero is a row the conductor writes, not a row
    that may be omitted" is defeated by precisely the means it exists to prevent,
    every assertion green. AC-5(c) is the worse half of the same hole and is why the
    leg is asserted there too: a builder wanting a convenient `NAME_POOL` token that
    happens to collide with a real name in a vault it cannot see adds a pool-table
    row with a fabricated non-occurrence scan, and `## Intent`''s one sentence about
    Dave''s contacts'' real names has no machine check behind it at all. This criterion''s
    own AC-1(a) already states the remedy applied to the wrong artifact — "frozen
    without a mechanism is a wish" — and the fix is that identical `sha256`-over-bytes
    move, with the one difference that decides whether it works: the expected value
    lives in the SIGNED CRITERION rather than in a module the build owns, because
    a digest constant a builder can edit in the same commit as the file it digests
    is not a wall. Absent this leg the census''s trustworthiness rests on a human
    noticing an unexpected diff to a shared doc during code review — which is exactly
    the "reviewable by eye" control AC-5''s own `why:` argues is not good enough for
    this item''s privacy property. ONE RECURRING COST IS NAMED HERE RATHER THAN DISCOVERED
    BY WHOEVER PAYS IT: because the branch half of the floor is derived, a new Tier-1
    branch added to either table reddens this criterion immediately, and discharging
    it needs a census row carrying a count, a scan command and verbatim stdout — all
    of which need the live vault, which no caged builder can read — so a routine package
    change (WI-022 just added a whole company table) is blocked on a conductor pass,
    and under (iv) that pass now also re-freezes the digest. That is LESSONS #45''s
    intended friction and it is not weakened here; it is written down because round
    4 weakened AC-5(c) to a containment specifically to remove paired edits across
    the cage boundary, and the derived floor reintroduces one in the other direction,
    so the next branch author should be told rather than surprised.

    check: test_every_census_corruption_class_has_a_specimen_with_a_verdict

    kind: test

    ```


    ```criteria

    id: AC-4

    desc: Loading the materialized corpus through the repositories produces exactly
    the declared skip surface, asserted PER REPOSITORY. THE DOMAIN OF EVERY EQUALITY
    IN THIS CRITERION IS ONE REPOSITORY, NEVER A UNION ACROSS THEM — the manifest
    declares `{repository_type: {path: reason}}`, keyed by each repository''s own
    `type_name` (`repositories/base.py:191`). THE SET OF REPOSITORIES IS DERIVED,
    NOT LISTED: the sweep takes the concrete `BaseRepository` subclasses the package
    exports (`obsidian_schemas/repositories/__init__.py`''s `__all__`, `:14-21` —
    the imports end at `:12`, and an earlier draft''s `:8-20` cite spanned both and
    matched neither; excluding `BaseRepository` itself) and asserts the manifest declares
    a mapping for exactly that set, keyed by `type_name` — the same runtime read of
    an exported declaration AC-2 makes against `TYPE_TO_MODEL` and AC-3 against the
    Tier-1 tables'' `branch_id`, applied here because a hand-written "the four repositories
    are person, company, meeting, book" is the same transcription that let AC-3''s
    floor sample its own branch table, and a fifth repository added later would otherwise
    join the corpus''s blind spot silently instead of failing until it has declared
    skips and a declared loadable count. WHICH READ IS MEANT IS PINNED, BECAUSE THE
    TWO AVAILABLE ONES ARE NOT EQUIVALENT: the sweep iterates the names `obsidian_schemas/repositories/__init__.py`
    EXPORTS (`__all__`, `:14-21`) and keeps those that are concrete `BaseRepository`
    subclasses — deterministic, and a fixed list the package authors — never `BaseRepository.__subclasses__()`,
    whose answer depends on which modules happen to have been imported. THAT EXPORT
    LIST IS FILTERED, NEVER ITERATED WHOLE, because it is not homogeneous: `__all__`
    also carries `VaultPathNotConfiguredError` (`:16`), an EXCEPTION rather than a
    repository, which the concrete-`BaseRepository`-subclass filter drops — the filter
    as stated already handles it, and saying so here is what saves the build a round
    spent discovering that a six-name export list does not mean six repositories.
    And one implementability detail is settled here rather than at build time: `type_name`
    is an abstract `@property` (`base.py:189-193`), readable off an INSTANCE and not
    off the class, so each repository must be instantiated against the materialized
    vault before the manifest''s key set can be compared — which legs (a) and (c)
    do anyway, so this is ordering rather than a gap. Four today — `person`, `company`,
    `meeting`, `book` — and the derived set is asserted NON-EMPTY and of exactly that
    size (LESSONS #46, for the same reason AC-2''s and AC-3''s derivations are: a
    read that silently resolves to nothing is green, and the size at the moment of
    writing is the cheapest form of having seen it red). The other four `TYPE_TO_MODEL`
    members have no repository at all, so they are AC-2''s parser-level business alone
    — and that asymmetry FOLLOWS from the two derivations rather than being separately
    checked, which is what an earlier draft claimed. Saying it was "itself checked"
    described an assertion of the form `A - B == A - B`: with both sides derived and
    no expected value declared, it passes for any package and asserts nothing. It
    costs nothing to drop, because a fifth repository is already caught by the derived
    sweep proper — which demands a declared mapping and a declared loadable count
    for it — and keeping it would have made this criterion its own counterexample
    to the governing rule it states three sentences later. WHAT IS DERIVED IS THE
    POPULATION AND NEVER THE ORACLE, AND THE LINE MATTERS: which repositories exist
    is a fact the package declares and must be read from it, while WHAT each one is
    expected to own — the globs and the ownership outcomes spelled out below — is
    the hand-written expected value a wrong-but-self-consistent implementation must
    MISMATCH (WI-286), so reading those from the code under test would turn this criterion
    into a mirror of it. THE SKIP-REASON CODOMAIN IS MADE READABLE BY THIS ITEM AND
    IS THEN READ, BECAUSE TODAY THERE IS NOTHING TO READ AND AN EARLIER DRAFT OF THIS
    CRITERION CLAIMED OTHERWISE: `_skip_reason` (`repositories/base.py:41-47`) returns
    three BARE STRING LITERALS — `:44`, `:46`, `:47` — with a type comment on `SkippedNote.reason`
    at `:37`, and the package exports no frozenset, tuple, dict or enum of them anywhere,
    so unlike `TYPE_TO_MODEL` (a dict AC-2 reads), the `branch_id` union (two exported
    tuples AC-3 reads) and this criterion''s own repository set (`__all__`), there
    is no declaration here at all and the only thing anyone has ever been able to
    do with this codomain is hand-transcribe it, which THREE hand-typed sites do today
    (P20, corrected — the enumeration was short by two until a grep for the three
    literals over every `*.py` in this worktree was actually run, and §4''s disposition
    table now carries all of them with a ruling each): `tests/test_loud_fail_load.py:187-188`
    transcribes the WHOLE codomain, `tests/test_loud_fail_load.py:209` re-spells `unreadable`
    twenty-two lines below it inside the same function, and `tests/test_name_gate.py:152`
    re-spells `unreadable` in a module that was not previously a write target. All
    three are closed by Task 11 and `tests/test_name_gate.py` gains a `## Write Targets`
    fence for the third. Two sites are deliberately NOT closed and are kept unchanged,
    because neither is a transcription of the vocabulary: the `#` type comment on
    `SkippedNote.reason` (`base.py:37`), which documents the declaration two lines
    beneath it, and the running-prose docstring sentence at `errors.py:112`. SO THE
    FIX IS TO CREATE THE DECLARATION RATHER THAN TO KEEP TRANSCRIBING IT, AND IT IS
    ONE LINE OF PACKAGE CHANGE INSIDE THIS ITEM''S BUILD: `repositories/base.py` gains
    a module-level `SKIP_REASONS` frozenset whose members `_skip_reason` returns BY
    NAME rather than as re-spelled literals (`obsidian_schemas/**` is in this project''s
    `write_authority`, P7), and this criterion reads it at test time exactly as AC-2
    reads `TYPE_TO_MODEL`. AN EXPORT ON ITS OWN WOULD BE DECORATION — NOTHING WOULD
    MAKE A FOURTH ARM UPDATE IT — SO IT IS TIED TO THE FUNCTION BY A SYNTAX DERIVATION
    IN THE ONE PLACE THIS TREE PERMITS ONE: `tests/derivations.py`, the standing shared
    scan module and the only file under `obsidian_schemas/` or `tests/` allowed to
    name `ast` (P9), gains ONE scan returning the set of string values `_skip_reason`''s
    own body can return — every `Return` whose value is a `str` Constant, plus every
    `Return` of a module-level Name bound in that file to a `str` Constant — and the
    criterion asserts that set EQUALS `SKIP_REASONS`. THE EQUALITY DIRECTION IS WHAT
    MAKES THAT WALL HOLD RATHER THAN MERELY EXIST, and it has three consequences worth
    stating so a builder does not weaken it to a containment: an arm added to `_skip_reason`
    without a matching frozenset member is RED at that equality; an arm whose return
    the scan CANNOT resolve to a literal makes the scan silently UNDER-read, which
    the equality reports RED instead of passing green (LESSONS #46 — the failure mode
    of every derived read in this document); and `SKIP_REASONS` is additionally asserted
    NON-EMPTY and of size exactly 3 at the moment of writing, which is the POPULATION''s
    size and never an oracle, since what each specimen must produce stays hand-declared
    in the manifest. AND THE CLASS IS CLOSED WITH ONE RULE RATHER THAN THREE REPOINTED
    LINES, BECAUSE AN ENUMERATION IN PROSE GOES STALE AND A WALL DOES NOT: a SECOND
    syntax scan in `tests/derivations.py`, `skip_reason_literal_sites`, returns every
    file under `python_files_under(PACKAGE_ROOT, TESTS_ROOT)` containing a `str` Constant
    EQUAL to a member of `SKIP_REASONS`, and this criterion asserts that set EQUALS
    exactly two named homes — `obsidian_schemas/repositories/base.py`, THE DECLARATION,
    and `tests/test_fixture_vault.py`, THE SPELLING PIN — so a fifth hand-typed site
    anywhere under the package or the suite is RED with the file named and its remedy
    is one import. It reads parsed SYNTAX and never source text for a reason the two
    KEPT sites make concrete: `ast` drops `#` comments entirely, so `base.py:37`''s
    type comment is invisible to it, and a docstring is ONE Constant whose value is
    the whole docstring, so `errors.py:112`''s prose mention is not equal to any member
    — a text grep would have to carve an exception for both, and an exception is the
    escape hatch this criterion has been folded for twice. The SECOND home is not
    a weakening but the repair of one the fold would otherwise have caused, and it
    is stated so nobody removes it as untidy: `tests/test_loud_fail_load.py:187-188`
    is today the ONLY thing in the tree pinning the literal SPELLINGS, and once it
    reads `SKIP_REASONS` both sides of that comparison move together, so a rename
    of `"schema-drift"` — a value consumers read off `SkippedNote.reason` — would
    pass every check in this criterion; the spellings are therefore hand-pinned ONCE,
    as `SKIP_REASONS == {"malformed-frontmatter", "schema-drift", "unreadable"}` in
    `tests/test_fixture_vault.py`, which is the one place a rename should have to
    be a deliberate edit. Because that universe grows with every file this item adds,
    `tests/fixture_vault.py` is a member of it, which is why the manifest IMPORTS
    the three constants for `SKIPS`''s reason values rather than re-spelling them
    (§3) — and WHICH constant a filename maps to remains the hand-declared oracle,
    so nothing about leg (a)''s both-directions equality is read from the code under
    test. ON TOP OF THAT DECLARATION the criterion asserts that the corpus carries
    at least one specimen for each member and that the UNION over the four declared
    per-repository mappings'' reasons is EQUAL to `SKIP_REASONS` — so a corpus missing
    a reason is RED, and a fourth reason added to the package later genuinely does
    fail until it has a specimen, which is now a property this criterion HAS rather
    than one it merely stated. THE DOUBLE-OWNERSHIP OF THE TWO UNTYPED CLASSES IS
    DECLARED EXPECTED BEHAVIOUR, NOT A BUILD-TIME SURPRISE: ownership is decided by
    `_note_skip` on the error''s `declared_type` (`base.py:267-275`), and `FrontmatterParseError`
    carries `declared_type=None` always (`errors.py:65-67`) while a `UnicodeDecodeError`
    carries the attribute not at all, so both fall to `_owns(None)`, which returns
    `Path(self.file_pattern).stem != "*"` (`base.py:258-265`) — TRUE for person and
    company (both inherit `@*.md`, `base.py:196-198`) and for meeting (`Meeting *.md`,
    `meeting.py:51-54`), FALSE for book (`*.md`, the catch-all, `book.py:50-53`).
    Combined with the flat directory''s glob partition, the manifest therefore declares,
    and the test asserts: a malformed-frontmatter or unreadable specimen FILENAMED
    `@<name>.md` appears in BOTH person''s and company''s mappings and in NEITHER
    meeting''s (its glob does not match) nor book''s (its glob matches but its catch-all
    stem declines ownership); the same specimen filenamed `Meeting <date> - <title>.md`
    appears in meeting''s mapping ONLY; and a `schema-drift` specimen, which does
    carry a `declared_type` (`errors.py:70-71`), appears ONLY in the mapping of the
    repository whose `type_name` equals it. Three legs. (a) SKIPPED — for EACH of
    the four repositories independently, the mapping `{note.path: note.reason for
    note in repo.skipped_notes}` after loading the materialized vault EQUALS that
    repository''s declared mapping, both directions: a malformed specimen that silently
    loads anyway is RED, a well-formed note a repository wrongly skips is RED, and
    an untyped skip that moves between owners is RED in two mappings at once. (b)
    THE PLANTED DISCRIMINATORS — the corpus contains an untyped specimen under EACH
    of the two owning globs (one `@<name>.md`, one `Meeting <date> - <title>.md`),
    and book''s declared mapping over the untyped classes is asserted EMPTY: without
    the second filename a stub that records untyped skips in one repository only is
    indistinguishable from the real rule, and without book''s empty assertion the
    catch-all arm of `_owns` is never exercised by anything. (c) LOADED — `len(repo.get_all())`
    for each of the four repositories equals that repository''s declared loadable
    count, and the resolvable identities declared in the manifest all resolve, so
    a corpus whose malformed members poison the surrounding load is RED rather than
    merely under-reported.

    why: WI-020 built `SkippedNote` because an unloadable note used to vanish at DEBUG
    — invisible to the cache, so `resolve()` missed it and `find_or_create_stub` minted
    a duplicate, the dup-proliferation class WI-119/WI-125 exist to fight (`base.py:29-34`).
    That surface has never had a vault on disk containing one of each and stating
    which is which, so nothing today would notice a regression that reclassified `schema-drift`
    as `unreadable` or that swallowed a malformed note without recording it. Set equality
    in both directions is what makes leg (a) an oracle rather than a membership check:
    `skipped_count >= 3` is passed by a repository that skips everything, and `skipped_count
    == 3` is passed by one that skips the three WRONG notes. But a both-directions
    equality with an UNSTATED DOMAIN is not an oracle either, and that was this criterion''s
    real gap: a union over all repositories and a per-repository mapping are two different
    declared manifests, each passes its own reading, and only the per-repository one
    goes RED when a regression moves an untyped skip between owners — which is the
    exact regression this surface exists to catch, because ownership is what decides
    whether a bad note is VISIBLE to the repository that would otherwise mint a duplicate
    for it. Declaring the double-ownership rather than discovering it is the WI-144
    economy: a build that meets it as a surprise reads two repositories reporting
    "the same" note, concludes the test is wrong, and quietly relaxes the equality
    to a union — losing the property. Leg (b) is WI-286''s planting rule applied to
    this criterion''s own discriminant: the corpus, not the code, has to supply the
    case that tells the per-repository rule apart from every cheaper approximation
    of it, and book''s empty mapping is the only assertion in the suite that the catch-all
    glob DECLINES ownership by design. Leg (c) exists because the failure that actually
    costs data is not the skip, it is the blast radius — a parse failure that aborts
    the directory walk leaves the cache silently short, and the only way to see it
    is to declare beforehand how many notes SHOULD have loaded. DERIVING THE REPOSITORY
    SET RATHER THAN LISTING IT WAS ADDED IN THE SAME PASS THAT DERIVED AC-3''s CLASS
    FLOOR, AND FOR THE SAME REASON RATHER THAN FOR SYMMETRY: this criterion''s whole
    subject is that a note''s VISIBILITY is a per-repository fact, so the one thing
    that must not be hand-maintained is which repositories there are — a fifth one
    added to the package would inherit `_owns`, take part in the same glob partition
    over the same flat directory, and be entirely absent from a hand-listed sweep,
    which is the exact silent under-coverage AC-3''s floor was found doing over the
    branch table. It is also the cheapest possible version of the fix: the subclasses
    are already exported and `type_name` is already the key the manifest uses. The
    oracle stays hand-written on purpose and the criterion says so, because the failure
    this leg exists to catch is a regression in ownership, and an expected value read
    from the code that computes it agrees with the regression. THE SKIP-REASON CODOMAIN
    WAS THE SEVENTH INSTANCE OF THIS DOCUMENT''S ONE RECURRING DEFECT, AND IT IS THE
    FIRST THAT COULD NOT BE FIXED BY READING SOMETHING — WHICH IS WHY THE FIX CREATES
    A DECLARATION INSTEAD. Two independent round-9 reads — the architect''s and the
    AC red-team''s, from a duplication angle and from a satisfiable-with-nothing-real-behind-it
    angle — found the same fact: this criterion put `_skip_reason`''s reasons on the
    DERIVED side of the document''s residue list and stated a consequence ("a fourth
    reason added to the package later fails until it has a specimen") that only a
    derivation delivers, while the package declares no set to read. Both sides of
    the equality were hand-typed, so a builder who added a fourth arm — a `PermissionError`
    distinguished as `unreadable-permission`, say; WI-020''s own `base.py:29-34` already
    distinguishes skip incidents by cause — would ship a GREEN criterion with the
    new failure class in exactly the blind spot `SkippedNote` was built to close,
    one layer up from where WI-020 closed it. That is a green-over-wrong route rather
    than a loud one, which is what separates it from round 8''s two instances and
    makes it worth a package change. THE ALTERNATIVE WAS OFFERED AND IS REJECTED FOR
    A STATED REASON: the honest cheap move was to keep the set hand-written, delete
    the false consequence and move it into the residue list beside this criterion''s
    ownership oracle. It is rejected because the residue list''s own membership test
    is "there is no declaration to read", and the other four members earn that by
    their SUBJECT — whether a field''s value IS a name, what a shape class should
    be called, what a repository OUGHT to own — all judgment. Which strings `_skip_reason`
    can emit is not judgment, it is mechanical, and this is the determinism boundary
    the whole document is organised around: a mechanical fact carried by a transcription
    is a defect wherever it appears, and the remedy for the one classification vocabulary
    that never got the module-level-literal treatment the package gives `TYPE_TO_MODEL`,
    `TIER1_BRANCHES`, `ENTITY_BODY_CONFIG` and `_GENERIC_ORG_SUFFIXES` is to give
    it that treatment. It is solve-in-one-place besides, and the enumeration behind
    that argument is now the grep''s rather than memory''s: the three strings live
    in a return chain (`base.py:44`, `:46`, `:47`), a `#` type comment (`:37`), a
    running-prose docstring sentence (`errors.py:112`) and THREE hand-typed test sites
    — `tests/test_loud_fail_load.py:187-188` (the whole codomain), `tests/test_loud_fail_load.py:209`
    and `tests/test_name_gate.py:152` (one member each) — and the criterion would
    have added a seventh. An earlier draft of this sentence named only the first,
    the second and one of the three test sites; the short list mattered because it
    was the ARGUMENT, and because it left the builder a judgment the spec had not
    made — repointing `:187-188` puts `:209` on the same screen with nothing saying
    whether it is in scope. §4 now carries a disposition table naming every site with
    a ruling, Task 11 closes all three test sites, and the two kept sites are kept
    for a stated reason rather than by omission. AND THE EXPORT IS DELIBERATELY NOT
    TRUSTED ON ITS OWN, WHICH IS THE PART TO KEEP IF THIS CRITERION IS EDITED AGAIN.
    `TYPE_TO_MODEL` cannot silently fall out of step with the package because dispatch
    depends on it; a `SKIP_REASONS` frozenset nothing consumes CAN, and a criterion
    that read it and stopped there would have re-created the same false consequence
    in a nicer-looking form — the fold breeding its own next finding, which this document
    has recorded three times. Binding it to `_skip_reason`''s own returns by a syntax
    scan in `tests/derivations.py` is what closes that, it needs no new machinery
    (the module exists, is importable, and single-homes `ast` by a standing wall),
    and asserting EQUALITY rather than containment is what makes the scan''s own under-read
    — the LESSONS #46 failure every derived read in this document shares — report
    RED instead of green.

    check: test_the_skip_surface_over_the_corpus_equals_its_declared_reasons

    kind: test

    ```


    ```criteria

    id: AC-5

    desc: No corpus note can carry a live identifier — an email, a phone number, a
    profile URL OR A NAME — asserted structurally rather than by inspection. THE REACH
    OF EVERY LEG IS every file under `tests/fixtures/vault/` PLUS `tests/fixture_vault.py`
    itself, because the manifest restates each specimen''s field values as AC-2''s
    declared oracle and a wall that scanned only the corpus would miss a real name
    typed into the oracle. Five legs. (a) RESERVED RANGES, derived not hand-listed
    — the test scans those bytes for every email-shaped, phone-shaped and profile-URL-shaped
    token and asserts each one is inside a reserved range: emails only under RFC 2606
    / RFC 6761 reserved names (`example.com`, `example.net`, `example.org`, or a `.test`
    / `.invalid` / `.example` TLD); phones only inside reserved fictional ranges (UK
    `+44 7700 900xxx` — the Ofcom drama block, IN EITHER OF ITS TWO SPELLINGS, the
    international `447700900xxx` and the national `07700900xxx`, which are ONE range
    and not two, because `normalize_phone` strips the `+` and keeps the leading `0`;
    NANP `555-01xx`); profile URLs only under a declared placeholder form. The scan
    is over ALL bytes in reach rather than a field list, so it needs no enumeration
    to be total — but the fields that carry these shapes are named for the corpus
    author''s benefit, since every one of them must be constructed: `Person.emails`
    (`models.py:81`), `Person.phones` (`:82`), `Person.whatsapp` (`:83`, a JID whose
    digits `normalize_phone` splits at the `@` — `phone_normalization.py:39-55`),
    `Person.linkedin` (`:86`), `Person.slack` (`:87`), `Company.website` (`:129`),
    `Company.linkedin` (`:131`), `Book.isbn` (`:165`), `Book.source_url` (`:168`)
    and `Explore.url` (`:223`). AND THE MANIFEST''S OWN DECLARED HEX LITERALS ARE
    EXCISED FROM THE TEXT BEFORE THE SPAN WALK, DECIDED HERE FOR THE SAME REASON §6.4
    DECIDES THE ISBN AND IN THE SAME BREATH, BECAUSE WITHOUT IT THIS LEG IS RED BY
    CONSTRUCTION OVER A WHOLLY CORRECT CORPUS. The reach includes `tests/fixture_vault.py`,
    which BY §3''s OWN DESIGN carries `CORPUS_DIGEST` (64 lowercase hex) and, for
    the single non-UTF-8 member, `NoteSpec.raw_bytes_hex` — that note''s COMPLETE
    bytes in lowercase hex, which leg (b) requires to be declared there and asserted
    byte-equal — and printable ASCII hex-encodes to bytes whose FIRST NIBBLE IS `2`–`7`,
    always a digit, so a nine-digit run inside such a literal is STRUCTURAL rather
    than unlucky: the five bytes of `type:` encode to `747970653a`, whose first nine
    characters are the phone-shaped run `747970653`, and `normalize_phone("747970653")`
    matches neither reserved pattern. A 64-character sha256 hex literal is a smaller
    instance of the same class — it carries a ≥9-digit run often enough that a merely
    RE-TAKEN digest could redden the leg on nothing but a legitimate corpus edit.
    THE EXCISED SET IS THEREFORE EXACTLY THE MANIFEST''S DECLARED HEX LITERALS, BY
    NAME AND NEVER BY SHAPE: `CORPUS_DIGEST`, every non-`None` `NoteSpec.raw_bytes_hex`,
    and the optional restatement of AC-3(iv)''s `CENSUS_DIGEST` that AC-3(iv) permits
    `fixture_vault.py` to carry for readability — and nothing else. Each is asserted
    FIRST to be well-formed lowercase hex of even length (`CORPUS_DIGEST` exactly
    64 characters, a restated `CENSUS_DIGEST` exactly 64). AND THE PRESENCE ASSERTION''S
    DOMAIN IS THE REACH, NEVER THE INDIVIDUAL FILE, WHICH IS STATED HERE BECAUSE THE
    TWO READINGS DIFFER BY ~50 REDs OVER A WHOLLY CORRECT CORPUS: each declared literal
    is asserted to OCCUR SOMEWHERE IN THE REACH — the union of the bytes of every
    file this leg scans, tested ONCE against that union — while the EXCISION is applied
    to EVERY file''s text independently, whether or not that file contains the literal,
    an excision of an absent substring being a no-op that costs nothing. The per-file
    reading is the harmful one and is excluded by name: `CORPUS_DIGEST` and every
    `NoteSpec.raw_bytes_hex` live in `tests/fixture_vault.py` BY §3''s OWN DESIGN
    and appear in no corpus note at all, so a per-file presence assertion would hold
    for exactly one of the ~51 files in reach and be RED on the other ~50, on a corpus
    with nothing wrong with it — the same criterion-versus-code fork the word "corpus-relative"
    closed in AC-1(a), with the same absence of any in-cage remedy once these criteria
    are signed (the builder facing it could only narrow a signed criterion or delete
    the assertion). The union domain is what the anti-hiding-place argument actually
    wants and loses nothing: an exemption declared for a literal that occurs NOWHERE
    in reach is still RED rather than free, so the exemption still cannot become a
    hiding place. The three surfaces that restate this — `## Design` §6.4, Task 8,
    and `## Edge Cases`''s "A declared hex literal read as a phone" — say the same
    thing in the same words. It is an author-declared, named exemption asserted by
    equality exactly as `RESERVED_ISBN` is, so it can no more be padded than that
    one can: any other ≥9-digit run anywhere in reach is still scored as a phone and
    still RED. The excision is scoped to THIS leg''s shape scan alone — leg (b)''s
    token scan is unaffected (a lowercase hex literal yields no extracted token, which
    is why leg (b) already requires that casing) and leg (e)''s absolute-path scan
    is unaffected. (b) NAME CLOSURE, SPLIT BY POSITION AND BY TOKEN KIND — THE SPLIT
    IS THE WALL. `fixture_vault.py` declares THREE literal frozensets and no computed
    membership: `NAME_POOL` (the constructed given names, surnames and company words
    the specimens are built from), `CONNECTIVE_SET` (the corruption classes'' own
    non-identifying furniture, FIXED BY ENUMERATION AT EXACTLY `{"Me", "My", "Dave"}`
    — the package''s OWN calendar/arrow/transcript prefix vocabulary, whose union
    across the three prefix regexes that spell a capitalized alternative is exactly
    that set: `name_cleaning.py:46` `_CALENDAR_PREFIX_RE` matches `^(Dave|Me|My)\s*[-/]\s+`
    and `:54` `_ARROW_PREFIX_RE` matches `^(Dave|Me|My)\s*[→⟶⇒➜↦⇨]\s*`, while `:55`
    `_ME_TO_PREFIX_RE` matches `^(Me|My)\s+to\s+` and carries NO `Dave` alternative
    — an earlier draft of this criterion said all three matched `(Dave|Me|My)`, which
    is wrong about `:55` and right about the union, and the union is what the set
    is; the test asserts that equality against the literal set written into this criterion,
    so the set cannot grow without an AC change and is never a build-time choice;
    the lowercase and punctuation connectives the classes also need, `to`, `->` and
    `→`, are NOT members, because the stated extractor cannot produce them and a member
    the closure can never exercise is a declaration that lies, and the mail-header
    prefixes `Re`, `Fwd` and `Fw` are NOT members for the harder version of the same
    reason — a Grep over the whole tree finds them in no Tier-1 branch, no recovery
    regex and no candidate census class, so no census row could ever measure one and
    no corpus specimen could ever honestly carry one, P11; AND THE SET IS ENUMERATED
    FROM THE WHOLE FURNITURE SURFACE RATHER THAN SAMPLED FROM THREE REGEXES OF ONE
    FILE — that surface is SIXTEEN regexes in two files and there is no third — the
    eleven of `name_validation.py` (`:66`, `:74`, `:82`, `:101`, `:107`, `:110`, `:113`,
    `:120`, `:123`, `:351`, `:445`) and the five prefix/suffix regexes of `name_cleaning.py`
    (`:46`, `:54`, `:55`, `:56`, `:57`) — plus both Tier-1 tables, the ten person
    branches (`name_validation.py:190-309`) and the five company ones (`:371-438`),
    with P16 recording the complete pass and P17 recording that no regex anywhere
    else in the package carries furniture. APPLYING THE RUN RULE THIS CRITERION PINS
    DOWN BELOW TO THE LITERAL SPELLING EACH REGEX CARRIES, THE UNION OF EXTRACTED
    FURNITURE TOKENS IS EXACTLY `{Me, My, Dave}` AND NO MEMBER IS ADDED — the two
    branches the earlier sampling omitted are the reason the rule had to be pinned
    first, and neither adds one. `archive_prefix` (`name_validation.py:110`, `^z+Archived\b`;
    recovery arm `name_cleaning.py:56`, `^z+Archived\s*-\s*`) contributes NOTHING,
    because `zArchived`/`zzArchived` is one run beginning lowercase and the run rule
    yields no token from it; that is not a reading chosen for convenience, since all
    five real specimens this repository commits for the branch spell it exactly that
    way with no exception (P15), so `Archived` is NOT a member and putting it in would
    plant an unexercisable literal in a frozen set — round 4''s defect authored by
    a fold instead of by a builder. `unknown_contact` (`name_validation.py:113`, `unknown\s+contact`
    under `re.IGNORECASE`; recovery arm `name_cleaning.py:57`, `\s+unknown\s+contact\b`)
    contributes nothing FROM THE CODE either, both regexes spelling the literal lowercase
    — but it is the one branch whose answer THIS REPOSITORY''S COMMITTED SPECIMENS
    leave open, because `IGNORECASE` hands the letter-case to the live vault and this
    repository commits BOTH forms: the lowercase suffix form the branch''s own "WhatsApp
    scanner artifact" comment describes (`tests/test_name_validation.py:248`, `:254`;
    `tests/test_name_cleaning.py:135`, `:140`) and a capitalized standalone form (`tests/test_name_gate.py:96`;
    `tests/test_lint_vault_fix_gate.py:58`; and the branch''s own display `specimen=`
    field at `name_validation.py:274`). THE FLAG ITSELF IS NOT WHAT MAKES THAT CELL
    SPECIAL, AND SAYING SO KEEPS THIS SENTENCE HONEST: `re.IGNORECASE` is carried
    by EIGHT of the sixteen regexes (P17 — all five of `name_cleaning.py`''s and `name_validation.py`''s
    `:82`, `:110`, `:113`; `:74` does not carry it), so the code pins the live casing
    of `Me`/`My`/`Dave` no more tightly than `unknown contact`''s. What separates
    them is the CORPUS: every committed specimen of the three prefix branches spells
    them canonically with no `ME`/`DAVE` variant anywhere in the tree (P16), while
    `unknown_contact` is committed both ways. The reconciliation instruction below
    is written general for exactly that reason and needs no widening — if the census
    measures a live `ME - X` form, it is absorbed at the same one-time edit. THAT
    ONE RESIDUAL DEGREE OF FREEDOM IS CLOSED BY RECONCILIATION RATHER THAN BY A GUESS:
    `CONNECTIVE_SET` therefore carries the SAME ONE-TIME PRE-ORIGINATION RECONCILIATION
    INSTRUCTION AC-3''s CLASS FLOOR CARRIES FOR ITS HAND-LISTED HALF (the branch half
    of that floor needs none, being read from the package at test time; this set needs
    one for the same reason those six shape classes do — the regexes declare patterns,
    not token lists, so there is no declaration to read) — before Dave signs, this
    literal set is reconciled ONCE against the census''s measured character profiles,
    so that if the census measures the live `unknown_contact` form as capitalized
    then `Unknown` and `Contact` are added HERE, in this criterion, and if it measures
    the lowercase suffix form they are not; the same reconciliation runs for any other
    furniture class whose measured profile would put a capitalized non-name run into
    an identity position. AFTER THAT ONE EDIT THE SET IS FROZEN EXACTLY AS IT IS NOW
    — asserted equal to the literal written in this criterion, unable to grow without
    an AC change — so the safety property is untouched, and the instruction adds NO
    obligation over members the builder does not author, because the set still carries
    no non-vacuity clause of any kind. THE CHEAPER ALTERNATIVE IS NAMED AND REJECTED
    so a builder does not reach for it: authoring the specimen in the lowercase form
    whatever the census measured would hold the set at three members for free, but
    it destroys the character profile the specimen exists to carry, which is the same
    argument that keeps the "lowercase it for green" dodge out of AC-2''s declared
    oracle and AC-3''s declared verdict), and `PROSE_ALLOWLIST` (the ordinary English
    of the note bodies plus this module''s own identifiers, docstring and comment
    vocabulary). THE EXTRACTOR IS STATED ONCE AND ITS "RUN" IS PINNED TO ONE READING,
    BECAUSE TWO READINGS OF IT RETURN DIFFERENT ANSWERS ON THE SAME BYTES AND THE
    DIFFERENCE DECIDES A FROZEN SET''S OWN MEMBERSHIP: decode every byte in reach
    with `errors="replace"`; a RUN is a MAXIMAL contiguous span of characters drawn
    from the class {Unicode letters, combining marks, `''`, `-`} — maximal meaning
    the span is bounded only by a character OUTSIDE that class (whitespace, a digit,
    any other punctuation, or the end of input) and NEVER restarted at an internal
    capital, so there is no camelCase splitting; a run is EXTRACTED as a token iff
    its FIRST character is an uppercase or non-ASCII letter; and an extracted run
    has leading and trailing `''` and `-` trimmed before it is compared against any
    set. FOUR WORKED CONSEQUENCES, WRITTEN OUT SO THE RULE IS CHECKABLE RATHER THAN
    INTERPRETABLE: `McDonald` is ONE token `McDonald`, never `Mc` plus `Donald`; `d''Angelo`
    is ONE run beginning with the lowercase `d` and therefore yields NO token (the
    extractor-domain residue already named in `why:`, not a new hole); `Zeta-9` yields
    `Zeta` (the run is `Zeta-`, trimmed); and — the consequence that settles `CONNECTIVE_SET`''s
    membership above — `zArchived` and `zzArchived` are each ONE run beginning with
    the lowercase `z` and yield NO TOKEN AT ALL. The maximal reading is chosen over
    the capital-restarting one for two stated reasons rather than by default: it is
    the reading that every real specimen this repository has ever committed for the
    `archive_prefix` branch is consistent with, all five of them spelling the prefix
    with nothing between the `z` and the capital (P15), and it is the reading that
    gives an ordinary hyphenated or Mc-prefixed surname the one answer a name needs.
    It is applied to two DISJOINT POSITION SETS with different rules. ONE ADMISSION
    IS DERIVED FROM THE PACKAGE RATHER THAN DECLARED HERE: an identity-position token
    whose `str.lower()` is a member of `name_cleaning._GENERIC_ORG_SUFFIXES` (`name_cleaning.py:58`
    — exactly `support`, `ltd`, `inc`, `corp`, `group`, `team`, `limited`, `llc`)
    is admissible with no `NAME_POOL` membership and no census row. THE COMPARISON
    OPERATION IS NAMED RATHER THAN DESCRIBED: the test lowercases with `str.lower()`,
    which is what the package itself does at `:148`, `:185` and `:191` — an earlier
    draft said "casefolded", which the package nowhere does; the eight members are
    ASCII so `lower` and `casefold` agree on them, but the corpus deliberately carries
    non-ASCII specimens and the criterion should name the operation its own test performs.
    It is READ from the package rather than written into `fixture_vault.py` precisely
    so a builder looking for the cheapest green cannot pad it, and it exists because
    the identity-position list below now reaches `Person.company` and `Book.publisher`:
    a specimen written `Voxleaf Ltd` would otherwise oblige the conductor to certify
    that `Ltd` occurs zero times in a vault of 2,159 company notes, which is not a
    claim anyone can honestly make, and none of the eight members can hide a person.
    **IDENTITY POSITIONS — ENUMERATED FIELD BY FIELD AGAINST `models.py`, NEVER NAMED
    BY CATEGORY, AND THE ENUMERATION IS ITS OWN RULE''S OUTPUT.** The rule is stated
    in THREE CLAUSES so a ninth entity type or a new field is CLASSIFIED rather than
    missed — and stated in three rather than one because a single "iff its value names
    a PERSON or an ORGANISATION" did not generate the list written under it in either
    direction, which is a criterion that is buildable two ways by its own reconciliation
    instruction. **CLAUSE 1 — NAMING.** A declared field is an identity position iff
    its VALUE IS a person''s or an organisation''s name: the whole scalar, or each
    element of the list, being such a name or a wikilink to a note that holds one.
    It is deliberately "IS a name", not "COULD CONTAIN one": the second reading sweeps
    every free-text field into the pool and obliges the conductor to certify ordinary
    English words with zero-hit live-vault rows, which is finding 1''s unsatisfiable-obligation
    shape rebuilt on purpose. **CLAUSE 2 — DECLARED OVER-CONSTRAINT, so reconciliation
    does not delete it.** Plus the four entity `title` fields — `Book.title` (`:160`),
    `Watch.title` (`:193`), `Explore.title` (`:222`), `Exploration.title` (`:295`).
    A book, a film, a link and a living document are not people or organisations,
    so clause 1 does NOT reach them; they are in the list ON PURPOSE and this clause
    is the authority a later reconciliation reads before removing them. The reason:
    a title is the human-written display string of a note whose live original the
    corpus author is copying a character profile from, so transcribing a real one
    is the same slip as transcribing a real name, and it costs nothing extra — `##
    Write Targets` already requires every identity-position token in a specimen to
    be a constructed string, naming "a naturally-worded meeting title" as the example.
    **CLAUSE 3 — UNDECLARED KEYS, BY DEFAULT AND WITH NO OPT-OUT.** `BaseEntity` sets
    `model_config = ConfigDict(extra="allow", ...)` (`models.py:31-32`), so a corpus
    note may carry frontmatter keys no model declares — a `manager:` or `introduced_by:`
    on a forward-compatibility or schema-drift specimen — and clauses 1 and 2, being
    enumerations over DECLARED fields, cannot reach them at all. Any manifest-declared
    value for a key the note''s model class does not declare is therefore an IDENTITY
    POSITION, full stop: there is no manifest flag that marks one prose, because a
    builder-settable exemption is the escape hatch this criterion has now been folded
    for twice. The default is satisfiable by construction rather than being an obligation
    over a set nobody authors — the corpus author chooses both which undeclared keys
    exist and what they hold, and the only cost of the default is that those values
    must be short constructed tokens rather than sentences. **THE CURRENT ANSWER**,
    reconciled field by field against every member of `TYPE_TO_MODEL` (the full pass
    is P14): every corpus filename stem (with the declared filename grammar''s `@`
    sigil and `Meeting <date> - ` prefix stripped), plus the manifest''s declared
    values for `Person.name` (`models.py:79`), `Person.aliases` (`:80`), `Person.company`
    (`:84`), `Company.name` (`:128`), `Book.title` (`:160`), `Book.author` (`:161`),
    `Book.publisher` (`:166`), `Watch.title` (`:193`), `Watch.director` (`:195`),
    `Watch.streaming_service` (`:199`), `Watch.recommended_by` (`:200`), `Explore.title`
    (`:222`), `Explore.source` (`:224` — "where you found it / who mentioned it"),
    `GiftIdea.for_person` (`:242`, frontmatter alias `for`), `GiftIdea.source` (`:243`),
    `Meeting.attendees` (`:261`), `Exploration.title` (`:295`) and `Exploration.related`
    (`:299`), plus every undeclared key''s declared value under clause 3. **FOUR EXCLUSIONS,
    EACH ARGUED, AND ONE CORRECTION.** `Person.title` (`:85`) is EXCLUDED: it is a
    JOB title, it names nobody, and forcing `Director` into a pool that owes a zero-hit
    live-vault row would manufacture an unsatisfiable obligation on purpose — `Person.company`
    (`:84`) and `Person.title` (`:85`) are different fields and only the first carries
    identity. `Meeting.topics` (`:262`) is EXCLUDED as free prose for the same reason.
    `Exploration.origin` (`:300`, glossed "What sparked this - problem, article, conversation"
    at `:281`) is EXCLUDED on the same argument and it is the closest call in the
    list: it is a SENTENCE rather than a name, so clause 1 does not reach it and clause
    1''s "could contain" reading is the one that breaks the criterion — the residue
    is stated plainly below rather than closed by a fifth clause. `Exploration.graduated_to`
    (`:301`, glossed `[[Project]]` at `:282`) is EXCLUDED: a project is neither a
    person nor an organisation, and a constructed project name like `Q3 Migration`
    would put ordinary words into a pool owing zero-hit rows — finding 1''s shape
    again. And `Meeting` DECLARES NO `title` FIELD AT ALL (`:259-263` — `date`, `attendees`,
    `topics`, `meeting_id`; `BaseEntity` adds only `type` and `tags`, `:39-40`), so
    the phrase this list replaced named a field the schema does not have; a meeting''s
    title is not lost, because it lives only in the filename and the stem scan already
    reaches it. The list is reconciled against the schema BY APPLYING ALL THREE CLAUSES,
    BEFORE origination, exactly as AC-3''s CLASS FLOOR reconciles its hand-listed
    half, so a field added to a model costs one edit here rather than a re-sign. IT
    IS HAND-LISTED RATHER THAN DERIVED FOR A STATED REASON AND NOT BY OVERSIGHT: `models.py`
    declares the FIELDS but nothing in it declares which of them hold a person''s
    or an organisation''s name, so unlike AC-2''s `TYPE_TO_MODEL`, AC-3''s `branch_id`s
    and AC-4''s repository set there is no population to read — the classification
    is judgment, which is why it sits with a stated rule, a recorded field-by-field
    pass (P14) and a reconciliation instruction instead of a runtime read. Every token
    extracted from an identity position MUST be in `NAME_POOL ∪ CONNECTIVE_SET` or
    be an admitted org suffix. `PROSE_ALLOWLIST` IS NOT A TERM IN THIS ASSERTION and
    is structurally unreachable from it; the test additionally asserts `PROSE_ALLOWLIST`
    is DISJOINT from the identity-position token set, so no token can hold both roles
    and adding a surname to the allowlist buys nothing whatsoever for a `name:` value,
    an `aliases` entry, a title field or a filename stem. **FREE-PROSE POSITIONS**
    — everything else in reach: note bodies, non-identity frontmatter values, and
    `fixture_vault.py`''s own source. Tokens here must be in `NAME_POOL ∪ CONNECTIVE_SET
    ∪ PROSE_ALLOWLIST`. **NON-VACUITY, `NAME_POOL` ONLY** — every `NAME_POOL` entry
    occurs as an extracted token in at least one IDENTITY position; "somewhere in
    the reach" is deliberately NOT the bar, because a pool padded through a note body
    would satisfy it. It is scoped to `NAME_POOL` because `NAME_POOL` is the one declared
    set THE BUILDER AUTHORS, so it is satisfiable by construction — declare only what
    the corpus uses. **`CONNECTIVE_SET` CARRIES NO NON-VACUITY OBLIGATION, AND ITS
    ABSENCE IS A FIX RATHER THAN A RELAXATION.** A mandatory occurrence clause over
    a set the builder does NOT author is the defect generator this criterion has now
    bred three times (`to`/`->`/`→`, then `Re`/`Fwd`/`Fw`): every such set has produced
    at least one member the corpus cannot exercise, and each earlier fold pruned the
    member and kept the clause. Nothing is lost by dropping it, because exercising
    the furniture was never the wall — what stops `CONNECTIVE_SET` becoming a second
    escape hatch is that it is frozen by literal enumeration IN this criterion and
    asserted equal to it, and coverage of whatever connective the live vault actually
    produces is already guaranteed by AC-3(i), which requires a specimen for every
    MEASURED census class and, correctly, can never demand one for a class the vault
    does not have. The single corpus member that is not valid UTF-8 is exempt from
    the token scan and instead has its COMPLETE bytes declared in the manifest as
    a LOWERCASE hex literal and asserted byte-equal — reviewed rather than silently
    skipped past the wall, and lowercase so the literal yields no extracted token
    and can never itself become a reason to grow the allowlist. (c) POOL PROVENANCE
    — SCOPED TO `NAME_POOL` ALONE, AND A CONTAINMENT RATHER THAN AN EQUALITY. `docs/vault-shape-census.md`
    carries a pool table whose rows each give a certified token, the shape class it
    is constructed to carry, and the conductor''s live-vault non-occurrence scan for
    it (the command run and its verbatim stdout, showing `0` hits as a name token
    anywhere in the vault — `## Write Targets` requires that command to emit a COUNT,
    so an honest zero result records verbatim as `0` rather than as nothing). The
    test asserts that `NAME_POOL` ⊆ the census''s pool table — ONE DIRECTION, and
    the direction matters — that every row carries a non-empty command and a non-empty
    stdout, and that the table''s token set is DISJOINT from `CONNECTIVE_SET`. AND
    IT ASSERTS CENSUS FIXITY FIRST, BEFORE IT TRUSTS ANY ROW OF THAT TABLE: `sha256`
    over `docs/vault-shape-census.md`''s bytes equals the `CENSUS_DIGEST` literal
    declared in AC-3(iv) and frozen by the same signature that freezes this criterion.
    This leg is asserted HERE as well as in AC-3 and not merely inherited from it,
    because each criterion''s `check:` is its own test function and an unguarded AC-5
    is the worse of the two exposures: the pool table is where this criterion''s entire
    ground truth lives, the suite cannot re-derive a single one of its non-occurrence
    claims, and `docs/**` is builder-writable in full (`pipeline-runners.yaml:34-38`,
    P7), so without the fixity assertion a builder who wants a convenient, easy-to-spell
    pool token — one that may collide with a real name in a vault the builder cannot
    see and has no way to check — adds a row asserting a scan that was never run,
    with fabricated command and stdout text satisfying every other check this leg
    makes (non-empty command, non-empty stdout, containment, disjointness), and `##
    Intent`''s sentence about Dave''s contacts'' real names has no machine check standing
    behind it at all. THE VALUE''S LOCATION IS THE WALL, not the digest: it is read
    from the signed AC-3 fence in `docs/vault-fixtures.md`, never from a constant
    in `tests/fixture_vault.py`, because a constant the build owns is updated in the
    same commit that edits the file it digests. The residue is stated rather than
    papered over: a build that deletes the assertion outright is the ordinary "did
    not implement the criterion" exposure every AC here carries — caught by the battery
    and by code review — and is not a bypass of this leg, whose subject is the expected
    value''s home. THE DIRECTION IS NOT A WEAKENING AND THE REASON IS AN ORDERING
    FACT ABOUT THIS PIPELINE, NOT A PREFERENCE: the census is a PRECONDITION that
    lands in HEAD before Dave signs these criteria and long before any corpus exists,
    while `NAME_POOL` is declared in-cage by a build that has not happened, so a both-directions
    equality would ask the earlier artifact to predict the later one''s exact token
    set — and a census that certifies one token the build does not end up using would
    go RED with no in-cage remedy except inventing a note to consume it. Closure is
    not weakened by a byte: a token with no row still cannot enter an identity position,
    which is the entire property, and a certified-but-unused row is not a leak because
    it carries its own scan. It also removes this item''s dominant recurring cost
    — under an equality every corpus edit is a paired edit across the cage boundary,
    and under a containment it is not. The leg is the same read-the-artifact-and-assert-its-shape
    move AC-3 makes: hermetic, no subprocess and no vault read. The connectives are
    exempt from provenance because a non-occurrence claim about them is unmakeable,
    not merely tedious: `Me`, `My` and `Dave` are the live stored-name prefix forms
    this vault actually produces — `name_validation.py:238-248` carries `specimen="Me
    to David Field"` on its `me_to_prefix` Tier-1 branch, `:226-236` carries `Dave
    - Thomas Gatten` on `calendar_prefix`, and `name_cleaning.py:46`/`:54`/`:55` strip
    exactly `(Dave|Me|My)` — so a zero-hit row for any of them would be a false statement
    inside the artifact whose whole job is to be the trustworthy ledger. The exemption''s
    ground is the code''s own vocabulary and NOT a guarantee about the census''s counts:
    an earlier draft justified it by saying AC-3 requires the census to report `Me
    to ` prefixes with a non-zero count, which AC-3 no longer promises now that any
    class may be ruled ABSENT. It does not need to promise it — `Dave|Me|My` being
    live prefix vocabulary in this package is a fact about `name_cleaning.py`, readable
    without the census, and it is what makes the non-occurrence claim unmakeable whatever
    the census measures. (d) THE PROPERTY IS NOT PAID FOR — every reserved phone in
    the corpus still normalizes through `normalize_phone` to a stable digits-only
    value (`phone_normalization.py:39-55` splits off the WhatsApp JID suffix and then
    strips every non-digit, so `+44 7700 900123` yields `447700900123`; the package
    emits E.164 nowhere and none is asserted here), and `phones_match` (`:58-90`)
    still matches that value against the reserved number''s `0`-prefixed and `+44`-prefixed
    variants, so the reservation does not cost the shape the fixture exists to exercise.
    (e) HERMETIC — materialization writes only underneath the caller''s `dest`, and
    the corpus contains no absolute filesystem path: no occurrence of `/Users/`, and
    no live vault path in any note or in the manifest.

    why: This package installs `-e` into three consumer repos and its git history
    is permanent — a real address, number, profile URL or NAME committed here is not
    meaningfully retractable, which is why the 2026-07-05 routing note put this item
    on Opus in the first place. Legs (b) and (c) exist because the first draft of
    this criterion walled two of the three categories `## Intent` names and left the
    third — and names are the field D1''s amendment says the corpus exists to carry
    the shape of, so the uncovered category was the likeliest one to be transcribed
    verbatim: a specimen whose email is correctly moved under `@example.com` and whose
    phone is correctly moved into the drama range, but whose `name:` is still the
    live vault''s, passes AC-1 (the digest freezes whatever bytes exist), AC-2 (the
    manifest declares whatever name is present as "expected"), AC-3 (per-specimen
    verdicts test refusal behaviour, not identity) and the old AC-5 (no email/phone/URL
    violation) all green. Names have no RFC 2606, so the wall cannot be a reserved-range
    rule and CANNOT be a denylist either — committing a list of real names to catch
    real names would be the leak it is meant to prevent. Closure is the available
    structural form: every name-shaped token in an IDENTITY position must have been
    deliberately added to a declared pool, which turns "transcribed by accident" into
    "typed the real name into the pool and the census''s provenance table as well".
    THE POSITION SPLIT IS WHAT MAKES THAT CLOSURE REAL, and it is the correction of
    a first attempt that failed on its own terms. That attempt ran ONE undifferentiated
    scan over the whole reach and offered two buckets — the pool, or a prose allowlist
    "of the ordinary vocabulary the note bodies and YAML keys need". The allowlist
    was unbounded, owed no census row, and was consulted from the same positions the
    wall exists to police, so the cheapest green for a specimen carrying the live
    vault''s real surname was to type the surname into the allowlist, where a real
    name is not visibly out of place: the wall''s bypass was larger, cheaper and more
    heterogeneous than the wall, which is not closure. The reach makes that worse
    rather than better, and the reach is still right — `fixture_vault.py` is a Python
    module and every capitalized identifier in it (`Path`, `SkippedNote`, `NameGateRefusal`,
    `UnicodeDecodeError`, the `AC-`/`WI-` prose) is an extracted token, so an allowlist
    covering it must be large and heterogeneous on day one. Splitting by POSITION
    rather than by bucket makes the size of the allowlist stop mattering: it is reachable
    only from free prose and is asserted disjoint from every identity token, so it
    can grow to whatever the module''s vocabulary needs without ever being able to
    admit a token into the field that carries identity. TWO CHEAPER ALTERNATIVES ARE
    REJECTED HERE so a builder does not rediscover them. Putting the census provenance
    obligation on the allowlist too collapses it into the pool — it taxes every docstring
    word with a conductor scan and doubles the two-artifact join for no privacy gain,
    since prose is not where identity lives. Dropping the allowlist entirely and forcing
    all prose through the pool is the same move by another name and makes the pool
    table unreviewable, which destroys the mitigating control''s own premise: what
    a human reviews is a few hundred declared IDENTITY tokens once. Likewise the CONNECTIVE
    split: a first draft put connectives and names in one pool under a type tag and
    then demanded a zero-hit live-vault row for every member, which is unsatisfiable
    by construction for `Me` — AC-3 charges the same artifact with reporting `Me to
    ` prefixes as a measured, non-zero class — so every route through it was either
    a RED criterion or a fabricated row. Connectives are exempt from provenance because
    non-occurrence is not a claim that can honestly be made about them; the exemption
    is safe ONLY because the set is frozen by enumeration in the criterion, which
    is what stops it becoming the same escape hatch the allowlist was, and it is asserted
    disjoint from the census table so nothing can be smuggled across the boundary
    in either direction. THE FOURTH FOLD REMOVED THE GENERATOR RATHER THAN ITS LATEST
    INSTANCE, AND THAT IS THE ONE THING TO KEEP IF THIS CRITERION IS EVER EDITED AGAIN.
    Three consecutive independent reads found a defect of a single family: a mandatory
    obligation over a declared set THE BUILDER DOES NOT AUTHOR — first a non-occurrence
    row demanded of `Me`, then an occurrence demanded of `to`/`->`/`→`, then an occurrence
    demanded of `Re`/`Fwd`/`Fw`, tokens that a Grep shows occur nowhere in this repository
    outside this document (P11). Each earlier fold pruned the member and kept the
    clause, which is why the family kept producing. Dropping `CONNECTIVE_SET`''s non-vacuity
    and making (c)''s pool relation a CONTAINMENT removes both surviving instances
    of the pattern at once, and the property they were nominally protecting is not
    lost: padding is prevented by the literal enumeration and by the per-token census
    scan, not by exercise. The same reading is why the identity-position list is now
    ENUMERATED against `models.py` with line cites instead of named by category —
    the previous phrase, "the company/meeting title fields", is exactly how `Person.company`
    was missed, and reading the models field by field showed it had also named a field
    `Meeting` does not have (`:259-263`) while missing `Meeting.attendees` (`:261`),
    `Book.author` (`:161`), `Watch.director` (`:195`), `Watch.recommended_by` (`:200`),
    `Explore.source` (`:224`) and `GiftIdea.for_person` (`:242`). Patching the one
    field named would have left six doors of the same shape one entity type over;
    stating the generating rule and the enumeration closes the family the way dropping
    non-vacuity closes the other one. THE FIFTH FOLD IS WHY THAT RULE IS NOW THREE
    CLAUSES INSTEAD OF ONE, AND THE LESSON IS NARROWER THAN THE FOURTH FOLD''S. Stating
    a one-line rule and then enumerating under it is not the same as enumerating BY
    it: two independent reads applied the single rule to `models.py` field by field
    and got a list that differed from the written one in both directions — it omitted
    `Exploration.related` (`:299`), whose own docstring (`:280`) glosses its members
    as `[[Other Exploration]], [[Person]], etc.`, and it included four media-`title`
    fields the rule plainly excludes. The omission was the expensive direction, because
    `related` is a field whose value IS a person link and the criterion scored it
    free prose: a real contact''s name written there went RED once on the free-prose
    leg and the cheapest green was ONE `PROSE_ALLOWLIST` entry — no pool membership,
    no census row — which is the exact bypass rounds 1 through 4 were each raised
    to close. And it was live rather than theoretical for this corpus specifically:
    AC-2 derives its sweep from `set(TYPE_TO_MODEL)`, `exploration` is a member, P4
    measures ZERO `exploration` references anywhere under `tests/`, so this corpus
    is guaranteed to contain the first `exploration` fixture anyone has authored —
    hand-written from a live note''s shape, by an author with nothing to copy from,
    and `related:` is the field that shape hangs on. The inclusion direction cost
    nothing yet but was the same defect: a criterion whose own reconciliation instruction
    ("reconciled against the schema BEFORE origination") tells a later reader to re-derive
    the list from the rule, while the rule as written deletes four listed fields,
    is buildable two ways — the WI-144 shape. Clause 2 fixes that by making the over-constraint
    DECLARED rather than accidental, so the reconciliation preserves it instead of
    pruning it on the rule''s own authority; clause 3 reaches the one door no enumeration
    over declared fields can, since `extra="allow"` (`:31-32`) means a specimen may
    carry keys no model declares. The two undecided siblings are decided rather than
    left: `Watch.streaming_service` (`:199`) names an organisation exactly as `Book.publisher`
    (`:166`) does and is now listed with it, and `GiftIdea.source` (`:243`) is listed
    alongside its glossed sibling `Explore.source` (`:224`) because a gift idea''s
    source is plausibly whoever suggested it — the same value kind must not get opposite
    answers inside one enumeration, which is what produced this finding. AND THE THIRD
    PLACE THE MACHINE STOPS IS NOW NAMED WITH THE OTHER TWO, because clause 1''s "IS
    a name, not COULD CONTAIN one" is what buys the criterion its satisfiability:
    a real name written into `Exploration.origin` (`:300`), `Meeting.topics` (`:262`)
    or a note body is walled by the free-prose leg and the pool''s human review, not
    by the closure, and one allowlist entry is its cheapest green. That residue is
    not new and is not a regression — note BODIES have been on that side since round
    1 and always will be, because prose cannot be closed against a pool without taxing
    every English word with a conductor scan (the alternative rejected two paragraphs
    above). What the fold guarantees is the line''s PLACEMENT: no field whose value
    IS a name sits on the prose side of it, which is what `Exploration.related` was
    doing. The org-suffix admission is derived from `name_cleaning._GENERIC_ORG_SUFFIXES`
    rather than hand-declared for the same discipline: a fourth hand-written literal
    set is what the generator eats, and a set read from the package cannot be padded
    by whoever is looking for the cheapest green. Say plainly where the machine stops:
    the suite is hermetic and cannot read the live vault, so the GROUND TRUTH that
    a pool token does not name a real contact is the conductor''s recorded scan in
    the census, not an in-suite assertion — leg (c) asserts that the scan was run
    and recorded for every token, and the census''s re-runnable command is what a
    later reader checks it against. That is the mitigating control, named and tied
    to a criterion rather than left as D4''s unstated "reviewable by eye" aside —
    and it is a real reduction, because what a human now reviews is a few hundred
    declared tokens once, not fifty notes of free text every time the corpus changes.
    THE SECOND PLACE THE MACHINE STOPS IS THE EXTRACTOR''S OWN DOMAIN, and it is named
    here rather than chased with another clause. The extractor takes runs beginning
    with an uppercase or non-ASCII letter, so an identity value written entirely in
    lowercase yields no token and is outside the wall — the same fact that (correctly)
    keeps `to`, `->` and `→` out of `CONNECTIVE_SET`. A deliberate "lowercase it to
    get green" dodge is therefore not closed by machine, and deliberately is not:
    it destroys the character profile the specimen exists to carry, so AC-2(b)''s
    hand-written declared oracle and AC-3''s declared per-specimen verdict both go
    RED on it, and the residue is covered by the same one-time human review of the
    pool table. A fifth clause bolted on to close it would be a mandatory obligation
    over something the criterion cannot see — the shape of every finding this criterion
    has produced so far. THE SIXTH FOLD PINNED THE EXTRACTOR''S "RUN" AND THEN RE-ENUMERATED
    THE FURNITURE SURFACE IN THAT ORDER, AND THE ORDER IS THE WHOLE LESSON. The finding
    arrived as two halves that disagreed: one read said `CONNECTIVE_SET` was sampled
    from three of the five prefix/suffix regexes in `name_cleaning.py` and should
    gain `Archived`, `Unknown` and `Contact`; the other said that literal fix is contradicted
    by this repository''s own specimens, because the criterion''s extractor never
    said what a "run" is and, under the plain maximal-span reading, `zArchived` yields
    no token at all — so `Archived` would be an unexercisable literal in a frozen
    set, which is exactly the round-4 defect with a gate''s fold as its author instead
    of a builder. Both halves are right and the resolution is sequencing, not a compromise:
    the membership question is not answerable until the extraction rule is, so the
    rule is stated first (maximal span, no camelCase restart, first character decides,
    trim `''`/`-`), with four worked examples so it is checked rather than interpreted,
    and only THEN is the surface re-enumerated by applying it. Done in that order
    the answer is that the set does not move: the fifteen regexes'' own literal spellings
    extract to exactly `{Me, My, Dave}`, `archive_prefix` contributes nothing under
    the reading every committed specimen for it supports (P15, five specimens, no
    exceptions), and `unknown_contact` contributes nothing from the code because both
    its regexes spell the literal lowercase. What the re-enumeration did buy is the
    one genuinely undecided cell being named instead of guessed: `re.IGNORECASE` on
    `name_validation.py:113` puts the letter-case of the live `unknown contact` form
    in the vault''s hands rather than the code''s, and this repository already commits
    it BOTH ways, so no amount of reading `obsidian_schemas/` settles it. That cell
    gets AC-3''s own remedy — a one-time pre-origination reconciliation against the
    census, which lands in HEAD while these are still drafts — rather than a fifth
    hand-written literal or a guess frozen by signature. It is worth being explicit
    that the reconciliation instruction is NOT the round-4 generator returning: the
    generator was a mandatory obligation over a set the builder does not author, and
    this set still carries no occurrence obligation at all; what it now carries is
    a one-time edit, made by the author before signature, against an artifact that
    exists by then, after which the set is as frozen as it was before. The general
    rule the two closures share, and the one to attach if this criterion is edited
    again: EVERY SET AC-5 DECLARES IS ENUMERATED BY APPLYING A STATED RULE TO A NAMED,
    ENUMERABLE SURFACE — round 5 needed `models.py` read field by field, this round
    needed the sixteen regexes read one by one, and both defects were "enumerated
    by sampling" rather than by the rule. Leg (d) is the honest cost check: a reserved-range
    rule that broke `normalize_phone`''s own fixtures would have bought privacy by
    deleting the property, and the UK drama range and NANP 555-01xx are chosen precisely
    because they are well-formed dialable-shaped numbers that will never ring. The
    leg names the digits-only output rather than E.164 because that is what the function
    actually produces — it strips every non-digit (`phone_normalization.py:39-55`),
    so the leading `+` does not survive and nothing in this package emits E.164; asserting
    E.164 would have been a criterion the corpus cannot satisfy no matter how well
    the reserved ranges were chosen, and `phones_match`''s `44`/`0` and `1`/10-digit
    arms (`:58-90`) are the property worth protecting anyway. Leg (e) keeps the corpus
    portable — a fixture carrying `/Users/davewascha/...` is both a small leak and
    a note that means something different on any other machine, and D6''s eventual
    export to the consumer repos depends on the bytes travelling unchanged.

    check: test_no_corpus_note_carries_a_live_identifier

    kind: test

    ```


    ### Examples of done


    **Given** someone writes a new test that needs a vault — **when** they call

    `materialize_vault(tmp_path)` — **then** they get ~50 notes with accents, hyphenated
    surnames, an

    address that leaked into a name field, the same person three times, notes that
    will not parse, and

    one of every entity type, without typing a single note. **And** the bug their
    change would have

    shipped is caught by a corpus they did not have to think of, which is the whole
    reason it is there.


    **Given** a future change to the parser that quietly breaks `Exploration` — **when**
    the floor runs —

    **then** it goes RED, because `exploration` is a member of `TYPE_TO_MODEL` and
    the sweep is derived

    from that map rather than from a list someone maintains. **And when** a ninth
    entity type is added

    with no fixture, the same sweep fails for the same reason, rather than the type
    joining `watch`,

    `explore` and `gift-idea` in the untested set.


    **Given** a fixture note someone edits to make their own test pass — **when**
    the floor runs —

    **then** the frozen digest mismatches and says so. **And given** an attempt to
    plant the corpus

    through `repo.save()` instead of copying bytes, **then** the arrow-connective
    and path-hostile

    specimens are refused by the gate and the corpus is provably incomplete — the
    two failures the word

    "frozen" is doing work against.


    **Given** the corpus is read by anyone, anywhere — **when** they look for a real
    person — **then**

    every address is `@example.com`, every number is a range that will never ring,
    every name in a field

    that carries identity — a `name:`, an alias, a person''s `company:`, a meeting''s
    attendee, a book''s

    author, a gift idea''s `for:`, an exploration''s `related:` link, a frontmatter
    key no model even

    declares, a filename — is a token from a pool the census certifies does not occur

    in the live vault, and the shapes are still the ones the live vault actually

    contains, because the census measured the distribution and the committed bytes
    are synthetic. **And

    given** someone adds a note to the corpus whose `name:` is not in that pool, **then**
    the floor goes

    RED — and the only way to green is the pool and the census''s provenance row,
    because the prose

    allowlist that keeps ordinary English quiet is not consulted for a name field
    at all. A real name

    cannot arrive by accident; only by being typed into the pool and the ledger as
    well.

    '
  frozen_intent: '

    Every test in this package should be able to reach for the same vault — one frozen
    sample whose

    shapes came from the real thing, not from Alice and Bob — instead of typing its
    own notes and

    quietly starting from a corpus that has never broken anything. The shapes that
    actually break this

    code (accents, hyphenated surnames, addresses leaking into name fields, the same
    person three times,

    notes that will not parse at all) should live in one place that every later name-and-identity
    change

    gets to regress against, and the entity types nobody has ever tested should stop
    being invisible.

    None of Dave''s contacts'' real names, emails or numbers go into this repository
    to get it.

    '
  note: null
