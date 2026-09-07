---
id: WI-023
title: "Identity engine endgame: delete the legacy cascade, cut over the unified index"
project: obsidian-schemas
stage: ready
created: 2026-07-05
last_touched: 2026-09-07
stage_changed: 2026-09-07
touched_by: spec-writer
tags: [identity, wi-125-followup, strangler-completion]
depends_on: []
transitions: ["idea>exploring@2026-09-06@session", "exploring>specced@2026-09-06@session", "specced>ready@2026-09-07@porter"]
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

**Cut 0 (oracle repair, no production change).** Re-point `tests/test_resolve_or_create.py`'s parity legs at `_find_or_create_stub_legacy` so they compare two different implementations again; build **one** item-local fixture vault — the **ten-note roster E8 fixes as literals, complete**, carrying E7's three email plants, E8's alias/email collision pair, E4 class (C)'s short-form target, AC-3's outer-vertex phone `44790055852` and the `company:`-bearing note whose one-token name corroborates to exactly 0.85, under **both** of E8's invariants (no two notes share a name token; no two notes carry phones `phones_match` unifies); and record two committed goldens **against this item's starting HEAD — before Cut 1, before Cut 2, before Cut 3**: `find_or_create_stub`'s `(name, created_new)` over the parity case set, and `resolve()`'s answer over a query space derived from that vault's own notes (every name, every name token, every alias, every email, every phone). **The four discriminating queries AC-4 hand-states run against the same single vault** — (i) `john smith kato`, (ii) `pat@example.com`, (iii) `andy` and (iv) `emily m`; (ii) is in the derived space already, the other three are hand-stated because the derived space provably cannot reach them (E4). There is no second ROSTER and no throwaway vault: one fixture declaration, two goldens recorded from it, one baseline moment. *(That is a statement about the roster, not about temp directories: D3(b) seeds the one roster once per sweep, because AC-1's stub sweep WRITES — its pre-cut Branch-B writeback rebuilds `emails[]` through the WI-021 gate and destroys two of E7's three plants in the vault it runs in — so the read-only resolve sweep must not be recorded in a vault it has touched.)* **This is the only baseline moment in the item.** Neither golden is ever re-recorded, and the fixture is frozen with them — not after a cut, not to absorb a diff, not if WI-016's vault lands first (E6, E7).

**Cut 1 (email).** Give email resolution exactly one authority. The audit in `## Write Targets` picks the arm: zero unparseable live entries → `_identifier_index` is the authority and `_email_index` is deleted; otherwise the permissive lookup stays — widened to also resolve the parsed address, so the typed door reaches it too (E7) — and the carve-out is written into the code with the audit's number beside it. Under both arms the shipped property is that `get_by_email`, `resolve`, `resolve_all` and `_resolve_identifier` reach the *same* lookup, so the two-authority state ends either way — *same lookup*, note, not *same answer*: `resolve`'s alias step still preempts its email step, which is a permanent declared asymmetry rather than a leak, and E8 pins it. **`resolve()` is one of those four surfaces, so this cut moves Cut 0's golden — on exactly the queries E7's table enumerates and no others** (cutover arm: `kit@localhost` and `" dana@example.com "`; carve-out arm: `" dana@example.com "` alone). Those rows are a closed literal list in the test, each with its declared post-cut answer; a fourth query that moves is RED, and so is an exception query that lands on some *other* answer.

**Cut 2 (phone, carve-out).** Phones stay on the fuzzy path, and the reason is made unforgettable rather than asserted: E3's non-transitivity witness ships as an executable test, and the code comment at the resolution site names it. `get_by_phone` iterates a materialized snapshot, closing WI-004's explicitly-open half.

**Cut 3 (cascade).** `resolve()` becomes `resolve_all()` plus a named selection policy — one that takes the **query** as well as the candidate list, accepts 0.6 while rejecting 0.65, and orders 1.0 ties by `matched_via` in `resolve`'s own cascade order (E4 states all three constraints and why each is forced) — green against Cut 0's golden including the four hand-stated discriminants, **with zero exceptions of its own**. Cut 1's enumerated rows are the only queries in the item whose golden value legitimately moves; if the consolidation wants to move a third, that is a decision for Dave with the case named, not a green test.

**Cut 4 (deletion, last).** `_find_or_create_stub_legacy` goes, and so do **both** of its consumers, named: the six vacuous parity cases in `tests/test_resolve_or_create.py:189-211` and `:214-224`, and `test_legacy_preserves_rich_note` at `tests/test_wi126_body_preservation.py:209-215` — the legacy twin of `test_engine_preserves_rich_note` (`:200-207`), which is left standing to carry the WI-126 body-preservation property alone. That twin is a real, currently-passing test, not scaffolding, so its removal is stated rather than implied: after this cut the WI-126 property has one witness, on the engine path, which is the only path that ships. The goldens survive all of it as the durable oracle. Riders land here: delete the dangling `docs/paren-decoration-at-the-door.md` reference (person.py:113) and give the slack carve-out note (person.py:238-242) its unblock condition.

Out of scope, routed: write-boundary phone canonicalization (new item, motivation in E3); a `lint_vault` repair rule for unparseable email entries (WI-026); the other three repositories' `resolve()` (untouched).

**Handoff.** New module boundaries are not created, no schema changes, no cross-system integration — but it changes which code resolves email and which person `resolve()` returns, across three consumer repos. **Spec-writer, not architect**, at the campaign's recorded Opus/high — with the sequencing above treated as a hard constraint on the implementation plan rather than as advice.

## Design

*Revised after spec-review round 2, which found the same defect at two more sites: an
enumeration this document treats as total that is one class short of the surface it covers.
Both findings are answered by closing the CLASS rather than the instances. **(1)** The four
falsified `person.py` documentation surfaces round 2 named are a minority of the class, and
reading
the census that found them turned up a member the markers missed (`_index_entity:193`) and one
sentence that has been false since before this item existed (`resolve_or_create:878-879`). **D11
is new**: it states the generator (five propositions about the strangler's mid-transition state),
the census, the per-site repair, which task lands each, a needle scan whose
unenumerated case fails LOUD, three named exclusions that would otherwise go RED on correct text,
and the next rung of the ladder swept and declared (other package modules: none; `tests/`: three,
all already owned; `docs/`: two, both routed; repo-root prose: none). D4 item 5 and D7's rider
list now say out loud that they are not total and point at it. *(Round 3 found that this fold was
itself one member short and re-founded D11's finding predicate on an enumerated surface; the
membership counts this paragraph originally carried are deliberately no longer restated here —
D11's own tables are the enumeration.)* **(2)** Task 12's needle and
non-vacuity positive are pinned, and `## Verification`'s non-vacuity table is no longer a list
somebody maintains — it states the rule that GENERATES it. Four
non-blocking notes are also taken: D2's golden ordinal (`kit@localhost` is 8, not 5) and its
`arm` vocabulary, `## Verification`'s regression count, and Task 5's invocation command. No
`## Acceptance Criteria` text was touched this round.*

*Revised again after spec-review round 3, whose first finding landed on **D11 itself**: the fold
written to close the strangler-prose class was one member short, and the missing member —
`resolve_all`'s own docstring at `:519-523` and `:534-539` — sits ninety lines above the comment
D11 does name, is matched by none of the six census markers, and is reachable by no needle the
plan pinned. Both defects were re-executed against the tree before repair and both are real
(`stops at the first cascade hit` states P4 in the file's own words; `"Emily M" … bumped 0.65 →
0.90 ≥ 0.85` is arithmetic that belongs to a different case — `"Emily M"` cannot reach the 0.65
`token-subset` arm at all, so step 6 records 0.6 and the bump lands on **exactly** 0.85, which
contradicts this document's own no-slack threshold disclosure). **The repair is a change of
FINDING PREDICATE, not a sixteenth table row**, and that is the whole point: two consecutive
rounds have now shown that a hand-picked marker set plus a reading pass decides which sentences
get read, and its reading step has under-reached both times. D11 is re-founded on a surface that
is enumerated at source — `prose_lines`, a fourth `tests/derivations.py` export returning EVERY
comment and docstring line in a file with its owning function — and the closure is a
**disposition rule over owners** that a machine checks in both directions against a Cut-0
snapshot, with the needle list demoted to what it should always have been: a cheap regression pin
over sentences already read. Round 3's second blocking finding, the `## Acceptance Criteria`
preamble restating a sign-off record that its own edits falsify, is closed by deleting the
restatement: the `## AC Sign-off` fence is now the single place the hash, the artifact and the
escalation are stated. Three non-blocking notes are also taken — `## Verification` cites D11's
needle sets instead of counting them (the third small-integer miscount in that one section), the
Task-6 transient red is named rather than denied, and this item's check module gets the
`CORPUS_COUPLING` declaration the two other `docs/**`-reading modules in this repo carry.*

*Revised a fourth time after spec-review round 4, whose first finding landed one level down from
round 3's: D11's FINDING predicate is now correct about which sentences must be READ, and its
DISPOSITION predicate was wrong about which owners must have CHANGED. "Every authorized owner
shows at least one Cut-0 line gone" was FALSE by D11's own table for two of the fifteen —
`select_resolution`, which Task 9 creates and which therefore owns no Cut-0 prose, and
`_clear_indexes`, whose one prose line D11 orders KEPT and whose authorization rested on a CODE
deletion at `:328` that `prose_lines` never emits — so Task 12 clause (e2) and Task 5's Cut-0
variant of it shipped RED against a correct build, with the two cheapest repairs from that red
being the two things D11 forbids in substance. **The fix is a change of AUTHORIZATION PREDICATE,
not an exemption list**: authorization is a statement about PROSE, never about code, so the set is
re-derived from the prose repair each owner is ordered (thirteen), `_clear_indexes` leaves it and
(e1) now pins its true docstring VERBATIM, and `select_resolution` is recorded as not a Cut-0 owner
at all. D11 then sweeps the next rung and declares it — the rule's other directions, per-OWNER
versus per-ROW (which is where a two-member exemption would have gone RED on `get_by_phone` and
`_project_identifiers`), the file level, and the one residual it does NOT close. Round 4's second
finding was mechanical and total: the 2026-09-07 threat model declared M1–M4 `kind: required` and
the document had not been folded since. M4 was already carried by D5 and Task 8; M1's recorder
path-binding, M2's `seed_vault` dest guard and M3's `NO_ARG_CONSTRUCTION` scan now land in D3(b)/
Task 5, D1/Task 3 and D10/Task 13, and all four have fold records in the new
`## Mitigation Folds — 2026-09-07`. Three non-blocking notes are also taken: D11's table gains the
`_find_or_create_stub_legacy` row the authorized list named without one, and D4 item 2 and the
Edge Cases error-propagation entry now name the `get_by_email(None)` widening instead of resting on
"the exception set is unchanged". No `## Acceptance Criteria` text was touched this round.*

*Revised a fifth time after spec-review round 5, whose finding is different in KIND from the four
before it: not another enumeration one member short, but a flat SELF-CONTRADICTION about one
shape. Task 2 listed "a code line containing `"""` inside a comment" as a near-miss that must NOT
be collected, four lines after listing "a trailing `#` comment on a code line" as a shape that IS
— and they are the same shape. `x = 1  # see the """ delimiter` carries a `COMMENT` token, so
D8's rule emits exactly one record for it, and the fixture was RED against a correct predicate at
the FIRST task in the plan, where the literal-instruction repair is to make `prose_lines` skip
comments containing `"""` — silently removing a class of comment from the finding surface D11's
whole closure is re-founded on, and invisible afterwards because `person.py` carries no instance
of it. **The generator is a fixture expectation written from what a line LOOKS LIKE rather than
from the predicate's own rule, so the fold is a rule and not a clause**: every planted line's
expectation is now DERIVED by applying D8's rule to that line's tokens, and where a plant and a
correct predicate disagree the PLANT is wrong unless D8's rule is — the predicate is never
narrowed to make a plant green. D8 then states the two line-scan-defeating shapes APART, because
they defeat it in opposite directions (a `#` in a string is a false positive owing no record; a
`"""` in a comment is a state-tracking failure that owes exactly one record, and what must not be
collected is the ordinary CODE that follows), and Task 2 asserts both halves. The same question
was re-run over the other three predicates and DECLARED: no second contradiction, but three
unproved cells, each now a plant — `materialized`'s five-wrapper vocabulary driven by `list`
alone, `attribute_reads_in` driving neither a Store nor a nested `def`, and
`docs_markdown_mentions` driving no docstring-borne mention — plus the two `attribute_reads_in`
clauses D8 had never stated. One rung further out, the same defect class turned up in the SHIPPED
helper Task 13 borrows: `tests/test_vault_path_required.py:_code_lines:295-304` is exactly that
line scan, so Task 13 now asserts no comment in this item's `tests/`-root modules carries a
triple-quote delimiter, with its one residual named. Three non-blocking notes are also taken:
D11's table gains `resolve_or_create:847-848` (the same already-false future tense as `:878-879`,
in the head of the same docstring — a SITE missing under an owner that had three rows, where
round 4's was an OWNER missing a row); `## Verification`'s non-vacuity rule now states two
sub-classes so a structural predicate's row is paired with something that proves the MATCHER'S
REACH rather than the data's size; and AC-2's `_email_index` zero is read at
`PACKAGE_ROOT, TESTS_ROOT` — the same scope Task 10 gives AC-5's identical "the tracked sources"
phrase — which makes Task 7's tests-root cleanup asserted rather than left to an `AttributeError`,
and adds a third authorized case to the Task-6 interior red that the boundary paragraph now
names. No `## Acceptance Criteria` text was touched this round either.*

*Revised a sixth time after spec-review round 6, whose finding is the mirror image of round 5's:
not a predicate that under-reaches, but two of this item's own checks ORDERED to spell, inside
`tests/test_identity_endgame.py`, a literal two other checks assert at ZERO across a root that
contains that very module. Task 9's AC-4 clause names `_email_index` in its `attribute_reads_in`
attrs list while Task 6 scans both roots for that string; Task 12's clause (e3) and its
authorized-owner list name `PersonRepository._find_or_create_stub_legacy` while AC-1's frozen
scan takes both roots. Each goes RED at the boundary where it is written, against a CORRECT
build, at a boundary `## Verification` declares must be green — and the two cheapest repairs
available from that red are re-scoping Task 6's clause back to `PACKAGE_ROOT` (undoing round 5's
own fold and re-splitting one signed phrase across two scopes) and dropping an attribute from a
signed criterion's check. **The fold is a MODULE rule, not two clauses**: Task 2 had already
written the rule and the reason, scoped to plants alone, and the reason was never about plants —
a plant, a check's argument list, an owner qualname, a comment and an assertion message are the
same source text to a per-line literal scan. **D12 is new**: it states the rule over source LINES
of this item's own `tests/`-root modules, derives the three bound literals from
`## Verification`'s own zero-count table rather than listing them by hand, tables every site the
sweep returns — which found a THIRD ordered site the round did not name, Task 5's tripwire
building its owner list from D11's table — and declares the second disposition arm the sweep
forced (a spelling this item DELETES in the same commit as the assertion that forbids it, which
is how Task 4's parity legs and the two pre-existing tests-root sites are legal). The next rung
is swept and declared: what "assembled from parts" must mean so an assembly does not reconstitute
the literal on one line, the near-miss plants checked against that test rather than assumed
compatible, the non-`.py` artifacts (`prose_surface_cut0.json` must carry `_email_index`
verbatim and is out of every scan's universe by file type), the reverse direction (a package
write breaking a tests-root zero), the tests-root modules this item does not write, and the one
PATTERN-shaped member of the class. Two non-blocking notes are also taken: `## Verification`'s
non-vacuity table gains the row its own generating rule returns for Task 13's third control, and
the two-sentence P1/P5 repair's span is corrected to `:683-686` in both places that state it. No
`## Acceptance Criteria` text was touched this round either.*

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

**The seeder refuses a `dest` the library would silently replace (threat model M1–M3's own
mechanism, folded here).** `seed_vault(roster, dest)` REFUSES a `dest` that
`obsidian_schemas/repositories/base.py:_is_unconfigured:86-91` would swallow — `None`, a blank or
whitespace-only string, or a value normalising to `Path(".")` — raising before it writes anything,
so a computed `dest` can never fall through
`obsidian_schemas/repositories/base.py:_resolve_vault_path:94-104` to `OBSIDIAN_VAULT_PATH`. The
reason is specific to where this module lives and is not hygiene: `_resolve_vault_path` takes the
explicit argument OR the env var and raises only when BOTH are unconfigured, that variable IS set
on Dave's machine, and the standing wall that forbids caller-independent defaults
(`tests/test_vault_path_required.py:test_no_implicit_vault_path_defaults:312-331`) scans
`obsidian_schemas/` and `scripts/` only — D10's own row says so — while this seeder is under
`tests/` deliberately (D3, to stay outside `test_write_routing.py`'s universe), which is precisely
what puts it outside that wall. A seeder handed a swallowed `dest` writes ten `@<name>.md` notes
into the live 1147-note vault. The refusal is the guard the wall would have been, at the one door
every seeding goes through.

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
    {"ordinal": 1, "arm": "name",       "query": "Jane Roe",      "expected": "Jane Roe"},
    {"ordinal": 2, "arm": "name-token", "query": "Jane",          "expected": "Jane Roe"},
    {"ordinal": 8, "arm": "email",      "query": "kit@localhost", "expected": "Kit Baldwin"}
  ]
}
```

`expected` is the resolved `person.name`, or `null` for a `None` answer.

**The resolve golden's `arm` vocabulary is CLOSED at five values, and `arm` participates in the
re-derivation comparison.** D3 fixes the stub golden's four arms by name (`per-email`,
`per-phone`, `per-company`, `not-present`); the resolve golden's are `name`, `name-token`,
`alias`, `email`, `phone` — one per clause of D3's query derivation, in that order within each
note. Nothing else is legal. The tripwire re-derives the whole `(ordinal, arm, query)` TRIPLE
from `roster.json` and compares all three fields, not the query string alone: an `arm` label is
the only record of WHICH derivation clause produced a query, so a re-derivation that agreed on
the strings while disagreeing on the clause would be a silently reshaped space. The ordinals in
the snippet above are the real ones and are worth reading as a worked check of D3's order —
`Jane Roe`'s four queries take 1–4, so `Kit Baldwin` the NAME is ordinal 5 and `kit@localhost`
is ordinal 8, not 5.

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

**And one more literal, which is the SHARED-VAULT tripwire rather than a re-record tripwire.**
The same check carries `("Jane Roe <jane.roe@example.com>", "Jane Roe")` as a literal in its own
source and asserts the resolve golden holds it. That row is the one query whose recorded value
differs between the two possible recorder shapes: recorded against the roster's bytes it is
`Jane Roe`, and recorded in a vault AC-1's stub sweep has already run in it is `None`, because
the writeback rebuilt `emails[]` and the bracketed key is gone (D3(b)). So a recorder that
shares one vault between the sweeps — the shape D3(b) forbids — is RED at Task 5 with the
diagnosis already written down, instead of being discovered as an unexplained diff against
clause 2's `(" dana@example.com ", None)`.

### D3 — Cut 0: the oracle

**(a) Repair the parity legs.** `tests/test_resolve_or_create.py:190` and `:214` currently
compare `parse_identifiers(...) + resolve_or_create(...)` against itself, because the Phase-4
adapter swap made `find_or_create_stub`
(`obsidian_schemas/repositories/person.py:find_or_create_stub:688-697`) *be* the engine. Point
the "legacy" leg at `_find_or_create_stub_legacy` so the six cases compare two implementations
again. They are deleted at Cut 4 (AC-1 requires it); their value is the three cuts in between,
which is exactly the window E1 says the oracle must survive.

**(b) Record both goldens — and each sweep gets its OWN freshly-seeded temp vault.**
`tests/record_identity_golden.py` — a one-shot recorder, run by hand once at Cut 0 and never
again. It derives the case list and the query list from `roster.json` by the rules below, then
seeds **two independent temp vaults** from that same roster and runs AC-4's read-only resolve
sweep in the first and AC-1's mutating stub sweep in the second, both against **unchanged**
code, and writes the two JSON files.

**The same run records a THIRD frozen artifact, and it reads no vault at all.**
`tests/fixtures/identity_endgame/prose_surface_cut0.json` is
`prose_lines(python_files_under(PACKAGE_ROOT))` filtered to
`obsidian_schemas/repositories/person.py`, as `{"schema_version": 1, "recorded_at": "cut-0",
"lines": [{"owner": …, "line": …, "text": …}, …]}` — the pre-cut prose surface D11's disposition
rule is checked against. **It is not a third golden and the item still has exactly two** — a
golden records an ANSWER the code gave and is replayed by a criterion; this records what the code
SAID, is replayed by nobody, and is read only by Task 12's diff. It shares the recorder and the
baseline moment for the one property it does share with them: after the first prose edit it can
no longer be re-derived, so the only moment it can be captured is this one. It is read from the
file's bytes rather than from a seeded vault, so it stands outside the two-vault rule; and
`recorded_at: "cut-0"` is asserted by the same tripwire clause the goldens carry.

**Why two seedings, named as a mechanism rather than asserted as hygiene.** AC-1's sweep does
not merely append to the vault — it REWRITES two of E7's three email plants, through the WI-021
semantic gate, and nothing about that is visible from AC-1's own text. Hand-executed for case 1
(`Jane Roe`, `email="Jane Roe <jane.roe@example.com>"`): `Email.parse` yields
`jane.roe@example.com`, which misses `_email_index`'s bracketed-literal key, so the case falls
through to Branch B, reuses on exact-name at 1.0, and calls `_writeback_identifier`
(`obsidian_schemas/repositories/person.py:_writeback_identifier:1149-1180`) with the PARSED
address — which is not an element of `person.emails`, so the write fires rather than no-opping.
`_writeback_identifier` routes through `update_fields`, which hands the delta to the semantic
gate (`obsidian_schemas/repositories/base.py:update_fields:473-475` —
`frontmatter.update(gate_write(updates, declared_type=…, whole_record=False))`), and the gate's
`emails` arm (`obsidian_schemas/name_gate.py:gate_write:387-404`) runs `split_address` over
every entry and rebuilds the list from the parsed address, so
`["Jane Roe <jane.roe@example.com>", "jane.roe@example.com"]` collapses to
`["jane.roe@example.com"]`. **The angle-bracket plant is destroyed**, and `whole_record=False`
means the M1/M2 migrations do not even preserve the display half in `aliases:`
(`name_gate.py:385`). Case 3 (`Dana Okafor`, `" dana@example.com "`) goes the same way:
`split_address(" dana@example.com ")` returns `("dana@example.com", "")`
(`obsidian_schemas/name_gate.py:split_address:97-135`, with `Email.parse` stripping at
`obsidian_schemas/identifier.py:Email:159`), so the entry becomes `"dana@example.com"` and the
rebuilt index gains the UN-padded key. Case 2 (`Kit Baldwin`) is untouched: `Email.parse`
refuses `kit@localhost`, so `parse_identifiers` yields no identifier at all, `email_str` is
`None` (`resolve_or_create:887`) and Branch B's writeback is a genuine no-op.

Recorded in that mutated vault, the resolve golden would contradict E7's table on two of its
three rows: `Jane Roe <jane.roe@example.com>` → **None** (the bracketed key is gone, step 4 gets
0 digits, step 5 finds no whole-word token) instead of `Jane Roe`, and `" dana@example.com "` →
**Dana Okafor** (`resolve` strips at `:480` and the un-padded key now hits) instead of `None`.
The first makes the angle-bracket query a THIRD query that moves at Cut 1, which AC-4 declares
RED; the second goes red against D2 tripwire clause 2's own literal
`(" dana@example.com ", None)`. Both reds land at Task 5 with no diagnosis in front of the
builder, and the cheapest-looking repairs from there — edit the literal, or re-record the
golden — are precisely the defeats E7 and R3 exist to close. So the recorder seeds per sweep:
the resolve golden is recorded against the roster's committed bytes, and the stub sweep's
mutation is confined to a vault nothing else ever reads.

**This is NOT the second vault E8 rejected, and the two statements do not collide.** AC-4's "there
is no second or throwaway vault" and E8's rejected arm (b) are both about a second ROSTER — a
differently-populated fixture built to dodge the alias/email collision. There is still exactly
ONE roster, ONE declaration and ONE baseline moment; what is per-sweep is the temp DIRECTORY the
one roster is seeded into, which is already what every acceptance check does on every run (see
the Edge Cases entry on first-run-versus-subsequent-run). Stated as a total rule so a later
reader cannot get it wrong by adding a sweep: **every sweep that WRITES runs in its own
freshly-seeded temp vault, and no sweep ever reads a vault another sweep wrote.** Of the sweeps
this item ships, exactly one writes — AC-1's, via Branch C's mints and pre-cut Branch B's
writeback; AC-2's four-door sweep, AC-3's `get_by_phone` lookups and AC-4's golden replay are
all read-only.

It lives under `tests/`, NOT under `scripts/`, and that is load-bearing rather than tidy: it
writes files with `Path.write_text`, and `tests/test_write_routing.py:91` sweeps
`python_files_under(PACKAGE_ROOT, SCRIPTS_ROOT)` for exactly that capability outside
`obsidian_schemas/vault_io.py`. A recorder in `scripts/` is RED on a standing wall before it
runs. The same applies to `tests/identity_fixture.py`.

**And that placement is exactly what puts the recorder outside the vault-binding wall, so it
carries its own (threat model M1, folded here).** Every `PersonRepository` the recorder constructs
is passed the explicit temp path that run just seeded, and the recorder REFUSES — before any sweep
writes — if a constructed repository's resolved `vault_path` is not that path. Construction goes
through one helper in the recorder rather than being spelled at each site, so "every repository"
is a property of the module rather than a habit: the helper builds `PersonRepository(dest)`,
compares `repo.vault_path` (`obsidian_schemas/repositories/base.py:BaseRepository.__init__:144`
assigns it from `_resolve_vault_path`) against the `dest` it was handed, and raises if they differ
or if `dest` is
one `_is_unconfigured` would swallow. This is not belt-and-braces on top of D1's seeder guard;
it closes a different door. **Task 5 runs this module BY HAND, once, outside pytest, from the tree
root with Dave's ambient environment** — the one invocation in this whole item that does — and it
executes AC-1's MUTATING sweep. A repository constructed there without the seeded path binds to
`OBSIDIAN_VAULT_PATH` and mints D3's ten not-present notes (`Wilbur Achebe`, `Greta Oyelaran`, …)
into the live vault, and pre-cut Branch B's `_writeback_identifier` then rebuilds real notes'
`emails:` through `gate_write`. That is data loss in Dave's vault from a `tests/`-root script, and
no standing check in this repo reaches it: the seeder's guard catches a swallowed `dest`, and this
catches a repository built with no `dest` at all, or with one the library then resolved elsewhere.
The refusal fires before the first write, not after it, because after it there is nothing left to
refuse.

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
either side. The pairs are identical; what differs is the SIDE EFFECT — pre-cut Branch B calls
`_writeback_identifier`, post-cut Branch A does not.

**E5's exclusion is about the parity contract's RETURN VALUES, and that is exactly as far as it
reaches.** It does not license a side effect that rewrites the oracle's own substrate, and (b)
above shows this one does: the writeback rebuilds `emails[]` through the semantic gate and
destroys two of E7's three plants in the vault it runs in. Two facts hold it harmless, and both
are stated rather than assumed. **Within** the stub sweep, no later case reads a rewritten
value: the case list is frozen data derived once from `roster.json`, never re-derived from the
mutated vault, and no case other than 1 and 3 queries Jane's or Dana's address in any form —
the twenty tokens of invariant 1 and the ten fresh not-present addresses are disjoint from both.
**Across** sweeps, nothing else runs in that vault at all, because the recorder seeds one vault
per sweep (b) and every acceptance check seeds its own.

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
   unchanged — it still returns `Optional[Person]` and still raises nothing. **One input shape
   moves and it is named rather than covered by that sentence:** `get_by_email(None)` raises
   `AttributeError` today, at the `email.lower()` of
   `obsidian_schemas/repositories/person.py:get_by_email:390`; post-cut `Email.parse(None)`
   raises `IdentifierError` (`obsidian_schemas/identifier.py:Email:145-146`), which this arm
   catches, so the call returns `None`. That is a WIDENING of accepted input, not a change to
   the documented exception set — nothing new is raised, and the one thing that stops being
   raised was never a documented answer. No consumer relies on the crash (the three consumers
   catch `NameValidationError`/`WeakIdentityError` off the write door, not `AttributeError` off
   a read), and the build log records the shift.
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
6. **Every OTHER prose surface in this file that this cut falsifies is repaired in the same
   commit, and they are not a list to remember — they are a derived class.** `__init__:160-167`,
   `_index_entity:193`, `_project_identifiers:231-234` and `:252`, `_index_identifiers:271-273`
   and `_resolve_identifier:949-951` all assert, in one way or another, that the per-kind dicts
   are still the permissive email surface. **D11 states the generator, the derived census, the
   per-site repair and the total rule that makes the enumeration fail LOUD rather than pass by
   assumption** — item 5 above is one member of that class, and reading this numbered list as
   total is the mistake D11 exists to stop.

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

Stated as the one requirement its two halves are: `get_by_phone`'s fuzzy scan iterates a
materialized snapshot of `_phone_index` rather than the live mapping `_clear_indexes:326-333`
mutates in place, and that is asserted by the stronger predicate above — every package `for` loop
whose iterable reaches `self._phone_index` is wrapped in `list`/`tuple`/`sorted`/`frozenset`/`dict`
— never by AC-3's "the iterable is a call" gloss, which is vacuously green against unchanged code.

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
- **This rider list is NOT total either, and D11 is why.** The three riders above plus D4 item 5
  are four members of one class — prose in `person.py` describing a mid-transition state these
  cuts end. `find_or_create_stub:682-685`, `resolve_or_create:851`/`:858-863`/`:871`/`:874`/
  `:878-879`/`:912`, `resolve:462-467` and **`resolve_all`'s own docstring at `:519-523` and
  `:534-539`** (the P4 restatement and the conflated company-bump arithmetic, which land in Task 9
  with the rest of that docstring's repair) are further members that Cuts 3 and 4 falsify; **D11
  enumerates all of them, states which task lands each, and closes the class with a disposition
  rule over an enumerated surface rather than with this list — a list that has now been one member
  short in three consecutive rounds, which is why it says so here rather than being trusted.**

### D8 — Four new derivations, and why they go in `tests/derivations.py`

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
| `prose_lines(files)` | D11 / Task 12 | every COMMENT line and every STRING-LITERAL (docstring) line in each file, as `(module, line, owner, text)` — `owner` being the innermost enclosing `def`'s qualname from `_iter_functions`, or the enclosing class's qualname, or `<module>` |

`tests/test_loud_fail_harness.py:test_derivations_are_single_sourced:74-97` asserts a **required
subset** of six named exports, explicitly "not a cardinality bound", so four more exports join
legally.

**Two clauses `attribute_reads_in` needs stated rather than left to the builder**, because Task 2
plants both cells and neither is decidable from the table row above. It collects **LOADS only** —
an assignment to a named attribute is a `Store` and is not a read, which is AC-4's own word
("does not itself read `_cache`, `_alias_index`, `_email_index` or `_phone_index`"). And a read
inside a **nested `def`** is attributed to the enclosing NAMED qualname by the same
`.<locals>.`-folding rule `prose_lines` uses below, so the two predicates answer the
nested-definition question identically rather than one of them being discovered to differ a round
later.

**`prose_lines`' rule, total, because its whole job is to be the surface nothing falls out of.**
It is the FINDING predicate D11 is re-founded on, so a member it cannot see is a member no
reading pass can be blamed for missing:

- Tokenize the file (`tokenize.generate_tokens`, not a regex and not a `startswith("#")` line
  scan). The two shapes that defeat a line scan defeat it in OPPOSITE directions, and conflating
  them under one "defeats a line scan" gloss is what produced round 5's finding, so they are
  stated apart. A `#` inside a STRING LITERAL is a false POSITIVE for a line scan: the line owes
  NO record. A `"""` inside a COMMENT is a STATE-TRACKING failure: the line itself IS a comment
  and DOES owe exactly one record, and what the line scan gets wrong is the ORDINARY CODE
  FOLLOWING it, which it swallows as a docstring body. The live specimen of the second is
  `tests/test_vault_path_required.py:_code_lines:295-304` — the shipped helper Task 13 runs,
  which sets `in_docstring` on any line holding an odd count of `"""`, trailing comments
  included. This predicate is the one place in the item where under-reach is the failure mode.
  `tokenize` is a NEW import in `tests/derivations.py`; that is legal and adds no wall
  membership, because the two single-homing walls pin `ast` alone
  (`tests/test_loud_fail_harness.py:103`, `tests/test_name_gate_wall.py:1136`) and
  `tests/test_write_routing.py`'s `module_import_uses` universe is
  `PACKAGE_ROOT + SCRIPTS_ROOT`, which excludes `tests/`.
- Emit one record per LINE of every `COMMENT` token and every `STRING` token that is an
  expression statement (a docstring — module, class or function), so a multi-line docstring
  contributes one record per line and the caller can pin a single sentence.
- `owner` is resolved from `_iter_functions`' `(FunctionId, node)` spans (`node.lineno` ..
  `node.end_lineno`) and from `ast.ClassDef` spans, taking the INNERMOST enclosing definition —
  except that a nested `def` whose own qualname carries `.<locals>.` is attributed to its
  outermost non-local ancestor, so `resolve_all`'s inner `record` helper contributes to
  `PersonRepository.resolve_all` rather than dropping out of a qualname-scoped sweep. Prose
  outside every definition gets `<module>`.
- `text` is the SOURCE LINE with leading and trailing whitespace stripped — not the token's own
  text, so a comment and the code it trails yield one record carrying the whole line, and a
  docstring line yields the line as written. That is total over `COMMENT` tokens and takes no
  notice of what the comment SAYS: a trailing comment containing `"""` is a `COMMENT` token like
  any other and yields its one record, which is the collected half of the pair above. Stripping
  is what lets Task 12 clause (e1) compare
  verbatim WORDING while tolerating an indentation change from an authorized neighbour's reflow.
  Lines that are empty after stripping contribute no record, so a docstring's blank separator
  lines are not surface.
- The `<module>` owner is not a residue class to be waved past: it is where the dangling
  `docs/paren-decoration-at-the-door.md` pointer actually lives (`:110-113`, attached to
  `_TRAILING_PAREN_RE` and OUTSIDE `_split_trailing_paren`, which starts at `:117`). A surface
  scoped to "the functions this item edits" would have missed it — which is why the surface is
  the whole file, partitioned by owner, rather than a set of functions.

**`docs_markdown_mentions`' rule, total, with its exclusion class named** — the data-premise
gate's counterexample hunt found three members that are false BY DESIGN and are not
dispositioned anywhere else in this document:

- Match `[A-Za-z0-9._/-]+\.md` per line over the file's whole text (comments and docstrings
  alike). That is deliberately BROADER than AC-5's wording, which says "named in a comment", and
  broader in the safe direction — it can only add mentions the resolve clause must satisfy, never
  drop one. It was checked to be satisfiable rather than assumed: at HEAD every `.md` mention
  anywhere in `obsidian_schemas/` sits in a comment or a docstring (no code constant names one),
  and of those, exactly three are in scope — `docs/company-name-corpus-audit.md` at
  `name_validation.py:40` and `:347`, which resolves, and `docs/paren-decoration-at-the-door.md`
  at `person.py:113`, which does not and which Task 10 deletes.
