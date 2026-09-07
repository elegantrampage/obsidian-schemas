# WI-016 vault-shape census — the grounding artifact for the acceptance-criteria frame

Conductor-performed, 2026-09-07, committed as WI-016's `kind: precondition` / `grounds:` fence
(`docs/vault-fixtures.md` → `## Write Targets`) BEFORE Dave signs the criteria. WI-016 is a pre-epoch item
(created 2026-03-22), so the WI-300 door that pauses a drive for this artifact was epoch-skipped and the
item reached `specced` without it; the origination CLI refused fail-closed on the absent path
(`ac_signoff.originate_signoff`, exit 3), which is the wall doing its job one layer later. This file is
what it asked for. Precedents: `docs/wi-024-consumer-audit.md`, `docs/company-name-corpus-audit.md`,
`docs/identity-cutover-corpus-audit.md`.

**What it settles (the fence's `grounds:`):** which note shapes the frozen corpus must cover, measured from
the live vault rather than remembered. Machine surface per Design §2: `census-meta` (one), `census-class`
(one per shape class), `census-pool` (one per certified identity token). Everything else here is prose.

## Method

- **Vault:** `$VAULT` = `/Users/davewascha/Documents/Obsidian/DaveRemoteVault`, read-only.
- **LIVE population:** every `*.md` whose frontmatter carries `type: <t>`, EXCLUDING dot-directories and
  the three non-live directories `_quarantine/`, `_merged_dupes/` and `Templates/`. Excluding them is what
  makes the person count (1150) agree with `PersonRepository`'s own load (1147 on 2026-09-06) to within
  the three notes the repository additionally skips. Whole-vault figures, where they differ materially,
  are given in prose beneath the row.
- **Person-name extraction (every branch row and four shape rows):** the FIRST `name:` line of each live
  person note, surrounding single or double quotes removed, interior spacing untouched, null-delimited so
  filenames carrying apostrophes survive `xargs`. Every command is ONE line, run under `LC_ALL=C` with
  `$VAULT` exported, and EMITS A COUNT (`grep -c`, `wc -l`, or a `print(n)`), so an honest zero records
  verbatim as `0`. The Python one-liners use `/usr/bin/python3` (stdlib only).
- **Branch rows** apply the package's own Tier-1 regexes (`obsidian_schemas/name_validation.py:60-123`)
  transliterated to `grep -E`; `id` is the `branch_id` itself. **Hand-listed rows** use the six ids AC-3
  reconciles against this artifact: `diacritics`, `hyphenated_surname`, `whitespace_damage`,
  `stem_name_divergence`, `same_name_collision`, `postal_address_in_name`.
- **Specimens** are constructed strings carrying the measured character profile; every identity-position
  token in them is certified below in the pool table; emails are RFC 2606 (`example.com`); phones are in
  Ofcom's reserved drama range (`07700 900xxx`). `Dave` is CONNECTIVE furniture (AC-5(b)), never pooled.

## Header

```census-meta
snapshot: 2026-09-07
vault_notes_person: 1150
vault_notes_company: 659
vault_notes_meeting: 1640
vault_notes_book: 279
vault_notes_watch: 2
vault_notes_explore: 23
vault_notes_gift_idea: 1
vault_notes_exploration: 7
```

`gift-idea` is keyed `vault_notes_gift_idea` (fence keys are identifiers). Whole vault, dot-dirs only excluded: person 1281, company 2160 — the remainder live in `_merged_dupes/` and `_quarantine/`.

## Class table

Branch-backed rows first, in `TIER1_BRANCHES` declaration order, then the six hand-listed shape classes.

### `email_chars`

```census-class
id: email_chars
count: 0
status: ABSENT
command: grep -rl --null -E --include='*.md' --exclude-dir='.*' --exclude-dir=_quarantine --exclude-dir=_merged_dupes --exclude-dir=Templates '^type: *person *$' "$VAULT" | xargs -0 -I{} grep -m1 -h '^name:' {} | sed -E "s/^name: *[\"']?//; s/[\"']$//" | grep -cE '@'
stdout: 0
ruling: No live person note's stored name contains '@'.
```

### `rfc2822_leak`

```census-class
id: rfc2822_leak
count: 0
status: ABSENT
command: grep -rl --null -E --include='*.md' --exclude-dir='.*' --exclude-dir=_quarantine --exclude-dir=_merged_dupes --exclude-dir=Templates '^type: *person *$' "$VAULT" | xargs -0 -I{} grep -m1 -h '^name:' {} | sed -E "s/^name: *[\"']?//; s/[\"']$//" | grep -cE '\b[a-z][a-z0-9._-]{4,}(com|net|org|io|ai|uk|co|gov|edu|app|biz)\b'
stdout: 0
ruling: No live person note's stored name carries an at-mangled lowercase email run fused onto it.
```

### `arrow_connective`

```census-class
id: arrow_connective
count: 0
status: ABSENT
command: grep -rl --null -E --include='*.md' --exclude-dir='.*' --exclude-dir=_quarantine --exclude-dir=_merged_dupes --exclude-dir=Templates '^type: *person *$' "$VAULT" | xargs -0 -I{} grep -m1 -h '^name:' {} | sed -E "s/^name: *[\"']?//; s/[\"']$//" | grep -c -e '->' -e '→' -e '⟶' -e '⇒' -e '➜' -e '↦' -e '⇨'
stdout: 0
ruling: No live person note's stored name contains a connective arrow.
```

### `calendar_prefix`

```census-class
id: calendar_prefix
count: 0
status: ABSENT
command: grep -rl --null -E --include='*.md' --exclude-dir='.*' --exclude-dir=_quarantine --exclude-dir=_merged_dupes --exclude-dir=Templates '^type: *person *$' "$VAULT" | xargs -0 -I{} grep -m1 -h '^name:' {} | sed -E "s/^name: *[\"']?//; s/[\"']$//" | grep -cE '^(Dave|Me|My) *[-/] +[A-Za-z0-9_]'
stdout: 0
ruling: No live person note's stored name starts with a Dave/Me/My calendar prefix followed by a dash or slash.
```

### `me_to_prefix`

```census-class
id: me_to_prefix
count: 0
status: ABSENT
command: grep -rl --null -E --include='*.md' --exclude-dir='.*' --exclude-dir=_quarantine --exclude-dir=_merged_dupes --exclude-dir=Templates '^type: *person *$' "$VAULT" | xargs -0 -I{} grep -m1 -h '^name:' {} | sed -E "s/^name: *[\"']?//; s/[\"']$//" | grep -ciE '^(Me|My) +to\b'
stdout: 0
ruling: No live person note's stored name starts with 'Me to' or 'My to' in any letter-case.
```

### `path_hostile`

```census-class
id: path_hostile
count: 0
status: ABSENT
command: grep -rl --null -E --include='*.md' --exclude-dir='.*' --exclude-dir=_quarantine --exclude-dir=_merged_dupes --exclude-dir=Templates '^type: *person *$' "$VAULT" | xargs -0 -I{} grep -m1 -h '^name:' {} | sed -E "s/^name: *[\"']?//; s/[\"']$//" | grep -cE '/'
stdout: 0
ruling: No live person note's stored name contains a forward slash.
```

### `archive_prefix`

```census-class
id: archive_prefix
count: 0
status: ABSENT
command: grep -rl --null -E --include='*.md' --exclude-dir='.*' --exclude-dir=_quarantine --exclude-dir=_merged_dupes --exclude-dir=Templates '^type: *person *$' "$VAULT" | xargs -0 -I{} grep -m1 -h '^name:' {} | sed -E "s/^name: *[\"']?//; s/[\"']$//" | grep -ciE '^z+Archived\b'
stdout: 0
ruling: No live person note's stored name starts with the zArchived convention (the one such note in the whole vault sits in _quarantine/, outside the live population — see prose).
```

### `unknown_contact`

```census-class
id: unknown_contact
count: 0
status: ABSENT
command: grep -rl --null -E --include='*.md' --exclude-dir='.*' --exclude-dir=_quarantine --exclude-dir=_merged_dupes --exclude-dir=Templates '^type: *person *$' "$VAULT" | xargs -0 -I{} grep -m1 -h '^name:' {} | sed -E "s/^name: *[\"']?//; s/[\"']$//" | grep -ciE 'unknown +contact'
stdout: 0
ruling: No live person note's stored name carries 'unknown contact' in any letter-case (the three such notes in the whole vault sit in _quarantine/ or _merged_dupes/, outside the live population — see prose).
```

### `pure_digit`

```census-class
id: pure_digit
count: 2
status: MEASURED
command: grep -rl --null -E --include='*.md' --exclude-dir='.*' --exclude-dir=_quarantine --exclude-dir=_merged_dupes --exclude-dir=Templates '^type: *person *$' "$VAULT" | xargs -0 -I{} grep -m1 -h '^name:' {} | sed -E "s/^name: *[\"']?//; s/[\"']$//" | grep -cE '^\+?[0-9]+$'
stdout: 2
specimen: +447700900123
```

### `empty`

```census-class
id: empty
count: 0
status: ABSENT
command: grep -rl --null -E --include='*.md' --exclude-dir='.*' --exclude-dir=_quarantine --exclude-dir=_merged_dupes --exclude-dir=Templates '^type: *person *$' "$VAULT" | xargs -0 -I{} grep -m1 -h '^name:' {} | sed -E "s/^name: *[\"']?//; s/[\"']$//" | grep -cE '^ *$'
stdout: 0
ruling: No live person note stores an empty or whitespace-only name; create_stub has guarded this branch out of production since it existed.
```

### `diacritics` (hand-listed)

```census-class
id: diacritics
count: 6
status: MEASURED
command: grep -rl --null -E --include='*.md' --exclude-dir='.*' --exclude-dir=_quarantine --exclude-dir=_merged_dupes --exclude-dir=Templates '^type: *person *$' "$VAULT" | xargs -0 -I{} grep -m1 -h '^name:' {} | sed -E "s/^name: *[\"']?//; s/[\"']$//" | /usr/bin/python3 -c "import sys,unicodedata;print(sum(1 for l in sys.stdin if any(ord(c)>127 and unicodedata.category(c).startswith('L') for c in l)))"
stdout: 6
specimen: Søréna Kelmarrä
```

### `hyphenated_surname` (hand-listed)

```census-class
id: hyphenated_surname
count: 29
status: MEASURED
command: grep -rl --null -E --include='*.md' --exclude-dir='.*' --exclude-dir=_quarantine --exclude-dir=_merged_dupes --exclude-dir=Templates '^type: *person *$' "$VAULT" | xargs -0 -I{} grep -m1 -h '^name:' {} | sed -E "s/^name: *[\"']?//; s/[\"']$//" | grep -cE '[[:alpha:]]-[[:alpha:]]'
stdout: 29
specimen: Oskaline Brenvik-Tarnquil
```

### `whitespace_damage` (hand-listed)

```census-class
id: whitespace_damage
count: 7
status: MEASURED
command: grep -rl --null -E --include='*.md' --exclude-dir='.*' --exclude-dir=_quarantine --exclude-dir=_merged_dupes --exclude-dir=Templates '^type: *person *$' "$VAULT" | xargs -0 -I{} grep -m1 -h '^name:' {} | sed -E "s/^name: *[\"']?//; s/[\"']$//" | grep -cE '  |^ | $'
stdout: 7
specimen: Dave  Marrowyn Fennwick
```

### `stem_name_divergence` (hand-listed)

```census-class
id: stem_name_divergence
count: 8
status: MEASURED
command: /usr/bin/python3 -c "import pathlib,re;V=pathlib.Path('$VAULT');X={'_quarantine','_merged_dupes','Templates'};print(sum(1 for p in V.rglob('*.md') if not any(s.startswith('.') or s in X for s in p.relative_to(V).parts) for t in [p.read_text(encoding='utf-8',errors='replace').split('---')] if len(t)>2 and re.search(r'^type: *person *$',t[1],re.M) for m in [re.search(r'^name: *[\"\']?(.*?)[\"\']? *$',t[1],re.M)] if m and p.stem!='@'+m.group(1)))"
stdout: 8
specimen: stem=@Quillam Ostrivane.md name=Quillam Ostrivane Lumbrek
```

### `same_name_collision` (hand-listed)

```census-class
id: same_name_collision
count: 0
status: ABSENT
command: /usr/bin/python3 -c "import pathlib,re,collections;V=pathlib.Path('$VAULT');X={'_quarantine','_merged_dupes','Templates'};c=collections.Counter(m.group(1) for p in V.rglob('*.md') if not any(s.startswith('.') or s in X for s in p.relative_to(V).parts) for t in [p.read_text(encoding='utf-8',errors='replace').split('---')] if len(t)>2 and re.search(r'^type: *person *$',t[1],re.M) for m in [re.search(r'^name: *[\"\']?(.*?)[\"\']? *$',t[1],re.M)] if m);print(sum(1 for v in c.values() if v>=3))"
stdout: 0
ruling: No stored person name is shared by three or more live notes; the largest live collision is two, and the collision class is therefore ruled a SEPARATE class from stem/name divergence, which IS measured (see the ONE-or-TWO ruling).
```

### `postal_address_in_name` (hand-listed)

```census-class
id: postal_address_in_name
count: 1
status: MEASURED
command: grep -rl --null -E --include='*.md' --exclude-dir='.*' --exclude-dir=_quarantine --exclude-dir=_merged_dupes --exclude-dir=Templates '^type: *person *$' "$VAULT" | xargs -0 -I{} grep -m1 -h '^name:' {} | sed -E "s/^name: *[\"']?//; s/[\"']$//" | grep -cE '[0-9]+ [A-Za-z]+ (Street|Road|Rd|St|Avenue|Ave|Lane|Ln|Drive|Dr|Close|Way|Place|Square)\b|\b[A-Z]{1,2}[0-9][A-Z0-9]? ?[0-9][A-Z]{2}\b'
stdout: 1
specimen: 25 Corvallen Ravensby-3rd Pellworth-Wexlund 8
```


### Prose beneath the rows

- **Furniture literals in their measured letter-case (for AC-5(b)'s one-time `CONNECTIVE_SET`
  reconciliation).** In the LIVE population every prefix/suffix branch measures 0. In the WHOLE vault the
  forms that exist are: `zArchived - Rosie Samuels` (one note, `_quarantine/`) — lowercase `z`, capital
  `A`, then ` - `; and `<digits> unknown contact` (three notes, `_quarantine/` and `_merged_dupes/`) —
  the LOWERCASE suffix form. No `Unknown Contact`, no `ME -`, no `DAVE -` form occurs anywhere.
  **Reconciliation outcome: `CONNECTIVE_SET` stays exactly `{"Me", "My", "Dave"}`** — `zArchived`
  yields no token under the extractor and the lowercase suffix yields none either.
- **`diacritics` counts non-ASCII LETTERS** (Unicode category L), so it is 6 and not 7: the seventh
  non-ASCII live name is `✨🌙 ✨`, an emoji-only name with no letter at all. That is a distinct shape
  outside the class floor (nothing in the package refuses it; `clean_person_name` passes it), recorded
  here for WI-026/lint_vault rather than given a class row, so no corpus specimen is owed for it.
- **`whitespace_damage`: all seven are the same profile** — `Dave` + TWO spaces + a name (e.g.
  `Dave  Naomi Pavie`, `Dave  Lauren King Speechmatics`): the calendar-prefix leak with its dash
  already stripped by the deleted mangler, which is why the specimen is `Dave  Marrowyn Fennwick` and
  not a plain double-spaced surname.
- **`postal_address_in_name`: MEASURED, one live note** — `25 Kingly Street-3rd Floor-Salmon 8`, a
  street address with floor and suite fused by hyphens. The specimen keeps that profile (leading number,
  hyphen-fused words, trailing digit) with every word constructed, because `Street`/`Floor`/a locality
  are ordinary vocabulary that cannot carry a zero-hit pool row.
- **`pure_digit`: both live members are `+<11-12 digits>`** (a phone stored as the name); the specimen
  is the reserved `+447700900123`.
- **`stem_name_divergence`: 8 live** (whole vault 110, of which 94 are in `_merged_dupes/`, the merge
  archive, and 5 in `_quarantine/`). The eight live shapes: a book-titled file holding a person note;
  an apostrophe dropped from the stem (`@Owen OLoan.md` / `Owen O'Loan`); a first-name-only stem; a
  suffix or middle name in one side only; token order swapped; a run-together stem (`@Clairejwallis.md`).
- **THE ONE-class-or-TWO RULING.** `same_name_collision` (≥3 live notes sharing one stored name) is
  ABSENT (largest live collision: 2) while `stem_name_divergence` is MEASURED (8). They are therefore
  TWO classes in this vault: today AC-3(i) obliges no collision specimen, and the manifest's
  covered-class set follows this ruling. §1.3 rule 5's mandated three-note collision, if the builder
  plants it, is filed under `stem_name_divergence` (structurally, a flat corpus's collision IS a
  divergence) — never as a `same_name_collision` specimen, which would be RED against this ABSENT row.
- **`lint_vault`'s five auto-fixable rules, measured on this snapshot** (`scripts/lint_vault.py --vault
  $VAULT --report`, `auto_fixable: true`, 1155 of 4730 issues; for WI-026, which `needs: WI-016`):

  | rule (message shape) | count |
  |---|---|
  | `Missing sections: …` (structural) | 821 |
  | `Attended [[…]] but it's not in Timeline` (timeline) | 315 |
  | `auto_created is string '…' instead of bool` (structural) | 19 |
  | `Empty name (suggest: '…')` (structural) | 0 |
  | `[[…]] doesn't resolve (fixable → [[…]])` (links) | 0 |

## Identity pool table

One row per token this corpus is CERTIFIED to use in an identity position. The relation AC-5(c) asserts is
`NAME_POOL ⊆ {row.token}`, a containment, so this table errs LONG: every token any specimen above uses is
here, plus spares for the builder's remaining notes. Each command counts FILES in the whole vault (dot-dirs
excluded, quarantine and merged-dupes INCLUDED — the stricter reach) carrying the token as a whole word,
case-insensitively. No connective token (`Me`, `My`, `Dave`) has a row, by design.

