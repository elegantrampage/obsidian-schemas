# Company stub parity — archived gate rounds

<!-- archive-split:v1 — IMMUTABLE APPEND-ONLY ARCHIVE. Written only by src/archive_split.py at a
completed conveyor transition; appended to, never edited, reordered or rewritten. It
carries no work-item frontmatter by design, so it is invisible to find_work_items and to
find_corrupt_work_item_docs. Living spec: docs/company-stub-parity.md -->

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


## Architectural Review — 2026-09-06

**Recommendation: PROMOTE to architected**

Cold-start read. Every `file:line` below was opened this round, not carried from the doc's own
citations: `obsidian_schemas/repositories/company.py`, `name_gate.py`, `name_validation.py`,
`writer.py:150-270,333-507`, `repositories/base.py:350-500`, `repositories/person.py:1105-1147,1310-1410`,
`models.py:1-140`, `scripts/lint_vault.py:440-470,938-949`, `tests/derivations.py:960-1010`,
`pipeline-runners.yaml`, `docs/company-name-corpus-audit.md`, `state/work-items.json`, and
`LESSONS.html` (#4, #7, #29, #32).

### Trigger check

Three fire, so the review runs rather than short-circuiting:

- **Establishes a new persistent contract / data shape** — a second Tier-1 table
  (`COMPANY_TIER1_BRANCHES`) and a `created_by` field that will exist on every company note written
  from here on.
- **Significantly extends a core system** — WI-021's gate, which is THE semantic write door for the
  whole package (`name_gate.py:1-53`).
- **Touches >3 files in different concerns** — `name_validation.py`, `name_gate.py`,
  `repositories/company.py`, `tests/`, plus the `docs/` audit artifact.

### Review

**Fit:** The approach reads back WI-021's own design instead of inventing one, and that is its main
virtue. `name_gate.py:311-312` is a *declared* pass-through for every non-person `declared_type`,
with the comment above it saying explicitly that a Book write "is gated and handed straight back" —
so the company arm is filling a hole the gate's author already marked, not bending the gate.
`name_gate.py:38-46` states the predicate-not-transform rule and its reason; `base.py:381-383` binds
`filename = f"@{name}.md"` from the raw `entity.name` one frame above every gate call and never
revisits it, which is exactly what the Constraints section says. I confirmed the company write
actually reaches the gate rather than assuming it: `create_stub:192` → `BaseRepository.save:388` →
`write_markdown_file` → `gate_write(fm, declared_type=fm.get("type"), whole_record=…)` at
`writer.py:252-253`, and `Company.type` is `Literal["company"] = "company"` (`models.py:127`), so
`fm["type"]` is the literal string the branch will key on. The person side already reifies its table
(`name_validation.py:170-289`) and walks it (`:506-510`), so "second table, same record, same walk"
harmonizes with the pattern rather than fighting it.

**Duplication:** In-tree the answer is clean and the design is the one that keeps it clean. I re-ran
the mangler scan myself: `obsidian_schemas/repositories/company.py:171` is the only live code site
in this tree (`person.py:1339` is a comment recording the WI-111 deletion; the rest are docs). And
homing the contract at the gate rather than at `create_stub` — D1, correctly rejected — is precisely
what stops a *second* name authority being born, which `name_gate.py:6-11` records as the defect the
person side actually had.

Out of tree it is **not** closed, and this item's own grounding artifact is what found it:
`docs/company-name-corpus-audit.md:121` records `exocortex/exocortex/ingestion/stages/company.py:157`
carrying a byte-identical copy of the same regex on the hourly company-ingest path, writing through
`write_markdown_file` directly. That path is outside this project's write authority
(`pipeline-runners.yaml:34-38`). This is LESSONS #4's named scar almost verbatim — "exocortex keeping
its *own* copy of the name-prefix regexes (`clean_person_name`) that won't inherit fixes to the
canonical validator". It does not block: the item structurally cannot reach that file, the audit
already names the follow-on and correctly identifies this item as its precondition
(`company-name-corpus-audit.md:163-171`), and widening a Dave-signed AC set into another repo is the
wrong instrument. But it is the one thing a reader of `## Problem / Motivation` would get wrong:
after this ships, `"O'Reilly Media"` → `"OReilly Media"` **keeps happening hourly** via exocortex.
The gate will judge that write, but exocortex's local copy has already destroyed the punctuation
before the gate ever sees the name, so the gate cannot tell. Note 1 below.

**Boundaries:** Ownership stays single-holder throughout: the gate owns the Tier-1 predicate,
`create_stub` owns Tier-2 repair *above* the filename derivation (mirroring `person.py:1327-1345`),
and `base.py:381-383` keeps owning the filename. The WI-185 question has the right answer here —
nothing is reconstructed at read time; the design stops the discard at the boundary that does the
discarding. One seam the spec-writer must *design* rather than discover: AC-2 requires the company
table be "walked by the same dispatcher", but `_raise_on_tier1` hardcodes `for branch in
TIER1_BRANCHES` (`name_validation.py:506`), and `validate_strict` raises `EMPTY_BRANCH` *above* the
chain (`:439-442`) and applies the phone-sentinel exemption above that (`:435-436`). Satisfying AC-2
therefore means parameterizing a person-side entry point. Non-blocking because it is mechanical, and
the default must stay `TIER1_BRANCHES` so no person behaviour moves — stated here so it is a decision
rather than a surprise. Note 3.

**Determinism boundary (LLM vs code):** No capability is handed to an LLM by this design, and the one
judgment/mechanical split that exists falls on the right side. The genuinely empirical question — does
any proposed branch refuse a company name that is legitimately on disk? — was settled by a measured
walk of 2,159 live `type: company` notes (`company-name-corpus-audit.md:14`, per-branch table
`:24-35`), not by reasoning about what company names look like; and AC-5's check is a mechanical shape
assertion over that artifact making no vault, subprocess or network call. That is LESSONS #7
(audit the real corpus before patching) and #32 (an unexecuted mechanical claim is a self-report)
both discharged with quoted output, including the verbatim scan commands and 40-hex HEADs at
`:80-150`.

**Reversibility:** High, and structurally so. The change is one branch in one function, one table in
one leaf module, and one deleted `re.sub` — no data migration, no on-disk format change, no
checkpoint needed. The delta rule is what makes back-out cheap and makes the fix non-bricking:
`gate_write` judges what a write *introduces*, never the merged record (`name_gate.py:30-36`), and I
confirmed all four gated update arms pass a delta rather than the record —
`writer.py:385-387`, `:443-445`, `base.py:473-475`, `lint_vault.py:947-948` — so every company note
already stored with a dirty name stays writable for any write that does not re-introduce the name.
A revert leaves nothing on disk to undo. The one piece that is irreversible in practice is a live
route starting to refuse; the audit bounds that at zero against the current corpus.

**Generalization:** Right-sized. A second table with its own membership, sharing the `Tier1Branch`
record (`name_validation.py:136-167`) and one walk, is three-similar-lines territory rather than a
premature per-type validator registry. Two types, two tables. The dispatcher parameterization the
Boundaries note describes is the natural seam if a third type ever needs one, and nothing here
forecloses it. The `pattern`-vs-`branch_id` discipline the doc adopts throughout (`## Approach`, D2,
AC-2) is correct and I verified the two divergences it rests on: `name_validation.py:194-227` gives
`arrow_connective`/`calendar_prefix`/`me_to_prefix` the shared `pattern="calendar_prefix"`, and
`:263-274` gives `branch_id="pure_digit"` / `pattern="pure_digit_name"`.

**Cost & maintenance:** One session, and I agree with the sizing — `Tier1Branch`, the walk,
`NameGateRefusal` and the derived arm sweep all exist already. Ongoing cost is one more table to keep
honest, and AC-2's negative-specimen field is what keeps it honest without a human re-auditing later,
which is the right trade. P5's claim that WI-021's derived AST wall stays green **without editing it**
is correct and I re-derived it rather than trusting it: `frontmatter_write_arms` collects `Assign`
nodes bound to the first positional argument of a `write_frontmatter` call (`tests/derivations.py:977-1008`),
and `gate_write` contains no `write_frontmatter` call at all, so a branch added inside it mints no arm.

**Build vs extend vs integrate:** Extend, correctly, and the two alternatives are ruled out on
grounds that hold against source. D1 (validator inside `create_stub`) is the pre-WI-021 defect
restated — `name_gate.py:6-11` records that exact history in the past tense. D3 (a narrower mangler)
re-incurs WI-111's ruling, whose reasoning is still in the tree at `person.py:1337-1344`, and re-opens
the filename/name divergence class WI-029 exists to repair (`state/work-items.json:877-879`). No
external library is in play.

**Prior art (outside view):** This item does build around a constraint, so the dimension applies. The
constraint: the vault binds identity to filename — `base.py:381-383` derives the stem from the name,
and `lint_vault.py:462-463` resolves `person.company` by comparing to `@{name}` stems — so a
character the filesystem or Obsidian forbids has nowhere to go. **The world's standard answer is to
decouple**: keep the display name intact and derive a separate slug/id for storage. That is what every
CMS and wiki does, what `django.utils.text.slugify` is, and — pointedly — the origin of the very
regex under discussion, which is `markdown/extensions/toc.py:44`'s *anchor-slug* function
(`company-name-corpus-audit.md:120`) misapplied to an identity field. This item takes the other road:
reject at the boundary, keep name and stem identical. The divergence is justified by a **cited
execution**, not by reasoning — the corpus walk found **zero of 2,159** live company names carrying
any character of the widened path-hostile set (`company-name-corpus-audit.md:29,48`), so rejection
costs nothing on the real corpus, while decoupling would change a vault-wide convention owned outside
this repo (wikilink targets, `_file_map` keying, the linter's stem comparison). Neither blocking
condition fires: this is not a 2nd+ recurrence of a constraint being compensated for — it is the
*first* application of an existing gate to a second type — and the one deferral behind a named
re-entry condition, D4, already has its work item minted (WI-029, `state/work-items.json:877-879`).

### Notes (non-blocking)

1. **The exocortex mangler copy is the item's unfinished half — mint the follow-on now, not later.**
   `company-name-corpus-audit.md:121,163-171` establishes it; this repo cannot fix it. Because it
   lives in another project it cannot be minted into this project's `state/work-items.json`, so it
   will be lost unless the conductor mints it in exocortex's backlog. Suggested shape: route
   `stages/company.py:132`'s `create_or_update_company` through the gate-backed
   `CompanyRepository.create_stub` and delete the local copy at `:157`. Until then the item closes the
   package's door while the hourly ingest keeps writing through its own.

2. **Place the company judgement so it cannot fall through into the person arm.** The cheapest-looking
   edit at `name_gate.py:311` — widening the condition to `declared_type not in (PERSON_TYPE,
   COMPANY_TYPE)` and letting company fall through — is wrong twice over: it applies `TIER1_BRANCHES`
   to company names (D2's rejected design, which refuses `"wetransfer.com"`), and it silently subjects
   company writes to the `phones[]` dedupe (`name_gate.py:346-347`) and the alias/email migrations
   (`:353,375-398`). The ACs catch the first (AC-1's preservation table plants `"wetransfer.com"`);
   nothing in the AC set catches the second. The company judgement belongs *inside* the non-person
   branch, before its `return dict(introduced)`.

3. **The dispatcher seam.** As above — `_raise_on_tier1` (`name_validation.py:485-510`) and
   `validate_strict` (`:426-449`) both hardcode the person table and its above-chain `empty` /
   phone-sentinel handling. Parameterize with `TIER1_BRANCHES` as the default.

4. **`name_validation.py`'s module docstring says "Single source of truth for what a *person* name
   looks like" (`:1`).** After this item that is no longer true of the module. One line, but it is the
   next reader's map.

5. **`create_stub`'s `"Unknown Company"` fallback (`company.py:172-173`) is unaddressed by `## Approach`.**
   Person keeps its analogous fallback (`person.py:1345-1347`), which is why `name_validation.py:275-279`
   can say `empty` "has never fired in production". If Company keeps its fallback, `empty` likewise
   never fires from `create_stub` and AC-2's `empty` specimen must be driven through a non-`create_stub`
   arm; if it is dropped, `create_stub("")` changes from writing a note to raising — a live behaviour
   change on HAL9000's `POST /api/entities/company` route (`company-name-corpus-audit.md:100,154-157`).
   Either is defensible; the spec should choose deliberately.

6. **Consumer handling of `NameGateRefusal` is measured but not resolved.** The audit delivered the
   call sites and HEADs AC-5 asks for, but not each consumer's *handling* of a new refusal. Two shapes
   differ: HAL9000's `entities.py:276` passes `name` verbatim, so the whole company table is reachable
   there; exocortex's path pre-strips with its local mangler, so only `empty` and `archive_prefix` can
   survive to fire. Loud failure is the house style and raising is correct — but an uncaught refusal on
   an hourly job is a different loudness from a 422, and it is worth one line in the spec's blast-radius
   section.

7. **D5 and D6 are parked in prose with no work item.** D4 has WI-029; D5 (Company's missing
   reuse-on-collision door, `person.py:1349-1367` vs `company.py:192`) and D6 (Person's whitespace-only
   `created_by`, `person.py:1387`) do not. Both are correctly out of the frozen Intent, and D6 in
   particular leaves a real hole open on the person side — a label that looks like a value and names
   nobody. Cheap to mint; easy to lose.

```verdict
gate: architect
verdict: PROMOTE
date: 2026-09-06
model: claude-opus-5
note: Approach B homes the company name contract in WI-021's existing gate as a predicate, which is a read-back of the gate's own declared design rather than a new one (name_gate.py:38-46, 311-312), and its one empirical premise — that no proposed branch refuses a name legitimately on disk — is settled by a cited corpus execution over 2,159 live notes rather than by reasoning; the surviving exocortex mangler copy is real but structurally out of write authority and is a conductor mint, not a defect in this approach.
```


## Data Audit — 2026-09-06

**Recommendation: REVISE — one artifact gap the caged builder cannot close**

Cold-start read. Reader tools only (Read/Grep/Glob, no shell): the live vault and the three consumer
repos are out of this cage and out of scope, so §1–§4 of `docs/company-name-corpus-audit.md` are
accepted as committed conductor evidence (the WI-024 precedent) and audited for SHAPE, internal
consistency, and conformance to the AC that pins them. Everything in-tree was re-executed this round
rather than carried from the doc's own citations.

### Trigger check

**Class 1 and Class 2 both fire — a real audit, not a trivial pass.**

- **Class 1 (data-distribution / field-presence).** The item asserts quantified claims about live
  data: 2,159 `type: company` notes, zero refused by any proposed branch, 7 mangler-residue notes
  sizing D4, and (in-tree) "exactly one live code site" for the mangler.
- **Class 2 (rule-effect-against-existing-corpus).** `COMPANY_TIER1_BRANCHES` is a new refusal rule
  whose correctness rests on its effect against the corpus as it exists TODAY — the "does this refuse
  a company legitimately on disk" question. This is the trigger's central case.

### Premise

Five load-bearing empirical claims, named explicitly:

- **E1 (corpus).** No member of the proposed five-branch table — including the *widened* path-hostile
  set — refuses any name currently stored on a live `type: company` note. Grounds AC-1 and AC-4's
  "no legitimate name becomes unwritable".
- **E2 (last live instance).** `company.py:171` is the only live site of the mangler in this package.
  Grounds AC-1's pattern-scan clause and the whole framing of `## Problem / Motivation`.
- **E3 (gate reachability).** A company write reaches `gate_write` with `declared_type == "company"`
  and is handed back untouched. Grounds the entire Approach: without it, the gate is the wrong home.
- **E4 (wall stability).** A branch added inside `gate_write` mints no new derived arm, so WI-021's
  AST wall stays green at eight arms without being edited. Grounds P5 and AC-1's derived sweep.
- **E5 (Person's guard).** `person.py:1387` does NOT normalize a whitespace-only `created_by`.
  Grounds AC-3's r2 divergence clause and D6.

### Predicate + result

Re-executed in-tree this round, 2026-09-06, against the seeded worktree:

| # | Predicate | Result |
|---|---|---|
| E2 | Grep `re\.sub\(\|re\.compile\(r?["']\[\^` over every `*.py` in the tree | 10 hits. The literal mangler regex is live at exactly one code site — `repositories/company.py:171` — plus `person.py:1339`, which is the WI-111 deletion-recording COMMENT. **E2 holds for the literal regex.** The other eight hits are dispositioned in the counterexample hunt below. |
| E3 | Read `company.py:153-194` → `base.py:388` → `writer.py:252` → `name_gate.py:293-312` | `create_stub:192` calls `self.save(...)`; `writer.py:252` is `fm.update(gate_write(fm, declared_type=fm.get("type"), …))`; `Company.type` is `Literal["company"]` (`models.py:127`); `name_gate.py:311-312` is `if declared_type is not None and declared_type != PERSON_TYPE: return dict(introduced)`. **E3 holds — reached, and declined.** |
| E4 | Grep `write_frontmatter` scoped to `obsidian_schemas/name_gate.py` | **0 occurrences.** `frontmatter_write_arms` (`tests/derivations.py:977-1008`) mints an arm only from an `Assign` feeding a `write_frontmatter` call's first positional arg, so a branch inside `gate_write` mints none. **E4 holds; the wall needs no edit.** |
| E5 | Hand-execute `person.py:1387` for `created_by="   "` | `not "   "` → `False`; `not isinstance("   ", str)` → `False`; `False or False` → `False`. The branch never fires; three spaces are stored verbatim. **E5 holds — AC-3's r2 divergence clause is correct and the "on Person's exact terms" phrasing was rightly struck.** |
| E1 | `docs/company-name-corpus-audit.md` §1–§3 | 2,159 live notes; per-branch refusal counts all **0**, including the widened path-hostile candidate; character census independently corroborates (`&` on 8 names, `.` on 3, and **no** live name carrying any of `/ \ : * ? " < > \| [ ] # ^`). **E1 holds on the numbers as reported** — but see the blocking finding on how they are evidenced. |

The r1/r2 AC-red-team premises about `name_validation.py` were also re-executed rather than trusted:
`:263-274` gives `branch_id="pure_digit"` / `pattern="pure_digit_name"`, and `:194-228` gives
`arrow_connective` / `calendar_prefix` / `me_to_prefix` the shared `pattern="calendar_prefix"`. Both
divergences AC-2 is built on are real.

### Blocking finding — the vault-side evidence is a REPORTED RESULT, not a QUOTED EXECUTION

AC-5 requires the artifact to carry "**the literal scan command run against the live vault with its
verbatim stdout** and the count of `type: company` notes scanned", and its `check:` asserts that
shape. The committed artifact does not carry it. §4 does this correctly for the three consumer repos
— three literal `grep` commands, verbatim stdout, four 40-hex HEADs (`company-name-corpus-audit.md:91-150`)
— but the vault walk itself is described in prose ("walked read-only, `*.md` with a frontmatter
`type: company` line, dot-directories skipped", `:11-13`), and §1's per-branch table (`:24-35`),
§2's character census (`:43-46`) and §3's residue counts (`:57-76`) present results with **no command
and no stdout**. The counts and the listed names are there; the execution that produced them is not.

Why this blocks rather than riding as a note. The artifact is a `kind: precondition` fence whose whole
purpose is that the **caged builder cannot reach the vault** — so a builder writing AC-5's test
faithfully goes RED against the artifact as committed, and cannot fix it: closing the gap requires
re-running the walk, which only the conductor can do. Catching it at build is the expensive place.
The remedy touches **no acceptance criterion and no signed hash** — it is one conductor edit to
`docs/company-name-corpus-audit.md`, so it costs no re-sign and no second interruption of Dave. The
architect's Determinism-boundary paragraph reads LESSONS #32 as discharged "with quoted output,
including the verbatim scan commands" — true of §4, over-read as to §1–§3, and #32 is exactly the
lesson that an unexecuted (or un-quoted) mechanical claim is a self-report.

Same edit, non-blocking rider: AC-5 also requires an empty result be "recorded as an explicit
'no matches' marker, never an absent field". Every `which` cell in §1's table is a bare em-dash
(`:26-31`). Whether an em-dash satisfies a shape test asserting an explicit marker is a coin-flip a
builder should not have to call — spell it while amending.

### Counterexample hunt (WI-293)

The document quantifies universally in two places over domains the factory can enumerate: AC-1's
"appears at **zero** live code sites in `obsidian_schemas/` and `scripts/`", and AC-1's sweep over
"**every** write arm `frontmatter_write_arms` derives". A third domain — the vault corpus — is walked
in the artifact. All three enumerated; each false-by-design class found is dispositioned below as a
**named exclusion the spec-writer must carry**, which closes it without editing a signed AC.

**Domain A — every character-class strip in `obsidian_schemas/` and `scripts/`.**
Predicate: Grep `re\.sub\(|re\.compile\(r?["']\[\^` over every `*.py` in the tree, then read each hit
in context. Ten members; **four false-by-design classes**, none of them the mangler:

1. **Filename sanitizers (3 sites): `book.py:348`, `book.py:352`, `meeting.py:229`** — all
   `re.sub(r'[<>:"/\\|?*]', '', …)`, all inside `_get_file_name`, operating on a LOCAL derived from
   the entity and never on the stored field (`BookRepository.create_stub` stores a bare
   `title.strip()`, `book.py:298`). They are the legitimate opposite of the mangler: it strips a
   negated catch-all class off an IDENTITY field; these strip an enumerated set of filesystem-hostile
   characters off a FILENAME. *Disposition — named exclusion:* AC-1's scan predicate must be the
   NEGATED catch-all shape (strip-everything-outside-`[\w\s-]`, or any equivalent whitelist-negation),
   never "a `re.sub` carrying a character class". Under the broad reading of "any equivalent
   character-class strip" a faithful builder goes RED on three sites whose only route to green is
   deleting filename sanitizers on Book and Meeting — outside the frozen Intent, and it would put
   `<>:"/\|?*` straight into note filenames.
2. **The deletion-recording comment: `person.py:1339`** — carries the literal mangler regex inside
   the WI-111 comment explaining why it was deleted. A literal text scan over tracked source hits it.
   AC-1 says "live code **sites**", which excludes it by intent; nothing says how the check
   discriminates. *Disposition — named exclusion:* the scan is comment-aware, or `person.py:1339` is
   an explicit allowlisted line. P1 records it as a comment; AC-1's own text does not.
3. **Non-name field normalizers: `phone_normalization.py:55`** (`re.sub(r"\D", "", phone)` — a
   negated class, on `phones`, and the leaf WI-021 relocated deliberately) and
   **`identifier.py:204`** (URL scheme strip). *Disposition — named exclusion:* the scan is scoped to
   name-bearing write paths, not to every regex substitution in the package.
4. **Tier-2 whitespace/digit repairs: `name_cleaning.py:136,138,197`** — the sanctioned Tier-2
   surface (`clean_person_name`, WI-117), and `\s{2,}` collapse is the very repair AC-1's `"Acme  Corp"`
   fixture requires to HAPPEN. *Disposition — named exclusion:* a Tier-2 repair is not a Tier-1
   mangler, and AC-1's own preservation table depends on this distinction holding.

**Domain B — the eight arms of `frontmatter_write_arms`.**
Predicate: read every `gate_write(` call site in `obsidian_schemas/` and `scripts/` and classify it
create-shaped (derives a filename) vs update-shaped (writes into an existing path). Six call sites,
eight arms; **two false-by-design classes** against AC-1's *second* leg ("the note's filename stem
equals `@{input}.md`"):

- **Update-shaped arms — 5 of 8: `base.py:473` (`update_fields`), `writer.py:385`
  (`update_frontmatter_field`), `writer.py:443` (`update_frontmatter_fields`), `lint_vault.py:947`
  (`apply_fixes`).** None derives a filename: `base.py:381-383` binds `@{name}.md` on the CREATE path
  only, and no arm here renames. The filename leg is not merely unexercised on these arms, it is
  meaningless — and worse, on an update the stem is whatever it already was, so a literal reading of
  "both legs, every arm" is unsatisfiable by a correct build. *Disposition — narrowed quantifier:*
  the filename-stem leg binds the three create-shaped `write_markdown_file` arms (`writer.py:252`);
  update-shaped arms carry the stored-`name:` leg alone.
- **`roundtrip_file` — false-by-design on BOTH legs.** `writer.py:494` is
  `gate_write({}, declared_type=None, whole_record=False)`: an empty delta, unconditionally, on every
  invocation. It introduces no name, so no company table can affect it. The re-verify-2 red-team round
  reached this arm from the opposite direction (could a bad build go green?) and cleared it; the
  inverse — can a correct build be asked for something this arm cannot express? — was not
  dispositioned. *Disposition — named exclusion:* `roundtrip_file` carries neither leg; it asserts YAML
  re-serialization fidelity and nothing about `COMPANY_TIER1_BRANCHES`.

**Domain C — the live vault, 2,159 `type: company` notes.**
Predicate: the audit's own walk (`company-name-corpus-audit.md:11-13`), read for its exclusions rather
than its counts. **One false-by-design member, filed in the census's exclusion line:**
`Templates/company.md` — it carries `type: company` and an EMPTY `name:`, and was excluded from the
population as "a template, not a company" (`:12-13`). That exclusion is right for the *population*
count and wrong for the *refusal* question: the file is on disk, it declares `type: company`, and the
new `empty` branch would refuse any write that re-introduced its name. §1's `empty` row therefore reads
0 by DEFINITION, not by measurement. *Disposition — already covered, stated so it is not rediscovered:*
AC-4's delta rule keeps it writable, and I verified every update-shaped arm passes a DELTA rather than
the merged record (`base.py:473-475`, `writer.py:385-387`, `:443-445`, `lint_vault.py:947-948`), so no
routine write re-introduces `name`. The honest number for `empty` is "0 live companies, 1 template,
writable under the delta rule".

Nothing else. The hunt found no member class that falsifies E1 itself: no live company name carries a
character any proposed branch refuses, and the character census (`&`, `.`, and nothing path-hostile)
independently corroborates the per-branch zeros rather than merely restating them.

### Conclusion

E2–E5 are grounded and were re-executed in-tree this round; every one holds. E1 — the load-bearing
Class-2 premise, and the only one that could make this item HARMFUL — is answered correctly on the
numbers, by a real walk of the real corpus, with per-branch rows and the refused names listed. This is
not a stale or hypothesized premise; it is the right audit, done.

What it is missing is the one thing AC-5 pins and the one thing that makes it re-runnable by the next
reader: the vault-side scan command and its verbatim stdout. The item cannot ship AC-5 green without
it, and the actor who must supply it is the conductor, not the builder. That is a one-edit fix to a
`docs/` artifact, touching no criterion text and no signed hash — cheap now, expensive at build.

Required grounding before this promotes:

1. Amend `docs/company-name-corpus-audit.md` §1–§3 to carry the literal vault-walk command(s) and
   verbatim stdout backing the 2,159 count, the per-branch refusal table, the character census and
   the 7-note D4 residue list — the shape §4 already models for the consumer repos. Spell the
   "no matches" marker explicitly while there.
2. Carry the counterexample hunt's dispositions above into the spec as named exclusions and the one
   narrowed quantifier. No AC text changes; the spec-writer records them so the builder implements
   AC-1's scan and sweep against the domains as bounded here.

```verdict
gate: data-premise
verdict: REVISE
targets: AC-5, AC-1, #write-targets
prior: none
basis: original
findings: 1/5
date: 2026-09-06
model: claude-opus-5
note: The corpus premise is answered correctly (2,159 notes, zero refusals, re-corroborated by the character census) but the vault-side evidence is a reported result rather than a quoted execution — AC-5 requires the literal scan command and verbatim stdout that §4 gives for the consumer repos and §1–§3 do not, and only the conductor can close it since the caged builder cannot reach the vault; four counterexample classes in AC-1's two universals (Book/Meeting filename sanitizers, the WI-111 comment, roundtrip_file's empty-delta arm, the five update-shaped arms with no filename leg) are dispositioned above as named exclusions needing no AC edit.
```

---


## Architectural Review — 2026-09-06

**Recommendation: PROMOTE to architected**

**This is a SECOND architect read, cold-start, taken after the `## Design`, `## Implementation Plan`,
`## Edge Cases`, `## Verification`, `## Scope Boundary` and `## Risk Analysis` sections landed.** The
earlier `## Architectural Review — 2026-09-06` section above PROMOTEd the *approach* when the document
ended at `## AC Sign-off`; that approach is unchanged and its verdict stands. What is new — and what
this round exists to pressure-test — is whether the design that was subsequently written is the design
that was promoted, and whether the machinery it now names holds against source. Every `file:line`
below was opened this round: `name_validation.py` (whole file), `name_gate.py` (whole file),
`repositories/company.py`, `repositories/base.py:355-500`, `repositories/person.py:1320-1405`,
`writer.py:190-270,370-507`, `name_cleaning.py:125-200`, `scripts/lint_vault.py:452-473`,
`tests/derivations.py:960-1010`, `tests/test_name_gate.py:150-230`,
`docs/company-name-corpus-audit.md`, and `LESSONS.html` (#4, #7, #29, #32, #33, #34, #37).

### Trigger check

The same three fire, so the review runs rather than short-circuiting:

- **Establishes a new persistent contract / data shape** — a second Tier-1 table and a `created_by`
  field on every company note written from here on.
- **Significantly extends a core system** — WI-021's gate (`name_gate.py:1-53`) and, now that §2 is
  written, `NameValidator`'s three entry points, which the person path runs.
- **Touches >3 files in different concerns** — `name_validation.py`, `name_gate.py`,
  `repositories/company.py`, two test modules, plus the `docs/` audit artifact.

### Review

**Fit:** The design is a faithful build-out of the promoted approach, not a drift from it, and its two
riskiest placements are correct against source. (a) The company judgement goes INSIDE the existing
non-person branch above its `return dict(introduced)` (§3), which is the placement the prior round's
Note 2 required — I confirmed the fall-through it avoids is real: widening the condition at
`name_gate.py:311` would carry company writes into the `phones[]` dedupe at `:346-347` (a DELETION over
stored data, `_dedupe_phones`'s own docstring says so at `:228-231`) and into the two migrations at
`:353,375-398`. (b) The arm stays a PREDICATE — `validate_strict`'s return discarded, `dict(introduced)`
returned — which is the rule `name_gate.py:38-46` states and the reason `base.py:381-383` gives it
(`name = getattr(entity, "name", "Unknown")` / `filename = f"@{name}.md"`, bound one frame above the
gate and never revisited). I re-walked the reach chain rather than inheriting it: `create_stub:192` →
`base.py:save:388` → `writer.py:252-253` `gate_write(fm, declared_type=fm.get("type"), …)`, with
`CompanyRepository.type_name` returning the literal `"company"` (`company.py:66-68`), so both the
create-shaped and the `update_fields` arms key on the string the branch tests.

**Duplication:** The design *reduces* in-tree duplication rather than adding to it, which is the
strongest thing I can say for §2.3. `clean` today interleaves the Tier-2 repair inline
(`name_validation.py:464-481`); naming it once as `tier2_repair` and composing both `clean` and
`company.py` onto it is the alternative to spelling `\s{2,}` a second time in the repository — the
second-authority shape this item exists to remove. I checked the obvious objection, that
`name_cleaning.py:197`'s `re.sub(r'\s{2,}', ' ', cleaned).strip()` already spells it: it does not
compete, because `clean_person_name` is the WI-117 *recovery* surface and that line is its terminal
normalize, not a Tier-2 contract other code invokes. And I re-ran the mangler scan myself:
`re.sub(r'[^\w\s-]', …)` appears at exactly one live code site in this tree,
`repositories/company.py:171` (`person.py:1339` is the WI-111 deletion comment). Task 7's deletion of
`import re` at `company.py:7` is safe — `re.` resolves at that one line in the whole module and
nowhere else.

Out of tree the duplication is **not** closed and the design says so plainly rather than eliding it:
`exocortex/exocortex/ingestion/stages/company.py:157` carries a byte-identical copy on the hourly
ingest path (`company-name-corpus-audit.md:121,158-171`). `exocortex/**` is outside this project's
`write_authority` (`pipeline-runners.yaml:34-38`). LESSONS #4's named scar is exocortex keeping its own
copy of these very regexes; `## Scope Boundary` now states the consequence in as many words — after
this ships, `"O'Reilly Media"` → `"OReilly Media"` keeps happening hourly and the gate cannot tell,
because the local copy destroys the punctuation before the gate sees the name. That is the right
handling for an item that structurally cannot reach the file, and it is still a conductor mint. Note 1.

**Boundaries:** The prior round's Note 3 — the dispatcher seam — was the one thing named as needing to
be *designed* rather than discovered, and §2 designs it correctly. `_raise_on_tier1` hardcodes
`for branch in TIER1_BRANCHES` (`name_validation.py:506`), `validate_strict` raises the module-level
`EMPTY_BRANCH` above the chain (`:440-442`) and applies the phone-sentinel exemption above that
(`:435-436`), and `clean` repeats both (`:457-462`); §2.2 parameterizes all three with the person table
as the default, so every existing call site — `person.py:1329`, `name_gate.py:329-331`, the whole of
`tests/test_name_validation.py` — is untouched by construction. Two details I checked rather than
assumed: `_raise_on_tier1` already `continue`s on `branch.regex is None` (`:507-508`), so the company
table's `empty` record is skipped by the chain and raised above it exactly as the person one is; and
`_empty_branch_of` rebinding `EMPTY_BRANCH` returns the SAME OBJECT, because `empty` is the only
regex-`None` record and it is last (`:280-293`), so `test_name_gate.py:189`'s
`assert EMPTY_BRANCH is TIER1_BRANCHES[-1]` holds by identity. Deriving the above-chain record from the
table instead of indexing position (§2.1) is the better of the two and closes a real hole: a second
table shipped without an `empty` record would otherwise make `validate_strict` silently ACCEPT `""` for
that type.

Ownership stays single-holder end to end: the gate owns the Tier-1 verdict, `create_stub` owns Tier-2
above the filename derivation, `base.py:381-383` keeps owning the filename. The WI-185 question has the
right answer — nothing is reconstructed at read time; the discard is stopped at the boundary that
discards it.

**Determinism boundary (LLM vs code):** No capability is handed to an LLM. The one empirical question
— does any proposed branch refuse a name legitimately on disk — was settled by a measured walk of
2,159 live `type: company` notes with a per-branch table and a corroborating character census
(`company-name-corpus-audit.md:12-14,24-35,43-48`), not by reasoning about company names; and AC-5's
check is a mechanical shape assertion making no vault, subprocess or network call. That discharges
LESSONS #7. It does **not** yet discharge #32 for §1–§3 of the artifact — see Note 2 — but that is a
gap in the evidence's *form*, not in the design's determinism split.

**Reversibility:** High, and structurally so. One branch inside one function, one table and three
defaulted keywords in one leaf module, one rewritten method, one widened test census, one deleted
`re.sub`. No migration, no on-disk format change, no flag. The property that makes it non-bricking is
the delta rule, and I confirmed every gated arm passes a DELTA rather than the merged record:
`base.py:473-475`, `writer.py:385-387`, `writer.py:443-445`, and `roundtrip_file`'s literal
`gate_write({}, declared_type=None, whole_record=False)` at `writer.py:494`. So the seven residue notes
D4 defers (`company-name-corpus-audit.md:57-67`) stay writable for every write that does not
re-introduce their name, which is the property this item owes them. The one thing a revert does not
undo is the `created_by` field on stubs written while it was live — additive and harmless, as
`## Risk Analysis` says.

**Generalization:** Right-sized, and the design resists the over-build. Two types, two tables, one
`Tier1Branch` record (`name_validation.py:136-167`), one walk — three-similar-lines territory rather
than a per-type validator registry. `negative_specimen` is appended WITH a default so the ten person
records keep compiling untouched, and AC-2 requires it non-empty for company members only, so the
default can never silently satisfy the correctness oracle where it matters. `## Scope Boundary`
declining to widen `__all__` is the same instinct and is correct: adding a public surface invites a
consumer this item has not audited.

**Cost & maintenance:** One session, and the two arithmetic claims the plan rests on both check out.
W8: `tests/test_name_gate.py:196-207` builds `compiled` from every module-level `*_RE` and asserts
`tabled == compiled - tier2` with `len(tabled) == 9`; the person table walks 9 distinct regexes, the
company table shares `_EMAIL_CHARS_RE`, `_ARROW_CONNECTIVE_RE` and `_ARCHIVE_PREFIX_RE` as the same
objects and contributes only `_COMPANY_PATH_HOSTILE_RE`, so the union is 10 and `compiled - tier2` is
10 — Task 5's move from 9 to 10 is a derivation, not a guess. W10: `frontmatter_write_arms` mints an
arm only from an `Assign` feeding a `write_frontmatter` call's first positional argument
(`tests/derivations.py:977-1008`), and `gate_write` contains no `write_frontmatter` call at all, so a
branch inside it mints no arm and the eight-arm floor needs no edit. Ongoing cost is one more table to
keep honest; the per-member negative specimen is what keeps it honest without a human re-auditing.

**Build vs extend vs integrate:** Extend, and the alternatives are ruled out on grounds that hold
against source. D1 is the pre-WI-021 defect restated — `name_gate.py:6-12` records exactly that history
in the past tense. D3 re-incurs WI-111's ruling, whose reasoning is still in the tree at
`person.py:1337-1344`. §2.3's decision to give companies ONE refusal channel (gate-owned Tier-1, so
`create_stub` raises `NameGateRefusal` rather than Person's `NameValidationError`) is a deliberate
non-mirroring of Person and is the right one — Person's `create_stub` calls `clean` (`person.py:1329`)
and therefore carries a second Tier-1 authority, which is the shape this item is removing, not
copying. Its cost lands downstream and is named in Note 3.

**Prior art (outside view):** Unchanged from the prior round and still correct. The constraint is that
this vault binds identity to filename (`base.py:381-383`; `lint_vault.py:462-463` resolves
`person.company` by comparing to `@{name}` stems), so a filesystem- or Obsidian-hostile character has
nowhere to go. The world's standard answer is to DECOUPLE — keep the display name and derive a slug —
which is what every CMS does, what `slugify` is, and the actual origin of the regex under discussion
(`markdown/extensions/toc.py:44`, `company-name-corpus-audit.md:120`, an anchor-slug function
misapplied to an identity field). This item takes the other road, and the divergence is justified by a
CITED EXECUTION rather than by reasoning: zero of 2,159 live company names carry any character of the
widened path-hostile set (`:29,48`), so rejection costs nothing on the real corpus, while decoupling
would change a vault-wide convention owned outside this repo. Neither blocking condition fires — this
is the first application of an existing gate to a second type, not a 2nd+ recurrence of a compensated
constraint, and D4's deferral already has its work item minted (WI-029).

### Notes (non-blocking)

1. **The exocortex mangler copy is still an unminted conductor follow-on.** Restated from the prior
   round because nothing has closed it: route
   `exocortex/exocortex/ingestion/stages/company.py:create_or_update_company:132` through the
   now-gate-backed `CompanyRepository.create_stub` and delete `:157`. It cannot be minted into this
   project's `state/work-items.json`; it will be lost unless the conductor mints it in exocortex's
   backlog. LESSONS #37's shape — the fix that exists only in prose prevents nothing.

2. **Prerequisite 2's amendment has NOT landed, verified this round against the artifact as it stands
   in the tree.** `docs/company-name-corpus-audit.md` §4 carries three literal commands, verbatim
   stdout and four 40-hex HEADs (`:91-150`); §1–§3 still present the 2,159 count, the per-branch table,
   the character census and the residue list with no `Command:` and no `Output` block
   (`:11-14,24-35,43-48,57-76`), and §1's `which` cells are still bare em-dashes (`:26-31`). This is
   LESSONS #33 exactly — a precondition only a non-builder actor can perform, which naming does not
   execute. It is not an architectural defect and it does not block this gate: the design's three
   layers (Prerequisite 2's field grammar, the Implementation Plan's abort preamble, Task 12's matching
   assertions) are the right instrument and bound the cost at one aborted spawn with nothing written.
   But #33's rule asks for a provably-executed step or a pre-spawn content check, and the WI-156 probe
   tests presence in HEAD only — so the conductor commit is the last thing standing between this item
   and a burned attempt. Land it before arming the builder.

3. **The refusal-type asymmetry at `create_stub` reaches a live route, and the follow-on is HAL9000's.**
   Person's `create_stub` raises `NameValidationError`, which HAL9000 maps to 422
   (`name_validation.py:336` records the contract); Company's will now raise `NameGateRefusal` out of
   `save()`. R2 names this and correctly declines to close it. Worth stating once more because the
   design's *reason* for the asymmetry is a virtue (one authority) while its *effect* is a 500 on
   `POST /api/entities/company` — the fix is one `except` clause in a repo this item cannot reach, and
   it belongs in the same conductor mint as Note 1.

4. **The company table's ORDER is load-bearing in a way the person table's is not, and §1.3 does not
   say why.** `_COMPANY_PATH_HOSTILE_RE` contains `<` and `>`, so it also matches the ASCII `->` that
   `arrow_connective`'s specimen `"Acme -> Globex"` carries — that specimen raises `calendar_prefix`
   only because `arrow_connective` precedes `path_hostile` in the tuple. AC-2's per-record
   pattern-equality leg does catch a reordering (the specimen would raise `path_hostile_char`), so this
   is checked rather than merely hoped for. Two things follow that the spec should record where the
   table literal is: the ordering constraint itself, and the fact that `arrow_connective` still earns
   its place because the six UNICODE arrows in `_ARROW_CONNECTIVE_RE:89` are outside the widened
   path-hostile set even though `->` is inside it.

5. **The widened path-hostile set makes two of the exploration's own example names unwritable, and the
   design quietly softened the specimen rather than saying so.** `### Constraints discovered` cites
   `"Company #1"` and `"Smith & Co. [UK]"` as shapes companies carry and person names do not; §1.2 then
   refuses `#`, `[` and `]`, and §1.3's negative specimen is `"Smith & Co. (UK)"` — parentheses, not
   brackets. The corpus makes this safe (zero of 2,159) and the failure is loud, so it is not blocking
   and R1 carries the residual honestly. But it is a deliberate policy narrowing that one section of
   this document argues for and another argues against; one clause at §1.2 saying "and yes, this makes
   the bracket form unwritable — refuse loudly rather than strip silently, per D3" removes the
   contradiction.

6. **`## Problem / Motivation`'s "last live instance of the mangler regex" is tree-scoped prose that
   reads as estate-wide.** P1's predicate is explicitly "over the whole tree", the audit found the
   exocortex copy afterwards, and `## Verified Diagnosis` and `## Scope Boundary` both correct it — so
   nothing is buildable two ways and no criterion depends on it. One qualifying clause in the opening
   paragraph would stop the next reader forming the wrong picture of the estate.

7. **D5 and D6 remain parked in prose with no work item.** D4 has WI-029. D5 (Company has no
   reuse-on-collision door — `person.py:1349-1367` vs `company.py:192`) and D6 (Person stores a
   whitespace-only `created_by` verbatim — `person.py:1387`, hand-executed again this round) do not.
   Both are correctly outside the frozen Intent; D6 in particular leaves a label that looks like a
   value and names nobody, on the side this item is not touching. Cheap to mint, easy to lose.

OPEN questions: **0** (cap is 2).

```verdict
gate: architect
verdict: PROMOTE
date: 2026-09-06
model: claude-opus-5
note: Second cold-start read, post-spec: the design that was written is the design that was promoted, and its three riskiest mechanics hold against source — the judgement is placed INSIDE name_gate.py's non-person branch (closing the prior round's Note 2 fall-through into the phones dedupe and migrations), the dispatcher parameterization defaults to TIER1_BRANCHES so no person behaviour moves and EMPTY_BRANCH's identity survives, and both counting claims re-derive correctly (W8 union of 10 regexes, no new frontmatter_write_arms member since gate_write calls write_frontmatter nowhere); the one open blocker is Prerequisite 2's audit-artifact amendment, which is a LESSONS-#33 conductor precondition rather than an architectural defect and is already bounded by the plan's abort preamble.
```


## Data Audit — 2026-09-06 (round 2)

**Recommendation: REVISE — the prior round's blocking finding is not closed, and re-reading the
artifact for it found the one row it most matters for is uninformative as printed**

Cold-start re-read of the document as it now stands, taken after `## Design`, `## Implementation
Plan`, `## Edge Cases`, `## Verification`, `## Scope Boundary` and `## Risk Analysis` landed. Reader
tools only (Read/Grep, no shell). Every in-tree predicate below was re-executed this round rather
than carried from the prior round's own table or from the document's citations; the live vault and
the three consumer repos remain out of this cage, so `docs/company-name-corpus-audit.md` is read as
committed conductor evidence and audited for shape and internal consistency.

### Trigger check

**Class 1 and Class 2 both fire, unchanged from round 1.** Class 1: the item rests on quantified
claims about live data (2,159 `type: company` notes, zero refused by any proposed branch, 7 residue
notes sizing D4). Class 2: `COMPANY_TIER1_BRANCHES` is a new refusal rule whose correctness rests on
its effect against the corpus as it exists today — the trigger's central case.

### What round 1 required, and what happened to each

Round 1 stamped REVISE with two required-grounding items. They did not fare the same way, so they are
dispositioned separately rather than as one arc.

**Required grounding 2 — CLOSED, and closed well.** The counterexample hunt's four false-by-design
classes and its one narrowed quantifier are carried into the spec as build instructions that change
no criterion text: §8.1 replaces "any equivalent character-class strip" with a stated
negated-catch-all-DELETION predicate (arms A and B), which is what keeps `book.py:348,352` and
`meeting.py:229` — re-confirmed this round as `re.sub(r'[<>:"/\\|?*]', '', …)`, enumerated rather
than negated — out of AC-1's scan; §8.2 excludes `person.py:1339`'s WI-111 comment BY CONSTRUCTION
(the predicate reads parsed syntax, so a comment is not a node) rather than by a line allowlist;
§8.3 dispositions `phone_normalization.py:55`, `identifier.py:204` and `name_cleaning.py:136,138,197`
against the same predicate; §8.4 narrows AC-1's filename-stem leg to the three create-shaped arms and
names `roundtrip_file` and `lint_vault.apply_fixes` as carrying neither leg, with the classification
asserted TOTAL over the DERIVED arm set in both directions so a ninth arm is RED until classified;
and §8.5 records the `Templates/company.md` disposition. Task 2's near-miss battery ships the same
shapes as fixtures. This is the fold doing the work the finding asked for.

**Required grounding 1 — NOT closed.** `docs/company-name-corpus-audit.md` is byte-unchanged: §1's
per-branch table (`:24-31`), §2's character census (`:43-48`) and §3's residue list (`:57-76`) still
carry no `Command:` line and no output block, §1's `which` cells are still bare em-dashes, and the
vault walk itself is still prose (`:11-14`). §4 still models the correct shape for the three consumer
repos (`:91-150`). The spec's answer is machinery rather than closure — Prerequisite 2 states the
exact field grammar, the Implementation Plan's preamble makes the builder ABORT rather than
fabricate, R6 prices it at one aborted spawn, and Task 12 asserts that same grammar. That machinery
is right, and it is not a substitute for the evidence: it bounds the COST of the gap without
grounding the premise, and the actor who must close it is the same conductor who drives this gate.

### Premise + predicate, re-executed 2026-09-06

E1–E5 are the five load-bearing claims round 1 named; the numbering is kept so the two rounds read as
one arc.

| # | Predicate re-run this round | Result |
|---|---|---|
| E2 | Grep `re\.sub\(\|re\.compile\(r?["']\[\^` over every `*.py` in the tree | 10 hits, unchanged. The literal mangler is live at exactly one code site, `repositories/company.py:171`; `person.py:1339` is the WI-111 comment; the other eight are the four classes §8.1–§8.3 now disposition. **E2 holds.** |
| E3 | Read `name_gate.py:300-319` and every `gate_write(` call site under `obsidian_schemas/` and `scripts/` | `name_gate.py:311-312` is still `if declared_type is not None and declared_type != PERSON_TYPE: return dict(introduced)`, with the comment at `:308-310` naming the pass-through as declared design. Seven call sites: `writer.py:252,385,443,494`, `base.py:473`, `lint_vault.py:947`, `person.py:1247`. **E3 holds — reached, and declined.** |
| E4 | Grep `write_frontmatter` scoped to `obsidian_schemas/name_gate.py` | **0 occurrences.** A branch inside `gate_write` mints no arm. **E4 holds; the AST wall needs no edit.** |
| E5 | Hand-execute `person.py:1387` for `created_by="   "` | The line is still exactly `if not created_by or not isinstance(created_by, str):`; `False or False` is `False`, so three spaces are stored verbatim. **E5 holds — AC-3's r2 divergence clause is correct.** |
| E1 | Re-read `docs/company-name-corpus-audit.md` §1–§3 for the widened path-hostile row specifically | The corpus-safety conclusion holds, but NOT on the strength of the row that measures it — see the finding below. **E1 holds via §2's census, not via §1 row 4.** |

Two claims the document makes about the derived arm population were also re-derived rather than
trusted, because a seventh `gate_write` call site turned up in E3's sweep that §8.4's eight-arm map
does not list: `PersonRepository.save:1247`. It mints no arm — `frontmatter_write_arms`
(`tests/derivations.py:977-1008`) keys on `write_frontmatter` calls, never on `gate_write`, and the
docstring at `:992-996` states that `PersonRepository.save` yields ZERO for exactly that reason. So
§8.4's "eight arms over six functions" stands and its leg map is total as written. Naming it so the
next reader can tell the discrepancy was checked rather than missed.

### Finding 1 (BLOCKING, carried) — the vault-side evidence is still a reported result, not a quoted execution

Unchanged in substance from round 1 and restated only because the artifact is unchanged: AC-5's
frozen text pins "the literal scan command run against the live vault with its verbatim stdout", the
committed artifact supplies that for §4 and not for §1–§3, and only the conductor can close it. What
IS new is that the spec now states the exact bytes required (Prerequisite 2), so the remedy is no
longer a judgement call — it is a transcription of a grammar the document itself declares, touching
no criterion text and no signed hash.

### Finding 2 (RIDER on the same edit, non-blocking alone) — §1's widened path-hostile row prints a pattern that cannot match, so that row's zero is uninformative

The one genuinely NEW refusal class this item introduces is the widened path-hostile set; every other
company branch reuses a regex the person table already ships and has already been audited against a
live corpus. §1 row 4 (`company-name-corpus-audit.md:29`) reports it as refusing 0 live names, and
prints the regex it used as `[/\:*?"<>|[]#^]`. Read as Python: the class opens at `[`, takes
`/ \: * ? " < > | [`, and CLOSES at the next `]` — leaving `#^]` as three literal characters that
must follow the matched one. As printed, that pattern matches no company name whatsoever, so its
`0` is what the pattern guarantees rather than what the corpus says. The regex the design actually
ships is `r'[/\\:*?"<>|\[\]#^]'` (§1.2), which escapes the inner bracket pair.

I do not conclude that E1 is false — the opposite. §2's census is the stronger instrument and it
answers the question independently: it enumerates EVERY character present in live company names
outside `[\w\s-]`, and returns only `&` (8 names) and `.` (3 names). Every member of the widened set,
every arrow, and `@` all lie outside `[\w\s-]`, so their absence from that census is a positive
measurement rather than a restatement of §1's zeros. E1 holds. What this finding establishes is that
the corpus safety of the item's only new refusal class rests on a census whose own execution is
equally unquoted, while the row that purports to measure it directly is, as printed, vacuous — which
is precisely the distinction between a reported result and a quoted execution, with teeth. The
remedy is one clause on the same conductor edit Finding 1 already requires: the amendment's
`Command:` block must carry the pattern AS EXECUTED, and Prerequisite 2's grammar should say so, so
the artifact cannot report a number produced by a different pattern than the one the build ships.

### Counterexample hunt (WI-293)

The document's universals are the same three domains round 1 enumerated; all three were re-walked
against the current text, because the fold added material to two of them.

**Domain A — every character-class strip in `obsidian_schemas/` and `scripts/`.** Predicate: the grep
in E2's row, then each hit read in context. Ten members, the same four false-by-design classes, and
all four are now dispositioned IN THE SPEC (§8.1–§8.3) rather than only in the audit. Re-checking the
fold's own predicate against them: `book.py:348,352` and `meeting.py:229` carry an enumerated class
and are excluded by arm (A)'s `[^` requirement; `phone_normalization.py:55` and `identifier.py:204`
likewise carry no `[^`; `name_cleaning.py:138,197` have non-empty replacements and `:136` carries no
`[^`; `person.py:1339` is a comment and therefore not a node. **No new member class, and the fold's
predicate excludes every one it was written to exclude.**

**Domain B — the arms of `frontmatter_write_arms`.** Predicate: every `gate_write(` call site under
`obsidian_schemas/` and `scripts/`, read and classified, then checked against the derivation's own
rule. Seven call sites; the eighth-arm accounting is unchanged, and the one member the leg map does
not name — `PersonRepository.save:1247` — is false-by-design as an ARM rather than as a leg: it calls
`gate_write` but no `write_frontmatter`, so the derivation mints nothing for it. *Disposition —
already covered:* §8.4's map is asserted total over the DERIVED set, so nothing is owed; recorded
here only because a reader comparing "seven gate calls" to "eight arms over six functions" would
otherwise suspect a miscount.

**Domain C — the live vault, 2,159 `type: company` notes.** Predicate: the audit's own walk, read for
its exclusions. The single false-by-design member is `Templates/company.md` (declares `type: company`,
empty `name:`, excluded from the population as a template), and §8.5 now carries the disposition
verbatim — writable under the delta rule, honest number "0 live companies, 1 template". **Closed by
the fold.** One new sub-domain the fold introduced was walked too: §10's wall census declares itself
a measured FLOOR rather than a total and hands Task 14 the obligation to RUN each predicate on final
text, so it quantifies over nothing it has not bounded and owes no hunt.

### Conclusion

The empirical premise is, on its numbers, right — and this round found nothing that moves it. E2–E5
were re-executed in-tree and all four hold unchanged; E1's corpus-safety answer survives scrutiny,
and survives it through §2's census rather than through §1's per-branch row. The spec-writer's fold
closed the whole of round 1's second required-grounding item, and closed it at the source rather than
where the finding pointed.

What is unresolved is what was unresolved before: the artifact reports results the next reader cannot
re-run, on the one premise that could make this item harmful. Round 1 priced that as "cheap now,
expensive at build"; the spec has since made it cheap at build too, and that is a real improvement to
the blast radius — but it converts a burned build into an aborted spawn, not evidence into evidence.
The gate does not promote a Class-2 premise whose grounding artifact its own frozen criterion pins
and does not have, when the remedy is one commit by the actor reading this verdict.

Required grounding before this promotes — one edit, no AC text, no re-sign:

1. Amend `docs/company-name-corpus-audit.md` §1–§3 to Prerequisite 2's grammar: the `Command:` block
   and verbatim `Output` block for the vault walk plus a `Notes scanned:` count, the same pair inside
   §1, §2 and §3, and `no matches` spelled in place of §1's em-dashes.
2. Add one clause to that amendment and to Prerequisite 2's grammar: each `Command:` block carries the
   pattern AS EXECUTED. §1 row 4's printed `[/\:*?"<>|[]#^]` closes its character class early and
   matches nothing, so as it stands the row's `0` is guaranteed by the pattern rather than measured
   from the corpus; the shipped regex is `r'[/\\:*?"<>|\[\]#^]'` (§1.2). E1 is not in doubt — §2's
   census carries it — but the row that most directly answers "does the new class refuse anything on
   disk" must be re-runnable, not re-readable.

```verdict
gate: data-premise
verdict: REVISE
targets: AC-5, #design
prior: mixed
basis: original
findings: 1/2
date: 2026-09-06
model: claude-opus-5
note: Round 1's counterexample-hunt dispositions are fully closed by the fold (§8.1-§8.5, at the source rather than where the finding pointed) but its blocking finding is not — docs/company-name-corpus-audit.md is byte-unchanged, §1-§3 still carry no command and no stdout, and the spec's answer (Prerequisite 2's grammar, the builder's abort preamble, R6) bounds the COST of the gap without grounding the premise; re-reading the artifact for that finding turned up a rider on the same one-commit remedy — §1's widened path-hostile row prints `[/\:*?"<>|[]#^]`, which closes its character class early and can match nothing, so the zero for this item's ONLY new refusal class is guaranteed by the pattern rather than measured, and E1 survives on §2's independent character census (only `&` and `.` outside `[\w\s-]` across 2,159 notes) rather than on that row.
```


## Threat Model — 2026-09-06

**Recommendation: PROMOTE to threat-modeled**

Cold-start STRIDE-lite read, first threat-model round on this item (no prior round to carry forward).
Read end-to-end, then cross-read against current source rather than against the document's citations:
`obsidian_schemas/name_gate.py` (whole file), `obsidian_schemas/name_validation.py:80-150`,
`obsidian_schemas/repositories/company.py:120-195`, `obsidian_schemas/repositories/person.py:1320-1404`,
`obsidian_schemas/writer.py:120-260`, `obsidian_schemas/vault_io.py:note_lock:363-414`,
`obsidian_schemas/parser.py:76-101`, and the project `CLAUDE.md`.

### Trigger check

Four fire, so the review runs rather than short-circuiting.

- **Handles input from external sources.** The `name` string arrives from HAL9000's
  `POST /api/entities/company` request body (`backend_fastapi/routers/entities.py:276`, the one live
  consumer) and from ingesters.
- **Persists data to user-owned files.** Every path here ends in a vault note write.
- **Performs filesystem operations on user-owned files**, and the value under review is the one that
  *derives the filename* (`repositories/base.py:save:381-383` binds `@{name}.md` from the raw name).
- **Crosses a trust boundary**, declared by the spec itself at Prerequisite 8: untrusted `name` →
  vault, with the gate as the boundary.

No secrets, credentials, OAuth scopes, MCP scopes, outbound API calls, subprocesses or permission
changes are in scope — checked, not assumed: Prerequisite 6 and AC-5's own text forbid a subprocess,
network or vault call in the checks, and Task 12's whole check is `read_text()` plus regex.

### STRIDE review

**Spoofing.** The company `name` IS the note identity, so a name that can impersonate another note is
the spoofing surface. The design closes the reachable form of it and keeps identity single-valued:
the gate is a PREDICATE that discards `validate_strict`'s repaired string (§3, property 1), so no
write can store `name: A B` inside `@A  B.md` and fork one company into two notes — the divergence
class WI-029 exists to repair on the person side. I checked the residual: homoglyph and
case-variant collisions (`@Аcme.md` with a Cyrillic А) survive both tables, but `\w` is
Unicode-aware in Python 3 patterns so the deleted mangler never caught them either — no regression,
and it is a vault-wide question that persons share. Not blocking, and not this item's to open.

**Tampering.** Three sub-questions, each checked against source.

*The delta rule is an integrity control, not just an ergonomics one.* `gate_write` judges
`introduced` — the delta — at every arm (`name_gate.py:31-36`), so this item cannot brick the 7
already-mangled notes into an unwritable state where a repair tool has to reach around the write
door to fix them. Remedy-is-the-disease avoided, and AC-4's delta clause pins it.

*No fall-through into the person body.* This is the one real integrity hazard the design creates for
itself, and it is correctly walled: `_dedupe_phones` is a DELETION over stored data
(`name_gate.py:228-231` says so outright), and the widened-condition spelling the architect's Note 2
warns about would silently apply it plus two migrations to company notes. §3's placement INSIDE the
non-person branch is structural, and Task 6 asserts a company payload carrying `phones`, `emails`
and `aliases` returns byte-identical. Carried as M5 below, because no frozen AC catches it.

*TOCTOU on the hoisted gate call.* The gate runs above `note_lock` at the create-shaped arms
(`writer.py:207-253`). I checked whether hoisting judgement outside the lock creates a
check-then-use window and it does not: the gate reads only its own arguments (`name_gate.py:22-29`),
and the one value that comes off disk — `declared_type` derived from the target note's own stored
`type:` at the update arms (`writer.py:385-386,443-444`) — is read IN-LOCK. Nothing judged outside
the lock can change between judgement and use.

*Declared-type confusion.* A caller who spells `type: book` gets the blanket pass-through and can
write any `name:` — but only into a path that caller already chose, and only for a payload it
already controls. Pre-existing for every non-person type, strictly narrowed by this item rather than
widened, and unreachable through `CompanyRepository`, whose `type_name` is the `Literal["company"]`
on the model (`models.py:127`). Not a finding.

**Repudiation.** This item is a net *improvement* to the audit trail and that is half its Intent:
`created_by` moves from absent (VD-3 — the string does not occur in `company.py` at all) to always
written, with `unknown` plus a WARNING as the findable sentinel for an unlabeled writer, and AC-3's
whitespace disjunct closes the shape that defeats that sentinel most quietly. Two honest limits,
both non-blocking and both noted below rather than swallowed: the label is self-asserted and
unauthenticated, and provenance covers only the `create_stub` arm of six.

**Information disclosure.** The sharpest instance is handled, and by inheritance rather than by
re-argument: `NameValidationError` interpolates the raw name into its message at every branch site,
and for `contains_email_chars` that "name" IS an email address — so the company arm raising through
the one `_refuse` construction site (`name_gate.py:134-166`), which suppresses the exception chain
via `chainable_cause` and puts no note-derived value in the message, is what keeps a refused address
out of the message, `__context__` and any rendered traceback. Verified at source, since the whole
property rests on that site being the only one. Carried as M1. Log surface checked for parity: the
INFO repair log in §4 renders `input=%r`, which is byte-identical in shape to Person's own at
`person.py:1331-1334` — parity, not a new class. Serialization checked too, because deleting a
stripper that absorbed `:`, `"` and `#` invites a frontmatter-injection question: `write_frontmatter`
is `yaml.dump` (`writer.py:152-157`) and reads are `yaml.safe_load` (`parser.py:101`), so a name
carrying YAML metacharacters round-trips as a quoted scalar and cannot inject a key, and a
non-`str` name emitting a python-specific tag is refused loudly at read rather than deserialized.

**Denial of service.** No rate limit, quota or cost ceiling is relevant — no outbound call, no
subprocess, no unbounded recursion, and the new per-write cost is walking a five-record table. Two
availability questions checked rather than waved: the added regexes are linear character classes and
literal-anchored (`_COMPANY_PATH_HOSTILE_RE`, `^z+Archived\b`), so no ReDoS reach; and an
unbounded-length name still fails loudly at the filesystem (ENAMETOOLONG) exactly as it does for
persons today — no length branch exists in either table, and adding one is a separate question
against a separate corpus. The real availability delta is a previously-permissive write path
starting to refuse, which R2 prices for HAL9000; the automated-consumer half of it is Note 2 below.

**Elevation of privilege.** Nothing. No scope, permission, credential or sudo path is touched; the
checks are hermetic by Prerequisite 6; the one new file-read capability in the suite is Task 12's
`read_text()` of a `docs/` artifact already in HEAD.

### Mitigations verified in place

All five are already required by the frozen criteria and already carried by a named plan task — the
fences below record which task each one lands on so the fold is machine-enforced rather than resting
on prose, and none of them asks for work the plan does not already contain.

1. **The refusal carries no note-derived value** — one construction site, chain suppressed
   (`name_gate.py:134-166`); asserted by AC-2 leg (a) and Task 8. → M1
2. **The refusal precedes every filesystem artifact** — the gate hoist above `note_lock`, whose
   outermost acquisition `ensure_dir`s a sentinel home under the note's own parent
   (`vault_io.py:393-400`), which for a `/`-bearing name is `<vault>/@Acme/`; asserted by AC-4's
   no-stray-directory leg and Task 11, with `OBSIDIAN_SCHEMAS_LOCK_DIR` unset by Prerequisite 3 so
   the oracle cannot pass vacuously. → M2
3. **Reject, never sanitize, and leave no second name authority** — AC-1's zero-live-site scan over
   the whole tracked source, Task 9. → M3
4. **Provenance on every stub, with a findable sentinel** — AC-3, Task 10. → M4
5. **No fall-through into the person body's destructive normalizations** — §3's placement, Task 6,
   and the only one of the five that no frozen AC catches. → M5

```mitigation
kind: required
id: M1
desc: The company arm's refusal must raise through the single `_refuse` construction site so no note-derived value — above all the refused name, which for `contains_email_chars` IS an email address — reaches the exception message, its context chain or a rendered traceback.
landed: Task 8
```

```mitigation
kind: required
id: M2
desc: A refused company name must leave nothing on disk: for a path-hostile name the vault carries no `@<first-segment>` directory, no lock sentinel inside one, and no `@<first-segment>.md`, asserted from paths the test itself computed rather than from a directory listing.
landed: Task 11
```

```mitigation
kind: required
id: M3
desc: The boundary rejects a hostile company name and never sanitizes it — no negated-character-class deletion may survive at any live site in `obsidian_schemas/` or `scripts/`, so no second name authority can silently manufacture a stored name the gate never judged.
landed: Task 9
```

```mitigation
kind: required
id: M4
desc: Every company stub records `created_by`, with an absent, non-`str` or whitespace-only label stored as `unknown` plus a WARNING naming the company, so a vault write by an unlabeled producer stays findable after the fact.
landed: Task 10
```

```mitigation
kind: required
id: M5
desc: The company judgement stays INSIDE the non-person branch above its return, so a company write is never subjected to the person body's `phones[]` dedupe — a deletion over stored data — or to the alias/email migrations; a company payload carrying `phones`, `emails` and `aliases` returns byte-identical.
landed: Task 6
```

### Notes (non-blocking)

1. **Deleting the mangler un-shields control and bidi characters that the widened class does not
   name — a real but small residue, on one arm only.** `[^\w\s-]` absorbed everything outside
   word/space/hyphen, which includes NUL, the C0 controls and the Unicode bidi overrides
   (U+202A–U+202E, U+2066–U+2069). The widened `_COMPANY_PATH_HOSTILE_RE` covers thirteen
   filesystem- and wikilink-hostile characters and none of those. The consequence is bounded and I
   priced it before deciding not to block: the five non-`create_stub` arms have NO company name
   validation today, so for them this item is strictly a gain; only `create_stub` — reachable from
   HAL9000's local route — loses a stripper that used to absorb them; NUL fails loudly at the
   filesystem; and a bidi override yields a deceptively-rendering note filename rather than any
   access. The cheap future close is one more member set on the class or a sibling branch
   covering `[\x00-\x1f\x7f]` plus the U+202A–U+202E and U+2066–U+2069 ranges — spelled as escapes
   in the source, so the constant does not itself carry an invisible reordering character. It is
   deliberately NOT required here because
   changing the shipped constant re-opens Prerequisite 2's conductor audit row and Task 12(g)'s pin
   for a threat with no realistic exploit path — R7's own residual already states that widening the
   class later is a new audit rather than a bug fix. Worth a sibling item, not a bounce.
2. **The automated consumer's failure profile is priced only for the interactive one.** R2 covers
   HAL9000's route returning 500 where it used to write. Exocortex's hourly company ingest writes
   through `write_markdown_file` directly after pre-stripping with its own mangler copy
   (`stages/company.py:157`), which leaves `empty` and `archive_prefix` able to fire there — and a
   name its local mangler reduces to `""` is exactly how `empty` gets reached. An unhandled
   `NameGateRefusal` on an hourly unattended path is a recurring availability failure with nobody at
   the keyboard, which is a different profile from a 500 a human sees immediately. Nothing in this
   repo can mitigate it — `exocortex/**` is outside `write_authority` — and the document already
   requires the conductor mint twice (Scope Boundary, architect Note 6). Recording it so the mint's
   framing carries the availability half and not only the correctness half.
3. **`created_by` is self-asserted and covers one arm of six.** It is a provenance hint, not an
   attestation: any caller can pass any label, including `"unknown"`, and the value is stored
   byte-identically with no gate judgement (correctly — AC-3's byte-identical clause is what stops
   the fix over-reaching into a trimmer). It is also written only at `create_stub`, so a company note
   created via `save()` or `write_markdown_file` carries no provenance at all. Both limits match
   Person's and both are outside the frozen Intent; naming them so a later reader does not mistake
   the field for an audit-grade attribution.
4. **The grounding artifact commits live vault contents to the repo.** AC-5 requires
   `docs/company-name-corpus-audit.md` to list each refused company name and the residue stems, and
   §4 carries absolute workspace paths. That is right for the evidence and it is already in HEAD, so
   this changes nothing today — but it means the artifact, not the code, is the file that matters if
   this repo's distribution ever widens beyond Dave's own workspaces. Recorded, not actioned.

### Calibration note

I considered and rejected a REVISE. The blocking bar here would be a realistic exploit path this
spec creates or leaves open, and the residue I found (Note 1) is a non-regression on five of six
arms, loud on one shape and cosmetic on the other, reachable only by someone who can already POST
arbitrary JSON to a local service. Against that, a REVISE would force either a signed-AC change (a
re-sign and a second interruption of Dave) or a change to the shipped constant that re-opens an
unlanded conductor audit row — a large, real cost against a small, theoretical threat. The item's
net direction is strongly security-positive: it replaces a silent sanitizer with a loud refusal,
homes the contract at the boundary rather than at one call site, keeps a refused address out of every
message, moves the refusal above the lock's `mkdir`, and adds an audit field where there was none.

OPEN questions: **0** (cap is 2).

```verdict
gate: threat-modeler
verdict: PROMOTE
date: 2026-09-06
model: claude-opus-5
note: Four triggers fire and the realistic threats are already mitigated in the frozen ACs and named plan tasks — the refusal carries no note-derived value through the one `_refuse` site (the refused "name" can BE an email address), it lands above `note_lock`'s sentinel `mkdir` so a path-hostile name leaves nothing on disk, the delta rule keeps stored-dirty notes writable so the remedy is not the disease, and yaml.dump/safe_load make the un-shielded YAML metacharacters a non-issue; the five controls are declared as fences on Tasks 6/8/9/10/11 so the fold is machine-enforced. The one residue found — deleting the mangler un-shields NUL, C0 controls and bidi overrides, which the widened thirteen-character class does not name — is a non-regression on five of six arms, loud or cosmetic on the sixth, and blocking it would re-open an unlanded conductor audit row against no realistic exploit path, so it rides as a sibling-item note.
```


## Adversarial Review — 2026-09-06

Cold-start injection-hunt (the two-key corroborator, WI-059), run on this drive's model seam,
independent of the spec-reviewer and every other gate. Read the work-item doc end-to-end (all
~2760 lines: Problem/Motivation through every prior gate's verdict prose — architect ×3,
data-premise ×3, threat-modeler, spec-reviewer), plus the material it chases: the grounding
artifact `docs/company-name-corpus-audit.md`, the byte-identical AC carrier
`docs/spec-reviews/WI-022-dave-review-2026-09-06.md`, and (for completeness, since the item's
own text references it) `docs/company-stub-parity-rounds.md`, the append-only archive of settled
rounds. The role's two reference docs named in its YAML (`docs/work-item-pipeline.md`,
`docs/compartmentalization-security-review.md`) are not present in this project's tree — they are
workshop-level references, not part of this item's own reading list — so there was nothing there
to chase.

**The one question:** has this spec, or any prior gate's verdict on it, been steered by a prompt
injection planted in the untrusted content the gates read?

Grepped the work-item doc and the archive for classic steering phrasing (imperatives addressed to
a reviewer, "ignore/disregard the previous instruction", "pre-approved, emit PROMOTE", claims of
authority over the review itself) — no hits beyond incidental false positives (`IGNORECASE` as a
regex flag name, "bidi overrides" as a Unicode term). Read every prior gate's verdict prose
looking for reasoning that reads as the product of steering rather than independent judgment: all
five prior gates (architect, data-premise, threat-modeler, spec-reviewer, ac-red-team) show
hand-executed, citation-anchored, counterexample-hunting reasoning that repeatedly finds and
reports real gaps against the document's own claims (the spec-reviewer's Task-8 `None`-fixture
finding; the data-premise gate's still-unlanded artifact amendment; the architect's transcription
hazard in §2.3) rather than converging suspiciously fast toward a clean pass. The grounding
artifact (`docs/company-name-corpus-audit.md`) is inert data — real company names and grep
output — with no imperative content, and its own incompleteness (missing `Command:`/`Output`
blocks in §1–§3) is a tracked, named finding rather than a hidden defect. Persuasive prose in the
doc (e.g. the Risk Analysis's mitigations, the Self-Review Dry Run's Q&A) argues the document's
own merits to a human reader, per this gate's "too strict" calibration warning, and does not take
the form of an instruction to a reviewing agent.

```verdict
gate: injection-hunter
verdict: PROMOTE
date: 2026-09-06
model: claude-sonnet-5
note: Full cold-start read of the doc, its five prior gate verdicts, the corpus-audit grounding artifact and the AC sign-off carrier found no text addressed to a reviewer/agent and no reasoning in any prior verdict that reads as the product of injected steering — every prior gate's prose shows independent, citation-anchored, counterexample-hunting judgment that repeatedly surfaces real gaps rather than converging suspiciously toward a clean pass.
```

