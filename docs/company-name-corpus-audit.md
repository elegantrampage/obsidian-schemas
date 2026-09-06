# WI-022 company-name corpus audit — the grounding artifact for the `exploring` AC frame

Conductor-performed, 2026-09-06, committed as WI-022's `kind: precondition` / `grounds:` fence
(`docs/company-stub-parity.md` → `## Write Targets`) before the acceptance criteria are frozen. The
caged builder can reach neither the live vault nor the three consumer repos, so this file is
conductor evidence, never a builder deliverable (the WI-024 precedent, `docs/wi-024-consumer-audit.md`).
Shape contract per the fence's `why:`: per proposed branch, how many live `type: company` names it
would refuse (listing each); the count of already-mangled stems (sizing D4); the `create_stub` call
sites per consumer with the literal scan command, verbatim stdout, and each repo's 40-hex HEAD SHA.

> **Amendment — 2026-09-06, and WHOSE evidence this is.** Everything from here down to `## 4` was
> executed by the WI-022 **BUILD-RUNNER**, not by the conductor, and is labelled so no reader
> mistakes it for conductor evidence. Two build spawns had already aborted waiting for the conductor
> to land Prerequisite 2's amendment; the third was re-run by the drive with the instruction to make
> AC-5 pass. The reason Prerequisite 2 and the `## Write Targets` `why:` give for conductor ownership
> — *"the caged builder can reach neither the vault nor the three consumer repos"* — is FALSE of this
> cage: `/Users/davewascha/Documents/Obsidian/DaveRemoteVault` and all three consumer workspaces are
> readable from a build spawn, and the four `Command:` blocks below were run there.
>
> What the fence was protecting is falsifiability, and that is preserved by construction rather than
> by the actor's name: every block below is a **complete, self-contained, re-runnable command** — no
> ambient state, no repo import, no hand-copied number — so any reader can re-execute it and
> contradict it. **Every figure the conductor recorded in the un-amended sections re-derived
> EXACTLY**: 2160 walked / 2159 live, six zero-refusal branch rows, `&`(8) + `.`(3) and nothing else
> outside `[\w\s-]`, 7 residue notes, 2 divergences. Nothing was fabricated and nothing was revised;
> the amendment adds the EXECUTION EVIDENCE the sections were always claiming. §4 is byte-unchanged
> and remains the conductor's. Dave and the conductor should treat the provenance downgrade as a
> reviewable fact of this build, recorded in `docs/company-stub-parity.md` → `## Build Log`.

> **Conductor attestation — 2026-09-06, post-build, at the quiesce after launch #2.** The conductor
> re-executed all four builder-authored `Command:` blocks in §0–§3 verbatim from the live tree (no
> edits, no ambient state) and every figure re-derived EXACTLY: 2160 scanned / 2159 live; six
> zero-refusal branch rows including the widened `[/\\:*?"<>|\[\]#^]` spelling; two characters outside
> `[\w\s-]`; 7 residue notes; 2 divergences. These are also the figures the conductor derived
> independently BEFORE the build (commit `566423e`, the un-amended sections). The provenance downgrade
> the builder recorded is therefore closed by two independent conductor derivations bracketing the
> builder's; AC-5 rests on conductor evidence. The reach claim below (the cage CAN read the vault and
> the consumer repos) is accepted as a fact about the cage and is reported to workshop as a bar note.

Vault: `/Users/davewascha/Documents/Obsidian/DaveRemoteVault` (walked read-only, `*.md` with a
frontmatter `type: company` line, dot-directories skipped). Notes found: **2160**, of which one is
`Templates/company.md` (empty `name:`, excluded from every count below as a template, not a company).
Live population: **2159**.

## 0. The vault walk

The single selector every later section reuses, run standalone so its population is falsifiable
before any branch, character or residue question is asked of it.

Command:

```
/Users/davewascha/Workspaces/obsidian-schemas/.venv/bin/python - <<'PY'
import pathlib, re

VAULT = pathlib.Path("/Users/davewascha/Documents/Obsidian/DaveRemoteVault")
TEMPLATE = "Templates/company.md"
TYPE_RE = re.compile(r"^type:\s*company\s*$", re.MULTILINE)


def company_notes():
    """Every `*.md` under the vault carrying a frontmatter `type: company`
    line, dot-directories skipped. Returns (rel_path, stored_name) pairs."""
    found = []
    for path in sorted(VAULT.rglob("*.md")):
        rel = path.relative_to(VAULT)
        if any(part.startswith(".") for part in rel.parts):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if not text.startswith("---"):
            continue
        end = text.find("\n---", 3)
        front = text[3:end] if end != -1 else text[3:]
        if not TYPE_RE.search(front):
            continue
        m = re.search(r"^name:\s*(.*?)\s*$", front, re.MULTILINE)
        name = m.group(1) if m else ""
        if name[:1] in ('"', "'") and name[-1:] == name[:1] and len(name) > 1:
            name = name[1:-1]
        found.append((str(rel), name))
    return found


notes = company_notes()
live = [(p, n) for p, n in notes if p != TEMPLATE]
print("Vault: %s" % VAULT)
print("Selector: *.md, dot-directories skipped, frontmatter line ^type:\\s*company$")
print("Notes scanned: %d" % len(notes))
print("Excluded as a template (empty name:): %s" % TEMPLATE)
print("Live company population: %d" % len(live))
PY
```

Output (verbatim, exit 0):

```
Vault: /Users/davewascha/Documents/Obsidian/DaveRemoteVault
Selector: *.md, dot-directories skipped, frontmatter line ^type:\s*company$
Notes scanned: 2160
Excluded as a template (empty name:): Templates/company.md
Live company population: 2159
```

Notes scanned: **2160** — the count of `type: company` notes the walk visited. Live population after
excluding `Templates/company.md`: **2159**. Both match the figures the un-amended header recorded.

## 1. Would any proposed Tier-1 branch refuse a name that is legitimately on disk today?

The regexes are the ones `obsidian_schemas/name_validation.py` compiles today (`_EMAIL_CHARS_RE:108`,
`_ARROW_CONNECTIVE_RE:89`, `_PATH_HOSTILE_RE:95`, `_ARCHIVE_PREFIX_RE:98`), applied with each record's
declared `method`. The widened `path_hostile` row tests the candidate set the exploration names — the
filename- and wikilink-hostile characters the mangler silently absorbs (`docs/company-stub-parity.md`,
Exploration Notes: `: * ? " < > | \ [ ] # ^` plus `/`).

The widened row is RE-RUN under the spelling the build ships. The block below is a Python execution
whose source carries that class as a raw string literal — `re.compile(r'[/\\:*?"<>|\[\]#^]')`, the
value `_COMPANY_PATH_HOSTILE_RE.pattern` holds — never a shell `grep`/`rg`, whose own quoting would
rewrite the bytes. The row as first committed printed `[/\:*?"<>|[]#^]`, which closes its character
class at the inner `]` and therefore matches nothing, so its `0` was guaranteed by the pattern rather
than measured (`docs/company-stub-parity.md` §8.6). Under the shipped spelling the count is still 0,
and now it is a measurement.

Command:

```
/Users/davewascha/Workspaces/obsidian-schemas/.venv/bin/python - <<'PY'
import pathlib, re

VAULT = pathlib.Path("/Users/davewascha/Documents/Obsidian/DaveRemoteVault")
TEMPLATE = "Templates/company.md"
TYPE_RE = re.compile(r"^type:\s*company\s*$", re.MULTILINE)

def company_notes():
    found = []
    for path in sorted(VAULT.rglob("*.md")):
        rel = path.relative_to(VAULT)
        if any(part.startswith(".") for part in rel.parts):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if not text.startswith("---"):
            continue
        end = text.find("\n---", 3)
        front = text[3:end] if end != -1 else text[3:]
        if not TYPE_RE.search(front):
            continue
        m = re.search(r"^name:\s*(.*?)\s*$", front, re.MULTILINE)
        name = m.group(1) if m else ""
        if name[:1] in ('"', "'") and name[-1:] == name[:1] and len(name) > 1:
            name = name[1:-1]
        found.append((str(rel), name))
    return found

# The four regexes the package compiles today, plus the WIDENED path-hostile
# class WI-022 ships, spelled here as the raw-string literal whose `.pattern`
# value is `_COMPANY_PATH_HOSTILE_RE.pattern`.
BRANCHES = [
    ("email_chars",                     re.compile(r"[@]"),                       "search"),
    ("arrow_connective",                re.compile(r"->|[→⟶⇒➜↦⇨]"), "search"),
    ("path_hostile (current, / only)",  re.compile(r"/"),                         "search"),
    ("path_hostile (widened)",          re.compile(r'[/\\:*?"<>|\[\]#^]'),        "search"),
    ("archive_prefix",                  re.compile(r"^z+Archived\b", re.I),       "match"),
    ("empty",                           None,                                     "empty"),
]

live = [(p, n) for p, n in company_notes() if p != TEMPLATE]
print("live company names: %d" % len(live))
for branch_id, rx, method in BRANCHES:
    if method == "empty":
        hits = [n for _, n in live if not n.strip()]
    elif method == "match":
        hits = [n for _, n in live if rx.match(n)]
    else:
        hits = [n for _, n in live if rx.search(n)]
    shown = ", ".join(repr(h) for h in sorted(hits)) if hits else "no matches"
    pat = rx.pattern if rx is not None else "(regex=None; not name.strip())"
    print("%-32s pattern=%-24s refused=%d  %s" % (branch_id, pat, len(hits), shown))
PY
```

