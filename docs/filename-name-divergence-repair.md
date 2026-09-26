---
id: WI-029
title: 'Filename/name divergence repair: rename the forked stems, then pin the invariant'
project: obsidian-schemas
stage: specced
created: 2026-09-06
last_touched: 2026-09-25
stage_changed: 2026-09-25
touched_by: session
tags: []
depends_on: []
transitions: ["idea>exploring@2026-09-21@porter", "exploring>specced@2026-09-25@porter"]
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

### 1. Data model — the provenance stamp

One new declared PRIVATE attribute on the base model, and nothing else. No frontmatter field, no
schema migration, no public signature change.

`obsidian_schemas/models.py:BaseEntity:31` today is:

```python
class BaseEntity(BaseModel):
    model_config = ConfigDict(
        extra="allow",
        use_enum_values=True,
        populate_by_name=True,
    )

    type: str
    tags: List[str] = Field(default_factory=list)
```

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
structure, the seam, or a signed criterion.

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
  window is two `move_note` calls wide, it exists only on the case-only branch (one live row), and
  the alternative is trading a transient extra note for a permanent invisible one — which is the
  direction door 3's own link-then-unlink ordering already chose.
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
spelling is the case-only two-step, where `source.samefile(destination)` is the inode test and needs
the `destination.exists()` guard because `samefile` raises on a missing operand. Task 10's IDEMPOTENCE
arm plants the spelling divergence rather than waiting for the platform to supply it. **What this
deliberately does NOT do is re-spell the stamp.** `entity._source_path = moved` keeps `move_note`'s own
resolved answer rather than substituting the repository's spelling of it, because normalizing at the
one place a DECISION is read is total (it survives a relative `vault_path`, a `..` segment and a
symlinked root alike) while re-spelling only papers over the one divergence the door itself
introduces. The one visible consequence is that `get_file_path(name)` answers a resolved path for a
note the door moved, where `load()`'s entries carry the constructor's spelling: the same file either
way, and every consumer of that mapping opens it, `.exists()`es it or hands it to a `vault_io` door,
each of which resolves internally (`obsidian_schemas/vault_io.py:_resolved:234-243`).

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
| case-only branch, between its two moves | the note sits at the staging name; the source is gone; the entity was never re-stamped | with the SAME entity: `FileNotFoundError` from the door's own `source.exists()`, since the stamp names a file that no longer exists. With an entity loaded from the STAGING note: it completes the move, but appends `<stem>.rename-tmp` to `aliases`, because that is honestly the stem it moved from | a hand rename (the residual is VISIBLE by M3, and this is the branch with one live row, repaired by the conductor by hand) |
| after the move, at the alias write | moved, correctly stamped, one alias missing | safe NO-OP: `same_place`, no second move, nothing appended | `repo.update_fields(entity, {"aliases": [*entity.aliases, <the old stem>]})`, or a hand edit |
| after everything | none | safe NO-OP | nothing to recover |

The invariant that row set carries, and the one worth stating as the door's contract: **a re-run is
always SAFE — it never moves twice, never appends twice and never forks — and it repairs exactly the
residuals in which the MOVE did not happen and the cause has gone. It repairs nothing that happened
AFTER the move.** Task 10 asserts the no-op row; the first row is the ordinary AC-2 arms; the second
is `## Edge Cases`' staging-name entry.

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
                                                       vault_io.guard_mode() != "enforce"):
                                                   raise ValueError(...)   # nothing written yet
        ...                                    # gate the delta
        write the content                      vault_io.write_note(file_path, new_content,
                                                                   precondition=stamp)
                                               # the LAST WRITE inside the lock; `stamp` is from
                                               # this frame's own read (base.py:449)
        mirror what the write committed        if "aliases" in updates:
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

**`update_fields` composes `f"@{new_name}.md"` for every entity type, and that is correct rather than
an oversight of the door's own docstring** *(third spec-review round, non-blocking note 4)*. The door
takes its destination from the caller because "each type's filename rule differs (`@{name}.md`,
`_get_file_name`)", and the one in-library caller then hardcodes the `@{name}.md` rule. It is right for
every type that can reach this line: `BaseRepository`, `PersonRepository` and `CompanyRepository` all
derive `@{name}.md`, and the two types with a different rule cannot reach it at all, because the
trigger is a change to a `name` field neither `Book` nor `Meeting` declares
(`obsidian_schemas/models.py:Book`, `obsidian_schemas/models.py:Meeting:259-263`). A future caller
whose type derives its filename otherwise composes the destination with `self._get_file_name(entity)`;
the door is indifferent, which is why the rule lives in the caller.

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
whole precondition class when threat-model M6 landed, and the heading keeps its original wording so
this document's four pointers to it still resolve)*. The
method deliberately keeps a name-keyed fallback — AC-1(g)'s second half turns on it — so `resolved`
can be `None` while `get_file_path(name)` answers, and for that entity `rename_note`'s documented
behaviour is the RAISE in the invocation table's row 10. Written naively the sequence commits the new
name at `base.py:490` and only then discovers the door will not move the file, leaving a note that is
divergent, un-aliased and unmoved, with an exception reaching a caller AFTER a successful write and no
reload. So the decision is made where nothing has been written yet: **inside the lock, immediately
after `renaming` is computed from `frontmatter` and BEFORE `gate_write`, `write_frontmatter` or
`vault_io.write_note` are reached, `if renaming and (resolved is None or vault_io.guard_mode() !=
"enforce"): raise ValueError`** — naming the method, the name it was asked to change to, and WHICH
precondition failed: that a name change needs the provenance a move is resolved from, or that the
write guard is not enforcing. The frame has performed one READ at that point, so the note is
byte-identical, the caller sees the refusal instead of a half-applied rename, and the residual state
is *nothing*.

**The predicate is the door's PRECONDITION class and not a list of two, which is the whole of the
rule.** M6 arrived as a second reason the door refuses before it touches the filesystem, and answering
it with a second remembered conjunct would leave the THIRD as the next round's finding. So the class is
enumerated at source — the door's own refusal arms, read off the body above, split by whether their
cause is knowable in this frame before the write:

| the door's refusal arm | knowable before `update_fields`' write? | who refuses early |
|---|---|---|
| no provenance (`source is None`) | YES — it is `resolved`, already bound at the head of the method | this conjunct |
| a non-enforcing write guard (M6) | YES — `vault_io.guard_mode()` is a per-call environment read taking no path | this conjunct |
| an uncontained destination (M1) | YES — the destination is `f"@{new_name}.md"` and `new_name` is in `updates` | **already refused earlier, by a different wall**: the only way that filename escapes is a `new_name` carrying a path separator, and `gate_write` refuses it on the delta before any write for both types that can reach this line (`path_hostile` for a person, the wider `COMPANY_TIER1_BRANCHES` class for a company, `obsidian_schemas/name_validation.py:_COMPANY_PATH_HOSTILE_RE:351`), while `Book` and `Meeting` cannot reach it at all — they declare no `name` field. Adding a containment conjunct here would PREEMPT the gate and degrade a `NameGateRefusal` carrying its `pattern` into a bare `ValueError`, so the right answer is that the class member is already closed, not that it is unclosed |
| the source no longer exists (`FileNotFoundError`) | NO — the frame READ that file inside the lock microseconds earlier, so an absent source is a concurrent delete and not a knowable precondition | nobody; it is the door's own raise, and the write-then-move window entry in `## Edge Cases` owns it |
| `move_note`'s refusals (`NoteAlreadyExists`, symlinked source) | NO — both are filesystem state at move time | nobody, deliberately: pre-checking either here is exactly the check-then-act this document refuses elsewhere, and the syscall is the stronger answer |
| the alias write raising | NO — it happens after the move by construction | nobody; the half-failure residual is stated in the re-run table |

The rule that table carries, and the one a later clause is measured against: **`update_fields` refuses
a name change before its content write for every reason the door refuses its own PRECONDITIONS —
things knowable from this frame's arguments and environment — and for no reason that depends on
filesystem state at move time, which stays the syscall's.** A seventh refusal arm added to the door
later is placed by that sentence rather than by remembering this list.

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
stem. **`update_fields` reconciles on its own side and the door is not changed:** where the committed
`updates` carried an `aliases` key, mirror the committed value onto the entity
(`entity.aliases = frontmatter["aliases"]`) before the door call, captured inside the lock with the
rest of the rename decision. That is keyed on the KEY THIS WRITE INTRODUCED and never on a type name —
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
| `update_fields` | `obsidian_schemas/repositories/base.py:BaseRepository.update_fields:438`, `:454-459`, `:490-495` | seam at the top, binding `resolved`; a `ValueError` inside the lock when the update changes the name and the door's preconditions do not hold — `resolved is None` or `vault_io.guard_mode() != "enforce"` (M6) — raised before anything is gated or written; the alias-append block becomes the door call — placed OUTSIDE the `note_lock` block, after the write commits, before the reload — with the committed `aliases` value mirrored onto the entity where the caller supplied one |
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
   destination is CONTAINED"). The claim now covers the whole item rather than half of it.
7. **Consumers are out of reach and the contract change is disclosed.** HAL9000, Exocortex and
   orchestrator install `-e` and are outside `pipeline-runners.yaml:write_authority:34-38`. The audit
   answers: 19 of 19 consumer sites on the nine paths are on LOADED entities; 0 `auto_load=False`
   constructions; 0 reconstructions feed a write; `BookRepository.save`/`MeetingRepository.save` have
   0 consumer call sites. The one consumer-visible behaviour change is HAL9000's generic entity PATCH
   (`routers/entities.py:461`), which forwards an arbitrary body that may carry `name` and which
   today forks — after this item it MOVES the file and keeps an alias. That is in Dave's signed
   read-back (conductor read-back note 4): disclosed, not discovered.
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

- **Case:** Two callers race `update_fields` with a name change — the content write commits inside the
  lock and the door's move happens after that lock has released, so there is now a WINDOW between them.
  **Decision:** Accepted knowingly. Every interleaving is LOUD, is exactly the `stem_name_divergence`
  the new detector reports, and is recoverable by re-running the idempotent door — every one of them
  is a MOVE that did not happen, which is the residual a re-run does complete (the half-failed ALIAS
  write is the one it does not, and it has its own entry below). A concurrent write of
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

- **Case:** The rename destination is occupied by a DIFFERENT note (the live MERGE row).
  **Decision:** `move_note` refuses by syscall with `NoteAlreadyExists` and both files are
  byte-identical afterwards. The door does not merge — merging is a conductor judgement, per the
  direction table.
  **Reasoning:** AC-2(b). The refusal is the kernel's `FileExistsError` on `os.link`
  (`obsidian_schemas/vault_io.py:_move_locked:759-771`), not a check-then-act. That refusal is
  CONDITIONAL on the write guard, which is why M6 makes an enforcing guard a precondition of the door
  rather than qualifying this Decision: the entry below owns the non-enforcing case and the door never
  reaches `move_note` in it, so this sentence is true of every call that gets that far.

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
  first positional — AC-5's own rule, applied to the item's own door.

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
  twice; the detector writes nothing. One residual a re-run does NOT repair, named so "idempotent" is
  not over-read: a missing alias left by a rename whose move committed and whose alias write raised —
  the entry above states it and names the one-field recovery. A repair row whose MOVE did not happen
  is completed by the re-run exactly as this entry says.
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

- [ ] **Task 1 — Capture the pre-build baselines, before the first edit that moves them.** Run the
  floor command and record its case count; run EVERY pinned derivation named here — the list, not a
  count, is the obligation, and Task 14 re-checks exactly what this task recorded — and record their values
  (`functions_reserializing_parsed_frontmatter` = 4, `functions_parsing_then_writing - writers` =
  `{write_markdown_file}`, `non_completed_write_sites` over `PACKAGE_ROOT` = 8, over `person.py` = 8
  with its five qualnames, `base_repository_subclasses` = 4, `load_file_implementations` = 3). Write
  all of them into the Build Log. Assert nothing on the numbers; they are the left-hand side later
  tasks compare against, and a baseline nobody captured is a value no check holds.
  verify: baseline — an informational capture whose only artifact is the Build Log; no later check asserts the recorded numbers, only that the pins did not move.

- [ ] **Task 2 — Declare and set the provenance stamp, and add the resolution function.** Add
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

- [ ] **Task 3 — Route `save` and `update_fields` through the seam.** Change
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

- [ ] **Task 4 — Route the five mutating body-writers.** Replace the identical
  `file_path = self.get_file_path(person.name)` opener at
  `obsidian_schemas/repositories/person.py` `:1403`, `:1522`, `:1653`, `:1719`, `:1793` with the
  REFUSE-fallback shape. Leave every `ValueError`, every `.exists()` check, every falsy return and
  every `return False` exactly where it is — `tests/test_loud_fail_write.py` classifies those sites
  by (function, ordinal) and a new or moved falsy return is RED. Leave
  `PersonRepository._get_body_content` alone and add one comment line there naming it as the
  read-side sibling that is deliberately outside the write seam.
  verify: test_no_library_write_can_fork_a_person_note

- [ ] **Task 5 — Route Book's and Meeting's `save` overrides.** Apply the CREATE-fallback shape to
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

- [ ] **Task 6 — Ship the rename door, contained and audited, and call it from `update_fields`.** Add
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
  **IMPORT THE ALIAS WRITER AS A BARE NAME:** extend
  `obsidian_schemas/repositories/base.py:20`'s existing `from ..writer import write_markdown_file,
  write_frontmatter` with `update_frontmatter_field` and call it unqualified. Two things key on that
  spelling: AC-5's bucket (ii) enumerates BARE-NAME calls to a member of `path_taking_writer_names`
  (Design §4), and Task 10 patches `obsidian_schemas.repositories.base.update_frontmatter_field` to
  drive the half-failure residual — a `writer.update_frontmatter_field(...)` spelling moves both.
  Four clauses of that body are the threat model's required mitigations and are not optional.
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
  `@{name}.md`) and `Book`/`Meeting` cannot reach it at all, since the trigger is a change to a `name`
  field neither declares (Design §2, "`update_fields` composes `f"@{new_name}.md"` for every entity
  type"). Hand the door the caller's own
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
  `vault_io.guard_mode() != "enforce"` (M6) — naming the method, the requested new name, and WHICH
  precondition failed: that a name change needs the provenance a move is resolved from, or that the
  write guard is not enforcing. Both disjuncts, not one: a name change that reaches the door under
  `observe` fails for the same structural reason a no-provenance one does, and answering only the
  remembered conjunct leaves the next precondition as the next round's finding. Design §2's
  precondition table is the authority for which of the door's refusal arms belong in this test and
  which stay the syscall's — read it rather than extending the disjunction by guess; in particular do
  NOT add a containment conjunct for M1 here, because `gate_write` on the delta already refuses a
  `new_name` carrying a path separator before any write, for both types that can reach this line, and
  a `ValueError` raised earlier would degrade a `NameGateRefusal` carrying its `pattern`. Without this
  arm the sequence commits the new name
  at `base.py:490` and only then hits `rename_note`'s raise, leaving a divergent
  un-aliased note and an exception after a successful write; with it the frame has performed one READ
  and the note is byte-identical. Test the STORED value and not `"name" in updates`: a PATCH body
  echoing an unchanged name must still write (Design §2, "The no-provenance name change refuses BEFORE
  the write", which also carries the precondition table and records why re-stamping from
  `get_file_path` is the wrong fix). **RECONCILE THE
  ALIAS LIST ON THIS SIDE:** where the committed `updates` carried an `aliases` key, mirror the committed
  value onto the entity (`entity.aliases = frontmatter["aliases"]`) before the door call, captured inside
  the lock with the rest of the rename decision — otherwise the door's in-memory list is the parsed one
  and overwrites the caller's (Design §2, "Which `aliases` list wins"). Keyed on the key this write
  introduced, never on a type name. The alias append itself moves INTO the
  door, where its two halves are deliberately asymmetric: the FILE write through
  `writer.update_frontmatter_field` is unconditional (`aliases:` is Obsidian's own type-agnostic key)
  while the in-memory assignment stays guarded by `hasattr(entity, "aliases")`, so the door never mints
  an undeclared extra on a `Company`, `Book` or `Meeting` entity (Design §2, ordering decision 3).
  `rename_note` must contain NO falsy return and NO `parse_frontmatter` call — which is also why the
  alias reconciliation above lives in `update_fields`, where `frontmatter` is already bound, and not in
  the door, whose membership of `functions_parsing_then_writing` is pinned by set equality.
  verify: test_a_person_note_is_renamed_only_through_the_one_door_and_stays_reachable

- [ ] **Task 7 — Build the AC-5 derivation in `tests/derivations.py`.** Add `WriteTargetSite`,
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

- [ ] **Task 8 — Write AC-5's check and its planted-escape battery.** New module
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

- [ ] **Task 9 — Write AC-1's sweep.** In `tests/test_provenance_write_seam.py`, add
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

- [ ] **Task 10 — Write AC-2's door battery.** In the same module, add
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
  It then drives the four mitigations Task 6 folded
  into the door, each pinned BOTH ways so the clause cannot pass by refusing everything.
  **(M1)** `rename_note` raises `ValueError` and leaves the vault's filename set unchanged for each
  of the escape's three reachable spellings — a traversing relative name built as
  `os.path.relpath(<a path the test created OUTSIDE the temp vault>, vault)`, the absolute path of
  that same outside file, and an in-vault filename that is a SYMLINK to it (the spelling a string
  compare cannot see; assert the outside file was NOT hard-linked to, by comparing its `st_nlink`
  before and after) — while an ordinary in-vault destination and a destination inside an in-vault
  SUBDIRECTORY both still move, so the clause is not "refuse everything". Every oracle is a path the
  test itself created; nothing is matched on a prefix or a substring of the tree.
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
  verify: test_a_person_note_is_renamed_only_through_the_one_door_and_stays_reachable

- [ ] **Task 11 — Ship the detector.** Add `NOT_RENAMEABLE_MARKER`, `_gate_refusal_pattern` and the
  `stem_name_divergence` arm to `scripts/lint_vault.py:check_structural`, placed after the
  `TYPE_TO_MODEL` guard so the `read_error`/`parse_error`/`missing_type` arms keep their triage
  order. ERROR, `structural`, `auto_fixable` left at its default. Add one comment naming why this
  call reaches the phone-sentinel exemption where `scripts/lint_vault.py:1009-1014`'s `--fix` delta
  path cannot. Touch no other check, no category list, and no `apply_fixes` branch.
  verify: test_lint_vault_reports_stem_name_divergence_and_never_repairs_it

- [ ] **Task 12 — Write AC-3's battery, inside the five-part containment door.** New module
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

- [ ] **Task 13 — Write AC-4's baseline-shape check and its reader battery.** New module
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

- [ ] **Task 14 — Close wall membership and the count pins, then run the floor.** In
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
why: Tasks 2, 3 and 6 — `_resolve_write_target` (Task 2, the pure resolver), `rename_note` with its M1 destination containment, M6 guard-mode fail-closed refusal, M3 staging name and M4 both-ends audit line, `save`'s CREATE fallback and its resolved-target INFO line, `update_fields`' REFUSE fallback (binding `resolved`), its in-lock `ValueError` for a name change whose door preconditions do not hold — no provenance, or a non-enforcing write guard (M6) — raised before anything is written, its mirroring of a caller-supplied `aliases` value onto the entity, and its write→move→rebind ordering with the door call placed OUTSIDE the `note_lock` block. Walls it joins: routing A/B/C (the move goes through `vault_io.move_note`, never `Path.rename`; `Path.resolve`, `Path.is_relative_to`, `Path.exists` and `Path.samefile` are READS and legal; M6 adds `vault_io.guard_mode()`, a module-attribute call on the already-imported `vault_io` that touches no filesystem and names no `os` member — and it is read through that function precisely so this file does not become a second `os.environ` home, which `vault_io._env_setting:104-115` forbids in writing); `non_completed_write_sites` over PACKAGE_ROOT (the door must contain no falsy return — M1 and M6 both RAISE, neither returns `None`); `functions_reserializing_parsed_frontmatter` and `functions_parsing_then_writing` (the door must contain no `parse_frontmatter` call); the new `write_target_buckets` scan (both new writers must classify SEAM-ROUTED — M1's two `contained = …` assignments bind a name the seed never tainted, M6's `mode = vault_io.guard_mode()` likewise binds a never-tainted name out of a value mentioning none, and `same_place = …` binds a name the fixpoint DOES taint, out of a value that mentions `source`, so the ordering-aware rebinding clause (which fires only on an Assign binding a tainted name out of a value mentioning NO tainted name) does not fire on any of them, and every `move_note`/`update_frontmatter_field` first positional in the door is still a name tainted by `source`; and `update_fields`' three-name head is legal by the clause that legalises the fallback itself — `resolved` is the seeded name, `file_path = resolved` is an Assign whose value mentions a tainted name, and `file_path = self.get_file_path(name)` rebinds a tainted name inside an `ast.If` whose test names it, which is AC-5's fifth ACCEPTED near-miss; the post-door `file_path = moved` lies AFTER the write call by position and so is outside the clause's span); WI-021's arm sweep and gate-placement pins (no new frontmatter arm, no new gate call); the new `door_calls_inside_note_lock` scan, which must stay EMPTY — `rename_note` holds no `note_lock` of its own and `update_fields` calls it AFTER its `with vault_io.note_lock(file_path)` block has exited.
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
why: Tasks 2, 9, 10, 14 — AC-1, AC-2, the two seam unit checks (both authored in Task 2, including M2's read-direction arm), AC-2's non-AC arms (the door's IDEMPOTENCE, `door_calls_inside_note_lock` asserted EMPTY over PACKAGE_ROOT with its planted both-ways battery — ordering decision 5 — and M6's both-ways guard-mode arm, which drives `OBSIDIAN_SCHEMAS_WRITE_GUARD` through `tests/support.py:patcher:73` — the project's own zero-fixture `monkeypatch` stand-in, whose `setitem` restores the prior value on exit and POPS the key where it was unset, so no later check inherits a mode this module set, and which is the same helper `tests/test_concurrent_access.py:706`, `:737` already uses for that variable) and the wall-membership closure. NEW FILE, so it joins every derived population that sweeps TESTS_ROOT: the `ast` single-home equality (it must not import `ast` — it imports the scans from `tests/derivations.py`); `modules_using_ast`'s non-vacuity; `skip_reason_literal_sites` (it must not hand-type a `SKIP_REASONS` member — import it); and the check contract, so every AC-named function is a top-level zero-argument `def` that RAISES on failure and the module's first statement is `ensure_project_interpreter(__file__)`.
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
| `tests/test_write_routing.py:test_filesystem_mutation_is_single_homed:87` (Walls A/B/C) | `python_files_under(PACKAGE_ROOT, SCRIPTS_ROOT)` | no filesystem-mutation capability, no non-read-only `os` member and no mutation-capable import outside `obsidian_schemas/vault_io.py`. The door moves through `vault_io.move_note`; the detector's checks are read-only; `Path.samefile`, `Path.exists` and `Path.resolve` are reads and legal; M6's `vault_io.guard_mode()` is a call on the already-imported `vault_io` module and names no `os` member, which is exactly why the mode is read through that function rather than through `os.environ` (`obsidian_schemas/vault_io.py:_env_setting:104-115`) |
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

All SIX `kind: required` mitigations of the LATEST speaking `## Threat Model` round (2026-09-25,
round 4), each folded into a `## Design` sentence AND an Implementation-Plan task in the same edit.
Four land on Task 6 (the door), one on Task 2 (the stamp) and one on Task 13 (AC-4's privacy wall),
exactly as the modeler's fences name them. Their batteries are Task 10 (M1, M3, M4, M6 — each pinned
both ways), Task 2's own check (M2) and Task 13's reader battery (M5, pinned both ways through the same
token function the live arm calls). M1–M5's `desc` values were re-emitted byte-identically by round 4
and are restated here unchanged; M6 is new in round 4, and its fold widened `update_fields`' pre-write
refusal from one remembered conjunct to the door's whole PRECONDITION class (Design §2's precondition
table) so the next refusal arm is placed by a rule rather than by the next round's finding.

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

