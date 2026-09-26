---
id: WI-029
title: 'Filename/name divergence repair: rename the forked stems, then pin the invariant'
project: obsidian-schemas
stage: done
created: 2026-09-06
last_touched: 2026-09-26
stage_changed: 2026-09-26
touched_by: spec-writer
tags: []
depends_on: []
transitions: ["idea>exploring@2026-09-21@porter", "exploring>specced@2026-09-25@porter", "specced>ready@2026-09-26@porter", "ready>building@2026-09-26@porter", "building>done@2026-09-26@porter"]
review_level: L3
review_level_provenance: selector
---

# Filename/name divergence repair: rename the forked stems, then pin the invariant

### Archived Rounds

<!-- archive-split: machine-maintained pointer; do not edit -->
Settled gate rounds for this item live in `docs/filename-name-divergence-repair-rounds.md` — every round at a conveyor door
this item has already advanced past, byte-for-byte, append-only, never rewritten. READ ON DEMAND
ONLY: each gate's latest standing round is still in this document, so nothing needed to advance this
item is in the drawer. Open it only to read a settled round's full reasoning.

## Problem / Motivation

Three live person notes carry a filename stem that differs from their stored `name:` — measured as
G4(b) in WI-021's 2026-08-11 shell pass and re-confirmed 2026-09-05: `@Dave Martin Right to Left.md`
vs `name: …Right To Left`, `@Maritza.md` vs `name: Maritza Bonano`, `@Owen OLoan.md` vs
`name: Owen O'Loan`. `BaseRepository.save` binds the target filename from the raw `entity.name`
(`base.py:381`) and never renames or unlinks, and WI-021's gate declines by design to repair a name
(its name output is an identity), so each of these notes forks into a SECOND note for one person on
its next `save()` — WI-021's "parked defect 1" corruption class, live today rather than
hypothetical. WI-021 explicitly scoped this out ("no rename, no backfill, no sweep") and named it
as the next item's neighbourhood.

The same shell passes booked four hand repairs that have no home and should ride with this item
so they are not lost: one book note carrying `type: person` (`The New York Trilogy - Paul
Auster.md`, `name: Nicole Stocker`, G5(a)), four notes with frontmatter but no `type:` (G1 bucket
(b), live), and three book notes whose frontmatter fence opened and did not parse (G1 bucket (d)).

**Queue review 2026-09-21 (Dave: ranking agreed — this item is now FIRST in `queue_order`; "proceed
with your recommendation" on the fold below).** Premise re-verified: the class has GROWN — the census
(`docs/vault-shape-census.md:262`, measured 2026-09-07) counts **8 live** stem≠name person notes against
the three named above, and `BaseRepository.save` still binds the filename from `entity.name`
(`base.py:381`). FOLD, counts only: load-time identity-reconciliation conflicts
(`PersonRepository.conflicts`, the load-time kind — one identifier on more than one note) are the
same duplicate-note class as a forked stem, so this item's conductor entry/exit measurement records
`len(PersonRepository().conflicts)` beside the divergence count, and the invariant test asserts it is
zero over the corpus. On 2026-09-21 one such pair was observed at the morning load (a two-note
conflict, last-wins) and had been merged by the re-check an hour later (1,172 → 1,171 person notes,
conflicts 0) — nothing to repair by hand today, and exactly the shape that should be visible on a
readout rather than in a log line nobody reads.

## Intent

A person note's filename and its stored name agree, everywhere in the live vault, and stay that
way: the forked notes are renamed once through the one sanctioned door (`vault_io.move_note`,
old stem preserved as an alias so nothing that referenced the old file goes dark), and an invariant
test over the corpus goes red the moment the class recurs — so this is the last time it is repaired
by hand. The booked hand repairs are done in the same pass and the counts that found them are
re-run to zero.

*(Sharpened at `exploring`, 2026-09-21: "the three forked notes" → "the forked notes". The count is
8 as of the 2026-09-07 census and the Problem section carries the re-verification; a frozen number
in the intent anchor would be falsified by the vault before the build starts. Nothing else in this
section is touched — the mechanism it names is re-derived below rather than rewritten here.)*

## Exploration Notes

Ideation ran cold-start, `involvement: null` → **approval-only**: the approach below is re-derived
from the frozen `## Intent` rather than inherited from the mint, and the mint's named mechanism
(`vault_io.move_note` + an invariant test over the corpus) is treated as a hypothesis (WI-146 tweak
11). One half of it survives intact, one half does not — see "Where the invariant can actually
live".

**Revised 2026-09-21, after the architect's REVISE round 1 (recorded in full at the end of this
document).** The finding was that the first draft's seam bound the write target by NAME
(`get_file_path(entity.name)`) while the Intent, the WI-185 section and AC-1 all require it bound by
PROVENANCE. It was correct, and the objection's own framing named the fix: the structure is already
built at the parse boundary and discarded one line later. Changed then: premise 2 amended (the
name→path map is not provenance) and premise 8 corrected (rename cost is linter noise, not a wrong
auto-rewrite); premises 10 and 11 added, both executed; "Where the structure lives" re-answered;
approach C re-derived as provenance-bound, with the name-keyed version kept as rejected C′ rather
than deleted; the incoming-reference disposition CHOSEN (accept the noise knowingly) instead of
left open; precondition 2's question list extended; AC-1 rebound to files and given the unloaded,
round-tripped and no-leak arms; AC-2 given the re-stamp arm. AC-3 and AC-4 were untouched — the
objection confirmed both.

**Revised again 2026-09-21, after REVISE round 2 (same document, below).** Round 1's fold held; the
finding this time was that it held only at ONE site. The stamp was read by `BaseRepository.save`
alone, while eight other mutating paths in the same package still resolved their target from a name
— so AC-1's "no library write" headline was false, and AC-2(c)'s own rename door was driven from
`update_fields`'s name-keyed lookup, able to move the wrong note of a live collision pair. Both
closing options were on the table; **(i) is chosen** — every write target in the package resolves
through ONE function. Changed here: premise 12 added (the write-path population, executed
site-by-site) and the "read at one site" sentence in the blast-radius bullet corrected, because it
is what made the gap invisible; a new subsection, "One target function, not one read site", carries
the decision and the fallback asymmetry it has to respect; `## Approach` (1) and (2) rewritten
around the one function; precondition 2's question list extended to the five body-writers and the two
`save` overrides, since it is HEAD-probed before the criteria freeze and would otherwise measure the
blast radius with the consumers' highest-volume write path missing; AC-1's oracle DERIVED over the
write-path population rather than exercising `save` alone, with the save-only arms kept where they
belong; AC-2 given the `update_fields`-reload re-stamp arm; **AC-5 added** — the containment wall
that makes the one function un-routable-around, on WI-031's own precedent. AC-3 and AC-4 remain
untouched across both rounds.

**Revised a third time 2026-09-21, after REVISE round 3 (same document, below).** Rounds 1 and 2 both
checked the MECHANISM against the code and neither checked the CORPUS against the criteria. Round 3
ran AC-1's own subject predicate over the frozen manifest and found the class's EXTENSION is not what
the criteria said: the stem≠name predicate selects **four** person notes, not the two AC-3 pinned nor
the three AC-1's rationale named, and the collision third is not among them — while two of the four
carry a stored `name:` that WI-021's gate permanently refuses, so `save()` on them raises before a
byte is written and "rename the file to match the stored name" is not merely wrong for them but
unexecutable. The whole predicate was re-executed here over the manifest before folding (premise 13);
it is confirmed, note for note. Changed: premise 13 added (the executed divergent population, with
the gate's verdict per member); a new subsection, "Which notes ARE the class", carrying the class
definition, the TWO derivations AC-1 needs and the gate-refused rule; two constraints added (a name
the gate refuses can never fork, and cannot be repaired by rename); `## Approach` corrected — the
body-writer count ("six"/nine) and the detector's dirty-name marker; precondition 1's direction table
given its third column BEFORE it is commissioned; AC-1's `why` corrected in both directions and its
group derivation DEFINED rather than assumed, with the `save` cell of a gate-refused subject given a
declared expected outcome; **AC-3 amended for the first time in this arm** — four ERRORs, the
dirty-name marker, and the comparison stated raw-vs-raw; AC-4's shape check extended to the third
column; AC-5 rebound to `tests/derivations.py`'s three-name `DOOR_NAMES`. The seam, the door, the
fallback asymmetry and AC-2 are untouched — round 3 confirmed all four.

**Revised a fourth time 2026-09-21, after REVISE round 4 (same document, below).** Round 3's fold held
note for note; the finding is inside the RULE that fold added. "A name the gate refuses can never
fork" was written as a total property and then spelled, in four places, as
`NameValidator.validate_strict` — which is not the question the write door asks. `Tier1Branch` carries
`sentinel_exempt`, `pure_digit` sets it, and `gate_write` DERIVES `allow_phone_sentinel` from the
payload (premise 14, executed here), so a divergent phone-only stub that declares `phones` is WRITTEN
where the rule predicted `NameGateRefusal` — and the census measures that branch at **2 live person
notes**, so the contradiction reaches precondition 1's table, which is commissioned once outside the
cage. Changed here: premise 14 added; the "can never fork" constraint replaced by the **door
predicate**, stated ONCE in "Which notes ARE the class" and INHERITED by the other three sites rather
than re-spelled in each; AC-1's gate-refused cell rebound to that predicate and given the planted
sentinel-exempt discriminator the corpus cannot supply (WI-286: the member that tells the two rules
apart); AC-3(c)'s marker rebound and its message re-scoped; AC-4's consistency rule rebound and the
sentinel-exempt row explicitly admitted as a legitimate `rename`; precondition 1's (b3) restated to
the door's own call. Two non-blocking notes folded: the "unexecutable" argument restated as a POLICY
with its reason (it is literally unexecutable only for `path_hostile`), and `update_fields`'
move-then-reload ordering named in `## Approach` (2) and AC-2's rationale. The population premise 13
measures, AC-1's union subject derivation, AC-3's four-ERROR count, the seam, the door, the fallback
asymmetry and AC-5 are untouched — round 4 confirmed all of them.

**Revised a fifth time 2026-09-21, after the AC RED-TEAM's REVISE round 1 (same document, below) — the
first gate round in this arc that is not the architect's.** Four architect rounds attacked the
MECHANISM and the corpus it quantifies over; this one attacked the CRITERIA's own construction, and
found the one place where two of them are satisfiable by a stub. The finding is exact and reproduces:
AC-1's Book and Meeting subjects were not required to be DIVERGENT, and AC-5's SEAM-ROUTED bucket
asked only whether `_resolve_write_target` is CALLED — so `BookRepository.save` and
`MeetingRepository.save` could add one line, call the function, discard its return, keep today's
`_get_file_name`-derived write, and go green on every arm. Those are precisely the two sites round 2
widened the seam to reach, and "one line each" was the argument for touching them at all. Changed
here: premise 15 added (both filename derivations read, and both spellings of the escape traced
through `tests/derivations.py`'s own shipped taint machinery); a new subsection, **"Divergence is not
a Person-only predicate"**, which states the divergence predicate in its TYPE-GENERAL form — the
type's own filename rule recomputed from the entity's current fields, of which premise 13's raw
stem≠name is the Person instance — and generalizes the name-sharing group to a COLLIDING group, so the
Book and Meeting plants are one shape rather than two ad-hoc fixtures; "One target function, not one
read site" given the clause that call-presence is not routing; `## Approach` (1) corrected on both
points; AC-1's subject set given the two planted colliding groups with their divergent members, and
(b)/(c) asserted over them; AC-5's SEAM-ROUTED bucket restated as a DATA-FLOW property, with the
escape battery extended by both spellings of call-and-discard and by the ACCEPTED near-miss that keeps
the fallback asymmetry legal. The seam, the door, the door predicate, the fallback asymmetry, AC-2,
AC-3 and AC-4 are untouched — the red-team re-executed premises 13 and 14 independently and confirmed
both, and found nothing else material.

### Data-premise audit (WI-147), run before any approach work

Every predicate below was EXECUTED against this tree as the drive seeded it — worktree
`cage-wt-rix_vnom`, git HEAD `6f045a9` plus the seeded uncommitted delta (one untracked doc,
`docs/whatsapp-jid-value-type.md`, irrelevant here) — using the reader's granted tools (Read, Grep,
Glob; no shell). Each is a dated snapshot another reader can re-run.

1. **The fork mechanism is still live, and its citation has drifted.** `BaseRepository.save` binds
   `name = getattr(entity, "name", "Unknown")`, `filename = f"@{name}.md"`,
   `file_path = self.vault_path / filename` at **`base.py:391-393`** — the mint and the queue-review
   fold both cite `base.py:381`, which is WI-021-era numbering and is now 10 lines stale. The
   method body (`:367-412`) contains no `unlink`, no `rename`, no `replace`: it cannot move a note,
   only write beside one. Predicate: read of the whole method.
2. **The repository holds a name→path map, and it is NOT provenance.** `_file_map` is filled at load
   with the note's real path keyed on the lowercased name (`base.py:241-248`), and `get_file_path`
   returns it (`:354-365`). `save` consults neither. `update_fields` DOES (`:438`) — which is why
   `update_fields` has never forked anything. But the map is **one path per name**, filled last-wins
   over `vault_path.glob`, i.e. in filesystem order; and `_ensure_loaded` is a **no-op** when
   `auto_load=False` and `load()` was never called (`:210-213`), so `get_file_path` then returns
   `None` for everything. Two notes sharing one `name:` therefore have exactly one entry between
   them, and an unloaded repository has none. *(Amended 2026-09-21 after the architect round: the
   original premise read "the repository already KNOWS the right path and throws it away", which is
   true of `load()` and false of `_file_map`. That overstatement is what put a name-keyed lookup into
   the first draft's seam; see "Where the structure lives".)*
3. **`update_fields` is a deliberate PRODUCER of divergence.** On a name change it appends the old
   stem to `aliases` and writes back to the *existing* file (`base.py:454-459`, then `:490`). The
   filename is left behind on purpose, with the old stem preserved as an alias. So "stem equals
   name, everywhere" is not merely unenforced today — one shipped, deliberate library behaviour
   contradicts it. This is the single most consequential finding of the exploration.
4. **In-library `save()` callers are all CREATE paths.** Grep for `\.save\(` over
   `obsidian_schemas/**`: `person.py:1340` (inside `create_stub`), `book.py:322`, `company.py:238`,
   plus `person.py:1197`'s `super().save(...)` delegation. None of them re-saves an entity loaded
   off a divergent stem — **so every in-tree call site is fork-free today and the fork arrives
   through a CONSUMER's `repo.save(person)`**, which this cage cannot read (see the second
   precondition fence).
5. **`vault_io.move_note` has exactly one caller in the whole tree** —
   `scripts/lint_vault.py:1343`, the `--quarantine` path. Predicate: grep `move_note` over the
   tree; the only other hits are docs and `state/**`. Door 3 is therefore essentially unexercised
   machinery: it refuses a symlinked source, refuses an existing destination by syscall
   (`os.link` → `NoteAlreadyExists`), links-then-unlinks so a mid-flight failure leaves a duplicate
   rather than a hole, and takes both locks in a global total order (`vault_io.py:721-783`).
6. **`lint_vault` has no divergence detector.** Grep `stem_name` over `scripts/lint_vault.py`: zero
   hits. The five check functions are `check_structural`, `check_completeness`, `check_links`,
   `check_timeline`, `check_noise`; the nearest neighbour is `person_missing_name`, which repairs in
   the OPPOSITE direction — `name = fpath.stem.lstrip("@")` (`:1043-1044`), i.e. the path is already
   treated as the authority when the field is empty.
7. **The frozen fixture corpus CONTAINS this defect class, by design and behind a digest.** Three
   notes — `tests/fixtures/vault/@Quillam Ostrivane.md`, `@Quillam Lumbrek.md`,
   `@Quillam Ostrivane Lumbrek.md` — all carry `name: "Quillam Ostrivane Lumbrek"` (predicate: grep
   `^name:` over `tests/fixtures/vault/@Quillam*.md`, three files, one value). Two are declared
   `shape_classes=("stem_name_divergence",)` and the third is the census's mandated three-filename
   collision (`tests/fixture_vault.py:255-276`). The corpus is byte-frozen by `CORPUS_DIGEST`
   (`tests/fixture_vault.py:44`), so growing it is a paired manifest+digest edit, not a drive-by.
   *(Round 3: this premise reads the LABELLED specimens and is true as far as it goes, but it is not
   the class's extension — the `Quillam` group is one name-sharing group of three, of which only TWO
   diverge, and the divergence predicate selects two FURTHER notes this premise never mentions. The
   executed population is premise 13, and it is what both AC-1 and AC-3 are now written against.)*
8. **`lint_vault` resolves wikilinks by STEM only — and the cost of that is NOISE, not a wrong
   rewrite.** `check_links` tests membership in `idx["all_stems"]` for `person_company_not_found`
   (`:517`), `meeting_attendee_not_found` (`:535`), `company_people_link_broken` (`:550`) and
   `broken_wikilink` (`:567`), with one trailing-whitespace fallback (`:569`) and one meeting-date
   fallback (`:573-579`). Frontmatter `aliases` are consulted nowhere in that function. Obsidian
   itself resolves `[[X]]` through aliases; this project's own linter does not. *(Corrected
   2026-09-21 after the architect round, and the correction matters because it changes a decision
   below.* The first draft added "and `broken_wikilink`'s fixable arm may then propose a wrong
   rewrite". Re-read: that arm is reached only when `MEETING_DATE_PATTERN.match(link_target)`
   succeeds AND exactly one dated candidate exists (`scripts/lint_vault.py:572-592`); a person stem
   cannot match that pattern, so a renamed person note's incoming links land on the non-fixable arm
   at `:594-600`, and `apply_fixes` handles only the JSON-carrying arm (`:1085-1096`). So a rename
   can produce linter WARNINGS at an unmeasured volume, and cannot produce a wrong auto-repair.*)
9. **The fork's downstream harm, read off the code.** The cache and `_file_map` key on the
   lowercased NAME (`base.py:319-321`, `:245-246`), so two notes sharing one `name:` collapse to one
   cache entry, glob order deciding the winner — the loser's timeline and identifiers become
   invisible to `get`/`get_all` while remaining on disk. Their identifiers collide in the WI-125
   index and land on `.conflicts` with a WARN (`person.py:336-366`), which is exactly why the queue
   review's fold of `len(PersonRepository().conflicts)` into this item's measurement is the right
   instrument rather than a second metric.
10. **The provenance this item needs ALREADY EXISTS, one frame above where it is dropped.**
    `parse_markdown_file` returns a `ParsedDocument` carrying `file_path` — a declared field
    (`parser.py:54`) set from the path it was handed (`:236`, `:246-252`). Every loader in the
    package goes through it: grep `parse_markdown_file` over `obsidian_schemas/**` gives the
    `__init__` re-export plus exactly three call sites, `base.py:311`, `book.py:79`,
    `meeting.py:83`, and all three do the same thing — `return doc.entity` (`base.py:311-314`),
    discarding `doc.file_path`. The binding "this entity came from this file" is therefore
    constructed at the parse boundary, held for three lines, and thrown away before any caller can
    see it. *(Executed 2026-09-21. This is the premise the revised seam stands on, and it is why
    the seam is ONE edit at ONE site rather than a per-repository change.)*
11. **A provenance stamp cannot leak into a note — but only as a declared PRIVATE attribute.**
    `entity_to_frontmatter` builds the written mapping from `type(entity).model_fields` plus
    `entity.model_extra` and nothing else (`writer.py:106-123`); a pydantic `PrivateAttr` is in
    neither, so it is unwritable by construction. The inverse is the trap: `BaseEntity.model_config`
    sets `extra="allow"` (`models.py:31-32`), so a bare `entity.source_path = p` assignment lands in
    `model_extra` and would be serialized into **every note the library writes**. Predicate: read of
    both sites. The mechanism below is therefore specified as a private attribute, and the
    unwritability is cheap to assert rather than assumed.
12. **`save` is NOT the package's only name-bound write path — there are nine, and the fold's first
    draft reached one.** Predicate, executed 2026-09-21: grep
    `write_markdown_file|vault_io\.write_note|get_file_path\(` over `obsidian_schemas/**`, then read
    each enclosing function. The population that derives a mutation target from a NAME rather than
    from the note it read:
    - `BaseRepository.save` — `@{name}.md` at `base.py:391-393`, written `:398`. *(The fold's one
      site.)*
    - `BaseRepository.update_fields` — `get_file_path(name)` at `base.py:438`, written `:490`.
    - Five MUTATING `PersonRepository` body-writers, each opening with the identical
      `file_path = self.get_file_path(person.name)`: `append_to_timeline` (`person.py:1403`, writes
      `:1447`/`:1458`), `append_to_body_section` (`:1522` → `:1559`), `add_to_discuss_item`
      (`:1653` → `:1679`), `update_to_discuss_item` (`:1719` → `:1758`), `remove_to_discuss_item`
      (`:1793` → `:1828`). A sixth site, `_get_body_content` (`:1590`), is the same lookup on a READ
      and so reads the wrong note rather than writing it — same root cause, outside AC-1's
      write-path scope, worth one line in the spec.
    - `BookRepository.save` (`book.py:167-170`) and `MeetingRepository.save` (`meeting.py:189-192`)
      **override and never call `super().save()`** — each derives its own filename from
      `self._get_file_name(entity)` and calls `write_markdown_file` directly. So a stamp set at the
      parse would be set and never read for Book and Meeting entities.

    **Nine mutating paths, then** — `save`, `update_fields`, five body-writers, two `save`
    overrides — of which round 1's fold reached exactly one.

13. **The defect class's EXTENSION over the frozen corpus is FOUR notes, and two of them cannot be
    `save()`d at all.** Predicate, executed 2026-09-21 by hand over `tests/fixture_vault.py`'s
    manifest (read in full, `NOTES` at `:217-479`): every entry with `declared_type="person"` and a
    declared `fields` mapping whose filename stem, less the leading `@`, differs from
    `fields["name"]` — compared RAW, no cleaner on either side. Twenty-two person notes declare
    fields (`LOADABLE`'s own comment says the same, `:521`); four diverge:

    | note | stored `name:` | manifest carries | the gate's verdict on that stored name |
    |---|---|---|---|
    | `@Quillam Ostrivane.md` (`:255-260`) | `Quillam Ostrivane Lumbrek` | `shape_classes=("stem_name_divergence",)` | clean — loads and saves |
    | `@Quillam Lumbrek.md` (`:261-266`) | `Quillam Ostrivane Lumbrek` | `shape_classes=("stem_name_divergence",)` | clean — loads and saves |
    | `@Perrowin Tessamund Drostane.md` (`:297-301`) | `Perrowin -> Tessamund Drostane` | `discriminator="arrow_connective"` | Tier-1 REFUSED, `pattern="calendar_prefix"` |
    | `@Yolvenna Brindlecote Skarnell.md` (`:302-306`) | `Yolvenna/Brindlecote Skarnell` | `discriminator="path_hostile"` | Tier-1 REFUSED, `pattern="path_hostile_char"` |

    Three facts fall out of that table and each of them contradicted a criterion as drafted.
    (a) **`@Quillam Ostrivane Lumbrek.md` (`:273-276`) is NOT selected** — its stem and its stored
    name agree exactly. It is the corpus's mandated three-filename collision and it enters this item
    as a member of a name-SHARING group, which is a different predicate; AC-1's rationale previously
    claimed the stem≠name predicate picks it up, and it cannot.
    (b) **The two unannounced members are gate specimens, and the gate refuses their names.**
    `TIER1_BRANCHES` declares `arrow_connective` (`name_validation.py:214-225`, regex `->|[→⟶⇒➜↦⇨]`,
    `pattern="calendar_prefix"`) and `path_hostile` (`:249-259`, regex `/`,
    `pattern="path_hostile_char"`); the expected refusal value is the branch's `pattern` field and
    never its `branch_id`, which is the manifest's own rule (`tests/fixture_vault.py:288-293`).
    `save` reaches the gate: `write_markdown_file` sets `gate_whole_record = True` on the
    `entity is not None` arm (`writer.py:229-233`) and calls `gate_write` once, above the lock
    (`:252-253`), so a `save()` of either entity raises `NameGateRefusal` before any write. The
    refusal is by design and permanent — `name_gate.py:33` says so outright.
    (c) **The other eight write paths are NOT refused for those two.** `update_fields` gates the
    DELTA with `whole_record=False` (`base.py:483-485`), and the comment at `:466-469` states the
    intent verbatim: a note whose stored name is already Tier-1 dirty stays writable for every write
    that does not re-introduce that name. The five body-writers reach `vault_io.write_note` directly
    with no gate call at all (read of `append_to_timeline`, `person.py:1403-1461`). So the
    gate-refusal is TWO CELLS of AC-1's (subject × path) matrix, not two subjects.

    Three narrowings, all read off the code and all load-bearing for how wide the fix has to be.
    (a) `PersonRepository.save` delegates through `super().save()` (`person.py:1197`) and
    `CompanyRepository` declares neither `save` nor `get_file_path`, so those two DO inherit
    whatever `BaseRepository.save` does. (b) The hazard does not arise for an entity obtained from
    the cache: `_cache` and `_file_map` are filled in the same iteration under the same key
    (`base.py:244-246`), so they agree. The exposed population is entities NOT from the cache —
    parsed directly (AC-1's own subject style), reconstructed, or handed across a consumer boundary.
    (c) The five body-writers and `update_fields` REFUSE on an unresolvable name — `ValueError` on a
    `None` path (`person.py:1404-1405`, `:1523`, `base.py:440-441`) — so their failure mode under
    `auto_load=False` is an exception, not a silent fork. The silent-fallback arm was `save`'s
    alone. What they share with `save` is the other half: on a live 2-note collision the name
    resolves to whichever note won the glob, so a timeline entry for A can land in B.

14. **The gate's refusal is NOT `validate_strict`'s refusal — one of the ten Tier-1 branches is
    exempt at the door, and it is a MEASURED live shape.** Predicate, executed 2026-09-21: read of
    `Tier1Branch` and the whole `TIER1_BRANCHES` tuple, of `gate_write`'s person arm, and of
    `validate_strict`.
    - `Tier1Branch` declares a `sentinel_exempt: bool` field, documented as *"the one branch the
      WI-083 phone-sentinel exemption suppresses"* (`name_validation.py:155-156`). Walking all ten
      records, exactly ONE sets it `True`: `pure_digit` (`:283-294`, `pattern="pure_digit_name"`).
      The other nine — `email_chars`, `rfc2822_leak`, `arrow_connective`, `calendar_prefix`,
      `me_to_prefix`, `path_hostile`, `archive_prefix`, `unknown_contact`, `empty` — set it `False`.
    - **The door DERIVES the exemption from the payload; it is not opt-in at the call site.**
      `gate_write`'s person arm computes
      `allow_phone_sentinel = bool(introduced.get("phones")) and name_text.strip().lstrip("+").isdigit()`
      (`name_gate.py:355-358`) and hands it to `validate_strict` (`:361-363`), which returns the name
      untouched on the first line of its body (`name_validation.py:607-609`).
    - **`validate_strict` alone answers the opposite.** Its own default is
      `allow_phone_sentinel: bool = False` (`:594`), documented *"Off by default to keep producers
      honest"* (`:599-601`). So `NameValidator().validate_strict(stored_name)` REFUSES a phone-only
      stub that the write door WRITES.
    - **The corpus documents the exemption it was built to avoid.** `@+447700900123.md` declares NO
      `phones` precisely so the branch fires, and its comment says so verbatim, citing
      `name_gate.py:355-358` (`tests/fixture_vault.py:283-293`). Its stem and stored name are the
      same digit string, so it is NOT in premise 13's divergent set — the two populations are
      independent, which is why round 3 could measure one correctly and still mis-rule the other.
    - **The shape is live and measured, not absent.** `pure_digit`: `count: 2`, `status: MEASURED`,
      both members `+<11-12 digits>` (`docs/vault-shape-census.md:148-157`, `:260-261`). Whether
      either of the two is ALSO among the eight divergent is precisely what precondition 1 exists to
      answer and what no caged reader can settle.
    - **And such a note is renameable.** `_PATH_HOSTILE_RE` is `/` and nothing else
      (`name_validation.py:107`); `@+447700900123.md` is an ordinary filename. `create_stub` mints
      exactly this shape, deriving the same sentinel flag from `phone` (`person.py:1270-1272`).

    Consequence: a rule that asks `validate_strict` mislabels a whole branch in the REFUSING
    direction — predicting a refusal where the package writes, and forbidding a rename that is both
    executable and correct.

15. **Book's and Meeting's filename rules are `@{name}.md` with different fields — and the
    call-and-discard escape is reachable at both, while the machinery that refuses it is already in
    the tree.** Predicate, executed 2026-09-21: read of `BookRepository.save` and its `_get_file_name`
    (`book.py:144-184`, `:340-355`), of `MeetingRepository.save` and its `_get_file_name`
    (`meeting.py:166-206`, `:208-231`), and of `tests/derivations.py`'s `_taints_a_write`
    (`:361-409`).
    - **Both overrides are the same two lines.** `filename = self._get_file_name(entity)` then
      `file_path = self.vault_path / filename` (`book.py:167-168`, `meeting.py:189-190`), then
      `write_markdown_file(file_path, entity=entity, …)` (`:170-178`, `:192-200`), then `_adopt` and
      return. Neither calls `super().save()`, confirming premise 12's narrowing from the other side.
    - **The rules themselves.** Book derives `f"{title} - {author}.md"`, or `f"{title}.md"` when
      `author` is empty, each half stripped of the character class `[<>:"/\|?*]` (`book.py:346-355`).
      Meeting derives `f"Meeting {date} - {title}.md"` where `date` is `entity.date` with hyphens
      removed (or the literal `unknown`) and `title` is `topics[0]`, else `"with "` plus the first two
      attendees, else `meeting_id`, else `"Untitled"` — cleaned by the same character class and
      truncated to 50 (`meeting.py:216-231`).
    - **So the derivation is recomputed from the entity's CURRENT fields against a file it may no
      longer name.** That is structurally `@{name}.md` with a different field set, which is why
      divergence is a TYPE-GENERAL class and not a Person one, and why a Book or Meeting subject whose
      deriving fields still agree with its file cannot discriminate a provenance-bound write from a
      derivation-bound one: for such a subject the two mechanisms compute the same path.
    - **The escape is reachable, and the counter-shape is shipped.** A `self._resolve_write_target(entity)`
      whose return is discarded — a bare expression statement, or bound to a name the write never
      reads — satisfies a call-presence rule and changes nothing about where the bytes land.
      `tests/derivations.py:361-409` is the shape that refuses it, already in the tree and already
      load-bearing for a shipped AC: it SEEDS a taint on the name bound to a call's return, propagates
      to a fixpoint over assignments (`:389-401`), and sinks at a write call's arguments (`:404-408`).
      A bare expression statement binds no target and seeds nothing; `_ = self._resolve_write_target(entity)`
      seeds `_`, which reaches no write.
    - **And the legitimate shape survives it.** `file_path = self._resolve_write_target(entity)`
      followed by a fallback arm REBINDING the same name keeps `file_path` tainted, because the taint
      set is monotone over names — so a data-flow rule does not force the builder to drop the fallback
      asymmetry round 3 argued for. This is the property that makes the AC-5 fold below cheap rather
      than a redesign.

**Exempt from execution, and the reason is RELIANCE rather than readability** (gate spawns arm no OS
read sandbox, so these are one call away — but an answer read there has no HEAD to pin a re-run to):
the live vault's own numbers (the census's 8, today's `.conflicts`, the per-note repair direction,
the incoming-reference counts) and the three consumer repositories' call sites. Both are declared as
`kind: precondition` fences in `## Write Targets` rather than asserted here.

### Constraints discovered

- **The corpus cannot be the invariant's subject in the obvious way.** An assertion of the form "no
  note in this corpus has stem ≠ name" is RED against `tests/fixtures/vault/` by construction
  (premise 7) and would put pressure on a digest-frozen corpus to be "cleaned" — destroying the very
  specimens WI-016 froze. The hermetic floor's corpus is a museum of corruption shapes, not a clean
  vault.
- **The live vault cannot be the invariant's subject either.** WI-031 (shipped today) closed the
  third live-vault route out of the test suite precisely so no floor run can reach
  `OBSIDIAN_VAULT_PATH`. A pytest assertion over Dave's vault is forbidden, non-hermetic, and
  unrunnable in the cage.
- **Renaming is not a free act — and the chosen disposition is ACCEPT THE NOISE KNOWINGLY.**
  Premise 8: the moment a stem moves, every incoming `[[@Old Stem]]`, every `attendees: [Old Stem]`
  and every `company:` value naming it becomes a linter WARNING. The alias preserves *library*
  reachability (`_alias_index`, `person.py:272-275`) and *Obsidian* reachability; it does not make
  this project's own linter quiet. Three dispositions were on the table — rewrite the incoming
  references during the repair, teach `check_links` to resolve through `aliases`, or accept the
  noise — and the first draft named all three and chose none, which would have left the repair run
  buildable two ways (WI-144). **Chosen: accept it, and measure it.** Rationale, in order: (i) with
  premise 8 corrected, the noise is warnings only — no auto-repair can act on it, so the failure
  mode is a longer report and never a wrong edit; (ii) rewriting incoming references would make the
  repair a second mutating authority over notes this item never typed, across meeting and company
  notes, which is approach D's objection wearing a different hat; (iii) teaching the linter aliases
  is a change to a shipped resolver with its own both-ways pinning obligation, it improves
  `check_links` for reasons unrelated to divergence, and it belongs to `lint_vault`'s own backlog,
  not to a repair item — if the measured count makes it worth doing, it is a separate work item and
  this item's precondition (c) is exactly the evidence that would justify minting it. The
  consequence is stated rather than discovered: after the repair run, and permanently after AC-2(c),
  `lint_vault --report` carries a bounded population of stem-resolution warnings for renamed notes.
  Precondition (c) exists to say how large that population is before Dave signs, not after.

- **The collision shape is LIVE, not hypothetical.** The census rules `same_name_collision` ABSENT
  only in its ≥3 sense — "largest live collision: 2" (`docs/vault-shape-census.md:222`, `:266-271`).
  So among the eight divergences there are live pairs of notes sharing one stored `name:`. Any
  mechanism that resolves a write target from a name cannot serve both members of such a pair, and
  any criterion asserting "the write lands in the note it was loaded from" is false for one of them.
  This is the constraint that decided the seam.
- **Per-note repair direction is a judgement, not a rule.** The census's own prose names eight live
  shapes including "a book-titled file holding a person note" and "a first-name-only stem"
  (`docs/vault-shape-census.md:262-265`). For some the stem is right and the field is wrong; for
  others the reverse; and where the canonical `@{name}.md` is ALREADY TAKEN the repair is a merge,
  not a rename. No criterion may promise "renamed to match `name:`" for all eight until that table
  exists.
- **A THIRD repair direction exists, and the corpus is what proved it: the stored name can itself be
  one the package refuses to write.** Premise 13(b): two of the corpus's four divergent notes carry a
  stored `name:` the door refuses. For such a note the repair is to fix the FIELD (or merge), never
  to move the file — but the REASON is a policy and not a physical impossibility, and round 4's
  non-blocking note is right that stating it as impossibility over-generalizes from one branch.
  Literal unexecutability is true of `path_hostile` ALONE: `@{name}.md` for a name containing `/`
  names a file in a DIFFERENT DIRECTORY (`_PATH_HOSTILE_RE` is `/` and nothing else,
  `name_validation.py:107`, `:249-259`). `@Perrowin -> Tessamund Drostane.md` is a perfectly legal
  filename, and so would an `archive_prefix` or `unknown_contact` stem be; what is refused there is
  the `save()`, not the move. **The policy, with its reason: we do not mint a filename from a name
  the package refuses to write.** A stem minted from a refused name is a stem the library can never
  reproduce — the note's own `save()` raises above the lock (`writer.py:229-233`, `:252-253`), so the
  vault would carry a canonical filename no write path in the package could ever have created, and
  the next repair pass would read it back as authority. Fix the field, and the stem follows from a
  name the door accepts. The census's live population is where this matters most: "a book-titled file
  holding a person note" is precisely the shape whose stored name is arbitrary text. This is why
  precondition 1's direction table gains a third column below, and why it is added BEFORE the
  baseline is commissioned rather than after it comes back with rows nobody can execute.
- **"A name the gate refuses can never fork" is TRUE — but only of the refusal the DOOR performs, and
  that is not what `validate_strict` answers.** The property itself holds and is worth pinning: where
  the door refuses, `save()` raises before a byte is written (`writer.py:252-253`, above `note_lock`
  at `:258`), so that cell of the sweep has a true, stable, declared outcome — `NameGateRefusal`
  carrying the branch's `pattern` — and asserting it beats hand-listing notes out, because the rule
  stays total: a future corpus member trips into the right expectation by itself. What round 3 got
  wrong was the PREDICATE, not the property. It spelled the question as
  `NameValidator.validate_strict(stored_name)` in four places, and premise 14 is why that is a
  different question: `pure_digit` is `sentinel_exempt`, `gate_write` derives `allow_phone_sentinel`
  from the note's own payload, and `validate_strict`'s default is `False` to keep producers honest.
  A divergent phone-only stub declaring `phones` — 2 live members of that branch, census
  `docs/vault-shape-census.md:148-157` — is therefore WRITTEN by the door, is renameable, and would
  have been predicted refused and forbidden a rename. **The rule is restated as the DOOR PREDICATE,
  defined once in "Which notes ARE the class" and inherited by AC-1, AC-3, AC-4 and precondition 1
  rather than re-spelled in each** — one clause in one place is also what stops the next drift, since
  four spellings of one question is how this one survived three rounds.
- **`overwrite=True` is `save`'s default.** For a divergent note whose canonical filename already
  exists (the Quillam shape), today's `save` does not fork — it writes over the OTHER note. Two
  distinct corruptions from one defect, which is why the acceptance oracle below is per-member
  rather than uniform.
- **A pre-existing key asymmetry, deliberately NOT made load-bearing.** `_get_cache_key` lowercases
  without stripping (`base.py:319-321`) while `get` and `get_file_path` look up
  `name.lower().strip()` (`:342`, `:365`). Under the rejected C′ the whole anti-fork guarantee would
  have rested on that lookup agreeing with that key; under C nothing in the write path consults
  either. Recorded so the spec neither depends on it nor "fixes" it inside this item: it is a
  resolution-core question in the WI-125/WI-023 neighbourhood, and YAML strips plain scalars, so it
  is low-severity today and stays out of scope.

- **Write authority** covers `obsidian_schemas/**`, `tests/**`, `scripts/**`, `docs/**`
  (`pipeline-runners.yaml:34-38`). Consumer repositories are structurally out of reach; a contract
  change here lands on them without this item being able to fix them.

### Where the invariant can actually live — the mint's mechanism, re-derived

"An invariant test over the corpus goes red the moment the class recurs" cannot be one test, because
the two corpora it could mean are both unavailable (constraints 1 and 2). It decomposes cleanly into
three, and the decomposition is the main product of this exploration:

1. **The write-path property** — hermetic, in the floor, over a materialized temp copy of the frozen
   corpus plus planted members: *no library write can turn one person note into two, or land one
   person's bytes in another person's file.* This is the half that makes recurrence impossible
   rather than merely visible — and after round 2 it comes in two pieces, the property asserted over
   the write paths that exist (AC-1) and a derived containment wall proving there are no others
   (AC-5), because the property was drafted once already as true of one path out of nine.
2. **The read-side detector** — a `lint_vault` check that names every diverged note, pinned both
   ways against the fixture corpus (which supplies FOUR true positives for free — premise 13, two of
   them notes the DOOR PREDICATE refuses, plus one planted member the corpus cannot supply). This is the half
   that is RED "the moment the class recurs" in the live vault, on the tool Dave already runs.
3. **The bracket** — an entry/exit measurement in a committed artifact, the WI-026 precedent
   (`docs/lint-vault-live-baseline.md`). The exit half is a ship condition, not a criterion: a
   `kind: precondition` fence is HEAD-probed before the build spawn and so cannot carry a post-build
   act, and a `kind: command` AC would point an automated battery at Dave's vault.

### Where the structure lives (the WI-185 question) — asked twice, answered properly the second time

*The draft repair reconstructs at repair time what production discards at write time.* `save` is
handed an entity that the repository loaded from a known file, and it re-derives a filename from the
name field instead. So the item's first task is the SEAM, not the sweep: **the path a write lands on
must come from the note the entity came from.**

The first draft of this exploration wrote that sentence and then implemented a weaker one. It bound
`save` to `get_file_path(entity.name)` — a *read-time reconstruction* from a field that is neither
unique nor always indexed (premise 2) — which is the very shape this question exists to catch. The
architect's round named it, and re-reading premise 2 confirms it three ways:

- **It is not provenance, it is glob order.** `_file_map` holds one path per lowercased name, filled
  last-wins over `vault_path.glob` (`base.py:241-248`). For the live 2-note collisions, the map can
  answer "which note won the walk" and can never answer "which note did this entity come from".
  Binding `save` to it would write one person's bytes into another person's note — trading a fork
  for a cross-write, which is the same corruption from the other side.
- **It is inert exactly where the fork is loudest.** With `auto_load=False` and no explicit `load()`,
  `_ensure_loaded` returns without doing anything (`base.py:210-213`), `get_file_path` returns
  `None`, and `save` falls through to `@{name}.md` — forking precisely as today, silently, for a
  whole repository configuration. A battery that must load the corpus to find its subjects cannot
  see this arm at all.
- **It makes `save` a read-then-write.** On a fresh repository the lookup triggers a full vault walk
  where today's `save` triggers none — a cost paid by every consumer, on every hot path, to answer a
  question the caller already knew.

**The answer: stamp provenance at the parse boundary and let `save` read it off the entity.**
Premise 10 is the whole argument — the binding already exists. `parse_markdown_file` constructs a
`ParsedDocument` carrying `file_path` (`parser.py:54`, `:246-252`) and all three `_load_file`
implementations discard it one line later (`base.py:311-314`, `book.py:79`, `meeting.py:83`). The
structure this needs is not missing and does not need reconstructing; it is built, held for three
lines, and dropped. Keeping it is one edit at one site, and it is the site where the path is a FACT
rather than a lookup — LESSONS #1, at the parse, where the project's own convention puts it.

What that buys, point for point against the three failures above: the stamp is per-ENTITY, so both
members of a name collision write back to themselves; it travels with the entity rather than with
the repository's index, so `auto_load=False` is no longer a special case and needs no fallback; and
`save` reads an attribute instead of walking a vault, so the hot path is untouched. It also composes
with the rename door — the door re-stamps the entity it moves, so a `save()` after a rename lands in
the new file instead of recreating the old stem.

Three consequences that must be specified rather than discovered, all of them cheap:

1. **The stamp is a declared private attribute, never an ordinary one.** Premise 11: `extra="allow"`
   on `BaseEntity` means a bare assignment would be serialized into every note the library writes.
   A `PrivateAttr` is invisible to `entity_to_frontmatter` by construction — and that
   unwritability is assertable, so it is asserted rather than trusted.
2. **A stamp from another vault is not honoured.** `save` uses the stamp only when it points inside
   this repository's own `vault_path`; otherwise it is treated as absent. A repository must not be
   steerable into writing outside its vault by an entity it was handed.
3. **Provenance can be LOST, and the loss must be visible.** An entity round-tripped through
   `model_dump()`/`model_validate()` arrives with no stamp and is then indistinguishable from a
   genuinely new entity — both get `@{name}.md`, today's behaviour. That is the honest limit of the
   mechanism and it is declared, not papered over (AC-1(f)). What is NOT acceptable is the loss
   being silent: when `save` creates at `@{name}.md` for an entity carrying no provenance and that
   file already exists, it logs a WARNING naming the collision. Behaviour is unchanged — this is a
   readout, not a refusal (approach E's ordering problem stands) — but the class becomes
   reconstructable from a consumer's logs instead of being discovered as a corrupted note months
   later.

Repairing the eight notes without closing this seam is buying a clean vault that starts re-dirtying
on the next consumer `save()`.

WI-021 reached the edge of this and stopped deliberately. Its audit table already records the two
facts verbatim ("the FILENAME is bound from the RAW `entity.name`" / "`save` never renames and never
unlinks" — `docs/write-door-bypasses.md:452-453`, both marked *confirmed*), and its option (a′) —
write the repaired name back onto the entity before the path binds — was REJECTED with the reason
that matters here: *"the first re-save writes a NEW file at the cleaned stem and leaves the old one —
`save` has no `unlink`. One orphan per note, on the fix's own first run"* (`:486`). That is this
item's defect, named by its predecessor and parked. Anything that changes what filename a write
derives, without giving the library a way to MOVE a note, reproduces it.

### One target function, not one read site (the round-2 decision)

Round 1's fold put the stamp in the right place and then read it in one. The blast-radius bullet
below used to say the stamp is *"read at one site (`base.py`'s `save`)"* — accurate about the fold,
false about the package, and that sentence is exactly what made the gap invisible. Premise 12 counts
the real population: **nine name-bound write paths, and the fold reached one.** Two of those nine
matter beyond bookkeeping:

- **AC-1's headline was false as written.** "No library write can turn one person note into two or
  land one person's bytes in another person's note" was asserted while its oracle exercised `save()`
  alone. A build could go green on every arm and ship a criterion whose headline is untrue — the
  item buildable two ways (WI-144), in the one criterion that carries the Intent.
- **The item's own repair machinery was driven from the lookup it exists to retire.** AC-2(c) has
  `update_fields` call the new rename door on a name change; `update_fields` picks its file from
  `_file_map[name.lower().strip()]` (`base.py:438`), one path per name, glob order. For an entity
  parsed from note A whose `name:` is shared with note B — a live shape, census
  `docs/vault-shape-census.md:266-267` — the door moves **note B**, appends A's old stem to B's
  `aliases`, and leaves A untouched. The correct path is sitting unread on the entity one frame
  away. The same defect one severity down is a timeline entry for A landing in B — precisely the
  harm premise 9 describes and the harm "Examples of done" promises to end.

**Chosen: (i), one resolution function; the promise is widened rather than narrowed.** The stamp
already exists on the entity at every one of those nine sites, so routing them all through one
private `_resolve_write_target(entity)` on `BaseRepository` is eight more one-line edits, not a
second mechanism. The alternative — declaring the seam `save`-only and restating AC-1's headline to
match — is cheaper to write and buys a boundary you can route around, which LESSONS #1 says was
never a boundary. It would also leave the rename door itself standing on the glob-order lookup,
which is not a residue anyone would accept once it is written down.

The function is deliberately thin, and the reason is a real asymmetry in what its callers do with a
miss: **`_resolve_write_target(entity)` returns the provenance stamp when it is present AND resolves
inside this repository's own `vault_path`, and `None` otherwise. It never falls back.** Each caller
applies its OWN documented fallback to `None`, because the correct fallback differs and collapsing
them would ship a new defect:

- `save` — and Book's and Meeting's overrides — falls back to CREATING at the name-derived filename
  (`@{name}.md`, or `_get_file_name(entity)` for the two overrides). That is today's behaviour for
  an entity with no provenance and it has to stay, or nothing can create a note.
- `update_fields` and the five body-writers fall back to `get_file_path(name)` and keep their
  existing REFUSAL when that is `None` (`ValueError`, premise 12(c)). A uniform fallback returning a
  name-derived path here would convert those refusals into note CREATION — turning a loud miss into
  a brand-new fork source, inside the item whose whole purpose is to close one.

Existence is deliberately not part of the resolution: the stamp is a path, not a promise the file is
still there. `save` creates at it (recreating a note deleted out from under the entity, which is
what the name path does today too), and `update_fields` and the body-writers keep their own
`.exists()` refusal one line later.

What the function buys is that the name-derived arm becomes unreachable for exactly the population
that has a right answer. Every entity the library parsed carries a stamp (premise 10), and that is
the whole population the collision hazard applies to (premise 12(b)); the residual name-keyed arm
serves only entities with no provenance, where there is nothing better to consult, and on the
mutating paths it refuses rather than guesses. Book and Meeting stop being a hole in the seam for
one line each — and a book-titled file holding a person note, one of the census's eight shapes and
one of this item's booked hand repairs, is exactly the sort of entity whose write path would
otherwise have been the unstamped one.

A function every caller *may* use is a polite request, so the seam ships with the wall WI-031 built
for `lint_vault`: a derived scan asserting that every mutation site under `obsidian_schemas/**`
either takes its path as a parameter (`writer.py`'s path-taking leaves, handed a path by their
caller) or routes through `_resolve_write_target` in its own body. That is AC-5, and it is what makes
a tenth write path join the seam automatically instead of quietly reopening this finding.

**Call-presence is not routing (the red-team's finding, and the reason this wall is data-flow).** The
first draft of that scan asked whether the function CALLS `_resolve_write_target` before it writes.
That is a structural question and it certifies the wrong thing: a `save` override can call the
function, discard the return, and write to its own `_get_file_name`-derived path — one line, green
wall, nothing routed. The escape is loudest at exactly the two sites the seam was widened for, since
Book's and Meeting's overrides already hold a complete name-derived write two lines long
(premise 15), so "call it and ignore it" is a smaller edit there than doing the work. The question
the wall has to ask is whether the RESOLVED VALUE reaches the write: the name bound to
`_resolve_write_target`'s return must taint the path argument of that function's own write call. That
is not new machinery — `tests/derivations.py:361-409` already implements seed → fixpoint → sink for a
different seed, and the fold is a second seed, not a second scanner. It is also not over-tight: the
taint set is monotone over names, so the documented fallback arms (which rebind the same local) stay
legal, which is the property that lets the asymmetry above survive the wall.

### Which notes ARE the class (the round-3 decision)

Two rounds settled the mechanism and neither asked the corpus what the defect class actually
contains. Premise 13 asked it. The class is defined here, once, and both criteria that quantify over
it are restated to this definition rather than to each other.

**The class, stated.** A person note is DIVERGENT when its filename stem, less the leading `@`,
differs from its stored `name:` — compared RAW on both sides. No `clean_person_name` on either half,
and the corpus contains the discriminator that makes that choice observable rather than stylistic:
`@Dave  Marrowyn Fennwick.md` carries the same double space in its stem and in its stored name
(`tests/fixture_vault.py:246-254`), so raw-vs-raw calls it CLEAN while a cleaned comparison calls it
divergent (the manifest declares `cleaned="Dave Marrowyn Fennwick"`). Raw is correct: this item's
subject is whether a write lands where it was read from, and the filesystem does not run a cleaner.
A note whose name is merely DIRTY is WI-021's business, not this item's; a note whose name and file
disagree is this item's. The cleaner is one import away and a builder may reasonably reach for it, so
the choice is written into AC-3's own text rather than left to the spec.

**Two derivations, not one — and the second is what AC-1 was already using without defining.**
- *Divergent set* — the predicate above, over the manifest. Four members (premise 13).
- *Name-sharing groups* — every person note whose stored `name:` equals another person note's. One
  group in the corpus: the three `Quillam` notes, two of them divergent and the third
  (`@Quillam Ostrivane Lumbrek.md`) AGREEING with its stem. AC-1's (b) and (c) were asserting over
  "every member of a name-sharing group" while the criterion derived only the divergent set — which
  is how the collision third ended up named in a rationale that the predicate cannot reach. The
  group derivation is stated as its own predicate and AC-1's subject set is the UNION, so the
  collision third is a full subject: five corpus subjects, not two, not three.

**THE DOOR PREDICATE — stated ONCE here, inherited everywhere else (the round-4 decision).** Four
places in this document need to answer one question — *would the package refuse to write this note's
stored name?* AC-1's gate-refused `save` cell, AC-3(c)'s marker, AC-4's table-consistency rule and
precondition 1's column (b3). Round 3 spelled that question four times and spelled it
`NameValidator.validate_strict(stored_name)`, which is a DIFFERENT question (premise 14). It is
stated once, here, and the four sites cite this paragraph:

> A person note is **GATE-REFUSED** when `gate_write(fm, declared_type=fm.get("type"),
> whole_record=True)` raises `NameGateRefusal` for that note's OWN stored frontmatter `fm` — the
> exact call `write_markdown_file` makes on its `entity is not None` arm (`writer.py:229-233`,
> `:252-253`), with the note's whole record as the payload. The expected value is the raised
> `pattern` — the branch's `pattern` field, never its `branch_id`, which three branches share
> (`name_validation.py:152-154`). It is NOT `NameValidator.validate_strict(name)`: that call's
> `allow_phone_sentinel` defaults to `False` (`:594`, `:599-601`) while the door DERIVES it from the
> payload (`name_gate.py:355-358`), so the two disagree on the one `sentinel_exempt` branch
> (`pure_digit`, `:283-294`) — and that branch is MEASURED at 2 live person notes, not absent.

Three things follow, and they are the reason the predicate is worth naming rather than inlining.
(i) **It is total by construction.** The payload it judges is the note's own record, so any future
member — a new Tier-1 branch, a new exemption, a record whose `phones` decide the answer — is judged
by the same code the write path runs, and no reader has to re-derive the exemption table. (ii) **A
divergent phone-only stub is NOT gate-refused**: it declares `phones`, the door writes it, and
`@+447700900123.md` is an ordinary filename — so its correct repair direction is *rename*, and any
rule that forbids that is forbidding the one thing that works. (iii) **Over today's corpus the
predicate selects exactly the two premise-13 specimens** — the arrow (`calendar_prefix`) and the
slash (`path_hostile_char`) — and no others, because the third and fourth divergent notes are clean
and the corpus's phone specimen declares no `phones` (`tests/fixture_vault.py:283-293`) but is not
divergent either way.

**The gate-refused cell, by RULE and not by hand-list.** For every (subject, `save`) cell the sweep
first applies the door predicate to the subject. If it refuses, the expected outcome of that cell IS
`NameGateRefusal` carrying that `pattern`, with no file in the vault changed; otherwise it is the
ordinary (a)(b)(c) assert. This asserts a true property rather than excusing two notes, and it keeps
both the manifest's `discriminator` label and the bare validator out of the definition. The other
eight paths are unaffected for those subjects and assert normally (premise 13(c)).

**And the corpus cannot tell the two rules apart, so the discriminating member is PLANTED (WI-286).**
Every divergent note the frozen corpus supplies is clean-or-refused under BOTH spellings — the
sentinel-exempt branch has no divergent representative there — so a build that implements the rule as
`validate_strict` passes every corpus cell. The member that discriminates is a DIVERGENT phone-only
stub: a file `@447700900123.md` carrying `name: "+447700900123"` and a `phones:` list (stem ≠ name
raw, `sentinel_exempt` branch, `phones` declared). Under the door predicate its `save` cell asserts
the ordinary (a)(b)(c); under `validate_strict` it predicts a `NameGateRefusal` that never comes.
That one planted note is the whole difference between the two implementations, and it is why AC-1's
subject set names it explicitly rather than trusting the corpus to supply it.

**Why the label cannot be the class, restated as the thing it decides.** AC-3 as drafted pinned "one
ERROR for each of the two notes the manifest declares in that class" — and a detector written to the
DEFINITION emits four. The only implementation that passed both of AC-3's arms as written was one
keyed on `shape_classes`, i.e. one where the manifest LABEL is the defect class. That is the
implementation AC-1's own rationale forbids, and it would be the shipped detector over the live
vault, where there are no labels at all. AC-3's counts are restated to four below. The two criteria
now read the same definition, which is the WI-144 condition: the item is buildable one way.

**The detector reports a gate-refused diverged note, loudly.** It is the shape the repair most needs
to see — divergent AND not repairable by moving the file — so suppressing it would hide the rows that
most need a human. The ERROR therefore carries a declared marker naming the refusal `pattern`, and
the marker fires on the DOOR predicate above, so a divergent phone-only stub is reported as an
ordinary divergence with NO marker and stays free to be repaired by rename. What the marked message
says is the policy, not a physical claim: *this divergence is not repaired by renaming the file to
the stored name — repair the field* (for `path_hostile` it is additionally impossible, since the
target is a path into another directory, and the message may say so per-pattern). That is AC-3's new
arm, and AC-4's shape check is what stops a direction table coming back with a `rename` in a marked
row — while leaving `rename` legitimate for every unmarked one.

### Divergence is not a Person-only predicate (the red-team round-1 decision)

Round 3 defined the class over the corpus and defined it correctly — for Person. Every subsequent
sentence then treated "the divergence predicate" as `@{name}.md`, and Book and Meeting entered AC-1
as bare subjects with no predicate of their own. The red-team's finding is what falls out of that:
their subjects were not required to DIVERGE, so their cells could not tell a provenance-bound write
from today's derivation-bound one, and the two sites round 2 widened the seam to reach were the two
the criteria could not observe.

**The class, stated type-generally.** A note is DIVERGENT when the filename its OWN TYPE'S write rule
recomputes from the entity's current fields differs from the file the entity was parsed from. The
Person predicate is the instance, not the definition:

| type | the rule, read from the code | the divergence predicate |
|---|---|---|
| Person | `@{name}.md` (`base.py:391-393`) | raw stem ≠ raw stored `name:` — premise 13, four corpus members |
| Book | `{title} - {author}.md`, or `{title}.md` with no author, class `[<>:"/\|?*]` stripped (`book.py:346-355`) | that string ≠ the file it was parsed from |
| Meeting | `Meeting {YYYYMMDD} - {title}.md`, title from `topics[0]` / first two attendees / `meeting_id` / `Untitled`, same class stripped, truncated 50 (`meeting.py:216-231`) | that string ≠ the file it was parsed from |

Nothing about premise 13 changes; it is re-read as the Person ROW of this table rather than as the
whole table. What changes is that "plant a divergent Book and a divergent Meeting" stops being an
extra fixture request and becomes the same derivation applied to the two types whose rule is not
`@{name}.md`.

**The COLLIDING group, generalized the same way.** A name-sharing group is every person note whose
`@{name}.md` agrees with another's — which is, in the general form, every note of a type whose
DERIVED filename agrees with another note's of that type while they live at different files. Two
facts make this the right generalization rather than a neat one. First, it is exactly the corpus's
`Quillam` shape: three notes, one derived filename, one of them living AT it and two elsewhere.
Second, it is self-seeding — a group of two or more notes with one derived filename contains AT MOST
one non-divergent member (the one that lives at that filename), so **a colliding group always
contains a divergent member.** One plant per type therefore supplies both of AC-1's derivations at
once.

**What is planted, and why it is a WI-286 plant rather than coverage.** For Book and for Meeting, a
group of TWO notes in the materialized temp vault whose derived filenames are identical: one living
AT that derived filename (non-divergent — the collision-third analogue) and one living elsewhere
(divergent). The frozen corpus cannot supply this and must not be asked to (`CORPUS_DIGEST`), and
without it the discriminating cell does not exist: for a Book subject whose `title`/`author` still
agree with its file, `_get_file_name(entity)` and the provenance stamp compute the SAME path, so a
correct seam and a "call it and discard the return" stub are indistinguishable (premise 15). With it,
the divergent member's write lands either in the file it was parsed from (seam) or on top of its
sibling at the derived filename (today's code, and the stub) — and those two outcomes differ in the
bytes of a note the caller never named. That sibling clobber is not a contrived shape: it is the
Book-side spelling of the same corruption premise 9 describes for Person, and the census's
"a book-titled file holding a person note" is a live specimen of a Book-shaped file whose derived
name has drifted from where it lives.

**One constraint on the mutation, so the arm measures what it says.** The mutation applied to a
Book or Meeting subject must touch NONE of the fields that type's filename rule reads — not
`title`/`author` for Book, not `date`/`topics`/`attendees`/`meeting_id` for Meeting. Otherwise the
derived filename moves with the mutation and the cell tests mutation-versus-derivation instead of
provenance-versus-derivation. (For Person the same constraint is already stated as "minimal non-name
mutation"; this is that rule read off each type's own row of the table above.)

**And the criterion's shape is not enough on its own** — AC-1 proves the nine paths behave on the
population where the two mechanisms differ, but a tenth path, or a re-written override, can still
call the seam and ignore it. That is a data-flow property and it belongs to the wall, not to the
sweep; it is folded into AC-5 below.

### Approaches considered

**A — Repair the notes by hand, add the detector, stop there.** Solves the live count today; the
seam still forks (premise 1), so the next consumer `save()` on any surviving or future divergence
re-opens the class. Fails the Intent's "this is the last time it is repaired by hand" outright.
*Rejected.*

**B — `save` renames the note to match the name (auto-converge).** Every write becomes a potential
file move; a caller updating a phone number silently relocates a note and breaks its incoming links;
`save` grows the two-lock door; and it is WI-021's rejected (a′) with an `unlink` bolted on. A
rename is a decision, and `save` is not where decisions are made. *Rejected.*

**C — every write in the package targets the note the entity came from, bound by PROVENANCE through
ONE resolution function; a separate, explicit door is the only thing that moves a file.** The parse
stamps each loaded entity with the file it was parsed from (premise 10, a private attribute per
premise 11); `_resolve_write_target(entity)` returns that stamp when it points inside this vault and
`None` otherwise, and all nine name-bound write paths (premise 12) consult it before deriving
anything from a name — `save` still creating `@{name}.md` when it is absent, `update_fields` and the
body-writers still refusing. Divergence
then persists harmlessly until someone decides to fix it, and nothing forks or clobbers. The rename
door (`vault_io.move_note` + old stem into `aliases` + index fixup + re-stamp) is called by the
repair run and by `update_fields` on a name change (premise 3), which is what makes "stem and name
agree, and stay that way" true rather than aspirational. *CHOSEN.*

**C′ — the same shape, but `save` binds from `get_file_path(entity.name)`.** This was the first
draft's choice and it is recorded here as a dead end rather than quietly replaced, because it is the
tempting version: it needs no new attribute, reuses `update_fields`'s own lookup, and reads as the
minimal change. It fails for reasons that are structural, not incidental — `_file_map` is name-keyed
and one-path-per-name so it cross-writes on the live collision pairs; it is empty under
`auto_load=False` so the seam is silently inert there; and it turns every `save` on a fresh
repository into a full vault walk. See "Where the structure lives" for the argument in full.
*Rejected — and the rejection is the reason the seam is specified at the parse boundary, so a later
reader who re-derives C′ as "simpler" can find out here why it is not.*

**D — Teach `lint_vault --fix` to rename.** Relocation is the highest-blast-radius act in the tool
(`docs/default-vault-path.md:83`), WI-026's four-bucket accounting exists precisely to bound `--fix`,
and per-note direction is a judgement no auto-fix can make (constraint 4). The detector is reported
and never repaired. *Rejected — and this rejection is an acceptance criterion, not a note.*

**E — Refuse the write: `save` raises when the mapped note's stem diverges.** Loud, cheap, and
correct in the abstract; but it turns every consumer write against any of the eight live notes into
an exception before the repair has run, in three repositories this item cannot patch. The refusal
direction is right, the ordering is unshippable. *Rejected in favour of C, which is silently correct
rather than loudly broken.*

**F — Key the cache and `_file_map` on the path instead of the name.** Addresses the shadowing
(premise 9) but not the duplication, rewrites the resolution core WI-125/WI-023 just settled, and
the census rules `same_name_collision` a SEPARATE class from divergence
(`docs/vault-shape-census.md:266-271`). Out of budget and out of intent. *Rejected — and C is not a
back door to it: the provenance stamp lives on the ENTITY and changes no key, no index and no
lookup. `get`, `get_all`, `_file_map` and the WI-125 identifier index behave exactly as they do
today, shadowing included. C fixes where a write LANDS; the shadowing of a collision's loser is
still a read-side defect, still visible on `.conflicts`, and still repaired by the direction table's
merge rows rather than by code.*

**G — Make the gate refuse a name that disagrees with its file.** `name_gate` judges a payload and
holds no path, and WI-021 ruled its name output an identity (option (b′), `:485`). Structurally
impossible without re-opening a shipped ruling. *Rejected.*

### Dependencies and neighbours

- **WI-026 / WI-031** — the containment wall over `tests/test_lint_vault_fix_rules.py`. Any new test
  driving `lint_vault`'s mutating entry points inherits clauses (i)–(v), including *zero repository
  constructions*. The detector's battery must drive a temp vault and construct no repository in that
  module.
- **WI-016** — the frozen corpus supplies four true positives free (premise 13); planting further members
  belongs in a temp copy, not in `tests/fixtures/vault/` (constraint: `CORPUS_DIGEST`). Round 4 adds a
  NAMED plant that both AC-1 and AC-3 depend on and the corpus structurally cannot supply: a divergent
  phone-only stub (`sentinel_exempt` branch, `phones` declared), the one member that tells the door
  predicate apart from a bare `validate_strict` — WI-286's plant-the-discriminator rule, not an extra
  fixture for coverage. Round 5 adds two more of the same kind and for the same reason: a Book and a
  Meeting COLLIDING GROUP (two notes per type, one at the derived filename and one elsewhere), which
  are the only subjects under which a provenance-bound write and today's `_get_file_name`-derived
  write land in different files — the corpus holds no divergent Book or Meeting, and the `Quillam`
  group is the Person-row specimen of exactly this shape.
- **WI-022 (company stub parity)** — booked seven mangled company notes onto this item explicitly
  (`docs/company-stub-parity.md:1333-1344`, `:1917-1919`) and named the machinery. Whether they ride
  in the same repair run is a scoping question for the spec; the direction table (precondition 1)
  should cover them if they do.
- **Consumers** — HAL9000, Exocortex, orchestrator all install `-e` and all call `save()`. Approach
  C changes where a `save()` on an existing entity lands. This is a contract change with out-of-repo
  blast radius and it needs the audit, not a guess (precondition 2; precedent
  `docs/wi-024-consumer-audit.md`).
- **The seam's blast radius inside the tree — corrected in round 2.** The stamp is WRITTEN at one
  site (`parser.py`'s `parse_markdown_file`) and DECLARED at one site (`models.py`'s `BaseEntity`,
  as a private attribute); `_load_file` in all three repositories needs no change because all three
  already route through the parser (premise 10), which is the solve-in-one-place argument for the
  parse boundary over a per-repository stamp. It is RESOLVED at one site
  (`BaseRepository._resolve_write_target`) and **CONSULTED at nine** — `save`, `update_fields`, the
  five mutating `PersonRepository` body-writers, and Book's and Meeting's `save` overrides
  (premise 12).
  Round 1's draft of this bullet said "read at one site (`base.py`'s `save`)", which was true of the
  fold and false of the package; that sentence is what hid the round-2 finding, so it is corrected
  here rather than quietly dropped. Nine one-line call-site edits, one new helper, no signature
  change on any public method. `parse_markdown_content` has no path and so stamps nothing; entities
  from that route behave as AC-1(f) describes.

- **Effort budget** — one build session for the code (seam + the nine call sites, door, detector,
  five test batteries), at the upper end of one rather than comfortably inside it after round 2's
  widening; two conductor acts outside the cage (the two preconditions, then the repair run and the
  exit attestation). No new dependency, no schema change, no public signature change.
- **Routing** — **architect**, then spec-writer: a new public repository door, a behaviour change on
  nine shipped write paths with consumer blast radius, and a new lint check across three files. The
  architect's trigger heuristics fire on all three.

### Hand repairs riding along

The mint books four extra repairs with no home: one book note carrying `type: person`, four notes
with frontmatter but no `type:`, three book notes whose frontmatter fence opened and did not parse.
Three of those classes are already DETECTED by the shipped linter — `missing_type` (`:373-381`) and
`parse_error` (`:351-359`) — and none is auto-fixable, so they are conductor edits during the repair
run, recorded in the same baseline artifact and re-counted at the exit. The book-note-typed-`person`
shape is detected by nothing today; it is one line in the direction table, not a new check.

### Conductor read-back — 2026-09-21 (both grounding artifacts landed in HEAD, read before the signature)

Per the `awaiting-precondition-commit` pause's own instruction — commit, READ what landed, correct any
criterion the bytes falsify BEFORE the signature — two corrections and three facts, all from
`docs/stem-divergence-live-baseline.md` and `docs/wi-029-consumer-audit.md`:

1. **The case-only member (baseline §2, row 3).** One of the eight divergent live notes differs from its
   stored name only by letter case. Under the vault's case-insensitive filesystem its canonical
   `@{name}.md` resolves to ITSELF, so a destination check by string says "occupied" while a check by
   file identity says "same file". As drafted, AC-4's consistency rule forbade `rename` onto ANY occupied
   destination (the row would have been RED against a correct artifact — WI-026's AC-5(b) shape) and
   AC-2(b) had the door refuse ANY existing destination by syscall (the one repair that works for that
   row). CORRECTED: AC-4's rule now reads "occupied by a DIFFERENT note", and AC-2 gains arm (h),
   CASE-ONLY — the door moves a case-variant of the note's own stem (two-step via a temporary stem;
   `NoteAlreadyExists` only when `samefile` is false). No other criterion text changed; nothing is signed.
2. **Zero live rows are gate-refused (baseline §1).** All eight are WRITTEN by the door, and neither
   pure-digit note is divergent — so AC-1's sentinel-exempt subject and AC-3(c)'s marker have their
   discriminating members ONLY in the frozen corpus and the plants, exactly as those criteria already
   say. Row 8 (a book-titled file holding a person whose canonical note exists) is the one live MERGE and
   the one true live subject of the not-renameable marker; the seven renames carry 24 wikilinks and 14
   attendee-carrying notes of blast radius, 13 + 11 of it on one row.
3. **Every consumer write is on a LOADED entity — 19 of 19 (audit §Reading 1)**, so AC-1(f)'s
   round-tripped-entity residual arm has an EMPTY consumer population, and (g)'s `auto_load=False`
   population is 0 uses across all three repos.
4. **The one consumer-visible door for rename-on-`update_fields` is HAL9000's generic entity PATCH
   (`routers/entities.py:461`, audit §Reading 2)** — an arbitrary body may carry `name` (or a book
   `title` / meeting `meeting_id`), and today that produces a fork; after this item it produces a move
   with an alias. That is a consumer-visible behaviour change and is named here for Dave's sign-off;
   every other consumer `update_fields` call fixes a name-free field set.
5. **`BookRepository.save` / `MeetingRepository.save` have zero consumer call sites** (audit §Reading 4);
   bringing them inside the seam changes no consumer today. The audit's structural findings — exocortex's
   second never-refreshed repository feeding wikilinks and graph.db, orchestrator's five out-of-library
   repair scripts and the latent 3-way-merge stale-path bug, HAL9000's legacy YAML reader — are recorded
   there for the next queue review, not folded into this item.

## Approach

Close the seam first, then repair, then keep it closed. (1) **The seam — bind EVERY write by
PROVENANCE, at the parse, through one function.** The parse boundary already knows which file an
entity came from and drops it one line later (premise 10); it keeps it instead, as a private
attribute that cannot reach frontmatter (premise 11). One private
`BaseRepository._resolve_write_target(entity)` returns that stamp when it is present and points
inside this repository's vault, and `None` otherwise — never a fallback of its own. All nine
name-bound write paths in the package call it first (premise 12): `save`, `update_fields`, the FIVE
MUTATING `PersonRepository` body-writers (`append_to_timeline`, `append_to_body_section`,
`add_to_discuss_item`, `update_to_discuss_item`, `remove_to_discuss_item`), and Book's and Meeting's
`save` overrides — five and not six, because the sixth site sharing that lookup,
`_get_body_content` (`person.py:1590`), is a READ: it returns `None` on a miss and writes nothing, so
it is the same root cause outside the write seam and is one line in the spec rather than a tenth
caller. The fallback on `None`
stays each caller's own, because it differs: `save` and the two overrides CREATE at the name-derived
filename exactly as today — logging a WARNING when that file already exists, so the one residual arm
is observable rather than silent — while `update_fields` and the body-writers fall back to
`get_file_path(name)` and keep today's `ValueError` refusal, which a uniform fallback would have
silently converted into note creation. The path is never reconstructed from the name for an entity
that has provenance, so a loaded entity's bytes land in its own note even when two notes share one
`name:` (the live collision shape), and the seam behaves identically under `auto_load=False`, where
a name-keyed lookup would have been inert. Book's and Meeting's overrides are inside this for the
same reason and on the same terms: their filename rule is `@{name}.md` with different fields
(premise 15), so divergence is a TYPE-GENERAL class — the type's own rule recomputed against a file
it may no longer name — and the two overrides are exercised on PLANTED DIVERGENT subjects, where a
provenance-bound write and today's `_get_file_name`-derived write land in different files. A derived
scan pins that no mutation site under `obsidian_schemas/**` reaches a write without going through the
function — enumerating the doors by `tests/derivations.py`'s own `DOOR_NAMES` (`:47`: `write_note`,
`create_note`, `move_note`) rather than a hand-written pair, since this item's rename door itself
writes through `move_note`, and asking a DATA-FLOW question rather than a call-presence one (the
resolved value must reach the write call's path argument, on `tests/derivations.py:361-409`'s own
seed → fixpoint → sink shape), because a function that calls the seam and discards its return is one
line and routes nothing — so a tenth path cannot reopen the gap and a ninth cannot fake its way
inside it. (2) **The door**: one explicit rename entry point on the repository, built on
`vault_io.move_note`, which resolves ITS OWN target through the same function rather than from the
name — this is what stops the repair machinery relocating the wrong member of a collision pair —
preserves the old stem as an alias, refuses an occupied destination by syscall, repairs the caches
and indexes, and re-stamps the moved entity's provenance so a later `save` follows the file rather
than recreating the old stem; `update_fields` calls it on a name change so the library stops
manufacturing divergence at all, and it is the only thing in the package that moves a note. Inside
`update_fields` that call has a stated ORDER — write the content, THEN move, THEN rebind the local
`file_path` to the door's return value before the reload — because the frame holds a `stamp` from
`read_note` (`base.py:449`), commits against the OLD path with it (`:490`) and reloads from that same
path (`:493-495`), while `move_note` calls `forget_snapshot(source)` (`vault_io.py:780`); calling the
door from inside the already-held lock is itself safe, since it sorts both resolved paths into a
global total order and the locks are reentrant (`vault_io.py:744-750`).
Incoming references to a renamed stem are knowingly left to become linter warnings — the disposition
is chosen, and precondition (c) sizes it before signature. (3) **The detector**: a read-only
`stem_name_divergence` check in `scripts/lint_vault.py`, ERROR, never auto-fixable, comparing the raw
stem against the raw stored name and pinned both ways against the frozen corpus — where the class's
real extension is FOUR notes (premise 13), two of which are GATE-REFUSED under the door predicate, so
the issue those two produce carries a marker naming the refusal `pattern` and says the divergence is
not repaired by renaming the file: divergent AND not-renameable is the shape the repair most needs to
see, not the one to suppress — while a divergent note the door would WRITE (a phone-only stub
declaring `phones`: the one `sentinel_exempt` branch, 2 live per the census) is reported UNMARKED and
stays repairable by rename. (4) **The repair**: a
conductor run outside the cage, per a committed per-note direction table, bracketed by an entry and
exit measurement of the divergence count and `len(PersonRepository(...).conflicts)` in a new
evidence artifact — the exit half being a declared ship condition on this item, on the WI-026
precedent. The invariant Dave asked for is the first three together: the write path cannot recreate
the class, and the tool he already runs goes red if anything else does.

## Design

Specced 2026-09-25 from the settled approach. Five architect rounds, two AC red-team rounds and the
data-premise audit all closed; the five signed `criteria` fences (`ac_hash 15189b874b27`) are **not
touched by this spec** — every section below is written to them. Where a gate left a non-blocking note
for the spec-writer, the fold is named inline as *(round N note M)*.

*(Revised 2026-09-25 after the first spec-review round. Its four blocking findings land here: the
detector's guard is stated as `entity_type` and never `is_at_prefixed`, with the live vault's row 8 as
the subject and a plant in Task 12 (Design §3, and §3a closes the whole WI-286 class the finding is the
third member of); `update_fields`' door call is placed explicitly OUTSIDE its `note_lock` block, with
the reentrancy argument corrected where it was unsound and the placement made structural by a new
derived scan (Design §2's ordering block and decision 5, Task 6, Task 10); the ordering block hands the
door `entity` and the undefined `updated_view` is gone; and the `## Acceptance Criteria` preamble now
states the freeze instead of contradicting it — prose only, no signed fence's bytes touched, so every
per-criterion hash stays intact. The eight non-blocking notes are folded in the same edit and each is
named where it lands.)*

*(Revised again 2026-09-25 after the SECOND spec-review round. Its two blocking findings land here.
(1) `update_fields` with a name change on an entity carrying NO provenance would have committed the new
name and then hit `rename_note`'s no-provenance raise — the one population the method's own preserved
name-keyed fallback exists to serve — so the refusal is moved BEFORE the write and the two alternative
answers are rejected in writing (Design §2, "The no-provenance name change refuses BEFORE the write";
Task 3's `resolved` binding, Task 6's clause, Task 10's arm, two `## Edge Cases` entries, a
`## Verification` failure mode and a `## Risk Analysis` row). (2) Design §3a's own class-level rule —
plant every free variable of the detector's arm the frozen corpus is unanimous about, with the list
DERIVED by reading the arm — had not been applied to the arm's `stored.strip()` conjunct, so the sweep
table gains that row and Task 12 gains plant (vi). The five non-blocking notes and the three still-open
carried-forward notes are folded in the same edit, each named where it lands: the `.md`-token rule's
fenced-code clause (Task 13), the `aliases` source-of-truth question (Design §2, Task 6, Task 10), Task
14's two uncalled `## Wall Membership` rows, AC-5 bucket (a)'s second-parameter disposition (Design §4),
the `Meeting`/`tags` citation (`## Verification`), the write-then-move window (`## Edge Cases`,
`## Risk Analysis`), M1's exact bound (Design §2) and the M3 `load()` window (`## Verification`'s
close-out). No signed fence's bytes are touched, so every `ac_hash_AC-N` remains byte-intact.)*

*(Revised a THIRD time, 2026-09-25, to fold the THIRD threat-model round's one new required
mitigation. M1–M4 held on their named tasks with their ordinals unmoved and are restated unchanged;
M5 is new and it is the previous round's own fold coming back as a finding, which is why the note
above is superseded rather than extended. The second spec-review round fixed a false RED in AC-4's
`.md`-token rule — `sorted(V.rglob('*.md'))` at `docs/stem-divergence-live-baseline.md:36` — by
excluding a REGION, every line inside a fenced code block, and that region is exactly where the
close-out's pasted `lint_vault --report` output lands, a command that names note filenames per path.
The narrower fix was available for the same cost and is now taken: exempt the TOKEN CLASS (a token
containing `*`) and keep the rule whole-file. It lands in a new Design §4a, in Task 13's privacy-wall
clause and its reader battery, in `## Verification`'s structural arms, in the `writes` fence for
`tests/test_stem_divergence_baseline_shape.py` and in a `## Mitigation Folds` record. Two stale
enumerations found while folding are corrected in the same edit — the `writes` fence for
`tests/test_stem_name_divergence_detector.py` and `## Verification`'s structural arms both said FIVE
planted detector members while Task 12 and §3a carry six — and both are re-stated as the LIST rather
than as a count, so the next plant does not reopen them (WI-229). No signed fence's bytes are touched
by any of it; every `ac_hash_AC-N` remains byte-intact, and AC-4's own `desc` already promises exactly
what M5 restores — "no absolute path and no note filename leaks the privacy wall" — so this is a
refinement of the CHECK toward the frozen criterion, never a change to the criterion.)*

*(Revised a FOURTH time, 2026-09-25, after the THIRD spec-review round. Its two blocking findings are
the same paragraph seen twice — `rename_note`'s branch structure — and both land here. (1) The door
read `old_stem` off the SOURCE and guarded the alias append on `old_stem != new_stem`, so after a
rename whose move committed and whose alias write raised, the prescribed recovery appends NOTHING;
three surfaces promised that re-run as a repair while Task 10 correctly asserted the opposite. The
honest residual and its one-field caller-side recovery are now stated, and — because the same
over-claim had been made about three DIFFERENT residuals, which is the generator rather than the
instance — the whole class is closed by one table enumerating the door's sequence points and what a
re-run does at each, with the contract stated as an invariant: a re-run is always SAFE, repairs
exactly the residuals in which the MOVE did not happen and whose cause has gone, and repairs nothing
that happened after the move (Design §2, "What a half-failed rename leaves" and "the CLASS behind that
finding"; ordering decision 2; three `## Edge Cases` entries; two `## Risk Analysis` rows; Task 6).
Task 10 gains an arm that ASSERTS the residual rather than describing it — the alias write forced to
raise, the moved-stamped-un-aliased state pinned, the re-run shown to repair none of it and the
one-field recovery driven — which is why Task 6 also fixes the alias writer's import spelling, since
that arm patches it by name. (2) `destination == source` was a raw
string compare against a stamp `move_note` hands back RESOLVED, so on this project's own platform the
idempotent re-run fell through to the case-only two-step and Task 10's "no `move_note` call recorded"
would have been RED against a verbatim-correct build. The branch key is now file identity — resolved
PARENT plus RAW `.name`, which keeps the case-only branch reachable — and Task 10 PLANTS the spelling
divergence rather than depending on `$TMPDIR` being a symlink (Design §2's door body and its new
paragraph, Task 6's branch clause, Task 10, a new `## Edge Cases` entry, a new `## Risk Analysis`
row). Two consequences of the same fact are prescribed in the same edit, because a builder hits both:
the door does NOT re-spell the stamp back into the repository's spelling, and every Task 10 assertion
comparing a path the door returned or stamped against a path the test created resolves both sides. Six non-blocking notes are folded in the same edit, each named where it lands: the `!=`'s
operand normalization, closed as Design §3a's FIFTH member with Task 12's plant (vii) and the ladder
declaration extended from intersections down to SUB-CELLS across all six conjuncts; §4a's
`docs/lint-vault-live-baseline.md` line citation (`:5` → `:6`); the WI-126 body constraint on the
mutation table's Book and Meeting rows; `update_fields`' `f"@{new_name}.md"` composition (Design §2,
Task 6); the M1 paragraph's "non-person" precision, which omitted COMPANY; AC-1(g)'s vault-walk oracle
(Task 9); and `## Wall Membership`'s mid-function line anchor (`:127` → `:112`). No signed fence's
bytes are touched, no `## Mitigation Folds` record needed an edit — M1's, M3's and M4's quoted Design
sentences and Task-6 work text are unchanged byte for byte, the branch-key clause being a SEPARATE
clause beside them — and every `ac_hash_AC-N` remains byte-intact.)*

*(Read back a FIFTH time, 2026-09-25. The third spec-review round's two blocking findings and all six
of its non-blocking notes were already folded when this pass opened — the fourth note above lists every
site and each was re-read against the code, not against the note. So this pass ordered no fix and spent
itself on the one rung the branch-key fix OPENED: the key settles which SPELLING takes which branch and
said nothing about what ELSE makes `source.samefile(destination)` true, which is the same generator one
level down. Design §2 now enumerates that population at source — a case variant, a hard link, a symlink
at the destination naming the source — with each outcome read off `move_note`'s body, no work ordered,
and pointers from the re-run table's second row and the `## Edge Cases` case-only entry. One Task 10
precondition is stated in the same edit: the M1 arm's in-vault-SUBDIRECTORY cell must `mkdir` that
directory, or `os.link` raises against a missing parent and the ACCEPTED cell is red for a reason that
is not M1's. No signed fence's bytes are touched, no `## Mitigation Folds` record needed an edit — the
sweep is a new paragraph BESIDE every sentence those records quote — and every `ac_hash_AC-N` remains
byte-intact.)*

*(Revised a SIXTH time, 2026-09-26, after the FOURTH spec-review round. Its one blocking finding is the
THIRD member of one class — `update_fields`' rename branch commits its content write and then discovers
the door will not complete the move — so it is answered with a FOLD and not a fourth disjunct. Round 2's
finding 1 was that member for NO PROVENANCE and M7 was it for A TYPE DECLARING NO `name`; both causes
are knowable in the frame and were closed by a disjunct. This round's — a destination ALREADY OCCUPIED
by a different note, with no race, no configuration and no exotic type — is NOT knowable in the frame,
and the precondition table's disposition of that row ("pre-checking is check-then-act and the syscall is
the stronger answer") is RIGHT. What was missing is the RESIDUAL that disposition leaves, and a rule
that partitions a surface while stating the residual of only one half is the generator. So the table
gains its COMPLEMENT: for every row it answers NO, what the method leaves and what the caller must do,
derived from the table's own rows and stated as one invariant — the content write has committed, the
note carries its new stored `name:` at its old filename with no alias and the entity un-re-stamped, and
the recovery is always "remove the cause, then call `rename_note` DIRECTLY", never a re-run of
`update_fields`, whose trigger now reads the committed name back out of the note. The choice the rule
makes is stated rather than left to silence — the residual is ACCEPTED, move-then-write is shown
UNAVAILABLE (the door's alias write invalidates the content write's `precondition=stamp`) and
pre-checking is refused — with the honest comparison against today, where the same call SUCCEEDS and
leaves the same divergence silently. The three surfaces that said it could not happen are corrected: the
`## Edge Cases` occupied-destination Decision is scoped to the DIRECT call with a new entry beside it,
the `## Risk Analysis` `update_fields`-moves-a-file row no longer claims the alias unconditionally and
gains its own row for the residual, and Prerequisites 7 discloses the three consumer-visible arms of the
PATCH change that RAISE. `## Verification`'s failure-mode list gains the mode and Task 10 the arm that
asserts the residual directly; Task 6 gains the negative clause that stops a builder "fixing" it by
pre-checking or reordering. Three non-blocking notes land in the same edit: the `aliases` mirror is
gated on `renaming` (Design §2's sequencing block and "Which `aliases` list wins", Task 6); the
`update_fields`-now-works-on-Book-and-Meeting widening is declared as a decision in Design §5; and
Design §1's `BaseEntity` quotation is restored to the verbatim source. No signed fence's bytes are
touched, no `## Mitigation Folds` record needed an edit — M1's, M3's, M4's, M6's and M7's quoted Design
sentences and Task-6 work text are unchanged byte for byte, every clause added being a SEPARATE clause
or paragraph beside them — and every `ac_hash_AC-N` remains byte-intact.)*

### 1. Data model — the provenance stamp

One new declared PRIVATE attribute on the base model, and nothing else. No frontmatter field, no
schema migration, no public signature change.

`obsidian_schemas/models.py:BaseEntity:31` today is:

```python
class BaseEntity(BaseModel):
    """
    Base class for all Obsidian entity types.

    Allows extra fields for forward compatibility - any fields in the
    frontmatter that aren't in the model will be preserved.
    """

    model_config = ConfigDict(
        extra="allow",
        # Use enum values when serializing
        use_enum_values=True,
        # Allow population by field name or alias
        populate_by_name=True,
    )

    type: str
    tags: List[str] = Field(default_factory=list)
```

*(Quoted verbatim from `obsidian_schemas/models.py:BaseEntity:23-40`, docstring and inline comments
included — the earlier form of this block silently dropped the two `ConfigDict` comments and the
docstring, which made one code quotation in this document a paraphrase while every other is exact;
fourth spec-review round, non-blocking note 3.)*

It gains exactly one member (and `PrivateAttr` joins the `pydantic` import):

```python
    #: The file this entity was PARSED FROM, or None. Set at the one parse
    #: boundary that holds a path (`parser.parse_markdown_file`) and read by the
    #: one function that chooses a write target
    #: (`BaseRepository._resolve_write_target`). A PrivateAttr and never an
    #: ordinary attribute: `extra="allow"` above means a bare assignment lands in
    #: `model_extra`, which `writer.model_to_frontmatter` serializes into every
    #: note the library writes (writer.py:120-123). A PrivateAttr is in neither
    #: `model_fields` nor `model_extra`, so it is unwritable BY CONSTRUCTION.
    _source_path: Optional[Path] = PrivateAttr(default=None)
```

Every property of that choice this item leans on is listed below — the list is the obligation, not its
length — and each is load-bearing and asserted rather than assumed:

- **Unwritable.** `model_to_frontmatter` composes the written mapping from
  `type(entity).model_fields`, then `entity.model_extra`, then the explicit `extra_fields`
  (`obsidian_schemas/writer.py:model_to_frontmatter:106-131`) — a private attribute is in none of the
  three. AC-1(h) asserts it over every note the sweep writes. *(Premise 11 names this function
  `entity_to_frontmatter`; the symbol is `model_to_frontmatter`
  (`obsidian_schemas/writer.py:model_to_frontmatter:89`). Corrected here rather than in the premise,
  which is the ideation gate's append-only record; every downstream citation in this document already
  uses the real name.)*
- **AC-1(h)'s promise is bounded, and the bound is stated here so no builder reads it as a
  sanitizer.** (h) is *no note the sweep writes GAINS a frontmatter key holding a path* — it is NOT
  "the package strips extras". `extra="allow"` means any undeclared key ALREADY in a note survives
  the round trip through `entity.model_extra` and is re-serialized unchanged
  (`obsidian_schemas/writer.py:model_to_frontmatter:119-123`), a forged `_source_path:` key included
  (M2, below). That is a pre-existing package property this item neither creates nor worsens, and it
  is why M2's arm asserts the READ direction — which value the seam consults — rather than the
  disappearance of the forged key. *(The threat model's 2026-09-25 "pre-existing extras leak, not
  this item's to fix" note, folded where AC-1(h) is defined rather than into a task: there is no work
  here, only a boundary that must not be mistaken for a promise.)*
- **Unforgeable from note content (M2, folded 2026-09-25).**
  A note whose own frontmatter declares `_source_path` naming a DIFFERENT file still resolves, through `_resolve_write_target`, to the file it was parsed from, and Task 2's check asserts that READ direction rather than inferring it.
  `extra="allow"` (`obsidian_schemas/models.py:BaseEntity:31-32`) lets a crafted `_source_path:` key
  reach model construction and land in `__pydantic_extra__`; a pydantic v2 `PrivateAttr` wins
  attribute lookup over it, and the parse's own assignment
  (`obsidian_schemas/parser.py:parse_markdown_file:244`) is the last write either way — so
  `getattr(entity, "_source_path", None)`, which is verbatim what `_resolve_write_target` reads,
  answers the parsed path. That is a property of two implementation details in two files, and
  AC-1(h) and Task 2's existing arms test only the WRITE direction (the stamp cannot reach a note),
  so the read direction is asserted explicitly: if it ever regressed the consequence is this item's
  own corruption turned into a DIRECTED one — a note steering a consumer's `save()` into a different
  person's file, bounded only by `_resolve_write_target`'s vault containment. The two-detail argument
  in this paragraph is the EXPLANATION of why the property holds; what Task 2 ASSERTS is the property
  itself — the accessor `_resolve_write_target` reads answers the parsed path, and nothing the seam
  reads answers the forged one — so the arm stays green if a pydantic release changes either detail
  (whether the underscore key is retained in `model_extra` at all, or how lookup precedence is
  implemented). Where the forged key ends up is a Build-Log observation in that task, never an
  assertion.
- **Survives `model_copy`, lost by `model_dump()`/`model_validate()`.** Pydantic v2 copies
  `__pydantic_private__` on `model_copy`, so the commonest consumer copy idiom PRESERVES the stamp,
  while a dict round-trip drops it. That is the honest boundary AC-1(f) declares. *(Round 6 note 4:
  precondition 2's question (4) listed `model_copy(update=…)` among the reconstructions that drop the
  stamp — it does not, and the audit's over-collection is in the safe direction. The consumer audit
  answers 0 reconstructions feeding a write, so the residual arm's consumer population is empty
  today.)*
- **Not an identity and not a key.** Nothing keys on it: `_cache`, `_file_map`, the alias/phone/slack
  dicts and the WI-125 identifier index are untouched. Approach F stays rejected. *(Round 6 note 5
  corrects one sentence of F's rejection: `_adopt` does write `_file_map[name_key] = file_path`
  (`obsidian_schemas/repositories/base.py:BaseRepository._adopt:186-190`), and `save`'s `file_path`
  is what this item changes — so after a provenance-bound save of a divergent entity the map points
  at the note that EXISTS instead of at a canonical filename that may not. That is an improvement, it
  is not index-neutrality, and no criterion rests on the sentence.)*

### 2. Flow — one resolution function, ten callers, one door

**The stamp is WRITTEN at one site.** `obsidian_schemas/parser.py:parse_markdown_file:244` already
builds the binding and drops it; it keeps it:

```python
    entity, extra_fields = parse_to_model(frontmatter, expected_type, path=file_path)
    if entity is not None:
        entity._source_path = file_path          # <- the one write of the stamp

    return ParsedDocument(...)
```

`parse_markdown_content` passes `file_path=None` (`parser.py:parse_markdown_content:283`) and stamps
nothing, so an entity from that route behaves exactly as AC-1(f) describes. All three `_load_file`
implementations route through `parse_markdown_file`
(`obsidian_schemas/repositories/base.py:BaseRepository._load_file:311`,
`obsidian_schemas/repositories/book.py:BookRepository._load_file:79`,
`obsidian_schemas/repositories/meeting.py:MeetingRepository._load_file:83`) and need no change —
which is the solve-in-one-place argument for the parse boundary over a per-repository stamp.

**The stamp is RESOLVED at one site.** A new private method on `BaseRepository`, placed beside
`get_file_path`:

```python
    def _resolve_write_target(self, entity: T) -> Optional[Path]:
        """THE one place a mutation target is chosen from PROVENANCE (WI-029).

        Returns the file this entity was parsed from when that file lies inside
        THIS repository's vault, and None otherwise. It NEVER falls back: each
        caller applies its own documented fallback, because the correct fallback
        differs by path and a uniform one would convert `update_fields`' and the
        body-writers' loud refusals into note CREATION.

        Existence is deliberately not part of the resolution — the stamp is a
        path, not a promise the file is still there. `save` creates at it (as the
        name-derived path does today); the refusing callers keep their own
        `.exists()` check one line later.
        """
        stamped = getattr(entity, "_source_path", None)
        if stamped is None:
            return None
        candidate = Path(stamped)
        try:
            inside = candidate.resolve().is_relative_to(self.vault_path.resolve())
        except (OSError, ValueError):
            return None
        return candidate if inside else None
```

The vault containment test is not decoration: a repository must not be steerable into writing
outside its own vault by an entity it was handed. `Path.resolve()` is non-strict, so a stamp naming a
file that has since been deleted still resolves and still answers the containment question.

**The stamp is CONSULTED at ten sites** — the nine name-bound write paths premise 12 enumerated,
plus the rename door this item ships. Each consults `_resolve_write_target` FIRST and applies its own
fallback:

| # | path | file:symbol | fallback on `None` |
|---|---|---|---|
| 1 | `BaseRepository.save` | `obsidian_schemas/repositories/base.py:BaseRepository.save:391` | create at `@{name}.md`, WARNING first when that file exists |
| 2 | `BaseRepository.update_fields` | `obsidian_schemas/repositories/base.py:BaseRepository.update_fields:438` | `get_file_path(name)`, then today's `ValueError` — and, when the update also CHANGES the name, a `ValueError` before any write even where `get_file_path` answers, since the move this method now performs has no provenance to resolve ("The no-provenance name change refuses BEFORE the write", below) |
| 3 | `PersonRepository.append_to_timeline` | `obsidian_schemas/repositories/person.py:PersonRepository.append_to_timeline:1403` | `get_file_path(person.name)`, then today's `ValueError` |
| 4 | `PersonRepository.append_to_body_section` | `obsidian_schemas/repositories/person.py:PersonRepository.append_to_body_section:1522` | as above |
| 5 | `PersonRepository.add_to_discuss_item` | `obsidian_schemas/repositories/person.py:PersonRepository.add_to_discuss_item:1653` | as above |
| 6 | `PersonRepository.update_to_discuss_item` | `obsidian_schemas/repositories/person.py:PersonRepository.update_to_discuss_item:1719` | as above |
| 7 | `PersonRepository.remove_to_discuss_item` | `obsidian_schemas/repositories/person.py:PersonRepository.remove_to_discuss_item:1793` | as above |
| 8 | `BookRepository.save` | `obsidian_schemas/repositories/book.py:BookRepository.save:167` | create at `self._get_file_name(entity)`, WARNING first when that file exists |
| 9 | `MeetingRepository.save` | `obsidian_schemas/repositories/meeting.py:MeetingRepository.save:189` | as above |
| 10 | `BaseRepository.rename_note` | NEW, `obsidian_schemas/repositories/base.py` | none — it RAISES `ValueError`; a mover with no provenance has nothing to move |

`PersonRepository.save` is NOT an eleventh: it is WI-021's rider and delegates through
`super().save()` (`obsidian_schemas/repositories/person.py:PersonRepository.save:1197`), binding no
path of its own. `CompanyRepository` declares neither `save` nor `get_file_path` and inherits the
seam whole.

**The three fallback shapes, written out**, because the asymmetry between them is the design and a
uniform fallback is the defect:

```python
# 1 — BaseRepository.save (and, with `self._get_file_name(entity)` in place of
#     the `@{name}.md`, Book's and Meeting's overrides). CREATES on a miss.
name = getattr(entity, "name", "Unknown")
resolved = self._resolve_write_target(entity)
derived = self.vault_path / f"@{name}.md"
if resolved is None and derived.exists():
    logger.warning(
        "no provenance on this %s: the write targets the name-derived filename "
        "and a note already exists there, path=%s", self.type_name, derived)
file_path = resolved or derived
write_markdown_file(file_path, entity=entity, ...)      # unchanged below

# 2 — update_fields and the five body-writers. REFUSE on a miss, exactly as today.
resolved = self._resolve_write_target(entity)    # PROVENANCE, or None
file_path = resolved
if file_path is None:
    file_path = self.get_file_path(name)
if file_path is None:
    raise ValueError(f"{self.type_name} not found in repository: {name}")
```

`update_fields` binds `resolved` and the five body-writers do not, and the extra name is not
cosmetic: `update_fields` is the only one of the six that can go on to MOVE the file, and its
name-change arm must know WHICH arm answered rather than merely which path it holds — see "The
no-provenance name change refuses BEFORE the write" below. The extra binding is legal under AC-5's
bucket (b) by the same clause that legalises the fallback itself: `resolved` is the seeded name,
`file_path = resolved` is an Assign whose VALUE mentions a tainted name, and
`file_path = self.get_file_path(name)` rebinds a tainted name inside an `ast.If` whose test names it —
which is AC-5's fifth ACCEPTED near-miss exactly (Design §4). The write's first positional is still
`file_path`.

The WARNING is emitted BEFORE `write_markdown_file` is called, and that ordering is the point: for
an entity with no provenance whose `@{name}.md` already exists, `write_markdown_file` reaches its
ZERO CASE (`snapshot_stamp` is `None`, so `is_create` is True —
`obsidian_schemas/writer.py:write_markdown_file:275`) and refuses with `NoteAlreadyExists`. The
readout must therefore precede the refusal or it is never seen. Behaviour is unchanged in both arms;
the class becomes reconstructable from a consumer's logs.

**And the mirror-image fact, load-bearing for every battery below.** A provenance-bound write of a
LOADED entity lands on `write_markdown_file`'s 2u arm rather than that zero case, because
`_load_file` already remembered the snapshot for that path —
`obsidian_schemas/repositories/base.py:BaseRepository._load_file:313` is
`vault_io.remember_snapshot(file_path, stamp)`, one line above the `return doc.entity` that drops
the provenance this item keeps. That is why AC-1's sweep binds every subject with
`repo._load_file(path)` and never with a bare `parse_markdown_file` (Task 9 says so in its own
words): a subject parsed without the repository's read would carry the stamp, resolve correctly, and
then be refused by door 2u's create arm — a RED cell against correct code, for a reason in neither
the criterion nor the seam.

**The door.** One public entry point on `BaseRepository`, the only thing in the package that moves a
note:

```python
    def rename_note(self, entity: T, new_filename: str) -> Path:
        """Door 3's one repository caller (WI-029). Moves the note THIS ENTITY
        was parsed from to `new_filename` inside this vault, keeps the old stem
        as an alias, repairs the caches, and RE-STAMPS the entity so its next
        write follows the file instead of recreating the old stem.

        The destination is the CALLER'S, never derived from the entity: deriving
        it here would re-introduce a name-bound target on the one path whose
        whole job is to move files, and each type's filename rule differs
        (`@{name}.md`, `_get_file_name`).
        """
        source = self._resolve_write_target(entity)
        if source is None:
            raise ValueError(
                f"no provenance for this {self.type_name}: rename_note moves the "
                f"note an entity was PARSED FROM, and this entity was not")
        if not source.exists():
            raise FileNotFoundError(f"File not found: {source}")

        destination = self.vault_path / new_filename
        try:                                            # M1 — CONTAINMENT
            contained = destination.resolve().is_relative_to(
                self.vault_path.resolve())
        except (OSError, ValueError):
            contained = False                           # unresolvable == not contained
        if not contained:
            raise ValueError(
                f"refusing to move this {self.type_name} outside the vault: "
                f"new_filename={new_filename!r}")

        mode = vault_io.guard_mode()                 # M6 — FAIL CLOSED
        if mode != "enforce":
            raise ValueError(
                f"refusing to move this {self.type_name} while the write guard "
                f"is not enforcing (OBSIDIAN_SCHEMAS_WRITE_GUARD={mode!r}): "
                f"under it door 3 OVERWRITES an occupied destination instead "
                f"of raising NoteAlreadyExists")
        old_stem = source.stem.lstrip("@")

        # WHICH FILE each side names, never how it is SPELLED. `move_note`
        # returns `_resolved(dest)` (vault_io.py:_resolved:234-243, :783), so a
        # stamp written by an earlier rename is RESOLVED while
        # `self.vault_path / new_filename` carries whatever spelling this
        # repository was constructed with — two strings, one file. The PARENT
        # is resolved and the RAW `.name` is not: resolving the directory eats
        # the spellings the environment supplies, while leaving the basename
        # alone keeps a case-only destination out of this branch even on a
        # platform whose `resolve()` normalizes case. A final-component symlink
        # is deliberately not followed here — a symlinked SOURCE is door 3's
        # refusal and a symlinked DESTINATION is M1's containment question.
        same_place = ((destination.parent.resolve(), destination.name)
                      == (source.parent.resolve(), source.name))

        if same_place:                                  # idempotent re-run
            moved = source
        elif destination.exists() and source.samefile(destination):
            # CASE-ONLY on a case-insensitive filesystem: `os.link` would raise
            # FileExistsError against the note's OWN inode, so door 3 cannot go
            # straight there. Two steps through a staging name DERIVED FROM THE
            # SOURCE (never from the destination — the seam's value must reach
            # every move's first positional), and the staging name's own
            # existence is refused by door 3's syscall rather than by a check.
            # M3: the staging name keeps the `.md` SUFFIX, so the window between
            # the two moves holds a note every reader still sees.
            staging = source.with_name(destination.stem + ".rename-tmp.md")
            vault_io.move_note(source, staging)
            moved = vault_io.move_note(staging, destination)
        else:
            moved = vault_io.move_note(source, destination)

        entity._source_path = moved                     # RE-STAMP, before anything else can fail
        new_stem = moved.stem.lstrip("@")
        aliases = list(getattr(entity, "aliases", []) or [])
        if old_stem and old_stem != new_stem and old_stem not in aliases:
            aliases.append(old_stem)
            update_frontmatter_field(moved, "aliases", aliases)
            if hasattr(entity, "aliases"):
                entity.aliases = aliases
        self._adopt(self._get_cache_key(entity), entity, moved)
        logger.info("Renamed %s note from %s to %s",        # M4 — BOTH ends
                    self.type_name, source.name, moved.name)
        return moved
```

**Four clauses in that body are the threat model's REQUIRED mitigations** (2026-09-25), folded here
and into Task 6. They are clauses on work the plan already schedules; none of them moves the door's
structure, the seam, or a signed criterion. A FIFTH required mitigation, M7 (2026-09-26), lands one
frame over in `update_fields`' pre-write refusal rather than in this body and is stated with that
refusal below — the count here is of the DOOR's clauses, not of the item's required mitigations, which
`## Mitigation Folds` carries at seven.

- **The destination is CONTAINED (M1).**
  `rename_note` refuses a `new_filename` whose RESOLVED destination is not inside `self.vault_path`, raising `ValueError` before any `vault_io.move_note` call — the same containment test `_resolve_write_target` already applies to the SOURCE, applied to the caller-supplied destination, resolved rather than string-compared so that a symlink inside the vault cannot point the move outside it.
  Nothing underneath catches it: `destination = self.vault_path / new_filename` traverses on `..`
  and is replaced outright by an absolute operand (pathlib's `/` rule), `vault_io._resolved` is a
  bare `Path(path).resolve()` with no notion of a vault root
  (`obsidian_schemas/vault_io.py:_resolved:234-243`), and `move_note` checks a symlinked SOURCE and
  nothing about where `dest` points (`obsidian_schemas/vault_io.py:move_note:721-750`). RESOLVED and
  not string-compared because the escape has two spellings and only one is in the string: a dangling
  symlink at an in-vault filename resolves to the outside path, `os.link` succeeds there, and the
  note lands outside under a perfectly clean name. The one thing standing between this and the
  in-library caller today is accidental — `path_hostile`'s `/` regex
  (`obsidian_schemas/name_validation.py:249-259`) in a name-hygiene table this item's Scope Boundary
  declares read-never-edited, which `gate_write` skips entirely for a declared non-person,
  non-COMPANY type (`obsidian_schemas/name_gate.py:305-344`; a declared `company` write is validated
  inside that same branch against `COMPANY_TIER1_BRANCHES`, whose path-hostile class
  `obsidian_schemas/name_validation.py:_COMPANY_PATH_HOSTILE_RE:351` is WIDER than the person one —
  the precision matters only so a reader does not over-read the sentence, since M1 exists precisely
  because leaning on ANY of those tables is the shape it refuses) — and depending on it is the
  boundary-you-can-route-around shape. An unresolvable destination is treated as NOT contained, so the unenumerated case refuses
  rather than passing by assumption. The exception is a plain `ValueError` and NOT a `LoudFailError`
  leaf, for the same reason the no-provenance arm at the top of the method already is: both are the
  door refusing its own ARGUMENTS before any write is attempted, which is a caller error and not a
  write that failed, and `obsidian_schemas/errors.py:LoudFailError:37` subclasses `ValueError`
  anyway — so a consumer catching `ValueError` catches both, and no new leaf enters `__all__`.
  **M1's exact bound, stated so nobody over-reads it** *(threat model round 2's carried-forward note,
  folded here rather than left in a gate section)*. The clause is resolve-then-`os.link`, so it is
  check-then-act on a path: an attacker who can plant a symlink at the destination BETWEEN the resolve
  and the link can still win. That attacker already holds write access to Dave's vault directory, which
  is outside this item's threat model (Prerequisites 6 bounds the untrusted input to vault BYTES), and
  `os.link` has no `O_NOFOLLOW` spelling reachable through pathlib. M1's job is to stop a
  CALLER-SUPPLIED or request-derived filename from escaping, and it does that completely; it is not a
  promise about a concurrently-hostile filesystem, and the plan orders no work for the residual.
- **The case-only staging name stays in the `.md` namespace (M3).**
  The case-only two-step stages through `source.with_name(destination.stem + ".rename-tmp.md")`, so a rename interrupted between the two moves leaves a note that Obsidian, the repository and `lint_vault` can all still see rather than a file no reader picks up.
  Door 3's own principle is link-then-unlink *"deliberately over unlink-then-link: a failure between
  the two leaves BOTH paths present, and a duplicate is recoverable by hand while a lost note is
  not"* (`obsidian_schemas/vault_io.py:move_note:732-734`); a staging name OUTSIDE `*.md` manufactures
  exactly the hole that principle refuses to manufacture, because `BaseRepository.file_pattern` is
  `@*.md` (`obsidian_schemas/repositories/base.py:file_pattern:206-208`), `BookRepository`'s is
  `*.md` (`obsidian_schemas/repositories/book.py:file_pattern:51-53`) and `MeetingRepository`'s is
  `Meeting *.md` (`obsidian_schemas/repositories/meeting.py:file_pattern:52-54`) — every one of them
  suffix-anchored on `.md` — while `lint_vault` reads the vault with
  `sorted(vault_path.rglob("*.md"))` (`scripts/lint_vault.py:read_vault:123`) and Obsidian shows
  `*.md` — so `@Foo.md.rename-tmp` is invisible to every one of them while
  `@Foo.rename-tmp.md` is a visible, lintable, divergent note. `move_note` validates no suffix
  (`obsidian_schemas/vault_io.py:move_note:721-750`), so the change costs one expression, and the
  staging name is still composed through `source.with_name(...)`, which is what keeps the seam's
  value in every move's first positional. The cost is honest and accepted: during a SUCCESSFUL
  two-step a concurrent `load()` can now see the staging note where before it saw nothing. That
  window is two `move_note` calls wide, it exists only on the TWO-STEP branch — one live row, and the
  branch's two other reachable members are enumerated in the same-file sweep below with no work
  ordered — and the alternative is trading a transient extra note for a permanent invisible one, which
  is the direction door 3's own link-then-unlink ordering already chose.
- **The audit line names both ends (M4).**
  `rename_note`'s audit line names the SOURCE path as well as the destination, so a relocation performed by `update_fields` on a consumer's behalf is reconstructable from logs.
  The item argues its own logging rule at the `save` WARNING — the class must be *"reconstructable
  from a consumer's logs instead of being discovered as a corrupted note months later"* — and after
  this item `update_fields` MOVES a file on every name change, permanently, in three consumer
  repositories (the risk table rates that likelihood *certain*), so the one act with no undo is the
  one whose before-state must be in the log. `source.name` and `moved.name`, not absolute paths:
  that is the package's shipped INFO idiom (`obsidian_schemas/repositories/base.py:411` logs
  `@{name}.md`) and it adds no PII surface the package does not already have.
- **The door FAILS CLOSED when the write guard is not enforcing (M6).**
  `rename_note` reads `vault_io.guard_mode()` and raises `ValueError` naming the mode unless it answers `"enforce"`, beside M1's containment block and before any `vault_io.move_note` call, because every occupied-destination refusal this item relies on is conditional on that mode — under `OBSIDIAN_SCHEMAS_WRITE_GUARD=observe` door 3 does `os.replace(source, target)` and DESTROYS the occupied note instead of raising `NoteAlreadyExists`.
  The fail-open is in the door, not in this item's prose: `obsidian_schemas/vault_io.py:_move_locked:757-771`
  catches the kernel's `FileExistsError` on `os.link` and, when `guard_mode() == "observe"`, logs a
  WARNING, performs `os.replace(source, target)`, forgets both snapshots and RETURNS the destination
  as though the move had succeeded — so `rename_note` would go on to append an alias, `_adopt` the
  entity and log a successful rename over a third party's destroyed bytes. That is
  `docs/concurrent-access.md:649-656`'s declared residual **R9** verbatim (*"while it is set, this
  item's Intent is explicitly not delivered for doors 2 and 3"*), and it was a defensible residual
  exactly while door 3 had, in this document's own words, "exactly ONE caller in the tree today
  (`scripts/lint_vault.py:1343`, quarantine)". THIS item is what makes door 3 the package's
  relocation capability, ships it public to three `-e` consumers and drives it on every
  `update_fields` name change — a likelihood `## Risk Analysis` rates *certain (it is the design)* —
  so the residual's blast radius is created here and closing it is this item's cost. It is reached by
  the estate's own runbook rather than by an attacker: `docs/concurrent-access.md:4286` names
  `OBSIDIAN_SCHEMAS_WRITE_GUARD=observe` as the cheapest ROLLBACK LEVER and `:2556` as the
  measure-before-adopting mode the three consumers are invited to set, so a consumer that hits a
  write-guard refusal and reaches for the documented rollback silently turns the relocation door's
  refusal into an overwrite. `guard_mode` is read PER CALL
  (`obsidian_schemas/vault_io.py:guard_mode:169-181`, an `_env_setting` over
  `OBSIDIAN_SCHEMAS_WRITE_GUARD` defaulting to `"enforce"`), so the check sees the mode in force at
  the moment of the move and no restart is involved in either direction. **The mode is read through
  `vault_io.guard_mode()` and NEVER through a second `os.environ` access**, even though
  `obsidian_schemas/repositories/base.py:9` already imports `os` and the wrong spelling would build:
  `obsidian_schemas/vault_io.py:_env_setting:104-115` reserves that capability to itself in writing
  (*"it either routes through here and gets the rule, or it names `os.environ` a second time — which
  is a capability duplication inside the one file the routing wall excludes"*), and going through the
  function is also what makes an INVALID value refuse (as `WriteFailedError`, the mode's own rule)
  rather than being read here as some third mode. The refusal is a plain `ValueError` for the same
  reason the no-provenance and M1 arms are — the door refusing its own preconditions before any write
  is attempted — and it NAMES the mode, which carries no PII by construction because `guard_mode`'s
  validator admits exactly `"enforce"` and `"observe"`
  (`obsidian_schemas/vault_io.py:guard_mode:176-181`).
  **M6's exact bound, stated so nobody over-reads it.** The clause covers the door THIS ITEM SHIPS and
  deliberately not door 2's create arm (`obsidian_schemas/vault_io.py:create_note:709-718`), which has
  the identical fail-open and which AC-1(f) leans on for its `NoteAlreadyExists`. This item moves that
  arm in neither direction — (f)'s declared behaviour is *"today's behaviour holds"*, and today's
  behaviour under `observe` is today's behaviour under `observe` — so it remains WI-004's R9 and
  belongs to WI-004's backlog, not to Task 3. The tempting over-fold is a guard-mode refusal on every
  write path in the package: that is a second behaviour this item was not asked for and would put the
  seam itself behind a configuration check it does not need.

**And the CLASS behind M6, swept and closed here rather than one sentence at a time.** The generator
is not "one paragraph was imprecise": it is that door 3's occupied-destination refusal is conditional
on a process-wide setting that no surface of this document named, so EVERY sentence leaning on that
refusal was false under one environment variable. Six surfaces state it, four of them citing the
syscall — AC-2(b) (signed), ordering decision 1 below, the `## Edge Cases` live-MERGE entry, the
`## Edge Cases` write-then-move race entry, the re-run table's first row, and `## Risk Analysis`'s
Rollback paragraph. M6 closes all six the same way and in one place: the condition becomes a
PRECONDITION OF THE DOOR, so the door is never reached with the refusal downgraded, and every one of
those sentences is true of every call that gets past this clause. Each surface therefore points HERE
for the qualification instead of restating it — and so do the two further mentions the modeler's list
did not carry, `## Risk Analysis`'s non-atomicity row and this section's write-then-move Edge Case,
which were found by re-reading every "by syscall" in the document rather than by working the list.
The seventh mention, `## Approach` (2)'s *"refuses an occupied destination by syscall"*, is left
standing where it is: that section is the ideation gate's append-only record and is overruled HERE,
exactly as ordering decision 5 overrules its locking sentence.
**AC-2(b) is untouched and stays true as written**
— its check runs under the floor command, which sets no environment, so `guard_mode()` answers its
`"enforce"` default and the door raises `NoteAlreadyExists` exactly as the signed text says.
Then the next rung of the ladder, DECLARED rather than assumed: the whole guard-conditional refusal
surface in `vault_io` is three sites, found by reading every `guard_mode()` and `_refuse` use in that
module rather than by remembering them — `write_note`'s precondition mismatch
(`obsidian_schemas/vault_io.py:_refuse:188-199`, reached at `obsidian_schemas/vault_io.py:write_note:697`),
`create_note`'s no-clobber (`obsidian_schemas/vault_io.py:create_note:712-718`) and `_move_locked`'s
occupied destination (`obsidian_schemas/vault_io.py:_move_locked:757-771`). The third is this item's
and is closed above. The second is AC-1(f)'s and is bounded above. The first this document leans on
NOWHERE — it names `vault_io.write_note(file_path, new_content, precondition=stamp)` only to say the
write has COMMITTED, never to claim a refusal — so it is out of scope by measurement and not by
omission. `move_note`'s symlinked-SOURCE refusal (`obsidian_schemas/vault_io.py:move_note:736-740`)
raises unconditionally and is untouched by the mode, which is why AC-2(d) needs nothing from M6.

**Which branch fires is decided by WHICH FILE each side names, never by how the path is SPELLED**
*(revised 2026-09-25 after the third spec-review round's blocking finding 2)*. The three branches above
used to discriminate with `destination == source`, a raw `Path` comparison, and that is a discriminant
the ENVIRONMENT decides rather than the caller. `vault_io.move_note` returns `_move_locked`'s `target`,
which is `_resolved(dest)` — a bare non-strict `Path(dest).resolve()`
(`obsidian_schemas/vault_io.py:_resolved:234-243`, `obsidian_schemas/vault_io.py:move_note:741-742`,
`obsidian_schemas/vault_io.py:_move_locked:783`) — so after ONE rename the entity's stamp is a RESOLVED
path, while `destination = self.vault_path / new_filename` is built from
`obsidian_schemas/repositories/base.py:_resolve_vault_path:104-114`'s `Path(str(candidate).strip())`,
which resolves nothing. On macOS `/var` is a symlink to `/private/var` and
`tests/support.py:temp_dir:31-37` — the zero-argument temp-directory idiom every AC check must use,
since a conveyor-invoked check takes no `tmp_path` fixture — hands back an UNRESOLVED `mkdtemp` path
under `$TMPDIR` (which is why `tests/test_lint_vault_fix_rules.py:_temp_vault:158-191` resolves both
sides of every comparison it makes). So on this project's own platform the idempotent re-run's two
operands are the same file under two strings: the string compare answers False, the door falls through
to the CASE-ONLY two-step, performs two real moves through a staging name, and the property
`## Edge Cases` and `## Risk Analysis` both call "idempotent" is false — with an interrupted re-run
able to leave a `.rename-tmp.md` where the document says nothing moved at all. The fix is the key
above and it is WI-149's oracle rule applied to a branch discriminant, twice over. `.resolve()` on
each side's PARENT normalizes exactly the spellings the environment supplies — a symlinked temp root,
a `..` segment, a relative vault path — and the RAW `.name` is compared unnormalized, so the case-only
branch stays reachable even on a platform whose `resolve()` canonicalizes case (POSIX `realpath`
resolves symlinks only and preserves case; the door must not DEPEND on that, which is the whole point
of the finding). The two branches therefore remain distinct and total over the same-file population:
same directory AND identical basename spelling is the no-op; same file under a DIFFERENT basename
spelling is the two-step — named for the case variant it exists to serve, and the sweep immediately
below enumerates the rest of what reaches it — where `source.samefile(destination)` is the inode test
and needs the `destination.exists()` guard because `samefile` raises on a missing operand. Task 10's IDEMPOTENCE
arm plants the spelling divergence rather than waiting for the platform to supply it. **What this
deliberately does NOT do is re-spell the stamp.** `entity._source_path = moved` keeps `move_note`'s own
resolved answer rather than substituting the repository's spelling of it, because normalizing at the
one place a DECISION is read is total (it survives a relative `vault_path`, a `..` segment and a
symlinked root alike) while re-spelling only papers over the one divergence the door itself
introduces. The one visible consequence is that `get_file_path(name)` answers a resolved path for a
note the door moved, where `load()`'s entries carry the constructor's spelling: the same file either
way, and every consumer of that mapping opens it, `.exists()`es it or hands it to a `vault_io` door,
each of which resolves internally (`obsidian_schemas/vault_io.py:_resolved:234-243`).

**And the next rung of THAT ladder, swept and DECLARED rather than left as the next round's finding.**
The branch key above settles which SPELLING lands in which branch; it does not say what else can make
`source.samefile(destination)` true. The second branch is NAMED for the member it exists to serve, and
two other shapes reach it — so the population is enumerated at source rather than remembered, because
"two distinct in-vault names for one inode" is a closed set: a CASE variant on a case-insensitive
filesystem, or a LINK. Each member's outcome below is read off `move_note`'s own body rather than
assumed, and **no work is ordered for any of them** — they are here so a later reader does not
rediscover them as a defect:

- **A case variant on a case-insensitive filesystem.** The member the branch exists for (live baseline
  §2, row 3, the one live row). Two moves through the M3 staging name; one directory entry afterwards,
  spelled in the new case, old spelling in `aliases`. Asserted by Task 10's case-only arm.
- **A second HARD LINK inside the vault naming the same inode.** The two-step's first move succeeds
  (source → staging) and its second RAISES `NoteAlreadyExists`, because the destination's own directory
  entry is still present and `os.link` refuses it (`obsidian_schemas/vault_io.py:_move_locked:759-771`).
  The residual is the case-only branch's mid-flight residual exactly — a VISIBLE `.md` note at the
  staging name, which is M3's whole point — so the re-run table's second row already owns it and already
  names the hand recovery. Loud, and nothing is lost.
- **A SYMLINK at the destination naming the source.** M1 admits it, because it resolves INSIDE the
  vault, and it is the case the door's own branch comment hands on when it says *"a symlinked
  DESTINATION is M1's containment question"*. Both moves then run to completion and land the note back
  where it started:
  `move_note` resolves its `dest` (`obsidian_schemas/vault_io.py:move_note:741-742`), and by the time
  the second move runs the first has already unlinked the symlink's target, so the non-strict
  `resolve()` still answers the SOURCE path and `os.link` recreates the note there. The door returns
  that path, re-stamps the entity to the file it actually occupies, appends no alias (`old_stem ==
  new_stem` by then) and logs a rename from a name to itself. Nothing is lost, nothing is written that a
  reader cannot see, and the caller learns from the RETURN VALUE which file it holds. Refusing it
  instead would mean teaching the door a third symlink rule where `move_note` already owns the SOURCE
  and M1 already owns the destination.

That is the whole population, and the reason no work is ordered is the same in each row: the member is
either the one Task 10 already asserts, a loud refusal whose residual M3 already made visible, or a
no-op that returns the truth. A fourth shape would have to be a fourth way for two in-vault names to
name one inode, which the filesystem does not provide.

**What a half-failed rename leaves, and what a re-run does and does NOT repair** *(revised 2026-09-25
after the third spec-review round's blocking finding 1; three surfaces of this document previously
claimed a repair the prescribed body cannot perform)*. `old_stem` is read off the SOURCE, before the
branch, and the append is guarded on `old_stem != new_stem`. So after a rename that moved the file and
then raised out of `update_frontmatter_field`, the residual is a moved, correctly-stamped note missing
one alias — and `rename_note(entity, <the same filename>)` does NOT restore it: `_resolve_write_target`
now answers the DESTINATION, `same_place` is True, `old_stem == new_stem`, and nothing is appended. The
re-run is a safe no-op, not a repair, and Task 10's IDEMPOTENCE arm asserts exactly that (`aliases`
unchanged). **The recovery is a one-field edit by the caller** — `repo.update_fields(entity,
{"aliases": [*entity.aliases, <the old stem>]})`, or a hand edit of the note's `aliases:` — and
`## Edge Cases` states it there. Repairing it inside the door would need the door to remember a stem
provenance no longer holds, which means either re-stamping LAST (rejected by ordering decision 2, since
a failure then leaves an entity whose next `save()` recreates the note the rename just removed — a fork
manufactured by the repair) or persisting an intent record, a journal this item does not ship. The
trade is deliberate and is the same direction door 3's own link-then-unlink ordering already chose: an
un-aliased moved note loses one reachability route and is repairable by one field edit, while a fork is
the harm the item exists to end.

**And the CLASS behind that finding, closed once here instead of one residual at a time.** Three
surfaces of this document said "recoverable by re-running the idempotent door" about three DIFFERENT
residuals, and only some of them are. The generator is that "idempotent" answers *is a second call
safe?* while every one of those sentences was using it to answer *does a second call REPAIR this?* —
two different questions, and the door only ever answers the first. So the repair question is settled
totally, by enumerating the door's own sequence points, and every other surface points here rather
than re-deriving it:

| where the first call stopped | residual | what a re-run of the door does | the recovery |
|---|---|---|---|
| before or at the move — the door refused its own preconditions (no provenance, uncontained destination, a non-enforcing write guard: M6), `move_note` refused (`NoteAlreadyExists`, symlinked source), or the process died before the first `os.link` | nothing moved, nothing written, stamp unchanged | performs the whole rename — move, alias, `_adopt` — ONCE the cause is gone; a precondition refusal simply repeats identically until the argument, the environment or the vault changes | remove the cause the exception names (free the destination, pass provenance, pass an in-vault name, unset `OBSIDIAN_SCHEMAS_WRITE_GUARD` or set it back to `enforce`), then re-run |
| the two-step branch, between its two moves — reached by a case variant, and by a hard link naming the same inode (the same-file sweep above) | the note sits at the staging name; the source is gone; the entity was never re-stamped | with the SAME entity: `FileNotFoundError` from the door's own `source.exists()`, since the stamp names a file that no longer exists. With an entity loaded from the STAGING note: it completes the move, but appends `<stem>.rename-tmp` to `aliases`, because that is honestly the stem it moved from | a hand rename (the residual is VISIBLE by M3, and this is the branch with one live row, repaired by the conductor by hand) |
| after the move, at the alias write | moved, correctly stamped, one alias missing | safe NO-OP: `same_place`, no second move, nothing appended | `repo.update_fields(entity, {"aliases": [*entity.aliases, <the old stem>]})`, or a hand edit |
| after everything | none | safe NO-OP | nothing to recover |

The invariant that row set carries, and the one worth stating as the door's contract: **a re-run is
always SAFE — it never moves twice, never appends twice and never forks — and it repairs exactly the
residuals in which the MOVE did not happen and the cause has gone. It repairs nothing that happened
AFTER the move.** Task 10 asserts the no-op row; the first row is the ordinary AC-2 arms; the second
is `## Edge Cases`' staging-name entry.

**That table is scoped to the DOOR's own frame, and the scoping is load-bearing** *(2026-09-26)*. Its
first row's *"nothing moved, nothing written"* is true of `rename_note` and of a caller that drives it
directly; it is NOT the whole state when the caller is `update_fields`, whose content write has already
COMMITTED by the time the door is entered. What that method leaves for each of those refusals is stated
where the refusals are enumerated — the complement rule beneath Design §2's precondition table, below —
and the two tables are read together: this one answers *what does a re-run of the DOOR do?*, that one
answers *what did `update_fields` leave, and what does the caller do about it?*

Five orderings inside it are decisions, not details:

1. **Move first, alias second.** AC-2(b) requires that a refused rename leave BOTH files
   byte-identical; an alias written before the move would falsify that on the source. `move_note`
   refuses a symlinked source and an occupied destination before it writes anything
   (`obsidian_schemas/vault_io.py:move_note:736-740`, `vault_io.py:_move_locked:759-771`), so nothing
   is written on either refusal arm. The occupied-destination half of that sentence holds because M6
   makes an enforcing write guard a precondition of this door — under `observe` that refusal is an
   `os.replace` instead, which is why the mode is checked above rather than qualified here; the
   symlink half is unconditional. M6's bullet owns the qualification for every surface of this
   document that names the refusal.
2. **Re-stamp immediately after the move, before the alias write.** A failure in the alias write then
   leaves a moved, correctly-stamped note missing one alias — loud, and SAFE to re-run, because
   `same_place` is the first branch. Safe is the whole claim: the re-run performs no second move and
   appends no duplicate, and it does not append the MISSING alias either, because provenance has
   already moved to the destination and `old_stem` is read from it (the paragraph above states the
   residual and names the one-field recovery; `## Edge Cases` resolves it). The reverse order would
   leave an entity whose next `save()` recreates the note the rename just removed: a fork manufactured
   by the repair — which is why the un-appended alias is the accepted side of this trade and not a
   defect to fix by re-ordering.
3. **The alias is appended to the MOVED file and to the in-memory entity**, then one `_adopt`, which
   is what re-indexes `_alias_index` and repoints `_file_map` at the new path
   (`obsidian_schemas/repositories/base.py:BaseRepository._adopt:184-191` →
   `obsidian_schemas/repositories/person.py:PersonRepository._index_entity:272-275`). That is AC-2(a)'s
   "resolves under BOTH names afterwards", as a resolution property rather than the presence of a key.
   **The asymmetry between the two halves is a DECISION, not an oversight** — the FILE write is
   unconditional and the in-memory assignment is guarded by `hasattr(entity, "aliases")`, because they
   write to two different things. `aliases:` is OBSIDIAN's own frontmatter key and is type-agnostic: a
   moved company, book or meeting note keeps its old stem reachable in Obsidian exactly as a person
   note does, and `CompanyRepository` inherits this door whole (it declares neither `save` nor
   `get_file_path`), which is what lets WI-022's seven mangled company notes ride the same conductor
   repair run. The MODEL field is Person's alone (`obsidian_schemas/models.py:Person:80`; `Company`,
   `Book` and `Meeting` declare none), so an unguarded `entity.aliases = …` would mint an UNDECLARED
   extra on a non-Person entity under `extra="allow"` — a value `model_to_frontmatter` then
   re-serializes out of `model_extra` on that entity's next full `save`, i.e. this door quietly
   teaching a second writer a field the model does not have. The guard is therefore keyed on the
   DECLARED field and never on a type name, and nothing downstream needs the extra:
   `_index_entity` reads `entity.aliases` directly
   (`obsidian_schemas/repositories/person.py:PersonRepository._index_entity:272-275`) and exists only
   on the Person side.
4. **The alias write DELEGATES to `writer.update_frontmatter_field`** rather than parsing and
   re-serializing here. Three reasons, and the third is structural: it is already gated
   (`obsidian_schemas/writer.py:update_frontmatter_field:385-387`, `whole_record=False`, so a note
   whose stored name is already Tier-1 dirty stays writable); it is already a path-taking leaf, so it
   adds no frontmatter write arm to WI-021's wall; and a `parse_frontmatter` call in this frame would
   make `rename_note` a member of `functions_parsing_then_writing`, which
   `tests/test_concurrent_access.py:test_wi020_derivations_survive_the_routing:1080` pins by set
   equality to `{write_markdown_file}`.
5. **No outer lock is held across the two acts, and this is the ONE lock rule the whole item obeys.**
   `update_frontmatter_field` takes `note_lock` itself
   (`obsidian_schemas/writer.py:update_frontmatter_field:368`) and `move_note` takes BOTH paths' locks
   in a global sorted order (`obsidian_schemas/vault_io.py:move_note:744-750`); holding the source
   lock across a call that acquires the destination's would violate that order for a concurrent mover.
   **Reentrancy is NOT the argument, and a sentence elsewhere in this document that says it is has
   been superseded here.** Door 3's own docstring says the locks are reentrant, "so a caller already
   holding either is unaffected" (`obsidian_schemas/vault_io.py:move_note:744-747`) — that excuses
   RE-ACQUIRING a lock you already hold; it says nothing about ORDER. A caller holding
   `note_lock(A)` that then calls `move_note(A, B)` where `str(B) < str(A)` acquires A-then-B against
   the global order, and a concurrent `move_note(B, A)` acquires B-then-A: the two block each other,
   and `rename_note`'s `update_frontmatter_field(moved, …)` is a second out-of-order acquisition from
   inside the same held lock. No site in the tree holds a note lock across `move_note` today
   (`scripts/lint_vault.py:1343` is its one caller and holds none), so this item would be the one
   INTRODUCING that edge — which is why the rule is structural rather than remembered, and why the
   rule is stated as a PROPERTY OF THE PACKAGE and not as a property of this door:
   **no call to `move_note`, to one of `writer.py`'s path-taking leaves, or to a repository method that
   itself calls `move_note`, is lexically nested inside a `with` statement whose items mention
   `note_lock`.** Each clause earns its place. `move_note` takes two locks. Each path-taking leaf takes
   its OWN lock on a path the calling frame did not lock (`update_frontmatter_field:368`,
   `update_frontmatter_fields:434`, `roundtrip_file:497`, `write_markdown_file:258`). The third clause
   is what makes the rule reach the placement below, and it is DERIVED rather than a name:
   `functions_calling(python_files_under(PACKAGE_ROOT), "move_note")` is exactly
   `{BaseRepository.rename_note}` after this item — AC-2(c)'s own scan, which Task 10 already runs —
   and the bare method names it returns join the forbidden callee set, so `update_fields` calling
   `self.rename_note(...)` inside its lock is refused by the same scan that refuses a direct
   `move_note` call, and a future second mover enlists automatically instead of needing to be
   remembered. The single-path doors `write_note` and `create_note` are deliberately NOT in the set,
   because `write_markdown_file` must call them inside its own lock
   (`obsidian_schemas/writer.py:317`, `:319`, and `vault_io._require_lock` demands exactly that);
   collecting them would make the scan RED against shipped code. The rule holds over the package today:
   every `note_lock` holder in it — `writer.py:258`, `:368`, `:434`, `:497`, `base.py:448`, and the
   five body-writers at `person.py:1410`, `:1529`, `:1660`, `:1726`, `:1800` — calls no member of that
   set. Task 7 ships the derivation, Task 10 asserts it EMPTY over `PACKAGE_ROOT` with a planted
   both-ways battery. That assertion is what makes `update_fields`' door-call placement below
   checkable rather than promised.

**`update_fields` calls the door on a name change**, replacing the deliberate leave-behind at
`obsidian_schemas/repositories/base.py:BaseRepository.update_fields:454-459`. The ORDER inside that
method is a real sequencing constraint *(round 4 note 2)* and is prescribed rather than discovered:

```
    with vault_io.note_lock(file_path):        # the frame's EXISTING block, unchanged
        read + parse                           content, stamp = vault_io.read_note(file_path)
                                               frontmatter, body = parse_frontmatter(content)
        decide the rename                      renaming = ("name" in updates and
                                                   updates["name"] != frontmatter.get("name", ""))
        REFUSE IT NOW IF IT CANNOT COMPLETE    if renaming and (resolved is None or
                                                       vault_io.guard_mode() != "enforce" or
                                                       "name" not in
                                                       type(entity).model_fields):
                                                   raise ValueError(...)   # nothing written yet
        ...                                    # gate the delta
        write the content                      vault_io.write_note(file_path, new_content,
                                                                   precondition=stamp)
                                               # the LAST WRITE inside the lock; `stamp` is from
                                               # this frame's own read (base.py:449)
        mirror what the write committed        if renaming and "aliases" in updates:
                                                   entity.aliases = frontmatter["aliases"]
                                               new_name = updates["name"] if renaming else None
    # ---- the `with` block ENDS here. NO lock is held across the call below. ----
    THEN move (only if `renaming`)             moved = self.rename_note(entity, f"@{new_name}.md")
    THEN rebind                                file_path = moved
    THEN reload                                updated_entity = self._load_file(file_path)
```

because the frame commits against the OLD path with a stamp `move_note` then forgets
(`obsidian_schemas/vault_io.py:_move_locked:780-781`) and reloads from that same path
(`base.py:493-495`, `ValueError` on a `None` reload). The alias append moves out of `update_fields`
into the door, which is where AC-2(a) puts it and which stops the same list being appended twice.

**`update_fields` composes `f"@{new_name}.md"` for every entity type it lets through, and that is
correct rather than an oversight of the door's own docstring** *(third spec-review round, non-blocking
note 4; the reach claim below was ASSERTED and not enforced until threat-model M7, 2026-09-26)*. The
door takes its destination from the caller because "each type's filename rule differs (`@{name}.md`,
`_get_file_name`)", and the one in-library caller then hardcodes the `@{name}.md` rule. It is right for
every type that can reach this line: `BaseRepository`, `PersonRepository` and `CompanyRepository` all
derive `@{name}.md`, and the two types with a different rule cannot reach it at all — **which is now a
property of the code rather than a reading of the models.** The earlier form of this paragraph said the
two types "cannot reach it, because the trigger is a change to a `name` field neither `Book` nor
`Meeting` declares"; that is a fact about `obsidian_schemas/models.py` (`Person:79` and `Company:128`
declare `name`; `Book:139` and `Meeting:247` do not, and `BaseEntity:39-40` declares only `type` and
`tags`) which the trigger never consults, since it is
`"name" in updates and updates["name"] != frontmatter.get("name", "")` — the CALLER's dict against the
NOTE's frontmatter, and a book note carries no `name:` key, so `frontmatter.get("name", "")` is `""`
and any non-empty `updates["name"]` set `renaming` True. The refusal's third disjunct
(`"name" not in type(entity).model_fields`, M7, stated in full below) is what makes the sentence true:
a `name` delta on a type that does not declare `name` is REFUSED before the content write, so by the
time this composition runs the entity's class declares `name` and `@{name}.md` is its filename rule by
construction. A future caller whose type derives its filename otherwise composes the destination with
`self._get_file_name(entity)`; the door is indifferent, which is why the rule lives in the caller.

**The door call sits OUTSIDE the `with vault_io.note_lock(file_path)` block — stated here because it
is the one placement decision in this method a builder could get either way, and because the earlier
drafts of this document stated it twice, oppositely.** `## Approach` (2) says "calling the door from
inside the already-held lock is itself safe, since it sorts both resolved paths into a global total
order and the locks are reentrant"; that sentence is SUPERSEDED by this paragraph and by ordering
decision 5 above (it is left standing there because `## Approach` is the ideation gate's append-only
record, and it is overruled HERE, where the builder reads this method's prescription), for the reason
decision 5 gives — sorting plus reentrancy makes `move_note`
deadlock-free only while no caller holds either lock across it, so the inside-the-lock placement is
precisely the configuration the sorted order cannot defend. Nothing in the sequencing argument wants
it inside: `vault_io.write_note(file_path, new_content, precondition=stamp)` has already COMMITTED
when the lock releases, `forget_snapshot(source)` is `move_note`'s own business
(`obsidian_schemas/vault_io.py:_move_locked:780-781`), and the reload at
`obsidian_schemas/repositories/base.py:BaseRepository.update_fields:493-495` is already outside the
block in today's code — so the three statements above simply extend the existing post-lock tail. The
structural consequence: this method must contain no `rename_note` call inside its `with`, which is
exactly the EMPTY set decision 5's derived scan asserts. AC-2's signed `why` is untouched and stays
true under this placement — it says the call "is safe with respect to LOCKING", which it is when no
lock is held, and it never says the call is made in-lock.

The entity handed to the door must carry the provenance of the note being edited: the door is called
with the caller's **`entity`** — the parameter `update_fields` was handed, already stamped by the
parse — and never with a freshly-constructed or re-parsed view. That is the object `rename_note`
re-stamps (`entity._source_path = moved`), reads `aliases` off, and `_adopt`s, so AC-2(e) (a `save()`
on the SAME in-memory entity lands in the new file) and AC-2(g) both turn on it being this one.
AC-2(g) then follows for free, because `_load_file` re-stamps on the reload.

**The no-provenance name change refuses BEFORE the write — and so does every other PRECONDITION the
door needs, which is the same clause and not a second one** *(revised 2026-09-25 after the second
spec-review round's blocking finding 1; the predicate widened from `resolved is None` to the door's
whole precondition class when threat-model M6 landed, and gained its third disjunct when M7 landed
2026-09-26; the heading keeps its original wording so this document's four pointers to it still
resolve)*. The
method deliberately keeps a name-keyed fallback — AC-1(g)'s second half turns on it — so `resolved`
can be `None` while `get_file_path(name)` answers, and for that entity `rename_note`'s documented
behaviour is the RAISE in the invocation table's row 10. Written naively the sequence commits the new
name at `base.py:490` and only then discovers the door will not move the file, leaving a note that is
divergent, un-aliased and unmoved, with an exception reaching a caller AFTER a successful write and no
reload. So the decision is made where nothing has been written yet: **inside the lock, immediately
after `renaming` is computed from `frontmatter` and BEFORE `gate_write`, `write_frontmatter` or
`vault_io.write_note` are reached, `if renaming and (resolved is None or vault_io.guard_mode() !=
"enforce" or "name" not in type(entity).model_fields): raise ValueError`** — naming the method, the name
it was asked to change to, and WHICH precondition failed: that a name change needs the provenance a move
is resolved from, that the write guard is not enforcing, or that this entity's own type does not declare
`name` and so derives no `@{name}.md` destination. The frame has performed one READ at that point, so the note is
byte-identical, the caller sees the refusal instead of a half-applied rename, and the residual state
is *nothing*.

**That same arm carries a SECOND CLAUSE, and it fires where `renaming` is FALSE** *(2026-09-26,
threat-model M8; stated in full as "the THIRD rule" below, which is where the reasoning lives — it is
named here so a builder reading this paragraph for the arm's SHAPE does not ship half of it)*. The
disjunction above is the whole of `if renaming and (…)`, so every delta carrying no `name` key skips it
entirely — and for a `Book` or a `Meeting` the filename rule is not made of `name`, so exactly those
deltas are the ones that move it. The arm is therefore two clauses, both raised inside the lock before
anything is gated or written:
`if not renaming and derive is not None and derive(projected) != derive(entity): raise ValueError`,
where `derive = getattr(self, "_get_file_name", None)` and `projected` is
`entity.model_copy(update={k: v for k, v in updates.items() if k in type(entity).model_fields})`.

**The predicate is the door's PRECONDITION class and not a list of remembered conjuncts, which is the
whole of the rule.** M6 arrived as a second reason the door refuses before it touches the filesystem,
and answering it with a second remembered conjunct would leave the THIRD as the next round's finding
— which is exactly what happened: M7 is the third, and it was findable only because the table below
declares its own coverage row by row. So the class is
enumerated at source — the door's own refusal arms, read off the body above, split by whether their
cause is knowable in this frame before the write:

| the door's refusal arm | knowable before `update_fields`' write? | who refuses early |
|---|---|---|
| no provenance (`source is None`) | YES — it is `resolved`, already bound at the head of the method | this conjunct |
| a non-enforcing write guard (M6) | YES — `vault_io.guard_mode()` is a per-call environment read taking no path | this conjunct |
| an uncontained destination (M1) | YES — the destination is `f"@{new_name}.md"` and `new_name` is in `updates` | **SPLIT BY DECLARED FIELD, and closed on both sides of the split** *(corrected 2026-09-26 with M7; the earlier answer delegated the whole row to `gate_write` and was wrong for every type that wall passes through)*. The only way that filename escapes is a `new_name` carrying a path separator. For the two types that DECLARE `name` and therefore derive `@{name}.md`, `gate_write` refuses it on the delta before any write (`path_hostile` for a person, the wider `COMPANY_TIER1_BRANCHES` class for a company, `obsidian_schemas/name_validation.py:_COMPANY_PATH_HOSTILE_RE:351`) — a different wall, and adding a containment conjunct here would PREEMPT it and degrade a `NameGateRefusal` carrying its `pattern` into a bare `ValueError`, so that half stays delegated. For every OTHER declared type the gate is a pass-through — `obsidian_schemas/name_gate.py:gate_write:319-344` returns the delta UNVALIDATED once `declared_type` is neither `person` nor `company` — so the residue is refused HERE, by the third disjunct (`"name" not in type(entity).model_fields`, M7), on the ground that `@{new_name}.md` is not that type's filename rule at all rather than on containment. Both halves together close the row for EVERY type; neither half rests on a premise about which types "cannot reach" this line |
| the source no longer exists (`FileNotFoundError`) | NO — the frame READ that file inside the lock microseconds earlier, so an absent source is a concurrent delete and not a knowable precondition | nobody; it is the door's own raise, and the write-then-move window entry in `## Edge Cases` owns it |
| `move_note`'s refusals (`NoteAlreadyExists`, symlinked source) | NO — both are filesystem state at move time | nobody, deliberately: pre-checking either here is exactly the check-then-act this document refuses elsewhere, and the syscall is the stronger answer |
| the alias write raising | NO — it happens after the move by construction | nobody; the half-failure residual is stated in the re-run table |

The rule that table carries, and the one a later clause is measured against: **`update_fields` refuses
a name change before its content write for every reason the door refuses its own PRECONDITIONS —
things knowable from this frame's arguments and environment — and for no reason that depends on
filesystem state at move time, which stays the syscall's.** A seventh refusal arm added to the door
later is placed by that sentence rather than by remembering this list.

**The COMPLEMENT of that rule — the half a rule that PARTITIONS a surface must also state**
*(2026-09-26, after the fourth spec-review round's blocking finding)*. The rule above says which of the
table's rows refuse EARLY. It said nothing about what the method LEAVES for the rows it answers NO, and
a rule that partitions a surface while stating the residual of only one half is how this class keeps
producing members: the finding that forced this paragraph is the THIRD time `update_fields`' rename
branch has been found committing its content write and only then discovering the door will not complete
the move — no provenance (round 2), a type declaring no `name` (M7), and now a destination ALREADY
OCCUPIED by a different note, with no race, no configuration and no exotic type. The first two were
closed by a disjunct because their causes are knowable in this frame; this one's is not, and
pre-checking it is the check-then-act the table refuses, so the table's **NO** stands — which makes the
RESIDUAL the whole of the answer rather than a footnote to it. Stated as one rule over the whole NO
half, derived from the table's own rows:

**For every row the table answers NO whose cause sits BEFORE or AT the move, `vault_io.write_note` at
`obsidian_schemas/repositories/base.py:BaseRepository.update_fields:490` has already COMMITTED, so the
method leaves the note carrying its NEW stored `name:` at its OLD filename, with no alias, with the
entity UN-RE-STAMPED at that old path, and with the door's own exception reaching the caller after a
successful write. The recovery is the same for every one of them and is NEVER a re-run of
`update_fields`: remove the cause, then call `repo.rename_note(entity, f"@{new_name}.md")` DIRECTLY —
the entity still carries the provenance the door resolves from, and a direct door call is safe by the
RE-RUN table's first row — and then re-bind the entity from the path the door returns, because the refused call never
reached its reload and the in-memory entity still holds the OLD `name`. A re-run of `update_fields`
with the same `updates` is SAFE and is not the repair: the trigger compares the caller's dict against
the note's frontmatter, which now already carries the new name, so `renaming` is False and the branch
never fires. For the ONE NO row whose cause sits AFTER the move — the alias write — the move DID
happen, and the re-run table's third row owns it and names its own one-field recovery.**

Row by row, so the rule is CHECKED against the table rather than asserted over it:

| the NO row | what `update_fields` leaves | where it is owned |
|---|---|---|
| the source no longer exists (`FileNotFoundError`) | a concurrent delete, and the two orderings differ: a delete landing BEFORE the content write makes `stat_stamp(target) != precondition` and `vault_io.write_note` refuses with `ExternalWriteConflict` (`obsidian_schemas/vault_io.py:write_note:685-698`), so NOTHING is committed; a delete landing after it leaves committed bytes at a path another actor removed, which is that actor's loss and not this method's | the write-then-move window entry in `## Edge Cases` |
| `move_note`'s `NoteAlreadyExists` — the destination is ALREADY OCCUPIED by a DIFFERENT note, with no race and every precondition satisfied | the residual the rule states: the new `name:` committed, the note still at its old filename, no alias, the entity still stamped there — and the destination note BYTE-IDENTICAL, since `os.link` failed before anything was written | the `## Edge Cases` occupied-destination entry, its own `## Risk Analysis` row, and Task 10's arm |
| `move_note`'s symlinked-source refusal (`WriteFailedError`) | the IDENTICAL residual by the identical route — `_resolve_write_target` answers the stamp, `source.exists()` follows the link and is True, and the door's refusal comes out of `move_note` (`obsidian_schemas/vault_io.py:move_note:736-740`) | the same entry; the two are ONE shape and are deliberately not listed apart |
| the alias write raising | moved, correctly stamped, one alias missing — the move DID happen, so this row is the rule's exception and not an instance of it | the re-run table's third row |

**The choice that rule makes, stated rather than left to silence, because the three available answers
differ observably.** The residual is **ACCEPTED**. The two alternatives are rejected for cited reasons:

- **Removing it by ORDERING — move first, write second — is UNAVAILABLE, not merely undesirable.** The
  door does not only move: it appends the alias through
  `update_frontmatter_field(moved, "aliases", aliases)` in the same call, and that write changes the
  file's `st_mtime_ns` and `st_size`. The content write's `precondition=stamp` comes from this frame's
  own `read_note` (`obsidian_schemas/repositories/base.py:BaseRepository.update_fields:449`), so after
  a move-then-alias the precondition MISMATCHES and `vault_io.write_note` refuses every SUCCESSFUL
  rename with `ExternalWriteConflict` (`obsidian_schemas/vault_io.py:write_note:685-698`) — the
  ordering that removes a rare residual manufactures a certain one. Splitting the door so the alias
  lands last would give `update_fields` a second composition rule over a door whose whole point is that
  it is one call, and AC-2's SIGNED `why` prescribes this order in its own words — *"so the order is
  write, then move, then rebind `file_path` to the door's return value before the reload"* — so
  reversing it is a re-sign, not a spec edit.
- **Removing it by PRE-CHECKING the destination** is the check-then-act the table already refuses, and
  refuses correctly: the check answers a question the filesystem may answer differently one syscall
  later, so the residual would survive at a smaller window while the package gained a SECOND authority
  on occupancy beside `os.link`. The syscall stays the authority, and Task 6 says so in the negative.

**And the residual is not the loss it first reads as — the comparison against today, made honestly.**
Today this same call SUCCEEDS: `obsidian_schemas/repositories/base.py:BaseRepository.update_fields:454-459`
appends the old stem to `aliases` in-lock, the write commits, the reload returns the entity. So today it
SILENTLY manufactures exactly the divergence `## Verified Diagnosis` 1 and AC-2(c) exist to end, and
after this item it manufactures the SAME divergence — in the one sub-population whose move cannot
complete — and says so out loud. The one thing lost against today is the alias, and in THIS residual the
old stem is still the note's own FILENAME: an `aliases` entry recording it is a reachability route the
file itself already provides, not a route that goes dark. Keeping today's in-lock append to preserve it
was considered and refused — it would put two writers on one `aliases` list one frame apart, which is
the question "Which `aliases` list wins" settles in the other direction, to buy a decoration.

**One precision about loudness, so the "every residual is detector-visible" claim is true where it is
made.** For a PERSON subject this residual IS a `stem_name_divergence` and Task 11's arm reports it.
`CompanyRepository` inherits `update_fields` and the door whole (it declares neither `save` nor
`get_file_path`) and `Company` DECLARES `name` (`obsidian_schemas/models.py:Company:128`), so M7's
disjunct passes and a company name change reaches the same residual — while the detector's arm is
guarded on `vf.entity_type == "person"` (Design §3). That company residual is therefore the ONE
FAILED-OPERATION residual this item leaves that the new detector cannot see, and it is named here rather
than implied; widening the detector to a second type is a declared non-action (`## Scope Boundary`), and
the guard's own reasoning is in Design §3. **One further detector-blind divergence exists and is NOT a
residual of a failed operation but a SIGNED trade, so it is named beside this one rather than counted
with it** *(2026-09-26, the next-level sweep behind M8)*: after this item a `save` of a `Book` or
`Meeting` entity whose deriving fields the caller changed lands in the PARSED file instead of forking a
second note, which is AC-1's promise and `## Verified Diagnosis` 1's whole point — and the resulting note
no longer recomputes to its own filename, outside the detector's person-only arm. It is accepted by
decision, stated in `## Scope Boundary` and `## Risk Analysis`, and is the conductor direction table's
business; `update_fields` is the path where the same shape IS refused, because it alone takes a caller's
DELTA and has the frame to judge it (M8, "the THIRD rule" below).

**And the SECOND rule, which is what the M1 row got wrong and is the one that generalises**
*(2026-09-26, threat-model M7)*. A row of that table may answer *"already refused earlier, by a
different wall"* — but a delegation is only as total as the wall's OWN DECLARED SCOPE, so:
**where a refusal is delegated to another wall, the delegation is checked against that wall's declared
scope, never against a premise about which callers or types reach the line; wherever the wall is
narrower than the delegating population, the residue is refused HERE.** The M1 row was answered by
delegating to `gate_write` and then bounding the residue with "`Book` and `Meeting` cannot reach it at
all — they declare no `name` field", a fact about `obsidian_schemas/models.py` that the trigger
consults nowhere: `gate_write` is type-scoped BY DESIGN
(`obsidian_schemas/name_gate.py:gate_write:319-344`, whose own comment reads *"a Book write is gated and
handed straight back"*), while the trigger reads the caller's dict against the note's frontmatter. The
member that fell through that gap is M7's, and it is closed by one disjunct rather than by a note:

**`update_fields` refuses a `name` delta on an entity whose own class does not DECLARE `name` — the third disjunct of the same pre-write refusal, `"name" not in type(entity).model_fields`, keyed on the DECLARED FIELD and never on a type name — because `f"@{new_name}.md"` is not that type's filename rule and `gate_write` hands a `name` delta straight back UNVALIDATED for every `declared_type` that is neither `person` nor `company`, so the rename branch is reachable only for a type that derives `@{name}.md` BY CONSTRUCTION rather than by the trigger's silence.**

Three things about that disjunct, so it is neither over- nor under-read. **It reads the CLASS, not the
instance** — `type(entity).model_fields`, which is the spelling `obsidian_schemas/writer.py:108`'s own
comment reserves ("Access model_fields from the class, not instance (Pydantic v2.11+ deprecation)") and
which `obsidian_schemas/parser.py:199` and `obsidian_schemas/writer.py:112` already use; a `hasattr`
or an `entity.model_fields` spelling would answer differently for a Book note that stores `aliases:` or
`name:` as a pydantic EXTRA, and the extra is precisely the case that must still refuse, because such a
note's filename rule is `_get_file_name` and `@{name}.md` is the wrong destination for it. **It REFUSES
rather than silently skipping the branch, and that is why it is written as the refusal's NEGATIVE
disjunct rather than as the trigger's positive conjunct.** M7's own `desc` states the requirement the
other way round — *"the trigger gains one conjunct … `"name" in type(entity).model_fields`"* — and
prescribes an oracle that RAISES (*"raises before the content write with that note BYTE-IDENTICAL"*);
the two are the same requirement from the two sides, and the refusal is the side that satisfies both.
Making the conjunct part of `renaming` itself would leave
the caller's ungated `name:` committed into the note with no exception at all — the same residual, minus
the loudness, and a `renaming` that silently answers False is exactly the unchecked reach premise this
mitigation exists to replace. So the disjunct lives in the refusal, where the frame has performed one
READ and the note is byte-identical afterwards, and `renaming` is left reading the caller's dict against
the note's frontmatter unchanged; by the time it is USED to call the door, the entity's class declares
`name`, which is the conjunct the `desc` names, established structurally rather than by silence. **It changes WHICH CALLS fire the rename branch and nothing else:** it adds
no containment conjunct (M1 stays the door's, so no `NameGateRefusal` is degraded), does not widen
`gate_write` to a third type, does not touch the Tier-1 tables, and does not move `save` or the five
body-writers, none of which has a rename branch.

**What the sweep behind that rule found, declared rather than left implicit** *(WI-226: the finding's
GENERATOR is "a bound on a population asserted from the models and enforced by a predicate that never
reads them", so the whole class is closed here and the next level named)*. MEMBERS — the same claim was
made at three sites and checked at none: this table's M1 row, the `f"@{new_name}.md"` paragraph above,
and Task 6's restatement of it. All three now rest on the disjunct. NEXT LEVEL, every other place this
item bounds a population by type reach, read one at a time: `BaseRepository.save`'s `@{name}.md`
derivation (`obsidian_schemas/repositories/base.py:BaseRepository.save:391-393`) is bounded by METHOD
OVERRIDE — `BookRepository.save` and `MeetingRepository.save` exist and Task 5 keeps both — which
dispatch makes structural, so it is not a member; ordering decision 3's in-memory alias assignment is
already keyed on the declared field and the alias reconciliation on the key the write introduced, which
are the two existing instances of the correct idiom and where M7's spelling comes from; the remaining
table rows 4–6 delegate to the SYSCALL on an argument about what is knowable in this frame, which is a
property of the frame and not of a type, so the second rule does not reach them; and the detector's
`vf.entity_type == "person"` guard (Design §3) is a declared narrowing over vault BYTES with its own
stated reasoning, not an unchecked reach premise. The sweep returned no fourth member.

**And the THIRD rule, which is what the precondition table and M7 between them still left open, and is
the one that makes this arm's coverage TYPE-GENERAL** *(2026-09-26, threat-model M8)*. Everything above
describes ONE obligation — refuse a RENAME the door cannot complete — and the whole predicate that
discharges it is `if renaming and (…)`. `renaming` is `"name" in updates and updates["name"] !=
frontmatter.get("name", "")` (`obsidian_schemas/repositories/base.py:BaseRepository.update_fields:454`),
so a delta carrying no `name` key never evaluates any of it. That is exactly correct for a `Person` or a
`Company`, whose filename rule IS `@{name}.md` — and exactly wrong for the other two types this item
newly lets into the frame, because their filename rule does not read `name` at all:
`obsidian_schemas/repositories/book.py:BookRepository._get_file_name:340-355` derives from
`entity.title` (`:346`) and `entity.author` (`:350-353`), and
`obsidian_schemas/repositories/meeting.py:MeetingRepository._get_file_name:208-231` from `entity.date`
(`:216`), `entity.topics[0]` (`:219-220`), `entity.attendees[:2]` (`:221-224`) and `entity.meeting_id`
(`:226`) — six DECLARED model fields (`obsidian_schemas/models.py:Book.title:160`, `:author:161`;
`obsidian_schemas/models.py:Meeting:260-263`). So the rule the arm is actually measured against is:

**The pre-write arm has TWO obligations and not one: it refuses a RENAME the door cannot complete — the
precondition class above — AND it refuses a WRITE that moves the entity type's OWN filename rule with no
rename to follow it; a version of this arm stated over only the first is bounded by `name`, which is
`Person`'s and `Company`'s filename rule and not the package's, and the residue it leaves is this
document's own type-general divergence predicate manufactured by the method that exists to end it.**

The second obligation is discharged by the arm's second clause, and this is the sentence the clause is
measured against:

**`update_fields` refuses, before its content write, a delta that moves the entity type's OWN filename rule when no rename will follow it — the same pre-write arm's second clause, `not renaming and derive is not None and derive(projected) != derive(entity)`, where `derive = getattr(self, "_get_file_name", None)` and `projected` is `entity.model_copy(update={k: v for k, v in updates.items() if k in type(entity).model_fields})` — keyed on the REPOSITORY'S OWN DECLARED FILENAME RULE and never on `name` or on a type name, and DELTA-RELATIVE (`derive(projected)` against `derive(entity)`, never against `file_path.name`) so that an ALREADY-divergent note stays writable for every delta that does not move its rule further.**

Five things about that clause, so it is neither over- nor under-read.

- **`derive` is `getattr(self, "_get_file_name", None)` and not a remembered type list, which is what
  makes it total rather than a third member of the same class.** `_get_file_name` is declared on exactly
  two repositories today — `obsidian_schemas/repositories/book.py:BookRepository._get_file_name:340` and
  `obsidian_schemas/repositories/meeting.py:MeetingRepository._get_file_name:208`; `BaseRepository`,
  `PersonRepository` and `CompanyRepository` declare none — so `derive` is `None` for the two types whose
  rule is `@{name}.md` and the clause is STRUCTURALLY inert for them, rather than inert by a premise
  about which types reach the line. That is the same DECLARED-CAPABILITY keying ordering decision 3 uses
  for `aliases` and M7 uses for `name`, applied to the filename rule itself, and it is why the clause
  survives the one change `## Scope Boundary` books as a separate item: if the `BaseRepository.save`
  collapse ever puts `_get_file_name` on the base class, `derive` starts answering for all four types and
  the `not renaming` conjunct — not a type list — is what keeps a `Person` name delta on the rename
  branch where it belongs.
- **`not renaming` is a CONJUNCT of this clause and not a coincidence.** A `name` delta on a type that
  derives `@{name}.md` is the rename branch's business: the branch moves the file and appends the old
  stem, which reconciles the rule rather than breaking it, so the clause must not reach it. A `name`
  delta on a type that does NOT declare `name` is M7's, one clause up. The two clauses therefore
  partition the delta space by whether a rename FOLLOWS the write, which is the property that actually
  matters, and neither of them is keyed on a type name.
- **The comparison is DELTA-RELATIVE, and that is load-bearing rather than defensive.** Comparing
  `derive(projected)` against `file_path.name` would refuse every write to an already-divergent Book or
  Meeting note — which is the live *"book-titled file holding a person note"* class and its siblings,
  the exact population this item exists to repair and which `docs/stem-divergence-live-baseline.md` §4
  books as a HAND repair. Such a note must stay writable for every delta that leaves its rule where it
  found it; what is refused is a delta that moves it FURTHER.
- **The projection is `model_copy(update=…)` restricted to DECLARED fields, and a raise out of it
  REFUSES.** `model_copy` preserves `__pydantic_private__` and so preserves the stamp (Design §1,
  "Survives `model_copy`"), and restricting the update to `type(entity).model_fields` keeps a caller's
  undeclared key out of the projection where it could not have moved the rule anyway. `model_copy` does
  NOT validate, so a delta supplying a non-string `title` or a non-list `topics` makes `derive(projected)`
  raise — compute `derive(entity)` FIRST, outside any `try`, and treat ANY exception out of
  `derive(projected)` as *the rule cannot be recomputed over this delta* and raise the same `ValueError`.
  Fail closed, the same direction M1 takes with an `OSError` out of its own resolve, and never a silent
  pass. `derive(entity)` needs no guard: the entity came through model validation, so its declared fields
  hold their declared types.
- **It ADDS NO CAPABILITY, and that is what makes it the cheap answer rather than the scope-expanding
  one.** It does not teach the door or `update_fields` a second filename rule for COMPOSING a
  destination — `_get_file_name` is recomputed only to COMPARE, never to build a path — it renames no
  Book or Meeting note, puts `_get_file_name` on no rename path, touches neither `gate_write` nor the
  Tier-1 tables, and moves neither `save`, the two `save` overrides nor the five body-writers.
  `## Scope Boundary` already declines to teach the door those two rules *"where refusal costs nothing
  anyone does today"* — this clause is that stated alternative made real instead of asserted.

**What the sweep behind THAT rule found, declared rather than left implicit** *(WI-226; the generator
here is one level up from M7's — not "a bound enforced by a predicate that never reads the models" but
**a guard keyed on the PERSON instance (`name`) of a predicate this document itself states
TYPE-GENERALLY**, which is the shape that produced M7 and M8 from the same paragraph two rounds apart).
MEMBERS — every guard this item ships, asked whether it is keyed on `name` or on the type's own rule:
the rename-branch trigger is `name`-keyed and M7 closes it on the DECLARED field; `update_fields`'
content write was `name`-keyed by omission and M8 closes it on the DECLARED RULE; the detector's
`vf.entity_type == "person"` arm (Design §3) is `name`-keyed by declaration, with its own stated
reasoning over vault BYTES, and stays a declared narrowing — it is the reason M8's residual would be
SILENT and is why M8 refuses rather than reports. NEXT LEVEL — the other eight write paths, asked the
same question one at a time. `BaseRepository.save` and the two `save` overrides DERIVE their own target
from the entity's current fields and have no rename to reconcile, so they cannot leave a delta
unresolved; what they leave instead is the seam's own declared trade — after this item a `save` of an
entity whose deriving fields the caller changed lands in the PARSED file rather than forking a second
note, which is AC-1's signed promise and `## Verified Diagnosis` 1's whole point, and refusing there
would refuse the criterion. That trade's own residual is named rather than implied: for a Book or
Meeting subject it is a divergence the detector's person-only arm cannot see, the same detector-blind
class as the COMPANY residual named in the loudness precision above, and it is the conductor direction
table's business rather than this door's. The five body-writers write BODY sections and carry no
frontmatter field delta at all, so no deriving field can move through them — structural, not asserted.
`rename_note` takes its destination from the CALLER by design, and the caller's rule is
`f"@{new_name}.md"`, which M7 makes true by construction. INTERSECTION — a type declaring BOTH `name`
and its own `_get_file_name` override exists nowhere today (`Person:79` and `Company:128` declare `name`
and override nothing; `Book:139` and `Meeting:247` override and declare no `name`), and under the two
clauses as written it is already total if one appears: its `name` delta sets `renaming` and goes to the
rename branch, its non-`name` deriving delta hits the second clause, and its non-deriving delta writes.
The sweep returned no member the two clauses leave open and one declared trade, stated above.

Three things fix that as the chosen answer rather than the door's raise leaking upward. The predicate
must be `renaming`, not `"name" in updates`: Prerequisites 7 records that the one consumer-visible
door is HAL9000's generic entity PATCH forwarding an arbitrary body *that may carry `name`*, and a
PATCH echoing the UNCHANGED name is the likely shape — refusing that would break a live consumer path
over an update that needs no move at all, which is why the test is against `frontmatter`'s stored value
and therefore has to sit inside the lock. The two alternatives are both worse and are rejected for
cited reasons. **Skipping the move** keeps today's leave-behind, which is the divergence
`## Verified Diagnosis` 1 and AC-2(c) exist to end — *"one shipped library behaviour deliberately
creates the divergence this item promises to end, so either it changes or the promise is false"* — and
it would additionally drop the alias today's block appends in-lock (`base.py:454-459`), so the
population would come out of this item strictly worse off than it went in. **Re-stamping `entity` from
the already-resolved `file_path`** is the tempting one-liner and it is the most dangerous option in the
set: `get_file_path` reads `_file_map`, one path per lowercased name filled last-wins over
`vault_path.glob` (`obsidian_schemas/repositories/base.py:BaseRepository.load:241-246`), so on a live
2-note collision (`docs/vault-shape-census.md:222`) it answers *which note won the walk* — and
laundering that guess into a provenance stamp would hand the door a note the caller never named and
MOVE it, alias it, and `_adopt` it. That is verbatim the harm AC-2(f)'s `why` calls *"the repair
machinery corrupting a note it was never asked about"*, manufactured by this item rather than merely
survived. Provenance has exactly two write sites — the parse and the door's own re-stamp — and
`update_fields` does not become a third.

What that leaves unchanged is the fallback's whole remaining population: an unstamped entity whose
update carries NO name change still resolves through `get_file_path` and still writes, exactly as
today. The fallback is alive for what it was kept for, and the one arm it cannot serve is the one arm
that refuses. The consumer audit measures the intersection at zero today (19 of 19 call sites on
LOADED entities, 0 reconstructions feeding a write), so this is one clause and not a redesign, and the
refusal is a `ValueError` for the same reason the door's own argument refusals are: it is the method
refusing its ARGUMENTS before any write is attempted, and `obsidian_schemas/errors.py:LoudFailError:37`
subclasses `ValueError` anyway, so no consumer's handler shape changes and no new leaf enters
`__all__`.

**Which `aliases` list wins, settled in one place** *(second spec-review round, non-blocking note 2)*.
The door's source is the IN-MEMORY entity — `aliases = list(getattr(entity, "aliases", []) or [])` —
where today's `update_fields` block reads the FILE's list in-lock (`base.py:456` is
`frontmatter.get("aliases", [])`). For a parsed entity of ANY type those are the same list: `Person`
declares the field (`obsidian_schemas/models.py:Person:80`) and `extra="allow"` puts a `Company`,
`Book` or `Meeting` note's own `aliases:` key into `model_extra`, which `getattr` resolves. They part
company in exactly one situation — a caller passing `aliases` in the SAME `update_fields` call as a
name change, because the write at `base.py:490` commits the caller's list while the entity still holds
the parsed one, and the door would then overwrite the caller's list with the stale one plus the old
stem. **`update_fields` reconciles on its own side and the door is not changed:** where the call is RENAMING
**and** the committed `updates` carried an `aliases` key, mirror the committed value onto the entity
(`entity.aliases = frontmatter["aliases"]`) before the door call, captured inside the lock with the
rest of the rename decision. **The `renaming` conjunct is part of the clause and not an optimization**
*(fourth spec-review round, non-blocking note 1)*: this mirror exists solely to stop the door
overwriting the caller's list with the parsed one, the door is the only consumer, and an ungated form
would give `repo.update_fields(person, {"aliases": […]})` with no name change a NEW in-place mutation
of the caller's object that today's `update_fields` never performs — benign, but a caller-visible
widening neither Prerequisites 7 nor `## Risk Analysis` discloses, bought for nothing. That is keyed on the KEY THIS WRITE INTRODUCED and never on a type name —
ordering decision 3's own rule, applied one frame over — and it mints nothing on a non-Person entity,
because the note itself now carries `aliases:` precisely because this call committed it, so the
`model_extra` value is a mirror of the file rather than an invented field. The alternative, having the
door read the moved file's list for itself, is refused by ordering decision 4's third reason: a
`parse_frontmatter` call in `rename_note`'s frame would make it a member of
`functions_parsing_then_writing`, which
`tests/test_concurrent_access.py:test_wi020_derivations_survive_the_routing:1080` pins by set equality
to `{write_markdown_file}`. A direct `rename_note` call is unaffected — its entity's list is the
file's.

### 3. The detector — `stem_name_divergence` in `lint_vault`

A READ-ONLY check, ERROR severity, `auto_fixable` left at its `False` default, emitted from
`scripts/lint_vault.py:check_structural` in the `structural` category. It goes in
`check_structural` and not in a new category on purpose: the five categories are a closed choice list
in three places (`scripts/lint_vault.py:CATEGORY_ORDER:1206`, `CATEGORY_LABELS:1207`, and `main`'s
`--category` choices), the property is structural, and a sixth category is surface this item does not
need.

Placement inside the loop is what buys AC-3(e) for free: `read_error` and `parse_error` files
`continue` above (`scripts/lint_vault.py:check_structural:340-359`), so an undecodable or unparsable
note never reaches the new arm, preserving WI-026's triage order. The arm sits after the
`TYPE_TO_MODEL` guard (`:387-388`):

```python
        if vf.entity_type == "person":
            stored = vf.frontmatter.get("name")
            stem = vf.stem[1:] if vf.stem.startswith("@") else vf.stem
            # A note with NO stored name belongs to `person_missing_name`, which
            # is auto-fixable and repairs in the OPPOSITE direction
            # (`--fix` writes the stem into the field, lint_vault.py:1040-1045).
            # Claiming it here would give one note an auto-fixable ERROR and a
            # never-fixable ERROR that the first one silently repairs away.
            if isinstance(stored, str) and stored.strip() and stem != stored:
                pattern = _gate_refusal_pattern(vf.frontmatter)
                marker = "" if pattern is None else (
                    f" [{NOT_RENAMEABLE_MARKER}: pattern={pattern}] — this "
                    f"divergence is not repaired by renaming the file to the "
                    f"stored name; repair the field")
                issues.append(LintIssue(
                    vf.path, "stem_name_divergence", Severity.ERROR,
                    f"Filename stem '{stem}' does not match stored name "
                    f"'{stored}'{marker}",
                    "structural",
                ))
```

- **RAW on both sides.** No `clean_person_name` on either half. The corpus holds the discriminator:
  `@Dave  Marrowyn Fennwick.md` carries the same double space in stem and stored name
  (`tests/fixture_vault.py:NOTES:246-254`, which declares `cleaned="Dave Marrowyn Fennwick"`), so raw
  calls it clean and a cleaned comparison wrongly reports it — AC-3(b)'s pinning arm.
- **The guard is `vf.entity_type == "person"` and NEVER `vf.is_at_prefixed`.** This is the arm's most
  mis-buildable line, and the live vault is what decides it: `docs/stem-divergence-live-baseline.md`
  row 8 (`:153`) is *"a **book-titled file** (no `@`, at the vault root) holding `type: person`"* — one
  of the eight divergences this item exists to repair, the single live MERGE, and one of the four
  booked hand repairs (`§4`). `check_structural` DOES reach such a file: the two `is_at_prefixed`
  tests sit only on `no_frontmatter` and `missing_type`
  (`scripts/lint_vault.py:check_structural:362-381`), both of which `continue`, and `person` is in
  `TYPE_TO_MODEL` so the guard at `:387-388` passes it through. AC-3(b)'s *"every non-`@`-prefixed
  note"* clause quantifies over THE OTHER CORPUS NOTES — and every non-`@` note in the frozen corpus
  declares a type other than `person` (meetings, books, watches, explores, gift-ideas, explorations),
  while every one of its `declared_type="person"` entries is
  `@`-prefixed (`tests/fixture_vault.py:NOTES:217-479`) — so that clause is satisfied by the
  `entity_type` guard and must NOT be generalized into one. A note whose stored `type:` is `person`
  is a person note wherever it lives; narrowing the guard to `is_at_prefixed and entity_type ==
  "person"` passes every corpus arm of AC-3 and silently drops row 8 from the report Dave runs, which
  is the fourth "Examples of done" scenario verbatim. Task 12 plants the shape and asserts it fires.
- **The comparison is case-SENSITIVE, and strips EXACTLY ONE leading `@`.** Both are free variables
  the frozen corpus is unanimous about and the live vault is not, so both are written into the arm
  rather than left to a builder's taste. (i) `stem != stored` is a plain Python compare: live baseline
  row 3 (`:148`) is a **case-only** divergence, and a `stem.lower() != stored.lower()` comparison
  passes all four corpus cells (each differs by more than case) while dropping that row — the same
  defect as the guard above, one dimension over. (ii) `vf.stem[1:] if vf.stem.startswith("@")` strips
  one `@`, never `lstrip("@")`, because the filename the library MINTS is `f"@{name}.md"` with exactly
  one (`obsidian_schemas/repositories/base.py:BaseRepository.save:391-393`): for `@@Foo.md` holding
  `name: "Foo"` the canonical target is `@Foo.md`, so the note IS divergent and will fork on its next
  `save` — `lstrip` yields `Foo`, calls it clean, and hides exactly the fork this check exists to
  see. (The sibling rule `person_missing_name` does use `lstrip("@")`
  (`scripts/lint_vault.py:1043`); that is its own repair direction and this item does not touch it.)
- **A non-string stored `name:` is SKIPPED, as a declared narrowing.** `isinstance(stored, str)` in
  the guard means a note carrying `name: [Foo, Bar]` or `name: 12345` is not reported. That is
  deliberate: the divergence class is "the stem disagrees with the stored name" and its repair is a
  rename or a field fix, neither of which is defined when the field is not a name — comparing
  `str(value)` would emit an ERROR whose declared repair no rename can perform. It is a NARROWING and
  therefore pinned rather than assumed: Task 12 plants a list-valued `name:` person note and asserts
  NO `stem_name_divergence` issue for it. What that plant also records is a gap in the TOOL, not in
  this item: `person_missing_name` fires only on a falsy-or-blank name
  (`scripts/lint_vault.py:check_completeness:435-446`, and only for `classify_person_tier(vf) ==
  "active"`), so a list-valued `name:` is reported by no check today. That is one line in the Build
  Log and a candidate for `lint_vault`'s own backlog — never a second arm bolted onto this check.
- **A BLANK or whitespace-only stored `name:` is SKIPPED, as the arm's third conjunct and a declared
  narrowing** *(added 2026-09-25 after the second spec-review round's blocking finding 2; §3a's sweep
  row)*. `stored.strip()` sits between the `isinstance` and the `!=` for the reason the code comment
  above states, and it is a FREE VARIABLE the frozen corpus is unanimous about — no
  `declared_type="person"` entry declares an empty or whitespace-only `name:` — so an implementation
  written as `isinstance(stored, str) and stem != stored` passes every corpus arm and every other plant.
  What it then does on the live vault is give one note two ERRORs whose repairs point in opposite
  directions: `person_missing_name` (auto-fixable, and `--fix` writes `fpath.stem.lstrip("@")` INTO the
  field — `scripts/lint_vault.py:1040-1045`) and this never-fixable one, the first silently repairing the
  second away. Pinned rather than assumed: Task 12's plant (vi) is a person note with a whitespace-only
  `name:` whose stem differs from it, asserted to produce NO `stem_name_divergence` issue — the second
  near-miss beside the list-valued one, so the check is not satisfiable by "report everything that is not
  an exact match". The hand-off is not total across tiers and the `## Edge Cases` entry says so:
  `person_missing_name` is gated to ACTIVE-tier notes
  (`scripts/lint_vault.py:check_completeness:429-446`), so a STUB-tier blank-name note is claimed by
  neither rule — which is a measured-at-zero population this item does not widen either check to reach,
  and is why plant (vi) asserts this check's SILENCE and never a partner issue's presence.
- **The marker fires on the DOOR predicate**, never on `NameValidator.validate_strict`:

  ```python
  def _gate_refusal_pattern(frontmatter: dict) -> Optional[str]:
      """The DOOR's answer for this note's OWN stored record, not the bare
      validator's. `gate_write` DERIVES `allow_phone_sentinel` from the payload
      (name_gate.py:355-358) where `validate_strict` defaults it False
      (name_validation.py:594) — they disagree on the one `sentinel_exempt`
      branch, which the census measures at 2 live person notes."""
      try:
          gate_write(frontmatter, declared_type=frontmatter.get("type"),
                     whole_record=True)
      except NameGateRefusal as exc:
          return exc.pattern
      return None
  ```

  `gate_write` and `NameGateRefusal` are already imported by the tool
  (`scripts/lint_vault.py:47-48`) and `NameGateRefusalRecord` already carries a `path` and a
  `pattern` (`scripts/lint_vault.py:NameGateRefusalRecord:865`) — the marker reuses that vocabulary
  rather than inventing one *(round 6 note 3)*. Worth one line for whoever reads
  `scripts/lint_vault.py:1009-1014`, which states that in the `--fix` DELTA path the phone-sentinel
  exemption is structurally unreachable: this call is the opposite case — it gates the note's WHOLE
  record, so `phones` IS present and the exemption IS reachable, which is exactly why the door and
  the bare validator part company here.
- **NO live row carries the marker today, and row 8 is not its live subject** — the marker's
  discriminating members are in the frozen corpus and the plants ONLY. The baseline's own entry figure
  is *"divergent rows the WRITE DOOR refuses (b3): 0 of 8"*
  (`docs/stem-divergence-live-baseline.md:124`) and every row's (b3) column reads `WRITTEN` (`:146-153`),
  so `_gate_refusal_pattern` returns `None` for all eight and every live row is reported UNMARKED.
  This corrects one sentence that reads the other way in two places — the baseline's own §2 closing
  prose (`:158-161`, *"the 'cannot be repaired by renaming' marker (AC-3(c)) has exactly one true live
  subject, row 8"*) and the conductor read-back note 2 that echoes it in `## Exploration Notes`. Row 8
  is not repairable by renaming because its DESTINATION IS OCCUPIED by a different note, which the
  marker does not encode and the direction table's (b2) column does — the marker fires on the door
  predicate and on nothing else. Neither the criteria nor the batteries depend on the mis-statement
  (AC-3(c) already says the corpus supplies the two marked members and the plant supplies the
  negative), and the baseline is a conductor precondition this item reads and never writes — so the
  correction lands here, where the exit attestation's reader will hit it: expect ZERO marked rows on
  the live report, and read row 8's MERGE direction off (b2), not off the marker.
- **The frame question, settled** *(round 5 note 1)*. The predicate above passes the note's STORED
  frontmatter while `write_markdown_file` gates `model_to_frontmatter(entity)` — the entity
  PROJECTION (`obsidian_schemas/writer.py:write_markdown_file:230`) — and for a Person the decisive
  call is earlier still, WI-021's rider at
  `obsidian_schemas/repositories/person.py:PersonRepository.save:1190-1191`. Neither changes an
  expected outcome anywhere in this item: the rider passes the same payload and the same branch, so
  the raised `pattern` is identical, and projection and stored record agree on all three inputs a
  refusal reads (`name` — the parser applies no cleaner; `phones`; `type`). The one class where they
  part is a note with **no stored `type:`**, and that class cannot reach this arm: the detector runs
  only for `vf.entity_type == "person"`, which `lint_vault` reads off the stored record
  (`scripts/lint_vault.py:read_vault:176`), and an untyped `@`-note is already claimed by
  `missing_type` (`scripts/lint_vault.py:check_structural:373-381`). The simplest true statement of
  the predicate is *"would `repo.save(<the entity parsed from this note>)` raise, and with what
  `pattern`"*, and the frontmatter form above is that question asked with the payload a linter has.
- **Never repaired.** `auto_fixable=False` keeps it out of `apply_fixes` by construction, so
  WI-026's four-bucket partition still sums to the auto-fixable issue count
  (`scripts/lint_vault.py:FixOutcome:926-939`) and the new issue is counted only by the summary's
  non-fixable figures (`scripts/lint_vault.py:print_summary:1218-1221`). It also keeps the new check
  out of `auto_fixable_emitter_checks`, which
  `tests/test_lint_vault_fix_rules.py:1703` pins by set equality against the baseline's rows.

#### 3a. The GENERATOR behind the planted discriminators, closed as a class, then swept one level down

Three gate rounds have now produced the same finding in three different clothes, and the fourth
member was found by the spec review rather than by the batteries. The generator, stated once:

> **A criterion whose population is the FROZEN corpus certifies any implementation whose predicate is
> NARROWER than the definition along any dimension the corpus's own members are UNANIMOUS about.** The
> corpus is a museum of corruption shapes, not a cross-product: 22 person notes that happen to agree
> on a dozen incidental properties. Every property they agree on is a free variable a builder may
> read into the guard, pass every cell, and ship a detector or a seam that is wrong in the live vault
> — which is where both actually run.

Its members so far, each closed the same way (the discriminating member is PLANTED in the
materialized temp copy, never added to `tests/fixtures/vault/` — `CORPUS_DIGEST`): the door-predicate
spelling, `validate_strict` vs `gate_write` (round 4 — the sentinel-exempt phone stub); Book and
Meeting divergence, where every corpus Book/Meeting agrees with its own derived filename (the
red-team's round 1 — the two colliding groups); and now the detector's own guard and comparison.

**The class-level rule, which is what makes the next member somebody's assertion rather than the next
round's finding:** every free variable of the detector's arm and of AC-1's subject derivation on which
the frozen corpus is UNANIMOUS is closed by a PLANTED member, pinned BOTH ways — one plant the
predicate must claim and one near-miss it must not — and the list is DERIVED by reading the
predicate's own text for the properties it tests, never remembered from this table. The sweep below is
that reading, run 2026-09-25 over the arm in §3 and the subject derivation in AC-1. It is a FLOOR at a
date, not a total; anything a later reading adds is named in the Build Log and planted, never quietly
dropped.

| free variable of the predicate | the corpus's members | live evidence | disposition |
|---|---|---|---|
| the TYPE guard — `entity_type` vs `is_at_prefixed` | unanimous: all 22 person notes are `@`-prefixed | baseline row 8, a non-`@` file holding `type: person` | PLANT (Task 12), fires |
| letter CASE in the comparison | unanimous: no case-only divergence; all four differ by more than case | baseline row 3, case-only | PLANT (Task 12), fires; the door's own case-only arm is AC-2(h) / Task 10 |
| how many leading `@` are stripped | unanimous: every stem has exactly one | none measured | PLANT (Task 12): `@@<name>.md` holding `name: <name>` fires |
| the stored `name:`'s TYPE | unanimous: every declared `name:` is a string | none measured | PLANT (Task 12) as a NEAR-MISS: a list-valued `name:` is NOT reported (declared narrowing above) |
| whether the stored `name:` is BLANK — the arm's `stored.strip()` conjunct | unanimous: no `declared_type="person"` entry declares an empty or whitespace-only `name:` | none measured | PLANT (Task 12) as a SECOND NEAR-MISS: a person note with a whitespace-only `name:` whose stem differs from it is NOT reported (the `person_missing_name` hand-off below) |
| whitespace inside either side | NOT unanimous — `@Dave  Marrowyn Fennwick.md` is the discriminator | n/a | already pinned, AC-3(b) |
| the `!=`'s OPERANDS — whether either side is normalized before the compare (a SUB-CELL of the `!=`, not a sixth conjunct) | unanimous: no `declared_type="person"` entry declares a `name:` carrying LEADING or TRAILING whitespace | none measured | PLANT (Task 12): a person note whose stem is `<n>` and whose stored `name:` is the quoted `"  <n>  "` FIRES, which refuses `stem != stored.strip()` and `stem.strip() != stored` |
| directory DEPTH | unanimous: the corpus is one flat directory | baseline §4 books two untyped notes under `Notes` and `Resources` | PLANT (Task 12): a divergent person note in a sub-directory fires, since `read_vault` rglobs and `vf.stem` is depth-free (`scripts/lint_vault.py:read_vault:123`, `:155`) |
| the note's own decodability / parseability | NOT unanimous — the corpus carries all three specimens | n/a | already pinned, AC-3(e) |
| the ENTITY TYPE whose filename rule is recomputed (AC-1) | unanimous: no divergent Book or Meeting | none measured | already planted, AC-1's two colliding groups |
| whether the DOOR writes the stored name (AC-1, AC-3(c)) | unanimous under both spellings | `pure_digit` measured at 2 live notes, neither divergent | already planted, the sentinel-exempt subject |

**The `stored.strip()` row is the class's FOURTH member and the second one this sweep found only after a
reviewer read the arm** *(second spec-review round's blocking finding 2, 2026-09-25)*. It is here for
exactly the reason the rule above says the list is DERIVED by reading the predicate's own text: the arm
is `isinstance(stored, str) and stored.strip() and stem != stored` — five tests with the guard and the
`@`-strip, and the sweep had planted four of them. An implementation written without that conjunct
passes all four AC-3(a) cells, all of AC-3(b) and every other plant in this table, and then, on the
live vault, reports every blank-name ACTIVE person note as `stem_name_divergence` on top of its
`person_missing_name` — the auto-fixable ERROR silently repairing away the never-fixable one, which is
the interaction Design §3's own comment and the `## Edge Cases` entry argue against and which had a
**Decision** and a **Reasoning** and no test. "The live stake is measured at zero" is not the
discriminator, and cannot be: the double-`@` and stored-value-TYPE rows both carry *none measured* and
are planted anyway. Note that the interaction bites in BOTH tiers and differently, which is why the
plant asserts silence rather than a particular partner issue: for an ACTIVE-tier note the two ERRORs
collide (`scripts/lint_vault.py:check_completeness:429-446` gates `person_missing_name` to
`classify_person_tier(vf) == "active"`, and `--fix` writes `fpath.stem.lstrip("@")` into the field at
`scripts/lint_vault.py:1040-1045`), while for a STUB-tier note `person_missing_name` never fires at all
and the dropped conjunct would leave a lone, permanent divergence ERROR on a note whose only defect is
an empty field.

**The `!=`'s operand row is the class's FIFTH member, and it is the sweep going one level DOWN rather
than one member along** *(third spec-review round, non-blocking note 1, closed here rather than
deferred)*. The four rows above are free variables of four DIFFERENT conjuncts; this one is a free
variable of a conjunct the sweep had already read — the `!=` itself — and the reviewer found it by
asking not "which test is missing" but "what is unconstrained INSIDE a test the sweep already named".
The arm is `stem != stored`, raw on both sides, and an implementation written `stem != stored.strip()`
— a plausible slip once `.strip()` sits in the conjunct immediately to its left — passes all four
AC-3(a) cells, passes AC-3(b)'s `@Dave  Marrowyn Fennwick.md` discriminator (whose double space is
INNER, which `.strip()` does not touch) and passes all six earlier plants, while silently dropping a
live person note whose stored `name:` is its stem plus stray leading or trailing whitespace — a note
that is genuinely divergent, because `save` would mint `@  <n>  .md` for it
(`obsidian_schemas/repositories/base.py:BaseRepository.save:391-393`), which is a fork. So it is
planted, positively (the note FIRES), and the plant discriminates both directions of the slip at once,
since `stem.strip() != stored` drops it too. The live population is measured at zero and that is
deliberately NOT the discriminator: the double-`@` and stored-value-TYPE rows both read *none measured*
and are planted anyway, for the reason the class-level rule gives.

Rows carrying no `(AC-…)` tag are the DETECTOR's arm. A dimension is not planted twice where it is not
a free variable of the other consumer: the `@` prefix, letter case and the `@`-strip are read only by
the detector, while the SEAM never reads a stem at all — it reads the stamp — so a non-`@` divergent
person note needs no AC-1 plant. Its `save` cell behaves exactly as the corpus `Quillam` members' do
(canonical filename occupied by a different note, today's silent overwrite), which AC-1's subject
derivation already reaches.

**The next level of the ladder, swept and DECLARED.** Members → dimensions → intersections →
SUB-CELLS, and this round walked the last two rungs. (i) The INTERSECTION cells are a non-`@` note
that is ALSO case-only divergent, a sub-directory note that is also gate-refused, and so on. They are
deliberately NOT planted, and the reason is a property rather than a budget: the arm is a conjunction
of INDEPENDENT tests — one guard on `entity_type`, one strip, one `isinstance`, one `stored.strip()`,
one `!=`, one marker call on the note's own record — with no branch in which any of them reads
another's input, so a cell that passes each dimension singly cannot fail their intersection.
(`stored.strip()` is named in that enumeration deliberately: it was the conjunct the previous
statement of this declaration omitted, and an unnamed conjunct is precisely how this class generates
its next member.) (ii) The SUB-CELLS are the free variables INSIDE each of those six tests, which is
the rung the `!=`-operand row above came from, and the sweep was run over all six rather than over the
one a reviewer named: the `entity_type` guard compares a stored string to a literal and normalizes
neither side (its own free variable, CASE of the stored `type:` value, is not this check's to decide —
`lint_vault` reads `vf.entity_type` off the stored record at `scripts/lint_vault.py:read_vault:176`
and every other check keys on the same value, so an arm that lower-cased it here would disagree with
the tool around it and is refused for that reason, not planted); the `@`-strip's count is the
double-`@` row; `isinstance`'s type is the stored-value-TYPE row; `stored.strip()`'s emptiness test is
the blank-`name:` row; the `!=`'s operands are the new row; and the marker call's own free variable —
which predicate answers, `gate_write` or `validate_strict`, and with which payload — is the
door-predicate member closed in round 4 and re-argued in §3's "frame question". That is the
declaration: after this round every one of the six conjuncts has both its dimension and its operands
planted or dispositioned in writing, and the only shape that would invalidate the intersection
argument is a builder who FUSES two tests into one expression (a normalizing comparison that also
strips, a guard that also tests the stem's shape). The arm as specified in §3 has no such expression,
AC-3's set-equality assertions over the whole materialization are what would catch one, and a later
reading that finds a seventh member names it in the Build Log and plants it.

### 4. The containment wall — one derivation, two buckets (AC-5)

A new derivation in `tests/derivations.py` (the ONLY module in this repo permitted to name `ast` —
see `## Wall Membership`), and a new seed for the machinery that is already there. Not a second
scanner.

```python
class WriteTargetSite(NamedTuple):
    module: str
    qualname: str
    lineno: int          # the write call's line
    bucket: Optional[str]    # "leaf" | "seam" | None == FAILS the wall

SEAM_FUNCTION = "_resolve_write_target"

def path_taking_writer_names(writer_path: Path) -> frozenset:
    """The writer module's PATH-TAKING PUBLIC WRITERS, derived and never listed:
    every module-level `def` in writer.py whose FIRST parameter is `file_path`
    and whose own body contains a write call. Today: write_markdown_file,
    update_frontmatter_field, update_frontmatter_fields, roundtrip_file."""

def write_target_buckets(files, writer_path) -> list[WriteTargetSite]:
    """Every mutation site under the given files, classified."""

def door_calls_inside_note_lock(files, writer_path) -> list[WriteTargetSite]:
    """Ordering decision 5's structural half (NOT part of AC-5's two buckets):
    every call to `move_note`, to a member of `path_taking_writer_names`, or to
    a repository method that itself calls `move_note` — the last clause DERIVED
    from `functions_calling(files, "move_note")` and never named, so this item's
    own door and any future mover enlist by themselves — that is lexically
    NESTED inside a `with` statement whose items mention `note_lock`. That third
    clause is what makes `update_fields`' `self.rename_note(...)` placement
    checkable rather than promised. EMPTY over PACKAGE_ROOT, asserted in
    Task 10. The single-path
    doors `write_note` and `create_note` are deliberately NOT collected —
    `write_markdown_file` must call them inside its own lock (writer.py:317,
    :319; `vault_io._require_lock` demands it), so collecting them would make
    the scan RED against shipped code."""
```

**The enumeration** is the union of two predicates, and it is WIDER than AC-5's floor by exactly the
amount round 5's note 3 asked for: (i) the shipped `tests/derivations.py:_is_write_call:286` —
attribute calls whose attr is in `{"write_text", "write_bytes"} | DOOR_NAMES`
(`tests/derivations.py:DOOR_NAMES:47`) — reused rather than re-spelled, so a tenth path built on a
bare `Path.write_text` or on `create_note` is enumerated too; plus (ii) bare-name calls to a member
of `path_taking_writer_names`, which is what reaches `write_markdown_file` and the three sibling
leaves this item's own door writes through. `vault_io.py`'s own terminal writes (`os.replace`,
`os.unlink` at `vault_io.py:537`, `:586`, `:765`, `:776`) are NOT enumerated — they are reached by
neither predicate, which is the disposition the data-premise audit's Domain A hunt recorded; a
builder who widens the enumeration to raw filesystem calls will redden the door the item ships
through, and must not.

**Bucket (a) PATH-TAKING LEAF** — the enclosing function is a MODULE-LEVEL function (no `self`
parameter) and every name in the write call's first positional argument is tainted by that
function's own FIRST PARAMETER. Stated over module-level functions rather than "a parameter" in
general, because every repository method has `entity` as a parameter and a bucket keyed on bare
parameter-taint would admit `file_path = self.vault_path / f"@{entity.name}.md"` — the exact shape
the wall exists to refuse. Today's members are `writer.py`'s four functions (four FUNCTIONS, not four
calls: `write_markdown_file` holds both `writer.py:317` and `:319`), and a future path-taking leaf
written as a METHOD fails loud and is someone's decision rather than a silent pass.

**The bucket is narrowed to the FIRST parameter, and the second-parameter case is a DELIBERATE loud
refusal, not an unconsidered gap** *(second spec-review round, non-blocking note 4)*. All four current
leaves take the path first and by that name — `write_markdown_file(file_path, entity=…, …)`,
`update_frontmatter_field(file_path, field_name, field_value)`,
`update_frontmatter_fields(file_path, updates)`, `roundtrip_file(file_path)`
(`obsidian_schemas/writer.py:write_markdown_file:160-161`, `:update_frontmatter_field:333-334`,
`:update_frontmatter_fields:405-406`, `:roundtrip_file:463`) — so nothing is red today. A future leaf
taking its path as a SECOND parameter gets the same disposition as one written as a method: bucket
`None`, the scan RED, naming the file, the function and the line. That is the wall working, and the
resolution is a human decision made in the open — widen `path_taking_writer_names`' predicate and
re-derive, or move the path to the first parameter — never a silent pass. The taint direction is stated
once and applies to both halves: a leaf's path comes from its FIRST parameter, and a write's path is its
FIRST POSITIONAL argument, so the two ends of the rule agree and neither is a special case of the
other.

**Bucket (b) SEAM-ROUTED** — a DATA-FLOW property, never call-presence *(the red-team's round-1
finding)*, and ordering-aware, which is what closes the monotone-taint escape *(round 6 note 1)*:

> Seed the taint set on the name bound to a call whose callee attribute is `_resolve_write_target`,
> propagate to a fixpoint over `ast.Assign` targets **and `with … as` bindings** exactly as
> `tests/derivations.py:_taints_a_write:361-409` does, and sink at the write call's FIRST POSITIONAL
> argument only. Then, additionally: every `ast.Assign` that binds a tainted name, lies between the
> seeding assignment and that write call by position, and whose VALUE mentions no tainted name, must
> be nested inside an `ast.If` whose `test` mentions that same name. Otherwise the site is not
> seam-routed.

Propagation reaches `ast.Name` targets and the `ast.Name` elements of a `Tuple`/`List` target — the
shape `tests/derivations.py:_assign_targets_name:928` already encodes — and NEVER the base of an
`ast.Attribute` or `ast.Subscript` target: `entity._source_path = moved` binds no local name, and
propagating through it would taint `entity` itself and hand every later expression mentioning the
parameter a taint it did not earn. This is one place the new seed must NOT copy `_taints_a_write`'s
`_names_in(target)` verbatim, and it is the door's own body that makes the difference observable.

The `with … as` hop is not optional: `write_markdown_file` writes to `resolved`, bound by
`with vault_io.note_lock(file_path) as resolved` (`obsidian_schemas/writer.py:258`), so without it
the archetypal bucket-(a) member fails and the wall is RED against shipped code. The rebinding clause
is what the fold needed and did not have: `_taints_a_write` propagates by ADDING names
(`tests/derivations.py:389-401`) and retains no branch structure, so

```python
file_path = self._resolve_write_target(entity)   # seeds file_path
filename  = self._get_file_name(entity)
file_path = self.vault_path / filename           # UNCONDITIONAL — resolved value discarded
write_markdown_file(file_path, ...)              # still "tainted" under a pure fixpoint
```

passes a monotone rule and routes nothing — a one-line insertion into today's `BookRepository.save`.
Under the clause above it FAILS (the third line binds a tainted name, sits between seed and sink, its
value mentions no tainted name, and it is not inside an `if` testing `file_path`), while AC-5's
load-bearing fifth ACCEPTED near-miss — the documented fallback arm, `if file_path is None:
file_path = self.get_file_path(name)` — PASSES, because its rebinding is inside an `If` whose test
names it. Both of the shipped fallback spellings are legal by construction: the `or` form
(`file_path = resolved or derived`) is one Assign whose value mentions a tainted name, and the
guarded form is the near-miss itself. That is the property that lets the fallback asymmetry survive
the wall rather than being quietly removed by it.

**"First positional" is the total rule** *(round 6 note 2)*, and it is correct at every door:
`write_markdown_file(file_path, …)` (`obsidian_schemas/writer.py:write_markdown_file:160`),
`write_note(path, text, …)` (`obsidian_schemas/vault_io.py:write_note:670`),
`create_note(path, text)` (`obsidian_schemas/vault_io.py:create_note:701`), and
`move_note(src, dest)` (`obsidian_schemas/vault_io.py:move_note:721`) — whose first positional is
`src`, the note being moved, which is exactly the one the seam must resolve. A rule reading "all path
arguments" would refuse this item's own door, whose `dest` is legitimately caller-derived. A write
call with NO positional argument fails the scan by the same rule rather than being skipped.

**The expected classification after the build**, asserted as a SET equality and not a count:

- bucket "leaf" — `write_markdown_file`, `update_frontmatter_field`, `update_frontmatter_fields`,
  `roundtrip_file` (all `obsidian_schemas/writer.py`).
- bucket "seam" — `BaseRepository.save`, `BaseRepository.update_fields`, `BaseRepository.rename_note`,
  `PersonRepository.append_to_timeline`, `PersonRepository.append_to_body_section`,
  `PersonRepository.add_to_discuss_item`, `PersonRepository.update_to_discuss_item`,
  `PersonRepository.remove_to_discuss_item`, `BookRepository.save`, `MeetingRepository.save`.
- bucket `None` — empty.

AC-1 derives its PATH set from that same "seam" set (its invocation table's keys, plus
`BaseRepository.rename_note`, must EQUAL it), so a tenth path joins both batteries by construction
instead of quietly reopening the round-2 finding.

### 4a. The privacy wall on the committed live-vault artifact — a TOKEN CLASS, never a REGION (M5)

AC-4's shape check grades a conductor-committed artifact measured off Dave's live vault
(`docs/stem-divergence-live-baseline.md`), and the criterion's own `desc` promises that *"no absolute
path and no note filename leaks the privacy wall"*. Two conjuncts carry that promise and both are
WHOLE-FILE.

- **The absolute-path half** scans the whole file for any member of
  `tests/test_vault_path_required.py:FORBIDDEN_DEFAULT_PATTERNS:278` — today
  `["expanduser", "Path.home()", "/Users/"]` — IMPORTED and never re-spelled, or the assertion becomes
  its own offender. This fold does not touch it.
- **The filename half** is the `.md`-token rule, and it is where the threat model's M5 lands. AC-4's `.md`-token privacy rule is TOTAL over the whole committed artifact — every `.md` token anywhere in `docs/stem-divergence-live-baseline.md`, inside a fenced code block exactly as much as outside one, must resolve to a path that EXISTS in this repo, or be the declared template literal `@{name}.md`, or CONTAIN a `*` and so be a glob rather than a filename; the exemption is that TOKEN CLASS and never a REGION, because a fenced block is precisely where the exit attestation's pasted output lands and §5's second re-run command is `scripts/lint_vault.py --vault "$VAULT" --report`, which reports issues PER PATH and therefore names note filenames by construction.

**Why the region form was wrong rather than merely wide** *(threat model round 3, M5 — this supersedes
the fenced-code clause the SECOND spec-review round folded into Task 13)*. The region the earlier form
excluded is exactly the region a leak would land in. The artifact already carries two fences of verbatim
command output (`docs/stem-divergence-live-baseline.md:98-115`) because that is how a conductor records
a re-run, and the close-out re-runs two commands, the second of which names paths. Nothing else in the
build catches a bare relative filename: `@Someone Real.md` contains no member of
`FORBIDDEN_DEFAULT_PATTERNS`. And the artifact declares the stronger property about itself at
`docs/stem-divergence-live-baseline.md:15` — *"No absolute path appears anywhere in this file, so a
whole-file privacy scan is legal against it."* A precondition that declares a whole-file scan legal,
graded by a check that no longer performs one, is the wall verified where the reader looked and false
where it also runs.

**The token class is green against the artifact as committed, verified against its bytes and not
assumed.** The false RED the region exclusion was reaching for is `sorted(V.rglob('*.md'))`
(`docs/stem-divergence-live-baseline.md:36`) — a GLOB, not a filename. Every `.md` token in the file
today is one of: `docs/filename-name-divergence-repair.md` (`:4`), `docs/vault-shape-census.md` (`:5`,
`:22`), `docs/lint-vault-live-baseline.md` (`:6`) — four tokens naming three paths that exist in this
repo — `*.md` (`:36`, the glob) and `@{name}.md` three times (`:76` inside the script, `:126` and `:153`
in prose), already exempt as the declared template literal. So the token-class exemption costs one
clause on the same task, keeps the rule total over every real filename anywhere in the file, and is
GREEN today.

**Two mechanical consequences a builder needs** *(they are prescribed in Task 13 and repeated here
because they decide whether the rule can see its own exemption)*. First, tokenize with a character class
that INCLUDES `*` — `re.findall(r"[\w@{}*./+-]+\.md", text)` is the shape — because a class without it
captures `.md` with the `*` left outside the token and the exemption becomes unreachable. Second, a
leaked filename containing a space is captured as its trailing segment only (`@Someone Real.md` yields
`Real.md`), which resolves to nothing in this repo and so still FIRES; the wall catches it, it merely
names a shorter token, and widening the class to spaces to pretty that up would start swallowing prose.

**There is no fence toggle left in the privacy path, and that is the point.** The region form needed one,
and needed a guard on it — Task 13 previously asked the check to *"assert the exclusion is non-vacuous
(at least one line was skipped)"* — but "at least one line was skipped" is satisfied by a toggle stuck
OPEN, which is the whole-file exemption the guard claimed to prevent. The token-class rule has no toggle
and needs no guard. The artifact's OTHER readers are unaffected because they are scoped to their own
`##` section: §1's and §2's table readers never see §0's pipe-bearing script and stdout, so removing the
fence detector removes nothing they depended on. The privacy scan is the only whole-file reader in the
module and it needs no fence awareness at all.

### 5. Integration points

| what changes | file:symbol | delta |
|---|---|---|
| the stamp's declaration | `obsidian_schemas/models.py:BaseEntity:31` | one `PrivateAttr`, one import |
| the stamp's one write | `obsidian_schemas/parser.py:parse_markdown_file:244` | two lines |
| the resolution function | `obsidian_schemas/repositories/base.py:BaseRepository.get_file_path:354` (placed beside) | new private method |
| the door | `obsidian_schemas/repositories/base.py` | new public method `rename_note`, including its M1 destination containment and its M6 `vault_io.guard_mode()` fail-closed refusal — one read of an existing `vault_io` function, no new import and no `os.environ` access |
| `save` | `obsidian_schemas/repositories/base.py:BaseRepository.save:391-393`, `:411` | three lines, plus the INFO line naming the file actually written; `overwrite`/gate/adopt untouched |
| `update_fields` | `obsidian_schemas/repositories/base.py:BaseRepository.update_fields:438`, `:454-459`, `:490-495` | seam at the top, binding `resolved`; a `ValueError` inside the lock when the update changes the name and the door's preconditions do not hold — `resolved is None`, or `vault_io.guard_mode() != "enforce"` (M6), or `"name" not in type(entity).model_fields` (M7) — raised before anything is gated or written; the alias-append block becomes the door call — placed OUTSIDE the `note_lock` block, after the write commits, before the reload — with the committed `aliases` value mirrored onto the entity where the caller supplied one |
| the five body-writers | `obsidian_schemas/repositories/person.py` (`:1403`, `:1522`, `:1653`, `:1719`, `:1793`) | one line each, `ValueError` arms unchanged |
| the two `save` overrides | `obsidian_schemas/repositories/book.py:BookRepository.save:167`, `obsidian_schemas/repositories/meeting.py:MeetingRepository.save:189` | three lines each, plus each override's INFO line |
| the detector | `scripts/lint_vault.py:check_structural:328`, plus one module constant and one helper | read-only arm |
| the wall's derivation | `tests/derivations.py` | one NamedTuple, three functions, one new seed, one lock-nesting scan |

**The diff size, stated honestly, because two earlier passages under-count it.** `## Exploration
Notes` says "eight more one-line edits" ("One target function, not one read site") and its
blast-radius bullet says "Nine one-line call-site edits"; that is the shape of the CALL, not of the
diff. Per site it is the three-line CREATE-fallback shape at `save` and
the two overrides (resolve, conditional WARNING, `resolved or derived`) and the three-line
REFUSE-fallback shape at `update_fields` and each of the five body-writers (resolve, guarded rebind,
today's `ValueError`) — the two shapes written out above. Nine SITES, ~3 lines each, one new helper,
one new door, no public signature change. The count that matters downstream is the SITE count (AC-1's
path set and AC-5's seam bucket both quantify over it); the line count is stated only so a builder
does not read "one line" as a constraint on the shape.

**One CAPABILITY WIDENING falls out of Task 3's reorder and is declared here rather than left to read
as a side effect** *(fourth spec-review round, non-blocking note 2)*. Today `update_fields` is
unusable on a `Book` or a `Meeting`: it opens `name = getattr(entity, "name", "")`, which is `""` for
both, and `get_file_path("")` answers `None` — `BookRepository.get_file_path:326-338` keys on
`title.lower().strip()` — so the method raises ABOVE the lock
(`obsidian_schemas/repositories/base.py:BaseRepository.update_fields:437-441`) and the frame never
runs. Task 3's `resolved`-first shape binds the file from the STAMP, so after this item the whole frame
runs for those two types and `repo.update_fields(<a stamped book>, {"status": "read"})` SUCCEEDS —
Task 10's M7 arm asserts exactly that as its ACCEPTED half. That is INTENDED and is the correct
direction: the seam's whole claim is that a write of an entity the library parsed lands in the note it
was parsed from, and a method that refuses two of the four entity types because its name-keyed opener
cannot see them is the name binding, not a boundary. Its blast radius is measured at zero — the audit
records 0 consumer call sites on `BookRepository.save`/`MeetingRepository.save` and the generic PATCH
as the only consumer route to those two repositories
(`docs/wi-029-consumer-audit.md:134-140`, `:371-376`) — and what it does NOT widen is stated by the
DELTA and not by the branch, which is this paragraph's own 2026-09-26 correction *(threat model round 6,
M8; the earlier wording read "the one thing it does NOT widen is the rename branch, which M7 refuses for
both types", and that bound is `name`-shaped while neither of those two types' filename rule reads
`name` —
`obsidian_schemas/repositories/book.py:BookRepository._get_file_name:340-355` derives from `title` and
`author`, `obsidian_schemas/repositories/meeting.py:MeetingRepository._get_file_name:208-231` from
`date`, `topics`, `attendees` and `meeting_id` — so the sentence was true of the rename branch and
silent about the six declared fields that actually compose those filenames)*. Stated correctly, the
widening admits exactly the deltas that leave the type's own filename rule where they found it: a
`{"status": …}` or `{"description": …}` on a Book, a `{"tags": …}` on a Meeting, which is the ACCEPTED
half Task 10's M7 arm already asserts. A delta carrying `name` is refused by M7's clause, and a delta
touching any of those six DERIVING fields is refused by M8's — the second clause of the same pre-write
arm (Design §2, "the THIRD rule"), because such a write commits silently, moves nothing, records no
alias for the stem the note is leaving behind and raises nothing, manufacturing this document's own
type-general divergence predicate on the one externally-supplied route the item names. No criterion
quantifies over this: AC-1's path set restricts a Book and Meeting subject to that type's `save`
override, so the widening is additional capability outside every signed promise rather than a change to
one — and the two refusals narrow it back to the deltas that were safe to admit, rather than adding a
behaviour the signed set did not contemplate.

**Read-side sites that share the root cause and are deliberately NOT in the write seam**, named so a
builder does not route them: `PersonRepository._get_body_content`
(`obsidian_schemas/repositories/person.py:PersonRepository._get_body_content:1590`), which resolves
by name and returns `None` on a miss — it reads the wrong note rather than writing it; and
`PersonRepository.create_stub`'s lost-create-race recovery
(`obsidian_schemas/repositories/person.py:PersonRepository.create_stub:1353`), which builds
`self.vault_path / f"@{clean_name}.md"`, `_load_file`s it and `_adopt`s the result — and is CORRECT
as written, because that path is exactly the one `save` just collided on, so the recovered entity's
stamp and its `_file_map` entry both name the winner's real file *(the data-premise audit's Domain B
hunt; two read-side sites, not one)*.

### 6. Configuration

**This item INTRODUCES no setting** — no threshold, no toggle, no env var of its own, no feature flag.
The seam is unconditional: a flag would make the package buildable two ways and would put the fork
behind a default. The detector runs with the rest of the `structural` category and honours the
existing `--category`/`--min-severity` filters without change.

**It READS exactly one existing setting, and it reads it as a REFUSAL PRECONDITION rather than as a
behaviour toggle** *(added 2026-09-25 with threat-model M6; this section previously said "no env var"
flatly and that is why it is restated rather than amended in place)*.

| setting | where it lives | values | default | what this item does with it |
|---|---|---|---|---|
| `OBSIDIAN_SCHEMAS_WRITE_GUARD` | the process environment, read per call by `obsidian_schemas/vault_io.py:guard_mode:169-181` | `enforce`, `observe`; any other value RAISES `WriteFailedError` from `_env_setting` | `enforce` | `rename_note` and `update_fields`' name-change arm REFUSE while it is anything but `enforce` (M6). Nothing else in this item consults it, and no path is enabled, widened or altered by it — the only two outcomes are "behave as specified" and "refuse loudly" |

The asymmetry is the design. A setting that changes WHICH write path runs would be the flag this
section refuses; a setting whose only effect is to turn a capability OFF has one safe direction and
this item takes it. The mode is never cached: `guard_mode` is an `_env_setting` read on every call, so
a consumer that sets it mid-run gets the refusal at the next rename with no restart, and one that
unsets it gets the door back the same way. The floor command sets no environment, so every battery
runs under `enforce`; the one check that drives `observe` sets and restores it itself (Task 10).

### 7. Prerequisites & Assumptions

Explicit, because the reviewer hunts for the unstated ones:

1. **Both `kind: precondition` artifacts are in the tree's git HEAD.** They are —
   `docs/stem-divergence-live-baseline.md` and `docs/wi-029-consumer-audit.md`, committed at
   `7615990` before the AC frame was presented, read back before the signature, and re-read by the
   data-premise gate against the criteria that consume them. The builder READS both and writes
   NEITHER.
2. **The live vault is unreachable from the build.** No test may construct a repository without an
   explicit vault path, name an absolute path, or read `OBSIDIAN_VAULT_PATH`. WI-031 closed the last
   route deliberately; `scripts/lint_vault.py:DEFAULT_VAULT:62` is still an environment read, which
   is why AC-3's module ships the five-part containment door described in `## Wall Membership`.
3. **The frozen corpus is byte-frozen.** `tests/fixtures/vault/` is pinned by
   `tests/fixture_vault.py:CORPUS_DIGEST:44`. Every battery materializes a TEMP copy with
   `tests/fixture_vault.py:materialize_vault:626` and plants into that copy. No fixture note is
   added, edited or deleted, so the digest constant is untouched and no manifest+digest pair edit is
   in scope.
4. **`Path.is_relative_to` and `Path.samefile`** — Python ≥3.9 and ≥3.5 respectively; the project
   already targets 3.9+ (`Path.is_relative_to` idioms and `X | Y` type unions appear throughout
   `obsidian_schemas/repositories/base.py`).
5. **The filesystem under the live vault is case-INSENSITIVE** (macOS/APFS default). This is why
   AC-2(h) exists and why the door's case-only branch is not dead code. The hermetic battery must
   NOT assume the build machine's temp filesystem shares that property: AC-2(h) is asserted by
   probing the behaviour (write `@x.md`, test whether `@X.md` resolves to the same file) and
   exercising the branch a builder can reach either way — see `## Edge Cases`, "case-insensitivity is
   not guaranteed under the cage".
6. **Trust boundary.** The only untrusted input is vault BYTES: note frontmatter and filenames. It
   crosses into typed models at `obsidian_schemas/parser.py:parse_markdown_file` and into the
   filesystem at `obsidian_schemas/vault_io.py`'s three doors. This item ADDS no boundary and moves
   none: the stamp is a path the package itself produced from a path the caller handed it, never a
   value read out of a note, and `_resolve_write_target` refuses one that resolves outside this
   repository's vault. Both halves of that claim are ASSERTED and not assumed, which is the threat
   model's 2026-09-25 correction to this paragraph. Its *never a value read out of a note* half is
   the READ direction of the stamp, untested before M2 and now Task 2's check (Design §1, "Unforgeable
   from note content"). Its containment half was true of the SOURCE and false of the door: the
   destination `rename_note` moves to is caller-supplied and was contained nowhere, so M1 applies the
   identical resolved-containment test to it before any `vault_io.move_note` call (Design §2, "The
   destination is CONTAINED"). The claim now covers the whole item rather than half of it. **A THIRD
   half, added 2026-09-26 with M7:** the one place in this item where an externally-supplied string
   COMPOSES a write target is `update_fields`' `f"@{new_name}.md"`, and `new_name` comes out of
   `updates` — i.e. off the untrusted side of this same boundary, since Prerequisites 7's one
   consumer-visible door forwards an arbitrary PATCH body that may carry `name`. That composition is
   bounded on both sides and neither side is an assumption: `gate_write` refuses a separator-carrying
   `name` on the delta for the two types it validates, the pre-write refusal's third disjunct refuses the
   delta outright for every type it does not, and M1 contains whatever destination does reach the door.
   The residue the FIRST two leave — a `name:` key committed into a note the door then refuses to move —
   is what M7 closes (Design §2's precondition table, the M1 row).
7. **Consumers are out of reach and the contract change is disclosed.** HAL9000, Exocortex and
   orchestrator install `-e` and are outside `pipeline-runners.yaml:write_authority:34-38`. The audit
   answers: 19 of 19 consumer sites on the nine paths are on LOADED entities; 0 `auto_load=False`
   constructions; 0 reconstructions feed a write; `BookRepository.save`/`MeetingRepository.save` have
   0 consumer call sites. The one consumer-visible behaviour change is HAL9000's generic entity PATCH
   (`routers/entities.py:461`), which forwards an arbitrary body that may carry `name` and which
   today forks — after this item it MOVES the file and keeps an alias. That is in Dave's signed
   read-back (conductor read-back note 4): disclosed, not discovered. **Three sub-populations of that
   one change RAISE where today's call returns 200, and they are disclosed here rather than left to
   the consumer to discover** *(added 2026-09-26 after the fourth spec-review round; the read-back's
   "a move with an alias" is the MAIN arm and these are the arms beside it, none of which changes what
   Dave signed — the read-back describes the capability, and a refusal is that capability declining
   rather than a second behaviour)*. A PATCH carrying `name` against an entity with no provenance
   raises `ValueError` (Design §2's pre-write refusal, first disjunct); against a `Book` or `Meeting`
   it raises `ValueError` (M7, third disjunct); and against a name whose `@{name}.md` is ALREADY
   OCCUPIED by a different note it commits the field and then raises `NoteAlreadyExists`, leaving the
   residual Design §2's complement rule states and `## Edge Cases` resolves. **A FOURTH arm is
   disclosed here too, and it is the one that does NOT fit that sentence's "where today's call returns
   200" frame** *(added 2026-09-26 with M8)*: a PATCH carrying NO `name` key against a `Book` or
   `Meeting`, touching one of the six fields that type's own filename rule is made of — `title` or
   `author` for a Book, `date`, `topics`, `attendees` or `meeting_id` for a Meeting — raises
   `ValueError` naming the filename-rule precondition (Design §2's second clause). Today that same
   call raises too, one frame earlier and for an unrelated reason: `update_fields` opens
   `get_file_path(getattr(entity, "name", ""))`, which for a Book is `_file_map.get("")` and answers
   `None`, so the method refuses ABOVE the lock
   (`obsidian_schemas/repositories/base.py:BaseRepository.update_fields:437-441`,
   `obsidian_schemas/repositories/book.py:BookRepository.get_file_path:326-338`). So the consumer sees
   a refusal before and a refusal after, with a different and more accurate message — no capability is
   withdrawn. What Task 3's `resolved`-first reorder DOES newly admit for those two types is the
   complement, a delta that leaves the filename rule where it found it (`{"status": …}` on a Book,
   `{"tags": …}` on a Meeting), which today raises and after this item succeeds: that is the widening
   Design §5 declares, and this arm is its bound rather than a second behaviour. The audit
   (`docs/wi-029-consumer-audit.md:84`) records the generic PATCH as the route and says nothing about
   an occupied destination, which is why the disclosure is made here from the design rather than read
   off the audit. The third is the only one of the three that leaves state behind, it is the direction
   table's MERGE shape (`docs/stem-divergence-live-baseline.md` §2 measures it at 1 of 8 live rows),
   and its recovery is one direct `rename_note` call once the destination is free.
8. **The repair run and the exit attestation happen OUTSIDE the cage.** The builder ships the seam,
   the door, the detector and the batteries; it does not touch Dave's vault, does not fill
   `docs/stem-divergence-live-baseline.md` §5, and does not run `--fix` against anything.
9. **The write guard is ENFORCING wherever a rename actually runs — and that is now a checked
   precondition rather than an assumption** *(added 2026-09-25 with threat-model M6)*. Every
   occupied-destination refusal this item leans on lives behind
   `obsidian_schemas/vault_io.py:guard_mode:169-181`, whose default is `"enforce"` and whose other
   legal value, `"observe"`, turns `_move_locked`'s `NoteAlreadyExists` into `os.replace` — a silent
   overwrite of the occupied note (`obsidian_schemas/vault_io.py:_move_locked:757-771`; WI-004's
   declared residual R9, `docs/concurrent-access.md:649-656`). This item does not ASSUME the mode: the
   door and `update_fields`' name-change arm both refuse while it is anything else, so the assumption
   is enforced at the two places it matters instead of being stated here and hoped for (Design §2,
   "The door FAILS CLOSED when the write guard is not enforcing"). Two consequences a reader should
   have explicitly. The conductor's live repair run inherits whatever the shell carries, so the
   close-out's step 2 is a no-op that raises rather than a corruption if `OBSIDIAN_SCHEMAS_WRITE_GUARD`
   is set in that shell — see `## Verification`'s close-out. And a consumer that reaches for the
   documented rollback lever (`docs/concurrent-access.md:4286`) loses the RENAME capability while it
   is set, which is the intended trade and is named in `## Risk Analysis`.

## Verified Diagnosis

SIX load-bearing claims about how the system behaves incorrectly today — the six numbered below, and
the count is stated to match them (an earlier draft said "four" over six items). Each is grounded in an
artifact a reader can re-run; if any were false, the work would be invalid.

1. **`save` binds its target from the raw name and can neither rename nor unlink, so a re-save of an
   entity loaded off a divergent stem creates a SECOND note.**
   `obsidian_schemas/repositories/base.py:BaseRepository.save:391-393` is
   `name = getattr(entity, "name", "Unknown")` → `filename = f"@{name}.md"` →
   `file_path = self.vault_path / filename`, and the method body (`:367-412`) contains no `unlink`,
   no `rename` and no `replace`. WI-021's own audit records both halves as *confirmed*
   (`docs/write-door-bypasses.md:452-453`) and rejected its option (a′) for exactly this consequence
   (`:486`). Re-executed independently by five architect rounds and by the data-premise gate.
2. **Where the canonical filename is already taken, the same defect silently OVERWRITES a sibling
   instead of forking.** `overwrite=True` is `save`'s default
   (`obsidian_schemas/repositories/base.py:BaseRepository.save:372`), so for the `Quillam` shape —
   three corpus notes, one stored name, one of them living at `@Quillam Ostrivane Lumbrek.md`
   (`tests/fixture_vault.py:NOTES:255-276`) — a save of either divergent member lands on the third.
   Two corruptions from one defect, which is why AC-1's oracle is per-member.
3. **`save` is not the only name-bound write path: there are nine.** Predicate (re-derived by the
   data-premise gate from a door-grep rather than from the list): grep
   `write_markdown_file\(|write_note\(|create_note\(|move_note\(` over `obsidian_schemas/**` returns
   twenty hits in thirteen enclosing functions — `writer.py`'s four path-taking leaves plus
   `base.py:398` (`save`), `base.py:490` (`update_fields`), `person.py:1447`+`:1458`
   (`append_to_timeline`), `:1559`, `:1679`, `:1758`, `:1828` (the other four body-writers),
   `book.py:170` and `meeting.py:192` (the two overrides). Every one of the nine repository paths
   resolves its target from a NAME: `base.py:391-393`, `base.py:438`, and the five identical
   `file_path = self.get_file_path(person.name)` lines, plus `self._get_file_name(entity)` at
   `book.py:167` and `meeting.py:189`.
4. **The name-keyed map cannot answer the question, and is empty for a whole repository
   configuration.** `_file_map` is one path per LOWERCASED NAME, filled last-wins over
   `vault_path.glob` (`obsidian_schemas/repositories/base.py:BaseRepository.load:241-246`), so for
   the live 2-note collisions (`docs/vault-shape-census.md:222`, "largest live collision: 2") it
   answers "which note won the walk"; and `_ensure_loaded` is a no-op under `auto_load=False`
   (`obsidian_schemas/repositories/base.py:BaseRepository._ensure_loaded:210-213`), so
   `get_file_path` then returns `None` for everything. This is the claim that rejects approach C′ and
   forces provenance.
5. **`lint_vault` has no divergence detector today.** `stem_name` has ZERO hits anywhere in
   `scripts/lint_vault.py`; the five check functions are `check_structural`, `check_completeness`,
   `check_links`, `check_timeline`, `check_noise` (`scripts/lint_vault.py:run_lint:1400-1406`); and
   the nearest neighbour, `person_missing_name`, repairs in the OPPOSITE direction — `--fix` writes
   `fm["name"] = fpath.stem.lstrip("@")` (`scripts/lint_vault.py:1040-1045`), i.e. the path is
   already treated as the authority when the field is empty.
6. **The live class is 8 notes and the class has grown** (`docs/vault-shape-census.md:262`, measured
   2026-09-07), with the per-note direction, occupancy and door verdict recorded in
   `docs/stem-divergence-live-baseline.md` §2: 7 RENAME (one of them case-only), 1 MERGE, 0
   FIELD-REPAIR, 0 gate-refused, 24 incoming wikilinks and 14 attendee-carrying notes of blast radius.

## Edge Cases & Open Questions

- **Case:** A note is parsed by `parse_markdown_content` (no path) or reconstructed through
  `model_dump()`/`model_validate()`, then saved.
  **Decision:** No stamp, so `save` creates at the name-derived filename exactly as today — and logs
  a WARNING naming the collision when that file already exists, before `write_markdown_file` reaches
  its zero case and raises `NoteAlreadyExists`. `update_fields` and the body-writers keep today's
  `ValueError`.
  **Reasoning:** AC-1(f) declares this as the honest limit rather than papering over it. Making the
  loss LOUD is the part that is buyable; refusing the write is approach E, whose ordering is
  unshippable. `model_copy` PRESERVES the stamp, so the commonest consumer copy idiom is not in this
  population, and the consumer audit measures the population at 0 sites today.

- **Case:** Two notes share one stored `name:` and a caller saves the one it actually read.
  **Decision:** The write lands in the note it was parsed from; the sibling is byte-identical
  afterwards.
  **Reasoning:** This is the whole point of binding by provenance rather than by `_file_map`, and it
  is the live shape (census: largest live collision 2). AC-1(b)+(c) assert it per member per path.

- **Case:** The repository was constructed with `auto_load=False` and `load()` was never called.
  **Decision:** Unchanged for the seam — a stamped entity writes to its own file with NO vault walk
  triggered. An entity with no stamp still raises `ValueError` from `update_fields` and from every
  body-writer rather than creating a note. This entry is the case where `get_file_path` is ALSO `None`,
  so nothing is written by construction; the case where it ANSWERS and the update changes the name is the
  separate entry below, and the two together are total over the no-provenance population.
  **Reasoning:** AC-1(g), both halves. The first half is the arm a load-derived battery structurally
  cannot see; the second is the arm that stops the seam being built as a uniform fallback, which
  would convert `person.py:1404-1405`'s loud refusals into a brand-new fork source.

- **Case:** `update_fields` is called with a NAME CHANGE on an entity carrying NO provenance, on a
  repository whose `get_file_path(name)` DOES answer — the one population the method's own preserved
  name-keyed fallback exists to serve.
  **Decision:** REFUSED with `ValueError`, raised INSIDE the lock immediately after the name-change
  decision is computed and BEFORE anything is gated or written, so the note is byte-identical
  afterwards: no new name committed, no alias appended, no file moved, no reload. The same call with
  no name change is unaffected and still writes through the fallback exactly as today.
  **Reasoning:** *(Second spec-review round's blocking finding 1, 2026-09-25.)* `rename_note`'s
  documented behaviour for an entity with no provenance is the raise in Design §2's invocation table
  row 10, so the only question is WHERE the refusal happens. After the write it leaves a divergent,
  un-aliased note plus an exception on a successful write — strictly the worst of the three available
  answers. Skipping the move keeps today's leave-behind, which is the divergence
  `## Verified Diagnosis` 1 and AC-2(c) exist to end, and drops the alias today's in-lock block
  appends (`base.py:454-459`). Re-stamping the entity from the name-keyed `file_path` is the one that
  causes new harm: `_file_map` is one path per lowercased name filled last-wins over `vault_path.glob`
  (`obsidian_schemas/repositories/base.py:BaseRepository.load:241-246`), so on a live 2-note collision
  it answers which note won the walk, and the door would then MOVE and alias a note the caller never
  named — AC-2(f)'s *"repair machinery corrupting a note it was never asked about"*, manufactured
  rather than survived. The predicate is the real one (`updates["name"] != frontmatter.get("name")`)
  and not `"name" in updates`, because HAL9000's generic PATCH forwards bodies that may carry an
  UNCHANGED `name` (Prerequisites 7) and refusing those would break a live consumer path over an
  update needing no move — which is why the check sits inside the lock, where `frontmatter` is bound.
  The consumer audit measures the population at zero today (19/19 loaded, 0 reconstructions feed a
  write), so it is one clause. Task 9's `update_fields` cell cannot reach this (it mutates `{"title":
  …}`) and AC-2's name-change arm binds a `_load_file`-stamped subject, so Task 10 asserts it directly.

- **Case:** `update_fields` is called with a `name` key on an entity whose own type does NOT declare
  `name` — a stamped `Book` or `Meeting`, reachable through HAL9000's generic entity PATCH, which
  forwards an arbitrary body (Prerequisites 7).
  **Decision:** REFUSED with `ValueError`, in the same in-lock arm and on the same third disjunct
  (`"name" not in type(entity).model_fields`), so the note is byte-identical afterwards: no `name:` key
  committed, no file moved, no reload. The same entity's update carrying no `name` key is unaffected and
  still writes through the seam exactly as Task 3 routes it — **for every field that is not one of the
  six that type's own filename rule is made of** *(bound added 2026-09-26 with M8; the sentence
  previously blessed the whole complement, and the complement contains `title`/`author` for a Book and
  `date`/`topics`/`attendees`/`meeting_id` for a Meeting, whose delta the entry immediately below
  refuses)*. A `Book` or `Meeting` note that STORES a
  `name:` key as a pydantic extra refuses identically and that is the correct direction, not a lost
  capability: its filename rule is `_get_file_name`, so `@{name}.md` is the wrong destination for it, and
  renaming such a note is the conductor's direction table's business (the booked "book-titled file
  holding a person note" hand repair) rather than this door's.
  **Reasoning:** *(Threat model 2026-09-26, M7.)* The trigger is `"name" in updates and updates["name"]
  != frontmatter.get("name", "")` — the caller's dict against the note's frontmatter — and a book note
  carries no `name:`, so `frontmatter.get("name", "")` is `""` and any non-empty `updates["name"]` would
  set `renaming` True. `gate_write` then hands the delta back UNVALIDATED, because it validates a `name`
  delta for `person` and `company` only (`obsidian_schemas/name_gate.py:gate_write:319-344`), so
  `base.py:490` COMMITS the caller's `name:` into the note and only then does `rename_note` raise:
  `@x/y.md` reaches `os.link` against a missing parent (`WriteFailedError`,
  `obsidian_schemas/vault_io.py:_move_locked:772-773`) and `@a/../../x.md` resolves above the vault and
  raises M1's containment `ValueError`. M1 holds in both — nothing is written outside the vault and
  nothing is hard-linked out — so the harm is not an escape; it is the committed-write-then-raise residual
  the no-provenance entry above calls *"strictly the worst of the three available answers"*, on an
  externally-supplied value, and SILENT where `## Risk Analysis` claims every residual is
  detector-visible, since Task 11's arm fires only on `vf.entity_type == "person"`. THIS ITEM creates the
  reachability: today `update_fields` opens with `get_file_path(getattr(entity, "name", ""))`, which for a
  Book answers `None` and raises above the lock (`base.py:437-441`, `:354-365`), while Task 3's
  `resolved`-first shape binds the file from the stamp and runs the whole frame. Refusing is chosen over
  composing the destination with `self._get_file_name(entity)` instead: that would make this item ship a
  SECOND filename rule through the door for two types with zero measured consumer call sites
  (Prerequisites 7: 0 on `BookRepository.save`/`MeetingRepository.save`) and would put Book's and
  Meeting's stem derivation on the rename path with no live direction table behind it — a capability this
  item was not asked for, where refusal costs nothing anyone is doing today.

- **Case:** `update_fields` is called with NO `name` key on a stamped `Book` or `Meeting`, where the
  delta touches one of the fields that type's own filename rule is made of — `{"title": "New Title"}`
  on a book living at `Old Title - Author.md`, `{"date": …}` or `{"topics": [...]}` on a meeting —
  reachable through the same generic entity PATCH (Prerequisites 7), which forwards an arbitrary body.
  **Decision:** REFUSED with `ValueError` naming the FILENAME-RULE precondition and the field(s) at
  issue, in the same in-lock pre-write arm, on its SECOND clause
  (`not renaming and derive is not None and derive(projected) != derive(entity)`), so the note is
  byte-identical afterwards: no field committed, no file moved, no reload. The same entity's delta
  touching only fields the rule does not read (`{"status": …}` on a Book, `{"tags": …}` on a Meeting)
  still SUCCEEDS and lands in the file the entity was parsed from — that is the widening Design §5
  declares. An ALREADY-divergent Book or Meeting note — one whose file does not match its own rule
  today, the live *"book-titled file holding a person note"* class — also still accepts any delta that
  does not move its rule further, because the comparison is `derive(projected)` against
  `derive(entity)` and never against `file_path.name`. And a `Person` or `Company` is untouched: their
  repositories declare no `_get_file_name` at all, so `derive` is `None` and the clause is structurally
  inert for them.
  **Reasoning:** *(Threat model 2026-09-26, M8.)* `renaming` is
  `"name" in updates and updates["name"] != frontmatter.get("name", "")`
  (`obsidian_schemas/repositories/base.py:BaseRepository.update_fields:454`) and the entire rename-side
  predicate is `if renaming and (…)`, so a delta with no `name` key evaluates none of it;
  `obsidian_schemas/name_gate.py:gate_write:319-344` hands a non-`person`, non-`company` delta back
  UNVALIDATED; and `base.py:490` COMMITS. Nothing moves, nothing raises, no alias records the stem the
  note is leaving behind — the note's own filename rule no longer recomputes to the file it lives in,
  which is verbatim this document's type-general divergence predicate
  (`## Exploration Notes`, "Divergence is not a Person-only predicate": *"that string ≠ the file it was
  parsed from"*) manufactured by the method that exists to end it. It is SILENT where
  `## Risk Analysis` claims every residual is loud and detector-visible, because Task 11's arm fires
  only on `vf.entity_type == "person"`. THIS ITEM creates the reachability, exactly as it does for M6
  and M7: today `update_fields` opens `get_file_path(getattr(entity, "name", ""))`, which for a Book is
  `_file_map.get("")` and raises ABOVE the lock (`base.py:437-441`,
  `obsidian_schemas/repositories/book.py:BookRepository.get_file_path:326-338`), while Task 3's
  `resolved`-first shape binds the file from the stamp and runs the whole frame — the premise Design §5
  states in its own words as the widening it declares. The route is external and is the one this item
  already singles out: `docs/wi-029-consumer-audit.md:84` records `routers/entities.py:461` as
  `repo.update_fields(entity, body)` with *"`body` is an arbitrary HTTP PATCH dict"*, and `:137` names
  the same route as the ONLY consumer path to those two repositories — so `PATCH
  /api/entities/book/{name}` with `{"title": …}` is an ordinary request, not an attack. Refusing is
  chosen over the two alternatives for the same reasons the M7 entry gives one row up: composing the
  destination with `self._get_file_name(entity)` and MOVING the note would ship a second filename rule
  through the door for two types with zero measured consumer call sites and no live direction table
  behind it, and committing-then-reporting is the silent divergence itself. `## Scope Boundary` already
  declared refusal the right answer *"where **refusal** costs nothing anyone does today"*; this clause
  is that declaration made real.

- **Case:** Two callers race `update_fields` with a name change — the content write commits inside the
  lock and the door's move happens after that lock has released, so there is now a WINDOW between them.
  **Decision:** Accepted knowingly. Every interleaving is LOUD, is (for a Person subject) exactly the
  `stem_name_divergence` the new detector reports, and is recoverable by re-running **the DOOR** —
  `repo.rename_note(entity, f"@{new_name}.md")`, never a re-run of `update_fields`, whose trigger now
  reads the committed name back out of the note's own frontmatter and so never fires the branch
  (Design §2, "The COMPLEMENT of that rule"). Every one of them is a MOVE that did not happen, which
  is the residual a door re-run does complete (the half-failed ALIAS write is the one it does not, and
  it has its own entry below). A concurrent write of
  the source loses to last-writer-wins and then moves with the file; a concurrent move or delete of the
  source gives `FileNotFoundError` from the door's own `source.exists()` check; a concurrent create at
  the destination gives `NoteAlreadyExists` by syscall — which holds because M6 has already refused the
  whole call where the write guard is not enforcing, the one configuration under which that syscall
  refusal is an `os.replace` instead (Design §2, "The door FAILS CLOSED…"; the `observe` entry below).
  No interleaving lands one person's bytes in
  another person's note, which is the harm this item exists to end.
  **Reasoning:** *(Threat model round 2's carried-forward note, folded here beside the lock-ordering
  entry it must not be read as part of.)* `update_fields` was ATOMIC across write-then-alias before this
  item, because the alias write happened inside the same lock; it is not atomic across write-then-move
  after it, because the move cannot be held inside that lock without creating the deadlock ordering
  decision 5 refuses. The entry below is true as written — *no new lock-ordering edge exists* — and it
  must not be read as *no new window exists*: the trade is one non-atomic sequence whose every residual
  is loud and detector-visible, against a deadlock in a library three consumers run. The window is not a
  required mitigation and the plan orders no work for it; it is recorded so the two statements cannot be
  confused.

- **Case:** The stamped file has been deleted, or moved, out from under the entity.
  **Decision:** `_resolve_write_target` still returns it (existence is not part of the resolution).
  `save` then CREATES at that path — which is what the name-derived path does today for a deleted
  note; `update_fields` and the body-writers hit their own `.exists()` check one line later and raise
  `FileNotFoundError`/`ValueError` as they do today.
  **Reasoning:** Keeping existence out of the resolution is what makes the function total and its one
  answer stable. Folding it in would give `save` a second silent fallback.

- **Case:** An entity is handed to a repository whose `vault_path` is a DIFFERENT vault (a consumer
  holding two repositories; a test).
  **Decision:** The stamp is treated as absent — `_resolve_write_target` returns `None` and the
  caller's own fallback applies.
  **Reasoning:** A repository must not be steerable into writing outside its vault by an entity it
  was handed. Asserted directly rather than trusted.

- **Case:** Two callers write the same note concurrently; or one renames while another saves.
  **Decision:** Unchanged, and it stays unchanged only because NO CALLER HOLDS A NOTE LOCK ACROSS THE
  TWO-LOCK DOOR. Every write still goes through `vault_io`'s doors, which hold `note_lock` and a
  precondition stamp; `move_note` takes both paths' locks in a global sorted order
  (`obsidian_schemas/vault_io.py:move_note:744-750`). `rename_note` holds no outer lock across the
  move and the alias write, and `update_fields` calls it AFTER its own
  `with vault_io.note_lock(file_path)` block has exited (Design §2, and the block is written out
  there) — so the global order is the only order in play and no new lock-ordering edge exists. That is a
  claim about LOCK ORDERING and about nothing else: `update_fields` DOES gain a non-atomic window between
  its committed write and the move, which is the entry above, and the two statements are separate on
  purpose.
  **Reasoning:** The seam changes WHICH path a write targets, never HOW it is committed. The one new
  concurrency surface is the door, and it is built on the one door designed for two paths. The
  REENTRANCY of `note_lock` is deliberately NOT the argument here, because it does not carry the
  weight: reentrancy excuses re-acquiring a lock you already hold, while a sorted two-lock
  acquisition is deadlock-free only while nobody holds either lock across the call. A caller inside
  `note_lock(A)` calling `move_note(A, B)` with `str(B) < str(A)` takes A-then-B against the order,
  a concurrent `move_note(B, A)` takes B-then-A, and both block; `rename_note`'s
  `update_frontmatter_field(moved, …)` (`obsidian_schemas/writer.py:update_frontmatter_field:368`)
  would be a second out-of-order acquisition from the same held lock. Nothing in the tree does this
  today (`scripts/lint_vault.py:1343` is `move_note`'s one caller and holds no lock), so this item is
  the only thing that could introduce the edge — which is why the rule is asserted structurally
  (ordering decision 5's `door_calls_inside_note_lock` scan, EMPTY over `PACKAGE_ROOT`, pinned both
  ways in Task 10) rather than promised in prose.

- **Case:** The rename fails halfway — the move succeeded and the alias write did not.
  **Decision:** *(Restated 2026-09-25 after the third spec-review round's blocking finding 1; the
  previous Decision claimed a repair the prescribed door cannot perform.)* The entity is already
  re-stamped at the new path (the re-stamp precedes the alias write) and the exception propagates as a
  `LoudFailError`. The residual is **a moved, correctly-stamped note missing one alias** — the file is
  where it should be, under the new name, and the only loss is that the OLD stem no longer resolves.
  Re-running `rename_note(entity, <the same filename>)` is SAFE and is a NO-OP: it takes the
  `same_place` branch, performs no second move, and appends **nothing** — `old_stem` is read from the
  source, which is now the destination, so the `old_stem != new_stem` guard is False. **It does not
  repair the missing alias.** The recovery is a one-field edit by the caller —
  `repo.update_fields(entity, {"aliases": [*entity.aliases, <the old stem>]})`, which goes through the
  ordinary write path and moves nothing since the name is unchanged — or a hand edit of the note's
  `aliases:` key.
  **Reasoning:** `move_note` is link-then-unlink precisely so a mid-flight failure leaves a duplicate
  rather than a hole (`obsidian_schemas/vault_io.py:move_note:729-734`), and the residual here is
  strictly smaller than that: one note, one missing alias, nothing forked and nothing lost. Making the
  door repair it would require re-stamping LAST, which ordering decision 2 rejects because the failure
  would then leave an entity whose next `save()` recreates the note the rename removed — a fork
  manufactured by the repair — or persisting an intent record, a journal this item does not ship. One
  unreachable old stem against a manufactured fork is the trade, taken deliberately. The no-op half is
  ASSERTED rather than assumed: Task 10 drives `rename_note(entity, <the same filename>)` twice and
  pins the second call — no `move_note` call recorded, the filename set unchanged, `aliases` unchanged
  (nothing appended twice, and after a half-failure nothing appended at all), the stamp still naming
  that file. AC-2 is signed and gains no arm; the battery covering it does.

- **Case:** The rename destination is occupied by a DIFFERENT note (the live MERGE row), on a DIRECT
  `rename_note` call.
  **Decision:** `move_note` refuses by syscall with `NoteAlreadyExists` and both files are
  byte-identical afterwards. The door does not merge — merging is a conductor judgement, per the
  direction table.
  **Reasoning:** AC-2(b). The refusal is the kernel's `FileExistsError` on `os.link`
  (`obsidian_schemas/vault_io.py:_move_locked:759-771`), not a check-then-act. That refusal is
  CONDITIONAL on the write guard, which is why M6 makes an enforcing guard a precondition of the door
  rather than qualifying this Decision: the entry below owns the non-enforcing case and the door never
  reaches `move_note` in it, so this sentence is true of every call that gets that far. **The
  byte-identical half is scoped to the DIRECT call and is false on the `update_fields` path**, which is
  the entry immediately below — it was previously stated here unscoped, and this section's only
  occupied-destination entry therefore said the `update_fields` residual could not happen *(fourth
  spec-review round's blocking finding, 2026-09-26)*.

- **Case:** `update_fields` is called with a name change whose destination `@{new_name}.md` is ALREADY
  OCCUPIED by a DIFFERENT note — every precondition satisfied, no race, no configuration, no exotic
  type: a stamped `Person` or `Company`, an enforcing write guard, a `name` the gate accepts. (The
  same shape, by the same route, for a SYMLINKED source, whose refusal also comes out of `move_note`.)
  **Decision:** The content write COMMITS and the door then raises — `NoteAlreadyExists` for the
  occupied destination, `WriteFailedError` for the symlinked source — so the residual is **the note
  carrying its NEW stored `name:` at its OLD filename, with no alias, with the entity still stamped at
  that old path, and an exception on the caller after a successful write**. The destination note is
  BYTE-IDENTICAL: `os.link` failed before anything was written to it. This is ACCEPTED, and the
  recovery is stated rather than left to the caller to infer: remove the cause — for the occupied
  destination that is the direction table's MERGE, a conductor judgement the door is specified never to
  make — then call `repo.rename_note(entity, f"@{new_name}.md")` DIRECTLY and re-bind the entity from
  the path it returns. A re-run of `update_fields` with the same `updates` is SAFE and is NOT the
  repair: the note's frontmatter now already carries the new name, so `renaming` is False and no move
  is attempted.
  **Reasoning:** *(Fourth spec-review round's blocking finding, 2026-09-26; the THIRD member of the
  class "`update_fields`' rename branch commits its content write and then discovers the door will not
  complete the move", which is why Design §2 answers it with the rule total over the precondition
  table's whole NO half — "The COMPLEMENT of that rule" — rather than with a fourth disjunct.)* The
  two alternatives are refused there with their citations: move-then-write is UNAVAILABLE, because the
  door's own alias write invalidates the content write's `precondition=stamp` and would turn every
  successful rename into an `ExternalWriteConflict`
  (`obsidian_schemas/vault_io.py:write_note:685-698`), and AC-2's signed `why` prescribes
  write-then-move in its own words; pre-checking the destination is the check-then-act the precondition
  table refuses, since the check answers a question the filesystem may answer differently one syscall
  later while the package gains a second authority beside `os.link`. And the residual is not a
  regression against today, which is the comparison that decides it: today this same call SUCCEEDS
  (`base.py:454-459` appends the old stem in-lock, the write commits, the reload returns) and silently
  leaves exactly this divergence — `## Verified Diagnosis` 1, the thing AC-2(c) exists to end — so what
  changes is that the caller now LEARNS, and the one thing lost is an `aliases` entry naming a stem the
  note still occupies as its own filename. Loudness has one honest bound: for a Person the residual is
  exactly the `stem_name_divergence` Task 11 reports, while the same residual on a COMPANY note is
  outside the detector's `vf.entity_type == "person"` guard — stated in Design §2 rather than implied.

- **Case:** `OBSIDIAN_SCHEMAS_WRITE_GUARD` is set to `observe` — the estate's own documented rollback
  lever (`docs/concurrent-access.md:4286`) and measure-before-adopting mode (`:2556`) — and a rename
  is attempted.
  **Decision:** REFUSED. `rename_note` reads `vault_io.guard_mode()` beside M1's containment block and
  raises `ValueError` naming the mode before any `vault_io.move_note` call, so NOTHING moves, no alias
  is appended, no entity is `_adopt`ed and no successful-rename INFO line is logged. `update_fields`
  refuses the same condition EARLIER — inside its lock, in the same arm that refuses a no-provenance
  name change, before anything is gated or written — so a name change under `observe` leaves the note
  byte-identical rather than committing the new name and then discovering the door will not move the
  file. Every other write path in the package is unchanged in both directions: `save`, the five
  body-writers and a non-rename `update_fields` behave under `observe` exactly as they do today.
  **Reasoning:** *(Threat model 2026-09-25, M6.)* Under `observe`,
  `obsidian_schemas/vault_io.py:_move_locked:757-771` catches the kernel's `FileExistsError` and does
  `os.replace(source, target)` — it DESTROYS the occupied note, returns the destination as a success,
  and the door would then alias, adopt and log a rename that overwrote a third party. That is
  `## Intent`'s own harm, unrecoverable where a fork is recoverable, in the one act `## Risk Analysis`
  says `git` cannot undo. WI-004 declared the residual acceptable (R9,
  `docs/concurrent-access.md:649-656`) while door 3 had one quarantine caller; this item makes door 3
  the package's relocation capability, so the premise is gone and the cost is this item's. Refusing
  the DOOR rather than repairing door 3's observe arm keeps the change inside this item's scope —
  `create_note`'s identical arm is AC-1(f)'s and stays WI-004's — and failing closed is the safe
  direction for a capability whose only two outcomes are "move correctly" and "refuse loudly". The
  cost is honest: while the mode is set, the library cannot rename, which is a capability LOSS a
  consumer can observe. It is the intended trade (a rollback lever that disables the newest write
  capability is behaving correctly) and is stated in Prerequisites 9 and `## Risk Analysis` rather
  than discovered.

- **Case:** The rename destination is the note's OWN case-variant on a case-insensitive filesystem
  (live baseline §2, row 3).
  **Decision:** The door detects it with `source.samefile(destination)` and moves in two steps
  through a staging name derived from the SOURCE that keeps the `.md` suffix
  (`source.with_name(destination.stem + ".rename-tmp.md")`). Afterwards the directory holds exactly
  one entry for that note, spelled in the new case, with the old spelling in `aliases`.
  **Reasoning:** AC-2(h). A door that compares destination STRINGS refuses the one repair that works
  for that row; `os.link` against the note's own inode raises `FileExistsError` regardless of
  spelling. The staging name is derived from the source so the seam's value reaches every move's
  first positional — AC-5's own rule, applied to the item's own door. Two OTHER shapes reach this same
  branch and neither is left open: Design §2's same-file sweep enumerates them and orders no work — a
  second in-vault HARD LINK to the note takes the two-step and its second move raises
  `NoteAlreadyExists`, leaving exactly the visible staging note the entry below owns, while an in-vault
  SYMLINK at the destination naming the source runs both moves and lands the note back where it
  started, the door returning that path and appending nothing.

- **Case:** The destination and the entity's stamp name the SAME file under two different strings —
  the stamp is `move_note`'s RESOLVED answer from an earlier rename while `self.vault_path` is
  whatever spelling the repository was constructed with (macOS's `/var` → `/private/var` under
  `$TMPDIR`; a relative vault path; a `..` segment).
  **Decision:** *(Third spec-review round's blocking finding 2, 2026-09-25.)* The branch key is
  `(destination.parent.resolve(), destination.name) == (source.parent.resolve(), source.name)`, never
  a raw `Path` comparison, so the idempotent branch fires on file identity and the re-run is the no-op
  it is documented to be. The RAW `.name` stays in the key, so a case-only destination still falls
  through to the two-step even on a platform whose `resolve()` canonicalizes case.
  **Reasoning:** WI-149's rule applied to a branch discriminant: `destination == source` turns on a
  path SHAPE the ENVIRONMENT decides, not the caller. Under it, the idempotent re-run on this
  project's own platform takes the case-only two-step instead — two real moves through a staging name,
  so an interrupted re-run can leave a `.rename-tmp.md` where this document says nothing moved at all,
  and Task 10's "no `move_note` call recorded" would be RED against a verbatim-correct build. Task 10
  PLANTS the spelling divergence rather than waiting for the platform to supply it (a vault path the
  test itself spells through a real sub-directory and `..`), so the arm discriminates everywhere and
  not only where `$TMPDIR` happens to be a symlink.

- **Case:** The process dies between the case-only branch's two moves, leaving the note at the
  staging name.
  **Decision:** The staging name is inside the `*.md` namespace (M3), so the residual state is a
  VISIBLE note: Obsidian shows it, all three `file_pattern` globs match it, `lint_vault` reads it,
  and the new detector reports it as a `stem_name_divergence` ERROR. Recovery is a HAND rename. A
  re-run of the door is not it, and the reason is stated totally in Design §2's re-run table: with the
  SAME entity the door raises `FileNotFoundError`, because the stamp still names the pre-move source
  (the re-stamp is not reached on this path) and that file is gone; with an entity loaded from the
  staging note the door does complete the move, but appends `<stem>.rename-tmp` to `aliases`, which is
  then one more thing to strip by hand.
  **Reasoning:** *(Threat model 2026-09-25, M3.)* A staging name outside `*.md` makes the same
  failure SILENT — no reader picks the file up, so the note is simply gone from every surface until
  someone looks in the directory. That is the hole `move_note`'s link-then-unlink ordering exists to
  avoid (`obsidian_schemas/vault_io.py:move_note:732-734`), manufactured by its own caller. The
  likelihood is low (one live row, baseline §2 row 3, repaired by hand by the conductor) and the fix
  is one expression, so low is not a reason to skip it.

- **Case:** A caller hands `rename_note` a `new_filename` that leaves the vault — `../../x.md`, an
  absolute path such as `/tmp/x.md` (which replaces the vault root outright under pathlib's `/`), or
  an in-vault filename occupied by a SYMLINK pointing outside.
  **Decision:** Refused with `ValueError` before any `vault_io.move_note` call, on the RESOLVED
  destination (M1). The symlink spelling is the reason the test is resolved rather than
  string-compared: `vault_io._resolved` follows symlinks
  (`obsidian_schemas/vault_io.py:_resolved:234-243`), so a dangling in-vault symlink resolves
  outside, `os.link` succeeds there, and the note lands outside under a clean name no Tier-1 branch
  would ever flag. A destination whose `.resolve()` raises `OSError`/`ValueError` is treated as NOT
  contained.
  **Reasoning:** *(Threat model 2026-09-25, M1.)* `rename_note` is PUBLIC and this item ships the
  package's first relocation capability to three `-e` consumers, one of which already forwards
  arbitrary request bodies into this layer (HAL9000's generic entity PATCH, `routers/entities.py:461`),
  so a filename derived from request data reaching the door is the next obvious call site rather than
  a contrived one. The only thing bounding it today is `path_hostile`'s `/` regex in a name-hygiene
  table this item declares read-never-edited, which `gate_write` skips for a declared non-person type
  — a boundary you can route around. The door refuses for itself, in one clause, with the test the
  seam already performs on the source.

- **Case:** Case-insensitivity is NOT guaranteed on the cage's temp filesystem, so AC-2(h)'s
  precondition may be absent where the check runs.
  **Decision:** The check PROBES rather than assumes: it writes `@Probe.md`, tests whether
  `(vault / "@probe.md").exists()`, and on a case-SENSITIVE filesystem asserts the same door call
  through its ordinary branch (a plain move to a different-cased name, which is simply a distinct
  file there) while asserting the same post-conditions — one directory entry for that note, spelled
  in the new case, old spelling in `aliases`. The samefile branch is additionally driven directly by
  a unit-level call in the same check, so the branch is never unexercised.
  **Reasoning:** WI-149's rule: derive the oracle from what the test itself created and observed,
  never from an environmental shape assumed present. A check that assumed case-insensitivity would be
  red in a correct build on a case-sensitive filesystem, and one that assumed sensitivity would skip
  the arm the live vault needs.

- **Case:** A person note has no stored `name:` at all, or a blank one.
  **Decision:** It is NOT reported as divergent — that is the `stored.strip()` conjunct of the arm, and
  Task 12 plants a whitespace-only-`name:` person note whose stem differs from it and asserts NO
  `stem_name_divergence` issue for it (plant (vi), Design §3a's sweep row). It belongs to
  `person_missing_name`.
  **Reasoning:** *(Round 5 note 2; the PLANT added 2026-09-25 after the second spec-review round's
  blocking finding 2, which is the class-level rule of Design §3a applied to the one conjunct the sweep
  had not read.)* That rule is ERROR and AUTO-FIXABLE and repairs in the opposite
  direction (`scripts/lint_vault.py:1040-1045` writes the stem into the field), so claiming the note
  here would give it an auto-fixable ERROR and a never-fixable ERROR that the first one silently
  repairs away — a confusing row on the report and an odd interaction with AC-3(d)'s accounting. The
  live stake is measured at zero at both ends of the WI-026 bracket
  (`docs/lint-vault-live-baseline.md:82`, `:149`) and at zero corpus subjects. One precision, so the
  hand-off is not overstated: `person_missing_name` is gated to ACTIVE-tier notes
  (`scripts/lint_vault.py:check_completeness:429-446`, `classify_person_tier`), so a STUB-tier note
  with a blank `name:` is claimed by neither rule. That population is measured at zero at both ends of
  the same bracket and this item does not widen either check to cover it — recorded here rather than
  implied by "it belongs to `person_missing_name`". That same precision is why the plant asserts
  SILENCE from this check rather than the presence of a particular partner issue: dropping the conjunct
  is wrong in both tiers and differently — a double ERROR on an ACTIVE note, a lone permanent one on a
  STUB — and the property this check owes is the same in both.

- **Case:** A person note's stored `name:` is not a string — a YAML list, a number, a mapping.
  **Decision:** NOT reported as divergent (`isinstance(stored, str)` in the arm), and Task 12 plants
  one so the narrowing is pinned rather than incidental.
  **Reasoning:** The class is "the stem disagrees with the stored NAME", and both declared repair
  directions — move the file, or fix the field to match the file — are undefined when the field is not
  a name; a `str(value)` comparison would emit an ERROR whose stated repair no rename can perform.
  Design §3 carries the argument and the consequence: no check in the tool reports that shape today,
  which is one Build-Log line and a candidate for `lint_vault`'s backlog, not a second arm here.

- **Case:** A note that is NOT `@`-prefixed carries `type: person` — the live vault's row 8, a
  book-titled file at the vault root (`docs/stem-divergence-live-baseline.md:153`).
  **Decision:** REPORTED as `stem_name_divergence`, because the guard is `vf.entity_type == "person"`
  and not `vf.is_at_prefixed`. Its repair is the direction table's MERGE (its canonical `@{name}.md`
  is occupied by a different note), not a rename, and the issue carries NO not-renameable marker
  because the door WRITES its stored name (baseline `§1`: 0 of 8 refused).
  **Reasoning:** `check_structural` reaches the file — the two `is_at_prefixed` tests guard only
  `no_frontmatter` and `missing_type` (`scripts/lint_vault.py:check_structural:362-381`) and `person`
  is in `TYPE_TO_MODEL`. This is one of the eight divergences the item exists to repair and one of the
  four booked hand repairs, so a detector that cannot see it fails the fourth "Examples of done"
  scenario on the live report while passing every corpus arm — the WI-286 generator, third member
  (Design §3a). Task 12 plants the shape and asserts the ERROR fires.

- **Case:** A note the linter cannot decode, or whose frontmatter does not parse.
  **Decision:** Never reported as divergent; it keeps its `unreadable_note` / `parse_error` ERROR.
  **Reasoning:** AC-3(e). Both arms `continue` above the new one in `check_structural`
  (`scripts/lint_vault.py:check_structural:340-359`), so this is a placement property rather than a
  second guard — WI-026's triage order is preserved by construction.

- **Case:** A `NoteSpec` in the corpus manifest declares NO `fields` mapping (SCHEMA_DRIFT,
  MALFORMED_FRONTMATTER, UNREADABLE specimens).
  **Decision:** The manifest-side derivation SKIPS it rather than crashing on it or silently widening.
  **Reasoning:** *(The data-premise audit's manifest/bytes note.)* AC-3(a) derives its expected set
  from the manifest while the shipped detector reads FILES, and three person-owned specimens declare
  no `fields`. The audit read all three bytes-first: `@Ferrigan Ostrakine.md`,
  `@Halvorne Sennaby.md` and `@Isolde Varnholt.md` each agree with their own stem, so four holds
  against the corpus BYTES and not only against the manifest — but the derivation must still handle
  the absent mapping explicitly.

- **Case:** A renamed note's incoming `[[wikilinks]]`, `attendees:` entries and `company:` values
  still name the old stem.
  **Decision:** Accepted knowingly, and measured before the signature: 24 wikilinks and 14
  attendee-carrying notes (`docs/stem-divergence-live-baseline.md` §1, §3). They become linter
  WARNINGS and can never become a wrong auto-repair — `broken_wikilink`'s fixable arm needs
  `MEETING_DATE_PATTERN` to match (`scripts/lint_vault.py:572-592`), which a person stem cannot.
  **Reasoning:** The disposition was chosen in exploration with its rejected alternatives. Teaching
  `check_links` to resolve through `aliases` is a change to a shipped resolver with its own both-ways
  pinning obligation and belongs to `lint_vault`'s own backlog; precondition (c) is exactly the
  evidence that would justify minting it.

- **Case:** Re-running the whole build, or re-running the repair, or re-running the detector.
  **Decision:** All idempotent. The seam is a pure resolution; `rename_note` short-circuits when the
  note is already at the destination (by file identity, not by string) and never appends an alias
  twice; the detector writes nothing. TWO residuals a re-run does NOT repair, named so "idempotent" is
  not over-read. (1) A missing alias left by a rename whose move committed and whose alias write raised
  — the entry above states it and names the one-field recovery. (2) A `update_fields` name change whose
  door raised BEFORE the move (an occupied destination, a symlinked source): re-running
  `update_fields` is safe and completes NOTHING, because the note's frontmatter already carries the
  committed new name so `renaming` is False; the repair is a direct `rename_note` call once the cause
  is gone (Design §2, "The COMPLEMENT of that rule"). A repair row whose MOVE did not happen is
  completed by re-running THE DOOR exactly as this entry says.
  **Reasoning:** The live repair is a conductor act that may need a second pass after a partial
  failure, and a door that is not idempotent turns that into a second incident.

- **Case:** A tenth write path is added later, or an existing one is rewritten to call the seam and
  discard its return.
  **Decision:** AC-5's scan fails it, naming the file, the function and the line — the call-and-
  discard shape and the unconditional-rebinding shape are both in the REFUSED battery.
  **Reasoning:** A function every caller MAY use is a polite request, not a boundary.

- **Case:** The live baseline is four days old at spec time and the vault moves daily.
  **Decision:** Contained by design and NOT blocking: the Intent carries no frozen count (the
  2026-09-21 sharpening replaced "the three forked notes" with "the forked notes" for this reason),
  no acceptance criterion asserts the number 8, AC-4 asserts that the entry counts are PRESENT and
  NUMERIC rather than equal to any value, and AC-4's exit half re-runs the identical script. The
  build-runner's Verify-Assumptions step re-runs §0's script and treats a changed direction TABLE — a
  new row, or a row whose (b2)/(b3) answer moved — as a drift report rather than merely a changed
  count.
  **Reasoning:** *(The data-premise gate's premise-rot note.)* A number quoted today is stale by
  build time; the property is not.

OPEN: None.

## Implementation Plan

Fourteen tasks, ordered by dependency. Tasks 2–6 are the library and must land in order; 7–12 are
batteries and may be written in any order once 6 has landed; 13–14 close the item. Every task's
`verify:` names a standing artifact or declares one of the four exception kinds with its reason.

**One property of that ordering, said out loud so the builder is not surprised by it.** Tasks 3, 4, 5,
6, 7 and 11 each declare a `verify:` naming a test that a LATER task authors — the library lands
first, its batteries second, which is the only order in which a battery can assert against real code.
The consequence for a builder finishing Task 3 is that nothing but the floor is runnable for it yet;
that is intended, not an omission. It refuses nothing: D10a checks only that each declaration is
well-formed, and D10b runs at `building → done`, after every task has landed. Do not reorder the plan
to make each task self-verifying — that would put a battery in front of the code it measures and
invert the WI-149 rule about deriving an oracle from what the test itself created.

- [x] **Task 1 — Capture the pre-build baselines, before the first edit that moves them.** Run the
  floor command and record its case count; run EVERY pinned derivation named here — the list, not a
  count, is the obligation, and Task 14 re-checks exactly what this task recorded — and record their values
  (`functions_reserializing_parsed_frontmatter` = 4, `functions_parsing_then_writing - writers` =
  `{write_markdown_file}`, `non_completed_write_sites` over `PACKAGE_ROOT` = 8, over `person.py` = 8
  with its five qualnames, `base_repository_subclasses` = 4, `load_file_implementations` = 3). Write
  all of them into the Build Log. Assert nothing on the numbers; they are the left-hand side later
  tasks compare against, and a baseline nobody captured is a value no check holds.
  verify: baseline — an informational capture whose only artifact is the Build Log; no later check asserts the recorded numbers, only that the pins did not move.

- [x] **Task 2 — Declare and set the provenance stamp, and add the resolution function.** Add
  `_source_path: Optional[Path] = PrivateAttr(default=None)` to
  `obsidian_schemas/models.py:BaseEntity` with the comment block from
  Design §1, importing `PrivateAttr` and `Path`. Set it at the one parse site that holds a path,
  `obsidian_schemas/parser.py:parse_markdown_file`, on the `entity is not None` arm only. Add
  `_resolve_write_target` from Design §2 to `BaseRepository`, beside `get_file_path` — the pure
  resolution only; routing the nine write paths through it is Tasks 3–5, and the method is added
  here so the stamp's READ direction can be asserted end-to-end in this task rather than left to a
  later one. Write
  `test_the_parse_stamps_provenance_and_the_stamp_cannot_reach_a_note` in the new module
  `tests/test_provenance_write_seam.py`: a note parsed from a file carries the stamp; the same bytes
  through `parse_markdown_content` carry `None`; `model_to_frontmatter` of a stamped entity contains
  no key whose value is a path and no `_source_path` key; a `write_markdown_file` of a stamped entity
  produces frontmatter with the same key set as the unstamped one; `model_copy()` preserves the stamp
  and `model_validate(model_dump())` drops it. The oracle for the key-set arm is derived from the
  entity the test itself built, never from a hardcoded field list. Then the READ direction, which is
  M2 and is the arm this check did not have: plant TWO person notes A and B in the temp vault where
  A's OWN frontmatter declares `_source_path: <B's path>` (written as bytes, never through
  `repo.save`), parse A with `parse_markdown_file`, and assert that `_resolve_write_target` answers
  A's own path, that `getattr(entity, "_source_path")` — verbatim the accessor
  `_resolve_write_target` reads — is A's path and is not B's, and that NOTHING the seam reads answers
  B. Where the forged key ENDED UP is an observation and not an assertion: record in the Build Log
  whether pydantic v2 retained it (`entity.model_extra`) or dropped it at `model_validate` time, and
  assert only the property — the accessor answers the parsed path and the forged value is not
  reachable through it. Pinning the RETENTION would make this arm RED against correct code if a
  pydantic release stops keeping underscore-prefixed extras, and M2's property holds either way. Do NOT
  assert anything about where a `save` of A lands: `save` is not routed through the seam until Task
  3, and the end-to-end write consequence is AC-1's sweep (Task 9). Both oracles are the exact paths
  the test itself created, never a prefix, substring or layout of the tree. Also write
  `test_the_seam_returns_the_stamp_only_inside_this_vault` in the same module: a stamped entity
  resolves to its own file; an entity with no stamp resolves to `None`; an entity stamped inside a
  DIFFERENT temp vault resolves to `None` against this repository; a stamped-but-deleted file still
  resolves (existence is not part of the answer).
  verify: test_the_parse_stamps_provenance_and_the_stamp_cannot_reach_a_note test_the_seam_returns_the_stamp_only_inside_this_vault

- [x] **Task 3 — Route `save` and `update_fields` through the seam.** Change
  `BaseRepository.save` to the CREATE-fallback shape (resolved-or-derived, with the WARNING emitted
  before the write when provenance is absent and the derived target exists) and
  `BaseRepository.update_fields` to the REFUSE-fallback shape (guarded rebinding, then today's
  `ValueError`). In `update_fields` specifically, write that shape with the `resolved` binding Design
  §2's fallback shape 2 shows — `resolved = self._resolve_write_target(entity)` then
  `file_path = resolved` — because Task 6's name-change refusal reads `resolved` and a builder who
  collapses the two names here has to reopen the head of the method later. The five body-writers need no
  such binding. Do not touch `save`'s gate, `overwrite` or `_adopt`, and do not add a
  second resolution site — `_resolve_write_target` landed in Task 2 and is called, never re-spelled.
  ONE line of `save`'s logging DOES change, and it is the M4 defect one method over: today's
  `logger.info(f"Saved {self.type_name}: {filename}")`
  (`obsidian_schemas/repositories/base.py:BaseRepository.save:411`) names `filename`, the
  NAME-DERIVED `@{name}.md` (`:392`) — under the resolved-or-derived shape the write can land
  somewhere else entirely while the log still claims that filename. Log the file actually written
  (`file_path.name`, after the resolution), for exactly the reason the `## Approach` WARNING exists:
  this class has to be *reconstructable from a consumer's logs*, and a log naming a file the call did
  not write is worse than no log. No test pins that string (grep `Saved ` over `tests/` → zero hits),
  so it costs one line. Task 5 applies the same one-line change to both overrides
  (`obsidian_schemas/repositories/book.py:BookRepository.save:183` and Meeting's counterpart).
  verify: test_no_library_write_can_fork_a_person_note

- [x] **Task 4 — Route the five mutating body-writers.** Replace the identical
  `file_path = self.get_file_path(person.name)` opener at
  `obsidian_schemas/repositories/person.py` `:1403`, `:1522`, `:1653`, `:1719`, `:1793` with the
  REFUSE-fallback shape. Leave every `ValueError`, every `.exists()` check, every falsy return and
  every `return False` exactly where it is — `tests/test_loud_fail_write.py` classifies those sites
  by (function, ordinal) and a new or moved falsy return is RED. Leave
  `PersonRepository._get_body_content` alone and add one comment line there naming it as the
  read-side sibling that is deliberately outside the write seam.
  verify: test_no_library_write_can_fork_a_person_note

- [x] **Task 5 — Route Book's and Meeting's `save` overrides.** Apply the CREATE-fallback shape to
  `obsidian_schemas/repositories/book.py:BookRepository.save` and
  `obsidian_schemas/repositories/meeting.py:MeetingRepository.save`, keeping
  `self._get_file_name(entity)` as the fallback expression and both `_adopt` calls unchanged. Each
  override's INFO line takes Task 3's one-line change — log the file actually written
  (`file_path.name`) rather than the derived `filename`
  (`obsidian_schemas/repositories/book.py:BookRepository.save:183` and Meeting's counterpart), since
  these two derive their target from `_get_file_name` and so can now write somewhere the derived name
  does not describe. Neither override starts calling `super().save()`: collapsing them is a different
  item and would move the population every criterion here quantifies over.
  verify: test_no_library_write_can_fork_a_person_note

- [x] **Task 6 — Ship the rename door, contained and audited, and call it from `update_fields`.** Add
  `BaseRepository.rename_note` exactly as Design §2 specifies, including the idempotent branch, the
  case-only two-step through a source-derived staging name, the re-stamp before the alias write, the
  delegation of the alias append to `writer.update_frontmatter_field`, and the single `_adopt`.
  **BRANCH ON FILE IDENTITY, NEVER ON THE PATH STRING:** the idempotent branch's test is
  `(destination.parent.resolve(), destination.name) == (source.parent.resolve(), source.name)`, NOT
  `destination == source`. `vault_io.move_note` returns `_resolved(dest)`
  (`obsidian_schemas/vault_io.py:_resolved:234-243`, `obsidian_schemas/vault_io.py:_move_locked:783`),
  so a stamp written by an earlier rename is RESOLVED, while `self.vault_path` is unresolved
  (`obsidian_schemas/repositories/base.py:_resolve_vault_path:104-114`) — under macOS's `/var` →
  `/private/var` the string compare answers False for the same file, the door falls through to the
  case-only two-step, and the "idempotent" re-run performs two real moves. Resolve each side's PARENT
  and compare the RAW `.name`: resolving the DIRECTORY normalizes the spellings the environment
  supplies, leaving `.name` unnormalized is what keeps the case-only branch reachable, and resolving
  the parent rather than the whole path is what keeps a final-component symlink out of the branch
  decision — a symlinked source is door 3's refusal and a symlinked destination is M1's question
  (Design §2, "Which branch fires is decided by WHICH FILE each side names"). The case-only branch keeps
  `destination.exists() and source.samefile(destination)` as its own test — `samefile` is the inode
  test and raises on a missing operand, which is what the `exists()` guard is for.
  **DO NOT ADD AN ALIAS-REPAIR ARM:** after a rename whose move committed and whose alias write
  raised, a re-run appends nothing (provenance has moved, so `old_stem == new_stem`) and that is the
  specified behaviour, not a bug to fix here — Task 10 asserts `aliases` UNCHANGED on the second call
  and asserts the whole residual directly, and `## Edge Cases` names the caller-side recovery.
  **DO NOT PRE-CHECK THE DESTINATION'S OCCUPANCY, IN THE DOOR OR IN `update_fields`, AND DO NOT REORDER
  `update_fields` TO MOVE BEFORE IT WRITES:** an occupied `@{new_name}.md` reaches `os.link` and comes
  back as `NoteAlreadyExists` (`obsidian_schemas/vault_io.py:_move_locked:759-771`), which is the
  stronger answer and is the only authority on occupancy this package has — a pre-check is check-then-act
  and would leave the same residual at a smaller window (Design §2's precondition table, and the
  COMPLEMENT rule beneath it, which is the authority for what that residual IS and what the caller does
  about it). The reorder is worse than unchosen, it is UNAVAILABLE: the door appends the alias through
  `update_frontmatter_field(moved, …)` in the same call, which moves the file's `st_mtime_ns` and
  `st_size`, so a content write carrying this frame's `precondition=stamp` (`base.py:449`) would then
  MISMATCH and `vault_io.write_note` would refuse every SUCCESSFUL rename with `ExternalWriteConflict`
  (`obsidian_schemas/vault_io.py:write_note:685-698`). Write, then move, then rebind — which is also
  what AC-2's signed `why` prescribes in its own words. Task 10 asserts the accepted residual directly,
  so a builder who "fixes" it by pre-checking turns that arm RED on the raised LEAF.
  **IMPORT THE ALIAS WRITER AS A BARE NAME:** extend
  `obsidian_schemas/repositories/base.py:20`'s existing `from ..writer import write_markdown_file,
  write_frontmatter` with `update_frontmatter_field` and call it unqualified. Two things key on that
  spelling: AC-5's bucket (ii) enumerates BARE-NAME calls to a member of `path_taking_writer_names`
  (Design §4), and Task 10 patches `obsidian_schemas.repositories.base.update_frontmatter_field` to
  drive the half-failure residual — a `writer.update_frontmatter_field(...)` spelling moves both.
  Four clauses of that body are the threat model's required mitigations and are not optional (a fifth
  and a sixth, M7 and M8, are required too and land in `update_fields`' pre-write refusal further down
  this task — its first and second clause respectively — not in the door).
  **(M1) Contain the destination:** immediately after `destination = self.vault_path / new_filename`,
  raise `ValueError` unless `destination.resolve().is_relative_to(self.vault_path.resolve())`, with
  an `OSError`/`ValueError` out of the resolve treated as NOT contained, and raise BEFORE any
  `vault_io.move_note` call — resolved and never string-compared, because a dangling in-vault symlink
  is an escape the string cannot show. **(M3) Keep the staging name in the `.md` namespace:** the
  case-only branch stages through `source.with_name(destination.stem + ".rename-tmp.md")`, not
  `destination.name + ".rename-tmp"`, so an interrupted rename leaves a note all three `file_pattern`
  globs, `lint_vault` and Obsidian still see. **(M4) Name both ends in the audit line:**
  `logger.info("Renamed %s note from %s to %s", self.type_name, source.name, moved.name)` — the
  source as well as the destination, since after this item `update_fields` moves a file permanently
  on every name change. **(M6) Fail closed when the write guard is not enforcing:** bind
  `mode = vault_io.guard_mode()` immediately after M1's containment block and, unless it equals
  `"enforce"`, `raise ValueError` naming the mode — before any `vault_io.move_note` call, beside the
  door's other precondition refusals. Read it through `vault_io.guard_mode()` and NEVER through
  `os.environ`: `base.py:9` already imports `os` and that spelling would build, but
  `obsidian_schemas/vault_io.py:_env_setting:104-115` reserves environment access to itself in writing
  and `vault_io` is already imported at `base.py:22`, so the call costs no import. Without this clause
  every occupied-destination refusal this item relies on is conditional on an environment variable:
  under `OBSIDIAN_SCHEMAS_WRITE_GUARD=observe`,
  `obsidian_schemas/vault_io.py:_move_locked:757-771` does `os.replace(source, target)` instead of
  raising `NoteAlreadyExists`, destroying the occupied note and returning the destination as a
  success, so the door would alias, `_adopt` and log a rename that overwrote a third party (WI-004's
  declared residual R9, `docs/concurrent-access.md:649-656`, acceptable while door 3 had one
  quarantine caller and not once this item drives it on every name change in three `-e` consumers).
  Do NOT widen this to `save`, the body-writers or `create_note`'s identical arm — that arm is
  AC-1(f)'s and stays WI-004's (Design §2, "M6's exact bound"). **THE SAME CONDITION REFUSES EARLIER IN
  `update_fields`, IN THE ARM BELOW:** the widened predicate is stated there, because a name change
  that reaches the door under `observe` would otherwise commit its content write first and raise after
  it. Then replace `update_fields`' alias-append block (`base.py:454-459`) with a
  door call placed **OUTSIDE the `with vault_io.note_lock(file_path)` block** — after the block has
  exited, so after `vault_io.write_note` has COMMITTED (`base.py:490`), and before the reload
  (`base.py:493`) — rebinding `file_path` to the door's return. NOT inside the lock: `move_note`
  acquires two locks in a global sorted order and `rename_note`'s `update_frontmatter_field` acquires
  a third, so a held outer lock is the one configuration that order cannot defend (Design §2, ordering
  decision 5 — reentrancy excuses re-acquisition, never ordering). Compose the destination as
  `f"@{new_name}.md"`, the caller's rule and not the door's: it is correct for every type that can
  reach this line (`BaseRepository`, `PersonRepository` and `CompanyRepository` all derive
  `@{name}.md`), and `Book`/`Meeting` cannot reach it because the M7 disjunct below REFUSES them —
  not because the trigger declines to fire, which it does not (Design §2, "`update_fields` composes
  `f"@{new_name}.md"` for every entity type it lets through"). Hand the door the caller's own
  `entity` parameter, never a re-parsed or freshly-constructed view: that is the object the door
  re-stamps and `_adopt`s, and AC-2(e)/(g) turn on it. Keep the name-change condition
  (`"name" in updates and updates["name"] != frontmatter.get("name", "")`)
  as the trigger — it reads `frontmatter`, which is bound inside the lock, so capture the decision (and
  the new name) before the block exits rather than re-parsing after it. **REFUSE A NAME CHANGE THE DOOR
  CANNOT COMPLETE, BEFORE ANYTHING IS WRITTEN:** read the `resolved` name Task 3 already bound at the top
  of the method (Design §2's fallback shape 2 keeps that name precisely so this arm can read it — do not
  add a second `_resolve_write_target` call here) and, inside the lock immediately after the name-change
  decision is computed and BEFORE
  `gate_write`, `write_frontmatter` or `vault_io.write_note` are reached, `raise ValueError` when the
  update changes the name and the door's PRECONDITIONS do not hold — `resolved is None` **or**
  `vault_io.guard_mode() != "enforce"` (M6) **or** `"name" not in type(entity).model_fields` (M7) —
  naming the method, the requested new name, and WHICH
  precondition failed: that a name change needs the provenance a move is resolved from, that the
  write guard is not enforcing, or that this entity's type declares no `name` and so derives no
  `@{name}.md` destination. All THREE disjuncts, not one and not two: a name change that reaches the door
  under `observe` fails for the same structural reason a no-provenance one does, and answering only the
  remembered conjunct leaves the next precondition as the next round's finding — which is precisely how
  M7 arrived. **And the ARM is two CLAUSES, not one**: everything in this paragraph is `if renaming and
  (…)`, so it is never evaluated for a delta carrying no `name` key — which is exactly the gap M8
  arrived through, because `Book`'s and `Meeting`'s filename rules are not made of `name`. The second
  clause is stated below under **(M8)** and both are raised from the same place, before anything is
  gated or written (Design §2, "The pre-write arm has TWO obligations and not one"). Design §2's
  precondition table is the authority for which of the door's refusal arms belong in this test and
  which stay the syscall's — read it rather than extending the disjunction by guess; in particular do
  NOT add a containment conjunct for M1 here, because for the two types that DECLARE `name`
  `gate_write` on the delta already refuses a `new_name` carrying a path separator before any write and
  a `ValueError` raised earlier would degrade a `NameGateRefusal` carrying its `pattern` — while for
  every type that wall passes through, the M7 disjunct is what closes the same row, on the ground that
  the type derives no `@{name}.md` at all rather than on containment (Design §2, the M1 row and the
  delegation rule beneath the table). **(M7) Refuse a `name` delta on a type that does not declare
  `name`:** the third disjunct is `"name" not in type(entity).model_fields` — the DECLARED field, read
  off the CLASS (`type(entity)`, never the instance: `obsidian_schemas/writer.py:108`'s own comment
  reserves that spelling for the pydantic v2.11+ deprecation, and an instance or `hasattr` spelling
  would answer differently for a note storing `name:` as an EXTRA, which is exactly the case that must
  still refuse) and never a type-name comparison, the same keying ordering decision 3 already uses for
  `aliases`; it is needed because `gate_write` hands a `name` delta straight back UNVALIDATED for every
  `declared_type` that is neither `person` nor `company` (`obsidian_schemas/name_gate.py:gate_write:319-344`,
  whose own comment reads *"a Book write is gated and handed straight back"*) while the trigger reads the
  CALLER's dict against the NOTE's frontmatter and consults the model nowhere — so without it a stamped
  Book or Meeting entity handed `{"name": <anything>}` has `frontmatter.get("name", "")` answer `""`,
  sets `renaming` True, passes the other two disjuncts, COMMITS the ungated caller-supplied `name:` at
  `base.py:490`, and only then raises out of `rename_note` (`@x/y.md` → `WriteFailedError` from
  `os.link` against a missing parent, `obsidian_schemas/vault_io.py:_move_locked:772-773`;
  `@a/../../x.md` → M1's containment `ValueError`), which is the committed-write-then-raise residual
  this whole arm exists to prevent and which the new detector cannot see because it fires only on
  `vf.entity_type == "person"`. Task 3's `resolved`-first binding is what makes that frame reachable at
  all — today's `get_file_path(getattr(entity, "name", ""))` opener answers `None` for a Book and raises
  above the lock (`base.py:437-441`, `:354-365`). Do NOT instead compose the destination with
  `self._get_file_name(entity)` for those two types: that ships a second filename rule through the door
  with no live direction table behind it (`## Scope Boundary`). **(M8) Refuse a delta that moves the
  entity type's OWN filename rule when no rename will follow it — the arm's SECOND CLAUSE, which fires
  where `renaming` is FALSE:** bind `derive = getattr(self, "_get_file_name", None)` and, when it is not
  `None` and `not renaming`, project the delta onto the entity's declared fields —
  `projected = entity.model_copy(update={k: v for k, v in updates.items() if k in
  type(entity).model_fields})`, which preserves the private stamp (Design §1, "Survives `model_copy`")
  and keeps an undeclared caller key out of a comparison it could not have moved — and `raise
  ValueError` naming the METHOD, the field(s) at issue and THIS precondition when `derive(projected) !=
  derive(entity)`. Compute `derive(entity)` FIRST and outside any `try`; wrap only `derive(projected)`,
  and treat ANY exception out of it as *the rule cannot be recomputed over this delta* and raise the
  same `ValueError` — `model_copy(update=…)` does not validate, so a delta supplying a non-string
  `title` or a non-list `topics` would otherwise leak an `AttributeError`/`TypeError` out of
  `_get_file_name`; fail closed, the direction M1 takes with an `OSError` out of its own resolve.
  Read it off `self` and never off a type list: `_get_file_name` is declared on exactly
  `obsidian_schemas/repositories/book.py:BookRepository._get_file_name:340` and
  `obsidian_schemas/repositories/meeting.py:MeetingRepository._get_file_name:208`, so `derive` is `None`
  for `BaseRepository`, `PersonRepository` and `CompanyRepository` and the clause is STRUCTURALLY inert
  for the two types whose rule is `@{name}.md`. Compare DELTA-RELATIVELY (`derive(projected)` against
  `derive(entity)`) and NEVER against `file_path.name`: the latter spelling refuses every write to an
  already-divergent Book or Meeting note, which is the live "book-titled file holding a person note"
  class this item exists to repair. Keep the `not renaming` conjunct: a `name` delta on a type that
  declares `name` belongs to the rename branch, which reconciles the rule by moving the file, and a
  `name` delta on a type that does not is M7's clause one line up. It is needed because the rename-side
  predicate is the WHOLE of `if renaming and (…)` while `Book`'s filename is made of `title` and
  `author` (`book.py:346`, `:350-353`) and `Meeting`'s of `date`, `topics`, `attendees` and
  `meeting_id` (`meeting.py:216`, `:219-226`) — six DECLARED fields
  (`obsidian_schemas/models.py:Book.title:160`, `:author:161`;
  `obsidian_schemas/models.py:Meeting:260-263`) — so without it a stamped Book handed `{"title": "New
  Title"}` leaves `renaming` False, evaluates no disjunct at all, is handed back UNVALIDATED by
  `gate_write` (`obsidian_schemas/name_gate.py:gate_write:319-344`), COMMITS at `base.py:490`, moves
  nothing, records no alias for the stem it is leaving behind and raises nothing — the item's own
  type-general divergence, manufactured silently, and invisible to Task 11's `vf.entity_type ==
  "person"` arm. Do NOT instead rename the note by composing `self._get_file_name(entity)`: the rule is
  recomputed here only to COMPARE, never to build a path, and the door learns no second filename rule
  (`## Scope Boundary`). Without the REFUSAL
  ARM AS A WHOLE the residual is the same shape reached two ways, and both are what the arm exists to
  prevent: with any one of its three RENAME-SIDE disjuncts missing the sequence commits the new name at
  `base.py:490` and only then hits `rename_note`'s raise, leaving a divergent un-aliased note and an
  exception after a successful write; with its SECOND CLAUSE missing the sequence commits at the same
  line, reaches no door at all and raises NOTHING, leaving the same divergent un-aliased note in
  silence. With the arm entire, in both directions, the frame has performed one READ and the note is
  byte-identical. Test the STORED value and not `"name" in updates`: a PATCH body
  echoing an unchanged name must still write (Design §2, "The no-provenance name change refuses BEFORE
  the write", which also carries the precondition table and records why re-stamping from
  `get_file_path` is the wrong fix). **RECONCILE THE
  ALIAS LIST ON THIS SIDE:** where the committed `updates` carried an `aliases` key, mirror the committed
  value onto the entity (`entity.aliases = frontmatter["aliases"]`) before the door call, captured inside
  the lock with the rest of the rename decision — otherwise the door's in-memory list is the parsed one
  and overwrites the caller's (Design §2, "Which `aliases` list wins"). Keyed on the key this write
  introduced, never on a type name, and GATED ON `renaming`: the mirror's only consumer is the door, so
  an ungated `if "aliases" in updates:` would add a caller-visible in-place mutation to every non-rename
  update as well, which today's `update_fields` never performs. The alias append itself moves INTO the
  door, where its two halves are deliberately asymmetric: the FILE write through
  `writer.update_frontmatter_field` is unconditional (`aliases:` is Obsidian's own type-agnostic key)
  while the in-memory assignment stays guarded by `hasattr(entity, "aliases")`, so the door never mints
  an undeclared extra on a `Company`, `Book` or `Meeting` entity (Design §2, ordering decision 3).
  `rename_note` must contain NO falsy return and NO `parse_frontmatter` call — which is also why the
  alias reconciliation above lives in `update_fields`, where `frontmatter` is already bound, and not in
  the door, whose membership of `functions_parsing_then_writing` is pinned by set equality.
  verify: test_a_person_note_is_renamed_only_through_the_one_door_and_stays_reachable

- [x] **Task 7 — Build the AC-5 derivation in `tests/derivations.py`.** Add `WriteTargetSite`,
  `SEAM_FUNCTION`, `path_taking_writer_names` and `write_target_buckets` per Design §4, reusing
  `_is_write_call`, `_own_body_nodes`, `_names_in`, `_assign_targets_name` and `_pos` rather than
  re-implementing them, and extending the taint propagation with the `with … as` hop and the
  ordering-aware rebinding clause. Add `door_calls_inside_note_lock` in the same module (Design §4's
  sketch): every call to `move_note`, to a member of `path_taking_writer_names`, or to a repository
  method that itself calls `move_note` — that third clause DERIVED from
  `functions_calling(files, "move_note")` rather than named, which is what makes it reach
  `update_fields`' own `self.rename_note(...)` call — lexically nested
  inside a `with` whose items mention `note_lock`. The single-path doors `write_note`/`create_note` are
  deliberately NOT collected, since `write_markdown_file` must call them inside its own lock
  (`obsidian_schemas/writer.py:317`, `:319`) and collecting them would make the scan RED against
  shipped code. This is the ONLY module in the repo that may name `ast`.
  verify: test_every_write_site_resolves_its_target_through_the_one_seam test_a_person_note_is_renamed_only_through_the_one_door_and_stays_reachable

- [x] **Task 8 — Write AC-5's check and its planted-escape battery.** New module
  `tests/test_write_target_seam_wall.py` holding
  `test_every_write_site_resolves_its_target_through_the_one_seam` (zero-arg, raising, preceded by
  `ensure_project_interpreter(__file__)`). The live half runs `write_target_buckets` over
  `python_files_under(PACKAGE_ROOT)` and asserts the two bucket sets equal the fourteen qualnames
  Design §4 names, that no site classifies `None`, and that the scan is non-vacuous. The battery
  plants source files in a temp directory and drives them through the SAME function — REFUSED: a
  name-derived write in both spellings (`self.vault_path / f"@{name}.md"`, and a helper returning
  one); a bare-expression-statement call to the seam beside a separately-derived write; the return
  bound and unused (`_ = self._resolve_write_target(entity)`); the UNCONDITIONAL rebinding shape from
  Design §4; the resolved value passed as a non-path argument while the path argument is separately
  derived; a write call with no positional argument. ACCEPTED: a module-level path-taking leaf; a
  seam-routed writer; a read-only function using `get_file_path`; a function naming
  `_resolve_write_target` only in a comment or docstring; and — the load-bearing one — a seam-routed
  writer whose documented fallback arm REBINDS THE SAME LOCAL inside an `if` testing it. Each planted
  shape's oracle is the exact source the test itself wrote, never a substring of the tree.
  verify: test_every_write_site_resolves_its_target_through_the_one_seam

- [x] **Task 9 — Write AC-1's sweep.** In `tests/test_provenance_write_seam.py`, add
  `test_no_library_write_can_fork_a_person_note` (zero-arg, raising). Materialize the frozen corpus
  into a temp vault with `materialize_vault`; DERIVE the subject set as the union of the two
  manifest predicates (divergent: `declared_type == "person"`, a declared `fields` mapping — SKIP a
  `NoteSpec` with none — and raw stem-less-`@` ≠ raw `fields["name"]`; name-sharing: every person
  `NoteSpec` whose declared `name:` equals another's), never from `shape_classes`. PLANT, by writing
  bytes directly (never `repo.save`, never `write_markdown_file` — half the corpus is gate-refused):
  the sentinel-exempt subject `@447700900123.md` carrying `name: "+447700900123"` and a non-empty
  `phones:`; a divergent note whose canonical `@{name}.md` is FREE; a genuinely-new entity; a
  round-tripped entity plus an occupied `@{name}.md`; and one COLLIDING GROUP per type for Book and
  Meeting — two notes whose `_get_file_name` output is identical, one living AT it and one elsewhere.
  Bind each subject with `repo._load_file(path)`, which parses from the FILE and records the
  derivation stamp door 2u needs — never `repo.get(name)`. Apply each path's minimal mutation from
  the table in `## Verification`, touching none of that type's filename-deriving fields. Assert
  (a) the vault's filename SET is unchanged, (b) the changed bytes are in the file the subject was
  parsed from — for every member of a colliding group independently and for the divergent member of
  each planted Book/Meeting group by name, (c) every other member of that group is byte-identical.
  For the `save` cell only, apply the DOOR PREDICATE first and expect `NameGateRefusal` with the
  raised `pattern` and no file changed where it fires. Then arms (d)–(h) as AC-1 states them, with
  (f)'s WARNING captured through `tests/support.py:captured_logs` and its `NoteAlreadyExists`
  asserted as today's unchanged behaviour. **(g)'s "with no vault walk triggered" has one stated
  oracle so a builder does not invent a second** *(third spec-review round, non-blocking note 6)*:
  construct the repository with `auto_load=False`, bind the subject with `repo._load_file(path)`
  (which does not set the flag), perform the writes, and assert `repo._loaded` is still False
  afterwards. Nothing on the seam's write path calls `_ensure_loaded`
  (`obsidian_schemas/repositories/base.py:_ensure_loaded:210-213`), and the flag goes True only inside
  `load()` itself (`obsidian_schemas/repositories/base.py:load:237`, `:254`) or in `refresh()`'s
  clobber-refusal restore, which calls `load()` one line earlier
  (`obsidian_schemas/repositories/base.py:refresh:545-562`) — so the flag IS the walk. Do not patch
  `Path.glob` to count calls: that oracle grades a spelling of the walk rather than its absence. Assert the invocation table's keys plus
  `BaseRepository.rename_note` EQUAL `write_target_buckets`' seam set.
  verify: test_no_library_write_can_fork_a_person_note

- [x] **Task 10 — Write AC-2's door battery.** In the same module, add
  `test_a_person_note_is_renamed_only_through_the_one_door_and_stays_reachable` (zero-arg, raising)
  covering arms (a)–(h): resolution through the seam and reachability under both names via `get`,
  `get_by_email` and the alias route; `NoteAlreadyExists` with both files byte-identical; the
  `update_fields`-with-a-name-change path plus the derived scan asserting
  `functions_calling(python_files_under(PACKAGE_ROOT), "move_note") ==
  {FunctionId("obsidian_schemas/repositories/base.py", "BaseRepository.rename_note")}`; the symlink
  refusal; the write-follows-the-file arm in BOTH directions (after success it lands in the new file
  and the old stem is not recreated; after a refusal it lands in the unmoved original); the collision
  arm over the corpus `Quillam` pair; the re-stamped reload; and the case-only arm with the
  filesystem PROBE described in `## Edge Cases`. **One rule over every arm in this check, because the
  door answers in RESOLVED paths:** `rename_note` returns `move_note`'s `_resolved(dest)` and stamps
  that value, so any assertion comparing a path the door RETURNED or STAMPED against a path the TEST
  created compares them `.resolve()`d on both sides (or with `Path.samefile`), never by raw `==` —
  exactly the normalization `tests/test_lint_vault_fix_rules.py:_temp_vault:158-191` already performs
  for the same reason. Assertions over the vault's filename SET are unaffected: those read `.name`
  values out of one directory listing. Two further arms, neither of them an AC-2 arm (AC-2 is
  signed and gains none) and both of them properties this document leans on elsewhere.
  **IDEMPOTENCE, AFTER A REAL MOVE AND ON A VAULT PATH WHOSE SPELLING THE TEST ITSELF MADE DIVERGENT**
  — the ORDER is the arm. Drive one REAL rename (`@Old.md` → `@New.md`), which is what re-stamps the
  entity with `move_note`'s RESOLVED answer, and only THEN call `rename_note(entity, "@New.md")` — the
  filename it now has — and pin that second call: no `move_note` call recorded (through the same
  recording delegate M3's arm installs), the vault's filename SET unchanged, the note's `aliases`
  unchanged (nothing appended twice), and the stamp still naming that file. Calling the door twice on
  a filename it already had from the START would NOT test this: there the stamp is `_load_file`'s and
  carries the repository's own spelling, so even a raw string compare fires and the arm is vacuous.
  **The oracle's precondition is planted, not inherited from the platform** *(third spec-review
  round's blocking finding 2)*: the divergence exists only where `repo.vault_path`'s spelling differs
  from its resolved form, so make them differ with a path the test built — create a real
  sub-directory inside the temp root and construct the repository with
  `vault_path = <root> / <that sub-directory> / ".."`, a spelling that resolves to the root on every
  platform — then assert, before the arm runs, that `repo.vault_path != repo.vault_path.resolve()`, so
  the arm cannot pass vacuously. Do NOT reach for macOS's `/var` → `/private/var` (which
  `tests/support.py:temp_dir:31-37` supplies unresolved under `$TMPDIR`) as the source of the
  divergence: it is the naturally occurring instance of exactly this shape and it is why the defect is
  live here, but a check that depends on it is green-by-environment on one platform and vacuous on
  another — WI-149's rule. Against a door that compares `destination == source` this arm is RED (the
  second call takes the case-only two-step and records TWO `move_note` calls through a staging name);
  against the specified file-identity key it is green.
  **THE HALF-FAILED RENAME'S RESIDUAL, AND WHAT THE RE-RUN DOES WITH IT** — the other half of the same
  branch, asserted rather than asserted-about *(third spec-review round's blocking finding 1)*. Patch
  `obsidian_schemas.repositories.base.update_frontmatter_field` with a delegate that RAISES on its
  first call (restored in a `finally`, the same idiom as M3's recorder), drive
  `rename_note(entity, "@New.md")` on a note at `@Old.md`, and assert the residual Design §2's re-run
  table declares: the exception propagates, the file IS at `@New.md`, `@Old.md` is gone, the stamp
  names `@New.md`, and the note's `aliases` does NOT contain the old stem. Then restore the real
  writer, re-run `rename_note(entity, "@New.md")`, and assert the re-run is a no-op that repairs
  NOTHING: no `move_note` call recorded, filename set unchanged, and `aliases` STILL without the old
  stem. Finally assert the documented recovery works —
  `repo.update_fields(entity, {"aliases": [<the old stem>]})` puts it back and moves no file. That
  sequence is the `## Edge Cases` Decision and the `## Risk Analysis` mitigation made falsifiable;
  before this round both claimed the re-run performed the repair, and nothing in the battery could
  have contradicted them.
  **THE OCCUPIED DESTINATION, REACHED THROUGH `update_fields`** — the accepted residual, ASSERTED
  rather than described *(fourth spec-review round's blocking finding, 2026-09-26)*, and the arm no
  other cell in this battery reaches: AC-2(b)'s drives the door DIRECTLY, M6's `update_fields` half runs
  under `observe` and so refuses before the write, and M7's subject is a Book. Set
  `OBSIDIAN_SCHEMAS_WRITE_GUARD` to `"enforce"` explicitly through `tests/support.py:patcher:73` for the
  whole arm, for the M6 arm's own reason — an ambient `observe` would make it pass on the wrong refusal
  (WI-149). Plant TWO person notes as BYTES: subject A at `@Old.md` carrying `name: Old` and a body, and
  a DIFFERENT note B at `@New.md` carrying its own distinct `name:` and body; capture B's bytes and A's
  bytes. Bind A with `repo._load_file(<A's path>)` so it is stamped. Call
  `repo.update_fields(entity_A, {"name": "New"})` and assert the residual exactly as Design §2's
  complement rule states it: the raised exception is `NoteAlreadyExists` — the LEAF, and the
  discrimination that matters, because a bare `ValueError` would mean the method or the door PRE-CHECKED
  the destination, which Task 6 forbids and which `NoteAlreadyExists` being a `LoudFailError` (hence a
  `ValueError`) would otherwise hide; the vault's filename SET is unchanged; B is BYTE-IDENTICAL to the
  bytes the test wrote; A's file now parses with `name: New` while still sitting at `@Old.md` — which is
  the assertion that pins the write as COMMITTED rather than assumed, and the one an implementation that
  refused early would fail; A's `aliases` does NOT contain `Old`; and `entity_A`'s stamp still names
  `@Old.md` (the door raised above its re-stamp), compared `.resolve()`d on both sides per this check's
  one rule. Then the two recovery arms, which are what make the Decision falsifiable rather than
  narrative. NOT-A-REPAIR: with B still in place, call `repo.update_fields(entity_A, {"name": "New"})` a
  SECOND time and assert it does NOT raise, records NO `move_note` call (through the same recording
  delegate M3's arm installs), and leaves the filename SET unchanged — because the note's frontmatter
  now already carries `New`, so `renaming` is False. THE DOCUMENTED RECOVERY: remove B (the direction
  table's MERGE, performed here by the test as the conductor would by hand), call
  `repo.rename_note(entity_A, "@New.md")` DIRECTLY, and assert it MOVES — `@New.md` holds A's bytes,
  `@Old.md` is gone, the moved note's `aliases` now carries `Old`, and the returned path and the stamp
  both name the new file. Every oracle is the exact path and the exact bytes the test itself wrote.
  **THE NO-PROVENANCE NAME CHANGE, REFUSED BEFORE THE WRITE** — the arm no existing battery reaches
  (Task 9's `update_fields` cell carries no `name` key; AC-2's name-change arm binds a
  `_load_file`-stamped subject). Bind a subject the repository CAN answer by name but whose entity
  carries no stamp — parse it with `parse_markdown_content` over bytes the test itself read, so
  `_resolve_write_target` answers `None` while `get_file_path` answers the file — then call
  `repo.update_fields(entity, {"name": <a DIFFERENT name>, "title": "…"})` and assert: `ValueError`
  raised; the vault's filename SET unchanged; and the subject's file BYTE-IDENTICAL to what the test
  wrote, which is the assertion that distinguishes refusing before the write from refusing after it.
  Then the arm that proves the refusal is not "refuse every unstamped update": the SAME unstamped entity
  through `repo.update_fields(entity, {"title": "…"})` SUCCEEDS and the change lands in that file, and
  `repo.update_fields(entity, {"name": <the name it ALREADY has>})` also succeeds, which is the PATCH
  echo shape Prerequisites 7 names. Every oracle is the exact path and exact bytes the test itself
  created. Also pin the alias reconciliation while a stamped subject is in hand: `update_fields(entity,
  {"name": <new>, "aliases": [<a value not on the entity>]})` leaves the moved note's `aliases`
  containing BOTH that caller-supplied value and the old stem, which is what fails a door handed the
  stale parsed list.
  **THE LOCK-ORDERING RULE, STRUCTURALLY** — assert `door_calls_inside_note_lock` over
  `python_files_under(PACKAGE_ROOT)` and `PACKAGE_ROOT / "writer.py"` (the two roots
  `tests/derivations.py:PACKAGE_ROOT:31` already gives; no new module constant) is EMPTY, which is
  ordering decision 5 made checkable: it is what
  forbids `update_fields` from calling the door inside its own `note_lock` block and forbids the door
  from wrapping its move. Pinned BOTH ways with planted source files driven through the SAME function
  — REFUSED: a method holding `with vault_io.note_lock(p):` that calls `vault_io.move_note(p, q)`
  inside it (the deadlock shape, the one a reentrancy argument would wave through), one that calls
  `update_frontmatter_field(q, …)` inside it, and one that calls `self.rename_note(e, n)` inside it
  while a sibling method in the same planted module calls `move_note` (the derived third clause — the
  exact placement error this whole finding is about, refused by the scan and not by prose);
  ACCEPTED: `write_markdown_file`'s own shape (a
  `with vault_io.note_lock(...)` holding a `write_note` call — a single-path door, which MUST stay
  legal), and a method that calls `move_note` after its `with` block has exited (the shape Task 6
  ships). Each planted oracle is the exact source the test wrote, never a substring of the tree.
  It then drives the six mitigations Task 6 folded — the four in the door's own body
  (M1, M3, M4, M6) and, in `update_fields`' pre-write refusal, M7 on its rename-side disjunction and M8
  on its second clause — each pinned BOTH ways so the clause
  cannot pass by refusing everything.
  **(M1)** `rename_note` raises `ValueError` and leaves the vault's filename set unchanged for each
  of the escape's three reachable spellings — a traversing relative name built as
  `os.path.relpath(<a path the test created OUTSIDE the temp vault>, vault)`, the absolute path of
  that same outside file, and an in-vault filename that is a SYMLINK to it (the spelling a string
  compare cannot see; assert the outside file was NOT hard-linked to, by comparing its `st_nlink`
  before and after) — while an ordinary in-vault destination and a destination inside an in-vault
  SUBDIRECTORY both still move, so the clause is not "refuse everything". **Create that sub-directory
  before the call:** `move_note` reaches `os.link` against a missing parent and raises
  `FileNotFoundError` into a `WriteFailedError`
  (`obsidian_schemas/vault_io.py:_move_locked:772-773`), so an ACCEPTED cell written without the
  `mkdir` is RED against a correct door for a reason that has nothing to do with M1. Every oracle is a
  path the test itself created; nothing is matched on a prefix or a substring of the tree.
  **(M3)** the case-only branch's staging name stays in the `.md` namespace: wrap
  `obsidian_schemas.repositories.base.vault_io.move_note` in a recording delegate (restored in a
  `finally`) that forwards to the real door, drive one case-only rename, and assert that the recorded
  call sequence has two entries, that EVERY path in it — both positionals of both calls — has suffix
  `.md`, and that the intermediate staging path is matched by `vault_path.glob(repo.file_pattern)`,
  which is the very enumeration `BaseRepository.load` uses
  (`obsidian_schemas/repositories/base.py:load:241`) and therefore the property "a reader still sees
  it" reduces to. A near-miss in the same arm: assert that
  `source.with_name(destination.name + ".rename-tmp")` — the rejected spelling — is NOT matched by
  that same glob, so the assertion is shown to discriminate rather than to hold vacuously.
  **(M4)** the audit line names both ends: capture it through
  `tests/support.py:captured_logs:91` with `level=logging.INFO` — its default is `WARNING`
  (`tests/support.py:captured_logs:91`) and the door logs at INFO, so the default would capture
  nothing — across one successful rename, and assert the emitted record contains the SOURCE filename
  as well as the destination's, both taken from the paths the test created.
  **(M6)** the door FAILS CLOSED when the write guard is not enforcing, and the arm's whole point is
  that it discriminates in the direction the fail-open goes. Set the mode through
  `tests/support.py:patcher:73` — `with patcher() as p: p.setitem(os.environ,
  "OBSIDIAN_SCHEMAS_WRITE_GUARD", "observe")` — and NOT through a hand-rolled try/finally. That helper
  is not pytest's `monkeypatch` (which a conveyor-invoked zero-argument check cannot take): it is the
  project's own stand-in, documented as *"covering the two forms the AC checks use"*, whose `setitem`
  already records the prior value, restores it on exit even when the body raises, and POPS the key
  where it was previously unset (`tests/support.py:Patcher.setitem:59-65`, `:patcher:72-78`) — which
  is exactly the restore this arm needs, and it is the same helper
  `tests/test_concurrent_access.py:706`, `:737` already drives this variable with. Rolling a second
  one here would be a duplicate of a shipped leaf and would get the unset case wrong on the first
  try. That IS M6's "environment set and restored in a `finally`" — `patcher()` is a
  `@contextmanager` whose `finally` calls `undo()` — and its `setattr` form is the same helper the M3
  recorder and the half-failure delegate above are restored by. REFUSED, under `observe`: plant notes A
  and B at two distinct filenames, capture B's bytes, call `rename_note(entity_A, <B's filename>)`,
  and assert that it RAISES, that the raised exception is NOT a `NoteAlreadyExists` (it is the door's
  own `ValueError` — the leaf matters here because `NoteAlreadyExists` would mean the door reached
  `move_note`, which is the thing the clause exists to prevent), that the vault's filename SET is
  unchanged, and that BOTH files are byte-identical against the bytes the test wrote. Against a door
  missing the clause this arm is RED in the loudest available way: there is no exception at all, B's
  file is gone and A's bytes are sitting at B's path. Assert the same refusal for an ORDINARY in-vault
  rename under `observe` (a free destination), so the clause is shown to be the capability-level
  refusal it is specified as rather than an occupied-destination special case. ACCEPTED, under the
  default `enforce` — asserted in the same arm rather than inherited from the arms above, so the pair
  reads as one discrimination: the same occupied-destination call raises `NoteAlreadyExists` with both
  files byte-identical, and the same ordinary in-vault rename MOVES. Do NOT write the `enforce` half by
  assuming the ambient environment: set the variable to `"enforce"` explicitly for that half, because a
  value inherited from the runner is an environmental shape the test did not create (WI-149). Then the
  `update_fields` half, which is where the residual would otherwise land: with a STAMPED subject and
  `observe` set, `repo.update_fields(entity, {"name": <a DIFFERENT name>, "title": "…"})` raises, the
  vault's filename SET is unchanged, and the subject's file is BYTE-IDENTICAL to what the test wrote —
  which is the assertion distinguishing the early in-lock refusal from a door raise after the content
  write has committed — while `repo.update_fields(entity, {"title": "…"})` under the same mode still
  SUCCEEDS and lands in that file, so the widened predicate refuses name changes and not every update.
  **(M7)** `update_fields` refuses a `name` delta on a type that does not DECLARE `name`, pinned BOTH
  ways, and this arm's subject is a BOOK and not a person. Plant a book note by writing BYTES into the
  temp vault — the same colliding-group shape Task 9 builds, one note whose `_get_file_name` output it
  lives at — carrying `type: book`, a `title:` and NO `name:` key at all, and bind it with
  `BookRepository(vault)._load_file(path)` so the entity is STAMPED (an unstamped one refuses on the
  first disjunct and the arm would be vacuous). Set
  `OBSIDIAN_SCHEMAS_WRITE_GUARD` to `"enforce"` explicitly through `tests/support.py:patcher:73` for the
  whole arm, for the M6 arm's own reason: a mode inherited from the runner is an environmental shape the
  test did not create (WI-149), and an ambient `observe` would make this arm pass on the WRONG disjunct.
  REFUSED: `repo.update_fields(entity, {"name": "x/y", "status": "read"})` raises `ValueError`; the
  vault's filename SET is unchanged; the book note is BYTE-IDENTICAL to the bytes the test wrote — which
  is the assertion that distinguishes refusing before the content write from raising after it, and is
  the whole finding, since without the disjunct that file comes back carrying `name: x/y` and `status:
  read`; and the raised message names the TYPE-DECLARATION precondition rather than provenance or the
  guard mode, so the arm cannot pass on a sibling disjunct (assert on the substring the refusal is
  specified to carry, taken from Task 6's own wording, never on the whole message). Assert the same for
  a name spelling that ESCAPES — `{"name": "a/../../x"}` — because the two reach different failures
  downstream of the missing disjunct (`WriteFailedError` versus M1's `ValueError`) and both must be
  refused HERE, before either. ACCEPTED, three arms so the disjunct is shown to refuse the branch and
  not every update: the SAME book entity through `repo.update_fields(entity, {"status": "read"})`
  SUCCEEDS and the change lands in that file; a person subject's name change in the same vault still
  MOVES, with both files reachable exactly as the arms above assert (the control that fails a disjunct
  written as an unconditional refusal or keyed on the wrong sense); and a book note that STORES a
  `name:` key as a pydantic extra — planted as bytes carrying both `title:` and `name:`, then
  `_load_file`d — is ALSO refused, which is the direction Design §2's third bullet declares correct and
  the arm that fails an `entity.model_fields` or `hasattr(entity, "name")` spelling while the specified
  `type(entity).model_fields` passes. Every oracle is the exact path and the exact bytes the test itself
  wrote.
  **(M8)** `update_fields` refuses a delta that moves the entity type's OWN filename rule when no
  rename will follow it, pinned BOTH ways, and the arm is written to cover the RULE rather than one
  field. Reuse the stamped Book the M7 arm already plants — a note written as BYTES into the temp vault
  carrying `type: book`, a `title:`, an `author:` and NO `name:` key, living at the filename
  `BookRepository._get_file_name` derives from those two values, bound with
  `BookRepository(vault)._load_file(path)` so it is STAMPED — and plant one stamped Meeting beside it
  the same way. Set `OBSIDIAN_SCHEMAS_WRITE_GUARD` to `"enforce"` explicitly through
  `tests/support.py:patcher:73` for the whole arm, for the M6 arm's own reason: an ambient mode is an
  environmental shape the test did not create (WI-149). REFUSED, and the four cells are chosen so the
  clause is shown to read the RULE and not a remembered field —
  `repo.update_fields(<the book>, {"title": "New Title"})` and `{"author": "New Author"}` on that same
  book, and `repo.update_fields(<the meeting>, {"date": "2026-01-01"})` and `{"topics": ["Other"]}` on
  the meeting — each asserting: `ValueError` raised; the vault's filename SET unchanged; the subject's
  file BYTE-IDENTICAL to the bytes the test wrote, which is the assertion that distinguishes refusing
  BEFORE the content write from committing it and is the whole finding, since without the clause that
  file comes back carrying the new value at its old filename with no alias and no exception; and the
  raised message naming the FILENAME-RULE precondition rather than provenance, the guard mode or the
  type declaration, so the cell cannot pass on a sibling clause (assert on the substring Task 6
  specifies, never on the whole message). ACCEPTED, four arms, each of which fails a different wrong
  spelling: the SAME book through `repo.update_fields(entity, {"status": "read"})` SUCCEEDS and the
  change lands in that file (`obsidian_schemas/models.py:Book.status:163` feeds no filename — this is
  the arm the M7 ACCEPTED half already asserts and it must stay green), and the same meeting through
  `{"tags": ["x"]}` likewise; an ALREADY-DIVERGENT planted Book — written as bytes at a filename that
  is NOT its own rule's output, then `_load_file`d — still accepts `{"status": "read"}`, which is the
  arm that fails a `derive(projected) != file_path.name` spelling; a PERSON name change in the same
  vault still MOVES through the door exactly as the arms above assert, which is the control that fails
  a clause written without the `not renaming` conjunct or one reaching a repository that declares no
  `_get_file_name`; and a delta supplying a NON-STRING value for a deriving field
  (`{"title": ["a", "b"]}` on the book) is refused with the SAME `ValueError` and NOT with an
  `AttributeError`/`TypeError` leaking out of `_get_file_name`, which is the fail-closed direction Task
  6 prescribes and the arm that fails an unguarded `derive(projected)`. Every oracle is the exact path
  and the exact bytes the test itself wrote; nothing is matched on a prefix or a substring of the tree.
  verify: test_a_person_note_is_renamed_only_through_the_one_door_and_stays_reachable

- [x] **Task 11 — Ship the detector.** Add `NOT_RENAMEABLE_MARKER`, `_gate_refusal_pattern` and the
  `stem_name_divergence` arm to `scripts/lint_vault.py:check_structural`, placed after the
  `TYPE_TO_MODEL` guard so the `read_error`/`parse_error`/`missing_type` arms keep their triage
  order. ERROR, `structural`, `auto_fixable` left at its default. Add one comment naming why this
  call reaches the phone-sentinel exemption where `scripts/lint_vault.py:1009-1014`'s `--fix` delta
  path cannot. Touch no other check, no category list, and no `apply_fixes` branch.
  verify: test_lint_vault_reports_stem_name_divergence_and_never_repairs_it

- [x] **Task 12 — Write AC-3's battery, inside the five-part containment door.** New module
  `tests/test_stem_name_divergence_detector.py` holding
  `test_lint_vault_reports_stem_name_divergence_and_never_repairs_it` (zero-arg, raising). It
  inherits WI-026/WI-031's containment clauses in full because it drives `lint_vault`'s mutating
  entry points: ONE `_temp_vault` door that asserts containment before returning and is the module's
  only binding of the identifier `vault`; the `mutating_drive_vault_args` scan asserting every
  mutating drive's vault argument is that identifier, that there is at least one, and that every
  binding of the name is a call to the door; no subprocess-capable import; no live-path token outside
  the door's body; and ZERO repository constructions anywhere in the module. Arms (a)–(e) as AC-3
  states them, with the expected four DERIVED from the manifest by the same predicate AC-1 uses
  (SKIPPING a `NoteSpec` that declares no `fields`) and the planted phone stub supplying (c)'s
  negative. The check runs the detector over TWO materializations and asserts a SET EQUALITY of the
  paths carrying a `stem_name_divergence` issue over each — that check's own issues, never the whole
  report, which carries unrelated arms — and that is what keeps the plants from loosening (a): over a
  PRISTINE materialization,
  exactly the derived four; over a materialization carrying the plants, those four plus exactly the
  planted members declared to fire, and nothing else.
  **The plants, one per free variable the frozen corpus is unanimous about** (Design §3a's sweep, which
  is the list's authority — read the arm's own text, do not copy this table): (i) ROW 8's SHAPE — a note
  with NO `@` prefix, a book-titled stem, carrying `type: person` and a stored `name:` that differs raw
  from that stem: it FIRES, which is what refuses a guard narrowed to `vf.is_at_prefixed and
  entity_type == "person"`, the narrowing every corpus arm of AC-3 tolerates and the live report does
  not (`docs/stem-divergence-live-baseline.md:153`); (ii) CASE-ONLY — a person note whose stem differs
  from its stored name only in letter case: FIRES, which refuses a `.lower()`-ed comparison and covers
  live baseline row 3; (iii) DOUBLE `@` — `@@<name>.md` carrying `name: <name>`: FIRES, which refuses
  `lstrip("@")` in place of a single-character strip, since the library's canonical target for that
  note is `@<name>.md`; (iv) SUB-DIRECTORY — a divergent person note inside a sub-directory of the temp
  vault whose name is NOT a member of `scripts/lint_vault.py:SKIP_DIRS` (imported, never re-typed):
  FIRES, since `read_vault` rglobs and `vf.stem` is depth-free
  (`scripts/lint_vault.py:read_vault:123`, `:155`); (v) NEAR-MISS, a NON-STRING `name:` — a person note
  carrying `name: [<two items>]`: does NOT fire, the declared narrowing in Design §3, and the arm that
  stops the check being satisfied by "report everything that is not an exact match"; (vi) SECOND
  NEAR-MISS, a BLANK `name:` — a person note carrying a whitespace-only `name:` (e.g. `name: "   "`)
  whose stem differs from it: does NOT fire, which is the arm's `stored.strip()` conjunct and refuses an
  implementation written as `isinstance(stored, str) and stem != stored`, the one that passes every other
  cell in this battery while reporting each blank-name note as a never-fixable divergence on top of the
  auto-fixable `person_missing_name` that repairs in the opposite direction
  (`scripts/lint_vault.py:1040-1045`). Plant (vi) asserts SILENCE from this check only and asserts
  nothing about which other issue the note carries, because `person_missing_name` is gated to ACTIVE
  tier (`scripts/lint_vault.py:check_completeness:429-446`) and pinning a partner issue would couple
  this arm to `classify_person_tier`'s own inputs; (vii) UNNORMALIZED OPERANDS — a person note whose
  stem is `<n>` and whose stored `name:` is the QUOTED `"  <n>  "` (leading and trailing spaces, which
  survive only because the scalar is quoted): it FIRES, because the arm is raw on both sides, and that
  refuses both spellings of the normalizing slip — `stem != stored.strip()` and `stem.strip() !=
  stored` — each of which passes every other cell in this battery while dropping a note whose next
  `save` would mint `@  <n>  .md` and fork it. Assert the issue's MESSAGE carries the stored value
  with its whitespace intact, so the plant cannot be satisfied by an arm that reports the note for a
  different reason. Every plant is
  written as BYTES into the temp copy, never through `repo.save` or `write_markdown_file` (this module
  constructs no repository at all), and every oracle is the exact path and exact stored value the test
  itself wrote — never a prefix, a substring or a layout of the tree.
  verify: test_lint_vault_reports_stem_name_divergence_and_never_repairs_it

- [x] **Task 13 — Write AC-4's baseline-shape check and its reader battery.** New module
  `tests/test_stem_divergence_baseline_shape.py` holding
  `test_the_stem_divergence_live_baseline_is_committed_and_shaped` (zero-arg, raising) and
  `test_the_baseline_readers_reach_their_claimed_shapes`. Readers live in this module and are driven
  by BOTH the live read and the planted battery, never re-implemented for one of them. The check
  asserts: the file is present in the tree; §1 carries the two entry figures AC-4 names — the
  divergence count and `len(PersonRepository($VAULT).conflicts)` — each parsing as an integer by
  LEADING-INTEGER extraction from its own cell and never by `int(cell)` over the whole cell, because
  §1's other rows legitimately read `0 of 8` and `1 of 8 by a DIFFERENT note (row 8); 1 of 8 by the
  SAME file …` and a whole-cell numeric rule would be RED against a correct artifact; §1's remaining
  rows are asserted PRESENT by their label only; neither figure is compared to a VALUE, because the
  population is LIVE, is re-measured at exit, and an equality written today is stale by build time;
  §2's table carries all of (b1), (b2),
  (b3), (c) and a direction for every row; every direction's leading token is in
  `{RENAME, MERGE, FIELD-REPAIR}` and every (b2) value's leading token is in
  `{no, same-file, different-note}` — the vocabulary the artifact declares for itself at
  `docs/stem-divergence-live-baseline.md:155-156`; NO row resolves to `rename` while its (b3) column
  declares a door refusal; NO row resolves to `rename` onto a destination occupied by a DIFFERENT
  note, while a `same-file` destination is NOT occupied for this rule and resolves to `rename` as a
  case change; §4's booked repairs and §5's named attestation section are present with their figure
  names and re-run commands; and **(M5)** the privacy wall holds WHOLE-FILE in BOTH of its halves — no
  member of `tests.test_vault_path_required.FORBIDDEN_DEFAULT_PATTERNS` appears (IMPORTED, never
  re-spelled, or this assertion becomes its own offender), and every `.md` token the file names
  ANYWHERE — inside a fenced code block exactly as much as outside one — resolves to a path that EXISTS
  in this repo, or is the declared template literal `@{name}.md`, or CONTAINS a `*` and is therefore a
  glob rather than a filename. The exemption is that TOKEN CLASS and NEVER a region: a fenced block is
  precisely where the exit attestation's pasted output lands, and §5's second re-run command is
  `scripts/lint_vault.py --vault "$VAULT" --report`, which reports issues PER PATH and so names note
  filenames by construction, while a bare `@Someone Real.md` contains no member of
  `FORBIDDEN_DEFAULT_PATTERNS` (`tests/test_vault_path_required.py:FORBIDDEN_DEFAULT_PATTERNS:278` is
  `["expanduser", "Path.home()", "/Users/"]`) so nothing else in the build would catch it, and the
  artifact declares at `docs/stem-divergence-live-baseline.md:15` that a whole-file privacy scan is legal
  against it. Tokenize with a character class that INCLUDES `*` —
  `re.findall(r"[\w@{}*./+-]+\.md", text)` — because a class without it leaves the glob's `*` outside the
  token and the exemption becomes unreachable; a leaked filename carrying a space is captured as its
  trailing segment (`@Someone Real.md` → `Real.md`), which resolves to nothing in this repo and so still
  FIRES, and the class is NOT widened to spaces chasing a prettier token. The rule is green against the
  artifact as committed and that was checked byte by byte rather than assumed (Design §4a enumerates its
  eight `.md` tokens: four existing repo paths, the `'*.md'` glob at `:36` — the false RED the second
  spec-review round reached for a region exclusion to dodge — and `@{name}.md` three times). Write NO
  fence toggle into the privacy path and NO non-vacuity guard on it: the earlier region form's guard
  ("at least one line was skipped") is satisfied by a toggle stuck OPEN, which is the whole-file
  exemption it claimed to prevent, and the token-class rule has no toggle to get stuck. The §1 and §2
  table readers are scoped to their own `##` section, so §0's pipe-bearing script and stdout are never in
  their input and nothing else in the module needed fence detection either. It executes nothing
  against any vault. The reader battery plants a row for every claimed shape — a refused row
  resolving to `merge`, a refused row resolving to `rename` (must RAISE), an occupied-by-a-different-
  note row resolving to `rename` (must RAISE), a `same-file` row resolving to `rename` (must PASS), a
  row missing a column (must RAISE) — and drives them through the same readers the live arm calls. It
  pins the privacy scan the same way, through the SAME token function the live arm calls and never a
  re-implementation, because a scan whose oracle is "zero offending tokens" is satisfied identically by
  one that resolves every claimed shape and by one that resolves almost none (WI-235): MUST FIRE — a bare
  note filename on a prose line, and the SAME filename on a line INSIDE a fenced code block, which is the
  M5 arm and the one the region form let through; MUST NOT FIRE — a `*.md` glob inside a fence, the
  `@{name}.md` template literal, and a repo-relative path to a file the test itself confirmed exists.
  Every planted oracle is text the test itself wrote.
  verify: test_the_stem_divergence_live_baseline_is_committed_and_shaped test_the_baseline_readers_reach_their_claimed_shapes

- [x] **Task 14 — Close wall membership and the count pins, then run the floor.** In
  `tests/test_provenance_write_seam.py`, add
  `test_every_wall_this_item_joins_is_run_on_the_final_text` (zero-arg, raising) following
  `tests/test_name_gate_wall.py:test_wall_membership_is_closed_by_running_each_walls_predicate:1057`'s
  shape: declare this item's touched-file list, assert every path exists, and CALL each wall's own
  shipped predicate on those files — the routing walls A/B/C (`filesystem_mutation_uses`,
  `os_module_attribute_uses`, `module_import_uses`), the `ast` single-home set equality over
  `python_files_under(PACKAGE_ROOT, TESTS_ROOT)`, `skip_reason_literal_sites` over the widened
  universe, `frontmatter_write_arms` and `gate_call_declarations`/`gate_call_placement` over the
  touched package files, `character_class_strip_sites` and `address_splitting_implementations` over
  the routing-universe slice, `auto_fixable_emitter_checks`/`auto_fixable_branch_checks` over
  `scripts/lint_vault.py`, `FORBIDDEN_DEFAULT_PATTERNS` via `_code_lines` over the authored
  files, and — the two rows an earlier draft of this task named in `## Wall Membership` and did not CALL,
  which is the whole failure mode WI-301's rule exists to close, since a row no task runs is satisfied by
  reasoning — wall D (`tests/test_name_gate_wall.py:_check_wall_d:1107`: `functions_calling(touched,
  "parse_markdown_file")` ⊆ `{obsidian_schemas/repositories/base.py}`; predicted green, since the door
  parses nothing and `_load_file` is unchanged) and the `_email_index` zero-sites pin
  (`tests/test_identity_endgame.py:590`: `_literal_sites(EMAIL_INDEX_ATTR,
  python_files_under(PACKAGE_ROOT, TESTS_ROOT))` empty; predicted green, and note that the needle there
  is ASSEMBLED FROM PARTS precisely so a module under those roots is not its own counterexample — no new
  test module may spell that attribute whole). The obligation is that EVERY row of `## Wall Membership`'s
  table is RUN here, and two of its thirteen rows are discharged by a RUN that is not a direct predicate
  call — declared rather than skipped, which is WI-301's own clause: the corpus-freeze row is
  `tests/test_fixture_vault.py` asserting `CORPUS_DIGEST`, which the floor command at the end of this task
  executes (no battery may add, edit or delete a fixture note, so the expected outcome is GREEN with the
  digest constant untouched), and the check-contract row is enforced by the conveyor's own per-criterion
  runs at `building → done` rather than by an in-build predicate — so this task instead asserts the
  contract's two mechanical halves directly over the four new modules' source: the first statement of each
  is `ensure_project_interpreter(__file__)`, ahead of every package import, and every function an
  acceptance criterion names is a top-level zero-argument `def`. Non-completion is covered where it
  already lives: `non_completed_write_sites`' bidirectional map is one of Task 1's pins and is re-run
  below. Then re-run EVERY count pin Task 1 recorded — the obligation is the list Task 1 wrote into the
  Build Log, never a number stated here — and assert each is unmoved. If any HAS moved,
  do not bump the number: name the new member in the Build Log, update the assertion in its own
  module to name the member (not merely the count), and say which design decision moved it.
  Finally run the floor command; it must be GREEN with a case count no lower than Task 1's.
  verify: test_every_wall_this_item_joins_is_run_on_the_final_text test_wi020_derivations_survive_the_routing test_wall_membership_is_closed_by_running_each_walls_predicate test_write_failure_raises_and_noops_keep_their_return

## Build Log — 2026-09-26 (build-runner, resumed after a spawn timeout)

Fourteen tasks landed. The floor is GREEN. Only things a future reader needs in order to understand
why the code looks the way it does are below; it is not a commit log.

### 0. The resume, and what the cursor actually was

The first build spawn TIMED OUT mid-build and the drive worktree retained its edits. It had **not**
written a `## Build Log`, so the prescribed resume cursor did not exist and the objection's instruction
to read it could not be followed as written. The cursor was reconstructed from the TREE instead — the
diff against HEAD, the presence or absence of each task's named artifact, and a floor run — which
placed the stop between Task 12 and Task 13: Tasks 2–12's code and batteries were all present and the
floor was green at 696, while `tests/test_stem_divergence_baseline_shape.py` (Task 13) did not exist
and `test_every_wall_this_item_joins_is_run_on_the_final_text` (Task 14) was named in
`tests/test_provenance_write_seam.py`'s own module docstring but not defined in it. Task 1's baselines
were also unrecorded, and recording them after the edits had landed is a different act from recording
them before — see §1. This session built Tasks 13 and 14, recovered Task 1, and re-ran everything.

Shell liveness was probed first (WI-228 P4): `Bash` execs, so nothing here was written blind.

### 1. Task 1's baselines — recovered from pristine HEAD, not from memory

Task 1 asks for a capture taken BEFORE the first edit that moves it, and the timed-out spawn made its
edits without taking one. Re-reading the pins in the edited tree would have recorded the
POST-conditions under a pre-condition's name, which is the one thing the task exists to prevent. So the
baselines were taken from a pristine export of HEAD — `git archive HEAD | tar -x -C $TMPDIR/...`, driven
with this project's own interpreter — which is HEAD's text by construction and required no writable
git state. **The list is the obligation, not the numbers**, and Task 14 re-runs exactly this list:

| pin | HEAD (baseline) | final text | moved? |
|---|---|---|---|
| floor case count | 689 | **699** | grew by 10, directional invariant satisfied |
| `functions_reserializing_parsed_frontmatter` | 4 | 4 | no |
| `functions_parsing_then_writing - writers` | `{write_markdown_file}` | `{write_markdown_file}` | no |
| `non_completed_write_sites(PACKAGE_ROOT)` | 8 | 8 | no |
| `non_completed_write_sites(person.py)` | 8, over the five qualnames | 8, same five | no |
| `base_repository_subclasses` | 4 | 4 | no |
| `load_file_implementations` | 3 | 3 | no |

The five `person.py` qualnames, recorded in full because a set that MOVED is edited to name its new
member rather than bumped: `append_to_timeline`, `append_to_body_section`, `update_to_discuss_item`,
`remove_to_discuss_item`, `_get_body_content`. Not one pin moved, so no pin-holding module needed an
edit — the three CONDITIONAL Write Targets (`tests/test_concurrent_access.py`,
`tests/test_name_gate_wall.py`, `tests/test_loud_fail_write.py`) are UNWRITTEN exactly as predicted.

### 2. M2's observation, which Task 2 asked for as an observation and not an assertion

Task 2 requires the Build Log to record where a FORGED `_source_path:` key in a note's own frontmatter
ends up, and to assert only the property. Measured on **pydantic 2.12.5**: the forged key IS RETAINED —
it appears in `entity.model_extra` as the raw string, and `model_dump()` includes it. The property
holds regardless and is what the check asserts: `getattr(entity, "_source_path")` — verbatim the
accessor `_resolve_write_target` reads — answers the file the entity was PARSED FROM, never the forged
value, because the `PrivateAttr` is a different namespace from `model_extra`. Pinning the retention
would make this arm RED against correct code on a pydantic release that stops keeping
underscore-prefixed extras, which is exactly why Task 2 forbade it.

One consequence worth stating so nobody reads AC-1(h) as broken: a note that ALREADY carries a forged
`_source_path:` will round-trip that key back out, because `extra="allow"` round-trips every unknown
key and always has. That is pre-existing behaviour for arbitrary frontmatter and not something the stamp
introduces — the library never MINTS the key, which is the half AC-1(h) measures and the half Task 2's
key-set arm asserts against the entity the test itself built.

### 3. One line in the door that Task 6 did not enumerate, and why it stays

`rename_note` contains `vault_io.record_snapshot(moved)`, guarded on "this call committed something".
Task 6's enumeration of the door's body does not name it. It is load-bearing rather than decorative, and
that was established by mutation and not by argument: replacing the call with `pass` turns AC-2's check
RED with `NoteAlreadyExists` on the save-after-rename arm — `move_note` forgets BOTH paths' snapshots
and the door's alias write records none, so the moved note is left UNREGISTERED and the entity's very
next `save()` takes `write_markdown_file`'s zero case and refuses against the note the rename just
created. That is AC-2(e)'s own save. The line was restored and the floor re-run green afterwards.
The guard matters as much as the call: unconditional, the idempotent no-op branch would launder a THIRD
PARTY's write into an accepted precondition.

### 4. What the Task 14 RUN returned that `## Wall Membership` did not name

`## Wall Membership` says anything the RUN returns that the section did not name is named here and
satisfied — never worked around, and never satisfied by narrowing the wall. One row did:

**Wall D's requirement under-reaches.** The row reads "no new `parse_markdown_file` caller outside
`obsidian_schemas/repositories/base.py`". Run over this item's touched package files, the callers are
three, not one: `Book` and `Meeting` carry standing `_load_file` OVERRIDES that parse, and both files
joined the touched list at Task 5. Both are pre-existing at HEAD (`git show HEAD:…` confirms the call in
each), so nothing was gained — but a module-level permitted list would have BLESSED whatever happened to
be there, which is the narrowing the rule forbids. The satisfying form is strictly stronger than the row
as stated: the parse-caller set over the touched package files is asserted EQUAL to the three
`_load_file` implementations, a set `load_file_implementations` derives INDEPENDENTLY of that call and
which Task 1 pins at three. So a parse call added to the door, to `save`, or to a body-writer in any of
these files is RED, where the row as written would have passed it in `base.py`. Verified to discriminate:
a planted module with a `parse_markdown_file` caller fires the assertion.

### 5. This module was the `_email_index` pin's only offender, which is the cheapest possible proof the pin is not vacuous

Task 14 warns that WI-023's zero-sites pin assembles its needle FROM PARTS so a module under its roots
is not its own counterexample, and that no new test module may spell the attribute whole. Written the
obvious way first — a helper named after the thing it checks, plus a docstring naming it — Task 14's
own check reddened that pin at three sites in `tests/test_provenance_write_seam.py`. The scan is a TEXT
scan and cannot tell a mention from a use. The helper is therefore named periphrastically
(`_wi029_the_deleted_identity_attribute_is_named_nowhere`) and its docstring names the attribute
nowhere. Recorded because the next author will reach for the obvious name too.

### 6. An undeclared Write Target: `tests/test_company_name_contract.py`

That file is MODIFIED and `## Write Targets` does not declare it. It is inside this project's write
authority (`tests/**`), so it is a declaration gap and not an authority one, and the edit is a forced
consequence of Tasks 3 and 6 rather than a choice: its `_drive_update_fields` arm driver planted a
company note, called `update_fields(entity, {"name": member})`, and returned the SEED path as the file
the arm wrote. Since this item, that call MOVES the note, so the seed path no longer exists when the
arm's oracle reads it. The driver now asks the repository which file it wrote
(`repo.get_file_path(member)`) rather than recomposing the filename rule, which keeps it true whatever
that rule is; the arm's own leg (`"stored"`) is unchanged, because the arm's write is still name-free —
the MOVE happens in `rename_note`, to a destination the caller composes. A comment at `ARM_LEGS` records
that distinction, since the old comment's "derive no filename" reading is now only half true.

### 7. Also in the worktree and NOT this item's: `docs/whatsapp-jid-value-type.md`

An untracked file carrying WI-032's frontmatter (`stage: idea`, created 2026-09-21). It was present when
this spawn started, is not referenced by anything here, and was deliberately NOT touched — the run scope
forbids editing another item's tracked document. Named so the exit gate does not read it as this build's
output.

### 8. Verification actually performed

- **Floor:** `.venv/bin/python -m pytest tests -q` → **699 passed** in ~21s. Baseline at HEAD was 689
  under the same interpreter, so the DIRECTIONAL invariant holds (+10 and no file silently lost).
- **Each AC check under the conveyor's own shape**, not only under pytest: all five invoked as
  `getattr(mod, name)()` with zero arguments through an `importlib` bootstrap, all five PASS. This is
  the WI-089 shape mismatch that bounced 8-of-9 elsewhere, and pytest collection does not test it.
- **Task 14's two new arms shown to DISCRIMINATE**, not merely to pass: wall D fires on a planted
  `parse_markdown_file` caller; the check-contract half fires on a module whose first statement is not
  the interpreter bridge.
- **Task 13's readers shown to discriminate** against the LIVE artifact's own bytes, in memory: flipping
  row 8's direction from `MERGE` to `RENAME` produces exactly one violation. The live read is
  non-vacuous — 8 direction rows, 12 §1 figures, 8 `.md` tokens — and the privacy rule is GREEN on the
  committed artifact for precisely the token census Design §4a enumerates (three existing repo paths
  across four tokens, the `*.md` glob, `@{name}.md` three times).
- **The `record_snapshot` line** established load-bearing by mutation and reverted (§3).

### 9. Things deliberately NOT done

- **No `criteria` fence was written or touched.** `## Acceptance Criteria` is FROZEN AND SIGNED
  (`ac_hash 15189b874b27`); `## Scope Boundary` names it and `## Intent` among what the builder must not
  touch. Every criterion's check now resolves and passes, which is the builder's whole obligation there.
- **No stage advance and no `state/work-items.json` write.** That is the conveyor's, via
  `stage_advancer.py`; `state/**` is deny-class for a builder in any case.
- **AC-4's EXIT half is not satisfied and cannot be from in here.** `docs/stem-divergence-live-baseline.md`
  §5 is a named EMPTY section by design. The item's declared SHIP CONDITION is that the conductor re-runs
  the §0 script and `scripts/lint_vault.py --vault "$VAULT" --report` against the live vault, appends the
  attestation, and reads zero on both divergence and conflicts. The shape check asserts §5 is PRESENT with
  its figure names and both re-run commands, and asserts nothing about its values — deliberately, since
  the population is live and an equality written today is stale by build time.

## Write Targets

Two conductor-committed grounding artifacts, both required in the tree's git HEAD BEFORE the
acceptance criteria are presented for signature (WI-300). Neither is producible from inside the
cage: one needs the live vault, the other needs three repositories outside this project's write
authority.

```writes
kind: precondition
path: docs/stem-divergence-live-baseline.md
grounds: Which live notes diverge today, how each one is repairable — which side is correct, whether the destination is occupied, whether the WRITE DOOR itself refuses the stored name — and what else points at the old stem
why: Three of this item's premises rest on content no caged reader can see, and each of them can falsify an acceptance criterion if it is guessed. (a) THE COUNT AND ITS COMPANION — the divergence count and `len(PersonRepository(<vault>).conflicts)` at entry, re-run identically at exit; the queue review folded the conflict count in and one such pair was observed self-healing between two reads on 2026-09-21, so a single reading is not a baseline. (b) THE DIRECTION, PER NOTE — for each diverged note, THREE columns and not two. (b1) which of stem and `name:` is correct; (b2) whether the canonical `@{name}.md` filename is ALREADY OCCUPIED, because an occupied destination makes the repair a MERGE rather than a rename and `vault_io.move_note` will refuse it by syscall; and (b3) whether the note is GATE-REFUSED **by the DOOR predicate defined in `## Exploration Notes` ("Which notes ARE the class")** — that is, whether `gate_write(fm, declared_type=fm.get("type"), whole_record=True)` raises for that note's OWN stored frontmatter, the exact call `write_markdown_file` makes (`writer.py:229-233`, `:252-253`) — recording the raised `pattern` where it fires. Run the DOOR, not a bare `NameValidator.validate_strict(name)`: the two disagree on the one `sentinel_exempt` branch, because `gate_write` derives `allow_phone_sentinel` from the note's own payload (`name_gate.py:355-358`) while `validate_strict` defaults it to `False` (`name_validation.py:594`, `:599-601`). That disagreement is not academic here — `pure_digit` is MEASURED at 2 live person notes, `+<11-12 digits>` (`docs/vault-shape-census.md:148-157`, `:260-261`), and whether either is ALSO among the eight divergent is exactly what this artifact answers. A phone-only stub that declares `phones` is WRITTEN by the door and `@+447700900123.md` is an ordinary filename, so its correct direction is RENAME; a table built on the bare validator would mark it refused and the shape check below would then forbid the one direction that works. (b3) is added on round 3's evidence and corrected on round 4's, and it is not hypothetical either way: two of the four divergent notes in the FROZEN corpus are gate-refused (premise 13), and for such a note the repair is to fix the FIELD (or merge) rather than to move the file — the policy being that we do not mint a filename from a name the package refuses to write, since the note's own `save()` would then raise on a stem no write path could have created; for `path_hostile` it is additionally impossible, `@{name}.md` for a name containing `/` being a path into a different directory. The census's live population is where this is likeliest: "a book-titled file holding a person note" and "a first-name-only stem" (`docs/vault-shape-census.md:262-265`) are shapes whose stored name is arbitrary text. Every row must therefore resolve to rename, merge, or FIELD-REPAIR, and a row whose (b3) fires may never resolve to rename. A criterion promising "renamed to match the stored name" is false for any member where the field is the wrong half or where the field is one the door refuses, and there is no way to know which members those are from here — the census records eight distinct shapes and quotes none of them (M1 privacy). Commissioning this table with two columns and discovering (b3) afterwards is a SECOND conductor act outside the cage, which is why the column is declared before the artifact is ordered rather than after it comes back. (c) THE BLAST RADIUS — how many incoming references (wikilinks, `attendees:` entries, `company:` values) name each old stem, since this project's own linter resolves by stem and not by alias, so every rename converts silent references into linter warnings at a volume nobody has measured. The same artifact carries the four booked hand repairs (one book note typed `person`, four untyped notes, three unparsed book fences) and their exit re-count. Privacy wall as the census and the WI-026 baseline: counts, classes and directions — no filename, no note bytes, no absolute path.
```

```writes
kind: precondition
path: docs/wi-029-consumer-audit.md
grounds: Whether any consumer calls a write path this item changes in a way the change would move, and whether any consumer's own idioms would defeat or be surprised by provenance-bound writes
why: Approach C changes where EVERY mutating library call on an ALREADY-EXISTING entity lands — not just `save` (from `@{name}.md` to the note the entity was PARSED FROM) but `update_fields`, the five mutating `PersonRepository` body-writers and Book's and Meeting's `save` overrides, all nine of which resolve their target from a name today (premise 12) — and it makes `update_fields` MOVE a file on a name change. Inside this tree that is provably safe: grep says every in-library `.save(` is a create path (`person.py:1340`, `book.py:322`, `company.py:238`) and nothing in-library calls a body-writer. The forks measured in the live vault therefore came from HAL9000, Exocortex or orchestrator, which install `-e` and are outside `pipeline-runners.yaml:34-38`'s write authority. The audit must state, per repository with its scanned HEAD and verbatim command output, SIX things. (1) Every call site of the nine changed paths — `.save(`, `.update_fields(`, `.append_to_timeline(`, `.append_to_body_section(`, `.add_to_discuss_item(`, `.update_to_discuss_item(`, `.remove_to_discuss_item(` — and for each, whether its entity was loaded from the vault or freshly constructed: the first decides which sites move, the second which keep today's behaviour. The body-writers are listed EXPLICITLY and are not an afterthought to `.save(`: `append_to_timeline` is plausibly the consumers' highest-volume write (Exocortex writes meeting timelines), it is the path premise 9's harm and the Examples-of-done both describe, and an audit commissioned without it measures this item's blast radius with its largest surface missing — re-measuring would be a second conductor act outside the cage. (2) Every site that holds a `Path` to a note across a write and would be left holding a stale path after a rename. (3) Every repository construction passing `auto_load=False`, or constructing a repository and never calling `load()`: under the first draft's name-keyed seam those sites would have been silently unprotected, and although provenance binding removes that hazard for `save`, the count is the evidence that removing it was necessary and is cheap to gather in the same sweep — note that the body-writers RAISE rather than fork in that configuration today (`person.py:1404`), so any site found here is a live exception risk that the seam converts into a correct write. (4) Every site that RECONSTRUCTS an entity rather than passing the loaded one through — `Person(**data)`, `model_validate(...)`, `model_copy(update=...)`, a dict round-trip, a cache that pickles or JSON-serializes entities between load and save — because each such site drops the provenance stamp and keeps today's name-bound behaviour, so this is the exact population of the one residual arm (AC-1(f)) and the only way to know whether it is empty, small, or the main path. (5) Every site holding a WIKILINK or `attendees:`/`company:` reference to a note it later renames, since those become linter warnings under the accepted-noise disposition. (6) Any consumer call against `BookRepository.save` or `MeetingRepository.save`, whose filename derivation is `_get_file_name(entity)` rather than `@{name}.md` (`book.py:167`, `meeting.py:189`) and which this item brings inside the seam — the same divergence class with a different filename rule, and the shape behind the booked hand repair of a book-titled file holding a person note. Precedent and shape: `docs/wi-024-consumer-audit.md`, `docs/company-name-corpus-audit.md`. It is a `kind: precondition` and not a criterion for the reason `docs/default-vault-path.md:109-116` records: a hermetic floor cannot reach another machine's checkout, so the fence enforces that the audit happened and no test pretends to re-perform it.
```

**The builder's own write targets** (added at `exploring → specced`; the two fences above are
EXTENDED, never replaced — their `grounds:` ordering is what made the AC frame correct, and both
artifacts are already in HEAD). The driven doc is implicit and is not declared. Every path below is
inside `pipeline-runners.yaml:write_authority:34-38` (`obsidian_schemas/**`, `tests/**`,
`scripts/**`, `docs/**`), so nothing in this plan is unbuildable by construction.

```writes
path: obsidian_schemas/models.py
why: Task 2 — `BaseEntity` gains the `_source_path` PrivateAttr and the `PrivateAttr`/`Path` imports. Walls it joins: routing A/B/C (names no filesystem-mutation capability, no non-read-only `os` member, no mutation-capable import), the WI-021 frontmatter-write-arm sweep (binds no frontmatter dict, so it contributes no arm).
```

```writes
path: obsidian_schemas/parser.py
why: Task 2 — `parse_markdown_file` stamps the entity it just derived; `parse_markdown_content` is untouched. Walls it joins: routing A/B/C; WI-020's parse-seam closure and `parse_frontmatter_exit_sites` over PACKAGE_ROOT (the edit adds no parse call and no exit site).
```

```writes
path: obsidian_schemas/repositories/base.py
why: Tasks 2, 3 and 6 — `_resolve_write_target` (Task 2, the pure resolver), `rename_note` with its M1 destination containment, M6 guard-mode fail-closed refusal, M3 staging name and M4 both-ends audit line, `save`'s CREATE fallback and its resolved-target INFO line, `update_fields`' REFUSE fallback (binding `resolved`), its in-lock `ValueError` for a name change whose door preconditions do not hold — no provenance, a non-enforcing write guard (M6), or an entity whose own type declares no `name` and therefore derives no `@{name}.md` destination (M7) — raised before anything is written, that same arm's SECOND CLAUSE refusing a NON-rename delta that moves the entity type's own `_get_file_name` rule (M8), its mirroring of a caller-supplied `aliases` value onto the entity ON THE RENAMING PATH ONLY, and its write→move→rebind ordering with the door call placed OUTSIDE the `note_lock` block — no destination pre-check and no move-before-write anywhere in either method, the occupied-destination residual being ACCEPTED and stated (Design §2, "The COMPLEMENT of that rule"). Walls it joins: routing A/B/C (the move goes through `vault_io.move_note`, never `Path.rename`; `Path.resolve`, `Path.is_relative_to`, `Path.exists` and `Path.samefile` are READS and legal; M6 adds `vault_io.guard_mode()`, a module-attribute call on the already-imported `vault_io` that touches no filesystem and names no `os` member — and it is read through that function precisely so this file does not become a second `os.environ` home, which `vault_io._env_setting:104-115` forbids in writing; M7 adds `type(entity).model_fields`, a class-attribute read that touches no filesystem, names no `os` member, imports nothing and is the spelling `writer.py:108`'s comment and `parser.py:199` already use; M8 adds `getattr(self, "_get_file_name", None)` and `entity.model_copy(update=…)`, both of them an attribute read and a pydantic call that touch no filesystem, name no `os` member and import nothing — `_get_file_name` is CALLED only to compare two derived strings and its result never becomes a path); `non_completed_write_sites` over PACKAGE_ROOT (the door must contain no falsy return — M1 and M6 both RAISE, neither returns `None`, and M7's disjunct and M8's second clause each extend or sit beside an existing `raise ValueError` rather than adding a return); `functions_reserializing_parsed_frontmatter` and `functions_parsing_then_writing` (the door must contain no `parse_frontmatter` call); the new `write_target_buckets` scan (both new writers must classify SEAM-ROUTED — M1's two `contained = …` assignments bind a name the seed never tainted, M6's `mode = vault_io.guard_mode()` likewise binds a never-tainted name out of a value mentioning none, M8's `derive = getattr(self, "_get_file_name", None)` and `projected = entity.model_copy(update=…)` do the same (neither name is ever tainted, and `entity` is not the seeded name — the seed is `self._resolve_write_target(entity)`'s RETURN, bound to `resolved`), and `same_place = …` binds a name the fixpoint DOES taint, out of a value that mentions `source`, so the ordering-aware rebinding clause (which fires only on an Assign binding a tainted name out of a value mentioning NO tainted name) does not fire on any of them, and every `move_note`/`update_frontmatter_field` first positional in the door is still a name tainted by `source`; and `update_fields`' three-name head is legal by the clause that legalises the fallback itself — `resolved` is the seeded name, `file_path = resolved` is an Assign whose value mentions a tainted name, and `file_path = self.get_file_path(name)` rebinds a tainted name inside an `ast.If` whose test names it, which is AC-5's fifth ACCEPTED near-miss; the post-door `file_path = moved` lies AFTER the write call by position and so is outside the clause's span); WI-021's arm sweep and gate-placement pins (no new frontmatter arm, no new gate call); the new `door_calls_inside_note_lock` scan, which must stay EMPTY — `rename_note` holds no `note_lock` of its own and `update_fields` calls it AFTER its `with vault_io.note_lock(file_path)` block has exited.
```

```writes
path: obsidian_schemas/repositories/person.py
why: Task 4 — five one-line openers on the mutating body-writers, plus one comment on `_get_body_content`. Walls it joins: routing A/B/C; `tests/test_loud_fail_write.py`'s falsy-return classification map, which is keyed (function, ordinal) and bidirectional, so no falsy return may be added, removed or reordered inside the five classified functions; `tests/test_name_gate_wall.py:PERSON_FALSY_RETURN_FUNCTIONS` and its `len(sites) == 8`; the `write_target_buckets` scan.
```

```writes
path: obsidian_schemas/repositories/book.py
why: Task 5 — `BookRepository.save`'s CREATE fallback; `_get_file_name` untouched. Walls it joins: routing A/B/C; `character_class_strip_sites` (the existing `[<>:"/\|?*]` strip is not moved or duplicated); the `write_target_buckets` scan (SEAM-ROUTED).
```

```writes
path: obsidian_schemas/repositories/meeting.py
why: Task 5 — `MeetingRepository.save`'s CREATE fallback; `_get_file_name` untouched. Same wall set as `book.py`.
```

```writes
path: scripts/lint_vault.py
why: Task 11 — the `stem_name_divergence` arm in `check_structural`, `NOT_RENAMEABLE_MARKER`, `_gate_refusal_pattern`. Walls it joins: routing A/B/C over (PACKAGE_ROOT, SCRIPTS_ROOT), which is why the new arm is a read-only comparison and never a probe that writes; `tests/test_vault_path_required.py:FORBIDDEN_DEFAULT_PATTERNS` over `_code_lines`; `auto_fixable_emitter_checks` / `auto_fixable_branch_checks`, pinned by set equality against the WI-026 baseline's rows — the new issue must NOT be auto-fixable or that equality moves; `frontmatter_write_arms`, pinned to exactly one arm in `apply_fixes`; `address_splitting_implementations`; `skip_reason_literal_sites`, which must not gain `scripts/lint_vault.py` as a third home.
```

```writes
path: tests/derivations.py
why: Task 7 — `WriteTargetSite`, `SEAM_FUNCTION`, `path_taking_writer_names`, `write_target_buckets`, `door_calls_inside_note_lock` (ordering decision 5's structural half, asserted EMPTY in Task 10), and the `with … as` plus ordering-aware rebinding extensions to the taint machinery. This is the ONE module in the repo permitted to name `ast` (`modules_using_ast` is a set EQUALITY over PACKAGE_ROOT + TESTS_ROOT, asserted from three separate modules), so the scan lives here and nowhere else.
```

```writes
path: tests/test_provenance_write_seam.py
why: Tasks 2, 9, 10, 14 — AC-1, AC-2, the two seam unit checks (both authored in Task 2, including M2's read-direction arm), AC-2's non-AC arms (the door's IDEMPOTENCE, the half-failed rename's residual, the OCCUPIED-DESTINATION residual reached through `update_fields` — the raised leaf, the committed `name:` at the unmoved filename, the absent alias, the un-re-stamped entity, the byte-identical destination note, the re-run's no-op and the direct-`rename_note` recovery — `door_calls_inside_note_lock` asserted EMPTY over PACKAGE_ROOT with its planted both-ways battery — ordering decision 5 — M7's both-ways arm over a planted stamped BOOK note, which additionally constructs a `BookRepository` over the same temp vault and sets the guard mode to `"enforce"` explicitly so the refusal is attributable to M7's disjunct and not to an ambient mode, and M6's both-ways guard-mode arm, which drives `OBSIDIAN_SCHEMAS_WRITE_GUARD` through `tests/support.py:patcher:73` — the project's own zero-fixture `monkeypatch` stand-in, whose `setitem` restores the prior value on exit and POPS the key where it was unset, so no later check inherits a mode this module set, and which is the same helper `tests/test_concurrent_access.py:706`, `:737` already uses for that variable) and the wall-membership closure. NEW FILE, so it joins every derived population that sweeps TESTS_ROOT: the `ast` single-home equality (it must not import `ast` — it imports the scans from `tests/derivations.py`); `modules_using_ast`'s non-vacuity; `skip_reason_literal_sites` (it must not hand-type a `SKIP_REASONS` member — import it); and the check contract, so every AC-named function is a top-level zero-argument `def` that RAISES on failure and the module's first statement is `ensure_project_interpreter(__file__)`.
```

```writes
path: tests/test_write_target_seam_wall.py
why: Task 8 — AC-5's live half and its planted-escape battery. NEW FILE; same TESTS_ROOT wall set as above. It constructs no repository and plants only into a temp directory.
```

```writes
path: tests/test_stem_name_divergence_detector.py
why: Task 12 — AC-3, including one planted member per free variable Design §3a's sweep declares (row 8's non-`@` `type: person` shape, case-only, double-`@`, sub-directory, the non-string-`name:` near-miss, the blank-`name:` near-miss and the leading/trailing-whitespace `name:` that must FIRE — the LIST is the obligation, never its length, and Task 12's own text is its authority), each written as bytes into the temp copy. NEW FILE; same TESTS_ROOT wall set, PLUS the WI-026/WI-031 containment door in all five parts because it drives `lint_vault`'s mutating entry points: one `_temp_vault` constructor, `mutating_drive_vault_args` over this module's own source, no subprocess-capable import, no live-path token outside the door's body, and ZERO repository constructions.
```

```writes
path: tests/test_stem_divergence_baseline_shape.py
why: Task 13 — AC-4, threat-model M5's whole-file privacy wall, and its reader battery. NEW FILE; same TESTS_ROOT wall set. It reads `docs/stem-divergence-live-baseline.md` and executes nothing against any vault; its readers — the direction-table readers AND the `.md`-token privacy scan — are driven by both the live arm and the planted battery through the same functions, so each matcher's reach is proven rather than assumed. It imports `FORBIDDEN_DEFAULT_PATTERNS` from `tests/test_vault_path_required.py` rather than re-spelling it, which is also what keeps this module from becoming that wall's own counterexample.
```

```writes
path: tests/test_concurrent_access.py
why: Task 14, CONDITIONAL and predicted UNWRITTEN — it carries the count pins listed here over populations this item alters, and the LIST is the obligation rather than its length (`functions_reserializing_parsed_frontmatter` == 4, `functions_parsing_then_writing - writers` == {write_markdown_file}, `non_completed_write_sites` == 8, `base_repository_subclasses` == 4, `load_file_implementations` == 3 — five). The design holds all five still (the door calls no `parse_frontmatter` and returns no falsy value, and no repository class or `_load_file` is added), so the expected edit is NONE; the path is declared because WI-229 says a count pin over an altered corpus is named as an obligation, and a pin discovered to have moved must be edited to NAME its new member rather than bumped.
```

```writes
path: tests/test_name_gate_wall.py
why: Task 14, CONDITIONAL and predicted UNWRITTEN — `PERSON_FALSY_RETURN_FUNCTIONS` and `len(sites) == 8` pin the falsy-return universe over `person.py`, which Task 4 edits. Same rule as above: predicted unmoved, declared because it is a pin over an altered file, and edited to name a member rather than to bump a number if it moves.
```

```writes
path: tests/test_loud_fail_write.py
why: Task 14, CONDITIONAL and predicted UNWRITTEN — its classification map over PACKAGE_ROOT is keyed (module, qualname, ordinal) and asserted in BOTH directions, so a falsy return added, removed or reordered inside a classified function is RED. Tasks 3–6 add none. Declared for the same WI-229 reason.
```

## Wall Membership (WI-301) — the inbound half, derived and then RUN

The outbound question — does this item's own wall hold? — is AC-5. The inbound one is which STANDING
walls sweep the files this item adds and edits, and what each requires of them. The list below is
DERIVED, not remembered: sweep the resolved test roots for modules that read, in their own text or
through a helper they call under those same roots, the text of files they did not name at authoring
time (`python_files_under`, `rglob`, `iterdir`, `read_text` over a derived path), then read every
file the sweep returns at FILE granularity and discard noise by reading. Run 2026-09-25; it is a
FLOOR measured at a date and never a total, because this derivation has under-reached at its reading
step every time it has been run. Anything the RUN in Task 14 returns that this section did not name
is NAMED in the Build Log and satisfied — never worked around, and never satisfied by narrowing the
wall.

| wall | its universe | what it requires of this item's files |
|---|---|---|
| `tests/test_write_routing.py:test_filesystem_mutation_is_single_homed:87` (Walls A/B/C) | `python_files_under(PACKAGE_ROOT, SCRIPTS_ROOT)` | no filesystem-mutation capability, no non-read-only `os` member and no mutation-capable import outside `obsidian_schemas/vault_io.py`. The door moves through `vault_io.move_note`; the detector's checks are read-only; `Path.samefile`, `Path.exists` and `Path.resolve` are reads and legal; M6's `vault_io.guard_mode()` is a call on the already-imported `vault_io` module and names no `os` member, which is exactly why the mode is read through that function rather than through `os.environ` (`obsidian_schemas/vault_io.py:_env_setting:104-115`); M7's `type(entity).model_fields` is a class-attribute read that adds no import, no `os` member and no filesystem capability; M8's `getattr(self, "_get_file_name", None)` and `entity.model_copy(update=…)` are the same — an attribute read and a pydantic call, no import, no `os` member, and `_get_file_name`'s result is COMPARED and never turned into a path |
| `tests/test_loud_fail_harness.py:103`, `tests/test_name_gate_wall.py:_check_the_ast_capability_stays_single_homed:1132`, `tests/test_lint_vault_fix_rules.py:_check_the_derived_walls_this_item_joins:1956` | `python_files_under(PACKAGE_ROOT, TESTS_ROOT)`, a set EQUALITY | `ast` is named ONLY by `tests/derivations.py`. Four new test modules and two edited package modules each have exactly one legal way to obtain syntax: import the scan |
| `tests/test_loud_fail_write.py:_check_write_failure_raises_and_noops_keep_their_return:112` | `non_completed_write_sites(python_files_under(PACKAGE_ROOT))`, bidirectional map | every falsy return in a write path is classified, and a classified site that DISAPPEARS is red exactly as a new one is. `rename_note` must raise, never return falsy; the body-writers' returns must not move |
| `tests/test_concurrent_access.py:test_wi020_derivations_survive_the_routing:1060` | `python_files_under(PACKAGE_ROOT)` | the routing pins it carries, listed and not counted: 4 reserializing writers, the discrimination guard `{write_markdown_file}`, 8 falsy-return sites, 4 subclasses, 3 `_load_file`s |
| `tests/test_name_gate_wall.py:test_every_frontmatter_door_routes_through_the_semantic_gate:813` and `test_the_arm_sweep_resolves_the_floor_and_its_match_shapes:313` | `python_files_under(PACKAGE_ROOT, SCRIPTS_ROOT)` | every frontmatter write arm has exactly one gate call with a resolvable declaration. This item adds NO arm: the door delegates to `writer.update_frontmatter_field`, which already carries one |
| `tests/test_name_gate_wall.py:_check_wall_d:1107` | its own touched list | no new `parse_markdown_file` caller outside `obsidian_schemas/repositories/base.py`. The door reads nothing; `_load_file` is unchanged |
| `tests/test_company_name_contract.py:603-609`, `tests/test_address_splitter.py:102`, `tests/test_identity_endgame.py:1150-1151` | `python_files_under(PACKAGE_ROOT, SCRIPTS_ROOT)` and per-file slices | no second character-class strip implementation and no second address splitter. Book's and Meeting's existing strips are not moved or copied |
| `tests/test_lint_vault_fix_rules.py:_check_the_skip_reason_wall_reaches_the_script_without_moving_its_homes:1001` | `python_files_under(PACKAGE_ROOT, TESTS_ROOT, SCRIPTS_ROOT)`, a set EQUALITY | the `SKIP_REASONS` vocabulary keeps exactly two hand-typed homes. No new file may transcribe a member — import it |
| `tests/test_lint_vault_fix_rules.py:1703` and the WI-026 baseline legs | `auto_fixable_emitter_checks([LINT_VAULT_PATH])`, a set EQUALITY against the baseline's §1 rows | the new issue must NOT be auto-fixable, or the census-to-rule mapping and the committed baseline both go red |
| `tests/test_vault_path_required.py:323` | `("obsidian_schemas", "scripts")` over `_code_lines` | no `expanduser`, `Path.home()` or `/Users/` on an executable line of `scripts/lint_vault.py`. It does not reach `tests/`, which is why each new test module carries its own containment (and why AC-3's module ships the five-part door) |
| `tests/test_identity_endgame.py:590` | `python_files_under(PACKAGE_ROOT, TESTS_ROOT)` | the deleted `_email_index` attribute is named at zero sites. No new file may name it |
| `tests/test_fixture_vault.py` + `tests/fixture_vault.py:CORPUS_DIGEST:44` | `tests/fixtures/vault/` | the corpus is byte-frozen. Every battery materializes a TEMP copy and plants into that copy; no fixture note is added, edited or deleted, so no manifest+digest pair edit is in scope |
| `tests/ac_interpreter.py` + the conveyor's check contract | every module holding a `check:` | `ensure_project_interpreter(__file__)` is the module's FIRST statement, ahead of every package import, and every AC-named function is a top-level zero-argument `def` that signals failure by RAISING — a returned `False` exits 0 and is read as PASS |

MEMBERSHIP is closed by CALLING each of those predicates on the files' FINAL text in Task 14, never
by reasoning about which shapes match: the outcome turns on incidental spellings a reader cannot see.
A predicate that cannot be called in the build profile is declared LOUDLY in the Build Log and never
skipped. **Every row above is named in Task 14, and the two whose RUN is not a direct predicate call are
named there as such** *(second spec-review round, non-blocking note 3 — an earlier draft of Task 14
omitted wall D and the `_email_index` pin while this section claimed all of them were called, which is a
row satisfied by reasoning and is the exact failure WI-301's rule exists to close)*: the corpus-freeze row
runs as `tests/test_fixture_vault.py` under the floor command, and the check-contract row is the
conveyor's own per-criterion invocation, for which Task 14 asserts the two mechanical halves over the new
modules' source instead. `non_completed_write_sites` is re-run as one of Task 1's pins rather than in the
predicate list.

## Mitigation Folds

All EIGHT `kind: required` mitigations of the LATEST speaking `## Threat Model` round (2026-09-26,
round 6 — the SECOND section carrying that date), each folded into a `## Design` sentence AND an
Implementation-Plan task in the same edit.
Six land on Task 6 (four in the door's own body; M7 and M8 in `update_fields`' pre-write refusal one
frame over — M7 on its rename-side disjunction, M8 on its second clause), one on Task 2 (the stamp)
and one on Task 13 (AC-4's privacy wall), exactly as the modeler's
fences name them. Their batteries are Task 10 (M1, M3, M4, M6, M7, M8 — each pinned
both ways), Task 2's own check (M2) and Task 13's reader battery (M5, pinned both ways through the same
token function the live arm calls). M1–M7's `desc` values were re-emitted byte-identically by round 6
and are restated here unchanged; M8 is new in round 6.

**M7 is the SECOND fold in one class and is folded as the class, not as the case** (WI-226). Round 4's
M6 fold widened `update_fields`' pre-write refusal from one remembered conjunct into the door's whole
PRECONDITION class, with a table enumerating the refusal arms — and round 5's finding is INSIDE that
table: its M1 row answered "already refused earlier, by a different wall" and the wall it named,
`gate_write`, validates a `name` delta for exactly two declared types. The GENERATOR is therefore not
"the M1 row" but *a bound on a population asserted from the models and enforced by a predicate that
never reads them*. So this fold closes the generator — Design §2 now carries a second rule beneath the
table, **a refusal delegated to another wall is only as total as that wall's own DECLARED SCOPE, and
wherever the wall is narrower the residue is refused HERE** — restates the three sites that made the
unchecked claim (the M1 row, the `f"@{new_name}.md"` paragraph, Task 6's restatement) on the disjunct
instead, and DECLARES the next level's sweep: `BaseRepository.save`'s `@{name}.md` derivation is bounded
by METHOD OVERRIDE and so is structural rather than a member; ordering decision 3's alias guard and the
alias reconciliation are the two existing instances of the correct idiom; the table's remaining rows
delegate to the SYSCALL on an argument about what is knowable in the frame, which is a property of the
frame and not of a type; and the detector's `entity_type == "person"` guard is a declared narrowing over
vault bytes with its own reasoning. The sweep returned no fourth member.

**M8 is the THIRD fold in one class, and the class is one level ABOVE M7's — which is why closing M7's
generator did not close it** (WI-226). M7's fold closed *a bound enforced by a predicate that never reads
the models* and swept that level honestly; M8 came out of the SAME paragraph two rounds later, through
the fold's own new material — Design §5's capability-widening declaration, whose bound read *"the one
thing it does NOT widen is the rename branch, which M7 refuses for both types"*. That bound is
`name`-shaped, and `Book`'s filename is made of `title` and `author`
(`obsidian_schemas/repositories/book.py:BookRepository._get_file_name:340-355`) while `Meeting`'s is
made of `date`, `topics`, `attendees` and `meeting_id`
(`obsidian_schemas/repositories/meeting.py:MeetingRepository._get_file_name:208-231`). So the GENERATOR
is one rung up: **a guard keyed on the PERSON instance (`name`) of a predicate this document itself
states TYPE-GENERALLY** — its own divergence definition is *"the filename this type's own write rule
recomputes from the entity's current fields differs from the file it was parsed from"*, and every guard
the item had shipped keyed on the `name` reading of it. This fold closes that class rather than the
`{"title": …}` instance. Design §2 now carries a THIRD rule — **the pre-write arm has TWO obligations,
refuse a RENAME the door cannot complete AND refuse a WRITE that moves the type's own filename rule with
no rename to follow it** — and the clause discharging the second is keyed on
`getattr(self, "_get_file_name", None)`, the repository's OWN declared rule, so it covers `title`,
`author`, `date`, `topics`, `attendees` and `meeting_id` by construction rather than by enumeration and
stays correct if a base-class `_get_file_name` or a fifth type ever appears. It restates the two sites
that made the `name`-shaped claim — Design §5's widening bound and the M7 `## Edge Cases` entry's
*"unaffected"* sentence — on the rule instead of leaving them standing. NEXT LEVEL, declared: the other
eight write paths, asked one at a time whether any can leave a delta that moves the type's rule
unresolved — `save` and the two `save` overrides derive their own target and have no rename to
reconcile, and what they leave is AC-1's SIGNED trade (in-place divergence instead of today's fork),
accepted by decision and named in `## Scope Boundary` and `## Risk Analysis` rather than closed by a
clause; the five body-writers carry no frontmatter field delta at all, so no deriving field can move
through them; `rename_note` takes its destination from the CALLER, whose rule M7 makes true by
construction. INTERSECTION: a type declaring BOTH `name` and its own `_get_file_name` exists nowhere
today (`Person:79`/`Company:128` declare `name` and override nothing; `Book:139`/`Meeting:247` override
and declare no `name`) and is already total under the two clauses as written — its `name` delta goes to
the rename branch, its non-`name` deriving delta to M8's clause, its non-deriving delta writes. The
sweep returned no member the two clauses leave open, and one declared trade.

```fold
id: M1
desc: `rename_note` must refuse a destination whose RESOLVED path is not inside `self.vault_path`, raising before any `vault_io.move_note` call — the containment test `_resolve_write_target` already applies to the source, applied to the caller-supplied destination, resolved rather than string-compared so that a symlink inside the vault cannot point the move outside it.
design: `rename_note` refuses a `new_filename` whose RESOLVED destination is not inside `self.vault_path`, raising `ValueError` before any `vault_io.move_note` call — the same containment test `_resolve_write_target` already applies to the SOURCE, applied to the caller-supplied destination, resolved rather than string-compared so that a symlink inside the vault cannot point the move outside it.
landed: Task 6
work: **(M1) Contain the destination:** immediately after `destination = self.vault_path / new_filename`, raise `ValueError` unless `destination.resolve().is_relative_to(self.vault_path.resolve())`, with an `OSError`/`ValueError` out of the resolve treated as NOT contained, and raise BEFORE any `vault_io.move_note` call — resolved and never string-compared, because a dangling in-vault symlink is an escape the string cannot show. — verify: test_a_person_note_is_renamed_only_through_the_one_door_and_stays_reachable
```

```fold
id: M2
desc: The provenance stamp must be unforgeable from note content, asserted and not assumed — a note whose own frontmatter declares `_source_path` naming a DIFFERENT file must still resolve, through `_resolve_write_target`, to the file it was parsed from.
design: A note whose own frontmatter declares `_source_path` naming a DIFFERENT file still resolves, through `_resolve_write_target`, to the file it was parsed from, and Task 2's check asserts that READ direction rather than inferring it.
landed: Task 2
work: Then the READ direction, which is M2 and is the arm this check did not have: plant TWO person notes A and B in the temp vault where A's OWN frontmatter declares `_source_path: <B's path>` (written as bytes, never through `repo.save`), parse A with `parse_markdown_file`, and assert that `_resolve_write_target` answers A's own path, that `getattr(entity, "_source_path")` — verbatim the accessor `_resolve_write_target` reads — is A's path and is not B's, and that NOTHING the seam reads answers B (where the forged key ended up is a Build-Log observation, never an assertion, so the arm cannot go RED on a pydantic release that drops underscore-prefixed extras). — verify: test_the_parse_stamps_provenance_and_the_stamp_cannot_reach_a_note test_the_seam_returns_the_stamp_only_inside_this_vault
```

```fold
id: M3
desc: The case-only two-step must not move the note out of the `*.md` namespace — the staging name keeps the `.md` suffix, so a rename interrupted between the two moves leaves a note that Obsidian, the repository and `lint_vault` can all still see rather than a file no reader picks up.
design: The case-only two-step stages through `source.with_name(destination.stem + ".rename-tmp.md")`, so a rename interrupted between the two moves leaves a note that Obsidian, the repository and `lint_vault` can all still see rather than a file no reader picks up.
landed: Task 6
work: **(M3) Keep the staging name in the `.md` namespace:** the case-only branch stages through `source.with_name(destination.stem + ".rename-tmp.md")`, not `destination.name + ".rename-tmp"`, so an interrupted rename leaves a note all three `file_pattern` globs, `lint_vault` and Obsidian still see. — verify: test_a_person_note_is_renamed_only_through_the_one_door_and_stays_reachable
```

```fold
id: M4
desc: `rename_note`'s audit line must name the SOURCE path as well as the destination, so a relocation performed by `update_fields` on a consumer's behalf is reconstructable from logs.
design: `rename_note`'s audit line names the SOURCE path as well as the destination, so a relocation performed by `update_fields` on a consumer's behalf is reconstructable from logs.
landed: Task 6
work: **(M4) Name both ends in the audit line:** `logger.info("Renamed %s note from %s to %s", self.type_name, source.name, moved.name)` — the source as well as the destination, since after this item `update_fields` moves a file permanently on every name change. — verify: test_a_person_note_is_renamed_only_through_the_one_door_and_stays_reachable
```

```fold
id: M5
desc: AC-4's no-note-filename privacy wall must stay TOTAL over the whole committed artifact — the check's `.md`-token rule is exempted by TOKEN CLASS (a token containing `*`, i.e. a glob, beside the already-declared template literal `@{name}.md`) and NEVER by excluding fenced code blocks, because a fenced block is exactly where a re-run's pasted output lands and the exit attestation re-runs `lint_vault --report`, which names note filenames per path; the two `.md` tokens inside the artifact's current fences are `'*.md'` and `f"@{name}.md"`, so the token-class exemption is green against it as committed and the region exclusion buys nothing the narrower rule does not.
design: AC-4's `.md`-token privacy rule is TOTAL over the whole committed artifact — every `.md` token anywhere in `docs/stem-divergence-live-baseline.md`, inside a fenced code block exactly as much as outside one, must resolve to a path that EXISTS in this repo, or be the declared template literal `@{name}.md`, or CONTAIN a `*` and so be a glob rather than a filename; the exemption is that TOKEN CLASS and never a REGION, because a fenced block is precisely where the exit attestation's pasted output lands and §5's second re-run command is `scripts/lint_vault.py --vault "$VAULT" --report`, which reports issues PER PATH and therefore names note filenames by construction.
landed: Task 13
work: **(M5)** the privacy wall holds WHOLE-FILE in BOTH of its halves — no member of `tests.test_vault_path_required.FORBIDDEN_DEFAULT_PATTERNS` appears (IMPORTED, never re-spelled, or this assertion becomes its own offender), and every `.md` token the file names ANYWHERE — inside a fenced code block exactly as much as outside one — resolves to a path that EXISTS in this repo, or is the declared template literal `@{name}.md`, or CONTAINS a `*` and is therefore a glob rather than a filename; the exemption is that TOKEN CLASS and NEVER a region; tokenize with a character class that INCLUDES `*` (`re.findall(r"[\w@{}*./+-]+\.md", text)`); write NO fence toggle into the privacy path and NO non-vacuity guard on it; and the reader battery pins the scan through the SAME token function the live arm calls — MUST FIRE for a bare note filename on a prose line and for the SAME filename on a line INSIDE a fenced code block, MUST NOT FIRE for a `*.md` glob inside a fence, for `@{name}.md`, or for a repo-relative path to a file the test itself confirmed exists. — verify: test_the_stem_divergence_live_baseline_is_committed_and_shaped test_the_baseline_readers_reach_their_claimed_shapes
```

```fold
id: M6
desc: `rename_note` must FAIL CLOSED when the write guard is not enforcing, because every occupied-destination refusal this item relies on is conditional on it — `vault_io._move_locked:757-771` does `os.replace(source, target)` and destroys the occupied note instead of raising `NoteAlreadyExists` when `guard_mode() == "observe"` (WI-004's declared residual R9, `docs/concurrent-access.md:649-656`, acceptable while door 3 had one quarantine caller and not once this item drives it on every `update_fields` name change in three `-e` consumers), so the door reads the mode through `vault_io.guard_mode()` — never a second `os.environ` access in `base.py`, which `vault_io._env_setting:104-115` forbids in writing — and RAISES beside M1's containment block, before any `vault_io.move_note` call, naming the mode; pinned BOTH ways in Task 10 with the environment set and restored in a `finally` (the same idiom the M3 recorder and the half-failure delegate already use, since a zero-arg AC check takes no `monkeypatch` fixture): under `observe` a rename onto a destination occupied by a DIFFERENT note raises, the vault's filename SET is unchanged and BOTH files are byte-identical, while under the default `enforce` the same call still raises `NoteAlreadyExists` and an ordinary in-vault rename still moves, so the clause is neither a no-op nor a refusal of everything.
design: `rename_note` reads `vault_io.guard_mode()` and raises `ValueError` naming the mode unless it answers `"enforce"`, beside M1's containment block and before any `vault_io.move_note` call, because every occupied-destination refusal this item relies on is conditional on that mode — under `OBSIDIAN_SCHEMAS_WRITE_GUARD=observe` door 3 does `os.replace(source, target)` and DESTROYS the occupied note instead of raising `NoteAlreadyExists`.
landed: Task 6
work: **(M6) Fail closed when the write guard is not enforcing:** bind `mode = vault_io.guard_mode()` immediately after M1's containment block and, unless it equals `"enforce"`, `raise ValueError` naming the mode — before any `vault_io.move_note` call, beside the door's other precondition refusals. Read it through `vault_io.guard_mode()` and NEVER through `os.environ`: `base.py:9` already imports `os` and that spelling would build, but `obsidian_schemas/vault_io.py:_env_setting:104-115` reserves environment access to itself in writing and `vault_io` is already imported at `base.py:22`, so the call costs no import. Without this clause every occupied-destination refusal this item relies on is conditional on an environment variable: under `OBSIDIAN_SCHEMAS_WRITE_GUARD=observe`, `obsidian_schemas/vault_io.py:_move_locked:757-771` does `os.replace(source, target)` instead of raising `NoteAlreadyExists`, destroying the occupied note and returning the destination as a success, so the door would alias, `_adopt` and log a rename that overwrote a third party (WI-004's declared residual R9, `docs/concurrent-access.md:649-656`, acceptable while door 3 had one quarantine caller and not once this item drives it on every name change in three `-e` consumers). Do NOT widen this to `save`, the body-writers or `create_note`'s identical arm — that arm is AC-1(f)'s and stays WI-004's (Design §2, "M6's exact bound"). THE SAME CONDITION REFUSES EARLIER IN `update_fields`, IN THE ARM BELOW: the widened predicate is stated there, because a name change that reaches the door under `observe` would otherwise commit its content write first and raise after it. — verify: test_a_person_note_is_renamed_only_through_the_one_door_and_stays_reachable
```

```fold
id: M7
desc: `update_fields` must not fire its rename branch for an entity whose own type does not derive `@{name}.md`, because the fold's precondition table answers the M1 row with a wall that covers two declared types and the trigger that reaches it consults the model nowhere — `obsidian_schemas/name_gate.py:319-344` returns a `name` delta UNVALIDATED for every `declared_type` that is neither `person` nor `company` (the path-hostile refusal the table delegates to is `_PATH_HOSTILE_RE = re.compile(r"/")` for a person and `_COMPANY_PATH_HOSTILE_RE:351` for a company, and `update_fields` passes `declared_type=self.type_name`, which is `"book"` and `"meeting"` at `book.py:47-49` and `meeting.py:48-50`), while the trigger is `"name" in updates and updates["name"] != frontmatter.get("name", "")` (`base.py:454`) — the caller's dict against the note's frontmatter, never `type(entity).model_fields` — so a stamped Book or Meeting entity handed `{"name": <anything>}` (Prerequisites 7's generic consumer PATCH forwards an arbitrary body that may carry `name`) sets `renaming` True against a book note's absent `name:`, passes the widened disjunction with provenance present and the guard enforcing, passes the gate untouched, COMMITS the new `name:` at `base.py:490`, and only then reaches `rename_note(entity, f"@{new_name}.md")` where `@x/y.md` raises `WriteFailedError` from `os.link` against a missing parent (`vault_io.py:_move_locked:772-773`) and `@a/../../x.md` raises M1's containment `ValueError` — M1 holds in both, so nothing lands outside the vault, but the residual is an ungated caller-supplied `name:` committed into a note that then did not move, which is exactly the state this arm exists to prevent and which the detector cannot see because it fires only on `entity_type == "person"`; THIS ITEM creates the reachability, since today's `get_file_path(getattr(entity, "name", ""))` opener answers `None` for a Book and raises above the lock (`base.py:437-441`, `:354-365`) while Task 3's `resolved`-first shape binds the file from the stamp and runs the frame; so the trigger gains one conjunct keyed on the DECLARED FIELD and never on a type name — `"name" in type(entity).model_fields`, the same keying ordering decision 3 already uses for `aliases` — which makes Design §2's "`Book` and `Meeting` cannot reach it at all" structural instead of asserted and closes the M1 row for every type rather than for two, WITHOUT adding a containment conjunct (M1 stays the door's, so no `NameGateRefusal` is degraded) and without touching `gate_write` or the Tier-1 tables, which `## Scope Boundary` declares read-never-edited; pinned BOTH ways in Task 10 against a planted colliding Book group member the battery already builds: `update_fields(<a stamped book>, {"name": "x/y", "status": "…"})` raises before the content write with that note BYTE-IDENTICAL and the vault's filename SET unchanged, while the SAME entity through `update_fields(entity, {"status": "…"})` still succeeds and lands in that file and a Person name change still moves — so the conjunct refuses the branch and not every update.
design: `update_fields` refuses a `name` delta on an entity whose own class does not DECLARE `name` — the third disjunct of the same pre-write refusal, `"name" not in type(entity).model_fields`, keyed on the DECLARED FIELD and never on a type name — because `f"@{new_name}.md"` is not that type's filename rule and `gate_write` hands a `name` delta straight back UNVALIDATED for every `declared_type` that is neither `person` nor `company`, so the rename branch is reachable only for a type that derives `@{name}.md` BY CONSTRUCTION rather than by the trigger's silence.
landed: Task 6
work: **(M7) Refuse a `name` delta on a type that does not declare `name`:** the third disjunct is `"name" not in type(entity).model_fields` — the DECLARED field, read off the CLASS (`type(entity)`, never the instance: `obsidian_schemas/writer.py:108`'s own comment reserves that spelling for the pydantic v2.11+ deprecation, and an instance or `hasattr` spelling would answer differently for a note storing `name:` as an EXTRA, which is exactly the case that must still refuse) and never a type-name comparison, the same keying ordering decision 3 already uses for `aliases`; it is needed because `gate_write` hands a `name` delta straight back UNVALIDATED for every `declared_type` that is neither `person` nor `company` (`obsidian_schemas/name_gate.py:gate_write:319-344`, whose own comment reads *"a Book write is gated and handed straight back"*) while the trigger reads the CALLER's dict against the NOTE's frontmatter and consults the model nowhere — so without it a stamped Book or Meeting entity handed `{"name": <anything>}` has `frontmatter.get("name", "")` answer `""`, sets `renaming` True, passes the other two disjuncts, COMMITS the ungated caller-supplied `name:` at `base.py:490`, and only then raises out of `rename_note` (`@x/y.md` → `WriteFailedError` from `os.link` against a missing parent, `obsidian_schemas/vault_io.py:_move_locked:772-773`; `@a/../../x.md` → M1's containment `ValueError`), which is the committed-write-then-raise residual this whole arm exists to prevent and which the new detector cannot see because it fires only on `vf.entity_type == "person"`. Task 3's `resolved`-first binding is what makes that frame reachable at all — today's `get_file_path(getattr(entity, "name", ""))` opener answers `None` for a Book and raises above the lock (`base.py:437-441`, `:354-365`). Do NOT instead compose the destination with `self._get_file_name(entity)` for those two types: that ships a second filename rule through the door with no live direction table behind it (`## Scope Boundary`). — verify: test_a_person_note_is_renamed_only_through_the_one_door_and_stays_reachable
```

```fold
id: M8
desc: `update_fields` must REFUSE, before its content write, a delta that moves the entity type's OWN filename rule when no rename will follow it — because Design §5's capability-widening declaration bounds the newly-reachable Book/Meeting frame with "the one thing it does NOT widen is the rename branch, which M7 refuses for both types", and neither of those two types' filename rule reads `name`: `obsidian_schemas/repositories/book.py:_get_file_name:340-355` derives from `title` and `author` (`models.py:Book.title:160`, `:author:161`) and `obsidian_schemas/repositories/meeting.py:_get_file_name:208-231` from `date` (`:216`), `topics[0]` (`:219-220`), `attendees[:2]` (`:221-224`) and `meeting_id` (`:226`) (`models.py:Meeting:260-263`), so a delta touching any of those SIX declared fields carries no `name` key, leaves `renaming` False at `base.py:454` and therefore never evaluates the pre-write refusal at all (the whole predicate is `if renaming and (...)`), is handed back UNVALIDATED by `gate_write` for a non-person non-company `declared_type` (`obsidian_schemas/name_gate.py:319-344`), and is COMMITTED at `base.py:490` with nothing moved, no alias recorded for the stem the note is leaving behind and NO exception — a note whose type's own filename rule no longer recomputes to the file it lives in, which is verbatim this document's own type-general divergence predicate (Exploration Notes' type table, "that string ≠ the file it was parsed from") manufactured by the method that exists to end it, SILENT where `## Risk Analysis` claims every residual is loud and detector-visible, and invisible to Task 11's arm because it fires only on `vf.entity_type == "person"`; THIS ITEM creates the reachability exactly as it does for M6 and M7, since today `update_fields` opens `get_file_path(getattr(entity, "name", ""))` which for a Book is `_file_map.get("")` and raises ABOVE the lock (`base.py:437-441`, `book.py:get_file_path:326-338`) while Task 3's `resolved`-first shape binds the file from the stamp and runs the whole frame — the premise Design §5's declaration states in its own words — and the route is external and already singled out by this item (`docs/wi-029-consumer-audit.md:84`, `routers/entities.py:461` forwards "an arbitrary HTTP PATCH dict" and is the ONE consumer path to those two repositories, `:137`), so an ordinary `PATCH /api/entities/book/{name}` body `{"title": …}` is the trigger; the refusal is therefore one more DISJUNCT on the same in-lock pre-write arm Task 6 already prescribes, evaluated independently of `renaming` and keyed on the REPOSITORY'S OWN DECLARED FILENAME RULE rather than on a type name or a remembered field list — `derive = getattr(self, "_get_file_name", None)`, and when it is not None and `not renaming`, project the delta onto the entity's declared fields (`entity.model_copy(update={k: v for k, v in updates.items() if k in type(entity).model_fields})`, which preserves the private stamp per Design §1) and `raise ValueError` naming the method, the field(s) at issue and THIS precondition when `derive(projected) != derive(entity)`; the comparison is DELTA-RELATIVE (`derive(projected)` against `derive(entity)`, never against `file_path.name`) so that an ALREADY-divergent Book or Meeting note — the live "book-titled file holding a person note" class and its siblings — stays writable for every delta that does not move its rule further, and the `not renaming` conjunct is what keeps the disjunct from ever reaching a Person or Company, whose rule IS `@{name}.md` and whose `name` delta the rename branch reconciles, so the clause stays total if the `BaseRepository.save` collapse `## Scope Boundary` books as a separate item ever puts `_get_file_name` on the base class; this ADDS NO capability and makes `## Scope Boundary`'s own stated alternative real instead of asserted — that section declines to teach the door Book's and Meeting's filename rule on the ground that "where refusal costs nothing anyone does today", and refusal is what this disjunct supplies — so the door learns no second filename rule, no Book or Meeting note is renamed, `gate_write` and the Tier-1 tables stay read-never-edited, and `save`, the two `save` overrides and the five body-writers are all untouched, none of them having a rename to reconcile; pinned BOTH ways in Task 10 on the same planted stamped Book the M7 arm already builds, with `OBSIDIAN_SCHEMAS_WRITE_GUARD` set to `"enforce"` explicitly for the arm (the M6 rule, WI-149) — REFUSED: `update_fields(<a stamped book at "Old Title - Author.md">, {"title": "New Title"})` raises `ValueError` whose message names the filename-rule precondition and not provenance, the guard mode or the type declaration (so the arm cannot pass on a sibling disjunct), the vault's filename SET is unchanged, and the book note is BYTE-IDENTICAL to the bytes the test wrote — which is the assertion that distinguishes refusing before the content write from committing it, and is the whole finding, since without the disjunct that file comes back carrying `title: New Title` at its old filename with no alias and no exception; the same for `{"author": …}` on that Book and for `{"date": …}` and `{"topics": [...]}` on a planted stamped Meeting, so the clause is shown to cover the RULE and not one field; ACCEPTED, three arms so it refuses the delta class and not every update: the SAME book entity through `update_fields(entity, {"status": "read"})` still SUCCEEDS and lands in that file (`models.py:Book.status:163` feeds no filename — this is the arm Task 10's M7 ACCEPTED half already asserts and it must stay green), an ALREADY-divergent planted Book whose file does not match its own rule still accepts a `{"status": …}` delta (the arm that fails a `derive(projected) != file_path.name` spelling), and a Person name change in the same vault still MOVES through the door exactly as the arms above assert (the control that fails a disjunct written without the `not renaming` conjunct).
design: `update_fields` refuses, before its content write, a delta that moves the entity type's OWN filename rule when no rename will follow it — the same pre-write arm's second clause, `not renaming and derive is not None and derive(projected) != derive(entity)`, where `derive = getattr(self, "_get_file_name", None)` and `projected` is `entity.model_copy(update={k: v for k, v in updates.items() if k in type(entity).model_fields})` — keyed on the REPOSITORY'S OWN DECLARED FILENAME RULE and never on `name` or on a type name, and DELTA-RELATIVE (`derive(projected)` against `derive(entity)`, never against `file_path.name`) so that an ALREADY-divergent note stays writable for every delta that does not move its rule further.
landed: Task 6
work: **(M8) Refuse a delta that moves the entity type's OWN filename rule when no rename will follow it — the arm's SECOND CLAUSE, which fires where `renaming` is FALSE:** bind `derive = getattr(self, "_get_file_name", None)` and, when it is not `None` and `not renaming`, project the delta onto the entity's declared fields — `projected = entity.model_copy(update={k: v for k, v in updates.items() if k in type(entity).model_fields})`, which preserves the private stamp (Design §1, "Survives `model_copy`") and keeps an undeclared caller key out of a comparison it could not have moved — and `raise ValueError` naming the METHOD, the field(s) at issue and THIS precondition when `derive(projected) != derive(entity)`. Compute `derive(entity)` FIRST and outside any `try`; wrap only `derive(projected)`, and treat ANY exception out of it as *the rule cannot be recomputed over this delta* and raise the same `ValueError` — `model_copy(update=…)` does not validate, so a delta supplying a non-string `title` or a non-list `topics` would otherwise leak an `AttributeError`/`TypeError` out of `_get_file_name`; fail closed, the direction M1 takes with an `OSError` out of its own resolve. Read it off `self` and never off a type list: `_get_file_name` is declared on exactly `obsidian_schemas/repositories/book.py:BookRepository._get_file_name:340` and `obsidian_schemas/repositories/meeting.py:MeetingRepository._get_file_name:208`, so `derive` is `None` for `BaseRepository`, `PersonRepository` and `CompanyRepository` and the clause is STRUCTURALLY inert for the two types whose rule is `@{name}.md`. Compare DELTA-RELATIVELY (`derive(projected)` against `derive(entity)`) and NEVER against `file_path.name`: the latter spelling refuses every write to an already-divergent Book or Meeting note, which is the live "book-titled file holding a person note" class this item exists to repair. Keep the `not renaming` conjunct: a `name` delta on a type that declares `name` belongs to the rename branch, which reconciles the rule by moving the file, and a `name` delta on a type that does not is M7's clause one line up. It is needed because the rename-side predicate is the WHOLE of `if renaming and (…)` while `Book`'s filename is made of `title` and `author` (`book.py:346`, `:350-353`) and `Meeting`'s of `date`, `topics`, `attendees` and `meeting_id` (`meeting.py:216`, `:219-226`) — six DECLARED fields (`obsidian_schemas/models.py:Book.title:160`, `:author:161`; `obsidian_schemas/models.py:Meeting:260-263`) — so without it a stamped Book handed `{"title": "New Title"}` leaves `renaming` False, evaluates no disjunct at all, is handed back UNVALIDATED by `gate_write` (`obsidian_schemas/name_gate.py:gate_write:319-344`), COMMITS at `base.py:490`, moves nothing, records no alias for the stem it is leaving behind and raises nothing — the item's own type-general divergence, manufactured silently, and invisible to Task 11's `vf.entity_type == "person"` arm. Do NOT instead rename the note by composing `self._get_file_name(entity)`: the rule is recomputed here only to COMPARE, never to build a path, and the door learns no second filename rule (`## Scope Boundary`). — verify: test_a_person_note_is_renamed_only_through_the_one_door_and_stays_reachable
```

## Verification

**Happy path (the smoke test).** In a temp copy of the frozen corpus, load `@Quillam Ostrivane.md`
through `repo._load_file`, append a timeline entry, and observe that the entry is in THAT file, that
`@Quillam Lumbrek.md` and `@Quillam Ostrivane Lumbrek.md` are byte-identical, and that the vault's
filename set is unchanged. That one sequence is false today on every one of the nine write paths and
is the Intent in miniature.

**The per-path minimal mutation table**, so AC-1's sweep is executable without a judgement call.
Each mutation touches NONE of that type's filename-deriving fields, which is what makes the cell
measure provenance against derivation:

| path | mutation | note |
|---|---|---|
| `BaseRepository.save` | set `person.title` (the JOB title, which names nobody and feeds no filename), then `repo.save(entity, body=<the note's current body>)` | the body is read from the subject's own file via `parse_markdown_file(path).body`; passing `""` over a note with body content raises `BodyTruncationError` (WI-126) and would grade the guard rather than the seam |
| `BaseRepository.update_fields` | `repo.update_fields(entity, {"title": "…"})` | no `name` key, so the rename branch does not fire |
| `append_to_timeline` | `repo.append_to_timeline(person, "### … \n- …")` | |
| `append_to_body_section` | `repo.append_to_body_section(person, "Notes", "- …")` | `create_if_missing` defaults True |
| `add_to_discuss_item` | `repo.add_to_discuss_item(person, "…")` | |
| `update_to_discuss_item` | add an item FIRST, then `repo.update_to_discuss_item(person, "…", True)` | it returns False and writes NOTHING when the item is absent, so an un-seeded cell would assert over a no-op |
| `remove_to_discuss_item` | add an item FIRST, then `repo.remove_to_discuss_item(person, "…")` | same reason |
| `BookRepository.save` | set `book.status` or `book.description` — never `title` or `author` — then `repo.save(entity, body=<the note's current body>)` | the WI-126 body guard is entity-type-AGNOSTIC (`obsidian_schemas/writer.py:write_markdown_file:285-302`), so row 1's constraint applies here identically; the planted Book/Meeting group members may instead be written with NO body at all, in which case the plain `repo.save(entity)` is legal *(third spec-review round, non-blocking note 3)* |
| `MeetingRepository.save` | set `meeting.tags` — `Meeting` declares `type`, `date`, `attendees`, `topics` and `meeting_id` (`obsidian_schemas/models.py:Meeting:259-263`) and INHERITS `tags` from `BaseEntity` (`obsidian_schemas/models.py:40`), so `tags` and `type` are the only two of its six fields that feed no filename rule and `tags` is the legal minimal mutation *(the citation previously spanned the wrong lines for `tags`; second spec-review round, non-blocking note 5)*; then `repo.save(entity, body=<the note's current body>)` on the same rule as the two rows above | |

**Failure modes that must fail gracefully, each asserted:** a DIRECT rename onto an occupied destination
(`NoteAlreadyExists`, both files byte-identical); **an `update_fields` NAME CHANGE onto an occupied
destination — the same refusal reached one frame up, where the content write has already committed
(`NoteAlreadyExists` the LEAF and not a pre-check `ValueError`, the vault's filename SET unchanged, the
DESTINATION note byte-identical, and the SOURCE note carrying its new stored `name:` at its old filename
with NO alias and the entity still stamped there — the residual asserted and not described, with the
re-run shown to be a no-op and the documented direct-`rename_note` recovery driven)**; a rename of a
symlinked source (`WriteFailedError`,
unmoved); a rename of an entity with no provenance (`ValueError`); a save of an entity whose stored
name the DOOR refuses (`NameGateRefusal` carrying the branch's `pattern`, no file changed); an
`update_fields`/body-writer call with no provenance on an unloaded repository (`ValueError`, no note
created); **an `update_fields` NAME CHANGE on an entity with no provenance whose name the repository CAN
resolve (`ValueError` raised before anything is written, the note BYTE-IDENTICAL afterwards, no new name
committed, no alias appended, no file moved — the residual state is nothing; and the same unstamped
entity's non-rename update, and its update echoing the UNCHANGED name, both still succeed)**; an entity
stamped in another vault (treated as unstamped); a note that cannot be decoded
(reported `unreadable_note`, never divergent); a person note whose stored `name:` is blank or
whitespace-only (never reported as divergent — the arm's `stored.strip()` conjunct, plant (vi));
**a rename, and an `update_fields` name change, attempted while `OBSIDIAN_SCHEMAS_WRITE_GUARD` is
`observe` (`ValueError` naming the mode, raised before any `vault_io.move_note` call and — for
`update_fields` — before its content write, the filename SET unchanged and every file byte-identical,
while a non-rename update under the same mode still succeeds: M6)**; **an `update_fields` call carrying a
`name` key on a STAMPED entity whose own type declares no `name` — a `Book` or `Meeting`, with or without
a stored `name:` extra (`ValueError` naming the type-declaration precondition, raised before the content
write, the note BYTE-IDENTICAL, the filename SET unchanged, for the escaping and the non-escaping
spelling alike, while that same entity's `{"status": …}` update still succeeds and a person's name change
still moves: M7)**; **an `update_fields` call on a STAMPED `Book` or `Meeting` carrying NO `name` key but
touching one of the six fields that type's own filename rule is made of — `title`/`author` for a Book,
`date`/`topics`/`attendees`/`meeting_id` for a Meeting (`ValueError` naming the FILENAME-RULE
precondition, raised before the content write, the note BYTE-IDENTICAL, the filename SET unchanged; a
non-string value for such a field refused with that same `ValueError` and never an `AttributeError`
leaking out of `_get_file_name`; while a `{"status": …}` on the same book, a `{"tags": …}` on the same
meeting, any delta on an ALREADY-divergent note that leaves its rule where it found it, and a person's
name change all still succeed: M8)**; and — the threat model's four door mitigations — a
rename to a destination that resolves outside the vault in any of its three spellings (`ValueError`,
nothing moved, nothing hard-linked outside: M1), a case-only rename interrupted between its two moves
(the residual file is inside `*.md` and every reader still sees it: M3), and a successful rename whose
audit line names the source as well as the destination (M4). Each of those four, and M7 and M8 one frame
over in `update_fields`, is pinned BOTH ways in
Task 10 — M6's second direction being that under the default `enforce` the same occupied-destination
call still raises `NoteAlreadyExists` and an ordinary in-vault rename still moves, the arm that stops
a fail-closed clause from passing by refusing everything; M7's being that the same book entity's
non-`name` update still succeeds and a person's name change still moves; and M8's being the four
ACCEPTED arms that separate a clause reading the type's RULE from one refusing every Book and Meeting
write — a non-deriving delta on each of the two types, an already-divergent note still writable, and a
person's name change still moving. The stamp's READ direction is a
correctness arm rather than a failure mode and sits with Task 2's check: a note declaring
`_source_path` for a DIFFERENT file still resolves to its own (M2).

**Four further arms are STRUCTURAL rather than behavioural**, named here so the verification set is
complete: the door is IDEMPOTENT on a re-run — second call after a REAL move, no `move_note`, no
duplicate alias, filename set unchanged, asserted on a vault whose spelling the test itself made
divergent from its resolved form so the file-identity branch key is what makes it pass, and beside it
the half-failure residual asserted directly (alias write forced to raise: the note IS moved, the stamp
IS the destination, the old stem is NOT in `aliases`, the re-run repairs none of it, and the documented
one-field recovery does) (Task 10); `door_calls_inside_note_lock` is EMPTY over `PACKAGE_ROOT`, so no
caller holds a note lock across the two-lock door and `update_fields`' door call is provably outside
its own lock (Task 10, ordering decision 5); the detector's planted members close the free
variables the frozen corpus is unanimous about, one plant per variable and the list is the obligation
rather than its length (Task 12, Design §3a) — a non-`@` note carrying
`type: person` (live row 8), a case-only divergence (live row 3), a double-`@` stem, a
sub-directory note and a stored `name:` carrying leading/trailing whitespace all FIRE, while a
non-string `name:` and a blank `name:` do NOT; and AC-4's privacy
wall over the committed live-vault artifact is TOTAL in both halves and pinned BOTH ways through the
same token function the live arm calls (Task 13, Design §4a, threat-model M5) — a bare note filename
fires whether it sits in prose or inside a fenced code block, while a `*.md` glob, the `@{name}.md`
template literal and an existing repo path do not.

**Integration — the downstream consumers that must still work.** The three repositories install `-e`
and are outside this tree's write authority, so this is verified by the committed audit rather than
by a test that pretends to reach them: 19 of 19 call sites on the nine changed paths are on LOADED
entities, 0 `auto_load=False` constructions, 0 reconstructions feed a write, 0 consumer call sites on
`BookRepository.save`/`MeetingRepository.save`, and exactly one consumer-visible ROUTE whose behaviour
changes (HAL9000's generic entity PATCH at `routers/entities.py:461`, disclosed in Dave's signed
read-back). What that route's behaviour changes TO is enumerated in Prerequisites 7 and not compressed
into a count: the MAIN arm (a name change now moves the file and keeps an alias), four disclosed RAISE
arms beside it (no provenance; a `Book`/`Meeting` `name` delta, M7; an occupied destination; and a
`Book`/`Meeting` delta that moves that type's own filename rule, M8), and the widening Design §5
declares (a `Book`/`Meeting` delta that does NOT move that rule now SUCCEEDS where today the method
raises above the lock).
Inside the tree, `PersonRepository.create_stub`, `find_or_create_stub` and `resolve_or_create` are
CREATE paths and keep today's behaviour by construction — their entities carry no stamp and their
target is the name-derived filename.

**Regression — DERIVED, not inherited.** Sweeping the resolved test roots for modules that name a
`## Write Targets` path in their own text returns twenty-four: `tests/test_write_routing.py`,
`tests/test_vault_path_required.py`, `tests/test_phone_normalization.py`,
`tests/test_name_gate_wall.py`, `tests/test_name_gate_refusals.py`,
`tests/test_name_gate_identifiers.py`, `tests/test_name_gate_delta_rule.py`,
`tests/test_name_gate.py`, `tests/test_loud_fail_write.py`, `tests/test_loud_fail_parse.py`,
`tests/test_loud_fail_harness.py`, `tests/test_lint_vault_fix_rules.py`,
`tests/test_lint_vault_fix_gate.py`, `tests/test_identity_endgame.py`,
`tests/test_fixture_vault.py`, `tests/test_company_name_contract.py`,
`tests/test_address_splitter.py`, `tests/test_ac_interpreter.py`, `tests/support.py`,
`tests/record_identity_golden.py`, `tests/identity_fixture.py`, `tests/fixture_vault.py`,
`tests/derivations.py`, `tests/ac_interpreter.py`. Those are the modules that assert INTO the edited
surfaces and each must be read individually if it goes red. They are a SUBSET of the regression
oracle, not the whole of it: the whole of it is the floor, because `test_repositories.py`,
`test_concurrent_access.py`, `test_identity_index.py`, `test_resolve_or_create.py`,
`test_writer.py`, `test_parser.py`, `test_models.py`, `test_wi126_body_preservation.py` and
`test_loud_fail_load.py` exercise the changed write paths behaviourally without naming a path in
their text.

**The floor.** One command, absolute, cwd-independent:

```
/Users/davewascha/Workspaces/obsidian-schemas/.venv/bin/python -m pytest \
    /Users/davewascha/Workspaces/obsidian-schemas/tests -q
```

GREEN, with a case count no LOWER than Task 1's recorded baseline. The count itself is
informational and is recorded in the Build Log rather than asserted: the invariant is DIRECTIONAL —
a drive that lands fewer cases than the previous run without explanation has silently lost a test
file.

**Close-out, OUTSIDE the cage — the live replay (WI-173).** This item exists because something real
is broken in a real vault, so a hermetic battery is not the whole of Verification. After the build,
before the ship commit, the conductor:

1. Re-runs `docs/stem-divergence-live-baseline.md` §0's script verbatim against the live vault and
   compares the direction TABLE, not merely the count — a new row, or a row whose (b2)/(b3) answer
   has moved since 2026-09-21, is a drift report that must be resolved before the repair.
2. Performs the repair per the committed direction table: 7 RENAME (one case-only) through
   `BaseRepository.rename_note`, 1 MERGE by hand, plus the four booked hand repairs. **The repair
   shell must not carry `OBSIDIAN_SCHEMAS_WRITE_GUARD` set to anything but `enforce`** — under
   `observe` every one of those renames raises `ValueError` naming the mode and nothing moves (M6),
   which is a loud, zero-damage stop rather than a corruption, and the fix is to unset the variable
   and re-run. This is the one step of this procedure that runs outside the cage in whatever
   environment the conductor's shell supplies, which is why the door checks rather than assumes
   (Prerequisites 9).
3. Re-runs the same script and `scripts/lint_vault.py --vault "$VAULT" --report` — `--report`/`-q`,
   never `--fix` — and fills §5's exit column, including the post-build HEAD.
4. Redacts before recording: counts, classes and directions only; no stem, no stored name, no note
   bytes, no absolute path. The run is live; the transcript is not.

**One reading a conductor must not misdiagnose at step 3** *(threat model round 2's carried-forward
note, folded here because this procedure's ship condition is what makes it matter)*. During a
SUCCESSFUL case-only rename — row 3, the one such live row — the M3 staging note is visible to a
concurrent `load()`, and `move_note`'s link-then-unlink means a sub-window in which BOTH paths exist, so
a `PersonRepository` loaded in that instant sees two notes carrying one identifier and records a
`.conflicts` row. It is two syscalls wide, on one branch, for one row. Read a conflict observed while
that repair is mid-flight as THIS window and re-measure once the door has returned; it is not a new
duplicate, and it is the one way the ship condition below can read non-zero against a correct repair.

The item is NOT done until the divergence count and `len(PersonRepository($VAULT).conflicts)` both
read zero at exit. That is a declared SHIP CONDITION on this item, enforced at the conductor's ship
door: a `kind: precondition` fence is HEAD-probed before the build spawn and cannot carry a
post-build act, and a `kind: command` AC would point an automated battery at Dave's live vault on a
path he did not authorize per run.

## Scope Boundary

**What we are NOT doing:**

- **Not rewriting incoming references.** A renamed stem's `[[wikilinks]]`, `attendees:` entries and
  `company:` values become linter WARNINGS at a measured volume (24 + 14). Rewriting them would make
  the repair a second mutating authority over notes this item never typed.
- **Not teaching `check_links` to resolve through `aliases`.** It is a change to a shipped resolver
  with its own both-ways pinning obligation, it improves `check_links` for reasons unrelated to
  divergence, and it belongs to `lint_vault`'s own backlog. If the measured noise makes it worth
  doing it is a separate work item, and precondition (c) is the evidence that would justify minting
  it.
- **Not auto-fixing divergence.** Approach D stays rejected and AC-3(d) makes the rejection
  enforceable: relocation is the highest-blast-radius act in the tool and per-note direction is a
  judgement no auto-fix can make.
- **Not refusing the write.** Approach E's direction is right and its ordering is unshippable: it
  would turn every consumer write against a live divergent note into an exception before the repair
  has run, in three repositories this item cannot patch.
- **Not re-keying the cache or `_file_map` on the path.** Approach F rewrites the resolution core
  WI-125/WI-023 just settled. The shadowing of a collision's loser remains a read-side defect,
  remains visible on `.conflicts`, and is repaired by the direction table's merge rows rather than by
  code.
- **Not collapsing Book's and Meeting's `save` overrides into `BaseRepository.save`.** It is the
  tempting "while I'm here" refactor, it would be a genuine improvement, and it would move the
  population every criterion here quantifies over. Separate item.
- **Not repairing `_get_cache_key`'s strip asymmetry** (`base.py:319-321` lowercases without
  stripping while `get`/`get_file_path` look up `name.lower().strip()`). Pre-existing, low-severity
  because YAML strips plain scalars, and non-load-bearing precisely because nothing in the write path
  consults either mapping after this item. It is a resolution-core question in the WI-125/WI-023
  neighbourhood.
- **Not routing the two read-side sites through the seam.** `PersonRepository._get_body_content` and
  `create_stub`'s lost-create-race recovery share the root cause; the first returns `None` on a miss
  and writes nothing, and the second is correct as written. They are named in Design §5 so a builder
  does not reach for them, and each gets at most one comment line.
- **Not growing the frozen corpus.** Every planted member lives in a materialized TEMP copy.
  `CORPUS_DIGEST` is untouched.
- **Not performing the live repair from inside the cage.** The repair, the hand repairs and the exit
  attestation are conductor acts; a caged builder's state writes are reverted at the merge boundary,
  so a plan-task replay would change nothing and report success.
- **Not repairing `vault_io`'s `observe`-mode fail-opens.** Three refusals in that module are
  downgraded to a WARNING-and-proceed under `OBSIDIAN_SCHEMAS_WRITE_GUARD=observe` —
  `write_note`'s precondition mismatch, `create_note`'s no-clobber and `_move_locked`'s occupied
  destination (`obsidian_schemas/vault_io.py:_refuse:188-199`, `:create_note:712-718`,
  `:_move_locked:757-771`). They are WI-004's declared residual R9
  (`docs/concurrent-access.md:649-656`) and `obsidian_schemas/vault_io.py` is on the unchanged-files
  list below. M6 does not touch any of them: it refuses at the DOOR THIS ITEM SHIPS, which is the
  only one whose blast radius this item creates. Repairing door 2's arms would move `create_note`'s
  behaviour, which AC-1(f) leans on, and belongs to WI-004's backlog.
- **Not widening `gate_write` to a third type, and not teaching the door Book's or Meeting's filename
  rule** *(the bound M7 declares for itself, 2026-09-26)*. M7 refuses a `name` delta on a type that
  declares no `name`; it does not make `name_gate.py` validate one for `book` or `meeting` (that file is
  on the unchanged list below, the Tier-1 tables are read and never edited, and widening the gate is a
  second behaviour with its own both-ways pinning obligation), and it does not compose the rename
  destination with `self._get_file_name(entity)` for those two types. That second option would be a NEW
  capability — renaming book and meeting notes by their derived stem — against 0 measured consumer call
  sites (Prerequisites 7) and with no live direction table behind it, where refusal costs nothing anyone
  does today. The one live instance of the shape, a book-titled file holding a person note, is already a
  BOOKED HAND REPAIR in `docs/stem-divergence-live-baseline.md` §4 and stays there. **M8 is this
  non-action made REAL rather than a second exception to it** *(2026-09-26)*: this bullet says refusal
  is the right answer where teaching the door a second filename rule costs more than it buys, and M8's
  clause is that refusal. It recomputes `self._get_file_name` only to COMPARE the delta against the
  entity, never to compose a destination; `rename_note` is untouched, no Book or Meeting note is
  renamed, and `_get_file_name` reaches no rename path.

- **Not applying M8's clause to `save` or the two `save` overrides, and not refusing the divergence
  they leave** *(the bound M8 declares for itself, 2026-09-26)*. Those three derive their own target
  from the entity's current fields and have no rename to reconcile, so after this item a `save` of an
  entity whose deriving fields the caller changed lands in the PARSED file rather than forking a second
  note. That is AC-1's signed promise and `## Verified Diagnosis` 1's whole point — a refusal there
  would refuse the criterion — so the resulting in-place divergence is an ACCEPTED trade against today's
  fork, named in Design §2's sweep and `## Risk Analysis` rather than closed by a clause. For a Book or
  Meeting subject it is outside the new detector's person-only arm, the same detector-blind class as the
  COMPANY residual, and it is the conductor direction table's business.
- **Not widening WI-022's seven mangled company notes into this build.** They ride the same conductor
  repair run if the direction table covers them; the library change already reaches `CompanyRepository`
  for free, since it declares neither `save` nor `get_file_path`.

**Unchanged files the builder must not touch:** `obsidian_schemas/vault_io.py` (the three doors are
used as they are — `move_note`'s contract is exactly what the item needs, and widening the wall's
enumeration to its terminal writes would redden the door the item ships through),
`obsidian_schemas/name_gate.py` and `obsidian_schemas/name_validation.py` (the gate's name output is
an identity — WI-021's ruling — and the Tier-1 table is read, never edited),
`obsidian_schemas/writer.py` (`model_to_frontmatter`, `write_markdown_file` and the three sibling
leaves are consumed unchanged), `tests/fixtures/vault/**` and `tests/fixture_vault.py`'s manifest and
digest, `docs/stem-divergence-live-baseline.md` and `docs/wi-029-consumer-audit.md` (conductor
preconditions: read, never written), `docs/vault-shape-census.md`, `state/**`,
`pipeline-runners.yaml`, and the `## Intent` and `## Acceptance Criteria` sections of this document,
which are hash-signed.

## Risk Analysis

| risk | likelihood | impact | mitigation |
|---|---|---|---|
| A consumer's `save()` now lands in a different file than it did yesterday, and something downstream depended on the old target | low | high — it is a live vault | The audit measured it: 19/19 consumer sites are on LOADED entities, so the new target is the note they READ. The one behaviour change a consumer can observe (HAL9000's generic PATCH now MOVES on a name change) is disclosed in Dave's signed read-back rather than discovered |
| `update_fields` now MOVES a file on every name change, permanently | certain (it is the design) | medium — incoming references go stale | On every name change whose MOVE COMPLETES the old stem is kept as an alias, so the library's own resolvers and Obsidian both still find the note; only this project's linter resolves by stem, and the resulting warning volume is measured (24 + 14) and accepted knowingly. **The alias is NOT claimed unconditionally** *(corrected 2026-09-26 after the fourth spec-review round, which found this mitigation false for the sub-population whose move cannot complete)*: where the door raises before the move — an occupied destination, a symlinked source — no alias is appended and no file moves, and the residual is the row below. Where the move completes and only the alias write raises, the alias is the one thing missing and the row two below it owns that |
| An `update_fields` name change whose destination `@{new_name}.md` is ALREADY OCCUPIED by a different note (or whose source is a symlink): the content write commits and the door then raises, leaving the note carrying its NEW stored name at its OLD filename with no alias, and an exception on a successful write | low but ORDINARY — no race, no configuration, no exotic type; the direction table measures the occupied-destination shape at 1 of 8 live rows (`docs/stem-divergence-live-baseline.md` §2, the MERGE row) and HAL9000's generic PATCH is a live route to it (Prerequisites 7) | medium — a divergence manufactured by the method that exists to end them, and for a COMPANY subject it is outside the new detector's `vf.entity_type == "person"` arm | ACCEPTED, with the residual and its recovery stated as a RULE over the precondition table's whole NO half rather than as one more case (Design §2, "The COMPLEMENT of that rule"): remove the cause — for an occupied destination that is the direction table's MERGE, a conductor judgement the door is specified never to make — then call `repo.rename_note(entity, f"@{new_name}.md")` DIRECTLY and re-bind the entity from the returned path; a re-run of `update_fields` is safe and completes nothing, because the committed name is now the stored one. Removing it by ORDERING is unavailable, not merely unchosen — the door's own alias write invalidates the content write's `precondition=stamp` and would turn every successful rename into an `ExternalWriteConflict` (`obsidian_schemas/vault_io.py:write_note:685-698`), and AC-2's signed `why` prescribes write-then-move — and removing it by PRE-CHECKING the destination is the check-then-act the precondition table refuses, which would leave the same residual at a smaller window while adding a second authority beside `os.link`. It is not a regression against today: today the same call SUCCEEDS and leaves exactly this divergence silently (`base.py:454-459`), and the only thing lost is an `aliases` entry naming a stem the note still occupies as its own filename. Task 10 asserts the residual directly — the raised leaf, the unchanged filename SET, the destination note byte-identical, the committed `name:`, the absent alias, the un-re-stamped entity — plus the re-run's no-op and the direct-door recovery |
| The rename door fails between the move and the alias write | low | low — the note is where it should be and correctly stamped; one reachability route is lost | REVISED after the third spec-review round (2026-09-25): the earlier mitigation read "the door is idempotent, so a re-run completes it", which the prescribed door cannot do — `old_stem` is read off the source, provenance has already moved to the destination, so the re-run is a safe NO-OP that appends nothing. What actually holds: the entity is re-stamped before the alias write (so no later `save` recreates the old stem — no fork), the exception is loud, the re-run is safe, and the missing alias is repaired by one caller-side field edit (`repo.update_fields(entity, {"aliases": […, <old stem>]})` or by hand), which `## Edge Cases` states and Task 10 pins as the `aliases`-unchanged property. `move_note` is link-then-unlink, so a mid-flight kernel failure leaves a duplicate rather than a hole |
| The idempotent re-run silently performs a two-step move, because the branch discriminant is a raw string compare while the stamp comes back from `move_note` RESOLVED | medium — it is the default on macOS, the platform the floor runs on | medium — an interrupted re-run leaves a `.rename-tmp.md` where the document says nothing moved, and a battery pinning "no move" is RED against correct code | The branch key is file identity, not spelling: `(destination.parent.resolve(), destination.name) == (source.parent.resolve(), source.name)` (Design §2, Task 6). Task 10 asserts it on a vault path the test itself spelled divergently from its resolved form, with a non-vacuity assertion that the two spellings really do differ, so the arm cannot pass by the platform's good luck |
| The case-only two-step leaves a `.rename-tmp.md` file behind | low | low | REVISED after the threat model's M3 (2026-09-25): the earlier mitigation read "the staging name is outside `*.md`, so no reader picks it up" — which is the same fact that would make the failure SILENT, offered as the reason it is safe. The staging name now keeps the `.md` suffix, so the leftover is a note Obsidian, all three `file_pattern` globs and `lint_vault` all see, and the new detector reports it as a divergence. The second `move_note` still raises loudly if the staging name is occupied, and the state is recovered by a HAND rename — not by a door re-run, for the reason Design §2's re-run table gives (the same entity's stamp names the pre-move source, which is gone) |
| A caller sends the rename door a destination outside the vault — `..`, an absolute path, or an in-vault symlink pointing out | low | high — a note written outside the vault, under a clean name nothing flags | M1: the door refuses on the RESOLVED destination before any `move_note` call, the same test the seam applies to the source. Pinned both ways in Task 10 — all three escape spellings refused, an ordinary destination and an in-vault subdirectory still moving — so the clause cannot degenerate into refusing everything |
| `update_fields` calls the two-lock door, and a builder places the call inside the `note_lock` block it already holds | low, but it is the natural reading of the surrounding code | high — a deadlock between two concurrent movers, in a library three consumers run | Design §2 states the placement (outside the block, after the write commits, before the reload) and ordering decision 5 states WHY reentrancy does not license the other placement; `door_calls_inside_note_lock` asserts it structurally as an EMPTY set over `PACKAGE_ROOT`, pinned both ways in Task 10 so it cannot pass by forbidding the single-path doors `write_markdown_file` legitimately calls inside its own lock |
| A builder lets `rename_note`'s no-provenance raise leak out of `update_fields` after the content write has committed, leaving a note renamed in its field, un-aliased, unmoved, and an exception on a successful write | low, but it is what the naive ordering produces | medium — a divergence manufactured by the method that exists to end them, on the one population the method's own fallback serves | The refusal is moved BEFORE the write: inside the lock, after the name-change decision, before anything is gated or written (Design §2, "The no-provenance name change refuses BEFORE the write"; Task 6). Task 10 asserts the note is BYTE-IDENTICAL after the refusal, which is the assertion that distinguishes refusing early from refusing late, and asserts the non-rename and unchanged-name updates still succeed so the clause is not "refuse every unstamped update". The two alternatives are rejected in writing: skipping the move keeps today's leave-behind, and re-stamping from `get_file_path` would hand the door whichever member of a collision won the vault walk |
| `update_fields` is no longer ATOMIC across write-then-move, because the move cannot be held inside the lock | certain (it is the design) | low — every residual is loud, detector-visible and recoverable | The interleavings are walked in `## Edge Cases`: a concurrent source write loses to last-writer-wins and moves with the file, a concurrent move or delete gives `FileNotFoundError` from the door's own `source.exists()`, a concurrent create at the destination gives `NoteAlreadyExists` by syscall — the syscall arm holding because M6 has already refused the call where the write guard is not enforcing, the row below. None lands one person's bytes in another's note, each residual is — for a PERSON subject — exactly the `stem_name_divergence` the new detector reports (the one subject type this item leaves outside that arm is a COMPANY, named in Design §2's complement rule rather than implied here), and each is a MOVE that did not happen, which re-running THE DOOR completes — `repo.rename_note(entity, …)` and never a re-run of `update_fields`, whose trigger reads the committed name back out of the note (pinned in Task 10; the one residual a door re-run does NOT repair is the missing alias after a move that SUCCEEDED, the "fails between the move and the alias write" row). The alternative placement is a deadlock in a library three consumers run |
| A consumer (or the conductor's own repair shell) sets `OBSIDIAN_SCHEMAS_WRITE_GUARD=observe` — the estate's documented rollback lever — and door 3's occupied-destination refusal silently becomes an `os.replace` that DESTROYS the occupied note | medium — it is the runbook's own cheapest rollback (`docs/concurrent-access.md:4286`) and the measure-before-adopting mode the three consumers are invited to set (`:2556`), read per call with no restart | high — one person's bytes land in another's note and the overwritten one is UNRECOVERABLE, in the one act Rollback says `git` cannot undo; WI-004 declared it acceptable (R9) only while door 3 had a single quarantine caller, a premise this item removes | M6: the door reads `vault_io.guard_mode()` beside M1's containment block and REFUSES with `ValueError` before any `move_note` call, and `update_fields` refuses the same condition inside its lock before its content write, so nothing is half-applied. Pinned both ways in Task 10 — refused under `observe` for an occupied AND an ordinary destination, still moving (and still raising `NoteAlreadyExists` on an occupied one) under `enforce` — with the environment set and restored in a `finally`. The residual is a capability LOSS while the mode is set, which is the intended direction for a rollback lever and is stated in Prerequisites 9 |
| A consumer PATCHes a `name` key onto a Book or Meeting entity — the generic entity PATCH forwards an arbitrary body — and `update_fields` commits an ungated `name:` into the note and only then discovers the door will not move it | low today (0 measured consumer call sites on Book's and Meeting's write paths), but it is what the naive trigger produces and THIS ITEM is what makes the frame reachable at all | medium — a note gains a caller-supplied field it has no rule for, unmoved, un-aliased, with an exception after a successful write, and it is the ONE residual of this item the new detector cannot report (Task 11's arm fires only on `vf.entity_type == "person"`), so the non-atomicity row above's "every residual is exactly the `stem_name_divergence` the new detector reports" claim would be false as written | M7: the pre-write refusal's third disjunct is `"name" not in type(entity).model_fields` — keyed on the DECLARED field, read off the class, never on a type name — so the delta is refused inside the lock before anything is gated or written and the note is byte-identical. It closes a class rather than a case: Design §2's delegation rule now says a refusal handed to another wall is only as total as that wall's DECLARED SCOPE, which is what `gate_write`'s two-type coverage (`obsidian_schemas/name_gate.py:gate_write:319-344`) breaks. Pinned both ways in Task 10 — the escaping and non-escaping spellings both refused with the note byte-identical, against the same entity's non-`name` update succeeding, a person's name change still moving, and a stored-`name:`-extra book still refusing |
| A consumer PATCHes a Book's `title` (or `author`, or a Meeting's `date`/`topics`/`attendees`/`meeting_id`) — no `name` key, so the rename branch never fires — and `update_fields` COMMITS the field, moves nothing, records no alias for the stem the note is leaving behind, and raises nothing | low today (0 measured consumer call sites on Book's and Meeting's write paths, and the generic PATCH is the only route, `docs/wi-029-consumer-audit.md:84`, `:137`), but it is an ORDINARY request — `PATCH /api/entities/book/{name}` with `{"title": …}` — and THIS ITEM is what makes the frame reachable at all (Task 3's `resolved`-first reorder; Design §5's declared widening) | medium — this document's own type-general divergence predicate manufactured SILENTLY by the method that exists to end it, and it is the QUIETEST residual in the item: M7's raises, the occupied-destination one raises, and this one raises nothing and is invisible to Task 11's `vf.entity_type == "person"` arm, so the non-atomicity row's "every residual is loud, detector-visible and recoverable" would be false as written | M8: the pre-write arm's SECOND CLAUSE, `not renaming and derive is not None and derive(projected) != derive(entity)` with `derive = getattr(self, "_get_file_name", None)` — keyed on the REPOSITORY'S OWN DECLARED FILENAME RULE, never on `name` or a type name — so the delta is refused inside the lock before anything is gated or written and the note is byte-identical. It closes a class rather than a case: the generator is a guard keyed on the PERSON instance (`name`) of a predicate this document states TYPE-GENERALLY, which produced M7 and M8 from the same paragraph two rounds apart, and Design §2's third rule now states the arm's TWO obligations (refuse a rename the door cannot complete; refuse a write that moves the type's own rule with no rename to follow). It adds no capability — the rule is recomputed only to COMPARE, never to build a path — and the comparison is DELTA-RELATIVE so an already-divergent Book or Meeting note stays writable. Pinned both ways in Task 10 across four REFUSED cells spanning both types and four ACCEPTED arms. The one place in this item where the same shape is ACCEPTED rather than refused is `save` and the two `save` overrides, and it is accepted by a SIGNED decision rather than by omission: a `save` of an entity whose deriving fields the caller changed now lands in the parsed file instead of forking a second note, which is AC-1's promise and `## Verified Diagnosis` 1's point — refusing there would refuse the criterion; its own residual for a Book or Meeting subject is detector-blind, the same class as the COMPANY residual named in Design §2's loudness precision, and is the conductor direction table's business |
| The seam is shipped but a tenth write path is added later and routes around it | medium over time | high — the class reopens silently | AC-5's derived scan, pinned both ways with a planted-escape battery including the two shapes a builder optimizing for green would reach for first |
| The live baseline has drifted in the four days since it was measured | medium | medium — a repair row that cannot be executed | No criterion asserts the number 8; the build-runner re-runs §0's script at Verify-Assumptions and treats a changed TABLE as a drift report; AC-4's exit half re-runs the identical script |
| Four new check modules each add a foreign-interpreter re-exec to the AC battery | certain | low — battery wall-clock only | `ensure_project_interpreter` is a NO-OP under the floor command and under CI, so the floor is unaffected; only the conveyor's per-criterion runs pay it, and they pay it once each |
| A count pin moves and is silently bumped to green | low | medium — a wall stops meaning anything | Task 14 states the rule explicitly: a moved pin is edited to NAME its new member, with the design decision that moved it recorded in the Build Log — never bumped |

**Rollback.** The seam, the door and the detector are one commit and revert cleanly; nothing in them
migrates data or changes a stored schema. The live repair is the one act that is not revertible by
`git`, which is why it is bracketed: the entry measurement is committed BEFORE it runs, the direction
table is signed per-row, `move_note` refuses an occupied destination by syscall — which M6 makes
unconditional at this door by refusing the rename outright when the write guard is not enforcing,
since that syscall refusal is an `os.replace` under `observe` and the bracket would otherwise be
absent in exactly the configuration the rollback lever produces — and every renamed note keeps its
old stem as an alias.

## Acceptance Criteria

**FROZEN AND SIGNED — these five criteria are not edited by anyone downstream of the signature.** Dave
originated and signed the set through `/review-spec` on 2026-09-25 (`## AC Sign-off`:
`ac_hash 15189b874b27`, `intent_hash 2dd3a4440900`, five per-criterion hashes,
`signed_at 2026-09-25T11:22:44+01:00`), and `## Scope Boundary` names this section and `## Intent`
among the things the builder must not touch. Every other section of this document is written TO these
criteria: nothing below is refined, hardened, split or re-worded by the spec-writer or by the builder.
If one of them proves WRONG, escalate to Dave and let him re-originate rather than editing it — an
in-place change to a signed criterion invalidates the signature (D4b) and costs a re-sign nobody
asked for. *(This paragraph replaces the section's pre-sign-off sentence — "Draft — … nothing here is
frozen yet" — which was still standing against the fence that froze it and invited exactly the edit
the Scope Boundary forbids. Prose only: no `criteria` fence's bytes are touched, so every
`ac_hash_AC-N` the sign-off fence carries remains byte-intact.)*

```criteria
id: AC-1
desc: A write of an entity the library parsed lands in the note it was parsed FROM — through EVERY mutating path in the package and not `save` alone, even when two notes share one stored name, and even on a repository that never loaded — so no library write can turn one person note into two or land one person's bytes in another person's note. Over a materialized TEMP copy of the frozen fixture corpus (never `tests/fixtures/vault/` itself — `CORPUS_DIGEST`), TWO sets are DERIVED rather than hand-listed. The SUBJECT set is the UNION of TWO declared predicates over the manifest, neither of them a `shape_classes` label: (i) DIVERGENT — every `NoteSpec` with `declared_type="person"` and declared `fields` whose filename stem (less the `@`) differs RAW from its declared `name:`, which over today's corpus is exactly four notes (premise 13); and (ii) NAME-SHARING — every person `NoteSpec` whose declared `name:` equals another person `NoteSpec`'s, which is what brings in the collision third `@Quillam Ostrivane Lumbrek.md` (a note whose stem and name AGREE, so predicate (i) cannot reach it) — PLUS the planted members the corpus cannot supply. Both predicates are the PERSON ROW of the type-general definition stated in `## Exploration Notes` ("Divergence is not a Person-only predicate"): DIVERGENT is "the filename this type's own write rule recomputes from the entity's current fields differs from the file it was parsed from", and a COLLIDING GROUP is "every note of a type whose DERIVED filename agrees with another's while they live at different files" — for Person those read as raw stem ≠ raw `name:` and as name-sharing, and for Book and Meeting they read against `_get_file_name` (`book.py:346-355`, `meeting.py:216-231`). Each subject is bound to a FILE and parsed from that path directly, never fetched by name. The PATH set is the package's own mutating write paths, taken from the same derivation AC-5 scans rather than hand-listed, restricted per subject to the paths its entity type admits: for a Person subject, `save`, `update_fields` and the five mutating body-writers (`append_to_timeline`, `append_to_body_section`, `add_to_discuss_item`, `update_to_discuss_item`, `remove_to_discuss_item`); for a Book and a Meeting subject, that type's `save` override. THE BOOK AND MEETING SUBJECTS ARE PLANTED AS COLLIDING GROUPS AND EVERY SUCH GROUP CONTAINS A DIVERGENT MEMBER: for each of the two types, a group of TWO notes in the temp vault whose derived filenames are identical — one living AT that derived filename (non-divergent) and one living elsewhere (divergent) — which is the `Quillam` shape read off that type's own rule and is the only construction under which a provenance-bound write and today's `_get_file_name`-derived write land in different files. A Book or Meeting subject whose deriving fields still agree with its file is NOT admissible as the type's only subject: for such a subject the two mechanisms compute the same path, so its cells cannot discriminate a correct seam from one that calls `_resolve_write_target` and discards the return (premise 15). For EVERY (subject, path) pair, apply that path's minimal mutation — which must touch NONE of the fields that subject's type derives its filename from (not `name` for Person, not `title`/`author` for Book, not `date`/`topics`/`attendees`/`meeting_id` for Meeting), so the cell measures provenance against derivation rather than mutation against derivation — and assert: (a) the SET of filenames in the vault is unchanged; (b) the changed bytes are in the file that subject was parsed from, asserted for EVERY member of a colliding group independently and for the DIVERGENT member of the planted Book and Meeting groups by name; (c) every other member of that group is byte-identical afterwards — which for the planted Book and Meeting groups is the sibling sitting at the derived filename, the note today's override would have written over. ONE cell of that matrix has a different declared outcome, reached BY RULE and never by a hand-list: for the `save` path, the sweep first applies the DOOR PREDICATE stated in `## Exploration Notes` ("Which notes ARE the class") to the subject — `gate_write(fm, declared_type=fm.get("type"), whole_record=True)` over that subject's OWN stored frontmatter, the exact call `write_markdown_file` makes on its `entity is not None` arm (`writer.py:229-233`, `:252-253`) — and where it raises, the expected outcome of that cell is a `NameGateRefusal` carrying the raised `pattern` with NO file in the vault changed. The predicate is the DOOR's and explicitly NOT `NameValidator.validate_strict(name)`, whose `allow_phone_sentinel` defaults to `False` while the door derives it from the payload (`name_gate.py:355-358`), and never the manifest's `discriminator`. Over today's corpus that is two subjects and two cells (premise 13); every other path for those same subjects asserts (a)(b)(c) normally. The corpus cannot discriminate the two spellings of that predicate, so the member that does is PLANTED and named here as a required subject — THE SENTINEL-EXEMPT SUBJECT: a divergent phone-only stub, file `@447700900123.md` carrying `name: "+447700900123"` and a non-empty `phones:` list, whose branch is the one `sentinel_exempt` record in the Tier-1 table (`pure_digit`, `name_validation.py:283-294`, `:155-156`) and which the door therefore WRITES. Its `save` cell asserts the ordinary (a)(b)(c), and asserting that it is NOT refused is the arm that fails an implementation built on the bare validator. Then the arms that belong to ONE path, because the behaviour on ABSENT provenance differs by path and must — (d) for the PLANTED divergent note whose canonical `@{name}.md` is FREE, `save` creates no `@{name}.md`; (e) for the PLANTED genuinely-new entity, `save` DOES create `@{name}.md` — the discriminator that stops "never write anywhere" from passing; (f) NARROWED ARM — for the PLANTED entity round-tripped through `model_dump()`/`model_validate()`, provenance is gone by design, so today's behaviour holds (`@{name}.md` is `save`'s target) AND the declared marker is asserted: a WARNING is emitted naming the collision when that target already exists; (g) UNLOADED — on a repository constructed `auto_load=False` and never `load()`ed, a subject parsed directly still writes to its own file through EVERY path in its path set with no vault walk triggered, AND an entity carrying no provenance still raises `ValueError` from `update_fields` and from each body-writer on that same repository rather than creating a note; (h) NO LEAK — no note written anywhere in the sweep gains a frontmatter key holding a path.
why: This is the half of the Intent that makes recurrence impossible rather than merely visible, and it is the defect WI-021 named and parked (`docs/write-door-bypasses.md:486`). The PATH set is DERIVED for the same reason the subject set is, and round 2 is why: this criterion previously claimed "no library write" while its oracle exercised `save()` alone, and eight further paths in the package resolved their target from a name (premise 12) — so a build could go green on every arm and ship a criterion whose headline was false, the item buildable two ways (WI-144) in the one criterion that carries the Intent. Subjects are derived from PREDICATES rather than from `shape_classes` because the label is not the class: the shipped detector runs over a live vault where nothing is labelled, and a corpus keyed on labels would certify an implementation that cannot exist in production. Round 3 is why there are TWO predicates and why this rationale no longer claims one does the other's work — the earlier wording said the stem≠name predicate "picks up all three `Quillam` notes, including the collision third", and that was false in both directions (premise 13): the collision third's stem and name AGREE, so the divergence predicate structurally cannot reach it, while the predicate DOES reach two notes this criterion never mentioned, the `arrow_connective` and `path_hostile` gate specimens. The collision third was already load-bearing for (b) and (c), which assert over "every member of a name-sharing group" — a second derivation the criterion used and never defined — so it is defined, and the subject set is the union. Each subject is bound to a FILE because `repo.get(name)` can only ever return one entity per name, which is the ambiguity this criterion exists to refuse. The gate-refused `save` cell is stated as a RULE rather than as an exclusion of two named notes, because an exclusion list is a hand-sample of the class (WI-185) while the rule is total: a name the DOOR refuses is a name that can NEVER fork — `save` raises above the lock (`writer.py:229-233`, `:252-253`) before a byte is written — so pinning the refusal asserts a true and permanent property and a future corpus member trips into the right expectation by itself. Round 4 is why the rule asks the DOOR and not `validate_strict`, and why one planted subject exists solely to hold it to that: the property is true, the spelling was not. `Tier1Branch` carries `sentinel_exempt` and `pure_digit` sets it (`name_validation.py:155-156`, `:283-294`); `gate_write` DERIVES `allow_phone_sentinel` from the note's own payload (`name_gate.py:355-358`) while `validate_strict` defaults it `False` "to keep producers honest" (`:594`, `:599-601`) — so the bare validator predicts a refusal the package does not perform, for a branch the census measures at 2 live person notes (`docs/vault-shape-census.md:148-157`). Every divergent note the FROZEN corpus supplies answers identically under both spellings, which is precisely the WI-286 case for planting the discriminating member rather than trusting the corpus: the SENTINEL-EXEMPT SUBJECT is the only cell in the matrix where a right and a wrong-but-self-consistent implementation differ, and without it a build keyed on `validate_strict` goes green on every arm and ships a detector, an AC-4 consistency rule and a conductor table that all forbid the one repair direction that works for that shape. That the OTHER eight paths still assert normally for those subjects is not an oversight but the code's own design: `update_fields` gates the delta with `whole_record=False` and says verbatim that a note whose stored name is already dirty stays writable (`base.py:466-485`), and the five body-writers call `vault_io.write_note` with no gate at all — so the refusal is two CELLS out of the fourteen those two subjects occupy (seven Person paths each), and excluding them as SUBJECTS would have silently dropped the other twelve. (b)+(c) asserted per group member PER PATH is what a name-keyed target cannot satisfy: the live corpus contains 2-note collisions (`docs/vault-shape-census.md:222`), and for those a name lookup answers with glob order — which on `append_to_timeline` means one person's timeline entry landing in another person's note, the exact harm premise 9 describes and "Examples of done" promises to end. The oracle is per-member because today's `save` produces TWO corruptions from one defect: a fork where the canonical filename is free, a silent overwrite of a sibling where it is taken (`overwrite=True` is the default). (d), (e), (f) and (g) are PLANTED or configured because the frozen corpus cannot discriminate a correct implementation from a stubbed or inert one — membership is not correctness (WI-286). (g)'s first half is the arm a load-derived battery structurally cannot see and the reason the binding is provenance rather than an index; its second half is the arm that stops the seam being built as a uniform fallback, since returning a name-derived path where those paths refuse today would convert a loud miss into a brand-new fork source. (f) is the WI-286 narrowing arm stated honestly: a round-tripped entity is indistinguishable from a new one, so the criterion does not promise what it cannot deliver — it promises the loss is LOUD, and precondition 2 question (4) measures how large that population is in real consumers. (h) makes premise 11's unwritability an assertion rather than an assumption, since `extra="allow"` would otherwise serialize a mis-declared stamp into every note the library writes. Round 5 — the AC red-team's — is why the Book and Meeting subjects are planted as DIVERGENT members of colliding groups rather than as bare subjects, and it is the same WI-286 defect this criterion already fixed twice in the Person half, found in the half that inherited none of the work: their path set said "that type's `save`" and their subjects were unconstrained, so a subject whose `title`/`author` (or `date`/`topics`) still agreed with its file made (b) hold trivially — `_get_file_name(entity)` recomputes the file it was parsed from — and made (c) vacuous, because no group was defined for those types at all. A `save` override that calls `_resolve_write_target` and discards the return passes every such cell while writing exactly where it writes today, which is the one-line incentive to leave open the hole round 2 widened the seam to close and `## Approach` calls "one line each". The fix is a derivation and not a fixture request: divergence is the type's OWN filename rule recomputed against the file it was parsed from (premise 15 reads both rules off the code), the Person predicate is its instance, and a colliding group is self-seeding — at most one member can live at the shared derived filename, so a planted pair always contains a divergent member and supplies both derivations at once. The mutation constraint is stated for the same reason the subject is: a mutation that touched `title` would move the derived filename WITH the write and the cell would pass under either mechanism. What the planted groups then assert is the Book-side spelling of premise 9's harm — today's override writes the divergent member's bytes over its sibling at the derived filename, a note the caller never named — and the census's "a book-titled file holding a person note" is a live specimen of a file whose derived name has drifted from where it lives.
check: test_no_library_write_can_fork_a_person_note
kind: test
```

```criteria
id: AC-2
desc: Exactly one door in the package moves a note, it moves the note it was ASKED about, a moved note stays reachable, and the next write follows it. (a) THE DOOR — a rename entry point on the repository resolves the file it is about to move through the SAME provenance function every write path uses, never from the entity's name, routes through `vault_io.move_note`, appends the old stem to `aliases`, and leaves `get`, `get_by_email` and the alias route resolving the person under BOTH the old and the new name afterwards. (b) REFUSAL — asked to rename onto an occupied filename it raises `NoteAlreadyExists` (the leaf, not the root) and BOTH files are byte-identical afterwards. (c) SINGLE HOME — `update_fields` with a name change calls that door rather than leaving the file behind, so the library no longer manufactures divergence (`base.py:454-459` today), and a derived scan finds no other site under `obsidian_schemas/**` naming a rename capability. (d) SYMLINK — a symlinked source is refused, unmoved, per door 3's own contract. (e) THE WRITE FOLLOWS THE FILE — after a successful rename, a `save()` on the SAME in-memory entity lands in the new file and the old stem is NOT recreated; after a REFUSED rename (b) or a refused symlink (d), that same `save()` still lands in the unmoved original. (f) THE RIGHT NOTE, UNDER COLLISION — for two corpus notes sharing one stored `name:`, renaming the entity parsed from note A moves A: note B is byte-identical afterwards, its `aliases` did not gain A's old stem, and it is still at its original path. (g) THE RELOAD RE-STAMPS — the entity `update_fields` returns carries provenance naming the file that was actually written, so a `save()` on the RETURNED entity lands there and not at `@{name}.md`. (h) CASE-ONLY — asked to rename a note to a stem that differs from its own only by letter case, on a case-insensitive filesystem, the door MOVES it rather than refusing: afterwards the directory holds exactly one entry for that note, spelled in the NEW case, with the old spelling in `aliases`; and (b)'s `NoteAlreadyExists` applies only to a destination that is a DIFFERENT file (`os.path.samefile` false), never to the note's own case-variant. The live baseline (`docs/stem-divergence-live-baseline.md` §2, row 3) has exactly one such member, and a door that compares destination STRINGS refuses the one repair that works for it.
why: The mint named `move_note` and it is the right machinery, but it has exactly ONE caller in the tree today (`scripts/lint_vault.py:1343`, quarantine) — essentially unexercised for this use. (a) and (f) are round 2's finding turned into an oracle, and they are the sharpest arm in the set: `update_fields` picks its file from `_file_map[name.lower().strip()]` (`base.py:438`), one path per name in glob order, so a door driven from that lookup moves the WRONG member of a live collision pair (`docs/vault-shape-census.md:266-267`) — appending A's old stem to B's `aliases` and leaving A untouched. That is the repair machinery corrupting a note it was never asked about, with the correct path sitting unread on the entity one frame away, so the door resolving through the seam is asserted rather than assumed. (a) is also what the Intent means by "nothing that referenced the old file goes dark", stated as a resolution property rather than as the presence of an `aliases` key. (c) is the finding that decides whether the Intent is achievable at all: one shipped library behaviour deliberately creates the divergence this item promises to end, so either it changes or the promise is false. (b) protects the merge case the direction table will contain. (e) is the seam's interaction with the door and it is not decoration: under provenance binding, an entity whose stamp still names the old path would, on its next save, RECREATE the note the rename just removed — a fork manufactured by the repair itself. Both arms are asserted because the stamp must be updated exactly when the file moved and not when the move was refused, and a stubbed door that re-stamps unconditionally passes the success arm alone. (g) is free once the parse stamps — `update_fields` reloads through `_load_file` (`base.py:493`) — and is pinned anyway, because a later refactor returning an unstamped entity would regress (e) silently. (g) is also the oracle for a real SEQUENCING constraint inside (c), named in `## Approach` (2) so the build does not discover it as a failing test: calling the door from `update_fields` is safe with respect to LOCKING (door 3 sorts both resolved paths into a global total order and the locks are reentrant, `vault_io.py:744-750`), but the frame holds a `stamp` from `read_note` (`base.py:449`) that it commits against the OLD path (`:490`) and then reloads from (`:493-495`, `ValueError` on a `None` reload), while `move_note` calls `forget_snapshot(source)` (`vault_io.py:780`) — so the order is write, then move, then rebind `file_path` to the door's return value before the reload.
check: test_a_person_note_is_renamed_only_through_the_one_door_and_stays_reachable
kind: test
```

```criteria
id: AC-3
desc: `lint_vault` REPORTS filename/name divergence and never repairs it. The comparison is RAW on both sides — the filename stem less the leading `@` against the stored `name:` exactly as written, with no `clean_person_name` on either half. (a) FIRES — over the frozen corpus the check emits one ERROR-severity `stem_name_divergence` issue for EACH of the FOUR person notes the definition selects, naming the stem and the stored name: `@Quillam Ostrivane.md`, `@Quillam Lumbrek.md`, `@Perrowin Tessamund Drostane.md` and `@Yolvenna Brindlecote Skarnell.md` (premise 13). The expected set is DERIVED from the manifest by the same predicate AC-1 uses, never from `shape_classes`, so it is four because the definition says four and not because four notes are listed here. (b) SILENT ELSEWHERE — it emits nothing for the other corpus notes, including `@Quillam Ostrivane Lumbrek.md` (stem and name agree), the diacritic, hyphenated, postal-address and pure-digit person notes, every non-`@`-prefixed note, and — the arm that pins the raw comparison — `@Dave  Marrowyn Fennwick.md`, whose stem and stored name BOTH carry the double space and which a `clean_person_name` comparison would wrongly report (`tests/fixture_vault.py:246-254` declares `cleaned="Dave Marrowyn Fennwick"`). (c) NOT-RENAMEABLE, REPORTED AND MARKED — for a diverged note the DOOR PREDICATE refuses (defined in `## Exploration Notes`, "Which notes ARE the class": what `gate_write` does with that note's OWN stored frontmatter, NOT `NameValidator.validate_strict(name)`), the check still fires, and the issue carries a declared marker naming the raised `pattern`: over the corpus that is two of the four (`pattern="calendar_prefix"` for the arrow specimen, `pattern="path_hostile_char"` for the slash one). The marker is asserted present on exactly those two and absent on the other two — AND absent on a PLANTED divergent phone-only stub (`@447700900123.md`, `name: "+447700900123"`, non-empty `phones:`), which the door writes because `pure_digit` is the one `sentinel_exempt` branch, so it is reported as an ordinary unmarked divergence whose correct repair IS a rename. That planted member is the arm that fails a detector built on the bare validator; the corpus alone cannot tell the two apart. The marked issue's message states the POLICY and not a physical claim — this divergence is not repaired by renaming the file to the stored name, repair the field — since only `path_hostile` makes the rename literally impossible. (d) NEVER REPAIRS — the issue carries `auto_fixable=False`, so it never enters `apply_fixes`; WI-026's four-bucket accounting still totals exactly the auto-fixable issue count with the new check enabled, and the new issue is counted by the summary line's non-fixable figure. (e) UNREADABLE NOTES — a note `read_vault` cannot decode is not reported as divergent (it has no stored name to disagree with), preserving WI-026's `read_error` triage order.
why: This is the half that goes red "the moment the class recurs" in the live vault, on the tool Dave already runs — the hermetic floor structurally cannot watch the vault (WI-031 closed the last route deliberately). Both directions are asserted because a detector pinned only on its true positives is the WI-235 shape, and this corpus makes the negative cheap: it deliberately holds every other corruption class, so (b) proves the check discriminates rather than merely fires. (a)'s count is FOUR and derived, which is round 3's finding and the sharpest thing in this criterion: it previously pinned "the two notes the manifest declares in that class", and a detector written to the DEFINITION emits four (premise 13) — so the only implementation that passed both (a) and (b) as written was one keyed on `shape_classes`, i.e. one where the manifest LABEL is the defect class, which is exactly what AC-1's derivation forbids and which cannot exist over a live vault where nothing is labelled. Two criteria disagreeing about the extension of one class over one frozen corpus, resolving toward the wrong implementation, is WI-144 in the half of the Intent Dave actually runs; both now read the one definition stated in `## Exploration Notes`. The RAW comparison is written into the desc rather than left to the spec because `clean_person_name` is one import away and a builder may reasonably reach for it, and the corpus contains the note that makes the two choices differ — (b)'s whitespace-damaged member, which a cleaned comparison reports and a raw one does not. (c) exists because the corpus proved the third repair direction is real: a note can be divergent AND not repairable by moving the file, because the door refuses to write its stored name at all — permanently — so a stem minted from that name is one no write path in the package could ever reproduce (and for `path_hostile` specifically, `@{name}.md` is a path into another directory, which is why the message states a policy rather than an impossibility). That is the row a human most needs to see, so it is reported loudly and marked, never suppressed — and the marker is what lets AC-4's shape check refuse a direction table that answers "rename" for such a note. Round 4 is why the marker fires on the DOOR predicate and why a planted phone stub is in (c)'s negative half: `pure_digit` is `sentinel_exempt` (`name_validation.py:155-156`, `:283-294`) and `gate_write` derives `allow_phone_sentinel` from the payload (`name_gate.py:355-358`), so a detector asking `validate_strict` would mark a phone-only stub not-renameable while the door writes it happily and `@+447700900123.md` is an ordinary filename — a FALSE message on Dave's own report, over a branch the census measures at 2 live person notes (`docs/vault-shape-census.md:148-157`, `:260-261`), telling him the one correct repair is impossible. The frozen corpus cannot catch that: its phone specimen declares no `phones` precisely so the branch fires (`tests/fixture_vault.py:283-293`) and it is not divergent anyway, so the discriminating member is planted (WI-286). (d) is the D-rejection made enforceable: relocation is the highest-blast-radius act in the tool and per-note direction is a judgement no auto-fix can make.
check: test_lint_vault_reports_stem_name_divergence_and_never_repairs_it
kind: test
```

```criteria
id: AC-4
desc: The live repair is BRACKETED and the bracket is in the tree. `docs/stem-divergence-live-baseline.md` is in git HEAD before the criteria are frozen, and carries, in a machine-readable shape the check asserts: an ENTRY section with the divergence count and `len(PersonRepository(<vault>).conflicts)` from one dated run, a per-note direction table whose every row declares THREE things — which side is correct, whether the destination filename is occupied, and whether the note is GATE-REFUSED under the DOOR PREDICATE defined in `## Exploration Notes` (what `gate_write` does with that note's OWN stored frontmatter, never a bare `NameValidator.validate_strict(name)`), with its raised `pattern` where it fires — the incoming-reference count per old stem, and the four booked hand repairs. The check reads the committed artifact and asserts its SHAPE and internal consistency (every row carries all three columns; every direction row resolves to rename / merge / field-repair; NO row resolves to `rename` while declaring a gate-refused stored name, and none resolves to `rename` onto a destination occupied by a DIFFERENT note — a destination that is the SAME file under a case-insensitive filesystem (the artifact's `same-file` value; a case-only divergence) is not occupied for this rule and resolves to `rename` as a case change; the entry counts are present and numeric; no absolute path and no note filename leaks the privacy wall) — the rule bites only on a row the DOOR refuses, so a row whose stored name is a phone sentinel the door writes stays free to resolve to `rename` — it executes nothing against any vault. The EXIT half is a declared SHIP CONDITION on this item and is stated as such in the document: at `building → done` the conductor re-runs the same measurement, appends the attestation to the same artifact, and the item is not done until divergence and conflicts both read zero.
why: WI-026's scar, applied before it is paid again: a 100% hermetic acceptance for a live-corpus repair proves nothing about the corpus it repaired. The precedent is `docs/lint-vault-live-baseline.md`. The split is deliberate and is stated rather than papered over — a `kind: precondition` fence is HEAD-probed BEFORE the build spawn so it cannot carry a post-build act, and a `kind: command` AC would point an automated battery at Dave's live vault on a path he did not authorize per run. So the entry half is fence-enforced and AC-read-back, and the exit half's wall is the conductor's ship door. The third column and its consistency rule are round 3's finding carried into the artifact the conductor commissions: the frozen corpus proved that a diverged note's stored name can itself be one the door refuses, which makes "rename to match the name" the wrong direction — so a two-column table would come back with rows the repair run cannot perform, and re-commissioning it is a second conductor act outside the cage. Asserting the rule here is what stops the table from being internally contradictory before anyone tries to execute it. Round 4 is why that column cites the DOOR predicate rather than `validate_strict`, and the hazard is the same ordering one step in: `pure_digit` is the one `sentinel_exempt` branch (`name_validation.py:155-156`, `:283-294`) and the census measures it at 2 live person notes (`docs/vault-shape-census.md:148-157`), so if either is also among the eight divergent — which is exactly what this artifact exists to answer and what no caged reader can settle — a table built on the bare validator comes back declaring a refusal for a row whose only correct direction is `rename`, and this criterion's own shape check then REFUSES it. An internally contradictory table, commissioned once, outside the cage, with the contradiction manufactured by the rule that was supposed to prevent it. One predicate, defined once and cited by all four sites, is what makes that unrepresentable. This criterion claims only what its check can reach.
check: test_the_stem_divergence_live_baseline_is_committed_and_shaped
kind: test
```

```criteria
id: AC-5
desc: The provenance function is the ONLY way a write target is chosen in this package — a tenth write path cannot route around it. A derived scan over `obsidian_schemas/**` (the WI-031 `tests/derivations.py` shape, not a grep in a docstring) enumerates every mutation site — every call to `write_markdown_file`, and every call to a `vault_io` door named in `tests/derivations.py`'s own `DOOR_NAMES` (`:47`: `write_note`, `create_note`, `move_note`), reusing that frozenset rather than spelling a shorter list here — and classifies each enclosing function into exactly one of two legal buckets: (a) PATH-TAKING LEAF — the target path is a parameter of that function, so its caller chose it (`writer.py`'s four sites today); or (b) SEAM-ROUTED — the VALUE `_resolve_write_target` returns REACHES that function's own write call, as DATA FLOW and never as call-presence: the name bound to the call's return must taint the PATH ARGUMENT of the write (the first positional of `write_markdown_file`, the path parameter of the door), on the seed → fixpoint → sink shape `tests/derivations.py:361-409` already implements for a different seed, reused rather than re-written. Any site in neither bucket FAILS the scan, naming the file, the function and the line. The scan is pinned BOTH ways with a planted-escape battery. REFUSED, at least four: a function that derives a path from a name and writes, in both spellings (`self.vault_path / f"@{name}.md"` and a helper returning one); a function that CALLS `_resolve_write_target` as a bare expression statement and writes to a separately-derived path; the same escape with the return bound and unused (`_ = self._resolve_write_target(entity)`, or a name the write never reads); and a function that passes the resolved value to the write as some OTHER argument while the path argument is separately derived. ACCEPTED, at least five near-misses: a path-taking leaf; a seam-routed writer; a read-only function using `get_file_path`; a function naming `_resolve_write_target` in a comment or docstring without calling it; and — the one that keeps the shipped design legal — a seam-routed writer whose documented fallback arm REBINDS THE SAME LOCAL to a name-derived path before writing, which must PASS, because that is the fallback asymmetry every one of the nine call sites depends on. The scan's enumeration is also the population AC-1 derives its PATH set from, so the two cannot drift apart.
why: A function every caller MAY use is a polite request, not a boundary (LESSONS #1). Round 1 of this item's review shipped a fold that put provenance in exactly the right place and read it at one of nine sites, and round 2 found it only by sweeping the package by hand — which is the work this criterion makes permanent and automatic. The bucket classification is what makes the scan sound rather than a grep: `writer.py`'s leaves legitimately write to a path they were handed, and a rule that simply demanded `_resolve_write_target` everywhere would be either false there or weakened until it caught nothing. The planted-escape battery is WI-235's shape and WI-031's own precedent (`VaultArgScan` + `REPOSITORY_CALLEE_SUFFIX`): a containment wall that has never been shown to REFUSE anything is an assertion about nothing, and the near-misses are what stop the refusal being a substring match. Sharing one derivation with AC-1 is deliberate — AC-1 proves the nine paths behave, AC-5 proves there are no others, and a tenth path added later joins both batteries by construction instead of quietly reopening this finding. The door vocabulary is `DOOR_NAMES` and not a two-name list because this item's OWN rename door commits through `move_note`: a wall that does not enumerate the door the item ships is a wall with the item's newest write path outside it, and `create_note` is in the same frozenset for free (its only in-package caller today is `writer.py:317`, inside a path-taking leaf, so the reuse costs nothing and closes the arm where a tenth path built on `create_note` would otherwise pass a scan whose headline says it cannot). Round 5 — the AC red-team's — is why bucket (b) is a DATA-FLOW property, and the defect it fixes is this criterion's own headline being satisfiable by a stub: as drafted, (b) asked only whether the function CALLS the seam before it writes, so `BookRepository.save` and `MeetingRepository.save` — each two lines from `_get_file_name(entity)` to the write (premise 15) — could add one line, call `_resolve_write_target`, discard the return, keep today's derivation, and pass a wall whose headline says a write target cannot be chosen any other way. That is the smaller edit for a builder optimizing for green, at exactly the two sites round 2 widened the seam to reach, so the incentive points at the hole. The fold costs a seed and not a scanner: `_taints_a_write` (`tests/derivations.py:361-409`) already seeds on a call's return, propagates to a fixpoint over assignments and sinks at a write call's arguments, and AC-1 already depends on it for a different seed — narrowed here to the write's PATH argument, so "pass the resolved value as an unrelated keyword" is refused too. The battery's fifth ACCEPTED near-miss is the load-bearing one and is the reason the rule is not over-tight: the taint set is monotone over names, so a fallback arm rebinding the same local stays green, and the wall therefore does not quietly demand the removal of the fallback asymmetry the seam is built on — a wall that forced a uniform fallback would convert `person.py:1404-1405`'s refusals into note creation, which is the defect round 3 corrected.
check: test_every_write_site_resolves_its_target_through_the_one_seam
kind: test
```

### Examples of done

**Given** one of the eight diverged notes — say a person whose file is `@Firstname.md` while the note
says `name: Firstname Lastname` — **when** HAL9000 resolves that person and saves a new phone number
onto them — **then** the phone lands in `@Firstname.md`, no second note appears, and the vault still
holds exactly one note for that person. (Today: a second note is created and the timeline stays
behind in the first.) **And** where two notes both say `name: Firstname Lastname`, a save of the one
HAL9000 actually read lands in that one — not in whichever of the pair the vault walk happened to
see last.

**Given** two people whose notes both say `name: Alex Morgan` — **when** Exocortex writes a meeting
timeline entry onto the one it actually read — **then** the entry lands on that person's note, and
the other Alex Morgan's note is untouched. (Today: `append_to_timeline` looks the file up by name,
so the entry goes to whichever of the two the vault walk saw last — and the same is true of every
"add a To Discuss item", "append to a body section" and "update these fields" call in the library.)

**Given** Dave renames someone in the vault through the library — **when** the name changes — **then**
the file moves to match the new name, the old filename is kept as an alias, and searching for either
the old or the new name still finds the one note. (Today: the file keeps its old name forever and the
next save forks it.)

**Given** the repair run has finished and a month has passed — **when** Dave runs
`scripts/lint_vault.py --vault $VAULT --report` — **then** the divergence count reads zero, and if any
new divergence has appeared the report names it as an ERROR with both halves quoted, without
offering to fix it.

## Spec-Writer Notes — 2026-09-25

A `##` section and deliberately NOT nested under `## Acceptance Criteria`: the `ac-signoff` freeze hashes
that section's whole body, nested `###` subsections included (`hash_section`,
`src/work_item_linter.py`), and this one accumulates across rounds (WI-185's rule).

**What each round changed** is listed in the corresponding `## Design` revision note and named at every
site it lands — the second note for the second spec-review fold, the THIRD note for the fold of
threat-model M5, the FOURTH for threat-model **M6** in Design §2's "The door FAILS CLOSED
when the write guard is not enforcing" bullet and the "CLASS behind M6" paragraph beside it, and the
FIFTH for threat-model **M7** in Design §2's delegation rule beneath the precondition table, and the
SIXTH for the fourth spec-review round's blocking finding in Design §2's **"The COMPLEMENT of that
rule"** block beneath the same table, and the SEVENTH for threat-model **M8** in Design §2's **"the
THIRD rule"** block, which is the last block in that section and states the pre-write arm's TWO
obligations. Nothing
below adds spec content; it records things a later reader would otherwise have to re-derive.

### This round (threat-model M8) — the SAME paragraph found twice, two rounds apart, and why the fold had to climb a rung

The two findings came out of one paragraph: Design §2's account of who may reach the rename branch. M7
(round 5) found the branch REACHABLE for a type that declares no `name`, because the trigger reads the
caller's dict against the note's frontmatter and consults the model nowhere. M8 (round 6) found the
complement — a delta carrying NO `name` key — UNGUARDED for those same two types, because the whole
rename-side predicate is `if renaming and (…)` and `Book`'s and `Meeting`'s filenames are not made of
`name` at all. M7's fold swept its own level honestly and still did not reach M8, and the reason is
worth carrying: **M7's generator was "a bound enforced by a predicate that never reads the models"; M8's
is one rung up — "a guard keyed on the PERSON instance (`name`) of a predicate this document itself
states TYPE-GENERALLY".** Every guard the item had shipped keyed on `name`, which is `Person`'s and
`Company`'s filename rule and not the package's, while the item's own divergence definition is stated
over *the filename this type's own write rule recomputes*. Sweeping the members of M7's class could not
find that, because M8 is not a member of it — it is the same class re-instantiated one level of
abstraction up.

The practical consequence, and the thing to reach for first on a bounce round of this shape: **when the
finding sits inside the previous fold's own new prose, check whether the KEY the fold chose is the
general form of the predicate or one type's instance of it.** M7 keyed on the declared FIELD
(`"name" in type(entity).model_fields`), which was the right key for the rename branch and still a
`name`-shaped key. M8 keys on the declared RULE (`getattr(self, "_get_file_name", None)`), which is what
the document's own type-general divergence predicate actually quantifies over — and once it is keyed
there, the six deriving fields are covered by construction, a fifth type is covered, and a base-class
`_get_file_name` is covered, none of them by enumeration.

Three things the fold deliberately did NOT do, recorded so a later round does not re-litigate them.
It did not teach the door or `update_fields` a second filename rule for COMPOSING a destination — the
rule is recomputed only to compare — because that is the NEW capability `## Scope Boundary` declines
against 0 measured consumer call sites. It did not compare against `file_path.name`, which would have
refused every write to an already-divergent Book or Meeting note, i.e. to the exact population the item
exists to repair. And it did not extend the same clause to `save` or the two `save` overrides: what they
leave is AC-1's SIGNED trade (in-place divergence instead of today's fork), so a refusal there would
refuse the criterion — that is declared in the sweep, in `## Scope Boundary` and in `## Risk Analysis`
rather than closed by a clause.

### The fourth spec-review round — the THIRD member of one class, and why the answer is a residual rule and not a disjunct

The finding's GENERATOR, which is the only part worth carrying forward: `update_fields`' rename branch
commits its content write inside the lock and only then discovers the door will not complete the move.
Three members so far — no provenance (spec-review round 2), a type declaring no `name` (threat model
M7), a destination already occupied (this round). The first two were closed by adding a disjunct to the
pre-write refusal, and that was right for both, because their causes are knowable in the frame from its
own arguments and environment. **The third is not, and the difference is the whole lesson:** its cause
is filesystem state at move time, the precondition table already answers that row **NO** for the right
reason, and a fourth disjunct would have been a pre-check — check-then-act, a second authority on
occupancy beside `os.link`, and the same residual at a smaller window.

So the fold is the table's COMPLEMENT rather than a fourth conjunct, and the shape is the one the
previous two folds already used one level up: a rule total over the surface, derived from the table's
own rows. Rule 1 said which rows refuse EARLY; the complement says what the method LEAVES for the rows
it answers NO, and what the caller does about it. Written once, checked row by row against the table in
a four-row table of its own, so the next reader can falsify it in the same breath — and so the FOURTH
NO row, if one is ever added to the door, is placed by the rule instead of arriving as round five's
finding.

Three things this round decided that a later reader should not have to re-derive:

- **Move-then-write is UNAVAILABLE, not merely unchosen, and the reason is in the door's own body.**
  `rename_note` appends the alias through `update_frontmatter_field(moved, …)` in the same call, so a
  move performed BEFORE `update_fields`' content write moves the file's `st_mtime_ns` and `st_size` and
  the content write's `precondition=stamp` — taken from this frame's own `read_note` — then MISMATCHES,
  turning every SUCCESSFUL rename into an `ExternalWriteConflict`
  (`obsidian_schemas/vault_io.py:write_note:685-698`). The reorder that removes a rare residual
  manufactures a certain one. AC-2's signed `why` prescribing write-then-move is the second reason and
  not the first; the code is the first.
- **The residual is not a regression against today, and that is what makes ACCEPT the right call.**
  Today the same call succeeds and silently leaves the very divergence `## Verified Diagnosis` 1 and
  AC-2(c) exist to end (`base.py:454-459` appends the old stem, the write commits, the reload returns).
  After this item the same divergence is produced in the one sub-population whose move cannot complete,
  and the caller is told. The only thing lost is an `aliases` entry naming a stem the note STILL
  OCCUPIES as its own filename — a route the file already provides. Keeping today's in-lock append to
  preserve it was considered and refused: two writers on one `aliases` list, one frame apart, for a
  decoration.
- **The recovery is the same for every NO row and is NOT a re-run of `update_fields`.** The trigger
  reads the caller's dict against the note's frontmatter, which now already carries the committed name,
  so a re-run is a safe no-op that completes nothing. `repo.rename_note(entity, f"@{new_name}.md")`
  once the cause is gone is the repair — the entity is still stamped at the unmoved file, which is
  exactly the provenance the door resolves from.

One precision folded in the same edit, because the loudness claim had to be true where it is made: for
a PERSON subject the residual IS a `stem_name_divergence` the new detector reports, while `Company` —
which declares `name`, inherits `update_fields` and the door whole, and is therefore reachable — sits
outside the detector's `vf.entity_type == "person"` guard. That is the one residual of this item the
detector cannot see (M7 removed the Book/Meeting one by refusing it outright), and it is named in
Design §2's complement rule and in `## Risk Analysis` rather than implied.

### The round before (M7) — the fold of a finding that lives INSIDE the previous fold

The fifth threat-model round's one new `kind: required` mitigation, M7, folded at every site the contract
names and at the sites its own class sweep reached:

- **Design §2, the pre-write refusal** — a third disjunct, `"name" not in type(entity).model_fields`, in
  the sequencing block, in the prose predicate and in the refusal message's "WHICH precondition failed"
  list.
- **Design §2, the precondition table** — the M1 row's answer CORRECTED. It read "already refused
  earlier, by a different wall" and delegated the whole row to `gate_write`, bounding the residue with
  "`Book` and `Meeting` cannot reach it at all — they declare no `name` field". That is a fact about
  `obsidian_schemas/models.py` the trigger never consults: the trigger reads the caller's dict against
  the note's frontmatter, a book note carries no `name:`, so `frontmatter.get("name", "")` is `""` and
  any non-empty `updates["name"]` fired the branch. The row is now SPLIT by declared field and closed on
  both sides.
- **Design §2, beneath the table — the class closure, which is the WI-226 half of this fold.** The
  generator is not "the M1 row" but *a bound on a population asserted from the models and enforced by a
  predicate that never reads them*, so the second rule is stated at source: **a refusal delegated to
  another wall is only as total as that wall's own DECLARED SCOPE, and wherever the wall is narrower the
  residue is refused HERE.** The three sites that carried the unchecked claim (the M1 row, the
  `f"@{new_name}.md"` paragraph, Task 6's restatement) now rest on the disjunct, and the next level's
  sweep is DECLARED with its four non-members and its result (no fourth member).
- **`## Edge Cases`, Prerequisites 6, Design §5** — one new entry for a `name` key on a type that
  declares none; the trust boundary's THIRD half, naming `f"@{new_name}.md"` as the one place in this
  item where an externally-supplied string composes a write target and the three bounds on it; the
  integration row's third disjunct.
- **Task 6, Task 10, `## Verification`, `## Risk Analysis`, `## Scope Boundary`, the `base.py` and
  `tests/test_provenance_write_seam.py` `writes` fences, `## Wall Membership`, `## Mitigation Folds`** —
  the clause, its both-ways battery over a planted stamped BOOK note, the failure-mode entry, a new risk
  row naming the detector-blindness the finding turned on, the not-doing entry for widening `gate_write`
  or teaching the door `_get_file_name`, the wall notes for `type(entity).model_fields`, and the M7 fold
  record.

Three deliberate NON-moves. **No signed criterion was edited** — AC-2 gains no arm; M7's battery is a
non-AC arm of AC-2's check, exactly as M6's and the idempotence arm are. **`name_gate.py` is untouched**:
widening the gate to a third type is a second behaviour with its own pinning obligation and the file is
on the unchanged list. **The door learns no second filename rule** — composing the destination with
`self._get_file_name(entity)` for Book and Meeting would be a NEW capability against 0 measured consumer
call sites, and the one live instance of the shape is already a booked hand repair. Task 6's
"do NOT add a containment conjunct for M1 here" instruction is KEPT and qualified rather than deleted:
it is right for the two types the gate validates (a `ValueError` raised earlier would degrade a
`NameGateRefusal` carrying its `pattern`) and it was the whole of the answer only because the row it
pointed at was wrong.

### Two rounds before (M6) — what moved, and the two things it deliberately did NOT move

The fourth threat-model round's one new `kind: required` mitigation, M6, is folded at every site the
contract names and at the sites its own class sweep reached:

- **Design §2** — the M6 bullet in the door's mitigation list (now four clauses, not three), the
  `mode = vault_io.guard_mode()` refusal in the door's code block, and the "CLASS behind M6" paragraph
  that sweeps the six surfaces stating the occupied-destination refusal and declares the next rung
  (the three guard-conditional refusal sites in `vault_io`, one this item's, one AC-1(f)'s, one this
  document leans on nowhere).
- **Design §2, the `update_fields` sequencing** — the pre-write refusal widened from `resolved is
  None` to the door's PRECONDITION class, with the enumerating table and the rule a seventh refusal
  arm would be placed by. This is the WI-226 half of the fold: answering M6 with a second remembered
  conjunct would have left the third as the next round's finding.
- **Design §6 and Prerequisites 9** — §6 said "no env var" flatly and was false the moment the door
  read one, so it is restated as "introduces none, READS one as a refusal precondition" with the
  setting's values, default and direction; Prerequisites 9 names the mode as a checked precondition
  rather than an assumption.
- **`## Edge Cases`** — one new entry for `observe`, and two existing entries (the live-MERGE row and
  the write-then-move race) now point at M6 instead of restating the refusal.
- **Task 6, Task 10, `## Verification`, `## Risk Analysis`, `## Scope Boundary`, the `base.py`
  `writes` fence, `## Mitigation Folds`** — the clause, its both-ways battery, the failure-mode list,
  a new risk row plus the Rollback sentence, the not-doing entry for `vault_io`'s other two
  fail-opens, the wall notes for the new `vault_io.guard_mode()` call, and the M6 fold record.

Two deliberate NON-moves, recorded so they read as decisions. **No signed criterion was edited**:
AC-2(b) is one of the six surfaces the finding names, and M6 makes it true rather than rewriting it —
its check runs under the floor command, which sets no environment, so `guard_mode()` answers its
`enforce` default and the door raises `NoteAlreadyExists` exactly as the signed text says. **No
`vault_io` fail-open was repaired**: door 2's `create_note` arm is AC-1(f)'s and moves in neither
direction, so it stays WI-004's R9 — the threat model's own scope bound, and `## Scope Boundary` now
names it. The three non-blocking notes of round 4 needed no work beyond that: the no-op branch's
cosmetic log line and the `update_fields` message's pre-existing name disclosure are both recorded by
the modeler as not-required, and the `os.environ`-versus-`guard_mode()` spelling warning is folded
into both the Design bullet and Task 6's clause.

### The round after the third spec review — the findings were already folded; what I re-derived, and the one rung I added

This pass opened on a document whose bytes already carried the third spec-review round's fix, so it
produced no repair. What it produced instead is a READ-BACK and one rung, and both are recorded here so
the next reviewer does not have to guess which is which.

- **Re-derived rather than inherited, because a fold can be right in prose and wrong in code.**
  `vault_io.move_note` returns `_move_locked`'s `target`, which is `_resolved(dest)` — a bare non-strict
  `Path(dest).resolve()` (`obsidian_schemas/vault_io.py:_resolved:234-243`,
  `obsidian_schemas/vault_io.py:move_note:741-742`, `obsidian_schemas/vault_io.py:_move_locked:783`), so
  the stamp a rename writes really is resolved; `obsidian_schemas/repositories/base.py:_resolve_vault_path:104-114`
  really is `Path(str(candidate).strip())` and resolves nothing; `tests/support.py:temp_dir:31-37` really
  hands back an unresolved `mkdtemp` path; and `tests/support.py:Patcher.setitem:59-65` really pops a key
  it found unset, which is the restore Task 10's M6 arm needs. The branch key, the half-failure residual
  and the one-field recovery are correct against those.
- **The rung.** The file-identity key answers WHICH SPELLING takes which branch. It says nothing about
  what ELSE makes `source.samefile(destination)` true, and that is the same generator one level down —
  exactly the shape §3a's ladder rule and the re-run table were each written to stop. Two distinct
  in-vault names for one inode is a closed set (a case variant, or a link), so Design §2 now enumerates
  it with each outcome read off `move_note`'s body: the case variant is Task 10's asserted arm; a hard
  link makes the second move raise `NoteAlreadyExists` and leaves precisely the visible staging note M3
  exists to guarantee; a symlink at the destination naming the source runs both moves and lands the note
  back where it started, the door returning that path and appending nothing. **No work is ordered for
  any of them** — each is either already asserted, a loud refusal with a visible residual, or a no-op
  that returns the truth — and that is a decision, not an omission.
- **One Task 10 precondition, the WI-149 shape.** The M1 arm's ACCEPTED cell renames into an in-vault
  SUBDIRECTORY; `os.link` against a missing parent raises into a `WriteFailedError`
  (`obsidian_schemas/vault_io.py:_move_locked:772-773`), so the task now says the test creates that
  directory. Without the clause the cell is red against a correct door for a reason that is not M1's.

### The duplicated `## Adversarial Review — 2026-09-25` heading — a conductor question, recorded and NOT answered here

The injection-hunter's 2026-09-25 REVISE is a MACHINERY finding about this document's own structure
rather than a defect in the spec, so it is not a spec-writer fix and this note does not pretend to close
it. What I can state are facts a reader can check against the bytes, plus the one thing that is mine to
promise:

1. **Two sections in this document carry the heading `## Adversarial Review — 2026-09-25`**, each holding
   a `gate: injection-hunter` fence — the earlier one (positioned between the first Spec Review round and
   the second Threat Model round) `verdict: PROMOTE`, the later one (at the document's end)
   `verdict: REVISE`. The duplication is itself worth the conductor's attention independently of
   provenance: a heading-keyed structural reader has two candidate sections for one gate, and which one
   it resolves is not stated anywhere.
2. **On a latest-round reading the injection-hunter's standing verdict is REVISE**, because the REVISE
   section is later in document order. The item is not at a `specced → ready` attempt in any case: both
   spec-review rounds resolve REVISE and no `gate: spec-reviewer` PROMOTE exists anywhere in this
   document, so D5's first key is absent and the second key is not currently load-bearing for any
   transition.
3. **I did not author, move, edit or delete either section's bytes in this round, and no edit in this
   round touches any `verdict`, `mitigation` or `criteria` fence.** Every change I made is listed in
   `## Design`'s revision note and sits in a spec-writer-owned section. That is checkable by diff, and it
   is the only assurance about those bytes I am in a position to give.
4. **Whether the earlier section is a genuine, provenance-tracked prior injection-hunter round is not
   answerable from inside this document, and I could not answer it from outside it either** — this spawn
   has no shell, so `git log`/`git blame` over the section's lines was not available to me. I am
   explicitly NOT vouching for it: a producer asserting that a reviewing gate's fence is authentic would
   be the same confused-deputy shape the finding is about, one role over. The open action is the
   conductor's — confirm the earlier round's origin (an ad-hoc Dave-triggered run is the innocent
   explanation the finding itself offers) and make it say so on its face, or strike it so the next
   injection-hunter round is not asked to trust an unattributed PROMOTE under its own heading.

### The still-open non-blocking items, so the next round does not re-find them

Every blocking finding and every non-blocking note from the second and THIRD spec-review rounds is
folded; there is no deferred list from either. The third round's two blocking findings and all six of
its non-blocking notes land where the fourth `## Design` revision note names them — including the one
the reviewer explicitly declined to block on and left to the writer's discretion (the `!=`'s operand
normalization), which is closed rather than carried, because it is the FIFTH member of a class §3a
already owns and carrying it would have made it the next round's finding by construction. Its
carried-forward notes are re-dispositioned unchanged: the duplicated `## Adversarial Review` heading
is the conductor's (above, and still not answered here), and architect round 6's out-of-scope items
stand as `## Scope Boundary` names them. The THIRD threat-model round's one new required
mitigation, M5, was folded two rounds ago (Design §4a, Task 13, `## Verification`, the `writes`
fence, a `## Mitigation Folds` record), and its five non-blocking notes needed no work: four record that
material this document already carries is correct, and the fifth was the stale "five planted members"
count in a `writes` fence — corrected then, re-stated as the LIST rather than as a number, and the list
is what grew when plant (vii) landed. **The M1–M6 `## Mitigation Folds` records were NOT edited in the
M7 round and none needed to be:** the fifth threat-model round re-emitted all six `desc` values
byte-identically, and M7's disjunct sits in `update_fields`' refusal one frame over — it touches no
sentence M1–M6's records quote. That was CHECKED after the M7 edits rather than assumed, and the check's
scope is stated so a later reader does not have to redo it: all six `design:` sentences still resolve to
their unwrapped Design lines verbatim, and the four Task-6 `work:` values (M1, M3, M4, M6) still resolve
to their clauses verbatim — M7's clause was inserted after M6's and edited neither. Two pre-existing,
pre-M7 deviations are carried unchanged because this round did not touch their tasks: M2's `work:` (Task
2) compresses the arm's closing three sentences into one parenthetical, and M5's `work:` (Task 13)
stitches five non-contiguous stretches with semicolons and rewords the reader-battery tail; M6's drops
the `**` emphasis markers around its final sentence. All three date from the rounds that authored them.
Only the section's preamble and the new M7 record moved this round. Three dispositions are deliberate
NON-actions and are recorded so
they read as decisions rather than omissions: **M1's residual** (resolve-then-`os.link` is check-then-act
against an attacker who can plant a symlink between the two — out of this item's threat model, bounded in
Design §2's M1 bullet, no work ordered), **the write-then-move window** (non-atomic by design, every
residual loud and detector-visible, resolved in `## Edge Cases` and `## Risk Analysis`, no work ordered),
and **the no-op branch's cosmetic audit line** (round 4's first non-blocking note: on the `same_place`
branch M4's INFO line reads "Renamed … from @New.md to @New.md"; the modeler recorded it as harmless,
not a security defect and not folded, so it is carried unchanged rather than spent a clause on).
None of the three is a `kind: required` mitigation and none has a fold record, which is correct: the
latest speaking threat-model round's EIGHT required mitigations are the only ones `## Mitigation Folds`
carries.

**Round 5's three non-blocking notes, dispositioned so the next round does not re-find them.** (1) The
`guard_mode()` double read — `update_fields` checks the mode inside its lock and `rename_note` checks it
again after that lock releases, so an in-process `os.environ` mutation between the two would put the
door's refusal after the committed write. The modeler ordered no work: it needs code inside the process
to move the variable, which is strictly more privileged than the boundary Prerequisites 6 draws, and
Design §2's re-run table already owns the outcome by name. Carried unchanged. (2) AC-2(b)'s
occupied-destination arm depends on the ambient environment while only the M6 arm is told to set it —
worth one line so a conductor reading a red AC-2(b) checks the shell before the code, and NOT a spec
edit, because the direction is safe (under an ambient `observe` the arm goes RED, not green) and AC-2 is
signed. M7's own arm follows the M6 rule and sets `enforce` explicitly, which is now stated in Task 10.
(3) Round 4's three carried-forward dispositions stand: the no-op branch's cosmetic audit line, the
`update_fields` message's pre-existing person-name disclosure (a shipped class — `base.py`'s
`ValueError(f"{self.type_name} not found in repository: {name}")` already does the same in the same
method), and the `os.environ`-versus-`guard_mode()` spelling warning, folded into both the Design bullet
and Task 6's clause. **OPEN security questions: none**, in round 5 as in round 4.

**The FOURTH spec-review round (2026-09-26), dispositioned so the next round does not re-find any of
it.** Its one blocking finding is folded as the class (above, and in Design §2's "The COMPLEMENT of
that rule"); all three of its non-blocking notes are CLOSED rather than carried, each at its own site:
the `aliases` mirror is gated on `renaming` (Design §2's sequencing block, "Which `aliases` list
wins", Task 6, and the `base.py` `writes` fence), the Book/Meeting `update_fields` widening is declared
as a decision with its measured blast radius (Design §5), and Design §1's `BaseEntity` quotation is
restored verbatim from `obsidian_schemas/models.py:BaseEntity:23-40`. Its carried-forward notes are
re-dispositioned unchanged and none acquired work this round: the duplicated `## Adversarial Review`
heading is the conductor's (above, still not answered here); M1's exact bound, the write-then-move
window and the no-op branch's cosmetic audit line remain the three declared NON-actions listed in the
paragraph above; the `guard_mode()` double read stays deferred for the modeler's own reason, and the
reviewer's observation that it is this round's class one step further out is right and changes nothing
— it needs a privileged actor inside the process, where the occupied destination needs only a taken
filename, which is exactly why one is deferred and the other is folded; AC-2(b)'s ambient-environment
dependence stays a conductor reading note and not a spec edit (the direction is safe and AC-2 is
signed); and architect round 6's out-of-scope items stand as `## Scope Boundary` names them.
**The `## Mitigation Folds` records were NOT edited this round and none needed to be**, checked after
the edits rather than assumed and with the same stated scope as the M7 round's check: all seven
`design:` sentences still resolve to their unwrapped Design lines verbatim, and the five Task-6
`work:` values (M1, M3, M4, M6, M7) still resolve to their clauses verbatim — every clause this round
added to Design §2 is a separate paragraph BESIDE the sentences those records quote, and Task 6's new
DO-NOT-PRE-CHECK clause was inserted above the M1 clause and edited none of them. The two pre-existing
deviations (M2's compressed `work:`, M5's stitched one) are carried unchanged for the same reason: this
round touched neither Task 2 nor Task 13.

**The SIXTH threat-model round (2026-09-26, the second section under that date), dispositioned so the
next round does not re-find any of it.** Its one new required mitigation, M8, is folded as the CLASS
one rung above M7's — Design §2's third rule ("the pre-write arm has TWO obligations"), the second
clause in Task 6, the both-ways battery in Task 10, the bound restated in Design §5 and in the M7
`## Edge Cases` entry, a new `## Edge Cases` entry, a `## Risk Analysis` row, two `## Scope Boundary`
bullets, the fourth disclosed RAISE arm in Prerequisites 7, the `## Verification` failure-mode
enumeration, the `base.py` `writes` fence, the Walls A/B/C row of `## Wall Membership`, and a
`## Mitigation Folds` record. Its four non-blocking notes need no work and are dispositioned here.
(1) The three closures of the fifth fold LAND (the `renaming`-gated `aliases` mirror, Design §5's
declared widening, Design §1's restored `BaseEntity` quotation) — recorded, nothing ordered; the
widening's BOUND is where this round's finding sat, and that bound is now corrected in place.
(2) `_get_cache_key`'s `""` key for a Book reaching `update_fields`' cache surgery is a CORRECTNESS
observation and not a security one: with the frame newly reachable, `old_name_key = name.lower()` is
`""` (`obsidian_schemas/repositories/base.py:BaseRepository.update_fields:498`) while `new_name_key` is
the title, so the removal half operates on a cache entry that is almost never there — nothing is
corrupted on disk, no wrong note is written, and the index is merely not cleaned for a key that was
never set. `## Scope Boundary` already declines `_get_cache_key`'s strip asymmetry in the same
neighbourhood; carried as a NON-action, recorded so the next round does not re-find it. (3) Round 5's
three non-blocking notes stand exactly as the paragraphs above disposition them, including the
`guard_mode()` double read (deferred: it needs a privileged actor inside the process, where this
round's finding needed only an ordinary PATCH field) and AC-2(b)'s ambient-environment dependence
(a conductor reading note; AC-2 is signed). (4) The duplicated `## Adversarial Review` heading is still
the conductor's and is still not answered here. **OPEN security questions: none**, in round 6 as in
rounds 4 and 5. **The M1–M7 `## Mitigation Folds` records were NOT edited this round and none needed to
be**, checked after the edits rather than assumed and with the same stated scope: all seven `design:`
sentences still resolve to their unwrapped Design lines verbatim, and the five Task-6 `work:` values
(M1, M3, M4, M6, M7) still resolve to their clauses verbatim — the new M8 clause was inserted AFTER
M7's and before the "Without the REFUSAL ARM AS A WHOLE" sentence, which no record quotes, and the two
other Task-6 edits (the "four clauses of that body" preamble and the "All THREE disjuncts" sentence)
both sit outside every quoted span. Task 2 and Task 13 were not touched, so M2's and M5's pre-existing
`work:` deviations are carried unchanged for the fourth round running.

## Architectural Review — 2026-09-21

**Recommendation: PROMOTE to architected — the red-team's fold holds where it matters; its second
half is weaker than its own text claims, and that is a spec-time clause, not an approach defect**

Cold-start spawn. Rounds 1–5 of this arm were the architect's and are this document's carry-forward;
I read them, then re-executed the fifth revision's new material against this worktree
(`cage-wt-rix_vnom`, HEAD `6f045a9`) with Read/Grep rather than trusting the account of it — premise
15's two filename rules read off the code, `tests/derivations.py`'s taint machinery read line by line,
plus `move_note`'s body, `_adopt`, and the four sites round 5 left as open notes. The approach has
been settled since round 5 and nothing I found moves it. What I did find is one place where the new
AC-5 asserts a property the machinery it *mandates reusing* cannot deliver — it is real, it is
precise, and it is covered today by AC-1's half of the same fold, which is why it is note 1 and not
round 6.

### Trigger check

Unchanged, four fire: a new public repository door (rename); a behaviour change on nine shipped write
paths with out-of-repo consumer blast radius; a new lint check across three files; effort > 1 day.

### The red-team's finding: the AC-1 half CLOSED, the AC-5 half PARTIAL

The red-team named two independent closures and said either alone would close the gap. After
re-execution that is no longer true — one of them closes it and the other does not.

- **Premise 15 CONFIRMED, both rules, verbatim.** `BookRepository.save` is
  `filename = self._get_file_name(entity)` then `file_path = self.vault_path / filename` then
  `write_markdown_file(file_path, …)` (`book.py:167-178`), with `_get_file_name` deriving
  `f"{title} - {author}.md"` / `f"{title}.md"` under `re.sub(r'[<>:"/\\|?*]', '', …)`
  (`book.py:346-355`). `MeetingRepository.save` is the same two lines (`meeting.py:189-200`), with
  `_get_file_name` deriving `f"Meeting {date_str} - {title}.md"`, `date_str` hyphen-stripped or
  `"unknown"`, title from `topics[0]` / `"with " + first two attendees` / `meeting_id` / `"Untitled"`,
  same class stripped, `[:50]` (`meeting.py:216-231`). Neither calls `super().save()`. The
  type-general restatement of divergence is read off the code, not constructed to fit.
- **AC-1's half is the one that closes it, and it closes it completely.** The planted colliding group
  is the right derivation: at most one member can live at the shared derived filename, so a planted
  pair always contains a divergent member, and for that member a provenance-bound write and today's
  `_get_file_name`-derived write land in **different files** — with the difference visible in the bytes
  of the sibling the caller never named. The mutation constraint (touch none of the deriving fields)
  is what keeps the cell measuring provenance-vs-derivation, and it is stated. Run the red-team's own
  one-line stub against this subject and AC-1(b) fails and (c) fails. That is the discriminator the
  corpus cannot supply, planted for the WI-286 reason and not for coverage.
- **AC-5's half does not close it — see note 1.** The fold rewrote bucket (b) as data flow and told the
  builder to reuse `_taints_a_write`, whose taint set is monotone over names. Monotonicity is cited in
  premise 15 and in AC-5's `why` as the *feature* that keeps the fallback asymmetry legal. It is also
  what admits the escape, one line larger than the one the red-team named.
- **AC-5's asserted foundation is otherwise real.** `_taints_a_write` (`tests/derivations.py:361-409`)
  does seed on a call's return (`:368-382`), propagate to a fixpoint over assignments (`:389-401`) and
  sink at a write call's args and keywords (`:404-408`); `_is_write_call` (`:286-299`) gates on
  `{"write_text", "write_bytes"} | DOOR_NAMES`. Re-seeding it on an `ast.Attribute` call is a second
  seed, not a second scanner, exactly as claimed.

No previous finding re-opened. Rounds 1→2→3→4 moved mechanism → scope → extension → predicate, round 5
found nothing blocking, and the red-team's round landed on criteria construction. This read found
nothing in the mechanism, the seam, the door, the door predicate, the fallback asymmetry, the corpus
population, or AC-2/AC-3/AC-4.

### Review

**Fit:** Strong and unchanged. Seam-then-repair-then-invariant is this project's own shape (WI-026's
detector plus committed live bracket; WI-031's containment wall). AC-4's split — hermetic check over a
committed artifact, live measurement as a conductor ship condition — is the honest treatment of a
live-corpus repair. The two `kind: precondition` fences cover exactly the facts a caged reader cannot
reach, in WI-300 order.

**Duplication:** None. `move_note` exists and is essentially unexercised for this use — re-read in
full: symlinked source refused (`vault_io.py:736-740`), both locks taken in sorted global order with
reentrancy documented (`:744-750`), link-then-unlink so a mid-flight failure leaves a duplicate rather
than a hole (`:758-778`), `NoteAlreadyExists` raised by syscall (`:770-771`), `forget_snapshot` on both
(`:780-781`). Every clause AC-2(a)(b)(d) leans on is in the code. `gate_write` and `NameGateRefusal`
are already imported by the linter (`lint_vault.py:47-48`), so AC-3's marker adds no new coupling.
AC-5 extends `tests/derivations.py` rather than growing a second scanner.

**Boundaries:** Clean, one capability per owner: the parse owns provenance, `_resolve_write_target`
owns target selection, one door owns relocation, the linter owns detection and never repair. The
WI-185 question is answered at the structure's source. The fallback asymmetry remains the load-bearing
detail and is still argued from the code rather than asserted.

**Determinism boundary:** n/a — nothing is handed to an LLM. The one judgement call, per-note repair
direction, is routed to a committed human-signed table with a shape check.

**Reversibility:** Good. Detector read-only; repair per-note through a door that refuses an occupied
destination by syscall. The seam is the one hard-to-reverse act and it has a consumer audit in front
of it.

**Generalization:** Now correctly type-general, which is this revision's real gain beyond closing a
hole: divergence is stated as "the type's own filename rule recomputed against the file it was parsed
from", with Person's raw stem≠name as the instance. That is the right altitude — it makes the Book and
Meeting plants one derivation instead of two ad-hoc fixtures, and it is what a fourth repository type
would inherit for free.

**Cost & maintenance:** Unchanged — one build session at its upper end plus two conductor acts. Nine
one-line call-site edits, one helper, one private attribute, one door, one check, one derived scan.
The fifth revision added planted fixtures and a seed, not surface.

**Build vs extend vs integrate:** Extend, throughout.

**Prior art (outside view):** Unchanged and still not a compensation-machinery concern. The world's
answer to filename/field divergence is to stop making the filename the identity (Notion, Roam:
immutable id, title as label); in Obsidian the filename IS the wikilink target, so identity-by-path is
imposed by the platform rather than chosen. WI-125's identifier index is already that id-based layer
inside this package, and the provenance stamp is the same move one level down.

### Notes for the spec-writer (non-blocking)

**1. AC-5's data-flow rule is monotone, so it still admits the escape it was folded in to refuse —
only AC-1's half of the red-team's fix actually closes the gap.** `_taints_a_write` propagates by
ADDING names (`tests/derivations.py:389-401`); nothing is ever untainted, and there is no branch
awareness. So this passes the wall as specified:

```
file_path = self._resolve_write_target(entity)       # seeds file_path
filename  = self._get_file_name(entity)              # today's two lines, unchanged
file_path = self.vault_path / filename               # UNCONDITIONAL — resolved value discarded
write_markdown_file(file_path, ...)                  # first positional is tainted → bucket (b)
```

That is a ONE-LINE INSERTION into today's `BookRepository.save`, and it is not in AC-5's REFUSED
battery: member 3 covers "the return bound and unused … or a name the write never reads", and here the
write reads the name. Worse, AC-5's ACCEPTED member 5 — "a seam-routed writer whose documented
fallback arm REBINDS THE SAME LOCAL to a name-derived path before writing, which must PASS" — is this
same shape with an `if` around the rebinding, and the mandated machinery cannot see the `if`. So the
criterion's `desc` (the rule) and its `why` ("a function that calls the seam and discards its return …
routes nothing", "narrowed here to the write's PATH argument") disagree about the same machinery,
which is the shape round 3 blocked on inside AC-1. The reason this is a note and not a sixth round is
the un-deferrability test this arc has used four times: it reaches no conductor act outside the cage,
changes no other criterion, and — decisively — AC-1's planted divergent Book and Meeting colliding
groups catch this exact stub today, for all nine paths, because the write lands on the sibling. The
exposure is AC-5's headline ("a tenth write path cannot route around it") and a future tenth path, not
any path that exists. What to write: add the unconditional-rebinding spelling to REFUSED, and state
the discriminator the rule turns on. Two spellings that work and are implementable on the same AST —
(i) a tainted name may be REBOUND before the sink only inside a branch whose test mentions it, or
(ii) require the fallback to be expressed in the path expression itself
(`file_path = self._resolve_write_target(entity) or <name-derived>`, and a bare `if … is None: raise`
for the refusing callers), which makes "discard it" unrepresentable rather than detected. (ii) is the
structural answer and costs the nine call sites nothing.

**2. "The path parameter of the door" is ambiguous for the one door this item ships.** AC-5 spells the
sink two ways — "the first positional of `write_markdown_file`, the path parameter of the door".
`move_note(src, dest)` has TWO (`vault_io.py:721`), and a rename door legitimately derives `dest` from
the new name, so a rule reading "all path arguments" would refuse the item's own door. FIRST POSITIONAL
is the clean total rule and it happens to be correct everywhere: `write_markdown_file(file_path, …)`
(`writer.py:160`), `write_note(path, text, *, precondition, origin)` (`vault_io.py:670`),
`create_note(path, text)` (`:701`), and `move_note`'s first positional is `src` — the note being moved,
which is exactly the one the seam must resolve. One clause.

**3. AC-3(c)'s marker has a shipped shape to reuse rather than invent.** `lint_vault` already carries
`NameGateRefusalRecord` with a `path` and a `pattern` field (`:865`), already catches `NameGateRefusal`
and records `exc.pattern` (`:1161`, `:1185`), and already calls `gate_write(delta,
declared_type=fm.get("type"), …)` (`:1107`). Corroboration for premise 14 from a third site, worth
knowing because it shows the linter's author already reasoned about this exemption: the comment at
`:1009-1014` states that in the `--fix` delta path "the phone-sentinel exemption is structurally
unreachable" because no identifier field reaches the gate there. The detector's call is the opposite
case — it gates the note's whole record, so `phones` IS present and the exemption IS reachable, which
is precisely why the door predicate and `validate_strict` part company. Say that, so a builder reading
`:1009-1014` does not conclude the exemption cannot fire in this tool.

**4. Precondition 2's question (4) puts `model_copy(update=…)` on the wrong side of the stamp.** It
lists `model_copy(update=...)` among the reconstructions that "drop the provenance stamp". In pydantic
v2 `model_copy` copies `__pydantic_private__`, so a declared `PrivateAttr` SURVIVES it — unlike
`model_dump()`/`model_validate()`, which is what AC-1(f) is correctly written against. Confirm it at
spec time and move it to the preserving side. Direction of the error is safe (the audit
over-collects rather than misses), so it needs no re-commissioning — but question (4) exists to size
the one residual arm, and a superset that silently includes the commonest copy idiom would report that
arm as the main path when it may be empty.

**5. Approach F's rejection overstates by one index.** It says C "changes no key, no index and no
lookup … `get`, `get_all`, `_file_map` and the WI-125 identifier index behave exactly as they do
today". `_adopt` writes `_file_map[name_key] = file_path` (`base.py:168`, `:186-188`), and `save`'s
`file_path` is the thing this item changes — so after a provenance-bound save of a divergent entity,
`_file_map` points at the note that actually exists instead of at a canonical filename that may not.
That is an improvement and no criterion depends on the sentence, but the sentence as written is false
and it is the paragraph a later reader will quote when arguing C is index-neutral.

**6. Carry-forward: round 5's four notes are still open, by design, and I re-verified the two with code
claims.** The fifth revision addressed the red-team only, so they have not been folded and should not
be read as stale. (i) The door predicate's frame — `PersonRepository.save`'s WI-021 rider calls
`gate_write(model_to_frontmatter(entity), declared_type=self.type_name, whole_record=True)` at
`person.py:1190-1191`, above `super().save()`, CONFIRMED, and its own docstring says the gate runs
twice on one save (`:1186-1188`), which makes spelling the predicate as *"would `repo.save(<entity
parsed from this note>)` raise, and with what `pattern`"* the simplest true form. (ii) The
`name:`-less note — `person_missing_name` is ERROR with `auto_fixable=True` (`lint_vault.py:440-443`)
and `--fix` writes the stem into the field (`:1040-1043`), CONFIRMED, so one clause excluding a note
with no stored `name:` from this check avoids one note carrying two ERRORs where the auto-fixable one
repairs the never-fixable one away. (iii) AC-5 enumerating a strict subset of `_is_write_call` and
(iv) the deliberately-out-of-scope items stand as written.

Five architect rounds and one red-team round have each closed and narrowed, with nothing re-opened
across six independent re-executions. The mechanism, its scope, the class's extension, the predicate
that decorates it and the criteria's own construction have each been attacked and each survived.
What remains is spec-writer work — formalize the nine call sites, `update_fields`' write → move →
rebind ordering, the detector's two arms, and the scan's bucket rule with note 1's discriminator in
it. Nothing here needs redesigning during speccing, which is the bar this gate is calibrated to.

*(Stage not advanced from this spawn: the cage grants no shell, so
`python src/stage_advancer.py advance WI-029 --to architected --project <path> --actor architect` is
the conductor's to run.)*

```verdict
gate: architect
verdict: PROMOTE
date: 2026-09-21
model: claude-opus-5
note: The red-team's fold holds where it decides outcomes — premise 15's two filename rules re-read off the code, and AC-1's planted divergent Book/Meeting colliding groups genuinely discriminate a provenance-bound write from today's `_get_file_name`-derived one (the divergent member's write lands on its sibling under the stub), so every one of the nine paths is covered; AC-5's data-flow rebuild is the weaker half, since `_taints_a_write` is monotone over names (tests/derivations.py:389-401) and so cannot distinguish the ACCEPTED guarded fallback from an unconditional rebinding that discards the resolved value — but that residue reaches no conductor act, no other criterion and no path that exists today, so it is note 1 for the spec-writer rather than a sixth round.
```

## AC Red-Team — 2026-09-21

Re-verify round (round 2 of this gate; round 1 above, `prior: none`, is mine). Spawned cold-start,
different model from `ideation-partner` per the driver's decorrelation rule (`claude-sonnet-5`, same
model I ran round 1 on — the architect's fold is what changed, not the reviewer). I did not read round
1's finding and trust the architect's account of it: I re-derived the failure scenario from the entity
predicate and re-executed the code claims underneath it.

**Round 1's finding: CLOSED, verified against the code and not against the fold's prose.**

- **The stub AC-1 was blind to now fails AC-1, independent of AC-5.** I re-read AC-1's planted-subject
  requirement (`## Acceptance Criteria`, AC-1 desc: "THE BOOK AND MEETING SUBJECTS ARE PLANTED AS
  COLLIDING GROUPS AND EVERY SUCH GROUP CONTAINS A DIVERGENT MEMBER") and simulated the exact stub my
  round-1 finding named — `_resolve_write_target(entity)` called and its return discarded,
  `_get_file_name(entity)`-derived write kept — against that fixture. For the divergent member of a
  planted collision pair, `_get_file_name` recomputes the SAME derived filename as its non-divergent
  sibling (that is what makes the pair collide), so the stub's write lands on the sibling's file, not
  on the file the divergent member was parsed from. That fails AC-1(b) ("the changed bytes are in the
  file that subject was parsed from") and AC-1(c) ("every other member of that group is byte-identical
  afterwards") directly — no dependency on AC-5's bucket classification. I confirmed the mechanics this
  rests on by direct read rather than by trusting the document's account: `BookRepository.save` is
  `filename = self._get_file_name(entity)` then `file_path = self.vault_path / filename` then
  `write_markdown_file(file_path, entity=entity, ...)`, verbatim, at `book.py:167-178` — the two-line
  shape premise 15 and the architect's round 6 describe, still unbuilt (this is a draft AC set; the
  seam does not exist in the tree yet). So the closure is real and it is the stronger of the two the
  document offers: AC-1 alone defeats the stub, for both planted types, with no reliance on AC-5.
- **AC-5's residual weakness is real, exactly as the architect's round-6 note states, and does not
  reopen my finding.** I read `tests/derivations.py:361-409`'s `_taints_a_write` directly rather than
  taking the "monotone over names" claim on faith: propagation is `tainted.add(name)` with no removal
  anywhere in the fixpoint loop (`:397-401`), and the predicate walks `_own_body_nodes(func)` with no
  branch structure retained — so a tainted name rebound unconditionally right before the sink and a
  tainted name rebound inside a guarded fallback are the same AST shape to this scan. That confirms the
  escape the round-6 note describes is real for a FUTURE tenth write path. It is not a live escape for
  this item's own nine paths, because AC-1's planted fixtures catch the concrete instance (Book/Meeting)
  regardless of what AC-5 lets through structurally, and premise 12's grep (re-confirmed across four
  architect rounds, not re-run by me byte-for-byte this round) is what establishes there is no tenth
  path in the tree today for the gap to bite on.
- **I independently re-ran the two corpus predicates my own round 1 leaned on, against the files rather
  than the document's transcription of them**, per this gate's standing instruction to run rather than
  trust an empirical premise: `tests/fixture_vault.py`'s manifest (`:246-306`) confirms the four-member
  divergent population verbatim (`@Quillam Ostrivane.md`, `@Quillam Lumbrek.md`,
  `@Perrowin Tessamund Drostane.md`, `@Yolvenna Brindlecote Skarnell.md`) and that
  `@+447700900123.md` declares no `phones` (so it is not itself the sentinel-exempt plant AC-1 requires
  — a NEW note is what AC-1 names). `name_validation.py`'s `TIER1_BRANCHES` (`:190-306`) confirms
  `pure_digit` is the sole `sentinel_exempt=True` record among ten. `name_gate.py:355-358` confirms
  `gate_write` derives `allow_phone_sentinel` from the payload; `name_validation.py:594` confirms
  `validate_strict`'s own default is `False`. All four reproduce exactly as round 1 and the architect's
  four rounds state them.

**Is the AC-5 residue material enough to REVISE anyway?** No, and saying why is the finding this round
actually returns. The calibration this gate is held to is whether a builder could satisfy the set while
skipping the real work the Intent needs — not whether a criterion's own headline is airtight in the
abstract. For every write path this item actually ships (the nine `## Approach` enumerates), AC-1's
per-member, per-group oracle is the wall that decides correctness, and it does not admit the "call and
discard" shape for either of the two paths where that shape is tempting (Book, Meeting) — I verified
that failure directly above, not by re-stating the architect's claim. AC-5's gap only bites a tenth path
that does not exist in this build, which is exactly the boundary the role's calibration section warns
against re-litigating ("too strict: you REVISE because... you would have specified the work
differently"). Blocking a signable set to demand AC-5's wall be un-gameable in the abstract, when the
concrete defect it exists to prevent is already caught by a sibling criterion, would cost a fold round
for a residue the spec-writer can close with the two-line fix the architect's round-6 note already
names, without touching an approach the architect closed five rounds ago.

I attacked AC-2, AC-3 and AC-4 fresh rather than re-reading my round-1 pass on them (which did not find
material issues there either): AC-2's collision-pair door test still stands on the live-shaped Quillam
pair rather than a hand-picked stand-in, AC-3's four-count derivation and door-predicate marker still
match my own re-execution of the manifest and the Tier-1 table, and AC-4's shape/consistency rule still
correctly forbids `rename` on a gate-refused row while leaving it legal on the sentinel-exempt one.
Found nothing new in any of the three.

```verdict
gate: ac-red-team
verdict: PROMOTE
date: 2026-09-21
model: claude-sonnet-5
note: Round 1's CRITICAL (Book/Meeting `save()` faking provenance-binding via call-and-discard) is closed — re-simulated directly against AC-1's planted colliding-group oracle rather than the fold's prose, and the stub fails AC-1(b)/(c) on the divergent member's sibling-clobber regardless of AC-5's bucket rule. AC-5's monotone-taint residue (architect round 6, note 1) is confirmed real by direct read of `_taints_a_write` but bites only a hypothetical tenth write path, not any of the nine this item ships, so it is correctly non-blocking rather than a re-opening of this finding.
```

## AC Sign-off

```verdict
gate: ac-signoff
verdict: PROMOTE
date: 2026-09-25
reviewer: dave
channel: cli
signed_at: 2026-09-25T11:22:44+01:00
provenance: verified
signoff_escalation: ESC-WI-029-exploring-awaiting-ac-signoff-c8fa2aec
ac_hash: 15189b874b27
intent_hash: 2dd3a4440900
ac_hash_AC-1: c6f4d70405ec
ac_hash_AC-2: 510393423e26
ac_hash_AC-3: bb186845ac80
ac_hash_AC-4: 82e8589871c2
ac_hash_AC-5: 366c0cca779e
artifact: docs/spec-reviews/WI-029-dave-review-2026-09-25.md
```

## Data Audit — 2026-09-25

**Recommendation: PROMOTE to specced**

Cold-start read, no prior data-premise round on this document. The cage grants Read/Grep/Glob and no
shell, so every predicate below was executed with those against this worktree
(`cage-wt-3dsckdph`, the tree as committed at `b8e5d77` plus the one untracked doc
`docs/whatsapp-jid-value-type.md`, irrelevant here). I re-ran the premises rather than reading the
five architect rounds' and two red-team rounds' accounts of them; where I reached a fact by a
different route than the document did, I say so.

### Trigger check

**Class 1 AND Class 2, both heavily.** Class 1: the document quantifies live data in four
load-bearing places — 8 divergent live person notes, `len(PersonRepository().conflicts)` = 0, the
`pure_digit` branch at 2 live members, `same_name_collision` absent only in its ≥3 sense (largest
live collision 2) — and AC-1's, AC-3's and AC-4's shapes are each decided by one of them. Class 2:
three new rules are introduced whose correctness is a claim about their effect on the corpus that
exists today — the `stem_name_divergence` detector (AC-3 pins an exact count over the frozen
corpus), the AC-5 containment scan (it must classify every mutation site in the package that exists
now), and AC-4's shape/consistency rule (it must not refuse a correct artifact). All three were run
against what exists. No Class-0 arm anywhere in this item.

### Premises, re-executed

Each line is a predicate I ran, then the result, then the verdict against what the document claims.

1. **The nine name-bound write paths (premise 12) — CONFIRMED, and I derived the population
   independently rather than checking the list.** Predicate: grep
   `write_markdown_file\(|write_note\(|create_note\(|move_note\(` over `obsidian_schemas/**`, then
   read each enclosing function. Twenty hits. Three are the door DEFINITIONS (`vault_io.py:670`,
   `:701`, `:721`); one is a docstring (`writer.py:32`) and one a module docstring
   (`name_gate.py:9`). The remaining fifteen call sites sit in exactly **thirteen** enclosing
   functions: four in `writer.py` (`write_markdown_file` holding both `:317` and `:319`, then `:393`,
   `:451`, `:504`) — the path-taking leaves — and **nine** repository paths: `base.py:398` (`save`),
   `base.py:490` (`update_fields`), `person.py:1447`+`:1458` (`append_to_timeline`, two writes one
   function), `:1559`, `:1679`, `:1758`, `:1828` (the other four body-writers), `book.py:170` and
   `meeting.py:192` (the two `save` overrides). Nine, and "writer.py's four sites" in AC-5 is four
   FUNCTIONS and not four calls — which is the reading bucket (a) needs and is the correct one.
2. **The divergent class's extension over the frozen corpus (premise 13) — CONFIRMED, note for
   note.** Predicate: read `tests/fixture_vault.py`'s `NOTES` manifest in full and select every entry
   with `declared_type="person"` and a declared `fields` mapping whose filename stem, less the `@`,
   differs RAW from `fields["name"]`. Twenty-two such entries (`:219-341`), which is what `LOADABLE`'s
   own comment says (`:521`, "22 person files"). Four diverge: `@Quillam Ostrivane.md` and
   `@Quillam Lumbrek.md` (both `Quillam Ostrivane Lumbrek`), `@Perrowin Tessamund Drostane.md`
   (`Perrowin -> Tessamund Drostane`), `@Yolvenna Brindlecote Skarnell.md`
   (`Yolvenna/Brindlecote Skarnell`). `@Dave  Marrowyn Fennwick.md` carries the double space on BOTH
   sides and is correctly CLEAN under the raw comparison; `@+447700900123.md`'s stem and name are the
   same digit string; `@Quillam Ostrivane Lumbrek.md` agrees with its stem. Exactly one name-sharing
   group, the three `Quillam` notes. AC-1's union subject set is therefore five corpus subjects and
   AC-3(a)'s count is four, both as written.
3. **The door predicate's two spellings (premise 14) — CONFIRMED, by a different route than the
   document's.** Predicate: grep `sentinel_exempt` over `name_validation.py`. Sixteen assignments;
   the Tier-1 tuple's ten records are at `:195`, `:206`, `:218`, `:230`, `:242`, `:253`, `:264`,
   `:275`, `:287`, `:304` and **exactly one is `True`** (`:287`, the `pure_digit` record). The
   remaining six `False` records belong to the later (non-Tier-1) tuples. `gate_write` derives
   `allow_phone_sentinel = bool(introduced.get("phones")) and name_text.strip().lstrip("+").isdigit()`
   and hands it to `validate_strict` (`name_gate.py:355-363`), read verbatim;
   `validate_strict`'s own signature defaults it `False` (`name_validation.py:594`). The two spellings
   really do disagree on one branch, and the census measures that branch at `count: 2`,
   `status: MEASURED` (`docs/vault-shape-census.md:148-157`, prose at `:260-261`). The WI-286 plant
   AC-1 and AC-3(c) require is the only thing that can tell the implementations apart — correct.
4. **The live counts — CONFIRMED at source.** `stem_name_divergence`: **8 live**
   (`docs/vault-shape-census.md:262`). The ONE-class-or-TWO ruling: `same_name_collision` ABSENT,
   "largest live collision: 2" (`:266-271`) — so the collision shape this item's seam is decided by is
   live, as the architect's round 1 said.
5. **The seam's foundation (premises 6, 10, 15) — CONFIRMED.** `ParsedDocument.file_path` is a
   declared field (`parser.py:54`), set from the path handed in (`:236`, `:250`), and
   `parse_markdown_content` passes `file_path=None` (`:283`) — so entities from that route carry no
   stamp, exactly as AC-1(f) declares. `stem_name` has ZERO hits anywhere in `scripts/lint_vault.py`
   (grep over the tree returns only `tests/fixture_vault.py` and `tests/test_fixture_vault.py`), so
   the detector genuinely does not exist. `BookRepository._get_file_name` is
   `f"{title} - {author}.md"` / `f"{title}.md"` with `[<>:"/\|?*]` stripped (`book.py:340-355`),
   verbatim as premise 15 reads it.
6. **AC-5's cited vocabulary — CONFIRMED.** `DOOR_NAMES = frozenset({"write_note", "create_note",
   "move_note"})` at `tests/derivations.py:47`, the exact line and content AC-5 cites;
   `_is_write_call` at `:286` matches `{"write_text", "write_bytes"} | DOOR_NAMES`; `_taints_a_write`
   at `:361`. The machinery AC-5 proposes to reuse is where it says it is.

### The two grounding artifacts, read against the criteria they ground

Both are in the tree. I read each in full and checked it against the criterion that consumes it,
because a precondition artifact that a criterion's own shape check would REFUSE is the expensive
failure here — it is commissioned once, outside the cage.

- **`docs/stem-divergence-live-baseline.md`** carries the script verbatim, its stdout, and a per-row
  table with all three of (b1) correct side, (b2) occupancy, (b3) the DOOR's verdict — and the (b3)
  column was produced by `gate_write(fm, declared_type=fm.get("type"), whole_record=True)` (`:79`),
  the door and not the bare validator, which is the correction round 4 bought. Entry figures: 8
  divergent, 0 conflicts, 1,171 person notes, **0 of 8 gate-refused**, 24 incoming wikilinks, 14
  attendee-carrying notes, 1 destination occupied by a DIFFERENT note (row 8) and 1 by the SAME file
  under the case-insensitive filesystem (row 3). Directions total 7 RENAME + 1 MERGE + 0
  FIELD-REPAIR. I checked it against AC-4's consistency rule clause by clause: no row resolves to
  `rename` while gate-refused (vacuous — none is refused); no row resolves to `rename` onto a
  destination occupied by a different note (row 8 is the MERGE); row 3's `same-file` value is present
  and is what makes its `rename` legal. **The artifact passes the check that will read it.** Two of
  the criteria it grounds have no live subject today and say so honestly: AC-1's sentinel-exempt
  subject and AC-3(c)'s marker discriminate only in the corpus and the plants, which the artifact
  states outright (`§1`, `§2` totals) rather than leaving to be discovered.
- **`docs/wi-029-consumer-audit.md`** answers all six commissioned questions per repo with HEADs,
  literal commands and verbatim output. The load-bearing answers: 19 of 19 consumer sites on the nine
  paths are on LOADED entities, so AC-1(f)'s residual arm has an empty consumer population; 0
  `auto_load=False` uses anywhere, with one construct-then-write relying on the lazy default
  (`orchestrator bin/repair-field-rfc2822.py:55`), which the seam converts into a correct write; 0
  reconstructions feed a write; `BookRepository.save`/`MeetingRepository.save` have 0 consumer call
  sites. The one consumer-visible behaviour change is named — HAL9000's generic entity PATCH
  (`routers/entities.py:461`), which forwards an arbitrary body that may carry `name` — and it is the
  one thing in this item a consumer will observe. That is in Dave's signed read-back (conductor
  read-back note 4), so it is disclosed, not discovered.

### Counterexample hunt (WI-293)

The Intent and three criteria quantify universally over enumerable domains — AC-1 "no library write
can turn one person note into two", AC-5 "every mutation site under `obsidian_schemas/**`" and "the
ONLY way a write target is chosen in this package". I walked two domains for members that are false
by DESIGN, reading declarations and docstrings rather than shapes.

**Domain A — every byte-mutating site under `obsidian_schemas/**`.** Predicate: grep
`write_text\(|\.unlink\(|os\.replace|os\.rename|shutil\.|open\(.*["']w` over the package, unioned
with the door/`write_markdown_file` grep of premise 1 above. The union adds exactly one class beyond
the thirteen functions premise 1 found: **`vault_io.py`'s own terminal writes** — `os.replace` at
`:537` (inside `_commit`) and `:765` (inside `move_note`), `os.unlink` at `:586` and `:776`. This is
a false-by-design member and it is the one the census-shaped reading would file silently: it is a
mutation site under `obsidian_schemas/**` and it will never route through `_resolve_write_target`,
because it IS the write door (CLAUDE.md names `vault_io.py` "THE write door (WI-004)") and sits
BELOW the seam by construction. **Disposition: named exclusion, and it needs no criterion change,
for two independent reasons.** AC-5's enumeration predicate reaches calls TO `write_markdown_file`
and to `DOOR_NAMES`, not the doors' own bodies, so these sites are never enumerated; and even if a
builder widened the enumeration to raw filesystem calls, all three doors take their path as a
PARAMETER (`write_note(path, …)`, `create_note(path, …)`, `move_note(src, dest)`, `:670`, `:701`,
`:721`), so every one of them classifies legally into bucket (a). The rule is total either way. It
is worth one line in the spec so a builder who reads AC-5's headline literally ("every mutation
site") does not widen the scan and then go red on the door the item ships through.

**Domain B — every name-derived path resolution in the package, write or read.** Predicate: grep
`get_file_path\(` plus `file_path = self.vault_path` over `obsidian_schemas/**`. This reproduces the
nine write paths and `_get_body_content` (`person.py:1590`), the read-side site the document already
books as one spec line — and finds **one further read-side member the document does not name**:
`person.py:1353`, inside `create_stub`'s lost-create-race recovery, which builds
`self.vault_path / f"@{clean_name}.md"`, `_load_file`s it and then `_adopt`s it into `_file_map`. It
is a READ and so outside AC-1's write-path scope, and it is CORRECT as written — the path is exactly
the one `save` just collided on, so the recovered entity's stamp and `_file_map` entry both name the
winner's real file. Disposition: no criterion change; the spec's read-side note is two sites, not
one.

**Nothing found in either domain falsifies a criterion.** Both domains and both predicates are stated
above so the "none found" is falsifiable.

### One thing the manifest predicate cannot see, and I checked the bytes instead

AC-3(a) derives its expected four-member set "from the manifest by the same predicate AC-1 uses",
while the SHIPPED detector reads files. Those two populations are not the same domain: the manifest
predicate requires a declared `fields` mapping, and three person-owned specimens declare none —
`@Ferrigan Ostrakine.md` (`:467`, SCHEMA_DRIFT), `@Halvorne Sennaby.md` (`:465`,
MALFORMED_FRONTMATTER) and `@Isolde Varnholt.md` (`:472`, UNREADABLE). A divergent member there would
make the detector emit five where the derivation expects four. I read all three: `@Ferrigan
Ostrakine.md` stores `name: "Ferrigan Ostrakine"` and `@Halvorne Sennaby.md` stores an unterminated
`name: "Halvorne Sennaby`, and `@Isolde Varnholt.md`'s declared hex (`:477`) decodes to
`name: "Isolde Varnholt"` — every one of them agrees with its own stem. **So AC-3(a)'s four holds
against the corpus BYTES and not only against the manifest**, and AC-3(e)'s `read_error` arm keeps
the undecodable one out regardless. This is a corpus fact rather than a property, so it is worth one
spec line: the derived expectation must handle a `NoteSpec` carrying no `fields` (skip it) rather
than crash on it or silently widen.

### Premise rot, for the build-runner

The live baseline is dated **2026-09-21** and this gate runs **2026-09-25** — four days of drift on a
corpus that demonstrably moves: the artifact itself records conflicts going 1 → 0 and person notes
1,172 → 1,171 within one hour on its own measurement day (`§1`, the companion reading). This is
contained by design and I am not blocking on it: the Intent carries no frozen count (the 2026-09-21
sharpening deliberately replaced "the three forked notes" with "the forked notes" for exactly this
reason), no acceptance criterion asserts the number 8, and AC-4's exit half re-runs the identical
script. The build-runner's `### 2. Verify Assumptions` step should re-run `§0`'s script before
building and treat a changed direction TABLE — a new row, or a row whose (b2)/(b3) answer moved — as
a drift report, not merely a changed count.

### Conclusion

Every empirical premise this item's criteria rest on has been executed against real data and each one
holds: the corpus premises re-derived here note for note, the live premises carried by two committed,
dated, privacy-walled conductor artifacts that were produced by the exact predicates the criteria
name — including the door call rather than the bare validator, which is the one place a two-column
table would have come back internally contradictory. The two gaps the audit found are read-side and
enumeration-scope notes for the spec-writer, neither of which changes a criterion. Three universals
were walked for false-by-design members; one class was found (`vault_io`'s own terminal writes) and
is dispositioned as a named exclusion that the criterion's own enumeration predicate already
excludes. Zero OPEN data questions.

```verdict
gate: data-premise
verdict: PROMOTE
date: 2026-09-25
model: claude-opus-5
note: Every premise re-executed independently and all hold — the nine write paths derived fresh from a door-grep (13 enclosing functions: 9 repository paths + writer.py's 4 leaves), premise 13's four divergent corpus members and single name-sharing group note for note, the one `sentinel_exempt` Tier-1 record out of ten with `gate_write` deriving the flag the bare validator defaults `False`, and the census's 8 / 2 / largest-collision-2; both grounding artifacts are in HEAD, dated, produced by the DOOR call the criteria name, and the live baseline passes AC-4's own consistency rule (0 gate-refused, 7 RENAME + 1 MERGE, row 3 same-file, row 8 different-note). Counterexample hunt over two enumerated domains found one false-by-design class — `vault_io.py`'s own `os.replace`/`os.unlink` terminal writes — excluded by AC-5's enumeration predicate and legal under bucket (a) anyway, so no criterion moves; the four-day-old live baseline is the only rot risk and is contained by the Intent carrying no frozen count plus AC-4's exit re-run.
```

## Threat Model — 2026-09-26

**Recommendation: PROMOTE to threat-modeled — round 6 (the SECOND section carrying today's date under this
heading; round 5 is the earlier one, and this is a distinct round, not a re-emission of it). M1 through M7
all HELD: I re-verified each against the code or the artifact it prescribes, every ordinal is unmoved, and
the seven fences below are RE-EMITTED with byte-identical `desc`. The FIFTH fold — the fourth spec-review
round's occupied-destination complement rule — is correct at every citation it rests on, and I checked its
three non-blocking closures too: all three land. The finding this round is inside the fold again, and again
it is the fold's own widening that made it findable. Design §5's new "One CAPABILITY WIDENING" declaration
states, as a decision, that Task 3's `resolved`-first reorder makes `update_fields` usable on `Book` and
`Meeting` for the first time, and bounds it with *"the one thing it does NOT widen is the rename branch,
which M7 refuses for both types"*. That bound is `name`-shaped, and those two types' filename rule does not
read `name`: `BookRepository._get_file_name` derives from `title` and `author` (`book.py:340-355`) and
`MeetingRepository._get_file_name` from `date`, `topics`, `attendees` and `meeting_id`
(`meeting.py:208-231`). So a delta carrying NO `name` key — the exact delta the M7 `## Edge Cases` entry
blesses as *"unaffected"* — passes every disjunct, passes `gate_write` untouched, COMMITS, moves nothing,
aliases nothing and raises nothing: a silent, detector-blind instance of this item's own defect class,
newly reachable through the one externally-supplied door the item names. One new required mitigation, M8,
one more disjunct on the predicate Task 6 already prescribes, keyed on the repository's own declared
filename rule.**

Sixth threat-model round on this document, spawned cold-start. I read it from line 1, then re-read the
material the FIFTH fold added — Design §2's **"The COMPLEMENT of that rule"** block and its four-row NO
table, the SECOND rule beneath the precondition table, the loudness precision naming `Company` as the one
detector-blind residual, the re-run table's new DOOR-frame scoping paragraph, the `renaming` gate on the
`aliases` mirror in the sequencing block and in "Which `aliases` list wins", Design §1's restored
`BaseEntity` quotation, Design §5's capability-widening declaration, Prerequisites 7's three disclosed
RAISE arms, the new `## Edge Cases` entry beside the occupied-destination Decision, `## Risk Analysis`'s new
residual row and its amended `update_fields`-moves-a-file row, Task 6's DO-NOT-PRE-CHECK clause and Task
10's occupied-destination arm — and checked each against the CODE rather than against the fold's prose. I
re-read round 5 in full as my carry-forward.

### Trigger check

The same six fire, unchanged in shape: filesystem operations on user-owned files, persistence, untrusted
vault bytes crossing into a trusted write-target decision, PII (person names in a WARNING, an ERROR and a
committed live-vault artifact), an out-of-repo blast radius through three `-e` consumers, and configuration
that changes a trust boundary. The fold added no seventh: no network, no subprocess, no credential, no new
import capability, no new environment read. The trigger this round's finding sits on is the second reached
through the first: an externally-supplied PATCH body persisting a field change that breaks the
filename-to-content agreement, on a write path this item opens.

### The seven standing mitigations, re-verified against the code

**M1 — still landed and still total.** The fold inserted nothing into the door body: the sequence is
unchanged at source-resolve → `source.exists()` → `destination = self.vault_path / new_filename` → M1's
containment block → M6's `mode = vault_io.guard_mode()` → `old_stem` → `same_place` → the three branches, so
M1 still precedes every move on all three branches. I re-confirmed the two facts underneath it in this
worktree rather than carrying round 5's account: `move_note` still refuses only a symlinked SOURCE
(`obsidian_schemas/vault_io.py:move_note:736-740`, a `WriteFailedError` raised BEFORE `_resolved(src)`) and
checks nothing about where `dest` points — `:741-742` resolves both operands and `_move_locked` goes
straight to `os.link` — so M1's clause is still the only thing bounding the destination. Task 6, ordinal
unmoved.

**M2 — still landed, unchanged.** Task 2's arm still asserts the PROPERTY (the accessor
`_resolve_write_target` reads answers A's own path; nothing the seam reads answers B), with pydantic's
extras retention demoted to a Build-Log observation. The fold touched neither the stamp nor the parse, and
Design §1's restored quotation is where I checked it: `obsidian_schemas/models.py:23-40` is byte-verbatim
the docstring, the four `ConfigDict` lines with both inline comments, and `type:`/`tags:` at `:39-40` — the
fold's third non-blocking closure is exact. Task 2, ordinal unmoved.

**M3 — still landed, unchanged.** `source.with_name(destination.stem + ".rename-tmp.md")` is byte-for-byte
in the door body, in Task 6's work text, in the `## Edge Cases` entry for a process dying mid-two-step and
in the `## Risk Analysis` row; Task 10's oracle is still `vault_path.glob(repo.file_pattern)` with the
rejected spelling driven through the same glob as a near-miss. The fold changed no branch, so the staging
window is unchanged in width. Task 6, ordinal unmoved.

**M4 — still landed, unchanged.** `logger.info("Renamed %s note from %s to %s", self.type_name,
source.name, moved.name)` in the door body and in Task 6, captured in Task 10 through
`captured_logs(level=logging.INFO)`. Task 6, ordinal unmoved.

**M5 — still landed, unchanged, and untouched by this fold.** Task 13 still carries the token-class rule
whole-file in both halves, with no fence toggle and no non-vacuity guard in the privacy path, and the
reader battery is still pinned MUST-FIRE for a bare filename INSIDE a fenced code block. This round's diff
touches neither the artifact nor Design §4a, so the empirical half stands as round 4 measured it and round 5
re-read it. Task 13, ordinal unmoved.

**M6 — still landed, unchanged, and I re-derived its load-bearing citation rather than reading it back.**
`obsidian_schemas/vault_io.py:_move_locked:757-771` is verbatim the `try: os.link(source, target)` /
`except FileExistsError` / `if guard_mode() == "observe": logger.warning(...) ... os.replace(source, target)
... return target` / `raise NoteAlreadyExists` shape the clause describes, at exactly those lines, with the
`except OSError` → `WriteFailedError` arm at `:772-773` and `create_note:709-718` carrying the identical
fail-open at `:712-718` — so M6's scope bound still names a real sibling. The door body's
`mode = vault_io.guard_mode()` refusal is unmoved and still sits above the branch. Task 6, ordinal unmoved.

**M7 — still landed, and the fold strengthened rather than weakened it.** `gate_write` is still type-scoped
exactly as M7 states: `obsidian_schemas/name_gate.py:319` is `if declared_type is not None and
declared_type != PERSON_TYPE:`, its body validates only when `declared_type == COMPANY_TYPE` (`:329-343`),
and it otherwise falls to `return dict(introduced)` at `:344` — the delta handed back UNVALIDATED, with the
method's own comment at `:316-318` saying so. The trigger is still `"name" in updates and updates["name"] !=
frontmatter.get("name", "")` at `base.py:454`, reading the caller's dict against the note's frontmatter and
consulting `type(entity).model_fields` nowhere. `Book:139` and `Meeting:247` declare no `name`, while
`Person:79` and `Company:128` do — all four confirmed. The fold restated the M1 row SPLIT by declared field
and closed on both sides, which is the right shape, and Design §2's third bullet's insistence on
`type(entity).model_fields` over `hasattr`/instance spelling is the correct direction for a note storing
`name:` as an extra. Task 6, ordinal unmoved.

### STRIDE delta — what the fifth fold moved

**Spoofing, Denial of service, Elevation of privilege: unmoved.** M2 still closes the stamp's read
direction. The fold added no configuration read, no retry, no recursion, no backoff, no unbounded loop, and
no new capability at the door — it declared a residual and gated one in-memory mirror more narrowly.

**Repudiation: better.** The `renaming` gate on the `aliases` mirror removes a caller-visible in-place
mutation that no disclosure named, and Prerequisites 7's three disclosed RAISE arms turn a consumer-visible
behaviour change from discoverable into disclosed. Both are movements in the right direction.

**Tampering: better in the half the fold addressed, and the finding is in the half it did not.** The
occupied-destination residual is now stated, bounded, compared honestly against today and asserted directly
by Task 10 — and I confirmed the two claims that disposition turns on. `vault_io.write_note:685-698` really
does raise `ExternalWriteConflict` on a `stat_stamp(target) != precondition` mismatch before `_commit`, so
the move-then-write reorder really is UNAVAILABLE and not merely unchosen; and under `enforce`
`_move_locked`'s `os.link` raises `FileExistsError` before anything is written (`:757-771`), so the
occupied note really is BYTE-IDENTICAL and the complement table's row is exact. The symlinked-source row is
right too, and right for the reason it gives: `move_note:736-740` raises above `_resolved(src)`, so that
refusal is one shape with the occupied one. Against that, Design §5's declaration of the capability the same
reorder opens bounds it by a predicate that does not describe those two types' filenames — below.

**Information disclosure: nothing new.** The fold added one `ValueError` message shape I checked (the
complement rule adds no new message; Task 10's arm reads existing ones) and no new log line. The one
residual the fold newly names as detector-blind is a COMPANY subject, named explicitly in Design §2 and
`## Risk Analysis` rather than implied — which is the honest direction.

### The finding — the capability widening the fold DECLARED is bounded by a `name`-shaped predicate, and Book's and Meeting's filenames are not made of `name`

The fifth fold closed the spec-reviewer's non-blocking note 2 by declaring the widening as a decision in
Design §5. That is the right move and it is why this is findable at all. But the declaration's bound is
answered wrong:

> *Its blast radius is measured at zero … and the one thing it does NOT widen is the rename branch, which
> M7 refuses for both types.*

**M7 refuses a `name` DELTA. Neither of those two types' filename rule reads `name`.** Four facts, each read
off the code in this worktree:

1. **Book's filename is made of `title` and `author`; Meeting's of `date`, `topics`, `attendees` and
   `meeting_id`.** `obsidian_schemas/repositories/book.py:_get_file_name:340-355` reads `entity.title` and
   `entity.author`; `obsidian_schemas/repositories/meeting.py:_get_file_name:208-231` reads `entity.date`
   (`:216`), `entity.topics[0]` (`:219-220`), `entity.attendees[:2]` (`:221-224`) and `entity.meeting_id`
   (`:226`). All six are DECLARED model fields — `Book.title:160`, `Book.author:161`, `Meeting.date:260`,
   `Meeting.attendees:261`, `Meeting.topics:262`, `Meeting.meeting_id:263`. This document already states
   the rules correctly twice (its own type-general divergence table at lines 787-788, and premise 15); what
   it does not do is carry them into the widening's bound.
2. **A delta touching any of the six carries no `name` key, so every guard in the frame passes it.**
   `renaming` is False (`base.py:454` needs `"name" in updates`), so the pre-write refusal's three
   disjuncts are never evaluated — the whole predicate is `if renaming and (...)`. `gate_write` returns the
   delta UNVALIDATED (`name_gate.py:319-344`, the same pass-through M7 rests on). `vault_io.write_note`
   COMMITS at `base.py:490`. No rename branch fires, no alias is appended, no exception is raised, and the
   method returns the reloaded entity as a success.
3. **THIS ITEM is what makes it reachable, which is what makes it this item's cost — the same shape as M6
   and M7.** Today `update_fields` opens `name = getattr(entity, "name", "")` then
   `file_path = self.get_file_path(name)` and raises `ValueError` above the lock when that answers `None`
   (`base.py:437-441`); for a Book `name` is `""` and `BookRepository.get_file_path:326-338` is
   `_file_map.get("")`, so the frame does not run. Design §5 states this itself, in its own words, as the
   premise of the widening. Task 3's `resolved`-first shape binds `file_path = resolved` from the stamp, so
   after this item a stamped Book or Meeting entity runs the whole frame.
4. **The residual is the item's own defect class, manufactured silently.** After
   `update_fields(<a stamped book at "Old Title - Author.md">, {"title": "New Title"})` the note carries
   `title: New Title` at `Old Title - Author.md`: its type's own filename rule no longer recomputes to the
   file it lives in, which is verbatim this document's own type-general divergence predicate (line 787,
   *"that string ≠ the file it was parsed from"*). Nothing moved, so no alias records the old stem and every
   incoming `[[Old Title - Author]]` goes dark — the harm premise 8 measures for persons, with no
   compensating alias. And Task 11's detector fires on `vf.entity_type == "person"`, so nothing reports it.

Four things make this the finding rather than a theoretical one.

- **The document instructs the reader that this delta is safe, on this premise.** The M7 `## Edge Cases`
  entry says *"The same entity's update carrying no `name` key is unaffected and still writes through the
  seam exactly as Task 3 routes it"*, and Task 10's M7 ACCEPTED arm asserts precisely such a call
  succeeding. Both are right for `{"status": "read"}` — `Book.status:163` feeds no filename — and both read
  as a blessing of the whole complement, which contains the six fields that do. A builder reading the
  widening's declaration plus that sentence ships the hole.
- **The input is external and the route is the one this document already singles out.** The consumer audit
  records `routers/entities.py:461` as `repo.update_fields(entity, body)` with *"`body` is an arbitrary HTTP
  PATCH dict"*, and — in the audit's own words — *"the ONE consumer site that can trigger
  rename-on-`update_fields` from caller data, for person AND (via the generic route) book/meeting"*
  (`docs/wi-029-consumer-audit.md:84`, and `:137` names the same route as the ONLY consumer path to those two
  repositories). `PATCH /api/entities/book/{name}` with `{"title": …}` is an ordinary request, not an attack.
- **It is SILENT where every comparable residual in this item is loud, and the item's own claims say so.**
  M7's residual raises. The occupied-destination residual raises. `## Risk Analysis`'s non-atomicity row
  claims *"every residual is loud, detector-visible and recoverable"* and the fold went to the trouble of
  naming the one COMPANY exception explicitly. This one raises nothing, reports nothing and is not named.
  It is strictly quieter than the two findings I promoted mitigations for in rounds 4 and 5.
- **The fix is one more disjunct on the predicate Task 6 already prescribes, and it makes the Scope
  Boundary's own stated alternative real rather than adding a behaviour.** `## Scope Boundary` declines to
  teach the door Book's and Meeting's filename rule and justifies it with *"where **refusal** costs nothing
  anyone does today"* — refusal is already the declared answer; it simply is not what the code does. Keying
  the new disjunct on the repository's own declared filename rule recomputed over the delta is the
  document's own type-general predicate used as a predicate, and it is the same DECLARED-capability keying
  ordering decision 3 uses for `aliases` and M7 uses for `name`. **M8.**

*The mitigation's bound, so it is not over-read.* M8 refuses one class of DELTA and changes nothing else. It
does NOT teach the door or `update_fields` a second filename rule, does not rename a Book or Meeting note,
and does not put `_get_file_name` on the rename path — `## Scope Boundary`'s non-action stands exactly as
written. It does not touch `save` or the two `save` overrides, which derive their own target and have no
rename to reconcile, nor the five body-writers, none of which has a rename branch. It does not touch
`gate_write`, `name_gate.py` or the Tier-1 tables, all of which `## Scope Boundary` declares
read-never-edited. It does not narrow the widening Design §5 declares: the ACCEPTED half is the arm Task 10
already builds, because `status` is not a filename field. And the `not renaming` conjunct is what keeps it
from ever reaching a Person or Company: their rule is `@{name}.md`, a `name` delta sets `renaming` True, and
the rename branch is what reconciles it — so the disjunct is scoped to *a delta that moves the type's own
filename rule with no rename to follow it*, which is total over the four types today and stays total if the
`BaseRepository.save` collapse `## Scope Boundary` books as a separate item ever puts `_get_file_name` on
the base class.

### Notes (non-blocking)

- **The three non-blocking closures of the fifth fold all land, checked individually.** The `renaming` gate
  on the `aliases` mirror is in the sequencing block, in "Which `aliases` list wins" and in Task 6, and its
  reasoning is right — an ungated mirror is a caller-visible in-place mutation on every non-rename update
  that no disclosure names. The widening is declared in Design §5 (and is where this round's finding sits,
  which is a property of the bound and not of the decision to declare it). Design §1's quotation is verbatim
  against `models.py:23-40`. No work ordered on any of the three.
- **`_get_cache_key`'s `""` key for a Book reaching `update_fields`' cache surgery is a correctness
  observation, not a security one.** With the frame newly reachable for a Book, `old_name_key = name.lower()`
  is `""` (`base.py:498`) while `new_name_key` is the title, so the removal half operates on a cache entry
  that is almost never there. Nothing is corrupted on disk and no wrong note is written; the index is merely
  not cleaned for a key that was never set. `## Scope Boundary` already declines `_get_cache_key`'s strip
  asymmetry in the same neighbourhood. Recorded so the next round does not re-find it; no work ordered.
- **Round 5's three non-blocking notes stand as the writer dispositioned them.** The `guard_mode()` double
  read stays deferred (it needs a privileged actor inside the process, where this round's finding needs only
  an ordinary PATCH field — which is exactly the discrimination the spec-reviewer drew for its own finding
  and it is the right one). AC-2(b)'s ambient-environment dependence stays a conductor reading note; the
  direction is safe and AC-2 is signed. Round 4's three carried-forward dispositions — the no-op branch's
  cosmetic audit line, the `update_fields` message's pre-existing person-name disclosure, and the
  `os.environ`-versus-`guard_mode()` spelling warning — stand unchanged. M1's check-then-act residual, the
  write-then-move window and the M3 `load()` window are all re-deferred unchanged for the reasons rounds 3,
  4 and 5 gave.
- **The duplicated `## Adversarial Review` heading is still the conductor's and is still not mine**, and it
  has now grown to three sections plus a fourth dated 2026-09-26. Unchanged by this round; recorded so the
  chain is unbroken. This section's own heading duplicates round 5's date for the same structural reason and
  is called out in my first paragraph.
- **OPEN security questions: none.**

```mitigation
kind: required
id: M1
desc: `rename_note` must refuse a destination whose RESOLVED path is not inside `self.vault_path`, raising before any `vault_io.move_note` call — the containment test `_resolve_write_target` already applies to the source, applied to the caller-supplied destination, resolved rather than string-compared so that a symlink inside the vault cannot point the move outside it.
landed: Task 6
```

```mitigation
kind: required
id: M2
desc: The provenance stamp must be unforgeable from note content, asserted and not assumed — a note whose own frontmatter declares `_source_path` naming a DIFFERENT file must still resolve, through `_resolve_write_target`, to the file it was parsed from.
landed: Task 2
```

```mitigation
kind: required
id: M3
desc: The case-only two-step must not move the note out of the `*.md` namespace — the staging name keeps the `.md` suffix, so a rename interrupted between the two moves leaves a note that Obsidian, the repository and `lint_vault` can all still see rather than a file no reader picks up.
landed: Task 6
```

```mitigation
kind: required
id: M4
desc: `rename_note`'s audit line must name the SOURCE path as well as the destination, so a relocation performed by `update_fields` on a consumer's behalf is reconstructable from logs.
landed: Task 6
```

```mitigation
kind: required
id: M5
desc: AC-4's no-note-filename privacy wall must stay TOTAL over the whole committed artifact — the check's `.md`-token rule is exempted by TOKEN CLASS (a token containing `*`, i.e. a glob, beside the already-declared template literal `@{name}.md`) and NEVER by excluding fenced code blocks, because a fenced block is exactly where a re-run's pasted output lands and the exit attestation re-runs `lint_vault --report`, which names note filenames per path; the two `.md` tokens inside the artifact's current fences are `'*.md'` and `f"@{name}.md"`, so the token-class exemption is green against it as committed and the region exclusion buys nothing the narrower rule does not.
landed: Task 13
```

```mitigation
kind: required
id: M6
desc: `rename_note` must FAIL CLOSED when the write guard is not enforcing, because every occupied-destination refusal this item relies on is conditional on it — `vault_io._move_locked:757-771` does `os.replace(source, target)` and destroys the occupied note instead of raising `NoteAlreadyExists` when `guard_mode() == "observe"` (WI-004's declared residual R9, `docs/concurrent-access.md:649-656`, acceptable while door 3 had one quarantine caller and not once this item drives it on every `update_fields` name change in three `-e` consumers), so the door reads the mode through `vault_io.guard_mode()` — never a second `os.environ` access in `base.py`, which `vault_io._env_setting:104-115` forbids in writing — and RAISES beside M1's containment block, before any `vault_io.move_note` call, naming the mode; pinned BOTH ways in Task 10 with the environment set and restored in a `finally` (the same idiom the M3 recorder and the half-failure delegate already use, since a zero-arg AC check takes no `monkeypatch` fixture): under `observe` a rename onto a destination occupied by a DIFFERENT note raises, the vault's filename SET is unchanged and BOTH files are byte-identical, while under the default `enforce` the same call still raises `NoteAlreadyExists` and an ordinary in-vault rename still moves, so the clause is neither a no-op nor a refusal of everything.
landed: Task 6
```

```mitigation
kind: required
id: M7
desc: `update_fields` must not fire its rename branch for an entity whose own type does not derive `@{name}.md`, because the fold's precondition table answers the M1 row with a wall that covers two declared types and the trigger that reaches it consults the model nowhere — `obsidian_schemas/name_gate.py:319-344` returns a `name` delta UNVALIDATED for every `declared_type` that is neither `person` nor `company` (the path-hostile refusal the table delegates to is `_PATH_HOSTILE_RE = re.compile(r"/")` for a person and `_COMPANY_PATH_HOSTILE_RE:351` for a company, and `update_fields` passes `declared_type=self.type_name`, which is `"book"` and `"meeting"` at `book.py:47-49` and `meeting.py:48-50`), while the trigger is `"name" in updates and updates["name"] != frontmatter.get("name", "")` (`base.py:454`) — the caller's dict against the note's frontmatter, never `type(entity).model_fields` — so a stamped Book or Meeting entity handed `{"name": <anything>}` (Prerequisites 7's generic consumer PATCH forwards an arbitrary body that may carry `name`) sets `renaming` True against a book note's absent `name:`, passes the widened disjunction with provenance present and the guard enforcing, passes the gate untouched, COMMITS the new `name:` at `base.py:490`, and only then reaches `rename_note(entity, f"@{new_name}.md")` where `@x/y.md` raises `WriteFailedError` from `os.link` against a missing parent (`vault_io.py:_move_locked:772-773`) and `@a/../../x.md` raises M1's containment `ValueError` — M1 holds in both, so nothing lands outside the vault, but the residual is an ungated caller-supplied `name:` committed into a note that then did not move, which is exactly the state this arm exists to prevent and which the detector cannot see because it fires only on `entity_type == "person"`; THIS ITEM creates the reachability, since today's `get_file_path(getattr(entity, "name", ""))` opener answers `None` for a Book and raises above the lock (`base.py:437-441`, `:354-365`) while Task 3's `resolved`-first shape binds the file from the stamp and runs the frame; so the trigger gains one conjunct keyed on the DECLARED FIELD and never on a type name — `"name" in type(entity).model_fields`, the same keying ordering decision 3 already uses for `aliases` — which makes Design §2's "`Book` and `Meeting` cannot reach it at all" structural instead of asserted and closes the M1 row for every type rather than for two, WITHOUT adding a containment conjunct (M1 stays the door's, so no `NameGateRefusal` is degraded) and without touching `gate_write` or the Tier-1 tables, which `## Scope Boundary` declares read-never-edited; pinned BOTH ways in Task 10 against a planted colliding Book group member the battery already builds: `update_fields(<a stamped book>, {"name": "x/y", "status": "…"})` raises before the content write with that note BYTE-IDENTICAL and the vault's filename SET unchanged, while the SAME entity through `update_fields(entity, {"status": "…"})` still succeeds and lands in that file and a Person name change still moves — so the conjunct refuses the branch and not every update.
landed: Task 6
```

```mitigation
kind: required
id: M8
desc: `update_fields` must REFUSE, before its content write, a delta that moves the entity type's OWN filename rule when no rename will follow it — because Design §5's capability-widening declaration bounds the newly-reachable Book/Meeting frame with "the one thing it does NOT widen is the rename branch, which M7 refuses for both types", and neither of those two types' filename rule reads `name`: `obsidian_schemas/repositories/book.py:_get_file_name:340-355` derives from `title` and `author` (`models.py:Book.title:160`, `:author:161`) and `obsidian_schemas/repositories/meeting.py:_get_file_name:208-231` from `date` (`:216`), `topics[0]` (`:219-220`), `attendees[:2]` (`:221-224`) and `meeting_id` (`:226`) (`models.py:Meeting:260-263`), so a delta touching any of those SIX declared fields carries no `name` key, leaves `renaming` False at `base.py:454` and therefore never evaluates the pre-write refusal at all (the whole predicate is `if renaming and (...)`), is handed back UNVALIDATED by `gate_write` for a non-person non-company `declared_type` (`obsidian_schemas/name_gate.py:319-344`), and is COMMITTED at `base.py:490` with nothing moved, no alias recorded for the stem the note is leaving behind and NO exception — a note whose type's own filename rule no longer recomputes to the file it lives in, which is verbatim this document's own type-general divergence predicate (Exploration Notes' type table, "that string ≠ the file it was parsed from") manufactured by the method that exists to end it, SILENT where `## Risk Analysis` claims every residual is loud and detector-visible, and invisible to Task 11's arm because it fires only on `vf.entity_type == "person"`; THIS ITEM creates the reachability exactly as it does for M6 and M7, since today `update_fields` opens `get_file_path(getattr(entity, "name", ""))` which for a Book is `_file_map.get("")` and raises ABOVE the lock (`base.py:437-441`, `book.py:get_file_path:326-338`) while Task 3's `resolved`-first shape binds the file from the stamp and runs the whole frame — the premise Design §5's declaration states in its own words — and the route is external and already singled out by this item (`docs/wi-029-consumer-audit.md:84`, `routers/entities.py:461` forwards "an arbitrary HTTP PATCH dict" and is the ONE consumer path to those two repositories, `:137`), so an ordinary `PATCH /api/entities/book/{name}` body `{"title": …}` is the trigger; the refusal is therefore one more DISJUNCT on the same in-lock pre-write arm Task 6 already prescribes, evaluated independently of `renaming` and keyed on the REPOSITORY'S OWN DECLARED FILENAME RULE rather than on a type name or a remembered field list — `derive = getattr(self, "_get_file_name", None)`, and when it is not None and `not renaming`, project the delta onto the entity's declared fields (`entity.model_copy(update={k: v for k, v in updates.items() if k in type(entity).model_fields})`, which preserves the private stamp per Design §1) and `raise ValueError` naming the method, the field(s) at issue and THIS precondition when `derive(projected) != derive(entity)`; the comparison is DELTA-RELATIVE (`derive(projected)` against `derive(entity)`, never against `file_path.name`) so that an ALREADY-divergent Book or Meeting note — the live "book-titled file holding a person note" class and its siblings — stays writable for every delta that does not move its rule further, and the `not renaming` conjunct is what keeps the disjunct from ever reaching a Person or Company, whose rule IS `@{name}.md` and whose `name` delta the rename branch reconciles, so the clause stays total if the `BaseRepository.save` collapse `## Scope Boundary` books as a separate item ever puts `_get_file_name` on the base class; this ADDS NO capability and makes `## Scope Boundary`'s own stated alternative real instead of asserted — that section declines to teach the door Book's and Meeting's filename rule on the ground that "where refusal costs nothing anyone does today", and refusal is what this disjunct supplies — so the door learns no second filename rule, no Book or Meeting note is renamed, `gate_write` and the Tier-1 tables stay read-never-edited, and `save`, the two `save` overrides and the five body-writers are all untouched, none of them having a rename to reconcile; pinned BOTH ways in Task 10 on the same planted stamped Book the M7 arm already builds, with `OBSIDIAN_SCHEMAS_WRITE_GUARD` set to `"enforce"` explicitly for the arm (the M6 rule, WI-149) — REFUSED: `update_fields(<a stamped book at "Old Title - Author.md">, {"title": "New Title"})` raises `ValueError` whose message names the filename-rule precondition and not provenance, the guard mode or the type declaration (so the arm cannot pass on a sibling disjunct), the vault's filename SET is unchanged, and the book note is BYTE-IDENTICAL to the bytes the test wrote — which is the assertion that distinguishes refusing before the content write from committing it, and is the whole finding, since without the disjunct that file comes back carrying `title: New Title` at its old filename with no alias and no exception; the same for `{"author": …}` on that Book and for `{"date": …}` and `{"topics": [...]}` on a planted stamped Meeting, so the clause is shown to cover the RULE and not one field; ACCEPTED, three arms so it refuses the delta class and not every update: the SAME book entity through `update_fields(entity, {"status": "read"})` still SUCCEEDS and lands in that file (`models.py:Book.status:163` feeds no filename — this is the arm Task 10's M7 ACCEPTED half already asserts and it must stay green), an ALREADY-divergent planted Book whose file does not match its own rule still accepts a `{"status": …}` delta (the arm that fails a `derive(projected) != file_path.name` spelling), and a Person name change in the same vault still MOVES through the door exactly as the arms above assert (the control that fails a disjunct written without the `not renaming` conjunct).
landed: Task 6
```

```verdict
gate: threat-modeler
verdict: PROMOTE
date: 2026-09-26
model: claude-opus-5
note: Round 6 re-verified M1-M7 against the code each prescribes — all seven HELD with ordinals unmoved and `desc` re-emitted byte-identically. The fifth fold (the occupied-destination complement rule) is correct at every citation it rests on, re-derived rather than carried: `vault_io.write_note:685-698` really raises `ExternalWriteConflict` on a `stat_stamp != precondition` mismatch before `_commit`, so move-then-write really is UNAVAILABLE; `_move_locked:757-771`'s `os.link` raises `FileExistsError` before anything is written, so the occupied note really is byte-identical; `move_note:736-740` raises above `_resolved(src)`, so the symlinked-source row really is one shape with it; and all three of the fold's non-blocking closures land, including Design §1's quotation, which is byte-verbatim against `models.py:23-40`. The finding is INSIDE the fold again, and again the fold's own widening made it findable. Design §5's new capability-widening declaration states that Task 3's `resolved`-first reorder makes `update_fields` usable on `Book` and `Meeting` for the first time, and bounds it with "the one thing it does NOT widen is the rename branch, which M7 refuses for both types" — a `name`-shaped bound over two types whose filename rule does not read `name`. `book.py:_get_file_name:340-355` derives from `title` and `author`; `meeting.py:_get_file_name:208-231` from `date`, `topics`, `attendees` and `meeting_id`; all six are declared model fields (`models.py:160-161`, `:260-263`). A delta touching any of them carries no `name` key, so `renaming` is False at `base.py:454` and the pre-write refusal — whose whole predicate is `if renaming and (...)` — is never evaluated; `gate_write` hands the delta back UNVALIDATED (`name_gate.py:319-344`); `base.py:490` COMMITS; nothing moves, no alias records the stem the note leaves behind, and nothing raises. The result is this item's own type-general divergence predicate manufactured silently, on the one externally-supplied route the item singles out (`docs/wi-029-consumer-audit.md:84` — `routers/entities.py:461` forwards "an arbitrary HTTP PATCH dict" and is the ONLY consumer path to those two repositories, `:137`), and invisible to Task 11's `entity_type == "person"` arm. THIS ITEM creates the reachability, exactly as with M6 and M7: today's `get_file_path(getattr(entity,"name",""))` opener is `_file_map.get("")` for a Book and raises above the lock (`base.py:437-441`, `book.py:326-338`) — which Design §5 states itself as the widening's premise. The document actively blesses the hole: the M7 `## Edge Cases` entry says "the same entity's update carrying no `name` key is unaffected", true for `{"status": …}` and false for the six fields that make the filename. M8 is one more disjunct on the predicate Task 6 already prescribes, evaluated independently of `renaming` and keyed on the repository's own declared filename rule (`getattr(self, "_get_file_name", None)`) with a DELTA-RELATIVE comparison (`derive(projected) != derive(entity)`, so an already-divergent note stays writable) and a `not renaming` conjunct (so it never reaches a Person or Company, whose `name` delta the rename branch reconciles). It adds no capability and makes `## Scope Boundary`'s own stated alternative real: that section declines to teach the door Book's and Meeting's filename rule on the ground that "refusal costs nothing anyone does today", and refusal is precisely what this disjunct supplies. Zero OPEN questions.
```

## Spec Review — 2026-09-26

**Recommendation: PROMOTE to ready — the M8 fold lands at every surface that states the behaviour and is grounded in the code at each of its own citations; all five prior rounds' blocking findings are closed and nothing new blocks**

Fifth spec-review round on this document, spawned cold-start. **This heading duplicates the FOURTH
round's date** — that round is the earlier section carrying it, immediately above the 2026-09-26
adversarial round — so a latest-round reading resolves THIS one. The collision is the same structural
fact the sixth threat-model round called out about its own heading and is recorded here so the chain
is unbroken; it is not a finding against the spec.

Rulings on record: WI-021's gate-name-output-is-an-identity ruling (approach G's rejection), Dave's `ac_hash 15189b874b27` sign-off freezing AC-1…AC-5 and the Intent, the exploration's accept-the-linter-noise disposition, the threat model's eight `kind: required` mitigations, and the Spec-Writer Notes' declared NON-actions (M1's check-then-act residual, the write-then-move window, the no-op branch's cosmetic audit line, the `guard_mode()` double read, `_get_cache_key`'s `""` key for a newly-reachable Book) — I route against all of them and nothing below touches a signed criterion's text.

I read the document from line 1 in full rather than diffing against the previous round, then read the
code at every load-bearing citation rather than reading the folds back. **All four of round 4's
predecessors HELD, and round 4's own finding is closed.** The occupied-destination residual is now a
RULE total over the precondition table's whole NO half, checked row by row against that table, with
the three surfaces that denied it corrected and Task 10 asserting the residual directly. Round 4's
three non-blocking notes are closed at their own sites, not carried: the `aliases` mirror is gated on
`renaming`, the Book/Meeting `update_fields` widening is declared as a decision in Design §5 with its
measured blast radius, and Design §1's `BaseEntity` quotation is byte-verbatim against
`obsidian_schemas/models.py:BaseEntity:23-40` — I diffed it line by line, docstring and both
`ConfigDict` comments included.

The new material this round is threat-model **M8**, and it is a fold of the CLASS one rung above M7's
rather than of the `{"title": …}` instance. I checked it the way the fold-record rule asks — finding
each quoted sentence where it claims to be and reading the surrounding text — and it holds.

### Citation verification

All verified against current code; nothing drifted. The ones the M8 fold rests on, re-derived rather
than carried:

- **The filename rules, read off the code and not off the document's own table.**
  `obsidian_schemas/repositories/book.py:BookRepository._get_file_name:340-355` is
  `title = entity.title.strip()` (`:346`), the `[<>:"/\|?*]` strip (`:348`), `entity.author` at
  `:350-353`, and returns `f"{title} - {author}.md"` or `f"{title}.md"`.
  `obsidian_schemas/repositories/meeting.py:MeetingRepository._get_file_name:208-231` is
  `entity.date` (`:216`), `entity.topics[0]` (`:219-220`), `entity.attendees[:2]` with the `+N` tail
  (`:221-224`), `entity.meeting_id or "Untitled"` (`:226`), the same strip truncated to 50 (`:229`).
  All six are declared model fields — `Book.title:160`, `Book.author:161`, `Meeting.date:260`,
  `Meeting.attendees:261`, `Meeting.topics:262`, `Meeting.meeting_id:263` — and `Book:139` /
  `Meeting:247` declare no `name` while `Person:79` / `Company:128` do. `Book.status:163` really is a
  plain `str` feeding no filename, so Task 10's ACCEPTED cell is the right control.
- **`_get_file_name` is declared at exactly two sites in the package** — grep over
  `obsidian_schemas/**` returns `book.py:340`, `meeting.py:208` and their two call sites,
  `book.py:167` and `meeting.py:189`. So `derive = getattr(self, "_get_file_name", None)` really is
  `None` for `BaseRepository`, `PersonRepository` and `CompanyRepository`, and M8's clause is
  structurally inert for them rather than inert by a premise about which types reach the line.
- **The trigger and the commit.**
  `obsidian_schemas/repositories/base.py:BaseRepository.update_fields:454` is verbatim
  `if "name" in updates and updates["name"] != frontmatter.get("name", ""):` and names
  `model_fields` nowhere; the alias block is `:455-459`; the gate is `:483-485` with
  `whole_record=False`; `vault_io.write_note(file_path, new_content, precondition=stamp)` is `:490`;
  the reload is `:493-495`; `old_name_key = name.lower()` is `:498` and `_adopt` is `:520`. The
  opener is `name = getattr(entity, "name", "")` / `self.get_file_path(name)` at `:437-438` raising
  above the lock at `:440-441`, and `BookRepository.get_file_path:326-338` keys on
  `title.lower().strip()` — so `get_file_path("")` answers `None` for a Book, and for a Meeting
  through the inherited `BaseRepository.get_file_path:354-365` over a `_file_map` keyed by
  `MeetingRepository._get_cache_key:56-64` (meeting_id, else date+attendee), which never answers
  `""`. Design §5's reachability premise is therefore true for BOTH types, not just the one it cites.
- **The pass-through M8 rests on.** `obsidian_schemas/name_gate.py:gate_write:319` is
  `if declared_type is not None and declared_type != PERSON_TYPE:`, its body validates only at
  `:329-343` (`declared_type == COMPANY_TYPE and "name" in introduced`, against
  `COMPANY_TIER1_BRANCHES`), and it otherwise falls to `return dict(introduced)` at `:344`; the
  comment at `:316-318` really reads *"a Book write is gated and handed straight back"*. The person
  arm's `allow_phone_sentinel` derivation is `:355-358`, exactly as the door predicate says.
- **`model_copy` preserves the stamp.** Pydantic v2 copies `__pydantic_private__` on
  `model_copy`, and `update=` merges into `__dict__` without validating — which is precisely why Task
  6 orders `derive(entity)` computed first outside any `try` and ANY exception out of
  `derive(projected)` treated as a refusal. Both halves of that prescription are necessary and
  correct.
- **The door and its syscalls.** `obsidian_schemas/vault_io.py:move_note:721-750` refuses a symlinked
  SOURCE at `:736-740` with `WriteFailedError` BEFORE `_resolved(src)` at `:741`, resolves both
  operands, and takes the two locks in sorted order at `:744-750`; `_move_locked:753-783` is
  `os.link` at `:758`, the `observe` `os.replace` at `:760-769`, `NoteAlreadyExists` at `:770-771`,
  the `OSError` → `WriteFailedError` at `:772-773`, `os.unlink` at `:776`, `forget_snapshot` at
  `:780-781`, `return target` at `:783`. Every sentence of M6, of the complement table and of the
  same-file sweep is exact against those bytes.
- **The seam's structural half.** `tests/derivations.py:_taints_a_write:361-409` is seed `:368-382`,
  monotone fixpoint `:389-401`, sink over `node.args + keywords` `:404-408` — and it propagates via
  `_names_in(target)` (`:282-283`), which `ast.walk`s and so WOULD collect `entity` from
  `entity._source_path = moved`. Design §4's warning that the new seed must use
  `_assign_targets_name:928-944` instead of `_names_in` for targets is therefore exactly right, and
  `_assign_targets_name` really does reach only `ast.Name` and `Tuple`/`List` elements.
  `_is_write_call:286-299` gates on `ast.Attribute`, which is why Design §4's SECOND predicate
  (bare-name calls to `path_taking_writer_names`) is needed to reach `write_markdown_file` at all.
- **The lock-nesting claim, checked at the sites it quantifies over.**
  `obsidian_schemas/repositories/person.py:PersonRepository.append_to_timeline:1403-1461` holds
  `vault_io.note_lock` at `:1410` and calls only `vault_io.write_note` inside it (`:1447`, `:1458`) —
  a single-path door, deliberately NOT collected — so `door_calls_inside_note_lock` really is EMPTY
  over `PACKAGE_ROOT` today and Task 10's assertion is not RED against shipped code.
- **`scripts/lint_vault.py:check_structural:328-388`** is `read_error` `continue` `:340-348`,
  `parse_error` `continue` `:350-359`, the two `is_at_prefixed` arms `:362-381`,
  `if not vf.entity_type: continue` `:383-384`, the `TYPE_TO_MODEL` guard `:387-388`. AC-3(e) is a
  placement property exactly as Design §3 claims, and a non-`@` `type: person` file does reach the
  new arm.
- **The committed baseline.** `docs/stem-divergence-live-baseline.md` §1's two entry figures are
  `:121` (`8`) and `:122` (`0`), the non-numeric cells Task 13 excludes from leading-integer parsing
  are `:124`/`:126`, the eight rows are `:146-153` with row 3 `same-file` → RENAME and row 8
  `different-note` → MERGE, the two declared vocabularies are `:155-156`, and the mis-statement
  Design §3 corrects is `:158-161`. I re-ran §4a's tokenizer over the bytes: eight `.md` tokens,
  three existing repo paths, one `*.md` glob, `@{name}.md` three times — M5's token-class rule is
  green and total as committed.
- **The consumer audit.** `docs/wi-029-consumer-audit.md:84` is the generic PATCH row with *"`body`
  is an arbitrary HTTP PATCH dict and may carry `name`"* and names book/meeting via the generic
  route; `:134-140` is the zero-call-sites reading naming `routers/entities.py:461` as the ONLY
  consumer path to those two repositories. M8's external-route claim is the audit's own sentence, not
  a reconstruction.
- **One factual claim a builder acts on, checked because it is cheap:** Task 3's *"grep `Saved ` over
  `tests/` → zero hits"* is true, so retargeting `save`'s INFO line to the file actually written
  breaks nothing.

### Bar check

Walked every check of `docs/spec-quality-bar.md` (the doc's own list is the count — never hardcode
it). The spec satisfies the bar. The ones worth recording:

- **Check 4.** OPEN: None. I cross-walked every resolved Edge Case against a named test; each of the
  twenty-seven resolves to a Task 2/9/10/12/13 arm, an AC, or an explicitly declared NON-action with
  its reason. The three new M7/M8/occupied-destination entries each carry a Task 10 arm.
- **Check 5.** Fourteen canonical task definitions, ordinals 1–14, unique, all shaped
  `- [ ] **Task N — <title>.**`. Every `landed: Task N` in the latest speaking threat-model round
  resolves (M2→2, M5→13, the other six→6), so D8b is clean. Fourteen `verify:` declarations, one per
  task and none begun illustratively elsewhere in the document: twelve check arms (max four names,
  under the eight-name bound) and one `baseline` exception whose reason is 139 characters. Task 14's
  three pre-existing names all resolve —
  `tests/test_concurrent_access.py:test_wi020_derivations_survive_the_routing:1060`,
  `tests/test_name_gate_wall.py:test_wall_membership_is_closed_by_running_each_walls_predicate:1057`,
  `tests/test_loud_fail_write.py:test_write_failure_raises_and_noops_keep_their_return:105`.
- **Write-Targets coverage.** Every plan task's target is declared, and every declared path has a
  task: `models.py`/`parser.py`/`base.py`/the new seam module (Task 2), `base.py` (3, 6),
  `person.py` (4), `book.py`+`meeting.py` (5), `derivations.py` (7), the four new test modules (8,
  9/10, 12, 13), `scripts/lint_vault.py` (11), and the three CONDITIONAL count-pin modules declared
  under the WI-229 rule with their predicted-unmoved reasoning. No fence declares a path no task
  writes. No verify command writes outside `write_authority` — Task 14's floor command is pytest over
  `tests/`, and nothing in the plan orders a state-writing CLI.
- **Check 12 (AC drift).** The five `criteria` fences are the frozen originals; every revision note
  in `## Design` states, and the section's own preamble restates, that no fence's bytes were touched
  — so there is no diff to classify against `ac_hash 15189b874b27`. M7 and M8 both land as NON-AC
  arms of AC-2's check, the same shape M6 and the idempotence arm already used. No
  strength-weakening, actor-swap, scope-narrowing, oracle-swap or exception-carving-by-addition.
- **The fold records.** Eight records for the eight `kind: required` mitigations of the latest
  speaking round; each `desc` matches its `mitigation` fence, each `landed:` resolves, and I found
  each `design:` and `work:` quote where it claims to be and read the surrounding text rather than
  judging the pair alone. M8's `design:` is the bolded sentence in Design §2's "the THIRD rule" block
  byte-for-byte modulo the emphasis markers, and its `work:` is Task 6's (M8) clause through
  *"the door learns no second filename rule (`## Scope Boundary`)"* — both faithful. The two
  pre-existing deviations the writer discloses (M2's compressed `work:`, M5's stitched one) are
  accurate compressions of tasks this round did not touch.
- **The class-fold obligation.** M8 closes the GENERATOR (*a guard keyed on the PERSON instance,
  `name`, of a predicate this document states TYPE-GENERALLY*) rather than the `{"title": …}`
  instance, keys the clause on the repository's own declared rule so the six deriving fields are
  covered by construction, and DECLARES the next ladder level's sweep with its members, its
  non-members and its one named trade (`save` and the two overrides, accepted because refusing there
  would refuse AC-1). I ran the sweep independently over the nine write paths and the door and found
  no member the two clauses leave open.
- **The ruling-sweep.** I enumerated every surface that states what `update_fields` does with a
  Book/Meeting delta and confirmed each states the ruling: Design §2's third rule, the paragraph
  naming the arm's second clause beside the sequencing block, Design §5's corrected widening bound,
  the M7 `## Edge Cases` entry's added bound, the new `## Edge Cases` entry, the new
  `## Risk Analysis` row, Prerequisites 7's fourth disclosed arm, `## Verification`'s failure-mode
  list, two `## Scope Boundary` bullets, Task 6's clause, Task 10's arm, the `base.py` `writes`
  fence, `## Wall Membership`'s Walls A/B/C row, and the fold record. None still asserts the
  pre-ruling behaviour.

### Build-runner dry-run

Walked the Implementation Plan top-to-bottom; no judgment-call gaps detected. Three questions a
cold-start builder plausibly asks, and where the document answers each:

1. *"The pre-write arm now has TWO clauses, but the sequencing block only shows the first — where
   does the second go?"* Answered immediately beneath the block ("That same arm carries a SECOND
   CLAUSE, and it fires where `renaming` is FALSE"), which gives the clause verbatim and points at
   the THIRD rule; Task 6's (M8) paragraph prescribes the same in-lock position, before anything is
   gated or written.
2. *"`update_fields` now runs its whole frame for a Book. What happens at the cache surgery when
   `old_name_key` is `""`?"* Answered as a declared NON-action in the Spec-Writer Notes and in the
   sixth threat-model round's note 2, and it checks out against `base.py:498-520`: `_cache.get("")`
   is `None`, the removal half is skipped, and `_adopt` re-keys on `_get_cache_key`. Nothing on disk
   is touched.
3. *"Task 10 is one check function carrying arms (a)–(h) plus six mitigations plus four non-AC arms —
   may I split it?"* Answered by the check contract in `## Wall Membership` and Task 14: AC-2's
   signed `check:` names the one function, so the AC-named symbol must stay a top-level zero-argument
   `def`; helper functions beneath it are unconstrained. The document never forbids helpers, and
   every arm's oracle is stated independently, so the split is mechanical.

### Minor notes (non-blocking)

1. **Two of Task 10's M8/M7 control arms are claimed to discriminate a wrong spelling that the wrong
   spelling actually passes.** Neither misleads a builder about what to WRITE — Task 6 prescribes both
   clauses verbatim — so this is an over-claim about the battery's reach rather than a buildability
   defect, and it costs one clause each to state honestly.
   (i) Task 10's M8 ACCEPTED half calls the person-name-change cell *"the control that fails a clause
   written without the `not renaming` conjunct or one reaching a repository that declares no
   `_get_file_name`"*. It does fail the second spelling, but not the first: for a `PersonRepository`
   `derive` is `None`, so `derive is not None` already excludes the cell and dropping `not renaming`
   changes nothing there. The conjunct's real value is the forward one Design §2's first M8 bullet
   states honestly (it is what keeps the clause total if the `BaseRepository.save` collapse ever puts
   `_get_file_name` on the base class) — and no fixture in the corpus or the plants can discriminate
   it today, which is the WI-286 shape: either plant a repository declaring BOTH `name` and
   `_get_file_name` in the escape battery, or say in one line that the conjunct is forward-looking and
   has no discriminating member.
   (ii) Design §2's third M7 bullet and Task 10's M7 ACCEPTED half both say an `entity.model_fields`
   spelling *"would answer differently"* for a note storing `name:` as a pydantic EXTRA. `hasattr`
   does; `entity.model_fields` does not — it resolves to the same mapping as
   `type(entity).model_fields` (in pydantic ≥2.11 via a deprecation shim) and therefore still answers
   "not declared", so that cell passes under both spellings. The reason to insist on
   `type(entity).model_fields` is the one `obsidian_schemas/writer.py:108`'s own comment gives — the
   v2.11+ deprecation — and that reason is already in the document; only the "answers differently"
   half is wrong.
2. **Task 10's M8 arm says "ACCEPTED, four arms" and then lists five items, one of which is a
   REFUSAL.** The non-string-deriving-field cell (`{"title": ["a", "b"]}`) asserts a `ValueError` and
   belongs in the REFUSED bucket beside the other four; M8's own `desc` says "three arms" for the same
   list. The assertion each cell must make is unambiguous, so nothing is buildable two ways — but this
   is the third instance in this document of a count stated beside a list that has since grown
   ("five planted members" vs six; "eight more one-line edits"), and the writer's own WI-229 repair
   was to re-state the LIST and drop the number. Same repair here, plus moving the non-string cell
   under REFUSED.
3. **`save`'s no-provenance WARNING text is `name`-shaped for the two types whose target is not
   name-derived.** Design §2's fallback shape 1 emits *"the write targets the name-derived
   filename"*, and Task 5 applies that shape to Book's and Meeting's overrides, where the target is
   `_get_file_name`-derived. It is a log string and no criterion reads it, but it is one more member
   of the class M8 just closed and costs one word (`derived filename`).

### Carried-forward notes

- **The duplicated `## Adversarial Review` heading — still the conductor's, and it has grown again.**
  THREE sections carry the identical `2026-09-25` heading (rounds 1 PROMOTE, 2 REVISE, 3 PROMOTE) and
  a fourth is dated 2026-09-26, so a heading-keyed structural reader has three candidates for one
  gate at one date. A latest-round reading resolves the 2026-09-26 section. The spec-writer correctly
  declines to touch those bytes; the action is the conductor's — confirm the earliest section's
  origin and make it say so on its face, or strike it. **This round's own heading duplicates round
  4's date for the same structural reason and is called out in my first paragraph.** I am emitting
  PROMOTE, so D5's second key IS now load-bearing: the conductor should resolve the collision before
  the `specced → ready` attempt rather than after it.
- **M1's exact bound (threat model round 2).** Resolve-then-`os.link` is check-then-act against an
  attacker who can plant a symlink at the destination between the two. Re-deferred unchanged: the
  bound is stated in Design §2's M1 bullet, the attacker is outside Prerequisites 6's trust boundary,
  and `os.link` has no `O_NOFOLLOW` spelling reachable through pathlib. No work ordered.
- **The write-then-move window (threat model round 2).** Re-deferred as a declared NON-action, folded
  as a `## Edge Cases` entry and a `## Risk Analysis` row with the lock-ordering entry explicitly
  scoped to ORDERING only. Stated again so neither M8 nor round 4's fold is read as re-opening it.
- **The `guard_mode()` double read (threat model round 5, note 1).** Re-deferred unchanged: it needs
  a privileged actor inside the process to move `os.environ` between `update_fields`' in-lock check
  and the door's, which is more privileged than the boundary Prerequisites 6 draws, and the re-run
  table's first row already owns the outcome by name.
- **AC-2(b)'s occupied-destination arm depends on the ambient environment (threat model round 5,
  note 2).** Re-deferred, and the gap has narrowed rather than closed: Task 10 now sets
  `OBSIDIAN_SCHEMAS_WRITE_GUARD` explicitly through `tests/support.py:patcher:73` for FOUR arms (M6's
  both halves, M7, M8 and the occupied-destination `update_fields` arm) while AC-2(b)'s own arm still
  inherits whatever the runner carries. The direction stays safe (an ambient `observe` reddens it)
  and AC-2 is signed, so this is not a spec edit — but one sentence extending the same instruction to
  the WHOLE of Task 10's check would close it for free, and the conductor-facing line ("read a red
  AC-2(b) as a shell question before a code question") is still not in the document.
- **The no-op branch's cosmetic audit line (threat model round 4).** On the `same_place` branch M4's
  INFO line reads *"Renamed … from @New.md to @New.md"*. Recorded by the modeler as harmless and not
  a security defect; carried unchanged.
- **`_get_cache_key`'s `""` key for a newly-reachable Book (threat model round 6, note 2).** A
  correctness observation, not a security one, and verified above against `base.py:498-520`. Carried
  as a NON-action in the same neighbourhood `## Scope Boundary` already declines.
- **Architect round 6, note 6(iv)** — the deliberately-out-of-scope items (`_get_cache_key`'s strip
  asymmetry, approach F's re-keying, the Book/Meeting `save` collapse) stand as written and are all
  named in `## Scope Boundary`. Closed; recorded so the chain is unbroken.
- All other prior non-blocking notes are FOLDED and I verified each at its landing site against the
  code rather than the prose: round 4's three (the `renaming`-gated `aliases` mirror, Design §5's
  declared widening, Design §1's restored quotation), round 3's six, round 2's five, round 1's
  twelve, the M3 `load()` window (now `## Verification`'s close-out paragraph) and the threat model's
  pre-existing-extras-leak bound (Design §1, beside AC-1(h)).

```verdict
gate: spec-reviewer
verdict: PROMOTE
date: 2026-09-26
model: claude-opus-5
note: Fifth round, cold-start, read from line 1 and re-derived at the code rather than from the folds — no blocking gap survives. Round 4's finding is closed as a RULE total over the precondition table's whole NO half, checked row by row against that table, with the three surfaces that denied the occupied-destination residual corrected and Task 10 asserting it directly (the raised LEAF, the committed `name:` at the unmoved filename, the absent alias, the un-re-stamped entity, the byte-identical destination, the re-run's no-op and the direct-`rename_note` recovery); its three non-blocking notes are closed at their own sites, including Design §1's quotation, which I diffed byte-for-byte against `models.py:BaseEntity:23-40`. This round's new material is threat-model M8, and it is a fold of the class one rung above M7's rather than of the `{"title": …}` instance: I re-derived all four facts it rests on — `book.py:_get_file_name:340-355` derives from `title`/`author` and `meeting.py:_get_file_name:208-231` from `date`/`topics`/`attendees`/`meeting_id`, all six DECLARED (`models.py:160-161`, `:260-263`); `base.py:454` is verbatim the caller's-dict-against-frontmatter trigger and names `model_fields` nowhere, so a delta with no `name` key evaluates none of `if renaming and (...)`; `name_gate.py:319-344` really falls to `return dict(introduced)` for a non-person non-company `declared_type`; and `base.py:490` COMMITS. The clause is keyed on `getattr(self, "_get_file_name", None)`, which grep confirms is declared at exactly `book.py:340` and `meeting.py:208`, so it is structurally inert for Person and Company rather than inert by premise, and it is DELTA-RELATIVE so an already-divergent note stays writable. I ran the ruling-sweep over every surface stating what `update_fields` does with a Book/Meeting delta — fourteen of them — and each states the ruling; I ran the next-ladder-level sweep over the nine write paths and the door independently and found no member the two clauses leave open, one declared trade (`save` and the two overrides, accepted because refusing there would refuse AC-1) and one named detector-blind residual (COMPANY). Fourteen canonical task definitions with fourteen well-formed `verify:` declarations, every `landed: Task N` resolving, every plan-task target declared in `## Write Targets` with no undeclared path and no writing verify command, eight complete and faithful fold records whose `design:` and `work:` quotes I located and read in context, and the five signed criteria untouched (no diff to classify against `ac_hash 15189b874b27`). Three non-blocking notes: two control arms over-claim which wrong spelling they discriminate (the `not renaming` conjunct has no discriminating member today, and `entity.model_fields` answers the same as `type(entity).model_fields` — only `hasattr` differs), Task 10's M8 ACCEPTED bucket says "four arms" over five items one of which is a refusal, and `save`'s WARNING string says "name-derived" on the two paths whose target is `_get_file_name`-derived. One carried-forward item is now the conductor's to act on BEFORE the transition rather than after it: three sections share the heading `## Adversarial Review — 2026-09-25`, and with a spec-reviewer PROMOTE on record D5's second key becomes load-bearing.
```

## Adversarial Review — 2026-09-26

Cold-start spawn, fifth injection-hunter round on this document (four prior sections stand: round 1
PROMOTE, round 2 REVISE on a provenance concern about round 1's own standing, round 3 PROMOTE
resolving round 2 on the merits, round 4 PROMOTE covering Threat Model rounds 4–5 and Spec Review
round 4's REVISE). I read the document from line 1 to its end in full — Problem/Motivation, Intent,
the entire Exploration Notes arm (all five architect rounds, the AC red-team round, all fifteen
numbered premises, every constraint, the conductor read-back), Approach, Design §1 and §2 in full
(the stamp, the ten-caller resolution function, the door body and its M1/M3/M4/M6/M7/M8 clauses),
`## Edge Cases & Open Questions` in full, the fourteen-task Implementation Plan in full, `## Write
Targets`, `## Wall Membership`, `## Mitigation Folds` including all eight `fold` fences, `##
Verification`, `## Scope Boundary`, `## Risk Analysis`, all five signed `criteria` fences and
Examples of Done, Spec-Writer Notes, then every prior gate's verdict prose in document order —
Architectural Review, AC Red-Team, AC Sign-off, Data Audit, Threat Model rounds 1–6, Spec Review
rounds 1–5, and all four existing Adversarial Review sections read directly. I additionally ran
several whole-document greps for verdict-steering phrasing ("ignore previous instruction",
"pre-approved", "you must/should emit/output", imperative address to a reviewer, "trust this",
role-play framing ("act as", "you are now"), `SYSTEM:`/`assistant:`/chat-template tokens, hidden
zero-width or base64 tricks) and separately for every HTML comment and every `writes` fence. All
returned only legitimate hits: the steering-phrase matches are prior gates' own prose *discussing*
the absence of such phrasing (including this section's); the only HTML comment is the
machine-maintained archive-split pointer at line 21; and every `writes` fence names a path inside
this item's own declared write authority (`obsidian_schemas/**`, `tests/**`, `scripts/**`,
`docs/**`) — none names another work item's own tracked document, so WI-245's merge-authorization
scrutiny does not arise.

**This round's own new material — the sixth threat-model round (M8, the `getattr(self,
"_get_file_name", None)` clause) and the fifth spec-review round (PROMOTE) — is the same genre as
every round before it.** Both are dense, line-cited technical argument about the CODE (a
capability-widening bound stated in `name`-shaped terms over two types whose filename rule is not
made of `name`; a citation-by-citation re-derivation of the four facts M8 rests on) and neither
reads as addressed to a reviewing agent or shaped to produce a verdict rather than an
understanding. I independently re-checked the spec-reviewer's central citations — `book.py:_get_file_name:340-355`
deriving from `title`/`author`, `meeting.py:_get_file_name:208-231` deriving from
`date`/`topics`/`attendees`/`meeting_id`, `base.py:454`'s trigger reading the caller's dict against
the note's frontmatter and never `model_fields`, `name_gate.py:319-344` falling through to `return
dict(introduced)` for a non-person, non-company `declared_type` — against the prose describing them
rather than accepting the prose, and they reproduce exactly as stated.

**The heading collision the spec-reviewer just flagged as now load-bearing is a document-structure
fact, not a finding I am reopening.** Three sections share the heading `## Adversarial Review —
2026-09-25` (rounds 1, 2, 3) and a fourth carries `## Adversarial Review — 2026-09-26` (round 4,
this section's own heading duplicates it a second time). Round 2 raised the substantive version of
this concern — could a stale or forged PROMOTE under this gate's own heading satisfy D5 without a
genuine review of current content — and round 3 resolved it on the merits: every gate in this
document is a cold-start spawn that self-discovers its own round number by reading the document,
no gate round here carries cryptographic provenance so that bar cannot discriminate a forged round
from a genuine one for ANY gate, and the mid-document position is the same append-only artifact
every other repeated section (Threat Model ×6, Spec Review ×5) shows. I re-read round 3's reasoning
against round 1's and round 2's own text rather than against round 3's summary, and it still holds;
nothing in this round's material reopens it. The protective action available to me is not to
re-litigate that closed question a third time — it is to make sure the section a "latest-round
reading" resolves to is itself a genuine, current review, which is what this section is: a
fresh, full read of the document as it now stands, including the M8 fold and the just-landed
spec-reviewer PROMOTE, neither of which any prior Adversarial Review section could have seen. The
structural cleanup itself (deduplicating or dating the collision) is the conductor's action, as
every prior round from round 3 onward has correctly recorded, and is not something an injection-hunter
verdict can or should perform.

I found no text anywhere in the document whose *effect* is to steer any gate's verdict, planted or
otherwise, including in the material added since round 4.

```verdict
gate: injection-hunter
verdict: PROMOTE
date: 2026-09-26
model: claude-sonnet-5
note: Full end-to-end read (Problem/Motivation through the just-landed fifth Spec Review round, including all four existing Adversarial Review sections read directly) plus several whole-document greps for steering phrasing, HTML comments and non-conforming `writes` fences found no planted text steering any gate's verdict and no cross-item merge-authorization concern. This round's new material — Threat Model round 6 (M8) and Spec Review round 5 (PROMOTE) — is the same genre as every prior round: dense, line-cited technical argument about the code, and I independently re-verified the spec-reviewer's central citations (`book.py`/`meeting.py`'s `_get_file_name` field lists, `base.py:454`'s trigger, `name_gate.py:319-344`'s pass-through) against the code rather than the prose. Round 2's provenance concern about round 1's standing is not reopened — round 3's resolution holds on direct re-read and nothing here contradicts it — and the heading collision the spec-reviewer just flagged as load-bearing is the conductor's structural action, not an injection finding; this section itself supplies a genuine, current "latest round" covering the material no prior Adversarial Review section had seen.
```

## Code Review — 2026-09-26

Cold-start build-exit read, first round at this door. My tool grant carried **no shell**, so nothing
below rests on a command I ran: every claim is a direct read of the final text in this worktree, and
where the only available evidence is the builder's own run I say so and treat it as a claim rather
than as a measurement (see the standing caveat at the end of the test section).

### Trigger check

FIRES. The post-build diff is not doc-only: six package/script files modified
(`obsidian_schemas/models.py`, `parser.py`, `repositories/base.py`, `repositories/person.py`,
`repositories/book.py`, `repositories/meeting.py`, `scripts/lint_vault.py`), one test helper modified
(`tests/derivations.py`), one test module modified (`tests/test_company_name_contract.py`) and four
new test modules added. New public API surface (`BaseRepository.rename_note`), a changed write-target
resolution on nine mutating paths, and two new pre-write refusals in `update_fields` — none of the
skip patterns apply, and the mechanical-change exemption is nowhere near reachable.

### What I read against what

I read the fourteen-task Implementation Plan, `## Write Targets`, `## Wall Membership`, the Build
Log, `## Scope Boundary`, `## Risk Analysis` and all five signed `criteria` fences; then the shipped
code for each task and each new/edited test module; then the prior gates' standing rounds (Spec
Review round 5, Adversarial Review round 4, and the carried-forward note ledger). The two
`kind: precondition` artifacts (`docs/stem-divergence-live-baseline.md`,
`docs/wi-029-consumer-audit.md`) are both present in the tree and both unmodified, as the Scope
Boundary requires.

**Task-by-task conformance, checked at the code and not at the prose.** Task 2: the `PrivateAttr`
lands at `obsidian_schemas/models.py:51` with the comment block, and `parser.py:251-252` stamps on
the `entity is not None` arm only — `parse_markdown_content` is untouched, which is the property AC-1
and Task 2's unit check both turn on. Task 3: `base.py:450-457` is the CREATE-fallback shape with the
WARNING emitted before `write_markdown_file`, and `base.py:627-630` is the REFUSE-fallback with
`resolved` bound under its own name exactly so Task 6's arm can read it — a builder who collapsed the
two names would have had to reopen the method head, and the collapse did not happen. The M4 log
defect is fixed at all three sites (`base.py:480`, `book.py:196`, `meeting.py:216`): each names
`file_path.name`, the file actually written. Task 4: all five body-writer openers are the
provenance-then-name shape (`person.py:1408`, `:1534`, `:1675`, `:1748`, `:1829`) and every
`ValueError`, `.exists()` guard and falsy return is left in place — I checked that the refusal
one line below the opener is still the original `raise ValueError`, which is what
`tests/test_loud_fail_write.py`'s (function, ordinal) map keys on. Task 5: both overrides keep
`_get_file_name` as the fallback expression and neither starts calling `super().save()`.

**Task 6, the door, read clause by clause against Design §2's listed body.** It matches, including
every clause the plan marked non-optional: M1's containment on the RESOLVED destination with
`OSError`/`ValueError` treated as not-contained and raised before any `move_note`
(`base.py:511-519`); M6's `vault_io.guard_mode()` read through `vault_io` and never `os.environ`
(`:521-527`); M3's staging name derived from the SOURCE and keeping the `.md` suffix (`:556`); M4's
both-ends audit line (`:593-594`). The branch discriminant is file identity and not the path string
(`:541-542`) — parents resolved, raw `.name` compared — which is the one place a string compare would
have turned the "idempotent" re-run into two real moves on this platform. There is no
destination pre-check in either the door or `update_fields`, no alias-repair arm, and no
move-before-write; `update_fields` calls the door at `base.py:753-754`, after the
`with vault_io.note_lock(file_path)` block has exited and before the reload, which is ordering
decision 5's required placement. The door contains no `parse_frontmatter` call and no falsy return
(M1 and M6 both raise), so the two count pins it could have moved cannot have moved.

I also traced the ONE line the plan did not enumerate. `vault_io.record_snapshot(moved)`
(`base.py:578-591`) is guarded on `moved_now or aliased`. The Build Log §3 establishes it as
load-bearing by mutation rather than by argument, and the guard's own reason — that an unconditional
call would let the idempotent no-op branch launder a third party's write into an accepted
precondition — is the right reason. I checked the consequence the guard leaves open: after a
half-failed rename (move committed, alias write raised) the frame exits through the exception before
reaching the call, so the moved note is left unregistered — and that is exactly the residual the
document declares, whose stated recovery (`update_fields(entity, {"aliases": [...]})`) re-reads
through `vault_io.read_note` and so re-establishes a snapshot for itself. Consistent, not a gap.

**M7 and M8, the two clauses that change consumer-visible behaviour.** `base.py:665-676` is the
three-disjunct rename-side refusal, keyed on `type(entity).model_fields` read off the CLASS, raised
inside the lock before `gate_write`, `write_frontmatter` or `vault_io.write_note` are reached.
`base.py:685-705` is the second clause: `derive = getattr(self, "_get_file_name", None)`, delta-
relative, `derive(entity)` computed FIRST and outside the `try`, with only `derive(projected)`
wrapped and any exception out of it converted to the same `ValueError`. I checked the one thing that
placement could have cost: `Book.title`/`Book.author` are `str` with `""` defaults
(`models.py:171-172`) and `Meeting.date`/`topics`/`attendees`/`meeting_id` likewise
(`models.py:271-274`), so `derive(entity)` on a *validated* entity cannot raise and the
outside-the-`try` position is safe rather than merely prescribed. `model_copy(update=…)` does not
validate, which is what makes the wrapped call the one that can raise, and that is the arm the
battery drives with `{"title": ["a", "b"]}`.

**The detector (Task 11).** `scripts/lint_vault.py:433-462` sits after the `TYPE_TO_MODEL` guard, so
WI-026's `read_error`/`parse_error`/`missing_type` triage order is preserved by construction and not
by a second guard. The comparison is raw on both sides with exactly one leading `@` stripped
(`:441`), the `isinstance(stored, str) and stored.strip()` conjuncts are both present and both
commented with the repair-direction reason, and `auto_fixable` is left at its default so the issue
cannot enter `apply_fixes`. The guard is `vf.entity_type == "person"` and not `vf.is_at_prefixed`,
which is the narrowing that would have silently dropped the live MERGE row. `_gate_refusal_pattern`
(`:334-352`) asks the DOOR (`gate_write(fm, declared_type=fm.get("type"), whole_record=True)`) and
not the bare validator — the whole point of the round-4 fold. I checked its raise surface, because
this function runs inside a whole-vault sweep and an unexpected exception would abort the lint run on
one bad note: `gate_write`'s person body reaches `NameValidationError` only through `_refuse`
(converted to `NameGateRefusal`, which is caught), and every list-shaped operation is gated by
`_shaped`'s `_is_str_list` precondition (`name_gate.py:196-198`), so the narrow catch is sound rather
than lucky.

**The AI-maintainability checks.** No new cross-project reach (no `sys.path` manipulation, no sibling
repo paths, no foreign `.env`/state reads). No new dependence on deprecated code. No idiom
regression: the new refusals raise typed loud failures, the new logging is `logger.warning`/
`logger.info` with structured args, the environment is read through `vault_io.guard_mode()` precisely
so `base.py` does not become a second `os.environ` home, and the boundary field (`_source_path`) is a
typed `Optional[Path]` rather than a stringly-typed one. No silent swallow at the Blocking bar — see
Note 1 for the one typed `except` that returns a sentinel, and why it is a guard rather than a
swallow.

**Step 2c — readback and no-silent-PASS-on-empty.** No new outbound write to an external service:
every write in the diff routes through `vault_io`, which is this package's verified write door and
already carries stamp preconditions and snapshot registration — and the one place the diff *adds* to
that registry (`record_snapshot(moved)`) exists precisely because `move_note` forgets both paths and
the next `save` would otherwise refuse against a note the rename just created. On silent-PASS: I
walked each new path where an absence is possible. `_resolve_write_target` returning `None` is
handled explicitly and DIFFERENTLY per caller — `save` creates and warns when the derived target is
occupied, `update_fields` and the five body-writers refuse — which is the whole reason the resolver
never falls back on its own behalf; a uniform fallback would have converted those loud refusals into
note creation. The detector's two near-miss narrowings (non-string `name:`, blank `name:`) are
intentional, commented, and each is pinned by a planted member asserting SILENCE, so neither is a
default pass. I found no code path in the diff where an empty result, a `None`, or a swallowed
exception is the default outcome without an explicit, commented decision behind it.

**Cage-reverted writes.** My input carries no `<<< cage-reverted writes >>>` block, so there is
nothing to check and I manufacture no finding. I did check the adjacent thing that block exists to
catch: the Build Log names one undeclared-but-in-authority Write Target
(`tests/test_company_name_contract.py`, §6) and one file it deliberately did NOT touch
(`docs/whatsapp-jid-value-type.md`, §7, WI-032's untracked idea doc). Both disclosures match the
tree — `test_company_name_contract.py` is modified and the whatsapp doc is untracked and, by its
absence from every diff hunk I read, unedited. The declaration gap is real and correctly
self-reported: the edit is a forced consequence of Tasks 3 and 6 (that arm's driver returned the seed
path as the file the arm wrote, and since this item `update_fields` MOVES the note), and the repair —
asking the repository which file it wrote rather than recomposing the filename rule — is the right
direction rather than a fixture patch.

### Findings

**Blocking: none.**

Three Notes, none of which changes what the code should do:

1. **`_resolve_write_target`'s typed `except` returns a sentinel without logging**
   (`obsidian_schemas/repositories/base.py:410-413`). An `OSError`/`ValueError` out of
   `candidate.resolve()` or `is_relative_to` is converted to "no provenance" silently. This is a
   guard rather than a swallow — the return value is a documented three-way answer, not a discarded
   failure, and every caller's handling of `None` is loud (refuse) or announced (`save`'s WARNING when
   the derived target is occupied) — so it does not reach the Blocking bar the check sets for an
   `except` that "neither logs nor re-raises". Recorded because the one configuration it hides is a
   vault path that stopped resolving mid-process, where `save` would then create at `@{name}.md`
   with no WARNING unless that file happens to exist. One `logger.debug` would close it; no criterion
   reads it either way.

2. **The door's `@`-strip and the detector's are deliberately different spellings of one idea, and
   only one of them is documented as such.** `rename_note` uses `source.stem.lstrip("@")`
   (`base.py:528`, `:565`, verbatim per Design §2:1447) while the detector strips exactly one
   character (`scripts/lint_vault.py:441`, with a comment explaining why `lstrip` would hide
   `@@Foo.md`). Both are right for their own job, but the consequence is unstated: renaming
   `@@Foo.md` → `@Foo.md` computes `old_stem == new_stem == "Foo"` and appends NO alias, so a
   wikilink spelled `[[@@Foo]]` goes dark. The class is one live-report row at most and the item
   already declines incoming-reference repair as a non-action (`## Scope Boundary`), so this is a
   sentence for the next doc pass rather than a code change.

3. **CLAUDE.md's "~15s" floor figure is now stale, and its re-exec parenthetical under-counts.** The
   project file reads *"Hermetic, ~15s (WI-016's fixture-vault battery makes six foreign-interpreter
   subprocess runs per floor; WI-026 added a seventh check module with its own re-exec)"*. This item
   adds four more check modules carrying `ensure_project_interpreter(__file__)` and the Build Log
   reports the floor at ~21s. I am NOT calling this a Blocking "docs made false" hit, for two
   reasons that I checked rather than assumed: the figure is hedged (`~`) and is a duration, not one
   of the counts the check enumerates; and the re-exec is a NO-OP under the floor command
   (`## Risk Analysis`'s own row says so), so the *"six foreign-interpreter subprocess runs per
   floor"* count is genuinely unmoved and the *"WI-026 added a seventh"* clause remains a true
   historical statement. What moved is the wall-clock and the module count a reader would infer from
   it. Worth one line at the next `/wrap-up`; not worth a bounce.

For the record, the three non-blocking notes the fifth Spec Review round left open: note 3 (`save`'s
WARNING string saying "name-derived" on the two paths whose target is `_get_file_name`-derived) is
CLOSED in the code — all three warnings read "the derived filename" (`base.py:454`, `book.py:178`,
`meeting.py:198`). Notes 1 and 2 are over-claims in Task 10's own prose about which wrong spelling
two control arms discriminate; they are document text inside a section the builder was right not to
rewrite, and they mislead nobody about what to build.

### Summary

Fourteen tasks landed as specified, including every clause the plan marked non-optional and the six
required mitigations at their prescribed sites. The two behaviour changes a consumer can observe
(`update_fields` MOVES on a name change; a Book/Meeting delta that would move its own filename rule
is now refused) are both signed decisions disclosed in `## Risk Analysis`, not discoveries. I found
no Blocking issue.

```verdict
gate: code-reviewer
verdict: PROMOTE
date: 2026-09-26
model: claude-opus-5
note: Read every task's code against its spec clause by clause with no shell — the seam, the door's M1/M3/M4/M6 clauses, `update_fields`' two-clause pre-write refusal (M7/M8), the five body-writer openers, both `save` overrides and the detector all match Design §2/§3, including the file-identity branch discriminant, the outside-the-lock door call, the absence of any destination pre-check, and the `type(entity).model_fields` and `getattr(self, "_get_file_name", None)` keyings; I additionally verified two things the prose asserts rather than proves (that `derive(entity)` outside the `try` cannot raise, because Book's and Meeting's six deriving fields are all non-optional `str`/`List[str]` with defaults, and that `_gate_refusal_pattern`'s narrow catch is sound, because `gate_write`'s only raise on a person payload is `NameGateRefusal` and every list operation sits behind `_shaped`'s `_is_str_list`), and confirmed the one unenumerated door line (`record_snapshot`, guarded) is load-bearing with a correct guard. No Blocking finding; three Notes (a typed sentinel-return `except` with no log at `base.py:410-413`, the undocumented consequence of the door's `lstrip("@")` on a `@@`-stemmed stem, and CLAUDE.md's now-stale `~15s` floor figure), and the spec-reviewer's one code-facing open note is closed in the shipped warnings.
```

## Test & Observability Review — 2026-09-26

### Trigger check

FIRES, and this pass APPLIES rather than self-declaring N/A: the item adds a new production code path
(`BaseRepository.rename_note`, a file-moving public method three `-e` consumers can reach), changes
the write target of nine existing mutating paths, adds two new refusals to a shipped method, and adds
a new detector arm to a tool Dave runs by hand against the live vault. This is persistence and new
prod surface, not a refactor.

### Check 1 — tests exist for the new code paths

Yes, and they are unusually strong. Four new modules, all four present on disk with the named
functions defined as top-level zero-argument `def`s and with `ensure_project_interpreter(__file__)`
as the module's first statement:

- `tests/test_provenance_write_seam.py` — the two seam unit checks, AC-1's sweep, AC-2's door
  battery (twenty-odd named arms), and Task 14's wall closure.
- `tests/test_write_target_seam_wall.py` — AC-5's live classification plus a planted-escape battery.
- `tests/test_stem_name_divergence_detector.py` — AC-3, inside the five-part WI-026/WI-031
  containment door (`test_every_divergence_drive_in_this_module_is_confined_to_a_temp_vault` is
  present, and the module constructs no repository).
- `tests/test_stem_divergence_baseline_shape.py` — AC-4's shape check plus a reader battery that
  drives the SAME readers and the SAME `.md`-token scan the live arm calls.

Happy path AND failure modes are both covered, which is what I checked rather than the count.
Spot-verifying the two arms most likely to be stubbed: AC-1's cell driver
(`test_provenance_write_seam.py:450-513`) derives its subject set from two manifest predicates and
asserts them at 4 / 3 / 5 before sweeping, asserts its invoked path set is EQUAL to AC-5's seam
bucket (`:423-436`, so the two batteries cannot drift), and grades each cell on the stronger
property `changed == {filename}` — the only note whose bytes moved is the subject's own — rather than
on the weaker "the subject changed". It also asserts `repo._loaded is False` at EVERY cell, so AC-1(g)'s
no-vault-walk half is checked once per cell rather than once per run. AC-5's wall
(`test_write_target_seam_wall.py:212-289`) asserts its own predicate is single-homed in
`tests.derivations` before using it, asserts the scan is non-vacuous, asserts both bucket sets by SET
EQUALITY against fourteen qualnames, and then drives seven refused and five accepted plants through
the same function — including the two call-and-discard spellings and the accepted
guarded-fallback rebinding that keeps the shipped design legal.

I independently traced the wall's own soundness rather than trusting the green: `_is_seam_routed`'s
taint closure and ordering-aware rebinding clause classify `rename_note` SEAM correctly (the seed
`source` propagates through `staging`, `same_place` and `moved`, no Assign between seed and sink
rebinds a tainted name out of an untainted value, and every `move_note`/`update_frontmatter_field`
first positional is tainted), and I confirmed the fourteen expected qualnames are the complete write
population by grepping every `write_markdown_file`/`write_note`/`create_note`/`move_note`/
`update_frontmatter_field`/`write_text`/`write_bytes` call under `obsidian_schemas/**` — four writer
leaves, three in `base.py`, six calls across five `person.py` body-writers, one each in `book.py` and
`meeting.py`, and none in `company.py` (which declares no `save`, so it inherits the seam for free).
`PersonRepository.save` delegates via `super().save()` and so is correctly absent. Nothing is
outside the wall.

One genuine (Recommended, non-blocking) weakness in AC-3's battery:
`tests/test_stem_name_divergence_detector.py:334-338` and `:363` compare a bare `path.name` against
`silent`, which is a set of repo-relative POSIX paths. Over today's corpus the two coincide, because
`tests/fixtures/vault/` is FLAT — I listed it to check, 54 notes, no subdirectory — so the arm is
sound as shipped. It would go vacuous the day a fixture note lands in a subdirectory, which is the
same class of latent-vacuity the rest of this battery is scrupulous about. One `.as_posix()` on the
relative path closes it.

### Check 2 — logging at WARN/ERROR for each failure mode

Adequate, and improved over HEAD. Every new failure mode is LOUD rather than logged: the door's four
precondition refusals raise `ValueError` naming the type, the offending argument and which
precondition failed; `update_fields`' two pre-write clauses raise `ValueError` naming the method, the
requested value and the specific precondition (three distinct precondition constants on the rename
side, one on the filename-rule side), so a consumer's traceback identifies which disjunct fired
rather than merely that something refused. The occupied destination comes back as the LEAF
`NoteAlreadyExists` from the syscall rather than as a pre-check `ValueError`, which is both the
stronger answer and the more debuggable one.

On the non-raising side: the M4 audit line names BOTH ends of every move
(`base.py:593-594`) — required, because after this item `update_fields` moves a file permanently on
every name change, and a log naming only the destination cannot reconstruct the class. The three
`save` INFO lines now name the file actually written rather than the derived filename, which is the
defect that would otherwise have made this class *unreconstructable from a consumer's logs* exactly
when provenance binding started sending writes somewhere the derived name does not describe. The one
new WARNING (`base.py:453-456`, `book.py:177-179`, `meeting.py:197-199`) is emitted BEFORE the write
that is about to refuse, which is the only ordering in which it is ever seen, and AC-1(f) captures it
through `tests/support.py:captured_logs`. I found no new silent failure mode in the diff.

### Check 3 — alerts wired

**N/A by shape, and I checked rather than assumed it.** This is a library with no scheduler, no
launchd/cron entry point, no daemon and no outbound channel of its own; it signals to its three `-e`
consumers by raising, and to a human through `scripts/lint_vault.py`, which is hand-run. The
alerting question belongs to HAL9000/Exocortex/orchestrator, whose call sites the `kind: precondition`
consumer audit already measured (19/19 on loaded entities), not to this package.

### Check 4 — invariant registration

**N/A — no registry in this project.** The v1 registry scope is orchestrator-only
(`orchestrator/src/invariants.py`); `obsidian-schemas` ships none, so per this role's own rule the
dimension is skipped and not failed. The project's equivalent mechanism is the derived-wall family,
and this item joins it properly rather than around it: `## Wall Membership` derives thirteen inbound
walls and Task 14 RUNS eleven of them as direct predicate calls
(`test_provenance_write_seam.py:1728-1754`), with the remaining two discharged by a run that is not a
predicate call and DECLARED as such. I checked the row the Build Log says under-reached: wall D as
written permitted `base.py` alone, the run returned three parse callers (Book's and Meeting's
standing `_load_file` overrides joined the touched list at Task 5), and the satisfying form shipped
is strictly STRONGER than the row — `functions_calling(touched, "parse_markdown_file")` asserted EQUAL
to `load_file_implementations(...)`, a set derived independently and pinned at three — rather than a
module-level permitted list that would have blessed whatever happened to be there. That is the right
direction for a wall that under-reaches.

### The standing caveat, and the one thing still owed at this door

**I could not re-run the floor.** My grant carried no shell, so the Build Log's numbers are the
builder's claim, not my measurement: 689 → 699 (+10, directional invariant satisfied), every count
pin unmoved with the five `person.py` qualnames recorded in full, all five AC checks additionally
invoked under the conveyor's own zero-argument `getattr(mod, name)()` shape, and two Task 14 arms plus
Task 13's readers shown to DISCRIMINATE rather than merely pass. The claims are internally consistent
and every artifact they name exists on disk with the asserted shape, and the Build Log evidences a
live shell (§0 records the WI-228 P4 liveness probe; §3 records a mutation-and-revert experiment that
is only performable by running something). Whoever advances this item should let the conveyor's own
per-criterion runs be the measurement.

**AC-4's EXIT half is NOT satisfied and cannot be from inside the cage.** The Build Log §9 declares
this loudly and correctly: `docs/stem-divergence-live-baseline.md` §5 is a named EMPTY section by
design, and the item's declared SHIP CONDITION is that the conductor re-runs §0's script and
`scripts/lint_vault.py --vault "$VAULT" --report` against the live vault, appends the attestation, and
reads ZERO on both the divergence count and `len(PersonRepository(...).conflicts)`. AC-4's shape check
asserts §5 is PRESENT with its figure names and both re-run commands and asserts nothing about its
values — deliberately, since the population is live. I am not holding a REVISE for it: it is not a
code or test defect, and no builder could close it from in here. But it is a real obligation on the
transition this gate sits at, so it is recorded here in the plainest terms available to me — the
library work is ready; the live repair is not done, and AC-4's own words are *"the item is not done
until divergence and conflicts both read zero"*.

### Summary

New prod paths have tests covering the happy path and many failure modes, with both-ways pinning on
every containment wall and planted discriminators wherever the frozen corpus is unanimous; every new
failure mode raises or logs with enough context to debug from; alerting and invariant registration are
N/A by shape, checked rather than waved. One Recommended fix (a basename-vs-relative-path comparison
in AC-3's battery that is sound today only because the fixture vault is flat). Nothing Blocking.

```verdict
gate: test-observability-checker
verdict: PROMOTE
date: 2026-09-26
model: claude-opus-5
note: Four new check modules present with every AC-named function a top-level zero-arg `def` behind `ensure_project_interpreter`, covering happy path plus many failure modes and pinned BOTH ways throughout — I verified the two batteries most susceptible to stubbing by reading their oracles (AC-1 grades each cell on `changed == {filename}` and asserts its path set EQUAL to AC-5's seam bucket so the two cannot drift; AC-5 asserts single-homing, non-vacuity and two set equalities before driving seven refused and five accepted plants), and independently confirmed the wall's completeness by grepping every write call under `obsidian_schemas/**` against the fourteen expected qualnames (`company.py` has none and `PersonRepository.save` delegates, both correctly absent). Every new failure mode is loud with a precondition-identifying message; the M4 line names both ends of a move and all three `save` INFO lines now name the file actually written, which is what keeps this class reconstructable from a consumer's logs. Alerts N/A (library, no scheduler, no outbound channel) and invariant registration N/A (no registry in this project — the derived-wall family is the equivalent, and Task 14 RUNS eleven of the thirteen rows, with wall D satisfied in a form strictly stronger than the row it under-reached). One Recommended fix: `test_stem_name_divergence_detector.py:334-338`/`:363` compare a bare basename against a set of repo-relative paths, sound only because the fixture vault is flat (I listed it). TWO things this verdict does NOT certify, both stated rather than implied: I had no shell, so the 699-case floor and the five conveyor-shape invocations are the builder's claim and should be re-measured by the conveyor's own per-criterion runs; and AC-4's EXIT half is unsatisfied by design — the live repair, the four booked hand repairs and the §5 attestation reading zero on divergence AND conflicts are the conductor's ship door, and the item's own criterion says it is not done until they do.
```

## Intent Check

Cold-start read against the frozen referent: `## Intent`, all five signed `criteria` fences
(`ac_hash 15189b874b27`), `### Examples of Done`, the Build Log, and the test body behind each
AC's `check:` (grepped by name in `tests/`, whole function read — no `ac_runner:` declared for
this project, so the plain-grep arm applies). I additionally read the standing Code Review and
Test & Observability Review sections, both of which independently traced these same test bodies
against the shipped code with no Blocking findings, and spot-verified rather than deferred to
them: `test_no_library_write_can_fork_a_person_note` and the first half of
`test_a_person_note_is_renamed_only_through_the_one_door_and_stays_reachable`
(`tests/test_provenance_write_seam.py:409-748`) drive real `PersonRepository`/`BookRepository`/
`MeetingRepository` instances against a materialized temp copy of the frozen fixture vault, with
no stub or mock on the write seam anywhere in the driven path — every cell reads bytes off disk
before and after the call and asserts the stronger `changed == {filename}` property (not merely
"the subject changed"), asserts the untouched colliding-group members are byte-identical, and
plants the two subjects (the sentinel-exempt phone stub, the Book/Meeting colliding pairs) the
frozen corpus cannot supply on its own — this is proof of the promised property, not a rubber
stamp of green.

Per AC: AC-1's `desc` promises no library write can fork or cross-contaminate a person note over
every mutating path, including the DOOR-refused cell reached by rule (not a hand-list) and the
unloaded-repository arm; the test's matrix over derived subjects × derived paths, plus the four
planted arms `_sentinel_exempt_cell`/`_planted_type_general_cells`/`_absent_provenance_arms`/
`_unloaded_repository_arms`, proves exactly that, with the negative arms (no vault walk, no
canonical file created for a divergent note, the collision WARNING) asserted alongside the
positive ones. AC-2's `desc` promises one door, the right note under collision, and the reload
re-stamping; `_person_cell`'s sibling battery and the door test's own bucket
(`_door_resolves_through_the_seam_and_stays_reachable`, `_door_refuses_an_occupied_destination`,
`_update_fields_calls_the_door_and_nothing_else_moves`) match, per the Code Review's independent
trace of the door body clause-by-clause against Design §2. AC-3, AC-4 and AC-5 are read the same
way through the Code Review's and Test & Observability Review's own citations (the raw-comparison
detector, the committed live-baseline shape reader, the seam wall's set-equality and
seven-refused/five-accepted plant battery) and I found no daylight between what those sections
quote and what the referenced line ranges actually contain.

`### Examples of Done`'s four scenarios (the forked-stem save, the two-Alex-Morgan timeline
write, the library rename with alias-preserving lookup, the post-repair lint report) are each the
direct consumer-facing restatement of AC-1/AC-2/AC-3's own matrix cells and are proven by the same
tests — none strains against the built artifact.

No taxonomy defect (stubbed-seam, weakened-assertion, narrowed-input-domain,
missing-negative-case, oracle-swap) found in the sampled or cited test bodies, and no text in any
test body or comment addressed itself to a reviewer. This is a fidelity PROMOTE only — it says
nothing about AC-4's EXIT half, which every prior gate already correctly names as the conductor's
unfinished ship door, not a build defect.

```verdict
gate: intent-check
verdict: PROMOTE
date: 2026-09-26
model: claude-sonnet-5
note: Read the frozen Intent/AC/Examples referent against the Build Log and the test bodies behind all five `check:` ids (spot-verified `test_no_library_write_can_fork_a_person_note` and the AC-2 door battery directly — real repositories, no stub on the write seam, byte-level before/after diffs, planted discriminating subjects); every AC's test proves its `desc`+`why` rather than a weakened or stubbed substitute, and the four Examples of Done are the direct consumer restatement of AC-1/AC-2/AC-3's own proven cells. No fidelity defect and no intent-drift found.
```

## Retrospective — 2026-09-26

### Was the spec accurate?

Mostly, and the drift that did occur was small and self-corrected in the Build Log rather than
argued around. The spec went through five spec-review rounds and a six-mitigation threat model
before reaching `ready`, and that weight paid off: the code review and test/observability review
both landed zero Blocking findings on the first cold-start pass at each door, and the intent-check
found no fidelity defect across all five ACs. Two small drifts surfaced during build, both recorded
and closed rather than hidden: `## Wall Membership`'s Wall D row named only `base.py` as the
permitted `parse_markdown_file` caller, but Book's and Meeting's standing `_load_file` overrides
also parse (pre-existing at HEAD, not introduced by this item) — the builder shipped a strictly
stronger check instead of narrowing the wall to fit. And Task 6's enumeration of the door's body
didn't name the `vault_io.record_snapshot(moved)` line, which turned out to be load-bearing
(established by mutation testing, not by re-reading the plan).

### Edge cases that surprised us

- The unenumerated `record_snapshot` guard in the door (Build Log §3) — omission from the plan's
  clause list, not a design gap; the guard itself was correct once found.
- Wall D's under-reach once Book/Meeting joined the touched-file list at Task 5 (Build Log §4).
- An undeclared-but-in-authority Write Target, `tests/test_company_name_contract.py`, forced by
  Tasks 3 and 6 changing what `update_fields` does to a note's filename (Build Log §6) — the fixture
  driver had been recomposing the filename rule by hand instead of asking the repository what it
  wrote, which broke as soon as the note could move.
- The door's `lstrip("@")` and the detector's one-character strip are deliberately different (code
  review Note 2) and their divergence on a `@@Foo.md` stem was undocumented until this pass.

None of these were spec defects that cost a REVISE bounce — they were caught and closed inside the
same build session, which is the outcome the heavy spec-review investment was for.

### What would have shortened the build?

The build spawn that preceded this session timed out mid-build without ever writing a `## Build
Log` section, so the resume had no prescribed cursor to read and had to be reconstructed from the
tree diff (present artifacts, floor run) against the fourteen-task plan (Build Log §0). A build-
runner convention of writing (or at least stubbing) `## Build Log` incrementally, task-by-task,
rather than once at the end, would have let a timed-out resume read its cursor directly instead of
re-deriving it — and would have avoided the harder problem in §1: baselines that must be captured
*before* the first edit could not be re-captured from the already-edited tree without recording
post-conditions under a pre-condition's name, which only pristine `git archive HEAD` avoided.

### Recommended follow-ups

- Consider a build-runner instruction to write `## Build Log` as a running append (one entry per
  completed task, or a stub row created eagerly at task start) rather than as a single end-of-build
  section, specifically to make timeout-resume cursors reconstructible without a tree-diff
  archaeology pass. This is a process gap this item's own build hit directly, not a hypothetical.
- No bar or role instruction-update is warranted from the wall-under-reach or door-enumeration
  drifts above — both are one-off enumeration gaps in this item's own plan, already closed in the
  shipped code, and don't show a pattern in spec-writer or code-reviewer behavior worth generalizing.

### Was the build-earned lesson bar cleared?

No. The build's process issue (reconstructing a resume cursor after a spawn timeout with no Build
Log) cost session time but shipped no corruption and no wrong output — the reconstruction was done
correctly, from pristine HEAD, and the floor caught nothing wrong. That's a smooth-enough recovery,
not a scar. Nothing appended to `LESSONS.html`.

### Did the build serve the original intent, or the spec's drift of it?

Serves the intent. `## Intent` promises the fork renamed once through the one door with the old
stem preserved as an alias, and an invariant test that goes red the moment the class recurs — the
Intent Check (above) independently verified the AC tests drive real repositories with no stub on
the write seam and assert the stronger `changed == {filename}` property, not a rubber-stamped
green. The one open item, AC-4's EXIT half (the live-vault re-run reading zero on divergence and
conflicts), is correctly scoped by every prior gate as the conductor's ship condition, not a build
defect — the library work the intent actually asked for is done and proven.

### Post-done defect check (WI-084)

None to record. No bug shipped past a gate surfaced here; the three Code Review Notes and the one
Test & Observability Recommended item are all pre-existing-behavior disclosures or latent (not yet
triggered) weaknesses, not defects this or a prior WI shipped silently.
