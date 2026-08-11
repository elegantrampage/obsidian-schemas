schema_version: 1
wi_id: WI-021
spec_path: docs/write-door-bypasses.md
spec_stage_at_review: exploring
reviewed_at: '2026-08-11T10:33:24+01:00'
reviewer: dave
signoff:
  verdict: PROMOTE
  channel: conversational
  provenance: verified
  signoff_escalation: ESC-WI-021-exploring-awaiting-ac-signoff-154d37c4
  comments: Dave reviewed and approved all ACs conversationally ('all approved', 2026-08-11);
    originate executed with --channel conversational, provenance via --from-escalation
    this id.
  ac_hash: a76ebad54da2
  intent_hash: 176e2ec73fda
  ac_item_hashes:
    AC-1: 33653902f47f
    AC-2: b6874ac5d7ef
    AC-3: 9e2bae0c2137
    AC-4: 175736170bcc
    AC-5: 7fe74b36327e
  frozen_acceptance_criteria: "\n**DRAFT — not frozen.** These are the ideation convergence\
    \ artifact: what would prove this worked.\nThey have NOT been through `/review-spec`\
    \ and carry no `ac-signoff` fence, so origination must not\nbe attempted from\
    \ this state.\n\n**Revision 1 — 2026-08-11, answering the AC red-team below.**\
    \ The REMOVE-audit rule's required\ncold-start red-team has now run against the\
    \ draft set (section at the foot of this doc) and returned\nfour findings; this\
    \ revision answers all four, and the answers are the reason the criteria read\
    \ the\nway they do:\n\n- **AC-1** gained a floor and a reach battery. The unbounded\
    \ version was satisfiable by a vacuous\n  sweep — \"every member of {} routes\
    \ through the gate\" is true — and because AC-2 and AC-4 both\n  delegate their\
    \ door coverage to this set, one under-resolving predicate would have shrunk all\n\
    \  three at once while six real doors stayed open.\n- **AC-4** is now bound to\
    \ AC-1's derived set instead of naming four call sites, with `roundtrip_file`\n\
    \  as the single asserted exclusion. The old hand-list silently exempted `write_markdown_file`\
    \ and\n  `lint_vault --fix` — both shown unnormalized in Finding B's own table\
    \ — while reading as total.\n- **AC-2** gained the untyped-frontmatter clause,\
    \ and Finding B above no longer defers the\n  no-`type:` dispatch rule to the\
    \ architect: it adopts `_owns`'s fail-closed answer and pins it here.\n  That\
    \ residue sat upstream of every other criterion, so no amount of door coverage\
    \ could have caught it.\n- **AC-5**'s sweep is re-keyed from the `parseaddr` symbol\
    \ to the job shape, with per-shape positive\n  controls. Finding D records why:\
    \ its own table came from a `parseaddr` grep and is a lower bound.\n\n**Revision\
    \ 2 — 2026-08-11, answering the round-2 re-verify.** Round 2 confirmed the AC-1\
    \ / AC-4 /\nAC-5 fixes and found that revision 1 had folded the no-`type:` dispatch\
    \ residue only HALF way: AC-2\npinned it for names, AC-4 said nothing about the\
    \ `type:` dimension at all, so an implementation\ndispatching on `if frontmatter.get(\"\
    type\") == \"person\"` could green the whole set while every untyped\nnote in\
    \ the vault took unnormalized identifiers — the N3 corruption through the type-less\
    \ side door.\n\n- **AC-4** now carries the same untyped clause AC-2 does, asserted\
    \ as a REPEAT of its whole property\n  over the `type:`-present/absent dimension\
    \ rather than one extra fixture, so the dimension the\n  dispatch code actually\
    \ branches on is varied on the identifier half exactly as it is on the name\n\
    \  half. Scoping the untyped case out of AC-4 was the alternative and was rejected:\
    \ it would have had\n  AC-2 and AC-4 take opposite calls on one residue over one\
    \ door set, against an Intent that draws no\n  such line.\n- **Finding B** was\
    \ rewritten to state the pinning as one rule covering both halves, and to say\
    \ why\n  it must be asserted in two places: dispatch fires once per write, upstream\
    \ of the name/address\n  distinction, so an unasserted half is a switch nobody\
    \ is watching.\n- **Examples of done** gained the untyped variant of the identifier\
    \ scenario, so Dave sees the\n  behaviour he is signing in his own terms, not\
    \ only in the criteria fence.\n\n**Revision 3 — 2026-08-11, answering the round-3\
    \ re-verify.** Round 3 confirmed revision 2 closed the\ndispatch residue where\
    \ it is real, and found that it over-reached: AC-4's untyped pass was bound to\n\
    AC-1's whole derived set minus only `roundtrip_file`, which pinned the entity-only\
    \ doors into an\nuntyped pass they cannot undergo — `model_to_frontmatter` emits\
    \ every declared field (writer.py:111)\nand `Person.type` is `Literal[\"person\"\
    ] = \"person\"` (models.py:78), so an entity write always stamps\n`type: person`\
    \ and there is no branch to get wrong. A builder could satisfy that sentence only\
    \ with a\nfixture that passes with or without the dispatch fix.\n\n- **AC-4**\
    \ now states TWO exclusion sets, one per pass, instead of asserting one set holds\
    \ \"in both\":\n  typed pass `{roundtrip_file}` over AC-1's full derived set (unchanged\
    \ — this is what closed round\n  1's Finding 2 and it stays total); untyped pass\
    \ `{BaseRepository.save, PersonRepository.save,\n  roundtrip_file}` over the dict-shaped\
    \ doors. Both are still asserted by EQUALITY, so narrowing the\n  untyped pass\
    \ did not reopen the escape hatch round 1 closed — a door is out only by being\n\
    \  entity-only or introducing nothing, both stated reasons, neither a builder's\
    \ choice.\n- **One correction to the reviewer's suggested fix, taken from the\
    \ code rather than the door table.**\n  Round 3 proposed excluding D1–D3 from\
    \ the untyped pass as \"the entity-shaped doors\". D1 is not one:\n  `write_markdown_file`\
    \ has TWO arms (writer.py:161-162), and its `frontmatter=` arm takes a\n  caller-supplied\
    \ dict copied verbatim at :259 — which can genuinely lack `type:` and is exactly\
    \ the\n  documented public entry point round 1's Finding 2 fought to keep in scope.\
    \ Excluding it by name\n  would have re-opened that hole on the untyped side.\
    \ The exclusion sets are therefore stated at\n  function granularity and name\
    \ only `BaseRepository.save` / `PersonRepository.save`, the two doors\n  whose\
    \ ONLY input is a typed model.\n- **AC-2** was given the same explicit treatment.\
    \ Its untyped clause already said \"dict-shaped\", but\n  left the term undefined\
    \ and its exclusion set unstated — so a builder could have read D1 out of it\n\
    \  wholesale, the same defect one AC over. It now enumerates what dict-shaped\
    \ means and asserts the\n  identical `{BaseRepository.save, PersonRepository.save,\
    \ roundtrip_file}` set, so the two halves of\n  one rule are scoped identically\
    \ rather than differently-worded.\n- **Finding B** gained the \"where the untyped\
    \ dimension exists, and where it cannot\" paragraph — the\n  door-shape split,\
    \ with the code citations that make the entity-only case unconstructible rather\n\
    \  than merely unlikely — so the scoping is motivated in the exploration rather\
    \ than asserted in a\n  criteria fence. The D1 row of the door table now records\
    \ both arms.\n\n**Revision 4 — 2026-08-11, answering the round-4 re-verify.**\
    \ Round 4 confirmed revision 3's\ntyped/untyped exclusion-set split and found\
    \ the residue one level down: both ACs bound their coverage\nto AC-1's derived\
    \ set, but that set's unit was the FUNCTION, so \"every door in AC-1's derived\
    \ set\"\ncould be satisfied for `write_markdown_file` by a `frontmatter={\"type\"\
    : \"person\", …}` call — the same\nfixture shape the untyped pass already needs\
    \ — and the `entity=` arm that AC-4's own rationale cites\nas the live example\
    \ was never a required fixture. A gate written inside `if entity is not None:`\n\
    (natural: that branch holds the typed `Person`) or, symmetrically, in only one\
    \ of the other branches,\ngreens every criterion while real callers stay ungated.\n\
    \n- **The fix is structural rather than two more sub-clauses.** AC-1's derivation\
    \ unit is now the write\n  ARM — one member per distinct binding of the dict a\
    \ function serializes — so the floor is ten arms\n  across eight functions instead\
    \ of eight doors. Because AC-2 and AC-4 already iterate that set,\n  arm-granularity\
    \ membership makes a fixture through each arm mandatory without either criterion\n\
    \  hand-listing one. Hand-listing is exactly the shape rounds 1–3 kept punishing;\
    \ adding an `entity=`\n  sub-clause to two ACs would have fixed this arm and left\
    \ the next one to the round after.\n- **Reading the code for the fix found a THIRD\
    \ arm the review named only two of.**\n  `write_markdown_file` has three fm-building\
    \ branches, not two: `entity=` (writer.py:256-257),\n  `frontmatter=` (:258-261),\
    \ and `else: fm = extra_fields or {}` (:262-263), which serializes a\n  caller-supplied\
    \ dict as the whole record with no model and no `frontmatter=` argument.\n  `write_markdown_file(path,\
    \ extra_fields={\"type\": \"person\", \"name\": \"Dave/Bob\"})` is a legal call\
    \ on\n  a documented public function that reaches vault bytes. Under the round-4\
    \ suggested fix — an\n  `entity=` sub-clause on each AC — that arm would have\
    \ stayed unexercised on both passes; under arm\n  derivation it is a member, on\
    \ both.\n- **One further code reading, recorded because it bounds the delta rule.**\
    \ `extra_fields` merges\n  differently per arm: guarded on the entity arm (`if\
    \ key not in result`, writer.py:127, so it cannot\n  override `name`), an overriding\
    \ `update` on the `frontmatter=` arm (:260-261), and the sole source\n  on the\
    \ `else` arm. So `extra_fields` is a live field source for the gate on two of\
    \ the three arms\n  and inert on the first — which is why the arms are separate\
    \ members rather than one door with a\n  parameter.\n- **Finding B** gained the\
    \ arm table and now states the door set as ten arms across eight functions;\n\
    \  the untyped scoping is restated in terms of dict-shaped vs entity-shaped ARMS,\
    \ which is what lets\n  `write_markdown_file` be in the untyped pass through two\
    \ arms and out through one, instead of the\n  function-granularity approximation\
    \ revision 3 had to apologise for. The D1 row of the door table\n  records all\
    \ three arms.\n- **Examples of done** gained the direct-call variants — both the\
    \ bare\n  `write_markdown_file(entity=…)` bypassing the repositories and the `extra_fields`-only\
    \ call — so\n  the behaviour Dave signs includes the consumer who never touches\
    \ a repository.\n\nStill owed before Dave signs: the consumer audit named under\
    \ Constraints, since AC-2's refusal is a\nbreaking change for three repositories.\n\
    \nEvery `check` is a top-level `def test_*(` taking ZERO arguments that signals\
    \ failure by RAISING —\na returned `False` exits 0 and reads as PASS.\n\n```criteria\n\
    id: AC-1\ndesc: The set of write ARMS in obsidian_schemas/ and scripts/ that build\
    \ vault bytes from a frontmatter dict is DERIVED by an AST sweep (never enumerated),\
    \ every member routes through the one semantic gate, and the sweep's REACH is\
    \ proven rather than assumed. The unit of the set is the ARM — one member per\
    \ distinct binding of the dict a function serializes, so a function with N such\
    \ branches contributes N members — never the function. (a) The derived set contains\
    \ AT LEAST the ten arms Finding B names, asserted by (qualname, arm) — write_markdown_file's\
    \ `entity=` arm (writer.py:256-257), its `frontmatter=` arm (:258-261) and its\
    \ extra_fields-only `else` arm (:262-263) as three DISTINCT members, plus BaseRepository.save,\
    \ PersonRepository.save, BaseRepository.update_fields, update_frontmatter_field,\
    \ update_frontmatter_fields, roundtrip_file, and lint_vault's --fix writer — so\
    \ a predicate that resolves fewer arms, or that collapses a multi-arm function\
    \ to one member, is RED rather than vacuously green. (b) A planted scratch module\
    \ carrying one function per arm SHAPE in that table — including one multi-branch\
    \ function whose branches must resolve as separate members — is matched when driven\
    \ through the same derivation function the live wall calls, never a re-implementation.\
    \ (c) A planted near-miss — a function that reads and mutates a frontmatter dict\
    \ but hands it back to its caller instead of serializing it — is NOT matched.\
    \ An eleventh arm added without the gate, whether it is a new function or a new\
    \ branch inside an existing one, is red without editing the wall.\nwhy: A quantifier\
    \ oracle carries no information about a matcher's reach — \"every member of {}\
    \ routes through the gate\" is vacuously true, and AC-2 and AC-4 both delegate\
    \ their door coverage to this set, so an under-resolving sweep silently shrinks\
    \ all three. The floor makes under-resolution fail; the planted controls prove\
    \ reach; the near-miss stops the wall passing by matching everything. Deriving\
    \ at ARM rather than function granularity is what closes the branch-shaped bypass:\
    \ write_markdown_file's three arms converge on one write_frontmatter call (writer.py:266),\
    \ so a wall proving only \"this function calls the gate somewhere\" passes for\
    \ a gate written inside `if entity is not None:` while `frontmatter=` and extra_fields-only\
    \ callers stay ungated — and because AC-2/AC-4 iterate this set, per-arm members\
    \ force a fixture through each arm without either criterion hand-listing one,\
    \ which is the hand-list shape rounds 1-3 kept punishing. WI-004's own walls already\
    \ ship exactly this battery (tests/test_write_routing.py:1-18) — this reuses the\
    \ shape rather than inventing one.\ncheck: test_every_frontmatter_door_routes_through_the_semantic_gate\n\
    kind: test\n```\n\n```criteria\nid: AC-2\ndesc: For EVERY Tier-1 pattern NameValidator\
    \ declares — the fixture space swept from that module's own pattern table, not\
    \ sampled — a write that INTRODUCES a matching name is refused at every ARM in\
    \ AC-1's derived set, the target is left byte-identical, no stray directory is\
    \ created, and the refusal is a LoudFailError carrying the stable pattern key\
    \ and no note content. TYPED PASS — the set itself, iterated at arm granularity,\
    \ with the exclusion set asserted to BE exactly {roundtrip_file}, the one arm\
    \ that introduces no fields (Finding C). Because AC-1's members are arms, write_markdown_file\
    \ contributes three separate required fixtures and a `type: person` value arriving\
    \ through the `frontmatter=` arm never stands in for the `entity=` one: a bare\
    \ write_markdown_file(entity=Person(name=<dirty>)) call, bypassing both repositories,\
    \ is required by construction, as is write_markdown_file(path, extra_fields={\"\
    type\": \"person\", \"name\": <dirty>}) through the extra_fields-only arm. UNTYPED\
    \ PASS — the same refusal fires when the write carries NO `type:` key: at every\
    \ DICT-SHAPED arm in that set (write_markdown_file's `frontmatter=` arm and its\
    \ extra_fields-only arm, update_fields, update_frontmatter_field, update_frontmatter_fields,\
    \ lint_vault --fix), a dict with `type:` absent, under the `@*.md` convention,\
    \ is gated exactly as a `type: person` one is, with its exclusion set asserted\
    \ to BE exactly {write_markdown_file's `entity=` arm, BaseRepository.save, PersonRepository.save,\
    \ roundtrip_file}. Both exclusion sets are asserted by equality, so an arm is\
    \ out of a pass only by being entity-shaped or introducing nothing, never by an\
    \ implementation skipping it. Untypedness never exempts a write.\nwhy: Class-closing\
    \ (WI-185): a hand-picked sample is the WI-131 single-literal gap, and a pattern\
    \ added to NameValidator later must join the sweep automatically. The byte-identical\
    \ and no-stray-directory clauses pin Finding F. Iterating AC-1's set at ARM granularity\
    \ is what forces the `entity=` arm to be exercised directly rather than hand-listing\
    \ it as a sub-clause: write_markdown_file's three arms build fm in three independent\
    \ branches that converge on one write_frontmatter call (writer.py:256-266), so\
    \ a uniform dict-shaped fixture harness — the cheapest to write, since most arms\
    \ take dicts — would satisfy a function-granularity binding while a gate wired\
    \ inside `if entity is not None:` leaves the other two arms open, or a gate wired\
    \ at the convergence point leaves nothing to distinguish it from one that is not.\
    \ The untyped clause closes Finding B's dispatch residue, which sits UPSTREAM\
    \ of every other check here — a `type`-keyed dispatch defaulting untyped notes\
    \ to \"not a person write\" would bypass the whole gate — and it pins the fail-closed\
    \ answer `BaseRepository._owns` (base.py:257-264) already gives rather than inventing\
    \ a second rule. Scoping that clause to dict-shaped arms is not a carve-out: on\
    \ an entity-shaped arm the untyped case is unconstructible, because `model_to_frontmatter`\
    \ emits every declared field (writer.py:111) and `Person.type` is `Literal[\"\
    person\"] = \"person\"` (models.py:78), so `type: person` is always stamped and\
    \ there is no branch to get wrong — a fixture there would pass with or without\
    \ the dispatch fix. Excluding arms rather than functions is what keeps write_markdown_file's\
    \ dict arms IN while its entity arm is out, without the function being included\
    \ or excluded wholesale. AC-4 asserts the identical structure on the identifier\
    \ half; the rule is one rule, but dispatch fires once per write for BOTH halves,\
    \ so a half left unasserted is a half a wrong `type:` check can switch off unnoticed.\n\
    check: test_every_tier1_pattern_is_refused_at_every_door\nkind: test\n```\n\n\
    ```criteria\nid: AC-3\ndesc: A note whose STORED name already matches a Tier-1\
    \ pattern stays writable for every write that does not set the name — update_fields\
    \ on an unrelated field, a body-section append, roundtrip_file, and lint_vault\
    \ --fix all still commit — while a write that sets the name to that same value\
    \ is refused.\nwhy: The delta rule (Finding C). Without this the item bricks every\
    \ legacy-dirty note in a 1647-note vault and refuses the very repair tools that\
    \ exist to clean them.\ncheck: test_a_legacy_dirty_name_stays_writable_for_unrelated_writes\n\
    kind: test\n```\n\n```criteria\nid: AC-4\ndesc: An identifier arriving through\
    \ EVERY ARM in AC-1's derived set — the set itself, iterated at arm granularity,\
    \ not a hand-listed subset — plus _writeback_identifier's reuse branch, which\
    \ reaches that set through update_fields, lands in emails[]/phones[] in the same\
    \ normalized form, so that 'Name <a@b.com>', 'Name (a@b.com)' and a bare address\
    \ collapse to one entry and a re-spaced phone does not create a second one. That\
    \ property is asserted over TWO passes, one for each value of the `type:` dimension\
    \ the dispatch code branches on, and each pass states its own exclusion set. TYPED\
    \ PASS — against a `type: person` note, over AC-1's derived set with the exclusion\
    \ set asserted to BE exactly {roundtrip_file}, the one arm that introduces no\
    \ fields (Finding C). Because AC-1's members are arms, write_markdown_file's `entity=`\
    \ arm is a required fixture in its own right and no `frontmatter=` call carrying\
    \ `type: person` can stand in for it: the direct write_markdown_file(entity=Person(emails=[\"\
    Name <A@B.com>\"])) call named in this criterion's own rationale is exercised\
    \ by construction, as is the extra_fields-only arm. UNTYPED PASS — the same inputs\
    \ and the same required outcome against a note with `type:` ABSENT under the `@*.md`\
    \ convention, over every DICT-SHAPED arm in that set (write_markdown_file's `frontmatter=`\
    \ arm and its extra_fields-only arm, update_fields, update_frontmatter_field,\
    \ update_frontmatter_fields, lint_vault --fix), with its exclusion set asserted\
    \ to BE exactly {write_markdown_file's `entity=` arm, BaseRepository.save, PersonRepository.save,\
    \ roundtrip_file} — the entity-shaped arms, where an untyped write cannot be constructed,\
    \ plus the arm that introduces nothing. Both exclusion sets are asserted by equality\
    \ rather than tolerated, so \"excluded\" is never an arm the implementation happened\
    \ to skip. Untypedness never exempts an identifier write wherever the dispatch\
    \ branch is live, exactly as it never exempts a name write (AC-2), and the two\
    \ ACs scope both of their passes identically.\nwhy: Closes N3 and Finding G in\
    \ the same property, stated as an agreement ACROSS arms rather than per-door,\
    \ so an arm normalizing differently is a failure rather than a passing variant.\
    \ Binding the typed pass to AC-1's derived set (as AC-2 does) is what makes it\
    \ total: a hand-listed subset silently exempts the doors it forgot — write_markdown_file(entity=Person(emails=[\"\
    Name <A@B.com>\"])) is the live example, a documented public entry point (README.md:196)\
    \ that bypasses PersonRepository.save's normalization entirely — and exempts the\
    \ next door by construction. Iterating that set at ARM granularity is what makes\
    \ the live example actually get called: at function granularity a builder satisfies\
    \ \"door = write_markdown_file\" with frontmatter={\"type\": \"person\", ...},\
    \ reusing the untyped pass's own fixture shape, and never issues the entity= call\
    \ the example names, so a gate wired into only one of the three branches that\
    \ converge at writer.py:266 greens the set. The untyped pass closes the OTHER\
    \ half of Finding B's dispatch residue: dispatch decides once per write whether\
    \ the gate fires at all, upstream of the name/address distinction, so with AC-2\
    \ asserting untypedness only on names, `if frontmatter.get(\"type\") == \"person\"\
    : normalize_identifiers(...)` — the natural wrong mirror of the bug AC-2's clause\
    \ forces out — would green this whole set while update_fields(person, {\"emails\"\
    : [\"Name <A@B.com>\"]}) writes unnormalized on every legacy `type:`-less note\
    \ in the vault. Varying the exact dimension the code branches on is what makes\
    \ that implementation RED. The two passes carry DIFFERENT exclusion sets because\
    \ the dimension is only live on one class of arm: on an entity-shaped arm `model_to_frontmatter`\
    \ emits every declared field (writer.py:111) and `Person.type` is `Literal[\"\
    person\"] = \"person\"` (models.py:78), so `type: person` is stamped unconditionally,\
    \ there is no branch to get wrong, and an \"untyped\" fixture there would pass\
    \ whether or not the dispatch rule was implemented — a control with no discriminating\
    \ power reading as coverage. One exclusion set asserted across both passes would\
    \ force exactly that fixture; naming both sets at ARM granularity keeps every\
    \ live dict arm in — write_markdown_file is in the untyped pass through `frontmatter=`\
    \ and extra_fields, and out of it through `entity=` — without the function being\
    \ included or excluded wholesale and without inventing coverage where the failure\
    \ cannot occur.\ncheck: test_identifiers_normalize_identically_on_every_door\n\
    kind: test\n```\n\n```criteria\nid: AC-5\ndesc: Exactly ONE implementation of\
    \ the JOB \"split a display-name/address blob into (address, display)\" exists\
    \ in the package, with identifier.Email.parse's angle-bracket-gated use as the\
    \ one permitted home — the fixture space derived by a sweep keyed on the JOB SHAPE,\
    \ not on the parseaddr symbol (a function returning a 2-tuple whose body carries\
    \ address-splitting evidence: any email.utils member, or a '<' / '(' / '@' literal\
    \ used to split or match a string), proven by planted positive controls it MUST\
    \ match in each implementation shape — a parseaddr call, a hand-rolled regex,\
    \ a bare raw.split('<') — and a planted near-miss returning a differently-shaped\
    \ pair it must NOT match. The surviving implementation agrees with Email.parse\
    \ on every input form the deleted create_stub and _normalize_address_fields sites\
    \ accepted, including the parens form.\nwhy: The consolidation rider, corrected\
    \ by Finding D: the property that matters is no SECOND authority for one job.\
    \ A sweep keyed on the literal parseaddr symbol names the MECHANISM one level\
    \ below the property (the WI-185 shape) and is blind to exactly the duplication\
    \ most likely to survive — Finding D's own table was built by a parseaddr grep\
    \ and is a lower bound, and _extract_email_and_name already reaches for a parens\
    \ regex before it reaches parseaddr, proving the job is written here without the\
    \ symbol. The agreement clause is what stops the consolidation silently changing\
    \ behaviour on the parens and laxity deltas.\ncheck: test_address_splitting_is_single_homed_and_agrees_with_email_parse\n\
    kind: test\n```\n\n### Examples of done\n\n**Given** a producer calls `repo.save(Person(name=\"\
    Dave/Bob\"))` — the path-hostile form WI-105\nalready rejects at `create_stub`\
    \ — **when** the save runs, **then** it refuses with a bounded\n`LoudFailError`\
    \ naming `path_hostile_char`, and the vault contains no new `@Dave/` directory\
    \ and no\n`Bob.md` inside one. **And when** a consumer skips the repository entirely\
    \ and calls the public\nwriter directly — `write_markdown_file(path, entity=Person(name=\"\
    Dave/Bob\", emails=[\"Al B <A@B.com>\"]))`\n— **then** the answer is identical:\
    \ the same refusal, no directory, no note. **And when** it instead\ncalls `write_markdown_file(path,\
    \ extra_fields={\"type\": \"person\", \"name\": \"Dave/Bob\"})`, handing the\n\
    writer a bare dict and no model at all, **then** that too is refused. Three different\
    \ ways into the\nsame function are three doors, and none of them is the way through.\n\
    \n**Given** an existing note `@Me to David Field.md` whose stored name has been\
    \ Tier-1 dirty since\nbefore this item, **when** the enricher calls `update_fields(person,\
    \ {\"company\": \"Acme\"})`, **then**\nthe company is written and the note is\
    \ untouched otherwise — **and when** something instead calls\n`update_fields(person,\
    \ {\"name\": \"Me to David Field\"})`, **then** that write is refused. **And when**\n\
    that same note turns out to be hand-created with no `type:` key at all, **then**\
    \ both answers are\nunchanged: the company write still commits, the name write\
    \ is still refused — being untyped is not a\nway through.\n\n**Given** `find_or_create_stub`\
    \ resolves to a canonical who already has `a@b.com` and `+447739341679`,\n**when**\
    \ the reuse branch writes back `\"Al B <A@B.com>\"` and `\"+44 7739 341679\"`,\
    \ **then**\n`emails[]` and `phones[]` each still hold exactly one entry, and `\"\
    Al B\"` has landed in `aliases[]`.\n**And when** that canonical is instead one\
    \ of the hand-created notes carrying no `type:` key,\n**then** nothing about that\
    \ answer changes — one email entry, one phone entry — because being untyped\n\
    is not a way through on the address side either, exactly as it is not on the name\
    \ side above.\n"
  frozen_intent: '

    There is no door into the vault through which an unvalidated name or unnormalized
    address can pass. One RFC 2822 parse authority; an invariant test per closed door.

    '
  note: null
