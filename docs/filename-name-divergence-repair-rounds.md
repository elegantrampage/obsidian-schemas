# Filename/name divergence repair: rename the forked stems, then pin the invariant — archived gate rounds

<!-- archive-split:v1 — IMMUTABLE APPEND-ONLY ARCHIVE. Written only by src/archive_split.py at a
completed conveyor transition; appended to, never edited, reordered or rewritten. It
carries no work-item frontmatter by design, so it is invisible to find_work_items and to
find_corrupt_work_item_docs. Living spec: docs/filename-name-divergence-repair.md -->

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


## Threat Model — 2026-09-26

**Recommendation: PROMOTE to threat-modeled — round 5. M1 through M6 all HELD: I re-verified each against
the code or the artifact it prescribes, every ordinal is unmoved, and the six fences below are RE-EMITTED
with byte-identical `desc`. The FOURTH fold — M6 — is correct at every site it touched, and I checked its
one new behaviour (a configuration read inside a write path) for the two ways it could have gone wrong:
it could not. The finding this round is inside the fold, and it is the fold's own widening that made it
findable: the new precondition table in Design §2 declares the M1-class member "already refused earlier,
by a different wall", and that wall is `gate_write`, which validates a `name` delta for exactly TWO
declared types. For every other type it returns the delta UNTOUCHED
(`obsidian_schemas/name_gate.py:319-344`), and `update_fields`' rename trigger reads the CALLER'S dict
and the NOTE'S frontmatter — it consults `model_fields` nowhere — so the "`Book` and `Meeting` cannot
reach it" premise the table and two other surfaces rest on is a non-sequitur, and Task 3's own
`resolved`-first binding is what makes it reachable. One new required mitigation, M7, one conjunct on the
trigger Task 6 already prescribes.**

Fifth threat-model round on this document, spawned cold-start. I read it from line 1, then re-read the
material the FOURTH fold added — Design §2's "The door FAILS CLOSED when the write guard is not
enforcing" bullet and the "CLASS behind M6" paragraph beside it, the `mode = vault_io.guard_mode()`
refusal in the door body, the widened `update_fields` pre-write predicate and its new precondition table,
Design §5's integration rows, Design §6's restated Configuration section, Prerequisites 9, the new
`observe` entry in `## Edge Cases` and the two existing entries redirected to M6, Task 6's M6 clause and
its `THE SAME CONDITION REFUSES EARLIER` half, Task 10's M6 both-ways arm, `## Verification`'s failure
mode and close-out step 2, `## Risk Analysis`'s new row and the amended Rollback paragraph, `## Scope
Boundary`'s not-repairing entry, the `base.py` and `tests/test_provenance_write_seam.py` `writes` fences,
`## Wall Membership`'s two amended rows and the M6 fold record — and checked each against the CODE rather
than against the fold's prose. I re-read round 4 in full as my carry-forward.

### Trigger check

The same six fire, unchanged in shape: filesystem operations on user-owned files, persistence, untrusted
vault bytes crossing into a trusted write-target decision, PII (person names in a WARNING, an ERROR and a
committed live-vault artifact), an out-of-repo blast radius through three `-e` consumers, and — round 4's
addition — configuration that changes a trust boundary. The fold added no seventh: no network, no
subprocess, no credential, no new import capability, and the one environment read it introduces is a read
of an existing function on an already-imported module. The trigger this round's finding sits on is the
first one, reached through the second: a caller-supplied value composing a write target.

### The six standing mitigations, re-verified against the code

**M1 — still landed and still total, and the fold did not displace it.** The door body's sequence is now
source-resolve → `source.exists()` → `destination = self.vault_path / new_filename` → M1's containment
block → M6's `mode = vault_io.guard_mode()` → `old_stem` → `same_place` → the three branches. M6's
insertion lands AFTER the containment block and BEFORE the first `vault_io.move_note` call, so M1 still
precedes every move on all three branches and nothing was re-ordered around it. I re-confirmed the two
facts underneath it in this worktree rather than carrying round 4's account: `vault_io._resolved` is still
a bare non-strict `Path(path).resolve()` with no notion of a vault root
(`obsidian_schemas/vault_io.py:_resolved:234-243`) and `move_note` still refuses only a symlinked SOURCE
(`obsidian_schemas/vault_io.py:move_note:736-740`) and checks nothing about where `dest` points, so M1's
clause is still the only thing bounding the destination. Task 6, ordinal unmoved. **M1 is also what
catches the escaping spelling in this round's finding — it holds there too, which is why that finding is
about ORDERING and not about containment.**

**M2 — still landed, unchanged.** Task 2's arm still asserts the PROPERTY (the accessor
`_resolve_write_target` reads answers A's own path; nothing the seam reads answers B), with pydantic's
extras retention demoted to a Build-Log observation. The fold touched neither the stamp nor the parse.
Task 2, ordinal unmoved.

**M3 — still landed, unchanged.** `source.with_name(destination.stem + ".rename-tmp.md")` is
byte-for-byte in the door body, in Task 6's work text, in the `## Edge Cases` entry for a process dying
mid-two-step and in the `## Risk Analysis` row; Task 10's oracle is still
`vault_path.glob(repo.file_pattern)` with the rejected spelling driven through the same glob as a
near-miss. M6 sits above the branch, so the staging window is unchanged in width. Task 6, ordinal
unmoved.

**M4 — still landed, unchanged.** `logger.info("Renamed %s note from %s to %s", self.type_name,
source.name, moved.name)` in the door body and in Task 6, captured in Task 10 through
`captured_logs(level=logging.INFO)` — and `tests/support.py:captured_logs:91` really does default to
`WARNING`, which is why the level argument is prescribed. Task 6, ordinal unmoved.

**M5 — still landed, unchanged, and untouched by this fold.** Task 13 still carries the token-class rule
whole-file in both halves, with no fence toggle and no non-vacuity guard in the privacy path, and the
reader battery is still pinned MUST-FIRE for a bare filename INSIDE a fenced code block. Round 4 re-ran
§4a's own tokenizer over the committed artifact and I found no edit to either the artifact or Design §4a
in this round's diff, so the empirical half stands as measured. Task 13, ordinal unmoved.

**M6 — landed, and I re-derived every citation it rests on rather than reading the fold's prose back.**
`obsidian_schemas/vault_io.py:_move_locked:757-771` is verbatim the `try: os.link(...)` /
`except FileExistsError` / `if guard_mode() == "observe": ... os.replace(source, target) ... return
target` / `raise NoteAlreadyExists` shape the clause describes, at exactly those lines.
`guard_mode:169-181` is an `_env_setting` over `OBSIDIAN_SCHEMAS_WRITE_GUARD` defaulting to `"enforce"`
with `validate=lambda v: v in ("enforce", "observe")` at `:176-181`, so the mode the refusal message
names is one of two literals by construction and carries no PII — the fold's claim is exact.
`_env_setting:104-115`'s docstring really does reserve environment access to itself in the words the
Design bullet quotes. `obsidian_schemas/repositories/base.py:9` imports `os` and `:22` imports
`vault_io`, so both halves of the spelling warning are true: the wrong spelling would build, and the
right one costs no import. `create_note:709-718` really does carry the identical fail-open at `:712-718`,
so M6's scope bound names a real sibling rather than a hypothetical one. `tests/support.py:patcher:72-78`
is a `@contextmanager` whose `finally` calls `undo()`, and `Patcher.setitem:59-65` records `_UNSET` for a
key it found absent and POPS it on restore — which is exactly the restore Task 10's arm needs, and
`tests/test_concurrent_access.py:706` and `:737` really do drive this variable through that helper. The
fold is correct at every step. Task 6, ordinal unmoved.

