# WI-023 identity-cutover corpus audit — the grounding artifact for the `exploring` AC frame

Conductor-performed, 2026-09-06, committed as WI-023's `kind: precondition` / `grounds:` fence
(`docs/identity-engine-endgame.md` → `## Write Targets`) BEFORE the acceptance criteria are frozen — the
WI-300 door fired at zero spawns (`ESC-WI-023-exploring-awaiting-precondition-commit-da221d36`) and this
is the conductor act that answers it. Precedents: `docs/wi-024-consumer-audit.md`,
`docs/company-name-corpus-audit.md`. The question it settles is the fence's `grounds:` line: **whether the
unified index resolves every email the legacy per-kind dicts resolve on the live vault today.**

The whole audit is ONE self-contained command, run under the project interpreter (the repo root is put
on `sys.path` explicitly because this `.venv`'s editable install is stale-relocated — `CLAUDE.md`,
load-bearing). It loads the vault through `PersonRepository` — the same loader that feeds `_email_index`
— so what it scans is exactly what the legacy dict indexes. Re-run it to contradict any number below.

## The command (literal)

```
/Users/davewascha/Workspaces/obsidian-schemas/.venv/bin/python - <<'PY'
import sys, itertools, collections, subprocess
sys.path.insert(0, "/Users/davewascha/Workspaces/obsidian-schemas")
from obsidian_schemas.repositories.person import PersonRepository
from obsidian_schemas.identifier import Email, Phone, IdentifierError
from obsidian_schemas.phone_normalization import phones_match

VAULT = "/Users/davewascha/Documents/Obsidian/DaveRemoteVault"
repo = PersonRepository(VAULT)
people = repo.get_all()
skipped = list(repo.skipped_notes)
print(f"(a) type: person notes loaded: {len(people)}; notes the repository owns but could not load (skip surface): {len(skipped)}; scanned = {len(people)+len(skipped)}")
for s in skipped:
    print(f"    skipped: {getattr(s,'path',getattr(s,'file_path',s))} — {getattr(s,'reason','?')}")

# (b) emails Email.parse refuses — the class _email_index indexes and _identifier_index drops
refused = []
entries = 0
for p in people:
    for raw in (p.emails or []):
        if not raw:
            continue
        entries += 1
        try:
            Email.parse(raw)
        except IdentifierError as e:
            refused.append((p.name, raw, str(e)))
print(f"(b) non-empty `emails:` entries scanned: {entries}; entries Email.parse REFUSES: {len(refused)}")
if refused:
    for name, raw, why in refused:
        print(f"    REFUSED {raw!r} on note {name!r}: {why}")
else:
    print("    no matches")

# (c) raw.lower() != Email.parse(raw).value — whitespace class vs angle-bracket class
ws, ab, other = [], [], []
for p in people:
    for raw in (p.emails or []):
        if not raw:
            continue
        try:
            v = Email.parse(raw).value
        except IdentifierError:
            continue
        if raw.lower() != v:
            if "<" in raw or ">" in raw:
                ab.append((p.name, raw, v))
            elif raw != raw.strip():
                ws.append((p.name, raw, v))
            else:
                other.append((p.name, raw, v))
print(f"(c) entries where raw.lower() != Email.parse(raw).value: {len(ws)+len(ab)+len(other)} — whitespace class: {len(ws)}; angle-bracket class: {len(ab)}; other: {len(other)}")
for label, rows in (("whitespace", ws), ("angle-bracket", ab), ("other", other)):
    if rows:
        for name, raw, v in rows:
            print(f"    {label}: {raw!r} -> {v!r} on note {name!r}")
    else:
        print(f"    {label}: no matches")

# (d) cross-note phones:/whatsapp: pairs phones_match unifies but Phone.key does not
vals = []  # (note, raw, key or None)
for p in people:
    for raw in list(p.phones or []) + ([p.whatsapp] if p.whatsapp else []):
        if not raw:
            continue
        try:
            k = Phone.parse(raw).key
        except IdentifierError:
            k = None
        vals.append((p.name, raw, k))
pairs = 0
examples = []
by_note = collections.defaultdict(set)
for (n1, r1, k1), (n2, r2, k2) in itertools.combinations(vals, 2):
    if n1 == n2:
        continue
    if phones_match(r1, r2) and not (k1 is not None and k1 == k2):
        pairs += 1
        by_note[frozenset((n1, n2))].add((r1, r2))
        if len(examples) < 20:
            examples.append((n1, r1, k1, n2, r2, k2))
print(f"(d) phone/whatsapp values scanned: {len(vals)} (Phone.parse refused: {sum(1 for _,_,k in vals if k is None)}); cross-note PAIRS phones_match unifies but Phone.key does not: {pairs}; distinct note-pairs involved: {len(by_note)}")
if examples:
    for n1, r1, k1, n2, r2, k2 in examples:
        print(f"    {r1!r} [{k1}] on {n1!r}  ~  {r2!r} [{k2}] on {n2!r}")
    if pairs > len(examples):
        print(f"    ... {pairs-len(examples)} more pairs not listed")
else:
    print("    no matches")

# (e) consumer HEAD SHAs + direct reaches into the legacy dicts
print("(e) HEAD SHAs and direct consumer reaches into the legacy per-kind dicts:")
for r in ("HAL9000", "exocortex", "orchestrator", "obsidian-schemas"):
    sha = subprocess.run(["git", "-C", f"/Users/davewascha/Workspaces/{r}", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    print(f"    {r}: {sha}")
for r in ("HAL9000", "exocortex", "orchestrator"):
    g = subprocess.run(["grep", "-rn", "--include=*.py", "-E", r"_email_index|_phone_index|_alias_index|_slack_index", f"/Users/davewascha/Workspaces/{r}"], capture_output=True, text=True).stdout
    hits = [l for l in g.splitlines() if "/.venv/" not in l and "/archive/" not in l]
    print(f"    {r}: direct references to _email_index/_phone_index/_alias_index/_slack_index outside .venv/archive: {len(hits)}")
    for l in hits[:10]:
        print(f"        {l[:200]}")
PY
```