- The starts-with-`docs/` test is applied to the MATCHED TOKEN, never to the line: the character
  class includes `/`, so the match is greedy leftwards and swallows any leading path segment,
  which is exactly the mechanism the exclusion below relies on.
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

**And it declares its docs-corpus coupling in its own docstring, because AC-5's check reads a
live `docs/**` artifact at run time.** `tests/test_identity_endgame.py` reads
`docs/identity-cutover-corpus-audit.md` and pins its SHAPE, which is a fixture reaching into a
corpus the factory's own splitter may rewrite on an ordinary ship. This repo's convention for
that is a one-line `CORPUS_COUPLING:` declaration in the reading module's own docstring —
`tests/test_company_name_contract.py:15` and `tests/test_ac_interpreter.py:23` both carry one,
and Task 14 already updates the second — so this module carries one too, naming the document it
reads and the property it consumes (the artifact's declared section/field shape, not its
numbers). It is the arm this item can take honestly: the artifact is a conductor-committed
precondition whose bytes are frozen in HEAD, so neither "derive it from the corpus's own code"
nor "carry frozen bytes" applies, and the declaration is what lets the next reader falsify the
coupling in the same breath it is made.

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
| `tests/test_loud_fail_harness.py:test_derivations_are_single_sourced` | `python_files_under(PACKAGE_ROOT, TESTS_ROOT)`, set EQUALITY | no new module names `ast`; all four new predicates are exports of `tests/derivations.py` |
| `tests/test_name_gate_wall.py:_check_the_ast_capability_stays_single_homed` | same, set EQUALITY | same |
| `tests/test_name_gate_wall.py:_check_the_loud_fail_write_universe_in_the_removal_direction` | `non_completed_write_sites([person.py])`, pinned to five qualnames and eight sites | unchanged: the functions this item edits or deletes contain no `write_text`/`write_bytes`/`write_note`/`create_note`/`move_note` attribute call, so none of them is in that universe |
| `tests/test_loud_fail_write.py:test_write_failure_raises_and_noops_keep_their_return` | `non_completed_write_sites(python_files_under(PACKAGE_ROOT))`, bidirectional classification | same |
| `tests/test_concurrent_access.py:test_wi020_derivations_survive_the_routing` | four derivations over `PACKAGE_ROOT`, count pins 4 / `write_markdown_file` / 8 / 4 / 3 | unchanged: no repository subclass, no `_load_file`, no reserializing writer is touched |
| `tests/test_write_routing.py` | `filesystem_mutation_uses`, `os_module_attribute_uses`, `module_import_uses` over `PACKAGE_ROOT + SCRIPTS_ROOT` | `person.py`'s edits name no filesystem-mutation capability; the recorder and seeder are under `tests/`, outside this universe, which is WHY they are there — and so is `tests/derivations.py`, which is why `prose_lines`' new `tokenize` import joins no `module_import_uses` population |
| `tests/test_company_name_contract.py:test_company_name_punctuation_survives_every_write_arm` | `character_class_strip_sites` + `frontmatter_write_arms` over `PACKAGE_ROOT + SCRIPTS_ROOT`, bidirectional | unchanged: `person.py` contributes no `write_frontmatter` arm and no character-class strip; the deleted function contains neither |
| `tests/test_address_splitter.py:test_address_splitting_is_single_homed_and_agrees_with_email_parse` | `address_splitting_implementations` over `PACKAGE_ROOT + SCRIPTS_ROOT`, exactly one home | unchanged: the one home is `name_gate.split_address`; nothing this item writes splits an address |
| `tests/test_vault_path_required.py:test_no_implicit_vault_path_defaults` | `(REPO_ROOT/"obsidian_schemas"\|"scripts").rglob("*.py")` | `person.py`'s edits introduce no caller-independent default path |
| `tests/test_vault_path_required.py:test_docs_do_not_advertise_no_arg_construction` | `REPO_ROOT.rglob("*.md")` minus `.git/.venv/docs/state/node_modules` | **this item adds no `.md` under `tests/`** — the fixture is JSON and the vault is seeded into a temp directory, so nothing joins this population |
| `tests/test_ac_interpreter.py:check_module` | `TESTS_ROOT.glob("test_*.py")`, unique `def <check>(` | the five check names appear in exactly one module, `tests/test_identity_endgame.py` |
| `tests/test_vault_path_required.py:NO_ARG_CONSTRUCTION` — the PATTERN, run by this item over a universe no standing wall covers (threat model M3) | this item's own `tests/`-root `.py` files, code lines only via `tests/test_vault_path_required.py:_code_lines:281` | zero `\w+Repository\(\s*\)` matches (the pattern is IMPORTED, never re-spelled — this cell transcribes it only to say what it means) in `tests/identity_fixture.py`, `tests/record_identity_golden.py`, `tests/test_identity_endgame.py`, `tests/derivations.py`, `tests/test_resolve_or_create.py`, `tests/test_wi126_body_preservation.py`, `tests/test_identity_index.py` and `tests/test_ac_interpreter.py` — **and, per file, that the borrowed line scan cannot have swallowed code**: no line `prose_lines` returns for these files carries a `#` whose trailing text contains `"""` or `'''`, because `_code_lines:295-304` is the `startswith`/delimiter line scan D8 refuses and one such comment silently eats every code line beneath it, which would make this zero an under-reach that reads like a clean scan |

Anything the RUN returns that this table did not name is NAMED in the Build Log and satisfied —
never worked around, and never satisfied by narrowing the wall.

**The last row is an ADDITION to the 2026-09-06 census, not a member of it, and the distinction is
the census's own floor discipline.** The first eleven rows are walls that already sweep this item's
files; the twelfth is a wall-shaped hole. `tests/test_vault_path_required.py` ships the pattern
that names the defect (`NO_ARG_CONSTRUCTION` at `:382`) and two consumers of it, and NEITHER reaches
a `tests/`-root Python module: `test_no_implicit_vault_path_defaults:312-331` scans
`obsidian_schemas/` and `scripts/` only, and `test_docs_do_not_advertise_no_arg_construction` scans
`*.md`. This item adds three repository-constructing modules under `tests/` — two of which WRITE —
so it inherits the obligation the wall would have imposed had its universe reached them, and Task 13
discharges it by running the shipped pattern rather than by re-implementing one. Adding the row does
not falsify the census's date-stamp: the sweep that produced the eleven asked which walls REACH these
files, and this row exists precisely because none does. `tests/test_vault_path_required.py` is
IMPORTED and never edited — it is not a `## Write Targets` path, `## Scope Boundary` keeps it
unchanged, and importing its pattern is what makes this scan track the wall's own meaning instead of
freezing a copy of it.

### D11 — The strangler-prose class: the generator, the enumerated surface, and the disposition rule

Three reviewing rounds have now found the same shape at different sites — an enumeration this
document treats as total that is one member short of the surface it covers. Round 2 found it in
the very list D4 item 5 edits. **Round 3 found it in the fold written to close it**: the first
version of this section derived its census from six hand-picked markers plus a reading pass, and
the reading pass missed `resolve_all`'s own docstring, which carries two members ninety lines
above the comment the census DID name.

So closing sites is not the fold, and neither is adding a row. **Two things generate the class,
and the section states both.** The SUBSTANTIVE generator is that `person.py`'s prose describes
the WI-125 strangler's MID-TRANSITION state, and describes `resolve()`'s cascade AS A BODY; this
item ends both. The PROCEDURAL generator — the one that has produced a finding in each of the
last two rounds — is that the census's own finding predicate was a marker set, so the markers
decided which sentences got read, and a member carrying no marker was invisible to the reading
step as well. That half is closed by replacing the predicate with a surface enumerated at source
(`prose_lines`, D8) and a **disposition rule over owners** that a machine checks in both
directions. The needle tiers survive as what they should always have been: a cheap regression
pin over sentences already read, never the thing that decides which sentences get read.

A sentence in that file is falsified iff its truth depends on one of five propositions:

- **(P1)** `_email_index` exists. *(ended by Cut 1)*
- **(P2)** the per-kind dicts are the permissive/legacy lookup surface for EMAIL, so a
  malformed-but-present entry still resolves the old way. *(ended by Cut 1)*
- **(P3)** collapsing the dicts into views of `_identifier_index` is an open LATER cut.
  *(ended by Cut 1 for email and closed permanently by E5 for the rest — there is no `Alias`
  type and `slack` is unprojectable, so the remaining three dicts are not "not yet collapsed",
  they are never collapsible)*
- **(P4)** `resolve()` has a five-step body of its own, tried in that order. *(ended by Cut 3)*
- **(P5)** `_find_or_create_stub_legacy` exists and is the Phase-5 parity baseline / rollback.
  *(ended by Cut 4)*

**The surface, enumerated at source.** `prose_lines(python_files_under(PACKAGE_ROOT))` is the
finding surface: every comment line and every docstring line in the package, each with its owning
definition. Two facts about that surface decide everything below.

- **The marker scan located the file, not the members.** A per-line literal scan for the markers
  `_email_index`, `_find_or_create_stub_legacy`, `Phase-5`, `per-kind`, `permissive lookup` and
  `Tries in order` returns **21 matched lines in exactly ONE file**,
  `obsidian_schemas/repositories/person.py` (21 is a count of matched LINES, not of markers —
  `:675` carries two). That one-file result is the first rung of the ladder swept and DECLARED,
  not assumed: no other module under `obsidian_schemas/` carries a member. It is retained for
  exactly that — scoping the READING to one file — and for nothing else.
- **The reading is over the whole of that file's prose surface, partitioned by owner.** Not over
  the marker hits, and not over "the functions the cuts edit" either: the members are
  `_index_entity:193` (no marker), `resolve_all:519-523` and `:534-539` (no marker, and ninety
  lines from anything the earlier census named), and the `<module>`-owned dangling pointer at
  `:110-113`, which is outside every function this item touches. Any predicate narrower than the
  file's whole prose surface loses at least one of those four.

**The disposition rule — this, and not the table, is the fold.** Every prose line in `person.py`
belongs to exactly one owner, and every owner has exactly one disposition:

> An owner is AUTHORIZED iff the table below orders it a PROSE repair — at least one Cut-0 prose
> line of its own rewritten or deleted. A Cut-0 prose line whose owner is NOT authorized must
> survive the build **verbatim**; every authorized owner must show at least one Cut-0 line gone
> (the repair landed); and `PersonRepository._find_or_create_stub_legacy` must own **zero** prose
> lines at the end. Both directions quantify over the CUT-0 surface's own owners, so an owner this
> item CREATES is in neither. Anything the run returns that this table did not name is NAMED in
> the Build Log and repaired — never worked around, and never satisfied by narrowing the scan.

That rule is total in both directions and needs no marker: the Cut-0 surface is recorded as
committed data beside the goldens (`prose_surface_cut0.json`, D2/D3(b)), so an unauthorized
rewrite is RED and an authorized repair that never landed is RED. What it deliberately does NOT
claim is that the unauthorized lines are TRUE — no check can decide that. What it buys is that
the set of sentences a reviewer has to have read is a machine-produced list rather than a
reader's recollection, and that the list is frozen where the next round can audit it once instead
of rediscovering one member per round.

**Why that rule is worded over PROSE repairs and not over edited functions — round 4's finding,
and it is the same generator one level down.** The first version of this rule read "an owner is
authorized iff it appears in the table", and the set it pointed at was derived from D4/D5/D6/D7's
**edit lists** — that is, from which functions the CUTS TOUCH. But the surface the rule runs over
is `prose_lines`' output, which emits records only for `COMMENT` and docstring `STRING` tokens
(D8): a CODE line is not on it. So an owner authorized for a code-only edit is an owner the
"at least one Cut-0 line gone" direction is FALSE about by construction, and the check ships RED
against a correct build. One of the fifteen was exactly that (`_clear_indexes`), and a second
(`select_resolution`) failed the same direction for the sibling reason that it does not exist at
Cut 0 at all; the cheapest repairs available
from that red were the two things this section forbids in substance — rewrite a true docstring so
a line "goes", or narrow the check by adding an exclusion nobody declared. The repair is a change
of the AUTHORIZATION PREDICATE, not an exemption list bolted onto the check: **authorization is a
statement about PROSE, never about code.** Re-derived from the prose obligation, the set is
**thirteen** and the two are outside it for two different structural reasons, each of which is a
CLASS and not a case:

- **An owner whose code changes but whose prose does not is NOT authorized, and (e1) then pins its
  prose verbatim.** `PersonRepository._clear_indexes` is the whole of that class today. It owns
  exactly one prose line, the docstring `"""Clear custom indexes on refresh."""` at `:327`, which
  is TRUE and which this section orders KEPT; what Cut 1 deletes is `self._email_index.clear()` at
  `:328`, a code line `prose_lines` never emits. Under the old wording it was authorized (so its
  true docstring was unpinned) and (e2) demanded a deletion that could not occur. Under this
  wording it is unauthorized, which is strictly stronger in both directions: (e2) does not bind it,
  and (e1) now requires that docstring to survive **verbatim** — which is what the table always
  said should happen and what nothing was checking.
- **An owner this item CREATES is not a Cut-0 owner at all, so it is in neither direction.**
  `select_resolution` is the whole of that class today; Task 9 creates it. (e1) quantifies over
  Cut-0 lines and it has none, so (e1) is vacuous for it correctly; (e2) quantifies over the Cut-0
  surface's owners and it is not one, so it is not exempted from (e2) — it never enters. It keeps
  its table row, marked as the one row that is deliberately NOT an authorized owner, so the table
  stays a complete reading of the surface plus the one owner the build adds.

**The next rung, swept and DECLARED** — because the generator here is "a rule quantifying over a
domain whose members do not all satisfy it", and closing two members is not closing that:

- **Every other direction of the rule, checked for the same defect.** (e1) quantifies over Cut-0
  LINES, which by construction all exist — no member can fail to have one. (e3) quantifies over one
  named owner whose whole function is deleted, so its domain is a singleton and it is TRUE of it.
  Only (e2) quantified over a set that could contain a non-satisfier, and it is the one repaired.
- **Per-OWNER versus per-ROW, which is where a two-member exemption would have been wrong.** The
  table is keyed by SITE, and four rows carry `—` in the "falsified by" column. Two of those rows'
  owners still lose a Cut-0 line elsewhere and remain authorized: `get_by_phone:416`'s comment IS
  replaced at Task 8, and `_project_identifiers:238-242` survives while its owner loses
  `:231-234`, `:236-238` and `:252`. A rule written over ROWS with a `—` would have swept both in
  and gone RED on a correct build in two more places. The predicate is per-OWNER, and the two
  non-members above are the owners for which EVERY row is `—`-or-absent.
- **The same question one level out, at the file.** `prose_lines` runs over
  `python_files_under(PACKAGE_ROOT)` and clause (e) filters to `person.py`; no other package module
  has an authorized owner, so no other file can carry an owner the rule is false about. Declared
  rather than assumed, and it is the same sweep the "other package modules" rung below records.
- **And the direction nobody has checked: an authorized owner that loses a line for the WRONG
  reason.** (e2) cannot distinguish "the ordered repair landed" from "some other line of the same
  owner vanished". That is a real residual and it is not closed here, because closing it means
  pinning per-LINE repairs, which is the needle tier's job — Tier A and Tier B pin named sentences
  of the authorized owners at zero, and clause (c) pins two replacements as present. Which owners
  those cover is read off the two needle tables' own site columns, never restated as a count here.
  Named so the next round finds it recorded rather than fresh.

**The authorized owners, and why the set is what it is.** **Thirteen**, derived from the PROSE
repair each is ordered — not from D4/D5/D6/D7's edit lists, which is the derivation round 4
falsified: `<module>` (the `:110-113` pointer), `PersonRepository.__init__`, `._index_entity`,
`._project_identifiers`, `._index_identifiers`, `._remove_entity_from_indexes`, `.get_by_phone`,
`.resolve`, `.resolve_all`, `.find_or_create_stub`, `._find_or_create_stub_legacy`,
`.resolve_or_create`, `._resolve_identifier`. Each of the thirteen has at least one Cut-0 prose
line the table orders rewritten or deleted, and the table's `lands in` column names the task for
every one; that correspondence is what makes the (e2) direction true of the whole set rather than
of most of it.

**Four absences are deliberate and are the rule doing work rather than oversights.** Two are
owners whose prose the item simply does not touch: **`_split_trailing_paren` is NOT authorized** —
its docstring is true and the dangling pointer four lines above it belongs to `<module>` — and
**`get_by_email` is NOT authorized**, because D4 item 2 leaves its signature, return type,
exception set and therefore its docstring untouched while rewriting its body (its body carries no
comment at all, so the owner contributes exactly its docstring to the surface). The other two are
round 4's finding and are the two structural classes stated above: **`_clear_indexes` is NOT
authorized** — Cut 1 deletes a CODE line inside it (`:328`) and `prose_lines` never emits code, so
its one true docstring at `:327` is pinned VERBATIM by (e1) instead — and **`select_resolution` is
NOT an authorized owner** because Task 9 creates it, so it owns no Cut-0 prose and enters neither
direction. If a build rewrites any of the four's prose, that is a red the builder must justify in
the Build Log, which is the point.

**The table: the per-site reading of that surface, run 2026-09-06 over `prose_lines`' output, with
round 4's missing ROW and round 5's missing SITE added.** Its `owner` column is the thirteen
authorized owners **plus exactly
two declared non-members**, each labelled in place — `_clear_indexes` (authorized-looking because
Cut 1 edits its body, but ordered no prose repair) and `select_resolution` (created by this item).
Every authorized owner appears here and every owner here is either authorized or one of those two,
so the set and the table cannot drift apart; round 4 found them one row apart in the other
direction — `_find_or_create_stub_legacy` was in the prose list with no row — and that row is now
present rather than the sentence being softened. Round 5's addition moves neither the thirteen nor
the two: `resolve_or_create:847-848` belongs to an owner that is already authorized and already
carries several rows, so the OWNER partition is untouched and only the SITE reading got one member
longer. Both axes are named because they fail independently — round 4's finding was an owner with
no row, round 5's is a site with no row under an owner that had three — and completeness on one
axis says nothing about the other.

| owner / site | the prose, and which proposition it rests on | falsified by | lands in |
|---|---|---|---|
| `<module>:110-113` | the dangling `docs/paren-decoration-at-the-door.md` pointer (not a P — a pointer that has been dangling since WI-121). Owned by `<module>`, NOT by `_split_trailing_paren`, which begins at `:117` | truth | Task 10 |
| `__init__:160-167` | "the dicts stay the permissive lookup surface (zero parity risk)"; "Collapsing the dicts into views of this map + deleting them is the strangler's later deletion cut." — **P2 + P3** | Cut 1 | Task 6 |
| `_index_entity:193` | `"""Build email, phone, and alias indexes."""` — **P1** | Cut 1 | Task 6 |
| `_project_identifiers:231-234` | "the legacy per-kind dicts remain the permissive lookup surface during transition, so a malformed-but-present field still resolves the old way while this typed index just omits it" — **P2** | Cut 1 | Task 6 |
| `_project_identifiers:236-238` | the "942 notes, 2026-06-13, ZERO failures" claim — staleness, not a P | 205 notes of drift | Task 10 |
| `_project_identifiers:238-242` | the slack carve-out note — TRUE, and it survives; it is authorized because Task 10 ADDS its `UNBLOCK:` line. `:242`'s "Company isn't activated this cut" is correct and must survive the same edit | — | Task 10 |
| `_project_identifiers:252` | `pass  # lenient — legacy per-kind dict still indexes it` — **P2**, four lines below the sentence D4 item 5 rewrites | Cut 1 | Task 6 |
| `_index_identifiers:271-273` | "byte-identical to the legacy per-kind dicts' overwrite semantics … so Phase-3 resolution through this index returns the same entity legacy lookups do" — **P2** | Cut 1 | Task 6 |
| `_clear_indexes:327` | `"""Clear custom indexes on refresh."""` — TRUE and it stays true. **NOT an authorized owner** (round 4): what Cut 1 deletes here is `self._email_index.clear()` at `:328`, a CODE line `prose_lines` never emits, so this owner is ordered no prose repair at all and (e1) pins this docstring VERBATIM. Task 6 edits its body and not its prose, which is precisely the distinction the authorization predicate now draws | — (code-only edit) | Task 6, body only |
| `_remove_entity_from_indexes:337` | `# Remove emails from index` — **P1**: it labels a loop Cut 1 deletes, and it dies with it | Cut 1 | Task 6 |
| `get_by_phone:416` | `# Fuzzy match with country code handling` — TRUE; Cut 2 replaces it with the non-transitivity comment that names E3's witness by test name | — | Task 8 |
| `resolve:462-467` | "Tries in order: 1. Exact name match 2. Alias match 3. Email match … 5. Partial name match" — **P4** | Cut 3 | Task 9 |
| `resolve_all:519-523` | "resolve() returns a single Optional[Person] **and stops at the first cascade hit**; resolve_all returns ALL plausible candidates ranked by confidence" — **P4, stated in the file's own words, in the docstring of the function `resolve` is about to be built on.** After Cut 3 `resolve` does not stop at the first cascade hit: it ranks the WHOLE cascade through `resolve_all` and applies `select_resolution`, which for a multi-token query rejects the only candidate the cascade found (D6, the 0.65 `token-subset` row). This is the member round 3 found; it is the second-most-read prose in the file after `resolve`'s own docstring, and leaving it would have contradicted `resolve`'s repaired docstring inside the same commit | Cut 3 | Task 9 |
| `resolve_all:534-539` | the company-hint paragraph, false on two counts and neither is a P: **(i)** "This catches `Emily M` + company=`Speechmatics` → canonical Emily Mendes **bumped 0.65 → 0.90** ≥ 0.85 cutoff for safe reuse" — hand-executed, `"Emily M"` cannot reach the 0.65 `token-subset` arm at all (`:607-608` requires `len(shared) >= 2` and it shares only `emily`), so step 6 records **0.6** at `:626` and the bump yields **exactly 0.85**, with no margin; the 0.65 → 0.90 arithmetic belongs to the two-shared-token Naomi Pavie case the same sentence also names, and the two are conflated. **(ii)** the rider "see the code at `person.py:~476`" — the bump is at `:628-651`. Both matter beyond tidiness: E8, D1 and architect round 4 all record that the corroborated short-form case sits precisely ON the threshold with no float slack, and this docstring tells its reader there is 0.05 of headroom — the identical misreading-invitation as `:615-617`, which AC-5 owns | pre-existing | Task 9 |
| `resolve_all:615-617` | the false sub-floor comment — truth, not a P | pre-existing | Task 10 |
| `find_or_create_stub:675-676` | "preserved verbatim as `_find_or_create_stub_legacy` — the Phase-5 parity baseline AND the one-commit rollback" — **P5** | Cut 4 | Task 11 |
| `find_or_create_stub:683-686` | "The legacy path indexed malformed values; the engine resolves on the typed ones and the name path." (**P1**, `:683-685`) and "The Phase-5 replay confirms zero return-value divergence over the real vault." (**P5**, `:685-686`) | Cuts 1 and 4 | Task 11 |
| `resolve_or_create:847-848` | "the identifier-first core that the **Phase-4 adapter will run** `find_or_create_stub` through" — **P5**, and **already false at HEAD**: `find_or_create_stub:688-696` runs through it today. It is the same false tense, in the same docstring, thirty lines above `:878-879`, which this table already carries; round 5's read found it. It is admitted because the class demonstrably takes pre-existing falsehoods (`:878-879`, `resolve_all:534-539`) and taking one member of a shape while leaving its twin is the exact generator this section exists to close — leaving it would have shipped a docstring whose repaired tail says the swap HAS happened while its head says it WILL. Line-WRAPPED (`the` ends `:847`, `Phase-4 adapter will run` begins `:848`), so like `:878-879` and `:949-951` it gets no needle of its own and is carried by its owner's named repair obligation instead | pre-existing | Task 11 |
| `resolve_or_create:851` | "the Phase-5 parity contract is `(resolved_name, created_new)`" — **P5** | Cut 4 | Task 11 |
| `resolve_or_create:858-863`, `:871`, `:874`, `:912` | "byte-identical to **legacy Strategy 1**", "(legacy Strategy 2)", "(legacy Strategy 3)", "= legacy best-hit" — **P5**: the referent is the body being deleted. The same span carries a **P1** clause at `:859-860`, "email/phone via the legacy fuzzy `get_by_email`/`get_by_phone` — their country-code/casing fuzzing has no index equivalent **this cut**", which Cut 1 falsifies for the email half; it is one of the two `this cut` MEMBERS the exclusion paragraph below distinguishes from the four true survivors | Cuts 1 and 4 | Task 11 |
| `resolve_or_create:878-879` | "Not yet wired into `find_or_create_stub` — that's the Phase-4 adapter swap, gated by the Phase-5 offline parity replay." — **P5**, and **already false at HEAD**: `find_or_create_stub:688-696` delegates to it today | pre-existing | Task 11 |
| `_resolve_identifier:949-951` | "Email/phone delegate to the legacy fuzzy `get_by_*` … `get_by_phone`'s UK/US country-code fuzzing has no index equivalent **this cut**" — **P1** for the email half; the phone half's "this cut" is a temporariness E3 disproves. Note the phrase is line-WRAPPED (`this` ends `:950`, `cut` begins `:951`), so no per-line scan could see it either way — it is a member the surface returns and a needle could not | Cut 1 (email); E3/Cut 2 (phone) | Task 6 |
| `_find_or_create_stub_legacy:709-712` and the whole of its docstring | "the pre-WI-125 `find_or_create_stub` body, preserved verbatim … (1) the Phase-5 offline parity baseline the engine is diffed against; (2) the one-commit rollback … NOT called in production" — **P5**, and the owner round 4 found in the authorized list with no row here. Every prose line it owns dies with the function; (e3) states that as its own clause because "at least one line gone" is far weaker than what is owed | Cut 4 | Task 11 |
| `select_resolution` (new) | no Cut-0 prose. **NOT an authorized owner** and not a Cut-0 owner at all — Task 9 creates it, so (e1) is vacuous for it and (e2) never reaches it. Listed so the table is a complete reading of the surface PLUS the one owner the build adds | — (does not exist at Cut 0) | Task 9 |

