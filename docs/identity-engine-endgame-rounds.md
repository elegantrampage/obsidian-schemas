# Identity engine endgame — archived gate rounds

<!-- archive-split:v1 — IMMUTABLE APPEND-ONLY ARCHIVE. Written only by src/archive_split.py at a
completed conveyor transition; appended to, never edited, reordered or rewritten. It
carries no work-item frontmatter by design, so it is invisible to find_work_items and to
find_corrupt_work_item_docs. Living spec: docs/identity-engine-endgame.md -->

## Architectural Review — 2026-09-06

**Recommendation: REVISE — return to exploration**

Cold-start read of the whole document against the tree at HEAD `2bf731f` + the seeded delta. Every citation was re-resolved and every hand-executed claim re-executed independently; the findings below are NOT about the exploration being wrong, they are about two places where the document disagrees with itself and leaves the item buildable two ways.

### Trigger check

Fires on three: significantly extends/replaces a core system (which code resolves email, and which person `resolve()` returns, across three consumer repos); touches >3 files in different concerns (`repositories/person.py`, `identifier.py`, `tests/test_resolve_or_create.py`, `tests/test_wi126_body_preservation.py`, a new golden, a new audit doc); effort > 1 day (four ordered cuts + a precondition artifact).

### What I re-verified, and what held

Stated first because it is the reason this is REVISE and not REJECT — the exploration is unusually well grounded and I could not falsify any of its load-bearing claims.

- **E1's tautology is real.** `tests/test_resolve_or_create.py:198` calls `find_or_create_stub`, which since the Phase-4 swap is `parse_identifiers(...)` + `self.resolve_or_create(...)` + `_hydrate` (person.py:688-697); `:204-209` is the same three calls with the same arguments and the same defaults. Both legs are one computation. `:214-224` likewise. Six cases that read as the Phase-5 parity contract cannot go red.
- **E3's non-transitivity witness is correct.** Hand-executed against `phone_normalization.py:58-90`: `("0790055852","44790055852")` takes the `norm2.startswith("44") and norm1.startswith("0")` arm at `:79-80` → `"790055852" == "790055852"` → True; `("0790055852","10790055852")` takes the `norm2.startswith("1") and len(norm2)==11` arm at `:86-88` → `"0790055852" == "0790055852"` → True; `("44790055852","10790055852")` matches no arm → False. All three clear `MIN_DIGITS = 7` (identifier.py:237) and yield three distinct `phone:` keys (`:253-254`). No key function exists for this relation. The carve-out arm is forced, and the Intent licenses it in terms.
- **E4's two divergences are correct.** `resolve("john smith kato")` → step 5 at person.py:507 tests `query_lower in name.split()`, never true for a multi-token string → None; `resolve_all` at `:607-609` scores it 0.65 `token-subset`. And `resolve` orders alias (`:488`) before email (`:493`) while `resolve_all` orders email (`:573`) before alias (`:581`) with the ordering commented deliberate at `:571-572`, so the tie at 1.0 inverts under a stable sort. A literal thin head widens `resolve()`, which is the wrong-person direction.
- **Every remaining citation resolves and means what the doc says.** `_find_or_create_stub_legacy` is defined once (person.py:699) with exactly one caller in the tree (`tests/test_wi126_body_preservation.py:212`); `_resolve_identifier` delegates email→`get_by_email` and phone→`get_by_phone` (person.py:955-958); `get_by_phone` iterates the live `self._phone_index.items()` at `:417` while `_clear_indexes` mutates it in place at `:326-333`, and `docs/concurrent-access.md:8713-8714` does leave that half explicitly NOT closed; `identifier.py:45` imports `normalize_phone` at module scope and the two deferred imports are gone; `docs/paren-decoration-at-the-door.md` is referenced at exactly one site (person.py:113) and does not exist; `scripts/` holds only `lint_vault.py` and `migrate_person_to_discuss.py`, so the campaign's replay invariant (`docs/backlog-campaign-2026-07-05.md:37,62`) is indeed not runnable in this tree; WI-021's two declines are at `phone_normalization.py:29-33` and `tests/test_name_gate.py:481-485`.

### Blocking issues

**1. The document states two different baseline moments for the same golden, and Cut 1 moves what that golden pins.** `## Approach` Cut 0 records the `resolve()` golden "against unchanged code" — i.e. before Cuts 1, 2 and 3. AC-4 says it is "recorded BEFORE the cut", which in context reads as before the *consolidation* (Cut 3). Those are not the same instant, and the difference is load-bearing because **Cut 1 rewires `resolve()` itself**: `resolve` step 3 reads `_email_index` directly (person.py:492-496), AC-2 names `resolve` as one of the four surfaces that must reach the one authority, and E2 says in terms that the cutover *loses* class (a) and *gains* classes (b)/(c). So under the cutover arm, `resolve()`'s answers on those classes move at Cut 1 — while AC-4 declares "any query where the policy CANNOT reproduce the golden is RED; there is no allowance for 'improved' answers."

   The collision is not hypothetical against the fixture AC-2 mandates. AC-2 requires planting "a note whose `emails:` carries a string `Email.parse` refuses", unconstrained; AC-4's query space is derived from the same fixture and includes "each email". Plant `"not-an-email"` (the tree's existing specimen at `tests/test_identity_index.py:186`) and nothing moves — `resolve` step 3 is gated on `"@" in query_lower`, so it returns None before and after. Plant `"jane@bad domain.com"` or `"a@b"` and pre-cut `resolve` returns the note via `_email_index` while post-cut it returns None: AC-2 demands that None, AC-4 forbids it, and the two criteria are jointly unsatisfiable. Which plant lands is currently the spec-writer's coin flip.

   The cheap repair a build will reach for is regenerating the golden after Cut 1 — which is precisely the defeat AC-4's own `why` names ("a golden regenerated from post-cut code agrees with whatever the cut did"). Pick the arm in writing: either (a) the golden is recorded once at Cut 0 and Cut 1's changes to `resolve()`'s email answers are enumerated as named, Dave-visible exceptions — the machinery this doc already built for E4's two divergences — or (b) `resolve()`'s email path is explicitly declared out of AC-4's query space and pinned by AC-2 alone. Do not leave it to the plant.

**2. "No dependency on WI-016, the golden can be re-homed, a cheap follow-on" is false, and WI-016 is the item immediately ahead in the queue.** `state/work-items.json:2017-2027` reads `WI-022, WI-016, WI-023, …` — WI-016 (the frozen ~50-note real-data fixture vault) is very likely to land before this builds. E6's dismissal treats the golden as portable data. It is not: the golden's query space *and* its answers are derived from the fixture vault's own notes, so changing the fixture means **re-recording** the golden — against whatever code exists at that moment, which after Cut 1/Cut 3 is post-cut code. That is the same oracle defeat as finding 1, arriving through the back door of a "cheap follow-on".

   The three arms are architecturally different and one must be chosen here, not discovered at build: (a) declare the dependency and build both oracles on WI-016's fixture from the start; (b) declare the golden permanently homed to this item's own `tests/`-local fixture and state that it is never re-homed — accepting a second fixture vault beside WI-016's, with the solve-in-one-place cost named; or (c) re-order so WI-023 precedes WI-016. Silence here buys either a duplicate fixture corpus or a re-recorded golden.

### Non-blocking notes for the spec-writer

- **AC-1 names a derivation that cannot see the thing it asserts.** `tests/derivations.py:871-885` — `functions_calling(files, name)` returns "every function whose OWN body calls `name`". Delete the two callers, leave the 126-line `def _find_or_create_stub_legacy` (person.py:699) in place, and that scan returns the empty set: AC-1's zero-sites clause is green with the duplicate still shipped. The AC's *property* ("appears at zero sites") is right; the mechanism cite is wrong, and `derivations.py` exposes no public definition-scan (`_iter_functions` is private). This is the item's own defect class landing in the item's own deletion criterion — worth fixing loudly rather than quietly.
- **The surviving caller is a real test, and Cut 4 does not name it.** `tests/test_wi126_body_preservation.py:209-215` `test_legacy_preserves_rich_note` is the legacy twin of `test_engine_preserves_rich_note` (`:200-207`). AC-1 forces its deletion; Cut 4 names only "the harness that consumed it", which reads as `test_resolve_or_create.py`. Say explicitly that the twin goes and the engine leg carries the WI-126 property alone.
- **Determinism boundary: clean, and deliberately so.** No capability in this design is handed to an LLM. The one empirical premise that cannot be reasoned about — the live-corpus email refusal count — is routed to a `## Write Targets` precondition with a decision rule stated in advance, rather than to a builder's reading of `_project_identifiers`' three-month-old docstring claim (person.py:236-238). That is the right side of the boundary and the right side of LESSONS #7 and #32.
- **Prior art: no divergence to justify.** The constraint being worked around is "the pre-WI-125 oracle is about to be deleted", and the world's standard answer is characterization/approval/golden testing. That is exactly what Cut 0 reaches for. No compensation machinery is being built around a subtracted capability, so this dimension raises nothing.
- **Fit, duplication, boundaries, reversibility, cost — all clean.** The derived-sweep-plus-AST-wall idiom matches what WI-020/WI-021 established in `tests/derivations.py`; the item *removes* a duplicate rather than adding one; the compat re-export (person.py:78-85) and `find_or_create_stub`'s consumer contract (person.py:668-686) are both correctly declared untouchable; the lint_vault repair rule is routed to WI-026 rather than absorbed; the ordering is reversible cut-by-cut with the oracle standing until Cut 4. E5's "Branch A does no writeback" warning (person.py:866-870) is exactly the kind of deliberate divergence a repaired harness would otherwise "discover" as a regression, and it is pre-empted.

```verdict
gate: architect
verdict: REVISE
date: 2026-09-06
model: claude-opus-5
targets: AC-1, AC-2, AC-4, #approach, #exploration-notes
prior: none
basis: original
findings: 2/3
note: The item's spine is the golden oracle, and the doc gives it two different baseline moments — Cut 0 records it "against unchanged code" while Cut 1 deliberately moves what `resolve()` returns on the email path — so AC-2 and AC-4 are jointly unsatisfiable for a refused-string plant containing "@", and E6's "re-homing the golden is cheap" is false for the same reason with WI-016 sitting immediately ahead in queue_order.
```


## Architectural Review

**Round 2. Recommendation: REVISE — return to exploration**

Cold-start re-read of the whole document against the tree at HEAD `2bf731f` + the seeded delta. Both of round 1's blocking findings are CLOSED, both non-blocking notes are taken, and I could not falsify anything the fold added. The two findings below are new and are the SAME defect class as round 1's — the criteria collide with each other, and the oracle has a reachable blind spot — but they land on text that predates the fold, in the part of `resolve()`/`resolve_all()` the fold had no reason to re-read.

### Trigger check

Fires on three, unchanged: significantly extends/replaces a core system (which code resolves email, and which person `resolve()` returns, across three consumer repos); touches >3 files in different concerns; effort > 1 day (four ordered cuts + a precondition artifact).

### Round 1's findings: HELD

- **Finding 1 (two baseline moments) is closed.** E7 states one baseline absolutely ("recorded ONCE, at Cut 0, against the code at this item's starting HEAD … never re-recorded"), fixes the three plants as literals rather than leaving the refused string to the spec-writer, and closes the exception list per arm. I re-executed every row of E7's table independently and all three hold: `Jane Roe <jane.roe@example.com>` → Jane Roe pre-cut via the whole lowered literal at person.py:197/:494 and post-cut via `parseaddr` at identifier.py:154-156, so it does not move under either arm; `kit@localhost` → Kit Baldwin pre-cut, **None** post-cut under the cutover arm (identifier.py:167-168 refuses it for the missing `.` in the domain, `normalize_phone` yields 0 digits so step 4 is skipped, and it is not a whole-word token of `kit baldwin`); `" dana@example.com "` → **None** pre-cut (`resolve` strips at person.py:480, the index key keeps the padding) and Dana Okafor post-cut under both arms. The E7 carve-out superset argument is also right: with today's `_email_index` unchanged, surface 4 would look up `jane.roe@example.com` and miss the bracketed-literal key, which is why the carve-out arm has to key both.
- **Finding 2 (WI-016 / re-homing) is closed.** `state/work-items.json:2017-2027` confirms `WI-022, WI-016, WI-023, …`, arm (b) is chosen explicitly, and E6 names the solve-in-one-place cost rather than waving it past. The corpus-vs-oracle distinction is the right axis to split on.
- **Both non-blocking notes taken.** AC-1's mechanism is now a literal-string scan over `tests/derivations.py:python_files_under` — verified public, `*roots`-parameterized, and it walks files rather than call graphs (derivations.py:183-197), so it sees the `def` itself, which `functions_calling` (derivations.py:871-885) provably cannot. Cut 4 now names `test_legacy_preserves_rich_note` (tests/test_wi126_body_preservation.py:209-215) and states that its engine twin at `:200-207` carries WI-126 alone.

### Blocking issues

**1. AC-2's four-surface agreement and AC-4's discriminant (ii) are jointly unsatisfiable on the fixture AC-4 mandates.** AC-4 (ii) requires that where person X carries `jane@example.com` as an ALIAS and a different person Y carries it as an EMAIL, `resolve("jane@example.com")` returns **X** — correctly, because `resolve` orders alias (person.py:488) before email (person.py:493). AC-2 requires that over a sweep containing "every `emails:` entry on every note", all four surfaces return the SAME person. `jane@example.com` IS one of Y's `emails:` entries, so it is in AC-2's sweep, and I hand-executed the four doors against that fixture: `get_by_email` → Y (person.py:391); `resolve` → **X** (alias step preempts); `resolve_all` highest-ranked → **Y** (email records first at 1.0 at person.py:573-578, alias records X at 1.0 at :581-585, both clear the floor, and `candidates.sort(key=confidence, reverse=True)` at :655 is stable so insertion order keeps Y first); `_resolve_identifier(Email.parse(...))` → Y. AC-2 says RED, AC-4 says the X answer is required. Both cannot ship.

   This is not the refused-string collision E7 closed — it is a second, independent one, and it survives the arm choice: it is identical under cutover and carve-out, because the alias index is not one of the four email doors at all. Nor does it go away if the discriminants get their own tmp vault: `## Approach` Cut 0 says the golden's query space is "derived from the fixture vault's own notes … plus the discriminating queries E4 names", which reads as one vault, and AC-4's derived space includes "each alias" — so whether the collision is in the golden fixture is currently undecided in the document, which is itself the finding (buildable two ways).

   Pick and write it: either (a) AC-2's agreement property is scoped to inputs that are NOT also aliases, with the alias-preemption named as a declared, permanent asymmetry (which is what it is — `resolve` is a cascade over four indexes, the other three doors are email-only, and AC-4 requires that preserved); or (b) the golden fixture is declared free of alias/email collisions and discriminant (ii) is hand-built on its own vault, with `## Approach` Cut 0 corrected to say so. Arm (a) is the honest one — "one authority for EMAIL" was never "one authority for RESOLVE" — but it needs saying, because AC-2's `why` currently reads as the stronger claim ("the answer does not depend on which of the four doors was used", third Example of done).

**2. E4 and AC-4 under-enumerate the divergence classes: `resolve_all` step 6 is a third, and the golden cannot see it.** E4 says "Two divergence classes, hand-executed", and AC-4 hand-states three discriminating queries on that basis. There is a third, at person.py:614-626 — the short-form first-token + last-initial match, which `resolve` has NO analogue for. Hand-executed: `resolve("emily m")` against a vault holding `Emily Mendes` returns None (step 1 misses, no `@`, 0 digits, and `"emily m"` is not an element of `["emily","mendes"]` at person.py:507), while `resolve_all("emily m")` with no company hint records Emily Mendes at 0.6 `partial-name` at :626, which clears the `>= 0.5` floor at :654 and is returned. A thin head — or any selection policy that keys on confidence and `matched_via` — returns Emily Mendes. That is `resolve()` newly claiming a match it declines today: the widening direction, on the exact query shape person.py:537 names as the live orchestrator case.

   Three things make this blocking rather than a footnote. **(i) The golden cannot reach it.** AC-4's derived query space is names, name tokens, aliases, emails, phones; a bare name token is one token and a full name hits exact-name, so no two-token-with-short-second query enters the space unless an alias happens to have that shape — and an alias query short-circuits at step 2/step 3 at 1.0 anyway. So the divergence is invisible to the oracle and unnamed in the prose, which is precisely the gap AC-4's own `why` says the hand-stated discriminants exist to fill. **(ii) The obvious policy cannot separate it from a case AC-4 requires preserved.** Step 5's single-token branch (:610-612) and step 6 (:624-626) record the SAME confidence (0.6) under the SAME `matched_via` label (`"partial-name"`), yet `resolve("sandy")` must return Sandy Forster and `resolve("emily m")` must return None. No pure function of `List[ResolveCandidate]` can do both; the policy has to read the QUERY as well (e.g. reject sub-1.0 candidates for multi-token queries). AC-4's structural clause permits that — it forbids reading `_cache`/`_alias_index`/`_email_index`/`_phone_index`, not the query — but nothing in the document tells the builder the constraint exists. **(iii) The code's own comment says the opposite.** person.py:615-617 states this match "stays low confidence (< 0.5) and gets filtered out below". It records 0.6 and the floor is 0.5, so it is not filtered — a builder auditing `resolve_all` for divergences will read that comment and correctly conclude step 6 is inert. It is not.

   Repair: add it to E4 as a third hand-executed divergence class and to AC-4 as discriminant (iv) — `resolve("emily m")` against a fixture holding `Emily Mendes`, no company hint, returns **None** — and update `## Approach` Cut 0, which currently says the golden carries "the discriminating queries E4 names" (two) while AC-4 already names three. While there, fix or flag the false comment at person.py:615-617; it is documentation that has stopped being true, which is the class AC-5 already owns.

