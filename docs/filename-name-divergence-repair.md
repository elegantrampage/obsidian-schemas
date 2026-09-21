---
id: WI-029
title: 'Filename/name divergence repair: rename the forked stems, then pin the invariant'
project: obsidian-schemas
stage: exploring
created: 2026-09-06
last_touched: 2026-09-21
stage_changed: 2026-09-21
touched_by: session
tags: []
depends_on: []
transitions: ["idea>exploring@2026-09-21@porter"]
---

# Filename/name divergence repair: rename the forked stems, then pin the invariant

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

## Acceptance Criteria

Draft — proposed at `exploring`, to be reviewed and signed by Dave through `/review-spec` before
`→ specced`. The spec-writer refines them in place; nothing here is frozen yet.

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

## Architectural Review — 2026-09-21

**Recommendation: REVISE — one approach-level defect, everything else holds**

Cold-start read, no prior gate round on this document. Every citation below was re-executed against
this worktree (`cage-wt-rix_vnom`, HEAD `6f045a9`) with Read/Grep; where a line number in the
document had drifted I say so.

### Trigger check

Four fire: a new public repository door (rename); a behaviour change on two shipped write paths
(`BaseRepository.save`, `update_fields`) with out-of-repo consumer blast radius; a new check across
three files in `scripts/lint_vault.py`; effort > 1 day. Review runs.

### Premise re-verification (what I re-executed)

The document's data-premise audit holds, with two corrections and one confirmation worth recording:

- Premise 1 is CORRECT and its own correction is correct — `save` binds `name` → `filename` →
  `file_path` at `obsidian_schemas/repositories/base.py:391-393`, and `:367-412` contains no
  `unlink`/`rename`/`replace`. (`docs/write-door-bypasses.md:452` still cites the WI-021-era `:380-382`.)
- Premises 2, 3, 4, 5 CONFIRMED verbatim: `_file_map` filled at `base.py:244-246`, read at `:354-365`,
  consulted by `update_fields` at `:438` and by `save` nowhere; the deliberate alias-append at
  `:454-459`; four in-library `.save(` sites, all create paths; `move_note`'s single caller and its
  link-then-unlink contract at `vault_io.py:721-783`.
- Premise 7 CONFIRMED at `tests/fixture_vault.py:255-276` — two `stem_name_divergence` members plus
  the collision third.
- Premise 6 CONFIRMED: no divergence detector exists; the five check functions are as listed.
- **Premise 8 is OVERSTATED, in the safe direction.** `broken_wikilink`'s auto-fixable arm is reached
  only when `MEETING_DATE_PATTERN.match(link_target)` succeeds AND exactly one dated candidate exists
  (`scripts/lint_vault.py:572-592`); a person stem cannot match it, so a renamed person note's
  incoming links land on the non-fixable arm at `:594-600` and `apply_fixes` never touches them
  (`:1085-1096` handles only the JSON-carrying arm). The rename's cost is therefore linter NOISE, not
  a wrong auto-rewrite. The rest of premise 8 — stem-only resolution, aliases consulted nowhere in
  `check_links` — is correct.
- The live counts CONFIRMED at `docs/vault-shape-census.md:262-271`: 8 live divergences, and
  **`same_name_collision` ABSENT only in the ≥3 sense — "largest live collision: 2"**. That line is
  load-bearing for the blocking finding below: the merge shape is live, not hypothetical.

### Review

**Fit:** Strong. Seam-then-repair-then-invariant is this project's own shape (WI-026: detector +
committed live bracket; WI-031: containment wall). AC-4's split — hermetic check over a committed
artifact, live measurement as a conductor ship condition — is LESSONS #27 applied correctly rather
than a hermetic test pretending to certify a production surface. The `kind: precondition` fences are
used for exactly the two facts a caged reader cannot reach, with the WI-300 ordering honoured.

**Duplication:** No overlap found. `move_note` exists and is unexercised for this use
(`vault_io.py:721`); building the door on it rather than beside it is right. Approach D's rejection
correctly refuses a second repair authority inside `--fix`.

**Boundaries:** Clean, with one asymmetry the document already names: the contract change lands on
three repositories this item cannot patch, which is why precondition 2 is the right instrument.
`save` keeps its single responsibility; the rename decision lives in one explicit door. Approach E's
rejection (loud-but-unshippable ordering) is the correct call.

**Determinism boundary:** n/a — nothing here is handed to an LLM. Per-note repair direction is the
one judgement call and it is correctly routed to a committed human-signed table, not to a rule.

**Reversibility:** Good. The detector is read-only; the repair is per-note through a door that
refuses an occupied destination by syscall and leaves a duplicate rather than a hole on mid-flight
failure. The seam change is the one hard-to-reverse act, and it is a behaviour consumers observe —
hence the audit.

**Generalization:** Correctly scoped. The seam is stated over `BaseRepository`, so Book/Company/
Meeting inherit it; the detector is person-shaped, which matches the measured class. WI-022's seven
company notes are left as a spec-time scoping question rather than pre-decided — right.

**Cost & maintenance:** One build session plus two conductor acts is credible for this surface. No
new dependency, no schema change.

**Build vs extend vs integrate:** Extend, throughout. Right answer.

**Prior art (outside view):** The world's answer to filename/field divergence is to stop making the
filename the identity — Notion/Roam key on an immutable id and treat the title as a label. That
option is genuinely closed here, and not by preference: in Obsidian the filename IS the wikilink
target, so identity-by-path is imposed by the platform. No compensation-machinery concern, and this
is not a recurrence of a previously-worked-around constraint. Worth noting that WI-125's identifier
index already IS an id-based identity layer inside this package — which is the direction the
blocking finding points.

### Blocking issue

**1. The seam binds the write path by NAME, but the Intent, the WI-185 section and AC-1 all require
it bound by PROVENANCE — and those differ exactly where the live corpus is dirtiest.**

`## Approach` (1) and AC-1 choose `get_file_path(entity.name)` as the mechanism. `_file_map` is keyed
`name.lower()` (`base.py:244-246`, `:321`) and holds **one path per name**. So the mechanism cannot
answer "which note did this entity come from"; it answers "which note won the glob"
(`base.py:241-246` — last iteration wins over `vault_path.glob`, i.e. filesystem order). Two
consequences, both concrete:

- *(a) AC-1(b) is not satisfiable as written.* AC-1 derives its subject set as every `NoteSpec`
  carrying `stem_name_divergence` — which is `@Quillam Ostrivane.md` and `@Quillam Lumbrek.md`
  (`tests/fixture_vault.py:255-266`), **both carrying one `name:`**. At most one of them can receive
  its own bytes, and which one is glob order. "The changed bytes are in the file the entity was
  loaded FROM" is therefore false for one of the two subjects on every run, and non-deterministic
  across machines.
- *(b) Worse than a test problem — for the collision shape the approach swaps one corruption for
  another.* A consumer that parses a specific note into a `Person` and calls `repo.save(person)`
  gets its bytes written into a **different note** under approach C, which is precisely the harm
  AC-1's headline forbids ("land one person's bytes in another person's note"). Today that call
  creates `@{name}.md`. The census records a live 2-note collision
  (`docs/vault-shape-census.md:266-267`), so this is a shape the direction table will contain as a
  merge row, not an invented edge.

There is a second witness for the same root cause, and it is the one AC-1's battery structurally
cannot see: `_ensure_loaded` is a **no-op** when `auto_load=False` and `load()` was never called
(`base.py:210-213`). On such a repository `get_file_path` returns `None`, `save` falls back to
`@{name}.md`, and the seam is **silently inert** — forking exactly as today. AC-1's battery must load
the corpus to derive its subjects, so it can never distinguish "seam works" from "seam absent for a
whole repository configuration". That is the WI-286 shape AC-1 itself invokes, one level up.

