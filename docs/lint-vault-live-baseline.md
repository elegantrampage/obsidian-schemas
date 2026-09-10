# WI-026 lint_vault live baseline — the ENTRY half of the bracket

Conductor-performed, 2026-09-10 11:10 BST, committed as WI-026's `kind: precondition` / `grounds:` fence
(`docs/lint-vault-fix-safety.md` → `## Write Targets`) BEFORE the acceptance criteria are presented and
BEFORE the build changes what `read_vault` returns. Precedent: `docs/company-name-corpus-audit.md`. The
privacy wall reaches this artifact the way it reaches the census: counts only — no note filename, no
byte of any note, no absolute path (the one occurrence of the vault path in the linter's own header line
is rendered as `$VAULT` below; that is the only substitution in any verbatim block).

- **Vault:** `$VAULT` is the root of Dave's Obsidian vault (the `DaveRemoteVault` folder), exported in the
  shell; read-only throughout. `--report` and never `--fix`.
- **Tree:** obsidian-schemas HEAD `e0ffbe860937ec775d286521181358ccdd2aec06` (pre-build; `scripts/lint_vault.py` as
  it stands before WI-026 touches it).
- **Interpreter:** `/Users/davewascha/Workspaces/obsidian-schemas/.venv/bin/python` (the project floor's).
  `lint_vault.py` exits 1 whenever it reports any issue; both runs below exited 1.

## 0. The run

Command (the JSON report; its stdout is 1,380,432 bytes and names live notes, so it is NOT reproduced —
its digest is, so a re-run on the same vault snapshot can be compared byte-for-byte):

```
/Users/davewascha/Workspaces/obsidian-schemas/.venv/bin/python /Users/davewascha/Workspaces/obsidian-schemas/scripts/lint_vault.py --vault "$VAULT" --report
```

Result: exit 1; stdout 1,380,432 bytes; `sha256 = b5c69cec51eece150f7e5d3657034ab5cce75f0e4da7743da688a3f15bb24b4b`;
4,764 issues over 3,952 files scanned (the `-q` summary of the same walk, verbatim, is the human-readable
form and carries every count this artifact uses):

```
/Users/davewascha/Workspaces/obsidian-schemas/.venv/bin/python /Users/davewascha/Workspaces/obsidian-schemas/scripts/lint_vault.py --vault "$VAULT" -q
```

```

Vault Lint Report — $VAULT
========================================================================
3,952 files scanned in 4.0s | 4,764 issues (3 errors, 1712 warnings, 3049 info)

COMPLETENESS (1,674 issues)
  person_no_email ..................... 167 warnings
  company_no_website .................. 660 infos
  person_no_company ................... 358 infos
  person_no_linkedin .................. 489 infos

LINK INTEGRITY (563 issues)
  broken_wikilink ..................... 68 warnings
  company_people_link_broken .......... 42 warnings
  meeting_attendee_not_found .......... 151 warnings
  person_company_not_found ............ 106 warnings
  person_not_in_company_people ........ 196 infos

TIMELINE (324 issues)
  intro_not_symmetric ................. 7 warnings
  meeting_missing_from_timeline ....... 315 warnings  [315 auto-fixable]
  timeline_meeting_not_found .......... 2 warnings

NOISE & GARBAGE (1,346 issues)
  garbage_candidate_company ........... 3 infos
  garbage_candidate_person ............ 34 infos
  orphaned_note ....................... 1,253 infos
  possible_duplicate .................. 56 infos

STRUCTURAL (857 issues)
  parse_error ......................... 3 errors
  field_type_mismatch ................. 19 warnings  [19 auto-fixable]
  missing_body_sections ............... 835 warnings  [835 auto-fixable]

Auto-fixable: 1169 issues. Run with --fix to apply.
```

## 1. The five auto-fixable counts (vs `docs/vault-shape-census.md:272-281`, measured 2026-09-07)

Derived from the JSON report by `check` name where `auto_fixable` is true (the census keyed its table by
message shape; the mapping is one-to-one and stated):

| `check` (auto_fixable=True) | census 2026-09-07 (message shape) | today 2026-09-10 | delta |
|---|---|---|---|
| `missing_body_sections` | 821 (`Missing sections: …`) | 835 | +14 |
| `meeting_missing_from_timeline` | 315 (`Attended [[…]] but it's not in Timeline`) | 315 | 0 |
| `field_type_mismatch` | 19 (`auto_created is string '…' instead of bool`) | 19 | 0 |
| `person_missing_name` | 0 (`Empty name (suggest: '…')`) | 0 | 0 |
| `broken_wikilink` (the `fixable →` sub-case) | 0 (`[[…]] doesn't resolve (fixable → [[…]])`) | 0 | 0 |
| **total auto-fixable** | **1,155 of 4,730** | **1,169 of 4,764** | +14 / +34 |

The +14 is three days of vault growth in one rule (new notes missing body sections); it is the staleness
signal AC-5 exists to raise, not an error in either measurement. Two of the five rules have no live subject
today; AC-1's oracle set still covers all five because it derives the rule set from the script's syntax,
never from these counts.

## 2. The five stem-keyed check counts (pre-change baseline)

The checks this item's `read_vault` change moves (`scripts/lint_vault.py:463`, `:482`, `:497`, `:513`,
`:722`), from the same report:

| `check` | count today |
|---|---|
| `person_company_not_found` | 106 |
| `meeting_attendee_not_found` | 151 |
| `company_people_link_broken` | 42 |
| `broken_wikilink` | 68 |
| `orphaned_note` | 1,253 |

## 3. The undecodable scan

Standalone count over `read_vault`'s own walk — `vault_path.rglob("*.md")` minus `should_skip`
(`SKIP_DIRS = {".obsidian", "Templates", "src", ".trash", "_quarantine", "_merged_dupes"}`,
`scripts/lint_vault.py:58,105-118`) — of paths for which `read_text(encoding="utf-8")` raises. Count and
nothing else, by contract.

```
/usr/bin/python3 -c "from pathlib import Path;V=Path('$VAULT');S={'.obsidian','Templates','src','.trash','_quarantine','_merged_dupes'};w=[m for m in sorted(V.rglob('*.md')) if not any(p in S for p in m.relative_to(V).parts)];u=0
for m in w:
  try: m.read_text(encoding='utf-8')
  except Exception: u+=1
print('paths walked:',len(w));print('undecodable:',u)"
```

```
paths walked: 3952
undecodable: 0
```

**Zero undecodable notes today.** The `read_error` path this item adds to `read_vault` has no live subject
on this snapshot; its oracle is therefore the fixture corpus's one deliberately non-UTF-8 member (WI-016
§1.3 rule 4), and the live-vault half of the bracket can only confirm the count stays 0 after the build.

## 4. Post-build attestation

*Named empty section — the EXIT half of the bracket. The conductor fills it at `ready → done`, before the
ship commit, on the same vault, with the same commands, and it is a ship condition of this item.*

Commands to re-run verbatim (same interpreter, same flags, `--report` never `--fix`):

1. `scripts/lint_vault.py --vault "$VAULT" -q` — record verbatim.
2. `scripts/lint_vault.py --vault "$VAULT" --report` — record exit code, stdout byte count, sha256.
3. The §3 undecodable one-liner — record `paths walked` and `undecodable`.

Figures to fill, each as `entry → exit`:

| figure | entry (this file) | exit |
|---|---|---|
| files scanned | 3,952 | |
| issues total | 4,764 | |
| auto-fixable total | 1,169 | |
| `missing_body_sections` | 835 | |
| `meeting_missing_from_timeline` | 315 | |
| `field_type_mismatch` | 19 | |
| `person_missing_name` | 0 | |
| `broken_wikilink` fixable sub-case | 0 | |
| `person_company_not_found` | 106 | |
| `meeting_attendee_not_found` | 151 | |
| `company_people_link_broken` | 42 | |
| `broken_wikilink` | 68 | |
| `orphaned_note` | 1,253 | |
| paths walked | 3,952 | |
| undecodable | 0 | |
| post-build HEAD | — | |

A moved stem-keyed count is the delta this item exists to make visible; a moved auto-fixable count is
vault drift between the two runs unless the run dates are the same day. Post-build HEAD SHA, run date and
the report digest go here too.
