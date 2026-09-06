---
id: WI-023
title: "Identity engine endgame: delete the legacy cascade, cut over the unified index"
project: obsidian-schemas
stage: specced
created: 2026-07-05
last_touched: 2026-09-06
stage_changed: 2026-09-06
touched_by: spec-writer
tags: [identity, wi-125-followup, strangler-completion]
depends_on: []
transitions: ["idea>exploring@2026-09-06@session", "exploring>specced@2026-09-06@session"]
review_level: L3
review_level_provenance: selector
---

# Identity engine endgame

> **Model routing** (2026-07-05 campaign, `docs/backlog-campaign-2026-07-05.md`; self-sufficient):
> - **Explore: —** (the design was pre-recorded in the WI-125 strangler plan, person.py:181-184, and the 2026-07-05 architecture review maps the seams; the parity replay already PASSED — 942 inputs, 0 diffs, `orchestrator/state/identity-parity.json`).
> - **Spec: Opus / high. Spec-review: Opus / high. Build: Opus / medium** — deletion cut over identity machinery: mostly removal with a strong parity net, but the index cutover changes which code resolves email/phone, so the spec must state the parity evidence per cut.
> - Sequencing: Phase 3, after the Phase 1 floor. **WI-025 (person.py decomposition) is gated on this** — delete the duplicate before moving what remains.
>
> *Explore ran after all, 2026-09-06 (approval-only, cold-start).* The routing table's `—` rested on "the design was pre-recorded in the WI-125 strangler plan and the parity replay already PASSED". Two months and three shipped items later both halves of that had moved: one of the five scope items is already **done** (WI-021 landed it), the in-tree artefact that reads as the parity guard is **vacuous**, and one scope item is **impossible as written**. See `## Exploration Notes`.

## Problem / Motivation

WI-125 landed as a strangler: engine live, old paths retained, index dormant. The 2026-07-05 architecture review confirmed the retained half is an **active maintenance tax** — WI-121 had to be threaded through the legacy body and the engine "symmetrically" by hand, with nothing forcing the two copies to agree.

Exploration sharpened this. The tax is real, but it is not the dangerous part. **The dangerous part is that the duplicate the item wants to delete is the only oracle the item's other cuts have.** `_find_or_create_stub_legacy` is not merely dead weight: it is the pre-WI-125 answer, preserved verbatim, and it is what any behaviour-changing cut in this item would have to be diffed against. Deleting it first — the order the scope below implies — spends the oracle before the cuts that need it. And the two artefacts that were supposed to stand in for it do not: the offline replay lives in another repo and predates WI-020/WI-021, and the in-tree "parity harness" now compares the engine to itself.

Original scope, each item **re-verified against the tree as this drive seeded it (HEAD `2bf731f` + the seeded uncommitted delta), 2026-09-06**:

1. **Delete `_find_or_create_stub_legacy`** — still live at **person.py:699-824** (126 lines). Still "NOT called in production": `tests/derivations.py:functions_calling` sees one caller in the whole tree, `tests/test_wi126_body_preservation.py:212`, and that is a body-preservation witness, not a parity test. **Premise holds; the ORDER does not** — see Exploration Notes E1.
2. **Cut email/phone resolution over to the unified `_identifier_index`** — still true: `_resolve_identifier` (**person.py:946-966**) delegates `Email` to `get_by_email` and `Phone` to `get_by_phone`, so the index's only live effect remains conflict observability. The **phone question is now answered, and the answer is "not by key-normalizing"**: `phones_match` is not transitive, so it has no quotient and therefore no key function (E3, with a witness). The **email half is live and decidable**, but on a corpus number nobody has run (`## Write Targets`). "Collapse the per-kind dicts into views" (the plan at **person.py:160-167**) can reach at most 2 of the 4 dicts in any world — there is no `Alias` identifier type at all, and `slack` is deliberately unprojected (**person.py:238-242**).
3. **Consolidate the resolution cascades** (review finding N5) — still true: `resolve()` (**person.py:458-510**) and `resolve_all()` (**person.py:512-656**) carry separately-maintained match logic. But "make `resolve` a thin head of `resolve_all`" is **a behaviour change, not a refactor** — **three** divergence classes are hand-executed in E4, and two of them widen what `resolve()` returns, which is the direction that mints wrong-person resolutions in HAL9000's contact cascade.
4. ~~**Break the lazy-import cycle**~~ — **DONE, delete from scope.** WI-021 shipped `obsidian_schemas/phone_normalization.py`; `identifier.py:38-45` now imports `normalize_phone` at **module scope** and the two deferred imports inside `Phone.parse`/`WhatsAppJID.parse` are gone. `repositories/person.py:78-85` keeps a compat re-export for two live consumers. WI-021's build note says it "lands WI-023's own scope item 4 early" (phone_normalization.py:25-27) — verified, it did.
5. **Riders** — both still live, at drifted lines: the dangling `docs/paren-decoration-at-the-door.md` reference is at **person.py:113** (one site in the tree; the file does not exist under `docs/`), and the slack-index carve-out note is at **person.py:238-242**.

## Intent

One find-or-create implementation, one resolution cascade, an identifier index that is actually the resolution authority (or documentedly not, per kind), no import cycle — with the parity replay re-run green after each cut.

*(Frozen anchor, untouched. Read in approval-only mode: the mint's named mechanisms are hypotheses; the outcome clauses are the requirement. Note the Intent already licenses the per-kind carve-out — "**or documentedly not, per kind**" — which is the arm E3 forces for phones.)*

## Exploration Notes

Cold-start, approval-only. Re-derived from the frozen `## Intent` rather than from the mint's mechanism list. Every claim below is stated as a predicate over the tree as this drive seeded it (HEAD `2bf731f` plus the seeded uncommitted delta) so it can be re-run; the two premises that are about the **live vault** and therefore cannot be, are routed to `## Write Targets` instead of asserted.

*Revised 2026-09-06 after the architectural review below (round 1).* Both blocking findings were about the document disagreeing with itself rather than about a claim being wrong, and both are answered in place: the golden's two baseline moments are collapsed to one and the resulting Cut-1 divergences are enumerated as a closed list in the new **E7** (with the fixture's plants fixed as literals, since which literal landed decided whether AC-2 and AC-4 were jointly satisfiable); the false "re-homing the golden onto WI-016's fixture is cheap" is retracted in **E6** and an arm chosen, with its solve-in-one-place cost named. The two non-blocking notes are also taken: AC-1's `functions_calling` mechanism is replaced (it sees callers, never the `def`, so the zero-sites clause would have gone green with the duplicate still shipped) and Cut 4 now names the WI-126 legacy twin it deletes.

*Revised again after round 2, which found the same defect class at two sites the fold had no reason to re-read.* Both findings verified independently against the tree before repair, and both are answered in place. **(1) The second criterion collision** — AC-2's four-door agreement against AC-4's alias-before-email discriminant — is settled in the new **E8**: the agreement property is scoped to non-alias inputs and the alias preemption is pinned as a declared, permanent asymmetry rather than carved out, because an unpinned asymmetry is what Cut 3 deletes by accident. E8 also fixes the **eight-note fixture roster** as literals (round 1's lesson: an unfixed plant decides buildability) on one single vault, with a no-shared-name-token invariant that removes a walk-order dependency the golden would otherwise have carried. **(2) The third divergence class** — `resolve_all` step 6, which `resolve` has no analogue for, whose own comment at person.py:615-617 falsely calls it sub-floor, and which the derived golden provably cannot reach — is hand-executed as class **(C)** in **E4** and hand-stated as AC-4 discriminant **(iv)**; the comment repair rides in AC-5. E4 also now states the three constraints the classes jointly force on the selection policy (it reads the query, it accepts 0.6 while rejecting 0.65, it re-orders 1.0 ties by `matched_via`), which subsumes the round-2 non-blocking note; the other non-blocking note, E6's fixture undercount, is corrected against E8's roster.

*Revised a third time after the AC red-team, which attacked the criteria TEXT rather than the architecture and found the two places where a fixture literal was still the builder's coin flip.* Both are answered by fixing the literal, which is this document's own standing rule (E7: an unfixed plant decides buildability) applied to the two plants the earlier folds left unfixed. **(1) AC-3's phone plant is pinned to the OUTER vertex `44790055852`.** E3's triangle has a centre — `0790055852` is matched by BOTH `44790055852` and `10790055852` — so a fixture note carrying the centre is found by all three forms, AC-3's own "and NOT for the one that does not" clause names nothing, and **no implementation, correct or otherwise, can satisfy it**. The centre is the obvious first reach (it is the form E3's witness table lists first), so leaving the choice open shipped a coin flip with an unbuildable face. **(2) E8's roster grows from eight notes to ten**, so AC-1's "by construction" branch coverage is true of the fixture this document actually pins: the eight notes carry no `phones:` and no `company:` field, so "every note contributes … its phone" was false of every one of them, and Branch A (phone hit) and Branch B (name+company reuse) were CLAIMED rather than constructed — a golden sweep silently missing two of its four branches while AC-1 reads as though it covered them. E8 also gains the phone analogue of its no-shared-name-token invariant, forced by the identical mechanism: `get_by_phone`'s fuzzy arm returns the FIRST `_phone_index` entry that `phones_match` accepts, in insertion order (person.py:417-419), so two unifiable fixture phones would make AC-3's negative witness and AC-1's phone sweep both walk-order-dependent. **Nothing in E7's closed exception list moves**: the two added notes carry no `emails:` and no `aliases:`, and Cut 1 is an email cut.

### E1 — The thing being deleted is the oracle for everything else being changed

`_find_or_create_stub_legacy` (person.py:699-824) exists for two declared reasons (person.py:709-712): the Phase-5 parity baseline, and the one-commit rollback. The item treats both as spent. The rollback genuinely is. **The baseline is not**, and the evidence that it was has decayed in three separate ways:

1. **The in-tree parity harness is vacuous.** `tests/test_resolve_or_create.py:189-211` reads as the Phase-5 contract in miniature — twin vaults, five `PARITY_CASES`, "identical `(name, created)`". Its "legacy" leg (`:198`) calls `find_or_create_stub`, which since the Phase-4 adapter swap is `parse_identifiers(...)` + `self.resolve_or_create(...)` (person.py:688-697). Its "engine" leg (`:204`) calls `parse_identifiers(...)` + `resolve_or_create(...)` with the same arguments. **Both legs are the same computation.** The test cannot fail for any change to either path. `test_engine_matches_legacy_on_weak_identity` (`:214-224`) has the identical defect. Six cases that read as the item's safety net guard nothing. Nobody did anything wrong — the harness was written when `find_or_create_stub` *was* the legacy body, and the adapter swap turned it into a tautology in place, silently, which is exactly the failure mode the item exists to end.
2. **The out-of-tree replay is unreachable and stale.** `orchestrator/state/identity-parity.json` (942 inputs, 0 diffs) is in another repo, was produced against the live vault, and predates WI-020 (loud-fail boundaries) and WI-021 (the `name_gate` semantic write gate, which now sits on `create_stub` and `save` — i.e. inside Branch C of both paths). A 2026-06 PASS is not evidence about 2026-09 code.
3. **Consequently the campaign's library invariant for this item — "WI-023's cuts each re-run the parity replay green" (`docs/backlog-campaign-2026-07-05.md:37,62`) — is not satisfiable as written.** There is no runnable replay harness anywhere in this tree (`scripts/` holds `lint_vault.py` and `migrate_person_to_discuss.py` only). This is a routing note for the conductor, not a finding against the campaign: the invariant's *intent* — no cut lands unless something red-flags a behaviour change — is preserved below by an in-tree oracle that the hermetic floor can actually execute.

**Decision (the item's spine).** Invert the mint's order. The oracle is repaired first, used for the behaviour-changing cuts, and deleted last, inside this same item. Concretely: repair the harness → record a golden → cut → delete. This costs one extra commit and buys the only thing that makes the deletion safe rather than merely tidy.

**Rejected: "delete first, it's dead code."** True and irrelevant. The risk in this item is not in cut 1, it is in cuts 2 and 3; deleting the oracle first is spending the safety net before entering the part that needs it. **Rejected: "re-run the orchestrator replay first."** Cross-repo, live-vault, non-hermetic, and it would have to be re-run after every cut by hand — that is the shape this repo's floor command exists to avoid.

### E2 — Where the email cutover actually diverges (three classes, hand-executed)

`_email_index` is keyed `email.lower()` at index time (person.py:197) and queried `email.lower().strip()` (person.py:390). `_identifier_index` is keyed `Email.key` = `email:{local}@{domain}` after `Email.parse` (identifier.py:143-177). Routing email resolution through the index therefore changes behaviour in exactly three classes:

- **(a) Junk-keyed entries stop resolving.** `_email_index` indexes *any* non-empty string; `_project_identifiers` skips whatever `Email.parse` refuses (person.py:246-252). `tests/test_identity_index.py:184-201` already pins this divergence deliberately (`"not-an-email"` and `"bad email"` are in the legacy dict and absent from the typed index). Cutting over **loses** these lookups. Size on the live vault: unknown → `## Write Targets`.
- **(b) Angle-bracket forms start resolving, by their address.** A note whose `emails:` carries `Jane <jane@x.com>` (the WI-017 leak shape) is in `_email_index` under the whole string and in `_identifier_index` under `email:jane@x.com`. Cutover **gains** the sane lookup and loses the literal one. An improvement, but it is a behaviour change and belongs in the record.
- **(c) Whitespace-bearing entries start resolving trimmed.** Indexed un-stripped today (`:197`), stripped by `Email.parse`. Also an improvement.

Class (a) is the only one that can lose something real, and it is the decision. **Decision rule, stated in advance so the audit is decision-forcing rather than decorative:** if the audit finds **zero** live person-note email entries that `Email.parse` refuses, email cuts over to the index and `_email_index` is deleted. If it finds **any**, the email cutover is **blocked** on repairing those notes (a `lint_vault` rule — WI-026's territory, solve-in-one-place) and this item takes the documented-carve-out arm for email too, exactly as it does for phone. Either way the shipped property is the same one (E5, AC-2): *one* authority, not two.

**These three classes are exactly the classes that move `resolve()`'s answers at Cut 1** — `resolve` step 3 reads `_email_index` directly (person.py:492-496), so it is one of the four surfaces AC-2 re-homes. That collides with AC-4's golden unless the collision is enumerated rather than left to the fixture author. **E7 does the enumeration**: it fixes the fixture's three decorated/refused plants as literals, hand-executes each one's pre-cut and post-cut answer under both arms, and closes the resulting exception list. Read E7 before reading AC-2 or AC-4 — neither is decidable without it.

### E3 — The phone question is answered: `phones_match` has no key function, because it is not transitive

This was the mint's one genuinely open design call ("either key-normalize into the index or keep phones on the fuzzy path *explicitly and documentedly*"), and both WI-021's build (`phone_normalization.py:29-33`) and its test wall (`tests/test_name_gate.py:479-492`) deliberately declined to answer it and left it labelled "WI-023 item 2's question". It is answerable from the source alone, no corpus needed.

A key function `k` such that `phones_match(x, y) ⟺ k(x) == k(y)` can exist only if `phones_match` is an equivalence relation. It is reflexive and symmetric (both country-code arms at `phone_normalization.py:76-88` are written in both directions). **It is not transitive.** Witness, hand-executed against `phone_normalization.py:58-90`:

| pair | arm | result |
|---|---|---|
| `phones_match("0790055852", "44790055852")` | UK, `norm2[2:] == norm1[1:]` → `"790055852" == "790055852"` | **True** |
| `phones_match("0790055852", "10790055852")` | US, `len(norm2)==11`, `norm2[1:] == norm1` → `"0790055852" == "0790055852"` | **True** |
| `phones_match("44790055852", "10790055852")` | UK arm needs a `"0"` prefix (has `"1"`); US arm gives `norm2[1:] == "0790055852" ≠ "44790055852"` | **False** |

All three parse as `Phone` (10 and 11 digits, `MIN_DIGITS = 7`, identifier.py:237) and produce three **distinct** keys. So no `Phone.key` — and no re-normalization of it — can express this relation. "Key-normalize into the index" is not a hard option, it is an unavailable one. **Phones take the carve-out arm, which the Intent explicitly licenses.**

**Where the structure actually lives.** The fuzzy arm is a read-time reconstruction of information the write boundary destroyed: `normalize_phone` strips everything non-digit, `+` included (phone_normalization.py:52-55), so a vault phone records no region and no E.164 form, and `phones_match` is left guessing at read time whether a leading `0` is a UK trunk prefix. That is the WI-185 shape — and the honest fix is at the seam, not downstream: canonicalize phones to E.164 **at the write door** (the WI-021 `name_gate`, which already owns `phones[]` dedupe at name_gate.py:198-237) and the whole fuzzy arm becomes deletable and phones become keyable. **That is a separate item**, not this one: it needs a region policy, a vault-wide migration of existing `phones:` values, and consumer coordination — three repos read these fields. Recorded here as a follow-on to mint, with this section as its motivation, so it is not re-derived from scratch.

**Rider that rides with the carve-out.** WI-004 left one finding explicitly OPEN by name: `get_by_phone` iterates a live mapping (`docs/concurrent-access.md:8713-8714`, re-verified — person.py:417 iterates `self._phone_index.items()` while `_clear_indexes` mutates that same dict in place at person.py:326-333). WI-004 closed the wrong-VALUE half and left the iterate-a-live-mapping half open *because* phones were expected to leave the fuzzy path here. They are not. So this item owes the one-line snapshot (`list(...)`) that closes it, or the finding stays open forever with no owner.

### E4 — "Make `resolve` a thin head of `resolve_all`" is a behaviour change, and it widens

The N5 finding is right that two cascades drift. But a literal thin head (`resolve_all(q)[0].person if candidates else None`) is not behaviour-preserving. **Three** divergence classes, hand-executed against person.py:458-510 and :512-656:

- **(A) Multi-token miss becomes a 0.65 hit.** `resolve("john smith kato")` against a vault holding `John Smith`: step 5 tests `query_lower in name.split()`, and a multi-token query string is never an element of a token list, so today it returns **None**. `resolve_all` scores it 0.65 `token-subset` (cache tokens ⊆ query tokens, 2 shared, person.py:607-609), clears the 0.5 floor, and a thin head returns **John Smith**. This is `resolve()` newly claiming matches it used to decline — the direction that produces wrong-person resolutions downstream.
- **(B) Alias-vs-email precedence inverts.** `resolve` orders alias (step 2, person.py:488) before email (step 3, :493); `resolve_all` orders email (:573) before alias (:581) and comments that the ordering is deliberate (:571-572). For a query that is person X's alias *and* person Y's email address, `resolve` returns **X** today; both score 1.0 in `resolve_all`, insertion order puts Y first, and Python's stable sort at :655 keeps it there — a thin head returns **Y**. This class is also the site of AC-2's own collision, and it is settled separately in **E8**.
- **(C) The short-form arm has no `resolve` analogue at all, and its own comment says otherwise.** `resolve_all` step 6 (person.py:614-626) matches "first token exact + second token ≤2 chars, prefix of the cache key's second token" — the `Emily M` shape. `resolve` has no such branch. Hand-executed on `resolve("emily m")` against a vault holding `Emily Mendes`, **no company hint**: `resolve` misses step 1 (not a cache key), step 2 (not an alias), step 3 (no `@`), step 4 (`normalize_phone` yields 0 digits) and step 5 (`"emily m"` is not an element of `["emily", "mendes"]`, person.py:507) → **None**. `resolve_all` misses step 5 too (`{"emily","m"}` is a subset of neither direction of `{"emily","mendes"}`, so neither :607-609 nor :610-612 fires) and then step 6 records **Emily Mendes at 0.6 `partial-name`** (:624-626), which clears the `>= 0.5` floor at :654 and is returned. A thin head returns Emily Mendes. Widening again — and on exactly the query shape the `resolve_all` docstring names as the live orchestrator case (person.py:537).

  **The code's comment at person.py:615-617 asserts the opposite** — "without it, this match stays low confidence (< 0.5) and gets filtered out below". It records 0.6 and the floor is 0.5, so it is **not** filtered; the company hint only bumps an already-surviving candidate. Anyone auditing `resolve_all` for divergences by reading the comments concludes step 6 is inert. It is not, and this is why the class went unnamed until round 2 of review. The comment is documentation that has stopped being true — the class AC-5 already owns — so its repair rides there.

**What the three classes jointly force on the selection policy.** They are not independent, and reading them together is what tells the builder the shape of the thing before the build discovers it by going red:

1. **The policy must read the QUERY, not just the candidate list.** Step 5's single-token branch (:610-612) and step 6 (:624-626) record the **same confidence (0.6) under the same `matched_via` label (`"partial-name"`)** — yet `resolve("sandy")` must return `Sandy Forster` (step 5's 0.6, today's answer) while `resolve("emily m")` must return **None** (step 6's 0.6). No pure function of `List[ResolveCandidate]` can separate them; the discriminant is the query's token count. AC-4's structural clause permits this — it forbids `resolve()` reading `_cache`/`_alias_index`/`_email_index`/`_phone_index`, not reading its own argument.
2. **The policy must accept 0.6 and reject 0.65** — a confidence threshold gets this exactly backwards. Class (A) requires rejecting step 5's `token-subset` at 0.65; `resolve("sandy")` requires accepting step 5's `partial-name` at 0.6. Sorting by confidence and taking the head is wrong in both directions.
3. **The policy must restore `resolve`'s cascade priority on 1.0 ties.** Class (B) is a tie the sort cannot break: `resolve_all` emits email before alias, `resolve` wants alias before email. Ranking equal-confidence candidates by `matched_via` in `resolve`'s own order — exact-name > alias > email > phone — reproduces it, and stays inside the structural clause because `matched_via` is on the candidate.

**Decision.** Consolidate, but on a recorded oracle rather than on the claim that the two cascades "should" agree. `resolve()` keeps no match logic of its own — it becomes `resolve_all()` plus a **named selection policy** whose inputs are the candidate list *and the query string* — and the policy is required to reproduce today's answers over a query space *derived from the fixture vault's own notes*, pinned by a golden recorded at **Cut 0, against unchanged code, before Cuts 1, 2 and 3, and never re-recorded** (E7 — "before the cut" was ambiguous between "before Cut 1" and "before Cut 3", and they are different instants because Cut 1 moves `resolve()` too). Where the policy cannot reproduce a legacy answer, that case is either fixed in the policy or promoted to an explicit, named, Dave-visible change — never absorbed. **All three classes above are hand-stated as discriminants in AC-4**, precisely so a golden regenerated after the cut (the one way this oracle can be defeated) contradicts the document — and class (C) *has* to be hand-stated, because **the derived golden cannot reach it**: the derived space is names, name tokens, aliases, emails and phones, a full name hits exact-name and a bare token is one token, so no two-token-with-short-second query enters the space at all (an alias of that shape would short-circuit at 1.0 anyway). An oracle that cannot see a divergence is not evidence about it. **Cut 3 itself is allowed no exceptions at all** — the only queries whose golden value legitimately moves are the Cut 1 exceptions E7 enumerates.

**Rejected: preserve the legacy `resolve` body as `_resolve_legacy` for the duration.** It works, and it is what E1 does for the stub path — but it adds a *second* temporary duplicate to an item whose whole point is removing the first, and a recorded golden gives the same differential signal as committed data rather than as code. **Rejected: leave `resolve()` alone and call item 3 done by documentation.** The drift is real (`resolve_all`'s own docstring carried a +0.2/+0.25 error through WI-117), and the Intent says *one* cascade.

**Noted, not adopted:** `resolve()` is a four-repository convention — `company.py:96`, `meeting.py:345`, `book.py:231` each carry their own. Only Person gets `resolve_all`. Consolidating Person's pair does not oblige the other three, and this item should not touch them.

### E5 — Constraints discovered

- **The index can never absorb all four dicts.** There is no `Alias` identifier type in `identifier.py` at all (the union is Email / EmailDomain / Phone / WhatsAppJID / SlackUserId / LinkedInSlug / CalendarEventId / GranolaDocId), and aliases are name variants rather than hard identifiers (`tests/test_identity_index.py:104`). `slack` is unprojectable until frontmatter carries a workspace (person.py:238-242) — that is the rider-5 carve-out note, and it should be **kept and given its unblock condition**, not retired. So "collapse the per-kind dicts into views" tops out at `_email_index` (+ `_phone_index`, only in the world E3 rules out). The Intent's real property is *one authority per kind*, not *one dict*.
- **`normalize_phone` / `phones_match` are load-bearing in two consumer repos by their `repositories.person` path** (person.py:78-85, measured by WI-021 on 2026-09-05). The compat re-export stays; this item must not "tidy" it away while decomposing.
- **`find_or_create_stub`'s signature, return shape and exception set are the consumer contract** (person.py:668-686) — orchestrator `contact_normalizer.py` calls it directly, HAL9000 `entities.py` over HTTP. Nothing in this item touches them.
- **The floor stays hermetic.** No test may reach the live vault or `OBSIDIAN_VAULT_PATH` (WI-024). Every oracle this item builds is a committed fixture or a committed golden, never a vault walk.
- **`Branch A does no writeback` is an existing, deliberate divergence** from the legacy body (person.py:866-870) and is *inside* the parity contract's stated scope (return values only, side effects excluded). Do not let a repaired harness "discover" it as a regression.

### E6 — Dependencies and sequencing

- **Unblocks WI-025** (`person.py` decomposition, queued directly after this) — deleting 126 lines and one of two cascades before the pure-move is the stated reason for the gate. person.py is ~1,894 lines today, up from the 1,839 the mint recorded.
- **WI-016 (fixture vault): no dependency, and the golden is NEVER re-homed onto it.** The earlier reading of this — "if WI-016 lands first the golden can be re-homed, a cheap follow-on" — was **wrong and is retracted**. WI-016 (`docs/vault-fixtures.md`, a frozen anonymized ~50-note real-data vault) sits immediately ahead of this item in `queue_order` (`state/work-items.json:2017-2027`: WI-022, WI-016, WI-023, …), so it plausibly lands first, and re-homing is not a data move. The golden's query space *and* its answers are both derived from the fixture's own notes, so a different fixture means **re-recording** — and after Cut 1 or Cut 3 the only code available to record against is post-cut code. That is E7's oracle defeat arriving through the back door of a "cheap follow-on".

  **Arm chosen: the golden is permanently homed to this item's own `tests/`-local fixture, frozen with it, and never re-homed** (the reviewer's arm (b)). The two rejected arms: (a) build both oracles on WI-016's fixture from the start — rejected, it makes a `ready` item depend on an item still at `idea` with no spec, and it would force this item's deliberately-malformed plants (E7) into a *shared* corpus that other suites assert against; (c) re-order WI-023 ahead of WI-016 — not needed under arm (b), and queue order is Dave's ruling, not this document's.

  **The solve-in-one-place cost, named rather than waved past:** this leaves two fixture vaults in `tests/`. It is the right trade because they are different *kinds* of artifact. WI-016's is a realism corpus — a sample, meant to be extended, meant to be shared. This item's is an **oracle's declaration**: the **ten** purpose-built notes E8's roster fixes as literals — a complete roster, with nothing left for a criterion to assume — whose whole value is that they are byte-frozen at the instant the golden was recorded, carrying plants (a refused address, an angle-bracket address, a whitespace-padded address, an alias that is another person's email, a two-token short-form name, an outer vertex of a non-transitivity triangle, a company that corroborates a one-token name to exactly the 0.85 threshold) that a corpus anonymized from Dave's real vault has no reason to contain. A fixture that other tests may extend cannot be a golden's baseline — extending it silently invalidates the golden. *(The earlier "three or four" here counted only E7's email plants and would have produced a fixture that cannot carry AC-4's discriminants; the later "eight plus whatever AC-1 needs" left AC-1's own by-construction coverage claim resting on notes that did not exist. The roster is now stated ONCE, complete, in E8, and every criterion cites it rather than re-deriving it or extending it.)* Making them one artifact would be the duplication error, not fixing it. When WI-016 lands, its vault serves the suites that want realism and this one keeps serving the golden; neither imports the other.
- **Touches WI-026's territory once**, in the blocked branch of E2's decision rule (a `lint_vault` repair rule for unparseable email entries). Route it there, do not grow this item into it.
- **Mints one follow-on**: E3's write-boundary phone canonicalization (E.164 at the `name_gate`), which is what would eventually let phones key into the index and let the fuzzy arm be deleted.

### E7 — One baseline moment, three named plants, and a CLOSED exception list

The golden is this item's spine, and the exploration above left it with two baseline moments: the Approach recorded it "against unchanged code" (before Cuts 1–3) while AC-4 said "before the cut", which reads as before the *consolidation* (Cut 3). Those are different instants, and the difference is load-bearing because **Cut 1 rewires `resolve()` as well as `get_by_email`** — `resolve` step 3 reads `_email_index` directly at person.py:492-496. So on E2's three divergence classes, `resolve()`'s answers move at Cut 1, while AC-4 says "any query where the policy CANNOT reproduce the golden is RED; there is no allowance for 'improved' answers". Left as it was, AC-2 and AC-4 were jointly unsatisfiable and the build's cheapest repair would have been regenerating the golden after Cut 1 — the exact defeat AC-4's own rationale names.

**Decision, in three parts.**

**(1) One baseline, stated absolutely.** The golden is recorded ONCE, at Cut 0, against the code at this item's starting HEAD — before Cut 1, before Cut 2, before Cut 3 — and is **never re-recorded**: not after a cut, not to absorb a diff, not because the fixture grew, not if WI-016 lands (E6). Its fixture is frozen with it. A build that regenerates it has destroyed the only evidence this item ships.

**(2) The plants are literals, not the spec-writer's choice.** The reviewer's collision was reachable only because AC-2 said "a note whose `emails:` carries a string `Email.parse` refuses" without saying which — and `"not-an-email"` (the tree's specimen at `tests/test_identity_index.py:186`) moves nothing (`resolve` step 3 is gated on `"@" in query_lower`, so it returns None before and after) while `"a@b"` moves everything. Which one landed decided whether the item was buildable. So the fixture's decorated/refused notes are fixed here, as literals:

| note | `emails:` entry, verbatim | why this one |
|---|---|---|
| `Jane Roe` | `"Jane Roe <jane.roe@example.com>"` | E2 class (b), the WI-017 leak shape. Parses (identifier.py:154-156 routes genuine angle-bracket forms through `parseaddr`). |
| `Kit Baldwin` | `"kit@localhost"` | E2 class (a) — **refused**, `"malformed local@domain"` (identifier.py:167-168, no `.` in domain) — and it CONTAINS `@`, so it reaches `resolve` step 3 and the divergence is visible rather than masked. |
| `Dana Okafor` | `" dana@example.com "` | E2 class (c). Must be YAML-quoted: `emails: [" dana@example.com "]`. `_index_entity` keys it un-stripped (person.py:197) and the model applies no validator (`emails: List[str]`, models.py:81), so the padding survives load — an unquoted scalar would be stripped by YAML and the plant would be inert. |

Every other fixture note's `emails:` entries are well-formed, already lowercase, whitespace-free, and unique across the fixture — so no other note contributes a divergence, and no address-collision tie-break can drift between the two lookups. *(One address, `pat@example.com`, is deliberately carried by two notes — as `Rosa Delgado`'s email and as `Alex Nkemdirim`'s ALIAS. That is not an `emails:` collision and does not weaken the clause above: it is E8's alias-preemption plant, it lives in a different index, and it moves nothing at Cut 1 because `resolve` never reaches its email step for that query. E8 fixes the full ten-note roster; this table is the email-divergence subset of it, and the two phone/company notes E8 adds carry no `emails:` at all, so they extend neither this table nor the exception list below.)*

**(3) The exception list is closed and hand-executed.** Hand-executed against person.py:458-510, :390-392, :197 and identifier.py:143-177 for the pre-cut column. Each row is a query in AC-4's derived space (each note's `emails:` entry, verbatim):