```census-pool
token: Tarnquil
class: surname
command: grep -rliw --include='*.md' --exclude-dir='.*' 'Tarnquil' "$VAULT" | wc -l | tr -d ' '
stdout: 0
```

```census-pool
token: Brenvik
class: surname
command: grep -rliw --include='*.md' --exclude-dir='.*' 'Brenvik' "$VAULT" | wc -l | tr -d ' '
stdout: 0
```

```census-pool
token: Oskaline
class: given-name
command: grep -rliw --include='*.md' --exclude-dir='.*' 'Oskaline' "$VAULT" | wc -l | tr -d ' '
stdout: 0
```

```census-pool
token: Dalquest
class: surname
command: grep -rliw --include='*.md' --exclude-dir='.*' 'Dalquest' "$VAULT" | wc -l | tr -d ' '
stdout: 0
```

```census-pool
token: Marrowyn
class: given-name
command: grep -rliw --include='*.md' --exclude-dir='.*' 'Marrowyn' "$VAULT" | wc -l | tr -d ' '
stdout: 0
```

```census-pool
token: Fennwick
class: surname
command: grep -rliw --include='*.md' --exclude-dir='.*' 'Fennwick' "$VAULT" | wc -l | tr -d ' '
stdout: 0
```

```census-pool
token: Quillam
class: given-name
command: grep -rliw --include='*.md' --exclude-dir='.*' 'Quillam' "$VAULT" | wc -l | tr -d ' '
stdout: 0
```

