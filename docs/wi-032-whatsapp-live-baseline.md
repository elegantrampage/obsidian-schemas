# WI-032 `whatsapp` scalar → list — live baseline (the ENTRY half of the bracket)

Section shape copied literally from `docs/stem-divergence-live-baseline.md` (WI-029's bracket), which is
this document's declared precedent. Unlike that one this file is NOT a `kind: precondition` fence: it is a
DELIVERABLE of the ship condition (`docs/whatsapp-jid-value-type.md` → `## Approach` step (4)), written
during the drive. Its entry figures are not re-measured here — they are copied from
`docs/wi-032-whatsapp-corpus-census.md`'s committed stdout block, and
`tests/test_whatsapp_migration.py:test_wi032_live_baseline_row_shape_and_redaction_wall` asserts that every
figure in §1 AGREES with that artifact by parsing its `(a)`, `(c)` and `(c')` lines.

**Privacy wall (`## Design` §10(b)), and this item SHIPS it rather than relying on it.** Counts, classes and
code paths only — no vault note name, no live identifier, and specifically NONE of the migration's
`(stored value → proposed JID)` repair pairs and none of the `whatsapp_not_storable` detector's per-note
issue lines. Both of those are STDOUT of the conductor's live run and stay on the terminal. `docs/**` is a
member of `DOC_SCAN_EXCLUDED` (`tests/test_vault_path_required.py`), so no standing markdown wall reads this
file at all; the check named above is the only thing that does, and it runs a redaction predicate over this
document's FINAL text — after stripping every 40-hex commit token, no run of nine or more digits and no
digit-immediately-before-`@`-and-a-domain-label may survive. The bare domain literals `@s.whatsapp.net` and
`@lid` are deliberately NOT refused: §2 below names them as the storable classes' domains and must keep
being able to.

- **Vault:** `$VAULT`, Dave's live Obsidian vault; the population is `type: person` notes under the
  census's own walk (no dot-directory, none of `_quarantine`, `_merged_dupes`, `Templates`).
- **Tree:** no obsidian-schemas HEAD is pinned here, deliberately. The census artifact carries the
  pre-build tree it was measured against and this file copies its numbers, so the tree pin that matters is
  the census's own and a second one here could only go stale. **Interpreter:** the project's own `.venv/bin/python`,
  run from the repo root (the `.venv` editable install is deliberately stale — `pipeline-runners.yaml`).
  No absolute path appears anywhere in this file, so a whole-file privacy scan is legal against it.
- **The measurement command** is §0.

## 0. The measurement — the two commands, run once each, stdout read and NOT pasted here

The entry figures are the census's. Nothing is re-measured for this file; §1 is a TRANSCRIPTION whose
agreement with the artifact is machine-asserted.

```bash
# (1) the dry run — READ-ONLY, prints the six per-cell counts, the repair
#     disclosure (uncorroborated members FIRST) and the predicted triple.
.venv/bin/python scripts/migrate_whatsapp_to_list.py --vault "$VAULT"

# (2) the independent second witness to the residual R, AFTER the write.
.venv/bin/python scripts/lint_vault.py --vault "$VAULT" --report
```

The dry run's repair disclosure is read as EXACTLY one record line per class-C note plus its headers —
that equality is guaranteed by the render (`## Design` §10(d)), so a line count that disagrees is a defect
and not a long value, and any visible `\xNN`-style escape inside a printed value is the render doing its
job rather than a corrupt note. Those pairs stay on the terminal.

## 1. Entry figures

Transcribed from `docs/wi-032-whatsapp-corpus-census.md`'s verbatim stdout block. The six class rows are
its `(c)` lines; class Ø is split into its two live spellings from its `(c')` line, because only the
key-PRESENT spelling is a write.

| figure | entry (2026-09-27) |
|---|---|
| `type: person` notes | 1174 |
| class **Ø** — introduces no identifier | 1031 |
| class Ø, spelling `absent key` — needs NO write, outside the partition's domain | 6 |
| class Ø, spelling `""` — the SHAPE-ONLY conversion population | 1025 |
| class **A** — parses, phone-bearing, storable | 35 |
| class **B** — parses, `@lid`, storable | 26 |
| class **C** — parses, phone-bearing, NOT storable (the Kim Faura class) | 82 |
| class **D** — non-empty, does not parse | 0 |
| class **E** — `@lid` substring, domain outside the closed set | 0 |
| value already list-shaped | 0 |

And the five DERIVED partition figures, each computed from the rows above rather than measured
independently:

| derived figure | entry | derivation |
|---|---|---|
| `whatsapp`-CARRYING notes — the population the TERMINAL-STATE PARTITION ranges over | 1168 | 1174 less the 6 absent-key notes |
| MIGRATED — part (2) of the partition | 1168 | carrying less the residual R |
| ⤷ named sub-count: SHAPE-ONLY conversions (class Ø, key present) | 1025 | the `""` spelling |
| ⤷ named sub-count: class-C REPAIRS | 82 | the class-C row, under Ruling A/B's recommended arm |
| the residual R — part (3), reported and left byte-identical | 0 | class D plus class E |

Part (1) of the partition — notes left in the SCALAR shape OUTSIDE R — is **ZERO** by construction of the
run, and is the figure §5 reports against.

**The 1025 is ~88% of the run's writes with NO semantic effect, and that is posed here rather than after
the write.** The tolerant reader already presents `whatsapp: ""` as the empty collection, so converting
those notes changes no resolution, no key, no model value and no consumer-visible behaviour — it buys
cosmetic uniformity and it costs turning the riskiest step in the item from ~143 notes into ~1168, with the
same multiple on a reverse migration. The partition as it stands REQUIRES them. If Dave says "leave those
alone" with that number in hand, part (1)'s zero becomes "zero outside R and outside class Ø" and the
tolerant reader is what makes that safe — a one-line consequence in §5, not a redesign.

## 2. The direction, per class

| class | storable? | direction | reversible? |
|---|---|---|---|
| **Ø** (key present) | n/a — no identifier | SHAPE-ONLY: `""` → `[]` | yes, exactly |
| **Ø** (key absent) | n/a | **no write** — outside the partition's domain | n/a |
| **A** (`@s.whatsapp.net`) | yes | CONVERT: `[<member verbatim>]` | yes, exactly |
| **B** (`@lid`) | yes | CONVERT: `[<member verbatim>]` | yes, exactly |
| **C** (bare number) | **no** | REPAIR then convert — the digits re-spelled as a JID, guarded on the parsed form carrying non-empty phone digits | **up to the re-spelling** — a list→scalar reverse returns the CANONICAL form, not the pre-migration bytes, for all 82 |
| **D** (unparseable) | no | **no write** — reported and left BYTE-IDENTICAL; terminally scalar BY DESIGN | n/a — nothing moved |
| **E** (`@lid` substring, wrong domain) | no | **no write** — reported and left BYTE-IDENTICAL | n/a — nothing moved |

The storable domains are `@s.whatsapp.net` and `@lid`, by MEMBERSHIP of a closed set on the type and never
by a suffix test. Classes C, D and E are what the write door refuses and what the new
`whatsapp_not_storable` detector reports; R is the C/D/E population under whichever arm of the repair
ruling is taken, which is why the detector's issue COUNT is an independent second witness to `|R|`.

**The run NEVER CLEARS a value to make a note convert.** Emptying a class-D value would move it out of R
and reach part (1)'s zero trivially, by deleting the population this item exists to preserve. Clearing is a
repair somebody ASKS for through a delta arm, never something the run decides.

**Back-out.** Reverting the library is NOT a back-out: a list-shaped note against pre-WI-032 code fails
validation and lands on the load skip surface, INVISIBLE rather than oddly shaped. The back-out is a
REVERSE migration through the same door, exact up to the 82 canonical re-spellings above, and only while no
note carries a second JID — true on the day this ships, because this item makes the shape available and
does not itself populate second JIDs. Once a second JID exists anywhere the position is forward-only with
the tolerant reader kept, and §5 records that window closing.

## 3. Blast radius — the consumer breaks, read against the linter and against the audit

Every break below is tripped by the VALUE becoming a list, and NONE by the door refusing anything. Measured
in `docs/wi-032-consumer-audit.md` across three repos at pinned HEADs; that artifact's ordered list is SEVEN
sites. The two LOUD ones are the ordered list here. The third stands outside it, in its own row, for the
reason that row states.

**The two LOUD breaks** — each announces itself the instant it breaks, is therefore self-limiting, and is
repairable at leisure:

1. `orchestrator/src/invariants.py:663-665` — `person_field_shapes_correct` goes RED vault-wide, for every
   person carrying a non-empty list; the baseline ratchet does not cover shape. HEAD
   `27cb78cc5a2099972dccea984664193e69414def`.
2. `HAL9000/backend_fastapi/routers/contacts.py:41,50` — `/api/contacts` starts 500ing for every such
   person. HEAD `fb2b6c431d9edb639ba9b9ab79ab5f9a5ad1307d`.

### DATA-LOSS HOLD

`orchestrator/bin/merge-duplicate-persons.py:380-384` — HEAD
`27cb78cc5a2099972dccea984664193e69414def`. **Stated as its own row and not as item three of the list
above, because it is the only one of the three that does not announce itself.** It regex-reads a single
`whatsapp` LINE, merges scalars and re-emits `whatsapp: "<v>"` through a raw file write — outside the
package boundary, so it bypasses `PersonRepository` and therefore the write door entirely. Against a
migrated vault it can silently collapse a person's list to ONE value, or blank the field to `""` when its
single-line regex misses a block-YAML list (the clearing path measured at
`docs/wi-032-consumer-audit.md:202-204`). That is the exact harm this item exists to prevent, arriving
silently.

- **Reaching callers:** `bin/apply-vault-review.py:152,158`.
- **THE CONDUCTOR INSTRUCTION, which is what makes this a hold rather than a note:** after the migration,
  neither `merge-duplicate-persons.py` nor `apply-vault-review.py` is to be run against the vault until
  that repository's own item fixes the writer.
- Not this repo's to fix (`## Scope Boundary`): it edits frontmatter as TEXT outside the package boundary,
  so `## Intent`'s "every writer refuses it at the boundary" is false of it BY DESIGN — a named exclusion,
  and already on the WI-029 divergence-generator list. Declining the fix is not declining the disclosure.

**Items 4–7 of the audit's seven-site list** are carried as a pointer rather than re-listed:
`docs/wi-032-consumer-audit.md:227-239` (`find-duplicate-persons.py`, `generate-vault-review.py:450`, the
enricher role's PATCH body, and the two latent `ContactInfo` mirrors). HEAD for the exocortex mirror:
`58aaac03386a7a9e20ef5889539193b5e58c1a36`.

**The resolution fix's own blast radius, stated narrowly because the census's §2 is slightly over-broad
about it.** The census measures ZERO live collisions of the HARMFUL shape — a query for a REAL stored
number returning a lid's owner — so "the resolution fix changes no live lookup result" is true of THAT row.
It is over-broad for the other shape: 26 vault notes store a lid whose digits sit in the phone index today,
so a query for a number NOBODY holds can still return one of those 26 people, and this item retires exactly
that. No consumer synthesizes such a query (orchestrator strips the JID first; HAL9000's
`resolve_by_whatsapp` has no production caller). So the entry figure is **26 notes leave the phone index,
0 live answers move** — not "no lookup result changes".

## 4. The booked hand repairs — entry counts

| repair | entry | note |
|---|---|---|
| class-D notes needing a hand repair (clear the field, or write a properly spelled JID) | 0 | the census measures class D at zero |
| class-E notes needing a hand repair | 0 | the census measures class E at zero |
| **the residual R, total booked for hand repair** | **0** | Ruling B leg 2 prices at nothing today: after the class-C repair pass, no live note holds a value the whole-record arms would refuse |

The `whatsapp_not_storable` detector therefore ships against an EMPTY live population, which is the right
way round — it is the wall against the NEXT bare number, not a backlog.

## 5. Post-build attestation

*Named empty section — the EXIT half of the bracket. The conductor fills it after the live run, before the
ship commit: same vault, the §0 commands, `--report` never `--fix`. The check that reads this document
asserts this HEADING exists and asserts NOTHING about its content, so the exit figures cannot redden the
floor at the moment the item closes. The redaction predicate still holds over this section, because what it
carries is counts.*

The exit figures are the TERMINAL-STATE PARTITION's three parts, counts only, in the order `## Approach`
step (4) and AC-5 leg (e) state them, with part (2)'s two named sub-counts — plus the two corpus-wide
conjuncts:

| figure | entry | exit |
|---|---|---|
| (1) notes left in the SCALAR shape OUTSIDE R | 1168 | |
| (2) MIGRATED — now carrying the LIST form | 0 | |
| ⤷ sub-count: SHAPE-ONLY conversions (class Ø, key present) | 0 | |
| ⤷ sub-count: class-C REPAIRS | 0 | |
| (3) the residual R — reported, byte-identical, terminally scalar | 0 | |
| `whatsapp_not_storable` issue count (the INDEPENDENT second witness to the residual R) | n/a — the detector does not exist pre-build | |
| identifier-key multiset unchanged corpus-wide | n/a | |
| values CLEARED by the run | n/a — the run never clears | |

The two counts of part (3) are taken by DIFFERENT tools — the migration's own readback and the linter's
detector — and must agree; a disagreement is the bracket's failure signal, not a figure to adjudicate in
prose.

**Also recorded at exit:** the incident replay. A write of the Kim Faura value into `whatsapp:` on a
DISPOSABLE person note through HAL9000's PATCH door, confirmed refused, with the note's bytes unchanged and
the note still editable for everything else. Never Kim Faura's own note and never any production record.
The transcript is redacted before anything from it is recorded here — the run is live, the transcript is
not.