| query (the entry, verbatim) | pre-cut `resolve()` | post-cut, CUTOVER arm | post-cut, CARVE-OUT arm |
|---|---|---|---|
| `Jane Roe <jane.roe@example.com>` | Jane Roe — step 3, `_email_index` key is the whole lowered string | Jane Roe — `Email.parse` → `email:jane.roe@example.com`, present | Jane Roe |
| `kit@localhost` | Kit Baldwin — `_email_index` indexes any non-empty string | **None** — `Email.parse` refuses, step 4 gets 0 digits, step 5 finds no whole-word token | Kit Baldwin |
| `" dana@example.com "` | **None** — `resolve` strips the query at :480, the index key retains the padding, so the lookup misses | Dana Okafor — `Email.parse` strips | Dana Okafor |

So the exception list is, per arm, exactly:

- **Cutover arm — two exceptions.** `kit@localhost`: Kit Baldwin → None (a **loss**, and it is E2 class (a) made concrete: this is precisely what the corpus audit is sizing on the live vault). `" dana@example.com "`: None → Dana Okafor (a **gain**).
- **Carve-out arm — one exception.** `" dana@example.com "`: None → Dana Okafor. `kit@localhost` does not move, because the carve-out arm keeps the permissive lookup.

Note what the table also shows: the angle-bracket entry does **not** move under either arm when queried by its literal. E2 class (b)'s gain is only visible when the *canonical* address `jane.roe@example.com` is queried, and that string is not in AC-4's derived space (it is not an entry). It is in AC-2's sweep, which adds variants. The two criteria therefore partition cleanly rather than overlapping.

**What the carve-out arm has to be, for AC-2's fourth surface to agree.** Under the carve-out arm `_resolve_identifier` is handed a typed `Email`, whose value is the *parsed* address — so if the surviving authority were today's `_email_index` unchanged, the typed door would look up `jane.roe@example.com`, miss (the only key is the bracketed literal), and disagree with the three string doors. So the carve-out arm's single authority must resolve a **superset** of what pre-cut `_email_index` resolved: every raw entry by its lowered literal (that is what "carve-out" means — class (a) is not lost) **and**, where `Email.parse` succeeds, by the parsed address too. Stated as a property, not an implementation; it is what makes "one authority" true rather than "one map, two doors". And for `kit@localhost` there is no typed `Email` at all, so surface 4 is **not applicable** to that query under either arm — the criterion asserts `Email.parse` refuses it and holds the other three doors to the arm's declared answer.

**Rejected: declare `resolve()`'s email path out of AC-4's query space and let AC-2 pin it alone** (the reviewer's arm (b) for this finding). It removes the collision, but it also removes the only pre-cut *record* of what `resolve()` answered on email — which is the exact class Cut 1 moves, i.e. the one place a record is worth having. Enumerating three rows is cheaper than deleting the evidence.

**Rejected: regenerate the golden after Cut 1 and diff the two goldens.** This is the shape a build reaches for, and it looks rigorous. It is not: the second golden is recorded against post-cut code, so it ratifies whatever the cut did, and the diff is a description rather than a test. The exception list above is written in prose, in this document, before the code exists — which is what regeneration cannot reach.

### E8 — "One authority for EMAIL" was never "one authority for RESOLVE": the alias asymmetry, declared

E4 class (B) is not only a consolidation hazard. It is a **collision between two of this item's own criteria**, on the very fixture they share, and it survives the E2/E7 arm choice untouched — because the alias index is not one of the four email doors at all.

**The collision, hand-executed.** AC-4 discriminant (ii) mandates a fixture where person X carries an address as an **alias** and a different person Y carries the same address as an **email**, and requires `resolve()` to return **X**. That is today's answer and it must be preserved. But that address is one of Y's `emails:` entries, so it is also in AC-2's derived sweep, which demands all four surfaces return the *same* person. Hand-executed against the four doors:

| door | code path | answer |
|---|---|---|
| `get_by_email` | `_email_index[q]` (person.py:391) | **Y** |
| `resolve` | step 2 alias (`:488`) fires before step 3 email (`:493`) | **X** |
| `resolve_all` highest-ranked | email records first at 1.0 (`:573-578`), alias records X at 1.0 (`:581-585`), both clear the floor, `sort` at `:655` is stable | **Y** |
| `_resolve_identifier(Email.parse(...))` | delegates to `get_by_email` (`:955-956`) | **Y** |

So AC-2 as written called that fixture RED and AC-4 required exactly the answer that made it RED. Both could not ship.

**Decision: name the asymmetry as permanent, and pin it, rather than scoping it out.** `resolve()` is a cascade over **four** indexes — name, alias, email, phone — while the other three doors are email-only. An alias that happens to be spelled like an email address is a *name variant* (`tests/test_identity_index.py:104`), not an identifier, and there is no `Alias` type in `identifier.py` for it to become one (E5). "One authority for EMAIL" therefore never entailed "one answer from `resolve` for any string containing `@`", and AC-2's `why` was overclaiming when it read that way. Cut 1 does not change this and must not: it re-homes *which lookup* the email step consults, never *where the email step sits in the cascade*.

**So the property splits in two, and both halves are asserted:**

- Over the sweep **minus** the alias-colliding inputs, all four surfaces return the same person — the agreement property, unchanged.
- Over the alias-colliding inputs, the criterion asserts the **declared asymmetry** itself: the three email-only doors return the email owner Y, and `resolve` returns the alias owner X. This is strictly better than carving the input out of the sweep — a carve-out leaves the behaviour unpinned, and an unpinned asymmetry is exactly what a "tidy the cascades" refactor deletes by accident.

Note what this does *not* cost the golden: the query is in AC-4's derived space (it is both an alias and an email), and its golden value is **X** both pre-cut and post-cut under both arms, because Cut 1 never reaches step 2. It is not an exception; E7's exception list stays closed at two rows (cutover) / one row (carve-out).

**Rejected: reorder `resolve_all` to put alias before email so all four agree.** It would make the collision vanish, and it is wrong twice over: the ordering at person.py:571-572 is commented deliberate (email is the more specific signal, and it wins the `matched_via` label race), and changing `resolve_all`'s output ordering is a behaviour change to a function two consumer repos rank on — bought to tidy a criterion, which is the tail wagging the dog.

**Rejected: give discriminant (ii) its own throwaway vault so the golden's fixture stays collision-free** (the reviewer's arm (b)). It removes the collision by hiding it, and the document would then hold no statement of what `resolve` does when its cascade steps disagree — the thing Cut 3 is most likely to break.

**The fixture roster, fixed here as literals — and it is the COMPLETE roster, not a subset.** Round 1's finding was that leaving a plant to the spec-writer's choice decided whether the item was buildable; the same applies to every row here. **Ten notes**, and two invariants that make the golden order-independent. This table is the single place the roster is stated; `## Approach` Cut 0, AC-1, AC-2, AC-3 and AC-4 all cite it rather than re-deriving it, and no criterion may assume a note that is not on it:

| note | plant | serves |
|---|---|---|
| `Jane Roe` | `emails: ["Jane Roe <jane.roe@example.com>"]` | E7 / E2 class (b) |
| `Kit Baldwin` | `emails: ["kit@localhost"]` | E7 / E2 class (a), refused |
| `Dana Okafor` | `emails: [" dana@example.com "]` (YAML-quoted) | E7 / E2 class (c) |
| `John Smith` | well-formed | AC-4 discriminant (i) |
| `Sandy Forster` | well-formed | AC-4 discriminant (iii) |
| `Alex Nkemdirim` | `aliases: ["pat@example.com"]` | AC-4 (ii), the alias owner X |
| `Rosa Delgado` | `emails: ["pat@example.com"]` | AC-4 (ii), the email owner Y |
| `Emily Mendes` | well-formed, no `company:` | AC-4 discriminant (iv), E4 class (C) |
| `Priya Raman` | `phones: ["44790055852"]`; no `emails:`, no `aliases:`, no `company:` | AC-3's carve-out witness (the OUTER vertex, below); AC-1 Branch A (phone hit) |
| `Tomas Villalobos` | `phones: ["2125550147"]`, `company: "Kestrel Analytics"`; no `emails:`, no `aliases:` | AC-1 Branch B (name+company reuse); AC-1 Branch A (phone hit), second witness |

**Why the last two rows exist, and why they are literals too.** The eight-note roster was assembled to carry E7's email plants and AC-4's four discriminants, and it does — but AC-1 claims its derived case set covers Branch A (email hit), Branch A (phone hit), Branch B and Branch C **by construction**, and construction needs material. None of the eight carries a `phones:` field or a `company:` field, so on that roster the phone arm of Branch A has nothing to hit and Branch B's company-corroboration arm is unreachable: the sweep would run green over eight notes while two of the four branches it names were never entered. Adding the two notes is the cheap half; pinning their values is the load-bearing half, and each is hand-executed:

- **`Priya Raman` carries `44790055852` — an OUTER vertex of E3's triangle, never the centre.** Hand-executed against `phone_normalization.py:66-90` with `_phone_index` keyed `normalize_phone(...)` (person.py:200-203) and `get_by_phone` normalizing the query first (person.py:407): `get_by_phone("44790055852")` is a direct key hit → Priya Raman; `get_by_phone("0790055852")` misses the direct lookup and takes the fuzzy arm at `:79-80` (`norm2.startswith("44") and norm1.startswith("0")` → `"790055852" == "790055852"`) → Priya Raman; `get_by_phone("10790055852")` misses the direct lookup, and against the single indexed digit-string `44790055852` no arm fires (neither starts with `0`; `norm1[1:]` is `"0790055852"`, not `"44790055852"`) → **None**. Two matching forms, one non-matching form, which is exactly the witness AC-3 asserts. Had the note carried the centre `0790055852` instead, both other forms would match it and AC-3's negative clause would have no witness at all — see AC-3's `why`.
- **`Tomas Villalobos` carries `company: "Kestrel Analytics"`, which makes Branch B's company arm arithmetic exact.** Hand-executed: `find_or_create_stub(name="Tomas", company="Kestrel Analytics")` parses no identifiers, so Branch A is skipped (person.py:905-915); `resolve_all("Tomas", company="Kestrel Analytics")` misses steps 1–4 (`"tomas"` is not a `_cache` key — the key is `"tomas villalobos"` — no `@`, not an alias, `normalize_phone("Tomas")` is `""`), records **0.6 `partial-name`** at step 5's single-token branch (`:610-612`: `{"tomas"} ⊂ {"tomas","villalobos"}`, one shared token), and the company-hint bump at `:635-651` adds 0.25 for the exact `company` field match → **0.85 `partial-name+company-hint`**, which clears the `>= threshold` test at `:920` at exactly the default 0.85 and returns `(Tomas Villalobos, False)` through Branch B. The value is two words on purpose: the bump's second arm tests `company_lower in canonical_name_tokens` against a set of single tokens (`:639-643`), which a two-word string can never be an element of, so only the `company` field arm can fire and only for this note.

**Invariant 1: no two fixture notes share a name token** (jane, roe, kit, baldwin, dana, okafor, john, smith, sandy, forster, alex, nkemdirim, rosa, delgado, emily, mendes, priya, raman, tomas, villalobos — **twenty** distinct tokens across the ten notes; `kestrel` and `analytics` are also absent from that set, so the company bump cannot reach a second note through its name). This is load-bearing, not tidiness: `resolve` step 5 returns the **first** `_cache` entry whose token list contains the query (person.py:506-508), and `_cache` insertion order follows the filesystem walk. If two notes shared a token, every single-token golden value for it would be walk-order-dependent, and the golden would be flaky on a machine that enumerates the fixture differently. Deliberately spelling the collision pair `pat@example.com` rather than the reviewer's illustrative `jane@example.com` is what keeps this true against the `Jane Roe` plant. The alias/email collision above is the **only** deliberate cross-note key collision in the fixture; addresses are otherwise unique, per E7.

**Invariant 2: no two fixture notes carry phones that `phones_match` unifies** — and no fixture phone unifies with any of E3's three forms other than `Priya Raman`'s. This is the phone analogue of invariant 1 and it is forced by the identical mechanism: `get_by_phone` falls through to a fuzzy scan that returns the **first** `_phone_index` entry `phones_match` accepts, in insertion order (person.py:417-419). Without it, AC-3's `get_by_phone("10790055852") is None` clause could fail because some *other* note answered — a red for a reason with nothing to do with the property under test — and AC-1's phone sweep would resolve phone-hit cases to walk-order-dependent notes. Hand-executed for the two phones on the roster: `phones_match("2125550147", "44790055852")` is False (no direct match; neither UK arm, since `"2125550147"` starts with neither `44` nor `0`; neither US arm, since `"2125550147"` is 10 digits and does not start with `1`, and `"44790055852"[1:]` is not it), and `2125550147` likewise unifies with neither `0790055852` nor `10790055852` (`"10790055852"[1:]` is `"0790055852"`, not `"2125550147"`). The invariant also constrains what a "not-present phone" may be in AC-1's derived case set: not-present means not-present **under `phones_match`**, not under string equality — `10790055852` looks like a fresh number and is one `phones_match` arm away from `0790055852`.

