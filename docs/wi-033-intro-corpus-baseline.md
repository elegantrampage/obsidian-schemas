# WI-033 precondition 2 — the live vault's timeline-kind census (intro-by / intro-to / legacy `[intro]` / retired `introduced_by`)

Conductor-measured 2026-09-28 (after the same day's one-note `introduced_by` → `intro-by` conversion,
recorded in WI-033's `## Ruling — 2026-09-28`), committed as WI-033's second `kind: precondition` fence
(`docs/timeline-entry-relocation.md` → `## Write Targets`) BEFORE the criteria are frozen. The floor is
hermetic (WI-031 clause (v)) and the builder cannot reach the vault; this file turns the ruling's prose
numbers into a dated, re-runnable snapshot. **Counts and shapes only — no vault note name and no live
identifier appears here**, matching `docs/vault-shape-census.md`'s rule. `$VAULT` is the live vault root
(`OBSIDIAN_VAULT_PATH`); obsidian-schemas HEAD at measurement: `bc2f11e23df9af2b1635c97ba0be7940a8ab2184`.

This is also the ENTRY half of the bracket should the `[intro]` → `intro-to` rewrite (A5) ever be taken.

## What it settles, per criterion

- **AC-3 (the population an unconditional ban could brick is empty).** `introduced_by_frontmatter_carriers:
  0` over 5664 markdown files (1314 with `type: person`),
  0 undecodable. The ban has no live carrier to brick.
- **AC-2 (marker-only reach is honest, not convenient).** Legacy `intro`: 86
  entries, 22 with a well-formed marker — so markerless entries are a
  real population. `intro-by`: 1 entry, 1
  marked, on 1 note (the 2026-09-28 conversion). `intro-to`:
  0. The accessor's live yield today is exactly one record.
- **AC-4 (expected live yield of the report-only checks).** `legacy_intro_entry` should report
  86 (heading grammars: 43
  `Month D, YYYY` / 38 ISO with time /
  5 bare ISO — all three planted by AC-4(a));
  `intro_by_without_marker` should report 0;
  `retired_key_introduced_by` should report 0.
- **Other kinds on disk (context for precondition 1's parity universe).** `note`
  4 (all ISO-with-time, no marker — the pre-WI-058 contacts-skill shape),
  `merge` 3 (all `Month D, YYYY` with a well-formed marker — the current
  renderer's shape, via an ad-hoc HTTP-door caller), `meeting` 1 and
  `email` 1 (bare ISO, no marker). Every timeline heading found sits
  inside a `## Timeline` section; no marker anywhere carries a kind different from its own heading.

## Definitions (the predicates, so another reader can contradict them)

- An **entry** is a line matching `^### (?P<date>.*?) \[(?P<kind>[a-z][a-z0-9_-]*)\] *$` in any `*.md`
  under `$VAULT` (recursive). Its **body** is the following lines up to the next `^#{2,3} ` line.
- A **well-formed marker** is a body line matching
  `^<!-- (?P<kind>[a-z][a-z0-9_-]*):(?P<day>\d{4}-\d{2}-\d{2}):(?P<disc>.+) -->$` whose `kind` equals
  the entry's own. A marker whose kind differs is counted under `marker_kind_mismatch_by_kind`.
- An **`introduced_by` carrier** is a note whose YAML frontmatter (between the leading `---` fences) has a
  line matching `^introduced_by\s*:`.
- **Heading date grammar**: `month_d_yyyy` = `[A-Z][a-z]+ \d{1,2}, \d{4}`; `iso_with_time` =
  `\d{4}-\d{2}-\d{2} \d{2}:\d{2}(:\d{2})?`; `iso` = `\d{4}-\d{2}-\d{2}`; anything else `other`.

## Command

```
cd /Users/davewascha/Workspaces/obsidian-schemas && .venv/bin/python <census.py from the appendix> "$VAULT"
```

Read-only: the script opens files with `read_text` and writes nothing.

## Counts

The machine-readable snapshot. One `yaml` fence; a test reads it as a premise (AC-3(c)'s live half) and
never re-measures the vault. Keys are exactly the script's output keys.

```yaml
entries_by_kind:
  email: 1
  intro: 86
  intro-by: 1
  intro-to: 0
  meeting: 1
  merge: 3
  note: 4
heading_date_grammar_by_kind:
  email:
    iso: 1
  intro:
    iso: 5
    iso_with_time: 38
    month_d_yyyy: 43
  intro-by:
    month_d_yyyy: 1
  intro-to: {}
  meeting:
    iso: 1
  merge:
    month_d_yyyy: 3
  note:
    iso_with_time: 4
inside_timeline_section_by_kind:
  email: 1
  intro: 86
  intro-by: 1
  intro-to: 0
  meeting: 1
  merge: 3
  note: 4
introduced_by_frontmatter_carriers: 0
markdown_files_scanned: 5664
marker_kind_mismatch_by_kind:
  email: 0
  intro: 0
  intro-by: 0
  intro-to: 0
  meeting: 0
  merge: 0
  note: 0
notes_carrying_intro_by: 1
person_notes: 1314
undecodable_files: 0
well_formed_marker_by_kind:
  email: 0
  intro: 22
  intro-by: 1
  intro-to: 0
  meeting: 0
  merge: 3
  note: 0
```

## Verbatim output

```
{
  "entries_by_kind": {
    "email": 1,
    "intro": 86,
    "intro-by": 1,
    "intro-to": 0,
    "meeting": 1,
    "merge": 3,
    "note": 4
  },
  "heading_date_grammar_by_kind": {
    "email": {
      "iso": 1
    },
    "intro": {
      "iso": 5,
      "iso_with_time": 38,
      "month_d_yyyy": 43
    },
    "intro-by": {
      "month_d_yyyy": 1
    },
    "intro-to": {},
    "meeting": {
      "iso": 1
    },
    "merge": {
      "month_d_yyyy": 3
    },
    "note": {
      "iso_with_time": 4
    }
  },
  "inside_timeline_section_by_kind": {
    "email": 1,
    "intro": 86,
    "intro-by": 1,
    "intro-to": 0,
    "meeting": 1,
    "merge": 3,
    "note": 4
  },
  "introduced_by_frontmatter_carriers": 0,
  "markdown_files_scanned": 5664,
  "marker_kind_mismatch_by_kind": {
    "email": 0,
    "intro": 0,
    "intro-by": 0,
    "intro-to": 0,
    "meeting": 0,
    "merge": 0,
    "note": 0
  },
  "notes_carrying_intro_by": 1,
  "person_notes": 1314,
  "undecodable_files": 0,
  "well_formed_marker_by_kind": {
    "email": 0,
    "intro": 22,
    "intro-by": 1,
    "intro-to": 0,
    "meeting": 0,
    "merge": 3,
    "note": 0
  }
}
```

## Appendix — `census.py`, verbatim

```python
"""WI-033 precondition 2 census: counts and shapes only, never a note name or identifier.
Usage: python census.py "$OBSIDIAN_VAULT_PATH"   (read-only; opens files with open(), writes nothing)"""
import re, sys, json
from collections import Counter
from pathlib import Path
vault = Path(sys.argv[1])
HEAD_RE = re.compile(r"^### (?P<date>.*?) \[(?P<kind>[a-z][a-z0-9_-]*)\] *$")
SECTION_RE = re.compile(r"^#{2,3} ")
MARKER_RE = re.compile(r"^<!-- (?P<kind>[a-z][a-z0-9_-]*):(?P<day>\d{4}-\d{2}-\d{2}):(?P<disc>.+) -->$")
def grammar(d):
    if re.fullmatch(r"[A-Z][a-z]+ \d{1,2}, \d{4}", d): return "month_d_yyyy"
    if re.fullmatch(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}(:\d{2})?", d): return "iso_with_time"
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", d): return "iso"
    return "other"
files = sorted(vault.rglob("*.md")); undecodable = 0
entries = Counter(); marked = Counter(); mismatched = Counter(); in_timeline = Counter()
grammars = Counter(); introduced_by = 0; person_notes = 0; notes_with_intro_by = 0
for f in files:
    try: text = f.read_text(encoding="utf-8")
    except UnicodeDecodeError: undecodable += 1; continue
    lines = text.splitlines()
    fm = []
    if lines and lines[0] == "---":
        for l in lines[1:]:
            if l == "---": break
            fm.append(l)
    if any(l.startswith("type: person") for l in fm): person_notes += 1
    if any(re.match(r"^introduced_by\s*:", l) for l in fm): introduced_by += 1
    section = None; has_ib = False
    for i, l in enumerate(lines):
        if l.startswith("## "): section = l[3:].strip()
        m = HEAD_RE.match(l)
        if not m: continue
        k = m["kind"]; entries[k] += 1; grammars[(k, grammar(m["date"]))] += 1
        if k == "intro-by": has_ib = True
        if section == "Timeline": in_timeline[k] += 1
        body = []
        for l2 in lines[i+1:]:
            if SECTION_RE.match(l2): break
            body.append(l2)
        mk = [MARKER_RE.match(b) for b in body]; mk = [x for x in mk if x]
        if any(x["kind"] == k for x in mk): marked[k] += 1
        elif mk: mismatched[k] += 1
    notes_with_intro_by += has_ib
kinds = sorted(entries)
out = {
  "markdown_files_scanned": len(files), "undecodable_files": undecodable, "person_notes": person_notes,
  "introduced_by_frontmatter_carriers": introduced_by,
  "entries_by_kind": {k: entries[k] for k in kinds},
  "well_formed_marker_by_kind": {k: marked[k] for k in kinds},
  "marker_kind_mismatch_by_kind": {k: mismatched[k] for k in kinds},
  "inside_timeline_section_by_kind": {k: in_timeline[k] for k in kinds},
  "heading_date_grammar_by_kind": {k: {g: grammars[(k, g)] for g in ("month_d_yyyy", "iso_with_time", "iso", "other") if grammars[(k, g)]} for k in kinds},
  "notes_carrying_intro_by": notes_with_intro_by,
}
for k in ("intro", "intro-by", "intro-to"):
    for d in ("entries_by_kind", "well_formed_marker_by_kind", "marker_kind_mismatch_by_kind", "inside_timeline_section_by_kind"):
        out[d].setdefault(k, 0)
    out["heading_date_grammar_by_kind"].setdefault(k, {})
print(json.dumps(out, indent=2, sort_keys=True))
```
