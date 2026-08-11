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