```census-pool
token: Zebrant
class: surname
command: grep -rliw --include='*.md' --exclude-dir='.*' 'Zebrant' "$VAULT" | wc -l | tr -d ' '
stdout: 0
```

```census-pool
token: Ostrivane
class: given-name
command: grep -rliw --include='*.md' --exclude-dir='.*' 'Ostrivane' "$VAULT" | wc -l | tr -d ' '
stdout: 0
```

```census-pool
token: Lumbrek
class: surname
command: grep -rliw --include='*.md' --exclude-dir='.*' 'Lumbrek' "$VAULT" | wc -l | tr -d ' '
stdout: 0
```

```census-pool
token: Halvorne
class: given-name
command: grep -rliw --include='*.md' --exclude-dir='.*' 'Halvorne' "$VAULT" | wc -l | tr -d ' '
stdout: 0
```

```census-pool
token: Sennaby
class: surname
command: grep -rliw --include='*.md' --exclude-dir='.*' 'Sennaby' "$VAULT" | wc -l | tr -d ' '
stdout: 0
```

```census-pool
token: Corvallen
class: given-name
command: grep -rliw --include='*.md' --exclude-dir='.*' 'Corvallen' "$VAULT" | wc -l | tr -d ' '
stdout: 0
```

```census-pool
token: Wexlund
class: surname
command: grep -rliw --include='*.md' --exclude-dir='.*' 'Wexlund' "$VAULT" | wc -l | tr -d ' '
stdout: 0
```