### Non-blocking notes for the spec-writer

- **E6 undercounts the fixture it is costing.** It describes the item-local vault as "three or four purpose-built notes". The criteria mandate at least seven: E7's three plants (`Jane Roe`, `Kit Baldwin`, `Dana Okafor`), `John Smith` for discriminant (i), `Sandy Forster` for (iii), and the X/Y pair for (ii) — plus whatever AC-1's derived case set needs to cover Branches A/B/C. The cost argument (oracle-declaration vs realism-corpus) is unaffected and still right; the number is just wrong, and a spec that inherits "three or four" will build a fixture that cannot carry the ACs.
- **The policy must accept 0.6 and reject 0.65.** Reproducing today's answers means accepting step 5's single-token `partial-name` (0.6) while rejecting step 5's `token-subset` (0.65, discriminant (i)) — a policy that filters on a confidence threshold gets this exactly backwards. Worth stating in the spec so the build does not discover it by going red.
- **Determinism boundary, prior art, fit, duplication, boundaries, reversibility, cost — all still clean**, unchanged from round 1 and re-checked against the folded text. The live-corpus premise is still routed to a `## Write Targets` precondition with the decision rule stated in advance; the oracle idiom is still characterization/golden testing, which is the world's standard answer to "the baseline is about to be deleted", so there is no divergence to justify; the item still removes a duplicate rather than adding one; the compat re-export (person.py:78-85) and `find_or_create_stub`'s consumer contract (person.py:668-686) are still correctly declared untouchable.
- **Arc note.** Both rounds have found the same thing — two criteria that cannot both be satisfied on the fixture the document mandates — but at different sites, and round 1's site is genuinely closed. This is a converging ladder, not a treadmill: round 1 found the collision on the refused-string plant, round 2 finds the two that remained on the alias door and the short-form arm. I do not expect a third; the remaining `resolve`/`resolve_all` asymmetries are enumerated above and I swept the rest (exact-name, phone, empty-query, dedupe-and-stable-sort ordering) and found them identical.

```verdict
gate: architect
verdict: REVISE
date: 2026-09-06
model: claude-opus-5
targets: AC-2, AC-4, #exploration-notes, #approach
prior: held
basis: original
findings: 2/3
note: Round 1's two findings are closed and I could not falsify the fold, but two more criterion collisions remain on pre-fold text — AC-2's four-door agreement contradicts AC-4's alias-before-email discriminant on the very fixture AC-4 mandates, and E4's "two divergence classes" misses a third (`resolve_all` step 6, person.py:614-626, whose own comment falsely calls it sub-floor) that the derived golden cannot reach and that no confidence/matched_via policy can separate from a case AC-4 requires preserved.
```


## Architectural Review — 2026-09-06

**Round 3. Recommendation: PROMOTE to architected**

Cold-start re-read of the whole document against the tree at HEAD `2bf731f` + the seeded delta. Round 2's two blocking findings are CLOSED and its two non-blocking notes are taken. I re-executed every hand-executed claim in the document independently — including the ones the fold added — and could not falsify any of them. More decisively, I was able to **derive a selection policy that satisfies all four AC-4 discriminants, `resolve("sandy")`, and every 1.0-tie case simultaneously** (below), which is the thing round 2 could not yet assert: the item is not merely internally consistent, it is demonstrably buildable. The residue is three spec-level details, none of which requires an arm choice or a redesign, and all of which the spec-review gate can hold.

### Trigger check

Fires on three, unchanged: significantly extends/replaces a core system (which code resolves email, and which person `resolve()` returns, across three consumer repos); touches >3 files in different concerns; effort > 1 day (four ordered cuts + a precondition artifact).

### Round 2's findings: HELD

- **Finding 1 (AC-2 four-door agreement vs AC-4 discriminant (ii)) is closed, on the honest arm.** E8 takes arm (a) — scope the agreement property to non-alias inputs and **assert** the preemption rather than carve it out — and AC-2 now carries both halves as literals. I re-executed E8's four-door table against the tree: `get_by_email("pat@example.com")` → Rosa via `_email_index` (person.py:391); `resolve` → Alex, because step 2 (`:488`) precedes step 3 (`:493`); `resolve_all` → Rosa, because email records at 1.0 first (`:573-578`), alias records Alex at 1.0 second (`:581-585`), step 5 contributes nothing (`{"pat@example.com"}` shares no token with either cache key, so `:604-605` continues), step 6 needs `len(query_tokens) == 2` (`:618`), and the sort at `:655` is stable; `_resolve_identifier` → Rosa via `:955-956`. E8's claim that this costs the golden nothing is also right: Cut 1 never reaches step 2, so the value is Alex pre- and post-cut under both arms, and the exception list stays closed at two rows / one row.
- **Finding 2 (the third divergence class) is closed and correctly sourced.** E4 class (C) and AC-4 discriminant (iv) both land. Re-executed: `resolve("emily m")` misses steps 1–5 (`normalize_phone("emily m")` is `""`, and `"emily m"` is not an element of `["emily","mendes"]` at `:507`) → None; `resolve_all("emily m")` misses step 5 in both directions at `:607-612` and then records Emily Mendes at 0.6 `partial-name` at `:626`, which clears the `>= 0.5` floor at `:654`. The comment at `:615-617` does say "stays low confidence (< 0.5) and gets filtered out below" and is false, and AC-5 now owns its repair. `## Approach` Cut 0 now names four discriminants, matching AC-4.
- **Both non-blocking notes taken.** E6's fixture count is corrected against E8's roster and no longer says "three or four"; the accept-0.6-reject-0.65 constraint is now stated in E4, AC-4 and Cut 3 rather than left for the build to hit.

### What I verified this round, and what held

- **The selection policy exists.** E4's three constraints are not just individually forced, they are jointly *sufficient*, and the policy they describe is short: for a **single-token** query take the best candidate, breaking 1.0 ties by `matched_via` in `resolve`'s cascade order (exact-name > alias > email > phone); for a **multi-token** query accept only a 1.0 candidate. That reproduces every stated answer, because `resolve` step 5 is structurally single-token — `query_lower in name.split()` (person.py:507) can only be true for a query with no whitespace — so a multi-token query can be answered today *only* by steps 1–4, all of which score 1.0 in `resolve_all`. It also cannot be defeated by the confidence collision AC-4 names: step 5's `token-subset` needs `len(shared) >= 2` (`:608`), unreachable from a one-token query, and step 6 needs exactly two tokens (`:618`), so a single-token query's non-1.0 candidates are *only* step 5's 0.6 `partial-name` and a multi-token query's are *only* 0.65 and 0.6. I raise this as a held check rather than a note because it is the one thing that would have made this item a REVISE if it had come out the other way.
- **Every 1.0 tie other than alias/email already agrees.** Swept exact-name vs alias, exact-name vs email, exact-name vs phone, alias vs phone, email vs phone: in each pair `resolve`'s cascade order and `resolve_all`'s insertion order (`:567`, `:573`, `:581`, `:587`) rank them identically, so E4 class (B) is the only inversion and `matched_via` ordering is the whole fix. Empty and whitespace-only queries return None / `[]` consistently (`:477-478` vs `:547-548`).
- **E7's three rows re-execute correctly, and the plants are the right literals.** `identifier.py:154-156` routes `"Jane Roe <jane.roe@example.com>"` through `parseaddr` (it has both `<` and `>`) → `jane.roe@example.com`; `"kit@localhost"` has no angle brackets, survives the whitespace and single-`@` checks, and dies at `:167-168` on the missing `.` in the domain; `" dana@example.com "` is stripped at `:159` and parses. On the pre-cut side, `_index_entity` keys on `email.lower()` with no strip (person.py:197) while `get_by_email` and `resolve` both strip the query (`:390`, `:480`), which is exactly what makes Dana miss today and Kit hit. The padding survives load: `models.py:81` is a bare `emails: List[str]` and `models.py` contains **no** validator of any kind, and `parser.py` contains no `strip` call, so nothing between YAML and the index normalizes it.
- **E3's witness re-executes.** `("0790055852","44790055852")` → the `norm2.startswith("44") and norm1.startswith("0")` arm at `phone_normalization.py:79-80` returns `"790055852" == "790055852"` → True; `("0790055852","10790055852")` → the arm at `:86-88` returns `"0790055852" == "0790055852"` → True; `("44790055852","10790055852")` matches no arm → False. All three clear `MIN_DIGITS = 7` (`identifier.py:237`) and produce three distinct `phone:` keys (`:253-254`). No key function; the carve-out is forced and the Intent licenses it in terms.
- **AC-1's replacement mechanism is sound.** `tests/derivations.py:183-197` `python_files_under(*roots)` is public, `*roots`-parameterized, and `rglob`s files — so a literal-text scan over what it returns sees the `def` itself, which `functions_calling` (`:871-885`, "every function whose OWN body calls `name`", built on `_iter_functions` at `:217`) provably cannot.
- **The remaining citations still resolve and still mean what the doc says.** `_email_index`/`_phone_index`/`_alias_index`/`_slack_index`/`_identifier_index` are declared at person.py:156-167 with the collapse plan in the comment at `:160-167`; `_project_identifiers` skips unparseable values at `:246-252` and carries the three-month-old zero-failures claim at `:236-238`; `slack` is unprojected at `:238-242`; `get_by_phone` iterates the live `self._phone_index.items()` at `:417` while `_clear_indexes` mutates it in place at `:326-333`; `_split_trailing_paren`'s comment still points at the non-existent `docs/paren-decoration-at-the-door.md` at `:113`; the compat re-export and `find_or_create_stub`'s consumer contract are where E5 says they are.

### Review

**Fit:** Matches what this package established in WI-020/WI-021 — a derived AST/text wall in `tests/derivations.py` plus a hermetic fixture, rather than hand-enumerated site lists. AC-1's literal-text scan over `python_files_under` (derivations.py:183-197), AC-3's structural assertion that the `get_by_phone` loop's iterable is a call rather than a bare attribute, and AC-4's structural clause on `resolve`'s body are all the same idiom the last two shipped items used. The floor stays hermetic (E5), which is WI-024's standing constraint.

**Duplication:** The item *removes* the duplicate rather than adding one — that is its purpose. The one duplication it knowingly accepts is a second fixture vault beside WI-016's, and E6 now argues it on the right axis (a realism corpus that other suites may extend versus an oracle's byte-frozen declaration) and names the cost instead of waving past it. A fixture other tests may extend cannot be a golden's baseline; making them one artifact would be the error. The `lint_vault` repair rule is routed to WI-026 (E6) rather than grown into here, and E3's write-boundary phone canonicalization is minted as a follow-on rather than absorbed — both correct solve-in-one-place calls.

**Boundaries:** Ownership stays clean. `find_or_create_stub`'s signature/return/exception set (person.py:668-686) and the `normalize_phone`/`phones_match` compat re-export (person.py:78-85) are both declared untouchable, and both are load-bearing in consumer repos. The other three repositories' `resolve()` (`company.py:96`, `meeting.py:345`, `book.py:231`) are explicitly out of scope. E3 applies the WI-185 lens honestly — it names the write boundary (`normalize_phone` destroying the `+` at phone_normalization.py:52-55) as the real work item, states that the downstream fuzzy arm is the reconstruction, and then routes the seam fix out rather than smuggling a vault-wide migration and a region policy into a deletion item.

**Determinism boundary:** Clean, and deliberately so. No capability is handed to an LLM. The single empirical premise that cannot be reasoned about — the live-corpus refusal count — is routed to a `## Write Targets` precondition with a shape contract and a decision rule stated in advance, rather than to a builder's reading of a three-month-old docstring claim (person.py:236-238). That is the right side of the boundary and of LESSONS #7 and #32, and E3 goes further by making the phone carve-out an *executable* witness rather than a comment, which is the same instinct applied to a design decision.

**Reversibility:** Cut-by-cut. The oracle stands until Cut 4, which is the whole point of inverting the mint's order, and the deletion — the only irreversible step — happens last with two committed goldens already in the tree. Cut 1's arm is selected by an artifact, not by a build-time judgement call.

**Generalization:** Correctly scoped down. E5 kills the tempting over-reach ("collapse the per-kind dicts into views") by showing there is no `Alias` identifier type and `slack` is unprojectable, so the Intent's real property is one authority *per kind* — which is what AC-2 asserts.

**Cost & maintenance:** Net negative code (126 lines plus one cascade plus six vacuous cases), with the added cost being one frozen fixture and two golden files. The golden is data, not machinery, and it executes inside the existing ~1s floor.

**Build vs extend vs integrate:** Extend-then-delete, in that order, which is the only ordering that keeps an oracle alive across the behaviour-changing cuts.

**Prior art (outside view):** No divergence to justify. The constraint is "the pre-WI-125 oracle is about to be deleted", and the world's standard answer — characterization / approval / golden testing — is exactly what Cut 0 reaches for, including the standard discipline that the golden is recorded once against unchanged code and never regenerated. Nothing is being built *around* a subtracted capability, so this dimension raises nothing. The one place the item builds machinery rather than buying it (the derived query sweep) is cheaper than the alternative it replaces, which was a cross-repo live-vault replay.

### Notes (non-blocking) for the spec-writer

- **AC-3's phone plant is the one literal the fold left unfixed, and one of the three choices makes AC-3 unsatisfiable.** AC-3 says "a fixture note carrying **one of the three forms** is found by `get_by_phone` for the two forms that match it and NOT for the one that does not". `0790055852` is the **centre** of E3's non-transitivity triangle: hand-executed, it is matched by `44790055852` (`phone_normalization.py:79-80`) *and* by `10790055852` (`:86-88`), so a note carrying it is found by all three forms and the "NOT" clause has no witness. The note must carry an **outer** form — `44790055852` or `10790055852` — and the spec should fix which one as a literal, on E7's own stated grounds (an unfixed plant decides buildability). This is a note rather than a blocking finding because AC-3's own text discloses the constraint to anyone transcribing it, unlike rounds 1 and 2, where both readings looked equally sound and only hand-execution separated them.
- **The fixture needs a phone invariant as well as a name-token invariant, and for the same reason.** E8's no-shared-name-token rule exists because `resolve` step 5 returns the *first* `_cache` entry containing the token (person.py:506-508) and `_cache` order is the filesystem walk. `get_by_phone`'s fuzzy arm has the identical shape — it returns the first `_phone_index` entry that `phones_match` accepts (`:417-419`), in insertion order — and E6 asks for "phones on at least two" notes. So state the analogue: **no two fixture notes carry phones that `phones_match` unifies.** Without it, if AC-3's note carries `44790055852` and some other note carries `0790055852`, the query `10790055852` is answered by that other note and AC-3's "NOT" clause fails for a reason that has nothing to do with the property under test.
- **E8's roster is eight notes; the single fixture the Approach mandates needs at least ten.** E6 names the extras honestly ("at least one note carrying a `company:`", "phones on at least two"), so nothing is hidden — but E8 presents the roster as "fixed here as literals" and the extras are not. Since `## Approach` Cut 0 is emphatic that there is one vault and one baseline, the spec should carry a single complete roster (the eight plus the `company:`-bearing note for AC-1's Branch B and the phone note(s) for AC-3/Branch A), extending E8's sixteen-distinct-token invariant to cover them.
- **AC-1's golden sweep MUTATES the vault, so its case ORDER is part of the oracle.** `find_or_create_stub` creates on Branch C, and AC-1's case set includes "a not-present variant of each" name/email/phone — so every not-present case writes a note that is visible to every later case in the same run. The golden must therefore freeze the ordered case list as data (which "seeded from the golden's own declaration" implies but does not say), not re-derive the order from a filesystem walk at test time; and the spec should say whether the sweep runs in one vault sequentially or one case per fresh copy. Also worth pinning: a "not-present variant" of a phone must be not-present under `phones_match`, not merely under string equality — `10790055852` is a plausible-looking variant of `0790055852` that Branch A would resolve as a hit.
- **Under the carve-out arm, the removal path needs the same widening as the insert path.** E7 requires the surviving authority to key both the lowered raw entry and the parsed address. `_remove_entity_from_indexes` currently deletes only the lowered literal (person.py:337-342), so an `update_fields` that drops an email would leave the parsed-address key behind pointing at a stale cache key. Cheap, but it is exactly the kind of asymmetry a "widen the index" cut leaves behind.
- **Stage advance is owed to the conveyor.** This gate emits the verdict only; the stage move to `architected` belongs to `stage_advancer.py`, run by the driver.