The document already contains the correct principle — *"the path a write lands on must come from the
note the entity came from"* (`## Exploration Notes`, "Where the structure lives"). The mechanism does
not implement it: it reconstructs the path from a field that is neither unique nor always indexed.
That is LESSONS #1 (enforce by construction, at the parse) against a read-time reconstruction, which
is the same WI-185 question the section asks and then answers with the weaker half.

**What would close it** — the document must choose one and say so; I am not specifying it:
(i) carry the source path as a typed fact on the loaded entity (or a path-keyed provenance side map
filled at `base.py:242`, where the path is in hand) so `save` writes where the entity actually came
from, which closes the collision shape and the `auto_load=False` shape together; or (ii) narrow the
promise explicitly — declare divergence-with-collision out of AC-1's scope, restate AC-1's headline
so it does not claim what the mechanism cannot deliver, hand the collision class to AC-3's detector
plus the direction table's merge rows, and state what an unloaded repository does. Either is cheap.
Shipping (ii)'s mechanism under (i)'s guarantee is not.

### Non-blocking notes for the spec-writer

- **AC-1's subject derivation under-covers by construction.** Deriving subjects from
  `shape_classes == stem_name_divergence` makes the corpus manifest the definition of the defect
  class. The collision third (`@Quillam Ostrivane Lumbrek.md`, `tests/fixture_vault.py:273-276`)
  carries no `shape_classes` at all and so is excluded from the sweep while being the file AC-1(c)
  asserts about. Bind the subject to a FILE, not to `repo.get(name)`, or the oracle inherits the
  glob-order problem above.
- **The incoming-reference disposition is named three ways and chosen none.** `## Exploration Notes`
  ("Renaming is not a free act") offers rewrite-the-references / teach-the-linter-aliases /
  accept-the-noise; `## Approach` and the criteria pick none, and precondition (c) measures the
  count without saying what is done with it. That leaves the repair run buildable two ways (WI-144).
  Given the premise-8 correction above, "accept the noise knowingly" is now a materially cheaper
  answer than the document assumes — but it should be written down as the answer.
- **AC-2(c) makes every future name change relocate a file, permanently.** That is the right call for
  ending manufactured divergence, but its ongoing cost is the same unmeasured link noise, and
  precondition 2's question list (`## Write Targets`) asks consumers about `.save(`/`update_fields(`
  call sites and stale `Path` handles — not about `auto_load=False` construction (now load-bearing,
  per the blocking finding) and not about anything holding a wikilink to a note it renames. Two
  questions to add while the audit is being commissioned rather than after.
- **`save` becomes a read-then-write.** Under any form of the seam, `save` on a fresh repository
  triggers a full vault walk where today it triggers none. Worth one line in the spec on whether
  that is acceptable on consumers' hot paths, and it is a second reason the `auto_load=False` case
  needs a stated answer rather than a fallback.
- Minor, for accuracy: `_get_cache_key` is `name.lower()` (`base.py:321`, no strip) while
  `get_file_path` looks up `name.lower().strip()` (`:365`). Pre-existing and low-severity — YAML
  strips plain scalars — but it becomes load-bearing the moment the anti-fork guarantee rests on
  that lookup.

The approach is sound and the exploration behind it is unusually well grounded — this is one
mechanism substitution away from PROMOTE, not a return to ideation.

```verdict
gate: architect
verdict: REVISE
date: 2026-09-21
model: claude-opus-5
note: The seam binds the write path from `_file_map` (keyed `name.lower()`, one path per name, empty when `auto_load=False`), so it cannot deliver AC-1's absolute no-fork/no-cross-write guarantee for the live collision shape or for an unloaded repository — bind by provenance or narrow the promise.
targets: AC-1, AC-2, #approach, #exploration-notes, #write-targets
prior: none
basis: original
findings: 1/4
```

## Architectural Review — 2026-09-21

**Recommendation: REVISE (round 2) — the fold HELD; one sibling of the same class is still open**

Round 1 was mine. I re-executed every claim the fold rests on against this worktree
(`cage-wt-rix_vnom`, HEAD `6f045a9`) with Read/Grep, then swept the package for the rest of the
class. The fold is correct and well made. It is not yet complete, and the gap has to be settled
BEFORE precondition 2 is commissioned rather than during speccing — which is why this is one more
round and not a note.

### Trigger check

Unchanged, four fire: new public repository door; behaviour change on shipped write paths with
out-of-repo consumer blast radius; new lint check across three files; effort > 1 day.

### Round 1's finding: CLOSED

Verified line by line, because a fold that merely *says* provenance would be worse than the
name-keyed version it replaced:

- **Premise 10 CONFIRMED, exactly as written.** `ParsedDocument.file_path` is a declared field
  (`parser.py:54`), set from the path handed in (`:236`, `:246-252`). Grep for `parse_markdown_file`
  over `obsidian_schemas/**` returns the definition, the `__init__` re-export and exactly three call
  sites — `base.py:311`, `book.py:79`, `meeting.py:83` — and `base.py:311-314` does
  `return doc.entity`, dropping the path one line after it was constructed. The binding really is
  built, held for three lines and thrown away. This is the right place to keep it: LESSONS #1, at the
  parse, not reconstructed at read time.
- **Premise 11 CONFIRMED, including the trap.** `entity_to_frontmatter` composes the written mapping
  from `type(entity).model_fields`, then `entity.model_extra`, then explicit `extra_fields`, and
  nothing else (`writer.py:106-131`) — a `PrivateAttr` is in none of the three, so it is unwritable
  by construction. `BaseEntity.model_config` does set `extra="allow"` (`models.py:31-32`), so the
  bare-assignment version would indeed be serialized into every note the library writes. Specifying
  the stamp as a declared private attribute, and asserting the unwritability in AC-1(h) rather than
  trusting it, is the correct treatment.
- **Premise 2's amendment is the honest correction.** `_file_map` is filled last-wins over
  `vault_path.glob` (`base.py:241-246`), read at `:354-365`, and `_ensure_loaded` is a no-op under
  `auto_load=False` (`:210-213`). "Glob order, not provenance" is right, and retiring the earlier
  "the repository already knows the right path" phrasing removes the sentence that produced C′.
- **Premise 8's correction is right and I under-read it in round 1 in the same direction the document
  now records.** `broken_wikilink`'s fixable arm needs `MEETING_DATE_PATTERN` to match
  (`scripts/lint_vault.py:572-592`); a person stem cannot, so renames land on `:594-600` and
  `apply_fixes` (`:1085-1096`) cannot act. Noise, never a wrong auto-repair — and that correction is
  what makes "accept the noise knowingly" the cheap answer rather than the lazy one. Choosing a
  disposition in writing closes round 1's WI-144 note.
- **C′ is recorded as a rejected approach rather than quietly replaced**, with the three structural
  reasons intact. That is the right form: the next reader who re-derives "just use `get_file_path`,
  it's simpler" finds out here why it is not.
- **AC-1 now binds each subject to a FILE and derives the subject set from the stem≠name predicate**,
  which picks up the collision third (`tests/fixture_vault.py:273-276`) and closes round 1's
  under-covering note. The added (f)/(g)/(h) arms are the discriminating ones, and AC-2(e)'s
  both-arms re-stamp closes the fork-manufactured-by-the-repair hazard properly — a door that
  re-stamps unconditionally fails the refused arm.

No previous finding re-opened. The class narrowed; it did not move.

### Blocking issue

**1. `save` becomes provenance-bound; the package's other mutating write paths do not. AC-1's
headline ("no library write…") therefore stays false as written, and — the sharp end — this item's
OWN new rename door is driven from the name-keyed lookup it was built to retire.**

The fold's blast-radius bullet states the stamp is "read at one site (`base.py`'s `save`)". That
sentence is accurate about the fold and wrong about the package. Swept with grep over
`obsidian_schemas/**` for `write_markdown_file|vault_io.write_note|\.save\(|update_fields\(`, then
read at each site, the full population of write paths that resolve a target from a NAME is:

- `BaseRepository.update_fields` — target bound at `base.py:438` via `get_file_path(name)`, written
  at `:490`.
- Six `PersonRepository` body-writers, every one of them `file_path = self.get_file_path(person.name)`:
  `append_to_timeline` (`person.py:1403` → writes `:1447`, `:1458`), `append_to_body_section`
  (`:1522` → `:1559`), `add_to_discuss_item` (`:1653` → `:1679`), `update_to_discuss_item`
  (`:1719` → `:1758`), `remove_to_discuss_item` (`:1793` → `:1828`), plus the read helper
  `_get_body_content` (`:1590`).
- `BookRepository.save` (`book.py:167-170`) and `MeetingRepository.save` (`meeting.py:189-192`)
  **override** and derive the filename from `self._get_file_name(entity)` without ever calling
  `super().save()` — so for Book and Meeting entities the parse would set a stamp that nothing reads.
  (`PersonRepository.save` delegates through `super().save()` at `person.py:1197`, and
  `CompanyRepository` declares no `save`, so those two do inherit the seam.)

Three reasons this blocks rather than waits for the spec-writer:

- *(a) The criterion over-claims against its own oracle.* AC-1's desc says "**no library write** can
  turn one person note into two or land one person's bytes in another person's note", while its
  oracle exercises `save()` only. A spec-writer can build every arm of AC-1 green and ship a
  criterion whose headline is false — the item buildable two ways (WI-144), in the one criterion that
  carries the Intent.
