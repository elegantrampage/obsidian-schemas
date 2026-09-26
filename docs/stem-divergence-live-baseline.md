# WI-029 stem/name divergence — live baseline (the ENTRY half of the bracket)

Conductor-performed, 2026-09-21 16:11 BST, read-only, committed as WI-029's first `kind: precondition` /
`grounds:` fence (`docs/filename-name-divergence-repair.md` → `## Write Targets`) BEFORE the acceptance
criteria are frozen. Precedents: `docs/vault-shape-census.md` (the census whose predicate this reuses),
`docs/lint-vault-live-baseline.md` (the entry/exit bracket shape). Privacy wall, as both: counts, classes
and directions only — no stem, no stored name, no note bytes, no absolute vault path; the vault root is
rendered `$VAULT` (the script reads it from `OBSIDIAN_VAULT_PATH`).

- **Vault:** `$VAULT`, Dave's live Obsidian vault; `live` = the census's predicate (no dot-directory,
  none of `_quarantine`, `_merged_dupes`, `Templates`).
- **Tree:** obsidian-schemas HEAD `b7befd0c66460560c887549a2efc93b1e0f09451` (pre-build; the package as
  it stands before WI-029 touches it). **Interpreter:** the project's own `.venv/bin/python`, run from the
  repo root with `PYTHONPATH=.` (the `.venv` editable install is deliberately stale — `pipeline-runners.yaml`).
  No absolute path appears anywhere in this file, so a whole-file privacy scan is legal against it.
- **The door run for (b3)** is `gate_write(fm, declared_type=fm.get("type"), whole_record=True)` — the
  exact call `write_markdown_file` makes — and never a bare `validate_strict`; the fence's `why:` says
  why (the `sentinel_exempt` branch).

## 0. The measurement — one script, run once, stdout verbatim

The census's own `stem_name_divergence` predicate is the FIRST count (`docs/vault-shape-census.md:209`,
re-executed here inside the script rather than re-spelled). Everything else is derived in the same walk.

```
PYTHONPATH=. .venv/bin/python wi029_baseline.py      # from the obsidian-schemas repo root
```

