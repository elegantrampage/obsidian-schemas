---
id: WI-022
title: "Company stub parity: retire the deleted name-mangler, add validation + provenance"
project: obsidian-schemas
stage: exploring
created: 2026-07-05
last_touched: 2026-09-06
stage_changed: 2026-09-06
touched_by: session
tags: [company-repository, data-quality, small-mechanical]
depends_on: []
transitions: ["idea>exploring@2026-09-06@session"]
---

# Company stub parity

> **Model routing** (2026-07-05 campaign, `docs/backlog-campaign-2026-07-05.md`; self-sufficient):
> - **Explore: —. Spec: Sonnet / low** (template: the Person-side WI-105/WI-111/WI-119 pattern, applied to Company). **Spec-review: Opus / medium. Build: Sonnet / medium** + Opus code-review (standing rule). Leaf build with executable ACs.
> - Sequencing: Phase 2; independent of WI-004/WI-021 — schedule opportunistically.

## Problem / Motivation

*(Rewritten at ideation, 2026-09-06. The mint's line references were written on 2026-07-05 and two of them
have since moved; the re-measured versions are below. The defect itself is unchanged and live.)*

`CompanyRepository.create_stub` still runs `clean_name = re.sub(r'[^\w\s-]', '', name).strip()` —
**`obsidian_schemas/repositories/company.py:171`**, and it is the **last live instance of the mangler
regex WI-111 deleted from the Person side**. Consequences on real inputs: `"O'Reilly Media"` →
`"OReilly Media"`, `"AT&T"` → `"ATT"`, `"Yahoo!"` → `"Yahoo"`, `"Booking.com"` → `"Bookingcom"` —
persisted as the canonical `name:` **and** as the filename, since `BaseRepository.save` binds
`@{entity.name}.md` from the raw name (`obsidian_schemas/repositories/base.py:382`).

The Company path applies **no name contract at all**, and the shape of that hole has changed since the
mint: it is no longer "bypasses NameValidator", it is "reaches the semantic gate and the gate hands it
straight back". Company writes *do* route through WI-021's `gate_write` (via
`writer.write_markdown_file:252`, with `declared_type="company"` because `Company.type` is
`Literal["company"]`, `models.py:127`) — and `name_gate.py:311-312` is an explicit
`declared_type is not None and declared_type != PERSON_TYPE → return dict(introduced)` pass-through.
The gate is built and wired; companies are simply not in it. And `create_stub` writes no `created_by`
(WI-119 covered Person only): the string `created_by` does not appear in `company.py` at all.

**Two second-order consequences the mint did not name, both inside this tree:**

1. A mangled company note degrades **person** name-cleaning. `PersonRepository._known_companies`
   (`person.py:1111-1147`) unions `CompanyRepository` names into the set `clean_person_name` uses for
   corroborated company-suffix stripping. Stored as `ATT`, the note no longer corroborates the suffix
   in a person name written `"Someone AT&T"` — the corroboration silently misses and the person name
   keeps the suffix.
2. `scripts/lint_vault.py`'s `person_company_not_found` check compares `person.company` to `@{name}.md`
   stems (`lint_vault.py:458-467`). A person whose `company: AT&T` points at a note stored as
   `@ATT.md` produces a spurious WARNING on every lint run, for every such person.

2026-07-05 review finding N1; corruption of company names on write, one call site, well-tested
neighbouring pattern to follow.

## Intent

Company stubs get the same boundary discipline persons got: no lossy character-class stripping, a validating cleaning step, `created_by` provenance, and invariant tests on the punctuation cases the mangler destroyed.

## Exploration Notes