- *(b) A concrete failure, and it is the item's own machinery.* AC-2(c) has `update_fields` call the
  new rename door on a name change. `update_fields` picks its file at `base.py:438` from
  `_file_map[name.lower().strip()]` — one path per name, glob order. The census records live 2-note
  collisions (`docs/vault-shape-census.md:266-267`). So for an entity parsed from note A whose name
  is shared with note B, the door **moves note B**, appending A's old stem to B's `aliases` and
  leaving A untouched — the repair machinery relocating the wrong person's note, with the correct
  path sitting unread on the entity one frame away. Same defect for the six body-writers: a timeline
  entry for A lands in B, which is precisely the harm premise 9 describes and the "Examples of done"
  promises to end ("the timeline stays behind in the first"). The narrowing worth stating is that for
  an entity obtained from the cache the hazard does not arise — `_cache` and `_file_map` are filled in
  the same iteration under the same key (`base.py:244-246`), so they agree. The exposed population is
  entities NOT obtained from the cache: parsed directly (AC-1's own subject style), reconstructed, or
  handed across a consumer boundary.
- *(c) The ordering makes it un-deferrable.* Precondition 2 is HEAD-probed before the criteria are
  frozen (WI-300), and its five questions name only `.save(`/`update_fields(` call sites.
  `append_to_timeline` is plausibly the consumers' highest-volume write — Exocortex writes meeting
  timelines — and it is not in the question list. Commission the audit as written and the item's
  consumer blast radius is measured with its largest write path omitted; re-measuring is a second
  conductor act outside the cage. This is the question that has to be answered before the audit is
  ordered, not while the spec is being written.

**What would close it** — the document chooses and says so; I am not specifying it. Either
**(i) resolve every write target through one function**: a private `_write_target(entity)` that
returns the stamp when present and inside `vault_path`, else the name-derived path, called by `save`,
`update_fields` and the six body-writers, with Book's and Meeting's overrides routed through it too —
one seam, one place, which is what LESSONS #1 actually asks for ("a boundary you can route around was
never a boundary; it was a polite request"); or **(ii) declare the seam `save`-only and narrow the
promise**: restate AC-1's headline to the scope the mechanism covers, say in `## Approach` which paths
keep name-binding and why that is tolerable, note that Book/Meeting are deliberately outside it, and
add those paths to precondition 2's question list regardless so the residue is measured before the
repair rather than discovered after it. (i) looks the smaller change from here — the stamp already
exists on the entity at every one of those sites. Either way, the "read at one site" sentence is the
one to correct first, because it is what makes the gap invisible.

### Non-blocking notes

- **Correcting my own round 1.** My Generalization paragraph said "the seam is stated over
  `BaseRepository`, so Book/Company/Meeting inherit it." That is wrong for Book and Meeting — both
  override `save` with their own filename derivation (`book.py:167`, `meeting.py:189`). Company
  inherits and Person delegates. Do not build the scoping argument on that sentence.
- **The re-stamp on `update_fields`' reload is free but should be asserted.** `update_fields` reloads
  through `_load_file` (`base.py:493`), so once the parse stamps, the returned entity carries fresh
  provenance without extra work. One arm pinning that keeps a later refactor from silently returning
  an unstamped entity and regressing AC-2(e).
- **Observation in the fold's favour, worth a line in the spec if (ii) is chosen:** the six
  body-writers already refuse rather than misfire under `auto_load=False` — they raise `ValueError`
  on a `None` path (`person.py:1404`, `:1523`). The silent-fallback arm was `save`'s alone, and the
  fold closes it. So the residual exposure of the name-bound paths is the collision cross-write, not
  the unloaded-repository fork.

The mechanism substitution I asked for in round 1 was made properly and at the right boundary. This
round is the same class one step out: the seam is correct and is not yet the only door.

```verdict
gate: architect
verdict: REVISE
date: 2026-09-21
model: claude-opus-5
note: Provenance binding landed correctly at the parse and closed round 1, but only `BaseRepository.save` reads it — `update_fields` (base.py:438), six PersonRepository body-writers and Book/Meeting's `save` overrides still resolve targets by name, so AC-1's "no library write" is false and AC-2(c)'s rename door can move the wrong note of a live collision pair; widen the seam or narrow the promise, and fix precondition 2's question list before it is commissioned.
targets: AC-1, AC-2, #approach, #exploration-notes, #write-targets
prior: held
basis: original
findings: 1/3
```

## Architectural Review — 2026-09-21

**Recommendation: REVISE (round 3) — round 2's fold HELD and the seam is settled; the defect class's
EXTENSION over the frozen corpus is not what two criteria say it is**

Rounds 1 and 2 were mine. I re-executed round 2's fold site by site against this worktree
(`cage-wt-rix_vnom`, HEAD `6f045a9`) with Read/Grep, then — for the first time in this arm, and this
is the omission that produced this round — I ran AC-1's own subject PREDICATE over the frozen
manifest by hand instead of reading the criterion's claim about what it selects. It selects a
different set than either AC-1 or AC-3 says, and two of its members cannot be `save()`d at all.

### Trigger check

Unchanged, four fire: new public repository door; behaviour change on shipped write paths with
out-of-repo consumer blast radius; new lint check across three files; effort > 1 day.

### Round 2's finding: CLOSED, and closed better than I specified it

Verified against the code, not against the document's account of the code:

- **Premise 12 is CORRECT, site for site.** Grep for
  `write_markdown_file|vault_io\.write_note|get_file_path\(` over `obsidian_schemas/**` returns
  exactly the declared population: `base.py:398` (in `save`, target bound `:391-393`),
  `base.py:490` (in `update_fields`, target bound `:438`), `person.py:1447`/`1458` (bound `:1403`),
  `:1559` (bound `:1522`), `:1679` (bound `:1653`), `:1758` (bound `:1719`), `:1828` (bound `:1793`),
  `book.py:170` (bound `:167-170`), `meeting.py:192`. Nine. The `_get_body_content` narrowing is
  right — `person.py:1590-1592` returns `None` on a miss and writes nothing.
- **Narrowing (c) CONFIRMED**: `person.py:1404-1405` raises `ValueError` on a `None`-or-missing path,
  as do `:1523` and `base.py:440-441`. So the deviation the fold made from what I proposed in round 2
  — `_resolve_write_target` returning `None` and **never** falling back, each caller keeping its own
  fallback — is not a paraphrase of my option (i), it is a CORRECTION of it. My wording ("else the
  name-derived path") would have converted those three refusals into note creation, minting a new
  fork source inside the item that exists to close one. The document argues this from the code and
  states the asymmetry explicitly. That is an audit fold, not a compliance fold, and it is the reason
  this round does not re-open anything.
- **AC-5's two buckets are sound against today's tree.** `writer.py`'s four write sites (`:319`,
  `:393`, `:451`, `:504`) sit in `write_markdown_file`, `update_frontmatter_field`,
  `update_frontmatter_fields` and `roundtrip_file`, each taking `file_path` as its first parameter
  (`:160`, `:333`, `:405`, `:463`) — genuine path-taking leaves, so bucket (a) is a real category and
  not an escape hatch.
- Round 1's provenance finding stays closed; premises 10 and 11 re-confirmed (`parser.py:54`,
  `:236`, `:246-252`; three `_load_file` call sites; `writer.py:106-131` composing from
  `model_fields` + `model_extra` + `extra_fields` only; `models.py:31-32`'s `extra="allow"`).

No previous finding re-opened. This round's finding is a sibling neither previous round looked for,
because both of us checked the mechanism against the code and never checked the CORPUS against the
criteria.

### Blocking issue

**1. The stem≠name predicate selects FOUR person notes in the frozen corpus, not the two AC-3 pins
and not the three AC-1's rationale names — and on two of the four, `save()` cannot run at all,
because WI-021's gate refuses their stored name.**

Executed over `tests/fixture_vault.py`'s manifest, every `NoteSpec` with `declared_type="person"`
whose filename stem (less `@`) differs from `fields["name"]`:

| note | stored `name:` | manifest label |
|---|---|---|
| `@Quillam Ostrivane.md` (`:255-260`) | `Quillam Ostrivane Lumbrek` | `stem_name_divergence` |
| `@Quillam Lumbrek.md` (`:261-266`) | `Quillam Ostrivane Lumbrek` | `stem_name_divergence` |
| `@Perrowin Tessamund Drostane.md` (`:297-301`) | `Perrowin -> Tessamund Drostane` | `discriminator="arrow_connective"` |
| `@Yolvenna Brindlecote Skarnell.md` (`:302-306`) | `Yolvenna/Brindlecote Skarnell` | `discriminator="path_hostile"` |

And `@Quillam Ostrivane Lumbrek.md` (`:273-276`) is **not** selected — its stem and its name agree.
Three consequences, in ascending order of cost:

- *(a) AC-1's `why` is false in both directions.* It states the predicate "picks up all three
  `Quillam` notes, including the collision third that carries no `shape_classes`". The collision
  third is exactly the member a stem≠name predicate cannot pick up, and the two members it does pick
  up unannounced are specimens frozen for the name-gate neighbourhood. The `desc` (the predicate) and
  the `why` (its stated consequence) disagree about the same manifest, and the `why` is the half a
  spec-writer reads to understand what the derivation is FOR. Note this does not damage AC-1(c): the
  collision third still enters as a *member of a name-sharing group*, which is a second derivation
  the criterion uses and never defines.
- *(b) Two of the four subjects make AC-1's sweep raise instead of assert.* `save()` routes through
  `write_markdown_file(entity=…)`, which sets `gate_whole_record = True` (`writer.py:229-233`) and
  calls `gate_write` above the lock (`:252`). `name_validation.py`'s Tier-1 branches include
  `arrow_connective` (`:214-225`, regex `->|[→⟶⇒➜↦⇨]`) and `path_hostile` (`:249-259`, `/`), so both
  extra subjects are refused with `NameGateRefusal` before a byte is written —
  `name_gate.py:33` states the intent outright ("permanently refuse every note whose STORED name is
  already Tier-1 dirty"). AC-1 says "for EVERY (subject, path) pair, apply that path's minimal
  non-name mutation and assert (a)(b)(c)"; for these two on the `save` path there is no write to
  assert about. The other paths are unaffected — the five body-writers reach `vault_io.write_note`
  directly and `update_fields` gates the delta with `whole_record=False` (`base.py:483-485`) — so
  this is two cells of the matrix, not two subjects.
- *(c) AC-3 is RED against the corpus for a correctly-written detector, and GREEN only for a wrongly
  written one.* (a) pins "one ERROR for each of the **two** notes the manifest declares in that
  class" and (b) pins "emits nothing for the ~50 other corpus notes". A detector written to the
  DEFINITION emits four. The only implementation that passes both arms as written is one keyed on
  `shape_classes` — i.e. one where the manifest label IS the defect class, which is precisely what
  AC-1's own `why` forbids ("the label is not the class"). So the two criteria that between them
  define this item's defect class disagree about its extension over one frozen corpus, and the
  disagreement resolves toward the wrong implementation. That is WI-144, in the detector that is half
  the Intent.

**Why this blocks rather than waits for the spec-writer**, on the same test round 2 turned on:
`docs/stem-divergence-live-baseline.md` is a `kind: precondition`, HEAD-probed before the criteria
freeze, and its per-note direction table currently asks two questions — which side is correct, and
is `@{name}.md` occupied. The gate adds a third that the corpus just demonstrated is real: **is the
stored `name:` itself Tier-1 dirty?** For such a note "rename the file to match the stored name" is
not merely wrong, it is unexecutable — `@{name}.md` for a name containing `/` is a different
directory, and the entity cannot be `save()`d either. The census's eight live shapes include
"a book-titled file holding a person note" and "a first-name-only stem"
(`docs/vault-shape-census.md:262-265`), which is the population where a dirty stored name is most
likely. Commission the baseline without that column and the direction table comes back with rows
that cannot be executed; re-commissioning is a second conductor act outside the cage. That is the
same un-deferrable ordering that made round 2 a round.

**What would close it** — the document chooses and says so; I am not specifying it. The three things
that need to be written down: (1) the corpus's ACTUAL divergent population, with AC-3's counts
restated to it and AC-1's `why` corrected (and, if the two gate-neighbourhood specimens are to be
excluded from AC-1's sweep, a stated RULE for the exclusion rather than a hand-list — "subjects whose
stored name the gate refuses" is such a rule, and asserting the `NameGateRefusal` as that cell's
expected outcome is a defensible alternative: a name the gate refuses is a name that can never fork,
which is a true and cheap thing for the sweep to pin); (2) whether the detector reports a diverged
note whose stored name is Tier-1 dirty — it should, since that is the shape the repair most needs to
see, but AC-3 must then say what the ERROR says about a note that cannot be renamed to its name;
(3) the third column on precondition 1's direction table, added before the baseline is commissioned.

### Non-blocking notes

- **`## Approach` counts the body-writers twice-over.** It reads "All nine name-bound write paths in
  the package call it first (premise 12): `save`, `update_fields`, the **six** `PersonRepository`
  body-writers, and Book's and Meeting's `save` overrides" — a list of ten described as nine, and
  "six" contradicts premise 12, the blast-radius bullet and AC-1, all of which say five mutating
  body-writers with `_get_body_content` deliberately outside the write-path scope. Trivial to fix and
  worth fixing precisely because it is the section the spec-writer formalizes from: as written it
  invites routing a READ helper through the write seam, which no criterion covers.
- **AC-5's enumeration knows two door names; the tree declares three.** It scans "every call to
  `write_markdown_file` or `vault_io.write_note`", while `tests/derivations.py:47` already carries
  `DOOR_NAMES = frozenset({"write_note", "create_note", "move_note"})` from WI-026/WI-031. Today the
  gap is harmless — `create_note`'s only in-package caller is `writer.py:317`, inside a path-taking
  leaf — but this item's OWN rename door writes through `move_note`, so the wall as scoped does not
  enumerate the one new door the item ships, and a tenth path built on `create_note` passes it while
  the criterion's headline says it cannot. Reuse `DOOR_NAMES` rather than a two-name list.
- **Say that the comparison is raw-vs-raw.** AC-3(b) already pins it implicitly by listing the
  whitespace-damaged note (`@Dave  Marrowyn Fennwick.md`, stem and stored name both carrying the
  double space, `tests/fixture_vault.py:246-254`) among the silent ~50 — under a `clean_person_name`
  comparison that note IS divergent (`verdict=cleaned="Dave Marrowyn Fennwick"`). One sentence, since
  the cleaner is one import away and a builder may reasonably reach for it.
- The seam itself, the door, the fallback asymmetry, AC-2 and AC-4 are unchanged by this round and I
  found nothing further in them.

The mechanism is settled and I do not expect to revisit it. What is open is one sentence-level
question — *which notes ARE the class* — asked of the corpus rather than of the code, and answered
before the baseline is ordered.

```verdict
gate: architect
verdict: REVISE
date: 2026-09-21
model: claude-opus-5
note: Round 2's seam fold held and improved on what I specified, but the stem≠name predicate over the frozen manifest selects four person notes (the two Quillams plus the `arrow_connective` and `path_hostile` specimens) and NOT the collision third — so AC-1's rationale is false both ways, `save()` on two derived subjects raises `NameGateRefusal` (writer.py:229-233 → name_validation.py:214/249), AC-3's two-ERROR pin is green only for a detector keyed on the manifest LABEL that AC-1 forbids, and precondition 1's direction table needs a "is the stored name Tier-1 dirty" column before it is commissioned.
targets: AC-1, AC-3, AC-5, #approach, #write-targets
prior: held
basis: original
findings: 1/4
```

## Architectural Review — 2026-09-21

**Recommendation: REVISE (round 4) — round 3's fold HELD, note for note; the RULE it added is not
total, and the one branch it misses is a measured live shape**

Rounds 1–3 were mine. I re-executed round 3's fold against this worktree (`cage-wt-rix_vnom`,
HEAD `6f045a9`) with Read/Grep — including re-deriving the divergent population by hand over the
manifest rather than reading the document's table — and then, for the first time in this arm, I read
the Tier-1 table as a TABLE rather than as two of its records. It declares a flag that the new rule
does not consult, and the exemption that flag marks is live in the vault this item repairs.