### STRIDE delta — what the fourth fold moved

**Spoofing, Repudiation, Denial of service: unmoved.** M2 still closes the stamp's read direction. M4's
line is unchanged and the new refusals are loud rather than silent, so reconstructability improves. The
fold added one per-call environment read and no retry, recursion, backoff or unbounded loop; the mode is
never cached, so there is no poisoned-state shape to attack.

**Elevation of privilege: strictly better, and this is the axis the fold was for.** The door's capability
— relocating a file — is now behind a precondition that fails CLOSED, and the failure direction of the
one setting involved is refusal in both directions: an invalid value raises `WriteFailedError` out of
`_env_setting` rather than being read as a third mode, and the legal non-default value refuses rather
than widens. Design §6's asymmetry argument ("a setting whose only effect is to turn a capability OFF has
one safe direction") is the right frame and the code supports it.

**Tampering: better at the door, and worse by one ordering at the caller — the finding below.** The door
itself cannot now reach `_move_locked`'s `os.replace` arm at all, which is the whole of M6 and is the
larger movement. Against that, the fold's widened `update_fields` predicate declares a precondition CLASS
total and it is not, so one member of that class still reaches the frame's content write first.

**Information disclosure: nothing new, and I checked the three places the fold could have opened
something.** The door's M6 message names the mode (two literals, no PII, checked above) and the
`type_name`; `update_fields`' widened refusal names the requested new name, which is the shipped class
round 4 already dispositioned (`base.py`'s `ValueError(f"{self.type_name} not found in repository:
{name}")` does the same in the same method); and `vault_io`'s own `observe` WARNING renders `path=` —
which is pre-existing, is in the module this item's `## Scope Boundary` declares unchanged, and which M6
makes the door stop reaching rather than start reaching.

### The finding — the fold's precondition table closes the M1 row for two types and declares it closed for all

The fourth fold did the WI-226 thing and widened `update_fields`' pre-write refusal from one remembered
conjunct into a declared PRECONDITION CLASS, with a table enumerating the door's refusal arms and a rule
for placing a seventh. That is the right move and it is why this is findable at all. But one row of that
table is answered wrong:

> *an uncontained destination (M1) | YES — the destination is `f"@{new_name}.md"` and `new_name` is in
> `updates` | **already refused earlier, by a different wall**: the only way that filename escapes is a
> `new_name` carrying a path separator, and `gate_write` refuses it on the delta before any write for
> both types that can reach this line … while `Book` and `Meeting` cannot reach it at all — they declare
> no `name` field.*

**`gate_write` judges a `name` delta for exactly two declared types, and the trigger that reaches it
consults the entity's declared fields nowhere.** Four facts, each read off the code in this worktree:

1. **The gate is type-scoped, by design.** `obsidian_schemas/name_gate.py:319` is `if declared_type is
   not None and declared_type != PERSON_TYPE:`, whose body validates only when `declared_type ==
   COMPANY_TYPE` (`:329-343`) and otherwise falls to `return dict(introduced)` at `:344` — the delta
   handed back UNVALIDATED. Its own comment says so: *"a Book write is gated and handed straight back"*
   (`:316-318`). `update_fields` calls it as `gate_write(updates, declared_type=self.type_name,
   whole_record=False)` (`base.py:483-485`), and `type_name` is `"book"` (`book.py:47-49`) and
   `"meeting"` (`meeting.py:48-50`). So the wall the table delegates to covers `person`
   (`_PATH_HOSTILE_RE` is `re.compile(r"/")`, branch `path_hostile`, `name_validation.py:249-259`) and
   `company` (`_COMPANY_PATH_HOSTILE_RE:351`), and no other declared type — present or future.
2. **The rename trigger is keyed on the caller's dict and the note's bytes, not on the model.** It is
   `"name" in updates and updates["name"] != frontmatter.get("name", "")` (`base.py:454`, kept verbatim
   by Task 6's *"Keep the name-change condition … as the trigger"*). `type(entity).model_fields` appears
   nowhere in it. A book note carries `title:` and no `name:`, so `frontmatter.get("name", "")` is `""`
   and ANY non-empty `updates["name"]` sets `renaming` True. The table's reason — *"they declare no
   `name` field"* — is a fact about `obsidian_schemas/models.py` (`Person:79` and `Company:128` declare
   `name`; `Book:139` and `Meeting:247` do not, which I confirmed) that the predicate never consults.
   Design §2's `f"@{new_name}.md"` paragraph and Task 6's restatement of it rest on the same
   non-sequitur, so the claim is made at three sites and checked at none.
3. **THIS ITEM is what makes it reachable, which is what makes it this item's cost.** Today
   `update_fields` opens with `name = getattr(entity, "name", "")` and `file_path =
   self.get_file_path(name)`, raising `ValueError` above the lock when that answers `None`
   (`base.py:437-441`); for a Book entity `name` is `""` and `get_file_path` is `_file_map.get("")`
   (`base.py:354-365`), so the frame does not run. Task 3's REFUSE-fallback shape binds `file_path =
   resolved` from the provenance stamp FIRST and only falls back to the name lookup, so after this item a
   stamped Book or Meeting entity runs the whole frame. This is the same shape as M6 — a residual that
   was unreachable until this item shipped the path that reaches it.
4. **The residual is a committed write followed by a raise, which is precisely what the arm exists to
   prevent.** With `{"name": "x/y"}` on a stamped book entity: `renaming` is True, `resolved` is not
   `None` and the guard is enforcing so the widened disjunction passes, `gate_write` hands the delta
   back untouched, `vault_io.write_note` COMMITS `name: x/y` into the book note (`base.py:490`), and only
   then does `rename_note(entity, "@x/y.md")` run — where `destination.resolve()` IS inside the vault
   (`@x` is read as a sub-directory), so M1 passes, and `move_note` reaches `os.link` against a missing
   parent and raises `WriteFailedError` (`obsidian_schemas/vault_io.py:_move_locked:772-773`). With the
   escaping spelling `{"name": "a/../../x"}` the destination `@a/../../x.md` resolves ABOVE the vault —
   `f"@{new_name}.md"` can traverse up only by consuming its own first segment, which is exactly this
   shape — and M1 raises its containment `ValueError`. **M1 holds in both: nothing is written outside the
   vault and nothing is hard-linked out.** What is left behind is a note that gained an ungated,
   caller-supplied `name:` key, unmoved, un-aliased, with an exception reaching the caller after a
   successful write — verbatim the state `## Edge Cases`' no-provenance entry calls *"strictly the worst
   of the three available answers"* and `## Risk Analysis` gives its own row.

Four things make this the finding rather than a theoretical one.

- **The document instructs the builder to leave it open, on this premise.** Task 6 says *"Design §2's
  precondition table is the authority for which of the door's refusal arms belong in this test and which
  stay the syscall's — read it rather than extending the disjunction by guess; in particular do NOT add a
  containment conjunct for M1 here."* That instruction is right for `person` and `company`, where a
  containment conjunct really would preempt the gate and degrade a `NameGateRefusal` carrying its
  `pattern` into a bare `ValueError`. It is wrong for every type the gate passes through, and a builder
  following the instruction ships the hole.
- **The input is external and the shape is named in this document already.** Prerequisites 7 records the
  one consumer-visible door as HAL9000's generic entity PATCH *"forwarding an arbitrary body that may
  carry `name`"* (`routers/entities.py:461`) — a request body, i.e. the untrusted side of the boundary
  Prerequisites 6 draws. The value lands in a write target through `f"@{new_name}.md"`, which is the one
  place in this item where an externally-supplied string composes a path.
- **The residual is SILENT where the item's own claims say every residual is loud.** `## Risk Analysis`'s
  non-atomicity row asserts *"each residual is exactly the `stem_name_divergence` the new detector
  reports"*, and Task 11's detector fires on `vf.entity_type == "person"`
  (`scripts/lint_vault.py:read_vault:176` is the source of that field, per Design §3's own argument at
  this document's line 2095). A book or meeting note carrying a spurious `name:` is reported by nothing.
- **The fix is one conjunct on a predicate Task 6 already prescribes, and it makes an existing claim
  structural rather than adding a behaviour.** Design §2 already asserts that `Book` and `Meeting` cannot
  reach the door; keying the trigger on the DECLARED field makes that true instead of hoped for. It is
  also the keying this document already chose one decision over: ordering decision 3 guards the in-memory
  alias assignment on `hasattr(entity, "aliases")` *"keyed on the DECLARED field and never on a type
  name"*, for the same reason — so the shape is the item's own idiom, not an import. **M7.**

*The mitigation's bound, so it is not over-read.* M7 changes WHICH CALLS fire the rename branch and
nothing else. It does not add a containment conjunct (M1 stays the door's and the `NameGateRefusal`
degradation the table warns about does not arise), it does not touch `gate_write` or the Tier-1 tables —
`## Scope Boundary` declares both read-never-edited and they stay so — it does not widen the gate to a
third type, which would be a second behaviour this item was not asked for and would put `name_gate.py` on
a `writes` fence it is deliberately off, and it does not move `save` or the five body-writers, none of
which has a rename branch. A Book or Meeting note that carries a stored `name:` as a pydantic extra is
covered by the same conjunct in the correct direction: its filename rule is `_get_file_name`, so
`@{name}.md` is the wrong destination for it and refusing is the right answer, not a lost capability.

### Notes (non-blocking)

- **`guard_mode()` is read twice per name change, and the window between them is a member of a class the
  fold already closed.** `update_fields` checks the mode inside its lock and `rename_note` checks it
  again after that lock releases; an in-process mutation of `os.environ` between the two would put the
  door's refusal after the committed write. It needs code inside the process to move the variable, which
  is strictly more privileged than the boundary Prerequisites 6 draws, and Design §2's re-run table
  already owns the outcome by name — row 1 lists *"a non-enforcing write guard (M6)"* as a residual in
  which nothing moved and whose recovery is *"unset `OBSIDIAN_SCHEMAS_WRITE_GUARD` or set it back to
  `enforce`, then re-run"*. Recorded so the next round does not re-find it; no work ordered.
- **AC-2(b)'s occupied-destination arm now depends on the ambient environment, and only the M6 arm is
  told to set it.** Task 10 is explicit that M6's `enforce` half must *"set the variable to `"enforce"`
  explicitly … because a value inherited from the runner is an environmental shape the test did not
  create (WI-149)"*, and Design §2 justifies leaving the signed AC-2(b) untouched on the grounds that
  *"its check runs under the floor command, which sets no environment"* — which is an assumption about
  the runner's shell, the same shape one arm over. The direction is safe: under an ambient `observe` the
  door raises M6's `ValueError` instead of `NoteAlreadyExists`, so the arm goes RED rather than green.
  Worth one line only so a conductor reading a red AC-2(b) checks the shell before the code.
- **Round 4's three carried-forward dispositions still stand and need no work.** The no-op branch's
  cosmetic audit line (harmless, not folded), the `update_fields` message's pre-existing person-name
  disclosure (shipped class, unchanged), and the `os.environ`-versus-`guard_mode()` spelling warning
  (folded into both the Design bullet and Task 6's clause — I confirmed both carry it). M1's
  check-then-act residual, the write-then-move window and the M3 `load()` window are all re-deferred
  unchanged for the reasons round 3 and round 4 gave.
- **The duplicated `## Adversarial Review` heading is still the conductor's and is still not mine.**
  Unchanged by this round. Recorded so the chain is unbroken.
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

```verdict
gate: threat-modeler
verdict: PROMOTE
date: 2026-09-26
model: claude-opus-5
note: Round 5 re-verified M1-M6 against the code each prescribes — all six HELD with ordinals unmoved and `desc` re-emitted byte-identically. M6 I re-derived rather than carried, and every citation the fold rests on is exact in this worktree: `_move_locked:757-771` is verbatim the `os.link` / `except FileExistsError` / `if guard_mode() == "observe": os.replace(...)` / `raise NoteAlreadyExists` shape; `guard_mode:169-181` validates to exactly two literals at `:176-181`, so the refusal message carries no PII by construction; `_env_setting:104-115` reserves environment access in the words the bullet quotes; `base.py:9` imports `os` and `:22` imports `vault_io`, so both halves of the spelling warning are true; `create_note:709-718` really carries the identical fail-open the scope bound names; and `support.py:patcher:72-78` plus `Patcher.setitem:59-65` really pop a key they found unset, which is the restore Task 10's arm needs. M1 needed a real re-check because M6 inserted a statement into the door body: it lands AFTER the containment block and before the first `move_note` call, so M1 still precedes every move on all three branches. The finding is INSIDE the fold, and the fold's own widening is what made it findable. The new Design §2 precondition table answers its M1 row "already refused earlier, by a different wall" — that wall is `gate_write`, and `obsidian_schemas/name_gate.py:319-344` returns a `name` delta UNVALIDATED for every declared type that is neither `person` nor `company`, while the trigger that reaches it is `"name" in updates and updates["name"] != frontmatter.get("name", "")` (`base.py:454`), which reads the caller's dict and the note's frontmatter and consults `type(entity).model_fields` nowhere. So the "`Book` and `Meeting` cannot reach it — they declare no `name` field" premise, made at three sites and checked at none, is a non-sequitur: a book note carries no `name:`, so `frontmatter.get("name","")` is `""` and any non-empty `updates["name"]` sets `renaming` True. THIS ITEM creates the reachability — today's `get_file_path(getattr(entity,"name",""))` opener answers `None` for a Book and raises above the lock (`base.py:437-441`, `:354-365`), while Task 3's `resolved`-first shape binds from the stamp and runs the frame — which is the same "the blast radius is created here" shape as M6. The residual is not a containment escape: M1 holds for `@a/../../x.md` and `move_note` raises on the missing parent for `@x/y.md`. It is that BOTH raise AFTER `base.py:490` has committed an ungated, caller-supplied `name:` into the note, which is verbatim the state the pre-write arm exists to prevent, on an externally-supplied value (Prerequisites 7's generic PATCH forwards an arbitrary body that may carry `name`), and it is SILENT where `## Risk Analysis` claims every residual is detector-visible, since Task 11's arm fires only on `entity_type == "person"`. Task 6 actively instructs the builder to leave it open ("do NOT add a containment conjunct for M1 here") on that false premise. M7 is one conjunct on a predicate Task 6 already prescribes, keyed on the DECLARED field and never a type name — the idiom ordering decision 3 already chose for `aliases` — so it adds no behaviour, touches neither `gate_write` nor the Tier-1 tables that `## Scope Boundary` freezes, and makes Design §2's own claim structural instead of hoped for. Zero OPEN questions.
```


## Spec Review — 2026-09-26

**Recommendation: REVISE — return to spec writer (one blocking gap, and it is the THIRD member of one class: propose the fold rather than a fourth disjunct)**

Fourth spec-review round on this document, spawned cold-start. Rulings on record: WI-021's
gate-name-output-is-an-identity ruling (approach G's rejection), Dave's `ac_hash 15189b874b27` sign-off
freezing AC-1…AC-5 and the Intent, the exploration's accept-the-linter-noise disposition, the threat
model's seven `kind: required` mitigations, and the Spec-Writer Notes' three declared NON-actions (M1's
check-then-act residual, the write-then-move window, the no-op branch's cosmetic audit line) — I route
against all of them and nothing below touches a signed criterion's text.

I read the document from line 1 in full rather than diffing against the previous round, then re-read the
code at every load-bearing citation. **All three of round 3's predecessors HELD.** Round 3's two blocking
findings are closed and I verified each against the code rather than the fold's prose: the re-run table
now states the half-failed-alias residual honestly and names the one-field recovery, with Task 10
asserting it directly; the branch key is `(destination.parent.resolve(), destination.name) ==
(source.parent.resolve(), source.name)` and Task 10 plants the spelling divergence instead of inheriting
it from `$TMPDIR`. Round 2's two and round 1's four are still closed. Every non-blocking note from all
three rounds is folded — including the six from round 3, each of which I re-checked at its landing site
(§3a's fifth member plus Task 12's plant (vii); §4a's `:6`; the WI-126 body constraint on the
Verification table's Book and Meeting rows; the `f"@{new_name}.md"` paragraph; M1's COMPANY precision;
AC-1(g)'s `repo._loaded` oracle in Task 9; and `## Wall Membership`'s `:112` re-anchor). The M7 fold is
faithful at every site the contract names, and I re-derived its four supporting facts rather than reading
the fold back.

The one blocking finding is the THIRD member of a class this document has now folded twice, and it is
inside the fold both times added: `update_fields`' rename branch commits its content write and then
discovers the door will not complete the move. That is why the recommendation below is a FOLD and not a
fourth disjunct.

### Citation verification

All verified against current code; nothing drifted. The ones a wrong reading would have made the design
unbuildable, and the ones the M7 fold rests on:

- **The M7 fold, re-derived rather than carried.** `obsidian_schemas/name_gate.py:gate_write:319` is
  `if declared_type is not None and declared_type != PERSON_TYPE:`, whose body validates only at
  `:329-343` (`declared_type == COMPANY_TYPE and "name" in introduced`, against
  `COMPANY_TIER1_BRANCHES`) and otherwise falls to `return dict(introduced)` at `:344`; the comment at
  `:316-318` really reads *"a Book write is gated and handed straight back"*. `base.py:454` is verbatim
  `if "name" in updates and updates["name"] != frontmatter.get("name", ""):` and names
  `model_fields` nowhere. `book.py:47-49` is `"book"` and `meeting.py:48-50` is `"meeting"`.
  `_COMPANY_PATH_HOSTILE_RE:351` is `[/\\:*?"<>|\[\]#^]` — wider than the person `_PATH_HOSTILE_RE:107`
  (`/`), so the M1 row's split is right on both halves. `writer.py:108`'s comment really does reserve
  `type(entity).model_fields` for the pydantic v2.11+ deprecation and `:112` uses it;
  `parser.py:199` uses `model_class.model_fields`. `Person:79`/`Company:128` declare `name`;
  `Book:139`+`:160` declares `title`/`status:163` and no `name`; `Meeting:247` declares
  `type`/`date`/`attendees`/`topics`/`meeting_id` at `:259-263` and inherits `tags` from
  `BaseEntity:40`. And the reachability claim holds in the direction M7 states it: today
  `update_fields` opens `name = getattr(entity, "name", "")` / `file_path = self.get_file_path(name)`
  and raises above the lock at `base.py:440-441`, and `BookRepository.get_file_path:326-338` keys on
  `title.lower().strip()`, so `get_file_path("")` answers `None` for a Book either way.
- `obsidian_schemas/repositories/base.py`: `_adopt:184-191` (the `_file_map` write at `:188`);
  `file_pattern:206-208`; `_ensure_loaded:210-213`; `load:241-248`; `_load_file:299-317` with
  `parse_markdown_file` at `:311`, `remember_snapshot` at `:313`, `return doc.entity` at `:314`;
  `_get_cache_key:319-321`; `get:331-342`; `get_file_path:354-365`; `save:367-412` (`overwrite=True`
  at `:372`, `:391-393`, `write_markdown_file` at `:398`, the INFO line at `:411`);
  `update_fields:414-523` (`:437-438`, `:440-441`, `:443-444`, lock `:448`, `read_note` `:449`,
  `parse_frontmatter` `:450`, the alias block `:454-459`, the gate `:483-485`, `write_frontmatter`
  `:488`, `write_note` `:490`, the reload `:493-495`, `_adopt` `:520`).
- `obsidian_schemas/writer.py`: `model_to_frontmatter:89` composing `model_fields` (`:112`) →
  `model_extra` (`:119-123`) → `extra_fields` (`:126-129`); `write_markdown_file:160` with the
  `entity is not None` arm at `:229-233`, the one `gate_write` at `:252-253`,
  `with vault_io.note_lock(file_path) as resolved` at `:258`, `is_create` at `:275`, the WI-126 guard
  at `:285-302`, the two writes at `:317`/`:319`; `update_frontmatter_field:333` (existence guard
  `:361-362`, lock `:368`, write `:393`), `update_frontmatter_fields:405` (`:434`, `:451`),
  `roundtrip_file:463` (`:494`'s empty-delta gate call, lock `:497`, write `:504`). All four leaves
  take the path as their FIRST parameter and write that same name, and **no leaf calls another leaf
  inside its own lock**, so `door_calls_inside_note_lock` really is EMPTY over `writer.py` today.
- `obsidian_schemas/vault_io.py`: `_env_setting:103-125` (its docstring reserves environment access in
  the words Design §2 quotes); `guard_mode:169-181` validating to exactly `("enforce", "observe")` at
  `:176-181`; `_resolved:234-243` a bare non-strict `Path(path).resolve()`; `remember_snapshot:266-270`,
  `snapshot_stamp:284-293` and `forget_snapshot:296-299` all keyed on `str(_resolved(path))`, which is
  why the 2u-arm claim survives a spelling divergence; `create_note:701-718` with the identical
  fail-open at `:712-718`; `move_note:721-750` with the symlinked-source refusal at `:736-740`, the
  link-then-unlink docstring at `:732-734` and the sorted two-lock acquisition at `:744-750`;
  `_move_locked:753-783` with `os.link` at `:758`, the `observe` `os.replace` at `:760-769`, the
  `NoteAlreadyExists` raise at `:770-771`, the `OSError` → `WriteFailedError` at `:772-773`, `os.unlink`
  at `:776` and `forget_snapshot` at `:780-781`. `move_note` returns `_resolved(dest)`.
- `obsidian_schemas/parser.py`: `parse_markdown_file:214-252` — `:244` is the `parse_to_model` line and
  `:246-252` the `ParsedDocument(...)`, so the two-line insertion lands where Design §2 shows it, and
  the parse gates NOTHING (`gate_write` has zero hits in this file), which is what makes premise 13's
  two refused specimens loadable; `parse_markdown_content:283` passes `file_path=None`.
  `models.py:BaseEntity:23-40` with `extra="allow"` at `:31-32`; `Optional` is imported at `:18` and
  `Path` is not, so Task 2's import list is right.
- `obsidian_schemas/repositories/person.py`: the five identical `self.get_file_path(person.name)`
  openers at `:1403`, `:1522`, `:1653`, `:1719`, `:1793` and the READ sibling at `:1590` — five sites
  and not six, exactly as premise 12 and `## Approach` (1) say; `append_to_timeline:1371-1470` with the
  combined `not file_path or not file_path.exists()` guard at `:1404-1405`, `note_lock` at `:1410` and
  both writes at `:1447`/`:1458` with `file_path` as first positional; `PersonRepository.save:1155`
  with the rider's `gate_write` at `:1190-1191` and `super().save(...)` at `:1197`.
  `CompanyRepository` declares only `type_name` — no `save`, no `get_file_path`, no `_get_cache_key`,
  no `file_pattern` — so it does inherit the seam whole. `BookRepository.save:144-184` and its
  `_get_file_name:340-355` are the two-line shape premise 15 reads, with the INFO line at `:183`.
- `scripts/lint_vault.py`: `read_vault:121` with `rglob("*.md")` at `:123`, `should_skip:116-118`,
  `stem = md.stem` at `:155`, `etype` read off the stored record at `:176`; `check_structural:328` with
  the `read_error`/`parse_error` `continue`s at `:340-359`, the two `is_at_prefixed` tests at
  `:362-381`, `if not vf.entity_type: continue` at `:383-384` and the `TYPE_TO_MODEL` guard at
  `:387-388` — so the new arm's placement buys AC-3(e) exactly as §3 claims and row 8's shape does
  reach it. I also re-checked that `_gate_refusal_pattern` cannot crash the tool on a corrupt note:
  `gate_write` mutates nothing (`result = dict(introduced)` at `:346`, `return dict(introduced)` at
  `:344`) and every address rule is guarded by `_shaped:196-198` (present AND a list of strings), so a
  malformed `emails:`/`phones:` passes through instead of raising, and the `name` arm is reached only
  behind the arm's own `isinstance(stored, str)`.
- `tests/derivations.py`: `PACKAGE_ROOT:31`, `DOOR_NAMES:47`, `_own_body_nodes:245`, `_called_names:264`,
  `_names_in:282`, `_is_write_call:286-299` (the `ast.Attribute` gate, which is why Design §4's second
  predicate is needed to reach `write_markdown_file`), `_taints_a_write:361-409` (seed `:368-382`,
  monotone fixpoint `:389-401`, sink `:404-408`), `functions_calling:873-887` (matching `f(...)` and
  `x.f(...)` alike, own body only), `_pos:924`, `_assign_targets_name:928-944`. **`move_note` is named
  exactly ONCE in `obsidian_schemas/**` today — its own `def` at `vault_io.py:721`** — so AC-2(c)'s set
  equality really does go from empty to `{BaseRepository.rename_note}` and nothing else joins it.
- I walked the AC-5 rebinding clause by hand over the ten prescribed seam bodies and the four leaves
  again, and it still admits every shipped shape and refuses the monotone escape. Two spots are worth
  recording because they are the ones a builder could get wrong: in `rename_note` the only Assign that
  binds a TAINTED name out of a value mentioning no tainted name would be `file_path`-shaped and there
  is none (`destination`, `contained`, `mode` bind names the seed never taints; `old_stem`,
  `same_place`, `staging`, `moved`, `new_stem` all mention `source` or a name derived from it; and
  `entity._source_path = moved` binds no local under `_assign_targets_name`'s target rule, so `entity`
  stays untainted and `aliases = list(getattr(entity, "aliases", []) or [])` is outside the clause).
  In `update_fields` the fixpoint taints `content`, `stamp`, `frontmatter`, `body`, `yaml_content`,
  `new_content` off `file_path`, so the only clause-eligible Assign is
  `file_path = self.get_file_path(name)` — inside `if file_path is None:`, which is AC-5's fifth
  ACCEPTED near-miss.
- `tests/fixture_vault.py`: `CORPUS_DIGEST:44`, `NOTES:217`, the four divergent specimens at
  `:255-260`, `:261-266`, `:297-301`, `:302-306`, the collision third at `:273-276` (stem and name
  AGREE), the whitespace discriminator at `:246-254` — and I checked the BYTES, not just the manifest:
  `tests/fixtures/vault/@Dave  Marrowyn Fennwick.md:3` is `name: "Dave  Marrowyn Fennwick"`, QUOTED, so
  the double space survives YAML and AC-3(b)'s raw-comparison discriminator really is clean raw and
  divergent cleaned. The phone specimen at `:288-293` declares no `phones` and its stem equals its
  stored name, so it is in neither population — the two plants AC-1 and AC-3(c) name are still the only
  members that discriminate the door predicate from the bare validator.
- `obsidian_schemas/name_validation.py`: `Tier1Branch:148-179` with `pattern`'s non-uniqueness at
  `:152-154` and `sentinel_exempt` documented at `:155-156`; `validate_strict:594-609` with
  `allow_phone_sentinel: bool = False` at `:594`, the *"Off by default to keep producers honest"*
  docstring at `:599-601` and the sentinel early-return at `:607-609`; `arrow_connective:214-225`
  raising `pattern="calendar_prefix"`, `path_hostile:249-259` raising `pattern="path_hostile_char"`.
- `tests/support.py`: `temp_dir:31-37` returns an UNRESOLVED `mkdtemp` path; `Patcher.setitem:59-65`
  records `_UNSET` for an absent key and POPS it on restore; `patcher:72-78` is a `@contextmanager`
  whose `finally` calls `undo()`; `captured_logs:91` defaults `level=logging.WARNING`, so Task 10's
  explicit INFO for M4 is required.
- The pinned walls and their anchors: `tests/test_loud_fail_write.py:test_write_failure_raises_and_noops_keep_their_return:105`
  with `_check_write_failure_raises_and_noops_keep_their_return:112` (round 3's re-anchor is landed);
  `tests/test_name_gate_wall.py:PERSON_FALSY_RETURN_FUNCTIONS:1048`,
  `test_wall_membership_is_closed_by_running_each_walls_predicate:1057`, `_check_wall_d:1107`,
  `_check_the_ast_capability_stays_single_homed:1132`, the `len(sites) == 8` pin at `:1156`.
- `docs/vault-shape-census.md`: `pure_digit` MEASURED at 2 (`:148-157`), `stem_name_divergence`
  MEASURED at 8 (`:203-212`, the predicate at `:209`), `same_name_collision` ABSENT with *"the largest
  live collision is two"* (`:214-223`), the ONE-or-TWO ruling at `:266-271`.
- `docs/stem-divergence-live-baseline.md`: the whole-file-scan-is-legal declaration at `:15`, the
  `'*.md'` glob at `:36`, §1's two entry figures at `:121-122`, *"divergent rows the WRITE DOOR refuses
  (b3): 0 of 8"* at `:124`, the occupancy row at `:126`, the eight rows at `:146-153` with row 3
  `same-file` → RENAME and row 8 `different-note` → MERGE, the two declared vocabularies at
  `:155-156`, and the mis-statement Design §3 corrects at `:158-161`. I re-ran §4a's own tokenizer
  (`[\w@{}*./+-]+\.md`) over the committed bytes myself: exactly EIGHT tokens —
  `docs/filename-name-divergence-repair.md` (`:4`), `docs/vault-shape-census.md` (`:5`, `:22`),
  `docs/lint-vault-live-baseline.md` (`:6`), `*.md` (`:36`) and `@{name}.md` (`:76`, `:126`, `:153`) —
  all three repo paths present. M5's token-class rule is GREEN and total against the artifact as
  committed, and §4a's line citations are now right.
- `docs/wi-029-consumer-audit.md`: the generic PATCH row at `:84` (*"`body` is an arbitrary HTTP PATCH
  dict and may carry `name`"* — and it names book/meeting via the generic route, which is what M7
  closes), the Book/Meeting zero-call-sites reading at `:134-140`, the 19-of-19 summary at `:371-376`,
  the `auto_load=False` zero at `:389`. **The audit says nothing anywhere about an occupied rename
  destination** — which is the blocking finding below.

### Blocking issues

**1. `update_fields` with a name change onto a destination that is ALREADY occupied by a different note
commits the new name and then raises — no race, no configuration, no exotic type — and three surfaces of
this document say it cannot happen. This is the THIRD member of one class, so the fix is the FOLD, not a
fourth disjunct.**

The class, stated first, because it is the point: *`update_fields`' rename branch commits its content
write inside the lock and only then discovers the door will not complete the move.* Round 2's blocking
finding 1 was that member for **no provenance**. Threat-model round 5's M7 was that member for **a type
that declares no `name`**. Both were closed by adding a disjunct to the same pre-write refusal, and the
M6 fold then declared the refusal's predicate to be *the door's whole PRECONDITION class* with a table
enumerating the door's refusal arms. The table is where this round's member lives, and it lives there
**by the table's own disposition**:

> | `move_note`'s refusals (`NoteAlreadyExists`, symlinked source) | NO — both are filesystem state at
> move time | nobody, deliberately: pre-checking either here is exactly the check-then-act this document
> refuses elsewhere, and the syscall is the stronger answer |

I agree with the disposition. A pre-check of the destination is check-then-act and the syscall IS the
stronger answer. What is missing is not a conjunct — it is **the residual that disposition leaves,
stated anywhere at all.** Trace it, with no concurrency and every precondition satisfied:

`repo.update_fields(person_A, {"name": "Robert Smith"})` where the entity is stamped, the guard is
enforcing, `Person` declares `name`, and `@Robert Smith.md` already exists as a DIFFERENT note.
`renaming` is True; all three disjuncts pass; `gate_write` accepts the delta (`base.py:483-485` — no
path separator, so no Tier-1 branch fires); `vault_io.write_note(file_path, new_content,
precondition=stamp)` **COMMITS `name: Robert Smith` into note A** (`base.py:490`); the lock releases;
`rename_note(entity, "@Robert Smith.md")` clears the no-provenance arm, `source.exists()`, M1's
containment and M6's guard check, reaches `vault_io.move_note`, and `os.link` raises `FileExistsError`
→ `NoteAlreadyExists` (`vault_io.py:_move_locked:758-771`). The re-stamp and the alias append are both
AFTER the move, so neither runs; `update_fields` never reaches its reload and returns nothing.

**The residual: note A carries a stored name it does not own, sits at its old stem, has NO alias for
that stem, and the caller holds an exception raised after a successful write.** That is verbatim the
state `## Edge Cases`' no-provenance entry calls *"strictly the worst of the three available answers"*
and the state M7's own `desc` exists to prevent, reached here on ordinary caller data. And it is worse
than today in exactly the way the no-provenance entry used to reject "skipping the move": today the same
call SUCCEEDS — `base.py:454-459` appends the old stem to `aliases` in-lock, the write commits, the
reload returns the entity — so this population *"would come out of this item strictly worse off than it
went in"*, losing the alias and gaining an exception.

Three surfaces state the opposite, and a fourth is the one that would have caught it:

- **`## Edge Cases`, *"The rename destination is occupied by a DIFFERENT note (the live MERGE row)"*** —
  **Decision:** *"`move_note` refuses by syscall with `NoteAlreadyExists` and **both files are
  byte-identical afterwards**."* True of a direct door call; false on the `update_fields` path, where
  the source note is not byte-identical. The entry is the ONLY occupied-destination entry in the
  section and it is not scoped to the door.
- **`## Risk Analysis`, the *"`update_fields` now MOVES a file on every name change, permanently"*
  row** — its whole mitigation is *"The old stem is kept as an alias, so the library's own resolvers and
  Obsidian both still find the note."* False for this sub-population: no alias is appended, and the
  in-lock append this item deletes is what used to guarantee it.
- **Prerequisites 7 and the conductor read-back note 4 Dave signed** — *"today that produces a fork;
  after this item it produces a move with an alias."* Incomplete for the same sub-population: the one
  consumer-visible door (HAL9000's generic PATCH, `routers/entities.py:461`, whose post-call path is
  re-derived from `updated.name` at `:464`) goes from a 200 with the entity to an exception. That is an
  undisclosed consumer-visible behaviour change on the exact site the audit singles out, and the audit
  itself never mentions an occupied destination.
- **`## Verification`'s failure-mode list** names *"a rename onto an occupied destination
  (`NoteAlreadyExists`, both files byte-identical)"* — door-scoped — and no `update_fields` variant, so
  no arm of Task 10 reaches it: AC-2(b)'s arm drives the door directly, the M6 arm's `update_fields`
  half runs under `observe` (refused pre-write), and the M7 arm's subject is a Book.

Nothing here needs new machinery, and it is *not* a re-opening of the write-then-move window (that entry
is about interleavings and is a declared NON-action; this member has no race in it). **The fold — the
rule total over the surface, on the same shape the third round's fold already produced for the door.**
The precondition table's rule currently says only which refusals move EARLY:

> *`update_fields` refuses a name change before its content write for every reason the door refuses its
> own PRECONDITIONS … and for no reason that depends on filesystem state at move time, which stays the
> syscall's.*

A rule that partitions a surface and states the residual of only one half is how this class keeps
producing members. Extend it in one place, DERIVED from the table's own rows rather than from a
remembered list: for every row the table answers **NO**, state what the method leaves and what the
caller must do — the way Design §2's re-run table does for the door's four sequence points. Three of the
four NO rows already have homes (`FileNotFoundError` on a deleted source → the write-then-move entry;
the alias write → the re-run table's third row; `move_note`'s symlinked-source refusal → the same shape
as the occupied one); the occupied destination's non-racy member has none, and it is the one with a live
consumer path. Then correct the three surfaces above — the `## Edge Cases` Decision scoped to the door
with the `update_fields` path stated beside it, the `## Risk Analysis` mitigation no longer claiming the
alias unconditionally, and Prerequisites 7 disclosing the exception — and give Task 10 the arm that makes
it falsifiable: with a stamped Person subject and the guard at `enforce`,
`repo.update_fields(entity, {"name": <a name whose @{name}.md the test planted as a DIFFERENT note>})`
raises `NoteAlreadyExists`, the vault's filename SET is unchanged, the DESTINATION note is byte-identical,
and the SOURCE note's state is asserted as whatever the fold decides it is. AC-2 is signed and gains
nothing; this is a non-AC arm of its check, exactly as the idempotence, M6 and M7 arms are.

One decision the fold has to make explicitly rather than inherit, because it is the only place a builder
could go either way and the three available answers differ observably: **whether the method accepts this
residual (loud, detector-visible, one hand repair) or removes it by ordering** — move first and write
second, which is available because the content write's `precondition=stamp` comes from this frame's own
`read_note` and `move_note` is link-then-unlink over the same inode, or by refusing the whole name change
when the destination exists, which the table correctly refuses as check-then-act. I am not choosing for
the spec; I am saying the choice is currently made by silence, and the surfaces that describe it are
false either way.

(Builder's question this answers: *"`update_fields` committed the new name and `rename_note` raised
`NoteAlreadyExists` because the destination was already taken — `## Edge Cases` says both files are
byte-identical afterwards and `## Risk Analysis` says the old stem is kept as an alias. Neither is true
of the note I just wrote. Which state am I supposed to leave, and what am I supposed to assert?"*)

### Non-blocking notes

- **Design §2's sequencing block mirrors `aliases` onto the caller's entity on EVERY path, not only the
  rename path.** The block's line is `if "aliases" in updates: entity.aliases = frontmatter["aliases"]`,
  ungated by `renaming`, while the prose that orders it (*"Which `aliases` list wins"*) says it is
  *"captured inside the lock with the rest of the rename decision"* and its only consumer is the door.
  So `repo.update_fields(person, {"aliases": [...]})` with no name change gains a new in-place mutation
  of the caller's object that today's `update_fields` never performs — benign (the value mirrors what
  the write committed, and `PersonRepository.save`'s WI-021 rider already mutates three fields in place)
  but a caller-visible widening neither Prerequisites 7 nor `## Risk Analysis` names. One clause: gate it
  on `renaming`, or say the mutation is intended on every path.
- **This item makes `update_fields` usable on `Book` and `Meeting` entities for the first time, and that
  widening is asserted by a battery without being declared anywhere.** Today the method raises above the
  lock for both types (`name = getattr(entity, "name", "")` is `""` and `get_file_path("")` answers
  `None` — `base.py:437-441`, and `BookRepository.get_file_path:326-338` keys on `title`), so the frame
  never runs; Task 3's `resolved`-first shape binds the file from the stamp and the whole frame runs.
  M7 refuses the `name` delta, which is right — but Task 10's own ACCEPTED arm asserts that
  `repo.update_fields(<a stamped book>, {"status": "read"})` now SUCCEEDS, i.e. a capability the package
  did not have. The audit's `:134-140` reading says the generic PATCH is the only consumer route to those
  two repositories, so the blast radius is measured at zero; the point is that the widening should read
  as a decision (one line in Design §5 or `## Scope Boundary`) rather than as a side effect of a
  fallback reorder.
- **Design §1's quoted `BaseEntity` body is a paraphrase presented as a quote.** The snippet under
  *"`obsidian_schemas/models.py:BaseEntity:31` today is"* drops the two inline comments the source
  carries inside `ConfigDict` (`models.py:33`, `:35`). Nothing downstream depends on it and the fields
  quoted are exact; worth one edit only because every other code quotation in this document is verbatim
  and a reader who diffs this one will wonder what else was smoothed.

### Carried-forward notes

- **The duplicated `## Adversarial Review — 2026-09-25` heading — still the conductor's, and it has
  grown.** THREE sections now carry that identical heading (rounds 1 PROMOTE, 2 REVISE, 3 PROMOTE), so a
  heading-keyed structural reader has three candidate sections for one gate and a latest-round reading
  resolves the third. Round 3's injection-hunter resolved round 2's provenance concern on the merits, so
  the standing verdict is PROMOTE; the HEADING collision is a document-structure fact the spec-writer
  correctly declines to touch. It reaches nothing in this round — I am emitting REVISE, so D5 is not
  approached. Recorded so the conductor's action does not go missing behind another gate round.
- **M1's exact bound (threat model round 2).** Resolve-then-`os.link` is check-then-act against an
  attacker who can plant a symlink at the destination between the two. FOLDED as a stated bound in
  Design §2's M1 bullet with no work ordered, and re-declared as a NON-action in the Spec-Writer Notes.
  Re-deferred unchanged: the bound is stated, the attacker is outside Prerequisites 6, and
  `os.link` has no `O_NOFOLLOW` spelling reachable through pathlib.
- **The write-then-move window (threat model round 2).** FOLDED as a `## Edge Cases` entry and a
  `## Risk Analysis` row, with the lock-ordering entry explicitly marked as a claim about ORDERING only.
  Re-deferred as a declared NON-action. Stated here explicitly so the fold above is not read as
  re-opening it: that entry is about INTERLEAVINGS, and blocking finding 1 has no race in it.
- **The `guard_mode()` double read (threat model round 5, note 1).** `update_fields` checks the mode
  in-lock and `rename_note` checks it again after the lock releases; an in-process `os.environ` mutation
  between the two would put the door's refusal after the committed write. Re-deferred unchanged: it
  needs code inside the process to move the variable, which is more privileged than the boundary
  Prerequisites 6 draws, and the re-run table's first row already owns the outcome by name. Worth noting
  that it is the same class as blocking finding 1 one step further out — the difference is that this one
  needs a privileged actor and finding 1 needs only an occupied filename.
- **AC-2(b)'s occupied-destination arm depends on the ambient environment (threat model round 5,
  note 2).** Only the M6 and M7 arms are told to set `OBSIDIAN_SCHEMAS_WRITE_GUARD` explicitly, while
  AC-2(b)'s own arm inherits whatever the runner carries; Design §2 justifies leaving the signed
  criterion untouched on the grounds that *"its check runs under the floor command, which sets no
  environment"*, which is an assumption about a shell. Re-deferred for the writer's stated reason: the
  failure direction is safe (under an ambient `observe` the arm goes RED, not green) and AC-2 is signed.
  The one line that would help a conductor reading a red AC-2(b) — check the shell before the code — is
  still not in the document.
- **The no-op branch's cosmetic audit line (threat model round 4).** On the `same_place` branch M4's INFO
  line reads *"Renamed … from @New.md to @New.md"*. Recorded by the modeler as harmless and not a
  security defect; carried unchanged.
- **Architect round 6, note 6(iv)** — the deliberately-out-of-scope items (`_get_cache_key`'s strip
  asymmetry, approach F's re-keying, the Book/Meeting `save` collapse) stand as written and are all
  named in `## Scope Boundary`. Closed; recorded so the chain is unbroken.
- All other prior non-blocking notes are FOLDED and I verified each against the code rather than the
  prose: round 3's six (listed in the preamble above), round 2's five, round 1's twelve, the M3
  `load()` window (now `## Verification`'s close-out paragraph), and the threat model's
  pre-existing-extras-leak bound (Design §1, beside AC-1(h)).

```verdict
gate: spec-reviewer
verdict: REVISE
date: 2026-09-26
model: claude-opus-5
targets: Task 6, Task 10, #design, #risk-analysis
prior: held
basis: folded-material
findings: 1/4
note: One blocking finding, and it is the THIRD member of one class — `update_fields`' rename branch commits its content write and then discovers the door will not complete the move — so the recommendation is the FOLD and not a fourth disjunct. Round 2's finding 1 was that member for no provenance; threat-model M7 was it for a type declaring no `name`; this round's is it for a destination ALREADY OCCUPIED by a different note, with no race, no configuration and no exotic type: `update_fields(person, {"name": X})` where `@X.md` exists as another note passes all three refusal disjuncts, passes `gate_write` (no separator, so no Tier-1 branch fires), COMMITS the new name at `base.py:490`, then `rename_note` reaches `move_note` and `os.link` raises `FileExistsError` → `NoteAlreadyExists` (`vault_io.py:_move_locked:758-771`) with the re-stamp and the alias append both after the move, so neither runs. The residual — a note carrying a name it does not own, at its old stem, with NO alias, and an exception after a successful write — is verbatim what `## Edge Cases`' no-provenance entry calls "strictly the worst of the three available answers", and it is STRICTLY WORSE than today, where the same call succeeds and `base.py:454-459` appends the old stem in-lock. Three surfaces say it cannot happen: the `## Edge Cases` occupied-destination entry ("both files are byte-identical afterwards" — false on this path, and it is the section's only occupied-destination entry), the `## Risk Analysis` update_fields-moves-a-file row (whose entire mitigation is "the old stem is kept as an alias"), and Prerequisites 7 plus Dave's signed read-back note 4 ("after this item it produces a move with an alias") — an undisclosed consumer-visible change on the one site the audit singles out, HAL9000's generic PATCH at `routers/entities.py:461`, which the audit never discusses for an occupied destination. No battery reaches it (AC-2(b)'s arm drives the door directly, M6's `update_fields` half runs under `observe`, M7's subject is a Book). The precondition table's disposition of the row ("nobody, deliberately: pre-checking is check-then-act and the syscall is the stronger answer") is RIGHT; what is missing is the residual that disposition leaves. So the fold is the rule total over the surface, on the same shape the third round's fold already produced for the door: for every row that table answers NO, state what the method leaves and what the caller must do, DERIVED from the table's own rows — three of the four NO rows already have homes and only this one does not. Rounds 1-3's eight blocking findings all held closed and every non-blocking and carried-forward note is folded; I re-derived M7's four supporting facts and re-ran §4a's tokenizer over the committed baseline myself (exactly the eight tokens it enumerates, all three repo paths present).
```


## Adversarial Review — 2026-09-26

Cold-start spawn, fourth injection-hunter round on this document (three `## Adversarial Review —
2026-09-25` sections already stand: round 1 PROMOTE, round 2 REVISE on a provenance concern about
round 1's own standing, round 3 PROMOTE resolving round 2 on the merits). I read the document from
line 1 to its end in full — Problem/Motivation, Intent, the entire Exploration Notes arm (all five
architect rounds, the AC red-team round, all fifteen numbered premises, every constraint, the
conductor read-back), Approach, Design §1 and §2 in full (the stamp, the ten-caller resolution
function, the door body and its M1/M3/M4/M6/M7 clauses, the branch-key and half-failed-rename
material), Write Targets (both `kind: precondition` fences and every builder `writes` fence), Wall
Membership, Mitigation Folds, Verification, Scope Boundary, Risk Analysis, all five signed `criteria`
fences and Examples of Done, Spec-Writer Notes, then every prior gate's verdict prose in document
order — Architectural Review, AC Red-Team, AC Sign-off, Data Audit, Threat Model rounds 4 and 5,
Spec Review round 4 (the round immediately above, just landed), and all three existing Adversarial
Review sections read directly rather than taken on each other's word. I additionally grepped the
whole document, several passes, for verdict-steering phrasing ("ignore previous instruction",
"pre-approved", "you must/should emit", imperative address to a reviewer, "trust this", role-play
framing, "SYSTEM:"/"assistant:"/chat-template tokens, hidden-formatting tricks including base64 and
zero-width characters) and separately for every HTML comment and every `writes` fence. All greps
returned only legitimate hits: the steering-phrase grep matched nothing outside prior gates' own
verdict prose *discussing* the absence of such phrasing (including this section's own citations of
theirs); the only HTML comment in the document is the machine-maintained archive-split pointer at
line 21; and every `writes` fence names a path inside this item's own declared write authority
(`obsidian_schemas/**`, `tests/**`, `scripts/**`, `docs/**`) — none names another work item's own
tracked document, so the WI-245 merge-authorization scrutiny does not arise here.

**Round 2's provenance concern, re-confirmed closed rather than re-litigated.** Round 2 flagged that a
standing PROMOTE under this gate's own heading had unconfirmed provenance; round 3 resolved it on the
merits, reading both prior sections directly and finding each of round 2's three supporting facts had
a specific, non-malicious explanation (every gate on this document is a cold-start spawn that
self-discovers its own round number; the fence Threat Model round 2 repaired sat at the boundary of
*its own* section, not the injection-hunter's; the absent accompanying spec-reviewer PROMOTE was never
load-bearing because no transition has ever been at risk of firing on it). I read round 3's reasoning
against round 1 and round 2's own text rather than against round 3's summary of them, and it holds:
nothing in this round's read surfaces a fact round 3 missed, and the class of "no gate round in this
append-only document carries cryptographic provenance" is still true of every gate here, this one
included, so it remains a bar nothing in the document can clear rather than a live signal.

**This round's own material — the fourth threat-model round, the fifth threat-model round and the
fourth spec-review round — is the same genre as every round before it.** Each is dense, code-cited,
self-correcting prose that argues a technical claim about the CODE (a fail-open under
`OBSIDIAN_SCHEMAS_WRITE_GUARD=observe`, a `gate_write` type-scoping non-sequitur, a committed-write-
then-raise residual on an occupied rename destination) with a citation at every load-bearing step, and
none of it is addressed to a reviewing agent or shaped to produce a particular verdict rather than a
particular understanding of the system. The spec-reviewer's REVISE immediately above this section is,
like every prior spec-review and threat-model round, an independently re-derived, line-cited finding —
I re-checked its central trace (`update_fields(person, {"name": "Robert Smith"})` against an occupied
`@Robert Smith.md`, through `gate_write`, `base.py:490`'s commit, and `_move_locked`'s
`FileExistsError` → `NoteAlreadyExists`) against the code myself rather than accepting the fence's
prose, and it reproduces exactly as stated. Nothing in this document's extensive self-arguing style —
which repeatedly defends its own design choices, narrates its own history of self-correction, and
states in its own voice why an earlier draft was wrong — reads as an instruction aimed at a gate rather
than the spec and its reviewers making their own case about the system being built.

I found no text whose *effect* is to steer any gate's verdict, planted or otherwise, anywhere in the
document.

```verdict
gate: injection-hunter
verdict: PROMOTE
date: 2026-09-26
model: claude-sonnet-5
note: Full end-to-end read (Problem/Motivation through the just-landed fourth Spec Review round, including all three existing Adversarial Review sections read directly) plus several whole-document greps for steering phrasing, HTML comments and non-conforming `writes` fences found no planted text steering any gate's verdict and no cross-item merge-authorization concern (every `writes` fence stays inside this item's own declared write authority). Round 2's provenance concern about round 1's standing is not reopened: round 3's resolution holds on a direct re-read of all three prior sections, not merely on trusting round 3's summary. This round's Threat Model (rounds 4-5) and Spec Review (round 4) material is the same genre as every prior round — dense, line-cited technical argument about the code (the M6 write-guard fail-open, the M7 `gate_write` type-scoping gap, the occupied-destination commit-then-raise residual) — and I independently re-verified the spec-reviewer's central trace against the code rather than its prose; none of it is addressed to a reviewing agent or shaped to produce a verdict rather than an understanding.
```

