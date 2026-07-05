# obsidian-schemas backlog campaign — 2026-07-05

Curated with Fable (this review is the project's Fable touch, per `workshop/docs/model-routing-plan-2026-07-04.md` as amended 2026-07-05: Fable touches are justification-gated, not capped — each must name the fork it resolves; Fable never authors and reviews the same item). Inputs: parallel architecture / code-health / test-suite / work-item-corpus reviews, all corruption-class claims spot-verified at file:line. Governs sequencing, per-stage **model routing**, and per-stage **reasoning effort**. The table is a default, not a cage — escalation valve open per doctrine.

## State of play (evidence-checked 2026-07-05)

- **The library is in good shape where it's been worked**: 563 hermetic tests, all green in 1.09s; every WI-105→WI-126 commit shipped with pinning tests; real-data-shaped fixtures (José García, RFC 2822 leaks, mangled stubs) are now the convention. Clean leaf boundary — one env var, no sibling-repo reaches.
- **The identity engine (WI-125) is live but half-cut-over, and the retained half is an active tax**: `find_or_create_stub` runs the engine, but the full legacy cascade sits verbatim as `_find_or_create_stub_legacy` (person.py:719) and WI-121 had to be hand-threaded through **both** copies "symmetrically". The unified identifier index is built on every load yet bypassed for email/phone resolution (person.py:966-986) — its only live effect is conflict observability. The parity replay already PASSED (942 inputs, 0 diffs), so the deletion cut is unblocked.
- **Five corruption-class silent-degrade sites are live** (all spot-verified): malformed YAML silently becomes "no frontmatter" and the rebuild paths then destroy the original frontmatter (parser.py:78-80 × base.py:255-273); the WI-126 body-shrink guard disables itself on read error (writer.py:189-190); un-loadable notes vanish at DEBUG and seed duplicate stubs (base.py:125-126); model-validation errors are swallowed (parser.py:139-150); write failures return the same `False` as no-ops (five sites in person.py).
- **No locking or atomic writes anywhere** while HAL9000's server, orchestrator, CLI sessions, and Obsidian itself write the same live vault — the systemic corruption risk (C1).
- **`CompanyRepository.create_stub` still runs the exact mangler regex the Person side deleted** (company.py:171 vs person.py:1381-1388) — no validator, no provenance.
- **Untested blast radius**: the hardcoded live-vault default path (base.py:21 — misconfigured consumer silently writes real data); `scripts/lint_vault.py` (1,198 LOC, zero tests, `--fix` bypasses the WI-126 guard and can drop frontmatter on malformed notes).
- **Governance had drifted badly**: state file 5 weeks stale with 8 shipped orchestrator-numbered items unregistered; SESSION_LOG's newest entry (March) sat uncommitted for 4 months; 17 item docs untracked; CLAUDE.md claimed docs/ was empty and "195+ tests". Fixed inline this session.

## Curation decisions

| Item | Decision | Why |
|---|---|---|
| WI-004 Concurrent Access | **Reslice (queued P2)** | March framing (in-process thread-safety) is a subset; real scope = atomic writes + locking + stale-read protection across processes AND Obsidian. Absorbs WI-015; absorbs the six hand-rolled frontmatter splits (N6) as consolidation rider. |
| WI-015 Obsidian Plugin Sync | **Park → merged into WI-004** | Same root cause (unlocked read-modify-write vs a second writer), same mechanism. WI-126 narrowed but didn't close it. |
| WI-014 HAL9000 Singleton | **Park** | Premise eroded (HAL9000 now has `entity_registry.py:34 get_repository`) and remaining lifecycle work belongs to HAL9000 — solve in one place. |
| WI-016 Vault Fixtures | **Reslice (queued P3)** | Real-data-shaped fixtures became the convention organically; residual = frozen anonymized ~50-note fixture vault + Exploration round-trip; Hypothesis demoted to stretch. Coordinate with exocortex WI-034 (one shared anonymization design). |
| WI-008 Exploration Entity Type | **Premise fixed, stays idea** | "Model exists but uncommitted" is false — committed at models.py:266. Residual: repository + writer round-trip. |
| WI-011 Validation Modes | **Keep unqueued + scope note** | The malformed-YAML degrade is NOT this item — it's corruption-class and went to new WI-020. WI-011 stays the unknown-field mode selector. |
| WI-009 Role & Seniority | **Keep (queued P5)** | Verified unshipped (models.py:78-90); has a real consumer (headhunter agent). |
| WI-017/018/019 | **Confirmed done** | Verified in code; WI-017 doc frontmatter (stage: specced) corrected to done. WI-019's caller-migration follow-on is half-open but lives in the owning repos (see Cross-project signals). |
| WI-001/002/003/005/006/007/010/012/013 | **Keep as unqueued ideas** | All premises re-verified valid 2026-07-05 (corpus review); performance/freshness/capability cluster with no recorded current pain. WI-006 stays blocked on WI-005. |

**New items opened by this review:** WI-020 (loud-fail hardening: parse/guard/write-return boundaries — C2/C3/C4/C5/N4), WI-021 (write-door bypasses: NameValidator + address normalization on every mutation path — N2/N3), WI-022 (Company stub parity — N1), WI-023 (identity engine endgame: legacy deletion cut + index cutover — G1/N5/N7 + cycle break), WI-024 (remove hardcoded live-vault default — H1), WI-025 (decompose person.py — gated on WI-023), WI-026 (lint_vault --fix safety + scripts test floor — H2), WI-027 (needs_resolution flip — WI-125's deferred follow-on, unqueued, sequenced with orchestrator WI-118).

## Doctrine (obsidian-schemas adaptation)

- **Fable** — this review, plus **one forward touch**: the **WI-004 explore**. Named fork: per-file `flock` vs single-writer process vs optimistic mtime-precondition vs temp-file+rename-only, × coexistence with Obsidian's editor writes. Genuinely open (four frames with different consumer-facing semantics), expensive to reframe once three repos depend on the semantics, and the failure mode — silent data loss — is definitionally hard to detect downstream. Fable is explorer only; the WI-004 spec-review is Opus (no author/reviewer overlap; decorrelation preserved). Two borderline forks considered and left at Opus: WI-020's quarantine semantics (workspace loud-fail doctrine constrains the space) and WI-016's anonymization design (shared with exocortex WI-034 — flagged as a cross-project fork below rather than spent here).
- **Opus** — default judgment engine: specs, spec-reviews, and any build touching the parser, writer, write paths, or identity machinery. Code-review of every Sonnet build, always.
- **Sonnet** — leaf builds with executable ACs (WI-022 company parity, WI-024 path removal, fixture-vault build, lint_vault rules), template-bound specs, retro drafting.
- **Effort** — default medium; low = mechanical; high = corruption-class builds/reviews and the Fable explore; **the single xhigh is the WI-004 spec-review** — the primitive every vault mutation will route through; a correlated miss there corrupts the live vault for all three consumers.
- **Library invariant:** every patch ships its invariant test (563-test floor only goes up); any name/identity-touching change gets a real-data-shaped fixture; WI-023's cuts each re-run the parity replay green.

## Campaign queue — routing & effort

Stages shown are remaining stages per item. `—` = skipped (doc already carries it or N/A).

### Phase 1 — Protect the floor (corruption-class)

| # | Item | Explore | Spec | Spec-review | Build | Notes |
|---|---|---|---|---|---|---|
| 1 | **WI-020** loud-fail boundaries | — (review is the exploration) | Opus / high | Opus / high | **Opus / high** | Quarantine semantics is the one design call. Keystone regression: malformed-YAML round-trip protection. WI-004 builds on this floor. |
| 2 | **WI-024** remove live-vault default | — | — (doc + consumer audit) | Opus / low | **Sonnet / low** | **Dave sign-off** — breaking change; audit no-arg constructions in all 3 consumers first. |

### Phase 2 — Write safety & boundary closure

| # | Item | Explore | Spec | Spec-review | Build | Notes |
|---|---|---|---|---|---|---|
| 3 | **WI-004** concurrent & external write safety | **FABLE / high** | Opus / high | **Opus / xhigh** | **Opus / high** | The campaign's Fable fork + single xhigh. One primitive; all six hand-rolled splits route through it. |
| 4 | **WI-021** write-door bypasses | — | Opus / medium | Opus / medium | **Opus / medium** | After WI-004 — hang the checks on the new primitive, not on six doors about to collapse. |
| 5 | **WI-022** Company stub parity | — | Sonnet / low | Opus / medium | **Sonnet / medium** | Independent; schedule opportunistically. Punctuation-preserving cleaning contract, not a blind Person copy. |

### Phase 3 — Identity endgame & test floor

| # | Item | Explore | Spec | Spec-review | Build | Notes |
|---|---|---|---|---|---|---|
| 6 | **WI-023** identity engine endgame | — (strangler plan + parity PASS recorded) | Opus / high | Opus / high | **Opus / medium** | Delete legacy cascade; index cutover (resolve the Phone.key question); consolidate resolve/resolve_all; break the normalize_phone cycle. Parity replay green after each cut. |
| 7 | **WI-016** frozen real-data fixture vault | — | Opus / high | Opus / medium | **Sonnet / medium** | Anonymization design shared with exocortex WI-034. Includes Exploration round-trip. |

### Phase 4 — Quality

| # | Item | Explore | Spec | Spec-review | Build | Notes |
|---|---|---|---|---|---|---|
| 8 | **WI-025** decompose person.py | — | Opus / medium | Opus / medium | **Opus / medium** | Strictly after WI-023. Pure-move; WHY-comments travel with code. |
| 9 | **WI-026** lint_vault --fix safety | — | Sonnet / medium | Opus / medium | **Sonnet / medium** | After WI-004 + WI-020 (routes through the primitive, respects quarantine semantics). |

### Phase 5 — Capability

| # | Item | Explore | Spec | Spec-review | Build | Notes |
|---|---|---|---|---|---|---|
| 10 | **WI-009** profession & seniority fields | Opus / low (taxonomy w/ Dave) | Sonnet / medium | Opus / medium | **Sonnet / medium** | Consumer-facing schema change — spec lists the HAL9000/Exocortex ContactInfo mirror updates. |

**Unqueued ideas** (valid, no current pain): WI-001 file watching, WI-002 TTL cache, WI-003 lazy loading, WI-005 cross-repo linking, WI-006 relationship tracking (blocked on WI-005), WI-007 WatchRepository, WI-008 Exploration residual, WI-010 migration support, WI-011 validation modes, WI-012 index persistence, WI-013 incremental loading, WI-027 needs_resolution flip (sequenced with orchestrator WI-118).

**Fable budget: 1 forward touch** (WI-004 explore) + this review. Single xhigh: WI-004 spec-review. Escalation valve open.

## Cross-cutting defaults

- Code-review of any Sonnet build: **Opus, always.**
- Retro drafting: Sonnet / low.
- Every patch ships an invariant test; suite must stay green and hermetic (no test may ever touch `OBSIDIAN_VAULT_PATH` — and after WI-024, no code can by accident).
- Cross-repo verification rider on schema changes: HAL9000 + Exocortex mirror updates listed in the spec, verified by readback in the build.

## Cross-project signals

For the portfolio meta-campaign. This repo is the shared foundation — every consumer-facing schema/type decision here is by definition cross-project.

- **Pattern-class: loud-fail sweep.** WI-020 here is the same item class as exocortex WI-040 (and the parser/guard silent-degrade shapes will exist in any repo that parses files). Candidate for a portfolio-level pattern: "every repo gets a silent-degrade audit."
- **Pattern-class: frozen anonymized real-data fixtures.** WI-016 here ↔ exocortex WI-034 — same vault, same personal data, same anonymization problem. **Nominated fork for meta-campaign attention:** one shared anonymization design (and possibly one shared fixture corpus) instead of two independent ones. This was a borderline Fable touch deliberately left at Opus pending the portfolio view.
- **Fable fork (spent here):** WI-004's write-safety frame. Its outcome is itself cross-project — whatever locking/atomicity semantics this library adopts become the contract for HAL9000, orchestrator, and exocortex vault writes, and should inform any other repo that writes shared files.
- **Owner-elsewhere items:** the WI-019/WI-103 caller migration is half-open in the owning repos — orchestrator `roles/contact-detector.yaml:160` still instructs `create_stub` (WI-083 there), and the exocortex Granola ingester (`ingestion/transcript.py:804`, the highest-frequency caller) is deferred as orchestrator WI-118, blocked on a shadow-harness design. HAL9000 `entities.py:203` retains a `create_stub` fallback branch. None of these get obsidian-schemas items; they need to stay live in their owners' queues.
- ~~Duplicate HAL9000 checkout~~ — **retracted 2026-07-05 (same session):** `hal9000` and `HAL9000` are the same directory (same inode) on the case-insensitive APFS volume, not two checkouts. No drift risk. Kept here so the meta-campaign doesn't re-flag it.
- **Consumer-facing type decisions queued here:** WI-024 (unconfigured construction becomes loud-fail — breaking for any lazy consumer), WI-021 (validation on every write door — consumers lose the ability to write unvalidated names), WI-027 (WeakIdentityError → needs_resolution flag — a contract change that must land in lockstep with orchestrator WI-118), WI-009 (new Person fields — ContactInfo mirrors in HAL9000/Exocortex). Exocortex WI-042 ("value types at boundaries — coordinate with obsidian-schemas") should consume this repo's `Identifier` union rather than minting its own types.
