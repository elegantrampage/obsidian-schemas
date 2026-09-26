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

