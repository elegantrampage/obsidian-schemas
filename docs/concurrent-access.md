---
id: WI-004
title: "Concurrent & external write safety (atomic writes, locking, stale-read protection)"
project: obsidian-schemas
stage: exploring
created: 2026-03-22
last_touched: 2026-07-08
stage_changed: 2026-07-08
touched_by: session
tags: [repository, write-safety, corruption-class]
depends_on: ["WI-020"]
transitions: ["idea>exploring@2026-07-08@fable-explore"]
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
3. **Consolidation rider:** the package has **six hand-rolled `content.split("---", 2)` frontmatter splits** in the body-section writers (`person.py:1564-1805`) plus a seventh section-splitter in `append_to_timeline` (`person.py:1481-1494`), each a divergence risk from the canonical parser. The new primitive is the one door they all route through — solve-in-one-place.
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

One composite primitive `mutate_note(path, fn)` in the package: per-file advisory flock
(with in-process holder registry) → fresh read under lock → caller's pure transform →
serialize → external-write precondition re-stat → temp-file+fsync+`os.replace`. All
update/append/section-writer paths (base.py `update_fields`, writer.py's four
`write_text` sites, the six person.py splitters + `append_to_timeline`, lint_vault
`--fix`) route through it; `ExternalWriteConflict` is loud and retryable; torn writes
impossible by construction; the residual µs external window documented as a known,
accepted property.

## Intent

One atomic, guarded, lock-aware write primitive; every vault mutation in the package routes through it; a concurrent or external edit can no longer be silently destroyed, and a crash can no longer tear a note.