**What each repair SAYS, so the builder is not inventing prose.** `__init__`: `_identifier_index`
is the email authority; `_alias_index`, `_phone_index` and `_slack_index` are permanent, not
pending, with E5's reason (no `Alias` type; `slack` needs a workspace — the `UNBLOCK:` line).
`_index_entity`: builds the phone and alias indexes and projects into the unified identifier
index. `_project_identifiers` and its `add` comment: leniency now means the entry resolves
through NO door for email — which is exactly what Task 7's test asserts — and the permissive
sentence survives only with its scope narrowed to phone/alias/slack. `_index_identifiers`: the
last-writer-wins semantics stand on their own; there is no legacy email dict left to be
byte-identical to. `_remove_entity_from_indexes`: the email-removal loop and its label go; the
identifier-index removal at `:374-377` already covers email keys through `_project_identifiers`.
`resolve`: it ranks through `resolve_all` and selects with
`select_resolution`; what survives of the old numbering is `_RESOLVE_CASCADE_ORDER`, which is a
**tie-break over `matched_via`, not a trial order**, and `resolve_all` emits email before alias
(`:571-572`). `resolve_all`'s docstring, both members: the WI-018 paragraph says `resolve` returns
one `Optional[Person]` by applying `select_resolution` to this function's full ranking, while
`resolve_all` returns the ranking itself — the "stops at the first cascade hit" clause goes,
because after Cut 3 nothing stops at a first hit. And the company-hint paragraph states the
arithmetic that actually runs: the bump is `+0.25` capped at 1.0 (`:628-651`, not `~476`); the
Naomi Pavie shape reaches step 5's `token-subset` arm at 0.65 and bumps to 0.90; the `Emily M`
shape cannot reach that arm (one shared token), reaches step 6 at 0.6, and bumps to **exactly
0.85** — landing ON the 0.85 reuse threshold with no margin, which is the same disclosure E8 and
D1 already carry and the opposite of the 0.05 of headroom the sentence implies today.
`find_or_create_stub` and `resolve_or_create`: the Phase-5 replay's in-tree
successor is `tests/fixtures/identity_endgame/stub_golden.json` and
`tests/fixtures/identity_endgame/resolve_golden.json`, named by literal, and each Branch is
stated on its own terms rather than by reference to a deleted body. `resolve_or_create`'s
docstring is repaired at BOTH ends in the one edit — the head at `:847-848` and the tail at
`:878-879` carry the same already-false future tense about the Phase-4 adapter, so both say
plainly that `find_or_create_stub` runs through this method today (`:688-696`); repairing one
end only would leave the docstring contradicting itself inside the commit that repaired it. `_resolve_identifier`:
`get_by_email` is the index reader; `get_by_phone` stays fuzzy **permanently**, because E3 proves
no key function for `phones_match` can exist.

**What the needles are FOR, now that they are no longer the finding predicate.** The two tiers
below are a REGRESSION PIN over sentences the surface sweep already returned and this section
already read. They are not the census's source and they are not its closure — the disposition
rule above is both. Keeping them is still worth the lines, for a reason each round has
demonstrated: a needle at zero is a cheap, per-sentence, second-signal red that fires
independently of the surface diff, so a build that satisfies the diff by rewriting a sentence
into a differently-worded version of the same falsehood still goes red. Two facts about the
needle SET are stated so nobody mistakes it for the surface again. First, **the markers did not
find every member**: `_index_entity:193` (`"""Build email, phone, and alias indexes."""`)
carries none of the six; `resolve_all:519-523` and `:534-539` carry none of them either and are
ninety lines from anything the markers hit; and `_resolve_identifier:949-951`'s `this cut` is
line-wrapped past any per-line scan. Second, a marker like `per-kind` legitimately SURVIVES in
the functions that describe the three dicts that remain, so a bare marker zero would be a false
red. So the rule is not "the markers go to zero" — it is:

> Every sentence that CARRIES a falsified proposition and can be pinned by a literal on ONE
> unwrapped line is a needle at zero hits; a member with no safe needle (`:949-951`) is carried
> by its owner's named repair obligation instead; the markers that legitimately survive are not
> needles at all; and anything the build finds beyond this table is NAMED in the Build Log and
> repaired — never worked around, and never satisfied by narrowing the scan.

**Tier A — seven needles naming a thing that no longer exists.** Zero hits over
`python_files_under(PACKAGE_ROOT)`, each verified present today at exactly the sites the table
above names and nowhere else in the package:

| needle | today's sites | gone because |
|---|---|---|
| `_email_index` | `:156`, `:197`, `:328`, `:341-342`, `:391`, `:494`, `:574` | Cut 1 deletes the attribute |
| `_find_or_create_stub_legacy` | `:675`, `:699` | Cut 4 |
| `Phase-5` | `:675`, `:685`, `:710`, `:851`, `:879` | there is no runnable Phase-5 replay in this tree; the goldens are its successor. **The hyphenated form only** — the surviving WI-125 phase names are `Phase 2`/`Phase 3`/`Phase 4`/`Phase-4` and are not this needle |
| `Tries in order` | `:462` | Cut 3 — `resolve` tries nothing in order |
| `Build email, phone, and alias indexes` | `:193` | Cut 1 — **the member the marker scan missed**, pinned as its own literal precisely because of that |
| `legacy Strategy` | `:863`, `:871`, `:874` | Cut 4 deletes the referent |
| `legacy best-hit` | `:865`, `:912` | same referent; `legacy's` at `:867` is the third sentence in that block and dies with the same repair, but is not its own needle because the apostrophe form is too close to ordinary prose to pin |

**Tier B — nine sentences that carry a falsified proposition in the file's own words.** Zero hits
over the same file list; each is a literal present at exactly one site today, wholly on one
unwrapped line:

| needle | site | proposition |
|---|---|---|
| `zero parity risk` | `:163` | P2 |
| `later deletion cut` | `:165` | P3 |
| `during transition` | `:233` | P2 |
| `resolves the old way` | `:234` | P2 |
| `still indexes it` | `:252` | P2 |
| `stops at the first cascade hit` | `:521` | **P4** — round 3's member, and the reason Tier B exists at all: a falsified proposition restated in the file's own words, in `resolve_all`'s docstring |
| `bumped 0.65` | `:538` | not a P — the conflated `Emily M`/Naomi Pavie arithmetic; the true figure for the `Emily M` shape is 0.6 → exactly 0.85 |
| `person.py:~476` | `:536` | not a P — a stale in-file pointer to the company bump, which is at `:628-651`; the same class as the dangling `docs/` pointer at `:110-113` |
| `replay confirms zero` | `:685` | P5 |