Explored 2026-09-06, cold-start, approval-only (no `involvement:` flag — the approach below is
re-derived from the frozen `## Intent`, and the mint's named mechanism, "add NameValidator to
`create_stub`", is treated as a hypothesis and is **rejected** in D1 below).

### Data premises, measured (predicate + currency stated so each is re-runnable)

Currency for all five: **the tree as this drive seeded it** — git HEAD `2bf731f` plus the seeded
uncommitted delta, `/…/cage-wt-h1vq08yw/tree`. Reader tools: Read/Grep/Glob, no shell.

| # | Predicate | Result |
|---|---|---|
| P1 | `rg '\[^\\w\\s-\]'` over the whole tree | 5 hits, **exactly one live code site**: `obsidian_schemas/repositories/company.py:171`. The others are a comment recording the person-side deletion (`person.py:1339`) and three doc mentions (`docs/create-stub-rfc2822-parse.md:35,50`, this doc). `BookRepository.create_stub` does a bare `.strip()` (`book.py:298`) — Company is the only survivor. |
| P2 | `rg 'created_by'` scoped to `obsidian_schemas/repositories/company.py` | **0 hits.** Person writes it unconditionally at `person.py:1387-1393`, with falsy/non-`str` → `"unknown"` + WARNING. **But the guard is `if not created_by or not isinstance(created_by, str):` and that is narrower than its own comment claims** ("an empty label is an unlabeled writer", `:1385-1386`): for `created_by="   "` neither conjunct fires — a non-empty string is truthy, and it is a `str` — so Person stores three spaces verbatim. Hand-executed against the line, not inferred from the comment. This is the one place the document's mirror-Person premise breaks; D6 records it and AC-3 states the Company-side widening explicitly. |
| P3 | Company-write path through the gate | `CompanyRepository.create_stub:192` → `BaseRepository.save:388` → `writer.write_markdown_file` → `gate_write(fm, declared_type=fm.get("type"), …)` at `writer.py:252`. `fm["type"]` is the string `"company"`, so `name_gate.py:311-312` returns the payload **untouched**. The gate is reached and declines to judge. |
| P4 | `CompanyRepository.create_stub` test coverage | **One test**, `tests/test_repositories.py:1852-1861`, name `"New Startup"` — no punctuation, no provenance, no collision, no refusal. There is no `tests/*company*` file. |
| P5 | Does a branch added inside `gate_write` disturb WI-021's derived AST wall? | **No.** `tests/derivations.py:977-1008` derives an ARM from `Assign` nodes feeding a `write_frontmatter` call; a new `declared_type == "company"` branch inside `gate_write` creates no such assign, so `frontmatter_write_arms` still resolves eight arms over six functions and the wall stays green **without editing it**. |

**Not settled here, and deliberately so.** Every claim about *how many live company notes* carry a
mangled name, about *which* proposed Tier-1 branch would refuse a name that is actually on disk, and
about which consumers call `CompanyRepository.create_stub`, is out-of-repo (the live vault; HAL9000 /
Exocortex / orchestrator). Those are not routed away as unreachable-because-forbidden — the gate spawn
arms no read sandbox and I could open the vault — but an answer read there pins to no HEAD and is not
re-runnable by the next reader. They are the grounding artifact declared under `## Write Targets`,
and AC-5 pins its shape. This is the WI-147 correction taken *before* the signature rather than after.

### Constraints discovered

- **The name is an IDENTITY, not a transform — and this is the constraint that shapes the whole
  design.** `base.py:382` binds `@{entity.name}.md` from the raw name one frame *above* every gate
  call and never revisits it. A gate that *returned a repaired* company name would write `name: A B`
  into `@A  B.md`, and the next `save()` would mint a second note for one company — the exact live
  corruption class WI-029 exists to repair on the person side. So: the gate is a **predicate** for
  companies exactly as it is for persons (`name_gate.py:38-46`), and any Tier-2 repair stays in
  `create_stub`, above the filename derivation.
- **Company Tier-1 cannot be Person Tier-1.** `TIER1_BRANCHES` was derived from a 2026-06-02 audit of
  **1647 person notes** (`name_validation.py:26-28`). Nothing equivalent exists for companies, and at
  least one branch is actively hostile to them — see D2.
- **Deleting the mangler *un-shields* characters nobody has thought about.** `[^\w\s-]` strips
  everything outside word-chars/space/hyphen, so today it silently absorbs `: * ? " < > | \ [ ] # ^`
  as well as the apostrophes and ampersands we want back. Obsidian bars those from filenames and
  wikilink targets. Person's `_PATH_HOSTILE_RE` is `/` **only** (`name_validation.py:95`) — an
  under-reach the person side survives because human names rarely carry them, and companies do
  (`"Yahoo! Inc."`, `"Company #1"`, `"Smith & Co. [UK]"`). The company table must be **wider** on
  path-hostility than the person table, not a subset of it.
- **Write authority.** `pipeline-runners.yaml:34-38` grants `obsidian_schemas/**`, `tests/**`,
  `scripts/**`, `docs/**`. Everything this item writes is inside it; the audit artifact is declared a
  `precondition` for the WI-024 reason (evidence the caged builder cannot see), not for a path reason.
- **Effort budget.** Leaf, one session. `Tier1Branch`, the chain walker, `NameGateRefusal` and the
  derived arm sweep all already exist; this adds a table, a branch, and tests.
- **Dependencies.** None. WI-004 and WI-021 have both shipped, which is what made the re-derivation
  below possible at all. Nothing depends on this item; WI-029 is adjacent (see D4).

### Approaches considered and rejected

**D1 — Put `NameValidator` in `CompanyRepository.create_stub` (the mint's named mechanism). REJECTED.**
This is precisely the pre-WI-021 defect on the person side, restated for companies. `name_gate.py:6-8`
records it in the past tense: *"`NameValidator` fired at exactly one site in the package —
`create_stub` — so a direct `repo.save(...)`, an `update_fields(person, {"name": ...})` or a bare
`write_markdown_file(...)` wrote an arbitrary or path-hostile name with no validation at all."* Build
D1 and `CompanyRepository.save(Company(name="Acme/Corp"))` still puts a `@Acme/` directory in the
vault. The mint predates the gate; asking where the contract *lives* is what moves it.

**D2 — Reuse `TIER1_BRANCHES` unchanged for companies. REJECTED, and `rfc2822_leak` is why.** That
branch's regex is `\b[a-z][a-z0-9._\-]{4,}(com|net|org|io|ai|uk|co|gov|edu|app|biz)\b`. Company names
*are* domains and are often styled lowercase. Hand-tracing: `"Booking.com"` survives (the `\b[a-z]`
anchor cannot start mid-word at `ooking`, and the run after the `.` is too short), but
`"wetransfer.com"` **matches and would be refused** — a real company, unwritable. Four more branches
are transcript artifacts of the *person* ingest path with no company producer, named here by
`branch_id`: `calendar_prefix`, `me_to_prefix`, `unknown_contact`, `pure_digit`. (That last one is
`branch_id="pure_digit"` carrying `pattern="pure_digit_name"`, `name_validation.py:263-274` — the two
keys diverge, and the branch is excluded because a numeric brand or ticker-styled company name is a
real thing a person name is not.) A blind copy refuses real companies and carries four dead branches;
naming the exclusions **by `branch_id`** is what makes the table company-appropriate.

**D3 — Keep a mangler, just a narrower one (strip only path-hostile chars). REJECTED.** This is the
WI-111 ruling re-applied: a stripper manufactures Tier-1 failures out of validator-passing inputs and
silently changes what the producer meant. Worse here than on the person side, because it re-opens the
filename/name divergence class: `"Yahoo! Inc."` stripped to `"Yahoo Inc."` *is* a divergence between
what the producer holds and what the vault stores, and there is no signal that it happened. Reject at
the boundary and make the producer fix it.

**D4 — Repair the company notes already mangled on disk. OUT OF SCOPE, named so it is not lost.** The
frozen Intent is about the write path. Repairing stored names is a rename through `vault_io.move_note`
with the old stem preserved as an alias — the same machinery WI-029 is minted to run for the three
forked *person* notes. It belongs there or in a sibling, and the audit artifact this item requires
will size it. Cost of deferring: `_known_companies` corroboration and `person_company_not_found` stay
degraded for the existing population until it runs.

**D5 — Give Company `create_stub` Person's reuse-on-collision door (WI-126 door C). PARKED.**
Discovered while reading, and it is a real asymmetry: on a name collision Person *reuses* the existing
note (`person.py:1359-1367`) while Company calls `save()` straight through, which raises
`BodyTruncationError` if the note is loaded and has a body, or `NoteAlreadyExists` if it is not. That
is **loud, not silent data loss**, and it is not in the frozen Intent. Parked deliberately rather than
folded in — widening a frozen intent mid-flight is how the AC set stops matching what Dave signed.

**D6 — Close Person's whitespace-only `created_by` hole as well. PARKED; Company closes it on its own
side regardless.** Found while grounding AC-3 against source rather than against P2's summary of it.
`person.py:1387` is `if not created_by or not isinstance(created_by, str):`, and for `created_by="   "`
both conjuncts are `False` — a non-empty string is truthy, and it is a `str` — so the branch never fires
and Person writes `created_by: "   "`, a label that looks like a value in the frontmatter and names
nobody. Person's `"unknown"` + WARNING sentinel exists precisely to make an unlabelled writer findable,
and whitespace is the shape that defeats it most quietly. Two consequences for this item, both taken:
Company's guard is Person's two-part check **plus** a third disjunct (emptiness after `.strip()`), making
it a deliberate, stated SUPERSET of Person's rather than a transcription — AC-3 says so in its own text,
so the divergence is licensed at sign-off instead of discovered in code review; and the phrase "on
Person's exact terms" is struck from `## Approach`, because on this one input it is false. The
Person-side repair itself is one conjunct and one test, but `PersonRepository.create_stub` is not in the
frozen Intent and touching it widens the item — parked exactly like D5, cheap to mint as a sibling. Cost
of deferring: person stubs written with a whitespace-only label keep an unfindable writer.

### Convergence

Approach B (the gate) over the mint's Approach D1 (`create_stub`), with the contract **split exactly
the way the person side is split** — Tier-1 reject in the gate as a predicate, Tier-2 repair in
`create_stub` above the filename derivation. This is not a design decision so much as reading back
what WI-021 already established and noticing that the company branch of it was left as a
pass-through.

## Approach

Give `gate_write`'s non-person branch a real judgement for `declared_type == "company"` instead of the
blanket pass-through at `name_gate.py:311-312`, backed by a **`COMPANY_TIER1_BRANCHES` table in
`name_validation.py` with its own membership** — reusing the existing `Tier1Branch` record and the
same walk, but carrying only the branches that make sense for a company name. **Membership is stated
by `branch_id` throughout this item, never by `pattern`** — the two keys diverge and `pattern` is not
unique (`name_validation.py:142-144` says so outright). Included, by `branch_id`: `empty`,
`archive_prefix`, `arrow_connective`, `email_chars`, and a **widened** `path_hostile` covering the
filename- and wikilink-hostile characters the mangler has been silently absorbing. Excluded, by
`branch_id`: `rfc2822_leak`, `calendar_prefix`, `me_to_prefix`, `unknown_contact`, `pure_digit` — for
the reasons D2 records. Note the two places where a `pattern`-keyed reading of that split would give a
*different and wrong* table: `arrow_connective` is INCLUDED even though it shares
`pattern="calendar_prefix"` with two excluded branches, and the excluded pure-digit branch is
`branch_id="pure_digit"` even though it raises `pattern="pure_digit_name"`. Every record carries a
*negative* specimen so the table proves it does not fire on real company names.
On `name` the company arm is a **predicate**: it raises `NameGateRefusal` with the branch's stable
`pattern`, or hands the name back byte-for-byte — never a repaired string, because the filename is
bound from the raw name one frame above. `CompanyRepository.create_stub` then loses the mangler
(`company.py:171`), gains the Tier-2 repair in its place (strip + collapse, above the filename
derivation, mirroring `person.py:1327-1345`), and gains `created_by` provenance in `extra_fields` on
Person's terms plus **one deliberate, named widening**: always written; falsy or non-`str` → `"unknown"`
plus a WARNING, exactly as `person.py:1387-1393`; and whitespace-only → `"unknown"` too, which Person's
own guard does **not** do (`not "   "` is `False` and `isinstance("   ", str)` is `True`, so its branch
never fires and it stores the spaces verbatim — hand-executed, D6). Company's guard is therefore Person's
two-part check with a third disjunct, `or not created_by.strip()`, and is not a byte-for-byte
transcription of it; a non-empty label is still stored byte-identically, never trimmed, so the `.strip()`
is a test and not a transform. The final
membership of the table — specifically whether `email_chars` and the widened path-hostile set refuse
anything that is legitimately on disk today — is settled by a conductor-run corpus audit committed
before the criteria are frozen, not by reasoning about company names from memory.

## Write Targets

```writes
kind: precondition
path: docs/company-name-corpus-audit.md
grounds: AC-2's COMPANY_TIER1_BRANCHES membership and the AC-1/AC-4 claim that no name on disk today becomes unwritable
why: Both premises rest on the live vault's company-name corpus and on which consumers call CompanyRepository.create_stub, neither of which is in this repo. The audit records, per proposed branch, how many live `type: company` names it would refuse (listing each), the count of already-mangled stems (sizing D4), and the create_stub call sites in HAL9000 / Exocortex / orchestrator with the scan command, its verbatim stdout, and each repo's 40-char HEAD SHA. (Conductor 2026-09-06: `grounds:` shortened to the linter's 120-char cap per workshop WI-327's idiom; the detail moved here, nothing dropped.) The caged builder can reach neither the vault nor the three consumer repos, so a builder-authored version of this file would be fabrication (the WI-024 precedent, docs/default-vault-path.md:623-627). It is declared HERE, at exploring, rather than at ready because it settles a premise the acceptance criteria are ABOUT: if the audit shows `email_chars` or the widened path-hostile set refusing a real company name, that is one line edited in a draft AC — after origination it is a D4b re-sign and a second interruption of Dave (the WI-281 shape). `docs/**` is inside this project's write_authority (pipeline-runners.yaml:34-38), so the fence kind here is about EVIDENCE, not about path permission.
```

## Acceptance Criteria

Draft — originated cold-start, approval-only mode, re-derived from the frozen `## Intent`. **Not yet
frozen:** the `ac-signoff` fence is written by `bin/review-spec-helper.py` only after Dave's review,
never by hand. Every `check` is a top-level zero-argument `def test_*(` that signals failure by
raising.

*Revised 2026-09-06 (r1), AC-2 only, answering the ac-red-team findings below.* Both landed on the
exclusion clause and both were confirmed against source before revising: `name_validation.py:264` is
`branch_id="pure_digit"` / `pattern="pure_digit_name"`, and `:194-228` gives `arrow_connective`,
`calendar_prefix` and `me_to_prefix` one shared `pattern="calendar_prefix"`. The clause now (a) names
`.branch_id` as the keying field explicitly and cites the two divergences, (b) uses the real id
`pure_digit`, (c) spells both sets literally instead of pointing at prose, and (d) adds a positive
guard asserting `arrow_connective` is a company-table member carrying `.pattern == "calendar_prefix"`,
so the `.pattern`-keyed reading is not merely unintended but contradicted by the AC's own text. The
same branch_id-granularity fix was pushed UPSTREAM into `## Approach` and D2, so the ambiguity is gone
at its source rather than patched only where the red-team found it. AC-1, AC-3, AC-4 and AC-5 were
unchanged at r1.

*Revised 2026-09-06 (r2), AC-3 only, answering the re-verify round's Finding 3.* The finding is
CONFIRMED by hand-executing the cited line rather than reading it: `person.py:1387` is
`if not created_by or not isinstance(created_by, str):`, and for `"   "` both conjuncts are `False`, so
Person stores three spaces verbatim — "on Person's exact terms" was false at exactly the input AC-3's
own fixture list requires. Taking the finding's remedy (b): `"   "` STAYS in the fixture list, and AC-3
now states outright that Company's guard is Person's two-part check PLUS a `.strip()`-emptiness disjunct
Person's code lacks, that the widening is deliberate, and that a verbatim transcription of
`person.py:1387-1393` is therefore RED on this AC by design. Remedy (a) — dropping `"   "` — was
rejected: a whitespace-only label is the shape that defeats the `"unknown"` + WARNING sentinel most
quietly (it looks like a value and names nobody), so the item would ship provenance with a hole in it to
preserve a parity that is itself the defect. The fix was pushed UPSTREAM the same way r1's was: `##
Approach` no longer says "Person's exact terms", P2 records the measured hole beside its citation, and
new **D6** parks the Person-side repair as out-of-Intent. AC-3 also gains an explicit byte-identical
clause for non-empty labels, so the `.strip()` cannot be read as licence to trim what is stored. AC-1,
AC-2, AC-4 and AC-5 are unchanged at r2.

```criteria
id: AC-1
desc: The character-class mangler is gone from the package — `re.sub(r'[^\w\s-]', '', …)` and any equivalent character-class strip appears at zero live code sites in obsidian_schemas/ and scripts/ (asserted as a pattern scan over the tracked source, not a check against company.py:171 by line) — and every name in a declared PRESERVATION table survives a company write BYTE-IDENTICAL on both legs: the stored `name:` read back off disk equals the input byte-for-byte, AND the note's filename stem equals `@{input}.md`. The table is a module-level object the build declares, and it contains at minimum one name per character class the mangler destroyed: apostrophe ("O'Reilly Media"), ampersand ("AT&T"), exclamation ("Yahoo!"), dot ("Booking.com"), comma+dot ("Alphabet, Inc."), plus a lowercase-styled brand ("wetransfer.com") and a Tier-2-dirty name ("Acme  Corp", double space) whose repaired form must appear in BOTH legs consistently — a build that repairs the name but not the filename is RED on the second leg. The sweep runs over the arm set `tests/derivations.py:frontmatter_write_arms` derives (never a hand-list), so a future arm joins it automatically.
why: This is the item, and the two legs are what make it unfakeable. A build that re-adds a narrower strip passes any refusal-only oracle while still corrupting "AT&T"; a build that instead reaches for `NameValidator.clean`'s RETURN value passes the stored-name leg and fails the filename leg, which is exactly the divergence WI-029 exists to repair on the person side (base.py:382 binds `@{entity.name}.md` from the raw name one frame above every gate call and never revisits it). "wetransfer.com" is planted deliberately: it is the discriminating member that separates this table from a blind copy of TIER1_BRANCHES, whose `rfc2822_leak` branch refuses it.
check: test_company_name_punctuation_survives_every_write_arm
kind: test
```

```criteria
id: AC-2
desc: A `COMPANY_TIER1_BRANCHES` table exists in name_validation.py, built from the same `Tier1Branch` record as the person table and walked by the same dispatcher, and the fixture space is DERIVED from it (the swept set of `.branch_id` values asserted EQUAL to the table's own membership, so a hand-listed sample is RED). EVERY set-membership assertion in this criterion is keyed on `.branch_id` and NEVER on `.pattern`; the two fields diverge and `.pattern` is not unique, per `name_validation.py:142-144`, `:194-228` (`arrow_connective`, `calendar_prefix` and `me_to_prefix` all carry `pattern="calendar_prefix"`) and `:263-274` (`branch_id="pure_digit"` carries `pattern="pure_digit_name"`). For EVERY member: (a) a company write introducing that record's `specimen` is refused with a `NameGateRefusal` — the WI-021 leaf, never the LoudFailError root — carrying that record's stable `pattern` on its `.pattern` attribute and no note content; and (b) — the correctness oracle, not merely membership — that record's declared NEGATIVE specimen, a real company name the branch must NOT fire on, is written successfully and byte-identically. The record type gains that negative-specimen field for this purpose. Three membership assertions, all by `.branch_id`: (i) EQUALITY — `{b.branch_id for b in COMPANY_TIER1_BRANCHES} == {"empty", "archive_prefix", "arrow_connective", "email_chars", "path_hostile"}`, the set `## Approach` states and the audit artifact confirms, which by itself turns any of the five excluded ids into RED; (ii) NON-CONVERGENCE in the other direction — each of `{"rfc2822_leak", "calendar_prefix", "me_to_prefix", "unknown_contact", "pure_digit"}` asserted still PRESENT in `{b.branch_id for b in TIER1_BRANCHES}`, so a build cannot go green by subtracting those branches from the person tuple in place; and (iii) the SHARED-PATTERN guard — `arrow_connective` asserted a member of the company table AND asserted to carry `.pattern == "calendar_prefix"`, so excluding the `calendar_prefix` and `me_to_prefix` BRANCHES is proven not to have removed it.
why: A derived sweep proves MEMBERSHIP, never correctness (WI-286): a branch implemented as `return True` refuses every specimen and passes leg (a) for all of them, which is why every member owes a negative specimen it must decline to fire on. The membership equality — in both directions — is the whole of "company-appropriate, not a blind copy": D2 measured that `rfc2822_leak` refuses "wetransfer.com", so a build that reuses the person table wholesale must be RED here rather than merely under-tested, and a build that omits the widened path-hostile set must be RED too, since that set is what the mangler has been silently absorbing. The keying field is named once and the ids are spelled literally because `branch_id` and `pattern` are different keys carrying overlapping tokens, and BOTH ways of confusing them fail silently. Keyed on `.branch_id`, the token `pure_digit_name` matches no record in either table, so an exclusion check written with it passes unconditionally — green whether or not the pure-digit branch was actually excluded, and if it was not, every all-digit company name (a numeric brand, a ticker-styled stub seeded from an employer field) is refused with no test noticing. Keyed on `.pattern`, excluding `calendar_prefix` is FALSE against the very table the Approach specifies, because the INCLUDED `arrow_connective` raises exactly that pattern — so a correct build goes RED and the only route to green is dropping the one connective branch that is genuinely company-appropriate, reopening the D2 gap. Assertion (iii) exists to make that second reading impossible to hold: it states the shared pattern as a POSITIVE required fact rather than leaving it as an absence a builder must infer.
check: test_company_tier1_table_is_swept_and_each_branch_has_an_oracle
kind: test
```

```criteria
id: AC-3
desc: `CompanyRepository.create_stub` ALWAYS writes a `created_by` frontmatter field. A non-empty `str` label is stored BYTE-IDENTICALLY — the value read back off disk equals the label passed, with no trimming, so `"  ingester  "` round-trips with its spaces intact. For each of the UNLABELLED shapes — `None`, `""`, `"   "`, `0`, `123` — the stored value is the literal `"unknown"` AND a WARNING naming the company is emitted. This guard is Person's (`person.py:1387-1393`) PLUS one disjunct Person's own code lacks, and the widening is DELIBERATE, not an oversight to be reconciled: `person.py:1387` is `if not created_by or not isinstance(created_by, str):`, and for `"   "` neither conjunct fires — a non-empty string is truthy, and it IS a `str` — so Person stores a whitespace-only label verbatim (hand-executed against the line; D6 parks the Person-side repair). Company's guard is that two-part check with a third disjunct, emptiness AFTER `.strip()`. Consequently a verbatim transcription of `person.py:1387-1393` is RED on the `"   "` fixture BY DESIGN, and this criterion does NOT ask for byte-for-byte parity with those lines — where this desc and that citation disagree, this desc governs. The `.strip()` is a TEST on the guard, never a transform on the stored value: the byte-identical clause above still holds for every non-empty label. `auto_created` keeps its current behaviour (written only when the flag is set) and is asserted to be a SEPARATE field, so provenance and the workflow flag cannot be collapsed into one. The signature gains `created_by: Optional[str] = None` as a keyword with a default, so every existing call site keeps compiling.
why: Provenance is half the frozen Intent, and "always written" is the part a build gets wrong by writing the field only when a label is supplied — which reads as green on any test that passes one. The `"unknown"` + WARNING sentinel is what makes an unlabelled writer findable later instead of invisible, and whitespace-only is the shape that defeats it most quietly: it looks like a value in the frontmatter and names nobody. Every one of the five shapes needs its own conjunct and none of the readings is sufficient alone — `if not created_by` alone lets `123` through, `isinstance` alone lets `""` through, and the two ANDed together, which is Person's ACTUAL line and what the earlier "on Person's exact terms" phrasing pointed a builder at, STILL let `"   "` through. That is why the third condition is spelled out here instead of delegated to a citation: the previous phrasing invited a faithful transcription that is RED on this AC's own fixture, and the two halves were only satisfiable by silently diverging from the cited parity. Naming the divergence converts it from a trap into a decision — Company gets the guard Person's comment already claims to have, and D6 carries the Person-side repair rather than this item widening into it. The byte-identical clause is what stops the fix over-reaching into a trimmer, which would corrupt a legitimate label the same way the mangler corrupts a name. Keeping `auto_created` separate is stated because the two fields look interchangeable and are not: one is written once at creation and never mutated, the other is a flag the enricher flips.
check: test_company_stub_records_created_by_provenance
kind: test
```

```criteria
id: AC-4
desc: The company name contract is homed in the GATE, not in `create_stub` — proven by three writes that never call `create_stub` at all, each refused identically with the same `pattern`: `CompanyRepository.save(Company(name=<dirty>))`; `write_markdown_file(path, extra_fields={"type": "company", "name": <dirty>})`, handing the writer a bare dict and no model; and `update_frontmatter_field(path, "name", <dirty>)` against an existing `type: company` note. On the two create-shaped arms the refusal lands BEFORE anything reaches disk: for a `/`-bearing name against a tmp vault, `<vault>/@<first-segment>` does not exist (which subsumes the lock home and any note inside it) and `<vault>/@<first-segment>.md` does not exist — artifacts named from values the test holds, never an ambient directory listing. THE DELTA RULE holds for companies exactly as for persons: a `type: company` note whose STORED name already matches a company Tier-1 branch stays writable for any write that does not RE-INTRODUCE the name (`update_fields` on `website`, `update_frontmatter_field` on `industry`, `roundtrip_file`), while a write setting `name` to that same stored value is refused.
why: This is the criterion that makes D1 — the mint's `create_stub`-only mechanism — unbuildable, and it is the specific hole `name_gate.py:6-8` records the person side having had. The no-stray-directory leg is a property of the FRAME rather than of the gate: `note_lock`'s outermost acquisition mkdirs a sentinel home defaulting to the note's own parent, so a company check placed at the convergence point instead of above the lock refuses only AFTER `<vault>/@Acme/` and a `.lock` are already on disk. The delta rule rides here because without it this item BRICKS every company note already stored with a dirty name — remedy-is-the-disease — and those notes are the exact population D4 defers repairing, so they must stay writable in the meantime.
check: test_company_name_contract_is_homed_in_the_gate_not_create_stub
kind: test
```

```criteria
id: AC-5
desc: `docs/company-name-corpus-audit.md` exists and carries: the literal scan command run against the live vault with its verbatim stdout and the count of `type: company` notes scanned; ONE ROW PER MEMBER of `COMPANY_TIER1_BRANCHES` giving the number of live company names that branch would refuse and listing each such name (an empty result recorded as an explicit "no matches" marker, never an absent field); the count of company notes whose stored `name:` shows mangler damage, sizing the D4 follow-on; and, for EACH of HAL9000, Exocortex and orchestrator, the `CompanyRepository.create_stub` call-site scan command, its verbatim stdout, and that repo's 40-char git HEAD SHA. The test asserts this SHAPE — failing on a missing branch row, a missing field, a SHA that is not 40 hex chars, or a branch present in the table with no row — and makes no subprocess, network or vault call.
why: The membership of the table is an EMPIRICAL premise about a corpus, and settling it by reasoning about what company names look like is the WI-144 shape — a confident reading that the corpus falsified after the signature rather than before it. The teeth are the precondition fence, not this test; this pins the artifact's shape so the audit cannot be discharged as one hand-waved prose sentence, and the per-branch row is what forces the answer to the only question that can make this item harmful: does a branch we are about to add refuse a company that is legitimately on disk today. The consumer rows are here because AC-3 changes a public signature and AC-2/AC-4 make a previously-permissive write path start refusing — a blast radius measured in three repos this suite is, by design, hermetic against.
check: test_company_name_corpus_audit_is_complete
kind: test
```

### Examples of done

**Given** an ingester hands `create_stub` the name `"O'Reilly Media"` — **when** the stub is written —
**then** the vault holds `@O'Reilly Media.md` with `name: O'Reilly Media`, byte-for-byte, and
`created_by:` naming whoever wrote it. **And when** the same ingester hands it `"AT&T"` or
`"Booking.com"`, **then** the answer is the same shape: nothing is stripped, and the person notes
carrying `company: AT&T` resolve to that note instead of pointing at a stem that does not exist.

**Given** a producer bypasses the repository entirely and calls
`write_markdown_file(path, extra_fields={"type": "company", "name": "Acme/Corp"})` — **when** the
write runs — **then** it refuses with a `NameGateRefusal` whose `pattern` is the path-hostile key, and
afterwards the vault contains no `@Acme` directory, no lock home inside one, no `Corp.md` and no
`@Acme.md`. Three different ways into the write door are three doors, and none of them is a way
through.

**Given** a company note already on disk stored with a dirty name from before this fix — **when**
someone updates that note's `website` or `industry`, or the linter round-trips it — **then** the write
still commits, because the write did not re-introduce the name. **And when** someone writes that same
dirty string back into `name:`, **then** that one is refused. The fix declines to create the problem;
it does not brick the notes that already have it.

## AC Red-Team — 2026-09-06

Read in the mandated order: `## Intent`, `### Examples of done`, `## Problem / Motivation` and
`## Exploration Notes`, then the draft `## Acceptance Criteria` last. Cross-read the actual code
the ACs would be checked against — `obsidian_schemas/repositories/company.py`,
`obsidian_schemas/name_gate.py`, `obsidian_schemas/name_validation.py`, and `obsidian_schemas/writer.py`'s
`update_frontmatter_field` — to confirm each criterion's premises hold against current source, not
just against the Approach's prose description of it.

AC-1, AC-3, AC-4 and AC-5 held up under attack: AC-1's byte-identical preservation-table oracle makes
an "equivalent mangler" ungameable in practice (a stray strip anywhere in the write path corrupts one
of the seven required specimens, so the pattern-scan clause isn't the only wall); AC-3's provenance
oracle correctly forces the "always written" reading rather than "written when a label is supplied";
AC-4's three-arm gate-homing test is grounded in real code — `writer.py:385-386` and `:443-444` confirm
`update_frontmatter_field`/`update_frontmatter_fields` derive `declared_type` from the EXISTING note's
own stored `frontmatter.get("type")`, so the third arm's premise (a bare `{"name": <dirty>}` payload
against an existing `type: company` note still reaches the gate as `declared_type="company"`) is real,
not assumed; and AC-5's shape-only assertions make no vault/subprocess/network call, matching the
hermetic claim.

AC-2 has two concrete defects, both inside the exclusion clause of its equality assertion.

**Finding 1 (CRITICAL) — AC-2's `pure_digit_name` exclusion is tautological; it can never fail.**

AC-2's desc requires: "the exclusions asserted too: `rfc2822_leak`, `calendar_prefix`, `me_to_prefix`,
`unknown_contact` and `pure_digit_name` are asserted ABSENT from the company table." The membership
equality this same sentence anchors to ("asserted BY EQUALITY against the set stated in `## Approach`")
is keyed on **branch_id** — the Approach's own inclusion list (`empty`, `archive_prefix`,
`arrow_connective`, `email_chars`, `path_hostile`) names branch_ids, and AC-2's derived-sweep clause
says so explicitly ("the swept set of **branch_ids** asserted EQUAL to the table's own membership").
But in `obsidian_schemas/name_validation.py:263-274`, the Tier-1 record for pure-digit names has
`branch_id="pure_digit"` and `pattern="pure_digit_name"` — the token in AC-2's exclusion list is the
record's **pattern**, not its branch_id. No entry in `TIER1_BRANCHES` (or any sane `COMPANY_TIER1_BRANCHES`)
has `branch_id == "pure_digit_name"`.

Failure scenario: a builder writes the exclusion check the way every other clause in this AC is keyed
— `assert "pure_digit_name" not in {b.branch_id for b in COMPANY_TIER1_BRANCHES}` — straight from the
AC's own wording. That assertion is true **unconditionally**, whether the `pure_digit` branch is
excluded from the company table (per the Approach's actual intent) or left in it (silently refusing
every company name that is all digits — a numeric brand/ticker-style name, or a stub seeded from a
phone-only contact's employer field). The AC set does not catch a build that forgets to exclude
`pure_digit` from `COMPANY_TIER1_BRANCHES`, which is exactly the tautological-AC class this gate hunts
for (WI-122): the check restates a string that can never be found, not a property of the table.

What would have to change: the exclusion token must be corrected to the real branch_id, `pure_digit`
(matching `name_validation.py:263`), or the check must be stated as "no company-table member's
`pattern` equals `pure_digit_name`" if pattern-level exclusion is what's actually intended — but see
Finding 2, which shows the pattern-level reading is NOT what's intended and conflicts with the
Approach's own design.

**Finding 2 (MATERIAL) — the `calendar_prefix` exclusion is ambiguous between branch_id and pattern,
and only one reading is buildable.** `name_validation.py:194-227` shows three branches —
`arrow_connective`, `calendar_prefix`, `me_to_prefix` — all raising the SAME `pattern` value,
`"calendar_prefix"` (the module's own docstring at `name_validation.py:120-122` names this
deliberate sharing). The `## Approach` INCLUDES `arrow_connective` in `COMPANY_TIER1_BRANCHES` while
EXCLUDING `calendar_prefix` and `me_to_prefix` — a design that is internally consistent only when
"exclude branch X" is read at branch_id granularity. AC-2's exclusion sentence uses the bare tokens
`calendar_prefix` and `me_to_prefix` with no field named, and those tokens are simultaneously valid
branch_ids AND (for `calendar_prefix`) the literal pattern value that the explicitly-INCLUDED
`arrow_connective` branch also carries.

Failure scenario: a builder who keys the exclusion assertion on `.pattern` (a plausible reading,
since `.pattern` is the field AC-2's own leg (a) already cares about — "carrying that record's stable
`pattern` on its `.pattern` attribute") writes `assert "calendar_prefix" not in {b.pattern for b in
COMPANY_TIER1_BRANCHES}`. That assertion is FALSE against the table the Approach itself specifies
(`arrow_connective` is a member and its `.pattern` is `"calendar_prefix"`), so a correct build of the
Approach fails this reading of the AC — while a build that drops `arrow_connective` to satisfy this
reading of the AC contradicts the Approach's explicit inclusion list and reopens the D2 gap
(`arrow_connective` is the branch that is company-appropriate; dropping it loses real refusal value
with no compensating branch). The two readings of one sentence produce two different required tables;
that is the mutually-unsatisfiable-ACs shape (WI-139) at the granularity of a single exclusion clause,
not the whole AC.

What would have to change: state the exclusion assertion explicitly as "no member's `branch_id` is one
of {`calendar_prefix`, `me_to_prefix`}" (branch_id-level, consistent with the equality assertion's own
stated granularity and with keeping `arrow_connective`), so a `.pattern`-keyed implementation is not a
reasonable reading of the same sentence.

Both findings land on the same clause and the same fix pattern (name the field the exclusion set is
keyed on, and use the record's actual branch_id rather than its pattern where the two diverge) — but
they are two independent ways a faithful-seeming build passes AC-2 while `COMPANY_TIER1_BRANCHES`
diverges from the Approach, so both are named rather than folded into one.

```verdict
gate: ac-red-team
verdict: REVISE
targets: AC-2
prior: none
basis: original
findings: 2/2
date: 2026-09-06
model: claude-sonnet-5
note: AC-2's exclusion clause is tautological for pure_digit_name (wrong field: pattern not branch_id) and ambiguous for calendar_prefix/arrow_connective's shared pattern key.
```

## AC Red-Team — 2026-09-06 (re-verify)

Re-spawned to verify the fold recorded in `## AC Red-Team — 2026-09-06` above. Read in the mandated
order: `## Intent`, `### Examples of done`, `## Problem / Motivation` and `## Exploration Notes`, then
the current (r1) `## Acceptance Criteria` last. Cross-read `obsidian_schemas/name_validation.py`,
`obsidian_schemas/name_gate.py`, `obsidian_schemas/repositories/company.py:153-194`, and
`obsidian_schemas/repositories/person.py:1383-1393` against the ACs' premises rather than trusting the
prior round's citations.

**Round-1 findings held — both close.** Finding 1 (tautological `pure_digit_name` exclusion): the r1
exclusion clause is now stated by `.branch_id` throughout, and equality assertion (i) —
`{b.branch_id for b in COMPANY_TIER1_BRANCHES} == {"empty", "archive_prefix", "arrow_connective",
"email_chars", "path_hostile"}` — forces `pure_digit`'s absence directly rather than through a
never-matching token; assertion (ii)'s presence check now names the real branch_id, confirmed at
`name_validation.py:263-274` (`branch_id="pure_digit"`, `pattern="pure_digit_name"`). Finding 2
(calendar_prefix/arrow_connective shared-pattern ambiguity): assertion (iii) now pins `arrow_connective`
as a required company-table member AND requires `.pattern == "calendar_prefix"` on it — confirmed at
`name_validation.py:194-205` — which makes the `.pattern`-keyed misreading fail this AC's own text
rather than merely being discouraged in prose elsewhere. Neither finding re-opened; nothing in the fold
introduced a new defect in AC-2 itself.

A fresh, independent pass over the rest of the set turned up one new finding, in AC-3 — a criterion the
r1 revision note states is "unchanged," so this is original material, not something the fold touched.

**Finding 3 (MATERIAL) — AC-3's "on Person's exact terms" citation misreads its own cited code for the
whitespace-only case, so a build that transcribes the cited guard verbatim fails AC-3's own fixture.**

`person.py:1387` is `if not created_by or not isinstance(created_by, str):`. For `created_by = "   "`
(three spaces): `not "   "` is `False` — a non-empty string is truthy in Python, and whitespace does not
make a string falsy — and `isinstance("   ", str)` is `True`, so `not isinstance(...)` is also `False`.
`False or False` is `False`: the branch is never entered, `created_by` stays `"   "`, and
`extra_fields["created_by"] = "   "` is written as-is. Person does **not** normalize a whitespace-only
label to `"unknown"` — confirmed by re-reading `person.py:1383-1393` at its current line numbers this
round, independent of the prior round's read.

AC-3 nonetheless lists `"   "` among the falsy/non-`str` shapes required to store as the literal
`"unknown"`, framed as "on Person's exact terms (person.py:1387-1393)". The AC's own `why` compounds the
error: it observes that "`if not created_by` alone lets `"   "` through" — true — but does not notice
that ANDing that test with `isinstance` (exactly what `person.py:1387` does, and exactly what "Person's
exact terms" cites) *still* lets `"   "` through, since neither conjunct fires on a non-empty, all-`str`
value. Catching it needs a third condition the cited line never has, e.g. `or not created_by.strip()`.

Failure scenario: a builder implements Company's `created_by` guard by transcribing `person.py:1387-1393`
verbatim — the literal instruction "on Person's exact terms" invites exactly this — producing
`if not created_by or not isinstance(created_by, str): created_by = "unknown"`. This is a faithful,
good-faith reading of the AC's own cited reference, and it is RED on AC-3's own `"   "` fixture, which
the `check:` must exercise per the desc. Conversely, a builder who adds the extra `.strip()`-emptiness
guard to pass that fixture has, at that exact input, DEPARTED from "Person's exact terms" — the two
halves of AC-3's desc (cite-Person-verbatim vs. require-whitespace-normalization) are only simultaneously
satisfiable by silently diverging from the cited parity, and the AC never flags or licenses that
divergence.

This is not the WI-139 mutually-unsatisfiable shape — nothing here is unbuildable — it is a
premise-about-code error, the same species as the pre-fold AC-2 findings: an instruction that reads as
more mechanical and more authoritative than it is, because the cited line numbers were not re-executed
against the actual truthiness of a whitespace-only string.

What would have to change: either (a) drop `"   "` from AC-3's fixture list and drop the implicit claim
that whitespace is already handled by "Person's exact terms," accepting that Company's guard is a
narrower match to Person than the desc currently states, or (b) keep `"   "` in the fixture list and
state explicitly that the Company guard is Person's two-part check PLUS a `.strip()`-emptiness condition
Person's own code lacks — in which case "on Person's exact terms" needs to stop implying byte-identical
transcription. Either fix is one clause; noting it here because `## Problem / Motivation` and the rest
of this document otherwise treat `person.py:1387-1393` as settled-correct behavior to mirror, and this
is the one place that reliance breaks.

```verdict
gate: ac-red-team
verdict: REVISE
targets: AC-3
prior: held
basis: original
findings: 1/1
date: 2026-09-06
model: claude-sonnet-5
note: Round-1's two AC-2 findings held closed after the fold; new MATERIAL finding on AC-3 (unchanged by the fold) — its "Person's exact terms" citation (person.py:1387) does not actually normalize a whitespace-only created_by to "unknown", so a verbatim transcription of the cited guard fails the AC's own "   " fixture.
```

## AC Red-Team — 2026-09-06 (re-verify 2)

Cold-start re-attack of the r2 document. Read in the mandated order: `## Intent`, `### Examples
of done`, `## Problem / Motivation` and `## Exploration Notes`, then the current (r2) `##
Acceptance Criteria` last. Cross-read against current source rather than trusting either prior
round's citations: `obsidian_schemas/repositories/company.py:153-194`,
`obsidian_schemas/name_validation.py` (whole file), `obsidian_schemas/name_gate.py` (whole file),
`obsidian_schemas/repositories/base.py:360-399`, `obsidian_schemas/writer.py:160-260,333-460`,
`obsidian_schemas/vault_io.py`'s `note_lock` (~L364-420), `tests/derivations.py`'s
`frontmatter_write_arms`, `tests/test_name_gate_wall.py`'s `FLOOR`/`EDITED_FUNCTION_ARM_COUNTS`,
and `scripts/lint_vault.py:apply_fixes`.

**Round-1 and round-2 findings held.** Hand-executed again, independent of both prior rounds'
citations: `name_validation.py:263-274` still gives `branch_id="pure_digit"` /
`pattern="pure_digit_name"`, and `arrow_connective`/`calendar_prefix`/`me_to_prefix`
(`:194-227`) still share `pattern="calendar_prefix"` — AC-2's r1 branch_id-keyed equality and its
assertion (iii) (`arrow_connective` required present AND `.pattern == "calendar_prefix"`) still
close both. `person.py:1387` is still exactly `if not created_by or not isinstance(created_by,
str):`, still lets `"   "` through unnormalized — AC-3's r2 text still states the divergence
explicitly rather than implying byte-identical transcription. Nothing in the document's r1/r2
text has drifted from source since the last round.

A fresh, independent pass over AC-1 and AC-4 turned up one line of inquiry worth recording even
though it does not clear the materiality bar, per this gate's "too strict" calibration warning
against re-designing an AC that merely could be sharper.

**Considered and cleared — AC-1's sweep over `frontmatter_write_arms` includes arms whose gate
call cannot exercise `COMPANY_TIER1_BRANCHES` at all.** `frontmatter_write_arms` currently derives
eight arms over six functions (`tests/test_name_gate_wall.py`'s `FLOOR` /
`EDITED_FUNCTION_ARM_COUNTS`): three in `write_markdown_file` (create-shaped), one each in
`BaseRepository.update_fields`, `update_frontmatter_field`, `update_frontmatter_fields`
(update-shaped, gated IN-LOCK against the note's OWN stored `type:`), one in `roundtrip_file`, and
one in `lint_vault.apply_fixes`. `roundtrip_file` (D7) calls `gate_write({}, declared_type=None,
whole_record=False)` UNCONDITIONALLY (`writer.py:494`) — an empty delta, on every invocation,
regardless of what `COMPANY_TIER1_BRANCHES` contains — so no per-arm byte-identical assertion
built on that arm's public call can ever distinguish a correct company table from a broken or
absent one. I checked whether this makes the sweep gameable — a build that ships an empty or
wrong `COMPANY_TIER1_BRANCHES` going green on AC-1's D7 leg — and concluded it does not rise to a
red-team finding: AC-1 independently requires (a) the pattern-scan clause over the whole tracked
source (`obsidian_schemas/` and `scripts/`, not a `company.py:171` line pin) and (b) byte-identical
preservation specifically on the three create-shaped arms, where the mangler actually lived and
where `COMPANY_TIER1_BRANCHES` is actually consulted on the write path. A build cannot satisfy
those two clauses without doing the real work, so the D7/D8/update-arm legs of the sweep are
redundant-but-harmless (they test YAML re-serialization fidelity on an already-named note, a real
if narrower property) rather than load-bearing, and their inclusion creates no path to a false
green on the property AC-1 exists to pin. Naming this so the next reader can tell it was checked
rather than missed.

AC-2, AC-3, AC-4 and AC-5 re-verified against current source: AC-2's three membership assertions,
AC-3's five-shape provenance oracle and byte-identical clause, AC-4's three-arm gate-homing test
(the `update_frontmatter_field`/`update_frontmatter_fields` `declared_type` derivation from the
note's own stored `type:` re-confirmed at `writer.py:385-386,443-444`; the pre-lock gate hoist and
its reason re-confirmed at `writer.py:207-253` against `vault_io.py`'s sentinel-`mkdir` at
`note_lock`'s outermost acquisition, `~L394-400`) and the delta-rule's stored-dirty-stays-writable
clause, and AC-5's shape-only, no-vault-call assertion — all hold against current source with
nothing new found.

```verdict
gate: ac-red-team
verdict: PROMOTE
date: 2026-09-06
model: claude-sonnet-5
note: Fresh cold-start re-attack; both prior rounds' findings (AC-2 exclusion keying, AC-3 whitespace citation) hold closed against current source. New scrutiny of AC-1's 8-arm sweep (roundtrip_file's gate call is an unconditional no-op) and AC-4's lock/gate-hoist mechanics found nothing material — the mangler-removal property is independently pinned by AC-1's pattern-scan and create-arm oracles.
```