```census-pool
token: Søréna
class: given-name
command: grep -rliw --include='*.md' --exclude-dir='.*' 'Søréna' "$VAULT" | wc -l | tr -d ' '
stdout: 0
```

```census-pool
token: Kelmarrä
class: surname
command: grep -rliw --include='*.md' --exclude-dir='.*' 'Kelmarrä' "$VAULT" | wc -l | tr -d ' '
stdout: 0
```

```census-pool
token: Kelmarra
class: surname
command: grep -rliw --include='*.md' --exclude-dir='.*' 'Kelmarra' "$VAULT" | wc -l | tr -d ' '
stdout: 0
```

```census-pool
token: Voxleaf
class: company-name
command: grep -rliw --include='*.md' --exclude-dir='.*' 'Voxleaf' "$VAULT" | wc -l | tr -d ' '
stdout: 0
```

```census-pool
token: Thrandell
class: given-name
command: grep -rliw --include='*.md' --exclude-dir='.*' 'Thrandell' "$VAULT" | wc -l | tr -d ' '
stdout: 0
```

```census-pool
token: Ibberly
class: surname
command: grep -rliw --include='*.md' --exclude-dir='.*' 'Ibberly' "$VAULT" | wc -l | tr -d ' '
stdout: 0
```

```census-pool
token: Perrowin
class: given-name
command: grep -rliw --include='*.md' --exclude-dir='.*' 'Perrowin' "$VAULT" | wc -l | tr -d ' '
stdout: 0
```

