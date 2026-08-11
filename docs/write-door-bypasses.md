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
| D8 `lint_vault --fix` | `vf.entity_type`, already computed from `fm.get("type", "")` | `lint_vault.py:140`, `:148`; field declared at `:93` |
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
discharges re-entry step 3's "check the rewrite against member 9": the gate at D8 is handed
`vf.entity_type`, the value the enclosing repair loop already dispatches on at eleven sites (`:186`,
`:188`, `:190`, `:374`, `:423`, `:458`, `:472`, `:490`, `:548`, `:673`, `:688`), so that call frame
carries ONE dispatch implementation instead of the three the superseded design was about to create.

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
  projection of the same entity. A gate call here would be pure redundancy. **Finding F is closed at
  D1a, not at D2, and that is checkable rather than asserted:** `vault_io.ensure_dir(file_path.parent)`
  is at `writer.py:273`, DOWNSTREAM of the convergence point at `:266` (re-read from source this
  round), so a refusal raised at D1a precedes the `mkdir` and no `@Dave/` directory is created — which
  is the byte-identical/no-stray-directory promise `AC-2` makes. **That argument covers the REFUSAL
  case only, and one object `save` binds is not a byte the seam produces**: the FILENAME, bound from the
  raw `entity.name` at `base.py:381` and never revisited. What makes the removal safe on the
  accept-and-normalize path too is the identity rule on the gate's name output — see the round-8
  subsection below, which is where that leg is derived rather than assumed.
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
produces reaches the seam through D1a one frame later"*. That argument is true and it was verified
against the REFUSAL case — a refusal at D1a precedes `vault_io.ensure_dir` (`writer.py:273` vs the
convergence at `:266`), so Finding F stays closed. It says nothing about the ACCEPT-but-normalize case,
and the object that breaks there is not a frontmatter byte at all. Re-derived from source this round:

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
> only thing available one frame above the seam anyway (base.py:437 pre-merge, writer.py:329, :381),
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
(`"rfc2822_leak"`, `"path_hostile_char"`, …) rides in the `declared_type` slot, which
`bounded_message` renders verbatim and which a pattern id may legitimately occupy because it is a
source literal by construction. That is exactly the channel `vault_io._bad_setting` (vault_io.py:88)
uses to name an environment variable without leaking its value. Consumers keep the routing signal;
the person's name never reaches a log line.

### Finding F — the concrete failure this closes

Not hypothetical. `repo.save(Person(name="Dave/Bob"))` → `filename = f"@{name}.md"` (base.py:381) →
`write_markdown_file` → `vault_io.ensure_dir(file_path.parent)` (writer.py:273), which CREATES
`<vault>/@Dave/` and writes `Bob.md` inside it. A spurious directory and an invisible note, from a
name `NameValidator._PATH_HOSTILE_RE` (name_validation.py:95) already knows how to reject and simply
never sees on this path. This is the AC-2 fixture.

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

### Constraints & dependencies

- **WI-004 is the floor, not the home.** `vault_io` owns the mechanical door; this is the semantic
  layer above it, and it must not put semantics inside that module — doing so would give the one
  file the routing wall exempts a second reason to exist.
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
- **Effort:** one to two sessions. **Two** new modules — the gate and the phone leaf — routing at
  **eight arms across six functions** plus one rider at `PersonRepository.save` *(corrected round-7
  fold: two of the previously-counted ten bind no dict and are not arms; taking the architect's shape
  (b) makes the derived set exactly what one stated predicate resolves and REDUCES the work by two
  call sites and a second predicate; **round-8 fold: shape (b′) reduces it again** — declaring the
  gate's name output an identity DELETES a rider obligation rather than adding one, since there is then
  nothing on that field to write back)*, one derived wall, the splitter consolidation *(which is the
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

Build **one semantic gate** — a single function, in a module of its own next to `errors.py`, that
takes the fields a write is INTRODUCING plus **a declared entity type it is HANDED**, and returns
them validated and — on the address fields only — normalized, or refuses. The gate never consults the filesystem: no glob, no path
shape, no sibling note, and `BaseRepository._owns` is not called anywhere in this design. Six of
the eight arms already hold the declaration they must pass — the model's own `type` at D1a,
`self.type_name` at D4 (and at the D3 rider), the note's parsed `type:` at D5/D6, `vf.entity_type` at
D8, with D7 needing none because it introduces nothing — so this
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
`emails[]`, `phones[]`, `aliases[]` — and never `name`** *(round-8 fold)*: those are precisely the
fields `_normalize_address_fields` mutates in place today (`person.py:1317`, `:1343`), and under the
identity rule the gate returns the name unchanged, so there is nothing on that field to write back. That
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
wall. Then prove the routing TOTAL with a derived AST wall in `tests/derivations.py`, so
that the ninth arm someone adds next month, whether a new function or a new branch inside an
existing one, is red at test time rather than silently unguarded. **The wall must pin what each arm
PASSES as well as which arms CALL**: the declaration handed to the gate is the one available at that
arm, **and where none is available that is EXPRESSED rather than defaulted** — without that, wiring
all eight arms with the type defaulting to `None` greens the routing while every `update_fields` write
(whose delta carries no `type:` key) escapes the contract permanently. *(Wording aligned with the
re-origination brief's `AC-1` entry, 2026-08-11 round-6 fold, per architect round-4 note 2: the
round-3 phrasing "no arm hardcodes a literal or defaults it" is too strong, because two arms
legitimately have no declaration to pass — `roundtrip_file` (D7), which parses a note it does not
judge (`writer.py:419`), and D1b/D1c when the caller's dict genuinely carries no `type:`, which is
the undeclared cell rule (ii) exists for. Corrected here so `## Approach` and the brief do not state
the pin two ways.)*

The gate judges the DELTA, never the stored record, which is what keeps a note writable by the tools
whose job is to repair it. Refusals convert to a `LoudFailError` carrying the stable NameValidator
pattern key on a **dedicated `pattern` attribute** — not in `declared_type`, which `base._note_skip`
already feeds back into `_owns` (base.py:266-274) — and no note content, so `except LoudFailError`
remains the one idiom for "this package refused". The refusal's reason literal must be chosen at spec
time and added to `REASONS`, a closed frozenset of fifteen (`errors.py:110-127`) that
`bounded_message` refuses any non-member of (`errors.py:139-145`).

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

## AC Red-Team — 2026-08-11

Read in the prescribed order: `## Intent`, `### Examples of done`, `## Problem / Motivation` plus
Exploration Notes (Findings A–G, the approaches-considered table, the parked-defects list), then
`## Acceptance Criteria` last. Attacked with the One Question: could a builder green this set while
doing as little of the real work as possible, or while honestly misreading it — and would greening
it mean the Intent was actually served?

**Finding 1 — CRITICAL — AC-1's derived-set predicate has no floor, so it is satisfiable by a vacuous
sweep, and the vacuity propagates into AC-2.** AC-1's `desc` requires the door set be "DERIVED by an
AST sweep (never enumerated)" but states no minimum cardinality and no positive-control fixture
proving the sweep predicate actually resolves the door shapes Finding B names (D1–D8, all six
`f"---\n{yaml}---\n"` sites `write_frontmatter` feeds). A predicate that is too narrow — matches on
one import alias, one call shape, or a not-yet-existing marker — can legitimately discover an EMPTY
or near-empty set and the check (`test_every_frontmatter_door_routes_through_the_semantic_gate`)
still passes: "every member of {} routes through the gate" is vacuously true. That is the WI-130
specimen (satisfiable with zero implementation written) landing on the exact mechanism — an AST
sweep — that spec-quality-bar's WI-235 "shape controls for a counting wall" rule exists for: a
`matches == N` oracle (here N could be 0) carries no information about the matcher's reach without a
driven positive-control fixture per claimed door shape. Worse, AC-2's `desc` delegates its own door
coverage to "every door in AC-1's derived set" — so if AC-1's sweep under-resolves, AC-2's refusal
guarantee silently shrinks with it. A builder whose sweep matches only 2 of the 8 named doors
satisfies AC-1 AND AC-2 in full while 6 real doors stay open — exactly the failure this item exists
to close. What would have to change: AC-1 needs either a minimum-cardinality assertion (the derived
set has ≥8 members, or names D1–D8 as a floor) or driven positive-control fixtures — one known door
per shape in Finding B's table — the sweep must catch, plus a near-miss fixture (a function that
touches frontmatter but isn't a write door) it must NOT catch.

**Finding 2 — CRITICAL — AC-4 claims "ANY door" but enumerates a strict subset, excluding D1
(`write_markdown_file(entity=…)`), which Finding B itself already shows unnormalized today.** AC-4's
desc: "An identifier arriving through ANY door — save, update_fields, update_frontmatter_field(s),
and `_writeback_identifier`'s reuse branch — lands in emails[]/phones[] in the same normalized
form…" The em-dash list is offered as the exhaustive account of "ANY door," but it omits D1
(`writer.write_markdown_file(entity=…)`, the public API Finding B's own table marks "no" for address
normalization, the same row class as D3 which the Approach commits to fixing) and D8 (`lint_vault
--fix`). D1 is not hypothetical: it is a documented public entry point (README.md:196 per Finding B)
a caller can invoke directly with a `Person` carrying an unnormalized `emails`/`aliases` entry,
bypassing `PersonRepository.save`'s `_normalize_address_fields` entirely — the same shape as the
concrete Finding F scenario, on the identifier axis instead of the name axis. Contrast AC-2, which
ties its coverage to "every door in AC-1's derived set" (dynamic, total by construction); AC-4
hardcodes four call sites instead, so a ninth door — or an EXISTING door the enumeration simply
forgot — is silently exempt from the identifier-normalization guarantee even though `## Approach`
explicitly commits to routing "all eight doors" including `write_markdown_file`. A builder can
satisfy AC-4 to the letter while `write_markdown_file(entity=Person(emails=["Name <A@B.com>"]))`
still writes an unnormalized entry. What would have to change: bind AC-4 to AC-1's derived set the
same way AC-2 does ("every door in AC-1's derived set"), or explicitly add D1 and D8 to the named
list and justify why D7 is the only legitimate exclusion (Finding C: `roundtrip_file` introduces
nothing).

**Finding 3 — MATERIAL — Finding B's own unresolved "no-`type:` key" dispatch residue is not covered
by any AC.** Exploration Notes, Finding B, states plainly: "a hand-created note with no `type:` key
is invisible to a `type`-keyed dispatch… the spec must pick one rule rather than inventing a
second," and defers the choice to the architect. No AC exercises this case. If the eventual dispatch
rule resolves an untyped note as "not a person write" — the likeliest default for a `type`-keyed
dispatch — a hand-created or legacy note with no `type:` key can carry a bad name or an unnormalized
address through every door in AC-1's derived set with zero AC catching it, because dispatch decides
per-write whether the gate fires at all, upstream of everything AC-1–AC-5 test. This is the class the
role instructions flag as the worst-defect shape: an absence, not a wrong assertion. What would have
to change: either the AC set states the no-`type:` case is out of scope for this item (and says so),
or AC-1/AC-2 add a fixture using a `type:`-less frontmatter dict and pin the chosen behavior.

**Finding 4 — MATERIAL — AC-5's "exactly one implementation" is operationalized as a parseaddr-call
sweep, which is narrower than the property it claims to close.** AC-5 claims "Exactly ONE
implementation of 'split a display-name/address blob into (address, display)' exists in the
package," but derives its fixture space by "sweeping for parseaddr uses." A second implementation of
the SAME job that does not call `parseaddr` directly — a hand-rolled regex splitter, a manual
`str.split('<')`, or a call through `email.utils` under a different name — duplicates the job Finding
D says must collapse to one authority, and is invisible to a sweep keyed on the literal `parseaddr`
symbol. The AC's own desc names the property ("exactly one implementation of the job"); the check's
fixture space names the mechanism ("parseaddr call sites") one level narrower than the property,
which is the WI-185 shape — a generator that does not actually span the class it closes. What would
have to change: broaden the sweep's target predicate to the JOB (any function returning an
`(address, display)`-shaped split, however implemented) rather than the `parseaddr` symbol, or add
prose stating the narrower scope is intentional because Finding D's own audit table was itself built
by grepping for `parseaddr` and no other implementation shape is plausible given the codebase's
conventions — the current draft states neither.

Also attacked and held: AC-2's Tier-1 pattern sweep is genuinely class-closing (swept from
`NameValidator`'s own pattern table, not sampled — directly answers the WI-185/WI-131 specimen);
AC-2's byte-identical/no-stray-directory clauses pin Finding F concretely; AC-3's delta-rule test
correctly distinguishes "sets the name" from "preserves the name," and its third example (refusing an
`update_fields` call that redundantly re-asserts the SAME already-dirty stored value) is consistent
with the delta rule as stated in Finding C rather than a contradiction; every `check:` names a bare
`test_*` function, none absent or a pytest node id (Check 10 / WI-248 clean); no mutually
unsatisfiable pair found across AC-1–AC-5.

```verdict
gate: ac-red-team
verdict: REVISE
date: 2026-08-11
model: claude-sonnet-5
targets: AC-1, AC-2, AC-4, AC-5, #exploration-notes
note: Vacuous/gameable coverage gaps (AC-1's floorless sweep cascading into AC-2; AC-4's hardcoded door list vs. AC-1's total set) plus an uncovered no-type dispatch residue and a narrow AC-5 generator.
```

### Re-verify — Revision 1 fold, round 2 (same day, fresh spawn)

Re-spawned cold against the doc as it now stands, after `ideation-partner`'s Revision 1 fold (the
note prefacing `## Acceptance Criteria` claims it answers round 1's four findings). Re-read in the
prescribed order — `## Intent`, `### Examples of done`, `## Problem / Motivation` plus Exploration
Notes, `## Acceptance Criteria` last — attacking the REVISED set fresh rather than trusting the
fold's own account of itself.

**Findings 1, 2, 4 — FIXED.** AC-1 now states an explicit floor ("the derived set contains AT LEAST
the eight doors… asserted by qualname… so a predicate that resolves fewer is RED") plus a driven
positive-control battery ((b) a planted scratch module, one function per door SHAPE, matched through
the live derivation function) and a near-miss ((c) mutate-but-don't-serialize, must NOT match). A
predicate that under-resolves, or one loose enough to catch the near-miss, is now RED rather than
silently vacuously green — round 1's Finding 1 is closed. AC-4 is now bound to "AC-1's derived
set… iterated, not a hand-listed subset," with the exclusion set asserted to be exactly
`{roundtrip_file}` — `write_markdown_file` (D1) and `lint_vault --fix` (D8), both silently exempt
under the old hand-list, are back in scope by construction; round 1's Finding 2 is closed. AC-5's
sweep is now keyed on the JOB SHAPE (a 2-tuple-returning function whose body carries
address-splitting evidence) with per-shape positive controls (a `parseaddr` call, a hand-rolled
regex, a bare `raw.split('<')`) and a near-miss (differently-shaped return) — round 1's Finding 4 is
closed.

**Finding 3 — HALF-FIXED, and the surviving half is a NEW CRITICAL.** Round 1's Finding 3 named the
no-`type:` dispatch residue as putting BOTH "a bad name or an unnormalized address" through every
door with zero AC catching it. The fold answered only the name half: AC-2 gained an explicit untyped
clause — "at every dict-shaped door in that set, a frontmatter dict with `type:` absent… is gated
exactly as a `type: person` one is." AC-4 (identifier normalization) got no corresponding clause and
no untyped fixture; its `desc`/`why` carry no mention of the `type:`-present/absent dimension at all.

Concrete failure scenario: a legacy/hand-created person note with no `type:` key, living under the
`@*.md` naming convention, already has `emails: ["a@b.com"]`. A caller does
`update_fields(person, {"emails": ["Name <A@B.com>"]})` — D4, inside AC-1's derived set. Finding B's
fail-closed rule (which AC-2 now pins as behaviour) says this must still be gated as a person write.
But no AC-4 fixture varies the `type:`-present/absent dimension — every positive control needed to
pass AC-4 as written can be built against a typed note — so an implementation that wires dispatch as
`if frontmatter.get("type") == "person": normalize_identifiers(...)` (the natural, wrong mirror of
the very bug AC-2's new clause was written to force out on the name side) satisfies AC-1 through AC-5
in full while `"Name <A@B.com>"` lands unnormalized in `emails[]` on every untyped note in the vault
— the identical N3/Finding-F corruption, on the identifier axis this item's own Finding G already
showed mirrors the name axis, entered through the type-less side door. This is the catalog's "trivial
fixture on a production-varying dimension" shape: AC-4's fixtures never vary the exact dimension
(`type:` present/absent) the dispatch code branches on, so it is satisfiable with zero
untyped-identifier-normalization implementation written — the WI-130 specimen, recurring one AC over
from where round 1 found it.

What would have to change: give AC-4 the same untyped clause AC-2 now has — an untyped, dict-shaped-
door fixture asserting identifier normalization still fires on a `type:`-less note — or an explicit,
stated scope note that the untyped case is out of scope for AC-4 specifically. The latter would need
to explain why AC-2 and AC-4 take opposite calls on the identical residue, over the identical door
set, against an Intent ("no door… through which an unvalidated name or unnormalized address can
pass") that draws no such distinction between the two.

Also re-attacked and held: AC-3's delta rule is unchanged from round 1 and still correctly
distinguishes "sets the name" from "preserves the name"; no mutually unsatisfiable pair across the
revised AC-1–AC-5; every `check:` still names a bare `test_*` function taking zero arguments.

```verdict
gate: ac-red-team
verdict: REVISE
date: 2026-08-11
model: claude-sonnet-5
targets: AC-4, AC-2, #exploration-notes
note: Revision 1 fixed findings 1/2/4 in full; finding 3 (no-type dispatch residue) was only half-folded — AC-2 pinned it for names, AC-4 has no matching clause, so untyped-note identifier normalization is satisfiable with zero implementation.
```

### Re-verify — Revision 2 fold, round 3 (same day, fresh spawn)

Re-spawned cold against the doc as it now stands, after `ideation-partner`'s Revision 2 fold (the
note prefacing `## Acceptance Criteria` claims it closes round 2's surviving half of Finding 3). Read
fresh in the prescribed order — `## Intent`, `### Examples of done`, `## Problem / Motivation` plus
Exploration Notes, `## Acceptance Criteria` last — attacking the REVISED set rather than trusting the
fold's own account, and reading the actual code the ACs would be checked against (`writer.py`,
`models.py`, `repositories/base.py`, `repositories/person.py`) where satisfiability turned on it.

**Round 2's Finding 3 — FIXED for the risk that made it CRITICAL.** AC-4 now carries: "That WHOLE
property is asserted twice, once for each value of the `type:` dimension… once against a `type:
person` note, and once against a note with `type:` ABSENT living under the `@*.md` convention…
Untypedness never exempts an identifier write, exactly as it never exempts a name write (AC-2)." The
concrete N3-shape scenario round 2 raised — `update_fields(person, {"emails": ["Name <A@B.com>"]})`
(D4, a dict-shaped door) on a `type:`-less legacy note landing unnormalized — is now a required
fixture bound to AC-1's derived set, the same way AC-2's untyped clause is. `### Examples of done`
grew the matching worked scenario (the reuse-branch write-back "changes nothing" on a `type:`-less
canonical). Round 2's finding is closed for the doors where the residue is real.

**New finding — MATERIAL — AC-4's untyped repeat is bound to AC-1's WHOLE derived set (minus only
`roundtrip_file`), which forces the untyped pass onto the three entity-shaped doors where the
scenario it is meant to test cannot occur, and the AC's own exclusion-set pin forbids carving them
out.** AC-2's untyped clause is deliberately scoped to "every **dict-shaped** door in that set" — it
does not claim the untyped repeat for D1–D3, because those doors take a typed `Person`, not a
frontmatter dict, so there is nothing to dispatch on. AC-4 drops that qualifier: its untyped clause
says "same doors" (i.e., AC-1's full derived set), and its exclusion-set sentence pins the excluded
set to be *exactly* `{roundtrip_file}` "in both the typed and the untyped pass" — which reads D1–D3
back into the untyped pass by name.

That is not satisfiable the way the clause's own `why:` describes it. `writer.write_markdown_file`
builds frontmatter from an entity via `model_to_frontmatter` (`writer.py:159`, `writer.py:256-257`
`fm = model_to_frontmatter(entity, extra_fields)`), which iterates `model_class.model_fields.keys()`
(`writer.py:111`) and always emits every declared field — `Person.type: Literal["person"] = "person"`
(`models.py:78`) is a declared field with a default, so it is unconditionally present. `save()` on
`BaseRepository` (`base.py:356`) and `PersonRepository` (`person.py:1255`) both take `entity: T` /
`entity` — a typed model, never a dict — and route to the same `write_markdown_file(entity=…)` path.
There is no way to make an entity-shaped write (D1–D3) produce, or act on, a "frontmatter dict with
`type:` absent": the caller never hands the door a dict at all, and the door's own serialization
always stamps `type: person`. Concretely, an implementation trying to honor "same doors… in both the
typed and the untyped pass" for D1 has nothing to construct the untyped fixture from — the entity is
always typed by the model, so any "untyped" variant a builder invents for D1–D3 either (a) tests
something that trivially passes regardless of whether the real dispatch fix exists (once AC-1 routes
the door through the gate at all, the gate fires unconditionally for an entity-shaped call — there is
no type-keyed branch to get wrong, so the fixture adds no discriminating power over the residue Finding
B names), or (b) silently narrows the untyped pass to the dict-shaped doors — the same scope AC-2
already states — which directly contradicts AC-4's own "the exclusion set IS `{roundtrip_file}`… rather
than tolerating any door the implementation happens to skip" sentence, since that sentence commits to
D1–D3 being IN the untyped pass. The AC cannot be satisfied both as literally stated and as
meaningfully testable at once, and neither `### Examples of done`'s new untyped scenario (which
exercises only the reuse branch through `update_fields`, a dict-shaped door) nor Finding B's own
prose (which frames the residue strictly as a "`type`-keyed dispatch" ambiguity — a concept that only
applies where the door receives a dict rather than a typed model) motivates extending it to D1–D3.

What would have to change: give AC-4's untyped clause the same "every dict-shaped door in that set"
qualifier AC-2 already has, and correct the exclusion-set sentence to state the untyped pass's
exclusion set separately from the typed pass's (typed pass: `{roundtrip_file}`; untyped pass:
`{roundtrip_file}` plus the entity-shaped doors — or name them, `write_markdown_file(entity=…)` /
`BaseRepository.save` / `PersonRepository.save`) — rather than asserting one exclusion set holds "in
both" passes.

Also re-attacked and held: the typed pass's binding to AC-1's full derived set (minus only
`roundtrip_file`) is correct and is exactly what closed round 1's Finding 2 — `write_markdown_file`
and `lint_vault --fix` are rightly back in scope there, since both take dicts or build one internally
without the type-dispatch ambiguity D1–D3's typed-object shape removes. AC-2's Tier-1 sweep, AC-3's
delta rule, and AC-5's job-shape sweep are unchanged from round 2 and still hold; no mutually
unsatisfiable pair found across the revised AC-1–AC-5 beyond the internal AC-4 tension above; every
`check:` still names a bare `test_*` function.

```verdict
gate: ac-red-team
verdict: REVISE
date: 2026-08-11
model: claude-sonnet-5
targets: AC-4
note: Revision 2 fully closed round 2's Finding 3 (dict-shaped-door untyped identifier coverage); it introduced a new, narrower defect — AC-4's untyped repeat is bound to AC-1's whole derived set minus only roundtrip_file, which pins entity-shaped doors D1-D3 into an untyped pass they cannot meaningfully undergo (model_to_frontmatter always stamps type:person), unlike AC-2's correctly dict-shaped-scoped clause.
```

### Re-verify — Revision 3 fold, round 4 (same day, fresh spawn)

Re-spawned cold against the doc as it now stands, after `ideation-partner`'s Revision 3 fold (the note
prefacing `## Acceptance Criteria` claims it corrects round 3's over-reach). Read fresh in the
prescribed order — `## Intent`, `### Examples of done`, `## Problem / Motivation` plus Exploration
Notes, `## Acceptance Criteria` last — attacking the REVISED set rather than trusting the fold's own
account, and re-reading the actual code (`writer.py`, `repositories/base.py`, `repositories/person.py`,
`identifier.py`) where satisfiability turned on it.

**Round 3's finding — FIXED.** AC-4 now states two separately-named exclusion sets instead of one
asserted "in both" passes: typed pass `{roundtrip_file}` over AC-1's full derived set (7 of 8 doors,
unchanged from round 1); untyped pass `{BaseRepository.save, PersonRepository.save, roundtrip_file}`
over "every DICT-SHAPED door in that set" (5 of 8 doors), with the same five doors named explicitly
(`write_markdown_file`'s `frontmatter=` arm, `update_fields`, `update_frontmatter_field`,
`update_frontmatter_fields`, `lint_vault --fix`). The counts reconcile (8 − 3 = 5) and the scoping now
matches AC-2's "every dict-shaped door in that set" clause verbatim rather than contradicting it. Round
3's unsatisfiable-as-stated tension (D1–D3 pinned into an untyped pass they cannot construct) is gone.

**New finding — CRITICAL — neither AC-2's nor AC-4's TYPED-pass clause pins which of
`write_markdown_file`'s two arms the fixture must exercise, so the fixture set can satisfy "every door
in AC-1's derived set" while never directly exercising the `entity=` arm — the exact call shape AC-4's
own `why:` names as "the live example."** Finding B states `write_markdown_file` "sits in BOTH classes"
— entity-shaped via its `entity=` arm, dict-shaped via its `frontmatter=` arm (`writer.py:159-163`,
confirmed: `entity: Optional[BaseEntity] = None, frontmatter: Optional[dict[str, Any]] = None`, and at
:256-263 the two branches build `fm` differently before both fall through to the same
`write_frontmatter(fm)` call at :266) — and says it "belongs to the untyped pass through its
`frontmatter=` arm **only**." That pins the untyped/dict-shaped side correctly (confirmed FIXED above).
But for the TYPED pass, AC-4's `desc` distinguishes passes solely by the `type:` dimension ("one for
each value of the `type:` dimension the dispatch code branches on") — never by input SHAPE — so a
fixture satisfying "typed pass, door = write_markdown_file" only needs a `type: person` value to be
present; nothing requires that value to arrive via the `entity=` arm rather than via `frontmatter={"type":
"person", ...}`. The two other doors requiring an entity object (`BaseRepository.save`,
`PersonRepository.save`, `base.py:356`/`person.py:1255`) already force entity-shaped fixtures by their
own signatures, so a builder assembling one uniform dict-shaped harness across all 8 doors (cheapest to
write, since 6 of 8 doors — `update_fields`, both `update_frontmatter_field(s)`, `lint_vault --fix`, and
`write_markdown_file`'s `frontmatter=` arm, plus the two `save` methods separately as entity fixtures) can
satisfy AC-4's typed pass for `write_markdown_file` using ONLY `frontmatter={"type": "person", "emails":
[...]}`, reusing the exact same fixture shape the untyped pass already requires (minus the `type:` key).
`write_markdown_file(entity=Person(emails=["Name <A@B.com>"]))` — AC-4's own cited scenario, and the
identical shape as Finding F's `repo.save(Person(name="Dave/Bob"))` on the identifier axis instead of the
name axis — is never a REQUIRED fixture anywhere in the set, on either AC.

This is not rescued by AC-1's routing wall. AC-1(a)/(b) prove `write_markdown_file` is DISCOVERED as a
door and CALLS the gate somewhere in its body (a presence check, the same shape as WI-004's own
`_is_write_call`, cited as the precedent); it does not prove the gate call is reachable from BOTH
branches. `write_markdown_file` builds `fm` via two independent branches (:256-257 `entity is not None`
vs. :258-261 `frontmatter is not None`) before they converge at `write_frontmatter(fm)` (:266) — the
natural place to insert one gate call that both branches reach. But a builder who instead validates
right after each branch (plausible: the `entity` branch has a typed `Person` available and the
`frontmatter` branch has a raw dict, so a name/identifier gate keyed on model attributes might read
naturally as belonging inside the `entity is not None:` branch specifically) can wire the gate correctly
for the branch every dict-shaped-door-uniform fixture exercises (frontmatter=) while leaving the
`entity=` branch's call to the gate absent, wrong, or divergent — and AC-1's structural wall still shows
"write_markdown_file calls the gate somewhere," AC-2's Tier-1 typed-pass fixture (built the same
dict-shaped way, per the same economy argument) never catches it, and AC-4's typed-pass fixture never
catches it either. The concrete failure: `write_markdown_file(entity=Person(name="Dave/Bad", emails=["Name
<A@B.com>"]))` called directly (a documented public entry point, README.md:196, per Finding B) writes an
unrefused Tier-1-dirty name and an unnormalized email, while every AC-1–AC-5 fixture as currently scoped
passes.

This is the same shape as AC-2/AC-4's round-2/round-3 `type:` residue, one dimension over: there the
unvaried dimension was `type:` present/absent; here it is call-shape (`entity=` vs `frontmatter=`) on the
one door that has both, and it is unvaried on the TYPED side of both ACs even though it is exactly the
dimension Finding B's own two-arm split exists to name. It is the catalog's "trivial fixture on a
production-varying dimension" (WI-173's AC-6 shape): real-shaped on the record content, trivial on the
one dimension — which call arm supplies it — the exercised code actually branches on.

What would have to change: AC-2's and AC-4's typed-pass clauses each need an explicit `write_markdown_file`
sub-clause requiring a fixture through the `entity=` arm specifically (not merely "a `type: person` note"
satisfiable via the dict arm), the same way the untyped clause already pins `write_markdown_file`'s
`frontmatter=` arm by name. `### Examples of done` should gain the direct-call variant too — its two
`write_markdown_file` mentions so far are all `repo.save(...)`/`update_fields(...)`, never a bare
`write_markdown_file(entity=...)` call bypassing both repositories.

Also re-attacked and held: AC-2's Tier-1 sweep, AC-3's delta rule, and AC-5's job-shape sweep are
unchanged from round 3 and still hold; the untyped-pass scoping on both AC-2 and AC-4 is now internally
consistent (see above); no mutually unsatisfiable pair found across the revised AC-1–AC-5 beyond the
arm-coverage gap above; every `check:` still names a bare `test_*` function taking zero arguments.

```verdict
gate: ac-red-team
verdict: REVISE
date: 2026-08-11
model: claude-sonnet-5
targets: AC-2, AC-4, #exploration-notes
note: Revision 3 correctly fixed round 3 (AC-4's typed/untyped exclusion sets now split and match AC-2's dict-shaped scoping); new finding — neither AC-2's nor AC-4's typed-pass clause pins write_markdown_file's entity= arm, so a dict-shaped-uniform fixture set can satisfy both ACs while AC-4's own cited "live example" (write_markdown_file(entity=...) bypassing normalization) stays unexercised.
```

### Re-verify — Revision 4 fold, round 5 (same day, fresh spawn)

Re-spawned cold against the doc as it now stands, after `ideation-partner`'s Revision 4 fold (the note
prefacing `## Acceptance Criteria` claims it closes round 4's entity=-arm coverage gap structurally
rather than by sub-clause). Read fresh in the prescribed order — `## Intent`, `### Examples of done`,
`## Problem / Motivation` plus Exploration Notes, `## Acceptance Criteria` last — attacking the
REVISED set rather than trusting the fold's own account, and re-reading the actual code
(`writer.py`, `repositories/base.py`) to confirm the arm citations the fold's argument turns on are
still accurate against the tree (`write_markdown_file`'s three branches at writer.py:256-257 /
:258-261 / :262-263, `_owns` at base.py:257, `save` at base.py:356, `update_fields` at base.py:403
all confirmed unchanged).

**Round 4's finding — FIXED, structurally rather than patched.** AC-1's derivation unit is now the
write ARM rather than the function — "one member per distinct binding of the dict a function
serializes" — so `write_markdown_file`'s three branches (`entity=`, `frontmatter=`, the
`extra_fields`-only `else`) are three DISTINCT, separately-required members of a ten-arm floor
instead of one door satisfiable by any one of the three. AC-2's and AC-4's typed-pass clauses each
now name the `entity=` arm and the `extra_fields`-only arm as required "by construction," explicitly
stating that "a `type: person` value arriving through the `frontmatter=` arm never stands in for the
`entity=` one" — closing exactly the escape round 4 demonstrated (a uniform dict-shaped fixture
harness satisfying both ACs while the direct `write_markdown_file(entity=…)` call, the concrete
scenario named in AC-4's own rationale, stayed unexercised). This is not a one-off sub-clause patch:
because AC-2 and AC-4 both delegate their coverage to AC-1's derived set, and that set is now defined
at arm granularity, a future arm added to any function is a required fixture on both ACs by
construction, the same generality argument the fold's own commentary makes.

**Nothing new found.** Re-attacked with the One Question against the full revised set:

- **AC-1** — floor (10 arms, `AT LEAST`), driven positive controls (b: one scratch function per arm
  shape including a multi-branch one), and a near-miss (c: mutate-but-don't-serialize) together
  still close the WI-130 vacuous-sweep shape; the arm-vs-function unit is now explicit and the
  reach-proof survives the restructuring.
- **AC-2** — Tier-1 sweep still class-closing (swept from `NameValidator`'s own pattern table); typed
  pass now forces `entity=` and `extra_fields`-only fixtures by name, not just membership; untyped
  pass's dict-shaped/entity-shaped split is unchanged from round 3 and still internally consistent
  (6 dict-shaped arms + 4 excluded = 10, reconciles against AC-1's floor).
- **AC-3** — delta rule unaffected by the AC-1 restructuring; still correctly distinguishes "sets the
  name" from "preserves the name."
- **AC-4** — mirrors AC-2's fix exactly; typed pass now names `entity=Person(emails=[…])` — its own
  cited "live example" — as a required fixture rather than an example sentence with no forcing
  clause; untyped pass's exclusion set (`{entity= arm, BaseRepository.save, PersonRepository.save,
  roundtrip_file}`) is unchanged from round 3 and still reconciles (6 + 4 = 10).
- **AC-5** — job-shape sweep unaffected by the AC-1 restructuring; unchanged since round 2, still
  holds.
- Checked for a new mutually-unsatisfiable pair introduced by the arm-granularity restructuring
  (the round-3 failure mode, recurring one AC over) — none found: AC-2 and AC-4's typed/untyped
  exclusion sets both reconcile against AC-1's 10-arm floor with no arm double-counted or
  unaccounted-for.
- Every `check:` still names a bare `test_*` function taking zero arguments (Check 10 / WI-248
  clean).
- Regress-signature check: four REVISE rounds on one day is a real signal to weigh, but each round's
  finding was a DIFFERENT defect (vacuous sweep → hardcoded door list → dispatch residue →
  arm-coverage gap), not the same target re-raised, and round 4's fix was structural (a derivation-unit
  change) rather than another sub-clause patched onto the surface the prior fix created — this reads
  as convergence, not the machinery-chasing treadmill the role instructions warn against naming.

No CRITICAL, MATERIAL, or MINOR finding survives this round.

```verdict
gate: ac-red-team
verdict: PROMOTE
date: 2026-08-11
model: claude-sonnet-5
note: Revision 4 closed round 4's entity=-arm coverage gap structurally (AC-1 now derives at arm granularity; AC-2/AC-4 typed passes name the entity= and extra_fields-only arms as required fixtures by construction) — re-attacked the full AC-1–AC-5 set fresh, verified the arm citations against the live code, and found nothing material.
```

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

## Architectural Review — 2026-08-11

**Recommendation: REVISE — return to exploration**

Cold-start, read in role order: `architect.yaml`, this document in full, then the code every
citation in it names (`writer.py`, `repositories/base.py`, `repositories/company.py`,
`repositories/person.py`, `identifier.py`, `name_validation.py`, `errors.py`, `tests/derivations.py`,
`tests/test_write_routing.py`, `scripts/lint_vault.py`), plus `LESSONS.html`. Every line citation in
Findings A–G that I checked re-derives correctly against the tree as it stands — the arm split at
writer.py:256-263, the convergence at :266, `_owns` at base.py:257-264, the filename derivation at
base.py:381, `update_fields`' pre-merge delta at base.py:437-451, `_writeback_identifier`'s raw
membership tests at person.py:1205/:1208, `_extract_email_and_name`'s parens regex at person.py:1295
and its laxer `"@" in … and "." in …` test at :1292, `Email.parse`'s deliberate angle-bracket gate at
identifier.py:141-149, and the fixture-battery precedent at tests/test_write_routing.py:1-18. The
exploration is unusually good and the chosen approach (F) is the right one. One premise it settled
rather than deferred is wrong on a fact I can check, and because it was settled it is pinned by
equality into two signed acceptance criteria.

### Trigger check

Three fire: a new module (the gate); a contract change crossing into three downstream repositories
(`docs/backlog-campaign-2026-07-05.md`, consumer-facing type decisions); a derived-wall enforcement
mechanism that must be designed rather than copied. Effort is stated at one to two sessions.

### Blocking issue

**The untyped-dispatch rule annexes an entity class this item declares out of scope, because `@*.md`
is not a person convention — it is the convention Person and Company SHARE.**

Finding B's resolution reads: "`@*.md` (base.py:197, which PersonRepository does not override) is
such a convention, so an untyped note under it IS claimed as a person note." The premise is that
`_owns`'s glob fallback yields a *person* answer. It does not — it yields a *per-repository* answer,
and two repositories answer yes:

- `CompanyRepository` (company.py:46) declares `entity_type`, `type_name`, `_index_entity`,
  `_clear_indexes`, `get_by_domain`, `resolve`, `get_by_industry`, `create_stub` — and **no
  `file_pattern` override and no `save` override**. It therefore inherits `@*.md` (base.py:197)
  exactly as `PersonRepository` does, and inherits `filename = f"@{name}.md"` (base.py:381), so
  `CompanyRepository.save(Company(name="Acme"))` writes `<vault>/@Acme.md` into the same directory
  the person glob walks.
- `_owns(None)` is therefore `True` for **both** repositories on the same untyped `@Foo.md`
  (base.py:264). That is harmless where `_owns` is actually consumed — `_note_skip` (base.py:266-274),
  where over-claiming costs one duplicate WARNING on the skip surface. It is not harmless as a GATE
  dispatch rule, where over-claiming costs a refused write judged under the wrong entity's contract.
  The predicate's fail-closed direction was calibrated for a consequence this design does not have.

The item states plainly that the two contracts differ: parked defect 3 — "This item stays
**Person-only**; company names have a different contract (a company suffix is legitimate there and is
Tier 3 here)" — with WI-022 already open to give Company its own validator. Yet AC-2's untyped clause
requires that at every dict-shaped arm "a dict with `type:` absent, under the `@*.md` convention, is
gated exactly as a `type: person` one is", with the exclusion set "asserted to BE exactly" a named
four. There is no arm left through which an untyped company note can be written, and no room for the
build to decline.

Concrete failure: `NameValidator._RFC2822_LEAK_RE` (name_validation.py:54) matches any lowercase run
of ≥5 characters ending in a TLD. `booking.com` matches it (`b` + `ooking.` + `com` + word boundary).
So `write_markdown_file(vault/"@booking.com.md", extra_fields={"name": "booking.com", "website":
"https://booking.com"})` — the D1c arm, dict-shaped, untyped, under `@*.md`, introducing a name — is
refused as `rfc2822_leak` under AC-2 as signed. The same rule hands every untyped company note in the
vault to a validator whose Tier-1 table was empirically derived from 1647 **person** names
(name_validation.py:26-28). AC-4's half is milder (normalizing `emails[]` on a company note is mostly
inert) but rests on the identical wrong premise.

Why no prior gate caught it: five ac-red-team rounds each attacked *gameability* — can a builder green
this while doing less than the real work. Every round's finding was of that shape, and the fold that
answered round 1's Finding 3 chose "person" as the fail-closed answer and cited `_owns` for it. No
round asked whether "person" was the right answer, because the premise was ambient in the document by
then. That is LESSONS #21 exactly — a review gate validates within the premise. It is also why this
cannot be folded at spec time: the exploration explicitly removed the choice from me ("the no-`type:`
BEHAVIOUR is no longer an open question … the architect is choosing a mechanism that satisfies it, not
choosing whether to honour it"), and both ACs pin it by equality. The spec-writer would have to
redesign the dispatch rule, which is the calibration failure this gate exists to prevent.

What has to change — in the exploration first, then in AC-2's and AC-4's untyped clauses, then
re-signed: Finding B must state what `@*.md` actually encodes (person-or-company, by this codebase's
own construction) and pick a rule that survives it. The fail-closed instinct is right and should be
kept; the annexation is what must go. The shape that does both, offered as direction rather than
design: on an untyped dict-shaped write, apply the checks that are **entity-agnostic** — `/` is
path-hostile for a note of any type (name_validation.py:95; it is the Finding F defect and does not
care whose note it is) — and withhold the person-specific Tier-1 patterns until the write declares a
type. Alternatives worth weighing during re-exploration: require dict-shaped doors to carry an
explicit entity type and refuse an undeclared one outright (strictest, largest consumer blast
radius); or resolve ownership through the repository that already owns the note rather than through
a glob two repositories share. Whichever is chosen, the two halves must still be pinned together —
revision 2's reasoning for that (dispatch fires once per write, upstream of the name/address split)
is correct and survives this finding intact.

### Rulings on the two open questions the exploration hands the architect

Both are settled here so the fold has them; neither is blocking.

**Gate signature — no `existing` parameter, one entry point.** `(existing, incoming)` is the wrong
shape: Finding C's delta rule says the stored record is precisely what must not be judged, and a
parameter carrying it exists only to be misused. The gate takes the introduced fields plus the entity
type. One function rather than two entry points: the entity-shaped arms project the model to a field
dict first, and `model_to_frontmatter` (writer.py:88) already is that projection, so the entity/dict
distinction dissolves before the gate rather than inside it. This also keeps the gate ignorant of
`BaseEntity`, which keeps the new module a leaf next to `errors.py` (errors.py:1-8) rather than a
second place that imports models.

**Splitter vs `Email.parse` — the splitter is TOTAL and owns the parens form; `Email.parse` is not
widened.** Two of the three call sites pass inputs that are usually not addresses at all
(`create_stub` at person.py:1386 splits a *name*; `_normalize_address_fields` has an explicit
keep-as-is branch at person.py:1313), so a splitter that raises turns the common case into an
exception. It returns `(address | None, display)`, delegating to `Email.parse` inside a try and
mapping `IdentifierError` to "not an address" — which is how `create_stub` inherits the strict
refusal without inheriting a raise. The parens form (person.py:1295) is handled in the splitter
*before* delegation, not by loosening `Email.parse`: that function's angle-bracket gate is a
deliberate identity-key protection with its reason written at identifier.py:141-144, and the parens
form is a display-wrapper concern with no identity consequence. Finding D's reconciliation 2 (the
laxity delta on live data) stays owed to the spec as a behaviour change, not a refactor.

### Review

**Fit:** Strong. Approach F is the same shape WI-004 landed — a narrow authority plus a derived AST
wall proving the routing is total — and it reuses rather than re-invents: `tests/derivations.py` is
already the only file permitted to name `ast` (derivations.py:14-17), and
`tests/test_write_routing.py:1-18` already ships the exact match-shape battery AC-1(b)/(c) demand,
with the vacuity argument written out. Finding A's rejection of the mint's named mechanism is
correct and is the WI-185 read protocol working: `vault_io`'s doors take `(path, text)`, so a check
there would reconstruct the structure the caller discarded one frame earlier. Finding B's location
of the seam is right and its arm-granularity refinement is the strongest thing in the document.

**Duplication:** Finding D's correction of the mint (three jobs, not four copies) reads correctly
against the tree, and its self-declared limit — the table came from a `parseaddr` grep and is a lower
bound — is the honest statement AC-5's job-shape sweep is built on. `_extract_email_and_name`
reaching for a parens regex (person.py:1295) before it reaches parseaddr is a genuine existence proof
that the job is written here without the symbol.

**Boundaries:** This is where the blocking issue lives — `_owns` is borrowed across a boundary where
its calibration does not carry. Two smaller boundary notes below. The constraint that the gate must
not live inside `vault_io` is right: that module's exemption from the routing wall is paid for by it
owning exactly one thing.

**Determinism boundary (LLM vs code):** n/a — no capability in this design is handed to an LLM. The
whole item is the opposite move: taking a contract currently enforced by producer discipline and
making it structural.

**Reversibility:** Good. The gate is one module and ten call sites; the wall is one test file. Backing
out is deleting a module and un-routing. Approach E's rejection of an observe/enforce knob is right
for the reason given — the delta rule already bounds the blast radius to writes that introduce a
violation, and WI-004's D6 already ruled one reader per setting.

**Generalization:** Correctly scoped. Person-only, with Company parked to WI-022 — except that the
blocking issue silently breaks that scoping. Fix the dispatch rule and the scoping holds.

**Cost & maintenance:** One to two sessions is plausible. The maintenance cost is the wall, and the
wall is the point — it is what makes the eleventh arm red rather than silently open.

**Build vs extend vs integrate:** Extend, correctly. `NameValidator`, `Email.parse` and
`normalize_phone` all exist and are tested; this is routing, plus one new splitter and one new gate.

**Prior art (outside view):** The design builds a derived AST wall around a real constraint — Python
cannot make a semantic check unavoidable the way WI-004's capability wall could. Finding A already
states why the capability instrument does not transfer, and the standard answers are considered and
correctly rejected on cited grounds: parse-don't-validate at the type level (Approach C) fires on
READ, which drops dirty notes into the skip surface and re-opens the dup-proliferation class
base.py:27-38 exists to fight; a validating serializer (Approach B) sees the merged record and never
the delta. The remaining standard answer the world reaches for is *shrink the surface rather than
police it* — see the second note below. Not blocking, and no cited execution is owed here: the wall
instrument is not novel machinery, it is this repository's own established precedent
(tests/test_write_routing.py), which is the outside view already satisfied.

### Notes (non-blocking) — for the fold and for the spec

1. **`declared_type` already has a consumer that decodes it as an entity type.** Finding E routes the
   stable NameValidator pattern key (`"path_hostile_char"`, …) through `LoudFailError`'s
   `declared_type` slot. `bounded_message` does render it verbatim (errors.py:150), and the
   `vault_io._bad_setting` precedent is real — but `base._note_skip` reads
   `getattr(error, "declared_type", None)` and feeds it straight to `_owns` (base.py:267-269), where
   a pattern key would evaluate as "not our type". Not reachable today (the gate is on the write path;
   `_note_skip` fires from `_load_file`'s read path), but it gives one field two meanings inside one
   hierarchy, which is how the next reader gets it wrong. A dedicated `pattern` attribute on the new
   error class costs nothing and keeps `declared_type` meaning one thing. Also owed: the refusal
   needs a new literal in `REASONS` (errors.py:110), which the module's own contract permits
   ("extended only by editing this set alongside that table") — the spec should say so explicitly so
   the build does not discover the closed enumeration at implementation time.

2. **Ten arms is itself a finding, and AC-1's floor now pins it.** `update_frontmatter_field`
   (writer.py:292), `update_frontmatter_fields` (:350) and `roundtrip_file` (:402) are one function
   under three parameterizations — identical read-parse-mutate-serialize-write bodies differing only
   at :332 / :384 / (nothing). Collapsing them to one door with two thin delegating wrappers would
   drop the arm count and the routing surface *before* this item routes it, which is the
   pay-down-principal move (LESSONS #13) against a design that otherwise deletes only two parseaddr
   sites and adds a module, a wall and ten call sites. It cannot happen inside this item now — AC-1's
   floor asserts the ten arms exist, so removing one turns the wall red — which is a real and
   acceptable cost of a signed AC set, but it should be recorded as a follow-on work item alongside
   the two already parked, sequenced *after* this one.

3. **`lint_vault --fix` (D8) is the one arm where the delta has no natural expression.** The fix loop
   mutates `fm` in place across eight `elif` branches and serializes the whole dict at
   lint_vault.py:876-882; there is no delta object to hand the gate. Supplying one means threading a
   per-key record through every branch, in `scripts/`, outside the package. Worth pricing at spec
   time — it is the single largest piece of unglamorous work in the routing. Related, and benign: the
   `person_missing_name` branch (:835-837) genuinely introduces a name, derived from
   `fpath.stem.lstrip("@")`, so on a note whose stem is itself Tier-1 dirty the repair is now refused
   — correct behaviour under the delta rule (it *sets* the name, so AC-3 is satisfied), and it
   degrades quietly because the broad `except Exception` at :902 prints and continues. That branch is
   type-gated on `vf.entity_type == "person"` (lint_vault.py:374) and `entity_type` is derived from
   `fm.get("type")` (:140), so it does not fire on untyped notes — worth knowing when the untyped rule
   is re-derived.

4. **Sibling `save` overrides that bypass `BaseRepository.save`.** `MeetingRepository.save`
   (meeting.py:192) and `BookRepository.save` (book.py:170) call `write_markdown_file(entity=…)`
   directly rather than through `super().save()`. They are correctly *not* arms under AC-1's
   definition — they bind no dict they serialize, and they inherit gating at D1a — but the door
   table's "D2 → D1" framing understates how many repository saves exist. Arm derivation handles them
   by construction; noting it so the build does not read the table as a census of callers.

5. **Held on re-attack, and worth saying so:** Finding C's delta rule is correct and is the load-
   bearing insight — whole-record validation at the seam really would refuse the repair tools, and
   the delta really is available one frame up at every arm except D8 (base.py:437 pre-merge,
   writer.py:329/:381). Finding G's phone scope-in is right and its constraint (dedupe on the
   normalized form, store the display form) is forced by `Phone.parse` normalizing to bare digits
   (identifier.py:237-240). Class 2's pass-throughs really cannot introduce a name or an address.
   AC-1's floor, driven positive controls and near-miss are the right battery and match the
   established precedent. None of this needs re-deriving in the fold.

```verdict
gate: architect
verdict: REVISE
date: 2026-08-11
model: claude-opus-5
targets: AC-2, AC-4, #exploration-notes
note: Finding B's untyped-dispatch rule reads `@*.md` as a person convention, but CompanyRepository overrides neither file_pattern (base.py:197) nor save (base.py:381), so companies share the glob and the filename — `_owns` answers yes for both repositories, and AC-2/AC-4's untyped clauses (pinned by equality) therefore subject every untyped company note to a person-only Tier-1 table this item explicitly scopes out to WI-022.
```

## Data Audit — 2026-08-11

**Recommendation: REVISE — return to exploration**

Cold-start, read in role order: `data-premise.yaml`, this document in full (including all five
ac-red-team rounds, the AC sign-off fence, and the architect's REVISE), then the code every premise
turns on. Audit method note, stated up front because it bounds what follows: this cage has **no
shell**, so every predicate below was resolved by direct source read and grep over the tree, and the
scope bound is this tree's files only — **the live vault was not read and no query was run against
it.** That limitation is not incidental to the verdict; it is half of it. The corpus predicate this
item's central rule depends on has never been run by anyone, in any of the seven gate rounds this
document records, and this gate could not run it either.

### Trigger check

**Class 1 AND Class 2 — both fire, on the same rule.**

- Class 1 (data-distribution / field-presence): the pinned untyped-dispatch rule is an existence
  claim about live data — that `@*.md` notes with no `type:` key exist, and that they are person
  notes. AC-3's necessity is a second Class-1 claim: that Tier-1-dirty stored names still exist in
  the vault today.
- Class 2 (rule-effect-against-existing-corpus): AC-2's untyped clause introduces a new refusal rule
  whose correctness depends on what it flags when run against the corpus **as it exists today**.
  This is the live `--enforce` shape verbatim — a rule reasoned about at length for hypothesised
  future writes and never once executed against what is already on disk.

### Premise vs reality

**Premise 1 (the load-bearing one) — "an untyped note under `@*.md` IS a person note."**
Finding B settles the no-`type:` residue by adopting `_owns`'s glob fallback, and AC-2 and AC-4 pin
that answer *by equality* into a signed AC set. Grounded against source, the premise is false in the
direction the architect names, and I confirm every leg of it independently:

| Claim | Read from the tree | Result |
|---|---|---|
| `@*.md` is the default glob | `base.py:195-197` | confirmed |
| `_owns(None)` returns True whenever the glob is not a catch-all | `base.py:260-264` — `Path("@*.md").stem` is `"@*"`, `!= "*"` → **True** | confirmed |
| `CompanyRepository` inherits it | `company.py:46`; grep for `def file_pattern` in `company.py` → **no match** (only `book.py:51` and `meeting.py:52` override) | confirmed |
| `CompanyRepository` inherits `@{name}.md` | grep for `def save` in `company.py` → **no match**; `base.py:381` supplies the filename | confirmed |
| `_RFC2822_LEAK_RE` matches `booking.com` | `name_validation.py:54-56` — `\b[a-z][a-z0-9._\-]{4,}(com|…)\b`; `b` + `ooking.` (7 ≥ 4) + `com` + `\b` | confirmed, matches |

So `_owns(None)` is True for **both** repositories on the same untyped `@Foo.md`, and the Tier-1
table it would hand that note to is, by its own module docstring (`name_validation.py:26-28`),
derived from an audit of **person** names. The architect's blocking issue is correct on the facts.

**What the architect's finding leaves open, and what makes it a DATA finding rather than only a
design one: the population is uncounted.** The architect ordered a rule change and offered three
candidate rules — entity-agnostic checks only; require an explicit declared type; resolve ownership
through the owning repository. Which of those is right is not decidable from source, because all
three differ only in how they treat a population nobody has measured. This document contains **zero
counts** about untyped notes. The numbers it does carry — 1647 notes, 1590 names, `0` containing
`/`, `0` containing `->`, `1` containing `→` — every one of them traces to
`name_validation.py:26-107` and `tests/test_name_validation.py:8-262`, i.e. the audits of
**2026-06-02 / 06-06 / 06-09**, all person-scoped, none re-run in the two months since. Grep across
`tests/` for any untyped-frontmatter fixture returns **no files**: the case AC-2 and AC-4 now pin as
required behaviour has no existing exemplar anywhere in the repository, real or synthetic.

**Premise 2 — "legacy-dirty stored names exist, so whole-record validation would brick the vault."**
This is Finding C, the insight the entire delta rule and Approach F rest on, and it is the item's
most consequential empirical claim. Its evidence is the 2026-06-02 audit (two months stale) plus the
observation that WI-111 and WI-117 each removed corrupt names *by hand* as late as June — which cuts
both ways, since hand-removal is exactly the process that shrinks the population being cited. The
delta rule is very likely still right (the design argument holds even at a low count, and AC-3 is
fixture-based so it stays testable regardless). But nobody has re-run the predicate, and this is
precisely the class the build-start re-grounding step exists to catch — better to date it now than
to have the builder discover it.

**Premise 3 — the ten-arm door set (Class 2, code-corpus).** Spot-checked and **holds**:
`writer.py:255-263` shows exactly three fm-building branches converging on one
`write_frontmatter(fm)` at `:266`, matching Finding B's arm table. This premise is grounded and is
not part of the revision.

**Premise 4 — Finding D's four-site table is a lower bound.** Self-declared in the document and
correctly answered by AC-5's job-shape sweep. Grounded; not part of the revision.

### Required grounding

Before this can be re-signed and specced, run these against the live vault and paste the numbers in
— they are cheap, and the first two determine which of the architect's three candidate rules is
correct rather than merely defensible:

1. **Count the untyped population and its entity mix.** Over `<vault>/@*.md`: how many notes lack a
   `type:` key; of those, how many are companies, how many are persons, how many are neither. If the
   population is empty, the fail-closed rule is a design choice with no live consequence and the
   cheapest safe rule wins. If it is largely companies, the architect's annexation finding is a live
   corruption path and the rule must discriminate.
2. **Run AC-2's untyped rule against the corpus as it stands (the Class-2 predicate).** For every
   untyped `@*.md` note, evaluate the Tier-1 table against its stored `name:` and report what it
   flags. This is the one predicate that tells you whether "gated exactly as a `type: person` one is"
   refuses real notes today — and specifically how many company-shaped names (`booking.com` and its
   siblings) `_RFC2822_LEAK_RE` catches. Reasoning about the rule is what five red-team rounds
   already did; running it is what has not happened.
3. **Re-ground Finding C's premise.** Re-run the Tier-1 table over all stored names and report the
   current count of legacy-dirty notes, dated 2026-08-11. If it is now zero, say so and keep the
   delta rule on its design argument rather than on a stale number.
4. **Carry the counts into the fold.** Whichever rule Finding B is rewritten to, state it with the
   number it was chosen against, so build-start re-grounding has something to detect rot in.

### Conclusion

The item's *code*-premises are in excellent shape — every structural citation I checked re-derives.
Its central *data* premise is not: the untyped-dispatch rule is an unmeasured claim about a
population, it was settled rather than deferred, and it is pinned by equality into two signed
acceptance criteria — so it cannot be folded downstream. The architect independently reached REVISE
on the same rule from the boundary side; this gate reaches it from the data side and adds the part
that ruling does not supply — the fix needs a count, not just a better rule. Stage stays at
`exploring`.

```verdict
gate: data-premise
verdict: REVISE
date: 2026-08-11
model: claude-opus-5
targets: AC-2, AC-4, AC-3, #exploration-notes
note: The untyped-dispatch rule pinned by equality into AC-2/AC-4 is an ungrounded Class-1/Class-2 premise — no one has ever counted the untyped `@*.md` population or run the Tier-1 table against it, and `_owns(None)` is True for CompanyRepository too (confirmed: no file_pattern/save override in company.py); AC-3's legacy-dirt premise is a two-month-stale person-scoped number.
```

## Spec-Writer Hand-Back — 2026-08-11 (round 2, restated in place)

> **SUPERSEDED by the round-3 hand-back at the foot of this document.** Kept as the record of the two
> generator sweeps it ran, both of which round 3 carries forward. One claim in its "settled and
> carried forward" list is corrected there: `AC-3` does need an edit.

**No spec was written. The item stays at `exploring`.** This section is the push-back the
spec-writer role prescribes when the exploration is not ready, written into the doc rather than
into a chat reply, plus everything I could settle that does NOT depend on the contested premise —
so the re-exploration and re-sign round costs one loop instead of three.

Cold-start, read in role order: `spec-writer.yaml`, this document in full (all five ac-red-team
rounds, the `ac-signoff` fence, the architect's REVISE, the data audit's REVISE), the project
`CLAUDE.md`, then the code every premise below turns on. I re-derived the blocking citations myself
rather than inheriting them — the results are in "Re-verified independently" below. This cage has
**no shell** and its scope bound is this tree's files only.

**This is the SECOND spec-writer round against the same architect objection, and the answer is
unchanged: hand back.** The three locks below are not a judgement call that a fresh spawn might
decide differently — one of them (D3) is enforced by the conveyor and would refuse the transition
no matter how good the spec was. A third re-run without step 1 of the re-entry path will produce
this same section again. What round 2 ADDS, so the loop is not spent:

- **The class sweep the architect's finding actually demands** (below, "The generator behind the
  architect's finding"). Round 1's hand-back swept round 4's generator — a derived fixture space
  specified at a coarser unit than the code branches on — and found two more open members. It did
  not sweep the ARCHITECT's generator, which is a different one. Swept here: nine borrowings, four
  already closed by folds this document made without naming the class, one correctly declined,
  **four open**, of which the architect found two and the data-premise gate one.
- **One new open member, verified this round: `lint_vault` already answers the untyped question,
  and it answers it the OTHER way** — so AC-2 as signed would install, inside D8, a dispatch rule
  that contradicts the dispatch rule the enclosing repair loop uses to decide what to repair.
  Independent of the Company annexation, and it would be round 8 if it is not folded in the same
  re-exploration.
- **Re-verification rather than inheritance.** I re-read `base.py`, `company.py`,
  `name_validation.py`, `writer.py` and `scripts/lint_vault.py` at every blocking citation
  (results below), including the Tier-1 branch/key count round 1 asserted.

### Why no spec — three locks, and each one alone is sufficient

1. **The conveyor refuses the transition.** Rule D3 refuses `→ specced` without a data-premise
   PROMOTE. The standing data-premise verdict is REVISE (2026-08-11). A spec written now could not
   be promoted even if it were perfect.
2. **Both REVISE verdicts target SIGNED text, and signed text is Dave's to change.** `AC-2` and
   `AC-4` are inside the `ac-signoff` hash span (`ac_hash_AC-2: b6874ac5d7ef`,
   `ac_hash_AC-4: 175736170bcc`, `ac_hash: a76ebad54da2`). The role's WI-061 rule is explicit: refine
   a signed AC within the spirit of the original, but **if an original AC itself proves wrong, do not
   quietly change it — escalate and let Dave re-originate.** Two independent gates have now ruled
   that these two originals are wrong on a fact, not merely imprecise. That is the escalate branch,
   not the refine branch.
3. **The architect named this role specifically as the wrong place to fix it.** "It is also why this
   cannot be folded at spec time: the exploration explicitly removed the choice from me … and both
   ACs pin it by equality. The spec-writer would have to redesign the dispatch rule, which is the
   calibration failure this gate exists to prevent." Writing a Design section that picks a dispatch
   rule is precisely the move that ruling forbids; writing one that honours `AC-2` as signed would
   ship the corruption path the architect found.

The data audit's required grounding is also not producible here. It asks for three counts over the
live vault (`<vault>/@*.md`). The vault is not in this tree and this cage has no shell — the same
limitation the data-premise gate declared about itself. Those counts have to be run by an actor with
a shell and vault access, outside the cage, before Finding B can be rewritten against a number.

### Re-verified independently — the blocking facts hold

I checked these against the tree rather than taking them from the two REVISE notes. All confirm.

| Claim | Where I read it | Result |
|---|---|---|
| `@*.md` is the inherited default glob | `obsidian_schemas/repositories/base.py:file_pattern:195-197` | confirmed |
| `_owns(None)` → `Path("@*.md").stem != "*"` → `"@*" != "*"` → True | `base.py:_owns:257-264` | confirmed |
| `CompanyRepository` overrides neither `file_pattern` nor `save` | `obsidian_schemas/repositories/company.py:CompanyRepository:46`; grep for `def file_pattern` / `def save` across `repositories/` returns only `book.py:51`, `book.py:144`, `meeting.py:52`, `meeting.py:166`, `base.py:195`, `base.py:356`, `person.py:1255` | confirmed |
| `_RFC2822_LEAK_RE` matches `booking.com` | `obsidian_schemas/name_validation.py:_RFC2822_LEAK_RE:54-56` — `\b[a-z][a-z0-9._\-]{4,}(com\|…)\b`; `b` + `ooking.` (7 ≥ 4) + `com` + `\b` | confirmed, matches |
| The Tier-1 table was derived from an audit of **person** names | `name_validation.py:26-28` (module docstring) | confirmed |
| `write_markdown_file`'s three fm-building arms converge on one `write_frontmatter` | `obsidian_schemas/writer.py:write_markdown_file:255-266` | confirmed |
| The Tier-1 chain is a hand-written `if` chain — **9 branches, 7 distinct keys**; `_ARROW_CONNECTIVE_RE`, `_CALENDAR_PREFIX_RE` and `_ME_TO_PREFIX_RE` all raise `"calendar_prefix"` | `name_validation.py:_raise_on_tier1:301-377` (branches at :310, :320, :329, :336, :343, :352, :359, :366, :373) | confirmed — round 1's "Member 2" count re-derived, not inherited |
| `lint_vault` derives `entity_type` from `fm.get("type", "")` and dispatches on it by equality, so untyped matches no branch | `scripts/lint_vault.py:140` / `:148`, dispatch at `:186`, `:188`, `:190`, `:374`, `:423`, `:458`, `:472`, `:490`, `:548`, `:673`, `:688` | confirmed — new this round |

**One narrowing the two REVISE notes do not state, and it bounds the fix.** The `@*.md` ambiguity is
exactly **two-way, not open-ended**: `BookRepository` and `MeetingRepository` both override
`file_pattern` (`book.py:51`, `meeting.py:52`), so Person and Company are the only two repositories
whose `_owns(None)` answers yes on the same untyped `@Foo.md`. The architect's third candidate rule —
"resolve ownership through the repository that already owns the note" — therefore has a
two-element candidate set to disambiguate, not an unbounded one. That is worth knowing before the
rule is re-chosen, because it makes the cheapest candidate materially cheaper than it looks.

### One consequence neither REVISE states: the architect's own preferred fix is incompatible with `AC-2` as signed

The architect's recommended direction is: "on an untyped dict-shaped write, apply the checks that are
**entity-agnostic** — `/` is path-hostile for a note of any type … — and withhold the person-specific
Tier-1 patterns until the write declares a type."

`AC-2` as signed cannot accommodate that. Its fixture space is swept from the WHOLE Tier-1 table
("For EVERY Tier-1 pattern NameValidator declares … not sampled"), and its untyped clause requires
that on every dict-shaped arm an untyped dict "is gated **exactly as** a `type: person` one is". Under
the architect's rule, `booking.com` on an untyped write must NOT be refused — while `AC-2` as signed
requires it to be. `_PATH_HOSTILE_RE` (`name_validation.py:_PATH_HOSTILE_RE:95`) is itself a Tier-1
branch, so "entity-agnostic checks only" is a strict SUBSET of the swept space, not a different space.

So `AC-2`'s untyped clause does not need re-scoping — it needs **re-originating with a partitioned
fixture space**: the Tier-1 branches split into an entity-agnostic subset the untyped pass sweeps and
asserts DOES fire, and a person-specific subset it sweeps and asserts does NOT fire. Asserting the
second half is what keeps the criterion class-closing rather than merely weakened, and it is what
makes a future Tier-1 branch have to declare which side it lands on. This is stated here so that the
partition is designed in the re-exploration and signed once, rather than discovered as round 7.

### A second defect in the signed set, with the same generator as round 4's

Per the class-shaped-fold rule: round 4's finding was not "the door set forgot an arm", it was **a
derived fixture space specified at a coarser unit than the unit the code actually branches on**
(the space said `function`; the code branches per `arm`). That generator has three members in this
document. Round 4 closed one. Sweeping the other two finds both still open, and both sit in signed
text.

**Member 1 — `AC-1`'s door set. CLOSED at round 4** (function → arm; ten arms across eight functions).

**Member 2 — `AC-2`'s Tier-1 set. OPEN, and it is the criterion every round certified as
"genuinely class-closing".** `AC-2` sweeps "every Tier-1 **pattern** NameValidator declares". There is
no pattern table to sweep: `name_validation.py:_raise_on_tier1:301-377` is a hand-written `if` chain,
and the only enumerable label it exposes is the stable pattern key that rides in the raised error. The
chain has **nine branches carrying seven distinct keys** — `_ARROW_CONNECTIVE_RE` (:329),
`_CALENDAR_PREFIX_RE` (:336) and `_ME_TO_PREFIX_RE` (:343) all raise the same `"calendar_prefix"` key,
deliberately, so that "invariant `by_pattern` reporting stays coherent" (WI-111 comment, :327-328). A
sweep keyed on the pattern key therefore yields seven fixtures and silently leaves two branches
unexercised — the exact under-coverage `AC-1`'s floor exists to make red, one AC over. Worse, the
refusal's key is *non-injective by construction*, so an assertion of the form "refused with key K"
cannot even distinguish which of those three branches fired. Two obligations fall out, both requiring
re-origination: the build must first **reify** the Tier-1 chain into an iterable table (there is
nothing to sweep today), and the sweep's unit must be the **branch**, with the fixture asserting the
`(input form → key)` pair rather than the key alone. The partition in the section above is also a
per-branch classification, not a per-key one — a third reason the unit has to change.

**Member 3 — `AC-5`'s job-shape set. OPEN.** `AC-5` sweeps for "**a function** returning a 2-tuple
whose body carries address-splitting evidence". Same coarseness: a second implementation of the job
can live as one BRANCH inside a function that returns a 2-tuple on only one path, or that returns
something else entirely. The document already contains the existence proof —
`person.py:_extract_email_and_name:1286` reaches for a parens regex at :1295 *before* it reaches
parseaddr, i.e. the job is written there as a branch, not as a function. Finding D's honest "this is a
lower bound, not a census" is therefore still true of the job-shape sweep that replaced it, one level
down. `AC-5`'s unit should be the returning branch, and its planted positive controls should include
a multi-branch function where only one branch does the job — the direct analogue of `AC-1(b)`'s
multi-branch control.

None of these three is a fix I may apply: `AC-2` and `AC-5` are signed. They are recorded here so
that the re-origination round Dave already owes for the architect/data-premise finding covers all of
it at once.

### The generator behind the architect's finding — swept (new, round 2)

Round 1 swept round 4's generator and stopped. The architect's finding has a DIFFERENT generator,
and the contract's class-shaped-fold rule says to name it and close the class rather than the
instance. Stated at source:

> **A predicate is adopted from an existing site together with its calibration — but that
> calibration was set by the CONSEQUENCE of being wrong at the original site, and the new site's
> consequence is different.**

That is exactly the architect's argument in one line: `_owns`'s fail-closed direction is right where
over-claiming costs one duplicate WARNING on a diagnostic surface (`base.py:_note_skip:266-274`) and
wrong where over-claiming costs a refused write judged under another entity's contract. The class is
worth naming rather than patching because **this document has already folded four members of it
without ever calling it a class** — which is why the fifth arrived as a blocking gate finding.

Every borrowing the design makes, with the consequence that calibrated it at each end:

| # | Borrowed | Consequence that calibrated it at the ORIGINAL site | Consequence at the NEW site | Status |
|---|---|---|---|---|
| 1 | `_owns`'s glob fallback (`base.py:_owns:257-264`) | `_note_skip` — over-claiming costs one duplicate WARNING on the skip surface | the gate — over-claiming costs a REFUSED WRITE judged under the wrong entity's contract | **OPEN — the architect's blocking issue** |
| 2 | `NameValidator`'s Tier-1 chain (`name_validation.py:_raise_on_tier1:301-377`) | `create_stub`, a CREATE boundary — a false positive tells a producer to fix its input for a note that does not exist yet | every write arm — a false positive makes an EXISTING note unwritable through the door its caller chose, repair tools included | **CLOSED by Finding C's delta rule** |
| 3 | `_RFC2822_LEAK_RE` (`name_validation.py:_RFC2822_LEAK_RE:54-56`) | person names on original casing, with the Maurizio/Francisco/Patricio false-positive analysis written into the comment at :48-53 | untyped `@*.md`, which by construction includes company notes, where a domain-shaped name is CORRECT | **OPEN — same fold as 1; the architect's `booking.com` specimen** |
| 4 | `Email.parse`'s angle-bracket gate (`identifier.py:141-149`) | minting an identity KEY — refuse rather than silently repair `a@b c.com` into `a@bc.com` | a display splitter whose two main callers pass inputs that are usually not addresses at all | **CLOSED by the architect's splitter ruling** (total splitter, `IdentifierError` → "not an address") |
| 5 | the `declared_type` slot on `LoudFailError` | `vault_io._bad_setting` — name a thing without leaking its value; ONE consumer | `base._note_skip` reads it and feeds it straight to `_owns` (`base.py:267-269`), where a pattern key evaluates as "not our type" | **OPEN — architect note 1. Unsigned, so this one IS closable in the spec** (dedicated `pattern` attribute) |
| 6 | function-granularity write derivation (`tests/derivations.py:_is_write_call:238`) | WI-004's CAPABILITY question — "may this file name a filesystem mutation" — which is genuinely per-file | this item's ROUTING question — "through which branch" — which is per-arm | **CLOSED at round 4 by AC-1's arm granularity** |
| 7 | `Phone.parse`'s bare-digit normalization (`identifier.py:237-240`) | an identity KEY, where the display form is noise | the STORED value, where the display form is the thing a human reads | **CLOSED by Finding G's constraint** (dedupe normalized, store display) |
| 8 | `OBSIDIAN_SCHEMAS_WRITE_GUARD`'s observe/enforce knob | WI-004's mechanical guard, where a staged rollout was worth a second setting | — | **DECLINED, correctly** (Approach E; WI-004's D6 rules one reader per setting) |
| 9 | `lint_vault`'s own `fm.get("type")` dispatch (`scripts/lint_vault.py:140`) | the linter's checks — untyped answers "neither person nor company", so person checks are SKIPPED | the gate installed at D8 inside that same loop, where Finding B's rule answers "IS a person" | **OPEN — new this round, see below** |

**The two generators intersect at member 6, and that is the useful part.** Round 1's generator
(a derived set specified at a coarser unit than the code branches on) is one DIMENSION of this one —
"adopted at the original site's unit". The other dimensions the sweep exposes are the population the
predicate was tuned on (members 2, 3), the cost of a false positive (1, 2, 4), and how many consumers
decode the value (5). Sweeping that next level down is what turns up member 9, which no dimension of
round 1's generator would have found. **Declared, per the sweep rule:** with members 1/3 folded as
one rule, 5 closable in the spec and 9 folded into the re-exploration, I find no further member —
every remaining borrowing in the design (`NameValidator.clean`'s Tier-2 repairs, `model_to_frontmatter`
as the entity→dict projection, `vault_io.write_note`'s stamp precondition) is used at the same site
and for the same consequence it was written for.

### New open member — `lint_vault` already answers the untyped question, the other way

Verified this round, and independent of the Company annexation: **`scripts/lint_vault.py` derives
`entity_type` from `fm.get("type", "")` (`scripts/lint_vault.py:140`, stored at :148) and dispatches
on it by equality at eleven sites** (`:186`, `:188`, `:190`, `:374`, `:423`, `:458`, `:472`, `:490`,
`:548`, `:673`, `:688`). An untyped note yields `""`, which equals no branch — so the linter's own,
already-shipped answer to "is this untyped `@*.md` note a person?" is **no**, and every person check
is skipped for it.

D8 is one of AC-1's ten arms. Under `AC-2` as signed, routing D8 through the gate installs inside
that same call frame a second, contradictory answer to the identical question: the repair loop
declines to run person checks on the note, while the gate judges every field that loop writes for
any other reason under the person contract. The concrete shape: an untyped `@Foo.md` needing only
the `field_type_mismatch` repair — a boolean coercion of `auto_created` (`scripts/lint_vault.py:828-833`),
nothing to do with names — reaches the whole-`fm` serialization at `:876-882`, where the gate now
applies a person-only Tier-1 table to a note the enclosing function has just classified as not a
person. Two rules, one frame, opposite answers.

Why this is a re-exploration obligation and not a build detail: whichever rule Finding B is rewritten
to, `lint_vault`'s existing dispatch is a THIRD implementation of entity dispatch in the call chain
(alongside `_owns` and the gate's own), and the item currently plans to add the second without
reconciling the third. The cheapest reconciliation is probably that the gate is handed the type the
caller already resolved rather than re-deriving one — which is also the architect's settled gate
signature ("the introduced fields plus the entity type"), and at D8 `vf.entity_type` is that value,
already computed. Stating it here so the rewrite picks a rule that is coherent at the arm where it
is hardest, rather than at the arm where it is easiest.

### Settled and carried forward — do not re-litigate in the next loop

Everything below survived the two REVISE verdicts untouched, is verified, and should be lifted into
the spec rather than re-derived. Both reviewing gates say so explicitly.

- **Approach F is the right approach** — one gate module, routing at the arms, a derived AST wall
  proving the routing total. Architect: "the chosen approach (F) is the right one"; Findings A–G's
  structural citations "re-derive correctly against the tree"; data audit: "the item's *code*-premises
  are in excellent shape".
- **The architect's two rulings are settled and need no re-derivation.** (a) *Gate signature:* no
  `existing` parameter, one entry point taking the introduced fields plus the entity type; the
  entity-shaped arms project through `model_to_frontmatter` (`writer.py:88`) first, which keeps the new
  module a leaf beside `errors.py`. (b) *Splitter:* TOTAL, returning `(address | None, display)`,
  owning the parens form *before* delegating, mapping `IdentifierError` to "not an address";
  `Email.parse`'s angle-bracket gate is NOT widened (`identifier.py:141-144`). Finding D's
  reconciliation 2 — the laxity delta on live data — stays owed to the spec as a behaviour change.
- **Finding C's delta rule** (judge what the write INTRODUCES, never what it preserves) is the
  load-bearing insight and is held on re-attack by both gates. Its *design* argument stands
  independently of the count; only the count is stale (audit item 3 asks for a re-dated number, not a
  different rule). `AC-3`'s text is fixture-based and, on my reading, needs no edit — the re-grounding
  it wants lands in Finding C's prose.
- **Finding G's phone scope-in** and its constraint — dedupe on the normalized form, store the display
  form, forced by `Phone.parse` normalizing to bare digits (`identifier.py:237-240`).
- **`AC-1`'s ten-arm floor, driven positive controls and near-miss** are the right battery and match
  the established precedent (`tests/test_write_routing.py:1-18`). Unaffected by both REVISEs.
- **Class 2's pass-throughs really cannot introduce a name or an address**, which is what makes the
  delta rule implementable.
- **The architect's four non-blocking notes are all spec obligations**, and I add one verification to
  note 1: `REASONS` (`obsidian_schemas/errors.py:REASONS:110-127`) is a closed frozenset of fifteen
  literals and `bounded_message` (`errors.py:bounded_message:134-145`) raises on any non-member, so the
  refusal's new reason literal must be chosen and added at spec time, not discovered at build time. The
  same note's point stands: give the new error class a dedicated `pattern` attribute rather than
  overloading `declared_type`, which `base._note_skip` (`base.py:_note_skip:266-274`) already feeds
  straight back into `_owns`.
- **The consumer audit is still owed** and is still the largest unstarted piece: `AC-2`'s refusal is a
  breaking change for HAL9000, exocortex and orchestrator, all of which install this library with
  `pip install -e`.

### Re-entry path — ordered, and the first step needs a shell

1. **Run the data audit's three counts against the live vault** (untyped `@*.md` population and its
   person/company mix; the Tier-1 table evaluated over every untyped note's stored `name:`; the
   current legacy-dirty count, dated). Outside the cage — this needs a shell and vault access.
2. **Rewrite Finding B's untyped rule against those numbers**, stating the count it was chosen
   against, and recording that the ambiguity is two-way (Person/Company only). Keep the fail-closed
   instinct; drop the annexation. **Check the rewrite against member 9** — the rule must be coherent
   with `lint_vault`'s existing `fm.get("type")` dispatch at the D8 arm, not only defensible in the
   abstract.
3. **Design the Tier-1 partition** the chosen rule implies (entity-agnostic vs person-specific,
   per branch), and the branch-unit reification of the Tier-1 chain.
4. **Dave re-originates and re-signs** `AC-2`, `AC-4` and `AC-5` in one round — the untyped clauses
   against the new rule and the partition, `AC-2`'s and `AC-5`'s sweep units moved to the branch.
   `AC-1` and `AC-3` stand.
5. **ac-red-team** on the re-originated set, then **architect** (its two rulings above carry forward
   and need not be re-derived), then **data-premise**, which must reach PROMOTE for D3.
6. **spec-writer.** With steps 1–5 done, the spec is largely assembly: the carried-forward list above
   plus the routing, the wall, and the `lint_vault --fix` delta threading the architect prices as the
   single largest piece of unglamorous work.

### Three questions the next spec round will owe, beyond the blocking one

Named now so the re-exploration can close them in the same loop rather than generating another round.

1. **What does the gate do on a dict-shaped write whose declared `type:` is neither `person` nor
   absent** — `type: company`, or a typo? The signed ACs cover `person` and absent; the third case is
   unstated, and it is the case a partitioned rule makes reachable rather than theoretical. Note that
   `lint_vault` already answers it, by falling through every equality branch (member 9) — so the
   answer chosen here is a third dispatch implementation unless the gate is HANDED the type the
   caller resolved rather than re-deriving one, which is what the architect's settled gate signature
   already implies.
2. **How does `lint_vault --fix` (D8) express a delta at all?** Architect note 3: the fix loop mutates
   `fm` in place across eight `elif` branches (`scripts/lint_vault.py:876-882`) with no delta object to
   hand the gate, and it lives in `scripts/`, outside the package. Threading a per-key record through
   every branch is the concrete cost, and it wants pricing before it is planned.
3. **What happens to `create_stub`'s existing refusal channel** once the same check also fires from the
   write path? `NameValidationError` (`name_validation.py:NameValidationError:125`) interpolates the
   offending name into its message and is a bare `ValueError` that `chainable_cause` suppresses
   (`errors.py:212`). Finding E resolves the write-path direction; whether `create_stub` keeps raising
   the old error, starts raising the new one, or raises both depending on entry point is unstated, and
   three downstream repositories catch on it.

## Architectural Review — 2026-08-11

**Recommendation: REVISE — return to exploration**

**Round 2, cold-start re-spawn.** Read in role order: `architect.yaml`, this document in full
(including all five ac-red-team rounds, the `ac-signoff` fence, the round-1 architectural review, the
data audit and the spec-writer hand-back), then the code every premise below turns on
(`repositories/base.py`, `repositories/company.py`, `repositories/book.py`, `repositories/meeting.py`,
`name_validation.py`, `writer.py`, `errors.py`, `tests/test_write_routing.py`, `scripts/lint_vault.py`),
plus `LESSONS.html`. This cage has no shell; every predicate below was resolved by direct source read
and grep over this tree, and the live vault was not read.

**State of the item, stated first because it bounds what this round can be.** Every section this gate
rules on — `## Intent`, `## Approach`, Finding B, `AC-2`, `AC-4` — is unchanged since the round-1
architectural review. No fold has occurred. Two further gates have ruled in the interval, both REVISE,
both on the same rule: the data audit (which adds that the population under the rule has never been
counted) and the spec-writer, which declined to write a spec and named three independent locks. So
this round is not a re-litigation of a folded design; it is the same design, re-attacked cold. I
re-derived the blocking facts myself rather than inheriting them, and they hold. What follows is
therefore a confirmation plus **two things round 1 did not have**: a sharper statement of why the
borrowed predicate cannot answer the gate's question at all, and one new finding in signed text.

### Trigger check

Three fire, unchanged: a new module (the gate); a contract change crossing into three downstream
repositories installed with `pip install -e` (`docs/backlog-campaign-2026-07-05.md:98`); a derived-wall
enforcement mechanism that must be designed rather than copied. Effort stated at one to two sessions.

### Blocking issue 1 — CONFIRMED and sharpened: `_owns` cannot answer the question the gate asks

Round 1 found that Finding B reads `@*.md` as a person convention when it is the convention Person and
Company **share**, and that borrowing `_owns`'s fail-closed direction carries a calibration set by a
different consequence. Re-derived here from the source, independently:

| Claim | Read from | Result |
|---|---|---|
| `@*.md` is the inherited default glob | `base.py:194-197` | confirmed |
| `_owns(None)` → `Path(self.file_pattern).stem != "*"` | `base.py:257-264` | confirmed; `"@*" != "*"` → True |
| `CompanyRepository` overrides neither `file_pattern` nor `save` | `company.py:46-194` (the class declares `entity_type`, `type_name`, `_index_entity`, `_clear_indexes`, `get_by_domain`, `resolve`, `get_by_industry`, `create_stub` — and nothing else) | confirmed |
| so `CompanyRepository.save` writes `@{name}.md` into the same directory the person glob walks | `base.py:380-382`, reached from `company.py:192` | confirmed |
| `_RFC2822_LEAK_RE` matches `booking.com` | `name_validation.py:54-56` — `b` + `ooking.` (7 ≥ 4) + `com` + `\b` | confirmed, matches |
| the Tier-1 table was derived from an audit of **person** names | `name_validation.py:26-28` | confirmed |

**The sharpening, and it changes what the fix has to be.** `_owns` takes no path — its signature is
`_owns(self, declared_type: Optional[str])` (`base.py:257`). It is not a path-ownership predicate; it
answers "would I claim a note *my own glob has already handed me*", which is exactly the question
`_note_skip` needs (`base.py:266-274`, reached from `_load_file`'s except at `base.py:304-305`, inside
a walk driven by `self.vault_path.glob(self.file_pattern)` at `base.py:230`). The gate has no
repository and no glob walk. It has a path. Reading the four repositories against that path shows the
predicate giving four different kinds of answer on the same untyped `@Foo.md`:

- `PersonRepository` — glob matches, `_owns(None)` True.
- `CompanyRepository` — glob matches, `_owns(None)` True.
- `BookRepository` — `file_pattern` is `*.md` (`book.py:51-53`), which **matches** `@Foo.md`, yet
  `_owns(None)` is False because the pattern is a catch-all.
- `MeetingRepository` — `file_pattern` is `Meeting *.md` (`meeting.py:52-54`), which does **not** match
  `@Foo.md`, yet `_owns(None)` is True because the pattern is a convention.

So the predicate's answer and the path's actual glob membership come apart in *both* directions, and
neither Book nor Meeting is an edge case invented for the argument — they are the only two overrides in
the tree. Round 1's framing ("the calibration does not carry") is correct but understates it: the
inputs do not carry either. Finding B's sentence "This item inherits that answer verbatim" inherits an
answer to a question the gate is not in a position to ask.

That also means the spec-writer's narrowing — "the ambiguity is exactly two-way, Person and Company" —
is right in its conclusion but must not be justified by `_owns`. It holds only under a predicate that
combines glob **match** against the path with glob **shape** (convention vs catch-all); `_owns` supplies
only the second half. Whichever rule the re-exploration picks, that composite is the thing that has to
be written down, and it is new code, not a borrowing.

**Why this is still architectural rather than spec-time.** `AC-2`'s untyped clause requires that at
every dict-shaped arm "a dict with `type:` absent, under the `@*.md` convention, is gated exactly as a
`type: person` one is", with the exclusion set "asserted to BE exactly" a named four; `AC-4` mirrors it.
Both are inside the `ac-signoff` hash span (`ac_hash_AC-2: b6874ac5d7ef`, `ac_hash_AC-4: 175736170bcc`).
There is no arm through which an untyped company note can be written and no room for the build to
decline, so `write_markdown_file(vault/"@booking.com.md", extra_fields={"name": "booking.com"})` — the
D1c arm, dict-shaped, untyped, introducing a name — is refused as `rfc2822_leak` under the set as
signed, against an item whose own parked defect 3 says "This item stays **Person-only**". This is
LESSONS #21 (`LESSONS.html:453`, "a review gate validates within the premise") in its exact shape:
five ac-red-team rounds each attacked gameability, and the premise was ambient by the time they ran.

**Direction, offered as direction rather than design.** The root is not the dispatch rule; it is where
the gate lives. Six of the ten arms are *generic* infrastructure — `write_markdown_file` (writer.py:159),
`BaseRepository.save` (base.py:356), `update_fields` (base.py:403), `update_frontmatter_field(s)`
(writer.py:292, :350), `roundtrip_file` (writer.py:402) — shared by Person, Company, Book and Meeting
alike. Routing a person-specific contract through them forces the generic layer to re-derive an entity
type it was designed never to know, which is precisely where the untyped question is born. The two
shapes that dissolve it rather than answer it: (a) make the semantic contract **polymorphic and owned
by the entity type** — a hook `BaseRepository` defaults to no-op and `PersonRepository` overrides — so
the repository doors carry no dispatch at all, and only the four repository-less arms need a declared
type; (b) require dict-shaped doors to be **handed** the entity type by the caller and refuse an
undeclared one, which is also the round-1 gate-signature ruling ("the introduced fields plus the entity
type") and is what the spec-writer's member-9 finding needs at D8, where `vf.entity_type`
(`scripts/lint_vault.py:93`, derived from `fm.get("type", "")` at `:148`) is already computed. Keep the
fail-closed instinct; drop the annexation. Whichever is chosen, round 2's reasoning that the two halves
must be pinned together — dispatch fires once per write, upstream of the name/address split — survives
this finding intact.

### Blocking issue 2 — NEW: `AC-2` sweeps a "pattern table" that does not exist, and misses a Tier-1 branch that lives outside the chain

`AC-2` derives its fixture space "from that module's own pattern table, not sampled". Read against the
tree, there is no table to sweep, and the shortfall is worse than the unit problem the spec-writer's
hand-back records.

- `_raise_on_tier1`'s docstring says "Walks the Tier 1 pattern table" (`name_validation.py:302`), but
  the body is a hand-written `if` chain — nine `if` statements at `:310`, `:320`, `:329`, `:336`,
  `:343`, `:352`, `:359`, `:366`, `:373`. There is no iterable object anywhere in the module. So the
  build must **reify** the chain before anything can sweep it; the AC as signed names a structure the
  code does not have.
- The chain's nine branches raise **seven** distinct keys: `_ARROW_CONNECTIVE_RE` (:329),
  `_CALENDAR_PREFIX_RE` (:336) and `_ME_TO_PREFIX_RE` (:343) all raise `calendar_prefix`, deliberately,
  so that "invariant `by_pattern` reporting stays coherent" (WI-111 comment, `:326-328`). A sweep keyed
  on the key yields seven fixtures and leaves two branches unexercised, and an assertion of the form
  "refused with key K" cannot even say which of the three fired.
- **New, and not recorded anywhere in this document: a tenth Tier-1 refusal lives outside the chain
  entirely.** `NameValidationError("empty", "name is empty or whitespace-only")` is raised in
  `validate_strict` (`name_validation.py:257-259`) and again in `clean` (`:277-278`) — before either
  delegates to `_raise_on_tier1`. It is a Tier-1 refusal by every property the AC cares about (same
  exception, same stable key), and **no** reification of `_raise_on_tier1`, at branch granularity or
  any other, reaches it. Both public entry points carry it, so it is live on every arm this item routes.
  A sweep that is class-closing over the chain is still not class-closing over the module.
- This also constrains the partition the untyped rule needs: `_PATH_HOSTILE_RE` (`:95`) is a branch of
  the same chain (`:352`), so "apply the entity-agnostic checks only" is a strict SUBSET of the swept
  space, not a different space. The partition has to be per-branch and has to say which side `empty`
  lands on.

I cannot fold this — `AC-2` is signed. It is recorded here so the re-origination round Dave already
owes for issue 1 covers it in the same pass rather than surfacing as round 8.

### Rulings carried forward — settled, do not re-derive

Round 1's two rulings stand unchanged and were re-checked against the code this round:

- **Gate signature:** no `existing` parameter, one entry point taking the introduced fields plus the
  entity type; the entity-shaped arms project through `model_to_frontmatter` (`writer.py:88-130`) first,
  which keeps the new module a leaf beside `errors.py`. Reinforced by the direction above — a gate that
  is *handed* the type is the shape that reconciles the third dispatch implementation at D8.
- **Splitter:** TOTAL, returning `(address | None, display)`, owning the parens form *before*
  delegating, mapping `IdentifierError` to "not an address"; `Email.parse`'s angle-bracket gate is NOT
  widened. Finding D's reconciliation 2 (the laxity delta on live data) stays owed to the spec as a
  behaviour change.

### Review

**Fit:** Strong, unchanged. Approach F is the same shape WI-004 landed, and the precedent it copies is
real and load-bearing: `tests/test_write_routing.py:1-18` is a module docstring that already argues the
vacuity case out loud ("a count oracle says NOTHING about a matcher's reach") and already ships the
plant-a-scratch-module-and-drive-it-through-the-live-function battery `AC-1(b)/(c)` demand
(`test_write_routing.py:22-37` imports the derivation functions from `tests.derivations` rather than
re-implementing them). Finding A's rejection of the mint's named mechanism and Finding B's location of
the seam both hold.

**Duplication:** Unchanged and correct — three jobs, not four copies, with the self-declared lower-bound
limit that `AC-5`'s job-shape sweep is built on.

**Boundaries:** Where both blocking issues live. Issue 1 is a predicate borrowed across a boundary
whose inputs do not carry, not merely whose calibration does not; the generic-infrastructure direction
above is the boundary question underneath it. The constraint that the gate must not live inside
`vault_io` remains right.

**Determinism boundary (LLM vs code):** n/a — no capability here is handed to an LLM. The item is the
opposite move: a contract currently held by producer discipline, made structural.

**Reversibility:** Good, unchanged — one module, ten call sites, one test file. But note the coupling
the sign-off has introduced: `AC-1`'s ten-arm floor is now signed text, so the arm count cannot fall
without turning the wall red. That is a real reduction in reversibility of the *design*, not of the
code, and it is why issues 1 and 2 both have to be re-originated rather than folded.

**Generalization:** Correctly scoped Person-only in intent, with Company parked to WI-022 — and issue 1
is precisely the place where the signed criteria break that scoping. Fix the dispatch rule and the
scoping holds.

**Cost & maintenance:** One to two sessions remains plausible for the routing, plus the Tier-1
reification issue 2 now adds and the `lint_vault --fix` delta threading round 1 priced as the single
largest unglamorous piece.

**Build vs extend vs integrate:** Extend, correctly — `NameValidator`, `Email.parse` and
`normalize_phone` all exist and are tested. Issue 2 adds one genuine *build*: the Tier-1 chain has to
become a real table before anything can sweep it.

**Prior art (outside view):** Unchanged from round 1 and not blocking. The design builds a derived AST
wall around a real constraint (Python cannot make a semantic check unavoidable the way WI-004's
capability wall could), the standard answers are considered and rejected on cited grounds (Approach C
fires on READ; Approach B sees the merged record, never the delta), and no cited execution is owed
because the wall instrument is this repository's own established precedent
(`tests/test_write_routing.py`), not novel machinery. The one standard answer still open —
*shrink the surface rather than police it* — is note 2 below.

### Notes (non-blocking) — carried and one added

1. Round 1's four notes all stand and are re-affirmed: the dedicated `pattern` attribute rather than
   overloading `declared_type` (`base.py:267-269` feeds it straight back into `_owns`); the new
   refusal's reason literal must be chosen at spec time because `REASONS` (`errors.py:110-127`) is a
   closed frozenset of fifteen literals and `bounded_message` raises on any non-member
   (`errors.py:139-145`); `lint_vault --fix`'s missing delta object; and the sibling `save` overrides
   in `meeting.py` / `book.py` that are correctly not arms.
2. The three-functions-one-shape collapse (`update_frontmatter_field` / `update_frontmatter_fields` /
   `roundtrip_file`) remains the pay-down-principal move and remains blocked by `AC-1`'s signed floor.
   Since a re-origination round is now owed anyway, this is the moment it could be sequenced in — but
   it is a *different* item, and I am not recommending it be absorbed here.
3. The data audit's three counts remain the first step of the re-entry path and cannot be produced in
   this cage. Nothing in this round's findings changes that ordering: issue 1's rule must be chosen
   against a number, and issue 2's partition depends on which rule is chosen.

```verdict
gate: architect
verdict: REVISE
date: 2026-08-11
model: claude-opus-5
targets: AC-2, AC-4, #exploration-notes, #approach
note: Re-attacked cold against an unfolded document — round 1's annexation finding is confirmed and sharpens to a structural one (`_owns` takes no path; Book's `*.md` matches `@Foo.md` yet answers False while Meeting's `Meeting *.md` answers True without matching, so the borrowed predicate cannot answer the gate's question at all), and one new defect in signed text: AC-2 sweeps a "pattern table" that does not exist (`_raise_on_tier1` is a nine-branch `if` chain raising seven keys) and would still miss the `empty` Tier-1 refusal raised outside it at name_validation.py:259/:278.
```

## Data Audit — 2026-08-11

**Recommendation: REVISE — return to exploration**

**Round 2, cold-start re-spawn.** Read in role order: `data-premise.yaml`, this document in full
(all five ac-red-team rounds, the `ac-signoff` fence, both architectural reviews, the round-1 data
audit, the spec-writer hand-back), then the code every premise turns on. Same method bound as every
other round in this cage: **no shell, scope limited to this tree's files, the live vault was not
read.** I re-derived the blocking facts from source rather than inheriting them from the round-1
audit or from either architect round.

**State first, because it bounds what this round can be.** Nothing has been folded since the
round-1 data audit. `## Intent`, Finding B, `AC-2`, `AC-4` and the sign-off fence are byte-unchanged;
the only additions are three further gate sections, all REVISE. So this is not a re-audit of a
revised premise — it is the same ungrounded premise, re-attacked cold. The verdict is therefore the
same verdict, and saying so plainly is the honest output. What this round ADDS is one new grounding
obligation the earlier rounds could not have named, because it only becomes a data question once the
architect's round-2 issue 2 exists.

### Trigger check

**Class 1 AND Class 2 — unchanged, both still fire on the same rule.**

- Class 1 (data-distribution / field-presence): the pinned untyped-dispatch rule is an existence
  claim about live data — that `@*.md` notes with no `type:` key exist, and that they are person
  notes. Finding C's legacy-dirt claim is a second Class-1 claim.
- Class 2 (rule-effect-against-existing-corpus): `AC-2`'s untyped clause is a new refusal rule whose
  correctness depends on what it flags when run against the corpus **as it exists today**. Eight gate
  rounds have now reasoned about that rule; none has executed it.

### Premise vs reality — re-derived this round, not inherited

Every leg of the round-1 table re-read from source. All confirm, and I add the two the architect's
round-2 issue 2 turns on:

| Claim | Read from | Result |
|---|---|---|
| `@*.md` is the inherited default glob | `base.py:194-197` | confirmed |
| `_owns(None)` → `Path("@*.md").stem` is `"@*"`, `!= "*"` → True | `base.py:257-264` | confirmed |
| `CompanyRepository` overrides neither `file_pattern` nor `save` | grep `def (file_pattern\|save)` across `repositories/` returns only `base.py:195`, `base.py:356`, `book.py:51`, `book.py:144`, `meeting.py:52`, `meeting.py:166`, `person.py:1255` — **no `company.py` hit for either** | confirmed |
| `_RFC2822_LEAK_RE` matches `booking.com` | `name_validation.py:54-56` — `b` + `ooking.` (7 ≥ 4) + `com` + `\b` | confirmed, matches |
| the Tier-1 table was derived from an audit of **person** names | `name_validation.py:26-28` | confirmed |
| `_raise_on_tier1` is a nine-branch `if` chain raising **seven** distinct keys | `name_validation.py:301-377` (branches at :310, :320, :329, :336, :343, :352, :359, :366, :373; `calendar_prefix` raised at :331, :338, :345) | confirmed |
| a **tenth** Tier-1 refusal, key `empty`, is raised OUTSIDE the chain by both public entry points | `name_validation.py:259` (`validate_strict`) and `:278` (`clean`) | confirmed |

So the round-1 finding stands in full, and the architect's round-2 issue 2 stands on the facts.

**The three counts required by the round-1 audit have not been produced.** They cannot be produced
here: the vault is not in this tree, this cage has no shell, and grep for `OBSIDIAN_VAULT_PATH`
across the tree resolves only to source, docs and tests — no live vault path is readable from within
the scope bound. The spec-writer reached the same conclusion independently and made it step 1 of its
re-entry path. This is not a gate that can unblock itself.

### New this round — the Tier-1 partition is a DATA question, and nobody has stated it as one

The architect and the spec-writer both now require a **partition** of the Tier-1 refusals into an
entity-agnostic subset (fires on an untyped write) and a person-specific subset (withheld until the
write declares a type). Both frame it as a design task. Read against the source it is not: the
partition is a claim about which patterns would misfire on real company names, and that claim is
exactly as unmeasured as the population claim round 1 flagged.

The classification is not obvious from the source. Reading the ten refusals cold, three are
defensibly entity-agnostic — `path_hostile_char` (`:352`, `/` breaks `@{name}.md` for a note of any
type, `base.py:381`), `empty` (`:259`/`:278`), and `pure_digit_name` (`:373`) — and the remaining
seven are person-tuned by their own comments: `_RFC2822_LEAK_RE`'s false-positive analysis is
written against *person* first names (`:48-53`, Maurizio/Francisco/Patricio), `calendar_prefix` and
`unknown_contact` name person-scoped producers (calendar attendee fields, the WhatsApp scanner), and
`contains_email_chars` (`:310`) is the one I cannot call from source at all — an `@` in a company
name is as impossible as in a person's, but that is an intuition, not a count. The architect's own
`booking.com` specimen is the proof that the intuition fails somewhere in this list.

**So the partition needs its own predicate, and it is cheap:** run the Tier-1 table over the vault's
`type: company` notes' stored `name:` values and report per-key flag counts. Every key that flags a
legitimate company name is person-specific by evidence; a key that flags none across the whole
company corpus is entity-agnostic by evidence rather than by reading. Without that run, the partition
gets chosen by the same mechanism that produced the annexation — a plausible reading of a pattern's
comment — and the fold will have re-derived the defect one level down. That is the round-1 finding's
own generator, and naming it here is what stops it becoming round 9.

### Required grounding

Items 1–4 are carried unchanged from the round-1 audit (still unrun). Item 5 is new.

1. **Count the untyped population and its entity mix.** Over `<vault>/@*.md`: how many notes lack a
   `type:` key; of those, how many are companies, how many persons, how many neither.
2. **Run `AC-2`'s untyped rule against the corpus as it stands** (the Class-2 predicate): for every
   untyped `@*.md` note, evaluate the Tier-1 table against its stored `name:` and report what it
   flags, per key.
3. **Re-ground Finding C's premise** — the current count of Tier-1-dirty stored names, dated
   2026-08-11. If it is zero, say so and keep the delta rule on its design argument.
4. **Carry the counts into the fold** — state whichever rule Finding B is rewritten to alongside the
   number it was chosen against, so build-start re-grounding has something to detect rot in.
5. **NEW — run the Tier-1 table over the `type: company` corpus, per key.** This is the predicate
   that decides the partition items 1–4 leave open, and it is the one that would have caught the
   `booking.com` class two months before an architect read for it. It must cover all TEN refusals,
   including `empty` (`:259`/`:278`), which no reification of `_raise_on_tier1` reaches.

### Conclusion

Unchanged and re-confirmed from source: the item's *code* premises are in excellent shape and every
structural citation re-derives, but its central *data* premise — that an untyped `@*.md` note is a
person note — is an unmeasured claim pinned by equality into two signed acceptance criteria, and
`_owns(None)` is True for `CompanyRepository` too. The one thing this round adds is that the FIX now
carries an unmeasured premise of its own: the Tier-1 partition both reviewing gates require is a
classification of ten refusals against a company corpus nobody has run them over.

**Signal for the factory, stated because the targets line alone cannot carry it:** this is the same
target as the round-1 audit, but it is not a treadmill round — the document has not moved between
them, and no gate re-run can move it. Step 1 of the spec-writer's re-entry path needs a shell and
vault access **outside this cage**. Spawning another exploration, architect or data-premise round
before those counts exist will reproduce this section a third time. Stage stays at `exploring`.

```verdict
gate: data-premise
verdict: REVISE
date: 2026-08-11
model: claude-opus-5
targets: AC-2, AC-4, #exploration-notes
note: Re-audited cold against an unfolded document — round 1's ungrounded untyped-`@*.md` premise stands verbatim (re-derived from source: `_owns(None)` True for CompanyRepository, which overrides neither file_pattern nor save; `_RFC2822_LEAK_RE` matches `booking.com`), the three required vault counts remain unrun and unrunnable in this cage, and the fix both reviewing gates now demand carries a NEW ungrounded premise — the Tier-1 entity-agnostic/person-specific partition is a per-key claim about company names that has never been run against the company corpus, and must cover the tenth refusal (`empty`) raised outside `_raise_on_tier1` at name_validation.py:259/:278.
```

## Spec-Writer Hand-Back — 2026-08-11 (round 3)

**No spec was written. The item stays at `exploring`.** This supersedes the round-2 hand-back above,
which is kept as the record of the two generator sweeps it ran — both carried forward here, one of
its carried-forward claims corrected.

Cold-start, read in role order: `spec-writer.yaml`, this document in full (all five ac-red-team
rounds, the `ac-signoff` fence, BOTH architectural reviews, BOTH data audits, the round-2 hand-back),
the project `CLAUDE.md`, then the code every premise below turns on (`name_validation.py`,
`repositories/person.py`, `repositories/base.py`, `repositories/company.py`, `writer.py`,
`errors.py`, `tests/derivations.py`, `scripts/lint_vault.py`, `scripts/migrate_person_to_discuss.py`).
Every citation below was re-derived from source this round, not inherited. This cage has **no shell**,
its scope bound is this tree's files only, and the live vault was not read.

**This is the THIRD spec-writer round against the same objection, and the answer is unchanged: hand
back.** The three locks are restated compactly below because each alone is still sufficient and none
is a judgement a fresh spawn could decide differently. What round 3 ADDS, so the loop is not spent:

- **The architect's round-2 issue 2 has a generator, and sweeping it turns up two more open members
  in signed text** — both verified from source this round, neither recorded anywhere in this
  document. One of them (`AC-2` × the phone sentinel) breaks a shipped feature, WI-083 phone-only
  stubs, on the item's own primary door.
- **One consequence for `## Approach`** — the architect's round-2 target that no round has yet
  answered. The settled gate signature ("the introduced fields plus the entity type") is one input
  short, and the missing input is caller intent the gate cannot re-derive without repeating the
  exact move issue 1 rejects.
- **A re-ordering of the re-entry path.** Three of the data audit's five required counts are
  CONDITIONAL on which gate shape is chosen, not prior to it. Choosing the shape first makes the
  vault work materially smaller. Stated so the shell-holding actor runs the right queries once.
- **One correction to the round-2 hand-back**: it carried `AC-3` forward as needing no edit. It does.

### Why no spec — the three locks, unchanged

1. **The conveyor refuses the transition.** Rule D3 refuses `→ specced` without a data-premise
   PROMOTE. The standing data-premise verdict is REVISE, now twice (`2026-08-11`, rounds 1 and 2).
   A perfect spec could not be promoted from here.
2. **Both REVISE verdicts target SIGNED text.** `AC-2` and `AC-4` are inside the `ac-signoff` hash
   span (`ac_hash_AC-2: b6874ac5d7ef`, `ac_hash_AC-4: 175736170bcc`, `ac_hash: a76ebad54da2`).
   WI-061 is explicit: refine a signed AC within the spirit of the original, but **if an original AC
   proves wrong, escalate and let Dave re-originate.** Four gate rounds across two gates now say
   these originals are wrong on facts, not imprecise. That is the escalate branch.
3. **The architect named this role as the wrong place to fix it** — "the spec-writer would have to
   redesign the dispatch rule, which is the calibration failure this gate exists to prevent."

The data audit's required grounding is still not producible here: it asks for counts over
`<vault>/@*.md`, the vault is not in this tree, and this cage has no shell. Both data-premise rounds
and both prior spec-writer rounds reached that conclusion independently.

### Re-verified independently this round — the blocking facts hold, and two are sharper

| Claim | Where I read it | Result |
|---|---|---|
| `_raise_on_tier1` is a hand-written `if` chain, **9 branches, 7 distinct keys** — no iterable table exists in the module | `obsidian_schemas/name_validation.py:_raise_on_tier1:301-377` (branches at :310, :320, :329, :336, :343, :352, :359, :366, :373; `calendar_prefix` raised at :331, :338, :345) | confirmed |
| a **tenth** refusal, key `empty`, is raised OUTSIDE the chain by both public entry points | `name_validation.py:validate_strict:258-259` and `name_validation.py:clean:277-278` | confirmed |
| `_RFC2822_LEAK_RE` matches `booking.com`; the Tier-1 table was derived from an audit of **person** names | `name_validation.py:_RFC2822_LEAK_RE:54-56`; module docstring `:26-28` | confirmed |
| `CompanyRepository` overrides neither `file_pattern` nor `save`, so `_owns(None)` is True for it too | `obsidian_schemas/repositories/company.py:CompanyRepository:46`; `base.py:file_pattern:195-197`; `base.py:_owns:257-264` | confirmed |
| `write_markdown_file`'s three fm-building arms converge on one `write_frontmatter(fm)` | `obsidian_schemas/writer.py:write_markdown_file:255-266` | confirmed |
| `REASONS` is a closed frozenset of **fifteen** literals; `bounded_message` raises on any non-member | `obsidian_schemas/errors.py:REASONS:110-127`; `errors.py:bounded_message:139-145` | confirmed |
| **NEW —** the Tier-1 chain is CONDITIONALLY SUPPRESSED by `allow_phone_sentinel`, and the suppression is live in production | `name_validation.py:253-254` / `:274-275`; caller at `obsidian_schemas/repositories/person.py:create_stub:1405-1407` | confirmed |
| **NEW —** `_normalize_address_fields` writes THREE identifier-bearing fields, not two: `emails[]`, `phones[]` (via the caller) and `aliases[]` | `person.py:_normalize_address_fields:1300-1343` — `person.emails = new_emails` at :1317, `person.aliases = new_aliases` at :1343 | confirmed |
| `scripts/migrate_person_to_discuss.py` re-emits the frontmatter as the VERBATIM string it read, so it is a Class-2 pass-through and correctly not an arm | `scripts/migrate_person_to_discuss.py:81` / `:103` / `:109` | confirmed |

**One sharpening on the `empty` refusal that the architect's note leaves open, and it raises the
stakes.** `create_stub` guards its validator call with `if name and name.strip():`
(`person.py:1405`), so `empty` is UNREACHABLE on the create path — it has never fired in production.
On the write path it is reachable immediately: `write_markdown_file(path, extra_fields={"type":
"person", "name": ""})` is a legal D1c call that succeeds today and is refused under the gate. So
`empty` is not a refusal this item ROUTES; it is a refusal this item INTRODUCES, on a code path with
no prior art and no audit behind it. That is a stronger reason for it to be signed explicitly rather
than swept up by a reification, and it is the one Tier-1 refusal whose partition side cannot be
decided by running the table over the company corpus (data audit item 5) — an empty name is empty
for a note of any type.

### The generator behind the architect's round-2 issue 2 — named and swept

Per the contract's class-shaped-fold rule, the finding in front of me is not "AC-2 forgot the `empty`
branch". Stated at source, the generator is:

> **An AC names a CONTAINER as its swept space, but the property it claims to close lives on a
> SURFACE the container does not span — and the mismatch runs in BOTH directions: refusals and
> call-shapes that live outside the container escape the sweep, while cases the container holds are
> ones the property must EXEMPT.**

This is a level down from the round-2 hand-back's generator ("a derived fixture space specified at a
coarser unit than the unit the code branches on"). That one was about the GRAIN of the container;
this one is about its EXTENT. Round 2 swept grain and found three members. Sweeping extent across
all five criteria — the next level of the ladder — finds five, of which two are new:

| AC | Container the AC names | Surface the property actually lives on | Status |
|---|---|---|---|
| AC-1 | write arms "in `obsidian_schemas/` and `scripts/`" | every site building vault bytes from a frontmatter dict | **CLOSED by this sweep.** The only other candidate in either directory, `scripts/migrate_person_to_discuss.py:103`, re-emits the frontmatter string verbatim (`:81`) and cannot introduce a name — a Class-2 pass-through by the item's own definition. No frontmatter-building site exists outside the two roots. The container spans. |
| AC-2 | "that module's own pattern table" | `NameValidator`'s actual refusal surface: **(branch × sentinel-state)** across BOTH public entry points | **OPEN — three ways.** (i) there is no table (architect issue 2); (ii) 9 branches / 7 keys, non-injective (round-2 Member 2); (iii) `empty` outside the chain (architect issue 2); and **(iv) NEW — the sentinel exemption, below.** |
| AC-3 | "a note whose STORED name already matches a Tier-1 pattern" | same surface as AC-2, read from the other side | **OPEN — NEW.** Correcting the round-2 hand-back, which carried AC-3 forward as needing no edit. See below. |
| AC-4 | "lands in `emails[]`/`phones[]`" | the identifier fields the normalization reads AND writes: `emails[]`, `phones[]`, **`aliases[]`** | **OPEN — NEW, below.** |
| AC-5 | "a function returning a 2-tuple" | the job, which can live as one BRANCH of a function that returns something else | **OPEN** — round-2 Member 3, unchanged. |

**Declared, per the sweep rule.** I swept extent over all five criteria and over both dimensions the
generator has (things outside the container that belong in; things inside it that must be exempt).
Beyond the five rows above I find no further member: `AC-1`'s near-miss and positive-control battery
already pin extent on the wall side, and `AC-3`'s and `AC-5`'s remaining containers are the two named.
The next level down — intersections, e.g. "an untyped write introducing an `aliases[]` entry whose
display half is Tier-1 dirty" — is a real cell and is reachable, but it is a *product* of the members
above rather than a new member, and it closes automatically once AC-2's and AC-4's surfaces are stated
correctly. Naming it here so the re-origination round covers the cell rather than discovering it.

### New open member 1 — `AC-2` as signed makes WI-083 phone-only stubs unwritable

`pure_digit_name` (`name_validation.py:373-377`) is a Tier-1 pattern. `AC-2` requires that "For EVERY
Tier-1 pattern NameValidator declares … a write that INTRODUCES a matching name is refused at every
ARM in AC-1's derived set", typed-pass exclusion set "asserted to BE exactly `{roundtrip_file}`".
`PersonRepository.save` is an arm and is not excluded.

But the codebase deliberately and conditionally PERMITS that exact name form. `validate_strict` and
`clean` both take `allow_phone_sentinel` and return the name untouched before the chain runs when it
is set (`name_validation.py:253-254`, `:274-275`), and the flag is live in production:
`create_stub` computes `_allow_phone_sentinel = bool(phone) and name.strip().lstrip("+").isdigit()`
(`person.py:1406`), passes it (`:1407`), and then calls `self.save(person, …)` at `person.py:1475`.
That is D3 — the item's own primary door — carrying a name that matches a Tier-1 pattern, by design,
for the documented WI-083 phone-only-stub path (`create_stub`'s own docstring, `person.py:1358-1361`).

Two consequences, and the second is the larger one:

1. **Creation breaks.** Under `AC-2` as signed the `save` at `person.py:1475` must be refused, so a
   phone-only stub can no longer be created through the function whose docstring documents the case.
2. **Every subsequent re-save breaks too.** Finding C rules that "An entity write (D1–D3) rewrites
   the whole record from a typed model, so its name IS the delta." So for a phone-sentinel person the
   name is INTRODUCED on every entity-shaped write, not merely the first — an ordinary
   load-set-`company`-`save()` enrichment is refused. `AC-3`'s exemption ("stays writable for every
   write that does not set the name") never reaches it, because under the delta rule no entity write
   is a write that does not set the name. That is why AC-3 is implicated and why the round-2
   hand-back's "AC-3 needs no edit" is wrong.

**Why this is re-origination and not a build detail.** The sentinel is per-call caller intent. The
gate cannot receive it: the architect's settled signature is "the introduced fields plus the entity
type", and nothing in it carries "this pure-digit name is intentional". The gate could re-derive it
from the co-present phone exactly as `create_stub` does at `:1406` — but re-deriving caller intent
inside a generic layer is precisely the move blocking issue 1 rejects for the entity type, one input
over. So this changes either a signed AC or a settled architectural ruling, and both are above this
role. It also lands in the same partition question: `pure_digit_name` is the one Tier-1 key the data
audit's round-2 reading called "defensibly entity-agnostic", and it turns out to be the key with a
live, deliberate person-scoped exemption.

### New open member 2 — `AC-4`'s field container omits `aliases[]`, which the code it replaces reads and writes

`AC-4` asserts that an identifier arriving through every arm "lands in `emails[]`/`phones[]` in the
same normalized form". The behaviour it is replacing spans a third field.
`_normalize_address_fields` walks `person.emails` (`person.py:1304-1317`) **and** `person.aliases`
(`:1323-1343`), and on the aliases pass it extracts a wrapped address out of an alias entry and
appends it to `person.emails` (`:1326-1329`) while keeping the display half in `aliases[]`
(`:1331-1333`). `create_stub` seeds `aliases=[email]` with a bare address (`person.py:1448`), so the
aliases-as-identifier-input path is not hypothetical — it is the path parked defect 2 already
describes.

So `aliases[]` is on BOTH sides of the property: an input the normalization reads addresses out of,
and an output normalized values land in. `AC-4`'s container names it on neither. A gate that
normalizes `emails[]` and `phones[]` and leaves `aliases[]` untouched satisfies `AC-4` as signed
while `aliases: ["Al B <A@B.com>"]` — handled today at `person.py:1323-1337` — writes raw through
every arm, and the D3 behaviour the item must not regress is silently lost. `### Examples of done`
mentions `aliases[]` once, on the output side ("`Al B` has landed in `aliases[]`"), which is what
makes the omission read as deliberate scoping rather than a gap; it is not scoped anywhere in the
criterion's `desc` or `why`.

### Consequence for `## Approach` — the architect's round-2 target, answered as far as this role may

Round 2 of the architectural review added `#approach` to its targets and located the root as *where
the gate lives*: six of the ten arms are generic infrastructure shared by Person, Company, Book and
Meeting, so routing a person-specific contract through them forces the generic layer to re-derive an
entity type it was designed never to know. Two shapes were offered — (a) a polymorphic hook owned by
the entity type, (b) hand the gate a declared type and refuse an undeclared one.

**What this round adds to that choice, without making it:** the entity type is not the only piece of
caller-only context the gate needs. New open member 1 shows a second — the sentinel — and the
round-2 hand-back's member 9 shows a third already computed by a caller (`vf.entity_type` at
`scripts/lint_vault.py:93`, derived from `fm.get("type", "")` at `:148`). Three independent findings,
from three gates, all say the same thing: **every time the gate re-derives something the caller
already knew, a defect appears.** That is an argument about the SIGNATURE, and the signature is
settled architect text ("the introduced fields plus the entity type"). It is one input short of what
the code requires, and widening it is not a refinement I may make.

Stated as the concrete question for the re-exploration, since it is what shape (a) and shape (b)
actually differ on: **does a write DECLARE its semantic context (type, and whether a
pattern-matching name is intentional), or does the gate INFER it?** Under (b) — declare — the untyped
question dissolves rather than being answered, and with it three of the data audit's five counts.
Under (a) — polymorphic — the repository arms carry no dispatch at all, but the four repository-less
arms still need a declared type, so (b) is a strict sub-part of (a) rather than an alternative to it.
Either way the sentinel needs a channel. This is the `#approach` fold the re-exploration owes.

### Re-entry path — re-ordered, with the reason

The round-2 hand-back put "run the three counts" first. Round 2 of the data audit then added a
fourth and fifth. Read against what each count is FOR, three of the five are conditional on a
decision that has not been made, and running them first risks running the wrong ones:

1. **Choose the gate SHAPE first** — declare-vs-infer, per the section above. This is architect work
   and needs no vault access. It is unconditional and it bounds everything below.
2. **Run the counts the chosen shape actually needs.** Outside the cage — this needs a shell and
   vault access.
   - *Unconditional under every shape:* data-audit item 1 (the untyped `@*.md` population and its
     person/company/neither mix — under a declare shape this is no longer a rule-choice number but it
     is still the consumer-blast-radius number, since it sizes how many live writes start refusing)
     and item 3 (the current, dated count of Tier-1-dirty stored names, re-grounding Finding C).
   - *Conditional on an INFER shape:* items 2 (the Tier-1 table run over untyped notes' stored
     `name:`) and 5 (the Tier-1 table run per key over the `type: company` corpus, which decides the
     entity-agnostic/person-specific partition). Under a declare shape there is no untyped dispatch
     and no partition, and both become moot.
   - **NEW, unconditional:** count the live phone-sentinel population — notes whose stored `name:`
     matches `^\+?\d+$`. That is the population new open member 1 makes unwritable, and it is the
     number the sentinel channel has to be justified against.
3. **Rewrite Finding B's rule against those numbers**, stating the count it was chosen against.
   Record that the `@*.md` ambiguity is exactly two-way (Person/Company — `book.py:51` and
   `meeting.py:52` are the only other `file_pattern` overrides), but **do not justify it with
   `_owns`**: the architect's round-2 sharpening is right that `_owns` takes no path and its answer
   and the path's glob membership come apart in both directions. Check the rewrite against member 9 —
   the rule must be coherent with `lint_vault`'s existing `fm.get("type")` dispatch at the D8 arm.
4. **Design the Tier-1 refusal surface**, not just a partition: the branch-unit reification of the
   chain, the `empty` refusal outside it, and the sentinel exemption inside it. All three are the
   same object and should be specified once.
5. **Dave re-originates and re-signs `AC-2`, `AC-3`, `AC-4` and `AC-5` in one round.** `AC-1` stands.
   The list has grown by one since the round-2 hand-back (`AC-3`, per new open member 1).
6. **ac-red-team**, then **architect** (its two rulings carry forward except where the signature
   question above reopens the first), then **data-premise**, which must reach PROMOTE for D3.
7. **spec-writer.** With 1–6 done the spec is largely assembly.

### Settled and carried forward — do not re-litigate

Unchanged from the round-2 hand-back and re-affirmed by both round-2 gates, with one correction.

- **Approach F is the right approach**; Findings A, C, D, E, G and the arm-granularity refinement of
  Finding B all hold; every structural citation re-derives. Both reviewing gates say so explicitly.
- **The architect's two rulings** — gate signature (no `existing` parameter, one entry point, entity
  arms project through `model_to_frontmatter` at `writer.py:88-130`) and splitter (TOTAL, returns
  `(address | None, display)`, owns the parens form before delegating, maps `IdentifierError` to "not
  an address", does NOT widen `Email.parse`'s angle-bracket gate at `identifier.py:141-144`) — stand,
  subject only to the signature question raised above.
- **Finding C's delta rule** is load-bearing and held on re-attack by four gate rounds; only its
  count is stale.
- **Finding G's phone scope-in** and its constraint (dedupe on the normalized form, store the display
  form, forced by `Phone.parse` at `identifier.py:237-240`).
- **`AC-1`'s ten-arm floor, driven positive controls and near-miss** are the right battery and match
  the precedent (`tests/test_write_routing.py:1-18`). Unaffected by every REVISE so far, and its
  container is now swept and closed (table above).
- **The new refusal needs a new literal in `REASONS`** (`errors.py:REASONS:110-127`, fifteen
  literals, closed) chosen at spec time, and a dedicated `pattern` attribute rather than overloading
  `declared_type`, which `base._note_skip` (`base.py:266-274`) feeds straight back into `_owns`.
- **The consumer audit is still owed** — `AC-2`'s refusal is a breaking change for HAL9000, exocortex
  and orchestrator, all installed with `pip install -e`.
- **CORRECTION to the round-2 hand-back:** it recorded "`AC-3`'s text is fixture-based and, on my
  reading, needs no edit". That is wrong — see new open member 1. `AC-3` joins the re-origination set.

### Questions the next spec round will owe, beyond the blocking ones

Carried from round 2, with one added.

1. **What does the gate do on a dict-shaped write whose declared `type:` is neither `person` nor
   absent** (`type: company`, or a typo)? The signed ACs cover `person` and absent. `lint_vault`
   already answers it by falling through every equality branch (member 9).
2. **How does `lint_vault --fix` (D8) express a delta at all?** The fix loop mutates `fm` in place
   across eight `elif` branches and serializes the whole dict (`scripts/lint_vault.py:876-882`), in
   `scripts/`, outside the package. Both architect rounds price this as the single largest piece of
   unglamorous work; it wants pricing before it is planned.
3. **What happens to `create_stub`'s existing refusal channel** once the same check fires from the
   write path? `NameValidationError` (`name_validation.py:NameValidationError:125`) interpolates the
   offending name and is a bare `ValueError` that `chainable_cause` suppresses (`errors.py:212`).
   Three downstream repositories catch on it.
4. **NEW — does `create_stub` still validate at all, once every door below it does?** Today it is the
   only site carrying the name contract (`person.py:1407`) and it applies Tier-2 repairs whose output
   it stores (`:1413`). If the gate refuses at D3 one frame later, the create path runs the same table
   twice with two different exemption states — `create_stub` with the sentinel honoured, the gate
   without it. Whether `create_stub`'s call is kept, demoted to cleaning-only, or deleted is a spec
   decision that new open member 1 makes load-bearing rather than cosmetic.

## Architectural Review — 2026-08-11 (round 3)

**Recommendation: REVISE — return to exploration**

**Round 3, cold-start re-spawn.** Read in role order: `architect.yaml`, this document in full (five
ac-red-team rounds, the `ac-signoff` fence, both prior architectural reviews, both data audits, all
three spec-writer hand-backs), then the code every premise below turns on (`name_validation.py`,
`writer.py`, `repositories/base.py`, `repositories/company.py`, `repositories/person.py`,
`errors.py`, `scripts/lint_vault.py`), plus `LESSONS.html`. No shell in this cage; the live vault was
not read. Every citation below was re-derived from source this round.

**What moved since round 2, and what this round is for.** The design sections are still unfolded —
`## Intent`, `## Approach`, Finding B, `AC-2`, `AC-4` are byte-unchanged. The only addition is the
round-3 spec-writer hand-back, and it puts one question directly to this gate: its re-entry path now
opens with *"Choose the gate SHAPE first — declare-vs-infer. This is architect work and needs no
vault access. It is unconditional and it bounds everything below."* That is correct, it is mine to
answer, and answering it is the whole value of this round. **The ruling is below and it is the
deliverable**; the REVISE follows from it, because the ruling changes what `AC-1`–`AC-4` must say and
those are signed. I am not re-litigating rounds 1 and 2 — both findings stand, re-derived, and the
sections below say only what is new.

### Trigger check

Three fire, unchanged: a new module (the gate); a contract change crossing into three downstream
repositories installed with `pip install -e` (`docs/backlog-campaign-2026-07-05.md:98`); a
derived-wall enforcement mechanism that must be designed rather than copied.

### RULING — the gate is HANDED its semantic context; it never infers it

This settles the round-2 `#approach` target and the spec-writer's step 1. Stated as one rule:

> **The gate reads only what the write itself carries, plus what the caller declares. It never
> consults the filesystem — no glob, no path shape, no sibling note. A write with no declared type
> gets no type's contract.**

The line is between *the payload* and *the environment*, not between *code* and *inference*. Reading
a field out of the record being written is mechanical and stays in the gate; reconstructing the
entity type from where the file happens to sit is the WI-185 move Finding A already used to reject
`vault_io` as the home — one frame further up, and this document has spent eight gate rounds
demonstrating it a second time.

**Adopt it and eight of the ten arms already carry a declaration, with no caller change at all.**
This is the part the exploration never checked, and it is why the ruling is cheap:

| Arm | Declaration already available at that arm | Read from |
|---|---|---|
| D1a `entity=` | the model itself — `Person.type` is `Literal["person"] = "person"`, emitted unconditionally | `models.py:78`, `writer.py:111` |
| D2 / D3 `save` | `self.type_name` — **abstract** on the base, so every repository has one | `base.py:188-192`; `person.py:232`, `company.py:67` |
| D4 `update_fields` | `self.type_name`, same object, already used at `:430`/`:461` | `base.py:403-430` |
| D5 / D6 `update_frontmatter_field(s)` | the target note's own `type:`, already parsed in-lock one line earlier | `writer.py:329`, `:381` |
| D7 `roundtrip_file` | n/a — introduces nothing, out under the delta rule | `writer.py:419` |
| D8 `lint_vault --fix` | `vf.entity_type`, already computed from `fm.get("type", "")` | `lint_vault.py:140`, `:148` |
| D1b `frontmatter=` | the caller's dict — declared iff it carries `type:` | `writer.py:259` |
| D1c `extra_fields`-only | the caller's dict — declared iff it carries `type:` | `writer.py:263` |

So the undeclared cell is not "every dict-shaped write". It is: **D1b/D1c called without a `type:`
key, and D5/D6/D8 against a note that itself carries none.** Everything the last six gate rounds
fought over lives in that one cell, and `_owns` is not consulted anywhere — which disposes of round
2's blocking issue 1 structurally rather than by picking a better inference. The Company annexation
cannot occur: a company write declares `company` (via `CompanyRepository.type_name`, `company.py:67`,
or via its own `type:` key) and simply is not a person write. Parked defect 3's Person-only scoping
holds by construction instead of by a rule that has to be argued.

**At D8 the ruling also closes the spec-writer's member 9.** Handing the gate `vf.entity_type` makes
it agree with the answer the enclosing repair loop already reached (`lint_vault.py:140`/`:148`,
dispatched by equality at eleven sites) instead of installing a second, contradictory one in the same
call frame. Three dispatch implementations become one, in the place the item's own design was about
to make it three.

**What still has to be decided, and it is exactly one thing.** In the undeclared cell, either
(i) apply only the checks whose justification is **structural** — true of a note of any type written
under the `@{name}.md` convention — and withhold every person-tuned pattern until a type is declared;
or (ii) refuse an undeclared write that introduces a `name:` outright. (i) cannot annex and cannot
brick; (ii) is strictly stronger but its blast radius IS the untyped population. **The partition (i)
needs is decidable from source, not from the vault** — each Tier-1 pattern's own comment states its
evidence, and only two rest on a filesystem property: `_PATH_HOSTILE_RE` ("breaks the `@{name}.md`
file path", `name_validation.py:91-95`, which is Finding F, and `base.py:381` derives that filename
for *every* repository) and `empty` (`:258-259`/`:277-278`, which yields `@.md`). Every other pattern
cites the person-name audit in its own comment — the Maurizio/Francisco analysis at `:48-53`,
calendar/`Me to` prefixes at `:58-73`, `zArchived` `:97-98`, `unknown contact` `:100-101`, `@` "cannot
appear in a human name" `:103-108`. The choice between (i) and (ii) is a blast-radius question and
wants the count; the partition is not.

**Consequence for the required grounding, offered to the data gate rather than over its head.** If
this ruling is adopted, data-audit items 2 and 4-as-stated (the Tier-1 table run over untyped notes)
and item 5 (the same table run per key over the `type: company` corpus) lose their purpose — under a
declare rule no person-tuned pattern ever evaluates a company or an undeclared note, so how it *would*
have scored on them decides nothing. Item 1 survives, as the blast-radius number for the (i)/(ii)
choice; item 3 (re-dating Finding C) survives untouched; the spec-writer's new phone-sentinel count
survives. That is three counts instead of five, and none of them gates the rule's *shape*. The
data-premise gate should re-rule on that — I am not discharging it.

**The sentinel is not a missing input.** The spec-writer reads its member 1 as proof that the settled
signature ("the introduced fields plus the entity type") is one input short. Read from the source it
is not: `create_stub` derives the flag itself, from the payload — `bool(phone) and
name.strip().lstrip("+").isdigit()` (`person.py:1406`) — and at D3 the phone is in the record being
written (`person.py:1450`, `:1456`). So the rule the gate needs is *a pure-digit name is permitted
when the record it is introduced with carries a phone*, computed from what the gate already receives.
That is inside the ruling's line (payload), not outside it (environment), and it needs no new
parameter and no thread through the generic layer. Two consequences the re-origination must state
rather than discover: `pure_digit_name` is therefore **not** unconditional even on a declared-person
write, which is what makes `AC-2` and `AC-3` wrong as signed; and under Finding C's delta rule a
`update_fields(person, {"name": "+447…"})` that introduces the name without the phone is refused,
because the phone is stored, not introduced. Rare, defensible, and it must be written down.

### One new finding, created by this ruling and owed in the same round — `AC-1`

Both prior rounds explicitly held `AC-1`. Under an infer shape it was sound, because the gate took no
type argument and there was nothing for an arm to get wrong. **The declare ruling creates that
surface, so naming it is part of making the ruling responsibly.**

`AC-1(a)/(b)/(c)` resolve WHICH arms call the gate — a floor of ten, driven positive controls, a
near-miss. Nothing in the criterion, or in `AC-2`/`AC-4` which delegate to it, constrains WHAT an arm
passes. A build that wires `gate(introduced_fields)` at all ten arms with the type defaulting to
`None` greens `AC-1` completely: every arm routes, the sweep resolves ten members, the near-miss still
fails. The concrete bypass is at D4, and it is this item's own Example of done:
`update_fields(person, {"name": "Dave/Bob"})` passes a delta that contains no `type:` key — the
declaration lives on the repository (`self.type_name`), not in the introduced fields — so a gate
falling back to reading the type out of the payload puts **every** `update_fields` write into the
undeclared cell permanently, and the name check never fires on the door N2 was raised about.

So the wall has to pin, per arm, that the declaration passed is the one available at that arm (the
model's type at D1a, `self.type_name` at D2/D3/D4, the parsed note's `type:` at D5/D6, `vf.entity_type`
at D8), and that no arm hardcodes a literal. This is the same instrument `AC-1` already specifies, one
argument wider — not a new mechanism.

### Confirmed independently from source — the spec-writer's two new members

Both re-derived this round rather than inherited; both hold, and both are re-origination obligations.

- **`AC-2`/`AC-3` × the phone sentinel.** `validate_strict`/`clean` return the name untouched when
  `allow_phone_sentinel` is set (`name_validation.py:253-254`, `:274-275`); `create_stub` sets it at
  `person.py:1406-1407` and then calls `self.save(person, …)` at `:1475`, which is D3 (and D1a
  beneath it) carrying a `pure_digit_name` (`:373-377`) by design, for the WI-083 path its own
  docstring documents (`person.py:1358-1361`). Under `AC-2` as signed that save is refused, and under
  Finding C's delta rule every *subsequent* entity write for that person is refused too, because an
  entity write's name is always the delta. `AC-3`'s exemption never reaches it. Confirmed.
- **`AC-4` × `aliases[]`.** `_normalize_address_fields` walks `person.aliases` as an identifier INPUT
  and writes it as an output (`person.py:1323-1343`; the extracted address is appended to
  `person.emails` at `:1328`, the display half kept at `:1332`), and `create_stub` seeds
  `aliases=[email]` with a bare address (`person.py:1448`). `AC-4`'s container names `emails[]` and
  `phones[]` only, so a gate that leaves `aliases[]` alone satisfies it while regressing behaviour
  D3 has today. Confirmed.

### Regress signature — named, per LESSONS #38, with an escalation rather than another fold

Twelve gate rounds have run on this document in one day: five ac-red-team, two architect, two
data-premise, three spec-writer. Read as an arc, the ac-red-team five were **entirely** about the
checking machinery — sweep floors, derivation units, exclusion sets, arm-vs-function granularity —
and the last two hand-backs have been sweeping the *generators* of prior findings at successively
higher altitude ("round 2 swept grain and found three members; sweeping extent finds five"). That is
LESSONS #38 (`LESSONS.html:678-687`) in its exact shape, and its scar is this repository: WI-020, 27
rounds, stopped only by Dave issuing a specification-altitude declaration. Its rule is explicit —
when findings shift from the thing to the checking-of-the-thing, **name the signature and escalate for
a human sufficiency/altitude ruling instead of folding again.**

Naming it. Two things follow, and they are the practical output of this round:

1. **The behavioural findings are not part of the regress and must land**: the Company annexation
   (rounds 1–2), the ungrounded population (data), the phone sentinel breaking a shipped feature, the
   `aliases[]` omission, and the `AC-1` declaration gap above. These are "the thing is wrong", every
   one of them is a real vault consequence, and every one is in signed text.
2. **Another gate round buys nothing.** Nothing in this document can move until (a) Dave rules on the
   altitude and re-originates, and (b) someone with a shell runs the three surviving counts. A fourth
   architect spawn, a third data spawn or a fourth spec-writer spawn against an unfolded document will
   reproduce its predecessor — the round-2 data audit said so of itself, and it was right.

### Re-entry path — this ruling's effect on the spec-writer's ordering

Its step 1 is now discharged: the shape is DECLARE. The remaining order, unchanged in substance:
run the three surviving counts (item 1, item 3, the sentinel population) outside the cage; rewrite
Finding B to the ruling above — deleting the untyped-dispatch rule rather than repairing it, and
recording that `_owns` is not consulted at all; specify the Tier-1 refusal surface once (branch-unit
reification, the `empty` refusal outside the chain at `:259`/`:278`, the sentinel exemption inside it,
and the structural/person-tuned partition); then Dave re-originates `AC-1`, `AC-2`, `AC-3`, `AC-4` and
`AC-5` in ONE round; then ac-red-team → architect → data-premise → spec-writer.

### Review

Only what changed. **Fit / Duplication / Reversibility / Generalization / Build vs extend /
Prior art** are as round 2 recorded them and are not re-derived here; Approach F remains the right
approach and every structural citation in Findings A–G re-derives.

**Boundaries:** the ruling is the boundary answer. Six of the ten arms are generic infrastructure
shared by Person, Company, Book and Meeting; the design's original mistake was to make that generic
layer *derive* an entity type it was built never to know. Handing it one instead is the smallest
change that removes the derivation, and the base class already exposes the value
(`type_name`, `base.py:188-192`).

**Determinism boundary (LLM vs code):** n/a for LLMs — but the dimension's underlying principle is
what the ruling turns on. The entity type is mechanically available one frame up at eight of ten arms
and was going to be reconstructed downstream from a glob; that is the same shape as the WI-115 scar
the role instruction records, with a filesystem heuristic standing in for the LLM.

**Cost & maintenance:** unchanged at one to two sessions for the routing, plus the Tier-1 reification
and the `lint_vault --fix` delta threading. The ruling *reduces* cost: no partition research, no
untyped-dispatch rule, two of five vault counts moot, and the D8 dispatch collapses into an existing
value rather than a third implementation.

### Notes (non-blocking)

1. Rounds 1 and 2's notes all stand: the dedicated `pattern` attribute rather than overloading
   `declared_type` (`base.py:267-269` feeds it back into `_owns` — LESSONS #43's shared-field shape);
   the new reason literal, which must be chosen at spec time because `REASONS` is a closed frozenset
   of fifteen (`errors.py:110-127`) and `bounded_message` raises on any non-member (`:139-145`);
   `lint_vault --fix`'s missing delta object; the sibling `save` overrides in `book.py`/`meeting.py`
   that are correctly not arms.
2. **The three-functions-one-shape collapse is newly unblocked.** Round 2 recorded it as blocked by
   `AC-1`'s signed ten-arm floor. `AC-1` is now in the re-origination set anyway (finding above), so
   the sequencing constraint is lifted — collapsing `update_frontmatter_field` /
   `update_frontmatter_fields` / `roundtrip_file` could precede this item and shrink the routing
   surface before it is routed (LESSONS #13). Still a different work item; still not recommending
   absorption. Recording only that the reason it was impossible has gone away.
3. The two round-1 rulings (gate signature; total splitter owning the parens form, `Email.parse` not
   widened) stand, re-checked. The signature ruling is now *reinforced* rather than reopened: the
   spec-writer's "one input short" resolves inside the payload, not by widening the signature.

```verdict
gate: architect
verdict: REVISE
date: 2026-08-11
model: claude-opus-5
targets: #approach, #exploration-notes, AC-1, AC-2, AC-3, AC-4
note: Ruled the open shape question the spec-writer routed here — the gate is HANDED its type and never infers one (8 of 10 arms already carry a declaration: the model at D1a, `self.type_name` at D2/D3/D4, the parsed note at D5/D6, `vf.entity_type` at D8), which deletes the untyped-dispatch rule rather than repairing it, moots two of the five vault counts, and makes the sentinel a payload rule not a new input — and that ruling creates one new defect in signed text: AC-1 proves which arms CALL the gate, never what they PASS, so a type defaulting to None greens all ten arms while every update_fields write (whose delta carries no `type:`) escapes the contract permanently.
```

## Data Audit — 2026-08-11

**Recommendation: REVISE — return to exploration**

**Round 3, cold-start re-spawn.** Read in role order: `data-premise.yaml`, this document in full
(five ac-red-team rounds, the `ac-signoff` fence, all three architectural reviews, both prior data
audits, all three spec-writer hand-backs), then the code every premise below turns on. Same method
bound as every prior round in this cage: **no shell, scope limited to this tree's files, the live
vault was not read.** Every citation below was re-derived from source this round rather than
inherited.

**What this round is for, stated first.** The design sections are still unfolded — `## Intent`,
`## Approach`, Finding B, `AC-2`, `AC-4` are byte-unchanged since the round-1 audit, so the
standing premise finding is unchanged and I do not re-argue it. What is new is that the round-3
architectural review issued the DECLARE ruling and explicitly routed its data consequence back to
this gate: *"data-audit items 2 and 4-as-stated … and item 5 lose their purpose … The data-premise
gate should re-rule on that — I am not discharging it."* That re-ruling is this round's deliverable.
The answer is that the ruling **narrows** those items rather than mooting them, and the narrowed
version is the cheapest count in this document — but it is still a count, and skipping it would
re-derive the annexation defect one level down.

### Trigger check

**Class 1 AND Class 2 — both still fire, but on a smaller rule than in rounds 1–2.**

- Class 1 (data-distribution / field-presence): the undeclared-cell population is still an
  unmeasured existence claim, and it is now the blast-radius number for the architect's one
  remaining open choice ((i) structural-checks-only vs (ii) refuse-undeclared). Finding C's
  legacy-dirt claim is a second Class-1 claim, still two months stale.
- Class 2 (rule-effect-against-existing-corpus): under shape (i) a NEW refusal rule fires on
  undeclared writes, and its correctness depends on what it flags against the corpus as it exists
  today. Twelve gate rounds have reasoned about a refusal rule of some shape; none has executed one.

### The DECLARE ruling re-ruled, from source — the counts narrow, they do not vanish

I verified the ruling's own factual base before ruling on its consequence. Every leg confirms:

| Claim | Read from | Result |
|---|---|---|
| `type_name` is **abstract** on the base, so every repository supplies one | `base.py:188-192` | confirmed |
| `update_fields`' delta (`updates`) carries no `type:` key; the declaration lives on `self.type_name` | `base.py:403-451` — `updates` is the caller's dict, merged into the parsed note at `:451`; `self.type_name` used at `:430`/`:461` | confirmed — the architect's `AC-1` declaration-gap finding holds |
| D5/D6 parse the target note's own frontmatter in-lock, one line before the mutation | `writer.py:329` / `:381` | confirmed |
| D7 `roundtrip_file` introduces nothing | `writer.py:419-424` | confirmed |
| the type vocabulary agrees across the declaration channels | `models.py:TYPE_TO_MODEL:309-318` keys `"person"`/`"company"`; `Person.type` `Literal["person"]` `models.py:78`; `_owns` compares `declared_type == self.type_name` `base.py:261` | confirmed — no string-vocabulary mismatch between the four channels the ruling would draw on |
| `CompanyRepository` still inherits `@{name}.md` | grep `def save` / `filename = ` across `repositories/` → `base.py:381`, `book.py:167`, `meeting.py:189`, `person.py:1255` — **no `company.py` hit** | confirmed |

So the ruling's premise holds, and its structural effect is real: with a declared type at eight of
ten arms and `_owns` never consulted, the Company annexation cannot occur and the person-tuned
patterns never evaluate a company note. **Items 2 and 5 as WRITTEN are therefore correctly moot** —
running the whole ten-refusal table over untyped notes, or per key over the `type: company` corpus,
decides nothing once no person-tuned pattern can reach either population.

**But the ruling relocates the ungrounded premise rather than removing it, and that is this round's
finding.** Under shape (i) the gate still fires on undeclared writes — with the **structural**
subset. The architect classifies that subset from source as exactly two refusals,
`path_hostile_char` (`name_validation.py:352-356`) and `empty` (`:258-259`/`:277-278`), on the
grounds that only these two rest on a filesystem property rather than on the person audit. I read
the module's comments independently and **the classification is right**: every other pattern states
person-scoped evidence in its own comment — the Maurizio/Francisco/Patricio false-positive analysis
at `:48-53`, the calendar/`Me to` prefixes at `:58-73`, `zArchived` at `:97-98`, `unknown contact`
at `:100-101`, `@` "cannot appear in a human name" at `:103-108`, and `pure_digit_name`'s sentinel
exemption at `:110-111`/`:253-254`. The *side* each pattern lands on is decidable from source, as
the architect says.

**What is not decidable from source is whether the structural side is safe on the population it
will now be applied to.** `_PATH_HOSTILE_RE`'s only empirical grounding is its own comment:
*"Verified 2026-06-06: 0 live vault names contain '/'"* (`name_validation.py:94`) — and that zero
comes from the same 2026-06-02 audit of **person** names the module docstring describes
(`:26-28`, 1647 notes / 1590 names; the sibling verifications at `:79` and `:87-88` cite the same
corpus). Under shape (i) that person-scoped zero is carried across an entity boundary to license a
refusal on undeclared writes, which by construction include company-shaped notes. That is the
identical generator that produced the annexation — a number measured on persons, reused where the
population is not persons — one level down and two patterns wide instead of ten. The document's own
`booking.com` specimen is the proof that this generator's output survives careful reading; a
slash-bearing legitimate organisation name (`AC/DC`, `S/4HANA`, a `Bausch/Lomb`-shaped merger form)
is the same shape on the pattern the ruling keeps.

**One consequence worth recording alongside it, because the same query answers both.** The DECLARE
ruling scopes the gate to declared-person writes plus the undeclared cell, so
`CompanyRepository.save(Company(name="Bausch/Lomb"))` — which reaches `filename = f"@{name}.md"`
(`base.py:381`, inherited, no override in `company.py`) and then `vault_io.ensure_dir` — still
creates a spurious `@Bausch/` directory. Finding F's defect is entity-agnostic; the fix, correctly,
is not. That is WI-022's to close and I am not scoping it in — but the count of company names
containing `/` is the same number item 5′ below asks for, so it is free.

### Required grounding — re-ruled, three counts and one narrowed fifth

Items 1 and 3 are carried unchanged from round 1 and remain unrun. Items 2 and 5 are **withdrawn as
written** and replaced by the narrowed 5′. The spec-writer's sentinel count is adopted. All of these
still need a shell and vault access **outside this cage**.

1. **Count the undeclared cell.** Over `<vault>/@*.md`: how many notes lack a `type:` key, and of
   those how many are companies, persons, neither. Under DECLARE this is no longer a rule-choice
   number — it is the blast-radius number that decides the architect's open (i)/(ii) choice, and it
   is the consumer-audit number, since it sizes how many live writes start refusing.
2. ~~Run the Tier-1 table over untyped notes' stored `name:`~~ — **withdrawn.** Moot under DECLARE:
   no person-tuned pattern reaches an undeclared write.
3. **Re-ground Finding C's premise** — the current, dated count of Tier-1-dirty stored names. If it
   is zero, say so and keep the delta rule on its design argument, which four gate rounds have held.
4. **Carry the counts into the fold** — state whichever rule the undeclared cell is given alongside
   the number it was chosen against, so build-start re-grounding has something to detect rot in.
5. ~~Run the whole Tier-1 table per key over the `type: company` corpus~~ — **withdrawn**, replaced
   by **5′ — run the STRUCTURAL subset only (`path_hostile_char`, `empty`) over every NON-person
   name in the vault**: the `type: company` corpus plus the undeclared cell from item 1. Two
   patterns, not ten, over a corpus item 1 already enumerates. This is the predicate that decides
   whether shape (i) is safe, and it is the one that re-dates `_PATH_HOSTILE_RE`'s person-scoped
   `0` against the population it is about to be applied to.
6. **Count the live phone-sentinel population** — notes whose stored `name:` matches `^\+?\d+$`
   (`name_validation.py:111`). Adopted from the round-3 hand-back; it is the population `AC-2`/`AC-3`
   as signed make unwritable, and the number the payload-derived sentinel rule
   (`person.py:1406`) must be justified against.

### Conclusion

The DECLARE ruling is a genuine improvement to the data position and I confirm its factual base from
source: the type vocabulary agrees across all four declaration channels, eight of ten arms carry a
declaration already, and `_owns` drops out entirely. Two of the five counts really are moot. But the
item's central data premise is not yet grounded — it has moved, from "an untyped `@*.md` note is a
person note" to "the two structural Tier-1 refusals are safe on non-person names", and the only
evidence for the new one is a zero measured on 1590 person names in June. That is the same generator
at a smaller scale, and it is cheap to close: two patterns over a corpus item 1 already walks.

`AC-2` and `AC-4` remain signed around the superseded rule, so nothing can be folded downstream; rule
D3 refuses `→ specced` on this verdict regardless. Stage stays at `exploring`.

**Signal for the factory, stated because the targets line alone cannot carry it.** This is the third
data-premise round and it names the same two ACs as the first two — but it is not a treadmill round
in the sense the arc test is asking about, and the distinction matters here. Rounds 1 and 2 targeted
`AC-2`/`AC-4` because the document had not moved; this round targets them because the architect's
round-3 ruling moved the *design* out from under them, which is progress, not repetition — the
required grounding shrank from five counts to four, one of them narrowed from ten patterns to two.
What has NOT changed is that no further gate spawn can advance this item: the round-3 architectural
review has already named the LESSONS #38 regress signature and escalated for Dave's altitude ruling
and re-origination, and every count above needs a shell this cage does not have. A fourth spec-writer,
architect or data-premise spawn against an unfolded document will reproduce its predecessor. The two
things that unblock this item are both outside the cage: **Dave re-originates the signed set, and
someone with vault access runs items 1, 3, 5′ and 6.**

```verdict
gate: data-premise
verdict: REVISE
date: 2026-08-11
model: claude-opus-5
targets: AC-2, AC-4, #exploration-notes, #approach
note: Re-ruled the grounding list the round-3 DECLARE ruling routed here — confirmed from source that it moots items 2 and 5 (no person-tuned pattern can reach a company or undeclared write; type vocabulary agrees across all four declaration channels; `_owns` drops out), but it RELOCATES the ungrounded premise rather than removing it: under shape (i) the structural subset (`path_hostile_char`, `empty`) now fires on undeclared writes, and its only evidence is `_PATH_HOSTILE_RE`'s person-scoped "0 of 1590" from 2026-06-06 (name_validation.py:94, corpus at :26-28) — the same person-number-across-an-entity-boundary generator that produced the annexation, two patterns wide instead of ten; four counts still owed and still unrunnable in this cage.
```


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
name-identity rule). They size blast radius and they give build-start re-grounding something that
detects rot. *(Round-8 note, so the list is not misread as growing under a decision: G4 is added this
round and it is a SIZING query for a choice already made in the fold, not an input to it — the round-7
data audit's own reading is that the chosen shape (b′) has a zero live blast radius on the population
G4 counts, and the shapes it would have priced are the two the fold rejected.)*

| # | Query | Owed to | What it decides |
|---|---|---|---|
| **G1** | **Rule (ii)'s undeclared population, at the rule's own scope.** Over EVERY `.md` file in the vault (not `rglob("@*.md")`): classify as (a) frontmatter carrying `type:` → declared; (b) frontmatter, no `type:` → undeclared; (c) no frontmatter fence → undeclared. Report `\|b\|` and `\|c\|` **separately**, each split by path class (under `@*.md` / under `_merged_dupes/` or `_quarantine/` / neither). Predicate stated in Finding B. | data-premise round 4, Finding 1; supersedes round-1 item 1 and item 4's `@*.md` phrasing | Nothing about the rule's direction — (ii) is fail-closed, so a larger population is stricter, not wronger. It sizes the target set the consumer audit then intersects, and it is the number build-start re-grounding re-runs. |
| **G2** | **Finding D reconciliation 2, four cells plus the case cell — reported PER FIELD, plus one deletion column.** Over every stored `emails[]`/`aliases[]` entry, evaluate BOTH `_extract_email_and_name` (`person.py:1286-1298`) and `Email.parse` (`identifier.py:134-160`); report *agree* / *extracted-but-refused* / *not-extracted-but-parsed* / *neither*, plus, within *agree*, how many differ only by CASE. Counts and a sample per cell, **with every cell reported separately for `emails[]` and for `aliases[]`** *(amended round-6 fold, per data-premise round 5)*. **And within the `emails[]` *extracted* cell, how many entries have a non-empty display half whose value is NOT already present in that same note's `aliases[]`** *(amended round-7 fold, per data-premise round 6)*. | data-premise round 4 Finding 2(a); per-field split, data-premise round 5; deletion column, data-premise round 6 | Three things, one pass. The `emails[]` half: whether the splitter consolidation is a refactor or a behaviour change, and how large — non-empty cells 2–3 are a list the spec owes, and a non-empty case cell forces the splitter's return contract to be stated (raw slice vs `Email.parse(...).value`). The `aliases[]` half: the *extracted* cell IS the address-bearing-alias population, which is what Finding I's arm-shape split forks and what `AC-4`'s scoped clause is signed against. **The deletion column:** the dict-arm rule stores the bare address and drops the display half with no destination, and an entry whose display half is already in `aliases[]` loses nothing — so this intersection, not the extracted cell, is the population the fix DELETES, and it is the number `AC-4`'s dict-side clause and `### Examples of done` scenario 3's (a)/(b) choice must be signed against. |
| **G4** | **The Tier-2 / path-divergence population, two columns** *(new, round-8 fold, per data-premise round 7)*. Over every live `@*.md` note with parseable frontmatter — the same corpus and the same walk count 3 already did — report: **(a)** how many stored `name:` values are Tier-1-CLEAN (`validate_strict` does not raise) but Tier-2-DIRTY (`validate_strict(name) != name`, i.e. a strip or a `\s{2,}` collapse fires), with a sample and a breakdown by which repair fires; and **(b)** how many notes have a filename stem (`path.stem.lstrip("@")`) that differs from the stored `name:` value. | data-premise round 7 | **Neither column gates the chosen shape** — the round-8 fold takes (b′), whose live blast radius on column (a) is zero by construction, so this is booked for the same reason G1 is: it sizes, it does not decide. **(a)** is the population (b′) declines to repair — the notes that keep a Tier-2-dirty stored name on every non-`create_stub` path — and it is the number a future rename-the-file item (parked defect 1) would be scoped against; it is ALSO the number that would have priced (a′)/(c′), so recording it keeps the rejected shapes falsifiable rather than merely rejected. **(b)** is the population where path and field have ALREADY diverged, which forks on its next `save` under every shape including (b′), because this item does not rename files; it is parked defect 1's standing size. Count 3 cannot bound either: Tier 1 RAISES and Tier 2 REWRITES with `_raise_on_tier1` between them (`name_validation.py:288-295`), so every Tier-2-dirty name sits inside count 3's clean 3,339 by construction. **Cheap:** one extra string comparison and one `path.stem` read on a walk already performed once, with no new corpus and no new parsing. |
| ~~G3~~ | ~~Stored `phones[]` entries normalizing to fewer than seven digits (`identifier.py:228`)~~ | data-premise round 4, Finding 2(b) | **MOOT — the condition it was conditional on did not occur.** The audit scoped it *"conditional on the architect's phone-authority ruling — if the gate is to delegate to `Phone.parse`"*. Round 5 chose the relocation shape instead, so `MIN_DIGITS` never enters the dedupe path and there is no refusal to size (Finding G). Withdrawn on the same terms it was raised. |

**Also owed and NOT a vault query — the consumer audit**, carried unchanged from Constraints and
sharpened by G1. `AC-2`'s refusal is a breaking change for HAL9000, exocortex and orchestrator, all
installed with `pip install -e` (`docs/backlog-campaign-2026-07-05.md:98`). Two greps, in the shape
WI-024 used: non-`create_stub` write callers across all three repos, and — new, per the round-5
Finding G resolution — any importer of `obsidian_schemas.repositories.person.normalize_phone` /
`phones_match`, which the compat re-export is there to keep working and which the audit should
confirm rather than assume. G1 bounds the notes; this bounds the callers; the live blast radius is
their intersection, and neither half bounds it alone.

## Spec-Writer Fold — 2026-08-11 (round 4)

**This round PRODUCED the fold. It is not a fourth hand-back.** Rounds 1–3 handed back because the
two things the item needed were both outside the cage: Dave's rulings and a shell with vault access.
`## Conductor Rulings & Grounding` supplies both, so the exploration work those rounds could not do
is done here, and the conductor's own re-entry line names it as this round's deliverable — *"the
spec-writer rewrites Finding B to the DECLARE ruling stating the counts above"*.

Cold-start, read in role order: `spec-writer.yaml`, this document in full (five ac-red-team rounds,
the `ac-signoff` fence, all three architectural reviews, all three data audits, all three prior
hand-backs, the conductor rulings), the project `CLAUDE.md`, then the code every claim below turns
on. Every citation was re-derived from source this round, not inherited: `name_validation.py`
(module docstring, the Tier-1 constants, `validate_strict`, `clean`, `_raise_on_tier1`),
`repositories/base.py` (`type_name`, `file_pattern`, `_owns`, `save`, `update_fields`),
`repositories/person.py` (`_writeback_identifier`, `_extract_email_and_name`,
`_normalize_address_fields`, `create_stub`), `repositories/company.py`, `writer.py`
(`model_to_frontmatter`, `write_markdown_file`, both `update_frontmatter_*`, `roundtrip_file`),
`models.py`, `errors.py` (`REASONS`, `bounded_message`), `scripts/lint_vault.py`. This cage has no
shell and its scope bound is this tree's files only; the live vault was not read — the counts used
below are the conductor's, cited as such.

### What this round wrote

| Section | Change |
|---|---|
| **Finding B** | Rewritten to the DECLARE ruling. The `_owns`-derived untyped-dispatch rule is DELETED, not repaired. Adds the per-arm declaration table (8 of 10 arms already carry one), names the undeclared cell exactly, records rule (ii) with the count it was chosen against (0 of 3,418), and states the per-arm *what-is-passed* obligation. The ten-arm door set and the arm table are unchanged. |
| **Finding B — D8** | **New finding, from source:** the D8 arm cannot serialize an undeclared note at all (`lint_vault.py:318-326` classifies it `missing_type`/ERROR and `continue`s; `auto_fixable` defaults `False` at `:83`; `apply_fixes` collects only auto-fixable issues at `:810`). This discharges re-entry step 3's member-9 check and independently corroborates ruling 2 from the tree. |
| **Finding C** | Re-dated against the conductor's count 3. The legacy-dirt premise is now historical (79 total, 2 live, both intentional sentinel stubs); the delta rule is kept, explicitly on its design argument, with both legs that never depended on the count re-derived. |
| **Finding H (new)** | The Tier-1 refusal surface specified ONCE, as re-entry step 4 asks: branch-unit reification (9 branches / 7 keys), the `empty` refusal outside the chain, the sentinel exemption above it, the payload-derived sentinel rule and its three stated consequences, and the cancellation of the partition under rule (ii). |
| **Finding I (new)** | The identifier container is three fields — `aliases[]` is both an identifier input and an output in the code being replaced. |
| **`## Approach`** | Rewritten to the DECLARE shape and rule (ii); door count corrected to ten arms; the reification, the third identifier field, the per-arm declaration pin, the dedicated `pattern` attribute and the `REASONS` obligation all folded in. |
| **"Where this goes next"** | Its three open questions are marked answered, with the answers and where they live. Its second half (the derived-wall obligations) is unchanged and still owed. |
| **Constraints — Effort** | Corrected to ten arms and given the two pieces the gate rounds added and priced. |

### What this round deliberately did NOT write, and why

**No Design, Edge Cases, Implementation Plan, Write Targets, Verification, or `criteria` refinement.**
Not a judgement call a fresh spawn could make differently:

1. **`AC-1`–`AC-5` are inside the `ac-signoff` hash span** (`ac_hash: a76ebad54da2`) and five of them
   are named wrong-on-facts by gates whose findings Dave has accepted. WI-061 is explicit: refine a
   signed AC within the spirit of the original, but where an original proves wrong, **escalate and
   let Dave re-originate**. The brief below is that escalation, in the shape that lets it happen in
   ONE round.
2. **The plan and the criteria are the same object.** Every task's verify text points at a check an
   AC names; writing them against criteria that are about to be re-originated produces a plan that
   must be rewritten, and a reviewer comparing the two would be comparing a spec to a stale set.
3. **The conveyor refuses the transition regardless.** Rule D3 refuses `→ specced` without a
   data-premise PROMOTE, and the standing data-premise verdict is REVISE. The gate sequence
   `ac-red-team → architect → data-premise → spec-writer` has to run on the re-originated set first.

So the ordering is unchanged from the conductor's re-entry line, and this round moved it forward by
exactly one step. **Nothing else in the item is blocked**: the carried-forward list below is complete
and verified, so the later spec round is assembly.

### Class-shaped fold — declared, and bounded by ruling 3

Per WI-226 the fold closes the CLASS, not the instance. The class both reviewing gates converged on
was named in the round-2 hand-back: *a predicate is adopted from an existing site together with its
calibration, but that calibration was set by the consequence of being wrong at the ORIGINAL site,
and the new site's consequence is different.* The DECLARE ruling closes the whole class in one move
rather than member by member — it removes the *borrowing* entirely at the arms that were doing it:
`_owns` is not consulted (member 1), `_RFC2822_LEAK_RE` never sees a non-person name (member 3),
`lint_vault`'s dispatch becomes the value the gate is handed rather than a competitor to it
(member 9), and the `declared_type` overload is replaced by a dedicated `pattern` attribute
(member 5). Members 2, 4, 6, 7 were already closed and 8 correctly declined.

**Sweeping the next level and declaring what it found, as the rule requires:** the remaining
dimensions of that class are *the population a predicate was tuned on*, *the cost of a false
positive*, *the unit it was written at*, and *how many consumers decode its value*. Under DECLARE the
first collapses (no predicate evaluates a population it was not tuned on), the second is bounded by
the delta rule, the third is pinned by AC-1's arm granularity, and the fourth by the dedicated
attribute. I find no further open member.

**And here the sweep STOPS, on Dave's authority rather than on mine.** Ruling 3 is the LESSONS #38
altitude declaration the round-3 architectural review escalated for: the AC checking machinery is
sufficiently specified, the re-origination fixes named defects only, and further
checking-of-the-checking findings do not block. This section therefore does not open the next rung
of the ladder, and the two findings that would have sat on it are recorded in tier C below rather
than acted on.

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
  `type:` at D5/D6; `vf.entity_type` at D8), **and where none is available that is EXPRESSED rather
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
    arms**; entity-shaped writes are gated at D1a, which is upstream of `vault_io.ensure_dir`
    (`writer.py:273` vs the convergence at `:266`), so Finding F's no-stray-directory promise is
    unaffected;
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
- **Class 2's pass-throughs cannot introduce a name or an address** — including
  `scripts/migrate_person_to_discuss.py`, which re-emits the frontmatter string verbatim (`:81`,
  `:103`, `:109`) and is correctly not an arm.
- **`REASONS` is a closed frozenset of fifteen** (`errors.py:110-127`) and `bounded_message` raises on
  any non-member (`:139-145`), so the refusal's new reason literal is chosen at SPEC time. The error
  carries the pattern key on a dedicated `pattern` attribute, never in `declared_type`, which
  `base._note_skip` feeds straight back into `_owns` (`base.py:266-274`).
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
- **The consumer audit is still owed** and is the largest unstarted piece: the refusal is a breaking
  change for HAL9000, exocortex and orchestrator, all installed with `pip install -e`
  (`docs/backlog-campaign-2026-07-05.md:98`). Rule (ii) sharpens it rather than enlarging it — the
  `@*.md` undeclared population is 0, so the live blast radius is dominated by the *declared*-person
  writes that introduce a Tier-1-dirty name, which is a behaviour those callers should not have.
  *(Round-5 correction: "0" bounds the `@*.md` subset only — rule (ii)'s surface is path-agnostic, so
  the audit's target set is query G1's, not count 1's. See `## Grounding Still Owed`.)*

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
   threading is not.
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

## Architectural Review — 2026-08-11 (round 4)

**Recommendation: REVISE — return to exploration**

**Round 4, cold-start re-spawn — the first spawn against a FOLDED document.** Read in role order:
`architect.yaml`, this document in full (five ac-red-team rounds, the `ac-signoff` fence, three prior
architectural reviews, three data audits, three spec-writer hand-backs, `## Conductor Rulings &
Grounding`, and the round-4 spec-writer fold), then the code every new claim turns on (`writer.py`,
`repositories/base.py`, `repositories/person.py`, `repositories/company.py`, `identifier.py`,
`name_validation.py`, `models.py`, `scripts/lint_vault.py`), plus `LESSONS.html`. No shell in this
cage; the live vault was not read — the counts used below are the conductor's, cited as such.

**What moved, and what this round is for.** Rounds 2 and 3 were the same document re-attacked. This
one is not: Dave's three rulings landed, and the fold implemented them — Finding B rewritten to
DECLARE with the `_owns` rule DELETED rather than repaired, Findings H and I new, `## Approach`
rewritten, the re-origination brief staged for one round. **My round-3 ruling is implemented
faithfully, and every new claim the fold makes re-derives from source — I checked each one rather
than accepting the fold's account of itself** (table below). Rounds 1 and 2's blocking issues are
genuinely dissolved, not argued away. The blocking issue here is new, it sits in UNSIGNED text, and
it is the one part of this design nobody has yet asked the duplication question about.

### Trigger check

Three fire, unchanged: a new module (the gate); a contract change crossing into three downstream
repositories installed with `pip install -e` (`docs/backlog-campaign-2026-07-05.md:98`); a
derived-wall enforcement mechanism that must be designed rather than copied.

### Verified from source — the fold's new claims hold

Re-derived this round, not inherited. All confirm.

| Claim the fold makes | Where I read it | Result |
|---|---|---|
| The D8 arm cannot serialize an undeclared note at all | `lint_vault.py:318-326` (`missing_type` ERROR then `continue`), `auto_fixable` defaults `False` at `:83`, `apply_fixes` collects only auto-fixable at `:810`; and I checked the two OTHER auto-fixable branches that reach the whole-`fm` write at `:876-882` — `person_missing_name` is gated on `vf.entity_type == "person"` (`:374`) and `meeting_missing_from_timeline` targets `idx["persons"]`, built only from `entity_type == "person"` (`:186-187`) | **confirmed, and stronger than stated** — the two fix branches that set `changed` are both person-typed by construction; `broken_wikilink` never sets `changed` |
| 8 of 10 arms already carry a declaration | `models.py:78` (`type: Literal["person"] = "person"`) with `writer.py:111` emitting every declared field and `:127` guarding the `extra_fields` merge; `base.py:188-192` (`type_name` abstract), `company.py:67-68`; `writer.py:329`/`:381` (note's own `type:`, parsed in-lock); `lint_vault.py:140`/`:148` | confirmed |
| `update_fields`' delta carries no `type:`, so AC-1's pass-what pin is required | `base.py:403-451` — `updates` is the caller's dict, merged at `:451`; `self.type_name` at `:430`/`:461` | confirmed |
| The sentinel is payload-derived, not a new gate input | `person.py:1406` (`bool(phone) and name.strip().lstrip("+").isdigit()`), passed `:1407`, `save` at `:1475`; the phone is in the record at `:1450`/`:1456` | confirmed |
| Finding H's surface: ten refusals over ten branch-sites, one exemption above them | `name_validation.py` — nine branches at `:310`, `:320`, `:329`, `:336`, `:343`, `:352`, `:359`, `:366`, `:373` raising seven keys; `empty` at `:259`/`:278`; sentinel exemption at `:253-254`/`:274-275`; `_PURE_DIGIT_RE` is `^\+?\d+$` (`:111`) so the exemption cannot swallow an empty name | confirmed, including the ordering argument |
| Finding I: `aliases[]` is both identifier input and output | `person.py:1323-1329` (address extracted OUT, appended to `emails`), `:1331-1333` and `:1339-1343` (display halves back IN), seeded at `:1448` | confirmed |
| Three fm-building arms converging on one `write_frontmatter` | `writer.py:256-257` / `:258-261` / `:262-263` → `:266` | confirmed |

Rounds 1 and 2's blocking issues are dissolved by the ruling, not deferred: `_owns` is consulted
nowhere, a company write declares `company` (`company.py:67`), and no person-tuned pattern can reach
a non-person record. Parked defect 3's Person-only scoping now holds by construction.

### Blocking issue — the leaf gate cannot reach the phone authority `## Approach` commits to

`## Approach` places the gate in "a module of its own next to `errors.py`" — a leaf, which my round-1
signature ruling justified — and commits it to phone behaviour: *"Phones dedupe on `normalize_phone`'s
output while storing the display form."* Finding G is where that scope-in was made. Read against the
module graph, a leaf cannot do it:

- `normalize_phone` and `phones_match` are module-level functions in **`repositories/person.py`**
  (`person.py:129`, `:148`) — inside the repository layer, not in a leaf.
- `repositories/person.py` imports `.base` (`person.py:78`); `repositories/base.py` imports
  `..writer` (`base.py:19`); and `writer.py` is where six of the ten arms live (D1a/D1b/D1c, D5, D6,
  D7), so `writer.py` must import the gate.
- So a gate that names `normalize_phone` at module scope closes the cycle
  `writer.py → gate → repositories/person.py → repositories/base.py → writer.py`, and
  `obsidian_schemas/__init__.py` imports both ends (`:40`, `:72`), so it fails at package load.

**This is the second recurrence of the same constraint, and the tree already records the first.**
`Phone.parse` reaches for the same symbol behind a deferred import, with the reason written in the
source: *"Lazy import: keeps the canonical normalizer single-sourced without a module-load circular
import once person.py imports the engine"* (`identifier.py:234-236`). `identifier.py` is otherwise a
pure leaf — stdlib only (`:31-36`). My role's prior-art dimension is explicit that a 2nd recurrence
makes the FRAME the suspect rather than the workaround: the frame here is that the canonical phone
normalizer is stranded inside the repository layer while two lower layers need it. A third workaround
is interest, not principal (LESSONS #13) — and unlike the three-functions collapse in note 2 below,
this one is not a separable follow-on, because this item is what forces the second reach.

**The obvious substitute is not free, and the doc does not record its cost.** Using
`identifier.Phone.parse` instead — the authority AC-5's sibling argument would point at — imports a
refusal the dedupe path does not have today: `MIN_DIGITS = 7` (`identifier.py:228`) raises
`IdentifierError` on anything shorter (`:238-239`), where `normalize_phone` returns the digits
(`person.py:138-145`). That is a behaviour change on live data of exactly the shape Finding D's
reconciliation 2 was careful to book on the address side, and nothing in this document books it on
the phone side.

**Why this is architectural and not a spec detail.** Finding D asked "where does this job live, and
is there a second authority" for RFC 2822 splitting, and the answer became AC-5. The identical
question was never asked for phones, even though Finding G scoped phones IN and the Approach names
the symbol. The answer determines the new module's position in the import graph and, if it is
*"move `normalize_phone` to a leaf"*, changes where a public module-level symbol lives — which is a
consumer-visible move. One narrowing that makes it cheaper than it looks, from source:
`normalize_phone` is **not** re-exported at top level — `obsidian_schemas/__init__.py` pulls only the
repository classes from the package (`repositories/__init__.py:8-12`) — so a consumer reaching it
must name `obsidian_schemas.repositories.person`, which is a grep the consumer audit already owes.

**What has to change, in the exploration first:** Finding G and `## Approach` must name where the
phone normalization authority lives once a leaf gate needs it, and state the delta that choice
carries. Three shapes, offered as direction rather than design: move `normalize_phone`/`phones_match`
to a leaf (`identifier.py` already holds `Phone`, and it would delete the lazy import at `:236` —
the only option that pays principal); have the gate delegate to `Phone.parse` and record the
`MIN_DIGITS` refusal as a stated behaviour change; or a second deferred import inside the gate, which
works and is the one I would not take without saying why. **If the second is chosen, `AC-4` acquires
a refusal case it does not currently describe and joins the re-origination set** — flagged here, not
in the targets line, because it is conditional on a choice not yet made, and because Dave's one round
should absorb it if it materialises rather than discovering it after the re-sign.

### Rulings carried forward — settled, do not re-derive

Rounds 1–3's rulings all stand and were re-checked against the code this round: the gate signature
(no `existing` parameter, one entry point taking the introduced fields plus the entity type, entity
arms projecting through `model_to_frontmatter`, `writer.py:88-130`); the TOTAL splitter owning the
parens form before delegating, with `Email.parse`'s angle-bracket gate NOT widened
(`identifier.py:145-149`); and the DECLARE ruling, now adopted by Dave and folded. Nothing above
reopens any of them — the finding is about which module a symbol lives in, not about what the gate
receives.

### Review — only what changed

**Fit / Reversibility / Generalization / Prior art:** as rounds 2 and 3 recorded them. Approach F
remains right, `tests/test_write_routing.py:1-18` remains the precedent AC-1's battery copies, and no
cited execution is owed.

**Duplication:** this is where the blocking issue lives, and it is the dimension the document applied
rigorously to one half of its own scope and not at all to the other. Finding D's audit is honest and
self-limiting about addresses; phones got a scope-in (Finding G) and a storage constraint, but never
the "is there a second authority, and where does it live" question. `Phone.parse` delegating to
`normalize_phone` across a layer boundary via a deferred import is the tree telling you the answer is
already unsettled.

**Boundaries:** the DECLARE ruling fixed the boundary problem rounds 1–3 were about — the generic
layer no longer derives an entity type it was built never to know. The residual boundary cost is
narrower and acceptable: `writer.py` and `base.py` gain a dependency on a gate module that dispatches
on a type string, with the person rules inside the gate rather than in the writer. That is the right
place for them. The phone finding is the one edge of that graph the design has not drawn.

**Determinism boundary (LLM vs code):** n/a for LLMs; the item is the opposite move throughout.

**Cost & maintenance:** unchanged at one to two sessions plus the Tier-1 reification and the D8 delta
threading. The fold's D8 finding genuinely reduces cost — an undeclared note cannot reach that arm,
so the undeclared case needs no D8 fixture.

**Build vs extend vs integrate:** extend, correctly — with the caveat that "extend" here may require
one symbol to MOVE before it can be extended from, which is the blocking issue.

### Notes (non-blocking)

1. **The document is currently buildable two ways, and that is Dave's to close, not mine.**
   `## Approach` says an undeclared write is refused; `AC-2`/`AC-4` as signed say an untyped dict is
   "gated exactly as a `type: person` one is". The fold names this itself in Tier A of the
   re-origination brief and correctly declines to fix signed text. I am not re-raising it as a
   finding — recording it so the next reader does not mistake my PROMOTE-adjacent language about the
   design for a statement that the document as a whole is coherent today. It is not, and it becomes
   so at Dave's re-origination.
2. **A wording edge in the Tier B `AC-1` addendum, which is mine to have caused.** My round-3 text
   asks the wall to pin that "no arm hardcodes a literal or defaults it" — but two arms legitimately
   have no declaration to pass: `roundtrip_file` (D7), which parses a note it does not judge
   (`writer.py:419`), and D1b/D1c when the caller's dict genuinely carries no `type:`, which is the
   undeclared cell rule (ii) exists for. The pin should read *the declaration passed is the one
   available at that arm, and where none is available that is expressed rather than defaulted*.
   Non-blocking and NOT a REVISE target, per Dave's ruling 3 — this is checking-of-the-checking, and
   the altitude declaration says such findings do not block. Fold it into the same re-origination
   text if it is free; do not open a round for it.
3. **One scope note for the data-premise gate, offered rather than ruled.** Count 1 (0 of 3,418) was
   measured over `@*.md`. Rule (ii)'s surface is not path-scoped: `update_frontmatter_field(s)` (D5/D6)
   and `write_markdown_file`'s dict arms (D1b/D1c) take any path, so an untyped non-`@` note that
   receives a `name:` key through them is refused under rule (ii) and is outside what the count
   bounds. I think the exposure is small and it is inside the consumer audit already owed, but the
   number as stated does not bound the rule as written, and that gate owns the call.
4. **At D1b the gate must read the POST-merge dict.** Finding B's table cites `writer.py:259`
   (`frontmatter.copy()`) for that arm's declaration, but `extra_fields` overrides it one line later
   (`:260-261`), so a caller passing `frontmatter={"name": …}` with `extra_fields={"type": "person"}`
   is DECLARED and must not be refused. Reading `fm` at the convergence point rather than the
   parameter resolves it; worth one sentence in the spec so the build does not read the citation as
   the instruction.
5. **Rounds 1–3's standing notes all carry:** the dedicated `pattern` attribute rather than
   overloading `declared_type` (`base.py:267-269`); the new `REASONS` literal chosen at spec time
   (`errors.py:110-127`); the `lint_vault --fix` delta threading; the `book.py`/`meeting.py` `save`
   overrides that are correctly not arms; and the three-functions-one-shape collapse, still a
   separate work item and still not recommended for absorption.

```verdict
gate: architect
verdict: REVISE
date: 2026-08-11
model: claude-opus-5
targets: #approach, #exploration-notes
note: The fold is faithful and every new claim re-derives from source (D8 cannot serialize an undeclared note — confirmed twice over via the person-gated fix branches; 8 of 10 arms carry a declaration; the sentinel is payload-derived) — but the leaf gate `## Approach` commits to cannot reach the phone authority it names: `normalize_phone` lives in repositories/person.py:129, so writer.py→gate→person.py→base.py→writer.py closes a module-load cycle, which identifier.py:234-236 already dodges once by deferred-importing the same symbol (2nd recurrence — the frame is the suspect), and the obvious substitute `Phone.parse` silently adds a MIN_DIGITS=7 refusal (identifier.py:228, :238-239) this document books nowhere.
```

## Data Audit — 2026-08-11

**Recommendation: REVISE — return to exploration**

**Round 4, cold-start re-spawn — the first data round against a FOLDED document with real counts in
it.** Read in role order: `data-premise.yaml`, this document in full (five ac-red-team rounds, the
`ac-signoff` fence, four architectural reviews, three prior data audits, three spec-writer
hand-backs, `## Conductor Rulings & Grounding`, the round-4 spec-writer fold and the
re-origination brief), then the code every premise below turns on. Same method bound as every prior
round in this cage: **no shell, scope limited to this tree's files, the live vault was not read** —
the counts used below are the conductor's, cited as such. Every citation was re-derived from source
this round rather than inherited.

**What moved, and what this round is for.** Rounds 1–3 audited an unfolded document and said the
same thing three times because it could not move. It has now moved twice over: Dave's three rulings
landed, the conductor ran three counts against the live vault with the method stated, and the fold
rewrote Finding B to DECLARE + rule (ii), re-dated Finding C against count 3, and added Findings H
and I. **My round-3 finding is closed** — see the withdrawal below — and the fold explicitly routed
its discharge back here rather than declaring it over my head ("offered to the data-premise gate to
re-rule on"), which is the right handling and is why this round is a narrow one. What survives is
smaller, different, and cheap: the number rule (ii) is pinned to does not bound the rule as written,
and two behaviour deltas this document books as owed on live data have never been given a number.

### Trigger check

**Class 1 AND Class 2 — both still fire, on a materially smaller rule than in rounds 1–3.**

- Class 1 (data-distribution / field-presence): rule (ii)'s justification is an existence claim about
  the live undeclared population, and that population is now measured over a *proper subset* of the
  rule's surface (below). Finding D's reconciliation 2 and the phone-authority substitution are two
  further quantified claims about live entries, both unmeasured.
- Class 2 (rule-effect-against-existing-corpus): rule (ii) is a new refusal rule, and what it refuses
  when run against the corpus as it exists today is still only partially known — known for `@*.md`
  (count 1), unknown everywhere else the rule reaches.

### What is now GROUNDED — three premises discharged, and one of my own findings withdrawn

Read against `## Conductor Rulings & Grounding` and re-checked against the code the counts were run
with:

| Premise | Grounding | Status |
|---|---|---|
| Finding C — "legacy-dirty stored names exist, so whole-record validation would brick the vault" | count 3, 2026-08-11: 79 Tier-1-dirty stored names total, **2 live**, both pure-digit WI-083 sentinel stubs; 77 in `_merged_dupes/` (61) and `_quarantine/` (16) | **DISCHARGED and correctly re-dated.** The fold does exactly what audit item 3 asked: it retires the count as an empirical argument and keeps the delta rule on its two design legs (repair tools are refused by a preserve-judging gate; the delta only exists one frame above the seam). Both legs re-derive — `base.py:437` pre-merge, `writer.py:329`, `:381`. |
| The phone-sentinel exemption's population | sentinel count, 2026-08-11: **3** (2 live stubs, 1 quarantined) | **DISCHARGED.** Small, real, dated, and it is the number Finding H's payload-derived rule and the `AC-2`/`AC-3` re-origination are justified against. |
| Rule (ii)'s undeclared cell, *as measured* | count 1, 2026-08-11: **0 of 3,418** `@*.md` notes lack a `type:` key | **GROUNDED for the population measured** — see the scope finding below for the population it does not cover. |

**Round-3's finding is WITHDRAWN, and audit item 5′ with it.** My round-3 audit found that shape (i)
relocated the ungrounded premise rather than removing it: the structural subset
(`path_hostile_char`, `empty`) would fire on undeclared writes carrying `_PATH_HOSTILE_RE`'s
person-scoped "0 of 1590" (`name_validation.py:94`, corpus at `:26-28` — both re-read this round and
unchanged). Dave's ruling 2 chose (ii) instead, and under (ii) the write is refused *before* any
Tier-1 pattern is evaluated, so no person-derived number crosses an entity boundary at all. That
dissolves the finding rather than answering it, exactly as Finding B claims. **Item 5′ is withdrawn**,
item 2 stays withdrawn, and the entity-agnostic/person-specific partition is correctly cancelled
rather than deferred. The company-name `/` count 5′ also asked for is not this item's to run —
`CompanyRepository.save(Company(name="Bausch/Lomb"))` still creates a spurious directory
(`base.py:381`, no override in `company.py` — re-confirmed by grep this round), and that is WI-022's.

### Finding 1 — rule (ii) is pinned to a number that does not bound its surface

This is the call architect round 4 note 3 routes here, and the gate owns it. Read from source rather
than from the note:

- `update_frontmatter_field(file_path, field_name, field_value)` (`writer.py:292-296`) and
  `update_frontmatter_fields(file_path, updates)` (`writer.py:350-353`) take **any** path, parse
  whatever frontmatter that note carries (`writer.py:329`, `:381`), and mutate it in place. Their
  declaration is the target note's own `type:`, so the undeclared case is "the note on disk carries
  none" — for a note anywhere in the vault, not only under `@*.md`.
- `write_markdown_file`'s D1b/D1c arms (`writer.py:258-263`) likewise take any path with a
  caller-supplied dict.
- Count 1's method, as stated in `## Conductor Rulings & Grounding`, is `rglob("@*.md")`.

So the population rule (ii) was chosen against is `@*.md`-scoped and the rule is not. Finding B
states the justification as an absolute — "the live undeclared population is **0 of 3,418**" — and
ruling 2 records the same number as its basis. The number is real and correctly run; it just answers
a narrower question than the one the rule asks. This matters in three concrete ways, none
hypothetical:

1. **The blast radius is the consumer-audit number.** `AC-2`'s refusal is a breaking change for
   HAL9000, exocortex and orchestrator, all installed with `pip install -e`
   (`docs/backlog-campaign-2026-07-05.md:98`). A consumer calling
   `update_frontmatter_fields(some_note, {"name": ...})` against an untyped note that is not a
   person note starts raising. "0" does not bound that; nobody has counted the notes it does bound.
2. **The stated "0" already embeds a judgement that the re-grounding predicate must carry.** The
   conductor's own note records three `@*.md` files with **no frontmatter at all**, discounted as
   archive residue under `_merged_dupes/`. Under rule (ii) a no-frontmatter note is an undeclared
   note — the distinction is "untyped frontmatter" vs "no frontmatter", and the rule does not draw
   it. The discount is defensible for archive paths; it is not visible in the "0" that Finding B and
   ruling 2 both quote.
3. **Audit item 4's purpose is defeated by an imprecise predicate.** Item 4 exists so build-start
   re-grounding has something to detect rot in. A re-grounding step handed "the untyped population
   is 0 of 3,418" will re-run `rglob("@*.md")` and see 0 again while the population the rule
   actually reaches has grown. The predicate has to be written down in the form the rule is stated
   in, not in the form the first query happened to take.

This is not a request to re-rule (ii) — with the `@*.md` population at 0 the ruling is very likely
right on the wider population too, and the fail-closed direction is Dave's call already made. It is
a request for the number that rule is stated with to be the number that bounds it.

### Finding 2 — two live-data deltas this document books as owed and never numbers

Both are the item's own words, and both are Class-1 claims sitting in unsigned text where the fold
can still carry a number into them.

**(a) The address-laxity delta (Finding D, reconciliation 2).** `_extract_email_and_name`'s
acceptance test is `"@" in email_p and "." in email_p` (`person.py:1292`); `Email.parse`
additionally rejects whitespace and multiple `@` (`identifier.py:141-160`). Finding D states the
consequence plainly — "Some entries that are kept-as-is today will start normalizing, and vice
versa. That is a real behaviour delta on live data, not a refactor" — and then never gives it a
size. `AC-5`'s agreement clause ("agrees with `Email.parse` on every input form the deleted sites
accepted") is written *around* this delta rather than over it, so no criterion will catch it. The
predicate is one pass over stored `emails[]`/`aliases[]` entries evaluating both tests and reporting
disagreements. If it is zero, the consolidation is a refactor and the spec can say so; if it is not,
the spec owes the list.

**(b) The phone-authority delta (architect round 4, blocking).** The architect's finding is
architectural and I do not re-rule it, but two of its three candidate shapes turn on a number nobody
has. Delegating to `Phone.parse` imports `MIN_DIGITS = 7` (`identifier.py:228`), which raises
`IdentifierError` on anything shorter (`:238-239`), where `normalize_phone` returns the digits
(`person.py:138-145`) — re-read this round, both confirmed. The choice between "move
`normalize_phone` to a leaf" and "delegate to `Phone.parse`" is therefore a blast-radius question
exactly like the (i)/(ii) choice was, and it is decided by one count: stored `phones[]` entries with
fewer than seven digits. Conditional on a choice not yet made, which is why it is listed as
conditional below rather than blocking on its own — but if it is not run in the same pass, the
architect's next round will be waiting on a shell again.

### Required grounding

Items 3 and 6 of the round-3 list are **satisfied** (see the grounded table). Items 2 and 5/5′ are
**withdrawn**. What remains is three queries, all cheap, all needing a shell and vault access
**outside this cage**, and all runnable in the same pass as the re-origination:

1. **Re-scope count 1 to the rule's surface.** Over the whole vault, not `rglob("@*.md")`: how many
   notes lack a `type:` key, split into *has frontmatter but no `type:`* and *no frontmatter at
   all*, and split by whether the path is under `@*.md`, an archive directory
   (`_merged_dupes/`, `_quarantine/`), or neither. Then state rule (ii) in Finding B with THAT
   number, and write the predicate down in re-runnable form so build-start re-grounding tests the
   rule rather than the first query.
2. **Number Finding D's reconciliation 2.** Over stored `emails[]` and `aliases[]` entries: how many
   are accepted by `_extract_email_and_name`'s `"@" in … and "." in …` (`person.py:1292`) but
   refused by `Email.parse` (`identifier.py:141-160`), and how many the reverse. Report the count and
   a sample; carry it into Finding D and into the spec's behaviour-change note.
3. **Conditional on the architect's phone-authority ruling** — if the gate is to delegate to
   `Phone.parse`: how many stored `phones[]` entries normalize to fewer than seven digits
   (`identifier.py:228`). Run it anyway if the shell is already open; it is the number that decides
   whether the substitute is free, and if it is non-zero `AC-4` acquires a refusal case and joins
   the re-origination set.

### Conclusion

The item's data position has genuinely improved, and this is the first round where that is true. The
premise that blocked rounds 1–3 is gone — not argued away but *dissolved* by a ruling that removes
the inference, with counts run and pasted in, Finding C honestly re-dated to a spent number, and the
sentinel exemption justified against a real population of three. My own round-3 finding is withdrawn
and two of the five grounding items with it.

What stops this being a PROMOTE is narrow and, I think, one pass from being fixed: the rule the whole
design now turns on is stated with a number measured over `@*.md` while the rule itself is
path-agnostic (`writer.py:292`, `:350` take any path), and the two behaviour changes this document
books as owed on live data — the address-laxity delta and, conditionally, the `MIN_DIGITS` refusal —
have never been given a size. Those are Class-1 premises in the plainest sense, and audit item 4's
whole purpose is that the number a rule is chosen against be the number that bounds it.

**Signal for the factory, stated because the targets line alone cannot carry it.** This is a
CONVERGING round, not a treadmill one, and the arc is visible in the targets: rounds 1–3 all named
`AC-2`/`AC-4` and the untyped-dispatch premise; that target is CLOSED — deleted by ruling 1, folded,
and re-verified from source here. This round names `#approach` and `#exploration-notes` only, on a
scope correction to a number that now exists and two deltas the document itself already books as
owed. It does not re-raise the signed criteria: the `AC-1`–`AC-5` defects are staged in
`## Re-origination Brief` for Dave's one round and I add nothing to that list. The three queries above
are the last data work this item needs, they are smaller than any prior round's, and they can be run
by the same shell-holding actor in the same pass as the re-origination. A fifth data-premise spawn
before those numbers exist will reproduce this section. Stage stays at `exploring`.

```verdict
gate: data-premise
verdict: REVISE
date: 2026-08-11
model: claude-opus-5
targets: #approach, #exploration-notes
note: First round with real counts — round 3's finding is WITHDRAWN (rule (ii) refuses before any Tier-1 pattern evaluates an undeclared write, so no person-scoped number crosses an entity boundary; items 2 and 5′ withdrawn) and Finding C's re-dating plus the sentinel population are discharged — but rule (ii) is pinned to "0 of 3,418", measured by `rglob("@*.md")`, while the rule's own surface is path-agnostic (update_frontmatter_field(s) at writer.py:292/:350 and D1b/D1c take any path), the stated 0 silently discounts three no-frontmatter notes that rule (ii) would treat as undeclared, and two live-data deltas the doc books as owed are still unnumbered (Finding D's laxity delta at person.py:1292 vs identifier.py:141-160; conditionally Phone.parse's MIN_DIGITS=7 at identifier.py:228).
```

## Spec-Writer Fold — 2026-08-11 (round 5)

**This round PRODUCED a fold, not a hand-back.** Both round-4 verdicts target `#approach` and
`#exploration-notes` **only** — unsigned text, and both gates said in terms that they add nothing to
the re-origination list. That is the first time in this document's history that every open finding is
inside my authority to fix, and it is why this round writes rather than escalates.

Cold-start, read in role order: `spec-writer.yaml`, this document in full (five ac-red-team rounds,
the `ac-signoff` fence, four architectural reviews, four data audits, three prior hand-backs, the
round-4 fold, `## Conductor Rulings & Grounding`, the re-origination brief), then the code every claim
below turns on. Every citation re-derived from source this round, not inherited: `identifier.py`
(module imports, `Email.parse`, `Phone`, `WhatsAppJID.parse`), `repositories/person.py`
(`normalize_phone`, `phones_match`, `_extract_email_and_name`, `_normalize_address_fields`,
`_writeback_identifier`, the module import block), `repositories/base.py` (import block),
`writer.py` (import block, the three fm-building arms, both `update_frontmatter_*` signatures),
`obsidian_schemas/__init__.py`, `repositories/__init__.py`, plus `docs/identity-engine-endgame.md`
and `docs/backlog-campaign-2026-07-05.md`. This cage has **no shell**; the live vault was not read.

### What this round wrote

| Section | Change | Answers |
|---|---|---|
| **Finding G** — new subsection *"Where the phone normalization authority LIVES"* | Names the authority and states the delta. The cycle claim is re-derived from source and confirmed; the resolution is **relocation to a stdlib-only leaf** (`obsidian_schemas/phone_normalization.py`) with a compat re-export, deleting BOTH deferred imports at `identifier.py:236` and `:272`. Both rejected shapes named with the reason. | architect round 4, blocking |
| **`## Approach`** | The phone paragraph now says where the authority lives before it names the symbol; header note records the amendment and what did not change. | architect round 4, `#approach` |
| **Constraints** | New bullet on the WI-023 overlap and its sequencing; Effort corrected to **two** new modules with the relocation priced and its verification named. | architect round 4 |
| **Finding B** — rule (ii) | Re-scoped. The absolute *"0 of 3,418"* is replaced by the rule's actual surface, the untyped-frontmatter/no-frontmatter split, a re-runnable re-grounding predicate at the rule's own scope, and an explicit statement of what the owed number can and cannot change. | data-premise round 4, Finding 1 |
| **Finding B** — new paragraph on D1b | The gate reads the POST-merge dict at the convergence point (`writer.py:266`), not the `frontmatter=` parameter (`:259`), which `extra_fields` overrides at `:260-261`. | architect round 4, note 4 |
| **Finding D** — reconciliation 2 | Enumerated into **six** disagreement classes from source, with a re-runnable four-cell predicate. | data-premise round 4, Finding 2(a) |
| **`## Grounding Still Owed`** (new section) | The complement of `## Conductor Rulings & Grounding`: G1, G2, G3-withdrawn, plus the consumer audit, in one artifact instead of three verdict notes. | both round-4 gates |
| **Re-origination Brief** | Header records that the list has **not** grown; architect note 2's wording correction folded into the `AC-1` entry. | architect round 4, note 2 |
| **Carried Forward** | Gains the phone relocation; the consumer-audit bullet's "0" is corrected to the `@*.md` subset. | both |

### Two things this round found that the reviews did not have

1. **The deferred import is already TWO, and the frame already has an owner.**
   `identifier.py:272` (`WhatsAppJID.parse`) reaches `normalize_phone` the same way `:236` does, so
   the gate would be the third reach rather than the second. And WI-023 carries *"move
   `normalize_phone`/`phones_match` … to a small util module"* as scope item 4
   (`docs/identity-engine-endgame.md:28`), listed again on its campaign row
   (`docs/backlog-campaign-2026-07-05.md:62`) — at stage `idea`, sequenced **Phase 3, after** this
   Phase-2 item. The architect's "the frame is the suspect" reading is a recorded diagnosis whose
   owner is sequenced behind the item that forces the third reach. That is what makes the relocation
   the obviously right shape rather than a judgement call, and it is why this fold takes item 4 rather
   than deferring to WI-023.
2. **A seventh disagreement class on the address side that nobody named: CASE.** `_extract_email_and_name`
   stores parseaddr's output verbatim (`person.py:1293`, stored at `:1308`); `Email.parse` lower-cases
   (`identifier.py:150`) and `.value` re-emits the lower-cased halves (`:163-164`). Dedupe is already
   case-insensitive at the callers (`person.py:1307`, `:1314`), so nothing collapses that did not
   collapse before — but the stored BYTE changes on every mixed-case address. That makes the
   splitter's return contract a spec decision the architect's shape ruling is silent on (raw slice vs
   `Email.parse(...).value`), and it is booked as such rather than decided in the exploration.

### What this round still deliberately did NOT write, and why — unchanged from round 4

**No Design, Edge Cases, Implementation Plan, Write Targets, Verification, or `criteria` refinement.**
The three reasons are the round-4 ones and none has moved: `AC-1`–`AC-5` remain inside the
`ac-signoff` hash span (`ac_hash: a76ebad54da2`) with four of them named wrong-on-facts by gates whose
findings Dave has accepted, so WI-061 routes them to re-origination, not refinement; the plan and the
criteria are one object, so a plan written against a set about to be re-originated is a plan that must
be rewritten; and rule D3 refuses `→ specced` without a data-premise PROMOTE, which the standing
verdict is not. The re-origination brief is still the escalation, still one round, and — per the note
added to its header this round — still exactly Tier A + Tier B.

### Class-shaped fold — declared, and still bounded by ruling 3

Per WI-226, the finding in front of me is not "the Approach named one symbol it cannot reach". The
generator both round-4 gates are instances of:

> **A commitment is made to a SYMBOL or a NUMBER without asking where it lives / what it spans — and
> the answer, when finally asked, is one layer away from where the commitment assumed it was.**

Architect round 4 is that shape on a symbol (`normalize_phone` — committed to in `## Approach`, lives
one layer up in the repository package). Data-premise round 4 is the identical shape on a number
(count 1 — committed to in Finding B, spans a proper subset of the rule's surface). Sweeping the rest
of the document for the same shape, this round closed both instances **and** the two nearest members:
Finding D's reconciliation 2 (a delta committed to as "some entries" with no span) and the splitter's
return contract (a shape committed to with the stored byte unstated). **Declared:** sweeping the
remaining commitments — the `REASONS` literal (span: a closed frozenset of fifteen, `errors.py:110-127`,
already stated), the `pattern` attribute (one consumer, already stated), `model_to_frontmatter` as the
entity→dict projection (`writer.py:88-130`, same layer), `vf.entity_type` at D8 (same call frame) — I
find no further open member: each already names both its home and its span in the text that commits
to it.

**And here the sweep STOPS**, on Dave's ruling 3 rather than on mine. The altitude declaration holds:
the AC checking machinery is sufficiently specified, the re-origination fixes named defects only, and
findings of the checking-of-the-checking shape do not block. This section opens no further rung.

### Re-entry — unchanged in order, one step shorter

1. **Dave re-originates `AC-1`–`AC-4` in ONE round** (Tier A + Tier B of the brief; `AC-5` unchanged).
   The list did not grow this round and the phone finding did not add to it.
2. **One shell pass, alongside the re-origination:** queries **G1** and **G2** in
   `## Grounding Still Owed`, plus the consumer audit's two greps. G3 is withdrawn as moot.
3. **ac-red-team → architect → data-premise → spec-writer.** The architect's four rulings carry
   forward and need no re-derivation; the data gate's round-4 conclusion says its three queries "are
   the last data work this item needs", and one of the three is now moot.
4. **spec-writer.** With 1–3 done the spec is assembly: `## Carried Forward` plus the routing, the
   wall, the phone relocation, the splitter consolidation, the Tier-1 branch-unit reification, and
   the `lint_vault --fix` delta threading.

## Architectural Review — 2026-08-11 (round 5)

**Recommendation: REVISE — return to exploration**

**Round 5, cold-start re-spawn.** Read in role order: `architect.yaml`, this document in full (five
ac-red-team rounds, the `ac-signoff` fence, four prior architectural reviews, four data audits, five
spec-writer rounds, `## Conductor Rulings & Grounding`, `## Grounding Still Owed`, the
re-origination brief), then the code every new claim turns on (`identifier.py`,
`repositories/person.py`, `repositories/base.py`, `writer.py`, `obsidian_schemas/__init__.py`,
`repositories/__init__.py`, `tests/test_repositories.py`, `docs/identity-engine-endgame.md`,
`docs/backlog-campaign-2026-07-05.md`), plus `LESSONS.html`. No shell in this cage; the live vault
was not read — the counts used below are the conductor's, cited as such.

**My round-4 blocking issue is CLOSED, and closed with the shape I said pays principal.** I
re-derived every leg of the round-5 fold's phone resolution from source rather than accepting its
account of itself (table below); all confirm. What follows is one new blocking issue. It is not a
new generator and it is not checking-of-the-checking: it is a correction to the SHAPE of a defect
already inside Dave's ruling-3 list (`AC-4`'s `aliases[]`), and it has to land before the
re-origination rather than after it, because the brief as written pins a clause the design cannot
satisfy on six of its ten arms.

### Trigger check

Three fire, unchanged: **two** new modules now (the gate and the phone leaf); a contract change
crossing into three downstream repositories installed with `pip install -e`
(`docs/backlog-campaign-2026-07-05.md:98`); a derived-wall enforcement mechanism that must be
designed rather than copied. Effort stated at one to two sessions.

### Round-4's blocking issue — verified closed from source

| Claim the round-5 fold makes | Where I read it | Result |
|---|---|---|
| `normalize_phone`/`phones_match` are module-level, stdlib-only (`re`), relocatable verbatim | `person.py:129-145`, `:148-179` | confirmed — no package imports in either body |
| the cycle a leaf gate would close | `person.py:78` (`from .base import BaseRepository`); `base.py:19` (`from ..writer import …`); `writer.py:19-33` imports only `errors`, `models`, `parser`, `vault_io` | confirmed — no repository import in `writer.py` |
| both ends imported at package load | `obsidian_schemas/__init__.py:40` (writer), `:72` (repositories) | confirmed |
| the deferred import is already TWO | `identifier.py:236` (`Phone.parse`) and `:272` (`WhatsAppJID.parse`), both `from .repositories.person import normalize_phone` | confirmed — the gate would be the third reach |
| `Phone.parse`'s floor is not in the dedupe path | `identifier.py:228` (`MIN_DIGITS: ClassVar[int] = 7`), raise at `:238-239`; `normalize_phone` is `re.sub(r"\D", "", …)` with no floor (`person.py:145`) | confirmed |
| consumers: `normalize_phone` is not re-exported at top level | `repositories/__init__.py:8-12` exports only the four repository classes; `__init__.py:72-78` pulls only those | confirmed |
| the compat re-export's verification is real | grep for `normalize_phone`/`phones_match` across the tree returns exactly `identifier.py` (2 deferred), `tests/test_repositories.py:1868-1893` (7 sites) and `person.py`'s own ten in-module calls — no other importer | confirmed |
| the frame already has an owner, sequenced behind this item | `docs/identity-engine-endgame.md:28` (WI-023 scope item 4, stage `idea`); `docs/backlog-campaign-2026-07-05.md:62` | confirmed |

That is the right answer to the prior-art dimension's 2nd-recurrence rule: the frame was the
suspect, the frame had a recorded owner sequenced *after* the item that forces the third reach, and
the fold pays the principal instead of taking the two-line dodge. I also re-derived the fold's other
new claims — Finding B's D1b post-merge paragraph (`writer.py:256-266`: `extra_fields` overrides the
`frontmatter=` copy at `:260-261`, so `fm` at the convergence point is the declaration, not the
parameter at `:259`) and all six of Finding D's reconciliation-2 classes (`person.py:1291-1298` vs
`identifier.py:145-160`, including class 6's `.lower()` at `:150` re-emitted by `.value` at
`:163-164`). All hold.

### Blocking issue — Finding I's `aliases[]` obligation is a cross-field MIGRATION, and it is not expressible on the dict-shaped arms under the two rulings it sits between

Finding I and Tier B of the re-origination brief both instruct: **"Add `aliases[]` to the container,
on both sides."** Read against the code they cite, the behaviour on the input side is not
normalization of an alias entry. It is a MOVE between fields:

- `_normalize_address_fields` walks `person.aliases`, splits each entry, and appends the extracted
  address to a *different* list — `person.emails.append(email)` (`person.py:1328`) — keeping only
  the display half in `aliases[]` (`:1331-1333`).
- The move is guarded by `seen_emails_lower` (`:1327`), a set populated by the **emails[] pass** of
  the same call (`:1303`, `:1307-1316`). The dedupe is what stops the migration minting a second
  copy of an address the person already has.

Three settled things collide on that, and the collision is only visible once `aliases[]` is in the
container:

1. **The gate has no `existing` parameter** — my round-1 ruling, re-affirmed in rounds 2, 3 and 4 and
   carried forward in `## Carried Forward`. On a write that introduces only `aliases`, the gate
   cannot see the stored `emails[]`, so it cannot perform `:1327`'s dedupe at all.
2. **Finding C's delta rule** — judge what the write INTRODUCES, never what it preserves. `emails[]`
   on such a write is preserved, not introduced, so it is outside what the gate may touch.
3. **`## Approach`'s stated output contract** — the gate "takes the fields a write is INTRODUCING …
   and returns **them** validated and normalized, or refuses". Emitting a key the caller did not pass
   is outside that contract.

**And doing it anyway is worse than not doing it, which is what makes this blocking rather than a
question owed.** `update_fields` merges by key REPLACEMENT — `frontmatter.update(updates)`
(`base.py:451`). A gate handed `{"aliases": ["Al B <a@b.com>"]}` that emitted `emails: ["a@b.com"]`
would not append to the stored list; it would **replace** it, destroying every other stored address
on that person. Concrete: a canonical carrying `emails: ["dave@acme.com", "d@personal.com"]` receives
`update_fields(person, {"aliases": ["Al B <a@b.com>"]})` — D4, inside AC-1's derived set — and comes
back with one email. That is a new corruption class, introduced by the fix, in an item whose whole
purpose is closing a corruption class. `update_frontmatter_field(path, "aliases", …)` (D5,
`writer.py:329-335`) and the D1b/D1c dict arms have the same shape.

**Where it IS expressible, and that is the fix.** On the entity-shaped arms the gate receives the
projection of the whole record — `model_to_frontmatter` emits every declared field
(`writer.py:111`), so `emails[]` and `aliases[]` are both in its input, the `:1327` dedupe has its
set, and under Finding C an entity write's delta IS the whole record, so nothing is preserved that
the migration touches. D1a/D2/D3 are also exactly where `_normalize_address_fields` runs today
(`person.py:1269`), so the behaviour Finding I says must not regress is preserved where it already
lives, and nothing is lost.

So the obligation splits by ARM SHAPE, and this is the same split ac-red-team round 3 already forced
on `AC-4` for the other dimension — two clauses, one per class of arm, because the case is only
constructible on one of them (`docs/write-door-bypasses.md`, revision 3's exclusion-set note). Stated
as direction rather than design: **the alias-borne-address migration is an entity-arm behaviour; on a
dict-shaped arm the gate normalizes the `aliases[]` entries it is handed IN PLACE and never emits a
field the write did not carry.** Whichever way it is written, `AC-4`'s new `aliases[]` clause must
carry the scoping, because "on both sides, on every arm in AC-1's derived set" asserted flat is a
criterion the design cannot meet on six arms and can only be *greened* by the replacement bug above.

**Why this is architectural and why now.** It is not a build detail: it turns on the gate's signature
and its output contract, both of which are my settled rulings, and on the delta rule, which four
gates have held. It is not a new rung of the LESSONS #38 ladder either — Dave's ruling 3 enumerates
`AC-4`'s `aliases[]` as one of the named defects the re-origination fixes, and this says what that
fix has to SAY. It costs the queued re-origination round one scoping clause and a paragraph in
Finding I; discovered after the re-sign it costs another one, which is the price this document has
already paid five times.

**One consequence the fold should state in the same pass.** `_extract_email_and_name` is an INNER
function of `_normalize_address_fields` (`person.py:1286`, nested inside the static method at
`:1278`), so Finding D's "REPLACE" of that site is an edit to the enclosing method, not a local
swap — and the enclosing method's fate (deleted and subsumed by the gate, or kept above it on the
save path) is what this issue decides. `## Approach` currently implies subsumption ("the code being
replaced"); nothing states it.

### Rulings carried forward — settled, do not re-derive

All four stand and were re-checked against the code this round; nothing above reopens any of them —
this finding is about what the gate may EMIT, not about what it receives.

- **Gate signature:** no `existing` parameter, one entry point taking the introduced fields plus the
  entity type; entity arms project through `model_to_frontmatter` (`writer.py:88-130`) first.
- **Splitter:** TOTAL, returns `(address | None, display)`, owns the parens form before delegating,
  maps `IdentifierError` to "not an address"; `Email.parse`'s angle-bracket gate
  (`identifier.py:141-149`) is NOT widened.
- **DECLARE:** the gate is handed its semantic context and never consults the filesystem. Adopted by
  Dave (ruling 1) and folded.
- **The phone authority relocates to a leaf** — ratified this round from source, above.

### Review — only what changed

**Fit / Reversibility / Generalization / Prior art:** as rounds 2–4 recorded them. Approach F remains
right; `tests/test_write_routing.py:1-18` remains the precedent AC-1's battery copies; no cited
execution is owed. Reversibility improves slightly with the relocation — it deletes two workarounds
rather than adding a third.

**Duplication:** the dimension that produced round 4's finding is now discharged on both halves.
Addresses: one authority (`Email.parse`) plus one splitter, with Finding D's honest lower-bound limit.
Phones: one authority, relocated to where both lower layers can reach it, with `phones_match`
deliberately left out of the gate's semantics so WI-023 item 2's `Phone.key` question stays open.
That last restraint is the right call and worth naming — moving a symbol without co-opting its
semantics is what keeps this item out of another item's decision.

**Boundaries:** the residual boundary question is the one in the blocking issue — not *where the gate
lives* (settled) but *how wide its output is*. A gate that may add keys the caller did not pass is a
different component from one that returns what it was handed, and the difference is invisible until
`aliases[]` enters the container. Everything else is unchanged: `writer.py`/`base.py` gain a leaf
dependency, the person rules live inside the gate, `vault_io` keeps its single reason to exist.

**Determinism boundary (LLM vs code):** n/a for LLMs; the item is the opposite move throughout —
a contract held by producer discipline, made structural.

**Cost & maintenance:** unchanged at one to two sessions plus the Tier-1 branch-unit reification and
the D8 delta threading. The relocation is small and its verification is honest
(`tests/test_repositories.py:1868-1893` green *unedited*).

**Build vs extend vs integrate:** extend, with one symbol moving first — now correctly priced as two
new modules in Constraints.

### Notes (non-blocking)

1. **`MIN_DIGITS` is `Phone.MIN_DIGITS`, a ClassVar, not a module-level symbol.** Finding G's table
   cites it as `identifier.py:MIN_DIGITS:228`; the line is right, the symbol form is not, and a grep
   for it as written resolves nothing. Also worth knowing though it does not affect the relocation:
   the floor has TWO consumers — `Phone.parse` (`:238-239`) and `WhatsAppJID.parse` (`:274`) — and
   the fold names one.
2. **Two cosmetic slips in the same subsection, free to fix in the same edit.** "restoring the module
   to the pure stdlib-only leaf its own docstring claims (`:31-36`)" — after the relocation
   `identifier.py` imports a package sibling, so it is a leaf but not stdlib-only, and `:31-36` is the
   import block, not the docstring (`:1-29`). And "its nine in-module call sites" lists ten
   (`person.py:156`, `:157`, `:244`, `:250`, `:389`, `:395`, `:450`, `:461`, `:542`, `:631` — grep
   confirms exactly those ten). The list is right; the count is not.
3. **Rounds 1–4's standing notes all carry:** the dedicated `pattern` attribute rather than
   overloading `declared_type` (`base.py:267-269` feeds it back into `_owns`); the new `REASONS`
   literal chosen at spec time (`errors.py:110-127`, closed frozenset of fifteen; `bounded_message`
   raises on any non-member at `:139-145`); `lint_vault --fix`'s missing delta object; the
   `book.py`/`meeting.py` `save` overrides that are correctly not arms; and the
   three-functions-one-shape collapse, still a separate work item and still not recommended for
   absorption.
4. **The document is still buildable two ways until Dave re-originates** — `## Approach` refuses an
   undeclared write, `AC-2`/`AC-4` as signed gate an untyped dict "exactly as a `type: person` one
   is". Tier A of the brief names this and correctly declines to fix signed text. Recorded again only
   so nothing above is read as a statement that the document is internally coherent today.

### Arc note — this is convergence, not a treadmill

Stated because the targets line alone cannot carry it, and because ruling 3 makes the distinction
load-bearing. The five architect rounds have each closed their target and moved to a different one:
the Company annexation (1) → its structural sharpening plus the missing Tier-1 table (2) → the
DECLARE ruling plus the `AC-1` pass-what gap (3) → the phone authority (4) → the `aliases[]`
migration's expressibility (5). Round 4's target is closed and verified from source this round. No
target has been re-raised. This round's finding is inside ruling 3's own named list rather than a new
rung of the ladder, and it is the last thing the re-origination needs to be right the first time —
after it, the brief is Tier A + Tier B with `AC-4`'s clause correctly scoped, and the queued order
(re-originate → one shell pass for G1/G2 + the consumer audit → ac-red-team → architect →
data-premise → spec-writer) stands unchanged.

```verdict
gate: architect
verdict: REVISE
date: 2026-08-11
model: claude-opus-5
targets: AC-4, #exploration-notes, #approach
note: Round 4's phone finding is closed and re-verified from source (relocation to a stdlib-only leaf breaks the writer→gate→person→base→writer cycle, deletes both deferred imports at identifier.py:236/:272, lands WI-023 item 4, no behaviour or consumer delta) — but Finding I's `aliases[]` obligation is a cross-field MIGRATION (person.py:1328 appends the extracted address to person.emails, deduped at :1327 against the emails[] pass's own set), which is unexpressible on the six dict-shaped arms under the settled no-`existing` signature and the delta rule, and a gate emitting an `emails` key there would REPLACE the stored list via base.py:451's frontmatter.update — so AC-4's forthcoming clause must scope the migration to the entity-shaped arms before Dave signs it, not after.
```

## Data Audit — 2026-08-11

**Recommendation: REVISE — return to exploration**

**Round 5, cold-start re-spawn.** Read in role order: `data-premise.yaml`, this document in full
(five ac-red-team rounds, the `ac-signoff` fence, five architectural reviews, four prior data audits,
five spec-writer rounds, `## Conductor Rulings & Grounding`, `## Grounding Still Owed`, the
re-origination brief), then the code every premise below turns on. Same method bound as every prior
round in this cage: **no shell, scope limited to this tree's files, the live vault was not read** —
the counts used below are the conductor's, cited as such. Every citation was re-derived from source
this round rather than inherited.

**What moved, and what this round is for.** The round-5 fold answered both of my round-4 findings as
far as a shell-less cage can, and the round-5 architectural review then landed a new blocking issue
that changes what one owed query has to report. So this round is short and has exactly two parts:
discharge what the fold discharged, and name the one Class-1 claim the `aliases[]` finding created
that no query in `## Grounding Still Owed` currently sizes.

### Trigger check

**Class 1 AND Class 2 — both still fire, on a smaller surface again.**

- Class 1 (data-distribution / field-presence): three quantified claims about live entries remain
  unmeasured — G1's undeclared population at the rule's own scope, G2's four disagreement cells plus
  the case cell, and (new this round) the population of address-bearing `aliases[]` entries, which is
  the population the round-5 architect finding splits by arm shape.
- Class 2 (rule-effect-against-existing-corpus): rule (ii) is still a new refusal rule whose effect
  against the corpus as it exists today is known for `@*.md` (count 1) and unknown everywhere else it
  reaches. G2 is the same shape on the splitter consolidation: a new acceptance predicate never run
  over the stored entries it will judge.

### My round-4 findings — what the fold discharged, and what it could not

Re-read against the fold's text and re-derived from source. I am explicit about the split because it
is what makes this round an arc rather than a repetition of round 4.

| Round-4 finding | What it asked for | Status |
|---|---|---|
| **Finding 1** — rule (ii) pinned to a number that does not bound its surface | (a) state the rule with a predicate at the rule's OWN scope, in re-runnable form, and stop quoting "0 of 3,418" as an absolute; (b) run it | **(a) DELIVERED IN FULL.** Finding B now re-scopes the rule, splits the undeclared case into untyped-frontmatter/no-frontmatter shapes, states the re-grounding predicate over every `.md` file rather than `rglob("@*.md")`, books the number as OWED at that scope (G1), and — the part I did not ask for and should credit — states explicitly what the number can and cannot change: rule (ii) is fail-closed, so a larger population is stricter, not wronger; the number sizes blast radius, not correctness. I re-derived the path-agnosticism from source: `update_frontmatter_field` (`writer.py:292-296`) and `update_frontmatter_fields` (`writer.py:350-353`) both take `file_path: Union[str, Path]` with no glob constraint, and D1b/D1c likewise (`writer.py:258-263`). **(b) NOT RUN.** |
| **Finding 2(a)** — the address-laxity delta is booked as owed and never numbered | enumerate it and give it a predicate; run it | **enumerated, NOT RUN.** Finding D's six-class table re-derives exactly against `person.py:1286-1298` and `identifier.py:134-160`, read side by side this round: class 1 whitespace (`:1292` vs `:153-154`), class 2 multiple `@` (`:155-156`), class 3 dot outside the domain (`:158`), class 4 empty local (`:158`), class 5 the parens regex's dotless domain (`person.py:1295` vs `identifier.py:158`), class 6 case (`person.py:1293` stored verbatim at `:1308` vs `identifier.py:150`'s `.lower()` re-emitted by `.value` at `:163-164`). Class 6 was found by the fold, not by me, and it is the one that changes stored bytes rather than behaviour. The predicate is booked as G2. |
| **Finding 2(b)** — `Phone.parse`'s `MIN_DIGITS` refusal, conditional | run it if the delegate shape is chosen | **CORRECTLY MOOT.** The relocation shape was chosen, so the floor never enters the dedupe path. Verified from source: `MIN_DIGITS` is a `ClassVar` on `Phone` (`identifier.py:228`) consumed at `:238-239` and `:274`, while `normalize_phone` (`person.py:129-145`) applies no floor. G3 is withdrawn on the same terms it was raised, which is the right handling. |

**The fold's other new claims also re-derive**, and I checked them rather than accepting its account:
`normalize_phone`/`phones_match` are module-level and stdlib-only (`re` alone — `person.py:129-145`,
`:148-180`), so the relocation is verbatim; both deferred imports exist and reach the same symbol
(`identifier.py:236` in `Phone.parse`, `:272` in `WhatsAppJID.parse`); and the caller-side dedupe
class 6 leans on really is case-insensitive (`person.py:1307`, `:1314`, and the aliases pass at
`:1327`, `:1331`, `:1335`, `:1340` — every one compares `.lower()`), so the fold is right that
nothing collapses that did not collapse before and the delta is the stored byte.

**One citation slip, non-blocking and already named.** Finding G's table cites
`identifier.py:MIN_DIGITS:228`. The line is correct; the symbol form is not — it is `Phone.MIN_DIGITS`,
a `ClassVar`, so a symbol grep resolves nothing. Architect round-5 note 1 already flags this. Recorded
only because it is the one citation in this document that does not resolve as written; it changes no
premise.

### Finding — the `aliases[]` arm-shape split is about to be signed against an unmeasured population, and no owed query sizes it

This is the one thing this round adds, and it exists only because the round-5 architectural review
landed after `## Grounding Still Owed` was written.

The architect's blocking issue splits Finding I's `aliases[]` obligation **by arm shape**: on the
entity-shaped arms the alias-borne-address migration is preserved (the gate receives the whole
projection, so `:1327`'s dedupe has its set); on the six dict-shaped arms the gate normalizes the
`aliases[]` entries it is handed in place and never emits a field the write did not carry. That is a
behaviour DIFFERENCE between arms, written into `AC-4` before Dave signs it — and its live
consequence is bounded by one number nobody has: **how many stored `aliases[]` entries are
address-bearing.**

The document's own evidence on that population points in two directions at once, which is precisely
why it needs a count rather than a reading:

- Finding I offers `create_stub`'s `aliases=[email]` seed (`person.py:1448`) as the existence proof
  that the aliases-as-identifier-input path "is not hypothetical".
- Parked defect 2 says that same seeded alias is **erased by its own save** — `_extract_email_and_name`
  reads it as an address, `:1327` finds it already in `seen_emails_lower` from the `emails[]` pass, so
  no email is appended, and the entry produces no display half and is dropped (`person.py:1323-1337`).
  I re-read the loop this round and the erasure is real.

So the item's stated existence proof is the one path that provably leaves nothing behind. Whether the
population is zero, three, or three thousand is not decidable from source, and the two ends have
opposite consequences for the criterion: at zero the arm-shape split is a correctness-preserving
scoping clause with no live subject and the spec can say so; non-zero, it is a real behavioural fork
across ten arms on a live population, and `AC-4`'s clause is the only thing standing between it and a
silent regression of D3 behaviour on the dict side.

**G2 as written cannot answer it**, and the fix is one word. Its predicate reads *"over every stored
`emails[]` and `aliases[]` entry … report four cells"* — one combined report over the two fields.
Under the round-5 split the two fields now get different treatment, so the cells must be reported
**per field**. That is a reporting change to a query already owed, run in the same pass, at no extra
cost. The *extracted* cell restricted to `aliases[]` is exactly the population above.

### Required grounding

Nothing new is added to the shell pass. Two queries carried, one amended.

1. **G1 — unchanged and still unrun.** Rule (ii)'s undeclared population at the rule's own
   path-agnostic scope, with the untyped-frontmatter / no-frontmatter split and the path-class split.
   It does not gate the rule's direction (fail-closed, Dave's ruling 2); it sizes the target set the
   consumer audit intersects, and it is what build-start re-grounding re-runs.
2. **G2 — amended: report the four cells and the case cell PER FIELD** (`emails[]` and `aliases[]`
   separately) rather than combined. The `emails[]` half answers Finding D's reconciliation 2 as
   before; the `aliases[]` half is the population the round-5 arm-shape split turns on. Same pass,
   same corpus, one extra column.
3. **The consumer audit** — not a vault query, still owed, and now carrying the round-5 addition:
   importers of `obsidian_schemas.repositories.person.normalize_phone` / `phones_match` in the three
   installed repos, which the compat re-export exists to keep working. The in-tree half is grounded —
   I re-ran the grep and it resolves to `identifier.py` (2 deferred imports), `tests/test_repositories.py`
   and `person.py`'s own in-module calls, and nothing else — but the three `pip install -e` consumers
   are outside this tree and outside this cage.

### Conclusion

The fold did what round 4 asked of it wherever a shell-less actor could: the rule is now stated with
a predicate at its own scope, the address delta is a closed enumeration rather than the phrase "some
entries", the conditional third query is honestly withdrawn, and every new claim re-derives from
source. What stops this being a PROMOTE is that the two surviving predicates have still never been
executed, and that the newest design decision — the `aliases[]` arm-shape split the architect landed
this round — is heading into a signed criterion against a population the document's own evidence
describes twice, incompatibly. Stamping PROMOTE now would release the D3 brake at exactly the moment
`AC-4`'s clause is being written against an unmeasured fact, which is the failure this gate exists to
prevent one station earlier.

**Signal for the factory, stated because the targets line alone cannot carry it.** This is a
converging round and the arc is visible in what closed: rounds 1–3 named the untyped-dispatch premise
(closed, deleted by ruling 1); round 4 named the count's scope and two unnumbered deltas (one moot,
one enumerated, one re-scoped — the *stateable* half of that finding is delivered in full and I
withdraw it as a document defect); this round names a different target, `AC-4`'s forthcoming
`aliases[]` clause, and asks for one extra column on a query already queued. **What has not moved is
the thing no gate spawn can move**: G1 and G2 need a shell and vault access outside every cage, and a
sixth data-premise spawn before those numbers exist will reproduce this section, as rounds 2 and 3
did. The unblock is unchanged and is one pass: Dave re-originates `AC-1`–`AC-4` with `AC-4`'s
`aliases[]` clause scoped per the architect's round-5 finding, and the same shell-holding actor runs
G1 and the amended G2 alongside it.

```verdict
gate: data-premise
verdict: REVISE
date: 2026-08-11
model: claude-opus-5
targets: AC-4, #exploration-notes
note: My round-4 findings are discharged as far as a shell-less cage allows and re-verified from source (Finding B re-scoped with a re-runnable predicate and the fail-closed direction correctly stated; Finding D's six classes re-derive at person.py:1286-1298 vs identifier.py:134-160, including class 6's case delta whose caller-side dedupe I confirmed case-insensitive at person.py:1307/:1314/:1327; G3 correctly moot under the relocation, MIN_DIGITS being a ClassVar at identifier.py:228) — but G1 and G2 remain UNRUN, and the round-5 architect finding splits Finding I's `aliases[]` obligation by arm shape, which puts a behavioural fork into AC-4 sized by a population no owed query reports: the doc's own existence proof for address-bearing aliases[] (create_stub's seed at person.py:1448) is the one path parked defect 2 shows is erased by its own save (person.py:1323-1337), so G2 must report its cells PER FIELD before that clause is signed.
```

## Spec-Writer Fold — 2026-08-11 (round 6)

**This round PRODUCED a fold, not a hand-back.** Both round-5 verdicts name `AC-4` in their targets,
but neither asks me to edit it: the architect's finding is explicitly about what `AC-4`'s *forthcoming*
clause must say **before** Dave signs it, and the data gate's is one extra column on a query already
owed. The text that carries both is unsigned — Finding I, `## Approach`, `## Grounding Still Owed` and
`## Re-origination Brief` — so this round writes.

Cold-start, read in role order: `spec-writer.yaml`, this document in full (five ac-red-team rounds,
the `ac-signoff` fence, five architectural reviews, five data audits, five prior spec-writer rounds,
`## Conductor Rulings & Grounding`, `## Grounding Still Owed`, the re-origination brief), the project
`CLAUDE.md`, then the code every claim below turns on. Every citation re-derived from source this
round, not inherited: `repositories/person.py` (`_normalize_address_fields` and its inner
`_extract_email_and_name`, `create_stub`, `_writeback_identifier`, `normalize_phone`, `phones_match`),
`repositories/base.py` (`update_fields`), `writer.py` (`model_to_frontmatter`, `write_markdown_file`,
`update_frontmatter_field`), `identifier.py` (module docstring and import block, `Phone`,
`WhatsAppJID.parse`). This cage has **no shell**; the live vault was not read.

### What this round wrote

| Section | Change | Answers |
|---|---|---|
| **Finding I** — new subsection *"The obligation is a cross-field MIGRATION, and it splits by arm shape"* | The `aliases[]` obligation re-derived as a MIGRATION, the three settled rulings it collides with, the `base.py:451` replacement bug that makes doing-it-anyway worse than not, the entity-arm/dict-arm split, one correction to what "in place" can mean, **the mirror migration M2**, and the subsumption + idempotency riders. | architect round 5, blocking |
| **`## Approach`** | States the gate's OUTPUT contract explicitly (returns what it was handed; never emits an uncarried key) and scopes the three-field claim by arm shape; states `_normalize_address_fields`'s fate as SUBSUMED and the idempotency requirement. Header note records the amendment and what did not change. | architect round 5, `#approach` |
| **Finding G** | Two cosmetic corrections, from source: `MIN_DIGITS` is `Phone.MIN_DIGITS`, a `ClassVar` (`identifier.py:Phone:228`) with TWO consumers (`:238-239`, `:274`); and the post-relocation `identifier.py` is a leaf but not stdlib-only, with the purity claim in the docstring (`:1-29`), not the import block (`:31-36`). Ten in-module call sites, not nine. | architect round 5, notes 1–2 |
| **Finding D** — the reconciliation-2 predicate | Amended to report every cell **per field**, with the reason: the `aliases[]` *extracted* cell is the address-bearing-alias population the arm-shape split forks. | data-premise round 5 |
| **`## Grounding Still Owed`** — G2 | Same amendment in the query table, with both halves' purposes stated separately. G1 and the consumer audit unchanged. | data-premise round 5 |
| **`## Re-origination Brief`** — Tier B `AC-4` | The flat *"add `aliases[]` to the container, on both sides"* replaced by two scoped sub-clauses, one per arm class, with the byte-identity assertion on the dict side stated as class-closing rather than silent. **New sibling entry:** `### Examples of done` scenario 3's second clause, with two ways to close it. Header note records that the item GREW rather than letting it read as unchanged. | architect round 5; the class sweep |
| **`## Carried Forward`** | Gains the output contract and the arm-shape split as a settled item. | both |
| **Constraints — Effort** | The splitter consolidation is priced as a SUBSUMPTION of the enclosing method, not a local swap. | architect round 5 |

### Two things this round found that the reviews did not have

1. **The migration is a PAIR, and the second one lands in signed text.** The architect's finding names
   `aliases[] → emails[]` (`person.py:1328`). The same function performs the mirror move —
   `emails[]`'s extracted display half → `aliases[]` (`:1311` collects, `:1339-1342` appends) — with
   the identical failure on a dict arm and the identical `base.py:451` blast radius. It matters
   because it is the one that is *promised* in signed text: `### Examples of done` scenario 3 asserts
   `"Al B"` lands in `aliases[]` on a write whose actual arm is `_writeback_identifier` →
   `update_fields` (`person.py:1204-1217`) — D4, dict-shaped. Closing only the instance the architect
   named would have left that clause to be discovered after the re-sign, which is the cost this
   document has paid five times.
2. **"Normalize in place" is not available on an address-bearing alias, and the honest answer is
   identity.** Splitting `"Al B <a@b.com>"` without the accompanying migration keeps the display half
   and puts the address NOWHERE (`:1331-1333`); a bare-address alias splits to an empty display half
   and is dropped outright (`create_stub`'s seed at `:1448`, which is parked defect 2's erasure). So
   the dict-arm rule for `aliases[]` is byte-identity, not a narrower normalization — and the
   criterion has to ASSERT the byte-identity, or a build reading "in place" as "split it anyway"
   ships a deletion and is green.

### What this round still deliberately did NOT write, and why — unchanged from rounds 4 and 5

**No Design, Edge Cases, Implementation Plan, Write Targets, Verification, or `criteria` refinement.**
The three reasons are unchanged and none has moved. `AC-1`–`AC-5` remain inside the `ac-signoff` hash
span (`ac_hash: a76ebad54da2`), with four of them named wrong-on-facts by gates whose findings Dave has
accepted, so WI-061 routes them to re-origination rather than refinement — and this round's own
finding, the `### Examples of done` clause, is inside the same span. The plan and the criteria are one
object, so a plan written against a set about to be re-originated is a plan that must be rewritten.
And rule D3 refuses `→ specced` without a data-premise PROMOTE, which the standing verdict is not.

### Class-shaped fold — declared, and still bounded by ruling 3

Per WI-226 the finding in front of me is not "Finding I forgot to scope one clause". The generator,
stated at source:

> **The replaced code performs CROSS-FIELD moves, and a cross-field move is expressible only where the
> gate is handed the whole record — so every such move is an entity-arm behaviour, and asserting one
> flat across a set that contains dict-shaped arms is a criterion the design cannot meet.**

Enumerating what generates it rather than closing the instance: the moves are the members. Sweeping
every site the consolidation touches —

| # | Cross-field move | Where | Disposition |
|---|---|---|---|
| M1 | `aliases[]` entry → `emails[]` | `person.py:1328`, deduped at `:1327` | **CLOSED this round** — entity-arm; dict arms pass `aliases[]` through byte-identical |
| M2 | `emails[]` display half → `aliases[]` | `:1311`, `:1339-1342`, deduped at `:1340` | **CLOSED this round** — entity-arm; the signed Examples-of-done consequence staged in the brief |
| M3 | name blob → `email` argument | `create_stub` `:1386-1393` — `email = parsed_email` at `:1391`, `name` rewritten at `:1393` | **NOT in the gate, correctly.** The splitter is a pure function returning the pair; the MOVE is what its caller does with it, and `create_stub` keeps its own. Finding D's "REPLACE" swaps the parser under it and nothing else. |
| — | `phones[]` | dedupe on `normalize_phone`'s output, store the display form (Finding G) | **No cross-field move exists** — one field in, one field out |
| — | `update_fields`' old-stem alias | `base.py:443-448` | **A door-introduced field, not a move**: the entry is a NAME, `_extract_email_and_name` returns `("", "")` for it (`:1298`), pass-through unchanged (Finding I, already stated) |

**Sweeping the next level, as the rule requires — the dimensions of this generator are *which fields a
rule spans*, *which arms can supply them*, and *what the merge at the destination does*.** The first
two are now stated per arm class in `## Approach` and Finding I. The third is the one that made the
defect real rather than theoretical, so I checked the destination merge at **all ten arms** rather than
just D4's, since a single appending arm would make the split a special case instead of a rule:

| Arm | What the destination merge does | Read from |
|---|---|---|
| D1a `entity=` | GUARDED — `extra_fields` merges only `if key not in result`, so it cannot displace a model field | `writer.py:127`, `:257` |
| D1b `frontmatter=` | REPLACE — `extra_fields` overrides the caller's copied dict | `writer.py:259-261` |
| D1c `extra_fields`-only | the whole record; an added key simply IS the record | `writer.py:263` |
| D2 / D3 `save` | reach bytes only through D1a | `base.py:356`, `person.py:1255` |
| D4 `update_fields` | REPLACE by key | `base.py:451` |
| D5 `update_frontmatter_field` | REPLACE, one key | `writer.py:332` |
| D6 `update_frontmatter_fields` | REPLACE by key | `writer.py:384` |
| D7 `roundtrip_file` | introduces nothing, so there is no gate output to merge | `writer.py:419` |
| D8 `lint_vault --fix` | the loop owns the whole `fm` and serializes it; an added key is set on it | `lint_vault.py:876-882` |

**Every merge in the set is replace, guarded, or whole-record; not one appends.** So there is no arm
anywhere in the ten where an emitted destination key would add to a stored list rather than overwrite
it, which is what makes the entity-arm/dict-arm split a total rule rather than a D4 special case.
**Declared: I find no further open member.**

**And here the sweep STOPS**, on Dave's ruling 3 rather than on mine. The altitude declaration holds:
the AC checking machinery is sufficiently specified, the re-origination fixes named defects only, and
findings of the checking-of-the-checking shape do not block. This round's finding is inside ruling 3's
own named list (`AC-4`'s `aliases[]`) — it corrects that item's SHAPE and sweeps its class to one
sibling clause in the same span. It opens no further rung.

### Contradiction scan — what this round's claims now disagree with

Run over the whole document for every claim added or edited this round, because a paragraph that is
right against the code and wrong against another section leaves the item buildable two ways.

- **`## Approach`'s old "normalizes three identifier-bearing fields" sentence** — REWRITTEN in place,
  not left standing beside the new one.
- **Finding I's opening "three fields, not two" analysis** — still correct and deliberately kept; the
  new subsection narrows what the *obligation* may be, not what the code does. Stated explicitly at
  the top of the subsection so the two are not read as competing.
- **`### Examples of done` scenario 3** — genuinely contradicts the arm-shape split. NOT resolved
  here: it is signed, so it is staged in the brief with both closures. This is now the SECOND known
  place the document is buildable two ways until Dave re-originates; the first is Tier A's undeclared
  clause, which architect round-4 note 1 and round-5 note 4 both record. Both are in the brief, and
  the brief is one round.
- **`AC-4`'s signed `desc`** — names `emails[]`/`phones[]` only, so it does not yet contradict the
  split; it is silent where the split speaks, which is exactly the gap the re-origination fills.
- **Finding D's "REPLACE" classification of `_extract_email_and_name`** — now says explicitly that the
  edit is to the ENCLOSING method. No other section claimed a local swap; `## Approach`'s "the code
  being replaced" phrasing is now backed by a stated fate rather than implying one.
- **One contradiction this scan found that no gate raised, and it is fixed rather than recorded:**
  `## Approach`'s routing-wall paragraph still carried the round-3 pin *"no arm hardcodes a literal or
  defaults it to `None`"*, which architect round-4 note 2 corrected and which the re-origination
  brief's `AC-1` entry has carried in its corrected form since the round-5 fold. The document was
  stating the same pin two ways, one of them too strong on two arms that legitimately have no
  declaration to pass (D7, and D1b/D1c in the undeclared cell). `## Approach` is unsigned, so this is
  a fix, not an escalation; it does not widen Dave's list.
- **Finding G's "relocates into a new stdlib-only leaf"** — checked against this round's own
  correction and it is NOT the same claim: `phone_normalization.py` genuinely is stdlib-only; what is
  no longer stdlib-only after the move is `identifier.py`, which now names one package sibling. Both
  sentences stand.

### Re-entry — unchanged in order and in length

1. **Dave re-originates `AC-1`–`AC-4` in ONE round** (Tier A + Tier B; `AC-5` unchanged), with
   `AC-4`'s `aliases[]` clause scoped by arm shape and one yes/no on `### Examples of done`
   scenario 3.
2. **One shell pass, alongside the re-origination:** **G1** and the amended **G2** (per field) in
   `## Grounding Still Owed`, plus the consumer audit's two greps. G3 stays withdrawn as moot.
3. **ac-red-team → architect → data-premise → spec-writer.** The architect's four rulings and the
   output contract carry forward and need no re-derivation.
4. **spec-writer.** With 1–3 done the spec is assembly: `## Carried Forward` plus the routing, the
   wall, the phone relocation, the splitter consolidation and the subsumption, the Tier-1 branch-unit
   reification, and the `lint_vault --fix` delta threading.

## Architectural Review — 2026-08-11 (round 6)

**Recommendation: REVISE — return to exploration**

**Round 6, cold-start re-spawn.** Read in role order: `architect.yaml`, this document in full (five
ac-red-team rounds, the `ac-signoff` fence, five prior architectural reviews, five data audits, six
spec-writer rounds, `## Conductor Rulings & Grounding`, `## Grounding Still Owed`, the re-origination
brief), then the code every new claim turns on (`writer.py`, `repositories/base.py`,
`repositories/person.py`, `repositories/book.py`, `repositories/meeting.py`, `identifier.py`,
`name_validation.py`, `tests/derivations.py`, `tests/test_write_routing.py`,
`scripts/lint_vault.py`), plus `LESSONS.html`. No shell in this cage; the live vault was not read —
the counts used below are the conductor's, cited as such.

**My round-5 blocking issue is CLOSED, and closed correctly.** The round-6 fold's arm-shape split
re-derives from source at every leg (table below), and its two additions the review did not have —
the mirror migration M2 and the byte-identity correction to what "in place" can mean — are both
right and both matter. The finding below is new, it is a defect in the door set itself rather than in
the checking of it, and it lands inside `AC-1`, which is already on ruling 3's named list. It has to
be right before Dave signs, for the same reason round 5's did.

### Trigger check

Three fire, unchanged: **two** new modules (the gate and the phone leaf); a contract change crossing
into three downstream repositories installed with `pip install -e`
(`docs/backlog-campaign-2026-07-05.md:98`); a derived-wall enforcement mechanism that must be
designed rather than copied. Effort stated at one to two sessions.

### Round-5's blocking issue — verified closed from source

Re-derived this round rather than accepting the fold's account of itself. All confirm.

| Claim the round-6 fold makes | Where I read it | Result |
|---|---|---|
| M1 is a MOVE, not a normalization: the extracted address is appended to a *different* list, guarded by the `emails[]` pass's own set | `person.py:1324-1329` — `person.emails.append(email)` at `:1328`, `seen_emails_lower` populated at `:1303`, `:1307-1316` | confirmed |
| M2 is the mirror and has the identical shape | `person.py:1311` collects, `:1339-1342` appends, `:1343` rebinds, deduped at `:1340` | confirmed |
| `update_fields` merges by key REPLACEMENT, so an emitted destination key overwrites rather than appends | `base.py:451` (`frontmatter.update(updates)`) | confirmed |
| The merge at the destination is replace / guarded / whole-record at **all ten** arms — not one appends | `writer.py:127` (guarded), `:259-261`, `:263`, `:332`, `:384`, `:419`; `base.py:451`; `lint_vault.py:876-882` | confirmed — I re-walked the table rather than the one arm, and it holds |
| "In place" on an address-bearing alias would DESTROY the address half, so byte-identity is the only safe dict-arm rule | `person.py:1291-1298` (the split), `:1331-1333` (display half only), `:1448` (bare-address seed → empty display → dropped) | confirmed |
| The gate is idempotent by construction | after pass 1 an alias is display-only, so `_extract_email_and_name` returns `("", "")` at `:1298`; M2's `:1340` finds the display half present | confirmed — I traced both passes |
| `_extract_email_and_name` is an INNER function, so "REPLACE" is an edit to the enclosing method | `person.py:1286`, nested inside the static method at `:1277-1278` | confirmed |
| Finding G's two corrections | `MIN_DIGITS: ClassVar[int] = 7` on `Phone` (`identifier.py:228`), consumed at `:238-239` and `:274`; `identifier.py`'s purity claim is in the docstring (`:1-29`), the import block is `:31-36` | confirmed |

That is the right answer to round 5. The cross-field move really is expressible only where the gate
holds the whole record, the fold found the second one before it was raised, and the class sweep it
declared — *every* destination merge in the ten, not just D4's — is what makes the entity-arm/dict-arm
split a rule instead of a special case. I add nothing to it.

### Blocking issue — two of the ten "arms" are not arms under this document's own definition, and the wall's predicate cannot resolve them

`AC-1` states the derivation unit: *"one member per distinct binding of the dict a function
serializes, so a function with N such branches contributes N members — never the function."*
`## Approach` and Finding B state the set as **ten arms across eight functions**, and `AC-1(a)` pins
that as a floor asserted by `(qualname, arm)`. Read against the source, two of the ten named members
bind no dict and serialize nothing:

- **D2 `BaseRepository.save` (base.py:356-401).** It computes `filename = f"@{name}.md"` (`:381`) and
  calls `write_markdown_file(file_path, entity=entity, body=…, extra_fields=…, overwrite=…)`
  (`:387-395`). No frontmatter dict is bound in its body; `extra_fields` is passed through, not
  serialized.
- **D3 `PersonRepository.save` (person.py:1255-1275).** It calls `_normalize_address_fields(entity)`
  (`:1269`) and `super().save(...)` (`:1272`). It binds nothing at all.

**This document already applies that exact test the other way, to code I have now read and found
structurally identical.** Architect round-1 note 4 excludes the sibling saves — *"`MeetingRepository.save`
(meeting.py:192) and `BookRepository.save` (book.py:170) call `write_markdown_file(entity=…)` directly
… They are correctly *not* arms under AC-1's definition — they bind no dict they serialize, and they
inherit gating at D1a"* — and that note has stood unchallenged through five rounds and is carried in
`## Carried Forward`'s standing-notes line. Read side by side, `book.py:167-178` and
`meeting.py:189-200` differ from `base.py:381-395` in exactly one expression: the filename derivation
(`self._get_file_name(entity)` vs `f"@{name}.md"`). Everything the arm predicate looks at is the same
in all three. So the ten-arm set puts two members and two non-members on opposite sides of a boundary
that does not separate them.

**The existing derivation vocabulary confirms the direction rather than rescuing it.**
`functions_reserializing_parsed_frontmatter` (`derivations.py:294-310`) is a parse→serialize data-flow
predicate whose own docstring records that it *rejects* `write_markdown_file` because that function
"builds what it writes from its own entity/frontmatter ARGUMENTS" (`:299-302`). Neither `save` calls
`parse_frontmatter` at all, so neither is reachable by that family either. The eight arms that ARE
resolvable by a binds-and-serializes predicate are D1a (`writer.py:257`), D1b (`:259-261`), D1c
(`:263`), D4 (`base.py:439`→`:454`), D5 (`writer.py:329`→`:335`), D6 (`:381`→`:387`), D7
(`:419`→`:421`) and D8 (`lint_vault.py:876-882`). The floor names ten.

**The trilemma, and every branch is bad.** This is why it is blocking rather than a wording note:

1. The build implements the stated predicate → the sweep resolves eight, `AC-1(a)`'s ten-member floor
   is RED, and the derived wall — the entire enforcement mechanism of Approach F — cannot go green
   against the tree it is written for.
2. The build hard-codes the two saves → `AC-1`'s *"DERIVED by an AST sweep (never enumerated)"* is
   violated at precisely the two members, which is the vacuity hole ac-red-team round 1 spent a round
   closing.
3. The build widens the predicate to "calls a write function with an entity" → `BookRepository.save`
   and `MeetingRepository.save` join the set, so two non-person repositories acquire gate call sites,
   the ten-arm count is wrong in the other direction, and `AC-2`/`AC-4`'s exclusion sets — asserted by
   EQUALITY, which is what closed round 1 — no longer reconcile.

**Underneath it is a design question nobody in twelve rounds has asked: does a gate call belong at D2
at all?** D3 has an independent reason to exist and the fold supplies it — Finding I's rider requires
`PersonRepository.save` to write the gate's normalized values back onto the entity so today's in-place
model mutation survives, and no other frame can do that. D2 has no such reason. It binds no dict, and
every byte it produces reaches the seam through D1a one frame later, where the gate already fires on
`model_to_frontmatter`'s projection of the same entity. Finding F's spurious `@Dave/` directory is
closed there too, not here: `vault_io.ensure_dir` is at `writer.py:273`, downstream of the convergence
point at `:266`, so a refusal at D1a precedes the `mkdir`. On the evidence I can read, the D2 gate call
is pure redundancy — and it is one of the three invocations `## Approach` cites when it requires
idempotency (*"one `PersonRepository.save` passes through THREE arms — D3 → D2 → D1a"*). Idempotency is
still required for D3 → D1a, so nothing is lost by dropping D2; what is lost is a member the wall
cannot derive.

**What has to change, in the exploration first.** Finding B's door table and `## Approach` must either
(a) state what makes `BaseRepository.save`/`PersonRepository.save` arms when `BookRepository.save`/
`MeetingRepository.save` are not — a distinction I could not find in the source and which, if it
exists, is a second predicate the wall must ship its own controls for — or (b) drop D2 from the arm
set and record that entity-shaped writes are gated at D1a, with `PersonRepository.save` carrying one
gate call that is a *rider* (the entity write-back) rather than an arm, explicitly outside the derived
set and pinned by its own fixture. **(b) is the shape I would take**, and it is cheap: it makes the
derived set exactly the eight sites a single stated predicate resolves, it removes the redundancy, and
it leaves every behaviour this item promises intact. Either way `AC-1`'s floor moves — it is signed,
and `AC-1` is already open in Dave's one round for the pass-what pin, so this lands in the same edit
rather than in a round of its own.

### Why this is not a new rung of the LESSONS #38 ladder

Stated because ruling 3 makes the distinction load-bearing and I am the gate that escalated for it.
The finding is not "the sweep's unit is too coarse" (round 4's) or "the AC names a container that does
not span its surface" (the round-2 hand-back's). It is that the **door set** — the design's central
object, stated in unsigned text at `## Approach` and Finding B — contains two members that fail the
document's own membership test, while two structurally identical sites are correctly excluded by that
same test in this document's own carried-forward notes. That is "the thing is wrong", which round 3's
regress analysis explicitly holds outside the ladder, and it lands inside a criterion ruling 3 already
enumerates. It opens no higher altitude and I ran no new generator sweep.

### Rulings carried forward — settled, do not re-derive

All five stand, re-checked against the code this round. Nothing above reopens any of them — this
finding is about which SITES are in the set, not about what the gate receives, emits, or is handed.

- **Gate signature:** no `existing` parameter, one entry point taking the introduced fields plus the
  entity type; entity arms project through `model_to_frontmatter` (`writer.py:88-130`) first.
- **Splitter:** TOTAL, returns `(address | None, display)`, owns the parens form before delegating,
  maps `IdentifierError` to "not an address"; `Email.parse`'s angle-bracket gate
  (`identifier.py:141-149`) is NOT widened.
- **DECLARE:** the gate is handed its semantic context and never consults the filesystem. Adopted by
  Dave (ruling 1), folded, and re-verified — `_owns` is consulted nowhere in the design.
- **The phone authority relocates to a leaf** (`obsidian_schemas/phone_normalization.py`), ratified in
  round 5 and unaffected by this finding.
- **The gate's OUTPUT contract and the arm-shape split** — ratified this round from source, above.

### Review — only what changed

**Fit / Duplication / Reversibility / Generalization / Prior art:** as rounds 2–5 recorded them.
Approach F remains right; `tests/test_write_routing.py:1-18` remains the precedent `AC-1`'s battery
copies, and reading it this round sharpens why it is the right precedent: it plants a scratch module
and drives it *through the same function the live wall calls* (`test_write_routing.py:22-37` imports
from `tests.derivations` rather than re-implementing), which is exactly the discipline the finding
above says the two `save` members cannot survive. No cited execution is owed.

**Boundaries:** the residual boundary question is now the wall's, not the gate's. A derived set whose
membership rule cannot be stated once is a set maintained by hand under an AST costume, and the
eleventh-arm guarantee — the thing that makes this item worth building rather than adding six checks —
is exactly what it stops delivering. Everything else is unchanged and right: the generic layer derives
no entity type, the person rules live inside the gate, `vault_io` keeps its single reason to exist.

**Determinism boundary (LLM vs code):** n/a for LLMs; the item is the opposite move throughout. The
dimension's underlying principle is what the finding turns on, though — a membership fact that is
mechanically derivable for eight sites and asserted by hand for two is the same shape one level down.

**Cost & maintenance:** unchanged at one to two sessions plus the Tier-1 branch-unit reification and
the D8 delta threading. Taking shape (b) *reduces* cost: eight derived members instead of ten, one
predicate instead of two, and two fewer call sites to wire.

**Build vs extend vs integrate:** extend, correctly, with one symbol moving first.

### Notes (non-blocking)

1. **Finding I's door-introduced alias is not in the delta the gate judges, and the sentence says it
   is.** Finding I states that `update_fields`' old-stem alias (`base.py:443-448`) "is a
   door-introduced field and therefore inside the delta the gate judges". Read from source, the stem
   is appended to the *parsed* `frontmatter["aliases"]` at `:445-448`, while `updates` — the delta —
   is the caller's dict, merged only at `:451`. A gate handed the delta never sees that entry. The
   OUTCOME the finding asserts is right (it passes through unchanged), so nothing behavioural turns
   on it; the sentence would just send the build looking for it in the wrong object. One clause.
   Adjacent and pre-existing, worth a line in the spec rather than scope: a call carrying BOTH `name`
   and `aliases` in `updates` loses the stem the door just appended, because `:451` replaces the list
   `:448` had just mutated. That is parked defect 1's neighbourhood, not this item's.
2. **The two unresolvable `identifier.py:MIN_DIGITS` citations are both inside prose that names the
   slip itself** (`## Architectural Review` round 5 note 1, and the round-5 data audit's citation-slip
   paragraph). Finding G's table now cites `identifier.py:Phone:228` correctly. No action — recorded
   only so a citation-drift sweep's two hits are not read as a live defect.
3. **Rounds 1–5's standing notes all carry:** the dedicated `pattern` attribute rather than
   overloading `declared_type` (`base.py:267-269` feeds it back into `_owns`); the new `REASONS`
   literal chosen at spec time (`errors.py:110-127`, closed frozenset of fifteen; `bounded_message`
   raises on any non-member at `:139-145`); `lint_vault --fix`'s missing delta object; the
   `book.py`/`meeting.py` `save` overrides that are correctly not arms — now load-bearing rather than
   incidental, per the blocking issue; and the three-functions-one-shape collapse, still a separate
   work item and still not recommended for absorption.
4. **The document is still buildable two ways until Dave re-originates** — `## Approach` refuses an
   undeclared write, `AC-2`/`AC-4` as signed gate an untyped dict "exactly as a `type: person` one
   is"; and `### Examples of done` scenario 3 now contradicts the arm-shape split. Both are staged in
   the brief, both correctly declined by the fold as signed text, and neither is re-raised here.

### Arc note — convergence, and the re-origination is one clause from ready

The six architect rounds have each closed their target and moved to a different one: the Company
annexation (1) → its structural sharpening plus the missing Tier-1 table (2) → the DECLARE ruling plus
the `AC-1` pass-what gap (3) → the phone authority (4) → the `aliases[]` migration's expressibility
(5) → the door set's own membership rule (6). Round 5's target is closed and verified from source
above; no target has been re-raised. This round's finding sits inside `AC-1`, which ruling 3 already
opens, and it is the last thing I can find that would otherwise be discovered after the re-sign. The
queued order stands unchanged and does not lengthen: Dave re-originates `AC-1`–`AC-4` in ONE round
(with `AC-1`'s floor corrected to the derived set a single stated predicate resolves, plus the
pass-what pin), one shell pass runs G1 and the amended G2 plus the consumer audit's greps, then
ac-red-team → architect → data-premise → spec-writer.

```verdict
gate: architect
verdict: REVISE
date: 2026-08-11
model: claude-opus-5
targets: AC-1, #approach, #exploration-notes
note: Round 5's aliases[] finding is closed and every round-6 claim re-derives (M1/M2 at person.py:1328/:1339-1342, the all-ten-arm merge table, idempotency via :1298/:1340, the nested-inner-function subsumption) — but two of the ten named arms bind no dict and serialize nothing (BaseRepository.save at base.py:381-395, PersonRepository.save at person.py:1269-1272), so AC-1's own unit cannot derive them, while this document's carried-forward note 4 excludes BookRepository.save/MeetingRepository.save on that exact test against code I read as structurally identical (book.py:167-178, meeting.py:189-200) — leaving the wall's predicate resolving 8 against a signed floor of 10, with hand-listing or widening as the only alternatives.
```

## Data Audit — 2026-08-11

**Recommendation: REVISE — return to exploration**

**Round 6, cold-start re-spawn.** Read in role order: `data-premise.yaml`, this document in full
(five ac-red-team rounds, the `ac-signoff` fence, six architectural reviews, five prior data audits,
six spec-writer rounds, `## Conductor Rulings & Grounding`, `## Grounding Still Owed`, the
re-origination brief), then the code every premise below turns on. Same method bound as every prior
round in this cage: **no shell — this spawn has no Bash tool at all — scope limited to this tree's
files, and the live vault was not read.** The counts used below are the conductor's, cited as such.
Every citation was re-derived from source this round rather than inherited.

**What moved, and what this round is for.** The round-6 fold answered my round-5 finding as far as a
shell-less actor can, and the round-6 architectural review then landed a new blocking issue in the
door set. This round has three parts: discharge what the fold discharged, verify the architect's new
finding from source and state its (nil) data consequence so Dave's one round does not have to
rediscover the interaction, and name one Class-1 claim the round-6 fold's own arm-shape split
created that no owed query sizes — and that the fold explicitly classifies as *not* a regression on
a comparison I read as incomplete.

### Trigger check

**Class 1 AND Class 2 — both still fire.**

- Class 1 (data-distribution / field-presence): three quantified claims about live entries remain
  unmeasured — G1's undeclared population at the rule's own scope, G2's cells per field, and (new
  this round) the population of stored `emails[]` entries whose display half is not already present
  in the same note's `aliases[]`, which is the population the dict-arm rule destroys.
- Class 2 (rule-effect-against-existing-corpus): rule (ii) is still a new refusal rule whose effect
  is known for `@*.md` (count 1) and unknown everywhere else it reaches; the splitter consolidation
  is a new acceptance predicate never run over the stored entries it will judge.

### My round-5 finding — discharged as far as this cage allows

| Round-5 ask | Status |
|---|---|
| **G2 must report its cells PER FIELD** before `AC-4`'s `aliases[]` clause is signed, because the `aliases[]` *extracted* cell IS the address-bearing-alias population the arm-shape split forks | **DELIVERED as a statement.** Finding D's predicate, `## Grounding Still Owed` G2, and Finding D's new "why the per-field split" paragraph all carry it, with both halves' purposes stated separately. **NOT RUN.** |
| The document's two incompatible readings of that population | **Correctly preserved rather than resolved by argument.** Finding D now states both — Finding I's `create_stub` seed (`person.py:1448`) as the existence proof, and parked defect 2's erasure — and says the count decides. I re-read the loop this round: for a bare-address alias, `parseaddr("a@b.com")` yields `("", "a@b.com")`, `:1292` accepts it, `:1327` finds it already in `seen_emails_lower` from the `emails[]` pass so nothing is appended, and the empty display half means `:1331-1333` appends nothing — the entry is dropped. The erasure is real, and the fold is right to let the number settle it. |

### Verified from source this round

Re-derived rather than inherited. All confirm.

| Claim | Where I read it | Result |
|---|---|---|
| `BaseRepository.save` binds no frontmatter dict and serializes nothing — it derives a filename and passes `extra_fields` through | `base.py:356-401`; `filename = f"@{name}.md"` at `:381`, `write_markdown_file(...)` at `:387-395` | confirmed — architect round 6 holds |
| `PersonRepository.save` binds nothing at all | `person.py:1255-1275` — `_normalize_address_fields(entity)` at `:1269`, `super().save(...)` at `:1272` | confirmed |
| `BookRepository.save` / `MeetingRepository.save` are structurally identical to `BaseRepository.save` apart from the filename expression | `book.py:167-178`, `meeting.py:189-200` — both `self._get_file_name(entity)` then the same `write_markdown_file(entity=…)` call | confirmed — the two excluded sites and the two included ones really do sit on opposite sides of a boundary that does not separate them |
| `_writeback_identifier` passes the WHOLE stored list, not the new entry | `person.py:1204-1217` — `person.emails = list(person.emails or []) + [email]` then `updates["emails"] = person.emails`, routed through `update_fields` at `:1217` | confirmed — this is what sets the blast radius of the finding below |
| the three unresolved `identifier.py:MIN_DIGITS` citations are all inside prose that names the slip | doc `:4258` (architect round-5 note 1), `:4353` (data round-5 citation-slip paragraph), `:4784` (architect round-6 note 2, which names the other two) | confirmed — benign; Finding G's table cites `identifier.py:Phone:228` correctly. No live citation defect. |

**The architect's round-6 finding has no data consequence, and saying so is worth one line.** Whether
the derived set is ten arms or the eight a single stated predicate resolves, the *dict-shaped* half
is unchanged — D1b, D1c, D4, D5, D6, D8 — and that is the half every arm-shape-scoped clause in
`AC-4` turns on. Dropping D2 moves `PersonRepository.save` from "entity-shaped arm" to "rider on
D1a"; the migrations still run where the gate holds the whole record, because D1a is where the
projection is. So `AC-1`'s floor correction and `AC-4`'s arm-shape clause can be signed in the same
round without interacting. Stated because both land in Dave's one round and nothing else in the
document says they are independent.

### Finding — the dict-arm rule DESTROYS a display half that is on disk today, and the document books it as costless

This is the one new thing this round adds, and it is a data question, not a design preference.

The round-6 fold's arm-shape split rules that on a dict-shaped arm the gate normalizes `emails[]` in
place and performs no migration, so **the extracted display half is DROPPED** (`## Approach`,
Finding I's M2 row). The fold then prices that:

> "It is *not* a regression — today no dict arm normalizes anything, so today the display half is not
> in `aliases[]` either, and the entry is stored raw on top of that. What it costs is the second half
> of one signed `### Examples of done` scenario."

**The comparison is against `aliases[]` only, and that is the wrong baseline.** Today a dict-arm
write stores `"Al B <a@b.com>"` verbatim, so the display half **is on disk** — embedded in the
`emails[]` entry, recoverable by anything that re-splits it, which is exactly what
`_normalize_address_fields` does on the next entity write. Under the new rule that same write stores
`"a@b.com"` and drops `"Al B"` with no destination, so the display half leaves the note entirely.
That is not "not migrated"; it is deleted, and it is deleted by the fix.

**The blast radius is not one entry per write.** `_writeback_identifier` sets
`updates["emails"] = person.emails` (`person.py:1207`) — the whole list, loaded from the note — and
routes through `update_fields` (`:1217`), which is D4. So a single reuse-branch write-back, the
item's own scenario 3, passes **every** stored `emails[]` entry on that person through the gate at a
dict arm, and every one of them that still carries a display half loses it in that one write.
`update_frontmatter_field(path, "emails", …)` (D5) and the D1b/D1c dict arms have the same shape.

**The at-risk population is nameable and is not the same as G2's `emails[]` extracted cell.** A
person previously saved through `PersonRepository.save` has already had M2 run, so the display half
is in `aliases[]` and losing it from `emails[]` costs nothing. The entries that lose real information
are those where the display half is **absent from that note's `aliases[]`** — the notes never
re-saved through the repository since WI-109. G2 as amended reports the *extracted* cell per field;
it does not report that intersection, and the intersection is the number.

**What this does not claim.** It is not an argument against the arm-shape split — the split is
forced, and the architect's round-5 derivation plus the fold's all-ten-arm merge table (which I
re-walked: `writer.py:127` guarded, `:259-261`, `:263`, `:332`, `:384`, `:419`; `base.py:451`;
`lint_vault.py:876-882` — not one appends) are right that emitting the destination key on a dict arm
would REPLACE the stored list. Both options are lossy; the question is which loss, and how big. The
cheap third option the fold already names for scenario 3 — closure (b), have
`_writeback_identifier` pass `aliases` in the same `updates` dict — happens to close this too, for
that one caller, which is worth knowing when Dave picks between (a) and (b): (a) is free on the
example and leaves this deletion in place; (b) closes both. That is Dave's call and I am not making
it. What the gate requires is that the clause be signed against the number rather than against the
sentence "not a regression".

**Why this is inside ruling 3's list rather than a new rung.** It is not a finding about the checking
machinery. It is a behavioural data-loss claim about the design, and it corrects the SHAPE of an item
already on Dave's list (`AC-4`'s identifier clause and the `### Examples of done` sibling entry),
exactly as the architect's round-5 finding did. It opens no higher altitude and I ran no generator
sweep.

### Required grounding

Nothing is added to the shell pass. Two queries carried, one amended by one column.

1. **G1 — unchanged and still unrun.** Rule (ii)'s undeclared population at the rule's own
   path-agnostic scope, with the untyped-frontmatter / no-frontmatter split and the path-class split.
   It does not gate the rule's direction (fail-closed, Dave's ruling 2); it sizes the target set the
   consumer audit intersects, and it is what build-start re-grounding re-runs.
2. **G2 — amended: within the `emails[]` *extracted* cell, additionally report how many entries have
   a non-empty display half whose value is NOT already present in that note's `aliases[]`.** That is
   the population the dict-arm rule deletes. Same pass, same corpus, one more column on a query
   already owed and already being reported per field.
3. **The consumer audit** — unchanged, still owed, still not a vault query: non-`create_stub` write
   callers across HAL9000, exocortex and orchestrator, plus importers of
   `obsidian_schemas.repositories.person.normalize_phone` / `phones_match`. The in-tree half stays
   grounded; the three `pip install -e` consumers are outside this tree.

### Conclusion

The item's data position is the best it has been: the premise that blocked rounds 1–3 is deleted
rather than argued away, Finding C is honestly re-dated to a spent number, the sentinel exemption is
justified against a real population of three, G3 is correctly withdrawn, and every structural
citation I checked this round re-derives — including the architect's new door-set finding, which I
confirm, and the three citation-drift hits, which are all benign prose.

What stops this being a PROMOTE is unchanged in kind and one item larger in extent: **G1 and G2 have
still never been executed**, and the newest design decision — the arm-shape split — is heading into a
signed criterion carrying a data-loss class the document prices at zero on an incomplete comparison.
Promoting now would release the D3 brake at exactly the moment `AC-4`'s clause is written against an
unmeasured fact, which is the failure this gate exists to prevent one station earlier. Stage stays at
`exploring`.

**Signal for the factory, stated because the targets line alone cannot carry it.** This is a
converging round and the arc is visible in what closed: rounds 1–3 named the untyped-dispatch premise
(closed, deleted by ruling 1); round 4 named the count's scope and two unnumbered deltas (one moot,
one enumerated, one re-scoped, all discharged); round 5 named the per-field split on G2 (delivered as
a statement this round, and I withdraw it as a document defect). This round names a different thing
again — a deletion the fold classifies as costless — and asks for one more column on a query already
queued. **What has not moved is the thing no gate spawn can move**: G1 and G2 need a shell and vault
access outside every cage, and this spawn has no Bash tool at all, so the predicates are not merely
unrun but unrunnable here. A seventh data-premise spawn before those numbers exist will reproduce
this section, as rounds 2 and 3 did. The unblock is unchanged and is one pass: Dave re-originates
`AC-1`–`AC-4` (with `AC-1`'s floor corrected to the set one predicate resolves, and `AC-4`'s
`aliases[]`/`emails[]` clauses scoped by arm shape and priced against the deletion above), and the
same shell-holding actor runs G1 and the twice-amended G2 alongside it.

```verdict
gate: data-premise
verdict: REVISE
date: 2026-08-11
model: claude-opus-5
targets: AC-4, #exploration-notes, #approach
note: Round 5's per-field ask is delivered as a statement and withdrawn as a defect, and the architect's round-6 door-set finding is confirmed from source (base.py:356-401 and person.py:1255-1275 bind no dict; book.py:167-178 / meeting.py:189-200 are structurally identical to the excluded pair) with nil data consequence — but the round-6 arm-shape split DELETES data it prices at zero: today a dict arm stores `"Al B <a@b.com>"` verbatim so the display half is on disk, and the new dict-arm rule stores the address and drops it with no destination, at whole-list scale because `_writeback_identifier` passes `updates["emails"] = person.emails` through D4 (person.py:1207/:1217) — the at-risk population (extracted `emails[]` entries whose display half is absent from that note's `aliases[]`) is one more column on G2, and G1/G2 remain unrun and unrunnable in this cage.
```

## Spec-Writer Fold — 2026-08-11 (round 7)

**This round PRODUCED a fold, not a hand-back.** Both round-6 verdicts name a signed criterion in
their targets (`AC-1`, `AC-4`), but neither asks me to edit one: the architect's finding is explicitly
about what `AC-1`'s floor must say **before** Dave signs it and lands *"in the same edit"* as the
pass-what pin already queued; the data gate's is one more column on a query already owed plus a
correction to how unsigned text PRICES a consequence. The text that carries both is unsigned —
Finding B, Finding C, Finding D, Finding I, `## Approach`, Constraints, `## Grounding Still Owed`,
`## Carried Forward` and `## Re-origination Brief` — so this round writes.

Cold-start, read in role order: `spec-writer.yaml`, this document in full (five ac-red-team rounds,
the `ac-signoff` fence, six architectural reviews, six data audits, six prior spec-writer rounds,
`## Conductor Rulings & Grounding`, `## Grounding Still Owed`, the re-origination brief), the project
`CLAUDE.md`, then the code every claim below turns on. Every citation re-derived from source this
round, not inherited: `repositories/base.py` (`save`, `update_fields`), `repositories/person.py`
(`save`, `_normalize_address_fields` and its inner `_extract_email_and_name`, `_writeback_identifier`),
`repositories/book.py` (`save`), `repositories/meeting.py` (`save`), `writer.py`
(`write_markdown_file`'s three arms, the convergence point, `ensure_dir`, both `update_frontmatter_*`,
`roundtrip_file`), `tests/derivations.py` (`_is_write_call`,
`functions_reserializing_parsed_frontmatter`), `errors.py` (`REASONS`, `bounded_message`). This cage
has **no shell**; the live vault was not read — the counts used are the conductor's, cited as such.

### What this round wrote

| Section | Change | Answers |
|---|---|---|
| **Finding B** — new membership note under the door table, and a new subsection *"The two `save` methods bind NOTHING, so the set is eight arms across six functions"* | The four-site table (`base.py:356-401`, `person.py:1255-1275`, `book.py:167-178`, `meeting.py:189-200`) showing the two included and the two excluded sites differ in exactly one expression; the trilemma restated; the derivation-vocabulary check (`derivations.py:294-310` cannot reach either `save`); the corrected eight-arm set; and what happens at D2 (no gate call — Finding F closes at D1a, upstream of `ensure_dir` at `writer.py:273`) and D3 (one gate call, as a RIDER outside the derived set). | architect round 6, blocking |
| **Finding B** — declaration table, undeclared-cell bullets, seam paragraph, re-origination note | Re-counted to *six of the eight*; the D2/D3 row becomes the D3 rider's; "repository arms D2, D3, D4" becomes "D4 and the rider"; "entity-shaped arm D1a, the only one"; the six `write_frontmatter` call sites are recorded as corroborating the six-function count; and the note that both signed exclusion sets now name two NON-members. | architect round 6 |
| **Finding C** | The delta rule's "entity write (D1–D3)" restated as D1a plus the rider — same rule, corrected frames. | architect round 6 |
| **Finding I** — the M2 cost paragraph | **Rewritten.** The round-6 pricing (*"not a regression"*) is retracted as measured against the wrong container: the display half is on disk today INSIDE the raw `emails[]` entry, so the dict-arm rule DELETES it, at whole-list scale via `_writeback_identifier` (`person.py:1206-1207`, `:1217`). The at-risk population named, booked to G2, and closure (b) recorded as the one that closes it. | data-premise round 6, blocking |
| **Finding I** — the door-introduced alias | **Corrected**: the old stem is appended to the PARSED frontmatter (`base.py:445-448`), not to `updates`, so a gate handed the delta never sees it; the outcome is unchanged. The adjacent `name`+`aliases` stem-loss defect parked to defect 1's neighbourhood. | architect round 6, note 1 |
| **Finding I** — arm-shape and idempotency riders | "D1a/D2/D3" → D1a and the rider; "three arms (D3 → D2 → D1a)" → twice; the write-back named explicitly as the rider. | architect round 6 |
| **Finding D** — the reconciliation-2 predicate | One more column: within the `emails[]` *extracted* cell, entries whose non-empty display half is not already in that note's `aliases[]`. | data-premise round 6 |
| **`## Approach`** | Header note records both corrections; six-of-eight declaration count; the entity bullet is D1a + rider; the dict bullet states the deletion explicitly; the subsumption paragraph names the rider; "route all ten arms across eight functions" → eight across six plus the rider; idempotency twice; "eleventh arm" → ninth. | both round-6 gates |
| **Constraints — Effort** | Eight arms across six functions plus one rider, with the note that shape (b) *reduces* the work. | architect round 6 |
| **`## Grounding Still Owed`** — G2 | The deletion column added, with its own purpose stated beside the other two. G1 and the consumer audit unchanged. | data-premise round 6 |
| **`## Re-origination Brief`** | Header note records that the list did not grow. Tier A gains the non-member sentence with both exclusion sets restated over the eight arms. Tier B `AC-1` gains the floor correction (ten → eight) and the rider clause. Tier B `AC-4`'s dict-side sub-clause gains the deletion and its number. The Examples-of-done entry's (a)/(b) choice gains its consequence. | both round-6 gates |
| **`## Carried Forward`** | The `AC-1` floor bullet re-stated at arm granularity with the cardinality correction; the output-contract bullet re-stated at D1a + rider, with the deletion named. | both |

### Two things this round found that the reviews did not have

1. **The six `write_frontmatter` call sites ARE the six functions, and that is an independent
   confirmation of the corrected count.** Finding B has recorded since round 1 that all six
   `f"---\n{yaml}---\n"` constructions in the package and scripts are fed by one call, at
   `writer.py:266`, `:335`, `:387`, `:421`, `base.py:454` and `lint_vault.py:880`. Neither `save`
   appears in that list — they reach the seam only transitively, through D1a. So the document has
   carried the disproof of its own ten-arm count in the paragraph immediately above the count, for six
   rounds, and the corrected set is not a new claim about the code so much as the two paragraphs
   finally agreeing.
2. **Dropping D2 is not merely count-neutral — it is where Finding F is actually closed, and that is
   checkable.** `vault_io.ensure_dir(file_path.parent)` is at `writer.py:273`, DOWNSTREAM of the
   convergence point at `:266` (read from source this round). A refusal raised at D1a therefore
   precedes the `mkdir`, so `repo.save(Person(name="Dave/Bob"))` creates no `@Dave/` directory with no
   gate call at D2 at all. The design's most concrete promise survives the removal of the arm the
   document assumed was carrying it, which is what makes shape (b) safe rather than merely tidier.

### What this round still deliberately did NOT write, and why — unchanged from rounds 4, 5 and 6

**No Design, Edge Cases, Implementation Plan, Write Targets, Verification, or `criteria` refinement.**
The three reasons are unchanged and none has moved. `AC-1`–`AC-5` remain inside the `ac-signoff` hash
span (`ac_hash: a76ebad54da2`), and this round's own two findings land inside `AC-1`'s floor and
`AC-4`'s dict-side clause — both signed, both named wrong-on-facts by gates whose findings Dave has
accepted, so WI-061 routes them to re-origination rather than refinement. The plan and the criteria are
one object: a plan whose task-verify text points at `AC-1`'s ten-arm floor would have to be rewritten
the moment the floor becomes eight. And rule D3 refuses `→ specced` without a data-premise PROMOTE,
which the standing verdict is not.

### Class-shaped fold — declared, and still bounded by ruling 3

Per WI-226 the finding in front of me is not "the arm count was two too high" or "one cost sentence
compared the wrong thing". Both round-6 findings are instances of one generator, stated at source:

> **A SET or a BASELINE is carried forward by its label after the definition underneath it moved — so
> the label keeps naming what it named before the move, and nothing re-derives it because the label
> reads as already-verified.**

The ten came from rounds 1–3's FUNCTION-unit door set (D1–D8); round 4 changed the unit to the ARM and
produced the ten by expanding D1 into three and keeping D2…D8 as they stood — the label was carried,
not re-derived under the new unit, which is exactly why two members that the new unit cannot resolve
survived four further rounds. The *"not a regression"* baseline came from a comparison of
`aliases[]`-then vs `aliases[]`-now; the arm-shape split changed what the write STORES in `emails[]`,
and the baseline was carried rather than re-derived against the bytes.

**Enumerating what generates it and sweeping the members, as the rule requires.** The members are
every set-cardinality or baseline claim in this document whose defining rule has moved since the claim
was written. Re-derived, not inherited:

| # | Carried label | Definition that moved under it | Disposition |
|---|---|---|---|
| 1 | "ten arms across eight functions" | the derivation unit, function → arm (round 4) | **CLOSED this round** — eight across six |
| 2 | "eight of the ten arms already carry a declaration" | the arm set itself | **CLOSED this round** — six of eight |
| 3 | "one `save` passes through THREE arms (D3 → D2 → D1a)" | the arm set itself | **CLOSED this round** — twice (rider, then D1a) |
| 4 | "the eleventh arm someone adds next month" | the arm set itself | **CLOSED this round** — the ninth |
| 5 | "not a regression — the display half is not in `aliases[]` either" | what a dict arm STORES, once the split was adopted (round 6) | **CLOSED this round** — it is a deletion, sized by G2's new column |
| 6 | "six dict-shaped arms" (D1b, D1c, D4, D5, D6, D8) | the arm set | **HOLDS, re-derived** — neither `save` was ever dict-shaped, so the removal does not touch it |
| 7 | "four arms where the undeclared case is CONSTRUCTIBLE" (D1b, D1c, D5, D6) | the arm set | **HOLDS, re-derived** — same reason |
| 8 | "0 of 3,418" as rule (ii)'s justification | rule (ii)'s surface, once it was stated path-agnostically | **already CLOSED at round 5** — re-scoped to G1 |
| 9 | "1647 notes of legacy dirt" | the vault, two months on | **already CLOSED at round 4** — re-dated to 79/2 |
| 10 | "`REASONS`, a closed frozenset of fifteen" | `errors.py` | **HOLDS — re-counted from source this round**: fifteen literals at `errors.py:110-127` (one spans two source lines, `:114-115`), `bounded_message` raises on any non-member at `:139-145` |
| 11 | "ten refusals over ten branch-sites, one exemption" (Finding H) | `name_validation.py` | **HOLDS under its own stated unit** — nine chain branches plus `empty` as one refusal, which architect round 4 verified from source. It is checking-machinery, and ruling 3 closes it |
| 12 | "six disagreement classes" (Finding D) | `Email.parse` / `_extract_email_and_name` | **HOLDS** — neither implementation has moved; data-premise round 5 re-derived all six independently |

**Declared: I find no further open member.** Every remaining cardinality in the document either names
the rule that produces it in the same sentence (the eight arms, the six functions, the four
constructible arms) or is a live query rather than a stored number (G1, G2).

**And here the sweep STOPS**, on Dave's ruling 3 rather than on mine. The altitude declaration holds:
the AC checking machinery is sufficiently specified, the re-origination fixes named defects only, and
findings of the checking-of-the-checking shape do not block. Both of this round's findings are inside
ruling 3's own named list (`AC-1`'s pin, `AC-4`'s `aliases[]` clause) — they correct those items'
CARDINALITY and PRICE, not the machinery that checks them. Member 11 above is the one place this sweep
touched the machinery, and it is left where ruling 3 puts it. This round opens no further rung.

### Contradiction scan — what this round's claims now disagree with

Run over the whole document for every claim added or edited this round, because a paragraph that is
right against the code and wrong against another section leaves the item buildable two ways.

- **Finding B's round-4 header note** (*"the arm table and the ten-arm door set are unchanged"*) —
  genuinely contradicted the new count. FIXED in place with a forward pointer, not left standing.
- **Finding B's seam paragraph** (*"Every one of D1–D8 calls `write_frontmatter` … six call sites"*) —
  it said "calls" where D2/D3 only reach it transitively. Reworded to "reaches", and turned into the
  corroboration it always was.
- **Finding I's opening "three fields, not two" analysis** — unchanged and still correct: it describes
  what the CODE does, while the new pricing describes what the DESIGN costs. Not competing.
- **Finding I's own M1 half** — unaffected: M1's loss is the address, which the byte-identity rule
  already prevents by passing address-bearing aliases through unchanged. Only M2's half was mispriced.
- **`## Approach`'s dict-arm bullet and the brief's `AC-4` sub-clause** — both now carry the deletion,
  in the same words, rather than one carrying it and the other still reading "byte-identical and
  therefore free".
- **The round-6 fold's own all-ten-arm merge table** — deliberately NOT edited. It is a prior round's
  record and its conclusion is unchanged by the correction: its D2/D3 row already read *"reach bytes
  only through D1a"*, i.e. those two rows contributed no merge behaviour, so the table's finding
  ("every merge in the set is replace, guarded, or whole-record; not one appends") re-walks identically
  over the eight. Recorded here rather than restated there.
- **`### Examples of done` scenario 3** — still contradicts the arm-shape split, now on two counts
  rather than one. Still signed, still staged in the brief with both closures and, new this round, with
  the consequence that distinguishes them. This remains the SECOND of two places the document is
  buildable two ways until Dave re-originates; the first is Tier A's undeclared clause.
- **`AC-1`'s signed `desc`** — its floor now names two members the corrected set does not contain, so
  it does not merely under-specify, it disagrees. That is the re-origination obligation, not a fix.
- **Citation-drift note, recorded rather than actioned.** The pre-spawn sweep resolves four
  `identifier.py:MIN_DIGITS` citations that name no symbol. All four sit inside gate-authored sections
  and every one of them is prose *naming the slip itself* — architect round-5 note 1, the round-5 data
  audit's citation-slip paragraph, architect round-6 note 2, and the round-6 data audit's confirmation
  table. Both round-6 gates checked this independently and called it benign. Finding G's table, which
  is the live citation and mine, reads `identifier.py:Phone:228` and resolves. **No live citation
  defect, and no edit is available to me**: gate sections are theirs, not mine.

### Re-entry — unchanged in order and in length

1. **Dave re-originates `AC-1`–`AC-4` in ONE round** (Tier A + Tier B; `AC-5` unchanged), now with
   `AC-1`'s floor at eight arms plus the rider clause and the pass-what pin, `AC-4`'s `aliases[]`
   clause scoped by arm shape and its dict side priced against the deletion, and one yes/no on
   `### Examples of done` scenario 3 — where (b) closes the deletion and (a) does not.
2. **One shell pass, alongside the re-origination:** **G1** and the twice-amended **G2** (per field,
   plus the deletion column) in `## Grounding Still Owed`, plus the consumer audit's two greps. G3
   stays withdrawn as moot.
3. **ac-red-team → architect → data-premise → spec-writer.** The architect's rulings — gate signature,
   splitter, DECLARE, the phone relocation, the output contract and the arm-shape split — all carry
   forward and need no re-derivation.
4. **spec-writer.** With 1–3 done the spec is assembly: `## Carried Forward` plus the routing at eight
   arms and one rider, the wall, the phone relocation, the splitter consolidation and the subsumption,
   the Tier-1 branch-unit reification, and the `lint_vault --fix` delta threading.

## Architectural Review — 2026-08-11 (round 7)

**Recommendation: REVISE — return to exploration**

**Round 7, cold-start re-spawn.** Read in role order: `architect.yaml`, this document in full (five
ac-red-team rounds, the `ac-signoff` fence, six prior architectural reviews, six data audits, seven
spec-writer rounds, `## Conductor Rulings & Grounding`, `## Grounding Still Owed`, the re-origination
brief), then the code every claim below turns on (`repositories/base.py`, `repositories/person.py`,
`repositories/book.py`, `writer.py`, `name_validation.py`), plus `LESSONS.html`. No shell in this
cage; the live vault was not read — the counts used below are the conductor's, cited as such.

**My round-6 blocking issue is CLOSED, and closed with the shape I said I would take.** The round-7
fold takes shape (b): D2 leaves the derived set, D3 keeps one gate call as a rider, and the floor
moves to the eight arms one stated predicate resolves. Every leg re-derives from source (table
below), and the fold's two additions the review did not have — the six `write_frontmatter` call sites
being exactly the six functions, and the `ensure_dir`-is-downstream check that keeps Finding F closed
at D1a — are both right and both matter.

The finding below is new. It is a direct consequence of the arm-set correction my own round-6 ruling
ordered, which is why it belongs in this round rather than after the re-sign: the fold verified the
D2 removal against the REFUSAL case and against frontmatter bytes, and the case that breaks is the
ACCEPT-but-normalize one, on an object that is not a frontmatter byte.

### Trigger check

Three fire, unchanged: **two** new modules (the gate and the phone leaf); a contract change crossing
into three downstream repositories installed with `pip install -e`
(`docs/backlog-campaign-2026-07-05.md:98`); a derived-wall enforcement mechanism that must be
designed rather than copied. Effort stated at one to two sessions.

### Round-6's blocking issue — verified closed from source

Re-derived this round rather than accepting the fold's account of itself. All confirm.

| Claim the round-7 fold makes | Where I read it | Result |
|---|---|---|
| `BaseRepository.save` binds a FILENAME and serializes nothing — `entity=`/`extra_fields=` pass straight through | `base.py:380-382` (`name = getattr(entity, "name", "Unknown")`, `filename = f"@{name}.md"`, `file_path = …`), `:387-395` | confirmed |
| `PersonRepository.save` binds nothing at all | `person.py:1255-1275` — `_normalize_address_fields(entity)` at `:1269`, `super().save(...)` at `:1272` | confirmed |
| `BookRepository.save` differs in exactly one expression, the filename derivation | `book.py:167-178` — `self._get_file_name(entity)` at `:167`, then the identical `write_markdown_file(entity=…)` call | confirmed |
| the three fm-building arms converge on one `write_frontmatter(fm)` | `writer.py:256-257` / `:258-261` / `:262-263` → `:266` | confirmed |
| `vault_io.ensure_dir` is DOWNSTREAM of the convergence point, so a refusal at D1a precedes the `mkdir` and Finding F stays closed | `writer.py:273`, against `:266` | confirmed — the fold's key check for the removal, and it holds as far as it goes |
| `update_fields` merges by key REPLACEMENT, and the old stem is appended to the PARSED frontmatter rather than to `updates` | `base.py:443-448` then `:451` | confirmed — round-6 note 1's correction landed correctly |

That is the right answer to round 6, and the eight-arm set is the set one predicate resolves. I add
nothing to it.

### Blocking issue — the FILENAME is bound one frame above the first arm that judges the name, and the gate's name output is not an identity function

Dropping D2 leaves `base.py:381` — the only place a person note's path is chosen — upstream of every
gate call in the design. That is safe if and only if the gate either refuses or returns the name
BYTE-IDENTICAL. It does neither, and the document never says which of those two it does.

**Both public `NameValidator` entry points return a name that can differ from the one they were
handed.** Read from source this round:

| Entry point | What it returns | Read from |
|---|---|---|
| `validate_strict` | `_DOUBLE_SPACE_RE.sub(" ", name.strip())` — a strip AND a whitespace collapse, on the success path | `name_validation.py:257`, `:265-266`; `_DOUBLE_SPACE_RE` is `\s{2,}` at `:118` |
| `clean` | `CleanResult.cleaned_name` after the same two Tier-2 repairs, recorded as `strip_whitespace` / `double_space_collapse` | `name_validation.py:284-286`, `:293-297`; `CleanResult` at `:214-223` |

Neither is a predicate. `## Approach` commits the gate to returning "the fields it was HANDED —
normalized", and `name` is one of them.

**The concrete failure, and it is not hypothetical.** `repo.save(Person(name="Dave  Smith"))` — a
double space, Tier-2 dirty, refused by nothing:

1. `PersonRepository.save` runs the rider (`person.py:1269`'s replacement) and delegates (`:1272`).
2. `BaseRepository.save` binds `filename = "@Dave  Smith.md"` from the raw `entity.name`
   (`base.py:380-382`) and calls `write_markdown_file` (`:387-395`).
3. D1a fires the gate on `model_to_frontmatter`'s projection; the gate returns `name: "Dave Smith"`;
   `write_frontmatter` serializes it (`writer.py:257`, `:266`).
4. The note is created at `@Dave  Smith.md` carrying `name: Dave Smith`.
5. The next `save()` of the reloaded entity computes `@Dave Smith.md` (`base.py:381`) and mints a
   **second note for one person.**

That is parked defect 1's corruption class verbatim — *"`update_fields` renames the entity but never
the file … A later `save()` of the reloaded entity computes `@New.md` (base.py:381) and mints a
SECOND note for one person"* — arriving through `save` instead of `update_fields`, and **introduced
by this item's own fix**. Today the same call writes `name: Dave  Smith` into `@Dave  Smith.md`: no
door except `create_stub` touches a name, so the path and the field agree by construction. The
second-order consequence lands in the same frame: `_adopt(self._get_cache_key(entity), …)`
(`base.py:398`) keys the in-memory cache on the raw `entity.name.lower()` (`base.py:308-310`), so the
cache also disagrees with the note it has just written, until a refresh rebuilds it from the file.

**The existing create path is the proof that the ordering is load-bearing, and it is the ordering the
eight-arm set inverts.** `create_stub` cleans at `person.py:1407`, assigns
`name = clean_result.cleaned_name` at `:1413`, builds `Person(name=clean_name)` at `:1453`, and only
then calls `self.save(person, …)` at `:1475`. The cleaning is ABOVE the filename derivation — which
is why WI-105 never produced this divergence in two months of production. The corrected set moves the
first name judgement BELOW it for every non-`create_stub` entity write.

**Why the fold's own check did not catch it.** Its D2-removal argument is *"Nothing behavioural is
lost: every byte either `save` produces reaches the seam through D1a one frame later"*, plus the
`ensure_dir`-is-downstream check. Both are true, and both are about the refusal case and about
frontmatter bytes. The path is not a byte the seam produces — it is bound at `base.py:382` and never
revisited — so "reaches the seam one frame later" is exactly the property that does not cover it.
This is the round-7 fold's own declared generator, one member further on: *a label carried forward
after the definition underneath it moved.* "Entity writes are gated at D1a" was derived against
refusal; it is being relied on for normalization.

**What has to change, in the exploration first** — direction rather than design, and all three are
cheap because the document is already open at both places this lands:

- **(b′) Declare the gate's name output an IDENTITY** — refuse, or return the name byte-for-byte,
  with Tier-2 repair remaining a `create_stub`-only behaviour above the write path. Then no arm can
  emit a name any path disagrees with, for any entity type, with no rider and no ordering premise.
  `## Approach`'s "validated and normalized" has to say that *normalized* is address-side only. **This
  is the shape I would take**: it removes the coupling rather than sequencing around it.
- **(a′) State that the D3 rider's write-back includes the NAME**, not only the identifier fields its
  stated justification cites (`person.py:1317`, `:1343` are `person.emails` / `person.aliases`
  exclusively). `PersonRepository.save` is the only frame through which a Person reaches
  `base.py:381`, so this closes it for Person — but it widens the rider's reason from "preserve
  today's in-place mutation" to "preserve an ORDERING", which is a different and larger claim, and it
  leaves the property true only by a repository override rather than by construction.
- **(c′) Re-instate a gate call above the filename derivation** — round-6 shape (a). I rejected it for
  the reasons that still hold; recorded so the option set is complete rather than as a recommendation.

Whichever is chosen, `AC-1`'s rider clause — already staged in Tier B for Dave's one round — is where
the fixture pin changes: under (b′) the rider is pinned on identifier fields only and a separate
control asserts the gate never alters a `name`; under (a′) the rider's fixture must assert the name
write-back. That is one clause inside an item already on the list, so **Dave's round does not grow.**

### Why this is not a new rung of the LESSONS #38 ladder

Stated because ruling 3 makes the distinction load-bearing. This is not "the sweep's unit is too
coarse", not "the AC names a container that does not span its surface", and not a generator sweep at
a higher altitude — I ran none. It is a data-corruption path in the design: a specific input, through
the item's own primary door, producing two notes for one person where today it produces one. Round
3's regress analysis explicitly holds "the thing is wrong" findings outside the ladder, and Dave's
ruling 3 bounds only checking-of-the-checking. It also lands in unsigned text (`## Approach`, Finding
B's D2 paragraph, Finding I's rider) plus one clause of an `AC-1` entry already open.

### Rulings carried forward — settled, do not re-derive

All six stand, re-checked against the code this round. Nothing above reopens any of them — this
finding is about an object bound OUTSIDE the derived set, not about what the gate receives, emits, or
is handed.

- **Gate signature:** no `existing` parameter, one entry point taking the introduced fields plus the
  entity type; entity arms project through `model_to_frontmatter` (`writer.py:88-130`) first.
- **Splitter:** TOTAL, returns `(address | None, display)`, owns the parens form before delegating,
  maps `IdentifierError` to "not an address"; `Email.parse`'s angle-bracket gate is NOT widened.
- **DECLARE:** the gate is handed its semantic context and never consults the filesystem. `_owns` is
  consulted nowhere in the design — re-verified.
- **The phone authority relocates to a leaf** (`obsidian_schemas/phone_normalization.py`).
- **The gate's OUTPUT contract and the arm-shape split** — it returns the fields it was handed and
  never emits a key the write did not carry; both cross-field migrations are entity-arm behaviour.
- **The eight-arm derived set plus the D3 rider** — ratified this round from source, above.

### Review — only what changed

**Fit / Duplication / Reversibility / Generalization / Prior art:** as rounds 2–6 recorded them.
Approach F remains right; `tests/test_write_routing.py:1-18` remains the precedent `AC-1`'s battery
copies; no cited execution is owed. Reversibility improves again with the eight-arm set — two fewer
call sites and one predicate instead of two.

**Boundaries:** the residual boundary question is now the one the finding names, and it is a genuine
boundary rather than an oversight: the FILE PATH and the FRONTMATTER are two derivations of one value
(`entity.name`) taken in two different frames, and this item inserts a transform between them. The
generic layer owns the path (`base.py:381`); the gate owns the field. Nobody owns their agreement.
That is the shape LESSONS #43 names — one value, two readers, no single owner — and the cheapest
answer is to make the transform an identity so the question cannot be asked (shape (b′)).

**Determinism boundary (LLM vs code):** n/a for LLMs; the item is the opposite move throughout. The
underlying principle is what the finding turns on, though: the filename IS mechanically derivable from
the gated name one frame down, and the design leaves the two to agree by convention.

**Cost & maintenance:** unchanged at one to two sessions plus the Tier-1 branch-unit reification and
the D8 delta threading. Shape (b′) *reduces* cost — it deletes a rider obligation rather than adding
one.

**Build vs extend vs integrate:** extend, correctly, with one symbol moving first.

### Notes (non-blocking)

1. **`validate_strict` vs `clean` is unstated everywhere the gate is described, and the finding above
   is the reason it matters.** `## Approach` says only "Names go through `NameValidator`"; Finding H
   reifies across BOTH entry points; owed question 4 asks what happens to `create_stub`'s call. Under
   shape (b′) the answer becomes forced (neither, as a mutator — the gate consumes the Tier-1 decision
   and discards the repaired string), which is worth stating explicitly so the build does not pick one
   by convenience.
2. **Rounds 1–6's standing notes all carry:** the dedicated `pattern` attribute rather than overloading
   `declared_type` (`base.py:267-269` feeds it back into `_owns`); the new `REASONS` literal chosen at
   spec time (`errors.py:110-127`, a closed frozenset of fifteen; `bounded_message` raises on any
   non-member at `:139-145`); `lint_vault --fix`'s missing delta object; the `book.py`/`meeting.py`
   `save` overrides that are correctly not arms — load-bearing since round 6; and the
   three-functions-one-shape collapse, still a separate work item and still not recommended for
   absorption.
3. **The document is still buildable two ways until Dave re-originates** — `## Approach` refuses an
   undeclared write while `AC-2`/`AC-4` as signed gate an untyped dict "exactly as a `type: person` one
   is"; `### Examples of done` scenario 3 contradicts the arm-shape split; and `AC-1`'s floor names two
   members the corrected set does not contain. All three are staged in the brief, all three correctly
   declined by the fold as signed text, and none is re-raised here.
4. **The four unresolved `identifier.py:MIN_DIGITS` citations are all inside prose that names the slip
   itself** (architect rounds 5 and 6, data-premise rounds 5 and 6). Finding G's live citation reads
   `identifier.py:Phone:228` and resolves. Confirmed benign for the third time; no action.

### Arc note — convergence, and the arm-set correction's last consequence

The seven architect rounds have each closed their target and moved to a different one: the Company
annexation (1) → its structural sharpening plus the missing Tier-1 table (2) → the DECLARE ruling plus
the `AC-1` pass-what gap (3) → the phone authority (4) → the `aliases[]` migration's expressibility
(5) → the door set's own membership rule (6) → the filename derivation the membership correction left
above the set (7). Round 6's target is closed and verified from source above; no target has been
re-raised. This round's finding is the consequence of round 6's own ruling, which is the honest thing
to say about it and the reason it could not have been found earlier: before the correction, D2 carried
a gate call and the ordering was covered by accident. The queued order stands unchanged and does not
lengthen — Dave re-originates `AC-1`–`AC-4` in ONE round, one shell pass runs G1 and the twice-amended
G2 plus the consumer audit's greps, then ac-red-team → architect → data-premise → spec-writer.

```verdict
gate: architect
verdict: REVISE
date: 2026-08-11
model: claude-opus-5
targets: AC-1, #approach, #exploration-notes
note: Round 6's arm-set finding is closed and every round-7 claim re-derives from source — but dropping D2 leaves `filename = f"@{name}.md"` (base.py:380-382) bound one frame ABOVE the first arm that judges the name, and neither NameValidator entry point returns the name byte-identical (validate_strict strips and collapses at name_validation.py:257/:265-266; clean applies the same two Tier-2 repairs at :284-297), so `repo.save(Person(name="Dave  Smith"))` writes `@Dave  Smith.md` carrying `name: Dave Smith` and the next save mints a SECOND note — parked defect 1's corruption class, introduced by this item's own fix, and invisible to the fold's D2 check because that verified the refusal case (ensure_dir at writer.py:273 downstream of :266) rather than the accept-but-normalize one.
```

## Data Audit — 2026-08-11

**Recommendation: REVISE — return to exploration**

**Round 7, cold-start re-spawn.** Read in role order: `data-premise.yaml`, this document in full (five
ac-red-team rounds, the `ac-signoff` fence, seven architectural reviews, six prior data audits, seven
spec-writer rounds, `## Conductor Rulings & Grounding`, `## Grounding Still Owed`, the re-origination
brief), then the code every premise below turns on. Same method bound as every prior round in this
cage: **no shell — this spawn has no Bash tool at all — scope limited to this tree's files, and the
live vault was not read.** The counts used below are the conductor's, cited as such. Every citation
was re-derived from source this round rather than inherited.

**What this round is for.** The round-7 fold discharged my round-6 finding in full (the deletion is
retracted as "not a regression", named, and booked to G2 as one more column) and the round-7
architectural review then landed a new blocking issue: the FILENAME is bound at `base.py:381`, one
frame above the first arm that judges the name, and the gate's name output is not an identity. That
finding is correct and I confirm it from source. This round adds the one thing it does not carry: the
three shapes it offers Dave — (b′), (a′), (c′) — have **different live blast radii, over a population
nobody has measured and no owed query names**, and the number that separates them is not the one
count 3 already ran.

### Trigger check

**Class 1 AND Class 2 — both still fire.**

- Class 1 (data-distribution / field-presence): now **four** quantified claims about live entries are
  unmeasured — G1's undeclared population at the rule's own scope, G2's cells per field, G2's new
  deletion column, and (new this round) the population of live `@*.md` notes whose stored `name:` is
  Tier-1-CLEAN but Tier-2-DIRTY, which is what the (a′)/(b′) choice costs.
- Class 2 (rule-effect-against-existing-corpus): rule (ii) is still a new refusal rule whose effect is
  known for `@*.md` (count 1) and unknown everywhere else it reaches; the splitter consolidation is
  still a new acceptance predicate never run over the stored entries it will judge; and the Tier-2
  repair the gate performs on the name is a new **mutation** rule never run against the stored names it
  will rewrite.

### My round-6 finding — discharged

| Round-6 ask | Status |
|---|---|
| The dict-arm rule's *"not a regression"* pricing is measured against `aliases[]` when the display half is on disk INSIDE the raw `emails[]` entry — it is a DELETION | **DISCHARGED.** Finding I's M2 cost paragraph is rewritten, the whole-list blast radius via `_writeback_identifier` (`person.py:1206-1207`, `:1217`) is stated, `## Approach`'s dict bullet and the brief's `AC-4` sub-clause both carry the deletion in the same words, and the fold's contradiction scan says so. |
| The at-risk population is the intersection, not G2's extracted cell — one more column | **DELIVERED as a statement.** `## Grounding Still Owed` G2 carries it with its own purpose stated. **NOT RUN.** |
| Whether the (a)/(b) closure choice on `### Examples of done` scenario 3 has a consequence | **DELIVERED** — the brief's entry now records that (b) closes the deletion and (a) does not. Dave's call, correctly left to him. |

I withdraw the round-6 finding as a document defect. It is closed in text; only its number is owed.

### Verified from source this round

Re-derived rather than inherited. All confirm.

| Claim | Where I read it | Result |
|---|---|---|
| `validate_strict` is not an identity on the success path | `name_validation.py:257` (`stripped = name.strip()`), `:265-266` (`_DOUBLE_SPACE_RE.sub(" ", stripped)`); `_DOUBLE_SPACE_RE` is `\s{2,}` at `:118` | confirmed — architect round 7 holds |
| `clean` applies the same two Tier-2 repairs and returns the repaired string | `name_validation.py:283-286` (`strip_whitespace`), `:292-295` (`double_space_collapse`), returned at `:297` | confirmed |
| Tier-1 and Tier-2 are DISJOINT predicates — Tier 1 raises, Tier 2 rewrites, and `_raise_on_tier1` runs between them | `name_validation.py:288-290` (Tier-1 dispatch sits AFTER the strip and BEFORE the collapse) | confirmed — **this is why count 3 does not size the finding**; see below |
| `filename` is bound from the RAW `entity.name` and `save` writes to that path with no delete of any prior file | `base.py:380-382`, `:387-395`, `:398` — no `unlink`, no rename anywhere in the frame | confirmed |
| `create_stub` cleans ABOVE the filename derivation, which is why WI-105 never produced this divergence | `person.py:1405-1413` (`clean` at `:1407`, `name = clean_result.cleaned_name` at `:1413`), then `Person(...)` and `self.save(...)` | confirmed |
| `update_fields` does NOT rename the file on a name change — it appends the old stem to the parsed frontmatter's `aliases` and rewrites the same path | `base.py:443-448`, `:451`, `:456` | confirmed — the D4 divergence is field-only, a different shape from the `save` one |
| `Phone.MIN_DIGITS` is a `ClassVar` at `identifier.py:228`, consumed at `:238-239` and `:274`; `normalize_phone` applies no floor | `identifier.py:228`, `:238-239`, `:274`; `person.py:138-145` | confirmed — Finding G's live citation `identifier.py:Phone:228` resolves |

**On the citation-drift sweep: six hits now, all still benign, and the count is an artifact of the doc
recording itself.** The pre-spawn sweep resolves six `identifier.py:MIN_DIGITS` citations naming no
symbol. All six sit inside gate-authored prose whose subject IS the slip — architect round-5 note 1
(`:4525-4526`), the round-5 data audit's citation-slip paragraph (`:4621`), the round-6 data audit's
confirmation table (`:5139`), architect round-6 note 2 (`:5052`), the round-7 fold's contradiction scan
(`:5398`) and architect round-7 note 4 (`:5614`). The sweep counted three at round 5, four at round 6
and six now **because each round adds another sentence about it**, not because any live citation
regressed. There is still exactly one live `MIN_DIGITS` citation in the document — Finding G's, at
`:634` — and it resolves. Confirmed benign for the fourth time; I add no seventh sentence to the class
beyond this one, and I note the self-amplification so a later round does not read a rising number as a
rising defect.

### Finding — the (b′)/(a′)/(c′) choice has three different live blast radii, and the number that separates them has never been run

This is the one new thing this round adds. It is a data question, it lands on a design choice already
open in Dave's one round (`AC-1`'s rider clause, per the architect's own "Dave's round does not grow"),
and no owed query sizes it.

**The architect's scenario is the INTRODUCE case; the vault-side case is bigger and unstated.** The
review's example is a caller passing a fresh `Person(name="Dave  Smith")` — whose frequency is a
caller-behaviour fact belonging to the consumer audit, not a vault fact. But the same divergence fires
on **re-save of a note that already exists**, and that population IS a vault fact:

1. A stored note `@Dave  Smith.md` carrying `name: Dave  Smith` loads into a `Person` unchanged.
2. `repo.save(person)` binds `filename = "@Dave  Smith.md"` from the raw name (`base.py:380-382`) — it
   matches, so this write lands on the right file.
3. D1a fires the gate; the gate returns `name: "Dave Smith"`; the note at `@Dave  Smith.md` now carries
   `name: Dave Smith`. Path and field have diverged, on a note nobody edited.
4. The NEXT `save()` of the reloaded entity computes `@Dave Smith.md` and mints the second note.

So under the design as it stands, **every stored Tier-2-dirty name is a note that forks on its second
re-save**, with no dirty input from any caller.

**The three shapes do not merely differ in tidiness — they differ in what happens to that population:**

| Shape | Effect on a stored Tier-2-dirty note |
|---|---|
| **(b′) identity** — refuse or return byte-for-byte | **Nothing.** Path and field never disagree; the note keeps its dirty name forever on every non-`create_stub` path. Zero blast radius, and the repair is permanently a `create_stub`-only behaviour. |
| **(a′) rider writes the NAME back onto the entity** before `base.py:381` binds the path | The first re-save writes a **new file** at the cleaned stem and **leaves the old one in place** — `save` has no `unlink` and no rename (`base.py:380-398`). One orphan per note, immediately, on the fix's own first run. |
| **(c′) gate above the filename derivation** — round-6 shape (a) | Same as (a′) on this population, for the same reason. |

(a′) and (c′) are the shapes that *repair*, and repairing is exactly what forks the file. (b′) is free
on this population because it does nothing to it. **That is the trade Dave is being asked to sign, and
the document states neither side of it.** The architect recommends (b′) on boundary grounds (LESSONS
#43, one value two readers) and is right on those grounds; my point is narrower and additive — (b′) is
*also* the only one of the three with a zero live blast radius, and (a′)/(c′)'s radius is a number, not
an argument.

**Count 3 does not answer this, and the reason is structural rather than an oversight.** The
conductor's live pass ran `NameValidator.validate_strict` and counted what it **raised** on — 79
Tier-1-dirty stored names, 2 live. Tier 2 does not raise; it rewrites, and `_raise_on_tier1` runs
between the two repairs (`name_validation.py:284-295`). A name that strips or collapses passes
`validate_strict` cleanly and is therefore invisible in count 3 **by construction** — it is in the
3,339 that count 3 reports as fine. The two predicates are disjoint, so the existing number is not a
bound, an estimate, or even the same order of magnitude claim. **Nothing measured so far touches this
population**: G1 is `type:` presence, G2 is address splitting, G3 is withdrawn.

**Why I think this is worth a query rather than an assumption.** I have no shell and did not read the
vault, so I will not guess the number. What I can say is that the prior is not obviously zero: stored
names in this vault arrive from calendar attendee strings, WhatsApp contacts and email display halves,
all of which carry incidental double spaces, and — unlike the Tier-1 classes — nothing has ever swept
or repaired them, because Tier 2 has only ever run inside `create_stub` on the way IN. The adjacent
column is worth the same pass and is the sharper one: notes where the filename stem and the stored
`name:` **already** disagree are notes that fork on their next save under *any* of the three shapes,
including (b′), and they are also the ones parked defect 1 has been accumulating.

**What this does not claim.** It is not an argument for or against (b′) — the architect's boundary
reasoning stands on its own and I am not the architect. It is not a new blocking issue in the design;
it is the price tag on one already open. And it opens no rung of the LESSONS #38 ladder: it is a
behavioural population question about a design choice, inside ruling 3's own named item (`AC-1`'s
rider clause), exactly the shape my round-6 finding took and the fold accepted. I ran no generator
sweep.

### Required grounding

Nothing added to the shell pass except one query that rides the pass count 3 already proved cheap.
Three items carried unchanged, one new.

1. **G1 — unchanged and still unrun.** Rule (ii)'s undeclared population at the rule's own
   path-agnostic scope, with the untyped-frontmatter / no-frontmatter split and the path-class split.
   It does not gate the rule's direction (fail-closed, Dave's ruling 2); it sizes the target set the
   consumer audit intersects, and it is what build-start re-grounding re-runs.
2. **G2 — unchanged and still unrun,** now with all three of its parts stated: per-field cells, the
   case sub-cell, and the round-6 deletion column (`emails[]` extracted entries whose non-empty display
   half is not already in that note's `aliases[]`).
3. **G4 — NEW. The Tier-2 repair population, two columns.** Over every live `@*.md` note with
   parseable frontmatter — the same corpus and the same walk count 3 already did — report:
   **(a)** how many stored `name:` values are Tier-1-CLEAN (`validate_strict` does not raise) but
   Tier-2-DIRTY (`validate_strict(name) != name`, i.e. a strip or a `\s{2,}` collapse fires), with a
   sample and a breakdown by which repair fires; and **(b)** how many notes have a filename stem
   (`path.stem.lstrip("@")`) that differs from the stored `name:` value — the population where path and
   field have *already* diverged. Column (a) is the live blast radius of shapes (a′) and (c′) and is
   zero for (b′); column (b) is the population that forks on the next `save` under all three, and is
   parked defect 1's standing size. **Owed to:** this round, sizing the architect's round-7 finding.
   **Cheap:** it is one extra string comparison and one `path.stem` read on the pass count 3 already
   ran, with no new corpus and no new parsing.
4. **The consumer audit** — unchanged, still owed, still not a vault query: non-`create_stub` write
   callers across HAL9000, exocortex and orchestrator, plus importers of
   `obsidian_schemas.repositories.person.normalize_phone` / `phones_match`. The architect's INTRODUCE
   case belongs here — which of those callers passes a name it did not get from `create_stub` — and it
   is the other half of G4's blast radius.

### Conclusion

The document keeps improving and every round-7 claim I checked re-derives from source, including the
architect's new finding, which I confirm on all four legs. The fold discharged my round-6 finding
honestly — it retracted its own pricing rather than defending it.

What stops this being a PROMOTE is unchanged in kind and one item larger in extent. **G1 and G2 have
still never been executed**, and the newest design decision in front of Dave — which of (b′)/(a′)/(c′)
resolves the filename/name coupling — is heading into `AC-1`'s rider clause with two of its three
options carrying an unmeasured live cost that the only number anyone has run cannot bound, because
Tier 1 and Tier 2 are disjoint predicates. Promoting now would release the D3 brake at exactly the
moment a criterion is signed against a fact nobody has looked at, which is the failure this gate exists
to prevent one station earlier. Stage stays at `exploring`.

**Signal for the factory, stated because the targets line alone cannot carry it.** This is a converging
round and the arc is visible in what closed: rounds 1–3 named the untyped-dispatch premise (closed,
deleted by ruling 1); round 4 named the count's scope and two unnumbered deltas (all discharged); round
5 named the per-field split on G2 (delivered, withdrawn); round 6 named the dict-arm deletion (closed
in text this round, booked to G2, withdrawn above). No target has been re-raised. This round names a
different thing again — the price of a choice the architect only landed this round — and asks for two
columns on a walk that has already been performed once. **What has not moved is the thing no gate spawn
can move:** G1, G2 and now G4 need a shell and vault access outside every cage, and this spawn has no
Bash tool at all, so the predicates are not merely unrun but unrunnable here. My round-6 note predicted
that a seventh spawn before those numbers exist would reproduce that section; it has, and an eighth
will too. **The unblock is unchanged and is still one pass, now with one more query in it:** Dave
re-originates `AC-1`–`AC-4` (with `AC-1`'s floor at eight arms, the rider clause pinned to whichever of
(b′)/(a′)/(c′) he takes, and `AC-4`'s dict side priced against the deletion), and the same shell-holding
actor runs G1, the twice-amended G2 and the two columns of G4 alongside it.

```verdict
gate: data-premise
verdict: REVISE
date: 2026-08-11
model: claude-opus-5
targets: AC-1, #approach, #exploration-notes
note: Round 6's deletion finding is discharged in text and withdrawn, and architect round 7's filename/name finding is confirmed from source on all four legs (validate_strict is not an identity at name_validation.py:257/:265-266; clean repairs at :283-297; base.py:380-382 binds the path from the raw name and save has no unlink at :380-398; create_stub cleans above it at person.py:1405-1413) — but the three shapes it offers Dave have DIFFERENT live blast radii that nothing has measured: (a′)/(c′) repair a stored Tier-2-dirty name and so write a new file at the cleaned stem while leaving the old one, (b′) does nothing to that population, and count 3 cannot bound it because Tier 1 RAISES and Tier 2 REWRITES with _raise_on_tier1 between them (name_validation.py:284-295), so every Tier-2-dirty name sits inside count 3's clean 3,339 by construction; new query G4 sizes it in two columns on the walk count 3 already ran, and G1/G2/G4 remain unrun and unrunnable in this cage.
```

## Spec-Writer Fold — 2026-08-11 (round 8)

**This round PRODUCED a fold, not a hand-back.** Both round-7 verdicts target `AC-1`, but neither asks
me to edit it: the architect's finding is explicitly *"in the exploration first — direction rather than
design"*, and both gates say in their own words that the AC consequence is one clause inside an item
already staged for Dave (*"Dave's round does not grow"*; *"it lands on a design choice already open in
Dave's one round"*). The text that carries the finding is unsigned — `## Approach`, Finding B, Finding
H, Constraints, `## Grounding Still Owed`, `## Carried Forward`, `## Re-origination Brief` and the owed
questions — so this round writes.

Cold-start, read in role order: `spec-writer.yaml`, this document in full (five ac-red-team rounds, the
`ac-signoff` fence, seven architectural reviews, seven data audits, seven prior spec-writer rounds,
`## Conductor Rulings & Grounding`, `## Grounding Still Owed`, the re-origination brief), the project
`CLAUDE.md`, then the code every claim below turns on. Every citation re-derived from source this round,
not inherited: `name_validation.py` (`validate_strict`, `clean`, `_raise_on_tier1`, `_DOUBLE_SPACE_RE`,
both sentinel arms), `repositories/base.py` (`save`, `update_fields`, `_get_cache_key`),
`repositories/person.py` (`save`, `_normalize_address_fields`, `_writeback_identifier`, `create_stub`),
`writer.py` (`model_to_frontmatter`, the three arms, the convergence point, `ensure_dir`),
`scripts/lint_vault.py` (the `--fix` repair branches). This cage has **no shell**; the live vault was
not read — the counts used are the conductor's, cited as such.

### The decision this round made, stated first because everything else follows from it

The architect offered three shapes and named one as its own preference; the data audit priced all three
and confirmed the preference is also the cheapest live. **The fold takes (b′): the gate's name output is
an IDENTITY — it refuses, or it returns the name byte-for-byte, and Tier-2 repair stays a `create_stub`
behaviour above the filename derivation.**

Made here rather than escalated, and the reason is the boundary between signed and unsigned text rather
than confidence:

- **It weakens no signed criterion.** `AC-2` is about Tier-1 REFUSAL, `AC-4` about identifier
  normalization; neither asserts anything about a name's stored bytes. `AC-1` is about routing. So (b′)
  is expressible entirely inside `## Approach` and the Findings, which are mine.
- **It is the shape both round-7 gates point at**, from independent directions — the architect on
  boundary grounds (LESSONS #43: one value, two readers, no owner), the data gate on blast radius (zero
  on the population, versus one orphan file per repaired note under (a′)/(c′), since `save` has no
  `unlink` at `base.py:380-401`).
- **It is the only one of the three that does not need a number first.** (a′) and (c′) both repair, and
  repairing is what forks the file, so either would have to be signed against G4's column (a). (b′)
  does nothing to that population, so the choice is correct whatever the count turns out to be. G4 is
  still booked — it sizes what (b′) declines to repair and it sizes parked defect 1 — but it now
  RECORDS a consequence instead of gating a decision, which is the same relationship G1 has to rule
  (ii).
- **It removes an obligation rather than adding one.** The rider's write-back narrows to the identifier
  fields, and the path/field agreement then holds by construction for every entity type at every arm,
  rather than by a `PersonRepository` override.

### What this round wrote

| Section | Change | Answers |
|---|---|---|
| **Finding B** — new subsection *"The gate's NAME output is an IDENTITY, because the FILENAME is bound one frame above D1a"* | The seven-row source table (filename bound from the raw name at `base.py:380-382`; no `unlink`/`rename` in the frame; `validate_strict` not an identity at `:257`/`:265-266`; `clean`'s two repairs at `:283-297`; **both sentinel arms return `name.strip()`** — new this round; Tier 1/Tier 2 disjoint with `_raise_on_tier1` between them at `:288-290`; `create_stub` cleaning above the derivation at `:1405-1413`/`:1423`/`:1453`/`:1475`; the cache key at `:398`/`:308-310`), the concrete `"Dave  Smith"` failure, the identity rule stated over the gate's OUTPUT, the three-shape comparison with (a′)/(c′) rejected on cited grounds, and two further consequences — `lint_vault --fix`'s path-derived `person_missing_name` repair (`:835-839`) and the cache — plus an explicit statement of what the rule does NOT do. | architect round 7, blocking; data-premise round 7 |
| **Finding B** — the D2 bullet | Its removal argument now says out loud that it covers the REFUSAL case only, and that the FILENAME is the object it does not reach, with a forward pointer to where that leg is derived. The `ensure_dir`-downstream check is unchanged and still right. | architect round 7 |
| **Finding H** — new paragraph | **Which entry point the gate calls and what it does with the return value** — the question architect round-7 note 1 says is unstated everywhere. Answer: `validate_strict`, for its raise behaviour, discarding the repaired string; `clean`'s extra product is precisely what must not be acted on. With the two properties this preserves (Tier 1 still judges the stripped form; the sentinel is still evaluated on `name.strip()`, so the three live records are unaffected). | architect round 7, note 1 |
| **`## Approach`** | Header note records the correction; *"validated and normalized"* becomes *"validated and — on the address fields only — normalized"*; the names paragraph states the predicate rule with its reason; the output contract reads *"the address fields normalized, `name` byte-for-byte"*; the subsumption paragraph narrows the rider's write-back to the identifier fields and says what that costs (nothing — it deletes an obligation). | both round-7 gates |
| **Constraints — Effort** | Shape (b′) reduces the work again, and why. | architect round 7 |
| **`## Grounding Still Owed`** | **G4 added**, both columns, with its purpose restated for the chosen shape — sizing, not deciding — and the preamble amended so a later reader does not misread a growing list as a growing uncertainty. G1, G2 and the consumer audit unchanged. | data-premise round 7 |
| **`## Re-origination Brief`** | Header note records that the list did not grow. The `AC-1` rider clause gains its fixture pin (identifier fields only) and one control asserting the gate never alters a `name` — the clause that is RED for a build reaching for `clean`. | both round-7 gates |
| **`## Carried Forward`** | New bullet carrying the identity rule with its derivation and three consequences; the output-contract bullet narrowed on the rider. | both |
| **Owed question 4** | **ANSWERED and struck through.** `create_stub`'s call is KEPT unchanged and is now the package's sole Tier-2 repairer; the two passes agree on the sentinel AND on the output, so the second is idempotent rather than competing. | architect round 7, note 1 |

### Two things this round found that the reviews did not have

1. **The SENTINEL arms are not identities either — both return `name.strip()`** (`name_validation.py:253-254`,
   `:274-275`, read from source this round). Both reviews reasoned about `validate_strict`'s and
   `clean`'s success paths; the exemption arm returns *before* either, and it strips. That matters for
   how the rule is stated: a build told "use the entry point that does not normalize" would find that
   there isn't one, and would then have to choose between four return values. Stating the rule over the
   gate's OUTPUT — *call one entry point for its raise behaviour, discard what it returns* — is total
   over all four arms, which a rule naming an entry point is not. It also means the three live sentinel
   records (`## Conductor Rulings & Grounding`) are unaffected by the choice, which they would not
   obviously have been under (a′).
2. **(b′) closes a second divergence the reviews did not reach: the repair tool's own.**
   `lint_vault --fix`'s `person_missing_name` branch derives the name FROM the path —
   `name = fpath.stem.lstrip("@")`, `fm["name"] = name` (`lint_vault.py:835-839`), read this round.
   Under (a′) or (c′) a Tier-2-dirty stem would be repaired into a `name:` that no longer matches the
   file it was just read off, with the repair tool performing the split — the exact inversion of what
   that branch exists to do. Under (b′) the repaired `name:` equals the stem byte-for-byte, or the
   write is refused. This is an argument for the chosen shape that neither gate had, and it lands at
   the arm both architectural rounds price as the hardest.

### What this round still deliberately did NOT write, and why — unchanged from rounds 4 through 7

**No Design, Edge Cases, Implementation Plan, Write Targets, Verification, or `criteria` refinement.**
The three reasons are unchanged and none has moved. `AC-1`–`AC-5` remain inside the `ac-signoff` hash
span (`ac_hash: a76ebad54da2`), and this round's decision lands as one clause inside `AC-1`'s rider —
signed text, and inside an item two gates have already named wrong-on-facts, so WI-061 routes it to
re-origination rather than refinement. The plan and the criteria are one object: a task-verify text
pointing at `AC-1`'s floor and rider would have to be rewritten the moment either is re-signed. And rule
D3 refuses `→ specced` without a data-premise PROMOTE, which the standing verdict is not.

### Class-shaped fold — declared, and still bounded by ruling 3

Per WI-226 the finding in front of me is not "the filename is bound above the gate". Stated at source,
the generator — and it is the round-7 generator's next term, which is why it was invisible until the
arm-set correction landed:

> **Every "the gate covers this write" claim in this document was verified on ONE of the gate's two
> output channels — the REFUSAL — by asking *does a bad value get stopped*. None was verified on the
> other channel, the MUTATION, by asking *what does a GOOD value come back as, and who else has already
> read the value it replaced*.**

Round 7's generator was *a label carried forward after the definition underneath it moved*. This is a
level down and in a different direction: not a stale label, but a property checked on half its surface.
The D2-removal argument is the specimen — true, checked, and checked only against refusal.

**Enumerating what generates it and sweeping the class, as the rule requires.** The class is *every
object bound from a gate-judged field's value in a frame the gate does not run in* — because those are
exactly the readers a mutation can silently disagree with. The gate judges four fields (`name`,
`emails[]`, `phones[]`, `aliases[]`). Every such object in the design, re-derived from source:

| # | Object bound outside the gate's frame | From | Disposition under (b′) |
|---|---|---|---|
| 1 | the FILE PATH on `save` — `filename = f"@{name}.md"` | `base.py:380-382` | **CLOSED this round** — the name output is an identity, so path and field cannot disagree |
| 2 | the FILE PATH on `update_fields` — `self.get_file_path(name)` from the entity's raw name | `base.py:426-427` | **CLOSED by the same rule**, and independently: the gate is handed the caller's `updates` delta, never the entity, so it has no reach to the value the lookup used |
| 3 | the FILE PATH on the OTHER repositories — `self._get_file_name(entity)` on the siblings; `base.py:381` inherited by `CompanyRepository`, which overrides no `save` | `book.py:167`, `meeting.py:189`; `company.py` (no override) | **CLOSED by the same rule, and this is why it had to be a RULE rather than a rider.** No name transform reaches them today — under DECLARE the gate is handed their type and this item defines a contract only for `person`. But `CompanyRepository` inherits `base.py:381` verbatim, and WI-022 is open to give Company its own name contract: under (a′), a write-back living on `PersonRepository.save`, WI-022 would inherit this exact defect with nothing in the design naming it. The identity rule holds for every entity type at every arm, so WI-022 inherits the property instead of the defect |
| 4 | the in-memory CACHE key — `_adopt(self._get_cache_key(entity), …)`, `entity.name.lower()` | `base.py:398`, `:308-310` | **CLOSED this round** — the key and the serialized `name:` are the same string, so no refresh is needed to reconcile them |
| 5 | `update_fields`' cache re-key — `old_name_key = name.lower()` vs `self._get_cache_key(updated_entity)` | `base.py:464-465` | **HOLDS, re-derived** — `update_fields` RELOADS from the file at `:459` before re-keying, so any model/bytes divergence closes inside the frame |
| 6 | the in-memory MODEL's identifier fields, after a gate that returns a dict and never touches the model | `person.py:1269` today; the D3 rider under the design | **HOLDS** — this is precisely the rider's stated reason, and it is why the rider survives (b′) rather than being deleted with the name half |
| 7 | `_writeback_identifier`'s membership tests, read off the model before the write | `person.py:1205`, `:1208` | **HOLDS, re-derived** — it routes through `update_fields`, which reloads from file at `base.py:459`, so the model is reconciled in the same call |
| 8 | `update_fields`' old-stem alias, read off the PATH | `base.py:443-448` | **HOLDS, unchanged by this item** — parked defect 1's neighbourhood; (b′) leaves it exactly as today rather than making it worse, which (a′)/(c′) would |
| 9 | `create_stub`'s reuse-on-collision lookup — `self.get(clean_name)` | `person.py:1437` | **HOLDS, re-derived** — keyed on `create_stub`'s own cleaned name, which then flows into `base.py:381` unchanged, so lookup, path and field all agree. This is the existence proof that the ordering is load-bearing |
| 10 | `lint_vault --fix`'s path-derived name — `fm["name"] = fpath.stem.lstrip("@")` | `lint_vault.py:835-839` | **CLOSED this round** — see finding 2 above; (a′)/(c′) would have had the repair tool create the divergence |

**Sweeping the next level of the ladder and declaring what it found, as the rule requires.** The
dimensions of this class are the KIND of derived object: a filesystem path (rows 1–3), an in-memory
index or cache key (4, 5), the source model itself (6, 7), and a derived lookup key (8, 9, 10). All
four are swept above and all four are closed or hold. The intersection cell — *an object derived from a
gate-judged field AND written by a different door than the one the gate ran in* — is real and is rows 7
and 8; both resolve by the reload at `base.py:459` or are explicitly parked. **I find no further open
member**, and I record the reason the sweep is finite rather than merely exhausted: the design's own
DECLARE rule bounds it, because a gate that never consults the filesystem has no readers except the
ones its callers hand it, and those are enumerable from the eight arms plus the rider.

**And here the sweep STOPS**, on Dave's ruling 3 rather than on mine. The altitude declaration holds:
the AC checking machinery is sufficiently specified, the re-origination fixes named defects only, and
findings of the checking-of-the-checking shape do not block. This round's finding is not one of those —
it is a data-corruption path in the design, which round 3's regress analysis holds outside the ladder
and which the architect's round-7 review says so explicitly. Its AC consequence lands in `AC-1`'s rider
clause, already inside ruling 3's own named set. This round opens no further rung.

### Contradiction scan — what this round's claims now disagree with

Run over the whole document for every claim added or edited this round, because a paragraph that is
right against the code and wrong against another section leaves the item buildable two ways.

- **Finding B's D2-removal bullet** (*"every byte either `save` produces reaches the seam through D1a
  one frame later"*) — genuinely under-stated, since the filename is not a byte the seam produces.
  FIXED in place with the scope of the argument named and a forward pointer, not left standing.
- **`## Approach`'s "validated and normalized"** — contradicted the identity rule on `name`. FIXED in
  three places (the opening sentence, the names paragraph, the output contract) so the section does not
  state the contract two ways.
- **The subsumption paragraph's "writing the gate's normalized values back onto the entity"** — would
  have read as including `name`. NARROWED explicitly to the identifier fields, with the reason.
- **Finding I's arm-shape split and the output contract's *never emit a key the write did not carry*** —
  unaffected. The identity rule narrows what the gate may CHANGE on a key it was handed; the output
  contract bounds which keys it may EMIT. Different clauses, not competing.
- **Finding H's sentinel rule** (*a pure-digit name is permitted when the record carries a phone*) —
  unaffected, and re-checked: the exemption is a REFUSAL decision, not an output transform, so it sits
  entirely on the channel the identity rule leaves alone. The paragraph added to Finding H says so.
- **Finding C's delta rule** — unaffected. It scopes WHICH fields are judged; the identity rule scopes
  what comes back out of the judgement.
- **Owed question 3** (`create_stub`'s refusal channel) — still open and still correctly open. Question
  4 is answered and struck; the two are adjacent but distinct, and answering 4 does not answer 3.
- **`### Examples of done` scenario 3** — unchanged by this round, still contradicting the arm-shape
  split, still signed, still staged in the brief. This remains one of the two places the document is
  buildable two ways until Dave re-originates; the other is Tier A's undeclared clause. **No third was
  created this round** — that is the point of making the choice in unsigned text.
- **Citation-drift note, recorded rather than actioned.** The pre-spawn sweep now resolves seven
  `identifier.py:MIN_DIGITS` citations naming no symbol, up from six. Every one sits inside
  gate-authored prose whose subject IS the slip — architect rounds 5, 6 and 7, the data audits of
  rounds 5, 6 and 7, and the round-7 fold's own contradiction scan. The round-7 data audit already
  diagnosed the rise correctly: the count grows because each round adds another sentence ABOUT it, not
  because any live citation regressed. There is still exactly one live `MIN_DIGITS` citation in the
  document — Finding G's, which reads `identifier.py:Phone:228` and resolves. Confirmed benign for the
  fifth time. **I add no eighth sentence to the class beyond this one, and I introduced none**: this
  round's new text cites `Phone.parse`'s floor nowhere. Gate sections are theirs, not mine, so no edit
  is available to me.

### Re-entry — unchanged in order and in length

1. **Dave re-originates `AC-1`–`AC-4` in ONE round** (Tier A + Tier B; `AC-5` unchanged), now with
   `AC-1`'s floor at eight arms, the pass-what pin, and the rider clause carrying BOTH its exclusion
   and its round-8 fixture pin (identifier fields only, plus the control that the gate never alters a
   `name`); `AC-4`'s `aliases[]` clause scoped by arm shape with its dict side priced against the
   deletion; and one yes/no on `### Examples of done` scenario 3, where (b) closes the deletion and (a)
   does not.
2. **One shell pass, alongside the re-origination:** **G1**, the twice-amended **G2** (per field, plus
   the deletion column) and the two columns of **G4** in `## Grounding Still Owed`, plus the consumer
   audit's two greps. G3 stays withdrawn as moot. None of the four gates a shape; all four size.
3. **ac-red-team → architect → data-premise → spec-writer.** The architect's rulings — gate signature,
   splitter, DECLARE, the phone relocation, the output contract, the arm-shape split and now the
   name-identity rule — all carry forward and need no re-derivation.
4. **spec-writer.** With 1–3 done the spec is assembly: `## Carried Forward` plus the routing at eight
   arms and one rider, the wall, the phone relocation, the splitter consolidation and the subsumption,
   the Tier-1 branch-unit reification, and the `lint_vault --fix` delta threading.

## Architectural Review — 2026-08-11 (round 8)

**Recommendation: REVISE — return to exploration**

**Round 8, cold-start re-spawn.** Read in role order: `architect.yaml`, this document in full (five
ac-red-team rounds, the `ac-signoff` fence, seven prior architectural reviews, seven data audits,
eight spec-writer rounds, `## Conductor Rulings & Grounding`, `## Grounding Still Owed`, the
re-origination brief), then the code every claim below turns on (`obsidian_schemas/vault_io.py`,
`writer.py`, `repositories/base.py`, `repositories/person.py`, `name_validation.py`,
`scripts/lint_vault.py`), plus `LESSONS.html`. No shell in this cage; the live vault was not read —
the counts used below are the conductor's, cited as such.

**My round-7 blocking issue is CLOSED, and closed with the shape I named.** The round-8 fold takes
(b′): the gate's name output is an IDENTITY, Tier-2 repair stays in `create_stub` above the filename
derivation, and the rider's write-back narrows to the identifier fields. Every leg re-derives from
source (table below), and the fold's two additions the review did not have — that the SENTINEL arms
are not identities either, and that (b′) also closes `lint_vault --fix`'s own path-derived repair —
are both right and both matter. The choice was correctly made in unsigned text.

The finding below is new and it is in the same neighbourhood, which is why it belongs in this round
rather than after the re-sign: round 7 found that the arm-set correction left the FILENAME bound above
the first arm that judges the name. It left something else above it too, and this one is not derived
from a field at all — it is a filesystem mutation performed by the write path before the gate can
refuse.

### Trigger check

Three fire, unchanged: **two** new modules (the gate and the phone leaf); a contract change crossing
into three downstream repositories installed with `pip install -e`
(`docs/backlog-campaign-2026-07-05.md:98`); a derived-wall enforcement mechanism that must be designed
rather than copied. Effort stated at one to two sessions.

### Round-7's blocking issue — verified closed from source

Re-derived this round rather than accepting the fold's account of itself. All confirm.

| Claim the round-8 fold makes | Where I read it | Result |
|---|---|---|
| `validate_strict` is not an identity — it strips AND collapses on the success path | `name_validation.py:257` (`stripped = name.strip()`), `:262` (`_raise_on_tier1`), `:265-266` (`_DOUBLE_SPACE_RE.sub(" ", stripped)`) | confirmed |
| `clean` applies the same two repairs and returns the repaired string | `name_validation.py:283-286`, `:292-295`, returned `:297` | confirmed |
| **both SENTINEL arms return `name.strip()`**, so no entry point is an identity | `name_validation.py:253-254` (`validate_strict`), `:274-275` (`clean`) | confirmed — and this is what makes stating the rule over the gate's OUTPUT correct rather than naming an entry point |
| Tier 1 and Tier 2 are disjoint, with `_raise_on_tier1` between the two repairs | `name_validation.py:288-290`, comment at `:288-289` | confirmed |
| the FILENAME is bound from the raw `entity.name`, and `save` neither renames nor unlinks | `base.py:380-382`, and no `unlink`/`rename`/`replace` anywhere in `:356-401` | confirmed |
| the cache key is the raw `entity.name.lower()`, taken one line after the write | `base.py:398`, `_get_cache_key` at `:308-310` | confirmed |
| `create_stub` cleans ABOVE the filename derivation | `person.py:1405-1413` (`clean` `:1407`, `name = clean_result.cleaned_name` `:1413`), `:1423`, `:1453`, `self.save` `:1475` | confirmed |
| `lint_vault --fix`'s `person_missing_name` derives the name FROM the path | `lint_vault.py:835-839` (`name = fpath.stem.lstrip("@")`, `fm["name"] = name`) | confirmed — the fold's second argument for (b′) holds |
| the eight-arm set and the three fm-building arms converging at `:266` | `writer.py:256-257` / `:258-261` / `:262-263` → `:266` | confirmed |

That is the right answer to round 7, and I add nothing to it. `## Carried Forward`'s new identity
bullet is accurate as written.

### Blocking issue — the write path creates the stray directory BEFORE the gate can refuse, so Finding F's own promise is not delivered by gating at D1a

The round-7 fold removed D2 from the derived set on one load-bearing check, restated in three places
since (`## Approach`'s round-7 header note, Finding B's D2 bullet, `## Carried Forward`, and the
brief's Tier B `AC-1` entry): *"`vault_io.ensure_dir(file_path.parent)` is at `writer.py:273`,
DOWNSTREAM of the convergence point at `:266` … so a refusal raised at D1a precedes the `mkdir` and no
`@Dave/` directory is created — which is the byte-identical/no-stray-directory promise `AC-2` makes."*

That check reads `write_markdown_file`'s own body and finds the one `ensure_dir` written in it. There
is a **second `mkdir` on the same path, one frame down, and it runs at `writer.py:209` — fifty-seven
lines above the convergence point.** Re-derived from source this round:

| Step | Read from | Result |
|---|---|---|
| `write_markdown_file` acquires the note lock as its FIRST action, before any fm is built | `writer.py:204-209` — `with vault_io.note_lock(file_path) as resolved:` at `:209`; the arms are at `:256-263` | confirmed |
| `note_lock` resolves non-strictly, so a path whose parent does not exist is accepted | `vault_io.py:376` (`target = _resolved(path)`), `:234-243` (`Path(path).resolve()`, docstring: *"a not-yet-existing leaf resolves against its resolved parent"*) | confirmed |
| on the outermost acquisition it derives a sentinel and **`ensure_dir`s the sentinel's parent** | `vault_io.py:392-400` — `if not reentrant:` → `sentinel = _sentinel_path(target)` (`:398`) → `ensure_dir(sentinel.parent)` (`:400`) | confirmed |
| the sentinel's home DEFAULTS to the note's own directory | `vault_io.py:_sentinel_path:335-351` — `home = configured if configured is not None else target.parent / SENTINEL_DIR_NAME`; `SENTINEL_DIR_NAME = ".obsidian-schemas-locks"` (`:58`) | confirmed |
| `_configured_lock_dir()` is `None` unless `OBSIDIAN_SCHEMAS_LOCK_DIR` is set to an absolute path — its own docstring says *"or None for the default (the note's own directory)"* | `vault_io.py:137-166`, `default=None` at `:149` | confirmed — the default is the live production case |
| `ensure_dir` is `mkdir(parents=True, exist_ok=True)` | `vault_io.py:618-638`, `:634` | confirmed |

**So the item's own headline scenario, traced end to end:** `repo.save(Person(name="Dave/Bob"))` →
`filename = "@Dave/Bob.md"` (`base.py:381`) → `write_markdown_file` → `note_lock` (`writer.py:209`) →
`_sentinel_path` yields `<vault>/@Dave/.obsidian-schemas-locks/<digest>.lock` → `ensure_dir` at
`vault_io.py:400` runs `mkdir(parents=True)` and **creates `<vault>/@Dave/`**, plus the lock
subdirectory inside it and, at `:410-414`, a `.lock` file. Only then does control reach `:266`, where
the gate refuses. The refusal propagates, the lock releases, and the directory stays: nothing in the
package removes it, and `ensure_dir` is documented as carrying no compensating action (`:621-624`).

That falsifies three things at once, which is why it is blocking rather than a note:

1. **`AC-2`'s signed clause** — *"the target is left byte-identical, **no stray directory is
   created**"* — cannot be met by a gate at the convergence point, on any of D1a/D1b/D1c.
2. **`### Examples of done` scenario 1**, also signed — *"the vault contains no new `@Dave/`
   directory and no `Bob.md` inside one"* — is false as to its first clause. The second clause holds:
   no note is written.
3. **The justification for the D2 removal**, which is about to enter `AC-1` as verified fact. The
   exclusion itself survives — `BaseRepository.save` still binds no dict, so the round-6 membership
   ruling stands — but the *reason given for it being safe* does not, and the brief's Tier B `AC-1`
   entry states it in the criterion text Dave is being asked to sign.

**Why no gate round caught it, and it is a named class.** Every architectural round including my own
verified this promise by READING — checking `write_markdown_file` for `ensure_dir` and finding the one
at `:273`. Nobody executed it. That is LESSONS #42 (`LESSONS.html:723-731`) in its exact shape: *"a
spec that prescribes a machine-checked state of the world is making an executable claim, and no number
of readers can falsify it … the unsatisfiability lives in the composition."* Here the composition is
`write_markdown_file` × `note_lock`, and each half is individually accurate. Eight architectural
rounds, five red-team rounds, seven data audits and eight spec-writer rounds have all reasoned about
`repo.save(Person(name="Dave/Bob"))`; the one thing that would have settled it is one `pytest -k` on a
tmp vault, and the cage has never had a shell to run it in.

**What has to change, in the exploration first — direction rather than design.** All three are cheap
and all three land in text already open:

- **(A) Hoist the fm construction and the gate call ABOVE the lock acquisition in
  `write_markdown_file`.** This is the shape I would take. The three arms at `writer.py:256-263` read
  only `entity` / `frontmatter` / `extra_fields` — nothing between `:209` and `:263` feeds them (the
  stamp lookup `:210`, the `unverified` flag `:214`, `is_create` `:226` and the WI-126 body read
  `:236-239` are all downstream consumers, not inputs), so the hoist is local, changes no arm's
  identity, and preserves the single convergence point. It also dissolves the state rather than
  detecting it, which is the second half of #42's rule. **It carries one new obligation**: the derived
  wall as described proves an arm *calls* the gate somewhere in its body, so the property *"the gate
  call precedes the first filesystem mutation on this path"* is a placement fact nothing enforces
  unless the wall pins it. Same instrument, one argument wider — the identical shape as the round-3
  pass-what pin, and it belongs beside it.
- **(B) Re-instate a gate call at `BaseRepository.save` as a RIDER** (not an arm), above
  `write_markdown_file` entirely. It works for repository saves and it does not reopen the membership
  problem. **It is not sufficient alone**: `write_markdown_file(path, extra_fields={"type": "person",
  "name": "Dave/Bob"})` is the D1c call `### Examples of done` scenario 1 explicitly requires to be
  refused with no directory, and it never passes through a repository.
- **(C) Narrow the promise** — drop "no stray directory" from `AC-2` and scenario 1, keeping "no note
  is created". Free, and honest, but it retires the concrete defect Finding F exists to close. Named
  so the option set is complete, not as a recommendation.

**One scoping note the fix must carry, so the build does not over-apply it.** Only D1a/D1b/D1c can
create a path that does not exist. D4 (`base.py:429-433`), D5 (`writer.py:320-321`) and D6
(`writer.py:374-375`) all raise on a missing file *before* locking, and D8 walks notes it has already
read — so their gate calls must STAY inside the lock, because that is where their declaration is read
from the note (`writer.py:329`, `:381`). The hoist is arm-specific, not a general rule, and stating it
that way is what stops a build moving D5/D6's gate call above the parse that supplies its type.

### Why this is not a new rung of the LESSONS #38 ladder

Stated because ruling 3 makes the distinction load-bearing and I am the gate that escalated for it.
This is not "the sweep's unit is too coarse", not "the AC names a container that does not span its
surface", and not a generator sweep at a higher altitude — I ran none. It is a stray directory left on
disk by the item's own headline scenario, contradicting a clause of a signed criterion: "the thing is
wrong", which round 3's regress analysis explicitly holds outside the ladder. Its AC consequence lands
in `AC-2`'s no-stray-directory clause and one sentence of the `AC-1` entry, both already inside ruling
3's named set.

**And the class this closes is finite, which is the reason I think this is the tail rather than round
9.** Rounds 7 and 8 are both consequences of the round-6 arm-set correction, and they share one
generator the document has not named: *the gate sits at the LAST point where the payload's structure
is decidable, but the item's promises are about the FIRST point where the write's side effects begin —
and those are not the same point.* Sweeping every side effect the write path performs on a path
derived from a gate-judged field between the caller's frame and `writer.py:266`, from source: the
FILENAME binding (`base.py:381` — closed by (b′) in round 8), the lock-sentinel `mkdir`
(`vault_io.py:400` — this finding), and the `.lock` file itself (`vault_io.py:410-414`, same fix).
Nothing else in `writer.py:204-266` touches the filesystem: `:210` is a registry lookup, `:215` and
`:236-239` are reads. Two members, both now on the table, and the enumeration is closed by inspection
rather than by assertion.

### Rulings carried forward — settled, do not re-derive

All seven stand, re-checked against the code this round. Nothing above reopens any of them — this
finding is about WHEN a gate call runs relative to a lock, not about what the gate receives, emits, or
is handed.

- **Gate signature:** no `existing` parameter, one entry point taking the introduced fields plus the
  entity type; entity arms project through `model_to_frontmatter` (`writer.py:88-130`) first.
- **Splitter:** TOTAL, returns `(address | None, display)`, owns the parens form before delegating,
  maps `IdentifierError` to "not an address"; `Email.parse`'s angle-bracket gate is NOT widened.
- **DECLARE:** the gate is handed its semantic context and never consults the filesystem. `_owns` is
  consulted nowhere — re-verified.
- **The phone authority relocates to a leaf** (`obsidian_schemas/phone_normalization.py`).
- **The gate's OUTPUT contract and the arm-shape split.**
- **The eight-arm derived set plus the D3 rider.** Unchanged by this finding — the membership ruling
  turns on what a function BINDS, and that is unaffected.
- **The gate's NAME output is an IDENTITY** — ratified this round from source, above.

### Review — only what changed

**Fit / Duplication / Generalization / Prior art:** as rounds 2–7 recorded them. Approach F remains
right; `tests/test_write_routing.py:1-18` remains the precedent `AC-1`'s battery copies; no cited
execution is owed on the wall instrument.

**Boundaries:** the residual question is a genuine layering one and it is the finding. `vault_io` owns
the mechanical door and correctly acquires its lock at the top of every write; this item's semantic
gate is placed at the deepest point where the payload is still typed. Those two placements are each
right on their own terms and they compose into "the mechanical door has already touched the filesystem
before the semantic door gets to say no". The item's own Constraints line — *"WI-004 is the floor, not
the home"* — is exactly correct and is also the reason the semantic layer must run BEFORE the
mechanical floor is entered, not inside it. That sentence is in the document; the ordering it implies
is not.

**Reversibility:** unchanged and good. Under (A) the change is a hoist within one function.

**Determinism boundary (LLM vs code):** n/a for LLMs; the item is the opposite move throughout. The
dimension's principle is what the finding turns on, though — whether a refusal precedes a side effect
is mechanically decidable from the call graph, and the design has left it to be true by reading.

**Cost & maintenance:** unchanged at one to two sessions plus the Tier-1 branch-unit reification and
the D8 delta threading. (A) adds one wall clause and moves ten lines.

**Build vs extend vs integrate:** extend, correctly, with one symbol moving first.

### Notes (non-blocking)

1. **`roundtrip_file` (D7) locks a path it never checks for existence** (`writer.py:414-417`), so it
   too can create the sentinel directory on a path that does not exist. It has no gate call and
   introduces nothing, so it is out of this finding — recorded only so the scoping note above is not
   read as a claim that D7 is exist-checked like D4/D5/D6.
2. **`OBSIDIAN_SCHEMAS_LOCK_DIR` changes the finding's shape but not its existence.** With an absolute
   lock home configured, `_sentinel_path` puts the sentinel outside the vault and no `@Dave/` appears —
   so a fixture that sets that variable would pass while production fails. Worth one sentence in the
   spec: `AC-2`'s no-stray-directory fixture must run under the DEFAULT lock home, or it is a control
   with no discriminating power.
3. **Rounds 1–7's standing notes all carry:** the dedicated `pattern` attribute rather than overloading
   `declared_type` (`base.py:267-269` feeds it back into `_owns`); the new `REASONS` literal chosen at
   spec time (`errors.py:110-127`, a closed frozenset of fifteen; `bounded_message` raises on any
   non-member at `:139-145`); `lint_vault --fix`'s missing delta object; the `book.py`/`meeting.py`
   `save` overrides that are correctly not arms; and the three-functions-one-shape collapse, still a
   separate work item and still not recommended for absorption.
4. **The document remains buildable two ways until Dave re-originates** — Tier A's undeclared clause,
   `### Examples of done` scenario 3 vs the arm-shape split, and `AC-1`'s floor naming two non-members.
   This round adds a third: scenario 1's directory clause. All four are staged in the brief or land in
   it; none is re-raised here.
5. **The eight unresolved `identifier.py:MIN_DIGITS` citations are all inside gate-authored prose whose
   subject IS the slip** (architect rounds 5–7, data audits 5–7, the round-7 and round-8 folds'
   contradiction scans). The round-7 data audit's diagnosis of the rising count is correct and I confirm
   it for the sixth time: exactly one live citation exists, Finding G's `identifier.py:Phone:228`, and it
   resolves. **I introduce no ninth** — this round cites `Phone.parse`'s floor nowhere.

### Arc note — convergence, and what would make round 9 unnecessary

The eight architect rounds have each closed their target and moved to a different one: the Company
annexation (1) → its structural sharpening plus the missing Tier-1 table (2) → the DECLARE ruling plus
the `AC-1` pass-what gap (3) → the phone authority (4) → the `aliases[]` migration's expressibility
(5) → the door set's membership rule (6) → the filename bound above the set (7) → the directory created
before the set can refuse (8). Round 7's target is closed and verified from source above; no target has
been re-raised.

Rounds 7 and 8 are both consequences of my own round-6 ruling, and I have said so plainly rather than
presenting this as an independent discovery. What separates it from a treadmill is that the class they
share is now named and swept to exhaustion from source (two members, both closed on the table above),
and that the sweep is bounded by something structural rather than by my confidence: between the
caller's frame and `writer.py:266` the write path performs exactly two filesystem-visible acts, and
both are enumerated.

**The one thing that would retire this whole class rather than its last member:** the queued shell pass
already runs G1, G2 and G4 against the live vault. The same actor, in the same pass, can execute
`repo.save(Person(name="Dave/Bob"))` against a throwaway tmp vault under the default lock home and list
what is on disk afterwards. That is not a vault query and it needs no vault — it is the one execution
eight reading gates could not substitute for, and per LESSONS #42 it is worth more than a ninth reader.
The queued order is otherwise unchanged and does not lengthen: Dave re-originates `AC-1`–`AC-4` in ONE
round, one shell pass runs G1/G2/G4 plus the consumer audit's greps, then ac-red-team → architect →
data-premise → spec-writer.

```verdict
gate: architect
verdict: REVISE
date: 2026-08-11
model: claude-opus-5
targets: AC-1, AC-2, #approach, #exploration-notes
note: Round 7's name-identity finding is closed and every round-8 claim re-derives from source (both sentinel arms return name.strip() at name_validation.py:253-254/:274-275; base.py:380-401 has no unlink; lint_vault.py:835-839 derives the name from the path) — but the D2-removal's load-bearing check is falsified: `note_lock` at writer.py:209 runs `ensure_dir(sentinel.parent)` at vault_io.py:400, whose home DEFAULTS to `target.parent/".obsidian-schemas-locks"` (vault_io.py:335-351, :137-166), so `repo.save(Person(name="Dave/Bob"))` mkdirs `<vault>/@Dave/` fifty-seven lines BEFORE the gate can refuse at writer.py:266 — AC-2's signed "no stray directory is created" clause and Examples-of-done scenario 1 are unmeetable by any gate call inside write_markdown_file, and eight architectural rounds verified the promise by reading `write_markdown_file` for `ensure_dir` and finding only the one at :273 (LESSONS #42).
```

## Data Audit — 2026-08-11

**Recommendation: REVISE — return to exploration**

**Round 8, cold-start re-spawn.** Read in role order: `data-premise.yaml`, this document in full (five
ac-red-team rounds, the `ac-signoff` fence, eight architectural reviews, seven prior data audits, eight
spec-writer rounds, `## Conductor Rulings & Grounding`, `## Grounding Still Owed`, the re-origination
brief), then the code every premise below turns on. Same method bound as every prior round in this
cage: **no shell — this spawn has no Bash tool at all — scope limited to this tree's files, and the
live vault was not read.** The counts used below are the conductor's, cited as such. Every citation was
re-derived from source this round rather than inherited.

**What this round is for.** The round-8 fold closed my round-7 finding by taking (b′), and the round-8
architectural review then landed a new blocking issue: `note_lock` `mkdir`s the note's parent directory
before any gate at the convergence point can refuse. That finding is correct and I confirm it from
source, every leg. This round adds the one thing it does not carry, and it is the same thing round 7
needed: the finding has a **live population**, and that population is structurally invisible to every
count that has been run and to every query that is owed.

### Trigger check

**Class 1 AND Class 2 — both still fire.**

- Class 1 (data-distribution / field-presence): now **five** quantified claims about live entries are
  unmeasured — G1's undeclared population at the rule's own scope, G2's cells per field, G2's deletion
  column, G4's two Tier-2 / path-divergence columns, and (new this round) the population of notes and
  directories Finding F's defect has **already created** in the live vault.
- Class 2 (rule-effect-against-existing-corpus): rule (ii) is still a new refusal rule whose effect is
  known for `@*.md` and unknown everywhere else it reaches; the splitter consolidation is still a new
  acceptance predicate never run over the stored entries it will judge; and — sharpened by the
  architect's finding — `AC-2`'s no-stray-directory clause is an **executable** claim about the composed
  write path that no reader has run and eight rounds of readers have now got wrong.

### My round-7 finding — discharged

| Round-7 ask | Status |
|---|---|
| The (b′)/(a′)/(c′) choice has three different live blast radii and nothing sizes them | **DISCHARGED.** The fold took (b′) — the shape whose radius on that population is zero by construction — and stated in `## Grounding Still Owed`'s round-8 preamble that G4 now RECORDS a consequence rather than gating a decision. That is the correct disposition of a sizing query once the shape that needs no number is chosen. |
| G4 booked, two columns, on the walk count 3 already ran | **DELIVERED as a statement**, with both columns and the cheapness argument intact. **NOT RUN.** |

I withdraw the round-7 finding as a document defect. It is closed in text; only its number is owed, and
it is now correctly booked as sizing rather than as a gate.

### Verified from source this round

Re-derived rather than inherited. The architect's round-8 finding confirms on every leg.

| Claim | Where I read it | Result |
|---|---|---|
| `write_markdown_file` acquires the note lock as its FIRST act, and the three fm arms are 47–54 lines below it | `writer.py:204` (`file_path = Path(file_path)`), `:209` (`with vault_io.note_lock(file_path) as resolved:`), arms `:256-263`, convergence `:266` | confirmed |
| the outermost acquisition derives a sentinel and `ensure_dir`s its parent, before yielding | `vault_io.py:392-393` (`if not reentrant:`), `:398`, `:400`; the `yield` is at `:424` | confirmed |
| the sentinel's home DEFAULTS to the note's own directory | `vault_io.py:350` (`home = configured if configured is not None else target.parent / SENTINEL_DIR_NAME`) | confirmed |
| `_configured_lock_dir()` is `None` unless an ABSOLUTE `OBSIDIAN_SCHEMAS_LOCK_DIR` is set — the docstring says so in its first line | `vault_io.py:137-152`, `default=None` at `:149` | confirmed — the default IS the production case |
| `ensure_dir` is `mkdir(parents=True, exist_ok=True)` with no compensating action | `vault_io.py:632-638`, ruling recorded at `:621-624` (*"Carries NO precondition and NO lock … it is idempotent and has no loss mode"*) | confirmed — nothing removes what it creates |
| the filename that reaches it is `f"@{name}.md"` from the raw entity name | `base.py:380-382`, passed at `:387-388` | confirmed |
| a `.lock` FILE is created inside that directory too, one frame later | `vault_io.py:410-414` | confirmed |

So `repo.save(Person(name="Dave/Bob"))` creates `<vault>/@Dave/.obsidian-schemas-locks/<digest>.lock`
before control reaches `writer.py:266`. `AC-2`'s *"no stray directory is created"* and scenario 1's
*"the vault contains no new `@Dave/` directory"* are both false under a gate at the convergence point.
I add nothing to the architect's three shapes (A)/(B)/(C); the choice is theirs and Dave's.

### Finding — Finding F's defect has a LIVE population, and every count run and every query owed is blind to it by construction

This is the one new thing this round adds, and it is the data half of the finding the architect landed
structurally.

**The defect is not prophylactic.** Finding F states, and `writer.py:273`/`base.py:381` confirm, that
`repo.save(Person(name="Dave/Bob"))` **today succeeds**: it creates `<vault>/@Dave/` and writes
`Bob.md` inside it. There is no gate yet, so nothing has ever stopped this. The question nobody has
asked in eight rounds is whether it has already happened — and if so, how often.

**Why no existing number can answer it.** The forked note's leaf is `Bob.md`, not `@Bob.md`. Therefore:

| Number | Method | Sees the forked note? |
|---|---|---|
| Count 1 (untyped population, 0 of 3,418) | `rglob("@*.md")` (`## Conductor Rulings & Grounding`) | **No** — the leaf does not match the pattern |
| Count 3 (79 Tier-1-dirty stored names, 2 live) | same walk | **No** — same reason. A stored `name: Dave/Bob` is Tier-1-dirty and would be a hit, and it is excluded before `validate_strict` ever runs |
| Sentinel population (3) | same walk | **No** |
| **G4** (round-8, both columns) | scoped in its own text to *"every live `@*.md` note with parseable frontmatter — the same corpus and the same walk count 3 already did"* | **No** — it inherits the same corpus deliberately |
| **G1** | walks EVERY `.md` in the vault — the right corpus — but reports only cells (b) and (c), the UNDECLARED ones | **No, by one cell.** A forked note carries `type: person` (`model_to_frontmatter` emits it unconditionally, `writer.py:111`; `models.py:78`), so it lands in cell (a), *"declared, out of scope"*, and is never reported |

G1 is the closest and it misses by a single reporting decision, which is why this is one column on an
already-queued walk rather than a new pass. **Nothing measured or owed touches this population.**

**Same instrument as my round-4 finding, different target — stated plainly so the arc is legible.**
Round 4's finding was that count 1's `rglob("@*.md")` measured a proper subset of rule (ii)'s surface;
the answer was G1. This is the identical blind spot applied to a different population and a different
criterion, and it becomes decision-relevant only now, because until the architect's round-8 finding the
`@Dave/` directory was a thing the fix PREVENTS, not a thing the vault might already CONTAIN. I am not
re-raising G1 — G1's shape is right and unchanged; I am adding one column to its report.

**Two consequences, both landing on signed text.**

1. **`AC-2`'s clause has an unstated second half.** Whichever of (A)/(B)/(C) is taken, the criterion
   speaks only about directories the fix declines to create. If forked directories already exist, the
   fix leaves them, and a fixture asserting "no stray directory" on a clean tmp vault is silent about
   the vault as it stands. That is a scope statement the criterion should make deliberately rather than
   by omission.
2. **A forked note is permanently unrepairable through this package's own doors, and `AC-3` is the
   criterion that says otherwise.** `AC-3` promises a stored-dirty note stays writable for every write
   that does not set the name — which holds — and it was signed against count 3's finding that the
   legacy-dirty population is 79 total / 2 live, both intentional sentinel stubs, i.e. *"the premise is
   now historical"*. A note at `<vault>/@Dave/Bob.md` carrying `name: Dave/Bob` is legacy-dirty, is NOT
   in count 3's 79, and cannot be moved to `@Dave Bob.md` by any door in this package once the gate
   lands: the repair requires setting the name, which is exactly what is refused. Under the round-8
   identity rule the package also declines to normalize it. So if this population is non-empty, "the
   legacy-dirt premise is historical" was concluded from a corpus that structurally excludes the dirt
   this item's own headline defect produces.

**What I am not claiming.** I have no shell and did not read the vault, so I will not guess the count —
it may well be zero, and `create_stub` has cleaned the dominant inbound path since WI-105. But zero is
a measurement, not a default, and it is the one number that makes `AC-3`'s "historical" reading safe
and `AC-2`'s clause complete. The prior is not obviously zero: `CompanyRepository.save` inherits
`base.py:381` with no override and no name contract at all (the residue Finding B names with
`@Bausch/Lomb`), and company names carry `/` far more often than person names do — so the directory
half of this query must not be person-scoped.

**Altitude.** This opens no rung of the LESSONS #38 ladder: it is not about the checking machinery, it
runs no generator sweep, and it is a live-population question about a defect and a clause the document
already names. Its consequences land in `AC-2`'s directory clause and `AC-3`'s premise — both already
inside ruling 3's named set.

### Required grounding

Nothing added to the shell pass except one column and one listing that ride walks already queued.
Four items carried unchanged, one new.

1. **G1 — unchanged and still unrun.** Rule (ii)'s undeclared population at the rule's own
   path-agnostic scope, with the untyped/no-frontmatter split and the path-class split.
2. **G2 — unchanged and still unrun,** all three parts: per-field cells, the case sub-cell, the
   deletion column.
3. **G4 — unchanged and still unrun,** both columns. Correctly demoted by the round-8 fold to sizing.
4. **G5 — NEW. The population Finding F's defect has already created, two parts.** On G1's own walk
   (every `.md` in the vault, not `rglob("@*.md")`): **(a)** how many notes whose frontmatter carries a
   `type:` key sit at a path whose leaf does NOT match `@*.md` — i.e. G1's cell (a) reported by path
   class rather than discarded — broken down by `type:` value, with the stored `name:` of each and
   whether that name is Tier-1-dirty; and **(b)** a listing of every directory in the vault whose own
   name begins with `@`, with its contents, since that is the byte-level signature `base.py:381` +
   `ensure_dir` leaves and it is decidable without parsing anything. **Owed to:** this round.
   **Cheap:** (a) is one extra breakdown on a cell G1 already computes and discards; (b) is one
   directory listing. Not person-scoped — `CompanyRepository` inherits `base.py:381` unguarded.
5. **G6 — NEW, and it is an EXECUTION rather than a query, endorsed from the architect's own arc note.**
   Against a throwaway tmp vault under the DEFAULT lock home (no `OBSIDIAN_SCHEMAS_LOCK_DIR`), run
   `repo.save(Person(name="Dave/Bob"))` and list what is on disk afterwards; repeat for the D1c call
   `write_markdown_file(path, extra_fields={"type": "person", "name": "Dave/Bob"})`. This needs no
   vault and no live data. I book it as grounding rather than leaving it in the architect's prose
   because it is the Class-2 predicate in its purest form — the rule run against what exists, not
   reasoned about — and because per LESSONS #42 the composition `write_markdown_file × note_lock` is
   precisely the shape no number of readers can falsify. Eight architectural rounds, five red-team
   rounds, seven prior data audits and eight spec-writer rounds all reasoned about this one call; one
   execution settles it. The architect's note 2 rider is part of the spec, not of the probe: the
   eventual `AC-2` fixture must run under the default lock home or it is a control with no
   discriminating power.
6. **The consumer audit** — unchanged, still owed, still not a vault query.

### Conclusion

Every round-8 claim I checked re-derives from source, and the fold's decision to take (b′) is the right
disposition of my round-7 finding — it chose the shape that needs no number, and demoted the number to
sizing rather than quietly dropping it. That is convergence, not deferral.

What stops this being a PROMOTE is one item larger in kind than last round. **A clause of a signed
criterion is now known FALSE** — `AC-2`'s no-stray-directory promise and scenario 1's first clause
cannot be met by any gate call inside `write_markdown_file`, confirmed from source above — and the
three repairs the architect offers are open, un-chosen and un-executed. On top of that, G1, G2 and G4
have still never run, and this round adds a population that no count run or owed can see: the notes and
directories Finding F's defect has already produced in the live vault, which bear directly on whether
`AC-3`'s "the legacy-dirt premise is historical" survives. Promoting now would release the D3 brake at
the exact moment a criterion is about to be re-signed against a false clause and an unlooked-at
population. Stage stays at `exploring`.

**Signal for the factory, stated because the targets line alone cannot carry it.** This is a converging
round and the arc remains visible in what closed: rounds 1–3 named the untyped-dispatch premise (closed
by ruling 1); round 4 named count 1's scope (discharged → G1); round 5 named the per-field split
(delivered → G2); round 6 named the dict-arm deletion (closed in text → G2's third column); round 7
named the (b′)/(a′)/(c′) blast radii (discharged this round — the fold chose the free shape → G4). No
target has been re-raised, and each round's target was closed before the next was named. This round
names a different thing again — the live population behind a defect the architect only made
decision-relevant this round — and asks for one extra breakdown on a walk already queued, one directory
listing, and one command against a tmp vault. **What has not moved is the thing no gate spawn can
move:** G1, G2, G4, G5 and G6 all need a shell outside every cage, and this spawn has no Bash tool at
all, so they are not merely unrun but unrunnable here. My round-6 and round-7 notes predicted that
further spawns before those numbers exist would reproduce this section; they have, and a ninth will
too. **The unblock is unchanged in order and does not lengthen:** Dave re-originates `AC-1`–`AC-4` in
ONE round (now also ruling on (A)/(B)/(C) for `AC-2`'s directory clause, which the architect scoped as
direction rather than design), and the same shell-holding actor runs G1, G2, G4, the two parts of G5,
the one-command G6 and the consumer audit's two greps alongside it. G6 is the cheapest item on that
list and retires the largest class.

```verdict
gate: data-premise
verdict: REVISE
date: 2026-08-11
model: claude-opus-5
targets: AC-2, AC-3, #exploration-notes
note: Round 7's blast-radius finding is discharged by the fold's (b′) choice, and architect round 8's stray-directory finding is confirmed from source on every leg (note_lock at writer.py:209 → ensure_dir(sentinel.parent) at vault_io.py:400, home defaulting to target.parent/SENTINEL_DIR_NAME at vault_io.py:350 with _configured_lock_dir None by default at :137-152, mkdir(parents=True) at :632-638 with no compensating action) — so AC-2's signed no-stray-directory clause is FALSE as written; and its data half is unmeasured: Finding F's defect succeeds today (writer.py:273, base.py:381), so the vault may already hold notes at <vault>/@X/Y.md, a population count 1, count 3 and G4 all miss because their leaf is not `@*.md` and G1 misses by one cell because such a note is `type:`-declared and lands in G1's discarded cell (a) — which is also the corpus count 3's "the legacy-dirt premise is historical" reading (AC-3) was concluded from; new G5 reports it as one breakdown on G1's own walk plus an `@*` directory listing, and new G6 books the one tmp-vault execution (LESSONS #42) that eight reading rounds could not substitute for.
```

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
