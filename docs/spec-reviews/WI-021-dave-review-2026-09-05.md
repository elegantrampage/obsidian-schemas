schema_version: 1
wi_id: WI-021
spec_path: docs/write-door-bypasses.md
spec_stage_at_review: exploring
reviewed_at: '2026-09-05T10:11:07+01:00'
reviewer: dave
signoff:
  verdict: PROMOTE
  channel: conversational
  provenance: attested
  signoff_escalation: null
  comments: approved
  ac_hash: 92a58783c84f
  intent_hash: 176e2ec73fda
  ac_item_hashes:
    AC-1: 9ca02c22e7a6
    AC-2: 9a33db1138ee
    AC-3: 85feb5a29bd5
    AC-4: cda8f55feed3
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
    \n**Revision 5 — 2026-09-05, the RE-ORIGINATION.** Drafted by the conductor from\
    \ `## Re-origination\nBrief` (Tier A + Tier B, every item; Tier C untouched per\
    \ ruling 3) for Dave's one signing round, after\nthe two pending hand repairs\
    \ and the G7/consumer re-run recorded in `## Conductor Shell Pass`. What\nchanged\
    \ against the 2026-08-11 signature, item by item: **AC-1** — floor ten→eight arms\
    \ across six\nfunctions (`BaseRepository.save`/`PersonRepository.save` out, the\
    \ `PersonRepository.save` write-back\nkept as a named RIDER outside the set);\
    \ the per-arm pass-what pin; the per-arm PLACEMENT pin with its\none local derivation\
    \ rule and RED consistency leg; the name-identity control. **AC-2** — untyped\n\
    clause → rule (ii) undeclared clause over the four constructible arms; both exclusion\
    \ sets restated\nover the eight arms; the four conjuncts scoped to what each frame\
    \ can keep (no-stray-directory to\n{D1a, D1b, D1c} by equality, with the default-lock-home\
    \ rider and the artifact-naming oracle); the\nrefusal typed as `NameGateRefusal`\
    \ with the D8 counted-record shape and its near-miss; the\nphone-sentinel exemption.\
    \ **AC-3** — the hand-list of four doors replaced by AC-1's derived set with\n\
    exclusion `{D1a, D1b, D1c}` by equality; the delta-not-record pin at D5/D6; the\
    \ scope sentence signed\nagainst G5's measured zero; synthetic fixtures for the\
    \ whole criterion with the reason; the\nphone-sentinel leg. **AC-4** — untyped\
    \ pass → undeclared pass; `aliases[]` as the third field, scoped\nby arm shape;\
    \ the rider and idempotence; the dict-arm deletion signed against G2's measured\
    \ zero.\n**AC-5** — byte-identical, per ruling 3. **`### Examples of done`** —\
    \ scenario 3's second clause\nre-worded to the entity path (option (a), free because\
    \ G2 = 0); scenario 2's untyped clause restated\nunder rule (ii); scenario 4 added\
    \ so the undeclared refusal is visible in Dave's own terms. One reading\nthe brief\
    \ left implicit and this revision states: an undeclared write introducing identifiers\n\
    WITHOUT a `name:` is normalized exactly as a declared one (rule (ii) speaks only\
    \ to `name:`), so\nuntypedness neither exempts nor widens an identifier write.\
    \ One inconsistency in the brief resolved\nin favour of the reasoned bullet: Tier\
    \ A's round-7 sentence restated the undeclared exclusion set as\n`{D1a, D7}`,\
    \ but its own earlier bullet establishes that D4 and D8 cannot construct the undeclared\n\
    case, so the set signed here is `{D1a, D4, D7, D8}` on both AC-2 and AC-4.\n\n\
    Every `check` is a top-level `def test_*(` taking ZERO arguments that signals\
    \ failure by RAISING —\na returned `False` exits 0 and reads as PASS.\n\n```criteria\n\
    id: AC-1\ndesc: The set of write ARMS in obsidian_schemas/ and scripts/ that build\
    \ vault bytes from a frontmatter dict is DERIVED by an AST sweep homed in tests/derivations.py\
    \ (never enumerated), every member routes through the one semantic gate, and the\
    \ sweep's REACH is proven rather than assumed. The unit of the set is the ARM\
    \ — one member per distinct binding of the dict a function serializes, so a function\
    \ with N such branches contributes N members — never the function. (a) FLOOR:\
    \ the derived set contains AT LEAST the eight arms across six functions Finding\
    \ B names, asserted by (qualname, arm) — write_markdown_file's `entity=` arm (D1a,\
    \ writer.py:256-257), its `frontmatter=` arm (D1b, :258-261) and its extra_fields-only\
    \ `else` arm (D1c, :262-263) as three DISTINCT members, plus BaseRepository.update_fields\
    \ (D4), update_frontmatter_field (D5), update_frontmatter_fields (D6), roundtrip_file\
    \ (D7) and lint_vault's apply_fixes writer (D8) — so a predicate that resolves\
    \ fewer arms, or collapses a multi-arm function to one member, is RED rather than\
    \ vacuously green. BaseRepository.save and PersonRepository.save are NOT members\
    \ and carry no gate call as arms: they bind no frontmatter dict and serialize\
    \ nothing (base.py:381-395, person.py:1269-1272), exactly as BookRepository.save\
    \ and MeetingRepository.save are not members; entity-shaped writes are gated at\
    \ D1a one frame later. (b) REACH: a planted scratch module carrying one function\
    \ per arm SHAPE in that table — including one multi-branch function whose branches\
    \ must resolve as separate members — is matched when driven through the same derivation\
    \ function the live wall calls, never a re-implementation. (c) NEAR-MISS: a planted\
    \ function that reads and mutates a frontmatter dict but hands it back to its\
    \ caller instead of serializing it is NOT matched. (d) PASS-WHAT PIN, per arm:\
    \ the wall asserts that the declaration each arm hands the gate is the one available\
    \ AT that arm — the model's own type at D1a; self.type_name at D4; the target\
    \ note's own `type:` parsed in-lock at D5/D6 (writer.py:329, :381) and at D8 (fm.get(\"\
    type\") off the in-lock parse at lint_vault.py:821, never vf.entity_type); at\
    \ D1b/D1c the `type:` of the caller's POST-merge dict as it stands at the convergence\
    \ point (writer.py:266), and where that dict carries none the absence is EXPRESSED\
    \ to the gate as undeclared rather than defaulted; D7 hands the gate an EMPTY\
    \ delta and no declaration. A build wiring every arm with the type defaulting\
    \ to None is RED. (e) PLACEMENT PIN, per arm: the wall asserts the triple (arm,\
    \ declaration passed, gate-call placement), where placement is `above` — the gate\
    \ call precedes the frame's first vault_io call of ANY kind, equivalently its\
    \ `with vault_io.note_lock(...)` statement — or `in-lock`. The REQUIRED value\
    \ is DERIVED, not listed, by ONE local syntactic rule over the arm's own frame:\
    \ `in-lock` iff that frame refuses on the target's non-existence above its first\
    \ vault_io call (base.py:432-433; writer.py:320-321, :374-375; and the guard this\
    \ item adds to apply_fixes immediately above lint_vault.py:819, a read-only Path.exists\
    \ probe), `above` otherwise — and `above` is the DEFAULT for an arm the predicate\
    \ does not recognise, so a ninth arm is RED by omission. Resolved on today's tree:\
    \ `above` = {D1a, D1b, D1c, D7}, `in-lock` = {D4, D5, D6, D8}. A second leg is\
    \ asserted as a RED consistency check, never as an alternative route to `in-lock`:\
    \ an arm that hands the gate a value bound inside the lock (D5/D6/D8 parse their\
    \ declaration there) MUST be `in-lock`, so an arm the rule requires `above` while\
    \ its gate arguments are bound in-lock is a contradiction the wall reports, whose\
    \ repair is that frame's missing guard rather than a hoist. (f) THE RIDER, outside\
    \ the set: PersonRepository.save carries ONE gate call as a rider — the write-back\
    \ of the gate's normalized emails[], phones[] and aliases[] onto the entity, never\
    \ name — pinned by its own named fixture rather than by the wall; the criterion\
    \ states it is NOT a member so a future sweep neither misses it nor re-derives\
    \ it as a ninth arm. (g) NAME-IDENTITY control: a Tier-1-clean, Tier-2-dirty name\
    \ (\"Dave  Smith\", double space) survives every arm byte-for-byte, and after\
    \ the write the note's filename stem and its stored name: are equal — RED for\
    \ a build that reaches for NameValidator.clean or for validate_strict's return\
    \ value. A ninth arm added without the gate, whether a new function or a new branch\
    \ inside an existing one, is red without editing the wall.\nwhy: A quantifier\
    \ oracle carries no information about a matcher's reach — \"every member of {}\
    \ routes through the gate\" is vacuously true, and AC-2, AC-3 and AC-4 all delegate\
    \ their door coverage to this set, so an under-resolving sweep silently shrinks\
    \ all four; the floor makes under-resolution fail, the planted controls prove\
    \ reach, the near-miss stops the wall passing by matching everything, and WI-004's\
    \ own walls already ship exactly this battery (tests/test_write_routing.py:1-18).\
    \ ARM granularity closes the branch-shaped bypass: write_markdown_file's three\
    \ arms converge on one write_frontmatter call (writer.py:266), so a wall proving\
    \ only \"this function calls the gate somewhere\" passes for a gate written inside\
    \ `if entity is not None:` while the two dict arms stay open. The floor is eight,\
    \ not ten, because the criterion's own unit cannot resolve the two save methods\
    \ — hand-listing them is the vacuity hole round 1 closed, and widening the predicate\
    \ until they match would pull BookRepository.save/MeetingRepository.save in too.\
    \ The PASS-WHAT pin exists because (a)/(b)/(c) resolve which arms CALL, and nothing\
    \ else constrains what they PASS: a build with the type defaulting to None greens\
    \ routing while every update_fields delta (which carries no `type:` key, base.py:403-451)\
    \ lands in the undeclared cell and, under rule (ii), is refused permanently. The\
    \ PLACEMENT pin exists because nothing else constrains WHERE the call sits, and\
    \ that is the property AC-2's no-stray-directory clause depends on: write_markdown_file\
    \ takes the note lock first (writer.py:209) and note_lock's outermost acquisition\
    \ mkdirs the sentinel home (vault_io.py:400) at a path defaulting to the note's\
    \ own parent (:350) — so a gate at the convergence point refuses after `<vault>/@Dave/`\
    \ and a .lock already exist, which the conductor confirmed by execution (## Conductor\
    \ Booking) after twenty reading rounds had reasoned about it; the anchor is the\
    \ first vault_io call of ANY kind because anchoring on the first MUTATION call\
    \ let every arm compute `above` (architect round 14). The one-rule derivation\
    \ is what keeps \"DERIVED, not listed\" true: the deleted second disjunct asked\
    \ an AST predicate to certify a fact about a caller two frames away (lint_vault.py:808-815\
    \ vs the walk at :111), so D8 gains the guard its three siblings carry instead.\
    \ The rider is stated because it is the one gate call the wall cannot see and\
    \ the only frame that can write normalized values back onto a model. The name-identity\
    \ control is forced by the FILENAME being bound from the raw entity.name at base.py:381,\
    \ one frame above every gate call and never revisited, while neither NameValidator\
    \ entry point returns a name byte-identical (name_validation.py:257, :265-266,\
    \ :283-297): a gate that normalized a name would write `name: Dave Smith` into\
    \ `@Dave  Smith.md` and the next save() would mint a second note — parked defect\
    \ 1's corruption class, introduced by this item's own fix. Tier-2 repair stays\
    \ a create_stub-only behaviour above the filename derivation.\ncheck: test_every_frontmatter_door_routes_through_the_semantic_gate\n\
    kind: test\n```\n\n```criteria\nid: AC-2\ndesc: For EVERY Tier-1 pattern NameValidator\
    \ declares — the fixture space swept from the branch-unit pattern table the build\
    \ reifies from that module (ten records including `empty`), never sampled — a\
    \ write that INTRODUCES a matching name is refused at every arm in AC-1's derived\
    \ set. TYPED PASS — the derived set iterated at arm granularity, exclusion set\
    \ asserted to BE exactly {D7 roundtrip_file}, the one arm that introduces no fields\
    \ (Finding C); so write_markdown_file contributes three separate required fixtures,\
    \ and a `type: person` value arriving through the `frontmatter=` arm never stands\
    \ in for the `entity=` one — a bare write_markdown_file(entity=Person(name=<dirty>))\
    \ call bypassing both repositories is required by construction, as is write_markdown_file(path,\
    \ extra_fields={\"type\": \"person\", \"name\": <dirty>}). Four conjuncts, each\
    \ bound to the arms whose FRAME can keep it: (1) REFUSED — all seven arms. (2)\
    \ TARGET — all seven arms: a target that existed is byte-identical afterwards,\
    \ and a target that did not exist is not created. (3) NO STRAY DIRECTORY — scoped\
    \ BY EQUALITY to {D1a, D1b, D1c}, the arms that bind what they serialize from\
    \ their own arguments rather than from a parse of the target (writer.py:257, :258-261,\
    \ :262-263), which is why they need no target to exist, why they are the arms\
    \ the hoist reaches, and why they are the only frames that can mint a path-mangled\
    \ parent (base.py:381); the fixture runs under the DEFAULT lock home with OBSIDIAN_SCHEMAS_LOCK_DIR\
    \ asserted unset, and its oracle names artifacts computed from values the test\
    \ holds — for save(Person(name=\"Dave/Bob\")) against a tmp vault, `<vault>/@Dave`\
    \ does not exist (which subsumes the lock home and any note inside it) and `<vault>/@Dave.md`\
    \ does not exist; for a direct write_markdown_file(target, …), `target`, `target.parent`\
    \ where the test did not create it, and `target.parent/\".obsidian-schemas-locks\"\
    ` do not exist — never \"the vault root's only child is X\", and never an ambient\
    \ recursive-listing snapshot. (4) TYPED REFUSAL — the refusal is a NameGateRefusal\
    \ (a leaf of LoudFailError, never NoteParseError) carrying the stable pattern\
    \ key on its `pattern` attribute and no note content. It is RAISED at the six\
    \ door arms D1a/D1b/D1c/D4/D5/D6, and at D8 it is RECORDED: apply_fixes gains\
    \ a dedicated refusal arm above its broad per-file `except Exception` that filters\
    \ on NameGateRefusal (never on the hierarchy root), records a structured per-file\
    \ refusal (path plus `pattern`, never note content), prints a line distinguishable\
    \ from `Fix error on …`, CONTINUES to the next file, and reports a refusal count\
    \ beside its fixed count; a record without a `pattern` key is RED, and the near-miss\
    \ control is one line — the same run over a note whose frontmatter fence does\
    \ not close produces NO refusal record and still prints `Fix error on …`. PHONE-SENTINEL\
    \ EXEMPTION: `pure_digit_name` is conditional — permitted when the record it is\
    \ introduced with carries a phone (the WI-083 stub path, create_stub → save, live\
    \ population 3), refused otherwise. UNDECLARED PASS (rule (ii), Dave's ruling\
    \ 2): a write that introduces a `name:` WITHOUT a declared type is refused with\
    \ its own refusal, regardless of whether the name matches any Tier-1 pattern —\
    \ asserted over the four arms where the undeclared case is constructible, D1b\
    \ and D1c (the caller's post-merge dict carries no `type:`) and D5 and D6 (the\
    \ target note's frontmatter carries none — including a note with no frontmatter\
    \ fence at all, which parse_frontmatter returns as an empty dict, parser.py:79-80),\
    \ with the exclusion set asserted to BE exactly {D1a, D4, D7, D8} for stated reasons:\
    \ D1a's projection always stamps `type: person` (models.py:78, writer.py:111),\
    \ D4 carries self.type_name unconditionally (base.py:188-192, :430, :461), D7\
    \ introduces nothing, and D8 cannot serialize an undeclared note at all (lint_vault.py:318-326,\
    \ :83, :810). The `@*.md` convention is no part of either pass. Both exclusion\
    \ sets are asserted by equality, so an arm is out of a pass only for a stated\
    \ structural reason, never because an implementation skipped it. Untypedness never\
    \ exempts a write.\nwhy: Class-closing (WI-185): a hand-picked sample is the WI-131\
    \ single-literal gap, and a pattern added to NameValidator later must join the\
    \ sweep automatically; the branch-unit table is what makes `empty` and the sentinel\
    \ exemption members of the sweep at all (Finding H). Iterating AC-1's set at ARM\
    \ granularity forces the `entity=` arm to be exercised directly, because write_markdown_file's\
    \ three arms build fm in three branches that converge on one write_frontmatter\
    \ call (writer.py:256-266) and a uniform dict-shaped harness would satisfy a function-granularity\
    \ binding while a gate wired inside `if entity is not None:` leaves the other\
    \ two arms open. The conjuncts are scoped per frame because two of the four are\
    \ properties of the FRAME, not of the gate (architect round 11, confirmed from\
    \ source by data-premise round 11): at the four in-lock arms note_lock has already\
    \ run ensure_dir(sentinel.parent) (vault_io.py:398-400) and created the .lock\
    \ (:407-414) before the gate can speak, with no compensating action (:618-638)\
    \ — and note_lock creates TWO artifacts with different arities (a per-directory\
    \ lock home, a per-note .lock), so an ambient \"listing unchanged\" oracle is\
    \ RED against a correct build at four of seven arms and flips on how the fixture\
    \ planted its note (LESSONS #35 inside the oracle written to discharge WI-149);\
    \ naming the artifacts from values the test holds is what `### Examples of done`\
    \ scenario 1 already says in Dave's words. The default-lock-home rider exists\
    \ because an absolute OBSIDIAN_SCHEMAS_LOCK_DIR puts the sentinel outside the\
    \ vault (vault_io.py:349-351), so a fixture that sets it passes against un-hoisted\
    \ code while production fails. The refusal is its OWN type because LoudFailError\
    \ is the hierarchy's base (errors.py:37) and apply_fixes's per-file try already\
    \ raises four of its subclasses (WriteFailedError from note_lock at lint_vault.py:819,\
    \ FrontmatterParseError from parse_frontmatter at :821, WriteFailedError/ExternalWriteConflict/NoteAlreadyExists\
    \ from write_note at :882/:900), none of which can carry a `pattern` — so a handler\
    \ on the root would record a corrupt fence or a lock timeout as \"the gate declined\
    \ this note\", and AC-2's fourth conjunct would be greenable on a build with no\
    \ gate at D8 at all; the record-and-continue shape at D8 is chosen over `except\
    \ LoudFailError: raise` because that handler sits inside the per-file loop (:815-816,\
    \ :902-903) and would turn one refused note into a vault-wide repair outage. The\
    \ sentinel exemption is payload-derived (create_stub sets allow_phone_sentinel\
    \ from the payload at person.py:1406-1407 then saves at :1475), so the gate needs\
    \ no new parameter. The undeclared pass replaces the signed untyped clause because\
    \ rulings 1 and 2 DELETED the untyped-dispatch rule: the gate is HANDED its declaration\
    \ and never consults the filesystem or _owns, and an undeclared name write is\
    \ refused rather than evaluated — the alternative (i), withhold the person-tuned\
    \ patterns and apply the rest, was rejected as the weaker rule with the larger\
    \ unmeasured surface. Rule (ii)'s live surface is sized at its own scope: G1 finds\
    \ 134 undeclared notes outside `@*.md` (4 with untyped frontmatter, 130 with no\
    \ fence), and G7 finds ZERO callers reaching D1b/D1c/D5/D6 in this package or\
    \ any consumer, so the measured live blast radius is empty (## Conductor Shell\
    \ Pass). The four-arm scoping is not a carve-out: on D1a the untyped case is unconstructible,\
    \ D4 always declares, D7 introduces nothing, D8 never reaches an undeclared note\
    \ (missing_type is a non-auto-fixable ERROR that `continue`s before serialization)\
    \ — a fixture at any of those would pass with or without the rule and read as\
    \ coverage. AC-4 asserts the identical structure on the identifier half; dispatch\
    \ fires once per write for BOTH halves, so a half left unasserted is a half a\
    \ wrong check can switch off unnoticed.\ncheck: test_every_tier1_pattern_is_refused_at_every_door\n\
    kind: test\n```\n\n```criteria\nid: AC-3\ndesc: A note whose STORED name already\
    \ matches a Tier-1 pattern stays writable for every write that does not INTRODUCE\
    \ the name — the delta rule (Finding C) — while a write that sets the name to\
    \ that same value is refused. The preservation property is bound to AC-1's derived\
    \ set, iterated at ARM granularity, with the exclusion set asserted BY EQUALITY\
    \ to be exactly {D1a, D1b, D1c}: those are the arms whose delta IS the whole record\
    \ (writer.py:257, :258-263), where a stored-dirty note cannot be written without\
    \ re-introducing its name and refusal is the correct answer AC-2's typed pass\
    \ already asserts. D4 update_fields on an unrelated field, D5 update_frontmatter_field\
    \ and D6 update_frontmatter_fields on an unrelated field, D7 roundtrip_file and\
    \ D8 lint_vault --fix all still COMMIT against the stored-dirty note, and a ninth\
    \ arm added later joins this criterion automatically. At D5/D6 the gate is handed\
    \ the INTRODUCED fields only — {field_name: field_value} constructed in the frame\
    \ at D5, the `updates` dict at D6 — never the merged record parsed at writer.py:329/:381,\
    \ so a build gating the merged record at update_frontmatter_field is RED here\
    \ even though it greens AC-1, AC-2 and AC-4. A body-section append is named as\
    \ a BEHAVIOURAL example that still commits — it is a Class-2 pass-through, not\
    \ an arm and not a member. PHONE SENTINEL: a WI-083 phone-sentinel record (pure-digit\
    \ name carried with a phone) stays writable through entity writes, and update_fields(person,\
    \ {\"name\": \"+447…\"}) introducing that name WITHOUT the phone is refused. SCOPE:\
    \ this criterion speaks to notes the fix declines to create and to stored-dirty\
    \ notes it leaves writable; pre-existing path-forked notes (a `name:` containing\
    \ `/` already on disk under a mangled parent) are neither repaired nor made writable-by-rename\
    \ by this item, and that population is measured at 0 as of 2026-08-11 (G5: no\
    \ `@`-prefixed directory exists anywhere in the vault). FIXTURES: the population\
    \ is SYNTHETIC for the whole criterion, planted in a tmp vault, and the criterion\
    \ says why — the only live Tier-1-dirty names are the two WI-083 sentinel stubs,\
    \ which the payload rule permits anyway, and the 77 archived ones sit under _merged_dupes/\
    \ and _quarantine/, which SKIP_DIRS (lint_vault.py:57) bars from D8 and the root-only\
    \ glob (base.py:230) bars from D4, so no door in this package can be exercised\
    \ against them.\nwhy: Without the delta rule the item bricks every legacy-dirty\
    \ note and refuses the very repair tools that exist to clean them — remedy-is-the-disease.\
    \ The hand-list of four doors it was signed with is the exact shape AC-2 and AC-4\
    \ were re-based onto AC-1's derived set to escape (a hand-list \"silently exempts\
    \ the doors it forgot … and exempts the next door by construction\"), and here\
    \ the omission was live rather than tidy: the two arms it omitted, D5 and D6,\
    \ are where the record/delta distinction is CONSTRUCTIBLE — update_frontmatter_field's\
    \ delta is two loose parameters (writer.py:294-295) while the stored record sits\
    \ bound one line above the natural call site (:329, mutated at :332) — so a build\
    \ gating the merged record there greens AC-1's whole per-arm triple, greens AC-2\
    \ (a refusal oracle cannot tell refused-because-introduced from refused-because-stored)\
    \ and greens AC-4, while making update_frontmatter_field permanently refuse every\
    \ legacy-dirty note; and D5/D6 are the ONLY arms that can reach the 77 archived\
    \ dirty notes at all (reachability crosses three partitions: SKIP_DIRS binds D8,\
    \ the non-recursive root glob binds D4 and every body writer, and D5/D6/D7 are\
    \ bound by nothing but .exists()). The exclusion set is the same one frame-local\
    \ predicate AC-2's conjunct 3 and AC-1's `above` set use — three criteria, one\
    \ fact per frame, no inter-procedural analysis. The scope sentence is signed against\
    \ G5's measured zero rather than against count 3's \"historical\" premise because\
    \ the defect SUCCEEDS today (## Conductor Booking) and a note it minted would\
    \ be invisible to every rglob(\"@*.md\") count and unrepairable through every\
    \ door once the gate lands; zero is a measurement and the next reader can falsify\
    \ it. Synthetic fixtures are stated with their reason because an oracle satisfied\
    \ identically whether or not the door works on the population the criterion was\
    \ written for is the WI-235 shape. The sentinel leg rides here because under the\
    \ delta rule an entity write's name is always the delta, so without it every subsequent\
    \ entity write for a WI-083 stub would be refused.\ncheck: test_a_legacy_dirty_name_stays_writable_for_unrelated_writes\n\
    kind: test\n```\n\n```criteria\nid: AC-4\ndesc: An identifier arriving through\
    \ EVERY arm in AC-1's derived set — iterated at arm granularity, not hand-listed\
    \ — plus _writeback_identifier's reuse branch (which reaches the set through update_fields)\
    \ and the PersonRepository.save RIDER, lands in emails[]/phones[] in the same\
    \ normalized form, so that 'Name <a@b.com>', 'Name (a@b.com)' and a bare address\
    \ collapse to one entry and a re-spaced phone does not create a second one; phones\
    \ dedupe on normalize_phone's output while storing the display form. TYPED PASS\
    \ — against a `type: person` write, over AC-1's derived set with the exclusion\
    \ set asserted to BE exactly {D7}, the one arm that introduces no fields; write_markdown_file's\
    \ `entity=` arm is a required fixture in its own right, so the direct write_markdown_file(entity=Person(emails=[\"\
    Name <A@B.com>\"])) call named in this criterion's rationale is exercised by construction,\
    \ as is the extra_fields-only arm. THE THIRD FIELD, SCOPED BY ARM SHAPE: on the\
    \ entity-shaped arm D1a and on the rider, aliases[] is in the container on both\
    \ sides and both cross-field migrations run — an address found in an aliases[]\
    \ entry moves to emails[], and a display half found in an emails[] entry moves\
    \ to aliases[] — preserving what _normalize_address_fields does today (person.py:1300-1343),\
    \ which is SUBSUMED and deleted; on every dict-shaped arm (D1b, D1c, D4, D5, D6,\
    \ D8) emails[] and phones[] normalize and dedupe, aliases[] is passed through\
    \ BYTE-IDENTICAL, and the gate emits NO key the write did not carry — a build\
    \ that splits an alias on a dict arm, or emits a destination key there, is RED,\
    \ because update_fields merges by key REPLACEMENT (base.py:451) and a split alias\
    \ without its migration would discard the address half. The dict-arm emails[]\
    \ rule stores the bare address and drops the display half; that deletion's live\
    \ population is measured at 0 (G2: no live emails[] entry has a display half missing\
    \ from its note's aliases[]). THE RIDER writes the gate's normalized emails[],\
    \ phones[] and aliases[] back onto the entity and never name, so the in-place\
    \ model mutation callers observe today is preserved (and phones[] is newly mutated\
    \ in place, which is the behaviour this criterion wants); the gate is IDEMPOTENT\
    \ — gate(gate(x)) == gate(x) — because one PersonRepository.save invokes it twice,\
    \ the rider and then D1a. UNDECLARED PASS (rule (ii)): over the four arms where\
    \ the undeclared case is constructible, {D1b, D1c, D5, D6}, with the exclusion\
    \ set asserted to BE exactly {D1a, D4, D7, D8} for the reasons AC-2 states — an\
    \ undeclared write that introduces identifiers TOGETHER WITH a `name:` is refused\
    \ under rule (ii) exactly as AC-2 requires, and an undeclared write that introduces\
    \ identifiers WITHOUT a `name:` lands them in the same normalized form as the\
    \ typed pass: untypedness never exempts an identifier write, and it never widens\
    \ one. Both exclusion sets are asserted by equality rather than tolerated, so\
    \ \"excluded\" is never an arm the implementation happened to skip.\nwhy: Closes\
    \ N3 and Finding G in the same property, stated as an agreement ACROSS arms rather\
    \ than per door, so an arm normalizing differently is a failure rather than a\
    \ passing variant; binding the typed pass to AC-1's derived set is what makes\
    \ it total — write_markdown_file(entity=Person(emails=[\"Name <A@B.com>\"])) is\
    \ a documented public entry point (README.md:196) that bypasses PersonRepository.save's\
    \ normalization entirely, and arm granularity is what makes that call actually\
    \ get issued rather than satisfied by a frontmatter= fixture through the same\
    \ function. aliases[] is the third field because _normalize_address_fields reads\
    \ addresses OUT of person.aliases (person.py:1323-1329) and writes display halves\
    \ back INTO it (:1331-1333, :1339-1343), and create_stub seeds aliases=[email]\
    \ with a bare address (:1448) — a gate that left aliases[] alone would satisfy\
    \ the old wording while regressing what D3 does today. The arm-shape split is\
    \ forced, not chosen: a migration needs both fields in hand plus the destination's\
    \ dedupe set (:1327, :1331), which only the whole-record frames have, and on a\
    \ dict arm an emitted destination key would REPLACE that field's stored list (base.py:451)\
    \ — so \"in place\" on a dict arm must mean byte-identity, and a build reading\
    \ it as \"split it anyway\" must be RED. The dict-arm deletion is signed against\
    \ G2's measured zero rather than an estimate because it is a real loss against\
    \ what is on disk today (the display half lives inside the raw emails[] entry)\
    \ applied at whole-list scale on every reuse write-back (_writeback_identifier\
    \ routes person.emails through update_fields, person.py:1206-1217) — the rule\
    \ governs the next entry written, so the clause stays even though its live subject\
    \ is empty. The rider is the reason PersonRepository.save carries a gate call\
    \ at all now that it is not an arm: no other frame can perform the write-back,\
    \ the gate returns a dict and never touches the model, and under the name-identity\
    \ rule there is nothing on name to write back. Idempotence is required rather\
    \ than incidental because one save invokes the gate twice. The undeclared pass\
    \ replaces the signed untyped clause for the reason AC-2 gives (rulings 1 and\
    \ 2 deleted untyped dispatch); the identifier-only reading is stated explicitly\
    \ because rule (ii) speaks only to `name:` and the brief left the identifier-without-name\
    \ cell implicit — the gate's address normalization is entity-agnostic and reads\
    \ only the payload, so the same normalized outcome is what DECLARE already implies,\
    \ and saying so is what stops a builder from either refusing or skipping that\
    \ cell.\ncheck: test_identifiers_normalize_identically_on_every_door\nkind: test\n\
    ```\n\n```criteria\nid: AC-5\ndesc: Exactly ONE implementation of the JOB \"split\
    \ a display-name/address blob into (address, display)\" exists in the package,\
    \ with identifier.Email.parse's angle-bracket-gated use as the one permitted home\
    \ — the fixture space derived by a sweep keyed on the JOB SHAPE, not on the parseaddr\
    \ symbol (a function returning a 2-tuple whose body carries address-splitting\
    \ evidence: any email.utils member, or a '<' / '(' / '@' literal used to split\
    \ or match a string), proven by planted positive controls it MUST match in each\
    \ implementation shape — a parseaddr call, a hand-rolled regex, a bare raw.split('<')\
    \ — and a planted near-miss returning a differently-shaped pair it must NOT match.\
    \ The surviving implementation agrees with Email.parse on every input form the\
    \ deleted create_stub and _normalize_address_fields sites accepted, including\
    \ the parens form.\nwhy: The consolidation rider, corrected by Finding D: the\
    \ property that matters is no SECOND authority for one job. A sweep keyed on the\
    \ literal parseaddr symbol names the MECHANISM one level below the property (the\
    \ WI-185 shape) and is blind to exactly the duplication most likely to survive\
    \ — Finding D's own table was built by a parseaddr grep and is a lower bound,\
    \ and _extract_email_and_name already reaches for a parens regex before it reaches\
    \ parseaddr, proving the job is written here without the symbol. The agreement\
    \ clause is what stops the consolidation silently changing behaviour on the parens\
    \ and laxity deltas.\ncheck: test_address_splitting_is_single_homed_and_agrees_with_email_parse\n\
    kind: test\n```\n\n### Examples of done\n\n**Given** a producer calls `repo.save(Person(name=\"\
    Dave/Bob\"))` — the path-hostile form WI-105\nalready rejects at `create_stub`\
    \ — **when** the save runs, **then** it refuses with a `NameGateRefusal`\nwhose\
    \ `pattern` is `path_hostile_char`, and the vault contains no `@Dave/` directory,\
    \ no lock home\ninside one, no `Bob.md`, and no `@Dave.md`. **And when** a consumer\
    \ skips the repository entirely and\ncalls the public writer directly — `write_markdown_file(path,\
    \ entity=Person(name=\"Dave/Bob\",\nemails=[\"Al B <A@B.com>\"]))` — **then**\
    \ the answer is identical: the same refusal, no directory, no lock\nhome, no note.\
    \ **And when** it instead calls `write_markdown_file(path, extra_fields={\"type\"\
    : \"person\",\n\"name\": \"Dave/Bob\"})`, handing the writer a bare dict and no\
    \ model at all, **then** that too is refused\nthe same way. Three different ways\
    \ into the same function are three doors, and none of them is the\nway through\
    \ — and the refusal lands BEFORE the writer touches the disk, not after it has\
    \ made a\ndirectory to lock.\n\n**Given** an existing note `@Me to David Field.md`\
    \ whose stored name has been Tier-1 dirty since\nbefore this item, **when** the\
    \ enricher calls `update_fields(person, {\"company\": \"Acme\"})`, **then**\n\
    the company is written and the note is untouched otherwise — **and when** something\
    \ instead calls\n`update_fields(person, {\"name\": \"Me to David Field\"})`, **then**\
    \ that write is refused. **And when**\nthat same note turns out to be hand-created\
    \ with no `type:` key at all, **then** through `update_fields`\nboth answers are\
    \ unchanged, because the repository declares the type on the note's behalf — while\
    \ a\ncaller that hands `update_frontmatter_fields` a `{\"name\": …}` for that\
    \ untyped note is refused outright,\nwhatever the name, because the write declares\
    \ nothing: being untyped is not a way through, and it is\nnot a way in either.\n\
    \n**Given** `find_or_create_stub` resolves to a canonical who already has `a@b.com`\
    \ and `+447739341679`,\n**when** the reuse branch writes back `\"Al B <A@B.com>\"\
    ` and `\"+44 7739 341679\"` through `update_fields`,\n**then** `emails[]` and\
    \ `phones[]` each still hold exactly one entry. **And when** that same person\
    \ is\ninstead saved as an entity — `repo.save(person)` with `\"Al B <A@B.com>\"\
    ` in `emails[]` — **then** the\nentries still collapse to one each **and** `\"\
    Al B\"` lands in `aliases[]`, because the entity path holds\nthe whole record\
    \ and can move the display half to where it belongs; the dict path collapses,\
    \ the entity\npath collapses and migrates. **And when** that canonical is one\
    \ of the hand-created notes carrying no\n`type:` key, **then** nothing about the\
    \ `update_fields` answer changes — one email entry, one phone\nentry — because\
    \ the repository declares the type and being untyped is not a way through on the\
    \ address\nside either.\n\n**Given** a consumer calls `write_markdown_file(path,\
    \ frontmatter={\"name\": \"Alice Example\"})` — a\nperfectly clean name, a bare\
    \ dict, and no `type:` anywhere — **when** the write runs, **then** it is\nrefused\
    \ with its own refusal naming the undeclared write, and nothing is written; **and\
    \ when** the\ncaller adds `extra_fields={\"type\": \"person\"}`, **then** the\
    \ same write commits. A write that names a\nperson has to say what it is writing.\n"
  frozen_intent: '

    There is no door into the vault through which an unvalidated name or unnormalized
    address can pass. One RFC 2822 parse authority; an invariant test per closed door.

    '
  note: null