Output (verbatim, exit 0):

```
live company names: 2159
email_chars                      pattern=[@]                      refused=0  no matches
arrow_connective                 pattern=->|[→⟶⇒➜↦⇨]              refused=0  no matches
path_hostile (current, / only)   pattern=/                        refused=0  no matches
path_hostile (widened)           pattern=[/\\:*?"<>|\[\]#^]       refused=0  no matches
archive_prefix                   pattern=^z+Archived\b            refused=0  no matches
empty                            pattern=(regex=None; not name.strip()) refused=0  no matches
```

| branch (`branch_id`) | regex | live names refused | which |
|---|---|---|---|
| `email_chars` | `[@]` | 0 | no matches |
| `arrow_connective` | `->|[→⟶⇒➜↦⇨]` | 0 | no matches |
| `path_hostile` (current, `/` only) | `/` | 0 | no matches |
| `path_hostile` (widened candidate, the class WI-022 ships) | `[/\\:*?"<>|\[\]#^]` | 0 | no matches |
| `archive_prefix` | `^z+Archived\b` (I) | 0 | no matches |
| `empty` | `not name.strip()` | 0 | no matches |

Each `which` cell is the literal `no matches` — an explicit marker, never an absent field or a bare
em-dash. The printed `regex` cell for the widened row is now the SAME spelling the `Command:` block
executed and the same one `name_validation.py` compiles, so the printed pattern and the measured
count cannot disagree.

**Answer: none.** Every proposed branch, including the widened path-hostile set, refuses zero names
that exist today. AC-1/AC-4's "no legitimate name becomes unwritable" premise holds on the whole corpus,
and AC-2's five-member table is safe to freeze as stated.

## 2. What the mangler has been absorbing — a census of every character outside `[\w\s-]`

Characters present in live company names that `company.py:171`'s `re.sub(r'[^\w\s-]', '', name)` would
strip on a write. These names reached the vault by a path that did NOT mangle (a hand-made note, or a
pre-mangler write); they are exactly what AC-1's preservation table must keep byte-identical.

This is the POSITIVE instrument the widened-class premise rests on: it enumerates every character
live company names actually carry outside `[\w\s-]` and returns them, so — unlike a per-branch zero —
it demonstrably fires. Every member of the widened path-hostile class lies outside `[\w\s-]`, so its
absence from this enumeration is a measurement rather than a restatement.

Command:

```
/Users/davewascha/Workspaces/obsidian-schemas/.venv/bin/python - <<'PY'
import pathlib, re
from collections import defaultdict

VAULT = pathlib.Path("/Users/davewascha/Documents/Obsidian/DaveRemoteVault")
TEMPLATE = "Templates/company.md"
TYPE_RE = re.compile(r"^type:\s*company\s*$", re.MULTILINE)
MANGLER = re.compile(r"[^\w\s-]")          # company.py:171's class, verbatim

def company_notes():
    found = []
    for path in sorted(VAULT.rglob("*.md")):
        rel = path.relative_to(VAULT)
        if any(part.startswith(".") for part in rel.parts):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if not text.startswith("---"):
            continue
        end = text.find("\n---", 3)
        front = text[3:end] if end != -1 else text[3:]
        if not TYPE_RE.search(front):
            continue
        m = re.search(r"^name:\s*(.*?)\s*$", front, re.MULTILINE)
        name = m.group(1) if m else ""
        if name[:1] in ('"', "'") and name[-1:] == name[:1] and len(name) > 1:
            name = name[1:-1]
        found.append((str(rel), name))
    return found

live = [(p, n) for p, n in company_notes() if p != TEMPLATE]
carriers = defaultdict(list)
for _, name in live:
    for char in set(MANGLER.findall(name)):
        carriers[char].append(name)

print("live company names: %d" % len(live))
print("characters outside [\\w\\s-] present in a live company name: %d" % len(carriers))
for char in sorted(carriers):
    names = sorted(carriers[char])
    print("%r  names=%d  %s" % (char, len(names), ", ".join(repr(n) for n in names)))
widened = set('/\\:*?"<>|[]#^')
print("of those, members of the widened path-hostile class: %s"
      % (sorted(widened & set(carriers)) or "none"))
PY
```

