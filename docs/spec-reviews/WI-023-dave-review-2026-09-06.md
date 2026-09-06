schema_version: 1
wi_id: WI-023
spec_path: docs/identity-engine-endgame.md
spec_stage_at_review: exploring
reviewed_at: '2026-09-06T17:23:59+01:00'
reviewer: dave
signoff:
  verdict: PROMOTE
  channel: cli
  provenance: verified
  signoff_escalation: ESC-WI-023-exploring-awaiting-ac-signoff-9d293950
  comments: wi-023 acs approved
  ac_hash: 583a1b6a293a
  intent_hash: ce7e35a70ea0
  ac_item_hashes:
    AC-1: bd76924cea03
    AC-2: 7523d81032ed
    AC-3: a2ce8381aa34
    AC-4: f21e51ef4ea0
    AC-5: 0dec3196b520
  frozen_acceptance_criteria: '

    Draft — originated cold-start, approval-only mode, re-derived from the frozen
    `## Intent`. **Not yet frozen:** the `ac-signoff` fence is written by `bin/review-spec-helper.py`
    only after Dave''s review, never by hand. Every `check` is a top-level zero-argument
    `def test_*(` in `tests/` that signals failure by raising.


    ```criteria

    id: AC-1

    desc: The duplicate is gone and a REAL oracle outlives it. `_find_or_create_stub_legacy`
    appears at zero sites across `obsidian_schemas/` and `tests/` — asserted as a
    LITERAL-STRING scan over the source TEXT of every file `tests/derivations.py:python_files_under`
    returns for those two roots, so that the 126-line `def` itself, every caller,
    and any comment or string mention are all in the scan''s reach; never as a check
    against person.py:699 by line, and explicitly NOT via `functions_calling`. Both
    of the duplicate''s consumers go with it, named: the vacuous parity cases at `tests/test_resolve_or_create.py:189-211`
    and `:214-224`, and `test_legacy_preserves_rich_note` at `tests/test_wi126_body_preservation.py:209-215`,
    whose engine twin at `:200-207` is left standing to carry the WI-126 body-preservation
    property alone. And no test''s two legs both reach `resolve_or_create`, which
    is the tautology those six cases are in today. In its place a committed golden
    file records, for every case in a derived case set, the `(resolved_name, created_new)`
    pair `find_or_create_stub` returns; a test re-runs the identical cases against
    a fixture vault seeded from the golden''s own declaration and asserts every pair
    matches. The case set is DERIVED from the fixture vault rather than hand-picked
    — that vault being E8''s **ten-note roster, complete and cited rather than re-derived**
    — and the derivation is stated per branch, so the coverage claim is CONSTRUCTED
    rather than asserted: for every note, one case per `emails:` entry (`name=<the
    note''s name>, email=<the entry>` → Branch A, email hit); one case per `phones:`
    entry (`name=<the note''s name>, phone=<the entry>` → Branch A, phone hit — reachable
    only because `Priya Raman` and `Tomas Villalobos` carry `phones:`, which no note
    on the earlier eight-note roster did); one case for every note carrying a `company:`,
    pairing that note''s FIRST name token with that company and NO identifiers (→
    Branch B, name+company reuse: 0.6 `partial-name` at person.py:610-612 plus the
    0.25 company bump at :635-651 is exactly the 0.85 default threshold tested at
    :920, and `Tomas Villalobos` is the note that supplies it); and one not-present
    variant of each (→ Branch C, create). A note added to the fixture joins the sweep
    automatically, and a note carrying no phone or no company contributes no case
    to those arms — which is why branch coverage is guaranteed by the ROSTER, not
    by the sweep, and why the roster is fixed as literals in E8 rather than left to
    the build. Two constraints on the derivation, because either one silently weakens
    the sweep while it still reads as total: a not-present PHONE is not-present under
    `phones_match`, never merely under string equality (E8 invariant 2 — `10790055852`
    reads like a fresh number and is one `phones_match` arm away from `0790055852`),
    and a not-present NAME is MULTI-TOKEN, because a single-token name with no email
    and no phone hits the weak-identity guard at `name_validation.py:385-387` and
    raises `WeakIdentityError` instead of reaching `create_stub`. And because Branch
    C cases WRITE, the golden freezes the ORDERED case list as data and the test replays
    it in that order: a case order re-derived from a filesystem walk at test time
    is machine-dependent, and every note a create case mints is visible to every later
    case in the same run. The golden is DATA in the repository, not a value recomputed
    at test time from the code under test.

    why: This is the item''s safety net and the reason the deletion is safe rather
    than merely tidy (E1). The zero-sites clause is the deletion; the golden clause
    is what stops the deletion from being a net loss of evidence. The mechanism is
    spelled out because the obvious cite was wrong in a way that would have shipped
    this item''s own defect class inside this item''s own deletion criterion: `tests/derivations.py:871-885`
    `functions_calling(files, name)` returns "every function whose OWN body calls
    `name`", so deleting the two callers while leaving the 126-line `def _find_or_create_stub_legacy`
    in place returns the EMPTY SET and the zero-sites clause goes green with the duplicate
    still shipped. `derivations.py` exposes no public definition-scan (`_iter_functions`
    is private), and a literal-text scan is total here — it sees the `def`, which
    is the thing being asserted absent. Naming both consumers is likewise deliberate:
    one is scaffolding, but `test_legacy_preserves_rich_note` is a real passing test,
    and a criterion that forces a real test''s deletion should say so out loud rather
    than let a build discover it. The both-legs clause is the specific defect found
    in the tree: six cases that read as the Phase-5 parity contract compare `parse_identifiers`
    + `resolve_or_create` against `parse_identifiers` + `resolve_or_create` and cannot
    fail for any change to either, because the Phase-4 adapter swap turned `find_or_create_stub`
    into the engine underneath them. Asserting the ABSENCE of that shape is what stops
    a build from "repairing" the harness by renaming it. Data-not-recomputation is
    the whole point: a golden regenerated from the post-cut code agrees with any implementation,
    which is the one way this oracle can be defeated. The per-branch derivation is
    spelled out for the same reason the mechanism is: "by construction" was a CLAIM
    about a fixture, and against the roster this document actually pinned it was false
    — the eight notes carried no `phones:` field and no `company:` field, so Branch
    A''s phone arm had nothing to hit and Branch B''s corroboration arm was unreachable,
    and a build taking both texts at their word would have shipped a sweep silently
    missing two of the four branches it names while this criterion read as though
    they were covered. Coverage lives in the roster, so the roster is where it is
    fixed (E8, now ten notes); naming the branch each derived case ENTERS, with the
    arithmetic for the one that is not obvious, is what makes the claim checkable
    by reading rather than by building. The two derivation constraints and the ordered-replay
    clause are cheap here and expensive later: a phone "variant" that `phones_match`
    unifies turns a create case into a resolve case and the golden records the wrong
    branch as though it were right; a single-token not-present name raises `WeakIdentityError`
    where the case expects a create; and a sweep whose case ORDER comes from a filesystem
    walk is a golden that passes on the machine that recorded it.

    check: test_legacy_stub_is_gone_and_the_golden_is_the_oracle

    kind: test

    ```


    ```criteria

    id: AC-2

    desc: Email resolution has exactly ONE authority, whichever arm the corpus audit
    selects. Over a sweep DERIVED from the fixture vault — every `emails:` entry on
    every note, plus a lowercase variant, a leading/trailing-whitespace variant, and
    (only where `Email.parse` succeeds on the entry) its parsed-address variant, which
    is the query that makes E2 class (b)''s gain visible: `jane.roe@example.com` is
    not itself an entry and so is not in AC-4''s derived space — all four email-resolving
    surfaces return the SAME person for the SAME input: `get_by_email`, `resolve`,
    `resolve_all` (highest-ranked candidate), and `_resolve_identifier(Email.parse(...))`.
    The correctness oracle is the note the address is actually on, declared by the
    fixture, not agreement-among-surfaces: a build in which all four consistently
    return the WRONG person is RED. THE AGREEMENT PROPERTY IS SCOPED to inputs that
    are not ALSO an alias of a different person, and the excluded case is not dropped
    — it is pinned as the DECLARED, PERMANENT ASYMMETRY E8 settles: for the planted
    pair (`Alex Nkemdirim` carrying `aliases: ["pat@example.com"]`, `Rosa Delgado`
    carrying `emails: ["pat@example.com"]`) the three email-only doors — `get_by_email`,
    `resolve_all` highest-ranked, `_resolve_identifier` — return **Rosa Delgado**,
    and `resolve` returns **Alex Nkemdirim**, because `resolve` is a cascade over
    four indexes and its alias step (person.py:488) precedes its email step (:493).
    Both halves are asserted; a build in which `resolve` returns Rosa is RED, and
    so is one in which any of the other three returns Alex. THREE further members
    are PLANTED, as the exact literals E7 fixes — this is not the spec-writer''s choice,
    because which literal lands decides whether this criterion and AC-4 are jointly
    satisfiable: `Jane Roe` carrying `"Jane Roe <jane.roe@example.com>"` (E2 class
    b), `Kit Baldwin` carrying `"kit@localhost"` (class a, refused by `Email.parse`
    as `malformed local@domain`, and containing `@` so it reaches `resolve` step 3),
    and `Dana Okafor` carrying the YAML-quoted `" dana@example.com "` (class c). Every
    other fixture note''s entries are well-formed, lowercase, whitespace-free and
    unique. For the refused entry the criterion asserts the DECLARED arm rather than
    inventing an answer — under the cutover arm `kit@localhost` resolves to nobody
    by all three string surfaces, under the carve-out arm it resolves to Kit Baldwin
    by all three — and surface 4 is NOT APPLICABLE to it under either arm, since `Email.parse`
    refuses it and there is no typed `Email` to hand over; the criterion asserts that
    refusal instead. Under the carve-out arm the surviving authority must resolve
    a SUPERSET of what pre-cut `_email_index` resolved — every raw entry by its lowered
    literal AND, where `Email.parse` succeeds, by the parsed address — which is what
    makes surface 4 agree with the three string doors on `Jane Roe <jane.roe@example.com>`
    instead of missing it. Structurally: `_email_index` is either absent from the
    tracked sources entirely, or present with a module-level comment carrying the
    audit''s refusal count; the two-authority state, where `get_by_email` reads one
    mapping and `_resolve_identifier` reads another, is RED under both arms.

    why: "An identifier index that is actually the resolution authority (or documentedly
    not, per kind)" is half the Intent, and the failure mode is not choosing wrong
    — it is shipping BOTH, which is the state today (person.py:955-956 delegates `Email`
    to `get_by_email` while `_identifier_index` holds the same fact). Writing the
    criterion on the arm-agnostic property lets the corpus audit decide the arm without
    re-signing the AC. The derived sweep proves membership only, so the oracle is
    the fixture''s own declaration of who owns each address — a stub returning the
    first person for every query sweeps every member and is RED on the planted notes.
    The plants are E2''s three divergence classes, planted rather than sampled precisely
    because a fixture built from clean addresses cannot distinguish the two authorities
    at all: on well-formed input they agree, which is what has let the duplicate survive
    this long. They are stated as LITERALS because leaving the refused string unconstrained
    made this criterion and AC-4 jointly unsatisfiable for some choices and vacuous
    for others — `"not-an-email"` moves nothing (`resolve` step 3 is gated on `@`),
    `"kit@localhost"` moves `resolve()`''s answer, and only the second is worth planting;
    E7''s table hand-executes the consequence for both arms and closes AC-4''s exception
    list over exactly these rows. The surface-4 carve-outs are stated for the same
    reason: a typed door cannot be handed an input its parser refuses, and pretending
    otherwise would have made the carve-out arm unbuildable on the angle-bracket plant.
    The alias scope is the second such statement, and the bigger one: an unqualified
    four-door agreement claim is STRONGER than the Intent''s "one authority per kind"
    and it directly contradicted AC-4 discriminant (ii), which requires the alias
    owner — the address is one of the email owner''s `emails:` entries, so it is in
    this sweep, and the four doors hand-execute to Rosa/Alex/Rosa/Rosa (E8''s table).
    "One authority for EMAIL" was never "one answer from RESOLVE for any string containing
    @": `resolve` is a cascade over four indexes, an alias is a name variant with
    no `Identifier` type (E5), and Cut 1 re-homes which lookup the email step consults,
    never where that step sits. Asserting the asymmetry beats carving the input out
    of the sweep, because an unpinned asymmetry is exactly what a "tidy the cascades"
    refactor deletes by accident — and Cut 3 is that refactor.

    check: test_email_has_exactly_one_resolution_authority

    kind: test

    ```


    ```criteria

    id: AC-3

    desc: The phone carve-out is PROVEN, not asserted, and its concurrency rider is
    closed. A test executes the non-transitivity witness against the shipped `phones_match`:
    `phones_match("0790055852", "44790055852")` and `phones_match("0790055852", "10790055852")`
    are both True while `phones_match("44790055852", "10790055852")` is False, and
    `Phone.parse` accepts all three and yields three DISTINCT `.key` values — which
    together are the proof that no key function for this relation exists and therefore
    that keying phones into `_identifier_index` is unavailable rather than merely
    unchosen. The same test asserts the behaviour the carve-out preserves, on a fixture
    note whose phone is fixed HERE as a literal rather than left to the build — `Priya
    Raman`, carrying `phones: ["44790055852"]`, which is an OUTER vertex of the triangle
    and never its centre (E8): `get_by_phone("44790055852")` returns Priya Raman by
    direct key hit, `get_by_phone("0790055852")` returns Priya Raman through the fuzzy
    arm, and `get_by_phone("10790055852")` returns **None**. The fixture carries no
    other phone that `phones_match` unifies with any of the three forms, and no two
    fixture notes carry phones `phones_match` unifies at all (E8 invariant 2). `get_by_phone`
    iterates a MATERIALIZED snapshot of `_phone_index` rather than the live mapping
    — asserted structurally over the tracked source (the loop''s iterable is a call,
    not a bare attribute), which is WI-004''s `docs/concurrent-access.md:8713-8714`
    finding closed. The resolution site carries a comment naming the non-transitivity
    as the reason, and the comment cites this test.

    why: The mint left this as an open design call and WI-021 deliberately declined
    it twice, labelling it "WI-023 item 2''s question" in both `phone_normalization.py:29-33`
    and `tests/test_name_gate.py:479-492`. The answer is derivable from source, and
    the risk is that it gets re-litigated by the next person who sees a raw-digit
    key next to a fuzzy matcher and reaches for the obvious tidy-up. A prose paragraph
    does not survive that; an executable witness does — it goes RED the moment someone
    "normalizes" `phones_match` into an equivalence, which is a real behaviour change
    to a matcher three consumer repos depend on. The concurrency rider rides here
    because WI-004 left that half open ON THE EXPECTATION that phones would leave
    the fuzzy path in this item; they do not, so this item either closes it or it
    stays open with no owner. The keys-are-distinct clause is the discriminating assertion:
    a build that "fixes" the problem by making all three forms produce one key passes
    any behaviour-only test and silently changes what `Phone.key` means for every
    consumer of the index. The fixture phone is a LITERAL here, and it is the outer
    vertex, because the earlier wording ("a note carrying one of the three forms …
    NOT for the one that does not") was a coin flip with an UNBUILDABLE face: `0790055852`
    is the CENTRE of the triangle — `phones_match` accepts it against `44790055852`
    (`phone_normalization.py:79-80`) and against `10790055852` (`:86-88`) — so a note
    carrying the centre is found by all three forms, "the one that does not" names
    nothing, and NO implementation, correct or otherwise, can satisfy the clause.
    The centre is also the obvious first reach, being the plain UK-local form and
    the one E3''s witness table lists first, so the coin was weighted toward the unbuildable
    face. Only `44790055852` and `10790055852` leave one matching and one non-matching
    query; this criterion takes the first, and E8 hand-executes all three lookups
    against the indexing path (person.py:200-203, :407-421) so the expected values
    come from a stated definition rather than from the implementation. The no-unifying-phones
    invariant rides in the same clause because without it the negative witness can
    fail for a reason that has nothing to do with the property: `get_by_phone` falls
    through to a scan that returns the FIRST unifying `_phone_index` entry in insertion
    order (:417-419), so a second unifiable fixture phone would answer the query that
    is supposed to answer None, and the red would be walk-order noise rather than
    a broken carve-out.

    check: test_phones_stay_on_the_fuzzy_path_and_the_reason_is_executable

    kind: test

    ```


    ```criteria

    id: AC-4

    desc: ONE cascade, pinned against a golden with exactly ONE baseline moment. `resolve()`
    contains no match logic of its own — asserted structurally over the tracked source:
    its body calls `resolve_all` and applies a named module-level selection policy,
    and it does not itself read `_cache`, `_alias_index`, `_email_index` or `_phone_index`.
    Behaviourally it is pinned against a golden recorded at CUT 0, against this item''s
    starting HEAD — before Cut 1, before Cut 2, before Cut 3 — and NEVER re-recorded:
    not after a cut, not to absorb a diff, not if the fixture changes (which is why
    the fixture is frozen with it and is never re-homed onto WI-016''s vault, E6).
    The query space is DERIVED from that fixture: for every note, its exact name,
    each whitespace token of that name, each alias, each email and each phone — the
    phone queries having well-defined golden values only because E8 invariant 2 forbids
    two fixture notes carrying phones `phones_match` unifies, which would otherwise
    leave `get_by_phone`''s fuzzy scan (person.py:417-419) returning a walk-order-dependent
    note; every query returns the same person (or the same None) as the golden — EXCEPT
    the closed exception list below, which is Cut 1''s alone and is a literal in the
    test, not a filter computed from a diff. Cut 3 gets no exceptions of its own.
    THE EXCEPTION LIST, hand-executed in E7: under the CUTOVER arm exactly two queries
    move — `"kit@localhost"` goes Kit Baldwin → **None**, and `" dana@example.com
    "` goes None → **Dana Okafor**; under the CARVE-OUT arm exactly one moves — `"
    dana@example.com "` goes None → **Dana Okafor**. Each exception is asserted to
    land on its DECLARED post-cut answer, never merely to differ; a query outside
    the list that moves is RED, and so is an exception that lands somewhere else.
    FOUR DISCRIMINATING queries are additionally hand-stated here, run against the
    SAME single fixture vault (E8''s **ten-note** roster, complete; there is no second
    or throwaway vault), with the answers hand-executed against person.py:458-510
    and :512-656 in `## Exploration Notes` E4 and E8, so that a golden regenerated
    after the cut contradicts this document instead of ratifying the change: (i) `resolve("john
    smith kato")` against the fixture''s `John Smith` returns **None**, not the 0.65
    `token-subset` candidate `resolve_all` scores for it (E4 class A); (ii) `resolve("pat@example.com")`
    returns **Alex Nkemdirim**, who carries it as an ALIAS, not `Rosa Delgado`, who
    carries it as an EMAIL — the alias step (person.py:488) preempts the email step
    (:493), and AC-2 pins the same pair from the other side as a declared asymmetry
    rather than an agreement failure (E4 class B, E8); (iii) `resolve("andy")` against
    the fixture''s `Sandy Forster` returns **None** (whole-word, never substring —
    the property `tests/test_repositories.py:385-395` already pins, restated here
    so the consolidation cannot silently widen it); (iv) `resolve("emily m")` against
    the fixture''s `Emily Mendes`, with NO company hint, returns **None**, not the
    0.6 `partial-name` candidate `resolve_all` step 6 records for it at person.py:624-626
    (E4 class C). Discriminants (i), (iii) and (iv) are hand-stated because the DERIVED
    query space provably cannot reach them; (ii) is in the derived space and is stated
    anyway because it is the one whose answer two criteria disagreed about. Two further
    clauses on the selection policy, because they are what these four jointly force
    and a build should not discover them by going red: the policy is a function of
    the candidate list AND THE QUERY (step 5''s single-token branch at :610-612 and
    step 6 at :624-626 record the SAME 0.6 under the SAME `partial-name` label, yet
    `resolve("sandy")` must return `Sandy Forster` while (iv) must return None — no
    pure function of `List[ResolveCandidate]` separates them), and it must ACCEPT
    0.6 while REJECTING 0.65, so a confidence threshold is the wrong shape. Outside
    the enumerated exception list there is no allowance for "improved" answers.

    why: N5''s drift is real, but "make resolve a thin head of resolve_all" is a behaviour
    change and it widens — the direction that mints wrong-person resolutions in HAL9000''s
    contact cascade, which is the exact class WI-019 and WI-103 were opened to stop.
    The golden is the oracle, and the four hand-stated queries are the oracle''s oracle:
    a derived golden proves membership over the query space, but a golden regenerated
    from post-cut code agrees with whatever the cut did, so the three known divergences
    and one known invariant are written into the contract in prose where regeneration
    cannot reach them. (i), (ii) and (iv) are E4''s three hand-executed divergence
    classes and are the specific answers a literal thin head gets wrong; (iii) is
    included because a widening consolidation is most likely to break substring rejection,
    and because it is an existing pinned promise this item must not spend. Three of
    the four are hand-stated for a stronger reason than belt-and-braces: THE DERIVED
    GOLDEN CANNOT SEE THEM. Its space is names, name tokens, aliases, emails and phones,
    so a three-token query (i), a substring-of-a-token (iii) and a two-token-with-short-second
    query (iv) never enter it — (iv) is the sharp case, because `resolve_all` step
    6 exists ONLY for that shape and its own comment at person.py:615-617 wrongly
    calls it sub-floor ("stays low confidence (< 0.5) and gets filtered out below";
    it records 0.6 against a 0.5 floor), so a builder auditing for divergences by
    reading the code concludes the branch is inert. An oracle blind to a divergence
    is not evidence about it, which is why the class went unnamed until it was hand-executed.
    The two policy clauses are stated because the four discriminants are jointly unsatisfiable
    by the obvious implementation: sorting by confidence and taking the head inverts
    (i) against `resolve("sandy")`, and no function of the candidate list alone separates
    (iv) from `resolve("sandy")` — the two record identical `(confidence, matched_via)`.
    Reading the QUERY is inside this criterion''s structural clause, which forbids
    `resolve` reading the four indexes, not its own argument; saying so here is what
    stops a build reading the clause as "candidates only" and concluding the ACs contradict
    each other. The single-baseline clause and the exception list exist because "recorded
    before the cut" was ambiguous and the ambiguity was load-bearing: Cut 1 rewires
    `resolve()` as well as `get_by_email` (step 3 reads `_email_index` at person.py:492-496)
    and AC-2 names `resolve` as one of the four surfaces it re-homes, so a bare "reproduce
    the golden" made AC-2 and this criterion jointly unsatisfiable for a refused-string
    plant containing `@` — and the cheapest repair, regenerating the golden after
    Cut 1, is precisely the defeat this criterion was written to prevent. Enumerating
    three rows in advance, in prose, costs nothing and cannot be reached by regeneration.
    Asserting each exception''s DECLARED value rather than "it differs" is what stops
    the list from becoming a licence: a build that breaks `kit@localhost` in some
    third way is still RED.

    check: test_resolve_is_one_cascade_and_matches_the_pre_cut_golden

    kind: test

    ```


    ```criteria

    id: AC-5

    desc: The documentation surface tells the truth. `docs/identity-cutover-corpus-audit.md`
    exists and carries the shape its precondition fence declares: the literal walk
    command with verbatim stdout and the count of `type: person` notes scanned; every
    `emails:` entry `Email.parse` refuses, quoted with its note and reason, or an
    explicit "no matches" marker rather than an absent field; the whitespace-class
    and angle-bracket-class divergence counts; the count of cross-note `phones:`/`whatsapp:`
    pairs `phones_match` unifies but `Phone.key` does not; and a 40-hex HEAD SHA per
    consumer repo scanned. The test asserts this SHAPE — failing on a missing section,
    an absent field, a SHA that is not 40 hex characters, or a stated count with no
    listing behind it — and makes no subprocess, network or vault call. In the same
    criterion: the string `paren-decoration-at-the-door` appears at zero sites across
    the tracked sources, and every `docs/`-relative markdown path named in a comment
    in `obsidian_schemas/` resolves to a file that exists; the slack carve-out at
    person.py:238-242 survives with its UNBLOCK CONDITION stated (what would have
    to be true of the frontmatter for `slack` to be projectable), not merely its current
    status; and the false comment on `resolve_all` step 6 is repaired — the claim
    at person.py:615-617 that without a company hint this match "stays low confidence
    (< 0.5) and gets filtered out below" is untrue (it records 0.6 at :626 against
    the `>= 0.5` floor at :654), so the tracked sources contain no comment asserting
    that step 6 is filtered out absent a company hint, and the surviving comment states
    what actually happens. Asserted over the source text, not by re-executing the
    cascade — the behaviour is AC-4''s job.

    why: The audit is an EMPIRICAL premise about a corpus and settling it by reasoning
    about what vault emails look like is the WI-144 shape — the reading that the corpus
    falsified after the signature rather than before it. The teeth are the precondition
    fence, not this test; this pins the artifact''s shape so the audit cannot be discharged
    as one hand-waved sentence, and the per-class listing is what forces the answer
    to the only question that can make Cut 1 harmful. The riders ride here rather
    than in their own criterion because they are the same property: a comment pointing
    at a file that does not exist, a carve-out note with no unblock condition, and
    a comment claiming a live branch is filtered out when it is not are all documentation
    that has stopped being true, and the dangling reference (person.py:113) has been
    dangling since WI-121. Generalizing from that one string to "every `docs/` path
    named in a package comment resolves" is what stops the fix being one deleted line
    that the next stale pointer walks straight past. The step-6 comment is the most
    expensive of the three and earns its place by demonstration rather than by principle:
    it is the reason E4''s third divergence class went unnamed through a full round
    of review — anyone auditing `resolve_all` for things `resolve` does not do reads
    "gets filtered out below" and correctly concludes the branch is inert, which is
    exactly the audit Cut 3 depends on.

    check: test_identity_cutover_docs_are_complete_and_truthful

    kind: test

    ```


    ### Examples of done


    **Given** the endgame has shipped — **when** someone greps the package for `_find_or_create_stub_legacy`
    — **then** there are no hits, and the thing that replaced it as evidence is a
    committed golden of what `find_or_create_stub` answered before any of this item''s
    cuts, still executing in the ~1s hermetic floor. The duplicate is gone *and* we
    can still tell if we broke it, which was never true of the harness that was standing
    there before.


    **Given** an ingester hands the library the address `jane.roe@example.com` — **when**
    it arrives through `get_by_email`, through `resolve`, through `resolve_all`, or
    as a typed `Email` inside `find_or_create_stub` — **then** all four reach the
    same lookup and return the same person, and if that address is instead recorded
    on the note as `Jane Roe <jane.roe@example.com>`, the answer does not depend on
    which of the four doors was used. One authority for email, and the audit''s number
    in the code saying why it is the one it is. **And** — the one thing that is deliberately
    *not* promised — if somebody else has that exact address recorded as an **alias**,
    `resolve` still hands back the alias owner, because `resolve` asks four indexes
    and the alias one comes first. That is not a leak in the one-authority property,
    it is a different question being asked, and the suite says so out loud instead
    of leaving the next refactor to guess.


    **Given** the golden was recorded at Cut 0 and Cut 1 then re-homed `resolve()`''s
    email lookup — **when** the suite runs after Cut 1 — **then** exactly the queries
    this document names in advance have moved, each to the answer this document names,
    and nothing else has; and when someone reaches for the obvious fix of re-recording
    the golden so the diff goes away, the enumerated list still says what the pre-cut
    answers were, because it is prose in the item and not data the build can regenerate.


    **Given** a maintainer six months from now sees `Phone.key` returning raw digits
    right next to a fuzzy country-code matcher and reaches for the obvious tidy-up
    — **when** they normalize `phones_match` into something keyable — **then** a test
    goes red holding three real phone numbers and the arithmetic showing the relation
    is not transitive, so no key can express it. The carve-out defends itself instead
    of relying on someone reading a comment.


    **Given** an orchestrator session calls `repo.resolve("john smith kato")` against
    a vault holding one `John Smith` — **when** the consolidated cascade runs — **then**
    it returns **None**, exactly as it does today, and a duplicate is not created
    against a person we merely share two name tokens with. The two cascades became
    one, and not one of the answers moved.


    **Given** the same session calls `repo.resolve("emily m")` with no company hint,
    against a vault holding one `Emily Mendes` — **when** the consolidated cascade
    runs — **then** it returns **None**, exactly as it does today, even though the
    ranked cascade underneath it scores Emily Mendes at 0.6 and the code comment sitting
    on that branch says it gets filtered out. `resolve_all` is still free to offer
    the candidate to a caller that asked for candidates and passed a company hint;
    `resolve`, which callers treat as an answer, still declines to guess from a first
    name and an initial.

    '
  frozen_intent: '

    One find-or-create implementation, one resolution cascade, an identifier index
    that is actually the resolution authority (or documentedly not, per kind), no
    import cycle — with the parity replay re-run green after each cut.


    *(Frozen anchor, untouched. Read in approval-only mode: the mint''s named mechanisms
    are hypotheses; the outcome clauses are the requirement. Note the Intent already
    licenses the per-kind carve-out — "**or documentedly not, per kind**" — which
    is the arm E3 forces for phones.)*

    '
  note: null
