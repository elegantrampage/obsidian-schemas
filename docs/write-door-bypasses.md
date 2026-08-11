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
| D2 | `BaseRepository.save` (base.py:356) → D1; derives the FILENAME from `entity.name` at base.py:381 | no | no |
| D3 | `PersonRepository.save` (person.py:1255) → D2 | no | **yes** — `_normalize_address_fields` at :1269 |
| D4 | `BaseRepository.update_fields` (base.py:403) — arbitrary `updates` dict, and it auto-appends the old file stem to `aliases` on a name change (:443-448) | no | no |
| D5 | `writer.update_frontmatter_field` (writer.py:292) — public, no repository involved | no | no |
| D6 | `writer.update_frontmatter_fields` (writer.py:350) — public | no | no |
| D7 | `writer.roundtrip_file` (writer.py:402) — re-serializes an existing note's own frontmatter | no | no |
| D8 | `scripts/lint_vault.py` `--fix` (lint_vault.py:876-882) — builds `fm`, serializes, calls `vault_io.write_note` directly | no | no |

Only `create_stub` (person.py:1345) carries the name contract, at :1407, and only `PersonRepository.save`
carries the address contract. Every other door is open. `_writeback_identifier` (person.py:1192)
reaches D4 with a raw string at :1217 — N3, confirmed live.

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

### Finding B — the seam is `write_frontmatter`, and it is total over the tree today

Every one of D1–D8 calls `writer.write_frontmatter` (writer.py:133) immediately before the bytes
exist: writer.py:266, :335, :387, :421, base.py:454, lint_vault.py:880. There are exactly six
`f"---\n{yaml}---\n"` constructions in the package and scripts, and all six are fed by that call.
Below it every value is a string; above it the field NAMES are still present. That is the last
point at which "this value is a `name`" and "this value is an `emails[]` entry" are decidable, and
therefore the seam this item is about.

Dispatch is decidable there too: `Person.type` is `Literal["person"]` (models.py:78), so an entity
write always carries `type: person` in the dict, and a dict-shaped write inherits it from the note
it parsed. The residue, stated rather than hidden: a hand-created note with no `type:` key is
invisible to a `type`-keyed dispatch — and a `type`-keyed dispatch's natural default is to read that
absence as "not a person write", which would open a bypass UPSTREAM of every check this item
installs, one that no amount of door coverage below it can catch.

**Resolved here rather than deferred, by adopting the rule the tree already has.**
`BaseRepository._owns` (base.py:257-264) faces exactly this ambiguity and answers it fail-closed:
when the note declares nothing, the only remaining evidence is the glob, and the glob counts *only
if it is a naming convention rather than a catch-all*. `@*.md` (base.py:197, which PersonRepository
does not override) is such a convention, so an untyped note under it IS claimed as a person note.
This item inherits that answer verbatim: **absence of `type:` never exempts a write from the gate.**

That is pinned as behaviour on BOTH halves of the gate — AC-2's untyped clause for names, AC-4's for
identifiers — not left to the architect. The two-place pinning is deliberate rather than redundant:
dispatch runs ONCE per write, upstream of the name/address distinction, so a single wrong
`if frontmatter.get("type") == "person":` would silently switch off whichever half is unasserted.
The Intent's wording ("no door … through which an unvalidated name **or** unnormalized address can
pass") draws no distinction between the two halves, so neither may the gate's dispatch. What remains
open for the architect is only the MECHANISM — whether each door passes the gate an explicit
entity-type argument, or the gate re-derives ownership from the target path the way `_owns` does —
and either mechanism must satisfy the same pinned behaviour, on both halves.

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

Every other door binds the dict it serializes exactly once (`update_fields` base.py:451/:454;
`update_frontmatter_field` writer.py:332/:335; `update_frontmatter_fields` writer.py:384/:387;
`roundtrip_file` writer.py:419/:421; `lint_vault --fix` lint_vault.py:876-880; and both `save`
methods, which reach bytes only through D1a). So the door set is **ten arms across eight functions** —
D1a, D1b, D1c, D2, D3, D4, D5, D6, D7, D8 — and AC-1's floor is stated in those terms. Because AC-2
and AC-4 bind their coverage to AC-1's derived set, per-arm derivation is what makes "a fixture
through the `entity=` arm specifically" a requirement neither of them has to hand-list, and what
makes a fourth arm added later join all three criteria automatically.

**Where the untyped dimension EXISTS, and where it cannot.** The residue above is a property of
dict-shaped arms specifically, so both untyped clauses are scoped by ARM shape rather than asserted
over the whole set:

- **Dict-shaped arms — D1b, D1c, D4, D5, D6, D8.** A frontmatter dict reaches the gate whose `type:`
  key the gate must read, either because the caller supplied it (D1b writer.py:259, D1c :263) or
  because the door parsed it off the note on disk and merged the caller's updates into it
  (`update_fields` base.py:439/:451; `update_frontmatter_field` writer.py:329/:332;
  `update_frontmatter_fields` writer.py:381/:384; `lint_vault --fix` lint_vault.py:876-882). On every
  one of these, `type:` can genuinely be absent — a hand-created note simply never had the key, and a
  caller-supplied dict need not carry one — and the dispatch branch is live. This is where the
  untyped pass discriminates.