```python
import os, re, sys, pathlib, logging
logging.disable(logging.CRITICAL)
V = pathlib.Path(os.environ["OBSIDIAN_VAULT_PATH"])
X = {'_quarantine','_merged_dupes','Templates'}
def live(p):
    return not any(s.startswith('.') or s in X for s in p.relative_to(V).parts)
files = [p for p in sorted(V.rglob('*.md')) if live(p)]
from obsidian_schemas.parser import parse_frontmatter
from obsidian_schemas.name_gate import gate_write
from obsidian_schemas.errors import NameGateRefusal
from obsidian_schemas import PersonRepository

def fm_of(p):
    t = p.read_text(encoding='utf-8', errors='replace')
    r = parse_frontmatter(t)
    return (r[0] if isinstance(r, tuple) else r) or {}

# (a) divergence count — census predicate verbatim, and conflicts
div = []
for p in files:
    t = p.read_text(encoding='utf-8', errors='replace').split('---')
    if len(t) > 2 and re.search(r'^type: *person *$', t[1], re.M):
        m = re.search(r'^name: *["\']?(.*?)["\']? *$', t[1], re.M)
        if m and p.stem != '@' + m.group(1):
            div.append((p, m.group(1)))
print("DIVERGENT (census predicate):", len(div))
repo = PersonRepository(V)
print("CONFLICTS len(PersonRepository(V).conflicts):", len(repo.conflicts))
print("PERSON NOTES loaded:", len(repo.get_all()))

# (b)+(c) per row — counts and classes only; no stem, no name, no path
def shape(stem, name):
    s = stem.lstrip('@'); n = name
    if s.replace("'", "") == n.replace("'", "") and s != n: return "apostrophe-differs"
    if s == n.replace(" ", ""): return "run-together-stem"
    st, nt = s.split(), n.split()
    if len(st) == 1 and len(nt) > 1 and st[0] == nt[0]: return "first-name-only-stem"
    if sorted(st) == sorted(nt): return "token-order-swapped"
    if set(st) < set(nt): return "name-has-extra-token(s)"
    if set(nt) < set(st): return "stem-has-extra-token(s)"
    if not stem.startswith('@'): return "non-@-stem (book-titled?)"
    return "other"
all_text = {p: p.read_text(encoding='utf-8', errors='replace') for p in files}
print("\nROW | shape | stem-starts-@ | dest_occupied | gate(pattern) | wikilinks_to_old_stem | attendees_refs | company_refs | top_dir")
for i, (p, name) in enumerate(div, 1):
    fm = fm_of(p)
    dest = (V / p.relative_to(V).parent / f"@{name}.md")
    occupied = dest.exists() and dest.resolve() != p.resolve()
    try:
        gate_write(fm, declared_type=fm.get("type"), whole_record=True); gate = "WRITTEN"
    except NameGateRefusal as e:
        gate = f"REFUSED:{getattr(e,'pattern',None)}"
    except Exception as e:
        gate = f"OTHER:{type(e).__name__}"
    old = p.stem
    wl = sum(t.count(f"[[{old}]]") + t.count(f"[[{old}|") for q, t in all_text.items() if q != p)
    att = sum(1 for q, t in all_text.items() if q != p and re.search(r'^attendees:', t, re.M) and old in t)
    comp = sum(1 for q, t in all_text.items() if q != p and re.search(rf'^company: *["\']?{re.escape(old.lstrip("@"))}["\']? *$', t, re.M))
    print(f"{i} | {shape(old, name)} | {old.startswith('@')} | {occupied} | {gate} | {wl} | {att} | {comp} | {p.relative_to(V).parts[0] if len(p.relative_to(V).parts)>1 else '<root>'}")

# booked hand repairs
person_non_at = [p for p in files if re.search(r'^type: *person *$', all_text[p].split('---')[1] if len(all_text[p].split('---'))>2 else '', re.M) and not p.stem.startswith('@')]
untyped = [p for p in files if all_text[p].startswith('---') and len(all_text[p].split('---'))>2 and not re.search(r'^type:', all_text[p].split('---')[1], re.M)]
unclosed = [p for p in files if all_text[p].startswith('---') and all_text[p].count('\n---') == 0]
print("\nBOOKED HAND REPAIRS: type:person with non-@ stem:", len(person_non_at), "| frontmatter but no type::", len(untyped), "| fence opened never closed:", len(unclosed))
print("  untyped dirs:", sorted({(p.relative_to(V).parts[0] if len(p.relative_to(V).parts)>1 else '<root>') for p in untyped}), "| unclosed dirs:", sorted({(p.relative_to(V).parts[0] if len(p.relative_to(V).parts)>1 else '<root>') for p in unclosed}))
```

```
DIVERGENT (census predicate): 8
CONFLICTS len(PersonRepository(V).conflicts): 0
PERSON NOTES loaded: 1171

ROW | shape | stem-starts-@ | dest_occupied | gate(pattern) | wikilinks_to_old_stem | attendees_refs | company_refs | top_dir
1 | stem-has-extra-token(s) | True | False | WRITTEN | 2 | 0 | 0 | <root>
2 | other | True | False | WRITTEN | 3 | 1 | 0 | <root>
3 | other | True | True | WRITTEN | 0 | 0 | 0 | <root>
4 | token-order-swapped | True | False | WRITTEN | 3 | 2 | 0 | <root>
5 | first-name-only-stem | True | False | WRITTEN | 0 | 0 | 0 | <root>
6 | apostrophe-differs | True | False | WRITTEN | 13 | 11 | 0 | <root>
7 | other | True | False | WRITTEN | 0 | 0 | 0 | <root>
8 | non-@-stem (book-titled?) | False | True | WRITTEN | 0 | 0 | 0 | <root>

BOOKED HAND REPAIRS: type:person with non-@ stem: 1 | frontmatter but no type:: 4 | fence opened never closed: 0
  untyped dirs: ['<root>', 'Notes', 'Resources'] | unclosed dirs: []
```

## 1. Entry figures

| figure | entry (2026-09-21) |
|---|---|
| divergent live person notes (census predicate) | 8 |
| `len(PersonRepository($VAULT).conflicts)` (load-time identity conflicts) | 0 |
| person notes loaded | 1,171 |
| divergent rows the WRITE DOOR refuses (b3) | 0 of 8 |
| divergent rows that are `pure_digit` / sentinel-exempt | 0 of 8 (the two live pure-digit notes are NOT divergent) |
| destination `@{name}.md` occupied (b2) | 1 of 8 by a DIFFERENT note (row 8); 1 of 8 by the SAME file under the case-insensitive filesystem (row 3) — see §2 |
| incoming wikilinks naming an old stem (c) | 24 |
| `attendees:`-carrying notes naming an old stem (c) | 14 |
| `company:` values naming an old stem (c) | 0 |
| booked repair: `type: person` note with a non-`@` (book-titled) stem | 1 (= row 8) |
| booked repair: frontmatter present, no `type:` | 4 (2 at the vault root with underscore stems, 1 under Notes, 1 under Resources) |
| booked repair: frontmatter that does not parse (`parse_error`, `lint_vault --report` 2026-09-21 07:03) | 3 (all at the vault root; the fence-never-closed sub-shape is 0) |