```verdict
gate: architect
verdict: PROMOTE
date: 2026-09-06
model: claude-opus-5
note: Round 2's two findings are closed on the honest arms (E8 asserts the alias asymmetry rather than carving it out; E4 class (C) and AC-4 discriminant (iv) land with AC-5 owning the false comment at person.py:615-617), every hand-executed claim re-executes against the tree, and E4's three policy constraints are not just forced but jointly sufficient — a single-token/multi-token split with 1.0 ties ordered by `matched_via` reproduces all four discriminants and `resolve("sandy")`, so the item is demonstrably buildable and the residue is three spec-level fixture details, not an arm choice.
```


## AC Red-Team — 2026-09-06

Cold-start attack on the DRAFT `## Acceptance Criteria`, read after `## Intent`, `### Examples of done`, `## Problem / Motivation` and `## Exploration Notes` as the referent. The architect's three rounds are unusually thorough and I could not falsify their held claims; I re-executed the phone non-transitivity witness and the `resolve`/`resolve_all` cascade traces independently (person.py:458-510, :512-656; phone_normalization.py:58-90) and they check out. Two findings below are about the AC TEXT itself, not the architecture, and both were surfaced by round 3 as "non-blocking notes for the spec-writer" — I disagree with routing them past the human sign-off, because both are the exact "an unfixed plant decides buildability" shape this document itself treats as blocking everywhere else it appears (round 1's finding, round 2's finding, E7, E8).

**AC-3 — CRITICAL. The fixture literal is unpinned, and one of its three permitted choices makes the AC's own clause unsatisfiable.** AC-3 requires "a fixture note carrying **one of the three forms** [is] found by `get_by_phone` for the two forms that match it and NOT for the one that does not." The three forms are E3's non-transitivity triangle: `A = 0790055852` (center), `B = 44790055852`, `C = 10790055852`, with `match(A,B)=True`, `match(A,C)=True`, `match(B,C)=False` (re-executed against `phone_normalization.py:76-90`). If the fixture note carries `A` — the most natural first reach, since it's the plain UK-local form and the one E3's own witness table lists first — then querying with `B` and `C` **both** match it; there is no third query left that fails to match, so "the one that does not" names nothing and the criterion cannot be satisfied by ANY implementation, correct or otherwise. Only fixture choices `B` or `C` (the "outer" vertices) leave one matching and one non-matching query. A builder who reads AC-3 literally and reaches for the obvious `0790055852` fixture (exactly as E3's witness table presents it) ships an unbuildable test, discovers it mid-build, and re-derives the outer-vertex requirement from scratch — the exact cost this document's own E7/E8 sections exist to avoid by fixing plants as literals in advance. What would have to change: AC-3 names the literal (`44790055852` or `10790055852`) rather than "one of the three forms."

**AC-1 — MATERIAL. The branch-coverage claim is "by construction," but the roster the document elsewhere pins as literal does not construct it.** AC-1's `desc` asserts the derived case set "covers Branch A (email hit), Branch A (phone hit), Branch B (name+company reuse) and Branch C (create) by construction" because "every note contributes its exact name, its email, its phone." `## Approach` Cut 0 ties AC-1's sweep to the SAME single vault as AC-2/AC-4 — "the eight-note roster E8 fixes as literals" — and E8's roster table (eight rows: Jane Roe, Kit Baldwin, Dana Okafor, John Smith, Sandy Forster, Alex Nkemdirim, Rosa Delgado, Emily Mendes) names no `company:` field on any note and no `phones:` field on any note. Round 3 flagged this directly ("E8's roster is eight notes; the single fixture the Approach mandates needs at least ten") but routed it as a non-blocking spec-writer note rather than correcting AC-1's own coverage clause. As the roster currently stands, "every note contributes its... phone" is false (no note has one) and there is no company-bearing note for Branch B's name+company reuse — so AC-1's "by construction" claim is either false against the fixture the document actually pins, or true only against a roster that does not yet exist anywhere in this document. A build that takes AC-1 at its word and the eight-note roster at its word ships a golden sweep silently missing Branch A (phone) and Branch B, while AC-1 reads as if it were covered. What would have to change: extend E8's roster (or a cited superset of it) with a company-bearing and a phone-bearing note before AC-1's coverage clause is signable, not after.

**MINOR, non-blocking.** Round 3's other fixture note — "no two fixture notes carry phones that `phones_match` unifies" — is real (without it, AC-1's phone-hit sweep and AC-3's negative witness can cross-contaminate via insertion-order in `get_by_phone`'s fuzzy scan) but is a fixture-construction detail rather than a defect in the AC text itself; noting it here so it travels with the fold rather than getting rediscovered.

```verdict
gate: ac-red-team
verdict: REVISE
date: 2026-09-06
model: claude-sonnet-5
targets: AC-3, AC-1, #acceptance-criteria
prior: none
basis: original
findings: 2/3
note: AC-3's fixture literal is unpinned and its most natural choice (the non-transitivity witness's center value) makes the AC's own "NOT" clause unsatisfiable by any implementation; AC-1's "by construction" branch-coverage claim is unsupported by the eight-note roster the document elsewhere pins as literal (E8), which carries no company- or phone-bearing note.
```


## Spec Review — 2026-09-06

**Recommendation: REVISE — return to spec writer (gaps to fix)**

Rulings on record: the CUTOVER arm is selected by the committed corpus audit (D0, data-premise PROMOTE) and is not re-decided here; E3's phone carve-out, E6 arm (b) (the golden is never re-homed onto WI-016's fixture), E8's declared alias asymmetry, and Dave's AC sign-off at `ac_hash 583a1b6a293a` are scope boundaries I route against rather than re-litigate.

Cold-start read of the whole document from line 1, then of the code at every citation. This is an unusually well-grounded spec and I could not falsify any of its hand-executions — I re-derived AC-4's 39-query space (it comes out at exactly 39), AC-1's 10 base + 10 not-present cases and their arm assignment, D6's policy table against all seven rows, E3's triangle, E7's three rows, E8's two invariants, and D10's wall table against each wall's own source. The two blocking findings below are new and neither is about a claim being wrong: one is about a step the document does not specify at all, and one is a citation.

### Citation verification

Every `file:line` and symbol-anchored citation in the document was resolved against the tree and read for the property it is cited for. All verified except one:

- **`name_validation.py:385-387` (AC-1's `desc`) does not name the weak-identity guard.** Lines 384-396 are a `Tier1Branch` table entry (`branch_id="arrow_connective"`, `specimen="Acme -> Globex"`), unrelated to weak identity. The guard is `weak_identity_reason` at `obsidian_schemas/name_validation.py:502`, and the single-token-no-email-no-phone clause AC-1 is actually pointing at is `:530-532`. See blocking issue 2.

Spot-verified and correct, for the record: person.py `:78-85`, `:113`, `:156-167`, `:192-209`, `:236-255`, `:326-333`, `:337-342`, `:374-377`, `:390-392`, `:407-421`, `:458-510`, `:492-496`, `:506-508`, `:512-656`, `:571-578`, `:607-612`, `:614-626`, `:615-617` (the false sub-floor comment, against `:626` and the `>= 0.5` floor at `:654`), `:635-651`, `:640-643`, `:655`, `:665`, `:668-697`, `:675`, `:685`, `:699-824`, `:729`, `:866-870`, `:905-944`, `:920`, `:946-966`, `:1076-1080`; identifier.py `:3-4`, `:38-45`, `:143-177`, `:148-168`, `:154-156`, `:159`, `:167-168`, `:176`, `:237`, `:253-254`; phone_normalization.py `:25-27`, `:29-33`, `:52-55`, `:58-90`, `:79-80`, `:83-88`; models.py `:81` with zero validators in the file; base.py `:158-181`, `:174-181`, `:231`, `:231-245`; name_validation.py `weak_identity_reason:531-532` (D3's cite, exact); derivations.py `:183-197`, `:217`, `:586-617`, `:871-885`; test_loud_fail_harness.py `:74-97`, `:103`; test_name_gate_wall.py `_check_the_ast_capability_stays_single_homed` and `_check_the_loud_fail_write_universe_in_the_removal_direction` (`PERSON_FALSY_RETURN_FUNCTIONS` at `:1048-1054` contains none of the functions this item edits or deletes — D10's row is right); test_concurrent_access.py `:1074-1089` (the 4 / `write_markdown_file` / 8 / 4 / 3 pins, and Task 1's "expected 8" over `PACKAGE_ROOT` is correct); test_write_routing.py `:91`; test_vault_path_required.py `:387` and `:421`; ac_interpreter.py `:1-44` and `ensure_project_interpreter:123`; test_ac_interpreter.py `:40`; test_identity_index.py `:104`, `:183-201`; test_resolve_or_create.py `:173-179` (five `PARITY_CASES`, so "six vacuous cases" and Task 15's "seven removed" are both right), `:189-211`, `:214-224`; test_wi126_body_preservation.py `:200-207`, `:209-215`; test_repositories.py `:385-395`; concurrent-access.md `:8713-8714`; `docs/identity-cutover-corpus-audit.md` (the artifact carries every clause AC-5 pins, and its (a)–(e) numbers are as D0 quotes them).

### Blocking issues

**1. The Cut-0 recorder is specified as ONE temp vault for BOTH sweeps, and the stub sweep's pre-cut writeback rewrites two of the three email plants through the WI-021 gate — so the literal reading of the plan records a `resolve_golden.json` that contradicts E7's table and AC-4's exception list.**

D3(b) says the recorder "seeds a temp vault from `roster.json`, derives the case list and the query list by the rules below, executes them against **unchanged** code" — one vault, both lists, order unstated. Task 5 repeats the singular ("executes them against a temp vault seeded from `roster.json`"). The Edge Cases entry ("Every run seeds a fresh temp vault … replays the frozen ordered case list") is about AC-1's sweep only.

What the document does not say is what AC-1's sweep *does to the vault*, and it is not the benign append D3 describes. Hand-executed:

- Case 1 (`Jane Roe`, email `Jane Roe <jane.roe@example.com>`) resolves pre-cut through Branch B (`Email.parse` yields `jane.roe@example.com`, which misses `_email_index`'s bracketed-literal key — D3 says this correctly) and therefore calls `_writeback_identifier` (`obsidian_schemas/repositories/person.py:_writeback_identifier:1149-1180`). That routes through `update_fields`, which hands the delta to the semantic gate: `frontmatter.update(gate_write(updates, declared_type=…, whole_record=False))` (`obsidian_schemas/repositories/base.py:update_fields:473-475`). The gate's `emails` arm (`obsidian_schemas/name_gate.py:387-404`) runs `split_address` on every entry and rebuilds the list from `Email.parse(...).value` — so `["Jane Roe <jane.roe@example.com>", "jane.roe@example.com"]` normalizes to `["jane.roe@example.com"]`. **The angle-bracket plant is destroyed.** (`whole_record=False`, so M2 does not even preserve the display half in `aliases`.)
- Case 3 (`Dana Okafor`, email `" dana@example.com "`) does the same: `split_address(" dana@example.com ")` returns `("dana@example.com", "")` (`name_gate.py:split_address:97-135`, and `Email.parse` strips at `identifier.py:159`), so the list becomes `["dana@example.com"]`. **The whitespace plant is destroyed**, and `_email_index` gains the un-padded key.

If the recorder then derives the resolve golden in that same vault, two of E7's three rows record the wrong pre-cut answer:

| query | E7 / AC-4 says pre-cut | recorded in a shared vault |
|---|---|---|
| `Jane Roe <jane.roe@example.com>` | Jane Roe (and it does NOT move at Cut 1) | **None** — the bracketed key is gone, step 4 gets 0 digits, step 5 finds no whole-word token |
| `" dana@example.com "` | **None** (the exception row's literal) | Dana Okafor — `resolve` strips at `:480` and the un-padded key now hits |

Both consequences are exactly what the item exists to prevent. The first makes `Jane Roe <jane.roe@example.com>` a *third* query that moves at Cut 1, which AC-4 declares RED ("a query outside the list that moves is RED"). The second contradicts D2 tripwire clause 2, whose whole point is that `(" dana@example.com ", None)` is a literal in the check's own source — so the build discovers this as a red at Task 5 with no diagnosis in the document, and the cheapest-looking repairs from there (edit the literal, re-record) are both the defeat E7 and R3 were written to close.

This is not a judgment call the builder can make from the document: the gate's normalization of `emails[]` is named nowhere in it, and D3's own account of the divergence — "only the SIDE EFFECT differs (pre-cut Branch B calls `_writeback_identifier`, post-cut Branch A does not), and side effects are explicitly outside the parity contract (E5)" — reads as though the side effect were an append to a list nothing else consumes. E5's exclusion is about the *parity contract's* return values; it does not license a side effect that rewrites the oracle's own substrate.

Suggested fix, in the document rather than left to the build: state which arm — (a) each sweep gets its own freshly-seeded temp vault, so the resolve golden is recorded against the roster's bytes and the stub sweep's mutation is confined to a vault nothing else reads; or (b) one vault with the read-only resolve sweep ordered strictly first. Arm (a) is the one that survives someone reordering the recorder later. Either way, name the mechanism (`update_fields` → `gate_write` → `name_gate.py:387-404` rebuilds `emails[]` from `Email.parse(...).value`) where D3 currently says "only the side effect differs", and carry the same statement into the Edge Cases entry on the mutating sweep — otherwise the next reader re-derives it from scratch, which is what this document's own E4 comment finding says costs a review round.

**2. AC-1 cites `name_validation.py:385-387` for the weak-identity guard; those lines are an unrelated Tier-1 branch-table entry.**

AC-1's `desc` reads: "a not-present NAME is MULTI-TOKEN, because a single-token name with no email and no phone hits the weak-identity guard at `name_validation.py:385-387` and raises `WeakIdentityError` instead of reaching `create_stub`." Lines 384-396 of that file are `Tier1Branch(branch_id="arrow_connective", pattern="calendar_prefix", specimen="Acme -> Globex", …)`. The guard is `weak_identity_reason` (`obsidian_schemas/name_validation.py:502-538`); its case-1 clause is `:530-532`, and the raise is `resolve_or_create`'s at `obsidian_schemas/repositories/person.py:934`.

The *property* is true and I verified it independently, and D3's own citation of the same guard is exact (`obsidian_schemas/name_validation.py:weak_identity_reason:531-532`) — so nothing downstream is built wrong, and D3's not-present table already satisfies the constraint by construction (all twenty fresh names are two tokens). But this is a bare `file:line` in the one section that is frozen, hashed and quoted downstream, and it points at code that has nothing to do with the claim. Re-anchor it to the symbol, as D3 already does. I raise it as blocking rather than as a note because the automatic-REVISE rule on citations is unconditional and because a signed criterion is the worst place for a reader to be sent to the wrong lines; the pipeline's own framing is that a re-sign is the cheap side of this trade.

### Non-blocking notes

- **The `## Acceptance Criteria` preamble contradicts `## AC Sign-off`.** It still says "Draft — originated cold-start, approval-only mode … **Not yet frozen:** the `ac-signoff` fence is written by `bin/review-spec-helper.py` only after Dave's review, never by hand", while the signoff fence three sections below records `verdict: PROMOTE`, `provenance: verified`, five per-AC hashes and the artifact `docs/spec-reviews/WI-023-dave-review-2026-09-06.md`. Correct the preamble to say the criteria are frozen at `ac_hash 583a1b6a293a`; a reader who takes the preamble at its word will think the criteria are still editable.
- **`## Verification`'s non-vacuity claim over-promises by two.** It says "Every zero-count assertion is paired with a positive one" and then lists five zero-counts but only three positives — the two literal-string scans (zero sites for `_find_or_create_stub_legacy`, zero sites for `_email_index` under `PACKAGE_ROOT`) have no paired positive. The needle-assembled-from-parts control in Tasks 6 and 11 is the right control for a substring scan's *self-reference*, but it is not a non-vacuity pairing: a scan whose file list came back empty is green either way. One positive per scan (the file list is non-empty; the needle is found in a planted scratch file) closes it, and it costs a line.
- **Task 4 states an outcome but not the branch if the outcome does not hold.** "Both tests stay green; they are now differential rather than tautological" is a forward claim about six cases nobody has executed against `_find_or_create_stub_legacy` since WI-020 and WI-021 landed on `create_stub`/`save` (which E1 names as the reason the out-of-tree replay is stale). A red at Task 4 is a *finding* — the first real differential signal this item has — not a build error, and the spec should say which it is and who decides, because it lands before any production edit and the builder otherwise has no instruction.

### Carried-forward notes

Every still-open note from the prior gates is closed in the folded text and I re-read each against the tree rather than taking the fold's word:

- Architect round 3 note 5 / round 4 note 4 (`_remove_entity_from_indexes` needs the same widening as the insert path) — closed by D0's arm selection, correctly: under cutover the removal at `person.py:374-377` goes through `_project_identifiers`, the same projection that inserted, so the asymmetry cannot arise.
- Architect round 4 note 1 (Branch-C variant names must stay off `tomas`/`villalobos`) — folded as D3's third derivation constraint and satisfied by the pinned table.
- Architect round 4 note 2 (AC-1's per-case annotation names the arm, not the runtime branch) — folded; the golden's field is `arm` and D3 records which three cases fall through to Branch B pre-cut.
- Architect round 4 note 3 (Branch B sits exactly on the 0.85 threshold) — disclosed in D1 and E8 and carried forward as a known cost.
- AC red-team round 2's "noted, not escalated" (unpinned Branch-C name for the company case) — same fold as round 4 note 1.
- Data-premise's three: the cross-repo `orchestrator/docs/…` pointers are dispositioned as D8's named exclusion (with the line-wrap blind spot stated); `person.py:675` is named in D7; `person.py:685` is named in D7 and given its own Task 12.

```verdict
gate: spec-reviewer
verdict: REVISE
date: 2026-09-06
model: claude-opus-5
targets: AC-1, Task 4, Task 5, #design, #verification, #acceptance-criteria
prior: none
basis: original
findings: 2/5
note: The item's spine is a golden recorded ONCE at Cut 0, and D3(b)/Task 5 specify one temp vault for both sweeps in unstated order — but AC-1's pre-cut sweep reuses through Branch B and its `_writeback_identifier` routes through `update_fields` → `gate_write`, whose `emails` arm (name_gate.py:387-404) rebuilds the list from `Email.parse(...).value` and so destroys both the `Jane Roe <…>` and the `" dana@example.com "` plants, making the shared-vault reading record a resolve golden that contradicts E7's table on two of its three rows; separately AC-1's `name_validation.py:385-387` names a Tier-1 arrow-connective branch entry, not the weak-identity guard (`weak_identity_reason:502`, clause at `:530-532`), which D3's own symbol-anchored cite gets right.
```


## Adversarial Review — 2026-09-06

Cold-start hunt, run on a model distinct from spec-reviewer by construction. Read the driven doc end-to-end — Problem/Motivation through Exploration Notes E1–E8, Approach, Design D0–D10, Edge Cases, Implementation Plan, Write Targets, Verification, Verified Diagnosis, Scope Boundary, Risk Analysis, Acceptance Criteria, and all nine prior gate verdicts (architect ×4, ac-red-team ×2, data-premise, spec-reviewer, plus Dave's ac-signoff) — as the untrusted content an attacker's steering would have to hide inside. Also read the role's two referenced docs (`docs/work-item-pipeline.md`, `docs/compartmentalization-security-review.md`) and the two artifacts this item's Write Targets and sign-off depend on (`docs/identity-cutover-corpus-audit.md`, `docs/spec-reviews/WI-023-dave-review-2026-09-06.md`).

**Method.** Grepped the driven doc and the whole `obsidian_schemas` package for injection-style phrasing (ignore/disregard-previous-instructions, "emit PROMOTE", "as an AI", "system:"/"assistant:" turns, jailbreak language) and for zero-width/bidi Unicode control characters — no hits anywhere. Spot-verified that the document's heaviest-cited anchors are real code, not fabricated pointers a steering attempt might use to send a reviewer down a false trail: `person.py:458` is `def resolve(`, `:512` is `def resolve_all(`, `:946` is `def _resolve_identifier(` — exact matches to what E4/D6/AC-4 cite throughout.

**What's actually in the document.** Nine chained gate verdicts, each arguing for its OWN conclusion on THIS spec's substance (phone non-transitivity arithmetic, golden-baseline timing, fixture-roster completeness, a mis-anchored citation) — never for a downstream gate's verdict, and never addressed to a reviewer as an instruction. The dense persuasive prose throughout (`why:` clauses, "Rejected: ..." notes, the Risk Analysis) is a spec and its reviewers arguing their own merits — the ordinary shape this role's calibration section names explicitly as NOT an injection target. The most recent entry, the spec-reviewer's REVISE, argues in the opposite direction a planted "emit PROMOTE" would push, and its reasoning (the `gate_write`/`name_gate.py:387-404` mechanism, the `name_validation.py` mis-citation) re-executes against verifiable line numbers rather than asserting an outcome.

**Conclusion.** No text arguing for a verdict independent of the spec's merits, no instructions addressed to a reviewer/agent, no section whose form is spec content but whose effect is to steer a gate, and no prior verdict that reads as the product of such steering. This is a real finding — I looked and found nothing planted — not a skipped check.

```verdict
gate: injection-hunter
verdict: PROMOTE
date: 2026-09-06
model: claude-sonnet-5
note: No planted steering found across the driven doc, its nine prior gate verdicts, or its two cited artifacts (the corpus audit and Dave's spec-review record) — grepped for injection-style phrasing and hidden-Unicode control characters with zero hits, and spot-verified the document's heaviest-cited code anchors (person.py:458/512/946) resolve to real, matching definitions rather than fabricated pointers.
```


## Spec Review — 2026-09-06

**Round 2. Recommendation: REVISE — return to spec writer (gaps to fix)**

Rulings on record: the CUTOVER arm selected by the committed corpus audit (D0, data-premise PROMOTE), E3's phone carve-out, E6 arm (b) (the golden is never re-homed onto WI-016's fixture), E8's declared alias asymmetry, and Dave's AC sign-off at `ac_hash 583a1b6a293a` are scope boundaries I route against rather than re-litigate.

Cold-start read of the whole document from line 1, then of the code at every citation, with no reference to round 1's gaps list until the walk was finished. Round 1's two blocking findings are CLOSED and I re-derived both closures against the tree rather than reading the fold's account of them (below). The two blocking findings this round are new, both land on text that predates the fold, and both are the same shape: an enumeration this document treats as total that is one class short of the surface it covers.

### Citation verification

Every `file:line` and symbol-anchored citation in the document was re-resolved against the tree and read for the property it is cited for. **All verified — including the one round 1 failed.**

- **The round-1 mis-citation is repaired and the repair is correct.** AC-1's `desc` now reads `obsidian_schemas/name_validation.py:weak_identity_reason:531-532`. Read: `weak_identity_reason` is defined at `:502`, and `:531-532` is exactly `if " " not in name and not email and not phone: return "single-name, no email"` — the case-1 clause the criterion is about. The raise is `resolve_or_create`'s at `person.py:934`, as D3 says.
- Re-read for the property this round (not merely resolved): person.py `:156`/`:192-197`/`:200-209`/`:212-214` (the four index population arms and the sole `entity.emails` domain), `:229-262` (`_project_identifiers`' leniency + the 942-note claim), `:326-333`, `:335-377` (removal, including the `_project_identifiers`-driven identifier removal at `:374-377`), `:379-392`, `:394-421`, `:458-510`, `:512-656` (the whole `resolve_all` cascade, `record`'s dedupe-on-higher-confidence at `:558-565`, the stable sort at `:655`), `:658-697`, `:675`, `:685`, `:699-712`, `:826-944` (the three branches and `_IDENTIFIER_PRIORITY`), `:946-965`, `:1149-1180`; identifier.py `Email.parse:144-169` (the `parseaddr` gate at `:154-156`, the strip-and-lower at `:159`, the `malformed local@domain` raise at `:167-168`) and `Email.key:176`; phone_normalization.py `normalize_phone:39-55` and `phones_match:58-90` — all three of E3's triangle rows and both of E8 invariant 2's rows re-executed by hand against the arm structure, and the early-`return` on the UK arms versus the fall-through on the US arms is what makes `("44790055852","10790055852")` False; name_gate.py `gate_write:387-404` (the `emails` rebuild) and `split_address`; base.py `update_fields:473-475`, `load:231`, `_adopt:158-181`; derivations.py `python_files_under:183-206`, `_called_names:262-277` (which collects attribute calls by name, so `functions_calling` CAN see `self.resolve_all(...)` — AC-4's "calls `resolve_all`" clause is checkable with an existing export, no fourth derivation owed), `functions_calling:871-885`; test_loud_fail_harness.py `:74-97` and `:103`; test_name_gate_wall.py `PERSON_FALSY_RETURN_FUNCTIONS:1048-1054` (none of the functions this item edits or deletes is a member) and `:1132-1163`; test_concurrent_access.py `:1074-1089` (Task 1's "expected 8" over `PACKAGE_ROOT` is right); test_write_routing.py `:91`; test_vault_path_required.py `:387`/`:421-433`; test_ac_interpreter.py `:40` (`WORK_ITEM_DOC`), `:23-26` (`CORPUS_COUPLING`), `:98-123` (the wall Task 14 generalizes, and its `[ac_interpreter]` delegation assertion is what makes D9's first-statement rule load-bearing); test_resolve_or_create.py `:173-179` (five `PARITY_CASES`, so "six vacuous cases" and Task 15's "seven removed" are both right), `:189-211`, `:214-224`; test_identity_index.py `:182-201`; test_repositories.py `:288-298`, `:361-407`, `:868-871`; `docs/identity-cutover-corpus-audit.md` (carries every clause AC-5 pins, with (a)–(e) as D0 quotes them).

**Independently re-derived, not taken from the fold:** the 39-query space (10 notes × name + tokens + alias/email/phone, `pat@example.com` collapsing once — it comes out at exactly 39); AC-1's 10 base cases (7 per-email, 2 per-phone, 1 per-company) + 10 not-present, and their ordinal pairing; D6's policy table against all seven rows plus every query in the derived space; D3(b)'s gate mechanism end to end (`_writeback_identifier:1162-1174` → `update_fields:473-475` → `gate_write:391-404` collapses `["Jane Roe <jane.roe@example.com>", "jane.roe@example.com"]` to `["jane.roe@example.com"]`); D2's shared-vault tripwire (in a stub-swept vault `resolve("Jane Roe <jane.roe@example.com>")` really is None — `normalize_phone` splits on `@` and yields no digits, and the string is no whole-word token of `jane roe`); both E8 invariants; D10's eleven rows against each wall's own source.

**Also verified, because Cut 3 is the item's largest behavioural risk:** the policy in D6 reproduces `resolve()` on *every* input, not just the seven tabulated. Multi-token queries are answerable today only by steps 1–4 (step 5 tests `query_lower in name.split()`, `:507`), all of which score 1.0; single-token queries can reach neither the 0.65 `token-subset` arm (`len(shared) >= 2`, `:608`) nor step 6 (`len(query_tokens) == 2`, `:618`), so their only sub-1.0 candidates are step 5's 0.6 `partial-name`, and among those `by_person` insertion order is `self._cache.items()` order — the same order `resolve` step 5 walks — with a stable sort at `:655` preserving it. So `test_repositories.py`'s `resolve` battery (`:361-407`, including the substring-rejection promises at `:385-395`) survives Cut 3 by construction, not by hope.

### AC drift taxonomy (Check 12)

Diffed the evolved `## Acceptance Criteria` against the frozen originals in `docs/spec-reviews/WI-023-dave-review-2026-09-06.md` (`frozen_acceptance_criteria`), independently, criterion by criterion. **Exactly one diff, and it is not drift:** AC-1's weak-identity citation, `name_validation.py:385-387` → `obsidian_schemas/name_validation.py:weak_identity_reason:531-532`. Classified against the taxonomy: not strength-weakening (the promise — a not-present NAME is multi-token *because* the guard raises — is byte-identical), not actor-swap, not scope-narrowing, not oracle-swap, not exception-carving-by-addition. AC-2, AC-3, AC-4 and AC-5 are verbatim, `check:` and `kind:` unchanged on all five. The document discloses the edit and the owed re-sign in its own preamble rather than leaving it to the hashes, which is the right handling. **Routing, not a finding:** the re-sign is the conductor's D4b act before `→ ready`, not a spec-writer round, and it does not block this verdict in either direction.

### Blocking issues

**1. Cut 1 and Cut 3 falsify four documentation surfaces inside `person.py`, and the item's documentation-truth enumeration — which is total everywhere else — names none of them. The sharpest is in the very docstring D4 item 5 edits.**

This item's AC-5 is titled "The documentation surface tells the truth", its `why` names three specimens of "documentation that has stopped being true", and its stated method is generalization ("what stops the fix being one deleted line that the next stale pointer walks straight past"). D4 item 5 and D7's rider list read as total: six named repairs at `:113`, `:236-238`, `:238-242`, `:615-617`, `:675`, `:685`. Four more sites are falsified *by this item's own cuts* and are named nowhere:

- **`obsidian_schemas/repositories/person.py:_project_identifiers:231-234`** — "*the legacy per-kind dicts remain the permissive lookup surface during transition, so a malformed-but-present field still resolves the old way while this typed index just omits it*." After Cut 1 that is false for email, and Task 7 ships a test asserting its exact negation: a note carrying `not-an-email` "resolves through NO door". The spec would land, in one file, a test and a docstring that contradict each other. This is also the sentence four lines above the ones D4 item 5 rewrites, so the builder is standing on it — and D4's numbered list tells them to change `:236-238` and nothing else.
- **`person.py:__init__:160-167`** — the `_identifier_index` comment: "*the dicts stay the permissive lookup surface (zero parity risk)*" and "*Collapsing the dicts into views of this map + deleting them is the strangler's later deletion cut.*" After Cut 1 one dict is deleted rather than collapsed into a view, and E5 establishes that the rest never can be (no `Alias` type; `slack` unprojectable). D4 item 1 deletes the attribute at `:156`; the comment describing the plan survives it.
- **`person.py:_index_entity:193`** — `"""Build email, phone, and alias indexes."""` After Cut 1 there is no email index.
- **`person.py:resolve:462-467`** — "*Tries in order: 1. Exact name match 2. Alias match 3. Email match … 5. Partial name match*." After Cut 3 `resolve` tries nothing in order; `resolve_all` ranks in a *different* order (email before alias, `:571-572`) and the cascade priority moves into `_RESOLVE_CASCADE_ORDER`. D6 correctly comments the new constant — but the docstring that is a reader's first stop for "why does `resolve` prefer the alias?" still describes the deleted body.

Why this blocks rather than rides as a note: AC-5's check as Task 10 specifies it goes GREEN with all four in place, so nothing catches them; and the document's method everywhere else is exhaustive enumeration, so a builder reading D4/D7 as total (which is how they are written) leaves them. That is a judgment call that can go either way, in the one file whose truthfulness is a signed criterion. **Suggested fix, cheap and outside the frozen criteria:** name the four sites in D4 item 5 / D7's rider list, and fold the assertion into **Task 12** — which already exists as the precedent for "prove a documentation-truth repair separately from AC-5" — rather than reopening AC-5 and buying a second re-sign.

**2. Task 12 orders a zero-count text scan and names neither its needle nor a non-vacuity positive, and `## Verification`'s non-vacuity table — the fold that answered round 1's note — omits it and one other, so its "enumerated rather than claimed" claim is false by two.**

Task 12 (`:1130-1135`): "*no file under `python_files_under(PACKAGE_ROOT)` claims a replay confirms zero divergence over the real vault, and the surviving text points at the committed goldens*."

- **No needle.** Every other literal-string scan in this item pins its needle (`_email_index`, `_find_or_create_stub_legacy`, `paren-decoration-at-the-door`, `UNBLOCK:`). This one asks the builder to invent a predicate for a *paraphrase* — "Phase-5 replay"? "zero return-value divergence"? "confirms zero"? — and to invent what "points at the committed goldens" means (naming `stub_golden.json`? `resolve_golden.json`? a `tests/fixtures/` path?). Both are build-time judgment calls that could go either way, in a document that has spent eight gate rounds removing them.
- **No positive.** A scan for a needle the repaired text no longer contains is green; a scan for a needle that never existed is *also* green. WI-235's rule applies squarely: this is a count of structural matches backing a plan-task verify, and the spec names no match-shape and no near-miss. Tasks 6 and 11 both ship the right controls (needle assembled from parts + a planted scratch file that IS found); Task 12 ships neither, and Task 2's shapes fixtures cover the three new derivations, not this scan.
- **The table under-enumerates by two.** `## Verification`'s table (`:1272-1279`) is prefaced "*Every zero-count assertion carries a positive beside it, and the pairing is enumerated rather than claimed*". It lists five. Two more zero-count assertions exist in the plan and are absent: Task 12's above, and AC-5's "the string `paren-decoration-at-the-door` appears at zero sites" (Task 10) — the table's third row pairs only the *docs-mentions* half of Task 10. Round 1's note on this claim was that it over-promised by two; the fold that closed it now under-enumerates by two, which is the same class landing on the same sentence.

**Suggested fix:** pin Task 12's needle as a literal (and say what "points at the committed goldens" is checked as), give it the same two-part positive Tasks 6 and 11 carry, and add both missing rows to the table.

### Non-blocking notes

- **D2's `resolve_golden.json` example contradicts D3's stated derivation order.** `:379` shows `{"ordinal": 5, "arm": "email", "query": "kit@localhost", …}`. Under D3's rule (name, then each name token in order, then aliases, then emails, then phones, roster order) ordinal 5 is `Kit Baldwin` and `kit@localhost` is ordinal 8. The tripwire re-derives the list so nothing ships wrong, but the illustration is a counting inconsistency in the one snippet a builder will copy the schema from.
- **The resolve golden's `arm` vocabulary is never enumerated.** D3 fixes the stub golden's four arms by name (`per-email`/`per-phone`/`per-company`/`not-present`); the resolve golden's `arm` appears only as `"name"` and `"email"` in D2's example, with no closed list — while Task 5's tripwire asserts the query list "re-derives identically from the roster". Say whether `arm` participates in that comparison, and if so name the five values.
- **`## Verification`'s regression paragraph miscounts the deliberate edits.** `:1308` says "two of them are edited deliberately (Tasks 4/7/11)"; three of the enumerated modules are — `tests/test_resolve_or_create.py` (4, 11), `tests/test_identity_index.py` (7), `tests/test_wi126_body_preservation.py` (11). All three are correctly declared in `## Write Targets`; only the prose count is wrong.
- **Task 5 does not say how the recorder is invoked.** It is a non-`test_*` module under `tests/` run exactly once by hand; naming the command (`.venv/bin/python -m tests.record_identity_golden`, or a `__main__` guard) costs a clause and removes the last "would I stop and ask?" in the plan.

### Carried-forward notes

Round 1's findings were re-checked against the tree, not against the fold's account of them.

- Round 1 blocking 1 (one temp vault for both sweeps) — **CLOSED, on the arm that survives reordering.** D3(b) states the total rule ("every sweep that WRITES runs in its own freshly-seeded temp vault, and no sweep ever reads a vault another sweep wrote"), names the mechanism where the old text said "only the side effect differs", reconciles it explicitly with AC-4's "no second or throwaway vault" (that clause is about the ROSTER, and there is still exactly one), carries the statement into `## Edge Cases` and Task 5, and adds D2's shared-vault literal as a tripwire. I re-executed the gate path and the resulting `None` independently; both hold. Of the sweeps this item ships, exactly one writes — that enumeration is correct (AC-2, AC-3, AC-4 and AC-5's checks are all read-only).
- Round 1 blocking 2 (AC-1's `name_validation.py:385-387`) — **CLOSED**; see Citation verification and the drift-taxonomy section above.
- Round 1 note 1 (the AC preamble contradicting `## AC Sign-off`) — **CLOSED**; the preamble now reads FROZEN at `ac_hash 583a1b6a293a` and discloses the one refinement and the owed re-sign.
- Round 1 note 2 (the non-vacuity claim over-promising by two) — **the instance is closed** (both literal-string scans now carry the file-list-non-empty and planted-scratch positives, in the table and in Tasks 6 and 11), **but the same sentence now under-enumerates by two**; raised fresh as blocking issue 2 rather than carried, because it is a different defect on the same claim.
- Round 1 note 3 (Task 4 states an outcome but not the branch) — **CLOSED**; Task 4 now declares a red a FINDING, forbids the builder repairing it, and routes to Dave through the same door D0 sets for a nonzero close-out audit.
- Architect round 3 note 5 / round 4 note 4 (`_remove_entity_from_indexes` needs the insert path's widening) — still correctly closed by D0's arm selection. Re-verified against `test_repositories.py:868-871`: under cutover the removal at `:374-377` projects through `_project_identifiers`, the same projection that inserted, so the reindex-on-`update_fields` case stays green with `_email_index` gone.
- Architect round 4 notes 1–3 and AC red-team round 2's "noted, not escalated" — all folded (D3's third derivation constraint and its pinned not-present table; the golden's `arm` field with the three Branch-B fall-throughs recorded; the on-the-threshold disclosure in D1/E8). No re-deferral.
- Data-premise's three — the cross-repo `orchestrator/docs/…` exclusion (with the line-wrap blind spot stated) is D8's named exclusion; `person.py:675` is D7's; `person.py:685` is D7's plus Task 12. All still closed; issue 2 above is about Task 12's *predicate*, not about the site being unnamed.

```verdict
gate: spec-reviewer
verdict: REVISE
date: 2026-09-06
model: claude-opus-5
targets: Task 10, Task 12, #design, #verification
prior: held
basis: original
findings: 2/6
note: Round 1's two findings are closed and I re-derived both closures against the tree, but the item's documentation-truth enumeration is one class short of its own surface — Cut 1 and Cut 3 falsify four in-file surfaces D4/D7 do not name, sharpest being `_project_identifiers`' docstring at person.py:231-234 ("a malformed-but-present field still resolves the old way"), whose exact negation Task 7 ships as a test four lines below the ones D4 item 5 rewrites; and Task 12 orders a zero-count text scan with no pinned needle and no non-vacuity positive, while `## Verification`'s table that answered round 1's note now omits Task 12's and Task 10's `paren-decoration-at-the-door` zero-counts, so its "enumerated rather than claimed" pairing is false by two.
```


## Adversarial Review — 2026-09-06

Round 2 (re-verify, post-fold). Cold-start read of the whole document end to end — Problem/Motivation
through Exploration Notes E1–E8, Approach, Design D0–D10, Edge Cases, Implementation Plan, Write
Targets, Verification, Verified Diagnosis, Scope Boundary, Risk Analysis, Acceptance Criteria — and
every prior gate verdict, including the round-2 Spec Review (REVISE) and this gate's own prior round-1
PROMOTE, as the untrusted content an attacker's steering would have to hide inside. Also re-read the
role's two referenced docs (`docs/work-item-pipeline.md`, `docs/compartmentalization-security-review.md`,
the latter found only under `/Users/davewascha/Workspaces/workshop-stable/docs/`, this project carrying
neither) and the two grounding artifacts (`docs/identity-cutover-corpus-audit.md`,
`docs/spec-reviews/WI-023-dave-review-2026-09-06.md`).

**What's new since round 1's PROMOTE.** One section: Spec Review round 2 (lines ~2075-2151), a REVISE
citing two fresh documentation-truth gaps and a citation drift table. Everything before it is unchanged
text round 1 already cleared.

**Method.** Grepped the driven doc for injection-style phrasing (ignore/disregard-previous-instructions,
"emit PROMOTE", "as an AI", "SYSTEM:"/"ASSISTANT:" turns, jailbreak language, addressed-to-a-reviewer
phrasing like "trust me" / "skip this check" / "already approved") and for zero-width/bidi Unicode
control characters, over the whole file — no hits outside round 1's own method paragraph, which mentions
"emit PROMOTE" only to describe its own search terms (the example-self-trap shape, correctly not a live
instruction). Independently re-verified, rather than trusted, that the newest section's heaviest citations
are real and match the property claimed rather than being fabricated pointers to send a reviewer down a
false trail: `person.py:231-234` is exactly `_project_identifiers`'s docstring and reads "the legacy
per-kind dicts remain the permissive lookup surface during transition, so a malformed-but-present field
still resolves the old way while this typed index just omits it"; `:160-167` is exactly the
`_identifier_index` comment describing the dicts as staying "the permissive lookup surface (zero parity
risk)" and the collapse plan; `:193` is exactly `"""Build email, phone, and alias indexes."""`; `:462-467`
is exactly `resolve`'s "Tries in order: 1. Exact name match 2. Alias match 3. Email match…" docstring. All
four checked byte-for-byte against the tree, not assumed from the quote. Also grepped
`obsidian_schemas/` itself (not just the doc) for injection-style phrasing addressed to a reviewer —
no hits.

**What's actually in the new section.** A spec-reviewer arguing, on its own re-derived evidence, that the
spec's documentation-truth criterion (AC-5) is under-inclusive — the opposite of a steering attempt, which
would push toward PROMOTE, not toward a second REVISE round with two new named gaps. The prose is the
ordinary shape this role's calibration explicitly excludes: technical argument for the document's own
merits (or defects), never an instruction addressed to a gate, never text arguing for a downstream verdict
independent of the finding underneath it.

**Conclusion.** No text arguing for a verdict independent of the spec's merits, no instructions addressed
to a reviewer/agent, no section whose form is spec content but whose effect is to steer a gate, no prior
verdict that reads as the product of such steering, and no fabricated citation in the newest material. This
is a real finding — I looked again, at the delta and at the whole, and found nothing planted — not a
skipped check.

```verdict
gate: injection-hunter
verdict: PROMOTE
date: 2026-09-06
model: claude-sonnet-5
note: Re-hunted cold-start after the new Spec Review round 2 (REVISE) section landed; grepped the whole document and the touched package again for injection-style phrasing and hidden-Unicode control characters with zero hits beyond round 1's own method paragraph (which only names its search terms), and independently byte-verified the new section's four heaviest citations (person.py:231-234, :160-167, :193, :462-467) against the tree rather than trusting the quotes — all accurate, and the new material argues technically against the spec's own completeness rather than toward any verdict, the opposite direction a planted steer would push.
```


## Spec Review — 2026-09-06

**Round 3. Recommendation: REVISE — return to spec writer (gaps to fix)**

Rulings on record: the CUTOVER arm selected by the committed corpus audit (D0, data-premise PROMOTE), E3's phone carve-out, E6 arm (b) (the golden is never re-homed onto WI-016's fixture), E8's declared alias asymmetry, and Dave's AC sign-off are scope boundaries I route against rather than re-litigate.

Cold-start read of the whole document from line 1, then of the code at every citation, with no reference to round 2's gaps list until the walk was finished. Round 2's two blocking findings are CLOSED and I re-derived both closures against the tree rather than reading the fold's account of them. The two blocking findings this round are new. The first is the same discipline as round 2's first — a documentation-truth enumeration one member short — landing this time on the fold that was written to close it, which is why the repair I recommend is a change of *predicate*, not another site added to a list. The second is a contradiction inside the signed contract's own preamble.

### Citation verification

Every `file:line` and symbol-anchored citation was re-resolved against the tree and read for the property it is cited for. **All verified**, including every site D11 asserts. Because D11 is new material whose entire value is the accuracy of its site list, I checked it line by line rather than sampling:

- **Tier A's seven needles, at exactly the sites claimed and nowhere else in the package.** `_email_index` at `:156`, `:197`, `:328`, `:341-342`, `:391`, `:494`, `:574`; `_find_or_create_stub_legacy` at `:675`, `:699`; `Phase-5` at `:675`, `:685`, `:710`, `:851`, `:879` (and the surviving `Phase 2`/`Phase 3`/`Phase 4`/`Phase-4` forms really are distinct strings, so the hyphen scoping is right); `Tries in order` at `:462`; `Build email, phone, and alias indexes` at `:193`; `legacy Strategy` at `:863`, `:871`, `:874`; `legacy best-hit` at `:865`, `:912`.
- **Tier B's six sentence literals, one site each:** `zero parity risk` `:163`, `later deletion cut` `:165`, `during transition` `:233`, `resolves the old way` `:234`, `still indexes it` `:252`, `replay confirms zero` `:685`.
- **The three exclusions are correctly excluded.** `per-kind` survives at `:161`, `:232`, `:252`, `:271`, `:370` and `permissive lookup` at `:162` — a zero on either would go RED on text that is still true of the three surviving dicts. The census's "21 occurrences" is a count of matched LINES (`:675` carries two markers), which is what the per-line scan D11 prescribes returns; it is right.
- **D8's exclusion arithmetic is right for the same reason.** 26 `.md` mentions in `obsidian_schemas/`, of which 18 *lines* are vault-note illustrations (`book.py:156` and `:344` each carry two matches), 2 in-repo resolving (`name_validation.py:40`, `:347`), 1 in-repo dangling (`person.py:113`), 3 cross-repo (`identifier.py:4` as the wrapped tail `revised-2026-06-13.md`, `name_validation.py:29`, `person.py:729`). The starts-with-`docs/` clause excludes all three cross-repo pointers, including the wrapped one, exactly as D8 says.
- **Re-read for the property, not merely resolved:** person.py `:110-114`, `:140-152`, `:154-182`, `:192-223`, `:229-262`, `:264-277`, `:326-333`, `:335-377`, `:379-392`, `:394-421`, `:458-510`, `:512-544` (see blocking issue 1), `:545-656`, `:658-697`, `:699-732`, `:840-944`, `:946-966`; identifier.py `Email.parse:144-169` (the `parseaddr` gate at `:154-156`, the strip-and-lower at `:159`, the `malformed local@domain` raise at `:167-168`) and `Email.key:176-177`; derivations.py `python_files_under:183-206`; test_loud_fail_harness.py `:65-116` (the six-name required subset at `:74-97`, explicitly "not a cardinality bound", and the set-EQUALITY ast home at `:103-113`); test_write_routing.py `:87-106`; test_vault_path_required.py `DOC_SCAN_EXCLUDED:387` and `_scanned_markdown_files:421-433`; test_ac_interpreter.py `:23-26`, `:40`, `:57-95`, `:98-123`; tests/`__init__.py` present, so Task 5's `python -m tests.record_identity_golden` resolves the way every other module in the suite imports.
- **Independently re-derived, not taken from the fold:** the 39-query space (39 exactly, with `pat@example.com` collapsing once); AC-1's 10 base cases and their ordinal assignment (7 per-email, 2 per-phone, 1 per-company — `Alex Nkemdirim` contributing none), which makes D3's not-present table's pairings 18↔8, 19↔9 and 20↔10 correct; D2's ordinal 8 for `kit@localhost`; E7's three rows on both sides of Cut 1; D6's policy against all seven tabulated rows.

### Blocking issues

**1. D11 closes the strangler-prose class by a list, and the list is one member short — the missing member is `resolve_all`'s own docstring, ninety lines above the comment in that same function D11 does name.**

`obsidian_schemas/repositories/person.py:resolve_all:517-539` is not in D11's fifteen-row table, is matched by none of the six census markers, and is not a Tier A or Tier B needle. It carries two defects of exactly the classes this item exists to end:

- **`:520-521` states P4 in the file's own words.** "*resolve() returns a single Optional[Person] and stops at the first cascade hit; resolve_all returns ALL plausible candidates ranked by confidence.*" After Cut 3 `resolve()` does not stop at the first cascade hit — it ranks the whole cascade through `resolve_all` and applies `select_resolution`, which for a multi-token query REJECTS the only candidate the cascade found (D6, the 0.65 `token-subset` row). D11's own repair text for `resolve:462-467` is "after this cut `resolve` tries nothing in order"; this sentence tells the reader the opposite, in the docstring of the function `resolve` is about to be built on. That is Tier B's stated purpose — "a falsified proposition restated in the file's own words" — and the literal `stops at the first cascade hit` occurs exactly once in the package, so it is pinnable at the same cost as the other six.
- **`:536-539` is false today, about the very branch AC-5 already repairs a comment for.** "*This catches "Emily M" + company="Speechmatics" → canonical Emily Mendes bumped 0.65 → 0.90 ≥ 0.85 cutoff for safe reuse.*" Hand-executed: `"Emily M"` cannot reach the 0.65 `token-subset` arm at all — it needs `len(shared) >= 2` (`:608`) and shares only `emily` — so step 6 records **0.6** at `:626` and the bump yields **exactly 0.85**, with no margin. The 0.65 → 0.90 arithmetic belongs to the two-shared-token Naomi Pavie case the same sentence also names, and the two are conflated. This matters beyond tidiness: E8, D1 and architect round 4's third note all record that the corroborated short-form case sits precisely ON the threshold with no float slack, and `person.py` tells its reader there is 0.05 of headroom. It is the identical misreading-invitation as `:615-617`, which AC-5 owns and whose `why` says it "is the reason E4's third divergence class went unnamed through a full round of review". *(Rider in the same sentence: "see the code at person.py:~476" — the company bump is at `:628-651`.)*
- **Corroboration that the enumeration, not the site, is the defect.** D11's `this cut` exclusion paragraph names four surviving sites (`identifier.py:386`, `:411`, `person.py:242`, `:875`). There are five: `person.py:860` also carries it, inside `resolve_or_create`'s Branch-A prose — and unlike the four, that one is *not* a true sentence after Cut 1 ("email/phone via the legacy fuzzy `get_by_email`/`get_by_phone`"). It is inside the `:858-863` range Task 11 rewrites, so it will be repaired, but the paragraph that enumerates it gets the count and the disposition wrong. Meanwhile the member D11 *does* claim for that paragraph, `_resolve_identifier:949-951`, is line-WRAPPED (`this` ends `:950`, `cut` begins `:951`), so no per-line scan could ever have seen it either way.

Why this blocks rather than rides as a note: the `resolve_all` docstring is the second-most-read prose in the file after `resolve`'s, it will contradict `resolve`'s repaired docstring inside the same commit, and nothing in the plan can find it — Task 12 scans thirteen needles derived from the table, so a member absent from the table has no needle, and clause (d)'s positives prove the scan finds what it was given, never that it was given everything.

**The repair, and why it should not be "add a sixteenth row."** Round 2's finding was this class; D11 was the audit fold; the fold is one member short in the same round it declares the class closed. The generator is fine — five propositions, correctly derived. What under-reaches is the *finding* predicate: a hand-picked marker set plus a reading pass, where the reading pass has now missed a member twice (D11 admits `_index_entity:193` was a marker miss found by reading, and this round the reading missed `resolve_all:517-539`). Close it over a surface the document already enumerates at source instead: **every function this item edits or deletes** — `__init__`, `_index_entity`, `_project_identifiers`, `_index_identifiers`, `_split_trailing_paren`, `get_by_email`, `get_by_phone`, `resolve`, `resolve_all`, `find_or_create_stub`, `_find_or_create_stub_legacy`, `resolve_or_create`, `_resolve_identifier` — is a closed set D4/D5/D6/D7 already name, every prose surface inside it is falsification-suspect by construction, and `tests/derivations.py` already owns the function-boundary machinery (`_iter_functions:217`) the item is extending anyway. Then the needle list is what it should be — a cheap regression pin over sentences already read — rather than the thing that decides which sentences get read. Whatever arm is chosen, `resolve_all:520-521` and `:536-539` need a row, a task and (for the first) a Tier B literal.

**2. The `## Acceptance Criteria` preamble and the `## AC Sign-off` fence record two different sign-offs, and the artifact the fence names is not in the tree.**

The preamble (`:1749`) says the criteria are "**FROZEN**: Dave signed this set on 2026-09-06 and the `## AC Sign-off` fence below records it at `ac_hash 583a1b6a293a` … artifact `docs/spec-reviews/WI-023-dave-review-2026-09-06.md`", and closes "it invalidates the frozen hashes (D4b), so a re-sign is owed before `→ ready`."

The fence records something else: `ac_hash: a8c767cdccea`, `signoff_escalation: ESC-WI-023-specced-awaiting-ac-signoff-90fe7e3e` (stage `specced`, not `exploring`), `artifact: docs/spec-reviews/WI-023-dave-review-2026-09-06-2.md`. Its per-AC hashes are internally coherent with a genuine D4b re-sign taken *after* the citation repair: `ac_hash_AC-2..AC-5` are byte-identical to the origination artifact's, and only `ac_hash_AC-1` moved (`bd76924cea03` → `97b4e402abd5`). So the re-sign the preamble says is owed has, on the fence's own evidence, already happened.

Two consequences, both cheap to fix and expensive to ship:

- **The artifact the in-force fence names does not exist in this tree.** `docs/spec-reviews/` holds `WI-023-dave-review-2026-09-06.md` (the origination sign-off, `spec_stage_at_review: exploring`, `ac_hash 583a1b6a293a`, whose frozen AC-1 still carries the old `name_validation.py:385-387` citation at `:68`) and no `-2` sibling. Check 12's referent for the *current* frozen set is therefore unreadable from this tree, and I ran this round's drift diff against the origination artifact by necessity. This half is the conductor's to close, not the spec-writer's — I raise it here because the document is what points at the missing path.
- **The preamble's restatement can never be true, and that is why it has now broken twice.** `ac_hash` is `hash_section(body, "Acceptance Criteria")` (`src/ac_signoff.py:1817`) — the whole section, preamble included. A preamble that names the hash of the section it sits inside falsifies that hash the moment it is edited to be correct. Round 1's note asked for this text to be corrected and it was; one re-sign later it is stale again in a new way. The stable fix is to stop restating the record: say the criteria are frozen and that the in-force record is the `## AC Sign-off` fence, and let the fence be the single place the hash, the artifact and the escalation are stated. That costs one D4b re-sign — the same act that has to produce the missing artifact anyway — and then never goes stale again.

### Non-blocking notes

- **`## Verification` says twelve needles; D11 and Task 12 say thirteen.** The loud-fail bullet reads "any of D11's **twelve** needles surviving in `obsidian_schemas/`", while Tier A is seven and Tier B is six, the non-vacuity table's row says "thirteen", and Task 12(d) says "ALL THIRTEEN". Nothing is built off the prose count, but this is the third round in a row that a count in this one section has been wrong by a small integer (round 1: over-promised by two; round 2: under-enumerated by two), so it is worth fixing as a class rather than as a digit — every count in `## Verification` is derivable from a section that states the members, and could cite it instead of restating it.
- **"All must be green at every task boundary" is false at the Task 6 boundary, by design.** Cut 1 deletes `_email_index` in Task 6; `tests/test_identity_index.py:183-201` asserts `"not-an-email" in repo._email_index` until Task 7 rewrites it. The regression paragraph's flat claim, read literally, tells a builder that a red there is a defect — when it is the plan working. Say the boundary is the CUT (Tasks 6 and 7 land as one commit), or name the transient red and its two case names.
- **AC-5's check reads a live `docs/**` artifact and the spec declares no coupling for it.** `tests/test_identity_endgame.py` will read `docs/identity-cutover-corpus-audit.md` at run time and pin its shape. Both existing modules in this repo that do this carry a one-line coupling declaration in their own docstring (`tests/test_company_name_contract.py:15`, `tests/test_ac_interpreter.py:23`), and Task 14 is careful to update that declaration for the other doc read it adds — so the convention is established and this module is the one place it is skipped. One line in the new module's docstring closes it.

### Carried-forward notes

Every prior round's still-open note was re-checked against the tree, not against the fold's account of it.

- Round 2 blocking 1 (four falsified in-file surfaces unnamed) — **CLOSED.** All four are in D11's table with a proposition, a falsifying cut and a landing task (`:231-234` and `:252` → Task 6, `:160-167` → Task 6, `:193` → Task 6 and pinned as its own Tier A literal precisely because the marker scan missed it, `:462-467` → Task 9), and D4 item 5 / D7's rider list now say out loud that they are not total. Blocking issue 1 above is a new member, not a re-opening.
- Round 2 blocking 2 (Task 12's unpinned needle, no positive, table short by two) — **CLOSED.** Thirteen literals pinned and assembled from parts, the two-part positive plus a case-sensitive near-miss (`Phase-4`, `email_index`, `legacy strategy`), the presence assertion on `stub_golden.json`/`resolve_golden.json` so Tier B's `replay confirms zero` cannot go green by deletion, and a table that now states its generating rule and runs to nine rows. I re-ran that rule over the plan as it stands and it returns nine.
- Round 2 notes 1–4 — all **CLOSED** and re-verified: `kit@localhost` is ordinal 8 in D2's snippet and in D3's derivation; the resolve golden's `arm` vocabulary is closed at five and participates in the tripwire's `(ordinal, arm, query)` comparison; the regression paragraph now says three deliberately-edited modules and names them; Task 5 gives the recorder a `__main__` guard and the literal invocation, which resolves because `tests/` is a package.
- Round 1's two blocking and three notes — still closed (D3(b)'s per-sweep seeding with the `gate_write` mechanism named; AC-1's symbol-anchored weak-identity citation; Task 4's red-is-a-finding door). The round-1 preamble note is closed *in its round-1 form* and has re-broken in a new one — raised fresh as blocking issue 2 rather than carried, because it is a different defect on the same sentence.
- Architect rounds 3/4 and both red-team rounds — all folded and still folded: the `_remove_entity_from_indexes` note stays closed by D0's arm selection (I re-read `:374-377`, which removes identifier keys through the same `_project_identifiers` projection that inserted them); the Branch-C variant names are pinned and off `tomas`/`villalobos`; the per-case `arm`-not-branch record is D3's; the on-the-threshold disclosure is carried in D1 and E8 — and blocking issue 1's second clause is that `person.py` itself still contradicts that disclosure.
- Data-premise's three — the cross-repo `orchestrator/docs/…` exclusion is D8's named exclusion with the line-wrap blind spot stated (I re-derived all 26 mentions and the class split); `person.py:675` is D7's; `person.py:685` is D7's plus Task 12's presence clause. All closed.

```verdict
gate: spec-reviewer
verdict: REVISE
date: 2026-09-06
model: claude-opus-5
targets: #design, Task 9, Task 12, #acceptance-criteria, #ac-sign-off
prior: held
basis: folded-material
findings: 2/5
note: Round 2's two findings are closed and I re-derived both closures against the tree, but D11 — the fold written to close the strangler-prose class — is itself one member short: `resolve_all`'s docstring at person.py:520-521 states P4 in the file's own words ("resolve() … stops at the first cascade hit", which Cut 3 ends) and at :536-539 asserts the "Emily M" case is "bumped 0.65 → 0.90" when step 6 records 0.6 at :626 and the bump lands on exactly 0.85, contradicting this document's own no-slack threshold disclosure — ninety lines above the `:615-617` comment D11 does name, reachable by no needle the plan pins, so the fix is a finding predicate scoped to the functions the cuts edit rather than a sixteenth table row; separately the AC preamble names `ac_hash 583a1b6a293a` and says a re-sign is owed while the `## AC Sign-off` fence records a completed D4b at `a8c767cdccea` whose artifact `docs/spec-reviews/WI-023-dave-review-2026-09-06-2.md` is absent from the tree.
```


## Adversarial Review — 2026-09-06

Round 3 (re-verify, post-fold). Cold-start read of the whole document end to end — Problem/Motivation
through Exploration Notes E1–E8, Approach, Design D0–D11, Edge Cases, Implementation Plan, Write
Targets, Verification, Verified Diagnosis, Scope Boundary, Risk Analysis, Acceptance Criteria — and
every prior gate verdict, including the round-3 Spec Review (REVISE) and this gate's own prior two
PROMOTEs, as the untrusted content an attacker's steering would have to hide inside. Re-read the two
role-referenced docs by their actual location, since this project carries neither under its own
`docs/`: `work-item-pipeline.md` and `compartmentalization-security-review.md` are absent from this
tree (confirmed by glob, matching round 2's finding — not re-litigated here since it is not this
gate's question). Re-read both grounding artifacts in full: `docs/identity-cutover-corpus-audit.md`
and `docs/spec-reviews/WI-023-dave-review-2026-09-06.md` (the only sign-off artifact present in the
tree; the `-2` sibling the current `## AC Sign-off` fence names is genuinely missing, which is
round 3's own finding, not something I take on trust — confirmed by glob here independently).

**What's new since round 2's PROMOTE.** One section: Spec Review round 3 (a REVISE), naming a
`resolve_all` docstring gap and a sign-off-artifact/preamble mismatch.

**Method.** Grepped the whole document for injection-style phrasing (ignore/disregard-previous-
instructions, "emit PROMOTE"/"emit REVISE"/"emit REJECT", "as an AI", "SYSTEM:"/"ASSISTANT:" turns,
jailbreak language, addressed-to-a-reviewer phrasing — "trust me", "skip this check", "already
approved", "do not flag/report/review", "this is pre-approved/authorized", "override your",
"reviewer should") and separately for zero-width/bidi Unicode control characters, over the whole
file. The only hits are in rounds 1 and 2's own method paragraphs, which name "emit PROMOTE" and the
other terms only to describe their own search vocabulary — the example-self-trap shape this role's
contract itself warns about, correctly not a live instruction. Zero Unicode control-character hits
anywhere in the file. Independently re-verified, rather than trusted, the newest section's two
heaviest citations: `person.py:521` reads exactly "and stops at the first cascade hit; resolve_all
returns ALL plausible" and `:537-538` reads exactly "canonical Emily Mendes bumped 0.65 → 0.90 ≥
0.85 cutoff for safe reuse" — both byte-accurate to what Spec Review round 3 quotes, not fabricated
pointers built to send a reviewer down a false trail. Also confirmed independently that
`docs/spec-reviews/WI-023-dave-review-2026-09-06-2.md` does not exist in this tree (a `Glob` for
`docs/spec-reviews/WI-023*` returns only the origination artifact) — the same absence Spec Review
round 3 reports, not contradicted by anything I found.

**What's actually in the new section.** A spec-reviewer arguing, on its own re-derived evidence,
that (1) a fold meant to close a prose-truth class missed one member in the very function the item's
consolidation cut is built on, and (2) the document's own sign-off preamble and its sign-off fence
disagree about which hash and which artifact are in force. Both are technical findings against the
document's internal consistency, argued from re-executed arithmetic and re-resolved citations — the
opposite direction a planted "emit PROMOTE" or "trust the prior gates" would push, and neither reads
as an instruction addressed to a gate rather than a description of the work.

**Conclusion.** No text arguing for a verdict independent of the spec's merits, no instructions
addressed to a reviewer/agent, no section whose form is spec content but whose effect is to steer a
gate, no prior verdict that reads as the product of such steering, and no fabricated citation in the
newest material — both citations I spot-checked resolve exactly as quoted. This is a real finding —
I looked again, at the delta and at the whole, and found nothing planted — not a skipped check.

```verdict
gate: injection-hunter
verdict: PROMOTE
date: 2026-09-06
model: claude-sonnet-5
note: Re-hunted cold-start after Spec Review round 3 (REVISE) landed; grepped the whole document again for injection-style phrasing and hidden-Unicode control characters with zero hits beyond the prior rounds' own method paragraphs (which only name their search terms), and independently byte-verified round 3's two heaviest citations (person.py:521, :537-538) against the tree — both accurate — plus the reported absence of the `-2` sign-off artifact via an independent glob; the new material argues technical inconsistency (an unfixed docstring, a sign-off preamble/fence mismatch) rather than pushing toward any verdict, the opposite direction a planted steer would push.
```


## Spec Review — 2026-09-07

**Round 4. Recommendation: REVISE — return to spec writer (gaps to fix)**

Rulings on record: the CUTOVER arm selected by the committed corpus audit (D0, data-premise PROMOTE), E3's phone carve-out, E6 arm (b) (the golden is never re-homed onto WI-016's fixture), E8's declared alias asymmetry, and Dave's AC sign-off are scope boundaries I route against rather than re-litigate.

Cold-start read of the whole document from line 1, then of the code at every citation, with no
reference to round 3's gaps list until the walk was finished. Round 3's two blocking findings are
CLOSED and I re-derived both closures against the tree rather than reading the fold's account of
them. The two blocking findings this round are new, and neither is about a claim being wrong. The
first is a universal quantifier over an enumerable domain — D11's authorized owners — that is
provably FALSE for two of its fifteen members by the fold's own table, so the check the fold ships
is RED against a correct build. The second is mechanical and total: the threat model landed four
`kind: required` mitigations on 2026-09-07 and the document has not been folded since, so three of
them name work no task orders and there is no `## Mitigation Folds` section at all.

### Citation verification

Every `file:line` and symbol-anchored citation was re-resolved against the tree and read for the
property it is cited for. **All verified.** The injected drift audit reported 28 symbol-anchored
citations resolved with 0 findings; I treated that as a floor and read the code at each regardless,
because a symbol that resolves can still mean something the spec does not claim.

- **D11's needle site lists are exact, and I checked them by scan rather than by sampling** — a
  per-line literal scan over `obsidian_schemas/` returns `_email_index` at `:156`, `:197`, `:328`,
  `:341-342`, `:391`, `:494`, `:574`; `Phase-5` at `:675`, `:685`, `:710`, `:851`, `:879`;
  `Tries in order` at `:462`; `Build email, phone, and alias indexes` at `:193`; `legacy Strategy`
  at `:863`, `:871`, `:874`; `legacy best-hit` at `:865`, `:912`; and each Tier B literal at exactly
  one site (`zero parity risk` `:163`, `later deletion cut` `:165`, `during transition` `:233`,
  `resolves the old way` `:234`, `still indexes it` `:252`, `stops at the first cascade hit` `:521`,
  `bumped 0.65` `:538`, `person.py:~476` `:536`, `replay confirms zero` `:685`). All in
  `person.py` alone.
- **The round-3 fold's own two members are where D11 says they are and say what it quotes.**
  `:521` reads "and stops at the first cascade hit; resolve_all returns ALL plausible"; `:536-538`
  reads "see the code at person.py:~476 … canonical Emily Mendes bumped 0.65 → 0.90 ≥ 0.85 cutoff".
  Re-executed: `"Emily M"` shares only `emily`, so `:607-608`'s `len(shared) >= 2` cannot fire; step
  6 records `0.6` at `:626`; the bump's field arm at `:640-643` yields exactly `0.85` against the
  `>= threshold` at `:920` with the default at `:665`. The docstring's arithmetic is conflated and
  D11's repair text is the correct one.
- **The three exclusions are still correctly excluded, and the corrected `this cut` count is right.**
  Five unwrapped sites — `identifier.py:386`, `:411`, `person.py:242`, `:860`, `:875` — with `:860`
  the member and the other four true survivors, plus the wrapped sixth at
  `_resolve_identifier:950-951` (`this` ends `:950`, `cut` begins `:951`). Confirmed by reading all
  six.
- **D8's two new-predicate rules check out against their substrate.** `tests/derivations.py` imports
  `ast` at `:24` only; `_iter_functions:217` and `python_files_under:183` are the spans `prose_lines`
  is built on; `tests/test_loud_fail_harness.py:_check_derivations_are_single_sourced:74-97` really
  does pin six names as a "required subset, not a cardinality bound" (`:77-78`) with the set-EQUALITY
  `ast` home at `:103-113`, so four more exports and a `tokenize` import join legally.
- **The threat model's premises, re-derived rather than inherited.**
  `obsidian_schemas/repositories/base.py:_is_unconfigured:86-91` swallows `None`, a blank string and
  `Path(".")`, and `_resolve_vault_path:94-104` falls through to `OBSIDIAN_VAULT_PATH` before
  raising; `tests/test_vault_path_required.py:test_no_implicit_vault_path_defaults:312-331` walks
  `obsidian_schemas` and `scripts` only, and `NO_ARG_CONSTRUCTION` is at `:382`. M1–M3's premise is
  correct and the gap it names is real.
- Re-read for the property, not merely resolved: person.py `:105-137` (the `<module>`-owned pointer
  at `:110-113` really does sit above `_TRAILING_PAREN_RE:114` and outside `_split_trailing_paren:117`),
  `:140-182`, `:192-223`, `:229-262`, `:326-333`, `:335-377`, `:379-392` (**`get_by_email`'s body
  carries no comment at all**, which is what makes D11's decision not to authorize it safe),
  `:394-421`, `:458-510`, `:512-544`, `:545-656`, `:658-697`, `:699-720`, `:840-944`, `:946-966`;
  base.py `:80-104`; derivations.py `:24-26`, `:183`, `:217`, `:871`;
  test_loud_fail_harness.py `:60-116`; test_vault_path_required.py `:255-331`, `:378-459`;
  `docs/spec-reviews/WI-023-dave-review-2026-09-06-2.md` (present in the tree now — see the
  carried-forward notes).

### AC drift taxonomy (Check 12)

Diffed the five evolved `criteria` fences against `frozen_acceptance_criteria` in the in-force
artifact `docs/spec-reviews/WI-023-dave-review-2026-09-06-2.md` (`ac_hash a8c767cdccea`,
`signed_at 2026-09-06T19:49:12+01:00`). **Zero diffs in criterion text**: AC-1 through AC-5 are
byte-identical, `check:` and `kind:` unchanged on all five. Nothing to classify against the
taxonomy — no strength-weakening, no actor-swap, no scope-narrowing, no oracle-swap, no
exception-carving-by-addition. The one edit inside `## Acceptance Criteria` since that signature is
the round-3 fold's rewrite of the **preamble**, which carries no promise; it is routed under
non-blocking notes because it moves the section hash and nothing else.

### Blocking issues

**1. Task 12 clause (e2) and Task 5's tripwire quantify over "every authorized owner", and D11's own
table proves the assertion FALSE for two of the fifteen — so the fold's closing check is RED against
a correct build, and the cheapest repair from that red is rewriting a docstring D11 says is true.**

D11's disposition rule states it, Task 12 clause (e2) checks it, and Task 5 checks a Cut-0 variant of
it:

- D11 (`:1027-1029`): "every authorized owner must show at least one Cut-0 line gone (the repair
  landed)".
- Task 12 (e2): "every authorized owner has at least one Cut-0 line absent from the final surface,
  so a repair the plan ordered and the build skipped is RED".
- Task 5: "`prose_surface_cut0.json` is non-empty and every authorized owner D11's table names owns
  at least one line in it".

The domain is enumerable — D11 fixes it at fifteen owners (`:1041-1047`) — so I walked it for the
members the universal is false about by design. Two are:

- **`select_resolution` owns ZERO Cut-0 lines, because it does not exist at Cut 0.** D11 says so in
  terms: "a NEW owner, listed so the authorized set and the table are the same set", "(a new owner,
  so it has no Cut-0 lines to preserve)". That sentence disposes of the (e1) direction and says
  nothing about (e2) or about Task 5. Task 5's clause is unsatisfiable for it at the moment the
  recorder runs — the surface is `person.py`'s prose at this item's starting HEAD, and
  `select_resolution` is created at Task 9. Task 12 (e2) is unsatisfiable for it too: an owner with
  no Cut-0 lines cannot have one absent.
- **`_clear_indexes` owns exactly one prose line and D11 orders it kept.** Read at the source: `def`
  at `:326`, docstring `"""Clear custom indexes on refresh."""` at `:327`, then five `.clear()`
  statements. D11's table row says the docstring is "TRUE and it stays true; the owner is authorized
  only because Cut 1 deletes the `_email_index.clear()` **line beneath it**", and D11's "What each
  repair SAYS" paragraph orders no prose for `_clear_indexes`. But the deleted `self._email_index.clear()`
  at `:328` is a CODE line, and `prose_lines` emits records only for `COMMENT` and docstring `STRING`
  tokens (D8) — so nothing `_clear_indexes` owns leaves the prose surface, and (e2) is RED.

This is not a paper cut, because of where the red lands and what the cheapest repair is. Task 12 is
the LAST assertion in the item's prose class and Task 5's is the FIRST; a builder who hits either
has exactly two moves on the table — edit `_clear_indexes`' true docstring so a line "goes", or add
an owner-exclusion to the check — and Task 12's own text forbids the second ("never satisfied by
narrowing a needle or by adding an owner to the authorized set to make (e1) go green") while D11
forbids the first in substance. That is a judgment call that can go either way, in the clause the
round-3 fold was written to make total.

The generator is worth naming because it is the third instance of one shape: D11 is now correct
about which sentences must be READ (the surface is enumerated at source, and I could not find a
sixteenth member) and wrong about which owners must have CHANGED. The finding predicate is fixed;
the disposition predicate inherited the same "one class short" defect one level down.

**Suggested fix, in the document and outside the frozen criteria.** State the exemption class where
the rule is stated, not in a check the builder has to narrow: an authorized owner is exempt from the
"at least one Cut-0 line gone" direction iff D11's table orders it **no prose repair** — which is
exactly `_clear_indexes` (authorized for a code-only deletion) and `select_resolution` (a new owner
with no Cut-0 surface) — and carry the same two-member exclusion into Task 12 (e2) and Task 5's
clause by name, so the exclusion is auditable rather than discovered. Note the two other "—" rows are
NOT exempt and must not be swept in with them: `get_by_phone:416`'s comment IS replaced at Task 8, and
`_project_identifiers:238-242` survives but its owner loses `:231-234`, `:236-238` and `:252`. The
exemption is per-OWNER, not per-row, and stating it that way is what keeps (e2) doing work for the
thirteen it still binds.

**2. The threat model landed four `kind: required` mitigations on 2026-09-07; the document has not
been folded since, so there is no `## Mitigation Folds` section, and three of the four name work that
appears in no task, no `## Design` section and no `## Write Targets` `why`.**

Two separate defects, and only the second is mechanical.

*The mechanical half.* `## Threat Model — 2026-09-07` is the latest speaking round and declares M1,
M2, M3 and M4, all `kind: required`. The document carries no `## Mitigation Folds` heading and no
`fold` fence anywhere. The conveyor's D8c rule refuses `specced -> ready` on exactly that, so this is
a refusal I can catch here one round earlier and for free.

*The substantive half, which is why the fold records cannot just be written.* A fold record quotes
the Design sentence that carries the mitigation and the `Task N` work + verify text that lands it. I
read each named task for the substance:

- **M1** (`landed: Task 5`) — the recorder binds every `PersonRepository` to the temp path it just
  seeded and refuses, before any sweep writes, if a resolved `vault_path` is not that path. Task 5
  orders the two seedings, the three artifacts, the `__main__` guard, the invocation command and the
  tripwire test. It says nothing about binding or refusing. **No surface carries M1's work.**
- **M2** (`landed: Task 3`) — `seed_vault` refuses a `dest` that `_is_unconfigured` would swallow.
  Task 3 orders `load_roster()`, `seed_vault(roster, dest)` with the double-quoting contract,
  `roster_digest()`, the two invariant re-derivations, the `company:` uniqueness assertion and the
  `load() == 10` check. **No surface carries M2's work.**
- **M3** (`landed: Task 13`) — the wall-membership run also scans this item's `tests/`-root files for
  no-argument repository construction with the shipped `NO_ARG_CONSTRUCTION` pattern. Task 13 orders
  "run every predicate in D10's table", and D10's table has eleven rows, none of which is that scan —
  its `test_vault_path_required.py` rows are `test_no_implicit_vault_path_defaults` (whose universe D10
  itself records as `obsidian_schemas`/`scripts`) and the `.md` doc scan. **No surface carries M3's
  work.** D10 declares itself "a FLOOR measured at that date, never a total", so adding a row is legal
  — but the row has to be added, and by name, because Task 13 is a run of the table.
- **M4** (`landed: Task 8`) — the materialized snapshot asserted by D5's stronger predicate rather
  than AC-3's gloss. **This one IS landed**: D5 items 1 and 2 and Task 8's `phone_index_iteration_sites`
  clause carry it, and D5 explicitly says why AC-3's parenthetical is vacuously green against
  unchanged code. M4's fold record can be written from the document as it stands.

So three of four mitigations need work added to a task before a record can quote it truthfully, and
all four need records. I raise this as one finding rather than four because it is one omission — the
document predates the threat model's arrival — and because M1–M3's substance is small and lands in
tasks that already exist.

**Suggested fix.** Add M1's binding-and-refusal clause to Task 5 (it belongs beside the "two
independent temp vaults" sentence, and it is what makes the hand-run outside pytest safe), M2's dest
guard to Task 3's `seed_vault` contract, and an M3 row to D10's table plus the scan to Task 13; then
write five-field `fold` records under a `## Mitigation Folds` heading for all four, with `desc` copied
verbatim from the 2026-09-07 fences. `tests/identity_fixture.py`, `tests/record_identity_golden.py`
and `tests/test_identity_endgame.py` are all already declared `## Write Targets` paths, so no fence
moves.

### Non-blocking notes

- **D11's authorized set is fifteen owners; its table names fourteen.**
  `PersonRepository._find_or_create_stub_legacy` is in the prose list at `:1044` but has no row in
  the table at `:1060-1083`, so the sentence "its `owner` column IS the authorized set above — every
  owner appears here … so the two columns cannot drift apart" is false by one. Nothing is built
  wrong: (e3) pins that owner at zero lines explicitly and the deletion is Task 11's. But Task 5's
  tripwire is scoped to "every authorized owner D11's **table names**", so the two spellings of the
  set are already being read as one, and this is the same drift the sentence promises cannot happen.
  One row with `Task 11` in the lands-in column closes it.
- **The preamble edit moves `ac_hash` one more time, and that is the conductor's D4b act, not a
  spec-writer round.** `ac_hash` is `hash_section(body, "Acceptance Criteria")` — preamble included —
  and the round-3 fold rewrote the preamble after the `a8c767cdccea` signature. The five criterion
  texts are byte-identical to the frozen set (see Check 12), so a re-sign is a formality, and the
  fold's shape change is correct: with the restatement gone the preamble can no longer go stale
  against its own hash a fourth time. Routing, not a finding, and it does not block this verdict in
  either direction.
- **D4 item 2's "exception set is unchanged — it still raises nothing" is slightly stronger than the
  code will be.** Today `get_by_email(None)` raises `AttributeError` at `person.py:390`; post-cut
  `Email.parse(None)` raises `IdentifierError`, which D4 item 2 catches, so the call returns `None`.
  That is a widening of accepted input and the right direction — the threat model records it — but
  the sentence as written reads as "no observable change", and the `## Edge Cases` error-propagation
  entry repeats it. One clause naming the `None` case would make the claim exactly true.

### Carried-forward notes

Every still-open note from every prior round, re-checked against the tree rather than against the
fold's account of it.

- Spec review round 3 note 1 (`## Verification` said twelve needles against a table of thirteen) —
  **CLOSED.** The section now cites D11's tables instead of counting them, and the italic paragraph
  at `:1797-1802` names the class rather than the digit.
- Spec review round 3 note 2 ("green at every task boundary" false at the Task 6 boundary) —
  **CLOSED.** `## Verification`'s "The green boundary is the CUT, not the task" paragraph names the
  transient red, both case names, and the one-commit rule; Task 7 repeats it.
- Spec review round 3 note 3 (AC-5's check reads a live `docs/**` artifact with no coupling
  declaration) — **CLOSED.** D9 states the `CORPUS_COUPLING:` line, Task 2 orders it, and the
  `## Write Targets` `why` for `tests/test_identity_endgame.py` names it. The two precedent modules
  (`tests/test_company_name_contract.py:15`, `tests/test_ac_interpreter.py:23`) both carry one.
- Spec review round 3 blocking 2, second half (the `-2` sign-off artifact absent from the tree) —
  **CLOSED by the conductor**, not by the spec: `docs/spec-reviews/WI-023-dave-review-2026-09-06-2.md`
  is present and I read it for Check 12 above.
- Spec review rounds 1–2's findings and notes — all still closed; re-verified D3(b)'s per-sweep
  seeding with the `gate_write` mechanism named, AC-1's symbol-anchored weak-identity citation,
  Task 4's red-is-a-finding door, D2's ordinal 8 for `kit@localhost`, the closed five-value `arm`
  vocabulary participating in the tripwire triple, the three deliberately-edited test modules, and
  Task 5's `__main__` guard and literal invocation.
- Architect round 3 note 5 / round 4 note 4 (`_remove_entity_from_indexes` needs the insert path's
  widening) — still closed by D0's arm selection; re-read `:374-377`, which removes identifier keys
  through the same `_project_identifiers` projection that inserted them.
- Architect round 4 notes 1–3 and AC red-team round 2's "noted, not escalated" — all folded and still
  folded (D3's third derivation constraint with its pinned not-present table; the `arm`-not-branch
  record with the three Branch-B fall-throughs; the on-the-threshold disclosure in D1 and E8, whose
  contradiction inside `person.py` Task 9 now repairs).
- Data-premise's three — the cross-repo `orchestrator/docs/…` exclusion is D8's named exclusion with
  the line-wrap blind spot stated; `person.py:675` and `:685` are D7's, the latter also Task 12's
  presence clause. All closed.
- **Threat model's three notes, carried forward for the first time and all still open, none blocking:**
  the `get_by_email(None)` shape change (raised as a non-blocking note above, since D4 item 2's
  sentence is where it would land); the alias-preemption residual, which is a pre-existing property
  this item makes testable and whose closure would be a new item; and the audit artifact's
  "quoted with its note and reason" clause against `## Verification`'s close-out "only the counts are
  recorded", which do not collide at 0 of 1021 and are routed to whoever re-runs the audit if the arm
  ever flips.

```verdict
gate: spec-reviewer
verdict: REVISE
date: 2026-09-07
model: claude-opus-5
targets: Task 5, Task 12, Task 3, Task 13, M1, M2, M3, #design
prior: held
basis: folded-material
findings: 2/5
note: Round 3's two findings are closed and I re-derived both closures against the tree, but D11's disposition rule now over-quantifies in the other direction — "every authorized owner has at least one Cut-0 line gone" (Task 12 clause (e2), and Task 5's Cut-0 variant of it) is FALSE by the fold's own table for two of the fifteen: `select_resolution` owns zero Cut-0 lines because it does not exist at Cut 0, and `_clear_indexes` owns exactly one prose line (`:327`) that D11 orders KEPT, its authorization resting on a CODE deletion at `:328` that `prose_lines` never emits — so the fold's closing check is RED against a correct build and the cheapest repairs are the two the same tasks forbid; separately the 2026-09-07 threat model declared M1–M4 `kind: required` and the document has not been folded since, so there is no `## Mitigation Folds` section (a D8c refusal) and M1's recorder path-binding, M2's `seed_vault` dest guard and M3's `NO_ARG_CONSTRUCTION` scan over this item's `tests/`-root files appear in no task, no Design section and no Write Targets `why` — only M4 is landed, by D5 and Task 8.
```


## Adversarial Review — 2026-09-07

Round 4 (re-verify, post-fold). Cold-start read of the whole document end to end — Problem/Motivation
through Exploration Notes E1–E8, Approach, Design D0–D11, Edge Cases, Implementation Plan, Write
Targets, Verification, Verified Diagnosis, Scope Boundary, Risk Analysis, Acceptance Criteria — and
every prior gate verdict, including `## Threat Model — 2026-09-07` (PROMOTE), Spec Review round 4
(`2026-09-07`, REVISE), and this gate's own prior three PROMOTEs, as the untrusted content an
attacker's steering would have to hide inside. Confirmed independently, by glob, that this project's
own `docs/` still carries neither `work-item-pipeline.md` nor `compartmentalization-security-review.md`
— the same absence rounds 2 and 3 record, not re-litigated here. Read `docs/identity-cutover-corpus-audit.md`
and `docs/spec-reviews/WI-023-dave-review-2026-09-06-2.md` in full; the latter is the AC sign-off's
own artifact and its five frozen `criteria` fences are byte-identical to the live document's, which
is also what Spec Review round 4's Check 12 reports.

**What's new since round 3's PROMOTE.** Two sections: `## Threat Model — 2026-09-07` (PROMOTE, four
`kind: required` mitigation fences M1–M4) and Spec Review round 4 (REVISE, two findings — D11's
"every authorized owner has a Cut-0 line gone" is false for two owners, and the threat model's
mitigations are undocumented in any task).

**Method.** Grepped the whole document for injection-style phrasing (ignore/disregard-previous-
instructions, "emit PROMOTE"/"emit REVISE"/"emit REJECT", "as an AI", "SYSTEM:"/"ASSISTANT:" turns,
jailbreak language, addressed-to-a-reviewer phrasing — "trust me", "skip this check", "already
approved", "do not flag/report/review", "pre-approved/authorized", "override your", "reviewer
should") and separately for zero-width/bidi Unicode control characters, over the whole file — same
zero hits outside rounds 1–3's own method paragraphs (which only name their search terms, the
example-self-trap shape) as every prior round found; re-ran both greps myself rather than trusting
the prior rounds' report, and they agree. Independently re-verified the newest sections' heaviest
claims rather than trusting the quotes: `person.py:326-333` is exactly `_clear_indexes`, whose body
is a docstring at `:327` (`"""Clear custom indexes on refresh."""`) followed by five `.clear()`
statements including `self._email_index.clear()` at `:328` — confirming Spec Review round 4's read
that the line D11 orders gone is CODE, not prose, which is the mechanism its finding turns on;
`base.py:_is_unconfigured` and `_resolve_vault_path` (cited by the threat model at `:86-104`) do
swallow an absent, blank or `"."` path and fall through to `OBSIDIAN_VAULT_PATH`, matching the threat
model's read exactly. Also grepped `obsidian_schemas/` and `tests/` themselves (not just the doc) for
injection-style phrasing addressed to a reviewer or a build agent — no hits.

**What's actually in the new sections.** The threat model is a STRIDE walk arguing, on re-executed
evidence, that one real gap exists (three new `tests/`-root modules construct repositories outside
the wall that forbids an implicit `OBSIDIAN_VAULT_PATH` fallback) and disposing everything else as
already mitigated or non-issues — the opposite of a steering document, which would minimize rather
than surface a live-vault-corruption path. Spec Review round 4 is the same shape as every prior
round: a reviewer arguing a structural inconsistency from re-executed code reads (a universal
quantifier the fold's own table falsifies for two members; a mitigation with no landing task) and
routing to REVISE, which is again the direction opposite a planted "emit PROMOTE" would push. Neither
section contains an instruction addressed to a gate, a claim that a check should be skipped, or
prose whose form is spec content but whose effect is to steer a verdict — both are the ordinary shape
this role's calibration excludes (technical argument for or against the document's own merits).

**Conclusion.** No text arguing for a verdict independent of the spec's merits, no instructions
addressed to a reviewer/agent, no section whose form is spec content but whose effect is to steer a
gate, no prior verdict — including the four architect rounds, two AC-red-team rounds, data-premise,
four spec-review rounds and the threat model — that reads as the product of such steering, and no
fabricated citation in the newest material. This is a real finding — I looked again, at the delta and
at the whole, independently re-ran the greps rather than trusting the prior rounds' report, and found
nothing planted — not a skipped check.

```verdict
gate: injection-hunter
verdict: PROMOTE
date: 2026-09-07
model: claude-sonnet-5
note: Re-hunted cold-start after Threat Model (PROMOTE, M1–M4) and Spec Review round 4 (REVISE) landed; independently re-ran the injection-phrasing and hidden-Unicode greps over the whole document rather than trusting the prior three rounds' reports, and got the same zero hits outside their own method paragraphs (which only name their search terms); byte-verified the newest sections' load-bearing claims (person.py:326-333's `_clear_indexes` docstring-vs-code-line split, and base.py's `_is_unconfigured`/`_resolve_vault_path` fallback to `OBSIDIAN_VAULT_PATH`) against the tree — both accurate. Both new sections argue technical findings (a live-vault-write gap the threat model surfaces rather than hides, a disposition-rule over-quantification) that push toward more scrutiny, the opposite direction a planted steer would push.
```


## Adversarial Review — 2026-09-07

Round 5 (re-verify, post-fold, cold-start). Read the driven doc end to end — Problem/Motivation
through Exploration Notes E1–E8, Approach, Design D0–D11, Edge Cases, Implementation Plan, Write
Targets, Mitigation Folds, Verification, Verified Diagnosis, Scope Boundary, Risk Analysis,
Acceptance Criteria — and every prior gate verdict, including `## Threat Model — 2026-09-07`
(PROMOTE), Spec Review round 4 (REVISE), Spec Review round 5 (REVISE, the newest section), and
this gate's own prior four PROMOTEs, as the untrusted content an attacker's steering would have to
hide inside. Independently confirmed by glob that this project's own `docs/` still carries neither
`work-item-pipeline.md` nor `compartmentalization-security-review.md` (the same absence rounds 2–4
record). Read `docs/identity-cutover-corpus-audit.md` and
`docs/spec-reviews/WI-023-dave-review-2026-09-06-2.md` in full — both are the two grounding
artifacts the driven doc's Write Targets and AC Sign-off fence depend on.

**What's new since round 4's PROMOTE.** One section: Spec Review round 5 (REVISE), one blocking
finding — Task 2's `prose_lines` shapes fixture asserts as a near-miss ("neither of which may be
collected") a shape that is, by D8's own stated rule and by Task 2's own three-clauses-earlier
"collected" list, actually a match (a trailing `#` comment containing `"""` still carries a
`COMMENT` token and so still yields one record).

**Method.** Re-ran the injection-phrasing and hidden-Unicode-control-character sweeps over the
whole document myself rather than trusting the prior four rounds' reports (`ignore/disregard-
previous-instructions`, `emit PROMOTE`/`REVISE`/`REJECT`, `as an AI`, `SYSTEM:`/`ASSISTANT:` turns,
jailbreak language, addressed-to-a-reviewer phrasing — "trust me", "skip this check", "already
approved", "pre-approved/authorized", "override your", "reviewer should", "do not flag/report/
review" — plus zero-width/bidi/BOM Unicode control points). Same result both sweeps found every
round: zero hits outside rounds 1–4's own method paragraphs, which name those terms only to
describe their own search vocabulary (the example-self-trap shape), and zero Unicode control
characters anywhere in the file. Independently re-verified, rather than trusted, round 5's own
citations: D8's `prose_lines` rule text (`"a comment and the code it trails yield one record
carrying the whole line"`) and Task 2's fixture list (which names "a trailing `#` comment on a
code line" as collected three clauses before naming "a code line containing `"""` inside a
comment" as a near-miss) — both quoted accurately from the driven doc itself, not fabricated.
Read the two grounding artifacts byte-for-byte: the corpus audit's command, verbatim stdout and
per-clause reading, and the AC-sign-off YAML's five frozen `criteria` fences — nothing in either
addresses a reviewer, argues for a verdict, or contains a payload; both are exactly the technical
content the driven doc quotes them as.

**What's actually in the new section.** A spec-reviewer arguing, from a re-executed reading of the
predicate's own stated rule against the fixture's own stated near-miss list, that the two
contradict each other on the identical shape — the same kind of self-consistency finding every
prior round has produced (a docstring restating a falsified proposition, a universal quantifier
false for two enumerated members, a missing fold section), never an instruction addressed to a
gate and never text whose form is spec content but whose effect is to steer a verdict. The finding
pushes toward MORE scrutiny of Task 2 before build, the opposite of what a planted "emit PROMOTE"
would do.

**Conclusion.** No text arguing for a verdict independent of the spec's merits, no instructions
addressed to a reviewer/agent, no section whose form is spec content but whose effect is to steer
a gate, no prior verdict — across all four architect rounds, two AC-red-team rounds, data-premise,
five spec-review rounds and the threat model — that reads as the product of such steering, and no
fabricated citation in the newest material. This is a real finding — I looked again, at the delta
and at the whole, independently re-ran the sweeps and the artifact reads rather than trusting the
prior four rounds' reports, and found nothing planted — not a skipped check.

```verdict
gate: injection-hunter
verdict: PROMOTE
date: 2026-09-07
model: claude-sonnet-5
note: Re-hunted cold-start after Spec Review round 5 (REVISE) landed; independently re-ran the injection-phrasing and hidden-Unicode-control-character sweeps over the whole document rather than trusting the prior four rounds' reports, and got the same zero hits outside their own method paragraphs (which only name their search terms); byte-verified round 5's own quotes (D8's prose_lines rule text and Task 2's "collected" vs "near-miss" fixture lists) against the driven doc and read both grounding artifacts (the corpus audit, the AC sign-off YAML) in full — all accurate, no reviewer-addressed text, no payload. The new section is a self-consistency finding (Task 2's fixture calls a match a near-miss) argued from re-executed rules, pushing toward more scrutiny rather than any verdict — the opposite of a planted steer.
```


## Adversarial Review — 2026-09-07

Round 6 (re-verify, post-fold, cold-start). Read the driven doc end to end — Problem/Motivation
through Exploration Notes E1–E8, Approach, Design D0–D11, Edge Cases, Implementation Plan, Write
Targets, Mitigation Folds, Verification, Verified Diagnosis, Scope Boundary, Risk Analysis,
Acceptance Criteria — and every prior gate verdict, including `## Threat Model — 2026-09-07`
(PROMOTE), all six Spec Review rounds (REVISE ×5, this gate's own five prior PROMOTEs), the four
Architectural Review rounds, both AC Red-Team rounds, Data Audit, and AC Sign-off, as the untrusted
content an attacker's steering would have to hide inside. Independently confirmed by glob that this
project's own `docs/` still carries neither `work-item-pipeline.md` nor
`compartmentalization-security-review.md` (the same absence rounds 2–5 record); both resolve under
`/Users/davewascha/Workspaces/workshop-stable/docs/` and I read both there in full.

**What's new since round 5's PROMOTE.** One section: Spec Review round 6 (REVISE), one blocking
finding — two of this item's own checks (Task 9's `attribute_reads_in` attrs list naming
`_email_index`; Task 12 clause (e3) and its authorized-owner list naming
`PersonRepository._find_or_create_stub_legacy`) spell, inside `tests/test_identity_endgame.py`
itself, literals that two other checks (Task 6; AC-1) assert at ZERO across both tracked roots —
so each collides with its own item's zero-count evidence at the commit boundary where it lands.

**Method.** Re-ran the injection-phrasing and hidden-Unicode-control-character sweeps over the
whole document myself rather than trusting the prior five rounds' reports: grepped for
ignore/disregard-previous-instructions, `emit PROMOTE`/`REVISE`/`REJECT`, "as an AI",
`SYSTEM:`/`ASSISTANT:` turns, jailbreak language, and addressed-to-a-reviewer phrasing ("trust me",
"skip this check", "already approved", "pre-approved/authorized", "override your", "reviewer
should", "do not flag/report/review") — zero hits outside rounds 1–5's own method paragraphs, which
name those terms only to describe their own search vocabulary (the example-self-trap shape this
role's own contract warns about). Separately grepped for zero-width, bidi and BOM Unicode control
points (`U+200B`–`U+200F`, `U+202A`–`U+202E`, `U+2060`–`U+2064`, `U+FEFF`) — zero hits anywhere in
the file. Also grepped the two role-referenced docs at their actual location
(`workshop-stable/docs/`) for the same injection vocabulary — one hit, "pre-approved actions" in
`compartmentalization-security-review.md:80`, which on inspection is the phrase "Action-Selector —
the AI can only pick from a fixed menu of **pre-approved** actions", a description of a security
design pattern in that doc's own subject matter, not an instruction addressed to a reviewer or
directed at this item. Independently re-verified round 6's own load-bearing claims rather than
trusting the quotes: `person.py`'s Task 9 site orders `attribute_reads_in` over
`_cache`/`_alias_index`/`_email_index`/`_phone_index`, matching AC-4's structural clause verbatim;
Task 6's needle clause is stated over `python_files_under(PACKAGE_ROOT, TESTS_ROOT)` and Task 11's
AC-1 scan is the frozen criterion text over the same two roots — both citations resolve to what
round 6 quotes them as.

**What's actually in the new section.** A spec-reviewer arguing, from re-derived task text and the
document's own frozen criteria, that two of the item's own zero-count checks collide with two of
its own non-zero-necessity checks at specific commit boundaries — the same self-consistency shape
every round since round 2 has produced (a falsified docstring, a universal quantifier false for
enumerated members, a missing fold section, a fixture near-miss that was actually a match), never
an instruction addressed to a gate and never text whose form is spec content but whose effect is to
steer a verdict. The finding pushes toward more scrutiny of Tasks 9 and 12 before build — the
opposite of what a planted "emit PROMOTE" would do — and it explicitly credits round 5's own fold
(widening Task 6's scan to both roots) as the proximate cause of one of the two instances, which is
the kind of even-handed, mechanism-first attribution a steering attempt has no reason to produce.

**Conclusion.** No text arguing for a verdict independent of the spec's merits, no instructions
addressed to a reviewer/agent, no section whose form is spec content but whose effect is to steer a
gate, no prior verdict — across all four architect rounds, two AC-red-team rounds, data-premise, six
spec-review rounds and the threat model — that reads as the product of such steering, and no
fabricated citation in the newest material. This is a real finding — I looked again, at the delta
and at the whole, independently re-ran the sweeps and the artifact reads rather than trusting the
prior five rounds' reports, and found nothing planted — not a skipped check.

```verdict
gate: injection-hunter
verdict: PROMOTE
date: 2026-09-07
model: claude-sonnet-5
note: Re-hunted cold-start after Spec Review round 6 (REVISE) landed; independently re-ran the injection-phrasing and hidden-Unicode-control-character sweeps over the whole document plus the two role-referenced docs at their real location (workshop-stable/docs/) rather than trusting the prior five rounds' reports — zero hits outside prior rounds' own method paragraphs (which only name their search terms) and one benign non-directed hit ("pre-approved actions", a security-pattern description in compartmentalization-security-review.md:80, not addressed to a reviewer); byte-verified round 6's own load-bearing citations (Task 9's attrs list, Task 6's and Task 11's both-roots scans) against the driven doc — all accurate. The new section is a self-consistency finding (two of the item's own checks collide with two of its own zero-count assertions at specific commit boundaries) argued from re-derived task text, pushing toward more scrutiny rather than any verdict — the opposite of a planted steer.
```