## Output (verbatim stdout, 2026-09-06, exit 0)

```
(a) type: person notes loaded: 1147; notes the repository owns but could not load (skip surface): 0; scanned = 1147
(b) non-empty `emails:` entries scanned: 1021; entries Email.parse REFUSES: 0
    no matches
(c) entries where raw.lower() != Email.parse(raw).value: 0 — whitespace class: 0; angle-bracket class: 0; other: 0
    whitespace: no matches
    angle-bracket: no matches
    other: no matches
(d) phone/whatsapp values scanned: 276 (Phone.parse refused: 0); cross-note PAIRS phones_match unifies but Phone.key does not: 0; distinct note-pairs involved: 0
    no matches
(e) HEAD SHAs and direct consumer reaches into the legacy per-kind dicts:
    HAL9000: 68fbd334bf8deb18fc5eb58ffa968273e90313bf
    exocortex: 2c6f0896a1e8b184b641e0b7fb91386ee11e2a76
    orchestrator: d44418d9c16a88e57ad0f0a88ea8a930b5a64ea0
    obsidian-schemas: 990aa6de47833cddeff765684c87812e907f63b4
    HAL9000: direct references to _email_index/_phone_index/_alias_index/_slack_index outside .venv/archive: 2
        /Users/davewascha/Workspaces/HAL9000/backend_fastapi/tests/test_one_ladder_contacts_door.py:56:PRIVATE_REACHES = frozenset({"_cache", "_alias_index", "_email_index", "_ensure_loaded"})
        /Users/davewascha/Workspaces/HAL9000/backend_fastapi/tests/test_wi061_registry_freshness.py:699:    (base.py:239-240) and survives an in-place clear, whereas `_alias_index` and its five
    exocortex: direct references to _email_index/_phone_index/_alias_index/_slack_index outside .venv/archive: 0
    orchestrator: direct references to _email_index/_phone_index/_alias_index/_slack_index outside .venv/archive: 0
```

## Reading, per shape-contract clause

**(a) Notes scanned: 1147** `type: person` notes loaded; the repository's skip surface is EMPTY (0
notes it owns but could not load), so scanned = loaded = 1147. The 2026-06-13 docstring figure of 942
(`person.py:236-238`) is 205 notes stale — the vault has grown by more than a fifth since the only
prior audit on record.

**(b) Entries `Email.parse` refuses: 0** of 1021 non-empty `emails:` entries. Explicit marker: **no
matches.** This is E2 class (a) — the only class that can LOSE a lookup at cutover — and it is empty on
the live corpus.

**(c) Entries where `raw.lower()` ≠ `Email.parse(raw).value`: 0.** Whitespace class (E2(c)): 0, no
matches. Angle-bracket class (E2(b)): 0, no matches. Other: 0, no matches. Neither behaviour-changing
"improvement" class has a single live specimen; cutover changes NO live answer.

**(d) Cross-note `phones:`/`whatsapp:` pairs `phones_match` unifies but `Phone.key` does not: 0** over
276 phone/whatsapp values (0 refused by `Phone.parse`), no matches. **The fuzzy arm AC-3 preserves has
zero live witnesses today** — on this corpus the non-transitive matcher and the typed key agree on every
cross-note pair. AC-3's preservation is therefore a behaviour-compatibility promise with no live case
behind it, not a repair of a live loss; the criterion stands (the arm is reachable and the fixture proves
it), but the reason to KEEP it is compatibility, and the number that would tell us if the arm is dead
is now on record: it is.

**(e) HEAD SHAs** at audit time (40-hex, from the verbatim block): HAL9000
`68fbd334bf8deb18fc5eb58ffa968273e90313bf`, exocortex `2c6f0896a1e8b184b641e0b7fb91386ee11e2a76`,
orchestrator `d44418d9c16a88e57ad0f0a88ea8a930b5a64ea0`, obsidian-schemas (pre-build)
`990aa6de47833cddeff765684c87812e907f63b4`. Direct consumer reaches into the legacy per-kind dicts:
HAL9000 2 (both in tests — one a wall that NAMES the private reaches as forbidden, one a docstring),
exocortex 0, orchestrator 0. No live consumer code reads `_email_index`; deleting it breaks nothing
outside this repo.

## What this settles for the AC frame (E2's decision rule, applied)

1. **Zero refusals ⇒ the CUTOVER arm.** Email resolution moves to the unified identifier index and
   `_email_index` is deleted; no repair rule is routed to WI-026 for email. AC-2's "whichever arm the
   corpus audit selects" resolves to: the index.
2. **No AC is falsified by these bytes.** AC-2 is written arm-agnostic; AC-3 preserves the fuzzy phone
   arm as behaviour (its live witness count is 0, recorded above, which does not make the criterion
   wrong); AC-4's golden is fixture-based (E5: hermetic, never a vault walk); AC-5 pins THIS file's shape.
3. **The stale docstring at `person.py:236-238` is a documentation-truth rider for AC-5's class**: a
   confident reading (942 notes, 2026-06-13) standing in for a run. It should be replaced by a pointer to
   this artifact, not refreshed with a new number that will drift the same way.