The (a) COMPANION reading: conflicts were **not** 0 at the day's first load — a two-note conflict on one
identifier was observed at 07:03 (1,172 person notes) and had been merged by the 08:xx re-read
(1,171) — which is exactly why this bracket has two readings and a single one is not a baseline.

## 2. The direction, per row — (b1) which side is correct, (b2) occupancy, (b3) the door, (c) blast radius

Row numbers are the script's, in sorted-path order. (b1) is the conductor's call, on one rule: the stored
`name:` is the library's identity (save binds from it, the gate validates it), and in every rename row
below it is also the WELL-FORMED side; Dave may override any row at sign-off.

| row | shape (census class) | (b1) correct side | (b2) dest occupied | (b3) door | (c) refs in | direction |
|---|---|---|---|---|---|---|
| 1 | stem carries extra tokens (a middle name + an honorific); name is the short canonical | name | no | WRITTEN | 2 wikilinks | RENAME — retarget 2 links |
| 2 | run-together lower-case stem carrying an initial | name | no | WRITTEN | 3 wikilinks + 1 attendees note | RENAME |
| 3 | **case-only** divergence (one token's capitalisation) | name | same-file — the destination resolves to THIS note under the case-insensitive filesystem, not to a different note | WRITTEN | 0 | RENAME — a case-only change; `vault_io.move_note`'s "destination exists" refusal would misfire here (source and destination are one inode), so the door needs a same-file check and a two-step move via a temporary stem |
| 4 | token order swapped (surname-first stem) | name | no | WRITTEN | 3 wikilinks + 2 attendees notes | RENAME |
| 5 | first-name-only stem | name | no | WRITTEN | 0 | RENAME |
| 6 | apostrophe dropped from the stem | name | no | WRITTEN | **13 wikilinks + 11 attendees notes** — the largest blast radius | RENAME |
| 7 | stem is not a person name (a run-together label repeating the first name around a product-like word) | name | no | WRITTEN | 0 | RENAME |
| 8 | a **book-titled file** (no `@`, at the vault root) holding `type: person` | name — but the person's own `@{name}.md` ALREADY EXISTS as a different note | different-note | WRITTEN | 0 | MERGE — never rename: fold the book-titled file into the existing person note (or re-type it); this is booked hand repair G5(a) |

The `direction` column's leading token is one of `RENAME`, `MERGE`, `FIELD-REPAIR` and the `(b2)` column is one
of `no`, `same-file`, `different-note` — the shapes a reader asserts. Totals: **7 RENAME** (one of them a
case-only change, row 3) + **1 MERGE** (row 8) + **0 FIELD-REPAIR**; **0 gate-refused**, so no row is a
FIELD-REPAIR by refusal and the sentinel-exempt question has no live member today. Two
consequences for the criteria: the collision-pair door test (AC-2) has its live-shaped member in row 8
(occupied by a different note) and its case-only member in row 3 (occupied by itself); and the "cannot be
repaired by renaming" marker (AC-3(c)) has exactly one true live subject, row 8.

## 3. Blast radius, read against the linter

This project's linter resolves references by STEM and not by alias (`scripts/lint_vault.py`
`build_indexes`), so every rename converts each incoming reference into a `broken_wikilink` /
`meeting_attendee_not_found` warning until retargeted: 24 wikilinks and 14 attendee-carrying notes,
concentrated in row 6 (13 + 11) and rows 2 and 4. `company:` values name no old stem. The accepted-noise
disposition in the work item covers this population; the alias kept on the moved note covers the
library's own resolvers, not the linter's.

## 4. The booked hand repairs — entry counts

| repair | entry |
|---|---|
| `type: person` under a book-titled, non-`@` stem (G5(a)) | 1 — row 8 above |
| frontmatter present, no `type:` (G1 bucket (b)) | 4 |
| frontmatter that does not parse (G1 bucket (d)) | 3, all at the vault root (`lint_vault --report`, `parse_error`) |

## 5. Post-build attestation

