# WI-022 company-name corpus audit — the grounding artifact for the `exploring` AC frame

Conductor-performed, 2026-09-06, committed as WI-022's `kind: precondition` / `grounds:` fence
(`docs/company-stub-parity.md` → `## Write Targets`) before the acceptance criteria are frozen. The
caged builder can reach neither the live vault nor the three consumer repos, so this file is
conductor evidence, never a builder deliverable (the WI-024 precedent, `docs/wi-024-consumer-audit.md`).
Shape contract per the fence's `why:`: per proposed branch, how many live `type: company` names it
would refuse (listing each); the count of already-mangled stems (sizing D4); the `create_stub` call
sites per consumer with the literal scan command, verbatim stdout, and each repo's 40-hex HEAD SHA.

Vault: `/Users/davewascha/Documents/Obsidian/DaveRemoteVault` (walked read-only, `*.md` with a
frontmatter `type: company` line, dot-directories skipped). Notes found: **2160**, of which one is
`Templates/company.md` (empty `name:`, excluded from every count below as a template, not a company).
Live population: **2159**.

## 1. Would any proposed Tier-1 branch refuse a name that is legitimately on disk today?

The regexes are the ones `obsidian_schemas/name_validation.py` compiles today (`_EMAIL_CHARS_RE:108`,
`_ARROW_CONNECTIVE_RE:89`, `_PATH_HOSTILE_RE:95`, `_ARCHIVE_PREFIX_RE:98`), applied with each record's
declared `method`. The widened `path_hostile` row tests the candidate set the exploration names — the
filename- and wikilink-hostile characters the mangler silently absorbs (`docs/company-stub-parity.md`,
Exploration Notes: `: * ? " < > | \ [ ] # ^` plus `/`).

| branch (`branch_id`) | regex | live names refused | which |
|---|---|---|---|
| `email_chars` | `[@]` | 0 | — |
| `arrow_connective` | `->|[→⟶⇒➜↦⇨]` | 0 | — |
| `path_hostile (current, `/` only)` | `/` | 0 | — |
| `path_hostile (widened candidate)` | `[/\:*?"<>|[]#^]` | 0 | — |
| `archive_prefix` | `^z+Archived\b` (I) | 0 | — |
| `empty` | `not name.strip()` | 0 | — |

**Answer: none.** Every proposed branch, including the widened path-hostile set, refuses zero names
that exist today. AC-1/AC-4's "no legitimate name becomes unwritable" premise holds on the whole corpus,
and AC-2's five-member table is safe to freeze as stated.

## 2. What the mangler has been absorbing — a census of every character outside `[\w\s-]`

Characters present in live company names that `company.py:171`'s `re.sub(r'[^\w\s-]', '', name)` would
strip on a write. These names reached the vault by a path that did NOT mangle (a hand-made note, or a
pre-mangler write); they are exactly what AC-1's preservation table must keep byte-identical.

| char | names carrying it | names |
|---|---|---|
| `&` | 8 | 'Constructive & Co', 'Bird & Bird LLP', 'Gordon & Eden', 'Bloom & Wild', 'Bain & Company', 'Savage & Hall', 'Gathered & Found', 'Corrib Consulting  Amplifi & Impact Ltd' |
| `.` | 3 | 'Booking.com', 'Gumtree.com', '5Mins.ai' |

No live name carries any character of the widened path-hostile candidate set (`/ \ : * ? " < > | [ ] # ^`).

## 3. Already-mangled notes on disk (sizing D4)

A mangled write leaves NO filename/name divergence — the mangler rewrites `name:` and the `@{name}.md`
stem from the same cleaned string — so `stem != "@" + name` undercounts it. The mangler's visible
residue is a double space where a stripped character used to sit (`"Allen & Overy"` → `"Allen  Overy"`),
i.e. the Tier-2-dirty shape AC-1's `"Acme  Corp"` fixture stands for.

Double-space / untrimmed names (mangler residue, D4 population): **7** — three in the vault root
(live, resolvable), three already in `_quarantine/companies/`, one in `_merged_dupes/`. Paths are
vault-relative.

- `@Bunch  The Bunch.md` — name `'Bunch  The Bunch'`
- `@Product  Climate.md` — name `'Product  Climate'`
- `@Gathered  Found.md` — name `'Gathered  Found'`
- `_quarantine/companies/@Allen  Overy.md` — name `'Allen  Overy'`
- `_quarantine/companies/@Virgin  Virgin Media  Virgin Mobile.md` — name `'Virgin  Virgin Media  Virgin Mobile'`
- `_quarantine/companies/@MS Marks  Spencer - starting pilot.md` — name `'MS Marks  Spencer - starting pilot'`
- `_merged_dupes/@Corrib Consulting  Amplifi & Impact Ltd.md` — name `'Corrib Consulting  Amplifi & Impact Ltd'`

