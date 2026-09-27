# WI-032 whatsapp corpus census — the grounding artifact for the `exploring` AC frame

Conductor-performed, 2026-09-27 07:35 BST, read-only, committed as WI-032's first `kind: precondition` /
`grounds:` fence (`docs/whatsapp-jid-value-type.md` → `## Write Targets`) BEFORE the acceptance criteria
are frozen — the WI-300 door fired at zero spawns (`ESC-WI-032-exploring-awaiting-precondition-commit-dbf38053`)
and this is the conductor act that answers it. Precedents and shape: `docs/stem-divergence-live-baseline.md`
(privacy wall, `$VAULT` rendering), `docs/identity-cutover-corpus-audit.md` (one self-contained command).
The question it settles is the fence's `grounds:` line: **whether a refusing write door and a scalar-to-list
migration are affordable against the live person corpus as it stands today.**

Privacy wall, as the precedent: counts and classes only — no stem, no stored name, no note bytes, no
identifier value, no absolute path. The vault root is rendered `$VAULT` (the script reads it from
`OBSIDIAN_VAULT_PATH`) and the WhatsApp bridge store `$BRIDGE_DB` (read from `WHATSAPP_BRIDGE_DB`; it is the
`messages.db` HAL9000's `whatsapp_client.py` and orchestrator's `queue_writer.py` both point at, table `chats`).

- **Vault:** `$VAULT`, Dave's live Obsidian vault. Person notes are enumerated exactly as `PersonRepository`
  enumerates them — the top-level `@*.md` glob (`repositories/base.py:231`) — and filtered on frontmatter
  `type: person`; the six-cell rows are computed off the note BYTES (frontmatter block → `yaml.safe_load`),
  never off loaded models, for the reason the fence's `why:` gives (a bare valueless key is YAML null and
  would fall onto the model skip surface). Row (d) is the model-side cross-check.
- **Tree:** obsidian-schemas HEAD `b8f37660b88ce3a237307f69c34e87a254ab6593` (pre-build; `WhatsAppJID.parse`
  and `phones_match` as they stand before WI-032 touches them). **Interpreter:** the project's own
  `.venv/bin/python`, run from the repo root with `PYTHONPATH=.` (the `.venv` editable install is
  deliberately stale — `pipeline-runners.yaml`).
- **The predicates are the doc's, called, never restated:** a value is class Ø when it introduces no
  identifier (absent key, `""`, YAML null); otherwise `WhatsAppJID.parse` decides parse/no-parse (D), and
  STORABLE is "the text after the LAST `@` of the parsed, normalized `.jid` is in `{"s.whatsapp.net", "lid"}`"
  — A/B storable by phone-bearing/lid, C/E not storable by phone-bearing/lid — the six-cell table in
  `## Exploration Notes`.

## 0. The measurement — one script, run once, stdout verbatim

```
OBSIDIAN_VAULT_PATH=$VAULT WHATSAPP_BRIDGE_DB=$BRIDGE_DB PYTHONPATH=. .venv/bin/python wi032_census.py   # from the obsidian-schemas repo root
```