- **Entity-shaped arms — D1a, D2, D3.** The arm's only field source is a typed model. Here the
  untyped case is UNCONSTRUCTIBLE, not merely unlikely: `model_to_frontmatter` iterates
  `model_class.model_fields.keys()` (writer.py:111) and emits every declared field, and
  `Person.type` is `Literal["person"] = "person"` (models.py:78) — a declared field with a default —
  so the serialized dict always carries `type: person` no matter what the caller passes, and
  `extra_fields` cannot displace it through the guarded merge. There is no type-keyed branch for an
  implementation to get wrong, so an "untyped" fixture on these arms would pass whether or not the
  dispatch rule was implemented correctly: a control with no discriminating power, which is worse
  than no control because it reads as coverage.

`write_markdown_file` therefore sits in BOTH classes, and stating the split at ARM granularity is
what lets that be said precisely: D1a is excluded from the untyped pass, D1b and D1c are in it, and
the function is never excluded or included wholesale. The exclusion sets in AC-2 and AC-4 name arms
for the same reason.

### Finding C — the delta rule, and why the seam is not the gate's home

Validating the WHOLE record at that seam would brick the vault. The 2026-06-02 audit that produced
NameValidator found real Tier-1 dirt across 1647 live notes; WI-111 and WI-117 each removed
individual corrupt names by hand as late as June. Under whole-record validation, every one of those
surviving notes becomes permanently unwritable — an unrelated `company` update through D4 would
raise, `roundtrip_file` could never normalize one again, and `lint_vault --fix`, the tool whose job
is to repair them, would be refused before it could write the repair. The remedy would be the
disease.

So the rule is: **judge what the write INTRODUCES, never what it preserves.** An entity write (D1–D3)
rewrites the whole record from a typed model, so its name IS the delta. A dict write (D4–D6, D8)
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
   behaviour delta on live data, not a refactor.
3. `create_stub` currently trusts parseaddr on a BARE input; `Email.parse` deliberately does not.
   Adopting the authority means `create_stub` inherits that refusal.

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
- **Effort:** one to two sessions. One new module, routing at eight sites, one derived wall, the
  splitter consolidation, and the invariant tests.
- **Test floor is directional** — run the floor command for the current count; a drive landing fewer
  cases than the previous run has lost a file.

### Where this goes next

**Hand off to the architect before the spec.** The architect's trigger heuristics fire on three
counts: a new module, a contract change that crosses into three downstream repositories, and a
derived-wall enforcement mechanism that has to be designed rather than copied. The open questions
the architect should take are: whether the gate's signature is `(existing, incoming)` or two
separate entry points for entity- and dict-shaped writes (Finding C); whether `Email.parse`'s
stricter acceptance is adopted wholesale or the splitter keeps a compatibility arm for the parens
form (Finding D); and by what mechanism a door tells the gate what entity it is writing — an
explicit argument per door, or path-derived ownership in the `_owns` shape (Finding B). Note that
the no-`type:` BEHAVIOUR is no longer an open question: Finding B settles it fail-closed and AC-2
pins it, so the architect is choosing a mechanism that satisfies it, not choosing whether to honour
it. Also owed at spec time: the derived-wall predicate for AC-1 and AC-5 — both are match-shape
walls in the WI-004 sense and must ship the fixture battery `tests/test_write_routing.py:1-18`
describes, which is the precedent to copy rather than re-derive. AC-1's predicate now has to resolve
at ARM granularity (Finding B): the members are the distinct bindings of the dict a function passes
to `write_frontmatter`, so a function with three such branches yields three members. That is the one
genuinely new piece of AST work in this item — the existing `_is_write_call` (derivations.py:238)
answers "does this function write", not "through which branch" — and it is the predicate the gate's
own routing must satisfy branch by branch.

## Approach

Build **one semantic gate** — a single function, in a module of its own, that takes what a door
knows (the fields that write is INTRODUCING, plus the entity type) and returns them validated and
normalized, or refuses. Names go through `NameValidator` unchanged; addresses go through one new
shared splitter built on `identifier.Email.parse`, which replaces both duplicate parseaddr sites;
phones dedupe on `normalize_phone`'s output while storing the display form. Route all eight doors
through it — `write_markdown_file`, `BaseRepository.save`/`update_fields`,
`update_frontmatter_field(s)`, `roundtrip_file`, `_writeback_identifier`, and `lint_vault --fix` —
and prove the routing TOTAL with a derived AST wall in `tests/derivations.py`, so that the ninth
door someone adds next month is red at test time rather than silently unguarded. The gate judges
the DELTA, never the stored record, which is what keeps every pre-existing dirty note writable by
the tools whose job is to repair it. Refusals convert to a `LoudFailError` carrying the stable
NameValidator pattern key in `declared_type` and no note content, so `except LoudFailError` remains
the one idiom for "this package refused".

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