**The two added notes are deliberately inert everywhere else.** They carry no `emails:` and no `aliases:`, so they contribute nothing to AC-2's email sweep, nothing to E7's divergence table, and nothing to the alias asymmetry above; and Cut 1 is an email cut, so no query they add can move at it. **E7's exception list therefore stays closed at two rows (cutover) / one row (carve-out)** with the roster at ten, exactly as it was at eight.

## Approach

Ship the endgame as **four ordered cuts inside one item, sequenced by oracle availability rather than by the mint's numbering**, and let the frozen Intent's own escape clause — "*or documentedly not, per kind*" — carry the phone half.

**Cut 0 (oracle repair, no production change).** Re-point `tests/test_resolve_or_create.py`'s parity legs at `_find_or_create_stub_legacy` so they compare two different implementations again; build **one** item-local fixture vault — the **ten-note roster E8 fixes as literals, complete**, carrying E7's three email plants, E8's alias/email collision pair, E4 class (C)'s short-form target, AC-3's outer-vertex phone `44790055852` and the `company:`-bearing note whose one-token name corroborates to exactly 0.85, under **both** of E8's invariants (no two notes share a name token; no two notes carry phones `phones_match` unifies); and record two committed goldens **against this item's starting HEAD — before Cut 1, before Cut 2, before Cut 3**: `find_or_create_stub`'s `(name, created_new)` over the parity case set, and `resolve()`'s answer over a query space derived from that vault's own notes (every name, every name token, every alias, every email, every phone). **The four discriminating queries AC-4 hand-states run against the same single vault** — (i) `john smith kato`, (ii) `pat@example.com`, (iii) `andy` and (iv) `emily m`; (ii) is in the derived space already, the other three are hand-stated because the derived space provably cannot reach them (E4). There is no second vault and no throwaway vault: one fixture, one golden, one baseline. **This is the only baseline moment in the item.** Neither golden is ever re-recorded, and the fixture is frozen with them — not after a cut, not to absorb a diff, not if WI-016's vault lands first (E6, E7).

**Cut 1 (email).** Give email resolution exactly one authority. The audit in `## Write Targets` picks the arm: zero unparseable live entries → `_identifier_index` is the authority and `_email_index` is deleted; otherwise the permissive lookup stays — widened to also resolve the parsed address, so the typed door reaches it too (E7) — and the carve-out is written into the code with the audit's number beside it. Under both arms the shipped property is that `get_by_email`, `resolve`, `resolve_all` and `_resolve_identifier` reach the *same* lookup, so the two-authority state ends either way — *same lookup*, note, not *same answer*: `resolve`'s alias step still preempts its email step, which is a permanent declared asymmetry rather than a leak, and E8 pins it. **`resolve()` is one of those four surfaces, so this cut moves Cut 0's golden — on exactly the queries E7's table enumerates and no others** (cutover arm: `kit@localhost` and `" dana@example.com "`; carve-out arm: `" dana@example.com "` alone). Those rows are a closed literal list in the test, each with its declared post-cut answer; a fourth query that moves is RED, and so is an exception query that lands on some *other* answer.

**Cut 2 (phone, carve-out).** Phones stay on the fuzzy path, and the reason is made unforgettable rather than asserted: E3's non-transitivity witness ships as an executable test, and the code comment at the resolution site names it. `get_by_phone` iterates a materialized snapshot, closing WI-004's explicitly-open half.

**Cut 3 (cascade).** `resolve()` becomes `resolve_all()` plus a named selection policy — one that takes the **query** as well as the candidate list, accepts 0.6 while rejecting 0.65, and orders 1.0 ties by `matched_via` in `resolve`'s own cascade order (E4 states all three constraints and why each is forced) — green against Cut 0's golden including the four hand-stated discriminants, **with zero exceptions of its own**. Cut 1's enumerated rows are the only queries in the item whose golden value legitimately moves; if the consolidation wants to move a third, that is a decision for Dave with the case named, not a green test.

**Cut 4 (deletion, last).** `_find_or_create_stub_legacy` goes, and so do **both** of its consumers, named: the six vacuous parity cases in `tests/test_resolve_or_create.py:189-211` and `:214-224`, and `test_legacy_preserves_rich_note` at `tests/test_wi126_body_preservation.py:209-215` — the legacy twin of `test_engine_preserves_rich_note` (`:200-207`), which is left standing to carry the WI-126 body-preservation property alone. That twin is a real, currently-passing test, not scaffolding, so its removal is stated rather than implied: after this cut the WI-126 property has one witness, on the engine path, which is the only path that ships. The goldens survive all of it as the durable oracle. Riders land here: delete the dangling `docs/paren-decoration-at-the-door.md` reference (person.py:113) and give the slack carve-out note (person.py:238-242) its unblock condition.

Out of scope, routed: write-boundary phone canonicalization (new item, motivation in E3); a `lint_vault` repair rule for unparseable email entries (WI-026); the other three repositories' `resolve()` (untouched).

**Handoff.** New module boundaries are not created, no schema changes, no cross-system integration — but it changes which code resolves email and which person `resolve()` returns, across three consumer repos. **Spec-writer, not architect**, at the campaign's recorded Opus/high — with the sequencing above treated as a hard constraint on the implementation plan rather than as advice.

## Design

### D0 — The arm is already selected, and the spec builds ONE arm

`## Approach` Cut 1 says "the audit in `## Write Targets` picks the arm". It has. The
grounding artifact is in HEAD at `docs/identity-cutover-corpus-audit.md` and the data-premise
gate verified that its predicate walked the domain the rule runs over: **0 of 1021 live
`emails:` entries are refused by `Email.parse`, 0 divergences in both improvement classes,
0 live non-test consumer reads of `_email_index`**. E2's decision rule therefore fires to
**CUTOVER**, and this spec is written for the cutover arm ONLY.

That is a deliberate narrowing and it is the safe direction: AC-2 and AC-4 are written
arm-agnostically, so the criteria are undisturbed, but a plan that carried both arms would
hand the builder a build-time judgement call — the thing this document has spent four
architect rounds removing. **If the conductor's close-out re-run of the audit command returns
a nonzero (b), the build STOPS and the item returns for a spec revision; it does not switch
arms mid-build.** That is stated as a Prerequisite, not as a branch in the plan.

One consequence worth naming because two review rounds flagged it: round 3's and round 4's
open note about `_remove_entity_from_indexes` needing the same widening as the insert path
applies **only to the carve-out arm**. Under cutover `_remove_entity_from_indexes`
(`obsidian_schemas/repositories/person.py:_remove_entity_from_indexes:335`) already removes
identifier keys through `_project_identifiers`, which is the same projection that inserted
them — so the asymmetry the note predicted cannot arise, and the note is closed by the arm
selection rather than by work.

### D1 — The fixture: one roster declaration, committed as DATA

E6 fixes the arm ("permanently homed to this item's own `tests/`-local fixture, frozen with
it, never re-homed") and E8 fixes the roster. AC-1 fixes the REPRESENTATION: the test runs
"against a fixture vault seeded from the golden's own declaration". So the fixture is not a
directory of committed `@*.md` notes — it is one committed JSON declaration plus a seeder that
writes the vault into a temp directory:

- `tests/fixtures/identity_endgame/roster.json` — the frozen ten-note roster, byte-frozen data.
- `tests/identity_fixture.py` — `seed_vault(roster, dest) -> Path`, which writes one
  `@<name>.md` per entry and returns the vault path. Not a `test_*.py` module, so pytest never
  collects it.

Two reasons this beats committed `.md` fixtures, both concrete rather than aesthetic. First,
the committed corpus cannot drift: AC-1's sweep MUTATES the vault (Branch C mints notes,
pre-cut Branch B writes identifiers back), so a committed vault would be rewritten by its own
test. Second, `tests/test_vault_path_required.py:_scanned_markdown_files:421` walks
`REPO_ROOT.rglob("*.md")` excluding only `.git/.venv/docs/state/node_modules` — committed
fixture notes would join that wall's population; a JSON declaration does not.

`roster.json` schema (`schema_version: 1`), one object per note in the order below, which IS
the frozen order every derivation uses:

```json
{
  "schema_version": 1,
  "notes": [
    {"name": "Jane Roe",   "emails": ["Jane Roe <jane.roe@example.com>"], "aliases": [], "phones": [], "company": null},
    {"name": "Kit Baldwin","emails": ["kit@localhost"],                   "aliases": [], "phones": [], "company": null}
  ]
}
```

**The complete roster, as literals.** E8's table plus the three values E7 constrained by rule
but never spelled — `John Smith`'s, `Sandy Forster`'s and `Emily Mendes`'s "well-formed"
addresses. Fixing them here is this document's own standing rule ("an unfixed plant decides
buildability") applied to the last three plants the folds left to prose:

| # | `name` | `emails` | `aliases` | `phones` | `company` |
|---|---|---|---|---|---|
| 1 | `Jane Roe` | `["Jane Roe <jane.roe@example.com>"]` | — | — | — |
| 2 | `Kit Baldwin` | `["kit@localhost"]` | — | — | — |
| 3 | `Dana Okafor` | `[" dana@example.com "]` | — | — | — |
| 4 | `John Smith` | `["john.smith@example.com"]` | — | — | — |
| 5 | `Sandy Forster` | `["sandy.forster@example.com"]` | — | — | — |
| 6 | `Alex Nkemdirim` | — | `["pat@example.com"]` | — | — |
| 7 | `Rosa Delgado` | `["pat@example.com"]` | — | — | — |
| 8 | `Emily Mendes` | `["emily.mendes@example.com"]` | — | — | — |
| 9 | `Priya Raman` | — | — | `["44790055852"]` | — |
| 10 | `Tomas Villalobos` | — | — | `["2125550147"]` | `Kestrel Analytics` |

The three added addresses satisfy every clause E7 and AC-2 place on "every other fixture
note's entries": well-formed, already lowercase, whitespace-free, and unique across the
fixture. Each is keyed identically by `_email_index` (`email.lower()`,
`obsidian_schemas/repositories/person.py:_index_entity:197`) and by `Email.key`
(`obsidian_schemas/identifier.py:Email:176`), so none of the three contributes a Cut-1
divergence and **E7's exception list stays closed at two rows** with the addresses pinned,
exactly as it was with them left to prose. `Tomas Villalobos` is the ONLY note carrying
`company:`, which is what makes AC-1's Branch-B arm yield exactly one case.

**The seeder's YAML contract, because one entry depends on it.** `Dana Okafor`'s padded entry
must survive load as `" dana@example.com "`, spaces intact. The seeder therefore emits every
`emails:`/`aliases:`/`phones:` element double-quoted (`  - " dana@example.com "`), never as a
bare scalar — a bare scalar is stripped by the YAML loader and the plant goes inert. Nothing
downstream re-normalizes it: `obsidian_schemas/models.py:Person:81` is a bare
`emails: List[str]` and the module carries no validator, and `parser.py` carries no `strip`.

**Both E8 invariants are properties of this table and are asserted, not assumed.** Invariant 1
(no two notes share a name token) holds over the twenty tokens *jane, roe, kit, baldwin, dana,
okafor, john, smith, sandy, forster, alex, nkemdirim, rosa, delgado, emily, mendes, priya,
raman, tomas, villalobos*, and `kestrel`/`analytics` are absent from that set. Invariant 2 (no
two notes carry phones `phones_match` unifies) holds over `{44790055852, 2125550147}`. Both are
re-derived from `roster.json` at test time rather than restated, so a future edit to the roster
that breaks either is RED rather than silently flaky.

### D2 — The two goldens: frozen data with a regeneration tripwire

Both goldens live beside the roster and are recorded ONCE, at Cut 0, against this item's
starting HEAD — before Cut 1, before Cut 2, before Cut 3 — and are **never re-recorded** (E7).

`tests/fixtures/identity_endgame/stub_golden.json`:

```json
{
  "schema_version": 1,
  "recorded_at": "cut-0",
  "roster_digest": "<sha256 of roster.json's bytes>",
  "cases": [
    {"ordinal": 1, "arm": "per-email", "name": "Jane Roe", "email": "Jane Roe <jane.roe@example.com>",
     "phone": null, "company": null, "expected_name": "Jane Roe", "expected_created": false}
  ]
}
```

`tests/fixtures/identity_endgame/resolve_golden.json`:

```json
{
  "schema_version": 1,
  "recorded_at": "cut-0",
  "roster_digest": "<sha256 of roster.json's bytes>",
  "queries": [
    {"ordinal": 1, "arm": "name",  "query": "Jane Roe",      "expected": "Jane Roe"},
    {"ordinal": 5, "arm": "email", "query": "kit@localhost", "expected": "Kit Baldwin"}
  ]
}
```

`expected` is the resolved `person.name`, or `null` for a `None` answer.

**`roster.json` IS the golden's own declaration, in AC-1's sense.** The roster lives in its own
file rather than inline in each golden for one reason — two goldens must not carry two copies of
one declaration, which is the duplication this item exists to remove — and the two are bound by
`roster_digest`, which every check verifies before it reads a case. A roster edited without a
re-record is RED, and a re-record is a diff a reviewer sees. Roster and goldens are frozen
together and are never re-homed onto WI-016's vault (E6).

**What makes "never re-recorded" machine-checkable rather than a promise.** Three clauses,
each of which a regenerated golden fails:

1. `roster_digest` must equal the sha256 of the committed `roster.json` bytes. A fixture edit
   without a re-record is RED; a re-record is visible in the diff.
2. The AC-4 check carries the two exception rows' **pre-cut** values as literals in its own
   source — `("kit@localhost", "Kit Baldwin")` and `(" dana@example.com ", None)` — and asserts
   the golden still holds them. A golden regenerated after Cut 1 records `None` and
   `"Dana Okafor"` for those two queries and this assertion goes RED. This is the clause E7
   said regeneration "cannot reach": it is prose in this document AND a literal in the test,
   never data the recorder can produce.
3. `recorded_at` must be the literal `"cut-0"`.

### D3 — Cut 0: the oracle

**(a) Repair the parity legs.** `tests/test_resolve_or_create.py:190` and `:214` currently
compare `parse_identifiers(...) + resolve_or_create(...)` against itself, because the Phase-4
adapter swap made `find_or_create_stub`
(`obsidian_schemas/repositories/person.py:find_or_create_stub:688-697`) *be* the engine. Point
the "legacy" leg at `_find_or_create_stub_legacy` so the six cases compare two implementations
again. They are deleted at Cut 4 (AC-1 requires it); their value is the three cuts in between,
which is exactly the window E1 says the oracle must survive.

**(b) Record both goldens.** `tests/record_identity_golden.py` — a one-shot recorder, run by
hand once at Cut 0 and never again. It seeds a temp vault from `roster.json`, derives the case
list and the query list by the rules below, executes them against **unchanged** code, and
writes the two JSON files.

It lives under `tests/`, NOT under `scripts/`, and that is load-bearing rather than tidy: it
writes files with `Path.write_text`, and `tests/test_write_routing.py:91` sweeps
`python_files_under(PACKAGE_ROOT, SCRIPTS_ROOT)` for exactly that capability outside
`obsidian_schemas/vault_io.py`. A recorder in `scripts/` is RED on a standing wall before it
runs. The same applies to `tests/identity_fixture.py`.

**AC-1's case derivation, per arm, in this order** (roster order, and within a note: emails,
then phones, then company):

| arm | rule |
|---|---|
| `per-email` | one case per `emails:` entry: `name=<the note's name>, email=<the entry verbatim>` |
| `per-phone` | one case per `phones:` entry: `name=<the note's name>, phone=<the entry verbatim>` |
| `per-company` | one case per note carrying `company:`: `name=<the note's FIRST name token>, company=<the company>`, no identifiers |
| `not-present` | one case per base case above, at ordinal `10 + i`, taking its fresh values from the pinned table below |

That yields **10 base cases and 10 not-present cases, 20 in all**. `Alex Nkemdirim` contributes
no base case (aliases are not an arm), which is correct and is why AC-1's coverage claim rests
on the ROSTER rather than on the sweep.

**The not-present variants, pinned as literals.** AC-1 constrains them twice (a not-present
NAME is multi-token, or `weak_identity_reason`
(`obsidian_schemas/name_validation.py:weak_identity_reason:531-532`) raises `WeakIdentityError`
where the case expects a create; a not-present PHONE is not-present under `phones_match`, not
under string equality) and round 4 added a third (keep the Branch-B variant's name away from
`tomas`/`villalobos`, where `0.65 + 0.25` would silently convert a create into a reuse). All
three are satisfied by construction below, and none of the twenty fresh tokens appears in the
roster's twenty:

| variant ordinal | pairs with | `name` | identifier / hint |
|---|---|---|---|
| 11 | 1 | `Wilbur Achebe` | `email=wilbur.achebe@notpresent.example.com` |
| 12 | 2 | `Greta Oyelaran` | `email=greta.oyelaran@notpresent.example.com` |
| 13 | 3 | `Marcus Thibodeaux` | `email=marcus.thibodeaux@notpresent.example.com` |
| 14 | 4 | `Ingrid Castellanos` | `email=ingrid.castellanos@notpresent.example.com` |
| 15 | 5 | `Otto Farrimond` | `email=otto.farrimond@notpresent.example.com` |
| 16 | 6 | `Neve Kowalczyk` | `email=neve.kowalczyk@notpresent.example.com` |
| 17 | 7 | `Rafael Ibarrola` | `email=rafael.ibarrola@notpresent.example.com` |
| 18 | 8 | `Sunniva Blackwood` | `phone=33612345678` |
| 19 | 9 | `Hugo Pemberton` | `phone=33698765432` |
| 20 | 10 | `Delphine Marchetti` | `company=Kestrel Analytics` |

Both fresh phones are not-present under `phones_match` and not merely under string equality,
hand-executed against `obsidian_schemas/phone_normalization.py:phones_match:58-90`: neither
`33612345678` nor `33698765432` starts with `44` or `0`, and neither is an eleven-digit string
starting with `1`, so no UK arm and no US arm can fire against `44790055852`, `2125550147`, or
against each other.

**The sweep runs sequentially in ONE temp vault, replaying the frozen ordered case list.** That
is AC-1's own clause ("every note a create case mints is visible to every later case in the
same run"), and it is safe because all ten base cases precede all ten variants and no minted
name shares a token with any roster name or with any other minted name — hand-executed:
`resolve_all("Delphine Marchetti", company="Kestrel Analytics")` at ordinal 20 has no candidate
to bump, because the company-hint bump at
`obsidian_schemas/repositories/person.py:resolve_all:635-651` lifts existing candidates and
never creates one.

**The one thing round 4 got right that this spec must not repeat.** AC-1's per-case annotation
names the derivation ARM, not the runtime BRANCH, and the two differ for three cases. The
golden's field is therefore `arm`, and the record is explicit: `Jane Roe`, `Kit Baldwin` and
`Dana Okafor` all fall through to Branch B pre-cut (`Email.parse` refuses `kit@localhost`;
`jane.roe@example.com` misses `_email_index`'s bracketed-literal key; `dana@example.com` misses
the padded key), and Jane's and Dana's move to Branch A post-cut. Branch coverage is carried by
`Rosa Delgado`'s `pat@example.com` (Branch A, email, both pre- and post-cut), `Priya Raman`'s
and `Tomas Villalobos`' phones (Branch A, phone), `Tomas`+`Kestrel Analytics` (Branch B), and
the ten variants (Branch C).

**AC-1's golden has NO exceptions across any cut.** Hand-executed for the three cases whose
runtime branch moves at Cut 1: Jane pre-cut takes Branch B and reuses on exact-name at 1.0
returning `("Jane Roe", False)`, post-cut takes Branch A and returns `("Jane Roe", False)`;
Dana likewise returns `("Dana Okafor", False)` on both sides; Kit parses no identifier at all on
either side. The pairs are identical; only the SIDE EFFECT differs (pre-cut Branch B calls
`_writeback_identifier`, post-cut Branch A does not), and side effects are explicitly outside
the parity contract (E5). No later case reads the written-back value, because the case list is
frozen data derived once from `roster.json` and is never re-read from the mutated vault.

**AC-4's query derivation**: for every note in roster order — the exact `name`, then each
whitespace token of that name in order, then each alias, then each email, then each phone — the
resulting list de-duplicated by query string, first occurrence winning. `pat@example.com`
appears twice (Alex's alias, Rosa's email) and collapses to one entry; the space is **39
queries**, stated as informational and asserted by re-derivation rather than pinned as a
number.

### D4 — Cut 1: email resolution gets exactly one authority

`_email_index` is deleted outright and `_identifier_index` becomes the email authority. All
changes are in `obsidian_schemas/repositories/person.py`:

1. Delete the `_email_index` attribute (`__init__:156`), its population loop
   (`_index_entity:194-197`), its clear (`_clear_indexes:328`) and its removal loop
   (`_remove_entity_from_indexes:337-342`). The identifier-index removal at `:374-377` already
   covers email keys through `_project_identifiers`.
2. `get_by_email` becomes the ONE reader: parse the argument with `Email.parse`, return `None`
   on `IdentifierError`, look up `self._identifier_index.get(ident.key)`, and hydrate through
   `self._cache.get(ref.canonical_key)`. Signature, return type and exception set are
   unchanged — it still returns `Optional[Person]` and still raises nothing.
3. `resolve` step 3 (`resolve:492-496`) and `resolve_all` step 2 (`resolve_all:571-578`) both
   stop reading a mapping and call `self.get_by_email(query)` instead. The `"@" in query_lower`
   gate stays on both: it changes no answer (a non-address query is refused by `Email.parse`
   anyway) and it keeps the pre-cut cascade shape legible.
4. `_resolve_identifier` (`:955-956`) is unchanged — it already delegates `Email` to
   `get_by_email`, which is now the index reader. That is what makes "one authority" structural
   rather than behavioural: after this cut the string `_identifier_index` is read for an
   `email:` key in exactly one function.
5. `_project_identifiers`' docstring (`:236-238`) loses the three-month-old "942 notes,
   2026-06-13, ZERO failures" claim and gains a pointer to
   `docs/identity-cutover-corpus-audit.md`. A pointer, not a fresh number — the number drifts
   the same way (this is the data-premise gate's own recommendation, and it rides in AC-5's
   documentation-truth class).

**The four surfaces, post-cut, on the three plants** — hand-executed and identical to E7's
table, which is why this cut moves exactly the two queries AC-4 enumerates:

| query | `get_by_email` | `resolve` | `resolve_all[0]` | `_resolve_identifier(Email.parse(q))` |
|---|---|---|---|---|
| `Jane Roe <jane.roe@example.com>` | Jane Roe | Jane Roe | Jane Roe | Jane Roe |
| `kit@localhost` | None | None | None | N/A — `Email.parse` refuses |
| `" dana@example.com "` | Dana Okafor | Dana Okafor | Dana Okafor | Dana Okafor |

**The alias asymmetry is untouched and is asserted.** For `pat@example.com` the three
email-only doors return `Rosa Delgado` and `resolve` returns `Alex Nkemdirim`, because
`resolve`'s alias step precedes its email step and `resolve_all` records email before alias at
equal confidence under a stable sort. AC-2's scope rule is stated as a PREDICATE rather than
per-literal, so the whitespace and lowercase variants of a colliding address are covered by the
same clause: **a sweep member is in the asymmetry set iff its stripped, lowered form is a key of
`_alias_index` belonging to a different person than the address's email owner.**

**One test module is falsified by this cut and must be rewritten, not deleted.**
`tests/test_identity_index.py:183-201` pins the divergence deliberately —
`assert "not-an-email" in repo._email_index` and `assert "bad email" in repo._email_index`,
each with the comment "legacy still has it". That property is exactly what Cut 1 ends. It is
replaced by the post-cutover property with the audit's number as its warrant: a note carrying
`not-an-email` loads without raising, contributes no identifier, and resolves through **no**
door — `get_by_email("not-an-email") is None` and `repo.resolve("not-an-email") is None` — and
the reason it is acceptable to lose is that the live corpus contains zero such entries
(`docs/identity-cutover-corpus-audit.md`, clause (b): 0 of 1021).

### D5 — Cut 2: the phone carve-out, made executable

Two changes in `obsidian_schemas/repositories/person.py:get_by_phone:394-421`:

1. The fuzzy scan iterates a **materialized snapshot**:
   `for indexed_phone, cache_key in list(self._phone_index.items()):`. This closes WI-004's
   explicitly-open half (`docs/concurrent-access.md:8713-8714` — `:417` iterates the live
   mapping while `_clear_indexes:326-333` mutates it in place).
2. The scan carries a comment naming the non-transitivity as the reason phones cannot key into
   `_identifier_index`, and citing the executable witness by name
   (`tests/test_identity_endgame.py::test_phones_stay_on_the_fuzzy_path_and_the_reason_is_executable`).

**AC-3's structural clause needs a sharper predicate than its own parenthetical, and the spec
says so rather than letting the build discover it.** AC-3 glosses the mechanism as "the loop's
iterable is a call, not a bare attribute". Today's iterable is already a call —
`self._phone_index.items()` — so that gloss alone is **vacuously green against unchanged
code**. The property AC-3 actually asserts is its leading clause, "iterates a MATERIALIZED
snapshot", so the check is: every `for` loop in the package whose iterable reaches
`self._phone_index` has an iterable that is a call to one of `list`, `tuple`, `sorted`,
`frozenset` or `dict` wrapping that reach. That is strictly stronger than the gloss and
satisfies it (a `list(...)` call is a call and is not a bare attribute); the parenthetical is
not weakened, it is discharged by something that can fail.

### D6 — Cut 3: one cascade, one named selection policy

`resolve()` keeps no match logic of its own. A module-level function in
`obsidian_schemas/repositories/person.py` — module-level so AC-4's "named module-level
selection policy" is checkable by attribute lookup rather than by reading:

```python
# resolve()'s own cascade order, which is what breaks a 1.0 tie between two
# DIFFERENT people. resolve_all emits email before alias deliberately
# (person.py:571-572); resolve has always answered alias first. Cut 3 preserves
# resolve's answer without touching resolve_all's ordering.
_RESOLVE_CASCADE_ORDER = ("exact-name", "alias", "email", "phone")


def select_resolution(query: Optional[str],
                      candidates: List[ResolveCandidate]) -> Optional[Person]:
    """The ONE selection policy resolve() applies to resolve_all()'s ranking."""
```

It returns a `Person` (the winning candidate's `.person`) or `None` — `resolve()`'s own return
type, so the method body is a delegation with no unwrapping of its own.

The policy, stated as a rule and not as code:

- No candidates → `None`. This arm is checked FIRST, so a `None` or empty query cannot reach
  the tokenizer and cannot raise.
- **Single-token query** (the stripped query contains no whitespace): take the highest
  confidence; among candidates tied at that confidence, take the one whose `matched_via`'s
  leading label ranks first in `_RESOLVE_CASCADE_ORDER`, unknown labels last, insertion order
  breaking a remaining tie.
- **Multi-token query**: return a candidate only if its confidence is `1.0`; otherwise `None`.
  Ties at `1.0` break by the same `matched_via` rule.

`matched_via` may carry a `+company-hint` suffix (`resolve_all:650`), so the rank is read off
the label BEFORE the first `+`. `resolve()` itself passes no company, so from this caller the
suffix never appears — the rule is stated totally anyway, because the policy is module-level
and a future caller may not be `resolve`.

**Why exactly these two arms, and why a confidence threshold is the wrong shape.** E4's three
constraints are jointly sufficient, and the reason is structural rather than empirical:
`resolve` step 5 tests `query_lower in name.split()`
(`obsidian_schemas/repositories/person.py:resolve:507`), which can only be true for a query with
no whitespace — so a multi-token query is answerable today ONLY by steps 1–4, every one of
which scores `1.0` in `resolve_all`. And the two 0.6 `partial-name` sites cannot collide across
the arms: the token-subset arm requires `len(shared) >= 2` (`resolve_all:608`), unreachable from
a one-token query, and the short-form arm requires `len(query_tokens) == 2` (`:618`),
unreachable from one token. So a single-token query's non-1.0 candidates are only step 5's 0.6,
and a multi-token query's are only 0.65 and 0.6.

Hand-executed against every answer this document requires:

| query | `resolve_all` records | policy | required |
|---|---|---|---|
| `john smith kato` | 0.65 `token-subset` | multi-token, not 1.0 → **None** | None (E4 A) |
| `pat@example.com` | Rosa 1.0 `email`, Alex 1.0 `alias` | single-token, tie → `alias` ranks above `email` → **Alex Nkemdirim** | Alex (E4 B) |
| `andy` | nothing | **None** | None |
| `emily m` | Emily 0.6 `partial-name` (step 6) | multi-token, not 1.0 → **None** | None (E4 C) |
| `sandy` | Sandy 0.6 `partial-name` (step 5) | single-token, best → **Sandy Forster** | Sandy |
| `Jane Roe` | Jane 1.0 `exact-name` | multi-token, 1.0 → **Jane Roe** | Jane |
| `44790055852` | Priya 1.0 `phone` | single-token, best → **Priya Raman** | Priya |

`resolve()`'s body after the cut is the empty-query guard, `self.resolve_all(query)`, and
`select_resolution(query, candidates)`. It reads none of `_cache`, `_alias_index`,
`_email_index` (gone) or `_phone_index`; reading its own `query` argument is inside AC-4's
structural clause, which forbids reading the four indexes and nothing else.

### D7 — Cut 4: the deletion, and the riders

- Delete `_find_or_create_stub_legacy` (`obsidian_schemas/repositories/person.py:699-824`).
- Delete the six vacuous parity cases repaired at Cut 0 (`tests/test_resolve_or_create.py`
  `PARITY_CASES` + `test_engine_matches_legacy_return_value` + the seed helper if it is left
  with no caller, and `test_engine_matches_legacy_on_weak_identity`).
- Delete `test_legacy_preserves_rich_note` (`tests/test_wi126_body_preservation.py:209-215`).
  Its engine twin at `:200-207` is left standing and carries the WI-126 body-preservation
  property alone — a real, currently-passing test is being removed, and this spec says so out
  loud because AC-1 forces it.
- Delete the prose mention at `obsidian_schemas/repositories/person.py:find_or_create_stub:675`
  ("The original body is preserved verbatim as `_find_or_create_stub_legacy`…"). The
  data-premise gate found this third site; `## Approach` Cut 4 names only two, and AC-1's
  literal-text scan is total and would have caught it at the last task. Naming it here moves
  the discovery to spec time.
- Repair the stale claim three lines below it at `:685` — "The Phase-5 replay confirms zero
  return-value divergence over the real vault". E1 establishes that replay is cross-repo,
  unreachable from this tree, and predates WI-020/WI-021. It is replaced by a pointer to the
  committed goldens, which are the replay's in-tree successor.
- Rider: delete the dangling `docs/paren-decoration-at-the-door.md` reference at `:113`.
- Rider: give the slack carve-out (`_project_identifiers:238-242`) its **unblock condition** on
  a line beginning with the literal marker `UNBLOCK:` — what would have to be true of the
  frontmatter for `slack` to be projectable. The marker is pinned so the clause is checkable by
  a text scan rather than by prose recognition.
- Rider: repair the false comment at `resolve_all:615-617`. It claims the short-form match
  "stays low confidence (< 0.5) and gets filtered out below"; it records 0.6 at `:626` against
  the `>= 0.5` floor at `:654`. The replacement states what actually happens: the branch
  records 0.6, which SURVIVES the floor, and the company hint bumps an already-surviving
  candidate rather than rescuing a filtered one.

### D8 — Three new derivations, and why they go in `tests/derivations.py`

The `ast` capability is single-homed by a standing set-EQUALITY assertion — `homes ==
{"tests/derivations.py"}` in both `tests/test_loud_fail_harness.py:103` and
`tests/test_name_gate_wall.py:_check_the_ast_capability_stays_single_homed:1136`, over
`python_files_under(PACKAGE_ROOT, TESTS_ROOT)`. **Every structural predicate this item needs
must therefore be a new export of `tests/derivations.py`, and no test module this item writes
may import `ast`.** A private copy in the check module is RED on two standing walls before it
asserts anything.

| new export | serves | returns |
|---|---|---|
| `phone_index_iteration_sites(files)` | AC-3 | one record per `for` loop whose iterable reaches `self._phone_index`, classified `materialized` (wrapped in `list`/`tuple`/`sorted`/`frozenset`/`dict`) or `live` |
| `attribute_reads_in(files, qualnames, attrs)` | AC-4 | every `<x>.<attr>` load inside the named functions, for `attr` in `attrs` |
| `docs_markdown_mentions(files)` | AC-5 | every `docs/`-relative `.md` path mentioned in the source text, with its module and line |

`tests/test_loud_fail_harness.py:test_derivations_are_single_sourced:74-97` asserts a **required
subset** of six named exports, explicitly "not a cardinality bound", so three more exports join
legally.

**`docs_markdown_mentions`' rule, total, with its exclusion class named** — the data-premise
gate's counterexample hunt found three members that are false BY DESIGN and are not
dispositioned anywhere else in this document:

- Match `[A-Za-z0-9._/-]+\.md` per line over the file's whole text (comments and docstrings
  alike).
- A match is IN SCOPE iff it **starts with** `docs/`. That single clause is the exclusion: the
  three cross-repository pointers — `orchestrator/docs/identity-model-revised-2026-06-13.md`
  (`obsidian_schemas/identifier.py:3-4`), `orchestrator/docs/name-validation-and-cleanup.md`
  (`obsidian_schemas/name_validation.py:29`) and `orchestrator/docs/find-or-create-stub.md`
  (`obsidian_schemas/repositories/person.py:729`, which dies with Cut 4) — match as
  `orchestrator/docs/…`, which does not start with `docs/`. Each names a real audit in a
  sibling repo and none can ever resolve under this tree; **a scan that collected them would go
  RED on two correct pointers and the cheapest repair would be deleting them, which is this
  item's own harm class.**
- The same clause excludes the eighteen vault-note filename illustrations (`Name.md`,
  `Speechmatics.md`, `October.md`, …), which are Obsidian note names in docstring examples.
- `identifier.py`'s pointer is line-WRAPPED, so the per-line scan sees the bare tail
  `revised-2026-06-13.md`, which also does not start with `docs/`. That is correct and
  deliberate, not a blind spot to fix: the pointer is out of scope by the same clause either
  way.
- Every in-scope mention must resolve to an existing file under the repo root.

### D9 — The interpreter bridge is mandatory for this item's check module

The conveyor runs a `kind: test` check as `<some python> -c "<importlib bootstrap>" <module
path> <check name>`, and the interpreter is the ADVANCER's, not this project's
(`tests/ac_interpreter.py:1-44`). Four of this item's five checks EXECUTE `PersonRepository`,
so the very first package import pulls in `pydantic` and every criterion reports
`ModuleNotFoundError` — the exact battery output WI-021's first build attempt drew on
five-of-five criteria with a green floor in the same tree.

So `tests/test_identity_endgame.py` calls `ensure_project_interpreter(__file__)` as its **first
statement, ahead of every package import**. This is not optional and it is not discoverable
from the criteria text; it is stated here because the failure is invisible from inside the
suite.

`tests/test_ac_interpreter.py` is the wall that proves the bridge by EXECUTION, and it is
currently pinned to one document (`WORK_ITEM_DOC = ROOT / "docs" / "write-door-bypasses.md"`,
`:40`). It is generalized to a tuple of documents and iterated, so this item's five checks are
proved under the foreign interpreter by the wall that already exists rather than by a second
copy of it. That is a solve-in-one-place call with a disclosed cost: five more `-S` subprocesses
per floor run, each re-execing into a one-node pytest.

### D10 — Wall memberships (the INBOUND half), derived not remembered

The derivation: sweep `tests/` for modules that read the text of files they did not name at
authoring time — in their own source or through a helper under the same root — then read every
file the sweep returns at FILE granularity. Run on 2026-09-06 it returns fourteen modules;
this census is a FLOOR measured at that date, never a total. Discarding by reading leaves the
walls below. **Membership is closed by CALLING each wall's own shipped predicate on the final
text of every file this item creates or edits**, never by reasoning about which shapes match:

| wall | universe | what it requires of this item's files |
|---|---|---|
| `tests/test_loud_fail_harness.py:test_derivations_are_single_sourced` | `python_files_under(PACKAGE_ROOT, TESTS_ROOT)`, set EQUALITY | no new module names `ast`; the three new predicates are exports of `tests/derivations.py` |
| `tests/test_name_gate_wall.py:_check_the_ast_capability_stays_single_homed` | same, set EQUALITY | same |
| `tests/test_name_gate_wall.py:_check_the_loud_fail_write_universe_in_the_removal_direction` | `non_completed_write_sites([person.py])`, pinned to five qualnames and eight sites | unchanged: the functions this item edits or deletes contain no `write_text`/`write_bytes`/`write_note`/`create_note`/`move_note` attribute call, so none of them is in that universe |
| `tests/test_loud_fail_write.py:test_write_failure_raises_and_noops_keep_their_return` | `non_completed_write_sites(python_files_under(PACKAGE_ROOT))`, bidirectional classification | same |
| `tests/test_concurrent_access.py:test_wi020_derivations_survive_the_routing` | four derivations over `PACKAGE_ROOT`, count pins 4 / `write_markdown_file` / 8 / 4 / 3 | unchanged: no repository subclass, no `_load_file`, no reserializing writer is touched |
| `tests/test_write_routing.py` | `filesystem_mutation_uses`, `os_module_attribute_uses`, `module_import_uses` over `PACKAGE_ROOT + SCRIPTS_ROOT` | `person.py`'s edits name no filesystem-mutation capability; the recorder and seeder are under `tests/`, outside this universe, which is WHY they are there |
| `tests/test_company_name_contract.py:test_company_name_punctuation_survives_every_write_arm` | `character_class_strip_sites` + `frontmatter_write_arms` over `PACKAGE_ROOT + SCRIPTS_ROOT`, bidirectional | unchanged: `person.py` contributes no `write_frontmatter` arm and no character-class strip; the deleted function contains neither |
| `tests/test_address_splitter.py:test_address_splitting_is_single_homed_and_agrees_with_email_parse` | `address_splitting_implementations` over `PACKAGE_ROOT + SCRIPTS_ROOT`, exactly one home | unchanged: the one home is `name_gate.split_address`; nothing this item writes splits an address |
| `tests/test_vault_path_required.py:test_no_implicit_vault_path_defaults` | `(REPO_ROOT/"obsidian_schemas"\|"scripts").rglob("*.py")` | `person.py`'s edits introduce no caller-independent default path |
| `tests/test_vault_path_required.py:test_docs_do_not_advertise_no_arg_construction` | `REPO_ROOT.rglob("*.md")` minus `.git/.venv/docs/state/node_modules` | **this item adds no `.md` under `tests/`** — the fixture is JSON and the vault is seeded into a temp directory, so nothing joins this population |
| `tests/test_ac_interpreter.py:check_module` | `TESTS_ROOT.glob("test_*.py")`, unique `def <check>(` | the five check names appear in exactly one module, `tests/test_identity_endgame.py` |

Anything the RUN returns that this table did not name is NAMED in the Build Log and satisfied —
never worked around, and never satisfied by narrowing the wall.

### Prerequisites & Assumptions