*Named empty section — the EXIT half of the bracket. The conductor fills it at `ready → done`, before the
ship commit, same vault, same script, `--report`/`-q` never `--fix`; the item's repairs are the ONLY
intended movement.*

Commands to re-run verbatim: (1) the §0 script; (2) `scripts/lint_vault.py --vault "$VAULT" --report`
for the `parse_error` count.

| figure | entry | exit |
|---|---|---|
| divergent live person notes | 8 | **0** |
| `len(PersonRepository($VAULT).conflicts)` | 0 | **0** |
| person notes loaded | 1,171 | 1,173 |
| rows gate-refused | 0 | 0 (no rows) |
| destination occupied by a different note | 1 | 0 (no rows) |
| incoming wikilinks naming an old stem | 24 | 0 |
| attendees notes naming an old stem | 14 | 0 |
| book-titled `type: person` | 1 | 0 |
| untyped frontmatter | 4 | 2 — the two that are not entity notes (a strategy note under Notes, a prompt file under Resources); the two person-shaped root notes were DUPLICATES of existing canonical notes and were quarantined |
| `parse_error` | 3 | 0 |
| post-build HEAD | — | `187f5e5920e9e9a360333741b235c1a4041b2228` + the WI-029 build in the working tree (this attestation ships in the same commit as the build) |

**Exit run — conductor-performed, 2026-09-26 15:31 BST, on Dave's in-session go ("proceed with the
sequence as proposed"), same vault, same §0 script verbatim, `--report`/`-q` only after the repair.**
Pre-repair re-run of §0 at 15:10 (close-out step 1): the direction TABLE was UNCHANGED from 2026-09-21 —
eight rows, same shapes, same (b2)/(b3) answers, 1,173 people (+2 drift), conflicts 0 — so no drift
report was owed. The repair (close-out step 2), every write through `vault_io`'s doors, nothing deleted:

- **7 RENAME through `BaseRepository.rename_note`** (guard `enforce`; every entity resolved to its own
  file by provenance before the call): 7 of 7 moved, readback per row — new stem on disk, exactly one
  directory entry (the case-only row 3 took the two-step branch and left no staging file), the old stem
  in `aliases` (five rows already carried it from an earlier repair; the door appended the other two).
- **1 MERGE (row 8):** the canonical person note already held every identifier the book-titled file
  carried, so no field moved; the book-titled file went to `_quarantine/` through `move_note`.
- **2 of the 4 untyped notes** were person-shaped root notes whose canonical `@{name}.md` ALREADY existed
  (duplicates, not divergences): canonical notes already complete, both quarantined through `move_note`.
  The other two untyped notes are not entity notes and were left as they are.
- **3 `parse_error` book notes:** root cause is a `parser.py:parse_frontmatter` weakness, not the notes'
  quoting — the fence regex's optional newline lets a ` --- ` INSIDE a quoted `description:` close the
  frontmatter mid-line. Repaired by replacing the in-text `---` with an em dash and re-quoting the
  field, written with a read-note precondition, every other key verified equal before and after; a
  library fix is minted separately (HANDOFF).
- **21 incoming wikilinks in 21 non-person notes retargeted** from the old stems to the new (the door's
  alias is the stem without `@`, so `[[@old]]` links would otherwise go dark in Obsidian); 0 remain.

`scripts/lint_vault.py --vault "$VAULT" --report`: exit 0, stdout 1,405,384 bytes,
`sha256 = c2b2dc3d442d3ce07cc1c21ccaa446bb6bb8e000029c5abeaff785e4293db5f7`; `-q`: 4,008 files scanned,
4,838 issues, **0 errors** (`stem_name_divergence` and `parse_error` both silent). `broken_wikilink` reads 70
against 68 on 2026-09-21; none of the 70 names a renamed or quarantined stem — five days of vault drift
(+21 files). The §0 script's exit stdout, verbatim:

```
DIVERGENT (census predicate): 0
CONFLICTS len(PersonRepository(V).conflicts): 0
PERSON NOTES loaded: 1173
ROW | shape | stem-starts-@ | dest_occupied | gate(pattern) | wikilinks_to_old_stem | attendees_refs | company_refs | top_dir
BOOKED HAND REPAIRS: type:person with non-@ stem: 0 | frontmatter but no type:: 2 | fence opened never closed: 0
  untyped dirs: ['Notes', 'Resources'] | unclosed dirs: []
```

**Ship condition MET: divergence 0, conflicts 0.**