```census-pool
token: Skarnell
class: surname
command: grep -rliw --include='*.md' --exclude-dir='.*' 'Skarnell' "$VAULT" | wc -l | tr -d ' '
stdout: 0
```

```census-pool
token: Ulvestre
class: company-name
command: grep -rliw --include='*.md' --exclude-dir='.*' 'Ulvestre' "$VAULT" | wc -l | tr -d ' '
stdout: 0
```

```census-pool
token: Brindlecote
class: company-name
command: grep -rliw --include='*.md' --exclude-dir='.*' 'Brindlecote' "$VAULT" | wc -l | tr -d ' '
stdout: 0
```

```census-pool
token: Tessamund
class: given-name
command: grep -rliw --include='*.md' --exclude-dir='.*' 'Tessamund' "$VAULT" | wc -l | tr -d ' '
stdout: 0
```

```census-pool
token: Harkwell
class: surname
command: grep -rliw --include='*.md' --exclude-dir='.*' 'Harkwell' "$VAULT" | wc -l | tr -d ' '
stdout: 0
```

```census-pool
token: Yolvenna
class: given-name
command: grep -rliw --include='*.md' --exclude-dir='.*' 'Yolvenna' "$VAULT" | wc -l | tr -d ' '
stdout: 0
```

```census-pool
token: Drostane
class: surname
command: grep -rliw --include='*.md' --exclude-dir='.*' 'Drostane' "$VAULT" | wc -l | tr -d ' '
stdout: 0
```

