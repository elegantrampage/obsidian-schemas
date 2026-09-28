schema_version: 1
wi_id: WI-033
spec_path: docs/timeline-entry-relocation.md
spec_stage_at_review: exploring
reviewed_at: '2026-09-28T10:52:08+01:00'
reviewer: dave
signoff:
  verdict: PROMOTE
  channel: conversational
  provenance: verified
  signoff_escalation: ESC-WI-033-exploring-awaiting-ac-signoff-3326b5a4
  comments: 'Dave, in-session 2026-09-28: "approved" — after the four ACs and five
    judgment calls were presented against witness wi-033-ac-witness.json'
  ac_hash: a2bb3913f2c8
  intent_hash: beab28f263a8
  ac_item_hashes:
    AC-1: c6ef8476f351
    AC-2: 6535ee8af9f4
    AC-3: c198dfc5612c
    AC-4: f9d4f2dffcaf
  frozen_acceptance_criteria: '

    **DRAFT — not frozen.** These four are the convergence artifact: what would prove
    this worked. They are

    frozen only when Dave reviews and signs them through `/review-spec`

    (`bin/review-spec-helper.py review --wi-id WI-033 --project <path>`), which writes
    the `ac-signoff`

    fence. The spec-writer refines them in place until then.


    ```criteria

    id: AC-1

    desc: The vault''s timeline-entry vocabulary has ONE definition, it lives in this
    library, and it reproduces HAL9000''s bytes without becoming stricter than them.
    A leaf module `obsidian_schemas/timeline_entry.py` defines `TimelineEntry` (kind,
    text, injectable `when`, optional discriminator), a `render()`, a derived `dedupe_key`,
    `parse_markers()`, an OPEN kind-SLUG RULE as the write door, and a declared `PARITY_KINDS`
    constant that is the parity/sweep universe and GATES NO WRITE (D8). (a) PARITY,
    AND THE CAPTURE''S SAMPLE SET GOVERNS THE SWEEP — not the library''s constant:
    the test parses the `## Parity samples` section of `docs/wi-033-hal9000-timeline-entry-capture.md`
    and, for EVERY sample it declares (one per kind HAL9000 renders, legacy `intro`
    included), constructs a `TimelineEntry` from THAT SAMPLE''S OWN INPUTS — `kind`,
    `text`, `when`, `discriminator` — and asserts `render()` is BYTE-IDENTICAL to
    the sample''s `rendered` block. Inputs and expected output are BOTH read from
    the file; no literal is re-typed into the test, and a sample whose `when` is unpinned
    is not constructible, which is why precondition 1 requires input→output PAIRS
    in a declared machine-readable shape rather than outputs alone. (a2) `PARITY_KINDS`
    EQUALS THE CAPTURED POPULATION, ASSERTED — `PARITY_KINDS` equals the set of kinds
    the capture holds, as a SET EQUALITY: a member with no sample is RED (it would
    be swept by (b) with no captured bytes to sweep against, so the library would
    claim parity it cannot show), and a kind HAL9000 renders that `PARITY_KINDS` omits
    is RED (it would be an on-disk kind absent from every derived sweep''s fixture
    space). This is a claim about the SWEEP SPACE, not a gate: see (a4). (a3) THE
    STALENESS ANCHOR IS MACHINE-CHECKED — the module declares `HAL9000_PARITY_ANCHOR`
    as a 40-hex HEAD and the test asserts it equals the HEAD the capture itself declares,
    so D7''s cutover re-entry condition has a pin to diff against rather than a paragraph.
    (a4) THE DOOR IS OPEN, AND THAT READING IS PLANTED RATHER THAN STATED — a kind
    that satisfies the slug rule and is ABSENT from `PARITY_KINDS` (a novel kind planted
    by this test, e.g. `deal-closed`) CONSTRUCTS, renders, and round-trips through
    (b)''s assertions; no `TimelineEntry` construction, `render()`, `dedupe_key` or
    `parse_markers` call consults `PARITY_KINDS`, and a build that refuses the planted
    kind is RED. This is the discriminating member the corpus cannot supply (P4, WI-286):
    it is the one assertion that tells a closed enum from an open rule, and without
    it both builds are green. (b) ROUND TRIP, DERIVED — the fixture space is `PARITY_KINDS`,
    iterated (never a hand list in the test), plus (a4)''s planted out-of-table kind;
    for each member, `parse_markers(render(entry))` returns exactly one marker whose
    kind, day and discriminator equal the entry''s, and `dedupe_key` equals that marker''s
    key. (c) FORGERY — a text or discriminator containing `-->` or `<!--` is REFUSED
    with a `LoudFailError` leaf named in this document, so no caller can forge a marker
    through the text channel; a discriminator that is empty, whitespace-only, or contains
    the key separator is refused the same way. (c2) REFUSAL PARITY, IN THE DIRECTION
    THAT CAN BREAK A CALLER — the test reads every INPUT→VERDICT pair from the `##
    Validation boundary` section of the same capture and asserts the library is NO
    STRICTER: every `value` the capture records HAL9000 ACCEPTING, the library accepts.
    The sole exception is the guard set (c) names — a `<!--`/`-->` bearing text, kind
    or discriminator, and an empty, whitespace-only or `:`-bearing discriminator —
    and it is asserted as a SET EQUALITY: the set of capture-ACCEPTED inputs the library
    refuses equals exactly that enumerated guard set, so any other over-refusal is
    RED and cannot be waved through as deliberate. The LOOSE direction is asserted
    NOT AT ALL and is out of scope in writing (D8): an input HAL9000 refuses and the
    library accepts cannot break a caller that works today, and the library''s own
    guards are pinned independently by (c). (d) THE DOOR CANNOT DISAGREE WITH ITSELF
    — `PersonRepository.append_to_timeline` accepts a `TimelineEntry` and derives
    BOTH the written entry and the dedupe key from it, so the key and the marker are
    the same string by construction; passing the same entry twice writes once, and
    the second call returns the deliberate dedup `False`. (e) DEDUPE IS ANCHORED —
    the typed path matches the MARKER FORM inside the `## Timeline` span only: a note
    whose `## Notes` section quotes the key verbatim is NOT deduped against, and an
    entry is still appended. (f) PLACEMENT UNCHANGED — the typed path prepends inside
    `## Timeline` exactly as the string path does today (`person.py:1543-1545`), and
    the existing string-and-key signature keeps working unchanged for existing callers.

    why: (a) is the criterion''s whole reason for resting on a precondition: "relocate"
    means byte parity, and 22 marker-bearing legacy entries plus every WI-077 entry
    on disk stop round-tripping if the renderer differs by a space — while a hermetic
    suite comparing the module against a literal a builder typed from the same reading
    of the same code would stay green either way (WI-144). Reading the committed sample
    is what makes the oracle external to the implementation, and it is only executable
    if the sample carries the INPUTS that produced it: `when` is injectable and feeds
    both the heading and the marker''s day slot, so an output with no pinned `when`
    cannot be reproduced at all and the builder would be driven back to the re-typed
    literal this clause forbids — a failure that would otherwise land AFTER the conductor''s
    commit pause, which is the expensive place for it. (a2) exists because the sweep
    and the samples are two different tables owned by two different repos: the earlier
    draft swept "the declared table" (the library''s) against a capture holding HAL9000''s,
    which is unsatisfiable by construction the moment the two differ; the set equality
    makes the difference itself the finding. What (a2) buys is stated precisely, because
    the round-2 review caught the earlier `why` overclaiming it as enforcement: it
    does NOT gate a write and it does not stop anyone using a new kind (D8, (a4)).
    It pins the FIXTURE SPACE — (b) and AC-2 both iterate `PARITY_KINDS`, so if that
    constant drifts from the capture, (b) round-trips a member against the library''s
    own renderer with no captured bytes behind it (self-consistent, proving nothing)
    or a kind that exists on disk is swept by nothing at all. The equality is what
    keeps two derived sweeps'' fixture space equal to the population that actually
    exists, and it makes the library''s byte-parity CLAIM — which kinds it has captured
    bytes for — falsifiable instead of a builder''s list. (a3) is the whole guard
    over D7''s window written as one assertion: this item ships the library half only,
    HAL9000 keeps its own copy until the minted cutover lands, and a pinned anchor
    is what converts "someone should re-run the capture" into a diff with a defined
    left-hand side. (a4) is the round-2 finding closed as an ASSERTION rather than
    as prose, because the two readings of `PARITY_KINDS` are two different write doors
    and a document that merely says which one it means is still buildable both ways:
    a closed enum would make the library STRICTER than the code it relocates (post-cutover,
    a HAL9000 call that writes today raises) and would break example-of-done 3''s
    promise to "any new writer that installs this library", so the open door is the
    ruled answer and the planted out-of-table kind is what makes a closed-enum build
    RED. It is planted rather than sampled for the P4 reason: the corpus has zero
    entries, so nothing on disk can discriminate. (b) derives the fixture space from
    the class''s own declaration (WI-185) rather than sampling kinds, so a kind added
    later joins the sweep automatically — but membership is not correctness (WI-286),
    which is why the per-member oracle is the entry''s own field values rather than
    "a marker came back". (c) is the guard the mint names explicitly and the one place
    a text channel can corrupt a machine channel. (c2) is the other half of what "relocate"
    means, and it was missing while the item''s own standard was already broader than
    render: `### Constraints discovered` says parity with HAL9000 is the meaning of
    the word, but every parity SAMPLE is a valid input, so a capture of samples structurally
    cannot detect a library that refuses something HAL9000 accepts — a divergence
    the hermetic floor never sees and whose first victim, after the cutover, is HAL9000''s
    own caller. Asserting only the ACCEPT direction is deliberate: over-refusal breaks
    working callers and is the failure this item can cause, while under-refusal cannot,
    and validating on HAL9000''s behalf is the cutover item''s business (D8), exactly
    as drift is D7''s. The guard set is an EQUALITY rather than an allowance because
    "the library may be stricter where it means to be" with no enumerated set is an
    exemption a later build widens one case at a time. (d) and (e) are the P2 defect
    closed at the door rather than documented: today `deduplicate_key` and the entry
    string are unrelated arguments and the check is a substring test over the WHOLE
    file including frontmatter, so a caller can dedupe on a key it never writes, and
    a `## Notes` line quoting a key silently suppresses a real entry. (f) is stated
    because prepend-despite-the-name is stored behaviour every reader of the vault
    depends on, and because breaking the existing signature would break four repos
    precondition 3 enumerates.

    check: test_timeline_entry_reproduces_hal9000_render_and_validation_boundary

    kind: test

    ```


    ```criteria

    id: AC-2

    desc: "Who introduced this person" is one typed call that reads the marker slot
    and nothing else. `PersonRepository.introduced_by(person) -> list[IntroRecord]`
    — three fields, each with a pinned value below: `introducer`, `date`, and `source`,
    the VERBATIM MARKER STRING the record was read from (the provenance field; a record
    whose `source` is `None` or reconstructed rather than the bytes on the page fails
    this criterion). Over a PLANTED temp vault — the frozen corpus contains zero timeline
    entries, so nothing here is sampled — the vault holds TWO person notes, and both
    axes the accessor selects on carry a discriminating member. Person A is the kind
    sweep''s note: the sweep iterates `PARITY_KINDS` — which by AC-1(a2) equals the
    capture''s kinds and therefore already contains the legacy kind `intro`, and which
    is a FIXTURE SPACE here and not a gate (D8) — plus AC-1(a4)''s planted out-of-table
    kind, and plants one entry per member on A with a known counterparty and day.
    Person B is the PERSON-axis discriminant: a second person note carrying its OWN
    well-formed `intro-by` entry with a DIFFERENT counterparty and a DIFFERENT day,
    so A''s record and B''s record differ in every field including `source`. The oracle
    is stated HERE: `introduced_by(A)` contains exactly one record for the `intro-by`
    member, carrying that member''s counterparty verbatim from the discriminator slot,
    its day parsed from the day slot, and its `source` equal BYTE-FOR-BYTE to the
    marker substring present in A''S OWN note text — and NO record for any other member,
    and NO record carrying B''s counterparty or B''s day. (a) THE DISCRIMINATING MEMBERS
    ARE PLANTED — `intro-to` and legacy `intro` are both in the sweep precisely because
    an implementation keyed on `"intro" in kind` is wrong-but-self-consistent and
    would return three records where the definition says one; AC-1(a4)''s out-of-table
    kind is in the sweep for the complementary reason — the accessor''s filter is
    the EXACT slug `intro-by` and is not `PARITY_KINDS` membership, so a kind the
    library never captured yields no record and does not raise. (a2) THE PERSON AXIS
    IS DISCRIMINATED, NOT ASSUMED — the accessor''s first argument selects a NOTE,
    and on a fixture holding `intro-by` data for exactly one person a build that globs
    every note under the vault for markers, or that reads a fixed or first note, is
    indistinguishable from a correct one; B is planted for exactly the reason `intro-to`
    is planted on the kind axis. Asserted in BOTH directions and on BOTH people: `introduced_by(A)`
    equals exactly A''s one record — never B''s alone, and never the union of the
    two — and `introduced_by(B)` equals exactly B''s one record, carrying B''s counterparty,
    B''s day and B''s `source` bytes and never A''s. And the read is scoped to that
    person''s OWN note rather than merely filtered: the same `introduced_by(A)` call
    over a temp vault from which B''s note has been removed returns the IDENTICAL
    list, so a build reading the vault at large cannot be green in both runs. The
    accessor loads A''s body through `parse_body_sections` from the note A was parsed
    from and reads only its `## Timeline` (`## Approach`); no clause here is satisfiable
    by a vault-wide scan. (b) PLURALITY AND ORDER — two `intro-by` entries on ONE
    person''s own note return exactly two records, both that person''s, in stored
    document order (newest-first, per `person.py:1543-1545`); with B''s note still
    in the vault, so plurality is that person''s own two and never a third borrowed
    from elsewhere. (c) NARROWED ARM, stated rather than invented — an `intro-by`
    HEADING carrying no marker has no counterparty slot and therefore no right answer;
    it is asserted ABSENT from the result AND asserted PRESENT in AC-4''s `intro_by_without_marker`
    report, which is the declared marker that keeps the promise honest. (d) NEVER
    THE OTHER CHANNELS — the accessor returns nothing for a note whose Timeline prose
    says "Introduced by [[@X]]" with no marker; nothing for a note carrying an `introduced_by`
    frontmatter key; and `[]` for a person with no `## Timeline` section at all, rather
    than raising. All three of these are asserted with B''s well-formed `intro-by`
    note PRESENT in the same vault, so "nothing" means nothing — not somebody else''s
    record. (e) NO SECOND COPY OF THE GRAMMAR, AND THE SCAN COVERS THE PLACE THE SECOND
    COPY WOULD ACTUALLY APPEAR — a derived scan over every `.py` file under `obsidian_schemas/**`
    AND `scripts/**` (the two trees this item writes; `tests/derivations.py:185`''s
    `python_files_under` is the existing derivation) finds the marker grammar DEFINED
    in exactly one file, `obsidian_schemas/timeline_entry.py`. The predicate is a
    definition, not a mention: a pattern or format literal containing the marker delimiters
    `<!--` / `-->`. Every other file that needs the grammar IMPORTS it — named specifically
    because this item puts marker-reading code there, `scripts/lint_vault.py`''s new
    `intro_by_without_marker` detector (AC-4(b)) imports the module''s regex/parser
    and defines no pattern of its own, which the same scan asserts by finding zero
    definitions in that file and an import of `obsidian_schemas.timeline_entry` in
    it. `intro_not_symmetric`''s prose regex (`scripts/lint_vault.py:816`) contains
    no marker delimiter, is untouched by this item (P7), and is therefore outside
    the predicate by construction rather than by exemption. And `introduced_by` is
    exported from the package so a consumer has a typed route.

    why: This is the half of the Intent consumers actually call, and P4 is why every
    word of it is planted: the frozen corpus has ZERO timeline entries (grep `^###
    |<!-- ` over `tests/fixtures/vault/` returns nothing), so the corpus cannot tell
    a correct accessor from a stub that returns `[]` — membership proves nothing here
    because there are no members. (a) is the WI-286 discriminant chosen deliberately:
    `"intro" in kind` is the cheapest wrong implementation, and `intro-to` and `intro`
    are exactly the members that catch it, so both are planted rather than hoped for.
    The out-of-table member is there because D8 makes `PARITY_KINDS` a fixture space
    rather than a gate, and a build that quietly used it as the accessor''s filter
    — or raised on an unlisted kind while reading a note — would otherwise be green
    here. The per-member oracle is a value this document defines (one record for one
    member, none for the rest), not a value re-derived from the implementation, so
    a wrong-but-self-consistent build MISMATCHES instead of agreeing with itself.
    (a2) is that same WI-286 discriminant applied to the axis the accessor''s own
    first argument selects on — the one axis the earlier draft left with a single
    member while discriminating the kind axis three ways. With `intro-by` data on
    exactly ONE note, an implementation that globs every note under the vault for
    markers (or reads a fixed or first note) returns precisely the record the oracle
    expects and goes green on every other clause of this criterion and on example-of-done
    1; shipped against the live vault''s thousand-plus person notes it could answer
    `introduced_by(@Alice)` with @Bob''s introducer, or with the union of everyone''s
    records, and `## Intent`''s "who introduced THIS person" would be answered for
    the wrong person with a green floor. P4 is again why the second member is PLANTED
    rather than found: the frozen corpus has zero entries, so it can supply a second
    person no more than it can supply a second kind. Asserting BOTH directions is
    what rules out the union build and the read-one-fixed-note build in the same pair
    of assertions — a one-directional check would still pass whichever of the two
    happens to order A first — and the B-removed re-run is what makes the promise
    "reads that person''s own note" rather than "filters a vault-wide read by something".
    (c) is the WI-286 narrowing arm taken honestly rather than papered over: the ruling''s
    audit measured 22 of 86 legacy entries carrying a marker, so markerless entries
    are a real population with genuinely no recoverable counterparty — the criterion
    promises a REPORT for them, not a guess, and asserting both halves is what stops
    a build from quietly dropping them. (d)''s first clause is the seam rule (`##
    Exploration Notes`, "Where the structure actually lives") made falsifiable: the
    prose is a lossy copy and reading it would rebuild `lint_vault`''s `intro_not_symmetric`
    regex (`scripts/lint_vault.py:816`) inside the library — the second parser copy
    the mint predicts. (d)''s second clause pins the ruling''s §1 and §2 as one behaviour
    rather than two. The `source` field is pinned rather than dropped because it is
    the record''s provenance: a consumer that disagrees with the accessor (or a linter
    issue that needs to name the offending bytes) has the exact substring to quote,
    and without a pinned value the tuple''s third slot is a field a build could ship
    as `None` with every other clause green. (e) is the boundary promise itself, asserted
    structurally so a later consumer copying the regex out is RED rather than merely
    impolite — and it reaches `scripts/**` because that is where the second copy has
    ALREADY appeared once in this tree (P7''s prose parser) and where this item''s
    own marker-reading detector lands: a scan bounded to `obsidian_schemas/**` would
    let a builder write a second marker regex in `scripts/lint_vault.py` and satisfy
    the criterion and violate the Intent in the same commit. The clause permits an
    IMPORT and forbids a RE-DEFINITION, which is the LESSONS #4 rule ("route to the
    first, do not copy it") stated as a predicate a test can run.

    check: test_introduced_by_reads_only_this_persons_intro_by_markers

    kind: test

    ```


    ```criteria

    id: AC-3

    desc: The retired `introduced_by` key cannot creep back, and the refusal is total
    rather than arm-conditional. (a) REFUSED, AND THE PLACEMENT IS NAMED — `gate_write`
    raises `NameGateRefusal` whenever `introduced_by` is among the fields a write
    INTRODUCES on a payload that reaches the gate''s PERSON BODY, on BOTH values of
    `whole_record`, with `pattern` set to a literal this document names and `refused_value`
    set to the literal key `"introduced_by"` and never to the key''s value. The rule
    lands IN THE PERSON BODY, below the declared-non-person early return at `name_gate.py:373-398`,
    NOT keyed on `declared_type == PERSON_TYPE` — so a `person`-declared write AND
    an UNDECLARED write (a person note missing its `type:`, which P10 measures as
    falling through to that body) are both refused, while `company` and `book` are
    exempted for free by that same return. The undeclared route is asserted explicitly:
    a write introducing `introduced_by` with `declared_type=None` and no `name:` is
    refused. (b) TOTAL OVER THE ARMS — the sweep derives the package''s gated write
    arms rather than hand-listing them (the six `gate_write` call sites: `writer.py:252`,
    `:385`, `:443`, `:494`; `base.py:728`; `person.py:1270`) and drives each one that
    can carry a person frontmatter delta. THE FILTER IS STATED AND ITSELF ASSERTED,
    so the sweep''s shortfall is visible rather than inferred: a site whose fields
    argument is a literal empty mapping AND whose `declared_type` is the literal `None`
    structurally cannot carry a person delta, and the excluded set is asserted to
    EQUAL exactly `writer.py:494` — WI-021''s D7 re-serialization arm, which introduces
    no field and passes `None` deliberately (`writer.py:477-494`) — leaving the other
    five all driven. The sweep asserts the refusal at every driven arm and asserts
    NO FILE CHANGED — including the `save()` path, where the key arrives inside `model_to_frontmatter`''s
    projection because `Person` is `extra="allow"` (`models.py:34-35`, `:49-52`).
    (c) THE POPULATION IS EMPTY, NOT EXEMPTED — `tests/fixtures/vault/@Morvette Harkwell.md`''s
    undeclared key is re-keyed from `introduced_by` to `manager` and `CORPUS_DIGEST`
    is regenerated; the manifest''s `undeclared` declaration moves with it and the
    note keeps its AC-5(b) clause-3 job; a derived scan asserts no note under `tests/fixtures/vault/`
    and no manifest entry names `introduced_by` afterwards, and the corpus''s OWN
    documentation stops offering the key as a legitimate specimen — `docs/vault-fixtures.md:279`
    currently names "a `manager:` or `introduced_by:` key" as the undeclared-key example
    and is updated to name `manager:` alone, so a later reader does not re-plant a
    key the gate now refuses. The live half is the committed count in `docs/wi-033-intro-corpus-baseline.md`,
    read by the test as a premise rather than re-measured. (d) NOTHING ELSE MOVES
    — a person write carrying any other undeclared key (including the newly-swapped
    `manager`) is gated and returned unchanged, so this is a one-key rule and not
    a whitelist of declared fields; a `company`-declared and a `book`-declared payload
    carrying `introduced_by` are NOT refused, because the ruling retires it as a PERSON
    frontmatter key.

    why: Ruling §1 says the gate refuses the key so it cannot creep back, and P6 is
    why that sentence needs a design rather than a line of code: the gate is DECLARE-only
    and reads nothing but its arguments (`name_gate.py:22-29`), so it structurally
    cannot tell "this write introduces the key" from "this projection re-emits a key
    the note already had" — and `model_to_frontmatter` re-emits `model_extra` unconditionally,
    which means a blanket ban makes every carrier permanently unwritable through `save`.
    That is the remedy-is-the-disease outcome the DELTA doctrine was written against
    (`name_gate.py:31-36`). (c) resolves it by measurement rather than by exemption:
    live is already zero after the 2026-09-28 conversion, and the one fixture carrier
    is re-keyed to a key `docs/vault-fixtures.md:279` already names as the same specimen
    class — so the rule stays unconditional, one place, one literal (P8), and no exemption
    arm exists for a later build to widen. The inverted trade is deliberate and argued
    in `## Exploration Notes` D3: a note that regains the key is unwritable until
    the key is deleted, which is correct pressure for a RETIRED KEY (one-line remedy,
    named by AC-4''s detector) where it would be punitive for a dirty NAME (no remedy
    but a rename). (b) is derived rather than hand-listed for the WI-185 reason, and
    it asserts NO FILE CHANGED because a refusal that fires after a partial write
    is worse than no refusal. Its filter is asserted as an equality rather than left
    implicit because a derived sweep that quietly drops arms is indistinguishable
    from an incomplete one: `writer.py:494` passes a literal `{}` with `declared_type=None`
    and can never carry the key, so excluding it is correct — but a reader (and a
    later build that adds a sixth arm) needs the exclusion NAMED, not discovered.
    (a)''s placement is stated rather than left to the build because both placements
    satisfy every other clause of this criterion while differing on one real route:
    P10 measures that `gate_write`''s declared-non-person early return (`name_gate.py:373`)
    is guarded by `is not None` precisely so an UNDECLARED write with no `name:` falls
    through to the person body, so a rule keyed on `declared_type == PERSON_TYPE`
    would leave a person note missing its `type:` free to carry the key — "cannot
    creep back" with a hole in it. Writing the rule into the body closes that route
    and keeps AC-3(d)''s company/book exemption for free, because those return before
    reaching it. (d)''s last clause is the criterion refusing to over-reach: the ruling
    retires a person key, and silently extending the ban to every entity type would
    be an unsigned subtraction. `refused_value` carries the KEY because at this arm
    the value is a person''s name, and keeping note-derived identity out of refusals
    is exactly what `_refuse`''s rule 2 exists for (`name_gate.py:174-186`).

    check: test_the_write_gate_refuses_the_retired_introduced_by_key

    kind: test

    ```


    ```criteria

    id: AC-4

    desc: `lint_vault` makes the legacy and retired shapes VISIBLE and repairs none
    of them. Three new checks, all report-only: (a) `legacy_intro_entry` — WARNING,
    one issue per `[intro]` timeline heading, naming the note and the heading, and
    firing for ALL THREE heading date grammars the ruling''s audit measured (`Month
    D, YYYY`, ISO with time, bare ISO), each planted; (b) `intro_by_without_marker`
    — WARNING, one issue per `intro-by` heading whose entry carries no well-formed
    marker, i.e. exactly the entries AC-2(c) declares invisible to the accessor; "well-formed"
    is the LIBRARY''s grammar, IMPORTED from `obsidian_schemas.timeline_entry` and
    never re-defined in `scripts/lint_vault.py`, which AC-2(e)''s scan asserts; (c)
    `retired_key_introduced_by` — ERROR, one issue per note carrying the retired frontmatter
    key. (d) SILENT ELSEWHERE — over a planted vault holding a well-formed `intro-by`
    entry, a well-formed `intro-to` entry, a person with an empty `## Timeline`, a
    person with no `## Timeline` at all, and a note whose prose merely mentions an
    introduction, none of the three checks fires; and over the frozen fixture corpus
    (which after AC-3(c) carries no `introduced_by` and no timeline entries at all)
    all three are silent, asserted as a SET EQUALITY whose baseline is DERIVED IN
    THE SAME RUN and named here: the set of `(note, rule_id)` pairs `lint_vault` yields
    over `tests/fixtures/vault/` with the three new checks registered equals the set
    it yields with those three rule ids filtered out. The baseline is that second
    computation, not a committed file — `docs/lint-vault-live-baseline.md` (`tests/test_lint_vault_fix_rules.py:113`)
    is the LIVE-vault bracket and is NOT the referent for this clause. A set equality
    rather than a count so a new issue that displaces an old one cannot cancel out.
    (e) NEVER REPAIRS — all three carry `auto_fixable=False`, so none enters `apply_fixes`;
    WI-026''s four-bucket per-issue accounting still totals exactly the auto-fixable
    issue count with the three checks enabled, and each new issue is counted by the
    summary''s non-fixable figure. (f) UNDECODABLE NOTES — a note `read_vault` cannot
    decode is reported by none of the three, preserving WI-026''s `read_error` triage
    order.

    why: Ruling §3 asks for the legacy detector by name; (b) and (c) are the two the
    ruling''s other clauses imply and which would otherwise have no enforcement at
    all — (b) is the declared marker AC-2(c)''s narrowing arm asserts against, so
    without it the accessor''s honest narrowing has nowhere to land, and (c) is what
    makes AC-3''s "cannot creep back" observable on the tool Dave actually runs rather
    than only at a write door nobody watches. This matters because the hermetic floor
    structurally cannot watch the vault (WI-031 clause (v)) — the linter is the only
    standing instrument over live data. (a)''s three grammars are planted rather than
    sampled for the P4 reason (the corpus has no entries) and are named explicitly
    because the audit measured all three live (43 / 38 / 5) and a detector written
    against one of them would be silent on nearly half the corpus while passing a
    single-grammar test. (d) is asserted in both directions because a detector pinned
    only on its true positives is the WI-235 shape; the negative is cheap here and
    the `intro-to` member is the specific one that catches a substring-matching implementation,
    the same wrong-but-self-consistent build AC-2(a) discriminates against. (d)''s
    baseline is named as a derivation inside the same run rather than a committed
    file because this tree has no committed fixture-corpus issue set — the one baseline
    document it does carry is the LIVE bracket — and a clause pointing at a non-existent
    referent is a clause that cannot be run; computing the corpus''s issue set twice,
    with and without the three rule ids, is the referent that actually exists and
    it also survives any future change to the corpus. (b) imports the grammar rather
    than re-stating it because `scripts/lint_vault.py` is precisely where this tree''s
    one existing second copy of a parser already lives (P7), so it is the file most
    likely to grow a third. (e) is ruling §3''s "never auto-fixed" made enforceable
    rather than documented, and it is the right call three times over: rewriting a
    legacy entry is a live migration with its own bracket (A5), synthesizing a missing
    marker would be inventing a counterparty, and deleting a frontmatter value is
    data loss whose direction is a judgement. (f) keeps WI-026''s triage order intact
    — an undecodable note is reported as undecodable, once, and never as four separate
    faults.

    check: test_lint_vault_reports_the_intro_legacy_shapes_and_never_repairs_them

    kind: test

    ```


    ### Examples of done


    **1 — the consumer question, answered by a call instead of a regex — and answered
    about the right person.**

    *Given* a vault where Alice''s note and Bob''s note each carry their own `intro-by`
    entry written by

    HAL9000''s door, with different introducers on different days,

    *when* exocortex asks `PersonRepository.introduced_by(alice)`,

    *then* it gets back ALICE''s introducer and date as typed values — not Bob''s,
    and not both of them — and

    exocortex contains no code that knows what `<!-- … -->` means.


    **2 — the retired key cannot come back.**

    *Given* any writer in the estate that tries to put `introduced_by` on a person
    note — through `save`,

    through `update_fields`, or by setting the attribute on a loaded `Person` and
    saving it,

    *when* the write reaches the library,

    *then* it is refused loudly, nothing is written, and the error names the key.
    If one ever does land by a

    hand-edit in Obsidian, `lint_vault` names that note as an ERROR the next time
    Dave runs it.


    **3 — the vocabulary has a home to move INTO, and the old corpus stays honest.**

    *Given* orchestrator or any new writer that installs this library,

    *when* it builds a `TimelineEntry` and hands it to the door — including one carrying
    a kind NOBODY has used

    before, such as `deal-closed`, which the library accepts on its slug rule without
    anyone editing a list,

    *then* the rendered bytes are identical to what HAL9000 writes today for the kinds
    HAL9000 writes, the dedupe

    key is the marker it actually writes, nothing the library now refuses was writable
    through HAL9000 yesterday,

    and the 86 legacy `[intro]` entries are untouched but listed in `lint_vault`''s
    report —

    visible, not silently rewritten and not silently ignored.


    **4 — the second half is an item, not a hope.**

    *Given* this item is done and HAL9000 still has its own `timeline_entry.py`,

    *when* Dave asks "so is the vocabulary actually in one place yet?",

    *then* the answer is a work item with an id, an owner and a re-entry condition
    — committed as

    `docs/wi-033-hal9000-cutover-followup.md`, naming the HEAD the library is pinned
    against — rather than a

    sentence in a dependencies list that nobody is holding.

    '
  frozen_intent: '

    Every timeline entry any writer puts on a vault note has ONE definition of its
    shape, and it lives in the

    library every writer already installs. "Who introduced this person" is answerable
    by any consumer through

    one typed call, without a stored field and without anyone parsing markdown they
    do not own.

    '
  note: null