```python
import os, re, sys, sqlite3, pathlib, collections
sys.path.insert(0, ".")
import yaml
from obsidian_schemas.identifier import WhatsAppJID, IdentifierError
from obsidian_schemas.phone_normalization import normalize_phone, phones_match
from obsidian_schemas.repositories.person import PersonRepository

V = pathlib.Path(os.environ["OBSIDIAN_VAULT_PATH"])
B = pathlib.Path(os.environ["WHATSAPP_BRIDGE_DB"])
STORABLE = {"s.whatsapp.net", "lid"}
FM = re.compile(r"^---\n(.*?)\n?---", re.S)

def classify(v):
    """Six-cell class of ONE non-list frontmatter value, off the BYTES (never a loaded model)."""
    if v is None or (isinstance(v, str) and v.strip() == ""):
        return "Ø"
    s = str(v)
    try:
        j = WhatsAppJID.parse(s)
    except IdentifierError:
        return "D"
    dom = j.jid.rsplit("@", 1)[1] if "@" in j.jid else ""
    storable = dom in STORABLE
    if storable:
        return "A" if j.phone_digits else "B"
    return "E" if j.phone_digits == "" else "C"

# (a) the person notes, enumerated the way PersonRepository enumerates them (top-level `@*.md`)
files = sorted(V.glob("@*.md"))
cells = collections.Counter(); sub = collections.Counter(); shapes = collections.Counter()
person_notes = 0; unparsed = 0; non_person = 0; list_elems = collections.Counter()
for p in files:
    try:
        txt = p.read_text(encoding="utf-8")
    except Exception:
        unparsed += 1; continue
    m = FM.match(txt)
    if not m:
        unparsed += 1; continue
    try:
        fm = yaml.safe_load(m.group(1)) or {}
    except Exception:
        unparsed += 1; continue
    if not isinstance(fm, dict) or fm.get("type") != "person":
        non_person += 1; continue
    person_notes += 1
    if "whatsapp" not in fm:
        cells["Ø"] += 1; sub["Ø:absent-key"] += 1; continue
    v = fm["whatsapp"]
    if isinstance(v, list):
        shapes["list"] += 1
        for e in v: list_elems[classify(e)] += 1
        cells["Ø" if not v else "(list)"] += 1; continue
    shapes["scalar"] += 1
    c = classify(v)
    cells[c] += 1
    if c == "Ø":
        sub["Ø:null" if v is None else "Ø:empty-string"] += 1
    if c == "C":
        sub["C:bare-number(no @)" if "@" not in str(v) else "C:other-domain"] += 1
    if c in ("A", "C"):
        d = WhatsAppJID.parse(str(v)).phone_digits
        own = [normalize_phone(str(x)) for x in (fm.get("phones") or []) if x]
        sub[f"{c}:digits-already-in-own-phones[]"] += int(any(phones_match(d, o) for o in own if o))

print(f"(a) top-level @*.md files: {len(files)}; type: person: {person_notes}; not person: {non_person}; frontmatter unreadable: {unparsed}")
print(f"(b) whatsapp value shape: scalar {shapes['scalar']}, list {shapes['list']} (list elements by class: {dict(list_elems) or '{}'})")
for k in ("Ø", "A", "B", "C", "D", "E", "(list)"):
    print(f"(c) class {k}: {cells[k]}")
print(f"(c') splits: {dict(sorted(sub.items()))}")
print(f"(c'') residual |R| recommended arm (D+E): {cells['D']+cells['E']}; alternative arm (C+D+E): {cells['C']+cells['D']+cells['E']}")

# (d) model-side cross-check: what the repository loads vs the byte count
repo = PersonRepository(V)
people = repo.get_all()
skipped = list(repo.skipped_notes)
print(f"(d) PersonRepository loads {len(people)} people; skip surface {len(skipped)}; loaded+skipped = {len(people)+len(skipped)} vs byte-count {person_notes}")

# (e) stored phone digits in the vault (phones[] + phone-bearing whatsapp), for the lid-collision count
vault_digits = set()
for pp in people:
    for ph in (pp.phones or []):
        d = normalize_phone(str(ph)) if ph else ""
        if d: vault_digits.add(d)
    w = getattr(pp, "whatsapp", None)
    for e in (w if isinstance(w, list) else [w]):
        if e:
            try: j = WhatsAppJID.parse(str(e))
            except IdentifierError: continue
            if j.phone_digits: vault_digits.add(j.phone_digits)
print(f"(e) distinct stored phone digit-strings in the vault (phones[] + phone-bearing whatsapp): {len(vault_digits)}")

# (f) the bridge store
con = sqlite3.connect(f"file:{B}?mode=ro", uri=True)
rows = con.execute("select jid, name from chats").fetchall()
kind = collections.Counter(); by_name = collections.defaultdict(set); lids = []
for jid, name in rows:
    jid = jid or ""
    dom = jid.rsplit("@", 1)[1] if "@" in jid else ""
    k = {"s.whatsapp.net": "phone-jid", "lid": "lid", "g.us": "group"}.get(dom, "other")
    kind[k] += 1
    if k in ("phone-jid", "lid") and name:
        by_name[name].add(k)
    if k == "lid":
        lids.append(jid.rsplit("@", 1)[0])
both = sum(1 for s in by_name.values() if {"phone-jid", "lid"} <= s)
print(f"(f) bridge chats: {len(rows)} = {dict(kind)}; distinct 1:1 names: {len(by_name)}; names holding BOTH a phone-JID and a lid: {both}")

# (g) lids whose digits phones_match a stored vault phone — the WI-035 pivot's false-positive population
def collides(digits):
    return any(phones_match(digits, vd) for vd in vault_digits)
bridge_coll = sum(1 for d in lids if d and collides(d))
vault_lids = []
for pp in people:
    w = getattr(pp, "whatsapp", None)
    for e in (w if isinstance(w, list) else [w]):
        if e and "@lid" in str(e):
            vault_lids.append(str(e).rsplit("@", 1)[0])
vault_coll = sum(1 for d in vault_lids if d and collides(d))
print(f"(g) bridge lids: {len(lids)}, of which digits phones_match a stored vault phone: {bridge_coll}; vault-stored lids: {len(vault_lids)}, of which collide: {vault_coll}")
```

stdout, verbatim:

```
(a) top-level @*.md files: 1838; type: person: 1174; not person: 664; frontmatter unreadable: 0
(b) whatsapp value shape: scalar 1168, list 0 (list elements by class: {})
(c) class Ø: 1031
(c) class A: 35
(c) class B: 26
(c) class C: 82
(c) class D: 0
(c) class E: 0
(c) class (list): 0
(c') splits: {'A:digits-already-in-own-phones[]': 35, 'C:bare-number(no @)': 82, 'C:digits-already-in-own-phones[]': 81, 'Ø:absent-key': 6, 'Ø:empty-string': 1025}
(c'') residual |R| recommended arm (D+E): 0; alternative arm (C+D+E): 82
(d) PersonRepository loads 1174 people; skip surface 0; loaded+skipped = 1174 vs byte-count 1174
(e) distinct stored phone digit-strings in the vault (phones[] + phone-bearing whatsapp): 141
(f) bridge chats: 729 = {'group': 182, 'phone-jid': 369, 'lid': 172, 'other': 6}; distinct 1:1 names: 475; names holding BOTH a phone-JID and a lid: 51
(g) bridge lids: 172, of which digits phones_match a stored vault phone: 0; vault-stored lids: 26, of which collide: 0
```

## 1. The six-cell table (the rows the fence asks for)

| cell | predicate | count | of `type: person` (1174) |
|---|---|---|---|
| **Ø** | no identifier: absent key 6, `""` 1025, YAML null 0 | **1031** | 87.8% — the denominator; migrates SHAPE-ONLY, always accepted |
| **A** | parses, phone-bearing, storable (`@s.whatsapp.net`) | **35** | 3.0% |
| **B** | parses, lid, storable (`@lid`) | **26** | 2.2% — the vault ALREADY stores lids |
| **C** | parses, phone-bearing, NOT storable — the Kim Faura class | **82** | 7.0% — **the load-bearing row**; all 82 are bare numbers (no `@` at all), none an odd-domain spelling |
| **D** | non-empty, does not parse | **0** | — |
| **E** | `@lid` substring, non-storable domain | **0** | — (expected zero; now on paper) |
| list-shaped | value already a YAML list | 0 | no note has been migrated by hand |

Every note is accounted for: 1031 + 35 + 26 + 82 + 0 + 0 = 1174, and the model-side count agrees
(row (d): the repository loads 1174, skip surface 0), so no person note is hidden from either view.

## 2. What the numbers decide

- **The residual `|R|` is ZERO under the recommended arm** (D + E = 0). Ruling B leg 2 — "reported and left
  for hand repair" — prices at nothing today: after the migration's class-C repair, no live note holds a
  value `PersonRepository.save` would refuse. The `lint_vault` detector (AC-3's REPORT LEG) ships against an
  empty population, which is the right way round: it is the wall against the NEXT bare number, not a
  backlog. Under the alternative arm (decline the repair) `|R|` would be 82 — Dave ruled **repair**
  (2026-09-27), so the alternative arm is closed and the bracket's exit figure is `|R| = 0`.
- **The repair pass is 82 notes and it is a re-spelling, not a data change.** All 82 class-C values are
  bare telephone numbers; 81 of the 82 already carry the same digits in their own `phones:` (row (c')), so
  `"<number>"` → `"<digits>@s.whatsapp.net"` keeps the same `phone:<digits>` key on every one and the
  readback oracle (`.key` multiset per note) has a non-trivial population to prove "no identifier moved"
  against. The one note whose whatsapp digits are not in its `phones:` is still key-preserving (the JID
  keys on its own digits); it is the one row worth eyeballing in the dry run.
- **The door's refusal is affordable.** After the repair, the refusing population on the live vault is
  0; the door then refuses only what a writer tries to add from now on (the 82 show that bare numbers DO
  arrive — one every ~14 person notes — so the wall is not theoretical).
- **The shape flip's live population is small and clean:** 35 A + 26 B + 82 C = 143 notes carry a
  value at all; 1031 convert shape-only. No note is list-shaped yet, so the migration meets a uniform
  scalar corpus.
- **Cardinality is a real need, re-measured:** the bridge store holds **51** display names carrying BOTH
  a phone-JID and a lid (the premise paragraph's 51, reproduced exactly) against 475 distinct 1:1 names;
  the vault today can hold one of the two, and 26 notes already chose the lid.
- **The WI-035 lid→phone pivot's false-positive population is ZERO today:** none of the 172 bridge lids,
  and none of the 26 vault-stored lids, has digits that `phones_match` any of the 141 stored phone
  digit-strings. The resolution fix (never answer a lid back as a phone) therefore changes no live lookup
  result on the day it lands; it closes a class, not an incident.

## 3. What this census does NOT claim

- It counts values, not people: a person with two notes counts twice (the WI-029 exit measured 0 stem
  divergences and 0 conflicts, so this is expected to be nil, but it is not re-measured here).
- Row (g)'s collision test is over the vault's 141 stored digit-strings only; a lid whose digits match a
  phone the vault does NOT store cannot be a false positive for the pivot, so the population is complete
  for the question asked.
- The bridge store is a moving target (729 chats at measurement; HAL9000's 2026-09-26 audit read 725).
  The 51 is reproduced exactly; the totals drift by the day and are not a criterion.

Commands to re-run verbatim: the §0 script, from the repo root, with the two environment variables set.
The bracket for the live run (`docs/wi-032-whatsapp-live-baseline.md`, a deliverable of `## Approach`
step (4)) compares its exit against §1's D + E rows (`|R| = 0`) and its class-C repair count against §1's
C row (82).