Filename/name divergence (`stem != "@" + name`): **2**, both in `_quarantine/companies/`
and both a filename-length truncation of a transcript-ingest junk name, not a punctuation mangle:

- `_quarantine/companies/@Coloop AI transcriptionanalysis platform with Silicon Valley funding founded by OxfordCambridge grads.md` — name `'Coloop AI transcriptionanalysis platform with Silicon Valley funding founded'`
- `_quarantine/companies/@Seven Shifts - Restaurant technology company Luke joined post series A raised 100M.md` — name `'Seven Shifts - Restaurant technology company Luke joined post series A raised'`

D4 therefore sizes at **7 notes** to rename-with-alias (WI-029's machinery), plus the two
quarantined junk notes that are a deletion question, not a repair.

## 4. Who writes company notes — call sites and mangler copies across the consumers

HEAD SHAs at scan time:

| repo | HEAD |
|---|---|
| HAL9000 | `25de08b6c1f1db60573124663f1b2baef0b1d680` |
| exocortex | `5b87de21b5530800ba3776fca3aadf203dac050d` |
| orchestrator | `aa3b6e56aad9655a3283ca3b486a8a7ee05140da` |
| obsidian-schemas (this repo, pre-build) | `2bf731f3d3abe0dcaf4d60977f74f379b4b4a1dd` |

### create_stub call sites (all three repos)

Command:

```
grep -rn --include='*.py' '\.create_stub(' /Users/davewascha/Workspaces/HAL9000 /Users/davewascha/Workspaces/exocortex /Users/davewascha/Workspaces/orchestrator | grep -v '/\.venv/\|/archive/\|/tests/\|/test_'
```

Output (verbatim, exit 0):

```
/Users/davewascha/Workspaces/HAL9000/backend_fastapi/routers/entities.py:276:        entity = repo.create_stub(**body)
/Users/davewascha/Workspaces/exocortex/exocortex/ingestion/stages/resolve.py:283:        person = proc.person_repo.create_stub(
/Users/davewascha/Workspaces/exocortex/jobs/attribution_audit.py:1083:        repo.create_stub(name=name, email=email or None,
/Users/davewascha/Workspaces/exocortex/jobs/attribution_audit.py:1115:            repo.create_stub(
/Users/davewascha/Workspaces/exocortex/jobs/attribution_audit.py:1121:        repo.create_stub(name=stranger_name, email=stranger_email,
/Users/davewascha/Workspaces/orchestrator/src/invariants.py:808:            repo.create_stub(name="Alpha Bravo", created_by="invariant-probe")  # canonical, no email/phone/company
/Users/davewascha/Workspaces/orchestrator/src/invariants.py:824:            repo.create_stub(name="Charlie Delta Speechmatics", company="",
```

### mangler regex copies (all three repos + this one)

Command:

```
grep -rn --include='*.py' -F '[^\w\s-]' /Users/davewascha/Workspaces/HAL9000 /Users/davewascha/Workspaces/exocortex /Users/davewascha/Workspaces/orchestrator /Users/davewascha/Workspaces/obsidian-schemas | grep -v '/\.venv/\|/archive/\|/tests/\|/test_'
```

Output (verbatim, exit 0):

```
/Users/davewascha/Workspaces/HAL9000/venv_fastapi/lib/python3.13/site-packages/markdown/extensions/toc.py:44:    value = re.sub(r'[^\w\s-]', '', value).strip().lower()
/Users/davewascha/Workspaces/exocortex/exocortex/ingestion/stages/company.py:157:    clean_name = re.sub(r'[^\w\s-]', '', company_name).strip()
/Users/davewascha/Workspaces/exocortex/exocortex/ingestion/stages/note.py:139:    safe_title = re.sub(r'[^\w\s-]', '', title)[:80].strip()
/Users/davewascha/Workspaces/exocortex/jobs/granola_sync.py:176:    slug = re.sub(r'[^\w\s-]', '', text.lower())
/Users/davewascha/Workspaces/obsidian-schemas/obsidian_schemas/repositories/person.py:1339:        # verbatim. The legacy `clean_name = re.sub(r'[^\w\s-]', '', name)`
/Users/davewascha/Workspaces/obsidian-schemas/obsidian_schemas/repositories/company.py:171:        clean_name = re.sub(r'[^\w\s-]', '', name).strip()
```

### CompanyRepository references outside tests

Command:

```
grep -rn --include='*.py' 'CompanyRepository' /Users/davewascha/Workspaces/HAL9000 /Users/davewascha/Workspaces/exocortex /Users/davewascha/Workspaces/orchestrator | grep -v '/\.venv/\|/archive/\|/tests/\|/test_'
```

Output (verbatim, exit 0):

```
/Users/davewascha/Workspaces/HAL9000/backend_fastapi/core/entity_registry.py:30:literal TYPE NAME and never on `repo.file_pattern` — `CompanyRepository` declares no
/Users/davewascha/Workspaces/HAL9000/backend_fastapi/core/entity_registry.py:46:    CompanyRepository,
/Users/davewascha/Workspaces/HAL9000/backend_fastapi/core/entity_registry.py:61:    "company": CompanyRepository,
/Users/davewascha/Workspaces/exocortex/exocortex/ingestion/transcript.py:16:from obsidian_schemas import Company, PersonRepository, CompanyRepository
/Users/davewascha/Workspaces/exocortex/exocortex/ingestion/transcript.py:110:    _company_repo: Optional[CompanyRepository] = None
/Users/davewascha/Workspaces/exocortex/exocortex/ingestion/transcript.py:218:    def company_repo(self) -> CompanyRepository:
/Users/davewascha/Workspaces/exocortex/exocortex/ingestion/transcript.py:219:        """CompanyRepository for fuzzy matching before stub creation."""
/Users/davewascha/Workspaces/exocortex/exocortex/ingestion/transcript.py:221:            self._company_repo = CompanyRepository(self.obsidian_vault_path)
/Users/davewascha/Workspaces/exocortex/exocortex/ingestion/stages/resolve.py:114:    # Combines explicit Person.company values with CompanyRepository's name set.
/Users/davewascha/Workspaces/exocortex/exocortex/ingestion/stages/resolve.py:123:            f"CompanyRepository unavailable while building the company blacklist "
/Users/davewascha/Workspaces/orchestrator/bin/identity-parity-replay.py:15:`CompanyRepository` (used by the corroborated name-cleaning) loads exactly as in
```

### Reading of the scans (conductor)

- **HAL9000** — `backend_fastapi/routers/entities.py:276` `repo.create_stub(**body)` is the generic
  non-person route; `POST /api/entities/company` reaches `CompanyRepository.create_stub` with the
  request's `name` verbatim. This is the one live consumer of the arm WI-022 rewrites. It passes no
  `created_by`, so AC-3's `"unknown"` + WARNING branch fires on every HAL9000-created company today.
- **exocortex** — does NOT call `CompanyRepository.create_stub`. `ingestion/stages/company.py:132`
  `create_or_update_company` carries its OWN copy of the mangler (`:157`, byte-identical regex) and
  writes the note through `write_markdown_file` (`:209-213`) with `extra_fields={"auto_created": True}`.
  Its `CompanyRepository` use is read-only (`get_all`, `get_file_path`) for fuzzy matching. The
  `jobs/attribution_audit.py` `create_stub` calls (`:1083`, `:1115`, `:1121`) are on a `PersonRepository`
  (`:1113`), out of scope. **Consequence for the premise:** the manifest note's "hourly transcript ingest
  can mint a stray `@Bausch/` directory" is not reachable from exocortex today — its local mangler
  strips `/` before the write. What exocortex DOES leak hourly is the `&`/`.`-stripping (the §3 residue),
  and deleting the mangler HERE does not touch that copy: `exocortex/**` is outside this project's
  write authority (`pipeline-runners.yaml:34-38`). A follow-on in exocortex (route the write through
  the gate-backed `CompanyRepository.create_stub`, delete the local copy) is the durable close of the
  leak; the gate's company arm (this item) is its precondition. The other two exocortex hits
  (`stages/note.py:139` title slug, `jobs/granola_sync.py:176` slug) are filename slugs of non-company
  notes, not name writes.
- **orchestrator** — no company write path. `src/invariants.py:808/824` are `PersonRepository` probes;
  `CompanyRepository` appears only in `bin/identity-parity-replay.py` docstring prose.
- **This repo** — `company.py:171` is the single live code site of the mangler (matches P1 in the
  exploration); `person.py:1339` is a comment.

## 5. What this settles for the AC frame

1. AC-2's membership `{empty, archive_prefix, arrow_connective, email_chars, path_hostile}` refuses no
   live name; the widened `path_hostile` set is also corpus-safe. Freeze as drafted.
2. AC-1's preservation table should carry at least the two real character classes the corpus holds —
   `&` (8 names) and `.` (3 names) — which the drafted fixtures (`"AT&T"`, `"Booking.com"`) already do.
3. The company gate's provenance branch (AC-3) will fire `"unknown"` for HAL9000's route on day one;
   that is the intended signal, not a regression.
4. The exocortex-side mangler copy is a NEW fact the exploration did not carry (its P1 scan was
   tree-local). It does not change WI-022's scope; it names the follow-on that makes the hourly leak
   actually stop.