**Three exclusions, named rather than left to a regex — D8's discipline applied here.**
`per-kind` and `permissive lookup` are **not needles**: they legitimately survive in `__init__`,
`_project_identifiers`, `_index_identifiers` and `_remove_entity_from_indexes`, whose repaired
prose still describes the three dicts that remain, and a zero on them would go RED on correct
text. And `this cut` is **not a needle** either. It occurs at **five** unwrapped sites, and their
dispositions differ, which is precisely why no single count over it can be an oracle:
`identifier.py:386` and `:411` ("not activated this cut", about Meeting), `person.py:242`
("Company isn't activated this cut") and `person.py:875` ("UNCHANGED this cut — the
`needs_resolution` flip is a follow-on") are all TRUE before and after, and the last two sit
inside ranges Tasks 6 and 11 rewrite, so each must SURVIVE its owner's repair rather than be
tidied away with it. `person.py:860` is the fifth and it is a **member**, not a survivor:
"email/phone via the legacy fuzzy `get_by_email`/`get_by_phone` — their country-code/casing
fuzzing has no index equivalent this cut" is false for the email half after Cut 1, and it is
repaired inside the `:858-863` range Task 11 already rewrites. A sixth use is line-WRAPPED at
`_resolve_identifier:950-951` and is also a member. So a `this cut` scan would go RED on four
true sentences, miss one member entirely, and collect a fifth whose repair is already owned —
and the cheapest repair from that red is deleting the true ones, which is this item's own harm
class. Both members are repaired by their owners' named obligations (Tasks 6 and 11) instead,
which is what a member with no safe needle gets. *(This paragraph is itself the round-3
correction: its earlier version named four surviving sites, and there are five — the fifth being
the one that is not a survivor at all.)*

**The next rung of the ladder, swept and DECLARED rather than assumed** — because a fold that
closes only the current level leaves the next level as the next round's finding:

- **Other package modules.** Both sweeps agree and are stated separately, because round 3's
  lesson is that a marker result is weaker evidence than a surface result. The marker scan over
  `python_files_under(PACKAGE_ROOT)` returns `person.py` alone; and the `prose_lines` surface over
  the same file list, read for the five propositions, returns no member outside `person.py` —
  `identifier.py:386` and `:411`'s "not activated this cut" are about Meeting activation, not
  about any P. **No members.**
- **`tests/`.** The same markers over `python_files_under(TESTS_ROOT)` return three modules —
  `tests/test_resolve_or_create.py`, `tests/test_wi126_body_preservation.py`,
  `tests/test_identity_index.py` — all three already `## Write Targets` entries with a task
  that rewrites or deletes the member (Tasks 4/7/11). **No unowned members.** Task 12's Tier A
  and Tier B needle scans are deliberately scoped to `PACKAGE_ROOT` and not to `TESTS_ROOT`,
  because a test may legitimately name a deleted symbol in order to assert its absence, while
  the package may not; the tests-root half of the one needle where absence IS required across
  both roots is Task 11's own total scan.
- **`docs/`.** Two members. `docs/backlog-campaign-2026-07-05.md:37,62` carries the campaign's
  "WI-023's cuts each re-run the parity replay green" invariant — **routed, not repaired**: E1
  already records that the invariant is not satisfiable as written and that its intent is
  carried by the goldens, and the campaign doc is the conductor's artifact, not a builder write
  target. `docs/person-repo-decomposition.md:22` describes "the resolve cascades", plural, which
  Cut 3 falsifies — **out of scope by construction**: it is WI-025's own work-item doc and this
  drive may not edit a work-item doc other than this one. Recorded here so WI-025's spec-writer
  inherits it rather than rediscovering it.
- **Repo-root prose, which is OUTSIDE the cage allowlist and so was worth checking rather than
  assuming.** `CLAUDE.md:37` says "resolve cascade", singular — true before and after.
  `README.md:234` shows `repo.get_by_email("john@example.com")` — D4 item 2 leaves the
  signature, return type and exception set unchanged, so it is still true. **Neither is a
  member, and nothing outside the allowlist is owed.**
- **The dimension beyond prose.** The same generator can falsify a TEST'S text as well as a
  docstring's; that intersection is the `tests/` rung above and it is owned. It cannot falsify
  a NAME this item keeps (`get_by_email`, `find_or_create_stub`, `_project_identifiers` all
  survive with their signatures), which is why no rename rides here.

### D12 — The self-collision rule: a literal this item asserts at zero may not be SPELLED in this item's own `tests/`-root modules

**The generator, stated before the members, because two rounds of experience say the members are
what a reader will otherwise take away.** Five acceptance checks and six supporting tests of this
item live in ONE module, `tests/test_identity_endgame.py` (`## Write Targets`: "Tasks 2, 3, 5, 6,
8, 9, 10, 11, 12, 13"). Three of this item's zero-count assertions scan
`python_files_under(PACKAGE_ROOT, TESTS_ROOT)` — a universe that CONTAINS that module. So a
needle asserted at zero across both roots is a needle the check module may not spell, and that
constraint is a property of the MODULE, not of any one clause inside it. Task 2 wrote the rule
and its reason for PLANTS; the reason was never about plants. To a per-line literal scan a
plant's text, a check's argument list, an owner qualname in a check's data, a comment, a
docstring and an assertion message are all the same thing: source text on a line the scan reads.

**What round 6 found, and why it blocks rather than rides.** Task 9's AC-4 structural clause is
ordered as "`attribute_reads_in` over `PersonRepository.resolve` for `_cache`, `_alias_index`,
`_email_index`, `_phone_index` is empty" — an argument list, which Task 6's plant-scoped wording
does not reach — and Task 12's clause (e3) plus its authorized-owner list are ordered to name
`PersonRepository._find_or_create_stub_legacy`, which Task 12's own "assembled from parts"
sentence scopes to clauses (a)–(d). Each turns a CORRECT sibling check red at the boundary where
it is written: `test_email_has_exactly_one_resolution_authority` at Task 9's commit,
`test_legacy_stub_is_gone_and_the_golden_is_the_oracle` at Task 12's — boundaries `## Verification`
declares "a defect". The sweep this section ran to state the rule found a THIRD ordered site the
round did not name (Task 5's tripwire, below), which is the evidence that a per-site repair was
the wrong shape.

**The rule, quantified over source lines rather than over clause kinds:**

> No literal this item asserts at ZERO over a root that contains one of this item's own
> `tests/`-root modules may appear as a contiguous substring of ANY SINGLE SOURCE LINE of those
> modules — not in a plant, not in a check's argument list, not in an owner qualname, not in a
> comment, not in a docstring, not in an assertion message, not in a test id. Where a check needs
> such a name it is ASSEMBLED FROM PARTS in the check's own source, so no one line carries it
> whole. The single exception is a spelling this item DELETES in the same commit as the assertion
> that forbids it; that arm is legal only where the table below names BOTH tasks.

**The three literals it binds are DERIVED, not listed.** Filter `## Verification`'s zero-count
table to the assertions whose root list includes `TESTS_ROOT`: `_email_index` (Task 6 / AC-2),
`_find_or_create_stub_legacy` (Task 11 / AC-1), `paren-decoration-at-the-door` (Task 10 / AC-5).
D11's other fourteen Tier A and Tier B needles are scanned over `PACKAGE_ROOT` alone (Task 12
clauses (a) and (b)) and are therefore OUTSIDE this rule — Task 12 assembles them anyway, for the
different reason its own text gives (a check that spells its needle whole is its own
counterexample), and the two members that appear in both places are bound here regardless. Stating
the derivation rather than a list is what stops a fourth bound literal — should a later clause
widen a scan's roots — from being a fourth round's finding.

**The members: every site the sweep returns, with its disposition.**

| module | the site, and why the name is needed there | literal | disposition |
|---|---|---|---|
| `tests/test_identity_endgame.py` | Task 5's tripwire asserts "every owner D11's table names owns at least one line" in `prose_surface_cut0.json`; that owner list contains `PersonRepository._find_or_create_stub_legacy` | `_find_or_create_stub_legacy` | ASSEMBLED — the site round 6 did not name, found by running this sweep |
| `tests/test_identity_endgame.py` | Task 6's AC-2 needle clause | `_email_index` | ASSEMBLED (already ordered there) |
| `tests/test_identity_endgame.py` | Task 9's AC-4 `attribute_reads_in` attrs argument | `_email_index` | ASSEMBLED — round 6's first instance |
| `tests/test_identity_endgame.py` | Task 10's AC-5 needle clause | `paren-decoration-at-the-door` | ASSEMBLED (already ordered there) |
| `tests/test_identity_endgame.py` | Task 11's AC-1 needle clause | `_find_or_create_stub_legacy` | ASSEMBLED (already ordered there) |
| `tests/test_identity_endgame.py` | Task 12 clause (a)'s Tier A needle list | both | ASSEMBLED (already ordered by (a)–(d)) |
| `tests/test_identity_endgame.py` | Task 12 clause (e)'s thirteen authorized owners and clause (e3)'s named owner | `_find_or_create_stub_legacy` | ASSEMBLED — round 6's second instance |
| `tests/test_identity_endgame.py` | Task 2's plants | all three | never spelled at all — a plant invents its own names (`_plant_index`, `docs/does-not-exist.md`) |
| `tests/test_resolve_or_create.py` | Task 4 points both parity legs at the real attribute; it is a CALL, so it cannot be assembled | `_find_or_create_stub_legacy` | CO-LANDING — Task 11 deletes those six cases in the same commit that writes AC-1's check, so the spelling and the assertion never coexist in one tree |
| `tests/test_wi126_body_preservation.py:212` | the pre-existing legacy body-preservation witness call | `_find_or_create_stub_legacy` | CO-LANDING — deleted by Task 11 in that same commit |
| `tests/test_identity_index.py:184`, `:189`, `:201` | the pre-existing leniency assertions | `_email_index` | CO-LANDING — rewritten by Task 7, which lands as ONE commit with Task 6; this is the interior red `## Verification`'s boundary paragraph already authorizes |
| `tests/derivations.py`, `tests/identity_fixture.py`, `tests/record_identity_golden.py`, `tests/test_ac_interpreter.py` | — | — | the sweep returns no site: none of the four needs any of the three |

**The next rung of the ladder, swept and DECLARED** — because closing three sites is not closing
the class, and closing the site level is not closing the level above it:

- **The DIMENSION: every way a name enters a module.** The rule above is quantified over source
  LINES precisely so that argument lists, owner qualnames, plants, comments, docstrings,
  assertion messages, test ids and f-strings are one case rather than eight — a new way of
  needing a name is then not a new finding.
- **The SUB-CELL: what "assembled from parts" has to mean, since a careless assembly
  reconstitutes the literal.** The test is contiguous-substring per LINE, because that is what
  the scans do. `"_email" + "_index"` is legal — no line of the source holds `_email_index`. An
  implicit concatenation that happens to abut (`"_email_" "index"`) is legal for the same reason.
  A line holding the name whole in any form — a slice, a comment restating it, an f-string
  literal segment — is not. The qualname case assembles its tail only:
  `f"PersonRepository.{LEGACY_ATTR}"` where `LEGACY_ATTR` is itself assembled.
- **The INTERSECTION with Task 12's near-miss plants, checked rather than assumed compatible.**
  Clause (d) plants `Phase-4`, `email_index` (no leading underscore) and `legacy strategy`
  (lower-cased) as shapes the case-sensitive needles must NOT collect. `Phase-4` and
  `legacy strategy` are outside the three bound literals. `email_index` is legal against
  `_email_index` only because the test is contiguous-substring: the plant must be spelled with a
  non-underscore character before it (`self.email_index`), and `x._email_index` or
  `foo_email_index` would violate the rule while still being a valid near-miss — so the plant's
  SPELLING is fixed here, exactly as Task 2 fixes its other plants.
- **The non-`.py` artifacts, where the rule must NOT be applied.** `prose_surface_cut0.json`
  records `person.py`'s Cut-0 prose verbatim, and `:156` is a code line with a trailing comment
  (`self._email_index: dict[str, str] = {}  # email -> cache_key`) that `prose_lines` emits as a
  whole stripped source line — so the committed record CONTAINS `_email_index`, and must, because
  its whole value is that its text is verbatim. It is out of every scan's universe by file type:
  `python_files_under` returns `.py` files only. Declared rather than assumed, because "assemble
  it from parts" applied to a frozen record would destroy the record.
- **The REVERSE direction: a package write breaking a tests-root zero.** The item's only package
  write target is `obsidian_schemas/repositories/person.py`, and all three literals are DELETED
  from it by Tasks 6, 10 and 11 — those deletions ARE the assertions. D11's ladder sweep records
  that no other package module carries any of the three.
- **A tests-root module this item does NOT write.** The three literals' entire tests-root
  population today is the four sites tabled above (three `_email_index`, one
  `_find_or_create_stub_legacy`, zero `paren-decoration-at-the-door` — the last occurs nowhere
  under `tests/`), and every one of them is in a declared `## Write Targets` path. Nothing outside
  this item's own write set can turn one of these zeros red.
- **The two NON-LITERAL members of the class, named so neither is a later round's finding.** The
  class one level up from this rule is *an assertion whose universe contains this item's own
  modules constrains how those modules are WRITTEN*, and a literal is only its commonest shape.
  Both other shapes are already disposed of in Task 13 and are recorded here so the sweep is
  complete rather than lucky. **(i) A PATTERN.** `NO_ARG_CONSTRUCTION` is a regex, and Task 13's
  own non-vacuity plant spells `PersonRepository()` inside this same module; it is legal because
  that scan runs over `tests/test_vault_path_required.py:_code_lines:281`, which does not yield
  lines inside a `'''…'''` plant constant. **(ii) A DELIMITER.** Task 13's third control asserts
  that no `prose_lines` record for these files carries a `#` whose trailing text contains `"""` or
  `'''` — a zero over the modules' own text exactly like the three literals, discharged by the
  authoring constraint Task 13 states (a triple-quote delimiter appears in these modules as a
  docstring delimiter or as a plant constant's delimiter, never inside a comment) with its one
  even-count residual named there. Neither is repaired by assembling a name, which is why they are
  disposed of in Task 13 rather than folded into the rule above; what they share with it is the
  direction of repair — the module is edited, never the scan.

**Why the direction of repair is fixed here rather than left to whoever meets the red.** From
inside the build, a red at Task 9's or Task 12's boundary is indistinguishable from a legitimate
narrowing — the same situation Task 2's rule exists for. The two cheapest repairs are both
forbidden in substance: re-scoping Task 6's clause back to `PACKAGE_ROOT` undoes round 5's own
fold and re-splits one signed phrase across two scopes, and dropping `_email_index` from AC-4's
attribute list weakens a signed criterion's check. **The repair is always to assemble the name**,
and a site this section did not name is recorded in the Build Log and repaired the same way —
never by narrowing a scan.

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

- **Case:** the mutating sweep and a read-only sweep share a vault.
  **Decision:** forbidden, per sweep, by the total rule in D3(b): every sweep that WRITES runs in
  its own freshly-seeded temp vault, and no sweep ever reads a vault another sweep wrote. The
  Cut-0 recorder therefore seeds twice from the one roster — once for AC-1's stub sweep, once for
  AC-4's resolve sweep — and D2's shared-vault literal
  (`("Jane Roe <jane.roe@example.com>", "Jane Roe")`) is the tripwire that goes RED if a later
  edit collapses them back into one.
  **Reasoning:** AC-1's sweep is not a benign append. Pre-cut, cases 1 and 3 fall through to
  Branch B and call `_writeback_identifier`
  (`obsidian_schemas/repositories/person.py:_writeback_identifier:1149-1180`) with the PARSED
  address; that routes through `update_fields`
  (`obsidian_schemas/repositories/base.py:update_fields:473-475`) into the WI-021 semantic gate,
  whose `emails` arm (`obsidian_schemas/name_gate.py:gate_write:387-404`) rebuilds the list from
  `split_address`. The `Jane Roe <…>` and `" dana@example.com "` plants are destroyed in place —
  so a resolve golden recorded afterwards in that vault contradicts E7's table on two of its
  three rows, which is the oracle defeat this item's whole spine exists to prevent. E5 excludes
  side effects from the parity contract's RETURN VALUES; it does not license one that rewrites
  the oracle's substrate.

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
  set exactly (`NameValidationError`, `WeakIdentityError`). **The one shape that does move,
  stated rather than covered by "unchanged":** `get_by_email(None)` raises `AttributeError`
  today at `get_by_email:390` and returns `None` after the cut, because `Email.parse(None)`
  raises `IdentifierError` into the arm that catches it (D4 item 2). Undocumented input
  becoming a documented answer is a widening, and it is the direction this cut is for.
  **Reasoning:** three consumer repos catch on those shapes; widening or narrowing the exception
  set is a consumer break bought for nothing — and `AttributeError` from a `None` argument was
  never part of that set, so accepting the input costs no consumer anything.

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

- [ ] **Task 2 — Add the four structural derivations to `tests/derivations.py`, each with its
      claimed match-shapes as planted fixtures.** Add `phone_index_iteration_sites`,
      `attribute_reads_in`, `docs_markdown_mentions` and `prose_lines` per D8. Write
      `tests/test_identity_endgame.py` (with `ensure_project_interpreter(__file__)` as its FIRST
      statement, per D9, and a one-line `CORPUS_COUPLING:` declaration in its module docstring
      naming `docs/identity-cutover-corpus-audit.md` and the property AC-5's check consumes —
      the artifact's declared section/field SHAPE, not its numbers — matching the convention at
      `tests/test_company_name_contract.py:15` and `tests/test_ac_interpreter.py:23`) carrying a
      shapes test that drives every claimed shape through the
      derivation's OWN predicate — never a re-implementation — over a scratch directory scanned
      by `python_files_under(plant_dir)`.
      **The rule that generates every expectation below, stated once so that a plant and the
      predicate cannot disagree in prose (round 5's finding).** Each planted line's expected
      record set is DERIVED by applying D8's stated rule to that line's own TOKENS — never from
      what the line looks like to a reader — and where a plant's assertion and a correct
      predicate disagree, the PLANT is wrong unless D8's rule is itself wrong: the predicate is
      never narrowed to make a plant green. **How the plants are SPELLED is governed by D12, the
      MODULE rule, of which this task's plants are one member and not the whole domain** (round 6:
      the constraint stated here was correct and its reason was never about plants, so Task 9's
      argument list, Task 12's owner qualnames and Task 5's owner list fell outside a rule that
      should always have covered them). Concretely, for this task: no plant may contain, on any
      single source line, any literal this item asserts at zero over a root containing
      `tests/test_identity_endgame.py`. Where a plant needs a name of its own it invents one
      (`_plant_index`, `docs/does-not-exist.md`); it never spells `_email_index`,
      `_find_or_create_stub_legacy` or `paren-decoration-at-the-door`, because Tasks 6, 10, 11 and
      12 scan `python_files_under(PACKAGE_ROOT[, TESTS_ROOT])` and `tests/test_identity_endgame.py`
      is under one of those roots: a plant spelling one of those needles turns another task's
      correct zero RED, and the cheapest repair from that red is narrowing the scope of a scan
      this item's whole evidence rests on. The one name a plant MUST spell literally is
      `_phone_index`, because `phone_index_iteration_sites` targets that attribute by name and it
      is an attribute this item KEEPS — no zero-count assertion in this document names it, so
      spelling it costs nothing, and D12 records it as the one such name that may be spelled.
      That direction is not a preference. Every one of
      these four is a FINDING surface whose failure mode is under-reach (D11), and a narrowing
      is invisible afterwards wherever `person.py` happens to carry no instance of the class
      removed — so a disagreement is recorded in the Build Log and resolved by fixing the plant,
      or, if D8's rule is the thing that is wrong, by returning the item rather than by editing
      the predicate to fit. Then the shapes, per predicate:
      **`phone_index_iteration_sites`** — the plants are written as METHODS of a class in the
      scratch file, so the iterable is spelled `self._phone_index` exactly as `person.py` spells
      it: a `list(...)`-wrapped loop AND a `sorted(...)`-wrapped loop (both match, both
      `materialized` — two of the five wrappers D8's vocabulary names, so the classification is
      not proved by its first member alone), a bare `.items()` loop (matches, `live`), and a
      loop over an unrelated attribute (near-miss, not collected).
      **`attribute_reads_in`** — a read of a named attribute inside a named function (matches);
      the same read in a DIFFERENT function (near-miss); a read of an attribute not in the set
      (near-miss); an ASSIGNMENT to a named attribute inside a named function (near-miss — D8
      collects LOADS, and AC-4's clause is worded "does not itself read"); and a read inside a
      NESTED `def` inside a named function (MATCHES, attributed to the enclosing NAMED qualname
      by the same `.<locals>.`-folding rule `prose_lines` uses, which D8 now states for both).
      **`docs_markdown_mentions`** — a resolving `docs/company-name-corpus-audit.md` planted in a
      DOCSTRING and a dangling `docs/does-not-exist.md` planted in a TRAILING COMMENT (both
      collected; both token kinds are driven because D8's rule runs over the file's whole text,
      not over comments alone), and `orchestrator/docs/x.md`, a bare `Smith.md` and a wrapped
      tail `revised-2026-06-13.md` (all three near-misses that must NOT be collected). The
      starts-with-`docs/` test is applied to the MATCHED TOKEN, never to the line: the character
      class is greedy and swallows the leading `orchestrator/`, which is exactly why that plant
      is out of scope.
      **`prose_lines`** — COLLECTED: a function docstring line; a `#` comment line in a
      function's body; a trailing `#` comment on a code line; a comment inside a NESTED `def`
      inside that function (attributed to the OUTER function's qualname, not to a `.<locals>.`
      qualname); and a module-level comment outside every definition (`owner == "<module>"`).
      Then the two shapes that defeat a line scan — the load-bearing half, because this
      predicate's failure mode is under-reach — stated SEPARATELY, because they defeat it in
      opposite directions and conflating them is what produced round 5's finding:
      **(i) the false-positive case, which owes NO record.** A code line carrying a `#` inside a
      STRING LITERAL (`x = "a # b"`) contributes nothing: it holds no `COMMENT` token, and its
      `STRING` token is part of an assignment rather than an expression statement, so it is no
      docstring either.
      **(ii) the state-tracking case, which IS collected — the near-miss is what follows it.** A
      code line whose TRAILING COMMENT contains `"""` (`x = 1  # see the """ delimiter`) carries
      a `COMMENT` token, so D8's rule emits exactly ONE record for it holding the whole stripped
      source line, identically to the plain trailing-comment shape above; the assertion is that
      one record, and then that the two ORDINARY CODE LINES FOLLOWING it contribute NONE. That
      second half is the near-miss: a `startswith`/delimiter line scan reads the `"""` as opening
      a docstring and swallows those two lines as prose. *An earlier wording of this task listed
      (ii) itself among the shapes that "may not be collected", which contradicted both D8's rule
      and this task's own trailing-comment shape four clauses above; it is resolved here in
      favour of the rule, and the predicate is not narrowed to match the old wording.* The shape
      is not hypothetical: `tests/test_vault_path_required.py:_code_lines:295-304` is precisely
      that line scan, it is the shipped helper Task 13 runs, and Task 13 now carries the clause
      that makes its swallowing RED.
      Import no `ast` anywhere outside `tests/derivations.py`; `tokenize` is
      a new import in that same file and is legal (D8).
      **The sweep across the other three predicates, DECLARED**, because closing the one
      contradiction in front of us is not the fold: the same question — does each claimed shape
      follow from that predicate's own stated rule? — was re-run over
      `phone_index_iteration_sites`, `attribute_reads_in` and `docs_markdown_mentions`, and found
      no second contradiction. What it DID find is three unproved cells, each now a plant above
      rather than a later round's finding: `materialized`'s five-wrapper vocabulary was driven by
      `list` alone, `attribute_reads_in` drove neither a Store nor a nested `def`, and
      `docs_markdown_mentions` drove no docstring-borne mention. The next rung out — whether a
      predicate's rule is stated at all for a cell a plant needs — returned the two
      `attribute_reads_in` clauses D8 now states.
      verify: test_identity_endgame_derivations_match_their_claimed_shapes

- [ ] **Task 3 — Author the frozen roster and the seeder.** Write
      `tests/fixtures/identity_endgame/roster.json` from D1's ten-row table verbatim, and
      `tests/identity_fixture.py` exposing `load_roster()`, `seed_vault(roster, dest)` (emitting
      every list element double-quoted so `" dana@example.com "` survives load) and
      `roster_digest()`. **`seed_vault` REFUSES a `dest` that
      `obsidian_schemas/repositories/base.py:_is_unconfigured:86-91` would swallow — `None`, a
      blank or whitespace-only string, or a value normalising to `Path(".")` — raising before it
      writes anything, so a computed `dest` can never fall through
      `base.py:_resolve_vault_path:94-104` to `OBSIDIAN_VAULT_PATH`** (D1, the M2 landing; this
      module is under `tests/` deliberately and so sits outside
      `test_no_implicit_vault_path_defaults:312-331`, which scans `obsidian_schemas/` and
      `scripts/` only). Assert that refusal for each of the four swallowed values with
      `OBSIDIAN_VAULT_PATH` set to a scratch directory in the test's own environment — so the
      fall-through is live and the assertion is not vacuous — and assert that a real temp `dest`
      seeds and returns that same path. Add a test that re-derives both E8 invariants from
      `roster.json` rather
      than restating them: no two notes share a name token, and no two notes carry phones that
      `phones_match` unifies — the latter driven through the shipped `phones_match`, not a
      re-implementation. Assert `Tomas Villalobos` is the only note with `company:`, and that a
      seeded vault loads with `PersonRepository(vault).load() == 10` and a skip surface of 0.
      verify: test_identity_fixture_roster_is_complete_and_invariant_holding

- [ ] **Task 4 — Cut 0a: repair the parity legs so they compare two implementations again.**
      In `tests/test_resolve_or_create.py`, point the "legacy" leg of
      `test_engine_matches_legacy_return_value` and of `test_engine_matches_legacy_on_weak_identity`
      at `_find_or_create_stub_legacy` instead of `find_or_create_stub`. The EXPECTED outcome is
      that both tests stay green — they are now differential rather than tautological. **A red
      here is a FINDING, not a build error, and the builder does not repair it.** Nobody has
      executed those six cases against `_find_or_create_stub_legacy` since WI-020 and WI-021
      landed on `create_stub`/`save` (E1's own reason for calling the out-of-tree replay stale),
      so a red is the first genuine differential signal this item has: it says the engine and the
      pre-WI-125 body actually disagree on a case, which is a fact about the package, not about
      this task. It lands before any production edit, so the tree is clean. On a red the builder
      STOPS at Task 4, records the case, both legs' `(name, created_new)` pairs and the diverging
      call in the Build Log, and the item returns for a spec revision — the same door D0 sets for
      a nonzero close-out audit, and for the same reason: whether a real divergence is a defect to
      fix, an intended WI-020/WI-021 change to absorb, or grounds to re-cut the plan is Dave's
      call with the case named, never a build-time judgement. Do not edit the legacy body, the
      engine, or the parity cases to make it green. They are deleted at Task 11, which is why
      this task's verification cannot be a standing artifact: any test name it declared would
      stop resolving at the end of the build.
      **This task SPELLS `_find_or_create_stub_legacy` in a `tests/`-root module, which AC-1
      asserts at zero across `PACKAGE_ROOT, TESTS_ROOT` — that is legal by D12's CO-LANDING arm
      and by nothing else**: the spelling is a call, so it cannot be assembled from parts, and
      Task 11 deletes these six cases in the SAME commit that writes AC-1's check, so the literal
      and the assertion never coexist in one tree. The same arm covers the pre-existing call at
      `tests/test_wi126_body_preservation.py:212`, which Task 11 deletes in that same commit. Do
      not "future-proof" either by obfuscating the attribute name: an assembled `getattr` here
      would hide the differential leg this task exists to restore.
      verify: hand-run — the two repaired legs are run once here and are green; AC-1 deletes them at Task 11, so no standing artifact can carry this ordinal to the end of the build

- [ ] **Task 5 — Cut 0b: record both goldens against unchanged code, one temp vault PER SWEEP.**
      Write `tests/record_identity_golden.py` (under `tests/`, never `scripts/` — see D3), which
      derives AC-1's twenty ordered cases and AC-4's thirty-nine deduplicated queries by D3's
      rules, then seeds **two independent temp vaults** from the one `roster.json` and runs
      AC-4's read-only resolve sweep in the first and AC-1's mutating stub sweep in the second.
      **Every `PersonRepository` the recorder constructs goes through ONE helper in that module
      which is handed the explicit temp path just seeded, and the recorder REFUSES — raising before
      any sweep writes — if the constructed repository's resolved `vault_path` is not that path or
      if the path handed in is one `base.py:_is_unconfigured:86-91` would swallow** (D3(b), the M1
      landing): this is the item's ONE hand-run invocation, it runs from the tree root with Dave's
      ambient `OBSIDIAN_VAULT_PATH` set, `base.py:_resolve_vault_path:94-104` falls back to that
      variable for an absent, blank or `"."` argument, and this module is under `tests/` and so
      outside `test_no_implicit_vault_path_defaults:312-331`'s universe — an unbound repository
      here mints D3's ten not-present notes into the live 1147-note vault and rewrites real notes'
      `emails:` through `gate_write`.
      They must not share a vault: pre-cut, cases 1 and 3 fall through to Branch B and their
      `_writeback_identifier` routes through `update_fields` into `gate_write`, whose `emails`
      arm rebuilds the list from the parsed address and destroys the `Jane Roe <…>` and
      `" dana@example.com "` plants in place (D3(b), hand-executed there). Write
      `stub_golden.json` and `resolve_golden.json` with `recorded_at: "cut-0"` and the roster
      digest, the resolve golden's `arm` drawn from D2's closed five-value vocabulary. **The same
      run also writes `prose_surface_cut0.json`** — `prose_lines(python_files_under(PACKAGE_ROOT))`
      filtered to `obsidian_schemas/repositories/person.py`, with `recorded_at: "cut-0"` (D3(b)).
      It reads the file's bytes rather than a vault, so it belongs to neither sweep; it is
      recorded here because after the first prose edit it can no longer be derived, which is the
      same reason the goldens are. Give it a
      `if __name__ == "__main__":` guard and run it ONCE, now, before any edit to
      `obsidian_schemas/`, with the floor's interpreter from the tree root so both `tests` and
      `obsidian_schemas` resolve off the rootdir the same way pytest's rootdir insertion makes
      them resolve: `cd <tree root> && /Users/davewascha/Workspaces/obsidian-schemas/.venv/bin/python -m tests.record_identity_golden`.
      Commit all three files. Then
      write the tripwire test: the goldens' `roster_digest` matches the committed roster, all
      three carry `recorded_at: "cut-0"`, `prose_surface_cut0.json` is non-empty and **every owner
      D11's table names owns at least one line in it, with the ONE declared exception of
      `select_resolution`, which Task 9 creates and which therefore owns no Cut-0 prose at all**
      (so a surface recorded against a renamed or already-edited file is RED here rather than
      silently narrowing Task 12's diff; note this clause is over the TABLE's owners, which is
      broader than the thirteen authorized ones and deliberately still covers `_clear_indexes`,
      whose `:327` docstring must be in the Cut-0 record for Task 12 (e1) to pin it),
      **the recorder's binding helper is exercised as a unit — it returns a repository whose
      `vault_path` is the temp path it was handed, and it RAISES for each value
      `_is_unconfigured` swallows (`None`, `""`, `"   "`, `"."`) with `OBSIDIAN_VAULT_PATH` set to
      a scratch directory in the test's own environment, so the fall-through the guard exists to
      stop would otherwise succeed and the assertion is not vacuous** (M1),
      the case and query lists re-derive identically from the
      roster as full `(ordinal, arm, query)` triples (D2 — `arm` participates, so a reshaped
      space is RED even where the query strings agree),
      the golden still holds the two exception rows' PRE-CUT values as literals spelled
      in the test's own source — `("kit@localhost", "Kit Baldwin")` and
      `(" dana@example.com ", None)` — and it holds D2's shared-vault literal
      `("Jane Roe <jane.roe@example.com>", "Jane Roe")`, which is `None` in any golden recorded
      in a vault the stub sweep already ran in.
      **One spelling constraint on the tripwire, per D12**: its owner list — D11's table's owners,
      which the "every owner owns at least one Cut-0 line" clause needs as strings — contains
      `PersonRepository._find_or_create_stub_legacy`, a literal AC-1 asserts at ZERO across
      `PACKAGE_ROOT, TESTS_ROOT` and this module is under `TESTS_ROOT`. Assemble that qualname
      from parts in the check's own source, so no single line of
      `tests/test_identity_endgame.py` carries it whole. It lands at THIS task, six tasks before
      the assertion that would find it, which is why D12 states the rule over the module rather
      than over the two clauses round 6 named.
      verify: test_identity_goldens_are_frozen_pre_cut_data

- [ ] **Task 6 — Cut 1: give email resolution exactly one authority.** Apply D4 items 1–6 to
      `obsidian_schemas/repositories/person.py` — item 6 being **D11's six Cut-1 prose repairs,
      landed in this same commit**: `__init__:160-167` (the dicts are no longer the permissive
      email surface and the collapse is not a later cut), `_index_entity:193` (no email index to
      build), `_project_identifiers:231-234` **and** its `add` comment at `:252` (leniency for
      email now means the entry resolves through NO door — the exact property Task 7's test
      asserts four lines below), `_index_identifiers:271-273` (no legacy email dict left to be
      byte-identical to), and `_resolve_identifier:949-951` (`get_by_email` is the index reader;
      `get_by_phone` stays fuzzy permanently, per E3, not "this cut").
      **A seventh authorized owner is repaired by this task without being on that list, and it is
      named so Task 12 (e2) is falsifiable rather than lucky**: `_remove_entity_from_indexes:337`'s
      label `# Remove emails from index` is deleted by D4 **item 1**, along with the removal loop it
      labels — that is the whole of that owner's ordered prose repair, and its own docstring at
      `:336` ("Remove a person's entries from all indexes") stays TRUE and survives. Do not also
      rewrite `_clear_indexes`' docstring at `:327` while deleting `self._email_index.clear()`
      beneath it: that owner is deliberately NOT authorized (D11), its one prose line is true, and
      Task 12 (e1) pins it VERBATIM.
      Write AC-2's check: the derived sweep over every
      `emails:` entry plus its lowercase, whitespace-padded and (where `Email.parse` succeeds)
      parsed-address variants; four surfaces agreeing on the note the roster declares owns the
      address, EXCEPT members whose stripped lowered form is an alias of a different person,
      where the declared asymmetry is asserted instead (three email-only doors → `Rosa Delgado`,
      `resolve` → `Alex Nkemdirim`); `kit@localhost` resolving to nobody by all three string
      surfaces with surface 4 asserted as a refusal; and the structural clause that the string
      `_email_index` (built from parts in the test's own source, never spelled whole — **D12, and
      the needle binds the WHOLE module rather than this clause: Task 9's AC-4 attrs list sits in
      the same file and assembles it for the same reason**) appears at
      zero sites under `python_files_under(PACKAGE_ROOT, TESTS_ROOT)` — **both tracked source
      roots, the same reading Task 10 gives AC-5's identical "the tracked sources" phrase and the
      same two roots AC-1's scan takes, so one signed phrase is not read at two scopes by two
      tasks.** Both roots is satisfiable and non-vacuous: the attribute is named under `tests/`
      at exactly three sites today, all in `tests/test_identity_index.py:184`, `:189` and `:201`,
      which Task 7 rewrites in this same commit — that is what Task 7's "remove every remaining
      reference to the deleted attribute from `tests/`" is FOR, and this clause is what asserts
      it rather than leaving it to the `AttributeError` a surviving reference would raise. It
      carries the two POSITIVES that make the zero non-vacuous rather than the count of an empty
      file list: the file list `python_files_under(PACKAGE_ROOT, TESTS_ROOT)` returns is
      non-empty, and the same assembled needle, run through the same scan over a scratch
      directory holding one planted file that contains it, IS found. (Task 12 clause (a) keeps
      the SAME needle scoped to `PACKAGE_ROOT` alone and that is deliberate, not a drift: it
      asserts the needle as a member of the strangler-prose class, where a test may legitimately
      name a deleted symbol to assert its absence, while this clause asserts the DELETION landing
      across both roots. A build that lands one without the other should go red twice.)
      verify: test_email_has_exactly_one_resolution_authority

- [ ] **Task 7 — Cut 1b: re-home the two leniency tests the cutover falsifies.** **This task and
      Task 6 are ONE commit** — Task 6 deletes `_email_index` while
      `test_malformed_email_skipped_but_legacy_indexes_it` and
      `test_clean_and_junk_in_one_list_indexes_only_the_clean` still assert its contents, so those
      two cases are RED between the two tasks by design — and so, from the other direction and
      over the same three surviving sites, is Task 6's own
      `test_email_has_exactly_one_resolution_authority`, whose needle clause now spans both
      tracked roots. Those three cases are the whole of the transient red the plan authorizes,
      they all close on this task's edit, and none of them is to be repaired on the Task 6 side.
      Rewrite
      `tests/test_identity_index.py`'s `test_malformed_email_skipped_but_legacy_indexes_it` and
      `test_clean_and_junk_in_one_list_indexes_only_the_clean` to assert the post-cutover
      property per D4: a note carrying `not-an-email` (and one carrying `bad email` beside a good
      address) loads without raising, contributes no identifier for the junk, and resolves
      through NO door — with the audit's 0-of-1021 cited in the test as the warrant for the loss.
      Remove every remaining reference to the deleted attribute from `tests/` — the three sites
      at `tests/test_identity_index.py:184`, `:189` and `:201` are the whole of them, and Task
      6's structural clause ASSERTS that zero across both tracked roots rather than leaving it to
      the `AttributeError` a survivor would raise at run time.
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
      D6, and rewrite `resolve()` as the empty guard plus `resolve_all` plus the policy. **Repair
      `resolve`'s own docstring at `:462-467` in this same commit (D11, the P4 member):** after
      this cut `resolve` tries nothing in order — it ranks through `resolve_all`, which emits
      email BEFORE alias (`:571-572`), and selects with `select_resolution`, whose
      `_RESOLVE_CASCADE_ORDER` is a tie-break over `matched_via` and not a trial order. Leaving
      the numbered list is the single most misleading survivor in the file, because it is a
      reader's first stop for "why does `resolve` prefer the alias?".
      **Repair `resolve_all`'s own docstring in the same commit — both D11 members, because they
      are one docstring and splitting them across commits is a needless hazard.** At `:519-523`
      the WI-018 paragraph says `resolve` "stops at the first cascade hit"; that is P4 in the
      file's own words, ninety lines above the comment this task already fixes, and after this
      cut it would contradict `resolve`'s repaired docstring inside this very commit — replace it
      with `resolve` returning one `Optional[Person]` by applying `select_resolution` to this
      function's full ranking. At `:534-539` the company-hint paragraph is false on two counts,
      neither of them caused by this cut but both riding here rather than in Task 10 for the
      one-docstring reason: it points at `person.py:~476` when the bump is at `:628-651`, and it
      attributes `bumped 0.65 → 0.90` to the `Emily M` shape, which cannot reach step 5's 0.65
      `token-subset` arm at all (`:607-608` needs `len(shared) >= 2`; it shares only `emily`) —
      that arithmetic is the two-shared-token Naomi Pavie case, while `Emily M` records **0.6** at
      `:626` and bumps to **exactly 0.85**, landing ON the reuse threshold with no float slack.
      The replacement states both cases separately with the real figures, and the on-the-threshold
      fact out loud, because E8, D1 and AC-1's Branch-B arithmetic all rest on it and the file
      currently tells its reader the opposite. Write
      AC-4's check: the structural clause (`resolve` calls `resolve_all` and `select_resolution`;
      `attribute_reads_in` over `PersonRepository.resolve` for `_cache`, `_alias_index`,
      `_email_index`, `_phone_index` is empty; `select_resolution` is a module-level function of
      `obsidian_schemas.repositories.person`) — **whose `attrs` argument is an ordered site of
      D12's rule and is ASSEMBLED FROM PARTS accordingly**: `_email_index` is a literal Task 6
      asserts at ZERO across `PACKAGE_ROOT, TESTS_ROOT`, `tests/test_identity_endgame.py` is
      under `TESTS_ROOT`, and an argument list is source text like any other, so spelling it here
      would turn `test_email_has_exactly_one_resolution_authority` RED at THIS task's boundary
      against a correct build. `_cache`, `_alias_index` and `_phone_index` are spelled plainly —
      no assertion in this document names any of the three at zero. Do not resolve such a red by
      re-scoping Task 6's clause to `PACKAGE_ROOT` or by dropping an attribute from AC-4's list:
      the first undoes round 5's fold and re-splits one signed phrase across two scopes, the
      second weakens a signed criterion's check, and the repair is to assemble the name (D12).
      Then the golden replay over all thirty-nine queries
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
      `paren-decoration-at-the-door` over `python_files_under(PACKAGE_ROOT, TESTS_ROOT)` — both
      tracked source roots, which is what AC-5's "across the tracked sources" says, and safe
      because the needle occurs nowhere under `tests/` today and the check assembles it from
      parts rather than spelling it whole (D12 — it is the third of the three literals that rule
      binds, and no other site in this item's `tests/`-root modules needs it). It carries **the same two-part non-vacuity positive
      Tasks 6, 11 and 12 carry**: the file list is non-empty, and the same assembled needle IS
      found by the same scan over a scratch directory holding one planted file containing it.
      Plus: every `docs_markdown_mentions` hit over
      `python_files_under(PACKAGE_ROOT)` resolving to an existing file; the
      `UNBLOCK:` marker present with non-empty text; and no source comment asserting that step 6
      is filtered out absent a company hint — that last zero-count paired with its own positive,
      namely that the REPAIRED step-6 comment is present at
      `obsidian_schemas/repositories/person.py:resolve_all` and states that the branch records
      0.6 and survives the floor, so the clause cannot go green by the comment having been
      deleted outright.
      verify: test_identity_cutover_docs_are_complete_and_truthful

- [ ] **Task 11 — Cut 4: delete the duplicate and both of its consumers.** Delete
      `_find_or_create_stub_legacy` and the prose mention at `:675`; repair the stale Phase-5
      replay claim at `:685` to point at the committed goldens **by literal name**
      (`stub_golden.json` and `resolve_golden.json`, which is what Task 12 checks for);
      **and land D11's remaining P5 repairs in the same commit** — `find_or_create_stub:683-686`
      ("the legacy path indexed malformed values" at `:683-685`, false since Cut 1, and "The
      Phase-5 replay confirms zero return-value divergence" at `:685-686`),
      `resolve_or_create:851` (the Phase-5 parity contract's in-tree successor is the two
      goldens), `:858-863`/`:871`/`:874`/`:912` (each Branch stated on its own terms instead of
      as "byte-identical to legacy Strategy N", whose referent this task deletes), and **both
      ends of `resolve_or_create`'s docstring, which carry the same already-false future tense
      about the Phase-4 adapter and must be repaired together** — `:878-879` ("Not yet wired into
      `find_or_create_stub`" — `:688-696` delegates today; the derivation surfaced this one and
      no prior gate named it) and its head at `:847-848` ("the identifier-first core that the
      Phase-4 adapter **will run** `find_or_create_stub` through", the same claim in the future
      tense thirty lines above the tail). Repairing one end only leaves the docstring saying the
      swap will happen in its head and has happened in its tail, inside the commit that repaired
      it.
      Delete the six parity cases in
      `tests/test_resolve_or_create.py` repaired at Task 4 and `test_legacy_preserves_rich_note`
      in `tests/test_wi126_body_preservation.py`, leaving `test_engine_preserves_rich_note`
      standing. **Those two deletions and this task's own AC-1 check land in ONE commit, which is
      what makes Task 4's and `test_wi126_body_preservation.py:212`'s spellings of the needle
      legal under D12's CO-LANDING arm** — the literal leaves `tests/` in the same commit the
      assertion enters it, so no boundary sees both. Write AC-1's check: a literal-text scan over every file
      `python_files_under(PACKAGE_ROOT, TESTS_ROOT)` returns, with the needle assembled from
      parts in the check's own source so the check is not its own counterexample **and, per D12,
      so no line of `tests/test_identity_endgame.py` carries it whole — a rule that binds Task
      5's tripwire owner list and Task 12's clauses (e)/(e3) in the same module, not just this
      clause**, and with the
      two POSITIVES that make its zero non-vacuous — the file list is non-empty, and the same
      assembled needle IS found by the same scan over a scratch directory holding one planted
      file that contains it; the both-legs clause (no test's two legs both reach
      `resolve_or_create`) — with ITS non-vacuity positive, that the same predicate DOES find the
      two-leg shape in a planted scratch module written to carry it, since after this task's own
      deletions the real population is empty and an unreachable predicate would be green;
      and the golden replay of all twenty ordered cases, in the frozen
      order, in a freshly-seeded temp vault of its own (D3(b): this is the sweep that WRITES),
      with every `(resolved_name, created_new)` pair matching and the committed fixture's bytes
      unchanged by the run.
      verify: test_legacy_stub_is_gone_and_the_golden_is_the_oracle

- [ ] **Task 12 — Close the strangler-prose class over an ENUMERATED SURFACE, with the needles
      demoted to a regression pin.** AC-5's check owns three documentation-truth repairs; D11
      shows they are three members of a class whose other members were surfaced after the criteria
      were frozen. This task asserts the class **without reopening AC-5** — Task 10 remains the
      precedent for proving a documentation-truth repair beside it rather than inside it. **Clause
      (e) is the closure and clauses (a)–(d) are the pin**; that ordering is the round-3 repair
      and it matters, because for two rounds the pin WAS the closure and its finding step
      under-reached both times. Clauses (a)–(d) run over the source TEXT of every file
      `python_files_under(PACKAGE_ROOT)` returns, scanned per line,
      **case-SENSITIVELY** (which is what makes clause (d)'s `legacy strategy`
      near-miss a near-miss rather than a hit), with every needle spelled as a **literal
      assembled from parts in the check's own source** so the check is not its own
      counterexample.
      **That assembly is NOT scoped to clauses (a)–(d): per D12 it binds every line of this check,
      clause (e)'s owner qualnames included.** `_email_index` and `_find_or_create_stub_legacy`
      are asserted at ZERO across `PACKAGE_ROOT, TESTS_ROOT` by Tasks 6 and 11, and
      `tests/test_identity_endgame.py` is under `TESTS_ROOT` — so clause (e)'s thirteen-owner list
      and clause (e3)'s single named owner, both of which need
      `PersonRepository._find_or_create_stub_legacy` as a STRING to filter `prose_lines` records
      by owner, are assembled from parts exactly as (a)'s Tier A list is. Spelling either whole
      turns `test_legacy_stub_is_gone_and_the_golden_is_the_oracle` RED at this task's boundary
      against a correct build, and the cheapest repairs from that red — re-scoping AC-1's frozen
      both-roots scan, or dropping the owner from (e3) — are respectively forbidden and a
      weakening of the strongest clause in this task. Clause (d)'s `email_index` near-miss plant
      is spelled with no leading underscore and with a non-underscore character before it, which
      is what keeps it a near-miss AND keeps it outside D12's contiguous-substring test. Then the
      clauses:
      **(a) D11's Tier A — seven needles at ZERO hits**: `_email_index`,
      `_find_or_create_stub_legacy`, `Phase-5`, `Tries in order`,
      `Build email, phone, and alias indexes`, `legacy Strategy`, `legacy best-hit`. (`Phase-5`
      is the hyphenated form only; `Phase 2`/`Phase 3`/`Phase 4`/`Phase-4` survive and are not
      this needle.)
      **(b) D11's Tier B — nine sentence literals at ZERO hits**, which is the clause that catches
      a falsified proposition restated in the file's own words: `zero parity risk`,
      `later deletion cut`, `during transition`, `resolves the old way`, `still indexes it`,
      `stops at the first cascade hit`, `bumped 0.65`, `person.py:~476`,
      `replay confirms zero`. Do NOT scan for `per-kind`, `permissive lookup` or `this cut` —
      D11 names all three as exclusions, and each would go RED on correct surviving text (`this
      cut` has five unwrapped sites, four of them true sentences that must SURVIVE).
      **(c) The presence assertion, which is what "the surviving text points at the committed
      goldens" is checked AS**: `person.py`'s text contains the literals `stub_golden.json` and
      `resolve_golden.json` (Task 11's `:685` and `:851` repairs). Without this, clause (b)'s
      `replay confirms zero` zero would be satisfied by deleting the sentence and pointing at
      nothing.
      **(d) The non-vacuity positives, the same two-part control Tasks 6, 10 and 11 carry** — a
      scan for a needle the repaired text no longer contains is green, and a scan for a needle
      that never existed is green too, so: the file list `python_files_under(PACKAGE_ROOT)`
      returns is non-empty; **every needle in D11's Tier A and Tier B tables** — the check builds
      its list from those two tables' members, and no count is written in the check or in this
      task, because a restated count is the one thing in this document that has been wrong in
      three consecutive rounds — IS found by the same scan over a
      scratch directory holding one planted file that contains each; and a NEAR-MISS planted
      line carrying `Phase-4`, `email_index` (no leading underscore) and `legacy strategy`
      (lower-cased) is NOT collected, so the scan cannot pass by matching everything and later be
      narrowed back with nothing checking that the narrowing kept the claimed shapes.
      **(e) The surface clause — D11's disposition rule, which is what actually closes the
      class.** Run `prose_lines(python_files_under(PACKAGE_ROOT))`, filter to
      `obsidian_schemas/repositories/person.py`, and compare against the committed
      `prose_surface_cut0.json`. **D11's authorized set is the THIRTEEN owners it names — owners
      ordered a PROSE repair — and the check builds its list from that paragraph, never from the
      table's owner column, which carries two declared non-members**: `_clear_indexes` (Cut 1
      deletes a CODE line inside it; `prose_lines` emits no code, so it is ordered no prose repair
      and clause (e1) pins its `:327` docstring verbatim like any other unauthorized owner) and
      `select_resolution` (Task 9 CREATES it, so it owns no Cut-0 line and is not a Cut-0 owner at
      all). Both are named here so the exclusion is auditable rather than discovered at the last
      task, and neither may be widened: the two other `—` rows in D11's table are NOT exempt,
      because per-OWNER `get_by_phone` loses `:416` at Task 8 and `_project_identifiers` loses
      `:231-234`, `:236-238` and `:252` while `:238-242` survives. Then:
      **(e1)** every Cut-0 line whose `owner` is NOT one of D11's thirteen
      authorized owners is present VERBATIM in the final surface — which includes both non-members
      above, and for `_clear_indexes` that is a real assertion rather than a formality; **(e2)**
      every one of the thirteen authorized owners
      has at least one Cut-0 line absent from the final surface, so a repair the plan ordered and
      the build skipped is RED (this is the clause that would have caught round 3's member had it
      been in the table, and it is what makes the table auditable once instead of one member per
      round); **(e3)** `PersonRepository._find_or_create_stub_legacy` owns ZERO lines in the final
      surface — which is strictly stronger than the (e2) it also satisfies, and is why it is its
      own clause; **(e4)** the non-vacuity positive for the whole clause — the Cut-0 surface is
      non-empty, the final surface is non-empty, and each of the thirteen authorized owners owns at
      least one line in the CUT-0 surface, so a predicate that returned nothing could not
      satisfy (e1) by having nothing to compare and (e2) could not go green over an empty domain.
      The comparison is on `(owner, text)` pairs, never
      on line numbers, so a repair that reflows an authorized owner's neighbours does not go red
      for the reflow; a rewrite of an UNAUTHORIZED owner's prose does, and that is intended —
      the builder either justifies it in the Build Log as a member D11 missed, or reverts it.
      **Anything the run returns that D11's table did not name is recorded in the Build Log and
      REPAIRED** — never worked around, and never satisfied by narrowing a needle or by adding an
      owner to the authorized set to make (e1) go green. Two of Tier
      A's needles (`_email_index`, `_find_or_create_stub_legacy`) are also asserted at zero by
      Tasks 6 and 11: that overlap is deliberate and neither supersedes the other, because Tasks
      6 and 11 assert them as the DELETION landing while this task asserts them as members of
      the prose class, and a build that lands one without the other should go red twice, not
      once.
      verify: test_strangler_prose_class_is_closed_in_the_package

- [ ] **Task 13 — Close wall membership by RUNNING each wall's own predicate.** Enumerate the
      files this item created or edited, assert each exists, and run every predicate in D10's
      table on their final text, asserting each wall's own requirement — **including D10's last
      row, which is the wall-shaped hole rather than a wall: scan every `tests/`-root `.py` file
      this item creates or edits with the SHIPPED pattern
      `tests/test_vault_path_required.py:NO_ARG_CONSTRUCTION:382`, over code lines only via that
      module's own `_code_lines:281`, and assert ZERO no-argument repository constructions**
      (the M3 landing — `test_no_implicit_vault_path_defaults:312-331` scans `obsidian_schemas/`
      and `scripts/` only and `test_docs_do_not_advertise_no_arg_construction` scans `*.md`, so
      nothing standing reaches these three new writing modules, and `base.py:_resolve_vault_path`
      silently binds an unargued repository to `OBSIDIAN_VAULT_PATH`). Import the pattern and the
      line iterator rather than re-spelling either, so a future narrowing of the wall's own regex
      cannot leave this scan asserting a shape the wall no longer means. **That zero carries the
      same two-part non-vacuity control the item's other zero-count assertions carry**: the file
      list is non-empty, and the same pattern run by the same scan over a scratch directory
      holding one planted file containing `PersonRepository()` DOES collect it.
      **And it carries a third control the other zero-counts do not need, because this one runs
      through a BORROWED LINE SCAN rather than through a tokenizer.** `_code_lines:295-304` sets
      `in_docstring` on any line holding an odd count of `"""`, trailing comments included, so a
      single comment carrying that delimiter swallows every ordinary code line beneath it until
      the next one — and the M3 zero then reads exactly like a clean scan while being an
      under-reach. That is the same defect class D8 built `prose_lines` on `tokenize` to avoid,
      met one level out in the shipped helper this task imports rather than in a predicate this
      item writes. So: **assert that no line `prose_lines` returns for any of these files carries
      a `#` whose trailing text contains `"""` or `'''`** — decidable from `prose_lines`' own
      records, which are whole source lines, and it is the exact shape that defeats
      `_code_lines`. It has no false red against this item's own plant idiom: a scratch plant is a
      triple-quoted assignment, whose interior is not an expression statement and so yields no
      `prose_lines` record at all, and the assertion looks only at lines that ARE records. The
      authoring constraint it enforces is the one to write to: in this item's `tests/`-root
      modules a triple-quote delimiter appears as a docstring delimiter or as a plant constant's
      delimiter, never inside a comment. That constraint also keeps the borrowed scan HONEST
      about plants rather than merely quiet: a `PLANT = '''…'''` constant is entered and left
      cleanly by `_code_lines`' own delimiter tracking, so a `PersonRepository()` inside a plant's
      TEXT is correctly not counted as a construction by this module, which is what the M3 zero
      means. **The residual is named rather than implied**: `_code_lines` ALSO declines to yield a
      code line carrying an even, self-closing `"""a"""` (the `for`/`else` at `:298-307` breaks
      without yielding), which this assertion does not see. It is left open deliberately — the
      same authoring constraint keeps such a line out of these modules, and every cheap machine
      form of it goes red against the plant idiom, so buying it would cost the control it was
      meant to add. And do NOT repair a red here by editing `tests/test_vault_path_required.py`,
      which `## Scope Boundary` keeps unchanged: the repair is to this item's own module — drop
      the delimiter out of the comment — or a Build Log entry if the red has another cause.
      Anything the run
      returns that D10 did not name is recorded in the Build Log and satisfied — never worked
      around, and never satisfied by narrowing a wall.
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
why: Tasks 6, 8, 9, 10, 11 — the email cutover (delete `_email_index`, re-home `get_by_email` onto `_identifier_index`, re-point `resolve` step 3 and `resolve_all` step 2), the phone snapshot + carve-out comment, `select_resolution` + the rewritten `resolve`, the four rider repairs, the deletion of `_find_or_create_stub_legacy` and its docstring mention, and D11's strangler-prose repairs across the authorized owners its disposition table names, distributed over those same tasks (Cut 1's set in Task 6, `resolve`'s and `resolve_all`'s docstrings in Task 9, the riders in Task 10, the P5 set in Task 11). No count is stated here on purpose: D11's table is the enumeration, and a number restated away from it has been wrong three rounds running.
```

```writes
path: tests/derivations.py
why: Task 2 — the four new structural predicates (`phone_index_iteration_sites`, `attribute_reads_in`, `docs_markdown_mentions`, `prose_lines`). They land HERE and nowhere else because `ast` is single-homed by two standing set-equality walls; `prose_lines` also brings a new `tokenize` import, which joins no wall population (the walls pin `ast`, and `test_write_routing.py`'s import universe is `PACKAGE_ROOT + SCRIPTS_ROOT`).
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
path: tests/fixtures/identity_endgame/prose_surface_cut0.json
why: Task 5 — D11's oracle: `person.py`'s whole prose surface at Cut 0, as `(owner, line, text)`, recorded by the same one-shot recorder and at the same baseline moment as the goldens. It is what Task 12 clause (e) diffs the final surface against, and like the goldens it cannot be re-derived once the first prose edit lands.
```

```writes
path: tests/test_identity_endgame.py
why: Tasks 2, 3, 5, 6, 8, 9, 10, 11, 12, 13 — all five acceptance checks plus the derivation-shapes, roster-invariant, golden-tripwire, stale-claim, strangler-prose-surface and wall-membership tests. Calls `ensure_project_interpreter(__file__)` as its first statement, and carries a one-line `CORPUS_COUPLING:` declaration in its module docstring because AC-5's check reads `docs/identity-cutover-corpus-audit.md` at run time (D9; the convention is `tests/test_company_name_contract.py:15` and `tests/test_ac_interpreter.py:23`).
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

## Mitigation Folds — 2026-09-07

The four `kind: required` mitigations of `## Threat Model — 2026-09-07` — the latest and only
speaking round — each folded into `## Design` AND the Implementation-Plan task its fence names, in
the same edit as this record. M4 was already carried by D5 and Task 8 before this round and its
`design`/`work` are quoted from them unchanged; M1, M2 and M3 named work no task ordered, and the
substance landed in D3(b)/Task 5, D1/Task 3 and D10/Task 13 respectively in this same edit. Every
`desc` is copied verbatim from the 2026-09-07 fences. No `## Write Targets` fence was added or
removed by this fold — `tests/identity_fixture.py`, `tests/record_identity_golden.py` and
`tests/test_identity_endgame.py` were already declared paths — so the `review_level: L3` touch
surface is unchanged, and no hash-signed span was touched.

```fold
id: M1
desc: tests/record_identity_golden.py binds every PersonRepository it constructs to the explicit temp path it just seeded, and refuses to run — before any sweep writes — if a repository's resolved vault_path is not that path
design: Every `PersonRepository` the recorder constructs is passed the explicit temp path that run just seeded, and the recorder REFUSES — before any sweep writes — if a constructed repository's resolved `vault_path` is not that path.
landed: Task 5
work: Write `tests/record_identity_golden.py`, which derives AC-1's twenty ordered cases and AC-4's thirty-nine deduplicated queries by D3's rules, then seeds two independent temp vaults from the one `roster.json`; every `PersonRepository` the recorder constructs goes through ONE helper in that module which is handed the explicit temp path just seeded, and the recorder REFUSES — raising before any sweep writes — if the constructed repository's resolved `vault_path` is not that path or if the path handed in is one `base.py:_is_unconfigured:86-91` would swallow, because this is the item's ONE hand-run invocation, it runs from the tree root with Dave's ambient `OBSIDIAN_VAULT_PATH` set, `base.py:_resolve_vault_path:94-104` falls back to that variable for an absent, blank or `"."` argument, and this module is under `tests/` and so outside `test_no_implicit_vault_path_defaults:312-331`'s universe — an unbound repository here mints D3's ten not-present notes into the live 1147-note vault and rewrites real notes' `emails:` through `gate_write`. The tripwire test then exercises the binding helper as a unit: it returns a repository whose `vault_path` is the temp path it was handed, and it RAISES for each value `_is_unconfigured` swallows (`None`, `""`, `"   "`, `"."`) with `OBSIDIAN_VAULT_PATH` set to a scratch directory in the test's own environment, so the fall-through the guard exists to stop would otherwise succeed and the assertion is not vacuous. verify: test_identity_goldens_are_frozen_pre_cut_data
```

```fold
id: M2
desc: tests/identity_fixture.py's seed_vault refuses a dest that base.py:_is_unconfigured would swallow (absent, blank, whitespace-only or "."), so a computed dest can never fall through _resolve_vault_path to OBSIDIAN_VAULT_PATH
design: `seed_vault(roster, dest)` REFUSES a `dest` that `obsidian_schemas/repositories/base.py:_is_unconfigured:86-91` would swallow — `None`, a blank or whitespace-only string, or a value normalising to `Path(".")` — raising before it writes anything, so a computed `dest` can never fall through `obsidian_schemas/repositories/base.py:_resolve_vault_path:94-104` to `OBSIDIAN_VAULT_PATH`.
landed: Task 3
work: Write `tests/identity_fixture.py` exposing `load_roster()`, `seed_vault(roster, dest)` (emitting every list element double-quoted so `" dana@example.com "` survives load) and `roster_digest()`; `seed_vault` REFUSES a `dest` that `obsidian_schemas/repositories/base.py:_is_unconfigured:86-91` would swallow — `None`, a blank or whitespace-only string, or a value normalising to `Path(".")` — raising before it writes anything, so a computed `dest` can never fall through `base.py:_resolve_vault_path:94-104` to `OBSIDIAN_VAULT_PATH`, this module being under `tests/` deliberately and so outside `test_no_implicit_vault_path_defaults:312-331`, which scans `obsidian_schemas/` and `scripts/` only. Assert that refusal for each of the four swallowed values with `OBSIDIAN_VAULT_PATH` set to a scratch directory in the test's own environment — so the fall-through is live and the assertion is not vacuous — and assert that a real temp `dest` seeds and returns that same path. verify: test_identity_fixture_roster_is_complete_and_invariant_holding
```

```fold
id: M3
desc: the wall-membership run also scans every file this item creates or edits under tests/ for no-argument repository construction, using the shipped NO_ARG_CONSTRUCTION pattern at tests/test_vault_path_required.py:382, because test_no_implicit_vault_path_defaults:312-331 scans only obsidian_schemas/ and scripts/
design: This item adds three repository-constructing modules under `tests/` — two of which WRITE — so it inherits the obligation the wall would have imposed had its universe reached them, and Task 13 discharges it by running the shipped pattern rather than by re-implementing one.
landed: Task 13
work: Enumerate the files this item created or edited, assert each exists, and run every predicate in D10's table on their final text, asserting each wall's own requirement — including D10's last row, which is the wall-shaped hole rather than a wall: scan every `tests/`-root `.py` file this item creates or edits with the SHIPPED pattern `tests/test_vault_path_required.py:NO_ARG_CONSTRUCTION:382`, over code lines only via that module's own `_code_lines:281`, and assert ZERO no-argument repository constructions, since `test_no_implicit_vault_path_defaults:312-331` scans `obsidian_schemas/` and `scripts/` only and `test_docs_do_not_advertise_no_arg_construction` scans `*.md`, so nothing standing reaches these three new writing modules while `base.py:_resolve_vault_path` silently binds an unargued repository to `OBSIDIAN_VAULT_PATH`. Import the pattern and the line iterator rather than re-spelling either, so a future narrowing of the wall's own regex cannot leave this scan asserting a shape the wall no longer means. That zero carries the same two-part non-vacuity control the item's other zero-count assertions carry: the file list is non-empty, and the same pattern run by the same scan over a scratch directory holding one planted file containing `PersonRepository()` DOES collect it; and it carries a third control the other zero-counts do not need, because this one runs through a BORROWED LINE SCAN rather than through a tokenizer — assert that no line `prose_lines` returns for any of these files carries a `#` whose trailing text contains `"""` or `'''`, because `_code_lines:295-304` sets `in_docstring` on any line holding an odd count of `"""`, trailing comments included, so one such comment swallows every code line beneath it and turns this zero into an under-reach that reads exactly like a clean scan. verify: test_identity_endgame_wall_membership_is_closed
```

```fold
id: M4
desc: get_by_phone's fuzzy scan iterates a materialized snapshot of _phone_index rather than the live mapping _clear_indexes mutates in place, asserted by the stronger predicate D5 states rather than by AC-3's "the iterable is a call" gloss, which is vacuously green against unchanged code
design: Stated as the one requirement its two halves are: `get_by_phone`'s fuzzy scan iterates a materialized snapshot of `_phone_index` rather than the live mapping `_clear_indexes:326-333` mutates in place, and that is asserted by the stronger predicate above — every package `for` loop whose iterable reaches `self._phone_index` is wrapped in `list`/`tuple`/`sorted`/`frozenset`/`dict` — never by AC-3's "the iterable is a call" gloss, which is vacuously green against unchanged code.
landed: Task 8
work: Materialize `get_by_phone`'s fuzzy scan (`list(self._phone_index.items())`) and add the comment naming the non-transitivity and citing the witness by name. Write AC-3's check: the three `phones_match` results against the shipped function; `Phone.parse` accepting all three forms and yielding three DISTINCT `.key` values; `get_by_phone("44790055852")` and `get_by_phone("0790055852")` returning `Priya Raman` while `get_by_phone("10790055852")` returns `None` against a vault seeded from `roster.json`; and the structural clause via `phone_index_iteration_sites` that every `_phone_index` loop in the package is `materialized` (with the non-vacuity assertion that at least one site exists). verify: test_phones_stay_on_the_fuzzy_path_and_the_reason_is_executable
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
held as literals in the check's own source); a resolve golden recorded in a vault AC-1's stub
sweep has already mutated (caught by D2's shared-vault literal,
`("Jane Roe <jane.roe@example.com>", "Jane Roe")`, which that recorder shape turns into `None`);
a `for` loop over `_phone_index` that is not
materialized; `resolve` reading any of the four indexes directly; a `docs/`-relative markdown
pointer in `obsidian_schemas/` that does not resolve; **any needle in D11's Tier A or Tier B
table surviving in `obsidian_schemas/`, Tier B's sentence literals especially — that is how a
falsified proposition restated in the file's own words fails LOUD rather than passing by
assumption**; **and, the clause that actually closes that class rather than pinning it, any
divergence between `person.py`'s final prose surface and `prose_surface_cut0.json` outside D11's
authorized owners, or an authorized owner whose repair never landed** (Task 12 clause (e));
the repaired
`find_or_create_stub` docstring naming no golden file; the audit artifact missing a section, a field, or carrying a stated count with no
listing behind it; **`seed_vault` handed a `dest` the library would resolve to
`OBSIDIAN_VAULT_PATH` (`None`, blank, whitespace-only, `"."`), and the Cut-0 recorder constructing
a `PersonRepository` whose resolved `vault_path` is not the temp path that run seeded — both refuse
BEFORE any write rather than seeding the live vault** (M1, M2); **a no-argument repository
construction anywhere in this item's `tests/`-root modules** (M3); **and a comment in any of
those modules carrying a `"""` or `'''` delimiter — the shape that makes the borrowed
`_code_lines` line scan swallow every code line beneath it, turning M3's zero into an under-reach
that reads exactly like a clean scan** (Task 13).

*Every count in this section is now a CITATION rather than a restatement, and that is a fix to a
class: three consecutive review rounds each caught a small-integer error in this one section
(round 1 over-promised the non-vacuity pairing by two, round 2 under-enumerated it by two, round
3 found "twelve needles" against a table of thirteen). Each of those numbers was derivable from a
section that states its members — so this section names the member-stating section instead, and
the arithmetic stops being something a reader has to re-check.*

**Counting walls ship their claimed match-shapes as fixtures (WI-235).** This item's zero-count
oracles are the rows the table below derives — every one of them a count of structural matches.
`matches == 0` is satisfied
identically by a predicate that resolves every claimed shape and by one that resolves almost
none, so Task 2 drives every claimed shape AND a near-miss through each predicate's own
function — the same function the live sweep calls, never a re-implementation — as green
fixtures on every floor run. The near-misses are named in Task 2 and are the load-bearing half:
without `orchestrator/docs/x.md` and a bare `Smith.md` as asserted non-matches, the docs scan
could pass by matching everything and later be narrowed back with nothing checking that the
narrowing kept the claimed shapes. **And the direction of repair is fixed in Task 2 rather than
left to whoever meets the red**, because a near-miss list is the one place in this item where an
authoring slip and a legitimate narrowing look identical from inside the build: where a plant
and a correct predicate disagree, the PLANT is wrong unless D8's rule is itself wrong, and the
predicate is never narrowed to make a plant green. That rule exists because round 5 found a plant
asserting the opposite of D8's own rule for `prose_lines`, where the literal-instruction repair
would have removed a whole class of comment from the finding surface D11 rests on — invisible
afterwards, because `person.py` carries no instance of it. The same reasoning is why Task 12's marker scan — the one
oracle in this item whose matcher is a needle SET rather than a single needle — carries its own
near-miss (`Phase-4` and `email_index`, neither of which may be collected).

**Non-vacuity, paired one-for-one — and the table is DERIVED, not remembered.** Round 1's note
was that this claim over-promised by two; the fold that answered it then under-enumerated by
two, which is the same defect on the same sentence. So the pairing is no longer a list somebody
maintains. **The rule that generates the table:** sweep the Implementation Plan's task text and
the five criteria for every assertion whose oracle is a COUNT OF STRUCTURAL MATCHES EQUAL TO
ZERO, then give each one a positive — and the positive must discharge the same thing in every
row, namely that THE MATCHER CAN FIND ITS SHAPE AT ALL, which no property of the data the
matcher ran over can supply. That splits into two sub-classes, stated apart so neither drifts
out of the table one member at a time. Where the matcher is a **literal-string scan**, the
positive is always the same two-part control (the file list is non-empty; the same assembled
needle IS found over a scratch directory holding one planted file containing it). Where it is
one of D8's four **structural predicates**, the positive is either the live run returning a
non-empty record set — available when the population the zero is about is not the whole of the
predicate's output, as in the `_phone_index` and `docs/`-mention rows — or, where the live
population is empty precisely BECAUSE the assertion holds, that predicate's own Task-2 shapes
fixture: the claimed match-shape driven through the same function and asserted collected. *Round
5 found the `resolve` row paired with a fact about the golden's size, which discharges neither
form; a row whose positive does not discharge the rule is the rule not being run, which is why
the rule is now stated as two sub-classes rather than one.* Run over the plan as it
stands, that sweep returns the rows below; **the number is deliberately not restated here** —
run the rule and count the rows, because a count written beside a table is exactly the artefact
that has been wrong three rounds running:

| zero-count assertion | its paired positive |
|---|---|
| zero non-materialized `_phone_index` loops (Task 8) | at least one `_phone_index` iteration site exists |
| zero unresolving `docs/` mentions (Task 10) | the docs scan returns a non-empty set of in-scope mentions |
| zero direct index reads in `resolve` (Task 9) | Task 2's `attribute_reads_in` fixture, which drives a read of a named attribute inside a named function through that same predicate and asserts it IS collected — the control that proves the matcher can find an attribute read at all, which is what this row's zero needs and what a golden's non-emptiness says nothing about |
| zero sites for `_email_index` under `PACKAGE_ROOT, TESTS_ROOT` (Task 6) | the two-part literal-scan control |
| zero sites for `_find_or_create_stub_legacy` under `PACKAGE_ROOT, TESTS_ROOT` (Task 11) | the two-part literal-scan control |
| zero sites for `paren-decoration-at-the-door` under `PACKAGE_ROOT, TESTS_ROOT` (Task 10) | the two-part literal-scan control |
| zero hits for every needle in D11's Tier A and Tier B tables (Task 12) | the two-part literal-scan control over every member of those two tables, PLUS a near-miss planted line (`Phase-4`, `email_index`, `legacy strategy`) the case-sensitive needles must NOT collect, PLUS the presence assertion that `stub_golden.json` and `resolve_golden.json` appear in `person.py` — so Tier B's `replay confirms zero` cannot go green by deletion |
| zero prose lines of `person.py` outside D11's authorized owners diverging from `prose_surface_cut0.json`, and zero prose lines owned by `_find_or_create_stub_legacy` (Task 12 clause (e)) | both surfaces are non-empty, AND every authorized owner has at least one Cut-0 line gone — so the diff cannot be satisfied by a predicate that returned nothing, nor by a build that landed no repair at all |
| zero comments asserting step 6 is filtered out absent a company hint (Task 10) | the REPAIRED step-6 comment is present at `resolve_all` and states that the branch records 0.6 and survives the floor — so the clause cannot go green by deletion |
| zero tests whose two legs both reach `resolve_or_create` (Task 11) | the same predicate DOES find the two-leg shape in a planted scratch module, since after Cut 4 the real population is empty |
| zero no-argument repository constructions in this item's `tests/`-root `.py` files, by the shipped `NO_ARG_CONSTRUCTION` pattern (Task 13, M3) | the file list is non-empty, and the same pattern run by the same scan over a scratch directory holding one planted file containing `PersonRepository()` DOES collect it |
| zero `prose_lines` records for those same files carrying a `#` whose trailing text contains `"""` or `'''` — Task 13's THIRD control, the one that stops the borrowed `_code_lines` scan from swallowing code beneath such a comment and reading as a clean zero | Task 2's `prose_lines` shapes fixture, whose case (ii) drives exactly that shape (`x = 1  # see the """ delimiter`) through the same predicate and asserts it IS collected as one record — the structural-predicate sub-class of the rule, since the live population here is empty precisely because the assertion holds (round 6's note: the row was owed by the rule stated two paragraphs above and was not returned when the rule was last run) |

The needle-assembled-from-parts control in Tasks 6, 10, 11 and 12 is a DIFFERENT control and all
are kept: it stops the check being its own counterexample (a check that spells the needle whole
finds itself), while the planted-scratch-file positive is what proves the scan can find the
needle at all. **D12 is a THIRD thing again, and the distinction is worth holding**: the
counterexample control is about a check finding ITSELF, and applies to the four scanning tasks
above; D12's self-collision rule is about a check in the SAME MODULE as a scanning check turning
that OTHER check red, and it therefore also binds Task 5's tripwire owner list and Task 9's AC-4
attrs argument, neither of which scans for anything. Both resolve to the same instruction —
assemble the name from parts — which is why they were conflatable for six rounds and why D12
states the rule over the module's source lines rather than over the clauses that happen to need
it today. Task 12's near-miss is the third control and belongs to WI-235's half rather than
to this one — without it the marker scan could pass by matching everything and later be narrowed
back with nothing checking that the narrowing kept the claimed shapes.

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
**`tests/test_name_validation.py`** and **`tests/test_company_name_contract.py`**. **Three** of
them are edited deliberately — `tests/test_resolve_or_create.py` (Tasks 4 and 11),
`tests/test_identity_index.py` (Task 7) and `tests/test_wi126_body_preservation.py` (Task 11) —
and each of the three is a declared `## Write Targets` path. No other module in this list may
change.

**The green boundary is the CUT, not the task — and there is exactly one place that matters.**
Cut 1 spans Tasks 6 and 7: Task 6 deletes `_email_index`, and until Task 7 lands,
`tests/test_identity_index.py:183-201` still asserts `"not-an-email" in repo._email_index` and
`"bad email" in repo._email_index`. So `test_malformed_email_skipped_but_legacy_indexes_it` and
`test_clean_and_junk_in_one_list_indexes_only_the_clean` go RED at the Task 6 boundary **by
design** — that red is the plan working, and it is named here so a builder does not read a flat
"green at every task boundary" as licence to repair the wrong side of it. **A third case joins
them for the same reason and from the same cause**: Task 6's own
`test_email_has_exactly_one_resolution_authority` asserts the `_email_index` needle at zero across
`PACKAGE_ROOT, TESTS_ROOT`, and those same three surviving `tests/test_identity_index.py` sites
are what Task 7 removes — so it too is red at the interior boundary and green at the commit. The
authorized set at this boundary is therefore exactly those three cases, all of them the SAME
three tests-root sites seen from two directions, and all of them closed by Task 7's edit. **Tasks
6 and 7 land as ONE commit**; the invariant is that the tree is green at every COMMIT boundary,
and every other task in the plan is its own commit and its own green. A red at any other
boundary, or a FOURTH red case at this one, is a defect.

**What makes "every other task is its own green" true rather than hoped-for is D12**, and it is
worth saying here because round 6 found it false in two places. Three of this item's zero-count
assertions scan a root that CONTAINS `tests/test_identity_endgame.py`, so any later task ordered
to spell one of those three literals in that module would go red at its own boundary against a
correct build — Task 9's AC-4 attrs list and Task 12's clauses (e)/(e3) were exactly that, and
Task 5's tripwire owner list was a third the round did not name. D12 closes the class by
assembling every such name from parts, and disposes of the four remaining spellings under
`tests/` — Task 4's two parity legs, `test_wi126_body_preservation.py:212`, and
`test_identity_index.py`'s three sites — through its CO-LANDING arm, which is the SAME commit
discipline this paragraph already states for Tasks 6+7 and 11. So the authorized red set stays at
three, and a red at Task 5's, 9's, 11's or 12's boundary is a defect whose repair is to assemble
the name, never to narrow a scan.

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

Originated cold-start in approval-only mode, re-derived from the frozen `## Intent`, and **FROZEN**: Dave signed this set, and **the `## AC Sign-off` fence at the foot of this document is the in-force record** — it is the single place the hash, the artifact and the escalation are stated, and nothing here restates any of them. Read this section as signed, not as editable. *(That is a deliberate change of shape, not a tidy-up. `ac_hash` is `hash_section(body, "Acceptance Criteria")` — the whole section, this preamble included — so a preamble that names the hash of the section it sits inside falsifies that hash the moment it is edited to be correct. It went stale twice on exactly that loop; pointing at the fence instead cannot.)* What this preamble does carry is the substantive disclosure a diff alone would not explain: since origination the only refinement to a criterion's TEXT is that AC-1's weak-identity citation was re-anchored from the bare `name_validation.py:385-387` (which names an unrelated Tier-1 `arrow_connective` branch-table entry) to the symbol `obsidian_schemas/name_validation.py:weak_identity_reason:531-532`, which is the clause the criterion was always about and the one D3 already cited correctly — a citation repair that changes no promise. Every `check` is a top-level zero-argument `def test_*(` in `tests/` that signals failure by raising.

```criteria
id: AC-1
desc: The duplicate is gone and a REAL oracle outlives it. `_find_or_create_stub_legacy` appears at zero sites across `obsidian_schemas/` and `tests/` — asserted as a LITERAL-STRING scan over the source TEXT of every file `tests/derivations.py:python_files_under` returns for those two roots, so that the 126-line `def` itself, every caller, and any comment or string mention are all in the scan's reach; never as a check against person.py:699 by line, and explicitly NOT via `functions_calling`. Both of the duplicate's consumers go with it, named: the vacuous parity cases at `tests/test_resolve_or_create.py:189-211` and `:214-224`, and `test_legacy_preserves_rich_note` at `tests/test_wi126_body_preservation.py:209-215`, whose engine twin at `:200-207` is left standing to carry the WI-126 body-preservation property alone. And no test's two legs both reach `resolve_or_create`, which is the tautology those six cases are in today. In its place a committed golden file records, for every case in a derived case set, the `(resolved_name, created_new)` pair `find_or_create_stub` returns; a test re-runs the identical cases against a fixture vault seeded from the golden's own declaration and asserts every pair matches. The case set is DERIVED from the fixture vault rather than hand-picked — that vault being E8's **ten-note roster, complete and cited rather than re-derived** — and the derivation is stated per branch, so the coverage claim is CONSTRUCTED rather than asserted: for every note, one case per `emails:` entry (`name=<the note's name>, email=<the entry>` → Branch A, email hit); one case per `phones:` entry (`name=<the note's name>, phone=<the entry>` → Branch A, phone hit — reachable only because `Priya Raman` and `Tomas Villalobos` carry `phones:`, which no note on the earlier eight-note roster did); one case for every note carrying a `company:`, pairing that note's FIRST name token with that company and NO identifiers (→ Branch B, name+company reuse: 0.6 `partial-name` at person.py:610-612 plus the 0.25 company bump at :635-651 is exactly the 0.85 default threshold tested at :920, and `Tomas Villalobos` is the note that supplies it); and one not-present variant of each (→ Branch C, create). A note added to the fixture joins the sweep automatically, and a note carrying no phone or no company contributes no case to those arms — which is why branch coverage is guaranteed by the ROSTER, not by the sweep, and why the roster is fixed as literals in E8 rather than left to the build. Two constraints on the derivation, because either one silently weakens the sweep while it still reads as total: a not-present PHONE is not-present under `phones_match`, never merely under string equality (E8 invariant 2 — `10790055852` reads like a fresh number and is one `phones_match` arm away from `0790055852`), and a not-present NAME is MULTI-TOKEN, because a single-token name with no email and no phone hits the weak-identity guard at `obsidian_schemas/name_validation.py:weak_identity_reason:531-532` — case 1, `" " not in name and not email and not phone` — which `resolve_or_create` turns into a raised `WeakIdentityError` at `obsidian_schemas/repositories/person.py:resolve_or_create:934` instead of reaching `create_stub`. And because Branch C cases WRITE, the golden freezes the ORDERED case list as data and the test replays it in that order: a case order re-derived from a filesystem walk at test time is machine-dependent, and every note a create case mints is visible to every later case in the same run. The golden is DATA in the repository, not a value recomputed at test time from the code under test.
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
date: 2026-09-07
reviewer: dave
channel: cli
signed_at: 2026-09-07T08:43:05+01:00
provenance: verified
signoff_escalation: ESC-WI-023-specced-awaiting-ac-signoff-90fe7e3e
ac_hash: 1c4e35e50556
intent_hash: ce7e35a70ea0
ac_hash_AC-1: 97b4e402abd5
ac_hash_AC-2: 7523d81032ed
ac_hash_AC-3: a2ce8381aa34
ac_hash_AC-4: f21e51ef4ea0
ac_hash_AC-5: 0dec3196b520
artifact: docs/spec-reviews/WI-023-dave-review-2026-09-07.md
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

## Threat Model — 2026-09-07

**Recommendation: PROMOTE to threat-modeled**

Cold-start read of the whole document, then of the code at every citation this review rests on.
Prior gates' verdicts are carried forward as read: the CUTOVER arm (data-premise PROMOTE), E3's
phone carve-out, E6 arm (b), E8's declared alias asymmetry and Dave's AC sign-off are rulings I
route against rather than re-litigate. Nothing below asks for a change to signed criteria text.

### Trigger check

Four triggers fire, and one of them is the item's whole subject matter.

- **Handles input from external sources.** `get_by_email` is re-homed onto `Email.parse` (D4
  item 2), so an argument that reaches this library from three consumer repos — orchestrator's
  `contact_normalizer.py` directly, HAL9000's `entities.py` over HTTP — now reaches a parser on
  the READ path for the first time.
- **Persists data to user-owned files.** AC-1's sweep WRITES: Branch C mints notes and pre-cut
  Branch B calls `_writeback_identifier` through the WI-021 gate, whose `emails` arm rebuilds
  the list in place (`obsidian_schemas/name_gate.py:387-404`, re-read here — `result["emails"] =
  new_emails` at `:404` is an unconditional rebuild, so the spec's D3(b) hand-execution is right).
- **Crosses a trust boundary.** The Edge Cases entry claims the boundary is unchanged; that is
  correct in direction (the read path joins the parser the write door already uses) but it means
  the item now owns a parser call on untrusted input.
- **Identity resolution IS an authentication-adjacent surface.** `resolve()` answers "who is
  this?" for a contact cascade; a widening consolidation is a wrong-person answer, which is the
  spoofing class this repo's WI-019 and WI-103 were opened to stop.

No skip pattern applies — this is neither doc-only nor a behaviour-preserving refactor; the
document says so itself (E4: "a behaviour change, not a refactor").

### STRIDE review

**Spoofing.** The realistic threat here is identity confusion, not impersonation of a principal —
there is no principal. Two sub-cases, both already handled.

*Widening `resolve()`.* E4's three divergence classes each widen what `resolve()` claims, and a
literal thin head gets three of AC-4's four discriminants wrong. This is R2 and the mitigations are
in the plan rather than in prose: a golden recorded at Cut 0 and never re-recorded, D2's three
tripwires (of which clause 2 carries the pre-cut answers as literals in the check's own source, so
regeneration cannot reach it), four hand-stated discriminants, and Cut 3 allowed zero exceptions of
its own. D6's policy is forced by the code's structure rather than tuned — I re-executed the
argument at `obsidian_schemas/repositories/person.py:resolve:507` (`query_lower in name.split()` can
only be true for a whitespace-free query, so a multi-token query is answerable today only by steps
1–4, all of which score 1.0) and it holds. Nothing further is owed.

*The alias asymmetry.* `resolve`'s alias step (`person.py:488`) preempts its email step (`:493`),
so a person carrying someone else's address in `aliases:` is what `resolve()` returns for that
address. This is a pre-existing property that E8 pins as permanent and AC-2/AC-4(ii) assert from
both sides. Security-wise this item makes it strictly better: an unpinned asymmetry is one a later
"tidy the cascades" pass deletes or inverts by accident, and after this item it is a test. The
residual — an ingestion path that lands an attacker-influenced display name in `aliases:` could
steer `resolve()` for a victim's address — is real but pre-existing, out of this item's scope, and
its fix is a behaviour change to `resolve()` that this item explicitly forbids. Noted, not blocking.

**Tampering.** Two findings, one closed by the plan and one not yet.

*The concurrency rider is closed correctly.* `get_by_phone` iterates the live mapping
(`person.py:417`) while `_clear_indexes` calls `.clear()` on that same dict (`:326-333`) — WI-004's
explicitly-open half, and a genuine TOCTOU on shared mutable state. Cut 2's
`list(self._phone_index.items())` closes it, and D5's sharper predicate is right to replace AC-3's
own parenthetical: today's iterable is ALREADY a call, so the gloss alone is vacuously green. This
is a required mitigation and is declared as **M4** so D8 enforces the landing rather than the
criterion's weaker wording.

*The one gap this review adds: the item's new WRITING modules sit outside the wall that stops a
repository binding to the live vault.* `obsidian_schemas/repositories/base.py:_resolve_vault_path:94-104`
takes an explicit argument OR `OBSIDIAN_VAULT_PATH`, and raises only when BOTH are unconfigured —
and `_is_unconfigured:88-91` swallows a blank string, `""`, and `Path(".")`, so
`PersonRepository()`, `PersonRepository("")` and `PersonRepository(Path("."))` all silently bind to
whatever the environment names. On Dave's machine that variable IS set (`~/.zshenv`, recorded at
`SESSION_LOG.md:240` and relied on by `tests/test_vault_path_required.py:10-12`, which scrubs it for
exactly this reason). The wall that forbids caller-independent defaults,
`tests/test_vault_path_required.py:test_no_implicit_vault_path_defaults:312-331`, scans
`obsidian_schemas/` and `scripts/` only — D10's own table row says so — and the repo has no
`conftest.py`, so nothing scrubs the environment for a `tests/`-root module. This item adds three
modules under `tests/` that construct repositories, two of which WRITE:
`tests/identity_fixture.py` (Task 3), `tests/record_identity_golden.py` (Task 5) and AC-1's
mutating sweep in `tests/test_identity_endgame.py` (Task 11). They are under `tests/` deliberately,
to stay outside `test_write_routing.py`'s universe (D3) — which is the right call, and is also
precisely what puts them outside this wall.

The recorder is the sharp one: Task 5 runs it BY HAND, once, outside pytest, from the tree root
with the ambient environment (`cd <tree root> && …/.venv/bin/python -m tests.record_identity_golden`),
and it executes AC-1's mutating sweep. A repository constructed there without the seeded path
writes into the live 1147-note vault: ten minted `@<name>.md` notes (`Wilbur Achebe`, `Greta
Oyelaran`, … — D3's pinned not-present table) plus a Branch-B writeback that rebuilds real notes'
`emails:` through `gate_write`. That is data loss in Dave's vault from a test-root script, and no
standing check in this repo would catch it. The fix is mechanical and small, so it is declared as
required mitigations **M1**, **M2** and **M3** rather than a REVISE — the fold rule's own case.

**Repudiation.** No audit trail is lost. `_index_identifiers` (`person.py:264-289`) records
cross-entity identifier collisions to `_conflict_sets` and fires a loud WARN; Cut 1 does not touch
it, and making `_identifier_index` the email authority strengthens rather than weakens conflict
observability, because the index that answers is now the index that reconciles. `_resolution_conflicts`
is untouched. One asymmetry worth naming and not blocking: after Cut 1 an `emails:` entry
`Email.parse` refuses resolves through no door and is skipped silently (`_project_identifiers`'s
`except IdentifierError: pass` at `person.py:249-252`) with no skip-surface entry, since the note
itself parsed. The live population is 0 of 1021 (`docs/identity-cutover-corpus-audit.md` clause (b)),
the loss is pinned as a test with that number cited (Task 7), and D0's STOP door catches a
close-out re-run that flips it — so no logging is owed here.

**Information disclosure.** No secrets, credentials, tokens or scopes anywhere in this item;
the floor is hermetic and AC-5's check makes no subprocess, network or vault call. The one PII
surface is `docs/identity-cutover-corpus-audit.md`, which is vault-derived and tracked. As committed
it discloses nothing — clause (b) is the explicit "no matches" marker, clause (c) is 0/0 — and only
counts and consumer SHAs are recorded. The tension to be aware of, rather than to fix now: the
precondition fence's shape contract and AC-5 both require refused entries "quoted with its note and
reason", while `## Verification`'s close-out says "only the counts are recorded". Those pull opposite
ways in the nonzero world. They do not collide today, and D0 routes a nonzero close-out to a STOP
and a spec revision rather than to an artifact update, so no builder is ever put in the position of
pasting live addresses into a tracked file. Non-blocking; recorded so whoever re-runs the audit after
a flip decides that deliberately.

Pre-existing and unchanged: `_index_identifiers`'s conflict WARN carries the identifier key, which
for email is the address. That is today's behaviour, the logger belongs to the consumer, and this
item neither widens nor narrows it.

**Denial of service.** Nothing realistic. `Email.parse` (`obsidian_schemas/identifier.py:144-169`)
is pure string operations — `parseaddr` only for genuine angle-bracket forms, then `strip`/`lower`/
`count`/`partition` — with no regex and therefore no backtracking surface, so putting untrusted
input on it costs nothing. `get_by_phone`'s fuzzy scan is O(n) over 276 live values and Cut 2 adds
one O(n) materialization per miss; `resolve` step 5 is O(n) over 1147 cache entries. Both are
unchanged in order and negligible at this corpus size. R6 already discloses the real cost — Task 14's
five `-S` subprocesses per floor run — and that is developer latency, not availability.

**Elevation of privilege.** No scopes, no permissions, no sudo path. The only process-spawning
surface is the interpreter bridge, and I read it rather than assuming it:
`tests/ac_interpreter.py:96-155` validates that argv is exactly the conveyor's three-element
bootstrap shape, resolves the module path and requires it to BE the calling module, matches the
check name against `^test_[A-Za-z0-9_]+$`, builds an argv LIST (no shell), `os.execve`s it with a
`DELEGATION_SENTINEL` loop guard, and raises with a hand-runnable command on every unrecognized
shape — fail-closed, never degrading to green. Task 14 generalizes `WORK_ITEM_DOC` to a tuple,
which widens which documents the wall reads to discover check names, not what it may execute:
names still come from `criteria` fences, still match that pattern, and still must resolve to a
unique module under `tests/`. Nothing owed.

### Mitigations verified in place

1. **Arm selection is data, not a build-time judgement.** D0 + the committed corpus audit, with a
   conductor close-out re-run and an explicit STOP door rather than a mid-build arm switch.
2. **Oracle-defeat is machine-checkable.** D2's three tripwires plus the shared-vault literal; R3.
3. **Consumer contracts fail closed and unchanged.** `find_or_create_stub`'s signature, return
   shape and exception set, and the `normalize_phone`/`phones_match` compat re-export
   (`person.py:78-85`), are named as untouchable in `## Scope Boundary`.
4. **Loud-fail is preserved.** `get_by_email` still returns `Optional[Person]` and raises nothing —
   an `IdentifierError` becomes `None`, the same answer a miss has always produced.
5. **Hermeticity is stated as a constraint** (E5, Prerequisites, `## Verification`) — what M1–M3
   below add is a CHECK for it on the three files where no standing wall reaches.

```mitigation
kind: required
id: M1
desc: tests/record_identity_golden.py binds every PersonRepository it constructs to the explicit temp path it just seeded, and refuses to run — before any sweep writes — if a repository's resolved vault_path is not that path
landed: Task 5
```

```mitigation
kind: required
id: M2
desc: tests/identity_fixture.py's seed_vault refuses a dest that base.py:_is_unconfigured would swallow (absent, blank, whitespace-only or "."), so a computed dest can never fall through _resolve_vault_path to OBSIDIAN_VAULT_PATH
landed: Task 3
```

```mitigation
kind: required
id: M3
desc: the wall-membership run also scans every file this item creates or edits under tests/ for no-argument repository construction, using the shipped NO_ARG_CONSTRUCTION pattern at tests/test_vault_path_required.py:382, because test_no_implicit_vault_path_defaults:312-331 scans only obsidian_schemas/ and scripts/
landed: Task 13
```

```mitigation
kind: required
id: M4
desc: get_by_phone's fuzzy scan iterates a materialized snapshot of _phone_index rather than the live mapping _clear_indexes mutates in place, asserted by the stronger predicate D5 states rather than by AC-3's "the iterable is a call" gloss, which is vacuously green against unchanged code
landed: Task 8
```

### Notes (non-blocking)

- **`get_by_email(None)` changes shape.** Today it raises `AttributeError` at `person.py:390`;
  post-cut `Email.parse(None)` raises `IdentifierError` (`identifier.py:145-146`), which D4 item 2
  catches, so the call returns `None`. D4 item 2's "exception set is unchanged — it still raises
  nothing" is true of the documented contract and this is a widening of accepted input, not a
  narrowing. Worth one sentence in the build log if a consumer relied on the crash; none does.
- **The alias-preemption residual** described under Spoofing is a pre-existing property this item
  makes explicit and testable. If it ever wants closing, it is a `resolve()` behaviour change and
  therefore a new item, not a fold here.
- **The audit artifact's quoting clause vs. the close-out's counts-only instruction** — recorded
  under Information disclosure. No action today (0 of 1021); a decision for whoever re-runs it if
  the arm ever flips.

```verdict
gate: threat-modeler
verdict: PROMOTE
date: 2026-09-07
model: claude-opus-5
note: No unsafe approach and no security gap in the design — the identity-confusion class (R2) is mitigated by a Cut-0 golden with tripwires regeneration cannot reach, Email.parse on the new read path is regex-free and fail-closed (identifier.py:144-169), and the interpreter bridge execs a validated argv list with no shell (ac_interpreter.py:96-155); the one real threat this review adds is mechanical and folds into existing tasks, so it is four mitigation fences rather than a REVISE — this item's three new repository-constructing modules live under tests/ (deliberately, to stay outside test_write_routing.py) and therefore outside test_no_implicit_vault_path_defaults:312-331, while base.py:_resolve_vault_path:94-104 silently falls back to OBSIDIAN_VAULT_PATH (set on Dave's machine) for an absent, blank or "." path, so the hand-run mutating recorder of Task 5 could mint ten notes and rewrite real emails: fields through gate_write in the live 1147-note vault with nothing in this repo catching it.
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

## Spec Review — 2026-09-07

**Round 5. Recommendation: REVISE — return to spec writer (one gap to fix)**

Rulings on record: the CUTOVER arm selected by the committed corpus audit (D0, data-premise PROMOTE), E3's phone carve-out, E6 arm (b) (the golden is never re-homed onto WI-016's fixture), E8's declared alias asymmetry, and Dave's AC sign-off are scope boundaries I route against rather than re-litigate.

Cold-start read of the whole document from line 1, then of the code at every citation, with no
reference to round 4's gaps list until the walk was finished. **Round 4's two blocking findings are
CLOSED and I re-derived both closures against the tree rather than reading the fold's account of
them** (below). One blocking finding this round. It is NOT another "the enumeration is one member
short" — I walked D11's surface for a sixteenth member and could not find one — it is a flat
contradiction between two sentences of this document about the SAME shape, in the fixture that is
supposed to prove D11's finding predicate can see what it claims to see.

### Citation verification

Every `file:line` and symbol-anchored citation was re-resolved against the tree and read for the
property it is cited for. **All verified.** The injected drift audit reported 36 symbol-anchored
citations resolved with 0 findings; I treated that as a floor and read the code at each regardless,
because a symbol that resolves can still mean something the spec does not claim.

- **D11's Tier A and Tier B site lists are exact, checked by scan rather than by sampling.** A
  literal scan over `obsidian_schemas/` returns `_email_index` at `:156`, `:197`, `:328`,
  `:341-342`, `:391`, `:494`, `:574`; `_find_or_create_stub_legacy` at `:675`, `:699`; `Phase-5` at
  `:675`, `:685`, `:710`, `:851`, `:879`; `Tries in order` at `:462`;
  `Build email, phone, and alias indexes` at `:193`; `legacy Strategy` at `:863`, `:871`, `:874`;
  `legacy best-hit` at `:865`, `:912`; and each Tier B literal at exactly one site
  (`zero parity risk` `:163`, `later deletion cut` `:165`, `during transition` `:233`,
  `resolves the old way` `:234`, `still indexes it` `:252`, `stops at the first cascade hit` `:521`,
  `bumped 0.65` `:538`, `person.py:~476` `:536`, `replay confirms zero` `:685`). All in `person.py`
  alone, and no needle has a site D11 does not name.
- **The three exclusions still hold and the `this cut` count is still five.** `per-kind` survives at
  `:161`, `:232`, `:252`, `:271`, `:370`; `permissive lookup` at `:162`; `this cut` unwrapped at
  `identifier.py:386`, `:411` and `person.py:242`, `:860`, `:875`, plus the wrapped sixth at
  `_resolve_identifier:950-951`.
- **The round-4 fold's own premises, re-derived rather than inherited.**
  `obsidian_schemas/repositories/base.py:_is_unconfigured:86-91` swallows `None`, a blank/whitespace
  string and `Path(".")`; `_resolve_vault_path:94-104` falls through to `OBSIDIAN_VAULT_PATH` before
  raising and does NOT `.resolve()`, so the M1 helper's `repo.vault_path == dest` comparison is
  sound on a temp path; `BaseRepository.__init__:144` assigns it. `NO_ARG_CONSTRUCTION` is at
  `tests/test_vault_path_required.py:382` and `_code_lines` at `:281`;
  `test_no_implicit_vault_path_defaults:312-331` really does walk `obsidian_schemas` and `scripts`
  only, and `_scanned_markdown_files:421-433` really does exclude `.git/.venv/docs/state/
  node_modules` from `REPO_ROOT.rglob("*.md")` — so D1's JSON-not-`.md` argument and D10's last row
  are both correct. **I also ran M3's own scan myself**: the only `\w+Repository\(\s*\)` matches
  anywhere under `tests/` are `test_vault_path_required.py:183` and `:222`, neither of which is a
  `## Write Targets` path, so Task 13's zero is satisfiable and non-vacuous.
- **The D10 wall rows re-check out.** `non_completed_write_sites` admits a function only if it
  contains a `write_text`/`write_bytes`/DOOR_NAMES *attribute* call or is one of the two
  `_SHARED_HELPERS` (`derivations.py:583`, `:604-617`) — `_find_or_create_stub_legacy` is neither,
  and neither is the new `select_resolution`, so `PERSON_FALSY_RETURN_FUNCTIONS`
  (`test_name_gate_wall.py:1048-1054`) is unmoved in both directions.
  `_check_the_ast_capability_stays_single_homed:1132-1145` and
  `test_derivations_are_single_sourced:73-97` are a set-EQUALITY on `ast` and a *required subset* of
  six names respectively, so four new exports and a `tokenize` import join legally.
  `tests/test_ac_interpreter.py:23-26` carries the `CORPUS_COUPLING` line, `:40` is the single
  `WORK_ITEM_DOC`, and `check_module:76-87` is the unique-`def` discovery rule D10's row names.
  `tests/test_corpus_fixture_coupling.py` does **not** exist in this project, so D9's
  declaration arm is the only one available and is correctly taken (the precedent modules
  `tests/test_company_name_contract.py:15` and `tests/test_ac_interpreter.py:23` both carry one, and
  both name a file rather than globbing `docs/**` — which is what Task 2 orders).
- **The four `fold` fences are well-formed and their `desc` values are byte-identical to the
  2026-09-07 mitigation fences.** `landed:` is `Task 5` / `Task 3` / `Task 13` / `Task 8`, each
  matching `^Task \d+$`, and each ordinal is defined in the plan. The dated heading
  `## Mitigation Folds — 2026-09-07` is accepted by the parser (`heading_matches` — exact or dated
  suffix, `work_item_linter.py:3263`), so D8c resolves.
- **I found each fold's `design` and `work` quotes where they claim to be and read the surrounding
  text, rather than judging the quoted pair alone.** M1's design sentence is in D3(b) beside the
  hand-run-recorder paragraph and its `work` is Task 5's; M2's is D1's seeder paragraph and Task 3's;
  M3's is D10's last-row justification and Task 13's; M4's is D5's closing "stated as the one
  requirement its two halves are" sentence and Task 8's. All four quotes are faithful, and in each
  case the surrounding text actually orders the work the mitigation asks for — M1's binding helper
  before any sweep write, M2's four swallowed `dest` values, M3's shipped-pattern scan over the
  eight `tests/`-root files, M4's `list(...)`-wrapped scan plus D5's stronger predicate.
- Re-read for the property, not merely resolved: person.py `:1-12` and `:78-91` (the
  `<module>`-owned prose the item does not touch), `:96-137`, `:140-182`, `:192-223`, `:225-262`,
  `:264-296`, `:326-333`, `:335-377`, `:379-392`, `:394-421`, `:458-510`, `:512-544`, `:545-656`,
  `:658-697`, `:699-732`, `:827-944`, `:946-966`, `:1315-1348`; base.py `:75-104`, `:124-181`;
  name_validation.py `weak_identity_reason:502-538` (the case-1 clause is exactly `:531-532`);
  derivations.py `:24`, `:183-206`, `:217-240`, `:284-297`, `:583-617`.

### AC drift taxonomy (Check 12)

**Zero criterion diffs.** The `## AC Sign-off` fence's five per-AC hashes
(`97b4e402abd5` / `7523d81032ed` / `a2ce8381aa34` / `f21e51ef4ea0` / `0dec3196b520`) are
byte-identical to `ac_item_hashes` in `docs/spec-reviews/WI-023-dave-review-2026-09-06-2.md`, whose
`frozen_acceptance_criteria` I read and spot-diffed against the live fences (AC-1's
`weak_identity_reason:531-532` anchor and its ten-note roster clause, AC-3's `44790055852` /
OUTER-vertex clause). Nothing to classify against the taxonomy — no strength-weakening, no
actor-swap, no scope-narrowing, no oracle-swap, no exception-carving-by-addition. Only the
section-level `ac_hash` moved (`a8c767cdccea` → `1c4e35e50556`), which is the round-3 preamble
rewrite and carries no promise. See the routing note below about the artifact the new fence names.

### Blocking issue

**1. Task 2's `prose_lines` fixture orders a NEAR-MISS that D8's own rule — and Task 2's own
collected list three clauses earlier — say is a MATCH, so the shapes test is RED against a correct
predicate and the cheapest repair narrows the surface D11's whole closure rests on.**

D8 states `prose_lines`' rule as total, and it is unambiguous on both halves:

> Emit one record per LINE of every `COMMENT` token and every `STRING` token that is an expression
> statement …
>
> `text` is the SOURCE LINE with leading and trailing whitespace stripped — not the token's own
> text, **so a comment and the code it trails yield one record carrying the whole line**.

Task 2 orders the fixture that drives the claimed shapes through that predicate. Its collected list
includes "**a trailing `#` comment on a code line**" (correct — one record, whole line). Its
near-miss list then says:

> … a code line containing a `#` inside a string literal and **a code line containing `"""` inside a
> comment**, NEITHER of which may be collected as prose.

The first near-miss is right: `x = "a # b"` tokenizes to a `STRING` token that is not an expression
statement and no `COMMENT` token, so the line contributes no record. **The second is the same shape
as the collected item.** `x = 1  # see the """ delimiter` tokenizes to `NAME OP NUMBER COMMENT
NEWLINE` — a `COMMENT` token — so `prose_lines` emits exactly one record for it, carrying the whole
line, per the rule above. A correct implementation FAILS Task 2's assertion.

Two things make this blocking rather than a nit, and the second is the one that matters.

- **It is a self-contradiction, not an under-specification.** Task 2 says the same shape is
  collected and not collected, four lines apart, so the builder cannot resolve it by reading harder.
  This document's own standard everywhere else is that an unfixed choice decides buildability.
- **One of the two faces silently narrows `prose_lines`.** The red lands at Task 2, the FIRST task
  in the plan, before `prose_surface_cut0.json` exists. From there the two moves on the table are
  (a) fix the fixture assertion, or (b) make `prose_lines` skip comment tokens containing `"""`.
  (b) is the one the task text literally instructs, and it removes a class of comment from the
  finding surface D11 is re-founded on — the "member no reading pass can be blamed for missing" it
  exists to prevent, and the same harm class D8's `docs_markdown_mentions` exclusion paragraph
  argues against for the cross-repo pointers. It is invisible afterwards, because `person.py`
  happens to carry no comment containing `"""`, so the Cut-0 snapshot and every later diff agree
  over a surface that is quietly one class small — and the predicate ships to the whole repo as a
  `tests/derivations.py` export.

The intent is recoverable and the repair is one clause: D8's rationale names both cases as things
that "defeat a LINE SCAN", which is true of both but means different things. For the `#`-in-string
case the line-scan defect is a false POSITIVE (no record is owed); for the `"""`-in-comment case it
is a state-tracking defect — the line IS a comment and IS collected, and what must NOT be collected
is the ordinary code that FOLLOWS it, which a `startswith`/delimiter line scan would swallow as a
docstring. **Suggested fix, in Task 2 and outside the frozen criteria:** state the two separately —
a code line carrying a `#` inside a string literal contributes NO record; a code line whose trailing
comment contains `"""` contributes exactly ONE record carrying the whole line, **and** the two
ordinary code lines after it contribute none. That second half is the near-miss the predicate must
not match, and it is the one the current wording was reaching for.

### Non-blocking notes

- **The regress signature is now visible and I am naming it rather than iterating it (WI-020).**
  Round 2's finding landed on the thing under review (four falsified `person.py` surfaces); round 3's
  landed on D11, the fold written to close that class; round 4's landed on D11's disposition
  predicate; this round's lands on the fixture that proves D11's finding predicate. Each fix created
  the surface the next finding landed on. This round's finding is different in KIND — a flat
  self-contradiction with a one-clause repair, not another completeness gap — and I swept for a
  sixteenth D11 member and did not find one, so I do not think a sufficiency ruling is owed today.
  But if a further round lands inside D11 or its predicate again, that is the point to escalate for
  a human sufficiency ruling rather than emit round 6, and I am recording the count here so the next
  gate does not have to reconstruct it.
- **`resolve_or_create:847-848` is the unnamed sibling of the `:878-879` member D11 does name.** It
  reads "the identifier-first core that the **Phase-4 adapter will run** `find_or_create_stub`
  through" — the same already-false-at-HEAD tense as ":878-879" ("Not yet wired into
  `find_or_create_stub`"), in the SAME docstring, thirty lines above it. D11 admits pre-existing
  falsehoods as members (`:878-879` and `resolve_all:534-539` are both marked "pre-existing"), so if
  the class takes one it should take the other; leaving it means Task 11's repaired tail says the
  swap has happened while the head of the same docstring says it will. Non-blocking because it
  depends on none of P1–P5, no check goes red either way, and it sits inside a docstring Task 11
  already rewrites — naming it here moves the discovery to spec time, exactly as D7 did for `:675`.
- **`## Verification`'s non-vacuity table pairs row 3 with something that is not a positive for it.**
  "zero direct index reads in `resolve` (Task 9)" is paired with "the golden's derived case and query
  lists are non-empty and re-derive to the same ordinals" — which proves the golden is not empty and
  says nothing about whether `attribute_reads_in` can find an attribute read at all. The real control
  exists (Task 2 drives a match and two near-misses through that predicate's own function), so
  nothing is unproved; the table should cite it, the way the WI-235 paragraph two paragraphs above
  already does. Worth taking because this is the fourth round in which this one section's pairing
  arithmetic has been off, and the fold's answer was to state the generating rule — a row whose
  positive does not discharge that rule is the rule not being run.
- **AC-2's "the tracked sources" is read at two different scopes by two tasks.** Task 10 reads the
  identical phrase in AC-5 as `python_files_under(PACKAGE_ROOT, TESTS_ROOT)` and says so in terms;
  Task 6 scopes AC-2's `_email_index` zero-count to `PACKAGE_ROOT` alone. Task 7 orders the
  tests-root cleanup ("Remove every remaining reference to the deleted attribute from `tests/`") but
  nothing asserts it. Self-catching in practice — a surviving `repo._email_index` reference raises
  `AttributeError` once the attribute is gone, so the floor reddens — but one root list would make
  the two readings of one signed phrase agree.
- **The `## AC Sign-off` fence names an artifact that is not in this tree.** The in-force fence
  records `ac_hash: 1c4e35e50556`, `signed_at 2026-09-07T08:43:05+01:00` and
  `artifact: docs/spec-reviews/WI-023-dave-review-2026-09-07.md`; `docs/spec-reviews/` holds only
  `WI-023-dave-review-2026-09-06.md` and `WI-023-dave-review-2026-09-06-2.md`. This is the conductor's
  to close, not the spec-writer's, and it is a recurrence of round 3's blocking issue 2 second half
  (which round 4 recorded closed) one re-sign later. It did not block Check 12 this round only
  because the fence's five per-AC hashes are byte-identical to the `-2026-09-06-2` artifact's, which
  pins the criterion text without needing the newer file — but that is luck, not method: a re-sign
  that DID move a criterion hash would leave Check 12 with no readable referent.
- **D10's last row transcribes the shipped pattern without its escaped parens** — it writes
  `\w+Repository(\s*)` where `tests/test_vault_path_required.py:382` is
  `re.compile(r"\w+Repository\(\s*\)")`. Nothing is built wrong: Task 13 orders the pattern IMPORTED
  rather than re-spelled, and the M3 fold record quotes that instruction. A transcription nit in a
  table whose whole value is exactness.

### Carried-forward notes

Every still-open note from every prior round, re-checked against the tree rather than against the
fold's account of it.

- **Round 4 blocking 1 (D11's `(e2)` false for two of fifteen owners) — CLOSED, and on the arm that
  cannot recur one level down.** Authorization is now a statement about PROSE: I re-derived the set
  from the table's ordered repairs and it is thirteen, each with at least one Cut-0 line the plan
  orders rewritten or deleted, hand-checked one owner at a time (`<module>` loses `:113`'s sentence;
  `__init__` loses `:156` and `:160-167`; `_index_entity` loses `:193` and `:194`;
  `_project_identifiers` loses `:231-234`; `_index_identifiers` loses `:271-273`;
  `_remove_entity_from_indexes` loses `:337`; `get_by_phone` loses `:416`; `resolve` loses
  `:462-467`; `resolve_all` loses `:519-523`/`:534-539`/`:615-617`; `find_or_create_stub` loses
  `:675-676`/`:682-685`; `_find_or_create_stub_legacy` loses all of `:709-712`; `resolve_or_create`
  loses `:851` and the Branch block; `_resolve_identifier` loses `:949-951`). `_clear_indexes` is out
  of the set and `(e1)` now pins its true `:327` docstring verbatim — I confirmed at the source that
  `:327` is the docstring and `:328` is the `self._email_index.clear()` CODE line `prose_lines` never
  emits. `select_resolution` is recorded as not a Cut-0 owner at all. The two `—` rows the fold warns
  must NOT be swept in are correctly non-exempt per-OWNER. Task 5's Cut-0 clause is over the TABLE's
  fourteen (all but `select_resolution`), which is the broader set and covers `_clear_indexes:327` —
  consistent, and I checked the two spellings of the set against each other.
- **Round 4 blocking 2 (four `kind: required` mitigations, no `## Mitigation Folds`) — CLOSED,
  substance first.** M1's binding-and-refusal clause is in D3(b) and Task 5 with the live-vault
  consequence named; M2's `dest` guard is in D1 and Task 3 with the not-vacuous env-var assertion;
  M3's row is added to D10 (declared as an ADDITION to the dated census rather than a member of it,
  which the census's own floor discipline permits) and the scan is in Task 13; M4 was already carried
  by D5 and Task 8. Four complete records, `desc` verbatim, no `## Write Targets` fence moved.
- **Round 4 note 1 (D11's table missing `_find_or_create_stub_legacy`) — CLOSED**; the row is present
  with `Task 11` in the lands-in column, and the table's owner column is now the thirteen plus two
  declared non-members, which is fifteen and matches the prose.
- **Round 4 note 2 (the preamble edit moves `ac_hash`, a conductor D4b act) — actioned by the
  conductor**; a 2026-09-07 re-sign is recorded. Its artifact is missing — see the routing note above.
- **Round 4 note 3 (D4 item 2's "exception set is unchanged" stronger than the code) — CLOSED.**
  D4 item 2 and the `## Edge Cases` error-propagation entry both now name `get_by_email(None)`
  explicitly as a widening, with `identifier.py:Email:145-146` cited; I re-read `get_by_email:390`
  and confirmed today's `AttributeError` and the post-cut `None`.
- **Spec review rounds 1–3's findings and notes — all still closed**, re-verified rather than
  assumed: D3(b)'s per-sweep seeding with the `gate_write` mechanism named at
  `name_gate.py:387-404`; AC-1's symbol-anchored weak-identity citation; Task 4's red-is-a-finding
  door; D2's ordinal 8 for `kit@localhost` (I re-derived the 39-query space and it comes out at 39,
  with Jane's four queries taking 1–4); the closed five-value `arm` vocabulary participating in the
  tripwire's `(ordinal, arm, query)` comparison; the three deliberately-edited test modules; Task 5's
  `__main__` guard and literal invocation; `## Verification`'s counts now citing D11's tables; the
  Task-6 transient red named as the CUT boundary with Tasks 6 and 7 as one commit; the
  `CORPUS_COUPLING` declaration ordered in D9, Task 2 and the `## Write Targets` `why`.
- **Architect rounds 3/4 and both red-team rounds — all folded and still folded.** The
  `_remove_entity_from_indexes` widening note stays closed by D0's arm selection (I re-read
  `:374-377`, which removes identifier keys through the same `_project_identifiers` projection that
  inserted them); the Branch-C variant names are pinned and off `tomas`/`villalobos`; the
  `arm`-not-branch record is D3's; the on-the-threshold 0.6 + 0.25 = 0.85 disclosure is in D1 and E8
  and Task 9 now repairs the `person.py` docstring that contradicts it.
- **Data-premise's three** — the cross-repo `orchestrator/docs/…` exclusion is D8's named exclusion
  with the line-wrap blind spot stated (I re-derived the class split and confirmed the
  starts-with-`docs/` clause excludes all three, including the wrapped tail); `person.py:675` is
  D7's; `:685` is D7's plus Task 12's presence clause on `stub_golden.json`/`resolve_golden.json`.
- **Threat model's three notes — still open, still non-blocking**: the `get_by_email(None)` shape
  change (now stated in D4 item 2 and Edge Cases, so effectively closed); the alias-preemption
  residual, which is a pre-existing property this item makes testable and whose closure would be a
  new item; and the audit artifact's "quoted with its note and reason" clause against
  `## Verification`'s counts-only close-out, which do not collide at 0 of 1021 and are routed to
  whoever re-runs the audit if the arm ever flips.
- **D11's own declared residual** — an authorized owner that loses a Cut-0 line for the WRONG reason,
  which `(e2)` cannot distinguish from the ordered repair landing (`resolve_or_create:867`'s
  "legacy's" is the live instance, pinned by no needle) — is **recorded, not re-raised.** It is
  disposed of in the document, the needle tiers are the stated mitigation, and re-litigating a
  disposition already on record is the treadmill direction.

```verdict
gate: spec-reviewer
verdict: REVISE
date: 2026-09-07
model: claude-opus-5
targets: Task 2, #design, #verification, Task 6, #ac-sign-off
prior: held
basis: folded-material
findings: 1/6
note: Round 4's two findings are closed and I re-derived both closures owner-by-owner against the tree (the thirteen authorized owners each lose a Cut-0 prose line; `_clear_indexes:327` is a docstring and `:328` is the CODE line `prose_lines` never emits; all four `fold` records are complete, `desc`-verbatim and their design/work quotes faithful at the sites they claim) — but Task 2's `prose_lines` fixture orders as a NEAR-MISS the very shape D8's rule and Task 2's own collected list call a MATCH: a code line whose trailing comment contains `"""` carries a COMMENT token, so the predicate emits one record for it, and the assertion "NEITHER of which may be collected" is RED against a correct build at the FIRST task in the plan — where the literal-instruction repair is to make `prose_lines` skip comments containing `"""`, silently removing a class from the finding surface D11's whole closure is re-founded on.
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

## Spec Review — 2026-09-07

**Round 6. Recommendation: REVISE — return to spec writer (one gap to fix)**

Rulings on record: the CUTOVER arm selected by the committed corpus audit (D0, data-premise PROMOTE), E3's phone carve-out, E6 arm (b) (the golden is never re-homed onto WI-016's fixture), E8's declared alias asymmetry, D11's declared residual (an authorized owner losing a Cut-0 line for the wrong reason), and Dave's AC sign-off are scope boundaries I route against rather than re-litigate.

Cold-start read of the whole document from line 1, then of the code at every citation, with no
reference to round 5's gaps list until the walk was finished. **Round 5's blocking finding is
CLOSED and I re-derived the closure against the tokenizer's actual behaviour rather than reading
the fold's account of it** (below). One blocking finding this round. It is not another
enumeration one member short and it is not inside D11's finding or disposition predicate — it is
a collision between two of this item's own zero-count scans and the module its own checks are
written in, and it goes RED at two task boundaries the plan declares must be green.

### Citation verification

Every `file:line` and symbol-anchored citation was re-resolved against the tree and read for the
property it is cited for. **All verified.** The injected drift audit reported 36 symbol-anchored
citations resolved with 0 findings; I treated that as a floor and read the code at each
regardless, because a symbol that resolves can still mean something the spec does not claim.

- **Round 5's own repair, re-derived against the tokenizer rather than against the fold.** D8 now
  states the two line-scan-defeating shapes apart and Task 2's fixture derives each expectation
  from D8's rule. Re-executed: `x = 1  # see the """ delimiter` tokenizes to
  `NAME OP NUMBER COMMENT NEWLINE` — a `COMMENT` token — so `prose_lines` owes exactly ONE record
  carrying the whole stripped line, and the two ordinary code lines beneath it owe none, which is
  the near-miss the old wording was reaching for. `x = "a # b"` holds no `COMMENT` token and its
  `STRING` token is part of an assignment rather than an expression statement, so it owes none.
  Both faces of the fold are correct and the predicate is not narrowed.
- **D11's Tier A and Tier B site lists are still exact, checked by scan rather than by sampling.**
  `_email_index` at `:156`, `:197`, `:328`, `:341-342`, `:391`, `:494`, `:574`;
  `_find_or_create_stub_legacy` at `:675`, `:699`; `Phase-5` at `:675`, `:685`, `:710`, `:851`,
  `:879`; `Tries in order` at `:462`; `Build email, phone, and alias indexes` at `:193`;
  `legacy Strategy` at `:863`, `:871`, `:874`; `legacy best-hit` at `:865`, `:912`; each Tier B
  literal at exactly one site (`zero parity risk` `:163`, `later deletion cut` `:165`,
  `during transition` `:233`, `resolves the old way` `:234`, `still indexes it` `:252`,
  `stops at the first cascade hit` `:521`, `bumped 0.65` `:538`, `person.py:~476` `:536`,
  `replay confirms zero` `:685`). All in `person.py` alone.
- **Round 5's newest member is where D11 now says it is.** `resolve_or_create:847-848` reads "the
  identifier-first core that the / Phase-4 adapter will run `find_or_create_stub` through" — the
  same already-false-at-HEAD future tense as `:878-879`, line-WRAPPED exactly as the table
  records, and `find_or_create_stub:688-696` delegates through it today.
- **The three exclusions still hold and the `this cut` count is still five.** `per-kind` survives
  at `:161`, `:232`, `:252`, `:271`, `:370`; `permissive lookup` at `:162`; `this cut` unwrapped
  at `identifier.py:386`, `:411` and `person.py:242`, `:860`, `:875`, plus the wrapped sixth at
  `_resolve_identifier:950-951`.
- **The four `fold` records are complete, `desc`-verbatim, and their quotes are faithful where they
  claim to be** — I found each quote at its claimed site and read the surrounding text rather than
  judging the pair alone. M1's design sentence sits in D3(b) beside the hand-run-recorder paragraph
  and its work is Task 5's (the ONE binding helper, the refusal before any sweep write, and the
  not-vacuous unit assertion with `OBSIDIAN_VAULT_PATH` set to a scratch dir); M2's is D1's seeder
  paragraph and Task 3's; M3's is D10's last-row justification and Task 13's; M4's is D5's closing
  "stated as the one requirement its two halves are" sentence and Task 8's. Each `desc` is
  byte-identical to its 2026-09-07 fence, each `landed:` ordinal is defined in the plan, and in
  each case the surrounding text actually orders the work the mitigation asks for.
- **The threat model's and the folds' premises, re-derived rather than inherited.**
  `base.py:_is_unconfigured:86-91` swallows `None`, a blank/whitespace string and `Path(".")`;
  `_resolve_vault_path:94-104` falls through to `OBSIDIAN_VAULT_PATH` before raising and does not
  `.resolve()`, so M1's `repo.vault_path == dest` comparison is sound; `BaseRepository.__init__:144`
  assigns it. `NO_ARG_CONSTRUCTION` is at `tests/test_vault_path_required.py:382` and `_code_lines`
  at `:281`, and its delimiter scan really is the `startswith`/odd-count line scan at `:295-307`,
  including the even-count `for`/`else` fall-through Task 13 names as its residual. **I ran M3's
  scan myself**: the only `\w+Repository\(\s*\)` matches under `tests/` are
  `test_vault_path_required.py:183` and `:222`, neither a write target, so Task 13's zero is
  satisfiable. **And I ran Task 13's third control myself over the five pre-existing modules this
  item edits** (`derivations.py`, `test_resolve_or_create.py`, `test_wi126_body_preservation.py`,
  `test_identity_index.py`, `test_ac_interpreter.py`): no comment in any of them carries a
  triple-quote delimiter, so that assertion is green against the files as they stand and the
  authoring constraint binds only new text.
- **Task 6's both-roots claim is exact about today's tree and that is what makes the finding
  below sharp.** A literal scan for `_email_index` under `tests/` returns exactly three sites —
  `tests/test_identity_index.py:184`, `:189`, `:201` — all of which Task 7 rewrites, as the task
  says.
- Re-read for the property, not merely resolved: person.py `:105-137` (the `<module>`-owned
  pointer at `:110-113` above `_TRAILING_PAREN_RE:114` and outside `_split_trailing_paren:117`),
  `:140-182`, `:192-223`, `:225-262`, `:264-296`, `:326-333` (`:327` the docstring, `:328` the
  `self._email_index.clear()` CODE line), `:335-377`, `:379-392` (`get_by_email`'s body carries no
  comment at all), `:394-421`, `:458-510`, `:512-544`, `:545-656`, `:658-697`, `:699-732`,
  `:840-944`, `:946-966`, `:1149-1180`; base.py `:75-104`, `:124-181`, `:225-245`, `:462-486`;
  name_gate.py `gate_write:378-404` (the `emails` arm's unconditional rebuild at `:404`, and
  `migrations = whole_record and …` at `:385`); derivations.py `:24`, `:183-206`, `:217-240`,
  `:583-617`; tests/ac_interpreter.py `:54`, `:96-155`; tests/test_ac_interpreter.py `:23-26`,
  `:40`, `:57-95`, `:98`; tests/test_vault_path_required.py `:255-331`, `:378-388`.

### AC drift taxonomy (Check 12)

The in-force `## AC Sign-off` fence's artifact is now present:
`docs/spec-reviews/WI-023-dave-review-2026-09-07.md` (`ac_hash 1c4e35e50556`,
`signed_at 2026-09-07T08:43:05+01:00`), and its five `ac_item_hashes` are byte-identical to the
fence's. I diffed the five evolved `criteria` fences against that artifact's
`frozen_acceptance_criteria`. **Zero criterion diffs** — AC-1 through AC-5 byte-identical,
`check:` and `kind:` unchanged on all five, and the preamble in the artifact is the live preamble.
Nothing to classify against the taxonomy: no strength-weakening, no actor-swap, no
scope-narrowing, no oracle-swap, no exception-carving-by-addition. Round 5's routing note about
the missing artifact is closed by the conductor.

### Task-definition and Write-Targets shape checks

Fifteen canonical task definitions, ordinals 1–15, unique. Every one carries exactly one
lowercase `verify:` declaration: eleven name a bare `test_` function, Task 1 declares `baseline`
with its reason, Tasks 4 and 15 declare `hand-run` with theirs. Task 14's name already resolves
(`tests/test_ac_interpreter.py:98`); the other ten are created by the build, which is D10b's
question, not D10a's. Every `landed: Task N` in the folds resolves to a defined ordinal. Each
task's write target is declared in `## Write Targets` and every declared path has a task that
writes it; `tests/test_vault_path_required.py` is IMPORTED by Task 13 and correctly not declared.
No verify command writes outside the declared set.

### Blocking issue

**1. Two of this item's checks are ordered to spell, in `tests/test_identity_endgame.py`, literals
that two other checks assert at ZERO across `TESTS_ROOT` — so each goes RED at the boundary where
it is written, and the cheapest repairs are narrowing a scan this item's evidence rests on or
weakening a signed criterion's check. Task 2 already states the rule that closes this; it is
scoped to plants alone.**

Task 2 states the constraint and its reason in terms:

> **no plant may contain any literal this item asserts at zero.** … it never spells
> `_email_index`, `_find_or_create_stub_legacy` or `paren-decoration-at-the-door`, because Tasks
> 6, 10, 11 and 12 scan `python_files_under(PACKAGE_ROOT[, TESTS_ROOT])` and
> `tests/test_identity_endgame.py` is under one of those roots: a plant spelling one of those
> needles turns another task's correct zero RED, and the cheapest repair from that red is
> narrowing the scope of a scan this item's whole evidence rests on.

That reasoning is right, and it is not about plants. It is about the module. All five acceptance
checks and the derivation, roster, tripwire, prose-surface and wall-membership tests live in one
file (`## Write Targets`: "Tasks 2, 3, 5, 6, 8, 9, 10, 11, 12, 13"), and two of them are ordered
to spell a zero-asserted literal outside a plant:

- **Task 9 must spell `_email_index`, and Task 6 asserts it at zero across both roots.** Task 9
  orders AC-4's structural clause as "`attribute_reads_in` over `PersonRepository.resolve` for
  `_cache`, `_alias_index`, `_email_index`, `_phone_index` is empty" — an argument list, not a
  needle, so Task 6's "built from parts … never spelled whole" does not reach it. Task 6's clause
  is `python_files_under(PACKAGE_ROOT, TESTS_ROOT)`, and `tests/test_identity_endgame.py` is under
  `TESTS_ROOT`. Task 6's own text enumerates today's tests-root population as exactly the three
  `tests/test_identity_index.py` sites Task 7 removes; it does not account for the site Task 9
  adds. So `test_email_has_exactly_one_resolution_authority` is green at the Tasks 6+7 commit and
  goes RED at Task 9's — a boundary `## Verification` declares "is a defect" ("The authorized set
  at this boundary is therefore exactly those three cases … A red at any other boundary … is a
  defect"). The builder's three moves are: assemble the literal from parts (right, and used four
  times elsewhere), scope Task 6's clause back to `PACKAGE_ROOT` (which un-does round 5's own
  fold and re-splits one signed phrase across two scopes), or drop `_email_index` from AC-4's
  attribute list (which weakens a signed criterion's check). Nothing in the document picks.
- **Task 12 must spell `PersonRepository._find_or_create_stub_legacy`, and Task 11 asserts that
  string at zero across both roots.** Clause (e3) names that owner literally, and clause (e)
  builds its authorized list "from that paragraph" — D11's thirteen, one of which is
  `._find_or_create_stub_legacy`. Both are owner qualnames the check needs as strings, and
  neither is covered by Task 12's "every needle spelled as a literal assembled from parts", which
  its own preamble scopes to clauses (a)–(d). AC-1's scan is `python_files_under(PACKAGE_ROOT,
  TESTS_ROOT)` — frozen criterion text — so `test_legacy_stub_is_gone_and_the_golden_is_the_oracle`
  is green at Task 11's commit and RED at Task 12's. Task 12's clause (a) would not catch it
  first: (a)–(d) run over `PACKAGE_ROOT` alone, and D11 says that narrowing is deliberate.

Why this blocks rather than rides as a note: both reds land against a *correct* build, at
boundaries the plan says must be green, with no diagnosis in front of the builder — and in each
case one of the available repairs is the harm class this document names repeatedly (a scan
narrowed until it passes). It is also the one place in the item where an authoring slip and a
legitimate narrowing look identical from inside the build, which is the situation Task 2's own
"the direction of repair is fixed here rather than left to whoever meets the red" paragraph
exists for. And it is cheap: the rule is already written, one file over, for a subset of its
domain.

**Suggested fix, in the plan and outside the frozen criteria — close the CLASS, not the two
sites.** Promote Task 2's constraint from a plant rule to a module rule, stated once where a
reader will find it (D8 or Task 2, cited by Tasks 9 and 12): *no literal this item asserts at zero
over a root containing `tests/test_identity_endgame.py` may appear whole anywhere in this item's
own `tests/`-root modules — not in a plant, not in a check's argument list, not in an owner
qualname, not in a comment; where such a name is needed it is assembled from parts in the check's
own source, and `_phone_index` is the one such name that may be spelled because no assertion in
this document names it at zero.* Then name the two ordered sites so the rule is auditable rather
than remembered: Task 9's `attrs` list and Task 12's authorized-owner list plus clause (e3).
Stating it as a rule rather than as two clauses is what stops the next check that needs one of
these names — Task 13's file list is one edit away from needing `record_identity_golden`'s
siblings — from re-discovering it as a third instance.

### Non-blocking notes

- **The regress signature, updated rather than re-derived — and where I think the escalation line
  now sits.** Round 5 recorded the count and set the trigger: "if a further round lands inside D11
  or its predicate again, that is the point to escalate for a human sufficiency ruling rather than
  emit round 6." This round's finding is not inside D11's finding predicate (`prose_lines` is
  correct and I could not find a sixteenth member) nor its disposition predicate (the thirteen
  authorized owners each lose a Cut-0 prose line, re-derived below), and one of its two instances
  (Task 12 vs Task 11) has been latent since round 4 and was not created by any fold. But the
  other instance was created by round 5's own fold — widening Task 6's scan to both roots is what
  put Task 9's argument list inside it — so the "each fix creates the surface the next finding
  lands on" shape is still live, at magnitude 1. I am emitting rather than escalating because the
  repair is one rule the document already wrote for a subset of its domain, and because a known
  build-time red against a correct build is not something to hand forward. **If a seventh round
  lands anywhere inside this item's check-module machinery — D11, `prose_lines`, Task 2's
  fixtures, or the zero-count scans' own literals — that is the point to stop and ask Dave for a
  sufficiency ruling on the prose-class apparatus rather than buy another round.** Recording it
  here so the next gate inherits the count (rounds 2→6, five consecutive rounds inside the
  documentation-truth apparatus) instead of reconstructing it.
- **`## Verification`'s non-vacuity table omits one row its own generating rule returns.** The rule
  is "sweep the Implementation Plan's task text and the five criteria for every assertion whose
  oracle is a COUNT OF STRUCTURAL MATCHES EQUAL TO ZERO". Task 13's third control — "no line
  `prose_lines` returns for any of these files carries a `#` whose trailing text contains `"""` or
  `'''`" — is exactly that, and it has no row. Nothing is unproved: the positive exists, because
  Task 2's `prose_lines` shapes fixture drives that very shape through the predicate and asserts it
  IS collected, which is the structural-predicate sub-class the rule names. The table should cite
  it, the way row 3 now cites the `attribute_reads_in` fixture. Raised as a note, not a finding,
  for the same reason round 5 raised its sibling: the control is real and only the citation is
  missing. It is worth taking because the row was added in the same fold that restated the
  generating rule — the rule was stated but not re-run over the clause the fold itself added.
- **One span disagrees with itself by a line.** D11's table gives
  `find_or_create_stub:682-685` for the two-sentence P1/P5 repair; Task 11 gives `:682-684` for
  the same repair. The sentences are at `:683-685` and `:685-686`, and both Tier A (`Phase-5`) and
  Tier B (`replay confirms zero`) pin `:685` correctly, so nothing is built wrong and the needles
  are exact. A transcription nit in a table whose value is exactness.

### Carried-forward notes

Every still-open note from every prior round, re-checked against the tree rather than against the
fold's account of it.

- **Round 5 blocking 1 (Task 2's `prose_lines` near-miss contradicting D8's rule) — CLOSED, and on
  the arm that cannot recur as a clause.** The fold is a RULE: every planted line's expectation is
  derived by applying D8's rule to that line's tokens, and where a plant and a correct predicate
  disagree the plant is wrong unless D8's rule is. D8 now states the two line-scan-defeating shapes
  apart, in the opposite directions they actually defeat it; Task 2 asserts both halves of (ii),
  including the two ordinary code lines beneath. I re-executed both against the tokenizer rather
  than reading the fold's account. The declared sweep over the other three predicates landed three
  new plants (`materialized`'s five-wrapper vocabulary driven by a second wrapper,
  `attribute_reads_in` driving a `Store` and a nested `def`, `docs_markdown_mentions` driving a
  docstring-borne mention) and the two `attribute_reads_in` clauses D8 now states.
- **Round 5 note (`resolve_or_create:847-848`) — CLOSED**; the row is in D11's table marked
  pre-existing, `lands in` Task 11, and Task 11 orders both ends of that docstring repaired in one
  edit with the reason stated.
- **Round 5 note (`## Verification` row 3 mispaired) — CLOSED**; the rule now splits into two
  sub-classes and row 3 cites Task 2's `attribute_reads_in` fixture rather than a fact about the
  golden's size.
- **Round 5 note (AC-2's "the tracked sources" read at two scopes) — CLOSED**; Task 6 now takes
  `PACKAGE_ROOT, TESTS_ROOT`, with the three surviving tests-root sites named and the Task-6
  interior red widened to three authorized cases. My blocking finding is a consequence of that
  closure, not a reopening of it — the closure is right and its unstated cost is one clause.
- **Round 5 note (the `## AC Sign-off` fence naming a missing artifact) — CLOSED by the
  conductor**; `docs/spec-reviews/WI-023-dave-review-2026-09-07.md` is present and I read it for
  Check 12.
- **Round 5 note (D10's last row transcribing the pattern without escaped parens) — CLOSED**; the
  cell now reads `\w+Repository\(\s*\)` and says it transcribes only to state meaning, the pattern
  being imported.
- **Round 4's two blocking findings and three notes — still closed**, re-verified rather than
  assumed: authorization is a statement about PROSE and the thirteen each lose a Cut-0 line
  (`<module>` `:113`; `__init__` `:160-167`; `_index_entity` `:193`/`:194`; `_project_identifiers`
  `:231-234`/`:236-238`/`:252`; `_index_identifiers` `:271-273`; `_remove_entity_from_indexes`
  `:337`; `get_by_phone` `:416`; `resolve` `:462-467`; `resolve_all`
  `:519-523`/`:534-539`/`:615-617`; `find_or_create_stub` `:675-676`/`:682-685`;
  `_find_or_create_stub_legacy` all of `:709-712`; `resolve_or_create` `:847-848`/`:851`/the Branch
  block/`:878-879`; `_resolve_identifier` `:949-951`); `_clear_indexes:327` is a docstring and
  `:328` the CODE line `prose_lines` never emits; `select_resolution` is not a Cut-0 owner; the
  four mitigation folds are complete with no `## Write Targets` fence moved; the
  `_find_or_create_stub_legacy` row is present; D4 item 2 and the Edge Cases entry both name the
  `get_by_email(None)` widening.
- **Spec review rounds 1–3's findings and notes — all still closed**, re-verified: D3(b)'s
  per-sweep seeding with the `gate_write` mechanism named (I re-executed the collapse of
  `["Jane Roe <jane.roe@example.com>", "jane.roe@example.com"]` to `["jane.roe@example.com"]`
  through `_writeback_identifier:1161-1174` → `update_fields:473-475` → `gate_write:387-404`);
  AC-1's symbol-anchored weak-identity citation at `weak_identity_reason:531-532`; Task 4's
  red-is-a-finding door; D2's ordinal 8 for `kit@localhost` (I re-derived the query space and it
  comes out at 39); the closed five-value `arm` vocabulary participating in the tripwire triple;
  the three deliberately-edited test modules; Task 5's `__main__` guard and literal invocation; the
  Task-6 transient red named as the CUT boundary; the `CORPUS_COUPLING` declaration ordered in D9,
  Task 2 and the `## Write Targets` `why`.
- **Architect rounds 3/4 and both red-team rounds — all folded and still folded.** The
  `_remove_entity_from_indexes` widening note stays closed by D0's arm selection (`:374-377`
  removes identifier keys through the same `_project_identifiers` projection that inserted them);
  the Branch-C variant names are pinned and off `tomas`/`villalobos`; the `arm`-not-branch record
  is D3's; the on-the-threshold `0.6 + 0.25 = 0.85` disclosure is in D1 and E8 and Task 9 repairs
  the `person.py` docstring that contradicts it.
- **Data-premise's three** — the cross-repo `orchestrator/docs/…` exclusion is D8's named
  exclusion with the line-wrap blind spot stated; `person.py:675` is D7's; `:685` is D7's plus
  Task 12's presence clause on `stub_golden.json`/`resolve_golden.json`.
- **Threat model's three notes — still open, still non-blocking**: the `get_by_email(None)` shape
  change (now stated in D4 item 2 and Edge Cases, so effectively closed); the alias-preemption
  residual, a pre-existing property this item makes testable and whose closure would be a new
  item; and the audit artifact's "quoted with its note and reason" clause against
  `## Verification`'s counts-only close-out, which do not collide at 0 of 1021 and are routed to
  whoever re-runs the audit if the arm ever flips.
- **D11's own declared residual** — an authorized owner that loses a Cut-0 line for the WRONG
  reason, which `(e2)` cannot distinguish from the ordered repair landing — is **recorded, not
  re-raised**; it is disposed of in the document with the needle tiers as its stated mitigation.

```verdict
gate: spec-reviewer
verdict: REVISE
date: 2026-09-07
model: claude-opus-5
targets: Task 9, Task 12, Task 2, Task 6, Task 11
prior: held
basis: folded-material
findings: 1/3
note: Round 5's finding is closed and I re-derived the closure against the tokenizer (a trailing comment carrying `"""` holds a COMMENT token, so D8's rule owes it one record and the near-miss is the two code lines beneath) — but two of this item's checks are ordered to spell, in `tests/test_identity_endgame.py`, literals two other checks assert at ZERO across TESTS_ROOT: Task 9's AC-4 clause names `_email_index` in its `attribute_reads_in` attrs list while Task 6 now scans both roots for that string, and Task 12's clause (e3) plus its authorized-owner list name `PersonRepository._find_or_create_stub_legacy` while AC-1's frozen scan takes both roots — so each goes RED at the boundary where it is written, against a correct build, and the cheapest repairs are re-narrowing Task 6's scope (undoing round 5's own fold) or dropping an attribute from a signed criterion's check; Task 2 already states the rule that closes this and scopes it to plants alone.
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

## Spec Review — 2026-09-07

**Round 7. Recommendation: PROMOTE to ready**

Rulings on record: the CUTOVER arm selected by the committed corpus audit (D0, data-premise PROMOTE), E3's phone carve-out, E6 arm (b) (the golden is never re-homed onto WI-016's fixture), E8's declared alias asymmetry, D11's declared residual (an authorized owner losing a Cut-0 line for the wrong reason), and Dave's AC sign-off are scope boundaries I route against rather than re-litigate.

Cold-start read of the whole document from line 1, then of the code at every citation, with no
reference to round 6's gaps list until the walk was finished. **No blocking finding this round.**
Round 6's finding is closed, and I re-derived the closure by running its own sweep against the
tree rather than reading D12's account of it.

### Citation verification

Every `file:line` and symbol-anchored citation re-resolved and read for the property it is cited
for. **All verified.** The injected drift audit reported 37 citations resolved with 0 findings; I
treated that as a floor and read the code at each regardless.

- **Re-executed, not merely resolved.** E3's triangle against `phone_normalization.py:phones_match:58-90`
  (the UK arm at `:79-80` returns eagerly, so `("44790055852","10790055852")` never reaches the US
  arms → False; the other two pairs are True) and E8's three `get_by_phone` lookups against the
  two-phone index; `Email.parse` on all five plant shapes at `obsidian_schemas/identifier.py:Email:143-169`
  — `kit@localhost` refused at `:167-168` for `"." not in domain`, `" dana@example.com "` stripped at
  `:159`, and (the one that decides AC-2's whitespace variant) `" Jane Roe <jane.roe@example.com> "`
  routed through `parseaddr` at `:154-156` and accepted, so surface 1 and surface 2 agree on the
  padded angle-bracket form rather than splitting; D6's seven-row policy table against
  `resolve:458-510` and `resolve_all:512-656`, including that `0.6 + 0.25` is bit-exactly `0.85` in
  IEEE double so Branch B's `>= threshold` at `:920` really does hold with zero slack.
- **I re-derived AC-4's whole derived space and replayed the policy over it.** Roster order gives
  39 queries after the one `pat@example.com` collapse (4+4+4+4+4+4+3+4+4+4), `kit@localhost` lands
  at ordinal 8 as D2 says, and every one of the 39 reproduces pre-cut `resolve()` under
  `select_resolution` except E7's two enumerated rows. The two that could have been a third and
  fourth exception are the ones I checked hardest: `Jane Roe <jane.roe@example.com>` queried by its
  literal is multi-token and scores 1.0 `email` post-cut (step 5's 0.65 `token-subset` is recorded
  second and `record` at `:558-565` keeps the higher), and `pat@example.com` is a single-token 1.0
  tie broken by `_RESOLVE_CASCADE_ORDER` to the alias owner.
- **AC-1's twenty cases hand-executed for the three whose runtime branch moves at Cut 1.** Jane,
  Kit and Dana all return the same `(name, created_new)` pair on both sides; the two fresh phones
  `33612345678`/`33698765432` are not-present under `phones_match` (neither starts `44`/`0`, neither
  is an 11-digit string starting `1`) and not merely under string equality; ordinal 20's
  `Delphine Marchetti` has no candidate for the company bump to lift (`resolve_all:635-651` lifts,
  never creates).
- **D11's Tier A and Tier B site lists, the three exclusions and the thirteen authorized owners' repairs
  re-checked by scan.** All sites exact and all in `person.py` alone; `find_or_create_stub:683-686`
  now spans both sentences correctly in D11's table AND in Task 11 (round 6's span nit is closed);
  `_project_identifiers:238-242` survives with `:242`'s true `this cut`. Each of the thirteen loses
  at least one Cut-0 prose line, `_clear_indexes:327` is a docstring above the `:328` CODE line
  `prose_lines` never emits, and `select_resolution` is not a Cut-0 owner.
- **I ran D12's own sweep rather than reading its table.** A literal scan under `tests/` returns
  `_email_index` at exactly `tests/test_identity_index.py:184`, `:189`, `:201`;
  `_find_or_create_stub_legacy` at exactly `tests/test_wi126_body_preservation.py:212`;
  `paren-decoration-at-the-door` nowhere. Then I walked all fifteen tasks for any ordered spelling
  of one of the three outside a plant and found no site D12's table does not carry — Task 5's
  tripwire owner list, Task 6's needle, Task 9's `attrs`, Task 10's needle, Task 11's needle and
  Task 12's (a)/(e)/(e3) are the seven ASSEMBLED rows; Task 4, `test_wi126_body_preservation.py:212`
  and `test_identity_index.py`'s three sites are the four CO-LANDING rows; `derivations.py`,
  `identity_fixture.py`, `record_identity_golden.py` and `test_ac_interpreter.py` need none of the
  three. The derivation ("filter the zero-count table to assertions whose root list includes
  `TESTS_ROOT`") returns exactly those three literals and correctly leaves `_phone_index` out.
- **Round 6's blocking finding is closed on the arm that cannot recur as a clause.** D12 is a rule
  over source LINES of the item's own `tests/`-root modules, not two clauses; both instances the
  round named are now ASSEMBLED, and the sweep that stated the rule found the third site
  (Task 5's tripwire) the round did not name. `## Verification`'s boundary paragraph is updated to
  match, so the authorized red set stays at three cases at the Tasks 6+7 interior boundary.
- **Premises re-derived rather than inherited.** `base.py:_is_unconfigured:86-91`,
  `_resolve_vault_path:94-104` (falls through to the env var before raising, and does not
  `.resolve()`, so M1's `repo.vault_path == dest` comparison is sound), `BaseRepository.__init__:144`,
  `_adopt:158-181`; `name_validation.py:weak_identity_reason:531-532` case 1;
  `tests/test_vault_path_required.py:NO_ARG_CONSTRUCTION:382` and `_code_lines:281` — whose
  `for`/`else` at `:298-307` really does break without yielding on an even self-closing `"""`, the
  residual Task 13 names. `tests/__init__.py` exists and the suite imports `tests.derivations`, so
  Task 5's `python -m tests.record_identity_golden` from the tree root resolves; there is no
  `conftest.py`, which is what makes M1/M2/M3 owed. Exactly five ```criteria fences in this
  document, so Task 14's generalized `criterion_checks` (`tests/test_ac_interpreter.py:57-73`)
  discovers this item's five check names and nothing else.

### AC drift taxonomy (Check 12)

The in-force `## AC Sign-off` fence points at `docs/spec-reviews/WI-023-dave-review-2026-09-07.md`
(`ac_hash 1c4e35e50556`, `signed_at 2026-09-07T08:43:05+01:00`); its five `ac_item_hashes` are
byte-identical to the fence's. I diffed the five evolved `criteria` fences against that artifact's
`frozen_acceptance_criteria`. **Zero criterion diffs** — all five byte-identical, `check:` and
`kind:` unchanged. Nothing to classify: no strength-weakening, no actor-swap, no scope-narrowing,
no oracle-swap, no exception-carving-by-addition. Rounds 4, 5 and 6 each recorded that no
`## Acceptance Criteria` text was touched, and the diff confirms it.

### Task-definition, verify-declaration and Write-Targets shape checks

Fifteen canonical task definitions, ordinals 1–15, unique, each with exactly one lowercase
`verify:` declaration beginning its segment: twelve name a bare `test_` function, Task 1 declares
`baseline` with its reason, Tasks 4 and 15 declare `hand-run` with theirs. The four folds'
`landed:` ordinals (Tasks 5, 3, 13, 8) are all defined; their `work:` values quote a `verify:` key
mid-line, which is not a declaration. Every task's target is a declared `## Write Targets` path and
every declared path has a task that writes it; `tests/test_vault_path_required.py` is IMPORTED by
Task 13 and correctly not declared. No verify command writes outside the declared set — the one
writing module (`tests/record_identity_golden.py`) is hand-run at Task 5 and writes only declared
fixture paths and temp directories, and Task 5's own verify is the read-only tripwire.

### Fold records (D8c)

All four `kind: required` mitigations of the latest speaking `## Threat Model — 2026-09-07` have
complete, fresh records in `## Mitigation Folds — 2026-09-07`. Each `desc` is byte-identical to its
fence. I found each `design` and `work` quote at the site it claims and read the surrounding text
rather than judging the pair alone: M1's design sentence is in D3(b)'s hand-run-recorder paragraph
and its work is Task 5's ONE-helper binding with the not-vacuous unit assertion; M2's is D1's seeder
paragraph and Task 3's four swallowed values asserted with `OBSIDIAN_VAULT_PATH` live; M3's is D10's
last-row justification and Task 13's shipped-pattern scan; M4's is D5's closing "stated as the one
requirement its two halves are" sentence and Task 8's structural clause. In each case the
surrounding text orders the work the mitigation asks for, and M4's stronger predicate really is
strictly stronger than AC-3's vacuous "the iterable is a call" gloss — today's iterable at
`get_by_phone:417` already IS a call.

### Bar check

Walked every check of `docs/spec-quality-bar.md`. Spec satisfies the bar. OPEN items: none.
The universal claims that quantify over an enumerable domain — D11's prose surface, D10's wall
census, D12's literal sweep, the non-vacuity rule — each state the domain they walked and the
predicate they walked it with, and each declares its exemption classes in place
(`_clear_indexes` and `select_resolution` for D11; the PATTERN and DELIMITER members for D12;
the three cross-repository `orchestrator/docs/…` pointers and the vault-note filename
illustrations for `docs_markdown_mentions`). Printed HEAD literals: the corpus numbers (1147,
1021/0, 276, 0) are FROZEN artifact readings cited by pointer rather than restated in code — D4
item 5 replaces the stale in-code number with a pointer precisely so it cannot drift — and the
counts this document could have restated (39 queries, 20 cases, thirteen owners, the needle
tallies) are asserted by re-derivation or read off a member-stating table rather than pinned by
equality.

### Build-runner dry-run

Walked the Implementation Plan top to bottom as the build-runner. Every task names a concrete
file, a concrete edit and a runnable verification; the two hand-run tasks say why no standing
artifact can carry them. The three questions I would have asked are all answered in the document:
*which arm do I build?* (D0 — CUTOVER only, with a STOP door rather than a mid-build switch);
*what do I do when Task 4's repaired parity legs go red?* (Task 4 — a red is a FINDING, stop and
return the item, do not repair either side); *how do I write a check that must name a string
another check asserts at zero?* (D12 — assemble it from parts, never narrow the scan, with the
seven ordered sites tabled). No judgment call that could go either way.

### Minor notes (non-blocking)

- **Task 2 cites D12 for something D12 does not say.** Task 2 (`:1796-1798`) says `_phone_index` is
  "the one name a plant MUST spell literally … and D12 records it as the one such name that may be
  spelled". D12 never mentions `_phone_index`. Nothing is built wrong — D12's rule is derived by
  filtering `## Verification`'s zero-count table to assertions whose root list includes
  `TESTS_ROOT`, which returns three literals and excludes `_phone_index` on its own, so a builder
  following D12 literally reaches the right answer. A dangling cross-reference in a section whose
  value is that its rule is derived rather than listed.
- **D8's satisfiability sentence for `docs_markdown_mentions` overstates.** It says "at HEAD every
  `.md` mention anywhere in `obsidian_schemas/` sits in a comment or a docstring (no code constant
  names one)". Eight code constants name one: `repositories/base.py:198`, `:382`,
  `repositories/meeting.py:54`, `:231`, `repositories/book.py:53`, `:353`, `:355` and
  `repositories/person.py:1410`. The conclusion is unaffected and I checked it by hand rather than
  assuming: every one of those is preceded by `*`, `}` or `@`, none of which is in the
  `[A-Za-z0-9._/-]` class, so the pattern matches nothing on those lines and the in-scope set is
  still exactly the three D8 names. The rule is right; the sentence justifying it is not.
- **Task 13's third control has a second residual it does not name.** It asserts no `prose_lines`
  record for these files carries a `#` whose trailing text holds `"""` or `'''`. A `'''`-delimited
  DOCSTRING whose *text* carries a bare `"""` defeats `_code_lines` the same way — `:298-304` tests
  `'"""'` first and would set `in_docstring` on the wrong delimiter — and it carries no `#`, so the
  control does not see it. Task 13's stated authoring constraint already forbids it (a triple-quote
  delimiter appears "as a docstring delimiter or as a plant constant's delimiter"), so nothing is
  unowned; only the residual paragraph, which names the even-count case explicitly, is one member
  short of what it could claim. Raised as a note and not a finding for the reason round 6 set out:
  the control is real, the constraint covers it, and buying a machine form of it would cost more
  than it adds.
- **A one-line span nit of the kind round 6 caught elsewhere.** D11's table gives
  `_project_identifiers:236-238` for the stale "942 notes" claim; the claim is at `:236-237` and
  `:238` opens the slack sentence the same table orders KEPT at `:238-242`. Task 10 rewrites that
  whole docstring and D11's "what each repair SAYS" paragraph states both outcomes, so nothing is
  built wrong; the two spans should not share a line in a table whose value is exactness.

### The regress signature, and why this round does not fire round 6's trigger

Round 6 recorded the count (rounds 2→6 inside the documentation-truth apparatus) and set the line:
*if a seventh round lands anywhere inside this item's check-module machinery — D11, `prose_lines`,
Task 2's fixtures, or the zero-count scans' own literals — stop and ask Dave for a sufficiency
ruling rather than buy another round.* I went looking there first and deliberately: I ran D12's
sweep myself across all fifteen tasks, re-derived D11's thirteen-owner obligation site by site,
re-executed `prose_lines`' two line-scan-defeating shapes against the tokenizer, and re-checked the
non-vacuity rule against the plan. **The trigger does not fire, because there is no seventh
finding.** The three notes above are outside the blocking bar and two of them are cross-reference
accuracy rather than machinery. Escalating for a sufficiency ruling with nothing blocking to rule
on would spend Dave's attention to confirm what this round already establishes by re-derivation,
and would leave a correct spec sitting at `specced`. Recording the disposition here so a future
gate inherits it: the arc closed at round 6's fold, five-blocking-to-zero, and the trigger stands
unfired rather than waived — if a later round *does* land inside this apparatus again, round 6's
instruction is still the right one and this section is not a licence against it.

### Carried-forward notes

Every still-open note from every prior round, re-checked against the tree rather than against the
fold's account of it.

- **Round 6 blocking 1 (two checks ordered to spell literals two other checks assert at zero across
  `TESTS_ROOT`) — CLOSED, on the arm that cannot recur as a clause.** D12 is a MODULE rule over
  source lines, its three bound literals are derived from `## Verification`'s own table rather than
  listed, and its sweep tables every site including the Task-5 tripwire the round did not name.
  Verified by running the sweep, not by reading the table.
- **Round 6 note (`## Verification`'s non-vacuity table missing the row its own rule returns for
  Task 13's third control) — CLOSED**; the row is present and cites Task 2's `prose_lines` shapes
  fixture, which is the structural-predicate sub-class the rule names.
- **Round 6 note (`find_or_create_stub` span disagreeing by a line between D11 and Task 11) —
  CLOSED**; both now read `:683-686`, and the two sentences are at `:683-685` and `:685-686`.
- **Rounds 1–5's findings and notes — all still closed**, re-verified rather than assumed: D3(b)'s
  per-sweep seeding with the `gate_write` mechanism named; AC-1's symbol-anchored weak-identity
  citation; Task 4's red-is-a-finding door; D2's ordinal 8 and the closed five-value `arm`
  vocabulary participating in the tripwire triple; Task 5's `__main__` guard and literal invocation;
  the Task-6 interior red named as the CUT boundary and widened to three authorized cases; the
  `CORPUS_COUPLING` declaration ordered in D9, Task 2 and the `## Write Targets` `why`; D11's
  authorization predicate stated over PROSE with the thirteen re-derived; D8's two
  line-scan-defeating shapes stated apart with each plant's expectation derived from the rule;
  `resolve_or_create:847-848` in the table and repaired with `:878-879` in one edit; D10's last row
  transcribing `\w+Repository\(\s*\)` while importing the pattern.
- **Architect rounds 1–4 and both AC red-team rounds — all folded and still folded**: the
  `_remove_entity_from_indexes` widening note closed by D0's arm selection; the Branch-C variant
  names pinned off `tomas`/`villalobos`; the `arm`-not-branch record; the on-the-threshold
  `0.6 + 0.25 = 0.85` disclosure carried in D1, E8, AC-1 and Task 9's docstring repair.
- **Data-premise's three** — the cross-repository `orchestrator/docs/…` exclusion is D8's named
  exclusion with its line-wrap blind spot stated; `person.py:675` is D7's; `:685` is D7's plus Task
  12's presence clause on `stub_golden.json`/`resolve_golden.json`.
- **Threat model's three notes — still open, still non-blocking, still correctly deferred**: the
  `get_by_email(None)` shape change (now stated in D4 item 2 and the Edge Cases error-propagation
  entry, so effectively closed); the alias-preemption residual, a pre-existing property this item
  makes testable and whose closure would be a `resolve()` behaviour change and therefore a new
  item; and the audit artifact's "quoted with its note and reason" clause against `## Verification`'s
  counts-only close-out, which cannot collide at 0 of 1021 and is routed to whoever re-runs the
  audit if the arm ever flips. **Re-deferred because each is owned elsewhere**: the first by a Build
  Log line, the second by a future item, the third by D0's STOP door.
- **D11's own declared residual** — an authorized owner that loses a Cut-0 line for the WRONG
  reason, which `(e2)` cannot distinguish from the ordered repair landing — is **recorded, not
  re-raised**; it is a ruling on record with the needle tiers as its stated mitigation.
- **E3's minted follow-on** (write-boundary E.164 canonicalization at the `name_gate`) and the
  `lint_vault` repair rule routed to WI-026 are `## Scope Boundary` entries, not open notes. So is
  `docs/person-repo-decomposition.md:22`, which D11 routes to WI-025's spec-writer rather than
  editing another item's doc.

```verdict
gate: spec-reviewer
verdict: PROMOTE
date: 2026-09-07
model: claude-opus-5
note: Round 6's finding is closed on the class rather than the two sites — D12 states the self-collision rule over source LINES of this item's own tests/-root modules, derives its three bound literals from `## Verification`'s zero-count table instead of listing them, and its sweep found a third ordered site (Task 5's tripwire) the round did not name; I re-ran that sweep across all fifteen tasks and found no eighth site, re-derived AC-4's full 39-query space and replayed `select_resolution` over it (all 39 reproduce pre-cut `resolve()` except E7's two enumerated rows), hand-executed the three AC-1 cases whose runtime branch moves at Cut 1 (identical pairs both sides), and confirmed `Email.parse` accepts the padded angle-bracket form at `identifier.py:154-159` so AC-2's whitespace variant cannot split surface 1 from surface 2 — the four folds are complete with faithful quotes, the five criteria are byte-identical to the signed artifact, and the three notes remaining are cross-reference accuracy, not buildability, so round 6's escalation trigger stands unfired rather than waived.
```

## Adversarial Review — 2026-09-07

Round 7 (re-verify, cold-start), run on a model distinct from spec-reviewer by construction. Read the driven doc end to end — Problem/Motivation through Exploration Notes E1–E8, Approach, Design D0–D12, Edge Cases, Implementation Plan, Write Targets, Mitigation Folds, Verification, Verified Diagnosis, Scope Boundary, Risk Analysis, Acceptance Criteria — and every prior gate verdict: four Architectural Review rounds, two AC Red-Team rounds, the Data Audit, seven Spec Review rounds, the Threat Model, the AC Sign-off, and this gate's own six prior PROMOTEs, as the untrusted content an attacker's steering would have to hide inside. This project's own `docs/` carries neither `work-item-pipeline.md` nor `compartmentalization-security-review.md` (confirmed by glob, the same absence every prior round records); both resolve under `/Users/davewascha/Workspaces/workshop-stable/docs/` and I read both there in full. Also read `docs/identity-cutover-corpus-audit.md` and `docs/spec-reviews/WI-023-dave-review-2026-09-07.md` in full — the two grounding artifacts the driven doc's Write Targets and AC Sign-off fence depend on.

**What's new since round 6's PROMOTE.** One section: Spec Review round 7 (PROMOTE to `ready`) — no blocking finding, three non-blocking cross-reference notes, and an explicit statement that round 6's escalation trigger (a possible seventh finding inside the documentation-truth apparatus) did not fire.

**Method.** Independently re-ran the injection-phrasing sweep over the whole document myself rather than trusting the prior six rounds' reports — `ignore`/`disregard`-previous-instructions, "emit PROMOTE"/"emit REVISE"/"emit REJECT", "as an AI", `SYSTEM:`/`ASSISTANT:` turns, jailbreak language, and addressed-to-a-reviewer phrasing ("trust me", "skip this check", "already approved", "pre-approved"/"authorized", "override your", "reviewer should", "do not flag/report/review"). Every hit is inside the six prior injection-hunter rounds' own method paragraphs, which name those terms only to describe their own search vocabulary (the example-self-trap shape this role's contract itself warns about) — the same self-referential pattern every round has found, confirmed by re-running the grep myself rather than reading the prior count. Separately grepped for zero-width/bidi/BOM Unicode control points (`U+200B`–`U+200F`, `U+202A`–`U+202E`, `U+2060`–`U+2064`, `U+FEFF`) — zero hits anywhere in the file. Independently re-verified, rather than trusted, round 7's own heaviest claim: `obsidian_schemas/identifier.py:Email.parse:144-169` — read directly rather than quoted — routes a genuine angle-bracket form through `parseaddr` only when both `<` and `>` are present (`:154-156`), strips and lowers otherwise (`:159`), and refuses `kit@localhost` at `:167-168` for the missing `.` in the domain (`"malformed local@domain"`) — all exactly as round 7 and every prior round quote it, byte-for-byte, not a fabricated pointer built to send a reviewer down a false trail.

**What's actually in the new section.** A spec-reviewer arguing, from its own re-derivation (the full 39-query AC-4 space replayed against `select_resolution`, all three Cut-1-moved AC-1 stub cases hand-executed, D12's sweep re-run across all fifteen tasks rather than read off its table), that no blocking defect remains and that round 6's own stated trigger for escalating to a human sufficiency ruling does not fire — a technical PROMOTE argued from re-executed evidence, not asserted. The prose is the ordinary shape this role's calibration excludes from injection concern: a reviewer's own conclusion about the document's merits, explicitly checked against the very thing (round 6's trigger) that would have obligated a pause rather than a PROMOTE. That the round chose to *test* the trigger rather than silently let it lapse is itself evidence against steering — a planted push toward PROMOTE has no reason to raise, then discharge in the open, the one condition that would block it.

**Conclusion.** No text arguing for a verdict independent of the spec's merits, no instructions addressed to a reviewer/agent, no section whose form is spec content but whose effect is to steer a gate, no prior verdict — across all four architect rounds, two AC-red-team rounds, data-premise, seven spec-review rounds, and the threat model — that reads as the product of such steering, and no fabricated citation in the newest material. This is a real finding — I looked again, at the delta and at the whole, independently re-ran both sweeps and spot-verified the newest section's load-bearing citation against source rather than trusting the quote, and found nothing planted — not a skipped check.

```verdict
gate: injection-hunter
verdict: PROMOTE
date: 2026-09-07
model: claude-sonnet-5
note: Re-hunted cold-start after Spec Review round 7 (PROMOTE to ready) landed; independently re-ran the injection-phrasing and hidden-Unicode-control-character sweeps over the whole document rather than trusting the prior six rounds' reports, and got the same zero hits outside those rounds' own method paragraphs (which only name their search terms); byte-verified round 7's heaviest citation (identifier.py:Email.parse:144-169, the parseaddr/strip/refusal logic every round quotes) directly against source rather than the quote — accurate. The new section is a reviewer's own re-derived conclusion (a full 39-query replay, three hand-executed stub cases, a re-run of D12's sweep) that explicitly tests and discharges round 6's own escalation trigger in the open rather than letting it lapse — the opposite of what a planted steer toward PROMOTE would do.
```