### Trigger check

Unchanged, four fire: new public repository door; behaviour change on shipped write paths with
out-of-repo consumer blast radius; new lint check across three files; effort > 1 day.

### Round 3's finding: CLOSED, and verified against the manifest rather than against the fold

- **Premise 13's population re-derived independently and CONFIRMED, note for note.** Reading `NOTES`
  in full (`tests/fixture_vault.py:217-479`) and applying the predicate by hand: 22 person notes
  declare `fields` (which `LOADABLE`'s own comment corroborates, `:521`), and exactly four have a
  stem that differs RAW from `fields["name"]` — `@Quillam Ostrivane.md` (`:255-260`),
  `@Quillam Lumbrek.md` (`:261-266`), `@Perrowin Tessamund Drostane.md` (`:297-301`),
  `@Yolvenna Brindlecote Skarnell.md` (`:302-306`). `@Quillam Ostrivane Lumbrek.md` (`:273-276`) is
  NOT selected, `@Dave  Marrowyn Fennwick.md` is NOT selected raw (`:246-254`), and `@+447700900123.md`
  is not selected either (`:288-293` — its stem and stored name are the same digit string).
- **The two `pattern` values CONFIRMED at the table**: `arrow_connective` carries
  `pattern="calendar_prefix"` (`name_validation.py:214-225`) and `path_hostile` carries
  `pattern="path_hostile_char"` (`:249-259`). The document's insistence on the `pattern` field over
  the `branch_id` is right and is the table's own stated rule (`:152-154` — three branches share
  `calendar_prefix`).
- **The gate-refused `save` cell CONFIRMED**: `write_markdown_file` sets `gate_whole_record = True`
  on the `entity is not None` arm (`writer.py:229-233`) and calls `gate_write` at `:252-253`, above
  `note_lock` at `:258`. A `save()` of either specimen raises before a byte is written.
- **Premise 13(c) CONFIRMED at the code and at its comment**: `update_fields` hands the gate
  `updates` — the delta — with `whole_record=False` (`base.py:483-485`), and `:466-469` states the
  intent verbatim. So the other eight paths really do assert normally for those two subjects, and
  treating the refusal as two CELLS rather than two subjects is correct.
- **AC-5's rebinding is real**: `tests/derivations.py:47` carries
  `DOOR_NAMES = frozenset({"write_note", "create_note", "move_note"})`, and `update_fields` commits
  through `vault_io.write_note` (`base.py:490`), so the wall's enumeration reaches it.
- **`## Approach` now counts nine and lists five** body-writers, with `_get_body_content` named as the
  read-side sibling outside the write seam. The arithmetic closes: 1 + 1 + 5 + 2.

No previous finding re-opened. Rounds 1→2→3 moved mechanism → scope → extension, and each fold has
survived a re-read. This round's finding is the first to land on material a fold ADDED rather than on
the original draft.

### Blocking issue

**1. "A name the gate refuses can never fork" is the load-bearing justification for round 3's rule,
and it is false for one of the ten Tier-1 branches — the one the live vault has two of. The rule asks
`validate_strict`; the gate asks something else.**

Round 3's fold replaced a hand-list with a rule, which was the right move, and stated its warrant in
`## Exploration Notes` ("Constraints discovered"): *"A name the gate refuses can never fork … which
keeps the subject derivation total: a future corpus member whose stored name trips a different Tier-1
branch joins the sweep with the right expectation automatically."* The rule is then written into four
places — AC-1's gate-refused cell, AC-3(c)'s marker, AC-4's consistency rule, and precondition 1's
column (b3), which names `NameValidator.validate_strict` by hand.

The table those four consult declares a flag they do not read. `Tier1Branch` carries
`sentinel_exempt`, documented at `name_validation.py:155-156` as *"the one branch the WI-083
phone-sentinel exemption suppresses"*, and `pure_digit` sets it `True` (`:287`). The suppression is
not theoretical and it is not opt-in at the call site this item cares about: `gate_write` DERIVES it
from the payload —

```
allow_phone_sentinel = (bool(introduced.get("phones"))
                        and name_text.strip().lstrip("+").isdigit())   # name_gate.py:355-358
```

— and hands it to `validate_strict` (`:361-363`), which returns the name untouched
(`name_validation.py:608-609`). Meanwhile `validate_strict`'s own default is
`allow_phone_sentinel=False`, *"Off by default to keep producers honest"* (`:594`, `:599-601`). So the
predicate the document tells the sweep, the detector and the conductor to run answers REFUSED for a
phone-only stub, and the code answers WRITTEN. The corpus's own manifest says the same thing in its
comment on `@+447700900123.md` (`tests/fixture_vault.py:283-287`): that specimen declares NO `phones`
precisely so the branch fires, which is the manifest documenting the exemption it was built to avoid.

Three consequences, ascending:

- *(a) AC-1's declared outcome is wrong for a plantable subject.* AC-1 requires planted members ("PLUS
  the planted members the corpus cannot supply"), and a divergent phone stub — `@447700900123.md`
  carrying `name: "+447700900123"` and a `phones:` list, which is exactly what `create_stub` mints
  (`person.py:1271-1272` derives the same sentinel flag) — makes the rule predict `NameGateRefusal`
  while `save` writes the file. The sweep's expectation fails on a correct implementation. The
  totality claim that justified the rule over a hand-list is what breaks.