**Failure modes that must fail gracefully, each asserted:** a rename onto an occupied destination
(`NoteAlreadyExists`, both files byte-identical); a rename of a symlinked source (`WriteFailedError`,
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
while a non-rename update under the same mode still succeeds: M6)**; and — the threat model's four door mitigations — a
rename to a destination that resolves outside the vault in any of its three spellings (`ValueError`,
nothing moved, nothing hard-linked outside: M1), a case-only rename interrupted between its two moves
(the residual file is inside `*.md` and every reader still sees it: M3), and a successful rename whose
audit line names the source as well as the destination (M4). Each of the four is pinned BOTH ways in
Task 10, M6's second direction being that under the default `enforce` the same occupied-destination
call still raises `NoteAlreadyExists` and an ordinary in-vault rename still moves — the arm that stops
a fail-closed clause from passing by refusing everything. The stamp's READ direction is a
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
`BookRepository.save`/`MeetingRepository.save`, and exactly one consumer-visible behaviour change
(HAL9000's generic entity PATCH at `routers/entities.py:461`, disclosed in Dave's signed read-back).
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
| `update_fields` now MOVES a file on every name change, permanently | certain (it is the design) | medium — incoming references go stale | The old stem is kept as an alias, so the library's own resolvers and Obsidian both still find the note; only this project's linter resolves by stem, and the resulting warning volume is measured (24 + 14) and accepted knowingly |
| The rename door fails between the move and the alias write | low | low — the note is where it should be and correctly stamped; one reachability route is lost | REVISED after the third spec-review round (2026-09-25): the earlier mitigation read "the door is idempotent, so a re-run completes it", which the prescribed door cannot do — `old_stem` is read off the source, provenance has already moved to the destination, so the re-run is a safe NO-OP that appends nothing. What actually holds: the entity is re-stamped before the alias write (so no later `save` recreates the old stem — no fork), the exception is loud, the re-run is safe, and the missing alias is repaired by one caller-side field edit (`repo.update_fields(entity, {"aliases": […, <old stem>]})` or by hand), which `## Edge Cases` states and Task 10 pins as the `aliases`-unchanged property. `move_note` is link-then-unlink, so a mid-flight kernel failure leaves a duplicate rather than a hole |
| The idempotent re-run silently performs a two-step move, because the branch discriminant is a raw string compare while the stamp comes back from `move_note` RESOLVED | medium — it is the default on macOS, the platform the floor runs on | medium — an interrupted re-run leaves a `.rename-tmp.md` where the document says nothing moved, and a battery pinning "no move" is RED against correct code | The branch key is file identity, not spelling: `(destination.parent.resolve(), destination.name) == (source.parent.resolve(), source.name)` (Design §2, Task 6). Task 10 asserts it on a vault path the test itself spelled divergently from its resolved form, with a non-vacuity assertion that the two spellings really do differ, so the arm cannot pass by the platform's good luck |
| The case-only two-step leaves a `.rename-tmp.md` file behind | low | low | REVISED after the threat model's M3 (2026-09-25): the earlier mitigation read "the staging name is outside `*.md`, so no reader picks it up" — which is the same fact that would make the failure SILENT, offered as the reason it is safe. The staging name now keeps the `.md` suffix, so the leftover is a note Obsidian, all three `file_pattern` globs and `lint_vault` all see, and the new detector reports it as a divergence. The second `move_note` still raises loudly if the staging name is occupied, and the state is recovered by a HAND rename — not by a door re-run, for the reason Design §2's re-run table gives (the same entity's stamp names the pre-move source, which is gone) |
| A caller sends the rename door a destination outside the vault — `..`, an absolute path, or an in-vault symlink pointing out | low | high — a note written outside the vault, under a clean name nothing flags | M1: the door refuses on the RESOLVED destination before any `move_note` call, the same test the seam applies to the source. Pinned both ways in Task 10 — all three escape spellings refused, an ordinary destination and an in-vault subdirectory still moving — so the clause cannot degenerate into refusing everything |
| `update_fields` calls the two-lock door, and a builder places the call inside the `note_lock` block it already holds | low, but it is the natural reading of the surrounding code | high — a deadlock between two concurrent movers, in a library three consumers run | Design §2 states the placement (outside the block, after the write commits, before the reload) and ordering decision 5 states WHY reentrancy does not license the other placement; `door_calls_inside_note_lock` asserts it structurally as an EMPTY set over `PACKAGE_ROOT`, pinned both ways in Task 10 so it cannot pass by forbidding the single-path doors `write_markdown_file` legitimately calls inside its own lock |
| A builder lets `rename_note`'s no-provenance raise leak out of `update_fields` after the content write has committed, leaving a note renamed in its field, un-aliased, unmoved, and an exception on a successful write | low, but it is what the naive ordering produces | medium — a divergence manufactured by the method that exists to end them, on the one population the method's own fallback serves | The refusal is moved BEFORE the write: inside the lock, after the name-change decision, before anything is gated or written (Design §2, "The no-provenance name change refuses BEFORE the write"; Task 6). Task 10 asserts the note is BYTE-IDENTICAL after the refusal, which is the assertion that distinguishes refusing early from refusing late, and asserts the non-rename and unchanged-name updates still succeed so the clause is not "refuse every unstamped update". The two alternatives are rejected in writing: skipping the move keeps today's leave-behind, and re-stamping from `get_file_path` would hand the door whichever member of a collision won the vault walk |
| `update_fields` is no longer ATOMIC across write-then-move, because the move cannot be held inside the lock | certain (it is the design) | low — every residual is loud, detector-visible and recoverable | The interleavings are walked in `## Edge Cases`: a concurrent source write loses to last-writer-wins and moves with the file, a concurrent move or delete gives `FileNotFoundError` from the door's own `source.exists()`, a concurrent create at the destination gives `NoteAlreadyExists` by syscall — the syscall arm holding because M6 has already refused the call where the write guard is not enforcing, the row below. None lands one person's bytes in another's note, each residual is exactly the `stem_name_divergence` the new detector reports, and each is a MOVE that did not happen, which re-running the idempotent door completes (pinned in Task 10; the one residual a re-run does NOT repair is the missing alias after a move that succeeded, which is the row above). The alternative placement is a deadlock in a library three consumers run |
| A consumer (or the conductor's own repair shell) sets `OBSIDIAN_SCHEMAS_WRITE_GUARD=observe` — the estate's documented rollback lever — and door 3's occupied-destination refusal silently becomes an `os.replace` that DESTROYS the occupied note | medium — it is the runbook's own cheapest rollback (`docs/concurrent-access.md:4286`) and the measure-before-adopting mode the three consumers are invited to set (`:2556`), read per call with no restart | high — one person's bytes land in another's note and the overwritten one is UNRECOVERABLE, in the one act Rollback says `git` cannot undo; WI-004 declared it acceptable (R9) only while door 3 had a single quarantine caller, a premise this item removes | M6: the door reads `vault_io.guard_mode()` beside M1's containment block and REFUSES with `ValueError` before any `move_note` call, and `update_fields` refuses the same condition inside its lock before its content write, so nothing is half-applied. Pinned both ways in Task 10 — refused under `observe` for an occupied AND an ordinary destination, still moving (and still raising `NoteAlreadyExists` on an occupied one) under `enforce` — with the environment set and restored in a `finally`. The residual is a capability LOSS while the mode is set, which is the intended direction for a rollback lever and is stated in Prerequisites 9 |
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
threat-model M5, and this round's fold of threat-model **M6** in Design §2's new "The door FAILS CLOSED
when the write guard is not enforcing" bullet and the "CLASS behind M6" paragraph beside it. Nothing
below adds spec content; it records things a later reader would otherwise have to re-derive.

### This round (M6) — what moved, and the two things it deliberately did NOT move

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
is what grew when plant (vii) landed. **The M1–M5 `## Mitigation Folds` records were NOT edited this
round and none needed to be:** the fourth threat-model round re-emitted all five `desc` values
byte-identically, and M6's clause sits BESIDE M1's in the door rather than inside it, so every quoted
Design sentence and Task-6 work text those five records carry is still byte-identical to the text at its
site. Only the section's preamble and the new M6 record moved. Three dispositions are deliberate
NON-actions and are recorded so
they read as decisions rather than omissions: **M1's residual** (resolve-then-`os.link` is check-then-act
against an attacker who can plant a symlink between the two — out of this item's threat model, bounded in
Design §2's M1 bullet, no work ordered), **the write-then-move window** (non-atomic by design, every
residual loud and detector-visible, resolved in `## Edge Cases` and `## Risk Analysis`, no work ordered),
and **the no-op branch's cosmetic audit line** (round 4's first non-blocking note: on the `same_place`
branch M4's INFO line reads "Renamed … from @New.md to @New.md"; the modeler recorded it as harmless,
not a security defect and not folded, so it is carried unchanged rather than spent a clause on).
None of the three is a `kind: required` mitigation and none has a fold record, which is correct: the
latest speaking threat-model round's SIX required mitigations are the only ones `## Mitigation Folds`
carries.

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

## Threat Model — 2026-09-25

**Recommendation: PROMOTE to threat-modeled — the approach is sound and its one genuinely new
capability is a RELOCATION door whose destination is caller-supplied and never containment-checked;
four required mitigations, each one clause, each landed on a plan task**

Cold-start spawn. I read the document in full including the five architect rounds, both red-team
rounds and the data-premise audit, then re-executed the security-relevant claims against this
worktree with Read/Grep rather than trusting the account of them — `vault_io`'s three doors and
`_resolved`, `name_gate.gate_write`'s type dispatch, both Tier-1 tables' `path_hostile` records,
`BaseRepository.save`/`update_fields` as they stand today, and the door body Design §2 specifies.
The seam itself is the safest part of this item: it REMOVES a name-derived target, and a name is the
one value in the payload an attacker can influence. What it adds is a door that moves files.

### Trigger check

Five fire. (1) **Filesystem operations on user-owned files** — the item ships the package's first
repository-level relocation capability over Dave's live vault. (2) **Persists data** — every write
path in the package changes where it lands. (3) **Untrusted input crossing into a trusted decision** —
vault BYTES (frontmatter, filenames) become a typed model at `obsidian_schemas/parser.py`, and this
item makes a value carried on that model decide where a write goes. (4) **PII** — person notes carry
names, emails and phones; the item adds a new WARNING and a new ERROR that quote them, and commits a
live-vault evidence artifact. (5) **Out-of-repo blast radius** — three consumers install `-e` and
inherit both the behaviour change and the new door.

### STRIDE review

**Spoofing — one surface, and it is the stamp's provenance.** The item's whole safety argument is
§7.6's claim that *"the stamp is a path the package itself produced from a path the caller handed it,
never a value read out of a note"*. That claim decides whether `_resolve_write_target`'s answer is
trusted input, so it is worth an assertion rather than a sentence. `BaseEntity.model_config` sets
`extra="allow"` (`obsidian_schemas/models.py:31-32`), so a crafted note declaring `_source_path:` in
its frontmatter reaches model construction; the design is correct that the parse's own assignment
lands last (`obsidian_schemas/parser.py:parse_markdown_file:244`, on the `entity is not None` arm) and
that a pydantic v2 `PrivateAttr` wins attribute lookup over `__pydantic_extra__` — so the forgery does
not take. But *does not take* is a property of two implementation details in two files, and nothing in
the plan asserts it: Task 2's check tests the WRITE direction (the stamp cannot reach a note) and AC-1(h)
tests the same direction over the sweep. The READ direction — a note cannot set the stamp — is
untested. If it ever regressed, the consequence is precisely the corruption this item exists to end,
turned into a directed one: a note that steers a consumer's `save()` into a different person's file.
The containment in `_resolve_write_target` bounds it to inside the vault and no further. **M2.**

**Tampering — the destination of `rename_note` is unbounded, and this is the finding.** The seam
resolves the SOURCE through a containment test (Design §2:
`candidate.resolve().is_relative_to(self.vault_path.resolve())`), and §7.6 states the property as if it
covered the door. It does not. `rename_note(entity, new_filename)` computes
`destination = self.vault_path / new_filename` (Design §2, doc `:1234`) and hands it straight to
`vault_io.move_note` with no containment test of its own, and there is nothing underneath to catch it:
`_resolved` is a bare `Path(path).resolve()` with no notion of a vault root
(`obsidian_schemas/vault_io.py:_resolved:234-243`), and `move_note` checks a symlinked SOURCE and
nothing about where `dest` points (`obsidian_schemas/vault_io.py:move_note:721-750`). Two reachable
spellings, and pathlib decides both:

- **A direct consumer call.** `rename_note` is PUBLIC and this item is the first thing to ship a
  relocation capability to HAL9000, Exocortex and orchestrator. `Path(vault) / "../../../x.md"`
  traverses and `Path(vault) / "/tmp/x.md"` replaces the vault root outright — an absolute operand
  wins. HAL9000 already forwards arbitrary request bodies into this layer
  (`routers/entities.py:461`, the one consumer-visible change in Dave's signed read-back), so a
  filename derived from request data reaching the new door is the obvious next call site, not a
  contrived one.
- **A symlinked DESTINATION inside the vault — and this one defeats the gate.** `_resolved` FOLLOWS
  symlinks. A dangling symlink at `@Target.md` pointing outside the vault resolves to the outside
  path, `os.link` succeeds there, and the note lands outside — with a perfectly clean name, so no
  Tier-1 branch is involved at all. (A non-dangling one is refused by `os.link`'s `FileExistsError` →
  `NoteAlreadyExists`, `obsidian_schemas/vault_io.py:_move_locked:758-771`.) This is why the
  mitigation has to test the RESOLVED destination and not the string.

What stands between this and the one in-library caller today is accidental and partial. `update_fields`
gates the delta above the write (`obsidian_schemas/repositories/base.py:483-485`) and for a Person a
`name` containing `/` is refused by `path_hostile` (`obsidian_schemas/name_validation.py:249-259`,
regex `/` and nothing else); Company has its own wider table (`:397-401`). But that is a NAME-HYGIENE
component doing path containment as a side effect, in a table this item's Scope Boundary declares
"read, never edited" — and `gate_write` returns a declared non-person type's delta **untouched**
without validating any name (`obsidian_schemas/name_gate.py:305-344`), so the protection is
type-dependent as well as incidental. Depending on it is the shape LESSONS #1 calls a boundary you can
route around. The door should refuse an escaping destination itself, in one clause, using the test the
seam already performs on the source. **M1.**

*Not a finding, checked and clean:* the occupied-destination refusal is a syscall and not a
check-then-act, so the `.exists()`/`samefile` branch in the door is a routing decision and not a TOCTOU
gate; `move_note` sorts both locks into a global total order and they are reentrant
(`vault_io.py:744-750`), so calling the door from inside `update_fields`' held lock introduces no
ordering edge; and cross-device escape fails loud, since `os.link` across filesystems raises `OSError`
→ `WriteFailedError`.

**Repudiation — one act is newly unreconstructable.** The item argues its own logging rule explicitly:
the `save` WARNING exists so *"the class becomes reconstructable from a consumer's logs instead of
being discovered as a corrupted note months later"* (doc `:585-588`). The door's audit line does not
meet that bar — `logger.info("Renamed %s note to %s", self.type_name, moved.name)` (Design §2)
records the destination and drops the source. After this item `update_fields` MOVES a file on every
name change, permanently, in three consumer repositories (the risk table rates that likelihood
*certain*), so the one act with no undo is the one whose before-state is not in the log. Naming both
ends is one format string. **M4.**

**Information disclosure — no new class; the existing wall is correctly placed.** The new WARNING
quotes an absolute vault path containing a person's name, which is a real PII surface but is the
package's shipped idiom, not a new one: `save` already logs `@{name}.md` at INFO
(`obsidian_schemas/repositories/base.py:411`) and `vault_io._refuse` already logs full resolved paths
at WARNING (`vault_io.py:195-198`). The detector's ERROR quotes a stem and a stored name — a linter
reporting a filename is the point, and it runs on Dave's machine on Dave's vault. The place this
genuinely matters is the committed artifact, and it is already walled: AC-4 asserts no absolute path
and no note filename leaks, importing `FORBIDDEN_DEFAULT_PATTERNS` rather than re-spelling it, and the
close-out procedure redacts to counts, classes and directions. The `_source_path` stamp is unwritable
by construction (`writer.model_to_frontmatter` composes from `model_fields` + `model_extra` +
`extra_fields`, `obsidian_schemas/writer.py:106-131`) and AC-1(h) asserts it. Nothing to require.

**Denial of service — nothing realistic, one availability finding under Tampering's heading.** No
network, no untrusted-size input, no recursion, no retry loop. The seam adds two `Path.resolve()`
calls per write where today there are none; negligible. The one availability concern is the case-only
two-step. Door 3's own design principle is stated in its docstring — *"link-then-unlink, deliberately
over unlink-then-link: a failure between the two leaves BOTH paths present, and a duplicate is
recoverable by hand while a lost note is not"* (`obsidian_schemas/vault_io.py:move_note:732-734`). The
two-step stages through `source.with_name(destination.name + ".rename-tmp")`, which manufactures
exactly the hole door 3 refuses to manufacture: between the two moves, and permanently if the process
dies there, the note is not a `*.md` file, so Obsidian does not show it, `lint_vault` does not read it,
the repository does not load it and the new detector cannot report it. The risk table rates this
low/low and gives as its mitigation *"the staging name is outside `*.md`, so no reader picks it up"* —
which is the same fact that makes the failure silent, offered as the reason it is safe. Keeping the
staging name inside the `.md` namespace costs one expression and converts a silent disappearance into
a visible, lintable, divergent note. It is one live row (baseline §2, row 3), repaired by hand by the
conductor, so the likelihood is low and the fix is cheap enough that low is not a reason to skip it.
**M3.**

**Elevation of privilege — none.** No credentials, no tokens, no scopes, no network egress, no
subprocess, no new import capability. The item's privilege surface is filesystem reach, and that is
what M1 bounds. WI-031's containment (no test may reach `OBSIDIAN_VAULT_PATH` or an absolute path) is
preserved and extended: AC-3's module ships the five-part door, AC-5's wall forbids a tenth write path,
and `## Wall Membership` enumerates the routing walls A/B/C that keep filesystem-mutation capability
single-homed in `vault_io.py`. The repair itself stays outside the cage.

### Mitigations

Four required, declared as fences below. All four are clauses on work the plan already schedules; none
changes the approach, the seam, the door's structure or any signed acceptance criterion, which is why
this is a PROMOTE with folds rather than a REVISE. Three land on Task 6 (the door) and one on Task 2
(the stamp).

1. **M1 — contain the door's destination.** `rename_note` refuses a `new_filename` whose RESOLVED
   destination is not inside `self.vault_path`, raising before any `move_note` call. Resolved and not
   string-compared, because the escape has two spellings and only one of them is in the string. This is
   the same test `_resolve_write_target` already applies to the source, which is what makes §7.6's
   trust-boundary claim true of the whole item rather than of half of it. Task 6.
2. **M2 — assert the stamp is unforgeable from note content.** Task 2's check already owns the write
   direction; it gains the read direction. One note whose frontmatter declares `_source_path` pointing
   at a second note, parsed, then `_resolve_write_target` asserted to answer the first note's own path.
   Task 2.
3. **M3 — the case-only staging window must not be silent.** The staging name keeps the `.md` suffix so
   an interrupted rename leaves a note every reader can still see. Task 6.
4. **M4 — the relocation audit line names both ends.** Task 6.

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

### Notes (non-blocking)

- **A pre-existing extras leak, not this item's to fix.** Any frontmatter key the models do not declare
  survives a round-trip through `entity.model_extra` and is re-serialized by `model_to_frontmatter`
  (`obsidian_schemas/writer.py:106-131`). AC-1(h) asserts no note *gains* a path-valued key, which is
  the right scope for this item; a note that already carries one keeps it. Worth knowing only so a
  builder does not read AC-1(h) as a claim that the package sanitizes extras.
- **`gate_write` validates no name for a declared non-person, non-company type**
  (`obsidian_schemas/name_gate.py:319-344`). Correct and deliberate — a Book title is not a person name
  — and noted only because it is why M1 cannot be satisfied by leaning on the gate.
- **The detector's `_gate_refusal_pattern` calls `gate_write` on every person note in the vault.** It is
  a pure predicate with no write arm and `lint_vault` already imports both symbols
  (`scripts/lint_vault.py:47-48`), so this adds no capability to the tool — confirming, rather than
  flagging, that the read-only property AC-3(d) asserts holds at the call as well as at the issue.
- **OPEN security questions: none.**

```verdict
gate: threat-modeler
verdict: PROMOTE
date: 2026-09-25
model: claude-opus-5
note: The seam removes a name-derived write target and is the safe half; the new capability is `rename_note`, whose destination is caller-supplied and contained nowhere — `self.vault_path / new_filename` traverses on `..` and is replaced outright by an absolute operand, `vault_io._resolved` is a bare `Path.resolve()` with no vault root (`vault_io.py:234-243`) and `move_note` checks only a symlinked SOURCE (`:721-750`), so the only thing bounding the one in-library caller today is `path_hostile`'s `/` regex in a name-hygiene table this item declares out of scope, which a symlinked destination bypasses entirely and which `gate_write` skips for a declared non-person type (`name_gate.py:319-344`) — closed by M1, one clause reusing the containment `_resolve_write_target` already performs on the source, with M2 asserting the stamp is unforgeable from note content (the read direction of §7.6's trust boundary, untested today), M3 keeping the case-only staging name inside `*.md` so an interrupted rename does not manufacture the hole door 3 is designed to avoid, and M4 logging the relocation's source; all four are clauses on scheduled tasks, none moves the approach or a signed criterion, zero OPEN questions.
```

## Spec Review — 2026-09-25

**Recommendation: REVISE — return to spec writer (gaps to fix)**

Cold-start spawn, first spec-review round on this document. I read it from line 1 in full — the
five architect rounds, both red-team rounds, the sign-off, the data audit and the threat model —
then re-read the code at every load-bearing citation rather than trusting the injected drift audit,
which proves only that symbols resolve. Rulings on record: WI-021's gate-name-output-is-an-identity
ruling (approach G's rejection), Dave's `ac_hash 15189b874b27` sign-off freezing AC-1…AC-5 and the
Intent, and the exploration's own accept-the-linter-noise disposition — I route against all three
rather than re-litigating them, and none of the findings below touches a signed criterion's text.

This is an unusually well-grounded spec. The seam is argued from the code rather than asserted, the
fallback asymmetry is the right shape, AC-5's data-flow rebuild is correct against
`tests/derivations.py`'s actual machinery, and the four threat-model folds are faithful. The findings
below are four places where the *document* decides something two ways, or where a class the live
vault contains has no member anywhere in the batteries.

### Citation verification

I read the code at every load-bearing citation. All resolve and all quote accurately, including the
ones a wrong reading would have made the design unbuildable:

- `obsidian_schemas/repositories/base.py:BaseRepository.save:391-393` / `:398` / `:411`;
  `update_fields:438`, `:440-441`, `:449`, `:454-459`, `:466-469`, `:483-485`, `:490`, `:493-495`;
  `_adopt:184-191` (the `_file_map[name_key] = file_path` write at `:188`); `_ensure_loaded:210-213`;
  `load:241-248`; `get_file_path:354-365`; `_load_file:311-314` — and `:313`'s
  `vault_io.remember_snapshot(file_path, stamp)`, which is what makes the provenance-bound `save`
  reach `write_markdown_file`'s 2u arm rather than its zero case. That is load-bearing for the whole
  design and the spec does not cite it; it is nonetheless TRUE, so this is a note rather than a gap.
- `obsidian_schemas/writer.py:model_to_frontmatter:89` composing from `model_fields` → `model_extra`
  → `extra_fields` at `:106-131`; `write_markdown_file:160`, the `entity is not None` gate arm at
  `:229-233`, the one `gate_write` call at `:252-253`, `with vault_io.note_lock(file_path) as
  resolved` at `:258`, `is_create` at `:275`, the two write calls at `:317`/`:319`;
  `update_frontmatter_field:333` (`:393`), `update_frontmatter_fields:405` (`:451`),
  `roundtrip_file:463` (`:504`) — all four path-taking leaves write their own FIRST parameter, so
  AC-5's bucket (a) holds, and `write_markdown_file` is the one that needs the `with … as` hop
  exactly as Design §4 says.
- `obsidian_schemas/vault_io.py:_resolved:234-243` (a bare `Path(path).resolve()`, symlink-following,
  no vault root); `move_note:721-750` with the sorted two-lock acquisition at `:744-750` and the
  symlink-source refusal at `:736-740`; `_move_locked:753-783` with `os.link`'s `FileExistsError` →
  `NoteAlreadyExists` at `:759-771` and `forget_snapshot` at `:780-781`. First positionals are
  `path`/`path`/`src` at `:670`/`:701`/`:721` — Design §4's "first positional is the total rule" is
  correct at every door.
- `obsidian_schemas/parser.py:parse_markdown_file:244` is the `parse_to_model` line and `:246-252`
  the `ParsedDocument(...)`, so the two-line insertion lands where the snippet shows;
  `parse_markdown_content:283` passes `file_path=None`. `models.py:BaseEntity:31-32` quotes verbatim.
- `scripts/lint_vault.py:check_structural:328` with `read_error`/`parse_error` `continue` at
  `:340-359`, `missing_type` at `:373-381`, the `TYPE_TO_MODEL` guard at `:387-388`;
  `read_vault:121` globbing `*.md` at `:123` and reading `entity_type` off the stored record at
  `:176`; `gate_write`/`NameGateRefusal` already imported at `:47-48`; `NameGateRefusalRecord:865`;
  `FixOutcome:926`; `CATEGORY_ORDER:1206`; the `person_missing_name` repair at `:1040-1045`; the
  phone-sentinel-unreachable comment at `:1009-1014`.
- `tests/derivations.py:DOOR_NAMES:47`, `_own_body_nodes:245`, `_names_in:282`, `_is_write_call:286`,
  `_taints_a_write:361-409` (seed `:368-382`, fixpoint `:389-401`, sink `:404-408`),
  `functions_calling:873`, `_pos:924`, `_assign_targets_name:928`, `mutating_drive_vault_args:2175`.
  The monotonicity claim and the `_names_in(target)` hazard Design §4 warns about are both real as
  written.
- `tests/fixture_vault.py:CORPUS_DIGEST:44`, `NOTES:217`, the four divergent specimens at `:255-260`,
  `:261-266`, `:297-301`, `:302-306`, the collision third at `:273-276`, the whitespace
  discriminator at `:246-254`, the phone specimen at `:288-293`, `LOADABLE:521`'s "22 person files",
  `materialize_vault:626`. Premise 13 reproduces note for note.
- `tests/support.py:captured_logs:91` does default `level=logging.WARNING`, so Task 10's explicit
  `level=logging.INFO` for M4 and its silence for (f)'s WARNING are both right.
- `tests/test_concurrent_access.py:test_wi020_derivations_survive_the_routing:1060` (the `{write_markdown_file}`
  set equality at `:1081`, `non_completed_write_sites == 8` at `:1085`);
  `tests/test_name_gate_wall.py:test_wall_membership_is_closed_by_running_each_walls_predicate:1057`;
  `tests/test_loud_fail_write.py:test_write_failure_raises_and_noops_keep_their_return:105`;
  `tests/test_lint_vault_fix_rules.py:1703`'s `auto_fixable_emitter_checks` set equality.
- `docs/stem-divergence-live-baseline.md` `:144-153` (the eight rows), `:155-156` (the two vocabularies
  Task 13 pins), `§0`–`§5` all present. AC-4's consistency rule does pass against it.

One stale SYMBOL, non-blocking and listed below: premise 11 names `entity_to_frontmatter`; the
function is `model_to_frontmatter` (`obsidian_schemas/writer.py:model_to_frontmatter:89`). Design §1
uses the correct name, so nothing downstream is wrong.

### Blocking issues

**1. The live vault's row 8 — a non-`@`-prefixed file holding `type: person` — has no member in any
battery, and AC-3(b)'s own wording points a builder away from it.**

`docs/stem-divergence-live-baseline.md:153` is one of the eight divergences this item exists to
repair: *"a **book-titled file** (no `@`, at the vault root) holding `type: person`"*, destination
occupied by a different note, the item's single live MERGE and one of its four booked hand repairs
(`§4`, `## Hand repairs riding along`). Design §3's arm is correct for it — the guard is
`vf.entity_type == "person"` and the stem strip is conditional
(`stem = vf.stem[1:] if vf.stem.startswith("@") else vf.stem`), and `check_structural`'s loop does
reach such a file, since the `is_at_prefixed` tests sit only on `no_frontmatter` and `missing_type`
and `person` is in `TYPE_TO_MODEL` (`scripts/lint_vault.py:check_structural:362-388`).

The problem is that nothing anywhere pins it, and one criterion reads as forbidding it. AC-3(b)
requires the check to emit nothing for *"every non-`@`-prefixed note"* among the corpus notes. Over
the frozen corpus that is satisfiable two ways, because every `declared_type="person"` entry in
`tests/fixture_vault.py:NOTES:217-479` is `@`-prefixed: by `vf.entity_type == "person"` (correct,
Design §3) and by `vf.is_at_prefixed and vf.entity_type == "person"` (wrong, and the narrower reading
of AC-3(b)'s clause). Both pass AC-3(a) with four, both pass AC-3(b), both pass AC-3(c)/(d)/(e) — and
the second one silently misses the live row on the report Dave actually runs, which is the fourth
"Examples of done" scenario verbatim.

This is the exact WI-286 shape this document already invoked twice and closed twice by PLANTING: the
sentinel-exempt phone stub for the door-predicate spelling (`## Exploration Notes`, "And the corpus
cannot tell the two rules apart"), and the Book/Meeting colliding groups for the call-and-discard
stub (the red-team's round 1). The third member of the same class was not planted. The fix is the
same two edits and touches no signed text: in **Task 12**, plant a non-`@`-prefixed note carrying
`type: person` and a stem that differs raw from its stored `name:` — row 8's shape — and assert it is
emitted as a `stem_name_divergence` ERROR; and in **Design §3**, state in one clause that the guard is
`entity_type` and NOT `is_at_prefixed`, naming baseline row 8 as the live subject, so a builder
reading AC-3(b)'s "every non-`@`-prefixed note" does not narrow the guard to satisfy it.
(A builder's question this answers: *"AC-3(b) says never report a non-`@` note — do I gate the new arm
on `is_at_prefixed`?"*)

**2. The lock scope of `update_fields`' call to `rename_note` is unspecified, and the safety argument
the document gives for the placement it implies is unsound.**

Design §2 states the ordering as a prescription:

> write the content … `# still inside `with vault_io.note_lock(file_path)`` / THEN move
> `moved = self.rename_note(…)` / THEN rebind / THEN reload

and then argues (same section, the paragraph ending the door's prescription) that *"calling the door
from inside the already-held lock is itself safe, since it sorts both resolved paths into a global
total order and the locks are reentrant (`vault_io.py:744-750`)"*. AC-2's `why` repeats it and
`## Edge Cases` resolves *"one renames while another saves"* with *"it introduces no new
lock-ordering edge"*.

Reentrancy only excuses re-acquiring the lock you already hold; it does not preserve the global
order. `move_note` sorts `[src, dest]` and acquires in that order (`vault_io.py:744-750`), which is
deadlock-free only while nobody holds either lock across the call. A caller holding `note_lock(A)`
that then calls `move_note(A, B)` with `B < A` acquires A-then-B against the total order; a
concurrent `move_note(B, A)` acquires B-then-A, and the two block. `rename_note` also calls
`writer.update_frontmatter_field(moved, …)`, which takes `note_lock(moved)` itself
(`obsidian_schemas/writer.py:update_frontmatter_field:363-393`) — a second out-of-order acquisition
from inside the same held lock. Today no site in the tree holds a note lock across `move_note`
(`scripts/lint_vault.py:1343` is the only caller and holds none), so this item introduces the edge.

The document's own ordering decision 5 states the correct rule and reaches the opposite conclusion —
*"holding the source lock across a call that acquires the destination's would violate that order for
a concurrent mover"* — which is why this is a contradiction rather than a debatable trade-off: the
spec is buildable both ways and the Edge Case is resolved on the half that does not hold. Nothing in
the sequencing argument requires the call to be inside: `vault_io.write_note(file_path, …,
precondition=stamp)` has already committed, `forget_snapshot(source)` is `move_note`'s business, and
the reload at `base.py:493-495` is outside the `with` already. State the placement explicitly in
Design §2 and in Task 6's work text, and correct whichever of the two safety sentences does not
survive it.
(Builder's question: *"Does `moved = self.rename_note(...)` go inside or after the `with
vault_io.note_lock(file_path)` block?"*)

**3. Design §2's `update_fields` ordering block hands the door `updated_view`, a name the document
never defines, and the paragraph below it says to hand it `entity`.**

The block reads `moved = self.rename_note(updated_view, f"@{new_name}.md")`; two paragraphs later:
*"the door is called with the caller's `entity` (already stamped by the parse) — never with a
freshly-constructed view."* `updated_view` appears nowhere else in the document. This is not
cosmetic: `rename_note` re-stamps whatever it is handed (`entity._source_path = moved`), reads
`aliases` off it, and `_adopt`s it — so AC-2(e) ("a `save()` on the SAME in-memory entity lands in
the new file") and AC-2(g) both turn on which object it gets. The prose answer is the right one and
the code line contradicts it; make the block say `entity`.

**4. The `## Acceptance Criteria` preamble still says the set is unsigned, contradicting the
`ac-signoff` fence and the Scope Boundary.**

The section opens *"Draft — proposed at `exploring`, to be reviewed and signed by Dave through
`/review-spec` before `→ specced`. The spec-writer refines them in place; nothing here is frozen
yet."* The `## AC Sign-off` fence records `verdict: PROMOTE`, `reviewer: dave`, `signed_at:
2026-09-25T11:22:44+01:00`, `ac_hash: 15189b874b27` plus five per-criterion hashes, and
`## Scope Boundary` lists *"the `## Intent` and `## Acceptance Criteria` sections of this document,
which are hash-signed"* among the files the builder must not touch. `## Design`'s own opening says
the ACs "are **not touched by this spec**". Three surfaces state the ruling and the fourth — the one
a builder reads immediately before the criteria themselves — still states the pre-ruling behaviour
and invites an in-place refinement that would break the signature. One sentence; it is the WI-226
sweep, not a style note.

### Non-blocking notes

- **`rename_note`'s idempotent branch ships untested.** `## Edge Cases` resolves two cases on it —
  *"The rename fails halfway"* (**Decision:** *"re-running `rename_note(entity, same)` is idempotent:
  the `destination == source` branch skips the move and appends the alias"*) and *"Re-running the
  whole build, or re-running the repair"* — and neither AC-2's eight arms nor Task 10's battery names
  an idempotency assertion. The branch is also what `## Risk Analysis`'s rollback row leans on
  ("recoverable by hand or by re-running the idempotent door"). AC-2 is signed and cannot gain an
  arm; Task 10 can, at the cost of one sentence.
- **`save`'s INFO line will name a file it did not write.** Task 3 says *"do not touch `save`'s gate,
  `overwrite`, `_adopt` or logging"*, and today's line is
  `logger.info(f"Saved {self.type_name}: {filename}")` with `filename = f"@{name}.md"`
  (`obsidian_schemas/repositories/base.py:BaseRepository.save:392`, `:411`). Under the
  resolved-or-derived shape the write can land elsewhere while the log still says `@{name}.md` — the
  exact defect M4 corrects one method over, and the shape the `## Approach` WARNING exists to make
  "reconstructable from a consumer's logs". Say whether the line logs the resolved target.
- **The alias write is unguarded for types that declare no `aliases` field.** The door does
  `update_frontmatter_field(moved, "aliases", aliases)` unconditionally while guarding only the
  in-memory half with `if hasattr(entity, "aliases")`. Only `Person` declares the field
  (`obsidian_schemas/models.py:Person:80`); `Company`, `Book` and `Meeting` do not, and
  `CompanyRepository` inherits the door whole — which `## Scope Boundary` explicitly contemplates for
  WI-022's seven mangled company notes. Writing Obsidian's own `aliases` key onto a non-Person note is
  arguably right, but the asymmetry between the two halves reads as an oversight rather than a
  decision; one clause settles it.
- **Counting slips, three of them, the class the earlier rounds kept catching.**
  `## Verified Diagnosis` opens *"Four load-bearing claims"* over six numbered items. The
  `tests/test_concurrent_access.py` write-target fence says *"four count pins"*, lists five, and the
  next sentence says *"The design holds all five still"*. `## Wall Membership`'s row for the same
  module says *"the four routing pins"* and lists five. Also, `## Approach` and the blast-radius
  bullet call the call-site edits *"nine one-line call-site edits"*, while the REFUSE-fallback shape
  Design §2 prescribes is three lines at each of the seven refusing sites.
- **Premise 11 names a symbol that does not exist.** `entity_to_frontmatter` → `model_to_frontmatter`
  (`obsidian_schemas/writer.py:model_to_frontmatter:89`). Exploration-notes archaeology, corrected
  everywhere downstream; worth one word so a later reader does not grep for it.
- **The read-back's "one true live subject of the not-renameable marker" is not one.** Conductor
  read-back note 2 says *"Row 8 … is the one live MERGE and the one true live subject of the
  not-renameable marker"*, echoing `docs/stem-divergence-live-baseline.md:159-161`. The marker fires on
  the DOOR PREDICATE, and row 8's (b3) column reads `WRITTEN`; `§1`'s own figure is *"divergent rows
  the WRITE DOOR refuses (b3): 0 of 8"*. So no live row carries the marker — which is what the same
  note's preceding sentence says ("their discriminating members ONLY in the frozen corpus and the
  plants"). Row 8 is not-renameable because its destination is occupied, which the marker does not
  encode and the direction table does. Nothing in the criteria depends on it; the sentence will
  mislead the conductor at the exit attestation.
- **Tasks 3, 4, 5, 6, 7 and 11 declare a `verify:` naming a test authored in a later task.** D10a is
  satisfied (the declarations are well-formed) and D10b runs after every task has landed, so this
  refuses nothing — but a builder finishing Task 3 has nothing runnable to prove it beyond the floor.
  Worth one line in the plan's preamble saying so, since the plan already explains the 2–6 / 7–12
  split.
- **Task 2's M2 arm asserts a pydantic internal without citing it.** *"assert … that the forged value
  reached the model but is confined to `entity.model_extra`"* is a claim about how pydantic v2 treats
  an underscore-prefixed extra key at `model_validate` time, uncited anywhere. The PROPERTY M2 needs —
  `getattr(entity, "_source_path")` answers the parsed path — holds whether or not the forged key is
  retained; pinning the retention makes the arm RED against correct code if pydantic drops it. Assert
  the property; make the `model_extra` half an observation or cite it.

### Carried-forward notes

- **Threat model 2026-09-25, "a pre-existing extras leak, not this item's to fix"** — still open and
  unfolded anywhere in the spec: any undeclared frontmatter key survives a round-trip through
  `entity.model_extra` and is re-serialized (`obsidian_schemas/writer.py:model_to_frontmatter:119-123`),
  so AC-1(h)'s promise is "no note GAINS a path-valued key" and never "the package sanitizes extras".
  Re-deferred deliberately: it is a pre-existing package property this item neither creates nor
  worsens, and the one sentence it wants belongs beside AC-1(h)'s note in Design §1, not in a task.
- **Architect round 6, note 6(iv)** — the deliberately-out-of-scope items (`_get_cache_key`'s strip
  asymmetry, approach F's re-keying, the Book/Meeting `save` collapse) stand as written and are all
  named in `## Scope Boundary`. Closed, recorded here so the chain is unbroken.
- All other prior non-blocking notes are FOLDED and I verified each fold against the code rather than
  the prose: architect notes 1 (the ordering-aware rebinding clause, Design §4, and it does correctly
  leave both shipped fallback spellings legal), 2 (first positional, correct at all four doors), 3
  (`NameGateRefusalRecord` reuse), 4 (`model_copy` preserves), 5 (approach F's `_adopt` sentence
  corrected); round 5 notes 1 (the frame question), 2 (the `name:`-less note), 3 (the enumeration
  widened past AC-5's floor); and the data audit's Domain A exclusion (Design §4's closing paragraph),
  Domain B second read-side site (Design §5), the `NoteSpec`-with-no-`fields` skip (Task 9, Task 12,
  `## Edge Cases`) and the premise-rot note (`## Edge Cases`, `## Risk Analysis`, `## Verification`).

```verdict
gate: spec-reviewer
verdict: REVISE
date: 2026-09-25
model: claude-opus-5
targets: AC-3, Task 12, Task 6, #design, #acceptance-criteria
prior: none
basis: original
findings: 4/12
note: The live vault's row 8 — a non-`@`-prefixed file holding `type: person`, the item's one MERGE and one of its eight divergences — has no member in any battery, and AC-3(b)'s "emits nothing for every non-`@`-prefixed note" makes `vf.is_at_prefixed and entity_type == "person"` pass every corpus arm while missing that row on the report Dave runs; it is the third instance of the WI-286 class this document already closed twice by planting, and the plant is the fix. Second, `update_fields`' call to `rename_note` is prescribed "still inside `with vault_io.note_lock(file_path)`" and justified by reentrancy plus `move_note`'s sorted two-lock order, which is exactly the configuration Design §2's own ordering decision 5 says "would violate that order for a concurrent mover" — reentrancy excuses re-acquiring the held lock, not holding it across a two-lock door — so the placement is stated twice, oppositely, and the concurrency Edge Case is resolved on the half that does not hold. Plus the same block hands the door an undefined `updated_view` where the prose says `entity` (AC-2(e)/(g) turn on which), and the `## Acceptance Criteria` preamble still reads "nothing here is frozen yet" against a signed `ac_hash 15189b874b27` and a Scope Boundary forbidding the edit it invites.
```

## Adversarial Review — 2026-09-25

Cold-start spawn, first injection-hunter round on this document (no `## Adversarial Review`
section existed before this edit, and no `gate: injection-hunter` fence appears anywhere else in
this document). I read the document from line 1 to its end in full — Problem/Motivation through
Intent, the entire Exploration Notes arm (all five architect rounds and the red-team round folded
inline, all fifteen numbered premises and every constraint), Approach, Design (all seven
subsections), Verified Diagnosis, Edge Cases, the fourteen-task Implementation Plan, Write Targets
(both `kind: precondition` fences and the builder's own write-target fences), Wall Membership,
Mitigation Folds, Verification, Scope Boundary, Risk Analysis, the five Acceptance Criteria fences
and Examples of Done, then every prior gate's verdict prose in order — Architectural Review,
AC Red-Team, AC Sign-off, Data Audit, Threat Model, and the just-landed Spec Review — reading each
gate's narrative for text whose *effect*, not merely its topic, is to steer a reviewer's verdict. I
also grepped the sibling archive (`docs/filename-name-divergence-repair-rounds.md`) for verdict
fences and steering phrases, and confirmed no `gate: injection-hunter` fence exists anywhere in
either file for this item — this is a genuine cold-start read, not a re-run.

Found nothing that reads as planted steering. The document is unusually dense, self-arguing prose —
it repeatedly defends its own design choices, names and rejects alternative approaches, and narrates
five architect rounds' worth of self-correction — but every instance of that is the spec (and the
prior gates) making a technical case about the CODE, never an instruction aimed at a reviewing
agent. There is no "ignore the previous instruction," no "this was pre-approved, emit PROMOTE," no
text addressed to "the reviewer" telling it what to conclude, and no hidden-formatting trick (I
checked for HTML comments specifically — the only one in the document is the legitimate
machine-maintained archive-split pointer at the top). The one place language brushes against
injection vocabulary is domain content about the SYSTEM being specified, not the review process: the
Design and Threat Model sections discuss a hypothetical "note steering a consumer's `save()` into a
different person's file" and a spec-reviewer aside dismisses "the injected drift audit" as proving
only that symbols resolve — both are the document's own subject matter (a provenance-forgery threat
model; a deterministic citation-checking tool's output) rather than steering aimed at me. The
spec-reviewer's own REVISE immediately above is argued from re-read code citations (row 8's absent
battery member, the lock-ordering contradiction, the undefined `updated_view`, the stale AC preamble
sentence) and is not itself the product of anything planted — it reads as an independent, well-cited
finding I would reach the same way on a fresh read, which I did.

```verdict
gate: injection-hunter
verdict: PROMOTE
date: 2026-09-25
model: claude-sonnet-5
note: Full end-to-end read of the document and its prior gates' verdict prose (architect x5, AC red-team, AC sign-off, data audit, threat model, spec review) plus the sibling rounds archive found no text addressed to a reviewer, no "ignore prior instructions"/"pre-approved" phrasing, and no hidden formatting (only one HTML comment in the document, the legitimate archive-split pointer) — the document's extensive self-arguing prose is the spec and prior gates making their own technical case, not steering a verdict, and the spec-reviewer's REVISE immediately above reads as an independently-derived, code-cited finding rather than the product of injected manipulation.
```

## Threat Model — 2026-09-25

**Recommendation: PROMOTE to threat-modeled — round 2. All four required mitigations of the
2026-09-25 round are folded faithfully into the code the spec prescribes and pinned both ways in a
battery; the fold introduced no new security surface; no mitigation moves and no new one is
required. The four fences below are RE-EMITTED with byte-identical `desc` and unchanged `landed:`.**

Second threat-model round on this document, re-reading the material the spec-writer's fold ADDED
since round 1 — the `## Mitigation Folds` section's four `fold` fences, Design §1's stamp bullets,
Design §2's door body and its five ordering decisions, the `update_fields` ordering block, Tasks 2, 3,
5, 6, 7, 10 and 12, and the eleven `## Edge Cases` entries that are new or rewritten. I checked each
fold against the CODE it cites rather than against the fold's own prose, and re-walked M1's
containment expression for escapes it admits rather than confirming the ones I named last round. I
also read the spec-review round that landed between my two rounds, because one of its four blocking
findings corrects a claim *I* made.

### Trigger check

The same five fire and none has changed shape: filesystem operations on user-owned files (the
package's first repository-level relocation capability), persistence (every write path changes where
it lands), untrusted vault bytes crossing into a trusted write-target decision, PII (person names in
a new WARNING, a new ERROR and a committed live-vault artifact), and an out-of-repo blast radius
through three `-e` consumers. The fold added no sixth: no network, no subprocess, no credential, no
new import capability, and `## Wall Membership`'s routing walls A/B/C still keep filesystem-mutation
capability single-homed in `obsidian_schemas/vault_io.py`.

### The four folds, verified against the code they prescribe

**M1 — landed and total.** Design §2's door body raises `ValueError` unless
`destination.resolve().is_relative_to(self.vault_path.resolve())`, with an `OSError`/`ValueError` out
of the resolve treated as NOT contained, positioned immediately after
`destination = self.vault_path / new_filename` and before every one of the three `vault_io.move_note`
call sites in the method (doc `:1289-1298`). Task 6 carries the same clause in its work text and Task
10 pins it both ways: refusal for all three reachable spellings — a traversing relative name built
with `os.path.relpath`, the absolute path, and an in-vault filename that is a SYMLINK to an outside
file — with the discriminating oracle being the outside file's `st_nlink` before and after, which is
the only assertion that actually proves `os.link` did not land there; and an ordinary destination plus
one inside an in-vault SUBDIRECTORY still moving, so the clause cannot degenerate into refusing
everything. `## Edge Cases` states all three spellings and the unresolvable case.

I re-walked the expression for escapes the fold admits rather than re-confirming the three I named.
Two classes normalize back INSIDE and therefore PASS containment — `new_filename="sub/.."` and
`""`/`"."`, all of which resolve to the vault root itself, which `is_relative_to` reports true of
itself — and both then die loud one frame later on `os.link`'s `FileExistsError` against a directory
(`NoteAlreadyExists`, `obsidian_schemas/vault_io.py:_move_locked:759-771`); nothing escapes and no
byte is written. The M3 staging name cannot be steered either: it is composed through
`source.with_name(...)`, and the only branch that reaches it requires
`source.samefile(destination)`, so `destination.stem` is the source's own stem in another case.
`Path.is_relative_to` is 3.9+, which the document's own constraint 4 declares and
`tests/test_lint_vault_fix_rules.py:1984-1985` already uses on shipped code. The clause is total for
the escape class and over-refuses nothing.

**M2 — landed, and the fold is STRONGER than what I asked for.** Task 2 plants A and B, declares
`_source_path: <B's path>` in A's own frontmatter as BYTES (never through `repo.save`), parses A, and
asserts the PROPERTY: `_resolve_write_target` answers A's own path, `getattr(entity, "_source_path")`
— verbatim the accessor the seam reads — is A's and not B's, and nothing the seam reads answers B.
Where the forged key ended up is demoted to a Build-Log observation with the reason stated, so the arm
cannot go RED against correct code on a pydantic release that stops retaining underscore-prefixed
extras. That is a better arm than the one I described, and Design §1's bullet separates the
two-implementation-detail EXPLANATION from the asserted property explicitly.

**M3 — landed, and the battery asserts the property rather than a proxy for it.** The staging name is
`source.with_name(destination.stem + ".rename-tmp.md")` in the door body, in Task 6's work text and in
the `## Edge Cases` entry for a process dying between the two moves. Task 10 wraps
`obsidian_schemas.repositories.base.vault_io.move_note` in a recording delegate restored in a
`finally`, drives one case-only rename, and asserts two recorded calls with `.md` on both positionals
of both — then that the staging path is matched by `vault_path.glob(repo.file_pattern)`, which is the
very enumeration `BaseRepository.load` uses (`obsidian_schemas/repositories/base.py:load:241`), so
"a reader still sees it" is reduced to the reader's own predicate instead of to a suffix string. The
near-miss arm drives the REJECTED spelling through the same glob and asserts it is NOT matched, so the
assertion is shown to discriminate. I checked the glob for each inheriting type: `@Foo.rename-tmp.md`
matches `@*.md`, `Meeting <x>.rename-tmp.md` matches `Meeting *.md`, and Book's `*.md` matches
unconditionally — the suffix-anchored argument Design §2 makes holds at all three. `## Risk Analysis`'s
row is rewritten and now names the earlier reasoning as the defect it was.

**M4 — landed.** `logger.info("Renamed %s note from %s to %s", self.type_name, source.name,
moved.name)`, in the door body and in Task 6, captured in Task 10 through
`tests/support.py:captured_logs` with an explicit `level=logging.INFO` (its default is `WARNING`, so
the default would have captured nothing — the fold got that right) and asserted to contain the source
filename as well as the destination's, both taken from paths the test created. The fold logs basenames
rather than absolute paths and argues why: it is the package's shipped INFO idiom
(`obsidian_schemas/repositories/base.py:411`) and adds no PII surface the package does not already
have. The requirement was that both ends be named so a permanent relocation is reconstructable, and
both ends are named — satisfied. Task 3 and Task 5 additionally fixed the sibling defect I only noted
(`save`'s INFO line naming a file it may not have written); that is the same rule applied one method
over and it is a straight improvement.

### One claim of my own that the spec-review correctly overturned

Round 1 filed the in-lock door call under *"not a finding, checked and clean"*, reasoning from
`move_note`'s sorted two-lock acquisition plus `note_lock`'s reentrancy
(`obsidian_schemas/vault_io.py:move_note:744-750`). That reasoning was wrong: a sorted acquisition is
deadlock-free only while no caller holds either lock ACROSS the call, and reentrancy excuses
re-acquiring a lock you hold, not the ordering. The spec-review's finding 2 is right, and a deadlock
in a library three consumers run is a real availability defect — so a genuine one was closed between
my rounds, and not by me.

The resolution the spec now ships is stronger than either a prose placement or a mitigation from me
would have been. The call is placed OUTSIDE the `with vault_io.note_lock(file_path)` block in Design
§2's ordering block and in Task 6; ordering decision 5 states the rule as a property of the PACKAGE
rather than of this door — no call to `move_note`, to one of `writer.py`'s path-taking leaves, or to a
repository method that itself calls `move_note`, is lexically nested inside a `with` mentioning
`note_lock` — with the third clause DERIVED from `functions_calling(files, "move_note")` so a future
second mover enlists without being remembered; and Task 7 ships
`door_calls_inside_note_lock` while Task 10 asserts it EMPTY over `PACKAGE_ROOT`, pinned both ways
with the deadlock shape in the REFUSED battery and `write_markdown_file`'s own in-lock `write_note`
call in the ACCEPTED battery so the scan cannot pass by forbidding shipped code. That is the right
shape, it requires nothing further from me, and the `## Edge Cases` concurrency entry and Design §2
now agree with each other where they previously did not.

### STRIDE delta — what the fold changed, category by category

Nothing in Spoofing, Information disclosure or Elevation of privilege moved: M2 closes the stamp's
read direction, the disclosure wall is where it was (AC-4 importing `FORBIDDEN_DEFAULT_PATTERNS`
rather than re-spelling it; the close-out redacting to counts, classes and directions), and the
privilege surface is still filesystem reach, now bounded by M1. Tampering is strictly better: the
door's destination is contained where it was contained nowhere. Repudiation is better at two sites,
not one. Denial of service is where the one delta sits, and it is an improvement plus one residual
noted below.

### Notes (non-blocking)

- **`update_fields` is no longer atomic across write-then-move, and that is the correct trade.**
  Moving the door call outside the lock opens a window between `vault_io.write_note(...,
  precondition=stamp)` committing and `move_note` taking its two locks. I walked the interleavings: a
  concurrent write of the source loses to last-writer-wins and then moves with the file; a concurrent
  move or delete of the source gives `FileNotFoundError` from the door's own `source.exists()` check;
  a concurrent create at the destination gives `NoteAlreadyExists` by syscall. In every case the
  residual state is LOUD, is exactly the `stem_name_divergence` the new detector reports, and is
  recoverable by re-running the door, whose idempotence Task 10 now pins. No interleaving lands one
  person's bytes in another person's note, which is the harm this item exists to end. The alternative
  placement is a deadlock. Not a required mitigation — recorded because a builder reading
  `## Edge Cases`' concurrency entry ("no new lock-ordering edge exists", which is true) should not
  read it as "no new window exists".
- **M1's exact bound, so it is not over-read.** It is resolve-then-`os.link`, so it is check-then-act
  on a path: an attacker who can plant a symlink at the destination BETWEEN the two can still win.
  That attacker already has write access to Dave's vault directory, which is outside this item's
  threat model, and `os.link` has no `O_NOFOLLOW` spelling reachable through pathlib. M1's job is to
  stop a caller-supplied or request-derived filename from escaping, and it does that completely.
- **The M3 window is now visible to `load()` as well as to a reader, which is the point and has one
  exit-attestation consequence.** During a SUCCESSFUL two-step a concurrent `load()` can see the
  staging note, and `move_note`'s link-then-unlink means a sub-window where both paths exist — so a
  load landing there sees two notes carrying one identifier and records a `PersonRepository.conflicts`
  row. It is two syscalls wide, on one branch, for one live row. Worth one line at the exit
  attestation only because that procedure's ship condition is `len(conflicts) == 0`: a conflict
  observed while a case-only repair is mid-flight is this window, not a new duplicate.
- **The extras leak is re-deferred and folded where it belongs.** Round 1's "pre-existing extras leak,
  not this item's to fix" is now a stated bound beside AC-1(h)'s definition in Design §1 rather than a
  task, which is the right home: there is no work, only a promise that must not be mistaken for a
  sanitizer.
- **One structural repair made in this edit.** The document ended with a stray unterminated ```` ``` ````
  line immediately after the injection-hunter's closing fence, which would have swallowed this entire
  section — including its `verdict` and `mitigation` fences — into an open code block and made the
  round declare nothing. Removed; no other gate's bytes touched.
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

```verdict
gate: threat-modeler
verdict: PROMOTE
date: 2026-09-25
model: claude-opus-5
note: Round 2 re-read the material the fold ADDED and checked each mitigation against the code it prescribes rather than its own prose: all four landed on their named tasks with ordinals unmoved, and two folds are stronger than what round 1 asked for — M2 asserts the PROPERTY (the accessor the seam reads answers the parsed path) and demotes pydantic's extras retention to a Build-Log observation so the arm cannot redden against correct code, and M3's battery reduces "a reader still sees it" to `vault_path.glob(repo.file_pattern)`, the enumeration `BaseRepository.load` itself uses, with the rejected spelling driven through the same glob as a near-miss. I re-walked M1's expression for escapes it ADMITS rather than the three I named: `sub/..`, `""` and `"."` all normalize back inside and pass containment, then die loud on `os.link`'s `FileExistsError` with no byte written, and the staging name is unsteerable because its branch requires `source.samefile(destination)` — so the clause is total for the escape class and over-refuses nothing, with Task 10's `st_nlink` before/after oracle the only assertion that actually proves `os.link` did not land outside. One claim of my own was overturned between rounds and correctly: round 1 filed the in-lock door call as clean, reasoning from `move_note`'s sorted two-lock order plus reentrancy, but sorting is deadlock-free only while no caller holds either lock across the call — the spec-review's finding 2 is right, and the resolution now shipped is structural rather than prose (the call placed outside the block, ordering decision 5 stated as a property of the PACKAGE with its third clause derived from `functions_calling`, and `door_calls_inside_note_lock` asserted EMPTY over `PACKAGE_ROOT` with the deadlock shape refused and `write_markdown_file`'s own in-lock `write_note` accepted), so a real availability defect closed and nothing further is required from me. The fold opened no new security surface: the one residual is that `update_fields` is no longer atomic across write-then-move, and every interleaving is loud, is the divergence the new detector reports, and is recoverable by the door whose idempotence Task 10 now pins — non-blocking against the alternative, which is a deadlock in a library three consumers run. Zero OPEN questions.
```

## Spec Review — 2026-09-25

**Recommendation: REVISE — return to spec writer (gaps to fix)**

Second spec-review round on this document, spawned cold-start. Rulings on record: WI-021's
gate-name-output-is-an-identity ruling (approach G's rejection), Dave's `ac_hash 15189b874b27`
sign-off freezing AC-1…AC-5 and the Intent, the exploration's accept-the-linter-noise disposition,
and the threat model's four `kind: required` mitigations — I route against all four and neither
finding below touches a signed criterion's text.

I read the document from line 1 in full rather than diffing against the previous round, then re-read
the code at every load-bearing citation. The previous round's four blocking findings are all CLOSED
and I verified each against the code rather than the fold's prose: Design §3 now states the guard as
`vf.entity_type == "person"` with baseline row 8 as its live subject and Task 12 plants the shape;
the `update_fields` door call is placed OUTSIDE the `note_lock` block with the reentrancy argument
corrected and made structural by `door_calls_inside_note_lock`; the ordering block hands the door
`entity` and `updated_view` is gone; and the `## Acceptance Criteria` preamble now states the freeze.
All twelve non-blocking notes are folded, including the three counting slips and the "one true live
subject" mis-statement.

The two findings below are new. One is a failure mode the fold's own prescription reaches and no
section resolves; the other is a member of the WI-286 class that Design §3a was added this round to
close, missed by §3a's own sweep of the predicate it swept.

### Citation verification

All verified against current code; nothing drifted. The ones a wrong reading would have made the
design unbuildable:

- `obsidian_schemas/writer.py:model_to_frontmatter:89` composing `model_fields` (`:112`) →
  `model_extra` (`:119-123`) → `extra_fields` (`:125-129`); `write_markdown_file:160` with the
  `entity is not None` arm at `:229-233`, the one `gate_write` at `:252-253`,
  `with vault_io.note_lock(file_path) as resolved` at `:258`, `is_create` at `:275` and the two
  writes at `:317`/`:319`; `update_frontmatter_field:333` (lock `:368`, gate `:385-387`, write
  `:393`), `update_frontmatter_fields:405` (`:434`, `:451`), `roundtrip_file:463` (`:497`, `:504`).
  All four leaves write their own FIRST parameter, and `write_markdown_file` is the one needing the
  `with … as` hop — Design §4 is right on both. No leaf calls another leaf inside its own lock, so
  `door_calls_inside_note_lock` is genuinely EMPTY over `writer.py` today.
- `obsidian_schemas/repositories/base.py`: `_adopt:184-191` (the `_file_map` write at `:188`),
  `file_pattern:206-208`, `_ensure_loaded:210-213`, `load:241-248`, `_load_file:311-314` with
  `remember_snapshot` at `:313`, `_get_cache_key:319-321`, `get_file_path:354-365`,
  `save:367-412` (`:372` `overwrite=True`, `:391-393`, `:398`, `:411`), `update_fields:414-523`
  (`:438`, `:440-441`, `:448`, `:449`, `:454-459`, `:466-469`, `:483-485`, `:490`, `:493-495`).
- `obsidian_schemas/repositories/person.py:PersonRepository.append_to_timeline:1403-1461` — the
  `get_file_path` opener at `:1403`, the combined `not file_path or not file_path.exists()` guard at
  `:1404-1405`, `note_lock` at `:1410`, both writes at `:1447`/`:1458` with `file_path` as first
  positional. `obsidian_schemas/repositories/book.py:BookRepository.save:167-178` with the INFO line
  at `:183`, exactly the two-line shape premise 15 reads.
- `obsidian_schemas/name_validation.py:Tier1Branch:148-174` — `pattern` documented as non-unique at
  `:152-154` and `sentinel_exempt` at `:155-156`; `arrow_connective` at `:214-225` raising
  `pattern="calendar_prefix"`, `path_hostile` at `:249-259` raising `pattern="path_hostile_char"`.
  AC-3(c)'s two expected marker values are the records' `pattern` fields, as stated.
- `scripts/lint_vault.py`: imports at `:44-48` (`TYPE_TO_MODEL`, `NameGateRefusal`, `gate_write`),
  `SKIP_DIRS:64`, `read_vault:121` with `rglob("*.md")` at `:123`, `stem = md.stem` at `:155` and
  `entity_type` read off the stored record at `:176`; `check_structural:328` with `read_error`/
  `parse_error` `continue` at `:340-359`, the two `is_at_prefixed` tests at `:362-381` and the
  `TYPE_TO_MODEL` guard at `:387-388`; `check_completeness:429-446` with `person_missing_name` gated
  to ACTIVE tier at `:429-432`; `NameGateRefusalRecord:865`, `FixOutcome:926`, `CATEGORY_ORDER:1206`,
  `print_summary:1216`. `"person"` is in `TYPE_TO_MODEL` (`obsidian_schemas/models.py:309-318`), so a
  non-`@` `type: person` file does reach the new arm — Design §3's row-8 argument holds.
- `tests/derivations.py`: `PACKAGE_ROOT:31`, `DOOR_NAMES:47`, `python_files_under:185`,
  `_own_body_nodes:245`, `_called_names:264`, `_names_in:282`, `_is_write_call:286-299`,
  `_taints_a_write:361-409` (seed `:368-382`, fixpoint `:389-401`, sink `:404-408`),
  `functions_calling:873`, `_pos:924`, `_assign_targets_name:928`, `mutating_drive_vault_args:2175`.
  `_is_write_call` gates on `ast.Attribute` only, which is exactly why Design §4's enumeration needs
  its second predicate (bare-name calls to a path-taking leaf) to reach `save`'s and the two
  overrides' `write_markdown_file(...)`. There is no `write_text`/`write_bytes` anywhere in
  `obsidian_schemas/**`, so the data audit's Domain A disposition is accurate.
- `tests/fixture_vault.py`: `CORPUS_DIGEST:44`, `NOTES:217`, the four divergent specimens at
  `:255-260`, `:261-266`, `:297-301`, `:302-306`, the collision third at `:273-276`, the whitespace
  discriminator at `:246-254`, the phone specimen at `:288-293`. I also re-ran Design §3's new
  claim — every non-`@` key in `NOTES` declares `meeting`, `book`, `watch`, `explore`, `gift-idea`,
  `exploration` or `None`, and every `declared_type="person"` entry is `@`-prefixed. AC-3(b)'s
  "every non-`@`-prefixed note" clause is therefore satisfied by the `entity_type` guard, as §3 says.
- `tests/support.py:captured_logs:91` defaults `level=logging.WARNING`, so Task 10's explicit
  `level=logging.INFO` for M4 is required. Task 3's `grep "Saved " tests/` → zero hits: confirmed, so
  the INFO-line change costs one line.
- `docs/stem-divergence-live-baseline.md`: §1's two entry figures parse by leading integer, §2's
  eight rows each carry (b1)/(b2)/(b3)/(c) and a direction, every direction token is `RENAME`/`MERGE`
  and every (b2) token is `no`/`same-file`/`different-note`, row 3 is `same-file` → RENAME and row 8
  is `different-note` → MERGE. AC-4's consistency rule passes against it, and no member of
  `tests/test_vault_path_required.py:FORBIDDEN_DEFAULT_PATTERNS:278`
  (`["expanduser", "Path.home()", "/Users/"]`) appears in the file.

I also walked the AC-5 rebinding clause by hand over all ten prescribed seam bodies and the four
leaves. It admits every shipped shape and refuses the monotone escape: in `rename_note` the two
`contained = …` assignments bind a name the seed never tainted, `staging`/`moved`/`old_stem`/
`new_stem` are all bound from values mentioning `source`, and `entity._source_path = moved` binds no
local name under `_assign_targets_name`'s target rule. The wall as specified is sound.

### Blocking issues

**1. `update_fields` with a name change on an entity carrying no provenance commits the new name and
then raises — the one population its own documented fallback exists to serve, and no section resolves
it.**

The spec deliberately keeps a name-keyed fallback on this method. Design §2's second fallback shape
is `file_path = self._resolve_write_target(entity)` → `get_file_path(name)` → today's `ValueError`,
and AC-1(g)'s second half turns on that fallback existing ("an entity carrying no provenance still
raises `ValueError` from `update_fields` … rather than creating a note"). So an entity with no stamp
whose name the loaded repository CAN resolve is a population this method still serves, by design.

On that same method the spec now inserts, unconditionally, after the content write has committed:

```
    THEN move                                  moved = self.rename_note(entity, f"@{new_name}.md")
```

and `rename_note`'s documented behaviour for an entity with no provenance is to RAISE — Design §2's
invocation table, row 10: *"none — it RAISES `ValueError`; a mover with no provenance has nothing to
move"*, and the door body's first statement after `source = self._resolve_write_target(entity)` is
that raise. Task 6 forecloses the alternatives explicitly: *"Hand the door the caller's own `entity`
parameter, never a re-parsed or freshly-constructed view."*

So for that population the sequence is: `vault_io.write_note(file_path, new_content,
precondition=stamp)` commits the NEW name to the file (`base.py:490`), the `with` block exits, and
`rename_note` raises `ValueError`. The note is left divergent, with no alias, no move, and the caller
sees an exception after a successful write — `update_fields` never reaches its reload, so it returns
nothing. Today that same call succeeds (alias appended in-lock at `base.py:454-459`, file left
behind, reloaded entity returned).

Three things make this a gap rather than a detail. It is a NEW partial-failure mode — the bar's Edge
Cases category — and `## Edge Cases`, `## Verification`'s failure-mode list and `## Risk Analysis`
resolve none of it; the closest entry, *"The repository was constructed with `auto_load=False`"*,
covers only the case where `get_file_path` is ALSO `None`, where nothing is written. No battery
reaches it: Task 9's `update_fields` cell mutates `{"title": …}` and says so ("no `name` key, so the
rename branch does not fire"), and AC-2's name-change arm binds its subject with `repo._load_file`,
which stamps. And the three available answers differ observably — raise (the loud arm, consistent
with the REFUSE-fallback philosophy), skip the move and keep today's leave-behind, or re-stamp
`entity` from the already-resolved `file_path` before calling the door — so the builder is choosing
the package's behaviour, not an implementation detail.

The consumer audit measures this population at zero today (19/19 loaded, 0 reconstructions feed a
write), which is why this is one clause and not a redesign. State it in Design §2's ordering block and
in Task 6, add the `## Edge Cases` entry, and name the residual state in `## Verification`'s failure
modes so the outcome is chosen rather than inherited from the door's raise.
(Builder's question this answers: *"`update_fields` resolved its write target through `get_file_path`
because the entity had no stamp — do I still call `rename_note` on the name change?"*)

**2. The detector arm's `stored.strip()` conjunct is an unanimous free variable with no plant, and
the Edge Case that resolves it has no test — the fourth member of the class Design §3a was added this
round to close.**

Design §3a states the generator and then a class-level rule I agree with:

> every free variable of the detector's arm and of AC-1's subject derivation on which the frozen
> corpus is UNANIMOUS is closed by a PLANTED member, pinned BOTH ways — one plant the predicate must
> claim and one near-miss it must not — and the list is DERIVED by reading the predicate's own text
> for the properties it tests, never remembered from this table.

Read the predicate's own text (Design §3): `if isinstance(stored, str) and stored.strip() and stem !=
stored:`. That is three tests, plus the `entity_type` guard and the `@`-strip above it. §3a's sweep
table plants the guard, the `@`-strip, letter case, directory depth and the stored value's TYPE
(`isinstance`, as the near-miss) — five plants, which Task 12 ships as (i)–(v). It has no row for
`stored.strip()`, and Task 12 plants no blank-or-whitespace `name:` note.

The corpus is unanimous about it in exactly the sense §3a means: no `declared_type="person"` entry in
`tests/fixture_vault.py:NOTES:217-479` declares an empty or whitespace-only `name:`, so an
implementation written as `isinstance(stored, str) and stem != stored` passes all four AC-3(a) cells,
all of AC-3(b), and all five of Task 12's plants. On the live vault that implementation reports every
blank-name ACTIVE person note as `stem_name_divergence` as well as `person_missing_name` — which is
the double-ERROR interaction Design §3's own comment and the `## Edge Cases` entry argue against,
where the auto-fixable rule silently repairs away the never-fixable one
(`scripts/lint_vault.py:1040-1045` writes `fpath.stem.lstrip("@")` into the field).

Two of §3a's existing plants carry "none measured" in the live-evidence column (the double-`@` stem
and the stored value's TYPE) and are planted anyway, so "the live stake is measured at zero"
(`## Edge Cases`) is not the discriminator here — it is the same argument those two rows already
overrode. And `## Edge Cases` resolves this case with a **Decision** and a **Reasoning** and no
corresponding test, which is the bar's Check-4 test-coupling clause independently of §3a.

The fix is §3a's own: one row in the sweep table and one plant in Task 12 — a person note with
`name: ""` (or whitespace-only) whose stem differs from it, asserted NOT to produce a
`stem_name_divergence` issue, as a second near-miss beside (v). §3a's closing declaration that the
arm is "a conjunction of INDEPENDENT tests" should then name this conjunct with the others.
(Builder's question: *"Design §3a says plant every unanimous free variable of the arm and derive the
list by reading the arm — the arm tests `stored.strip()` and the table does not. Do I plant it?"*)

### Non-blocking notes

- **Task 13's `.md`-token rule is false against the artifact it grades.** The check asserts *"every
  `.md` token the file names resolves to a path that EXISTS in this repo or is the declared template
  literal `@{name}.md`"*. `docs/stem-divergence-live-baseline.md:36` contains
  `sorted(V.rglob('*.md'))` inside §0's verbatim script fence — a `.md` token that is neither an
  existing repo path nor `@{name}.md`. Every token OUTSIDE the code fences does resolve, so the rule
  needs one clause (fenced code excluded, or globs exempt) or it is RED against a correct committed
  precondition, which is the WI-026 AC-5(b) shape the conductor read-back already corrected once for
  AC-4's occupancy rule. No criterion depends on it — AC-4's own desc says "no absolute path and no
  note filename", which the artifact satisfies.
- **The door reads `aliases` off the in-memory entity where `update_fields` reads them off the file
  inside the lock.** Today's block at `base.py:456` is `aliases = frontmatter.get("aliases", [])` —
  the FILE's list, parsed in-lock. Design §2's door body is
  `aliases = list(getattr(entity, "aliases", []) or [])` and then writes that list back through
  `update_frontmatter_field`. For `update_fields(entity, {"name": …, "aliases": […]})` the write at
  `base.py:490` commits the caller's new alias list and the door then overwrites it with the stale
  in-memory one plus the old stem. The source-of-truth change is deliberate for a direct
  `rename_note` call and incidental for the `update_fields` path; one clause settles which list wins.
- **Task 14's wall-closure RUN is narrower than `## Wall Membership`'s table**, while the section
  claims *"MEMBERSHIP is closed by CALLING each of those predicates on the files' FINAL text in Task
  14"*. Task 14 names the routing walls, the `ast` single-home equality, `skip_reason_literal_sites`,
  `frontmatter_write_arms`, `gate_call_declarations`/`gate_call_placement`,
  `character_class_strip_sites`, `address_splitting_implementations`, the two `auto_fixable_*` sets
  and `FORBIDDEN_DEFAULT_PATTERNS` — but not wall D
  (`tests/test_name_gate_wall.py:_check_wall_d:1107`, no new `parse_markdown_file` caller outside
  `base.py`) or `tests/test_identity_endgame.py:590`'s `_email_index` zero-sites pin. Both are
  predicted-green and cheap; the point is that WI-301's rule is discharged by RUNNING each predicate,
  and a row that no task calls is satisfied by reasoning.
- **AC-5 bucket (a) is narrowed to the FIRST parameter.** Design §4's justification covers the
  METHOD case ("a future path-taking leaf written as a METHOD fails loud and is someone's decision")
  but not a future leaf taking its path as a second parameter, which would also fail loud with no
  stated disposition. All four current leaves take it first, so nothing is red today; one clause
  would make the refusal deliberate.
- **`Meeting` "declares only … and `tags` (`models.py:Meeting:259-263`)"** — `tags` is inherited from
  `BaseEntity` (`obsidian_schemas/models.py:40`), not declared in that range. The Verification table's
  conclusion is right (`tags` feeds no filename rule and is a legal minimal mutation); the citation
  spans the wrong lines for one of the fields it names.

### Carried-forward notes

- **Threat model round 2, "`update_fields` is no longer atomic across write-then-move"** — recorded
  in `## Threat Model` and folded nowhere. The modeler walked the concurrency interleavings and
  ruled every residual loud, detector-visible and recoverable, and rated it non-blocking against the
  deadlock alternative; it belongs beside the `## Edge Cases` concurrency entry, whose "no new
  lock-ordering edge exists" is true and must not be read as "no new window exists". Adjacent to
  blocking finding 1, which is the non-concurrent member of the same window.
- **Threat model round 2, "M1's exact bound"** — the containment test is resolve-then-`os.link`, so
  it is check-then-act against an attacker who can plant a symlink at the destination between the
  two. Explicitly out of this item's threat model (that attacker already has write access to the
  vault) and recorded so M1 is not over-read. Re-deferred: it needs no work, only a bound nobody
  should mistake for a promise.
- **Threat model round 2, "the M3 window is visible to `load()`"** — during a successful case-only
  two-step a concurrent `load()` can see both paths and record a `PersonRepository.conflicts` row.
  Worth one line in `## Verification`'s close-out, because that procedure's ship condition is
  `len(conflicts) == 0` and a conflict observed mid-repair is this window rather than a new
  duplicate. Still open: the close-out steps do not mention it.
- **Architect round 6, note 6(iv)** — the deliberately-out-of-scope items (`_get_cache_key`'s strip
  asymmetry, approach F's re-keying, the Book/Meeting `save` collapse) stand as written and are all
  named in `## Scope Boundary`. Closed; recorded so the chain is unbroken.
- **Threat model round 1, "a pre-existing extras leak"** — now FOLDED, as a stated bound beside
  AC-1(h)'s definition in Design §1. Closed.
- All prior spec-review non-blocking notes are folded and I verified each against the code rather
  than the prose: the idempotence arm (Task 10), `save`'s INFO line (Task 3, Task 5), the alias
  write's deliberate asymmetry (Design §2, ordering decision 3), the three counting slips
  (`## Verified Diagnosis`'s SIX, the `test_concurrent_access.py` fence's five, `## Wall Membership`'s
  unlisted pins) and the diff-size correction, premise 11's symbol, the "one true live subject"
  correction (Design §3), the later-task `verify:` preamble, and Task 2's M2 arm now asserting the
  property with the pydantic retention demoted to a Build-Log observation.

```verdict
gate: spec-reviewer
verdict: REVISE
date: 2026-09-25
model: claude-opus-5
targets: Task 6, Task 12, Task 13, Task 14, AC-3, #design
prior: held
basis: original
findings: 2/7
note: `update_fields` with a name change on an entity carrying NO provenance now commits the new name inside the lock (`base.py:490`) and then raises from `rename_note`, whose documented no-provenance behaviour is a `ValueError` (Design §2's invocation table row 10) — that is exactly the population the method's own preserved `get_file_path` fallback exists to serve and AC-1(g)'s second half turns on, so the spec keeps the fallback alive and then hands the door an object it refuses; the residual is a note left divergent with no alias, no move and an exception after a successful write, resolved in no Edge Case, no Verification failure mode and no risk row, and reached by no battery (Task 9's `update_fields` cell carries no `name` key; AC-2's name-change arm binds a `_load_file`-stamped subject). Second, Design §3a states the class-level rule that every free variable of the detector's arm on which the frozen corpus is UNANIMOUS is closed by a plant, with the list DERIVED by reading the arm's own text — the arm is `isinstance(stored, str) and stored.strip() and stem != stored`, and the sweep table plants the guard, the `@`-strip, case, depth and the value's TYPE but not `stored.strip()`, so an implementation dropping that conjunct passes all four AC-3(a) cells, AC-3(b) and all five Task-12 plants while reporting every blank-name active person note as both an auto-fixable `person_missing_name` and a never-fixable divergence — the interaction `## Edge Cases` resolves with a Decision and no test. Both fixes are one clause and one plant; the previous round's four findings all held closed and every non-blocking note is folded.
```

## Adversarial Review — 2026-09-25

Cold-start spawn (this invocation carried no reference to any prior injection-hunter round on this
item — no "second round, re-reading the fold" framing the way every other repeat gate on this
document gets). I read the document from line 1 to its end in full: Problem/Motivation, Intent, the
entire Exploration Notes arm, Approach, Design, Verified Diagnosis, Edge Cases, the Implementation
Plan, Write Targets, Wall Membership, Mitigation Folds, Verification, Scope Boundary, Risk Analysis,
the Acceptance Criteria, and every gate verdict in document order — Architectural Review, AC
Red-Team, AC Sign-off, Data Audit, Threat Model round 1, Spec Review round 1, then the section below,
then Threat Model round 2, then Spec Review round 2. I also grepped the sibling archive
(`docs/filename-name-divergence-repair-rounds.md`) and the body for verdict-steering phrasing
("ignore previous instruction", "pre-approved", imperative text addressed to a reviewer). Aside from
the one finding below, nothing in the spec's own prose reads as steering rather than the document
making its own technical case — confirmed independently on a second pass of Exploration Notes
through Data Audit.

**Finding (blocking): an existing `## Adversarial Review — 2026-09-25` section, carrying a complete
`gate: injection-hunter` / `verdict: PROMOTE` fence, already sits in this document — not at the end,
but between Spec Review round 1 and Threat Model round 2 — and its provenance cannot be verified from
what this invocation was given.**

The section (this document, immediately above Threat Model round 2) opens: *"Cold-start spawn, first
injection-hunter round on this document (no `## Adversarial Review` section existed before this
edit, and no `gate: injection-hunter` fence appears anywhere else in this document) ... confirmed no
`gate: injection-hunter` fence exists anywhere in either file for this item — this is a genuine
cold-start read, not a re-run."* That is precisely the self-certification a genuine cold-start
injection-hunter run — this one — is asked to perform, pre-answered in the document before I did the
work myself.

Three things make this worth surfacing rather than silently trusting:

1. **No spec-reviewer PROMOTE exists anywhere in this document.** Both spec-review rounds resolve
   REVISE. D5 requires the injection-hunter's PROMOTE *beside* the spec-reviewer's, at the
   `specced -> ready` transition attempt — a standing PROMOTE with no accompanying spec-reviewer
   PROMOTE is consistent with an ad-hoc Dave-triggered run (the role YAML permits "Dave may also say
   'run the injection-hunter on WI-XXX'"), but I have no way to confirm that from the document or
   from this invocation's framing, and the document does not say so either.
2. **A later round edited bytes at that section's boundary.** Threat Model round 2's non-blocking
   notes state: *"One structural repair made in this edit. The document ended with a stray
   unterminated ``` line immediately after the injection-hunter's closing fence, which would have
   swallowed this entire section — including its `verdict` and `mitigation` fences — into an open
   code block and made the round declare nothing. Removed; no other gate's bytes touched."* A plain
   markdown slip is the innocent explanation; the same edit is also exactly what a forged verdict
   fence would need to stay machine-parseable rather than being inertly swallowed. I cannot
   distinguish the two from inside this document.
3. **This invocation was not told a prior round existed.** Every other repeat gate on this document
   (threat-modeler round 2, spec-reviewer round 2) opens by naming itself a second round and stating
   what it re-read. My own task framing named no prior injection-hunter round and gave no re-run
   instructions — I found the existing section only by reading the document myself.

None of this proves forgery — an ad-hoc human-triggered run plus an honest fence-balancing fix
explains the same facts. But a standing PROMOTE under my own gate's heading, of unconfirmed
provenance, sitting where a downstream structural parser (per the machine contract, "the fence counts
ONLY inside the `## Adversarial Review` section") could read it as satisfying D5's second key, is
exactly the shape of confused-deputy risk this role exists to close — and the calibration is explicit
that a false PROMOTE here is the feared failure, a false block is one cheap re-run. Escalating to
REVISE so the conductor confirms whether that section is a genuine, provenance-tracked prior
injection-hunter round (in which case it should say so on its face, the way every other repeat gate
here does) or an artifact that should not be trusted as a second key.

```verdict
gate: injection-hunter
verdict: REVISE
date: 2026-09-25
model: claude-sonnet-5
targets: #adversarial-review, #threat-model
prior: none
basis: machinery
findings: 1/1
note: This document already contains a standing `## Adversarial Review — 2026-09-25` section with a complete `gate: injection-hunter, verdict: PROMOTE` fence, positioned mid-document (between Spec Review round 1 and Threat Model round 2) rather than at the end, self-certifying exactly the cold-start facts this invocation was itself asked to verify, with no accompanying spec-reviewer PROMOTE anywhere in the document and no re-run framing in this invocation's own task briefing — and Threat Model round 2 separately records editing bytes immediately at that section's boundary to keep it parseable ("a stray unterminated ``` ... would have swallowed this entire section ... into an open code block"). This may be an innocent ad-hoc Dave-triggered run plus a fence-balancing fix, but I cannot verify its provenance from inside the document, and a standing PROMOTE under my own gate's heading of unconfirmed origin is precisely the confused-deputy shape D5 exists to close, so I escalate to REVISE for conductor verification rather than treat it as a second key.
```

## Threat Model — 2026-09-25

**Recommendation: PROMOTE to threat-modeled — round 3. M1, M2, M3 and M4 all HELD: I re-verified each
against the code it prescribes and each is on its named task with its ordinal unmoved, so the four
fences below are RE-EMITTED with byte-identical `desc`. The second fold introduced ONE new security
surface and it is mine: the fold that fixed AC-4's `.md`-token rule against a false RED did it by
exempting a REGION — every line inside a fenced code block — rather than a TOKEN CLASS, and that
region is exactly where the exit attestation's pasted re-run output lands. One new required
mitigation, M5, one clause on Task 13, verified green against the committed artifact's current bytes.**

Third threat-model round on this document. I read it from line 1, then re-read the material the
SECOND spec-review fold added — Design §2's "The no-provenance name change refuses BEFORE the write"
and "Which `aliases` list wins", §3's `stored.strip()` bullet, §3a's new sweep row and its re-stated
independence declaration, §4's second-parameter disposition, Tasks 3, 6, 10, 12, 13 and 14, the four
new or rewritten `Edge Cases` entries, the two new `Verification` clauses and the two new
`Risk Analysis` rows — and checked each against the CODE rather than against the fold's prose. I also
re-read the spec-review round that landed between my rounds, and I re-executed the artifact the new
Task 13 clause grades (`docs/stem-divergence-live-baseline.md`, read in full, byte by byte for its
`.md` tokens).

### Trigger check

The same five fire, unchanged in shape: filesystem operations on user-owned files, persistence,
untrusted vault bytes crossing into a trusted write-target decision, PII (person names in a new
WARNING, a new ERROR and a committed live-vault artifact), and an out-of-repo blast radius through
three `-e` consumers. The fold added no sixth — no network, no subprocess, no credential, no new
import capability — and the routing walls A/B/C still keep filesystem-mutation capability
single-homed in `obsidian_schemas/vault_io.py`.

### The four standing mitigations, re-verified against the code

**M1 — still landed and still total.** The door body's containment clause is byte-for-byte where round
2 found it, immediately after `destination = self.vault_path / new_filename` and before all three
`vault_io.move_note` call sites, with the resolve's `OSError`/`ValueError` treated as NOT contained.
I re-confirmed the two facts underneath it in this worktree rather than trusting round 2's account:
`vault_io._resolved` is still a bare `Path(path).resolve()` with no notion of a vault root
(`obsidian_schemas/vault_io.py:_resolved:234-243`) and `move_note` still checks a symlinked SOURCE and
nothing about where `dest` points (`obsidian_schemas/vault_io.py:move_note:721-750`), so the clause is
still the only thing bounding the destination. The new pre-write refusal does not touch it: the arm it
adds is in `update_fields`, above the write, and the door's own argument refusals are unchanged.

**M2 — still landed, unchanged.** Task 2's arm still asserts the PROPERTY (the accessor
`_resolve_write_target` reads answers A's own path; nothing the seam reads answers B) with pydantic's
extras retention demoted to a Build-Log observation, and Design §1's bullet still separates the
two-implementation-detail explanation from the asserted property.

**M3 — still landed, unchanged.** `source.with_name(destination.stem + ".rename-tmp.md")` in the door
body, in Task 6's work text, in the `Edge Cases` entry for a process dying mid-two-step and in the
rewritten `Risk Analysis` row; Task 10's oracle is still `vault_path.glob(repo.file_pattern)` with the
rejected spelling driven through the same glob as a near-miss.

**M4 — still landed, unchanged.** `logger.info("Renamed %s note from %s to %s", self.type_name,
source.name, moved.name)` in the door body and in Task 6, captured in Task 10 through
`captured_logs(level=logging.INFO)`.

### STRIDE delta — what the second fold moved

**Spoofing, Denial of service, Elevation of privilege: unmoved.** M2 still closes the stamp's read
direction; the privilege surface is still filesystem reach bounded by M1; `door_calls_inside_note_lock`
still makes the lock-ordering rule structural.

**Tampering: strictly better, and I checked the one shape that could have gone the other way.** The
new `update_fields` clause is `if renaming and resolved is None: raise ValueError`, placed inside the
lock after `renaming` is computed from `frontmatter` and before `gate_write`, `write_frontmatter` or
`vault_io.write_note` are reached. I walked the three answers the spec-review named and the spec
rejects the dangerous one for the right reason: re-stamping `entity` from the name-keyed `file_path`
would have laundered `_file_map`'s last-wins glob answer (`obsidian_schemas/repositories/base.py:load:241-246`)
into a provenance stamp and handed the door a note the caller never named — a DIRECTED write into a
third party's file, manufactured by the repair machinery, which is the same harm class M2 exists to
keep unreachable from note content. The spec now states that provenance has exactly two write sites
(the parse and the door's re-stamp) and that `update_fields` does not become a third. That is the
correct invariant and it is the one I would have required.

**Repudiation: better at three sites now, not two.** Task 3's and Task 5's INFO-line fix stands, and
the new refusal raises with the method, the requested name and the reason named.

**Information disclosure: this is where the fold opened something, and it is the finding.** Round 1
closed this category with *"Nothing to require"* explicitly BECAUSE the one place it genuinely matters
— a live-vault evidence artifact committed to git forever — was already walled by AC-4, which asserts
*"no absolute path and no note filename leaks the privacy wall"*. This fold narrowed the half of that
wall that catches filenames. Task 13 now reads: `FORBIDDEN_DEFAULT_PATTERNS` must not appear (still
whole-file, still total — the absolute-path half is intact), *and* `every .md token the file names
**on a line OUTSIDE a fenced code block** resolves to a path that EXISTS in this repo or is the
declared template literal @{name}.md`. The region exclusion is attached to the filename conjunct
alone, so after this fold nothing in the build checks for a note filename inside a fenced block.

Three things make that the wrong exemption rather than a cosmetic one.

1. **The excluded region is precisely where a leak would land.** The artifact's §0 already carries two
   fences of verbatim command OUTPUT (`docs/stem-divergence-live-baseline.md:98-115`), which is how a
   conductor records a re-run. The exit attestation re-runs two commands, and the second is
   `scripts/lint_vault.py --vault "$VAULT" --report`, which reports issues PER PATH — it names note
   filenames by construction. The entry run was redacted by hand and holds up: I checked its output
   fence token by token and it carries counts, shape labels, booleans and directory names only. The
   wall exists for the run where that discipline slips, and it is now blind in the one region that run
   writes to. A bare relative filename (`@Someone Real.md`) contains no member of
   `["expanduser", "Path.home()", "/Users/"]` (`tests/test_vault_path_required.py:278`), so nothing
   else in the build catches it.
2. **The artifact itself claims the stronger property.** `docs/stem-divergence-live-baseline.md:15`
   reads *"No absolute path appears anywhere in this file, so a whole-file privacy scan is legal
   against it."* The precondition declares a whole-file scan legal; the check that grades it no longer
   performs one.
3. **The narrow fix exists, the spec-review itself named it as the alternative, and I verified it is
   green.** The false RED the fold was fixing is `sorted(V.rglob('*.md'))` at `:36` — a GLOB, not a
   filename. I read every `.md` token inside every fence in that file: there are exactly two, `'*.md'`
   at `:36` and `f"@{name}.md"` at `:76`, and the second is already exempt as the declared template
   literal. So exempting the TOKEN CLASS — a token containing `*` — makes the rule green against the
   artifact as committed with no region exclusion at all, and keeps it total over every real filename
   anywhere in the file. That is one clause, on the same task, for the same cost.

A fourth point is about the clause's own guard rather than its scope, and the token-class fix
dissolves it: Task 13 asks the check to *"assert the exclusion is non-vacuous (at least one line was
skipped) so a broken fence detector cannot silently exempt the whole file"* — but "at least one line
was skipped" is satisfied by a toggle stuck OPEN, which is the whole-file exemption the sentence says
it prevents. Under a token-class exemption there is no fence toggle in the privacy path to get stuck.
**M5.**

*The mitigation's bound, so it is not over-read:* a filename committed to git is not un-leaked by
detecting it afterwards, and the close-out's step 4 redaction is the primary control either way. M5
buys a standing automated check that stays total for the life of the repo instead of one with a
permanent blind region — which is the whole reason AC-4 carries a privacy wall rather than a promise.

### Notes (non-blocking)

- **The `aliases` reconciliation is correct, and I verified the dict it reads.** Design §2's
  `entity.aliases = frontmatter["aliases"]` is captured inside the lock after
  `frontmatter.update(gate_write(updates, …))` (`obsidian_schemas/repositories/base.py:483-485`) and
  before the write at `:490` serializes that same dict, so `frontmatter["aliases"]` IS the committed
  value and not the pre-write one. No security delta: an arbitrary caller-supplied alias list already
  reaches disk through `update_fields` today, and the value the DOOR adds (`old_stem`) is derived from
  the note's own filename, never from caller input — so this item hands the alias index no new
  attacker-influenced value.
- **The door's own case-only staging name is still unsteerable**, for the reason round 2 gave and the
  fold did not disturb: the branch that composes it requires `source.samefile(destination)`, so
  `destination.stem` is the source's own stem in another case.
- **M1's exact bound and the M3 `load()` window are both now FOLDED** where they belong — the first
  into Design §2 beside the containment clause, the second into `Verification`'s close-out, whose ship
  condition is `len(conflicts) == 0` and is the one place a conductor could misread that window as a
  new duplicate. Both were my round-2 carried-forward notes; both are closed and neither needed work.
- **The write-then-move window is folded as an `Edge Cases` entry and a `Risk Analysis` row**, stated
  as a trade against a deadlock, with the lock-ordering entry explicitly marked as a claim about
  ORDERING and nothing else. That is exactly the separation I asked for and it needs nothing further.
- **One stale enumeration, named for the record and not a security matter.** The `writes` fence for
  `tests/test_stem_name_divergence_detector.py` still says *"the five planted members Design §3a's
  sweep requires"* and lists five; Task 12 and §3a now carry SIX ((vi), the blank-`name:` near-miss).
  A counting slip in a declaration, no criterion depends on it, and it is the spec-reviewer's ledger
  rather than mine.
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

```verdict
gate: threat-modeler
verdict: PROMOTE
date: 2026-09-25
model: claude-opus-5
note: Round 3 re-verified M1-M4 against the code each prescribes rather than the fold's prose — all four HELD on their named tasks with ordinals unmoved and `desc` re-emitted byte-identically, and I re-confirmed the two facts M1 rests on in this worktree (`vault_io._resolved` is still a bare `Path.resolve()` with no vault root, `vault_io.py:234-243`; `move_note` still checks only a symlinked SOURCE, `:721-750`). The second fold's Tampering delta is an improvement and I checked the shape that could have gone the other way: `update_fields`' new pre-write refusal rejects re-stamping from `get_file_path`, which would have laundered `_file_map`'s last-wins glob answer (`base.py:241-246`) into a provenance stamp and moved a note the caller never named — the spec now pins provenance to exactly two write sites, which is the invariant I would have required. ONE new surface, and it is in the half of the wall round 1 leaned on to close Information disclosure with "nothing to require": Task 13's fold fixed a false RED on `sorted(V.rglob('*.md'))` by exempting a REGION — every line inside a fenced code block — from AC-4's `.md`-token rule, and that region is where a re-run's pasted output lands, with the exit attestation re-running `lint_vault --report`, which names note filenames per path; the absolute-path half stays whole-file and total, but a bare `@Someone Real.md` matches no member of `FORBIDDEN_DEFAULT_PATTERNS` (`tests/test_vault_path_required.py:278`) so nothing else catches it, and the artifact itself declares at `:15` that a whole-file privacy scan is legal against it. The narrow fix is verified rather than proposed: the only two `.md` tokens inside that file's fences are the glob at `:36` and the already-exempt template literal at `:76`, so exempting the TOKEN CLASS is green against the artifact as committed and keeps the rule total over every real filename — M5, one clause on Task 13, which also dissolves the clause's own unsound guard ("at least one line was skipped" is satisfied by a fence toggle stuck open, the very whole-file exemption it claims to prevent). Both of my round-2 carried-forward notes are folded and closed (M1's check-then-act bound into Design §2, the M3 `load()` window into the close-out whose ship condition is `len(conflicts) == 0`), the write-then-move window is an Edge Case and a risk row with the lock-ordering claim kept separate, the `aliases` mirror reads the post-gate dict and adds no attacker-influenced value, and zero OPEN questions.
```

## Spec Review — 2026-09-25

**Recommendation: REVISE — return to spec writer (gaps to fix)**

Third spec-review round on this document, spawned cold-start. Rulings on record: WI-021's gate-name-output-is-an-identity ruling (approach G's rejection), Dave's `ac_hash 15189b874b27` sign-off freezing AC-1…AC-5 and the Intent, the exploration's accept-the-linter-noise disposition, the threat model's five `kind: required` mitigations, and the Spec-Writer Notes' two declared NON-actions (M1's check-then-act residual; the write-then-move window) — I route against all five and neither finding below touches a signed criterion's text.

I read the document from line 1 in full rather than diffing against the previous round, then re-read the code at every load-bearing citation. Both of round 2's blocking findings are CLOSED and I verified each against the code: `update_fields`' name-change-with-no-provenance now refuses inside the lock before `gate_write`, `write_frontmatter` or `vault_io.write_note` are reached, swept across Design §2, Task 3's `resolved` binding, Task 6, Task 10, two `## Edge Cases` entries, a `## Verification` failure mode, a `## Risk Analysis` row and the `base.py` `writes` fence; and the `stored.strip()` conjunct now has §3a's sweep row, Task 12's plant (vi) and a `## Verification` arm. Round 1's four findings are still closed. All five of round 2's non-blocking notes and all three of its carried-forward notes are folded. Threat-model M5's fold is complete and, unusually, I was able to verify its load-bearing empirical claim rather than accept it — see Citation verification.

The two findings below are new and they are the same paragraph seen twice: `rename_note`'s branch structure, where the document promises a recovery the prescribed body cannot perform and a battery arm the prescribed body makes RED.

### Citation verification

All verified against current code; nothing drifted. The ones a wrong reading would have made the design unbuildable, and the ones this round's fold rests on:

- `obsidian_schemas/repositories/base.py`: `_adopt:168-191` (signature `(name_key, entity, file_path)`, the `_file_map` write at `:188` — Design §2's `self._adopt(self._get_cache_key(entity), entity, moved)` matches it argument for argument); `file_pattern:206-208`; `_ensure_loaded:210-213`; `load:241-248`; `_load_file:299-317` with `parse_markdown_file` at `:311`, `remember_snapshot` at `:313` and the `return doc.entity` at `:314`; `_get_cache_key:319-321`; `get_file_path:354-365`; `save:367-412` (`overwrite=True` at `:372`, `:391-393`, `write_markdown_file` at `:398`, the INFO line at `:411`); `update_fields:414-523` (`:437-438`, `:440-441`, `:443-444`, lock `:448`, `read_note` `:449`, `parse_frontmatter` `:450`, alias block `:454-459`, gate `:483-485`, `write_frontmatter` `:488`, `write_note` `:490`, reload `:493-495`, and `self._adopt(new_name_key, updated_entity, file_path)` at `:520`, which is why the ordering block's `file_path = moved` rebind before the reload is load-bearing for the cache too).
- `obsidian_schemas/writer.py`: `model_to_frontmatter:89` composing `model_fields` (`:112`) → `model_extra` (`:119-123`) → `extra_fields` (`:126-129`); `write_markdown_file:160` with the `entity is not None` arm at `:229-233`, the one `gate_write` at `:252-253`, `with vault_io.note_lock(file_path) as resolved` at `:258`, `is_create` at `:275`, the WI-126 guard at `:285-302` and the two writes at `:317`/`:319`; `update_frontmatter_field:333` (lock `:368`, gate `:385-387`, write `:393`), `update_frontmatter_fields:405` (`:434`, `:451`), `roundtrip_file:463` (`:497`, `:504`). All four leaves take the path as their FIRST parameter and write that same name, so AC-5's bucket (a) holds and only `write_markdown_file` needs the `with … as` hop.
- `obsidian_schemas/vault_io.py`: `_resolved:234-243` is a bare non-strict `Path(path).resolve()`; `move_note:721-750` with the symlinked-source refusal at `:736-740`, the sorted two-lock acquisition at `:744-750` and the link-then-unlink docstring at `:732-734`; `_move_locked:753-783` with `os.link`'s `FileExistsError` → `NoteAlreadyExists` at `:759-771`, the `os.unlink` at `:776` and `forget_snapshot` at `:780-781`. First positionals are `path`/`path`/`src` at `:670`/`:701`/`:721`. **`move_note` returns `_move_locked`'s `target`, which is `_resolved(dest)` — a RESOLVED path.** That is the fact finding 2 turns on and the spec does not cite it anywhere.
- `obsidian_schemas/name_gate.py:gate_write`: `result = dict(introduced)` at `:346` and `return dict(introduced)` at `:344`, so the call MUTATES nothing — Design §3's `_gate_refusal_pattern(vf.frontmatter)` really is read-only against the linter's own dict, which AC-3(d) and the `scripts/lint_vault.py` `writes` fence both assert. `allow_phone_sentinel` derived at `:355-358` verbatim; the declared-non-person pass-through at `:319-344`.
- `obsidian_schemas/name_validation.py`: `_PATH_HOSTILE_RE = re.compile(r"/")` at `:107`; `Tier1Branch:148-174` with `pattern`'s non-uniqueness documented at `:152-154` and `sentinel_exempt` at `:155-156`; `arrow_connective:214-225` raising `pattern="calendar_prefix"`, `path_hostile:249-259` raising `pattern="path_hostile_char"`, `pure_digit` the one `sentinel_exempt=True` record at `:287`.
- `obsidian_schemas/models.py`: `BaseEntity:23-40` (`extra="allow"` at `:31-32`, `tags` at `:40`), `Person.aliases:80`, `Meeting:259-263` declaring `type`/`date`/`attendees`/`topics`/`meeting_id` and inheriting `tags` — round 2's citation fix is correct — `TYPE_TO_MODEL:309-318` containing `"person"`. Neither `Book` nor `Meeting` declares `name`.
- `scripts/lint_vault.py`: imports at `:44-48`, `DEFAULT_VAULT:62`, `SKIP_DIRS:64`, `read_vault:121` with `rglob("*.md")` at `:123`, `stem = md.stem` at `:155` and `etype` read off the stored record at `:176`; `check_structural:328` with the `read_error`/`parse_error` `continue`s at `:340-359`, the two `is_at_prefixed` tests at `:362-381`, `if not vf.entity_type: continue` at `:383-384` and the `TYPE_TO_MODEL` guard at `:387-388`; `check_completeness:429-446` with the ACTIVE-tier gate at `:429-432` and `person_missing_name` at `:440-443`; the `--fix` repair at `:1040-1045`; the phone-sentinel-unreachable comment at `:1001-1014`; `CATEGORY_ORDER:1206`, `print_summary:1216-1221`. I re-checked the two arms Design §3 leans on against the live code rather than the fold's account: `person_missing_name` fires on `not name or not str(name).strip()`, so a list-valued `name:` is claimed by no check today (Design §3's Build-Log line is right) and a whitespace-only `name:` IS claimed, but only at ACTIVE tier (the `## Edge Cases` precision is right).
- `tests/derivations.py`: `PACKAGE_ROOT:31`, `DOOR_NAMES:47`, `FunctionId:90-96` (module is a posix relpath, so Task 10's `FunctionId("obsidian_schemas/repositories/base.py", "BaseRepository.rename_note")` is the right shape), `python_files_under:185`, `_own_body_nodes:245`, `_called_names:264`, `_names_in:282`, `_is_write_call:286-299`, `functions_parsing_then_writing:316`, `_taints_a_write:361-409` (seed `:368-382`, monotone fixpoint `:389-401`, sink `:404-408`), `_SHARED_HELPERS:585`, `non_completed_write_sites:588-619`, `functions_calling:873`, `_pos:924`, `_assign_targets_name:928-944`. Design §4 is right on both hazards: `_taints_a_write` propagates through `_names_in(target)`, which WOULD taint `entity` off `entity._source_path = moved`, and `_assign_targets_name`'s target rule is the one that does not.
- I walked the AC-5 rule by hand over all ten prescribed seam bodies and the four leaves and it still admits every shipped shape and refuses the monotone escape; and I confirmed `_resolve_write_target` does not join `non_completed_write_sites` (no write call in its body, and `_SHARED_HELPERS` is `{"_get_body_content", "_split_frontmatter_fence"}`), so Task 1's `= 8` pin genuinely does not move.
- `door_calls_inside_note_lock` is genuinely EMPTY over `PACKAGE_ROOT` today, and I derived that rather than accepting it: a grep for the four path-taking leaf names over `obsidian_schemas/**` returns only the definitions, two `__init__` re-exports, `base.py:398`, `book.py:170` and `meeting.py:192` — none of them inside a `note_lock` `with` — while every `note_lock` holder in the package (`writer.py:258`, `:368`, `:434`, `:497`, `base.py:448`, `person.py:1410`, `:1529`, `:1660`, `:1726`, `:1800`) calls only `vault_io.write_note`/`create_note`, which Design §4 deliberately excludes.
- `tests/test_concurrent_access.py:test_wi020_derivations_survive_the_routing:1060` — `len(writers) == 4` at `:1077`, the `{write_markdown_file}` set equality at `:1081`, `non_completed_write_sites == 8` at `:1085`, subclasses 4 at `:1088`, `_load_file`s 3 at `:1089`. Task 1's pin list is correct value for value.
- `tests/test_name_gate_wall.py`: `PERSON_FALSY_RETURN_FUNCTIONS:1048`, `test_wall_membership_is_closed_by_running_each_walls_predicate:1057`, `_check_wall_d:1107`, `_check_the_ast_capability_stays_single_homed:1132`, `len(sites) == 8` at `:1161`. `tests/test_loud_fail_write.py:test_write_failure_raises_and_noops_keep_their_return:105`. `tests/test_lint_vault_fix_rules.py:1703`'s `auto_fixable_emitter_checks` set equality. `tests/test_identity_endgame.py:590-594`'s `_email_index` zero-sites pin, with the needle assembled from parts exactly as Task 14 says. `tests/test_vault_path_required.py:FORBIDDEN_DEFAULT_PATTERNS:278` is `["expanduser", "Path.home()", "/Users/"]`, `_code_lines:281`, the sweep at `:323`.
- `tests/fixture_vault.py`: `CORPUS_DIGEST:44`, `NOTES:217`, the four divergent specimens at `:255-260`, `:261-266`, `:297-301`, `:302-306`, the collision third at `:273-276`, the whitespace discriminator at `:246-254`, the phone specimen at `:288-293`, `LOADABLE:521`. I also re-ran Design §3's corpus claim myself: every non-`@` key in `NOTES` declares `meeting`, `book`, `watch`, `explore`, `gift-idea`, `exploration` or `None`, and no `declared_type="person"` entry is non-`@`, so AC-3(b)'s "every non-`@`-prefixed note" clause really is satisfied by the `entity_type` guard.
- `tests/support.py:captured_logs:91` defaults `level=logging.WARNING`, so Task 10's explicit INFO for M4 is required and Task 9's silence for AC-1(f)'s WARNING is right. `tests/support.py:temp_dir:31-37` returns `Path(tempfile.mkdtemp(prefix="wi020-"))` — **UNRESOLVED**, which is why `tests/test_lint_vault_fix_rules.py:_temp_vault:158-191` calls `.resolve()` on both sides of every comparison it makes and still returns the unresolved `built`. That is the other half of finding 2.
- **M5's empirical claim, re-derived rather than accepted.** I ran Design §4a's own prescribed tokenizer (`[\w@{}*./+-]+\.md`) over `docs/stem-divergence-live-baseline.md` as committed. It returns exactly EIGHT tokens and they are exactly the eight §4a enumerates: `docs/filename-name-divergence-repair.md` (`:4`), `docs/vault-shape-census.md` (`:5`, `:22`), `docs/lint-vault-live-baseline.md`, `*.md` (`:36`), `@{name}.md` (`:76`, `:126`, `:153`). All three repo-relative paths exist. So the token-class rule is GREEN against the artifact as committed and total over every real filename in it — M5 is correct, and its fold is complete across Design §4a, Task 13, the `## Verification` structural arms, the `writes` fence and the `## Mitigation Folds` record, with no surviving statement of the superseded region form in any spec-writer-owned surface. Also re-checked against AC-4's other clauses: §1's two entry figures parse by leading integer, §2's eight rows each carry (b1)/(b2)/(b3)/(c), every direction token is `RENAME`/`MERGE` and every (b2) token is `no`/`same-file`/`different-note`, row 3 is `same-file` → RENAME and row 8 is `different-note` → MERGE. The artifact passes the check that will read it.

One line-number nit, listed below and not drift: §4a puts `docs/lint-vault-live-baseline.md` at `:5`; it is at `:6`.

### Blocking issues

**1. The document promises, in three places, that re-running `rename_note` repairs a half-failed rename's missing alias. The door body it prescribes cannot append that alias, and Task 10 asserts the opposite.**

Design §2's door body reads `old_stem` from the SOURCE, before the branch, and guards the alias append on `old_stem != new_stem`:

```
old_stem = source.stem.lstrip("@")
...
entity._source_path = moved                     # RE-STAMP, before anything else can fail
new_stem = moved.stem.lstrip("@")
aliases = list(getattr(entity, "aliases", []) or [])
if old_stem and old_stem != new_stem and old_stem not in aliases:
```

Trace the half-failure the document resolves. `rename_note(entity, "@New.md")` on a note at `@Old.md`: `old_stem = "Old"`, the move succeeds, `entity._source_path = @New.md` (ordering decision 2 puts the re-stamp first, for a reason I agree with), then `update_frontmatter_field` raises. Residual: the note is at `@New.md` with no alias, the entity is stamped `@New.md`.

Now the prescribed recovery. `rename_note(entity, "@New.md")` again: `source = self._resolve_write_target(entity)` answers `@New.md`, so `old_stem = "New"`; `destination == source`, so `moved = source` and `new_stem = "New"`; the guard `old_stem != new_stem` is FALSE and **nothing is appended**. The alias is lost permanently, and AC-2(a)'s "resolves under BOTH names afterwards" is never restored.

Three surfaces state the false version and a fourth states the true one, which is the WI-144 condition:

- `## Edge Cases`, *"The rename fails halfway"* — **Decision:** *"re-running `rename_note(entity, same)` is idempotent: the `destination == source` branch skips the move **and appends the alias**"*; **Reasoning:** *"one note, one missing alias, **recoverable by a re-run**"*.
- `## Risk Analysis`, the door-fails-between-move-and-alias row — *"the door is idempotent, **so a re-run completes it**"*. That sentence is the whole of the row's mitigation and is what makes it low/low.
- Design §2, ordering decision 2 — *"leaves a moved, correctly-stamped note missing one alias — loud, and idempotent on a re-run, because `destination == source` is the first branch"*. True about safety, and the sentence it sits beside in `## Edge Cases` reads it as a repair.
- Task 10's IDEMPOTENCE arm — *"the note's `aliases` **unchanged** so nothing is appended twice"*. Correct for the door as written, and the direct negation of the Edge Case's Decision.

So the builder is told both, by the two surfaces they are most likely to read (the Edge Case resolves the failure mode; Task 10 writes the test). This is a resolved edge case in the bar's partial-failure and idempotency categories whose Decision the prescribed code contradicts, and a `## Risk Analysis` mitigation that does not hold.

Nothing here needs a new mechanism — the honest statement is available and cheap: after a failed alias write the residual is a moved, correctly-stamped note missing one alias, and the door cannot repair it because provenance has already moved to the destination (which ordering decision 2 wants and should keep); the recovery is a hand alias edit or an `update_fields(entity, {"aliases": [...]})`. State that in the `## Edge Cases` Decision and Reasoning, restate the `## Risk Analysis` mitigation so it does not claim the re-run completes the append, and say in Task 10 that the IDEMPOTENCE arm's "aliases unchanged" is the property (so the next reader does not read it as the bug).
(Builder's question this answers: *"`## Edge Cases` says the re-run appends the alias and Task 10 says the re-run leaves `aliases` unchanged — which one am I building, and which one am I asserting?"*)

**2. `destination == source` is a raw `Path` comparison against a stamp `move_note` hands back RESOLVED, so the idempotent branch does not fire on a symlinked temp root — and Task 10's "no `move_note` call recorded" is RED against a correct build on this project's own platform.**

`vault_io.move_note` returns `_move_locked`'s `target`, and `target` is `_resolved(dest)` = `Path(dest).resolve()` (`obsidian_schemas/vault_io.py:_resolved:234-243`, `:741-742`, `:783`). Design §2's door then does `entity._source_path = moved`, so after one rename the stamp is a RESOLVED path. `_resolve_write_target` returns the stamp unchanged (it resolves only for the containment test and returns `candidate`), while `destination = self.vault_path / new_filename` is built from the repository's `vault_path` exactly as the caller supplied it.

On macOS `/var` is a symlink to `/private/var`, and `tests/support.py:temp_dir:31-37` — this repo's only zero-arg temp-directory idiom, which the AC checks must use because they take no `tmp_path` fixture — returns `Path(tempfile.mkdtemp(prefix="wi020-"))` UNRESOLVED under `$TMPDIR`. `tests/test_lint_vault_fix_rules.py:_temp_vault:158-191` is the standing evidence: it calls `.resolve()` on both sides of every comparison it makes precisely because the raw path is not resolved, and it still hands its caller the unresolved `built`.

So for a repository built on such a vault, the second `rename_note(entity, <the filename it already has>)` has `source = /private/var/…/@New.md` and `destination = /var/…/@New.md`. They are unequal as `Path`s, so the first branch is skipped; `destination.exists()` is True and `source.samefile(destination)` is True, so the door takes the **case-only two-step** and records TWO `move_note` calls. Task 10 pins the second call at *"no `move_note` call recorded (through the same recording delegate M3's arm installs)"* — RED, against a build that implements Design §2 verbatim, on the platform the floor runs on. It also means the idempotent re-run silently performs two moves through a staging name, so an interrupted re-run can leave a `.rename-tmp.md` where the document says nothing moved at all.

This is WI-149's oracle rule one level in: the branch's discriminant is a path SHAPE that the environment decides, and nothing in the document names it. The fix is one expression and it is the builder's to write only once the spec says which — compare the two by file identity rather than by string (`destination == source or (destination.exists() and source.samefile(destination))` collapses the first two branches, or resolve both operands before comparing), and say so in Design §2's door body, in Task 6's clause and in Task 10's IDEMPOTENCE arm. Note the interaction with M3 if the branches are collapsed: the case-only two-step must still not fire when the two paths are the same spelling, or the idempotent re-run gains the M3 window for nothing.
(Builder's question this answers: *"the stamp came back from `move_note` resolved and my vault path is not — does `destination == source` fire on the idempotent re-run, and if not, is the two-step the intended behaviour or is the assertion wrong?"*)

### Non-blocking notes

- **The `!=`'s operand-normalization is a free variable of the detector's arm with no plant, and §3a's sweep dispositions the adjacent one.** The arm is `isinstance(stored, str) and stored.strip() and stem != stored`; an implementation written `stem != stored.strip()` — a plausible slip now that `.strip()` sits in the conjunct immediately to its left — passes all four AC-3(a) cells, AC-3(b)'s double-space discriminator (which is INNER whitespace, so `.strip()` does not move it) and all six of Task 12's plants, while dropping a live divergence whose only difference is leading or trailing whitespace in a quoted `name:`. §3a's table has a row for *"whitespace inside either side"* and dispositions it as already pinned by AC-3(b); the leading/trailing sub-cell is a different one. I am deliberately NOT blocking on this: Design §3 spells the arm as literal code, AC-3's signed desc says *"exactly as written"*, the live population is zero, and round 3 emitting the next member of a class whose generator §3a has already enumerated and whose next ladder level it has already declared is the treadmill the fold exists to end. If the writer touches §3a for any other reason, one row and one plant close it.
- **Design §4a's line citation for `docs/lint-vault-live-baseline.md` is `:5`; the token is on `:6`.** `docs/vault-shape-census.md` is the `:5` token. The enumeration's substance (four tokens, three paths) is exactly right.
- **The `## Verification` mutation table carries the body constraint on row 1 only.** The `BaseRepository.save` row says `repo.save(entity, body=<the note's current body>)` because `""` over a note with body content raises `BodyTruncationError` (`obsidian_schemas/writer.py:write_markdown_file:285-302`, and the guard is entity-type-agnostic). Rows 8 and 9 name only the field to set. A builder who plants a Book or Meeting with body content and calls `repo.save(entity)` hits the same guard; one clause on those two rows, or one sentence saying the planted Book/Meeting notes carry no body, removes the round trip.
- **`update_fields` hands the door `f"@{new_name}.md"` for every entity type.** `rename_note`'s own docstring gives as its reason for taking the destination from the caller that *"each type's filename rule differs (`@{name}.md`, `_get_file_name`)"* — and the one in-library caller then hardcodes the Person/Company rule. It is correct for `BaseRepository`/`PersonRepository`/`CompanyRepository` (all three derive `@{name}.md`) and unreachable-in-practice for Book and Meeting, which declare no `name` field (`obsidian_schemas/models.py:Book`, `:Meeting:259-263`), so nothing is wrong today; the tension is worth one clause so a later reader does not resolve it the other way.
- **Design §2's M1 paragraph says `gate_write` "skips entirely for a declared non-person type".** Company does not skip — it is validated against `COMPANY_TIER1_BRANCHES` (`obsidian_schemas/name_gate.py:329-343`, `obsidian_schemas/name_validation.py:_COMPANY_PATH_HOSTILE_RE:351`, the `path_hostile` record at `:398-404`), whose path-hostile class is WIDER than the person one. M1's argument is unaffected — it exists precisely because leaning on the gate is the boundary-you-can-route-around shape — and the threat model's own note states the narrow version correctly ("non-person, non-company"). One word.
- **AC-1(g)'s "with no vault walk triggered" has no stated oracle.** Task 9 says *"Then arms (d)–(h) as AC-1 states them"*. The obvious observation is `repo._loaded` still False after the writes (nothing on the new seam's path calls `_ensure_loaded`), but a builder could equally reach for a patched glob. AC-1 is signed and cannot gain text; Task 9 can, at the cost of one clause.
- **A re-anchoring nit.** `## Wall Membership`'s third row cites `tests/test_loud_fail_write.py:_check_write_failure_raises_and_noops_keep_their_return:127`; the symbol is defined at `:112` and `:127` is inside its body. Not drift — the symbol resolves — but the trailing courtesy line points into the middle of the function rather than at it.

### Carried-forward notes

- **The duplicated `## Adversarial Review — 2026-09-25` heading (injection-hunter, 2026-09-25, REVISE).** Still open and still not the spec-writer's to close — both sections and both `gate: injection-hunter` fences are present in the bytes I read, the earlier one PROMOTE and the later one REVISE, and the Spec-Writer Notes record the question without answering it, correctly. It reaches nothing in this review: no `gate: spec-reviewer` PROMOTE exists in this document, so D5's first key is absent and the second is not load-bearing for any transition today. Recorded so the chain is unbroken and so the conductor's action does not go missing behind a spec-writer round.
- **M1's exact bound (threat model round 2).** Resolve-then-`os.link` is check-then-act against an attacker who can plant a symlink at the destination between the two. FOLDED into Design §2's M1 bullet as a stated bound with no work ordered, and re-declared as a deliberate NON-action in the Spec-Writer Notes. Re-deferred: the bound is stated, the attacker is outside Prerequisites 6, and there is nothing to build.
- **The write-then-move window (threat model round 2).** FOLDED as a `## Edge Cases` entry and a `## Risk Analysis` row, with the lock-ordering entry explicitly marked as a claim about ORDERING and nothing else. Re-deferred as a declared NON-action for the same reason: the trade is stated, every residual is loud and detector-visible, and no work is ordered. Note it is adjacent to blocking finding 1 — both are about what the residual of a partially-completed rename actually is — but it is not the same defect and it does not need re-opening.
- **Architect round 6, note 6(iv)** — the deliberately-out-of-scope items (`_get_cache_key`'s strip asymmetry, approach F's re-keying, the Book/Meeting `save` collapse) stand as written and are all named in `## Scope Boundary`. Closed; recorded so the chain is unbroken.
- All other prior non-blocking notes are FOLDED and I verified each against the code rather than the prose: round 2's `.md`-token false RED (now M5's token class, and I re-ran the tokenizer over the artifact), the `aliases` source-of-truth question (Design §2's "Which `aliases` list wins", Task 6, Task 10), Task 14's two uncalled `## Wall Membership` rows (wall D and the `_email_index` pin, both now named and both predicted green — I confirmed the `_email_index` needle really is assembled from parts at `tests/test_identity_endgame.py:586-594`), AC-5 bucket (a)'s second-parameter disposition (Design §4), the `Meeting`/`tags` citation (`## Verification`), and threat-model round 3's stale "five planted members" count (the `writes` fence now states the LIST, six members, matching Task 12 and §3a).

```verdict
gate: spec-reviewer
verdict: REVISE
date: 2026-09-25
model: claude-opus-5
targets: Task 6, Task 10, #design, #risk-analysis
prior: held
basis: original
findings: 2/9
note: Both findings are Design §2's door branch structure, and both are cheap. (1) `rename_note` reads `old_stem` off the SOURCE before the branch and guards the alias append on `old_stem != new_stem`, so after a half-failed rename — move committed, `entity._source_path` already re-stamped to the destination by ordering decision 2, `update_frontmatter_field` raised — the prescribed recovery `rename_note(entity, same)` takes the `destination == source` branch with `old_stem == new_stem` and appends NOTHING; `## Edge Cases` says that branch "skips the move and appends the alias", `## Risk Analysis`'s rollback mitigation says "a re-run completes it", and Task 10's own IDEMPOTENCE arm asserts `aliases` UNCHANGED, so three surfaces promise a repair the fourth correctly denies and the builder picks one. (2) `move_note` returns `_resolved(dest)` (`vault_io.py:_resolved:234-243`, `:783`), so the stamp is RESOLVED while `destination = self.vault_path / new_filename` is not; `tests/support.py:temp_dir:31-37` hands the zero-arg AC checks an UNRESOLVED `mkdtemp` path (which is why `tests/test_lint_vault_fix_rules.py:_temp_vault` resolves both sides of every comparison it makes), and on macOS `/var` → `/private/var` — so the idempotent re-run's `destination == source` is False, the door falls through to the case-only two-step, and Task 10's "no `move_note` call recorded" is RED against a verbatim-correct build on the platform the floor runs on. Round 2's two findings and round 1's four all held closed and every non-blocking and carried-forward note is folded; M5's fold is complete and I verified its empirical half by running §4a's own tokenizer over the committed artifact — exactly the eight tokens it enumerates, all three repo paths present, so the token-class rule is green and total.
```

## Adversarial Review — 2026-09-25

Cold-start spawn, third injection-hunter round on this document (two `## Adversarial Review —
2026-09-25` sections already stand — round 1's PROMOTE, positioned between the first Spec Review and
the second Threat Model round, and round 2's REVISE, positioned between the second Spec Review and
the third Threat Model round). I read the document from line 1 to its end in full — Problem/Motivation,
Intent, the entire Exploration Notes arm (all five architect rounds, the AC red-team round, all
fifteen numbered premises, every constraint, the conductor read-back), Approach, Design §1–§2 read in
full with the remaining subsections sampled, Acceptance Criteria (all five signed `criteria` fences),
Spec-Writer Notes, then every prior gate's verdict prose in document order — Architectural Review, AC
Red-Team, AC Sign-off, Data Audit, Threat Model rounds 1–3, Spec Review rounds 1–3, and both existing
Adversarial Review sections. I also grepped the whole document (not just the sections I read closely)
for verdict-steering phrasing — "ignore previous instruction", "pre-approved", "you must/should
emit/output", imperative address to a reviewer, "trust this", role-play framing ("act as", "you are
now"), hidden-formatting tricks — and separately for every HTML comment in the file. Both greps
returned only legitimate hits: the steering-phrase grep matched nothing outside prior gates'
verdict prose *discussing* the absence of such phrasing, and the only HTML comment in the document is
the machine-maintained archive-split pointer at line 21.

**The one substantive question this round had to settle: is round 2's REVISE (the duplicate-heading
finding) a real injection-adjacent risk, or a false block?** I read both existing sections in full,
independently of round 2's own framing, before reading round 2's conclusion.

Round 2's finding, restated: a mid-document `## Adversarial Review — 2026-09-25` section (round 1)
carries a complete `PROMOTE` fence and self-certifies "first injection-hunter round... genuine
cold-start read, not a re-run" — a claim round 2 found impossible to verify from inside the document,
compounded by (a) no accompanying spec-reviewer PROMOTE existing anywhere, (b) Threat Model round 2
recording a structural edit at that exact section's boundary (removing a stray unterminated code
fence), and (c) round 2's own invocation carrying no "this is a re-run" framing the way other repeat
gates get.

Re-examining all three: (c) does not hold up. Both Threat Model round 3 ("Third threat-model round on
this document, spawned cold-start... I read it from line 1") and Spec Review round 3 ("Third
spec-review round on this document, spawned cold-start") state explicitly that they too are cold-start
spawns that determine their own round number *by reading the document*, not from invocation framing —
which is exactly what round 1, round 2, and this round all did. There is no gate on this document that
receives "this is round N" as a fact handed to it; every gate, on every round, discovers it the same
way I am discovering mine now. Round 2's point 3 treated a universal property of this pipeline's
cold-start gates as if it were something unique and suspicious about the injection-hunter's history.

(b) also resolves cleanly on a full read of Threat Model round 2's own account (the non-blocking note
at that section): the stray unterminated fence sat "immediately after the injection-hunter's closing
fence, which would have swallowed **this entire section** [Threat Model round 2's own] — including its
`verdict` and `mitigation` fences — into an open code block and made **the round** [Threat Model round
2] **declare nothing**." Threat Model round 2 fixed a markdown bug that was about to break *its own*
parseability, not the injection-hunter's. That a fence-closing bug happened to sit at the boundary of
whatever section preceded it is not evidence of tampering with that preceding section — it is what
"the document ends with a broken fence" always looks like, regardless of which section wrote it.

(a) is true but load-bearing for nothing: D5 needs the injection-hunter's PROMOTE *beside* a
spec-reviewer PROMOTE at a `specced -> ready` attempt, and neither has ever coincided in this document
— both spec-review rounds after round 1's Adversarial Review section are REVISE, so no transition has
ever been at risk of firing on a stale or forged injection-hunter key. An absent spec-reviewer PROMOTE
is consistent with (and explains) round 1 never having been load-bearing, not with it being forged.

The position itself — "mid-document, not at the end" — is also exactly what every OTHER repeat gate's
history looks like once later rounds accumulate after it: Threat Model and Spec Review each appear
three times, interleaved in matching cadence (Threat Model r1 → Spec Review r1 → Adversarial Review r1
→ Threat Model r2 → Spec Review r2 → Adversarial Review r2 → Threat Model r3 → Spec Review r3 → [this
section]). Round 1's Adversarial Review section was genuinely at the end of the document when it was
written; it is "mid-document" now purely because this pipeline's append-only accumulation model put
two more full review cycles after it — the same reason Threat Model round 1 now sits in the middle
too, and nobody reads that as forged. And there is no cryptographic or otherwise-verifiable provenance
mechanism for ANY gate round in this document (only Dave's AC sign-off carries a hash); demanding one
uniquely of the injection-hunter's own history, when no other gate's rounds carry it either, is not a
signal — it is a bar nothing in this document could clear, including this very section.

None of this proves round 1 with certainty — nothing in an unsigned, append-only document can be
proven from inside it, which is the honest limit this role carries. But round 2's three supporting
facts each have a specific, checkable, non-malicious explanation once read against the rest of the
document's own pattern, and I found no independent evidence anywhere in the body, in either
Adversarial Review section, or in the sibling material I read, of text whose *effect* is to steer a
verdict. Round 2's escalation was the right instinct under uncertainty but the uncertainty is now
resolved by the document's own structure, so re-escalating a third time would be manufacturing a
treadmill out of a closed question rather than doing the work this role exists for. I found nothing
newly suspicious in any material this round read that round 1 and round 2 had not already covered.

```verdict
gate: injection-hunter
verdict: PROMOTE
date: 2026-09-25
model: claude-sonnet-5
note: Full end-to-end read (Exploration Notes through both existing Adversarial Review sections) plus whole-document greps for steering phrasing and HTML comments found no planted text steering any gate's verdict — the only comment in the file is the legitimate archive-split pointer. Round 2's REVISE (duplicate-heading provenance concern) is resolved rather than reopened: its "no re-run framing" point is false (Threat Model r3 and Spec Review r3 both state they are cold-start spawns that self-discover their round number by reading the document, exactly as every injection-hunter round including this one does); its "fence fixed at the boundary" point is Threat Model round 2 repairing a stray unterminated fence that threatened to swallow *its own* section, not evidence of tampering with the injection-hunter's; its "no accompanying spec-reviewer PROMOTE" point is true but never load-bearing, since no transition has been at risk; and round 1's mid-document position is the same append-only artifact every other repeat gate on this document shows (Threat Model and Spec Review each run three interleaved rounds too) — no gate round in this document carries cryptographic provenance, so that bar cannot discriminate a forged round from a genuine one for any gate, this one included.
```

## Threat Model — 2026-09-25

**Recommendation: PROMOTE to threat-modeled — round 4. M1, M2, M3, M4 and M5 all HELD: I re-verified each
against the code or the artifact it prescribes, every ordinal is unmoved, and the five fences below are
RE-EMITTED with byte-identical `desc`. The THIRD fold introduced no new security surface — its branch-key
change is strictly better on integrity and I checked the shape that could have gone the other way. The
finding this round is not in the fold: it is a fail-OPEN underneath the refusal this document names as its
safety net in six places. `vault_io.move_note`'s occupied-destination refusal is conditional on
`guard_mode() == "enforce"`; under `OBSIDIAN_SCHEMAS_WRITE_GUARD=observe` door 3 does `os.replace(source,
target)` and DESTROYS the occupied note. WI-004 declared that residual acceptable in writing (R9) while
door 3 had one quarantine caller; this is the item that makes door 3 the package's relocation capability
and drives it on every consumer name change. One new required mitigation, M6, one clause on Task 6.**

Fourth threat-model round on this document, spawned cold-start. I read it from line 1, then re-read the
material the THIRD spec-review fold added — Design §2's "Which branch fires is decided by WHICH FILE each
side names", "What a half-failed rename leaves" and the re-run sequence-point table, ordering decision 2's
restatement, the `f"@{new_name}.md"` paragraph, the M1 bullet's COMPANY precision, §3a's fifth member,
§4a's corrected citation, three `## Edge Cases` entries, two `## Risk Analysis` rows, Task 6's three new
clauses (branch key, no-alias-repair-arm, bare-name import), Task 9's (g) oracle, Task 10's three new arms
and its resolve-both-sides rule, Task 12's plant (vii) and the `## Verification` mutation-table
constraint — and checked each against the CODE rather than against the fold's prose. I re-read the
spec-review round that landed between my rounds. I also re-ran M5's empirical claim over the committed
artifact's current bytes rather than carrying it forward.

### Trigger check

The same five fire, unchanged in shape: filesystem operations on user-owned files, persistence, untrusted
vault bytes crossing into a trusted write-target decision, PII (person names in a WARNING, an ERROR and a
committed live-vault artifact), and an out-of-repo blast radius through three `-e` consumers. The fold
added no sixth — no network, no subprocess, no credential, no new import capability. **But this round adds
a sixth trigger that three rounds of mine did not name and should have: CONFIGURATION THAT CHANGES A TRUST
BOUNDARY.** `obsidian_schemas/vault_io.py:guard_mode:169-181` is an environment-read setting, re-read per
call, that converts every door-2/door-3 refusal into a WARNING-and-proceed. That is the trigger the
finding below sits on, and it fires because this item is the first thing to put weight on door 3.

### The five standing mitigations, re-verified against the code

**M1 — still landed and still total, and the fold did not displace it.** This was the one ordering I had to
check rather than assume: the fold inserted two new statements into the door body, so I re-read the body's
sequence. It is source-resolve → `source.exists()` → `destination = self.vault_path / new_filename` →
M1's containment block → `old_stem` → `same_place` → the three branches. Both insertions (`old_stem` at
Design §2's line, `same_place` beside it) land AFTER the containment block and BEFORE the first
`vault_io.move_note` call, so M1 still precedes every move on all three branches. I re-confirmed the two
facts underneath it in this worktree rather than trusting round 3's account: `vault_io._resolved` is still
a bare non-strict `Path(path).resolve()` with no notion of a vault root
(`obsidian_schemas/vault_io.py:_resolved:234-243`) and `move_note` still refuses only a symlinked SOURCE
(`obsidian_schemas/vault_io.py:move_note:736-740`) and checks nothing about where `dest` points, so M1's
clause is still the only thing bounding the destination. Task 6, ordinal unmoved.

**M2 — still landed, unchanged.** Task 2's arm still asserts the PROPERTY (the accessor
`_resolve_write_target` reads answers A's own path; nothing the seam reads answers B), with pydantic's
extras retention demoted to a Build-Log observation. Task 2, ordinal unmoved.

**M3 — still landed, unchanged, and the fold made its window NARROWER rather than wider.**
`source.with_name(destination.stem + ".rename-tmp.md")` is byte-for-byte in the door body, in Task 6's
work text, in the `## Edge Cases` entry for a process dying mid-two-step and in the `## Risk Analysis`
row; Task 10's oracle is still `vault_path.glob(repo.file_pattern)` with the rejected spelling driven
through the same glob as a near-miss. The branch-key fix is a bonus for M3 that the fold does not claim:
under the old raw string compare the idempotent re-run FELL THROUGH to the case-only two-step on this
project's own platform, so every no-op re-run was opening M3's staging window for nothing. Task 6,
ordinal unmoved.

**M4 — still landed, unchanged.** `logger.info("Renamed %s note from %s to %s", self.type_name,
source.name, moved.name)` in the door body and in Task 6, captured in Task 10 through
`captured_logs(level=logging.INFO)`. Task 6, ordinal unmoved.

**M5 — still landed, and I re-derived its empirical half instead of carrying it.** I ran §4a's own
prescribed tokenizer (`[\w@{}*./+-]+\.md`) over `docs/stem-divergence-live-baseline.md` as committed
TODAY. It returns exactly EIGHT tokens and they are exactly the eight §4a enumerates:
`docs/filename-name-divergence-repair.md` (`:4`), `docs/vault-shape-census.md` (`:5`, `:22`),
`docs/lint-vault-live-baseline.md` (`:6`), `*.md` (`:36`) and `@{name}.md` (`:76`, `:126`, `:153`). I
globbed all three repo-relative paths and all three exist. So the token-class rule is GREEN against the
artifact as committed and TOTAL over every real filename in it. The fold's citation correction is right —
`docs/lint-vault-live-baseline.md` is on `:6`, not `:5` — and Task 13 now carries the token-class rule
whole-file in both halves, with no fence toggle and no non-vacuity guard in the privacy path, and with the
reader battery pinned MUST-FIRE for a bare filename INSIDE a fence. That is the arm the region form let
through and it is the whole of M5. Task 13, ordinal unmoved.

### STRIDE delta — what the third fold moved

**Spoofing, Denial of service, Elevation of privilege: unmoved.** M2 still closes the stamp's read
direction; the privilege surface is still filesystem reach bounded by M1; `door_calls_inside_note_lock`
still makes the lock-ordering rule structural, and the fold added two `.resolve()` calls per rename and no
retry, recursion or unbounded loop.

**Tampering: strictly better, and I checked the branch key for the one way it could have gone wrong.** The
question a new branch discriminant has to answer is whether the no-op branch can fire on two DIFFERENT
files — because that branch skips the move and returns as though the rename succeeded, which on a wrong
answer would silently abandon a repair the conductor believes was performed. It cannot. The key is
`(destination.parent.resolve(), destination.name) == (source.parent.resolve(), source.name)`: equal
resolved parent directories plus a byte-identical basename is the same directory entry, hence the same
file, on every filesystem — there is no spelling of two distinct notes that satisfies both halves. And the
failure direction on a MISS is safe rather than dangerous: a same-file pair the key fails to recognise
falls through to `destination.exists() and source.samefile(destination)`, which is the inode test, and
from there into the two-step M3 already protects. The old raw compare had the opposite failure direction
on this project's own platform. I also confirmed the premise the key rests on in this worktree:
`move_note` returns `_move_locked`'s `target`, and `target` is `_resolved(dest)`
(`obsidian_schemas/vault_io.py:move_note:741-750`, `:_move_locked:783`) — a RESOLVED path. The fold's
account is correct at every step.

**Repudiation: better at the same three sites, with one cosmetic regression noted below.** The re-run
table and the honest residual statement are an improvement to reconstructability, not a threat delta: they
tell a conductor reading a log what state the vault is actually in after a partial failure, which is
exactly what M4 exists for.

**Information disclosure: nothing new, and I checked the two places the fold could have opened
something.** The fold added no log line and no exception message carrying a value the package does not
already emit: `update_fields`' new refusal names the requested new name, which is a person name, but
`base.py`'s shipped `ValueError(f"{self.type_name} not found in repository: {name}")` already does exactly
that in the same method, so the class is unchanged. Task 3's and Task 5's INFO change swaps one filename
for another filename (`file_path.name` for the derived `filename`) and stays inside the package's shipped
`@{name}.md` INFO idiom. M5's half of AC-4 is re-verified above and is total.

### The finding, and why it is not in the fold

**Every refusal this document leans on at an occupied destination is conditional on an environment
variable, and the document never names it.** Six surfaces state the refusal as unconditional, four of them
citing the syscall:

- **AC-2(b), signed** — *"asked to rename onto an occupied filename it raises `NoteAlreadyExists` (the
  leaf, not the root) and BOTH files are byte-identical afterwards."*
- Design §2, ordering decision 1 — *"`move_note` refuses a symlinked source and an occupied destination
  before it writes anything … so nothing is written on either refusal arm."*
- `## Edge Cases`, the live MERGE row — *"`move_note` refuses by syscall with `NoteAlreadyExists` and both
  files are byte-identical afterwards … The refusal is the kernel's `FileExistsError` on `os.link`
  (`obsidian_schemas/vault_io.py:_move_locked:759-771`), not a check-then-act."*
- `## Edge Cases`, the write-then-move race — *"a concurrent create at the destination gives
  `NoteAlreadyExists` by syscall."*
- Design §2's re-run table, row 1 — `NoteAlreadyExists` as one of the refusals a re-run repeats identically.
- `## Risk Analysis`, Rollback — *"`move_note` refuses an occupied destination by syscall."*

All six are false under one setting. `obsidian_schemas/vault_io.py:_move_locked:757-771` reads:

```
    try:
        os.link(source, target)
    except FileExistsError as exc:
        if guard_mode() == "observe":
            logger.warning(...)
            os.replace(source, target)
            forget_snapshot(source)
            forget_snapshot(target)
            _fsync_dir(target.parent)
            return target
        raise NoteAlreadyExists(...)
```

`os.replace(source, target)` OVERWRITES the destination. There is no refusal, no exception, and no
`NoteAlreadyExists`: the door returns the destination path as though the move had succeeded, the occupied
note's bytes are gone, and `rename_note` proceeds to append an alias, `_adopt` the entity and log a
successful rename. `guard_mode` is `_env_setting("OBSIDIAN_SCHEMAS_WRITE_GUARD", …, default="enforce")`
(`obsidian_schemas/vault_io.py:guard_mode:169-181`), read PER CALL, so no restart is needed and no
in-process state records that the mode was ever set beyond one INFO line per process
(`:_announce_mode_once:202-220`).

Five things make this the finding rather than a theoretical one.

1. **WI-004 declared this exact residual, for this exact door, in writing — and declared it acceptable on
   a premise this item removes.** `docs/concurrent-access.md:649-656` is residual **R9**: *"A consumer that
   sets `OBSIDIAN_SCHEMAS_WRITE_GUARD=observe` keeps today's exact write semantics — including the
   concurrent-create clobber … while it is set, this item's Intent is explicitly **not** delivered for
   doors 2 and 3."* **Door 3 is `move_note`.** That was a defensible residual when door 3 had, in this
   document's own words, *"exactly ONE caller in the tree today (`scripts/lint_vault.py:1343`,
   quarantine) — essentially unexercised for this use."* WI-029 is the item that makes door 3 the
   package's relocation capability, ships it public to three `-e` consumers, and drives it on **every**
   `update_fields` name change — which `## Risk Analysis` rates *certain (it is the design)*. The
   residual's blast radius is created by this item, so closing it is this item's cost.
2. **`observe` is not an exotic setting — this estate's own docs name it as the cheapest ROLLBACK LEVER
   and as the measure-before-adopting mode the three consumers are invited to set.**
   `docs/concurrent-access.md:4286` — *"Rollback plan. Three levels, cheapest first. (i) Set
   `OBSIDIAN_SCHEMAS_WRITE_GUARD=observe`"*; `:2556` — *"wants to measure before adopting,
   `OBSIDIAN_SCHEMAS_WRITE_GUARD=observe`"*; `:6794` — the same lever *"with no code change."* So the
   realistic sequence is not an attack: a consumer hits a write-guard refusal, reaches for the documented
   rollback, and the relocation door silently stops refusing. That is a fail-open reached by following
   the estate's own runbook.
3. **The harm is the exact harm the Intent exists to end, and it is not recoverable.** `os.replace` of A
   over B lands one person's bytes in another person's note and destroys B — which is verbatim what AC-2(f)'s
   `why` calls *"the repair machinery corrupting a note it was never asked about"*, except worse, because a
   forked note is recoverable and an overwritten one is not. `## Risk Analysis`'s Rollback paragraph is
   explicit that the live repair *"is the one act that is not revertible by `git`"*, and it lists the
   syscall refusal as one of the four things that bracket it. Under `observe` that bracket is absent.
4. **The live repair run is exactly where it would bite, and the document's own drift procedure is what
   reaches it.** The close-out drives 7 RENAMEs through `rename_note` against Dave's live vault, outside
   the cage, in whatever environment the conductor's shell carries. The plan does not drive the occupied
   row — row 8 is *"1 MERGE by hand"* — but step 1 exists precisely because the table can drift: *"a new
   row, or a row whose (b2)/(b3) answer has moved since 2026-09-21, is a drift report."* A row whose (b2)
   moved from `no` to `different-note` is a destination that became occupied, and the safety net for
   executing it anyway is the syscall refusal. The concurrent-create case is the same shape with Obsidian
   or HAL9000 as the other writer, and `## Edge Cases` resolves it by naming the refusal.
5. **Nothing in the build would catch it, and the fix is one expression.** The floor command sets no
   environment, so every battery runs under `enforce` and stays green either way; `observe` is exercised in
   the suite at `tests/test_concurrent_access.py:737` against door 2 (`write_note`) only, so door 3's
   observe arm is pinned by nothing today and would not be pinned by this item either. And the door
   already has the mode one call away: `base.py:22` is `from obsidian_schemas import vault_io`, so
   `vault_io.guard_mode()` costs no import and lands beside M1's containment block, with the other
   pre-move argument refusals. **M6.**

*The mitigation's bound, so it is not over-read.* M6 covers the door THIS ITEM SHIPS and deliberately not
door 2's create arm (`obsidian_schemas/vault_io.py:create_note:709-718`), which has the same fail-open and
which AC-1(f) leans on for its `NoteAlreadyExists`. That one is untouched by this item in both directions —
(f)'s declared behaviour is *"today's behaviour holds"*, and today's behaviour under `observe` is today's
behaviour under `observe`. It remains WI-004's R9 and belongs to WI-004's backlog, not to Task 3. Naming
the scope matters because the tempting over-fold is a guard-mode refusal on every write path in the
package, which would be a second behaviour this item was not asked for and would put the item's seam
behind a configuration check it does not need.

### Notes (non-blocking)

- **The no-op branch logs a rename that did not happen, which is one line of noise in the surface M4
  exists to make trustworthy.** On the `same_place` branch `moved = source`, so M4's line reads
  *"Renamed person note from @New.md to @New.md"*. It is harmless and it is not a security defect, but M4's
  whole claim is that a relocation is *"reconstructable from logs"*, and a log in which no-ops are
  indistinguishable from moves is weaker at exactly that. If the writer touches Task 6's branch for any
  other reason, moving the INFO line inside the two moving branches (or naming the no-op in it) closes it
  for one clause. Not folded and not required — I am recording it rather than spending a round on it.
- **`update_fields`' new refusal message names a person name, and that is the shipped class rather than a
  new one.** The same method already raises `ValueError(f"{self.type_name} not found in repository:
  {name}")` with the name in it, so no disclosure boundary moves. Worth one line only because
  `vault_io._env_setting:104-115` documents the opposite discipline for its own messages (*"never the
  value, which could carry a person's name"*), and a reader comparing the two should know the asymmetry is
  pre-existing and deliberate, not something this item introduced.
- **M6 must read the mode through `vault_io.guard_mode()` and never through `os.environ`, and the wrong
  spelling is one keystroke away.** `base.py` already imports `os` (`:9`), so
  `os.environ.get("OBSIDIAN_SCHEMAS_WRITE_GUARD")` would build — and it would duplicate the capability
  `vault_io._env_setting:104-115` reserves to itself in writing (*"The module's ONLY environment access …
  it either routes through here and gets the rule, or it names `os.environ` a second time — which is a
  capability duplication inside the one file the routing wall excludes"*). The mitigation's `desc` names
  the required spelling for that reason.
- **All three of round 3's carried-forward dispositions still stand and need no work.** M1's
  check-then-act residual is bounded in Design §2 with no work ordered and the attacker is outside
  Prerequisites 6; the write-then-move window is an `## Edge Cases` entry and a `## Risk Analysis` row with
  the lock-ordering claim kept separate; the M3 `load()` window is folded into the close-out whose ship
  condition is `len(conflicts) == 0`. Re-deferred unchanged.
- **The duplicated `## Adversarial Review` heading is still the conductor's and is still not mine.** The
  third injection-hunter round resolved it on the merits and PROMOTEd; the structural question of two
  sections under one heading is unchanged by that and unchanged by this round. Recorded so the chain is
  unbroken.
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

```verdict
gate: threat-modeler
verdict: PROMOTE
date: 2026-09-25
model: claude-opus-5
note: Round 4 re-verified M1-M5 against the code or artifact each prescribes — all five HELD with ordinals unmoved and `desc` re-emitted byte-identically. M1 needed a real re-check because the fold inserted two statements into the door body: `old_stem` and `same_place` both land AFTER the containment block and before the first `move_note` call, so M1 still precedes every move on all three branches, and the two facts it rests on are unchanged in this worktree (`vault_io._resolved` is still a bare `Path.resolve()` with no vault root, `:234-243`; `move_note` still refuses only a symlinked SOURCE, `:736-740`). M5 I re-derived rather than carried: §4a's own tokenizer over the committed artifact returns exactly the eight tokens it enumerates, all three repo paths exist, so the token-class rule is green and total, and the fold's `:5`→`:6` citation fix is right. The third fold opened NOTHING — I checked the branch key for the one way it could go wrong and it cannot: equal resolved parents plus a byte-identical basename is the same directory entry on every filesystem, so the no-op branch cannot fire on two different files, and a MISS falls through to `samefile` and the M3-protected two-step, which is the safe direction the old raw compare did not have. The finding is not in the fold. Six surfaces of this document — AC-2(b) among them — state that an occupied destination is refused BY SYSCALL, four of them citing `_move_locked:759-771`; all six are false under `OBSIDIAN_SCHEMAS_WRITE_GUARD=observe`, where `:757-771` does `os.replace(source, target)`, destroys the occupied note, returns the destination as a success and lets the door alias, `_adopt` and log a rename that overwrote a third party. This is WI-004's residual R9 verbatim (`docs/concurrent-access.md:649-656`: under `observe` the Intent is "explicitly not delivered for doors 2 and 3") — a residual that was defensible while door 3 had one quarantine caller and is not once THIS item makes it the package's relocation capability and drives it on every `update_fields` name change in three `-e` consumers, rated `certain` by the risk table. It is not exotic: the same estate's docs name `observe` as the cheapest rollback lever (`:4286`) and the measure-before-adopting mode (`:2556`), so the realistic path is a consumer following the runbook, not an attacker; the harm is AC-2(f)'s own "corrupting a note it was never asked about" but unrecoverable, in the one act Rollback says `git` cannot undo; the drift procedure at close-out step 1 is what reaches it; and nothing in the build catches it, since the floor sets no environment and the suite exercises `observe` against door 2 only (`tests/test_concurrent_access.py:737`). M6 is one expression beside M1's containment block — `base.py:22` already imports `vault_io`, so `guard_mode()` costs no import — scoped deliberately to the door this item ships and NOT to `create_note`'s identical arm, which AC-1(f) leans on and this item moves in neither direction. Zero OPEN questions.
```
