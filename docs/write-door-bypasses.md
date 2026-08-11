---
id: WI-021
title: "Close the write-door bypasses: name validation + address normalization on every mutation path"
project: obsidian-schemas
stage: exploring
created: 2026-07-05
last_touched: 2026-08-11
stage_changed: 2026-08-11
touched_by: session
tags: [typed-boundaries, name-validation, rfc2822]
depends_on: ["WI-004"]
round_budget: 16
transitions: ["idea>exploring@2026-08-11@session"]
---

# Close the write-door bypasses

> **Model routing** (2026-07-05 campaign, `docs/backlog-campaign-2026-07-05.md`; self-sufficient):
> - **Explore: —. Spec: Opus / medium. Spec-review: Opus / medium. Build: Opus / medium** — boundary machinery, but the boundaries themselves (NameValidator, `_normalize_address_fields`) already exist and are tested; this is routing every door through them.
> - Sequencing: Phase 2, **after WI-004** — the consolidated write primitive WI-004 ships is the natural single place to hang these checks (solve-in-one-place; don't bolt them onto six doors that WI-004 is about to collapse).

## Problem / Motivation

WI-105/WI-109 built real boundaries, but they only guard the create path (2026-07-05 review, findings N2/N3):

- **N2 — NameValidator is create-only.** `NameValidator().clean` runs only inside `create_stub` (person.py:1371-1379). A direct `repo.save(person)` or `update_fields(person, {"name": ...})` (which auto-manipulates name/aliases, base.py:260-265) writes an arbitrary or renamed name with no Tier-1 validation and no path-hostile `/` check — exactly the inputs WI-105 rejects, entering through the non-create doors.
- **N3 — RFC 2822 normalization bypassed on identifier write-back.** `_normalize_address_fields` runs only in `PersonRepository.save()` (person.py:1239); `_writeback_identifier` (person.py:1176-1188) appends raw email/phone strings via `update_fields`, which doesn't normalize — so `Name <email>` can land unnormalized in `emails[]`, breaking exact-email dedupe (the WI-109 corruption, back through a side door).
- **Consolidation rider:** RFC 2822 parsing now lives in ≥4 sites (`create_stub` parseaddr person.py:1352, `_normalize_address_fields` person.py:1257-1263, `identifier.Email.parse` identifier.py:145-160, `name_validation._RFC2822_LEAK_RE`). Collapse to one authority.

## Intent

There is no door into the vault through which an unvalidated name or unnormalized address can pass. One RFC 2822 parse authority; an invariant test per closed door.

## Currency note — 2026-08-11 (queue review)

Premise re-verified against the post-WI-004 tree: still live. `_writeback_identifier` (now
person.py:1192) still appends raw identifiers via `update_fields`; `_normalize_address_fields`
(now :1278, called from save at :1269) still runs only in `PersonRepository.save()`;
NameValidator still fires only on the create path. Line numbers above have drifted — re-derive
at spec time, don't trust the 07-05 citations. Relationship to WI-004: vault_io closed the
MECHANICAL write door (atomicity/locking/stamps); this item is the SEMANTIC layer on the same
door — validation and normalization on every path that reaches it. Deps satisfied (WI-004 done
2026-08-11); unblocked.

## Exploration Notes

**Run 2026-08-11, ideation-partner, `approval-only` mode** (no `involvement:` flag). The approach
below is re-derived from the frozen `## Intent`, not inherited from the mint: per the WI-185 read
protocol the mechanism the 07-05 campaign named — *"hang these checks on the consolidated write
primitive WI-004 ships"* — was treated as the first hypothesis to test, and it does not survive
(Finding A). Every line citation below was re-derived against the tree as it stands today; the
07-05 citations in `## Problem / Motivation` have drifted and are kept only as the historical record.

`## Intent` is left **unedited** and stands as the frozen anchor. One deliberate reading note for
the spec-writer and for D4a: its middle clause, *"One RFC 2822 parse authority"*, is sound as
INTENT — no second authority for one job — but is false if read as a count. Finding D shows the four
cited sites doing three different jobs, of which only two are duplicates. Sharpening the anchor to
say so would drift it after the fact; recording the correction here is the honest alternative.

### The premise audit — every path a name or an address can reach vault bytes through

The data premise (WI-147) first, because the whole shape of the item turns on it. Two classes of
write exist, and only one of them is a door for this item.

**Class 1 — the doors.** Every site that builds frontmatter from a typed entity or a field dict and
serializes it into vault bytes:

| # | Door | Name validated today? | Address normalized today? |
|---|---|---|---|
| D1 | `writer.write_markdown_file` (writer.py:159) — public API, documented in README.md:196; **three fm-building arms**, not two — `entity=` (:256-257), `frontmatter=` (:258-261) and the `else` arm that serializes `extra_fields` alone (:262-263). Broken out below as D1a/D1b/D1c | no | no |
| D2 | `BaseRepository.save` (base.py:356) → D1; derives the FILENAME from `entity.name` at base.py:381. **NOT an arm** — see the membership note below | no | no |
| D3 | `PersonRepository.save` (person.py:1255) → D2. **NOT an arm**; carries the entity write-back RIDER | no | **yes** — `_normalize_address_fields` at :1269 |
| D4 | `BaseRepository.update_fields` (base.py:403) — arbitrary `updates` dict, and it auto-appends the old file stem to `aliases` on a name change (:443-448) | no | no |
| D5 | `writer.update_frontmatter_field` (writer.py:292) — public, no repository involved | no | no |
| D6 | `writer.update_frontmatter_fields` (writer.py:350) — public | no | no |
| D7 | `writer.roundtrip_file` (writer.py:402) — re-serializes an existing note's own frontmatter | no | no |
| D8 | `scripts/lint_vault.py` `--fix` (lint_vault.py:876-882) — builds `fm`, serializes, calls `vault_io.write_note` directly | no | no |

Only `create_stub` (person.py:1345) carries the name contract, at :1407, and only `PersonRepository.save`
carries the address contract. Every other door is open. `_writeback_identifier` (person.py:1192)
reaches D4 with a raw string at :1217 — N3, confirmed live.

> **Membership correction, 2026-08-11 (fold, round 7), answering the round-5..6 architectural
> review's round-6 blocking issue.** The table above is the premise audit — *every path a name or an
> address can reach vault bytes through* — and it is unchanged and still right as that. It is NOT the
> derived ARM set, and D2/D3 are exactly where those two objects come apart: read from source,
> `BaseRepository.save` (`base.py:356-401`) binds no frontmatter dict — it computes
> `filename = f"@{name}.md"` (`:381`) and passes `entity=`/`extra_fields=` straight through to
> `write_markdown_file` (`:387-395`) — and `PersonRepository.save` (`person.py:1255-1275`) binds
> nothing at all, calling `_normalize_address_fields(entity)` (`:1269`) then `super().save(...)`
> (`:1272`). Both re-derived this round. Under `AC-1`'s own unit (*"one member per distinct binding of
> the dict a function serializes"*) neither is an arm — which is the identical test this document
> already applies the other way to `BookRepository.save` (`book.py:167-178`) and
> `MeetingRepository.save` (`meeting.py:189-200`), read side by side this round and differing from
> `base.py:381-395` in **exactly one expression**, the filename derivation
> (`self._get_file_name(entity)` vs `f"@{name}.md"`). The set is corrected below to the eight arms one
> stated predicate resolves, and D3 keeps ONE gate call as a **rider** rather than as an arm. Nothing
> behavioural is lost: every byte either `save` produces reaches the seam through D1a one frame later.

**Class 2 — the pass-throughs, which are NOT doors.** `append_to_timeline` (person.py:1582, :1593)
writes reconstructed whole-file content with the frontmatter untouched; the four body-section /
To-Discuss writers (person.py:1693, :1813, :1892, :1962) re-emit the fence as the VERBATIM string
they read; `lint_vault`'s wikilink substitution (lint_vault.py:884-900) is a string replacement on
content. None of them can introduce a name or an address. That is load-bearing rather than
incidental: it is what makes Finding C's delta rule implementable at all, because it means a note
carrying a legacy-dirty name is already writable by every body path without any exemption.

### Finding A — the mint's named mechanism does not survive

`vault_io`'s doors take `(path, text)`. By the time bytes arrive there the typed entity and the
field dict are both gone — `write_note` sees a string, and `_commit` sees `bytes`. Hanging a name
check on the WI-004 primitive therefore means re-parsing the markdown back into a frontmatter dict
inside the write door and guessing whether the result is a person note: reconstructing at write
time exactly the structure the caller discarded one stack frame earlier. That is the WI-185 shape
the ideation protocol exists to catch. The right question is *where does the structure actually
live* — and the answer is one frame up.

This is also why WI-004's own routing wall is the wrong instrument to copy wholesale. WI-004 could
make its door unavoidable because it owns a CAPABILITY (only `vault_io.py` may name a filesystem
mutation, `tests/derivations.py:686`). Semantics are not a capability; there is nothing for the
kernel or the import graph to enforce. The enforcement here has to be a derived wall over source,
which WI-004 also already built and which this item reuses (Approach F).

### Finding B — the seam is `write_frontmatter`, and the gate is HANDED its type there

> **Rewritten 2026-08-11 (spec-writer fold, round 4) to Dave's DECLARE ruling** — see
> `## Conductor Rulings & Grounding`, rulings 1 and 2, and the counts recorded there. The superseded
> text read `@*.md` as a person naming convention and adopted `BaseRepository._owns`'s glob fallback
> as the gate's dispatch rule ("absence of `type:` never exempts a write from the gate"). Three
> architectural rounds and three data-premise rounds found that wrong on facts: `CompanyRepository`
> overrides neither `file_pattern` nor `save`, so `_owns(None)` is True for it too and the rule
> annexed an entity class this item scopes out to WI-022. Per the ruling it is **DELETED, not
> repaired** — `_owns` is not consulted anywhere in this design, and the citation survives below only
> as the thing this item explicitly does NOT do. The arm table was unchanged by that round; only the
> dispatch rule moved. *(The door SET has since moved once — round-7 fold, from ten arms to the eight
> a single stated predicate resolves. See the membership correction below.)*

Every one of D1–D8 reaches `writer.write_frontmatter` (writer.py:133) immediately before the bytes
exist, through exactly six call sites: writer.py:266, :335, :387, :421, base.py:454,
lint_vault.py:880. *(Round-7 fold, and this is the corroboration rather than a caveat: those six
sites are precisely the six functions the corrected eight-arm set spans. D2 and D3 appear in neither
list — they reach the seam only transitively, through D1a, which is the same fact the membership
correction below turns on.)* There are exactly six
`f"---\n{yaml}---\n"` constructions in the package and scripts, and all six are fed by that call.
Below it every value is a string; above it the field NAMES are still present. That is the last
point at which "this value is a `name`" and "this value is an `emails[]` entry" are decidable, and
therefore the seam this item is about.

**The dispatch rule, in one sentence** (Dave's ruling 1, adopting the round-3 architectural ruling
verbatim):

> The gate reads only what the write itself carries, plus what the caller declares. It never
> consults the filesystem — no glob, no path shape, no sibling note. A write with no declared type
> gets no type's contract.

The line is between the PAYLOAD and the ENVIRONMENT, not between code and inference. Reading a field
out of the record being written is mechanical and stays in the gate; reconstructing the entity type
from where the file happens to sit is the same WI-185 move Finding A already used to reject
`vault_io` as the gate's home, one frame further up.

**Six of the eight arms already carry a declaration, and no caller changes** *(re-counted 2026-08-11,
round-7 fold, to the corrected arm set; the D2/D3 row becomes the D3 rider's row and nothing else in
the table moved)*. Every row re-derived from source this round rather than inherited:

| Arm | The declaration available AT that arm | Read from |
|---|---|---|
| D1a `entity=` | the model — `Person.type` is `Literal["person"] = "person"`, and the projection emits every declared field unconditionally | `models.py:78`; `writer.py:model_to_frontmatter:111` |
| *(the D3 rider — not an arm)* | `self.type_name` — an `@abstractmethod` property on the base, so every repository supplies one | `base.py:type_name:188-192`; `person.py:232`, `company.py:type_name:67` |
| D4 `update_fields` | `self.type_name`, the same object, already used at `:430` and `:461` | `base.py:update_fields:403-461` |
| D5 / D6 `update_frontmatter_field(s)` | the target note's own `type:`, already parsed in-lock one line before the mutation | `writer.py:329`; `writer.py:381` |
| D7 `roundtrip_file` | n/a — introduces nothing, out under the delta rule (Finding C) | `writer.py:roundtrip_file:419` |
| D8 `lint_vault --fix` | the note's own `type:` — `fm.get("type")` off the in-lock parse at `:821` *(round-10 correction: this row read `vf.entity_type`; `apply_fixes` is handed `issues`, `vault_path` and `idx` (`:804-805`) and never the walk's `VaultFile`, so the value `read_vault` records at `:140` is the same string in a frame this one cannot reach)* | `lint_vault.py:apply_fixes:819-821`; the equivalent walk-side value at `:140`, `:148`, field declared at `:93` |
| D1b `frontmatter=` | the caller's dict — declared iff it carries `type:` | `writer.py:259` |
| D1c `extra_fields`-only | the caller's dict — declared iff it carries `type:` | `writer.py:263` |

**At D1b the declaration is read from the POST-merge dict, not from the parameter** (new 2026-08-11,
round-5 fold, answering architect round-4 note 4). The table row above cites `writer.py:259`
(`fm = frontmatter.copy()`) as D1b's source, but `extra_fields` overrides it one line later
(`:260-261`), so `write_markdown_file(path, frontmatter={"name": …}, extra_fields={"type": "person"})`
IS a declared write and must not be refused under rule (ii). The citation names where the arm's dict
is *bound*; the gate must read `fm` as it stands at the convergence point (`:266`). Stated explicitly
so the build does not read the citation as the instruction — it is the one place in the arm table
where the two come apart.

**So the undeclared cell is small and nameable**: D1b and D1c called without a `type:` key, and D5/D6
against a note that itself carries none. Everything six gate rounds fought over lives in that one
cell. The Company annexation cannot occur under this rule — a company write declares `company`, via
`CompanyRepository.type_name` (company.py:67) or via its own `type:` key, and simply is not a person
write. Parked defect 3's Person-only scoping now holds by construction rather than by an argument
that has to be re-made at every arm.

**D8 is NOT in the undeclared cell, and that is decidable from source rather than from the vault —
new this round.** `lint_vault` classifies an `@`-prefixed note that has frontmatter but no `type:`
as `missing_type`, `Severity.ERROR` (lint_vault.py:318-325), and then `continue`s (`:326`) before any
other check runs. `LintIssue.auto_fixable` defaults to `False` (`:83`) and the `missing_type`
construction does not set it, while `apply_fixes` collects only `if issue.auto_fixable` (`:810`). So
an undeclared note yields exactly one non-auto-fixable ERROR and never reaches the whole-`fm`
serialization at `:876-882`. **The D8 arm cannot serialize an undeclared note at all.** That
discharges re-entry step 3's "check the rewrite against member 9": the gate at D8 is handed the note's
own `type:`, read as `fm.get("type")` off the in-lock parse at `:821` — the same string this module
already dispatches on at eleven sites through `vf.entity_type` (`:186`, `:188`, `:190`, `:374`, `:423`,
`:458`, `:472`, `:490`, `:548`, `:673`, `:688`), so the module carries ONE dispatch implementation
instead of the three the superseded design was about to create. *(Round-10 correction: this paragraph
named `vf.entity_type` as the value handed to the gate. `apply_fixes` never holds a `VaultFile` — it is
passed `issues`, `vault_path` and `idx` (`:804-805`) and reaches into `idx` for `meetings` alone
(`:813`) — so the in-frame source is `fm`. The dispatch-count argument is unchanged: it is the same
value by a different binding.)*

**The same reading corroborates ruling 2 from the tree.** `missing_type` being an ERROR is this
codebase's own already-shipped answer to "is an untyped `@*.md` note a legitimate record": no — it is
a defect to be repaired. Refusing an undeclared write that introduces a `name:` agrees with a
position this repository already holds; it does not invent one.

**Rule (ii) — refuse. Dave's ruling 2:** an undeclared write that introduces a `name:` is refused
outright. The alternative (i) — apply only the structurally justified checks and withhold the
person-tuned ones — was rejected as the weaker rule with the larger unmeasured surface.

> **Re-scoped 2026-08-11 (fold, round 5), answering the round-4 data audit's Finding 1 and the
> round-4 architectural review's note 3.** The superseded text stated rule (ii)'s justification as an
> absolute — *"the live undeclared population is **0 of 3,418**"* — and that is a number measured over
> a PROPER SUBSET of the rule's own surface. Count 1's method is `rglob("@*.md")`
> (`## Conductor Rulings & Grounding`), but rule (ii) is not path-scoped: re-read from source this
> round, `update_frontmatter_field(file_path, field_name, field_value)` (`writer.py:292-296`) and
> `update_frontmatter_fields(file_path, updates)` (`writer.py:350-353`) both take
> `file_path: Union[str, Path]` with no glob constraint and parse whatever frontmatter that note
> carries (`writer.py:329`, `:381`), and D1b/D1c likewise take any path with a caller-supplied dict
> (`writer.py:258-263`). The count is real and correctly run; it answers a narrower question than the
> rule asks. The gate owns that call and it is right — so the rule is restated below with the
> predicate that bounds it, and the number is booked as OWED at that scope rather than borrowed from
> the narrower one.

**The surface, stated as the rule states itself.** Rule (ii) fires on a write that (a) reaches one of
the four arms where the undeclared case is CONSTRUCTIBLE — D1b, D1c (the caller's dict carries no
`type:`) and D5, D6 (the note on disk carries none) — and (b) INTRODUCES a `name:` key. It is
indifferent to where the file sits. `update_fields` carries `self.type_name` unconditionally
(`base.py:188-192`, `:430`, `:461`) and D8 cannot reach an undeclared note at all
(`lint_vault.py:318-326`, `:83`, `:810`), so neither is on this surface.

**Two undeclared shapes, and the rule does not distinguish them.** The conductor's own note records
three `@*.md` files with **no frontmatter fence at all**, discounted as archive residue under
`_merged_dupes/`. Under rule (ii) a no-frontmatter note is an undeclared note exactly as an
untyped-frontmatter one is — "no declared type" is one condition with two shapes, and the discount is
invisible in the stated 0. Recorded here so the re-grounding predicate carries the judgement instead
of inheriting it silently. (At D5/D6 a no-frontmatter note raises `FrontmatterParseError` at
`writer.py:329`/`:381` before the gate is reached, so in practice the (c) shape is live only at
D1b/D1c, where the caller supplies the dict and the file may not exist yet.)

**The re-grounding predicate, in re-runnable form** — this replaces "0 of 3,418" as the thing
build-start re-grounding tests, per data-audit item 4, whose whole purpose is that the number a rule
is chosen against be the number that bounds it:

> Over **every** `.md` file in the vault (not `rglob("@*.md")`), classify each as
> **(a)** has frontmatter carrying a `type:` key → declared, out of scope; **(b)** has frontmatter,
> no `type:` key → undeclared; **(c)** no frontmatter fence at all → undeclared. Report `|b|` and
> `|c|` **separately**, each split by path class: under `@*.md`, under an archive directory
> (`_merged_dupes/`, `_quarantine/`), or neither.

**What that number can and cannot change, so the owed query is not over-read.** Rule (ii) is
fail-closed, so a larger undeclared population makes the rule stricter, never wronger — what the
number sizes is BLAST RADIUS, not correctness, and the direction is Dave's call already made
(ruling 2). What it feeds is the consumer audit already owed under Constraints: the population of
live *writes* rule (ii) starts refusing is not enumerable from the vault at all, because it is
consumers of `update_frontmatter_fields`/`write_markdown_file` in HAL9000, exocortex and orchestrator
sending a `name:` into an untyped note. The vault query bounds the target set; the consumer grep
bounds the callers. **Both are owed and neither is run** — see `## Grounding Still Owed`. What has
NOT changed is that the `@*.md` half of the target set is measured and is zero, which is why ruling 2
is very likely right on the wider population too.

**Choosing (ii) dissolves the round-3 data-premise finding rather than answering it.** That finding
is scoped to shape (i): under (i) the structural subset (`path_hostile_char`, `empty`) would fire on
undeclared writes carrying only person-scoped evidence — `_PATH_HOSTILE_RE`'s "Verified 2026-06-06: 0
live vault names contain '/'" (name_validation.py:94) measured over the 1590 person names of the
module docstring's audit (`:26-28`). Under (ii) **no Tier-1 pattern evaluates an undeclared write at
all**: the write is refused before any pattern runs, so no person-derived number is carried across an
entity boundary. The entity-agnostic/person-specific partition both reviewing gates asked for is
therefore moot under the chosen rule, and with it data-audit item 5′. That is offered to the
data-premise gate to re-rule on, not declared discharged over it.

**One residue this rule deliberately leaves open, named so it is not read as an oversight.**
`CompanyRepository.save(Company(name="Bausch/Lomb"))` reaches `filename = f"@{name}.md"`
(base.py:381, inherited — there is no `save` override in `company.py`) and then
`vault_io.ensure_dir`, so it still creates a spurious `@Bausch/` directory. Finding F's defect is
entity-agnostic; this item's fix is Person-only by parked defect 3, so the company half stays with
WI-022. Under DECLARE that is a scope boundary rather than a gap — a company write declares
`company`, and this item's gate does not judge it.

**What each arm PASSES is as load-bearing as which arms CALL.** The declare shape creates a surface
the infer shape did not have: an arm can route through the gate and hand it the wrong thing. The
concrete bypass is at D4 and it is this item's own Example of done —
`update_fields(person, {"name": "Dave/Bob"})` passes a delta carrying no `type:` key (base.py:403-451:
`updates` is the caller's dict, merged into the parsed note only at `:451`), because the declaration
lives on the repository as `self.type_name`, not in the introduced fields. A gate that falls back to
reading the type out of the payload would put EVERY `update_fields` write into the undeclared cell
permanently and, under rule (ii), refuse every name change through the exact door N2 was raised
about. So the routing wall must pin, per arm, that the declaration passed is the one this section's
table names for that arm, and that no arm hardcodes a literal. Same instrument, one argument wider.
This is a re-origination obligation on `AC-1`; it is written up in `## Re-origination Brief`.

**The unit of the door set is the write ARM, not the function.** A function that builds its
frontmatter dict in more than one branch is more than one door, because a gate call inserted in one
branch is not in the other — and a wall that proves only "this function calls the gate somewhere in
its body" cannot tell the two apart. `write_markdown_file` is the one such function in the tree, and
it has THREE fm-building branches, not the two its two keyword parameters suggest (writer.py:255-263):

| Arm | Branch | What supplies the fields | Shape |
|---|---|---|---|
| D1a | `if entity is not None:` → `fm = model_to_frontmatter(entity, extra_fields)` (writer.py:256-257) | the typed model. `extra_fields` can only ADD keys the model lacks — the merge is guarded, `if key not in result` (writer.py:127) — so it cannot override `name` or `emails` here | entity-shaped |
| D1b | `elif frontmatter is not None:` → `fm = frontmatter.copy()`, then `fm.update(extra_fields)` (writer.py:258-261) | a caller-supplied dict, with `extra_fields` OVERRIDING it — a bare `update`, not the guarded merge above | dict-shaped |
| D1c | `else: fm = extra_fields or {}` (writer.py:262-263) | `extra_fields` alone, as the WHOLE record | dict-shaped |

All three converge on one `write_frontmatter(fm)` at :266. That convergence point is the natural home
for a single gate call reaching every arm — but validating just after each branch is at least as
natural to write, because D1a is the branch holding a typed `Person` whose attributes a name check
wants to read, and a gate placed there leaves D1b and D1c ungated while the function still "calls the
gate". D1c is not a curiosity either: `write_markdown_file(path, extra_fields={"type": "person",
"name": "Dave/Bob"})` is a legal call on a documented public function (README.md:196) that reaches
vault bytes carrying a caller-supplied name and never touches a model.

Every other door binds the dict it serializes exactly once: `update_fields` (base.py:439 → :454),
`update_frontmatter_field` (writer.py:329/:332 → :335), `update_frontmatter_fields`
(writer.py:381/:384 → :387), `roundtrip_file` (writer.py:419 → :421), and `lint_vault --fix`
(lint_vault.py:876-882).

#### The two `save` methods bind NOTHING, so the set is eight arms across six functions (2026-08-11, round-7 fold)

> Answering the round-6 architectural review's blocking issue, and the round-6 data audit's
> confirmation of it. Its reading is correct, it re-derives from source below, and this fold takes the
> shape the review said it would take — **(b): D2 leaves the set entirely and D3 becomes a rider.**
> Only membership moves; every behaviour this item promises is unchanged, and the reason is given
> below rather than asserted.

`AC-1`'s unit is *"one member per distinct binding of the dict a function serializes, so a function
with N such branches contributes N members — never the function."* Applied to the two `save` methods,
re-read from source this round:

| Site | What it binds | What it serializes | Arm? |
|---|---|---|---|
| `BaseRepository.save` (`base.py:356-401`) | a FILENAME — `filename = f"@{name}.md"` (`:381`) | nothing; `entity=` and `extra_fields=` are passed through to `write_markdown_file` (`:387-395`) | **no** |
| `PersonRepository.save` (`person.py:1255-1275`) | nothing — `_normalize_address_fields(entity)` (`:1269`), then `super().save(...)` (`:1272`) | nothing | **no** |
| `BookRepository.save` (`book.py:167-178`) | a filename — `self._get_file_name(entity)` (`:167`) | nothing (`:170-178`) | **no** — architect round-1 note 4, standing since |
| `MeetingRepository.save` (`meeting.py:189-200`) | a filename — `self._get_file_name(entity)` (`:189`) | nothing (`:192-200`) | **no** — same note |

Read side by side, the four differ in **exactly one expression** — the filename derivation. Everything
the arm predicate looks at is identical in all four. So the ten-arm set put two members and two
non-members on opposite sides of a boundary that does not separate them, and no single stated
predicate can resolve it: implementing the stated unit yields eight and leaves `AC-1(a)`'s floor red;
hand-listing the two saves is the vacuity hole ac-red-team round 1 spent a round closing; and widening
to "calls a write function with an entity" pulls `BookRepository.save`/`MeetingRepository.save` in, so
two non-person repositories acquire gate call sites and `AC-2`/`AC-4`'s equality-asserted exclusion
sets stop reconciling.

**The existing derivation vocabulary points the same way rather than rescuing it.**
`functions_reserializing_parsed_frontmatter` (`derivations.py:294-310`) is a parse→serialize data-flow
predicate whose docstring records that it *rejects* `write_markdown_file` precisely because that
function "builds what it writes from its own entity/frontmatter ARGUMENTS" (`:299-302`). Neither
`save` calls `parse_frontmatter` at all, so neither is reachable by that family either. The arm
predicate AC-1 needs is new (it is the one genuinely new piece of AST work in this item), but nothing
in the module's established vocabulary would resolve the two saves under any reading.

**So the derived set is eight arms across six functions** — D1a, D1b, D1c (`write_markdown_file`), D4
(`update_fields`), D5 (`update_frontmatter_field`), D6 (`update_frontmatter_fields`), D7
(`roundtrip_file`), D8 (`lint_vault --fix`) — and `AC-1`'s floor is restated in those terms. Because
AC-2 and AC-4 bind their coverage to that set, per-arm derivation is still what makes "a fixture
through the `entity=` arm specifically" a requirement neither of them has to hand-list, and what makes
a ninth arm added later join all three criteria automatically.

**What happens at D2 and D3 instead, stated exactly so the build does not read "not an arm" as "not
gated".**

- **D2 `BaseRepository.save` gets NO gate call.** It binds no dict, and every byte it produces reaches
  the seam through D1a one frame later, where the gate already fires on `model_to_frontmatter`'s
  projection of the same entity. A gate call here would be pure redundancy. Two legs make the removal
  safe, and **neither is the one this bullet used to give**:
  - on the ACCEPT-and-normalize path, the identity rule on the gate's name output — the FILENAME is
    bound from the raw `entity.name` at `base.py:381` and never revisited, and under (b′) the gate
    cannot make the field disagree with it. Derived in the round-8 subsection below.
  - on the REFUSAL path, the gate's PLACEMENT inside `write_markdown_file`: it runs above
    `vault_io.note_lock`, so the refusal precedes every filesystem-visible act on that path. Derived
    in the round-9 subsection below.

  > **Corrected 2026-08-11 (fold, round 9), answering the round-8 architectural review's blocking issue
  > and the round-8 data audit's confirmation of it — and the conductor's EXECUTION of the scenario
  > (`## Conductor Booking`).** The superseded refusal leg read: *"`vault_io.ensure_dir(file_path.parent)`
  > is at `writer.py:273`, DOWNSTREAM of the convergence point at `:266`, so a refusal raised at D1a
  > precedes the `mkdir` and no `@Dave/` directory is created."* That check reads `write_markdown_file`'s
  > own body and finds the one `ensure_dir` written in it. It is **false as a claim about the frame**:
  > `write_markdown_file` takes the note lock as its FIRST action (`writer.py:209`), and `note_lock`
  > `mkdir`s the lock sentinel's home (`vault_io.py:400`), which DEFAULTS to `target.parent`
  > (`vault_io.py:350`) — fifty-seven lines above the convergence point. Eight architectural rounds,
  > five red-team rounds, eight data audits and eight spec-writer rounds verified this promise by
  > READING, and the composition `write_markdown_file × note_lock` is exactly the shape no reader can
  > falsify (LESSONS #42). The conductor executed it: `repo.save(Person(name="Dave/Bob"))` leaves
  > `<vault>/@Dave/`, `<vault>/@Dave/.obsidian-schemas-locks/<digest>.lock` and `<vault>/@Dave/Bob.md`
  > on disk today. The D2 removal itself is UNAFFECTED — the round-6 membership ruling turns on what a
  > function BINDS — but the reason given for it being safe is replaced above, and the fix is a
  > placement rule rather than a re-instated arm.
- **D3 `PersonRepository.save` carries ONE gate call, as a RIDER and not as an arm.** Its reason is
  independent of routing and no other frame can supply it: `_normalize_address_fields` mutates the
  caller's `Person` in place today (`person.py:1317`, `:1343`), so after `repo.save(person)` the
  caller's own object is normalized. The gate returns a dict and does not touch the model, so `save`
  calls the gate on the model's projection and writes the normalized values back onto the entity
  before delegating to `super().save()` (Finding I's rider). It is **explicitly outside the derived
  set**, so the wall neither derives it nor requires it, and it is pinned by its own fixture instead —
  which is the re-origination obligation on `AC-1` recorded in `## Re-origination Brief`.

**And the gate still runs twice on one `PersonRepository.save`** — the D3 rider, then D1a — which is
why idempotency (`gate(gate(x)) == gate(x)`) remains required rather than becoming incidental. Dropping
D2 removes one of the three invocations, not the requirement.

#### The gate's NAME output is an IDENTITY, because the FILENAME is bound one frame above D1a (2026-08-11, round-8 fold)

> Answering the round-7 architectural review's blocking issue, and the round-7 data audit's sizing of
> it. The review's reading is correct, it re-derives from source below, and this fold takes the shape
> the review said it would take — **(b′): the gate refuses, or returns the name byte-for-byte.** The
> Tier-2 repairs stay a `create_stub`-only behaviour, above the write path, where they already live.

The subsection above removed D2 from the derived set on the argument that *"every byte either `save`
produces reaches the seam through D1a one frame later"*. That argument was verified against the
REFUSAL case *(and that verification was itself wrong on the frame — see the round-9 subsection below,
which repairs it with a placement rule; nothing in THIS subsection turns on it)*. It says nothing about
the ACCEPT-but-normalize case, and the object that breaks there is not a frontmatter byte at all.
Re-derived from source this round:

| Claim | Read from | Result |
|---|---|---|
| the FILENAME is bound from the RAW `entity.name`, one frame above every gate call in the design | `base.py:save:380-382` — `name = getattr(entity, "name", "Unknown")`, `filename = f"@{name}.md"`, `file_path = self.vault_path / filename` | confirmed |
| `save` never renames and never unlinks — the frame binds the path and writes to it | `base.py:380-401` — no `unlink`, no `rename`, no `replace` anywhere in the method | confirmed |
| `validate_strict` is NOT an identity on its success path — it strips AND collapses | `name_validation.py:validate_strict:257` (`stripped = name.strip()`), `:265-266` (`cleaned = _DOUBLE_SPACE_RE.sub(" ", stripped)`, returned); `_DOUBLE_SPACE_RE` is `\s{2,}` at `:118` | confirmed |
| `clean` applies the same two Tier-2 repairs and returns the repaired string | `name_validation.py:clean:283-286` (`strip_whitespace`), `:292-295` (`double_space_collapse`), returned at `:297` | confirmed |
| even the SENTINEL arms are not identities — both return `name.strip()` | `name_validation.py:253-254` (`validate_strict`), `:274-275` (`clean`) | confirmed — new this round, and it is why the rule below is stated over the gate's output rather than over one entry point |
| Tier 1 and Tier 2 are DISJOINT — `_raise_on_tier1` runs BETWEEN the two repairs, on the stripped form | `name_validation.py:288-290`, with the source comment saying why (*"Tier 1 checks run AFTER strip … Strip is non-destructive"*) | confirmed |
| `create_stub` cleans ABOVE the filename derivation, which is why WI-105 never produced this divergence | `person.py:create_stub:1405-1413` (`clean` at `:1407`, `name = clean_result.cleaned_name` at `:1413`), `clean_name` at `:1423`, `Person(name=clean_name)` at `:1453`, `self.save(person, …)` at `:1475` | confirmed |
| the in-memory CACHE is keyed on the raw name in the same frame | `base.py:398` (`_adopt(self._get_cache_key(entity), …)`), `base.py:_get_cache_key:308-310` (`getattr(entity, "name", "").lower()`) | confirmed |

**The concrete failure, and it is this item's own fix that introduces it.**
`repo.save(Person(name="Dave  Smith"))` — a double space; Tier-2 dirty, Tier-1 clean, refused by
nothing. `BaseRepository.save` binds `@Dave  Smith.md` from the raw name (`:381`); D1a fires the gate on
`model_to_frontmatter`'s projection; a gate that normalized would return `name: "Dave Smith"` and
`write_frontmatter` would serialize it (`writer.py:257`, `:266`). The note lands at `@Dave  Smith.md`
carrying `name: Dave Smith`, and the next `save()` of the reloaded entity computes `@Dave Smith.md` and
mints a **second note for one person** — parked defect 1's corruption class, arriving through `save`
instead of `update_fields`. Today the same call writes `name: Dave  Smith` into `@Dave  Smith.md`: no
door except `create_stub` touches a name, so path and field agree by construction.

**So the rule, stated once and over the gate's OUTPUT rather than over an entry point:**

> On the `name` field the gate is a PREDICATE, not a transform. It refuses, or it returns the name it
> was handed **byte-for-byte**. Tier-2 repair (`strip_whitespace`, `double_space_collapse`) is not a
> write-path behaviour and remains where it already lives — `create_stub`, above the filename
> derivation. "Normalized" in this design is **address-side only**.

**Why (b′) and not the two alternatives, stated so the choice is falsifiable.** The other two were
offered by the same review and both work; the reason to prefer this one is that it removes the coupling
instead of sequencing around it, and the data gate's sizing then makes the preference concrete rather
than aesthetic:

| Shape | What it does | Effect on a stored Tier-2-dirty note | Verdict |
|---|---|---|---|
| **(b′) identity** — refuse or return byte-for-byte | no arm can emit a name any path disagrees with, for any entity type, with no rider and no ordering premise | **nothing.** Path and field never disagree; the note keeps its stored name on every non-`create_stub` path | **CHOSEN** |
| (a′) the D3 rider writes the NAME back onto the entity before `base.py:381` binds the path | closes it for Person only, and by a repository override rather than by construction; widens the rider's reason from *"preserve today's in-place mutation"* to *"preserve an ORDERING"* | the first re-save writes a NEW file at the cleaned stem and **leaves the old one** — `save` has no `unlink` (`base.py:380-401`). One orphan per note, on the fix's own first run | rejected |
| (c′) re-instate a gate call above the filename derivation — the round-6 shape (a) | re-adds the arm the round-7 fold removed, and re-opens the membership problem the eight-arm predicate resolves | same as (a′), for the same reason | rejected |

Two further consequences of the choice, both checked from source and neither needing a number:

- **The repair tool stops being able to create the divergence.** `lint_vault --fix`'s
  `person_missing_name` branch derives the name FROM the path — `name = fpath.stem.lstrip("@")`,
  `fm["name"] = name` (`lint_vault.py:835-839`). Under (a′)/(c′) a Tier-2-dirty stem would be repaired
  into a `name:` that no longer matches the file it was just read off, with the repair tool performing
  the split. Under (b′) the repaired `name:` equals the stem byte-for-byte, or the write is refused.
- **The cache agrees with the note it just wrote.** `_adopt` keys on the raw `entity.name.lower()`
  (`base.py:398`, `:308-310`), one line after the write. Under (b′) that key and the serialized `name:`
  are the same string, so no refresh is needed to reconcile them.

**What the identity rule does NOT do, said plainly so it is not over-read.** It does not repair the
stored Tier-2-dirty names; it declines to. Those notes keep their names, exactly as today, on every path
except `create_stub`. Whether that population is large enough to deserve a sweep is a *different* work
item (parked defect 1's neighbourhood — a rename that moves the file), and the number that would size
both is query **G4** in `## Grounding Still Owed`, booked this round. Nothing in this item's scope turns
on it, which is the point: (b′) is the one shape whose correctness does not wait on a count.

#### The gate runs ABOVE `note_lock`, because the frame's first filesystem-visible act is the LOCK's own `mkdir` (2026-08-11, round-9 fold)

> Answering the round-8 architectural review's blocking issue and the round-8 data audit's confirmation
> of it, **to Dave's ruling** — `## Conductor Preconditions`, precondition 1: *"option (a) adopted — the
> gate runs ABOVE `note_lock`."* The shape was not this round's to choose; what this round owes is the
> derivation, the SCOPE (which arms move and which must not), and the two obligations the move creates.
> `AC-2`'s *"no stray directory is created"* clause therefore **stands as signed and is now meetable**.

**The frame, re-derived from source this round.** Every row read rather than inherited:

| Step | Read from | Result |
|---|---|---|
| `write_markdown_file` acquires the note lock as its FIRST action — before the stamp lookup, before the WI-126 guard, before any fm is built | `writer.py:204` (`file_path = Path(file_path)`), `:209` (`with vault_io.note_lock(file_path) as resolved:`); the three arms are at `:256-263`, the convergence at `:266` | confirmed |
| `note_lock` resolves NON-STRICTLY, so a path whose parent does not exist is accepted rather than refused | `vault_io.py:note_lock:376` (`target = _resolved(path)`), `vault_io.py:_resolved:234-239` — docstring: *"a not-yet-existing leaf resolves against its resolved parent"* | confirmed |
| on the OUTERMOST acquisition it derives a sentinel and `ensure_dir`s the sentinel's parent, before it yields | `vault_io.py:392-393` (`if not reentrant:`), `:398` (`sentinel = _sentinel_path(target)`), `:400` (`ensure_dir(sentinel.parent)`); the `yield` is at `:424` | confirmed |
| the sentinel's home **DEFAULTS to the note's own directory** | `vault_io.py:_sentinel_path:350` — `home = configured if configured is not None else target.parent / SENTINEL_DIR_NAME`; `SENTINEL_DIR_NAME = ".obsidian-schemas-locks"` at `vault_io.py:SENTINEL_DIR_NAME:58` | confirmed |
| `_configured_lock_dir()` returns `None` unless `OBSIDIAN_SCHEMAS_LOCK_DIR` is set to an ABSOLUTE path — its own first docstring line says *"or None for the default (the note's own directory)"* | `vault_io.py:_configured_lock_dir:137-152`, `default=None` at `:149` | confirmed — **the default is the live production case** |
| `ensure_dir` is `mkdir(parents=True, exist_ok=True)` and carries no compensating action | `vault_io.py:ensure_dir:618-638`, `mkdir` at `:634`, the ruling at `:621-624` (*"Carries NO precondition and NO lock … it is idempotent and has no loss mode"*) | confirmed — nothing in the package removes what it creates |
| a `.lock` FILE is then created inside that directory | `vault_io.py:410-414` (`filelock.FileLock(str(sentinel), …)`, `file_lock.acquire(...)` at `:414`) | confirmed |
| `BaseRepository.save` performs no filesystem act in its own frame — it binds the path and delegates | `base.py:380-382`, `:387-395`; no `mkdir`/`open`/`unlink`/`rename` anywhere in `:356-401` | confirmed |

**So the item's own headline scenario, end to end:** `repo.save(Person(name="Dave/Bob"))` →
`filename = "@Dave/Bob.md"` (`base.py:381`) → `write_markdown_file` → `note_lock` (`writer.py:209`) →
`_sentinel_path` yields `<vault>/@Dave/.obsidian-schemas-locks/<digest>.lock` → `ensure_dir`
(`vault_io.py:400`) runs `mkdir(parents=True)` and **creates `<vault>/@Dave/`**, plus the lock
subdirectory inside it and the `.lock` file at `:410-414`. Only then does control reach `:266`. A gate
at the convergence point refuses *after* the directory exists, the lock releases, and the directory
stays. **This is no longer a reading**: the conductor executed it against a throwaway tmp vault and
recorded the four artefacts on disk (`## Conductor Booking`).

**The rule, stated once and over PLACEMENT rather than over membership:**

> At `write_markdown_file`'s three arms the fm construction and the gate call are **hoisted above
> `vault_io.note_lock`**. The gate's refusal precedes every filesystem-visible act the frame performs —
> the lock sentinel's `mkdir` (`vault_io.py:400`), the `.lock` file (`:410-414`) and
> `ensure_dir(file_path.parent)` (`writer.py:273`) alike. `write_frontmatter(fm)` stays where it is, at
> the convergence point.

**Why the hoist is legal, and it is Dave's ruling 1 that makes it so.** Under DECLARE the gate is a
pure function of the payload plus the handed type — *"it never consults the filesystem: no glob, no
path shape, no sibling note"* — so nothing it reads is protected by the lock and nothing it decides can
change while the lock is held. That is not a convenience: a gate that consulted the filesystem would
have had to run INSIDE the lock to be sound, and option (a) would not have been available at all.
Ruling 1 and precondition 1 are the same decision seen twice.

**And the hoist is mechanically local.** Re-read from source: nothing between `writer.py:209` and
`:263` feeds the three arms. The stamp lookup (`:210`), the `unverified` flag (`:214-215`), `is_create`
(`:226`) and the WI-126 body read (`:236-239`) are all downstream CONSUMERS of the lock, not inputs to
`fm`; the arms read only `entity`, `frontmatter` and `extra_fields`, which are parameters. So the hoist
moves ten lines, changes no arm's identity, creates no fourth branch, and **leaves `AC-1`'s eight-arm
floor and its `(qualname, arm)` assertion exactly as they are** — the three bindings are still three
bindings of the dict one function serializes, and they still converge on one `write_frontmatter` call.

**The hoist is ARM-SPECIFIC, and saying so is what stops a build over-applying it.** Only an arm whose
frame can reach a path that does not exist can create a stray directory. Swept from source across the
whole derived set plus the rider — every cell read this round:

| Arm | Frame's FIRST filesystem-visible act | Can the frame reach a non-existent path? | Gate placement |
|---|---|---|---|
| D1a / D1b / D1c `write_markdown_file` | `note_lock` (`writer.py:209`) → `ensure_dir(sentinel.parent)` (`vault_io.py:400`) + `.lock` (`:410-414`); then `ensure_dir(file_path.parent)` (`writer.py:273`) | **YES** — no existence guard anywhere in the frame; the create case is its normal case | **ABOVE the lock** (the hoist) |
| D4 `update_fields` | `note_lock` (`base.py:437`) | no — `raise FileNotFoundError` at `base.py:432-433`, above the lock | **in-lock, unchanged** |
| D5 `update_frontmatter_field` | `note_lock` (`writer.py:327`) | no — `raise FileNotFoundError` at `writer.py:320-321` | **in-lock, unchanged** — and it must stay, because the declaration is the note's own `type:`, parsed at `:329` |
| D6 `update_frontmatter_fields` | `note_lock` (`writer.py:379`) | no — `raise FileNotFoundError` at `writer.py:374-375` | **in-lock, unchanged** — declaration parsed at `:381` |
| D7 `roundtrip_file` | `note_lock` (`writer.py:417`) | **yes** — there is no existence guard in this frame | **ABOVE, by the default** *(round-10 correction; the row read "no gate call at all", which contradicts `## Approach` and `AC-1`'s floor alike)* — D7 is a member and routes, on an EMPTY delta (Finding C), so the call can never refuse and the placement is free. Its unguarded lock is parked defect 4, unchanged |
| D8 `lint_vault --fix` | `note_lock` (`lint_vault.py:819`) | ~~no — `fpath` comes from the vault walk~~ **YES, today** *(round-10 correction)* — `fpath` is bound from a dict keyed on the `issues` PARAMETER (`:808-815`); the walk is `read_vault`'s `rglob` at `:111`, two frames away (`run_lint:1069`, `apply_fixes` called at `:1100-1103`), so nothing in this frame is evidence the target exists | **in-lock — and this item makes that DERIVABLE** by adding the sibling guard above `:819` (round-10 fold). `fm` is parsed at `:821`, and the declaration is that dict's own `type:`, not `vf.entity_type` — `apply_fixes` never holds the walk's `VaultFile` |
| the D3 rider `PersonRepository.save` | none in its own frame (`person.py:1269-1272` delegates) | n/a | above `super().save()`, hence above D1's frame already |

Two things follow that the build must not blur. **D5/D6/D8's gate calls must STAY inside the lock**:
that is where the dict they judge and the declaration they pass are read from the note, and hoisting
them would move the gate above the parse that supplies its type. And **D4's stays too** — it needs no
hoist (`base.py:432-433` guards it) and its delta is the caller's `updates`, read from a parameter, so
there is no reason to move it and one reason not to (a second placement rule for no gain).

**The obligation the hoist creates, and it is the same instrument one argument wider.** The derived
wall as specified proves an arm *calls* the gate somewhere in its body. *"The gate call precedes the
frame's first filesystem-visible act"* is a PLACEMENT fact, and nothing enforces it — a build that
hoists correctly today and a build that leaves the call at `:266` are indistinguishable to a wall that
only asks whether the call exists. So the wall's per-arm assertion widens from a pair to a triple:

> Per arm, the wall asserts **(the arm, the declaration it passes, the gate call's PLACEMENT)**, where
> placement is `above` (the gate call precedes the frame's first `vault_io` call of ANY kind (equivalently its `with vault_io.note_lock(...)` statement; corrected per architect round 14 — anchoring on the first MUTATION call let every arm compute `above`)) or `in-lock`.
> The required value is DERIVED, not listed: an arm whose frame refuses on the target's non-existence
> before its first such act ~~— or whose target is supplied by a walk of notes already read —~~ may be
> `in-lock`; **every other arm requires `above`, which is the default for an arm the predicate does not
> recognise.** A ninth arm added next month is therefore RED unless it is hoisted or is provably
> existence-guarded, rather than green by omission.
>
> *(Round-10 fold: the struck disjunct is DELETED — it was a property of a caller two frames away, and
> it left D8 required `above` by the default and `in-lock` by the sentence below. The rule now has one
> local leg, and D8 is made to satisfy it. Derivation in the round-10 subsection below.)*

This sits beside the round-3 pass-what pin, on the same derived set, and it is a re-origination
obligation on `AC-1` — recorded in `## Re-origination Brief`, not written into the signed fence here.

**And the fixture that proves it must run under the DEFAULT lock home, or it is a control with no
discriminating power.** With an absolute `OBSIDIAN_SCHEMAS_LOCK_DIR` configured, `_sentinel_path` puts
the sentinel outside the vault entirely (`vault_io.py:_sentinel_path:349-351`) and no `@Dave/` appears —
so a fixture that sets that variable passes against un-hoisted code while production fails. The `AC-2`
no-stray-directory fixture must therefore assert the variable is UNSET. Its oracle must be derived from
what the test itself holds — ~~**snapshot the vault root's full recursive listing immediately before the
refused call and assert it is unchanged afterwards**~~ — never "the vault root's only child is X", which
assumes a layout the test did not create (WI-149).

> **The struck sentence is WRONG and is replaced here** *(round-12 fold; architect round 11 blocking,
> sharpened by data-premise round 11, both re-derived from source below)*. Its justification was one
> sentence — *"under the hoist the refusal precedes `note_lock`, so even the lock home is not created and
> the comparison is exact"* — which is true of the `above` set and of **nothing else**. At D4/D5/D6/D8 the
> placement rule REQUIRES `in-lock`, so `note_lock`'s outermost acquisition has already run
> `ensure_dir(sentinel.parent)` (`vault_io.py:note_lock:398-400`, before the `yield` at `:424`) and
> created the `.lock` (`:407-414`) by the time the gate can speak, and `ensure_dir` carries no
> compensating action by its own ruling (`vault_io.py:ensure_dir:618-638`, ruling at `:621-624`). A whole
> listing is an AMBIENT artifact set: it forbids every artifact, including the ones this package's own
> locking layer is REQUIRED to create before the gate is reached. That is LESSONS #35 re-incurred inside
> the oracle written to discharge WI-149 — a negative assertion must name the exact artifact it forbids.
>
> **The replacement, which is what `### Examples of done` scenario 1 already says in Dave's own words**
> (*"the vault contains no new `@Dave/` directory and no `Bob.md` inside one"*): the oracle names the
> artifacts, each COMPUTED from a value the test holds. For `repo.save(Person(name="Dave/Bob"))` against
> a tmp vault the test holds the name and the vault root, so it asserts `<vault>/@Dave` does not exist
> (which subsumes the lock home and the note inside it) and `<vault>/@Dave.md` does not exist. For a
> direct `write_markdown_file(target, …)` the test holds `target`, so it asserts `target` does not exist,
> `target.parent` does not exist where the test did not create it, and
> `target.parent/".obsidian-schemas-locks"` does not exist. Three assertions, every path derived from one
> value the fixture passed in, no ambient set quantified over.

**Why the replacement is not merely a weaker oracle: at the arms it covers, the flip the ambient oracle
suffers CANNOT occur** *(round-12 fold)*. The ambient oracle's verdict depends on how the fixture planted
its note — plant through a package door and the identical sentinel digest is already in the *before*
snapshot (`_sentinel_path` hashes `str(_resolved(target))`, `vault_io.py:348` with `_resolved` at `:376`),
so the comparison is green; plant with `Path.write_text`, which `AC-2`'s Tier-1 sweep needs and which the
round-10/11 riders prescribe for the whole of `AC-3`, and the digest is new and the same correct build is
red. But **a plant is needed at exactly the arms the directory clause is being scoped OUT of**: D4, D5,
D6 and D8 all refuse a non-existent target above their lock (`base.py:429-433` above `:437`;
`writer.py:320-321` above `:327`; `:374-375` above `:379`; and, added by this item, the sibling guard
above `lint_vault.py:819`), while D1a/D1b/D1c bind what they serialize from their own ARGUMENTS
(`writer.py:257`, `:258-261`, `:262-263`) and need no target to exist. Plant-requirement and clause-scope
are the SAME partition of the seven arms `AC-2`'s typed pass covers, so scoping the clause to
`{D1a, D1b, D1c}` does not narrow around the flip — it removes the flip's precondition. The scoping
itself is signed text and is staged in `## Re-origination Brief`.

**One parked adjacency, named so the scoping note is not read as a claim D7 is guarded.**
`roundtrip_file` locks a path it never existence-checks (`writer.py:414-417`), so calling it on a
non-existent path creates the sentinel directory and lock file and *then* fails in `read_note`. It
introduces nothing, so its gate call is on an empty delta and cannot refuse *(round-10 correction: the
superseded sentence read "it has no gate call", which contradicted `## Approach`'s eight-arm routing
and `AC-1`'s floor — D7 routes, and that is orthogonal to its unguarded lock)*, which is why the defect
is outside this item: it is the same shape as Finding F one door over, it is pre-existing, and this
item neither causes nor fixes it. **The fix is SHARED with D8's, not separate** *(round-10 fold,
architect round-9 note 1)*: the guard this item adds to `apply_fixes` is the same one statement
`roundtrip_file` is missing, so whoever takes parked defect 4 copies a line that will already be in the
tree. It is still parked — closing it would move D7 from `above` to `in-lock` in the placement table
and there is nothing in this item that needs that.

##### The placement value is DERIVED by ONE LOCAL rule, and D8 is made to satisfy it (2026-08-11, round-10 fold)

> Answering the round-9 architectural review's blocking issue, which the round-9 data audit confirmed
> from the same source. The finding is against the wall-rule block above — not against Dave's ruling and
> not against the hoist, both of which re-derive: **the rule as written gave D8 two required values at
> once.** Everything above this point stands; this subsection replaces one clause of it.

The round-9 rule let an arm be `in-lock` on either of two grounds — *the frame refuses on the target's
non-existence*, **or** *the target is supplied by a walk of notes already read*. The first is a fact
about the arm's own frame and an AST predicate resolves it for D4, D5 and D6 (`base.py:432-433` above
`:437`; `writer.py:320-321` above `:327`; `:374-375` above `:379` — all three re-read this round). **The
second is a fact about a CALLER**, and the D8 row of the sweep table above is corrected against source:
`apply_fixes(issues, vault_path, idx)` (`lint_vault.py:apply_fixes:804-805`) groups by
`issue.file_path` off its `issues` parameter (`:808-811`) and binds `fpath` from that dict (`:815`);
the walk that guarantees those paths existed is `vault_path.rglob("*.md")` in `read_vault` (`:111`),
reached from `run_lint` (`:1069`), with `apply_fixes` called thirty lines later (`:1100-1103`). Nothing
in `apply_fixes` is evidence the target exists. So the predicate that resolves the other three does not
recognise D8, D8 falls to the rule's own `above` default — while the same rule two paragraphs earlier
requires D8 to be `in-lock`, and D8 **cannot be hoisted**: its delta is `fm`, parsed at `:821` from the
read at `:820`, both inside the lock at `:819`, and hoisting means reading the note outside the lock,
which is the staleness WI-004 closed (`writer.py:324-326`). One pin, two answers, one arm.

**The repair is to make D8 derivable, not to widen the predicate** — the architect's shape (A), which
the round-9 data audit independently endorses because it also removes any need to reason about the
walk's scope:

> **This item adds to `apply_fixes` the existence guard its three siblings carry** — one
> `if not fpath.exists(): raise FileNotFoundError(...)` as the first statement of the per-file body,
> above `note_lock` at `lint_vault.py:819`, in the same statement shape as `base.py:432-433`,
> `writer.py:320-321` and `:374-375`. The placement rule then has ONE leg, local and syntactic:
> **`in-lock` iff the arm's own frame refuses on the target's non-existence above its first `vault_io`
> call of ANY kind (equivalently its `with vault_io.note_lock(...)` statement; corrected per
> architect round 14); `above` otherwise; `above` is the default for an arm the predicate does not
> recognise.** *"DERIVED, not listed"* survives as written, and the four in-lock arms resolve
> identically.

Three things about that guard, so the build does not read it as a formality. **It is a real
correction**: `apply_fixes` runs after the walk, so a note deleted or quarantined in between reaches
`note_lock` on a path that no longer exists, gets the sentinel `mkdir` (`vault_io.py:400`) and the
`.lock` file (`:410-414`), and only then fails inside `read_note` — Finding F's shape, one door over,
and the reason *"it came from a walk"* was never a safety property. **It changes no observable
behaviour for callers**: the raise lands inside the per-file `try/except Exception` at
`lint_vault.py:902-903`, which already prints `Fix error on <name>: …` and continues to the next file,
which is exactly what a vanished file does today via `read_note`. **And it is one line in a function
this item already opens** for the delta threading (`## Questions the later spec round still owes`,
item 2), so it adds a statement, not a work item.

**The second leg is a consistency CHECK, not a second route to `in-lock`.** D5, D6 and D8 pass the gate
a declaration bound inside the lock (`writer.py:329`, `:381`; `lint_vault.py:821`), so they must be
`in-lock` on pain of reading the note outside it. That is also locally decidable, and the wall asserts
it in the opposite direction: an arm the one rule requires `above` while its gate arguments are bound
in-lock is a CONTRADICTION the wall reports, and the repair is that frame's missing existence guard,
never a hoist above the parse that supplies its type. Under this rule the required values over the
whole set are D1a/D1b/D1c `above` (the hoist), D4/D5/D6 `in-lock` (guarded today), D8 `in-lock`
(guarded by this item), D7 `above` (unguarded, and free — its delta is empty).

**The rejected alternative, named so the choice is falsifiable.** The architect's shape (B) — state the
placement table by EQUALITY, as `AC-2` and `AC-4` already state their exclusion sets, with `above` the
default for any arm not in it — is fail-closed for the ninth arm and satisfiable for the eighth, and it
was rejected only because it costs the phrase *"DERIVED, not listed"* that three red-team rounds spent
their findings buying. It stays the correct fallback if the guard is ever found to disturb something
the consumer audit cares about; nothing else in the design depends on which of the two is taken.

##### `AC-2`'s four conjuncts are FRAME properties asserted over a set derived for the GATE — all four swept (2026-08-11, round-12 fold)

> Answering the round-11 architectural review's blocking issue and the round-11 data audit's sharpening
> of it. Neither is against Dave's ruling, the hoist, the arm set or the placement rule — all four
> re-derive from source this round. The finding is that ONE criterion asserts properties of the FRAME
> over the set `AC-1` derives for the GATE, and two of its four conjuncts are false at some arms in that
> set. The class is swept here; the signed consequences are staged in `## Re-origination Brief`.

`AC-2` conjoins four promises and binds them to every arm in `AC-1`'s derived set with the typed-pass
exclusion `{roundtrip_file}` asserted by equality — so **seven arms**: D1a, D1b, D1c, D4, D5, D6, D8.

> *"…is refused at every ARM in `AC-1`'s derived set, the target is left byte-identical, **no stray
> directory is created**, and the refusal is a `LoudFailError` carrying the stable pattern key and no
> note content."*

The gate is a pure function of payload plus handed type (the DECLARE ruling), so it can be routed
anywhere the frame's inputs allow — but *no directory appears* and *the caller sees an exception* are
properties of the FRAME, and a criterion cannot inherit them for every arm the gate is routed through.
Swept conjunct by conjunct, each against the arm's own source:

| # | Conjunct | Holds at all seven? | Result |
|---|---|---|---|
| 1 | refused | **yes** | the gate is total on the delta at every arm; nothing here is frame-dependent |
| 2 | target left byte-identical | **yes, with one sub-cell** | at D4/D5/D6/D8 the refusal is after `read_note` and before `write_note`, so the bytes are untouched; at D1a/D1b/D1c in the CREATE case there is no target to be identical to. See the sub-cell below |
| 3 | **no stray directory is created** | **NO — three of seven** | see the artifact table below |
| 4 | **the refusal is a `LoudFailError`** | **NO — six of seven** | at D8 the gate call is inside `apply_fixes`'s per-file `try` (`lint_vault.py:apply_fixes:816`) whose handler is `except Exception as exc: print(f"  Fix error on {fpath.name}: {exc}", file=sys.stderr)` (`:902-903`), so the refusal is swallowed into a stderr line. Every sibling frame carries `except LoudFailError: raise` above its broad catch (`writer.py:341-342`, `:393-394`); `apply_fixes` does not, because it predates the gate. Resolution in Finding E |

**Conjunct 3, and the fact this document has never separated: `note_lock` creates TWO artifacts with
DIFFERENT arities** *(data-premise round 11, re-derived from source)*. Every prior round wrote "the lock
debris" as one thing. It is two, and they are not created at the same rate:

| Artifact | Keyed on | Arity | Created when |
|---|---|---|---|
| `<parent>/.obsidian-schemas-locks/` | the target's PARENT (`vault_io.py:_sentinel_path:350`, `SENTINEL_DIR_NAME` at `:58`) | **one per directory, ever** | only if that parent has never been locked — `ensure_dir` is `mkdir(parents=True, exist_ok=True)` (`vault_io.py:ensure_dir:618-638`) |
| `<parent>/.obsidian-schemas-locks/<sha256(str(target))[:32]>.lock` | the RESOLVED TARGET (`vault_io.py:348`, `_resolved` at `:376`) | **one per note, ever** | only if that note has never been locked |

Three consequences, and they decide the shape rather than merely colouring it:

- **The signed conjunct is not what goes red at D4/D5/D6/D8 — the round-9 ORACLE is.** Those four arms
  reach the gate only if the target already exists, so its parent has a lock home already or acquires one
  once, ever; what a refused write leaves there is a new zero-byte `.lock` FILE, which is not a directory
  and which the conjunct does not forbid. The clause is *meetable* at those arms; the ambient-listing
  oracle is not. That is the same LESSONS #35 diagnosis one artifact finer — `.obsidian-schemas-locks/`
  and `<digest>.lock` are two artifacts, and an oracle that names neither forbids both.
- **A genuine stray DIRECTORY is creatable at `{D1a, D1b, D1c}` and only there.** It takes a
  path-mangled parent, and the only frame in this package that mints one is `base.py:381`'s filename
  derivation feeding `write_markdown_file` — Finding F's own defect, executed and on the record
  (`## Conductor Booking`). At the four in-lock arms the parent is an existing note's parent.
- **Filtering `SENTINEL_DIR_NAME` out of a listing does NOT rescue the ambient oracle.** Filtering the
  directory ENTRY leaves the per-note `.lock` inside it in the listing, and the `.lock` is the artifact
  that is always new; the filter would have to drop the whole SUBTREE. Recorded because it is the
  cheapest of the available repairs to implement subtly wrong.

**The sub-cell conjunct 2 leaves, found by sweeping the level below the conjuncts** *(this round's
next-level sweep, per WI-226)*. The dimension under "which conjunct" is *which artifact each conjunct's
oracle names*, and conjunct 2 names "the target" — which at D1a/D1b/D1c's create case does not exist
before the call. *"Left byte-identical"* has no referent there, and a fixture is free to read it as
vacuously true. The reading the criterion plainly means is *"a target that existed is unchanged; a target
that did not is not created"*, and the second half is exactly what the replacement oracle above asserts
by name. It costs one fixture sentence and no promise change, so it rides on the `AC-2` item already in
the brief rather than opening one.

**And the level below that — the artifacts no conjunct names — is declared rather than left open.** At
the four in-lock arms a refused write may leave a new `<digest>.lock` inside an existing lock home —
**and, where that parent has never been locked, the `.obsidian-schemas-locks/` DIRECTORY as well**
*(precision added round-13 fold, architect round-12 note 1; the round-12 wording said "inside an
EXISTING lock home" and understated the declaration by exactly this case)*. `ensure_dir` runs on every
OUTERMOST acquisition (`vault_io.py:note_lock:398-400`, guarded only by `if not reentrant:` at `:393`),
so the home is minted by the refused write itself whenever the parent is fresh — which is precisely the
state a fixture reaches when it plants its note with `Path.write_text` into a tmp vault, since nothing
there has locked anything. That is the fixture shape `AC-2`'s Tier-1 sweep produces at those arms, so the
case is not exotic; it scores NOTHING, because conjunct 3 is scoped out of `{D4, D5, D6, D8}` by the
clause above, and G5(b)'s new column sizes the same artifact in production. It is stated because a
declaration that omits it invites the next oracle to rediscover a directory appearing at an in-lock arm
and read it as the stray directory the criterion forbids. All of it is permitted debris: it is
`note_lock`'s contract, not this item's write, `ensure_dir`'s ruling says nothing in this package removes
what it creates (`vault_io.py:621-624`), and removing it is precondition 1's rejected option (b) — a
`vault_io`/WI-004 amendment with its own blast radius and a different work item. It is named here so that
a future oracle does not rediscover it as a finding, and its live size is G5(b)'s new column
(`## Grounding Still Owed`).

**Where the UNDECLARED case exists, and where it cannot.** Rewritten with the rest of Finding B: the
dimension is no longer "typed vs untyped note", it is "the caller declared a type or it did not", and
under rule (ii) it decides refusal rather than dispatch. It is a property of the arms whose dict is
the CALLER'S, so it is scoped by ARM shape rather than asserted over the whole set:

- **Caller-dict arms — D1b, D1c.** The frontmatter dict is the caller's and carries `type:` or does
  not (writer.py:259, :263). This is the whole of the undeclared cell on the write side, and it is
  where rule (ii)'s refusal is live and constructible.
- **Note-derived arms — D5, D6.** The dict is parsed off the note on disk one line before the
  mutation (writer.py:329, :381), so the declaration is the note's own `type:`. An undeclared write
  here means a note that itself carries none — live in principle, empty in the vault today (count 1),
  refused under rule (ii).
- **Repository arm — D4, and the D3 rider beside it** *(re-scoped round-7 fold: D2 and D3 are no
  longer arms; the rider is still handed a declaration and is still pinned, by its own fixture rather
  than by the wall)*. `self.type_name` is an abstract property on the base
  (base.py:188-192), so a declaration is always present and is never the caller's to omit. The
  undeclared case is UNCONSTRUCTIBLE here: there is no branch for an implementation to get wrong, and
  a fixture would pass whether or not the rule was implemented — a control with no discriminating
  power, which is worse than no control because it reads as coverage. What IS constructible on these
  arms, and what must be pinned instead, is the WRONG-DECLARATION case: an arm passing `None` (or a
  hardcoded literal) where `self.type_name` was available.
- **Entity-shaped arm — D1a**, the only one *(round-7 fold: D2/D3 left the set, so "the entity-shaped
  arms" is now one arm plus the D3 rider, and every entity-shaped clause in this document reads that
  way)*. `model_to_frontmatter` iterates `model_class.model_fields.keys()`
  (writer.py:111) and emits every declared field, and `Person.type` is `Literal["person"] = "person"`
  (models.py:78) — a declared field with a default — so the serialized dict always carries
  `type: person` no matter what the caller passes, and `extra_fields` cannot displace it through the
  guarded merge (writer.py:127). Unconstructible, for the same reason as the repository arms.
- **D8 `lint_vault --fix`.** Unconstructible for a different and stronger reason, established above:
  an undeclared note is stopped at lint_vault.py:318-326 and never reaches the arm.
- **D7 `roundtrip_file`.** Introduces nothing; out under the delta rule.

`write_markdown_file` therefore sits in BOTH classes, and stating the split at ARM granularity is
what lets that be said precisely: D1b and D1c are the undeclared cell, D1a is not, and the function
is never excluded or included wholesale. **Note for the re-origination:** this list is materially
narrower than the one AC-2 and AC-4 were signed against. Their untyped clauses name six dict-shaped
arms including `update_fields` and `lint_vault --fix`; under DECLARE those two carry a declaration
unconditionally and D8 cannot even reach an undeclared note, so exactly two arms — D1b and D1c — plus
the note-derived pair D5/D6 remain. **And their EXCLUSION sets now name two things that are not
members at all** (round-7 fold): both name `BaseRepository.save` and `PersonRepository.save`, which
under the corrected arm set are outside the derived set rather than excluded from a pass within it, so
an equality assertion over the eight arms cannot reconcile against either set as signed. Both
corrections are listed in `## Re-origination Brief`.

### Finding C — the delta rule, and why the seam is not the gate's home

Validating the WHOLE record at that seam would brick the vault. The 2026-06-02 audit that produced
NameValidator found real Tier-1 dirt across 1647 live notes; WI-111 and WI-117 each removed
individual corrupt names by hand as late as June. Under whole-record validation, every one of those
surviving notes becomes permanently unwritable — an unrelated `company` update through D4 would
raise, `roundtrip_file` could never normalize one again, and `lint_vault --fix`, the tool whose job
is to repair them, would be refused before it could write the repair. The remedy would be the
disease.

> **Re-dated 2026-08-11 (data-audit item 3, run by the conductor against the live vault; numbers in
> `## Conductor Rulings & Grounding`).** The count above is now historical and must not be cited as
> current. Today: **79 Tier-1-dirty stored names in total, of which 2 are live** — the other 77 sit
> in archive directories (`_merged_dupes/` 61, `_quarantine/` 16). Both live hits, `@+12068523646.md`
> and `@447950289840.md`, are pure-digit WI-083 phone-sentinel stubs — *intentional records*, not
> legacy dirt (Finding H). So the "1647 notes of legacy dirt would be bricked" argument is spent as
> an empirical claim, exactly as the data audit anticipated when it wrote "if it is zero, say so and
> keep the delta rule on its design argument".
>
> **The delta rule stands, and on the design argument alone.** Two legs of it never depended on the
> count and both re-derive: (a) `lint_vault --fix` and `roundtrip_file` exist to REPAIR records, so a
> gate that judges what a write preserves refuses the repair tools by construction — the argument is
> about the tools' purpose, not about how many notes currently need them; and (b) the delta is the
> only thing available one frame above the seam anyway (base.py:437 pre-merge, writer.py:329, :381
> — *round-11 correction: those three citations name where each frame binds its PARSE of the stored
> note, which is the delta's neighbour and not the delta itself; at D5 the introduced fields have no
> dict form in the frame at all. See the round-11 subsection below before reading any of them as an
> instruction*),
> so whole-record judging is not merely unwise here, it is a different and worse position in the call
> stack. Four gate rounds held the rule on this reasoning. What the re-dating DOES change is the risk
> register: the delta rule is now a cheap insurance policy rather than a load-bearing brick-avoidance
> mechanism, and the two live specimens it protects are the sentinel stubs, which Finding H handles
> by an exemption rather than by the delta rule.

So the rule is: **judge what the write INTRODUCES, never what it preserves.** An entity write — D1a,
and the D3 rider above it *(round-7 fold: was "D1–D3"; D2/D3 are no longer arms, but the shape of the
statement is unchanged, because an entity write still reaches bytes only through D1a)* — rewrites the
whole record from a typed model, so its name IS the delta. A dict write (D1b, D1c, D4–D6, D8)
introduces only the keys it carries, so only those are judged. `roundtrip_file` (D7) introduces
nothing and is judged on nothing.

And the delta only exists ONE FRAME ABOVE the seam — by `write_frontmatter` the incoming fields have
already been merged into the note's full frontmatter (base.py:451, writer.py:333, :384). That kills
the elegant "gate inside the serializer" answer (Approach B) and forces the shape the approach
below takes: one gate FUNCTION whose home is a module of its own, called by each door with what
that door actually knows, and a DERIVED wall that proves the call set is total instead of a
maintainer remembering to add the seventh door.

#### One of the four repair doors cannot REACH most of the population count 3 measured (2026-08-11, round-10 fold)

> Answering the round-9 data audit's finding. It is decided entirely by a constant in this tree, it
> needs no vault query, and it does not make `AC-3` false — every door `AC-3` names still commits for a
> stored-dirty note, which is the design property the criterion asserts. What it changes is which of
> those doors can be exercised against the live population, and therefore what the criterion's fixture
> is honestly proving.

`AC-3` names four repair doors — `update_fields` on an unrelated field, a body-section append,
`roundtrip_file`, and `lint_vault --fix`. The fourth one walks a corpus with a hole in it, and the hole
is exactly where the dirt is. Every link read from source this round:

| Link | Source |
|---|---|
| `--fix` fixes only what the lint pass found | `lint_vault.py:1100-1103` — `apply_fixes(fixable, …)` where `fixable ⊆ all_issues` |
| every issue comes from the files `read_vault` returned | `:1069` (`all_files = read_vault(vault_path)`), `:1080-1093` |
| `read_vault` walks `rglob("*.md")` and DROPS anything `should_skip` matches | `:109-113` |
| `should_skip` is true if ANY path part is in `SKIP_DIRS` | `:104-106` |
| `SKIP_DIRS` = `{".obsidian", "Templates", "src", ".trash", "_quarantine", "_merged_dupes"}` | **`lint_vault.py:SKIP_DIRS:57`** |

Against the conductor's count 3 — *79 Tier-1-dirty stored names total, of which 2 live; the 77 others
in `_merged_dupes/` (61) and `_quarantine/` (16)* — **both archive directory names are members of
`SKIP_DIRS`**. So `lint_vault --fix` provably never reads 77 of the 79 notes in the population `AC-3`
exists to keep writable, and the only Tier-1-dirty notes it CAN reach are count 3's two live hits,
`@+12068523646.md` and `@447950289840.md` — the WI-083 phone-sentinel stubs, which are dirty **by
design** and carry Finding H's payload-derived exemption (`person.py:1406`).

Three consequences, and only the first touches signed text:

1. **`AC-3`'s `lint_vault --fix` leg must be signed knowing its fixture is SYNTHETIC.** Its live
   discriminating population is at most two notes that the gate is required to permit anyway, so the
   fixture is necessarily a constructed tmp-vault note. That is fine and normal — it is not fine
   *silently*: an oracle that is satisfied identically whether or not the door works on the population
   it was written for is the WI-235 shape, and it is the same rider the round-9 fold demanded for
   `AC-2`'s fixture one criterion over. Staged in `## Re-origination Brief` under the `AC-3` item.
2. **Count 3's "the premise is now historical" reading is scoped TWICE, not once.** Round 8 showed the
   measurement corpus cannot see path-forked notes because their leaf is `Bob.md` rather than `@*.md`
   (that became G5). This shows the other half: even for the dirt count 3 DID find, the one repair door
   `AC-3` names that could clean it is barred from the directories it sits in. "Historical" means *out
   of the walker's scope*, not *cleaned* and not *reachable*.
3. **`should_skip` is the right partition for the owed queries, and `SKIP_DIRS` has six members, not
   two.** G1's hand-written path class names `_merged_dupes/` and `_quarantine/`; a note under
   `.trash/` or `Templates/` would land in G1's *"neither"* bucket and read as live while no vault
   walker in this repo will ever touch it. G1 has not run, so this is a free correction, made in
   `## Grounding Still Owed`; G4 and G5(a) inherit it rather than each carrying a hand-copy.

**What this does NOT say.** It does not weaken the delta rule, whose two surviving legs are arguments
about the repair tools' PURPOSE and about where the delta lives in the call stack — neither of which
turns on how many notes a given tool's walker reaches. And it does not remove `lint_vault --fix` from
the door set: it is D8, it is a routed arm, and a fixture through it is required by `AC-1` regardless.

#### Where the delta LIVES is arm-specific, and at D5 it has no dict form in the frame at all (2026-08-11, round-11 fold)

> Answering the round-10 architectural review's note 1 — the unsigned half of its blocking issue,
> free to fold in the same round. It is the correction the round-5 fold already wrote for D1b, in the
> other direction, and it costs one paragraph.

This Finding's own sentence cites `base.py:437`, `writer.py:329` and `:381` for *"the delta only exists
ONE FRAME ABOVE the seam"*. Those citations name where each frame binds its PARSE of the stored note.
That is the delta's neighbour, not the delta — and at two arms the two objects are not merely different:
one of them has no dict form in the frame at all. Every row re-read from source this round:

| Arm | Where the STORED record is bound | Where the INTRODUCED fields are | Merge |
|---|---|---|---|
| D4 `update_fields` | `frontmatter` — `base.py:439` | `updates`, the caller's dict, a parameter — `base.py:406` | `frontmatter.update(updates)`, `base.py:451` |
| **D5 `update_frontmatter_field`** | `frontmatter` — `writer.py:329` | **two loose parameters**, `field_name` and `field_value` (`writer.py:294-295`) — **no dict anywhere in the frame** | `frontmatter[field_name] = field_value`, `writer.py:332` |
| D6 `update_frontmatter_fields` | `frontmatter` — `writer.py:381` | `updates`, the caller's dict, a parameter — `writer.py:352` | `frontmatter.update(updates)`, `writer.py:384` |
| D8 `lint_vault --fix` | `fm` — `lint_vault.py:821` | nothing bound: the `elif` branches mutate `fm` in place, which is why threading a delta is item 2 of `## Questions the later spec round still owes` | in place, `:822-875` |
| D1a | — | `model_to_frontmatter`'s projection IS the whole record (`writer.py:257`) | none — record == delta |
| D1b / D1c | — | the caller's dict IS the whole record (`writer.py:258-263`) | none — record == delta |

**D5 is the sharpest case in the tree and the review is right to name it.** The gate must be handed
`{field_name: field_value}`, an object the build has to CONSTRUCT, while `frontmatter` — the stored
record, the wrong object — sits bound one line above the natural call site at `writer.py:332`. A build
that reads the Finding C citation as the instruction lands on precisely the object the delta rule exists
to keep out of the gate. D6 is the same shape with the delta available as a parameter, so it is one
degree safer and identical in consequence.

**Stated here for the same reason the round-5 fold stated D1b's, and it is the same sentence in the
other direction:** the citation names where the arm's dict is BOUND; the gate must be handed the fields
the write INTRODUCES. At D1b that meant reading `fm` at the convergence point rather than the
`frontmatter` parameter; at D5/D6 it means constructing the delta rather than reaching for the parse.
The two are the only places in this document where the citation and the instruction come apart, and both
are now stated.

#### Reachability is THREE partitions, not one — and it is what makes `AC-3`'s door list load-bearing (2026-08-11, round-11 fold)

> Answering the round-10 data audit's finding. It needs no vault query — every partition is a walker in
> this tree — and it is the reason the `AC-3` repair the round-10 architect asks for is necessary rather
> than merely tidier.

The subsection above established that `--fix` cannot reach `_merged_dupes/` or `_quarantine/`, where 77
of count 3's 79 Tier-1-dirty stored names sit, and restated G1's archive class as `should_skip`'s own
predicate. **`should_skip` is `lint_vault`'s partition. It is not the package's, and it is not the
repositories'.** Read from source this round, this tree has three independent reachability partitions,
they bind different arms, and they CROSS:

| Partition | Where | What it excludes | Which arms it binds |
|---|---|---|---|
| `should_skip` over `SKIP_DIRS` | `lint_vault.py:should_skip:104-106`; `lint_vault.py:SKIP_DIRS:57` | any path with a part in `{.obsidian, Templates, src, .trash, _quarantine, _merged_dupes}` | **D8** |
| `glob(file_pattern)` — **NON-RECURSIVE** | `base.py:load:230`, with the default `"@*.md"` at `base.py:file_pattern:195-197` | **everything not at the vault ROOT**, whatever it is named | **D4**, and every Class-2 body writer |
| none at all | `writer.py:update_frontmatter_field:292-296`, `writer.py:update_frontmatter_fields:350-353`, `writer.py:roundtrip_file:414` | nothing — any path that `.exists()` | **D5, D6, D7** |

Every leg re-derived rather than inherited. `update_fields` resolves its target through `get_file_path`
(`base.py:427`) → `self._file_map` (`base.py:get_file_path:343-354`), which only `load` populates
(`base.py:235`) off that non-recursive glob, and raises `ValueError` when the lookup misses (`:429-430`);
the six body writers reach the same accessor and raise the same way (`person.py:1538-1540`, and at
`:1657`, `:1725`, `:1788`, `:1854`, `:1928`). D5/D6/D7 take a `Union[str, Path]` and consult no walker at
all — the only constraint is `.exists()` (`writer.py:320-321`, `:374-375`).

**Mapped onto count 3's population, `AC-3`'s four hand-listed doors have an EMPTY live discriminating
set.**

| `AC-3`'s named door | Can it write one of the 77 archived dirty notes? | Why |
|---|---|---|
| `update_fields` on an unrelated field | **no** | the map is filled by a root-only `glob`, so an archived note is never loaded, `get_file_path` returns `None`, and `base.py:429-430` raises before any write |
| a body-section append | **no** | same accessor, same map, same raise (`person.py:1538-1540`) |
| `roundtrip_file` | yes | raw path, no walker — but it INTRODUCES nothing (`writer.py:414-426`), so the delta rule is satisfied by an empty delta and the fixture discriminates nothing |
| `lint_vault --fix` | **no** | `SKIP_DIRS`, derived in the subsection above |

**And the two arms `AC-3` does NOT name are the only two in the whole eight-arm set through which any of
those 77 can be written at all.**
`update_frontmatter_field(Path("<vault>/_merged_dupes/@X.md"), "company", "Acme")` is a legal call today:
no repository, no glob, no `SKIP_DIRS`, and the note's own `type:` supplies the declaration
(`writer.py:329`). Under the failure the round-10 architect describes — a build gating the merged record
rather than the delta at D5/D6 — that call becomes permanently refused, and there is no other door in
this package through which those notes can be amended or repaired. That is the *remedy-is-the-disease*
outcome this whole Finding exists to prevent, greenable with `AC-1`, `AC-2` and `AC-4` all satisfied.

**So the two omitted arms are not two more members of a list; they carry the whole of the criterion's
live subject matter.** Which is also why the repair is a RE-BASING onto `AC-1`'s derived set rather than
"add D5 and D6 to the list": a hand-list that happened to name the two arms with a live population would
still exempt the ninth arm by construction — the shape `AC-2` and `AC-4` were re-based to escape, in the
one criterion that still carries it. Staged in `## Re-origination Brief` under the `AC-3` item, with the
exclusion set asserted **by equality** as `{D1a, D1b, D1c}` and with its reason stated rather than left
to a builder: those are the arms whose delta IS the whole record (`writer.py:257`, `:258-263`), where a
note carrying a stored-dirty name cannot be written without re-introducing it and refusal is the correct
answer — which `AC-2`'s typed pass already asserts.

**Two consequences that ride with it, named so the re-origination does not have to rediscover them.**
(1) The fixture population for the WHOLE criterion is **synthetic**, for the reason the round-10 fold
already booked for the `--fix` leg alone — count 3's two live Tier-1-dirty names are the WI-083 sentinel
stubs, which the payload rule permits anyway — so that rider now covers `AC-3` end to end and carries a
stated reason instead of one door's accident. (2) The body-section append stays as a named BEHAVIOURAL
example rather than as a member: it is a Class-2 pass-through (`## Exploration Notes`, Class 2) and not
an arm, and the criterion should say so rather than leave the reader to infer it from the arm set's
silence.

**One non-blocking correction to the numbers, recorded so the next reader does not equate two objects.**
Count 1 and count 3 were measured with `rglob("@*.md")` (`## Conductor Rulings & Grounding`), a recursion
`PersonRepository` does not have — its corpus is `glob("@*.md")` at `base.py:230`, root only. This
changes no ruling: rule (ii) is fail-closed, so count 1 being a SUPERSET of the repository corpus is
conservative in the safe direction. It matters for count 3, which feeds `AC-3`'s *"the premise is now
historical"* reading: any dirty note in a subdirectory was counted while no repository door can touch it.
G1's new depth column (`## Grounding Still Owed`) resolves it as a by-product.

**What this subsection does NOT say.** It does not make `AC-3` false, and it does not weaken the delta
rule — if anything the D5/D6 reading strengthens it, because those are the arms where a legacy-dirty note
is genuinely reachable and genuinely brickable. It says the criterion as signed asserts the rule over
three arms where nothing is at stake and is silent at the two where everything is.

### Finding D — the consolidation rider is partly false; three jobs, not four copies

The mint claims RFC 2822 parsing "now lives in ≥4 sites … collapse to one authority". Read against
the tree, the four sites do three different jobs, and only two of them are duplicates. Trigger
predicates quoted from the current tree, per the REMOVE-audit rule — this item does propose deleting
mechanisms, and a name is not evidence:

| Site | TRIGGER PREDICATE (read from the tree) | Job | Classification |
|---|---|---|---|
| `create_stub` parseaddr (person.py:1386) | unconditional on every `create_stub` call; effect gated on `if parsed_email and "@" in parsed_email` (:1387) | split a name-blob into (name, address) and adopt the address if the caller passed none | **REPLACE** — the job survives verbatim, only the parser moves |
| `_extract_email_and_name` (person.py:1286) | called per entry of `person.emails` / `person.aliases` from `_normalize_address_fields`, itself called ONLY from `PersonRepository.save` (:1269) | split an `emails[]`/`aliases[]` entry into (address, display) | **REPLACE** — same job as the row above; this is the ONE real duplication |
| `identifier.Email.parse` parseaddr (identifier.py:145) | `if "<" in raw_s and ">" in raw_s` — angle-bracket forms only, deliberately excluding the bare form so parseaddr cannot silently repair `a@b c.com` into `a@bc.com` and mint a wrong identity key (:141-144) | parse to a typed, normalized `Email` | **KEEP — this is the authority** |
| `name_validation._RFC2822_LEAK_RE` (name_validation.py:54, fired at :320) | `_raise_on_tier1` searches it on the ORIGINAL casing, after the `@` check has already fired | DETECT an address that lost its punctuation (`faithmforstergmailcom`) — no `@`, no `<>`, nothing parseaddr can see | **KEEP — not a parser at all** |

So "one RFC 2822 parse authority" resolves to: `Email.parse` is the authority; one new shared
splitter is built on it and replaces the two duplicate sites; `_RFC2822_LEAK_RE` is a detector and
stays.

One honest limit on that table, stated because AC-5 depends on it: **it was assembled by grepping
for `parseaddr`, so it is a LOWER bound on the duplication, not a census.** A hand-rolled splitter —
`raw.split("<")`, a bare `re.match` on `Name <addr>`, a call through another `email.utils` member —
does the identical job and no `parseaddr` grep can see it. `_extract_email_and_name` is itself half
that shape already (it reaches for a parens REGEX at person.py:1295 before it ever reaches
parseaddr), which is the existence proof that the job is written in this codebase without the
symbol. AC-5's sweep is therefore keyed on the JOB SHAPE rather than on the `parseaddr` symbol; if
it resolves a fifth site the grep missed, that site is in scope for the consolidation by
construction rather than an out-of-scope surprise at build time.

Three concrete reconciliations the spec owes, all discovered by reading both implementations
side by side:

1. `_extract_email_and_name` accepts a parens form, `Name (a@b.com)`, via the regex at person.py:1295;
   `Email.parse` does not. Either the splitter handles it before delegating, or that form silently
   stops normalizing.
2. `_extract_email_and_name`'s acceptance test is `"@" in email_p and "." in email_p` (:1292) —
   strictly laxer than `Email.parse`, which additionally rejects whitespace and multiple `@`. Some
   entries that are kept-as-is today will start normalizing, and vice versa. That is a real
   behaviour delta on live data, not a refactor. **Enumerated and given a predicate below** (round-5
   fold), answering the round-4 data audit's Finding 2(a): "some entries" was an unbounded phrase
   sitting where a number belongs.
3. `create_stub` currently trusts parseaddr on a BARE input; `Email.parse` deliberately does not.
   Adopting the authority means `create_stub` inherits that refusal.

**Reconciliation 2, enumerated from source (new 2026-08-11, round-5 fold).** The data audit is right
that `AC-5`'s agreement clause is written *around* this delta rather than over it, so no criterion
catches it. What the fold can do inside this cage is turn "some entries … and vice versa" into a
CLOSED enumeration of disagreement classes plus a re-runnable predicate; what it cannot do is run it.
Both implementations read side by side this round — `_extract_email_and_name` at
`person.py:1286-1298`, `Email.parse` at `identifier.py:134-160`:

| # | Class | Today | Under the authority | Read from |
|---|---|---|---|---|
| 1 | address containing internal whitespace (`a@b c.com`) | `_extract`'s test is satisfied (`"@"` and `"."` both present), so it normalizes | **refused** — `any(c.isspace() …)` | `person.py:1292`; `identifier.py:153-154` |
| 2 | more than one `@` (`a@b@c.com`) | `"@" in email_p` is satisfied — normalizes | **refused** — `s.count("@") != 1` | `person.py:1292`; `identifier.py:155-156` |
| 3 | dot present but NOT in the domain (`a.b@localhost`) | `"." in email_p` tests the WHOLE string — normalizes | **refused** — `"." not in domain` | `person.py:1292`; `identifier.py:158` |
| 4 | empty local (`@b.com`) | `"@"` and `"."` both present — normalizes | **refused** — `not local` | `person.py:1292`; `identifier.py:158` |
| 5 | **parens form with a dotless domain** (`Jane (a@localhost)`) | the parens regex `[^@\s]+@[^\s)]+` requires no dot at all — extracts | **refused** | `person.py:1295`; `identifier.py:158` |
| 6 | **mixed-case address** (`Al.B@Example.COM`) | stored VERBATIM — `_extract` returns parseaddr's output unmodified | **lower-cased** — `s = candidate.strip().lower()` | `person.py:1293`, stored at `:1308`; `identifier.py:150`, `.value` at `:163-164` |

Classes 1–5 are the "stops normalizing" direction. Classes 1 and 2 are not accidents — they are
precisely what `Email.parse`'s angle-bracket gate was written to refuse, with the reason in the
source (`identifier.py:141-144`), so adopting the authority is *supposed* to change them; the point
is that the spec must say so rather than ship it as a refactor. **Class 5 is the one the architect's
splitter ruling does not close by itself**: owning the parens form BEFORE delegating fixes which
STRINGS reach `Email.parse`, not which of them it accepts.

**Class 6 is new, unconditional, and nobody has named it.** It is not a laxity difference at all —
it is a normalization difference that fires on every stored address carrying an uppercase letter.
Dedupe is already case-insensitive at the callers (`person.py:1307`, `:1314`), so nothing collapses
that did not collapse before; what changes is the stored BYTE. That makes it a spec decision the
splitter's contract must state explicitly: **does the splitter return `Email.parse(...).value` (the
normalized, lower-cased address) or the raw slice it matched?** The architect's ruling settles the
splitter's SHAPE (`(address | None, display)`, `IdentifierError` → "not an address") and is silent
on this, and the two answers write different bytes into every `emails[]` entry in the vault.
Recorded here as owed to the spec, not decided in the exploration.

**The predicate, in re-runnable form** (data-audit round-4 item 2):

> Over every stored `emails[]` and `aliases[]` entry in the vault, evaluate BOTH
> `_extract_email_and_name` (`person.py:1286-1298`) and `Email.parse` (`identifier.py:134-160`) and
> report four cells — *extracted AND parsed* (agree), *extracted but `IdentifierError`* (stops
> normalizing; classes 1–5), *not extracted but parsed* (starts normalizing), *neither*. Within the
> agreeing cell additionally report how many entries differ **only by case** between `_extract`'s
> returned address and `Email.parse(...).value` (class 6). Report counts and a sample per cell,
> **and report every cell separately for `emails[]` and for `aliases[]`** rather than combined.
> Finally, **within the `emails[]` *extracted* cell, report how many entries have a NON-EMPTY display
> half whose value is not already present in that same note's `aliases[]`** *(added round-7 fold, per
> the round-6 data audit)* — that intersection, not the extracted cell itself, is the population the
> dict-arm rule deletes, because an entry whose display half is already in `aliases[]` loses nothing
> when the stored `emails[]` entry is reduced to its address.

**Why the per-field split, added 2026-08-11 (round-6 fold), answering the round-5 data audit.** The
two fields no longer get the same treatment: under Finding I's arm-shape split the `aliases[]`
migration runs on entity-shaped arms only, so the *extracted* cell restricted to `aliases[]` is
exactly the population that split forks — **how many stored `aliases[]` entries are
address-bearing**. It is worth insisting on because this document's own evidence points two ways at
once: Finding I offers `create_stub`'s `aliases=[email]` seed (`person.py:1448`) as the existence
proof, and parked defect 2 shows that same seeded alias is erased by its own save
(`person.py:1323-1337` — the address is already in `seen_emails_lower` from the `emails[]` pass, so
nothing is appended and the empty display half drops the entry). At zero the arm-shape split is a
correctness-preserving scoping clause with no live subject and the spec says so; non-zero, it is a
live behavioural fork and `AC-4`'s scoped clause is what stands between it and a silent regression on
the dict side. Same pass, same corpus, one extra column.

If the first three non-agreeing cells are empty the consolidation is a refactor and the spec says so;
if they are not, the spec owes the list. Class 6's cell is the one most likely to be non-empty, and
it is the one that changes bytes rather than behaviour. Booked in `## Grounding Still Owed`.

### Finding E — the refusal cannot be raised the way WI-105 raises it

`NameValidationError` (name_validation.py:125) is a bare `ValueError` and interpolates the offending
name into its own message (`{name!r}` at :313, :323, and every sibling). That is tolerable at
`create_stub`, which is a producer-facing boundary. It is not tolerable once the same refusal
travels the WRITE path, where three WI-020 contracts now apply: `except LoudFailError` is the
documented "this package refused" idiom and would not catch it; `REASONS` (errors.py:110) is a
closed enumeration and `bounded_message` refuses any reason outside it; and `chainable_cause`
(errors.py:212) suppresses anything that is not a `LoudFailError` or an `OSError`, so a
`NameValidationError` cannot even ride `__cause__`.

The resolution has a precedent in the tree: the door converts, and the STABLE PATTERN KEY
(`"rfc2822_leak"`, `"path_hostile_char"`, …) rides in ~~the `declared_type` slot~~ **a dedicated
`pattern` attribute**, a source literal by construction, so no note content reaches a log line. That is
the same channel `vault_io._bad_setting` (`vault_io.py:88`) uses to name an environment variable without
leaking its value. Consumers keep the routing signal; the person's name never reaches a log line.
*(Correction, round-12 fold — an in-place repair of a contradiction, not a new decision. This paragraph
carried `declared_type` from round 1 while `## Approach` and `## Carried Forward` have both said
**dedicated `pattern` attribute, never `declared_type`** since round 3, for a stated reason:
`base._note_skip` reads `declared_type` straight off the exception and feeds it to `_owns`
(`base.py:_note_skip:266-274`, `_owns` at `:258-264`), so a pattern id in that slot makes every
repository disown the note it just refused. Left standing, this section and the design were buildable two
ways. Note for the spec: `bounded_message`'s keyword set is `path`/`declared_type`/`cause`
(`errors.py:bounded_message:134-136`), so whether `pattern` also RENDERS into the message is a spec-time
call on that function's signature; the attribute is the contract either way.)*

**And at D8 the refusal is not observable as an exception at all — the one arm where `except
LoudFailError` is false today** *(round-12 fold; architect round 11, second leg, confirmed from source by
data-premise round 11)*. `apply_fixes` wraps its whole per-file body in `try:` (`lint_vault.py:816`) with
`except Exception as exc: print(f"  Fix error on {fpath.name}: {exc}", file=sys.stderr)` (`:902-903`), and
that handler sits INSIDE the `for fpath, file_issues in by_file.items()` loop at `:815`. So a
`LoudFailError` raised by the gate at D8 is swallowed into a stderr line, and `## Approach`'s closing
claim — *"`except LoudFailError` remains the one idiom for 'this package refused'"* — is false at exactly
the arm the repair tool lives on. Every sibling frame already carries the correct idiom above its broad
catch (`writer.py:341-342`, `:393-394`).

**The repair is not `except LoudFailError: raise`, and this is a decision rather than a copy.** Because
the handler is inside the loop, re-raising aborts the whole `--fix` run on the first refused note —
3,418 notes' repairs abandoned because one carries a name the gate declines. That is the wrong contract
for a batch repair tool, and it is not what the sibling frames' idiom means: those are library DOORS with
one target each, where propagating is the only way to tell the caller. **This item takes the third
shape**: `apply_fixes` gains a dedicated refusal arm ABOVE the broad one, which records the refusal in a
structured per-file refusal list (path + the exception's `pattern` attribute, never note content), prints
a refusal line distinguishable from `Fix error on …`, and CONTINUES to the next file; the function reports
the refusal count alongside its `fixed` count, and the CLI surfaces it. That keeps the batch semantics,
makes "did this package refuse?" answerable structurally rather than by scraping stderr, and gives
`AC-2`'s fourth conjunct something to assert at D8 — a counted, typed refusal record rather than
`pytest.raises(LoudFailError)` at a tool boundary that has never propagated anything. **The rejected
alternative is named so the choice is falsifiable:** plain `except LoudFailError: raise`, which is one
word shorter, matches the siblings literally, and turns one dirty note into a vault-wide repair outage.
Which of the two `AC-2` means is a difference a fixture can see, so it is staged as one clause on the
`AC-2` item in `## Re-origination Brief` rather than decided silently here; the design above is this
fold's recommendation and the brief says so. The edit lands in the same function and the same task as the
delta threading and the existence guard (`## Questions the later spec round still owes`, item 2).

**And the arm CANNOT filter on `LoudFailError`, because that is the base of the hierarchy and this frame
already raises four of its subclasses today** *(round-13 fold, architect round 12 blocking, its exhibit
sized by data-premise round 12; re-derived from source here rather than accepted from the finding)*. The
round-12 wording above said *"a dedicated `except LoudFailError` arm"*, copying the siblings' idiom
verbatim. Read against `apply_fixes`'s own per-file `try` (`lint_vault.py:apply_fixes:816-900`), that
filter catches things the gate had no part in:

| Call inside the per-file `try` | Raises | Where that raise is written |
|---|---|---|
| `vault_io.note_lock(fpath)` (`lint_vault.py:819`) | `WriteFailedError` on thread-lock timeout, on `ensure_dir` failure, on `filelock.Timeout`, on `OSError` | `vault_io.py:note_lock:387-388`, `:405-406`, `:416-417`, `:419-420` |
| `parse_frontmatter(content)` (`:821`) | `FrontmatterParseError` — fence opened and never closed, or YAML `safe_load` refused | `parser.py:parse_frontmatter:96`, `:107` |
| `vault_io.write_note(...)` (`:882`, `:900`) | `WriteFailedError`, `ExternalWriteConflict`, `NoteAlreadyExists` — the three classes `vault_io`'s door-1 commit path raises | classes declared `errors.py:80`, `:92`, `:98`; the door's own raise sites are `vault_io`'s and are not re-cited here |

Every one is a `LoudFailError` by declaration (`errors.py:LoudFailError:37`; `FrontmatterParseError`
reaching it through `NoteParseError` at `:57`/`:65`), and **none of them can carry a `pattern`**:
`bounded_message`'s keyword set is `path`/`declared_type`/`cause` (`errors.py:bounded_message:134-136`)
and the hierarchy has exactly one constructor (`:47-54`). So the arm as first written would record
*"the gate declined this note"* — with its one typed field `None` — for a lock timeout, a corrupt
frontmatter fence, or a failed commit. Two consequences, and the first is why this is not cosmetic:

1. **`AC-2`'s fourth conjunct would lose its discriminating power in the same round it acquired it.** The
   clause asserts *a counted, typed refusal record at D8*. A fixture that hands `apply_fixes` an issue for
   a note whose frontmatter fence does not close — no dirty name anywhere — produces exactly that record,
   from `parser.py:96`, on a build where **no gate call exists at D8 at all**. `AC-1`'s wall cannot rescue
   it: the wall proves the arm CALLS, PASSES and is placed `in-lock`, never which exception the observable
   record came from. That is the *control with no discriminating power* shape five ac-red-team rounds and
   three architectural rounds have closed elsewhere in this set, arriving one last time through a
   criterion's ORACLE rather than through its quantifier.
2. **It is also a live diagnostics regression, independent of any fixture.** A lock timeout or a failed
   commit prints `Fix error on <name>: …` today (`:902-903`); under the wide filter it would print a
   refusal line instead and be counted as *"the package declined this note"* — a real IO failure moved out
   of the channel an operator reads for IO failures. `ExternalWriteConflict` names *"an external writer
   (Obsidian, another process) landed mid-mutation"* in its own docstring (`errors.py:92-95`), which is the
   ordinary condition of linting a vault that is open, so this is the likeliest of the four to fire rather
   than the cheapest to plant.

**The repair, decided here on the same authority the record-and-continue shape was: the refusal gets its
OWN type.** This item adds one class to the hierarchy — `NameGateRefusal(LoudFailError)`, a leaf beside
its siblings, declaring no `__init__` of its own exactly as `StaleEntityWrite` and `NoteAlreadyExists` do
not (`errors.py:84-89`, `:98-103`) — and D8's arm catches THAT. **Its parent is `LoudFailError` DIRECTLY
and never `NoteParseError`**, and that is a requirement rather than a preference: `NoteParseError`'s
subclasses are what `base._skip_reason` maps to a skip reason (`base.py:_skip_reason:40-46`) and what
`_note_skip` files into the repository's queryable skip surface (`base.py:266-274`), so a refusal parked
under it would read as *"this note could not be loaded"* — the note is perfectly loadable; a WRITE was
declined. The catch becomes exact by construction
instead of by an attribute probe on a base-class catch, which is a detecting check where a type makes the
miss impossible; the class already earns its keep on the same ground `StaleEntityWrite` does (the
distinction is visible to a caller and a caller acts on it); and it costs one source literal in `REASONS`
(`errors.py:REASONS:110-127`), which this item was already obliged to add (`## Carried Forward`). The
rejected shape is `except LoudFailError as exc:` with `if getattr(exc, "pattern", None) is None: raise` —
one line shorter, and it re-derives at runtime what a type states at import.

**The class this closes, stated as one rule over the whole surface rather than as this arm's fix**
*(WI-226; the generator is **a handler or an oracle discriminating on a SUPERTYPE in a frame that already
raises other members of it**)*. Swept: the package has seven `except LoudFailError` sites — `writer.py:341`,
`:393` and five in `person.py` (`:1598`, `:1700`, `:1819`, `:1899`, `:1968`) — and **every one of them
re-raises**, so its filter width is unobservable. D8's is the first that ABSORBS. Hence the rule, which is
total over the surface and makes the unenumerated case loud rather than assumed:

> **A handler that RE-RAISES may filter on the hierarchy root; a handler that ABSORBS — records, counts,
> logs and continues — must filter on the exact refusal type.** The same rule binds the criteria: every
> oracle that asserts the gate refused names `NameGateRefusal` and its `pattern`, never `LoudFailError`.

The next level down — the artifacts each such assertion names — is swept in the round-13 fold's
class-shaped fold, together with the one place a new hierarchy member is read by TYPE elsewhere in the
package (`base.py:_skip_reason:40-46`, whose `isinstance` chain is total with an *"unreadable"* fallback
and which sits on the LOAD path the gate never reaches).

### Finding F — the concrete failure this closes

Not hypothetical, and **no longer only read — EXECUTED** *(round-9 fold; the conductor ran it against a
throwaway tmp vault, `## Conductor Booking`)*. `repo.save(Person(name="Dave/Bob"))` →
`filename = f"@{name}.md"` (base.py:381) → `write_markdown_file` → the call SUCCEEDS, and afterwards the
disk carries four artefacts:

```
<vault>/@Dave/                                        ← the stray directory
<vault>/@Dave/.obsidian-schemas-locks/                ← the lock home, created INSIDE it
<vault>/@Dave/.obsidian-schemas-locks/48bc….lock
<vault>/@Dave/Bob.md                                  ← the note, path-mangled
```

A spurious directory and an invisible note, from a name `NameValidator._PATH_HOSTILE_RE`
(name_validation.py:95) already knows how to reject and simply never sees on this path. This is the
AC-2 fixture.

**Two corrections the execution forces on the sentence this Finding used to carry.** It named
`vault_io.ensure_dir(file_path.parent)` (writer.py:273) as the mkdir that creates `<vault>/@Dave/`.
That call does run, but it is not the FIRST one: `note_lock` (`writer.py:209`) has already `mkdir`ed
the sentinel's home (`vault_io.py:400`, defaulting to `target.parent` at `:350`) fifty-seven lines
earlier, which is why the lock debris is inside the stray directory rather than beside it. So (1) the
promise is unmeetable by any gate at the convergence point, and the fix is the **hoist above
`note_lock`** Dave ruled in (`## Conductor Preconditions`, precondition 1; derived in Finding B's
round-9 subsection); and (2) the defect is **not prophylactic** — it succeeds today, so the vault may
already contain notes and directories of this shape, a population no count run or owed can see. That
number is query **G5** in `## Grounding Still Owed`, and it bears on `AC-3` rather than on `AC-2`,
because a note at `<vault>/@X/Y.md` carrying `name: X/Y` is legacy-dirty and, once the gate lands, is
unrepairable through any door in this package.

### Finding G — phone write-back is the same defect the mint named only for email

`_writeback_identifier` tests membership with a raw `phone not in (person.phones or [])`
(person.py:1208). `normalize_phone` and `phones_match` (person.py:129, :148) exist and are bypassed,
so `"+44 7739 341679"` and `"+447739341679"` both land as separate entries on the same person —
identically the N3 corruption, on the other identifier kind. It is inside the Intent's wording
("unnormalized address"), it is one line from the email fix, and leaving it out would ship a
half-closed door. **Recommended in scope**, with one constraint discovered while reading: `Phone.parse`
(identifier.py:230) normalizes to bare digits, which would destroy the stored `+` display form —
so the rule must be *dedupe on the normalized form, store the display form*, not *store normalized*.
*(Round-5 note: the subsection below rules that the gate uses `normalize_phone` rather than
`Phone.parse`, which does not weaken this constraint — `normalize_phone` is `re.sub(r"\D", "", …)`
(`person.py:145`) and returns bare digits too, so the display form is destroyed by either authority
and the store-display/dedupe-normalized rule stands on the same reasoning.)*

#### Where the phone normalization authority LIVES (new 2026-08-11, round-5 fold)

The round-4 architectural review's blocking issue: this Finding scoped phones in and `## Approach`
named the symbol, but neither asked Finding D's question — *where does this job live, and is there a
second authority* — on the phone side. Re-derived from source this round, the objection holds
exactly:

| Claim | Read from | Result |
|---|---|---|
| `normalize_phone` / `phones_match` are module-level functions inside the REPOSITORY layer | `obsidian_schemas/repositories/person.py:normalize_phone:129`, `:phones_match:148` | confirmed |
| the cycle a leaf gate would close | `person.py:78` imports `.base`; `base.py:19` imports `..writer`; `writer.py:19-33` imports only `errors`, `models`, `parser`, `vault_io` — no repositories | confirmed: `writer.py → gate → repositories.person → repositories.base → writer.py` |
| both ends are imported at package load | `obsidian_schemas/__init__.py:40` (writer), `:72` (repositories) | confirmed |
| `identifier.py` already dodges it once, with the reason in the source | `identifier.py:234-236` — *"Lazy import: keeps the canonical normalizer single-sourced without a module-load circular import once person.py imports the engine"* | confirmed |
| `Phone.parse` imports a refusal the dedupe path does not have | `identifier.py:Phone:228` — the floor is `MIN_DIGITS: ClassVar[int] = 7`, a **ClassVar on `Phone`**, not a module-level symbol, and it has TWO consumers: `Phone.parse` (`:238-239`) and `WhatsAppJID.parse` (`:274`); `normalize_phone` returns the digits with no floor (`person.py:138-145`) | confirmed |

**One fact the review did not have, and it settles the choice.** The deferred import at
`identifier.py:236` is not the only one — there is a **second**, at `identifier.py:272`
(`WhatsAppJID.parse`), reaching the same symbol for the same reason. So the gate would be the THIRD
reach, not the second. And the frame is already named, dated and OWNED in this tree:
`docs/identity-engine-endgame.md:28` (WI-023, stage `idea`, created 2026-07-05) carries it as scope
item 4 — *"**Break the lazy-import cycle**: move `normalize_phone`/`phones_match` (person.py:105-156)
to a small util module so `identifier.py` stops importing backwards from a 1,839-line repo module
(identifier.py:234-236)"* — and the 07-05 campaign lists it on WI-023's row
(`docs/backlog-campaign-2026-07-05.md:62`, "break the normalize_phone cycle"). The architect's
"the FRAME is the suspect" reading is therefore not a new diagnosis; it is a recorded one whose owner
is sequenced **Phase 3, after this Phase-2 item**. This item is what forces the third reach, so the
sequencing is backwards and this is where it gets paid (LESSONS #13 — a third workaround is interest,
not principal).

**Resolution: the authority MOVES to a leaf, and this item makes the move.** A new leaf module
`obsidian_schemas/phone_normalization.py` holds `normalize_phone` and `phones_match` verbatim —
stdlib-only (`re`), no package imports, the same shape as the existing package-level leaves
`name_validation.py` / `name_cleaning.py` / `identifier.py`. Then:

- the gate imports it at module scope — leaf → leaf, no cycle;
- `identifier.py` imports it at module scope too, **deleting both deferred imports** (`:236`, `:272`).
  Stated precisely (architect round-5 note 2, corrected here): after the move `identifier.py` is
  still a LEAF — it names one package sibling and nothing in a layer above it — but it is no longer
  *stdlib-only*, and the purity claim it would then overstate lives in the module **docstring**
  (`:1-29`), not in the import block (`:31-36`). The docstring's own wording is "This module is the
  **pure** layer" (`:9`), which stays true under the move; the sentence to avoid writing in the spec
  is "restores it to stdlib-only", which the move does not do;
- `repositories/person.py` **re-exports both names** (`from ..phone_normalization import
  normalize_phone, phones_match`), so `obsidian_schemas.repositories.person.normalize_phone` keeps
  resolving and its **ten** in-module call sites (`person.py:156`, `:157`, `:244`, `:250`, `:389`,
  `:395`, `:450`, `:461`, `:542`, `:631` — grep confirms exactly those ten) are untouched.

**The delta this choice carries, stated as the review requires — and it is the reason this shape was
chosen over the other two.**

- **Behaviour: none.** The functions move verbatim; `normalize_phone`'s contract is unchanged and
  `Phone.parse`'s `MIN_DIGITS = 7` floor is **never introduced into the dedupe path**. That is the
  whole objection to the delegate-to-`Phone.parse` shape, and relocation dissolves it rather than
  pricing it.
- **Consumers: none.** `normalize_phone` is not re-exported at top level — `__init__.py` pulls only
  the repository classes from the package (`repositories/__init__.py:8-12`, `__init__.py:72-78`) — so
  a consumer must already name `obsidian_schemas.repositories.person`, and the compat re-export keeps
  that path working. The three existing in-tree importers (`tests/test_repositories.py:1868`, `:1872`,
  `:1876`, `:1880`, `:1884`, `:1888`, `:1892`) stay green **unchanged**, which is the check that
  proves the re-export is real rather than asserted.
- **Cross-item:** WI-023's scope item 4 lands early and becomes a no-op. Its item 2 — the open
  question of whether `Phone.key` (raw digits, `identifier.py:248`) can express `phones_match`'s
  UK-0/44 and US-1 equivalence — is **untouched**, which is why `phones_match` moves as a relocation
  and NOT as the gate's dedupe predicate (below). Moving the pair does not decide WI-023's question;
  co-opting `phones_match` into the gate's semantics would.
- **The gate dedupes on `normalize_phone` only.** `phones_match`'s country-code equivalence is a
  looser relation than "same number written differently", and it is exactly the relation WI-023 item 2
  is open on. Finding G's own specimen (`"+44 7739 341679"` vs `"+447739341679"`) is closed by
  `normalize_phone` alone. Scoping the gate to the tighter predicate keeps this item out of WI-023's
  decision.

**The two rejected shapes, named so the choice is falsifiable.** *Delegate to `identifier.Phone.parse`*
— imports the `MIN_DIGITS = 7` refusal onto live stored phones, which is a behaviour change of exactly
the shape Finding D's reconciliation 2 books on the address side and this document books nowhere on
the phone side; it would need a count before it could be chosen, and it makes `AC-4` acquire a refusal
case it does not describe. *A third deferred import inside the gate* — works, costs nothing today, and
is the one the review said it would not take without saying why: it is the third instance of a
workaround whose owning work item already exists, which is how a two-line dodge becomes permanent.
**Because the chosen shape is the relocation, `AC-4` does NOT acquire a refusal case and does NOT join
the re-origination set** — the conditional the review flagged does not fire.

### Finding H — the Tier-1 refusal surface, specified ONCE (new, 2026-08-11 fold)

Re-entry step 4 asks for this as a single object rather than three separate repairs: the branch-unit
reification of the chain, the `empty` refusal outside it, and the sentinel exemption inside it. They
are the same object. Read from source this round:

**The surface is `(branch × sentinel-state)` across BOTH public entry points — not a "pattern
table".** `_raise_on_tier1`'s own docstring says "Walks the Tier 1 pattern table"
(`name_validation.py:_raise_on_tier1:302`), but the body is a hand-written `if` chain: **nine
branches at `:310`, `:320`, `:329`, `:336`, `:343`, `:352`, `:359`, `:366`, `:373`, raising seven
distinct keys** — `_ARROW_CONNECTIVE_RE` (`:329`), `_CALENDAR_PREFIX_RE` (`:336`) and
`_ME_TO_PREFIX_RE` (`:343`) all raise `calendar_prefix`, deliberately, so that "invariant `by_pattern`
reporting stays coherent" (the WI-111 comment at `:326-328`). There is no iterable object anywhere in
the module. Two consequences: the build must **reify** the chain before anything can sweep it, and
the sweep's unit must be the BRANCH — a sweep keyed on the raised key yields seven fixtures, leaves
two branches unexercised, and cannot even say which of the three `calendar_prefix` branches fired.

**Two refusals live outside the chain, and no reification of it reaches them.**

| Refusal | Where | Why the chain does not reach it |
|---|---|---|
| `empty` | `name_validation.py:validate_strict:258-259` **and** `name_validation.py:clean:277-278` | raised by both public entry points *before* either delegates to `_raise_on_tier1` |
| the sentinel EXEMPTION | `name_validation.py:253-254` (`validate_strict`) and `:274-275` (`clean`) | an early `return` above everything, including the `empty` check — it suppresses the whole chain |

So the surface is **ten refusals over ten branch-sites, gated by one exemption**, and the
reification must model all three parts explicitly. The ordering is safe as it stands and should be
preserved: `_PURE_DIGIT_RE` is `^\+?\d+$` (`:111`), which cannot match an empty or whitespace-only
string, so the exemption sitting above the `empty` check cannot swallow an empty name.

**`empty` is a refusal this item INTRODUCES, not one it routes.** `create_stub` guards its validator
call with `if name and name.strip():` (`person.py:1405`), so `empty` is unreachable on the create
path and has never fired in production. On the write path it is reachable immediately:
`write_markdown_file(path, extra_fields={"type": "person", "name": ""})` is a legal D1c call that
succeeds today and is refused once the gate exists. That is new behaviour on a code path with no
prior art behind it, which is why it must be signed explicitly rather than swept up by a
reification.

**The sentinel is a PAYLOAD rule, not a new gate input.** The architect's round-3 ruling resolves the
round-3 hand-back's "the signature is one input short", and the resolution re-derives from source:
`create_stub` computes the flag itself, from the payload — `_allow_phone_sentinel = bool(phone) and
name.strip().lstrip("+").isdigit()` (`person.py:1406`), passed at `:1407` — and at D3 the phone is
in the record being written (`person.py:1450`, `:1456`). So the rule the gate needs is:

> A pure-digit name is permitted when the record it is introduced with carries a phone.

computed from what the gate already receives. That is inside the DECLARE line (payload), not outside
it (environment); it needs no new parameter and no thread through the generic layer, and the settled
gate signature ("the introduced fields plus the entity type") stands unwidened.

Three consequences the re-origination must STATE rather than let the build discover:

1. **`pure_digit_name` is not unconditional even on a declared-person write.** That is what makes
   `AC-2` and `AC-3` wrong as signed: `create_stub` reaches `self.save(person, …)` at
   `person.py:1475` — D3, and D1a beneath it — carrying a name that matches a Tier-1 pattern, by
   design, for the WI-083 phone-only-stub path its own docstring documents (`person.py:1358-1361`).
2. **Under Finding C's delta rule, `update_fields(person, {"name": "+447…"})` that introduces the
   name WITHOUT the phone is refused**, because the phone is stored, not introduced. Rare and
   defensible, and it must be written down rather than met at build time.
3. **The population is 3, and it is live**: the two live stubs `@+12068523646.md` and
   `@447950289840.md` plus one quarantined copy (`## Conductor Rulings & Grounding`). Small, real,
   and the number the exemption is justified against. These are also the *only* two live
   Tier-1-dirty stored names in the vault (Finding C, re-dated), so the exemption and the delta rule
   are protecting the same two records by two different mechanisms — the exemption is the one that
   actually does the work.

**Which entry point the gate calls, and what it does with the return value** *(new 2026-08-11, round-8
fold, answering architect round-7 note 1 — the question `## Approach` and owed question 4 both leave
unstated, and which the identity rule now forces).* Neither public entry point is a predicate: both
apply Tier-2 repairs and return the repaired string, and both SENTINEL arms return `name.strip()` as
well (`name_validation.py:253-254`, `:274-275`, `:283-297`, `:265-266` — all re-read this round). So the
choice is not between them:

> The gate consumes the Tier-1 DECISION and **discards the repaired string.** It calls one entry point
> for its raise behaviour and emits the name it was HANDED, byte-for-byte, on the accept path.

`validate_strict(name, allow_phone_sentinel=…)` is the one to call — `clean`'s extra product is exactly
the `CleanResult.repairs_applied` record the gate must not act on, so calling it would put the discarded
value in front of the next reader as if it were available. Two properties this preserves rather than
changes, both from the source: the Tier-1 chain still judges the STRIPPED form (`:257` → `:262`, and
`:288-290`'s comment says why that ordering is deliberate), so a name that is dirty only after a strip
is still refused; and the sentinel exemption is still evaluated on `name.strip()` (`:253`), so the
three live sentinel records (`## Conductor Rulings & Grounding`) are unaffected. What changes is only
what comes back out. `create_stub` keeps calling `clean` and keeps storing its output (`person.py:1407`,
`:1413`) — above the filename derivation, which is where that repair has always belonged and is the
reason it has never produced a divergence.

**The entity-agnostic / person-specific partition is MOOT under rule (ii)** and is not specified
here. It was required only under shape (i), where person-tuned patterns would have evaluated
undeclared writes. Under refuse-undeclared no Tier-1 pattern ever evaluates an undeclared write, so
there is nothing to partition. Recorded explicitly because two gate rounds ordered the partition as
work; it is cancelled by the ruling, not forgotten.

### Finding I — the identifier container is THREE fields, not two (new, 2026-08-11 fold)

`AC-4` asserts that identifiers "land in `emails[]`/`phones[]` in the same normalized form". The
behaviour it must not regress spans a third field, and `aliases[]` is on BOTH sides of it. Read from
source:

- `_normalize_address_fields` walks `person.emails` (`person.py:1304-1317`) **and** `person.aliases`
  (`:1323-1343`).
- On the aliases pass it treats each alias entry as a possible address: `_extract_email_and_name`
  splits it, the extracted address is appended to `person.emails` (`:1328`) and the display half is
  kept in `aliases[]` (`:1331-1333`). So `aliases[]` is an identifier INPUT.
- Display names extracted from `emails[]` are then appended to `aliases[]` (`:1339-1342`), and the
  list is rebound at `:1343`. So `aliases[]` is also an identifier OUTPUT.
- `create_stub` seeds `aliases=[email]` with a bare address (`person.py:1448`), so the
  aliases-as-identifier-input path is not hypothetical — it is the path parked defect 2 describes.

**Consequence:** a gate that normalizes `emails[]` and `phones[]` and leaves `aliases[]` untouched
satisfies `AC-4` as signed while `aliases: ["Al B <A@B.com>"]` — handled today at
`person.py:1323-1337` — writes raw through every arm, silently losing behaviour D3 has now.
`### Examples of done` mentions `aliases[]` once, on the output side, which is what makes the
omission read as deliberate scoping rather than a gap. It is not scoped anywhere in the criterion.
This is a re-origination obligation on `AC-4` — **but read the next subsection before writing that
clause**: the obligation is not "normalize `aliases[]` everywhere", and asserting it flat is a
criterion the design cannot meet on the six dict-shaped arms.

**One bounded interaction the spec owes, discovered while reading:** `update_fields` itself
introduces an `aliases[]` entry the caller never passed — on a name change it appends the old file
stem (`base.py:443-448`). That entry is a NAME, not an address, and `_extract_email_and_name` returns
`("", "")` for it (`person.py:1292-1298`), so it would be preserved either way.

> **Corrected 2026-08-11 (fold, round 7), per architect round-6 note 1 — and the correction is worth
> more than the sentence it fixes.** The superseded text said the stem "is a door-introduced field and
> therefore inside the delta the gate judges". Re-read from source, it is not: the stem is appended to
> the **parsed** `frontmatter["aliases"]` (`base.py:445-448`), while `updates` — the delta the gate is
> handed — is the caller's own dict, merged into that frontmatter only afterwards at `:451`. A gate
> handed the delta never sees the stem at all. The OUTCOME the finding asserted is right (it passes
> through unchanged), so nothing behavioural turns on it; the sentence would just have sent the build
> looking for the entry in the wrong object. The rule that survives, unchanged, is: a non-address
> `aliases[]` entry the write DOES carry passes through unchanged, which is what the code does today.
>
> **One adjacent pre-existing defect the same reading exposes, PARKED not scoped** (architect round-6
> note 1, second half): an `update_fields` call carrying BOTH `name` and `aliases` in `updates` loses
> the stem the door has just appended, because `:451`'s key replacement overwrites the very list
> `:448` mutated one branch earlier. It is parked defect 1's neighbourhood — `update_fields` renaming
> the entity without renaming the file — not this item's, and the gate neither causes it nor fixes it.
> Recorded so the build meets it as a known adjacency rather than as a surprise.

#### The obligation is a cross-field MIGRATION, and it splits by arm shape (new 2026-08-11, round-6 fold)

> Answering the round-5 architectural review's blocking issue. Its reading is correct and is
> re-derived from source below; the fold ADDS the second migration, which the finding names only in
> one direction and which lands in signed text. Nothing above is retracted — `aliases[]` really is on
> both sides of the property. What changes is what "add it to the container" is allowed to MEAN.

**The behaviour on the input side is not normalization of an alias entry. It is a MOVE between
fields.** Re-read from source this round:

- `_normalize_address_fields` walks `person.aliases`, splits each entry, and appends the extracted
  address to a *different* list — `person.emails.append(email)` (`person.py:1328`) — keeping only the
  display half in `aliases[]` (`:1331-1333`).
- The move is guarded by `seen_emails_lower` (`:1327`), a set populated by the **`emails[]` pass of
  the same call** (`:1303`, `:1307-1316`). That dedupe is what stops the migration minting a second
  copy of an address the person already has.

Three settled things collide on that, and the collision is only visible once `aliases[]` is in the
container. All three are carried-forward rulings, not new positions:

1. **The gate has no `existing` parameter** (architect ruling, rounds 1–5, `## Carried Forward`). On a
   write introducing only `aliases`, the gate cannot see the stored `emails[]`, so it cannot perform
   `:1327`'s dedupe at all.
2. **Finding C's delta rule** — judge what the write INTRODUCES, never what it preserves. `emails[]`
   on such a write is preserved, not introduced.
3. **The gate's output contract** (`## Approach`) — it returns the fields it was HANDED, validated and
   normalized, or refuses. Emitting a key the caller did not pass is outside it.

**Doing it anyway is a new corruption class, which is why this is a design fact and not a preference.**
`update_fields` merges by key REPLACEMENT — `frontmatter.update(updates)` (`base.py:451`), re-read this
round. A gate handed `{"aliases": ["Al B <a@b.com>"]}` that emitted `emails: ["a@b.com"]` would not
append to the stored list; it would **replace** it. Concrete: a canonical carrying
`emails: ["dave@acme.com", "d@personal.com"]` receives `update_fields(person, {"aliases": ["Al B
<a@b.com>"]})` — D4, inside AC-1's derived set — and comes back with one email, in an item whose whole
purpose is closing a corruption class. `update_frontmatter_field(path, "aliases", …)` (D5,
`writer.py:332`, single-key replacement into the parsed note) and the D1b/D1c dict arms have the same
shape.

**Where it IS expressible.** On the entity-shaped arms the gate receives the projection of the whole
record — `model_to_frontmatter` iterates `model_class.model_fields.keys()` and emits every declared
field (`writer.py:111-116`), so `emails[]`, `phones[]` and `aliases[]` are all in its input, `:1327`'s
dedupe has its set, and under Finding C an entity write's delta IS the whole record, so nothing the
migration touches is merely preserved. D1a **and the D3 rider** *(round-7 fold: was "D1a/D2/D3" — D2
and D3 are no longer arms, and the rider is the frame that holds the whole record on the save path)*
are also exactly where `_normalize_address_fields` runs today (called from `PersonRepository.save` at
`person.py:1269`), so the behaviour Finding I says must not regress is preserved where it already
lives, and nothing is lost.

**So the rule, stated once and scoped by arm shape:**

> The alias-borne-address migration is an **entity-arm** behaviour. On a **dict-shaped** arm the gate
> normalizes only the fields the write carries, in place, and NEVER emits a field the write did not
> carry.

**One correction to what "in place" can mean on `aliases[]`, forced by the same source.** The
architect's direction says the dict arm "normalizes the `aliases[]` entries it is handed IN PLACE".
Read against `_extract_email_and_name`, in-place normalization of an *address-bearing* alias entry
would DESTROY data rather than normalize it, because the split is only half the operation:

- `"Al B <a@b.com>"` splits to `("a@b.com", "Al B")` (`person.py:1291-1293`). Keeping the display half
  without the migration puts the address nowhere — it is gone from both fields.
- A BARE address alias — `create_stub`'s seed, `aliases=[email]` (`person.py:1448`) — splits to
  `("a@b.com", "")`, and the empty display half means the entry is DROPPED (`:1331-1333` appends
  nothing). Without the migration that is a deletion.

So on a dict-shaped arm an `aliases[]` entry that parses as an address is passed through
**UNCHANGED**, and the only `aliases[]` rule that survives there is the one Finding I already states
for non-address entries: pass through unchanged. Net: on dict-shaped arms `aliases[]` is outside the
normalized container entirely, and the gate's obligation on it is to leave it byte-identical. That is
strictly better than today (today every dict arm writes `aliases[]` raw as well) and it is the only
reading of "in place" that does not introduce data loss.

**The mirror migration — new this round, and it lands in SIGNED text.** The architect's finding names
the aliases→emails direction. There is a second, in the other direction, with the identical defect:

| # | Migration | Source | Guarded by |
|---|---|---|---|
| M1 | an `aliases[]` entry that is an address → appended to `emails[]` | `person.py:1328` | `seen_emails_lower`, populated by the `emails[]` pass (`:1303`, `:1307-1316`) |
| M2 | the display half of an `emails[]` entry → appended to `aliases[]` | `:1311` collects, `:1339-1342` appends, `:1343` rebinds | `seen_aliases_lower`, populated by the `aliases[]` pass (`:1331`, `:1335`) |

M2 fails on a dict-shaped arm for exactly M1's reason and with exactly M1's blast radius: a gate
handed `{"emails": ["Al B <a@b.com>"]}` that emitted `aliases: ["Al B"]` would REPLACE the stored
aliases list via `base.py:451`, destroying every other stored alias on that person. So M2 is an
entity-arm behaviour too, and on dict-shaped arms the extracted display half is DROPPED.

**What that costs, stated exactly, because it is the part that touches signed text — and the round-6
pricing of it was WRONG.**

> **Corrected 2026-08-11 (fold, round 7), answering the round-6 data audit's blocking finding.** The
> superseded text read: *"It is not a regression — today no dict arm normalizes anything, so today the
> display half is not in `aliases[]` either, and the entry is stored raw on top of that."* That
> compares the new behaviour against `aliases[]` alone, and `aliases[]` is not where the display half
> lives today. **Today a dict-arm write stores `"Al B <a@b.com>"` VERBATIM, so the display half is on
> disk** — embedded in the `emails[]` entry, and recoverable by anything that re-splits it, which is
> exactly what `_normalize_address_fields` does on the next entity write. Under the dict-arm rule that
> same write stores `"a@b.com"` and drops `"Al B"` with no destination, so the display half leaves the
> note entirely. That is not "not migrated"; it is a DELETION, and it is performed by this item's own
> fix. The audit is right, I re-derived it from source, and the honest accounting is below.

**The deletion's blast radius is a whole list per write, not one entry.** `_writeback_identifier`
sets `updates["emails"] = person.emails` — the WHOLE stored list, loaded from the note
(`person.py:1206-1207`) — and routes it through `update_fields` (`:1217`), which is D4. So a single
reuse-branch write-back passes **every** stored `emails[]` entry on that person through the gate at a
dict-shaped arm, and every one of them still carrying a display half loses it in that one write.
`update_frontmatter_field(path, "emails", …)` (D5) and the D1b/D1c arms have the same shape. Re-read
from source this round: `person.py:1204-1217`, `base.py:451`.

**The at-risk population is nameable, and it is NOT G2's `emails[]` extracted cell.** A person
previously saved through `PersonRepository.save` has already had M2 run, so the display half is
already in `aliases[]` and losing it from `emails[]` costs nothing. The entries that lose real
information are those whose display half is **absent from that note's own `aliases[]`** — notes never
re-saved through the repository since WI-109. That intersection is one more column on a query already
owed and already reported per field; it is booked as such in `## Grounding Still Owed` (G2) rather
than estimated here.

**What is NOT in doubt.** The arm-shape split itself is forced, not chosen: the all-ten-arm merge
table below shows no arm anywhere appends, so emitting the destination key on a dict arm would REPLACE
the stored list (`base.py:451`). Both available options are lossy — emit and destroy the stored list,
or normalize and drop the display half — so the question is which loss and how big, and that is a
number, not an argument. What the criterion must not do is book the second one at zero.

**Where it lands in signed text**, unchanged from round 6 except in its price: the second half of one
`### Examples of done` scenario — *"**when** the reuse branch writes back `"Al B <A@B.com>"` …
**then** `emails[]` and `phones[]` each still hold exactly one entry, **and `"Al B"` has landed in
`aliases[]`**."* That scenario's write is `_writeback_identifier` → `update_fields`
(`person.py:1204-1217`) — D4, a dict-shaped arm — so under the arm-shape split the first clause holds
and the second does not. `### Examples of done` is inside the `ac-signoff` hash span (it is a `###`
subsection of `## Acceptance Criteria`), so this is a re-origination obligation, recorded in
`## Re-origination Brief` and not edited here. **And the choice between its two closures is no longer
cosmetic:** closure (b) — have `_writeback_identifier` pass `aliases` in the same `updates` dict —
closes the deletion too, for that caller, because the display half then has a destination on the same
write. Closure (a) is free on the example and leaves the deletion in place. That is Dave's call; the
brief now states the consequence rather than presenting the two as equivalent.

Two honest ways out exist and BOTH are Dave's to pick, not mine — recorded so the one round can take
either without another loop: (a) accept the narrower promise and re-word the example's second clause
to the entity path; or (b) keep the promise by changing the CALLER — `_writeback_identifier` holds the
whole `Person` object, so it can take the display half back from the gate's result and pass `aliases`
in the same `updates` dict, which is a one-caller change inside this package and needs no widening of
the gate's output contract. (b) preserves the signed example verbatim and is the smaller behavioural
surface; (a) is free. Neither is available to a generic `update_frontmatter_field(path, "emails", …)`
caller, which is why the arm-shape split stands under both.

**One consequence for the code being replaced, which the architect asked be stated in the same pass.**
`_extract_email_and_name` is an INNER function of `_normalize_address_fields` (defined at
`person.py:1286`, nested inside the static method at `:1277-1278`), so Finding D's "REPLACE" of that
site is an edit to the ENCLOSING method, not a local swap — and the enclosing method's fate is what
this issue decides. **It is SUBSUMED:** `_normalize_address_fields` is deleted, its per-entry split
becomes the shared splitter, its two migrations become the gate's entity-arm behaviour, and
`PersonRepository.save`'s call at `person.py:1269` goes with it. Two riders the build must carry:

- **The in-model mutation.** `_normalize_address_fields` mutates the caller's `Person` in place today,
  so after `repo.save(person)` the caller's own object is normalized. The gate returns a dict and does
  not touch the model. To keep today's observable behaviour, `PersonRepository.save` writes the gate's
  normalized values back onto the entity before delegating to `super().save()`. At D1a called
  directly there is no model mutation and never was, so nothing regresses there.
- **The gate must be IDEMPOTENT**, and this is where it matters. One `PersonRepository.save` call
  invokes the gate TWICE — once as the D3 rider above, and once at D1a (`writer.py:256-257`) on the
  projection of the entity the rider has just normalized. *(Round-7 fold: this read "THREE arms —
  D3 → D2 → D1a" before D2 and D3 left the arm set. One invocation is gone; the requirement is not,
  because two passes over one write still have to agree.)* Both migrations are idempotent by
  construction: after the first pass an
  alias is display-only, so `_extract_email_and_name` returns `("", "")` for it (`:1298`) and M1 is a
  no-op, and M2's `seen_aliases_lower` check (`:1340`) finds the display half already present. The
  build must not weaken that — the invariant to pin is *gate(gate(x)) == gate(x)*.

### Approaches considered

| | Approach | Verdict |
|---|---|---|
| A | Hang the checks on `vault_io`'s doors (the mint's named mechanism) | **Rejected** — Finding A. The structure is gone by then; the check would have to reconstruct it. |
| B | Put the gate inside `write_frontmatter` — one function, total coverage, zero routing | **Rejected** — Finding C. It sees only the merged record, never the delta, so it cannot distinguish "introduced a bad name" from "preserved one", and bricks the repair tools. It also overloads a pure serializer with a semantic contract, and would fire on any consumer using it to render a preview. |
| C | A Pydantic `field_validator` on `Person.name` | **Rejected** — it fires on READ as well as write, so every existing dirty note stops model-validating, drops out of the cache into the skip surface, and `find_or_create_stub` mints a duplicate for someone Dave already has. That is the dup-proliferation class WI-020's skip surface was built to fight (base.py:27-38). It also misses D4–D6/D8 entirely, which write a dict and never build a model. |
| D | Add the two checks at each of the eight doors | **Rejected** — the sixth-door problem. It is precisely what the 07-05 routing note warned against, and D8 (`lint_vault`) proves the door set grows outside the package. |
| E | Ship the semantic refusal behind an observe/enforce env knob, mirroring `OBSIDIAN_SCHEMAS_WRITE_GUARD` | **Rejected, with pushback.** It is a second knob to forget, in a system where WI-004's D6 already rules one reader per setting, and where `observe` is a security-relevant mode that needed its own announce-once machinery (vault_io.py:202) to stop being invisible. The delta rule already bounds the blast radius to writes that INTRODUCE a violation, which is the population that should fail. If the consumer audit (below) shows a live caller that legitimately introduces dirty names, that is a bug in the caller, and a knob would hide it. |
| **F** | **One gate module + routing at the doors + a DERIVED wall proving the routing is total** | **Chosen.** |

### Discovered adjacent defects — named, and deliberately PARKED

Found while reading; each is real, none is this item, and absorbing them would blur a boundary item
into a person.py cleanup:

1. **`update_fields` renames the entity but never the file.** base.py:443-448 appends the old stem to
   `aliases` and writes the new `name:` into the frontmatter, but the note stays at `@Old.md`. A
   later `save()` of the reloaded entity computes `@New.md` (base.py:381) and mints a SECOND note
   for one person. A perfectly valid name is enough to trigger it, so this item's validation does
   not touch it. Candidate follow-on work item.
2. **`create_stub`'s `aliases=[email]` is silently erased by its own save.** create_stub seeds
   `aliases` with the bare email (person.py:1448); `_normalize_address_fields` then reads that entry
   as a wrapped address, moves it to `emails[]` where it already is, and drops the alias
   (person.py:1323-1337). Pre-existing and arguably correct, but undocumented — worth a comment
   during the build, not a scope extension.
3. **`CompanyRepository.create_stub` has no validator at all** and still runs the mangler regex the
   Person side deleted. That is WI-022, already open. This item stays **Person-only**; company names
   have a different contract (a company suffix is legitimate there and is Tier 3 here).
4. **`roundtrip_file` locks a path it never existence-checks** *(new, round-9 fold; architect round 8
   note 1)*. `writer.py:414-417` acquires `note_lock` with no guard, unlike its three siblings
   (`base.py:432-433`, `writer.py:320-321`, `:374-375`), so calling it on a path that does not exist
   creates the sentinel directory and lock file (`vault_io.py:400`, `:410-414`) and only then fails in
   `read_note`. Same shape as Finding F's stray directory, one door over. D7 introduces nothing — its
   gate call is handed an empty delta and cannot refuse *(round-10 correction: this entry read "D7 has
   no gate call", which contradicted `## Approach` and `AC-1`'s eight-arm floor; routing and guarding
   are independent facts)* — so this item neither causes nor fixes the unguarded lock. Recorded so the
   round-9 scoping note is not misread as a claim that D7 is existence-guarded like D4/D5/D6. Candidate
   follow-on, cheapest as one `if not file_path.exists(): raise FileNotFoundError` matching its
   siblings — **and that is now the SAME line this item adds to `apply_fixes`** *(round-10 fold,
   architect round-9 note 1)*, so the follow-on copies a statement already in the tree rather than
   inventing one. Deliberately still parked: adding it would flip D7's required placement from `above`
   to `in-lock` in the wall's table, and nothing in this item needs that.
5. **`Person.whatsapp` is a fourth identifier-bearing field and NOTHING normalizes it** *(new,
   round-11 fold; found by sweeping the level below this round's class rather than reported by a gate)*.
   `models.py:Person:83` declares `whatsapp: str = ""`, and `identifier.py` carries a typed parser for
   exactly that value — `identifier.py:WhatsAppJID.parse:264`, which normalizes through
   `normalize_phone` at `:272-273` and applies the `Phone.MIN_DIGITS` floor at `:274`. Read from source
   this round, no path this item routes ever touches it:
   `_normalize_address_fields` walks `person.emails` and `person.aliases` only
   (`person.py:1300-1343`), and `_writeback_identifier` sets `updates["emails"]`/`updates["phones"]`
   only (`person.py:1204-1210`). So the gate's three-field container — `emails[]`, `phones[]`,
   `aliases[]` — is **not a hand-list with an unnoticed hole**: the fourth candidate exists, is named
   here, and is genuinely outside, because preserving today's behaviour on a field nothing normalizes
   is not a regression and a JID is not an RFC 2822 address (Finding D's job partition). A dict arm CAN
   introduce it — `update_frontmatter_field(path, "whatsapp", "+44 7739 341679")` is legal — and the
   gate will pass it through unnormalized, exactly as every door does today. **Deliberately parked:**
   widening the container a fourth time would add an item to Dave's round for a defect this item
   neither causes nor worsens, and the typed-parser adoption is identity-engine territory (WI-023 /
   WI-125), not a write-door question. Candidate follow-on; recorded so the next reader does not
   discover it as a finding.

### Constraints & dependencies

- **WI-004 is the floor, not the home.** `vault_io` owns the mechanical door; this is the semantic
  layer above it, and it must not put semantics inside that module — doing so would give the one
  file the routing wall exempts a second reason to exist. **And "above" is an ORDERING, not only a
  layering** *(round-9 fold, per architect round 8's boundaries dimension)*: the mechanical floor
  touches the filesystem the moment it is entered — `note_lock`'s sentinel `mkdir` at
  `vault_io.py:400` — so the semantic layer must run BEFORE that floor is entered, not inside it.
  Both placements are individually right and they composed into "the mechanical door has already
  touched the filesystem before the semantic door gets to say no". This sentence implied the ordering
  from the start; Finding B's round-9 subsection is where it is finally stated.
- **The wall belongs in `tests/derivations.py`.** That module is the only file permitted to name
  `ast` (derivations.py:14-17), and its existing vocabulary — `_is_write_call` at :238,
  `functions_reserializing_parsed_frontmatter` at :294 — is most of the predicate this item needs.
  A private re-implementation elsewhere is already detectable by AC-7 of WI-020.
- **Consumer blast radius is real and already flagged.** HAL9000, exocortex and orchestrator install
  this library with `pip install -e`, and the 07-05 campaign lists WI-021 under "consumer-facing type
  decisions … consumers lose the ability to write unvalidated names"
  (`docs/backlog-campaign-2026-07-05.md:98`). The spec owes a consumer audit of the non-`create_stub`
  write callers in all three repos, in the shape WI-024 used.
- **The phone normalizer relocates first, and it partly overlaps WI-023** (new, round-5 fold).
  `obsidian_schemas/phone_normalization.py` is a prerequisite of the gate, not a rider: a leaf gate
  cannot name `repositories/person.py` (Finding G). The move is WI-023's own scope item 4
  (`docs/identity-engine-endgame.md:28`), and WI-023 is at stage `idea`, sequenced Phase 3 — after
  this Phase-2 item. **This item lands item 4; WI-023 keeps the rest**, including item 2's open
  `Phone.key`-vs-`phones_match` question, which this item deliberately does not touch. Worth stating
  because the next reader of WI-023 will find item 4 already done and should not read that as scope
  drift.
- **Effort: RE-DERIVED from current scope, 2026-08-11 (round-11 fold), per architect round 10's
  non-blocking note — and it is larger than the number this bullet carried.** *"One to two sessions"*
  was written at round 3, before the phone leaf module (round 5), the subsumption of
  `_normalize_address_fields` (round 6), the arm-shape split on two cross-field migrations (round 6), the
  name-identity rule (round 8), the hoist (round 9), the D8 existence guard (round 10) and the wall's
  growth from a per-arm PREDICATE to a per-arm TRIPLE (rounds 3, 9, 10). Each increment was priced
  honestly and small in its own round; nobody re-added them, and the estimate is the one number in this
  document that never moved while its subject did. Re-derived from the scope as it now stands, in units
  a builder can check rather than one number to be optimistic about:

  | Piece | Size | Note |
  |---|---|---|
  | `obsidian_schemas/phone_normalization.py` + re-export + two deferred imports deleted | **small** | two pure functions moved verbatim; verified by `tests/test_repositories.py:1868-1893` staying green UNEDITED |
  | The gate module: Tier-1 branch-unit reification (Finding H), payload-derived sentinel, splitter on `Email.parse` owning the parens form, three-field container with the arm-shape split, name-identity predicate, phone dedupe-normalized/store-display, `REASONS` literal + `pattern` attribute | **large** | the substance of the item; the reification alone has no table to sweep today |
  | Routing eight arms + the D3 rider, including the D1 hoist above `note_lock` and D5's CONSTRUCTED delta | **medium** | no new call sites beyond the eight + rider; ~10 moved lines in `write_markdown_file` |
  | `lint_vault --fix` delta threading + the existence guard | **largest single piece**, unchanged in that ranking across four architectural rounds | the fix loop mutates `fm` in place across its `elif` branches and serializes the whole dict (`lint_vault.py:876-882`), in `scripts/`, outside the package |
  | The derived wall: the new ARM predicate, plus three per-arm arguments (calls / passes / placement), the planted multi-branch positive control, the near-miss, and the RED consistency leg | **medium-large** | the one genuinely new piece of AST work; the battery shape is copied from `tests/test_write_routing.py:1-18` |
  | The five AC batteries, now including `AC-3` over five arms with synthetic fixtures | **medium** | `AC-2`/`AC-4` are each two passes over the derived set |

  **Honest total: three to four sessions**, with the `--fix` threading and the wall's third argument the
  two pieces most likely to overrun. This changes no design decision — it is recorded because carrying a
  round-3 number past six scope increments is how a plan ships an estimate nobody believes. The pieces
  below are unchanged and are what the table above prices.
- **Composition:** **Two** new modules — the gate and the phone leaf — routing at
  **eight arms across six functions** plus one rider at `PersonRepository.save` *(corrected round-7
  fold: two of the previously-counted ten bind no dict and are not arms; taking the architect's shape
  (b) makes the derived set exactly what one stated predicate resolves and REDUCES the work by two
  call sites and a second predicate; **round-8 fold: shape (b′) reduces it again** — declaring the
  gate's name output an identity DELETES a rider obligation rather than adding one, since there is then
  nothing on that field to write back; **round-9 fold: the gate-above-`note_lock` hoist adds ten moved
  lines in one function and one argument to the wall's per-arm assertion — it changes no arm's identity
  and creates no new call site**; **round-10 fold: making that argument derivable adds ONE statement —
  the existence guard in `apply_fixes` above `lint_vault.py:819` — in a function the delta threading
  already opens, and DELETES a clause from the rule rather than adding one**)*, one derived wall, the splitter consolidation *(which is the
  SUBSUMPTION of `_normalize_address_fields`, not a local swap: its inner `_extract_email_and_name`
  becomes the splitter and its two cross-field migrations become entity-arm gate behaviour —
  Finding I)*, and the invariant tests — plus two pieces the gate rounds added and priced: the
  **branch-unit reification of the Tier-1 chain** (Finding H; there is no table to sweep today),
  and the `lint_vault --fix`
  delta threading, which both architectural rounds call the single largest piece of unglamorous work
  in the routing (the fix loop mutates `fm` in place across its `elif` branches and serializes the
  whole dict at lint_vault.py:876-882, with no delta object to hand the gate, in `scripts/` outside
  the package). The phone relocation itself is small — two pure functions, one re-export, two
  deferred imports deleted — and its verification is that `tests/test_repositories.py:1868-1893`
  stays green **unedited**.
- **Test floor is directional** — run the floor command for the current count; a drive landing fewer
  cases than the previous run has lost a file.

### Where this goes next

> **Superseded 2026-08-11 (fold, round 4) as to the three open questions — all three are now
> ANSWERED, and the answers are recorded in the sections they belong to.** (a) *Gate signature:* no
> `existing` parameter, one entry point taking the introduced fields plus the entity type; the
> entity-shaped arms project through `model_to_frontmatter` (`writer.py:88-130`) first. Settled by
> the round-1 architectural review, re-affirmed in rounds 2 and 3, and NOT widened by the sentinel —
> Finding H shows why. (b) *Splitter:* TOTAL, returning `(address | None, display)`, owning the
> parens form BEFORE delegating, mapping `IdentifierError` to "not an address"; `Email.parse`'s
> angle-bracket gate (`identifier.py:141-144`) is not widened. Finding D's reconciliation 2 stays
> owed to the spec as a behaviour change on live data. (c) *How a door tells the gate what it is
> writing:* by DECLARATION — the gate is handed the type and never infers one, and it never consults
> the filesystem. Rewritten Finding B. The paragraph below is kept for the trigger-check record and
> for the derived-wall obligations in its second half, which are unchanged and still owed.

**Hand off to the architect before the spec.** The architect's trigger heuristics fire on three
counts: a new module, a contract change that crosses into three downstream repositories, and a
derived-wall enforcement mechanism that has to be designed rather than copied. The open questions
the architect should take are: whether the gate's signature is `(existing, incoming)` or two
separate entry points for entity- and dict-shaped writes (Finding C); whether `Email.parse`'s
stricter acceptance is adopted wholesale or the splitter keeps a compatibility arm for the parens
form (Finding D); and by what mechanism a door tells the gate what entity it is writing — an
explicit argument per door, or path-derived ownership in the `_owns` shape (Finding B).

Also owed at spec time, and unchanged: the derived-wall predicate for AC-1 and AC-5 — both are match-shape
walls in the WI-004 sense and must ship the fixture battery `tests/test_write_routing.py:1-18`
describes, which is the precedent to copy rather than re-derive. AC-1's predicate now has to resolve
at ARM granularity (Finding B): the members are the distinct bindings of the dict a function passes
to `write_frontmatter`, so a function with three such branches yields three members, and a function
that binds no such dict at all — `BaseRepository.save`, `PersonRepository.save`, and their
`book.py`/`meeting.py` siblings — yields none. That is the one
genuinely new piece of AST work in this item — the existing `_is_write_call` (derivations.py:238)
answers "does this function write", not "through which branch", and the data-flow family
`functions_reserializing_parsed_frontmatter` (derivations.py:294-310) is keyed on a
`parse_frontmatter` seed neither `save` has, so neither existing predicate resolves the set either
way — and it is the predicate the gate's own routing must satisfy branch by branch. *(Round-7 fold:
this is the paragraph the round-6 architectural review's blocking issue lands in — the predicate must
resolve the set WITHOUT a hand-list, which is what fixes the arm count at eight.)*

## Approach

> **Rewritten 2026-08-11 (fold, round 4)** to Dave's DECLARE ruling and rule (ii), and to the three
> findings the gate rounds confirmed in signed text (the sentinel, `aliases[]`, the per-arm
> declaration pin). The superseded text said "takes what a door knows … plus the entity type" without
> saying where that type comes from, and left the door count at eight; both are now stated exactly.
>
> **Amended 2026-08-11 (fold, round 5)** to the round-4 architectural review's blocking issue. The
> round-4 text placed the gate in a leaf module and, one paragraph later, committed it to
> `normalize_phone` — a symbol inside the repository layer, which a leaf cannot name without closing
> `writer.py → gate → person.py → base.py → writer.py`. The paragraph below now says where that
> authority lives, and Finding G states the delta and the two shapes rejected. Rule (ii)'s number is
> re-scoped in Finding B to the round-4 data audit's Finding 1; nothing else in the shape changed.
>
> **Amended 2026-08-11 (fold, round 6)** to the round-5 architectural review's blocking issue. The
> round-5 text said the splitter "normalizes three identifier-bearing fields" flat, across every arm.
> Two of the three fields' behaviour is a cross-field MIGRATION, and a migration is expressible only
> where the gate is handed the whole record; on a dict-shaped arm, emitting the destination key would
> REPLACE the stored list (`base.py:451`). The paragraph below now states the gate's OUTPUT contract
> explicitly and scopes the migration by arm shape; Finding I carries the derivation and the second
> migration. Nothing else in the shape changed — the signature, the splitter ruling, DECLARE and the
> phone relocation all stand.
>
> **Amended 2026-08-11 (fold, round 7)** to the round-6 architectural review's blocking issue and the
> round-6 data audit's. Two corrections, both to what this section COUNTS and PRICES rather than to its
> shape. (1) The routed set is **eight arms across six functions**, not ten across eight:
> `BaseRepository.save` and `PersonRepository.save` bind no frontmatter dict and serialize nothing
> (`base.py:381-395`, `person.py:1269-1272`), so `AC-1`'s own derivation unit cannot resolve them —
> the exact test this document already applies to the structurally identical `BookRepository.save` /
> `MeetingRepository.save`. D2 leaves the routing entirely (its bytes are gated at D1a one frame later,
> and `vault_io.ensure_dir` at `writer.py:273` is downstream of the convergence point at `:266`, so
> Finding F's spurious directory is still closed) and D3 keeps ONE gate call as a RIDER outside the
> derived set. (2) The dict-arm rule's cost is a **deletion**, not a non-migration: today a dict arm
> stores `"Al B <a@b.com>"` verbatim, so the display half IS on disk inside the `emails[]` entry, and
> the new rule drops it with no destination — its population is booked as one more column on G2. The
> signature, the splitter ruling, DECLARE, the phone relocation, the output contract and the arm-shape
> split all stand unchanged.
>
> **Amended 2026-08-11 (fold, round 8)** to the round-7 architectural review's blocking issue and the
> round-7 data audit's sizing of it. One correction, and it is to what the gate EMITS rather than to
> where it is called. The round-7 text said the gate returns the fields it was handed "validated and
> normalized" without saying which fields normalization reaches, and `name` is one of them — while the
> FILENAME is bound from the raw `entity.name` one frame ABOVE every gate call in the design
> (`base.py:381`) and neither `NameValidator` entry point returns a name byte-identical
> (`name_validation.py:257`/`:265-266`, `:283-297`). The gate's **name output is now declared an
> IDENTITY** — refuse, or return byte-for-byte — the architect's shape (b′), which the round-7 data
> audit independently records as the only one of the three with a zero live blast radius. Tier-2 repair
> stays a `create_stub`-only behaviour above the write path. Everything else stands: the signature, the
> splitter ruling, DECLARE, the phone relocation, the arm set, the arm-shape split, and the output
> contract's *never emit a key the write did not carry* clause, which this narrows rather than replaces.
>
> **Amended 2026-08-11 (fold, round 9)** to the round-8 architectural review's blocking issue, the
> round-8 data audit's confirmation, the conductor's EXECUTION of the scenario (`## Conductor Booking`)
> and **Dave's ruling on the fork** (`## Conductor Preconditions`, precondition 1). One correction, and
> it is to WHERE in the frame the gate call sits rather than to which arms carry one. Round 7's D2
> removal rested on *"`vault_io.ensure_dir` at `writer.py:273` is downstream of the convergence point at
> `:266`"* — true of the one `ensure_dir` written in `write_markdown_file`'s body, false of the frame:
> `note_lock` (`writer.py:209`) `mkdir`s the lock sentinel's home (`vault_io.py:400`), which DEFAULTS to
> the note's own parent (`:350`), before any fm exists. The gate therefore **runs ABOVE `note_lock`** at
> `write_markdown_file`'s three arms — option (a), Dave's call — and `AC-2`'s *"no stray directory is
> created"* clause stands as signed and becomes meetable. The hoist is arm-specific: D4/D5/D6/D8 keep
> their in-lock gate calls, because their frames refuse on a missing target before locking and because
> D5/D6/D8 read their declaration from the note inside it. Everything else stands: the signature, the
> splitter ruling, DECLARE, the phone relocation, the eight-arm set and its floor, the arm-shape split,
> the output contract and the name-identity rule.
>
> **Amended 2026-08-11 (fold, round 10)** to the round-9 architectural review's blocking issue and the
> round-9 data audit's. One correction, and it is to how the placement value is DERIVED rather than to
> any arm's placement. The round-9 text let an arm be `in-lock` if its frame refuses on the target's
> non-existence **or** if its *"target is supplied by a walk of notes already read"*. The second
> disjunct is a property of a CALLER two frames away — `apply_fixes` binds `fpath` from a dict keyed on
> its `issues` PARAMETER (`lint_vault.py:808-815`) and the walk is `read_vault`'s `rglob` at `:111` — so
> an AST predicate over the arm's own frame cannot resolve it, D8 fell to the rule's own `above`
> default, and the same rule requires D8 to stay `in-lock` (its declaration and its delta are parsed
> inside the lock at `:821`) where it also cannot be hoisted. One pin, two answers, on one arm. The
> disjunct is **DELETED** and D8 is made DERIVABLE instead — the architect's shape (A): this item gives
> `apply_fixes` the same existence guard its three siblings already carry, one statement above
> `note_lock`, so ONE local syntactic rule resolves all four in-lock arms identically and *"DERIVED,
> not listed"* survives as written. Everything else stands: the hoist, the eight-arm set, DECLARE, the
> splitter, the phone relocation, the output contract and the name-identity rule.
>
> **Amended 2026-08-11 (fold, round 11)** to the round-10 architectural review's note 1 and the round-10
> data audit's finding. **Nothing in the shape moved and no rule changed** — the whole of the round-10
> blocking issue lands in signed text (`AC-3`) and is staged in `## Re-origination Brief` rather than
> repaired here. What changed in this section is one sentence of PRECISION about a rule already written:
> the gate is handed the fields the write INTRODUCES, and Finding C's `writer.py:329`/`:381` citations
> name where each frame binds its PARSE — which at D5 is the only dict-shaped object in the frame, while
> the delta is two loose parameters (`writer.py:294-295`, mutated into the parse at `:332`). The delta
> rule, the hoist, the eight-arm set, DECLARE, the splitter, the phone relocation, the output contract
> and the name-identity rule all stand unchanged.
>
> **Amended 2026-08-11 (fold, round 12)** to the round-11 architectural review's blocking issue, its two
> non-blocking notes, and the round-11 data audit's artifact distinction. **No rule of the design moved
> and no arm changed placement** — the blocking issue is that ONE signed criterion asserts FRAME
> properties over the set `AC-1` derives for the GATE, which is staged in `## Re-origination Brief`. Three
> things changed in this section, all of them corrections to text that was already here. (1) The D8
> refusal is made OBSERVABLE: `apply_fixes`'s per-file `except Exception` (`lint_vault.py:902-903`)
> swallows a `LoudFailError` into a stderr line, so the closing sentence's *"one idiom"* claim is scoped
> to package doors and D8 gains a dedicated refusal arm that records and continues rather than aborting
> the run (Finding E). (2) The D3 rider's write-back sentence said `phones[]` was among the fields
> `_normalize_address_fields` mutates *"precisely"*; read from source it walks `emails` and `aliases`
> only (`person.py:_normalize_address_fields:1300-1343`), so the rider ADDS one in-place mutation rather
> than preserving three. (3) The delta paragraph now records that D4's frame contributes one key of its
> own. The gate, the splitter, DECLARE, the phone relocation, the eight-arm set, the arm-shape split, the
> output contract, the name-identity rule and the hoist all stand unchanged.
>
> **Amended 2026-08-11 (fold, round 13)** to the round-12 architectural review's blocking issue and the
> round-12 data audit's sizing of its exhibit. **No rule of the design moved, no arm changed placement,
> and no criterion changed scope** — the correction is to the MECHANISM round 12 chose for D8's refusal
> arm, one round after choosing it. That arm was written as `except LoudFailError`, which is the BASE of
> the hierarchy (`errors.py:LoudFailError:37`) in a frame that already raises four of its subclasses
> today — `WriteFailedError` from `note_lock` (`lint_vault.py:819`), `FrontmatterParseError` from
> `parse_frontmatter` (`:821`), and `WriteFailedError`/`ExternalWriteConflict`/`NoteAlreadyExists` from
> `write_note` (`:882`, `:900`) — none of which can carry a `pattern`, so a corrupt fence or a lock
> timeout would be recorded as *"the gate declined this note"*, and `AC-2`'s fourth conjunct would be
> greenable on a build with no gate at D8 at all. **The refusal therefore gets its OWN type**,
> `NameGateRefusal(LoudFailError)`, and every absorbing handler and every oracle names that type rather
> than the root (Finding E's round-13 subsection carries the derivation, the rejected attribute-probe
> shape, and the one rule that closes the class). The gate, the splitter, DECLARE, the phone relocation,
> the eight-arm set, the arm-shape split, the output contract, the name-identity rule, the hoist and the
> placement rule all stand unchanged.

Build **one semantic gate** — a single function, in a module of its own next to `errors.py`, that
takes the fields a write is INTRODUCING plus **a declared entity type it is HANDED**, and returns
them validated and — on the address fields only — normalized, or refuses. The gate never consults the filesystem: no glob, no path
shape, no sibling note, and `BaseRepository._owns` is not called anywhere in this design. Six of
the eight arms already hold the declaration they must pass — the model's own `type` at D1a,
`self.type_name` at D4 (and at the D3 rider), the note's parsed `type:` at D5/D6 and at D8
*(round-10 correction: at D8 that value is `fm.get("type")` from the in-lock parse at
`lint_vault.py:821`, NOT `vf.entity_type` — `apply_fixes` is handed `issues` and `idx`
(`lint_vault.py:804-805`) and never the walk's `VaultFile`, so `read_vault`'s `:140` is the same value
in a frame this one cannot see)*, with D7 needing no declaration because it introduces nothing — so this
costs no caller change; the remaining cell is a `frontmatter=` or `extra_fields`-only call that
carries no `type:` key, and **an undeclared write that introduces a `name:` is refused outright**
(Dave's ruling 2, chosen against a live undeclared population of 0 of 3,418 `@*.md` notes — a
*subset* of the rule's path-agnostic surface, so the number that BOUNDS the rule is query G1 in
`## Grounding Still Owed`, not this one; the direction is fail-closed either way, per Finding B).

Names go through `NameValidator`, whose Tier-1 chain is first **reified into a branch-unit table**
that also models the two refusals living outside it — `empty`, and the phone-sentinel exemption,
which the gate derives from the payload (*a pure-digit name is permitted when the record it is
introduced with carries a phone*) rather than from a new parameter (Finding H). **On `name` the gate is
a PREDICATE, not a transform**: it calls `validate_strict` for its raise behaviour, discards the
repaired string, and emits the name it was handed byte-for-byte. That is not tidiness — the FILENAME is
bound from the raw `entity.name` at `base.py:381`, one frame above every gate call in this design and
never revisited, so a gate that returned `"Dave Smith"` for `"Dave  Smith"` would write that field into
`@Dave  Smith.md` and the next `save()` would mint a second note for one person (Finding B's round-8
subsection). Tier-2 repair therefore stays exactly where it already runs — `create_stub`
(`person.py:1407`, `:1413`), ABOVE the filename derivation, which is why it has never produced that
divergence in two months of production. Addresses go through
one new shared splitter built on `identifier.Email.parse`, TOTAL, returning `(address | None,
display)` and owning the parens form before delegating; it replaces both duplicate parseaddr sites.

**The gate's OUTPUT contract, stated because it is what scopes the identifier half.** The gate returns
the fields it was HANDED — the address fields normalized, `name` byte-for-byte — or refuses. **It never emits a key the write did not carry**,
which is not a stylistic rule: `update_fields` merges by key REPLACEMENT (`frontmatter.update`,
`base.py:451`), so a gate that added a destination key would overwrite that field's stored list rather
than append to it (Finding I). Three identifier-bearing fields are in scope, not two — `emails[]`,
`phones[]` and `aliases[]` — but they do not all behave the same at every arm, because two of the
three behaviours are cross-field MIGRATIONS: an address found in an `aliases[]` entry moves to
`emails[]` (`person.py:1328`), and a display half found in an `emails[]` entry moves to `aliases[]`
(`:1339-1342`). A migration needs both fields in hand and needs the destination's dedupe set
(`:1327`, `:1331`), so it is available only where the gate receives the whole record. Therefore:

- **The entity-shaped arm (D1a), and the D3 rider above it** — the gate receives
  `model_to_frontmatter`'s projection of every declared field (`writer.py:111-116`), so both
  migrations run there, exactly as `_normalize_address_fields` runs them today at `person.py:1269`.
  Nothing is lost.
- **Dict-shaped arms (D1b, D1c, D4, D5, D6, D8)** — the gate normalizes only the fields the write
  carries and performs no migration. `emails[]` and `phones[]` normalize and dedupe as AC-4 requires;
  an `aliases[]` entry is passed through byte-identical, because splitting it without the migration
  would discard the address half rather than normalize it (Finding I). **The `emails[]` half of that
  rule DELETES the display half of any entry that carries one**, since M2 has no destination here and
  the entry is stored as its bare address — a real loss against what is on disk today, not merely a
  migration withheld, sized by G2's `emails[]`-display-half-not-in-`aliases[]` column (Finding I,
  round-7 correction).

`_normalize_address_fields` is SUBSUMED, not wrapped: it is deleted, its inner
`_extract_email_and_name` (`person.py:1286`, nested inside the static method at `:1277-1278`) becomes
the shared splitter, its two migrations become the entity-arm behaviour above, and
`PersonRepository.save`'s call at `:1269` goes with it — with `save` writing the gate's normalized
values back onto the entity so the in-place model mutation callers see today is preserved. **That
write-back IS the D3 rider**: it is the reason `PersonRepository.save` carries a gate call at all now
that it is not an arm, no other frame can perform it (the gate returns a dict and never touches the
model), and it sits explicitly outside the derived set. **The write-back is the IDENTIFIER fields only —
`emails[]`, `phones[]`, `aliases[]` — and never `name`** *(round-8 fold)*: those are ~~precisely~~ **two
of the fields `_normalize_address_fields` mutates in place today, plus one it does not**
(`person.emails = new_emails` at `person.py:1317`, `person.aliases = new_aliases` at `:1343`; that
function walks `emails` and `aliases` ONLY, `:1300-1343`, and never touches `person.phones`), and under
the identity rule the gate returns the name unchanged, so there is nothing on that field to write back.
*(Wording corrected round-12 fold, architect round-11 note 1. `phones[]` in the rider is a NEW in-place
mutation a caller holding a `Person` will observe where it does not today — the behaviour `AC-4` wants,
and no gate has objected to it, but the consumer audit's blast radius is one FIELD wider than
*"precisely"* implied, and the audit's grep list is written against this sentence.)* That
is the whole of what shape (b′) costs the rider — it deletes an obligation rather than adding one, and
it means no repository override is load-bearing for the path/field agreement: it holds by construction,
for every entity type, at every arm. The gate is
**idempotent** (`gate(gate(x)) == gate(x)`), which is required rather than incidental: one
`PersonRepository.save` invokes it twice — the D3 rider, then D1a on the projection of the entity the
rider just normalized.

**Phones dedupe on `normalize_phone`'s output while storing the display form — and that authority
MOVES to a leaf before the gate can name it.** `normalize_phone`/`phones_match` live in
`repositories/person.py` (`:129`, `:148`) today, so a leaf gate naming them would close
`writer.py → gate → repositories/person.py → repositories/base.py → writer.py` at package load
(`person.py:78`, `base.py:19`, `__init__.py:40`/`:72`). This item therefore relocates both functions
verbatim into a new stdlib-only leaf, `obsidian_schemas/phone_normalization.py`, which the gate and
`identifier.py` both import at module scope; `repositories/person.py` re-exports the two names so no
call site and no consumer changes. That **deletes the two deferred imports** at `identifier.py:236`
and `:272` — the workaround this item would otherwise reach for a third time — and lands WI-023's own
scope item 4 (`docs/identity-engine-endgame.md:28`) early rather than duplicating it. The relocation
carries **no behaviour delta**: `Phone.parse`'s `MIN_DIGITS = 7` floor (`identifier.py:228`,
`:238-239`) is never introduced into the dedupe path, which is why this shape was chosen over
delegating to `Phone.parse`. The gate dedupes on `normalize_phone` alone; `phones_match`'s
country-code equivalence moves with it but stays WI-023 item 2's question, not this item's.

Route all **eight arms across six functions** through it — `write_markdown_file`'s three fm-building
arms, `update_fields`, `update_frontmatter_field(s)`, `roundtrip_file`, and `lint_vault --fix`, with
`_writeback_identifier` reaching the set through `update_fields` — plus the one **rider** at
`PersonRepository.save`, which is not a member and is pinned by its own fixture rather than by the
wall.

**And route them at the right POINT in the frame, not merely somewhere in it** *(round-9 fold, Dave's
precondition 1; the DERIVATION corrected round-10 fold)*. At `write_markdown_file`'s three arms the fm construction and the gate call are
**hoisted above `vault_io.note_lock` (`writer.py:209`)**, because that lock's own outermost acquisition
`mkdir`s the sentinel home (`vault_io.py:400`) at a path that DEFAULTS to the note's own parent
(`:350`) — so a gate at the convergence point refuses *after* `<vault>/@Dave/` and a `.lock` file are
already on disk, which the conductor confirmed by execution (`## Conductor Booking`). The hoist is
legal precisely because of DECLARE: the gate reads only the payload and the handed type, so nothing it
touches is protected by the lock. It is also arm-specific — **D4, D5, D6 and D8 keep their in-lock gate
calls** — and the property that says which arms MAY is ONE fact about the arm's own frame: *the frame
refuses on the target's non-existence above its first `vault_io` call of ANY kind (equivalently its `with vault_io.note_lock(...)` statement; corrected per architect round 14 — anchoring on the first MUTATION call let every arm compute `above`)*. Three arms carry that
guard today (`base.py:432-433`, `writer.py:320-321`, `:374-375`). **D8 does not, and this item adds
it** *(round-10 fold)*: one `if not fpath.exists(): raise FileNotFoundError(...)` immediately above
`note_lock` at `lint_vault.py:819`, matching its three siblings statement for statement, in a function
this item already opens for the delta threading. That is not predicate plumbing — `apply_fixes` binds
`fpath` from a dict keyed on its `issues` parameter (`lint_vault.py:808-815`) and the walk that found
those paths ran two frames away in `read_vault` (`:111`, reached from `run_lint:1069`, with
`apply_fixes` called at `:1100-1103`), so nothing in the frame is evidence the target still exists and
a note deleted between the two passes gets the sentinel `mkdir` and the `.lock` before `read_note`
fails. D5/D6/D8 additionally **MUST** stay in-lock, because that is where the dict they judge and the
declaration they pass are parsed (`writer.py:329`, `:381`; `lint_vault.py:821`). **D7 takes `above`**,
by the default rather than by a hoist: its frame carries no guard either, and the placement costs
nothing because its gate call is handed an empty delta (see below). `write_frontmatter`
stays at the convergence point, so the arm set and `AC-1`'s floor are unchanged by the move.

**D7 routes, and what it passes is EMPTY** *(round-10 fold, resolving a contradiction round 9
created)*. `roundtrip_file` is one of the eight members of `AC-1`'s floor and `AC-1` requires every
member to route, so D7 carries a gate call like the rest; what makes it harmless is Finding C's delta
rule, not an exemption — it re-serializes the note's own parsed frontmatter (`writer.py:418-421`) and
introduces no field, so the gate is handed an empty mapping, has nothing to judge, can never refuse
and needs no declaration. That is exactly why `AC-2` and `AC-4` exclude it by equality as *"the one arm
that introduces no fields"*, and it is why the call is worth writing rather than skipping: the wall's
per-arm triple stays total, and the ninth arm someone adds next month by copying `roundtrip_file`
inherits a gate call instead of a hole. Round 9's placement table said *"no gate call at all"* for this
row, which contradicted this section and `AC-1` both; the row is corrected in Finding B.

Then prove the routing TOTAL with a derived AST wall in `tests/derivations.py`, so
that the ninth arm someone adds next month, whether a new function or a new branch inside an
existing one, is red at test time rather than silently unguarded. **The wall must pin what each arm
PASSES and WHERE each arm CALLS, as well as which arms call**: the declaration handed to the gate is
the one available at that arm, **and where none is available that is EXPRESSED rather than defaulted** —
without that, wiring all eight arms with the type defaulting to `None` greens the routing while every
`update_fields` write (whose delta carries no `type:` key) escapes the contract permanently — **and the
gate call's PLACEMENT is derived by ONE local, syntactic rule over the arm's OWN frame: the required
value is `in-lock` iff that frame refuses on the target's non-existence above its first `vault_io`
call of ANY kind (equivalently its `with vault_io.note_lock(...)` statement; corrected per
architect round 14), `above` otherwise, and `above` is the DEFAULT for any arm the predicate does not
recognise** *(round-9 fold; the rule's second disjunct — "or whose target is supplied by a walk of
notes already read" — DELETED round-10 fold, because it asked an AST instrument to certify a fact about
a caller two frames away and left D8 with two required values at once; D8 now satisfies the one rule,
by carrying the guard)*. One further leg rides with it, as a RED consistency check rather than as a
second route to `in-lock`: an arm that passes the gate a value bound inside the lock — D5/D6/D8 parse
their declaration from the note there (`writer.py:329`, `:381`; `lint_vault.py:821`) — must be
`in-lock`, so an arm the one rule requires `above` while its gate arguments are bound in-lock is a
contradiction the wall REPORTS rather than resolves, and the repair is that frame's missing guard, never
a hoist above the parse that supplies its type. Without that third argument, a build that leaves the D1 gate call at
`writer.py:266` is indistinguishable from one that hoists it, and `AC-2`'s no-stray-directory clause is
green in the wall and false on disk. *(Wording aligned with the
re-origination brief's `AC-1` entry, 2026-08-11 round-6 fold, per architect round-4 note 2: the
round-3 phrasing "no arm hardcodes a literal or defaults it" is too strong, because two arms
legitimately have no declaration to pass — `roundtrip_file` (D7), which parses a note it does not
judge (`writer.py:419`), and D1b/D1c when the caller's dict genuinely carries no `type:`, which is
the undeclared cell rule (ii) exists for. Corrected here so `## Approach` and the brief do not state
the pin two ways.)*

The gate judges the DELTA, never the stored record, which is what keeps a note writable by the tools
whose job is to repair it. **And WHERE that delta lives is arm-specific, so the object handed to the
gate is not the object each frame's parse citation names** *(round-11 fold)*: at D4 and D6 it is the
caller's `updates` dict (`base.py:406`, `writer.py:352`), at D1a/D1b/D1c it IS the whole record, at D7 it
is empty, at D8 it is what the delta threading must build, and **at D5 there is no dict in the frame at
all** — `update_frontmatter_field` takes `field_name`/`field_value` as two loose parameters
(`writer.py:294-295`) and mutates the parsed record with them at `writer.py:332`, so the build must
CONSTRUCT `{field_name: field_value}` while the stored record sits bound one line above the call site at
`:329`. Gating the merged record at D5/D6 would make `update_frontmatter_field` permanently refuse every
note whose stored name is Tier-1 dirty — the remedy-is-the-disease outcome this rule exists to prevent,
at the two arms where those notes are reachable at all (Finding C's two round-11 subsections). **One
frame contributes a key the gate is never handed, and the build must know it does** *(round-12 fold,
architect round-11 note 2)*: on a name change `update_fields` appends the old filename stem to `aliases`
itself (`base.py:update_fields:443-448`) before merging the caller's `updates` at `:451`, so D4's write
introduces a value that is not in the delta the design hands the gate. Under the arm-shape split
`aliases[]` is passed through byte-identical on dict arms, so there is nothing the gate would have done
differently and no rule changes — it is recorded so the D4 delta is specified as *the caller's `updates`
dict*, knowingly, rather than as *everything this write introduces*. (The pre-existing ordering bug —
`updates` carrying its own `aliases` at `:451` overwrites the append at `:448` — is not this item's and
is not absorbed; it joins the parked list only if a later item needs it.)

Refusals convert to **one new leaf of the loud-fail hierarchy, `NameGateRefusal(LoudFailError)`**
*(round-13 fold; round 12 said "a `LoudFailError`" and that is one level too wide — see below)*, carrying
the stable NameValidator
pattern key on a **dedicated `pattern` attribute** — not in `declared_type`, which `base._note_skip`
already feeds back into `_owns` (`base.py:_note_skip:266-274`) — and no note content, so **at every
package DOOR `except LoudFailError` remains the one idiom for "this package refused"** *(scoped round-12
fold, architect round 11: the unqualified claim was false at D8, where the arm is not a door but a batch
CLI whose per-file `except Exception` at `lint_vault.py:902-903` swallows it. D8's refusal is made
observable as a structured, counted refusal record that does not abort the run — Finding E carries the
shape, the rejected alternative and the `AC-2` consequence)*.

**The new type is what makes that record mean anything, and it is forced rather than chosen**
*(round-13 fold, architect round 12)*. `LoudFailError` is the hierarchy's base (`errors.py:37`) and
`apply_fixes`'s per-file `try` already raises four of its subclasses before this item touches the frame
(`note_lock` at `lint_vault.py:819`, `parse_frontmatter` at `:821`, `write_note` at `:882`/`:900`), none of
which can carry a `pattern` — `bounded_message`'s keyword set is `path`/`declared_type`/`cause`
(`errors.py:bounded_message:134-136`) and the hierarchy has exactly one constructor (`:47-54`). A handler
filtering on the root would therefore record a corrupt frontmatter fence as a gate refusal and move real
IO failures out of the `Fix error on …` channel. **One rule covers the whole surface**, and it is stated
that way rather than as this arm's exception: *a handler that RE-RAISES may filter on the hierarchy root —
which is why the package's seven existing `except LoudFailError` sites (`writer.py:341`, `:393`;
`person.py:1598`, `:1700`, `:1819`, `:1899`, `:1968`) are all correct as they stand — while a handler that
ABSORBS must filter on the exact refusal type, and every oracle asserting that the gate refused names
`NameGateRefusal` and its `pattern` rather than `LoudFailError`.* The new class declares no `__init__` of
its own, exactly as `StaleEntityWrite` and `NoteAlreadyExists` do not (`errors.py:84-89`, `:98-103`), so
the message bound holds by construction. The refusal's reason literal must be
chosen at spec time and added to `REASONS`, a closed frozenset of fifteen
(`errors.py:REASONS:110-127`) that `bounded_message` refuses any non-member of
(`errors.py:bounded_message:139-145`).

## Acceptance Criteria

**DRAFT — not frozen.** These are the ideation convergence artifact: what would prove this worked.
They have NOT been through `/review-spec` and carry no `ac-signoff` fence, so origination must not
be attempted from this state.

**Revision 1 — 2026-08-11, answering the AC red-team below.** The REMOVE-audit rule's required
cold-start red-team has now run against the draft set (section at the foot of this doc) and returned
four findings; this revision answers all four, and the answers are the reason the criteria read the
way they do:

- **AC-1** gained a floor and a reach battery. The unbounded version was satisfiable by a vacuous
  sweep — "every member of {} routes through the gate" is true — and because AC-2 and AC-4 both
  delegate their door coverage to this set, one under-resolving predicate would have shrunk all
  three at once while six real doors stayed open.
- **AC-4** is now bound to AC-1's derived set instead of naming four call sites, with `roundtrip_file`
  as the single asserted exclusion. The old hand-list silently exempted `write_markdown_file` and
  `lint_vault --fix` — both shown unnormalized in Finding B's own table — while reading as total.
- **AC-2** gained the untyped-frontmatter clause, and Finding B above no longer defers the
  no-`type:` dispatch rule to the architect: it adopts `_owns`'s fail-closed answer and pins it here.
  That residue sat upstream of every other criterion, so no amount of door coverage could have caught it.
- **AC-5**'s sweep is re-keyed from the `parseaddr` symbol to the job shape, with per-shape positive
  controls. Finding D records why: its own table came from a `parseaddr` grep and is a lower bound.

**Revision 2 — 2026-08-11, answering the round-2 re-verify.** Round 2 confirmed the AC-1 / AC-4 /
AC-5 fixes and found that revision 1 had folded the no-`type:` dispatch residue only HALF way: AC-2
pinned it for names, AC-4 said nothing about the `type:` dimension at all, so an implementation
dispatching on `if frontmatter.get("type") == "person"` could green the whole set while every untyped
note in the vault took unnormalized identifiers — the N3 corruption through the type-less side door.

- **AC-4** now carries the same untyped clause AC-2 does, asserted as a REPEAT of its whole property
  over the `type:`-present/absent dimension rather than one extra fixture, so the dimension the
  dispatch code actually branches on is varied on the identifier half exactly as it is on the name
  half. Scoping the untyped case out of AC-4 was the alternative and was rejected: it would have had
  AC-2 and AC-4 take opposite calls on one residue over one door set, against an Intent that draws no
  such line.
- **Finding B** was rewritten to state the pinning as one rule covering both halves, and to say why
  it must be asserted in two places: dispatch fires once per write, upstream of the name/address
  distinction, so an unasserted half is a switch nobody is watching.
- **Examples of done** gained the untyped variant of the identifier scenario, so Dave sees the
  behaviour he is signing in his own terms, not only in the criteria fence.

**Revision 3 — 2026-08-11, answering the round-3 re-verify.** Round 3 confirmed revision 2 closed the
dispatch residue where it is real, and found that it over-reached: AC-4's untyped pass was bound to
AC-1's whole derived set minus only `roundtrip_file`, which pinned the entity-only doors into an
untyped pass they cannot undergo — `model_to_frontmatter` emits every declared field (writer.py:111)
and `Person.type` is `Literal["person"] = "person"` (models.py:78), so an entity write always stamps
`type: person` and there is no branch to get wrong. A builder could satisfy that sentence only with a
fixture that passes with or without the dispatch fix.

- **AC-4** now states TWO exclusion sets, one per pass, instead of asserting one set holds "in both":
  typed pass `{roundtrip_file}` over AC-1's full derived set (unchanged — this is what closed round
  1's Finding 2 and it stays total); untyped pass `{BaseRepository.save, PersonRepository.save,
  roundtrip_file}` over the dict-shaped doors. Both are still asserted by EQUALITY, so narrowing the
  untyped pass did not reopen the escape hatch round 1 closed — a door is out only by being
  entity-only or introducing nothing, both stated reasons, neither a builder's choice.
- **One correction to the reviewer's suggested fix, taken from the code rather than the door table.**
  Round 3 proposed excluding D1–D3 from the untyped pass as "the entity-shaped doors". D1 is not one:
  `write_markdown_file` has TWO arms (writer.py:161-162), and its `frontmatter=` arm takes a
  caller-supplied dict copied verbatim at :259 — which can genuinely lack `type:` and is exactly the
  documented public entry point round 1's Finding 2 fought to keep in scope. Excluding it by name
  would have re-opened that hole on the untyped side. The exclusion sets are therefore stated at
  function granularity and name only `BaseRepository.save` / `PersonRepository.save`, the two doors
  whose ONLY input is a typed model.
- **AC-2** was given the same explicit treatment. Its untyped clause already said "dict-shaped", but
  left the term undefined and its exclusion set unstated — so a builder could have read D1 out of it
  wholesale, the same defect one AC over. It now enumerates what dict-shaped means and asserts the
  identical `{BaseRepository.save, PersonRepository.save, roundtrip_file}` set, so the two halves of
  one rule are scoped identically rather than differently-worded.
- **Finding B** gained the "where the untyped dimension exists, and where it cannot" paragraph — the
  door-shape split, with the code citations that make the entity-only case unconstructible rather
  than merely unlikely — so the scoping is motivated in the exploration rather than asserted in a
  criteria fence. The D1 row of the door table now records both arms.

**Revision 4 — 2026-08-11, answering the round-4 re-verify.** Round 4 confirmed revision 3's
typed/untyped exclusion-set split and found the residue one level down: both ACs bound their coverage
to AC-1's derived set, but that set's unit was the FUNCTION, so "every door in AC-1's derived set"
could be satisfied for `write_markdown_file` by a `frontmatter={"type": "person", …}` call — the same
fixture shape the untyped pass already needs — and the `entity=` arm that AC-4's own rationale cites
as the live example was never a required fixture. A gate written inside `if entity is not None:`
(natural: that branch holds the typed `Person`) or, symmetrically, in only one of the other branches,
greens every criterion while real callers stay ungated.

- **The fix is structural rather than two more sub-clauses.** AC-1's derivation unit is now the write
  ARM — one member per distinct binding of the dict a function serializes — so the floor is ten arms
  across eight functions instead of eight doors. Because AC-2 and AC-4 already iterate that set,
  arm-granularity membership makes a fixture through each arm mandatory without either criterion
  hand-listing one. Hand-listing is exactly the shape rounds 1–3 kept punishing; adding an `entity=`
  sub-clause to two ACs would have fixed this arm and left the next one to the round after.
- **Reading the code for the fix found a THIRD arm the review named only two of.**
  `write_markdown_file` has three fm-building branches, not two: `entity=` (writer.py:256-257),
  `frontmatter=` (:258-261), and `else: fm = extra_fields or {}` (:262-263), which serializes a
  caller-supplied dict as the whole record with no model and no `frontmatter=` argument.
  `write_markdown_file(path, extra_fields={"type": "person", "name": "Dave/Bob"})` is a legal call on
  a documented public function that reaches vault bytes. Under the round-4 suggested fix — an
  `entity=` sub-clause on each AC — that arm would have stayed unexercised on both passes; under arm
  derivation it is a member, on both.
- **One further code reading, recorded because it bounds the delta rule.** `extra_fields` merges
  differently per arm: guarded on the entity arm (`if key not in result`, writer.py:127, so it cannot
  override `name`), an overriding `update` on the `frontmatter=` arm (:260-261), and the sole source
  on the `else` arm. So `extra_fields` is a live field source for the gate on two of the three arms
  and inert on the first — which is why the arms are separate members rather than one door with a
  parameter.
- **Finding B** gained the arm table and now states the door set as ten arms across eight functions;
  the untyped scoping is restated in terms of dict-shaped vs entity-shaped ARMS, which is what lets
  `write_markdown_file` be in the untyped pass through two arms and out through one, instead of the
  function-granularity approximation revision 3 had to apologise for. The D1 row of the door table
  records all three arms.
- **Examples of done** gained the direct-call variants — both the bare
  `write_markdown_file(entity=…)` bypassing the repositories and the `extra_fields`-only call — so
  the behaviour Dave signs includes the consumer who never touches a repository.

Still owed before Dave signs: the consumer audit named under Constraints, since AC-2's refusal is a
breaking change for three repositories.

Every `check` is a top-level `def test_*(` taking ZERO arguments that signals failure by RAISING —
a returned `False` exits 0 and reads as PASS.

```criteria
id: AC-1
desc: The set of write ARMS in obsidian_schemas/ and scripts/ that build vault bytes from a frontmatter dict is DERIVED by an AST sweep (never enumerated), every member routes through the one semantic gate, and the sweep's REACH is proven rather than assumed. The unit of the set is the ARM — one member per distinct binding of the dict a function serializes, so a function with N such branches contributes N members — never the function. (a) The derived set contains AT LEAST the ten arms Finding B names, asserted by (qualname, arm) — write_markdown_file's `entity=` arm (writer.py:256-257), its `frontmatter=` arm (:258-261) and its extra_fields-only `else` arm (:262-263) as three DISTINCT members, plus BaseRepository.save, PersonRepository.save, BaseRepository.update_fields, update_frontmatter_field, update_frontmatter_fields, roundtrip_file, and lint_vault's --fix writer — so a predicate that resolves fewer arms, or that collapses a multi-arm function to one member, is RED rather than vacuously green. (b) A planted scratch module carrying one function per arm SHAPE in that table — including one multi-branch function whose branches must resolve as separate members — is matched when driven through the same derivation function the live wall calls, never a re-implementation. (c) A planted near-miss — a function that reads and mutates a frontmatter dict but hands it back to its caller instead of serializing it — is NOT matched. An eleventh arm added without the gate, whether it is a new function or a new branch inside an existing one, is red without editing the wall.
why: A quantifier oracle carries no information about a matcher's reach — "every member of {} routes through the gate" is vacuously true, and AC-2 and AC-4 both delegate their door coverage to this set, so an under-resolving sweep silently shrinks all three. The floor makes under-resolution fail; the planted controls prove reach; the near-miss stops the wall passing by matching everything. Deriving at ARM rather than function granularity is what closes the branch-shaped bypass: write_markdown_file's three arms converge on one write_frontmatter call (writer.py:266), so a wall proving only "this function calls the gate somewhere" passes for a gate written inside `if entity is not None:` while `frontmatter=` and extra_fields-only callers stay ungated — and because AC-2/AC-4 iterate this set, per-arm members force a fixture through each arm without either criterion hand-listing one, which is the hand-list shape rounds 1-3 kept punishing. WI-004's own walls already ship exactly this battery (tests/test_write_routing.py:1-18) — this reuses the shape rather than inventing one.
check: test_every_frontmatter_door_routes_through_the_semantic_gate
kind: test
```

```criteria
id: AC-2
desc: For EVERY Tier-1 pattern NameValidator declares — the fixture space swept from that module's own pattern table, not sampled — a write that INTRODUCES a matching name is refused at every ARM in AC-1's derived set, the target is left byte-identical, no stray directory is created, and the refusal is a LoudFailError carrying the stable pattern key and no note content. TYPED PASS — the set itself, iterated at arm granularity, with the exclusion set asserted to BE exactly {roundtrip_file}, the one arm that introduces no fields (Finding C). Because AC-1's members are arms, write_markdown_file contributes three separate required fixtures and a `type: person` value arriving through the `frontmatter=` arm never stands in for the `entity=` one: a bare write_markdown_file(entity=Person(name=<dirty>)) call, bypassing both repositories, is required by construction, as is write_markdown_file(path, extra_fields={"type": "person", "name": <dirty>}) through the extra_fields-only arm. UNTYPED PASS — the same refusal fires when the write carries NO `type:` key: at every DICT-SHAPED arm in that set (write_markdown_file's `frontmatter=` arm and its extra_fields-only arm, update_fields, update_frontmatter_field, update_frontmatter_fields, lint_vault --fix), a dict with `type:` absent, under the `@*.md` convention, is gated exactly as a `type: person` one is, with its exclusion set asserted to BE exactly {write_markdown_file's `entity=` arm, BaseRepository.save, PersonRepository.save, roundtrip_file}. Both exclusion sets are asserted by equality, so an arm is out of a pass only by being entity-shaped or introducing nothing, never by an implementation skipping it. Untypedness never exempts a write.
why: Class-closing (WI-185): a hand-picked sample is the WI-131 single-literal gap, and a pattern added to NameValidator later must join the sweep automatically. The byte-identical and no-stray-directory clauses pin Finding F. Iterating AC-1's set at ARM granularity is what forces the `entity=` arm to be exercised directly rather than hand-listing it as a sub-clause: write_markdown_file's three arms build fm in three independent branches that converge on one write_frontmatter call (writer.py:256-266), so a uniform dict-shaped fixture harness — the cheapest to write, since most arms take dicts — would satisfy a function-granularity binding while a gate wired inside `if entity is not None:` leaves the other two arms open, or a gate wired at the convergence point leaves nothing to distinguish it from one that is not. The untyped clause closes Finding B's dispatch residue, which sits UPSTREAM of every other check here — a `type`-keyed dispatch defaulting untyped notes to "not a person write" would bypass the whole gate — and it pins the fail-closed answer `BaseRepository._owns` (base.py:257-264) already gives rather than inventing a second rule. Scoping that clause to dict-shaped arms is not a carve-out: on an entity-shaped arm the untyped case is unconstructible, because `model_to_frontmatter` emits every declared field (writer.py:111) and `Person.type` is `Literal["person"] = "person"` (models.py:78), so `type: person` is always stamped and there is no branch to get wrong — a fixture there would pass with or without the dispatch fix. Excluding arms rather than functions is what keeps write_markdown_file's dict arms IN while its entity arm is out, without the function being included or excluded wholesale. AC-4 asserts the identical structure on the identifier half; the rule is one rule, but dispatch fires once per write for BOTH halves, so a half left unasserted is a half a wrong `type:` check can switch off unnoticed.
check: test_every_tier1_pattern_is_refused_at_every_door
kind: test
```

```criteria
id: AC-3
desc: A note whose STORED name already matches a Tier-1 pattern stays writable for every write that does not set the name — update_fields on an unrelated field, a body-section append, roundtrip_file, and lint_vault --fix all still commit — while a write that sets the name to that same value is refused.
why: The delta rule (Finding C). Without this the item bricks every legacy-dirty note in a 1647-note vault and refuses the very repair tools that exist to clean them.
check: test_a_legacy_dirty_name_stays_writable_for_unrelated_writes
kind: test
```

```criteria
id: AC-4
desc: An identifier arriving through EVERY ARM in AC-1's derived set — the set itself, iterated at arm granularity, not a hand-listed subset — plus _writeback_identifier's reuse branch, which reaches that set through update_fields, lands in emails[]/phones[] in the same normalized form, so that 'Name <a@b.com>', 'Name (a@b.com)' and a bare address collapse to one entry and a re-spaced phone does not create a second one. That property is asserted over TWO passes, one for each value of the `type:` dimension the dispatch code branches on, and each pass states its own exclusion set. TYPED PASS — against a `type: person` note, over AC-1's derived set with the exclusion set asserted to BE exactly {roundtrip_file}, the one arm that introduces no fields (Finding C). Because AC-1's members are arms, write_markdown_file's `entity=` arm is a required fixture in its own right and no `frontmatter=` call carrying `type: person` can stand in for it: the direct write_markdown_file(entity=Person(emails=["Name <A@B.com>"])) call named in this criterion's own rationale is exercised by construction, as is the extra_fields-only arm. UNTYPED PASS — the same inputs and the same required outcome against a note with `type:` ABSENT under the `@*.md` convention, over every DICT-SHAPED arm in that set (write_markdown_file's `frontmatter=` arm and its extra_fields-only arm, update_fields, update_frontmatter_field, update_frontmatter_fields, lint_vault --fix), with its exclusion set asserted to BE exactly {write_markdown_file's `entity=` arm, BaseRepository.save, PersonRepository.save, roundtrip_file} — the entity-shaped arms, where an untyped write cannot be constructed, plus the arm that introduces nothing. Both exclusion sets are asserted by equality rather than tolerated, so "excluded" is never an arm the implementation happened to skip. Untypedness never exempts an identifier write wherever the dispatch branch is live, exactly as it never exempts a name write (AC-2), and the two ACs scope both of their passes identically.
why: Closes N3 and Finding G in the same property, stated as an agreement ACROSS arms rather than per-door, so an arm normalizing differently is a failure rather than a passing variant. Binding the typed pass to AC-1's derived set (as AC-2 does) is what makes it total: a hand-listed subset silently exempts the doors it forgot — write_markdown_file(entity=Person(emails=["Name <A@B.com>"])) is the live example, a documented public entry point (README.md:196) that bypasses PersonRepository.save's normalization entirely — and exempts the next door by construction. Iterating that set at ARM granularity is what makes the live example actually get called: at function granularity a builder satisfies "door = write_markdown_file" with frontmatter={"type": "person", ...}, reusing the untyped pass's own fixture shape, and never issues the entity= call the example names, so a gate wired into only one of the three branches that converge at writer.py:266 greens the set. The untyped pass closes the OTHER half of Finding B's dispatch residue: dispatch decides once per write whether the gate fires at all, upstream of the name/address distinction, so with AC-2 asserting untypedness only on names, `if frontmatter.get("type") == "person": normalize_identifiers(...)` — the natural wrong mirror of the bug AC-2's clause forces out — would green this whole set while update_fields(person, {"emails": ["Name <A@B.com>"]}) writes unnormalized on every legacy `type:`-less note in the vault. Varying the exact dimension the code branches on is what makes that implementation RED. The two passes carry DIFFERENT exclusion sets because the dimension is only live on one class of arm: on an entity-shaped arm `model_to_frontmatter` emits every declared field (writer.py:111) and `Person.type` is `Literal["person"] = "person"` (models.py:78), so `type: person` is stamped unconditionally, there is no branch to get wrong, and an "untyped" fixture there would pass whether or not the dispatch rule was implemented — a control with no discriminating power reading as coverage. One exclusion set asserted across both passes would force exactly that fixture; naming both sets at ARM granularity keeps every live dict arm in — write_markdown_file is in the untyped pass through `frontmatter=` and extra_fields, and out of it through `entity=` — without the function being included or excluded wholesale and without inventing coverage where the failure cannot occur.
check: test_identifiers_normalize_identically_on_every_door
kind: test
```

```criteria
id: AC-5
desc: Exactly ONE implementation of the JOB "split a display-name/address blob into (address, display)" exists in the package, with identifier.Email.parse's angle-bracket-gated use as the one permitted home — the fixture space derived by a sweep keyed on the JOB SHAPE, not on the parseaddr symbol (a function returning a 2-tuple whose body carries address-splitting evidence: any email.utils member, or a '<' / '(' / '@' literal used to split or match a string), proven by planted positive controls it MUST match in each implementation shape — a parseaddr call, a hand-rolled regex, a bare raw.split('<') — and a planted near-miss returning a differently-shaped pair it must NOT match. The surviving implementation agrees with Email.parse on every input form the deleted create_stub and _normalize_address_fields sites accepted, including the parens form.
why: The consolidation rider, corrected by Finding D: the property that matters is no SECOND authority for one job. A sweep keyed on the literal parseaddr symbol names the MECHANISM one level below the property (the WI-185 shape) and is blind to exactly the duplication most likely to survive — Finding D's own table was built by a parseaddr grep and is a lower bound, and _extract_email_and_name already reaches for a parens regex before it reaches parseaddr, proving the job is written here without the symbol. The agreement clause is what stops the consolidation silently changing behaviour on the parens and laxity deltas.
check: test_address_splitting_is_single_homed_and_agrees_with_email_parse
kind: test
```

### Examples of done

**Given** a producer calls `repo.save(Person(name="Dave/Bob"))` — the path-hostile form WI-105
already rejects at `create_stub` — **when** the save runs, **then** it refuses with a bounded
`LoudFailError` naming `path_hostile_char`, and the vault contains no new `@Dave/` directory and no
`Bob.md` inside one. **And when** a consumer skips the repository entirely and calls the public
writer directly — `write_markdown_file(path, entity=Person(name="Dave/Bob", emails=["Al B <A@B.com>"]))`
— **then** the answer is identical: the same refusal, no directory, no note. **And when** it instead
calls `write_markdown_file(path, extra_fields={"type": "person", "name": "Dave/Bob"})`, handing the
writer a bare dict and no model at all, **then** that too is refused. Three different ways into the
same function are three doors, and none of them is the way through.

**Given** an existing note `@Me to David Field.md` whose stored name has been Tier-1 dirty since
before this item, **when** the enricher calls `update_fields(person, {"company": "Acme"})`, **then**
the company is written and the note is untouched otherwise — **and when** something instead calls
`update_fields(person, {"name": "Me to David Field"})`, **then** that write is refused. **And when**
that same note turns out to be hand-created with no `type:` key at all, **then** both answers are
unchanged: the company write still commits, the name write is still refused — being untyped is not a
way through.

**Given** `find_or_create_stub` resolves to a canonical who already has `a@b.com` and `+447739341679`,
**when** the reuse branch writes back `"Al B <A@B.com>"` and `"+44 7739 341679"`, **then**
`emails[]` and `phones[]` each still hold exactly one entry, and `"Al B"` has landed in `aliases[]`.
**And when** that canonical is instead one of the hand-created notes carrying no `type:` key,
**then** nothing about that answer changes — one email entry, one phone entry — because being untyped
is not a way through on the address side either, exactly as it is not on the name side above.

## AC Sign-off

```verdict
gate: ac-signoff
verdict: PROMOTE
date: 2026-08-11
reviewer: dave
channel: conversational
signed_at: 2026-08-11T10:33:24+01:00
provenance: verified
signoff_escalation: ESC-WI-021-exploring-awaiting-ac-signoff-154d37c4
ac_hash: a76ebad54da2
intent_hash: 176e2ec73fda
ac_hash_AC-1: 33653902f47f
ac_hash_AC-2: b6874ac5d7ef
ac_hash_AC-3: 9e2bae0c2137
ac_hash_AC-4: 175736170bcc
ac_hash_AC-5: 7fe74b36327e
artifact: docs/spec-reviews/WI-021-dave-review-2026-08-11.md
```

## AC Red-Team — 2026-08-11 (standing verdict)

> standing verdict carried verbatim at the 2026-08-11 archive-split; full round history in `write-door-bypasses-rounds.md`; a fresh gate round supersedes this fence.

```verdict
gate: ac-red-team
verdict: PROMOTE
date: 2026-08-11
model: claude-sonnet-5
note: Revision 4 closed round 4's entity=-arm coverage gap structurally (AC-1 now derives at arm granularity; AC-2/AC-4 typed passes name the entity= and extra_fields-only arms as required fixtures by construction) — re-attacked the full AC-1–AC-5 set fresh, verified the arm citations against the live code, and found nothing material.
```

## Architectural Review — 2026-08-11 (round 14, standing verdict)

> standing verdict carried verbatim at the 2026-08-11 archive-split; full round history in `write-door-bypasses-rounds.md`; a fresh gate round supersedes this fence.

```verdict
gate: architect
verdict: REVISE
date: 2026-08-11
model: claude-opus-5
targets: AC-1, #approach
note: My round-13 finding is CLOSED and the round-14 fold went past it — the corpus really is ONE declaring symbol over THREE roots (tests/derivations.py:29-31, python_files_under:137 rglob at :151), the data audit's correction from five modules to six is right (test_loud_fail_harness.py:96 computes modules_using_ast(python_files_under(PACKAGE_ROOT, TESTS_ROOT)) and asserts homes == {SHARED_MODULE_PATH} at :98-106 with a non-vacuity assert at :107-108), and the fold's two own new findings both verify from source: the closure at test_loud_fail_parse.py:308 really is a CALLER-fixpoint (seam_invocation_closure:449-490, seeding at :476-477, caller expansion at :485-487) whose residue equality at :332-335 and propagators at :348 the gate cannot join under DECLARE, and Wall A really does forbid a mkdir/touch-shaped existence guard (PATH_MUTATION_NAMES at derivations.py:50-53 contains mkdir and touch and not exists; test_write_routing.py:87-102 over python_files_under(PACKAGE_ROOT, SCRIPTS_ROOT) at :91) so the round-10 guard must be a read-only Path.exists probe. The NEW finding is on AC-1's THIRD per-arm pin — the placement argument added at round 9 to enforce Dave's precondition 1 — which is stated identically in three places (Finding B line 561, ## Approach :2134-2136, and the brief's AC-1 entry :4956-4958, the one that becomes SIGNED text) as "placement is `above` — the gate call precedes the frame's FIRST `vault_io` MUTATION call — or `in-lock`". The wall is an AST predicate and the only vocabularies the shared module ships are DOOR_NAMES {write_note, create_note, move_note} (derivations.py:45) and COMMIT_FUNCTION_NAMES (:76-79); note_lock is in NEITHER and there is no third set containing it — so, every arm frame re-read this round, the mutation anchor sits BELOW where the design puts the gate: write_markdown_file's is ensure_dir at writer.py:273, SEVEN lines below the convergence point at :266, so a build that leaves the D1 gate call exactly where my round-8 finding found it computes `above`, greens the wall, and still lets note_lock's ensure_dir(sentinel.parent) (vault_io.py:400, home defaulting to target.parent at :350) put <vault>/@Dave/ on disk — the artefact the conductor EXECUTED (## Conductor Booking), and ## Approach :2145-2147 says in terms that this is exactly what the third argument exists to make red. Worse, the two values stop being mutually exclusive: at D4 the in-lock call after base.py:451 also precedes write_note at :456, at D5 :329 precedes :338, at D7 :420 precedes :424, at D8 :821 precedes :882 — so ALL EIGHT arms compute `above`, the four arms the rule REQUIRES in-lock are red on the design's own intended build, and a builder reading the pair lexically against the `with` statement gets the opposite and correct answer with nothing in the document deciding between them (WI-144, inside AC-1's own pin); and the fail-closed default ("`above` is the DEFAULT for an arm the predicate does not recognise, so a ninth arm is RED by omission") stops being fail-closed, because `above` so anchored is satisfied by a gate call anywhere before the write door. This is the round-8 scar re-incurred inside the instrument written to discharge it — the superseded round-8 text was declared false as a claim about the frame for finding the one ensure_dir written in write_markdown_file's body and missing the composition with note_lock (LESSONS #42), and the predicate written to correct it re-encodes that same frame-local reading. The repair is ONE NOUN and keeps every property rounds 9 and 10 bought: anchor `above` on the frame's first `vault_io` call of ANY kind — equivalently its `with vault_io.note_lock(...)` statement — which is present and FIRST in all six arm functions (writer.py:209, base.py:437, writer.py:327, :379, :417, lint_vault.py:819, all re-read), so the anchor is one name, local, syntactic, identical across the derived set and mutually exclusive by construction; the required-value leg takes the same substitution and resolves identically (D4/D5/D6 guarded at base.py:432-433, writer.py:320-321, :374-375 and D8 by this item's added guard are in-lock; D1a/D1b/D1c and D7 take `above`). Blocking rather than a note because the pin's text is one of the three AC-1 pins Dave signs in the re-origination round that is now the item's ONLY remaining blocker — one noun in unsigned text now, a second Dave round later — and it is not the checking-of-the-checking shape ruling 3 excluded, since the consequence is a signed promise (AC-2 conjunct 3) falsified by an artefact already on the record. No item is added, no criterion joins the set, and the unblock does not lengthen.
```

## Data Audit — 2026-08-11 (round 14, standing verdict)

> standing verdict carried verbatim at the 2026-08-11 archive-split; full round history in `write-door-bypasses-rounds.md`; a fresh gate round supersedes this fence.

```verdict
gate: data-premise
verdict: REVISE
date: 2026-08-11
model: claude-opus-5
targets: #exploration-notes, #approach, #grounding-still-owed, #questions-the-later-spec-round-still-owes
note: The four queries owed since round 4 are RUN and I open only ONE open data question against this role's cap of two — but the FIRST fold of their results mis-states the rule they size. Finding B bounds rule (ii)'s live surface with "at D5/D6 a no-frontmatter note raises FrontmatterParseError at writer.py:329/:381 before the gate is reached, so in practice the (c) shape is live only at D1b/D1c" (lines 244-246), and that has buckets (c) and (d) exactly INVERTED against a fact this document established two rounds ago: read from source this round, parse_frontmatter returns ({}, content) for the genuinely fence-less document at parser.py:79-80 with its docstring saying so in terms at :76-77 ("A genuinely fence-less document is NOT an error"), and its two RAISE branches at :94-98 (fence opened, never closed) and :100-108 (yaml.safe_load refused) both sit strictly BELOW the startswith("---") guard so neither can fire on a fence-less note — so at D5/D6 bucket (c) parses to an empty dict, carries no type:, is undeclared and REACHES the gate, while bucket (d) dies above it. The provenance is exact and is nobody's carelessness: the sentence was written at the round-5 fold when the partition had three buckets, my own round-12 finding split them, the round-13 fold recorded the split correctly in G1's amendment, and that correction was propagated to G1, G4, G5(a) and D8's reachability but NEVER back to the one sentence that uses the distinction to SIZE the rule — the grep returns exactly one site, uncorrected through nine rounds. Before the shell pass this was latent over an unknown population; with G1 in it prices out, because rule (ii)'s live vault-side target set at D5/D6 is (b) 4 + (c) 130 = 134 and NOT the ~4 the sentence leaves standing, while the 3 it does count are the only ones that genuinely cannot reach the gate — the inversion moves the number by a factor of thirty in the direction of MORE refusal, at two PUBLIC doors that no path predicate bounds (update_frontmatter_field/_fields take Union[str, Path] with no glob, writer.py:292-296/:350-353). This is NOT disposed of by "fail-closed, so a larger population is stricter", which the round-14 fold's contradiction scan uses to discharge the 137: that is true about correctness and is not what is at issue, because Dave's ruling 2 is not justified on fail-closedness — its own words in ## Conductor Rulings & Grounding are "Chosen against count 1 below: the untyped population is ZERO, so the strictly stronger fail-closed rule has an EMPTY LIVE BLAST RADIUS — the data audit's own 'cheapest safe rule wins' case", that zero was count 1's rglob("@*.md")-scoped number, the round-5 fold itself booked that count 1 is @*.md-scoped and rule (ii) is not, and G1 has now returned 134 at the rule's OWN scope. I am not asking for ruling 2 to be re-ruled and it may well survive untouched; the finding is that its stated reason no longer matches the measured fact, which is the 20%-vs-65% class this seat exists for. Second half, and the one OPEN question: ## Grounding Still Owed says "G1 bounds the notes; this bounds the callers; the live blast radius is their INTERSECTION, and neither half bounds it alone", both halves are now run, neither has been intersected, and ## Questions… item 7 retires the consumer result as "a Scope Boundary sentence rather than a re-grep" — one step short of the number it was raised to produce; I cannot take it in-cage because the nine files are outside this tree, so it is booked as G7, one grep for the same shell-holding actor (of the nine, which reach D1b/D1c/D5/D6 with a name: key on a path outside @*.md). Arithmetic on the pass itself checked and sound: G1's buckets sum to its declared 5,459 census, its non-@ declared cells equal G5(a)'s 3,532 independently, its at-leaf-@ root cell equals G4's 1,786 corpus. I endorse the round-14 architect's anchor finding without extending it and verified its corpus leg from source — note_lock occurs ZERO times in tests/derivations.py, DOOR_NAMES at :45 is {write_note, create_note, move_note}, COMMIT_FUNCTION_NAMES at :76-79, PATH_MUTATION_NAMES at :50-53 holds mkdir and touch and not exists — it is his target and closes on his repair. Both my corrections are decided above from this tree, need no query, add no criterion, and ride the edit already open.
```

## Rounds drawer — where the gate-round records went

The 41 frozen gate-round records of the AC-formation campaign (ac-red-team ×5, architect ×14,
data-premise ×14, spec-writer ×14) live in `write-door-bypasses-rounds.md` (same directory),
moved there 2026-08-11 by the conductor per Dave's split-first ruling — the reference
implementation for workshop WI-267. They are immutable history: consult for archaeology,
never refresh. Everything needed to review, re-originate, or build stays in THIS file.

## Conductor Rulings & Grounding — 2026-08-11 (post-cap, Dave's word)

Recorded by the conductor session resolving `ESC-WI-021-exploring-revise-cap-e4e75157` by hand.
The three rulings are Dave's (conversational, 2026-08-11); the counts were run outside the cage
by the conductor with a shell, read-only against the live vault, method stated below. This
section is the "paste the numbers in" step both the data audit's Required grounding and the
architect's round-3 re-entry path prescribe.

### Rulings (Dave, 2026-08-11)

1. **Gate shape: DECLARE, adopted.** The architect's round-3 ruling stands as written: the gate
   is HANDED its semantic context — it reads only what the write carries plus what the caller
   declares, never the filesystem. The untyped-dispatch rule is DELETED, not repaired; `_owns`
   is not consulted anywhere.
2. **Undeclared cell: rule (ii) — refuse.** An undeclared write that introduces a `name:` is
   refused outright. Chosen against count 1 below: the untyped population is ZERO, so the
   strictly stronger fail-closed rule has an empty live blast radius — the data audit's own
   "cheapest safe rule wins" case.
3. **Altitude ruling (LESSONS #38), issued.** The AC checking machinery is declared sufficiently
   specified. The re-origination round fixes the NAMED defects only — AC-1's per-arm
   pass-what pin, AC-2/AC-3's sentinel exemption, AC-4's `aliases[]`, AC-5 unchanged — with no
   new generator sweeps at higher altitude. Further findings of the
   checking-of-the-checking shape do not block; this is the WI-020-precedent declaration the
   architect requested.

### Grounding counts (2026-08-11, live vault, conductor shell)

Method: `rglob("@*.md")` over the vault; frontmatter parsed with `yaml.safe_load` on the
leading `---` block; Tier-1 evaluated via `NameValidator.validate_strict` from this repo's own
`name_validation.py` (no `allow_phone_sentinel`). Read-only throughout.

- **Count 1 — untyped population: 0 of 3,418.** Every `@*.md` note with parseable frontmatter
  carries a `type:` key. Three files lack frontmatter entirely — all in `_merged_dupes/`
  (archive residue from the June cleanup), not "untyped frontmatter".
- **Count 3 — Finding C re-dated: 79 Tier-1-dirty stored names TOTAL, of which 2 live.**
  The 77 others sit in archive directories (`_merged_dupes/` 61, `_quarantine/` 16). The 2
  live hits are `@+12068523646.md` and `@447950289840.md` — the pure-digit phone-sentinel
  stubs themselves, i.e. intentional WI-083 records, not legacy dirt. Finding C's
  "legacy-dirty names would brick the vault" premise is now historical; the delta rule stands
  on its design argument, as the audit's item 3 anticipated.
- **Sentinel population (`^\+?\d+$`): 3** — the 2 live stubs above plus 1 quarantined copy.
  Small, real, and live: the payload-derived sentinel rule (`person.py:1406`) is justified
  against this population, and the re-origination must carry the AC-2/AC-3 exemption or make
  these three unwritable.

### Re-entry

Per the architect's round-3 path, now unblocked end-to-end: spec-writer rewrites Finding B to
the DECLARE ruling stating the counts above; then Dave re-originates AC-1–AC-5 in ONE round;
then ac-red-team → architect → data-premise → spec-writer.

## Grounding Still Owed — 2026-08-11 (round-5 fold)

The counts in `## Conductor Rulings & Grounding` are the ones that have been RUN. This section is
their complement: what a shell-holding actor still has to run, in the form the rule is stated in, so
the list is one artifact rather than three verdict notes. Every query below needs a shell and vault
access **outside the spec cage** and all of them can be run in one pass, alongside Dave's
re-origination. None of them gates the SHAPE of any rule — the shapes are ruled (Dave's rulings 1–3;
the architect's signature, splitter and DECLARE rulings; the round-5 phone relocation; the round-8
name-identity rule; the round-9 gate-above-lock placement). They size blast radius and they give
build-start re-grounding something that
detects rot. *(Round-8 note, so the list is not misread as growing under a decision: G4 is added this
round and it is a SIZING query for a choice already made in the fold, not an input to it — the round-7
data audit's own reading is that the chosen shape (b′) has a zero live blast radius on the population
G4 counts, and the shapes it would have priced are the two the fold rejected.)*

> **Round-9 note — one item LEAVES this list by being RUN, and one joins.** The round-8 data audit
> booked two new items. **G6 — the tmp-vault execution — is DONE**: the conductor ran it and the result
> is recorded verbatim in `## Conductor Booking`. It settled two things eight reading rounds could not
> (the N2 bypass completes today; the stray directory is created by `note_lock`'s sentinel `mkdir`, not
> by `writer.py:273`) and it is the evidence Dave's precondition 1 was decided against. It is listed
> below as **RUN with its finding** rather than deleted — a discharged query is evidence, and the next
> reader should not have to reconstruct why it stopped being owed. **G5 joins and is still owed**: it is
> the live population that same defect has ALREADY created, and unlike every other item on this list it
> bears on a signed criterion's PREMISE (`AC-3`'s "the legacy-dirt premise is historical") rather than
> only on blast radius.
>
> **Round-10 note — nothing is added, one item is CORRECTED before it runs.** The round-9 data audit's
> finding was decided in-cage against a constant in this tree and needs no query. Its one consequence
> here is free: **G1's path class is restated as `should_skip`'s own predicate** rather than as a
> hand-written two-name list, because `SKIP_DIRS` has six members (`lint_vault.py:SKIP_DIRS:57`) and a
> note under `.trash/` or `Templates/` would otherwise be reported as live while no walker in this repo
> can reach it. **G4 and G5(a) inherit the corrected partition** instead of carrying three hand-copies
> of a wrong one. The list is still four owed queries plus the consumer audit, and none of them gates a
> shape.
>
> **Round-11 note — again nothing is added, and the SAME item is corrected a second time before it
> runs.** The round-10 data audit found that round 10's correction adopted `lint_vault`'s reachability
> notion as the package's, and it is not: `should_skip` binds D8, while a NON-RECURSIVE
> `glob(file_pattern)` (`base.py:load:230`, default at `:195-197`) binds D4 and every Class-2 body
> writer, and D5/D6/D7 are bound by nothing at all (`writer.py:292-296`, `:350-353`, `:414`). **The two
> partitions CROSS** — a note at `<vault>/People/@Al.md` is `should_skip`-FALSE and would be reported
> as live while `PersonRepository` never loads it and `update_fields` raises `ValueError` on it
> (`base.py:427-430`); a note under `_quarantine/` is `should_skip`-TRUE and reported as archived while
> `update_frontmatter_field` writes it today. So **G1 gains one more column, not one more query: every
> bucket additionally split by DEPTH — at the vault root vs. in any subdirectory** — because
> root-vs-subdirectory is the reachability predicate for D4 and the body pass-throughs exactly as
> `should_skip` is for D8. **G4 and G5(a) inherit it** as they inherited the last correction; G5(b) asks
> for `@`-prefixed directories and is unaffected. The column is also what resolves the non-blocking
> observation that count 1 and count 3 were measured with an `rglob` the repositories do not have
> (Finding C's round-11 subsection). The list is still four owed queries plus the consumer audit, and
> none of them gates a shape.
>
> **Round-12 note — nothing is added, no query is written, and ONE existing query gains one free
> column.** The round-11 data audit's finding is decided in-cage from this tree (`note_lock` creates two
> artifacts with different arities — Finding B's round-12 subsection) except for one empirical half:
> whether the lock home already exists in the live vault, which decides whether the stray-directory harm
> at the four in-lock arms is live or is a first-write artifact already spent. **G5(b) answers it on the
> walk it is already performing** — it opens every `@`-prefixed directory anyway, so adding one
> `.exists()` at the vault root and one `iterdir` per directory costs no new corpus and no parsing. The
> list is still four owed queries plus the consumer audit, and none of them gates a shape. **Zero is a
> measurement here too**: an absent or empty root lock home would mean this package's own doors have
> never run against this vault, which is worth knowing before `AC-2` is signed against their behaviour.
>
> **Round-13 note — nothing is added, no query is written, and the LARGEST query gains a fourth BUCKET
> because its partition was not total.** The round-12 data audit found that G1 classifies every vault
> `.md` into (a) frontmatter with `type:`, (b) frontmatter without, (c) no fence — and a note whose fence
> OPENED and did not parse is none of the three: `parse_frontmatter` raises on it
> (`parser.py:parse_frontmatter:94-98` unclosed, `:100-108` YAML refused) and returns `({}, content)` only
> for the genuinely fence-less document at `:79-80`, which IS bucket (c). This repo's own whole-vault
> walker already needs the fourth state and carries a dedicated field for it (`read_vault`'s broad catch at
> `lint_vault.py:124-128`, the `parse_error` field at `:96`/`:121`, the second-chance YAML probe at
> `:131-138`), so a runner implementing G1 as written would either abort the pass on the first such note or
> copy `read_vault`'s shape and file it silently under (b) or (c). **Rule (ii)'s DIRECTION is unaffected** —
> it is fail-closed, so an unparseable note reads as undeclared and a larger population is stricter — but
> every number downstream is: the consumer audit intersects G1, build-start re-grounding re-runs it, and
> G4 and G5(a) inherit its partition. **G1 therefore gains bucket (d)** — *a fence that opened and did not
> parse* — reported separately with the same path-class and depth splits its other three carry, and G4 and
> G5(a) inherit it exactly as they inherited the `should_skip` correction and the depth column. Stated as
> an implementation obligation rather than a preference: the runner wraps the parse in
> `except FrontmatterParseError` (`errors.py:65`) and COUNTS, never swallowing into `{}`. **Zero is a
> measurement in both directions**: an empty (d) says the round-12 conjunct-4 exhibit has no live
> population and the defect was fixture-only; a non-empty (d) says `--fix` is meeting those notes today.
> *(One number does NOT transfer, per the same audit: `read_vault` walks `rglob("*.md")` under
> `should_skip` (`lint_vault.py:111-113`), so a `parse_error` count from a past `lint_vault` run is bucket
> (d) at `should_skip`-false only and says nothing about the archived class or the depth split — the column
> is not discharged by an old lint report.)* The list is still four owed queries plus the consumer audit,
> and none of them gates a shape.
>
> **Round-14 note — THE LIST IS NOW EMPTY. Every query on it has been RUN.** The conductor executed G1,
> G2, G4, G5 and the consumer audit in one read-only pass against the live vault, in the form each rule is
> stated in above, `SKIP_DIRS`/`should_skip` and the depth split per the amended definitions. Results are
> recorded verbatim in `## Conductor Shell Pass`; each row below is marked RUN **with its finding rather
> than deleted**, on the same principle G6 was — a discharged query is evidence, and the next reader should
> not have to reconstruct why it stopped being owed. **What the numbers settle, stated once here so the
> brief does not have to restate it:** G5(b) is **0**, so Finding F's defect has NEVER fired in this vault
> and **`AC-3`'s signed "historical" premise SURVIVES** — measured, not assumed, which is the one thing on
> this list that bore on a criterion's premise rather than its blast radius. G2's deletion column is **0**,
> so the population the dict-arm rule deletes is EMPTY and `### Examples of done` scenario 3's (a)/(b)
> choice loses the behavioural consequence round 7 gave it. G1's bucket (d) is **3** (non-empty), so the
> round-12 conjunct-4 exhibit has a live population rather than being fixture-only. G5(b)'s lock-home
> column is **22 `.lock` files at the vault root**, so this package's doors demonstrably run against this
> vault and `AC-2`'s conjunct-3 scoping is measured rather than only argued. Two results carry NEW spec
> obligations rather than closing one — G2's 19 case-only diffs and the consumer audit's nine files plus
> two live `normalize_phone` importers — and both are booked in `## Questions the later spec round still
> owes` (items 6 and 7) rather than left in a results table. **Nothing on this list is owed any longer;
> what remains before a spec is Dave's re-origination.**

| # | Query | Owed to | What it decides |
|---|---|---|---|
| **G1** | **Rule (ii)'s undeclared population, at the rule's own scope.** Over EVERY `.md` file in the vault (not `rglob("@*.md")`): classify as (a) frontmatter carrying `type:` → declared; (b) frontmatter, no `type:` → undeclared; (c) no frontmatter fence → undeclared; **(d) a fence that OPENED and did not parse → undeclared, and reported as its own bucket** *(amended round-13 fold, per data-premise round 12: the three-bucket partition is NOT TOTAL — `parse_frontmatter` RAISES on this input (`parser.py:parse_frontmatter:94-98`, `:100-108`) and returns `({}, content)` only for the genuinely fence-less document at `:79-80` that IS bucket (c), which is why `read_vault` carries a dedicated `parse_error` field beside its `fm` (`lint_vault.py:96`, `:121`, broad catch at `:124-128`). Implementation obligation: wrap the parse in `except FrontmatterParseError` (`errors.py:65`) and COUNT — do not swallow into `{}`, and do not let one such note abort the pass)*. Report `\|b\|`, `\|c\|` and `\|d\|` **separately**, each split by path class — **and the archive class is `should_skip`'s OWN predicate, not a hand-list** *(amended round-10 fold, per data-premise round 9)*: `any(part in SKIP_DIRS for part in rel.parts)` (`lint_vault.py:should_skip:104-106`) over the six-member `SKIP_DIRS` (`:57`), so the three buckets are (under `@*.md` / `should_skip` true / neither) and `.trash/`, `Templates/`, `src/` and `.obsidian/` stop being counted as live. **And every bucket is additionally split by DEPTH — at the vault ROOT vs. in any subdirectory** *(amended round-11 fold, per data-premise round 10)*, because `should_skip` is only `lint_vault`'s partition (it binds D8) while `BaseRepository.load`'s NON-RECURSIVE `glob(self.file_pattern)` (`base.py:load:230`, default `"@*.md"` at `:195-197`) is the reachability predicate for D4 and every Class-2 body writer, and the two CROSS in both directions. Predicate stated in Finding B; the crossing derived in Finding C's round-11 subsection. | data-premise round 4, Finding 1; supersedes round-1 item 1 and item 4's `@*.md` phrasing; path class corrected, data-premise round 9; depth column added, data-premise round 10; bucket (d) added, data-premise round 12 | **RUN — conductor shell pass, result in `## Conductor Shell Pass`.** Total census 5,459 `.md`; live undeclared = 4 (b) + 130 (c) + 3 (d) = **137**, **none of it under `@*.md`** (count 1's zero stands at its own scope), and **bucket (d) is NON-EMPTY at 3** — the conjunct-4 exhibit has a live population. Full four-bucket table with both splits in that section. *(Original decides-cell, kept as the record of what the number was run FOR.)* Nothing about the rule's direction — (ii) is fail-closed, so a larger population is stricter, not wronger. It sizes the target set the consumer audit then intersects, and it is the number build-start re-grounding re-runs. **The depth column additionally decides which of the counted notes any repository door can reach at all**, and it is what reconciles count 1 / count 3 (measured with `rglob`) against `PersonRepository`'s actual corpus (`glob`, root only). **And bucket (d) decides two things nothing else here can.** It makes the partition TOTAL, so the number is a census rather than a sample with an unnamed remainder — and it sizes the live population behind the round-12 conjunct-4 exhibit: those notes die at `parse_frontmatter` (`lint_vault.py:821`) above any gate call D8 would carry, and every one of the five `auto_fixable=True` producers already excludes them (`lint_vault.py:343`, `:359`, `:388`, `:532`, `:598`, with `apply_fixes` filtering to `auto_fixable` at `:810`), so **G1's undeclared count over-states the set that reaches the gate at D8 by exactly this cell** — the same *two partitions that cross* shape as the depth column, one layer lower, and invisible in the output rather than merely uncorrected until the bucket exists. Zero says the exhibit is fixture-only; non-zero says `--fix` meets those notes today. |
| **G2** | **Finding D reconciliation 2, four cells plus the case cell — reported PER FIELD, plus one deletion column.** Over every stored `emails[]`/`aliases[]` entry, evaluate BOTH `_extract_email_and_name` (`person.py:1286-1298`) and `Email.parse` (`identifier.py:134-160`); report *agree* / *extracted-but-refused* / *not-extracted-but-parsed* / *neither*, plus, within *agree*, how many differ only by CASE. Counts and a sample per cell, **with every cell reported separately for `emails[]` and for `aliases[]`** *(amended round-6 fold, per data-premise round 5)*. **And within the `emails[]` *extracted* cell, how many entries have a non-empty display half whose value is NOT already present in that same note's `aliases[]`** *(amended round-7 fold, per data-premise round 6)*. | data-premise round 4 Finding 2(a); per-field split, data-premise round 5; deletion column, data-premise round 6 | **RUN — conductor shell pass.** `emails[]`: **952 agree, 0 / 0 / 0** on cells 2–4, so the splitter consolidation is a REFACTOR and not a behaviour change on extraction — with **19 case-only diffs**, which fires this cell's own rider and forces the return contract to be stated (booked as `## Questions…` item 6). `aliases[]`: **520 agree** — that IS the address-bearing-alias population `AC-4`'s scoped clause is signed against — 170 neither, 5 case-only. **Deletion column: 0** — the population the dict-arm rule deletes is EMPTY, so scenario 3's (a)/(b) choice has no live consequence. *(Original decides-cell follows as the record of what was run FOR.)* Three things, one pass. The `emails[]` half: whether the splitter consolidation is a refactor or a behaviour change, and how large — non-empty cells 2–3 are a list the spec owes, and a non-empty case cell forces the splitter's return contract to be stated (raw slice vs `Email.parse(...).value`). The `aliases[]` half: the *extracted* cell IS the address-bearing-alias population, which is what Finding I's arm-shape split forks and what `AC-4`'s scoped clause is signed against. **The deletion column:** the dict-arm rule stores the bare address and drops the display half with no destination, and an entry whose display half is already in `aliases[]` loses nothing — so this intersection, not the extracted cell, is the population the fix DELETES, and it is the number `AC-4`'s dict-side clause and `### Examples of done` scenario 3's (a)/(b) choice must be signed against. |
| **G4** | **The Tier-2 / path-divergence population, two columns** *(new, round-8 fold, per data-premise round 7)*. Over every live `@*.md` note with parseable frontmatter — the same corpus and the same walk count 3 already did, with **"live" stated as `should_skip(path) is False`** (`lint_vault.py:should_skip:104-106` over `SKIP_DIRS` at `:57`) rather than as a two-name exclusion *(amended round-10 fold; inherits G1's corrected partition, and — round-11 fold — G1's DEPTH split too: report each column additionally split root vs. subdirectory, because column (b)'s path/field divergence forks on the next `save` only for notes a repository can load; and — round-13 fold — **G1's bucket (d)**, i.e. this corpus's own "parseable frontmatter" qualifier is the COMPLEMENT of (d) and must be reported as a count rather than assumed empty)* — report: **(a)** how many stored `name:` values are Tier-1-CLEAN (`validate_strict` does not raise) but Tier-2-DIRTY (`validate_strict(name) != name`, i.e. a strip or a `\s{2,}` collapse fires), with a sample and a breakdown by which repair fires; and **(b)** how many notes have a filename stem (`path.stem.lstrip("@")`) that differs from the stored `name:` value. | data-premise round 7 | **RUN — conductor shell pass.** Over 1,786 parseable live root `@*.md` (subdir: **0**, which also discharges the depth split for this corpus): **(a) 11** Tier-1-clean / Tier-2-dirty stored names, all double-space collapse — the population (b′) declines to repair, and parked defect 1's scope; **(b) 3** filename-stem ≠ stored-name divergences, named individually in that section — parked defect 1's standing size, forking on next save under every shape. Both small, both non-zero, neither gating. *(Original decides-cell follows.)* **Neither column gates the chosen shape** — the round-8 fold takes (b′), whose live blast radius on column (a) is zero by construction, so this is booked for the same reason G1 is: it sizes, it does not decide. **(a)** is the population (b′) declines to repair — the notes that keep a Tier-2-dirty stored name on every non-`create_stub` path — and it is the number a future rename-the-file item (parked defect 1) would be scoped against; it is ALSO the number that would have priced (a′)/(c′), so recording it keeps the rejected shapes falsifiable rather than merely rejected. **(b)** is the population where path and field have ALREADY diverged, which forks on its next `save` under every shape including (b′), because this item does not rename files; it is parked defect 1's standing size. Count 3 cannot bound either: Tier 1 RAISES and Tier 2 REWRITES with `_raise_on_tier1` between them (`name_validation.py:288-295`), so every Tier-2-dirty name sits inside count 3's clean 3,339 by construction. **Cheap:** one extra string comparison and one `path.stem` read on a walk already performed once, with no new corpus and no new parsing. |
| **G5** | **The population Finding F's defect has ALREADY created, two parts** *(new, round-9 fold, per data-premise round 8)*. On G1's own walk — every `.md` in the vault, NOT `rglob("@*.md")` — report **(a)** every note whose frontmatter carries a `type:` key but whose path leaf does NOT match `@*.md`, i.e. G1's cell (a) reported BY PATH CLASS — **G1's corrected three-bucket partition, `should_skip` and all** *(amended round-10 fold)*, **and by G1's DEPTH split** *(amended round-11 fold: a correctly-named `@*.md` note that has merely been filed into a folder is invisible to `PersonRepository` for a completely different reason than a path-forked one, and no other owed query counts it)* **and with G1's bucket (d) carried through** *(amended round-13 fold: a path-forked note whose fence does not parse has no legible `type:` and so cannot land in cell (a) at all — report it under (d) rather than dropping it, because it is the same defect's output and the same query's blind spot)* — rather than discarded, broken down by `type:` value, with each note's stored `name:` and whether that name is Tier-1-dirty; and **(b)** a listing of every directory in the vault whose own name begins with `@`, with its contents — **plus, on that same walk, whether `<vault>/.obsidian-schemas-locks/` exists at the vault ROOT and how many `<digest>.lock` files it holds, and the same two numbers for each `@`-prefixed directory the listing finds** *(amended round-12 fold, per data-premise round 11; one `.exists()` and one `iterdir` on a directory the query is already opening — no new corpus, no parsing, no new query)*. **Not person-scoped** — `CompanyRepository` inherits `base.py:381` with no `save` override and no name contract at all, and company names carry `/` far more often than person names do. | data-premise round 8; lock-home column, data-premise round 11 | **RUN — conductor shell pass, and this is the one result that decides a signed criterion's PREMISE.** **(b) directories named `@*`: ZERO** — Finding F's defect has never fired in the live vault, so **`AC-3`'s "the legacy-dirt premise is historical" reading SURVIVES**, measured rather than assumed. **Lock-home column: the root `<vault>/.obsidian-schemas-locks/` EXISTS with 22 `.lock` files**, so this package's doors demonstrably run against this vault — which bounds how every other count here is read and confirms `AC-2`'s conjunct-3 scoping from live data rather than from reading `ensure_dir`; no `@`-dir lock homes exist, there being no `@`-dirs. **(a) 3,532** typed notes at non-`@*.md` leaves, overwhelmingly other entity types (meeting 1,555, company 1,501, book 277) whose file convention simply is not `@*.md`; person-typed 131, all but one in skip dirs, the exception being one mis-typed book note booked for hand-repair and not a rule input. **(a-d) 3** path-forked unparseable fences, all book notes. *(Original decides-cell follows.)* **The only owed item that touches a signed criterion's PREMISE rather than its blast radius.** `AC-3` was signed against count 3's finding that the legacy-dirty population is 79 total / 2 live, both intentional sentinel stubs — *"the premise is now historical"*. A note at `<vault>/@X/Y.md` carrying `name: X/Y` is legacy-dirty, is structurally invisible to count 1, count 3 and G4 (their walk is `rglob("@*.md")` and the leaf is `Y.md`) and to G1 (such a note IS `type:`-declared, so it lands in G1's discarded cell (a)) — and once the gate lands it is **unrepairable through every door in this package**, because the repair requires setting the name, which is exactly what is refused, and under the round-8 identity rule the package also declines to normalize it. If (a) or (b) is non-empty, `AC-3`'s "historical" reading was concluded from a corpus that excludes the dirt this item's own headline defect produces, and `AC-2`'s directory clause needs its scope stated (the fix declines to CREATE such directories; it does not remove existing ones). **Cheap:** (a) is one extra breakdown on a cell G1 already computes and discards; (b) is one directory listing that parses nothing. **Zero is a measurement, not a default** — `create_stub` has cleaned the dominant inbound path since WI-105, so it may well be zero, but that is the number that makes `AC-3` safe. **And the new lock-home column decides one thing on a DIFFERENT criterion** *(round-12 fold)*: `AC-2`'s directory conjunct is scoped in the brief to `{D1a, D1b, D1c}` on the argument that at the four in-lock arms the parent is an existing note's parent and its lock home is a one-per-directory-ever artifact — a non-empty root lock home confirms that from live data rather than from reading `ensure_dir`, and an ABSENT one says this package's doors have never been run against this vault, which bounds how every other count here may be read. |
| **G6** | ~~**Execute `repo.save(Person(name="Dave/Bob"))` against a throwaway tmp vault under the DEFAULT lock home and list what is on disk afterwards.**~~ | data-premise round 8, endorsed from architect round 8's arc note | **RUN — by the conductor, result in `## Conductor Booking`.** The call **SUCCEEDED**; disk afterwards carried `<vault>/@Dave/`, `<vault>/@Dave/.obsidian-schemas-locks/`, a `.lock` file inside it, and `<vault>/@Dave/Bob.md`. Two findings beyond the static claim: the N2 bypass is live end-to-end (not merely un-gated in principle), and the stray directory is created by `note_lock`'s `ensure_dir` (`vault_io.py:400`, home defaulting to `target.parent` at `:350`) rather than by `writer.py:273` — so no gate inside `write_markdown_file` can meet `AC-2`'s clause. This is the evidence Dave's precondition 1 (hoist above the lock) was decided against, and it is the LESSONS #42 specimen for this item: one execution settled what eight architectural rounds, five red-team rounds, eight data audits and eight spec-writer rounds all reasoned about and got wrong. |
| ~~G3~~ | ~~Stored `phones[]` entries normalizing to fewer than seven digits (`identifier.py:228`)~~ | data-premise round 4, Finding 2(b) | **MOOT — the condition it was conditional on did not occur.** The audit scoped it *"conditional on the architect's phone-authority ruling — if the gate is to delegate to `Phone.parse`"*. Round 5 chose the relocation shape instead, so `MIN_DIGITS` never enters the dedupe path and there is no refusal to size (Finding G). Withdrawn on the same terms it was raised. |

**Also owed and NOT a vault query — the consumer audit**, carried unchanged from Constraints and
sharpened by G1. `AC-2`'s refusal is a breaking change for HAL9000, exocortex and orchestrator, all
installed with `pip install -e` (`docs/backlog-campaign-2026-07-05.md:98`). Two greps, in the shape
WI-024 used: non-`create_stub` write callers across all three repos, and — new, per the round-5
Finding G resolution — any importer of `obsidian_schemas.repositories.person.normalize_phone` /
`phones_match`, which the compat re-export is there to keep working and which the audit should
confirm rather than assume. G1 bounds the notes; this bounds the callers; the live blast radius is
their intersection, and neither half bounds it alone.

> **RUN — round-14, conductor shell pass.** Both greps executed (non-test, non-venv). **Nine files**
> hold non-`create_stub` write callers across the three consumers, and **two files import
> `normalize_phone`/`phones_match` directly** — so the compat re-export the round-5 fold committed to is
> **load-bearing in live consumers**, confirmed rather than assumed. Both lists are named in
> `## Conductor Shell Pass` and both carry forward as spec obligations, booked as `## Questions the later
> spec round still owes` item 7: the nine files are the finite set `AC-2`'s refusal semantics is read
> against and the scope of the spec's Risk Analysis; the two importers are a Scope Boundary constraint on
> the phone relocation. None of these files is in this repo, so none is a write target.

## Re-origination Brief — for Dave, one round

Every item is a defect a gate found in SIGNED text, with the source that proves it. Nothing here is
new this round except where marked. Three tiers, because they have three different authorities.

> **Unchanged after the round-4 reviews and the round-5 fold — the list has NOT grown.** Both round-4
> gates targeted `#approach` and `#exploration-notes` only, and both said so explicitly ("I add
> nothing to that list"). The one conditional either raised — architect round 4: *"if the gate is to
> delegate to `Phone.parse`, `AC-4` acquires a refusal case … and joins the re-origination set"* —
> **does not fire**, because the round-5 fold chose the relocation shape instead, which carries no
> behaviour delta (Finding G). Architect round-4 note 2's wording correction is folded into the
> `AC-1` entry below rather than added as an item. Dave's one round is still exactly Tier A + Tier B.
>
> **Updated after the round-5 reviews (round-6 fold) — still ONE round, and still Tier A + Tier B, but
> the `AC-4` item has GROWN and I am saying so rather than letting it read as unchanged.** The
> round-5 architectural review did not add an item; it corrected the SHAPE of one already on the list
> (`AC-4`'s `aliases[]`, inside ruling 3's own named set), and sweeping that correction to its class
> found the mirror migration, which lands in one clause of `### Examples of done` — signed text inside
> the same span, so it goes here rather than being fixed in place. Net change to Dave's round: the
> `AC-4` entry gains two scoped sub-clauses instead of one flat sentence, and one Examples-of-done
> clause needs a yes/no. No item was added to Tier A, no criterion joined the set, and `AC-5` remains
> unchanged.
>
> **Updated after the round-6 reviews (round-7 fold) — still ONE round, still Tier A + Tier B, still
> no new criterion, and again the change is to items ALREADY on the list rather than additions.**
> The round-6 architectural review corrected the shape of `AC-1` (its ten-arm floor names two members
> the criterion's own unit cannot derive) and the round-6 data audit corrected the PRICE of `AC-4`'s
> dict-side clause (it deletes a display half that is on disk today). Net change to Dave's round:
> the `AC-1` entry gains a floor correction and a rider clause beside the pass-what pin it already
> carried; the `AC-4` entry's dict-side sub-clause gains the deletion, and the Examples-of-done
> entry's (a)/(b) choice acquires a consequence it did not have. Tier A gains one sentence, because
> both exclusion sets as signed name two things the corrected set does not contain. `AC-5` remains
> unchanged, `AC-2`/`AC-3` are untouched by this round, and nothing new joined ruling 3's named list.
>
> **Updated after the round-7 reviews (round-8 fold) — still ONE round, still Tier A + Tier B, still no
> new criterion, and again the change lands inside an item already on the list.** The round-7
> architectural review found that dropping D2 left the FILENAME derivation (`base.py:381`) above every
> gate call while the gate's name output is not an identity, and offered three shapes; the round-7 data
> audit priced them and recorded that two of the three carry an unmeasured live cost the one number
> anyone has run cannot bound. The fold takes shape **(b′)** — the gate's name output is an IDENTITY —
> in unsigned text, which is where both gates said the choice belongs. Net change to Dave's round: the
> `AC-1` entry's rider clause gains its fixture pin (identifier fields only) plus one control asserting
> the gate never alters a `name`. **No item was added, no criterion joined the set, and no Tier A
> sentence moved.** `AC-2`, `AC-3`, `AC-4` and `AC-5` are untouched by this round.
>
> **Updated after the round-8 reviews, the conductor's EXECUTION and Dave's ruling (round-9 fold) —
> still ONE round, still Tier A + Tier B, and this time the list GROWS BY ONE ITEM. I am saying so
> plainly rather than letting it read as unchanged.** The round-8 architectural review found `AC-2`'s
> signed *"no stray directory is created"* clause unmeetable by any gate inside `write_markdown_file`;
> the round-8 data audit confirmed it from source and added its data half; the conductor executed the
> scenario and confirmed it by artefact (`## Conductor Booking`). **Dave has ruled the fork**
> (`## Conductor Preconditions`, precondition 1): option (a), the gate runs above `note_lock`, and
> `AC-2`'s clause **stands as signed**. Net change to Dave's round: `AC-1` gains a THIRD pin beside the
> pass-what pin and the rider clause — the gate call's placement — and `AC-2` gains a fixture rider
> (default lock home, snapshot oracle) rather than a wording change. **`AC-3` is the new item**: the
> defect succeeds today, so the vault may already hold notes this criterion's "historical" premise was
> concluded without seeing, and that is a scope sentence the criterion should carry deliberately rather
> than by omission. `AC-4` and `AC-5` remain untouched.
>
> **Updated after the round-9 reviews (round-10 fold) — still ONE round, still Tier A + Tier B, still no
> new criterion, and this time the list does NOT grow: both changes land inside items already on it.**
> The round-9 architectural review found the placement pin written LAST round self-contradictory on one
> arm — its second disjunct is a property of a caller two frames away, so the predicate cannot resolve
> D8 and the pin's own default requires `above` for an arm the same pin requires `in-lock` and which
> cannot be hoisted. That is a defect in the wording of an obligation Dave is about to sign, not a
> decision for him, so it is REPAIRED here rather than staged: the disjunct is deleted, the item adds
> D8's missing existence guard, and the `AC-1` entry below states the pin with one local rule. The
> round-9 data audit added the other change, inside the `AC-3` item this brief already carries: the one
> repair door `AC-3` names that could clean count 3's dirt is barred by `SKIP_DIRS`
> (`lint_vault.py:SKIP_DIRS:57`) from the two directories 77 of those 79 notes sit in, so that leg's
> fixture is necessarily synthetic and should be signed as such. Net change to Dave's round: `AC-1`'s
> placement pin reads differently and is now satisfiable; `AC-3` gains one fixture sentence beside the
> scope sentence it already had. **No item was added, no criterion joined the set**, and `AC-2`, `AC-4`
> and `AC-5` are untouched by this round.
>
> **Updated after the round-10 reviews (round-11 fold) — still ONE round, still Tier A + Tier B, still
> no new criterion, and the list does NOT grow: the change lands inside the `AC-3` item already on it.**
> The round-10 architectural review found that `AC-3` — the ONLY criterion pinning Finding C's delta
> rule — is still specified as the hand-list of four doors it was signed with, which is the exact shape
> `AC-2` and `AC-4` were re-based onto `AC-1`'s derived set to escape; it omits `update_frontmatter_field`
> and `update_frontmatter_fields`, the two arms where the record/delta distinction is constructible and
> where the delta is not a dict in the frame at all. The round-10 data audit confirmed it from source and
> supplied the fact that makes it urgent rather than tidy: mapped against the three reachability
> partitions this package actually has, the four doors `AC-3` names have an EMPTY live discriminating
> population while the two it omits are the only arms in the whole set that can reach the 77 archived
> Tier-1-dirty notes at all. Net change to Dave's round: **the `AC-3` entry gains a third clause** —
> re-base its preservation property onto `AC-1`'s derived set, iterated at arm granularity, with the
> exclusion set asserted by equality as `{D1a, D1b, D1c}` — beside the scope sentence (round 9) and the
> synthetic-fixture sentence (round 10) it already carries, and that fixture rider now covers the whole
> criterion with a stated reason rather than one door's accident. **No item was added, no criterion
> joined the set**, and `AC-1`, `AC-2`, `AC-4` and `AC-5` are untouched by this round.
>
> **Updated after the round-11 reviews (round-12 fold) — still ONE round, still Tier A + Tier B, still no
> new criterion, and the list does NOT grow: the change lands inside the `AC-2` item that has been on it
> since round 9.** The round-11 architectural review found that `AC-2` conjoins four promises and binds
> them to all seven arms of `AC-1`'s derived set (typed-pass exclusion `{roundtrip_file}`) — but two of
> the four are properties of the FRAME, not of the gate, and are false at some of those arms: the *"no
> stray directory is created"* conjunct is meetable only where the hoist reaches, and the *"the refusal
> is a `LoudFailError`"* conjunct is false at D8, where `apply_fixes`'s per-file `except Exception`
> swallows it. The round-11 data audit confirmed both from source and supplied the distinction that
> decides the repair: `note_lock` creates **two** artifacts with different arities, so at the four in-lock
> arms the signed conjunct HOLDS and it is the round-9 fixture RIDER — the ambient *"full recursive
> listing unchanged"* oracle, written in this brief — that is red against a correct build, with its
> verdict flipping on how the fixture planted its note. Net change to Dave's round: **the `AC-2` entry
> grows from one rider to a scoping clause, a refusal clause and a replaced oracle**, and the oracle half
> is REPAIRED here rather than staged, because that rider is this brief's own unsigned text rather than
> signed text. **No item was added, no criterion joined the set**, and `AC-1`, `AC-3`, `AC-4` and `AC-5`
> are untouched by this round. This is the last round `round_budget: 16` holds before the re-sign.
>
> **Updated after the round-12 reviews (round-13 fold) — still ONE round, still Tier A + Tier B, still no
> new criterion, and the list does NOT grow: the change is HALF A SENTENCE inside the `AC-2` item's
> conjunct-4 clause, which round 12 wrote.** The round-12 architectural review found that the D8 refusal
> arm round 12 designed filters on `except LoudFailError` — the BASE of the hierarchy
> (`errors.py:LoudFailError:37`) — in a frame that already raises four of its subclasses today, none of
> which can carry a `pattern`; the round-12 data audit confirmed every leg from source and sized the
> exhibit (the notes it is drawn from die at `parse_frontmatter`, `lint_vault.py:821`, above any gate call,
> and all five `auto_fixable=True` producers already exclude them — so the LIVE half of the harm rests on
> `WriteFailedError`/`ExternalWriteConflict` instead, the ordinary condition of linting an open vault).
> **The mechanism is repaired in unsigned text** — the refusal gets its own type, `NameGateRefusal`, and
> the design's absorbing handler and every oracle name it rather than the root (Finding E's round-13
> subsection, `## Approach`, `## Carried Forward`). What lands HERE is the one clause that is signed: the
> conjunct-4 obligation must say the record carries **the gate's own `pattern` key**, so a record without
> one is RED. Net change to Dave's round: half a sentence inside the `AC-2` item that has been on his list
> since round 9. **No item was added, no criterion joined the set**, and `AC-1`, `AC-3`, `AC-4` and `AC-5`
> are untouched by this round. **`round_budget: 12` is SPENT on three of the four gates** — see the
> round-13 fold's re-entry, which books the budget question as a conductor action rather than answering it.
>
> **Updated after the round-13 reviews AND the conductor's shell pass (round-14 fold) — still ONE round,
> still Tier A + Tier B, still no new criterion, and this time the list SHRINKS by one consequence rather
> than growing.** Neither round-13 verdict targeted this brief: both targeted
> `#questions-the-later-spec-round-still-owes`, and their finding — the WI-229 sweep's corpus — is a plan
> obligation with no criterion in it, folded there. What changed here is that **every owed query has been
> RUN** (`## Conductor Shell Pass`), and four items on this list were argued against populations nobody had
> measured. All four now have numbers, and the direction is favourable in three:
> - **`AC-3`'s premise SURVIVES, measured.** G5(b) is **ZERO** — no `@`-prefixed directory exists in the
>   vault, so Finding F's defect has never fired and the *"historical"* reading `AC-3` was signed with is
>   correct. The scope sentence this brief asks for is still worth signing (it states deliberately what was
>   previously true by luck, and the defect succeeds today whether or not it has yet been triggered), but it
>   is now a **precautionary** sentence about an empty population rather than a repair of a criterion
>   concluded from a corpus that excluded its own subject. **Sign it against zero, and say zero.**
> - **`### Examples of done` scenario 3's (a)/(b) choice loses its behavioural consequence.** G2's deletion
>   column is **ZERO**: no live `emails[]` entry has a display half missing from its own note's `aliases[]`,
>   so the population the dict-arm rule deletes is EMPTY. The round-7 correction — *"(b) closes the deletion
>   as well as the example; (a) closes only the example and leaves the deletion standing"* — is still true in
>   principle and now has **no live subject**. So this reverts to what round 6 called it: a **wording pick**,
>   with (a) free. Recorded rather than decided, because it is still signed text and still Dave's.
> - **`AC-2`'s conjunct-3 scoping is confirmed from live data.** G5(b)'s lock-home column found the root
>   `<vault>/.obsidian-schemas-locks/` present with **22** `.lock` files — this package's doors demonstrably
>   run against this vault, which is the fact the scoping argument leaned on and which an absent lock home
>   would have refuted.
> - **`AC-2`'s conjunct-4 exhibit has a live population.** G1's bucket (d) is **3** (three book notes whose
>   fence opens and does not parse), so the D8 refusal-record arm is not a fixture-only concern.
>
> Net change to Dave's round: **no item added, no item removed, one item's (a)/(b) fork gets cheaper, and
> two items can now be signed against measured numbers instead of against "it may well be zero".** `AC-1`,
> `AC-4` and `AC-5` are untouched by this round. **`round_budget` is now 16** (`## Conductor Preconditions`
> round-14 marker), so the post-re-sign verification chain this brief has assumed since round 9 is
> executable as written.

### Tier A — consequences of Dave's own rulings 1 and 2

These are not new findings. Rulings 1 and 2 DELETED the untyped-dispatch rule; `AC-2` and `AC-4`
still assert it, so leaving them as signed leaves the item buildable two ways — the design says
*refuse an undeclared write*, the criteria say an undeclared dict is *"gated exactly as a
`type: person` one is"*. Flagged explicitly because ruling 3's named list does not enumerate them,
so this is the one place the brief goes beyond that list; accept or overrule in the same pass.

- **`AC-2` untyped clause → undeclared clause.** Replace "a dict with `type:` absent, under the
  `@*.md` convention, is gated exactly as a `type: person` one is" with rule (ii): a write that
  introduces a `name:` **without a declared type is refused**, with its own refusal, regardless of
  whether the name matches any Tier-1 pattern. The `@*.md` convention is no longer part of the test.
- **`AC-4` untyped pass → undeclared pass**, the same replacement on the identifier half.
- **Both exclusion sets narrow.** The signed clauses name six dict-shaped arms. Under DECLARE the
  undeclared case is constructible on **four** — `write_markdown_file`'s `frontmatter=` and
  `extra_fields`-only arms (the caller's dict), and `update_frontmatter_field(s)` (the note's own
  `type:`). `update_fields` carries `self.type_name` unconditionally (base.py:188-192, :430, :461)
  and `lint_vault --fix` cannot reach an undeclared note at all (lint_vault.py:318-326, :83, :810).
  Keeping them in would force fixtures with no discriminating power — the defect round 3 of the
  ac-red-team already caught once, on the entity-shaped arms.
- **And both exclusion sets name two NON-MEMBERS** *(new, round-7 fold; consequence of the `AC-1`
  floor correction below)*. Each set as signed contains `BaseRepository.save` and
  `PersonRepository.save`. Under the corrected arm set neither is a member of `AC-1`'s derived set at
  all, so they cannot be *excluded from a pass within it* — an equality assertion over the eight arms
  cannot reconcile against either set as written. **Restate both sets over the eight arms:** the typed
  pass excludes exactly `{roundtrip_file}`; the undeclared pass excludes exactly
  {`write_markdown_file`'s `entity=` arm, `roundtrip_file`}. The two `save` methods drop out of the
  sentence entirely rather than moving sides, and `PersonRepository.save`'s gate call is pinned by
  the rider fixture named under `AC-1` instead.

### Tier B — the named defects ruling 3 enumerates

- **`AC-1` — the per-arm pass-what pin.** *(architect round 3.)* `AC-1(a)/(b)/(c)` resolve which arms
  CALL the gate; nothing constrains what they PASS. A build wiring `gate(introduced_fields)` at all
  ten arms with the type defaulting to `None` greens it completely, and at D4 the delta carries no
  `type:` key (base.py:403-451) so every `update_fields` write lands in the undeclared cell
  permanently — under rule (ii), refused. **Add:** per arm, the declaration passed is the one
  available at that arm (the model's type at D1a; `self.type_name` at D2/D3/D4; the parsed note's
  `type:` at D5/D6 **and at D8** *(round-10 correction: `fm.get("type")` off the in-lock parse at
  `lint_vault.py:821` — not `vf.entity_type`, which `apply_fixes` cannot reach; the value is the same
  string, the binding is not, and the pin is about what the arm PASSES)*), **and where none is
  available that is EXPRESSED rather
  than defaulted**. The ten-arm floor, the driven positive controls and the near-miss are unchanged.
  *(Wording corrected 2026-08-11, round-5 fold, per architect round-4 note 2 — which flags its own
  round-3 phrasing "no arm hardcodes a literal or defaults it" as too strong: two arms legitimately
  have no declaration to pass — `roundtrip_file` (D7), which parses a note it does not judge
  (`writer.py:419`), and D1b/D1c when the caller's dict genuinely carries no `type:`, which is the
  undeclared cell rule (ii) exists for. Folded here because it is free and the note asks for it in
  the same text rather than in a round of its own; it does not widen Dave's list.)*

  **And the floor itself moves, from ten arms to eight** *(NEW, round-7 fold; architect round 6, whose
  finding the round-6 data audit independently confirmed from source and priced at nil data
  consequence).* `AC-1(a)` names *"the ten arms Finding B names"* and asserts them by
  `(qualname, arm)`. Two of the ten bind no dict and serialize nothing —
  `BaseRepository.save` (`base.py:381-395`: it binds a filename and passes `entity=`/`extra_fields=`
  through) and `PersonRepository.save` (`person.py:1269-1272`: it binds nothing at all) — so the
  criterion's OWN unit cannot resolve them, while `BookRepository.save` (`book.py:167-178`) and
  `MeetingRepository.save` (`meeting.py:189-200`), which differ in exactly one expression (the
  filename derivation), are correctly excluded by that same unit in this document's own standing
  notes. As signed, the build's only options are to leave the floor RED at eight, to hand-list the two
  (the vacuity hole ac-red-team round 1 closed), or to widen the predicate until two non-person
  repositories acquire gate call sites. **Add / replace:**
  - the floor is **the eight arms Finding B names** — D1a, D1b, D1c, D4, D5, D6, D7, D8 — *"at
    least"*, asserted by `(qualname, arm)` exactly as before, with the multi-branch and near-miss
    controls unchanged;
  - `BaseRepository.save` and `PersonRepository.save` are **not members and carry no gate call as
    arms**; entity-shaped writes are gated at D1a, and Finding F's no-stray-directory promise is
    carried by the D1 gate call's PLACEMENT rather than by the removal *(corrected round-9 fold: the
    superseded clause read "upstream of `vault_io.ensure_dir` (`writer.py:273` vs the convergence at
    `:266`)", which is true of that one `mkdir` and false of the frame — `note_lock` at `writer.py:209`
    `mkdir`s the sentinel home at `vault_io.py:400` first. See the placement pin below)*;
  - `PersonRepository.save` carries **one gate call as a RIDER** — the entity write-back that keeps
    today's in-place model mutation (`person.py:1317`, `:1343`) observable to callers — which is
    **explicitly outside the derived set** and is pinned by its own named fixture rather than by the
    wall. Stating the exclusion in the criterion is what stops a future sweep either missing it or
    re-deriving it as a ninth member.

  **And the rider's fixture is pinned to the IDENTIFIER fields, beside one control on `name`** *(NEW,
  round-8 fold; architect round 7, whose finding the round-7 data audit confirmed from source and
  priced).* The FILENAME is bound from the raw `entity.name` at `base.py:381`, one frame ABOVE every
  gate call in the corrected set, and `save` neither renames nor unlinks (`base.py:380-401`); neither
  `NameValidator` entry point returns a name byte-identical (`name_validation.py:257`/`:265-266` strip
  and collapse; `clean` repairs at `:283-297`). So a gate that normalized a name would write
  `name: Dave Smith` into `@Dave  Smith.md` and the next `save()` would mint a SECOND note — parked
  defect 1's corruption class, introduced by this item's own fix. The fold takes the architect's shape
  **(b′)**: the gate's name output is an IDENTITY. **Add / replace, as two clauses on the rider:**
  - the rider's write-back covers `emails[]`, `phones[]` and `aliases[]` — the fields
    `_normalize_address_fields` mutates in place today — and **not `name`**, because under the identity
    rule there is nothing on that field to write back;
  - a **separate control asserts the gate never alters a `name`**: a Tier-1-clean, Tier-2-dirty name
    (`"Dave  Smith"`) survives every arm byte-for-byte, and the note's filename stem and its stored
    `name:` are equal after the write. This is the clause that must be RED for a build that reaches for
    `clean` or for `validate_strict`'s return value, and it belongs on `AC-1` rather than `AC-2`
    because it is a property of the gate's OUTPUT, not of its refusal set.

  This is one clause inside an item already on Dave's list; **it does not grow the round**, and it is
  the whole AC consequence of the shape choice — both round-7 gates say so in their own words. The two
  rejected shapes (the rider writing the name back; a gate call above the filename derivation) would
  each have needed G4's column (a) as a price before they could be signed; (b′) does not.

  **And the wall gains a THIRD per-arm argument — the gate call's PLACEMENT** *(NEW, round-9 fold;
  architect round 8, confirmed by data-premise round 8 and by the conductor's execution; shape ruled by
  Dave, precondition 1).* `AC-1(a)/(b)/(c)` resolve which arms CALL the gate and the pass-what pin
  resolves what they PASS. Neither constrains WHERE in the frame the call sits — and that is the
  property `AC-2`'s no-stray-directory clause actually depends on. `write_markdown_file` takes the note
  lock as its first action (`writer.py:209`), and `note_lock`'s outermost acquisition `mkdir`s the
  sentinel's home (`vault_io.py:400`), which defaults to the note's own parent (`vault_io.py:350`,
  `_configured_lock_dir` returning `None` at `:137-152`) — so a gate at the convergence point refuses
  fifty-seven lines after `<vault>/@Dave/` exists. The conductor executed it and the debris is on the
  record (`## Conductor Booking`). **Add, as one clause on the wall's per-arm assertion:**
  - per arm, the wall asserts the triple **(arm, declaration passed, gate-call placement)**, where
    placement is `above` — the gate call precedes the frame's first `vault_io` call of ANY kind (equivalently its `with vault_io.note_lock(...)` statement; corrected per architect round 14 — anchoring on the first MUTATION call let every arm compute `above`) — or
    `in-lock`;
  - the required value is **DERIVED, not listed, by ONE LOCAL rule over the arm's own frame**: it is
    `in-lock` iff that frame refuses on the target's non-existence above its first such act
    (`base.py:432-433`, `writer.py:320-321`, `:374-375`, and — added by this item — `apply_fixes`'s own
    guard above `lint_vault.py:819`), and `above` otherwise. **`above` is the DEFAULT for an arm the
    predicate does not recognise**, so a ninth arm is RED by omission rather than green by it.
    *(Restated round-10 fold, per architect round 9. The round-9 wording carried a second disjunct —
    "or whose target is supplied by a walk of notes already read" — which is a property of a CALLER:
    `apply_fixes` binds `fpath` from a dict keyed on its `issues` parameter (`lint_vault.py:808-815`)
    and the walk is `read_vault`'s `rglob` at `:111`, two frames away, so an AST predicate over the arm
    cannot resolve it. D8 therefore fell to the `above` default while the same pin required it
    `in-lock`, on an arm that cannot be hoisted — one clause, red against the design it enforces. The
    disjunct is deleted and D8 is made to satisfy the one rule instead; the guard is one statement in a
    function this item already edits, and it closes D8's own exposure to the sentinel `mkdir` on a note
    deleted since the walk.)*
  - a second leg is asserted as a **RED consistency check, never as an alternative route to
    `in-lock`**: an arm that passes the gate a value bound inside the lock — D5/D6/D8 parse their
    declaration from the note there (`writer.py:329`, `:381`; `lint_vault.py:821`) — MUST be `in-lock`,
    so an arm the one rule requires `above` while its gate arguments are bound in-lock is a
    contradiction the wall reports, whose repair is that frame's missing guard rather than a hoist;
  - the `above` set is **`write_markdown_file`'s three arms plus `roundtrip_file`** *(D7 added round-10
    fold: its frame carries no guard either, so it takes the default; the placement is free because its
    gate call is handed an empty delta and can never refuse — which is also why `AC-2`/`AC-4` exclude
    it, and it does NOT make D7 exempt from routing, which `AC-1` requires of every member)*. The hoist
    changes no arm's identity — the three `write_markdown_file` bindings still converge on one
    `write_frontmatter` call at `:266`, so the eight-arm floor and its `(qualname, arm)` assertion are
    untouched.

- **`AC-2` — the no-stray-directory clause STANDS AS SIGNED, and gains a fixture rider.** *(NEW,
  round-9 fold; Dave's precondition 1 chose option (a) precisely so the clause would not have to
  narrow.)* No wording change is owed. What IS owed is the discriminating power of the fixture that
  proves it, and it is not free: with an absolute `OBSIDIAN_SCHEMAS_LOCK_DIR` set, `_sentinel_path`
  puts the sentinel outside the vault entirely (`vault_io.py:_sentinel_path:349-351`) and no `@Dave/`
  ever appears — **so a fixture that sets that variable passes against un-hoisted code while production
  fails**. **Add, as a rider on the clause:** the no-stray-directory fixture runs under the DEFAULT lock
  home and asserts `OBSIDIAN_SCHEMAS_LOCK_DIR` is unset; and its oracle is derived from what the test
  itself holds — ~~**snapshot the vault root's full recursive listing immediately before the refused call
  and assert it is unchanged afterwards**~~ **(struck and replaced below, round-12 fold)** — never "the
  vault root's only child is X", which asserts a layout the test did not create (WI-149). The conductor's
  executed scenario is the fixture's shape: `save(Person(name="Dave/Bob"))` against a tmp vault
  (`## Conductor Booking`).

  **And the clause is signed over seven arms while only three frames can keep it — plus a second
  conjunct that is false at a fourth arm** *(NEW, round-12 fold; architect round 11 blocking with a
  second leg, confirmed and sharpened by data-premise round 11, both re-derived from source in Finding
  B's round-12 subsection).* `AC-2` conjoins **four** promises — *refused*, *target left byte-identical*,
  *no stray directory is created*, *the refusal is a `LoudFailError` carrying the stable pattern key and
  no note content* — and binds all four to every arm in `AC-1`'s derived set with the typed-pass
  exclusion `{roundtrip_file}`: seven arms, D1a/D1b/D1c/D4/D5/D6/D8. Conjuncts 1 and 2 are properties of
  the GATE and hold. Conjuncts 3 and 4 are properties of the FRAME:
  - **Conjunct 3 reaches only where the hoist reaches.** Dave's precondition 1 hoists the gate above
    `note_lock` at `write_markdown_file`'s three arms; at D4/D5/D6/D8 the placement rule REQUIRES
    `in-lock`, and three of those four cannot be hoisted at all because their declaration is parsed
    inside the lock (`writer.py:329`, `:381`; `lint_vault.py:821`). By the time the gate speaks there,
    `note_lock`'s outermost acquisition has already run `ensure_dir(sentinel.parent)`
    (`vault_io.py:note_lock:398-400`, before the `yield` at `:424`) on a home defaulting to
    `target.parent` (`:350`, `_configured_lock_dir` returning `None` at `:137-152`) and created the
    `.lock` (`:407-414`), with no compensating action anywhere (`vault_io.py:ensure_dir:618-638`).
  - **Conjunct 4 is false at D8.** `apply_fixes` wraps its per-file body in `try:`
    (`lint_vault.py:apply_fixes:816`) with `except Exception as exc: print(…, file=sys.stderr)` at
    `:902-903`, INSIDE the loop at `:815`, so a `LoudFailError` from the gate is swallowed into a stderr
    line. Every sibling frame carries `except LoudFailError: raise` (`writer.py:341-342`, `:393-394`);
    `apply_fixes` does not, because it predates the gate.

  **Add / replace, as three clauses. The first is the only one that needs a decision from Dave:**
  - **SCOPE conjunct 3 to `{D1a, D1b, D1c}`, asserted BY EQUALITY, with the reason stated** — those are
    the arms that bind what they serialize from their own ARGUMENTS rather than from a parse of the
    target (`writer.py:257`, `:258-261`, `:262-263`), which is why they need no target to exist and are
    the ones the hoist could reach. D4/D5/D6/D8 keep conjuncts 1, 2 and 4, which is what their frames can
    actually promise. **This is the same one frame-local predicate `AC-3`'s new exclusion set uses and
    the placement pin's `above` set is derived from — three criteria, one fact per frame, no
    inter-procedural analysis.** It is also where the harm actually lives: a genuine stray DIRECTORY
    needs a path-mangled parent, and the only frame that mints one is `base.py:381`'s filename derivation
    (Finding F, executed — `## Conductor Booking`). *(The two rejected shapes, recorded so the choice
    stays falsifiable: keeping the clause total and exempting the lock sentinel from the oracle re-installs
    a shape proxy in the one oracle written to remove one, and — data-premise round 11 — it must exempt the
    whole SUBTREE rather than the directory entry, because the per-note `.lock` is the artifact that is
    always new; and moving the lock home off `target.parent` is precondition 1's already-rejected option
    (b), a `vault_io`/WI-004 amendment and a different work item.)*
  - **REPLACE the oracle — repaired here rather than staged, because the struck sentence is this brief's
    own text.** The ambient *"full recursive listing unchanged"* forbids every artifact, including the
    ones `note_lock` is required to create before the gate is reached, so it is RED against a correct
    build at four of seven arms — and its verdict at those arms flips on whether the fixture planted its
    note through a package door (identical sentinel digest, already in the before-snapshot, green) or
    with `Path.write_text` (new digest, red), which is a fixture-construction choice with nothing to do
    with the property. That is LESSONS #35 inside the oracle written to discharge WI-149. **The
    replacement names the artifacts, each computed from a value the test holds** — and it is what
    `### Examples of done` scenario 1 already says in Dave's own words (*"the vault contains no new
    `@Dave/` directory and no `Bob.md` inside one"*): for `save(Person(name="Dave/Bob"))`, assert
    `<vault>/@Dave` does not exist (which subsumes the lock home and the note inside it) and
    `<vault>/@Dave.md` does not exist; for a direct `write_markdown_file(target, …)`, assert `target`,
    `target.parent` (where the test did not create it) and `target.parent/".obsidian-schemas-locks"` do
    not exist. Under the scoping above, the arms this oracle runs at are exactly the arms that need no
    plant, so the flip has no precondition left. **Rider on conjunct 2, from the same sweep:** at those
    three arms the create case has no target for *"left byte-identical"* to refer to, so state it as
    *"a target that existed is unchanged; a target that did not is not created"* — a fixture sentence,
    not a promise change.
  - **STATE what conjunct 4 means at D8**, because a fixture asserting `raises(LoudFailError)` and one
    asserting a recorded refusal are different criteria and the difference is visible. **This fold's
    recommendation, with its reasoning in Finding E:** `apply_fixes` gains a dedicated refusal
    arm above the broad one that records a structured per-file refusal (path plus the
    exception's `pattern` attribute, never note content), prints a line distinguishable from `Fix error
    on …`, CONTINUES to the next file, and reports a refusal count beside its `fixed` count — so the
    criterion asserts a counted, typed refusal record at D8 and a raise at the six door
    arms. The rejected alternative is plain `except LoudFailError: raise`, which matches the siblings
    literally and turns one refused note into a vault-wide repair outage, because the handler is inside
    the per-file loop.

    **And the record must be asserted BY THE GATE'S OWN SIGNAL, which is the half-sentence this clause
    was missing** *(round-13 fold; architect round 12 blocking, confirmed from source by data-premise
    round 12)*. *"A counted, typed refusal record"* is satisfiable without the gate: `LoudFailError` is the
    hierarchy's BASE (`errors.py:LoudFailError:37`) and `apply_fixes`'s per-file `try` already raises four
    of its subclasses before this item touches the frame — `WriteFailedError` from `note_lock` at
    `lint_vault.py:819`, `FrontmatterParseError` from `parse_frontmatter` at `:821`, and
    `WriteFailedError`/`ExternalWriteConflict`/`NoteAlreadyExists` from `write_note` at `:882`/`:900` — so a
    fixture handing `apply_fixes` an issue for a note whose frontmatter fence does not close produces
    exactly that record, with `pattern=None`, on a build carrying **no gate call at D8 at all**. `AC-1`'s
    wall cannot cover for it: the wall proves the arm CALLS, PASSES and sits `in-lock`, never which
    exception the observable record came from. **So the criterion asserts a refusal record carrying the
    gate's own `pattern` key — a record without one is RED** — and, since the design now mints
    `NameGateRefusal(LoudFailError)` for exactly this purpose (unsigned text: Finding E, `## Approach`,
    `## Carried Forward`), the oracle names that type at all seven arms rather than the root. The near-miss
    control that makes it discriminating is one line: the same corrupt-fence note produces NO refusal
    record and still prints `Fix error on …`. *(That last property is also a live diagnostics obligation
    rather than only a fixture: under a root-level filter a lock timeout or an external-writer conflict —
    `ExternalWriteConflict` names *"Obsidian, another process"* in its own docstring, `errors.py:92-95`, the
    ordinary condition of linting an open vault — would be reported as "the package declined this note".)*

  All three clauses sit inside an item already on Dave's list; **the round does not grow**, and the
  scoping needs no decision beyond accepting on `AC-2` the shape `AC-1` and `AC-3` already carry. It goes
  in *this* re-origination rather than the next because ac-red-team runs AFTER the re-sign — the argument
  that held at rounds 9, 10 and 11 — and because the budget holds no twelfth gate round. *(Round-13 fold:
  the third clause gains the pattern-key half-sentence above. Still one item, still one decision — the
  conjunct-3 scoping — and the half-sentence is a tightening of an obligation Dave has not yet signed,
  not a new promise.)*

- **`AC-3` — the "historical" premise was concluded from a corpus that excludes this defect's own
  output.** *(NEW this round — the one item that grows Dave's list; data-premise round 8, and the
  conductor's execution is what makes it live rather than theoretical.)* `AC-3` promises a stored-dirty
  note stays writable for every write that does not set the name, and it was signed against count 3's
  finding that the legacy-dirty population is 79 total / 2 live, both intentional WI-083 sentinel stubs
  — i.e. *"the premise is now historical"*. But `repo.save(Person(name="Dave/Bob"))` **succeeds today**
  (executed, `## Conductor Booking`), and the note it mints sits at `<vault>/@Dave/Bob.md` carrying
  `name: Dave/Bob`. That note is legacy-dirty and is invisible to every number anyone has run: count 1,
  count 3 and G4 all walk `rglob("@*.md")` and its leaf is `Bob.md`; G1 misses it by one cell, because
  it IS `type:`-declared and lands in G1's discarded cell (a). Worse, once the gate lands such a note is
  **unrepairable through every door in this package** — the repair requires setting the name, which is
  refused, and under the round-8 identity rule the package declines to normalize it either. **Add to
  `AC-3`:** a scope sentence stating that the criterion speaks to notes the fix declines to create and
  to stored-dirty notes it leaves writable, and that pre-existing path-forked notes are neither repaired
  nor made writable-by-rename by this item. **Sign it against G5's number** (`## Grounding Still Owed`),
  not against count 3's — G5 is one extra breakdown on G1's own walk plus one directory listing, and it
  is the only owed query that touches a criterion's premise rather than its blast radius. It may well be
  zero; zero is a measurement, and it is the measurement that makes the existing wording safe.

  **G5 HAS RUN, and the number is ZERO** *(round-14 fold; `## Conductor Shell Pass`)*. There is no
  `@`-prefixed directory anywhere in the vault: this defect has never fired, and `AC-3`'s *"historical"*
  premise is **correct as signed**, measured rather than assumed. Two things follow and neither reverses
  this item. The scope sentence is still worth signing — the defect SUCCEEDS today (`## Conductor Booking`),
  so the criterion should state deliberately what is currently true by luck, and the unrepairability
  argument above is unaffected by the population being empty — but it is now **precautionary wording about
  an empty set**, not the repair of a premise concluded from a corpus that excluded its own subject.
  Sign it against zero, and say zero: an `AC-3` that reads *"pre-existing path-forked notes are neither
  repaired nor made writable-by-rename by this item; that population is measured at 0 as of 2026-08-11"* is
  falsifiable by the next reader, which *"the premise is historical"* was not.

  **And one of the four doors this criterion names cannot be exercised against the live population at
  all** *(NEW, round-10 fold; data-premise round 9, decided from a constant in this tree with no query
  owed).* `lint_vault --fix` fixes only what the lint pass found, the pass sees only what `read_vault`
  returned, and `read_vault` drops every path `should_skip` matches (`lint_vault.py:1100-1103`, `:1069`,
  `:109-113`, `:104-106`) — where `SKIP_DIRS` (`lint_vault.py:SKIP_DIRS:57`) contains both
  `_merged_dupes` and `_quarantine`, the directories holding **77 of count 3's 79** Tier-1-dirty stored
  names. The only ones that door can reach are the 2 live hits, which are the WI-083 sentinel stubs and
  are dirty by design. So the `--fix` leg's fixture is necessarily a SYNTHETIC tmp-vault note. **Add to
  `AC-3`:** state that leg's fixture as synthetic and say why — an oracle satisfied identically whether
  or not the door works on the population the criterion was written for is the WI-235 shape, and it is
  the same rider `AC-2`'s fixture carries one criterion over. This is a fixture sentence, not a promise
  change: every door `AC-3` names still commits for a stored-dirty note, which is what the criterion
  asserts. Derivation in Finding C's round-10 subsection.

  **And the door list itself must go — `AC-3` is the last criterion still specified as a hand-list, and
  the two arms it omits carry the whole of its live subject matter** *(NEW, round-11 fold; architect
  round 10 blocking, confirmed and sharpened by data-premise round 10, both re-derived from source
  here).* `AC-3`'s `desc` states its property over four named doors — *"`update_fields` on an unrelated
  field, a body-section append, `roundtrip_file`, and `lint_vault --fix`"*. That is a hand-list, and it
  is the shape `AC-4`'s own `why:` was written to close in ac-red-team round 1: a hand-list *"silently
  exempts the doors it forgot … and exempts the next door by construction"*. `AC-2` and `AC-4` were both
  re-based onto `AC-1`'s derived set for exactly that reason; `AC-3` never was, because rounds 1–5 of
  the ac-red-team each recorded it as *"unchanged and still holds"* and the round-3 extent sweep swept
  its PATTERN extent, never its DOOR extent. Two facts make it live rather than cosmetic:
  - **The omitted arms are D5 and D6, and they are where the distinction is constructible.** At
    `update_frontmatter_field` the introduced fields are two loose parameters (`writer.py:294-295`)
    while the stored record sits bound one line above the natural call site (`:329`, mutated at `:332`),
    so a build gating the merged record greens `AC-1`'s whole per-arm triple (the arm calls, passes the
    declaration the table names for it — the note's own `type:` — and is `in-lock` as the placement rule
    requires), greens `AC-2` (a whole-record gate refuses an introduced dirty name too, and a refusal
    oracle cannot tell *refused because introduced* from *refused because stored*), greens `AC-4`, and
    makes `update_frontmatter_field` **permanently refuse every legacy-dirty note**. `AC-3` does not name
    D5, so nothing asks.
  - **Those two arms are the ONLY doors in this package that can reach the population `AC-3` is about.**
    Of count 3's 79 Tier-1-dirty stored names, 77 sit in `_merged_dupes/` and `_quarantine/`. `--fix` is
    barred by `SKIP_DIRS`; `update_fields` and every body-section append resolve through a root-only
    `glob` (`base.py:230`, `:195-197`, `:343-354`, raising at `:429-430`; `person.py:1538-1540`) and
    never load them; `roundtrip_file` reaches them and introduces nothing. D5/D6 consult no walker at
    all. So the criterion as signed has an empty live discriminating population at every door it names.
    Derivation in Finding C's second round-11 subsection.

  **Add / replace, and the shape is copied verbatim from two criteria in the same fence:** bind `AC-3`'s
  preservation property to **`AC-1`'s derived set, iterated at ARM granularity**, with the exclusion set
  asserted **BY EQUALITY** to be exactly `{write_markdown_file`'s `entity=` arm, its `frontmatter=` arm,
  its `extra_fields`-only arm`}` — i.e. `{D1a, D1b, D1c}` — **with the reason stated rather than left to
  a builder**: those are the arms whose delta IS the whole record (`writer.py:257`, `:258-263`), where a
  note carrying a stored-dirty name cannot be written without re-introducing it and refusal is the
  correct answer, which `AC-2`'s typed pass already asserts. D4, D5, D6, D7 and D8 remain in. Three
  riders ride with it:
  - **the body-section append stays as a named BEHAVIOURAL example, not a member** — it is a Class-2
    pass-through and not an arm, and the criterion should say so rather than leave it to be inferred;
  - **the fixture population is SYNTHETIC for the whole criterion**, not only for the `--fix` leg, and
    for the same stated reason (count 3's two live Tier-1-dirty names are the WI-083 sentinel stubs, which
    the payload rule permits anyway) — so the round-10 rider above widens rather than being duplicated;
  - **a ninth arm added later joins `AC-3` automatically**, which is the whole reason `AC-2` and `AC-4`
    were re-based.

  This is a third clause inside an item already on Dave's list, it needs no decision from him beyond
  accepting the shape his other two criteria already carry, and **it does not grow the round**. It goes in
  *this* re-origination rather than the next because ac-red-team runs AFTER the re-sign, one step too
  late — the same argument that held at round 9.
- **`AC-2` and `AC-3` — the phone-sentinel exemption.** *(spec-writer round 3, confirmed independently
  by architect round 3; re-derived here as Finding H.)* `create_stub` sets `allow_phone_sentinel`
  from the payload at `person.py:1406-1407` and then calls `self.save(person, …)` at `:1475` — D3,
  and D1a beneath it — carrying a `pure_digit_name` (`name_validation.py:373-377`) **by design**, for
  the WI-083 path its own docstring documents (`person.py:1358-1361`). Under `AC-2` as signed that
  save is refused; under the delta rule every *subsequent* entity write for that person is refused
  too, because an entity write's name is always the delta, and `AC-3`'s exemption never reaches it.
  **Add to `AC-2`:** `pure_digit_name` is conditional — permitted when the record it is introduced
  with carries a phone. **Add to `AC-3`:** a phone-sentinel record stays writable through entity
  writes, and `update_fields(person, {"name": "+447…"})` introducing the name *without* the phone is
  refused. Live population: 3 (2 live stubs, 1 quarantined).
- **`AC-4` — `aliases[]`, SCOPED BY ARM SHAPE.** *(spec-writer round 3, confirmed by architect round
  3; scoping added by architect round 5; Finding I.)* The container names `emails[]`/`phones[]` only,
  but `_normalize_address_fields` reads addresses OUT of `person.aliases` (`person.py:1323-1329`) and
  writes display halves back INTO it (`:1331-1333`, `:1339-1343`), and `create_stub` seeds
  `aliases=[email]` with a bare address (`:1448`). A gate that leaves `aliases[]` alone satisfies
  `AC-4` as signed while regressing behaviour D3 has today.

  **The clause must carry the arm-shape scoping, and this is the part that changed since round 4.**
  "Add `aliases[]` to the container, on both sides" asserted FLAT over AC-1's derived set is a
  criterion the design cannot meet on the six dict-shaped arms and can only be *greened* by a new
  corruption: both `aliases[]` behaviours are cross-field MIGRATIONS (an address moves OUT to
  `emails[]` at `person.py:1328`, a display half moves IN from `emails[]` at `:1339-1342`), each
  needing both fields and the destination's dedupe set (`:1327`, `:1331`), and a gate emitting the
  destination key on a dict arm would REPLACE that field's stored list via `frontmatter.update`
  (`base.py:451`) rather than append to it. **Add, as two clauses:**
  - *The entity-shaped arm (D1a), and the D3 rider above it* — `aliases[]` is in the container on both
    sides; both migrations run, preserving what `_normalize_address_fields` does today at
    `person.py:1269`. *(Round-7 fold: this read "D1a/D2/D3" before the arm-set correction below. The
    frames that hold the whole record are D1a and the rider; the behaviour did not move.)*
  - *Dict-shaped arms* — `emails[]`/`phones[]` normalize as AC-4 already requires; `aliases[]` is
    passed through **byte-identical** and the gate emits no field the write did not carry. Asserting
    the byte-identity rather than staying silent is what keeps the clause class-closing: splitting an
    address-bearing alias without its migration would DELETE the address half (`:1331-1333` keeps only
    the display half; a bare-address alias has none and is dropped entirely), so "in place" here means
    identity, and a build that reads it as "split it anyway" must be RED.

  **And the dict-side clause must be signed against what it COSTS, not against "not a regression"**
  *(NEW, round-7 fold; data-premise round 6, verified from source).* On a dict-shaped arm the
  `emails[]` rule stores the bare address, so the extracted display half is dropped with no
  destination — and that half is on disk **today**, embedded in the raw `"Al B <a@b.com>"` entry the
  arm stores verbatim, recoverable by anything that re-splits it. It is a deletion performed by the
  fix, at whole-list scale: `_writeback_identifier` sets `updates["emails"] = person.emails`
  (`person.py:1206-1207`) and routes the WHOLE stored list through `update_fields` (`:1217`), so one
  reuse-branch write-back passes every stored entry on that person through a dict arm. The at-risk
  population is *extracted `emails[]` entries whose display half is absent from that note's own
  `aliases[]`* — entries on notes re-saved through `PersonRepository.save` since WI-109 already have
  it there and lose nothing. **That number is G2's new column** (`## Grounding Still Owed`), and the
  clause should be signed with it rather than with an estimate. Both available options are lossy —
  emitting the destination key would REPLACE the stored list (`base.py:451`) — so this is a choice
  between two losses, not an argument against the split.

  **G2's deletion column HAS RUN, and it is ZERO** *(round-14 fold; `## Conductor Shell Pass`)*. No live
  `emails[]` entry has a display half that is missing from that same note's `aliases[]` — every stored
  entry's display half is already recoverable from `aliases[]`, which is what WI-109's re-saves through
  `PersonRepository.save` accomplished. **So the deletion this clause prices has an EMPTY live population.**
  The clause should still be signed — the rule is what governs the next entry written, and a criterion
  scoped to today's corpus is the WI-235 shape — but it is signed against a measured zero rather than
  against an unbounded loss, and the *"choice between two losses"* framing is now a choice between two
  losses one of which is empty today. The related number worth carrying: **520 address-bearing
  `aliases[]` entries** is the population the arm-shape split actually forks, and **19** `emails[]` entries
  differ from `Email.parse`'s output by CASE only — that second number is not this clause's, it is the
  splitter's return contract, booked as `## Questions the later spec round still owes` item 6.

- **`### Examples of done` — scenario 3's second clause.** *(NEW this round; the one place the brief
  has grown since round 4, and it is inside an item already on the list rather than a new one.)*
  Scenario 3 reads *"…**then** `emails[]` and `phones[]` each still hold exactly one entry, and
  `"Al B"` has landed in `aliases[]`."* Its write is `_writeback_identifier`, which sets
  `updates["emails"] = person.emails` and routes through `update_fields` (`person.py:1204-1217`) —
  **D4, a dict-shaped arm** — so under the scoping above the first clause holds and the second does
  not. `### Examples of done` is a `###` subsection of `## Acceptance Criteria`
  and therefore inside the `ac-signoff` hash span, so it cannot be fixed here. **Two ways to close it,
  Dave's pick:** (a) re-word the second clause to the entity path and let the dict arm
  promise only the collapse; or (b) keep the promise by changing the CALLER — `_writeback_identifier`
  holds the whole `Person`, so it can take the display half back from the gate's result and pass
  `aliases` in the same `updates` dict. (b) preserves the example verbatim, is one caller inside this
  package, and needs no widening of the gate's output contract; (a) is free.

  **The two are NOT equivalent, corrected round-7 fold (data-premise round 6).** Round 6 priced this
  as *"not a regression (today that arm normalizes nothing at all and stores the entry raw)"*. That
  comparison is against `aliases[]` alone and is wrong: today the display half is on disk **inside**
  the raw `emails[]` entry, and the dict-arm rule stores the bare address and drops it — a deletion,
  sized by G2's new column and applied to the whole stored list on every reuse write-back. So
  **(b) closes the deletion as well as the example, for this one caller; (a) closes only the example
  and leaves the deletion standing** at every dict arm including this one. Still Dave's pick, and
  still flagged rather than chosen because either answer changes signed text — but the choice now
  carries a behavioural consequence beyond the wording, and it should be made against G2's number.

  **G2's number is ZERO, so the behavioural consequence is empty and this reverts to a WORDING pick**
  *(round-14 fold; `## Conductor Shell Pass`)*. The round-7 correction stands as a statement about the
  rule — (b) closes the deletion, (a) leaves it standing — but the deletion has no live subject, so **(a)
  is free in practice as well as in principle**, and the decision costs Dave a preference rather than a
  trade-off. Recorded, not decided: it is still signed text inside the `ac-signoff` hash span, and still
  his. **This is the one item on the list that got cheaper this round.**
- **`AC-5` — unchanged**, per ruling 3.

### Tier C — named, and NOT acted on, per ruling 3

Recorded so they are not silently lost. Two of the three need no AC edit at all, which is what makes
the one-round re-origination clean:

- **`AC-2` sweeps "that module's own pattern table", which does not exist**, and a key-unit sweep
  would yield 7 fixtures over 9 branches while missing `empty` entirely. **No AC edit needed:** the
  build creates that table (Finding H orders the reification at BRANCH unit, including `empty`), and
  a branch-unit table of ten records satisfies the criterion exactly as signed. The defect is
  discharged by construction rather than by re-origination.
- **`AC-5`'s sweep unit is the function, but the job can live as one BRANCH** of a function that
  returns something else — `_extract_email_and_name` is itself half that shape
  (`person.py:1292-1298`). Ruling 3 holds `AC-5` unchanged, so this is an **accepted known limit**:
  the sweep is a lower bound on the duplication, as Finding D already says of its own table. Worth a
  follow-on work item if a second implementation is ever found; not this item's.
- **The three-functions-one-shape collapse** (`update_frontmatter_field` /
  `update_frontmatter_fields` / `roundtrip_file` — one body under three parameterizations) would
  shrink the routing surface *before* it is routed (LESSONS #13). It is a different work item, is not
  recommended for absorption, and `AC-1`'s ten-arm floor pins the count against it. Recorded only
  because architect round 3 noted the sequencing constraint had lifted.

## Carried Forward — verified, do not re-litigate

Everything below survived every REVISE, is re-verified against the tree this round, and is lifted
into the later spec rather than re-derived.

- **Approach F is the right approach** — one gate module, routing at the arms, a derived AST wall
  proving the routing total. All three architectural rounds say so explicitly; all three data audits
  say the code premises are in excellent shape.
- **Findings A, D, E, F, G hold**, along with Finding B's arm-granularity refinement and Finding C's
  delta rule (on its design argument — see the re-dating).
- **The architect's two rulings stand and are now reinforced rather than reopened.** *(a) Gate
  signature:* no `existing` parameter, one entry point taking the introduced fields plus the entity
  type, entity arms projecting through `model_to_frontmatter` (`writer.py:88-130`) first, which keeps
  the new module a leaf beside `errors.py`. The sentinel does NOT widen it — Finding H shows the flag
  is payload-derived. *(b) Splitter:* TOTAL, returns `(address | None, display)`, owns the parens form
  before delegating, maps `IdentifierError` to "not an address", does not widen `Email.parse`'s
  angle-bracket gate (`identifier.py:141-144`). Finding D's reconciliation 2 — the laxity delta on
  live data — stays owed to the spec as a behaviour change, not a refactor.
- **`AC-1`'s arm-granularity floor, driven positive controls and near-miss** are the right battery and
  match the precedent (`tests/test_write_routing.py:1-18`), which imports the derivation functions
  rather than re-implementing them. The BATTERY is unaffected by every REVISE; two things are added on
  top of it — the pass-what pin, and *(round-7 fold, architect round 6)* the floor's **cardinality
  correction from ten to eight**, because `BaseRepository.save`/`PersonRepository.save` bind no dict
  and serialize nothing (`base.py:381-395`, `person.py:1269-1272`) exactly as their `book.py`/
  `meeting.py` siblings do not, with `PersonRepository.save` keeping one gate call as a rider outside
  the derived set. Both are re-origination obligations, staged in the brief.

  **And the precedent module is itself INSIDE the corpus the WI-229 sweep walks** *(new, round-14 fold)*.
  `tests/test_write_routing.py` is not only the shape `AC-1`'s battery copies — it is the home of Walls A,
  B, D and E, whose universes are `python_files_under(PACKAGE_ROOT[, SCRIPTS_ROOT])` and which this item's
  two new package modules and four `scripts/lint_vault.py` edits therefore JOIN. Two consequences, both
  carried in `## Questions the later spec round still owes` item 5: the battery must satisfy the walls it
  copies from — no filesystem-mutation capability named outside `vault_io.py`, including in the D8
  existence guard, which must therefore be a read-only `Path.exists` probe — and `AC-1`'s arm sweep has
  exactly ONE legal home under `tests/test_loud_fail_harness.py:96-108`, namely `tests/derivations.py`,
  which is also where the precedent gets its own predicates from (`test_write_routing.py:22-36`,
  `_single_sourced` at `:49-55`). The battery's shape and the wall's constraint agree; they are one
  requirement seen twice, not two.
- **Class 2's pass-throughs cannot introduce a name or an address** — including
  `scripts/migrate_person_to_discuss.py`, which re-emits the frontmatter string verbatim (`:81`,
  `:103`, `:109`) and is correctly not an arm.
- **`REASONS` is a closed frozenset of fifteen** (`errors.py:110-127`) and `bounded_message` raises on
  any non-member (`:139-145`), so the refusal's new reason literal is chosen at SPEC time. The error
  carries the pattern key on a dedicated `pattern` attribute, never in `declared_type`, which
  `base._note_skip` feeds straight back into `_owns` (`base.py:266-274`).
- **The refusal is its OWN hierarchy leaf — `NameGateRefusal(LoudFailError)` — and an ABSORBING handler
  must filter on it, never on the root** *(added round 13, on the round-12 architectural review's blocking
  finding, re-derived from source)*. Forced, not chosen: `LoudFailError` is the base (`errors.py:37`) and
  `apply_fixes`'s per-file `try` already raises four of its subclasses before this item touches the frame —
  `WriteFailedError` from `note_lock` (`lint_vault.py:819`; `vault_io.py:note_lock:387-388`, `:405-406`,
  `:416-417`, `:419-420`), `FrontmatterParseError` from `parse_frontmatter` (`:821`;
  `parser.py:parse_frontmatter:96`, `:107`), and `WriteFailedError`/`ExternalWriteConflict`/
  `NoteAlreadyExists` from `write_note` (`:882`, `:900`) — and NONE of them can carry a `pattern`, because
  `bounded_message`'s keyword set is `path`/`declared_type`/`cause` (`errors.py:bounded_message:134-136`)
  over the hierarchy's one constructor (`:47-54`). **One rule, total over the surface:** a handler that
  RE-RAISES may filter on the root — which is why all seven existing sites are correct unedited
  (`writer.py:341`, `:393`; `person.py:1598`, `:1700`, `:1819`, `:1899`, `:1968`) — while a handler that
  ABSORBS, and every oracle asserting the gate refused, names `NameGateRefusal` and its `pattern`. The new
  class declares no `__init__`, exactly as `StaleEntityWrite` (`errors.py:84-89`) and `NoteAlreadyExists`
  (`:98-103`) do not, so the message bound holds by construction; **its parent is `LoudFailError` directly
  and never `NoteParseError`**, because that subtree is what `_skip_reason` maps to a skip reason and what
  `_note_skip` files into the repository skip surface (`base.py:266-274`) — the note is loadable, a write
  was declined; it costs one `REASONS` literal this item
  already owed; and `base._skip_reason`'s type dispatch (`base.py:_skip_reason:40-46`) stays total, its
  new member falling to *"unreadable"* on a LOAD path the write-side gate never reaches. **Its full price
  is three lines and one paragraph:** the class in `errors.py`, the `REASONS` literal beside it, two lines
  in `obsidian_schemas/__init__.py` (which imports the hierarchy's nine members at `:46-56` and re-exports
  them in `__all__` at `:122-131`, so a consumer's `from obsidian_schemas import …` keeps working), and the
  CLAUDE.md loud-fail note's *"six exported exception classes"* count, which is already stale at nine and
  is a conductor-committed doc line rather than a builder write. Finding E's round-13 subsection carries the
  derivation and the rejected attribute-probe shape.
- **The phone normalization authority relocates to a leaf before the gate exists** *(added round 5)* —
  `obsidian_schemas/phone_normalization.py`, holding `normalize_phone`/`phones_match` verbatim, with
  a compat re-export from `repositories/person.py` and the two deferred imports at
  `identifier.py:236`/`:272` deleted. No behaviour delta, no consumer change, and it lands WI-023's
  scope item 4 (`docs/identity-engine-endgame.md:28`) early. Verified by
  `tests/test_repositories.py:1868-1893` staying green **unedited**. Finding G carries the reasoning
  and the two rejected shapes.
- **The gate's OUTPUT contract: it returns the fields it was handed and never emits a key the write
  did not carry** *(added round 6, ratifying the round-5 architectural review)*. This is forced, not
  chosen — `update_fields` merges by key REPLACEMENT (`base.py:451`), so an emitted destination key
  overwrites that field's stored list. The consequence is the arm-shape split on the two cross-field
  migrations (`person.py:1328` and `:1339-1342`): both run at the entity-shaped arm D1a and at the D3
  rider, where `model_to_frontmatter` hands the gate every declared field (`writer.py:111-116`);
  neither runs on a dict-shaped arm, where `aliases[]` is passed through byte-identical and the
  `emails[]` display half is DELETED rather than merely not migrated *(round-7 correction, data-premise
  round 6 — the population is G2's new column)*. `_normalize_address_fields` is
  SUBSUMED rather than wrapped, `PersonRepository.save` writes the gate's values back onto the entity
  to preserve today's in-model mutation — that write-back IS the rider — and the gate is **idempotent**
  because one `save` invokes it twice (the rider, then D1a). Finding I carries the derivation.
  *(Round-8 narrowing: the rider's write-back is the IDENTIFIER fields only — never `name` — because of
  the identity rule in the next bullet.)*
- **The gate's NAME output is an IDENTITY — refuse, or return byte-for-byte** *(added round 8, taking
  the round-7 architectural review's shape (b′), which the round-7 data audit independently records as
  the only one of three with a zero live blast radius)*. Forced, not chosen: the FILENAME is bound from
  the raw `entity.name` at `base.py:381`, one frame ABOVE every gate call in the corrected arm set, and
  `save` neither renames nor unlinks (`base.py:380-401`), while neither `NameValidator` entry point
  returns a name byte-identical (`validate_strict` strips and collapses at `name_validation.py:257`,
  `:265-266`; `clean` applies the same two repairs at `:283-297`; both sentinel arms return
  `name.strip()` at `:253-254`/`:274-275`). So the gate calls `validate_strict` for its raise behaviour
  and **discards the repaired string**; Tier-2 repair stays a `create_stub`-only behaviour above the
  filename derivation (`person.py:1407`, `:1413`), which is where it already lives and why WI-105 never
  produced this divergence. Three consequences, all checked from source: the rider writes back the
  identifier fields only; the cache key (`base.py:398`, `_get_cache_key` at `:308-310`) agrees with the
  note it just wrote; and `lint_vault --fix`'s `person_missing_name` repair (`lint_vault.py:835-839`),
  which derives the name FROM the path, can no longer emit a name that disagrees with its own file.
  Finding B's round-8 subsection carries the derivation and the two rejected shapes.
- **The gate runs ABOVE `note_lock` at `write_markdown_file`'s three arms — Dave's ruling, decided
  against an execution** *(added round 9; `## Conductor Preconditions` precondition 1, on the round-8
  architectural review's option (A), the round-8 data audit's confirmation and the conductor's run
  recorded in `## Conductor Booking`)*. Forced, not chosen: `write_markdown_file` takes the note lock as
  its FIRST action (`writer.py:209`), and `note_lock`'s outermost acquisition `mkdir`s the sentinel's
  home (`vault_io.py:400`) at a path that DEFAULTS to the note's own parent (`vault_io.py:350`;
  `_configured_lock_dir` returns `None` unless an absolute `OBSIDIAN_SCHEMAS_LOCK_DIR` is set,
  `:137-152`), then creates a `.lock` file inside it (`:410-414`) — all before any fm exists. `ensure_dir`
  carries no compensating action (`:621-624`), so a refusal at the convergence point leaves the debris.
  The superseded argument — *"`ensure_dir` at `writer.py:273` is downstream of `:266`"* — is true of the
  one `mkdir` written in that function's body and false of the frame, and it survived eight
  architectural rounds, five red-team rounds, eight data audits and eight spec-writer rounds because
  every one of them verified it by READING (LESSONS #42). **The hoist is legal because of DECLARE** —
  the gate reads only the payload plus the handed type, so nothing it touches is lock-protected — and it
  is **arm-specific**: D4/D5/D6/D8 keep their in-lock calls, and D5/D6/D8 parse the declaration they
  pass inside that lock. Three consequences: `AC-2`'s clause stands as signed and becomes meetable; the
  wall's per-arm assertion gains a placement argument, defaulting to `above`; and the fixture must run
  under the DEFAULT lock home with the artifact-naming oracle — the "vault root's only child" form of Dave's precondition 1, per the round-12 fold's Finding B correction, superseding the earlier snapshot phrasing — or it has no discriminating power. Finding B's
  round-9 subsection carries the derivation and the whole-set sweep.
  *(Round-10 correction, architect round 9: which arms may be `in-lock` is decided by ONE property of
  the arm's OWN frame — it refuses on the target's non-existence above its first `vault_io` mutation
  call. The superseded clause added "or walks notes already read", which is a property of a caller two
  frames away (`lint_vault.py:808-815` vs the walk at `:111`) and left D8 required both `above` by
  default and `in-lock` by parse. **This item adds D8's missing guard** above `lint_vault.py:819`, one
  statement matching `base.py:432-433` / `writer.py:320-321` / `:374-375`, after which all four in-lock
  arms resolve by the same local rule; D7 takes `above` by the default, free because its delta is
  empty. `move_note` (`vault_io.py:move_note:721-750`) joins the enumeration of `vault_io`'s public
  mutation surface — outside the class, since `quarantine_garbage` derives its destination from the
  existing filename (`lint_vault.py:1044`), but a lower bound must not be stated as a census.)*
- **Reachability in this package is THREE partitions, and they CROSS** *(added round 11, on the round-10
  data audit's finding, re-derived from source)*. `should_skip` over `SKIP_DIRS` (`lint_vault.py:104-106`,
  `:57`) binds **D8** only; `BaseRepository.load`'s **NON-RECURSIVE** `glob(self.file_pattern)`
  (`base.py:230`, default `"@*.md"` at `:195-197`) binds **D4** and every Class-2 body writer, via
  `get_file_path`/`_file_map` (`:343-354`, populated only at `:235`) which raises `ValueError` on a miss
  (`:429-430`; same accessor and same raise at `person.py:1538-1540`); **D5, D6 and D7** are bound by
  nothing at all — a `Union[str, Path]` whose only constraint is `.exists()` (`writer.py:292-296`,
  `:320-321`; `:350-353`, `:374-375`; `:414`). A note at `<vault>/People/@Al.md` is `should_skip`-false
  and unloadable; a note under `_quarantine/` is `should_skip`-true and writable through D5. Two
  consequences that are now load-bearing: **D5/D6 are the only arms that can reach the 77 archived
  Tier-1-dirty notes**, which is why `AC-3`'s door list is a re-origination item rather than a wording
  nit; and **count 1 / count 3's `rglob("@*.md")` is a recursion the repositories do not have**, so 3,418
  is a SUPERSET of `PersonRepository`'s corpus — harmless for fail-closed rule (ii), material for
  `AC-3`'s "historical" reading, and resolved by G1's depth column. Finding C's second round-11
  subsection carries the derivation.
- **`note_lock` creates TWO artifacts, with DIFFERENT arities, and a negative assertion must name which**
  *(added round 12, on the round-11 data audit's finding, re-derived from source)*. The
  `<parent>/.obsidian-schemas-locks/` DIRECTORY is keyed on the target's PARENT
  (`vault_io.py:_sentinel_path:350`, `SENTINEL_DIR_NAME` at `:58`) and is **one per directory, ever** —
  `ensure_dir` is `mkdir(parents=True, exist_ok=True)` (`vault_io.py:ensure_dir:618-638`). The
  `<sha256(str(target))[:32]>.lock` FILE is keyed on the RESOLVED TARGET (`:348`, `_resolved` at `:376`)
  and is **one per note, ever**. Nothing in this package removes either (`:621-624`; the conductor's
  artefact shows both surviving a successful call). Three consequences that are now load-bearing: at the
  four in-lock arms — where the target must already exist for the frame to reach the gate — a refused
  write leaves a new FILE and creates a new DIRECTORY only if that parent was never locked, so `AC-2`'s
  signed directory conjunct HOLDS there and it is the round-9 ambient oracle that goes red; **a genuine
  stray directory is creatable only at `{D1a, D1b, D1c}`**, because it needs the path-mangled parent
  `base.py:381` mints; and an oracle that filters `SENTINEL_DIR_NAME` must filter the whole SUBTREE,
  since the per-note `.lock` inside it is the artifact that is always new. Finding B's round-12
  subsection carries the derivation and the four-conjunct sweep; the live size of the debris is G5(b)'s
  new column.
- ~~**The consumer audit is still owed** and is the largest unstarted piece~~ — **RUN, round 14**
  (`## Conductor Shell Pass`). The refusal is a breaking change for HAL9000, exocortex and orchestrator,
  all installed with `pip install -e` (`docs/backlog-campaign-2026-07-05.md:98`), and the callers are now
  a **finite named set of nine non-test files** rather than an unbounded worry. Rule (ii) sharpens it
  rather than enlarging it — the `@*.md` undeclared population is 0, so the live blast radius is dominated
  by the *declared*-person writes that introduce a Tier-1-dirty name, which is a behaviour those callers
  should not have. *(Round-5 correction: "0" bounds the `@*.md` subset only — rule (ii)'s surface is
  path-agnostic, so the audit's target set is query G1's, not count 1's; G1 has since run and reports
  **137** live undeclared notes, none of them under `@*.md`.)* **And the audit's second grep found a
  constraint rather than a worry:** two consumers import `normalize_phone`/`phones_match` directly
  (HAL9000 `core/contact_resolver.py:13`, exocortex `clients/contacts.py:14`), so the compat re-export the
  round-5 phone relocation committed to is **load-bearing in live code** and its survival is a Scope
  Boundary obligation, booked as `## Questions the later spec round still owes` item 7.

## Questions the later spec round still owes

Carried from the round-3 hand-back, with the two this fold answered struck through.

1. ~~**What does the gate do on a dict-shaped write whose declared `type:` is neither `person` nor
   absent?**~~ **ANSWERED by ruling 1**: it gets that type's contract, and this item defines a
   contract only for `person` — a `type: company` write is declared, is not a person write, and is
   not judged here (WI-022 owns Company). A typo'd type is likewise not `person` and is not judged;
   `lint_vault`'s `missing_type`/`TYPE_TO_MODEL` checks (`lint_vault.py:318-333`) remain the surface
   that catches it. No third dispatch implementation is created.
2. **How does `lint_vault --fix` (D8) express a delta at all?** Still open and still the single
   largest piece of unglamorous work. The fix loop mutates `fm` in place across its `elif` branches
   and serializes the whole dict (`lint_vault.py:876-882`), in `scripts/`, outside the package.
   Threading a per-key record through every branch is the concrete cost. **Narrowed by this fold:**
   the `person_missing_name` branch (`:835-839`) is the one branch that genuinely introduces a name,
   derived from `fpath.stem.lstrip("@")` — so the delta at D8 is small in practice even though the
   threading is not. **Two riders added round-10 fold, both landing in the same edit:** the frame gains
   the existence guard above `note_lock` (`:819`) that makes its `in-lock` placement derivable, and the
   declaration the gate is handed is `fm.get("type")` from the in-lock parse at `:821` — `apply_fixes`
   is handed `issues` and `idx` (`:804-805`) and never the walk's `VaultFile`, so `vf.entity_type` is
   not reachable from this frame and the earlier citation of it was wrong. **A third rider, added
   round-12 fold, landing in the same edit:** the frame also gains a dedicated refusal
   arm above its broad `except Exception` (`:902-903`) that records a structured per-file refusal and
   continues rather than aborting the run, plus a refusal count reported beside `fixed` — without it the
   gate's refusal at D8 is a stderr line and `AC-2`'s fourth conjunct has nothing to assert there
   (Finding E). So this one function takes four changes in one sitting: the existence guard, the delta
   threading, the gate call, and the refusal arm. **Two corrections to that third rider, round-13 fold.**
   (a) The arm catches **`NameGateRefusal`**, not `LoudFailError`: this frame already raises four
   `LoudFailError` subclasses today (`note_lock` at `:819`, `parse_frontmatter` at `:821`, `write_note` at
   `:882`/`:900`), so a root-level filter would count a corrupt fence or a lock timeout as a gate refusal
   and would let `AC-2`'s conjunct 4 green on a build with no gate here at all (Finding E's round-13
   subsection; architect round 12). (b) **Price the change as five lines of INTERFACE, not four of body**
   *(architect round-12 note 2)*: `apply_fixes` returns `int` (`lint_vault.py:apply_fixes:804-806`,
   `return fixed` at `:905`), is called at `:1103` and has its value printed as `Fixed {fixed} issues` on
   the next line (`:1104`), so reporting a refusal count beside it is a signature change on a `scripts/`
   function and its one call site — decide the shape (a `(fixed, refused)` tuple or a small record) in the
   same edit rather than after it.
3. **What happens to `create_stub`'s existing refusal channel** once the same check fires from the
   write path? `NameValidationError` (`name_validation.py:125`) interpolates the offending name into
   its message and is a bare `ValueError` that `chainable_cause` suppresses (`errors.py:212`).
   Finding E resolves the write-path direction; whether `create_stub` keeps raising the old error,
   starts raising the new one, or raises both by entry point is unstated, and three downstream
   repositories catch on it.
4. ~~**Does `create_stub` still validate at all, once every door below it does?**~~ **ANSWERED by the
   round-8 identity rule.** `create_stub`'s call is **KEPT, unchanged, and it is the only Tier-2
   repairer in the package.** Under (b′) the gate is a predicate on `name` and emits no repair, so
   `create_stub`'s `clean` at `person.py:1407` and its `name = clean_result.cleaned_name` at `:1413`
   are the sole surviving Tier-2 site — and they sit ABOVE the filename derivation (`:1423`, `:1453`,
   `self.save` at `:1475`), which is exactly why that ordering must not be disturbed. The create path
   still runs the Tier-1 table twice (`create_stub`, then the gate at the D3 rider and D1a), the two
   AGREE on the sentinel (Finding H) and now also on the output (both leave `create_stub`'s stored
   string untouched), so the second pass is idempotent rather than competing. The only thing that would
   break the arrangement is demoting or deleting `create_stub`'s call, which is now the one thing this
   item must NOT do — the later spec's Scope Boundary names `person.py:1405-1413` as unchanged, and the
   brief's `AC-1` rider control (a Tier-2-dirty name surviving every arm byte-for-byte) is what makes a
   build that moves the repair onto the write path RED.
5. **The WI-229 corpus sweep — SIX modules, and the sweep unit is the FILE, not the assertion.** *(New
   here, round-14 fold. The round-13 fold ran this sweep for the first time and concluded the pins "all
   live in one function"; architect round 13 refuted that from source and data-premise round 13 corrected
   his count from five to six. This item is the DURABLE HOME both verdicts asked for, and the round-13
   fold's own prescriptive tail now points here rather than restating a narrower version of it.)*

   **The corpus, stated once, because naming one module was the second-order form of the same mistake.**
   `tests/derivations.py:python_files_under:137` discovers Python files ON DISK by `rglob("*.py")` under
   whichever roots it is handed — `PACKAGE_ROOT = obsidian_schemas/` (`tests/derivations.py:PACKAGE_ROOT:29`),
   `TESTS_ROOT = tests/` (`:30`), `SCRIPTS_ROOT = scripts/` (`:31`) — deliberately so a new module is
   visible rather than hand-scoped (its own docstring, `:145-148`). **This item joins that corpus at all
   three roots at once:** two new modules under `PACKAGE_ROOT` (the gate and `phone_normalization.py`), at
   least two new sweeps under `TESTS_ROOT` (`AC-1`'s arm sweep, `AC-5`'s job-shape sweep), and four edits
   to `scripts/lint_vault.py` under `SCRIPTS_ROOT`. A sweep scoped to one root, or reported as one module,
   cannot see two thirds of what this item touches.

   **The obligation, stated as a predicate rather than as a count, because both the count and the module
   list have already moved twice:** grep the DECLARING symbol `python_files_under`, READ every file the
   grep reaches, and name EVERY assertion in it that computes over the corpus — never grep count literals,
   and never stop at the first assertion in a file. Run this round, that grep returns `tests/derivations.py`
   (the declaring module) plus SIX test modules. Each row below was read from source this round; the
   "expected to move" column is the claim the build must FALSIFY by re-derivation, not inherit.

   | Module | What it asserts over the corpus | Expected to move? |
   |---|---|---|
   | `tests/test_concurrent_access.py` `test_wi020_derivations_survive_the_routing:1060` (walk at `:1074`) | FOUR cardinality pins — `len(functions_reserializing_parsed_frontmatter) == 4` (`:1077`), `len(non_completed_write_sites) == 8` (`:1085`), `len(base_repository_subclasses) == 4` (`:1088`), `len(load_file_implementations(...)) == 3` (`:1089`) — plus ONE identity pin, `{f.qualname for f in functions_parsing_then_writing − writers} == {"write_markdown_file"}` (`:1081`). It also INVOKES two WI-020 checks directly (`:1094-1095`), so a red there surfaces here too | **No** on all five, if the gate is a module of predicates: it reserializes nothing, returns nothing falsy from a committing door, and subclasses nothing. Re-derive rather than assume — this is the module the round-13 fold named, and it is the WEAKEST instrument of every pair below |
   | `tests/test_loud_fail_parse.py` (walks at `:106`, `:217`) | FIVE, three of them identity. (i) `write_paths == expected`, set EQUALITY over four named `FunctionId`s (`:110-121`) — `base.py:BaseRepository.update_fields`, `writer.py:update_frontmatter_field`, `writer.py:update_frontmatter_fields`, `writer.py:roundtrip_file`, i.e. **arms D4/D5/D6/D7**; (ii) the same discrimination re-asserted three ways (`:128-137`); (iii) `set(sites) == set(site_classes)` over `parse_frontmatter_exit_sites`, keyed POSITIONALLY `sites[0]`–`sites[3]` (`:220-236`); (iv) a SECOND home for two of module 1's cardinality pins — `len(discovered_classes) == 4`, `len(loader_set) == 3` (`:300-305`); (v) the closure partition, below | **(i) is the one to watch.** It is an identity assertion over exactly four of the eight arms this item inserts gate calls into, and `len(writers) == 4` in module 1 survives a member swap that this does not. Inserting a CALL into those four functions does not change what they reserialize, so the expected answer is "no" — but that is a claim, and this is the assertion that falsifies it. (iii) is over `parser.py`, which the Scope Boundary leaves unchanged; note it is a positional index, so a fifth exit site is an `IndexError` rather than a diff |
   | `tests/test_loud_fail_parse.py:294-351` — the closure, called out separately because it is the ONLY assertion in the sweep a NEW MODULE can join | `seam_invocation_closure(files, stop)` at `:308` is a CALLER-fixpoint (`tests/derivations.py:seam_invocation_closure:476-490`) stopped at `write_set \| loader_set \| guard_set`; the partition is asserted in both directions (`:322-330`) and its residue by set EQUALITY — `{f.name for f in residue} == {parse_markdown_file, parse_markdown_content, parse_person, parse_company, parse_book, parse_meeting}` (`:332-335`) — with a matching `propagators` dict asserted `set(propagators) == {f.name for f in residue}` (`:348`) and every member invoked to raise (`:349-351`) | **No, and the reason is a testable consequence of Dave's ruling 1 rather than luck.** Under DECLARE the gate reads only what the write carries plus what the caller declares — it never parses a note — so it names no seam symbol, never enters `closure`, and never reaches `residue`. **If the gate module ever calls the parse seam, `:332-335` and `:348` go RED TOGETHER** and both a residue entry and an invocation that raises `FrontmatterParseError` must be added. State that as the plan's own check on the DECLARE ruling, not as a surprise |
   | `tests/test_loud_fail_write.py` (walk at `:127`) | BIDIRECTIONAL equality against an eight-entry `SiteId` classification map over `person.py` (`:128-149`): `unclassified = set(sites) - set(classification)` empty AND `stale = set(classification) - set(sites)` empty | **Re-derive in the REMOVAL direction.** This item deletes `_normalize_address_fields` by subsumption and edits `person.py`'s write paths; a classified site that disappears is red at `:148-149` exactly as a new unclassified one is red at `:142-147`. The eight entries are all in `append_to_timeline` / `append_to_body_section` / `update_to_discuss_item` / `remove_to_discuss_item` / `_get_body_content`, none of which this item names — so "no", and the removal leg is the one to check |
   | `tests/test_loud_fail_load.py` (walk at `:97`) | `discovered == set(matrix)` against a four-class matrix keyed by repository CLASS (`:103-124`) | **No.** Neither new package module defines a concrete `BaseRepository` subclass. Red only if the gate is shipped as a repository, which no ruling proposes |
   | `tests/test_write_routing.py` — THREE walls, and it is ALSO the module `## Carried Forward` names as `AC-1`'s battery precedent | **Wall A/B/C** at `:87-116`, universe `python_files_under(PACKAGE_ROOT, SCRIPTS_ROOT)` (`:91`): `filesystem_mutation_uses` must return NO member outside `DOOR_MODULE = "obsidian_schemas/vault_io.py"` (`:39-40`, `:94-102`), and Wall B the same for non-read-only `os` members (`:109-116`). **Wall D** at `:361-391`: `loaders` from `PACKAGE_ROOT` (`:368-369`) against `derivers = functions_calling(files, "parse_markdown_file")` over `python_files_under(PACKAGE_ROOT, SCRIPTS_ROOT)` (`:370`) — the ONE walk in the suite that includes `scripts/lint_vault.py` — asserted `derivers == loaders` (`:385-391`). **Wall E** at `:461-473`: `falsy_returns_in(python_files_under(PACKAGE_ROOT), COMMIT_FUNCTION_NAMES)` empty | **Wall A/B is a live CONSTRAINT ON THE NEW CODE, not a pin to re-derive.** Neither new module, and none of the four `lint_vault.py` edits, may name a filesystem-mutation capability — including the round-10 existence guard above `note_lock`, which must be a READ-only probe (`Path.exists`) and not a `mkdir`/`touch`. The wall's own message states the only permitted fix: route through `vault_io`, **never** add an exemption. **Wall D:** the D8 work parses via `parse_frontmatter` (`lint_vault.py:821`), not `parse_markdown_file`, so "no" — but any edit that reaches for `parse_markdown_file` in `scripts/` is red. **Wall E:** "no" unless the gate's name joins `COMMIT_FUNCTION_NAMES`. Noise already discarded by reading: `:526-531`'s `(1, 1, 2, 2)` are computed over a PLANTED module (`_plant:71-80`), which its own docstring puts outside the corpus by construction (`:74-76`) |
   | `tests/test_loud_fail_harness.py:96-108` (walk at `:96`) | **NOT a pin — a PLACEMENT CONSTRAINT, and the only assertion in the suite whose universe GROWS when this item adds a test file.** `live = modules_using_ast(python_files_under(PACKAGE_ROOT, TESTS_ROOT))`, then `homes == {"tests/derivations.py"}` (`:96-106`, `SHARED_MODULE_PATH` at `:31`), plus a non-vacuity assert (`:107-108`). `TESTS_ROOT` is referenced at exactly ONE test-module site in the whole suite — this one | **It binds THIS item's own new code and the answer belongs in `## Write Targets`.** See the placement rider below |

   **The placement rider — the sixth row's consequence, and it is a `## Write Targets` entry rather than
   an implementation choice** *(data-premise round 13, verified from source here).* `AC-1` requires its
   arm set *"DERIVED by an AST sweep (never enumerated)"*, driven *"through the same derivation function
   the live wall calls, never a re-implementation"*; `AC-5` requires a second sweep keyed on the job shape.
   Both are new syntax-traversing predicates, and under the equality above there is exactly **ONE legal
   home for either: `tests/derivations.py`**. Three placements are each natural, each un-forbidden by
   anything written in thirteen rounds, and each RED on the build's first floor run:
   - **in the new wall's own test module** — the shape a builder copies, since `tests/test_write_routing.py`
     is the precedent `AC-1`'s `why` names. That module passes today only because it imports every
     predicate from `tests/derivations.py` (`:22-36`, `_single_sourced` at `:49-55`) and names `ast`
     nowhere;
   - **inside the package**, plausible because this item already adds two modules under
     `obsidian_schemas/` and a derivation used by a wall can look like library code. `PACKAGE_ROOT` is
     inside the walk;
   - **a new shared test helper** (`tests/ast_arms.py` or similar), the tidiest-looking answer for two new
     sweeps. The assertion is an equality on the home SET, so a second home is red even when it is shared,
     imported and non-duplicative.

   The wall is fail-loud in the right direction — a builder cannot silently violate it — so this is a cost
   and design fact rather than a correctness hole. What makes it a plan obligation is that it is otherwise
   on the INHERITED side of the plan's boundary: a build discovers at first suite run that the placement of
   its two central new predicates was decided for it by a WI-020 criterion nobody in this document had
   cited. **Bounding note, stated so the boundary is named and not as a route:** `modules_using_ast`'s
   universe is `obsidian_schemas/` + `tests/` and NOT `scripts/`, so a sweep homed in `scripts/` would be
   invisible to this wall — no criterion puts a derivation there, and using it would be evading a wall
   rather than satisfying one.

   **Two staleness riders that ride along with the same edit, and the rule is the architect's:** fix the
   sentence to state the RULE, never a number that will be stale again. (a) `tests/test_loud_fail_harness.py:8-9`
   and `tests/derivations.py:modules_using_ast:587` both say *"three of the six derivations"*; the local
   `six` dict (`test_loud_fail_harness.py:72-81`) is a REQUIRED SUBSET by its own comment (`:69-71`), so
   two new derivations leave it green and only the two prose counts go stale — the plan should state
   whether the new sweeps JOIN that dict, and if they do, the `six` name and its `len(six) == 6` (`:81`)
   move together. (b) `CLAUDE.md`'s *"six exported exception classes"* line is already wrong at nine
   (`obsidian_schemas/__init__.py:46-56`) and `NameGateRefusal` makes ten — the fix is the
   catch-`LoudFailError` IDIOM sentence, not a tenth number. Note that `CLAUDE.md` is a project-root file:
   under the WI-132 cage rule it is **not** a builder write target and must be declared
   `kind: precondition` in `## Write Targets` or dropped from scope, not written by the caged build.
6. **What contract does the splitter RETURN on the 19 case-only-diff entries?** *(New here, round-14 fold —
   this is G2's own decides-cell firing, not a new question: "a non-empty case cell forces the splitter's
   return contract to be stated (raw slice vs `Email.parse(...).value`)". The cell is now measured at
   **19** on `emails[]` and **5** on `aliases[]` — `## Conductor Shell Pass`.)* Cells 2–3 came back ZERO,
   so the consolidation is a refactor rather than a behaviour change on extraction — but the case cell did
   not, and 19 live entries change value depending on which string the splitter hands back. Decide it at
   spec time and pin it in the Design's output contract; do not leave it to the build.
7. **The consumer audit's result is a FINITE named set, and the spec owes it a Scope Boundary sentence
   rather than a re-grep.** *(New here, round-14 fold; `## Conductor Shell Pass`.)* Nine non-test files
   across the three `pip install -e` consumers hold write callers beyond `create_stub` (HAL9000
   `routers/introductions.py`, `routers/entities.py`, `services/notifications/service.py`,
   `services/notifications/state.py`; exocortex `ingestion/transcript.py`, `jobs/validate_data.py`;
   orchestrator `bin/repair-field-rfc2822.py`, `bin/wi120-merge-dups.py`, `src/executor.py`) — that is the
   set `AC-2`'s refusal semantics must be read against, and it is the set the spec's Risk Analysis is
   scoped to. **And two of them import `normalize_phone`/`phones_match` directly** (HAL9000
   `core/contact_resolver.py:13`, exocortex `clients/contacts.py:14`; orchestrator none), so **the compat
   re-export is load-bearing in live consumers and must survive the round-5 phone relocation** — it is now
   measured rather than assumed. None of these files is in this repo, so none is a write target; they are
   Scope Boundary and Risk Analysis content.

## Conductor Booking — 2026-08-11 (round-8 finding: EXECUTED, confirmed, booked as open item)

Per Dave's directive on the final-round grant (`ae05ab7`): round 8's finding is BOOKED for the
re-origination, not bought as a ninth round. The architect asked for one execution eight reading
rounds could not substitute for; the conductor ran it (LESSONS #42):

```
repo = PersonRepository(<throwaway tmp vault>)
repo.save(Person(name="Dave/Bob"))     # → SUCCEEDED — no refusal anywhere today
# disk afterwards:
#   <vault>/@Dave/                                  ← stray directory
#   <vault>/@Dave/.obsidian-schemas-locks/          ← lock home, created inside it
#   <vault>/@Dave/.obsidian-schemas-locks/48bc….lock
#   <vault>/@Dave/Bob.md                            ← the note, path-mangled
```

Two facts the execution settles, both beyond the architect's static claim:

1. **The N2 bypass is live end-to-end**: `save` on a path-hostile name is not merely un-gated in
   principle — it completes, mints `@Dave/Bob.md`, and pollutes the vault today.
2. **The stray-directory clause is unmeetable by ANY gate inside `write_markdown_file`,
   confirmed by artifact**: the `@Dave/.obsidian-schemas-locks/<hash>.lock` debris is created by
   `note_lock`'s `ensure_dir` (vault_io.py default lock home = `target.parent/…`) before
   `write_markdown_file:266` runs — a refusal there still leaves the directory and lock file.

**Open item for the re-origination round (decision needed, in AC-2's re-sign):** pick one —
(a) hoist the gate above `note_lock` in the door (gate before any filesystem-visible act, keeping
AC-2's clause as signed), (b) relocate the lock home out of `target.parent` (a vault_io/WI-004
amendment — wider blast radius, own trade-offs), or (c) re-scope AC-2's clause to "no stray
directory SURVIVES a refused write" (refuse-then-clean). The architect's round-8 analysis
enumerates the two filesystem-visible acts; option (a) is the smallest and keeps the signed
promise intact, but the call belongs to the re-origination, made against this execution evidence.


## Conductor Preconditions — 2026-08-11 (round-budget fork resolved, Dave's word)

1. **Stray-directory resolution: option (a) adopted** — the gate runs ABOVE `note_lock`: the
   name/identifier gate must refuse BEFORE any filesystem-visible act (before the lock home's
   `ensure_dir` and before `ensure_dir(path.parent)` at writer.py:273). AC-2's "no stray
   directory is created" clause stands as signed and is now meetable; the re-originated AC set
   must pin gate-before-lock ordering (the execution evidence in the Conductor Booking above is
   the fixture shape: `save(Person(name="Dave/Bob"))` against a tmp vault, then assert the vault
   root's only child is the lock-home-free state).
2. **`round_budget: 12`** set in frontmatter (was DEFAULT 8; all three exploring gates were
   8/8). The four fresh rounds per gate are for the post-re-sign verification chain
   (ac-red-team → architect → data-premise → spec-writer). Dave's altitude ruling and the
   booked-not-bought directive continue to bound what rounds may be spent on.

> **Round-14 marker — precondition 2's number has since been RAISED, and this record is kept rather than
> rewritten.** The round-12 architect's second blocking issue was that rounds 9–12 spent the four-per-gate
> reservation BEFORE the re-sign; the round-13 fold booked the fork as a conductor action and recommended
> **16**; both round-13 gates seconded it. **The conductor executed it: frontmatter now carries
> `round_budget: 16`.** Item 2's text above is Dave's original and is left as written — the live value is
> the frontmatter, and the two must not be read as disagreeing. The reservation's MEANING is restored:
> ac-red-team stands at 5, and architect, data-premise and spec-writer each have four rounds for the
> post-re-sign verification chain. Re-entry step 4 of the round-13 fold is therefore executable as written
> and is NOT deleted. **Nothing else in this section moved**; precondition 1 stands exactly as ruled.

## Conductor Shell Pass — 2026-08-11 (G1/G2/G4/G5 + consumer audit: RUN)

The pass the data-premise seat has owed since round 4, run by the conductor (read-only, live
vault, `SKIP_DIRS`/`should_skip` per the amended definitions; script preserved in session
scratchpad `wi021_shellpass.py`). Every owed query is now executed.

### G1 — the undeclared population, total census (5,459 `.md` files)

| bucket | path class | depth | count |
|---|---|---|---|
| (a) declared | at-leaf-@ | root | 1,786 |
| (a) declared | other-live | root | 328 |
| (a) declared | other-live | subdir | 1,565 |
| (a) declared | skip | subdir | 1,639 |
| (b) fm, no `type:` | other-live | root | 2 |
| (b) fm, no `type:` | other-live | subdir | 2 |
| (c) no fence | other-live | root/subdir | 62 / 68 |
| (c) no fence | skip | subdir | 4 |
| (d) fence opened, did not parse | other-live | root | 3 |

Rule (ii)'s live undeclared population: **4 (b) + 130 live (c) + 3 (d)** — none under `@*.md`
(count 1's zero stands at its own scope). Bucket (d) is non-empty: the round-12 conjunct-4
exhibit has a live population of 3 (all book notes, listed under G5(a-d) below).

### G2 — identifier cells, per field (live `@*.md` person notes)

- `emails[]`: **952 agree, 0 extracted-but-refused, 0 not-extracted-but-parsed, 0 neither**;
  case-only-diff within agree: **19** (forces the splitter's return contract to be stated —
  raw slice vs `Email.parse(...).value`).
- `aliases[]`: **520 agree** (the address-bearing-alias population AC-4's scoped clause is
  signed against), 170 neither (plain display names — correct), 5 case-only.
- **Deletion column: 0.** No live `emails[]` entry has a display half missing from that note's
  `aliases[]` — the population the dict-arm rule deletes is EMPTY; scenario 3's (a)/(b) choice
  has no live consequence.

### G4 — Tier-2 / path-divergence (live root `@*.md`, 1,786 parseable; subdir: 0)

- **(a) Tier-1-clean / Tier-2-dirty names: 11** — all double-space collapse (`Dave  Naomi
  Pavie` shape). The population shape (b′) declines to repair; parked defect 1's scope.
- **(b) filename stem ≠ stored name: 3** (`@Dave Martin Right to Left.md` ≠ `…Right To Left`,
  `@Maritza.md` ≠ `Maritza Bonano`, `@Owen OLoan.md` ≠ `Owen O'Loan`) — parked defect 1's
  standing size; forks on next save under every shape.

### G5 — Finding F's already-created population: **ZERO where it matters**

- **(b) directories named `@*`: 0.** Finding F's defect has NEVER fired in the live vault.
  **AC-3's "the legacy-dirt premise is historical" reading SURVIVES** — the count that makes
  AC-3 safe is measured, not assumed.
- Root lock home `<vault>/.obsidian-schemas-locks/` exists with **22** `.lock` files — this
  package's doors demonstrably run against this vault (bounds how every count is read); no
  `@`-dir lock homes exist (there are no `@`-dirs).
- (a) typed notes at non-`@*.md` leaves: 3,532 — overwhelmingly OTHER entity types (meeting
  1,555, company 1,501, book 277) whose file conventions are simply not `@*.md`; person-typed:
  131, all but one in skip dirs (`_merged_dupes/`). The one live curiosity:
  `The New York Trilogy - Paul Auster.md` carries `type: person`, `name: Nicole Stocker` — a
  mis-typed note, booked for hand-repair, not a rule input.
- (a-d) path-forked unparseable fences: 3 (all book notes: `American Gods…`, `anything You
  Want…`, `tomorrow, and tomorrow…`).

### Consumer audit — the two greps (non-test, non-venv)

- **Write callers beyond `create_stub`**: HAL9000 `routers/introductions.py`,
  `routers/entities.py`, `services/notifications/service.py`, `services/notifications/state.py`;
  exocortex `ingestion/transcript.py`, `jobs/validate_data.py`; orchestrator
  `bin/repair-field-rfc2822.py`, `bin/wi120-merge-dups.py`, `src/executor.py`. Nine files —
  the finite set the build's refusal semantics must be checked against.
- **`normalize_phone`/`phones_match` importers**: HAL9000 `core/contact_resolver.py:13`,
  exocortex `clients/contacts.py:14`; orchestrator none. **The compat re-export is
  load-bearing in two consumers** — it must survive the relocation, as the round-5 fold
  committed.

## Hold state — 2026-08-11 (Dave's word, relayed via HQ)

The drive is PARKED at the spawn-budget fork (52/50; escalation standing, deliberately
unanswered). Archive-split done (this file + the rounds drawer). **Nothing proceeds — no
spawns, no D4a presentation, no budget raise — until Dave's explicit go-ahead.** The agreed
sequence on resume: (1) D4a presentation of the eight ACs with the presented-text-vs-live-doc
match made explicit, then sign; (2) verify-once (ONE round per gate, findings booked not
bought); (3) build; spawn_budget raised by ~15 at resume, not before. Pending conductor work
at resume, from the round-14 standing verdicts: the Finding B bucket-inversion sentence repair
(data-premise: rule (ii)'s D5/D6 live surface is 134, not ~4 — ruling 2's stated reason needs
re-stating against the rule-scope number, though the ruling itself may stand); the G7 grep
(which of the nine consumer caller files reach D1b/D1c/D5/D6 with a name: key outside @*.md);
and the architect's one-noun anchor repair is already applied at all five design-text sites.