- *(b) AC-3(c) ships a FALSE message over a measured live population.* The marker is specified to say
  "the divergence cannot be repaired by renaming the file". For a phone stub that is wrong twice: the
  gate permits the save, and `@+447700900123.md` is a perfectly ordinary filename — `_PATH_HOSTILE_RE`
  is `/` and nothing else (`name_validation.py:107`), which is why `path_hostile` is its own branch.
  Rename is the correct repair there, and the detector would tell Dave it is impossible. The census
  measures `pure_digit` at **2 live person notes**, `+<11-12 digits>` (`docs/vault-shape-census.md:148-153`,
  `:260-261`) — MEASURED, not ABSENT.
- *(c) It reaches the conductor artifact, which is why it blocks now rather than at speccing.*
  Precondition 1's (b3) tells the conductor to run `validate_strict` and "record the refusal `pattern`
  where it fires"; AC-4 then asserts "NO row resolves to `rename` while declaring a gate-refused
  stored name". If either of the two live pure-digit notes is also among the eight divergent — which
  is precisely the question precondition 1 exists to answer, and which no caged reader can settle —
  the table comes back declaring a refusal for a row whose only correct direction is rename, and
  AC-4's own shape check refuses it. That is an internally contradictory table, commissioned once,
  outside the cage. It is the same un-deferrable ordering that made rounds 2 and 3 rounds, applied
  this time to round 3's own fold.

**What would close it** — the document chooses and says so; I am not specifying it. The rule needs to
ask the question the WRITE DOOR asks, not the question `validate_strict` asks by default: either
consult `sentinel_exempt` explicitly (`name_validation.py:287`) and declare the sentinel-exempt branch
a non-refusal when the note declares `phones`, or state the predicate as "what `gate_write` would do
with this note's own payload" (`name_gate.py:355-358`) and let one derivation serve AC-1's cell,
AC-3's marker, AC-4's rule and precondition 1's column. Whichever spelling, it is one clause in one
place and the other three inherit it — which is the argument for saying it once rather than three
times.

### Non-blocking notes

- **"Unexecutable" generalizes from one branch, and the constraint states it as though it covered
  all.** `## Exploration Notes` argues the third repair direction from `@{name}.md` for a name
  containing `/` naming a file in another directory — true, and true only of `path_hostile`.
  `@Perrowin -> Tessamund Drostane.md` is a legal filename; what is refused there is the `save()`,
  not the move, and the same holds for `archive_prefix` and `unknown_contact` rows should the live
  table contain any. The prohibition on renaming to a gate-refused name is still the right POLICY —
  repair the field, then the stem follows — but it should be stated as a policy with its reason
  ("we do not mint filenames from names the package refuses to write"), because a spec-writer
  generalizing from "it is unexecutable" will meet a row where it plainly is executable.
- **AC-2(c)'s door call lands inside a held lock and inside a live stamp, and the reload is the
  casualty.** Door 3 is explicitly safe to call from a frame already holding the source lock — it
  sorts the two resolved paths and the locks are reentrant (`vault_io.py:744-750`). What is not free
  is the rest of `update_fields`' frame: `move_note` calls `forget_snapshot(source)` (`:780`), while
  `update_fields` still holds `stamp` from `read_note` (`base.py:449`) and later commits with
  `precondition=stamp` against the OLD `file_path` (`:490`), then reloads from that same stale path
  (`:493`) and raises `ValueError` when the reload returns `None` (`:494-495`). So the ordering
  inside that method — content write, then move, then rebind `file_path` to the door's return value
  before the reload — is a real sequencing constraint rather than a detail. AC-2(g) is already the
  oracle that catches it; one line in the spec naming the ordering would stop the build discovering
  it as a failing test.
- The seam, the one resolution function, the fallback asymmetry, the door, AC-2 and AC-5 are
  unchanged by this round and I found nothing further in them. Premise 13's table, AC-1's union
  subject derivation and AC-3's four-ERROR pin are correct as written; the correction above is to the
  rule that decorates them, not to the population they quantify over.

Three rounds have each closed and narrowed. This one is a clause inside the last fold, not a new
class — the smallest finding of the arc, on the smallest surface, and the last place I would expect
to look, which is why it took a fourth read to see it.

```verdict
gate: architect
verdict: REVISE
date: 2026-09-21
model: claude-opus-5
note: Round 3's fold held note-for-note, but the Tier-1 RULE it added is not total — `pure_digit` is `sentinel_exempt` (name_validation.py:155-156, :287) and `gate_write` derives `allow_phone_sentinel` from the payload (name_gate.py:355-358), so a divergent phone-only stub is WRITTEN where AC-1's cell predicts `NameGateRefusal`, AC-3(c) would mark a renameable note unrenameable over a population the census measures at 2 live, and precondition 1's (b3) + AC-4 would forbid the one correct direction in a table commissioned once outside the cage.
targets: AC-1, AC-3, AC-4, #write-targets, #exploration-notes
prior: held
basis: folded-material
findings: 1/3
```

## Architectural Review — 2026-09-21

**Recommendation: PROMOTE to architected — round 4's fold HELD, and the arc has closed**

Rounds 1–4 were mine. I re-executed round 4's fold against this worktree (`cage-wt-rix_vnom`,
HEAD `6f045a9`) with Read/Grep — the Tier-1 table record by record rather than two of its rows, the
door's own derivation, `validate_strict`'s signature, the four sites that were supposed to inherit
the one predicate, and AC-5's asserted foundation in `tests/derivations.py`. Everything holds. I then
went looking for a fifth sibling in the same class — a population the stated predicate answers
differently from the code — and found two, both inert over every set this item quantifies over and
both measured at zero or excluded by construction. Neither buys a round. They are notes.

### Trigger check

Unchanged, four fire: new public repository door; behaviour change on nine shipped write paths with
out-of-repo consumer blast radius; new lint check across three files; effort > 1 day.

### Round 4's finding: CLOSED, and closed at the right altitude

- **Premise 14 CONFIRMED, record by record.** `Tier1Branch` declares `sentinel_exempt: bool`
  (`name_validation.py:166`), documented at `:155-156` as *"the one branch the WI-083 phone-sentinel
  exemption suppresses"*. Walking the whole person table: `email_chars` (`:195`), `rfc2822_leak`
  (`:206`), `arrow_connective` (`:218`), `calendar_prefix` (`:230`), `me_to_prefix` (`:242`),
  `path_hostile` (`:253`), `archive_prefix` (`:264`), `unknown_contact` (`:275`) and `empty` (`:304`)
  all set it `False`; `pure_digit` (`:285-294`) sets it `True` at `:287`. Exactly one, as the document
  says. (The five `COMPANY_TIER1_BRANCHES` records, `:374-436`, are all `False` too — so the
  exemption is a person-table fact and nothing about the company arm needs restating.)
- **The door's derivation and the validator's default CONFIRMED, and they really do disagree.**
  `gate_write` computes `allow_phone_sentinel` from the payload at `name_gate.py:355-358` and hands it
  to `validate_strict` at `:361-363`; `validate_strict`'s own signature defaults it `False`
  (`name_validation.py:594`) with the docstring reason at `:599-601`, and its first executable line is
  the early return `if allow_phone_sentinel and _PURE_DIGIT_RE.match(name.strip()): return
  name.strip()` (`:607-609`). So for the planted subject — `name: "+447700900123"` with a non-empty
  `phones:` — `"+447700900123".strip().lstrip("+").isdigit()` is `True`, the door returns the name
  untouched, and the bare validator raises `pure_digit_name`. **The planted member discriminates the
  two implementations exactly as AC-1 and AC-3(c) claim.** That is a real WI-286 plant, not a coverage
  fixture.
- **The "state it ONCE and inherit it" discipline is actually observed.** I read all four inheriting
  sites. AC-1's gate-refused cell, AC-3(c)'s marker, AC-4's consistency rule and precondition 1's
  (b3) each cite the `## Exploration Notes` paragraph and each say explicitly that the predicate is
  NOT `NameValidator.validate_strict`. No site re-spells the question. Round 4's own diagnosis was
  that four spellings of one question is how the drift survived three rounds; the fold fixed the
  spelling *and* the structure that produced it, which is why I expect this one to stay closed.
