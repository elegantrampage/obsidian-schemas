schema_version: 1
wi_id: WI-029
spec_path: docs/filename-name-divergence-repair.md
spec_stage_at_review: exploring
reviewed_at: '2026-09-25T11:22:44+01:00'
reviewer: dave
signoff:
  verdict: PROMOTE
  channel: cli
  provenance: verified
  signoff_escalation: ESC-WI-029-exploring-awaiting-ac-signoff-c8fa2aec
  comments: proceed
  ac_hash: 15189b874b27
  intent_hash: 2dd3a4440900
  ac_item_hashes:
    AC-1: c6f4d70405ec
    AC-2: 510393423e26
    AC-3: bb186845ac80
    AC-4: 82e8589871c2
    AC-5: 366c0cca779e
  frozen_acceptance_criteria: '

    Draft — proposed at `exploring`, to be reviewed and signed by Dave through `/review-spec`
    before

    `→ specced`. The spec-writer refines them in place; nothing here is frozen yet.


    ```criteria

    id: AC-1

    desc: A write of an entity the library parsed lands in the note it was parsed
    FROM — through EVERY mutating path in the package and not `save` alone, even when
    two notes share one stored name, and even on a repository that never loaded —
    so no library write can turn one person note into two or land one person''s bytes
    in another person''s note. Over a materialized TEMP copy of the frozen fixture
    corpus (never `tests/fixtures/vault/` itself — `CORPUS_DIGEST`), TWO sets are
    DERIVED rather than hand-listed. The SUBJECT set is the UNION of TWO declared
    predicates over the manifest, neither of them a `shape_classes` label: (i) DIVERGENT
    — every `NoteSpec` with `declared_type="person"` and declared `fields` whose filename
    stem (less the `@`) differs RAW from its declared `name:`, which over today''s
    corpus is exactly four notes (premise 13); and (ii) NAME-SHARING — every person
    `NoteSpec` whose declared `name:` equals another person `NoteSpec`''s, which is
    what brings in the collision third `@Quillam Ostrivane Lumbrek.md` (a note whose
    stem and name AGREE, so predicate (i) cannot reach it) — PLUS the planted members
    the corpus cannot supply. Both predicates are the PERSON ROW of the type-general
    definition stated in `## Exploration Notes` ("Divergence is not a Person-only
    predicate"): DIVERGENT is "the filename this type''s own write rule recomputes
    from the entity''s current fields differs from the file it was parsed from", and
    a COLLIDING GROUP is "every note of a type whose DERIVED filename agrees with
    another''s while they live at different files" — for Person those read as raw
    stem ≠ raw `name:` and as name-sharing, and for Book and Meeting they read against
    `_get_file_name` (`book.py:346-355`, `meeting.py:216-231`). Each subject is bound
    to a FILE and parsed from that path directly, never fetched by name. The PATH
    set is the package''s own mutating write paths, taken from the same derivation
    AC-5 scans rather than hand-listed, restricted per subject to the paths its entity
    type admits: for a Person subject, `save`, `update_fields` and the five mutating
    body-writers (`append_to_timeline`, `append_to_body_section`, `add_to_discuss_item`,
    `update_to_discuss_item`, `remove_to_discuss_item`); for a Book and a Meeting
    subject, that type''s `save` override. THE BOOK AND MEETING SUBJECTS ARE PLANTED
    AS COLLIDING GROUPS AND EVERY SUCH GROUP CONTAINS A DIVERGENT MEMBER: for each
    of the two types, a group of TWO notes in the temp vault whose derived filenames
    are identical — one living AT that derived filename (non-divergent) and one living
    elsewhere (divergent) — which is the `Quillam` shape read off that type''s own
    rule and is the only construction under which a provenance-bound write and today''s
    `_get_file_name`-derived write land in different files. A Book or Meeting subject
    whose deriving fields still agree with its file is NOT admissible as the type''s
    only subject: for such a subject the two mechanisms compute the same path, so
    its cells cannot discriminate a correct seam from one that calls `_resolve_write_target`
    and discards the return (premise 15). For EVERY (subject, path) pair, apply that
    path''s minimal mutation — which must touch NONE of the fields that subject''s
    type derives its filename from (not `name` for Person, not `title`/`author` for
    Book, not `date`/`topics`/`attendees`/`meeting_id` for Meeting), so the cell measures
    provenance against derivation rather than mutation against derivation — and assert:
    (a) the SET of filenames in the vault is unchanged; (b) the changed bytes are
    in the file that subject was parsed from, asserted for EVERY member of a colliding
    group independently and for the DIVERGENT member of the planted Book and Meeting
    groups by name; (c) every other member of that group is byte-identical afterwards
    — which for the planted Book and Meeting groups is the sibling sitting at the
    derived filename, the note today''s override would have written over. ONE cell
    of that matrix has a different declared outcome, reached BY RULE and never by
    a hand-list: for the `save` path, the sweep first applies the DOOR PREDICATE stated
    in `## Exploration Notes` ("Which notes ARE the class") to the subject — `gate_write(fm,
    declared_type=fm.get("type"), whole_record=True)` over that subject''s OWN stored
    frontmatter, the exact call `write_markdown_file` makes on its `entity is not
    None` arm (`writer.py:229-233`, `:252-253`) — and where it raises, the expected
    outcome of that cell is a `NameGateRefusal` carrying the raised `pattern` with
    NO file in the vault changed. The predicate is the DOOR''s and explicitly NOT
    `NameValidator.validate_strict(name)`, whose `allow_phone_sentinel` defaults to
    `False` while the door derives it from the payload (`name_gate.py:355-358`), and
    never the manifest''s `discriminator`. Over today''s corpus that is two subjects
    and two cells (premise 13); every other path for those same subjects asserts (a)(b)(c)
    normally. The corpus cannot discriminate the two spellings of that predicate,
    so the member that does is PLANTED and named here as a required subject — THE
    SENTINEL-EXEMPT SUBJECT: a divergent phone-only stub, file `@447700900123.md`
    carrying `name: "+447700900123"` and a non-empty `phones:` list, whose branch
    is the one `sentinel_exempt` record in the Tier-1 table (`pure_digit`, `name_validation.py:283-294`,
    `:155-156`) and which the door therefore WRITES. Its `save` cell asserts the ordinary
    (a)(b)(c), and asserting that it is NOT refused is the arm that fails an implementation
    built on the bare validator. Then the arms that belong to ONE path, because the
    behaviour on ABSENT provenance differs by path and must — (d) for the PLANTED
    divergent note whose canonical `@{name}.md` is FREE, `save` creates no `@{name}.md`;
    (e) for the PLANTED genuinely-new entity, `save` DOES create `@{name}.md` — the
    discriminator that stops "never write anywhere" from passing; (f) NARROWED ARM
    — for the PLANTED entity round-tripped through `model_dump()`/`model_validate()`,
    provenance is gone by design, so today''s behaviour holds (`@{name}.md` is `save`''s
    target) AND the declared marker is asserted: a WARNING is emitted naming the collision
    when that target already exists; (g) UNLOADED — on a repository constructed `auto_load=False`
    and never `load()`ed, a subject parsed directly still writes to its own file through
    EVERY path in its path set with no vault walk triggered, AND an entity carrying
    no provenance still raises `ValueError` from `update_fields` and from each body-writer
    on that same repository rather than creating a note; (h) NO LEAK — no note written
    anywhere in the sweep gains a frontmatter key holding a path.

    why: This is the half of the Intent that makes recurrence impossible rather than
    merely visible, and it is the defect WI-021 named and parked (`docs/write-door-bypasses.md:486`).
    The PATH set is DERIVED for the same reason the subject set is, and round 2 is
    why: this criterion previously claimed "no library write" while its oracle exercised
    `save()` alone, and eight further paths in the package resolved their target from
    a name (premise 12) — so a build could go green on every arm and ship a criterion
    whose headline was false, the item buildable two ways (WI-144) in the one criterion
    that carries the Intent. Subjects are derived from PREDICATES rather than from
    `shape_classes` because the label is not the class: the shipped detector runs
    over a live vault where nothing is labelled, and a corpus keyed on labels would
    certify an implementation that cannot exist in production. Round 3 is why there
    are TWO predicates and why this rationale no longer claims one does the other''s
    work — the earlier wording said the stem≠name predicate "picks up all three `Quillam`
    notes, including the collision third", and that was false in both directions (premise
    13): the collision third''s stem and name AGREE, so the divergence predicate structurally
    cannot reach it, while the predicate DOES reach two notes this criterion never
    mentioned, the `arrow_connective` and `path_hostile` gate specimens. The collision
    third was already load-bearing for (b) and (c), which assert over "every member
    of a name-sharing group" — a second derivation the criterion used and never defined
    — so it is defined, and the subject set is the union. Each subject is bound to
    a FILE because `repo.get(name)` can only ever return one entity per name, which
    is the ambiguity this criterion exists to refuse. The gate-refused `save` cell
    is stated as a RULE rather than as an exclusion of two named notes, because an
    exclusion list is a hand-sample of the class (WI-185) while the rule is total:
    a name the DOOR refuses is a name that can NEVER fork — `save` raises above the
    lock (`writer.py:229-233`, `:252-253`) before a byte is written — so pinning the
    refusal asserts a true and permanent property and a future corpus member trips
    into the right expectation by itself. Round 4 is why the rule asks the DOOR and
    not `validate_strict`, and why one planted subject exists solely to hold it to
    that: the property is true, the spelling was not. `Tier1Branch` carries `sentinel_exempt`
    and `pure_digit` sets it (`name_validation.py:155-156`, `:283-294`); `gate_write`
    DERIVES `allow_phone_sentinel` from the note''s own payload (`name_gate.py:355-358`)
    while `validate_strict` defaults it `False` "to keep producers honest" (`:594`,
    `:599-601`) — so the bare validator predicts a refusal the package does not perform,
    for a branch the census measures at 2 live person notes (`docs/vault-shape-census.md:148-157`).
    Every divergent note the FROZEN corpus supplies answers identically under both
    spellings, which is precisely the WI-286 case for planting the discriminating
    member rather than trusting the corpus: the SENTINEL-EXEMPT SUBJECT is the only
    cell in the matrix where a right and a wrong-but-self-consistent implementation
    differ, and without it a build keyed on `validate_strict` goes green on every
    arm and ships a detector, an AC-4 consistency rule and a conductor table that
    all forbid the one repair direction that works for that shape. That the OTHER
    eight paths still assert normally for those subjects is not an oversight but the
    code''s own design: `update_fields` gates the delta with `whole_record=False`
    and says verbatim that a note whose stored name is already dirty stays writable
    (`base.py:466-485`), and the five body-writers call `vault_io.write_note` with
    no gate at all — so the refusal is two CELLS out of the fourteen those two subjects
    occupy (seven Person paths each), and excluding them as SUBJECTS would have silently
    dropped the other twelve. (b)+(c) asserted per group member PER PATH is what a
    name-keyed target cannot satisfy: the live corpus contains 2-note collisions (`docs/vault-shape-census.md:222`),
    and for those a name lookup answers with glob order — which on `append_to_timeline`
    means one person''s timeline entry landing in another person''s note, the exact
    harm premise 9 describes and "Examples of done" promises to end. The oracle is
    per-member because today''s `save` produces TWO corruptions from one defect: a
    fork where the canonical filename is free, a silent overwrite of a sibling where
    it is taken (`overwrite=True` is the default). (d), (e), (f) and (g) are PLANTED
    or configured because the frozen corpus cannot discriminate a correct implementation
    from a stubbed or inert one — membership is not correctness (WI-286). (g)''s first
    half is the arm a load-derived battery structurally cannot see and the reason
    the binding is provenance rather than an index; its second half is the arm that
    stops the seam being built as a uniform fallback, since returning a name-derived
    path where those paths refuse today would convert a loud miss into a brand-new
    fork source. (f) is the WI-286 narrowing arm stated honestly: a round-tripped
    entity is indistinguishable from a new one, so the criterion does not promise
    what it cannot deliver — it promises the loss is LOUD, and precondition 2 question
    (4) measures how large that population is in real consumers. (h) makes premise
    11''s unwritability an assertion rather than an assumption, since `extra="allow"`
    would otherwise serialize a mis-declared stamp into every note the library writes.
    Round 5 — the AC red-team''s — is why the Book and Meeting subjects are planted
    as DIVERGENT members of colliding groups rather than as bare subjects, and it
    is the same WI-286 defect this criterion already fixed twice in the Person half,
    found in the half that inherited none of the work: their path set said "that type''s
    `save`" and their subjects were unconstrained, so a subject whose `title`/`author`
    (or `date`/`topics`) still agreed with its file made (b) hold trivially — `_get_file_name(entity)`
    recomputes the file it was parsed from — and made (c) vacuous, because no group
    was defined for those types at all. A `save` override that calls `_resolve_write_target`
    and discards the return passes every such cell while writing exactly where it
    writes today, which is the one-line incentive to leave open the hole round 2 widened
    the seam to close and `## Approach` calls "one line each". The fix is a derivation
    and not a fixture request: divergence is the type''s OWN filename rule recomputed
    against the file it was parsed from (premise 15 reads both rules off the code),
    the Person predicate is its instance, and a colliding group is self-seeding —
    at most one member can live at the shared derived filename, so a planted pair
    always contains a divergent member and supplies both derivations at once. The
    mutation constraint is stated for the same reason the subject is: a mutation that
    touched `title` would move the derived filename WITH the write and the cell would
    pass under either mechanism. What the planted groups then assert is the Book-side
    spelling of premise 9''s harm — today''s override writes the divergent member''s
    bytes over its sibling at the derived filename, a note the caller never named
    — and the census''s "a book-titled file holding a person note" is a live specimen
    of a file whose derived name has drifted from where it lives.

    check: test_no_library_write_can_fork_a_person_note

    kind: test

    ```


    ```criteria

    id: AC-2

    desc: Exactly one door in the package moves a note, it moves the note it was ASKED
    about, a moved note stays reachable, and the next write follows it. (a) THE DOOR
    — a rename entry point on the repository resolves the file it is about to move
    through the SAME provenance function every write path uses, never from the entity''s
    name, routes through `vault_io.move_note`, appends the old stem to `aliases`,
    and leaves `get`, `get_by_email` and the alias route resolving the person under
    BOTH the old and the new name afterwards. (b) REFUSAL — asked to rename onto an
    occupied filename it raises `NoteAlreadyExists` (the leaf, not the root) and BOTH
    files are byte-identical afterwards. (c) SINGLE HOME — `update_fields` with a
    name change calls that door rather than leaving the file behind, so the library
    no longer manufactures divergence (`base.py:454-459` today), and a derived scan
    finds no other site under `obsidian_schemas/**` naming a rename capability. (d)
    SYMLINK — a symlinked source is refused, unmoved, per door 3''s own contract.
    (e) THE WRITE FOLLOWS THE FILE — after a successful rename, a `save()` on the
    SAME in-memory entity lands in the new file and the old stem is NOT recreated;
    after a REFUSED rename (b) or a refused symlink (d), that same `save()` still
    lands in the unmoved original. (f) THE RIGHT NOTE, UNDER COLLISION — for two corpus
    notes sharing one stored `name:`, renaming the entity parsed from note A moves
    A: note B is byte-identical afterwards, its `aliases` did not gain A''s old stem,
    and it is still at its original path. (g) THE RELOAD RE-STAMPS — the entity `update_fields`
    returns carries provenance naming the file that was actually written, so a `save()`
    on the RETURNED entity lands there and not at `@{name}.md`. (h) CASE-ONLY — asked
    to rename a note to a stem that differs from its own only by letter case, on a
    case-insensitive filesystem, the door MOVES it rather than refusing: afterwards
    the directory holds exactly one entry for that note, spelled in the NEW case,
    with the old spelling in `aliases`; and (b)''s `NoteAlreadyExists` applies only
    to a destination that is a DIFFERENT file (`os.path.samefile` false), never to
    the note''s own case-variant. The live baseline (`docs/stem-divergence-live-baseline.md`
    §2, row 3) has exactly one such member, and a door that compares destination STRINGS
    refuses the one repair that works for it.

    why: The mint named `move_note` and it is the right machinery, but it has exactly
    ONE caller in the tree today (`scripts/lint_vault.py:1343`, quarantine) — essentially
    unexercised for this use. (a) and (f) are round 2''s finding turned into an oracle,
    and they are the sharpest arm in the set: `update_fields` picks its file from
    `_file_map[name.lower().strip()]` (`base.py:438`), one path per name in glob order,
    so a door driven from that lookup moves the WRONG member of a live collision pair
    (`docs/vault-shape-census.md:266-267`) — appending A''s old stem to B''s `aliases`
    and leaving A untouched. That is the repair machinery corrupting a note it was
    never asked about, with the correct path sitting unread on the entity one frame
    away, so the door resolving through the seam is asserted rather than assumed.
    (a) is also what the Intent means by "nothing that referenced the old file goes
    dark", stated as a resolution property rather than as the presence of an `aliases`
    key. (c) is the finding that decides whether the Intent is achievable at all:
    one shipped library behaviour deliberately creates the divergence this item promises
    to end, so either it changes or the promise is false. (b) protects the merge case
    the direction table will contain. (e) is the seam''s interaction with the door
    and it is not decoration: under provenance binding, an entity whose stamp still
    names the old path would, on its next save, RECREATE the note the rename just
    removed — a fork manufactured by the repair itself. Both arms are asserted because
    the stamp must be updated exactly when the file moved and not when the move was
    refused, and a stubbed door that re-stamps unconditionally passes the success
    arm alone. (g) is free once the parse stamps — `update_fields` reloads through
    `_load_file` (`base.py:493`) — and is pinned anyway, because a later refactor
    returning an unstamped entity would regress (e) silently. (g) is also the oracle
    for a real SEQUENCING constraint inside (c), named in `## Approach` (2) so the
    build does not discover it as a failing test: calling the door from `update_fields`
    is safe with respect to LOCKING (door 3 sorts both resolved paths into a global
    total order and the locks are reentrant, `vault_io.py:744-750`), but the frame
    holds a `stamp` from `read_note` (`base.py:449`) that it commits against the OLD
    path (`:490`) and then reloads from (`:493-495`, `ValueError` on a `None` reload),
    while `move_note` calls `forget_snapshot(source)` (`vault_io.py:780`) — so the
    order is write, then move, then rebind `file_path` to the door''s return value
    before the reload.

    check: test_a_person_note_is_renamed_only_through_the_one_door_and_stays_reachable

    kind: test

    ```


    ```criteria

    id: AC-3

    desc: `lint_vault` REPORTS filename/name divergence and never repairs it. The
    comparison is RAW on both sides — the filename stem less the leading `@` against
    the stored `name:` exactly as written, with no `clean_person_name` on either half.
    (a) FIRES — over the frozen corpus the check emits one ERROR-severity `stem_name_divergence`
    issue for EACH of the FOUR person notes the definition selects, naming the stem
    and the stored name: `@Quillam Ostrivane.md`, `@Quillam Lumbrek.md`, `@Perrowin
    Tessamund Drostane.md` and `@Yolvenna Brindlecote Skarnell.md` (premise 13). The
    expected set is DERIVED from the manifest by the same predicate AC-1 uses, never
    from `shape_classes`, so it is four because the definition says four and not because
    four notes are listed here. (b) SILENT ELSEWHERE — it emits nothing for the other
    corpus notes, including `@Quillam Ostrivane Lumbrek.md` (stem and name agree),
    the diacritic, hyphenated, postal-address and pure-digit person notes, every non-`@`-prefixed
    note, and — the arm that pins the raw comparison — `@Dave  Marrowyn Fennwick.md`,
    whose stem and stored name BOTH carry the double space and which a `clean_person_name`
    comparison would wrongly report (`tests/fixture_vault.py:246-254` declares `cleaned="Dave
    Marrowyn Fennwick"`). (c) NOT-RENAMEABLE, REPORTED AND MARKED — for a diverged
    note the DOOR PREDICATE refuses (defined in `## Exploration Notes`, "Which notes
    ARE the class": what `gate_write` does with that note''s OWN stored frontmatter,
    NOT `NameValidator.validate_strict(name)`), the check still fires, and the issue
    carries a declared marker naming the raised `pattern`: over the corpus that is
    two of the four (`pattern="calendar_prefix"` for the arrow specimen, `pattern="path_hostile_char"`
    for the slash one). The marker is asserted present on exactly those two and absent
    on the other two — AND absent on a PLANTED divergent phone-only stub (`@447700900123.md`,
    `name: "+447700900123"`, non-empty `phones:`), which the door writes because `pure_digit`
    is the one `sentinel_exempt` branch, so it is reported as an ordinary unmarked
    divergence whose correct repair IS a rename. That planted member is the arm that
    fails a detector built on the bare validator; the corpus alone cannot tell the
    two apart. The marked issue''s message states the POLICY and not a physical claim
    — this divergence is not repaired by renaming the file to the stored name, repair
    the field — since only `path_hostile` makes the rename literally impossible. (d)
    NEVER REPAIRS — the issue carries `auto_fixable=False`, so it never enters `apply_fixes`;
    WI-026''s four-bucket accounting still totals exactly the auto-fixable issue count
    with the new check enabled, and the new issue is counted by the summary line''s
    non-fixable figure. (e) UNREADABLE NOTES — a note `read_vault` cannot decode is
    not reported as divergent (it has no stored name to disagree with), preserving
    WI-026''s `read_error` triage order.

    why: This is the half that goes red "the moment the class recurs" in the live
    vault, on the tool Dave already runs — the hermetic floor structurally cannot
    watch the vault (WI-031 closed the last route deliberately). Both directions are
    asserted because a detector pinned only on its true positives is the WI-235 shape,
    and this corpus makes the negative cheap: it deliberately holds every other corruption
    class, so (b) proves the check discriminates rather than merely fires. (a)''s
    count is FOUR and derived, which is round 3''s finding and the sharpest thing
    in this criterion: it previously pinned "the two notes the manifest declares in
    that class", and a detector written to the DEFINITION emits four (premise 13)
    — so the only implementation that passed both (a) and (b) as written was one keyed
    on `shape_classes`, i.e. one where the manifest LABEL is the defect class, which
    is exactly what AC-1''s derivation forbids and which cannot exist over a live
    vault where nothing is labelled. Two criteria disagreeing about the extension
    of one class over one frozen corpus, resolving toward the wrong implementation,
    is WI-144 in the half of the Intent Dave actually runs; both now read the one
    definition stated in `## Exploration Notes`. The RAW comparison is written into
    the desc rather than left to the spec because `clean_person_name` is one import
    away and a builder may reasonably reach for it, and the corpus contains the note
    that makes the two choices differ — (b)''s whitespace-damaged member, which a
    cleaned comparison reports and a raw one does not. (c) exists because the corpus
    proved the third repair direction is real: a note can be divergent AND not repairable
    by moving the file, because the door refuses to write its stored name at all —
    permanently — so a stem minted from that name is one no write path in the package
    could ever reproduce (and for `path_hostile` specifically, `@{name}.md` is a path
    into another directory, which is why the message states a policy rather than an
    impossibility). That is the row a human most needs to see, so it is reported loudly
    and marked, never suppressed — and the marker is what lets AC-4''s shape check
    refuse a direction table that answers "rename" for such a note. Round 4 is why
    the marker fires on the DOOR predicate and why a planted phone stub is in (c)''s
    negative half: `pure_digit` is `sentinel_exempt` (`name_validation.py:155-156`,
    `:283-294`) and `gate_write` derives `allow_phone_sentinel` from the payload (`name_gate.py:355-358`),
    so a detector asking `validate_strict` would mark a phone-only stub not-renameable
    while the door writes it happily and `@+447700900123.md` is an ordinary filename
    — a FALSE message on Dave''s own report, over a branch the census measures at
    2 live person notes (`docs/vault-shape-census.md:148-157`, `:260-261`), telling
    him the one correct repair is impossible. The frozen corpus cannot catch that:
    its phone specimen declares no `phones` precisely so the branch fires (`tests/fixture_vault.py:283-293`)
    and it is not divergent anyway, so the discriminating member is planted (WI-286).
    (d) is the D-rejection made enforceable: relocation is the highest-blast-radius
    act in the tool and per-note direction is a judgement no auto-fix can make.

    check: test_lint_vault_reports_stem_name_divergence_and_never_repairs_it

    kind: test

    ```


    ```criteria

    id: AC-4

    desc: The live repair is BRACKETED and the bracket is in the tree. `docs/stem-divergence-live-baseline.md`
    is in git HEAD before the criteria are frozen, and carries, in a machine-readable
    shape the check asserts: an ENTRY section with the divergence count and `len(PersonRepository(<vault>).conflicts)`
    from one dated run, a per-note direction table whose every row declares THREE
    things — which side is correct, whether the destination filename is occupied,
    and whether the note is GATE-REFUSED under the DOOR PREDICATE defined in `## Exploration
    Notes` (what `gate_write` does with that note''s OWN stored frontmatter, never
    a bare `NameValidator.validate_strict(name)`), with its raised `pattern` where
    it fires — the incoming-reference count per old stem, and the four booked hand
    repairs. The check reads the committed artifact and asserts its SHAPE and internal
    consistency (every row carries all three columns; every direction row resolves
    to rename / merge / field-repair; NO row resolves to `rename` while declaring
    a gate-refused stored name, and none resolves to `rename` onto a destination occupied
    by a DIFFERENT note — a destination that is the SAME file under a case-insensitive
    filesystem (the artifact''s `same-file` value; a case-only divergence) is not
    occupied for this rule and resolves to `rename` as a case change; the entry counts
    are present and numeric; no absolute path and no note filename leaks the privacy
    wall) — the rule bites only on a row the DOOR refuses, so a row whose stored name
    is a phone sentinel the door writes stays free to resolve to `rename` — it executes
    nothing against any vault. The EXIT half is a declared SHIP CONDITION on this
    item and is stated as such in the document: at `building → done` the conductor
    re-runs the same measurement, appends the attestation to the same artifact, and
    the item is not done until divergence and conflicts both read zero.

    why: WI-026''s scar, applied before it is paid again: a 100% hermetic acceptance
    for a live-corpus repair proves nothing about the corpus it repaired. The precedent
    is `docs/lint-vault-live-baseline.md`. The split is deliberate and is stated rather
    than papered over — a `kind: precondition` fence is HEAD-probed BEFORE the build
    spawn so it cannot carry a post-build act, and a `kind: command` AC would point
    an automated battery at Dave''s live vault on a path he did not authorize per
    run. So the entry half is fence-enforced and AC-read-back, and the exit half''s
    wall is the conductor''s ship door. The third column and its consistency rule
    are round 3''s finding carried into the artifact the conductor commissions: the
    frozen corpus proved that a diverged note''s stored name can itself be one the
    door refuses, which makes "rename to match the name" the wrong direction — so
    a two-column table would come back with rows the repair run cannot perform, and
    re-commissioning it is a second conductor act outside the cage. Asserting the
    rule here is what stops the table from being internally contradictory before anyone
    tries to execute it. Round 4 is why that column cites the DOOR predicate rather
    than `validate_strict`, and the hazard is the same ordering one step in: `pure_digit`
    is the one `sentinel_exempt` branch (`name_validation.py:155-156`, `:283-294`)
    and the census measures it at 2 live person notes (`docs/vault-shape-census.md:148-157`),
    so if either is also among the eight divergent — which is exactly what this artifact
    exists to answer and what no caged reader can settle — a table built on the bare
    validator comes back declaring a refusal for a row whose only correct direction
    is `rename`, and this criterion''s own shape check then REFUSES it. An internally
    contradictory table, commissioned once, outside the cage, with the contradiction
    manufactured by the rule that was supposed to prevent it. One predicate, defined
    once and cited by all four sites, is what makes that unrepresentable. This criterion
    claims only what its check can reach.

    check: test_the_stem_divergence_live_baseline_is_committed_and_shaped

    kind: test

    ```


    ```criteria

    id: AC-5

    desc: The provenance function is the ONLY way a write target is chosen in this
    package — a tenth write path cannot route around it. A derived scan over `obsidian_schemas/**`
    (the WI-031 `tests/derivations.py` shape, not a grep in a docstring) enumerates
    every mutation site — every call to `write_markdown_file`, and every call to a
    `vault_io` door named in `tests/derivations.py`''s own `DOOR_NAMES` (`:47`: `write_note`,
    `create_note`, `move_note`), reusing that frozenset rather than spelling a shorter
    list here — and classifies each enclosing function into exactly one of two legal
    buckets: (a) PATH-TAKING LEAF — the target path is a parameter of that function,
    so its caller chose it (`writer.py`''s four sites today); or (b) SEAM-ROUTED —
    the VALUE `_resolve_write_target` returns REACHES that function''s own write call,
    as DATA FLOW and never as call-presence: the name bound to the call''s return
    must taint the PATH ARGUMENT of the write (the first positional of `write_markdown_file`,
    the path parameter of the door), on the seed → fixpoint → sink shape `tests/derivations.py:361-409`
    already implements for a different seed, reused rather than re-written. Any site
    in neither bucket FAILS the scan, naming the file, the function and the line.
    The scan is pinned BOTH ways with a planted-escape battery. REFUSED, at least
    four: a function that derives a path from a name and writes, in both spellings
    (`self.vault_path / f"@{name}.md"` and a helper returning one); a function that
    CALLS `_resolve_write_target` as a bare expression statement and writes to a separately-derived
    path; the same escape with the return bound and unused (`_ = self._resolve_write_target(entity)`,
    or a name the write never reads); and a function that passes the resolved value
    to the write as some OTHER argument while the path argument is separately derived.
    ACCEPTED, at least five near-misses: a path-taking leaf; a seam-routed writer;
    a read-only function using `get_file_path`; a function naming `_resolve_write_target`
    in a comment or docstring without calling it; and — the one that keeps the shipped
    design legal — a seam-routed writer whose documented fallback arm REBINDS THE
    SAME LOCAL to a name-derived path before writing, which must PASS, because that
    is the fallback asymmetry every one of the nine call sites depends on. The scan''s
    enumeration is also the population AC-1 derives its PATH set from, so the two
    cannot drift apart.

    why: A function every caller MAY use is a polite request, not a boundary (LESSONS
    #1). Round 1 of this item''s review shipped a fold that put provenance in exactly
    the right place and read it at one of nine sites, and round 2 found it only by
    sweeping the package by hand — which is the work this criterion makes permanent
    and automatic. The bucket classification is what makes the scan sound rather than
    a grep: `writer.py`''s leaves legitimately write to a path they were handed, and
    a rule that simply demanded `_resolve_write_target` everywhere would be either
    false there or weakened until it caught nothing. The planted-escape battery is
    WI-235''s shape and WI-031''s own precedent (`VaultArgScan` + `REPOSITORY_CALLEE_SUFFIX`):
    a containment wall that has never been shown to REFUSE anything is an assertion
    about nothing, and the near-misses are what stop the refusal being a substring
    match. Sharing one derivation with AC-1 is deliberate — AC-1 proves the nine paths
    behave, AC-5 proves there are no others, and a tenth path added later joins both
    batteries by construction instead of quietly reopening this finding. The door
    vocabulary is `DOOR_NAMES` and not a two-name list because this item''s OWN rename
    door commits through `move_note`: a wall that does not enumerate the door the
    item ships is a wall with the item''s newest write path outside it, and `create_note`
    is in the same frozenset for free (its only in-package caller today is `writer.py:317`,
    inside a path-taking leaf, so the reuse costs nothing and closes the arm where
    a tenth path built on `create_note` would otherwise pass a scan whose headline
    says it cannot). Round 5 — the AC red-team''s — is why bucket (b) is a DATA-FLOW
    property, and the defect it fixes is this criterion''s own headline being satisfiable
    by a stub: as drafted, (b) asked only whether the function CALLS the seam before
    it writes, so `BookRepository.save` and `MeetingRepository.save` — each two lines
    from `_get_file_name(entity)` to the write (premise 15) — could add one line,
    call `_resolve_write_target`, discard the return, keep today''s derivation, and
    pass a wall whose headline says a write target cannot be chosen any other way.
    That is the smaller edit for a builder optimizing for green, at exactly the two
    sites round 2 widened the seam to reach, so the incentive points at the hole.
    The fold costs a seed and not a scanner: `_taints_a_write` (`tests/derivations.py:361-409`)
    already seeds on a call''s return, propagates to a fixpoint over assignments and
    sinks at a write call''s arguments, and AC-1 already depends on it for a different
    seed — narrowed here to the write''s PATH argument, so "pass the resolved value
    as an unrelated keyword" is refused too. The battery''s fifth ACCEPTED near-miss
    is the load-bearing one and is the reason the rule is not over-tight: the taint
    set is monotone over names, so a fallback arm rebinding the same local stays green,
    and the wall therefore does not quietly demand the removal of the fallback asymmetry
    the seam is built on — a wall that forced a uniform fallback would convert `person.py:1404-1405`''s
    refusals into note creation, which is the defect round 3 corrected.

    check: test_every_write_site_resolves_its_target_through_the_one_seam

    kind: test

    ```


    ### Examples of done


    **Given** one of the eight diverged notes — say a person whose file is `@Firstname.md`
    while the note

    says `name: Firstname Lastname` — **when** HAL9000 resolves that person and saves
    a new phone number

    onto them — **then** the phone lands in `@Firstname.md`, no second note appears,
    and the vault still

    holds exactly one note for that person. (Today: a second note is created and the
    timeline stays

    behind in the first.) **And** where two notes both say `name: Firstname Lastname`,
    a save of the one

    HAL9000 actually read lands in that one — not in whichever of the pair the vault
    walk happened to

    see last.


    **Given** two people whose notes both say `name: Alex Morgan` — **when** Exocortex
    writes a meeting

    timeline entry onto the one it actually read — **then** the entry lands on that
    person''s note, and

    the other Alex Morgan''s note is untouched. (Today: `append_to_timeline` looks
    the file up by name,

    so the entry goes to whichever of the two the vault walk saw last — and the same
    is true of every

    "add a To Discuss item", "append to a body section" and "update these fields"
    call in the library.)


    **Given** Dave renames someone in the vault through the library — **when** the
    name changes — **then**

    the file moves to match the new name, the old filename is kept as an alias, and
    searching for either

    the old or the new name still finds the one note. (Today: the file keeps its old
    name forever and the

    next save forks it.)


    **Given** the repair run has finished and a month has passed — **when** Dave runs

    `scripts/lint_vault.py --vault $VAULT --report` — **then** the divergence count
    reads zero, and if any

    new divergence has appeared the report names it as an ERROR with both halves quoted,
    without

    offering to fix it.

    '
  frozen_intent: '

    A person note''s filename and its stored name agree, everywhere in the live vault,
    and stay that

    way: the forked notes are renamed once through the one sanctioned door (`vault_io.move_note`,

    old stem preserved as an alias so nothing that referenced the old file goes dark),
    and an invariant

    test over the corpus goes red the moment the class recurs — so this is the last
    time it is repaired

    by hand. The booked hand repairs are done in the same pass and the counts that
    found them are

    re-run to zero.


    *(Sharpened at `exploring`, 2026-09-21: "the three forked notes" → "the forked
    notes". The count is

    8 as of the 2026-09-07 census and the Problem section carries the re-verification;
    a frozen number

    in the intent anchor would be falsified by the vault before the build starts.
    Nothing else in this

    section is touched — the mechanism it names is re-derived below rather than rewritten
    here.)*

    '
  note: null