```census-pool
token: Nimbrook
class: company-name
command: grep -rliw --include='*.md' --exclude-dir='.*' 'Nimbrook' "$VAULT" | wc -l | tr -d ' '
stdout: 0
```

```census-pool
token: Caldreth
class: surname
command: grep -rliw --include='*.md' --exclude-dir='.*' 'Caldreth' "$VAULT" | wc -l | tr -d ' '
stdout: 0
```

```census-pool
token: Elowick
class: given-name
command: grep -rliw --include='*.md' --exclude-dir='.*' 'Elowick' "$VAULT" | wc -l | tr -d ' '
stdout: 0
```

```census-pool
token: Varnholt
class: surname
command: grep -rliw --include='*.md' --exclude-dir='.*' 'Varnholt' "$VAULT" | wc -l | tr -d ' '
stdout: 0
```

```census-pool
token: Ferrigan
class: surname
command: grep -rliw --include='*.md' --exclude-dir='.*' 'Ferrigan' "$VAULT" | wc -l | tr -d ' '
stdout: 0
```

```census-pool
token: Ashquill
class: company-name
command: grep -rliw --include='*.md' --exclude-dir='.*' 'Ashquill' "$VAULT" | wc -l | tr -d ' '
stdout: 0
```

```census-pool
token: Morvette
class: given-name
command: grep -rliw --include='*.md' --exclude-dir='.*' 'Morvette' "$VAULT" | wc -l | tr -d ' '
stdout: 0
```

```census-pool
token: Quenlaw
class: surname
command: grep -rliw --include='*.md' --exclude-dir='.*' 'Quenlaw' "$VAULT" | wc -l | tr -d ' '
stdout: 0
```

```census-pool
token: Ravensby
class: company-name
command: grep -rliw --include='*.md' --exclude-dir='.*' 'Ravensby' "$VAULT" | wc -l | tr -d ' '
stdout: 0
```

```census-pool
token: Isolde
class: given-name
command: grep -rliw --include='*.md' --exclude-dir='.*' 'Isolde' "$VAULT" | wc -l | tr -d ' '
stdout: 0
```

```census-pool
token: Pellworth
class: surname
command: grep -rliw --include='*.md' --exclude-dir='.*' 'Pellworth' "$VAULT" | wc -l | tr -d ' '
stdout: 0
```

```census-pool
token: Ostrakine
class: company-name
command: grep -rliw --include='*.md' --exclude-dir='.*' 'Ostrakine' "$VAULT" | wc -l | tr -d ' '
stdout: 0
```