- **AC-5's foundation is real, not aspirational.** `tests/derivations.py:47` carries
  `DOOR_NAMES = frozenset({"write_note", "create_note", "move_note"})`; `_is_write_call`
  (`:286-298`) already gates on `{"write_text", "write_bytes"} | DOOR_NAMES`; `PACKAGE_ROOT` is
  `obsidian_schemas` (`:31`) and the module is the single declared place permitted to name the tree's
  paths (`:14`). AC-5 extends shipped machinery by one classification rule, which is what its cost
  estimate assumes.
- **The two non-blocking notes were both folded properly rather than acknowledged.** The
  "unexecutable" argument is now a POLICY with its reason — *we do not mint a filename from a name the
  package refuses to write* — with literal impossibility correctly narrowed to `path_hostile`
  (`_PATH_HOSTILE_RE` is `/` and nothing else, `name_validation.py:107`, `:251-259`). And
  `update_fields`' write → move → rebind ordering is stated in `## Approach` (2) with AC-2(g) as its
  oracle, which is the right pairing: the constraint is named where the builder reads it and pinned
  where a refactor would break it.

No previous finding re-opened, in four consecutive re-reads. Rounds 1→2→3→4 moved mechanism → scope →
extension → predicate, each strictly inside the last, and each fold has survived an independent
re-execution. That is a converging ladder and it has reached its floor.

### Review

**Fit:** Strong, and unchanged across the arc. Seam-then-repair-then-invariant is this project's own
shape (WI-026's detector + committed live bracket; WI-031's containment wall). AC-4's split — a
hermetic check over a committed artifact, the live measurement as a conductor ship condition — is the
honest treatment of a live-corpus repair rather than a hermetic test pretending to certify
production. The `kind: precondition` fences cover exactly the two facts a caged reader cannot reach,
in WI-300 order.

**Duplication:** None. `move_note` exists and is unexercised for this use (`vault_io.py:721-783`,
one caller at `scripts/lint_vault.py:1343`); the door is built on it. `gate_write` is already imported
by the linter (`lint_vault.py:1107`), so AC-3's marker adds no new coupling between the tool and the
package. AC-5 reuses `tests/derivations.py` rather than growing a second scanner.

**Boundaries:** Clean. One capability, one owner: the parse owns provenance, `_resolve_write_target`
owns target selection, one door owns relocation, the linter owns detection and never repair. The
WI-185 question is answered at the structure's source rather than reconstructed downstream — premise
10 re-confirmed (`parser.py:54`, `:236`, `:246-252`; three `_load_file` call sites discarding
`doc.file_path`). The fallback asymmetry is the load-bearing detail and it is argued from the code,
not asserted: a uniform fallback would convert `person.py:1404-1405` / `base.py:440-441`'s refusals
into note creation.

**Determinism boundary:** n/a — nothing is handed to an LLM. The one judgement call, per-note repair
direction, is correctly routed to a committed human-signed table with a shape check, not to a rule.

**Reversibility:** Good. Detector read-only; repair per-note through a door that refuses an occupied
destination by syscall and links-then-unlinks. The seam is the one hard-to-reverse act and it is the
one with a consumer audit in front of it.

**Generalization:** Correctly scoped, and round 2 corrected my own round-1 error here — Book and
Meeting do NOT inherit `BaseRepository.save` (`book.py:167-170`, `meeting.py:189-192`), which is why
they are named call sites rather than assumed. The detector is person-shaped, matching the measured
class; WI-022's seven company notes stay a spec-time scoping question.

**Cost & maintenance:** One build session at its upper end, plus two conductor acts. Nine one-line
call-site edits, one helper, one declared private attribute, one door, one check, one derived scan —
no new dependency, no schema change, no public signature change. Ownership is unambiguous: the seam
lives where the package's own conventions put it.

**Build vs extend vs integrate:** Extend, throughout.

**Prior art (outside view):** Unchanged from round 1 — the world's answer to filename/field divergence
is to stop making the filename the identity (Notion, Roam: immutable id, title as label), and that
option is closed by the platform rather than by preference, since in Obsidian the filename IS the
wikilink target. No compensation machinery, no recurrence of a worked-around constraint. Worth
repeating that WI-125's identifier index already is an id-based identity layer inside this package,
and the provenance stamp is the same move one level down.

### Notes for the spec-writer (non-blocking)

- **The door predicate is one frame off, and the frame is inert — but say the true one.** The
  paragraph calls itself *"the exact call `write_markdown_file` makes"*. Two small inaccuracies:
  (i) the payload that arm gates is `model_to_frontmatter(entity)` (`writer.py:230`), the entity
  PROJECTION, not the note's stored frontmatter; (ii) for a **Person** the decisive gate call is not
  that one at all — `PersonRepository.save`'s WI-021 rider calls
  `gate_write(model_to_frontmatter(entity), declared_type=self.type_name, whole_record=True)` at
  `person.py:1190-1191`, *before* `super().save()`, so it raises first. Neither changes an expected
  outcome anywhere in this document: the rider passes the same payload and the same branch, so the
  raised `pattern` is identical, and projection and stored record agree on all three inputs a refusal
  reads (`name` — the parser applies no cleaner, `clean_person_name` appears only at
  `person.py:975`, in a resolution helper; `phones`; `type`). The single class where they part is a
  note with **no stored `type:`**: the predicate as spelled refuses it via rule (ii)
  (`name_gate.py:305-306`) while `save` writes it, because `Person.type` is
  `Literal["person"] = "person"` (`models.py:78`) and `model_to_frontmatter` emits every declared
  field (`writer.py:112-117`). That class is live — the mint books four untyped notes as hand
  repairs — but `lint_vault` types a note off its stored record (`:176`) and has a separate
  `missing_type` ERROR for exactly this shape (`:372-377`), so a `type`-gated detector never admits
  one and the contradiction cannot reach precondition 1's table. Spelling the predicate over the
  entity projection — or, simplest and truest, as *"would `repo.save(<entity parsed from this
  note>)` raise, and with what `pattern`"* — makes the frame question disappear and costs a clause.
- **The class definition is undefined for a person note carrying no `name:` at all.** "Stem differs
  RAW from its stored `name:`" reads as divergent when there is no stored name to differ from. The
  stake today is zero and measured both ways: `person_missing_name` is **0 live** at both ends of the
  WI-026 bracket (`docs/lint-vault-live-baseline.md:82`, `:149`) and has **0 corpus subjects**
  (`docs/lint-vault-fix-safety.md:109`). But the shipped linter already owns that shape with an
  AUTO-FIXABLE rule repairing in the opposite direction — `lint_vault.py:436-446` emits it,
  `--fix` writes `fm["name"] = fpath.stem.lstrip("@")` at `:1043-1045` — so if the new check also
  claims such a note, one note carries an auto-fixable ERROR and a never-fixable ERROR that the first
  one silently repairs away, which is a confusing row on the report and an odd interaction with
  AC-3(d)'s accounting. One clause: a note with no stored `name:` belongs to `person_missing_name`,
  not to this check.
- **AC-5 enumerates a strict subset of a predicate that already exists.** It scans
  `write_markdown_file` plus `DOOR_NAMES`; `_is_write_call` (`tests/derivations.py:286-298`) gates on
  `{"write_text", "write_bytes"} | DOOR_NAMES`. Reusing the predicate rather than the frozenset alone
  closes a tenth path built on a bare `Path.write_text`, by the criterion's own stated argument for
  reusing `DOOR_NAMES` over a hand-written pair.
- **AC-1's gate-refused cell cites the frame that raises second.** Per the first note, for a Person
  subject `person.py:1190-1191` raises before `writer.py:252-253`. The cell's declared outcome —
  `NameGateRefusal` carrying that `pattern`, no file changed — is correct either way (the rider is
  above every write, and `writer.py:252-253` is above `note_lock` at `:258`). Worth one line so a
  builder who asserts on a traceback frame rather than on the exception does not chase it.
- **Two things I am deliberately not asking for.** The `_get_cache_key`/`get_file_path` strip
  asymmetry (`base.py:319-321` vs `:365`) stays out of scope and the document is right that provenance
  binding makes it non-load-bearing. And precondition 1's privacy wall (counts, classes and
  directions; no filenames, no bytes, no absolute paths) is correctly inherited from the census and
  the WI-026 baseline — the direction table can carry all three of its columns without quoting a
  single live name.

The mechanism, its scope, the class's extension and the predicate that decorates it have each been
challenged and each survived a re-read. What is left is spec-writer work: formalize the nine call
sites, the door's ordering inside `update_fields`, the detector's two arms and the derived scan's
bucket rule. Nothing here needs redesigning during speccing, which is the bar this gate is calibrated
to.

```verdict
gate: architect
verdict: PROMOTE
date: 2026-09-21
model: claude-opus-5
note: Round 4's fold holds under independent re-execution — `pure_digit` is the sole `sentinel_exempt` record (name_validation.py:287), the door derives the flag (name_gate.py:355-358) where `validate_strict` defaults it False (:594), the planted phone stub genuinely discriminates the two implementations, and all four sites now inherit one predicate instead of re-spelling it; four rounds have each closed and narrowed with nothing re-opened, and the two residues I found this round (the predicate's payload frame, and a `name:`-less note) are measured at zero or excluded by construction and are spec-time notes, not approach defects.
```

## AC Red-Team — 2026-09-21

Cold-start read on a different model from the architect that authored this arm (`claude-opus-5`). Read
`## Intent`, `### Examples of done`, `## Problem / Motivation`, and the exploration sections before the
criteria, per Step 2. I then re-executed two of the document's own load-bearing corpus claims by hand
rather than trusting the architect's four rounds of re-execution: premise 13's divergent-population count
over `tests/fixture_vault.py`'s manifest (person notes with declared `fields`, stem vs. `name:` compared
raw) reproduces at exactly four — `@Quillam Ostrivane.md`, `@Quillam Lumbrek.md`,
`@Perrowin Tessamund Drostane.md`, `@Yolvenna Brindlecote Skarnell.md` — and premise 14's Tier-1 table
read (`name_validation.py:190-304`) confirms `pure_digit` is the sole `sentinel_exempt` record and that
`gate_write` (`name_gate.py:355-358`) derives `allow_phone_sentinel` from the payload where
`validate_strict`'s own default is `False` (`:594`). Both premises hold under independent re-execution.
That narrowed the search to the ACs' own construction rather than the mechanism, which four architect
rounds already attacked hard.