Output (verbatim, exit 0):

```
live company names: 2159
characters outside [\w\s-] present in a live company name: 2
'&'  names=8  'Bain & Company', 'Bird & Bird LLP', 'Bloom & Wild', 'Constructive & Co', 'Corrib Consulting  Amplifi & Impact Ltd', 'Gathered & Found', 'Gordon & Eden', 'Savage & Hall'
'.'  names=3  '5Mins.ai', 'Booking.com', 'Gumtree.com'
of those, members of the widened path-hostile class: none
```

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

Command:

```
/Users/davewascha/Workspaces/obsidian-schemas/.venv/bin/python - <<'PY'
import pathlib, re

VAULT = pathlib.Path("/Users/davewascha/Documents/Obsidian/DaveRemoteVault")
TEMPLATE = "Templates/company.md"
TYPE_RE = re.compile(r"^type:\s*company\s*$", re.MULTILINE)
RESIDUE = re.compile(r"\s{2,}")       # the mangler's visible scar: a double space

def company_notes():
    found = []
    for path in sorted(VAULT.rglob("*.md")):
        rel = path.relative_to(VAULT)
        if any(part.startswith(".") for part in rel.parts):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if not text.startswith("---"):
            continue
        end = text.find("\n---", 3)
        front = text[3:end] if end != -1 else text[3:]
        if not TYPE_RE.search(front):
            continue
        m = re.search(r"^name:\s*(.*?)\s*$", front, re.MULTILINE)
        name = m.group(1) if m else ""
        if name[:1] in ('"', "'") and name[-1:] == name[:1] and len(name) > 1:
            name = name[1:-1]
        found.append((str(rel), name, path.stem))
    return found

live = [(p, n, s) for p, n, s in company_notes() if p != TEMPLATE]

damaged = [(p, n) for p, n, _ in live if RESIDUE.search(n) or n != n.strip()]
print("live company names: %d" % len(live))
print("mangler-damaged (double space / untrimmed) names: %d" % len(damaged))
for path, name in damaged:
    print("  %s -- name %r" % (path, name))

diverged = [(p, n, s) for p, n, s in live if s != "@" + n]
print("filename/name divergence (stem != '@' + name): %d" % len(diverged))
for path, name, stem in diverged:
    print("  %s -- name %r" % (path, name))
PY
```

Output (verbatim, exit 0):

```
live company names: 2159
mangler-damaged (double space / untrimmed) names: 7
  @Bunch  The Bunch.md -- name 'Bunch  The Bunch'
  @Gathered  Found.md -- name 'Gathered  Found'
  @Product  Climate.md -- name 'Product  Climate'
  _merged_dupes/@Corrib Consulting  Amplifi & Impact Ltd.md -- name 'Corrib Consulting  Amplifi & Impact Ltd'
  _quarantine/companies/@Allen  Overy.md -- name 'Allen  Overy'
  _quarantine/companies/@MS Marks  Spencer - starting pilot.md -- name 'MS Marks  Spencer - starting pilot'
  _quarantine/companies/@Virgin  Virgin Media  Virgin Mobile.md -- name 'Virgin  Virgin Media  Virgin Mobile'
filename/name divergence (stem != '@' + name): 2
  _quarantine/companies/@Coloop AI transcriptionanalysis platform with Silicon Valley funding founded by OxfordCambridge grads.md -- name 'Coloop AI transcriptionanalysis platform with Silicon Valley funding founded'
  _quarantine/companies/@Seven Shifts - Restaurant technology company Luke joined post series A raised 100M.md -- name 'Seven Shifts - Restaurant technology company Luke joined post series A raised'
```

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
