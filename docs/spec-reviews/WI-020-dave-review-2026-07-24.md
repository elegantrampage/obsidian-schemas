schema_version: 1
wi_id: WI-020
spec_path: docs/loud-fail-boundaries.md
spec_stage_at_review: exploring
reviewed_at: '2026-07-24T13:53:06+01:00'
reviewer: dave
signoff:
  verdict: PROMOTE
  channel: cli
  provenance: verified
  signoff_escalation: ESC-WI-020-exploring-awaiting-ac-signoff-94ce85e7
  comments: null
  ac_hash: dfa3ceddda0b
  intent_hash: eaa4e881448e
  ac_item_hashes:
    AC-1: 0bb25d0237e8
    AC-2: c0bc96ee6874
    AC-3: c4494a7ec5a0
    AC-4: 6257494d1c78
    AC-5: c9af928ccc69
    AC-6: 3e57f0a2efee
    AC-7: 7cc31153b6f2
  frozen_acceptance_criteria: '

    Draft acceptance criteria — a convergence artifact ("what would prove this worked?"),
    to be reviewed and frozen with Dave via `/review-spec` before origination (the
    `ac-signoff` fence is written by code after his review, never here), then refined
    in place by the spec-writer. Each `check:` name is a proposed test the build will
    implement.


    **Specification altitude (Dave-ruled 2026-07-24, a one-off scope declaration for
    THIS document — it amends no role or bar and is recorded as a specimen for the
    WI-187 altitude session):** this AC set specifies three things — (a) observable
    behaviour at the package''s boundaries, (b) the derivation obligations that keep
    its sweeps live rather than frozen, and (c) the composition of those derivations:
    shared outputs (round 17), one shared implementation (round 19), and the partition
    they must jointly satisfy. Concerns BELOW that line — how the shared scan module
    is factored or named, how it is itself unit-tested, and any further property of
    the harness''s internal architecture — are the declared jurisdiction of the pipeline''s
    existing later gates (build-exit review for harness code quality; intent-check
    for desc-vs-test fidelity), not of this AC set or its red-team pass. A finding
    at that altitude is real but routed: it belongs to those gates'' reviews, not
    to another fold here.


    **Revised 2026-07-24** in response to the decorrelated red-team recorded below.
    Three structural changes: each AC that quantifies over a class now **derives**
    its sweep from the code rather than naming a list (which turned up two missed
    class members — see the red-team response in Exploration Notes); the malformed-must-raise
    half is now paired with the **absent-must-still-succeed** half so the fix cannot
    over-shoot; and AC-5''s cross-repo consumer audit is **removed** — no check available
    in this repo can verify it (see Non-goals) — replaced by a backward-compat property
    that is locally provable.


    **Revised again 2026-07-24 (round 2)** after the re-verify pass. Both remaining
    gaps were an AC deriving one half of its property and hand-writing the other.
    AC-1''s absent-must-succeed half now quantifies over the **same** derived four-path
    list as its raise half; AC-5 now carries an explicit **second derivation predicate**
    (the frontmatter-fence split) instead of naming one function''s branches — which
    turned up a fifth site (`_get_body_content`) that no prior pass had seen. Rule
    for anything added later: **an AC names its predicate, never its sites.**


    **Revised again 2026-07-24 (round 3)** after the second re-verify. One gap, and
    it is the round-2 rule missing its other half: AC-3 derived its *repository* sweep
    from the code but hand-picked its *fixture space*, so `BookRepository`''s catch-all
    `"*.md"` glob (book.py:49-51) would have made every malformed note in the vault
    a "skipped book". Re-deriving the fixture space per repository from its own `file_pattern`
    also exposed a larger case on a **healthy** vault: `PersonRepository` and `CompanyRepository`
    share the `@*.md` glob and `base._load_file` checks no `type` at all, so post-fix
    every company note would report as a skipped person. AC-3 now derives its fixture
    vault per repository, requires it to be heterogeneous, and asserts the skip surface
    in both directions. Extended rule: **an AC names its predicate, never its sites
    — and derives its fixture space, never samples it.**


    **Revised again 2026-07-24 (round 4)** after the third re-verify. One gap, inside
    AC-3''s own fixture list: "a known type fails Pydantic validation" names two mechanically
    identical cases — a foreign `type: company` note under `PersonRepository`, and
    an owned `type: person` note that fails on another field — with **opposite** required
    answers, and the doc gave a worked example only for the one that must be *excluded*.
    So the owned-but-drifted note that is C5''s actual duplicate-creation driver was
    never pinned as present, and the natural implementation ("if the model failed
    to build, it isn''t mine") would drop it while every AC read green. AC-3 now requires
    **three distinct fixture files**, forbids (b) and (c) from being the same file,
    and states the mechanism-forcing property this turns on: **ownership is decided
    on the raw `type` value, never on whether `model_validate` succeeded.** Rule added:
    **two fixtures that share a code path but require opposite answers must be two
    files, asserted in one test.**


    **Revised again 2026-07-24 (round 5)** after the fourth re-verify. One gap, and
    it is the round-4 rule one level out: AC-3 derived its fixture space per repository
    but derived its *repository sweep* from the three `_load_file` **overrides**,
    which collapses `PersonRepository` and `CompanyRepository` — two classes sharing
    one inherited implementation and one `@*.md` glob — into a single sweep entry.
    Every fixture, direction and Example of done in the doc was written from `PersonRepository`''s
    side, so a test parametrized over `{PersonRepository, MeetingRepository, BookRepository}`
    read as satisfying the AC while the *larger* half of round 3''s healthy-vault
    exposure — "every person note becomes a skipped company" — shipped unverified,
    and a comparison hardcoded to one type literal instead of `self.type_name` would
    pass it. AC-3 now sweeps the **four concrete `BaseRepository` subclasses**, requires
    `PersonRepository` and `CompanyRepository` to be **independently instantiated**
    against the same shared vault and asserted in all three directions each, derives
    each class''s own (b)/(c) fixtures from its own `type_name` and model fields,
    and a seventh Example of done pins the company side in Dave''s terms. Rule added:
    **when two classes share one code path, the sweep counts the classes, not the
    path — a shared implementation is verified once per class that inherits it.**


    **Revised again 2026-07-24 (round 6)** after the fifth re-verify. One gap, and
    it is the round-5 rule left half-applied: AC-3 named four repository classes but
    worked out fixtures for two — `MeetingRepository` appeared only in the enumeration
    and in a counter-example, `BookRepository` only in its exclusion clause. The direction
    never reached was fixture (b), the owned-but-drifted note, which is the one that
    carries this item''s *new* signal into each class''s *own* `_load_file` — and
    `meeting.py`/`book.py` are structurally unlike `base.py` (both prefilter on the
    raw `type` at meeting.py:72-75 / book.py:67-70, so their foreign-type direction
    is already sound, while a `type: meeting` + `attendees: "not-a-list"` or `type:
    book` + `tags: book` note passes that prefilter and fails only inside `parse_markdown_file`,
    landing in their own untested `except`). Since `BaseRepository.load()` (base.py:157-165)
    wraps `_load_file` in no `try`/`except` at all, a narrowed catch that misses the
    new error there aborts the entire batch — the HAL9000-startup regression, reached
    by exactly the narrowing AC-6 asks for elsewhere. AC-3 is now the complete derived
    **4×3 matrix**: one fixture set per class, each derived from that class''s own
    `type_name`, model fields and `_load_file` structure, with a NO-ABORT assertion
    on all twelve cells; and it records that the matrix is **not uniform** — fixture
    (a) is must-be-listed for three classes and must-NOT-be-listed for `BookRepository`,
    while fixture (b) is must-be-listed for all four. Rules added: **when a sweep''s
    members do not all have the same answer, the AC writes each member out — a quantifier
    with one shared expectation table silently asserts uniformity nobody checked**;
    and **prove the insulation, not only what it produces.**


    **Revised again 2026-07-24 (round 7)** after the sixth re-verify — the audit-fold
    applied to AC-5''s own derivation, per the same Dave ruling that produced round
    6''s. The finding: AC-5 swept by TWO predicates, and `append_to_timeline` collapses
    a third — marker-absent (person.py:1482-1484) and a structurally-dead split guard
    (1491-1492) return the same `False` as the legitimate dedup no-op, on notes whose
    own template guarantees `## Timeline` exists (body_sections.py:305-306), so a
    caller''s timeline entry is silently dropped. Instead of adding the found predicate
    alone, the falsy-site classification was re-derived from scratch over the whole
    write-path surface at source, which found two more gaps the finding did not name:
    writer.py''s existence pre-checks (243, 282) return `False` for the file-missing
    condition every sibling writer in the package raises for, and the no-op half''s
    citation list was wrong in both directions (update_to_discuss_item''s section-absent
    site 1746-1747 mislabeled as "item text not found"; remove_to_discuss_item''s
    1813-1814 missing entirely). AC-5 is now a FOUR-predicate derivation with the
    no-op half derived by predicate too, split on whether a falsy return drops a caller''s
    payload (failure) or answers "the thing you named is not here" (no-op). Rule added:
    **when a round shows a derivation''s predicate list incomplete, re-run the whole
    derivation at source and fold once — the found member is a symptom, and patching
    it alone is the treadmill.**


    **Revised again 2026-07-24 (round 8)** after re-verifying the round-7 fold at
    source. Every round-7 claim holds live (`append_to_timeline`''s four falsy returns
    including the structurally-dead split guard, the person template''s guaranteed
    `## Timeline`, writer.py''s existence pre-checks against the package''s five sibling
    `ValueError` raises and `base.update_fields`'' `FileNotFoundError`, and the corrected
    no-op citations). What the re-derivation exposed is one level up from any single
    predicate: AC-5 *asserted* its predicate list exhaustive rather than proving it,
    which is the same treadmill as patching a found member — five consecutive rounds
    had the class right and the members short. Swept live, the package''s complete
    universe of non-completed-write returns in write paths and shared section-read
    helpers is **28 sites** and nothing else (`company.py`, `meeting.py` and `book.py`
    declare no bool-returning writer at all, which is also what makes `append_to_timeline`
    P3''s only member by enumeration rather than inspection). Classifying all 28 left
    exactly one residue — `_get_body_content`''s missing-file `None`, already converted
    to a `ValueError` by its only caller — now no-op class **(d)**. AC-5 gains that
    class and a **CLOSURE** clause requiring the test to enumerate the universe and
    land every member in exactly one of P1-P4 or (a)-(d), with the out-of-universe
    returns named explicitly. Rule added: **a derived sweep is finished when its universe
    is enumerated and every member classified — until then "derived by N predicates"
    is still a sample, just a principled one.**


    **Revised again 2026-07-24 (round 9)** after the eighth re-verify — the first
    round whose finding was a *design* objection rather than an enumeration gap (the
    28-site universe was independently re-derived and confirmed exact). The finding:
    P3 forced `append_to_timeline`''s marker-absent case to raise on a raw-content
    check that cannot distinguish "corrupted since creation by this package" from
    "legitimately never had a Timeline section" (hand-created in Obsidian, or predating
    the template convention — a scenario round 6''s own prose named), while the sibling
    `append_to_body_section` already handles the identical ambiguity with a caller-facing
    `create_if_missing` lever that P3 gave `append_to_timeline` no equivalent of.
    Dave ruled remedy (a): **accommodate** — auto-create the section and insert, mirroring
    the sibling''s default, so the entry always lands and the drop becomes impossible
    without manufacturing a failure out of a structural variant. P3''s disposition
    changes from raise to accommodate (the CLOSURE taxonomy stays eight buckets: three
    raise predicates, one accommodate predicate, four no-op classes); dedup keeps
    its exact `False`; the Example of done is restated in both directions. Rule added:
    **when a raise remedy rests on a premise the runtime check cannot confirm, and
    a sibling already solves the same ambiguity by accommodation, converge on the
    sibling — refusal is only loud-fail when the thing refused is actually a failure.**


    **Revised again 2026-07-24 (round 10)** — the audit-fold applied to round 9''s
    own remedy, since a ruling that says "mirror the sibling" is a name-level argument
    until the sibling is read. It was, and it is lossy in exactly the case the ruling
    serves: `append_to_body_section`''s `create_if_missing=True` route rebuilds the
    body via `parse_body_sections`/`write_body_sections` (person.py:1586-1593 → body_sections.py:74-97,
    100-134), which retain only `^## `-delimited spans — so a preamble above the first
    heading is deleted and a heading-less body is destroyed outright, written by a
    raw `write_text` (person.py:1495, 1597) that writer.py:178-183 deliberately exempts
    from the WI-126 body-shrink guard AC-4 is hardening. The note least likely to
    have `##` headings is the hand-created-in-Obsidian note round 9 ruled the accommodation
    in for, so the naive mirror would trade a silently dropped entry for a silently
    dropped note body. Dave''s ruling is unchanged; AC-5''s P3 gains a **PRESERVATION**
    clause (pre-existing body entirely present, frontmatter byte-identical, proved
    on a heading-less fixture and a preamble fixture, with today''s `body_sections`
    round-trip explicitly failing it) plus an idempotence assertion, the CLOSURE clause
    now says it is evaluated against the **post-fix** package (28 is a baseline, not
    the expected answer — P3''s own remedy adds code), and the "the drop is impossible"
    claim is corrected to *structural* absence, since whole-file dedup (person.py:1476,
    deliberate per person.py:1521-1524) is frozen by this AC''s backward-compat half
    and remains the one falsy path. Rule added: **when a fold converges on a sibling''s
    semantics it inherits the sibling''s implementation — read the sibling, don''t
    cite it; a contract ("creates the section if missing") is not a predicate (round-trips
    the body through a lossy parser).**


    **Revised again 2026-07-24 (round 11)** after the tenth re-verify, Dave-ruled
    remedy (a) on a single-gap ask. The finding: AC-1''s "a fifth caller joins the
    sweep" and AC-5''s CLOSURE both promised a *forward-looking* completeness property
    — a future silent-`False` writer or `parse_frontmatter`-calling write path gets
    caught by the suite going red — but neither `check:` required the derivation to
    be performed by the test against live source; a hand-derived enumeration frozen
    at build time satisfied both as written, and a sixth To-Discuss-style writer copy-pasted
    in next month would ship green and invisible, which is the original five findings''
    failure mode reproduced by the very clause built to prevent it. Both ACs now require
    the derivation be EXECUTED at test time (AST/inspect scan of the swept surface,
    checked against an explicit in-test classification map; unclassified site = red),
    and state that a hardcoded name/line list does not satisfy them. This is the terminus
    of the item''s derive-don''t-name ladder: sites → predicates → universe → disposition
    → preservation → the test itself performs the derivation. Rule added: **a completeness
    claim is only as durable as the process that re-checks it — if the AC promises
    "future instances join the sweep," the check must run the derivation, not remember
    its output.**


    **Revised again 2026-07-24 (round 12)** — the audit-fold applied to round 11''s
    own remedy, since "the test performs the derivation" is a promise about a predicate
    until the predicate is run. It was, against the live tree, and it returns a member
    AC-1 does not sweep: `write_markdown_file` calls `parse_frontmatter` (writer.py:186)
    and then writes (217), satisfying round 11''s literal "callers of parse_frontmatter
    that subsequently write" — so a builder implementing that scan gets five paths,
    sees the AC names four, and drops the fifth by name, which is the frozen curation
    round 11 abolished, moved inside the scan. What actually separates them is data
    flow: the four members re-serialize the dict `parse_frontmatter` returned into
    the bytes they write, while `write_markdown_file` discards it and builds its output
    from its own arguments (writer.py:197-205). AC-1 now states the predicate that
    way and requires `write_markdown_file` be **reached and rejected by the scan**,
    asserted as a negative — a scan that only confirms what it returns has not been
    shown to discriminate. Re-running the finding''s shape over the whole AC set (rather
    than the two ACs the gate named) found the same overclaim standing in two more
    places: **AC-3**, whose "a fourth repository joins automatically" has been in
    the Exploration Notes since round 1 with no check behind it, now derives its **class
    list** live from the concrete `BaseRepository` subclasses (ABC with abstract `entity_type`/`type_name`,
    base.py:120-130) while round 6''s non-uniform twelve cells stay explicit — the
    cells are the map, the scan supplies its keys, an unmapped key fails; and **AC-2**,
    whose "one case per return site" is a completeness claim over a function this
    item''s own fix edits, now scans `parse_frontmatter`''s post-fix return sites
    (five is a baseline, not the answer). AC-5''s classification map gains the key
    it was missing: a source-stable site identity (module + qualified function + ordinal
    within that function), since line numbers all shift in `person.py` when the fix
    lands and a function name alone cannot separate `append_to_timeline`''s four sites
    across three buckets. Rule added: **a live derivation is a predicate plus a proven
    negative, and the clause belongs to every AC that claims a class is complete —
    not to the ones a round happened to name.**


    **Revised again 2026-07-24 (round 13)** after the twelfth re-verify, Dave-ruled
    on a single-gap ask with a totality upgrade. The finding: AC-3''s class-list derivation
    was specified as a runtime `__subclasses__()`-style check while its sibling sweeps
    are AST-based — and the import graph is a weaker oracle than the source: a fifth
    repository module not imported by `repositories/__init__.py` by test time is invisible
    to `__subclasses__()`, so the discovery clause itself reproduces the green-suite/zero-coverage
    gap it was added to close. The fold applied the class fix, not the instance fix:
    ALL four derived sweeps (write paths, parse return sites, repository classes,
    the falsy-site universe) now state one uniform mechanism — discovery from source,
    AST over the package''s module files on disk, with the test importing what it
    discovers — and AC-3 explicitly rejects the runtime check. Rule added: **a sweep
    derived from the import graph inherits the import graph''s blind spots — derive
    from source; the set of modules that happen to be imported is itself an unproven
    premise.**


    **Revised again 2026-07-24 (round 14)** — the audit-fold applied to round 13''s
    own remedy, by running the four scans it unified rather than re-reading its summary
    of them. Two findings, one class. First, round 13''s note claims all four sweeps
    now state one mechanism; read live, it rewrote AC-3 and AC-2 already said "AST",
    while **AC-1 and AC-5 still read "AST *or inspect-based*"** — and `inspect` enumerates
    module objects, which exist only for imported modules, so it carries the identical
    blind spot `__subclasses__()` was rejected for. It reads green today only because
    every module in this package happens to be transitively imported (`name_validation.py`
    solely via `repositories/person.py:22`), which is round 12''s own tell. Second,
    the same gap one level down: three of the four scans hand-write their **file set**
    — AC-3 walks `repositories/`, AC-5 walks "the swept modules" (the two its 28-site
    count lives in), AC-1 says "the package" — and a source scan scoped by a directory
    or a module list misses a fifth repository or a sixth silent-`False` writer added
    in a new module exactly as the import graph does. All four now walk one derived
    file set: every `.py` under `obsidian_schemas/`, recursively, discovered by the
    test. Third and separately, running AC-2''s scan exposed a keying error nothing
    had caught: AC-2 says "one case per return site" and lists five, but `parse_frontmatter`
    has **four** `return` statements (parser.py:65, 70, 77, 80) carrying five outcome
    classes — the empty-fence case is the `safe_load`-returns-`None` normalisation
    at 74-75, which shares site 77 with the valid case — so the AC''s own site-set
    equality assertion is red on a correct implementation, and the cheap repair drops
    the unmatched *class*. AC-2 now keys its map by return site, allows a site to
    carry more than one named outcome class, and requires each class exercised. Rules
    added: **a source scan is only as complete as the file set it walks — derive the
    file set too; naming a directory is the frozen list wearing a path**; and **never
    key a scan''s map to a construct the scan cannot return.**


    **Revised again 2026-07-24 (round 15)** after the fourteenth re-verify, Dave-ruled
    on a one-line ask. The finding: the parse seam''s loudness change cascades to
    callers no derived sweep could discover — `parse_markdown_content` and the four
    typed conveniences (parser.py:216-237), none behind a `try`/`except` — the uncovered-invocation-layer
    class (WI-158''s, LESSONS #7 corollary). The fold enumerated the seam''s COMPLETE
    invocation surface at source: every package caller of `parse_frontmatter`/`parse_to_model`
    classified into exactly one of four caller classes — refusing writer (AC-1), insulated
    loader (AC-3), the discarding guard (AC-4), and the previously unnamed fourth
    class, the PROPAGATING PUBLIC PARSE SURFACE, now covered by AC-2''s invocation-surface
    clause (malformed propagates the typed error, asserted per discovered member;
    absent/unknown keep today''s returns exactly). Export status was verified at source
    rather than trusted from the finding (the gate''s "all package-exported" was an
    overclaim: `__init__` exports `parse_frontmatter`/`parse_markdown_file`/`ParsedDocument`
    only; `parse_markdown_content` is README-documented; the four conveniences are
    public-by-module-path with zero external consumers today), and the Constraints
    bullet claiming N4 "the only finding that is not purely internal" is corrected
    — false once the public surface propagates. Rule added: **an item that changes
    a seam''s failure behaviour sweeps the seam''s callers, not only the code it edits
    — every caller lands in a named class or the suite is red; "internal-only" is
    a claim about an enumerated caller set, never about intent.**


    **Revised again 2026-07-24 (round 16)** — the audit-fold applied to round 15''s
    own remedy, by running the invocation-surface scan it added rather than re-reading
    its description of it. The finding: that scan is specified as "every caller of
    `parse_frontmatter` and `parse_to_model`", which is direct-call **adjacency**,
    and four of the six functions AC-2''s own map calls propagating members are not
    direct callers — `parse_person`/`parse_company`/`parse_book`/`parse_meeting` (parser.py:216-237)
    reach the seam only through `parse_markdown_content`, and `base._load_file` only
    through `parse_markdown_file` (base.py:178). Run live the scan returns nine functions
    containing none of those five, so a faithful implementation goes red against its
    own map and the cheap repair deletes precisely the README-documented conveniences
    the round-14 finding was raised about — round 14''s "never key a map to what the
    scan cannot return" recurring inside the remedy that rule produced. AC-2''s invocation
    surface is now a **transitive closure** (fixpoint of "functions that REACH the
    seam") whose stop rule is "another criterion has already assigned this function
    a disposition" — which terminates it and makes "exactly one class" well-defined
    — with the map equality asserted in **both** directions, and the six-member residue
    computed rather than named. The same read also retired an unverifiable claim:
    AC-2 asserted the conveniences have no external consumer "verified against HAL9000
    and exocortex source", which this hermetic floor cannot check and which the first
    fold already removed a clause for; export status is now stated only from in-repo
    source, with external consumers parked alongside N4''s companion item. Rule added:
    **a caller sweep is a transitive closure, not an adjacency list — a seam''s invocation
    surface is every function that REACHES it, and the closure is well-founded only
    because it stops where another criterion has already assigned a disposition.**


    **Revised again 2026-07-24 (round 17)** after the sixteenth re-verify, Dave-ruled
    on a one-line ask. The finding: the closure''s own stop set — the one construct
    that makes the walk terminate — was named by example (AC-1''s four writers, AC-3''s
    three loaders, AC-4''s guard) in a document where every other set forbids a hardcoded
    list; a future writer or loader those ACs auto-discover would fall outside the
    frozen stop list, unbounding the closure or leaving one function claimed by two
    ACs with incompatible dispositions. The fold composes rather than restates: the
    stop set is now CONSUMED as the live output of AC-1''s, AC-3''s and AC-4''s own
    test-time derivations, and a PARTITION assertion requires the three computed stop
    sets plus the propagating residue to partition the computed closure exactly —
    a member in no class or in two is red by computation. This closes the derivation
    system under its own checks: there is no set left in the AC set that is named
    rather than derived, and the sweeps now verify each other''s boundaries. Rule
    added: **when criteria share a boundary, one criterion consumes the other''s derivation
    as input — restating a sibling''s set is a frozen list wearing a cross-reference,
    and the partition of the whole surface is itself an assertable property.**


    **Revised again 2026-07-24 (round 18)** — the audit-fold applied to round 17''s
    own remedy, by running the composition it introduced rather than re-reading the
    sentence that composes it. The finding: AC-2''s stop set is specified as the union
    of AC-1''s, AC-3''s and AC-4''s live derivations, but only AC-1''s is a set of
    *functions*. AC-3''s derivation discovers **classes** (its whole map is keyed
    by class), and a class is not a member of a closure over functions — consumed
    literally the intersection is empty, so the closure never stops at `base._load_file`
    and climbs through `load()`, `get_all()` and `resolve()`, the unbounded walk the
    stop rule exists to prevent, now reached *through* the rule. And AC-4 runs no
    derivation at all — it names `write_markdown_file` and asserts two fixtures —
    so "AC-4''s live output" is fictitious and the only repair available is the hardcoded
    name the clause abolished. Worse, the PARTITION assertion is satisfiable on the
    broken implementation: empty stop sets make the residue the whole closure, every
    member lands in exactly one class, and AC-2 ends up asserting that AC-1''s writers
    PROPAGATE — the refuse-vs-propagate collision the partition was built to catch,
    reached through the partition. The fold makes each contribution state its own
    conversion: AC-1''s arrives as functions; AC-3''s is resolved per discovered class
    through the MRO to its `_load_file` implementation and deduplicated (four classes
    → three functions, both baselines); AC-4''s guard is sourced instead from AC-1''s
    discrimination proof, whose two predicates'' **set difference** already computes
    it. All three plus the closure are normalised to one source-stable function identity
    before any set operation, and each contribution must be non-empty and a subset
    of the closure. Rules added: **consuming a sibling criterion''s derivation is
    a typed operation, not a cross-reference — state what the sibling produces, what
    this criterion needs, and the conversion between them; a sibling that derives
    nothing cannot be consumed**; and **a composition is checked by running it, not
    by reading the sentence that composes it.**


    **Revised again 2026-07-24 (round 19)** after the eighteenth re-verify, Dave-ruled
    as a TWO-PART fold on a framed ask. Part one, the finding''s fix: nothing required
    the scans the stop set consumes to be one implementation — a builder could satisfy
    every fence with independently-written duplicate predicates that agree on today''s
    tree and diverge on the first future write path, the refuse-vs-propagate collision
    reappearing one level down. AC-2 now requires ONE shared importable scan module
    consumed by every test that derives, with implementation identity asserted (same
    callables, not same-typed outputs) — solve-in-one-place applied to the harness.
    Part two, Dave-ruled and explicitly one-off: a **specification-altitude declaration**
    in the AC preamble. The last four rounds'' findings all concerned the checking
    machinery''s own architecture, each fold''s fix creating the surface the next
    round examined — a regress with no natural floor. The declaration scopes THIS
    AC set to observable behaviour + derivation obligations + their composition, and
    routes findings below that line (harness factoring, the scan module''s own tests)
    to the pipeline''s existing later gates (build-exit review, intent-check) where
    they already have an owner. It amends no role or bar; it is recorded as the first
    live specimen for the WI-187 altitude session. Rule added: **an AC set needs a
    declared floor as much as a derived sweep needs a declared universe — without
    one, the red-team''s regress is unbounded by construction, and every fix mints
    the next finding''s surface.**


    **Revised again 2026-07-24 (round 20)** — the audit-fold applied to round 19''s
    own Part 1, by reading where that clause landed in each fence it binds rather
    than re-reading the fence it was written into. The finding: `ONE IMPLEMENTATION`
    was written into **AC-2 alone**. AC-1, AC-3 and AC-5 were left saying only that
    their derivations are performed at test time by an AST scan over a walked file
    set — none says where the scan is defined or that its own test must import it
    — and AC-4 still names `write_markdown_file` with no statement that AC-2''s stop-set
    member comes from AC-1''s set difference. That is one-sided, and it is unimplementable
    in the direction that matters: AC-2 asserts "the callables it consumes are the
    same objects the sibling tests invoke", but object identity can only be asserted
    against a callable the asserting test can reach, and a scan nested inside AC-1''s
    test function — the ordinary shape for a self-contained pytest test, and the shape
    nothing forbade — is reachable by nobody. The compliant-looking implementation
    imports the shared module in AC-2, asserts identity against the objects it just
    imported (vacuously true), and leaves AC-1 running a private copy; the fifth write
    path then makes AC-1 say *refuse* and AC-2 say *propagate*, which is the exact
    collision round 19 was written to prevent. Every producing fence now carries the
    obligation — the shared module''s scans are obtained **by import** in each criterion''s
    own test, and a local re-implementation fails **that** criterion, not only AC-2''s
    — AC-4 states that its function''s identity is supplied by AC-1''s derivation,
    the Approach carries the property (round 19 amended neither it nor the producing
    fences), and a fourteenth Example of done pins the cross-AC consistency direction
    none of the previous thirteen did. Verified live that the obligation is satisfiable
    on this floor as it stands: no `conftest.py` exists anywhere in the tree, and
    none is required, because `tests/__init__.py` makes `tests/` an importable package
    under the rootdir prepend the suite already depends on. This sits **on** round
    19''s declared floor at item (c), composition; where the module lives, what it
    is called and how it is factored remain below it and routed as declared. Rule
    added: **an obligation that binds two criteria must be written into both — a shared-implementation
    clause stated only by the consumer is an assertion about code the producer was
    never required to expose, and it degrades to identity-against-itself.**


    **Revised again 2026-07-24 (round 21)** after the twentieth re-verify, Dave-ruled
    on a one-line ask — and the first round in which the altitude declaration did
    its work: the gate explicitly set aside a sub-floor observation as not weighing
    into the verdict, and its material finding was in-scope, the composition property''s
    own operationalization. The finding: "obtains it by import" constrains how a test
    is written, not what any check asserts — AC-2''s identity comparison is vacuously
    true against the shared module itself while a sibling runs a private copy, and
    the Example of done''s red-on-divergence promise had no check delivering it. The
    fold operationalizes by DEFINITION-SITE UNIQUENESS: a named check (test_derivations_are_single_sourced)
    scans the test tree and package with the same AST walk the tests use on the package
    and asserts each derivation predicate is defined exactly once, in the shared module
    — a second definition site is a red test naming the site. Identity-by-comparison
    is replaced with uniqueness-by-scan, which holds even for tests that never touch
    the partition check. Rule added: **an identity claim is operationalized by proving
    the copy CANNOT EXIST, not by comparing an object to itself — uniqueness of definition
    sites is scannable; identity of uses is not.**


    **Revised again 2026-07-24 (round 22)** — the audit-fold applied to round 21''s
    own remedy, by asking which fence carries the check that remedy names rather than
    by re-reading the sentence that names it. Two findings, one class. First, `test_derivations_are_single_sourced`
    was written into **AC-2''s `desc:`**, and AC-2''s `check:` is `test_parse_boundaries_distinguish_failure_from_empty`
    — a criteria fence carries exactly one check (`parse_criteria`, work_item_linter.py:984-997;
    the conveyor discovers a test by `def <check>(`), so the uniqueness property was
    owned by no fence and a builder who never writes that test satisfies every criterion
    in the set. That is the round-20 finding''s own shape recurring inside its remedy:
    the obligation moved from prose-about-imports to prose-about-a-check, and prose
    is graded by nothing. AC-6''s `why:` had already recorded the fix ("a criteria
    fence carries exactly one check") when the same problem split it out of AC-3.
    Second, uniqueness is the one assertion in this AC set that **fails open**: a
    detector matching nothing in `tests/` still finds the single site in the shared
    module and still reports "exactly one", so an under-generating scan is indistinguishable
    from a compliant harness — where every other sweep here goes red when it under-generates.
    The fold promotes uniqueness to **AC-7** under its own `check:`, walks `tests/`
    as well as `obsidian_schemas/`, and requires a **planted** second definition site
    the scan must reach, match and name, one per shape its detector claims to match.
    Separately, the import obligation is made assertable where it is graded: AC-1,
    AC-3 and AC-5 each assert, of the same bindings they compute with, that the callable''s
    `__module__` is the shared module''s — so "a locally re-implemented copy FAILS
    this criterion" is true of that criterion''s own check rather than of a sibling''s.
    The Approach gains the property (round 21 amended neither it nor the producing
    fences), a fifteenth Example of done pins both directions, and AC-2''s stale `(round-18
    finding)` label — the round-20 gate''s MINOR — is disambiguated, this document
    having numbered an audit-fold and a gate pass 18 alike. Rules added: **a property
    is enforced by a fence, not by a sentence — an AC set grades exactly the `check:`
    names its fences carry, so naming a new check inside another criterion''s `desc:`
    moves the obligation from unenforced prose to unenforced prose**; and **an assertion
    satisfied by finding nothing needs its negative planted, not merely stated.**


    **Revised again 2026-07-24 (round 23)** after the twenty-second re-verify, Dave-ruled
    on a one-line ask. The finding: AC-7''s per-derivation cardinality was unimplementable
    as written — three of its six derivations share one AST-walk detector shape, and
    the loose and data-flow predicates are indistinguishable by ANY shape, differing
    only semantically. The fold stops shape-detecting semantics: uniqueness is restated
    at the CAPABILITY level — use of the ast module, the one thing every derivation
    copy must do, asserted single-homed to the shared scan module across the derived
    package+tests file set, with the planted negative covering both marker forms —
    and completeness moves to the one place distinctness is decidable, the shared
    module''s six named exports resolving to six distinct function objects. Capability
    uniqueness implies uniqueness of every predicate built on it; no semantic discrimination
    is ever required. Completed on re-run: the **Approach** and the Check-strategy
    note still specified the retired per-derivation shape attribution after the fence
    was corrected — the fourth consecutive fold to leave the Approach behind — and
    both now carry capability detection; and the two verifications the fold rested
    on were run rather than asserted, confirming live that nothing under `obsidian_schemas/`
    or `tests/` references `ast` today (so single-homing is satisfiable, not red on
    arrival) and exposing a self-match that forced a clause: the check must contain
    the planted fixture''s source, so a text-matching detector finds a second `import
    ast` in its own module and goes red on a clean harness. AC-7 now states that the
    marker is read off **parsed syntax, never source text**. Rules added: **detect
    the capability, not the semantics — when two implementations differ only in meaning,
    uniqueness is asserted on what every copy must DO, and completeness on names,
    the one identity a scan can decide**; **a fold is not landed until every layer
    that states the mechanism states the NEW one — a retired mechanism surviving in
    the Approach is a specification a builder can implement faithfully**; and **a
    detector that plants its own negative must be told what it reads, or the plant
    matches the planter.**


    **Revised again 2026-07-24 (round 25)** after the twenty-fourth re-verify, Dave-ruled
    on a one-line ask. The finding: AC-7''s sufficiency universal was false for one
    member — the file-set walk is pure filesystem enumeration and references no ast
    symbol, so a private copy of exactly that derivation (the least-effort one to
    reimplement) was invisible to the ast marker, and the `__module__` self-certs
    only catch a copy a consuming test actually binds. The fold states sufficiency
    **per member**, and it did so in two passes. The first pass gave the sixth derivation
    its own capability marker — `.py`-targeted filesystem enumeration, single-homed
    by the same scan — which is the obvious repair and is **withdrawn on re-run, because
    running the verification round 23 made mandatory kills it**: `tests/test_vault_path_required.py:320`
    already runs `rglob("*.py")` over `obsidian_schemas/` and `scripts/` as WI-024''s
    own AC-2 forbidden-default scan, so the marker is red on a compliant, non-duplicated
    tree the day it is written — the identical red-on-a-correct-implementation defect
    the per-derivation framing was dropped for, reproduced inside the remedy for the
    *next* finding. Nor can the pattern be narrowed out of it: both that scan and
    a walk copy `rglob` `".py"` rooted at `obsidian_schemas/`, and separating them
    is the semantic question round 22 proved undecidable, while exempting it by name
    is the frozen list this document has abolished six times — and the exempted test''s
    own docstring rules against exception lists in as many words. So the landed fold
    claims sufficiency for **five** members via the `ast` marker (re-verified live
    at this fold: no `.py` file anywhere in this tree references `ast`) and dispositions
    the sixth by argument: a walk that FEEDS a derivation is caught by the copy of
    that derivation it feeds; a walk a sweeping test BINDS is caught by that test''s
    `__module__` self-cert; a walk feeding neither is not a derivation copy, and a
    genuine seventh derivation is forced into the export list by COMPLETENESS and
    surfaced by AC-2''s partition. The residue is **named as undetected** with its
    blast radius bounded, rather than covered by a sentence. Rules added: **a sufficiency
    claim over a set is proven member-by-member — one member outside the mechanism''s
    reach is not an approximation, it is the copy that will be written**; and its
    correction, **when a universal fails for one member, the fix is not automatically
    a second mechanism — run the new mechanism against the live tree before adopting
    it, and if the capability it detects is generic rather than a signature, state
    the member''s residue honestly instead of shipping a marker that is red on arrival.
    An AC that names its edge is stronger than one that stretches a marker until it
    matches the tree''s legitimate code.**


    **Revised again 2026-07-24 (round 27)** after the twenty-sixth re-verify, Dave-ruled
    on a one-line ask — and the first finding since round 10 that is about the ITEM''S
    BEHAVIOUR rather than the harness: the harness thread is exhausted. The finding:
    AC-2''s parse_to_model clause distinguished "known type whose validation failed"
    (raise) from "unknown type" (None) without stating how known-ness is decided when
    the model class is CALLER-FORCED — which it is at every in-scope caller — so a
    compliant implementation could make parse_person raise on a well-formed book note,
    breaking the existing test_parse_person_wrong_type baseline and an Example of
    done. The fold states the decision rule, and it is AC-3''s ownership principle
    one layer down: known-ness is a property of the NOTE (raw declared type equals
    the forced class''s type name), never of the call — raise only on owned-and-drifted;
    a readable foreign type is an answer (today''s None, baselines byte-preserved);
    an unmodelled type is an answer. Completed on re-run, and it is this document''s
    most-repeated omission for the sixth fold running: the **Approach** and the **C5
    per-finding direction** both still carried the retired "known type, failed validation
    vs. unknown type" framing after the fence was corrected — the exact sentence the
    finding is about, in the two places a spec-writer reads before it reads a fence
    — and both now state the deciding input. Three further gaps the re-run found and
    closed, none of them in the first pass: the rule named a comparand it never derived
    (now `model_class.model_fields["type"].default`, read off the class''s own `Literal`,
    models.py:78/127/159/192/220/240/259/294, because an unsourced type name is implemented
    as a hardcoded `"person"`); the rule was stated only for the caller-forced branch,
    leaving the auto-detect branch undecided, when in fact `TYPE_TO_MODEL` (models.py:309-317)
    maps each type string to the class declaring that same string, so one rule covers
    both branches by construction; and a **third case** was defaulting by accident
    — a note with non-empty frontmatter, no `type` key and a drifted field, which
    validates past the `type` `Literal`''s default, fails on the drifted field, has
    no ownership evidence and no glob at this layer to supply any, and must keep today''s
    `None`. Finally the finding''s own remedy was taken in full: AC-2 now requires
    the **fixture pair asserted in one test** at a caller-forced call site (round
    4''s rule, fourth application, first at the parse layer), the Check-strategy note
    moves that half out of the Hypothesis family into the explicit-fixture family
    for the round-6 reason AC-3''s matrix is there, and a seventeenth Example of done
    pins both directions in Dave''s terms. Rules added: **a distinction an AC draws
    must name its deciding input — "known" is ambiguous wherever the caller supplies
    an expectation, and the note''s own declaration, not the caller''s hope, is what
    this document decides ownership on everywhere else**; and **a decision rule is
    incomplete until its comparand is derived and every branch that reaches it is
    dispositioned — naming the input without naming where the input is read from re-opens
    the frozen-list door one level inside the remedy.**


    **Check strategy (Dave''s 2026-07-23 testing ruling, applied at round 7):** this
    is a pytest-floor project with Pydantic schemas and a parse/serialize inverse
    pair, so checks whose properties quantify over *inputs* are implemented as Hypothesis
    property tests over generated note contents — AC-1 (any generated note with malformed
    frontmatter: every derived write path raises and the file is byte-identical; any
    generated note with absent frontmatter: none raises and behaviour matches the
    captured baseline), AC-2''s `parse_frontmatter` half (generated inputs per return-site
    class; malformed never returns a legitimate case''s value), and AC-5''s two halves
    (generated failure inputs raise; generated legitimate no-ops keep today''s exact
    returns). AC-3''s twelve cells stay explicit hand-derived fixtures — the cells
    have non-uniform, opposite answers and the matrix IS the specification; property
    generation there would re-introduce the shared-expectation-table error the round-6
    rule forbids. **AC-2''s `parse_to_model` half is in that same explicit family,
    for the same reason** (round-27 fold, completed on re-run): owned-and-drifted,
    well-formed-foreign and absent-type inputs share one code path and carry opposite
    answers, so they are three named fixtures asserted in one test rather than a generated
    space — a generator over "inputs that fail `model_validate`" has exactly one expectation
    table to offer and would assert the uniformity that *is* the defect. Property
    tests quantify over inputs; they do not substitute for the site/predicate derivations
    above, which quantify over code. AC-7 is in that second family and is explicitly
    not a property test: it quantifies over the harness''s own use of one capability,
    and its generated case is the planted duplicate, hand-written per MARKER FORM
    — an `import ast` statement, and a bare `ast.*` reference under a from-import
    or aliased import — rather than sampled. There are no derivation shapes left to
    enumerate: round 23 replaced shape attribution with capability detection precisely
    because no shape discriminates the six derivations from each other. Two marker
    forms is the whole generated set — the sixth derivation, the file-set walk, carries
    no marker of its own (its capability has a legitimate pre-existing home at `tests/test_vault_path_required.py:320`,
    so a marker for it would be red on arrival), and is dispositioned by argument
    in AC-7''s SUFFICIENCY clause rather than by a planted case there is nothing sound
    to plant against.


    ```criteria

    id: AC-1

    desc: No write/mutate path rebuilds a note from a frontmatter parse that failed,
    and no legitimate parse loses its ability to write. The test parametrizes over
    the write paths DERIVED from the package itself — every caller of parse_frontmatter
    that then re-serializes and writes, today update_fields (base.py:312), update_frontmatter_field
    (writer.py:247), update_frontmatter_fields (writer.py:286) and roundtrip_file
    (writer.py:317) — and the derivation is PERFORMED BY THE TEST AT TEST TIME against
    the live source — an AST scan over a file set the test WALKS rather than names
    (every .py under obsidian_schemas/, recursively, discovered on disk), never an
    inspect-based scan (inspect.getmembers/getsource enumerate module OBJECTS, which
    exist only for modules something imported, so an inspect sweep carries the exact
    import-graph blind spot AC-3 rejects; it happens to read complete today only because
    every module in this package is transitively imported, name_validation.py solely
    via repositories/person.py:22) and never a file set scoped by hand to a directory
    or a module list (a sixth such caller added in a NEW module beside writer.py is
    as invisible to a directory-scoped source scan as to the import graph — the frozen
    list wearing a path), never a hand-derived list frozen at build time: the test
    asserts its scan finds exactly the paths it then parametrizes over, so a fifth
    such caller added later is DISCOVERED by the suite going red, not by a human noticing
    — that forward-looking property is what this clause guarantees, and a check that
    hardcodes the four names does not satisfy it. The scan''s predicate is DATA FLOW,
    not adjacency — a member is a function in which the dict returned by parse_frontmatter
    is re-serialized into the bytes that same function writes (base.py:312 -> 324
    -> 327-329; writer.py:247 -> 250 -> 253-256, 286 -> 289 -> 292-295, 317 -> 319-322).
    "Calls parse_frontmatter and later writes" is NOT the predicate and returns a
    FIFTH function that must not be swept: write_markdown_file (parse at writer.py:186,
    write at 217) discards the parsed frontmatter (it binds only existing_body, for
    the WI-126 shrink guard) and builds what it writes from its own entity/frontmatter
    arguments (writer.py:197-205); its malformed-existing-file behaviour is AC-4''s,
    not this criterion''s. The test must therefore prove its scan DISCRIMINATES rather
    than merely enumerates: write_markdown_file is REACHED by the scan''s traversal
    and REJECTED BY ITS PREDICATE, asserted as a negative case in the same test. A
    scan that excludes it by name, or that never visits it, does NOT satisfy this
    criterion — a scan asserted only against the members it returns is indistinguishable
    from a function that returns those four names, which is the frozen list this clause
    exists to forbid. SHARED IMPLEMENTATION (round-20 finding): the file-set walk,
    the loose "calls parse_frontmatter and later writes" predicate, the data-flow
    predicate, and the SET DIFFERENCE between them are DEFINED IN the one shared importable
    scan module AC-2 requires, and THIS test obtains them FROM IT BY IMPORT — never
    as helpers private to this test module, and never nested inside the test function.
    A locally re-implemented copy FAILS this criterion even when it returns the same
    four names on today''s tree — and that failure is ASSERTED BY THIS CHECK, not
    left to a sibling''s (round-22 finding). "Obtains it by import" is a constraint
    on how this test is WRITTEN, and how a test is written is graded by nothing: this
    criterion is satisfied, mechanically, by test_no_mutation_writes_through_failed_parse
    passing, so a builder who defines the two predicates privately in this test module
    and never touches the shared module still computes the same four write paths and
    still goes green. The obligation is therefore made an assertion this test makes
    about ITSELF: for each derivation callable it invokes — the file-set walk, the
    loose predicate, the data-flow predicate, the set difference — it asserts that
    callable''s __module__ is the shared scan module''s, asserted on the SAME binding
    it parametrizes from, so a private copy carries this test module''s __module__
    and turns THIS check red. The reason it must be true here rather than only over
    there is that this derivation is not this criterion''s alone: AC-2''s stop set
    consumes it, and an identity assertion made in AC-2 can only bind to a callable
    another module can reach — a scan nested in this test function is reachable by
    nobody, so AC-2''s comparison would degrade to the shared module against itself
    while this test ran a private copy. AC-7 closes the same gap from the opposite
    side, by proving no second definition site EXISTS anywhere in the harness; the
    two are complementary and neither substitutes for the other — this one catches
    a private copy this test USES, AC-7 catches a private copy that merely exists.
    Two copies that agree today diverge on the first future write path (say one matches
    an ast.Attribute-style call and the other an ast.Name one), and the divergence
    surfaces as this criterion requiring a function to REFUSE while AC-2''s residue
    simultaneously asserts it PROPAGATES — the refuse-vs-propagate collision, reached
    through the composition built to prevent it. Where that module lives and what
    it is called is not specified here and is not this criterion''s business; that
    it is ONE module, imported rather than re-typed, is. For EACH path, on a note
    whose frontmatter is malformed YAML the call raises a typed ValueError subclass
    AND the file on disk is byte-identical to before (original content never duplicated
    into the body, frontmatter never replaced by the partial updates). Conversely,
    and over the SAME derived path list rather than a subset of it, on a note with
    genuinely absent frontmatter (parser.py:64-65) NO path raises — each of the four
    still behaves exactly as it does today, asserted against a baseline captured from
    the current tree (same return value AND same resulting file bytes), so update_fields
    and update_frontmatter_field(s) still add the frontmatter and preserve the body,
    and roundtrip_file still honours its documented contract of preserving all content.
    Malformed YAML is the ONLY input the raise half licenses; a fix that also raises
    on absent frontmatter at ANY path in the sweep fails this criterion, and a fix
    that special-cases absent at some paths but not others fails it too.

    kind: test

    check: test_no_mutation_writes_through_failed_parse

    ```


    why: this is the keystone — the C2 corruption chain, confirmed live, destroys
    and duplicates real note content silently; asserting on-disk bytes rather than
    merely "it raised" is what closes the door, deriving the path list is what stops
    the fix landing on one of four, and quantifying the absent-frontmatter half over
    that SAME derived list (not the two paths it originally named) is what stops a
    builder satisfying the raise-half by making parse_frontmatter refuse everything
    it cannot hand back a real dict for and then special-casing only the paths the
    AC happened to check — which would leave update_fields raising on every freshly-created
    stub and roundtrip_file raising on every frontmatter-less note it normalizes.
    And pinning the scan''s predicate to data flow with a proven negative is what
    makes "the test performs the derivation" mean something: the loose predicate ("parses,
    then writes") returns write_markdown_file, which this criterion must not sweep,
    so a builder running it as written would exclude the fifth member by name — re-freezing
    the list inside the very scan that was supposed to abolish the frozen list. Requiring
    the scan to visit that function and reject it on the predicate is the only form
    the exclusion can take that a future fifth member cannot slip past, and it is
    the difference between a scan that discriminates and one that recites.


    ```criteria

    id: AC-2

    desc: The parse boundaries distinguish failure from a legitimate empty/unknown
    result, with a case per outcome DERIVED from each function''s own branch structure
    rather than a sampled fixture. For parse_frontmatter that is one case per OUTCOME
    CLASS, mapped onto the function''s actual RETURN SITES — which are NOT in bijection
    with them and must not be conflated (round-14 finding). Five outcome classes:
    no leading fence (parser.py:64-65), an opening fence with no closing fence (69-70),
    a fence present but empty (the safe_load-returns-None normalisation at 74-75),
    valid frontmatter (77), and YAMLError (78-80). FOUR return sites carry them: parser.py
    65, 70, 77 and 80 are the only ast.Return nodes in the function, because the empty-fence
    class has no return of its own and falls through to site 77, which it SHARES with
    the valid-frontmatter class. Malformed YAML must never return the same value as
    a fence-less or empty-fence document, and the legitimate cases must keep returning
    today''s value so existing callers are unchanged. The unclosed-fence case must
    be classified explicitly as absent or as malformed — not left to default by accident
    — because append_to_body_section already treats that same input as a distinct
    malformed-fence case (person.py:1564-1570). For parse_to_model, a known type whose
    model_validate raised (loud — schema drift) is distinguishable from a legitimately
    unknown or unmodelled type (returns None as today, parser.py:135-137) — and "KNOWN
    TYPE" IS A PROPERTY OF THE NOTE, NEVER OF THE CALL (round-26 finding): every in-scope
    caller forces a model class (parse_person forces Person; base._load_file forces
    its entity_type), so the decision rule must be stated or a compliant implementation
    can raise on a well-formed foreign-type note. The rule is AC-3''s ownership principle
    one layer down: parse_to_model raises ONLY when the note''s raw declared type
    equals the forced class''s own type name AND model_validate fails — owned-and-drifted,
    the schema-drift case. A well-formed note of a DIFFERENT readable type handed
    to the wrong parser is decidably foreign — an answer, not a failure — and keeps
    today''s None exactly (the existing test_parse_person_wrong_type baseline and
    the "book where a person was expected" Example of done both keep passing unchanged);
    a type nothing models likewise keeps today''s None. An implementation that raises
    on foreign-type input at any caller-forced site FAILS this criterion. The forced
    class''s own type name is READ OFF THAT CLASS''S OWN DECLARATION, never hardcoded
    and never taken from the calling function''s name: every model declares type as
    a Literal with a matching default (models.py 78, 127, 159, 192, 220, 240, 259,
    294), so model_class.model_fields["type"].default is the deriving source, and
    a comparison against a "person" literal — or against isinstance of the constructed
    model, which is the defective predicate AC-3 forbids one layer up — does NOT satisfy
    this criterion. ONE RULE, BOTH BRANCHES, not a caller-forced special case bolted
    onto the auto-detect one: TYPE_TO_MODEL (models.py:309-317) maps each type string
    to the class whose own Literal declares that same string, so whenever get_model_for_type
    resolves on the model_class=None path (parser.py:130-133) the resolved class''s
    type name equals the note''s declared type BY CONSTRUCTION and the equality above
    holds automatically, while an unresolvable type has no class at all and today''s
    None at parser.py:135-137 stands untouched. A rule stated only for the caller-forced
    branch would leave the auto-detect branch''s loudness undecided, which is the
    same silence this finding is about. THIRD CASE, named so it cannot default by
    accident (the unclosed-fence lesson, one function down): a note whose type is
    ABSENT or unreadable while a class is FORCED carries no ownership evidence of
    either kind — there is no glob at this layer to own it by convention, so the four-bucket
    ownership taxonomy''s convention-owned row has no analogue here — and it keeps
    today''s return exactly and NEVER raises. It is reachable today and is not the
    empty-frontmatter short-circuit at parser.py:123: a note with non-empty frontmatter,
    no type key and a drifted field validates past the type Literal''s own default
    and fails on the drifted field alone, so parse_person on it returns None today
    and must still return None. TWO FIXTURES, ONE TEST — the round-4 rule, of which
    this is the fourth application and the first at the parse layer: the owned-and-drifted
    note and the well-formed foreign note travel the IDENTICAL code path (both are
    model_validate raising inside parser.py:139-150, with model_class the same object
    either way and nothing left in scope at the point of failure that separates them)
    and require OPPOSITE answers, so they must be two distinct inputs asserted in
    the SAME test AT A CALLER-FORCED CALL SITE — parse_person on type person content
    whose emails field holds a bare string RAISES, and parse_person on well-formed
    type company content RETURNS None — with a third input for the case above (no
    type key, drifted field) also returning None. A fixture set containing only the
    drifted note reads as the whole property and is exactly what an AC-2 fixture set
    naturally contains, which is what lets the foreign-type regression ship green
    against a passing check; and because these three cases have non-uniform, opposite
    answers on one code path, they are EXPLICIT hand-derived fixtures rather than
    generated inputs, for the round-6 reason AC-3''s matrix is. Every distinction
    is observable by the caller, not only in a log line. The return-site enumeration
    is PERFORMED BY THE TEST AT TEST TIME against the live POST-FIX source — an AST
    scan of parse_frontmatter for its ast.Return nodes, found by walking the package''s
    module files on disk (the same derived file set AC-1, AC-3 and AC-5 walk; never
    an inspect-based scan, never a hand-named module) — checked against an explicit
    in-test map KEYED BY RETURN SITE, where a site maps to ONE OR MORE named outcome
    classes. Keying the map by outcome class instead FAILS this criterion and is the
    round-14 finding: five classes against four sites means an entry keyed at 73-75
    matches no site the scan can return, the site-set equality assertion goes red
    on a CORRECT implementation, and the cheap repair — delete the entry with no matching
    site — silently drops the empty-fence class, which is in this AC precisely because
    it is a distinct outcome reached through a shared return. So the test asserts
    BOTH halves: the discovered site set equals the map''s keys exactly, AND every
    named outcome class in the map is exercised by at least one input, so a site carrying
    two classes cannot be closed with one case. Neither count is the expected answer
    — four sites and five classes are today''s baselines, and this item''s own fix
    changes both (the malformed case stops returning ({}, content), and the unclosed-fence
    case may gain its own site once classified). A return site the scan finds with
    no case mapped to it, or a named class no input exercises, FAILS this criterion
    rather than passing unnoticed. A five-case list frozen at build time does not
    satisfy it. Same reason as AC-1 and AC-5: an enumeration that is remembered rather
    than re-run stops being true the first time the function it describes is edited,
    and this fix edits it. INVOCATION SURFACE (round-14 finding; its derivation corrected
    round 16): the seam this item makes loud has callers outside the sweeps above,
    and they are covered by the same derivation discipline — but the derivation is
    a TRANSITIVE CLOSURE over the call graph, never a direct-caller list. The test
    computes, at test time by AST over the package''s module files walked on disk
    (the same derived file set AC-1, AC-3 and AC-5 walk), the FIXPOINT of "package
    functions that REACH parse_frontmatter or parse_to_model": seed the set with the
    functions that name either symbol directly, then repeatedly add the callers of
    everything already in the set until it stops growing. Direct-call ADJACENCY is
    NOT the predicate and cannot return this class — parse_person, parse_company,
    parse_book and parse_meeting (parser.py:216-237) name neither seam symbol, reaching
    it only through parse_markdown_content (218, 224, 230, 236), and base._load_file
    reaches it only through parse_markdown_file (base.py:178) — so an adjacency scan
    returns nine functions containing none of those five while this criterion''s map
    names four of them as propagating members and one as an insulated loader, which
    is red on a correct implementation and whose cheap repair deletes the four conveniences
    that are the whole reason this clause exists (the round-14 keying error, recurring
    inside round 14''s own remedy). The closure STOPS at any function another criterion
    has already assigned a disposition to, and the STOP SET IS COMPUTED, NEVER NAMED
    (round-16 finding): it is the union of THREE contributions, each CONSUMED AS THE
    LIVE OUTPUT of a derivation another criterion''s test already runs — those scans
    reused as inputs, never re-stated as a list here. A live output is only consumable
    in the domain the closure is computed in, and two of the three are NOT in that
    domain as their own AC produces them (round-18 audit-fold), so each contribution
    carries its own conversion and none may be repaired by naming. (i) REFUSING WRITERS:
    AC-1''s data-flow scan output, taken directly — already a set of functions, no
    conversion. (ii) INSULATED LOADERS: NOT AC-3''s output as AC-3 produces it. AC-3''s
    test-time derivation discovers CLASSES (an AST scan for BaseRepository subclasses,
    checked against its 4x3 matrix''s class keys), and a class is not a member of
    a closure over functions — so consuming AC-3''s output literally contributes NOTHING
    to the stop set, the closure never stops at base._load_file, and it climbs through
    load(), get_all() and resolve() into every consumer-facing method, which is the
    unbounded walk the stop rule exists to prevent. The conversion is REQUIRED and
    belongs to this criterion: resolve each class AC-3 discovers to the function implementing
    its _load_file through that class''s MRO, then DEDUPLICATE, because the map is
    many-to-one. Four discovered classes resolve to THREE functions today — PersonRepository
    (person.py:159) and CompanyRepository (company.py:46) declare no _load_file and
    both resolve to base.py:171, while meeting.py:64 and book.py:57 are their own
    — so a check asserting one loader per discovered class is RED on a correct implementation
    (the round-14 keying error in the shape this document has carried since round
    5''s class/path asymmetry), and both counts are today''s baseline, not the answer.
    (iii) The C3 GUARD: likewise not consumable from AC-4, which runs NO scan at all
    — it names write_markdown_file and asserts two fixtures — so "AC-4''s live output"
    does not exist, and the only repair available to a builder reading it that way
    is to hardcode the name, which is the frozen list this clause abolished reappearing
    inside the clause itself. It IS computed, from a derivation already required to
    run: AC-1''s discrimination proof evaluates TWO predicates over one traversal
    — the loose "calls parse_frontmatter and later writes" and the data-flow one —
    and this contribution is their SET DIFFERENCE (loose MINUS data-flow), which is
    precisely the function AC-1 must REACH and REJECT, today write_markdown_file alone.
    AC-4 dispositions that function; AC-1''s scan derives it; neither names it into
    this stop set. IDENTITY DOMAIN: all three contributions, and the closure itself,
    are normalised to ONE source-stable function identity before any set operation
    — module path plus qualified function name (the function-level half of AC-5''s
    site identity) — never a line number, and never AST nodes for one set against
    imported objects or classes for another, because a partition asserted across mixed
    identity domains is vacuously satisfiable: nothing in one domain ever equals anything
    in another, so the assertion passes while proving nothing. The function names
    in this document (update_fields, update_frontmatter_field(s), roundtrip_file;
    base/meeting/book _load_file; write_markdown_file) are today''s baseline listing,
    not the specification; a check that hardcodes them does not satisfy this criterion,
    because a fifth writer AC-1''s scan auto-discovers would fall outside a frozen
    stop list and either unbound the closure or leave one function claimed by two
    ACs with incompatible dispositions (refuse vs. propagate). This is the last named
    set in the document made derived: every other sweep already forbids a hardcoded
    list, and the stop set is those sweeps'' own outputs composed. That is what makes
    the closure terminate and what makes "exactly one class" well-defined; without
    the stop rule it climbs through load(), resolve() and every consumer-facing method
    in the package. PARTITION: the three computed stop sets plus the propagating residue
    must partition the computed closure EXACTLY, asserted by computation over the
    normalised identity above — a closure member landing in no class, or in two (the
    refuse-vs-propagate collision), FAILS this criterion; the partition assertion
    is what makes the four ACs'' sweeps verify each other''s boundaries instead of
    merely coexisting. Because a partition over an empty or mis-domained contribution
    degenerates into "everything is residue" while still reading green, each of the
    three contributions must additionally be asserted NON-EMPTY and asserted to be
    a SUBSET of the computed closure — that is the assertion that catches a loader
    contribution left as four class objects, and it is why the conversions above are
    stated as requirements rather than as implementation notes. ONE IMPLEMENTATION
    (round-18 gate finding, folded at round 19 — the label, not the clause, was the
    round-20 gate''s MINOR): the derivations this criterion consumes and the derivations
    their home criteria run are THE SAME CODE, never same-typed reimplementations
    — the file-set walk, the loose and data-flow write-path scans, the subclass scan
    and its MRO resolution, and the closure computation live in ONE shared importable
    scan module, and every consuming test imports it from there. THIS test SELF-CERTIFIES
    that import inside its own named check, which is the only form of the obligation
    this fence can grade (round-22 finding): for every derivation callable it invokes,
    it asserts that callable''s __module__ is the shared scan module''s, asserted
    on the SAME binding it computes the closure and the stop set with — so a private
    copy substituted for the computation turns THIS check red rather than leaving
    the obligation to a sibling. What this fence must NOT do is assert IMPLEMENTATION
    IDENTITY by comparing the callables it imported against themselves (round-20 finding):
    that comparison is vacuously true while a sibling test runs an untouched private
    copy, and closing it is what round 21 was folded for. Identity is proven instead
    by DEFINITION-SITE UNIQUENESS — the copy is shown not to be able to EXIST rather
    than compared against — and that property is carried by AC-7 under ITS OWN check
    (test_derivations_are_single_sourced), never by a check named only in this fence''s
    prose: a criteria fence carries exactly one check, which is why AC-6 was split
    out of AC-3, so a check named in a desc and owned by no fence is graded by nothing
    — the same unenforced-prose failure the round-20 gate found one level up, reproduced
    by the remedy for it. Uniqueness-by-scan rather than identity-by-comparison is
    what makes the property hold for tests that never touch this partition check at
    all. Two independently-written predicates that agree on today''s tree can silently
    diverge on the first future write path, reproducing the exact refuse-vs-propagate
    collision this composition exists to prevent while every fence reads satisfied
    — output agreement today is not implementation identity tomorrow; solve-in-one-place
    applies to the harness. Every member of the closure is classified into exactly
    ONE of four caller classes: refusing writer (AC-1''s data-flow sweep), insulated
    repository loader (AC-3''s per-class except + skip surface), the C3 guard (AC-4''s
    write_markdown_file, which discards the parse), or PROPAGATING PUBLIC PARSE SURFACE
    — the closure''s residue, today exactly six and computed rather than named: parse_markdown_file
    (parser.py:174-176), parse_markdown_content (201-202) and the four typed conveniences
    (216-237), none behind a try/except. Six is today''s baseline, not the expected
    answer. The test asserts the computed closure equals the classification map''s
    keys in BOTH directions — a discovered function fitting no class FAILS this criterion,
    AND a class member the closure does not discover FAILS it too, because the one-directional
    form is exactly what lets an under-generating scan read as satisfied. For every
    member of the propagating class: on malformed frontmatter the typed parse error
    PROPAGATES to the caller — asserted by invoking each DISCOVERED member on the
    malformed fixture and catching the typed error, never assumed from the call graph
    — and on absent frontmatter and on a legitimately unknown/unmodelled type each
    keeps today''s return exactly (parse_person on fence-less non-person content returns
    None today and still does; malformed stops being conflated with either). Export
    status is stated from source, never from reputation and never from a repository
    this floor cannot read: __init__ exports parse_frontmatter, parse_markdown_file
    and ParsedDocument only (__init__.py:35-39, 102-103); parse_markdown_content is
    README-documented (README.md:160, 176) and exercised by this suite (tests/test_parser.py:13);
    the four conveniences carry no __init__ export and parse_person is exercised by
    this suite (tests/test_parser.py:14). Whether any consumer OUTSIDE this repo calls
    them is NOT asserted here — that audit is cross-repo, unavailable to a hermetic
    floor, and parked with N4''s companion item (Non-goals); claiming it verified
    would re-import the unverifiable clause the first fold removed. The propagating
    class is swept regardless, because importable-by-module-path is public.

    kind: test

    check: test_parse_boundaries_distinguish_failure_from_empty

    ```


    why: C2 and C5 are the same defect one layer apart — a parse failure rendered
    as the success-shaped value a legitimate empty/unknown case also produces; enumerating
    the return sites is what makes the property total over the class instead of true
    for the one fixture someone picked, and it is what surfaced the unclosed-fence
    case two parts of this package already disagree about. Separating the return sites
    from the outcome classes is what makes that enumeration runnable rather than merely
    stated: the function has four `return` statements and five outcomes, so an AC
    that calls all five "return sites" is red against a faithful scan and green the
    moment the builder deletes the outcome that has no site of its own — which is
    the empty-fence case, the one that only exists in the list because it is reached
    through a shared return. Keying the map by what the scan can return, letting a
    site carry several classes, and requiring each class its own input is the only
    shape that keeps both halves honest. And walking the package''s files on disk
    rather than its imported modules is what stops the whole clause resting on a coincidence:
    every module here is transitively imported today, so an `inspect`-based scan would
    look complete while proving nothing about the next module nobody wires up. The
    invocation-surface clause is the round-14 finding folded under totality: the seam''s
    loudness travels to every caller, and the other sweeps each cover a class of caller
    — writers that refuse (AC-1), loaders that insulate (AC-3), a guard that must
    not re-swallow (AC-4) — so the remaining class, the public parse functions that
    neither refuse nor insulate, had to be named and asserted as PROPAGATING, or the
    item ships a README-documented entry point whose behaviour under the new failure
    mode nobody specified. Classifying every discovered caller into exactly one class
    is what makes the coverage claim checkable: a future caller lands in a class or
    turns the suite red, instead of waiting for a fifteenth red-team round to notice
    it. And making that sweep a transitive CLOSURE rather than a list of direct callers
    is what makes it return the members it was written for at all: four of the six
    propagating functions never name the seam — `parse_person` and its three siblings
    reach it through `parse_markdown_content`, one call away — so an adjacency scan
    discovers neither them nor `base._load_file`, leaves four map entries matching
    nothing, goes red on a faithful implementation, and is repaired by deleting exactly
    the README-shaped entry points round 14 was raised about. A closure with a stated
    stop rule (another criterion has already dispositioned this function) terminates,
    covers them, and keeps "exactly one class" meaningful; asserting the equality
    in both directions is what stops an under-generating scan from reading as satisfied,
    which is the same lesson as AC-1''s proven negative seen from the other side —
    a scan has to be shown both to reach what it must classify and to reject what
    it must not. And spelling out how each stop contribution is *obtained* is what
    makes "consume the sibling''s derivation" executable rather than aspirational:
    two of the three siblings cannot hand this closure a set of functions as they
    stand — AC-3 derives classes, and AC-4 derives nothing at all — so a builder reading
    round 17''s clause literally gets an empty stop set from AC-3 (the closure then
    eats `load()`, `resolve()` and the whole public repository surface) and, from
    AC-4, nothing to call but the hardcoded name the clause exists to forbid. Naming
    the MRO resolution and the many-to-one collapse for the loaders, and sourcing
    the guard from the set difference AC-1''s discrimination proof already computes,
    is what turns the composition into an operation instead of a cross-reference;
    requiring each contribution to be non-empty and inside the closure is what stops
    a mis-typed contribution from degrading the partition into a tautology that passes.
    And naming the deciding input for "known type" is what keeps this criterion''s
    `parse_to_model` half from being satisfiable in the direction that breaks the
    tree: the branch this document''s own prose describes — read the `type`, resolve
    a model, return `None` when nothing resolves — is the branch **no caller in scope
    reaches**, since `base._load_file` and all four conveniences force the class,
    so "known" read as "a model class was supplied" is the most direct reading available
    to a builder once the auto-detect path is out of the picture, and it makes `parse_person`
    raise on a well-formed company note. That is not a hypothetical: `test_parse_person_wrong_type`
    (tests/test_parser.py:265-273) asserts the `None` today, it is one of the 607
    baseline cases this item may not touch, and the "book where a person was expected"
    Example of done requires it in Dave''s own terms. Deciding known-ness on the note''s
    raw declared `type` against the type the class itself declares is round 4''s remedy
    — ownership read before and independently of `model_validate` — applied one layer
    below the loaders it was written for, and pinning the two fixtures in one test
    is the only shape that proves both halves, because the drifted note alone looks
    exactly like the property while the foreign note is the one that regresses.


    ```criteria

    id: AC-3

    desc: A batch load survives a bad note, surfaces it at WARNING (never DEBUG),
    and surfaces ONLY the notes that repository owns — proven over the COMPLETE derived
    4x3 matrix, one worked fixture set PER repository class, each derived from that
    class''s OWN model fields and its OWN _load_file structure (never transposed by
    hand from a sibling): (1) PersonRepository (inherits base._load_file base.py:171-183,
    glob @*.md, isinstance-after-construction) — (a) malformed-YAML @-note in its
    skip surface; (b) own-type-drifted type person + emails "not-a-list" (Person.emails
    List[str], models.py:81) MUST be listed; (c) foreign readable type (@Acme.md type
    company) MUST NOT be listed. (2) CompanyRepository (same inherited path and glob,
    independently instantiated and independently asserted in BOTH directions — sharing
    code is not sharing proof) — (b) type company + tags "not-a-list" (its only list
    field is the INHERITED BaseEntity.tags, models.py:40 — derived, not transposed);
    (a) and (c) mirrored with company-owned fixtures. (3) MeetingRepository (OWN _load_file
    meeting.py:64-83, glob "Meeting *.md", raw-type prefilter meeting.py:72-75 BEFORE
    parse_markdown_file, own except meeting.py:81-83) — (a) malformed-YAML "Meeting
    X.md" listed; (b) type meeting + attendees "not-a-list" (Meeting.attendees List[str])
    MUST be listed — this fixture passes the prefilter and fails only inside parse_markdown_file,
    exercising meeting.py''s except under the new failure mode; (c) a "Meeting Y.md"
    with type person excluded via the prefilter (the naming-convention glob makes
    strays rare — asserted anyway, reasoning stated). (4) BookRepository (OWN _load_file
    book.py:57-79, CATCH-ALL glob *.md book.py:49-51, prefilter book.py:67-70, own
    except book.py:77-79) — (a) a malformed-YAML note of any type under the catch-all
    glob (the @John.md of fixture (1)(a)) MUST NOT be listed, since neither kind of
    ownership evidence survives — the glob is not a naming convention and the type
    is unreadable; (b) type book + tags "not-a-list" (Book declares NO own list field
    — models.py:159-170 are all str — so the inherited BaseEntity.tags at models.py:40
    is the derivation, reached from Book''s own field list rather than copied from
    Company''s) MUST be listed, the catch-all glob being irrelevant once the raw type
    reads "book"; (c) a well-formed foreign note (@Sarah.md type person) MUST NOT
    be listed, excluded by the prefilter at book.py:70. The twelve cells do NOT share
    one expectation table and a test that parametrizes over the four classes against
    a single expected result is wrong by construction — fixture (a) is MUST-be-listed
    for PersonRepository, CompanyRepository and MeetingRepository (owned by naming
    convention, the C4 keystone) and MUST-NOT-be-listed for BookRepository alone,
    while fixture (b) is MUST-be-listed for all four and fixture (c) MUST-NOT-be for
    all four. The heterogeneous-vault requirement stands (one vault mixing @-notes,
    Meeting-notes, and bare-titled book notes). For EVERY one of the twelve cells
    additionally assert NO-ABORT — the fixture''s failure is caught inside that class''s
    OWN _load_file and never propagates into BaseRepository.load()''s bare for-loop
    (base.py:157-165 has NO try/except — one escaped exception aborts the whole batch,
    the C4/HAL9000-startup regression), so any implementation that narrows meeting.py''s
    or book.py''s except clause must still catch the new typed validation failure,
    and the test proves it per class rather than assuming the base-path result transfers.
    The CLASS LIST itself is DERIVED BY THE TEST AT TEST TIME, not written into it
    — and derived at SOURCE level, never from the import graph: the test enumerates
    the PACKAGE''s module files on disk — every .py under obsidian_schemas/, walked
    recursively, the SAME derived file set AC-1, AC-2 and AC-5 walk, and NOT the repositories/
    subdirectory alone (round-14: nothing requires a fifth repository to live under
    repositories/, and a source scan scoped to a directory is the frozen list wearing
    a path — as blind to a module outside it as __subclasses__() is to a module nobody
    imported) — and scans their AST for classes deriving (directly or transitively)
    from BaseRepository, importing each discovered module itself, and asserts that
    discovered set equals exactly the classes its matrix holds cells for — so a fifth
    subclass added later arrives as a key with no entry and turns the suite red, forcing
    whoever adds it to state its three answers. A runtime __subclasses__()-style check
    does NOT satisfy this clause (round-12 finding): __subclasses__() sees only classes
    whose modules happen to be imported by test time, so a fifth repository module
    not wired into repositories/__init__.py would be silently invisible — reproducing,
    inside the discovery clause itself, the exact green-suite/zero-coverage gap it
    exists to close. Concreteness is still decided by the ABC contract (abstract entity_type/type_name,
    base.py:120-130), but membership is decided by the source on disk. This is the
    property the Exploration Notes have claimed since round 1 ("a fourth repository
    joins automatically") and that no check enforced until now; a check that hardcodes
    the four class names does not satisfy it. Round 6''s ruling is untouched: the
    twelve CELLS stay explicit and hand-derived because their answers are non-uniform
    and the matrix IS the specification — deriving the class list is precisely what
    keeps that explicit map from silently going stale. The map is keyed by class,
    the scan supplies the keys, and an unmapped key FAILS rather than passes. SHARED
    IMPLEMENTATION (round-20 finding): the file-set walk and the BaseRepository-subclass
    scan are DEFINED IN the one shared importable scan module AC-2 requires, and THIS
    test obtains them FROM IT BY IMPORT — never as helpers private to this test module,
    and never nested inside the test function. A locally re-implemented copy FAILS
    this criterion even when it returns the same four classes on today''s tree — and
    that failure is ASSERTED BY THIS CHECK (round-22 finding): this criterion is graded
    by test_batch_load_survives_and_surfaces_only_owned_bad_notes passing and by nothing
    else, so an import obligation stated only as a writing instruction is satisfied
    by a test that never imports anything. This test therefore asserts, of the SAME
    bindings it derives its class list with, that each one''s __module__ is the shared
    scan module''s — a subclass scan defined privately here carries this test module''s
    __module__ and turns THIS check red. It must be true here because AC-2''s stop
    set consumes this scan (resolving each discovered class through its MRO to that
    class''s _load_file implementation, the conversion AC-2 owns), and an identity
    assertion made in AC-2 can only bind to a callable another module can reach —
    so a scan nested in this test''s function would leave AC-2 comparing the shared
    module to itself while this criterion ran a private copy. AC-7 covers the complementary
    case of a second definition site that exists whether or not this test uses it.
    A fifth repository that one copy discovers and the other misses then leaves base._load_file
    (or the new loader) outside the stop set, and the closure climbs through load(),
    get_all() and resolve() — the unbounded walk the stop rule exists to prevent —
    while both tests read green.

    kind: test

    check: test_batch_load_survives_and_surfaces_only_owned_bad_notes

    ```


    why: C4 is the duplicate-creation engine — an invisible note makes resolve() miss
    and find_or_create_stub mint a dup; a queryable skip-list is required because
    a log line is exactly the mechanism that already failed, and the schema-drift
    fixture is required because "unparseable-or-invalid" otherwise reads satisfied
    while half the same consequence is never exercised at the repository level. That
    fixture has to be its OWN file, distinct from the foreign-type one, because the
    two are the same code path with opposite answers: the natural way to exclude a
    well-formed @Acme.md from PersonRepository''s skip-list — "if the model failed
    to build, it isn''t mine" — also excludes an owned @Broken.md carrying type: person
    with a non-coercible field, which is precisely the note whose disappearance mints
    the duplicate. One fixture cannot prove both halves; forcing three files and forbidding
    ownership to be read off model construction is what makes the skip-list mean "these
    are mine and they need attention" rather than "these are the ones I happened to
    be able to parse." Deriving the fixture space from each repository''s own glob
    is what stops the surface being trustworthy in the test and noise in production:
    every repository globs files it does not own and decides ownership downstream
    of the parse this item makes loud, so on a real heterogeneous vault a naive fix
    reports every company note as a skipped person, every person note as a skipped
    company, and every malformed note anywhere in the vault as a skipped book. A signal
    that cries wolf on day one fails the same way the unread DEBUG line fails, and
    asserting the surface in both directions — owned bad note present, decidably-foreign
    note absent — is the only form a single-type fixture cannot fake. Sweeping the
    four repository CLASSES rather than the three `_load_file` code paths applies
    that same rule one level out: `PersonRepository` and `CompanyRepository` are two
    classes sharing one inherited implementation and one glob, and the healthy-vault
    exposure between them runs both ways, so a test that instantiates only the first
    proves half a property. The natural implementation — a shared `_owns()` on `BaseRepository`
    — is precisely the kind that reads `self.type_name` correctly for the class that
    was exercised while a hardcoded, inverted, or mis-ordered comparison goes unnoticed
    for the class that was not, which is why the AC counts instantiated classes and
    not code paths. Writing all twelve cells out rather than parametrizing over four
    is the same rule once more: the members do not share an answer — `BookRepository`''s
    malformed-note cell is MUST-NOT-be-listed where the other three are MUST-be-listed
    — so a sweep with one shared expectation table asserts a uniformity nobody checked,
    and gets the one member wrong in the direction that floods the surface with every
    bad note in the vault. And fixture (b) is required from every chair, not just
    the two whose `_load_file` is `base`''s, because it is the only cell that carries
    this item''s *new* signal through `meeting.py`''s and `book.py`''s own except
    clauses: those two already prefilter on the raw `type` (meeting.py:72-75, book.py:67-70),
    so their foreign-type direction is sound today and their own-type-drifted note
    is the one that reaches code no fixture has ever exercised. The NO-ABORT half
    is there because `BaseRepository.load()` (base.py:157-165) wraps `_load_file`
    in no `try`/`except` at all — each class''s own clause is the entire safety margin,
    AC-6 makes narrowing such clauses this item''s house style, and a narrowed catch
    that misses the new typed failure turns "one note skipped" into a dead `BookRepository`/`MeetingRepository`
    load. That is the startup regression the whole item exists to prevent, so it is
    asserted per class rather than inferred from the base path passing.


    ```criteria

    id: AC-4

    desc: The WI-126 body-shrink guard refuses when it cannot verify, and does not
    re-swallow the signal AC-1/AC-2 introduce. write_markdown_file''s guard (writer.py:184-195)
    raises rather than setting existing_body = "" for BOTH required fixtures — (a)
    the existing file''s frontmatter is malformed YAML, the coupling case the Constraints
    section flags as highest-risk, since post-AC-2 parse_frontmatter raises there
    and today''s bare except Exception would re-bury it; and (b) the existing file
    cannot be read at all (permission or IO error). Naming (a) explicitly is required:
    a test built only around a generic read error would satisfy the guard''s wording
    while never proving the coupling holds. The except clause is narrowed so neither
    case reaches existing_body = "", and the guard''s refusal is distinguishable from
    BodyTruncationError. This criterion runs NO scan and derives nothing, which is
    deliberate and is why AC-2 does not consume it (round-18 finding): the identity
    of the function dispositioned here — write_markdown_file — is supplied to AC-2''s
    stop set by AC-1''s own derivation, as the SET DIFFERENCE between AC-1''s loose
    "calls parse_frontmatter and later writes" predicate and its data-flow predicate,
    computed in the one shared scan module. The name written into this fence is today''s
    baseline, not the specification: if a second guard of the same shape is ever added,
    AC-1''s set difference discovers it and AC-2''s stop set gains it without this
    fence being edited, and this criterion''s fixtures then need extending — which
    is a red test there, not a silent gap here.

    kind: test

    check: test_body_guard_refuses_when_unverifiable

    ```


    why: C3 is the one mechanism protecting against body-wipe turning itself off exactly
    when it cannot confirm it is safe; it sits directly downstream of parse_frontmatter,
    so the malformed-YAML fixture is the whole point — without it C3 lands green and
    silently re-opens C2 on the overwrite path.


    ```criteria

    id: AC-5

    desc: Write paths make genuine failure raise while every legitimate no-op keeps
    its current return value. The test classifies every falsy-return site in the package''s
    write paths and section-read helpers, DERIVED by FOUR predicates rather than by
    a name list, so a site added later joins the sweep automatically. Predicate 1
    is the blanket except Exception in a writer (writer.py:259 and 298; person.py:1500,
    1603, 1702, 1775, 1837) - a genuine I/O failure (disk full, torn write, permission
    denied) raises a typed ValueError subclass, so it can no longer be misread as
    a no-op and a consumer''s existing except ValueError still catches it. Predicate
    2 is the frontmatter-fence split (content.startswith("---") followed by split("---",
    2)), which yields FIVE sites in person.py rather than the single function earlier
    rounds named - append_to_body_section (1558-1570), add_to_discuss_item (1675-1683),
    update_to_discuss_item (1734-1742) and remove_to_discuss_item (1801-1809), where
    "no fence" and "malformed fence" are pseudo-no-ops that are really failures and
    move to the raise side for ALL FOUR, so neither can keep returning the same False
    a legitimate item-not-found returns; plus the read helper _get_body_content (1622-1626),
    which today falls through to return content and hands its caller the whole file,
    frontmatter included, as body. Being a read it surfaces rather than raises, but
    the test must assert a caller can distinguish an unsplittable fence from a genuinely
    empty body, so get_to_discuss_items can no longer report a broken-fence note as
    having no items. Predicate 3 is the guaranteed-section insertion writer - a writer
    that inserts caller-supplied content at a named section marker and returns falsy
    when the marker is absent - which run over the package yields exactly ONE member,
    append_to_timeline (marker-absent branch person.py:1482-1484, plus its structurally-dead
    split guard 1491-1492 - the marker was just confirmed present, so split(timeline_marker,
    1) cannot yield fewer than two parts). Disposition (round-9 finding, Dave-ruled
    2026-07-24): ACCOMMODATE, not raise - on a note without a "## Timeline" marker
    the call auto-creates the section, inserts the entry, and returns True with the
    entry readable back, mirroring the create_if_missing=True default its sibling
    append_to_body_section already has for the identical ambiguity. The person template
    guarantees "## Timeline" on package-created notes (body_sections.py:305-306, written
    by create_stub via get_default_body, person.py:1440), but a raw-content check
    cannot distinguish "corrupted since creation" from "legitimately never had one"
    (hand-created in Obsidian, or predating the template convention - the scenario
    round 6 itself named), so refusal would manufacture a failure out of a structural
    variant; accommodation eliminates the STRUCTURAL drop - the caller''s entry can
    no longer vanish into the same False the dedup no-op returns because the section
    was missing - without inventing a new failure mode. Marker-absent must never again
    return False, and the dedup branch (1476-1478) stays a legitimate no-op with its
    exact current False. PRESERVATION (round-10 audit-fold, and non-negotiable, because
    the sibling this disposition mirrors is lossy in exactly the case the disposition
    serves): the auto-create must leave the note''s pre-existing body content ENTIRELY
    present and its frontmatter BYTE-IDENTICAL, asserted on two fixtures derived from
    the failure mode of the naive implementation rather than from a convenient note
    - (i) a person note whose body has NO "## " heading at all (free text only), and
    (ii) a person note with body text ABOVE its first "## " heading. Both are destroyed
    today by the sibling''s own absent-section route: append_to_body_section with
    create_if_missing=True calls append_to_section/prepend_to_section (person.py:1586-1593),
    which are parse_body_sections -> mutate -> write_body_sections (body_sections.py:241-252,
    209-220); parse_body_sections keeps ONLY "^## "-delimited spans (body_sections.py:74-97)
    and returns an empty OrderedDict when there are no headings (76-78), and write_body_sections
    rebuilds the body from that dict alone (100-134), so fixture (ii) loses its preamble
    and fixture (i) loses its whole body. Nothing downstream catches it: append_to_timeline
    and append_to_body_section both write via a raw file_path.write_text (person.py:1495,
    1597) and writer.py:178-183 exempts exactly these "section writers" from the WI-126
    body-shrink guard (writer.py:184-195) that AC-4 hardens. A fix that satisfies
    "the entry lands" by routing the absent-section case through today''s body_sections
    round-trip FAILS this criterion. The mechanism is open (string insertion, or making
    the section round-trip content-preserving - the latter repairs the sibling''s
    identical latent wipe at the same time and is the "solve in one place" answer),
    and adding a caller-facing create_if_missing-style parameter to append_to_timeline
    is permitted but NOT required: Dave''s ruling is that the default accommodates.
    Also assert idempotence - after the auto-create, a second call with the same deduplicate_key
    returns the frozen dedup False and the note holds exactly ONE "## Timeline" section.
    append_to_body_section is NOT a P3 member (its absent-section behaviour is already
    an explicit contract governed by create_if_missing), and the To-Discuss match-mutation
    writers are not members because a falsy return there drops no caller payload (see
    the no-op half). Predicate 4 is the existence pre-check returning falsy in a writer
    whose package siblings raise for the same condition - update_frontmatter_field
    (writer.py:242-243) and update_frontmatter_fields (writer.py:281-282) return False
    for a missing file where person.py''s five writers raise ValueError (e.g. 1469-1470)
    and base.update_fields raises FileNotFoundError (base.py:305-308); both move to
    the raise side, converging on the convention the package already has. No-op half
    - DERIVED by predicate as well, never by a citation list: (a) dedup-key match
    (append_to_timeline 1476-1478; append_to_body_section 1583-1584) - noting explicitly
    that append_to_timeline''s dedup is WHOLE-FILE (deduplicate_key in content, person.py:1476)
    while the sibling''s is section-scoped, deliberately per person.py:1521-1524,
    so a key already present in another section still returns False and still writes
    nothing even on a Timeline-less note; that is frozen by this AC''s own backward-compat
    half and is therefore the ONE remaining falsy path by which an entry does not
    land, which is why the P3 claim is scoped to STRUCTURAL absence rather than stated
    as "a drop is impossible"; (b) governed absence - create_if_missing=False with
    the section absent (append_to_body_section 1578-1579); (c) match-not-found in
    a match-mutation writer, where a section-absent return is the degenerate case
    of the named item not being there and no caller payload is dropped (update_to_discuss_item
    1746-1747 section-absent and 1759-1761 item-not-found; remove_to_discuss_item
    1813-1814 section-absent and 1822-1824 item-not-found). (d) a helper''s falsy
    return that its ONLY caller already makes loud - _get_body_content''s missing-file
    None (person.py 1616-1617), which get_to_discuss_items converts to a ValueError
    at person.py 1641-1643, so it is already distinguishable at every call site there
    is. Every (a)-(d) case returns the SAME falsy value it returns today, so an existing
    caller''s `if not repo.append_to_body_section(...)` branch keeps its current meaning.
    Net contract change is one-directional - no consumer-visible return value changes
    except where it was reporting a failure as a no-op. CLOSURE - the four derivation
    predicates are not merely asserted exhaustive, the test PROVES them so, because
    a predicate list is itself a sample until its universe is enumerated. The test
    enumerates every return site in the package''s write paths and shared section-read
    helpers that does NOT report a completed write - the falsy returns plus _get_body_content''s
    whole-file fall-through at person.py 1626 - which today is exactly 28 sites (writer.py
    243, 260, 282, 299; person.py 1478, 1484, 1492, 1502, 1563, 1570, 1579, 1584,
    1607, 1617, 1626, 1681, 1683, 1704, 1740, 1742, 1747, 1761, 1777, 1807, 1809,
    1814, 1824, 1839) and nothing else in the package, since company.py, meeting.py
    and book.py declare no bool-returning writer at all - which is also what makes
    append_to_timeline P3''s only member by enumeration rather than by inspection.
    Every one of the 28 must fall into exactly ONE of the raise predicates P1, P2
    and P4, the accommodate predicate P3, or the no-op classes (a)-(d), and a site
    matching none of the eight FAILS this criterion rather than passing unnoticed,
    so the next un-derived predicate arrives as a red test instead of as another red-team
    round. The enumeration is performed BY THE TEST, AT TEST TIME, against the LIVE
    POST-FIX source - an AST scan (NEVER inspect-based: inspect enumerates module
    objects, which exist only for modules something imported, so it carries the identical
    blind spot AC-3 rejects __subclasses__() for, and reads complete today only because
    every module in this package happens to be transitively imported) over the package''s
    module files WALKED ON DISK (every .py under obsidian_schemas/, recursively -
    the same derived file set AC-1, AC-2 and AC-3 walk, and NOT the two modules today''s
    28 sites happen to live in: a sixth To-Discuss-style writer copy-pasted into a
    NEW module beside person.py is exactly as invisible to a scan scoped by a hand-written
    module list as it is to the import graph) for return sites in write paths and
    shared section-read helpers that do not report a completed write, checked against
    an explicit in-test classification map (site -> P1/P2/P3/P4/(a)-(d)) keyed by
    a SOURCE-STABLE site identity - module, plus qualified function name, plus the
    site''s ordinal within that function - never by line number (this fix shifts every
    line number in person.py, so a line-keyed map turns unrelated edits red) and never
    by function name alone (append_to_timeline holds four sites landing in three different
    buckets, so a function-keyed map cannot express the classification at all) - and
    never a hand-derived list frozen at build time: 28 is today''s baseline count,
    not the expected answer, because the fix itself adds code (P3''s accommodation
    gives append_to_timeline an absent-section branch it does not have today, and
    any frontmatter-fence split it acquires on the way joins P2 by predicate rather
    than becoming a 29th silent False), and because the forward-looking guarantee
    is the point - a sixth To-Discuss-style writer copy-pasted into person.py next
    month must turn the suite red by appearing in the scan unclassified, not wait
    for a human to re-read the module; a check that hardcodes the 28 line numbers
    reads green on that future writer and therefore does not satisfy this criterion.
    Out of universe by construction, and named so the exclusion is explicit rather
    than silent - pure predicates (phones_match, person.py 136 and 156) and lookup-miss
    None returns (person.py 429, 441, 498, 530, 1012, 1065; company.py 114, 134; meeting.py
    357, 387; book.py 243, 269), which are AC-2/AC-3 territory - a lookup miss is
    an answer to a question, not an unreported write. SHARED IMPLEMENTATION (round-20
    finding) - the file-set walk this criterion shares with AC-1, AC-2 and AC-3, and
    the falsy-site universe scan itself, are DEFINED IN the one shared importable
    scan module AC-2 requires, and THIS test obtains them FROM IT BY IMPORT, never
    as helpers private to this test module and never nested inside the test function.
    A locally re-implemented copy FAILS this criterion even when it returns the same
    28 sites on today''s tree, and that failure is ASSERTED BY THIS CHECK (round-22
    finding): nothing grades this criterion except test_write_failure_raises_and_noops_keep_their_return
    passing, so an import stated as a writing instruction is unenforced - a private
    walk that finds the same 28 sites reads green. This test therefore asserts, of
    the SAME bindings it enumerates the universe with, that each one''s __module__
    is the shared scan module''s; a copy defined here carries this test module''s
    __module__ and turns THIS check red. The stake is that four criteria walk the
    same file set, and four hand-written walks that agree today are four things to
    keep in step tomorrow - the module added beside person.py that one walk finds
    and another misses is exactly the case every one of these sweeps exists to catch,
    and it would be missed by the one that matters while the others read green. AC-7
    proves the second definition site cannot exist at all, which covers the copy nobody''s
    assertion happens to touch. Solve-in-one-place applies to the harness, and it
    is why this obligation is both stated and ASSERTED by each criterion that PRODUCES
    a derivation rather than only by the one that consumes them.

    kind: test

    check: test_write_failure_raises_and_noops_keep_their_return

    ```


    why: N4 collapses "your data was skipped on purpose" and "your data was lost"
    into one bare False. The original wording bundled a cross-repo consumer audit
    that nothing in this repo can verify — HAL9000 is not in this tree, the floor
    is hermetic, and no runner is registered here that could lint another repo — so
    the audit is parked (Non-goals) and replaced by the strongest property that IS
    provable locally: the no-op returns are frozen, so the only behaviour any existing
    consumer sees change is a silent data-loss becoming loud. Naming a second derivation
    predicate rather than one function''s branches is what makes that total: the fence-split
    shape is copy-pasted across four writers, so fixing only the one a prior round
    happened to cite would leave update_to_discuss_item still reporting a corrupted
    fence as "nothing matched" — and running the predicate is what exposed the fifth
    site, a read helper that answers a broken fence by returning the frontmatter as
    body. The third and fourth predicates are the round-7 re-derivation''s, and both
    are the same lesson at new seams: append_to_timeline''s marker-absent False is
    the only falsy return in the package that silently discards caller-supplied content
    on a note whose own template guarantees the write target exists — the N4 story
    in one line, indistinguishable today from "already there, skipped on purpose"
    — with accommodation rather than raise as its remedy, because round 9 showed a
    raw-content check cannot tell "corrupted since creation" from "legitimately never
    had one" while the sibling writer already solves that exact ambiguity with create_if_missing,
    so P3 converges on the sibling''s semantics (the entry lands whatever the note''s
    structure, and no legitimate structural variant is manufactured into a failure).
    The PRESERVATION half is what makes that convergence safe rather than merely recorded:
    read at source rather than taken from its contract, the sibling''s absent-section
    route rebuilds the body from `parse_body_sections`, which keeps only `^## `-delimited
    spans — so it deletes a preamble and destroys a heading-less body outright, on
    a write path writer.py:178-183 deliberately exempts from the WI-126 body-shrink
    guard. That is the body-wipe class AC-4 exists to harden, reached by this item''s
    own remedy, and it lands on precisely the hand-created-in-Obsidian note the accommodation
    was ruled in to serve — so mirroring the sibling naively would trade a silently
    dropped entry for a silently dropped note body, which is worse than the defect.
    Pinning the two fixtures that break the naive implementation (heading-less body,
    preamble body) is what forces the implementation to be content-preserving rather
    than merely section-creating, and fixing it at the `body_sections` round-trip
    repairs the sibling''s identical latent wipe in the same move. The same read forced
    the honest scoping of the claim: dedup is whole-file by deliberate design (person.py:1476,
    1521-1524) and is frozen by this AC''s own backward-compat half, so *structural*
    absence can no longer drop an entry — a drop is not "impossible", and saying so
    would have been the kind of overclaim a later round finds. And writer.py''s existence
    pre-checks report as a no-op the exact condition every sibling writer in the package
    already raises for, so moving them is convergence on an existing convention, not
    a new contract. Deriving the no-op half by predicate rather than by citation list
    is what caught the old list being wrong in both directions — one section-absent
    site mislabeled as item-not-found, one missing entirely — and the match-mutation/insertion
    distinction is what makes the classification principled rather than curated: a
    falsy return that drops a caller''s payload is a failure, a falsy return that
    reports "the thing you named is not here" is an answer. The CLOSURE clause is
    what stops the predicate list itself being the next thing a round finds incomplete:
    five consecutive rounds ended with the class right and the members short, and
    each was answered by adding the predicate that round happened to find — which
    leaves a builder no way to know whether four is the whole count. Enumerating the
    28-site universe and requiring every member to land in exactly one bucket converts
    that from a promise into an assertion, and it is only affordable because the universe
    is this small: three of the package''s four repository modules contain no bool-returning
    writer at all, so the sweep is a closed set rather than an open-ended hunt. The
    residue it turned up — `_get_body_content`''s missing-file `None`, already made
    loud by its only caller — is precisely the kind of case that reads as a gap until
    someone checks the call site, which is why the count has to come out even rather
    than approximately.


    ```criteria

    id: AC-6

    desc: The bare except in _known_companies (person.py:1147-1160) is narrowed at
    the except clause itself, not merely re-logged. A VaultPathNotConfiguredError
    raised inside that try block PROPAGATES out of _known_companies rather than being
    swallowed — the WI-024 error this bare except currently buries — while the expected-unavailable
    case it exists for (ImportError on the CompanyRepository import) is still caught
    and still degrades to the person-company set. Changing logger.debug to logger.warning
    without narrowing the except clause does not satisfy this criterion.

    kind: test

    check: test_company_set_except_is_narrowed_not_just_logged

    ```


    why: split out of AC-3 because riding on "not swallowed to DEBUG" is satisfiable
    by a log-level change on the same bare except — precisely the move A5 rejects;
    asserting that a specific unexpected exception propagates forces the mechanism
    rather than the symptom, and a criteria fence carries exactly one check.


    ```criteria

    id: AC-7

    desc: The syntax-reading derivation CAPABILITY has exactly one home, that uniqueness
    is proven by a scan rather than asserted by an identity comparison, and the one
    derivation that does not exercise it is dispositioned explicitly rather than swept
    under the same claim. This criterion exists because a criteria fence carries exactly
    one check (the reason AC-6 was split out of AC-3), so the uniqueness property
    named in AC-2''s desc was owned by no fence and therefore graded by nothing —
    round 21''s remedy carrying round 20''s own defect one level down. The mechanism
    is CAPABILITY-LEVEL, never per-derivation (round-22 finding): the loose and data-flow
    scans both reference parse_frontmatter and differ only in a semantic property
    — adjacency vs. true data-flow — that NO detector shape can discriminate, and
    three of the six derivations share one AST-walk shape, so a per-derivation "cardinality
    exactly one" is unimplementable as written against a correct, non-duplicated tree.
    What IS decidable is the capability the syntax-reading derivation forms necessarily
    exercise: obtaining or traversing module syntax — five of the six, the sixth being
    dispositioned separately under SUFFICIENCY below rather than folded into this
    sentence (round-24 finding). The detectable marker is USE OF THE ast MODULE —
    an `import ast` or any `ast.*` attribute reference — READ OFF PARSED SYNTAX AND
    NEVER OFF SOURCE TEXT: the marker is an Import/ImportFrom node naming the module
    ast, or an Attribute node on the binding such an import creates, never a substring
    match, because this check''s OWN module necessarily carries the planted fixture''s
    source as a string literal and a text matcher therefore matches itself, making
    the exactly-one assertion RED on a correct implementation — the identical red-on-a-correct-tree
    defect the per-derivation framing was dropped for, reappearing one level inside
    its replacement if the detection level is left unstated. The check asserts the
    marker is SINGLE-HOMED: it walks a file set it DERIVES rather than names (every
    .py under obsidian_schemas/ AND every .py under tests/, recursively, discovered
    on disk, never an inspect-based or import-graph scan — a private copy in a test
    module nobody imports is exactly the copy this check exists to find) and asserts
    the marker occurs in EXACTLY ONE module, the shared scan module. That is satisfiable
    on this floor rather than red on arrival, verified live at fold time: no module
    under obsidian_schemas/ or tests/ imports or references ast today, so the shared
    scan module becomes the sole home by construction the moment it is written — and
    if a later work item gives the package a legitimate second ast consumer, this
    assertion is precisely what forces that fact to be stated (by extending this criterion)
    rather than absorbed silently. Any other module in package or tests that imports
    or references ast — a helper private to a test module, a helper nested inside
    a test function, a duplicate inside the package — FAILS this criterion, and the
    failure message NAMES the offending module, qualified name and line, because a
    red that does not say where the copy is sends the builder back to the same manual
    re-read this document has done twenty-one times. SUFFICIENCY, stated PER MEMBER
    and claiming no more than it covers (round-24 finding — the blanket universal
    was false for one of the six; completed on re-run — the second capability marker
    this fold''s first pass gave that member is RED ON ARRIVAL and is withdrawn, see
    below): FIVE of the six shared derivations — the loose scan, the data-flow scan,
    the subclass scan, the MRO resolution, the closure computation — cannot compute
    anything without traversing syntax they first obtain via ast (a copy that never
    touches syntax derives nothing), so the ast marker covers those five soundly.
    The SIXTH, the file-set walk, is pure filesystem enumeration: it touches no syntax,
    names no ast symbol, and a private copy of exactly that derivation — the least-effort
    of the six to reimplement locally, being fewer lines than the import that would
    avoid it — is invisible to the ast marker. It gets NO marker of its own, and the
    reason is a live fact rather than a preference. Capability detection works for
    ast because using ast IS this package''s derivation signature, re-verified at
    this fold: no .py file anywhere in this tree — obsidian_schemas/, tests/ or scripts/
    — imports or references ast. ".py-targeted filesystem enumeration" is NOT a signature
    but a generic operation, and this tree proves it: tests/test_vault_path_required.py:320
    already runs rglob("*.py") over obsidian_schemas/ and scripts/ as WI-024''s own
    AC-2 forbidden-default scan — a legitimate, unrelated, pre-existing second home.
    Asserting THAT marker single-homed is red on a compliant, non-duplicated tree,
    which is the identical red-on-a-correct-implementation defect the per-derivation
    framing was dropped for; and no narrowing of the pattern separates WI-024''s scan
    from a walk copy without deciding a semantic question (both rglob ".py" rooted
    at obsidian_schemas/), which is the same undecidability round 22 established.
    Exempting it by name would be the frozen list this document has abolished six
    times, and the exempted test''s own docstring rules against it ("a scan that carries
    an exception list is a scan nobody trusts"). So the walk''s uniqueness is carried
    by three stated mechanisms and this criterion claims exactly those and no more.
    (1) A walk copy that FEEDS any of the five ast-bearing derivations is caught here
    regardless, because the derivation copy it feeds is itself a second ast home —
    no walk copy INSIDE the derivation system is invisible to this check. (2) A walk
    copy that one of AC-1/AC-3/AC-5''s tests BINDS is caught by those criteria''s
    own __module__ self-certs, each of which names the file-set walk explicitly among
    the callables it certifies. (3) A walk that feeds neither — a lint helper, a later
    test that merely wants a file list — is by construction not a copy of a shared
    DERIVATION but ordinary enumeration of WI-024''s own shape; and if it is in fact
    a SEVENTH shared derivation, COMPLETENESS below requires it exported from the
    shared module and AC-2''s partition surfaces its absence. RESIDUE, stated rather
    than implied: a divergent private walk that computes no sweep and that no self-certifying
    test binds is NOT detected by this criterion, its detection is NOT claimed, and
    its blast radius is bounded by the very fact that makes it undetectable — it feeds
    none of the derivations, so no fence''s sweep is computed from it. Writing that
    member into the SUFFICIENCY sentence as covered would be round 24''s overclaim
    reproduced one fold later, in the remedy for it. COMPLETENESS is asserted by NAME,
    where distinctness IS decidable: the shared scan module exports the six shared
    derivations AC-2 enumerates — the file-set walk, the loose scan, the data-flow
    scan, the BaseRepository-subclass scan, the MRO resolution, the closure computation
    — as six DISTINCT importable callables, asserted by importing them and checking
    six names resolve to six different function objects homed in that module; a seventh
    shared derivation added later extends this export list, and its absence from the
    consuming composition is AC-2''s partition''s problem to surface, not this check''s
    to guess. PROVEN NEGATIVE, in the direction that fails silently: a marker detector
    matching nothing in the test tree still finds the one shared module and still
    reads "exactly one", so the test must run its detector against a PLANTED module
    — a fixture written into tmp_path (or a fixture directory the walk is pointed
    at) containing a def that imports ast and walks a parsed tree — and assert the
    scan REACHES it, MATCHES it, and names it; one planted case per marker form the
    predicate claims to match (an `import ast` statement; a bare `ast.*` attribute
    reference under a from-import or aliased import), so a predicate that recognises
    one form and misses the other is red here before the copy that matters is written
    in the other style. A scan asserted only against the clean tree does NOT satisfy
    this criterion. Both counts are baselines, not the specification: six exported
    derivations is today''s list and one capability home is today''s answer.

    kind: test

    check: test_derivations_are_single_sourced

    ```


    why: round 20''s finding was that "obtains it by import" constrains how a test
    is WRITTEN while only a `check:` passing grades a criterion — so the obligation
    was unenforced. Round 21 answered it with definition-site uniqueness, which is
    the right mechanism (proving the copy cannot exist beats comparing an object to
    itself, because it holds for tests that never make the comparison), but it wrote
    the answer into AC-2''s `desc:` and named a check no fence carries — reproducing
    the finding''s exact shape inside its own remedy: a property stated in prose,
    and a test function nothing will notice is missing. Giving it its own fence is
    the only structural fix available, and the document already set that precedent
    when AC-6 was split out of AC-3 for the same reason. Requiring the planted-duplicate
    negative is the other half: uniqueness is the one assertion in this AC set that
    an under-generating scan satisfies by finding nothing, so without a copy it is
    made to catch, "each derivation has exactly one definition site" is provable by
    a detector that cannot see test modules at all — which is precisely the private
    copy round 20 described, now hidden behind the check written to forbid it. And
    it is what finally delivers the Examples-of-done promise that the suite goes red
    on two copies *not being the same code*, rather than only when they happen to
    disagree on some input someone tried. The capability-level restatement is what
    makes the check implementable at all: round 22 proved no shape discriminates the
    loose scan from the data-flow scan (both reference the same seam symbol; the difference
    is semantic), so the check stops trying to recognise WHICH derivation a copy is
    and catches the one thing every copy must do — touch the ast module — which is
    single-homable, trivially detectable in both its forms, and exactly as strong:
    uniqueness of the capability implies uniqueness of every predicate built on it,
    while completeness moves to the one place distinctness is decidable, the shared
    module''s own export names. And pinning the detection to parsed syntax rather
    than source text is what keeps the planted negative from eating the assertion
    it proves: the only module in the tree guaranteed to contain the literal characters
    `import ast` outside the shared module is this check itself, which has to write
    the plant''s source somewhere, so a grep-shaped detector fails on a clean, compliant
    harness — the round-22 defect in miniature, reached through round 23''s own remedy.
    And stating sufficiency per member rather than as a universal is what stops the
    capability mechanism from claiming a member it cannot reach: five of the six derivations
    cannot exist without touching `ast`, but the file-set walk is filesystem enumeration
    and touches nothing syntactic, so the sentence that swept all six under one marker
    was asserting a coverage the check does not have — round 24''s finding. The obvious
    repair, a second marker for `.py`-targeted enumeration, was tried in this fold''s
    first pass and is withdrawn because running it kills it: `tests/test_vault_path_required.py:320`
    already enumerates `.py` files under `obsidian_schemas/` for WI-024''s forbidden-default
    scan, so the marker is red on a compliant tree the day it is written, and nothing
    separates that scan from a walk copy except the semantic question round 22 proved
    undecidable. What is left is the honest decomposition — a walk feeding a derivation
    is caught by the derivation''s own marker, a walk a sweeping test binds is caught
    by that test''s `__module__` self-cert, and a walk feeding neither is not a derivation
    copy at all — plus a residue this criterion names as undetected rather than covering
    with a sentence. A marker stretched until it matches everything matches the tree''s
    legitimate code first, and an AC that over-claims coverage is worse than one that
    states its edge, because the edge is where the next copy gets written.


    ### Examples of done


    **Given** a person note whose frontmatter has a stray unquoted colon (invalid
    YAML), **when** a skill calls `update_frontmatter_field` to bump `last_contacted`,
    **then** it raises loudly and the note on disk is untouched — instead of silently
    rewriting the file with the whole original note dumped into the body and the frontmatter
    replaced by just `last_contacted`.


    **Given** a vault where one of 400 notes has malformed frontmatter, **when** HAL9000
    starts up and loads all people, **then** the other 399 load fine, startup logs
    a WARNING naming the one skipped file, and the repository reports a skip-list
    of length 1 — instead of the load aborting, or the bad note vanishing silently
    so `resolve()` later mints a duplicate.


    **Given** an `append_to_body_section` write that fails midway because the disk
    is full, **when** the caller checks the result, **then** it sees a raised exception
    — instead of the same `False` it gets when the line was already present and deliberately
    skipped. **And given** that same caller''s dedup path, **when** the line was already
    present, **then** it still gets exactly the `False` it gets today, so its existing
    `if not …:` branch is untouched.


    **Given** a brand-new note with no frontmatter fence at all, **when** *anything*
    writes to it — `update_frontmatter_field` setting `last_contacted`, `update_fields`
    setting a field on a freshly-created stub, or `roundtrip_file` normalising it
    — **then** every one of them succeeds exactly as today, byte-for-byte, and the
    note gains (or keeps) its content unchanged. The hardening refuses malformed frontmatter,
    not absent frontmatter, and it refuses it at every write path or none.


    **Given** Dave''s real vault, where `@Sarah.md` (person), `@Acme Corp.md` (company),
    `Meeting 20260701 - Board.md` and `Four Thousand Weeks - Oliver Burkeman.md` all
    sit in one directory and exactly one person note has malformed frontmatter, **when**
    something asks `PersonRepository` what it skipped, **then** it names that one
    person note and nothing else — not the company notes it globbed and could plainly
    see were companies. **And when** something asks `BookRepository` what it skipped,
    **then** it does not claim that person note as a book it failed to load, even
    though its `*.md` glob matched it. The skip count means "these need attention",
    not "these are what my glob happened to catch."


    **Given** `@Broken.md` — a real person note, `type: person`, that someone hand-edited
    so `emails:` holds a bare string instead of a list — sitting in that same vault
    next to `@Acme Corp.md`, **when** something asks `PersonRepository` what it skipped,
    **then** `@Broken.md` is on the list and `@Acme Corp.md` is not. The two notes
    fail the same way underneath — neither can be built into a `Person` — but one
    is Dave''s contact with a typo in it and the other is a company that was never
    a person. Getting that backwards is how the duplicate gets minted: `@Broken.md`
    goes quiet, `resolve()` misses it, and a second Broken note appears.


    **Given** that same vault, **when** something asks `CompanyRepository` — not `PersonRepository`
    — what *it* skipped, **then** it names `@Broken Corp.md` (the company note someone
    typed `tags: company` into instead of `tags: [company]`) and the malformed `@John.md`
    it globbed but genuinely cannot identify, and it does **not** name `@Sarah.md`,
    which plainly says `type: person`. The two repositories read the same `@*.md`
    files through the same inherited code, so "person notes are not skipped companies"
    has to be true from the company side too — a fix proven only from `PersonRepository`''s
    chair can still report all 400 people as companies that failed to load.


    **Given** that same directory, where `Meeting 20260701 - Board.md` has `attendees:`
    holding one bare name instead of a list, and `Four Thousand Weeks - Oliver Burkeman.md`
    has `tags: book` where it should be `tags: [book]`, **when** anything loads meetings
    or books, **then** each load finishes — every other meeting and every other book
    still comes back, neither repository dies partway through the vault — and each
    names its *own* broken note: the meeting repo reports the meeting, the book repo
    reports the book. Both notes plainly say what they are, so both get claimed. **And
    when** the malformed `@John.md` from the earlier example sits in that same directory,
    **then** `BookRepository` does not claim it as a book it failed to load, even
    though its `*.md` glob matched it — it cannot read that file''s type, and nothing
    else about it says "book." A repository claims what it can prove is its own; where
    it can prove nothing, it stays quiet rather than guessing. The point of the list
    is that Dave can act on every line of it.


    **Given** a person note whose frontmatter fence got truncated, **when** a skill
    calls `update_to_discuss_item` to tick an item off, **then** it fails loudly —
    instead of returning the same `False` it returns when the item text simply wasn''t
    found, which would read as "nothing to tick" while the note sat corrupted. **And**
    `get_to_discuss_items` on that note says the file is unreadable rather than reporting
    it has no items.


    **Given** a person note with no `## Timeline` heading — whether someone hand-deleted
    it or the note was created by hand in Obsidian and never had one — **when** the
    exocortex meeting sync calls `append_to_timeline` to record yesterday''s meeting,
    **then** the note gains a `## Timeline` section with the entry in it and the call
    returns `True` — instead of returning the same `False` it returns when the entry
    was already there, so the sync believed it deduplicated while the meeting record
    was silently thrown away. A missing section is no longer a reason for an entry
    to vanish.


    **And given** that the hand-made note is a hand-made note — it opens with a couple
    of lines of free text before any heading, or has no `##` headings at all, because
    nobody made it from our template — **when** that same sync adds the Timeline section
    to it, **then** every word Dave already wrote in that note is still there afterwards,
    in the same order, with the frontmatter untouched. Gaining a Timeline section
    must never cost the note its contents: fixing "your meeting note went missing"
    by losing the page it was going onto is a worse trade than the bug. **And given**
    a note whose Timeline already contains that entry''s dedup key, **when** the sync
    retries it, **then** it still gets exactly the `False` it gets today, and the
    note still has exactly one `## Timeline` section.


    **Given** a script of Dave''s that never touches a Repository — it reads a note
    it downloaded into a string and calls `parse_markdown_content` on it, the way
    the README says to, or `parse_person` the way the tests do — **when** that string''s
    frontmatter is malformed YAML, **then** it gets the same loud typed error every
    write path gets, rather than a document claiming the note has no frontmatter and
    a body that is quietly the entire file. **And when** the string simply has no
    frontmatter fence, or is a book where a person was expected, **then** it gets
    back exactly what it gets today — `None`, an empty frontmatter dict, the whole
    string as body — because absent and wrong-type were never failures. The parse
    functions are a supported way in; they do not get a quieter version of the truth
    than the repositories do.


    **And given** two notes handed to the *same* wrong-looking call — `parse_person(@Acme
    Corp.md)`, a perfectly good company note, and `parse_person(@Broken.md)`, Dave''s
    own contact with `emails:` hand-typed as a bare string instead of a list — **when**
    each one comes back, **then** the company note comes back `None`, exactly as it
    does today and as `test_parse_person_wrong_type` has asserted all along, and the
    broken contact raises. Underneath they are the same event: `Person` refused to
    be built. What tells them apart is what the note *says it is* — one says `type:
    company` and was never a person, the other says `type: person` and has a typo
    in it — and that is read off the note before anything tries to build a model from
    it, never from whether the build worked. Getting this backwards in the *quiet*
    direction is C5, the duplicate. Getting it backwards in the *loud* direction is
    a script of Dave''s blowing up the first time it points `parse_person` at a folder
    that also has companies in it, which is a thing it is allowed to do today. **And
    given** a note that never says what it is at all — no `type:` line, and a drifted
    field besides — **then** it too comes back `None`, because nothing about it claims
    to be Dave''s contact and there is no folder name here to claim it on its behalf.


    **Given** someone six months from now — not Dave, not anyone who has read this
    document — who adds a fifth repository class, or copy-pastes a sixth To-Discuss-style
    writer into `person.py`, or adds a branch to `parse_frontmatter`, **when** they
    run the suite, **then** it goes red and names the thing they added and did not
    classify: a repository with no answers for the three fixtures, a write path in
    no bucket, a return site with no case. **And given** that they did the ordinary
    thing and put it in a new file of its own — `repositories/recipe.py`, or a `timeline_writer.py`
    next to `writer.py` — wiring it into no `__init__.py` and importing it from nothing,
    **then** the suite still goes red, because the sweeps walk the package''s files
    on disk rather than the modules that happen to be imported or the folder someone
    expected the code to land in. **And given** they added a branch that reuses an
    existing `return` rather than writing a new one — the shape the empty-fence case
    already has — **then** the suite still names it, because a return site is allowed
    to carry more than one outcome and each outcome has to be exercised on its own.
    **And given** a new function that reads a note''s frontmatter and then writes
    the file but does not write that frontmatter back — the shape `write_markdown_file`
    already has — **then** the suite stays green, because the sweep excluded it on
    what it does, not on its name. **And given** they wrap one of the parse functions
    in a friendlier helper of their own rather than calling the parser seam directly
    — the shape `parse_person` already has, one call away from anything that mentions
    `parse_frontmatter` — **then** the suite still names it, because the caller sweep
    follows what *reaches* the seam rather than what mentions it. Every finding in
    this document was caught by a person re-reading the source by hand, twelve times
    running. The thirteenth should be caught by the tests.


    **And given** that same person adds `merge_frontmatter_field` — a fifth function
    that reads a note''s frontmatter, changes a field and writes it back — **when**
    they run the suite, **then** the two tests that have to agree about it *do* agree:
    the write-path test names it as a path that must refuse a malformed note, and
    the caller-classification test stops counting it among the parse functions that
    simply pass the error through, because both tests asked the **same piece of code**
    which functions write the frontmatter back. **And given** that those two tests
    had instead each been written with its own private copy of that question — one
    spotting a call written one way, one spotting it written another — **then** the
    suite goes red on the two copies not being the same code, rather than shipping
    green with one test saying the new function refuses and the other saying it passes
    the error along. That contradiction is not an untidy test suite; it is a note
    getting quietly rewritten, because whichever of the two answers the implementation
    followed, the other one was the guarantee this document spent nineteen rounds
    writing down. Two answers that agree today are not one answer.


    **And given** that the second copy is written on a day when the two copies still
    agree perfectly — nobody has added `merge_frontmatter_field` yet, both answers
    are identical on every note in the vault, and there is nothing to disagree about
    — **when** the suite runs, **then** it is *already* red, and it says which file
    and which line the second copy is on. It does not wait for the day the copies
    diverge, because that is the day a note gets rewritten, and by then whoever wrote
    the copy has been gone for months. **And given** a test that quietly stopped importing
    the shared answer and computes its own instead, **when** that test runs, **then**
    *that* test is the one that fails — not a different test somewhere else that happens
    to notice, and not nothing at all. A rule about how the tests are supposed to
    be written is worth nothing; a test that goes red when they are not is the whole
    of it.


    **And given** the one part of the shared answer that is only three lines — "which
    `.py` files are we looking at" — **when** someone writes their own copy of it
    because importing it costs more lines than retyping it, **then** what happens
    depends on what they do with it, and the difference is stated rather than hoped
    for. **If** that copy feeds a sweep — they went on to look for write paths, or
    repositories, or return sites with it — **then** the suite goes red and names
    their file, because the looking-at-code part cannot be written without the tool
    that reads code, and that tool has exactly one home. **If** the copy is bound
    by one of the tests that does the sweeping, **then** that test goes red, because
    it checks that the answers it uses came from the shared module. **But if** it
    feeds neither — they wanted a file list for something else entirely, the way `test_vault_path_required.py`
    has legitimately wanted one since WI-024 — **then** the suite stays green, and
    that is a decision this document made with its eyes open, not a hole it failed
    to notice: listing files is something ordinary code does for ordinary reasons,
    so a check that went red on all of it would go red on the honest code first, and
    a copy that computes none of the sweeps cannot make any of the sweeps wrong. The
    tests promise to catch a second copy of the *answer*, not a second use of the
    *filesystem* — and knowing exactly which one is promised is the difference between
    a guarantee and a slogan.

    '
  frozen_intent: '

    A malformed or unwritable note is loud at the boundary where it''s met: loads
    surface what they skipped, guards refuse rather than assume, writes that fail
    raise. No vault mutation is ever built on a parse that failed. Every fix ships
    its invariant test (malformed-YAML round-trip protection is the keystone regression).

    '
  note: null