- **Services:** none. The floor is hermetic and no test may reach the live vault or
  `OBSIDIAN_VAULT_PATH` (E5, WI-024's standing constraint).
- **Env vars / credentials / scopes:** none.
- **Required state in HEAD before the build is armed:** `docs/identity-cutover-corpus-audit.md`
  (the `kind: precondition` fence below; already committed).
- **The arm is CUTOVER and is not re-decided in the build.** The audit's clause (b) is 0 of
  1021. If the conductor's close-out re-run returns nonzero, the build STOPS and the item
  returns for a spec revision.
- **Interpreter:** the floor command is
  `/Users/davewascha/Workspaces/obsidian-schemas/.venv/bin/python -m pytest
  /Users/davewascha/Workspaces/obsidian-schemas/tests -q`, run against the worktree. System
  python has no pytest. The `.venv`'s editable install is stale by design; the suite works
  because pytest prepends its rootdir — see `pipeline-runners.yaml`, and do not "fix" it.
- **Consumer contracts that must not move:** `find_or_create_stub`'s signature, return shape and
  exception set (`obsidian_schemas/repositories/person.py:find_or_create_stub:658-697`), and the
  `normalize_phone`/`phones_match` compat re-export (`:78-85`), which two live consumers import
  by this module's path.
- **Trust boundaries:** unchanged. `Email.parse` is already the address authority at the write
  door; this item moves a READ path onto the same parser and adds no new input surface.
- **Assumed and stated rather than implicit:** `_cache` insertion order is the filesystem walk
  (`obsidian_schemas/repositories/base.py:load:231` globs unsorted), which is why both E8
  invariants are load-bearing; and `_adopt` (`base.py:_adopt:158-181`) appends a minted note to
  a COPY of the mapping rather than re-globbing, which is what makes AC-1's ordered replay
  deterministic under mutation.
- **No other work item is a prerequisite.** WI-016 sits immediately ahead in `queue_order` and
  is deliberately NOT a dependency (E6, arm (b)); if it lands first, nothing here changes.

## Edge Cases & Open Questions

- **Case:** the query is empty, `None`, or whitespace-only.
  **Decision:** `resolve` returns `None` and `resolve_all` returns `[]`, unchanged.
  `select_resolution` receives an empty candidate list and returns `None` before touching the
  query, so a `None` query cannot raise.
  **Reasoning:** today's behaviour (`resolve:477-478` vs `resolve_all:547-548`) and round 3
  swept it; the policy must not be the first thing to change it.

- **Case:** an `emails:` entry that `Email.parse` refuses.
  **Decision:** after Cut 1 it resolves through no door. `get_by_email` returns `None`,
  `resolve` falls through its cascade, `resolve_all` records no email candidate, and
  `_project_identifiers` skips it as it already does (`:246-252`).
  **Reasoning:** this is E2 class (a) and it is the only class the cutover can LOSE. The live
  size is 0 of 1021 (`docs/identity-cutover-corpus-audit.md`), which is what makes the loss
  acceptable, and the number is what the code comment points at rather than restates.

- **Case:** two callers hit the repository concurrently while a refresh clears the indexes.
  **Decision:** `get_by_phone` iterates `list(self._phone_index.items())` — a materialized
  snapshot. `load()` and `_adopt` already rebind whole mappings under `_cache_lock` rather than
  mutating in place.
  **Reasoning:** WI-004 closed the wrong-VALUE half and left the iterate-a-live-mapping half
  open by name (`docs/concurrent-access.md:8713-8714`) on the expectation that phones would
  leave the fuzzy path here. They do not, so this item owns it or nobody does.

- **Case:** an external dependency is unavailable — the live vault, a consumer repo, the
  network.
  **Decision:** nothing in the build touches any of them. The one empirical premise is settled
  by a committed artifact read as bytes, and AC-5's check makes no subprocess, network or vault
  call.
  **Reasoning:** the caged builder can reach none of them, so a builder-authored version of that
  artifact would be fabrication (the WI-024 and WI-022 precedents).

- **Case:** first run versus subsequent runs of the golden sweep.
  **Decision:** identical. Every run seeds a fresh temp vault from `roster.json`, replays the
  frozen ordered case list, and discards the vault. The committed fixture is never written.
  **Reasoning:** the sweep mutates (Branch C mints, pre-cut Branch B writes back); a sweep that
  mutated its own committed baseline would invalidate the golden on its first green run.

- **Case:** migration / backfill of existing data.
  **Decision:** none exists and none is needed. No frontmatter schema changes, no vault
  rewrite, no state migration. The only "migration" is the index the library builds in memory at
  load time.
  **Reasoning:** the cutover changes which in-memory map answers a lookup, not what a note
  contains. The write-boundary E.164 canonicalization that WOULD need a vault-wide migration is
  minted as a separate item (E3) precisely so it is not smuggled in here.

- **Case:** re-running the build, or re-running the suite.
  **Decision:** idempotent. The goldens are recorded once and committed; the recorder is never
  run again; every test derives its own temp vault.
  **Reasoning:** a second recording is the one way this oracle can be defeated, and D2's three
  tripwires make it RED rather than silent.

- **Case:** transient versus permanent failure inside a cut.
  **Decision:** there are no retries and none are wanted. Every operation is a local file write
  or an in-memory lookup; a failure is a defect, and the package's `LoudFailError` hierarchy
  already refuses rather than degrading.
  **Reasoning:** WI-020's loud-fail contract. A retry here would hide the only signal.

- **Case:** partial failure — a cut lands and a later cut does not.
  **Decision:** each cut is a commit, the goldens stand from Cut 0 to Cut 4, and the deletion is
  last. A build that stops after Cut 2 leaves a tree that is green, shippable, and still holds
  the duplicate.
  **Reasoning:** that is the whole reason for inverting the mint's order (E1). Reversibility is
  cut-by-cut, and the only irreversible step happens against two committed goldens.

- **Case:** error propagation to a caller.
  **Decision:** unchanged in every public surface. `get_by_email` still returns `Optional[Person]`
  and raises nothing — an `IdentifierError` from `Email.parse` is caught and becomes `None`,
  which is the same answer a miss has always produced. `find_or_create_stub` keeps its exception
  set exactly (`NameValidationError`, `WeakIdentityError`).
  **Reasoning:** three consumer repos catch on those shapes; widening or narrowing the exception
  set is a consumer break bought for nothing.

- **Case:** a trust-boundary crossing — untrusted input reaching the new parser.
  **Decision:** `get_by_email` now parses its argument. `Email.parse` refuses whitespace-bearing
  bare addresses rather than letting `parseaddr` silently repair them
  (`obsidian_schemas/identifier.py:Email:148-168`), and routes only genuine angle-bracket forms
  through `parseaddr`.
  **Reasoning:** that refusal is the WI-017 lesson already shipped at the write door; putting
  the read path on the same parser is the point of the cut, not a side effect of it.

**OPEN: None.**

## Implementation Plan

Tasks are ordered by dependency and each is independently verifiable. Tasks 2 and 3 are
independent of each other and may be done in either order; everything from Task 4 on is
strictly sequential, because the cut order IS the oracle's availability.

- [ ] **Task 1 — Capture the pre-build baseline.** Before the first edit, run the floor command
      and record in the Build Log: the pass/fail counts, and the value of
      `len(non_completed_write_sites(python_files_under(PACKAGE_ROOT)))` (expected 8, the number
      two standing walls pin). Both are informational anchors for the directional invariant; no
      later check asserts either number.
      verify: baseline — the numbers are recorded in the Build Log before any edit that could move them, and nothing asserts them afterwards

- [ ] **Task 2 — Add the three structural derivations to `tests/derivations.py`, each with its
      claimed match-shapes as planted fixtures.** Add `phone_index_iteration_sites`,
      `attribute_reads_in` and `docs_markdown_mentions` per D8. Write
      `tests/test_identity_endgame.py` (with `ensure_project_interpreter(__file__)` as its FIRST
      statement, per D9) carrying a shapes test that drives every claimed shape through the
      derivation's OWN predicate — never a re-implementation — over a scratch directory scanned
      by `python_files_under(plant_dir)`: for `phone_index_iteration_sites`, a `list(...)`-wrapped
      loop (matches, `materialized`), a bare `.items()` loop (matches, `live`) and a loop over an
      unrelated attribute (near-miss, not collected); for `attribute_reads_in`, a read of a named
      attribute inside a named function (matches), the same read in a DIFFERENT function
      (near-miss), and a read of an attribute not in the set (near-miss); for
      `docs_markdown_mentions`, a resolving `docs/company-name-corpus-audit.md` and a dangling
      `docs/does-not-exist.md` (both collected), and `orchestrator/docs/x.md`, a bare `Smith.md`
      and a wrapped tail `revised-2026-06-13.md` (all three near-misses that must NOT be
      collected). Import no `ast` anywhere outside `tests/derivations.py`.
      verify: test_identity_endgame_derivations_match_their_claimed_shapes

- [ ] **Task 3 — Author the frozen roster and the seeder.** Write
      `tests/fixtures/identity_endgame/roster.json` from D1's ten-row table verbatim, and
      `tests/identity_fixture.py` exposing `load_roster()`, `seed_vault(roster, dest)` (emitting
      every list element double-quoted so `" dana@example.com "` survives load) and
      `roster_digest()`. Add a test that re-derives both E8 invariants from `roster.json` rather
      than restating them: no two notes share a name token, and no two notes carry phones that
      `phones_match` unifies — the latter driven through the shipped `phones_match`, not a
      re-implementation. Assert `Tomas Villalobos` is the only note with `company:`, and that a
      seeded vault loads with `PersonRepository(vault).load() == 10` and a skip surface of 0.
      verify: test_identity_fixture_roster_is_complete_and_invariant_holding

- [ ] **Task 4 — Cut 0a: repair the parity legs so they compare two implementations again.**
      In `tests/test_resolve_or_create.py`, point the "legacy" leg of
      `test_engine_matches_legacy_return_value` and of `test_engine_matches_legacy_on_weak_identity`
      at `_find_or_create_stub_legacy` instead of `find_or_create_stub`. Both tests stay green;
      they are now differential rather than tautological. They are deleted at Task 11, which is
      why this task's verification cannot be a standing artifact: any test name it declared
      would stop resolving at the end of the build.
      verify: hand-run — the two repaired legs are run once here and are green; AC-1 deletes them at Task 11, so no standing artifact can carry this ordinal to the end of the build

- [ ] **Task 5 — Cut 0b: record both goldens against unchanged code.** Write
      `tests/record_identity_golden.py` (under `tests/`, never `scripts/` — see D3), which
      derives AC-1's twenty ordered cases and AC-4's thirty-nine deduplicated queries by D3's
      rules, executes them against a temp vault seeded from `roster.json`, and writes
      `stub_golden.json` and `resolve_golden.json` with `recorded_at: "cut-0"` and the roster
      digest. Run it ONCE, now, before any edit to `obsidian_schemas/`. Commit both files. Then
      write the tripwire test: the goldens' `roster_digest` matches the committed roster, both
      carry `recorded_at: "cut-0"`, the case and query lists re-derive identically from the
      roster, and the golden still holds the two exception rows' PRE-CUT values as literals
      spelled in the test's own source — `("kit@localhost", "Kit Baldwin")` and
      `(" dana@example.com ", None)`.
      verify: test_identity_goldens_are_frozen_pre_cut_data

- [ ] **Task 6 — Cut 1: give email resolution exactly one authority.** Apply D4 items 1–5 to
      `obsidian_schemas/repositories/person.py`. Write AC-2's check: the derived sweep over every
      `emails:` entry plus its lowercase, whitespace-padded and (where `Email.parse` succeeds)
      parsed-address variants; four surfaces agreeing on the note the roster declares owns the
      address, EXCEPT members whose stripped lowered form is an alias of a different person,
      where the declared asymmetry is asserted instead (three email-only doors → `Rosa Delgado`,
      `resolve` → `Alex Nkemdirim`); `kit@localhost` resolving to nobody by all three string
      surfaces with surface 4 asserted as a refusal; and the structural clause that the string
      `_email_index` (built from parts in the test's own source, never spelled whole) appears at
      zero sites under `python_files_under(PACKAGE_ROOT)`.
      verify: test_email_has_exactly_one_resolution_authority

- [ ] **Task 7 — Cut 1b: re-home the two leniency tests the cutover falsifies.** Rewrite
      `tests/test_identity_index.py`'s `test_malformed_email_skipped_but_legacy_indexes_it` and
      `test_clean_and_junk_in_one_list_indexes_only_the_clean` to assert the post-cutover
      property per D4: a note carrying `not-an-email` (and one carrying `bad email` beside a good
      address) loads without raising, contributes no identifier for the junk, and resolves
      through NO door — with the audit's 0-of-1021 cited in the test as the warrant for the loss.
      Remove every remaining reference to the deleted attribute from `tests/`.
      verify: test_malformed_email_resolves_nowhere_after_cutover

- [ ] **Task 8 — Cut 2: the phone carve-out, made executable and concurrency-safe.** Materialize
      `get_by_phone`'s fuzzy scan (`list(self._phone_index.items())`) and add the comment naming
      the non-transitivity and citing the witness by name. Write AC-3's check: the three
      `phones_match` results against the shipped function; `Phone.parse` accepting all three
      forms and yielding three DISTINCT `.key` values; `get_by_phone("44790055852")` and
      `get_by_phone("0790055852")` returning `Priya Raman` while `get_by_phone("10790055852")`
      returns `None` against a vault seeded from `roster.json`; and the structural clause via
      `phone_index_iteration_sites` that every `_phone_index` loop in the package is
      `materialized` (with the non-vacuity assertion that at least one site exists).
      verify: test_phones_stay_on_the_fuzzy_path_and_the_reason_is_executable

- [ ] **Task 9 — Cut 3: one cascade behind one named selection policy.** Add
      `_RESOLVE_CASCADE_ORDER` and the module-level `select_resolution(query, candidates)` per
      D6, and rewrite `resolve()` as the empty guard plus `resolve_all` plus the policy. Write
      AC-4's check: the structural clause (`resolve` calls `resolve_all` and `select_resolution`;
      `attribute_reads_in` over `PersonRepository.resolve` for `_cache`, `_alias_index`,
      `_email_index`, `_phone_index` is empty; `select_resolution` is a module-level function of
      `obsidian_schemas.repositories.person`), the golden replay over all thirty-nine queries
      with the two-row exception list as literals each asserted to land on its DECLARED post-cut
      answer, and the four hand-stated discriminants plus `resolve("sandy")` against the same
      single seeded vault.
      verify: test_resolve_is_one_cascade_and_matches_the_pre_cut_golden

- [ ] **Task 10 — Riders and the documentation-truth repairs.** Apply D7's four rider edits to
      `obsidian_schemas/repositories/person.py`: delete the dangling
      `docs/paren-decoration-at-the-door.md` reference at `:113`; give the slack carve-out its
      `UNBLOCK:` line; repair the false step-6 comment at `:615-617`; and replace the
      three-month-old zero-failures claim at `:236-238` with a pointer to the audit artifact.
      Write AC-5's check: the audit artifact's SHAPE (the literal command, verbatim stdout, the
      `type: person` count, an explicit no-matches marker rather than an absent field per class,
      the two divergence-class counts, the cross-note phone-pair count, and a 40-hex SHA per
      consumer repo), with no subprocess, network or vault call; plus zero sites for
      `paren-decoration-at-the-door`, every `docs_markdown_mentions` hit over
      `python_files_under(PACKAGE_ROOT)` resolving to an existing file, the `UNBLOCK:` marker
      present with non-empty text, and no source comment asserting that step 6 is filtered out
      absent a company hint.
      verify: test_identity_cutover_docs_are_complete_and_truthful

- [ ] **Task 11 — Cut 4: delete the duplicate and both of its consumers.** Delete
      `_find_or_create_stub_legacy` and the prose mention at `:675`; repair the stale Phase-5
      replay claim at `:685` to point at the committed goldens; delete the six parity cases in
      `tests/test_resolve_or_create.py` repaired at Task 4 and `test_legacy_preserves_rich_note`
      in `tests/test_wi126_body_preservation.py`, leaving `test_engine_preserves_rich_note`
      standing. Write AC-1's check: a literal-text scan over every file
      `python_files_under(PACKAGE_ROOT, TESTS_ROOT)` returns, with the needle assembled from
      parts in the check's own source so the check is not its own counterexample; the both-legs
      clause (no test's two legs both reach `resolve_or_create`); and the golden replay of all
      twenty ordered cases with every `(resolved_name, created_new)` pair matching and the
      committed fixture's bytes unchanged by the run.
      verify: test_legacy_stub_is_gone_and_the_golden_is_the_oracle

- [ ] **Task 12 — Prove the stale-claim repair separately from AC-5.** AC-5's check owns three
      documentation-truth repairs; the Phase-5 replay claim at `:685` is a fourth that the
      data-premise gate surfaced after the criteria were frozen. Assert it directly: no file
      under `python_files_under(PACKAGE_ROOT)` claims a replay confirms zero divergence over the
      real vault, and the surviving text points at the committed goldens.
      verify: test_no_source_claims_a_runnable_phase5_replay

- [ ] **Task 13 — Close wall membership by RUNNING each wall's own predicate.** Enumerate the
      files this item created or edited, assert each exists, and run every predicate in D10's
      table on their final text, asserting each wall's own requirement. Anything the run returns
      that D10 did not name is recorded in the Build Log and satisfied — never worked around, and
      never satisfied by narrowing a wall.
      verify: test_identity_endgame_wall_membership_is_closed

- [ ] **Task 14 — Prove this item's checks survive the conveyor's interpreter.** Generalize
      `tests/test_ac_interpreter.py` from a single `WORK_ITEM_DOC` to a tuple of documents,
      iterated, adding `docs/identity-engine-endgame.md`; update its `CORPUS_COUPLING`
      declaration to name both. The wall then discovers this item's five `check:` names from its
      own `criteria` fences, resolves each to its unique module, and runs it under `-S` — which
      is what proves `ensure_project_interpreter` is wired, not merely present. Record the
      resulting floor wall-clock in the Build Log.
      verify: test_every_acceptance_criterion_passes_under_the_conveyors_interpreter

- [ ] **Task 15 — Full floor, green, with the directional invariant satisfied.** Run the floor
      command against the worktree. Case count must be no lower than Task 1's baseline except by
      the seven cases this item deliberately removes (six parity cases plus the WI-126 legacy
      twin), which the Build Log names explicitly against the baseline.
      verify: hand-run — the floor command's own output is the artifact; the count is compared against Task 1's Build Log baseline by hand, and every standing check that proves a property of this item is already named as another task's verify

## Write Targets

```writes
kind: precondition
path: docs/identity-cutover-corpus-audit.md
grounds: whether the unified index resolves every email the legacy per-kind dicts resolve on the live vault today
why: AC-2 asks for ONE email authority, and E2 shows the two candidate authorities disagree on a class that only the live corpus can size — entries `Email.parse` refuses, which are in `_email_index` (person.py:197 indexes any non-empty string) and absent from `_identifier_index` (person.py:246-252 skips them). The only claim on record is a 2026-06-13 line in a docstring, "audited against the live vault (942 notes): email/phone/whatsapp/linkedin parse with ZERO failures" (person.py:236-238) — three months old, about a vault that has been written to daily since, and it is the WI-144 shape exactly: a confident reading standing in for a run. E2's decision rule is stated in advance so this artifact is decision-forcing rather than decorative: zero refusals means cut over and delete `_email_index`; any refusals means the carve-out arm and a repair rule routed to WI-026. Shape contract: (a) the literal walk command with verbatim stdout and the count of `type: person` notes scanned; (b) every `emails:` entry `Email.parse` refuses, quoted with its note and the refusal reason, or an explicit "no matches" marker — never an absent field; (c) every entry where `raw.lower()` differs from `Email.parse(raw).value`, split into the whitespace and angle-bracket classes of E2(b)/(c), with counts; (d) the count of `phones:`/`whatsapp:` value PAIRS on DIFFERENT notes that `phones_match` unifies but `Phone.key` does not — the live size of the fuzzy arm AC-3 preserves, and the number that would tell us if the arm is in fact dead; (e) the 40-hex HEAD SHA of each consumer repo scanned. The caged builder can reach neither the live vault nor the consumer repos, so a builder-authored version of this file would be fabrication (the WI-024 precedent, `docs/wi-024-consumer-audit.md`; the WI-022 precedent, `docs/company-name-corpus-audit.md`). It is declared HERE, at exploring, because it settles a premise the criteria are ABOUT: a nonzero result edits one clause of a draft AC now, or costs a D4b re-sign and a second interruption of Dave later (the WI-281 shape).
```

*The fence above is the ideation-authored grounding precondition and is unchanged. The builder
write targets below extend the section; nothing above them is rewritten.*

```writes
path: obsidian_schemas/repositories/person.py
why: Tasks 6, 8, 9, 10, 11 — the email cutover (delete `_email_index`, re-home `get_by_email` onto `_identifier_index`, re-point `resolve` step 3 and `resolve_all` step 2), the phone snapshot + carve-out comment, `select_resolution` + the rewritten `resolve`, the four rider repairs, and the deletion of `_find_or_create_stub_legacy` and its docstring mention.
```

```writes
path: tests/derivations.py
why: Task 2 — the three new structural predicates (`phone_index_iteration_sites`, `attribute_reads_in`, `docs_markdown_mentions`). They land HERE and nowhere else because `ast` is single-homed by two standing set-equality walls.
```

```writes
path: tests/identity_fixture.py
why: Task 3 — `load_roster` / `seed_vault` / `roster_digest`. Under `tests/` rather than `scripts/` because it writes notes with `Path.write_text`, which `tests/test_write_routing.py` forbids anywhere under `obsidian_schemas/` or `scripts/`.
```

```writes
path: tests/fixtures/identity_endgame/roster.json
why: Task 3 — the frozen ten-note roster declaration, byte-frozen data, the fixture both goldens are digest-bound to.
```

```writes
path: tests/record_identity_golden.py
why: Task 5 — the one-shot Cut-0 recorder. Under `tests/` for the same write-routing reason as the seeder; never a `test_*.py`, so pytest does not collect it, and never run again after Cut 0.
```

```writes
path: tests/fixtures/identity_endgame/stub_golden.json
why: Task 5 — AC-1's oracle: the twenty ordered cases and the `(resolved_name, created_new)` pair each returned against unchanged code.
```

```writes
path: tests/fixtures/identity_endgame/resolve_golden.json
why: Task 5 — AC-4's oracle: the thirty-nine deduplicated queries and `resolve()`'s pre-cut answer to each.
```

```writes
path: tests/test_identity_endgame.py
why: Tasks 2, 3, 5, 6, 8, 9, 10, 11, 12, 13 — all five acceptance checks plus the derivation-shapes, roster-invariant, golden-tripwire, stale-claim and wall-membership tests. Calls `ensure_project_interpreter(__file__)` as its first statement.
```

```writes
path: tests/test_resolve_or_create.py
why: Tasks 4 and 11 — repair the two parity legs to compare two implementations again, then delete the six cases at Cut 4 per AC-1.
```

```writes
path: tests/test_wi126_body_preservation.py
why: Task 11 — delete `test_legacy_preserves_rich_note`, leaving `test_engine_preserves_rich_note` to carry the WI-126 property alone.
```

```writes
path: tests/test_identity_index.py
why: Task 7 — the two leniency cases pin the very divergence Cut 1 ends (`assert "not-an-email" in repo._email_index`); they are re-homed onto the post-cutover property with the audit's 0-of-1021 as the warrant, not deleted.
```

```writes
path: tests/test_ac_interpreter.py
why: Task 14 — generalize `WORK_ITEM_DOC` to a tuple and add this item's doc, so the standing foreign-interpreter wall proves this item's five checks rather than a second copy of it being written.
```

## Verification

**Happy path (smoke).** Seed a vault from `roster.json`, then: `get_by_email`, `resolve`,
`resolve_all` and `_resolve_identifier(Email.parse(...))` all return `Jane Roe` for
`jane.roe@example.com` and for `Jane Roe <jane.roe@example.com>`; `resolve("pat@example.com")`
returns `Alex Nkemdirim` while the three email-only doors return `Rosa Delgado`;
`resolve("sandy")` returns `Sandy Forster`; `find_or_create_stub("Tomas", company="Kestrel
Analytics")` returns `(Tomas Villalobos, False)`.

**Failure modes that must fail gracefully.** `get_by_email` on a string `Email.parse` refuses
returns `None` rather than raising. `resolve` on an empty, `None` or whitespace-only query
returns `None`. `get_by_phone` on a query normalizing to fewer than seven digits returns `None`
before touching the index. A malformed `emails:` entry still loads its note without raising and
is still reported nowhere as a skip, because the note itself parsed.

**Failure modes that must fail LOUDLY.** A golden whose `roster_digest` no longer matches the
committed roster; a golden regenerated after any cut (caught by the two pre-cut exception rows
held as literals in the check's own source); a `for` loop over `_phone_index` that is not
materialized; `resolve` reading any of the four indexes directly; a `docs/`-relative markdown
pointer in `obsidian_schemas/` that does not resolve; the audit artifact missing a section, a
field, or carrying a stated count with no listing behind it.

**Counting walls ship their claimed match-shapes as fixtures (WI-235).** Three of this item's
oracles are counts of structural matches — zero sites for `_find_or_create_stub_legacy`, zero
sites for `_email_index` under `PACKAGE_ROOT`, zero non-materialized `_phone_index` loops, zero
unresolving `docs/` mentions, zero direct index reads in `resolve`. `matches == 0` is satisfied
identically by a predicate that resolves every claimed shape and by one that resolves almost
none, so Task 2 drives every claimed shape AND a near-miss through each predicate's own
function — the same function the live sweep calls, never a re-implementation — as green
fixtures on every floor run. The near-misses are named in Task 2 and are the load-bearing half:
without `orchestrator/docs/x.md` and a bare `Smith.md` as asserted non-matches, the docs scan
could pass by matching everything and later be narrowed back with nothing checking that the
narrowing kept the claimed shapes.

**Non-vacuity.** Every zero-count assertion is paired with a positive one: at least one
`_phone_index` iteration site exists; the docs scan returns a non-empty set of in-scope
mentions; the golden's derived case and query lists are non-empty and re-derive to the same
ordinals.

**Integration — downstream consumers that must still work.** `find_or_create_stub`'s signature,
return shape and exception set are unchanged, which is what orchestrator's
`contact_normalizer.py` calls directly and HAL9000's `entities.py` calls over HTTP. The
`normalize_phone` / `phones_match` compat re-export at
`obsidian_schemas/repositories/person.py:78-85` is untouched, and it is load-bearing in HAL9000
`core/contact_resolver.py:13` and exocortex `clients/contacts.py:13`. The corpus audit's clause
(e) records that no consumer code outside this repo reads `_email_index` at all — HAL9000's two
hits are a test wall naming the reaches as forbidden and a docstring, exocortex and orchestrator
have none — so the deletion is repo-local, against HEAD SHAs recorded in the artifact for
re-checking at build start.

**Regression — the enumeration is DERIVED from the edited surfaces, not inherited.** Sweeping
`tests/` for modules naming `resolve(`, `resolve_all(`, `find_or_create_stub`, `get_by_phone(`
or `resolve_or_create(` returns eleven files; reading each at file granularity discards four as
`Path.resolve()` or scan plumbing (`tests/derivations.py`, `tests/ac_interpreter.py`,
`tests/test_ac_interpreter.py`, `tests/test_vault_path_required.py`) and leaves the modules that
actually assert on the surfaces this item edits: **`tests/test_repositories.py`** (75 sites — the
`resolve` cascade battery, including the substring-rejection promises
`test_resolve_rejects_substring_andy` and `test_resolve_rejects_substring_ed` at `:385-395`
that AC-4 discriminant (iii) restates, and the `get_by_email` / `get_by_phone` /
`update_fields`-reindex cases), **`tests/test_resolve_or_create.py`** (17), **`tests/test_wi126_body_preservation.py`** (4),
**`tests/test_identity_index.py`**, **`tests/test_concurrent_access.py`**,
**`tests/test_name_validation.py`** and **`tests/test_company_name_contract.py`**. All must be
green at every task boundary; two of them are edited deliberately (Tasks 4/7/11) and no other
may change.

**The floor, and the directional invariant.** The floor command is the pipeline's test floor —
hermetic, and it must stay so: no test this item writes may reach the live vault or read
`OBSIDIAN_VAULT_PATH`. The case count is compared against Task 1's recorded baseline as a
PROPERTY, not against a number written here: green, with the only permitted decrease being the
seven cases this item deliberately removes, each named in the Build Log.

**Close-out, run OUTSIDE the cage by the conductor, before the ship.** Re-run the literal
command recorded in `docs/identity-cutover-corpus-audit.md` against the live vault and confirm
clause (b) is still 0. That is the one verification the cage cannot perform — it has neither the
vault nor the consumer repos — and it is the rot direction that matters: a single newly-written
malformed `emails:` entry flips the arm. Redact nothing sensitive into a tracked document; only
the counts are recorded.

## Verified Diagnosis

Five load-bearing claims about how the current system behaves incorrectly. Each cites a
falsifiable artifact; if any were false the corresponding work would be invalid.

1. **The in-tree parity harness is vacuous.** `tests/test_resolve_or_create.py:198` calls
   `find_or_create_stub`, which since the Phase-4 adapter swap is
   `parse_identifiers(...) + self.resolve_or_create(...) + self._hydrate(...)`
   (`obsidian_schemas/repositories/person.py:find_or_create_stub:688-697`); `:204-209` is the
   same three calls with the same arguments. Both legs are one computation, so the six cases at
   `:189-211` and `:214-224` cannot fail for any change to either path. Falsifiable by reading
   those two spans side by side; independently re-executed by four architect rounds.

2. **The comment on `resolve_all` step 6 asserts the opposite of what the code does.**
   `obsidian_schemas/repositories/person.py:resolve_all:615-617` says the short-form match
   "stays low confidence (< 0.5) and gets filtered out below". It records `0.6` at `:626` and
   the floor is `>= 0.5` at `:654`. Falsifiable by two line reads; the branch is live, and its
   apparent inertness is why E4's third divergence class went unnamed through a full round of
   review.

3. **`get_by_phone` iterates a live mapping while another method mutates it in place.**
   `:417` iterates `self._phone_index.items()`; `_clear_indexes:326-333` calls `.clear()` on
   that same dict. `docs/concurrent-access.md:8713-8714` records this half as explicitly NOT
   closed by WI-004.

4. **A package comment points at a file that does not exist.**
   `obsidian_schemas/repositories/person.py:113` names `docs/paren-decoration-at-the-door.md`;
   there is no such file under `docs/`. Exactly one site in the tree.

5. **Two docstring claims in `person.py` are empirically false today.** `:236-238` asserts an
   audit "against the live vault (942 notes, 2026-06-13)" — the vault now holds 1147 `type:
   person` notes (`docs/identity-cutover-corpus-audit.md`, clause (a)), so the reading is 205
   notes stale. `:685` asserts "The Phase-5 replay confirms zero return-value divergence over
   the real vault" — that replay is `orchestrator/state/identity-parity.json`, in another repo,
   produced before WI-020 and WI-021, and there is no runnable replay harness anywhere in this
   tree (`scripts/` holds `lint_vault.py` and `migrate_person_to_discuss.py` only).

Not load-bearing and therefore not asserted here: that the duplicate costs maintenance effort.
It does, but the item's justification rests on the five claims above, not on that.

## Scope Boundary

**What we are NOT doing.**

- **Write-boundary phone canonicalization (E.164 at the `name_gate`).** E3 shows the fuzzy arm
  is a read-time reconstruction of information `normalize_phone` destroys at the write door
  (`obsidian_schemas/phone_normalization.py:normalize_phone:52-55` strips the `+`), and that
  fixing the seam is what would eventually make phones keyable. It needs a region policy, a
  vault-wide migration of existing `phones:` values, and coordination across three repos.
  Minted as a follow-on with E3 as its motivation; not started here.
- **A `lint_vault` repair rule for unparseable email entries.** WI-026's territory. The corpus
  audit returned 0 refusals so no rule is owed today; if a future re-run returns nonzero, it is
  routed there, not grown into this item.
- **Collapsing the remaining per-kind dicts into views of `_identifier_index`.** E5 shows the
  ceiling: there is no `Alias` identifier type at all, and `slack` is unprojectable until
  frontmatter carries a workspace. This item gives that carve-out an `UNBLOCK:` condition and
  stops there. `_alias_index`, `_phone_index` and `_slack_index` all survive.
- **The other three repositories' `resolve()`** — `company.py:96`, `meeting.py:345`,
  `book.py:231` each carry their own cascade. Only Person has a `resolve_all` to consolidate
  against; consolidating Person's pair obliges none of them.
- **`person.py` decomposition.** WI-025 is gated on this item precisely so the duplicate is
  deleted before the pure move. Deleting 126 lines is in scope; moving what remains is not.
- **Re-homing anything onto WI-016's fixture vault.** E6 arm (b): this item's oracle is
  permanently homed to its own `tests/`-local fixture. When WI-016 lands, neither imports the
  other.
- **Changing `resolve_all`'s output ordering.** E8 rejected reordering alias before email: the
  ordering at `:571-572` is commented deliberate and two consumer repos rank on that output.
  The inversion `resolve` needs lives in the selection policy, on `resolve`'s side of the seam.

**Unchanged files the builder must not touch.** `obsidian_schemas/identifier.py`,
`obsidian_schemas/name_gate.py`, `obsidian_schemas/name_validation.py`,
`obsidian_schemas/name_cleaning.py`, `obsidian_schemas/phone_normalization.py`,
`obsidian_schemas/models.py`, `obsidian_schemas/parser.py`, `obsidian_schemas/writer.py`,
`obsidian_schemas/vault_io.py`, `obsidian_schemas/repositories/base.py`,
`obsidian_schemas/repositories/company.py`, `obsidian_schemas/repositories/meeting.py`,
`obsidian_schemas/repositories/book.py`, everything under `scripts/`, and every test module not
named in `## Write Targets`. In particular: the compat re-export block at
`obsidian_schemas/repositories/person.py:78-85` stays exactly as it is — it looks like tidy-up
bait during a decomposition and it is load-bearing in two consumer repos.

## Risk Analysis

**R1 — the cutover loses a live lookup.** *What could go wrong:* an `emails:` entry that
`Email.parse` refuses stops resolving. *Likelihood:* measured, not guessed — 0 of 1021 live
entries today. *Impact:* a contact silently fails to resolve and a duplicate note is minted.
*Mitigation:* the arm is selected by a committed artifact rather than by a build-time judgement
call; the conductor re-runs its literal command as a close-out before the ship; the loss class
is pinned as a test with the number cited beside it. *Rollback:* Cut 1 is one commit.

**R2 — the consolidated `resolve()` widens.** *What could go wrong:* `resolve` starts claiming
matches it declines today, which mints wrong-person resolutions in HAL9000's contact cascade —
the exact class WI-019 and WI-103 were opened to stop. *Likelihood:* high for the obvious
implementation; a literal thin head gets three of AC-4's four discriminants wrong, and sorting
by confidence inverts two of them. *Impact:* the worst in the item. *Mitigation:* a golden
recorded before any cut over a query space derived from the fixture, plus four discriminants
hand-stated in prose because the derived space provably cannot reach three of them, plus a
policy whose two arms are forced by the code's own structure (D6) rather than tuned until the
tests pass. Cut 3 is allowed no exceptions of its own.

**R3 — the oracle is defeated by regeneration.** *What could go wrong:* the build hits a golden
diff after Cut 1 and re-records the golden, which then ratifies whatever the cut did.
*Likelihood:* this is the cheapest repair a build reaches for, so: high without a wall.
*Impact:* the item ships with no evidence and reads as though it shipped with the best evidence
in the backlog. *Mitigation:* D2's three tripwires, of which the second cannot be reached by
regeneration at all — the two exception rows' pre-cut values are literals in the check's own
source and in this document's prose.

**R4 — the criteria pass under the floor and fail under the conveyor's interpreter.** *What
could go wrong:* four of five checks import the package, the battery's interpreter has no
pydantic, and all five report `ModuleNotFoundError`. *Likelihood:* certain without the bridge —
this is WI-021's shipped scar, five-of-five criteria red with a green floor in the same tree.
*Impact:* a build-exit round bought for nothing. *Mitigation:* `ensure_project_interpreter` as
the check module's first statement, proved by EXECUTION through the standing wall
(`tests/test_ac_interpreter.py`) rather than asserted by construction.

**R5 — the golden is flaky on a machine that enumerates the fixture differently.** *What could
go wrong:* `_cache` insertion order is the filesystem walk
(`obsidian_schemas/repositories/base.py:load:231` globs unsorted), `resolve` step 5 returns the
FIRST cache entry containing the token, and `get_by_phone`'s fuzzy scan returns the FIRST
unifying entry. *Likelihood:* certain if the fixture shares a name token or a unifiable phone.
*Impact:* a red that grades the machine, not the code. *Mitigation:* both E8 invariants are
re-derived from `roster.json` at test time rather than restated, so a roster edit that breaks
either is RED; and AC-1's case order is frozen data, never re-derived from a walk.

**R6 — the floor gets slower.** *What could go wrong:* Task 14 adds five `-S` subprocesses per
floor run, each re-execing into a one-node pytest, to a floor CLAUDE.md describes as ~1s.
*Likelihood:* certain; it is the cost of the mitigation, not a failure. *Impact:* a slower
inner loop for everyone. *Mitigation:* it is the one wall that can catch R4, and generalizing
the existing module beats writing a second one. The measured cost is recorded in the Build Log
so the next person deciding whether to keep it has the number rather than an impression.

**Migration path.** There is none to manage: no frontmatter changes, no persisted state, no
consumer signature moves. The transition is four commits in one item, each green, with the
oracle standing from the first to the last and the only irreversible step — the deletion —
happening last against two committed goldens.

## Acceptance Criteria

Draft — originated cold-start, approval-only mode, re-derived from the frozen `## Intent`. **Not yet frozen:** the `ac-signoff` fence is written by `bin/review-spec-helper.py` only after Dave's review, never by hand. Every `check` is a top-level zero-argument `def test_*(` in `tests/` that signals failure by raising.

```criteria
id: AC-1
desc: The duplicate is gone and a REAL oracle outlives it. `_find_or_create_stub_legacy` appears at zero sites across `obsidian_schemas/` and `tests/` — asserted as a LITERAL-STRING scan over the source TEXT of every file `tests/derivations.py:python_files_under` returns for those two roots, so that the 126-line `def` itself, every caller, and any comment or string mention are all in the scan's reach; never as a check against person.py:699 by line, and explicitly NOT via `functions_calling`. Both of the duplicate's consumers go with it, named: the vacuous parity cases at `tests/test_resolve_or_create.py:189-211` and `:214-224`, and `test_legacy_preserves_rich_note` at `tests/test_wi126_body_preservation.py:209-215`, whose engine twin at `:200-207` is left standing to carry the WI-126 body-preservation property alone. And no test's two legs both reach `resolve_or_create`, which is the tautology those six cases are in today. In its place a committed golden file records, for every case in a derived case set, the `(resolved_name, created_new)` pair `find_or_create_stub` returns; a test re-runs the identical cases against a fixture vault seeded from the golden's own declaration and asserts every pair matches. The case set is DERIVED from the fixture vault rather than hand-picked — that vault being E8's **ten-note roster, complete and cited rather than re-derived** — and the derivation is stated per branch, so the coverage claim is CONSTRUCTED rather than asserted: for every note, one case per `emails:` entry (`name=<the note's name>, email=<the entry>` → Branch A, email hit); one case per `phones:` entry (`name=<the note's name>, phone=<the entry>` → Branch A, phone hit — reachable only because `Priya Raman` and `Tomas Villalobos` carry `phones:`, which no note on the earlier eight-note roster did); one case for every note carrying a `company:`, pairing that note's FIRST name token with that company and NO identifiers (→ Branch B, name+company reuse: 0.6 `partial-name` at person.py:610-612 plus the 0.25 company bump at :635-651 is exactly the 0.85 default threshold tested at :920, and `Tomas Villalobos` is the note that supplies it); and one not-present variant of each (→ Branch C, create). A note added to the fixture joins the sweep automatically, and a note carrying no phone or no company contributes no case to those arms — which is why branch coverage is guaranteed by the ROSTER, not by the sweep, and why the roster is fixed as literals in E8 rather than left to the build. Two constraints on the derivation, because either one silently weakens the sweep while it still reads as total: a not-present PHONE is not-present under `phones_match`, never merely under string equality (E8 invariant 2 — `10790055852` reads like a fresh number and is one `phones_match` arm away from `0790055852`), and a not-present NAME is MULTI-TOKEN, because a single-token name with no email and no phone hits the weak-identity guard at `name_validation.py:385-387` and raises `WeakIdentityError` instead of reaching `create_stub`. And because Branch C cases WRITE, the golden freezes the ORDERED case list as data and the test replays it in that order: a case order re-derived from a filesystem walk at test time is machine-dependent, and every note a create case mints is visible to every later case in the same run. The golden is DATA in the repository, not a value recomputed at test time from the code under test.
why: This is the item's safety net and the reason the deletion is safe rather than merely tidy (E1). The zero-sites clause is the deletion; the golden clause is what stops the deletion from being a net loss of evidence. The mechanism is spelled out because the obvious cite was wrong in a way that would have shipped this item's own defect class inside this item's own deletion criterion: `tests/derivations.py:871-885` `functions_calling(files, name)` returns "every function whose OWN body calls `name`", so deleting the two callers while leaving the 126-line `def _find_or_create_stub_legacy` in place returns the EMPTY SET and the zero-sites clause goes green with the duplicate still shipped. `derivations.py` exposes no public definition-scan (`_iter_functions` is private), and a literal-text scan is total here — it sees the `def`, which is the thing being asserted absent. Naming both consumers is likewise deliberate: one is scaffolding, but `test_legacy_preserves_rich_note` is a real passing test, and a criterion that forces a real test's deletion should say so out loud rather than let a build discover it. The both-legs clause is the specific defect found in the tree: six cases that read as the Phase-5 parity contract compare `parse_identifiers` + `resolve_or_create` against `parse_identifiers` + `resolve_or_create` and cannot fail for any change to either, because the Phase-4 adapter swap turned `find_or_create_stub` into the engine underneath them. Asserting the ABSENCE of that shape is what stops a build from "repairing" the harness by renaming it. Data-not-recomputation is the whole point: a golden regenerated from the post-cut code agrees with any implementation, which is the one way this oracle can be defeated. The per-branch derivation is spelled out for the same reason the mechanism is: "by construction" was a CLAIM about a fixture, and against the roster this document actually pinned it was false — the eight notes carried no `phones:` field and no `company:` field, so Branch A's phone arm had nothing to hit and Branch B's corroboration arm was unreachable, and a build taking both texts at their word would have shipped a sweep silently missing two of the four branches it names while this criterion read as though they were covered. Coverage lives in the roster, so the roster is where it is fixed (E8, now ten notes); naming the branch each derived case ENTERS, with the arithmetic for the one that is not obvious, is what makes the claim checkable by reading rather than by building. The two derivation constraints and the ordered-replay clause are cheap here and expensive later: a phone "variant" that `phones_match` unifies turns a create case into a resolve case and the golden records the wrong branch as though it were right; a single-token not-present name raises `WeakIdentityError` where the case expects a create; and a sweep whose case ORDER comes from a filesystem walk is a golden that passes on the machine that recorded it.
check: test_legacy_stub_is_gone_and_the_golden_is_the_oracle
kind: test
```

```criteria
id: AC-2
desc: Email resolution has exactly ONE authority, whichever arm the corpus audit selects. Over a sweep DERIVED from the fixture vault — every `emails:` entry on every note, plus a lowercase variant, a leading/trailing-whitespace variant, and (only where `Email.parse` succeeds on the entry) its parsed-address variant, which is the query that makes E2 class (b)'s gain visible: `jane.roe@example.com` is not itself an entry and so is not in AC-4's derived space — all four email-resolving surfaces return the SAME person for the SAME input: `get_by_email`, `resolve`, `resolve_all` (highest-ranked candidate), and `_resolve_identifier(Email.parse(...))`. The correctness oracle is the note the address is actually on, declared by the fixture, not agreement-among-surfaces: a build in which all four consistently return the WRONG person is RED. THE AGREEMENT PROPERTY IS SCOPED to inputs that are not ALSO an alias of a different person, and the excluded case is not dropped — it is pinned as the DECLARED, PERMANENT ASYMMETRY E8 settles: for the planted pair (`Alex Nkemdirim` carrying `aliases: ["pat@example.com"]`, `Rosa Delgado` carrying `emails: ["pat@example.com"]`) the three email-only doors — `get_by_email`, `resolve_all` highest-ranked, `_resolve_identifier` — return **Rosa Delgado**, and `resolve` returns **Alex Nkemdirim**, because `resolve` is a cascade over four indexes and its alias step (person.py:488) precedes its email step (:493). Both halves are asserted; a build in which `resolve` returns Rosa is RED, and so is one in which any of the other three returns Alex. THREE further members are PLANTED, as the exact literals E7 fixes — this is not the spec-writer's choice, because which literal lands decides whether this criterion and AC-4 are jointly satisfiable: `Jane Roe` carrying `"Jane Roe <jane.roe@example.com>"` (E2 class b), `Kit Baldwin` carrying `"kit@localhost"` (class a, refused by `Email.parse` as `malformed local@domain`, and containing `@` so it reaches `resolve` step 3), and `Dana Okafor` carrying the YAML-quoted `" dana@example.com "` (class c). Every other fixture note's entries are well-formed, lowercase, whitespace-free and unique. For the refused entry the criterion asserts the DECLARED arm rather than inventing an answer — under the cutover arm `kit@localhost` resolves to nobody by all three string surfaces, under the carve-out arm it resolves to Kit Baldwin by all three — and surface 4 is NOT APPLICABLE to it under either arm, since `Email.parse` refuses it and there is no typed `Email` to hand over; the criterion asserts that refusal instead. Under the carve-out arm the surviving authority must resolve a SUPERSET of what pre-cut `_email_index` resolved — every raw entry by its lowered literal AND, where `Email.parse` succeeds, by the parsed address — which is what makes surface 4 agree with the three string doors on `Jane Roe <jane.roe@example.com>` instead of missing it. Structurally: `_email_index` is either absent from the tracked sources entirely, or present with a module-level comment carrying the audit's refusal count; the two-authority state, where `get_by_email` reads one mapping and `_resolve_identifier` reads another, is RED under both arms.
why: "An identifier index that is actually the resolution authority (or documentedly not, per kind)" is half the Intent, and the failure mode is not choosing wrong — it is shipping BOTH, which is the state today (person.py:955-956 delegates `Email` to `get_by_email` while `_identifier_index` holds the same fact). Writing the criterion on the arm-agnostic property lets the corpus audit decide the arm without re-signing the AC. The derived sweep proves membership only, so the oracle is the fixture's own declaration of who owns each address — a stub returning the first person for every query sweeps every member and is RED on the planted notes. The plants are E2's three divergence classes, planted rather than sampled precisely because a fixture built from clean addresses cannot distinguish the two authorities at all: on well-formed input they agree, which is what has let the duplicate survive this long. They are stated as LITERALS because leaving the refused string unconstrained made this criterion and AC-4 jointly unsatisfiable for some choices and vacuous for others — `"not-an-email"` moves nothing (`resolve` step 3 is gated on `@`), `"kit@localhost"` moves `resolve()`'s answer, and only the second is worth planting; E7's table hand-executes the consequence for both arms and closes AC-4's exception list over exactly these rows. The surface-4 carve-outs are stated for the same reason: a typed door cannot be handed an input its parser refuses, and pretending otherwise would have made the carve-out arm unbuildable on the angle-bracket plant. The alias scope is the second such statement, and the bigger one: an unqualified four-door agreement claim is STRONGER than the Intent's "one authority per kind" and it directly contradicted AC-4 discriminant (ii), which requires the alias owner — the address is one of the email owner's `emails:` entries, so it is in this sweep, and the four doors hand-execute to Rosa/Alex/Rosa/Rosa (E8's table). "One authority for EMAIL" was never "one answer from RESOLVE for any string containing @": `resolve` is a cascade over four indexes, an alias is a name variant with no `Identifier` type (E5), and Cut 1 re-homes which lookup the email step consults, never where that step sits. Asserting the asymmetry beats carving the input out of the sweep, because an unpinned asymmetry is exactly what a "tidy the cascades" refactor deletes by accident — and Cut 3 is that refactor.
check: test_email_has_exactly_one_resolution_authority
kind: test
```

```criteria
id: AC-3
desc: The phone carve-out is PROVEN, not asserted, and its concurrency rider is closed. A test executes the non-transitivity witness against the shipped `phones_match`: `phones_match("0790055852", "44790055852")` and `phones_match("0790055852", "10790055852")` are both True while `phones_match("44790055852", "10790055852")` is False, and `Phone.parse` accepts all three and yields three DISTINCT `.key` values — which together are the proof that no key function for this relation exists and therefore that keying phones into `_identifier_index` is unavailable rather than merely unchosen. The same test asserts the behaviour the carve-out preserves, on a fixture note whose phone is fixed HERE as a literal rather than left to the build — `Priya Raman`, carrying `phones: ["44790055852"]`, which is an OUTER vertex of the triangle and never its centre (E8): `get_by_phone("44790055852")` returns Priya Raman by direct key hit, `get_by_phone("0790055852")` returns Priya Raman through the fuzzy arm, and `get_by_phone("10790055852")` returns **None**. The fixture carries no other phone that `phones_match` unifies with any of the three forms, and no two fixture notes carry phones `phones_match` unifies at all (E8 invariant 2). `get_by_phone` iterates a MATERIALIZED snapshot of `_phone_index` rather than the live mapping — asserted structurally over the tracked source (the loop's iterable is a call, not a bare attribute), which is WI-004's `docs/concurrent-access.md:8713-8714` finding closed. The resolution site carries a comment naming the non-transitivity as the reason, and the comment cites this test.
why: The mint left this as an open design call and WI-021 deliberately declined it twice, labelling it "WI-023 item 2's question" in both `phone_normalization.py:29-33` and `tests/test_name_gate.py:479-492`. The answer is derivable from source, and the risk is that it gets re-litigated by the next person who sees a raw-digit key next to a fuzzy matcher and reaches for the obvious tidy-up. A prose paragraph does not survive that; an executable witness does — it goes RED the moment someone "normalizes" `phones_match` into an equivalence, which is a real behaviour change to a matcher three consumer repos depend on. The concurrency rider rides here because WI-004 left that half open ON THE EXPECTATION that phones would leave the fuzzy path in this item; they do not, so this item either closes it or it stays open with no owner. The keys-are-distinct clause is the discriminating assertion: a build that "fixes" the problem by making all three forms produce one key passes any behaviour-only test and silently changes what `Phone.key` means for every consumer of the index. The fixture phone is a LITERAL here, and it is the outer vertex, because the earlier wording ("a note carrying one of the three forms … NOT for the one that does not") was a coin flip with an UNBUILDABLE face: `0790055852` is the CENTRE of the triangle — `phones_match` accepts it against `44790055852` (`phone_normalization.py:79-80`) and against `10790055852` (`:86-88`) — so a note carrying the centre is found by all three forms, "the one that does not" names nothing, and NO implementation, correct or otherwise, can satisfy the clause. The centre is also the obvious first reach, being the plain UK-local form and the one E3's witness table lists first, so the coin was weighted toward the unbuildable face. Only `44790055852` and `10790055852` leave one matching and one non-matching query; this criterion takes the first, and E8 hand-executes all three lookups against the indexing path (person.py:200-203, :407-421) so the expected values come from a stated definition rather than from the implementation. The no-unifying-phones invariant rides in the same clause because without it the negative witness can fail for a reason that has nothing to do with the property: `get_by_phone` falls through to a scan that returns the FIRST unifying `_phone_index` entry in insertion order (:417-419), so a second unifiable fixture phone would answer the query that is supposed to answer None, and the red would be walk-order noise rather than a broken carve-out.
check: test_phones_stay_on_the_fuzzy_path_and_the_reason_is_executable
kind: test
```

```criteria
id: AC-4
desc: ONE cascade, pinned against a golden with exactly ONE baseline moment. `resolve()` contains no match logic of its own — asserted structurally over the tracked source: its body calls `resolve_all` and applies a named module-level selection policy, and it does not itself read `_cache`, `_alias_index`, `_email_index` or `_phone_index`. Behaviourally it is pinned against a golden recorded at CUT 0, against this item's starting HEAD — before Cut 1, before Cut 2, before Cut 3 — and NEVER re-recorded: not after a cut, not to absorb a diff, not if the fixture changes (which is why the fixture is frozen with it and is never re-homed onto WI-016's vault, E6). The query space is DERIVED from that fixture: for every note, its exact name, each whitespace token of that name, each alias, each email and each phone — the phone queries having well-defined golden values only because E8 invariant 2 forbids two fixture notes carrying phones `phones_match` unifies, which would otherwise leave `get_by_phone`'s fuzzy scan (person.py:417-419) returning a walk-order-dependent note; every query returns the same person (or the same None) as the golden — EXCEPT the closed exception list below, which is Cut 1's alone and is a literal in the test, not a filter computed from a diff. Cut 3 gets no exceptions of its own. THE EXCEPTION LIST, hand-executed in E7: under the CUTOVER arm exactly two queries move — `"kit@localhost"` goes Kit Baldwin → **None**, and `" dana@example.com "` goes None → **Dana Okafor**; under the CARVE-OUT arm exactly one moves — `" dana@example.com "` goes None → **Dana Okafor**. Each exception is asserted to land on its DECLARED post-cut answer, never merely to differ; a query outside the list that moves is RED, and so is an exception that lands somewhere else. FOUR DISCRIMINATING queries are additionally hand-stated here, run against the SAME single fixture vault (E8's **ten-note** roster, complete; there is no second or throwaway vault), with the answers hand-executed against person.py:458-510 and :512-656 in `## Exploration Notes` E4 and E8, so that a golden regenerated after the cut contradicts this document instead of ratifying the change: (i) `resolve("john smith kato")` against the fixture's `John Smith` returns **None**, not the 0.65 `token-subset` candidate `resolve_all` scores for it (E4 class A); (ii) `resolve("pat@example.com")` returns **Alex Nkemdirim**, who carries it as an ALIAS, not `Rosa Delgado`, who carries it as an EMAIL — the alias step (person.py:488) preempts the email step (:493), and AC-2 pins the same pair from the other side as a declared asymmetry rather than an agreement failure (E4 class B, E8); (iii) `resolve("andy")` against the fixture's `Sandy Forster` returns **None** (whole-word, never substring — the property `tests/test_repositories.py:385-395` already pins, restated here so the consolidation cannot silently widen it); (iv) `resolve("emily m")` against the fixture's `Emily Mendes`, with NO company hint, returns **None**, not the 0.6 `partial-name` candidate `resolve_all` step 6 records for it at person.py:624-626 (E4 class C). Discriminants (i), (iii) and (iv) are hand-stated because the DERIVED query space provably cannot reach them; (ii) is in the derived space and is stated anyway because it is the one whose answer two criteria disagreed about. Two further clauses on the selection policy, because they are what these four jointly force and a build should not discover them by going red: the policy is a function of the candidate list AND THE QUERY (step 5's single-token branch at :610-612 and step 6 at :624-626 record the SAME 0.6 under the SAME `partial-name` label, yet `resolve("sandy")` must return `Sandy Forster` while (iv) must return None — no pure function of `List[ResolveCandidate]` separates them), and it must ACCEPT 0.6 while REJECTING 0.65, so a confidence threshold is the wrong shape. Outside the enumerated exception list there is no allowance for "improved" answers.
why: N5's drift is real, but "make resolve a thin head of resolve_all" is a behaviour change and it widens — the direction that mints wrong-person resolutions in HAL9000's contact cascade, which is the exact class WI-019 and WI-103 were opened to stop. The golden is the oracle, and the four hand-stated queries are the oracle's oracle: a derived golden proves membership over the query space, but a golden regenerated from post-cut code agrees with whatever the cut did, so the three known divergences and one known invariant are written into the contract in prose where regeneration cannot reach them. (i), (ii) and (iv) are E4's three hand-executed divergence classes and are the specific answers a literal thin head gets wrong; (iii) is included because a widening consolidation is most likely to break substring rejection, and because it is an existing pinned promise this item must not spend. Three of the four are hand-stated for a stronger reason than belt-and-braces: THE DERIVED GOLDEN CANNOT SEE THEM. Its space is names, name tokens, aliases, emails and phones, so a three-token query (i), a substring-of-a-token (iii) and a two-token-with-short-second query (iv) never enter it — (iv) is the sharp case, because `resolve_all` step 6 exists ONLY for that shape and its own comment at person.py:615-617 wrongly calls it sub-floor ("stays low confidence (< 0.5) and gets filtered out below"; it records 0.6 against a 0.5 floor), so a builder auditing for divergences by reading the code concludes the branch is inert. An oracle blind to a divergence is not evidence about it, which is why the class went unnamed until it was hand-executed. The two policy clauses are stated because the four discriminants are jointly unsatisfiable by the obvious implementation: sorting by confidence and taking the head inverts (i) against `resolve("sandy")`, and no function of the candidate list alone separates (iv) from `resolve("sandy")` — the two record identical `(confidence, matched_via)`. Reading the QUERY is inside this criterion's structural clause, which forbids `resolve` reading the four indexes, not its own argument; saying so here is what stops a build reading the clause as "candidates only" and concluding the ACs contradict each other. The single-baseline clause and the exception list exist because "recorded before the cut" was ambiguous and the ambiguity was load-bearing: Cut 1 rewires `resolve()` as well as `get_by_email` (step 3 reads `_email_index` at person.py:492-496) and AC-2 names `resolve` as one of the four surfaces it re-homes, so a bare "reproduce the golden" made AC-2 and this criterion jointly unsatisfiable for a refused-string plant containing `@` — and the cheapest repair, regenerating the golden after Cut 1, is precisely the defeat this criterion was written to prevent. Enumerating three rows in advance, in prose, costs nothing and cannot be reached by regeneration. Asserting each exception's DECLARED value rather than "it differs" is what stops the list from becoming a licence: a build that breaks `kit@localhost` in some third way is still RED.
check: test_resolve_is_one_cascade_and_matches_the_pre_cut_golden
kind: test
```

```criteria
id: AC-5
desc: The documentation surface tells the truth. `docs/identity-cutover-corpus-audit.md` exists and carries the shape its precondition fence declares: the literal walk command with verbatim stdout and the count of `type: person` notes scanned; every `emails:` entry `Email.parse` refuses, quoted with its note and reason, or an explicit "no matches" marker rather than an absent field; the whitespace-class and angle-bracket-class divergence counts; the count of cross-note `phones:`/`whatsapp:` pairs `phones_match` unifies but `Phone.key` does not; and a 40-hex HEAD SHA per consumer repo scanned. The test asserts this SHAPE — failing on a missing section, an absent field, a SHA that is not 40 hex characters, or a stated count with no listing behind it — and makes no subprocess, network or vault call. In the same criterion: the string `paren-decoration-at-the-door` appears at zero sites across the tracked sources, and every `docs/`-relative markdown path named in a comment in `obsidian_schemas/` resolves to a file that exists; the slack carve-out at person.py:238-242 survives with its UNBLOCK CONDITION stated (what would have to be true of the frontmatter for `slack` to be projectable), not merely its current status; and the false comment on `resolve_all` step 6 is repaired — the claim at person.py:615-617 that without a company hint this match "stays low confidence (< 0.5) and gets filtered out below" is untrue (it records 0.6 at :626 against the `>= 0.5` floor at :654), so the tracked sources contain no comment asserting that step 6 is filtered out absent a company hint, and the surviving comment states what actually happens. Asserted over the source text, not by re-executing the cascade — the behaviour is AC-4's job.
why: The audit is an EMPIRICAL premise about a corpus and settling it by reasoning about what vault emails look like is the WI-144 shape — the reading that the corpus falsified after the signature rather than before it. The teeth are the precondition fence, not this test; this pins the artifact's shape so the audit cannot be discharged as one hand-waved sentence, and the per-class listing is what forces the answer to the only question that can make Cut 1 harmful. The riders ride here rather than in their own criterion because they are the same property: a comment pointing at a file that does not exist, a carve-out note with no unblock condition, and a comment claiming a live branch is filtered out when it is not are all documentation that has stopped being true, and the dangling reference (person.py:113) has been dangling since WI-121. Generalizing from that one string to "every `docs/` path named in a package comment resolves" is what stops the fix being one deleted line that the next stale pointer walks straight past. The step-6 comment is the most expensive of the three and earns its place by demonstration rather than by principle: it is the reason E4's third divergence class went unnamed through a full round of review — anyone auditing `resolve_all` for things `resolve` does not do reads "gets filtered out below" and correctly concludes the branch is inert, which is exactly the audit Cut 3 depends on.
check: test_identity_cutover_docs_are_complete_and_truthful
kind: test
```

### Examples of done

**Given** the endgame has shipped — **when** someone greps the package for `_find_or_create_stub_legacy` — **then** there are no hits, and the thing that replaced it as evidence is a committed golden of what `find_or_create_stub` answered before any of this item's cuts, still executing in the ~1s hermetic floor. The duplicate is gone *and* we can still tell if we broke it, which was never true of the harness that was standing there before.

**Given** an ingester hands the library the address `jane.roe@example.com` — **when** it arrives through `get_by_email`, through `resolve`, through `resolve_all`, or as a typed `Email` inside `find_or_create_stub` — **then** all four reach the same lookup and return the same person, and if that address is instead recorded on the note as `Jane Roe <jane.roe@example.com>`, the answer does not depend on which of the four doors was used. One authority for email, and the audit's number in the code saying why it is the one it is. **And** — the one thing that is deliberately *not* promised — if somebody else has that exact address recorded as an **alias**, `resolve` still hands back the alias owner, because `resolve` asks four indexes and the alias one comes first. That is not a leak in the one-authority property, it is a different question being asked, and the suite says so out loud instead of leaving the next refactor to guess.

**Given** the golden was recorded at Cut 0 and Cut 1 then re-homed `resolve()`'s email lookup — **when** the suite runs after Cut 1 — **then** exactly the queries this document names in advance have moved, each to the answer this document names, and nothing else has; and when someone reaches for the obvious fix of re-recording the golden so the diff goes away, the enumerated list still says what the pre-cut answers were, because it is prose in the item and not data the build can regenerate.

**Given** a maintainer six months from now sees `Phone.key` returning raw digits right next to a fuzzy country-code matcher and reaches for the obvious tidy-up — **when** they normalize `phones_match` into something keyable — **then** a test goes red holding three real phone numbers and the arithmetic showing the relation is not transitive, so no key can express it. The carve-out defends itself instead of relying on someone reading a comment.

**Given** an orchestrator session calls `repo.resolve("john smith kato")` against a vault holding one `John Smith` — **when** the consolidated cascade runs — **then** it returns **None**, exactly as it does today, and a duplicate is not created against a person we merely share two name tokens with. The two cascades became one, and not one of the answers moved.

**Given** the same session calls `repo.resolve("emily m")` with no company hint, against a vault holding one `Emily Mendes` — **when** the consolidated cascade runs — **then** it returns **None**, exactly as it does today, even though the ranked cascade underneath it scores Emily Mendes at 0.6 and the code comment sitting on that branch says it gets filtered out. `resolve_all` is still free to offer the candidate to a caller that asked for candidates and passed a company hint; `resolve`, which callers treat as an answer, still declines to guess from a first name and an initial.

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

## Architectural Review — 2026-09-06

**Round 4 (post-AC-red-team fold). Recommendation: PROMOTE to architected**

Cold-start re-read of the whole document against the tree at HEAD `2bf731f` + the seeded delta. The red-team's two findings are CLOSED, four of round 3's five spec-writer notes are folded in, and I re-executed every hand-execution the third fold added — the two new roster rows, both fixture invariants, and the Branch-B threshold arithmetic — without falsifying any of them. The residue is three notes, none of which changes an arm, a cut order, an oracle, or a criterion's satisfiability.

### Trigger check

Fires on three, unchanged: significantly extends/replaces a core system (which code resolves email, and which person `resolve()` returns, across three consumer repos); touches >3 files in different concerns; effort > 1 day (four ordered cuts + a precondition artifact).

### The red-team's findings: HELD

- **AC-3's phone plant is pinned, and pinned to the buildable vertex.** AC-3 now names `44790055852` as a literal and E8 hand-executes all three lookups. Re-executed independently against `_phone_index` keyed `normalize_phone(...)` (person.py:200-203) with `get_by_phone` normalizing the query first (person.py:407): `44790055852` is a direct key hit (`:412-414`) → Priya Raman; `0790055852` misses the direct lookup and takes the fuzzy scan at `:417-419`, where `phones_match("0790055852","44790055852")` fires the `norm2.startswith("44") and norm1.startswith("0")` arm (phone_normalization.py:79-80) → `"790055852" == "790055852"` → Priya Raman; `10790055852` misses the direct lookup and no arm fires against the single indexed digit-string (neither side starts with `0`; the US arm at `:83-85` gives `norm1[1:] == "0790055852"`, not `"44790055852"`) → **None**. Two matching, one non-matching — the witness AC-3 asserts, and the one the centre `0790055852` provably could not supply.
- **AC-1's branch coverage is now constructed by pinned material, not claimed.** The roster carries `phones:` on two notes and `company:` on one, so Branch A's phone arm and Branch B's corroboration arm have something to hit. I re-executed Branch B's arithmetic end to end rather than trusting it, because it lands exactly on the threshold: `find_or_create_stub(name="Tomas", company="Kestrel Analytics")` parses no identifiers so `ids` is empty and Branch A is skipped (person.py:883-915); `_clean_query_for_lookup` returns `"Tomas"` unchanged (`_strip_corroborated_company_suffix` returns verbatim below 3 tokens, person.py:1076-1080); `resolve_all("Tomas", company=…)` misses steps 1-4 (`"tomas"` is not the `_cache` key `"tomas villalobos"`, no `@`, no alias, `normalize_phone("Tomas")` is `""`), records 0.6 `partial-name` at the single-token branch (`:610-612`), and the company bump's field arm at `:640-643` adds 0.25 → 0.85. `0.6 + 0.25` is exact in IEEE-754 double (both sides are `7656119366529843 × 2⁻⁵³`), so the `>= threshold` test at `:920` passes on equality against the default `confidence_threshold: float = 0.85` (`:665`) rather than on a rounding accident. E8's claim that the bump's second arm cannot fire is also right: `company_lower in canonical_name_tokens` (`:642`) tests a two-word string for membership in a set of single tokens.
- **Both fixture invariants are load-bearing, not tidiness — confirmed at the source.** `base.py:231` loads via `self.vault_path.glob(self.file_pattern)`, unsorted, so `_cache` insertion order genuinely is the filesystem walk; `resolve` step 5 returns the first `_cache` entry containing the token (person.py:506-508) and `get_by_phone`'s fuzzy scan returns the first unifying `_phone_index` entry (`:417-419`). Both invariants therefore remove real machine-dependence. Invariant 1's arithmetic checks out: twenty distinct tokens across ten notes, with `kestrel` and `analytics` absent from that set. Invariant 2's hand-execution checks out: `phones_match("2125550147","44790055852")` is False (no direct match; `"2125550147"` starts with neither `44` nor `0`, is 10 digits, and does not start with `1`; `"44790055852"[1:]` is not it), and `2125550147` unifies with neither `0790055852` nor `10790055852`.
- **The fold costs the closed exception list nothing.** The two added notes carry no `emails:` and no `aliases:`, and every query they contribute to AC-4's derived space (`priya raman`, `priya`, `raman`, `44790055852`, `tomas villalobos`, `tomas`, `villalobos`, `2125550147`) is free of `@`, so `resolve` step 3 — the only thing Cut 1 re-homes — is never reached for any of them. E7's list stays at two rows (cutover) / one row (carve-out) with the roster at ten, exactly as claimed.

### What I verified this round, and what held

- **Round 3's selection policy still discharges the enlarged roster.** Single-token query → best candidate, 1.0 ties ordered by `matched_via` in `resolve`'s cascade order; multi-token query → only a 1.0 candidate. Re-run against the new queries: `priya`/`raman`/`tomas`/`villalobos` each record one 0.6 `partial-name` (invariant 1 makes the target unique) and reproduce today's step-5 answer; `44790055852` and `2125550147` record 1.0 `phone`; `priya raman` and `tomas villalobos` hit exact-name at 1.0. Nothing the fold added reaches step 6 (`len(query_tokens) == 2` with a ≤2-char second token, `:618-620`) or the 0.65 `token-subset` arm, so the four discriminants and `resolve("sandy")` are undisturbed.
- **The AC-1 sweep is deterministic under mutation, which its ordered-replay clause needs.** `create_stub` reaches the vault through `save`, and the adoption door at base.py:174-181 copies the mapping and appends the new key — it does not re-`glob`. So a Branch C mint lands at the end of `_cache` in case order, and a golden recorded from the frozen ordered case list replays identically on a machine that enumerates the fixture differently. The clause is satisfiable as written.
- **Every citation still resolves and still means what the doc says.** Spot-re-resolved this round: person.py:78-85 (the compat re-export, with the two consumer sites named), `:113` (the dangling `paren-decoration-at-the-door` pointer, still exactly one site, still no such file), `:238-242` (the slack carve-out), `:337-342` (`_remove_entity_from_indexes` deleting only the lowered literal), `:417` iterating the live `self._phone_index.items()` against `_clear_indexes` mutating it in place at `:326-333`, `:615-617` (the false sub-floor comment) against `:626`/`:654`, `:668-686` and `:905-944` (the consumer contract and the three branches); identifier.py:154-156/:159/:167-168 (`parseaddr` routing, the strip, the `malformed local@domain` refusal) and `:237`/`:253-254`; name_validation.py:385-387 (the weak-identity guard, single-token-no-email-no-phone); models.py:81-84 with **zero** validators anywhere in the file, so `" dana@example.com "` survives load un-normalized; derivations.py:183-197 (`python_files_under`, public and `rglob`-based) against `:871-885` (`functions_calling`, which cannot see a `def`); tests/test_resolve_or_create.py:189-211 and `:214-224` (both legs still one computation) and tests/test_wi126_body_preservation.py:200-207/:209-215; state/work-items.json:2017-2027 (`WI-022, WI-016, WI-023, …`).

### Review

**Fit:** Unchanged and still right — a derived AST/text wall in `tests/derivations.py` plus a hermetic committed fixture is the idiom WI-020 and WI-021 established, and AC-1's literal-text scan, AC-3's structural assertion on the `get_by_phone` loop's iterable, and AC-4's structural clause on `resolve`'s body are all that idiom. The floor stays hermetic (E5), which is WI-024's standing constraint.

**Duplication:** The item removes a duplicate. The one it knowingly accepts — a second fixture vault beside WI-016's — is argued on the right axis in E6 (a realism corpus other suites may extend versus an oracle's byte-frozen declaration) and the cost is named. The fold makes that argument *stronger*, not weaker: the two added notes carry a deliberate non-transitivity vertex and a threshold-exact company corroboration, which is precisely the kind of plant an anonymized real-vault corpus has no reason to contain. `lint_vault` repair is still routed to WI-026 and the E.164 write-boundary fix is still minted as a follow-on rather than absorbed.

**Boundaries:** `find_or_create_stub`'s signature/return/exception set (person.py:668-686) and the `normalize_phone`/`phones_match` re-export (person.py:78-85) remain declared untouchable and are still load-bearing in two consumer repos; the other three repositories' `resolve()` stay out of scope. E3 applies the WI-185 lens honestly — it names `normalize_phone` destroying the `+` (phone_normalization.py:52-55) as the real seam and routes the seam fix out rather than smuggling a region policy and a vault migration into a deletion item.

**Determinism boundary:** Clean. No capability is handed to an LLM; the single empirical premise that cannot be reasoned about is routed to a `## Write Targets` precondition with a shape contract and a decision rule stated in advance, rather than to a builder's reading of the three-month-old zero-failures claim at person.py:236-238.

**Reversibility:** Cut-by-cut, with the oracle standing until Cut 4 and the only irreversible step happening last against two committed goldens.

**Generalization:** Correctly scoped down by E5 — no `Alias` identifier type exists and `slack` is unprojectable, so the Intent's real property is one authority *per kind*, which is what AC-2 asserts.

**Cost & maintenance:** Net negative code, with the added cost being one frozen ten-note fixture and two golden files, executing inside the existing ~1s floor.

**Build vs extend vs integrate:** Extend-then-delete, in that order — the only ordering that keeps an oracle alive across the behaviour-changing cuts.

**Prior art (outside view):** No divergence to justify. The constraint is "the pre-WI-125 oracle is about to be deleted", and the standard answer — characterization / approval / golden testing, recorded once against unchanged code and never regenerated — is exactly what Cut 0 reaches for, down to the never-re-record discipline.

### Notes (non-blocking) for the spec-writer

- **AC-1's Branch C variants are the last unfixed plants, and they mutate the vault the later cases run against.** The criterion constrains them twice (multi-token name; not-present under `phones_match`) but not on name tokens — and a mint whose name shares a token with a roster note is visible to every later case in the same run, because the adoption door appends it to `_cache` (base.py:174-181). Nothing becomes unsatisfiable (a shared single token scores 0.6 and two shared tokens 0.65, neither reaching the 0.85 reuse threshold without a company hint, and the golden records whatever happens deterministically), so this is a note rather than a finding — but the cheap belt is to extend E8 invariant 1 over the minted names too, and in particular to keep the not-present variant of the Branch B case (the one carrying `company: "Kestrel Analytics"`) away from `tomas`/`villalobos`, where 0.65 + 0.25 would silently convert a create case into a reuse and quietly drop a Branch C witness from the sweep.
- **AC-1's per-case branch annotation is wrong for exactly the three planted email notes.** "one case per `emails:` entry (`name=…, email=<the entry>` → Branch A, email hit)" does not hold for `Jane Roe`, `Kit Baldwin` or `Dana Okafor`: hand-executed, `Email.parse` refuses `kit@localhost` so `parse_identifiers(strict=False)` yields no identifier at all; `"Jane Roe <jane.roe@example.com>"` parses to `jane.roe@example.com`, which misses `_email_index`'s bracketed-literal key; and `" dana@example.com "` parses stripped, which misses the padded key. All three fall through to Branch B and reuse on exact-name at 1.0, so their golden pairs are unchanged and unmoved by Cut 1 — the coverage claim survives because `Rosa Delgado`'s pinned `pat@example.com` is a genuine Branch A email hit both pre- and post-cut. Worth correcting anyway: AC-1's whole design is that branch coverage is checkable *by reading*, and as written the annotation tells a reader that the refused plant covers Branch A when it structurally never can.
- **The Branch B witness sits exactly ON the threshold.** 0.6 + 0.25 == 0.85 is exact, so it is correct today and not a rounding hazard — but it means any future re-tuning of the `partial-name` score or the +0.25 bump flips that case from reuse to create and reddens the golden for a reason unrelated to this item. E8 discloses this ("corroborates a one-token name to exactly the 0.85 threshold"), so it is a known cost, not a hidden one; the spec should carry the disclosure forward to whoever reads the red.
- **Round 3's fifth note is still open and still worth taking.** Under the carve-out arm E7 requires the surviving authority to key both the lowered raw entry and the parsed address; `_remove_entity_from_indexes` deletes only the lowered literal (person.py:337-342), so an `update_fields` that drops an email would strand the parsed-address key pointing at a stale cache key. Cheap, and exactly the asymmetry a widen-the-index cut leaves behind.
- **Stage advance is owed to the conveyor.** This gate emits the verdict only; the move to `architected` belongs to `stage_advancer.py`, run by the driver.

```verdict
gate: architect
verdict: PROMOTE
date: 2026-09-06
model: claude-opus-5
note: The red-team's two findings are closed on pinned literals I re-executed rather than took on trust — AC-3's plant is the outer vertex `44790055852` (two matching forms, one non-matching, against `_phone_index` and the fuzzy scan) and E8's ten-note roster now constructs Branch A's phone arm and Branch B's corroboration, whose 0.6 + 0.25 lands exactly on the 0.85 threshold with no float slack — both fixture invariants are load-bearing against an unsorted `glob` at base.py:231, the enlarged roster leaves E7's exception list closed and round 3's selection policy intact, and the residue is three spec-level notes that change no arm, no cut order and no oracle.
```

## AC Red-Team — 2026-09-06

Round 2 (re-verify, post-fold). Cold-start re-read of the whole document against the tree at HEAD `2bf731f` + the seeded delta, read in the prescribed order (`## Intent`, `### Examples of done`, `## Problem / Motivation` and `## Exploration Notes` before `## Acceptance Criteria`). I do not trust the architect's four rounds of re-execution as a substitute for my own — decorrelation is the point of this gate — so I independently re-derived the two pieces of arithmetic my round-1 REVISE turned on, against the actual source rather than the document's prose.

**AC-3's fixture literal — re-executed independently, holds.** `phone_normalization.py:58-90`, hand-run: `phones_match("44790055852","0790055852")` → both `normalize_phone` outputs are digit-only, no direct match, `norm1.startswith("44") and norm2.startswith("0")` → `norm1[2:]=="790055852"==norm2[1:]` → **True**. `phones_match("0790055852","10790055852")` → `norm2.startswith("1") and len(norm2)==11` → `norm2[1:]=="0790055852"==norm1` → **True**. `phones_match("44790055852","10790055852")` → neither UK arm fires (neither side starts `"44"`+`"0"` in the right slots — `10790055852` starts `"1"`, not `"0"`), the US arm gives `norm2[1:]=="0790055852"`, not `"44790055852"` → **False**. So `Priya Raman`'s pinned `44790055852` is a direct key hit for itself, is reached by `0790055852` through the fuzzy arm, and is NOT reached by `10790055852` — exactly AC-3's asserted witness, and the fix is IN the criteria text itself (`docs/identity-engine-endgame.md`'s `AC-3` fence names `Priya Raman` and `44790055852` by literal), not left in the exploration notes for a builder to infer. Round 1's CRITICAL — the unpinned choice whose natural first reach (`0790055852`, the triangle's centre) is provably unbuildable — is closed.

**AC-1's roster-construction claim — re-executed independently, holds.** Read `repositories/person.py:595-656` directly: for query `"tomas"` against cache key `"tomas villalobos"`, `shared={"tomas"}`, `len(shared)==1`, `query_tokens.issubset(cache_tokens)` is true, and the `elif len(query_tokens)==1` branch records `0.6, "partial-name"` (`:610-612`) — matches the doc. The company-hint bump (`:635-651`) computes `canonical_company == company_lower` for `"kestrel analytics" == "kestrel analytics"` → `True`, `new_conf = min(1.0, 0.6+0.25) = 0.85`. I did not take the document's IEEE-754 exactness claim on faith merely because it's precise-sounding; the code's own comparison is `>= confidence_threshold` (`:796`) with a default of exactly `0.85` (`:665`), and `0.6+0.25` is the identical Python float expression on both sides of that boundary regardless of which repr the doc favors — the pass is not an accident of the doc's chosen decimal literals. AC-1's criteria fence now names `Priya Raman` and `Tomas Villalobos` directly and derives their cases from the same ten-note roster AC-3, AC-2 and AC-4 all cite — round 1's MATERIAL (branch coverage claimed but not constructed against the pinned eight-note roster) is closed by construction, not by assertion.

**Both findings: `basis: original` material, now folded, held on independent re-execution — no reopening.** I also swept for the failure classes my round-1 pass had not yet reached given the two blocking items in front of it: tautological ACs (none — AC-1's replacement mechanism is a literal-text scan over `python_files_under`, re-confirmed public and `rglob`-based at `derivations.py:183-197`, distinct from `functions_calling` which structurally cannot see a `def`, `:871-885`); gameable-by-single-literal (none found — AC-2/AC-4's plants are pinned, distinct, and each moves a different divergence class); mutually unsatisfiable pairs beyond the two already closed (swept AC-1↔AC-4, AC-3↔AC-4, AC-2↔AC-5 — no new collision); an uncovered invocation layer (none — AC-2 names all four resolving surfaces by name); a mocked oracle (none — the golden is committed data captured once at Cut 0, never regenerated, which is the correct answer to the mint's dead in-tree parity harness per E1); an unrun corpus claim (already correctly routed to the `## Write Targets` precondition rather than asserted in an AC).

**Noted, not escalated.** Round 4's own non-blocking note — that AC-1's Branch-C "not-present variant" of the company case is an unpinned name, and if a spec-writer later chose one sharing two tokens with `Tomas Villalobos` the `0.65 token-subset + 0.25 company-hint = 0.90` bump would silently convert that create case into a reuse and drop a Branch-C witness — is real, but I am not escalating it. It is different in kind from the two findings above: those were about the DOCUMENT'S OWN PINNED LITERALS, checkable by reading, where one specific choice was provably unbuildable (AC-3) or the currently-pinned roster provably lacked a witness (AC-1, pre-fold). This is a warning about a hypothetical FUTURE choice by whoever builds the fixture, over an unbounded space of valid names, where the document already states the exact hazard and its remedy (extend E8 invariant 1 to the minted names) in plain terms. Escalating it would be grading the spec-writer's future diligence rather than attacking a defect present in the criteria as written — the "too strict" failure this gate is calibrated against. It is real enough to be worth a line here so it travels forward rather than needing rediscovery.

I attacked the fold, not just read it, and could not falsify either repair. Nothing else in the criteria set is gameable, tautological, or drifted from Intent that I could find. This document has now been through four architect rounds and two red-team rounds; the remaining residue is spec-level, not architectural or criterial.

```verdict
gate: ac-red-team
verdict: PROMOTE
date: 2026-09-06
model: claude-sonnet-5
note: Both round-1 findings are closed and I re-derived the arithmetic independently rather than trusting the document — AC-3's outer-vertex phone literal (44790055852) is pinned in the criteria text and its two-match-one-miss witness re-executes against phone_normalization.py:58-90, and AC-1's company/phone branch coverage is now constructed by the same two named roster notes (Priya Raman, Tomas Villalobos) whose 0.6+0.25 company-hint bump re-executes against person.py:595-656 to clear the 0.85 threshold; swept the remaining failure classes (tautology, single-literal gameability, further mutual-unsatisfiability, uncovered invocation layers, mocked oracles, unrun corpus claims) and found nothing new.
```

## AC Sign-off

```verdict
gate: ac-signoff
verdict: PROMOTE
date: 2026-09-06
reviewer: dave
channel: cli
signed_at: 2026-09-06T17:23:59+01:00
provenance: verified
signoff_escalation: ESC-WI-023-exploring-awaiting-ac-signoff-9d293950
ac_hash: 583a1b6a293a
intent_hash: ce7e35a70ea0
ac_hash_AC-1: bd76924cea03
ac_hash_AC-2: 7523d81032ed
ac_hash_AC-3: a2ce8381aa34
ac_hash_AC-4: f21e51ef4ea0
ac_hash_AC-5: 0dec3196b520
artifact: docs/spec-reviews/WI-023-dave-review-2026-09-06.md
```

## Data Audit — 2026-09-06

**Recommendation: PROMOTE to specced**

Cold-start read of the whole document, the committed grounding artifact
(`docs/identity-cutover-corpus-audit.md`) and the tree. I did not take the artifact's numbers
on trust — I cannot re-run its command from inside this worktree (no live vault, no consumer
repos, no shell), so I did the one thing that IS available and is the thing that actually
decides whether a corpus number means what it claims: I re-derived, from the source, the
DOMAIN the audit's predicate walked and checked it against the domain `_email_index` is
actually built from. That check is below, and it is what this verdict rests on.

### Trigger check

**Class 1 and Class 2.** Class 1 fires on an existence claim about live data: E2's decision
rule turns on whether *any* live person-note `emails:` entry is refused by `Email.parse`, and
E2 class (a) is explicitly "size on the live vault: unknown". Class 2 fires because Cut 1
introduces a new resolution rule (route email through `_identifier_index`) whose correctness
depends on its effect against the corpus that exists *today*, not on hypothesized inputs.
Class 0 is not available to this item — the `## Write Targets` fence declares the premise in
terms.

### Premise

Three empirical claims, all load-bearing:

1. **The arm-selecting one.** Zero live `emails:` entries are refused by `Email.parse`
   ⇒ the CUTOVER arm; any refusals ⇒ the carve-out arm plus a repair rule routed to WI-026.
   This is the only premise that changes what the item BUILDS.
2. **The improvement-class sizes.** E2 classes (b) and (c) — angle-bracket and
   whitespace-bearing entries — are behaviour changes at cutover; their live counts size how
   much real behaviour Cut 1 moves.
3. **The fuzzy arm's live witness count.** AC-3 preserves `phones_match`'s non-transitive arm;
   the number of cross-note phone pairs it unifies where `Phone.key` does not is what says
   whether the arm is live or dead.

Everything else the document asserts is a predicate over the TREE, not the vault — E1's
tautology, E3's non-transitivity, E4's three divergence classes, E7's and E8's hand-executions
— and those are not this gate's premise. I spot-re-executed the ones the audit's validity
depends on and they hold (below).

### Predicate + result

The predicate was run — once, by the conductor, on 2026-09-06 — and the artifact is committed
at `docs/identity-cutover-corpus-audit.md`, carrying the literal one-shot command, verbatim
stdout, and exit 0. The numbers, dated so build-start re-grounding can detect rot:

| clause | result, live vault, 2026-09-06 |
|---|---|
| (a) `type: person` notes loaded | **1147**; skip surface **0**, so scanned = loaded |
| (b) non-empty `emails:` entries / entries `Email.parse` REFUSES | **1021 / 0** — explicit "no matches" |
| (c) entries where `raw.lower() != Email.parse(raw).value` | **0** — whitespace class 0, angle-bracket class 0, other 0 |
| (d) cross-note phone/whatsapp pairs `phones_match` unifies but `Phone.key` does not | **0** over 276 values, 0 refused by `Phone.parse` |
| (e) consumer HEAD SHAs (40-hex) + live reaches into the legacy dicts | HAL9000 `68fbd334…`, exocortex `2c6f0896…`, orchestrator `d44418d9…`, obsidian-schemas `990aa6de…`; **0** non-test reaches (HAL9000's 2 are a test wall naming the reaches as forbidden and a docstring) |

**The check that makes those numbers admissible, re-derived here rather than assumed.** A
corpus count is only evidence if the predicate walked the same domain the rule will run over.
Hand-verified against the tree:

- `_index_entity` populates `_email_index` from **`entity.emails` only** — one loop,
  `self._email_index[email.lower()] = cache_key` (person.py:192-197). No other field feeds it.
- `_project_identifiers` runs `Email.parse` over **`entity.emails` only**
  (person.py:254-255). Same domain, no wider, no narrower.
- The audit's (b) iterates `p.emails` over `repo.get_all()`. `load()` indexes exactly the
  entities `_load_file` returns and `get_all()` returns exactly those (base.py:231-245), so
  the audited set is *identically* the set `_email_index` was built from. There is no
  third field, and no note in one and not the other.
- The skip surface is real and owned-scoped, not decorative: `_note_skip` records a
  `SkippedNote` only for files the repository can PROVE are its own on the declared type
  (base.py:258-275), and `_load_file`'s broad except routes every load failure through it
  (base.py:277-307). A skip surface of 0 therefore means no note declaring `type: person`
  failed to load — it is not silence standing in for absence.
- (d)'s domain is right too: `_index_entity` puts both `phones` and `whatsapp` into
  `_phone_index` (person.py:200-209), and the audit scans `p.phones + p.whatsapp`.

So (b)'s zero is over exactly the class E2(a) names, not a proxy for it.

### Conclusion

**The premise holds and the decision rule fires cleanly.** Zero of 1021 live `emails:` entries
are refused ⇒ **CUTOVER**: `_identifier_index` becomes the email authority and `_email_index`
is deleted; no repair rule is routed to WI-026 for email. AC-2 is written arm-agnostic and is
undisturbed by the selection. (c)'s two zeros are the stronger result and worth stating plainly:
not only is nothing LOST at cutover, nothing MOVES — neither improvement class has a single
live specimen, so on today's corpus Cut 1 changes no live answer at all. (e) closes the
consumer half: no live code outside this repo reads `_email_index`, so the deletion is
repo-local.

(d)'s zero does not falsify AC-3 and I want to be exact about why, because it is the one
number that reads as awkward for a criterion: AC-3 asserts the fuzzy arm is **unavailable to
key**, which is a property of `phones_match` derivable from source (E3, re-executed below),
not a claim that the arm has live witnesses. Zero witnesses makes the carve-out a
compatibility promise rather than a repair of a live loss — which is what the artifact says
in terms, and which the criterion already survives. It is also the number that would justify
the E3 follow-on (E.164 at the write door) being cheap when someone picks it up.

**Staleness note for build-start re-grounding (WI-022).** The artifact carries the literal
command; re-run it before Cut 1. The rot direction that matters is (b) going nonzero — one
newly-written malformed `emails:` entry flips the arm. Note the premise this audit REPLACES:
`person.py:236-238`'s "audited against the live vault (942 notes, 2026-06-13): ZERO failures"
was a confident reading standing in for a run, and it was 205 notes stale — the exact WI-144
shape. AC-5's rider should replace it with a pointer to the artifact, not with a fresh number
that will drift the same way; the artifact says this and I agree.

### Counterexample hunt (WI-293)

The document quantifies universally over domains this factory can enumerate, so a census is
not enough — I walked for members that are false BY DESIGN.

**Domain 1 — AC-5's "every `docs/`-relative markdown path named in a comment in
`obsidian_schemas/` resolves to a file that exists".** Predicate: every `.md` path mention in
`obsidian_schemas/` source (comments and docstrings), matched with `[A-Za-z0-9._/-]+\.md`
rather than a `docs/`-anchored pattern, precisely so the scan could not pre-filter out the
exemptions. **26 mentions, four classes:**

- *Vault-note filename illustrations* (18): `Name.md`, `person.md`, `Title.md`, `Smith.md`,
  `Speechmatics.md`, `October.md`, … These are Obsidian note names in docstring examples, not
  repository paths. **False by design**, and AC-5's "`docs/`-relative" qualifier already
  excludes them — the qualifier earns its keep. *Disposition: already-named exclusion.*
- *In-repo, resolving* (2): `docs/company-name-corpus-audit.md` at name_validation.py:40 and
  :347. Both resolve. ✓
- *In-repo, dangling* (1): `docs/paren-decoration-at-the-door.md` at person.py:113 — the
  rider's target, still exactly one site, still no such file. ✓
- ***Cross-repository pointers* (3) — THE FALSE-BY-DESIGN CLASS, and it is not dispositioned
  anywhere in this document.** `orchestrator/docs/identity-model-revised-2026-06-13.md`
  (identifier.py:3-4), `orchestrator/docs/name-validation-and-cleanup.md`
  (name_validation.py:29), `orchestrator/docs/find-or-create-stub.md` (person.py:729). Each
  names a real audit or spec in a sibling repo, each is *correct*, and none can ever resolve
  under this tree's `docs/`. The third dies with Cut 4 (it is inside
  `_find_or_create_stub_legacy`'s docstring); **two survive the item**. A build that
  implements AC-5's clause with the obvious `docs/[\w./-]+\.md` scan goes RED on two correct
  pointers, and the cheapest repair on the table is deleting them — losing a pointer to a real
  audit, which is this item's own harm class. There is a second wrinkle in the same class:
  identifier.py's pointer is line-WRAPPED (`orchestrator/docs/identity-model-` / `revised-
  2026-06-13.md`), so a line-based scan sees the bare filename `revised-2026-06-13.md` with no
  `docs/` prefix and misses it entirely — the exemption and the blind spot are the same site.
  *Disposition: **named exclusion**. AC-5's plain reading ("`docs/`-relative" ≠
  "`orchestrator/docs/`-relative") already gets this right, so the criterion is satisfiable as
  signed and this is not blocking — but the spec should state the exclusion class explicitly
  (a `docs/` match not preceded by another path segment) rather than leave it to a regex, on
  this document's own standing rule that an unfixed choice decides buildability.*

**Domain 2 — AC-1's "`_find_or_create_stub_legacy` appears at zero sites across
`obsidian_schemas/` and `tests/`".** Predicate: literal-string scan over both roots. **Three
sites**: person.py:699 (the `def`), person.py:675 (a prose mention inside the *surviving*
`find_or_create_stub` docstring), tests/test_wi126_body_preservation.py:212 (the caller).
**No false-by-design member** — nothing in those two roots needs to keep naming the symbol
after it is gone. But `## Approach` Cut 4 enumerates only the `def` and the two consumers and
does **not** name person.py:675, so the item's own site list is one short of its own criterion.
Self-correcting (AC-1's literal-text scan is total and will catch it, which is exactly why the
mechanism was changed away from `functions_calling`), hence a note rather than a finding.
While there: the same surviving docstring asserts at person.py:685 that "the Phase-5 replay
confirms zero return-value divergence over the real vault" — E1 establishes that replay is
cross-repo, unreachable and pre-WI-020/WI-021. That is AC-5's documentation-truth class,
unnamed by AC-5, and it sits three lines from a site Cut 4 already has to edit.

**Domain 3 — E5's "`normalize_phone`/`phones_match` are load-bearing in two consumer repos by
their `repositories.person` path".** I cannot walk this domain from here (no consumer repos),
and neither did the committed audit — its (e) greps consumer trees for
`_email_index|_phone_index|_alias_index|_slack_index` but not for the compat re-export.
**Domain not walked; stated rather than hidden.** Non-blocking in every direction: the claim
is a *don't touch* constraint, so being wrong about it costs a retained re-export nobody uses,
and (e) records the consumer SHAs, so it is re-checkable at build-start.

### OPEN questions

**None.** The two hunt results above are dispositioned (a named exclusion; a self-correcting
enumeration gap), and the one unwalked domain is conservative-by-construction. The premise
that selects the arm is grounded, decision-forcing, and settled.

```verdict
gate: data-premise
verdict: PROMOTE
date: 2026-09-06
model: claude-opus-5
note: The arm-selecting premise is grounded by a committed, re-runnable artifact — 0 of 1021 live `emails:` entries refused, 0 divergences in both improvement classes, 0 live consumer reads of `_email_index` — and I verified the thing that makes those numbers admissible rather than trusting them: `_email_index` (person.py:192-197) and `_project_identifiers` (person.py:254-255) are both built from `entity.emails` alone over exactly the set `get_all()` returns, with an owned-scoped skip surface reporting 0 (base.py:258-307), so the audited domain IS the indexed domain; E2's rule fires to CUTOVER and no draft AC is falsified — the counterexample hunt's one live class (three cross-repo `orchestrator/docs/…` pointers that AC-5's universal can never resolve, two surviving Cut 4) is dispositioned as a named exclusion AC-5's own "`docs/`-relative" wording already reads correctly.
```