**Finding — AC-1, CRITICAL.** AC-1's planted Book and Meeting subjects are not required to be
*divergent*, and AC-5's SEAM-ROUTED bucket is a pure call-presence check — together they let Book's and
Meeting's `save()` overrides fake provenance-binding while doing none of the work the Intent and this
item's own Approach section (`### One target function, not one read site`, "Book and Meeting stop being a
hole in the seam for one line each") name as the point of touching those two sites at all.

*The failure scenario, concretely.* `BookRepository.save` and `MeetingRepository.save` derive their write
target from `self._get_file_name(entity)` — a title/date-derived path recomputed from the entity's
*current* fields (`book.py:167`, confirmed by direct read: `filename = self._get_file_name(entity)` then
`file_path = self.vault_path / filename`), structurally identical to `@{name}.md` for Person. A minimal
implementation of "the seam" for these two sites is: add one line, `self._resolve_write_target(entity)`,
call it and discard the return value, and leave the existing `_get_file_name`-derived write untouched.
- **AC-5 passes.** Its SEAM-ROUTED bucket is defined purely as "the function calls
  `_resolve_write_target` in its own body before it writes" (AC-5 `desc`) — a structural, not a
  data-flow, requirement. Nothing in the criterion or its escape battery (path-taking leaf / seam-routed
  writer / read-only `get_file_path` user / function naming `_resolve_write_target` only in a comment)
  requires the WRITE PATH to be *derived from* the function's return value. "Call it and ignore it" is a
  fifth near-miss the stated battery never names, let alone plants.
- **AC-1 passes.** Its desc restricts the Book/Meeting path set to "that type's `save`" and says nothing
  about the planted subject needing to be divergent — unlike the Person subject set, which is explicitly
  derived from the DIVERGENT/NAME-SHARING predicates so the seam is exercised on exactly the population
  where name-derived and provenance-derived paths disagree. Arms (d)–(g), which DO plant divergence-style
  discriminators (the free-destination arm, the genuinely-new arm, the round-tripped arm, the unloaded
  arm), are all written against `@{name}.md` — Person's own filename rule — and never extended to Book or
  Meeting. Apply AC-1's stated procedure to a planted Book/Meeting subject whose title/date fields have
  NOT been mutated: `_get_file_name(entity)` recomputes the same file the subject was parsed from whether
  or not `_resolve_write_target`'s return value was ever consulted, so arm (b) ("the changed bytes are in
  the file that subject was parsed from") holds trivially and arm (c) is vacuous — Book/Meeting have no
  name-sharing predicate defined at all, so "every other member of that group" is an empty set.

The two sites this defeats are not incidental — they are the exact ones round 2's architect fold (the
`prior: held` round, `targets: AC-1, AC-2`) identified as consequential enough to widen the seam over, and
premise 12/the Approach section name them as "a hole in the seam" closed "for one line each." A builder
optimizing for green ACs has a one-line incentive to leave that hole open. The census's own "book-titled
file holding a person note" shape (one of this item's booked hand repairs) is a live specimen of exactly
the risk this gap leaves unclosed — a Book- or Meeting-shaped write whose current derived filename has
drifted from the file it lives at, which is precisely the case AC-1 needs a planted, divergent Book/Meeting
subject to catch and does not.

**What would close it** (naming the defect, not designing the fix — that is the author's job): AC-1 must
plant at least one divergent Book subject and one divergent Meeting subject — parsed from a file whose
current `_get_file_name(entity)` output does NOT match the file it was parsed from — and assert (b)/(c)
against that mismatch the same way the Person divergent set is exercised; and/or AC-5's SEAM-ROUTED bucket
must require that the value handed to the write call is DERIVED FROM `_resolve_write_target`'s return
(a data-flow property, not a call-presence one), with "calls the function but writes to a
separately-derived path" added to the escape battery as the near-miss it currently omits. Either change
alone closes the gap; both together is what the rest of this document's own standard (WI-286: membership
is not correctness, plant the discriminating member) would ask for.

I attacked the remaining criteria — AC-2's collision-pair door test (uses the real live-shaped Quillam
pair, not a hand-picked stand-in), AC-3's four-count derivation and door-predicate marker (matches my own
re-execution), AC-4's shape/consistency check, and AC-5's bucket classification apart from the data-flow
gap above — and found nothing else material. The `check:` keys are bare function names, not node ids.
Every empirical premise I sampled reproduced.

```verdict
gate: ac-red-team
verdict: REVISE
date: 2026-09-21
model: claude-sonnet-5
note: AC-1 never plants a divergent Book/Meeting subject and AC-5's SEAM-ROUTED bucket only checks that `_resolve_write_target` is CALLED, not that its return value drives the write path — so a Book/Meeting `save()` override that calls the function and discards the result, keeping today's `_get_file_name`-derived write, passes every AC while leaving exactly the two sites premise 12/round-2's fold flagged as "a hole in the seam" unclosed.
targets: AC-1, AC-5, #approach
prior: none
basis: original
findings: 1/1
```

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
