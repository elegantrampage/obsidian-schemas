schema_version: 1
wi_id: WI-032
spec_path: docs/whatsapp-jid-value-type.md
spec_stage_at_review: exploring
reviewed_at: '2026-09-27T08:00:00+01:00'
reviewer: dave
signoff:
  verdict: PROMOTE
  channel: conversational
  provenance: verified
  signoff_escalation: ESC-WI-032-exploring-awaiting-ac-signoff-eb28d58c
  comments: 'Dave (in-session, 2026-09-27): ''proceed with A, AC''s approved''. Ruling
    A = the recommended arm (STORABLE predicate; bare numbers refused at the write
    door, parser unchanged for reach). Conductor originates conversationally with
    the WI-268 witness captured before the ACs were shown.'
  ac_hash: dd772c1183de
  intent_hash: 6eab0010f9ce
  ac_item_hashes:
    AC-1: 291f1a902f27
    AC-2: 0f67fabf15c5
    AC-3: 6e8ae465f384
    AC-4: 7bfa6009474f
    AC-5: 975c8d928253
  frozen_acceptance_criteria: '

    Drafted at `exploring` for Dave to agree or tweak, then FROZEN by his signature
    through

    `/review-spec` (`bin/review-spec-helper.py review --wi-id WI-032 --project <path>`)
    — code writes the

    `ac-signoff` fence, never this document''s author. Five criteria; each computes
    its expected value by

    CALLING the two predicates stated at the top of `## Exploration Notes` — never
    from a literal read off

    the same source as the implementation, and never from a restated shape.


    **Read the three rulings first.** These five are drafted to the recommended arm
    of each. Ruling A

    decides whether AC-3''s refused population is C + D + E or class D alone — that
    is the difference

    between closing the minted defect and retiring it. Ruling B decides AC-4 leg (b)
    and AC-3''s `save` arm,

    and AC-5 leg (d) is written to hold either way he rules on the repair. All three
    are a one-line edit

    now and a D4b re-sign after the signature. **None of them is touched by the class-Ø
    fold below**, which

    narrows the refused population to exactly what Dave''s ruling (1) already describes.


    **What the AC red-team round changed (2026-09-26), so a reader can see the delta
    without diffing.** Two

    things, both inside the criterion text rather than in a paragraph a builder has
    to infer from. (i) AC-5

    leg (c)''s readback oracle now states that the key multiset ranges over the PARSEABLE
    values only, with

    the parseable/unparseable split computed by calling `parse` and catching `IdentifierError`,
    and class D''s

    guarantee named as byte-identity instead — the old wording ranged over "the pre-migration
    raw value or

    values" while the same AC mandates a class-D plant, so the oracle RAISED on its
    own fixture rather than

    passing or failing. A total-value count was added alongside the key count so the
    exclusion cannot become

    a licence to delete what it excludes. (ii) The class table gained **class E**
    — parses via the `@lid`

    SUBSTRING, no phone digits, not storable — which is the cell the four-cell table
    was missing and the

    counterexample to its "exhaustive" claim; AC-1''s exhaustiveness is now scoped
    to the enumerated table,

    the corpus and a named boundary-probe list, with the classifier asserted to have
    NO fall-through bucket,

    and every downstream statement of "class D alone" became "class D plus class E".
    The architect''s

    round-2 notes 1 and 2 are absorbed in the same move: the STORABLE predicate''s
    closed-set reading is

    pinned (the bare-suffix licence is deleted, because it changes which cell Thrandell''s
    value falls in),

    and AC-5 leg (d)''s repair is guarded on `phone_digits` being non-empty.


    **What the SECOND AC red-team round and the architect''s third round changed (2026-09-26),
    same

    convention.** Both gates found the same defect independently in text no earlier
    fold had touched: the

    class table filed `""` and `None` under class D, and AC-3 refuses class D at every
    arm — so the door

    refused the model''s own default, the value on 21 of the 22 `whatsapp`-carrying
    fixture notes, and the only

    spelling this package has for CLEARING a field, which made the hand-repair path
    AC-5 leg (e) and Ruling B

    leg 2 promise for the D+E residual unbuildable. Nothing in the drafted suite would
    have caught it, because

    the entity path never hands the gate a literal `""`. The fold: (i) **class Ø**
    enters the table as a cell

    of its own — absence introduces no identifier, is classified BEFORE either predicate
    is called, and is

    ACCEPTED at every arm (F16, which carries the derivation and the citations); (ii)
    class D''s exemplars lose

    `""`/`None` and its definition gains NON-EMPTY; (iii) AC-3''s refusal population
    is scoped to the non-empty

    values that fail STORABLE, and it gains a **CLEARING leg** — clearing the field
    succeeds even when the

    stored value is class C, D or E, which is the residual''s actual repair door —
    and a **CLASS-Ø leg**, that

    class accepted at every arm in every spelling; (iv) AC-1 asserts the classification
    ORDER rather than only

    its totality, because a classifier that asks the predicates first files the whole
    corpus as D; (v)

    AC-4(a)''s empty-as-absence clause is cross-referenced to the CLASS-Ø leg so the
    read and write sides state

    one rule instead of two. Three of

    the architect''s non-blocking notes are folded in the same pass: the `whole_record`
    handle corrected to

    "whole-record projection" with `write_markdown_file(entity=…)` named as the second
    such arm (F11, AC-3,

    `### Examples of done`), AC-5''s readback pinned as a RE-READ from note bytes
    rather than through the

    migrating process''s own cache, and `tests/fixture_vault.py:94` added to the touch
    list.


    **What the THIRD AC red-team round and the architect''s fourth round changed (2026-09-26),
    same

    convention — and this one changes WHERE the discriminating members live, not WHAT
    anything asserts.**

    Both gates, again independently, attacked the fixture-plant plan the previous
    folds had written and

    found it had never been checked against the frozen corpus''s own two contracts.
    (i) `@Thrandell

    Ibberly.md` is the corpus''s SOLE person `roundtrip_representative` and two in-tree
    tests write it

    through the gated whole-record arm asserting NO refusal, so AC-1''s `why:` calling
    its class-C value

    "free" licensed a build that turns both tests red and then "fixes" them by deleting
    the repo''s only

    proof that a whole person field set survives the write door. (ii) The class-A
    and class-D

    `@s.whatsapp.net` literals and the class-E `…@lid.example.com` literal are all
    RED on WI-016''s privacy

    wall if planted in the frozen corpus''s reach — structurally so for class A, since
    STORABLE is

    membership of `{"s.whatsapp.net", "lid"}`, which is itself why the corpus''s one
    JID is spelled

    `@example.com` and therefore class C at all. The fold, all of it inside criterion
    text: the class table

    gains a fourth column saying where each cell''s member can physically live; AC-1
    gains a WHERE CLAUSE

    (A, D, E and every boundary probe are test-module literals; B replaces the representative''s
    value with

    the storable `15555550142@lid`; C moves to a non-representative corpus note keeping

    `447700900789@example.com`) and asserts the representative is storable-clean;
    AC-1''s `why:` retracts

    the "free" claim; AC-3''s required class-E member is respelled `447700900654@lid.example`
    (same cell,

    wall-clean) and its `why:` names the re-expect-the-refusal branch as forbidden;
    AC-5 states that its

    plants land in the MATERIALIZED COPY only; and every planted digit run is now
    an UNUSED member of a

    reserved block, because the old class-A exemplar reused Thrandell''s own phone
    digits and would have

    minted a silent identifier conflict. F17 carries the derivation and the citations;
    rejected items 11

    and 12 record the two branches not taken. Three of the architect''s non-blocking
    notes land in the same

    pass: AC-2''s class-Ø cascade leg restated as a pin on the blank-query guard''s
    POSITION (the behaviour is

    already true at `person.py:606-611`, so the leg now guards the new step being
    inserted BELOW it),

    AC-4(a) naming YAML null as a class-Ø read spelling, and the census''s class-Ø
    row required to be

    counted off note BYTES. **No ruling is touched, and no criterion''s assertion
    changed** — which is the

    test this fold had to pass, since the previous round''s text was already signed
    off on by two gates on

    every other axis.


    **What the FOURTH AC red-team round and the architect''s fifth round changed (2026-09-26)
    — and this one

    finishes the sweep rather than adding another member to it.** Both gates went
    one level past the previous

    fold and found the two places it had stopped short. (i) AC-5 required a plant
    "one note carrying TWO

    JIDs" and, ALONE among that criterion''s required members, pinned no literal for
    it — so the values a test

    author reaches for are the class-A and class-B ones printed two sentences earlier,
    which puts a second

    entity carrying `phone:447700900321` or `jid:15555550142@lid` into the same materialized
    copy and mints

    the silent identifier conflict F17 leg 3 had already found and priced ("it would
    not go red, it would

    just be wrong"), on the one note whose entire purpose is proving a person keeps
    BOTH identifiers.

    (ii) `### Effort` item (iv) and F6 still priced "a census row per newly declared
    class, and its own digest

    follows" as free build-side work, but `docs/vault-shape-census.md` is digest-frozen
    against a literal

    inside WI-016''s SIGNED AC-3 criterion and its row vocabulary is name-corruption
    `branch_id`s with

    live-vault counts and name specimens — so the two cheapest greens were amending
    another item''s signed

    criterion or writing a false `ABSENT/0` row, which is verbatim the route that
    criterion exists to close.

    The fold: AC-5''s desc pins `447700900987@s.whatsapp.net` and `15555550163@lid`
    for the two-JID note (both

    unused reserved-block members, both unclaimed tree-wide); `### Effort` item (iv)
    now states

    affirmatively that the census is NOT touched and F6 and its third amendment drop
    the row clause; and F18

    runs the plant-literal × corpus-contract MATRIX to its end, stating the walls
    that came back clean as

    well as the ones that bit — the skip surface, `LOADABLE` and `RESOLVABLE`; the
    census verdict loop, which

    adds a receiver constraint to AC-1''s WHERE clause (`@Fennwick Drostane.md`);
    where the refusal `pattern`

    is DECLARED, now a clause in AC-3 rather than an inference; the three set-equality
    walls the new test

    module joins, one of which lands as a clause in AC-4(a); and a literal-by-literal
    sweep whose one empty

    row is stated as empty. **No ruling is touched and every criterion''s assertions
    are the same ones** —

    what changed is which literal, which note and which artifact the criteria name.


    **What the FIFTH AC red-team round and the architect''s sixth round changed (2026-09-26)
    — and this one

    ADDS an assertion rather than relocating a literal, which is what makes it different
    from the four folds

    above.** Both gates, independently again, left the fixture-plant class (which
    they agree is closed) and

    attacked F9 — ORIGINAL text no fold had touched — finding that the linter''s report
    surface does not exist.

    `_gate_refusal_pattern` has exactly ONE call site (`scripts/lint_vault.py:450`),
    inside

    `check_structural`''s `stem_name_divergence` arm and behind `stem != stored`,
    where it splices a MARKER

    into that issue''s message and emits no `LintIssue` of its own; `rg -n ''whatsapp''
    scripts/lint_vault.py` is

    0 matches; and WI-029 closed that arm''s live population to ZERO five days before
    this item was minted

    (`docs/stem-divergence-live-baseline.md:191`). So the "reported and left" promise
    that `## Intent`, F13

    leg 3, Ruling B leg 2, AC-5 leg (e) and `### Examples of done` all make had, as
    its only named mechanism,

    AC-3''s closing clause — a sentence that called the consequence FREE, carried
    no `check:` of its own, and

    was therefore satisfied by three different builds, two of them silent. The fold:
    **AC-3''s closing clause

    becomes a REPORT LEG with five assertions** — a new report-only detector arm in
    `check_structural`, its own

    check name, ERROR/`structural`, `auto_fixable` at its `False` default, firing
    on classes C/D/E in BOTH

    stored shapes, silent on class Ø and on storable values, and never reporting through

    `stem_name_divergence`''s `NOT_RENAMEABLE_MARKER` — and **AC-3''s `check:` is
    renamed to name both

    surfaces**, because a write-door test has no reason to assert anything about a
    lint tool unless the

    criterion says so. AC-1''s WHERE clause gains its third receiver constraint, NOT
    STEM-DIVERGENT, which the

    first two do not imply (two marker-bearing divergent notes satisfied the old clause);
    AC-5 leg (e)''s

    "reported" names the detector; `### Effort` carries `scripts/lint_vault.py` as
    a DETECTOR plus a test

    module instead of "pattern routing only", and gains `tests/test_parser.py:248-264`
    as a third reader of the

    representative''s declared value; F9 is RETRACTED in place and F19 carries the
    derivation, the three-build

    argument and the measured cost. **`## Intent` is unchanged** — its promise is
    now true by construction, and

    the alternative of deleting the word "reported" from five places is a promise
    being withdrawn, which is

    Dave''s call and is recorded as rejected item 13 rather than taken here. No ruling
    is touched.


    **What the SIXTH AC red-team round and the architect''s seventh round changed
    (2026-09-26) — one clause, on

    the PACKAGE file this item edits most, which is the artifact class no round had
    opened.** Both gates,

    independently again, left the two closed classes (fixture plants, the report surface)
    and read the walls

    that sweep `obsidian_schemas/repositories/person.py` itself. WI-024 froze that
    module''s comment and

    docstring TEXT at Cut 0, and clause (e1) of `test_strangler_prose_class_is_closed_in_the_package`

    (`tests/test_identity_endgame.py:1008-1019`) asserts on every floor run that every
    Cut-0 `(owner, text)`

    pair of an owner outside the thirteen in `AUTHORIZED_PROSE_OWNERS` (`:359-373`)
    survives verbatim —

    and `PersonRepository.save`, the frame F11 makes this item''s write-back disclosure
    home and F13 makes its

    refusal surface, is such an owner, with 29 recorded lines (`prose_surface_cut0.json:2400-2544`,
    count

    re-run for this fold; both arriving fences say 31). So F11''s accurate citation
    of `person.py:1180-1184` as

    the disclosure''s model invited the one edit that reddens it, and the red resolves
    three ways, all green on

    every `check:` in this set: append (correct and free), authorize `save` (then
    clause (e2) at `:1021-1030`

    demands one of its lines be DELETED), or revert the disclosure (silently withdrawing
    `### Examples of

    done`''s "and it says so"). The fold: **AC-3''s `save` arm gains an APPEND-ONLY
    clause with three conjuncts**

    — the Cut-0 pairs survive, `AUTHORIZED_PROSE_OWNERS` and `prose_surface_cut0.json`
    are untouched (the

    conjunct WI-024''s own clauses cannot supply, since authorize-and-delete satisfies
    both), and the disclosure

    demonstrably LANDED — and AC-3''s `check:` is renamed for the third surface it
    now asserts. `## Approach`

    step (2) states the same constraint as an instruction, `### Effort` carries `person.py`''s
    prose surface and

    `tests/test_identity_endgame.py` as a wall the item JOINS, F11 is amended so its
    citation names a shape

    rather than a paragraph to extend, and rejected items 15 and 16 record the two
    branches not taken. F20

    carries the derivation and sweeps the rest of that suite against every frame this
    item edits, stating the

    five CLEAN results (the Cut-0 resolve golden, the wall-membership rows, `phone_index_iteration_sites`
    with

    its materializing-wrapper constraint, the `ast` single-home, and `tests/test_phone_normalization.py`''s

    `parse` boundary) as well as the one that bit. The architect''s note on `_IDENTIFIER_PRIORITY`
    — a SECOND

    `whatsapp_jid` ordering this document never cited — lands as an amendment to F15:
    different frame, right as

    it stands, not edited. **No ruling is touched and no arm''s behaviour changed**
    — what moves is where a

    disclosure''s TEXT may be written.


    **What the SEVENTH AC red-team round and the architect''s eighth round changed
    (2026-09-27) — and this one is

    the first that made a criterion UNBUILDABLE rather than wrong about a fixture,
    a tool or a frame.** Both

    gates, independently again, left all three closed artifact classes and asked a
    question no round had asked:

    what does the vault LOOK LIKE when the migration has succeeded? AC-3 refuses a
    class-D/E value in both

    shapes and AC-5 leg (b) routes every migration write through that gate, so a shape
    conversion — a write that

    RE-INTRODUCES the field, which the delta rule therefore cannot excuse (`name_gate.py:31-36`)
    — is refused for

    those notes and they are TERMINALLY SCALAR. Yet AC-5 leg (e), `## Approach` step
    (4)''s exit numbers and

    `### Examples of done` all promised "zero notes left in the scalar shape" in the
    same breath as "the D+E

    residual reported and byte-identical", and AC-5''s own mandated class-D and class-E
    plants make that population

    non-zero in the hermetic suite — so no build passed, and all four routes out were
    red (accept → AC-3, bypass →

    leg (b), CLEAR the values → leg (c)''s total-value count and silent erasure, honour
    byte-identity → the old

    leg (e)). The fold: **the exit figure becomes a PARTITION rather than an absolute**
    — `## Exploration Notes`

    declares THE TERMINAL-STATE PARTITION once (scalar-outside-the-residual = 0; MIGRATED;
    the RESIDUAL R,

    reported and byte-identical, its membership per Ruling B''s arm and `|R|` equal
    to the census''s corresponding

    rows) and AC-5 leg (e), `## Approach` step (4), the live bracket''s exit row and
    `### Examples of done` restate

    it; **leg (e) gains the never-clears conjunct**, so the erase-to-convert route
    is red BY INTENT rather than as

    a side effect of a guard added for another reason (rejected item 17); **leg (d)''s
    "either way Dave rules"

    claim is corrected** and asserted over BOTH arms, because under Ruling B''s alternative
    arm class C joins R and

    the number Dave is shown changes; **AC-4 leg (c) is scoped** to writes that succeed
    and introduce the field,

    the same absolute one criterion over. And the class is CLOSED by a declared sweep
    in `## Exploration Notes`:

    every absolute — "zero", "every", "all", "never" — in the five AC descs, `## Intent`,
    `## Approach` and

    `### Examples of done`, with the population it ranges over and the residual it
    excludes, the clean rows stated

    as clean. F21 carries the derivation. **No ruling is reopened and nothing about
    what the migration does to any

    cell moves** — what moves is what this document claims the vault looks like afterwards,
    plus the cost line

    Ruling B''s alternative arm was missing.


    ```criteria

    id: AC-1

    desc: A JID''s digits enter `_phone_index` IF AND ONLY IF `WhatsAppJID.parse`
    gives it a non-empty `phone_digits`, and the discriminating member is PLANTED
    rather than hoped for. The fixture space is a table of raw values the test classifies
    BY CALLING the two predicates of `## Exploration Notes` - `WhatsAppJID.parse`
    and the STORABLE property - yielding the SIX cells of that table: Ø (introduces
    NO identifier - an absent key, `""` or `None` - filed BEFORE either predicate
    is called), plus the five classes of a NON-EMPTY value, A (parses, phone-bearing,
    storable), B (parses, `@lid`, `phone_digits == ""`, storable), C (parses, phone-bearing,
    NOT storable), D (NON-EMPTY and does not parse) and E (parses via the `@lid` SUBSTRING,
    `phone_digits == ""`, NOT storable - the `447700900654@lid.example` shape, whose
    `jid_domain` is `lid.example` and so is not in the closed set), with each cell
    asserted non-empty so a cell that loses its only member is RED rather than vacuously
    green. The classification ORDER is asserted, not merely the classification - an
    emptiness test precedes both predicate calls, proven by the classifier filing
    `""` and `None` as Ø rather than as D, because `WhatsAppJID.parse` raises on them
    through the same two lines it raises on `"n/a"` with (`identifier.py:271-275`,
    no blank branch) and so a classifier that asks the predicates first files the
    corpus''s dominant value as a defect class (F16). The EXHAUSTIVENESS claim is
    stated at the reach it actually has, which is the correction the previous round
    made - the classifier is a TOTAL function with NO fall-through bucket, so a raw
    value matching no declared cell RAISES rather than being silently filed, and it
    is asserted total over (i) the enumerated raw-value table, (ii) every `whatsapp`
    value in the fixture corpus, classified without exception, and (iii) a named boundary-probe
    list, held as literals in the NEW TEST MODULE (never in the frozen corpus - see
    the WHERE clause below), that includes `447700900654@lid.example`, `123@lid.example.com`,
    `notaphone@s.whatsapp.net`, `447700900789@example.com`, the bare `"+44 7739 341679"`,
    and - added with class Ø - `""`, `None`, YAML null, a whitespace-only `"   "`
    and an absent key. It is NOT claimed over every string in the language - that
    was the four-cell table''s false promise, and class E was the counterexample:
    it parsed, carried no phone digits and was not storable, so it belonged to no
    cell while every planted exemplar still went green. Per member the oracle is the
    predicate results themselves, never a restated shape. Classes A and C, the index
    key is exactly `phone_digits` and `get_by_phone(<that number>)` returns this person
    - C is in the phone arm deliberately, because a bare number in the field IS a
    stored phone number and resolution stays liberal (F12), and the test states that
    as the expected answer rather than leaving it to inference. Classes B and E, NO
    key derived from the value''s digits exists in `_phone_index` at all, and the
    falsifying member is planted and named - a lid whose digits are an 11-digit string
    beginning with `1` on a vault where NOBODY holds the corresponding 10-digit number,
    for which `get_by_phone(<the 10-digit form>)` must return None (today it returns
    the lid''s owner, via the permanent fuzzy arm at `person.py:494-496`). That member
    is spelled `15555550142@lid` and its 10-digit counterpart is `5555550142`, which
    is not a free choice of digits: a class-B member sits in the frozen corpus (the
    WHERE clause below), where `reserved_phone_violations` scores every ≥9-digit span
    against the drama block or NANP 555-01xx (`tests/test_fixture_vault.py:308-312`,
    `:342-361`), so an arbitrary 11-digit lid is RED on that wall and the control
    would be discovered unplantable at build time; `15555550142` matches the 555-01xx
    pattern and no member of that block appears anywhere in the corpus today (F17
    leg 3). E is planted with its digits in the ≥ `Phone.MIN_DIGITS` range for the
    same reason, so a build that lost the `@lid` branch and fell through to `normalize_phone`
    produces a phone key and is RED rather than raising for an unrelated reason. Class
    D, the NARROWING arm - there is no right phone for a value the parser refuses,
    so the assertion is the declared marker - no `_phone_index` entry, no exception
    out of the load, and the note still loads. Class Ø, the same NARROWING arm and
    for the same reason, plus one more assertion that distinguishes it from D - no
    `_phone_index` entry, no `jid:` entry, NO identifier of any kind projected from
    the field (the `_project_identifiers` output for that note carries no `whatsapp_jid`
    member at all), and the note loads clean; a build that filed Ø as D would satisfy
    the no-key half and fail nothing else in this criterion, which is why the no-identifier-projected
    half is stated. The two predicates are asserted INDEPENDENT in BOTH directions
    on planted members - `notaphone@s.whatsapp.net` carries a JID domain and is class
    D, and class E parses while carrying a domain that is not one - so a build that
    implemented storability as "parses", or parsing as "has a suffix", or storability
    as "contains `@lid`", is RED. THE WHERE CLAUSE, which is part of the criterion
    and not a build note, because two of these members are inadmissible in the frozen
    corpus and a build that plants them there turns ANOTHER item''s green wall red:
    classes A, D and E - and every literal of the boundary-probe list - live in the
    NEW TEST MODULE''s own temp vault and are never written into `tests/fixtures/vault/`
    or declared in `tests/fixture_vault.py`; class Ø is the corpus''s own 21 `whatsapp:
    ""` notes; class B is the person round-trip representative''s value; class C is
    a non-representative corpus note carrying `447700900789@example.com` - and WHICH
    note that is carries THREE constraints of its own rather than being free choice
    among the 21: it must be a note that LOADS, so never one of the three declared
    person skip specimens (`tests/fixture_vault.py:490-494`), because this criterion''s
    class-C arm asserts `get_by_phone` returns that person and on a skipped note the
    leg is vacuous rather than red; it must declare NO `shape_classes`/`verdict`,
    because the census verdict loop writes every shape-class specimen''s whole declared
    field set through the gated door and asserts the refusal `pattern` equals the
    DECLARED name pattern (`tests/test_fixture_vault.py:856-878`), so a non-storable
    `whatsapp` there makes which refusal fires depend on where the new gate arm sits
    relative to the name arm; and it must NOT BE STEM-DIVERGENT, which is the constraint
    this round adds and which the first two do not imply - `@Perrowin Tessamund Drostane.md`
    and `@Yolvenna Brindlecote Skarnell.md` LOAD and declare `shape_classes=()` with
    no verdict (they carry a `discriminator` instead, `tests/fixture_vault.py:294-306`)
    and so satisfied the WHERE clause as it stood, while being the corpus''s two MARKER-BEARING
    divergent notes, asserted by EQUALITY at `tests/test_stem_name_divergence_detector.py:341-345`
    with their patterns pinned individually at `:346-352`: a non-storable `whatsapp`
    on either routes through `_gate_refusal_pattern` (`scripts/lint_vault.py:450`)
    and makes that other item''s marked-set equality depend on the new gate arm''s
    insertion point, the same question the second constraint removes for census specimens.
    `@Fennwick Drostane.md` is the receiver, one of eight plain loading notes that
    satisfy all three (F18 leg 2, F19 leg 5), and the constraint is stated as well
    as the note because the constraint is what a builder reasons from when the named
    note stops being available. All four divergent corpus notes carry `whatsapp: ""`
    by `_person`''s declared defaults (`tests/fixture_vault.py:85-105`), so they stay
    class Ø under the two corpus edits and that marked set is untouched by the edits
    themselves. The corpus must hold NO class-A and NO class-C member on `@Thrandell
    Ibberly.md`, and that is asserted rather than left to review: the test reads `NOTES`
    and fails if the person `roundtrip_representative`''s declared `whatsapp` is not
    accepted by the STORABLE predicate, and WI-016''s own privacy-wall leg (`tests/test_fixture_vault.py:302-319`,
    reach at `:386-392`) stays green untouched - no exemption added, no pattern widened.
    `_remove_entity_from_indexes` is asserted to be the exact inverse over the same
    table, so a refresh leaves no orphan key.

    why: A lid is an opaque WhatsApp-internal id, so indexing its digits as a telephone
    number invents an identity claim the data never made, and `phones_match`''s US
    arm turns that into a false-positive answer for a number nobody has - the corruption
    shape with a real victim. The class table is derived by CALLING the type rather
    than hand-listed, so widening the storable domain set or adding a third accepted
    parse form later joins the sweep automatically. The plants are required because
    the frozen corpus has zero `@lid`, zero unparseable and zero storable-JID members
    and would green a build that changed nothing. Only class Ø is FREE (21 notes);
    the other five cost something, and the WHERE clause is where they cost it - a
    claim this criterion made wrongly for two rounds and which F17 corrects. Classes
    A, D and E are temp-vault plants because WI-016''s privacy wall makes `@s.whatsapp.net`
    inadmissible anywhere in the corpus''s reach - which is structural for A, since
    STORABLE is membership of `{"s.whatsapp.net", "lid"}` - and because the wall is
    another item''s green invariant, not this item''s to widen (rejected item 11).
    Classes B and C are corpus EDITS: the earlier text called C free because `@Thrandell
    Ibberly.md:7` already carries a class-C value, but that note is the corpus''s
    SOLE person `roundtrip_representative` (`tests/fixture_vault.py:219-233`, `tests/test_fixture_vault.py:689-695`)
    and two tests write it through the gated whole-record arm asserting no refusal
    (`tests/test_writer.py:421`, `tests/test_fixture_vault.py:753`) - so a build implementing
    AC-3 correctly turns both red, and the self-consistent repair is to delete the
    repo''s only proof that a whole person field set survives the write door (rejected
    item 12). Hence B replaces the representative''s value and C moves to a non-representative
    note, which is WI-016''s own deviation-3 fold for the identical collision (`docs/vault-fixtures.md:5938-5943`).
    The digits are pinned rather than illustrative for the same class of reason: the
    old class-A exemplar reused Thrandell''s own phone digits and would have minted
    a silent identifier conflict, and an arbitrary class-B lid is RED on the corpus''s
    phone wall (F17 leg 3). The RECEIVER is named for the same reason one level further
    out - "any note whose `whatsapp` is `""` will do" was true of the bytes and false
    of THREE contracts those notes carry: a skip specimen cannot answer `get_by_phone`
    at all; a census specimen''s declared refusal pattern is asserted by another item''s
    green test, so putting an unstorable value there makes that assertion depend on
    where a builder inserts the new gate arm (F18 leg 2); and a MARKER-BEARING stem-divergent
    note routes its whole record through `_gate_refusal_pattern` and puts the same
    insertion-point question inside a THIRD item''s set equality (F19 leg 5) - which
    is why the clause now states a property and not only a filename, since the receiver
    is a fixture that can be renamed while the contracts cannot. The ORDER assertion
    is new and is the cheapest line in the criterion: absence is not malformation,
    every other part of the library already draws that line before parsing (`person.py:318-320`),
    and a build that draws it after refuses the model''s own default at every dict
    door while passing every other leg here (F16). The independence assertion exists
    because conflating the two predicates is the cheapest wrong build available and
    every other leg of this criterion would still pass. The exhaustiveness wording
    is scoped rather than universal because the universal version was FALSE as written
    - class E is a real input with no cell in the four-cell table - and a criterion
    that claims a totality its predicate table cannot deliver is the same defect one
    level up from the thing it is guarding: the no-fall-through classifier is what
    converts a future sixth shape from a silent mis-file into a failing test, which
    is the strongest honest form of the claim.

    check: test_lid_digits_never_enter_the_phone_index

    kind: test

    ```


    ```criteria

    id: AC-2

    desc: Every PARSEABLE JID form has exactly ONE public resolution door and the
    answer is the person carrying it. Over the same derived SIX-cell table as AC-1,
    a public `get_by_identifier(Identifier)` and the `resolve`/`resolve_all` cascade
    both answer, with the expected entity computed from `WhatsAppJID.parse(v).key`
    plus the fixture''s own note-to-value map. Classes A and C resolve to their note
    through the `phone:` key, unifying with a bare `phones[]` entry for the same number
    exactly as `tests/test_identity_index.py` already pins - class C is asserted to
    RESOLVE even though AC-3 refuses to STORE it, which is the reach-versus-storable
    split made executable, and a build that made resolution strict is RED here. Classes
    B and E resolve to their note through the `jid:<value>` key the index ALREADY
    builds (`person.py:330-331`) - today the same query answers None or, worse, the
    wrong person. E is named alongside B rather than treated as a refusal case, because
    resolution keys on `parse` and E parses: a build that wired the STORABLE predicate
    into the resolver makes E (and C) unresolvable and is RED on this leg, which is
    the same reach-versus-storable split the class-C clause pins from the phone side.
    Classes D and Ø take the NARROWING arm - None, no exception, and no candidate
    above the cascade''s noise floor; for Ø the query is not constructible as a typed
    `Identifier` at all (`WhatsAppJID.parse("")` raises), so the leg is stated over
    the CASCADE with a blank query string and asserts it neither raises nor returns
    a person who merely has an empty `whatsapp:` field - which 21 of 22 fixture notes
    do, making a blank query the one input that could match ~the whole corpus if the
    step compared stored values instead of keys. Stated as a POSITION pin rather than
    as a behaviour claim, because the behaviour is already true and so could not fail
    for the reason it names: `resolve_all` bails out on a blank or whitespace-only
    query BEFORE step 1 runs (`person.py:606-611`, read this round), so what this
    leg actually guards is that the new `whatsapp_jid` step is inserted BELOW that
    guard and never above it - the one thing adding a step can break - and the assertion
    is that the blank-query bail-out still precedes every cascade step including the
    new one. Three guards - the lid answer is asserted to come from the identifier
    index and NOT from a phone lookup (a build that resolved lids by re-normalizing
    digits is RED); the new cascade label is asserted PRESENT in `_RESOLVE_CASCADE_ORDER`
    (`person.py:145`) and ranked ahead of `phone`, proven by a tie between a lid hit
    and a fuzzy phone hit resolving to the lid''s owner (an unranked label sorts last
    at `person.py:190-197`, so omitting it is silently wrong); and `README.md:238`''s
    documented behaviour of looking a phone-bearing JID up through `get_by_phone`
    still holds, so the fix does not silently retract a published API.

    why: The index is already right and nothing public reads it - the gap is a door,
    not data (F5), and a resolution step is the half of the Intent the mint left implicit.
    Asserting WHERE the lid answer comes from is what stops the cheap wrong build
    - re-normalizing a lid''s digits in the resolver would green an answer-shaped
    test while preserving exactly the phone-confusion AC-1 removes. Class C is asserted
    resolvable because the one real risk of adding a storable predicate is that someone
    wires it into the resolver too, which would break lookups that work today (F12),
    and the cascade-label guard is here because it is one line, invisible when wrong,
    and produces a wrong ANSWER rather than an error.

    check: test_whatsapp_jid_resolution_door_over_every_accepted_form

    kind: test

    ```


    ```criteria

    id: AC-3

    desc: Every write arm that can introduce a `whatsapp` value refuses a NON-EMPTY
    value that is not STORABLE - classes C, D and E, so the refused set is defined
    by the STORABLE predicate over the non-empty values, never by "does not parse"
    and never over the absence case - in BOTH shapes, with nothing written. The refused
    population is NON-EMPTY by construction and this is a scoping clause rather than
    a softening one: class Ø (an absent key, `""`, `None`, whitespace-only) introduces
    no identifier, is never judged by either predicate, and is ACCEPTED at every arm,
    which leg (v) pins - `WhatsAppJID.parse` raises on `""` and `None` through the
    same lines it raises on `"n/a"` with (`identifier.py:271-275`), so a door built
    to refuse "everything the parser refuses" refuses the model''s own default (`models.py:94`)
    and the corpus''s dominant value at every dict door (F16). The arm set is DERIVED
    from the tree by the existing WI-021 sweep in `tests/derivations.py` (never hand-listed),
    asserted in scope by EQUALITY, with any arm that cannot introduce the field excluded
    for a stated structural reason, PLUS one arm the derivation cannot supply - `PersonRepository.save`,
    which the WI-021 wall deliberately excludes as a rider (`person.py:1162-1163`)
    and whose gate call runs over a WHOLE-RECORD PROJECTION (`person.py:1190-1191`);
    the derived set already contains the OTHER whole-record-projection arm, the exported
    `write_markdown_file(entity=…)` (`writer.py:229-233`, which `BaseRepository.save`
    delegates into at `base.py:462-465`), and the criterion names it so the two are
    pinned as ONE class of arm rather than as `save` plus an accident - `whole_record`
    is not the discriminant, the payload containing the key is (`name_gate.py:289-294`).
    Per arm, two shapes - a bare scalar `str` (the shape every live caller uses and
    the shape `_shaped` passes through untouched today - F2) and a list containing
    one bad member among good ones. Per arm, three conjuncts - (1) REFUSED with a
    leaf of `LoudFailError` carrying the offending raw value as an ATTRIBUTE and NOT
    in its message, and carrying its own stable `pattern` value distinct from every
    `NameValidator` pattern - DECLARED AS A GATE-LOCAL LITERAL and never as a new
    `NameValidator` Tier-1 branch record, which is a clause about WHERE and not only
    about distinctness: `_refuse` takes a plain `pattern_key: str` (`name_gate.py:142-174`)
    so a gate-local literal needs no record anywhere, while a branch record would
    join WI-016''s AC-3 class floor, which is DERIVED by equality from `{record.branch_id
    for record in TIER1_BRANCHES + COMPANY_TIER1_BRANCHES}` and asserted in both directions
    (`tests/test_fixture_vault.py:830-838`) - reddening another item''s signed criterion
    whose only discharge is a live-vault count, a scan command, verbatim stdout and
    a re-taken census digest, i.e. a conductor pass, for a refusal that is not a name
    judgement at all (F18 leg 4); (2) the target note is byte-identical afterwards,
    and a target that did not exist is not created; (3) a storable value in the same
    payload is accepted and stored in the list shape. `"+44 7739 341679"` is named
    as a REQUIRED class-C member at every arm, because it is the value the item was
    minted for and the value a parse-only door accepts, and `447700900654@lid.example`
    is a REQUIRED class-E member at every arm, because it is the value a door that
    asked "contains `@lid`?" instead of "is the domain in the closed set?" would accept
    - respelled this round from `447700900456@lid.example.com`, which is the SAME
    cell but is RED on WI-016''s privacy wall if it ever lands in the corpus''s reach,
    since `example.com` is matched by EQUALITY and a subdomain of it is not reserved
    (F17 leg 2). Every member named in this criterion is a literal of the new test
    module, not a corpus note; the class-C and class-E values a WRITE arm is handed
    are constructed in the test, and the corpus''s own class-C member (`447700900789@example.com`,
    moved off the round-trip representative per F17 leg 1) is what the `save` arm
    below loads from a note. The `save` arm is pinned in BOTH directions over an entity
    loaded from a note whose STORED value is class C, D or E - (i) `save()` REFUSES
    with that same pattern and the note is byte-identical, and (ii) the value is STILL
    PRESENT on the model and in the note afterwards, never silently emptied, which
    is the assertion an erasing build fails while passing every other leg here. Plus
    the near-miss control - the same note stays writable through a delta arm for a
    write that does not re-introduce the field (the delta-not-record rule, `name_gate.py:31-36`),
    so the remedy is not the disease, and that asymmetry between the whole-record
    arms and the delta arms is asserted rather than assumed. AND THE APPEND-ONLY CLAUSE,
    which is about WHERE the `save` arm''s disclosure may be written rather than about
    what the arm does, and is a criterion rather than a build note because the two
    builds it forbids are green on every other `check:` in this document: `PersonRepository.save`''s
    docstring is a frozen fixture of WI-024 - all 29 of its Cut-0 `(owner, text)`
    pairs (`tests/fixtures/identity_endgame/prose_surface_cut0.json:2400-2544`) belong
    to an owner OUTSIDE `AUTHORIZED_PROSE_OWNERS` (`tests/test_identity_endgame.py:359-373`)
    and clause (e1) (`:1008-1019`) requires each to survive VERBATIM - so this item''s
    write-back disclosure (F11) and refusal disclosure (F13) land as NEW PARAGRAPHS
    and never as edits to `person.py:1169-1184`. Three conjuncts, computed through
    `prose_lines` (`tests/derivations.py:1773`) so the new module names no `ast` of
    its own (F18 leg 5): (1) every Cut-0 pair owned by `PersonRepository.save` is
    present in the final surface - which WI-024''s own (e1) also asserts, restated
    HERE because this is the criterion whose build would break it; (2) `AUTHORIZED_PROSE_OWNERS`
    still has exactly its thirteen declared members and `prose_surface_cut0.json`
    is byte-identical to its pre-build bytes, which is the conjunct (e1) and (e2)
    CANNOT supply - a build that authorizes `save` and then deletes one of its 29
    lines to satisfy (e2) is green on both of WI-024''s clauses and is rejected item
    15; and (3) the final surface for that owner carries at least one line that is
    NOT a Cut-0 member, i.e. the disclosure actually LANDED - the conjunct that fails
    rejected item 16, the build that buys its green by writing no disclosure at all
    while `### Examples of done` promises the refusal surface "says so". THE CLEARING
    LEG, added by the class-Ø fold and the leg that makes the design''s own repair
    promise buildable - over a note whose STORED value is class C, D or E, CLEARING
    the field SUCCEEDS through the delta arms in both of the package''s spellings,
    `update_frontmatter_field(path, "whatsapp", "")` and `update_fields(person, {"whatsapp":
    None})`, with the note afterwards carrying the empty collection and the unstorable
    value GONE because a caller asked for it to go; asserted at every delta arm, not
    just one, because there is no delete or remove affordance anywhere in the writer
    (`writer.py:333-337` sets a value) and so this IS the hand-repair path Ruling
    B leg 2 and AC-5 leg (e) commit to for the D+E residual. THE CLASS-Ø LEG - at
    every arm in the derived set, in every spelling (absent key, `""`, `None`, whitespace-only,
    `[]`) and in both shapes, a write carrying class Ø is ACCEPTED, the note is written,
    and nothing is refused; a build that refuses blank fails here and nowhere else
    in this set, which is exactly why the leg exists. THE REPORT LEG, which this round
    adds and which replaces a clause that called the same consequence FREE and was
    therefore satisfied by silence - `scripts/lint_vault.py` gains a REPORT-ONLY DETECTOR
    ARM in `check_structural` that fires on a note whose STORED `whatsapp` is NON-EMPTY
    and not STORABLE (classes C, D and E), emitting its OWN `LintIssue` under its
    OWN check name, `Severity.ERROR`, category `structural`, with `auto_fixable` left
    at its `False` default (`scripts/lint_vault.py:96`) so the note never enters `apply_fixes`
    and `--fix`''s four-bucket delta contract is untouched while it still repairs
    that note''s OTHER issues. Five conjuncts, every one an assertion rather than
    a consequence: (1) it FIRES on classes C, D and E - over a materialized copy of
    the frozen corpus this check''s issue set is EXACTLY the one non-representative
    note carrying `447700900789@example.com` (AC-1''s WHERE clause), and over the
    new test module''s temp-vault plants it fires on a class-D value and on `447700900654@lid.example`;
    (2) it is SILENT on class Ø in every spelling (absent key, `""`, `None`, YAML
    null, `[]`) and on every STORABLE value, so the person round-trip representative''s
    `15555550142@lid` and the corpus''s 21 `whatsapp: ""` notes produce no issue of
    this check at all - the leg that a detector keyed on "does not parse" fails; (3)
    it judges BOTH stored shapes, a bare scalar `str` and a list with one bad member
    among good ones, because `lint_vault` reads RAW frontmatter and both shapes exist
    on disk throughout the migration window - F2''s inert-arm trap one tool over;
    (4) `auto_fixable is False` on every issue it emits, asserted per issue, and this
    check is NOT a member of `auto_fixable_emitter_checks` - which is also why it
    owes no repair oracle in `tests/test_lint_vault_fix_rules.py:596-624`, whose table
    is scoped to that derived set (`:599`, `:621-624`); and (5) the report NEVER travels
    as `stem_name_divergence`''s `NOT_RENAMEABLE_MARKER` - asserted by that module''s
    own marked-set equality staying green and untouched (`tests/test_stem_name_divergence_detector.py:341-345`,
    which filters on `issue.check` at `:283-289`), because the build that widens the
    existing marker instead is green on everything else in this set while putting
    a false "repair the field" message onto a defect that is a FILENAME (`scripts/lint_vault.py:451-454`)
    and moving live rows against WI-029''s committed "divergent rows the WRITE DOOR
    refuses (b3): 0 of 8" (`docs/stem-divergence-live-baseline.md:124`). This leg
    is covered by THIS criterion''s `check:`, which is named for all THREE surfaces
    it now asserts - the write door, the lint tool and the frozen prose frame - for
    exactly that reason: a write-door test has no reason to assert anything about
    a lint tool, or about another item''s prose fixture, unless the criterion says
    it does.

    why: The Intent''s "every writer refuses it at the boundary" is only true if the
    refusal sits on the surface all writers share - a field type cannot see `update_frontmatter_field(path,
    "whatsapp", "+44 7739 341679")`, which is legal today (F1, `docs/write-door-bypasses.md:3993`)
    - and it is only true of the value that MOTIVATED the item if the door asks the
    storable question, since `WhatsAppJID.parse` accepts that exact string (F12).
    Both shapes are required because an arm copied from `emails`/`phones` is silent
    for scalars and every live value is a scalar. `save` must be named explicitly
    because the derivation that proves no arm routes around the gate excludes it by
    design, and it is an arm where a value the note already stores is re-introduced
    and therefore judged (F13) - the build that ships an erasing reader is green on
    every other criterion in this set; naming `write_markdown_file(entity=…)` alongside
    it is what keeps the disclosure honest, since the refusal surface is "re-serializing
    a whole stored person record", not one method (F11''s correction). The attribute-not-message
    rule is the WI-021 refusal contract (`name_gate.py:142-174`) and the way to honour
    "naming the value" without rendering note bytes in tracebacks (F4). A distinct
    `pattern` is what keeps a bad JID from being reported and routed as a bad name,
    and F18 leg 4 is why it is a GATE-LOCAL literal. The APPEND-ONLY clause is this
    round''s material addition and it is a frozen-AC-text gap rather than a build-runner
    inference: F11''s citation of `person.py:1180-1184` as "the same class of disclosure"
    is ACCURATE and naming it is right, but the paragraph it names is one of 29 lines
    WI-024 froze for an owner it did not authorize, so the natural reading - extend
    the paragraph that already carries this disclosure shape - turns `test_strangler_prose_class_is_closed_in_the_package`
    red with a failure message that names exactly two exits, "name it in the Build
    Log" (authorize the owner) or "revert it", and BOTH are green on every `check:`
    this document names while one destroys prose to buy a green (clause (e2) demands
    an authorized owner LOSE a Cut-0 line, rejected item 15) and the other silently
    withdraws a promise `### Examples of done` makes (rejected item 16). Only the
    third build - append, leave all 29 lines byte-identical - is both correct and
    free, and nothing in this set said so; conjunct (2) is the one that does work
    WI-024''s own wall cannot, because the authorize-and-delete build satisfies (e1)
    and (e2) together. This is the same "leave the other item''s wall alone" instruction
    this document already gives for WI-016''s privacy wall (rejected item 11) and
    for the census digest (F18 leg 1), now for a third frozen artifact - and it is
    the PACKAGE file this item edits most, which is why it was priced as ordinary
    material for seven rounds (F20). The REPORT LEG is this round''s material addition
    and it is a correction to frozen criterion text rather than a build-runner inference,
    because the sentence it replaces was satisfied by SILENCE: `_gate_refusal_pattern`
    has exactly ONE call site (`scripts/lint_vault.py:450`), inside the `stem_name_divergence`
    arm and behind `stem != stored` (`:449`), splicing a MARKER into that issue''s
    message and emitting no issue of its own, while `rg -n ''whatsapp'' scripts/lint_vault.py`
    is 0 matches and WI-029 closed that arm''s live population to ZERO (`docs/stem-divergence-live-baseline.md:191`)
    - so the surface `## Intent`, F13 leg 3, Ruling B leg 2, AC-5 leg (e) and `###
    Examples of done` all promise did not exist, and THREE self-consistent builds
    satisfied every `check:` in this set: leave the tool alone (residual silent),
    widen the existing marker (silent about its own defect and false about the other
    one, rejected item 14), or add a real detector (the only one that keeps the promise,
    and the one nothing priced). A clause phrased as a CONSEQUENCE is what let three
    gate rounds read it as already-true; phrased as five assertions under a check
    named for the surface, it is buildable exactly one way (F19). The detector is
    cheap for a measured reason rather than an assumed one - report-only rules are
    outside the WI-026 oracle table''s derived set and a new check name is invisible
    to the divergence module''s set equalities - which is the accounting F9 skipped
    by pricing the surface off a docstring. The CLEARING and CLASS-Ø legs were the
    class-Ø fold''s material addition and neither is defensive padding: refusing class
    Ø is a SELF-CONSISTENT build that passes every other leg here and every leg of
    AC-4 and AC-5, because the entity path never hands the gate a literal `""` (the
    `[]` default has no member to judge) and no drafted member was blank - so two
    honest implementers reading the earlier text diverged on whether writing `""`
    succeeds, and the losing one bricked the only repair channel the residual population
    has while breaking every producer that clears the field (F16). The legs are stated
    at EVERY delta arm rather than one because the repair is done by whichever door
    the repairer happens to hold. One thing this criterion must NOT be allowed to
    buy, stated here because it is the cheapest way to make the battery green: turning
    the whole-record arms into refusal surfaces collides with the frozen corpus, which
    today stores a class-C value on the SOLE person round-trip representative and
    writes it through that exact arm expecting no refusal (`tests/test_writer.py:421`,
    `tests/test_fixture_vault.py:753`). The resolution is the corpus edit AC-1''s
    WHERE clause pins - the representative takes a storable value, the class-C member
    moves to a non-representative note - and NOT re-expecting a refusal in those two
    tests, which would delete the repo''s only assertion that a whole person field
    set survives the write door (F17 leg 1, rejected item 12).

    check: test_whatsapp_refused_at_every_write_arm_reported_by_lint_vault_and_disclosed_append_only

    kind: test

    ```


    ```criteria

    id: AC-4

    desc: Both stored shapes load, nothing stored is dropped, exactly one shape is
    written, and nothing dataclass-shaped reaches YAML. Four legs, over every cell
    of AC-1''s SIX-cell table. (a) TOLERANT READ - a note carrying `whatsapp: "<value>"`
    and a note carrying `whatsapp: ["<value>"]` both load with NO `SchemaDriftError`
    and present the same field value; a note with an empty value, a note with the
    key absent, and a note carrying a BARE valueless `whatsapp:` key (which YAML loads
    as null) all present the empty collection - that is class Ø on the READ side,
    and the bare-key spelling is named explicitly because it is the one that does
    not work today and the one a build will miss: `_normalize_frontmatter` passes
    `None` through untouched (`parser.py:118-132`) and `whatsapp: str` (`models.py:94`)
    rejects it, so such a note currently raises `SchemaDriftError` and lands on the
    load skip surface (`parser.py:203-208`) - INVISIBLE rather than empty - and where
    this leg names a skip REASON it IMPORTS the constant from `obsidian_schemas/repositories/base.py`
    rather than typing the string, because the legal homes for a `SKIP_REASONS` literal
    are pinned to exactly two files by EQUALITY (`tests/test_fixture_vault.py:1392-1395`)
    and a hand-typed member in the new test module is RED on another item''s wall
    (F18 leg 5) - and the post-migration annotation must coerce null to the empty
    collection or the clearing spelling''s own residue is unreadable, and it is the
    SAME rule AC-3''s CLASS-Ø leg states on the WRITE side, asserted as one rule over
    one cell rather than as a read-side convenience: the leg is stated so that a build
    accepting empty on read while refusing it on write fails HERE too (the round-3
    and red-team-round-2 contradiction, F16), by round-tripping the empty note through
    a gated delta write and back. (b) NO SILENT DROP - for every NON-STORABLE member
    (classes C, D and E) the RAW stored string is still present on the loaded model,
    asserted by equality against the note''s bytes, and the derived typed accessor
    exposes the PARSEABLE members only (so class D appears in the raw field and not
    in the typed view, while classes C and E appear in both - they parse, they are
    merely unstorable, and a build that filtered the typed view on STORABILITY instead
    of on parseability is RED here) - a reader that filtered unparseable values out
    of the stored field fails too, and this is the leg that makes AC-3''s `save` arm
    reachable at all. (c) ONE WRITTEN SHAPE - after any gated write that SUCCEEDS
    and introduces the field the note''s bytes carry the LIST form, re-`yaml.safe_load`
    cleanly, and contain no `!!python/object` tag anywhere; a scalar-carrying note
    written for an unrelated reason is NOT silently rewritten unless the write introduces
    the field (delta rule). The population is named rather than left as "any gated
    write" because the terminal-state partition carves a residual out of it (F21):
    on a note in the residual R - a stored non-empty value the STORABLE predicate
    refuses - there IS no succeeding write that introduces the field, since AC-3 refuses
    it in both shapes, so such a note keeps the SCALAR spelling indefinitely and this
    leg is SILENT about it rather than violated by it. Asserted both ways over a planted
    class-D note: an unrelated delta write leaves its scalar `whatsapp` bytes untouched,
    and a write that re-introduces the field is refused with the bytes unchanged,
    so no build can read "one written shape" as a licence to convert it. (d) ROUND
    TRIP - load, save, load again is a fixed point on the field for every member the
    door accepts, so a second save produces byte-identical frontmatter (the idempotence
    the gate already requires of itself); for members the door refuses, the fixed
    point is AC-3''s refusal with the bytes unchanged.

    why: The vault is shared mutable state, so the reader must accept both shapes
    for as long as any consumer may be running older code - and an un-migrated note
    does not merely look odd, it raises `SchemaDriftError` and lands on the load skip
    surface, invisible to every consumer (F7, F14). Leg (b) is the anti-erasure wall
    and it is new this round - a literal `list[WhatsAppJID]` annotation cannot hold
    a value the type refuses, so the natural build drops it, and since `model_to_frontmatter`
    emits every declared field unconditionally the next `save()` writes the drop back
    to disk (F13). Asserting the raw string survives is what makes that build RED
    before it reaches the live vault. Leg (c) exists because `model_to_frontmatter`
    hands field values straight to `yaml.dump` with the default `Dumper` while the
    reader is `yaml.safe_load` (F8) - a typed object in `model_fields` would write
    notes this package cannot read, and "no `!!python/object` in the bytes" is the
    one assertion that catches it whichever way the implementation goes. Leg (a)''s
    class-Ø round trip is the cross-check the earlier draft lacked: the read side
    already said empty means absence and the write side said empty is refused, and
    because the entity path never constructs a literal `""` for the gate to judge,
    NOTHING in the suite made the two sides meet - which is how a build could satisfy
    both sentences at once and still be wrong. Leg (c)''s population is named this
    round for the same reason one level out: "after ANY gated write the bytes carry
    the LIST form" is an absolute over a population AC-3 carves a residual out of,
    and read literally it says a residual note must end up list-shaped - which AC-3
    forbids and AC-5 leg (e) guarantees against. The clause does not change what any
    build does; it stops the absolute from being the second place a builder finds
    the contradiction F21 removed from the first (the absolutes sweep in `## Exploration
    Notes` is why it was looked for here at all).

    check: test_whatsapp_read_write_shape_and_no_silent_drop

    kind: test

    ```


    ```criteria

    id: AC-5

    desc: The migration is a dry run, then a gated write, then a readback - and it
    proves no identifier moved. Driven in tests against a COPY of the fixture corpus,
    planted with at least one note per NON-Ø cell of AC-1''s table - A, B, C, D and
    E - plus one note carrying TWO JIDs — a phone-bearing one and an `@lid`, and THEIR
    LITERALS ARE PINNED HERE like every other required member of this criterion: `447700900987@s.whatsapp.net`
    (the phone-bearing half, class A) and `15555550163@lid` (the `@lid` half, class
    B), both UNUSED members of the reserved blocks and both distinct from every other
    run this document spends. That pinning is the criterion''s own business and not
    a build note: this was the ONE required member with no literal, and the values
    printed two sentences above are what a test author reaches for — building the
    note out of `447700900321@s.whatsapp.net` and `15555550142@lid` plants a SECOND
    entity in the same materialized copy carrying the class-A plant''s `phone:447700900321`
    and the representative''s `jid:15555550142@lid`, which is verbatim the mechanism
    F17 leg 3 already priced: `_index_identifiers` (`person.py:336-366`) does not
    raise on the collision, nothing in the battery pins the corpus''s conflict set,
    so this criterion''s own readback oracle would be computed against an ambiguous
    index for that note and it would not go red, it would just be wrong. Both new
    runs are wall-clean by the reserved patterns (`447700900987` matches `^447700900\d{3}$`,
    `15555550163` matches `^1?\d{3}55501\d{2}$`, `tests/test_fixture_vault.py:308-312`)
    and unclaimed anywhere in the tree (F18 leg 6). Class Ø needs no plant, the corpus''s
    own 21 `whatsapp: ""` notes being its members and the population the migration
    converts SHAPE-ONLY. The plants land in the MATERIALIZED COPY and never in `tests/fixtures/vault/`
    itself, which is what keeps this leg compatible with the corpus''s own privacy
    wall: `447700900321@s.whatsapp.net` (class A) and `notaphone@s.whatsapp.net` (class
    D) are RED on that wall in the frozen corpus''s reach and admissible only outside
    it (`tests/test_fixture_vault.py:302-319`, reach at `:386-392`; F17 leg 2), so
    a build that "saves a plant" by promoting either into the frozen corpus turns
    another item''s green invariant red. Class E''s plant is `447700900654@lid.example`,
    respelled from `447700900456@lid.example.com` for the same wall and the same cell.
    The class-B and class-C members come from the corpus edits AC-1''s WHERE clause
    pins (`15555550142@lid` on the person round-trip representative, `447700900789@example.com`
    on a non-representative note) and so arrive in the copy for free; every planted
    digit run is an UNUSED member of a reserved block, which is not decoration - the
    earlier class-A exemplar reused Thrandell''s own phone digits and would have keyed
    `phone:447700900123` onto two entities in the copy, minting an identifier conflict
    nothing in the battery pins (F17 leg 3). All of it under the containment wall
    that proves the module drives only a temp vault (`tests/derivations.py:mutating_drive_vault_args`).
    Five legs. (a) DRY RUN - reports counts per cell of AC-1''s table and leaves the
    tree byte-identical, asserted by a digest over the materialized tree before and
    after. (b) WRITE - every write goes through `vault_io` and through the gate (no
    direct `write_text`), asserted structurally rather than by observing the result.
    (c) READBACK ORACLE, stated over KEYS, computed over the PARSEABLE values ONLY,
    and read from the note BYTES - for every note, the MULTISET of `WhatsAppJID.parse(v).key`
    over the post-migration values equals the multiset computed the same way from
    the pre-migration value or values, where BOTH multisets range over exactly those
    values for which `WhatsAppJID.parse` does not raise (classes A, B, C and E). The
    post-migration values come from a RE-READ: the note''s bytes, parsed by a repository
    or a load that did not exist before the write, never through the migrating process''s
    own repository - which holds a process-local cache and re-indexes the entity it
    just wrote (`person.py:257-284` plus the save rider), so an oracle computed through
    it compares the model against itself and is green by construction whatever the
    bytes say. The oracle NEVER calls `.parse` on a value the parser refuses - the
    parseable/unparseable split is itself computed by CALLING `parse` and catching
    `IdentifierError`, never from a hand-kept list, so a class-D value (`"n/a"`, `"ask
    Kate"`) contributes no key to either side instead of making the check RAISE, and
    a class-Ø value contributes none because there is no value. A class-D value''s
    guarantee is BYTE-IDENTITY, not key equality - asserted per note against the pre-migration
    bytes, which is leg (e)''s clause and is where the coverage for D lives. Class
    Ø''s guarantee is the shape conversion and nothing else: `""` becomes `[]`, no
    key on either side, and the note is otherwise byte-stable. Alongside the key multiset,
    TWO counts per note are asserted unchanged: the number of PARSEABLE values (so
    a dropped JID fails) and the TOTAL number of values including the unparseable
    ones (so a run that quietly deleted the class-D junk it was told to leave alone
    fails too, even though that value never had a key). A migration that dropped a
    person''s second JID FAILS this while remaining self-consistent, and a migration
    that invented one fails it too. Keys rather than whole parsed objects, deliberately
    - leg (d) rewrites a raw spelling on purpose and `.jid` legitimately changes while
    `.key` must not. (d) CLASS-C REPAIR, counted as its own class, and guarded on
    PHONE-BEARING - a class-C value is rewritten to its canonical `<digits>@s.whatsapp.net`
    form and ONLY values whose `WhatsAppJID.parse(v).phone_digits` is non-empty are
    ever rewritten, asserted key-preserving by leg (c) over exactly those notes. The
    guard is asserted, not assumed: applying the repair to a phone-less unstorable
    value (class E) would write `"@s.whatsapp.net"`, which `parse` then refuses, so
    a build without the guard converts a leave-alone note into one the readback cannot
    even classify - the test plants a class-E note and asserts it is byte-identical
    after a repair-enabled run. So the population `PersonRepository.save` will refuse
    afterwards is class D plus class E, not class D alone. The count of repairs is
    reported separately from the count of shape-only conversions, and a run invoked
    with repair disabled leaves class C untouched and reports it - which is Ruling
    B''s alternative arm, and the criterion holds under it with ONE stated difference
    rather than unchanged, because the earlier claim that it "holds either way Dave
    rules" was false in a way Dave is entitled to see before he rules: class C is
    unstorable at the gate, so under the alternative arm class C JOINS the residual
    R of leg (e) - the notes stay scalar AND unsaveable through the whole-record arms
    until hand repair - and `|R|` grows by the census''s class-C row, the row this
    document calls the load-bearing one. The test asserts BOTH arms: with repair enabled
    R is the class-D and class-E plants, with repair disabled R is those plus the
    class-C note, and the class-C note is byte-identical under the disabled run. (e)
    COUNTS RECONCILE OVER THE TERMINAL-STATE PARTITION, which is this round''s material
    correction and is a three-part oracle rather than one absolute (F21) - the dry
    run''s per-cell counts, the number of notes the write commits, the repair count
    and the readback''s counts all agree PART FOR PART over the three parts `## Exploration
    Notes` declares: (1) notes left in the SCALAR shape OUTSIDE the residual R - ZERO;
    (2) MIGRATED - every class-Ø, class-A, class-B and repaired class-C note, in the
    list shape; (3) the RESIDUAL R itself - the notes whose stored non-empty value
    the STORABLE predicate refuses and which therefore CANNOT be converted, since
    a conversion re-introduces the field and AC-3 refuses it in both shapes, so each
    one is REPORTED and left BYTE-IDENTICAL and stays scalar BY DESIGN, with R''s
    membership per Ruling B''s arm (class D plus class E under the recommended arm,
    class C plus D plus E under the alternative) and `|R|` equal to the census''s
    corresponding rows. The old wording asserted "zero notes left in the scalar shape"
    full stop, alongside this same leg''s byte-identity guarantee for classes D and
    E, and this criterion''s own mandated class-D and class-E plants make those two
    conjuncts unsatisfiable on the hermetic suite - so the criterion as previously
    drafted could not be written green by any build, and the only exits were amending
    a frozen criterion or silently narrowing the absolute to "the notes the write
    COMMITS" with nothing licensing the narrowing. A disagreement in ANY part is REPORTED
    loudly and the run exits non-zero rather than finishing quietly. And one conjunct
    that keeps the erase-to-convert build red BY INTENT rather than as a side effect
    of the total-value count: THE RUN NEVER CLEARS A VALUE TO MAKE A NOTE CONVERT
    - asserted per plant, since emptying the class-D plant would move it out of R
    into part (2) and reach zero-outside-R trivially by deleting the population this
    item exists to preserve; clearing is a repair somebody ASKS for through a delta
    arm and never something the run does. A class-D or class-E value is never dropped
    and never rewritten - it is reported as needing repair, by the run''s own per-cell
    counts AND, persistently after the run has finished, by the `lint_vault` detector
    AC-3''s REPORT LEG requires, which is a surface this item BUILDS and not one it
    inherits (F19 retracts the F9 claim that the report path came free) - and its
    note''s `whatsapp` bytes are asserted byte-identical. And the residual''s repair
    path is asserted to exist rather than promised: after the run, a class-D note
    is cleared through a delta arm and a class-E note is rewritten through one, both
    SUCCEED (AC-3''s CLEARING and CLASS-Ø legs are what make that true), so "reported
    and left for hand repair" names a door this suite has opened rather than a door
    the write gate refuses (F16).

    why: This is WI-010''s stated un-park criterion (`docs/migration-support.md:20-22`)
    and the first real schema migration in this repo, so the discipline it establishes
    is reused. The readback oracle is the point - a one-off script over ~1,170 notes
    with only a success count cannot distinguish "migrated" from "migrated and lost
    the second JID", which is precisely the data this item exists to start storing.
    It is stated over `.key` and a count because that is what "no identifier moved"
    MEANS to every index and resolver in the package, and because leg (d) changes
    raw spellings by design - an oracle over the parsed dataclass would refuse the
    repair the design depends on, which is the kind of contradiction that is free
    to fix now and costs a re-sign later. The PARSEABLE-ONLY scoping of leg (c) is
    the round''s material correction and it is stated INSIDE the criterion on purpose
    - the earlier wording said the multiset ran over "the pre-migration raw value
    or values" while this same AC mandates a class-D plant, so an author implementing
    the sentence literally called `.parse("n/a")` and the oracle RAISED instead of
    passing or failing: it errored out before either a correct or a wrong build could
    be judged. The correct exclusion was inferable from other paragraphs, which is
    exactly the problem - the frozen criterion is what a builder builds against, and
    every real vault carries some unrepaired junk, so two honest implementers reading
    the old sentence would have diverged on whether the readback ran at all. The TOTAL-count
    arm is what stops the scoping from becoming a licence to delete the values it
    excludes from the key check. Leg (d) is what makes AC-3''s `save` refusal affordable
    rather than a field of unsaveable notes (F13 leg 3), and it is split out as its
    own count because rewriting stored values is a disclosure Dave is ruling on, not
    a silent side effect; its phone-bearing guard exists because "class C is always
    phone-bearing" is only true once class E is carved out of it. Leg (a)''s digest
    and the containment wall exist because a migration that writes during its dry
    run has already spent the only cheap chance to be wrong. Two additions this round.
    The RE-READ clause in leg (c) closes a reading under which the whole oracle is
    vacuous rather than wrong: the repository re-indexes what it just wrote, so a
    readback taken through the migrating process is a comparison of a private replica
    with itself - verify-by-readback means a re-READ or it means nothing, and the
    wrong reading passes silently on a migration that wrote nothing at all. And leg
    (e)''s repair-path assertion is what stops "reported and left for hand repair"
    from being a phrase: the whole class-Ø fold exists because that sentence was,
    under the earlier AC-3 text, a promise the item''s own write door refused (F16),
    so the criterion now exercises the door instead of naming it. One addition in
    the round after that, and it is a containment clause rather than a new assertion:
    the plant list now says the plants land in the MATERIALIZED COPY and names the
    literals, because two of them are RED on WI-016''s privacy wall in the frozen
    corpus''s reach and the shortest way to satisfy "plant a member per cell" is to
    write them into `tests/fixtures/vault/` - which would turn another item''s green
    invariant red as a side effect of a fixture convenience, and which nothing in
    THIS criterion would have caught (F17 leg 2). The unused-digits clause is the
    same shape of trap one level down: `447700900123@s.whatsapp.net` is a reserved-LOOKING
    literal that is already Thrandell''s phone, so it would key one phone identifier
    onto two entities in the copy and nothing in the battery pins the corpus''s conflict
    set - it would not go red, it would just be wrong (F17 leg 3). One addition in
    the round after THAT, and it is the same trap reaching its next member rather
    than a new kind: the two-JID note was the only required plant in this criterion
    carrying no literal of its own, while every other member had a hard-pinned reserved-block
    value two sentences away - so the cheapest way to satisfy "a phone-bearing one
    and an `@lid`" was to reuse the class-A and class-B values already printed, which
    mints exactly the silent conflict the clause above exists to close, on the ONE
    note whose whole purpose is proving a person keeps BOTH identifiers across the
    migration. Pinning `447700900987@s.whatsapp.net` and `15555550163@lid` costs nothing
    - the fixture is free, the digits are unclaimed - and leaving them unstated invited
    the one mistake this criterion had already paid a finding to learn. And the addition
    in the round after THAT is the only one so far that made this criterion UNBUILDABLE
    rather than wrong in a fixture: leg (e) promised "zero notes left in the scalar
    shape" while leg (d) and leg (e) both guarantee the class-D and class-E residual
    is left BYTE-IDENTICAL, and AC-3 refuses a class-D or class-E value at every write
    arm in both shapes with leg (b) asserting structurally that the migration''s own
    writes go through that gate - so those notes cannot be converted, and this criterion''s
    own required plants guarantee the population is non-zero in the hermetic suite.
    All four routes out were red: let the gate accept them (red on AC-3, and it retires
    the item''s own refusal), bypass the gate (red on leg (b)), CLEAR the values so
    the notes convert as class Ø (red on leg (c)''s total-value count, and it is silent
    data loss on the population the item exists to preserve - rejected item 8''s harm
    arriving through the migration instead of through the reader), or honour byte-identity
    and report the residual (the correct build, red on the old leg (e)). So the real
    exits were amending a criterion after Dave''s signature or quietly reinterpreting
    the exit number the live bracket ships against - a clause satisfied by a reader''s
    generosity rather than by construction, the same defect SHAPE F19 closed one artifact
    over, and worse here because the same absolute was also an exit figure a conductor
    has to produce in front of Dave. The partition is the fix and it costs nothing:
    it is still an oracle, still falsifiable, and now backed by the `lint_vault` detector''s
    issue count as an independent second witness to `|R|` - which is what AC-3''s
    REPORT LEG was built to buy. The never-clears conjunct is stated because the erase
    route was caught only as a side effect of a guard added for a different reason,
    and a guard that holds by accident is the thing this document declines everywhere
    else. Leg (d)''s arm-agnostic sentence is corrected in the same move rather than
    left: it told Dave the criterion was indifferent to his repair ruling while the
    alternative arm moves N notes - the census''s class-C row - into a state where
    they are BOTH scalar and unsaveable through the whole-record arms, which is exactly
    the number he should have when he rules.

    check: test_whatsapp_migration_dry_run_then_write_then_readback

    kind: test

    ```


    ### Examples of done


    **Given** someone in the vault has two WhatsApp identities — an old phone-JID
    and the newer `@lid`

    WhatsApp now sends — **when** the sync writes both, **then** the note carries
    both under `whatsapp:`,

    and looking up either one returns that person and only that person. **And** the
    lid is never answered

    back as a phone number: asking for a telephone number nobody in the vault holds
    returns nothing, where

    today it can return whoever happens to own a lid with those digits.


    **Given** anything tries to write a bare telephone number into `whatsapp:` — `"+44
    7739 341679"`,

    the Kim Faura value, through HAL9000''s PATCH door, through the `new-person` skill,
    or through a bare

    `update_frontmatter_field(path, "whatsapp", …)` that skips the repository entirely
    — **then** all three

    refuse, because a phone number is not a JID; the refusal says which value it refused
    (on the error, not

    in a traceback full of note content); and the note on disk is byte-identical afterwards.
    **And** asking

    the vault about that same number still finds the person — refusing to STORE it
    never means refusing to

    LOOK IT UP.


    **Given** a note that already holds a value the door would now refuse — **then**
    nothing erases it.

    The note still loads, the value is still there, the linter names it — under its
    own check, in its own

    line of the report, every time the linter runs and not only if that note''s filename
    happens to be wrong

    too — instead of nobody noticing until a hand repair, and the note stays editable
    for everything else. What refuses until the value is fixed is

    re-serializing the WHOLE stored person record — saving the person through the
    repository, or writing the

    entity through `write_markdown_file` — and it says so. **And** when somebody goes
    to FIX it, that works:

    clearing the field, or writing a properly spelled JID over it, succeeds through
    any of the package''s

    doors — the door judges the value the write is CARRYING, not the value the note
    used to hold, so a repair

    lands everywhere, while re-saving the record with the bad value still in it keeps
    refusing until the value

    is actually fixed. Emptying `whatsapp:` is always allowed, everywhere, because
    an empty field claims no identity and

    there is nothing to validate — which is also why a person note created from the
    template, with

    `whatsapp:` unset, is written without complaint. "Reported and left for hand repair"
    has to name a repair

    somebody can actually do.


    **Given** the live vault on the day the migration runs — **when** it runs the
    first time, **then** it

    PRINTS what it would change and changes nothing; **when** it runs for real, **then**
    every person is

    reachable by exactly the same WhatsApp identities as before — a bare number that
    becomes a properly

    spelled JID still answers to the same number, and nobody loses a second identity
    — and the readback

    reports the vault in three parts and not one number, which is the same TERMINAL-STATE
    PARTITION

    `## Exploration Notes` states and the same one the bracket''s exit row carries,
    said plainly: **zero notes

    left in the old shape apart from the ones it could not touch**; the notes it could
    not touch — the values

    that are already wrong and cannot be spelled as a JID — **still there, byte for
    byte, each one named in the

    linter''s report**, with that count matching what the census said before the run;
    and **zero notes whose

    identities moved**. It is "zero except what it reported" rather than a flat zero
    because a value the door

    refuses cannot be rewritten into the new shape either — writing it back IS the
    refused write — so a run

    that reached a flat zero could only have done it by DELETING those values, which
    is the one thing this item

    exists to prevent, and the migration never does it: emptying a field is a repair
    somebody asks for by hand,

    never something the run decides. (The identities promise ranges over the values
    the package can parse — a

    `"n/a"` was never reachable before the run and is not after; what it gets instead
    is the byte-identity

    guarantee.) **And** if any of those three numbers disagree, the run says so and
    exits non-zero rather than

    finishing quietly.

    '
  frozen_intent: '

    A WhatsApp identifier that is not a WhatsApp JID never reaches a person note —
    that promise is about

    arrival, so it ranges over WRITES from the day this lands and not over the values
    already on disk, which

    the third paragraph below owns and which the migration REPORTS and LEAVES rather
    than converting. "A JID" means it

    carries a WhatsApp JID domain — `@s.whatsapp.net` or `@lid`, where the domain
    is the text after the

    LAST `@`, so `447700900456@lid.example.com` does not qualify and neither does
    `…@example.com` — so a

    bare telephone number typed into

    `whatsapp:` is refused rather than stored, which is precisely the value that caused
    this item. Every

    writer refuses it at the boundary, loudly and naming the value on the error, and
    the one definition

    lives in obsidian-schemas so no consumer carries its own copy.


    And the other half, which the mint left implicit: a JID that IS on a note resolves
    to its person —

    both forms of it, and a person who has two of them keeps both — and it is never
    mistaken for a

    telephone number. Resolution stays LIBERAL where storage is strict: asking with
    a bare number still

    finds the person, because a lookup is not a write.


    And the condition on all of it: nothing already written on a note is silently
    dropped to make the

    above true. A value that is already wrong is reported and left, never erased —
    and it stays FIXABLE, by

    hand, through the ordinary doors: an empty `whatsapp:` field claims no identity,
    so emptying the field is

    always allowed and strictness never lands on the absence of a value.


    *(Sentence one states Ruling A''s recommended arm — the STORABLE predicate. If
    Dave rules the other

    way, this is the sentence that changes, and it is a one-line edit while the ACs
    are still drafts.)*

    '
  note: null
