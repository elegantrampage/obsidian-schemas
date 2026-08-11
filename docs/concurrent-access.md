---
id: WI-004
title: "Concurrent & external write safety (atomic writes, locking, stale-read protection)"
project: obsidian-schemas
stage: done
created: 2026-03-22
last_touched: 2026-08-11
stage_changed: 2026-08-11
touched_by: spec-writer
tags: [repository, write-safety, corruption-class]
round_budget: 10
depends_on: ["WI-020"]
transitions: ["idea>exploring@2026-07-08@fable-explore", "exploring>specced@2026-08-09@session", "specced>ready@2026-08-09@session", "ready>building@2026-08-09@session", "building>done@2026-08-11@session"]
---

# Concurrent & external write safety

> **Model routing** (2026-07-05 campaign, `docs/backlog-campaign-2026-07-05.md`; self-sufficient):
> - **Explore: FABLE (claude-fable-5) / high** — justified by the fork it resolves: per-file `flock` vs single-writer process vs optimistic mtime-precondition vs temp-file+rename-only, × how the chosen frame coexists with Obsidian's own editor writes (absorbed WI-015). Genuinely open (four plausible frames with different consumer-facing semantics), expensive to reframe once three consumer repos depend on the semantics, and its failure mode — silent data loss — is by nature hard to detect downstream. Fable is explorer only here; the spec-review is deliberately a different model.
> - **Spec: Opus / high.** **Spec-review: Opus / xhigh** — the campaign's single xhigh: this primitive becomes the door every vault mutation walks through; a correlated miss here corrupts the live vault for all consumers.
> - **Build: Opus / high** — core write machinery.
> - Sequencing: after WI-020 (loud-fail floor first, so the primitive's failure modes surface instead of degrading). WI-021's write-door consolidation routes through the primitive this item ships.

**Resliced 2026-07-05 (campaign review).** The March framing (in-process thread-safety for the FastAPI server) is a subset of the real problem the code-health review confirmed: **every write in the package is an unlocked, non-atomic read-modify-write** (`base.py:254-273` update_fields, `writer.py:217/246-295/322`, five body-section writers in `person.py:1495-1831`, `scripts/lint_vault.py:875`), with zero locking of any kind (grep-verified), while HAL9000, orchestrator, and CLI sessions write the same live vault concurrently — and Obsidian itself edits the same files (absorbs **WI-015 Obsidian Plugin Sync**, parked → merged here; same root cause, same mechanism).

## Problem / Motivation

The repository layer currently assumes single-threaded use — no locking, no thread-safe cache operations. HAL9000 runs as a FastAPI server handling concurrent requests, which means multiple request handlers can read and write the same repository cache simultaneously. This creates race conditions: a refresh triggered by one request can corrupt the cache mid-read by another. Thread-safe cache operations with read-write locks are needed to make repositories safe for multi-threaded servers without serializing all access behind a single lock.

**Expanded scope (2026-07-05):**

1. **Lost-update class:** process A reads a note, process B appends a Timeline entry and writes, process A writes back a frontmatter-only change built from the stale body → B's edit silently gone. Same class with Obsidian as the second writer (ex-WI-015).
2. **Torn-write class:** a crash mid-`Path.write_text` leaves a truncated note. No temp-file+rename anywhere.
3. **Consolidation rider — premise restated 2026-08-09; the original claim has been discharged by WI-020.** The six hand-rolled `content.split("---", 2)` splits this rider was written against no longer exist *in the package*. WI-020 collapsed them into one raising helper, `obsidian_schemas/repositories/person.py:_split_frontmatter_fence`, called from five sites (`:1626`, `:1697`, `:1754`, `:1817`, `:1888`), and `obsidian_schemas/repositories/person.py:append_to_timeline` now does deliberate end-of-file string insertion rather than a fence split. Exactly one hand-rolled split survives, at `scripts/migrate_person_to_discuss.py:migrate_person_file:70` — the same unenumerated file that carries an unenumerated write at `:104`. So the parse-divergence argument for this rider is **spent for the package and live only for `scripts/`**. The solve-in-one-place case for the *write* door is untouched by this and stands on its own. See `## Spec-Writer Round — 2026-08-09`.
4. In-process thread-safety (the original March scope) rides along: whatever locking frame the explore picks must also cover the repository cache races.

## Exploration — 2026-07-08 (Fable explore; resolves the 4-way fork)

**Ruling: the four "frames" are not four alternatives. One is a base mechanic, two are
complementary layers over different writer populations, and one is rejected.** The
primitive is a LAYERED COMPOSITE (the WI-057 cage precedent — layers over a single seam):

**The key structural observation:** the vault has two writer populations with different
tractability, and no single frame covers both.
- **Cooperating writers** — this package's consumers (HAL9000, orchestrator, exocortex,
  CLI sessions, lint_vault). They can be made to honor any protocol.
- **A non-cooperating writer** — Obsidian's editor (and any sync agent). It will never
  take our lock, honor our precondition, or route through our door. Any frame that
  pretends otherwise (flock alone) silently fails exactly where WI-015 lived.

**Layer 1 — temp-file + fsync + `os.replace`, unconditionally.** Not a fork option: the
base mechanic every other frame needs. Kills the torn-write class outright. Write to a
sibling temp file in the SAME directory (same filesystem — `os.replace` must not cross
devices), never a temp dir (the WI-065/M1 lesson: temp locations that escape the target
tree break atomicity and confuse sync agents).

**Layer 2 — per-file advisory `flock` for cooperating writers, with the mutate-under-lock
API shape.** The primitive is a callback: `mutate_note(path, fn)` — acquire lock → FRESH
read → parse → `fn` transforms → serialize → Layer-1 replace → release. Because the read
happens INSIDE the lock, a caller structurally cannot write from a stale snapshot — the
lost-update class among cooperating writers is closed by construction, not by caller
discipline (structural guard > prose). This also subsumes the March in-process scope: an
in-process holder registry (the WI-065 `_HELD` depth-registry pattern — flock is per-FD,
threads need the registry) plus a per-repository RLock for cache mutation rides along.
Pattern is REIMPLEMENTED here, not imported from workshop (boundary rule: cross-project
by installed package only, and the dependency points the wrong way — this package is the
foundation; workshop's lock stays workshop's).

**Layer 3 — external-writer detection: precondition re-stat immediately before replace.**
Capture (mtime_ns, size) of the file at the Layer-2 fresh read; immediately before
`os.replace`, re-stat; if changed, an external writer (Obsidian) landed mid-mutation →
raise a loud `ExternalWriteConflict` (caller retries the whole `mutate_note`; the fresh
re-read picks up Obsidian's edit). Never silent, never a code-side merge — deterministic
detection in code, resolution is a retry against fresh state.

**Honest residual (documented, not hidden):** POSIX offers no compare-and-swap on file
content, so a µs-scale window remains between the final re-stat and the `os.replace` in
which an Obsidian write can still be lost. This is irreducible from our side of the
boundary. It is acceptable because: (a) the window shrinks from "entire read-modify-write
span, seconds" to microseconds — the WI-015 class becomes astronomically rare instead of
routine; (b) Obsidian only writes when Dave is actively editing THAT note in the same
microsecond as a pipeline mutation of the same note; (c) Obsidian's own writes are
whole-file safe-writes, so the loser is one field update, detected at next read, never a
torn file. The spec must state this residual verbatim; a spec claiming total external
safety is wrong and should fail review.

**Rejected: single-writer daemon.** It does NOT remove the second writer (Obsidian still
writes regardless), so it buys no external safety over Layers 2+3; it couples every
consumer — cron jobs, CLI one-offs, exocortex batch ingest — to a daemon's availability
(and the tempting "fall back to direct writes when the daemon is down" is precisely the
circumvention-helper anti-pattern); and it is the largest build for the least marginal
safety. The existing behavioral rule ("people notes via HAL9000 API") stays as policy
for note CREATION; it is not the mutation-safety mechanism.

**Rejected as sole frame: optimistic-only (no flock).** Detection without mutual
exclusion turns every cooperating collision into a caller-visible retry; with flock
available and cheap on a local single-host vault, making our own traffic collision-free
and reserving conflict errors for genuinely external writes is strictly better ergonomics
for three consumer repos.

**Spec-stage verification obligations (data-premise material — verify, don't assume):**
1. Vault filesystem: confirm the live vault is local APFS (flock semantics degrade on
   some network/synced filesystems; if iCloud/Dropbox is under it, re-open this ruling).
2. Obsidian's write pattern: confirm by observation (edit a note, watch inode/mtime)
   that it whole-file-replaces — grounds the Layer-3 residual argument.
3. Lock sentinel placement: sentinels must NOT be vault-visible files Obsidian indexes —
   candidate: a dot-directory (e.g. `<vault>/.obsidian-schemas-locks/`) since Obsidian
   ignores dot-dirs; verify, else home them outside the vault keyed by path hash.
4. Enumerate ALL mutation sites (the doc's list is 2026-07-05-dated; re-grep at spec
   time) — the consolidation is only solve-in-one-place if the routing is exhaustive.

## Approach

**Revised 2026-08-09 after the architect's REVISE (`targets: #approach, #intent`) and the
data-premise gate's finding on the quarantine rename.** The prior text defined the primitive by a
*list of sites* and gave it one shape, `mutate_note(path, fn)` :: `(path, text → text)`. Both
blocking findings are the same defect seen twice: a site whose semantics that shape cannot express.
This revision replaces the site list with a **shape-defined surface**, rules on every cell of the
mutation sweep recorded in `## Spec-Writer Round — 2026-08-09` — including the two cells no
reviewing gate has named yet — and closes the residual enumeration the architect asked for. What
the ruling is conditional on is stated at the end rather than assumed away.

**Revised again 2026-08-09 (round 3) after the architect's round-2 REVISE on the create path.** The
round-2 finding is that door 2's ruling covered writes with a derivation read and said nothing about
writes with none, so "the rule is total because every write has a derivation read" was false for
`create_stub` and the concurrent-create clobber survived the frame — silently. Round 3 does four
things: it **restates the total rule** so its zero case (no derivation read → atomic non-existence
precondition) is part of the rule rather than an ad-hoc handling of door 3; it **rules the create
cell** at (i), an atomic no-clobber create, with the consequence spelled out for `create_stub`,
`find_or_create_stub` and the book/company stubs; it **names where door 2 physically lives**
(`write_markdown_file`, with a path-keyed stamp registry) after verifying that two of the three
`save()` implementations never reach `BaseRepository.save`; and it **adds R7** to the residual list.
The rulings the architect explicitly closed in round 1 — (b) for door 2u, the prior-art paragraph,
the shape-defined framing — are untouched.

**Revised again 2026-08-09 (round 5), in two places only.** The round-4 architect and data-premise
gates both found the same two defects, and neither is in the frame: (1) the *observation* side of the
door-2 boundary was written as one function name while the tree has three loaders — closed in
`## Design` D5 by deriving the corpus and enforcing over it, with the level above it (entity
derivation outside the loader corpus) swept and declared in the same fold; (2) `mkdir` was ruled to
stay outside the primitive while sitting inside the routing wall's vocabulary, which made AC-7
unsatisfiable — closed by moving both calls into `vault_io.ensure_dir` and restating R5 below.
Nothing else in this section moves; `## Spec-Writer Round 5 — 2026-08-09` at the end of this document
records what changed and what deliberately did not.

### The generator, and the one rule that closes it

The class behind both findings is stated in the spec-writer round: *the primitive's surface was
chosen before the mutation shapes were enumerated.* `(path, text → text)` is a claim that every
vault mutation is a pure transform over the current bytes of one existing file. Three cells of the
sweep falsify it, so each reviewing gate finds one more and will keep doing so.

**Revised again 2026-08-09 (round 3), and the revision is a level up.** The round-2 architect found
a write with **no** derivation read — the create path — and the rule as previously written ("the rule
is total because every write has a derivation read") was simply false there. That finding is not a
fourth instance of round 1's generator; it belongs to a *second* generator, one level above it, and
the two are closed by one sentence.

**Generator A (round 1) — the surface was chosen before the shapes were enumerated.** Closed by
defining the surface by mutation shape. Holds; not re-opened.

**Generator B (round 2) — a precondition evaluated against something other than the target, at a
time other than the write, whose ABSENCE was read as a pass.** Every member found by sweeping the
tree for "what does this write check, against what, and when":

| Site | What it checks | Against what | When |
|---|---|---|---|
| `obsidian_schemas/repositories/person.py:create_stub:1429` | destination exists | `self._cache` (`base.py:get:269`) — **not the target** | at guard, not at write |
| `obsidian_schemas/repositories/book.py:create_stub:273`, `obsidian_schemas/repositories/company.py:create_stub:153` | **nothing** — no collision branch of any kind | — | — |
| `obsidian_schemas/writer.py:write_markdown_file:186` (`overwrite=False`) | destination exists | the target | at guard; the `write_text` is 50 lines later at `:236` |
| `scripts/lint_vault.py:quarantine_garbage:1036` | destination exists | the target | at guard; the `rename` is at `:1038` |
| Door 2's stamp (as ruled round 2) | derivation-read equality | the target | at the write — **the only one that was already right** |

Closing the instances is not the fold. The rule that closes both generators, and it is a
generalisation of Layer 3 rather than a new mechanism:

> **Every write is preconditioned at the write syscall, against the target itself, on the read its
> bytes were derived from — and a write whose bytes derive from no read of the target is
> preconditioned on the target's NON-EXISTENCE, enforced atomically.**

The second clause is not an exception to the first: it is the first clause's **zero case**. An empty
derivation read admits exactly one prior state of the target — absent — so "the target still matches
what my bytes came from" *means* "the target still does not exist". That is why doors 2c and 3 below
are one ruling and not two ad-hoc ones.

Three properties make the rule total where the previous sentence was not:

1. **Absence of a stamp is the strictest case, never the loosest.** Under the previous text, a path
   with no recorded derivation read had no precondition — which is exactly LESSONS #5's
   PASS-by-default-on-empty ("empty is a bug shape, not a normal mode") sitting at the write
   boundary, and exactly what the round-2 architect found in code. Under the rule, an unstamped path
   must not exist. A cell nobody enumerated fails closed.
2. **The precondition is evaluated at the write, against the target.** This is what collapses every
   check-then-mutate gap in the table into a single syscall guarantee, rather than fixing the one a
   gate happened to name — and it is why the rows with no check at all (`book.py`, `company.py`) need
   no per-site fix: the precondition lives in the door, so a caller that never wrote a guard gets one.
3. **A successful DOOR-2 write registers the new stamp for its path**, exactly as a derivation read
   does — otherwise a process that creates a note and then saves it again would refuse its own
   second write. **Narrowed round 4 to door 2 only, closing the architect's round-3 note #1.** As
   first written this said "a successful write", which made the registry serve two purposes on one
   field: a door-1 write would advance the stamp for a path whose cached ENTITY is older, and the
   next `save()` of that entity would compare S1 to S1 and pass — silently destroying the door-1
   frontmatter change by the very mechanism written to make it loud (LESSONS #43). The registry
   records at the points where an ENTITY is derived from a file's bytes and nowhere else; door 1
   never touches it, because its precondition is call-local and needs no registry at all. Mechanics,
   the observation points, and the re-run of the architect's own scenario are in `## Design` D5.

Layer 3 as originally written anchors the precondition at the fresh in-lock read, which is correct
*for a caller whose bytes are derived from that read*. For a caller whose bytes are derived from an
earlier read, comparing against the in-lock read proves nothing — this is exactly why Layer 3
"cannot rescue" the entity door. The doors below differ only in **where that read happened, or that
it did not happen at all**, and the size of each door's residual window is exactly the distance
between that read and the replace.

**What the next level of the ladder returned, declared rather than left for round 4.** Sweeping
(precondition source) × (evaluation time) × (meaning of absence) over the four level-2 mutation kinds
returns three further sub-cells, all ruled here rather than deferred:

- **Door 1 against a path that does not exist.** `mutate_note` reads before it transforms, so a
  missing file is not a create — it raises (`NoteParseError`/`FileNotFoundError`, per WI-020's
  floor). Door 1 never creates, by construction; a caller wanting a create uses door 2c.
- **Door 2c against a path this process itself just created.** Covered by property 3 above: the
  create registers its stamp, so the following `save()` is a 2u update, not a refused create.
- **`mkdir` (the namespace cell).** Absence-of-precondition is *correct* there and stays ruled out —
  `mkdir(parents=True, exist_ok=True)` is idempotent and has no loss mode. It is the one cell where
  "no precondition" is a decision rather than a gap, and it is recorded as such below and as R5.
  **Narrowed round 5.** What this cell is outside is the PRECONDITION rule — it is *not* outside the
  wall's reach. Those are two different claims and the round-4 architect and data-premise gates both
  found the document conflating them: `mkdir` sits in the wall's vocabulary, so Wall A forbids the two
  live calls (`obsidian_schemas/writer.py:write_markdown_file:233`,
  `scripts/lint_vault.py:quarantine_garbage:1034`) that R5 as written ordered left in place, making
  AC-7 unsatisfiable. Ruled: **the calls move into the single-homed module as `ensure_dir`, and
  `mkdir` stays in the vocabulary.** Wall A's claim is about where a filesystem capability may be
  NAMED, not about which calls have a loss mode, and narrowing the vocabulary to make a green
  is the wall silently shrinking its own reach — the precise failure D10's fixture battery exists to
  prevent. R5 is restated below on that ruling. *(Round 6: `mkdir` is homonym-free, so it lands in
  `PATH_MUTATION_NAMES` — the arm matched on attribute name alone. Nothing about this cell moves;
  only the vocabulary's name does. See D10.)*

### Door 1 — content transform: three primitives in the caller's own frame

Layers 1+2+3 as explored. Acquire per-file advisory lock (with in-process reentrancy) → fresh read
→ parse → caller's transform → serialize → re-stat precondition against the in-lock read →
temp-file + `fsync` + `os.replace` in the same directory. Derivation read = the in-lock read, so
the precondition is anchored there and the residual window is the µs between the final re-stat and
the replace.

**Revised round 4 — the CALL SHAPE, and only the call shape.** Door 1 is not `mutate_note(path, fn)`
:: `(path, text → text)`. It is three primitives the caller invokes in its own frame —
`note_lock(path)`, `read_note(path) -> (text, stamp)`, `write_note(path, text, precondition=stamp)`.
Layers, ordering, precondition anchor and residual are all unchanged; what changes is that the
caller's transform stays in the caller's body instead of moving into a callback. Two reasons, the
first of which is a hard build constraint no gate has named:

1. **A callback moves every routed writer's body into a nested function, and WI-020's derived
   acceptance battery classifies those bodies.** `tests/derivations.py:_own_body_nodes:148` skips
   nested functions by construction, so under a callback shape the eight falsy returns
   `tests/test_loud_fail_write.py:103` classifies by `SiteId(module, qualname, ordinal)` acquire new
   qualnames (`…append_to_timeline.<locals>.…`) and the map at `:126-139` goes stale — AC-5 red
   against correct code. `tests/test_loud_fail_parse.py:110-137` has the same exposure: its
   `write_paths` set is exactly four `FunctionId`s whose membership requires the parsed frontmatter
   dict to reach a write call **in that same function's own body**. Under the three-primitive shape
   both survive with ONE edit — `_is_write_call` gains the door names — because "a call that commits
   bytes" is unchanged in meaning and the door is how package code now commits them.
2. **It does not weaken the structural guard, because the guard was never the closure.** What makes
   a stale-snapshot write impossible is the PRECONDITION, not the callback: `write_note` takes a
   `NoteStamp` that only `read_note` (and the repository observation points) can mint, and a call
   with no stamp is the zero case — an atomic no-clobber create. A caller that skips `read_note`
   therefore cannot silently overwrite; it gets a create refusal. `write_note` additionally refuses
   when the lock for its path is not held by this process, so a caller that skips `note_lock` fails
   loud rather than racing. Both are enforced in the door, which is where the rule above puts them.

**Routes here (13 of the 14 content-write sites),** in the two sub-shapes the level-4 sweep found —
both genuinely transform-shaped:

- *Parse-and-reserialize:* `obsidian_schemas/writer.py:update_frontmatter_field:283`,
  `obsidian_schemas/writer.py:update_frontmatter_fields:333`,
  `obsidian_schemas/writer.py:roundtrip_file:365`,
  `obsidian_schemas/repositories/base.py:update_fields:390`, `scripts/lint_vault.py:876`.
- *Verbatim frontmatter carry-through:* the five `person.py` body writers
  (`:1543`, `:1554`, `:1652`, `:1769`, `:1845`, `:1912` — six sites, five methods; see the
  granularity note in the spec-writer round), `scripts/lint_vault.py:894`,
  `scripts/migrate_person_to_discuss.py:104`.

### Door 2 — the entity write: two preconditions, one door, and the door is `write_markdown_file`

Door 2 is the entity write — the only door that sees an entity rather than bytes. It carries **two**
preconditions because it serves two cases, and the round-2 architect's finding is that the previous
text wrote only the first. Both are the one rule above, evaluated at the write syscall against the
target; they differ only in whether a derivation read exists.

#### Door 2u — update: a derivation read exists, so the precondition is stamp equality

**The finding, re-verified in code this round.** `obsidian_schemas/repositories/base.py:save:294`
passes an entity straight to `obsidian_schemas/writer.py:write_markdown_file:154`, which at
`:217-218` builds frontmatter wholesale from that entity (`fm = model_to_frontmatter(entity, …)`)
and never merges with disk. The entity comes from `self._cache` (`base.py:142`), populated once at
`load()` and invalidated only by an explicit `refresh()`
(`obsidian_schemas/repositories/base.py:refresh:419`) — nothing else triggers it, so in a
long-lived HAL9000 process the snapshot can be hours old. The WI-126 guard does not cover this:
`obsidian_schemas/writer.py:_body_content_lines:69` iterates `body.splitlines()` only, and its own
docstring says so ("The frontmatter survives … the body is the loss"). All three `save()` overrides
reach `write_markdown_file` (`obsidian_schemas/repositories/person.py:save:1252`, `book.py:save:138`,
`meeting.py:save:160`) — though only person's reaches it *via* `BaseRepository.save`, which is the
placement point ruled below.

**Ruling: (b) — `save()` keeps snapshot-overwrite semantics. (a), the merge, is rejected.** The
merge would require a field-level precedence rule that does not exist anywhere in this package, and
that rule is undecidable from here: a consumer that deliberately *clears* a field is
indistinguishable, at the frontmatter level, from a consumer whose snapshot simply predates someone
else setting it. Choosing a precedence rule to make the merge work would silently reinstate cleared
fields for three consumer repos — a new correctness hazard introduced by the fix. Snapshot
semantics are what `save()` means today and what its callers were written against; they stay.

**But (b) does not mean the loss stays silent.** Applying the rule above: door 2u's derivation read
is the *cache load*, so its precondition is anchored there. The repository records `(mtime_ns, size)`
for each note at the moment it loads that note into `_cache`/`_file_map` — into the path-keyed stamp
registry the door owns, per the placement ruling below, not onto the repository object; the door then
takes the lock, re-stats the target, and compares against **the stamp the snapshot was taken at**. On
a mismatch it raises `StaleEntityWrite` — loud, retryable by `refresh()` + re-apply, never a
code-side merge.
This is the same optimistic-precondition mechanism as Layer 3 (and the same one `If-Match`, vim and
VS Code use), anchored one level up; it is not a new closure semantic. Layers 1 and 2 apply to this
door unchanged — atomicity and mutual exclusion are free here and strictly better than not having
them.

**Consumer-facing consequence, stated plainly:** `save()` gains a new raising failure mode. Code in
HAL9000, orchestrator and exocortex that calls `repo.save(entity)` and today always succeeds can
now raise `StaleEntityWrite` when another writer touched the note since this process loaded it.
That is the intended change — it converts a silent lost update with a window measured in hours into
a loud, retryable refusal — and it is the direction WI-020's loud-fail floor already committed this
package to. `StaleEntityWrite` and `ExternalWriteConflict` are both `LoudFailError` subclasses
(so `except LoudFailError` catches "this package refused"), and both must be distinguishable from
`WriteFailedError` so a caller can retry on a conflict without also retrying a genuine IO failure.

**Integration constraint on minting those exceptions, noted so Design does not discover it.** WI-020's
hierarchy has ONE constructor and a closed reason vocabulary: `obsidian_schemas/errors.py:REASONS:88`
is a frozenset of exactly twelve source literals, and
`obsidian_schemas/errors.py:bounded_message:109-120` raises on any reason outside it — "the enforced
form of 'a literal written in this package's source'". Each new subclass this item mints
(`StaleEntityWrite`, `ExternalWriteConflict`, `NoteAlreadyExists`) therefore lands as a subclass
declaring no `__init__` of its own **plus** its reason literal added to `REASONS`, in the same edit.
A subclass added without its literal raises `ValueError` at first construction — i.e. exactly when
the conflict it exists to report occurs.

**And the count is a pin, so it goes (round 4).** `obsidian_schemas/errors.py:84` opens the frozenset
with the prose "Exactly the twelve literals of the construction table below". That sentence is a
hardcoded count over a corpus this item grows by three, so Design orders it restated as a predicate
("exactly the literals of the construction table below") rather than re-numbered to fifteen — the
pin moves again the next time a subclass is minted. No test asserts `len(REASONS)`; the sweep behind
that claim, and the two count pins this item does NOT move, are declared in `## Implementation Plan`
Task 2.

#### Door 2c — create: no derivation read, so the precondition is atomic non-existence

**The finding, verified in code this round rather than inherited.** `create_stub` builds a `Person`
from scratch (`obsidian_schemas/repositories/person.py:create_stub:1444-1452`) and writes it through
door 2 at `:1466` with `overwrite` defaulting to `True`
(`obsidian_schemas/repositories/base.py:save:299`, `obsidian_schemas/repositories/person.py:save:1252`).
Its collision guard reads the **cache, not the disk** — `existing = self.get(clean_name)` at `:1429`
resolves to `self._cache.get(...)` (`obsidian_schemas/repositories/base.py:get:269`), populated at
`load()` and invalidated only by an explicit `refresh()` — so a note another process created *after*
this process loaded is invisible and the reuse branch at `:1430-1437` is never taken. The WI-126
guard does not catch the overwrite that follows: `obsidian_schemas/writer.py:write_markdown_file:210-214`
runs the drop check only `if existing_lines:`, and `obsidian_schemas/writer.py:_body_content_lines:69-80`
discards blank and `#`-prefixed lines, so against a freshly-minted victim stub — body
`"## To Discuss\n\n## Timeline\n\n## Notes\n"` (`obsidian_schemas/body_sections.py:ENTITY_BODY_CONFIG:306`),
headings only — the set is empty, the guard no-ops, and `writer.py:236` rebuilds the note from the
in-memory entity (`writer.py:217-218`). `BookRepository.create_stub`
(`obsidian_schemas/repositories/book.py:create_stub:273`, body `# {title}` + headings, also
content-empty) and `CompanyRepository.create_stub`
(`obsidian_schemas/repositories/company.py:create_stub:153`) are the same shape and carry **no
collision branch at all**, not even a cache-backed one.

**Ruling: (i) — a create is an atomic no-clobber create.** The destination's non-existence is
enforced by the syscall, not by a check: the temp file of Layer 1 is linked into place with a
no-clobber form (`os.link`, or `O_CREAT|O_EXCL`) whose failure on an existing destination is a
kernel guarantee rather than a race. On failure the door raises `NoteAlreadyExists`, a
`LoudFailError` sibling of `StaleEntityWrite` and `ExternalWriteConflict`. Option (ii) — no
precondition — is rejected: it leaves door 2's widest hole open on the package's highest-frequency
write path, and the doc's own deciding argument for minting door 3 applies here verbatim ("declaring
the cell out of scope would leave a known destructive race inside the very item that exists to kill
destructive races"), with a window equal to the cache's lifetime rather than an instruction gap.

**Why this is a declaration rather than a redesign** — the same test that made (b) the right ruling
for door 2u. Not-clobbering an existing note on create is not a new semantic this spec is inventing:
it is the invariant the code *already declares in a comment it cannot keep*.
`obsidian_schemas/repositories/person.py:1419-1428` states it outright — "REUSE it — never overwrite
a rich note with the empty template, which resets `created`/`created_by` and wipes the Timeline (the
loud door WI-119 caught on 06-14)". The reuse branch is defeated cross-process only because the
guard consults a cache. (i) restores an intent the tree records; (ii) would knowingly preserve a
defect. Choosing (ii) is Dave's to make and is now a reversal of a written ruling, not a gap.

**Consumer-facing consequence, stated as plainly as 2u's.** The refusal is caught where a reuse
branch already exists and surfaced where one does not:

- **`PersonRepository.create_stub`** catches `NoteAlreadyExists`, re-reads *that one path* via
  `obsidian_schemas/repositories/base.py:_load_file:226` (not `refresh()` — that is a whole-vault
  reload whose zero-entity restore guard at `base.py:refresh:419` makes it the wrong instrument for
  a single-note recovery), and then takes the reuse-on-collision branch it already has at `:1430-1437`
  — `_writeback_identifier` merges the supplied email/phone, and it returns the existing person. Net
  effect for HAL9000 and exocortex: **the cross-process race now produces the same outcome the
  in-process collision already produces**, with the same WARNING at `:1431`. No new raising mode in
  the normal case.
- **`find_or_create_stub`** (`obsidian_schemas/repositories/person.py:find_or_create_stub:698`)
  reaches `create_stub` through the WI-125 engine's Branch C
  (`obsidian_schemas/repositories/person.py:resolve_or_create:878`) and therefore inherits that
  recovery unchanged. Its `(Person, created_new)` contract is preserved: a create that loses the race
  returns `created_new=False`, which is what in fact happened. A caller that keyed off
  `created_new is True` sees `False` in a case where it previously saw `True` over a clobbered note.
- **`BookRepository.create_stub` and `CompanyRepository.create_stub` gain a genuine raising mode**,
  because they have no reuse branch to fall into. `NoteAlreadyExists` reaches the caller. Loud
  beats clobber; giving them the reuse-and-writeback behaviour `PersonRepository` has is a
  resolution-policy change on two entity types, out of scope here, and it is a strictly smaller
  question once the door refuses rather than clobbers.
- **`save()` on an existing note held by a repository that never loaded it** (e.g. `auto_load=False`,
  or a note created after this process's `load()`) has no stamp, so it is refused as a create rather
  than landing as a silent overwrite. The remedy is `refresh()` then re-apply — the same remedy
  `StaleEntityWrite` already prescribes. Where a caller genuinely means "replace this note from a
  snapshot I did not read", the escape is an **explicit, per-call, named** argument in the shape of
  the WI-126 precedent (`allow_body_replacement`, `obsidian_schemas/writer.py:write_markdown_file:161,173-174`)
  — never a module-level default, and never `overwrite=True`, which is already the default and
  therefore means nothing.

#### Where door 2 physically lives: `write_markdown_file`, with a path-keyed stamp registry

The round-2 architect is right that "in `save()`" does not name a place: `save()` is three
implementations and two of them never reach `obsidian_schemas/repositories/base.py:save:294` —
`obsidian_schemas/repositories/book.py:save:163` and
`obsidian_schemas/repositories/meeting.py:save:185` call `write_markdown_file` directly, verified in
code this round. **Ruling: the door is `obsidian_schemas/writer.py:write_markdown_file:154`, and the
stamp registry is path-keyed and owned by the write primitive, not by the repository.** Three
reasons, in order of weight:

1. **It is the only placement that is total.** `write_markdown_file` is the one choke point that sees
   both the entity and the path. Every present `save()` routes through it, and a fourth repository
   added tomorrow inherits the door for free rather than needing to be remembered.
2. **The alternative cannot be enforced by the wall this item ships.** Routing every `save()`
   individually leaves a miss the routing wall structurally cannot see: its inventory is filesystem-
   call *kinds* (`tests/derivations.py:_is_write_call:189-195` matches `write_text`/`write_bytes`
   only, confirmed), while a repository that calls `write_markdown_file` performs no filesystem write
   at all. The wall would stay green while door 2 was bypassed — precisely what the
   "unrecognised kind is an ERROR, not a pass" rule exists to make impossible. Putting the door
   *inside* `write_markdown_file` dissolves that bypass rather than asking the wall to detect it.
3. **It keeps the two halves where each is known.** The repository is what performs derivation reads,
   so the repository **records** `(mtime_ns, size)` into the registry keyed by resolved absolute
   path; the primitive is what performs writes, so it **enforces**. *Sharpened round 5:* "the
   repository" is not a place either, and naming one function for it was the round-4 defect — the
   recording point is the CORPUS `load_file_implementations(base_repository_subclasses(...))`
   resolves to, which is three functions today and is enforced as such by Wall D. Mechanics in
   `## Design` D5. The registry is
   a record of observations, never an authority: an unregistered path is the zero case of the rule
   (must not exist), so the fail-safe direction is built in rather than assumed.

**Cross-process cache staleness — the title's "stale-read protection" — gets its owner here, and it
is a partial one.** The stamp precondition closes the stale-*write* case for door 2: a write derived
from a stale snapshot is refused rather than landing. It does **not** make reads fresh — `get()`,
`get_all()` and `resolve()` still serve whatever `load()` put in `_cache`, and a note another
process rewrote is served stale until someone calls `refresh()`. Making reads coherent is a
different mechanism (invalidation on stat, or a watch) with a different cost profile, and it is
**out of scope for this item**; it is declared as residual R2 below rather than left implied by the
title.

### Door 3 — whole-file move: a second door, `move_note(src, dest)`

`scripts/lint_vault.py:quarantine_garbage:1038` renames a note into `<vault>/_quarantine/`. The
file's identity changes, so there is no "current bytes of this path" to transform; it is
structurally inexpressible as door 1, exactly as the data-premise gate found.

**Ruling: a second door, not an out-of-scope declaration.** The deciding fact is that the site
carries a live TOCTOU of its own — `dest.exists()` at `:1036` guards `src.rename(dest)` at `:1038`
with nothing held between them, and `Path.rename` clobbers silently on POSIX when the guard loses
the race. Declaring the cell out of scope would leave a known destructive race inside the very item
that exists to kill destructive races. `move_note(src, dest)` therefore takes Layers 1+2 in the form
those layers have for a move: both paths locked, **acquired in sorted-path order** so two concurrent
moves cannot deadlock, and an **atomic no-clobber** create at the destination (a link-then-unlink
form, whose failure on an existing destination is a syscall guarantee rather than a check) so the
`exists()`/`rename` gap ceases to exist.

**Door 3 is not a special case — it is door 2c's mechanism on a different payload.** Round 2's text
handled this door ad hoc ("Layer 3 does not apply: there is no derivation read of the destination's
bytes") and that ad-hoc-ness was the tell: a second write with no derivation read was already in the
doc before the create path was found. Under the rule, both are the zero case — bytes derived from no
read of the target are preconditioned on the target's non-existence, enforced atomically — so door 3
and door 2c share one mechanism and one exception (`NoteAlreadyExists`). The only difference is the
payload: door 2c links a serialized entity into place, door 3 links an existing inode. The source
path of a move *does* have a derivation read in the ordinary sense and is covered by Layer 2's lock;
what has none is the destination.

### The cells that get no door, ruled rather than omitted

- **Namespace mutation (`Path.mkdir`) — out of the PRECONDITION rule, inside the module. Not a
  residual.** Two sites, re-verified round 5 and still exactly two under `obsidian_schemas/` and
  `scripts/`: `obsidian_schemas/writer.py:write_markdown_file:233` and
  `scripts/lint_vault.py:quarantine_garbage:1034`, both `mkdir(parents=True, exist_ok=True)`. They
  create no note content and have no loss mode: the call is idempotent and there is nothing for a
  second writer to overwrite, so it gets **no door and no precondition** — ruled out because the cell
  is empty of risk, not because nobody looked at it. **But the call still lives in
  `obsidian_schemas/vault_io.py`, as `ensure_dir(path)`** (round-5 ruling; both sites and
  `note_lock`'s own sentinel-directory creation route through it), because the single-homing wall's
  subject is the *capability's location*, not the *call's risk*. Keeping two `mkdir` calls outside
  the module while `mkdir` is in the wall's vocabulary is a contradiction the builder can only
  resolve by narrowing the wall; keeping them outside while dropping `mkdir` from the vocabulary
  makes a future `Path.mkdir` anywhere invisible to Wall A. Neither is acceptable, and `ensure_dir`
  costs two call sites.
- **Delete (`unlink` / `os.remove` / `rmdir`) — zero sites today.** The cell is empty in
  `obsidian_schemas/` and `scripts/`. It does not get a door, and it must not get one by
  assumption either: see the wall rule immediately below.
- **The wall rule for cells nobody has enumerated** (distinct from the precondition rule above: that
  one is total over *writes*, this one is total over *mutation kinds*). The routing wall derives its
  mutation inventory **from the tree**, per kind, and treats a kind it does not recognise as an
  **ERROR, not a pass**. A future `unlink`, `shutil.move` or `open(p, "w")` therefore surfaces as a
  red wall demanding a ruling, rather than as the next reviewing gate's next finding. **Three**
  obligations ride with that wall and belong in Design, not here.
  *(a)* `tests/derivations.py:_is_write_call:189-195` matches on attribute name in
  `{"write_text", "write_bytes"}` only, so it resolves **none** of the level-2 kinds beyond content
  rewrite — it must be widened to the kinds above before it can back a "no un-routed mutation"
  claim. **Sharpened round 6:** it also gates on `isinstance(node.func, ast.Attribute)`, so *how the
  routed sites CALL the door* is part of this obligation and not a build detail — ruled in D10 (the
  doors are named as module attributes, `vault_io.write_note(...)`). *(b)* The wall's roots must
  include `scripts/`, since both enumeration misses every gate found landed there. *(d, round 6)* The
  wall's vocabulary must **discriminate by provenance, not by member name**, wherever the name has a
  non-filesystem homonym: an attribute-NAME oracle cannot separate `p.replace(q)` from
  `s.replace("-", "")` or `shutil.copyfile` from `frontmatter.copy()`, and this tree exercises the
  non-filesystem side of both verbs today. D10 rules it and R10 states what the ruling leaves open.
  *(c)* **The wall's claim must be stated as single-homing, not as a call
  count** — the primitive's module is the ONE file under `obsidian_schemas/` or `scripts/`
  permitted to name `write_text`, `write_bytes`, `rename`, `os.replace` or the temp-file machinery,
  and the wall asserts that. This is the shape `tests/derivations.py` already uses on itself — its
  module docstring at `tests/derivations.py:1-22` declares it "the only file under
  `obsidian_schemas/` or `tests/` permitted to name `ast`", and AC-7 enforces that by scanning for
  the capability rather than for known copies. Single-homing is what makes the wall's oracle mean
  something: a kind-counting wall cannot see a package-internal bypass (a repository that calls
  `write_markdown_file` performs no filesystem write at all), whereas a capability wall catches any
  new file that reaches for the syscall, named or not.

### Prior art — the two outside-view rulings, written rather than assumed

**Obsidian's own API via MCP. Rejected.** WI-015, which this item absorbs, named "preferring
Obsidian's API via MCP where possible" (`docs/obsidian-plugin-sync.md:20`) and the absorption
dropped it without a ruling. Rejected on three counts. It inverts the dependency direction: this
package is the filesystem foundation three repos install `-e`, and routing its writes through an
editor plugin makes the foundation depend on a GUI application being alive. It cannot serve the
consumers that matter most here — headless cron jobs, CLI one-offs and exocortex batch ingest all
write when Obsidian is not running, and the tempting "fall back to direct writes when the API is
unavailable" is the same circumvention-helper shape this doc already rejects for the single-writer
daemon. And the project has made this call once already, in code:
`obsidian_schemas/repositories/person.py:append_to_body_section:1567` exists precisely so writers
route through the package "instead of MCP `patch_vault_file`" (`:1578-1579`). Reversing that at the
write primitive would undo a decision the tree records.

**Build vs integrate for Layer 2. Ruled: integrate `filelock`.** The doc rules out importing
workshop's lock (correctly — the dependency points the wrong way) but never considered the
maintained third-party answer. `filelock` and `portalocker` both solve exactly the Layer-2
sub-problem *including* the reentrant in-process holder counter this doc planned to reimplement as
the WI-065 `_HELD` registry. That counter and the per-FD/per-thread distinction are the part of
advisory locking that is easy to get subtly wrong and whose failure is silent, which is the
strongest case there is for not writing it again. The cost is real and is the counter-argument: a
new runtime dependency on a foundation library with three consumers, which all three inherit. It is
outweighed here because `filelock` is pure Python with no native code and a stable API, and this
package already carries `pydantic` and `PyYAML`. **This ruling is recorded so it is not re-raised
as unruled a third time**; reversing it to a hand-rolled `_HELD` registry is a legitimate call for
Dave to make, but it is now a reversal of a written decision rather than a gap.

### The WI-021 seam

`docs/write-door-bypasses.md:18` plans to hang NameValidator and address normalization on this
primitive. Door 1 is **content-level** (`path`, `text → text`) and cannot host entity-level checks —
there is nothing there for WI-021 to hang on. **Door 2 is the seam**: it is the only door that sees
an entity. Sharpened round 3 by the placement ruling — the seam is door 2's entry *inside*
`obsidian_schemas/writer.py:write_markdown_file:154`, before either precondition and before the
serialize, because that is the choke point every `save()` reaches and the two repositories that
bypass `BaseRepository.save` (`book.py:save:163`, `meeting.py:save:185`) would otherwise skip an
entity-level check hung one frame higher. The precedent for an entity-level check on this path is
`_normalize_address_fields`, which `obsidian_schemas/repositories/person.py:save:1252` runs today —
but note that it sits in exactly that higher frame and therefore does *not* run for books or
meetings. Whether to move it down to the door is WI-021's call, not this item's; this item neither
moves it nor depends on where it lands. Door 1 and door 3 are explicitly not WI-021 surfaces; the
paths WI-021 names that are frontmatter-level but route through door 1 (notably
`base.py:update_fields:339`) need their own ruling in WI-021 and do not get one here.

### Residuals under this frame — the closed list

The architect asked that the residual paragraph enumerate *every* residual the chosen frame leaves,
not only the µs external window. One entry per (mutation kind × writer population) cell this frame
does not cover:

- **R1 — the µs external window (all three doors × the non-cooperating writer).** *Stated verbatim
  as the exploration requires:* POSIX offers no compare-and-swap on file content, so a µs-scale
  window remains between the final re-stat and the `os.replace` in which an Obsidian write can still
  be lost. This is irreducible from our side of the boundary. It is acceptable because: (a) the
  window shrinks from "entire read-modify-write span, seconds" to microseconds — the WI-015 class
  becomes astronomically rare instead of routine; (b) Obsidian only writes when Dave is actively
  editing THAT note in the same microsecond as a pipeline mutation of the same note; (c) **restated
  on observation, 2026-08-09 (obligation 2 discharged): Obsidian saves IN PLACE — same inode
  (220735514), size 5049→5085, mtime advanced, across a live person-note edit by Dave — i.e.
  truncate-and-write, NOT a whole-file safe-write.** The prior draft's clause (c) ("the loser is one
  field update … never a torn file") was wrong in kind, exactly as this marker anticipated: a reader
  overlapping Obsidian's truncate window can observe a truncated note, so the µs-window loser is not
  bounded to one field update in shape — (a) and (b) still bound the *frequency*; nothing bounds the
  *shape*. The spec must reproduce THIS observed residual verbatim; a spec claiming total external
  safety, or claiming Obsidian safe-writes, is wrong and should fail review.
- **R2 — read staleness (all doors × the cooperating writer).** A repository serves `get()` from a
  cache invalidated only by an explicit `refresh()`. Door 2's stamp precondition refuses a *write*
  derived from a stale snapshot; nothing here makes a *read* fresh. Owner: the caller, via
  `refresh()`. Out of scope, declared.
- **R3 — advisory means advisory (all doors × the non-cooperating writer).** Layer 2 excludes only
  writers that take the lock. Obsidian, sync agents, and any hand-rolled script that does not route
  through these doors are unaffected by construction. Layer 3 detects them after the fact; it does
  not exclude them.
- **R4 — door 3 has no external-writer detection.** A move has no derivation read of the
  destination's bytes, so Layer 3 does not apply. An Obsidian edit in flight when a note is
  quarantined is moved along with the note; the edit is not lost, but its path changes under the
  editor.
- **R5 — the namespace cell gets no PRECONDITION (restated round 5).** `mkdir` gets no door and no
  precondition: it is idempotent and has no loss mode (see above), so this is a declared decision
  rather than an accepted risk. It is **not** outside the wall's reach — `mkdir` stays in the wall's
  vocabulary (round 6: in `PATH_MUTATION_NAMES`) and all three calls (`writer.py:233`,
  `scripts/lint_vault.py:1034`, and
  `note_lock`'s sentinel directory) are made through `obsidian_schemas/vault_io.py:ensure_dir`, so
  Wall A's single-homing claim is literally true rather than carrying a silent exemption. The prior
  wording — "`mkdir` gets no door", read as "the two sites stay where they are" — is what made AC-7
  unsatisfiable, and it is corrected rather than softened.
- **R6 — `scripts/` is a consumer, not the package.** The two script sites route through the doors,
  but a *new* script bypassing them is caught only if the routing wall's roots include `scripts/`.
  That is an obligation on the wall (above), and until it holds this is a residual.
- **R7 — a losing create keeps only its identifiers (door 2c × the cooperating writer).** Added
  round 3, with the create cell's ruling. The atomic no-clobber create means the *destination* is
  never destroyed, so there is no lost-update residual on the winner's note. What is not preserved
  is the rest of the loser's payload: `create_stub`'s recovery re-enters the reuse branch, which
  merges the supplied email/phone through `_writeback_identifier` and drops everything else the
  losing create carried — `company`, and the `created_by` provenance the caller passed
  (`obsidian_schemas/repositories/person.py:create_stub:1463`). **Reuse is not merge**, and merge is
  rejected here for exactly the reason it is rejected for door 2u: it needs a field-level precedence
  rule that does not exist in this package. The loss is logged, not silent — the WARNING at
  `obsidian_schemas/repositories/person.py:create_stub:1431` already names the collision and the
  `created_by` value — and it is bounded to the fields of one stub rather than to a whole note. If
  Dave wants the losing create's fields merged, that is the same (a)-shaped decision as door 2u's
  merge and needs him to originate the precedence rule.
- **R8 — the snapshot registry is PROCESS-local (door 2 × the cooperating writer).** Added round 4
  with the placement mechanics. The stamp registry lives in the write primitive's module namespace,
  so two processes of the same consumer do not share it and a note loaded by process A carries no
  stamp in process B. That is the fail-safe direction, not a hole — an unstamped path is the zero
  case, so B's write is refused as a create rather than landing. The cost is a false refusal where B
  legitimately means to overwrite a note it never read; the named remedy is the explicit per-call
  `allow_unverified_overwrite` escape ruled in door 2c, and the registry never crosses a process
  boundary by design (a shared registry would be a second source of truth about the filesystem, and
  the filesystem is already the first).
- **R9 — `observe` mode delivers `## Intent` for Layer 1 only (all doors × both populations).** Added
  round 4 with the graduated-rollout ruling. A consumer that sets
  `OBSIDIAN_SCHEMAS_WRITE_GUARD=observe` keeps today's exact write semantics — including the
  concurrent-create clobber and the silent snapshot overwrite — and gets a WARNING naming the
  refusal that would have fired. Atomicity and mutual exclusion still apply, because neither has a
  ramp to justify. The mode exists so three consumer repos can measure the real collision rate
  before the refusals are load-bearing; while it is set, this item's Intent is explicitly **not**
  delivered for doors 2 and 3, and that is a declared residual rather than a configuration detail.
- **R10 — Wall A cannot see a `Path.replace` spelled on an unqualified receiver (all doors × a future
  in-package writer).** Added round 6 with the provenance ruling in D10. `replace` is the ONE
  `pathlib.Path` mutator whose attribute name collides with a method of a builtin type
  (`str.replace`), and this tree exercises the string side at nine lines / fourteen call nodes in
  files `## Scope Boundary` forbids the builder to touch. So `replace` is matched by **import
  provenance only** — `os.replace(a, b)` and `from os import replace as _r; _r(a, b)` are matched,
  and a bare `p.replace(q)` on a `Path` variable is **not**. What bounds it: D2 orders the door's own
  replace form as `os.replace(tmp, target)`; Wall B independently makes any `os` member outside
  `OS_READONLY_NAMES` red wherever it is named; and the sweep behind the ruling is total rather than
  anecdotal — every OTHER `Path` mutator (`write_text`, `write_bytes`, `mkdir`, `rmdir`, `unlink`,
  `rename`, `touch`, `symlink_to`, `hardlink_to`, `chmod`) is homonym-free and IS matched on
  attribute name alone. The alternative was priced and rejected in D10: putting `replace` in the
  name-matched arm is Wall A red on day one against fourteen live `str.replace` call nodes, with no
  `ensure_dir`-shaped move available because they are not filesystem calls at all. D10 ships
  `p.replace(q)` as a NAMED near-miss fixture pointing at this residual, so a later reader who tries
  to "fix" the gap meets the ruling rather than the fourteen reds.
- **R11 — Wall A is a wall over the two roots, not over the consumers (all doors × the three consumer
  repos).** Added round 6 for completeness of the (kind × population) grid. `PACKAGE_ROOT` and
  `SCRIPTS_ROOT` are the whole of the wall's universe; HAL9000, exocortex and orchestrator can name
  `Path.write_text` against the vault freely and nothing here detects it. That is R3 (advisory means
  advisory) wearing a cooperating-writer hat: the doors are available to them, not imposed on them.
  Their adoption is the close-out consumer audit, not a check this item can ship.
- **R12 — a door-1 write ages the stamp of a note whose cached entity is still current (door 1 × door
  2 × the cooperating writer).** Added round 7 with the D12.5 sweep. Door 1 deliberately does not
  touch the registry (D5), so `append_to_timeline(p, …)` followed by `repo.save(p)` in one process
  refuses with `StaleEntityWrite` even though only the BODY moved and the cached frontmatter is
  accurate. The stamp is whole-file, and at the stamp level a door-1 write to the body is
  indistinguishable from `update_frontmatter_field`'s write to the frontmatter — which is the case the
  refusal exists to catch (D5's re-run of the architect's note-#1 scenario). This item takes the
  fail-safe side knowingly. The remedy is the caller's, and it is the one already in the tree:
  re-read through the repository, which is why `_writeback_identifier` routes through `update_fields`
  (`obsidian_schemas/repositories/person.py:_writeback_identifier:1214`) — `update_fields` re-reads
  via `self._load_file(...)` at `obsidian_schemas/repositories/base.py:393` and re-registers. Making
  the six body writers re-register instead would advance a stamp for a payload nobody re-derived —
  LESSONS #43, the very shape D5's rule closes — so it is rejected rather than deferred.
- **R13 — the registry can be NEWER than a live cached entity (door 2 × the cooperating writer).**
  Added round 7 on the round-6 architect's note #1. D5's adoption sweep proves every `_cache` write
  has a matching stamp record; the converse does not hold, and the converse is the fail-OPEN
  direction. A direct exported `write_markdown_file(P, …, overwrite=True)` registers a stamp at D8
  step 8 that no `_cache` adopted, and two repository instances over one vault share the module-level
  registry while holding separate caches — in both, a later `save()` from the older cache compares
  equal and PASSES. No in-package caller does either today (the only `write_markdown_file` call sites
  under `obsidian_schemas/` are `base.py:save:321`, `book.py:save:163` and `meeting.py:save:185`, each
  adopting into its own `_cache` in the same call). Closing it would require the stamp to ride on the
  PAYLOAD rather than the path — a different frame from the one ruled here — so it is declared, and
  its shape is stated so a consumer that hits it recognises it.
- **R14 — inode replacement does not carry every inode-borne property across (all doors × both
  populations).** Added round 8 with the threat model's M1/M3 fold. Layer 1 swaps the inode where
  today's `Path.write_text` truncates in place, so properties that rode on the inode surviving stop
  riding for free. The full enumeration and the ruling on each cell is D2.1's table; three cells are
  CLOSED (permission bits are preserved, a symlinked write door resolves, a symlinked move door
  refuses, and a multiply-hard-linked target refuses) and the rest are this residual: **owner and
  group** (`os.chown` to another uid needs privilege this library never has; in practice the writer
  owns the vault), **extended attributes, macOS Finder tags and file flags** (editor and Finder
  metadata, not vault data; copying them is work no consumer has asked for and no code in this
  package does today), **ACLs** — and that cell is called out separately as of round 9, because the
  round-2 threat model is right that an ACL is not metadata: a macOS ACL
  (`com.apple.system.Security`) is an access-control decision, so dropping it on inode replacement
  widens access in exactly the direction M1 exists to narrow, silently, with the write reporting
  success. It is declared rather than mitigated on the modeler's own calibration — no note in an
  Obsidian vault normally carries one, and it explicitly does not require it — and the cheap answer
  if it is ever wanted is the shape D2.1 already chose for hard links, `os.listxattr(target)` naming
  the ACL xattr → refuse, never a copy — and **the inode number itself** (that IS the mechanism — a consumer keying on
  `st_ino` across a write sees a new value; none of the three consumer repos does so today). All are
  declared rather than attempted, and close-out step 3b is the sweep that would find a consumer
  depending on any of them.

### What this ruling was conditional on — DISCHARGED, and the conditions came back positive

**Rewritten round 4.** The three preceding rounds of this section said "not discharged by this
revision"; that is no longer true and leaving it would put the document back to contradicting
itself. All three obligations were run against the live vault in the conductor sitting recorded
verbatim at `## Spec-Writer Round — 2026-08-09` → `### DISCHARGED — 2026-08-09`. What each one
settled, and what Design is therefore entitled to assert:

- **Obligation 1 (filesystem under the vault) — POSITIVE.** `/dev/disk3s5 on /System/Volumes/Data
  (apfs, local, journaled, nobrowse, protect, root data)`. Local journaled APFS; no iCloud Drive,
  Dropbox, Syncthing or network mount. Dave confirmed Obsidian Sync is app-level (it writes through
  the Obsidian process — the non-cooperating writer this frame already models) and the planned
  backup system is read-only. **Layer 2 stands for all three doors and the four-way fork stays
  closed.** This Approach is no longer written on an assumption; the sentence that said it was is
  deleted rather than softened.
- **Obligation 2 (Obsidian's on-save behaviour) — NEGATIVE, and R1's clause (c) is restated on the
  observation.** Same inode `220735514`, size `5049 → 5085`, mtime advanced: in-place
  truncate-and-write, not a whole-file safe-write. R1 above carries the restated clause and no
  longer carries a marker. Design reproduces R1 verbatim from there.
- **Obligation 3 (dot-dir sentinel visibility) — NOT VISIBLE, with the evidence scope stated.** A
  probe at `<vault>/.obsidian-schemas-locks/probe.md` did not surface in Obsidian's quick-switcher
  filename search; full-text search and graph were not separately checked. **Decision: in-vault
  dot-directory sentinels stand**, and the fallback (sentinels homed outside the vault, keyed by
  path hash) is retained as the named successor, reachable without a code change via
  `OBSIDIAN_SCHEMAS_LOCK_DIR`. Design states the sentinel location on this observation and carries
  the scope limit with it rather than rounding it up to "Obsidian ignores dot-dirs".

**Dave's two standing reversal questions were answered in the same sitting, and both rulings were
CONFIRMED:** door 2c stays option (i) — an atomic no-clobber create raising `NoteAlreadyExists`,
which `create_stub` converts into its existing reuse branch — and Layer 2 stays **integrate
`filelock`** rather than a hand-rolled `_HELD` registry. Neither is open; each remains reversible by
Dave, and each reversal is now a change to a written decision with a named consumer-facing cost.

**What that leaves conditional: nothing in this ruling's shape, and exactly one thing in its build
environment.** `filelock` is a runtime dependency this package does not yet declare, and
`pyproject.toml` sits outside the caged builder's write authority (`pipeline-runners.yaml:34-38`
grants `obsidian_schemas/**`, `tests/**`, `scripts/**`, `docs/**` — the project root is excluded on
purpose). It is therefore a **conductor-committed precondition**, declared as a fence in
`## Write Targets` and gated by Task 1, which aborts the build in its first minute if the dependency
is not importable rather than discovering it as a red floor halfway through. That is a build-ordering
obligation, not a condition on the ruling.

`## Design` is written this round, below.

## Intent

**Restated 2026-08-09 (round 3) — the previous restatement was still false for the create path.**
Three write doors, defined by mutation shape rather than by a site list, with a routing wall derived
from the tree that turns an unrecognised mutation kind into a red build rather than the next
reviewer's finding. **Round 5 adds the other half of that sentence:** the observation side is
derived from the tree too — every function the loader corpus resolves to records the stamp its
payload derives from, and a new loader or a new entity-derivation site that records none is the same
red build, not the same next finding. Every door is atomic, so a crash can no longer tear a note. Every door's write
is preconditioned **at the write syscall, against the target itself**: on the read its bytes were
derived from, or — where they derive from no read of the target — on the target's non-existence,
enforced atomically. So a concurrent or external edit is either excluded (cooperating writers,
Layer 2) or **detected and loudly refused**, never silently destroyed, and a path with no recorded
derivation read fails closed rather than open. `save()` keeps its snapshot-overwrite meaning and
gains `StaleEntityWrite`; it does not gain merge semantics. A create that loses a race raises
`NoteAlreadyExists` at the door, which `PersonRepository.create_stub` converts into the
reuse-on-collision branch it already has — restoring cross-process the invariant its own comment
declares — and which the book and company stubs surface to the caller. What remains uncovered is
enumerated in the closed residual list in `## Approach` — chiefly the irreducible µs external
window, read staleness, and the losing create's non-identifier fields, which this item logs but does
not merge.

**One consequence added round 7, so this paragraph is not read as narrower than it is.** "A path with
no recorded derivation read fails closed" reaches consumers, not only repositories: a caller that
parses a note with the exported `parse_markdown_file` and writes it back with
`write_markdown_file(..., overwrite=True)` — the recipe at `README.md:317-338` — derives an entity
from bytes no wall here can observe, and is refused with `NoteAlreadyExists`. That is the fail-closed
direction working as intended rather than an oversight, it is ruled with its consumer face in
`## Design` D5, and the named answer is the per-call `allow_unverified_overwrite=True`, which still
runs the WI-126 body-shrink guard.

**One bound added round 8, so "every door is atomic" is not read as free of cost.** Atomicity is
obtained by replacing the note's INODE where today's `Path.write_text` truncates it in place, and
properties that rode on the inode surviving stop riding for free. This item does not let that change
anything silently: the permission bits are carried across (M1), a symlinked path is resolved once and
used everywhere so the real file receives the bytes and the link stays a link (M3), an existing
target with more than one hard link is REFUSED rather than silently divorced from its siblings, and
the remaining inode-borne properties — ownership, extended attributes and the inode number itself —
are enumerated and declared as R14 rather than left unmentioned. The enumeration and the ruling on
every cell are in `## Design` D2.1.

**One qualifier added round 4, so this paragraph is not false under the shipped configuration.**
Everything above describes the DEFAULT mode, `OBSIDIAN_SCHEMAS_WRITE_GUARD=enforce`. A consumer that
sets `observe` keeps today's exact semantics for doors 2 and 3 — including the concurrent-create
clobber and the silent snapshot overwrite — and gets a WARNING naming the refusal that would have
fired; only Layer 1's atomicity and Layer 2's mutual exclusion still hold, because neither has a
ramp to justify. That mode exists so three consumer repos can measure the real collision rate before
the refusals are load-bearing, and while it is set this Intent is delivered for atomicity only. It is
residual R9.

## Design

Written 2026-08-09 (round 4), the first round in which it could be: obligations 1–3 are discharged
(`## Approach` → "What this ruling was conditional on"), the architect's round-3 PROMOTE stands, and
its note #1 — the one it said the spec must resolve — is resolved in "The stamp registry" below.
Everything here implements the ruled frame; nothing here re-opens it.

### D0. Prerequisites & Assumptions

Stated explicitly; implicit assumptions are forbidden.

1. **`filelock` is importable by the interpreter that runs the floor.** The floor command is
   `.venv/bin/python -m pytest`, and the `.venv` is seeded into the build worktree
   (`pipeline-runners.yaml:18-19`). Two halves must both be in place BEFORE the drive is armed:
   `filelock>=3.12` declared in `pyproject.toml`'s `dependencies` (currently `pydantic>=2.0.0`,
   `pyyaml>=6.0` — `pyproject.toml:26-29`), and the package actually installed into that `.venv`.
   The caged builder can do neither: `pyproject.toml` is outside `write_authority`
   (`pipeline-runners.yaml:34-38`) and a `pip install` into `.venv` is likewise outside it and would
   be reverted at the merge boundary. **Atomic landing:** both halves land together, before the
   worktree is cut. Declared as a `kind: precondition` fence and gated by Task 1.
   *Honest limit of the fence:* the driver probes a declared precondition path for membership in git
   HEAD, and `pyproject.toml` is already in HEAD, so the probe passes whether or not the dependency
   line was added. Task 1's `import filelock` is therefore the real gate, and it is ordered first for
   that reason.
2. **The vault is on local journaled APFS** (obligation 1, observed). `flock`/`filelock` advisory
   semantics are sound. No filesystem-level sync agent sits above the vault; Obsidian Sync writes
   through the Obsidian process and is the already-modelled non-cooperating writer.
3. **Obsidian saves in place (truncate-and-write), not by replace-and-rename** (obligation 2,
   observed). R1's clause (c) is stated on this and Design reproduces R1 verbatim.
4. **Obsidian does not surface `<vault>/.obsidian-schemas-locks/` in filename search** (obligation 3,
   observed; full-text and graph not separately checked). Sentinels are in-vault dot-directories by
   default, with `OBSIDIAN_SCHEMAS_LOCK_DIR` as the named, code-change-free fallback.
5. **No service must be running.** This is a library change; HAL9000, exocortex and orchestrator are
   consumers, not dependencies. No credentials, no OAuth scopes, no network.
6. **WI-020 has landed** (`obsidian_schemas/errors.py` exists with `LoudFailError` and the `REASONS`
   frozenset). `depends_on: ["WI-020"]` in this doc's frontmatter is satisfied.
7. **Trust boundary.** The untrusted input crossing into this code is *the filesystem itself* —
   bytes another process or Obsidian wrote between our read and our write. There is no user-supplied
   string, no network payload and no deserialization of foreign data introduced by this item. The
   validation performed at that boundary is the stat precondition; the sanitization is that nothing
   read at the boundary is interpolated into any message (WI-020's `bounded_message` contract,
   `obsidian_schemas/errors.py:bounded_message:109`, which every new exception routes through by
   declaring no `__init__` of its own).

### D1. The new module and its single-homing contract

**New file: `obsidian_schemas/vault_io.py`.** It is the ONE file under `obsidian_schemas/` or
`scripts/` permitted to name a filesystem-mutation capability. This is the same self-rule
`tests/derivations.py` already applies to itself — its module docstring at `tests/derivations.py:14`
declares it "the only file under `obsidian_schemas/` or `tests/` permitted to name `ast`", and
`modules_using_ast` (`tests/derivations.py:528`) enforces it by scanning for the capability rather
than for known copies. The routing wall (D7) enforces the same shape here.

**Public surface** (everything else in the module is private):

```
NoteStamp            frozen dataclass: mtime_ns: int, size: int, exists: bool
note_lock(path)      context manager — Layer 2. Reentrant in-process, exclusive cross-process.
read_note(path)      -> tuple[str, NoteStamp]. Requires the lock. Stats BEFORE reading.
write_note(path, text, *, precondition: NoteStamp)   -> Path.  Layers 3 + 1.
create_note(path, text)                              -> Path.  The zero case: atomic no-clobber.
move_note(src, dest)                                 -> Path.  Door 3.
ensure_dir(path)      -> Path                        The namespace cell (R5): mkdir(parents, exist_ok).
stat_stamp(path)      -> NoteStamp                   Pure observation. Does NOT touch the registry.
remember_snapshot(path, stamp) -> None               Commits an already-taken stamp to the registry.
record_snapshot(path) -> NoteStamp                   stat_stamp + remember_snapshot, for post-write use.
snapshot_stamp(path)  -> NoteStamp | None            Door 2 reads this.
forget_snapshot(path) -> None
clear_snapshots()     -> None                        Test hygiene only.
guard_mode()          -> "enforce" | "observe"       Reads config each call (D6).
```

**`stat_stamp` and `remember_snapshot` are two functions rather than one because the observation
points must stat BEFORE they read and record AFTER they know an entity was derived** (D5). A single
`record_snapshot(path)` stats at call time, which is the correct shape only for the post-write case
in D8 step 8, where the bytes on disk are the ones this process just committed. Every read-side
observation point takes `stamp = stat_stamp(p)` first and calls `remember_snapshot(p, stamp)` last;
`record_snapshot` is the composition, kept for the write side.

**`ensure_dir(path)` carries no precondition and no lock** — it is `mkdir(parents=True,
exist_ok=True)`, idempotent, with no loss mode (R5). It lives here for one reason: this module is the
only place under `obsidian_schemas/` or `scripts/` permitted to NAME a filesystem-mutation
capability, and `mkdir` is one (Wall A, D10).

**Two properties of the public surface that no signature above shows, added round 8 because Layer 1
changes the mechanism that used to supply them for free, and SHARPENED round 9 because the round-2
threat model moved what each one requires (M1, M3).** Neither is a new function and
neither changes a signature; both are contract clauses on every door, and D2 is where they are
specified and D10's vocabulary already admits them without a change:

1. **A note written through any door keeps the mode it had, and its content never exists on disk at a
   wider mode than the target's — not even for the span of the write and the `fsync`.** Today
   `obsidian_schemas/writer.py:236`
   is `file_path.write_text(content, encoding="utf-8")`, which opens `"w"` and truncates in place, so
   the inode — and therefore `st_mode` — survives every write in the package. Layer 1 swaps the inode,
   so the mode would otherwise come from however the temp file was created. D2.2 carries it across
   onto the temp file's OWN DESCRIPTOR **before the first byte of the note is written to it**, so the
   preserved mode and the no-wider-window property are one mechanism rather than two;
   `write_note`, `create_note` and `move_note` all inherit that clause, and the caller
   never passes a mode.
2. **Every door resolves its path exactly ONCE and uses that one value everywhere — including the
   HOME of its lock sentinel, not only the sentinel's key.** `note_lock`'s sentinel directory and
   sentinel hash, the registry (D5), the temp file's directory, the precondition stat and the
   terminal syscall all
   key on the same resolved path, so a symlinked note cannot be locked and stamped under one identity
   and committed under another, and two paths naming ONE real note cannot place their sentinels in two
   directories and both acquire. `move_note` is the one door where resolution alone is not an answer,
   and it refuses instead (D2).

Both are behaviour this item newly INTRODUCES rather than inherits, which is why they are written
rather than assumed: `grep -rn 'chmod\|st_mode\|umask\|is_symlink\|st_nlink' obsidian_schemas/
scripts/` returns **zero** hits against this tree (run 2026-08-09), so there is no existing handling
for either to defer to.

**`read_note`'s error contract, stated rather than left incidental (round 7, the round-6 architect's
note #2).** `read_note(path)` wraps NOTHING: a missing path raises `FileNotFoundError`, and an
`OSError` or a `UnicodeDecodeError` from the read propagates **unwrapped, with no `raise … from`**.
That is not a convenience — it is what keeps a routed door-1 site's own `except` clause seeing the
same exception class it sees today, and WI-020's chain contract is written on exactly that. At
`tests/test_loud_fail_parse.py:test_error_chains_are_bounded:412` part 4 (`:462-471`) an undecodable
note must reach `update_frontmatter_field`'s `except Exception as e` as a `UnicodeDecodeError`, so
that `chainable_cause` returns `None` and the note-derived bytes never reach `__cause__`; part 3
(`:440-457`) needs the mirror-image outcome for an `OSError`. Had `read_note` wrapped either into a
`LoudFailError`, the site's `except LoudFailError: raise` arm would fire first and both halves of
that contract would change silently. `write_note`, `create_note` and `move_note` are the opposite:
they are the package's own refusal surface and every failure on them is a `LoudFailError` subclass
(D4), chained through `chainable_cause`.

**`NoteStamp`** is a frozen dataclass with exactly `mtime_ns: int`, `size: int`, `exists: bool`.
`exists=False` carries `mtime_ns=0, size=0`. Equality is field equality. It is minted ONLY by
`read_note` and `record_snapshot`; callers cannot construct a passing stamp out of nothing, which is
what makes "a caller structurally cannot write from a stale snapshot" a property of the type rather
than of caller discipline.

**No function in `vault_io.py` that RETURNS A VALUE A CALLER ACTS ON returns a falsy one.** Every
failure on those paths raises. This is WI-020's own contract, and round 6 gives it an oracle it did
not have.

**Corrected round 8 on the round-7 architect's note #3 — the RULE is restated to match its set,
never the set narrowed to match the rule.** The previous sentence said "COMMITS BYTES", while
`COMMIT_FUNCTION_NAMES` also carries `read_note`, `stat_stamp`, `record_snapshot` and `ensure_dir` —
none of which commits bytes, and the last of which mints no stamp either — so Wall E's failure
message quoted a rule its own set was wider than. The set is right and the sentence was wrong:
`ensure_dir` returns the directory a caller then writes into, and `read_note`/`stat_stamp` return the
payload and the precondition a caller then commits on, so a falsy return from any of them is the same
silent-noop class as a falsy return from `write_note`. The set is the module's **path-, payload- and
stamp-returning surface**. Narrowing the set instead — dropping `ensure_dir` to make the old sentence
true — is the wall narrowing its own reach (D10.3's rule at a different wall) and is rejected.

**Corrected round 6 — the previous sentence named the wrong enforcer, and the claim it made was
vacuous.** It said the rule is enforced because `non_completed_write_sites`
(`tests/derivations.py:non_completed_write_sites:484`) "scans every function under `PACKAGE_ROOT`
that contains a commit call". That scan's universe gate is `_is_write_call`
(`tests/derivations.py:507`), which matches `write_text`/`write_bytes` (and, after this item,
`DOOR_NAMES`). D2 commits through a file descriptor — `f.write`, `f.flush`, `os.fsync(fd)`,
`os.replace`, `os.link` — so **no `vault_io` function enters that universe at all**, and the stated
build constraint checked nothing. That is the same class as the walls: a claim asserted against a
predicate that cannot see its subject. The rule is real and worth keeping, so it gets its own
enforcer rather than a softer sentence:

> **Wall E (D10): `falsy_returns_in(python_files_under(PACKAGE_ROOT), COMMIT_FUNCTION_NAMES)` is
> empty** — no explicit falsy `return` in the own body of `write_note`, `create_note`, `move_note`,
> `read_note`, `stat_stamp`, `record_snapshot` or `ensure_dir`.

`falsy_returns_in` shares `_own_body_nodes` and `_is_falsy_return` with `non_completed_write_sites`
— one rule over two universes, not a second copy. (An implicit fall-off-the-end is not an
`ast.Return` node and is invisible to either; an explicit `return`/`return None`/`return False` is
not, which is exactly the shape the rule forbids.)

The scope of that rule is exactly that path-, payload- and stamp-returning surface, and the
exclusions are deliberate rather than overlooked: `snapshot_stamp` returns `None` for an unregistered
path — the ZERO CASE the
whole precondition rule is built on, and the strictest outcome rather than the loosest (D4, D8 step
5) — and `remember_snapshot`, `forget_snapshot`, `clear_snapshots` and `guard_mode` are procedures
or pure lookups. None of them is in `COMMIT_FUNCTION_NAMES`, which is why that set is written out
rather than derived from "everything public".

**And `vault_io.py`'s effect on WI-020's four existing sweeps is derived, not assumed** — it is a new
file under `PACKAGE_ROOT`, so it joins the file set of every sweep that walks `python_files_under`.
It calls no `parse_frontmatter`, so it enters neither `functions_parsing_then_writing` nor
`functions_reserializing_parsed_frontmatter`; it declares no `BaseRepository` subclass, so the `== 4`
pin at `tests/test_loud_fail_parse.py:300` is untouched; it reaches neither `SEAM_NAMES` member, so
`seam_invocation_closure` gains no member and the residue name-set at
`tests/test_loud_fail_parse.py:332` is unchanged; it contains no `write_text`/`write_bytes`/door call
(D2 commits through an fd), so it contributes nothing to `non_completed_write_sites`; and Task 3
forbids it to import `ast`, so `modules_using_ast` stays single-homed. Task 0 and Task 11 print each
of these rather than trusting this paragraph.

### D2. Layer 1 — atomicity

Every commit is: create a temp file **in the resolved target's own directory** (never a temp dir —
WI-065's own M1 rule, not this document's; `os.replace` must not cross devices and a temp location
outside the tree confuses sync agents), **carry the mode across onto that descriptor while the file is
still empty**, write the bytes, `flush`, `os.fsync(fd)`, close, then link or replace into position,
then `os.fsync` the parent directory so the
directory entry is durable. **The mode step moved ahead of the write in round 9 and that ORDER is the
whole of M1** — see D2.2. The temp file is named `.<target-name>.<pid>.<counter>.tmp` —
dot-prefixed so a crash leaves nothing Obsidian indexes — and is `os.unlink`-ed in a `finally` on
every failure path.

Two terminal forms, and the choice between them IS the rule from `## Approach`:

- **Replace form** (`os.replace(tmp, target)`) — used when a derivation read exists. Atomic
  same-directory rename; the reader of `target` sees either all old bytes or all new bytes, never a
  truncated file.
- **No-clobber form** (`os.link(tmp, target)` then `os.unlink(tmp)`) — used when there is no
  derivation read. `os.link` fails with `FileExistsError` if the destination exists, and that
  failure is a **kernel guarantee, not a check**, which is what makes doors 2c and 3 free of the
  check-then-mutate gap the generator-B table names.

`os.link` raising `OSError` with `errno == EXDEV` means the temp file and the target are on
different devices, which contradicts the same-directory rule and is a bug rather than a runtime
condition: it raises `WriteFailedError`. `os.replace` never crosses devices for the same reason.

#### D2.1 What inode replacement stops supplying for free — the generator behind M1 and M3

**Named rather than instanced, because both threat-model findings have ONE generator and closing the
two of them is not the fold.** The threat modeler states it in its own "why these are mitigations"
paragraph and it is exactly right:

> **Layer 1 changes the mechanism of committing bytes from truncate-in-place to inode replacement,
> and every property of a note that rode on the INODE surviving stops riding for free.**

`obsidian_schemas/writer.py:236` is `file_path.write_text(content, encoding="utf-8")` — `"w"`,
truncate in place, same inode — and the same is true of all fourteen `Path.write_text` sites
(`## Verified Diagnosis` claim 1). `os.replace(tmp, target)` and `os.link(tmp, target)` both put a
DIFFERENT inode at the path. So the correct fold is not "handle the mode, handle the symlink": it is
to enumerate the inode-borne properties of a vault note and rule EVERY cell, then declare what the
level above returned. The enumeration, and the ruling on each:

| Inode-borne property | Ruling |
|---|---|
| **Permission bits (`st_mode & 0o7777`)** | **Preserved (M1).** Specified below. |
| **The identity of the file a symlinked path names** | **Preserved for the write doors, refused for the move door (M3).** Specified below. |
| **Hard links (`st_nlink > 1`)** | **Refused.** A replace gives the other links the OLD bytes while today's truncate-in-place updates all of them — a silent divergence with no correct answer this package can pick. Every door therefore raises `WriteFailedError` when the resolved target EXISTS and its in-lock `os.stat` reports `st_nlink > 1`; a target that does not exist has no links to diverge, so `create_note`'s ordinary path is unaffected and the check costs the stat the precondition already takes. This is the third member of the same class; closing only the two the threat model named would have left it as the next round's finding. |
| **Owner and group (`st_uid`, `st_gid`)** | **Not preserved, and not preservable.** `os.chown` to another uid needs privilege this library never has. In practice the writer is the vault's owner and the property is unchanged; where it is not, the replace lands owned by the writing process. Declared as **R14**, not attempted. |
| **Extended attributes, macOS Finder tags, file flags** | **Not preserved.** Copying them is work no consumer has asked for and no code in this package does today; a note's xattrs are editor and Finder metadata, not vault data. Declared as **R14**. |
| **ACLs** | **Not preserved — and separated from the row above round 9, because an ACL is NOT metadata.** A macOS ACL (`com.apple.system.Security`) is an access-control decision, so dropping it on inode replacement widens access in the direction M1 exists to narrow, silently and with the write reporting success. Declared as **R14** rather than mitigated, on the round-2 threat model's own calibration (it does not require it: no note in an Obsidian vault normally carries an ACL, and a theoretical threat with no realistic path here is not a blocker). If it is ever wanted, the answer is this table's hard-link shape — `os.listxattr(target)` naming the ACL xattr → refuse — never a copy. |
| **The inode number itself** | **Not preserved — that IS the mechanism.** A consumer keying on `st_ino` across a write sees a new value. Declared as **R14**; nothing in this package or its three consumers does so today. |
| **mtime / atime / ctime** | **No loss.** A write moves them under either mechanism; Layer 3's precondition is built on that movement rather than harmed by it. |

**The next level of the ladder, swept and DECLARED rather than left for round 9.** Above
"properties of the target inode" sits *properties of the target's DIRECTORY ENTRY and of the
directory itself*, since the commit is a rename into a directory rather than a write through a
handle. Swept: (i) the parent directory's own mode and ownership are untouched — the door creates no
directory except through `ensure_dir`, whose `mkdir(parents=True, exist_ok=True)` is a no-op on an
existing tree; (ii) the target's NAME and case are untouched, because the terminal syscall names the
resolved target rather than re-deriving a filename (which matters on the case-insensitive APFS
checkout, `docs/backlog-campaign-2026-07-05.md:97`); (iii) directory-entry ORDER is not a property
POSIX offers, and `PersonRepository.load` globs `@*.md`
(`obsidian_schemas/repositories/base.py:load:186`) rather than depending on it; (iv) the temp file is
a new entry in the same directory for the span of one commit, which is the one observable this fold
does add, and it is bounded by the dot-prefix (D0.4's obligation-3 observation) and by the `finally`
unlink. Nothing in that level needs a rule; it is declared so that the absence of one is a finding
rather than a gap.

#### D2.2 M1 — the mode, carried onto the descriptor BEFORE the first byte

**Revised round 9 after the round-2 threat model moved M1's `desc`.** The previous text carried the
mode across with `os.chmod(tmp, mode)` "before the replace", which the design implemented literally
and correctly — and which leaves a file holding the note's COMPLETE content sitting at the
umask-derived create mode for the whole span of the write and the `fsync`. M1's justification is
**confidentiality** (person notes carry emails, phones and PII), and a reader of that temp file is
excluded by neither the write lock, nor the dot prefix, nor the unique name — all three of which are
**integrity** arguments. The requirement is therefore an ORDERING, and the fix deletes a call rather
than adding one. The rule, in one sentence:

> **Inside the lock, the door stats the resolved target for its mode BEFORE it opens the temp file,
> creates that temp file at the narrowest mode with an explicit-mode `os.open` (never
> `tempfile.mkstemp`'s `0600` as a committed mode and never a bare umask-wide `open(tmp, "w")`),
> applies the target's `st_mode & 0o7777` to the temp file's OWN DESCRIPTOR with `os.fchmod(fd, mode)`
> as the first operation on it and before a single note byte is written to it, and never chmods
> anything after the write — so the committed note keeps the mode it had AND its content never exists
> on disk at a wider mode than the target's, not even for the span of the write and the `fsync`.**

In order, inside the lock, on the resolved target:

1. **If the resolved target exists**, `st = os.stat(target)`: refuse with `WriteFailedError` when
   `st.st_nlink > 1` (D2.1's third cell), and take `mode = st.st_mode & 0o7777`. If it does not
   exist, `mode` is `None`.
2. **Create the temp file at the NARROWEST mode** —
   `fd = os.open(tmp, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)` when `mode is not None` — so the
   file is never, at any instant, wider than the target it will replace. It is empty at this point.
3. **Apply the target's mode to that descriptor as the FIRST operation on it** —
   `os.fchmod(fd, mode)` — **before any note byte is written**. `os.fchmod` rather than
   `os.chmod(tmp, …)` because the subject is the descriptor this door owns, not a path another
   process could have swapped underneath it in the interval.
4. **Then** write the bytes, `flush`, `os.fsync(fd)`, close, and take a terminal form. There is no
   later `os.chmod` — the round-8 call after the write is **deleted**, not supplemented.

**For a create (no existing target) there is no mode to preserve and step 3 does not run**: the temp
file is opened `os.open(tmp, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o666)`, whose umask masking gives
exactly the mode `Path.write_text` gives a fresh file today. Nothing is widened, because nothing
existed.

Four things that sequence decides, each deliberately:

- **Why `0o600` at create and `os.fchmod` after, rather than passing `mode` straight to `os.open`.**
  `os.open`'s mode argument is masked by the process umask, so it can only NARROW: a target at `0o666`
  under umask `0o022` would be created at `0o644`, and the door would commit at a mode nobody chose
  while believing it preserved one. `os.fchmod` is not umask-masked, so it is the only form that
  reproduces the target's bits exactly in both directions. Creating at `0o600` first means the
  strictest possible starting point, and the file is empty until step 3 has run. **This is not
  "mkstemp's `0600`"**, which M1's `desc` forbids: `0o600` here is the transient mode of an EMPTY
  file, and the committed note's mode is always `mode` (existing target) or the umask-derived
  `0o666 & ~umask` (create).
- **`tempfile.mkstemp` is NOT the temp-file mechanism.** It creates at `0600` and gives back no
  hook to correct it before the payload lands, so every note in the
  vault would silently narrow and a read-only backup reader — the discharge of obligation 1 records
  that the planned backup system is read-only — would lose access. A plain `open(tmp, "w")` is the
  opposite error: it takes the process umask unconditionally, so a note deliberately left at `0600`
  silently widens, and person notes carry emails, phones and PII. The explicit-mode `os.open` plus
  `os.fchmod` is the
  only form that is wrong in neither direction and wrong at no instant. D10.5's MATCHED fixture list keeps `tempfile.mkstemp()` and
  `tempfile.NamedTemporaryFile()` as planted shapes the predicate must resolve; that is a claim about
  the wall's reach, not about what `vault_io.py` calls, and Wall C's "`tempfile` is imported by
  `vault_io.py` only" stays true whether or not it imports it.
- **What the dot-prefix, the unique name and the lock DO buy, stated so the round-8 argument is not
  read as still load-bearing.** They exclude another WRITER from the temp file, which is why a crash
  leaves nothing Obsidian indexes and why two concurrent doors cannot collide on one temp name. They
  do NOT exclude a READER — any process that can list the note's directory can `open()` a
  world-readable temp file — and M1 is a confidentiality requirement, so the no-window property has to
  come from the ordering above and from nothing else.
- **No vocabulary or wall change is needed, and this is derived rather than hoped.** `os.fchmod`,
  `os.stat` and `os.open` are `os` members, and Wall B polices `os` at MEMBER granularity while
  excluding `vault_io.py` (D10.3) — so each is red anywhere else with no vocabulary at all, which is
  Wall B's own stated reason for existing ("a name no vocabulary ever anticipated"), and legal
  exactly where it is. None of the three is added to `OS_READONLY_NAMES`, and `chmod` stays in
  `PATH_MUTATION_NAMES` (D10.1) unchanged — nothing is removed from a vocabulary here, which is the
  move D10.3 forbids. Table 1 and Table 2 are
  unaffected: `fchmod` is in neither `MODULE_MUTATION_NAMES` nor `PATH_MUTATION_NAMES`, so Wall A's
  result set does not change shape, and every added call lives in the one file Wall B excludes.
  **Task 3 therefore still edits no vocabulary and no wall.**
- **The ONE honest exception to "keeps the exact `st_mode` bits it had", named rather than left
  implicit (round 10, the round-3 threat model's non-blocking note 2).** `st_mode & 0o7777` carries
  the setuid, setgid and sticky triad as well as the nine permission bits, and POSIX clears
  `S_ISUID`/`S_ISGID` on a write by an unprivileged process to a file that carries them. Under the
  ordering above — `fchmod` FIRST, then the bytes — a target that had `S_ISUID` or `S_ISGID` set can
  therefore commit without it, where a chmod-AFTER-write would have re-applied it. The direction is
  NARROWING (a privilege bit is dropped, never granted), no markdown note in this vault carries those
  bits, and AC-15 exercises `0o600`/`0o644` so its assertions cannot see it. It is recorded here and
  in `## Verification` so the phrase "keeps the exact `st_mode` bits it had" is read with its one
  exception rather than as an unqualified promise; the threat model does not require closing it, and
  re-ordering the `chmod` to close it would re-open the confidentiality window M1 exists for — which
  is why the trade is named rather than taken.

#### D2.3 M3 — one resolved path per door

Every door resolves its path exactly once at entry — `target = Path(path).resolve()` — and every
later step of that call uses that one value: the lock's sentinel HASH **and its sentinel DIRECTORY
`target.parent/.obsidian-schemas-locks/`**, the in-process lock key, the stamp-registry key, the temp file's
directory `target.parent`, the `stat_stamp` precondition and the terminal `os.replace`/`os.link`
argument, so no door ever mixes a resolved path with an unresolved one; `move_note` resolves `src`
and `dest` the same way and additionally refuses with `WriteFailedError` when `Path(src).is_symlink()`,
because a whole-file move through a symlink has no single correct meaning.

**The sentinel's HOME is in that list as of round 9, and its absence was the whole of the round-2
threat model's second finding.** Round 8's rule reached the lock's KEY; D3's sentinel path is
`<note's directory>/.obsidian-schemas-locks/<h>.lock`, and only `<h>` was stated as derived from
`str(path.resolve())`. Two processes reaching one real note through different parents — a symlink in
directory A, the real file in directory B — therefore computed the SAME hash and placed it in TWO
directories, took two different sentinels, and both proceeded. That is verbatim the failure M2's own
paragraph names as unacceptable ("key two writers' sentinels in different directories and evaporate
Layer 2's mutual exclusion with no sound"), arrived at from the other direction. Deriving the
directory from `target.parent` — the same sentence this section already writes for the temp file —
closes it, and under `OBSIDIAN_SCHEMAS_LOCK_DIR` the question does not arise at all because there is
one configured home for every note in the process.

- **Why resolve rather than refuse, for the write doors.** Today `Path.write_text` follows the link
  and updates the real file. Resolving reproduces that exactly, and it is the only choice that keeps
  the lock (`hashlib.sha256(str(path.resolve())…)`, D3) and the registry (`str(Path(p).resolve())`,
  D5) — both already resolved before this round — pointing at the same file the commit lands on. The
  defect the threat model found is precisely the half-resolved/half-unresolved SPLIT, and the fix is
  to make the resolved value the only one in the frame, not to add a second refusal.
- **Why refuse, for `move_note`.** A move of a symlink has two defensible meanings — relocate the
  link, or relocate its target — and door 3's only caller is
  `scripts/lint_vault.py:quarantine_garbage:1036-1038`, which quarantines garbage notes. Refusing is
  loud, costs nothing (the `NoteAlreadyExists` arm already `continue`s the loop; a `WriteFailedError`
  there is the fix loop's existing per-file `try` at `scripts/lint_vault.py:896-897`), and leaves the
  choice to whoever first needs it. This is the unenumerated case failing LOUD rather than being
  absorbed by the nearest-looking rule.
- **`resolve()` is non-strict**, so `create_note`'s not-yet-existing leaf resolves against its
  resolved parent and the create still keys on one value. A resolved parent that does not exist is
  created by `ensure_dir` (D8's flow, `writer.py:233` → `vault_io.ensure_dir`), unchanged.
- **The stamp minted by `stat_stamp` and the stamp checked at the door are the same file** under this
  rule, which is what makes D4's `current != precondition` comparison meaningful for a symlinked
  note. Before it, the two could differ by construction.

### D3. Layer 2 — locking

`note_lock(path)` is a context manager acquiring, in this order:

1. A per-path `threading.RLock` from a module-level `dict[str, RLock]` guarded by its own module
   `RLock`. This gives in-process thread exclusion **and** reentrancy for the same thread — the role
   the WI-065 `_HELD` depth registry played, obtained from the standard library.
2. A per-path `filelock.FileLock(sentinel, timeout=T, thread_local=False)` from a module-level
   `dict[str, FileLock]`, one instance per resolved path. `thread_local=False` is load-bearing:
   `filelock`'s default thread-local acquisition counter would let two threads sharing one instance
   each believe they hold a lock that the OS grants per-file-descriptor and therefore per-process.
   Step 1 already guarantees only one thread is inside, so the process-wide counter is the correct
   one.

**Sentinel location** (obligation 3), **with BOTH halves derived from the one resolved path as of
round 9 (M3)**: `target.parent / ".obsidian-schemas-locks" / f"{h}.lock"`, where
`target = Path(path).resolve()` and
`h = hashlib.sha256(str(target).encode("utf-8")).hexdigest()[:32]`. The directory is
`target.parent` — the RESOLVED note's own directory, never the caller's unresolved one — and the
hash is over that same `str(target)`, so two paths naming one real note compute one sentinel in one
directory and Layer 2 excludes them. Round 5's text said `<note's directory>` and left which
directory unstated, which is what let a symlink in directory A and the real file in directory B key
the same hash into two homes (D2.3). Hashed rather than
name-derived because the checkout volume is case-insensitive APFS
(`docs/backlog-campaign-2026-07-05.md:97`) and note names contain spaces and punctuation; the
directory is created by `ensure_dir` (D1), which is the one cell where "no precondition" is a ruled
decision (R5). Overridden wholesale by `OBSIDIAN_SCHEMAS_LOCK_DIR` (an
absolute path), which is the observed-fallback escape from obligation 3 — the same hash keying, one
home for every note in the process (so the two-directory question cannot arise there at all), no code
change.

**And that override is VALIDATED, which is M2 (round 8).** `OBSIDIAN_SCHEMAS_LOCK_DIR` is validated
at first lock acquisition exactly as the other two settings are — it must be a non-empty absolute
path naming a usable directory (created with `ensure_dir` if absent), and a relative, empty or
unusable value raises `WriteFailedError` rather than being resolved against the process CWD, which
would key two writers' sentinels in different directories and evaporate Layer 2's mutual exclusion
with no sound. Concretely the three refusals are: `value == ""` (LESSONS #5 — empty is a bug shape at
a precondition, which is the same ruling Edge Cases makes for a falsy path); `not
Path(value).is_absolute()`; and an `OSError` from `ensure_dir(value)` or a resolved value that exists
and is not a directory. All three carry reason `"write did not complete"`
(`obsidian_schemas/errors.py:REASONS:96`), so no new literal is minted — the same argument the
timeout path already makes below. This is the mutual-exclusion hole the threat model's non-blocking
note 2 points at: it is what stops a sentinel home outside the vault from being a silent hole rather
than a loud refusal.

**Timeout** `T` defaults to `10.0` seconds, overridden by `OBSIDIAN_SCHEMAS_LOCK_TIMEOUT` (a float,
valid range `> 0`; a non-positive or unparseable value raises `WriteFailedError` at first
acquisition rather than being silently coerced). On timeout: `WriteFailedError` with reason
`"write did not complete"` — an existing `REASONS` member, so no new literal is needed for this path.

**`write_note`, `create_note` and `move_note` each refuse when the lock for their path is not held
by this process**, raising `WriteFailedError`. The check is membership in the module's held-depth
map, not a `flock` probe. This is what makes step-skipping loud instead of racy.

**Deadlock:** `move_note` acquires `src` and `dest` in sorted order of their resolved POSIX strings.
A global total order over the only multi-path door is sufficient; no other door takes two locks.

### D4. Layer 3 and the total precondition rule

`write_note(path, text, precondition=stamp)`:

```
assert lock held for path                      -> else WriteFailedError
current = stat_stamp(path)                     # inside the lock
if current != precondition:                    -> ExternalWriteConflict   (door 1)
                                               -> StaleEntityWrite        (door 2u)
atomic replace                                 # D2 replace form
record_snapshot-equivalent update for door 2   # see D5
```

Which exception fires is decided by **where the precondition came from**, not by inspecting the
mismatch: `write_note` takes an `origin: Literal["content", "entity"]` keyword (defaulted to
`"content"`) and raises `ExternalWriteConflict` for `"content"`, `StaleEntityWrite` for `"entity"`.
Both are `LoudFailError` subclasses, so `except LoudFailError` catches "this package refused"; both
are distinguishable from `WriteFailedError` so a caller may retry a conflict without retrying a
genuine IO failure.

`create_note(path, text)` is the zero case: no precondition argument exists, the terminal form is
the no-clobber link, and `FileExistsError` from the kernel becomes `NoteAlreadyExists`.

**A stamp whose target no longer exists is a mismatch, not a create.** `current.exists is False`
while `precondition.exists is True` raises `StaleEntityWrite`/`ExternalWriteConflict` as above. The
note was deleted under us; silently resurrecting it from a stale snapshot is the same loss class
this item exists to kill, in the other direction.

### D5. The stamp registry — and the architect's note #1, resolved

The registry is `_SNAPSHOT_STAMPS: dict[str, NoteStamp]`, keyed by `str(Path(p).resolve())`, module-
level in `vault_io.py`, guarded by an `RLock`. It is path-keyed and owned by the write primitive
rather than by the repository, exactly as `## Approach` rules — `write_markdown_file` is the only
choke point that sees both the entity and the path, and it is exported public API
(`obsidian_schemas/__init__.py:42,115`), so a registry hung on the repository would be invisible to
consumers that bypass repositories entirely.

**The round-3 architect's note #1 is that a single path-keyed registry serving two purposes re-opens
a silent lost update:** a process loads note P (stamp `S0`), calls the exported
`update_frontmatter_field` on P (door 1 writes, and under the previous text's "property 3" that
write advances the registry to `S1`), then calls `repo.save(cached_entity)` — the stamp check
compares `S1` to `S1`, passes, and `obsidian_schemas/writer.py:217-218` rebuilds the frontmatter
from the pre-`S1` snapshot. That is LESSONS #43 exactly: two independently-correct guards reading
one field for different purposes.

**Resolution: the architect's first option — key the stamp to the PAYLOAD's derivation, not to the
last write.** Concretely, and this is the whole of the rule:

> **The registry records a stamp at exactly the points where an ENTITY is derived from a file's
> bytes, and nowhere else. A door-1 write does not touch it.**

The observation points are therefore two **classes**, not two names: every point where an entity is
derived from a file's bytes, and a successful **door-2** write, which registers the stamp of the
bytes it just committed. Door 1 has no registry involvement at all — its precondition is
call-local (`read_note` mints the stamp, `write_note` consumes it, both inside one lock and one call
frame), so there is nothing for it to record and nothing of the entity door's for it to overwrite.

#### The derivation corpus is DERIVED, not named (round-5 ruling)

**The defect the round-4 gates found, and it is generator A one level down.** The previous text named
the first class as one function — `BaseRepository._load_file` — and Task 7 ordered the recording
added there and nowhere else. That is false against this tree, and the tree says so in the module
this document elsewhere relies on:
`tests/derivations.py:load_file_implementations:355` documents the corpus as *"MANY-TO-ONE: four
classes resolve to three functions today"*, and `tests/test_loud_fail_parse.py:301` pins it at 3.
`obsidian_schemas/repositories/book.py:_load_file:57` (`:57-81`) and
`obsidian_schemas/repositories/meeting.py:_load_file:64` (`:64-85`) are complete overrides that never
call `super()._load_file`; each parses and returns `doc.entity` itself (`book.py:76`,
`meeting.py:80`). `obsidian_schemas/repositories/base.py:load:187` calls `self._load_file(file_path)`
— dynamic dispatch — so a book or meeting loaded from the vault would never reach `base.py:226`, its
`snapshot_stamp` would be `None`, D8 step 5's zero case would fire, and the ordinary in-process
`BookRepository.save` / `MeetingRepository.save` (`book.py:163`, `meeting.py:185`, both calling
`write_markdown_file` directly) would raise `NoteAlreadyExists` in the default mode. The enforcement
side was made total by derivation (D8's placement ruling); the observation side was written as a
list. **Deriving it is what closes the class** — closing the two loaders in front of us is not the
fold, because the fifth repository is the next round's finding.

**Ruling: closure (A′) — record inside every loader, with the loader corpus derived from the tree
and the recording obligation ENFORCED over that derived corpus (Wall D, D10).** Concretely:

> **Every function in `load_file_implementations(base_repository_subclasses(python_files_under(
> PACKAGE_ROOT)))` stats before it reads and records on its entity-returning branch, and the set of
> functions under `PACKAGE_ROOT`/`SCRIPTS_ROOT` that call `parse_markdown_file` is exactly that same
> set.**

The first half makes a loader that forgets to record a RED floor rather than a silent stamp loss on a
new entity type. The second half is the level above it: it makes an entity derivation that happens
*outside* the loader corpus — a script, a helper, a consumer-facing convenience — a RED floor
demanding a ruling, rather than the next gate's next finding. Both halves consume derivations the
tree already carries; neither re-implements one.

#### The cell Wall D(ii) cannot reach: a CONSUMER's own derivation (round-7 ruling)

**What the round-6 data-premise gate found, and it is a limit of the wall rather than a gap in it.**
Wall D(ii)'s universe is `python_files_under(PACKAGE_ROOT, SCRIPTS_ROOT)`. `parse_markdown_file` is
exported public API (`obsidian_schemas/__init__.py:37,111`), so a consumer that parses a note itself
and writes it back derives an entity from bytes the registry never observed — **by construction,
outside every wall this item ships** (R11's face on the read side). That is not hypothetical: it is
the recipe this package documents. `README.md:317-338`, "Round-Trip Preservation", is
`parse_markdown_file` → mutate → `write_markdown_file(..., overwrite=True)`, and the suite exercises
it verbatim at `tests/test_writer.py:test_roundtrip_preserves_data:287` (`:314` raw seed, `:317`
parse, `:322` write-back).

**Ruling: the cell is a KNOWING, declared break, and the documented consumer answer is
`allow_unverified_overwrite=True`.** Under D8 step 5 that call raises `NoteAlreadyExists`, because
`snapshot_stamp` is `None` and an unstamped path is the zero case. The two alternatives are rejected
in writing:

- **Make the exported parser an observation point** (record in `parse_markdown_file`, restating Wall
  D(ii)'s equality over the wider corpus). **Rejected — it re-opens the round-3 architect's note #1
  one door over.** `parse_markdown_file` cannot know whether its caller ADOPTED what it returned, so
  a read-only parse of P after another writer advanced P to `S1` would register `S1` while this
  process's cached entity still derives from `S0`; the next `repo.save(cached)` compares `S1` to
  `S1`, passes, and silently destroys the other writer's edit — LESSONS #43, and precisely the defect
  D5's rule exists to close. `## Scope Boundary` already records the same conclusion for
  `parser.py`; this is that conclusion promoted from an instruction to a ruling.
- **Narrow the zero case so `overwrite=True` against an existing target is not a create.**
  **Rejected — it re-opens the concurrent-create clobber that property 1 exists to close.**
  `BaseRepository.save` defaults `overwrite=True` (`obsidian_schemas/repositories/base.py:save:299`),
  so `create_stub`'s losing write IS an `overwrite=True` write with no stamp; a zero case that
  exempts `overwrite=True` exempts exactly the path door 2c was minted for.

**Consumer-facing consequence, stated as plainly as 2u's and 2c's.** `write_markdown_file(path, …,
overwrite=True)` against an EXISTING note that this process did not derive an entity from now raises
`NoteAlreadyExists` where it used to succeed. That reaches every consumer of the README recipe and
every `auto_load=False` / never-loaded repository (already named in door 2c's fourth bullet). The
answer is the per-call escape, which says in the call what the caller actually knows — *"I read this
myself, outside the package's observation, and I accept that the package cannot verify it"* — and
which, as corrected in D8(d), still runs the WI-126 body-shrink guard and still commits under the
lock with an in-lock stat precondition, i.e. degrades door 2u to door-1 strength rather than to no
protection at all. The consumer who wants the full precondition back goes through a repository
(`repo.get(...)` then `repo.save(...)`), which observes the derivation. `README.md` is outside the
cage (`pipeline-runners.yaml:32-33`), so updating that recipe is close-out step 5, not a plan task;
the three in-suite instances of the same shape are Table 3's R-β rows (D12).

**Why not the two alternatives, stated with their interaction with the `== 3` pin.**

- **(B) Template method** — `BaseRepository._load_file` stats, records and delegates parsing to a
  hook the subclasses override. It is total by construction, which is the strongest property on
  offer, and it is rejected on blast radius against a file this plan orders untouched. Under (B) the
  subclasses stop declaring `_load_file`, so `load_file_implementations` returns ONE function and
  `tests/test_loud_fail_parse.py:301`'s `assert len(loader_set) == 3` goes red; the hook
  implementations, which call `parse_frontmatter` directly (`book.py:67`, `meeting.py:72`), are seam
  seeds that belong to no contribution of the partition, so the residue name-set assertion at
  `tests/test_loud_fail_parse.py:332` goes red too. Task 2 orders both pins untouched because this
  item adds no repository — under (B) that stops being true, and the repair is two edits that change
  what a WI-020 acceptance test asserts. (B) also relocates each subclass's own broad
  `except → _note_skip`, which is WI-020's no-abort guarantee (`book.py:77-80`, `meeting.py:81-84`).
  If Dave wants (B) it is a legitimate call, and it is now a reversal of a written ruling with a
  named cost, not a gap.
- **(C) Record in `load()`'s loop at `base.py:187-193`** — rejected as not total: it misses the
  direct `_load_file` callers this design depends on, `BaseRepository.update_fields:393` (D5's
  self-healing argument below) and door 2c's recovery re-read (D9).

**(A′)'s interaction with the `== 3` pin is: none.** No class gains or loses a `_load_file`, so
`tests/test_loud_fail_parse.py:300` (`== 4`) and `:301` (`== 3`) both stay true and stay unedited,
and Wall D *consumes* the same two derivations rather than duplicating or moving them. That is the
deciding reason over (B), not a convenience.

**(A′) is not the route-every-one-individually shape `## Approach` rejected for door 2.** That
rejection turned on a specific fact — the routing wall's oracle is mutation-capability single-homing,
which is structurally blind to a repository that bypasses a door without performing a filesystem
write, so *no available derivation could see the miss*. Here a derivation already exists in the tree
and this document already relies on it, so the miss is exactly what a wall can see. Same move as
D8's, applied to the observation side: derive the corpus, then enforce over it.

**What the next level of the ladder returned, declared rather than left for round 5.** Sweeping
(entity derived from bytes) × (entity adopted into a cache) over this tree:

- **Derivation sites.** Every call of `parse_markdown_file` under `obsidian_schemas/` and `scripts/`
  is one of the three loaders — `obsidian_schemas/repositories/base.py:239`, `book.py:74`,
  `meeting.py:78`. `obsidian_schemas/__init__.py:37,111` re-exports the name and calls nothing. The
  derivation corpus and the loader corpus therefore coincide TODAY, and Wall D(ii) is what keeps them
  coincident rather than an observation that they happen to be.
- **Adoption sites.** Every assignment into `_cache` under `obsidian_schemas/` is
  `base.py:190` (the `load()` loop), `base.py:412` (`update_fields`), `base.py:332`, `book.py:174`
  and `meeting.py:196` (the three `save()` bodies). The first two adopt an entity a loader returned,
  so the stamp co-moves by (A′); the last three adopt the entity door 2 just committed, so the stamp
  co-moves by D8 step 8. There is no third way into `_cache`.
  `refresh()`'s zero-entity restore (`base.py:442-455`) puts back the entities of the *previous*
  load, whose stamps the registry still holds — the restore does not desynchronise them either.
  **Narrowed round 7 on the round-6 architect's note #1, because the sweep proves one direction
  only.** It proves every `_cache` write has a matching stamp record; it does **not** prove the
  converse, and the converse is the fail-OPEN direction. Two ways the registry ends up NEWER than a
  live cached entity: a direct `write_markdown_file(P, frontmatter=…, overwrite=True)` — exported
  public API at `obsidian_schemas/__init__.py:42,115` — registers at step 8 with no `_cache`
  adopting; and two repository instances over one vault share the module-level registry while
  holding separate caches, so instance A's `save()` advances the stamp for a note instance B still
  holds at an older snapshot. In both, B's next `save()` compares equal and passes. No in-package
  caller does either today — the only `write_markdown_file` call sites under `obsidian_schemas/` are
  `obsidian_schemas/repositories/base.py:save:321`, `obsidian_schemas/repositories/book.py:save:163`
  and `obsidian_schemas/repositories/meeting.py:save:185`, all of which adopt into their own
  `_cache` in the same call — so this is declared as residual **R13**, not redesigned. Making it
  total would require the stamp to ride on the PAYLOAD rather than on the path, which is a different
  frame from the one `## Approach` rules.
- **Sub-cell.** `PersonRepository` and `CompanyRepository` declare no loader and inherit
  `base._load_file`, so they are covered by the base recording with no per-class work — which is the
  same many-to-one fact the `== 3` pin exists to state.

Re-running the architect's scenario under the rule: load P → registry `S0`. `update_frontmatter_field`
(door 1) writes → disk is `S1`, registry is still `S0`. `repo.save(cached_entity)` → door 2 compares
`S0` to `S1` → **`StaleEntityWrite`**. The frontmatter change is protected by the mechanism written
to protect it.

Property 3's justification survives without the coupling: `create_stub` creates through door 2c,
which registers the new stamp, so its own following `save()` is a 2u update that passes. And the
in-package self-healing the architect observed falls out of the rule rather than being a special
case — `BaseRepository.update_fields` re-reads through `_load_file` at
`obsidian_schemas/repositories/base.py:393` after its door-1 write, so it re-registers the new stamp
*and* replaces the cached entity in the same step; cache and stamp co-move because the code already
made them. Under (A′) that argument is **dispatch-proof**, which is the point: `:393` is
`self._load_file(...)`, so for a book or meeting repository it lands in the overriding loader and
re-registers there. Closure (C) — recording in `load()`'s loop — would have left `:393` and door 2c's
recovery re-read (D9) unrecorded, which is why it is rejected above.

**The stat is taken BEFORE the bytes are read**, in `read_note` and at every observation point that
reads. The read and the stat are not atomic, so one of them must be stale under a race; stat-first
makes the stamp *older* than the payload, and an older stamp fails the precondition. The failure
direction is refusal. Stat-after would make the stamp newer than the payload and the failure
direction would be a silent lost update.

**Concretely, and identically, in each of the three loaders.** The shape is the same three lines
everywhere, which is what makes Wall D(i)'s call-name oracle sufficient:

```python
def _load_file(self, file_path):
    try:
        stamp = vault_io.stat_stamp(file_path)   # FIRST INSIDE THE try — before any read
        ...                                       # the loader's existing body, verbatim
        if doc.entity and isinstance(doc.entity, self.entity_type):
            vault_io.remember_snapshot(file_path, stamp)  # LAST — only on the entity branch
            return doc.entity
    except Exception as e:
        self._note_skip(file_path, e)       # unchanged: WI-020's no-abort guarantee
    return None
```

**The stat goes INSIDE the `try`, and that placement is load-bearing (corrected round 6 on the
round-5 architect's note #1).** The round-5 sketch made `stat_stamp` the FIRST statement of the
function, i.e. *above* the `try`. In two of the three loaders the `try` opens at
`obsidian_schemas/repositories/book.py:64` and `obsidian_schemas/repositories/meeting.py:70`, and the
broad `except → _note_skip` at `book.py:77-80` / `meeting.py:81-84` is explicitly WI-020's no-abort
guarantee — `obsidian_schemas/repositories/base.py:load:186-193`'s loop carries no `try` of its own,
so a `stat_stamp` raising above the `try` aborts the whole vault walk on one unreadable note. Inside
the `try`, an `OSError` from the stat lands in `_note_skip` exactly as a parse failure does. The
stat-before-read ordering argument above is untouched by the move, and Wall D(i)'s oracle is
`_called_names` over `_own_body_nodes`, which is indifferent to `try` nesting (it walks every node
that is not inside a nested function) — so the check sees the call either way.

- `obsidian_schemas/repositories/base.py:_load_file:226` does not read the file itself: the `try`
  already opens at `:238`, so the stat is its first statement, then `parse_markdown_file` at `:239`
  as today, then record on the entity branch (`:240-241`).
- `obsidian_schemas/repositories/book.py:_load_file:57` reads at `:66` before it parses, so the stat
  goes **immediately after `try:` at `:64` and above `:66`** — above the first read, not merely above
  `parse_markdown_file` at `:74` — and the record goes on the entity branch at `:75-76`. The
  `type != "book"` early `return None` at `:70-71` records nothing: no entity derives.
- `obsidian_schemas/repositories/meeting.py:_load_file:64` is the same shape: stat immediately after
  `try:` at `:70` and above the read at `:71`, record on the entity branch at `:79-80`, nothing on
  the `type != "meeting"` return at `:75-76`.

**The calls are spelled `vault_io.stat_stamp(...)` / `vault_io.remember_snapshot(...)` — module
attributes, never bare names.** That is D10's call-form ruling, applied here for the same reason it
is applied at every routed site: `tests/derivations.py:_is_write_call:189-195` gates on
`isinstance(node.func, ast.Attribute)`, and one call form across the whole item is what keeps that
gate a one-token edit. Wall D(i) is unaffected either way — `_called_names`
(`tests/derivations.py:_called_names:167-182`) collects `f(...)` and `x.f(...)` alike and keys the
attribute form on its `attr`, so `vault_io.stat_stamp(p)` contributes the name `stat_stamp`.

A note that fails to parse lands in `_skipped` (`base.py:223`), never in `_cache`, so no entity
derives from it and there is no derivation to anchor — and it therefore keeps the zero case's
protection: a later `save()` against it is refused as a create rather than passing on a stamp for
bytes nothing was derived from.

The post-write recording in D8 step 8 is the other direction and needs no such ordering: nothing is
being read, and the bytes on disk are the ones this process just committed, so a plain stat after
the commit is exactly the stamp the payload derives from.

The registry is process-local and unbounded in principle; in practice it holds one 3-field tuple per
loaded note (a 5,000-note vault is well under a megabyte), and `clear_snapshots()` exists for tests.
Its process-locality is declared as residual R8.

### D6. Configuration

| Setting | Where | Default | Valid range | Effect |
|---|---|---|---|---|
| `OBSIDIAN_SCHEMAS_WRITE_GUARD` | env | `enforce` | `enforce` \| `observe` | `observe` logs each refusal at WARNING and proceeds with today's semantics (D9), and logs ONE INFO line naming the mode at the first write of the process. Any other value raises `WriteFailedError` at first write — never silently treated as `enforce`. |
| `OBSIDIAN_SCHEMAS_LOCK_DIR` | env | unset → `<note dir>/.obsidian-schemas-locks/` | non-empty absolute path naming a usable directory | Homes lock sentinels outside the vault (obligation 3's named fallback). A relative, empty or unusable value raises `WriteFailedError` at first lock acquisition — never resolved against the process CWD (M2, D3). |
| `OBSIDIAN_SCHEMAS_LOCK_TIMEOUT` | env | `10.0` | float `> 0` | Lock acquisition timeout in seconds. A non-positive or unparseable value raises `WriteFailedError` at first acquisition rather than being silently coerced (D3). |
| `allow_unverified_overwrite` | keyword arg on `write_markdown_file` | `False` | bool | Per-call escape from door 2's precondition (D8). Not env-derived, so it does not route through the reader below; its invalid-value case is Python's own, since a non-bool is truthiness-tested exactly as `allow_body_replacement` already is. |

Read from the environment at each call rather than cached at import, so a consumer can flip
`observe` → `enforce` without a restart. All three env vars are read in `vault_io.py` only.

**The rule that makes that table TOTAL, and it is the second of round 8's two class folds.** M2 was
not "one env var the author forgot". Its generator is *a validity rule stated once per item over an
enumerable configuration surface, with the enumeration left to the author's memory* — two of the
three vars got a raise-on-bad-value clause and the third did not, and nothing in the design could
tell. Adding a third clause closes the instance and leaves the fourth var as round 9's finding. The
fold is a rule the shape of the code makes total:

> **`vault_io.py` reads `os.environ` in exactly ONE private helper —
> `_env_setting(name, parse, validate)` — which returns the default when the var is unset and raises
> `WriteFailedError` naming nothing but the var's own name for every value that fails `parse` or
> `validate`. Every setting in the table above is a call of it, and there is no second path from the
> environment into this module.**

So a setting added later cannot skip validation by being forgotten: it either routes through the
helper and gets the rule, or it names `os.environ` a second time — which is a Wall-B-shaped
capability duplication inside the one file Wall B excludes, and which Task 3 forbids in writing. The
helper never interpolates the VALUE into the message, only the variable's name, so a lock directory
containing a person's name cannot reach a message (D0.7, WI-020's `bounded_message` contract).

**The next level of the ladder for that class, swept and DECLARED.** Above "each setting is
validated" sits *each setting's cases*, and the sweep is: (i) **unset** — every var has a documented
default in the table and unset is never an error; (ii) **empty string** — distinct from unset on
POSIX and ruled a refusal for all three, because empty at a precondition is a bug shape (LESSONS #5)
and `""` silently means "the current directory" for a path and "zero" for nothing at all;
(iii) **valid but hostile** — a lock directory on a different filesystem is fine (sentinels are never
renamed across devices), a timeout of `1e9` is a hang the operator asked for, and neither is this
item's to police; (iv) **read timing** — every var is re-read per call rather than cached, so a
mid-run flip to an invalid value refuses at the NEXT door rather than at import, which is the
fail-closed direction. Cell (ii) is the one that changes behaviour and it is folded into the rule
above; the rest are declared so their absence is a finding rather than a gap.

### D7. Door 1 — routing, and what changes at each of the 13 sites

Each routed site becomes, in its own function body:

```python
from obsidian_schemas import vault_io          # module-level, once per routed file

with vault_io.note_lock(file_path):
    content, stamp = vault_io.read_note(file_path)
    ...                                    # the site's existing parse / dedup / transform, verbatim
    vault_io.write_note(file_path, new_content, precondition=stamp)
```

The site's `read_text` disappears; its parse, its dedup no-ops and its falsy returns stay exactly
where they are. This is the whole reason for the three-primitive shape ruled in `## Approach`
(Door 1, "Revised round 4").

**The call form is MODULE-ATTRIBUTE, and that is a ruling rather than a style (round 6).** Every door
invocation in this item — here, in D5's loaders, in D8's flow and in D9 — is written
`vault_io.<name>(...)`, never a bare `<name>(...)` imported with `from ... import write_note`. The
reason is `tests/derivations.py:_is_write_call:189-195`, whose body is
`isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in {...}`.
The `ast.Attribute` test is a hard gate: under a bare-name call form, widening the attr set "by
`DOOR_NAMES`" would match **nothing** at any routed site, and the three sweeps that consume the
predicate would all go red against correct code. The alternative resolution — give `_is_write_call`
an `ast.Name` arm — is rejected in writing: it changes the *node-shape gate* of the one predicate
four WI-020 sweeps depend on, which needs its own near-miss battery, whereas the module-attribute
form costs one import per routed file and leaves the shipped predicate's shape untouched.

**Parse-and-reserialize (5):** `obsidian_schemas/writer.py:update_frontmatter_field:283`,
`obsidian_schemas/writer.py:update_frontmatter_fields:333`,
`obsidian_schemas/writer.py:roundtrip_file:365`,
`obsidian_schemas/repositories/base.py:update_fields:390`, `scripts/lint_vault.py:876`.

**Verbatim frontmatter carry-through (8):** `obsidian_schemas/repositories/person.py:1543` and
`:1554` (both in `append_to_timeline`), `:1652` (`append_to_body_section`), `:1769`
(`add_to_discuss_item`), `:1845` (`update_to_discuss_item`), `:1912` (`remove_to_discuss_item`);
`scripts/lint_vault.py:894`; `scripts/migrate_person_to_discuss.py:104`.

Two site-specific notes the builder needs:

- `obsidian_schemas/writer.py:update_frontmatter_field:269-270` and `:319-320` raise
  `FileNotFoundError` when the file is absent, **before** any read (WI-020 AC-5 P4). That guard stays
  where it is and keeps its exception: door 1 never creates, by construction, and a missing target is
  a caller error rather than a race. `read_note` on a missing path likewise raises `FileNotFoundError`.
- `scripts/lint_vault.py:876` and `:894` both write `fpath` inside one `try` per file, and `:894`
  re-reads `fpath` at `:880`. Both writes take the same lock for the same path; the lock is
  reentrant, so a single `with note_lock(fpath):` spanning both is correct and is the shape to use —
  and each write still carries its own freshly-read stamp.

**What this preserves in WI-020's battery — DERIVED under the ruled call form, not predicted (round
6).** Each clause below is a walk of the actual predicate over the post-routing shape, and Task 11
RE-RUNS each one and pins what it printed; a mismatch is a hand-back, never an edit to the battery.

1. **`functions_reserializing_parsed_frontmatter` still returns exactly four.** Its sink is
   `_taints_a_write` (`tests/derivations.py:_taints_a_write:257`, sink loop at `:300-304`), which
   asks `_is_write_call(node)` and then whether any argument mentions a tainted name. In each of the
   four writers the transform's output is bound to `new_content`, tainted from the
   `parse_frontmatter` seed, and it is an argument of
   `vault_io.write_note(file_path, new_content, precondition=stamp)` — an `ast.Attribute` call whose
   `attr` is `write_note` ∈ `DOOR_NAMES`. Matched, tainted, member. The set is the same four
   `FunctionId`s at `tests/test_loud_fail_parse.py:110-116`. **No edit to that module.**
2. **The discrimination proof survives, and the reason is unchanged by routing.**
   `functions_parsing_then_writing:212` needs a `parse_frontmatter` call plus a later matched write
   in the same body. `write_markdown_file` keeps its `parse_frontmatter` call at
   `obsidian_schemas/writer.py:197` — D8(c) moves that read *inside the lock* and does not remove it
   — and its commit becomes `vault_io.create_note(...)` / `vault_io.write_note(...)`, matched. So
   `guard in loose_paths` holds. It is still REJECTED by the data-flow predicate for the same reason
   as today: `_, existing_body = parse_frontmatter(...)` seeds only `_` (tuple position 0), the
   committed `content` is built from `fm` and `body` at `:217-230`, and `_names_in(arg) & tainted` is
   therefore empty. `loose_paths - write_paths == {guard}` at
   `tests/test_loud_fail_parse.py:128-137` holds. **No edit.**
3. **`non_completed_write_sites` keeps every classified site.** Its universe gate is
   `writes = any(_is_write_call(n) for n in body)` (`tests/derivations.py:507`). The four `person.py`
   methods carrying the seven non-helper entries of the map at
   `tests/test_loud_fail_write.py:126-139` — `append_to_timeline`, `append_to_body_section`,
   `update_to_discuss_item`, `remove_to_discuss_item` — each call `vault_io.write_note(...)` in their
   OWN body after Task 5 (which forbids moving any of it into a nested helper), so each stays in the
   universe with its `SiteId` ordinals intact. `_get_body_content` is in the universe regardless, via
   `_SHARED_HELPERS` (`tests/derivations.py:481`). Neither `unclassified` nor `stale` at
   `tests/test_loud_fail_write.py:140-147` gains a member. **No edit.**
4. **The closure partition is untouched, which nothing before round 6 checked.** Routing changes what
   a function CALLS, never who calls it, and none of the five names it adds (`note_lock`, `read_note`,
   `write_note`, `create_note`, `stat_stamp`/`remember_snapshot`) reaches a `SEAM_NAMES` member — so
   `seam_invocation_closure` (`tests/derivations.py:seam_invocation_closure:393`) gains no member,
   the three contributions are the same sets as in (1)–(3), and the residue name-set assertion at
   `tests/test_loud_fail_parse.py:332` stays the same six parse functions. **No edit.**

The single required edit anywhere in the DERIVATION harness is the `_is_write_call` attr-set widening
in `tests/derivations.py` (D10), and its correctness is proven by Task 0 running the sweeps against
the *untouched* tree with `DOOR_NAMES` already in the set — where they match nothing, so the floor is
green and the widening is shown to be additive before a single routing edit exists.

**(5) And every clause above is STATIC — which is exactly half of each module (round-7 correction).**
Clauses (1)–(4) walk four AST predicates and are re-verified as correct. But
`tests/test_loud_fail_parse.py` and `tests/test_loud_fail_write.py` are each half derivation and half
BEHAVIOUR: they monkeypatch a commit call and assert what a repository method raises, and they call
`write_markdown_file` against paths they seeded themselves. A predicate walk cannot see either. The
round-6 architect and data-premise gates found five live breaks in that half, all real and all
re-verified this round. **The behavioural half is ruled in D12, which also replaces this section's
"no edit to that module" claim with an enumerated, sweep-derived edit set and a total disposition
rule.** Read D12 before executing Tasks 4, 5, 7 or 14.

### D8. Door 2 — inside `write_markdown_file`

`obsidian_schemas/writer.py:write_markdown_file:154` gains the door. Its new flow, in order:

```
1. resolve path
2. with vault_io.note_lock(path):
3.     stamp = vault_io.snapshot_stamp(path)
4.     unverified = allow_unverified_overwrite and overwrite and path.exists()
                                                    # WARNING naming the path; forces the 2u branch
5.     if not unverified and (stamp is None or overwrite is False):   # THE ZERO CASE
           WI-126 guard does not apply (no existing body by precondition)
           vault_io.create_note(path, content)      # atomic no-clobber; EEXIST -> NoteAlreadyExists
       else:                                        # 2u
6.         WI-126 body-shrink guard, read INSIDE the lock (see below) -- RUNS in BOTH 2u branches
7.         vault_io.write_note(
               path, content, origin="entity",
               precondition=stamp if not unverified else vault_io.stat_stamp(path))
8.     vault_io.record_snapshot(path)               # the write's own bytes become the new stamp
```

Every door call here is a module attribute, per D7's round-6 call-form ruling — which is what keeps
`write_markdown_file` inside `functions_parsing_then_writing`'s universe and therefore keeps the
discrimination proof at `tests/test_loud_fail_parse.py:128-137` green (D7, derivation 2).

Five consequences, each of which is a decision:

**(a) The `overwrite=False` guard at `obsidian_schemas/writer.py:186-187` is deleted.** It is a
generator-B row — `file_path.exists()` at `:186`, the write 50 lines later at `:236` — and the door
collapses it into the syscall. `overwrite=False` now *means* "this is a create", which routes to
step 5 regardless of stamp.

*And the flag has two different defaults, which is deliberate and load-bearing here.* The exported
`write_markdown_file` defaults `overwrite=False` (`obsidian_schemas/writer.py:write_markdown_file:160`)
while `BaseRepository.save` defaults it to `True` (`obsidian_schemas/repositories/base.py:save:299`,
and the three overrides copy that). So a bare `write_markdown_file(path, entity=e)` from a consumer
keeps today's exact create-or-refuse meaning — it routes to step 5 and raises `NoteAlreadyExists`
where it used to raise `FileExistsError` (D8b) — while `repo.save(e)` routes to step 5 only when it
has no stamp. This is not a repository-only flag and must not be read as one.

**(b) `NoteAlreadyExists` survives; `FileExistsError` does not.** The architect's note #2 asks which.
`NoteAlreadyExists` is a `LoudFailError` (→ `ValueError`) because `except LoudFailError` is how
WI-020 tells consumers to catch "this package refused", and that contract is the direction this
package is committed to. The two cannot be unified: `LoudFailError` derives from `ValueError` and
`FileExistsError` from `OSError`, and a class inheriting both fails at class-creation with
`TypeError: multiple bases have instance lay-out conflict`, so there is no subclass that satisfies
both `except` clauses. The cost is real and named in `## Risk Analysis`: a consumer catching
`FileExistsError` around `write_markdown_file` stops catching. In-repo the only catcher is
`tests/test_writer.py:test_no_overwrite_by_default:146-156`, updated in Task 14; out-of-repo it is a
close-out consumer audit in the shape of `docs/wi-024-consumer-audit.md`.

**And this paragraph is a sweep for CATCHERS only — the wider break it belongs to is D12's axis β
(round-7 correction).** Changing which exception a create collision raises is a small change beside
changing *which calls collide at all*: door 2 also changes the OUTCOME of every
`write_markdown_file(..., overwrite=True)` against a path this process never observed, and that
reaches callers with no `except` clause anywhere near them. That cell is ruled in D5, its in-suite
members are Table 3a rows 3–6, and its consumer members are close-out steps 3 and 5. Reading D8(b)'s
one catcher as the whole blast radius is the mistake round 6 caught.

**(c) The WI-126 body-shrink guard's read moves inside the lock.** Today
`obsidian_schemas/writer.py:195-214` reads the existing body at `:197-199` and writes at `:236` with
nothing held between. Under the door that read happens after the lock is taken and immediately
before the precondition, so the guard verifies the same bytes the precondition asserts. Its
behaviour is otherwise unchanged, including `UnverifiableBodyError` when the existing body cannot be
read (`:205-209`) and the `allow_body_replacement` escape. It does **not** run on the zero case:
there, non-existence is the precondition, so there is no existing body to shrink.

**(d) `allow_unverified_overwrite: bool = False`** is the named per-call escape for "replace this
note from a snapshot I did not read", in the shape of the WI-126 precedent
(`allow_body_replacement`, `obsidian_schemas/writer.py:161,173-174`) — never a module-level default,
and never `overwrite=True`, which is already the default and therefore means nothing.

**Corrected round 7: it bypasses step 5's ZERO CASE and step 7's stamp lookup, and nothing else.**
The previous text said "bypasses step 5–7" while also promising that "`allow_body_replacement` is
still required separately to drop body content" — and those two sentences contradict each other,
because step 6 IS the WI-126 body-shrink guard. Ruled on the second: the flag says *"I did not read
this note"*, never *"I may destroy its body"*. So step 6 runs in both 2u branches, and step 7 takes
its precondition from an in-lock `stat_stamp` instead of the registry. The escape therefore degrades
door 2u to **door-1 strength** — atomic, mutually excluded, and preconditioned on the read the guard
itself just took — rather than to no protection at all. With `overwrite=False` the flag has no
effect: that call means "create", and the zero case fires. Layers 1 and 2 still apply, and every use
logs at WARNING naming the path. It is threaded through
`BaseRepository.save` (`obsidian_schemas/repositories/base.py:save:294`),
`PersonRepository.save` (`obsidian_schemas/repositories/person.py:save:1252`),
`BookRepository.save` (`obsidian_schemas/repositories/book.py:save:138`) and
`MeetingRepository.save` (`obsidian_schemas/repositories/meeting.py:save:160`) as a keyword with the
same default, exactly as `allow_body_replacement` already is.

**(e) Placement is total on BOTH sides, and both are checkable.** *Enforcement:* all four `save()`
paths reach `write_markdown_file` — `person.py:1252` via `BaseRepository.save:321`; `company.py` has
no override so it inherits the same; `book.py:163` and `meeting.py:185` call it directly. A fifth
repository added tomorrow inherits the door for free, and the routing wall asserts it (D10 Wall A).
*Observation:* every loader records (D5's (A′)), so a note loaded by ANY repository carries a stamp
and reaches step 7's 2u path rather than step 5's zero case — and Wall D asserts that too, over the
same derived corpus. The two halves are what make step 5's `stamp is None` mean "nothing in this
process derived an entity from these bytes" rather than "nobody remembered to record here". Round 4
found the second half missing, which turned the ordinary `BookRepository.save` /
`MeetingRepository.save` of a loaded note into `NoteAlreadyExists` with every wall still green; that
path is now an acceptance criterion of its own (AC-11), because a wall over mutation capability is
structurally blind to a *missing observation*.

**And the sentence "nothing in this process derived an entity from these bytes" is true over the two
ROOTS only — never over a consumer (round-7 correction).** Both halves are walls over
`PACKAGE_ROOT`/`SCRIPTS_ROOT`. A caller outside them that parses a note with the exported
`parse_markdown_file` and writes it back HAS derived an entity from those bytes and still records no
stamp, so step 5's zero case fires against a live, documented pattern. That cell is ruled in D5
("The cell Wall D(ii) cannot reach"), its consumer face is stated there, and its three in-suite
instances are Table 3's R-β rows (D12). Nothing about step 5's flow changes; what changes is that
(e)'s claim is now bounded to the universe that can actually back it.

### D9. Door 2c's consumer-facing recovery, and door 3

**`PersonRepository.create_stub`** (`obsidian_schemas/repositories/person.py:create_stub:1337`) wraps
its `self.save(...)` at `:1466` in a `try`/`except NoteAlreadyExists`. On the exception it re-reads
**that one path** via `obsidian_schemas/repositories/base.py:_load_file:226` — not `refresh()`,
which is a whole-vault reload whose zero-entity restore guard (`base.py:refresh:442-455`) makes it
the wrong instrument for a single-note recovery — re-registers the stamp, **adopts the loaded entity
through `BaseRepository._adopt` (Edge Cases' adoption door — `_cache`, `_file_map` and
`_index_entity` in one locked critical section, never a bare `_cache[key] = entity`; the `_file_map`
half is load-bearing here, because the reuse branch's `_writeback_identifier` routes through
`update_fields`, which resolves the path through `get_file_path` and raises `ValueError` on a miss)**,
and then takes the reuse-on-collision branch it already has at `:1430-1437`: the same WARNING at
`:1431`, `_writeback_identifier` merging the supplied email/phone, and the existing `Person`
returned. If the re-read yields no entity (the winner wrote a note this repository cannot parse),
the `NoteAlreadyExists` propagates — a note that exists and does not load is not a reuse candidate,
and WI-020's skip surface is where it belongs.

Net effect for HAL9000 and exocortex: **the cross-process race now produces the same outcome the
in-process collision already produces.** `find_or_create_stub`
(`obsidian_schemas/repositories/person.py:find_or_create_stub:698`) reaches `create_stub` through
`resolve_or_create`'s Branch C (`obsidian_schemas/repositories/person.py:976`) and inherits the
recovery unchanged; its `(Person, created_new)` contract is preserved, with a lost race returning
`created_new=False` — which is what in fact happened.

**`BookRepository.create_stub`** (`obsidian_schemas/repositories/book.py:create_stub:273`) and
**`CompanyRepository.create_stub`** (`obsidian_schemas/repositories/company.py:create_stub:153`)
gain a genuine raising mode, because neither has a reuse branch to fall into (verified: `book.py`
goes straight to `self.save(...)` at `:317`, `company.py` at `:192`, neither with a collision
branch of any kind). `NoteAlreadyExists` reaches the caller. Giving them `PersonRepository`'s
reuse-and-writeback behaviour is a resolution-policy change on two entity types and is explicitly
out of scope (`## Scope Boundary`).

**Door 3** replaces `scripts/lint_vault.py:quarantine_garbage:1036-1038`. The `dest.exists()` guard
at `:1036` is deleted; `src.rename(dest)` at `:1038` becomes `vault_io.move_note(src, dest)`, whose
`NoteAlreadyExists` is caught in the loop and `continue`d — preserving the function's current
skip-on-collision behaviour while removing the TOCTOU. `quarantine_dir` is unchanged; the
`dest_dir.mkdir(parents=True, exist_ok=True)` at `:1034` becomes `vault_io.ensure_dir(dest_dir)` —
same
semantics, same absence of a precondition (R5, restated round 5), moved into the single-homed module
so Wall A's claim holds without an exemption. `move_note` forgets any snapshot for both paths.

**`observe` mode (D6)** turns every refusal in D4, D8 and door 3 into a WARNING naming the exception
class that would have fired, the path, and nothing else (`bounded_message`'s contract), and then
proceeds with today's semantics — the replace form even where the create form would have refused.
**And it announces itself once (round 8, the threat model's non-blocking note 1):** the first write
of a process whose `guard_mode()` is `observe` logs ONE INFO line naming the mode and the env var,
before any collision has occurred. Without it `observe` is a security-relevant configuration with no
signal at all while nothing is colliding, so a consumer can leave it set indefinitely and believe the
item shipped; a per-refusal WARNING only fires once the thing it is measuring has already happened.
One line per process, not per write, so it cannot become the noise that gets filtered.
Layers 1 and 2 apply in both modes. Default is `enforce`; the alternative (default `observe`, ramp
later) was considered and rejected, because a default that does not refuse ships the item without
its property and makes its acceptance criteria vacuous in production. The rollback for a consumer
that needs one is an environment variable, not a code change — which is the cheap reversibility the
architect's note #4 asked for. Declared as residual R9.

### D10. The routing wall

`tests/test_write_routing.py` (new), deriving every predicate from `tests/derivations.py`. **Five**
walls: A/B/C are the enforcement side — B is what makes "an unrecognised mutation kind is an
ERROR, not a pass" real rather than aspirational — **D is the observation side**, added round 5,
because a wall whose oracle is mutation capability is structurally blind to a *missing observation*
(D5), and **E is the door's own no-falsy-return contract**, added round 6 because D1's claim to be
enforced by an existing scan was vacuous.

#### D10.0 The class behind rounds 4 and 5, and the two folds that close it

**The generator, named rather than instanced.** Every wall in D10 was asserted green against today's
tree by PREDICTION. Round 4 found `mkdir`; the round-5 architect found `replace` and the door call
form; the round-5 data-premise gate found `copy` and the MUST-MATCH battery's dependency on a set no
wall consumed. Those are four members of one class: *a predicate whose effect on the current corpus
nobody executed.* Closing the four leaves round 6 the fifth, so this section closes the class.

**Fold 1 — structural: discriminate by PROVENANCE, never by member name where a module discriminator
exists.** The root defect is exact: *an attribute-NAME oracle over a vocabulary of stdlib verbs
cannot separate a filesystem receiver from a `str`/`dict` receiver*, and this tree exercises the
non-filesystem side of two of those verbs today. The fix is therefore not a choice between
`MUTATION_NAMES` and the union — under either reading the predicate is false. `MUTATION_SUSPECT_NAMES`
is **deleted**: every member of it is a member of a filesystem MODULE, and a module is a
discriminator syntax can decide. The vocabulary is re-partitioned by *how a name can be resolved*,
not by *whether this tree happens to use it*.

**Fold 2 — procedural: the predicates are RUN against the tree before the vocabulary is frozen, and
again after routing.** Task 0 executes every wall against the untouched tree and pins what each
returns in the Build Log against the table in D10.6; Task 11 re-runs the identical probe after
routing and pins it against the second table. **A mismatch either time is a HAND-BACK to the
conductor — never an edit to the vocabulary, never an edit to the pinned table, and never an edit to
WI-020's acceptance battery.** Round 4 found `mkdir` by running a predicate in a review; rounds 5's
findings would both have been caught by running Wall A once.

**The next level of the ladder, swept and declared rather than left for round 6.** Above the two
instances sit three dimensions, and all three are swept in D10.1–D10.5: (i) *vocabulary collision* —
every token in the vocabulary classified against this tree by receiver, in D10.6's first table, not
just the two the gates named; (ii) *call form* — whether each predicate's node-shape gate sees the
form the design writes, ruled in D7 and re-derived per sweep there; (iii) *universe membership* —
whether the routed functions still enter each consuming sweep's universe, derived in D7 (1)–(4).
Below those sits one intersection nobody had checked: **the effect of the NEW FILE on every existing
sweep's file set**, derived in D1's closing paragraph. Above them sits R11 — the wall's universe is
two roots, not the three consumer repos.

#### D10.1 The vocabulary, re-partitioned by resolvability

`tests/derivations.py` gains, and this is the whole of its edit:

```python
SCRIPTS_ROOT = _REPO_ROOT / "scripts"

DOOR_NAMES = frozenset({"write_note", "create_note", "move_note"})

# (1) pathlib.Path mutator methods with NO str/dict/list/set homonym. Safe to
#     match on ATTRIBUTE NAME alone, on any receiver -- and the MUST-NOT-MATCH
#     battery in D10.5 is what keeps that claim honest.
PATH_MUTATION_NAMES = frozenset({
    "write_text", "write_bytes", "mkdir", "rmdir", "unlink", "rename",
    "symlink_to", "hardlink_to", "link_to", "touch", "chmod", "lchmod",
})

# (2) names that are filesystem verbs ONLY as members of a filesystem module.
#     Matched ONLY through import provenance, never on attribute name, because
#     each has (or could have) a live non-filesystem homonym: `replace` is
#     str.replace, `copy` is dict.copy, `write` is any file object's.
MODULE_MUTATION_NAMES = frozenset({
    "replace", "remove", "removedirs", "makedirs", "renames", "rename",
    "unlink", "rmdir", "link", "symlink", "truncate", "chown", "fdopen",
    "open", "write", "move", "copy", "copy2", "copyfile", "copytree",
    "rmtree", "mkstemp", "mkdtemp", "NamedTemporaryFile", "TemporaryFile",
})

FS_MODULES = frozenset({"os", "shutil", "tempfile", "fcntl", "filelock", "mmap"})
OS_READONLY_NAMES = frozenset({"environ", "getenv", "sep", "path", "fspath", "getcwd"})
COMMIT_FUNCTION_NAMES = frozenset({
    "write_note", "create_note", "move_note", "read_note",
    "stat_stamp", "record_snapshot", "ensure_dir",
})

def filesystem_mutation_uses(files) -> list:      # -> list[AstUse]; Wall A
    ...
def os_module_attribute_uses(files) -> list:      # -> list[AstUse]; Wall B
    ...
def module_import_uses(files, modules) -> list:   # -> list[AstUse]; Wall C
    ...
def functions_calling(files, name: str) -> set:   # -> set[FunctionId]; Wall D
    ...
def falsy_returns_in(files, names) -> list:       # -> list[SiteId]; Wall E
    ...
```

A name may appear in BOTH vocabularies (`rename`, `unlink`, `rmdir` are genuine `Path` methods AND
`os` functions); the arms below are a union, so membership in one never narrows the other.

#### D10.2 `filesystem_mutation_uses` — four arms, every one decidable from syntax

It reads PARSED SYNTAX, never source text (the `modules_using_ast` lesson at
`tests/derivations.py:modules_using_ast:528`: a text matcher matches the test that plants its own
fixtures as string literals and goes red on a correct harness). Per file it first collects the
module-name bindings — `import m`, `import m as a`, `from m import n`, `from m import n as a` for
`m ∈ FS_MODULES` — exactly as `modules_using_ast` already collects `ast`'s. Then:

- **(a) Path-method arm.** An `ast.Attribute` call whose `attr ∈ PATH_MUTATION_NAMES`. No receiver
  analysis, because the vocabulary is homonym-free by construction.
- **(b) Module-qualified arm.** An `ast.Attribute` call whose receiver is an `ast.Name` bound by an
  import of an `FS_MODULES` member and whose `attr ∈ MODULE_MUTATION_NAMES | PATH_MUTATION_NAMES`.
  Resolves `os.replace(a, b)`, `os.makedirs(d)`, `shutil.move(a, b)`, `tempfile.mkstemp()`.
- **(c) Aliased-import arm.** An `ast.Name` call whose `id` is a name bound by
  `from <fs-module> import <n>` (with or without `as`), where the ORIGINAL `n` is in either
  vocabulary. Resolves `from shutil import move; move(a, b)` and
  `from os import replace as _r; _r(a, b)` — the shape WI-232's wall claimed and never collected.
  Provenance is the import, so the local alias is irrelevant.
- **(d) Write-mode `open` arm.** A call whose callee is the bare name `open` or an attribute named
  `open`, whose second positional argument or `mode=` keyword is a string literal containing any of
  `w`, `a`, `x`, `+`. Resolves `open(p, "w")` and `p.open("a")`; leaves every read-mode form alone.

**`PATH_MUTATION_NAMES` is TOTAL over `pathlib.Path`'s mutating API as it stands, and that is what
lets `## Intent` say "an unrecognised mutation kind is a red build" without overclaiming.** `Path`'s
mutators are `write_text`, `write_bytes`, `mkdir`, `rmdir`, `unlink`, `rename`, `replace`, `touch`,
`symlink_to`, `hardlink_to`, `link_to`, `chmod`, `lchmod` and `open` — every one of them is in the
name-matched arm except `open`, which arm (d) resolves with a mode test, and `replace`, which is
R10. Arms (b) and (c) are total over `os`, `shutil` and `tempfile` in a stronger sense still: Walls B
and C discriminate by MODULE, so a member no vocabulary ever anticipated is red anyway.

**What no arm resolves, and it is a declared residual rather than an oversight: `p.replace(q)`.**
`replace` is the ONE `pathlib.Path` mutator whose attribute name collides with a method of a builtin
type, so it sits in `MODULE_MUTATION_NAMES` only and a bare `p.replace(q)` on a `Path` variable is
invisible to Wall A. That is R10, with its price stated there and its alternative rejected below.

#### D10.3 Walls A, B, C

**Wall A — single-homing.** `filesystem_mutation_uses(python_files_under(PACKAGE_ROOT, SCRIPTS_ROOT))`
returns uses in `obsidian_schemas/vault_io.py` **and nowhere else**. Failure message names the
offending module, the line, and the capability.

**`replace` and `copy` do NOT enter the name-matched arm, and the alternatives are priced (round-6
ruling).** Run against this tree, `.replace(` resolves to fourteen call nodes across nine lines —
`obsidian_schemas/models.py:110`, `:136` (×2); `obsidian_schemas/repositories/book.py:94`, `:124`,
`:207`, `:255` (×2 each); `obsidian_schemas/repositories/meeting.py:211`;
`obsidian_schemas/repositories/person.py:1141`; `scripts/lint_vault.py:889` — every one a
`str.replace`; and `.copy()` resolves to `obsidian_schemas/writer.py:220`,
`obsidian_schemas/parser.py:176` and `:211`, every one a dict copy. `models.py`, `parser.py` and
`person.py`'s cleaning path are on `## Scope Boundary`'s untouchable list, and unlike the `mkdir`
cell there is no `ensure_dir`-shaped move available: these are not filesystem calls at all. So
putting either name in `PATH_MUTATION_NAMES` is Wall A **red on day one** with no green reachable
from inside the cage except the two moves this section forbids by name — dropping the token (the wall
narrowing its own reach) or carving an exemption (the exemption-not-predicate shape Wall B exists to
avoid). Provenance matching is the third answer, and the one that keeps `os.replace`,
`shutil.copyfile` and the aliased-import form all resolvable while `s.replace("-", "")` and
`frontmatter.copy()` are not. Both are pinned as near-misses in D10.5.

**`mkdir` stays in the vocabulary — in `PATH_MUTATION_NAMES` — and the two live sites move (round-5
ruling; R5 restated).** There are exactly two `mkdir` calls under these roots today —
`obsidian_schemas/writer.py:write_markdown_file:233` and
`scripts/lint_vault.py:quarantine_garbage:1034`, re-verified round 6 by the sweep in D10.6 — and the
round-4 gates were
right that Wall A as specified forbids both while R5/D9/Task 9 ordered them left in place, making
AC-7 unsatisfiable and Task 12's verify unachievable. Both now call `vault_io.ensure_dir` (D1, D9,
Task 9). The two alternatives are rejected in writing: dropping `"mkdir"` from the vocabulary is the
wall silently narrowing its own reach — the cheapest green from inside the cage, and the exact
failure this battery exists to prevent — and it would leave a future `Path.mkdir` anywhere outside
the door invisible to Wall A (Wall B still catches `os.makedirs`, but not the `Path` form); a named
exemption for `mkdir(parents=True, exist_ok=True)` re-introduces the exemption-not-predicate shape
Wall B was deliberately built to avoid. `p.mkdir(parents=True)` and `os.makedirs(d)` therefore stay
in the MUST-MATCH fixture list below, unchanged. `mkdir` is homonym-free, so unlike `replace` it
carries no day-one cost for being name-matched — which is exactly why the two cells get different
rulings from the same principle.

**Wall B — the unenumerated-kind trap on module access, in BOTH access forms.**
`os_module_attribute_uses` over the same
roots, excluding `vault_io.py`, returns only attributes in `OS_READONLY_NAMES`. This is a rule over
the *attribute*, not a list of exempt files: `obsidian_schemas/repositories/base.py:97` needs
`os.environ`, `scripts/lint_vault.py:52` and `scripts/migrate_person_to_discuss.py:160` need the
same, and all three pass by predicate rather than by exemption. **Widened round 6 to collect
`from os import <n>` bindings as well as `os.<attr>` accesses**, where `n ∉ OS_READONLY_NAMES` — that
form is how `from os import replace as _r` would otherwise smuggle a mutator past a wall keyed on
attribute access, and it is why Wall C is NOT widened to `os`: `import os` is legitimate at
`base.py:9`, `lint_vault.py:22` and `migrate_person_to_discuss.py:23` for `os.environ`, so `os` can
only be policed at member granularity. A future `os.unlink`, `os.replace`
or `os.open` anywhere outside the door is red — including a name no vocabulary ever
anticipated, because the discriminator is the *module*, not the member. **This is where `os.replace`
is caught even though `replace` is not name-matched (R10), and it is caught with no vocabulary at
all.**

**Wall C — import single-homing.** `shutil`, `tempfile`, `fcntl`, `filelock` and `mmap` are imported
by `vault_io.py` only, over the same roots, read as syntax (`ast.Import` / `ast.ImportFrom`, both
forms). This
closes the remaining route to a mutation capability that neither vocabulary names — and it is what
makes the aliased-import arm belt-and-braces rather than load-bearing for those five modules.

#### D10.4 Walls D and E

**Wall D — the observation side (new, round 5).** Walls A–C are total over *mutation*; nothing in
them can see a loader that never records a derivation stamp, because such a loader performs no write
at all. Wall D closes that class over the same derived corpus D5 rules on. Let

```python
loaders = load_file_implementations(base_repository_subclasses(python_files_under(PACKAGE_ROOT)))
files   = python_files_under(PACKAGE_ROOT, SCRIPTS_ROOT)
```

- **D(i) — every loader records.** `loaders <= functions_calling(files, "stat_stamp")` and
  `loaders <= functions_calling(files, "remember_snapshot")`. A fifth repository that declares its
  own `_load_file` and forgets either call is RED on the floor, naming the class and the missing
  call — instead of silently losing stamps and turning that entity type's first `save()` after load
  into `NoteAlreadyExists`.
- **D(ii) — nothing derives an entity outside the corpus.**
  `functions_calling(files, "parse_markdown_file") == loaders`. This holds exactly today (the only
  three call sites are `obsidian_schemas/repositories/base.py:239`, `book.py:74`, `meeting.py:78`,
  and all three ARE the loaders), and it is asserted so that it keeps holding: a new entity
  derivation added in a script or a helper is RED demanding a ruling — record a stamp there too, or
  say in writing why that payload never reaches door 2 — rather than becoming the next gate's next
  finding.

`functions_calling` is one predicate serving both halves of Wall D, built on the `_called_names`
machinery `tests/derivations.py:_called_names:167` already uses — it collects `f(...)` and
`x.f(...)` alike, from the function's OWN body (`_own_body_nodes`), so a call moved into a nested
helper does not count as the enclosing function's. That is the same attribute-name resolution the
module's own docstring justifies for `self._load_file(...)`, and it is why D7's module-attribute call
form costs Wall D nothing: `vault_io.stat_stamp(p)` contributes the name `stat_stamp` exactly as a
bare `stat_stamp(p)` would.

Both halves import their derivations from `tests.derivations` and assert
`derivation.__module__ == "tests.derivations"`, the same single-sourcing shape
`tests/test_loud_fail_parse.py:100-104` uses. Wall D consumes
`load_file_implementations` and `base_repository_subclasses` unchanged; it neither edits them nor
duplicates their logic, which is why the count pins at `tests/test_loud_fail_parse.py:300-301` stay
true and stay untouched (D5). The two predicates are type-compatible, which is not obvious and
matters: `load_file_implementations` mints its `FunctionId` through `_function_id_of`
(`tests/derivations.py:_function_id_of:380`, `func.__module__` → posix path + `__qualname__`) while
`functions_calling` mints its own through `_iter_functions` (`tests/derivations.py:_iter_functions:122`,
`module_id` + the nesting stack); both produce
`FunctionId("obsidian_schemas/repositories/base.py", "BaseRepository._load_file")`, so `<=` and `==`
mean what this section says they mean.

**Wall E — the doors' no-falsy-return contract (new, round 6).**
`falsy_returns_in(python_files_under(PACKAGE_ROOT), COMMIT_FUNCTION_NAMES)` is empty. It shares
`_own_body_nodes` (`tests/derivations.py:_own_body_nodes:148`) and `_is_falsy_return`
(`tests/derivations.py:_is_falsy_return:518`) with `non_completed_write_sites` — one rule over two
universes, never a second copy — and it exists because D1's rule was previously asserted against
`non_completed_write_sites`, whose universe gate is `_is_write_call` (`tests/derivations.py:507`), a
universe no `vault_io` function enters (D2 commits through a file descriptor). See D1.

`falsy_returns_in(files, names)` selects a function by `FunctionId.name` — the existing `.name`
property at `tests/derivations.py:FunctionId:39`, i.e. the last dotted segment of the qualname — so a
module-level `write_note` matches on `"write_note"` and a nested helper of the same name inside
another function does not contribute its parent's sites (`_own_body_nodes` already excludes nested
bodies). Sites are returned as `SiteId(module, qualname, ordinal)`, the same shape
`non_completed_write_sites` returns, so a failure message names the exact function and the ordinal of
the offending return.

#### D10.5 Every claimed match-shape ships as a fixture, driven through the wall's own predicate

**The obligation, stated ONCE over D10.1's predicate set rather than per wall (round 10).** Rounds 2
and 9 each closed a battery gap one wall at a time — Wall E's in round 9, after Wall A's and Wall
D's had shipped — and rounds 2 and 10 then found the next member. The generator is not "Wall E was
forgotten": it is that *this section's battery list was maintained by hand while the surface it
covers is closed, declared and derivable from D10.1*. So the rule is written over the source:

> **Every wall predicate declared in D10.1 ships a MATCHED battery and a NOT-matched battery,
> planted in a scratch module and driven through the SAME function the live wall calls — never a
> re-implementation. The set of batteries is `{filesystem_mutation_uses, os_module_attribute_uses,
> module_import_uses, functions_calling, falsy_returns_in}`, which is D10.1's predicate set, and
> Task 12 derives its battery list from that set rather than from a hand-written list. A predicate
> added to D10.1 later without a battery is an unfixtured wall, not a smaller job.**

**Why the two that were missing were the two that mattered most, and this is measured rather than
argued.** `os_module_attribute_uses` (Wall B) and `module_import_uses` (Wall C) are each ZERO-COUNT
on the arm the design leans on, verified against this tree: the only `os` imports under either root
are the plain `import os` at `obsidian_schemas/repositories/base.py:9`, `scripts/lint_vault.py:22`
and `scripts/migrate_person_to_discuss.py:23`; there are **zero `from os import` bindings** and
**zero `shutil`/`tempfile`/`fcntl`/`filelock`/`mmap` imports** anywhere under
`obsidian_schemas/` or `scripts/`. So a Wall B that never implements the `ast.ImportFrom` collection
D10.3 added in round 6 returns the identical three `environ` uses, and a Wall C that returns `[]`
unconditionally matches its own row — both GREEN at Task 0, GREEN at Task 11 and GREEN at Task 12,
while AC-7's `desc` certifies "imports a mutation-capable module, or reaches a non-read-only `os`
attribute **in either access form**", and while R10's stated bound on the declared blind spot
("Wall B independently makes any `os` member outside `OS_READONLY_NAMES` red wherever it is named")
would be false with every check green. A count of zero says nothing about a matcher's reach; that
is the whole of WI-235, and it bites hardest exactly where the live count is zero.

**Wall B ships its own match-shapes, over BOTH access forms.** `tests/test_write_routing.py` plants
a scratch module and drives it through **`os_module_attribute_uses` — the same function Wall B
calls** — asserting **MATCHED**:

| Shape | What it pins |
|---|---|
| `import os` + `os.unlink(p)`; `os.replace(a, b)`; `os.open(p, flags)`; `os.fchmod(fd, m)` | the attribute-access form over members outside `OS_READONLY_NAMES` — including `fchmod`, which is in NO vocabulary, because Wall B's discriminator is the MODULE and not the member (D10.3) |
| `import os as _o` + `_o.unlink(p)` | the aliased module binding — the discriminator is the import, not the local name |
| `from os import replace` (the binding, with `replace(a, b)` used) | the `ast.ImportFrom` arm added round 6 — the form that would otherwise smuggle a mutator past a wall keyed on attribute access |
| `from os import replace as _r` (with `_r(a, b)` used) | the same arm under an alias, which is the shape R10's bound depends on |
| `from os import unlink` with the binding **never called** | the arm collects the BINDING, not the call — an unused mutator import is still a mutation capability outside the door |

and **NOT matched**:

| Shape | Why |
|---|---|
| `os.environ.get("X")`; `os.getenv("X")`; `os.getcwd()`; `os.sep`; `os.path.join(a, b)`; `os.fspath(p)` | every member of `OS_READONLY_NAMES`. Three of these are LIVE at `base.py:97`, `lint_vault.py:52` and `migrate_person_to_discuss.py:160`, and they pass by predicate rather than by file exemption — that is Wall B's stated design |
| `from os import environ` (the binding, used) | same rule on the `ImportFrom` arm: membership of `OS_READONLY_NAMES` decides, not the access form |
| a bare `import os` with no attribute access and no `from` binding | legitimate at the three live sites; a plain module import is Wall C's business and Wall C is deliberately NOT widened to `os` (D10.3) |
| the string literal `"os.replace"` and a docstring naming `from os import unlink` | parsed syntax, never source text |
| `shutil.move(a, b)` | not `os`; Wall B's universe is the `os` module, and `shutil` is Wall C's and Wall A arm (b)'s |

**Wall C ships its own match-shapes, over both import statement forms.** Driven through
**`module_import_uses(files, modules)` — the same function Wall C calls** — asserting **MATCHED**:

| Shape | What it pins |
|---|---|
| `import shutil`; `import tempfile`; `import fcntl`; `import filelock`; `import mmap` | the `ast.Import` form over every member of the module set Wall C is called with, generated by ITERATING the set `D10.3` names rather than by a hand-written list, and asserting the returned module set equals it |
| `import tempfile as _t` | the aliased `ast.Import` form |
| `from filelock import FileLock`; `from shutil import move` | the `ast.ImportFrom` form — D10.3 claims "both forms", and a matcher implementing one is green against this tree either way |
| `from tempfile import NamedTemporaryFile as _n` | the aliased `ast.ImportFrom` form |
| an import of a member module that is **never used** | Wall C's oracle is the IMPORT, not a call — bringing the capability into a module is the thing it forbids |

and **NOT matched**:

| Shape | Why |
|---|---|
| `import os` | legitimate at three live sites; `os` is deliberately outside Wall C's module set and is policed at member granularity by Wall B (D10.3) |
| `import pathlib`; `from pathlib import Path`; `import hashlib`; `import threading` | modules outside the set — a wall matching everything is as useless as one matching nothing |
| the module names in a string literal (`"import shutil"`) or a docstring or a comment | parsed syntax, never source text |
| a local variable named `shutil` with no import | the arm reads import statements, not names |

**Wall D ships its own match-shapes (WI-235), because its oracle is a set comparison.** A subset
assertion is satisfied identically by a predicate that resolves every call form and by one that
resolves almost none. `tests/test_write_routing.py` therefore drives a planted scratch module through
`functions_calling` — the same function the walls call — asserting these are MATCHED:
`foo(x)` (bare name), `self.foo(x)` and `mod.foo(x)` (attribute), a call inside a nested `if`/`try`,
and a call inside a `for` body; and these NOT matched: the name in a docstring, in a comment, in a
bare string literal `"foo"`, as an import (`from m import foo`) with no call, as an attribute access
with no call (`fn = self.foo`), and a call of `foo` inside a NESTED function of the scanned function
(the `_own_body_nodes` boundary — a loader that hides its recording in a closure is deliberately RED,
for the same reason Task 5 forbids moving a dedup check into one).

**Wall E ships its own match-shapes, and its fixture space is DERIVED from `COMMIT_FUNCTION_NAMES`
rather than hand-listed (round 9).** Wall E was, at round 9, the zero-count wall whose missing
battery had been named — Walls B and C's were found one round later and are written out above, which
is why the obligation now lives at the top of this section over D10.1's whole predicate set instead
of arriving one wall per round. Before round 9 its only control was Task 12's mutate-and-observe probe,
which the bar names as "the complementary half and never sufficient". The reach AC-13 certifies is
not small — the rule holds over **all seven** members of `COMMIT_FUNCTION_NAMES`, with `read_note`
and `ensure_dir` INSIDE the set rather than quoted past it (D1's round-8 correction), over three
falsy forms, own-body-only, selected by `FunctionId.name`'s last dotted segment. A
`falsy_returns_in` that resolved only the three door names would leave a `return None` in
`read_note` invisible, Wall E green and AC-13 green while AC-13's `desc` asserts the opposite — the
WI-232 shape D10.5 already closes for Walls A and D. So `tests/test_write_routing.py` plants a
scratch module and drives it through **`falsy_returns_in` — the same function Wall E calls, never a
re-implementation** — asserting **MATCHED**:

| Shape | What it pins |
|---|---|
| **one module-level `def <n>(…): return None` for EVERY member of `COMMIT_FUNCTION_NAMES`**, the fixture source generated by ITERATING that frozenset rather than by a literal list, then asserting `{s.qualname.rsplit(".", 1)[-1] for s in falsy_returns_in([plant], COMMIT_FUNCTION_NAMES)} == set(COMMIT_FUNCTION_NAMES)` — set EQUALITY, not `⊇`. (`falsy_returns_in` returns `SiteId(module, qualname, ordinal)`, `tests/derivations.py:SiteId:48-51`, which carries no `.name` property of its own; the last dotted segment is the selection key, `tests/derivations.py:FunctionId:39` at `:43-45`.) | the wall's reach over its whole declared set — a name added to the constant later cannot be silently unfixtured, and today's `read_note` / `stat_stamp` / `record_snapshot` / `ensure_dir` members are driven rather than assumed |
| `return`, `return None` and `return False` in three separate functions all named `write_note` in three planted modules | the three falsy forms `_is_falsy_return` (`tests/derivations.py:_is_falsy_return:518-521`) claims |
| `return ""` and `return 0` in a `create_note` | the falsy-`ast.Constant` arm, which is broader than the three named forms and is claimed by the same predicate |
| a falsy return nested inside an `if` and inside a `try` in `move_note`'s own body | `_own_body_nodes` (`tests/derivations.py:_own_body_nodes:148-164`) descends into non-function children |
| `class X: def read_note(self): return None` | selection by `FunctionId.name`, the LAST dotted segment of the qualname (`tests/derivations.py:FunctionId:39`) — a method counts |

and asserting **NOT matched**:

| Shape | Why |
|---|---|
| `def write_note(…): return path` (an `ast.Name`); `return True`; `return "text"`; `return 1` | `_is_falsy_return` tests a falsy `ast.Constant`; a non-constant is never a member, which is why a door returning a real path is legal |
| a falsy `return` inside a **nested** function of `write_note` | the `_own_body_nodes` boundary — the same boundary Wall D's battery already pins, and the same reason Task 5 forbids moving a dedup check into a closure |
| a falsy return in `def helper(…)`, `def snapshot_stamp(…)`, `def guard_mode(…)` | names outside `COMMIT_FUNCTION_NAMES`. `snapshot_stamp` is named explicitly because its `None` return IS the zero case the whole precondition rule is built on (D1, D4, D8 step 5) — a wall that matched it would be red against the design |
| `def write_note(…):` with an implicit fall-off-the-end and no `ast.Return` at all | invisible to `falsy_returns_in` by construction (D10.4). Pinned as NOT matched so a later reader meets the declared limit instead of "fixing" the wall into a claim it does not make |
| the string literal `"write_note"` and a docstring naming `return None` | parsed syntax, never source text |

**The wall's claimed match-shapes ship as GREEN fixtures (WI-235).** A count oracle says nothing
about a matcher's reach — `matches == 0` is satisfied identically by a matcher that resolves every
claimed shape and by one that resolves almost none. `tests/test_write_routing.py` therefore plants a
scratch directory and drives it through `filesystem_mutation_uses` — **the same function the live
walls call, never a re-implementation** — asserting each of these is MATCHED:

**Restated round 6 so every claimed shape is resolvable by the predicate as ruled.** The previous
list asserted eleven shapes whose names lived only in the now-deleted `MUTATION_SUSPECT_NAMES`, i.e.
against a set no wall consumed — the defect the round-5 data-premise gate found. Each shape below is
annotated with the arm (D10.2) that must resolve it, so the fixture and the predicate cannot drift
apart silently. **MATCHED:**

| Shape | Arm |
|---|---|
| `p.write_text(s)`; `p.write_bytes(b)`; `Path(p).write_text(s)` | (a) |
| `src.rename(dest)`; `p.mkdir(parents=True)`; `p.unlink()`; `p.rmdir()`; `p.touch()`; `p.symlink_to(q)`; `p.hardlink_to(q)`; `p.chmod(0o600)` | (a) |
| `os.replace(a, b)`; `os.rename(a, b)`; `os.remove(p)`; `os.unlink(p)`; `os.makedirs(d)`; `os.link(a, b)`; `os.write(fd, b)` (each with `import os` in the fixture) | (b) |
| `shutil.move(a, b)`; `shutil.copyfile(a, b)`; `shutil.copytree(a, b)`; `shutil.rmtree(d)` | (b) |
| `tempfile.NamedTemporaryFile()`; `tempfile.mkstemp()` | (b) |
| `from shutil import move` + `move(a, b)` | (c) |
| `from os import replace as _r` + `_r(a, b)` | (c) |
| `open(p, "w")`; `open(p, mode="a")`; `open(p, "x")`; `p.open("w")` | (d) |

**NOT matched — and the last three are the round-5 findings, pinned so the wall cannot be "fixed"
into being red on arrival:**

| Shape | Why |
|---|---|
| `open(p)`; `open(p, "r")`; `open(p, encoding="utf-8")` | arm (d)'s mode test |
| a bare string literal `"write_text"`; a comment mentioning `os.replace`; a docstring naming `shutil.move` | parsed syntax, not text |
| an attribute *access* with no call (`fn = p.write_text`) | deliberately out of scope — the wall matches calls, and a bound-method smuggle is caught by Wall C's import rule instead |
| `os.environ.get("X")`; `os.getcwd()` | neither vocabulary names them; read-only `os` members are Wall B's business |
| **`s.replace("-", "")`** where `s` is any receiver not bound by an `FS_MODULES` import | `replace` is provenance-matched only (D10.3). Fourteen live call nodes in this tree depend on this |
| **`frontmatter.copy()`** | same rule for `copy`. Three live call nodes, one of them in `parser.py`, which is not a `## Write Targets` entry at all |
| **`p.replace(q)`** — a genuine `Path.replace` | **R10, the declared blind spot.** The fixture carries a comment naming R10 and D10.3, so a reader who "fixes" it meets the ruling and the fourteen `str.replace` sites instead of shipping a wall that is red on arrival |

The near-misses are what stop the wall from passing by matching everything and then being narrowed
back with nothing checking that the narrowing kept the claimed shapes; the last three are what stop
it from being *widened* back into a shape that cannot go green at all.

**`_is_write_call` (`tests/derivations.py:_is_write_call:189`) is widened to
`{"write_text", "write_bytes"} | DOOR_NAMES` and is NOT otherwise touched — in particular its
`isinstance(node.func, ast.Attribute)` gate stays.** Its docstring already says "a call that commits
bytes to the filesystem"; after this item the way package code commits bytes is by calling a door
**as a module attribute** (D7's call-form ruling), so the meaning is unchanged and the extension over
the sweeps that consume it
(`functions_parsing_then_writing:227`, `_taints_a_write:301`, `non_completed_write_sites:507`) is
preserved — as derived clause by clause in D7. Two alternatives are rejected in writing: giving it an
`ast.Name` arm changes the node-shape gate four WI-020 sweeps depend on and needs its own near-miss
battery (D7); and replacing its set with `PATH_MUTATION_NAMES` would sweep `mkdir` and `rename` into
WI-020's AC-1/AC-5 universes, which is a different predicate wearing the same name.

#### D10.6 What the predicates RETURN against this tree — pinned, not predicted

Both tables are executed rather than believed: Task 0 prints the first before any routing edit
exists, Task 11 prints the second after routing lands, and each is compared line by line against what
is written here. **A mismatch either time is a hand-back to the conductor** — the pinned table, the
vocabulary and WI-020's acceptance battery are all off-limits as the repair. This is the fold that
ends the arc: every finding rounds 4 and 5 produced was reachable by executing one of these rows.

**Table 1 — PRE-ROUTING, against the untouched tree (Task 0).** Roots `obsidian_schemas/` and
`scripts/`, `tests/` excluded.

| Predicate | Returns | Verdict |
|---|---|---|
| `filesystem_mutation_uses` | exactly 17 uses — `writer.py:233,236,283,333,365`; `repositories/base.py:390`; `repositories/person.py:1543,1554,1652,1769,1845,1912`; `lint_vault.py:876,894,1034,1038`; `migrate_person_to_discuss.py:104` (14 `write_text` + 2 `mkdir` + 1 `rename`) | Wall A **RED, expected** — `vault_io.py` does not exist yet |
| …and ZERO uses at `models.py:110,136`; `book.py:94,124,207,255`; `meeting.py:211`; `person.py:1141`; `lint_vault.py:889` | the fourteen `str.replace` call nodes | **the row that proves the discriminator**; a non-empty result here is the round-5 defect, and a hand-back |
| …and ZERO uses at `writer.py:220`; `parser.py:176,211` | the three `dict.copy` call nodes | same |
| `os_module_attribute_uses` | 3 uses, all `environ` — `repositories/base.py:97`, `lint_vault.py:52`, `migrate_person_to_discuss.py:160`; zero `from os import` bindings | Wall B **GREEN** |
| `module_import_uses(files, {"shutil","tempfile","fcntl","filelock","mmap"})` | empty | Wall C **GREEN** |
| `functions_calling(files, "stat_stamp")` | empty | Wall D(i) **RED, expected** |
| `functions_calling(files, "_adopt")` | empty — the adoption door does not exist yet | expected; the row exists so Table 2's non-empty result is a measured delta rather than a first sighting |
| `functions_calling(files, "parse_markdown_file")` | exactly the three loaders — `repositories/base.py:239`, `book.py:74`, `meeting.py:78` — and `== load_file_implementations(base_repository_subclasses(...))` | Wall D(ii) **GREEN** |
| `falsy_returns_in(python_files_under(PACKAGE_ROOT), COMMIT_FUNCTION_NAMES)` | empty **because `vault_io.py` does not exist** | Wall E green **vacuously** — stated as vacuous so Task 11's non-vacuous green is the one that counts |
| THE FLOOR, with `DOOR_NAMES` already inside `_is_write_call` | GREEN, at Task 1's baseline count | the widening is proven ADDITIVE before a single routing edit exists |

**Table 2 — POST-ROUTING (Task 11).** Same roots.

| Predicate | Returns |
|---|---|
| `filesystem_mutation_uses` | uses in `obsidian_schemas/vault_io.py` ONLY → Wall A **GREEN** |
| `os_module_attribute_uses`, `module_import_uses` | unchanged outside `vault_io.py` → Walls B, C **GREEN** |
| `functions_calling(files, "stat_stamp")` and `…"remember_snapshot"` | each a superset of the three loaders → Wall D(i) **GREEN** |
| `functions_calling(files, "_adopt")` | EXACTLY the five adopting functions — `base.py:save`, `base.py:update_fields`, `book.py:save`, `meeting.py:save` and `person.py:create_stub`; `base.py:load` is deliberately NOT among them, because it is a bulk rebuild that rebinds once rather than a per-entity adoption — set EQUALITY, so a sixth adoption site written without the door, or an existing one left mutating `_cache` directly, is a mismatch and a hand-back (Edge Cases' adoption-door rule) |
| `functions_calling(files, "parse_markdown_file")` | still exactly the loaders → Wall D(ii) **GREEN** |
| `falsy_returns_in(python_files_under(PACKAGE_ROOT), COMMIT_FUNCTION_NAMES)` | empty, now over a real `vault_io.py` → Wall E **GREEN** |
| `functions_reserializing_parsed_frontmatter(python_files_under(PACKAGE_ROOT))` | the same four `FunctionId`s at `tests/test_loud_fail_parse.py:110-116` (D7 derivation 1) |
| `functions_parsing_then_writing - functions_reserializing_parsed_frontmatter` | `{FunctionId("obsidian_schemas/writer.py", "write_markdown_file")}` (D7 derivation 2) |
| `non_completed_write_sites(python_files_under(PACKAGE_ROOT))` | the same eight `SiteId`s the map at `tests/test_loud_fail_write.py:126-139` classifies (D7 derivation 3) |
| `base_repository_subclasses` / `load_file_implementations` | 4 and 3 — the pins at `tests/test_loud_fail_parse.py:300-301`, unedited (D5) |

### D11. Integration points, at a glance

| File | Change |
|---|---|
| `obsidian_schemas/vault_io.py` | **NEW.** D1–D5. The only filesystem-mutation home — including `ensure_dir`, the namespace cell's one call site (R5). |
| `obsidian_schemas/errors.py` | `StaleEntityWrite`, `ExternalWriteConflict`, `NoteAlreadyExists` (each `LoudFailError`, no `__init__`); three literals into `REASONS:88`; the "twelve" pin at `:84` restated as a predicate. |
| `obsidian_schemas/__init__.py` | Export the three new classes beside the WI-020 six at `:46-53,118-124`. |
| `obsidian_schemas/writer.py` | Door 2 inside `write_markdown_file:154`; delete `:186-187`; WI-126 guard read under the lock; door-1 routing for `:283,333,365`; `allow_unverified_overwrite`; `:233`'s `mkdir` → `ensure_dir`. |
| `obsidian_schemas/repositories/base.py` | Door-1 routing for `update_fields:390`; stamp recording in `_load_file:226`; thread `allow_unverified_overwrite` through `save:294`; **the per-repository `_cache_lock`, the NEW `_adopt(name_key, entity, file_path)` adoption door, and the replace-the-mapping rule** at `__init__:142-144`, `load:176-178,189-192`, `save:331-334`, `update_fields:401-414`, `refresh:434-435,450-453`, `_note_skip:223`, `skipped_notes:202` and `skipped_count:206` (Edge Cases, AC-18). |
| `obsidian_schemas/repositories/person.py` | Door-1 routing for the six body-writer sites; `create_stub:1337` recovery, whose adoption of the winner's entity goes through `base.py`'s `_adopt` like every other (Edge Cases, round 10); thread the keyword through `save:1252`. **`save:1252` still adopts nothing of its own** — it delegates to `super().save()` at `:1266-1267`, so it calls `_adopt` nowhere. |
| `obsidian_schemas/repositories/book.py` | **Stamp recording in `_load_file:57`** (stat above the read at `:66`, record on the entity branch at `:75-76`); thread `allow_unverified_overwrite` through `save:138`; **the cache mutation at `save:173-176` becomes one `_adopt(...)` call** (Edge Cases). |
| `obsidian_schemas/repositories/meeting.py` | **Stamp recording in `_load_file:64`** (stat above the read at `:71`, record on the entity branch at `:79-80`); thread `allow_unverified_overwrite` through `save:160`; **the cache mutation at `save:195-198` becomes one `_adopt(...)` call** (Edge Cases). |
| `scripts/lint_vault.py` | Door-1 routing for `:876,894`; door 3 at `quarantine_garbage:1036-1038`; `:1034`'s `mkdir` → `ensure_dir`. |
| `scripts/migrate_person_to_discuss.py` | Door-1 routing for `:104`. |
| `tests/derivations.py` | D10.1's `SCRIPTS_ROOT` + provenance-partitioned vocabulary + five predicates (`filesystem_mutation_uses`, `os_module_attribute_uses`, `module_import_uses`, `functions_calling`, `falsy_returns_in`); `_is_write_call` widened by `DOOR_NAMES` with its `ast.Attribute` gate untouched. |
| `tests/test_loud_fail_parse.py` | **Table 3a row 1 ONLY** (D12) — the part-3 fault injection moves from `_Path.write_text` to `vault_io.write_note`. Every assertion, and the `write_paths`/`loose_paths` derivations at `:110-137`, unchanged. |
| `tests/test_loud_fail_write.py` | **Table 3a rows 2, 3, 4 ONLY** (D12) — P1's fault injection moves to `vault_io.write_note`; the two AC-4 calls gain `allow_unverified_overwrite=True`. Every assertion, and the `SiteId` classification map at `:126-139`, unchanged. |

**Unchanged by design:** `obsidian_schemas/parser.py`, `models.py`, `identifier.py`,
`name_validation.py`, `name_cleaning.py`, `body_sections.py`, `repositories/company.py` (it declares
neither a `save` nor a `_load_file` of its own, so it inherits both the door and the recording —
which is the many-to-one fact `tests/test_loud_fail_parse.py:301` pins).
`parser.py` stays unchanged deliberately: `parse_markdown_file` is where the bytes are read, but the
stamp must co-move with the entity's ADOPTION into a cache, and the parser cannot know whether its
caller adopted what it returned. Recording there would advance a stamp for a payload nobody kept —
the two-purposes-on-one-field shape (LESSONS #43) that D5's rule exists to close.

**And "unchanged" is now a checkable claim rather than an instruction (round 6).** Each of these
files carries at least one call node whose *name* is in the wall's vocabulary and whose *receiver* is
not a filesystem object — `models.py:110,136` and `person.py:1141` (`str.replace`), `book.py:94,124,
207,255` and `meeting.py:211` (`str.replace`), `parser.py:176,211` (`dict.copy`). Under D10.3's
provenance ruling none of them is a Wall A use, and Table 1's second and third rows assert exactly
that against the untouched tree — which is what makes "the builder does not touch these files"
achievable rather than an instruction Wall A contradicts. `book.py` and `meeting.py` ARE write
targets for their loaders and `save` signatures; their `str.replace` lines are not touched either.

### D12. The behavioural half — what routing MOVES, and how every red is dispositioned

Added round 7. D7 and D10 make this document's claims about **derivations**; this section makes its
claims about **behaviour**, and it exists because the two are not the same kind of claim and cannot
be settled by the same instrument.

#### D12.0 The generator, and why closing five instances is not the fold

Rounds 4–6 closed a class one level down: *a predicate whose effect on the current corpus nobody
executed* (D10.0). Round 6's Fold 2 gave that class its instrument — Task 0 RUNS every wall predicate
before the vocabulary is frozen. The round-6 gates then found the class one level UP, and it is the
same shape with a different subject:

> **Every claim this plan makes about what an EXISTING test returns after routing is a claim about
> BEHAVIOUR, and a behaviour claim is settled by RUNNING the test — never by walking a predicate.**

Five instances were produced by two readers in one round: three by the architect
(`tests/test_loud_fail_write.py:153`'s `Path.write_text` fault injection,
`tests/test_loud_fail_parse.py:450`'s, and `tests/test_loud_fail_write.py:66,89`'s raw-seeded
`write_markdown_file`), two more by the data-premise gate in the first module it read
(`tests/test_writer.py:171` and `:322`). All five were re-verified in code this round. The rate is
the evidence: enumeration is not converging, and a sixth instance is what round 8 would be. So this
section does the two things the class needs — it **sweeps the generating axes at source** and it
**gives the class an instrument that runs**, exactly as Fold 1 and Fold 2 did one level down.

#### D12.1 The axes, swept by their declaring shape

Routing moves behaviour along exactly three axes. Each is swept by grepping the shape that DECLARES
membership, over `tests/` — never by recalling which tests looked relevant.

| Axis | What routing moves | Declaring shape swept | Result |
|---|---|---|---|
| **α — commit-call identity** | `Path.write_text` stops being where package code commits bytes (D2 commits through an fd), so a fault injected there is never injected | `setattr(<Path>, "write_text"\|"write_bytes", …)` under `tests/` | **2 sites** — `tests/test_loud_fail_write.py:153`, `tests/test_loud_fail_parse.py:450` (plus their two restore calls at `:157` and `:453`) |
| **β — outcome against an UNOBSERVED path** | D8 step 5's zero case fires on `stamp is None`, so an `overwrite=True` write against a path this process did not derive an entity from raises `NoteAlreadyExists` | every `write_markdown_file(` call and every `.save(` call under `tests/`, each read to establish how its target came to exist | **4 sites** — `tests/test_loud_fail_write.py:66`, `:89`; `tests/test_writer.py:171`, `:322` |
| **γ — create-collision exception type** | `FileExistsError` → `NoteAlreadyExists` (D8b) | `FileExistsError` under `tests/` | **1 site** — `tests/test_writer.py:test_no_overwrite_by_default:146` |

**The β sweep read all 27 call sites rather than sampling them**, and the negative result is the part
that matters: the 17 `write_markdown_file(` calls are at `tests/test_loud_fail_write.py:66,89` and
`tests/test_writer.py:111,137,153,171,186,322,358,366,377,383,390,397,404,411,423`; the 10 `.save(`
calls are at `tests/test_repositories.py:644,661,676,693,709,725` and
`tests/test_writer.py:432,434,440,441`. *(That last group is four, not the two
`## Verified Diagnosis` claim 8 named before this round; claim 8's load-bearing half — that every one
of them is a `PersonRepository` — is unaffected and the count is corrected there too.)*
Everything not in the table above is green for a stated reason, and the reason is one of exactly
three: **(i)** the target does not exist, so the zero case IS a create and succeeds
(`test_writer.py:111,137,186,390`; all six `test_repositories.py` saves, whose names are fresh in
`temp_vault`; `test_writer.py:432,440`); **(ii)** the target was committed THROUGH door 2 earlier in
the same test, so step 8 registered its stamp and the follow-up takes the 2u path
(`TestBodyShrinkGuard._seed` at `test_writer.py:358` feeds `:366,377,383,397,404,411,423`;
`test_writer.py:434` follows `:432`, and `:441` follows `:440`); **(iii)** a repository loaded the
target first, so a loader recorded it (every `create_stub`/`resolve_or_create` path —
`create_stub`'s own guard calls `self.get(...)`, which runs `_ensure_loaded()` at
`obsidian_schemas/repositories/base.py:get:258-269`). Note that `BaseRepository.save` does **not**
call `_ensure_loaded()`, which is why (iii) has to be established per site rather than assumed.

**The β axis is WIDER than the shape that declares it, and the two escapes are named rather than
left to the fourth branch (round 8, the round-7 architect's note #1).** The declaring shape swept
above is "every `write_markdown_file(` call and every `.save(` call under `tests/`", which finds
every site that *calls* a door; the AXIS, though, is "the target exists and this process holds no
stamp for it", and reason (iii) discharges a site by asserting a load happened. Two ways a load can
happen and still leave no stamp:

- **The note exists on disk and does not parse.** It lands in `_skipped`
  (`obsidian_schemas/repositories/base.py:223`) and never in `_cache`, so no entity derives and
  `remember_snapshot` is never reached (D5's own paragraph says so). A later `save()` against that
  path is the zero case and raises `NoteAlreadyExists`.
- **The note is created on disk AFTER `_ensure_loaded()` ran.** The load-once cache is not
  re-stat-ed (`## Verified Diagnosis` claim 3), so a target that appeared between the load and the
  write carries no stamp however thoroughly the repository was loaded.

Neither has an instance in `tests/` today — that is why the sweep returned four sites and not six —
but both are R-β in kind, not a fourth-branch unknown. **Ruled: a Task-16 red whose check matches
either shape is R-β and takes `allow_unverified_overwrite=True`, and the Build Log records WHICH of
the two it was.** Everything else outside Table 3a remains D12.4's fourth branch. The point of
writing this down is that the builder meets a Table rule rather than a judgement call at the one
boundary where the sweep's declaring shape and its axis are known to disagree.

#### D12.2 The (α)/(β)/(γ) fork, ruled

The round-6 architect named three resolutions and required the choice be written. Ruled together
with D5's consumer cell, because they are one decision seen from two sides:

- **(α) Make `vault_io`'s temp write name `Path.write_text` so the injected fault still fires.**
  **Rejected.** It collides with D2's durability requirement — `write_text` leaves no file descriptor
  to `os.fsync`, and un-fsynced bytes behind an `os.replace` is the torn-write class this item exists
  to kill, re-introduced to keep a test's patch point. It also puts `vault_io` inside
  `_is_write_call`'s universe, which falsifies D1's derivation that the new file enters none of
  WI-020's four sweeps and makes Wall E's justification circular.
- **(β) Re-admit the two WI-020 acceptance modules as write targets and move the injection points.**
  **ACCEPTED, and this is a written reversal of round 6's withdrawal.** Round 6 withdrew them because
  a *contingency* licence hands a caged builder permission to edit a previous item's shipped battery
  at exactly the moment a red makes that the cheapest green. The reversal removes the licence rather
  than restoring it: the permitted edits are **enumerated line by line ahead of the build** in
  Table 3a, the asserted PROPERTY of each is unchanged, and every other red in those modules is a
  hand-back. The edits are possible at all only because of D7's module-attribute call-form ruling —
  a site that calls `vault_io.write_note(...)` resolves the door at call time, so
  `setattr(vault_io, "write_note", …)` reaches it; under a `from … import write_note` form it would
  not. The call form and the fault-injection fix hold each other up.
- **(γ) Narrow the zero case so `overwrite=True` against an existing unstamped target is not a
  create.** **Rejected in writing, with its consumer-facing consequence stated: it re-opens the
  concurrent-create clobber.** `BaseRepository.save` defaults `overwrite=True`
  (`obsidian_schemas/repositories/base.py:save:299`), so `create_stub`'s losing write is itself an
  `overwrite=True` write with no stamp — the exemption would exempt precisely the path door 2c was
  minted for, and property 1 of `## Approach`'s total rule would stop being total. The full ruling,
  including why the exported parser is not made an observation point instead, is in D5, "The cell
  Wall D(ii) cannot reach".

#### D12.3 Table 3 — the disposition set and the post-routing floor

**Table 3a — every site the D12.1 sweeps returned, its class, its permitted edit, and its owner.**
This is the COMPLETE set of edits to existing test modules that this item authorises. A red anywhere
else is D12.4's fourth branch.

| # | Site | Axis | Permitted edit — and nothing else | Lands in |
|---|---|---|---|---|
| 1 | `tests/test_loud_fail_parse.py:test_error_chains_are_bounded:412`, part 3 (`:445-453`) | α | Inject the `OSError` at `vault_io.write_note` instead of `_Path.write_text`: `monkeypatch.setattr(vault_io, "write_note", deny)`. The asserted outcome is unchanged — `WriteFailedError` with `caught.value.__cause__ is boom` | Task 4 |
| 2 | `tests/test_loud_fail_write.py:_check_write_failure_raises_and_noops_keep_their_return:110`, P1 (`:152-157`) | α | Same move: `monkeypatch.setattr(vault_io, "write_note", …throw(boom))`, restored the same way. The asserted outcome is unchanged — `repo.append_to_timeline(...)` raises `WriteFailedError` | Task 5 |
| 3 | `tests/test_loud_fail_write.py:_check_body_guard_refuses_when_unverifiable:58` (`:66`) | β | Add `allow_unverified_overwrite=True` to that one call. The asserted outcome is unchanged — `UnverifiableBodyError`, not `BodyTruncationError`, and `a` byte-identical | Task 7 |
| 4 | `tests/test_loud_fail_write.py:_check_body_guard_refuses_when_unverifiable:58` (`:89`) | β | Same keyword on that one call. Asserted outcome unchanged | Task 7 |
| 5 | `tests/test_writer.py:test_overwrite_when_requested:158` (`:171`) | β | Same keyword. `allow_body_replacement=True` stays and still governs the body; asserted outcome unchanged | Task 7 |
| 6 | `tests/test_writer.py:test_roundtrip_preserves_data:287` (`:322`) | β | Same keyword — this is the README recipe, and the keyword IS the documented consumer answer (D5). Asserted outcome unchanged | Task 7 |
| 7 | `tests/test_writer.py:test_no_overwrite_by_default:146` (`:152`) | γ | `pytest.raises(FileExistsError)` → `pytest.raises(NoteAlreadyExists)` (D8b) | Task 14 |

Rows 3–6 all land the SAME keyword for the SAME reason, which is the test that they are one ruling
rather than four patches: each call is a caller writing to a path it seeded itself and never asked
this package to observe, and `allow_unverified_overwrite=True` is that sentence written down.

**Table 3b — the complete expected floor state at the Task-16 boundary** (after Tasks 1, 0, 2–7 and
rows 1–6 of Table 3a, before Task 14). Task 16 runs THE FLOOR and records the WHOLE red set:

| Expected | Value |
|---|---|
| Failing checks | **exactly one** — `tests/test_writer.py::TestWriteMarkdownFile::test_no_overwrite_by_default`, raising `NoteAlreadyExists` where the test expects `FileExistsError` |
| Every other module, `tests/test_loud_fail_parse.py` and `tests/test_loud_fail_write.py` included | GREEN |
| Passing case count | ≥ Task 1's baseline minus one. Reported as a PROPERTY against the recorded baseline, never as a hardcoded number |

#### D12.4 The disposition rule — total, with a loud fourth branch

Task 16 does not repair anything. It records, classifies, and stops. A red in the routed tree is
**exactly one** of:

> **R-α** the check forces a failure at `Path.write_text`/`Path.write_bytes` → move the injection to
> the door the routed site now calls, asserting the identical exception type and the identical
> `__cause__` relation. **R-β** the check writes bytes to a path by a route the registry does not
> observe and then calls `write_markdown_file`/`save` with `overwrite=True` → add
> `allow_unverified_overwrite=True` to that call. **R-γ** the check asserts `FileExistsError` from
> `write_markdown_file` → `NoteAlreadyExists`. **Anything else → HAND BACK to the conductor**,
> naming the check, its assertion and the Table-3 row that failed to predict it.

The fourth branch is the point. Rows 1–7 are what the sweeps returned; a red they did not return
means an axis this section did not name, which is a spec defect and not a builder's judgement call —
LESSONS #5's shape at a disposition boundary, where the unenumerated case must fail LOUD rather than
be absorbed by the nearest-looking rule. The builder must not widen R-β to cover a red it does not
literally describe, and must not "fix" a check by weakening its assertion: **the asserted property of
every existing check is invariant across every permitted edit above**, and any repair that changes
what a check PROVES is a hand-back regardless of which class it appears to fall into.

#### D12.5 The next level of the ladder, swept and DECLARED

Above the three axes sits the question *what else does routing change that no predicate can see?*
Swept over the tree this round rather than left for round 8:

1. **Read-error surfacing.** A routed site's `read_text` becomes `vault_io.read_note`, so the class
   of exception reaching the site's own `except` is part of the contract. Ruled in D1: `read_note`
   wraps nothing, and `tests/test_loud_fail_parse.py:462-471` (part 4, the `UnicodeDecodeError`
   whose cause must NOT chain) therefore needs no edit and appears in no Table-3 row.
2a. **The new file entering an existing TEST-side sweep.** D1's closing paragraph derives
   `vault_io.py`'s effect on WI-020's four derivation sweeps; the same question on the acceptance
   side has one answer. `tests/test_vault_path_required.py:test_no_implicit_vault_path_defaults:312`
   rglobs every `*.py` under `obsidian_schemas/` and `scripts/` (`:320-321`) and asserts zero live
   occurrences of `expanduser`, `Path.home()` or `/Users/`. `vault_io.py` joins that universe, so it
   is a **hard constraint on Task 3**: the module resolves its sentinel home from
   `OBSIDIAN_SCHEMAS_LOCK_DIR` or from the note's own directory (D3), and must name no user-home
   default of any kind. `tests/test_vault_path_required.py:423`'s `*.md` rglob is a docs scan and
   is untouched. Neither is a Table-3 row; both are constraints the builder must not discover.
2. **Lock side effects on a test vault.** Every write now creates
   `<note dir>/.obsidian-schemas-locks/`. Swept: the only directory-listing assertion under `tests/`
   is `tests/test_loud_fail_load.py:190`, and it is a SUBSET check (`note.path.name in written`), so
   an added dot-directory does not move it. `PersonRepository.load` globs `@*.md`
   (`obsidian_schemas/repositories/base.py:load:186`) and cannot match a directory.
3. **`mkdir` → `ensure_dir`.** `tests/test_vault_path_required.py:265` and `:117-126` patch
   `Path.mkdir` to prove the unconfigured guard raises before any filesystem touch. `ensure_dir` is
   still a `Path.mkdir` call, and nothing about it moves earlier than the guard, so both stay green.
4. **A door-1 write followed by a `save()` on the same path in one process.** Door 1 does not touch
   the registry (D5), so the stamp goes stale against the disk and the following door-2u `save()`
   raises `StaleEntityWrite` even though the cached entity's FRONTMATTER is still current. The only
   in-package sequence of that shape is `BaseRepository.update_fields`, which re-reads through
   `self._load_file(...)` at `obsidian_schemas/repositories/base.py:393` and re-registers — that is
   why `_writeback_identifier` routes through `update_fields`
   (`obsidian_schemas/repositories/person.py:_writeback_identifier:1189`, `:1214`) rather than
   `save()`, and why it stays green. A consumer sequence has no such re-read: declared as **R12**,
   with the remedy named, and NOT closed by making the body writers re-register — that would advance
   a stamp for a payload nobody re-derived, which is the LESSONS #43 shape D5's rule exists to close.

   **Consumer-facing consequence, stated as plainly as 2u's and 2c's (round 8, the round-7
   architect's note #4).** R12 has been carried as a residual paragraph rather than as a break, and
   that undersold it: `repo.append_to_timeline(person, "### note\n")` followed by `repo.save(person)`
   **in one process, with no second writer anywhere**, raises `StaleEntityWrite` where it succeeds
   today. That is an ordinary consumer sequence — HAL9000 appends a Timeline entry and then persists
   a field change — and unlike 2u's and 2c's breaks it is reachable without concurrency at all, which
   makes it the most likely of the three to be met first. The refusal is correct and is not being
   softened: at the stamp level a door-1 write to the body is indistinguishable from
   `update_frontmatter_field`'s write to the frontmatter, which is the case AC-4 exists to catch. The
   named answer is the one already in the tree — re-read through the repository between the two
   calls, i.e. `repo.refresh()` or the `update_fields` path `_writeback_identifier` already uses
   (`obsidian_schemas/repositories/person.py:_writeback_identifier:1214`) — and, for a consumer that
   wants to measure before adopting, `OBSIDIAN_SCHEMAS_WRITE_GUARD=observe`. It is Risk row 17, and
   close-out step 3's consumer audit sweeps for it by name.
5. **Registry newer than a live cache.** Declared as **R13** in D5 — the fail-OPEN direction of the
   adoption sweep, with no in-package instance today.

Items 1–3 are closed with no edit; items 4–5 are residuals with named remedies. A red arising from
any of them is still D12.4's fourth branch, because none of them is an R-α/R-β/R-γ member.

## Edge Cases & Open Questions

- **Empty / null / malformed input.**
  **Case:** `write_note` is handed an empty string; a note's frontmatter does not parse; a path is
  `None` or `""`.
  **Decision:** an empty `text` is a legitimate payload and is written (a caller may legitimately
  empty a note; the WI-126 guard is what refuses an *unintended* body loss, and it is unchanged). A
  note whose frontmatter does not parse never reaches a door with a derived payload — WI-020's
  raising parse fires first, and `write_markdown_file`'s `UnverifiableBodyError` at
  `obsidian_schemas/writer.py:205-209` still refuses an overwrite the guard cannot verify. A falsy
  path raises `WriteFailedError` at the door rather than resolving to the current directory.
  **Reasoning:** LESSONS #5 — empty is a bug shape at a *precondition*, never at a payload. The
  distinction is preserved by putting the fail-closed behaviour on the stamp (absent stamp → strictest
  case) and leaving the payload permissive.

- **Race conditions / concurrent access.** This is the item. Every branch is enumerated in D4, D8 and
  D9; the residual list R1–R14 in `## Approach` states what is left uncovered. R1 is reproduced
  verbatim in `## Verification` and a spec claiming total external safety should fail review.

- **External dependency failure.**
  **Case:** `filelock` is not importable; the lock sentinel directory cannot be created; the lock
  times out; the disk is full mid-write.
  **Decision:** an unimportable `filelock` is a build-time abort (Task 1), not a runtime path — the
  package declares it as a dependency. Sentinel-directory creation failure, lock timeout and a
  `write`/`fsync` `OSError` all raise `WriteFailedError` with the existing reason
  `"write did not complete"`, chained through `chainable_cause` (`OSError` is in `CHAINABLE`,
  `obsidian_schemas/errors.py:184`).
  **Reasoning:** WI-020's floor already fixed the vocabulary for "a write path did not complete";
  minting a fourth exception for a fourth cause would multiply the surface without giving a caller a
  different action.

- **First-run vs subsequent-run.**
  **Case:** the first write against a vault has no `.obsidian-schemas-locks/` directory, and no note
  has a stamp.
  **Decision:** the sentinel directory is created idempotently on first lock acquisition
  (`mkdir(parents=True, exist_ok=True)`, R5). A repository that has not yet `load()`-ed holds no
  stamps, so its first `save()` of an existing note is refused as a create. `BaseRepository` sets
  `auto_load=True` by default (`base.py:124`) and `save()` is reached through methods that
  `_ensure_loaded()`, so the ordinary path is stamped; the `auto_load=False` path is the declared
  exception and its remedy is `load()`/`refresh()`, or the explicit escape.
  **Reasoning:** fail-closed on the first run is the correct direction for a corruption-class item.

- **Migration / backfill.**
  **Case:** existing vault notes carry no state this item introduces.
  **Decision:** none needed. There is no on-disk schema change, no new frontmatter field and no
  index to rebuild. Lock sentinels are created on demand and are disposable; deleting the whole
  `.obsidian-schemas-locks/` tree while no writer is running is safe and loses nothing.
  **Reasoning:** the state this item adds is process-local (D5) and filesystem-derived.

- **Idempotency.**
  **Case:** a caller retries `save()` after `StaleEntityWrite`, or re-runs a whole batch.
  **Decision:** each door is idempotent in the sense that matters — re-running the same write with a
  refreshed stamp converges. It is deliberately NOT idempotent in the sense of "re-running blindly
  succeeds": that is the refusal. `create_note` on an existing path always raises; `move_note` on an
  already-moved note raises `FileNotFoundError` for the source.
  **Reasoning:** a retry must re-derive from fresh state or it re-commits the same lost update.

- **Retry semantics.**
  **Case:** which failures should a caller retry?
  **Decision:** `ExternalWriteConflict` and `StaleEntityWrite` are retryable — re-read (door 1) or
  `refresh()` + re-apply (door 2), then re-attempt. `NoteAlreadyExists` is *not* retryable; it is a
  resolution outcome and the caller either reuses the existing note or surfaces it.
  `WriteFailedError` is not retryable without operator intervention. The three retryable/terminal
  classes are distinguishable by type, which is why `## Approach` requires them to be distinct from
  `WriteFailedError`.
  **Reasoning:** blanket retry on a `LoudFailError` would spin on a full disk.

- **Partial failure.**
  **Case:** `scripts/lint_vault.py`'s fix loop is 3 files into 50 when one raises; `move_note` links
  the destination and then fails to unlink the source.
  **Decision:** the fix loop's existing per-file `try` at `scripts/lint_vault.py:896-897` already
  isolates each file and is unchanged, so a refusal on one note does not abort the batch. A
  `move_note` that links and then fails to unlink leaves BOTH paths present and raises
  `WriteFailedError` naming both — a duplicate is recoverable by hand, a lost note is not, so the
  link-then-unlink order is chosen deliberately over unlink-then-link.
  **Reasoning:** at every partial-failure fork, prefer the state a human can repair.

- **Error propagation.**
  **Case:** what does a consumer see?
  **Decision:** `except LoudFailError` catches every refusal this item adds. `StaleEntityWrite`,
  `ExternalWriteConflict` and `NoteAlreadyExists` each carry `path` and route their message through
  `bounded_message`, so no note content and no foreign exception rendering reaches the message.
  `NoteAlreadyExists` replaces `FileExistsError` on `write_markdown_file` — a real, declared break
  (D8b, `## Risk Analysis`).
  **Reasoning:** WI-020's contract, extended rather than forked.

- **Trust boundary crossings.** Covered in D0.7. The boundary is the filesystem; the validation is
  the stat precondition; nothing crossing it is interpolated into a message.

- **Concurrent creates of the SAME note by two threads of one process.**
  **Case:** two threads call `create_stub("Jane Doe")` simultaneously.
  **Decision:** the per-path `threading.RLock` serializes them; the loser's `create_note` hits an
  existing destination and takes the same `NoteAlreadyExists` recovery as the cross-process loser.
  **Reasoning:** the in-process and cross-process paths converge on one mechanism, which is what
  absorbs the original March thread-safety scope without a second design.

- **The repository cache under concurrent mutation (the original March scope).**
  **Case:** one thread `refresh()`es while another iterates `get_all()`.
  **Decision:** `BaseRepository` gains a single per-repository `threading.RLock` guarding mutation of
  `_cache`, `_file_map` and `_skipped`, and **every mutation of the two mappings REPLACES the
  container rather than mutating a live one** — see the rule below, which is what makes the
  lock-free read side true rather than aspirational. AC-18 is its oracle and Task 7 lands it.
  **Reasoning:** the doc's own framing — "make repositories safe for multi-threaded servers without
  serializing all access behind a single lock".

  **The rule, stated once over the whole mutation surface (round 9).** A lock taken on the writers
  and skipped on the readers buys a lock-free reader NOTHING while `load` still does
  `self._cache.clear()` at `obsidian_schemas/repositories/base.py:load:176-178` and repopulates
  key-by-key at `:190-191`: a concurrent `get_all()` (`base.py:get_all:271`, `list(self._cache.values())`
  at `:279`) sees a COMPLETE list of a HALF-BUILT cache, and a concurrent iterating read —
  `person.py:get_by_role:1233`, `book.py:262` (`for title, book in self._cache.items()`),
  `company.py:130`, `meeting.py:402` — can raise `RuntimeError: dictionary changed size during
  iteration`. Neither is fixed by a lock the reader does not take. So:

  > **Every mutation of `_cache` and `_file_map` happens under the repository's `threading.RLock`
  > and REPLACES the mapping: the mutator builds a new dict (a fresh one in `load`, a
  > `dict(self._cache)` copy elsewhere), mutates that, and rebinds the attribute in one critical
  > section. No live mapping is ever mutated in place. `_skipped` is the one container whose two
  > readers — `skipped_notes` (`base.py:202`) and `skipped_count` (`:206`) — also take the lock,
  > because it is an append-only diagnostic no hot path reads. Every OTHER read path takes no lock
  > and is correct by construction: the container it obtained is never mutated afterwards.**

  **The mutation surface is DERIVED, and derived over the tree this plan PRODUCES rather than the
  tree it starts from (round 10).** Round 9 stated the surface as a grep result — "nine sites in five
  functions" — run against today's tree. That enumeration was correct about today and wrong about
  the build: **this item's own Task 8 adds a TENTH site**, in `person.py:create_stub`, the one file
  the round-9 text and D11 both declared needed no lock. A list derived over the PRE-change tree
  cannot reach a site the change creates, so the rule is restated as a DOOR the surface is total
  through by construction, exactly as D5's (A′) made the loader corpus total rather than listing it:

  > **`BaseRepository` gains ONE adoption method, `_adopt(name_key, entity, file_path)`. It takes
  > `_cache_lock`, builds `dict(self._cache)` and `dict(self._file_map)`, sets `name_key` in each
  > copy, rebinds both attributes, and calls `_index_entity(entity, name_key)` — the same three-part
  > adoption every existing site already performs — in one critical section. EVERY site that adopts
  > ONE entity calls it, and after this item there are exactly two other places in the package that
  > write `_cache` or `_file_map` at all: `load`, which rebuilds the WHOLE mapping, and
  > `update_fields`' removal half, which deletes a key. A per-entity mutation of `_cache` or
  > `_file_map` written anywhere else is the defect, not a variant.**

  **The FOUR existing single-entity sites the door replaces, each verified to be the identical
  three-part shape** (`_cache[k] = entity`, `_file_map[k] = path`, `_index_entity(entity, k)`, in
  that order): `base.py:save:331-334`, `base.py:update_fields:412-414`, `book.py:save:173-176` and
  `meeting.py:save:195-198`. **The fifth is Task 8's**, in `person.py:create_stub`'s
  `NoteAlreadyExists` recovery, and it is the reason the door exists rather than a fifth entry on a
  list. Three sites are NOT single-entity adoptions and keep their own rule under the same lock, and
  each is written out here so "everything goes through the door" is not read past its one honest
  boundary:

  - **`load` (`:176-178`, `:186-193`) is a BULK rebuild and must NOT call `_adopt` per note.** It
    binds fresh local `new_cache` / `new_file_map`, fills them key-by-key across the vault walk,
    calls `_index_entity` per entity, and rebinds both attributes ONCE at the end, holding
    `_cache_lock` across the whole walk. A per-note `_adopt` here would publish a half-built vault
    once per note instead of never — the opposite of what the rule buys — and it would copy the whole
    mapping N times. The live `self._cache.clear()` at `:176-178` is deleted, not locked.
  - **`update_fields`' removal half (`:401-410`)** builds its copies, deletes the old key from them,
    and its `_adopt(...)` call at `:412-414` closes the same critical section.
  - **`refresh` (`:434-435`, `:450-453`) and `_note_skip` (`:223`, `_skipped` only)** take the lock
    and are not adoptions at all.

  `person.py:save:1252` delegates to `super().save()` at `:1266-1267` and adopts nothing itself, so
  it calls `_adopt` nowhere — that remains true, and it is now a consequence of the door rather than
  a per-file instruction.

  **What makes this checkable rather than an instruction: `_adopt` is the door, and Task 12's Wall D
  battery already owns the predicate that finds callers.** `functions_calling(files, "_adopt")` must
  equal EXACTLY the five adopting functions after routing — `base.py:save`, `base.py:update_fields`,
  `book.py:save`, `meeting.py:save` and `person.py:create_stub`; `load` is deliberately NOT among
  them — that is Wall D's own function over a new name, no
  new machinery, and it is pinned as a Table-2 row so a sixth adoption site added later without
  the door, or an existing one left mutating `_cache` directly, is a RED floor rather than the next
  round's finding. The oracle for the BEHAVIOUR is AC-18; the oracle for the SURFACE is that row.
  **Lock ordering, so this cannot deadlock against Layer 2:** the repository lock spans the CACHE
  MUTATION only, never the filesystem write — `save` takes it for `base.py:331-333` and not around
  its `write_markdown_file` call, `update_fields` for `:399-413` and not around its door-1 write —
  so no thread ever holds the repository lock while acquiring `note_lock`, and `note_lock` is never
  held while acquiring the repository lock. `load` is the one long hold (it spans the vault walk);
  that blocks a concurrent WRITER for the duration of a refresh, which is correct behaviour rather
  than a defect, and blocks no reader at all.
  **What this rule does NOT cover, declared rather than left as the next round's finding:** the
  subclasses' own indexes (`_status_index`, and the alias/email indexes `_index_entity` /
  `_remove_entity_from_indexes` / `_clear_indexes` maintain) are mutated in place under the same lock
  by the same adopting and removing functions, but their readers are lock-free and copy-on-write is
  NOT specified for them. A lock-free index read concurrent with a `refresh()` can therefore still
  observe a partial index. That is unchanged from today, and it is declared here so its absence from
  AC-18 is a ruling rather than a gap.

  **And the declared bound has TWO halves, which are not the same claim — stated so a later reader
  does not take the re-check argument as covering both** (round 10, the round-3 threat model's
  non-blocking note 1). *(i) The wrong-VALUE half is closed:* every index lookup ends in
  `self._cache.get(cache_key)` — `person.py:454`, `:459`, `:476`, and the re-checks at `book.py:194`,
  `meeting.py:256`, `:299`, `:314` — so a partial index degrades to a MISS and can never resolve to
  the wrong person. *(ii) The iterate-a-live-mapping half is NOT closed:* `get_by_phone`'s fuzzy
  fallback at `obsidian_schemas/repositories/person.py:457` does
  `for indexed_phone, cache_key in self._phone_index.items()`, which is precisely the
  `RuntimeError: dictionary changed size during iteration` shape AC-18 exists to kill one level up on
  `_cache`. It is pre-existing, it is loud rather than silent, and it is fenced by a written
  `## Scope Boundary` entry — the threat model explicitly declines to require it — but the re-check
  argument in (i) does not reach it, and writing that down is what stops the next round from reading
  one bound as two.

OPEN: None.

## Implementation Plan

Tasks are ordered by dependency; the builder follows top to bottom. Tasks 4, 5 and 6 are
independent of each other and may be done in any order once Task 3 lands.

**Execute in CHECKBOX ORDER, top to bottom. The ordinals are stable identifiers, not the sequence.**
Task 0 sits below Task 1 (round 6) and Task 16 sits between Tasks 7 and 8 (round 7); both were given
free ordinals rather than renumbering, so that no `Task N` cross-reference elsewhere in this document
drifts. Where a task's text and its ordinal disagree about order, the text wins.

**Task 0 comes before everything for one reason (round 6): the vocabulary and the harness predicates
are landed and EXECUTED against the untouched tree before a single routing edit exists.** Rounds 4
and 5 produced four findings between them and every one was a predicate nobody had run. Task 0 turns
that from a review activity into the first ten minutes of the build, and its output is a pinned table
a later red is measured against — so a red at Task 12 is a hand-back with evidence rather than an
invitation to edit the wall.

**Every command below is run from the repository root and is written relative to it.** The absolute
form in `CLAUDE.md` names the live checkout; a build worktree's path is not knowable in advance, so
deriving anything from it — a prefix, a substring, a layout — is the WI-149 trap. THE FLOOR is:

```
.venv/bin/python -m pytest tests -q
```

- [x] **Task 1 — Precondition gate and baseline capture.** Run
      `.venv/bin/python -c "import filelock; print(filelock.__version__)"`. If it fails, **ABORT
      the build** and hand back to the conductor with the D0.1 precondition text — do NOT substitute
      `fcntl`, do NOT edit `pyproject.toml`, do NOT `pip install`. Then run THE FLOOR and record the
      PRE-BUILD passing case count in the Build Log — this is the baseline every later "case count
      did not go down" claim is measured against, captured before the first edit that moves it.
      *Verify:* the import prints a version, and the Build Log contains a line
      `baseline: N passed` with a concrete N.

- [x] **Task 0 — Land the harness predicates and RUN them against the untouched tree.** *Numbered 0
      because it is the plan's zeroth substantive edit — it lands the measuring instruments before
      anything they measure — and written below Task 1 because Task 1 is an abort gate that must
      occupy the build's first minute. Execute in checkbox order, top to bottom: Task 1, then Task 0,
      then Task 2 onward.* This task
      edits `tests/derivations.py` ONLY. Add `SCRIPTS_ROOT`, `DOOR_NAMES`, `PATH_MUTATION_NAMES`,
      `MODULE_MUTATION_NAMES`, `FS_MODULES`, `OS_READONLY_NAMES`, `COMMIT_FUNCTION_NAMES`, and the
      five predicates `filesystem_mutation_uses`, `os_module_attribute_uses`, `module_import_uses`,
      `functions_calling(files, name)` and `falsy_returns_in(files, names)` per D10.1–D10.2. Widen
      `_is_write_call:189` to `{"write_text", "write_bytes"} | DOOR_NAMES` and change **nothing else
      about it** — its `isinstance(node.func, ast.Attribute)` gate stays, because D7 rules every door
      call to be a module attribute. `functions_calling` and `falsy_returns_in` are built on the
      existing `_called_names:167` / `_own_body_nodes:148` / `_is_falsy_return:518` helpers rather
      than a second traversal. `load_file_implementations:355` and `base_repository_subclasses:312`
      are consumed AS THEY ARE: do not edit them, and do not edit the pins at
      `tests/test_loud_fail_parse.py:300-301` that assert over them. All new predicates read parsed
      syntax, never source text.
      **Then EXECUTE each predicate against the untouched tree and paste its result into the Build
      Log**, via a read-only one-liner per row of D10.6 Table 1, e.g.
      `.venv/bin/python -c "import sys; sys.path.insert(0,'.'); from tests.derivations import *;
      [print(u) for u in filesystem_mutation_uses(python_files_under(PACKAGE_ROOT, SCRIPTS_ROOT))]"`.
      Compare EVERY row against Table 1. **If any row differs — in particular if the `str.replace` or
      `dict.copy` rows return anything at all — ABORT and hand back to the conductor naming the row.
      Do NOT remove a name from a vocabulary, do NOT add an exemption, and do NOT edit Table 1.**
      **Count-pin ruling for the corpus THIS task grows (round 10; the rule is that the count-pin
      sweep covers every countable corpus this item GROWS, not only the ones it edits).** This task
      adds seven names to `tests/derivations.py`'s shared-derivation exports, which is a countable
      corpus with a live pin: `tests/test_loud_fail_harness.py:_check_derivations_are_single_sourced:66`
      builds `six = {...}` and asserts `len(six) == 6` at `:72-81`. **Verdict: the pin stays GREEN and
      must NOT be edited** — the dict is a hand-listed required SUBSET of six named exports, not a
      cardinality bound on the module, which that check's own comment states in as many words at
      `:70-71` ("A seventh shared derivation extends this list; it is a required subset, not a
      cardinality bound on the module"). Naming it here makes the sweep's silence a ruling rather
      than an omission. If it goes red, that is a hand-back, not an edit to the pin.
      *Verify:* the Build Log carries every Table-1 row with its actual output, each matching
      what D10.6 declares; the Build Log records `len(six) == 6` still passing in
      `tests/test_loud_fail_harness.py`; and THE FLOOR is GREEN at exactly Task 1's baseline count — which is the
      derivation, not the prediction, that `DOOR_NAMES` is additive against a tree with no door calls
      in it.

- [x] **Task 2 — Mint the three exceptions and de-pin the REASONS count.** In
      `obsidian_schemas/errors.py`: add `StaleEntityWrite`, `ExternalWriteConflict` and
      `NoteAlreadyExists`, each subclassing `LoudFailError` and **declaring no `__init__`**; add
      their three reason literals to `REASONS` (`obsidian_schemas/errors.py:REASONS:88`) in the SAME
      edit, because `bounded_message` (`:109-120`) raises on any reason outside the set — a subclass
      minted without its literal raises at first construction, i.e. exactly when the conflict it
      exists to report occurs. Restate the comment at `obsidian_schemas/errors.py:84` from "Exactly
      the twelve literals of the construction table below" to a predicate with no number in it.
      Export all three from `obsidian_schemas/__init__.py` beside the WI-020 six (`:46-53`, `:118-124`).
      **Count-pin sweep, declared over every countable corpus this item GROWS OR EDITS — not only
      the ones it edits (round 10).** The corpora are (i) `REASONS` — swept by
      grepping its declaring symbol `REASONS` across the tree and reading every file the sweep
      reaches; the only pin is the prose one at `errors.py:84`, and no test asserts `len(REASONS)`;
      (ii) the `BaseRepository` subclass corpus, whose declaring symbols are
      `tests/derivations.py:base_repository_subclasses:312` and
      `tests/derivations.py:load_file_implementations:355` — the pins are
      `tests/test_loud_fail_parse.py:300` (`== 4`) and `:301` (`== 3`), and this item adds no
      repository, so both stay true and must NOT be edited; and (iii)
      **`tests/derivations.py`'s shared-derivation exports**, which Task 0 GROWS by seven names — its
      pin is `tests/test_loud_fail_harness.py:72-81`'s `six = {...}` / `assert len(six) == 6`, its
      verdict is GREEN-and-untouched, and both are ruled in Task 0 where the growth happens. A corpus
      this item adds to is inside the sweep exactly as one it rewrites is; that generalisation is the
      point of naming (iii) rather than the specific pin.
      *Verify:* `.venv/bin/python -c "from obsidian_schemas import StaleEntityWrite,
      ExternalWriteConflict, NoteAlreadyExists as N; raise N('a note already exists at the
      destination')"` raises with a bounded message; the floor is GREEN.

- [x] **Task 3 — Build `obsidian_schemas/vault_io.py`.** Implement D1–D5: `NoteStamp`, `note_lock`,
      `read_note`, `write_note`, `create_note`, `move_note`, `ensure_dir`, the snapshot registry and
      its accessors — `stat_stamp`, `remember_snapshot`, `record_snapshot`, `snapshot_stamp`,
      `forget_snapshot`, `clear_snapshots` — `guard_mode`, and the three env-var readers of D6.
      `stat_stamp` and `remember_snapshot` are SEPARATE from `record_snapshot`: the read-side
      observation points must stat before they read and record after they know an entity was derived
      (D5), which one stat-now call cannot express. No function in the module returns a falsy value
      (D1), and `read_note` wraps NOTHING — `FileNotFoundError`, `OSError` and `UnicodeDecodeError`
      propagate unwrapped, which is what keeps WI-020's chain contract intact at every routed site
      (D1, D12.5 item 1). Do not import `ast`. **Beyond `obsidian_schemas/vault_io.py` and the four
      checks the verify below authors into `tests/test_concurrent_access.py`, touch no other file in
      this task** — both are declared `## Write Targets` entries; nothing else is.
      **Hard constraint from D12.5 item 2a:** this new file joins the universe of
      `tests/test_vault_path_required.py:test_no_implicit_vault_path_defaults:312`, so it must
      contain no `expanduser`, no `Path.home()` and no `/Users/` literal — the sentinel home comes
      from `OBSIDIAN_SCHEMAS_LOCK_DIR` or from the note's own directory (D3), never from a user home.
      **And land the threat model's three `kind: required` mitigations HERE, in this task, because
      this is the module that would otherwise ship without them** (D2.1–D2.3, D6):
      **(M1) mode on the descriptor BEFORE the first byte** (D2.2, revised round 9) — inside the
      lock, in this ORDER: (1) if the resolved target exists, `st = os.stat(target)`, raise
      `WriteFailedError` when `st.st_nlink > 1` (D2.1's third cell), and take
      `mode = st.st_mode & 0o7777`; (2) create the temp file
      `fd = os.open(tmp, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)` — the narrowest possible
      starting point, and empty; (3) `os.fchmod(fd, mode)` as the FIRST operation on that descriptor,
      **before any note byte is written to it**; (4) only then write, `flush`, `os.fsync(fd)`, close
      and take a terminal form. **There is NO `os.chmod` after the write** — a chmod-before-replace
      leaves the note's complete content sitting at the create mode across the write and the fsync,
      which is precisely the disclosure M1 exists to prevent. When the resolved target does NOT
      exist there is no mode to carry, and the temp file is opened
      `os.open(tmp, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o666)` so umask masking gives exactly the
      mode `Path.write_text` gives a fresh file today. Never `tempfile.mkstemp` (`0600`)
      and never a bare `open(tmp, "w")` (umask-wide). Do not pass `mode` straight to `os.open`: its
      mode argument is umask-masked and can only narrow, so a target at `0o666` under umask `0o022`
      would commit at `0o644`. An `OSError` from `os.stat`, `os.open` or `os.fchmod` raises
      `WriteFailedError` rather than committing at a mode nobody chose.
      **(M2) configuration validity** — read all three env vars through ONE private helper
      `_env_setting(name, parse, validate)`, which is the module's ONLY `os.environ` access; a second
      `os.environ` reference anywhere in this file is forbidden. `OBSIDIAN_SCHEMAS_LOCK_DIR` must be a
      non-empty absolute path naming a usable directory and raises `WriteFailedError` when it is
      relative, empty or unusable — never resolved against the process CWD. All refusals use the
      existing reason `"write did not complete"` (`obsidian_schemas/errors.py:REASONS:96`); mint no
      new literal here, and do not edit `REASONS` in this task.
      **(M3) one resolved path per door, INCLUDING the sentinel's own directory** (D2.3, D3, revised
      round 9) — resolve the path ONCE at entry
      (`target = Path(path).resolve()`, non-strict) and key the in-process lock, the registry, the temp
      directory `target.parent`, the `stat_stamp` precondition and the terminal `os.replace`/`os.link`
      on that single value. **The file sentinel is
      `target.parent / ".obsidian-schemas-locks" / f"{h}.lock"` with
      `h = hashlib.sha256(str(target).encode("utf-8")).hexdigest()[:32]` — its DIRECTORY derived from
      the resolved `target.parent`, never from the caller's unresolved parent, so two paths naming one
      real note cannot key one hash into two directories and both acquire.** Under
      `OBSIDIAN_SCHEMAS_LOCK_DIR` the home is that one configured directory for every note.
      `move_note` resolves `src` and `dest` the same way and refuses a
      `Path(src).is_symlink()` source with `WriteFailedError`. No door mixes a resolved value with an
      unresolved one.
      None of the three needs a vocabulary or wall change: `chmod` is already in
      `PATH_MUTATION_NAMES`, and `os.stat`, `os.open` and `os.fchmod` are `os` members Wall B polices
      at member granularity while excluding this
      file (D2.2), so do NOT edit `tests/derivations.py` in this task — in particular do NOT add
      `fchmod` to a vocabulary and do NOT add anything to `OS_READONLY_NAMES`.
      *Verify:* author four zero-argument top-level checks into `tests/test_concurrent_access.py`
      (this task creates the module; Task 13 finishes it) and run
      `.venv/bin/python -m pytest tests/test_concurrent_access.py -q` GREEN, then THE FLOOR GREEN.
      Each check takes its scratch vault from `tests/support.py:temp_dir:31` — the established
      zero-arg scratch-home shape (`tests/test_loud_fail_write.py:52-55`), so the vault has a declared
      home that is removed on exit rather than an unstated one. The four:
      (i) `test_vault_io_round_trips_and_refuses_a_stale_stamp` — create a note through `create_note`,
      re-create it and get `NoteAlreadyExists`, `read_note` it, mutate it through `write_note` with the
      returned stamp, then re-attempt `write_note` with the now-stale stamp and get
      `ExternalWriteConflict`;
      (ii) `test_every_door_preserves_the_targets_mode` (AC-15);
      (iii) `test_configuration_refuses_invalid_values_and_bounds_acquisition` (AC-16);
      (iv) `test_every_door_uses_one_resolved_path` (AC-17). Their oracles are specified in Task 13,
      and every one of them is a value the check itself wrote — the exact mode it chmod-ed, the exact
      path it created, the exact bytes it planted.

- [x] **Task 4 — Route door 1: `writer.py` and `base.update_fields`.** Convert
      `obsidian_schemas/writer.py:update_frontmatter_field:283`, `:update_frontmatter_fields:333`,
      `:roundtrip_file:365` and `obsidian_schemas/repositories/base.py:update_fields:390` to the
      `vault_io.note_lock` / `vault_io.read_note` / `vault_io.write_note` form of D7, keeping each
      site's existing
      `FileNotFoundError` guard, parse, and `LoudFailError`-re-raise structure exactly where it is.
      **Every door call is a module attribute** (`from obsidian_schemas import vault_io` at module
      level, then `vault_io.write_note(...)`) — a bare `write_note(...)` is not an `ast.Attribute`
      and `_is_write_call` would match nothing, which is the whole of D7's call-form ruling.
      **Then land Table 3a row 1, and nothing else in that module** (D12): in
      `tests/test_loud_fail_parse.py:test_error_chains_are_bounded:412` part 3 (`:445-453`), inject
      the `OSError` at the door instead of the old commit call — `from obsidian_schemas import
      vault_io`, then `monkeypatch.setattr(vault_io, "write_note", deny)` with the matching restore,
      replacing the `_Path.write_text` patch and its `real_write_text` save/restore. **Every
      assertion stays byte-identical**, including `caught.value.__cause__ is boom`. Part 4 (`:462-471`)
      is NOT edited: `read_note` wraps nothing (D1), so the `UnicodeDecodeError` still reaches the
      site's own `except` and still fails `chainable_cause`.
      *Verify:* `.venv/bin/python -m pytest tests/test_loud_fail_parse.py
      tests/test_writer.py tests/test_repositories.py -q` GREEN — in particular
      `test_no_mutation_writes_through_failed_parse`, whose `write_paths` set must still be exactly
      the four `FunctionId`s at `tests/test_loud_fail_parse.py:110-116`. **The derivation half is
      predicted from a derivation, not from hope: D7 (1) walks `_taints_a_write`'s sink over the
      routed body and shows the tainted `new_content` reaching a matched `vault_io.write_note` call.**
      Any RED here other than Table 3a row 1's own pre-edit failure is a **HAND-BACK to the
      conductor** (D12.4's fourth branch) — never a further edit to that module, and never a weakened
      assertion.

- [x] **Task 5 — Route door 1: the six `person.py` body-writer sites.** Convert `:1543`, `:1554`
      (`append_to_timeline`), `:1652` (`append_to_body_section`), `:1769` (`add_to_discuss_item`),
      `:1845` (`update_to_discuss_item`), `:1912` (`remove_to_discuss_item`). Every dedup check and
      every `return False` stays in its current function's own body — moving one into a nested
      function changes the `SiteId` qualname that `tests/test_loud_fail_write.py:126-139` classifies.
      **And the `vault_io.write_note(...)` call itself stays in that same own body**, module-attribute
      form as in Task 4: it is what keeps each of these four methods inside
      `non_completed_write_sites`' universe gate (`tests/derivations.py:507`), which is what keeps
      their seven `SiteId` entries returnable.
      **Then land Table 3a row 2, and nothing else in that module** (D12): in
      `tests/test_loud_fail_write.py:_check_write_failure_raises_and_noops_keep_their_return:110`
      P1 (`:152-157`), inject the `OSError(28)` at `vault_io.write_note` instead of `Path.write_text`
      — `monkeypatch.setattr(vault_io, "write_note", lambda *a, **k: (_ for _ in ()).throw(boom))`
      with the matching restore through the same `tests/support.py:patcher` shim. **Every assertion
      stays byte-identical**, including that `repo.append_to_timeline(person, "### new\n")` raises
      `WriteFailedError`. Rows 3 and 4 in this same module belong to Task 7, not here.
      *Verify:* `.venv/bin/python -m pytest tests/test_loud_fail_write.py
      tests/test_body_sections.py tests/test_wi126_body_preservation.py -q` GREEN — rows 3 and 4 do
      not fire yet, because door 2 does not exist until Task 7 and `write_markdown_file` still has
      today's behaviour. In particular
      `test_write_failure_raises_and_noops_keep_their_return` must be GREEN, with its classification
      map matching the scan with no stale and no unclassified entries. **The derivation half is
      predicted from D7 (3)'s walk of that universe gate, not from hope.** Any OTHER red is a
      HAND-BACK to the conductor (D12.4's fourth branch) — never a further edit to
      `tests/test_loud_fail_write.py`, and never a weakened assertion.

- [x] **Task 6 — Route door 1: the two script sites.** Convert `scripts/lint_vault.py:876` and `:894`
      (one enclosing `with vault_io.note_lock(fpath):` spanning both; each write carries its own
      freshly-read stamp) and `scripts/migrate_person_to_discuss.py:104`. Both scripts gain
      `from obsidian_schemas import vault_io` and call every door as a module attribute (D7).
      *Verify:* THE FLOOR GREEN, and
      `.venv/bin/python scripts/migrate_person_to_discuss.py --help` exits 0 (import-time
      sanity; the script's real run is a close-out step, not a plan task — it writes vault state).

- [x] **Task 7 — Install door 2 inside `write_markdown_file`.** Implement D8 (a)–(e) at
      `obsidian_schemas/writer.py:write_markdown_file:154`: the lock, the stamp lookup, the zero-case
      create, the 2u precondition, the WI-126 guard read moved inside the lock, deletion of the
      `overwrite=False` guard at `:186-187`, `allow_unverified_overwrite` threaded through
      `base.py:save:294`, `person.py:save:1252`, `book.py:save:138` and `meeting.py:save:160`. Also
      replace the `mkdir` at `obsidian_schemas/writer.py:233` with
      `vault_io.ensure_dir(file_path.parent)`
      (R5 as restated; Wall A forbids naming `mkdir` outside `vault_io.py`). Every door call in this
      task is a module attribute (D7).
      **And land the per-repository cache lock — the item's original March scope — as the RULE Edge
      Cases states, not as a bare lock** (round 9; AC-18 is its oracle, and it had none before this
      round). `BaseRepository.__init__` (`obsidian_schemas/repositories/base.py:142-144`) gains
      `self._cache_lock = threading.RLock()`, **and — this is the round-10 correction — `BaseRepository`
      gains ONE adoption method rather than the rule being restated at each site**:
      `_adopt(self, name_key, entity, file_path)` takes `_cache_lock`, builds `dict(self._cache)` and
      `dict(self._file_map)`, sets `name_key` in each copy, rebinds both attributes, and calls
      `self._index_entity(entity, name_key)` — the identical three-part adoption every existing site
      already performs, now written once. **After this task, `_adopt` is the only per-entity writer of
      `_cache`/`_file_map` in the package; the only two other writers of those mappings at all are
      `load` (a bulk rebuild) and `update_fields`' removal half (a delete).** Convert all FOUR
      existing single-entity adoption sites to one `_adopt(...)` call each, verified to be the same
      three-line shape today: `base.py:save:331-334`,
      `base.py:update_fields:412-414`, `book.py:save:173-176` and `meeting.py:save:195-198`. **Task 8
      adds the fifth caller and must not write its own** — that site is the reason this is a door
      rather than a list (Edge Cases' adoption-door rule; an enumeration derived over the pre-build
      tree cannot reach a site this plan itself creates). The three sites that are NOT single-entity
      adoptions keep their own rule under the same lock and **replace rather than mutate a live
      mapping**:
      `load` (`:176-178`, `:186-193`) binds fresh local `new_cache` / `new_file_map`, fills them
      key-by-key across the walk with its own `_index_entity` call, and rebinds both ONCE at the end
      inside a critical section spanning the whole walk — never
      `self._cache.clear()` on the live dict. **`load` does NOT call `_adopt`**, and that is a rule
      rather than an omission: a per-note `_adopt` would publish a half-built vault once per note
      instead of never, and would copy the whole mapping N times.
      `update_fields`' removal half (`:401-410`) builds its copies, deletes
      the old key from them, and hands them to the same critical section its `_adopt` call at
      `:412-414` closes;
      `refresh` (`:434-435`, `:450-453`) takes it across its snapshot and
      its restore; `_note_skip` (`:223`) takes it to append, and `skipped_notes` (`:202`) /
      `skipped_count` (`:206`) take it to read — `_skipped` is the ONE container whose readers lock.
      **No other read path takes the lock**, and no read path is edited.
      `person.py:save:1252` delegates to `super().save()` and adopts nothing itself — it calls
      `_adopt` nowhere, which is a consequence of the door rather than a per-file exemption.
      **The lock spans the cache mutation only, never the filesystem write**: it is not
      held across `write_markdown_file` in `save`, nor across `update_fields`' door-1 write, so no
      thread ever holds it while acquiring `note_lock` (Edge Cases' lock-ordering ruling). Do NOT
      widen it to the subclass indexes and do NOT make the indexes copy-on-write — that cell is ruled
      and declared in Edge Cases.
      **And record the derivation stamp in EVERY loader, not one** (D5's (A′) — this half is what
      makes step 5's zero case mean "nothing derived an entity here"). In each of the three functions
      the loader corpus resolves to — `obsidian_schemas/repositories/base.py:_load_file:226`,
      `obsidian_schemas/repositories/book.py:_load_file:57`,
      `obsidian_schemas/repositories/meeting.py:_load_file:64`, which is the corpus
      `tests/derivations.py:load_file_implementations:355` derives and
      `tests/test_loud_fail_parse.py:301` pins at 3 — take `stamp = vault_io.stat_stamp(file_path)`
      as the **first statement INSIDE that function's existing `try:`** (`base.py:238`, `book.py:64`,
      `meeting.py:70`) and above that function's first read of those bytes (`book.py:66`,
      `meeting.py:71`; the base loader's read is inside `parse_markdown_file` at `:239`), and call
      `vault_io.remember_snapshot(file_path, stamp)` ONLY on the branch that returns an entity
      (`base.py:240-241`, `book.py:75-76`, `meeting.py:79-80`). Record nothing on the wrong-`type`
      early returns (`book.py:70-71`, `meeting.py:75-76`), nothing in the `except` branches, and
      nothing on the trailing `return None`. **The stat goes INSIDE the `try`, never above it:**
      `base.py:load:186-193`'s loop carries no `try` of its own, so the loader's own broad
      `except → _note_skip` (`base.py:242-243`, `book.py:77-80`, `meeting.py:81-84`) IS WI-020's
      no-abort guarantee, and a `stat_stamp` raising above the `try` would abort the whole vault walk
      on one unreadable note (D5). Both calls go in the loader's OWN body — not in a nested
      helper, which Wall D(i) reads as absent. Do NOT restructure the loaders into a template method,
      and do NOT edit `tests/test_loud_fail_parse.py:300-301`: this task adds no repository and
      removes no `_load_file` declaration, so the `== 4` and `== 3` pins stay true (D5, "(A′)'s
      interaction with the `== 3` pin is: none").
      **And land Table 3a rows 3–6 — the four `allow_unverified_overwrite=True` additions — in the
      SAME task that creates the condition they answer** (D12): `tests/test_loud_fail_write.py:66`
      and `:89`, `tests/test_writer.py:171` and `:322`. One keyword per call, nothing else on those
      lines, and no assertion anywhere in either module altered. Each of those four calls writes to a
      path the test seeded itself and never asked this package to observe, so the keyword is the
      documented consumer answer (D5) rather than a patch — and adding it keeps every asserted
      property intact, because D8(d) as corrected still runs the WI-126 guard on that branch. Do NOT
      add the keyword anywhere the sweep did not return it, and do NOT reach for it as a general
      repair: a red outside Table 3a is D12.4's fourth branch.
      *Verify:* THE FLOOR — `tests/test_writer.py` is expected RED
      at `test_no_overwrite_by_default:146` only (it asserts `FileExistsError`); every other module
      GREEN, `tests/test_loud_fail_parse.py:300-301` unedited and passing. Task 16 measures that
      claim rather than trusting it, and Task 14 closes the one RED. Then author
      `test_a_loader_overriding_repository_can_update_a_note_it_loaded` into
      `tests/test_concurrent_access.py` (Task 3 created the module) and run it: a
      `BookRepository` and a `MeetingRepository` each load a note the test wrote into a scratch
      vault, then `save()` a mutated entity — the save SUCCEEDS as a 2u update rather than raising
      `NoteAlreadyExists`, and the file on disk carries the exact field value the test set; then the
      note is edited on disk behind the repository and the save is re-attempted, which raises
      `StaleEntityWrite`. Every oracle is a string the test itself wrote.
      **And author `test_repository_cache_is_consistent_under_concurrent_refresh` (AC-18) into the
      same module and run it** — the falsifier for the paragraph above, which without it is a
      six-word instruction with no check anywhere in this plan. Its oracle is specified in Task 13
      and is the note count the test itself wrote. This check exists because
      the routing wall is structurally blind to a missing observation and no test in `tests/` saves a
      book or a meeting today (all six `repo.save(` calls in `tests/test_repositories.py:644-725`,
      and all four in `tests/test_writer.py:432-441`, are `PersonRepository` — ten in total, per the
      corrected count in `## Verified Diagnosis` claim 8).

- [x] **Task 16 — RUN the whole floor against the routed tree and pin its COMPLETE red set.**
      *Executed here, immediately after Task 7 and before Task 8; the ordinal is 16 so that no
      `Task N` cross-reference in this document drifts.* This task **edits nothing**. Run THE FLOOR
      with failures listed rather than summarised:
      `.venv/bin/python -m pytest tests -q -rf`. Paste the WHOLE `short test summary info` block and
      the final counts into the Build Log verbatim — not a description of them — then compare against
      **D12.3's Table 3b**, which sits beside D10.6's two tables and is pinned the same way. This is
      Fold 2's instrument applied one level up:
      Task 0 executes the wall predicates before the vocabulary is frozen, and this task executes the
      ACCEPTANCE BATTERIES and the floor before "the routing is behaviourally clean" is believed.
      Every finding round 6 produced was reachable by running exactly this command.
      **Disposition every red by D12.4's rule and by nothing else.** Rows 1–6 of Table 3a have already
      landed in Tasks 4, 5 and 7, so the expected red set here is **exactly one** check —
      `tests/test_writer.py::TestWriteMarkdownFile::test_no_overwrite_by_default` (Table 3a row 7,
      owned by Task 14). **Any additional failing check, and any Table-3b row that is green when it
      should be red, is a HAND-BACK to the conductor** naming the check, its assertion and the axis
      that failed to predict it. Do NOT edit a test module here, do NOT weaken an assertion, do NOT
      widen `allow_unverified_overwrite` to a site the D12.1 sweep did not return, and do NOT edit
      Table 3.
      *Verify:* the Build Log contains the verbatim `-rf` summary and the final counts; the failing
      set is exactly the single check Table 3b names; and the passing count is at least Task 1's
      recorded baseline minus one, reported as a property against that baseline rather than as a
      hardcoded number.

- [x] **Task 8 — Door 2c's consumer recovery in `create_stub`.** Wrap the `self.save(...)` at
      `obsidian_schemas/repositories/person.py:1466` per D9: catch `NoteAlreadyExists`, re-read that
      one path via `base.py:_load_file:226`, re-register the stamp, **adopt the re-read entity by
      calling `self._adopt(self._get_cache_key(entity), entity, file_path)` — the door Task 7
      installed, and NOT a hand-written `self._cache[key] = entity`** — then take the
      existing reuse branch at `:1430-1437`; re-raise if the re-read yields no entity.
      **Why the door and not "cache the entity", spelled out because the narrow reading breaks this
      task's OWN verify (round 10).** `_adopt` writes three things — `_cache`, `_file_map` and
      `_index_entity` — and the reuse branch at `:1436` calls
      `_writeback_identifier` (`obsidian_schemas/repositories/person.py:_writeback_identifier:1189`),
      which routes through `update_fields` at `:1214`, which calls
      `get_file_path` (`obsidian_schemas/repositories/base.py:update_fields:363` →
      `get_file_path:292`, `self._file_map.get(...)`). A recovery that populated `_cache` alone leaves
      `_file_map` empty for that key, so `get_file_path` returns `None` and `update_fields` raises
      `ValueError(f"{self.type_name} not found in repository: {name}")` at
      `obsidian_schemas/repositories/base.py:366` — **before the phone is written back**, which is
      exactly the outcome the verify below asserts against. This is the FIFTH caller of the adoption
      door and the reason Edge Cases states the surface as a door rather than as a nine-site list:
      the tenth mutation site is one this plan itself creates, in the file the pre-build grep declared
      needed none.
      *Verify:* author `test_create_is_no_clobber_and_create_stub_reuses_the_winner` (AC-5) into
      `tests/test_concurrent_access.py` (Task 3 created the module) as a zero-argument top-level
      check, covering all three halves of AC-5's `desc` in one check:
      **(a) the no-clobber create** — `create_note` against a path a second writer already wrote
      raises `NoteAlreadyExists` and the destination's bytes are byte-identical to what that writer
      put there;
      **(b) `PersonRepository`** — a repository loads an empty
      vault, a second writer mints `@Jane Doe.md` with an email and `created_by` directly on disk,
      then `create_stub("Jane Doe", phone=...)` returns the WINNER's person with the winner's
      `created_by` and email intact and the phone written back into the note on disk;
      **(c) `BookRepository` and `CompanyRepository`** — the same losing-race shape against
      `book.py:create_stub:273` and `company.py:create_stub:153`, each of which has no reuse branch
      (D9), surfaces `NoteAlreadyExists` to the caller and leaves the winner's note byte-identical.
      Oracle values are the exact strings the test wrote, never a substring or a shape.

- [x] **Task 9 — Door 3 at `quarantine_garbage`.** Replace `scripts/lint_vault.py:1036-1038` per D9:
      delete the `dest.exists()` guard, call `vault_io.move_note(src, dest)`, catch
      `NoteAlreadyExists` and
      `continue`. Replace `dest_dir.mkdir(parents=True, exist_ok=True)` at `:1034` with
      `vault_io.ensure_dir(dest_dir)` — identical semantics and still no precondition (R5 as restated
      round
      5), but named inside `vault_io.py`, because `mkdir` is in `PATH_MUTATION_NAMES` and Wall A
      admits no
      exemption. Do NOT resolve this by dropping `"mkdir"` from the vocabulary: that is the wall
      narrowing its own reach, and it is ruled against in D10.3.
      *Verify:* `test_move_note_refuses_an_existing_destination` and
      `test_quarantine_skips_on_collision_without_clobbering` in `tests/test_concurrent_access.py`,
      the latter asserting the destination's bytes are byte-identical to what the test wrote there.

- [x] **Task 10 — Observe-only mode.** Implement D6/D9's `OBSIDIAN_SCHEMAS_WRITE_GUARD`: `enforce`
      (default), `observe` (WARNING + today's semantics), any other value raises `WriteFailedError`
      at first write. Applies to `ExternalWriteConflict`, `StaleEntityWrite` and `NoteAlreadyExists`;
      never to Layers 1 and 2. **And emit ONE INFO line at the first write of a process whose mode is
      `observe`**, naming the mode and the env var, before any collision has occurred (D9, round 8) —
      one line per process, not per write. The unrecognised-value refusal routes through
      `_env_setting` like every other setting (D6); do not add a second `os.environ` read.
      *Verify:* author `test_refusals_are_loud_bounded_and_mode_governed` (AC-9) into
      `tests/test_concurrent_access.py` as a zero-argument top-level check covering **both** halves of
      AC-9's `desc`, because the mode half alone leaves the bounded-message half authored by no task
      (round 10):
      **(a) the loud-and-bounded half** — provoke each of the three refusals this item mints
      (`StaleEntityWrite`, `ExternalWriteConflict`, `NoteAlreadyExists`) from a note whose body the
      check itself planted with a distinctive sentinel string, and for each assert it
      `isinstance(..., LoudFailError)`, that it is **not** a `WriteFailedError` (so
      `except WriteFailedError` cannot swallow a conflict, which is what "distinguishable" buys the
      caller), that `exc.path` is the exact path the check created, and that the sentinel string the
      check wrote into the body appears NOWHERE in `str(exc)` — the oracle is the string the check
      planted, never an assumed absence of some shape;
      **(b) the mode half** — both directions from one fixture, that an
      unrecognised value raises, and that exactly one INFO record naming the mode is emitted across
      two writes in `observe` — captured through `tests/support.py:captured_logs:91` with
      `level=logging.INFO` (its default is `WARNING`, which would see nothing) rather than by reading
      stderr.

- [x] **Task 11 — RE-RUN the predicates against the routed tree and pin Table 2.** No new predicate
      is written here: Task 0 landed them all, and `tests/derivations.py` should need no further edit.
      Re-execute the same read-only one-liners Task 0 used, now over the post-routing tree, plus the
      four WI-020 sweeps D7 derives, and paste every result into the Build Log beside D10.6's
      **Table 2**. The rows are: `filesystem_mutation_uses` (uses in `vault_io.py` only);
      `os_module_attribute_uses` and `module_import_uses` (unchanged outside `vault_io.py`);
      `functions_calling(files, "stat_stamp")` and `…"remember_snapshot"` (each ⊇ the three loaders);
      `functions_calling(files, "parse_markdown_file")` (still == the loaders);
      `functions_calling(files, "_adopt")` (EXACTLY the five adopting functions —
      `base.py:save`, `base.py:update_fields`, `book.py:save`, `meeting.py:save` and
      `person.py:create_stub`, with `base.py:load` deliberately NOT among them because it is a bulk
      rebuild — set equality, which is the surface oracle for Edge Cases' adoption-door rule);
      `falsy_returns_in(python_files_under(PACKAGE_ROOT), COMMIT_FUNCTION_NAMES)` (empty, now over a
      real `vault_io.py` — the non-vacuous green Table 1 flagged);
      `functions_reserializing_parsed_frontmatter` (the four `FunctionId`s at
      `tests/test_loud_fail_parse.py:110-116`);
      `functions_parsing_then_writing - functions_reserializing_parsed_frontmatter` (`{write_markdown_file}`);
      `non_completed_write_sites` (the eight `SiteId`s at `tests/test_loud_fail_write.py:126-139`);
      and `len(base_repository_subclasses(...)) == 4`, `len(load_file_implementations(...)) == 3`.
      **Any row that differs from Table 2 is a HAND-BACK to the conductor naming the row.** Do not
      edit the vocabulary, do not edit Table 2, and do not edit
      `tests/test_loud_fail_parse.py` or `tests/test_loud_fail_write.py` to make a row agree — a
      mismatch means D7's derivation is wrong, and relaxing a previous item's shipped acceptance
      property to hide that is the single failure this task exists to prevent.
      *Verify:* THE FLOOR GREEN except the one known RED from
      Task 7; `tests/test_loud_fail_harness.py:test_derivations_are_single_sourced:58` still passes
      — that module declares exactly ONE test, and it is the one that asserts `ast` is single-homed
      via `modules_using_ast(...)` inside its private helper
      `_check_derivations_are_single_sourced:66` at `:96`; the new predicates live in the module
      already permitted to name `ast`, so it stays green — and the Build Log
      carries every Table-2 row with its actual output.

- [x] **Task 12 — The routing wall.** New `tests/test_write_routing.py`: Walls A, B, C, **D and E**
      of D10, plus **one match-shape fixture battery per wall predicate — and the battery list is
      DERIVED from D10.1's predicate set, not hand-written (round 10).** The obligation is D10.5's
      opening rule, stated over the source rather than per wall: the predicate set is
      `{filesystem_mutation_uses, os_module_attribute_uses, module_import_uses, functions_calling,
      falsy_returns_in}` — **FIVE**, one per wall — and each ships a MATCHED battery and a NOT-matched
      battery, planted in a scratch module and driven through **the same function the live wall
      calls, never a re-implementation**. Concretely: every claimed mutation shape from D10.5's
      MATCHED table driven through `filesystem_mutation_uses`; every claimed `os` access shape, in
      BOTH access forms, driven through `os_module_attribute_uses`; every claimed import shape, in
      both statement forms, driven through `module_import_uses`; every claimed call shape
      driven through `functions_calling`; and every claimed falsy-return shape driven through
      `falsy_returns_in`. Each asserted MATCHED, and every near-miss from the corresponding
      NOT-matched table asserted NOT matched. **A wall shipped without its pair of batteries is an
      unfixtured wall and a hand-back, not a smaller job** — do not derive "three batteries" from any
      earlier revision of this task.
      **Walls B and C had no battery before round 10, and each is ZERO-COUNT on the arm that
      matters, which is why the omission was invisible** (D10.5): there are zero `from os import`
      bindings and zero `shutil`/`tempfile`/`fcntl`/`filelock`/`mmap` imports under either root
      today, so a Wall B that never implements the `ast.ImportFrom` arm and a Wall C that returns
      `[]` are both GREEN at Task 0, at Task 11 and here, while AC-7's `desc` certifies both. Plant
      the two batteries from D10.5's Wall B and Wall C tables: for Wall B, `os.unlink` /
      `os.replace` / `os.open` / `os.fchmod` (the last being in NO vocabulary, which is the point —
      the discriminator is the module), `import os as _o` + `_o.unlink(p)`, `from os import replace`,
      `from os import replace as _r`, and `from os import unlink` with the binding NEVER CALLED, each
      MATCHED; `os.environ.get` / `os.getenv` / `os.getcwd` / `os.sep` / `os.path.join` /
      `os.fspath`, `from os import environ`, a bare `import os` with no member access, `shutil.move`
      and the string literal `"os.replace"`, each NOT matched. For Wall C, **generate the MATCHED
      import fixtures by ITERATING the module set Wall C is called with** — `{shutil, tempfile,
      fcntl, filelock, mmap}` — rather than by a hand-written list, asserting the returned module set
      equals it, plus `import tempfile as _t`, `from filelock import FileLock`,
      `from shutil import move`, `from tempfile import NamedTemporaryFile as _n` and an imported-but-
      unused member; and NOT matched: `import os` (legitimate at three live sites), `import pathlib` /
      `from pathlib import Path` / `import hashlib` / `import threading`, the module names inside a
      string literal or docstring, and a local variable named `shutil` with no import.
      **Wall E's battery was missing before round 9 and is not optional** (D10.5): plant scratch
      modules and drive them through `falsy_returns_in` — **generating one
      `def <n>(…): return None` per member of `COMMIT_FUNCTION_NAMES` by ITERATING that frozenset,
      never by a hand-written list**, and asserting
      `{s.qualname.rsplit(".", 1)[-1] for s in falsy_returns_in([plant], COMMIT_FUNCTION_NAMES)}
      == set(COMMIT_FUNCTION_NAMES)` — set EQUALITY, not `⊇`, so `read_note`, `stat_stamp`,
      `record_snapshot` and `ensure_dir` are driven
      rather than assumed and a later addition to the constant cannot go unfixtured; plus the three
      falsy forms (`return`, `return None`, `return False`), the falsy-constant forms (`return ""`,
      `return 0`), a falsy return nested in an `if` and in a `try`, and a method
      `class X: def read_note(self): return None`. And the NOT-matched half: `return path`,
      `return True`, `return "text"`, `return 1`; a falsy return inside a NESTED function of
      `write_note`; a falsy return in `def helper(…)` / `def snapshot_stamp(…)` /
      `def guard_mode(…)` — `snapshot_stamp` carrying a comment naming D4 and D8 step 5, because its
      `None` IS the zero case and a wall that matched it would be red against the design; an implicit
      fall-off-the-end in a `write_note` with no `ast.Return` at all, pinned NOT matched so a later
      reader meets D10.4's declared limit rather than "fixing" the wall into a claim it does not
      make; and the string literal `"write_note"` in a docstring.
      **The three round-5 near-misses are not optional:** a fixture asserting
      `s.replace("-", "")` NOT matched, one asserting `frontmatter.copy()` NOT matched, and one
      asserting `p.replace(q)` NOT matched *carrying a comment naming R10 and D10.3*, so a later
      reader meets the ruling rather than "fixing" the wall into fourteen day-one reds. Each wall
      imports its predicate from `tests.derivations` and asserts
      `derivation.__module__ == "tests.derivations"`, the single-sourcing shape
      `tests/test_loud_fail_parse.py:100-104` already uses. The module's top-level checks are
      `test_filesystem_mutation_is_single_homed` (Walls A/B/C plus all THREE of their batteries —
      `filesystem_mutation_uses`, `os_module_attribute_uses` and `module_import_uses` — AC-7),
      `test_every_derived_loader_records_a_derivation_stamp` (Wall D plus the `functions_calling`
      battery — AC-12) and
      `test_committing_doors_never_return_falsy` (Wall E plus the `falsy_returns_in` battery —
      AC-13); each is a top-level `def test_*(`
      taking ZERO arguments and signalling failure by RAISING. Wall A is GREEN on the first run **by
      derivation, not by expectation**: Task 0 pinned exactly which 17 uses existed before routing and
      Table 2 pinned that all of them now live in `vault_io.py`. If any wall is RED, the fix is to
      move the offending call into `vault_io.py` or to HAND BACK — **never** to remove a name from a
      vocabulary, add an exemption, or edit D10.6's tables (D10.3, D10.6).
      *Verify:* `.venv/bin/python -m pytest tests/test_write_routing.py -q` GREEN, and three
      mutate-and-observe probes, each reverted immediately: temporarily adding `Path("x").unlink()`
      to `obsidian_schemas/writer.py` turns Wall A RED — **placed INSIDE an existing function's body,
      never at module scope** (round 10), because Wall A reads parsed syntax and never needs the
      statement to execute, while a module-scope `Path("x").unlink()` raises `FileNotFoundError` on
      import of `writer.py`, which `base_repository_subclasses` reaches BY IMPORT — so a module-scope
      probe would take Wall D down alongside Wall A and leave the builder diagnosing two reds at
      once; temporarily deleting the
      `vault_io.remember_snapshot` call from `obsidian_schemas/repositories/book.py:_load_file:57`
      turns Wall
      D(i) RED naming that loader; and temporarily adding `return None` to `vault_io.write_note`'s
      body turns Wall E RED naming that site. **Every probe target is a declared `## Write Targets`
      path inside the wall's own universe, and that is a rule rather than a coincidence** (corrected
      round 8): all three of `obsidian_schemas/writer.py`,
      `obsidian_schemas/repositories/book.py` and `obsidian_schemas/vault_io.py` are declared write
      targets that earlier tasks have already edited, so a probe never asks the builder to choose
      between violating a `## Scope Boundary` untouchable and silently dropping a verify step. Wall
      A's probe cannot be relocated into the scratch fixture directory this task already builds —
      Wall A's universe is `python_files_under(PACKAGE_ROOT, SCRIPTS_ROOT)`, so a scratch file is
      invisible to it by construction, which is exactly why the probe needs a real file and why that
      file must be a declared one. Mutate-and-observe is the complementary half and never sufficient
      on its own — the mutation is authored from the same mental model as the matcher — which is why
      the shape fixtures above exist.

- [x] **Task 13 — The behavioural battery.** `tests/test_concurrent_access.py` — Tasks 3, 7, 8, 9 and
      10 each author their own named checks into this module as they land (Task 3 creates the file,
      so no task's verify depends on a later one); Task 13 completes the remainder and is where
      the module is finished. Covering:
      torn-write impossibility (a reader never observes partial bytes across a `write_note`); door-1
      external conflict; door-2u `StaleEntityWrite`; the architect's note-#1 sequence explicitly
      (load → exported `update_frontmatter_field` → `repo.save(cached)` MUST raise `StaleEntityWrite`);
      the loader-override update path (Task 7's check — `BookRepository` and `MeetingRepository` load
      and then save, which is the class the walls cannot see); the no-clobber create and the door-2c
      create race across all three stub repositories (Task 8's check,
      `test_create_is_no_clobber_and_create_stub_reuses_the_winner`, AC-5);
      `move_note` collision (Task 9's checks); lock reentrancy
      within one thread and exclusion across two threads (AC-8 — the per-note `note_lock`, NOT the
      repository cache lock, which is AC-18's); refusal loudness, message boundedness and mode
      governance (Task 10's check, `test_refusals_are_loud_bounded_and_mode_governed`, AC-9); the
      repository-cache check Task 7 authored (AC-18); and the
      three mitigation checks Task 3 authored (below).
      **The three mitigation checks, with their oracles derived (Task 3 authors them; this task owns
      their completeness):**
      `test_every_door_preserves_the_targets_mode` (AC-15) — in a `temp_dir()` scratch vault, plant a
      note, `os.chmod` it to `0o600`, write through `write_note`, and assert
      `stat(p).st_mode & 0o7777 == 0o600`; repeat at `0o644`; then `create_note` a fresh path and
      assert its mode equals the mode a sibling `Path.write_text` gives an equally fresh path in the
      SAME directory — the oracle is the umask-derived mode the test measured in that run, never a
      hardcoded `0o644`, because the umask is the environment's and D2.2's promise is *equality with
      today*, not a constant. Then the same three assertions through `write_markdown_file` (door 2)
      and through `move_note` (door 3), so the claim is over every door rather than one.
      **And the ORDERING half, which the assertions above CANNOT see** (round 9): every one of them
      inspects the mode of the *committed* note, which is identical under mode-before-write and
      mode-after-write, so M1's window would stay green under the very ordering it forbids. The
      distinguishing observation is the temp file's mode **at the moment the payload is on disk and
      not yet committed**, and `os.fsync` is exactly that moment (D2 orders it after the write and
      before the terminal form). So: plant `real.md`, `os.chmod` it to `0o600`, and through
      `tests/support.py:patcher:73` replace `os.fsync` with a wrapper that, on its FIRST invocation,
      records `stat(t).st_mode & 0o7777` for every `.*.tmp` entry then present in that note's
      directory and delegates to the saved original (so the real fsync still happens, and the patch
      is undone on exit even if the body raises). Write through `write_note` and assert the recorded
      set is exactly `{0o600}` — the exact bits the test itself chmod-ed. Under the round-8 ordering
      the recorded value is the umask-derived create mode and this assertion is RED, which is what
      makes it the falsifier rather than a restatement. Repeat once through `write_markdown_file`, so
      the claim covers door 2's own commit; `move_note` needs no such probe and must not be given one
      — door 3 links an existing inode and writes no temp payload (D2), so there is no window to
      observe.
      `test_configuration_refuses_invalid_values_and_bounds_acquisition` (AC-16) — the whole
      configuration surface in one check, per D6's total rule:
      `OBSIDIAN_SCHEMAS_LOCK_DIR` set to a relative path, to `""`, and to a path that exists as a
      FILE each raise `WriteFailedError` at first acquisition and the message contains the var's name
      and not its value; the same for `OBSIDIAN_SCHEMAS_LOCK_TIMEOUT` at `"0"`, `"-1"` and `"abc"`;
      the same for `OBSIDIAN_SCHEMAS_WRITE_GUARD` at `"ENFORCE"` and `"yes"`; each var UNSET yields
      its documented default with no raise; and — this is the round-7 architect's note #2, which had
      no `criteria` fence before this round — with `OBSIDIAN_SCHEMAS_LOCK_TIMEOUT="0.05"` a second
      acquisition of a lock a background thread is holding raises `WriteFailedError` rather than
      hanging, and the check completes well inside the floor's runtime. Set every var through
      `monkeypatch`/`patcher` so nothing leaks into a sibling check.
      `test_every_door_uses_one_resolved_path` (AC-17) — in a `temp_dir()` scratch vault, create a
      real note `real.md` and a symlink `link.md → real.md`; write through `write_note(link.md, …)`
      and assert the bytes landed in `real.md`, that `link.md` is STILL a symlink
      (`Path("link.md").is_symlink()`), and that no regular file replaced it; then load through a
      repository and `save()` against the symlinked path and assert the same; then assert
      `move_note(link.md, dest)` raises `WriteFailedError` and both paths are untouched. Every oracle
      is the exact byte string the check wrote.
      **And the TWO-PARENTS-ONE-NOTE case, which neither the assertions above nor AC-8 can see**
      (round 9): the ones above are single-process and assert where the bytes land, and AC-8 asserts
      exclusion with no symlink in the picture, so a sentinel keyed into two directories is invisible
      to both. In the same scratch vault build `<v>/real/note.md` and
      `<v>/alias/note.md → ../real/note.md`, two paths in two different parents naming one real note.
      Then: **(a) the discriminating assertion** — take `note_lock` on each path in turn (sequentially,
      no threads), then walk the WHOLE scratch vault for `.obsidian-schemas-locks/*.lock` and assert
      **exactly one** sentinel file exists and that its parent directory is `<v>/real/.obsidian-schemas-locks`
      — the resolved note's own directory, which is the exact directory the check created `note.md` in.
      Under the round-8 text this returns TWO sentinels in two directories and the assertion is RED.
      **(b) the exclusion assertion** — with `OBSIDIAN_SCHEMAS_LOCK_TIMEOUT="0.05"` set through
      `patcher`, hold `note_lock(<v>/alias/note.md)` in a background thread and assert
      `note_lock(<v>/real/note.md)` raises `WriteFailedError` rather than acquiring, then join the
      thread. **(c)** repeat (a) with `OBSIDIAN_SCHEMAS_LOCK_DIR` set to an absolute scratch
      directory and assert the single sentinel lands there instead, so the configured-home branch is
      driven too and not assumed.
      `test_repository_cache_is_consistent_under_concurrent_refresh` (AC-18, Task 7 authors it) —
      the item's ORIGINAL March scope, which had no check anywhere in this plan before round 9. In a
      `temp_dir()` scratch vault the check writes **twelve** person notes itself, loads a
      `PersonRepository`, then runs two threads for a bounded number of iterations (200 is ample and
      keeps the check well inside the floor's runtime): thread W calls `repo.refresh()` in a loop;
      thread R calls `repo.get_all()` and `repo.get_by_role("vip")` in a loop, appending
      `len(repo.get_all())` to a list and catching nothing. Join both, re-raising any exception either
      thread stored. Assert `set(observed_lengths) == {12}` — twelve is the number of notes the check
      itself wrote, never a count read back from the repository — and that neither thread recorded an
      exception. `get_by_role` is in the loop deliberately: it ITERATES `self._cache.values()`
      (`obsidian_schemas/repositories/person.py:1233`), which is the read shape that raises
      `RuntimeError: dictionary changed size during iteration` against a live mapping mutated in
      place, while `get_all()`'s `list(...)` is the shape that silently returns a HALF-BUILT vault.
      Under a bare lock taken only by the writers — the pre-round-9 reading of Edge Cases — both
      assertions are RED; under the replace-the-mapping rule both are GREEN. Take no repository lock
      in the check itself.
      **Two checks this module owns that are not any earlier task's, both from D12:**
      (i) `test_wi020_derivations_survive_the_routing` (AC-10) asserts BOTH halves — the four D7
      derivations against their pinned sets, AND that WI-020's own battery still passes, by importing
      and calling `tests.test_loud_fail_write.test_body_guard_refuses_when_unverifiable` and
      `…test_write_failure_raises_and_noops_keep_their_return`, which are zero-arg top-level defs by
      construction (`tests/test_loud_fail_write.py:52`, `:103`) and therefore invocable directly;
      `test_error_chains_are_bounded` takes fixtures and is covered by the floor instead.
      (ii) `test_unobserved_overwrite_refuses_and_the_escape_still_guards_the_body` (AC-14) writes a
      note with `Path.write_text` in a scratch directory no repository loads, asserts
      `write_markdown_file(p, entity=…, body=…, overwrite=True)` raises `NoteAlreadyExists`, then
      re-runs the exact `README.md:317-338` sequence — `parse_markdown_file` → mutate →
      `write_markdown_file(..., overwrite=True, allow_unverified_overwrite=True)` — and asserts it
      lands with the extra field the test itself wrote still present; then asserts that the SAME
      escape against a shrinking body still raises `BodyTruncationError`, which is the half D8(d)'s
      round-7 correction exists to keep. Every
      oracle is derived from a value the test itself wrote — the exact path it created, the exact
      string it recorded — never from an environmental shape assumed absent. Each `kind: test` check
      named in `## Acceptance Criteria` is a top-level `def test_*(` taking ZERO arguments and
      signalling failure by RAISING; helper functions carry the fixtures (the shape
      `tests/test_loud_fail_write.py:103-107` uses).
      **And the AC → authoring-task map is DERIVED, not remembered (round 10).** Before declaring
      this task done, walk the `criteria` fence SET in `## Acceptance Criteria` — every fence, in
      order — and for each `check` name find the task that authors a top-level `def <check>(` in a
      `## Write Targets` module. `## Acceptance Criteria — Authoring Map` records the result of that
      walk and is the list to check against; **a `check` name that no task authors is the LOUD case
      and a hand-back to the conductor**, not a name to invent a test for here, because the conveyor
      resolves it by `getattr(mod, name)()` and a missing name fails the exam against an otherwise
      correct build. This rule exists because AC-5 and AC-9 named checks no task authored for nine
      rounds while a differently-named check for the same behaviour did exist — the map was
      maintained per-task from memory rather than derived from the fence set.
      *Additional verify for this rule:*
      `.venv/bin/python -c "import re,pathlib; d=pathlib.Path('docs/concurrent-access.md').read_text();
      names=re.findall(r'^check: (\S+)$', d, re.M); src=''.join(p.read_text() for p in
      pathlib.Path('tests').glob('test_*.py')); missing=[n for n in names if f'def {n}(' not in src];
      print('MISSING:', missing); assert not missing"` prints an empty list and exits 0 — run
      read-only from the repository root, writing nothing.
      *Verify:* `.venv/bin/python -m pytest tests/test_concurrent_access.py -q` GREEN.

- [x] **Task 14 — Close Table 3a row 7, the last expected RED, and sweep for siblings.** Update
      `tests/test_writer.py:test_no_overwrite_by_default:146-156` to expect `NoteAlreadyExists`
      (D8b), and re-run the axis-γ sweep — `grep -rn 'FileExistsError' tests/ obsidian_schemas/
      scripts/` — updating each hit or recording in the Build Log why it stands. Today that sweep
      returns exactly three: this test, and `obsidian_schemas/writer.py:180,187`, both of which Task 7
      already removed with the `overwrite=False` guard (D8a).
      *Verify:* THE FLOOR GREEN with zero known failures — the first fully green floor since Task 7,
      and the row that closes Table 3b.

- [x] **Task 15 — Full regression and the derived enumeration.** Run the floor. Then, per WI-238,
      DERIVE the regression enumeration rather than inheriting it: for each path in
      `## Write Targets`, sweep `tests` for modules naming that path or the symbols it
      declares, and name every module the sweep returns in the Build Log alongside its result. Assert
      the PROPERTY (GREEN, zero failures) and report the case count as informational against Task 1's
      baseline; do not hardcode a number.
      *Verify:* THE FLOOR exits 0, and the Build Log lists the
      swept module set with the baseline comparison.

**The two WI-020 acceptance modules: a NARROW, ENUMERATED re-admission — and this is a written
reversal of round 6's withdrawal (round 7).** Round 6 removed both from `## Write Targets` because
they had been declared as Task 4 / Task 5 *contingency* targets, which handed a caged builder written
permission to edit a previous item's shipped acceptance battery at exactly the moment a red made that
the cheapest green. That diagnosis was right and is not reversed. What was wrong was the conclusion
drawn from it: D7's derivations cover only the STATIC half of two modules that are half behaviour,
and three of their behavioural assertions break under routing (D12.1). With them withdrawn, the
build aborts at Task 4 and AC-10's "both UNEDITED" is unsatisfiable — so the withdrawal made an
unbuildable plan rather than a safe one.

The re-admission removes the LICENCE rather than restoring it. Both paths return to
`## Write Targets`, and:

1. **The permitted edits are enumerated line by line, ahead of the build, in D12.3 Table 3a** — rows
   1 (Task 4), 2 (Task 5), 3 and 4 (Task 7). Each is derived from a sweep of its declaring shape
   (D12.1), not from a reviewer's list.
2. **Every asserted property is invariant across every one of them.** No exception type, no
   `__cause__` relation, no byte-identity assertion and no classification map changes. An edit that
   changes what a check PROVES is a hand-back, whatever class it appears to fall into (D12.4).
3. **Everything else in those two modules is still off-limits, and the enforcement is a hand-back.**
   If either goes red at Task 4, Task 5, Task 7, Task 11 or Task 16 in any way Table 3a does not
   literally describe, the derivation is wrong; the builder ABORTS and hands back to the conductor,
   naming the failing assertion and the Table-2 or Table-3 row that disagreed. In particular the
   `write_paths`/`loose_paths` sets at `tests/test_loud_fail_parse.py:110-137`, the count pins at
   `:300-301`, the residue name-set at `:332` and the `SiteId` map at
   `tests/test_loud_fail_write.py:126-139` are named as untouchable in `## Scope Boundary`.
4. **Task 16 measures the claim rather than trusting it** — it runs the whole floor and pins the
   COMPLETE red set against Table 3b, so a fifth behavioural break nobody swept surfaces as a
   hand-back with evidence rather than as an improvised edit.

## Write Targets

```writes
kind: precondition
path: pyproject.toml
why: Task 1 — `filelock>=3.12` must be in `dependencies` AND installed into the seeded `.venv` before the worktree is cut; the project root is outside `write_authority` (`pipeline-runners.yaml:34-38`), so the conductor commits it and the caged builder never touches it.
```

```writes
path: obsidian_schemas/vault_io.py
why: Task 3 — the new write primitive; the only filesystem-mutation home.
```

```writes
path: obsidian_schemas/errors.py
why: Task 2 — three new LoudFailError subclasses, their three REASONS literals, and the de-pinned count comment.
```

```writes
path: obsidian_schemas/__init__.py
why: Task 2 — export the three new exception classes.
```

```writes
path: obsidian_schemas/writer.py
why: Tasks 4 and 7 — door-1 routing for three sites, door 2 installed inside write_markdown_file, and the mkdir at :233 replaced by vault_io.ensure_dir.
```

```writes
path: obsidian_schemas/repositories/base.py
why: Tasks 4 and 7 — door-1 routing for update_fields, stamp recording in _load_file, the per-repository _cache_lock, the NEW _adopt(name_key, entity, file_path) adoption door that is the only writer of _cache/_file_map, the replace-the-mapping rule across load/save/update_fields/refresh/_note_skip and the two _skipped readers, and allow_unverified_overwrite on save.
```

```writes
path: obsidian_schemas/repositories/person.py
why: Tasks 5, 7 and 8 — six body-writer sites routed, save threaded, and create_stub's NoteAlreadyExists recovery, whose adoption of the winner's entity is the fifth caller of base.py's _adopt door rather than a hand-written cache write.
```

```writes
path: obsidian_schemas/repositories/book.py
why: Task 7 — thread allow_unverified_overwrite through save, record the derivation stamp in _load_file:57 (the loader corpus is three functions, not one), and convert the save:173-176 cache mutation to one _adopt(...) call.
```

```writes
path: obsidian_schemas/repositories/meeting.py
why: Task 7 — thread allow_unverified_overwrite through save, record the derivation stamp in _load_file:64 (the loader corpus is three functions, not one), and convert the save:195-198 cache mutation to one _adopt(...) call.
```

```writes
path: scripts/lint_vault.py
why: Tasks 6 and 9 — door-1 routing for the two fix-loop writes, door 3 replacing the quarantine rename's TOCTOU, and the mkdir at :1034 replaced by vault_io.ensure_dir.
```

```writes
path: scripts/migrate_person_to_discuss.py
why: Task 6 — door-1 routing for the migration write.
```

```writes
path: tests/derivations.py
why: Task 0 — SCRIPTS_ROOT, the provenance-partitioned mutation vocabulary, five new predicates (filesystem_mutation_uses, os_module_attribute_uses, module_import_uses, functions_calling, falsy_returns_in), and _is_write_call widened by DOOR_NAMES with its ast.Attribute gate untouched. Task 11 re-runs them and needs no further edit here.
```

```writes
path: tests/test_write_routing.py
why: Task 12 — Walls A-E and ONE match-shape fixture battery per wall predicate, the list derived from D10.1's FIVE-predicate set rather than hand-written (filesystem_mutation_uses, os_module_attribute_uses and module_import_uses added round 10, functions_calling, falsy_returns_in added round 9), including the three round-5 near-misses (str.replace, dict.copy, p.replace), Wall E's COMMIT_FUNCTION_NAMES-derived MATCHED battery, and Wall C's module-set-derived import battery, each with its NOT-matched half.
```

```writes
path: tests/test_concurrent_access.py
why: Task 13 — the behavioural battery behind every acceptance criterion.
```

```writes
path: tests/test_writer.py
why: Tasks 7 and 14 — Table 3a rows 5 and 6 add allow_unverified_overwrite=True to the two raw-seeded overwrite calls, and row 7 makes test_no_overwrite_by_default expect NoteAlreadyExists.
```

```writes
path: tests/test_loud_fail_parse.py
why: Task 4 — Table 3a row 1 ONLY: part 3's fault injection moves from _Path.write_text to vault_io.write_note. Every assertion and every derivation set unchanged; any other red in this module is a hand-back (D12.4).
```

```writes
path: tests/test_loud_fail_write.py
why: Tasks 5 and 7 — Table 3a rows 2, 3 and 4 ONLY: P1's fault injection moves to vault_io.write_note, and the two AC-4 calls gain allow_unverified_overwrite=True. Every assertion and the SiteId classification map unchanged; any other red in this module is a hand-back (D12.4).
```


## Verification

**Happy path smoke.** With a scratch vault: `create_note` a note, `read_note` it, mutate through
`write_note` with the returned stamp, `save()` an entity through a repository that loaded it, and
`move_note` it into a subdirectory. All five succeed, the file is well-formed at every step, and no
`.tmp` file survives in any directory touched. **And the note's mode is the same before and after
every one of those five steps** — `stat(p).st_mode & 0o7777` compared against the value the smoke
itself set with `os.chmod` before the first step, which is M1's property as a positive check rather
than only as the negative row below. **And the same load-then-`save()` through
`BookRepository` and `MeetingRepository`** — the two repositories that override `_load_file` — which
is called out separately because it is the one happy path no wall in this item can see, and the
existing suite contains no book or meeting save at all.

**Failure modes that must fail loudly, each with a distinct type.**

| Condition | Expected |
|---|---|
| Door-1 write whose target changed since the in-lock read | `ExternalWriteConflict` |
| Door-2 write whose target changed since the cache load | `StaleEntityWrite` |
| Door-2 write with no stamp against an existing target | `NoteAlreadyExists` |
| `create_stub` losing a cross-process race | reuse of the winner, WARNING, no exception |
| `BookRepository`/`CompanyRepository` `create_stub` losing a race | `NoteAlreadyExists` to the caller — neither has a reuse branch (D9), and **AC-5 is its oracle as of round 10**; before this round the behaviour was stated in D9 and in this table and exercised by no check anywhere in the plan |
| `move_note` to an existing destination | `NoteAlreadyExists`, both files intact |
| `write_note` without the lock held | `WriteFailedError` |
| Lock acquisition timeout | `WriteFailedError` — AC-16 is its oracle (it had none before round 8) |
| `OBSIDIAN_SCHEMAS_WRITE_GUARD` set to anything but `enforce`/`observe` | `WriteFailedError` |
| `OBSIDIAN_SCHEMAS_LOCK_DIR` relative, empty, or naming a non-directory | `WriteFailedError` at first acquisition — **never** resolved against the process CWD, which would key two writers' sentinels in different directories and lose mutual exclusion silently (M2, D3) |
| `OBSIDIAN_SCHEMAS_LOCK_TIMEOUT` non-positive or unparseable | `WriteFailedError` at first acquisition, never coerced |
| `move_note` whose source is a symlink | `WriteFailedError`, both paths intact — a whole-file move through a link has two defensible meanings and door 3 refuses rather than picking one (M3, D2.3) |
| Any door whose EXISTING resolved target has `st_nlink > 1` | `WriteFailedError` — inode replacement would leave the other hard links on the OLD bytes while today's truncate-in-place updates all of them (D2.1) |
| `os.stat`, `os.open` or `os.fchmod` failing while carrying the mode onto the temp descriptor | `WriteFailedError` — never a commit at a mode nobody chose (M1, D2.2) |
| WI-126 body-shrink on an entity overwrite | `BodyTruncationError`, unchanged |
| Existing body unreadable during the guard | `UnverifiableBodyError`, unchanged |

**Must NOT fail — the class round 4 found, stated as a negative check.**

| Condition | Expected |
|---|---|
| `BookRepository.save` / `MeetingRepository.save` of a note this repository loaded | Succeeds as a 2u update. **Never `NoteAlreadyExists`** — that outcome is the round-4 defect, and AC-11 is its oracle |
| A loader in the derived corpus that records no derivation stamp | RED floor at Wall D(i), naming the loader — never a silent stamp loss |
| An entity derivation added outside the derived loader corpus | RED floor at Wall D(ii), demanding a ruling — never the next gate's finding |
| A `mkdir` named outside `vault_io.py` | RED floor at Wall A — the fix is to route through `ensure_dir`, never to shrink `PATH_MUTATION_NAMES` |
| **`str.replace` in `models.py`, `book.py`, `meeting.py`, `person.py`, `lint_vault.py`; `dict.copy` in `writer.py`, `parser.py`** | Wall A GREEN over all of them. These are the round-5 finding: a name-matched vocabulary makes Wall A red on day one against 17 call nodes in files `## Scope Boundary` forbids touching. Task 0 asserts a ZERO return for both before any routing edit exists |
| **A committing `vault_io` door returning a falsy value** | RED floor at Wall E, naming the site — not silently un-checked, which is what D1's rule was before round 6 |
| **A `falsy_returns_in` narrower than the set AC-13 certifies** — e.g. one resolving only the three door names, leaving a `return None` in `read_note` or `ensure_dir` invisible | RED floor at Wall E's fixture battery, which plants one function per member of `COMMIT_FUNCTION_NAMES` by iterating the frozenset and asserts SET EQUALITY over the returned names (D10.5, round 9). A zero-count wall says nothing about its matcher's reach — the WI-232 shape, and the reason D10.5 now states the battery obligation over D10.1's whole predicate set rather than wall by wall. AC-13 is its oracle |
| **An `os_module_attribute_uses` narrower than the set AC-7 certifies** — e.g. one implementing the `os.<attr>` arm but never the `from os import <n>` arm D10.3 added in round 6 | RED floor at Wall B's fixture battery, which plants both access forms (including `from os import replace as _r` and an imported-but-uncalled binding) and both halves of the `OS_READONLY_NAMES` rule. This is a ZERO-COUNT arm against this tree — there are no `from os import` bindings under either root — so nothing else in this document can see it, while AC-7's `desc` says "in either access form" and R10's declared bound on the `p.replace(q)` blind spot depends on it. AC-7 is its oracle |
| **A `module_import_uses` narrower than the set AC-7 certifies** — e.g. one reading `ast.Import` but not `ast.ImportFrom`, or one returning `[]` unconditionally | RED floor at Wall C's fixture battery, which generates its MATCHED imports by ITERATING the module set the wall is called with and asserts the returned module set equals it, plus both statement forms and their aliases. Wall C is a genuine zero-count wall today — zero `shutil`/`tempfile`/`fcntl`/`filelock`/`mmap` imports under either root — so a matcher that resolves nothing is green at Task 0, Task 11 and Task 12 without a battery. AC-7 is its oracle |
| **An adoption of an entity into `_cache`/`_file_map` written outside `BaseRepository._adopt`** | Table-2 mismatch at Task 11 — `functions_calling(files, "_adopt")` is asserted EQUAL to the six adopting functions, so a seventh site that skips the door, or an existing site left mutating `_cache` directly, is a HAND-BACK. The behavioural oracle is AC-18; this row is the SURFACE oracle, and it exists because the round-9 nine-site enumeration was derived over the pre-build tree and could not reach the tenth site Task 8 itself adds |
| **A routed site calling a door as a bare name rather than `vault_io.<door>`** | `_is_write_call`'s `ast.Attribute` gate stops matching it, which surfaces as a RED in WI-020's own battery at Task 4/5 and as a Table-2 mismatch at Task 11 — a HAND-BACK, never an edit to that battery |
| **`write_markdown_file(existing_unobserved_path, …, overwrite=True)` — the README round-trip recipe, and any never-loaded repository** | `NoteAlreadyExists`. **This is a declared consumer-facing break** (D5, "The cell Wall D(ii) cannot reach"), not a defect. With `allow_unverified_overwrite=True` it lands — and the WI-126 body-shrink guard STILL fires on a shrink, because D8(d) bypasses the zero case and the stamp lookup only. AC-14 is its oracle |
| **A behavioural break under routing that D12.1's axis sweeps did not return** | HAND-BACK at Task 16, with the whole `-rf` summary in the Build Log — never an improvised edit to a test module, never a widened `allow_unverified_overwrite`, never a weakened assertion |
| **A note written through any door keeps the mode it had** | `st_mode & 0o7777` unchanged across every door, and a fresh create takes the same umask-derived mode `Path.write_text` gives it today. **Never `0600`** (which `tempfile.mkstemp` would silently impose on the whole vault, breaking a read-only backup reader) and never a umask-widened `0644` over a note deliberately left at `0600` (person notes carry PII). This is M1, and AC-15 is its oracle. **One honest exception, named rather than implied (D2.2, round 10):** `st_mode & 0o7777` carries the setuid/setgid/sticky triad, and POSIX clears `S_ISUID`/`S_ISGID` on an unprivileged write to a file carrying them — so under M1's `fchmod`-then-write ordering a target with those bits can commit without them. The direction is NARROWING only, no markdown note in this vault carries them, AC-15's `0o600`/`0o644` cases cannot see it, and re-ordering to close it would re-open the confidentiality window M1 exists for |
| **The note's CONTENT never exists on disk at a mode wider than the target's — not for the span of the write and the `fsync`** | The target's mode is on the temp file's own descriptor before the first byte reaches it (`os.fchmod(fd, mode)`, D2.2), and there is no `os.chmod` after the write. A chmod-before-replace passes every committed-mode assertion while leaving the whole note readable at the umask-derived create mode for the length of the write — the confidentiality half of M1, which a committed-mode oracle is structurally blind to. AC-15's `os.fsync` probe is its oracle |
| **A symlinked note updated through any write door** | The real file receives the bytes and the link survives as a link — the same outcome `Path.write_text` gives today, because every door keys the sentinel's hash AND its directory, the stamp, the temp directory and the terminal syscall on ONE resolved path (M3, D2.3, D3). **Never a regular file where the symlink was**, which is what a half-resolved frame would have produced. AC-17 is its oracle |
| **Two paths in two different parents naming ONE real note** | ONE sentinel, in the resolved note's own `target.parent/.obsidian-schemas-locks/`, and the second acquirer waits or times out. **Never two sentinels in two directories, both acquired** — which is what deriving the hash from the resolved path while leaving its DIRECTORY unresolved produces, and which is verbatim the "evaporate Layer 2's mutual exclusion with no sound" failure M2 exists to prevent, reached from the other direction (M3, D2.3, D3). Invisible to AC-8 (no symlink) and to AC-17's single-process half (asserts where the bytes land); AC-17's two-parents case is its oracle |
| **A repository cache mutated while another thread reads it** | `get_all()` returns the complete pre- or post-refresh mapping and `get_by_role` iterates without raising — because every mutation REPLACES the mapping under the per-repository RLock rather than mutating a live one (Edge Cases). **Never a half-built vault reported as the whole one, and never `RuntimeError: dictionary changed size during iteration`** — a writers-only lock that lock-free readers do not take buys neither. This is the item's original March scope, and AC-18 is its oracle |
| **A configuration surface with a validity rule stated for some of its members** | Every env var this item reads routes through the one `_env_setting` helper and refuses loudly (D6). A setting that reaches `os.environ` a second way is the defect M2 was an instance of, and AC-16 asserts the rule over the whole surface rather than over the one var the threat model named |

`except LoudFailError` catches every row above except the two unchanged WI-126 rows, which keep
their current types.

**Integration — downstream consumers that must still work.** `PersonRepository.resolve`,
`get_by_role`, `find_or_create_stub` and `create_stub`; `CompanyRepository.create_stub`;
`BookRepository.create_stub`; `BookRepository.save` and `MeetingRepository.save` **of a note the
repository loaded** (the `_load_file`-override class, which has no coverage in `tests/` today);
`scripts/lint_vault.py --fix` and
`--quarantine`; `scripts/migrate_person_to_discuss.py`. The three consumer repos (HAL9000,
exocortex, orchestrator) install `-e` and pick the change up on import — their audit is a close-out
step, below.

**Regression — the enumeration is DERIVED, not inherited (WI-238).** Task 15 sweeps `tests`
for every module naming a `## Write Targets` path or a symbol it declares, and names each in the
Build Log. The modules the sweep is *expected* to return, stated so a shorter result is visibly a
miss rather than a pass: `test_loud_fail_parse.py`, `test_loud_fail_write.py`,
`test_loud_fail_load.py`, `test_loud_fail_harness.py`, `test_writer.py`, `test_repositories.py`,
`test_wi126_body_preservation.py`, `test_body_sections.py`, `test_resolve_or_create.py`,
`test_identity_index.py`, `test_vault_path_required.py`, `test_parser.py`. The assertion is the
PROPERTY — floor exits 0 with zero failures — with the case count reported informationally against
Task 1's captured baseline, never as a hardcoded number.

**The residual the spec is required to reproduce verbatim (R1, restated on observation).** *POSIX
offers no compare-and-swap on file content, so a µs-scale window remains between the final re-stat
and the `os.replace` in which an Obsidian write can still be lost. This is irreducible from our side
of the boundary. It is acceptable because: (a) the window shrinks from "entire read-modify-write
span, seconds" to microseconds — the WI-015 class becomes astronomically rare instead of routine;
(b) Obsidian only writes when Dave is actively editing THAT note in the same microsecond as a
pipeline mutation of the same note; (c) restated on observation, 2026-08-09 (obligation 2
discharged): Obsidian saves IN PLACE — same inode (220735514), size 5049→5085, mtime advanced,
across a live person-note edit by Dave — i.e. truncate-and-write, NOT a whole-file safe-write. A
reader overlapping Obsidian's truncate window can therefore observe a truncated note, so the
µs-window loser is not bounded in shape to one field update; (a) and (b) still bound the frequency,
nothing bounds the shape.* **A spec claiming total external safety, or claiming Obsidian
safe-writes, is wrong and should fail review.**

**CLOSE-OUT steps — run OUTSIDE the cage, by the conductor, after the build merges.** A caged
builder's writes outside the worktree are reverted at the merge boundary, so none of these is a plan
task and none would mean anything as one.

1. **Live concurrency exercise against a DISPOSABLE vault.** Copy a slice of the real vault to a
   throwaway directory, point `OBSIDIAN_VAULT_PATH` at the copy, and run two processes writing the
   same notes for sixty seconds: one appending Timeline entries through `append_to_timeline`, one
   calling `create_stub` on colliding names. Expect zero torn notes, zero lost Timeline entries, and
   `StaleEntityWrite`/`NoteAlreadyExists` at the observed rate. Never the live vault; redact paths
   and note names before any of the output is recorded in a tracked document.
2. **Obsidian sentinel re-check, widened.** Obligation 3's evidence scope was filename search only.
   With `.obsidian-schemas-locks/` populated by step 1's copy, check full-text search and the graph
   view as well. If sentinels surface, set `OBSIDIAN_SCHEMAS_LOCK_DIR` — the fallback is already
   built and needs no code change — and record it as the decision. **Point it at a USER-PRIVATE
   directory, never a world-writable one** (the round-2 threat model's non-blocking note 2): in a
   shared home another principal can hold the sentinel (a bounded DoS, loud via the timeout) or
   pre-place a symlink at the sentinel path. M2 validates absolute-and-usable, which is the right
   check for the failure mode M2 exists for; privacy of the home is this step's choice to make, not a
   rule the door can enforce.
3. **Consumer audit — three sweeps, not one, and each has a different grep.** All three are
   cross-repo over HAL9000, exocortex and orchestrator, in the shape of
   `docs/wi-024-consumer-audit.md`, and all three are structurally outside this item's scope
   boundary.
   **(3a) The `FileExistsError` → `NoteAlreadyExists` break (D8b).** Grep for `FileExistsError` near
   `write_markdown_file` / `save` / `create_stub`.
   **(3b) The permission assumption (round 8, the threat model's non-blocking note 3).** M1 lands as
   "preserve exactly", so a consumer that ASSUMED a mode rather than reading one is the break that
   survives: grep for `chmod`, `st_mode`, `0o6`, `0o7`, `stat(` and `umask` against vault paths, plus
   any backup or sync script that requires vault notes to be group- or world-readable. Different grep
   from (3a), same class of break, and it is the sweep that matters if M1 ever ships as anything
   other than preserve-exactly. Record the result even when it is empty — an unrecorded empty sweep
   is indistinguishable from an unrun one.
   **(3c) R12's one-process sequence (round 8, the round-7 architect's note #4).** Grep for a
   `append_to_timeline` / `append_to_body_section` / `add_to_discuss_item` call followed by a
   `save()` on the same entity in the same function — the sequence that now raises
   `StaleEntityWrite` with no second writer anywhere (D12.5 item 4). The remedy is a `refresh()` or
   an `update_fields` route between the two calls, and `observe` mode is the measure-first option.
4. **`CLAUDE.md` and `SESSION_LOG.md`.** `obsidian_schemas/vault_io.py` belongs in the Key Files
   table and the new env vars in the docs; both files are conductor-owned session-end work outside
   the cage (`pipeline-runners.yaml:32-33`).
5. **`README.md`'s "Round-Trip Preservation" recipe (`README.md:317-338`).** That recipe is
   `parse_markdown_file` → mutate → `write_markdown_file(..., overwrite=True)`, which under D8 step 5
   now raises `NoteAlreadyExists` — a consumer derivation the registry cannot observe (D5, "The cell
   Wall D(ii) cannot reach"). Add `allow_unverified_overwrite=True` to the documented call and one
   sentence saying what it asserts and what it costs (the write is preconditioned on the door's own
   in-lock stat rather than on the caller's read), plus the pointer that a caller wanting the full
   precondition goes through a repository. `README.md` is at the project root and outside
   `write_authority` (`pipeline-runners.yaml:32-33`), which is exactly why this is a close-out step
   and not a plan task — a caged edit to it is reverted at the merge boundary.

## Acceptance Criteria

Authored fresh: this item was created 2026-03-22, pre-`SIGNOFF_EPOCH`, and carries no frozen
originals or `ac-signoff` fence. Every `check` is a top-level `def test_*(` taking ZERO arguments
that signals failure by RAISING — a returned `False` exits 0 and reads as PASS
(`src/stage_advancer.py` invokes `getattr(mod, name)()`).

```criteria
id: AC-1
desc: A crash or concurrent read during any door's write never observes a partially-written note — every commit is atomic.
check: test_every_door_commits_atomically
kind: test
```

```criteria
id: AC-2
desc: A door-1 write whose target changed since its in-lock read raises ExternalWriteConflict and leaves the target byte-identical to the interloper's bytes.
check: test_door_one_refuses_a_raced_content_write
kind: test
```

```criteria
id: AC-3
desc: A door-2 save() derived from a cache snapshot older than the target raises StaleEntityWrite instead of overwriting, and refresh() plus re-apply succeeds.
check: test_save_refuses_a_stale_snapshot_and_succeeds_after_refresh
kind: test
```

```criteria
id: AC-4
desc: A door-1 write to a path does NOT satisfy a door-2 payload's precondition for that path — the architect's note-#1 sequence raises StaleEntityWrite rather than silently destroying the frontmatter change.
check: test_a_door_one_write_does_not_satisfy_a_door_two_payload
kind: test
```

```criteria
id: AC-5
desc: A create with no derivation read is an atomic no-clobber create — PersonRepository.create_stub losing a cross-process race reuses the winner's note with its created_by and email intact, while the book and company stubs surface NoteAlreadyExists.
check: test_create_is_no_clobber_and_create_stub_reuses_the_winner
kind: test
```

```criteria
id: AC-6
desc: move_note refuses an existing destination by syscall rather than by check, leaving both source and destination byte-identical, and quarantine_garbage skips that note instead of clobbering it.
check: test_move_note_refuses_an_existing_destination
kind: test
```

```criteria
id: AC-7
desc: obsidian_schemas/vault_io.py is the ONLY file under obsidian_schemas/ or scripts/ that names a filesystem-mutation capability, imports a mutation-capable module, or reaches a non-read-only os attribute in either access form — and the wall's predicate discriminates by provenance, proven to resolve every claimed match shape and to reject every near-miss including the live str.replace and dict.copy call nodes this tree already carries.
check: test_filesystem_mutation_is_single_homed
kind: test
```

```criteria
id: AC-8
desc: Layer 2 excludes concurrent writers both across processes and across threads, is reentrant within one thread, and a write attempted without the lock held raises WriteFailedError.
check: test_locking_excludes_and_is_reentrant
kind: test
```

```criteria
id: AC-9
desc: Every refusal this item adds is a LoudFailError distinguishable from WriteFailedError, carries its path, and leaks no note content into its message; observe mode downgrades each to a WARNING and an unrecognised guard value raises.
check: test_refusals_are_loud_bounded_and_mode_governed
kind: test
```

```criteria
id: AC-10
desc: WI-020's acceptance battery still holds over the re-routed tree in BOTH halves — its four derivations return exactly their pinned sets (four writers, write_markdown_file reached and rejected by the discrimination proof, every falsy return still classified, the count pins at tests/test_loud_fail_parse.py:300-301 passing), AND its own checks still PASS with every asserted property intact, the only edits being the fault-injection and escape-keyword lines D12.3 Table 3a enumerates.
check: test_wi020_derivations_survive_the_routing
kind: test
```

```criteria
id: AC-11
desc: A repository that OVERRIDES _load_file can update a note it loaded — BookRepository.save and MeetingRepository.save of a loaded note succeed as 2u updates rather than raising NoteAlreadyExists, and raise StaleEntityWrite once that note is edited on disk behind the repository.
check: test_a_loader_overriding_repository_can_update_a_note_it_loaded
kind: test
```

```criteria
id: AC-12
desc: The observation side is total over the corpus derived from the tree — every function the loader corpus resolves to records a derivation stamp (stat before read, remember on the entity branch), and the set of functions deriving an entity from a file's bytes is exactly that corpus, so a new loader or a new derivation site is a red floor rather than a silent stamp loss.
check: test_every_derived_loader_records_a_derivation_stamp
kind: test
```

```criteria
id: AC-13
desc: No function in vault_io.py's path-, payload- and stamp-returning surface returns a falsy value — the rule is stated over exactly the set the wall checks, COMMIT_FUNCTION_NAMES, with read_note and ensure_dir inside it rather than quoted past it, it is enforced by a predicate that can actually see the doors rather than by a scan whose universe gate no door enters, and that predicate's REACH is driven rather than assumed: a fixture generated by iterating COMMIT_FUNCTION_NAMES plants one falsy-returning function per member and asserts falsy_returns_in returns exactly that set of names, alongside the three falsy forms, the falsy-constant forms, the nested-function boundary and a near-miss battery the predicate must NOT match.
check: test_committing_doors_never_return_falsy
kind: test
```

```criteria
id: AC-14
desc: An overwrite of an existing note this process never observed is refused with NoteAlreadyExists, and the named escape allow_unverified_overwrite=True lets it land WITHOUT surrendering the WI-126 body-shrink guard — so the documented parse-then-write-back recipe works under the escape, preserves extra fields, and still raises BodyTruncationError on a shrink.
check: test_unobserved_overwrite_refuses_and_the_escape_still_guards_the_body
kind: test
```

```criteria
id: AC-15
desc: Inode replacement does not rewrite a note's permissions and never exposes its content at a wider mode than the target's — a note written through write_note, write_markdown_file or move_note keeps the exact st_mode bits it had, the target's mode is on the temp file's OWN DESCRIPTOR before the first note byte reaches it (observed at os.fsync time, when the payload is on disk and not yet committed, which is the only assertion that distinguishes it from a chmod after the write), a fresh create takes the same umask-derived mode Path.write_text gives an equally fresh sibling in that run, and a failure to carry the mode across raises WriteFailedError rather than committing at a mode nobody chose.
check: test_every_door_preserves_the_targets_mode
kind: test
```

```criteria
id: AC-16
desc: Every setting this item reads is validated at first use and refuses loudly rather than coercing — OBSIDIAN_SCHEMAS_LOCK_DIR relative, empty or naming a non-directory raises WriteFailedError instead of resolving against the process CWD, OBSIDIAN_SCHEMAS_LOCK_TIMEOUT non-positive or unparseable raises, OBSIDIAN_SCHEMAS_WRITE_GUARD unrecognised raises, each unset var yields its documented default, and a lock held past the configured timeout raises WriteFailedError rather than hanging.
check: test_configuration_refuses_invalid_values_and_bounds_acquisition
kind: test
```

```criteria
id: AC-17
desc: Every door derives its lock sentinel's HASH and its sentinel's own DIRECTORY, its stamp-registry key, its temp-file directory, its precondition stat and its terminal syscall from ONE resolved path — a symlinked note updated through any write door lands its bytes in the real file and leaves the symlink a symlink, exactly as Path.write_text does today; two paths in two different parents naming one real note produce exactly ONE sentinel, in the resolved note's own directory, so the second acquirer waits rather than proceeding; and move_note refuses a symlinked source with WriteFailedError leaving both paths intact.
check: test_every_door_uses_one_resolved_path
kind: test
```

```criteria
id: AC-18
desc: The repository cache is safe under concurrent mutation — the item's original March scope — because every mutation of _cache and _file_map REPLACES the mapping under the per-repository threading.RLock rather than mutating a live one, and every single-entity adoption routes through the one BaseRepository._adopt door (including the fifth one this item's own create_stub recovery adds, which a pre-build enumeration could not reach), so a thread calling get_all() and get_by_role() while another refreshes always sees the complete pre- or post-refresh mapping, never a half-built vault reported as the whole one and never a RuntimeError from a dict mutated mid-iteration, with no lock taken on any read path.
check: test_repository_cache_is_consistent_under_concurrent_refresh
kind: test
```

**Examples of done.**

1. Two shells, same disposable vault. Shell A holds a `PersonRepository` loaded an hour ago and
   calls `repo.save(person)`; shell B edited that note in between. A raises `StaleEntityWrite`
   naming the path; `repo.refresh()` then re-applying succeeds and B's edit survives.
2. `scripts/lint_vault.py --quarantine` run twice concurrently over the same garbage candidate:
   exactly one note moves, the other run logs a skip, and neither destination is overwritten.
3. `grep -rn 'write_text\|os\.replace\|shutil\.\|mkdir' obsidian_schemas/ scripts/` returns hits in
   `obsidian_schemas/vault_io.py` and nowhere else. (`mkdir` is in the pattern deliberately: the two
   sites at `writer.py:233` and `lint_vault.py:1034` route through `ensure_dir`, and Wall A would be
   red otherwise.)
4. A scratch vault holding one book note and one meeting note. `BookRepository(...).load()`, mutate
   the loaded `Book`, `save()` — it lands, and the file carries the new value. Edit the note in
   Obsidian, `save()` again from the same repository — `StaleEntityWrite`, naming the path. Neither
   call raises `NoteAlreadyExists` at any point.
5. A note written by hand into a scratch directory no repository has loaded. Run `README.md`'s
   Round-Trip Preservation snippet against it verbatim — it raises `NoteAlreadyExists` naming the
   path. Add `allow_unverified_overwrite=True` to the `write_markdown_file` call and re-run — it
   lands, the custom field survives, and replacing the body with an empty string still raises
   `BodyTruncationError`.
6. A scratch vault holding `real.md` at mode `0600` and a symlink `link.md → real.md`. `write_note`
   through `link.md`: the bytes land in `real.md`, `link.md` is still a symlink, and
   `stat("real.md").st_mode & 0o7777` is still `0o600`. `OBSIDIAN_SCHEMAS_LOCK_DIR=locks` (relative)
   on the same call: `WriteFailedError` naming the variable, before any byte moves.
7. The same vault with `real/note.md` and `alias/note.md → ../real/note.md`. Lock each path in turn,
   then `find . -name '*.lock'`: exactly ONE sentinel, under `real/.obsidian-schemas-locks/`. Hold
   the lock through one path in one shell and write through the other in a second shell with
   `OBSIDIAN_SCHEMAS_LOCK_TIMEOUT=0.05`: `WriteFailedError`, not a second acquisition.
8. A scratch vault of twelve notes and a loaded `PersonRepository`. One thread loops `refresh()`
   while another loops `get_all()` and `get_by_role("vip")` for a few hundred iterations: every
   `get_all()` returns twelve, and neither thread raises.

## Acceptance Criteria — Authoring Map

Added round 10, and it is a **derived** artifact rather than a second list to maintain: it is the
result of walking the `criteria` fence set above in order and, for each `check`, naming the task that
authors a top-level `def <check>(` in a `## Write Targets` module. Task 13's closing rule orders that
walk and gives it a read-only command; this table is what the walk must return.

**Why it exists.** For nine rounds AC-5 named `test_create_is_no_clobber_and_create_stub_reuses_the_winner`
while Task 8 authored `test_create_stub_losing_a_cross_process_race_reuses_the_winner`, and AC-9 named
`test_refusals_are_loud_bounded_and_mode_governed` while Task 10 authored
`test_observe_mode_warns_and_proceeds_where_enforce_refuses`. Both were invisible to every in-build
check — the authored tests pass, the floor is green, the walls are green — and both would have failed
the exam at `building → done`, where `src/stage_advancer.py` resolves each `check` by
`getattr(mod, name)()` against a correct build. The generator was that the map was maintained per
task, from memory; the fix is to derive it from the fence set. **An `AC-N` whose `check` no task
authors is the LOUD case: a hand-back, never a test invented at exam time.**

It lives in its own `##` section rather than as a `###` under `## Acceptance Criteria` because it
grows whenever a criterion or a task moves, and a subsection that drifts must not sit inside a span a
future `ac-signoff` would hash (WI-185). It carries no `criteria` fence, only this table.

| AC | `check` | Authored by | Module |
|---|---|---|---|
| AC-1 | `test_every_door_commits_atomically` | Task 13 | `tests/test_concurrent_access.py` |
| AC-2 | `test_door_one_refuses_a_raced_content_write` | Task 13 | `tests/test_concurrent_access.py` |
| AC-3 | `test_save_refuses_a_stale_snapshot_and_succeeds_after_refresh` | Task 13 | `tests/test_concurrent_access.py` |
| AC-4 | `test_a_door_one_write_does_not_satisfy_a_door_two_payload` | Task 13 | `tests/test_concurrent_access.py` |
| AC-5 | `test_create_is_no_clobber_and_create_stub_reuses_the_winner` | **Task 8** (renamed round 10 to the AC's name, and widened to cover the no-clobber create and the book/company halves the previous check never exercised) | `tests/test_concurrent_access.py` |
| AC-6 | `test_move_note_refuses_an_existing_destination` | Task 9 | `tests/test_concurrent_access.py` |
| AC-7 | `test_filesystem_mutation_is_single_homed` | Task 12 (Walls A, B, C + all three of their batteries) | `tests/test_write_routing.py` |
| AC-8 | `test_locking_excludes_and_is_reentrant` | Task 13 | `tests/test_concurrent_access.py` |
| AC-9 | `test_refusals_are_loud_bounded_and_mode_governed` | **Task 10** (renamed round 10 to the AC's name, and widened to cover the loud-and-bounded half no check exercised) | `tests/test_concurrent_access.py` |
| AC-10 | `test_wi020_derivations_survive_the_routing` | Task 13 | `tests/test_concurrent_access.py` |
| AC-11 | `test_a_loader_overriding_repository_can_update_a_note_it_loaded` | Task 7 | `tests/test_concurrent_access.py` |
| AC-12 | `test_every_derived_loader_records_a_derivation_stamp` | Task 12 (Wall D + its `functions_calling` battery) | `tests/test_write_routing.py` |
| AC-13 | `test_committing_doors_never_return_falsy` | Task 12 (Wall E + its `falsy_returns_in` battery) | `tests/test_write_routing.py` |
| AC-14 | `test_unobserved_overwrite_refuses_and_the_escape_still_guards_the_body` | Task 13 | `tests/test_concurrent_access.py` |
| AC-15 | `test_every_door_preserves_the_targets_mode` | Task 3 authors; Task 13 owns the oracle (including the `os.fsync` ordering probe) | `tests/test_concurrent_access.py` |
| AC-16 | `test_configuration_refuses_invalid_values_and_bounds_acquisition` | Task 3 authors; Task 13 owns the oracle | `tests/test_concurrent_access.py` |
| AC-17 | `test_every_door_uses_one_resolved_path` | Task 3 authors; Task 13 owns the oracle (including the two-parents-one-note case) | `tests/test_concurrent_access.py` |
| AC-18 | `test_repository_cache_is_consistent_under_concurrent_refresh` | Task 7 authors; Task 13 owns the oracle | `tests/test_concurrent_access.py` |

Every module in the right-hand column is a declared `## Write Targets` path, which is the second half
of the derivation: a `check` authored into a module the builder may not write is unbuildable for a
different reason and is the same hand-back.

## Mitigation Folds — 2026-08-09

The three `kind: required` mitigations of the latest speaking `## Threat Model` round — **round 2, at
the end of this document, which re-emits all three ids and MOVED M1's and M3's `desc`** — each folded
into `## Design` AND an Implementation-Plan task in the same edit that wrote these records. This
section carries no rounds: the set below is restated IN PLACE against the latest speaking round, and
the round-8 records it replaces are gone rather than kept beside it. Each
`design` value is the one sentence that now carries the requirement, unwrapped from its source lines;
each `work` value is that task's own work text plus the verify clause that measures it, so the claim
and its falsifier are readable in one breath. All three land in Task 3 because all three are
enforcement inside `obsidian_schemas/vault_io.py`, which Task 3 builds and which does not exist
before it. Their CLASS folds — the generator behind M1/M3 (D2.1) and the generator behind M2 (D6) —
are in Design rather than here, because a fold record quotes a ruling; it is not the ruling.

**What moved this round, so a reader can tell a re-fold from a restatement.** M2 is byte-identical
and its fold is unchanged. M1's requirement moved from "onto the temp file before the replace" to
"onto the temp file's OWN DESCRIPTOR before any note bytes are written to it" — an ORDERING, which
D2 (the commit sequence), D2.2 (rewritten), D1 property 1, Task 3's `(M1)` clause, both
`## Verification` mode rows, AC-15's `desc` and Task 13's AC-15 oracle all now carry; the oracle
needed a new assertion because the committed note's mode is identical under both orderings. M3's
moved from "temp-file directory and replace target" to those "AND its lock sentinel's own
DIRECTORY" — which D2.3's enumeration, D3's sentinel-location paragraph, D1 property 2, Task 3's
`(M3)` clause, two `## Verification` rows, AC-17's `desc` and Task 13's AC-17 oracle now carry; that
oracle needed the two-parents-one-note case, which neither AC-17's single-process half nor AC-8's
symlink-free exclusion could see.

```fold
id: M1
desc: Layer 1 must apply the target's existing st_mode to the temp file's OWN DESCRIPTOR before any note bytes are written to it (and create with an explicit mode, never mkstemp's 0600 nor a bare umask-wide open), so a note keeps the permissions it had AND its content never exists on disk at a wider mode than the target's, not even for the span of the write and fsync.
design: Inside the lock, the door stats the resolved target for its mode BEFORE it opens the temp file, creates that temp file at the narrowest mode with an explicit-mode `os.open` (never `tempfile.mkstemp`'s `0600` as a committed mode and never a bare umask-wide `open(tmp, "w")`), applies the target's `st_mode & 0o7777` to the temp file's OWN DESCRIPTOR with `os.fchmod(fd, mode)` as the first operation on it and before a single note byte is written to it, and never chmods anything after the write — so the committed note keeps the mode it had AND its content never exists on disk at a wider mode than the target's, not even for the span of the write and the `fsync`.
landed: Task 3
work: (M1) mode on the descriptor BEFORE the first byte (D2.2, revised round 9) — inside the lock, in this ORDER: (1) if the resolved target exists, `st = os.stat(target)`, raise `WriteFailedError` when `st.st_nlink > 1` (D2.1's third cell), and take `mode = st.st_mode & 0o7777`; (2) create the temp file `fd = os.open(tmp, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)` — the narrowest possible starting point, and empty; (3) `os.fchmod(fd, mode)` as the FIRST operation on that descriptor, before any note byte is written to it; (4) only then write, `flush`, `os.fsync(fd)`, close and take a terminal form. There is NO `os.chmod` after the write — a chmod-before-replace leaves the note's complete content sitting at the create mode across the write and the fsync, which is precisely the disclosure M1 exists to prevent. When the resolved target does NOT exist there is no mode to carry, and the temp file is opened `os.open(tmp, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o666)` so umask masking gives exactly the mode `Path.write_text` gives a fresh file today. Never `tempfile.mkstemp` (`0600`) and never a bare `open(tmp, "w")` (umask-wide). Do not pass `mode` straight to `os.open`: its mode argument is umask-masked and can only narrow, so a target at `0o666` under umask `0o022` would commit at `0o644`. An `OSError` from `os.stat`, `os.open` or `os.fchmod` raises `WriteFailedError` rather than committing at a mode nobody chose. Verify: author four zero-argument top-level checks into `tests/test_concurrent_access.py` including `test_every_door_preserves_the_targets_mode` (AC-15), each taking its scratch vault from `tests/support.py:temp_dir:31`, and run `.venv/bin/python -m pytest tests/test_concurrent_access.py -q` GREEN, then THE FLOOR GREEN — AC-15's oracle including the ORDERING half specified in Task 13, which patches `os.fsync` through `tests/support.py:patcher:73` to record the mode of every `.*.tmp` in the note's directory at the moment the payload is on disk and not yet committed, asserting exactly `{0o600}`, the bits the check itself chmod-ed.
```

```fold
id: M2
desc: OBSIDIAN_SCHEMAS_LOCK_DIR must be validated at first lock acquisition and raise WriteFailedError when it is not an absolute usable directory, exactly as OBSIDIAN_SCHEMAS_LOCK_TIMEOUT and OBSIDIAN_SCHEMAS_WRITE_GUARD already do — never silently resolved against the process CWD.
design: `OBSIDIAN_SCHEMAS_LOCK_DIR` is validated at first lock acquisition exactly as the other two settings are — it must be a non-empty absolute path naming a usable directory (created with `ensure_dir` if absent), and a relative, empty or unusable value raises `WriteFailedError` rather than being resolved against the process CWD, which would key two writers' sentinels in different directories and evaporate Layer 2's mutual exclusion with no sound.
landed: Task 3
work: (M2) configuration validity — read all three env vars through ONE private helper `_env_setting(name, parse, validate)`, which is the module's ONLY `os.environ` access; a second `os.environ` reference anywhere in this file is forbidden. `OBSIDIAN_SCHEMAS_LOCK_DIR` must be a non-empty absolute path naming a usable directory and raises `WriteFailedError` when it is relative, empty or unusable — never resolved against the process CWD. All refusals use the existing reason `"write did not complete"` (`obsidian_schemas/errors.py:REASONS:96`); mint no new literal here, and do not edit `REASONS` in this task. Verify: author `test_configuration_refuses_invalid_values_and_bounds_acquisition` (AC-16) into `tests/test_concurrent_access.py` as a zero-argument top-level check taking its scratch vault from `tests/support.py:temp_dir:31`, and run `.venv/bin/python -m pytest tests/test_concurrent_access.py -q` GREEN, then THE FLOOR GREEN.
```

```fold
id: M3
desc: Every door must derive its temp-file directory, its replace target AND its lock sentinel's own DIRECTORY from the same resolved path the sentinel hash and the stamp registry are keyed on, or refuse a symlinked target with WriteFailedError — never leave a symlink replaced by a regular file, and never let two paths naming one real note key their sentinels in two directories.
design: Every door resolves its path exactly once at entry — `target = Path(path).resolve()` — and every later step of that call uses that one value: the lock's sentinel HASH and its sentinel DIRECTORY `target.parent/.obsidian-schemas-locks/`, the in-process lock key, the stamp-registry key, the temp file's directory `target.parent`, the `stat_stamp` precondition and the terminal `os.replace`/`os.link` argument, so no door ever mixes a resolved path with an unresolved one; `move_note` resolves `src` and `dest` the same way and additionally refuses with `WriteFailedError` when `Path(src).is_symlink()`, because a whole-file move through a symlink has no single correct meaning.
landed: Task 3
work: (M3) one resolved path per door, INCLUDING the sentinel's own directory (D2.3, D3, revised round 9) — resolve the path ONCE at entry (`target = Path(path).resolve()`, non-strict) and key the in-process lock, the registry, the temp directory `target.parent`, the `stat_stamp` precondition and the terminal `os.replace`/`os.link` on that single value. The file sentinel is `target.parent / ".obsidian-schemas-locks" / f"{h}.lock"` with `h = hashlib.sha256(str(target).encode("utf-8")).hexdigest()[:32]` — its DIRECTORY derived from the resolved `target.parent`, never from the caller's unresolved parent, so two paths naming one real note cannot key one hash into two directories and both acquire. Under `OBSIDIAN_SCHEMAS_LOCK_DIR` the home is that one configured directory for every note. `move_note` resolves `src` and `dest` the same way and refuses a `Path(src).is_symlink()` source with `WriteFailedError`. No door mixes a resolved value with an unresolved one. Verify: author four zero-argument top-level checks into `tests/test_concurrent_access.py` including `test_every_door_uses_one_resolved_path` (AC-17), each taking its scratch vault from `tests/support.py:temp_dir:31`, and run `.venv/bin/python -m pytest tests/test_concurrent_access.py -q` GREEN, then THE FLOOR GREEN — AC-17's oracle including the two-parents-one-note case specified in Task 13, which locks `<v>/real/note.md` and `<v>/alias/note.md → ../real/note.md` in turn and asserts exactly ONE `.obsidian-schemas-locks/*.lock` exists in the whole vault, under `<v>/real/`, then holds one path's lock in a background thread and asserts the other raises `WriteFailedError` at `OBSIDIAN_SCHEMAS_LOCK_TIMEOUT="0.05"`.
```

## Verified Diagnosis

This spec makes load-bearing claims that the current system behaves incorrectly. Each is grounded in
a falsifiable artifact re-read against this tree on 2026-08-09.

1. **Every write in the package is an unlocked, non-atomic read-modify-write.** Falsifier: a grep
   for `flock|fcntl|fsync|os\.replace|mkstemp|NamedTemporaryFile|threading|RLock` across
   `obsidian_schemas/` and `scripts/` returns zero hits, while 14 bare `Path.write_text` calls exist
   at `obsidian_schemas/writer.py:236,283,333,365`; `obsidian_schemas/repositories/base.py:390`;
   `obsidian_schemas/repositories/person.py:1543,1554,1652,1769,1845,1912`;
   `scripts/lint_vault.py:876,894`; `scripts/migrate_person_to_discuss.py:104`. Independently
   re-derived by the architect (round 2) and the data-premise gate (rounds 1–3), cell for cell.
2. **`save()` overwrites frontmatter wholesale from a cache snapshot that can be hours old.**
   Falsifier: `obsidian_schemas/writer.py:217-218` builds `fm = model_to_frontmatter(entity, …)` from
   the entity argument and never merges with disk; `obsidian_schemas/repositories/base.py:save:321`
   passes an entity from `self._cache` (`base.py:142`), populated at `load()` (`:169-197`) and
   invalidated only by an explicit `refresh()` (`:419`). The WI-126 guard does not cover it —
   `obsidian_schemas/writer.py:_body_content_lines:69` iterates `body.splitlines()` only and its own
   docstring says "The frontmatter survives … the body is the loss" (`:47-48`).
3. **`create_stub`'s collision guard reads the cache, not the disk, so a concurrent create clobbers
   silently.** Falsifier: `obsidian_schemas/repositories/person.py:1429` calls `self.get(clean_name)`,
   which is `self._cache.get(...)` behind `_ensure_loaded()`
   (`obsidian_schemas/repositories/base.py:get:258-269`) — a lazy load-once, not a re-stat. The
   overwrite that follows is not caught by WI-126: `obsidian_schemas/writer.py:211` runs the drop
   check only `if existing_lines:`, `_body_content_lines` (`:69-80`) discards blank and `#`-prefixed
   lines, and a freshly-minted person stub's body is `"## To Discuss\n\n## Timeline\n\n## Notes\n"`
   (`obsidian_schemas/body_sections.py:ENTITY_BODY_CONFIG:306`) — headings only — so the set is
   empty, the guard no-ops, and `writer.py:236` rebuilds the note from the in-memory entity.
   `obsidian_schemas/repositories/book.py:create_stub:273` and
   `obsidian_schemas/repositories/company.py:create_stub:153` carry no collision branch at all.
4. **`quarantine_garbage` carries a live TOCTOU.** Falsifier: `scripts/lint_vault.py:1036` guards
   `dest.exists()` and `:1038` calls `src.rename(dest)` with nothing held between them;
   `Path.rename` clobbers silently on POSIX when the guard loses the race.
5. **`write_markdown_file`'s `overwrite=False` guard is a check-then-mutate gap.** Falsifier:
   `obsidian_schemas/writer.py:186-187` raises `FileExistsError` for "destination exists"; the write
   it guards is 50 lines later at `:236`.
6. **The existing routing predicate cannot back a "no un-routed mutation" claim, and its node-shape
   gate is as load-bearing as its vocabulary.** Falsifier: `tests/derivations.py:_is_write_call:189-195`
   is `isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in
   {"write_text", "write_bytes"}`. The vocabulary half means it resolves none of the other mutation
   kinds — including the live `Path.rename` at `scripts/lint_vault.py:1038`. The
   **`ast.Attribute` half** means it resolves no bare-name call at all, so a routed site calling a
   bare `write_note(...)` would be invisible to it and to the three sweeps that consume it
   (`functions_parsing_then_writing:227`, `_taints_a_write:301`, `non_completed_write_sites:507`).
   This is the claim D7's module-attribute call-form ruling is built on; if it were false, that
   ruling would be unnecessary.

7. **Entity derivation happens in THREE functions, not one, and the observation side of the door-2
   boundary must be derived rather than named.** Falsifier: `obsidian_schemas/repositories/base.py:
   load:187` and `:393` both call `self._load_file(...)` — dynamic dispatch — while
   `obsidian_schemas/repositories/book.py:_load_file:57` (`:57-81`) and
   `obsidian_schemas/repositories/meeting.py:_load_file:64` (`:64-85`) are complete overrides that
   never call `super()._load_file` and return `doc.entity` themselves (`book.py:76`,
   `meeting.py:80`). The tree states the corpus in the module this spec's Tasks 2 and 11 both cite:
   `tests/derivations.py:load_file_implementations:355` ("four classes resolve to three functions
   today"), pinned at `tests/test_loud_fail_parse.py:301`. Every call of `parse_markdown_file` under
   `obsidian_schemas/` and `scripts/` is one of those three (`base.py:239`, `book.py:74`,
   `meeting.py:78`). This is the claim D5's (A′) and D10's Wall D are built on; a design recording
   the stamp in `base.py:226` alone would leave every book and meeting unstamped and turn the
   ordinary `BookRepository.save`/`MeetingRepository.save` into `NoteAlreadyExists`.
8. **No test in the suite saves a book or a meeting, so that failure would land GREEN.** Falsifier: a
   sweep of `tests/` for `.save(` returns **ten** calls — `tests/test_repositories.py:644,661,676,693,
   709,725` and `tests/test_writer.py:432,434,440,441` — all `PersonRepository`. *(Count corrected
   round 7: the round-5 text said eight and named only `test_writer.py:432,441`, missing `:434` and
   `:441`'s sibling `:440`. The load-bearing half — that not one of them is a `BookRepository` or
   `MeetingRepository` — is unchanged, and the two extra calls are classified in D12.1's β sweep.)*
   This is why AC-11 is a
   behavioural criterion rather than an inspection note: the routing wall's oracle is
   mutation-capability single-homing and is structurally blind to a missing observation.

9. **An attribute-NAME oracle over stdlib mutation verbs cannot be made green against this tree, so
   the wall's vocabulary must discriminate by provenance.** Falsifier, run 2026-08-09 over
   `obsidian_schemas/` and `scripts/`: `.replace(` resolves to **fourteen call nodes across nine
   lines** — `obsidian_schemas/models.py:110`, `:136` (×2); `obsidian_schemas/repositories/book.py:94`,
   `:124`, `:207`, `:255` (×2 each); `obsidian_schemas/repositories/meeting.py:211`;
   `obsidian_schemas/repositories/person.py:1141`; `scripts/lint_vault.py:889` — every one a
   `str.replace`; and `.copy()` resolves to `obsidian_schemas/writer.py:220`,
   `obsidian_schemas/parser.py:176` and `:211` — every one a dict copy. `models.py`, `parser.py` and
   `person.py`'s cleaning path are on `## Scope Boundary`'s untouchable list and none of these is a
   filesystem call, so no `ensure_dir`-shaped relocation exists. This is the claim D10.1's
   `PATH_MUTATION_NAMES` / `MODULE_MUTATION_NAMES` split and R10 are built on; were it false, the
   simpler name-matched vocabulary would be correct.
10. **The full vocabulary sweep returns only three live filesystem tokens, which is what makes the
    homonym cell small and nameable.** Falsifier: sweeping every token of the combined vocabulary as
    a call under both roots returns `write_text` (14), `mkdir` (2) and `rename` (1) as filesystem
    uses; `replace` (14 nodes) and `copy` (3 nodes) as non-filesystem uses; and **zero occurrences of
    every other token**, including zero `open(` calls of any mode. So the collision cell is exactly
    two verbs today, and among `pathlib.Path`'s mutators `replace` is the only name with a builtin
    homonym — which is why R10 is one declared blind spot rather than an open-ended class.

11. **WI-020's two acceptance modules are half derivation and half BEHAVIOUR, and three of their
    behavioural assertions depend on facts routing removes.** Falsifier, each read in the tree
    2026-08-09: `tests/test_loud_fail_write.py:153` is
    `monkeypatch.setattr(Path, "write_text", lambda self, *a, **k: (_ for _ in ()).throw(boom))` and
    `:155-156` asserts `repo.append_to_timeline(...)` raises `WriteFailedError` — the fault is
    injected at the call D2 replaces with an fd commit, and D1's closing paragraph and Wall E's
    justification both state in terms that no `vault_io` function names `write_text`.
    `tests/test_loud_fail_parse.py:450` is the same mechanism on the CHAINABLE contract
    (`:451-457`, `caught.value.__cause__ is boom`). And `tests/test_loud_fail_write.py:63,66` and
    `:77,89` seed with a raw `path.write_text(...)` and then call
    `write_markdown_file(path, entity=entity, body="", overwrite=True)` expecting
    `UnverifiableBodyError`, which under D8 step 5 is `NoteAlreadyExists` because no repository loads
    either path. This is the claim D12 is built on; were it false, D7's four static derivations would
    be the whole of the routing's effect on that battery.
12. **The zero case also fires against the package's own documented public recipe, and its in-suite
    twin.** Falsifier: `tests/test_writer.py:test_overwrite_when_requested:158` seeds with
    `file_path.write_text("original content")` at `:169` and calls `write_markdown_file(...,
    overwrite=True, allow_body_replacement=True)` at `:171` — and `allow_body_replacement` is NOT
    `allow_unverified_overwrite`, which D8(d) mints as a separate flag in the same shape.
    `tests/test_writer.py:test_roundtrip_preserves_data:287` seeds at `:314`, calls
    `parse_markdown_file` at `:317` and writes back at `:322`; that sequence is
    `README.md:317-338`'s "Round-Trip Preservation" recipe verbatim, and both
    `parse_markdown_file` and `write_markdown_file` are exported
    (`obsidian_schemas/__init__.py:37,42,111,115`). An entity IS derived from those bytes, yet no
    stamp is recorded, because D5 rules the derivation corpus to be the three `_load_file` functions
    and nowhere else. This is the claim D5's "The cell Wall D(ii) cannot reach" and close-out step 5
    are built on. The counterpart negative result is what bounds it: sweeping ALL 17
    `write_markdown_file(` and 8 `.save(` call sites under `tests/` returns exactly these two plus the
    two in claim 11 — every other site either targets a non-existent path, was committed through door
    2 earlier in the same test, or was loaded by a repository first (D12.1).

13. **The package has no permission, symlink or hard-link handling at all, so M1, M3 and D2.1's
    `st_nlink` rule are behaviour this item newly INTRODUCES rather than inherits.** Falsifier, run
    2026-08-09 over this tree: `grep -rn 'chmod\|st_mode\|umask\|is_symlink\|st_nlink\|listxattr'
    obsidian_schemas/ scripts/` returns **zero** hits. Combined with claim 1 — every write is a bare
    `Path.write_text`, which opens `"w"` and truncates in place, so the inode and therefore the mode
    survive, and which follows a symlink to the real file — this is what makes D2.1's framing correct:
    the properties are not *currently handled somewhere else*, they are *currently free*, and Layer 1
    is what stops them being free. This is the claim D2.1's table, D2.2, D2.3 and R14 are built on;
    were it false, the fold would be a change to existing handling rather than the introduction of
    new handling, and the correct edit would be somewhere else entirely.

14. **A repository lock taken only by the writers buys a lock-free reader NOTHING, because `load()`
    empties the live mappings and repopulates them key-by-key.** Falsifier, read in the tree
    2026-08-09: `obsidian_schemas/repositories/base.py:load:176-178` is
    `self._cache.clear()` / `self._file_map.clear()` / `self._skipped.clear()` on the LIVE containers,
    and `:190-191` sets one key at a time inside the glob loop at `:186-193`. `get_all:271` returns
    `list(self._cache.values())` at `:279` — one atomic C-level call over a HALF-BUILT mapping, so a
    reader gets a complete list of an incomplete vault with no exception — and the iterating readers
    `person.py:get_by_role:1233`, `book.py:262`, `company.py:130` and `meeting.py:402` walk
    `self._cache` while `load()` is inserting into it, which is CPython's
    `RuntimeError: dictionary changed size during iteration`. `refresh:419` compounds it: it snapshots
    at `:434-435` and calls `load()` at `:440`, so the clear-and-repopulate window is on the very path
    the March scope names. This is the claim the Edge Cases replace-the-mapping rule, Task 7's cache
    paragraph and AC-18 are built on; were it false — were the lock alone sufficient — the six-word
    "add the per-repository `threading.RLock`" the plan carried before round 9 would have been the
    whole of the work, and AC-18's check would be asserting a property the design already had.

Claim (3)'s consequence — that the cross-process clobber is *silent* — is the one this item's Intent
turns on, and it is the one the architect's round-2 finding and the data-premise gate's round-3
corroboration both verified independently in code. Claims (9) and (10) are the ones D10's walls turn
on, and they are the reason Task 0 executes every predicate before the vocabulary is frozen rather
than asserting a first-run green in prose. Claim (14) is the one the item's ORIGINAL March scope
turns on, and it is why that scope is now a rule with an oracle rather than a lock with neither.

## Scope Boundary

**What we're NOT doing.**

- **Making READS fresh.** `get()`, `get_all()` and `resolve()` still serve whatever `load()` put in
  `_cache`. The stamp precondition refuses a stale *write*; nothing here makes a *read* coherent.
  That is residual R2, its owner is the caller via `refresh()`, and inventing invalidation-on-stat or
  a filesystem watch here would be a second design (`docs/watch-repository.md`,
  `docs/ttl-based-cache.md` and `docs/file-watching-realtime-updates.md` are the items that own it).
- **Merge semantics for `save()`.** Rejected as option (a) in `## Approach` for want of a field-level
  precedence rule that does not exist in this package and cannot be invented here without silently
  reinstating deliberately-cleared fields for three consumer repos. Reversing this needs Dave to
  originate the precedence rule and is a separate item.
- **Merging the losing create's non-identifier fields** (`company`, `created_by`). Residual R7. Same
  (a)-shaped decision, same owner.
- **Giving `BookRepository` and `CompanyRepository` a reuse-on-collision branch.** That is a
  resolution-policy change on two entity types (`docs/company-stub-parity.md` is where it belongs),
  and it is a strictly smaller question once the door refuses rather than clobbers.
- **Moving `_normalize_address_fields` down to the door.** It sits at
  `obsidian_schemas/repositories/person.py:save:1265`, one frame above `write_markdown_file`, and so
  does not run for books or meetings. Whether it moves is WI-021's call
  (`docs/write-door-bypasses.md:18`); this item neither moves it nor depends on where it lands, and
  it names door 2's entry inside `write_markdown_file` as the seam WI-021 hangs on.
- **Giving door 1 or door 3 a WI-021 surface.** They are content- and inode-level; there is nothing
  entity-shaped there to validate. The frontmatter-level paths WI-021 names that route through door 1
  — notably `obsidian_schemas/repositories/base.py:update_fields:339` — need their own ruling in
  WI-021 and do not get one here.
- **A single-writer daemon, or routing writes through Obsidian's MCP API.** Both rejected with
  reasons in `## Approach`; neither is re-opened.
- **Refactoring `_load_file` into a template method.** Closure (B) in D5 — a base loader that stats,
  records and delegates parsing to a subclass hook — is total by construction and is rejected on
  blast radius: it would move the loader corpus from three functions to one, turning
  `tests/test_loud_fail_parse.py:301`'s `== 3` red and the residue name-set assertion at `:332` red
  with it, in a file this plan orders untouched, and it would relocate each subclass's own broad
  `except → _note_skip` (WI-020's no-abort guarantee). The builder must not "improve" (A′) into (B)
  while implementing it. Reversing this is Dave's call and is now a change to a written ruling.
- **A delete door.** The cell is empty in `obsidian_schemas/` and `scripts/` today, and it must not
  get a door by assumption either — Wall B/C of D10 turn a future `unlink` into a red build demanding
  a ruling.
- **Consolidating `scripts/migrate_person_to_discuss.py:migrate_person_file:70`'s hand-rolled
  `content.split('---', 2)`.** It is the last surviving split (rider #3, live only for `scripts/`),
  and it is a *parse* consolidation, not a write one. Routing that file's write through door 1 is in
  scope; rewriting its parse is not.

- **Making Wall A see a `Path.replace` on an unqualified receiver.** R10, ruled in D10.3. `replace` is
  provenance-matched only, because the name-matched alternative is Wall A red on day one against
  fourteen live `str.replace` call nodes in files this section forbids the builder to touch. The
  builder must not "improve" the vocabulary by adding `replace` to `PATH_MUTATION_NAMES`, nor drop it
  from `MODULE_MUTATION_NAMES` — D10.5 ships a named near-miss fixture on exactly this, and Task 0
  surfaces the fourteen sites before any routing edit exists.
- **Editing `tests/test_loud_fail_parse.py` or `tests/test_loud_fail_write.py` beyond D12.3 Table 3a
  rows 1–4.** Both are write targets again (round-7 reversal, argued in `## Implementation Plan`),
  and the re-admission is exactly four enumerated lines: two fault-injection points moved to
  `vault_io.write_note`, and two `allow_unverified_overwrite=True` keywords. **Untouchable inside
  those same modules:** the `write_paths`/`loose_paths` sets at
  `tests/test_loud_fail_parse.py:110-137`, the count pins at `:300-301`, the residue name-set at
  `:332`, the `SiteId` classification map at `tests/test_loud_fail_write.py:126-139`, and every
  assertion in either file. A red the table does not literally describe is a hand-back (D12.4), never
  a fifth edit and never a relaxed assertion.
- **Making `parse_markdown_file` a stamp-observation point.** Ruled against in D5, "The cell Wall
  D(ii) cannot reach": the parser cannot know whether its caller adopted what it returned, so
  recording there would advance a stamp for a payload nobody kept and re-open the round-3 architect's
  note #1 one door over (LESSONS #43). The builder must not "fix" the README round-trip break that
  way; the ruled answer is `allow_unverified_overwrite=True` plus close-out step 5.
- **Preserving anything inode-borne beyond the permission bits.** Ownership, extended attributes,
  ACLs, macOS Finder tags, file flags and the inode number are R14, enumerated cell by cell in D2.1
  and declared rather than attempted. The builder must not add an xattr or `os.chown` copy "while in
  there": each would be a new capability inside the door with no consumer asking for it, and the
  ownership one cannot work without privilege this library never has.
- **Giving `move_note` a symlink POLICY.** D2.3 refuses a symlinked source rather than choosing
  between relocating the link and relocating its target. If a caller ever needs one of those two
  meanings, that is Dave's call to originate and a change to a written ruling — not a builder
  decision taken to make a fixture pass.
- **Making the hard-link case work.** A resolved target with `st_nlink > 1` is refused (D2.1). A
  copy-through-all-links implementation is a different mechanism from the one `## Approach` rules and
  is out of scope; the refusal is loud and the vault has no hard-linked notes today.
- **Making the subclasses' own INDEXES copy-on-write, or taking a lock on any read path.** Edge Cases
  scopes the replace-the-mapping rule to `_cache` and `_file_map`, locks `_skipped`'s two readers
  because it is an append-only diagnostic, and declares the index cell: a lock-free index read
  concurrent with a `refresh()` can still observe a partial index, which is unchanged from today. The
  bound has two halves and only one of them is closed by the re-check argument (Edge Cases, round 10):
  the WRONG-VALUE half is closed, because every index value is re-checked against `_cache` before use
  (`obsidian_schemas/repositories/book.py:194`, `meeting.py:256`, `:299`, `:314`) and a partial index
  degrades to a MISS; the ITERATE-A-LIVE-MAPPING half is NOT, because
  `obsidian_schemas/repositories/person.py:get_by_phone:457` iterates `self._phone_index.items()` and
  can raise `RuntimeError: dictionary changed size during iteration`. That is pre-existing and loud,
  it is explicitly not required by the threat model, and it is named here so the exclusion is a
  ruling over both halves rather than an argument that covers one. The builder must
  not "while I'm here" the indexes into the rule, and must not add a lock to `get`, `get_all`,
  `get_by_role`, `get_file_path` or any subclass lookup — lock-free reads are the framing this scope
  was originated under, and widening it is Dave's call.
- **Narrowing D8 step 5's zero case so `overwrite=True` against an existing target is not a create.**
  Ruled against in D12.2 as fork option (γ): `BaseRepository.save` defaults `overwrite=True`, so the
  exemption would exempt `create_stub`'s losing write — the exact path door 2c exists for — and
  property 1 of `## Approach`'s total rule would stop being total.

**Unchanged files — the builder should not touch these.** `obsidian_schemas/parser.py`,
`obsidian_schemas/models.py`, `obsidian_schemas/identifier.py`,
`obsidian_schemas/name_validation.py`, `obsidian_schemas/name_cleaning.py`,
`obsidian_schemas/body_sections.py`, `obsidian_schemas/repositories/company.py`,
`obsidian_schemas/repositories/__init__.py`; every `tests/` module not named in `## Write Targets`;
`CLAUDE.md`, `README.md`, `SESSION_LOG.md`, `state/**` and `pipeline-runners.yaml` (all outside the
cage by design). `pyproject.toml` is a conductor-committed precondition, not a builder write target.

## Risk Analysis

This item replaces every write path in a library three repos install `-e`, so it touches work Dave
relies on daily.

| # | What could go wrong | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| 1 | `filelock` not seeded into `.venv`; the build discovers it as a red floor mid-way and burns an attempt | Medium — it is a new dependency and the precondition probe cannot see it (D0.1) | High — a wasted build attempt | Task 1 aborts in the first minute with a named hand-off, before any edit |
| 2 | `FileExistsError` → `NoteAlreadyExists` breaks a consumer's `except` clause | Medium | Medium — a create collision escapes as an uncaught `ValueError` | Declared in D8b; close-out consumer audit (Verification step 3); `NoteAlreadyExists` subclasses `ValueError`, so a consumer's broad `except ValueError` still catches |
| 3 | The new refusals fire more often than expected and turn a working pipeline into a failing one | Medium — nothing in this doc measures the real collision rate | High — HAL9000 request failures | `observe` mode (D6/D9/R9): one env var, no code change, WARNING-only, today's semantics; roll forward per consumer after measuring |
| 4 | Deadlock between two writers | Low — only door 3 takes two locks, in sorted order | High if it happened | Sorted-path acquisition; a `10.0`s default timeout that converts a hang into a loud `WriteFailedError` |
| 5 | Lock sentinels become visible in Obsidian (search or graph), creating a self-inflicted corruption class | Low — obligation 3 observed not-visible for filename search | Medium | `OBSIDIAN_SCHEMAS_LOCK_DIR` fallback is already built; close-out step 2 widens the observation to full-text and graph |
| 6 | Widening `_is_write_call` shifts WI-020's four derived sweeps and turns AC-1/AC-5 red against correct code | Low, revised round 6 — previously Medium, when the mitigation was a contingency licence rather than a derivation | High — a build-exit REVISE, or worse, a silent relaxation of a previous item's shipped property | Three layers, in order: the three-primitive door shape keeps every parse, dedup and falsy return in its own function body (qualnames stable); D7's module-attribute call-form ruling keeps `_is_write_call`'s `ast.Attribute` gate matching (call form stable); and D7 (1)–(4) DERIVES the outcome for each consuming sweep, which Task 0 pins pre-routing and Task 11 pins post-routing. **Revised round 7:** the two WI-020 modules are write targets again, but narrowly — D12.3 Table 3a enumerates four permitted lines, every asserted property is invariant across them, `## Scope Boundary` names the four derivation sets inside those files as untouchable, and any other red is D12.4's fourth branch (a hand-back). The static half of this risk is unchanged; its behavioural half is Risk 14 |
| 7 | Performance: a lock acquisition, two stats and an fsync per write | Low | Low — a vault write is already milliseconds and this is a foreground human-scale workload, not a hot loop | Measured informally in close-out step 1; no mitigation planned |
| 8 | A note is deleted between a repository's load and a `save()`, and the refusal reads as a bug | Low | Low | Ruled in D4: a vanished target is a mismatch, not a create; `StaleEntityWrite` names the path |
| 9 | A future fifth repository declares its own `_load_file`, forgets the stamp, and that entity type's first `save()` after load starts refusing — silently green in every existing check | Medium — it is exactly what happened to `book.py`/`meeting.py` in round 4's draft | High — a whole entity type loses its update path | Wall D(i) over the DERIVED loader corpus (D10) turns it into a red floor naming the loader; AC-12 |
| 10 | An entity derivation added outside the loader corpus (a script, a helper) writes from bytes nothing stamped | Low today — the corpus and the `parse_markdown_file` call sites coincide exactly | Medium | Wall D(ii) asserts the two sets are EQUAL, so a new derivation site is red rather than silent |
| 11 | Wall A goes red on a vocabulary token and the cheapest green from inside the cage is to drop the token — the wall narrowing its own claim | Low, revised round 6 — it was reachable in the round-4 draft (`mkdir`) and the round-5 draft (`replace`, `copy`); Task 0 now surfaces it in minute two, before any routing exists to protect | High — an undeclared weakening of what AC-7 advertises | Ruled out in writing in D10.3, Task 0, Task 9 and Task 12; both `mkdir` sites route through `ensure_dir` before Task 12 runs; the MUST-MATCH battery keeps `p.mkdir(parents=True)` and `os.makedirs(d)`, and the NOT-matched battery pins `s.replace`, `frontmatter.copy()` and `p.replace(q)` so neither a narrowing nor a widening can pass silently |
| 12 | The vocabulary or a call form is wrong in a way nobody anticipated, and the builder discovers it deep in the plan with routing already landed | Low — this is the class rounds 4 and 5 lived in, and Task 0 is its close | Medium — a wasted build attempt, versus a corrupted acceptance battery before | Task 0 executes every wall predicate against the untouched tree and pins nine rows in the Build Log against D10.6 Table 1; Task 11 re-runs eleven rows against Table 2. A mismatch either time is a HAND-BACK with evidence, and the vocabulary, the tables and WI-020's battery are all named as off-limits repairs |
| 13 | A future in-package writer spells an atomic rename as `p.replace(q)` and Wall A does not see it | Low — the door is the only place a replace legitimately occurs, and D2 orders the `os.replace` form | Medium — one un-routed mutation site, detected at the next review rather than by the floor | Declared as R10 rather than hidden; Wall B independently reds any `os` member outside `OS_READONLY_NAMES` wherever it is named; and D10.5 ships `p.replace(q)` as a NAMED near-miss fixture citing R10, so a reader who meets the gap meets the ruling and the fourteen `str.replace` sites that price the alternative |
| 14 | A behavioural assertion in the existing suite depends on a fact routing removes, and the build discovers it as a red with no ruling — the round-6 class | Low, revised round 7 — it was the shape of every round-6 finding; three axes are now swept at source and the fourth branch is a hand-back | High — either a build abort, or a caged builder quietly weakening a previous item's shipped property to buy a green | D12.1 sweeps each axis by its DECLARING shape over all of `tests/` (2 + 4 + 1 sites, with the negative result for the other 20 stated); Table 3a enumerates every permitted edit line by line ahead of the build with its asserted property unchanged; Task 16 RUNS the whole floor and pins the complete red set against Table 3b; and D12.4's fourth branch makes an unswept red a hand-back rather than a judgement call. AC-10 and AC-14 |
| 15 | The documented README round-trip recipe starts raising `NoteAlreadyExists` for a consumer who never reads this doc | Medium — it is public API and the recipe is published | Medium — a working consumer script starts failing loudly (never silently, and never destructively) | Ruled and stated as a consumer-facing break in D5; the answer is one keyword, `allow_unverified_overwrite=True`, which keeps the WI-126 guard (D8(d), corrected round 7); close-out step 5 updates `README.md` outside the cage; `observe` mode (R9) is the zero-code-change rollback |
| 16 | Inode replacement silently rewrites something a consumer depends on — a note's permission bits, the file a symlink points at, or a hard-linked sibling's bytes | Medium — it is a side effect of the mechanism, not of the feature, so nothing in the item's stated subject would surface it; the threat model found it and no prior gate had | High — the permission direction is a disclosure on a vault of PII-bearing person notes, and the symlink direction leaves stale bytes at the real target with the write reporting success | D2.1 enumerates every inode-borne property and rules each cell rather than closing only the two that were named: mode preserved (M1, AC-15), symlinked write doors resolved and the move door refused (M3, AC-17), a multiply-hard-linked target refused, and the rest declared as R14. All three refusals are `WriteFailedError`, never a silent proceed. **Round 9 tightened both closed cells after the threat model's round-2 re-review**: M1 is now an ORDERING (the mode reaches the temp file's descriptor before the first note byte, so the payload never sits at a wider mode across the write and the fsync — a committed-mode oracle is blind to that window, so AC-15 gained an `os.fsync`-time probe), and M3 now reaches the lock sentinel's own DIRECTORY as well as its hash, so two paths naming one note cannot take two locks and both proceed (AC-17 gained the two-parents case). Close-out step 3b is the consumer sweep for the permission assumption, with a different grep from 3a's |
| 18 | The repository cache lock ships as a lock nobody's reader takes, over mappings `load()` still empties in place — so the item's ORIGINAL March scope lands looking done and is not | Medium before round 9 — the plan ordered it in six words with no verify clause, no `## Verification` row and no `criteria` fence, so every in-build check would have been green over it | Medium — a multi-threaded consumer reads a half-built vault as the whole one, or takes a `RuntimeError` mid-iteration, and nothing in this item would have caught either | Edge Cases states the rule over the WHOLE mutation surface (replace the mapping under the lock, never mutate a live one) and — **round 10** — makes that surface TOTAL BY CONSTRUCTION rather than by enumeration: one `BaseRepository._adopt` door is the only per-entity writer of `_cache`/`_file_map`, and all five adopting functions call it (`load` is a bulk rebuild and deliberately does not). That correction was forced by this item's own Task 8, which adds a FIFTH adoption site the round-9 nine-site grep could not reach because the grep ran over the pre-build tree; Task 7 carries the door as work, Task 8 calls it by name, `## Verified Diagnosis` claim 14 grounds why the lock alone is insufficient, AC-18's check is the behavioural falsifier and RED against the pre-round-9 reading, and Table 2's `functions_calling(files, "_adopt")` set-equality row is the surface falsifier for a sixth site written without the door. The subclass indexes are declared out of the rule rather than silently included, with both halves of their bound now named |
| 17 | R12's one-process sequence — an `append_to_timeline` followed by a `save()` on the same entity — starts raising `StaleEntityWrite` for a consumer with no concurrency at all | Medium — it is an ordinary HAL9000 shape and, unlike the 2u and 2c breaks, needs no second writer to fire, which makes it the most likely of the three to be met first | Medium — a working call sequence fails loudly, never silently and never destructively | Ruled with its consumer face stated plainly in D12.5 item 4; the remedy is already in the tree (`refresh()`, or the `update_fields` route `_writeback_identifier` uses); `observe` mode is the zero-code-change measure-first option; close-out step 3c sweeps the three consumer repos for the sequence by name. NOT closed by making the body writers re-register, which would advance a stamp for a payload nobody re-derived (LESSONS #43) |

**Rollback plan.** Three levels, cheapest first. (i) Set `OBSIDIAN_SCHEMAS_WRITE_GUARD=observe` — the
refusals become warnings and semantics revert to today's, with Layer 1's atomicity retained (it is
pure upside and has never needed a ramp). (ii) Revert the routing commits, leaving `vault_io.py` in
place and unused. (iii) Revert the whole change; there is no on-disk migration to undo and lock
sentinels are disposable (`rm -rf` any `.obsidian-schemas-locks/` while no writer runs).

**Migration path.** None required — see Edge Cases, "Migration / backfill". The semantic transition
for consumers is the ramp in (i): ship `observe`, measure, then move to the default `enforce`.

## Architectural Review — 2026-08-09

**Recommendation: REVISE — return to exploration**

### Trigger check

Fired: new module/primitive (the composite write door); touches >3 existing files across
different concerns (`writer.py`, `repositories/base.py`, `repositories/person.py`,
`scripts/lint_vault.py`); replaces/significantly extends a core system (every write path in
the package); effort > 1 day. Additionally the resulting semantics become a contract for
three consumer repos, per the campaign's own cross-project note
(`docs/backlog-campaign-2026-07-05.md:95`).

### What holds — not re-litigated

Re-verified against the tree, not taken from the doc:

- **The corruption premise is still live.** A grep for `flock|fcntl|threading|Lock|fsync|
  os.replace|mkstemp|NamedTemporaryFile` across `obsidian_schemas/**` and `scripts/**`
  returns zero hits. Every write is still a bare `Path.write_text` (`writer.py:236,283,333,365`;
  `base.py:390`; `person.py:1543,1554,1652,1769,1845,1912`; `scripts/lint_vault.py:876,894`).
  Unlocked, non-atomic read-modify-write, as claimed.
- **The layered-composite ruling is right and should be kept.** Layer 1 (temp + fsync +
  `os.replace`, same directory) is the universal standard for atomic file replacement — git,
  sqlite, and every editor do exactly this. Layer 2 (per-file advisory `flock`) is the standard
  local-host answer for cross-process exclusion. Layer 3 (capture `(mtime_ns, size)` at read,
  re-stat immediately before replace, raise on change) is what VS Code, vim, and Obsidian
  itself do for external modification. **This design converges on the outside view rather than
  diverging from it**, so the prior-art dimension's blocking conditions (Nth recurrence of a
  constraint; a deferral with a named re-entry condition and no probe) do not fire — the
  filesystem probe *is* minted, as spec obligation #1, with a named owner and a stated
  "re-open this ruling" consequence. The next round should not over-correct here.
- **Rejecting the single-writer daemon is correct** and correctly reasoned (it does not remove
  the second writer, and the "fall back to direct writes" escape is the circumvention-helper
  shape).
- **The honest-residual paragraph is the right instinct** and its verbatim-in-spec requirement
  should survive.

### Blocking issues

**1. The whole-entity `save()` door is never addressed, and the "closed by construction" claim
does not hold for it — leaving the item buildable two ways (`## Approach`, `## Intent`).**

The Exploration's load-bearing structural claim is that because the read happens inside the
lock, "a caller structurally cannot write from a stale snapshot — the lost-update class among
cooperating writers is closed by construction." That holds only for callers whose change is
expressible as a *transform over freshly-read content*. It does not hold for the package's
entity-snapshot door:

- `BaseRepository.save()` (`base.py:294-337`) writes an entity built from `self._cache`
  (`base.py:142`), populated once at `load()` (`base.py:169-197`) and invalidated only by an
  explicit `refresh()` (`base.py:419-457`). In a long-lived HAL9000 FastAPI process that
  snapshot can be hours old.
- `write_markdown_file` rebuilds frontmatter wholesale from the model (`writer.py:217-230`) and
  never merges with what is on disk.
- The WI-126 guard does not cover this: `_body_content_lines` (`writer.py:69-80`, applied at
  `writer.py:210-214`) compares **body** lines only. Frontmatter is unguarded.

So routing `save()` through `mutate_note` — which `## Approach` does, since
`write_markdown_file` is one of "writer.py's four `write_text` sites", and it is the door all
three `save()` overrides funnel into (`person.py:1252-1267`, `book.py:138-163`,
`meeting.py:160-185`) — buys atomicity and mutual exclusion, but the fresh read taken under the
lock is then *discarded* by a whole-file overwrite. A cooperating writer's frontmatter edit is
still silently destroyed, with a window equal to the lifetime of the cache, not microseconds.

This contradicts `## Intent` ("a concurrent or external edit can no longer be silently
destroyed") and it contradicts the residual paragraph, which names exactly one residual and
instructs that "a spec claiming total external safety is wrong and should fail review" — while
the doc itself under-declares a second, far larger residual.

Two resolutions exist with materially different consumer-facing semantics, and the doc picks
neither:

- (a) `save()` is re-expressed as a merge into freshly-read state — which changes what "save
  this entity" means for three repos and requires a field-level precedence rule that does not
  currently exist; or
- (b) `save()` keeps snapshot-overwrite semantics and gets only Layers 1+3, with the
  lost-update residual for that door declared as loudly as the µs external window is.

Choosing between these is an approach-level call, not a spec detail — under (a) the
spec-writer would be *designing* the closure semantics, which is the redesign this gate exists
to prevent. Note that Layer 3's re-stat does not rescue (b): it compares against the read taken
inside the lock, so a cooperating write that landed *before* the lock was acquired is invisible
to it.

The item's title also promises **stale-read** protection. The Exploration delivers stale-*write*
protection for transform-shaped callers, plus in-process cache locking; cross-process cache
staleness (another process writes, this process keeps serving and then re-writes the old
snapshot) is the same root and should be ruled on in the same pass.

**2. The prior-art check is unwritten, and the absorbed item's named alternative is dropped
without a ruling (`## Approach`).**

Every precedent the Exploration cites is internal — WI-057, WI-065's `_HELD` registry,
WI-065/M1, WI-015. That is the citation-density-on-your-own-code shape LESSONS #29 warns about,
and it leaves two outside-view questions unruled:

- **The platform's own answer.** WI-015 — which this item absorbs — explicitly named
  "preferring Obsidian's API via MCP where possible" (`docs/obsidian-plugin-sync.md:20`). The
  Exploration absorbs the item and silently drops its alternative. The rejection is almost
  certainly available and cheap (headless cron/CLI consumers cannot require a running Obsidian;
  it would invert the dependency direction for a filesystem library), and the project has
  already made this call once in code — `append_to_body_section` exists so writers route
  through the package "instead of MCP `patch_vault_file`" (`person.py:1578-1579`). But the
  ruling must be *written*; an unrecorded rejection is the thing the ritual exists to catch.
- **Build vs integrate.** The doc rules out importing workshop's lock (correctly — the
  dependency points the wrong way) but never considers the maintained third-party answer.
  `filelock` / `portalocker` solve exactly the Layer-2 sub-problem including the reentrant
  in-process holder counter that the doc plans to reimplement as the `_HELD` registry. Adding a
  dependency to a foundation library with three consumers is a real cost and reimplementing may
  well be right — but "considered and rejected because X" is required, not silence.

### Suggested adjustments

- In `## Approach`, rule explicitly on the entity-snapshot door: does `save()` become a merge,
  keep snapshot semantics with a declared residual, or cease to exist? Name the winner and its
  consumer-facing consequence. Fold the same ruling into the cross-process cache-staleness case
  so the title's "stale-read protection" has an owner.
- Restate the residual paragraph so it enumerates *every* residual the chosen frame leaves, not
  only the µs external window — the spec-review's job is easier when the list is closed.
- Add a short written prior-art paragraph: the Obsidian-API/MCP route (rejected, with the
  reason), and integrate-vs-reimplement for the lock (with the reason). Two paragraphs, not an
  exploration cycle.

### Notes (non-blocking) — for whoever takes the next pass

- **Rider #3's premise has been discharged by the dependency.** `## Problem / Motivation` claims
  "six hand-rolled `content.split("---", 2)` frontmatter splits in the body-section writers".
  WI-020 landed and collapsed them: there is now exactly one helper, `_split_frontmatter_fence`
  (`person.py:82-93`), called from five sites (`person.py:1626,1697,1754,1817,1888`). The
  divergence-risk argument for the consolidation rider no longer applies as written; the
  solve-in-one-place case for the *write* door is unaffected.
- **Line citations throughout are pre-WI-020 and have drifted** (e.g. `update_fields` is now
  `base.py:339-417`, not `254-273`). Spec obligation #4 already orders a re-grep, so this is
  bookkeeping — but note the re-grep must also catch `scripts/migrate_person_to_discuss.py:104`,
  a live mutation site that appears in no enumeration in this doc.
- **WI-021 coupling.** `docs/write-door-bypasses.md:18` plans to hang NameValidator and address
  normalization on this primitive. `mutate_note(path, fn)` as sketched is content-level
  (path + text transform) while those checks are entity/frontmatter-level. Worth a sentence in
  the spec on where that seam lands, so WI-021 does not arrive and find nothing to hang on.

```verdict
gate: architect
verdict: REVISE
date: 2026-08-09
model: claude-opus-5
targets: #approach, #intent
note: The layered composite is right, but the entity-snapshot save() door (base.py:294-337 → writer.py:217-230, frontmatter unguarded) is never ruled on, so the doc's "lost-update closed by construction" claim and its single-residual Intent are both false for that door — leaving two builds with different consumer-facing semantics.
```

## Data Audit — 2026-08-09

**Recommendation: REVISE — return to exploration**

### Trigger check

**Class 1 AND Class 2 both fire.**

- **Class 1 (data-distribution / field-presence / external-contract shape).** The Exploration's
  Layer-2 and Layer-3 rulings each rest on an unquantified claim about the live environment:
  that the vault lives on a filesystem with working `flock` semantics, that Obsidian
  whole-file-replaces on save, and that Obsidian ignores dot-directories. These are
  external-contract premises about production, not logic.
- **Class 2 (rule-effect-against-existing-corpus).** The Approach's load-bearing claim is
  routing: "All update/append/section-writer paths … route through it." That is a predicate
  over the *current* codebase — solve-in-one-place is true only if the enumeration is
  exhaustive against what exists today. The doc's enumeration is dated 2026-07-05 and predates
  WI-020's landing.

Notably, the doc *itself* declares all four of these as "data-premise material — verify, don't
assume" (spec-stage verification obligations 1–4). It correctly identified the premises; none
of the first three has been discharged, and the fourth is discharged here and comes back false.

### Premise vs reality

**Grounded here (obligation 4 — mutation-site enumeration): the premise is FALSE as written.**

Predicate: grep `write_text|write_bytes|open(…,"w")|\.rename\(|\.unlink\(|shutil\.|os\.replace|mkstemp|NamedTemporaryFile|flock|fcntl|fsync|threading|RLock` across `obsidian_schemas/**` and `scripts/**`, tests excluded. Run 2026-08-09 against this tree.

*Corruption premise — CONFIRMED, still live.* Zero hits for `flock`, `fcntl`, `fsync`,
`os.replace`, `mkstemp`, `NamedTemporaryFile`, `threading`, `RLock` anywhere in the package or
scripts. Every write is a bare `Path.write_text`. The item's reason to exist holds.

*Routing set — the real inventory is 14 content-write sites plus one non-content mutation:*

| Location | Sites | In the doc's enumeration? |
|---|---|---|
| `writer.py:236, 283, 333, 365` | 4 | yes ("writer.py's four `write_text` sites") |
| `repositories/base.py:390` (`update_fields`) | 1 | yes, but cited as `base.py:254-273` — drifted |
| `repositories/person.py:1543, 1554, 1652, 1769, 1845, 1912` | 6 | partly — doc says "five body-section writers"; there are six write sites |
| `scripts/lint_vault.py:876, 894` | 2 | **no** — doc cites `lint_vault.py:875` only, one of two |
| `scripts/migrate_person_to_discuss.py:104` | 1 | **no** — file appears in no enumeration |
| `scripts/lint_vault.py:1038` — `src.rename(dest)` (quarantine move) | 1 | **no** — and see below |

The doc undercounts by at least three sites. Two are bookkeeping (spec obligation #4's re-grep
would catch them). The third is not:

**`quarantine_garbage` (`scripts/lint_vault.py:1015-1040`) mutates the vault by *renaming a note
into `<vault>/_quarantine/`* — a whole-file move, not a content transform.** It is structurally
inexpressible as `mutate_note(path, fn)`, whose signature is (path, text→text). So the Approach's
"every vault mutation in the package routes through it" is not merely incomplete against today's
corpus — for this site it is unsatisfiable by the primitive as sketched. Either the primitive
grows a second shape (a locked-rename door), or `_quarantine` moves are declared out of scope
with the residual stated. That is an approach-level ruling, not a spec detail.

Related, discharging a stale claim the doc still leans on: `## Problem / Motivation` rider #3
claims "six hand-rolled `content.split("---", 2)` frontmatter splits". WI-020 collapsed those —
there is now one helper `_split_frontmatter_fence` (`person.py:82-93`) called from five sites
(`person.py:1626, 1697, 1754, 1817, 1888`). But the split did not disappear from the tree: a
seventh hand-rolled `content.split('---', 2)` survives at
`scripts/migrate_person_to_discuss.py:70`, in the same unenumerated file as the unenumerated
write at `:104`. The divergence-risk argument is discharged *for the package* and still live
*for `scripts/`* — which is exactly where both enumeration misses land.

**Not grounded (obligations 1–3) — three open empirical questions, over the Step-5 cap of 2.**

1. **Vault filesystem.** Ungrounded. The doc states its own consequence: "flock semantics degrade
   on some network/synced filesystems; if iCloud/Dropbox is under it, re-open this ruling." This
   is not a detail to confirm during the build — a negative result invalidates Layer 2 entirely
   and reopens the four-way fork. It must be answered before a spec is written on Layer 2.
   Nothing in this repository names the live vault path (`OBSIDIAN_VAULT_PATH` is read from the
   environment at `lint_vault.py:52`, `migrate_person_to_discuss.py:160`), so it cannot be
   grounded from the tree — it needs one `stat -f`/`mount` observation against the real vault.
2. **Obsidian's write pattern.** Ungrounded, and it is the sole support for the honest-residual
   paragraph's third clause ("Obsidian's own writes are whole-file safe-writes, so the loser is
   one field update … never a torn file"). If Obsidian instead truncates-and-writes in place,
   that clause is wrong in kind rather than in degree, and the residual the spec is required to
   state verbatim would be understating the risk. A premise that a spec must reproduce verbatim
   is precisely the one that must be observed, not assumed.
3. **Lock-sentinel placement.** Ungrounded. If Obsidian indexes the dot-directory, sentinels
   become vault-visible notes and the parse/lint layer starts seeing them — a self-inflicted
   corruption class introduced by the fix. The doc names the fallback (home them outside the
   vault, keyed by path hash), so a negative result is survivable, but the choice changes the
   primitive's configuration surface for three consumer repos.

Obligations 1 and 2 also sit underneath the architect's outstanding finding: the residual
enumeration it asks to be closed cannot be closed while the facts two of those residuals rest on
are unobserved.

### Required grounding

1. **Run obligation 1 against the live vault** and paste the result: filesystem type and whether
   any sync agent (iCloud Drive, Dropbox, Syncthing) is mounted above it. If it is not a local
   POSIX filesystem with working advisory locks, the Layer-2 ruling reopens — say so explicitly
   rather than proceeding.
2. **Observe obligation 2** — edit a note in Obsidian, capture inode + `mtime_ns` + size before
   and after — and paste the observation. Then restate the residual paragraph's third clause on
   what was observed, not on what is assumed.
3. **Settle obligation 3** by observation (does Obsidian index `<vault>/.obsidian-schemas-locks/`?)
   and record the fallback decision if it does.
4. **Rule on the non-content mutation.** `scripts/lint_vault.py:1038`'s quarantine rename cannot
   route through `mutate_note(path, fn)`. Decide: second door, out of scope with a declared
   residual, or a widened primitive signature. Then re-state the routing set as the closed
   14-site + 1-rename inventory above (or re-derive it), so "solve-in-one-place" is a checkable
   claim rather than a prose one.

Obligations 1–3 are cheap — three observations, minutes of work. The reason they block is that
the first can invalidate a whole layer and the second is load-bearing for text the spec is
required to reproduce verbatim; grounding them after the spec is written is the exact ordering
this gate exists to prevent.

```verdict
gate: data-premise
verdict: REVISE
date: 2026-08-09
model: claude-opus-5
targets: #approach, #intent
note: The doc's own four verification obligations are the premise set; three (vault filesystem/flock viability, Obsidian's write pattern underpinning the residual claim, dot-dir sentinel visibility) are entirely ungrounded, and the fourth is grounded here and comes back false — the routing set is 14 write sites plus a quarantine rename (lint_vault.py:1038) that mutate_note(path, fn) structurally cannot express, so "every vault mutation routes through it" is unsatisfiable as sketched.
```

## Spec-Writer Round — 2026-08-09

> **SUPERSEDED IN ITS CONCLUSION, 2026-08-09 (round 4). Kept as audit trail, amended rather than
> deleted.** This section's conclusion — "no spec, and that is the deliverable" — was correct for
> the rounds in which the three live-vault obligations were unobserved. They were observed in the
> conductor sitting recorded at `### DISCHARGED` below, so the residue this section names is gone
> and `## Design` … `## Risk Analysis` are written above. Two specific corrections, so nothing here
> reads as still open:
>
> - **Reason 1 below cites the wrong rule, as the round-3 architect's note #5 found.** D3 (refuses
>   `→ specced` without a data-premise PROMOTE) is epoch-gated on `AUDIT_EPOCH = 2026-06-21`, and
>   this item's `created` is `2026-03-22`, so **D3 is exempt here**. The conclusion was right for a
>   stronger reason: U1 is universal and un-epoch-gated, so any gate whose latest verdict is REVISE
>   blocks every transition. Recorded because anyone reasoning from D3's exemption would wrongly
>   conclude the item could have moved.
> - **Reason 3 — "three of the four premises are un-dischargeable from inside the cage" — remains
>   TRUE of any cage-scoped session** (WI-024 removed `DEFAULT_VAULT_PATH`, so nothing in this
>   repository names the live vault, and no future round can ground them from here either). It is no
>   longer a blocker because they were discharged from OUTSIDE the cage, which is exactly what the
>   data-premise gate's round-3 verdict asked for.

**No spec was written this round, and that is the deliverable.** This section records why, discharges
everything that could be discharged from inside the tree so the next round starts warm rather than
cold, and names the exact residue that has to be answered before `## Design` can exist. The item
stays at `exploring`.

### Why no spec

Three independent reasons, any one of which is sufficient:

1. **The conveyor would refuse the transition regardless.** The D3 rule refuses `→ specced` without a
   data-premise PROMOTE, and the data-premise verdict of record is REVISE. A spec written now cannot
   advance; it would only add a third surface stating a behaviour nobody has ruled on.
2. ~~**Both blocking findings are declared approach-level by the gates that raised them**~~ —
   **superseded by the revision round; see the amended "Not discharged" block below.** The original
   reasoning was that the architect had declared the `save()` door approach-level ("under (a) the
   spec-writer would be *designing* the closure semantics, which is the redesign this gate exists to
   prevent") and the data-premise gate had said the same of the quarantine rename ("That is an
   approach-level ruling, not a spec detail"), so deciding either was the exploration this role is
   not. What that missed is that the architect's own option (b) is the *status-quo-preserving* branch:
   it changes no consumer-facing semantics by design and needs no precedence rule to be invented, so
   ruling (b) is a declaration rather than a redesign. Only (a) was the redesign, and (a) is rejected.
   Both findings are ruled in `## Approach` on that basis. If Dave wants merge semantics for `save()`,
   that is (a), it is a separate item, and it needs him to originate the precedence rule.
3. **Three of the four premises are un-dischargeable from inside the cage.** Obligations 1–3 need
   observations against the live vault (filesystem type, Obsidian's on-save behaviour, dot-dir
   indexing). This session has no shell and is scoped to the worktree; the tree does not name the
   vault — `OBSIDIAN_VAULT_PATH` is read from the environment at
   `obsidian_schemas/repositories/base.py:ENV_VAULT_PATH:61`, `scripts/lint_vault.py:52`, and
   `scripts/migrate_person_to_discuss.py:main:160`. Nothing here can ground them.

The quality bar's own rule for this shape is the tiebreak: where rounds re-raise the same target and
folds are not holding, *do not buy another round — the open question is the APPROACH, and it goes to a
human.* Both verdicts target `#approach, #intent`.

**Amended on the revision round (2026-08-09).** What went to a human is now narrower than "the
approach". The two rulings the gates named are decided in `## Approach` (see the amended block at the
end of this section) and `## Intent` is restated to be true of the doors as ruled. What still needs a
human is the *empirical* residue — obligations 1–3, three observations against the live vault that no
session scoped to this worktree can make — plus the standing option for Dave to reverse either written
ruling (merge semantics for `save()`; a hand-rolled `_HELD` registry instead of `filelock`). Those are
reversals of recorded decisions now, not gaps.

### The generator behind both blocking findings (the class, not the two instances)

The architect found one door the primitive cannot express (`save()`); the data-premise gate found a
second (`quarantine_garbage`). Closing those two instances would leave the third for round three.
They share a generator, and it is worth stating plainly because it changes what the next Approach has
to say:

> **Every mutation inventory in this doc is hand-authored, and the primitive's surface was chosen
> before the mutation *shapes* were enumerated.** `mutate_note(path, fn)` has the type
> `(path, text → text)`. That type is a claim: *every vault mutation is a pure transform over the
> current bytes of one existing file.* The doc never tested that claim against the tree, so each
> reviewing gate finds one more site whose semantics do not fit — and will keep doing so.

Sweeping the next level of the ladder — members → mutation kinds → kinds × expressibility → sub-shapes
within the expressible kind — is what closes it. That sweep is below, and it returns **three**
inexpressible cells, not two.

### Discharged here: the mutation surface, derived rather than listed

Predicate, run against this tree on 2026-08-09, tests excluded:

```bash
rg -n 'write_text|write_bytes|open\(.*["'"'"']w|\.rename\(|\.unlink\(|os\.remove|os\.rmdir|shutil\.|move\(|copyfile|copytree|mkdir|\.touch\(|\.symlink|os\.replace|mkstemp|NamedTemporaryFile|flock|fcntl|fsync|threading|RLock' \
  obsidian_schemas/ scripts/
```

**Level 1 — the corruption premise. CONFIRMED, still live.** Zero hits for `flock`, `fcntl`, `fsync`,
`os.replace`, `mkstemp`, `NamedTemporaryFile`, `threading`, `RLock` anywhere in `obsidian_schemas/` or
`scripts/`. Every write is a bare `Path.write_text`. The item's reason to exist holds.

**Level 2 — mutation kinds. The sweep closes at four cells, one of them empty:**

| Kind | Sites | Where |
|---|---|---|
| Content rewrite (`write_text`) | 14 | `writer.py:236,283,333,365`; `repositories/base.py:390`; `repositories/person.py:1543,1554,1652,1769,1845,1912`; `scripts/lint_vault.py:876,894`; `scripts/migrate_person_to_discuss.py:104` |
| Whole-file move (`Path.rename`) | 1 | `scripts/lint_vault.py:quarantine_garbage:1038` |
| Directory create (`Path.mkdir`) | 2 | `obsidian_schemas/writer.py:write_markdown_file:233`; `scripts/lint_vault.py:quarantine_garbage:1034` |
| Delete (`unlink` / `os.remove` / `rmdir`) | 0 | — none in the package or scripts |

`write_bytes`, raw `open(..., "w")`, `shutil.*`, `os.rename`, `os.replace`, `symlink` and `touch`: zero
hits outside `tests/`. This matches the data-premise gate's inventory and extends it by the `mkdir`
cell, which no round has named yet — precisely the next-member-next-round shape.

A granularity note, because the two prior enumerations disagree and both are right: `person.py` has
**six write sites across five methods** — `append_to_timeline` writes at both `:1543` (section-creating
accommodation) and `:1554` (insert-after-marker). The 2026-07-05 text counted methods; the
2026-08-09 audit counted sites. State which unit is meant, or the discrepancy generates another round.

**Level 3 — kind × expressibility as `(path, text → text)`. Three cells do not fit:**

- **`quarantine_garbage`'s rename** (`scripts/lint_vault.py:quarantine_garbage:1038`) — the identity of
  the file changes; there is no "the current bytes of this path" to transform. It also carries its own
  TOCTOU: `dest.exists()` at `:1036` guards a `src.rename(dest)` at `:1038` with nothing holding
  between them.
- **Directory creation** (`:1034`, `writer.py:233`) — a namespace mutation, not a file mutation.
- **The entity-snapshot rebuild** — see below. This is the architect's finding, re-derived as a *shape*
  rather than as a site.

**Level 4 — sub-shapes within the expressible kind.** The 14 content rewrites are three shapes, not
one, and the third is the one that breaks:

- **(i) Parse-and-reserialize** — a dict from `parse_frontmatter` is mutated and dumped back:
  `writer.py:update_frontmatter_field:283`, `writer.py:update_frontmatter_fields:333`,
  `writer.py:roundtrip_file:365`, `repositories/base.py:update_fields:390`, `scripts/lint_vault.py:876`.
  Genuinely transform-shaped; `mutate_note` fits.
- **(ii) Verbatim frontmatter carry-through** — the fence text is passed through untouched and only the
  body changes: the five `person.py` body writers and `scripts/migrate_person_to_discuss.py:104`, plus
  the wikilink rewrite at `scripts/lint_vault.py:894`. Also transform-shaped; `mutate_note` fits.
- **(iii) Whole-file rebuild from an in-memory snapshot** — `obsidian_schemas/writer.py:write_markdown_file:217-230`
  builds frontmatter wholesale from the entity argument and never merges with disk. Its caller
  `obsidian_schemas/repositories/base.py:save:294-337` supplies an entity taken from `self._cache`
  (`base.py:142`), populated once at `load()` (`:169-197`) and invalidated only by an explicit
  `refresh()` (`:419-457`). **Not transform-shaped.** The fresh read `mutate_note` takes under the lock
  is discarded by the overwrite that follows it.

Two corroborations of the architect's finding, verified in code this round rather than inherited:

- The WI-126 guard does not cover it. `obsidian_schemas/writer.py:_body_content_lines:69-80`, applied at
  `:195-214`, compares **body** lines only — `for raw in body.splitlines()`. Frontmatter is unguarded,
  by construction, and the docstring says as much ("The frontmatter survives … the body is the loss").
- Layer 3 cannot rescue it. The re-stat compares against the read taken *inside* the lock, so a
  cooperating write that landed *before* the lock was acquired is invisible to it. The lost-update
  window for door (iii) is the lifetime of the cache — hours in a long-lived HAL9000 process — not
  microseconds.

**Consequence for the Approach, stated without deciding it:** the next Approach should define the
primitive's surface **by mutation shape**, not by a list of sites. A shape-defined surface answers
`save()`, the quarantine rename and `mkdir` in one ruling and is total against future sites; a
site-defined surface answers whichever site the last gate happened to name.

### Discharged here: the prior-art paragraph the architect asked for

Two rulings, written rather than assumed. Neither is an exploration cycle; both were scoped by the
architect as "two paragraphs".

**The platform's own answer — Obsidian's API via MCP. Rejected.** WI-015, which this item absorbs,
named "preferring Obsidian's API via MCP where possible" (`docs/obsidian-plugin-sync.md:20`) and the
absorption dropped it without a ruling. It is rejected on three counts. It inverts the dependency
direction: this package is a filesystem library and the foundation three repos install `-e`, and
routing its writes through an editor's plugin API makes the foundation depend on a GUI application
being alive. It cannot serve the consumers that matter most for this item — headless cron jobs, CLI
one-offs, and exocortex batch ingest all write when Obsidian is not running, and the tempting "fall
back to direct writes when the API is unavailable" is the same circumvention-helper shape the doc
already rejects for the single-writer daemon. And the project has made this call once already, in
code: `obsidian_schemas/repositories/person.py:append_to_body_section:1578-1579` exists precisely so
writers route through the package "instead of MCP `patch_vault_file`". Reversing that at the write
primitive would undo a decision the tree records.

**Build vs integrate for Layer 2.** The doc rules out importing workshop's lock (correctly — the
dependency points the wrong way) but never considers the maintained third-party answer. `filelock` and
`portalocker` both solve exactly the Layer-2 sub-problem, including the reentrant in-process holder
counter the doc plans to reimplement as the WI-065 `_HELD` registry. **The recommendation is
`filelock`, and the counter-argument is real enough that the next round should record whichever way it
goes.** For: the reentrancy counter and the per-FD/per-thread distinction are the part of advisory
locking that is easy to get subtly wrong, the failure is silent, and this package currently has zero
third-party runtime dependencies beyond `pydantic` and `PyYAML` — one more pure-Python, no-native-code
package with a stable API is a small addition. Against: it is a *new dependency on a foundation
library with three consumers*, each of which will inherit it. What must not happen is a third round
that re-raises this as unruled. **It did not: the revision round recorded the ruling — integrate
`filelock` — in `## Approach`, alongside the MCP rejection.**

### Discharged here: the WI-021 seam

`docs/write-door-bypasses.md:18` plans to hang NameValidator and address normalization on this
primitive. As sketched, `mutate_note(path, fn)` is **content-level** (`path`, `text → text`) while
those checks are **entity/frontmatter-level** — there is nothing for WI-021 to hang on at that
signature. The seam has to be named in this item, not discovered by WI-021's builder. Note that
shape (iii) above is the only door that even sees an entity, so the WI-021 seam and the `save()`
ruling are the same decision wearing two hats and had to be taken together. **They were, on the
revision round:** both are ruled in `## Approach` — the seam is door 2, at its entry, beside the
`_normalize_address_fields` call `obsidian_schemas/repositories/person.py:save:1252` already makes.

### Discharged here: the verification machinery already in the tree

Whoever specs this should not hand-write the "every mutation routes through the door" wall.
`tests/derivations.py` already exists as the package's single shared source-scanning module, built for
WI-020, and it already carries the exact predicate this item needs:
`tests/derivations.py:_is_write_call:189-195` matches `write_text`/`write_bytes` calls off parsed
syntax, `tests/derivations.py:python_files_under:88` walks the file set from disk rather than from a
hand-scoped list, and `tests/derivations.py:module_id:60` is the one rule mapping a file to an
identity. Its module docstring states the constraint that makes it load-bearing: it is *"the only file
under `obsidian_schemas/` or `tests/` permitted to name `ast`"*, so a private re-implementation of any
sweep is detectable.

Two obligations ride with using it, both from the bar:

- The wall's oracle will be a **count** of structural matches ("zero un-routed write sites"), and a
  count says nothing about the matcher's reach — `matches == 0` is satisfied identically by a matcher
  that resolves every claimed shape and by one that resolves almost none. The spec must name the
  match-shapes and ship them as green fixtures driven through the wall's *own* predicate, plus a
  near-miss the predicate must not match. `_is_write_call` today matches on attribute name only, so
  `open(p, "w").write(...)`, `shutil.move`, and `Path.rename` are all shapes it does **not** resolve —
  and the level-2 sweep above found a live `rename` it would miss.
- `_is_write_call`'s reach must be widened to the level-2 kinds before it can back a
  "no un-routed mutation" claim, or the claim must be narrowed in writing to content rewrites only.

### Not discharged, and who owns each

**Needs a shell against the live vault — not this cage.** Obligations 1–3 are minutes of work for
whoever has the vault mounted; they are stated here in runnable form so no one has to re-derive them:

1. **Filesystem under the vault.** `stat -f %T "$OBSIDIAN_VAULT_PATH"` and `mount | grep -i "$(df -P "$OBSIDIAN_VAULT_PATH" | tail -1 | awk '{print $NF}')"`. Paste the result. A negative (iCloud Drive, Dropbox, Syncthing, any network mount) invalidates Layer 2 and reopens the four-way fork — say so explicitly rather than proceeding. *Adjacent but not a substitute:* `docs/backlog-campaign-2026-07-05.md:97` records that `Workspaces` sits on a case-insensitive APFS volume. That is the code checkout, not the vault, and does not discharge this.
2. **Obsidian's write pattern.** Capture `stat -f '%i %m %z' <note>` before and after editing that note in Obsidian; an inode change means replace-by-rename, an unchanged inode with a changed size means in-place truncate-and-write. This is the sole support for the residual paragraph's third clause ("Obsidian's own writes are whole-file safe-writes, so the loser is one field update … never a torn file"). If it truncates in place, that clause is wrong *in kind*, and the residual the spec is required to reproduce verbatim would be understating the risk.
3. **Dot-dir sentinel visibility.** Create `<vault>/.obsidian-schemas-locks/probe.md`, open Obsidian, and check whether it appears in search/graph. If it does, record the fallback (sentinels homed outside the vault, keyed by path hash) as the decision rather than as an option — it changes the primitive's configuration surface for three consumer repos.

### DISCHARGED — 2026-08-09, conductor sitting with Dave (revise-cap resolution)

All three obligations were run against the live vault by the conductor (obsidian-schemas
session), with Dave at the keyboard for the interactive halves. Results verbatim:

1. **Filesystem: POSITIVE — local journaled APFS.** `mount` for the vault's volume:
   `/dev/disk3s5 on /System/Volumes/Data (apfs, local, journaled, nobrowse, protect, root data)`.
   Not iCloud Drive, not Dropbox/Syncthing, not a network mount. Dave confirmed no
   filesystem-level sync agent touches the vault: Obsidian Sync is in use but is app-level
   (writes arrive through the Obsidian process — the already-modeled non-cooperating writer),
   and a future planned backup system is read-only (adds no writer). **Layer 2 stands; the
   four-way fork stays closed.** (The `stat -f %T` form in the runnable block prints a
   file-type glyph on macOS, not the fs type — `mount` is the authoritative half; noted so
   round 4 doesn't chase the discrepancy.)
2. **Obsidian write pattern: NEGATIVE — truncate-and-write in place.** `stat -f '%i %m %z'`
   on a live person note across a real Obsidian edit by Dave: before `220735514 1786269371
   5049`, after `220735514 1786269577 5085`. Same inode, larger size, advanced mtime =
   in-place truncate-and-write. R1's clause (c) was wrong in kind and has been restated on
   this observation in `## Approach` (marker removed there): the µs-window loser is not
   bounded in shape to one field update; a reader overlapping the truncate window can see a
   truncated note.
3. **Dot-dir visibility: NOT VISIBLE (filename search).** Probe created at
   `<vault>/.obsidian-schemas-locks/probe.md`; Dave ran a Ctrl+O quick-switcher search for
   "probe": no results. Evidence scope stated exactly: filename search only — full-text
   search and graph were not separately checked. Decision recorded: **in-vault dot-dir
   sentinels stand** (the fallback is not triggered); if a later observation shows dot-dir
   content indexed elsewhere in Obsidian, the fallback (sentinels outside the vault, keyed
   by path hash) is the named successor. Probe file and directory deleted after the check.

**Dave's two reversal decisions, same sitting (conversational): BOTH RULINGS CONFIRMED** —
door 2c stays option (i) (atomic no-clobber create raising `NoteAlreadyExists`, converted by
`create_stub` into its reuse branch), and Layer 2 stays **integrate `filelock`** over a
hand-rolled `_HELD` registry.

**Superseded 2026-08-09 (revision round) — the two approach rulings LANDED in `## Approach`.** This
block originally routed both to Dave. It is kept for the audit trail and amended rather than deleted,
because leaving it as written would contradict the revised `## Approach` and put the item back to
buildable-two-ways — the exact defect the architect's REVISE named. Both were re-run as a revision to
that verdict and are now decided in `## Approach`; neither is open:

- ~~**The entity-snapshot door.**~~ **Ruled (b):** `save()` keeps snapshot-overwrite semantics, the
  merge is rejected for want of a field-level precedence rule, and the lost-update loss is converted
  from silent to loud by anchoring Layer 3's precondition at the *cache-load* stamp rather than the
  in-lock read — raising `StaleEntityWrite`. Consumer-facing consequence stated in `## Approach`.
  Cross-process cache staleness is ruled in the same pass: the stale *write* is refused, the stale
  *read* is declared out of scope as residual R2 with `refresh()` named as its owner.
- ~~**The non-content mutations.**~~ **Ruled as a class:** the quarantine rename gets a second door
  (`move_note(src, dest)` — the deciding fact being the live `dest.exists()`/`src.rename(dest)` TOCTOU
  at `scripts/lint_vault.py:quarantine_garbage:1036-1038`); the two `mkdir` sites are ruled out with
  the reason (idempotent, no loss mode); the empty delete cell gets no door and is covered instead by
  the total rule — the routing wall treats an unrecognised mutation kind as an ERROR, not a pass.

**Amended again on round 3 (2026-08-09) — the create cell is now ruled too.** The round-2 architect
found a third door-shaped cell the doc had not ruled: the create path, a door-2 write with **no**
derivation read, where the collision guard consults `_cache`
(`obsidian_schemas/repositories/person.py:create_stub:1429`) and WI-126's body-shrink guard no-ops on
a headings-only victim body (`obsidian_schemas/writer.py:write_markdown_file:210-214` runs only
`if existing_lines:`). Verified in code this round rather than inherited, and extended: `book.py` and
`company.py`'s `create_stub` carry no collision branch at all. It is ruled in `## Approach` as door
2c — an atomic no-clobber create raising `NoteAlreadyExists`, which `create_stub` converts into its
existing reuse branch — together with the placement question the same finding raised (door 2 lives in
`obsidian_schemas/writer.py:write_markdown_file:154`, since `book.py:save:163` and
`meeting.py:save:185` never reach `BaseRepository.save:294`). Neither is open.

**The class-shaped fold that round 3 performed, recorded so round 4 does not re-derive it.** Round 1
named generator A — *the surface was chosen before the mutation shapes were enumerated*. Round 2's
finding is not a fourth member of A; it is the first named member of **generator B: a precondition
evaluated against something other than the target, at a time other than the write, whose absence was
read as a pass.** Closing the create path alone would have left the other members for round 4, so
`## Approach` closes B with one rule (every write is preconditioned at the write syscall against the
target itself; no derivation read → atomic non-existence) and the sweep that rule closes is written
out there as a table: the cache-backed guard at `person.py:1429`, the *absent* guards at
`book.py:create_stub:273` and `company.py:create_stub:153`, the `exists()`-then-`write_text` gap
inside `write_markdown_file` (`:186` vs `:236`), and the `dest.exists()`-then-`rename` gap at
`scripts/lint_vault.py:quarantine_garbage:1036-1038`. The next level of the ladder — (precondition
source) × (evaluation time) × (meaning of absence) across the four level-2 mutation kinds — was swept
and its three further sub-cells are declared in `## Approach` (door 1 against a missing path; door 2c
against a path this process just created; `mkdir`, the one cell where "no precondition" is a decision
rather than a gap).

**CLOSED — 2026-08-09 conductor sitting (see `### DISCHARGED` above):** obligations 1–3 are
discharged (1 positive, 2 negative-and-restated, 3 not-visible with evidence scope stated), and
Dave confirmed both standing rulings — door 2c option (i) and `filelock` — in the same sitting.
Nothing in this block remains open.

**The residual paragraph now closes.** The architect asked for it to enumerate *every* residual rather
than only the µs external window. With the rulings landed, the residual set is enumerable — one entry
per (mutation kind × writer population) cell the chosen frame does not cover — and it is written as the
closed R1–R6 list in `## Approach` (**R7 added round 3** with the create cell's ruling — the losing
create's non-identifier fields are not merged). The requirement that the spec state R1 verbatim, and that a spec
claiming total external safety fail review, survives unchanged; R1's clause (c) is marked there as
resting on ungrounded obligation 2 and must be restated on what is observed before Design reproduces it.

### What holds, and should not be re-litigated next round

Re-verified against the tree this round, not carried from the doc: the layered composite (Layer 1
temp+fsync+`os.replace` in the same directory; Layer 2 per-file advisory `flock`; Layer 3
`(mtime_ns, size)` re-stat before replace) converges on the outside view rather than diverging from it;
the single-writer daemon rejection is correct and correctly reasoned; the honest-residual instinct and
its verbatim-in-spec requirement are right. The next round should fix what the gates named and leave
these alone.

## Architectural Review — 2026-08-09

**Recommendation: REVISE — return to exploration** (round 2, cold-start; read against the tree, not
against round 1's notes)

### Trigger check

Unchanged from round 1 and still firing: new primitive, >3 files across different concerns, replaces
a core system, effort > 1 day, and the resulting semantics become a contract for three consumer repos
(`docs/backlog-campaign-2026-07-05.md:95`).

### What round 1 bought — closed, and not to be re-opened

This is a **converging** round, not a treadmill: both findings I raised are closed, and the finding
below is about the frame of the ruling that was *made* this round, not a re-raise of the ruling that
was missing last round.

- **Finding 1 (the entity-snapshot door was unruled) — closed, and ruled correctly.** (b) is right:
  the merge would need a field-level precedence rule that does not exist here, and "a consumer cleared
  this field" is genuinely indistinguishable from "this snapshot predates someone setting it" at the
  frontmatter level. Anchoring the precondition at the cache-load stamp is the correct generalisation
  of Layer 3 rather than a new closure semantic, and R2 correctly declares read staleness out of scope
  with `obsidian_schemas/repositories/base.py:refresh:419` named as owner.
- **Finding 2 (prior art unwritten) — closed, and grounded.** Both citations check out:
  `docs/obsidian-plugin-sync.md:20` does name the MCP route, and
  `obsidian_schemas/repositories/person.py:1578-1579` does say the migrated writers route through the
  package "instead of MCP `patch_vault_file`". The `filelock` ruling is recorded with its real cost.
- **My three non-blocking notes — all discharged.** I re-derived the inventory independently rather
  than reading the doc's: the sweep returns exactly the doc's 14 `write_text` sites, the one
  `scripts/lint_vault.py:1038` rename, the two `mkdir` sites, zero deletes, and zero hits for
  `flock|fcntl|fsync|os.replace|mkstemp|NamedTemporaryFile|threading|RLock` in `obsidian_schemas/` or
  `scripts/`. The corruption premise holds. `scripts/migrate_person_to_discuss.py:70,104` are now
  enumerated, and the re-anchored citations resolve and mean what the doc claims
  (`base.py:save:294`, `base.py:update_fields:339`, `writer.py:217-218`, `writer.py:_body_content_lines:69`,
  `person.py:save:1252`).
- **Door 3 and the shape-defined framing are right.** Naming the generator — "the primitive's surface
  was chosen before the mutation shapes were enumerated" — is the most valuable thing in the round.

### Blocking issue

**The create path is a door-2 write with no derivation read. The rule the revision calls total is
false there, so the concurrent-create clobber survives the chosen frame — silently (`## Approach`,
`## Intent`).**

Verified in code this round:

- `create_stub` builds a `Person` from scratch (`obsidian_schemas/repositories/person.py:1444-1452`)
  and writes it through door 2 at `obsidian_schemas/repositories/person.py:1466`, with `overwrite`
  defaulting to `True` (`person.py:1252`). Same shape at `obsidian_schemas/repositories/book.py:317`
  and `obsidian_schemas/repositories/company.py:192`.
- Its collision guard reads the **cache, not the disk**: `existing = self.get(clean_name)`
  (`person.py:1429`) resolves to `self._cache.get(...)` (`obsidian_schemas/repositories/base.py:269`),
  populated at `load()` and invalidated only by an explicit `refresh()`. A note another process
  created *after* this process loaded is invisible, so the reuse-on-collision branch
  (`person.py:1430-1437`) is never taken.
- The WI-126 guard does not catch the overwrite that follows. `obsidian_schemas/writer.py:210-214`
  guards only `if existing_lines:`, and `_body_content_lines` (`writer.py:69-80`) drops blank and
  `#`-prefixed lines. A freshly minted stub's body is `"## To Discuss\n\n## Timeline\n\n## Notes\n"`
  (`obsidian_schemas/body_sections.py:306`) — headings only — so the set is **empty**, the guard
  no-ops, and `writer.py:236` rebuilds the note from the in-memory entity
  (`writer.py:217-218`), destroying the victim's frontmatter wholesale. That is LESSONS #5's
  PASS-by-default-on-empty ("empty is a bug shape, not a normal mode") sitting at the write boundary.
- **Door 2 as ruled does not reach it.** The stamp is recorded "at the moment it loads that note into
  `_cache`/`_file_map`" — for this write there is no such moment. So `## Approach`'s claim *"The rule
  is total because every write has a derivation read"* is false for this cell: its derivation read is
  a cache **existence check** about a file that did not exist at load time. `## Intent`'s "a
  concurrent or external edit is either excluded … or detected and loudly refused — never silently
  destroyed" is false for the same cell.

Concretely: exocortex batch ingest mints `@Jane Doe.md` with an email and `created_by`; HAL9000's
long-lived `PersonRepository`, loaded before that, handles one request calling
`create_stub("Jane Doe", phone=…)`; the email and the provenance are gone, with no exception and
nothing above INFO. This is exactly the class `person.py:1419-1428`'s own comment says the reuse
branch exists to prevent ("the loud door WI-119 caught on 06-14") — defeated cross-process because the
guard consults a cache.

Two forks make this approach-level rather than a Design detail:

1. **Semantics.** No stamp + destination exists → either (i) refuse loudly, i.e. a create becomes an
   **atomic no-clobber create** — door 3's own mechanism, reused — which gives `create_stub` and
   `find_or_create_stub` (`person.py:698`) a raising mode where today they always return; or (ii) no
   precondition at all, which leaves door 2's widest hole open on the package's highest-frequency
   write path. The doc's own deciding argument for minting door 3 applies verbatim here — "declaring
   the cell out of scope would leave a known destructive race inside the very item that exists to kill
   destructive races" — and this race's window is the cache's lifetime, not an instruction gap.
   Choosing between (i) and (ii) changes behaviour for three consumer repos; it is the same shape as
   the (a)/(b) fork ruled last round and needs ruling the same way, in writing.
2. **Placement.** `## Approach` locates the precondition in "`save()`", but `save()` is three
   implementations and two of them never reach `BaseRepository.save:294`:
   `obsidian_schemas/repositories/meeting.py:185` and `obsidian_schemas/repositories/book.py:163` call
   `write_markdown_file` directly. The one choke point that sees both the entity and the path is
   `obsidian_schemas/writer.py:write_markdown_file:154` — but the stamp lives on the repository
   (`base.py:142-143`), which that function cannot see. Either the stamp registry is path-keyed and
   owned by the write primitive, or every present and future `save()` is routed individually — and the
   routing wall cannot detect a miss of the second kind: its inventory is filesystem-call *kinds*
   (`tests/derivations.py:_is_write_call:189-195` matches `write_text`/`write_bytes`), while a
   repository that calls `write_markdown_file` performs no filesystem write at all. The wall stays
   green while door 2 is bypassed, which is precisely what the "unrecognised kind is an ERROR, not a
   pass" rule was meant to make impossible.

### Suggested adjustments

- Add the missing cell to the door ruling — **create / no-derivation-read** — and name the winner
  ((i) or (ii)) with its consumer-facing consequence spelled out for `create_stub` and
  `find_or_create_stub`, exactly as door 2's `StaleEntityWrite` consequence already is.
- Restate the total rule so it covers a write whose bytes derive from no read of the target. Door 3 is
  already one such write and was handled ad hoc; the create path is the second. The natural closed
  form: *a write with no derivation read is preconditioned on the target's non-existence, enforced
  atomically* — which makes doors 2-create and 3 the same ruling.
- Say where door 2 physically lives (`write_markdown_file` vs `BaseRepository.save`). If it stays on
  the repository, add the package-internal bypass to the wall's obligations alongside the two already
  listed, since a `write_text`-shaped matcher cannot see it.
- Add the create cell to the R1–R6 residual list once ruled.

### Notes (non-blocking)

- Nothing else in `## Approach` needs another pass. Every claim I spot-checked resolves and means what
  the doc says it means, and the inventory matches an independent sweep exactly.
- This finding needs **no shell** — it is entirely tree-grounded and orthogonal to obligations 1–3,
  which remain open and remain the data-premise gate's and Dave's.
- If Dave is being asked about obligations 1–3 anyway, fork 1 above belongs in the same ask: it is a
  behavioural change to `create_stub` that HAL9000 and exocortex will feel.

```verdict
gate: architect
verdict: REVISE
date: 2026-08-09
model: claude-opus-5
targets: #approach, #intent
note: Round 1's two findings are properly closed, but the create path (person.py:1466 via a cache-only collision check at :1429, WI-126's guard no-opping on a headings-only body at writer.py:210-214) is a door-2 write with no derivation read — so the revision's "the rule is total because every write has a derivation read" and Intent's "never silently destroyed" are both false for that cell, and the fix forks consumer-facing create semantics.
```

## Data Audit — 2026-08-09

**Recommendation: REVISE — but not for another document round.** (Round 2, cold-start; predicates
re-run against this tree, not carried from round 1's section above.)

Read this verdict together with its `targets:` line. Round 1 targeted `#approach, #intent` and raised
four required-grounding items. **One of the four — the only one groundable from inside the tree — is
closed, and closed well.** The other three were never document defects and are not document defects
now: they are observations against the live vault that no session scoped to this worktree can make.
This round narrows the target to `#approach` alone and re-raises it *deliberately*, because the honest
signal is that the remaining residue does not converge by buying another round. It converges by
someone with the vault mounted running three commands.

### Trigger check

**Class 1 and Class 2 both still fire**, unchanged in kind from round 1:

- **Class 1 — external-contract shape.** Layer 2's viability rests on the filesystem under the live
  vault; R1's clause (c) rests on Obsidian's on-save behaviour; the sentinel location rests on whether
  Obsidian indexes dot-directories. All three are claims about production, not logic.
- **Class 2 — rule-effect-against-existing-corpus.** `## Approach` claims a closed routing set over the
  *current* tree ("13 of the 14 content-write sites" to door 1, one to door 2, one to door 3) and a
  wall that derives its inventory from the tree. That is a predicate over what exists today, and it is
  re-run below.

### Grounded this round — the Class-2 premises now hold, exactly as written

Predicate, run against this tree on 2026-08-09, `tests/` excluded:

```
rg -n 'write_text|write_bytes|open\(.*"w|\.rename\(|\.unlink\(|os\.remove|os\.rmdir|shutil\.|mkdir|\.touch\(|symlink|os\.replace|mkstemp|NamedTemporaryFile|flock|fcntl|fsync|threading|RLock' obsidian_schemas/ scripts/
```

**Corruption premise — CONFIRMED, still live.** Zero hits for `flock`, `fcntl`, `fsync`, `os.replace`,
`mkstemp`, `NamedTemporaryFile`, `threading`, `RLock` in `obsidian_schemas/` or `scripts/`. Every write
is a bare `Path.write_text`. The item's reason to exist holds.

**Routing set — round 1's finding is DISCHARGED; the inventory is now exact.** I derived it
independently rather than reading the doc's, and it matches the revised `## Approach` cell for cell:

| Kind | Sites | Matches `## Approach`? |
|---|---|---|
| Content rewrite (`write_text`) | 14 — `writer.py:236,283,333,365`; `repositories/base.py:390`; `repositories/person.py:1543,1554,1652,1769,1845,1912`; `scripts/lint_vault.py:876,894`; `scripts/migrate_person_to_discuss.py:104` | yes — 13 to door 1, `writer.py:236` to door 2 |
| Whole-file move (`Path.rename`) | 1 — `scripts/lint_vault.py:1038` | yes — door 3, minted |
| Directory create (`Path.mkdir`) | 2 — `writer.py:233`, `scripts/lint_vault.py:1034` | yes — ruled out, with the reason |
| Delete | 0 | yes — empty cell, covered by the unrecognised-kind-is-an-ERROR rule |

Round 1's blocking finding was that the quarantine rename is structurally inexpressible as
`mutate_note(path, fn)`. That is now ruled — a second door with sorted-path lock acquisition and an
atomic no-clobber create, which also kills the live `dest.exists()`/`src.rename(dest)` TOCTOU at
`scripts/lint_vault.py:1036-1038`. **This gate's own finding is closed and should not be re-raised.**

**The two new tree-grounded premises the revision introduced both check out.** The `filelock` ruling
rests on "this package already carries `pydantic` and `PyYAML`" — confirmed, `pyproject.toml:26-29`
lists exactly those two runtime dependencies and nothing else. The wall obligation rests on
`tests/derivations.py:_is_write_call:189` matching on attribute name only — confirmed at `:189-195`,
`node.func.attr in {"write_text", "write_bytes"}`, so it resolves none of the other level-2 kinds and
would miss the live `rename` at `scripts/lint_vault.py:1038`. The obligation to widen it is correctly
stated and correctly placed in Design.

**Corroborating the architect's round-2 finding, since it is empirical and I verified it anyway:** the
create path's collision guard is cache-backed (`person.py:1429`) and the WI-126 guard genuinely no-ops
on a fresh stub — `writer.py:210-211` runs the drop check only `if existing_lines:`, `_body_content_lines`
(`writer.py:69-80`) discards blank and `#`-prefixed lines, and the person default body is
`"## To Discuss\n\n## Timeline\n\n## Notes\n"` (`body_sections.py:306`), i.e. headings only, so the set
is empty and `writer.py:236` rebuilds the note from the in-memory entity. The finding is real in code.
It is the architect's to close, not this gate's, and it needs no shell.

### Not grounded — the same three, and still not grounded from here

Obligations 1–3 (`## Spec-Writer Round — 2026-08-09`, "Not discharged, and who owns each") remain
entirely unobserved. Nothing in this tree names the live vault — `OBSIDIAN_VAULT_PATH` is read from
the environment at `obsidian_schemas/repositories/base.py:61`, `scripts/lint_vault.py:52`, and
`scripts/migrate_person_to_discuss.py:160` — and this session has no shell against it. Three OPEN data
questions, over the Step-5 cap of two.

They are not equal in weight, and the doc should not treat them as a block:

1. **Filesystem under the vault — this is the one that blocks.** `## Approach` states its own
   conditionality plainly: "This Approach is written on the assumption that it comes back local POSIX;
   if it does not, doors 1 and 2 fall back to Layers 1+3 only and every residual above widens." A spec
   written now would be a spec written on an assumption whose negation invalidates Layer 2 across all
   three doors and reopens the four-way fork. That is precisely the ordering this gate exists to
   prevent, and it is why this is REVISE rather than a conditional PROMOTE.
2. **Obsidian's on-save behaviour — blocks the text the spec must reproduce verbatim.** R1's clause (c)
   is currently marked as resting on it. A premise a spec is *required* to state verbatim is the last
   one that should be assumed; if Obsidian truncates in place, (c) is wrong in kind and the residual is
   understated rather than imprecise.
3. **Dot-dir sentinel visibility — does not block the ruling's shape,** as `## Approach` correctly
   says; it changes the configuration surface for three consumer repos. It should be observed in the
   same sitting as 1 and 2 because the marginal cost is zero, but it alone would not hold this item.

### Required grounding

Unchanged from round 1 in substance; restated so this section stands alone. The runnable forms are
already recorded at `## Spec-Writer Round — 2026-08-09` and do not need re-deriving:

1. Run obligation 1 against the live vault and paste the result — filesystem type, plus whether any
   sync agent (iCloud Drive, Dropbox, Syncthing) or network mount sits above it. If it is not local
   POSIX with working advisory locks, say so explicitly and reopen the Layer-2 ruling rather than
   proceeding. Note that `docs/backlog-campaign-2026-07-05.md:97`'s APFS record covers the code
   checkout, not the vault, and does not discharge this.
2. Observe obligation 2 (inode + `mtime_ns` + size across an Obsidian edit) and restate R1 clause (c)
   on what was observed, removing the marker.
3. Settle obligation 3 by observation and record the fallback as a decision if the probe is indexed.

Item 4 from round 1 is closed and is not restated.

### What this gate is NOT asking for

No further document round buys anything against `#approach` from inside a cage. Every claim in
`## Approach` that can be checked against this tree has now been checked and holds. If the next round
is another cage-scoped pass, it will re-derive the same inventory, re-confirm the same citations, and
re-report the same three unobserved facts. The item needs a shell and, on fork 1 of the architect's
round-2 finding, a call from Dave — and those two asks belong in the same sitting.

```verdict
gate: data-premise
verdict: REVISE
date: 2026-08-09
model: claude-opus-5
targets: #approach
note: Round 1's own blocking finding is DISCHARGED — the routing set re-derives exactly as `## Approach` now states it (14 write_text, 1 rename to door 3, 2 mkdir ruled out, 0 deletes), and the revision's new tree-grounded premises (pyproject.toml:26-29 for the filelock ruling, tests/derivations.py:189-195 for the wall's reach) both check out; what remains is the same three live-vault observations, un-groundable from any cage-scoped session, with obligation 1 alone able to invalidate Layer 2 across all three doors — so this re-raise of #approach is a signal that the residue needs a shell and Dave, not another document round.
```

## Architectural Review — 2026-08-09

**Recommendation: PROMOTE to architected** (round 3, cold-start; read against the tree, not against
rounds 1–2's notes)

### Trigger check

Unchanged and still firing: new primitive, >3 files across different concerns, replaces a core
system, effort > 1 day, and the resulting semantics become a contract for three consumer repos
(`docs/backlog-campaign-2026-07-05.md:95`).

### Round 2's finding is closed, and the fold is the right one

Verified in code this round rather than read off the doc:

- **The create cell is real and is now ruled.** `obsidian_schemas/repositories/person.py:create_stub`
  guards on `self.get(clean_name)` at `:1429` — `obsidian_schemas/repositories/base.py:get:258-269`,
  cache-backed — builds a `Person` at `:1444-1452` and saves at `:1466` with `overwrite` defaulting
  to `True` (`obsidian_schemas/repositories/base.py:save:299`). `CompanyRepository.create_stub`
  (`obsidian_schemas/repositories/company.py:153-194`) has **no collision branch of any kind** and
  goes straight to `self.save(...)` at `:192`. Confirmed, as the round-3 text claims.
- **The placement ruling is correct and was necessary.**
  `obsidian_schemas/repositories/book.py:save:138-170` calls `write_markdown_file` directly at `:163`
  rather than `super().save()`; same at `obsidian_schemas/repositories/meeting.py:185`. Only
  `person.py:save:1252-1267` routes via `BaseRepository.save`. So "in `save()`" genuinely does not
  name a place, and `obsidian_schemas/writer.py:write_markdown_file:154` genuinely is the only choke
  point that sees both the entity and the path. Better than the doc argues, in fact —
  `write_markdown_file` is *exported public API* (`obsidian_schemas/__init__.py:42,115`), so the door
  also catches consumers who bypass the repositories entirely.
- **The generator-B fold is a level up, not a fourth instance.** "Preconditioned at the write syscall,
  against the target itself, on the read its bytes were derived from — and where there is no such
  read, on the target's non-existence, enforced atomically" is a closed-form rule with its zero case
  inside it. Property 1 (absence is the strictest case, not the loosest) is the correct reading of
  LESSONS #5 — grounded, `LESSONS.html:217`, "each 'passed' because empty/absent was treated as fine".
  This is the audit fold the arc needed, and it should not be re-opened.

### Review

**Fit:** Harmonizes rather than fights. `write_markdown_file` is already the package's entity-write
choke point and already the place a write-boundary invariant hangs — WI-126's body-shrink guard sits
at `obsidian_schemas/writer.py:195-214`, in exactly the position door 2's precondition would take.
The new exceptions land inside WI-020's existing hierarchy, and the doc correctly pre-empts its one
non-obvious constraint (`obsidian_schemas/errors.py:REASONS:88` is a closed frozenset and
`bounded_message:109-120` raises on any reason outside it, so each new subclass ships with its
literal in the same edit).

**Duplication:** Solve-in-one-place holds. Door 2 is one physical place; the `filelock` ruling avoids
re-writing the reentrancy counter; the workshop lock is correctly not imported (dependency direction).
One overlap to resolve in Design, noted below: `writer.py:186-187` already raises `FileExistsError`
for "destination exists" and door 2c would raise `NoteAlreadyExists` for the same condition.

**Boundaries:** Ownership is split correctly and explicitly — the repository observes (records stamps
at `load`/`refresh`/`_load_file`), the primitive enforces. The WI-185 question ("where does the
structure this needs actually exist, and why doesn't it survive to where we consume it?") is answered
rather than worked around: the derivation read genuinely exists at `load()`, and the design *carries
it forward* as a stamp instead of reconstructing it at write time. That is the right direction of
fix. The WI-021 seam is named at door 2's entry, with the correct observation that
`_normalize_address_fields` (`person.py:1265`) sits one frame too high to serve books and meetings.

**Determinism boundary (LLM vs code):** No LLM anywhere in this design; everything is stat
comparison, lock acquisition and syscall preconditions. More to the point, the design consistently
prefers *structurally impossible* over *detected after the fact* — the no-clobber create is a kernel
guarantee rather than a check, and the doc says so in those terms. This is the dimension's ideal
shape, not merely a pass.

**Reversibility:** Layer 1 is pure upside and trivially reversible. The genuine irreversibility is
semantic: once three consumer repos catch `StaleEntityWrite` / `NoteAlreadyExists`, removing them is
a breaking change. The doc bounds that blast radius correctly by making the highest-frequency create
path land as a *reuse* rather than a raise (`person.py:1430-1437`), leaving a genuinely new raising
mode only on the book and company stubs. See the observe-only suggestion below.

**Generalization:** Right level. Shape-defined, not site-defined; future sites inherit the door;
the empty delete cell correctly gets no door but is covered by the unrecognised-kind-is-an-ERROR wall
rule. Not over-built for hypotheticals.

**Cost & maintenance:** One module, one pure-Python dependency, and a widening of
`tests/derivations.py`. The standing maintenance risk is the wall, and the doc has already routed it
to Design correctly — including the single-homing form, which is the right call for the reason
LESSONS #44 gives (`LESSONS.html:748-749`, a counting wall advertises reach it does not have) and
which `tests/derivations.py:1-22` already models on itself.

**Build vs extend vs integrate:** All three ruled in writing — extend `write_markdown_file`,
integrate `filelock`, reject the single-writer daemon and the MCP route.

**Prior art (outside view):** Converges on the standard answer rather than diverging from it:
temp+fsync+rename is what git, sqlite and every editor do; per-file advisory `flock` is the standard
local-host exclusion; an mtime/size precondition re-checked before replace is `If-Match`, vim and
VS Code. No divergence to justify, so the dimension's blocking conditions do not fire — and the
deferred option (Layer 2's viability) *does* have its probe minted, as obligation 1, with a named
owner and a written "re-open this ruling" consequence.

### Why PROMOTE now, and what it does not do

This is round 3 of this gate and the fifth REVISE against `#approach`. Two things decide it.

**The finding below is inside the ruled frame, not a fork of it.** Rounds 1 and 2 blocked because the
doc offered two builds with materially different consumer-facing semantics and picked neither — (a)
vs (b) for `save()`, (i) vs (ii) for the create. The note below has no such fork: both available
resolutions are invisible to consumers and neither needs Dave to originate a precedence rule. That is
the doc's own test for declaration-vs-redesign, and it lands on the Design side of it.

**This item is already escalated, and PROMOTE does not un-escalate it.** U1
(`workshop/src/work_item_linter.py:2628-2650`) is universal and un-epoch-gated: any gate whose latest
verdict is REVISE/REJECT blocks *every* transition. The data-premise gate's standing REVISE therefore
holds this item where it is even with this PROMOTE recorded — including `exploring → architected`
itself. Nothing advances until obligations 1–3 are observed against the live vault. Buying another
document round would not change that, and LESSONS #38 (`LESSONS.html:678-686`) is a scar this very
repo earned on WI-020: a capable reviewer pointed at a rich artifact never runs out of true findings,
and the answer is to escalate for a human sufficiency ruling rather than fold again. The escalation
already exists — obligations 1–3 plus the door-2c reversal question, in one sitting.

**Not re-litigated, and not to be re-opened by a later gate:** the layered composite, the
single-writer-daemon rejection, the MCP rejection, the `filelock` ruling, the (b) ruling for door 2u,
the (i) ruling for door 2c, the shape-defined framing, and the R1 verbatim-in-spec requirement.

### Notes (non-blocking) — the spec must resolve #1; the rest are small

1. **Property 3 and the path-keyed registry are two purposes on one field, and their composition
   re-opens a silent lost update.** `## Approach` states the rule as "preconditioned … on the read its
   bytes were derived from", then states property 3 as "a successful write registers the new stamp
   **for its path**". Those are the same thing only when every write's bytes derive from the latest
   read of that path. Door 1's do (fresh in-lock read); **door 2's do not** — door 2's bytes derive
   from the cache load, which can be arbitrarily older than the last door-1 write to the same path by
   the same process. So: a process loads note P (stamp S0), then calls the exported
   `update_frontmatter_field` (`obsidian_schemas/writer.py:241`, exported at
   `obsidian_schemas/__init__.py:43,116`) on P — door 1 writes and, per property 3, advances the
   registry to S1 — then calls `repo.save(cached_entity)`. The stamp check compares S1 to S1 and
   **passes**, and `writer.py:217-218` rebuilds the frontmatter from the pre-S1 snapshot. The
   frontmatter change is silently destroyed by the very mechanism written to make that loud. This is
   LESSONS #43 exactly (`LESSONS.html:735-743` — two independently-correct guards reading the same
   field for different purposes) and LESSONS #10's missing ordering contract on shared mutable state.
   Note the in-package instances are already self-healing and so do not show the defect:
   `base.update_fields:339-417` re-reads via `_load_file` at `:393`, and `_writeback_identifier:1214`
   deliberately routes through it. The exposure is the exported module-level writers.
   Two resolutions, both consumer-invisible, so this is Design's pick and not another approach round:
   either key the stamp to the *payload's* derivation (a door-2 write registers the stamp for the
   entity it just wrote; a door-1 write does not satisfy a door-2 payload's precondition), or require
   a door-1 write to refresh the cached entity for that path so cache and stamp co-move. Property 3's
   stated justification — the create-then-save sequence — is satisfied by the first without the
   coupling.
2. **`FileExistsError` and `NoteAlreadyExists` will both mean "destination exists."** The
   `overwrite=False` guard at `writer.py:186-187` is one of the generator-B table rows, but the doc
   does not say what the collapsed check raises. They are not interchangeable to a caller —
   `FileExistsError` is an `OSError`, `NoteAlreadyExists` is a `LoudFailError`/`ValueError` — and
   `tests/test_writer.py:153` already catches the former. Say which survives.
3. **The consumer-facing consequence is wider than `save()`.** Because door 2 lives inside
   `write_markdown_file`, and that function is exported (`obsidian_schemas/__init__.py:42,115`), the
   new raising modes join the *public function's* contract, not just the repositories'. The doc
   states the consequence only for `save()` / `create_stub` / `find_or_create_stub`. One sentence.
4. **Consider shipping Layers 2+3 observe-only first.** Nothing in the doc measures how often
   cooperating writers actually collide. An initial mode that logs `StaleEntityWrite` /
   `NoteAlreadyExists` conditions without raising would let the real rate be observed across three
   consumer repos before the refusal is turned on, and Layer 1 (the torn-write kill) needs no such
   ramp. Cheap reversibility on the one genuinely irreversible part of this change.
5. **The doc's stated reason for "no spec" cites a rule that does not apply to this item.**
   `## Spec-Writer Round — 2026-08-09` reason 1 says "the D3 rule refuses `→ specced` without a
   data-premise PROMOTE". D3 is epoch-gated —
   `workshop/src/work_item_linter.py:AUDIT_EPOCH:632` is `2026-06-21` and `post_epoch_audit` is
   `str(gi.created) >= audit_epoch` (`:2620`) — and this item's `created` is `2026-03-22`, so D3 is
   **exempt** here. The conclusion is right for a different and stronger reason: U1 (`:2628-2650`),
   which is universal. Worth correcting, because anyone reasoning from D3's exemption would wrongly
   conclude the item can move.

```verdict
gate: architect
verdict: PROMOTE
date: 2026-08-09
model: claude-opus-5
note: Round 2's create cell is closed correctly and verified in code (person.py:1429 cache guard, company.py:153 no guard at all, book.py:163/meeting.py:185 bypassing BaseRepository.save — so write_markdown_file:154 is the only total placement), and the generator-B rule is a genuine audit fold rather than a fourth instance; the one residue I found (property 3's path-keyed stamp lets a door-1 write satisfy a door-2 payload's precondition) has no consumer-facing fork and is Design's to key correctly, while U1 already holds this item on the data-premise REVISE until obligations 1-3 are observed against the live vault.
```

## Data Audit — 2026-08-09

**Recommendation: REVISE — and the re-raise is the finding.** (Round 3, cold-start; every predicate
below re-run against this tree, nothing carried from rounds 1–2.)

This is the third data-premise round and the third consecutive `targets: #approach`. That repetition is
deliberate and is the signal: **every premise in this document that a cage-scoped session can check has
now been checked across three rounds, and all of them hold.** What blocks is a set of three observations
against the live vault that no session scoped to this worktree can make — and it has been unchanged
since round 1 while the document has been revised three times around it. Rounds 1 and 2 each closed a
real document defect (the routing enumeration; the quarantine rename's inexpressibility). Round 3 closed
nothing of mine because I had nothing left open that a document round could close.

### Trigger check

**Class 1 and Class 2 both still fire**, unchanged in kind:

- **Class 1 — external-contract shape.** Layer 2's viability rests on the filesystem under the live
  vault; R1's clause (c) rests on Obsidian's on-save behaviour; sentinel placement rests on whether
  Obsidian indexes dot-directories. Claims about production, not logic.
- **Class 2 — rule-effect-against-existing-corpus.** Round 3 introduced new predicates over the current
  tree: a re-partitioned routing set (13 content sites to door 1, `writer.py:236` to door 2), the door-2
  placement claim (`write_markdown_file` is the only total choke point), the create-cell claims, and the
  `REASONS`-frozenset integration constraint. All are predicates over what exists today, and all are
  re-run below.

### Grounded this round — round 3's new Class-2 premises all hold

Predicate, run against this tree on 2026-08-09, `tests/` excluded:

```
rg -n 'write_text|write_bytes|\.rename\(|\.unlink\(|os\.remove|os\.rmdir|shutil\.|mkdir|\.touch\(|symlink|os\.replace|mkstemp|NamedTemporaryFile|flock|fcntl|fsync|threading|RLock' obsidian_schemas/ scripts/
```

**Corruption premise — CONFIRMED, still live.** Zero hits for `flock`, `fcntl`, `fsync`, `os.replace`,
`mkstemp`, `NamedTemporaryFile`, `threading`, `RLock` in `obsidian_schemas/` or `scripts/`. Every write
is a bare `Path.write_text`. The item's reason to exist holds, unchanged across all three rounds.

**Routing set — re-derives cell for cell, third time.** 14 content rewrites (`writer.py:236,283,333,365`;
`repositories/base.py:390`; `repositories/person.py:1543,1554,1652,1769,1845,1912`;
`scripts/lint_vault.py:876,894`; `scripts/migrate_person_to_discuss.py:104`), one `Path.rename`
(`scripts/lint_vault.py:1038`), two `mkdir` (`writer.py:233`, `scripts/lint_vault.py:1034`), zero
deletes. Round 3's *partition* of that set also checks out: the door-1 list is 5 parse-and-reserialize
plus 8 verbatim-carry-through = 13, leaving `writer.py:236` — the write inside `write_markdown_file` —
as the sole door-2 site. The arithmetic in `## Approach` is exact, not approximate.

**Round 3's four new tree-grounded claims, each verified in code rather than inherited:**

1. **The create cell.** `obsidian_schemas/repositories/person.py:create_stub:1337` guards on
   `self.get(clean_name)` at `:1429`, and `obsidian_schemas/repositories/base.py:get:258-269` is
   `self._cache.get(...)` behind `_ensure_loaded()` — a *lazy load-once*, not a re-stat, so the guard
   genuinely cannot see a note another process created after this process loaded. It builds a `Person`
   at `:1444-1452` and saves at `:1466`; `obsidian_schemas/repositories/base.py:save:294` defaults
   `overwrite=True` at `:299`. `CompanyRepository.create_stub`
   (`obsidian_schemas/repositories/company.py:153-194`) has **no collision branch of any kind** and goes
   straight to `self.save(...)` at `:192`; `BookRepository.create_stub` is at `:273`, same shape.
2. **The WI-126 no-op on a fresh stub.** `obsidian_schemas/writer.py:210-214` runs the drop check only
   `if existing_lines:`, and the person default body is `"## To Discuss\n\n## Timeline\n\n## Notes\n"`
   (`obsidian_schemas/body_sections.py:ENTITY_BODY_CONFIG:306` — headings only), so the set is empty and
   `writer.py:236` rebuilds from the in-memory entity (`:217-218`). Confirmed.
3. **The `REASONS` integration constraint — the one new *quantified* claim, and the number is right.**
   `obsidian_schemas/errors.py:REASONS:88` is a frozenset of **exactly twelve** string literals (counted:
   `:89-101`), and `bounded_message:109-120` raises `ValueError` on any reason outside it. So the
   Approach's warning is exact: a subclass minted without its literal in the same edit raises at first
   construction — i.e. precisely when the conflict it exists to report occurs.
4. **The `overwrite=False` collapse the architect flagged as note 2 is real in code.**
   `obsidian_schemas/writer.py:186-187` raises `FileExistsError` for "destination exists", 50 lines
   before the write at `:236` — the check-then-mutate gap the generator-B table names. It is a Design
   question (which exception survives), not a premise defect.

**One thing the tree says that strengthens obligation 1's un-groundability rather than weakening it.**
Nothing in this repository names or characterizes the live vault, and that is now *by construction*:
WI-024 removed the hardcoded `DEFAULT_VAULT_PATH` (`state/work-items.json` records "no
caller-independent filesystem path survives as a default in `obsidian_schemas/` or `scripts/`"), leaving
`OBSIDIAN_VAULT_PATH` read from the environment at
`obsidian_schemas/repositories/base.py:ENV_VAULT_PATH:61`, `scripts/lint_vault.py:52` and
`scripts/migrate_person_to_discuss.py:160`. `docs/backlog-campaign-2026-07-05.md:97`'s APFS record still
covers the code checkout, not the vault. Obligation 1 cannot be discharged from inside this tree by any
future round either — this is a permanent property of the repository, not a gap in my search.

### Not grounded — the same three, unchanged since round 1

Obligations 1–3 remain entirely unobserved. This session has no shell. Three OPEN data questions, over
the Step-5 cap of two, which is by itself dispositive for the verdict. Their weights are unchanged:

1. **Filesystem under the vault — the one that blocks the frame.** `## Approach` states its own
   conditionality: "This Approach is written on the assumption that it comes back local POSIX; if it does
   not, doors 1 and 2 fall back to Layers 1+3 only and every residual above widens." A negative result
   does not adjust the spec — it reopens the four-way fork this item's exploration exists to have closed.
2. **Obsidian's on-save behaviour — blocks text the spec must reproduce verbatim.** R1's clause (c) is
   correctly marked in `## Approach` as resting on it. If Obsidian truncates in place, (c) is wrong in
   kind and the residual the spec is *required* to state is understating the risk.
3. **Dot-dir sentinel visibility — does not block the frame,** only the configuration surface for three
   consumer repos. It rides in the same sitting at zero marginal cost.

### Required grounding

Unchanged in substance from rounds 1 and 2; the runnable forms are already recorded at
`## Spec-Writer Round — 2026-08-09` ("Not discharged, and who owns each") and are not re-derived here.
Run obligations 1–3 against the live vault, paste the results, restate R1 clause (c) on what was
observed and remove its marker, and record the sentinel fallback as a decision if the probe is indexed.
Round 1's item 4 is closed and stays closed.

### What this verdict is, and is not, asking for

It is **not** asking for a fourth document round. Read the series — `#approach, #intent` → `#approach` →
`#approach` — as it is meant to be read: rounds 1 and 2 converged, round 3 had nothing of mine left to
close, and the target is now stationary because the residue is not a document defect. A fourth
cage-scoped pass would re-derive the same 14/1/2/0 inventory, re-confirm the same citations, and
re-report the same three unobserved facts. That is a treadmill, and the answer to a treadmill is not
another lap.

What it is asking for is the sitting that three sections of this document now converge on: **obligations
1–3 against the live vault, plus the two standing reversal questions for Dave** (door 2c's option (i)
vs (ii); `filelock` vs a hand-rolled `_HELD` registry — both *ruled*, so what goes to him is the chance
to reverse a written decision, not a gap). The architect's round-3 PROMOTE and this REVISE are not in
tension: U1 holds the item on this verdict, exactly as that PROMOTE says it does, and it should — the
item is correctly escalated to a human, and PROMOTE from this gate would convert a well-escalated item
into a spec written on an assumption whose negation invalidates Layer 2 across all three doors. That is
the precise failure this gate exists to prevent, and it is the only reason I am not promoting a document
I otherwise find fully grounded.

```verdict
gate: data-premise
verdict: REVISE
date: 2026-08-09
model: claude-opus-5
targets: #approach
note: Third consecutive #approach re-raise, and the repetition IS the finding — every tree-checkable premise now holds, including round 3's new ones (create cell cache-guard at person.py:1429 via base.py:get:269's load-once, company.py:153 with no collision branch at all, WI-126 no-opping on the headings-only body at body_sections.py:306, and errors.py:REASONS:88 confirmed as exactly twelve literals with bounded_message:109-120 raising outside them), and the routing set re-derives cell for cell at 14/1/2/0 with round 3's 13+1 partition exact; what blocks is unchanged since round 1 — obligations 1-3 need a shell against the live vault, obligation 1 alone can invalidate Layer 2 across all three doors, and WI-024's removal of DEFAULT_VAULT_PATH means no future cage-scoped round can ground it either, so this is an escalation signal rather than a request for a fourth document round.
```

## Architectural Review — 2026-08-09

**Recommendation: REVISE — return to exploration** (round 4, cold-start; read against the tree, not
against rounds 1–3's notes. Both findings are in `## Design`, which did not exist when this gate last
ran, and neither re-raises `#approach`.)

### Trigger check

Unchanged and still firing: new module (`obsidian_schemas/vault_io.py`), >3 files across different
concerns, replaces a core system (every write path), effort > 1 day, and the resulting semantics
become a contract for three consumer repos (`docs/backlog-campaign-2026-07-05.md:95`).

### What round 3 bought — closed, verified, and not to be re-opened

Re-derived against the tree this round rather than read off the doc:

- **Note #1 (the two-purpose stamp registry) is closed, and D5 picks the right option.** Keying the
  stamp to the payload's derivation — "the registry records at exactly the points where an ENTITY is
  derived from a file's bytes, and nowhere else; a door-1 write does not touch it" — kills the
  S1-vs-S1 pass. The stat-before-read ordering argument in D5 is also correct and is the kind of
  reasoning that is usually left implicit: an older stamp fails closed, a newer one loses data.
- **Note #2 is closed in D8(b), and the reason given is a real language constraint,** not a
  preference. `LoudFailError` reaches `ValueError` and `FileExistsError` reaches `OSError`; a class
  inheriting both does fail at class creation. `tests/test_writer.py:153` does catch
  `FileExistsError` today, and Task 14 is the right place for it.
- **Note #4 is closed as D6/D9/R9,** with the correct default (`enforce`) and the correct reason for
  it. Note #5 is corrected in the amended `## Spec-Writer Round`.
- **The frame itself.** Layers 1–3, the (b) ruling for door 2u, the (i) ruling for door 2c, the
  `filelock` ruling, the MCP and single-writer-daemon rejections, door 3, the shape-defined framing
  and the generator-B rule are all settled and are **not** re-opened here. The three live-vault
  obligations are discharged with their evidence scope stated, which is the right form.
- **Wall B checks out as specified.** The only `os.<attr>` uses under `obsidian_schemas/` or
  `scripts/` are `os.environ` at `obsidian_schemas/repositories/base.py:97`,
  `scripts/lint_vault.py:52` and `scripts/migrate_person_to_discuss.py:160` — all inside
  `OS_READONLY_NAMES`, so the predicate-not-exemption claim in D10 holds.

### Blocking issues

**1. The observation side of the door-2 boundary is enumerated against one `_load_file` when the
tree has three — so `BookRepository.save()` and `MeetingRepository.save()` of any note loaded from
the vault raise `NoteAlreadyExists` in the default mode, and every green light this item ships stays
green (`## Design` D5, `## Implementation Plan` Task 7).**

D8's placement ruling made the *enforcement* side total by moving the door to the one choke point
every writer reaches. The *observation* side has the identical structure and did not get the same
treatment. Verified in code this round:

- `## Design` D5 names the observation point as "`BaseRepository._load_file`
  (`obsidian_schemas/repositories/base.py:_load_file:226`, which `load()` at `:187` and `refresh()`
  via `load()` both route through)", and Task 7 orders the recording added there and nowhere else.
- `obsidian_schemas/repositories/base.py:load:187` calls `self._load_file(file_path)` — dynamic
  dispatch. `BookRepository._load_file` (`obsidian_schemas/repositories/book.py:57-81`) and
  `MeetingRepository._load_file` (`obsidian_schemas/repositories/meeting.py:64-85`) are **complete
  overrides that never call `super()._load_file`**; each parses and returns `doc.entity` itself
  (`book.py:76`, `meeting.py:80`). So a book or meeting loaded from the vault never reaches
  `base.py:226`, and D5's parenthetical is the tell — `load()` routes through `self._load_file`, not
  through `BaseRepository._load_file`.
- The tree already states this corpus, in the very module Task 2 cites: `tests/derivations.py:
  load_file_implementations:365-368` — *"The map is MANY-TO-ONE: four classes resolve to three
  functions today (PersonRepository and CompanyRepository declare no `_load_file` of their own)."*
  The Design's enumeration disagrees with a derivation this document elsewhere relies on.
- Consequence, following D8's own flow: `snapshot_stamp(path)` is `None` for every book and meeting
  → step 5's zero case fires → `create_note(path, content)` → the destination exists → the kernel
  refuses → `NoteAlreadyExists`. `BookRepository.save:138-179` and `MeetingRepository.save:160-192`
  call `write_markdown_file` directly (`book.py:163`, `meeting.py:185`), so they take the door and
  the refusal. This is not the cross-process residual R8 and not the `auto_load=False` case ruled in
  door 2c; it is the ordinary in-process update path for two of the four repositories.

**Nothing this item ships detects it.** The routing wall's oracle is mutation-capability
single-homing — structurally blind to a *missing observation*. AC-1…AC-10 name no book or meeting
update path. And the floor does not cover it either: a sweep of `tests/test_repositories.py` for
save/update cases returns only `PersonRepository` ones (`:629-716`, `:800-873`), and no test loads a
book or meeting and then saves it. So the build lands GREEN — floor, wall and acceptance battery —
and HAL9000 / exocortex lose book and meeting updates on the first call after import. `observe` mode
does not mitigate this; it *masks* it, since R9 proceeds with today's semantics for exactly the
refusals that would have surfaced the gap.

This is LESSONS #7 (`LESSONS.html:240-246`, "audit the real corpus before patching — `NameValidator`
took three iterations because each fix was based only on the patterns we'd happened to see"), and it
is generator A recurring one level down: the observation points were chosen before the loader
implementations were enumerated.

**Why this needs a ruling rather than a note.** The three closures have different totality
properties and one of them collides with a pin this document orders untouched:

- (A) **Record inside each of the three `_load_file` implementations.** This is the
  route-every-one-individually shape whose miss `## Approach` explicitly rejected for door 2 ("the
  routing wall structurally cannot see it"), and a fifth repository that declares its own
  `_load_file` silently loses stamps again — re-arming the same defect on a future entity type.
- (B) **Make the observation a template method** — `BaseRepository._load_file` stats, records, and
  delegates parsing to a hook the subclasses override. Total, and it makes the boundary claim true
  by construction. But it changes the shape of the exact method `tests/test_loud_fail_parse.py:301`
  pins at `== 3` via `tests/derivations.py:load_file_implementations:355`, and Task 2 orders that pin
  "must NOT be edited".
- (C) **Record in `load()`'s loop at `base.py:187-193`.** Total for `load()`/`refresh()`, but not for
  the direct `_load_file` callers the design depends on — `base.update_fields:393` and door 2c's
  recovery re-read in D9.

Pick one in writing, with its interaction with the `== 3` pin stated, and add the book/meeting update
path to the acceptance battery so the wall's blind spot is covered by a behavioural check rather than
by inspection.

**2. Wall A forbids a call that Task 9 orders left in place, so `## Acceptance Criteria` AC-7 is
unsatisfiable as written and Task 12's verify cannot go green (`## Design` D10, Task 9, Task 12).**

- D10 declares `MUTATION_NAMES = {"write_text", "write_bytes", "rename", "replace", "mkdir"}` and
  Wall A asserts `filesystem_mutation_uses(python_files_under(PACKAGE_ROOT, SCRIPTS_ROOT))` returns
  uses in `obsidian_schemas/vault_io.py` **and nowhere else**. AC-7 states it as the criterion.
- There are exactly two `mkdir` calls under those roots, both live and both verified this round:
  `obsidian_schemas/writer.py:233` (`file_path.parent.mkdir(parents=True, exist_ok=True)`) and
  `scripts/lint_vault.py:1034` (`dest_dir.mkdir(parents=True, exist_ok=True)`).
- Both are ruled to **stay where they are**: `## Approach`'s "the cells that get no door" rules the
  namespace cell out of the primitive, R5 declares it, D9 says "`quarantine_dir` and the
  `dest_dir.mkdir` at `:1034` are unchanged (R5)", Task 9 says "Leave `dest_dir.mkdir` at `:1034`
  alone (R5)", and D11's `writer.py` row does not move `:233`.

Task 9 and Task 12 therefore cannot both be satisfied, and Task 12's stated verify
("`tests/test_write_routing.py -q` GREEN") is unachievable by a builder who follows the plan. The
failure mode matters more than the contradiction: the cheapest green from inside the cage is to drop
`"mkdir"` from `MUTATION_NAMES`, which is the wall silently narrowing its own reach — the precise
thing D10's fixture battery and LESSONS #44 exist to prevent, and it would land as an undeclared
weakening of the claim AC-7 advertises.

Rule it explicitly, one sentence either way: `mkdir` leaves the vocabulary and R5 is extended to say
the namespace cell is outside the *wall's reach* as well as outside the doors (so the
"unrecognised-kind-is-an-ERROR" claim is scoped honestly rather than overstated); or the two sites
route through a `vault_io` namespace helper, which contradicts R5 as currently written and needs R5
restated; or Wall A carries an explicit narrow exemption for `mkdir(parents=True, exist_ok=True)`
with the no-loss-mode reason attached. Whichever wins, the match-shape fixture battery in D10 lists
`p.mkdir(parents=True)` and `os.makedirs(d)` as MUST-MATCH shapes, so that list moves with it.

### Suggested adjustments

- In `## Design` D5, name the observation point so it is total over the loader corpus the tree
  actually has, and state the choice's interaction with `tests/test_loud_fail_parse.py:301`'s `== 3`
  pin. Update Task 7 to match, and add `book.py` / `meeting.py` to `## Write Targets` for whatever
  the ruling requires beyond threading the keyword.
- Add one acceptance check covering "a repository that overrides `_load_file` loads a note and saves
  it" — the wall cannot see this class, so it needs a behavioural oracle.
- Rule the `mkdir` cell's relationship to Wall A in D10 and reconcile Task 9, Task 12 and AC-7 with
  the ruling.

### Notes (non-blocking)

- **`overwrite`'s two defaults are worth one confirming sentence in D8(a).** The exported
  `write_markdown_file` defaults `overwrite=False` (`obsidian_schemas/writer.py:160`) while
  `BaseRepository.save` defaults it to `True` (`:299`). Under D8 step 5 that means a bare
  `write_markdown_file(path, entity=e)` from a consumer keeps today's create-or-refuse meaning, which
  reads correct — but D8(a) says "`overwrite=False` now *means* 'this is a create'" without noting it
  is also the exported function's default, and a reader can easily take it for a repository-only flag.
- Everything else I spot-checked in `## Design` resolves and means what the doc says: the `REASONS`
  frozenset constraint, the `_is_write_call` widening rationale, `_body_content_lines`'s body-only
  reach, and the four `save()` paths' convergence on `write_markdown_file`.
- Neither finding needs a shell. Both are tree-grounded, and both are orthogonal to the discharged
  obligations — no live-vault observation changes either one.

```verdict
gate: architect
verdict: REVISE
date: 2026-08-09
model: claude-opus-5
targets: #design, Task 7, Task 9, Task 12, AC-7
note: D5/Task 7 record the derivation stamp only in BaseRepository._load_file:226, but book.py:57 and meeting.py:64 fully override _load_file (the corpus tests/derivations.py:365-368 itself documents as three loaders), so every book and meeting loaded from the vault has no stamp and D8 step 5's zero case turns BookRepository.save/MeetingRepository.save into NoteAlreadyExists while floor, wall and AC battery all stay green; separately D10's Wall A forbids the two live mkdir calls (writer.py:233, lint_vault.py:1034) that R5/D9/Task 9 order left in place, making AC-7 and Task 12's verify unachievable as written.
```

## Data Audit — 2026-08-09

**Recommendation: REVISE — and this time the target MOVES.** (Round 4, cold-start; every predicate
below re-run against this tree, nothing carried from rounds 1–3.)

Read this verdict against the series. Rounds 1, 2 and 3 all targeted `#approach`, and round 3 said
plainly that the repetition *was* the finding: the residue was three observations against the live
vault that no cage-scoped session could make. **That escalation worked.** Obligations 1–3 were run
in the conductor sitting recorded at `### DISCHARGED — 2026-08-09`, the results are pasted in the
document, R1's clause (c) was restated on what was observed rather than on what was assumed, and
`## Design` … `## Risk Analysis` now exist. My standing blocker is CLOSED and is not re-raised.

What blocks now is different in kind, in location, and in owner: `## Design` introduced a new
Class-2 predicate — *which functions in the current tree derive an entity from a file's bytes* — and
that predicate, run against this corpus, comes back **false as written**.

### Trigger check

**Class 1 — DISCHARGED this round, for the first time in four rounds.** The three external-contract
premises (filesystem under the vault, Obsidian's on-save behaviour, dot-dir sentinel visibility) are
observed, dated, and carry their evidence scope. Obligation 2 came back NEGATIVE and the document did
the right thing with it: R1's clause (c) is restated on the inode/size observation
(`220735514`, `5049 → 5085`) instead of on the assumed whole-file safe-write, and `## Verification`
reproduces the restated form verbatim. Obligation 3's decision carries its own limit ("filename
search only; full-text and graph not separately checked") rather than rounding up to "Obsidian
ignores dot-dirs". That is the correct shape for an observation that answered less than the whole
question. Nothing in Class 1 is open.

**Class 2 — still fires, and now over `## Design`'s predicates rather than `## Approach`'s.** D5,
D8, D10 and Tasks 7/9/11/12 are all rules whose correctness depends on their effect against the
*current* corpus: where entities are derived, which mutation calls exist, which tests exercise which
repository. Re-run below.

### Grounded this round — the inventory premises all still hold

Predicate, run against this tree on 2026-08-09, `tests/` excluded:

```
rg -n 'write_text|write_bytes|\.rename\(|\.unlink\(|os\.remove|os\.rmdir|shutil\.|mkdir|\.touch\(|symlink|os\.replace|mkstemp|NamedTemporaryFile|flock|fcntl|fsync|threading|RLock' obsidian_schemas/ scripts/
```

- **Corruption premise — CONFIRMED, still live, fourth round running.** Zero hits for `flock`,
  `fcntl`, `fsync`, `os.replace`, `mkstemp`, `NamedTemporaryFile`, `threading`, `RLock`. Every write
  is a bare `Path.write_text`.
- **Routing set — re-derives cell for cell: 14 / 1 / 2 / 0.** Content rewrites at
  `obsidian_schemas/writer.py:236,283,333,365`; `obsidian_schemas/repositories/base.py:390`;
  `obsidian_schemas/repositories/person.py:1543,1554,1652,1769,1845,1912`;
  `scripts/lint_vault.py:876,894`; `scripts/migrate_person_to_discuss.py:104`. One `Path.rename`
  (`scripts/lint_vault.py:1038`), two `mkdir` (`obsidian_schemas/writer.py:233`,
  `scripts/lint_vault.py:1034`), zero deletes. D7's 5 + 8 = 13 door-1 partition leaving
  `writer.py:236` to door 2 is exact.
- **`REASONS` is exactly twelve literals** (`obsidian_schemas/errors.py:89-101`), the prose pin at
  `:84` says "twelve" and is correctly ordered de-pinned by Task 2, and `bounded_message:114-120`
  does raise on any reason outside the set. The integration constraint D0/Task 2 states is real.
- **Wall C is green against today's tree.** The only `import`s of `shutil`, `tempfile`, `fcntl`,
  `mmap` or `filelock` under `obsidian_schemas/` or `scripts/` are: none. The only `os` imports are
  `obsidian_schemas/repositories/base.py:9`, `scripts/lint_vault.py:22`,
  `scripts/migrate_person_to_discuss.py:23` — all for `os.environ`, inside `OS_READONLY_NAMES`, so
  Wall B's predicate-not-exemption claim holds too.
- **`tests/derivations.py:_is_write_call:189-195` matches `{"write_text", "write_bytes"}` on
  `node.func.attr` only** — confirmed, so D10's widening obligation is correctly stated.

### Premise vs reality — the one that comes back FALSE

**The premise.** `## Design` D5 names the door-2 observation point as a single function:
"`BaseRepository._load_file` (`obsidian_schemas/repositories/base.py:_load_file:226`, which `load()`
at `:187` and `refresh()` via `load()` both route through)". Task 7 orders the stamp recording added
there and nowhere else. The rule this serves is total only if that one function is where every
entity in this package derives from a file's bytes.

**The corpus, derived rather than assumed.** Sweeping for the derivation itself — every call of
`parse_markdown_file` under `obsidian_schemas/` — returns exactly three sites, in exactly three
functions:

| Function | Derivation site | Calls `super()._load_file`? |
|---|---|---|
| `obsidian_schemas/repositories/base.py:_load_file:226` | `:239` | — (it is the base) |
| `obsidian_schemas/repositories/book.py:_load_file:57` | `:74`, returning `doc.entity` at `:76` | **no** — complete override, `:57-81` |
| `obsidian_schemas/repositories/meeting.py:_load_file:64` | `:78`, returning `doc.entity` at `:80` | **no** — complete override, `:64-85` |

`obsidian_schemas/repositories/base.py:187` calls `self._load_file(file_path)` — dynamic dispatch —
so a book or meeting loaded from the vault never reaches `base.py:226`. `PersonRepository` and
`CompanyRepository` declare no `_load_file` and do inherit it. **The tree already states this corpus
in the module Task 2 and Task 11 both cite**: `tests/derivations.py:load_file_implementations:355`
carries it, and `tests/test_loud_fail_parse.py:300-301` pins it at 4 classes → **3** loaders — the
same pin Task 2 orders "must NOT be edited". So D5's enumeration contradicts a derivation this
document elsewhere relies on and forbids changing.

**The effect of the rule against today's corpus.** Following D8's own numbered flow for
`BookRepository.save` (`obsidian_schemas/repositories/book.py:138-179`, calling
`write_markdown_file` directly at `:163`) or `MeetingRepository.save` (`meeting.py:160-192`, at
`:185`): `snapshot_stamp(path)` is `None` → step 5's zero case fires → `create_note` → the
destination exists → `NoteAlreadyExists`. Not the cross-process residual R8, not the `auto_load=False`
case ruled in door 2c — the ordinary in-process update path for two of the four repositories, on the
first save after load, in the DEFAULT mode.

**And the corpus cannot report it.** This is the part that is mine rather than the architect's, and I
ran it: `tests/test_repositories.py` contains six `repo.save(` calls, all at `:644-725` and all
`PersonRepository`. The book section (`:1901-2019`) and meeting section (`:2025-2150`) construct
repositories and read; **neither contains a single `save(`**. So the floor stays GREEN, the routing
wall stays GREEN (its oracle is mutation-capability single-homing — structurally blind to a *missing
observation*), and AC-1…AC-10 name no book or meeting update path. `observe` mode does not mitigate
this; per R9 it proceeds with today's semantics for exactly the refusals that would have surfaced it.

**One extension the architect's finding does not name, same root, different consequence.** D5's
self-healing argument — "`BaseRepository.update_fields` re-reads through `_load_file` at
`obsidian_schemas/repositories/base.py:393` after its door-1 write, so it re-registers the new stamp
*and* replaces the cached entity in the same step; cache and stamp co-move because the code already
made them" — is dispatch-dependent in the identical way. `:393` is `self._load_file(file_path)`, so
for a book or meeting repository it lands in the overriding loader and the stamp does not co-move.
Whichever of D5's closures (A)/(B)/(C) is chosen has to cover `:393` as well as `:187`, and option
(C) — record in `load()`'s loop — explicitly does not.

**The second Class-2 collision, independently confirmed.** D10's `MUTATION_NAMES` includes `"mkdir"`
and Wall A asserts `filesystem_mutation_uses` returns uses in `obsidian_schemas/vault_io.py` and
nowhere else. Run against today's tree that predicate returns `obsidian_schemas/writer.py:233` and
`scripts/lint_vault.py:1034` — both live, both ruled to STAY (`## Approach`'s namespace cell, R5, D9,
Task 9). AC-7 is therefore unsatisfiable and Task 12's verify unachievable as written, and the
cheapest green from inside the cage is to drop `"mkdir"` from the vocabulary — a wall silently
narrowing its own reach, which is the exact failure D10's fixture battery exists to prevent.

### Required grounding

Two items. Both are tree-grounded; **neither needs a shell, and no live-vault observation changes
either one** — the Class-1 residue that held rounds 1–3 is genuinely closed.

1. **Re-derive D5's observation points from the loader corpus rather than naming one.** State the
   closure (A / B / C or another), state its interaction with the `== 3` pin at
   `tests/test_loud_fail_parse.py:301` that Task 2 orders untouched, and make it cover the direct
   `_load_file` callers — `obsidian_schemas/repositories/base.py:393` and door 2c's recovery re-read
   in D9 — not only `load()`'s loop. Update Task 7 and `## Write Targets` to match.
2. **Add a behavioural oracle for the loader-override class, and reconcile `mkdir` with Wall A.** The
   acceptance battery needs one check that loads a note through a repository which overrides
   `_load_file` and then saves it, because the wall is structurally blind to this class and the
   existing test corpus has zero such cases. And AC-7 / Task 9 / Task 12 need one sentence deciding
   whether `mkdir` leaves the vocabulary (with R5 extended to say the namespace cell is outside the
   wall's *reach* as well as outside the doors), routes through a `vault_io` helper, or gets a named
   exemption — with D10's must-match fixture list moved to match.

The premise defect here is generator A recurring one level down, and it is worth naming as such so
the next round does not close only the instance: **the observation points were chosen before the
loader implementations were enumerated**, exactly as the primitive's surface was once chosen before
the mutation shapes were. The enforcement side was made total by derivation (D8's placement ruling);
the observation side was written as a list. Deriving it is what closes the class.

```verdict
gate: data-premise
verdict: REVISE
date: 2026-08-09
model: claude-opus-5
targets: #design, Task 7, Task 12, AC-7
note: My three-round #approach block is DISCHARGED — obligations 1-3 are observed, dated and scope-stated, and R1(c) is restated on the negative Obsidian result — but Design introduces a new Class-2 predicate that comes back false: entity derivation happens in THREE functions (base.py:_load_file:226, book.py:57, meeting.py:64, neither subclass calling super, both reached by the dynamic dispatch at base.py:187 and :393, a corpus the tree pins at 3 in tests/test_loud_fail_parse.py:301), while D5/Task 7 record the stamp in one — so D8 step 5's zero case turns the ordinary BookRepository/MeetingRepository update into NoteAlreadyExists, and the corpus cannot report it because all six repo.save( calls in tests/test_repositories.py:644-725 are PersonRepository; separately Wall A's MUTATION_NAMES forbids the two live mkdir calls (writer.py:233, lint_vault.py:1034) that R5/D9/Task 9 order left in place, making AC-7 unsatisfiable.
```

## Spec-Writer Round 5 — 2026-08-09

Both round-4 findings are accepted in full; neither is counter-argued. Both were re-derived against
the tree this round rather than taken from the verdicts — the three loaders, their non-`super()`
overrides, the dynamic dispatch at `base.py:187` and `:393`, the two `mkdir` sites, and the eight
`.save(` calls in `tests/` that are all `PersonRepository`.

### Finding 1 — the observation side. Closed as a CLASS, with the next level swept.

The gates named the generator correctly: *the observation points were chosen before the loader
implementations were enumerated* — generator A one level down. So the fold is not "add book and
meeting to the list".

- **What closes the class:** D5's new "The derivation corpus is DERIVED, not named" ruling, (A′).
  The observation obligation is stated over
  `load_file_implementations(base_repository_subclasses(...))` — a derivation the tree already
  carries and this document already relies on — and it is ENFORCED over that same derived corpus by
  Wall D(i) (D10). A fifth repository that declares its own `_load_file` and forgets to record is a
  RED floor naming the loader, not a silent stamp loss on a new entity type.
- **The next level of the ladder, swept and DECLARED** (in D5, not left for round 5): (i) the
  *derivation* sites — every `parse_markdown_file` call under `obsidian_schemas/`/`scripts/` is one
  of the three loaders, and Wall D(ii) asserts that equality so a derivation added OUTSIDE the loader
  corpus is red rather than the next finding; (ii) the *adoption* sites — every write into `_cache`
  is `base.py:190`, `:412`, `base.py:332`, `book.py:174`, `meeting.py:196`, the first two adopting a
  loader's entity (stamp co-moves by (A′)), the last three adopting door 2's committed bytes (stamp
  co-moves by D8 step 8), with `refresh()`'s zero-entity restore (`base.py:442-455`) checked and not
  desynchronising; (iii) the sub-cell — `PersonRepository`/`CompanyRepository` declare no loader and
  inherit the recording.
- **The `== 3` pin:** (A′) does not move it, and that is the deciding reason it beat closure (B). No
  class gains or loses a `_load_file`, so `tests/test_loud_fail_parse.py:300-301` stay true and stay
  unedited, and Wall D consumes the same derivations rather than duplicating them. (B) would have
  turned both that pin and the residue name-set assertion at `:332` red in a file the plan orders
  untouched, and relocated WI-020's per-subclass no-abort `except`; it is rejected in writing in D5
  and named in `## Scope Boundary` so the builder does not "improve" (A′) into it. (C) is rejected
  for not covering `base.py:393` or D9's recovery re-read — under (A′) both are dispatch-proof
  because the recording is inside the callee.
- **The behavioural oracle the wall cannot supply:** AC-11 /
  `test_a_loader_overriding_repository_can_update_a_note_it_loaded`, authored in Task 7 and finished
  in Task 13 — a `BookRepository` and a `MeetingRepository` each load a note and save it (must
  SUCCEED as a 2u update, never `NoteAlreadyExists`), then save again over an external edit (must
  raise `StaleEntityWrite`). AC-12 covers Wall D structurally. `## Verification` gains a
  "must NOT fail" table for the same class, and `## Verified Diagnosis` gains claims 7 and 8 (the
  three-loader corpus, and the zero book/meeting saves in `tests/`).

### Finding 2 — `mkdir` vs Wall A. Ruled: the calls move; the vocabulary does not.

`ensure_dir(path)` joins `vault_io.py`'s public surface (D1) and both live sites route through it —
`obsidian_schemas/writer.py:233` in Task 7, `scripts/lint_vault.py:1034` in Task 9 — as does
`note_lock`'s own sentinel-directory creation (D3). `mkdir` stays in `MUTATION_NAMES` and
`p.mkdir(parents=True)` / `os.makedirs(d)` stay in the MUST-MATCH fixture list. R5 is restated in
`## Approach`: the namespace cell is outside the PRECONDITION rule, not outside the wall's reach —
the two are different claims and conflating them is what made AC-7 unsatisfiable. The other two
resolutions are rejected in writing in D10: dropping `"mkdir"` is the wall narrowing its own reach
(and blinds Wall A to any future `Path.mkdir`), and a named exemption re-introduces the
exemption-not-predicate shape Wall B exists to avoid. Task 9 and Task 12 now say so explicitly so the
cheapest-green path is closed to a caged builder, and Risk 11 records it.

### What did NOT change

The frame is untouched: layers 1–3, the (b) ruling for door 2u, (i) for door 2c, door 3, the
`filelock` and MCP rulings, the shape-defined surface, the three-primitive door-1 call shape, the
discharged obligations and R1's observation-restated clause (c). No new OPEN item; the count stays
`OPEN: None`. Two non-blocking notes are folded: D8(a) now states that `write_markdown_file` defaults
`overwrite=False` (`writer.py:160`) while `BaseRepository.save` defaults it `True` (`base.py:299`),
and `## Scope Boundary` records why `parser.py` is NOT the recording point (the parser cannot know
whether its caller adopted the entity it returned — recording there is LESSONS #43 again).

## Architectural Review — 2026-08-09

**Recommendation: REVISE — return to exploration** (round 5, cold-start; read against the tree, not
against rounds 1–4's notes. Both findings are in `## Design` D10 and the harness edits it orders;
neither touches the frame, and neither re-raises `#approach`.)

### Trigger check

Unchanged and still firing: new module (`obsidian_schemas/vault_io.py`), >3 files across different
concerns, replaces a core system (every write path), effort > 1 day, and the resulting semantics
become a contract for three consumer repos (`docs/backlog-campaign-2026-07-05.md:95`).

### What round 5 bought — closed, verified, and not to be re-opened

Re-derived against the tree this round rather than read off the doc:

- **Finding 1 (the observation side) is closed, and (A′) is the right closure.** The corpus is three
  functions and the doc now says so from a derivation rather than a list:
  `obsidian_schemas/repositories/book.py:_load_file:57` reads at `:66`, parses at `:74`, returns
  `doc.entity` on the branch at `:75-76` and returns `None` on the wrong-`type` early exit at
  `:70-71`; `obsidian_schemas/repositories/meeting.py:_load_file:64` is the same shape at `:71`,
  `:78`, `:79-80`, `:75-76`; neither calls `super()._load_file`. D5's per-loader placement is
  correct line for line. The `== 3` pin argument holds: `load_file_implementations`
  (`tests/derivations.py:355-377`) resolves classes through `__mro__` and dedupes, so (A′) adds and
  removes no `_load_file` declaration and `tests/test_loud_fail_parse.py:300-301` stay true.
- **Wall D(ii) is true today, and I checked it rather than inheriting it.** Every call of
  `parse_markdown_file` under `obsidian_schemas/` and `scripts/` is
  `obsidian_schemas/repositories/base.py:239`, `book.py:74`, `meeting.py:78` — exactly the three
  loaders. `obsidian_schemas/__init__.py:37,111` re-exports the name and calls nothing.
- **Wall D's two predicates are type-compatible, which is not obvious and matters.**
  `load_file_implementations` mints its `FunctionId` through `_function_id_of`
  (`tests/derivations.py:380-383`, `func.__module__` → posix path + `__qualname__`) while
  `functions_calling` would mint its own through `_iter_functions` (`:122-145`, `module_id` +
  the nesting stack). Both produce `FunctionId("obsidian_schemas/repositories/base.py",
  "BaseRepository._load_file")`, so `<=` and `==` mean what D10 says they mean.
- **Finding 2's `ensure_dir` ruling is right.** Keeping `mkdir` in the vocabulary and moving the two
  calls is the only resolution that does not shrink the wall's reach, and the adoption sweep in D5 is
  accurate — the writes into `_cache` are `base.py:190`, `:332`, `:412`, `book.py:174`,
  `meeting.py:196`, and `refresh()`'s restore at `:450` puts back entities whose stamps the registry
  still holds.
- **The frame.** Layers 1–3, (b) for door 2u, (i) for door 2c, door 3, `filelock`, the MCP and
  daemon rejections, the shape-defined surface and R1's observation-restated clause (c) are settled
  and are **not** re-opened here.

### Blocking issues

Both are the same class, and it is worth naming the class first because closing only the two
instances leaves round 6 the third: **every wall in D10 is asserted green against today's tree by
PREDICTION, not by derivation.** Task 12 says "Wall A is expected GREEN on the first run"; D7 says
WI-020's battery "survives with ONE edit"; D1 says the no-falsy-return rule is enforced by an
existing scan. Each of those is a predicate over the current corpus that nobody ran. Round 4's
`mkdir` finding was the first member. These are the next two, and both come back false.

**1. `_is_write_call` matches attribute calls ONLY, and every door call the design writes is a bare
name — so widening it "by `DOOR_NAMES`" resolves nothing, and three WI-020 acceptance assertions go
red against correct code (`## Design` D7, D10, `## Implementation Plan` Tasks 4, 5, 11; AC-10).**

`tests/derivations.py:_is_write_call:189-195` is:

```python
isinstance(node, ast.Call)
and isinstance(node.func, ast.Attribute)
and node.func.attr in {"write_text", "write_bytes"}
```

The `ast.Attribute` test is a hard gate, and D10 orders the set widened while changing "nothing else
about it" (Task 11 repeats the instruction verbatim). But every door invocation this document
sketches is an `ast.Name` call: D7's routed-site block is `write_note(file_path, new_content,
precondition=stamp)`, D8's flow is `create_note(path, content)` / `write_note(path, content, …)`,
D5's loader block is `stat_stamp(file_path)` / `remember_snapshot(file_path, stamp)`. A bare name is
not an `ast.Attribute`, so after routing the predicate matches **nothing** at any routed site.

Following that through the three sweeps that consume it:

- `functions_reserializing_parsed_frontmatter` (via `_taints_a_write:301`) needs a tainted name to
  reach a matched write call. None of the four writers has one any more, so it returns the empty set
  and `tests/test_loud_fail_parse.py:117-121` — `write_paths == expected`, the four `FunctionId`s at
  `:110-116` — is RED.
- `functions_parsing_then_writing:227` loses `write_markdown_file` (under D8 it commits through
  `create_note`/`write_note` and no longer calls `file_path.write_text` at `:236`), so the
  discrimination proof at `tests/test_loud_fail_parse.py:128-137` — `guard in loose_paths`, then
  `loose_paths - write_paths == {guard}` — is RED.
- `non_completed_write_sites:507` drops every routed function from its universe. `_get_body_content`
  survives via `_SHARED_HELPERS` (`tests/derivations.py:481`); the other **seven** entries of the
  classification map at `tests/test_loud_fail_write.py:126-139` name sites the scan can no longer
  return, and `:146-147`'s `stale` assertion is RED.

That is AC-10 unsatisfiable in three separate clauses, plus Task 4's and Task 5's stated verifies.
The failure mode is worse than the contradiction: `## Write Targets` already declares
`tests/test_loud_fail_parse.py` and `tests/test_loud_fail_write.py` as contingency write targets, and
Risk 6's mitigation points a builder straight at them. A caged builder who hits this red at Task 4 has
written permission to edit the two modules that carry WI-020's shipped acceptance battery, and the
cheapest green is to shrink `expected` and delete the stale map entries — a silent relaxation of a
*previous item's* declared property, arrived at by following this plan exactly.

D7's stated reason for choosing the three-primitive shape over the callback was that it keeps every
parse, dedup and falsy return in its own function body so the `SiteId` qualnames do not shift. That
argument is correct and I re-verified it (`_own_body_nodes:148-164` does skip nested functions). It
solves the *qualname* half of the trap and leaves the *call-form* half open — and the doc shows it
knows the two forms are different, because `filesystem_mutation_uses` is specified to collect both
("an `ast.Name` call whose `id` is in the vocabulary — the aliased-import form") and `functions_calling`
is built on `_called_names:167-182`, which collects `f(...)` and `x.f(...)` alike. Only
`_is_write_call`, the one predicate that has to see the new commit form, is left form-locked.

Two resolutions, both consumer-invisible; the doc must pick one in writing because they are not
equivalent to the wall. Either the doors are always invoked as module attributes
(`vault_io.write_note(...)`, which keeps `_is_write_call` a one-token edit but changes what every
routed site in D5/D7/D8 looks like and what Wall D(i)'s oracle sees), or `_is_write_call` gains an
`ast.Name` arm for `DOOR_NAMES` (which is the smaller behavioural change but is more than "gains the
door names", and needs the same near-miss treatment D10 gives its other predicates). Until one is
written, this item is buildable two ways with opposite outcomes on AC-10 (WI-144).

**2. Wall A's vocabulary is matched on attribute NAME, and `"replace"` is not a filesystem verb in
this tree — Wall A is red on day one against nine live call sites, most of them in files
`## Scope Boundary` forbids the builder to touch (`## Design` D10, Task 11, Task 12; AC-7).**

D10 declares `MUTATION_NAMES = {"write_text", "write_bytes", "rename", "replace", "mkdir"}` and
`filesystem_mutation_uses` collects "an `ast.Attribute` call whose `attr` is in the vocabulary".
`str.replace` shares that attribute name. Run against today's tree, the `.replace(` attribute calls
under `obsidian_schemas/` and `scripts/` are:

`obsidian_schemas/models.py:110`, `:136` (twice); `obsidian_schemas/repositories/book.py:94`, `:124`,
`:207`, `:255` (twice each); `obsidian_schemas/repositories/meeting.py:211`;
`obsidian_schemas/repositories/person.py:1141`; `scripts/lint_vault.py:889`.

Every one is a string operation. `models.py` and `person.py`'s cleaning path are on the
"**Unchanged files — the builder should not touch these**" list, so unlike the `mkdir` cell there is
no `ensure_dir`-shaped move available: the offending calls cannot be relocated into `vault_io.py`
because they are not filesystem calls at all. AC-7 is unsatisfiable and Task 12's verify unachievable,
and the only greens reachable from inside the cage are the two D10 rules out by name — drop the token
(the wall narrowing its own reach) or add an exemption (the exemption-not-predicate shape Wall B
exists to avoid).

**And dropping `"replace"` is not actually available, which is why this needs a ruling rather than a
deletion.** `Path.replace(target)` is a genuine atomic rename with the same attribute name, D2's
replace form is `os.replace(tmp, target)`, and D10's MUST-MATCH battery requires both `os.replace(a,
b)` and `from os import replace as _r` + `_r(a, b)` to match. An attribute-name oracle structurally
cannot separate `p.replace(q)` from `s.replace("-", "")`. The fork is real: discriminate by receiver
(and say what the predicate does with a bare `replace(...)`), or drop `replace` from Wall A and state
in writing that `os.replace` is Wall B's to catch and the aliased-import form needs Wall C widened to
`os` — which it currently is not (`shutil`, `tempfile`, `fcntl`, `filelock`, `mmap` only).

**One ambiguity in the same sentence, which decides how large this is.** D10 defines
`MUTATION_SUSPECT_NAMES` and then no wall consumes it — Wall A says "the vocabulary" without saying
whether that is `MUTATION_NAMES` or the union. If it is the union, `frontmatter.copy()` at
`obsidian_schemas/writer.py:220` and `obsidian_schemas/parser.py:176`, `:211` are three more day-one
reds in files this plan orders unchanged. Say which set `filesystem_mutation_uses` scans.

### Suggested adjustments

- Rule the door **call form** in D7/D8/D5 and reconcile Task 11 with it: either the doors are named
  as module attributes, or `_is_write_call` matches `ast.Name` ids in `DOOR_NAMES` as well. State
  the consequence for `functions_reserializing_parsed_frontmatter`, `functions_parsing_then_writing`
  and `non_completed_write_sites` explicitly, so Tasks 4 and 5 predict "no edit" from a derivation
  rather than from hope — and tighten the two contingency `## Write Targets` entries so a red there
  is a hand-back, not a licence.
- Rule `"replace"`'s membership in `MUTATION_NAMES`, say which set `filesystem_mutation_uses` scans,
  and state where the `os.replace` / aliased-import shapes are caught under the ruling. Move D10's
  MUST-MATCH list with it.
- **The class-level fold, which is what would end this arc:** order the walls' predicates RUN against
  the live tree before the vocabulary is frozen — a Task 0 that prints what each of Walls A–D returns
  today and pins the expected set in the Build Log — instead of asserting first-run green in prose.
  Round 4 found `mkdir` this way, I found `replace` and the call form this way, and the only reason
  those are three findings rather than one is that nobody has executed the predicates. Both of my
  findings would have been caught by running Wall A once.

### Notes (non-blocking)

1. **D5's stat-before-read placement breaks WI-020's no-abort guarantee in two of the three
   loaders.** The sketch puts `stamp = stat_stamp(file_path)` as the FIRST statement of the
   function; in `book.py:57` and `meeting.py:64` the `try:` opens at `:64`/`:70` and the broad
   `except → _note_skip` is explicitly the margin between one bad note and an aborted vault walk
   (`book.py:78-79`, `meeting.py:82-83`, and `base.py:186-193`'s loop has no `try` of its own). A
   `stat_stamp` that raises above the `try` aborts the whole load. Put the stat inside the `try`,
   still above the first read — the ordering argument in D5 is untouched and Wall D(i)'s own-body
   oracle does not care.
2. **D1's no-falsy-return rule may be vacuous rather than enforced.** It says
   `non_completed_write_sites` scans "every function under `PACKAGE_ROOT` that contains a commit
   call", but that scan's universe gate is `_is_write_call` (`tests/derivations.py:507`). D2 commits
   through an fd (`write`, `flush`, `os.fsync(fd)`), so unless `vault_io`'s temp write literally
   names `write_bytes`/`write_text`, none of its functions enters the universe and the stated build
   constraint checks nothing. Harmless either way, but the claim should be true.
3. Everything else I spot-checked in `## Design` resolves and means what the doc says: the twelve
   `REASONS` literals (`obsidian_schemas/errors.py:89-101`) with the prose pin at `:84` correctly
   ordered de-pinned, `bounded_message:114-120` raising outside the set, `CHAINABLE` at `:184`
   including `OSError`, `write_markdown_file`'s two `overwrite` defaults (`writer.py:160` vs
   `base.py:299`), the WI-126 guard's `if existing_lines:` gate at `:210-214`, and the four `save()`
   paths' convergence on `writer.py:154`.
4. Neither blocking finding needs a shell, and no live-vault observation changes either one. The
   discharged obligations stay discharged.

```verdict
gate: architect
verdict: REVISE
date: 2026-08-09
model: claude-opus-5
targets: #design, Task 4, Task 5, Task 11, Task 12, AC-7, AC-10
note: Round 4's two findings are properly closed and verified in code, but D10's walls are asserted green by prediction rather than derivation and two predicates come back false — tests/derivations.py:_is_write_call:189-195 gates on ast.Attribute while every door call D5/D7/D8 sketch is a bare name, so "widened by DOOR_NAMES" matches nothing and the four-writer set, the discrimination proof and seven SiteId entries all go red while Tasks 4/5 pre-authorise editing WI-020's battery; and MUTATION_NAMES' "replace" matches nine live str.replace calls (models.py:110,136, book.py:94,124,207,255, meeting.py:211, person.py:1141, lint_vault.py:889) in files Scope Boundary forbids touching, making AC-7 unsatisfiable with no ensure_dir-shaped move available.
```

## Data Audit — 2026-08-09

**Recommendation: REVISE — the target holds at `#design`/D10, and the vocabulary predicate is worse
than ambiguous: it comes back FALSE under BOTH readings.** (Round 5, cold-start; every predicate
below re-run against this tree, nothing carried from rounds 1–4 or from the round-5 architect.)

Read against the series. Rounds 1–3 targeted `#approach` and were discharged by the conductor sitting.
Round 4 targeted `#design`/Task 7/Task 12/AC-7 and both findings are **closed and verified by me this
round, line for line** — the arc is converging, not treadmilling, and the target has moved twice. What
blocks now is a third member of the class the round-5 architect named: *D10's walls are asserted green
against today's tree by prediction, never by derivation.* I ran them. One of the two the architect
found is sharpened below into something that has **no green answer as written**, which is why this is
a REVISE and not a note.

### Trigger check

**Class 1 — remains DISCHARGED; nothing in this round re-opens it.** Obligations 1–3 (local journaled
APFS, Obsidian's in-place truncate-and-write at inode `220735514` / `5049 → 5085`, dot-dir sentinel not
surfacing in filename search) are observed, dated and scope-stated, and R1's clause (c) still carries
the negative result rather than the assumed safe-write. **No live-vault observation changes anything
below, and none is required to close it** — every predicate here is tree-grounded.

**Class 2 — fires, over `## Design` D10's mutation vocabulary and the predicate that consumes it.**
D10, Task 11, Task 12 and AC-7 are rules whose correctness depends on their effect against the
*current* corpus. Re-run below.

### Grounded this round — everything round 5 added is TRUE against this tree

Re-derived, `tests/` excluded, roots `obsidian_schemas/` and `scripts/`:

- **The loader corpus is three functions, and D5's per-loader placement is correct line for line.**
  `obsidian_schemas/repositories/book.py:_load_file:57` reads at `:66`, parses at `:74`, returns
  `doc.entity` on the branch at `:75-76`, returns `None` on the wrong-`type` exit at `:70-71`, and its
  broad `except → _note_skip` is at `:77-80`; `obsidian_schemas/repositories/meeting.py:_load_file:64`
  is the same shape at `:71`/`:78`/`:79-80`/`:75-76`. Neither calls `super()._load_file`. Round 4's
  finding 1 is genuinely closed by (A′), and the `== 3` pin is untouched by it.
- **Wall D(ii) holds today.** Every call of `parse_markdown_file` under both roots is
  `obsidian_schemas/repositories/base.py:239`, `book.py:74`, `meeting.py:78` — exactly the loaders.
  `obsidian_schemas/__init__.py:37,111` re-exports the name and calls nothing. No script derives an
  entity.
- **AC-11's necessity is real and I re-ran it.** Every `.save(` in `tests/` is
  `tests/test_repositories.py:644,661,676,693,709,725` and `tests/test_writer.py:432,434,440,441` —
  ten calls, all `PersonRepository`. Zero book saves, zero meeting saves. The wall is blind to this
  class and so is the corpus.
- **The routing set re-derives cell for cell: 14 / 1 / 2 / 0.** Fourteen `Path.write_text`
  (`writer.py:236,283,333,365`; `base.py:390`; `person.py:1543,1554,1652,1769,1845,1912`;
  `lint_vault.py:876,894`; `migrate_person_to_discuss.py:104`), one `rename`
  (`lint_vault.py:1038`), two `mkdir` (`writer.py:233`, `lint_vault.py:1034`), zero deletes. D7's
  5 + 8 = 13 door-1 partition leaving `writer.py:236` to door 2 is exact. **Zero `open(` calls of any
  mode under either root** — so the `open(p, "w")` arm of `filesystem_mutation_uses` has no live site
  to trip over, in either direction.
- **Walls B and C are green against today's tree.** The only `os` attribute uses outside a door are
  `os.environ` at `base.py:97`, `lint_vault.py:52`, `migrate_person_to_discuss.py:160` — all inside
  `OS_READONLY_NAMES`, so Wall B's predicate-not-exemption claim is literally true. Zero imports of
  `shutil`, `tempfile`, `fcntl`, `filelock` or `mmap` under either root.
- **`tests/derivations.py:_is_write_call:189-195` gates on `ast.Attribute`** — I read it rather than
  inheriting it. The architect's finding 1 is CONFIRMED and I do not re-litigate it; it is folded into
  the required grounding below because the fix is the same fix.

### Premise vs reality — the vocabulary predicate is false under BOTH readings

**The premise.** D10 declares `MUTATION_NAMES`, `MUTATION_SUSPECT_NAMES`, and a
`filesystem_mutation_uses` that collects "an `ast.Attribute` call whose `attr` is in the vocabulary".
Wall A asserts it returns uses in `vault_io.py` and nowhere else (AC-7), and D10's MUST-MATCH fixture
battery asserts the same predicate resolves 23 named shapes. The round-5 architect asked which set
"the vocabulary" denotes. **Run against this corpus, that question has no green answer** — which
upgrades it from a sizing ambiguity to the blocking defect.

**Reading 1 — `MUTATION_NAMES` only.** Wall A is red on day one against `str.replace`: nine source
lines, fourteen call nodes — `obsidian_schemas/models.py:110`, `:136` (×2);
`obsidian_schemas/repositories/book.py:94`, `:124`, `:207`, `:255` (×2 each);
`obsidian_schemas/repositories/meeting.py:211`; `obsidian_schemas/repositories/person.py:1141`;
`scripts/lint_vault.py:889`. All string operations, and `models.py` and `person.py`'s cleaning path
are on `## Design` D11's "Unchanged by design" list, so unlike the `mkdir` cell there is no
`ensure_dir`-shaped move: they are not filesystem calls at all.

**And under the same reading, D10's own MUST-MATCH battery is unsatisfiable — this is the half the
architect's note does not reach.** Eleven of its 23 claimed shapes name members that exist ONLY in
`MUTATION_SUSPECT_NAMES`: `p.unlink()`, `os.remove(p)`, `shutil.move(a, b)`, `shutil.copyfile(a, b)`,
`shutil.rmtree(d)`, `os.makedirs(d)`, `os.link(a, b)`, `p.symlink_to(q)`, `p.touch()`,
`tempfile.NamedTemporaryFile()`, `tempfile.mkstemp()`. A predicate scanning `MUTATION_NAMES` alone
matches none of them and Task 12's fixture battery fails on eleven asserted-MATCHED shapes. So the
narrow reading cannot be chosen to make Wall A green — it just moves the red from the wall to the
battery that proves the wall means something.

**Reading 2 — the union.** The battery passes and Wall A gains three MORE day-one reds via `"copy"`:
`obsidian_schemas/writer.py:220`, `obsidian_schemas/parser.py:176`, `:211` — all
`frontmatter.copy()`, a dict copy. `parser.py` is on the "Unchanged by design" list and is not a
`## Write Targets` entry at all, so this one is not even relocatable in principle.

**Why this is one finding and not two.** `MUTATION_NAMES`' `"replace"`, `MUTATION_SUSPECT_NAMES`'
`"copy"`, and the aliased-import arm are all the same defect: **an attribute-NAME oracle over a
vocabulary of stdlib verbs cannot separate a filesystem receiver from a `str`/`dict` receiver**, and
this tree exercises both for two of those verbs today. The ruling D10 needs is a discriminator —
receiver or import provenance — not a set membership decision, and it is the same discriminator the
architect's `replace` fork already demands. Choosing either set without one leaves AC-7 unsatisfiable
and Task 12's verify unachievable, and the only greens reachable from inside the cage are the two D10
rules out by name: drop the token (the wall narrowing its own reach) or add an exemption (the
exemption-not-predicate shape Wall B exists to avoid). A caged builder who hits this at Task 12 has
`tests/derivations.py` in `## Write Targets` and the cheapest green is exactly the move the document
forbids in prose.

### Required grounding

Two items, both tree-grounded; **neither needs a shell against the live vault, and the Class-1
obligations stay discharged.**

1. **Rule the vocabulary predicate with a discriminator, then RUN it.** Say which set
   `filesystem_mutation_uses` scans AND how it separates `p.replace(q)` / a filesystem `copy` from
   `s.replace("-", "")` / `frontmatter.copy()` — receiver provenance, import provenance, or dropping
   the colliding tokens with `os.replace` explicitly reassigned to Wall B and Wall C widened to `os`
   (it currently is not). Move D10's MUST-MATCH list to match whichever set is chosen, so the eleven
   SUSPECT-only shapes above are not asserted against a predicate that cannot see them. Then, and this
   is the part that ends the arc: **execute Walls A–D against this tree before the vocabulary is
   frozen and paste what each returns into the document** — a Task 0 whose output is the pinned
   expected set. Round 4 found `mkdir` this way, the architect found `replace` and the call form this
   way, and I found `copy` and the battery's SUSPECT dependency the same way; four findings, one
   unrun predicate.
2. **Rule the door call form and derive — do not predict — its effect on WI-020's battery.** Either
   the doors are invoked as module attributes (`vault_io.write_note(...)`) or `_is_write_call` gains
   an `ast.Name` arm over `DOOR_NAMES`. State the derived outcome for
   `functions_reserializing_parsed_frontmatter`, `functions_parsing_then_writing` and
   `non_completed_write_sites` explicitly, so Tasks 4/5/11 predict "no edit" from a derivation rather
   than from hope, and tighten the two contingency `## Write Targets` entries
   (`tests/test_loud_fail_parse.py`, `tests/test_loud_fail_write.py`) so a red there is a hand-back
   rather than a licence to relax a previous item's shipped acceptance property.

OPEN questions raised: 2 (at the cap; both are "run the predicate", not "defer it").

```verdict
gate: data-premise
verdict: REVISE
date: 2026-08-09
model: claude-opus-5
targets: #design, Task 11, Task 12, AC-7, AC-10
note: Round 4's two findings are closed and I re-verified both against the tree (three loaders line-for-line, Wall D(ii) exact, both mkdir sites), but D10's vocabulary predicate comes back false under BOTH readings of "the vocabulary": MUTATION_NAMES alone leaves Wall A red on 14 str.replace call nodes across 9 lines (models.py:110,136, book.py:94,124,207,255, meeting.py:211, person.py:1141, lint_vault.py:889) AND makes 11 of D10's own 23 MUST-MATCH shapes unsatisfiable because they name SUSPECT-only members (unlink, remove, shutil.move/copyfile/rmtree, makedirs, link, symlink_to, touch, NamedTemporaryFile, mkstemp), while the union adds three more reds via "copy" (writer.py:220, parser.py:176,211) in files D11 orders unchanged — so an attribute-name oracle needs a receiver/import discriminator, not a set choice, and the walls must be RUN against this tree and their returned sets pinned before the vocabulary is frozen.
```

## Spec-Writer Round 6 — 2026-08-09

Both round-5 gates are accepted in full; nothing is counter-argued. Every fact behind them was
re-derived against the tree this round rather than taken from the verdicts: `_is_write_call`'s
`ast.Attribute` gate at `tests/derivations.py:189-195`; the fourteen `str.replace` call nodes at nine
lines; the three `frontmatter.copy()` nodes; the eight `SiteId` entries at
`tests/test_loud_fail_write.py:126-139` and which of them depend on a `write_text` in their own body;
the `_, existing_body = parse_frontmatter(...)` seed at `obsidian_schemas/writer.py:197` that keeps
`write_markdown_file` on the right side of the discrimination proof; and the `try:` line numbers in
all three loaders.

### The class both gates named, and why closing the two instances was not the fold

The round-5 architect stated it and the data-premise gate sharpened it: **every wall in D10 was
asserted green against today's tree by PREDICTION, not by derivation.** Four findings, one generator.
Round 4's `mkdir`, round 5's `replace` and door call form, round 5's `copy` and the MUST-MATCH
battery's dependency on a set no wall consumed. Fixing `replace` and the call form would have left
round 6 the fifth member. So round 6 closes the class twice over, structurally and procedurally, and
then sweeps the level above.

**Fold 1 — structural (D10.0–D10.2). Discriminate by PROVENANCE, never by member name where a module
discriminator exists.** The data-premise gate's diagnosis is exact and is adopted as the ruling: *an
attribute-NAME oracle over a vocabulary of stdlib verbs cannot separate a filesystem receiver from a
`str`/`dict` receiver.* The answer is therefore not a set choice — both readings were false.
`MUTATION_SUSPECT_NAMES` is **deleted**, and the vocabulary is re-partitioned by *how a name can be
resolved*: `PATH_MUTATION_NAMES` (homonym-free `Path` mutators, matched on attribute name alone) and
`MODULE_MUTATION_NAMES` (matched only through import provenance). Four arms, each decidable from
syntax. Consequences, each stated in writing: `os.replace(a, b)` and `from os import replace as _r;
_r(a, b)` are matched; `s.replace("-", "")` and `frontmatter.copy()` are not; `shutil.*` and
`tempfile.*` are matched by provenance rather than by name and are independently forbidden by Wall C;
and Wall B is widened to collect `from os import <n>` bindings as well as attribute accesses — which
is a better answer than the gates' suggested "widen Wall C to `os`", because `import os` is
legitimate at three live sites for `os.environ` and `os` can therefore only be policed at member
granularity.

**Fold 2 — procedural (D10.6, Task 0, Task 11). The predicates are RUN before the vocabulary is
frozen, and again after routing.** This is the class-level ask both gates made. Task 0 lands the
harness edit FIRST — before a single routing edit exists — and executes every wall against the
untouched tree, pinning nine rows against D10.6 Table 1, including two rows whose expected value is
ZERO and whose purpose is to prove the discriminator (`str.replace`, `dict.copy`). Task 11 re-runs
eleven rows against Table 2 after routing. **A mismatch either time is a hand-back**, with the
vocabulary, the tables and WI-020's battery all named as off-limits repairs. Every finding rounds 4
and 5 produced was reachable by executing one of those rows.

**The door call form, ruled: module attributes.** Every door invocation in D5, D7, D8 and D9 is
`vault_io.<name>(...)`. That keeps `_is_write_call`'s `ast.Attribute` gate — the one part of it four
WI-020 sweeps depend on — completely untouched, so "widened by `DOOR_NAMES`" is genuinely the
one-token edit D7 always claimed. The alternative (an `ast.Name` arm) is rejected in writing: it
changes the node-shape gate and needs its own near-miss battery. And D7 now **derives** the outcome
for `functions_reserializing_parsed_frontmatter`, `functions_parsing_then_writing`,
`non_completed_write_sites` and — new this round — `seam_invocation_closure`'s partition and residue
name-set, clause by clause, rather than predicting it.

**The two contingency write targets are withdrawn.** `tests/test_loud_fail_parse.py` and
`tests/test_loud_fail_write.py` are no longer `## Write Targets` entries at all. The architect was
right that Risk 6's mitigation pointed a caged builder straight at WI-020's shipped acceptance
battery at exactly the moment a red made editing it the cheapest green. With D7's derivations and
Task 11's pins in place, a red there means the derivation is wrong — so the contingency is replaced
by an explicit hand-back, and the cage's own revert is what enforces it rather than prose.

### The next level of the ladder, swept and DECLARED

Above the instances sit three dimensions and one intersection. All are closed in this revision rather
than left for round 6:

1. **Vocabulary collision, swept over the WHOLE vocabulary rather than the two tokens named.** Every
   token of the combined set, run as a call under both roots: filesystem uses are `write_text` (14),
   `mkdir` (2), `rename` (1); non-filesystem uses are `replace` (14 nodes / 9 lines) and `copy` (3
   nodes); **every other token returns zero**, including zero `open(` calls of any mode. Recorded as
   `## Verified Diagnosis` claim 10, and it is what bounds the collision cell to two verbs — and,
   among `Path`'s mutators, to the single name `replace`.
2. **Call form** — whether each predicate's node-shape gate sees the form the design writes. Ruled in
   D7 and re-derived per consuming sweep there.
3. **Universe membership** — whether the routed functions still enter each sweep's universe gate.
   Derived in D7 (1)–(4); the `non_completed_write_sites` clause is the one that decides seven of the
   eight classified `SiteId`s.
4. **The intersection nobody had checked: the effect of the NEW FILE on every existing sweep's file
   set.** `vault_io.py` joins `python_files_under(PACKAGE_ROOT)` for every WI-020 sweep. Derived in
   D1's closing paragraph: it enters none of them, and the `== 4` / `== 3` pins, the residue name-set
   and `modules_using_ast` are all untouched.
5. **And one level above the walls entirely: R11.** The wall's universe is two roots, not the three
   consumer repos — a consumer naming `Path.write_text` against the vault is invisible to every wall
   here by construction. Declared rather than implied.

### Two non-blocking notes, both folded

- **Note #1 — the stat's placement breaks WI-020's no-abort guarantee.** Accepted and corrected. The
  round-5 sketch put `stat_stamp` above the `try`; `base.py:load:186-193`'s loop carries no `try`, so
  a raising stat there aborts the whole vault walk. D5's sketch, D5's per-loader bullets and Task 7
  now all place it as the first statement INSIDE the existing `try` (`base.py:238`, `book.py:64`,
  `meeting.py:70`), still above the first read. The ordering argument is untouched and Wall D(i)'s
  own-body oracle does not care about `try` nesting.
- **Note #2 — D1's no-falsy-return rule was vacuous.** Accepted, and it is the same class as the
  walls: a claim asserted against a predicate that cannot see its subject. `non_completed_write_sites`
  gates on `_is_write_call`, and D2 commits through a file descriptor, so no `vault_io` function ever
  entered that universe. Rather than soften the sentence, the rule gets a real enforcer — **Wall E**,
  `falsy_returns_in(python_files_under(PACKAGE_ROOT), COMMIT_FUNCTION_NAMES) == []`, sharing
  `_own_body_nodes` and `_is_falsy_return` with `non_completed_write_sites` — plus AC-13 and a
  mutate-and-observe probe in Task 12.

### What did NOT change

The frame is untouched, exactly as both round-5 gates asked: layers 1–3, (b) for door 2u, (i) for
door 2c, door 3, the `filelock` and MCP rulings, the shape-defined surface, the three-primitive door-1
shape, D5's (A′) closure and its `== 3` pin argument, Wall D's two halves, the discharged obligations
1–3 and R1's observation-restated clause (c). No new OPEN item; the count stays `OPEN: None`. Task
numbering is unchanged for Tasks 1–15 so no cross-reference in this document drifts; the harness work
moves from Task 11 to a new Task 0 (land and pin the predicates) and Task 11 becomes the post-routing
re-run of the same probe. Two residuals are added — R10 (`Path.replace` on an unqualified receiver,
with its alternative priced) and R11 (the wall's two-root universe) — and Risk rows 12 and 13 record
the build-time and future-writer faces of the same two facts.

## Architectural Review — 2026-08-09

**Recommendation: REVISE — return to exploration** (round 6, cold-start; read against the tree, not
against rounds 1–5's notes. The finding is in `## Design` D7/D8 and the plan they drive; it does not
touch the frame and does not re-raise `#approach`.)

### Trigger check

Unchanged and still firing: new module (`obsidian_schemas/vault_io.py`), >3 files across different
concerns, replaces a core system (every write path), effort > 1 day, and the resulting semantics
become a contract for three consumer repos (`docs/backlog-campaign-2026-07-05.md:95`).

### What round 6 bought — closed, verified, and not to be re-opened

Re-derived against the tree this round rather than read off the doc:

- **Finding 1 (the call form) is closed, and the module-attribute ruling is the right half of the
  fork.** `tests/derivations.py:_is_write_call:189-195` is exactly
  `isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in
  {"write_text", "write_bytes"}` — the `ast.Attribute` gate is real and is a hard gate. Ruling
  `vault_io.<door>(...)` everywhere keeps it a one-token edit, and D7's derivations (1)–(4) are
  correct where I walked them: `_taints_a_write`'s sink loop (`tests/derivations.py:300-304`) matches
  the routed `vault_io.write_note(file_path, new_content, precondition=stamp)` and keeps the four
  `FunctionId`s at `tests/test_loud_fail_parse.py:110-116`; `write_markdown_file` keeps its
  `parse_frontmatter` at `obsidian_schemas/writer.py:197` seeding only `_`, so
  `loose_paths - write_paths == {guard}` at `:137` survives; and the seven non-helper `SiteId`s at
  `tests/test_loud_fail_write.py:128-136` sit in four methods that each keep a matched call in their
  own body (`_get_body_content` rides `_SHARED_HELPERS`, `tests/derivations.py:481`).
  `add_to_discuss_item` carries no falsy return, which is why its absence from that map is correct
  and stays correct.
- **Finding 2 (the vocabulary) is closed, and the provenance partition is the right shape.** I ran
  the discriminating rows rather than reading them: `.replace(` under both roots is fourteen call
  nodes across nine lines — `models.py:110`, `:136`(×2); `book.py:94`, `:124`, `:207`, `:255`(×2
  each); `meeting.py:211`; `person.py:1141`; `lint_vault.py:889` — every one a `str.replace`; and
  `.copy()` is `writer.py:220`, `parser.py:176`, `:211`, every one a dict copy. Table 1's other rows
  hold too: exactly three `os.<attr>` uses, all `environ` (`base.py:97`, `lint_vault.py:52`,
  `migrate_person_to_discuss.py:160`); zero imports of `shutil`/`tempfile`/`fcntl`/`mmap`/`filelock`;
  zero `open(` calls of any mode; two `mkdir` (`writer.py:233`, `lint_vault.py:1034`) and one
  `rename` (`lint_vault.py:1038`).
- **Fold 2 (Task 0) is the right instrument** and D10.6's two tables are the right artifact. Wall E
  and the corrected stat-inside-the-`try` are both correct: `_is_falsy_return`
  (`tests/derivations.py:518`), `_own_body_nodes` (`:148`) and `FunctionId.name` (`:43-45`) all exist
  and compose as D10.4 says, and `base.py:load:186-193` genuinely carries no `try` of its own.
- **The frame.** Layers 1–3, (b) for door 2u, (i) for door 2c, door 3, `filelock`, the MCP and daemon
  rejections, the shape-defined surface, D5's (A′) and its `== 3` pin argument, Wall D's two halves,
  the discharged obligations and R1's observation-restated clause (c) are settled and are **not**
  re-opened here.

### Blocking issue

**D7 derives the routing's effect on WI-020's battery over the four STATIC predicates only, but both
of those modules are half derivation and half BEHAVIOUR — and three behavioural assertions break
against the routed tree. Since round 6 withdrew both modules as write targets and made a red there a
mandatory hand-back, the plan as written aborts the build at Task 4 and AC-10 is unsatisfiable
(`## Design` D7, D8; Tasks 4, 5, 7; AC-10).**

This is LESSONS #42 (`LESSONS.html:723-731`) in its exact stated shape — *"each reviewer checks the
prose against the tree and finds every element individually accurate; the unsatisfiability lives in
the composition, visible only when the enforcing checks actually run"* — and it is the class D10.0
named, one level up from where round 6 closed it: Fold 2 executes the WALL predicates against the
untouched tree and again after routing, but nothing anywhere executes the two acceptance batteries
against a **routed** tree before "neither module needs an edit" is frozen into AC-10 and into the
withdrawal of the two write targets.

Three instances, each verified in code this round:

1. **`tests/test_loud_fail_write.py:149-157` (WI-020 AC-5, P1) — the fault-injection point is the
   call the routing removes.** It does `monkeypatch.setattr(Path, "write_text", … throw(OSError))`
   at `:153` and asserts `repo.append_to_timeline(person, …)` raises `WriteFailedError` at `:155-156`.
   After Task 5, `append_to_timeline` commits through `vault_io.write_note`, and this document has
   committed in writing that `Path.write_text` is **not** on that path: D2 commits through a file
   descriptor (`f.write` / `flush` / `os.fsync(fd)` / `os.replace`), D1's closing paragraph asserts
   `vault_io.py` "contains no `write_text`/`write_bytes`/door call", and Wall E exists precisely
   because "no `vault_io` function enters that universe at all". So no fault is injected, the write
   succeeds, and the assertion is `DID NOT RAISE`. Task 5's own verify names this test by name.
2. **`tests/test_loud_fail_parse.py:440-457` (`test_error_chains_are_bounded`, part 3) — same
   mechanism, different contract.** `monkeypatch.setattr(_Path, "write_text", deny)` at `:450`, then
   `update_frontmatter_field(good, "role", "vip")` must raise `WriteFailedError` with
   `caught.value.__cause__ is boom` at `:451-457`. Task 4 routes that write into
   `vault_io.write_note`; the `OSError` is never raised, and the assertion that a CHAINABLE cause
   survives into `__cause__` stops being exercised at all. Task 4's verify runs this module.
3. **`tests/test_loud_fail_write.py:58-92` (WI-020 AC-4) — door 2's zero case, not the call form.**
   Both halves seed with a raw `path.write_text(...)` (`:63`, `:77`) and then call
   `write_markdown_file(path, entity=entity, body="", overwrite=True)` (`:66`, `:89`), asserting
   `UnverifiableBodyError`. No repository ever loads those paths, so under D8's flow
   `snapshot_stamp(path)` is `None`, step 5's zero case fires on `stamp is None` **regardless of
   `overwrite=True`**, and D8 step 5 says in terms that the WI-126 guard "does not apply (no existing
   body by precondition)". The call raises `NoteAlreadyExists`, and `pytest.raises(
   UnverifiableBodyError)` fails on both halves. This surfaces at **Task 7**, whose verify states
   `tests/test_writer.py` is expected RED "at `test_no_overwrite_by_default:146` **only**; every other
   module GREEN".

Instance 3 also shows the D8(b) sweep is narrower than the break it declares. D8(b) says "In-repo the
only catcher is `tests/test_writer.py:test_no_overwrite_by_default:146-156`" — true as a sweep for
`FileExistsError` *catchers*, and I confirmed it. But the change is not confined to catchers: it
changes the **outcome** of every in-repo `write_markdown_file` call against a path this process did
not load, and two of those live in a module the plan forbids editing. (The WI-126 battery at
`tests/test_writer.py:355-424` is safe by luck rather than by design — its `_seed` at `:358` goes
*through* `write_markdown_file`, so D8 step 8 registers the stamp and the follow-up overwrite takes
the 2u path.)

**Why this is a ruling rather than a builder's judgement.** The three available resolutions are not
equivalent and one of them is consumer-facing:

- (α) Specify the commit so the injected fault still fires — i.e. `vault_io`'s temp write names
  `Path.write_text`. This collides with D2's `os.fsync(fd)` durability requirement (there is no fd to
  sync) and with D1's derivation that `vault_io` enters no existing sweep's universe.
- (β) Re-admit the two modules as write targets and edit the three assertions. This is precisely what
  round 6 withdrew, for the reason the round-5 architect gave; re-admitting it needs to be a written
  reversal, with the edits enumerated ahead of the build rather than discovered at a red.
- (γ) Narrow the zero case so `overwrite=True` against an existing target with no stamp is not a
  create. **Consumer-facing**, and it re-opens the concurrent-create clobber that property 1 exists to
  close — so if it is rejected, reject it in writing.

Nothing here needs a shell, and no live-vault observation changes any of it.

### Suggested adjustments

- In D7, extend the derivation from "which predicates still match" to "which **assertions** still
  hold", and cover the behavioural halves of both modules explicitly — fault-injection points and
  `write_markdown_file`'s outcome against an unstamped path are the two axes the routing moves.
- Rule (α)/(β)/(γ) in writing, with the consumer-facing consequence stated for (γ) as door 2u's and
  2c's already are. If (β) wins, name the three assertions in the plan so a red is *predicted*, and
  reconcile AC-10's "both UNEDITED" and Task 7's "every other module GREEN" with the ruling.
- Extend Fold 2's instrument to match its own class: Task 0 already runs the wall predicates
  pre-routing; the missing half is a task that runs **`tests/test_loud_fail_parse.py` and
  `tests/test_loud_fail_write.py` themselves** against the routed tree and pins the result, rather
  than a derivation asserting they pass (LESSONS #32, `LESSONS.html:608-617`).

### Notes (non-blocking)

1. **D5's "cache and registry cannot diverge" holds for one repository instance per path per
   process, and `write_markdown_file` is exported.** The adoption sweep proves every `_cache` write
   has a matching stamp record; it does not prove the converse. A direct
   `write_markdown_file(P, frontmatter=…, overwrite=True)` — public API at
   `obsidian_schemas/__init__.py:42,115` — takes door 2 and registers a stamp at step 8 that no
   `_cache` adopted, and two `PersonRepository` instances over one vault share the module-level
   registry while holding separate caches. In both, the registry ends up NEWER than a live cached
   entity, so the next `save()` compares equal and passes — the fail-OPEN direction, and the same
   shape as the round-3 note #1 D5 closed for door 1. No in-repo caller does either today (verified:
   the only `write_markdown_file` callers are `base.py:321`, `book.py:163`, `meeting.py:185` and
   tests), so this is a residual to declare, not a redesign.
2. **`read_note`'s error contract is specified only for a missing path.**
   `tests/test_loud_fail_parse.py:462-469` (part 4) depends on a `UnicodeDecodeError` from the read
   surfacing into the routed site's own `except` so the chain stays unbounded. One sentence in D1
   saying `read_note` lets `OSError`/`UnicodeDecodeError` out unwrapped would make that derivable
   rather than incidental.
3. Everything else I spot-checked in `## Design` resolves and means what the doc says: `_called_names`
   (`tests/derivations.py:167-182`) keying attribute calls on `attr` so `vault_io.stat_stamp(p)`
   contributes `stat_stamp` to Wall D(i); `_function_id_of` (`:380-383`) and `_iter_functions`
   (`:122-145`) minting compatible `FunctionId`s; the module's own `ast` single-homing declaration at
   `:14`; and `writer.py:186-187`'s `exists()`-then-`write_text`-at-`:236` gap.

```verdict
gate: architect
verdict: REVISE
date: 2026-08-09
model: claude-opus-5
targets: #design, Task 4, Task 5, Task 7, AC-10
note: Round 5's call-form and vocabulary findings are properly closed and I re-verified both, but D7 derives the routing's effect on WI-020's battery over the four static AST predicates only while both modules are half behaviour — Path.write_text fault injection at tests/test_loud_fail_write.py:153 and tests/test_loud_fail_parse.py:450 stops firing once the commit moves to vault_io's fd path (D1/D2/Wall E all state it does), and AC-4's two raw-seeded write_markdown_file(overwrite=True) calls at tests/test_loud_fail_write.py:66,89 hit D8 step 5's zero case and raise NoteAlreadyExists instead of UnverifiableBodyError — so with both modules withdrawn as write targets a red there is a mandatory hand-back, the build aborts at Task 4, and AC-10's "both UNEDITED" is unsatisfiable.
```

## Data Audit — 2026-08-09

**Recommendation: REVISE — the round-6 architect's class is real and their enumeration of it is
INCOMPLETE. The zero case fires against two more live sites in `tests/test_writer.py` — the module
Task 7 predicts RED "at `test_no_overwrite_by_default:146` **only**" — and one of those two is the
package's own README-documented public read-modify-write recipe, which no consumer-facing ruling in
this document covers.** (Round 6, cold-start; every site below read in the tree this round, nothing
carried from rounds 1–5 or from the round-6 architect.)

Read against the series first, because that judgement is this gate's to make. Rounds 1–3 targeted
`#approach` and were discharged by the conductor sitting. Round 4 targeted `#design`/Task 7/Task
12/AC-7 and closed. Round 5 targeted `#design`/Task 11/Task 12/AC-7/AC-10 and closed — I spot-checked
the fold and it holds: `MUTATION_SUSPECT_NAMES` is gone, the provenance partition is the right shape,
the module-attribute call-form ruling keeps `_is_write_call`'s `ast.Attribute` gate
(`tests/derivations.py:189-195`) a one-token edit, and Task 0 is the right instrument. **The target
has moved every round and this round it moves again**, from the static predicates to the behavioural
half — so this is a converging arc, not a treadmill. It is also round 6, and I say plainly below why
one more round of *enumeration* buys nothing and what actually ends the arc.

### Trigger check

**Class 1 — remains DISCHARGED.** Obligations 1–3 (local journaled APFS, Obsidian's in-place
truncate-and-write at inode `220735514` / `5049 → 5085`, dot-dir sentinel invisible to Obsidian's
filename search) are observed, dated and scope-stated, and R1's clause (c) still carries the negative
result. **No live-vault observation is required to close anything below** — every finding is
tree-grounded.

**Class 2 — fires, over `## Design` D8 step 5's zero case and the corpus it is evaluated against.**
D8(e) states the premise outright: with both halves in place, `stamp is None` means *"nothing in this
process derived an entity from these bytes"* rather than *"nobody remembered to record here"*. That is
a rule-effect-against-the-existing-corpus claim, and it is what Task 7's verify and AC-10 rest on.
Re-run below.

### Grounded this round — the round-6 architect's three instances are all TRUE

I read each rather than inheriting it, because the required grounding turns on how far the class
reaches, not on whether it exists:

- **Instance 1 is real.** `tests/test_loud_fail_write.py:153` does
  `monkeypatch.setattr(Path, "write_text", … throw(OSError(28)))` and `:155-156` asserts
  `repo.append_to_timeline(person, …)` raises `WriteFailedError`. After Task 5 that commit is
  `vault_io.write_note`, and D2's commit is `f.write` / `flush` / `os.fsync(fd)` / `os.replace` — D1's
  closing paragraph and Wall E's whole justification both state in terms that no `vault_io` function
  names `write_text`. The fault is never injected.
- **Instance 2 is real.** `tests/test_loud_fail_parse.py:450` patches `_Path.write_text` and
  `:451-457` requires `WriteFailedError` with `__cause__ is boom` out of
  `update_frontmatter_field(good, "role", "vip")` — routed by Task 4. Same mechanism; the CHAINABLE
  cause contract stops being exercised rather than failing loudly.
- **Instance 3 is real.** `tests/test_loud_fail_write.py:63,66` and `:77,89` seed with a raw
  `path.write_text(...)` and then call `write_markdown_file(path, entity=entity, body="",
  overwrite=True)` expecting `UnverifiableBodyError`. No repository loads either path, so
  `snapshot_stamp` is `None`, D8 step 5 fires on `stamp is None` **regardless of `overwrite=True`**,
  and `create_note` against an existing target raises `NoteAlreadyExists`.
- **And the architect's "safe by luck" note is right.** `tests/test_writer.py:355-424`'s `_seed`
  (`:358`) commits *through* `write_markdown_file`, so D8 step 8 registers the stamp and every
  follow-up `overwrite=True` takes the 2u path. Same for `test_repo_save_raises_on_shrink:426-434`.

I do not re-litigate any of the three. They are folded into the required grounding because the fix is
the same fix.

### Premise vs reality — the zero case reaches two sites nobody has named, and one of them is public API

**The premise.** D8(e): step 5's `stamp is None` means "nothing in this process derived an entity from
these bytes". Task 7's verify freezes the consequence: *"`tests/test_writer.py` is expected RED at
`test_no_overwrite_by_default:146` **only**; every other module GREEN"*, and Task 14 is scoped to that
one line. Run against this corpus, both are false.

**Site A — `tests/test_writer.py:test_overwrite_when_requested:158-179`.** `file_path.write_text(
"original content")` at `:169`, then `write_markdown_file(file_path, frontmatter={…},
overwrite=True, allow_body_replacement=True)` at `:171`, asserting the write lands. Nothing loads that
path and nothing commits it through door 2, so `snapshot_stamp` is `None`. `allow_body_replacement` is
**not** `allow_unverified_overwrite` — D8(d) mints the latter as a separate flag in the shape of the
former, precisely so they stay distinct — so step 4 does not fire and step 5's zero case does, on
`stamp is None`, against an existing target. `NoteAlreadyExists`. RED, and unpredicted.

**Site B — `tests/test_writer.py:test_roundtrip_preserves_data:287-338`, and this one is the finding.**
`file_path.write_text(original_content)` at `:314`, `doc = parse_markdown_file(file_path)` at `:317`,
then `write_markdown_file(file_path, entity=doc.entity, body=doc.body,
extra_fields=doc.extra_fields, overwrite=True)` at `:322`. An entity **is** derived from those bytes,
by the exported parser — and `## Design` D5 rules the derivation corpus to be exactly
`load_file_implementations(...)`, the three `_load_file` functions, "and nowhere else". So the stamp is
`None`, step 5's zero case fires, and `NoteAlreadyExists`. RED, unpredicted, and the premise sentence
in D8(e) is literally false here: something in this process derived an entity from these bytes, and
the door cannot see it.

**Why site B is not a test-shaped defect.** That is not an artificial sequence a test invented — it is
the sequence this package documents. `README.md:317-338`, "Round-Trip Preservation", is
`parse_markdown_file` → mutate → `write_markdown_file(..., overwrite=True)`, verbatim, as the public
recipe for editing a note without a repository. `parse_markdown_file` and `write_markdown_file` are
both exported (`obsidian_schemas/__init__.py:37,42,111,115`). D5 is explicit that the registry is
path-keyed and owned by the write primitive *"so a registry hung on the repository would be invisible
to consumers that bypass repositories entirely"* — but the OBSERVATION half was then given only to the
loaders, so a consumer that bypasses repositories still gets no stamp, and Wall D(ii) pins
"derivation corpus == loader corpus" over `PACKAGE_ROOT`/`SCRIPTS_ROOT` only, which puts every
consumer derivation outside the wall's universe **by construction** (R11's face, on the read side this
time). The net consumer-facing consequence — *the documented read-modify-write against an existing
note now raises `NoteAlreadyExists`* — is stated nowhere. D8(a) rules only the adjacent cell (a bare
`write_markdown_file(path, entity=e)` keeping its create-or-refuse meaning); the "Consumer-facing
consequence, stated plainly" paragraphs under 2u and 2c enumerate repository callers. This item's own
bar is that a semantic change of this size is ruled in writing with its consequence named, as (b) and
(i) both were.

**Why this is one finding and not two.** Sites A and B, and all three of the architect's, are the same
defect: **the plan's claims about which assertions survive routing are derived over static AST
predicates, and every one of them is really a claim about a BEHAVIOUR nobody executed.** The architect
named the class (LESSONS #42) and then enumerated three members; I found two more in the first module
I read, in the module whose expected result Task 7 states most precisely. That is the evidence that
matters: **enumeration is not converging on this class.** Fixing five instances leaves round 7 the
sixth, exactly as fixing `mkdir` left round 5 `replace`, and fixing `replace` left round 6 the
fault-injection points. Round 6's own Fold 2 already contains the right instrument — Task 0 executes
the wall predicates before the vocabulary is frozen — and the missing half is that **nothing executes
the acceptance battery, or the floor, against a routed tree** before "every other module GREEN" is
frozen into a plan and into AC-10.

### Required grounding

Two items. **Neither needs a shell against the live vault; the Class-1 obligations stay discharged.**

1. **Rule the derivation-outside-the-loader-corpus cell, with its consumer face stated as plainly as
   2u's and 2c's.** `parse_markdown_file` → `write_markdown_file(..., overwrite=True)` against an
   existing note is a real, documented, exported pattern (`README.md:317-338`) and today it silently
   succeeds; under D8 step 5 it raises `NoteAlreadyExists`. Say in writing which it is: the exported
   parser becomes an observation point (and Wall D(ii)'s equality is restated over the wider corpus);
   or `allow_unverified_overwrite` is the documented consumer answer and the README is a write target;
   or the cell is ruled a knowing break with the consumer audit named, as D8(b) does for
   `FileExistsError`. The architect's (α)/(β)/(γ) fork sits inside this — (γ) is the same
   "narrow the zero case" lever — so rule them together rather than twice. And carry the ruling into
   `tests/test_writer.py:158-179` and `:287-338` explicitly, because Task 7's "RED at `:146` only" and
   Task 14's one-line scope are both false as written whichever way it goes.
2. **Execute the batteries against a routed tree and pin what they return, exactly as Task 0 does for
   the walls.** Fold 2's instrument stops at the wall predicates; the missing task runs
   `tests/test_loud_fail_parse.py`, `tests/test_loud_fail_write.py`, `tests/test_writer.py` and THE
   FLOOR against the post-routing tree and pins the RED set — a Table 3 alongside D10.6's two — so
   Task 7's "every other module GREEN", Task 14's scope and AC-10's "both UNEDITED" are each measured
   against a run rather than asserted from a derivation. Five instances found by four readers, none of
   whom ran the suite, is the same shape as four wall findings found by nobody running a predicate;
   round 6 already accepted that argument once, and this is the half of it that was not applied.

OPEN questions raised: 2 (at the cap; both are "run it", not "defer it").

```verdict
gate: data-premise
verdict: REVISE
date: 2026-08-09
model: claude-opus-5
targets: #design, Task 7, Task 14, AC-10
note: The round-6 architect's three behavioural breaks are all real and I re-verified each, but their enumeration is incomplete and that is the finding — D8 step 5's zero case also fires at tests/test_writer.py:test_overwrite_when_requested:158-179 (raw write_text seed at :169, then overwrite=True at :171; allow_body_replacement is not D8(d)'s allow_unverified_overwrite) and at test_roundtrip_preserves_data:287-338, where parse_markdown_file:317 DOES derive an entity from those bytes yet records no stamp because D5 rules the derivation corpus to be the three _load_file functions and nowhere else, falsifying D8(e)'s "stamp is None means nothing derived an entity here" and breaking the package's own README:317-338 Round-Trip Preservation recipe with a consumer-facing NoteAlreadyExists that no ruling in this document covers — so Task 7's "test_writer.py RED at :146 only" and Task 14's one-line scope are both false, and the fold is to rule the derivation-outside-the-loader-corpus cell and to RUN the batteries and the floor against a routed tree rather than enumerate a sixth instance next round.
```

## Spec-Writer Round 7 — 2026-08-09

Both round-6 gates are accepted in full; nothing is counter-argued. Every site behind both verdicts
was re-read in the tree this round rather than taken from the verdicts: the two `Path.write_text`
fault injections (`tests/test_loud_fail_write.py:153`, `tests/test_loud_fail_parse.py:450`); the four
raw-seeded overwrite calls (`tests/test_loud_fail_write.py:63,66` and `:77,89`;
`tests/test_writer.py:169,171` and `:314,317,322`); `README.md:317-338`; the exports at
`obsidian_schemas/__init__.py:37,42,111,115`; `BaseRepository.save`'s `overwrite=True` default at
`obsidian_schemas/repositories/base.py:save:299` and the fact that `save` does NOT call
`_ensure_loaded()`; the three package `write_markdown_file` call sites; and
`_writeback_identifier`'s route through `update_fields`
(`obsidian_schemas/repositories/person.py:1214`).

### The class both gates named, and what a fold of it has to look like

The data-premise gate stated it exactly: *the plan's claims about which assertions survive routing are
derived over static AST predicates, and every one of them is really a claim about a BEHAVIOUR nobody
executed.* That is one level above the class round 6 closed. Round 6's Fold 2 gave *predicates* an
instrument (Task 0 runs them before the vocabulary is frozen); it gave *behaviour* none. Two readers
found five instances in one round — three, then two more in the first module the second reader
opened — which is the evidence that a sixth was round 8's finding.

So the fold is not "fix five tests". It is the same structural + procedural pair, one level up:

**Fold 1 — structural: the axes are swept at SOURCE, by their declaring shape (D12.1).** Routing moves
behaviour along exactly three axes — commit-call identity (α), outcome against an unobserved path (β),
create-collision exception type (γ) — and each is swept by grepping the shape that declares
membership over the whole of `tests/`: `setattr(<Path>, "write_text"|"write_bytes", …)` → 2 sites; all
17 `write_markdown_file(` and 8 `.save(` call sites, each READ to establish how its target came to
exist → 4 sites; `FileExistsError` → 1 site. The negative result is stated with the positive one: the
other 20 write sites are green for one of three named reasons, so a shorter enumeration is visibly a
miss rather than a pass.

**Fold 2 — procedural: the batteries and THE FLOOR are RUN against the routed tree, and the complete
red set is pinned (Task 16, D12.3 Table 3b).** This is Task 0's instrument applied to behaviour.
Task 16 edits nothing: it runs `pytest tests -q -rf`, pastes the whole failure summary into the Build
Log verbatim, and compares it to Table 3b — which pins the expected red set at exactly one check.
Every finding round 6 produced was reachable by running that one command.

**And the disposition rule is TOTAL, with a loud fourth branch (D12.4).** R-α → move the injection to
the door; R-β → add `allow_unverified_overwrite=True`; R-γ → `NoteAlreadyExists`; **anything else →
HAND BACK**. The asserted property of every existing check is invariant across every permitted edit,
and a repair that changes what a check PROVES is a hand-back whatever class it looks like. That is
what stops "fix five instances" from becoming "improvise the sixth".

### The rulings, all four written

- **The (α)/(β)/(γ) fork (D12.2).** (α) rejected — naming `Path.write_text` in `vault_io` to preserve
  a patch point costs D2's `os.fsync(fd)` durability and falsifies D1's new-file derivation. (β)
  **accepted, as a written reversal of round 6's withdrawal**, with the licence removed rather than
  restored: four enumerated lines in Table 3a, every asserted property invariant, everything else in
  those two modules a hand-back, and Task 16 measuring the claim. (γ) rejected in writing with its
  consequence stated — `BaseRepository.save` defaults `overwrite=True`, so exempting it exempts
  `create_stub`'s losing write, which is the one door 2c exists for.
- **The derivation-outside-the-loader-corpus cell (D5, "The cell Wall D(ii) cannot reach").** Ruled a
  KNOWING, declared break with its consumer face stated as plainly as 2u's and 2c's:
  `write_markdown_file(existing_unobserved_path, …, overwrite=True)` now raises `NoteAlreadyExists`,
  and the documented answer is `allow_unverified_overwrite=True`. Making the exported parser an
  observation point is rejected in writing — it re-opens the round-3 architect's note #1 one door
  over, because the parser cannot know whether its caller adopted what it returned. `README.md` is
  outside `write_authority`, so its recipe is close-out step 5; the three in-suite twins are Table 3a
  rows 4–6.
- **`allow_unverified_overwrite`'s semantics, corrected (D8(d)).** The previous text said it "bypasses
  step 5–7" *and* that "`allow_body_replacement` is still required separately to drop body content" —
  and those contradict, because step 6 IS the WI-126 guard. Ruled on the second sentence: the flag
  says "I did not read this note", never "I may destroy its body". It bypasses the zero case and the
  registry lookup only; step 6 runs, and step 7 preconditions on an in-lock `stat_stamp`. The escape
  therefore degrades door 2u to door-1 strength rather than to nothing — which is also what makes
  every Table-3a row 3–6 edit property-preserving.
- **`read_note`'s error contract (D1).** It wraps nothing: `OSError` and `UnicodeDecodeError`
  propagate unwrapped, which is what keeps `tests/test_loud_fail_parse.py:462-471` (part 4, the
  non-chaining cause) green with no edit. The round-6 architect's note #2, folded.

### The next level of the ladder, swept and DECLARED (D12.5)

Above the three axes: (1) read-error surfacing — closed by D1's contract, no edit; (2) lock sentinel
directories appearing in every test vault — swept, the only directory-listing assertion in `tests/`
is a SUBSET check at `tests/test_loud_fail_load.py:190`, and `load()`'s glob is `@*.md`; (3)
`mkdir` → `ensure_dir` against `tests/test_vault_path_required.py:265`'s `Path.mkdir` patch — still a
`Path.mkdir` call, still after the guard, no edit; (3a) the NEW FILE entering an existing *acceptance*
sweep, which is D1's intersection asked on the test side —
`tests/test_vault_path_required.py:test_no_implicit_vault_path_defaults:312` rglobs every `*.py`
under both roots, so `vault_io.py` may name no `expanduser`/`Path.home()`/`/Users/` default, folded
into Task 3 as a hard constraint; (4) **new residual R12** — a door-1 write ages the
stamp of a note whose cached entity is still current, so `append_to_timeline` then `save()` refuses;
the in-package instance is safe because `update_fields` re-reads through `_load_file`, and closing it
by making the body writers re-register is rejected as LESSONS #43; (5) **new residual R13** — the
round-6 architect's non-blocking note #1, the fail-OPEN direction of D5's adoption sweep, with no
in-package instance today and a fix that would require a different frame (a payload-keyed stamp).

### What did NOT change

The frame is untouched: layers 1–3, (b) for door 2u, (i) for door 2c, door 3, `filelock`, the MCP and
daemon rejections, the shape-defined surface, the three-primitive door-1 shape, D7's module-attribute
call-form ruling (which the fault-injection fix now *depends* on), D5's (A′) closure and its `== 3`
pin argument, Wall D's two halves, Wall E, D10's provenance partition and both of its tables, the
discharged obligations 1–3 and R1's observation-restated clause (c). No new OPEN item; the count stays
`OPEN: None`. Task ordinals 0–15 are unchanged so no cross-reference drifts; the one new task takes
the free ordinal 16 and is placed physically between Tasks 7 and 8, with the checkbox-order rule
restated at the top of the plan. Two ACs move: AC-10 is restated over BOTH halves of WI-020's battery
(the four derivations AND its own checks passing, with the edit set bounded by Table 3a), and AC-14 is
added for the consumer cell.

**One stale count corrected in passing.** `## Verified Diagnosis` claim 8 said the `.save(` sweep of
`tests/` returns eight calls and named `tests/test_writer.py:432,441`; re-running it this round
returns **ten**, because `:434` and `:440` are calls too. The claim's load-bearing half — that not one
of them is a `BookRepository` or `MeetingRepository`, which is why AC-11 exists — is unaffected, and
both extra calls are classified green in D12.1's β sweep, `:434` under (ii) and `:440` under (i).
Corrected rather than carried, because the β sweep's completeness argument rests on that same
enumeration and a spec cannot cite two different totals for one grep.

## Architectural Review — 2026-08-09

**Recommendation: PROMOTE to architected** (round 7, cold-start; every claim below re-run against
this tree, nothing carried from rounds 1–6's notes.)

### Trigger check

Unchanged and still firing: new module (`obsidian_schemas/vault_io.py`), >3 files across different
concerns, replaces a core system (every write path), effort > 1 day, and the resulting semantics
become a contract for three consumer repos (`docs/backlog-campaign-2026-07-05.md:95`).

### What round 7 bought — closed, RUN rather than read, and not to be re-opened

I did not spot-check the sweeps; I re-executed each one, because the whole subject of rounds 4–6 was
claims asserted against something nobody ran.

- **The α sweep is exact.** `setattr(<Path>, "write_text"|"write_bytes", …)` under `tests/` returns
  exactly two injection points — `tests/test_loud_fail_write.py:153` and
  `tests/test_loud_fail_parse.py:450` — with their two restores at `:157` and `:453`. Table 3a rows 1
  and 2, no more.
- **The γ sweep is exact.** `FileExistsError` under `tests/` returns exactly one site,
  `tests/test_writer.py:152`. Table 3a row 7.
- **The β sweep's 27 sites re-derive cell for cell.** Seventeen `write_markdown_file(` —
  `tests/test_loud_fail_write.py:66,89`; `tests/test_writer.py:111,137,153,171,186,322,358,366,377,
  383,390,397,404,411,423` — and ten `.save(` — `tests/test_repositories.py:644,661,676,693,709,725`;
  `tests/test_writer.py:432,434,440,441`. The round-7 correction to `## Verified Diagnosis` claim 8
  (eight → ten) is right, and every one of the ten is a `PersonRepository`, so AC-11's necessity
  stands.
- **Table 3a's property-invariance holds where I walked it, and for one reason the document does not
  state.** Row 5 is safe because `obsidian_schemas/writer.py:195` gates the ENTIRE WI-126 block on
  `not allow_body_replacement`, so `test_overwrite_when_requested`'s existing
  `allow_body_replacement=True` skips step 6 outright and the `"original content"` seed at `:169`
  never reaches `parse_frontmatter` — the added keyword changes only which branch of step 5 is taken.
  Row 6 keeps the guard and still passes because the round-trip body is preserved. Rows 3 and 4 both
  land in the guard's `except (FrontmatterParseError, OSError, UnicodeDecodeError)` at
  `obsidian_schemas/writer.py:200-209` — the MALFORMED seed at `tests/test_loud_fail_write.py:63` and
  the patched `Path.read_text` at `:87` — so `UnverifiableBodyError` survives the keyword unchanged,
  exactly as D8(d)'s round-7 correction requires.
- **D12.5 item 2's sweep is total, not sampled.** The only directory-listing assertion anywhere under
  `tests/` is `tests/test_loud_fail_load.py:190`, and it is a subset check; the only other vault glob
  is `tests/test_repositories.py:585`'s `@Dave*.md`. A `.obsidian-schemas-locks/` directory moves
  neither.
- **The three predicates D7 and D10 rest on are as described.**
  `tests/derivations.py:_is_write_call:189-195` does gate on `isinstance(node.func, ast.Attribute)`;
  `_called_names:167-182` collects `f(...)` and `x.f(...)` alike and keys the attribute form on
  `attr`; `_own_body_nodes:148-164` skips nested `FunctionDef`/`ClassDef`. So the module-attribute
  call-form ruling is genuinely the one-token edit D7 claims, and Wall D(i) is genuinely indifferent
  to it.
- **The frame.** Layers 1–3, (b) for door 2u, (i) for door 2c, door 3, `filelock`, the MCP and
  single-writer-daemon rejections, the shape-defined surface, D5's (A′) and its `== 3` pin argument,
  D10's provenance partition, Walls A–E and the discharged obligations are settled and are **not**
  re-opened here.

### Review

**Fit:** Harmonizes. `obsidian_schemas/writer.py:write_markdown_file:154` is already the package's
entity-write choke point and already the place a write-boundary invariant hangs — WI-126's guard sits
at `:195-214`, in exactly the position door 2's precondition takes. The new exceptions extend WI-020's
hierarchy rather than forking it, and the one non-obvious integration constraint is pre-empted
(`obsidian_schemas/errors.py:REASONS:88` is closed and `bounded_message:109-120` raises outside it, so
each subclass ships with its literal in the same edit).

**Duplication:** Solve-in-one-place holds and is now checkable rather than asserted. Door 2 is one
physical place that all four `save()` paths reach; `filelock` replaces a hand-rolled reentrancy
counter; `ensure_dir` collapses the two `mkdir` sites rather than exempting them; and Wall A's subject
is capability single-homing, not a call count. The in-package `self.save(` corpus is exactly
`obsidian_schemas/repositories/book.py:317`, `company.py:192` and `person.py:1466`, so the door-2c
consequence set in D9 is complete.

**Boundaries:** Ownership is split and both halves are now derived from the tree — the loader corpus
observes (D5's (A′), enforced by Wall D(i)), the primitive enforces (D8's placement, enforced by
Wall A). The WI-185 question is answered rather than worked around: the derivation read genuinely
exists at `load()`, and the design carries it forward as a stamp instead of reconstructing it at write
time. The WI-021 seam is named at door 2's entry with the correct observation that
`_normalize_address_fields` sits one frame too high to serve books and meetings.

**Determinism boundary (LLM vs code):** No LLM anywhere — stat comparison, lock acquisition and
syscall preconditions. The design consistently prefers *structurally impossible* over *detected after
the fact*: the no-clobber create is a kernel guarantee, not a check, and D12.4's fourth branch makes
the unenumerated disposition fail loud rather than be absorbed by the nearest-looking rule.

**Reversibility:** Three levels, cheapest first, and the cheapest is an env var
(`OBSIDIAN_SCHEMAS_WRITE_GUARD=observe`) with no code change. The genuine irreversibility is semantic —
once three repos catch `StaleEntityWrite`/`NoteAlreadyExists`, removing them breaks them — and the
blast radius is bounded correctly by making the highest-frequency create path land as a *reuse*
(`obsidian_schemas/repositories/person.py:1430-1437`).

**Generalization:** Right level. Shape-defined, not site-defined; the empty delete cell gets no door
but is covered by the unrecognised-kind-is-an-ERROR wall; R10 and R11 bound the walls' reach honestly
rather than overclaiming it.

**Cost & maintenance:** One module, one pure-Python dependency, a widening of `tests/derivations.py`,
and two new test modules. The standing maintenance cost is the five walls, and D10.6's two pinned
tables plus Task 0 / Task 11 are what keep them from silently narrowing.

**Build vs extend vs integrate:** All ruled in writing — extend `write_markdown_file`, integrate
`filelock`, reject the daemon and the MCP route.

**Prior art (outside view):** Converges on the standard answer rather than diverging from it —
temp+fsync+rename is git/sqlite/every editor, per-file advisory `flock` is the standard local-host
exclusion, and an mtime/size precondition re-checked before replace is `If-Match`, vim and VS Code. No
divergence to justify, so the dimension's blocking conditions do not fire, and the one deferred option
(Layer 2's viability) had its probe minted, run and answered.

### Why PROMOTE now, and what it does not do

**Round 7 closes the generator, not a seventh instance.** Rounds 4–6 were three members of one class —
*a claim about the current corpus that nobody executed*. Round 6's Fold 2 gave that class an instrument
for PREDICATES (Task 0). Round 7 gives it the missing instrument for BEHAVIOUR: D12.1 sweeps each axis
by its declaring shape, D12.3 enumerates every permitted edit line by line ahead of the build with its
asserted property invariant, Task 16 RUNS the whole floor and pins the complete red set against
Table 3b, and D12.4's fourth branch makes an unswept red a mandatory hand-back rather than a builder's
judgement call. That is the audit fold: a sixth instance now surfaces as a build-exit with evidence,
not as a silent relaxation of a previous item's shipped property.

**I tried to falsify Table 3b and could not.** The two likeliest escape hatches are (1) a test reaching
door 2 *indirectly* — `create_stub` / `find_or_create_stub` / `resolve_or_create` reach
`self.save(...)` at `obsidian_schemas/repositories/person.py:1466` without ever spelling `.save(` in a
test, and `tests/test_repositories.py`, `test_resolve_or_create.py`, `test_wi126_body_preservation.py`
and `test_identity_index.py` carry ~220 such call sites; and (2) a door-1 write followed by a `save()`
on the same path in one test (residual R12's shape, which is neither α, β nor γ). Both come back green:
`tests/test_wi126_body_preservation.py:52` seeds parseable notes so `create_stub` takes the
reuse branch at `:150,172` and never saves, `:167` creates a fresh name;
`tests/test_resolve_or_create.py:190-224` runs its parity cases against twin vaults, so each is a
reuse or a fresh create; and all ten `.save(` sites in `tests/` are fresh-person saves with no body
writer preceding them.

**This PROMOTE does not un-escalate the item.** U1 is universal and un-epoch-gated, so the
data-premise gate's standing round-6 REVISE holds this item at `exploring` regardless of this verdict.
Round 7 answers that gate's two asks directly — the derivation-outside-the-loader-corpus cell is ruled
with its consumer face in D5 and its in-suite twins are Table 3a rows 5–6, and Task 16 is the "run the
batteries" instrument it asked for — but clearing it is that gate's call, not mine.

**LESSONS #38 is the tiebreak** (`LESSONS.html:678`): a review gate with no declared floor regresses,
because each fix to the checking mechanism creates the next round's attack surface. That is literally
what rounds 4–7 have been — the harness got richer each round and the next round found a defect in the
new machinery. Task 16 IS the declared floor. Folding again against a document this grounded is the
treadmill, not the fix.

**Not to be re-opened by a later gate:** the frame as listed above, D12's three axes and their
disposition rule, Table 3a's edit set, and the R1 verbatim-in-spec requirement.

### Notes (non-blocking) — none forks consumer semantics; all are Design's to fold

1. **The β axis's declaring shape is narrower than the axis it declares, and the gap is discharged by
   prose rather than by a sweep.** The axis is "a door-2 write against a path the registry does not
   observe"; the declaring shape is "every `write_markdown_file(` call and every `.save(` call under
   `tests/`". Every test that reaches door 2 through `create_stub` / `find_or_create_stub` /
   `resolve_or_create` is a member the shape cannot return, and D12.1 discharges the whole class with
   one sentence — reason (iii), "`create_stub`'s own guard calls `self.get(...)`, which runs
   `_ensure_loaded()`". I ran the reachable cases and (iii) holds for all of them, so this is not a
   Table-3b defect. But (iii) has two escape hatches it does not name, and both are real: a note that
   exists on disk and FAILS to parse lands in `_skipped` (`obsidian_schemas/repositories/base.py:223`)
   and is never stamped, so `create_stub` for that name is a zero-case create against an existing file
   — which D9 already rules (the recovery re-read yields no entity, so `NoteAlreadyExists` propagates)
   but D12.1 never lists as a β cell; and a note created on disk *after* `_ensure_loaded()` already ran
   is the same shape. One sentence in D12.1 naming both would give a Task-16 red a Table row instead of
   the fourth branch.
2. **The lock timeout is a bound nobody has seen fire — LESSONS #41** (`LESSONS.html:711`). Risk 4's
   mitigation is "a `10.0`s default timeout that converts a hang into a loud `WriteFailedError`", and
   `## Verification`'s failure table lists it, but no `criteria` fence covers it and Task 13's
   enumeration does not name it (AC-8 covers exclusion, reentrancy and the lock-not-held refusal, not
   the timeout). `OBSIDIAN_SCHEMAS_LOCK_TIMEOUT` makes it a one-line check: hold the lock in one
   thread, set the timeout small, assert `WriteFailedError` in the other.
3. **`COMMIT_FUNCTION_NAMES` and the sentence it enforces disagree at the edges.** D1 states the rule
   as "no function in `vault_io.py` that COMMITS BYTES returns a falsy value" and AC-13 as "commits
   bytes or mints a stamp", but the set also carries `ensure_dir`, which does neither. Harmless — it
   never returns falsy — but Wall E's failure message will be quoting a rule its own set is wider than.
4. **R12's consumer face is thinner than 2u's and 2c's.** `repo.append_to_timeline(p, …)` followed by
   `repo.save(p)` in one process now raises `StaleEntityWrite`, and that is an ordinary consumer
   sequence, not an edge. It is declared with its remedy and it is the fail-safe direction, but unlike
   the other two breaks it gets no "Consumer-facing consequence, stated plainly" paragraph and no Risk
   row of its own — only Risk 3's generic "the new refusals fire more often than expected". Worth
   naming it in close-out step 3's consumer audit alongside the `FileExistsError` break, since the two
   greps are different.

```verdict
gate: architect
verdict: PROMOTE
date: 2026-08-09
model: claude-opus-5
note: Round 6's behavioural finding is closed by a genuine audit fold rather than a seventh instance — D12 sweeps each axis by its declaring shape, Table 3a enumerates every permitted edit ahead of the build with its asserted property invariant, and Task 16 RUNS the floor and pins the complete red set with D12.4's fourth branch making an unswept red a mandatory hand-back; I re-executed the sweeps rather than reading them (α = exactly tests/test_loud_fail_write.py:153 and tests/test_loud_fail_parse.py:450, γ = exactly tests/test_writer.py:152, β = the 17 write_markdown_file and 10 .save sites cell for cell, the only directory-listing assertion tests/test_loud_fail_load.py:190 a subset check, and writer.py:195's gate on not allow_body_replacement making row 5 property-preserving) and could not falsify Table 3b through either likely escape hatch — the ~220 indirect create_stub/resolve_or_create reaches or an R12-shaped door-1-then-save; my four residual findings are Design's to fold and none forks consumer semantics, while U1 keeps the item at exploring on the data-premise gate's standing REVISE regardless of this verdict.
```

## Data Audit — 2026-08-09

**Recommendation: PROMOTE to specced.** (Round 7, cold-start. Every sweep below was RE-EXECUTED
against this tree this round — not spot-checked, not inherited from round 6's verdict and not taken
from the round-7 architect, who ran the same three sweeps independently. Where we agree, we agree
from two runs.)

### Read against the series first, because that judgement is this gate's to make

Rounds 1–3 targeted `#approach` and were discharged by the conductor sitting with Dave. Round 4
targeted `#design`/Task 7/Task 12/AC-7 — closed. Round 5 targeted `#design`/Task 11/Task 12/AC-7/
AC-10 — closed. Round 6 (mine) targeted `#design`/Task 7/Task 14/AC-10, and its finding was one level
up from all of them: *the plan's claims about which assertions survive routing are claims about
BEHAVIOUR that nobody executed.* **The target has moved every round, and this round it does not move
because there is nothing left to move it to — round 7 gave that class the instrument it lacked
instead of enumerating a sixth member of it.** That is the shape of an audit fold, not a treadmill
step, and it is why this verdict is PROMOTE rather than an eighth round.

### Trigger check

**Class 1 — remains DISCHARGED, unchanged.** Obligations 1–3 (local journaled APFS; Obsidian's
in-place truncate-and-write observed at inode `220735514`, `5049 → 5085`; the dot-dir sentinel
invisible to Obsidian's filename search) were observed and dated in rounds 1–4, R1's clause (c) still
carries the negative result, and nothing round 7 added touches them. **No live-vault observation was
required to close anything below** — every finding this round is tree-grounded.

**Class 2 — fires, over `## Design` D12.3 Table 3b**: *"the complete expected floor state at the
Task-16 boundary is exactly one failing check."* That is a rule-effect-against-the-existing-corpus
claim of the purest kind — it predicts what a predicate-plus-routing does to the tests that exist
today — and Task 7's verify, Task 14's scope and AC-10 all rest on it. Re-run below.

### Grounded this round — the three declaring-shape sweeps return EXACTLY the doc's sets

I ran each declaring shape myself rather than reading D12.1's result column.

- **α — `setattr(<Path>, "write_text"|"write_bytes", …)` under `tests/`: exactly 2 sites.**
  `tests/test_loud_fail_write.py:153` (restore at `:157`) and `tests/test_loud_fail_parse.py:450`
  (restore at `:453`). Table 3a rows 1–2, no more. I widened the shape to `open`/`read_text`/`mkdir`/
  `replace`/`rename`/`unlink`/`touch` to test whether the axis was drawn too narrow, and it returns
  two further sites that are correctly **not** α members: `tests/test_loud_fail_write.py:87`'s
  `Path.read_text` patch, which D1's "`read_note` wraps nothing" contract and Table 3a row 4's
  reasoning both cover; and `tests/test_vault_path_required.py:265`'s `Path.mkdir` patch, which
  D12.5 item 3 rules unmoved because `ensure_dir` is still a `Path.mkdir` call after the guard.
  Nothing else in the enlarged shape exists.
- **γ — `FileExistsError` under `tests/`: exactly 1 site**, `tests/test_writer.py:152` inside
  `test_no_overwrite_by_default:146`. Table 3a row 7. (The only other in-tree occurrences are the
  raise and its docstring at `obsidian_schemas/writer.py:180,187`, which Task 7 deletes.)
- **β — 17 `write_markdown_file(` + 10 `.save(` under `tests/`, at exactly the enumerated lines.**
  `tests/test_loud_fail_write.py:66,89`; `tests/test_writer.py:111,137,153,171,186,322,358,366,377,
  383,390,397,404,411,423`; `tests/test_repositories.py:644,661,676,693,709,725`;
  `tests/test_writer.py:432,434,440,441`. **The round-7 correction to `## Verified Diagnosis` claim 8
  (eight → ten) is right**, and the eleventh `.save(` hit in the tree is
  `tests/test_wi126_body_preservation.py:69`, a docstring — correctly excluded, so the count of ten
  is a count of calls and not of grep lines.

**And the two β classifications the architect called "safe by luck" hold when walked rather than
assumed.** `TestBodyShrinkGuard._seed:355-359` commits through `write_markdown_file` at `:358`, so
D8 step 8 registers the stamp and `:366,377,383,397,404,411,423` are all reason (ii) 2u updates.
`test_repo_save_raises_on_shrink:426-434` constructs `PersonRepository(vault)` over a vault created
empty at `:430`, so the auto-load records nothing; `:432` is therefore reason (i) — the zero case IS
the create — and step 8's registration is what makes `:434` a 2u update that still reaches the WI-126
guard and still raises `BodyTruncationError`. `test_repo_save_allow_body_replacement:436-443` is the
same pair at `:440`/`:441`. The asserted property of both is preserved with no edit, which is what
Table 3b needs to be true.

### The round-6 premise, re-run: both required-grounding items are DISCHARGED

1. **The derivation-outside-the-loader-corpus cell is now RULED, with its consumer face stated as
   plainly as 2u's and 2c's** — `## Design` D5, "The cell Wall D(ii) cannot reach". It is a knowing,
   declared break: `write_markdown_file(existing_unobserved_path, …, overwrite=True)` raises
   `NoteAlreadyExists`, `allow_unverified_overwrite=True` is the documented consumer answer, and both
   alternatives are rejected **in writing with their costs named** (making `parse_markdown_file` an
   observation point re-opens the round-3 architect's LESSONS #43 defect one door over, because the
   parser cannot know whether its caller adopted what it returned; narrowing the zero case exempts
   exactly `create_stub`'s losing write, since `BaseRepository.save` defaults `overwrite=True` at
   `obsidian_schemas/repositories/base.py:save:299`). `README.md:317-338` is outside
   `write_authority` and lands as close-out step 5; the three in-suite twins are Table 3a rows 4–6;
   AC-14 is its oracle, and it is the right oracle because D8(d)'s round-7 correction keeps the
   WI-126 guard running under the escape — so the flag degrades door 2u to door-1 strength rather
   than to nothing. This is the ruling I asked for, in the shape I asked for it.
2. **The batteries and THE FLOOR are RUN against the routed tree, and the complete red set is
   pinned** — Task 16, which edits nothing, runs `pytest tests -q -rf`, pastes the whole failure
   summary into the Build Log verbatim, and compares it to Table 3b. This is the half of round 6's
   own Fold 2 argument that had been applied to predicates and not to behaviour.

**And D12.4's fourth branch is what makes the discharge durable rather than a promise.** Rows 1–7 are
what the sweeps returned; a red they did not return is a spec defect and a mandatory hand-back, with
the builder explicitly forbidden to widen R-β or weaken an assertion. So the honest residual — that
some eighth reader could still find a sixth instance — now surfaces as a build-exit with the whole
`-rf` block as evidence, never as a silent relaxation of a previous item's shipped property. **That
is the difference between this round and the last three, and it is the whole reason another round of
enumeration buys nothing.**

### One premise grounded here that no gate had run: D0.1's `filelock` precondition

The only assumption in this document about state outside the source tree. Run against this tree:
`pyproject.toml:26-29` is exactly `pydantic>=2.0.0`, `pyyaml>=6.0` — **no `filelock`** — and this
evidence tree carries no `.venv` at all, so neither half of D0.1's "atomic landing" is in place today.

**This is not a finding, because the document already says so and gates it.** D0.1 states the
dependency "this package does not yet declare", cites `pyproject.toml:26-29` exactly right, names why
the caged builder can fix neither half (`pipeline-runners.yaml:34-38`), and — unusually honest —
states the *limit of its own fence*: the driver probes a precondition path for membership in git
HEAD, `pyproject.toml` is already in HEAD, so the probe passes whether or not the line was added.
Task 1 is therefore ordered first as the real gate, aborts on a failed `import filelock`, and forbids
substituting `fcntl`, editing `pyproject.toml` or running `pip install`; Risk 1 carries it. Grounding
it here converts a declared unknown into a measured one: **the conductor must land both halves before
the worktree is cut, or Task 1 will abort in the build's first minute — as designed.**

### Conclusion

Every empirical claim this spec's correctness rests on is now either observed-and-dated (Class 1,
obligations 1–3), executed-against-this-tree (the three D12.1 sweeps, D1's four-sweep derivation,
D12.5's five declared cells, the `== 3`/`== 4` pins, the `REASONS` count pin), or declared as a
measured gap with a gate that aborts on it (D0.1's `filelock`). The one premise that was asserted
rather than run — Table 3b's red set — now has an instrument that runs it before the build can claim
it, and a disposition rule whose unenumerated branch fails loud.

The premise holds against the real data. PROMOTE.

OPEN questions raised: 0.

```verdict
gate: data-premise
verdict: PROMOTE
date: 2026-08-09
model: claude-opus-5
note: Both round-6 required-grounding items are discharged in the shape asked for — D5's "cell Wall D(ii) cannot reach" rules the consumer derivation cell as a knowing declared break with its consumer face, both alternatives rejected in writing with named costs, and AC-14 as its oracle; Task 16 RUNS the floor and pins the complete red set against Table 3b with D12.4's fourth branch making an unswept red a mandatory hand-back — and I re-executed all three declaring-shape sweeps cold rather than inheriting them, each returning EXACTLY the doc's set (α = 2 sites at tests/test_loud_fail_write.py:153 and tests/test_loud_fail_parse.py:450, and the widened shape's two extra hits at :87 read_text and test_vault_path_required.py:265 mkdir are correctly non-members per D1 and D12.5 item 3; γ = 1 site at tests/test_writer.py:152; β = the 17 write_markdown_file and 10 .save calls line for line, with the eleventh .save grep hit at test_wi126_body_preservation.py:69 correctly excluded as a docstring), plus I walked the two "safe by luck" classifications and both hold — _seed:358 commits through door 2 so :366-:423 are reason (ii), and repo.save at :432/:440 into a vault created empty at :430 is reason (i) whose step-8 registration is exactly what keeps :434/:441 reaching the WI-126 guard; the one premise no gate had run, D0.1's filelock, I grounded here and it comes back as the document already states it (pyproject.toml:26-29 is pydantic+pyyaml only, no .venv in this tree) with Task 1's abort as the real gate and the fence's own limit disclosed — so Class 1 stays discharged, the Class-2 premise is now measured rather than asserted, the target has moved every round and this round has nothing left to move to, and an eighth round of enumeration is the treadmill LESSONS #38 names rather than the fix.
```

## Threat Model — 2026-08-09

**Recommendation: PROMOTE to threat-modeled** (cold-start, first threat-model round on this item.)

### Trigger check

Fired: **persists data to files** (every note in the live vault); **filesystem operations on
user-owned files** (the entire item); **crosses a trust boundary** — the document names it itself at
D0.7, and correctly: the untrusted input is *the filesystem*, i.e. bytes another process or Obsidian
wrote between our read and our write. Did NOT fire: no secrets, no credentials, no OAuth scopes, no
MCP scopes, no network, no outbound API calls, no external messages, no user-supplied strings, no
deserialization of foreign data. The MCP route was considered and rejected in `## Approach`, so no
tool-permission surface is added either.

The review is therefore narrow by construction: this is an integrity item, and the STRIDE categories
that carry weight here are **T** and **I**, with **R** and **D** noted and **S**/**E** empty.

### STRIDE review

**Spoofing — nothing to spoof.** No identity claim, no authentication boundary, no principal. The
lock is advisory and its "holder" is a process, not an identity; R3 already declares that advisory
means advisory. Empty category, stated rather than skipped.

**Tampering — the item's whole subject, and the frame is right.** The three doors' precondition rule
(`## Approach`, "the one rule that closes it") is the correct integrity primitive: a precondition
evaluated *at the write syscall, against the target itself*, with the zero case failing closed.
Verified against the tree: the check-then-mutate gaps it collapses are real and still live —
`obsidian_schemas/writer.py:186-187` guards a write 50 lines later at `:236`, and
`scripts/lint_vault.py:1036` guards `src.rename(dest)` at `:1038` with nothing held between, which
`Path.rename` silently clobbers on POSIX. Replacing both with kernel guarantees (`os.link` /
`O_CREAT|O_EXCL`) is strictly stronger than any check, and the no-clobber create is the right answer
for door 2c and door 3 alike.

Three tampering findings survive that the frame does not yet reach, all inside the new module and
none of which re-opens a ruling. They are M1–M3 below.

- **M3 (symlinked target).** The design keys the lock on `hashlib.sha256(str(path.resolve())…)` (D3)
  and the stamp registry on `str(Path(p).resolve())` (D5), but D2 places the temp file "in the
  target's own directory" and commits with `os.replace(tmp, target)` against the *unresolved* path.
  Those are two different files when the note is a symlink. Nothing in the tree resolves or refuses
  symlinks today (grep for `is_symlink` over `obsidian_schemas/` returns nothing), and today's
  `Path.write_text` follows the link, so this is a behaviour the item would newly introduce rather
  than inherit. The half-resolved/half-unresolved split is the defect, not symlinks as such.

**Repudiation — adequate, one observation.** Every refusal raises a typed `LoudFailError` carrying
its `path`; `observe` mode logs each suppressed refusal at WARNING (D9); `allow_unverified_overwrite`
logs at WARNING naming the path on every use (D8d). That is the security-relevant event set and it is
covered. Non-blocking: there is no audit trail of *successful* writes, which means a lost update
inside R1's µs window leaves no record on our side — but R1 already declares that window irreducible
and an audit log would not close it, so this is noted, not required.

**Information disclosure — one real finding, one pre-existing contract confirmed sound.**

- **M1 (permission mutation).** This is the finding I would not want to discover in production.
  Today every write is `Path.write_text` (`obsidian_schemas/writer.py:236` and the thirteen sibling
  sites), which opens `"w"` and **truncates in place** — the inode survives, so the note keeps its
  existing mode. Layer 1 replaces that with temp-file + `os.replace`, which swaps in a *new* inode
  whose mode comes from how the temp file was created, not from the target. So the item silently
  rewrites the permissions of every note in the vault as a side effect of a change whose stated
  subject is concurrency. Both plausible implementations are wrong in opposite directions, and the
  design contemplates the first: `tempfile.mkstemp` (pinned as a MATCHED shape in D10.5, and
  `tempfile` is a Wall-C module reserved to `vault_io.py`) creates `0600`, so every note narrows and
  a read-only backup or any reader that is not this user silently loses access — the doc's own
  obligation-1 discharge records "the planned backup system is read-only"; a plain `open(tmp, "w")`
  takes the process umask, typically `0644`, so a note deliberately left at `0600` silently widens.
  Person notes carry emails, phones and PII, so the widening direction is a genuine disclosure. There
  is no permission handling anywhere in the package today (grep for `chmod|st_mode|umask` over
  `obsidian_schemas/` returns nothing), so this must be written, not inherited. It is one `os.stat` +
  `os.chmod` pair inside the door, and it is Wall-legal as specced: `chmod` is already in
  `PATH_MUTATION_NAMES` (D10.1) and `vault_io.py` is the one file permitted to name it, while Wall B
  excludes `vault_io.py` from its `os`-member rule — so the mitigation needs no vocabulary change and
  no exemption.
- **Message bounds — confirmed sound, no mitigation required.** I read the contract rather than
  trusting the citation. `obsidian_schemas/errors.py:bounded_message:109-128` builds messages from
  bounded parts only and refuses any reason outside `REASONS:88`; `chainable_cause:187-193` admits
  only `LoudFailError` and `OSError` into `__cause__`, suppressing `UnicodeDecodeError` and
  `MarkedYAMLError` precisely because their `str()` renders note bytes. The three new exceptions
  declare no `__init__` (D11, Task 2), so they inherit that bound by construction — note content
  cannot reach a message or a traceback through them. The one thing that *does* reach the message is
  `path=` (`errors.py:122-123`), and a person note's filename is a person's name; that is a
  pre-existing WI-020 decision applying unchanged here, not a break this item introduces, and I am
  not re-opening it.

**Denial of service — bounded, no mitigation required.** The relevant vectors are all already
answered: lock acquisition has a `10.0`s default timeout converting a hang into a loud
`WriteFailedError` (D3); deadlock is structurally excluded because door 3 is the only two-lock door
and acquires in sorted resolved-path order (D3); the stamp registry is one 3-field tuple per loaded
note with `clear_snapshots()` for tests (D5). Lock sentinels are never reaped, so
`.obsidian-schemas-locks/` grows to one small file per note ever written — disposable by design
(Edge Cases, "Migration / backfill") and not a realistic exhaustion path on a 5,000-note vault. I
note without requiring it that the architect's non-blocking note #2 is the same observation from the
reliability side: the timeout has no `criteria` fence. That is a coverage gap, not a security gap,
and it is Design's to fold.

**Elevation of privilege — empty, with one adjacent note.** No privilege boundary is crossed, no
sudo path, no scope grant. The only capability question is the new runtime dependency: `filelock`
becomes a transitive dependency of HAL9000, exocortex and orchestrator, which is a supply-chain
surface those three inherit without being asked. It is ruled in writing in `## Approach` with its
cost named, `filelock` is pure Python with no native code, and re-litigating it would be exactly the
theoretical-threat over-correction my calibration forbids. Recorded, not blocking.

### Mitigations verified in place — no fence needed for these

1. **Fail-closed on an unobserved path.** D8 step 5's zero case, and property 1 of `## Approach`'s
   total rule ("absence of a stamp is the strictest case, never the loosest"). This is the single
   most important security property in the document and it is already load-bearing, with AC-14 as its
   oracle and D12.2's option (γ) rejected in writing so a later builder cannot buy a green by
   exempting it.
2. **Stat-before-read ordering** (D5): the stamp is deliberately made *older* than the payload, so
   the failure direction is refusal rather than a silent lost update. Correct, and correctly argued.
3. **No-clobber create as a kernel guarantee** rather than a check (D2, D4) — closes every
   generator-B row without a per-site fix.
4. **Message and chain bounds** inherited from WI-020 by declaring no `__init__` (D11, Task 2),
   re-verified in `errors.py` above.
5. **Trust boundary named and its validation named** (D0.7): the boundary is the filesystem, the
   validation is the stat precondition, and nothing crossing it is interpolated into a message.
6. **`allow_unverified_overwrite` is a per-call, named escape that still runs the WI-126 guard**
   (D8d as corrected round 7) — never a module-level default and never `overwrite=True`. A security
   escape that degrades door 2u to door-1 strength rather than to nothing is the right shape.
7. **Fail-loud on bad configuration** for two of the three env vars — `OBSIDIAN_SCHEMAS_WRITE_GUARD`
   and `OBSIDIAN_SCHEMAS_LOCK_TIMEOUT` both raise `WriteFailedError` on an unrecognised value (D6)
   rather than coercing. M2 below is the third var, which was left out of that rule.

### Required mitigations

All three land inside `obsidian_schemas/vault_io.py`, which Task 3 builds; none touches the ruled
frame, none forks consumer semantics, and none requires a vocabulary or wall change.

```mitigation
kind: required
id: M1
desc: Layer 1 must carry the target's existing st_mode onto the temp file before the replace (and use an explicit mode on create), so a note written through any door keeps the permissions it had rather than silently inheriting mkstemp's 0600 or the process umask.
landed: Task 3
```

```mitigation
kind: required
id: M2
desc: OBSIDIAN_SCHEMAS_LOCK_DIR must be validated at first lock acquisition and raise WriteFailedError when it is not an absolute usable directory, exactly as OBSIDIAN_SCHEMAS_LOCK_TIMEOUT and OBSIDIAN_SCHEMAS_WRITE_GUARD already do — never silently resolved against the process CWD.
landed: Task 3
```

```mitigation
kind: required
id: M3
desc: Every door must derive its temp-file directory and its replace target from the SAME resolved path the lock and the stamp registry are keyed on, or refuse a symlinked target with WriteFailedError — never leave a symlink replaced by a regular file while the real target keeps stale bytes.
landed: Task 3
```

### Why these are mitigations rather than a REVISE

Each is a missing enforcement inside a module that does not exist yet, not a gap in the security
model. M2 is the fail-loud rule the document already applies to its other two env vars, applied to
the third. M1 and M3 are both the same shape: Layer 1 changes the *mechanism* of committing bytes
from truncate-in-place to inode-replacement, and two properties that rode for free on the old
mechanism — the file's mode, and the identity of the file a symlink points at — do not ride for free
on the new one. That is a consequence of the ruled frame, not an argument against it. Under WI-128's
fold rule the fences above are the enforceable form and D8's landing check owns them; bouncing a
document this converged for three one-line additions inside an unbuilt module would be the treadmill
step both round-7 gates just declined to take.

### Notes (non-blocking)

1. **`observe` mode is a security-relevant configuration and should be visible when it is on.** R9
   is honest that while `OBSIDIAN_SCHEMAS_WRITE_GUARD=observe` is set, the concurrent-create clobber
   and the silent snapshot overwrite both still happen. A per-refusal WARNING is specced; what is not
   is any signal that the mode is active at all when nothing is colliding, so a consumer can leave it
   set indefinitely and believe the item shipped. One INFO log at first write would close it. Design's
   call, not a requirement.
2. **The lock sentinel directory is a new attack-surface-shaped artifact in the vault**, and
   obligation 3's evidence scope was filename search only. Close-out step 2 already widens the
   observation to full-text and graph, which is the right owner; I note only that if sentinels ever
   move outside the vault via `OBSIDIAN_SCHEMAS_LOCK_DIR`, M2's validation is what stops that path
   from being a silent mutual-exclusion hole.
3. **Close-out step 3's consumer audit should sweep for the permission assumption too** if M1 lands
   as anything other than "preserve exactly" — a consumer or backup script that assumes vault notes
   are `0644` is the same class of break as the `FileExistsError` catcher, and the grep is different.

```verdict
gate: threat-modeler
verdict: PROMOTE
date: 2026-08-09
model: claude-opus-5
note: Triggers fire on filesystem persistence and the filesystem-as-trust-boundary the doc names itself at D0.7, and the frame is the right integrity primitive — precondition at the write syscall against the target, zero case failing closed, no-clobber create as a kernel guarantee rather than a check, and WI-020's message/chain bounds inherited by construction (verified in errors.py:109-193, not taken from the citation); the three findings I raise are all inside the unbuilt vault_io.py and all fall out of one fact the document never states — Layer 1 changes committing bytes from truncate-in-place (Path.write_text at writer.py:236 preserves the inode and therefore the mode) to inode replacement, so the note's permission bits (M1, silently 0600 under mkstemp or umask-wide under a plain open, on a vault of PII-bearing person notes with a read-only backup consumer) and the identity of a symlinked target (M3, the design keys lock and stamp on path.resolve() but commits os.replace against the unresolved path) both stop riding for free, while M2 is simply the fail-loud-on-bad-config rule D6 already applies to its other two env vars applied to OBSIDIAN_SCHEMAS_LOCK_DIR, whose silent CWD-relative resolution would evaporate Layer 2's mutual exclusion without a sound; none re-opens a ruling, forks consumer semantics or needs a wall or vocabulary change (chmod is already in PATH_MUTATION_NAMES and Wall B excludes vault_io.py), so per WI-128 they are fences landed on Task 3 rather than a REVISE of a document two gates just converged on.
```

## Spec Review — 2026-08-09

**Recommendation: REVISE — return to spec writer (gaps to fix)**

Read cold from line 1, against `docs/spec-quality-bar.md`, not against the diff. The frame is not
re-opened and neither is any ruling the round-7 architect listed as closed. Both blocking issues
below are the **same shape**: a decision that exists in the document but is stated on no surface the
caged builder reads.

### Citation verification

All verified ✓ — and verified for MEANING at each site, not only for resolution. Read in the tree
this round rather than taken from the injected drift audit (which proves existence only):

- `tests/derivations.py:_is_write_call:189-195` is exactly
  `isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in
  {"write_text", "write_bytes"}`. The `ast.Attribute` gate is real, so D7's module-attribute
  call-form ruling and `## Verified Diagnosis` claim 6 both hold as written.
- `tests/derivations.py:_own_body_nodes:148-164` does skip nested `FunctionDef`/`ClassDef`, and
  `_called_names:167-182` does collect `f(...)` and `x.f(...)` alike keying the attribute form on
  `.attr`. Wall D(i)'s indifference to the call form (D10.4) is therefore true, not hoped.
- `obsidian_schemas/writer.py:write_markdown_file:154` — `overwrite: bool = False` at `:160`;
  the exists-guard at `:186-187`; the WI-126 block gated on
  `file_path.exists() and overwrite and not allow_body_replacement` at `:195`; the read at
  `:197-199`; the `except (FrontmatterParseError, OSError, UnicodeDecodeError)` at `:200-209`;
  `existing_lines` at `:210-214`; `fm = model_to_frontmatter(entity, extra_fields)` at `:217-218`;
  `frontmatter.copy()` at `:220`; `mkdir(parents=True, exist_ok=True)` at `:233`;
  `file_path.write_text(...)` at `:236`. Every one as the doc states, including the round-7
  architect's Table-3a row-5 argument (the `:195` gate does make `allow_body_replacement=True` skip
  the block outright).
- `obsidian_schemas/errors.py:84` is verbatim "Exactly the twelve literals of the construction table
  below", `REASONS:88` holds exactly twelve, `bounded_message:109-120` raises `from None` outside the
  set, and `"write did not complete"` is a live member at `:96` — so D3's reuse of it for the timeout
  needs no new literal, as claimed.
- `obsidian_schemas/repositories/book.py:_load_file:57` — `try:` at `:64`, read at `:66`,
  `parse_frontmatter` at `:67`, wrong-type `return None` at `:70-71`, `parse_markdown_file` at `:74`,
  entity branch at `:75-76`, broad `except → _note_skip` at `:77-80` whose comment names the no-abort
  guarantee. D5's per-loader line placement is exact.
- `pipeline-runners.yaml:18-19` (`seed_deps: .venv`), `:32-33` (project root absent on purpose),
  `:34-38` (`obsidian_schemas/**`, `tests/**`, `scripts/**`, `docs/**`). D0.1's honesty about its own
  fence's limit is correct.

### Blocking issues

**1. The threat model's three `kind: required` mitigations are folded into nothing — no
`## Mitigation Folds` section exists, and M1/M2/M3's substance appears on zero surfaces.**

The `## Threat Model — 2026-08-09` round is the latest speaking round and lands `M1`, `M2`, `M3`, all
`kind: required`, all `landed: Task 3`. The document carries no `## Mitigation Folds` section and no
`fold` fence anywhere, so the conveyor's D8c rule refuses `→ ready` on mechanics alone. That is the
cheap half. The expensive half is that the fold has nothing to quote yet — each mitigation is absent
from **every** surface that states the behaviour it constrains, so a builder executing Task 3 from
this document builds none of them:

- **M1 (mode preservation).** D2 specifies the whole commit sequence — temp file in the target's own
  directory, `write`, `flush`, `os.fsync(fd)`, close, `os.replace`/`os.link`, parent-dir fsync,
  `.<target>.<pid>.<counter>.tmp` naming, `os.unlink` in a `finally` — and names no `st_mode` step at
  any point. D1's public surface, D6's table, Task 3's work text, Task 3's verify, `## Verification`'s
  failure table and `## Acceptance Criteria` are all silent too. I confirmed the premise rather than
  inheriting it: `obsidian_schemas/writer.py:236`'s `write_text` truncates in place, and
  `grep -rn 'chmod|st_mode|umask' obsidian_schemas/` returns **zero** hits, so mode preservation is
  behaviour this item newly introduces and cannot inherit. As specced, Task 3 ships whichever mode its
  temp-file mechanism happens to produce.
- **M2 (`OBSIDIAN_SCHEMAS_LOCK_DIR` validation).** D6's table gives the other two env vars an explicit
  failure rule — `OBSIDIAN_SCHEMAS_WRITE_GUARD`: "Any other value raises `WriteFailedError` at first
  write — never silently treated as `enforce`"; `OBSIDIAN_SCHEMAS_LOCK_TIMEOUT` (D3): "a non-positive
  or unparseable value raises `WriteFailedError` at first acquisition rather than being silently
  coerced". `OBSIDIAN_SCHEMAS_LOCK_DIR`'s row declares a valid range of "absolute path" and **no
  failure rule at all**, and D3 says only "Overridden wholesale by `OBSIDIAN_SCHEMAS_LOCK_DIR` (an
  absolute path)". A relative value therefore resolves against each process's CWD, two writers key
  sentinels in different directories, and Layer 2's mutual exclusion evaporates with no sound — the
  PASS-by-default-on-empty shape at a precondition that D5's property 1 exists to forbid.
- **M3 (one resolved path per door).** D3 keys the lock on
  `hashlib.sha256(str(path.resolve())...)`, D5 keys the registry on `str(Path(p).resolve())`, and D2
  places the temp file "in the target's own directory" and commits `os.replace(tmp, target)` against
  the unresolved path. Those are two different files for a symlinked note.
  `grep -rn 'is_symlink|resolve\(\)' obsidian_schemas/` returns only two prose comments, so this too
  is newly introduced rather than inherited. The half-resolved/half-unresolved split is stated
  nowhere in D1–D5, so a builder has no instruction to close it.

This is the sweep obligation, not an edit obligation: for each mitigation, the surfaces to close are
enumerable — the `## Design` sentence (D2 for M1 and M3, D3/D6 for M2), D1's public surface where the
contract changes shape, Task 3's work text AND its verify, `## Verification`'s "must fail loudly"
table, and an acceptance oracle (M2 and M3 both produce a `WriteFailedError` that AC-9's "every
refusal is a `LoudFailError` distinguishable from `WriteFailedError`" does not cover; M1 has no
oracle in any existing AC and its property — "a note keeps the mode it had" — is exactly the shape
`## Verification`'s happy-path smoke should assert). Then the `## Mitigation Folds` records can quote
real text: `desc` copied verbatim from the threat-model fences above, `design` the Design sentence
that now carries it, `landed: Task 3`, `work` that task's own work + verify text. Written in the
other order, the fold records would quote sentences that do not exist.

**2. Task 12's verify orders the builder to edit a file `## Scope Boundary` names untouchable and
`## Write Targets` does not declare.**

Task 12's mutate-and-observe probes are "temporarily adding `Path("x").unlink()` to
`obsidian_schemas/parser.py` turns Wall A RED". `## Scope Boundary`'s "Unchanged files — the builder
should not touch these" list opens with `obsidian_schemas/parser.py`, and no `writes` fence declares
it. The other two probes are clean — `obsidian_schemas/repositories/book.py` and
`obsidian_schemas/vault_io.py` are both declared write targets — so this is one file out of three,
which is what makes it a slip rather than a design position.

It matters because of where it lands. Task 12 is the wall task, sitting directly under a rule that a
red is a hand-back and that the vocabulary must not be narrowed; a builder who reaches it and finds
the plan and the scope boundary disagreeing has exactly the judgment call the bar forbids — violate a
named untouchable, or silently drop a verify step and report Task 12 green. Note that relocating the
probe into the scratch fixture directory the same task already builds does **not** work: Wall A's
universe is `python_files_under(PACKAGE_ROOT, SCRIPTS_ROOT)`, so a scratch file is invisible to it by
construction. The fix is to name a file that is already a `## Write Targets` entry under
`PACKAGE_ROOT` — `obsidian_schemas/writer.py` serves, and it is a file Task 7 has already edited by
the time Task 12 runs.

### Non-blocking notes

- **AC coverage for the mitigations, once folded.** M2's and M3's refusals are both
  `WriteFailedError`, which `## Verification`'s failure table already carries rows for in adjacent
  cases ("`write_note` without the lock held", "Lock acquisition timeout"). Two more rows plus one
  `criteria` fence would cover all three mitigations without a new test module — Task 13's
  `tests/test_concurrent_access.py` is the natural home and is already a declared write target.
- **Task 3's verify writes a scratch script whose home is unstated.** "a scratch script that creates a
  note through `create_note`…" — the script and its scratch vault have no declared location. Not the
  WI-238 shape (the verify's oracle is an exception raised live, not persisted state, so nothing is
  erased at the merge boundary that the verify then reports success over), but naming `tmp_path` or a
  `tests/` scratch fixture costs one clause and removes a decision.
- **`## Verification`'s "Must NOT fail" table would be the cheapest home for M1's property.** "A note
  written through any door keeps the mode it had" is a negative check in exactly that table's idiom,
  and that table is already where the round-4 class was pinned.

### Carried-forward notes

Prior rounds' non-blocking notes still open — all of them post-date `## Spec-Writer Round 7`, so none
has had a spec-writer pass yet. Carried by name, none re-deferred silently:

- **Architect round 7, note 1** — the β axis's declaring shape (`write_markdown_file(` / `.save(`
  under `tests/`) is narrower than the axis it declares; the two escape hatches it does not name are a
  note that exists on disk and fails to parse (lands in `_skipped` at
  `obsidian_schemas/repositories/base.py:223`, never stamped) and a note created after
  `_ensure_loaded()` ran. One sentence in D12.1 would give a Task-16 red a Table row instead of the
  fourth branch. Still open.
- **Architect round 7, note 2** — the `10.0`s lock timeout is a bound nobody has seen fire and carries
  no `criteria` fence (AC-8 covers exclusion, reentrancy and the lock-not-held refusal, not the
  timeout). Still open; the threat model's DoS paragraph independently names it as "a coverage gap,
  not a security gap, and it is Design's to fold".
- **Architect round 7, note 3** — `COMMIT_FUNCTION_NAMES` carries `ensure_dir`, which neither commits
  bytes nor mints a stamp, so Wall E's failure message quotes a rule its own set is wider than. Still
  open.
- **Architect round 7, note 4** — R12's consumer face is thinner than 2u's and 2c's:
  `repo.append_to_timeline(p, …)` then `repo.save(p)` in one process now raises `StaleEntityWrite`,
  and that is an ordinary consumer sequence with no "Consumer-facing consequence, stated plainly"
  paragraph and no Risk row of its own. Still open.
- **Threat model, note 1** — `observe` mode is a security-relevant configuration with no signal that
  it is active when nothing is colliding, so a consumer can leave it set indefinitely and believe the
  item shipped. One INFO log at first write closes it. Still open.
- **Threat model, note 2** — if sentinels ever move outside the vault via
  `OBSIDIAN_SCHEMAS_LOCK_DIR`, M2's validation is what stops that path being a silent mutual-exclusion
  hole. Rides with blocking issue 1; recorded separately because it is the reason M2's fold cannot be
  satisfied by a bare type check.
- **Threat model, note 3** — close-out step 3's consumer audit should sweep for the permission
  assumption too if M1 lands as anything other than "preserve exactly"; the grep is different from the
  `FileExistsError` one. Still open, and it becomes actionable only once M1 is folded.

### On the series — this is a fold round, not an eighth treadmill step

Recorded because the arc matters and this is the first `spec-reviewer` contact. Rounds 1–3 targeted
`#approach`/`#intent` and were discharged from outside the cage; rounds 4–6 were three members of one
class (*a claim about the current corpus nobody executed*) which round 7 closed with an instrument
rather than a seventh instance; both round-7 gates PROMOTE'd on that fold, and the threat modeler then
spoke for the first time and landed three fences under WI-128 rather than bouncing the document. My
targets are those three fences and one plan-task slip — a target no prior round could have raised,
because the fences did not exist until the round that created them. Nothing here re-raises a closed
objection, and I am not proposing an audit fold: the remaining work is bounded, enumerated above, and
the surfaces to close are listed rather than left to be rediscovered.

```verdict
gate: spec-reviewer
verdict: REVISE
date: 2026-08-09
model: claude-opus-5
targets: M1, M2, M3, Task 3, Task 12, #design
note: The threat model's three kind:required mitigations are folded into nothing — there is no `## Mitigation Folds` section (so D8c refuses `→ ready` mechanically) and, worse, M1/M2/M3's substance appears on zero surfaces a caged builder reads: D2 specifies Layer 1's whole commit sequence with no st_mode step, D6 gives OBSIDIAN_SCHEMAS_LOCK_DIR a valid range but no failure rule while its two sibling env vars each get an explicit raise, and D3/D5 key the lock and the registry on path.resolve() while D2 commits os.replace against the unresolved path — all three verified as newly-introduced rather than inherited (grep for chmod|st_mode|umask|is_symlink over obsidian_schemas/ returns nothing, and writer.py:236's write_text truncates in place), so Task 3 as written builds none of them and the fold records would have no real sentence to quote; separately Task 12's verify orders a temporary edit to obsidian_schemas/parser.py, which `## Scope Boundary` names untouchable and no writes fence declares, leaving the builder a judgment call at the wall task between violating a named untouchable and silently dropping a verify.
```

## Spec-Writer Round 8 — 2026-08-09

Both blocking issues closed, both class folds written rather than the four instances patched, the
next level of each ladder swept and DECLARED, and every carried-forward note either folded or
counter-argued by name. Nothing in the frame moves; no ruling any prior gate closed is re-opened.

### Blocking issue 1 — the three mitigations, folded as TWO classes rather than three instances

The reviewer's diagnosis was exact: the fences existed, the substance appeared on no surface a caged
builder reads, and a fold record written first would have quoted sentences that did not exist. So the
surfaces came first and the records second. What is now on each surface:

| Surface | M1 | M2 | M3 |
|---|---|---|---|
| `## Design` sentence | D2.2 | D3, restated in D6's table | D2.3 |
| D1's public surface | property 1 of the new "two properties" block | D6's `_env_setting` rule | property 2 of the same block |
| Task 3's work text | the `(M1)` clause | the `(M2)` clause | the `(M3)` clause |
| Task 3's verify | check (ii) | check (iii) | check (iv) |
| `## Verification` failure table | mode-carry `OSError` row, `st_nlink > 1` row | lock-dir row, timeout row | symlinked-`move_note` row |
| `## Verification` "Must NOT fail" | the mode row | the configuration-surface row | the symlinked-write row |
| Acceptance oracle | AC-15 | AC-16 | AC-17 |
| Fold record | `## Mitigation Folds — 2026-08-09` | same | same |

**But three fences is not three folds, and closing the three in front of me would have left the next
member as round 9's finding.** The threat modeler states the generator itself in its "why these are
mitigations" paragraph, and taking it at its word is what makes this a fold:

1. **Generator A — inode replacement stops supplying inode-borne properties for free** (M1 and M3 are
   two members). Closed in **D2.1** by enumerating EVERY inode-borne property of a vault note and
   ruling each cell, not by handling the two that were named. That enumeration produced a third
   member no gate had raised: a target with `st_nlink > 1`, where a replace leaves the other hard
   links on the OLD bytes while today's truncate-in-place updates all of them. It is now a
   `WriteFailedError`. The remaining cells — ownership, xattrs/ACLs/Finder tags/flags, and the inode
   number — are ruled as **R14** with a reason each, rather than left unmentioned. *Next level swept
   and declared:* directory-entry and parent-directory properties (D2.1's closing paragraph), four
   cells, none needing a rule and all four stated so their absence is a finding rather than a gap.
2. **Generator B — a validity rule stated once per item over an enumerable configuration surface,
   with the enumeration left to the author's memory** (M2 is one member; the surface had three).
   Closed in **D6** by a rule the shape of the code makes total: `vault_io.py` reads `os.environ` in
   exactly ONE private helper, every setting is a call of it, and a setting added later either routes
   through the helper and inherits the rule or duplicates a capability inside the file Wall B
   excludes — which Task 3 forbids in writing. Adding a third per-var clause would have been the
   instance. *Next level swept and declared:* each setting's CASES — unset, empty string, valid but
   hostile, and read timing — four cells, of which empty-string is the one that changes behaviour and
   is folded into the rule.

`## Verified Diagnosis` claim 13 grounds the premise both generators rest on, re-run against this
tree rather than inherited: `grep -rn 'chmod\|st_mode\|umask\|is_symlink\|st_nlink\|listxattr'
obsidian_schemas/ scripts/` returns zero hits, so none of this is a change to existing handling.

**No vocabulary, wall or Table edit was needed, and that is derived rather than asserted.** `chmod`
is already in `PATH_MUTATION_NAMES` so `os.chmod(tmp, mode)` is arm (a) and legal only in
`vault_io.py`; `os.stat`/`os.lstat` are `os` members Wall B polices at member granularity while
excluding `vault_io.py`; every added call lives in the one file Wall A's result set is defined to
contain. D10.6's Table 1 and Table 2 are therefore untouched, and Task 3 says in writing not to edit
`tests/derivations.py`.

### Blocking issue 2 — Task 12's Wall-A probe

`obsidian_schemas/parser.py` → `obsidian_schemas/writer.py`. The reviewer's reasoning is adopted
whole, including why relocating the probe into the scratch fixture directory does not work (Wall A's
universe is `python_files_under(PACKAGE_ROOT, SCRIPTS_ROOT)`, so a scratch file is invisible to it by
construction). And the fix is generalised rather than swapped one-for-one: Task 12 now states as a
RULE that every probe target is a declared `## Write Targets` path inside the wall's own universe,
and names all three, so the next probe added to that task cannot reintroduce the same slip. No
`## Write Targets` fence changes — `obsidian_schemas/writer.py` is already one (Tasks 4 and 7).

### The carried-forward notes, each closed by name

None re-deferred silently. All seven post-dated `## Spec-Writer Round 7`, so this is their first
spec-writer pass.

- **Architect round 7, note 1** (β axis's declaring shape narrower than its axis). **Folded** in
  D12.1: both escape hatches named — a note that exists and fails to parse (lands in `_skipped` at
  `obsidian_schemas/repositories/base.py:223`, never stamped) and a note created after
  `_ensure_loaded()` ran — and RULED as R-β rather than D12.4's fourth branch, with the Build Log
  recording which of the two it was. Neither has an instance in `tests/` today, which is why the
  sweep returned four sites and not six.
- **Architect round 7, note 2** (the `10.0`s timeout is a bound with no `criteria` fence).
  **Folded** into AC-16 rather than into a fence of its own, because the note and M2 are the same
  configuration surface seen from two sides: AC-16 asserts the whole surface — every var's invalid
  values, every var's unset default, and a `0.05`s timeout firing against a held lock — which is
  generator B's rule with an oracle instead of generator B's rule plus one extra criterion.
  `## Verification`'s timeout row now names AC-16 as its oracle.
- **Architect round 7, note 3** (`COMMIT_FUNCTION_NAMES` carries `ensure_dir`, so Wall E's message
  quotes a rule its set is wider than). **Folded** in D1 by restating the RULE to match the set —
  the module's path-, payload- and stamp-returning surface — and AC-13's `desc` with it. Narrowing
  the set to make the old sentence true is rejected in writing as the same move D10.3 forbids at
  Wall A.
- **Architect round 7, note 4** (R12's consumer face thinner than 2u's and 2c's). **Folded** in
  D12.5 item 4, which now carries a "Consumer-facing consequence, stated as plainly as 2u's and 2c's"
  paragraph naming the exact one-process sequence, plus **Risk row 17** and **close-out step 3c**.
  The point the note was making is now stated: unlike the other two breaks, this one needs no second
  writer, which makes it the most likely to be met first.
- **Threat model, note 1** (`observe` is invisible when nothing collides). **Folded** into D6's table,
  D9 and Task 10: one INFO line at the first write of a process whose mode is `observe`, naming the
  mode and the env var — one line per process, not per write, so it cannot become filtered noise.
  Task 10's verify captures it through `tests/support.py:captured_logs:91` at `level=logging.INFO`.
  *(Line suffix corrected round 9 — the symbol is at line 91, `:91-111`; the citation resolved either
  way, so this is a re-anchoring, not a drift fix.)*
- **Threat model, note 2** (sentinels outside the vault ride on M2's validation). **Folded** with M2:
  D3's M2 paragraph names it explicitly as the reason the check is a usable-directory check and not a
  bare type check.
- **Threat model, note 3** (close-out step 3 should sweep for the permission assumption too).
  **Folded**: close-out step 3 is now three sweeps with three different greps — 3a the
  `FileExistsError` catchers, 3b the permission assumption, 3c R12's sequence — and 3b says to record
  the result even when it is empty, because an unrecorded empty sweep is indistinguishable from an
  unrun one.

### The reviewer's non-blocking notes

- **AC coverage for the mitigations.** Done as AC-15/16/17, all three homed in
  `tests/test_concurrent_access.py` (already a declared write target), no new module.
- **Task 3's scratch script had no declared home.** Removed rather than located: Task 3's verify is
  now four zero-argument top-level checks authored into `tests/test_concurrent_access.py`, each
  taking its scratch vault from `tests/support.py:temp_dir:31` — the shape
  `tests/test_loud_fail_write.py:52-55` already uses for a zero-arg check — so the home is declared
  in the test and removed on exit, and nothing is written outside `write_authority`.
- **The "Must NOT fail" table as M1's home.** Adopted, and widened: that table now carries the mode
  row, the symlinked-write row and the configuration-surface row, and the happy-path smoke asserts
  mode equality across all five of its steps as the positive half.

### What did NOT change

The frame, all three doors, the total precondition rule and its zero case, the derived loader corpus
and Wall D, the provenance-partitioned vocabulary and R10, D8(d)'s round-7 correction, the two
WI-020 acceptance modules' narrow re-admission and Table 3a's seven rows, Table 1 and Table 2, every
`## Write Targets` fence, and every ruling `## Scope Boundary` records. Three new residuals-adjacent
entries were added — R14 in `## Approach`, Risk rows 16 and 17, and three Scope Boundary bullets
fencing off the R14 cells — and no existing residual, risk or boundary was weakened.

## Threat Model — 2026-08-09

**Recommendation: PROMOTE to threat-modeled** (round 2 — a re-review of my own round-1 fences after
`## Spec-Writer Round 8`. Per WI-144 this round re-emits my FULL set; a later declaration supersedes
an earlier one, so all three ids reappear by design.)

### Trigger check

Unchanged and still firing, for the same three reasons: **persists data to files** (every note in the
live vault); **filesystem operations on user-owned files** (the whole item); **crosses a trust
boundary**, which the document names itself at D0.7 — the untrusted input is the filesystem, i.e.
bytes another process or Obsidian wrote between our read and our write. Still NOT firing: no secrets,
no credentials, no OAuth or MCP scopes, no network, no outbound calls, no external messages, no
user-supplied strings, no deserialization of foreign data. **S** and **E** remain empty categories;
**T** and **I** carry the weight; **R** and **D** are noted.

### What round 8 landed, re-verified rather than read

I did not take the fold table in `## Spec-Writer Round 8` at its word. Each mitigation was re-read on
every surface it claims, and the premise both generators rest on was re-run against this tree:
`grep -rn 'chmod|st_mode|umask|is_symlink|st_nlink|listxattr|O_EXCL|fchmod' obsidian_schemas/`
returns **zero** hits, and `obsidian_schemas/writer.py:236` is still
`file_path.write_text(content, encoding="utf-8")` with `:233`'s `mkdir` and the three sibling
`write_text` calls at `:283,333,365`. So mode, symlink and hard-link handling are all behaviour this
item newly INTRODUCES, exactly as D2.1 and `## Verified Diagnosis` claim 13 state. I also re-read
`obsidian_schemas/errors.py` rather than the citation: `:84` is verbatim "Exactly the twelve literals",
`REASONS:88` holds twelve with `"write did not complete"` live at `:96`, and `bounded_message:114-120`
raises `from None` outside the set — so M2's "mint no new literal" and the three new subclasses'
inherited message bound both still hold.

**Round 8 did the right thing with M1 and M3: it folded the GENERATOR, not the two instances.** D2.1
enumerates every inode-borne property of a vault note and rules each cell, and that enumeration
produced a member no gate had raised — a target with `st_nlink > 1`, where a replace leaves the other
hard links on the OLD bytes while today's truncate-in-place updates all of them. Refusing it with
`WriteFailedError` is the correct shape and I am not re-opening it. Likewise M2's fold is the rule
(`_env_setting` as the module's ONE `os.environ` access) rather than a third per-var clause, which is
what makes the configuration surface total instead of enumerated-from-memory. My round-1 note 1
(`observe` invisible when nothing collides) landed as the one-INFO-line-per-process signal I asked
for; note 2 landed inside M2's own paragraph; note 3 landed as close-out step 3b with its own grep and
the "record the result even when it is empty" clause. All three are closed to my satisfaction.

### The two findings, and both are MY under-specification rather than a producer miss

This matters for how the series reads, so it is stated plainly: the spec-writer implemented my two
descs literally and correctly. What moved is what the mitigations REQUIRE, because I wrote each one
against the property I was protecting and named a boundary one step too late. Neither finding
re-opens a ruling, forks consumer semantics, or needs a vocabulary, wall or Table edit; both are one
line inside `obsidian_schemas/vault_io.py`, which does not exist yet.

**Finding 1 — M1's window: the design carries the mode across AFTER the note's bytes are already on
disk, and its own justification addresses the wrong threat.** D2 orders the commit as "write the
bytes, `flush`, `os.fsync(fd)`, close, carry the mode across, then link or replace", and D2.2
implements the carry as `os.chmod(tmp, os.stat(target).st_mode & 0o7777)` "before the replace". So
for the whole span of the write and the `fsync` — which is not microseconds under load — a file
holding the complete content of the note exists at the umask-derived mode `os.open(..., 0o666)` gave
it. For a note deliberately left at `0600`, that is precisely the silent widening M1 was minted to
prevent, relocated from the committed note to its temp file. D2.2 anticipates a window and rules it
out with: *"The temp file is dot-prefixed, pid- and counter-unique and exists only inside the lock, so
there is no window in which another WRITER can see the file whose mode is being set."* That argument
is sound and it is about **integrity**; M1's entire justification is **confidentiality** (person notes
carry emails, phones and PII), and a reader is not excluded by a write lock, a dot prefix or a unique
name. The fix is not a new mechanism: the door already holds the target's mode inside the lock before
it opens the temp file, so applying it to the descriptor (`os.fchmod(fd, mode)`, or the mode argument
of the `os.open` that already exists) before the first write closes the window entirely and deletes
the later `os.chmod` rather than adding a call. AC-15 does not catch this today — it asserts the
mode of the *committed* note, which is correct under both orderings.

**Finding 2 — M3's rule reaches the lock's KEY but not the lock's HOME, and the gap loses mutual
exclusion silently.** D2.3 enumerates what the one resolved path governs — "the lock key, the
stamp-registry key, the temp file's directory `target.parent`, the `stat_stamp` precondition and the
terminal `os.replace`/`os.link` argument" — and D1's property 2 says `note_lock` keys on it. But the
sentinel is specified in D3 (round-5 text, written before M3 existed) as
`<note's directory>/.obsidian-schemas-locks/<h>.lock`, and only `<h>` is stated as derived from
`str(path.resolve())`. `<note's directory>` is not. So two processes reaching one real note by two
different paths — a symlink in directory A and the real file in directory B — compute the SAME hash
and then place it in TWO different sentinel directories, take two different locks, and both proceed.
That is the identical failure mode M2's own paragraph names as unacceptable — *"key two writers'
sentinels in different directories and evaporate Layer 2's mutual exclusion with no sound"* — arrived
at from the other direction, and no acceptance criterion sees it: AC-17 is single-process and asserts
where the bytes land, AC-8 asserts exclusion but not through a symlink. The fix is to say that the
sentinel's DIRECTORY is `target.parent` (or, under `OBSIDIAN_SCHEMAS_LOCK_DIR`, the one configured
home, where the question does not arise) — the same sentence D2.3 already writes for the temp file.

### Why these are re-emitted fences and not a REVISE

Both live inside a module Task 3 builds and neither is a gap in the security model: the frame, the
total precondition rule, the zero case, the three doors and D2.1's cell-by-cell ruling all stand
unchanged and are not re-opened. Under WI-128 the enforceable form is a fence, and D8's landing check
owns the fold — routing one spec-writer pass rather than the full-cycle bounce. Round 8 is a genuine
fold round on a document two gates have already converged on, and bouncing it for two one-line
ordering constraints inside unbuilt code would be the treadmill step, not the fix.

**These two `desc` values are NOT cosmetic edits and the producer-fix round they cost is earned.**
What each mitigation requires has moved: M1 now names the ordering (mode on the descriptor before any
bytes), M3 now names the sentinel's directory alongside its key. M2 is re-emitted **byte-identical**,
because nothing about it moved.

### Mitigations verified in place — no fence needed for these

1. **Fail-closed on an unobserved path** — D8 step 5's zero case and property 1 of `## Approach`'s
   total rule, with AC-14 as its oracle and D12.2 option (γ) rejected in writing so a later builder
   cannot buy a green by exempting it. Still the single most important security property here.
2. **Stat-before-read ordering** (D5) — the stamp is deliberately older than the payload, so the
   failure direction is refusal rather than a silent lost update.
3. **No-clobber create as a kernel guarantee** rather than a check (D2, D4).
4. **`st_nlink > 1` refused** (D2.1, round 8) — a divergence with no correct answer, made loud.
5. **Message and chain bounds** inherited by declaring no `__init__` (D11, Task 2), re-verified in
   `obsidian_schemas/errors.py:109-128` this round.
6. **`allow_unverified_overwrite` degrades door 2u to door-1 strength, not to nothing** (D8d).
7. **Fail-loud on bad configuration over the WHOLE surface** — D6's `_env_setting` rule, AC-16.
8. **`observe` announces itself once per process** (D6, D9, Task 10) — my round-1 note 1, closed.

### Notes (non-blocking)

1. **R14 files ACLs under "editor and Finder metadata, not vault data", and an ACL is not metadata.**
   D2.1's cell for extended attributes sweeps `xattrs, ACLs, macOS Finder tags, file flags` together
   and declares them all unpreserved. Finder tags and flags are metadata; a macOS ACL
   (`com.apple.system.Security`) is an access-control decision, and dropping it on inode replacement
   widens access in exactly the direction M1 exists to narrow — silently, with the write reporting
   success. I am **not** requiring it: no note in an Obsidian vault normally carries an ACL, copying
   ACLs from Python is genuinely awkward, and a theoretical threat with no realistic path here is
   what my calibration forbids me to block on. But if it is ever wanted, the cheap answer is the
   shape D2.1 already chose for hard links — `os.listxattr(target)` naming the ACL xattr → refuse —
   not a copy. Worth one clause in R14 distinguishing the two so a later reader does not read
   "metadata" as settled.
2. **A sentinel home in a shared directory would move the lock into someone else's reach.** If
   close-out step 2 finds sentinels surfacing in Obsidian and `OBSIDIAN_SCHEMAS_LOCK_DIR` is set, the
   value should be a user-private directory rather than a world-writable one — in a shared home,
   another principal can hold the sentinel (a bounded DoS, loud via the timeout) or pre-place a
   symlink at the sentinel path. M2 validates absolute-and-usable, which is the right check for the
   failure mode M2 exists for; this is a deployment-time choice for close-out step 2, not a rule for
   the door.
3. **`move_note` still has no external-writer detection (R4), and round 8 did not change that.**
   Noted only to confirm it is still correctly declared rather than newly reachable: door 3's payload
   is an inode, its destination has no derivation read, and the quarantine caller's per-file `try` at
   `scripts/lint_vault.py:896-897` isolates a refusal. No mitigation.
4. **No audit trail of SUCCESSFUL writes** — unchanged from round 1. A lost update inside R1's µs
   window leaves no record on our side, and an audit log would not close it. Noted, not required.

```mitigation
kind: required
id: M1
desc: Layer 1 must apply the target's existing st_mode to the temp file's OWN DESCRIPTOR before any note bytes are written to it (and create with an explicit mode, never mkstemp's 0600 nor a bare umask-wide open), so a note keeps the permissions it had AND its content never exists on disk at a wider mode than the target's, not even for the span of the write and fsync.
landed: Task 3
```

```mitigation
kind: required
id: M2
desc: OBSIDIAN_SCHEMAS_LOCK_DIR must be validated at first lock acquisition and raise WriteFailedError when it is not an absolute usable directory, exactly as OBSIDIAN_SCHEMAS_LOCK_TIMEOUT and OBSIDIAN_SCHEMAS_WRITE_GUARD already do — never silently resolved against the process CWD.
landed: Task 3
```

```mitigation
kind: required
id: M3
desc: Every door must derive its temp-file directory, its replace target AND its lock sentinel's own DIRECTORY from the same resolved path the sentinel hash and the stamp registry are keyed on, or refuse a symlinked target with WriteFailedError — never leave a symlink replaced by a regular file, and never let two paths naming one real note key their sentinels in two directories.
landed: Task 3
```

```verdict
gate: threat-modeler
verdict: PROMOTE
date: 2026-08-09
model: claude-opus-5
note: Round 8 folded my three round-1 fences as the two GENERATORS rather than the three instances (D2.1 enumerates every inode-borne property and its sweep produced the st_nlink cell no gate had raised; D6's _env_setting makes the config surface total), all three of my non-blocking notes landed including the one-INFO-line observe signal, and I re-ran the premise rather than reading it (grep for chmod|st_mode|umask|is_symlink|st_nlink|listxattr over obsidian_schemas/ returns zero, writer.py:236 is still a bare write_text, and errors.py:84-128 confirms the twelve-literal set, the live "write did not complete" member and the from-None bound) — so the frame stands and I re-emit rather than bounce; the two descs that move are MY under-specification, not a producer miss: M1 said "before the replace" and the design complies literally, which leaves the full note content sitting at the umask-derived temp mode across the write and the fsync while D2.2's own no-window argument reasons about another WRITER when M1's whole justification is a READER of PII-bearing person notes, closed by fchmod-ing the descriptor before the first byte and deleting the later chmod; and M3 named the lock KEY but not the lock HOME, so D3's <note's directory>/.obsidian-schemas-locks/<h>.lock computes one hash and places it in two directories when a symlink and its real file are reached from different parents — two locks, both acquired, which is verbatim the "evaporate Layer 2's mutual exclusion with no sound" failure M2 exists to prevent, and which neither AC-17 (single-process) nor AC-8 (no symlink) can see.
```

## Spec Review — 2026-08-09

**Recommendation: REVISE — return to spec writer (gaps to fix)**

Read cold from line 1 against `docs/spec-quality-bar.md`, not against the diff. The frame is not
re-opened; no ruling any prior gate closed is re-raised. Blocking issue 1 is the direct consequence of
the round-2 threat model, which speaks AFTER `## Spec-Writer Round 8` and moves two of the three
requirements that round folded. Issues 2 and 3 are targets no prior round has raised.

### Citation verification

All verified ✓ — read in the tree this round for MEANING, not taken from the injected drift audit
(which proves existence only):

- `obsidian_schemas/writer.py:write_markdown_file` — the exists-guard at `:186-187`, the WI-126 block
  gated on `file_path.exists() and overwrite and not allow_body_replacement` at `:195`, the read at
  `:197-199`, `except (FrontmatterParseError, OSError, UnicodeDecodeError)` at `:200-209`,
  `existing_lines` at `:210-214`, `fm = model_to_frontmatter(entity, extra_fields)` at `:217-218`,
  `frontmatter.copy()` at `:220`, `mkdir(parents=True, exist_ok=True)` at `:233`, and
  `file_path.write_text(content, encoding="utf-8")` at `:236`. Every one as the doc states, and `:236`
  is still the truncate-in-place form D2.1's whole framing rests on.
- `obsidian_schemas/errors.py:84` is verbatim "Exactly the twelve literals of the construction table
  below", `REASONS:88` holds exactly twelve with `"write did not complete"` live at `:96`, and
  `bounded_message:109-120` raises `from None` outside the set. Task 2's de-pin and D3's reuse of the
  existing literal both hold.
- `tests/derivations.py:_is_write_call:189-195` is exactly the `ast.Call` + `ast.Attribute` +
  `attr in {"write_text", "write_bytes"}` form, so D7's call-form ruling and `## Verified Diagnosis`
  claim 6 both stand. `_own_body_nodes:148-164` does skip nested `FunctionDef`/`ClassDef`;
  `_called_names:167-182` collects `f(...)` and `x.f(...)` alike keying the attribute form on `.attr`;
  `_is_falsy_return:518-521` matches `return`, `return None` and a falsy `ast.Constant`;
  `non_completed_write_sites:484-515` gates its universe on `_is_write_call` exactly as D1 and D10.4
  say. `_SHARED_HELPERS:481` is `{"_get_body_content", "_split_frontmatter_fence"}` as D7 (3) claims.
- `## Verified Diagnosis` claim 13 re-run against this tree rather than inherited:
  `grep -rn 'chmod|st_mode|umask|is_symlink|st_nlink|listxattr|O_EXCL|fchmod' obsidian_schemas/`
  returns **zero**. Mode, symlink and hard-link handling are all newly introduced, as D2.1 states.
- `tests/support.py:temp_dir:31` is the `mkdtemp` context manager Task 3's verify names, and
  `patcher:73` is the shim Task 5 names.

One re-anchoring nit, not drift: `tests/support.py:captured_logs` is at **line 91** (`:91-111`), not
`:90`. Cited with the `:90` suffix twice — Task 10's verify and `## Spec-Writer Round 8`'s note-1
paragraph. The symbol resolves, so per WI-215 this is a nit rather than a REVISE; it is listed under
non-blocking notes.

### Blocking issues

**1. The round-2 threat model moved M1's and M3's `desc`, and neither the fold records nor any Design
surface has followed — so `→ ready` is refused on mechanics AND the two moved requirements appear on
zero surfaces a caged builder reads.**

`## Threat Model — 2026-08-09` (round 2, at the end of the document) is the LATEST SPEAKING round and
re-emits all three ids by design. `## Mitigation Folds — 2026-08-09` was written during round 8
against the round-1 fences. Comparing the fold records' `desc` values against the latest speaking
round:

- **M2** — byte-identical. Its fold is fresh and, having read D3's M2 paragraph, D6's table row, Task
  3's `(M2)` clause and AC-16, its `design` and `work` quotes are faithful and the mitigation is
  satisfied. No action.
- **M1** — **stale.** The fold quotes "carry the target's existing st_mode onto the temp file **before
  the replace**"; the latest desc requires "apply the target's existing st_mode to the temp file's
  **OWN DESCRIPTOR before any note bytes are written to it**".
- **M3** — **stale.** The fold quotes "derive its temp-file directory and its replace target from the
  SAME resolved path"; the latest desc adds "**AND its lock sentinel's own DIRECTORY**" and
  "never let two paths naming one real note key their sentinels in two directories".

That alone is a D8c refusal. The expensive half is that the substance moved too, and I confirmed the
gap on each surface rather than inheriting the threat modeler's reading:

- **M1's ordering is contradicted, not merely unstated.** D2 (line 995) orders the commit as "write
  the bytes, `flush`, `os.fsync(fd)`, close, **carry the mode across**, then link or replace", and
  D2.2 implements it as `os.chmod(tmp, mode)` "before the replace". So the temp file holds the note's
  complete content at the umask-derived `0o666`-and-umask mode for the whole span of the write and the
  fsync. D2.2's second bullet rules that window out with "there is no window in which another
  **writer** can see the file whose mode is being set" — and M1's justification, stated in D2.2's own
  first bullet, is that "person notes carry emails, phones and PII", i.e. a **reader**, whom neither a
  write lock nor a dot prefix nor a unique name excludes. Every other surface repeats the same
  ordering: D1's property 1, Task 3's `(M1)` clause, `## Verification`'s "`os.stat`/`os.chmod` failing
  while carrying the mode across" row, the "Must NOT fail" mode row, AC-15's `desc`, and Task 13's
  AC-15 oracle — which asserts the mode of the **committed** note and is therefore green under both
  orderings.
- **M3 reaches the lock's key and not its home.** D2.3 enumerates what the one resolved path governs —
  "the lock key, the stamp-registry key, the temp file's directory `target.parent`, the `stat_stamp`
  precondition and the terminal `os.replace`/`os.link` argument" — and the sentinel's directory is not
  in that list. D3 independently specifies the sentinel as
  `<note's directory>/.obsidian-schemas-locks/<h>.lock`, deriving only `<h>` from
  `str(path.resolve())`. Two processes reaching one real note through different parents therefore
  compute the same hash into two directories and both acquire — which is verbatim the failure D3's own
  M2 paragraph calls unacceptable ("key two writers' sentinels in different directories and evaporate
  Layer 2's mutual exclusion with no sound"). AC-17 is single-process and asserts where the bytes land;
  AC-8 asserts exclusion with no symlink in the picture; neither can see it. D1's property 2, Task 3's
  `(M3)` clause and `## Verification`'s symlink rows all carry the same unamended list.

This is a sweep obligation, and the surfaces are enumerable rather than remembered. For M1: D2's
commit-order sentence, D2.2 (including replacing the no-window argument, which addresses integrity
where M1's justification is confidentiality), D1 property 1, Task 3's `(M1)` clause, the two
`## Verification` rows, AC-15's `desc` and Task 13's AC-15 oracle — which needs an assertion that can
distinguish the two orderings, since "the committed note's mode" cannot. For M3: D2.3's enumeration,
D3's sentinel-location paragraph, D1 property 2, Task 3's `(M3)` clause, `## Verification`'s symlink
rows, AC-17's `desc` and Task 13's AC-17 oracle — which needs the two-parents-one-note case that
neither AC-17 nor AC-8 covers today. Only then can the two fold records quote sentences that exist.

**2. Wall E is a zero-count wall that ships no match-shape fixtures, on the one wall this document
minted last — and AC-13's `desc` certifies a reach nothing drives.**

D10.5 is titled "Every claimed match-shape ships as a fixture, driven through the wall's own
predicate", and it delivers exactly two batteries: `filesystem_mutation_uses` (Wall A) and
`functions_calling` (Wall D). Task 12 names those same two ("plus **both** match-shape fixture
batteries"). `falsy_returns_in` gets neither a MATCHED battery nor a near-miss, and its only control
is one mutate-and-observe probe — `return None` added to `vault_io.write_note` — which the bar names
as "the complementary half and never sufficient".

The reach being certified is not small. AC-13's `desc` claims the rule holds "over exactly the set the
wall checks, `COMMIT_FUNCTION_NAMES`, **with `read_note` and `ensure_dir` inside it rather than quoted
past it**" — seven function names — and D1/D10.4 claim three falsy forms (`return`, `return None`,
`return False`), own-body-only selection, and selection by `FunctionId.name`'s last dotted segment.
The new logic is that selector; `_is_falsy_return` and `_own_body_nodes` are inherited and already
driven by the live `SiteId` map at `tests/test_loud_fail_write.py:126-139`. A `falsy_returns_in` that
resolved only the three door names — the reading D1's own pre-round-8 sentence ("COMMITS BYTES")
invited, and which round 8 corrected in prose only — leaves a `return None` in `read_note` invisible,
Wall E green, AC-13 green, and AC-13's `desc` asserting the opposite. That is WI-232's shape exactly:
a wall certifying reach it does not have, with every in-build check GREEN. I am not re-deriving
whether the matcher will be correct — that is the builder's and the exit gate's; the question here is
only whether the spec prescribed the controls, and for Wall E it did not.

The fix is one more paragraph in D10.5 and one clause in Task 12, in the shape the document already
uses twice: plant a scratch module and drive it through `falsy_returns_in` — the same function the
wall calls — asserting MATCHED for `return`, `return None` and `return False` in functions named
`read_note`, `ensure_dir` and `stat_stamp` (not only the three doors), and NOT matched for a truthy
`return path`/`return True`, for a falsy return inside a NESTED function of a `write_note` (the
`_own_body_nodes` boundary D10.5 already pins for Wall D), and for a falsy return in a function whose
name is not in `COMMIT_FUNCTION_NAMES`.

**3. The original March scope — the repository cache RLock — is a resolved edge case with no test
anywhere in the plan, in Verification, or in the acceptance set.**

`## Edge Cases`'s last entry resolves "The repository cache under concurrent mutation (the original
March scope)" concretely: `BaseRepository` gains a per-repository `threading.RLock` guarding mutation
of `_cache`, `_file_map` and `_skipped`, taken in `load`, `refresh`, `save`, `update_fields` and each
of the three loaders' recording step, and NOT taken on read paths. Task 7 orders it in six words —
"Add the per-repository `threading.RLock` from Edge Cases" — with no verify clause naming it. I
cross-walked the whole acceptance set: AC-8 is Layer 2's per-note `note_lock` ("excludes concurrent
writers both across processes and across threads, is reentrant within one thread"), and Task 13's
battery item "lock reentrancy within one thread and exclusion across two threads" is that same note
lock. Nothing in `## Verification`'s three tables, nothing in Task 13's list, and no `criteria` fence
mentions `_cache`, `_file_map` or `_skipped` under concurrent mutation.

This is the coverage-gap class Check 4's test-coupling clause names, and it lands on the scope
`## Problem / Motivation` item 4 says "rides along" — the item's founding March framing. It is the
cheapest of the three to close: one `criteria` fence and one check in Task 13 (one thread iterating
`get_all()` while another `refresh()`es, asserting no partial view and no exception), plus a verify
clause on Task 7's RLock sentence so the builder has a falsifier for it.

### Non-blocking notes

- **`tests/support.py:captured_logs` is at line 91, not 90.** Two occurrences — Task 10's verify and
  `## Spec-Writer Round 8`'s note-1 paragraph. Symbol-anchored, so it resolves; a re-anchoring nit.
- **Duplicated line in Task 13.** The sentence "oracle is derived from a value the test itself wrote —
  the exact path it created, the exact" appears twice in succession inside the AC-14 paragraph.
  Cosmetic, but it sits mid-instruction in the task a builder executes.
- **AC-8's `desc` would be the natural home for the timeout, now that AC-16 owns it.** AC-16's `desc`
  ends with "a lock held past the configured timeout raises `WriteFailedError` rather than hanging",
  which is a Layer-2 property living in the configuration criterion. It reads correctly and I am not
  asking for a move — noted only so a later reader does not look for it under AC-8.

### Carried-forward notes

Every still-open non-blocking note from any prior round, by name. Round 8 closed all seven notes the
previous review carried (architect round 7 notes 1–4 and threat-model round-1 notes 1–3) and the
round-2 threat model confirmed its three closed to its satisfaction; I re-read each fold and agree, so
none of those is carried. The previous review's own three non-blocking notes were also actioned
(AC-15/16/17; Task 3's scratch script relocated to `tests/support.py:temp_dir`; the "Must NOT fail"
table widened). Still open:

- **Threat model round 2, note 1** — R14 files ACLs alongside "editor and Finder metadata, not vault
  data", but a macOS ACL is an access-control decision and dropping it on inode replacement widens
  access in the direction M1 exists to narrow. The modeler explicitly does not require it; one clause
  in R14 distinguishing an ACL from Finder metadata would stop a later reader treating "metadata" as
  settled. Still open.
- **Threat model round 2, note 2** — if close-out step 2 ever moves sentinels out of the vault via
  `OBSIDIAN_SCHEMAS_LOCK_DIR`, the value should be a user-private directory rather than a
  world-writable one. A deployment-time choice for close-out step 2, not a rule for the door. Still
  open.
- Threat-model round-2 notes 3 (`move_note` has no external-writer detection) and 4 (no audit trail of
  successful writes) are re-confirmations that R4 and the existing residual are correctly declared,
  with "no mitigation" / "not required" stated by the modeler. Recorded here as requiring no action
  rather than deferred.

### On the series — converging, not a treadmill

Recorded because the `targets:` line below repeats M1, M3 and Task 3 from my previous round, and that
repetition would otherwise read as folds failing to hold. It is not: round 8's M1 and M3 folds HELD,
and the round-2 threat modeler says so in its own words and re-verified each surface rather than
reading the fold table. What changed is the requirement — the modeler re-emitted both fences with
moved `desc` values and stated plainly that the movement is its own under-specification rather than a
producer miss, routing one spec-writer pass instead of a full-cycle bounce. My issue 1 is that pass's
work, which could not have been raised before the round that created it. Issues 2 and 3 are new
targets — Wall E's missing controls and the March cache lock's missing oracle — found by walking the
bar from scratch rather than by re-reading last round's list. I am not proposing an audit fold: the
remaining work is bounded, every surface to close is enumerated above, and none of it re-opens the
frame, the three doors, the total precondition rule, D2.1's cell-by-cell ruling or any `## Scope
Boundary` entry.

```verdict
gate: spec-reviewer
verdict: REVISE
date: 2026-08-09
model: claude-opus-5
targets: M1, M3, Task 3, Task 12, Task 13, AC-13, AC-15, AC-17, #mitigation-folds
note: The round-2 threat model speaks after Spec-Writer Round 8 and moves M1's and M3's desc, so both fold records are stale against the latest speaking round (D8c refuses `→ ready` on mechanics) and, worse, the moved substance is contradicted rather than merely unstated — D2 orders the commit "write the bytes, flush, os.fsync(fd), close, carry the mode across, then link or replace" and D2.2 implements it as os.chmod(tmp) before the replace, so the note's full content sits at the umask-derived temp mode across the write and the fsync while D2.2's own no-window argument excludes another WRITER and M1's justification is a READER of PII-bearing notes, and D2.3's enumeration plus D3's `<note's directory>/.obsidian-schemas-locks/<h>.lock` resolve the hash but not the sentinel's DIRECTORY, so two paths naming one note take two locks and both proceed — the exact failure D3's own M2 paragraph calls unacceptable, invisible to AC-15 (asserts the committed mode, green under both orderings), AC-17 (single-process) and AC-8 (no symlink); separately Wall E is a zero-count wall shipping neither a MATCHED battery nor a near-miss through falsy_returns_in while AC-13's desc certifies reach over all seven COMMIT_FUNCTION_NAMES including read_note and ensure_dir, the WI-232 shape D10.5 already closes for Walls A and D; and the repository-cache RLock — the item's original March scope, resolved concretely in `## Edge Cases` and ordered in six words in Task 7 — has no test in the plan, no row in `## Verification` and no criteria fence, with AC-8 and Task 13's reentrancy check both covering note_lock instead.
```

## Spec-Writer Round 9 — 2026-08-09

All three blocking issues folded, both still-open non-blocking notes closed, and the two
re-anchoring/cosmetic nits fixed. No ruling any prior gate closed is re-opened: the frame, the three
doors, the total precondition rule, D2.1's cell-by-cell ruling, D10.3's vocabulary rulings, D12's
Table 3 and every `## Scope Boundary` entry stand as written.

### Blocking issue 1 — M1 and M3 re-folded against the latest speaking round, surface by surface

The reviewer is right on both halves: the fold records were stale against the round-2 threat model,
and the moved substance was **contradicted** rather than merely unstated. Each surface it enumerated
was edited, and the two `desc` values are now copied byte-for-byte from the round-2 fences.

**M1 — the mode reaches the DESCRIPTOR before the first byte.** D2.2 is rewritten around a
single carrying sentence plus a four-step ordering: stat the target for its mode *before* opening the
temp file; create the temp at `0o600` (the narrowest starting point, and the file is empty);
`os.fchmod(fd, mode)` as the first operation on that descriptor; then write, `flush`, `fsync`, close,
commit. **The later `os.chmod` is deleted, not supplemented** — the fix removes a call. D2's commit
sequence now reads "carry the mode across onto that descriptor while the file is still empty, write
the bytes, …"; D1 property 1 names the window; Task 3's `(M1)` clause carries the four steps in
order; the `## Verification` failure row now names `os.stat`/`os.open`/`os.fchmod`, and a NEW
"Must NOT fail" row states the confidentiality property the old row could not see.

Two things that deserve stating because they are decisions, not transcription:

1. **`os.fchmod` rather than passing `mode` to `os.open`.** `os.open`'s mode argument is
   umask-masked, so it can only NARROW — a target at `0o666` under umask `0o022` would commit at
   `0o644` while the door believed it preserved a mode. `fchmod` is not masked. This is why the
   create step is `0o600`-then-`fchmod` rather than a single `os.open(tmp, …, mode)`, and D2.2 says
   so, including that the transient `0o600` on an EMPTY file is not the "mkstemp's `0600`" M1's
   `desc` forbids.
2. **D2.2's no-window argument is REPLACED, not kept.** The old bullet argued that the dot prefix,
   the unique name and the lock leave "no window in which another WRITER can see the file" — sound,
   and about integrity, when M1's justification is confidentiality. The new bullet states what those
   three properties actually buy and says plainly that the no-window property now comes from the
   ordering and from nothing else.

**The AC-15 oracle needed a new assertion, and the reviewer named exactly why.** Every existing
assertion inspects the *committed* note's mode, which is identical under both orderings. The
distinguishing observation is the temp file's mode at the moment its payload is on disk and not yet
committed — which is what `os.fsync` is, by D2's own ordering. Task 13 now prescribes patching
`os.fsync` through `tests/support.py:patcher:73` to record the mode of every `.*.tmp` in the note's
directory on its first invocation and delegate to the saved original, asserting exactly `{0o600}` —
the bits the check itself chmod-ed. **That assertion is RED under the round-8 ordering**, which is
what makes it a falsifier rather than a restatement. `move_note` is explicitly excluded: door 3 links
an existing inode and writes no temp payload, so there is no window to observe and a probe there
would be theatre.

**M3 — the sentinel's HOME, not only its key.** D3's sentinel location is now
`target.parent / ".obsidian-schemas-locks" / f"{h}.lock"` with both halves derived from
`target = Path(path).resolve()`; D2.3's enumeration lists the sentinel DIRECTORY beside the temp
file's; D1 property 2 names the two-directories failure; Task 3's `(M3)` clause carries the concrete
expression. Under `OBSIDIAN_SCHEMAS_LOCK_DIR` the question cannot arise, and that is said rather than
left implied.

**The AC-17 oracle needed the case neither AC-17 nor AC-8 could see.** Task 13 now prescribes
`<v>/real/note.md` and `<v>/alias/note.md → ../real/note.md`: (a) the **discriminating** assertion —
lock each path in turn, then walk the whole scratch vault and assert exactly ONE
`.obsidian-schemas-locks/*.lock` exists, under `<v>/real/`, which returns TWO under the round-8 text;
(b) the exclusion assertion through a background thread at
`OBSIDIAN_SCHEMAS_LOCK_TIMEOUT="0.05"`; (c) the same single-sentinel assertion with
`OBSIDIAN_SCHEMAS_LOCK_DIR` set, so the configured-home branch is driven rather than assumed. A
`## Verification` row states the property and names which criteria are blind to it.

**No vocabulary or wall change, derived rather than hoped.** `os.fchmod` joins `os.stat` and
`os.open` as `os` members Wall B polices at MEMBER granularity while excluding `vault_io.py` — which
is Wall B's own stated reason for existing ("a name no vocabulary ever anticipated") — so `fchmod` is
added to no vocabulary, nothing is added to `OS_READONLY_NAMES`, nothing is removed from
`PATH_MUTATION_NAMES`, and Tables 1 and 2 keep their shape. Task 3 still forbids editing
`tests/derivations.py`, now naming those two temptations explicitly.

### Blocking issue 2 — Wall E's battery, with its fixture space DERIVED from the constant

Correct and conceded: Wall E was the one zero-count wall in this document shipping neither a MATCHED
battery nor a near-miss, with only a mutate-and-observe probe the bar names as never sufficient. A
new D10.5 subsection and a new Task 12 clause close it in the shape the document already uses twice —
planted scratch modules driven through `falsy_returns_in`, the same function the wall calls.

**The fold is one level up from the reviewer's list, and deliberately so.** The reviewer proposed
asserting MATCHED for three falsy forms in `read_note`, `ensure_dir` and `stat_stamp` — a
five-of-seven sample, and the same generator that produced the gap (an enumeration left to the
author's memory) would leave the two unnamed members unfixtured and any later addition to
`COMMIT_FUNCTION_NAMES` silently uncovered. So the battery **generates one
`def <n>(…): return None` per member by ITERATING the frozenset** and asserts the returned sites'
names are EXACTLY that set — set equality, not `⊇`. A name added to the constant later cannot go
unfixtured, because the fixture reads the constant. On top of that: the three falsy forms, the
falsy-`ast.Constant` forms (`return ""`, `return 0`), the `if`/`try` nesting, and a method form for
the `FunctionId.name` last-segment selection.

The NOT-matched half pins four things beyond the obvious: a falsy return in a NESTED function
(`_own_body_nodes`); a falsy return in `snapshot_stamp`, **carrying a comment naming D4 and D8 step
5**, because its `None` IS the zero case and a wall that matched it would be red against the design;
an implicit fall-off-the-end with no `ast.Return` at all, pinned NOT matched so a later reader meets
D10.4's declared limit instead of "fixing" the wall into a claim it does not make; and the name in a
string literal. AC-13's `desc` now states that the reach is driven rather than asserted, and a
`## Verification` row names the narrower-matcher failure explicitly as the WI-232 shape.

### Blocking issue 3 — the March scope, from six words to a rule with an oracle

Also correct, and it was the cheapest of the three to find and the most expensive to close properly.
Writing the check the reviewer asked for — "no partial view and no exception" — exposed that the
Edge Case's decision as written **cannot deliver it**: a lock taken by the writers and skipped by the
readers buys a lock-free reader nothing while `load()` does `self._cache.clear()` on the live mapping
at `base.py:176-178` and repopulates key-by-key at `:190-191`. `get_all()`'s `list(...)` returns a
complete list of a HALF-BUILT vault; `get_by_role` and its four siblings iterate a dict being mutated
and raise `RuntimeError`. The ordered check would have been RED against code that implemented the
spec exactly.

So the fold is the rule that makes the Edge Case's own read-side sentence true rather than
aspirational: **every mutation of `_cache` and `_file_map` REPLACES the mapping under the
per-repository RLock; no live mapping is ever mutated in place.** `_skipped` is the one container
whose two readers also lock, because it is an append-only diagnostic no hot path reads. The mutation
surface is DERIVED — grep the three declaring names and the whole set is nine sites in five
functions, including the two `save` overrides in `book.py` and `meeting.py` that mutate the cache
directly and `person.py:save`, which delegates and needs no lock of its own. Lock ordering is stated
(the lock spans the cache mutation, never the filesystem write, so it is never held while acquiring
`note_lock`) and the long `load` hold is priced rather than hidden.

**The next level swept and DECLARED:** the subclasses' own indexes are mutated in place under the
same lock and are NOT copy-on-write, so a lock-free index read concurrent with a `refresh()` can
observe a partial index. That is unchanged from today, bounded because every index value is
re-checked against `_cache` before use, declared in Edge Cases, fenced in `## Scope Boundary`, and
excluded from AC-18 in writing — so its absence is a ruling rather than the next round's finding.

Landed as: Task 7's work text (the sites, the rule, the ordering, the two "do NOT"s) and its verify
clause; `## Verified Diagnosis` claim 14 (the falsifier for why the lock alone is insufficient);
a `## Verification` "Must NOT fail" row; Risk 18; AC-18 with
`test_repository_cache_is_consistent_under_concurrent_refresh`, whose oracle is the twelve notes the
check itself wrote and which exercises `get_by_role` alongside `get_all()` because the two fail
differently.

### The carried-forward notes, both closed

- **Threat model round 2, note 1 (ACLs).** D2.1's table splits the xattr row: ACLs get their own
  cell, stated as an access-control decision rather than metadata, declared R14 on the modeler's own
  calibration, with the `os.listxattr` → refuse shape named as the answer if it is ever wanted. R14's
  own text carries the same distinction. Closed.
- **Threat model round 2, note 2 (a shared sentinel home).** Close-out step 2 now says to point
  `OBSIDIAN_SCHEMAS_LOCK_DIR` at a user-private directory, with both failure modes named (a held
  sentinel, a pre-placed symlink) and the boundary stated — M2 validates absolute-and-usable, privacy
  of the home is the deployment choice. Closed.
- Notes 3 and 4 are the modeler's own re-confirmations with "no mitigation" / "not required" stated;
  no action, as the reviewer recorded.

### The reviewer's non-blocking notes

- **`captured_logs` is at line 91.** Both occurrences corrected (Task 10's verify and the round-8
  note-1 paragraph, the latter with a one-line marker so the correction is visible rather than
  silent).
- **The duplicated line in Task 13's AC-14 paragraph.** Removed.
- **AC-8 vs AC-16 and the timeout.** Left where it is, as the reviewer asked. Task 13's covering list
  now says explicitly that AC-8's reentrancy/exclusion check is the per-note `note_lock` and NOT the
  repository cache lock, which is AC-18's — the ambiguity that let issue 3 read as covered.

### What did NOT change

The frame; the three doors; the total precondition rule and its zero case; D2.1's enumeration and its
`st_nlink` cell; D5's derivation corpus and the `== 3` / `== 4` pins; D6's `_env_setting` rule and M2,
which is re-emitted byte-identical and whose fold record is untouched; D7's module-attribute call-form
ruling; D10.1's vocabulary partition and D10.3's `mkdir` / `replace` / `copy` rulings; D10.6's two
tables; D12's Table 3a/3b and the four-branch disposition rule; R1's verbatim reproduction; every
`## Scope Boundary` entry, which gained one bullet and lost none.

## Threat Model — 2026-08-09

**Recommendation: PROMOTE to threat-modeled** (round 3 — a re-review of my own round-2 fences after
`## Spec-Writer Round 9`. Per WI-144 this round re-emits my FULL set; all three ids reappear by
design, and all three `desc` values are **byte-identical to round 2** because nothing about what any
of them REQUIRES has moved.)

### Trigger check

Unchanged and still firing, for the same three reasons: **persists data to files** (every note in the
live vault); **filesystem operations on user-owned files** (the whole item); **crosses a trust
boundary**, which the document names itself at D0.7 — the untrusted input is the filesystem, i.e.
bytes another process or Obsidian wrote between our read and our write. Still NOT firing: no secrets,
no credentials, no OAuth or MCP scopes, no network, no outbound calls, no external messages, no
user-supplied strings, no deserialization of foreign data. Round 9 adds a `threading.RLock` and a
copy-on-write rule over `_cache`/`_file_map` (AC-18) and a wall fixture battery — neither opens a new
category. **S** and **E** remain empty; **T** and **I** carry the weight; **R** and **D** are noted.

### What round 9 landed, re-verified rather than read

I did not take `## Spec-Writer Round 9` or `## Mitigation Folds` at their word. The premise both
generators rest on was re-run against this tree, widened beyond round 2's pattern:
`grep -rn 'chmod|st_mode|umask|is_symlink|st_nlink|listxattr|O_EXCL|fchmod|mkstemp|
NamedTemporaryFile|os\.replace|os\.link|fsync' obsidian_schemas/ scripts/` returns **zero** hits, and
`obsidian_schemas/writer.py:236` is still `file_path.write_text(content, encoding="utf-8")` with
`:233`'s `mkdir(parents=True, exist_ok=True)` immediately above it. Mode, symlink, hard-link, temp-file
and fsync handling are ALL behaviour this item newly introduces — D2.1's whole framing and
`## Verified Diagnosis` claim 13 hold. `obsidian_schemas/errors.py:84` is still verbatim "Exactly the
twelve literals", `REASONS:88` holds twelve with `"write did not complete"` live at `:96`, and
`bounded_message:114-120` raises `from None` outside the set — so M2 mints no new literal and the three
new subclasses' inherited message bound both still stand.

**M1's fold is correct and it closes the confidentiality window I named.** D2.2's four-step ordering —
stat the target for its mode, `os.open(tmp, O_CREAT|O_EXCL|O_WRONLY, 0o600)`, `os.fchmod(fd, mode)` as
the first operation on that descriptor, only then write/`flush`/`fsync`/commit — means the note's
content never reaches disk at a mode wider than the target's, in either direction: a `0o600` target
never widens (the temp starts at `0o600` and `fchmod` holds it there) and a `0o644` target is widened
only while the file is still EMPTY. The later `os.chmod` is deleted rather than supplemented, which is
what I asked for. Three things I checked rather than assumed: (a) `O_EXCL` means a pre-placed file or
symlink at the temp path is a `FileExistsError` → `WriteFailedError`, not a silent write through
someone else's link; (b) the `os.open`-mode-is-umask-masked argument (D2.2's first bullet) is right, and
it is the reason `fchmod` is the only form correct in BOTH directions; (c) D2.2's step 1 keys on the
target's actual EXISTENCE at write time rather than on which door called, so `observe` mode's
replace-where-create-would-refuse path (D9) still carries the existing note's mode instead of falling
into the create branch. Round 8's no-window argument is replaced, not kept, and the replacement says
plainly that the dot prefix, the unique name and the lock are integrity properties that exclude a
WRITER and not a READER.

**M3's fold reaches the sentinel's HOME.** D3 now reads `target.parent / ".obsidian-schemas-locks" /
f"{h}.lock"` with both halves derived from `target = Path(path).resolve()`, D2.3's enumeration lists
the sentinel DIRECTORY beside the temp file's, and D1 property 2 names the two-directories failure.
Two paths naming one real note now compute one sentinel in one directory, which is the mutual-exclusion
hole closed.

**And both oracles can actually see what they certify, which is the half I checked hardest.** AC-15's
`os.fsync` probe asserts the recorded temp mode is exactly `{0o600}` against a note the check itself
chmod-ed to `0o600` — green under the round-9 ordering, RED under round 8's, so it is a genuine
falsifier for the ORDERING. On its own it could not distinguish "fchmod ran" from "fchmod never ran
and the create mode happened to match", but Task 13's committed-mode half repeats the whole assertion
**at `0o644`**, where a build that skipped `fchmod` commits `0o600` and goes red. The two halves
together cover both, and I record the reasoning because the `{0o600}` assertion read alone looks
weaker than it is. AC-17's two-parents-one-note case asserts exactly ONE sentinel under
`<v>/real/.obsidian-schemas-locks`, which returns TWO under the round-8 text, plus the exclusion half
through a background thread and the `OBSIDIAN_SCHEMAS_LOCK_DIR` branch driven rather than assumed.

**`observe`'s blast radius is correctly bounded, and this is the one thing that would have been a new
fence had it been false.** D9 scopes `observe` to "every refusal in D4, D8 and door 3" and states
"Layers 1 and 2 apply in both modes". So M2's configuration refusal, D2.1's `st_nlink > 1` refusal and
Layer 1's `os.stat`/`os.open`/`os.fchmod` `OSError` → `WriteFailedError` all raise in BOTH modes. A
security escape that could be widened by an env var into "tolerate a lock directory that silently
resolves against CWD" would have re-opened M2 through the back door; it cannot.

### Mitigations verified in place — no fence needed for these

1. **Fail-closed on an unobserved path** — D8 step 5's zero case and property 1 of `## Approach`'s
   total rule, AC-14 its oracle, D12.2 option (γ) rejected in writing. Still the single most important
   security property in the document.
2. **Stat-before-read ordering** (D5) — the stamp is deliberately older than the payload, so the
   failure direction is refusal rather than a silent lost update.
3. **No-clobber create as a kernel guarantee** rather than a check (D2, D4), plus `O_EXCL` on the temp
   file itself.
4. **`st_nlink > 1` refused** (D2.1) — a divergence with no correct answer, made loud, in both modes.
5. **Message and chain bounds** inherited by declaring no `__init__` (D11, Task 2), re-verified in
   `obsidian_schemas/errors.py:84-128` this round; `_env_setting` never interpolates a setting's VALUE
   into a message, only the variable's name (D6), so a lock directory carrying a person's name cannot
   reach a diagnostic.
6. **`allow_unverified_overwrite` degrades door 2u to door-1 strength, not to nothing** (D8d).
7. **Fail-loud on bad configuration over the WHOLE surface** — D6's `_env_setting` rule, AC-16, and
   `observe` cannot soften it.
8. **`observe` announces itself once per process** (D6, D9, Task 10) — my round-1 note 1, still closed.
9. **The sentinel filename is a SHA-256 of the resolved path, never the note's name** (D3) — chosen for
   case-insensitive APFS, but it also means a lock directory, in the vault or under
   `OBSIDIAN_SCHEMAS_LOCK_DIR`, leaks no person's name to anyone who can list it.
10. **The repository cache is replaced rather than mutated in place under the RLock** (Edge Cases,
    AC-18) — new this round, and it is an integrity improvement with no new surface. `base.py:176-178`'s
    in-place `.clear()` and `:190-191`'s key-by-key repopulate are exactly as claim 14 states, verified
    in the tree.

### Required mitigations — re-emitted, all three byte-identical

All three remain requirements on `obsidian_schemas/vault_io.py`, a module Task 3 has not yet built, so
all three still stand and are re-emitted per WI-144. Nothing about what any of them requires has moved,
so nothing about their `desc` moves either.

### Notes (non-blocking)

1. **The index level's declared bound answers the wrong-value half and not the iterate-a-live-mapping
   half.** Round 9 declares the subclasses' own indexes NOT copy-on-write and excludes them from AC-18
   in writing, "bounded because every index value is re-checked against `_cache` before use". I checked
   that premise rather than accepting it, and it is TRUE — `person.py:432`, `:454`, `:459` and `:476`
   all end in `self._cache.get(cache_key)`, so a partially-rebuilt index degrades an identity lookup to
   a MISS and cannot resolve an identifier to the WRONG person. That is the direction that would have
   mattered (HAL9000 resolves contacts through this cascade), and it is genuinely closed. What the
   stated bound does NOT cover is `get_by_phone`'s fuzzy fallback at
   `obsidian_schemas/repositories/person.py:457`, which ITERATES `self._phone_index.items()` — verbatim
   the `RuntimeError: dictionary changed size during iteration` shape AC-18 exists to kill one level up,
   surviving on the index. It is pre-existing, loud rather than silent, and fenced by a written ruling,
   so I do not require it; one clause distinguishing the two halves would stop a later reader taking the
   re-check argument as covering both.
2. **`st_mode & 0o7777` carries the setuid/setgid/sticky triad, and the round-9 ordering can drop the
   first two where round 8's could not.** `fchmod` before the write means a subsequent write may clear
   `S_ISUID`/`S_ISGID`; a chmod after the write would have re-applied them. The direction is NARROWING,
   which is the safe one, no markdown note in an Obsidian vault carries those bits, and AC-15 exercises
   `0o600` and `0o644` so it cannot see it either. Recorded only so "keeps the exact `st_mode` bits it
   had" is read with its one honest exception, and explicitly NOT required — a theoretical threat with
   no realistic path is what my calibration forbids me to block on.
3. **R14's ACL cell, closed to my satisfaction.** D2.1 now gives ACLs their own row stating them as an
   access-control decision rather than metadata, with the `os.listxattr` → refuse shape named as the
   answer if it is ever wanted, and R14 carries the same distinction. My round-2 note 1 is closed.
4. **Close-out step 2's user-private lock home, closed.** It now names both failure modes (a held
   sentinel, a pre-placed symlink) and states the boundary — M2 validates absolute-and-usable, privacy
   of the home is the deployment choice. My round-2 note 2 is closed.
5. **Unchanged and still correctly declared:** `move_note` has no external-writer detection (R4 — door
   3's payload is an inode and its destination has no derivation read), and there is no audit trail of
   SUCCESSFUL writes, so a lost update inside R1's µs window leaves no record on our side. An audit log
   would not close R1. No mitigation for either.

```mitigation
kind: required
id: M1
desc: Layer 1 must apply the target's existing st_mode to the temp file's OWN DESCRIPTOR before any note bytes are written to it (and create with an explicit mode, never mkstemp's 0600 nor a bare umask-wide open), so a note keeps the permissions it had AND its content never exists on disk at a wider mode than the target's, not even for the span of the write and fsync.
landed: Task 3
```

```mitigation
kind: required
id: M2
desc: OBSIDIAN_SCHEMAS_LOCK_DIR must be validated at first lock acquisition and raise WriteFailedError when it is not an absolute usable directory, exactly as OBSIDIAN_SCHEMAS_LOCK_TIMEOUT and OBSIDIAN_SCHEMAS_WRITE_GUARD already do — never silently resolved against the process CWD.
landed: Task 3
```

```mitigation
kind: required
id: M3
desc: Every door must derive its temp-file directory, its replace target AND its lock sentinel's own DIRECTORY from the same resolved path the sentinel hash and the stamp registry are keyed on, or refuse a symlinked target with WriteFailedError — never leave a symlink replaced by a regular file, and never let two paths naming one real note key their sentinels in two directories.
landed: Task 3
```

```verdict
gate: threat-modeler
verdict: PROMOTE
date: 2026-08-09
model: claude-opus-5
note: Round 9 closed both findings I raised in round 2 and closed them at the right level — M1's requirement was an ORDERING and D2.2 now stats the target, opens the temp at 0o600 with O_EXCL, fchmods the DESCRIPTOR before the first byte and DELETES the later chmod rather than supplementing it, so the note's content never reaches disk wider than the target in either direction and the round-8 no-window argument is replaced rather than kept; M3's sentinel now derives its DIRECTORY from target.parent alongside its hash, so two paths naming one real note key one sentinel; I re-ran the premise rather than reading it (grep for chmod|st_mode|umask|is_symlink|st_nlink|listxattr|O_EXCL|fchmod|mkstemp|os.replace|os.link|fsync over obsidian_schemas/ and scripts/ returns zero, writer.py:236 is still a bare truncate-in-place write_text under :233's mkdir, and errors.py:84-128 still holds the twelve-literal set with "write did not complete" live at :96 and the from-None bound), and I checked the two things that would have been new fences had they been false: D9 scopes observe to D4/D8/door-3 refusals with "Layers 1 and 2 apply in both modes", so M2's config refusal, the st_nlink refusal and Layer 1's mode-carry OSError all raise in BOTH modes and no env var can widen the escape; and AC-15's {0o600} fsync probe, which alone could not distinguish "fchmod ran" from "create mode happened to match", is covered by Task 13's committed-mode repetition at 0o644 where a skipped fchmod goes red — the two halves together see both failures. All three fences are re-emitted BYTE-IDENTICAL because nothing about what they require has moved; they stand only because Task 3 has not run yet, and the series is converging rather than treadmilling — round 2 raised my own under-specification, round 9 discharged it surface by surface, and my remaining notes are two calibration-level observations I explicitly decline to require.
```

## Spec Review — 2026-08-09

**Recommendation: REVISE — return to spec writer (gaps to fix)**

Read cold from line 1 against `docs/spec-quality-bar.md`, not against the diff. The frame is not
re-opened and no ruling any prior gate closed is re-raised. Round 9's three folds HOLD — I re-read
each rather than reading the round-9 narrative, and the round-3 threat model's `desc` values are
byte-identical to round 2's, so all three `## Mitigation Folds` records are FRESH and their `design`
and `work` quotes are faithful where I found them (M1 → D2.2's carrying sentence at the four-step
ordering; M2 → D3's M2 paragraph; M3 → D2.3's one-resolved-path sentence; each `work` value is Task
3's own clause plus its verify). All three mitigations are satisfied.

**This is my third REVISE, and I am proposing an audit fold rather than a fourth site list.** The
three findings below, my round-2 Wall-E finding and my round-2 March-scope finding are five members
of ONE discipline, and the pattern is stated in "On the series" at the end. The concrete sites are
still enumerated, because the writer needs them — but the ask is the fold, not the five patches.

### Citation verification

Verified for MEANING at each site, read in the tree this round rather than taken from the injected
drift audit (which proves symbol existence only). All resolve and mean what the doc claims —
`tests/derivations.py`'s symbol line numbers are exact to the line (`python_files_under:88`,
`_iter_functions:122`, `_own_body_nodes:148`, `_called_names:167`, `_is_write_call:189`,
`base_repository_subclasses:312`, `load_file_implementations:355`, `_function_id_of:380`,
`seam_invocation_closure:393`, `_SHARED_HELPERS:481`, `non_completed_write_sites:484`,
`_is_falsy_return:518`, `modules_using_ast:528`), `tests/support.py:temp_dir:31` / `patcher:73` /
`captured_logs:91` are all correct (round 9's re-anchoring landed), and every named check in
`tests/test_loud_fail_write.py` (`:52`, `:58`, `:103`, `:110`) and `tests/test_writer.py` (`:146`,
`:158`, `:287`, `:341`, `:426`, `:436`) is at the stated line. **One exception:**

- **`test_ast_is_single_homed` names nothing.** Task 11's verify reads "`test_ast_is_single_homed`
  in `tests/test_loud_fail_harness.py:96` still passes". That module declares exactly one test —
  `test_derivations_are_single_sourced` at `tests/test_loud_fail_harness.py:58` — and `:96` is the
  `modules_using_ast(...)` line inside its private helper `_check_derivations_are_single_sourced:66`.
  A builder cannot run the named check; `pytest ...::test_ast_is_single_homed` collects nothing. The
  fix is the correct name. *(The drift audit did not catch this because the citation is written as a
  prose name beside a bare `file:line` rather than in `path:symbol:line` form — which is the reason
  the bar requires reading the code regardless of an empty audit.)*

### Blocking issues

**1. Two of the five walls ship no match-shape battery, and AC-7's `desc` certifies the reach of
both — the WI-232 shape round 9 closed for Wall E only.**

D10.5 is titled "Every claimed match-shape ships as a fixture, driven through the wall's own
predicate" and delivers exactly three batteries: `filesystem_mutation_uses` (Wall A),
`functions_calling` (Wall D), `falsy_returns_in` (Wall E, added round 9). Task 12 says "all **THREE**
match-shape fixture batteries" and names those three; the `## Write Targets` `why` for
`tests/test_write_routing.py` names the same three. **`os_module_attribute_uses` (Wall B) and
`module_import_uses` (Wall C) get neither a MATCHED fixture nor a near-miss.** The two near-miss rows
that mention Wall B — `os.environ.get("X")`, `os.getcwd()` — are Wall *A* near-misses that defer to
Wall B in prose; nothing is driven through Wall B's own function.

Both are zero-count oracles on exactly the arm that matters, and I confirmed the counts against the
tree rather than reading Table 1:

- **Wall B's `from os import <n>` arm has ZERO live sites**, pre- and post-routing. The only `os`
  imports under either root are the plain `import os` at `obsidian_schemas/repositories/base.py:9`,
  `scripts/lint_vault.py:22` and `scripts/migrate_person_to_discuss.py:23`, and the only attribute
  uses are the three `os.environ` reads. So an `os_module_attribute_uses` that never implements the
  `ast.ImportFrom` collection returns the identical three `environ` uses, Wall B is GREEN, Table 1's
  row ("zero `from os import` bindings") matches, Table 2 matches, and AC-7 is GREEN. That arm was
  added in round 6 for one stated purpose — "that form is how `from os import replace as _r` would
  otherwise smuggle a mutator past a wall keyed on attribute access" — and it is one of the two
  things R10 names as bounding the declared blind spot ("Wall B independently makes any `os` member
  outside `OS_READONLY_NAMES` red wherever it is named"). Unfixtured, R10's bound can be false with
  every check green.
- **Wall C is a genuine zero-count wall.** `module_import_uses(files, {shutil, tempfile, fcntl,
  filelock, mmap})` returns empty today (confirmed: zero such imports under either root) and returns
  only `vault_io.py`'s after routing. D10.3 claims it reads "both forms" (`ast.Import` /
  `ast.ImportFrom`); a matcher implementing one form — or returning `[]` unconditionally — is green
  at Task 0, green at Task 11 and green at Task 12.

AC-7's `desc` asserts `vault_io.py` is the only file that "**imports a mutation-capable module**, or
reaches a non-read-only `os` attribute **in either access form** — and the wall's predicate …
**proven to resolve every claimed match shape and to reject every near-miss**". Two of the three
predicates AC-7 covers have no such proof prescribed. This is not a re-derivation of whether the
matchers will be correct — that is the builder's and the exit gate's — it is that the spec ordered
the checks and prescribed the controls for three of five.

*The fold, and why it closes the class rather than two instances:* D10 declares a CLOSED, enumerable
surface — five walls, five predicates, named in D10.1. State the obligation over that surface once —
*every wall predicate in D10 ships a MATCHED battery and a NOT-matched battery, planted in a scratch
module and driven through the same function the live wall calls* — and derive Task 12's battery list
from D10.1's predicate set rather than from a hand-written list of three, exactly as round 9 derived
Wall E's fixture space by iterating `COMMIT_FUNCTION_NAMES` instead of naming five of seven members.
For Wall B the MATCHED shapes are `os.<n>` for an `n ∉ OS_READONLY_NAMES` and `from os import <n>` /
`from os import <n> as <a>` with the binding used and unused, near-missed by `os.environ`,
`os.getcwd()` and `from os import environ`; for Wall C, `import shutil`, `import tempfile as _t` and
`from filelock import FileLock`, near-missed by `import os` (legitimate at three live sites) and by
the module names in a string literal.

**2. Task 8 adds a TENTH `_cache`/`_file_map` mutation site — in `person.py`, the one file D11 and
Task 7 both declare needs no cache lock — and the Edge Cases rule's derived nine-site surface was
swept over the PRE-build tree, so the site this item itself creates is the one that escapes it.**

Round 9's cache fold states the rule over a derived surface: "grep the declaring names `_cache`,
`_file_map` and `_skipped` across `obsidian_schemas/` and the whole set is **nine sites in five
functions**", ending "`person.py:save:1252` delegates to `super().save()` … so it needs no lock of
its own. A tenth site added later either goes through the rule or is a mutation of a live mapping a
lock-free reader can catch mid-flight — which is what AC-18's check is for." Task 7 repeats it as an
instruction ("do not add a lock there") and D11's `person.py` row states "**No cache lock here**".

But Task 8 orders precisely that tenth site, in that file: "catch `NoteAlreadyExists`, re-read that
one path via `base.py:_load_file:226`, **re-register the stamp, cache the entity**, then take the
existing reuse branch at `:1430-1437`" — D9 says the same ("caches the loaded entity"). The grep was
run against today's tree, where `create_stub` performs no cache mutation; after Task 8 it does. Three
consequences, each checked in code:

- **The rule does not reach it.** Nothing tells the builder that this adoption takes `_cache_lock`
  or replaces the mapping rather than mutating it, and D11/Task 7 affirmatively say `person.py`
  needs no lock — so the document is buildable two ways at a site whose whole purpose is
  cross-process correctness (WI-144).
- **AC-18 cannot see it.** Its check runs `repo.refresh()` against `get_all()` / `get_by_role()`;
  it never calls `create_stub`. So an in-place mutation here is green on the floor, green on every
  wall (they are blind to a cache write by construction) and green on AC-18.
- **"Cache the entity" is under-specified against the shape every other adoption site uses, and the
  narrow reading breaks Task 8's own verify.** All three existing adoptions write three things —
  `base.py:190-192`, `:331-334`, `:412-414` each set `_cache[key]`, `_file_map[key]` and call
  `_index_entity`. A builder who literally "caches the entity" into `_cache` alone leaves
  `_file_map` empty for that key; the reuse branch then calls `_writeback_identifier`
  (`obsidian_schemas/repositories/person.py:1436`), which routes through `update_fields`
  (`:1214`), which calls `get_file_path` (`obsidian_schemas/repositories/base.py:363` →
  `:292`, `self._file_map.get(...)`), gets `None`, and raises
  `ValueError(f"{self.type_name} not found in repository: {name}")` at `:366` — before the phone is
  written back. Task 8's verify asserts the opposite ("the phone written back"), so the check goes
  RED against a build that followed the task text.

*The fold, stated at the level that makes it total:* the cache-adoption surface is a countable corpus
this change ALTERS, so derive it over the tree the plan PRODUCES rather than over the tree the plan
starts from — or make it total by construction the way D5's (A′) made the loader corpus total: one
`BaseRepository` adoption method that writes `_cache`, `_file_map` and `_index_entity` under the lock
with the replace rule, with every adoption site (the five existing plus Task 8's) calling it, so a
tenth site either routes through the door or is a new in-place mutation a check can be pointed at.
Whichever shape wins, Task 8's text needs the three-part adoption named, and D11's `person.py` row
and Task 7's "do not add a lock there" need to say what they now mean.

**3. AC-5's and AC-9's `check` names are authored by no task — each has a task authoring a
DIFFERENTLY-NAMED check for the same behaviour, so both criteria fail at the exam against a correct
build.**

`## Acceptance Criteria`'s own preamble states the mechanism: "`src/stage_advancer.py` invokes
`getattr(mod, name)()`". I cross-walked all eighteen `check` names against every task that authors a
check. Sixteen resolve — AC-6 to Task 9, AC-7/AC-12/AC-13 to Task 12, AC-10/AC-14 to Task 13,
AC-11/AC-18 to Task 7, AC-15/AC-16/AC-17 to Task 3 and Task 13, and AC-1/2/3/4/8 to Task 13's
covering list under its closing rule that "each `kind: test` check named in `## Acceptance Criteria`
is a top-level `def test_*(` taking ZERO arguments". Two do not:

- **AC-5** names `test_create_is_no_clobber_and_create_stub_reuses_the_winner`. Task 8's verify
  orders `test_create_stub_losing_a_cross_process_race_reuses_the_winner`, and Task 13's covering
  list points at it as "door-2c create race (Task 8's check)". A builder following the plan authors
  Task 8's name; AC-5's name exists nowhere. **And the substance is short too:** AC-5's `desc`
  covers "while the book and company stubs surface `NoteAlreadyExists`", which Task 8's
  person-only check does not exercise and no other task's check does either, though D9 and
  `## Verification`'s failure table both state the behaviour.
- **AC-9** names `test_refusals_are_loud_bounded_and_mode_governed`. Task 10's verify orders
  `test_observe_mode_warns_and_proceeds_where_enforce_refuses`, and Task 13's list points at it as
  "observe mode (Task 10's check)". Same outcome — and AC-9's `desc` is wider than observe mode
  (every refusal is a `LoudFailError` distinguishable from `WriteFailedError`, carries its path, and
  leaks no note content into its message), so no authored check covers the bounded-message half.

This is the same discipline as issues 1 and 2 seen at the acceptance layer: the AC → authoring-task
map is maintained per-task from memory rather than derived from the `criteria` fence set. The fold
is to derive it — walk the fence set once, name the authoring task for every `check`, and let an AC
with no authoring task be the loud case.

### Non-blocking notes

- **Task 12's Wall-A probe may need a placement clause.** The probe temporarily adds
  `Path("x").unlink()` to `obsidian_schemas/writer.py`. Wall A reads parsed syntax, so the statement
  need never execute — but at module scope it would raise `FileNotFoundError` on import of
  `writer.py`, which Wall D's `base_repository_subclasses` reaches by import. One clause saying the
  probe goes inside a function body removes a decision the builder would otherwise have to make
  while a wall is red.
- **`## Verification`'s regression list is "expected", not derived.** Task 15 correctly derives the
  sweep, and the prose list is explicitly there "so a shorter result is visibly a miss". Worth noting
  that `tests/test_loud_fail_harness.py` is in the list and does consume `tests/derivations.py`, so
  Task 0's edit will be swept — good; no change asked.
- **Task 0's count-pin sweep names two corpora and this item alters a third.** Task 2 sweeps
  `REASONS` (no `len(REASONS)` pin exists — confirmed) and the `BaseRepository` subclass corpus (the
  `== 4` / `== 3` pins). Task 0 grows a third countable corpus, `tests/derivations.py`'s shared
  derivation exports, and `tests/test_loud_fail_harness.py:72-81` carries a count over it
  (`six = {...}`, `assert len(six) == 6`). It stays GREEN — its own comment says so explicitly ("a
  seventh shared derivation extends this list; it is a required subset, not a cardinality bound") —
  so this is a note rather than an issue, but naming it in Task 0 would make the sweep's silence a
  ruling rather than an omission.

### Carried-forward notes

Round 9 closed both notes my previous round carried (threat-model round-2 notes 1 and 2 — the ACL
cell now has its own D2.1 row, and close-out step 2 now names a user-private lock home), and the
round-3 threat model confirms both closed; I re-read each and agree, so neither is carried. My own
previous non-blocking notes were all actioned: `captured_logs` re-anchored to `:91` at both sites,
the duplicated line in Task 13's AC-14 paragraph removed, and AC-8/AC-16's timeout left where it is
as I asked. Still open:

- **Threat model round 3, note 1** — the index level's declared bound covers the wrong-value half
  and not the iterate-a-live-mapping half. Verified this round: `person.py:454`, `:459` and `:476`
  do end in `self._cache.get(cache_key)`, so a partial index degrades to a MISS and cannot resolve
  to the WRONG person — but `get_by_phone`'s fuzzy fallback at
  `obsidian_schemas/repositories/person.py:457` ITERATES `self._phone_index.items()`, which is the
  `RuntimeError: dictionary changed size during iteration` shape AC-18 exists to kill one level up.
  Pre-existing, loud rather than silent, and fenced by a written `## Scope Boundary` ruling; the
  modeler explicitly declines to require it. One clause in Edge Cases distinguishing the two halves
  would stop a later reader taking the re-check argument as covering both. Still open.
- **Threat model round 3, note 2** — `st_mode & 0o7777` carries the setuid/setgid/sticky triad, and
  the round-9 `fchmod`-before-write ordering can let a subsequent write clear `S_ISUID`/`S_ISGID`
  where a chmod-after-write would have re-applied them. The direction is NARROWING, no markdown note
  carries those bits, and AC-15 exercises `0o600`/`0o644` so it cannot see it. Explicitly not
  required by the modeler; recorded so "keeps the exact `st_mode` bits it had" is read with its one
  honest exception. Still open.
- Threat-model round-3 notes 3, 4 and 5 are the modeler's own re-confirmations that R4 (no
  external-writer detection on `move_note`) and the absent successful-write audit trail are
  correctly declared, with "no mitigation" / "not required" stated. Recorded as requiring no action
  rather than deferred.

### On the series — the audit fold, proposed rather than a fourth site list

My rounds have been monotone: round 1's two objections closed and stayed closed, round 2's three
closed and stayed closed, and I re-verified round 9's folds rather than assuming them. But they keep
landing NEW SITES OF ONE DISCIPLINE, and that is the signal the bar says to act on at the third
round:

> **An enumeration this document owns is maintained from the author's memory over the PRE-CHANGE
> tree, when the surface it enumerates is closed, declared, and derivable from its own source.**

Five members now: Wall E's missing battery (round 2), the March cache lock's missing oracle (round
2), Walls B and C's missing batteries (issue 1), the nine-site cache surface that the item's own
Task 8 makes ten (issue 2), and the AC → authoring-task map (issue 3). Every one of them is a list
where a derivation was available, and every one of them is green in every in-build check.

**The fold, and how to execute it: ONE audit pass over the document's enumerated surfaces, closing
each with a rule total over its source rather than by adding the missing entries.** The surfaces are
themselves enumerable, which is what makes this bounded — walk each and state the rule at its
declaring source:

1. **The wall set** (D10.1 declares five predicates) → every wall predicate ships a MATCHED and a
   NOT-matched battery driven through the wall's own function; Task 12's battery list is derived
   from the predicate set, not hand-listed.
2. **The acceptance set** (the `criteria` fences) → every `check` name has exactly one authoring
   task, derived by walking the fence set; an AC with no authoring task is the loud case.
3. **The cache-adoption surface** (the `_cache` / `_file_map` declaring names) → derived over the
   POST-build tree, or made total by construction with one adoption method every site calls.
4. **The count-pin surface** (Task 2's sweep) → the third corpus this item grows,
   `tests/derivations.py`'s exports, named with its pin and its verdict.

This is the same move this document already made twice and made well — D5's (A′) derived the loader
corpus and enforced over it with Wall D, and round 9 derived Wall E's fixture space by iterating
`COMMIT_FUNCTION_NAMES` instead of naming five of seven members. The ask is to run that move once
across the remaining enumerations rather than to buy a fourth round finding the sixth list. Nothing
here re-opens the frame, the three doors, the total precondition rule, D2.1's cell-by-cell ruling,
D10's vocabulary rulings, D12's Table 3, the three mitigations or any `## Scope Boundary` entry.

```verdict
gate: spec-reviewer
verdict: REVISE
date: 2026-08-09
model: claude-opus-5
targets: AC-5, AC-7, AC-9, Task 7, Task 8, Task 11, Task 12, #design
note: Third monotone REVISE, so this is an AUDIT-FOLD proposal rather than a fourth site list — the generator is that an enumeration this document owns is maintained from memory over the PRE-CHANGE tree where the surface is closed and derivable, and the five members are Wall E (my round 2), the March cache oracle (my round 2) and these three: D10.5/Task 12 ship match-shape batteries for three of the FIVE wall predicates, leaving os_module_attribute_uses and module_import_uses undriven while AC-7's desc certifies both ("imports a mutation-capable module, or reaches a non-read-only os attribute in either access form ... proven to resolve every claimed match shape"), and each is zero-count on the arm that matters (I confirmed the only os imports under either root are plain `import os` at base.py:9, lint_vault.py:22 and migrate_person_to_discuss.py:23 with zero `from os import` and zero shutil/tempfile/fcntl/filelock/mmap imports), so a Wall B without the ImportFrom arm added in round 6 and a Wall C that returns [] are both GREEN at Tasks 0, 11 and 12 while R10's stated bound on the declared blind spot is false; Task 8 orders "cache the entity" in create_stub's NoteAlreadyExists recovery, which is a TENTH _cache/_file_map mutation site in the one file D11 ("No cache lock here") and Task 7 ("do not add a lock there") declare needs none, escaping Edge Cases' nine-site grep because that grep was run over the pre-build tree, invisible to AC-18 (which exercises refresh/get_all/get_by_role, never create_stub), and under-specified against the three-part adoption every existing site uses (base.py:190-192, :331-334, :412-414) — cache alone leaves _file_map empty, so the reuse branch's _writeback_identifier -> update_fields -> get_file_path (base.py:363 -> :292) returns None and raises ValueError at base.py:366 before the phone is written back, which is exactly what Task 8's own verify asserts; and AC-5 and AC-9 name checks no task authors, each having a task that authors a differently-named check for the same behaviour (Task 8's test_create_stub_losing_a_cross_process_race_reuses_the_winner, Task 10's test_observe_mode_warns_and_proceeds_where_enforce_refuses), so both fail the exam's getattr(mod, name)() against a correct build, with AC-5's book/company half and AC-9's bounded-message half covered by no authored check at all; separately Task 11's verify names test_ast_is_single_homed in tests/test_loud_fail_harness.py, whose only test is test_derivations_are_single_sourced:58.
```

## Spec-Writer Round 10 — 2026-08-09

The reviewer's round-9 verdict declined to hand back a fourth site list and proposed an **audit fold**
instead: one pass over the enumerations this document owns, closing each with a rule total over its
own source rather than by adding the missing entries. That is what this round does. The three
blocking findings are closed as the four surfaces the fold names, not as three patches, and the
citation defect and both non-blocking notes are closed by name.

### The generator, accepted as stated

> An enumeration this document owns is maintained from the author's memory over the PRE-CHANGE tree,
> when the surface it enumerates is closed, declared, and derivable from its own source.

Five members, and the reviewer's count is right: Wall E's missing battery (its round 2), the March
cache lock's missing oracle (its round 2), Walls B and C's missing batteries, the nine-site cache
surface that this item's own Task 8 makes ten, and the AC → authoring-task map. Every one is green in
every in-build check, which is why enumeration was never going to converge. The four surfaces are
themselves enumerable, so the fold is bounded.

### Surface 1 — the wall set. Closed at D10.1, its declaring source.

`D10.5` now OPENS with the obligation stated once over the predicate set rather than per wall:
every predicate declared in D10.1 ships a MATCHED battery and a NOT-matched battery, planted in a
scratch module and driven through the same function the live wall calls. **Task 12 derives its
battery list from that set** — five, one per predicate — with an explicit instruction not to inherit
"three" from an earlier revision of the task. `## Write Targets`' `why` for
`tests/test_write_routing.py` says five and names which two arrived this round.

The two missing batteries are written out in full in D10.5 (Wall B over both access forms including
the `ast.ImportFrom` arm and an imported-but-uncalled binding; Wall C over both statement forms with
its MATCHED fixtures **generated by iterating the module set** rather than hand-listed, the same move
round 9 used on `COMMIT_FUNCTION_NAMES`). The reviewer's zero-count argument is reproduced in the
document rather than only in the review, because it is the reason the gap was invisible: verified
against this tree, the only `os` imports under either root are the plain `import os` at
`obsidian_schemas/repositories/base.py:9`, `scripts/lint_vault.py:22` and
`scripts/migrate_person_to_discuss.py:23`; there are zero `from os import` bindings and zero
`shutil`/`tempfile`/`fcntl`/`filelock`/`mmap` imports. Two `## Verification` "must NOT fail" rows now
name each narrower-matcher failure with AC-7 as its oracle.

### Surface 2 — the cache-adoption surface. Made TOTAL BY CONSTRUCTION, not re-derived.

The reviewer offered two shapes and this round takes the stronger one: **`BaseRepository._adopt(name_key,
entity, file_path)`**, one method that writes `_cache`, `_file_map` and `_index_entity` under
`_cache_lock` with the replace rule, and which every SINGLE-ENTITY adoption site calls. All four
existing single-entity sites are the identical three-line shape — verified in the tree this round at
`base.py:save:331-334`, `base.py:update_fields:412-414`, `book.py:save:173-176`,
`meeting.py:save:195-198` — and **Task 8's is the fifth**. That is the whole point: a list derived
over the pre-build tree cannot reach a site the plan itself creates, which is why the rule is a door
and not a longer grep. `base.py:load:189-192` is the one existing site that does NOT become an
`_adopt` call and it is ruled rather than skipped: `load` is a bulk rebuild that fills local mappings
across the walk and rebinds ONCE, so a per-note `_adopt` there would publish a half-built vault once
per note instead of never.

Three consequences the reviewer named, each closed:

- **The rule now reaches it.** Task 8 orders `self._adopt(...)` by name and forbids a bare
  `self._cache[key] = entity`; D9 says the same in the design; D11's `person.py` row no longer says
  "No cache lock here" but "`save:1252` still adopts nothing of its own", which is now a *consequence*
  of the door rather than a per-file exemption; Task 7's "do not add a lock there" is replaced by "it
  calls `_adopt` nowhere".
- **Something can see it.** `functions_calling(files, "_adopt")` is a new **Table 2** row asserted as
  set EQUALITY against the five adopting functions, and a new Table 1 row pins it empty pre-build so
  the post-build result is a measured delta. That is Wall D's own predicate over a new name — no new
  machinery — and it is the SURFACE oracle beside AC-18's BEHAVIOURAL one. Task 11 lists it.
- **"Cache the entity" is no longer under-specified, and the trap is written down.** Task 8 and D9
  both spell out why `_file_map` is load-bearing: the reuse branch calls `_writeback_identifier`
  (`person.py:1189`, `:1214`) → `update_fields` → `get_file_path` (`base.py:363` → `:292`), which
  returns `None` on a missing `_file_map` entry and raises `ValueError` at `base.py:366` **before the
  phone is written back** — which is exactly what Task 8's own verify asserts. Confirmed in code this
  round.

### Surface 3 — the acceptance set. Derived by walking the fences.

The walk was run over all eighteen fences. Sixteen resolved; AC-5 and AC-9 did not, exactly as the
reviewer found. Closed by making the authoring task author the AC's name **and** widening it to the
AC's full `desc`, rather than by renaming the criterion down to what a check happened to cover:

- **AC-5** — Task 8 now authors `test_create_is_no_clobber_and_create_stub_reuses_the_winner` in
  three parts: the no-clobber create, the `PersonRepository` reuse, and the
  `BookRepository`/`CompanyRepository` halves (`book.py:create_stub:273`,
  `company.py:create_stub:153`), which D9 and `## Verification` stated and no check exercised.
- **AC-9** — Task 10 now authors `test_refusals_are_loud_bounded_and_mode_governed` in two parts: the
  loud-and-bounded half (each refusal a `LoudFailError`, not a `WriteFailedError`, carrying its path,
  with a sentinel string the check itself planted asserted absent from the message) and the mode half.

New `## Acceptance Criteria — Authoring Map` section records the walk's result for all eighteen. It
is its own `##` section, not a `###` under `## Acceptance Criteria`, because it drifts (WI-185). Task
13's closing rule orders the walk and gives it a read-only one-liner, and declares an AC with no
authoring task a HAND-BACK rather than a test to invent at exam time.

### Surface 4 — the count-pin surface. Widened from "corpora this item EDITS" to "GROWS OR EDITS".

Task 2's sweep declaration now carries corpus (iii), `tests/derivations.py`'s shared-derivation
exports, and **Task 0 — the task that grows it — carries the ruling**: the pin is
`tests/test_loud_fail_harness.py:72-81`'s `six = {...}` / `assert len(six) == 6`, the verdict is
GREEN-and-untouched, and the reason is that check's own comment at `:70-71` ("a seventh shared
derivation extends this list; it is a required subset, not a cardinality bound"). Verified in code.
Task 0's verify records it, so the sweep's silence is a ruling.

### The citation defect

Task 11's verify named `test_ast_is_single_homed`, which exists nowhere.
`tests/test_loud_fail_harness.py` declares exactly one test — `test_derivations_are_single_sourced` at
`:58` — and `:96` is the `modules_using_ast(...)` line inside its private helper
`_check_derivations_are_single_sourced:66`. Corrected to the real name with both anchors, so a
builder can run it.

### The non-blocking notes and the carried-forward pair, each closed by name

- **Wall-A probe placement.** Task 12 now says the temporary `Path("x").unlink()` goes **inside an
  existing function body, never at module scope** — Wall A reads parsed syntax and never needs it to
  execute, while a module-scope statement raises `FileNotFoundError` on import of `writer.py`, which
  `base_repository_subclasses` reaches by import, taking Wall D down alongside Wall A.
- **Threat model round 3, note 1 — the index bound's two halves.** Edge Cases and the matching
  `## Scope Boundary` entry now distinguish them: the wrong-VALUE half is closed (every lookup ends in
  `self._cache.get(...)`, so a partial index degrades to a MISS), the ITERATE-A-LIVE-MAPPING half is
  not — `person.py:get_by_phone:457` iterates `self._phone_index.items()`, verified this round, which
  is the `RuntimeError` shape AC-18 kills one level up. Pre-existing, loud, explicitly not required;
  named so the re-check argument is not read as covering both.
- **Threat model round 3, note 2 — the setuid triad.** D2.2 gains a fifth bullet and the
  `## Verification` mode row gains a clause: `st_mode & 0o7777` carries `S_ISUID`/`S_ISGID`/sticky,
  POSIX clears the first two on an unprivileged write, so M1's `fchmod`-then-write ordering can drop
  them where a chmod-after-write would have re-applied them. Direction is narrowing only, no note
  carries them, AC-15's `0o600`/`0o644` cases cannot see it, and closing it would re-open M1's
  confidentiality window. Named as the one honest exception to "keeps the exact `st_mode` bits it had".
- The reviewer's third note (`## Verification`'s expected regression list being expected rather than
  derived, with `test_loud_fail_harness.py` correctly present) asked for no change and gets none.

### What did NOT change

The frame; the three doors; the total precondition rule; D2.1's cell-by-cell ruling; D5's (A′) and
its `== 3` / `== 4` pins; D10's vocabulary rulings including R10 and the `mkdir` cell; D12's Tables
3a and 3b and the four-branch disposition rule; every `## Scope Boundary` entry; and all three
mitigation folds — M1, M2 and M3 quote Task 3's clauses and D2.2/D2.3/D3 sentences, none of which
this round edited, so the three `fold` records are unchanged and remain fresh against the latest
speaking `## Threat Model` round.

## Threat Model — 2026-08-09

**Recommendation: PROMOTE to threat-modeled** (round 4 — a re-review of my round-3 fences after
`## Spec-Writer Round 10`. Per WI-144 this round re-emits my FULL set; all three ids reappear by
design, and all three `desc` values are **byte-identical to rounds 2 and 3** because nothing about
what any of them REQUIRES has moved.)

### Trigger check

Unchanged and still firing, for the same three reasons: **persists data to files** (every note in the
live vault); **filesystem operations on user-owned files** (the whole item); **crosses a trust
boundary**, which the document names itself at D0.7 — the untrusted input is the filesystem, i.e.
bytes another process or Obsidian wrote between our read and our write. Still NOT firing: no secrets,
no credentials, no OAuth or MCP scopes, no network, no outbound calls, no external messages, no
user-supplied strings, no deserialization of foreign data. Round 10 is an **audit fold** — four
enumerations closed by a rule over their own source — and I checked each of the four for a new
category rather than assuming a fold cannot open one. None does. **S** and **E** remain empty;
**T** and **I** carry the weight; **R** and **D** are noted.

### What round 10 landed, re-verified rather than read

The premise both generators rest on was re-run against this tree, not taken from
`## Spec-Writer Round 10`:

- **The module the three mitigations constrain still does not exist.** `obsidian_schemas/vault_io.py`
  is absent from the tree (glob over the whole checkout returns nothing), and so is
  `tests/test_concurrent_access.py` — the `tests/` listing is the nineteen pre-build modules. Task 3
  has not run. That is the entire reason all three fences still stand.
- **The mode/atomicity premise holds, widened.** `grep -rn
  'chmod|st_mode|umask|is_symlink|st_nlink|listxattr|O_EXCL|fchmod|mkstemp|NamedTemporaryFile|
  os\.replace|os\.link|fsync' obsidian_schemas/ scripts/` returns **zero** hits — every occurrence in
  the checkout is inside this document or `state/escalations.jsonl`. `obsidian_schemas/writer.py:236`
  is still verbatim `file_path.write_text(content, encoding="utf-8")` under `:233`'s
  `file_path.parent.mkdir(parents=True, exist_ok=True)`. Mode, symlink, hard-link, temp-file and
  fsync handling remain behaviour this item newly introduces, so D2.1's framing and
  `## Verified Diagnosis` claim 13 hold.
- **The message-bound premise holds.** `obsidian_schemas/errors.py:84` is still verbatim "Exactly the
  twelve literals", `REASONS:88-102` holds twelve with `"write did not complete"` live at `:96`, and
  `bounded_message:109-120` still raises `from None` outside the set — so M2 mints no new literal and
  the three new subclasses' inherited message bound stands.
- **The M2 premise holds.** The only `os` under either root is the plain `import os` at
  `base.py:9`, `scripts/lint_vault.py:22` and `scripts/migrate_person_to_discuss.py:23`; zero
  `from os import` bindings; the only attribute uses are three read-only `os.environ` reads
  (`base.py:97`, `lint_vault.py:52`, `migrate_person_to_discuss.py:160`). There is no
  `OBSIDIAN_SCHEMAS_LOCK_DIR` reader in the tree at all yet.
- **The M3 and cache premises hold.** Zero `threading`, `RLock`, `Lock(`, `filelock` or `fcntl`
  anywhere under `obsidian_schemas/`. Every cache mutation is unguarded and in-place exactly as
  claim 14 states: `base.py:176-178`'s `.clear()` triad and `:186-193`'s key-by-key repopulate.

**Surface 2 is the only one of the four that ships CODE, and its lock ordering is the thing I checked
hardest.** `BaseRepository._adopt` takes `_cache_lock` and rebinds `_cache`/`_file_map` from copies.
A door that takes a mutex inside a call graph that already takes a per-file `flock` is a deadlock
shape, and a deadlock here is a denial of service on HAL9000's request path, not a hygiene note.
Edge Cases rules it explicitly and the ruling is sound in both directions: the repository lock spans
the CACHE MUTATION only — `save` holds it for `base.py:331-333` and **not** around its
`write_markdown_file` call, `update_fields` for `:399-413` and not around its door-1 write — so no
thread holds the repository lock while acquiring `note_lock`, and `note_lock` is never held while
acquiring the repository lock. There is no cycle because there is no nesting in either direction. I
confirmed the four existing adoption sites are the identical three-line shape the door replaces
(`base.py:331-334`, `base.py:412-414`, `book.py:173-176`, `meeting.py:195-198`), that `load` is
correctly excluded (`:186-193` is a bulk walk; a per-note `_adopt` would publish a half-built vault
once per note), and that `person.py:save:1252` delegates to `super().save()` and adopts nothing of
its own. The `functions_calling(files, "_adopt")` Table-2 row is a real surface oracle for a sixth
site added later without the door.

**Surfaces 1, 3 and 4 are test-side and open nothing.** Wall B's and Wall C's new batteries plant
mutation-capable imports — `from os import unlink` with the binding never called, `shutil`,
`tempfile`, `fcntl`, `filelock`, `mmap` — into a **scratch** module that is parsed by the wall's own
predicate and never imported or executed, and which is outside `python_files_under(PACKAGE_ROOT,
SCRIPTS_ROOT)` by construction (Task 12 says so in as many words when it explains why Wall A's probe
cannot be relocated there). Nothing plants an executable mutator into a shipped module. AC-5's and
AC-9's new authoring tasks add checks, not behaviour — and AC-9's is a **security** oracle in my
favour: it plants a sentinel string and asserts it absent from every refusal message, which is the
falsifier for the information-disclosure property I have been relying on the `REASONS` bound to
carry. Task 0's count-pin ruling is a verdict of GREEN-and-untouched on
`tests/test_loud_fail_harness.py:72-81`; I read that check and its comment at `:70-71` in the tree
and the "required subset, not a cardinality bound" reading is correct, so the sweep's silence is a
ruling rather than an omission.

**Both of my round-3 non-blocking notes are closed by name, and closed correctly.** The index bound's
two halves are now distinguished in Edge Cases and in `## Scope Boundary`: the wrong-VALUE half
closed (`person.py:432`, `:454`, `:459`, `:476` all end in `self._cache.get(...)`, verified, so a
partial index degrades to a MISS and can never resolve an identifier to the WRONG person — the
direction that matters for HAL9000's contact cascade), the iterate-a-live-mapping half explicitly
NOT closed (`person.py:get_by_phone:457` iterates `self._phone_index.items()`, verified this round).
The setuid triad is now D2.2's fifth bullet with the trade named rather than taken. Neither becomes
a requirement.

### Mitigations verified in place — no fence needed for these

1. **Fail-closed on an unobserved path** — D8 step 5's zero case and property 1 of `## Approach`'s
   total rule, AC-14 its oracle, D12.2 option (γ) rejected in writing. Still the single most important
   security property in the document.
2. **Stat-before-read ordering** (D5) — the stamp is deliberately older than the payload, so the
   failure direction is refusal rather than a silent lost update.
3. **No-clobber create as a kernel guarantee** rather than a check (D2, D4), plus `O_EXCL` on the temp
   file itself.
4. **`st_nlink > 1` refused** (D2.1) — a divergence with no correct answer, made loud, in both modes.
5. **Message and chain bounds** inherited by declaring no `__init__` (D11, Task 2), re-verified in
   `obsidian_schemas/errors.py:84-128` this round; `_env_setting` never interpolates a setting's VALUE
   into a message, only the variable's name (D6), so a lock directory carrying a person's name cannot
   reach a diagnostic — and AC-9's sentinel-string half now measures it.
6. **`allow_unverified_overwrite` degrades door 2u to door-1 strength, not to nothing** (D8d).
7. **Fail-loud on bad configuration over the WHOLE surface** — D6's `_env_setting` rule, AC-16, and
   `observe` cannot soften it (D9: "Layers 1 and 2 apply in both modes").
8. **`observe` announces itself once per process** (D6, D9, Task 10) — my round-1 note 1, still closed.
9. **The sentinel filename is a SHA-256 of the resolved path, never the note's name** (D3) — chosen for
   case-insensitive APFS, but it also means a lock directory, in the vault or under
   `OBSIDIAN_SCHEMAS_LOCK_DIR`, leaks no person's name to anyone who can list it.
10. **The repository cache is replaced rather than mutated in place under the RLock, through ONE
    door** (Edge Cases, AC-18, `functions_calling(files, "_adopt")` as its surface oracle) — an
    integrity improvement with no new surface, and its lock ordering is ruled non-nesting in both
    directions, so it adds no deadlock path.

### Required mitigations — re-emitted, all three byte-identical

All three remain requirements on `obsidian_schemas/vault_io.py`, a module Task 3 has not yet built —
confirmed absent from the tree this round, not inferred. Round 10 edited none of the sentences that
carry them: D2.2's four-step ordering paragraph, D2.3's one-resolved-path sentence and D3's M2
paragraph are intact and I read all three in place. Task 3 is still the plan's `vault_io.py` builder
and still carries the three `(M1)`/`(M2)`/`(M3)` clauses, so `landed: Task 3` is unchanged. Nothing
about what any of them requires has moved, so nothing about their `desc` moves either.

### Notes (non-blocking)

1. **Wall A's probe now sits in a live module in a form that does not announce itself at import, and
   what contains it is Wall A's own redness.** Round 10 moved Task 12's `Path("x").unlink()` from
   module scope into an existing function body of `obsidian_schemas/writer.py`, for a good reason
   (a module-scope statement raises `FileNotFoundError` on import, which `base_repository_subclasses`
   reaches by import, taking Wall D down beside Wall A). The side effect is that a probe left behind
   is no longer caught by the next import — it is a real `unlink` of a CWD-relative path inside the
   package's write path. I traced the containment rather than assuming it: the probe's whole purpose
   is to turn Wall A RED, `tests/test_write_routing.py` is inside THE FLOOR, and every task after 12
   ends in THE FLOOR GREEN — so a surviving probe is a red floor at the next task, not a shipped
   `unlink`. Detection is as strong as the module-scope form was, just one step later. Recorded
   because the reasoning is no longer visible at the probe, and explicitly NOT required.
2. **`_adopt` copies both mappings on every single-entity adoption**, so a batch of N saves against a
   loaded repository is O(N²) in dict entries. At this vault's scale (thousands of notes, foreground
   human-scale writes — risk row 7's framing) that is microseconds per save and not a denial of
   service; exocortex's batch ingest is the only caller that could feel it, and it would feel it as
   slowness, never as incorrectness. Named so the copy-on-write rule is adopted with its cost known;
   not a mitigation.
3. **Unchanged and still correctly declared:** `move_note` has no external-writer detection (R4 — door
   3's payload is an inode and its destination has no derivation read), and there is no audit trail of
   SUCCESSFUL writes, so a lost update inside R1's µs window leaves no record on our side. An audit
   log would not close R1. No mitigation for either.

```mitigation
kind: required
id: M1
desc: Layer 1 must apply the target's existing st_mode to the temp file's OWN DESCRIPTOR before any note bytes are written to it (and create with an explicit mode, never mkstemp's 0600 nor a bare umask-wide open), so a note keeps the permissions it had AND its content never exists on disk at a wider mode than the target's, not even for the span of the write and fsync.
landed: Task 3
```

```mitigation
kind: required
id: M2
desc: OBSIDIAN_SCHEMAS_LOCK_DIR must be validated at first lock acquisition and raise WriteFailedError when it is not an absolute usable directory, exactly as OBSIDIAN_SCHEMAS_LOCK_TIMEOUT and OBSIDIAN_SCHEMAS_WRITE_GUARD already do — never silently resolved against the process CWD.
landed: Task 3
```

```mitigation
kind: required
id: M3
desc: Every door must derive its temp-file directory, its replace target AND its lock sentinel's own DIRECTORY from the same resolved path the sentinel hash and the stamp registry are keyed on, or refuse a symlinked target with WriteFailedError — never leave a symlink replaced by a regular file, and never let two paths naming one real note key their sentinels in two directories.
landed: Task 3
```

```verdict
gate: threat-modeler
verdict: PROMOTE
date: 2026-08-09
model: claude-opus-5
note: Round 10 is an audit fold rather than a design move, and I checked each of its four surfaces for a new security category instead of assuming a fold cannot open one — none does. The only surface shipping CODE is BaseRepository._adopt, whose mutex inside a call graph that already takes a per-file flock is the one genuine deadlock shape round 10 could have introduced; it does not, because the repository lock spans the cache mutation ONLY (save holds it for base.py:331-333 and not around write_markdown_file, update_fields for :399-413 and not around its door-1 write), so neither lock is ever held while acquiring the other and there is no cycle in either direction — and I verified the four replaced sites are the identical three-line shape (base.py:331-334, :412-414, book.py:173-176, meeting.py:195-198) with load correctly excluded as a bulk walk. Surfaces 1, 3 and 4 are test-side: Wall B's and Wall C's new batteries plant mutation-capable imports into a SCRATCH module that is parsed and never imported or executed and that sits outside python_files_under(PACKAGE_ROOT, SCRIPTS_ROOT) by construction, so nothing plants an executable mutator into a shipped module, and AC-9's new check is a security oracle in my favour — a planted sentinel string asserted absent from every refusal message, which falsifies the information-disclosure property I had been leaning on the REASONS bound to carry. I re-ran the premise rather than reading it: vault_io.py and tests/test_concurrent_access.py are BOTH absent from the tree so Task 3 has not run, the widened grep for chmod|st_mode|umask|is_symlink|st_nlink|listxattr|O_EXCL|fchmod|mkstemp|NamedTemporaryFile|os.replace|os.link|fsync over obsidian_schemas/ and scripts/ returns zero, writer.py:236 is still a bare truncate-in-place write_text under :233's mkdir, errors.py:84-128 still holds the twelve-literal set with "write did not complete" live at :96 and the from-None bound, there are zero from-os imports and zero threading/RLock/filelock/fcntl references package-wide, and D2.2's four-step ordering paragraph, D2.3's one-resolved-path sentence and D3's M2 paragraph are all intact with Task 3 still carrying their three clauses. Both of my round-3 notes are closed by name and closed correctly — the index bound's two halves are now distinguished with the wrong-VALUE half verified closed at person.py:432/:454/:459/:476, and the setuid triad is named as M1's one honest exception with the trade stated rather than taken. All three fences are re-emitted BYTE-IDENTICAL because nothing about what they require has moved; they stand only because Task 3 has not run, and the series is converging rather than treadmilling — my round 2 raised the under-specification, round 9 discharged it surface by surface, round 10 touched none of it, and my two remaining notes are calibration-level observations I explicitly decline to require.
```

## Spec Review — 2026-08-09

**Recommendation: PROMOTE to ready**

Read cold from line 1 against `docs/spec-quality-bar.md`, not against the diff, and not against my own
previous round's gaps list. The frame, the three doors, the total precondition rule, D2.1's
cell-by-cell ruling, D10's vocabulary rulings, D12's Table 3 and every `## Scope Boundary` entry are
untouched by this review.

### Citation verification

Verified for MEANING at each site, read in the tree this round rather than taken from the injected
drift audit (which proves symbol existence only). All resolve and mean what the doc claims. The ones
this round's new text rests on, read in code:

- **The four existing single-entity adoption sites are the identical three-part shape the `_adopt`
  door replaces** — `base.py:save:331-334`, `base.py:update_fields:412-414`, `book.py:save:173-176`,
  `meeting.py:save:195-198` each set `_cache[key]`, `_file_map[key]`, then `_index_entity(...)`, in
  that order. `base.py:load:176-178` is the live `.clear()` triad and `:186-193` the key-by-key
  repopulate, so excluding `load` from the door is correct rather than convenient.
- **Task 8's `_file_map` argument holds end to end.** `person.py:create_stub:1429-1437` is the reuse
  branch, `:1436` calls `_writeback_identifier` (`person.py:1189`), which at `:1214` routes through
  `update_fields`, which resolves the path at `base.py:363` via `get_file_path:292`
  (`self._file_map.get(...)`) and raises `ValueError` at `base.py:366` **before** the write — i.e.
  before the phone is written back, which is exactly what Task 8's verify asserts against.
- **Walls B and C's zero-count premises.** Under `obsidian_schemas/` and `scripts/` the only `os`
  imports are the plain `import os` at `base.py:9`, `scripts/lint_vault.py:22` and
  `scripts/migrate_person_to_discuss.py:23`; there are **zero** `from os import` bindings and **zero**
  `shutil`/`tempfile`/`fcntl`/`filelock`/`mmap` imports under either root (all such imports live in
  `tests/`). D10.5's argument for why the two missing batteries were the invisible ones is measured,
  not asserted.
- **The count-pin ruling is right.** `tests/test_loud_fail_harness.py:72-81` is a hand-listed dict of
  six named exports with `assert len(six) == 6` at `:81`, and its own comment at `:70-71` reads "A
  seventh shared derivation extends this list; it is a required subset, not a cardinality bound on the
  module". GREEN-and-untouched is the correct verdict for a corpus Task 0 grows by seven names.
- **The round-9 citation defect is closed.** `tests/test_loud_fail_harness.py` declares exactly one
  test — `test_derivations_are_single_sourced:58` — with `_check_derivations_are_single_sourced:66`
  and `modules_using_ast(...)` at `:96`. Task 11 now names all three, so a builder can run it.
- `tests/derivations.py` symbol anchors are exact to the line (`python_files_under:88`,
  `_iter_functions:122`, `_own_body_nodes:148`, `_called_names:167`, `_is_write_call:189`,
  `base_repository_subclasses:312`, `load_file_implementations:355`, `_function_id_of:380`,
  `seam_invocation_closure:393`, `_SHARED_HELPERS:481`, `non_completed_write_sites:484`,
  `_is_falsy_return:518`, `modules_using_ast:528`), and `_is_write_call:189-195` is verbatim the
  `ast.Call` + `ast.Attribute` + `attr in {"write_text","write_bytes"}` form D7's call-form ruling and
  `## Verified Diagnosis` claim 6 are built on.
- `obsidian_schemas/writer.py` — exists-guard `:186-187`, WI-126 block gated at `:195`, read
  `:197-199`, `UnverifiableBodyError` `:200-209`, `existing_lines` `:210-214`,
  `model_to_frontmatter` `:217-218`, `frontmatter.copy()` `:220`, `mkdir` `:233`, `write_text` `:236`.
  `book.py:_load_file:57` (`try:` `:64`, read `:66`, wrong-type return `:70-71`, parse `:74`, entity
  branch `:75-76`, `except → _note_skip` `:77-80`). `tests/support.py:temp_dir:31` / `patcher:73` /
  `captured_logs:91` (whose default level IS `WARNING`, which is why Task 10's `level=logging.INFO` is
  load-bearing). `tests/test_loud_fail_write.py:52`, `:58`, `:103`, `:110`. `person.py:432`, `:454`,
  `:457`, `:459`, `:476`, `:1233`, `save:1252` delegating at `:1266-1267`.

One phrasing looseness, not drift, under non-blocking notes below.

### Bar check

Walked every check of `docs/spec-quality-bar.md` (the doc's own list is the count). Spec satisfies the
bar. What I re-derived rather than inherited:

- **Check 5 / task shape.** Seventeen canonical `- [x] **Task N — …**` definitions, ordinals unique
  (0–16), execution order stated where it differs from the ordinals. `landed: Task 3` resolves.
- **Fold records (WI-216).** All three `desc` values are byte-identical to the latest speaking
  `## Threat Model` round (round 4), so the records are fresh. I found each `design` and `work` quote
  where it claims to be and read the surrounding text: M1 → D2.2's ordering blockquote (`fchmod` on
  the descriptor first, no `chmod` after the write) plus Task 3's `(M1)` clause; M2 → D3's validation
  paragraph plus Task 3's `(M2)` clause; M3 → D2.3's one-resolved-path sentence, now including the
  sentinel's own DIRECTORY, plus Task 3's `(M3)` clause. All three quotes are faithful, and all three
  mitigations are satisfied — each also carries an oracle that can distinguish the required behaviour
  from its near-miss (AC-15's `os.fsync`-time temp-mode probe, AC-16's whole-surface config battery,
  AC-17's two-parents-one-note case).
- **Counting walls (WI-235).** All five predicates declared in D10.1 now ship a MATCHED and a
  NOT-matched battery driven through the wall's own function, and Task 12 derives the battery list
  from that set with an explicit instruction not to inherit "three". Wall C's MATCHED imports and Wall
  E's MATCHED functions are generated by iterating the module set and `COMMIT_FUNCTION_NAMES`
  respectively, which is the derive-the-fixture-space form rather than a hand-picked sample.
- **Write-Targets coverage.** Every plan task's target is a declared `writes` path (including Task
  12's three probe targets), and every declared path has a task. No fence declares a path no task
  writes. No plan-task verify or `## Verification` bullet writes outside `write_authority`: Task 0's
  and Task 13's one-liners are read-only prints/asserts and say so, Task 6 runs `--help`, Task 16
  edits nothing, and every state-writing step is a close-out run outside the cage.
- **Conscious-pin sweep (WI-229).** Three corpora named with their declaring symbols and a verdict
  each — `REASONS` (no `len()` pin; the prose pin at `errors.py:84` de-pinned by Task 2), the
  `BaseRepository` subclass corpus (`== 4` / `== 3`, untouched), and `tests/derivations.py`'s exports
  (the `six` pin, GREEN-and-untouched). I swept for a fourth: no check anywhere in `tests/` pins a
  count over the package's python-file set, so `vault_io.py` joining `python_files_under` moves no
  pin, and the one file-set constraint that does exist
  (`tests/test_vault_path_required.py:321`'s rglob) is already a hard constraint on Task 3 (D12.5 2a).
- **Check 10.** Eighteen well-formed `criteria` fences, all `kind: test`, all zero-arg top-level
  names. I re-walked the fence set independently of `## Acceptance Criteria — Authoring Map`: every
  one of the eighteen `check` names is now authored by a named task into a declared write-target
  module, including AC-5 (Task 8, widened to the no-clobber create and the book/company halves) and
  AC-9 (Task 10, widened to the loud-and-bounded half). The map agrees with my walk row for row, and
  Task 13's closing rule makes an unauthored `check` a hand-back rather than a test invented at exam
  time — with a read-only command that would have caught the nine-round AC-5/AC-9 miss.

### Build-runner dry-run

Walked the Implementation Plan top to bottom in checkbox order (1, 0, 2–7, 16, 8–15). No judgment-call
gaps. The three questions I put to it: *where does the tenth cache-mutation site take its lock?* —
Task 8 names `self._adopt(...)` and forbids a bare `self._cache[key] = entity`, with the `_file_map`
consequence spelled out; *how many batteries does Task 12 ship?* — five, derived from D10.1's
predicate set, with the two new ones written out shape by shape; *what does a builder do when a wall
or a table row disagrees?* — hand back, with the vocabulary, both tables and WI-020's battery all
named as off-limits repairs.

### Minor notes (non-blocking)

- **`## Verification`'s `_adopt` row states the wrong count.** It reads "`functions_calling(files,
  "_adopt")` is asserted EQUAL to the **six** adopting functions, so a **seventh** site…", while
  D10.6 Table 2, Task 11, Task 7, Edge Cases, Risk row 18 and the round-4 threat model all say
  **five**, and both Table 2 and Task 11 name the five (`base.py:save`, `base.py:update_fields`,
  `book.py:save`, `meeting.py:save`, `person.py:create_stub`) with `base.py:load` deliberately
  excluded. Not blocking: the row names no functions and points at Table 2 as the authority, and the
  builder's instruction (Task 11) is explicit and adjacent — but it is a counting slip on the exact
  surface this round's fold was about, and it should be corrected at the next touch of the document.
- **`## Mitigation Folds`' preamble points at the wrong round.** It says the latest speaking
  `## Threat Model` round is "round 2, at the end of this document"; it is now round 4. Mechanically
  harmless — the three `desc` values are byte-identical across rounds 2, 3 and 4, so freshness is
  unaffected — but the pointer will read as stale to the next gate.
- **`## Write Targets`' `why` for `tests/test_write_routing.py`** groups `filesystem_mutation_uses`
  with the two batteries that actually arrived this round; only `os_module_attribute_uses` and
  `module_import_uses` are round-10 additions.
- **Edge Cases describes four re-check sites by the wrong form.** "every index lookup ends in
  `self._cache.get(cache_key)` — … the re-checks at `book.py:194`, `meeting.py:256`, `:299`, `:314`":
  those four are `[self._cache[k] for k in cache_keys if k in self._cache]`, a membership re-check
  rather than a `.get`. The asserted property — a partial index degrades to a MISS and never resolves
  to the wrong entity — is TRUE at all four, so this is a form description, not a wrong claim.
- **Task 8 does not say how the recovery obtains `file_path` for its `_adopt` call.** It is derivable
  (`BaseRepository.save` builds `@{name}.md` under `vault_path` at `base.py:317-319`), and the four
  existing sites all pass the path they just wrote, so this is one line rather than a decision — but
  naming it would remove a derivation from the one task that adds the fifth caller.

### Carried-forward notes

My own previous round's three non-blocking notes are all actioned: the Wall-A probe now has its
placement clause (inside an existing function body, with the import-time reason written down), Task 0
carries the count-pin ruling with its verdict, and the regression-list note asked for no change and
gets none. The round-3 threat model's two open notes are closed and I re-read each rather than
accepting the round-10 narrative — Edge Cases and `## Scope Boundary` now distinguish the index
bound's two halves (wrong-VALUE closed, iterate-a-live-mapping explicitly not), and D2.2's fifth
bullet plus the `## Verification` mode row name the setuid/setgid/sticky triad as M1's one honest
exception. Still open, all from the round-4 threat model and all explicitly not required by their
author:

- **Threat model round 4, note 1** — Wall A's probe now lives inside a live module in a form that does
  not announce itself at import, so a surviving probe is caught by the next task's floor rather than
  by the next import. Detection is one step later, not absent; recorded because the reasoning is no
  longer visible at the probe. Still open.
- **Threat model round 4, note 2** — `_adopt` copies both mappings on every single-entity adoption, so
  a batch of N saves is O(N²) in dict entries. Microseconds at this vault's scale; exocortex's batch
  ingest is the only caller that could feel it, and only as slowness. Named so the copy-on-write rule
  is adopted with its cost known. Still open.
- **Threat model round 4, note 3** — `move_note` has no external-writer detection (R4) and there is no
  audit trail of successful writes, so a lost update inside R1's µs window leaves no record on our
  side. Both re-confirmed as correctly declared with "no mitigation" stated. Recorded as requiring no
  action rather than deferred.

### On the series — the fold landed, so this is a PROMOTE and not a fourth round

My rounds were monotone and, at the third, kept landing new sites of one discipline: *an enumeration
this document owns, maintained from the author's memory over the PRE-CHANGE tree, where the surface it
enumerates is closed, declared and derivable from its own source.* I proposed the audit fold rather
than a fourth site list. Round 10 ran it, and I checked each of the four surfaces at its declaring
source rather than reading the round-10 narrative: the wall set is closed at D10.5's opening rule over
D10.1's predicate set with Task 12 deriving its battery list from it; the cache-adoption surface is
made total by construction with one `_adopt` door plus a Table-2 set-equality oracle, which is the
stronger of the two shapes I offered; the acceptance set is closed by a derived authoring map with an
unauthored `check` as the loud case; and the count-pin surface is widened from "corpora this item
EDITS" to "GROWS OR EDITS", with the third corpus named and ruled. The citation defect and every
non-blocking note are closed by name. The four remaining observations above are description-level and
none of them changes what a builder builds, so buying a fifth review round would be the regress
signature rather than progress.

```verdict
gate: spec-reviewer
verdict: PROMOTE
date: 2026-08-09
model: claude-opus-5
note: The audit fold I proposed last round LANDED, and I verified each of its four surfaces at its declaring source in code rather than reading the round-10 narrative — D10.5 now states the battery obligation ONCE over D10.1's five-predicate set with Task 12 deriving its list from it and Walls B and C written out shape by shape (their invisibility is measured, not argued: I confirmed zero `from os import` bindings and zero shutil/tempfile/fcntl/filelock/mmap imports under either root, the only os imports being plain `import os` at base.py:9, lint_vault.py:22 and migrate_person_to_discuss.py:23); the cache-adoption surface is total BY CONSTRUCTION through one BaseRepository._adopt door with functions_calling(files,"_adopt") pinned as a set-equality Table-2 row and a Table-1 empty row making it a measured delta, and I confirmed the four replaced sites are the identical three-part shape (base.py:331-334, :412-414, book.py:173-176, meeting.py:195-198) with load correctly excluded as a bulk rebuild (:176-178, :186-193), and that Task 8's _file_map argument holds end to end (person.py:1436 -> _writeback_identifier:1189/:1214 -> update_fields -> get_file_path base.py:363/:292 -> ValueError at :366 before the phone is written back); the acceptance set is closed by a DERIVED authoring map, and my own independent walk of all eighteen criteria fences found every check name authored by a named task into a declared write-target module, with AC-5 and AC-9 renamed to the AC's name AND widened to their full desc rather than the criterion narrowed to what a check happened to cover; and the count-pin surface is widened to corpora this item GROWS, with tests/derivations.py's exports named and the pin at test_loud_fail_harness.py:72-81 ruled GREEN-and-untouched on that check's own comment at :70-71, which I read. The round-9 citation defect is fixed to the real name and anchors (test_derivations_are_single_sourced:58, _check_derivations_are_single_sourced:66, modules_using_ast at :96), all three fold records are fresh (desc byte-identical to the latest speaking round 4) with their design and work quotes read in place and faithful and each mitigation carrying an oracle that distinguishes it from its near-miss, every plan task's target is a declared write target with no verify command writing outside write_authority, and both of the round-3 threat model's notes are closed correctly. Four description-level notes remain and none changes what a builder builds — chiefly `## Verification`'s _adopt row saying "six adopting functions / a seventh site" where Table 2, Task 11, Task 7, Edge Cases and Risk row 18 all say five and name them — so a fifth round would be the regress signature rather than progress.
```

## Build Log — 2026-08-10

Executed cold-start by the build-runner gate. **Shell liveness probe FIRST** (WI-228 P4): `echo hi`
→ `hi`, so `Bash` execs and nothing below is written from source-reads.

### Task 1 — precondition gate and baseline

`.venv/bin/python -c "import filelock; print(filelock.__version__)"` → **`3.32.2`**. The D0.1
precondition landed as the conductor committed it; no abort.

**`baseline: 617 passed`** — THE FLOOR (`.venv/bin/python -m pytest tests -q`) against the untouched
tree, captured before the first edit that moves it. Every later "the count did not go down" claim
below is measured against this number and not against `CLAUDE.md`'s drift-prone anchor.

### Task 0 — the harness predicates, EXECUTED against the untouched tree

`tests/derivations.py` gained `SCRIPTS_ROOT`, the provenance-partitioned vocabulary
(`DOOR_NAMES`, `PATH_MUTATION_NAMES`, `MODULE_MUTATION_NAMES`, `FS_MODULES`, `OS_READONLY_NAMES`,
`COMMIT_FUNCTION_NAMES`) and the five predicates. `_is_write_call` was widened to
`{"write_text", "write_bytes"} | DOOR_NAMES` and **nothing else about it moved** — its
`isinstance(node.func, ast.Attribute)` gate is intact. `load_file_implementations` and
`base_repository_subclasses` were consumed as-is.

**Table 1, every row RUN rather than predicted:**

| Predicate | Returned | vs Table 1 |
|---|---|---|
| `filesystem_mutation_uses` | **exactly 17** — `writer.py:233,236,283,333,365`; `base.py:390`; `person.py:1543,1554,1652,1769,1845,1912`; `lint_vault.py:876,894,1034,1038`; `migrate_person_to_discuss.py:104` (14 `write_text` + 2 `mkdir` + 1 `rename`) | **MATCH** |
| …`str.replace` / `dict.copy` nodes | **`[]`** — zero, both | **MATCH** — the row that proves the discriminator |
| `os_module_attribute_uses` | 3, all `environ` — `base.py:97`, `lint_vault.py:52`, `migrate_person_to_discuss.py:160`; zero `from os import` bindings | **MATCH** |
| `module_import_uses(…{shutil,tempfile,fcntl,filelock,mmap})` | `[]` | **MATCH** |
| `functions_calling("stat_stamp")` | `set()` | **MATCH** (RED, expected) |
| `functions_calling("_adopt")` | `set()` | **MATCH** |
| `functions_calling("parse_markdown_file")` | exactly the three loaders, and `== load_file_implementations(...)` → `True` | **MATCH** |
| `falsy_returns_in(PACKAGE_ROOT, COMMIT_FUNCTION_NAMES)` | `[]` (vacuous — `vault_io.py` does not exist) | **MATCH** |
| THE FLOOR with `DOOR_NAMES` already inside `_is_write_call` | **617 passed** = Task 1's baseline | **MATCH** — the widening is DERIVED additive, not hoped |

`tests/test_loud_fail_harness.py`'s `six = {...}` / `assert len(six) == 6` **stays GREEN and
unedited**, exactly as Task 0's count-pin ruling requires: it is a required SUBSET of six named
exports, not a cardinality bound, and this task added a seventh through eleventh.

### DEVIATION — Table 1's Wall B row vs D10.5's Wall B battery (raised, not resolved by me)

The two disagree about **where `os_module_attribute_uses` filters `OS_READONLY_NAMES`**, and no
implementation satisfies both:

- **D10.6 Table 1** pins the predicate as returning "3 uses, all `environ`", and three independent
  data-audit groundings read it the same way — most explicitly at the round-10 spec review, "an
  `os_module_attribute_uses` that never implements the `ast.ImportFrom` collection **returns the
  identical three `environ` uses**". D10.3 matches this too: it states the filter only on the
  `ImportFrom` arm ("where `n ∉ OS_READONLY_NAMES`") and states Wall B's own assertion as "returns
  only attributes in `OS_READONLY_NAMES`" — a live, non-vacuous claim against those three reads.
- **D10.5's Wall B NOT-matched table** instead pins `os.environ.get("X")`, `os.getenv`, `os.getcwd`,
  `os.sep`, `os.path.join` and `os.fspath` as **NOT matched by the predicate**, which requires the
  attribute arm to filter — under which Table 1's row returns `[]` and D10.3's assertion is vacuous.

**Resolved toward Table 1**, because Task 0's abort trigger is a Table-1 mismatch and Table 1 is the
pinned artifact three gates executed. The attribute arm returns every `os.<attr>` use; the
`ImportFrom` arm filters. So Task 0's Wall B row **matches exactly** and no hand-back was owed there.

Task 12's battery is then authored against the predicate as pinned: Wall B's rule
(membership of `OS_READONLY_NAMES`) is written ONCE as `_os_violations` in
`tests/test_write_routing.py` and **the live wall and its battery both call it**, so the battery
still drives the same code path the wall takes rather than a second copy of the matching logic. Every
shape in both D10.5 tables is driven; only the layer at which the readonly members are asserted
"not a violation" differs from D10.5's literal wording. **This is a spec-internal contradiction, not
a defect I introduced, and it is the one thing in this build a reviewer should rule on.**

### Task 2 — the three exceptions

`StaleEntityWrite`, `ExternalWriteConflict`, `NoteAlreadyExists` in `obsidian_schemas/errors.py`,
each a `LoudFailError` **declaring no `__init__`**, with their three reason literals added to
`REASONS` in the SAME edit. The `:84` comment is de-pinned to a predicate with no number in it. All
three exported from `obsidian_schemas/__init__.py`.

*Count-pin sweep, all three corpora:* (i) `REASONS` — grepped its declaring symbol across the tree
and read every file it reached; the only pin is the prose one, and **no test asserts
`len(REASONS)`** (confirmed by the sweep, not assumed); (ii) the `BaseRepository` subclass corpus —
`tests/test_loud_fail_parse.py:300` (`== 4`) and `:301` (`== 3`) **stay true and unedited**, verified
at Tasks 0, 11 and 15; (iii) `tests/derivations.py`'s exports — ruled in Task 0.

*Verify:* the `NoteAlreadyExists` construction raised with a bounded message; floor GREEN at 617.

### Task 3 — `obsidian_schemas/vault_io.py`

D1–D6 built: `NoteStamp`, `note_lock`, `read_note`, `write_note`, `create_note`, `move_note`,
`ensure_dir`, the registry and its six accessors, `guard_mode`, and the three env readers.

Hard constraints **verified by grep rather than by intent**: no `expanduser`, no `Path.home()`, no
`/Users/` literal (D12.5 item 2a — the file joins
`tests/test_vault_path_required.py:test_no_implicit_vault_path_defaults`'s universe); no `import ast`;
and **exactly ONE real `os.environ` access** (M2) — `grep -n "os.environ"` returns three lines, of
which two are prose and one is `_env_setting`'s own `os.environ.get(name)`.

All three `kind: required` mitigations landed here:
- **M1** — `os.stat` (with the `st_nlink > 1` refusal) → `os.open(…, 0o600)` → **`os.fchmod(fd, mode)`
  as the first operation on the descriptor** → write → `fsync` → close → terminal form. There is no
  `os.chmod` after the write. A fresh create opens at `0o666` so umask masking reproduces exactly
  what `Path.write_text` gives today.
- **M2** — one `_env_setting(name, parse, validate, default)` helper.
- **M3** — one `Path(path).resolve()` per door, keying the sentinel's hash **and its directory**, the
  registry, the temp directory, the precondition and the terminal syscall; `move_note` refuses a
  symlinked source.

Four checks authored into `tests/test_concurrent_access.py`, each taking its scratch vault from
`tests/support.py:temp_dir`.

**Two design corrections found by running the checks, not by reading:**
1. **`_FILE_LOCKS` was keyed on the note path**, so a changed `OBSIDIAN_SCHEMAS_LOCK_DIR` was masked
   by an instance cached under the old home — AC-17(c) caught it. The cache is now keyed on the
   SENTINEL path, the sentinel is re-derived on every outermost acquisition, and release goes through
   the instance that acquisition actually took (a thread-local `_held_locks` map).
2. **`move_note` self-acquires** both locks in sorted resolved-posix order rather than requiring a
   caller-held lock, because Task 9 calls it bare with no surrounding `note_lock`. D3's
   "refuses when the lock is not held" survives as a post-acquire invariant in `_move_locked`.

*Deviation, small and named:* AC-16 requires each refusal's message to carry **the variable's name
and not its value**. `bounded_message` renders `path=` as the VALUE and `bounded_cause` projects a
cause to its class name only, so neither slot can carry the name — and Task 3 forbids minting a
fourth `REASONS` literal. The name therefore rides in `declared_type`, the one slot rendered
verbatim, via a single `_bad_setting` helper. A cleaner home would be a reason literal per setting,
which is a Task-2-shaped edit this task is explicitly forbidden to make.

*Verify:* `tests/test_concurrent_access.py` GREEN except AC-15's door-2 half, which **cannot** be
green before Task 7 — that is the Task-3-authors / Task-13-owns-the-oracle split the plan describes,
not a failure. Floor: 620 passed, 1 failed (that half).

### Tasks 4–6 — door-1 routing, 13 sites

Every door call is a **module attribute** (`from obsidian_schemas import vault_io`, then
`vault_io.write_note(...)`), which is the whole of D7's call-form ruling and what keeps
`_is_write_call`'s `ast.Attribute` gate matching. Each site keeps its `FileNotFoundError` guard,
its parse, its dedup no-ops, its falsy returns and its `LoudFailError` re-raise exactly where they
were; nothing moved into a nested function.

- **Task 4** — `writer.py:update_frontmatter_field/_fields/roundtrip_file`, `base.update_fields`.
  Table 3a row 1 landed: `tests/test_loud_fail_parse.py` part 3 injects at `vault_io.write_note`,
  **every assertion byte-identical** including `caught.value.__cause__ is boom`. Part 4 NOT edited —
  `read_note` wraps nothing, so the `UnicodeDecodeError` still reaches the site's own `except`.
  *Verify:* the three named modules GREEN (211 passed). **The derivation half was measured:**
  `functions_reserializing_parsed_frontmatter` = 4, `loose − write` = `{write_markdown_file}`.
- **Task 5** — the six `person.py` body-writer sites. Table 3a row 2 landed the same way. Before the
  row, the module failed at exactly P1 and nowhere else, with the `SiteId` classification map already
  showing no unclassified and no stale entries — i.e. the expected pre-edit failure and nothing more.
  *Verify:* the three named modules GREEN.
- **Task 6** — `lint_vault.py:876,894` under ONE reentrant `with vault_io.note_lock(fpath):` spanning
  both, each write carrying its own freshly-read stamp; `migrate_person_to_discuss.py:104`.
  *Verify:* floor GREEN; `migrate_person_to_discuss.py --help` exits 0.

### Task 7 — door 2, the adoption door, the loaders, the cache lock

D8 (a)–(e) installed inside `write_markdown_file`: the lock spans the stamp lookup, the WI-126
guard's read and the commit; the `overwrite=False` guard at `:186-187` is deleted; the `mkdir` at
`:233` is `vault_io.ensure_dir`; `allow_unverified_overwrite` threaded through all four `save()`s.

`BaseRepository._adopt(name_key, entity, file_path)` is the ONE adoption door. All four existing
single-entity sites converted; `load` deliberately does NOT call it (a bulk rebuild — it fills fresh
local mappings across the walk and rebinds ONCE, and the live `self._cache.clear()` is deleted rather
than locked); `update_fields`' removal half, `refresh`, `_note_skip` and the two `_skipped` readers
take the lock. The lock never spans a filesystem write, so no thread holds it while acquiring
`note_lock`.

Stamp recording landed in **all three** loaders — `base.py`, `book.py`, `meeting.py` — with the stat
as the first statement INSIDE each existing `try` and above that function's first read, and
`remember_snapshot` only on the entity-returning branch. Nothing recorded on the wrong-`type` early
returns, nothing in the `except` branches. Table 3a rows 3–6 landed.

*Scope correction made during the task:* an earlier pass added `_clear_indexes()` calls to `load()`
that `load()` never had. Reverted — the spec's rule for `load` says nothing about indexes, and Edge
Cases explicitly declares the subclass indexes OUT of AC-18's scope. Behaviour is unchanged from
today there.

*Two check-fixture corrections, both mine and both instructive:* AC-15's and AC-11's door-2 fixtures
originally SHRANK the body, so `BodyTruncationError` fired before the stamp precondition could. That
is D8 step 6 running before step 7 exactly as specified — the escape does not surrender the WI-126
guard — so the fixtures were rewritten to grow the body. AC-11's meeting note also had to be named
`Meeting 20260809 - Standup.md`, the filename `MeetingRepository._get_file_name` derives, or `save()`
would mint a sibling rather than write back the note it loaded.

### Task 16 — the whole floor RUN, complete red set pinned

`.venv/bin/python -m pytest tests -q -rf`:

```
=========================== short test summary info ============================
FAILED tests/test_writer.py::TestWriteMarkdownFile::test_no_overwrite_by_default
1 failed, 622 passed in 2.65s
```

**Exactly the one check Table 3b names** (Table 3a row 7, owned by Task 14), raising
`NoteAlreadyExists` where the test still expected `FileExistsError`. Passing count 622 ≥ baseline
617 − 1. **No additional failing check, and no Table-3b row green that should have been red — so no
hand-back was owed.** Both WI-020 acceptance modules GREEN.

### Tasks 8–10 — door 2c, door 3, observe mode

- **Task 8** — `create_stub` catches `NoteAlreadyExists`, re-reads that one path via `_load_file`,
  and adopts through **`self._adopt(...)`, the fifth caller of the door** — not a hand-written
  `self._cache[key] = entity`, because the reuse branch's `_writeback_identifier` routes through
  `update_fields` → `get_file_path` → `self._file_map`, and a `_cache`-only recovery would raise
  `ValueError` before the phone was written back. Re-raises if the re-read yields no entity.
  AC-5 covers all three halves.
- **Task 9** — door 3 replaces the `dest.exists()` + `rename` TOCTOU; `:1034`'s `mkdir` →
  `vault_io.ensure_dir`. `"mkdir"` was NOT dropped from the vocabulary.
- **Task 10** — `observe` needed no new code (Task 3 built it); AC-9 covers both halves, including
  that exactly ONE INFO line naming the mode is emitted across TWO writes.

### Task 11 — the predicates RE-RUN, Table 2 pinned

| Predicate | Returned | vs Table 2 |
|---|---|---|
| `filesystem_mutation_uses` | modules = `['obsidian_schemas/vault_io.py']` — and nowhere else | Wall A **GREEN**, MATCH |
| `os_module_attribute_uses` outside the door | the same 3 `os.environ` (lines shifted to `base.py:100`, `lint_vault.py:55`, `migrate:165` by this item's own edits) | Wall B **GREEN**, MATCH |
| `module_import_uses` | `[('obsidian_schemas/vault_io.py', 'filelock')]` | Wall C **GREEN**, MATCH |
| `functions_calling("stat_stamp")` / `…("remember_snapshot")` | each ⊇ the three loaders → `True` | Wall D(i) **GREEN**, MATCH |
| `functions_calling("parse_markdown_file")` | `== loaders` → `True` | Wall D(ii) **GREEN**, MATCH |
| `functions_calling("_adopt")` | **EXACTLY** `base.py:save`, `base.py:update_fields`, `book.py:save`, `meeting.py:save`, `person.py:create_stub` — `base.py:load` deliberately absent | MATCH (set equality) |
| `falsy_returns_in(…, COMMIT_FUNCTION_NAMES)` | `[]`, now over a REAL `vault_io.py` | Wall E **GREEN**, MATCH — the non-vacuous green |
| `functions_reserializing_parsed_frontmatter` | 4 | MATCH |
| `functions_parsing_then_writing − …` | `{write_markdown_file}` | MATCH |
| `non_completed_write_sites` | 8 | MATCH |
| `base_repository_subclasses` / `load_file_implementations` | 4 / 3 | MATCH, both pins unedited |

**No row differed, so no hand-back.** `tests/test_loud_fail_harness.py` still GREEN — the new
predicates live in the module already permitted to name `ast`.

### Task 12 — the routing wall

`tests/test_write_routing.py`: Walls A–E and **five** batteries, the list derived from D10.1's
predicate set. Each battery plants a scratch module (parsed, never imported — outside
`python_files_under(PACKAGE_ROOT, SCRIPTS_ROOT)` by construction) and drives it through the same
function the live wall calls. Wall C's MATCHED imports are GENERATED by iterating the module set;
Wall E's MATCHED functions are GENERATED by iterating `COMMIT_FUNCTION_NAMES` with **set equality**
asserted. The three round-5 near-misses ship, `p.replace(q)` carrying its R10/D10.3 comment, as does
`snapshot_stamp`'s deliberate `None` and the implicit-fall-off-the-end declared limit.

*One battery-fixture correction:* Wall E's nested-function near-miss initially planted a function
NAMED `write_note` inside a differently-named parent, which the predicate matched — correctly, since
`FunctionId.name` is the last dotted segment. D10.5's actual claim is the inverse (a falsy return in
a nested function **of** `write_note`), and the fixture now plants that shape.

**Three mutate-and-observe probes, each RUN and each reverted:**

| Probe | Result |
|---|---|
| `Path('x').unlink()` **inside `write_markdown_file`'s body** (never module scope — a module-scope unlink raises on import and would take Wall D down alongside Wall A) | Wall A **RED**: `obsidian_schemas/writer.py:205 (unlink)` |
| delete `vault_io.remember_snapshot` from `book.py:_load_file` | Wall D(i) **RED**, naming `book.py:BookRepository._load_file` |
| `return None` in `vault_io.write_note` | Wall E **RED**, naming `vault_io.py:write_note#0` |

All three probe targets are declared `## Write Targets` paths, as the plan requires. *Note for the
conductor:* `git checkout` is not available inside the cage (`.git` is outside the sandbox's write
set — `Unable to create ... index.lock`), so the three probes were reverted by direct edit and the
revert was verified by re-running the floor rather than by `git status`.

### Tasks 13–15 — the battery, row 7, regression

Task 13 completed `tests/test_concurrent_access.py` (AC-1, 2, 3, 4, 8, 10, 14). **17 checks, all
GREEN.** AC-1 observes at `os.fsync` — the instant a truncate-in-place writer would be exposing a
half-written note — and asserts the target holds the complete old bytes.

**The AC → authoring-task walk was DERIVED, not remembered.** The read-only command Task 13
prescribes returns `checks found: 18`, `MISSING: []` — every `check` in every `criteria` fence
resolves to a top-level `def` in a `## Write Targets` module, so nothing is left to fail the exam at
`building → done`.

Task 14 closed row 7 and re-ran the axis-γ sweep (`grep -rn 'FileExistsError' tests/
obsidian_schemas/ scripts/`). It now returns: this test (updated); `writer.py:199`, a docstring
naming the break; and `vault_io.py:519,686`, which are the door's own kernel-`FileExistsError` →
`NoteAlreadyExists` conversion sites. The two `writer.py:180,187` hits the plan predicted are gone,
removed with the `overwrite=False` guard in Task 7.

**Task 15 — THE FLOOR: `637 passed` in 3.36s, ZERO failures.** Against Task 1's captured baseline of
617, that is +20 and never a decrease. The WI-238 derived sweep over `## Write Targets` paths and
their declared symbols returned 13 modules: `test_concurrent_access`, `test_identity_index`,
`test_loud_fail_harness`, `test_loud_fail_load`, `test_loud_fail_parse`, `test_loud_fail_write`,
`test_name_cleaning`, `test_repositories`, `test_resolve_or_create`, `test_vault_path_required`,
`test_wi126_body_preservation`, `test_write_routing`, `test_writer`. The floor runs all 20 test
modules regardless, and the asserted property is the floor's own zero-failure exit.

### What a reviewer should look at first

1. **The Wall B filter-placement contradiction above** — the one open spec question, resolved toward
   the pinned table with the reasoning written out.
2. **`declared_type` carrying a config variable's name** in `vault_io._bad_setting` — a small,
   deliberate misuse of a WI-020 slot, forced by Task 3's ban on minting a fourth `REASONS` literal.
3. `move_note`'s self-acquisition and the sentinel-keyed `_FILE_LOCKS` cache — both are departures
   from the literal text of D3, both forced by behaviour the checks caught.

### NOT done here — conductor close-out, outside the cage

The five `## Verification` CLOSE-OUT steps are untouched by design: the live disposable-vault
concurrency exercise, the widened Obsidian sentinel re-check, the three consumer-audit sweeps (3a
`FileExistsError`, 3b the permission assumption, 3c R12's one-process sequence), `CLAUDE.md` +
`SESSION_LOG.md`, and `README.md:317-338`'s round-trip recipe. All five are project-root or
cross-repo paths outside `write_authority`; a caged edit to any of them is reverted at the merge
boundary, which is exactly why they are close-out steps and not plan tasks. **`README.md`'s
documented recipe now raises `NoteAlreadyExists` until step 5 lands** — AC-14 pins both that break
and its `allow_unverified_overwrite=True` answer.

### Revision 1 — 2026-08-10, closing the code-review REVISE

Shell liveness re-probed first (`echo hi` → `hi`). Baseline for this round: the floor at
**`637 passed`**, the number Task 15 landed.

**The blocking finding, and it was real.** `_commit` discarded `os.write`'s return. `os.write` is
`write(2)` and returns the count actually written; a volume filling mid-write writes what fits and
returns that count rather than raising `ENOSPC`. The fragment was then `fsync`ed, `os.replace`d
over the target and its directory entry fsynced — a truncated note committed atomically and
durably, with `write_markdown_file` stamping a fresh snapshot over the corrupted bytes and nothing
raised. That is a **regression against pre-WI-004 behaviour**: `Path.write_text`, what all 17
routed sites called before this build, loops on short writes inside `io.BufferedWriter` and is loud
at flush. It falsifies AC-1, which certifies a commit is a COMPLETE note and not merely an
indivisible rename.

**The fix.** A new `vault_io._write_all(fd, payload)` loops until the payload is exhausted and
raises on a zero-byte return (no progress). It raises a plain `OSError` **deliberately**, so
`_commit`'s existing handler — the one place that closes the descriptor, discards the temp file and
re-raises as `WriteFailedError` — is the single exit. The refusal therefore never reaches
`os.replace`: the target keeps its old bytes and no temp file survives. Layer 1's module-docstring
claim was widened to say so rather than left to be inferred.

**The check, authored FAILING-TEST-FIRST (WI-029) rather than alongside.** AC-1's own check
`test_every_door_commits_atomically` gained the property, so the criterion the finding falsified is
the one that now pins it. Its oracle is the target's own OLD bytes, written by the check.
**Mutate-and-observe, RUN:** reverting `_write_all(fd, payload)` to the reviewed
`os.write(fd, payload)` takes the check RED at the exact assertion —
`AssertionError: a write that never delivered its whole payload must raise WriteFailedError, not
commit what landed` — and restoring it takes it green. The defect is pinned to falsifiable code,
not to a reading.

Both arms of the shape are driven, and the **near-miss is load-bearing**: the first stub goes short
*and then makes no progress* (the fill-up shape — proving the loop resumes from the offset AND that
it refuses instead of spinning), while a second stub returns short but keeps progressing 64 bytes at
a time and must still commit the COMPLETE note. Without that second half, a naive
"raise whenever `os.write` returns `< len(payload)`" would pass the first assertion while breaking
every real write on a short-returning descriptor.

**Recommended finding 2 — `ensure_dir` breaking the door contract — taken, not narrowed.**
`ensure_dir` is a member of `COMMIT_FUNCTION_NAMES`, i.e. the spec's own wall already treats it as a
door, so weakening the docstring instead of the code would have been the wrong direction. Its
`mkdir` now refuses as `WriteFailedError`, which makes `except LoudFailError` total over the doors
for `write_markdown_file` (`writer.py:273`) and `quarantine_garbage` (`lint_vault.py:1043`) — both
of which carry no `OSError` handler, so this is a refusal-type change and nothing else.

*The coupling this exposed, and why both internal callers moved with it.* `_configured_lock_dir`
and `note_lock` each caught `OSError` around their `ensure_dir` call; left alone, `ensure_dir`'s new
`WriteFailedError` would have escaped **carrying the directory in `path`** — and `path` renders the
VALUE, which is precisely what M2 keeps out of a message when the lock dir can carry a person's
name. Both excepts widened to `(OSError, WriteFailedError)`: `_configured_lock_dir` re-raises
through `_bad_setting` (name in `declared_type`, cause projected to a class name), and `note_lock`
re-homes onto the NOTE path. Verified by execution, not by reading —
`OBSIDIAN_SCHEMAS_LOCK_DIR=<a regular file>` yields
`write did not complete; declared_type='OBSIDIAN_SCHEMAS_LOCK_DIR'; cause=WriteFailedError`, with
the name present and the value absent; AC-16's `refuses("OBSIDIAN_SCHEMAS_LOCK_DIR", str(a_file))`
row drives exactly that path and stays GREEN.

**Notes 3 and 4 taken as stated.** `_fsync_dir`'s two `except OSError: pass` arms and `_discard`'s
one now `logger.debug(..., exc_info=True)`, so a directory entry that never became durable leaves a
trace at some level; both still run after the commit and still cannot turn a failure into a success.
`read_note`'s docstring now states the asymmetry with the doors below it explicitly — "requires the
lock" is a CALLER contract there, and the reason it is not enforced (an unlocked read cannot lose a
note; the worst it does is mint a stamp that fails its own precondition later, which is the refusal
direction) is written down rather than left to be rediscovered.

**Notes 5, 6 and 7 need no change** — 5 and 6 ratify rulings the Build Log already recorded (the
Wall B filter placement, and `declared_type` carrying a setting's name), and 7 is a clean bill.

*Verify, all RE-RUN after the fix:*

| Check | Result |
|---|---|
| `tests/test_concurrent_access.py` | **17 passed** — AC-1 now carries both halves |
| THE FLOOR, `.venv/bin/python -m pytest tests -q` | **`637 passed` in 3.29s, ZERO failures** — equal to Task 15's landed count, never a decrease |
| Wall A — `filesystem_mutation_uses` modules | `['obsidian_schemas/vault_io.py']`, GREEN |
| Wall B — `os_module_attribute_uses` outside the door | the same three `os.environ` (`base.py`, `lint_vault.py`, `migrate_person_to_discuss.py`); the new `os.write` is INSIDE the door, GREEN |
| Wall C — `module_import_uses` | `[('obsidian_schemas/vault_io.py', 'filelock')]`, GREEN |
| Wall E — `falsy_returns_in(PACKAGE_ROOT, COMMIT_FUNCTION_NAMES)` | `[]`, GREEN — `_write_all` returns None but is deliberately OUTSIDE the set (a private helper, not a path-, payload- or stamp-returning door), and `ensure_dir` still returns its directory |

No acceptance criterion changed: AC-1's `check:` still resolves to
`test_every_door_commits_atomically`, and no fence was edited. No file outside `write_authority` was
written, and the five close-out steps above remain untouched by design.

## Code Review — 2026-08-10

**Trigger check: FIRES.** The post-build diff is not doc-only — one new package module
(`obsidian_schemas/vault_io.py`, 711 lines), five modified package modules, two modified scripts,
two new test modules, three modified test modules, and a dependency change (`filelock>=3.12` in
`pyproject.toml`). No skip pattern applies.

Reviewed against the working tree, not against the Build Log's claims: Wall A's live property was
re-derived by grep (no `write_text`/`mkdir`/`unlink`/`rename`/write-mode `open` outside
`vault_io.py` under `obsidian_schemas/` or `scripts/`), Wall B's by grep (`os.<attr>` outside the
door is three `os.environ` reads at `base.py:100`, `lint_vault.py:55`,
`migrate_person_to_discuss.py:165`; the `os.link` at `errors.py:100` is inside a docstring and
therefore invisible to a syntax-reading predicate, and `errors.py` imports no `os` at all), and
Wall C's by grep (no `shutil`/`tempfile`/`fcntl`/`mmap` import outside the door; `filelock` only in
`vault_io.py`). The Build Log's shell-liveness probe, its measured baseline (`617`), its
intermediate reds (`620 passed, 1 failed` at Task 3; `622 passed, 1 failed` at Task 16) and the two
design corrections it attributes to *running* the checks rather than reading them are consistent
with a build that executed — the WI-228 P4 dead-shell condition does not apply.

### Blocking

**1. `obsidian_schemas/vault_io.py:503` — `os.write`'s return value is discarded, so a short write
commits a truncated note atomically, durably, and silently.**

```python
        os.write(fd, payload)
        os.fsync(fd)
```

`os.write` is the raw `write(2)` syscall and returns the number of bytes actually written. On a
regular file it can return short — the realistic trigger is a volume filling mid-write, where
POSIX `write()` writes what fits and returns that count rather than failing with `ENOSPC`. Nothing
here compares the return against `len(payload)`. The truncated temp file is then `fsync`ed,
`os.replace`d over the target, and the parent directory is fsynced: the partial note is committed
*and made durable*, `_commit` returns `target`, `write_note` returns it to the caller, and
`write_markdown_file` records a fresh snapshot over the corrupted bytes. No exception, no WARNING,
no readback.

Failure scenario, concrete: the vault volume has 2 KB free. `repo.save(person, body=…)` builds an
8 KB payload. `os.write` writes 2048 bytes and returns 2048. The note commits as a 2 KB fragment —
frontmatter plus a severed body — and `record_snapshot` stamps it as good. The next `load()` either
parses the fragment as a valid entity with a shorter body (silent Timeline loss, the WI-015/WI-126
class) or raises `FrontmatterParseError` into the WI-020 skip surface. Either way the original note
is gone and nothing signalled.

This is a **regression against pre-WI-004 behaviour** in the exact class this item exists to close.
`Path.write_text` — what every one of these sites called before this build — goes through
`io.BufferedWriter`, which loops on short writes and surfaces `ENOSPC` as an `OSError` at flush;
the old code was loud here and the new code is silent. It is also the Step 2c check-7 shape (a
faster-than-expected/under-length completion passing by default) and the check-6 shape (a completed
write with no readback asserting the result matches intent).

The `## Verification` table already promises the opposite — *"`os.stat`, `os.open` or `os.fchmod`
failing while carrying the mode onto the temp descriptor → `WriteFailedError` — never a commit at a
mode nobody chose"* — and AC-1 certifies that every commit is atomic in the sense of a complete
note, not merely of an indivisible rename. A short write satisfies the rename and falsifies AC-1.

Required fix, inside `_commit`'s existing `try`, before the `fsync`: loop `os.write` until the
payload is exhausted (raising `WriteFailedError` if a call returns `0`), or assert the single call
wrote `len(payload)` and raise `WriteFailedError(_WRITE_INCOMPLETE, path=target, cause=…)`
otherwise. Either shape also closes the readback gap. A check belongs with it — the natural home is
`tests/test_concurrent_access.py`, patching `os.write` to a short-writing stub and asserting the
target still holds the complete OLD bytes and `WriteFailedError` was raised.

### Recommended

**2. `obsidian_schemas/vault_io.py:563-573` — `ensure_dir` breaks the module's own stated door
contract.** The module docstring at `:588-589` says of the doors, *"they are this package's own
refusal surface, and every failure on them is a LoudFailError subclass."* `ensure_dir` calls
`directory.mkdir(parents=True, exist_ok=True)` with no handler, so a permission or `ENOSPC` failure
escapes as a raw `OSError`. That escapes `write_markdown_file` (`writer.py:273`) and
`quarantine_garbage` (`lint_vault.py:1043`) as a non-`LoudFailError`, so a consumer's
`except LoudFailError` — the documented "this package refused" idiom — does not catch it. Wrap it
like the other doors, or narrow the docstring's claim to exclude the namespace cell.

### Notes

**3. `obsidian_schemas/vault_io.py:545-556, 538-542` — two post-commit `except OSError: pass`
swallows.** `_fsync_dir` silently swallows both the `open` and the `fsync` failure, and `_discard`
swallows the temp `unlink`. Both are genuinely best-effort and both run *after* the commit
succeeded, so neither can turn a failure into a success — but a directory entry that was not made
durable is exactly the class this item's Layer 1 exists to bound, and it currently leaves no trace
at any level. A `logger.debug`/`logger.warning` on the `_fsync_dir` arm would cost nothing.

**4. `obsidian_schemas/vault_io.py:576-594` — `read_note`'s docstring says "Requires the lock" and
nothing enforces it.** Every write door calls `_require_lock`; `read_note` does not. The claim is a
caller contract rather than an enforced one, and the six `person.py` body writers plus the two
script sites all honour it — but the asymmetry with the doors immediately below is worth stating in
the docstring rather than leaving a future reader to discover it.

**5. The Wall B filter-placement contradiction the Build Log raises (`### DEVIATION`) is resolved
correctly.** D10.6's Table 1 is the pinned artifact three gates executed against; D10.5's
NOT-matched table would make Table 1's row `[]` and D10.3's own assertion vacuous. Resolving toward
Table 1 and homing the membership rule once in `tests/test_write_routing.py:_os_violations` — where
the live wall at `:110` and the battery at `:265`/`:296` both call it — preserves the property
D10.5 was reaching for (the battery drives the wall's own code path, not a second copy) while
keeping the live claim non-vacuous against the three `os.environ` reads. No hand-back was owed and
none is owed now. This is a spec-internal contradiction the spec should be reconciled on at
close-out, not a build defect.

**6. `declared_type` carrying a config variable's NAME in `_bad_setting` (`vault_io.py:86-98`) is
acceptable as built.** It is a deliberate, documented misuse of a WI-020 slot, forced by Task 3's
ban on minting a fourth `REASONS` literal, and the alternative slots genuinely cannot carry it
(`path` renders the value, `bounded_cause` projects to a class name). The bounded property AC-16
needs — the name reaches the message and the value never does — holds, and
`tests/test_concurrent_access.py:196-203` asserts both halves. A reason literal per setting is the
cleaner home whenever a future item is allowed to touch `errors.py`.

**7. No new cross-project reach, no new dependence on deprecated code, no idiom regression, and no
`CLAUDE.md` claim made false by this diff.** `CLAUDE.md`'s only count claim is already de-pinned
("never trust a number written here"), the Key Files table addition for `vault_io.py` is correctly
deferred to conductor close-out step 4 (project root is outside `write_authority`), and every door
call site uses the `vault_io.<door>` module-attribute form D7 requires. No `<<< cage-reverted
writes >>>` block was supplied with this build, so there is nothing to check for an
applied-but-not-shipped claim; the Build Log's `### NOT done here` section correctly declines to
claim the five close-out paths were touched.

**Summary.** The design is sound and the routing is exhaustively verified — Layer 1's ordering,
Layer 2's two-tier lock with `thread_local=False`, Layer 3's origin-decided exception, M1's
`fchmod`-first ordering, M3's single resolved path, and the declared residual are all built as
specified and driven by real oracles. One line falsifies AC-1: the commit does not verify that all
of the payload reached the temp descriptor, which turns a full disk from a loud `OSError` (today's
behaviour) into a silently committed truncated note.

```verdict
gate: code-reviewer
verdict: REVISE
date: 2026-08-10
model: claude-opus-5
targets: AC-1, Task 3
note: vault_io._commit discards os.write's return, so a short write (ENOSPC) commits a truncated note atomically and silently — a regression against Path.write_text's loud flush, in the exact loss class AC-1 certifies against.
```

## Test & Observability Review — 2026-08-10

**Trigger check: APPLIES.** This build adds a new production code path — the package's single write
door, through which every vault mutation in three consumer repos now travels. Not a refactor, not
test-only, so no `N/A` self-declaration.

**1. Tests exist — comfortably.** `tests/test_concurrent_access.py` ships 17 zero-argument
top-level checks covering the happy path (`create_note` → `read_note` → `write_note` → `save()` →
`move_note`) and, for each door, at least one failure mode with a distinct type:
`ExternalWriteConflict` (`:797`), `StaleEntityWrite` (`:839`), `NoteAlreadyExists` (`:475`, `:566`),
`WriteFailedError` for the unheld lock (`:971`), for every invalid setting on the whole
configuration surface (`:178`), and for the symlinked move source (`:271`).
`tests/test_write_routing.py` ships the five walls plus a match-shape battery per wall.

Two properties are worth calling out because they are the difference between a suite that looks
green and one that means something:

- **The oracles are values the check itself wrote.** AC-15 compares against the mode it `chmod`ed
  and, for the fresh-create case, against the umask-derived mode it measured from a sibling in the
  same run (`:99-105`) rather than a hardcoded `0o644`. AC-18 asserts `set(observed) == {12}`
  against the twelve notes it planted, never a count read back from the repository under test.
- **The zero-count walls carry reach batteries.** Walls B, C and E are all green against a matcher
  that resolves nothing on this tree, and each ships a battery that plants and drives the shapes it
  claims (`_wall_b_battery` plants the `from os import` arm that has no live instance; `_wall_c_battery`
  GENERATES its matched imports by iterating `WALL_C_MODULES`; `_wall_e_battery` generates one
  falsy-returning function per member of `COMMIT_FUNCTION_NAMES` and asserts SET EQUALITY). The
  near-miss halves are equally load-bearing — `s.replace`/`frontmatter.copy`/`p.replace` and
  `snapshot_stamp`'s deliberate `None` are each pinned NOT matched, with the declared blind spots
  written out so a later reader meets the ruling instead of "fixing" the wall red.

The three mutate-and-observe probes the Build Log records (Wall A red on a planted `unlink`, Wall
D(i) red on a deleted `remember_snapshot`, Wall E red on a planted `return None`) are the right
instrument for proving a wall can go red, and all three targets are declared `## Write Targets`
paths.

**2. Logging at WARN/ERROR per failure mode — present and specific.** Every refusal is a typed
`LoudFailError` carrying its resolved path and, by `bounded_message`'s construction, no note
content — asserted directly at `tests/test_concurrent_access.py:678-696` against a planted sentinel
string rather than against an assumed absence. `observe` mode emits a WARNING naming the exception
class that *would* have been raised (`vault_io.py:188-191`), the create-race recovery WARNs with
the loser's `created_by` (`person.py:1484-1487`), and `allow_unverified_overwrite` WARNs at every
use (`writer.py:217-220`). The once-per-process `observe` announcement (`_announce_mode_once`) is a
good call — a security-relevant mode that is silent while nothing collides is how a consumer leaves
it set for a month believing the item shipped — and AC-9 pins "exactly ONE INFO line across TWO
writes" rather than merely "at least one".

**3. Alerts wired — N/A, correctly.** This is an importable library with no daemon, cron entry or
launchd job of its own; there is no automated system here for Dave to be alerted about. The
operational signal is the exception surfacing in whatever consumer made the call, which is the
right seam.

**4. Invariant registration — N/A (skipped, not failed).** `obsidian-schemas` ships no invariant
registry; `src/invariants.py` does not exist in this project (v1 registry scope is orchestrator-only
per this role's checklist). The grep target does not resolve, so this dimension is noted N/A rather
than counted a finding, and no `## Observability Waiver` is owed.

**Residual, non-blocking:** `_fsync_dir` (`vault_io.py:545-556`) swallows both its `open` and its
`fsync` failure with no log at any level, so a directory entry that never became durable leaves no
trace. It runs after the commit and cannot turn a failure into a success, which is why it is a note
here rather than a finding — see Code Review note 3.

**One defect is deliberately NOT double-counted here.** The unchecked `os.write` return at
`vault_io.py:503` is a silent failure mode in a new production path and would ordinarily be this
pass's finding too; it is attributed once, to the Code Review fence, which already blocks
`building → done`. Recording it twice would read as two independent findings across rounds and
would muddy exactly the converging-arc signal the `targets:` line exists to carry. It is named here
so that a reader does not mistake this fence's PROMOTE for a pass that missed it.

**Summary.** Test coverage and observability are the strongest part of this build: real behavioural
oracles over a running filesystem, reach batteries behind every zero-count wall, red-probes proving
the walls can fail, and a loud, bounded, mode-governed refusal surface. Nothing in this dimension
blocks.

```verdict
gate: test-observability-checker
verdict: PROMOTE
date: 2026-08-10
model: claude-opus-5
note: 17 behavioural checks with self-written oracles plus reach batteries behind all three zero-count walls; refusals are typed, bounded and mode-governed, alerts are N/A for a library, and no invariant registry exists in this project.
```

## Code Review — 2026-08-11

**Trigger check: FIRES.** Same diff surface as round 1 plus `### Revision 1`'s edits — one new
package module, five modified package modules, two modified scripts, two new and three modified test
modules, and a dependency change. No skip pattern applies.

**Reviewer's own constraint, stated rather than implied.** This cage exposes no `Bash` tool
(confirmed by `ToolSearch`, which resolves only `TaskOutput`), so I could not re-run the floor
myself. Every claim below is from reading the working tree; where a number could only be measured,
I say so and attribute it to the Build Log rather than asserting it. The Build Log's own executions
are not in doubt — it opens with a liveness probe, records two intermediate RED states (`620 passed,
1 failed`; `622 passed, 1 failed`) and two corrections it attributes to running checks rather than
reading them, so the WI-228 P4 dead-shell condition does not apply to the build.

### The round-1 Blocking finding is CLOSED, and closed at the right level

`obsidian_schemas/vault_io.py:548-581` — `_write_all(fd, payload)` loops from the written offset over
`memoryview(payload)[written:]` and raises when a call returns `<= 0`. Three properties make this the
fix rather than a patch over the symptom:

1. **It resumes from the offset**, so a short-but-progressing descriptor still commits the complete
   note. A naive `raise if os.write(...) != len(payload)` would have satisfied the round-1 finding
   while breaking every real write on a short-returning fd.
2. **It raises plain `OSError`, deliberately** (`:567-571`), so `_commit`'s existing handler at
   `:515-518` — the one place that closes the descriptor, discards the temp file and re-raises as
   `WriteFailedError` — remains the single exit. I traced the path: the refusal cannot reach
   `os.replace` at `:537`, so the target keeps its old bytes and no temp file survives. That is the
   structural version of the fix, not a second cleanup site.
3. **The claim moved with the code.** Layer 1's module docstring (`:10-17`) now says the commit
   "writes EVERY byte of the payload — a short `write(2)` refuses rather than committing a fragment,
   so 'atomic' means a COMPLETE note and not merely an indivisible rename", which is exactly what
   AC-1 certifies and exactly what round 1 found the code not doing.

The pinning check is real: `tests/test_concurrent_access.py:806-865` drives the fill-up shape (short,
then no progress), asserts `WriteFailedError`, asserts the target still holds **the old bytes the
check itself wrote**, asserts no temp file survived, and then drives the near-miss (64 bytes at a
time, must commit the complete note). The Build Log records the mutate-and-observe both ways —
reverting to `os.write(fd, payload)` takes it RED at the named assertion. I could not re-run that,
but the assertion it names is present at `:832-835` and would fail as described.

### Round-1 Recommended and Notes — all taken, none narrowed

- **Finding 2 (`ensure_dir` breaking the door contract)** was taken at the code level, which is the
  right direction given `ensure_dir` is already inside `COMMIT_FUNCTION_NAMES`
  (`tests/derivations.py:76-79`). It now refuses as `WriteFailedError` (`vault_io.py:633-638`). I
  checked the coupling this exposes rather than trusting the Build Log's account of it: the two
  internal callers widened to `(OSError, WriteFailedError)` (`:156`, `:401`) and each re-homes the
  message off the configured value — `_configured_lock_dir` through `_bad_setting` (name in
  `declared_type`), `note_lock` onto the note path — which preserves M2. The two external callers,
  `writer.py:273` and `lint_vault.py:1043`, I read directly: **neither carries an `OSError` or
  `LoudFailError` handler**, so this is a refusal-*type* change and nothing else, and no consumer
  path silently swallows the new exception.
- **Notes 3 and 4** taken: `_discard` (`:584-588`) and both `_fsync_dir` arms (`:591-611`) now log
  at DEBUG with `exc_info=True`; `read_note`'s docstring (`:642-662`) now states the asymmetry with
  the doors below and *why* the lock is a caller contract there (an unlocked read cannot lose a note;
  the worst case is a stamp that fails its own precondition later — the refusal direction).
- **Notes 5, 6, 7** needed no change and still need none.

### Re-checked independently this round

The walls still hold with `os.write` added: `write` is provenance-matched via `MODULE_MUTATION_NAMES`
so Wall A resolves it, and both walls exclude `DOOR_MODULE` only — the new syscall is inside the door
(`tests/test_write_routing.py:95`, `:110`). `os.write` was already a driven shape in Wall A's matched
battery (`:162`, `:186`). `_write_all` returns `None` but is correctly outside
`COMMIT_FUNCTION_NAMES`, which is a set of path-, payload- and stamp-returning surfaces, so Wall E's
green is not bought by a widened exemption. I also re-walked all 13 door-1 routing sites: every one
takes `note_lock`, reads **inside** it, and preconditions on that read; `person.py:1582` and `:1593`
share a stamp but are mutually exclusive branches (`:1584` returns); `lint_vault.py:886` re-reads
before its second write rather than reusing `:820`'s stamp. AC-1's `check:` still resolves to
`test_every_door_commits_atomically`.

### Notes (non-blocking, none owed a fix)

**1. `vault_io.py:156-162, 401-406` — the re-homed message is bounded, but the `__cause__` chain is
not.** `raise _bad_setting(...) from exc` keeps the original `WriteFailedError` (whose `path` renders
the configured lock-dir VALUE) as `__cause__`, so a consumer logging with `exc_info=True` still
renders it. M2's own claim — the refusal's message carries the name and never the value — holds, and
this is unchanged in kind from before Revision 1 (an `OSError`'s `filename` carried it too). Worth
knowing, not worth a fix.

**2. `vault_io.py:520` — `os.close(fd)` on the success path is outside a handler.** A failure there
escapes a door as a raw `OSError` and leaves the temp file. Vanishingly unlikely after a successful
`fsync`, and it cannot commit anything, so it is a note.

**3. The precondition token is `(mtime_ns, size, exists)`.** Two writes of identical length within
one mtime tick compare equal. On the APFS volume the data-premise gate confirmed, `st_mtime_ns` is
genuine nanosecond resolution, so this is unreachable in practice and is fairly read as inside R1's
declared window — but the residual list R1–R14 is otherwise exhaustive enough that this is the one
shape not named in it. A line in R1 at close-out would complete the set.

**4. `_THREAD_LOCKS`, `_FILE_LOCKS` and `_SNAPSHOT_STAMPS` never shrink.** One small entry per path
ever locked or stamped, bounded by vault size, in a library whose main consumer is a long-lived
FastAPI process. Bounded and cheap; noted so a future reader meets it deliberately.

**Summary.** The one line that falsified AC-1 is fixed at the level the finding pointed at, the fix
cannot reach `os.replace`, and the criterion it falsified is the criterion that now pins it — with
both arms and a load-bearing near-miss driven by oracles the check wrote itself. The Recommended
finding was taken as code rather than as a narrowed docstring, and I verified by reading both
external callers that its refusal-type change swallows nothing. Nothing in this round's diff is
Blocking; the four notes are all bounded and none is owed a fix before `done`.

```verdict
gate: code-reviewer
verdict: PROMOTE
date: 2026-08-11
model: claude-opus-5
note: Revision 1 closes round 1's blocking short-write defect structurally — _write_all resumes from the offset and refuses through _commit's single cleanup exit, so a refusal cannot reach os.replace — and AC-1's own check now pins it with both arms plus the short-but-progressing near-miss.
```

## Test & Observability Review — 2026-08-11

**Trigger check: APPLIES.** Still a new production code path — the package's single write door, which
every vault mutation in three consumer repos now travels through. Not a refactor, not test-only, so
no `N/A` self-declaration is available.

**1. Tests exist — and this round's addition is the strongest check in the module.** Round 1's fence
PROMOTEd on 17 checks; the count is unchanged, but AC-1's own check grew the property the code-review
finding falsified. That placement is the point: the criterion that was falsified is the criterion
that now pins the fix, rather than a new check bolted alongside it. Three properties I verified by
reading `tests/test_concurrent_access.py:806-865`:

- **The oracle is the target's own OLD bytes**, written by the check at `:808` and compared at
  `:839-842`. Not a length, not a substring, not an assumed absence.
- **Both arms of the shape are driven, and the second is load-bearing.** `short_then_stuck`
  (`:812-820`) takes half and then makes no progress — proving the loop resumes from the offset AND
  refuses instead of spinning — while `chunked_write` (`:853-854`) returns short but keeps
  progressing and must still commit the COMPLETE note. Drop the second and a naive
  "raise on any short return" passes the first assertion while breaking every real write.
- **The probe asserts it actually ran.** `:836-838` asserts `len(calls) >= 2`, so a patch that never
  reached `os.write` cannot read as a pass — the exact silent-PASS-on-empty shape this project's
  Data Quality Discipline names.

Authored failing-test-first per WI-029, with the mutate-and-observe recorded both directions. I could
not re-run it (no `Bash` in this cage — see the Code Review section), so I read the assertions
instead; the one the Build Log names as the RED anchor is present at `:832-835` and would fail as
described.

**2. Logging at WARN/ERROR per failure mode — improved this round.** Round 1's residual is closed:
`_fsync_dir`'s two arms (`vault_io.py:591-611`) and `_discard` (`:584-588`) now leave a DEBUG trace
with `exc_info=True` where they previously left none at any level. DEBUG rather than WARNING is the
right call and not a narrowing — both run *after* the commit succeeded and neither can turn a failure
into a success, so a WARNING would be noise on a path that has no operational action attached. The
loud surface is unchanged and still correct: every refusal is a typed `LoudFailError` carrying its
resolved path and no note content (asserted at `:678-696` against a planted sentinel rather than an
assumed absence), `observe` mode WARNs per conflict and announces itself exactly once per process,
and `allow_unverified_overwrite` WARNs at every use.

The new refusal carries its diagnostic in the chain rather than the message —
`WriteFailedError("write did not complete", path=…, cause=OSError)`, with
`"write made no progress: N of M bytes written"` on `__cause__`. That is `bounded_cause` working as
designed (a cause projects to its class name), and the byte counts survive for a debugger via the
chain, so the failure is both loud and reconstructable.

**3. Alerts wired — N/A, correctly.** An importable library with no daemon, cron entry or launchd job
of its own. The operational signal is the exception surfacing in whatever consumer made the call,
which is the right seam. Nothing about Revision 1 changes this.

**4. Invariant registration — N/A (skipped, not failed).** Re-verified this round rather than carried
forward: a glob for `**/invariants.py` across the tree returns nothing, so `obsidian-schemas` ships no
invariant registry and v1 registry scope is orchestrator-only. The grep target does not resolve, so
this dimension is noted N/A and no `## Observability Waiver` is owed.

**Round-1 attribution, discharged.** Last round this fence deliberately declined to double-count the
unchecked `os.write` return, attributing it once to the Code Review so the `targets:` series would
read as one converging finding rather than two. That defect is now fixed and pinned, so there is
nothing outstanding under that attribution and no finding is being carried silently.

**Summary.** Test and observability readiness remains the strongest dimension of this build, and this
round improved it in both halves: the fix landed inside the acceptance criterion it falsified with a
self-written oracle and a load-bearing near-miss, and the one logging gap round 1 named is closed at
the level appropriate to a best-effort post-commit path. Nothing in this dimension blocks.

```verdict
gate: test-observability-checker
verdict: PROMOTE
date: 2026-08-11
model: claude-opus-5
note: Revision 1's fix is pinned inside AC-1's own check with the target's old bytes as oracle, both arms plus the short-but-progressing near-miss, and an assertion that the probe ran; round 1's _fsync_dir logging residual is closed and alerts/invariants remain correctly N/A.
```
