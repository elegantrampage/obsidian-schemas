# WI-033 precondition 1 — HAL9000's shipped timeline-entry code: source, parity samples, validation boundary

Conductor-produced 2026-09-28, committed as WI-033's first `kind: precondition` fence
(`docs/timeline-entry-relocation.md` → `## Write Targets`) BEFORE the criteria are frozen. The caged
builder cannot read HAL9000; this file is the external oracle AC-1(a), (a2), (a3) and (c2) read.

**Staleness anchor (AC-1(a3), D7).** HAL9000 HEAD: `d54430da9547a93525c6cc1b20cf781c9a63f82e`. Captured with `backend_fastapi/` clean at
that HEAD (`git status --short -- backend_fastapi` empty, asserted by the generator). The library's
`HAL9000_PARITY_ANCHOR` must equal this 40-hex value. The cutover item's re-entry condition re-runs this
capture at HAL9000's then-HEAD and diffs against it.

**How it was produced.** Every `rendered` block and every `verdict` below was produced by RUNNING
HAL9000's code, not by reading it: the generator imports `core.timeline_entry` (`TimelineEntry`,
`InvalidTimelineEntry`, `render`) and `routers.introduce` (`INTRO_KIND`, `OBSERVED_KIND_ON_INTRODUCEE`,
`OBSERVED_KIND_ON_INTRODUCER`, `_observed_entry_text`) under HAL9000's own venv with cwd
`backend_fastapi/`, and serializes the results with `yaml.safe_dump`. The generator is reproduced
verbatim in the appendix, so a re-run is one command. Every name in the samples is SYNTHETIC — no vault
note name and no live identifier appears in this file.

**Kinds HAL9000 renders (the parity universe).** Five. Four have a code producer, found by enumerating
every in-process caller of `append_timeline_entry` under `backend_fastapi/` (tests excluded): `intro`
(`routers/introduce.py:70`, written at `:707-712`), `intro-by` and `intro-to` (`:71-72`, written at
`:1058-1065` with text from `_observed_entry_text`), and `note` (`skills/contacts_skill.py:191-193`, no
discriminator). The fifth, `merge`, has NO code producer anywhere in the estate, but the live census
(`docs/wi-033-intro-corpus-baseline.md`) finds 3 `merge` entries, all dated 2026-09-26, in this renderer's
exact `Month D, YYYY` heading shape with a well-formed marker — i.e. written through the HTTP door
(`routers/entities.py:358-427`, which accepts any slug-valid kind) by an ad-hoc caller. It is therefore a
kind HAL9000 HAS rendered onto disk, and it carries a sample so AC-1(a2) holds; its sample `text` is
synthetic because no producer defines one. Two further kinds on disk, `meeting` and `email`, carry bare-ISO
headings and no marker — a pre-WI-058 writer's shape, not this renderer's — and carry no sample. The
library's `PARITY_KINDS` equals the set of `kind` values in `## Parity samples`:
{`intro`, `intro-by`, `intro-to`, `merge`, `note`}.

**Key format (WI-077 note 6).** `dedupe_key` is `{kind}:{YYYY-MM-DD}:{discriminator}` with the
discriminator VERBATIM (no slug, no case-fold); for `intro-by`/`intro-to` the discriminator is the
counterparty's canonical `Person.name` and is ALSO the datum WI-033's accessor reads
(`core/timeline_entry.py:47-63`). The embedded marker is `<!-- {key} -->` and is omitted, never emitted
empty, when the discriminator is `None`.

**Machine-readable shape.** `## Parity samples` holds one `yaml` fence per sample with exactly the keys
`kind`, `text`, `when` (an ISO-8601 string, naive local time, parsed by `datetime.fromisoformat`; it feeds
BOTH the heading and the marker's day slot), `discriminator` (explicit `null` where the shipped call
passes none) and `rendered` (a literal block scalar holding the verbatim bytes; its single trailing
newline is the renderer's own). `## Validation boundary` holds one `yaml` fence per probe with exactly the
keys `field`, `value` (explicit `null` for an absent discriminator) and `verdict` (`accept` | `refuse`),
each verdict being whether HAL9000's `TimelineEntry(...)` constructor raised `InvalidTimelineEntry` with
the other fields held at a valid baseline (`kind="note"`, `text="probe"`, `discriminator=None`).

**What the boundary shows, stated so no reader re-derives it.** HAL9000 validates `kind` by the slug
regex alone; it does NOT sanitize `text` (a `-->`/`<!--`-bearing text is ACCEPTED — deliberate,
`core/timeline_entry.py:41-46`); it refuses a discriminator only for a comment delimiter or a newline, so
an EMPTY, a WHITESPACE-ONLY and a `:`-bearing discriminator are all ACCEPTED. Those five accepted inputs
are exactly AC-1(c)'s deliberate guard set, which the library refuses on purpose; AC-1(c2) asserts that
set as an equality. Out of scope of these verdicts: the HTTP door's own 400 for a blank or missing
`kind`/`text` (`routers/entities.py:386-397`), which fires before the constructor.

## Part 1 — source (verbatim, with line ranges)

`backend_fastapi/core/timeline_entry.py` lines 84-190 at `d54430da9547a93525c6cc1b20cf781c9a63f82e`:

```python
KIND_PATTERN = re.compile(r"^[a-z][a-z0-9_-]{0,31}$")

# The two byte sequences that would let a `discriminator` escape or forge the
# HTML comment it lands inside.
_COMMENT_DELIMITERS = ("-->", "<!--")


class InvalidTimelineEntry(ValueError):
    """A caller-supplied field that would break the entry's own structure.

    Raised by `TimelineEntry`'s own validation, so it is impossible to hold an
    entry that renders to broken markdown. The HTTP door maps it to 422.
    """


@dataclass(frozen=True)
class TimelineEntry:
    """One timeline event, before it is markdown.

    `when` is ALWAYS supplied by the constructor's caller — `render` never reads
    a clock — so a multi-write request can pin one stamp across all of its
    entries.
    """

    kind: str
    text: str
    when: datetime
    discriminator: Optional[str] = None

    def __post_init__(self) -> None:
        if not isinstance(self.kind, str) or not KIND_PATTERN.match(self.kind):
            raise InvalidTimelineEntry(
                f"kind must be a 1-32 character lowercase slug matching "
                f"{KIND_PATTERN.pattern!r}, got {self.kind!r}"
            )
        if not isinstance(self.text, str) or not self.text.strip():
            raise InvalidTimelineEntry("text must be a non-empty string")
        if self.discriminator is not None:
            if not isinstance(self.discriminator, str):
                raise InvalidTimelineEntry("discriminator must be a string or null")
            for delimiter in _COMMENT_DELIMITERS:
                if delimiter in self.discriminator:
                    raise InvalidTimelineEntry(
                        f"discriminator may not contain {delimiter!r} — it lands "
                        f"inside an HTML comment"
                    )
            if "\n" in self.discriminator or "\r" in self.discriminator:
                raise InvalidTimelineEntry(
                    "discriminator may not contain a newline — it lands inside a "
                    "single-line HTML comment"
                )


def _now() -> datetime:
    """The module's single clock read, patchable BY NAME.

    Module-level so a check can swap `core.timeline_entry._now`, exactly as
    `routers/introduce.py:_now` is swapped today. Never called from inside an
    `except` handler (the standing WI-046 sweep goes red on that).
    """
    return datetime.now()


def dedupe_key(entry: TimelineEntry) -> Optional[str]:
    """The BARE key — what a caller RECORDS (e.g. `TimelineWrite.deduplicate_key`).

    `None` when the entry carries no discriminator, which means "no dedupe": a
    free-text note has no event identity to key on, and inventing one would
    silently suppress a second, genuinely intended note with the same words.

    The discriminator is carried VERBATIM — no slug, no case-fold, no
    transliteration, or `Sören Winter` and `Søren Winter` would collide.
    """
    if entry.discriminator is None:
        return None
    return f"{entry.kind}:{entry.when.strftime('%Y-%m-%d')}:{entry.discriminator}"


def dedupe_probe(entry: TimelineEntry) -> Optional[str]:
    """M1 — the DELIMITED form, and the ONLY string handed to the primitive.

    Derived from the same `entry` whose comment `render` emits, so a key that is
    passed can never fail to be the key that was embedded.
    """
    key = dedupe_key(entry)
    return None if key is None else f"<!-- {key} -->"


def render(entry: TimelineEntry) -> str:
    """The canonical bytes, and the only place they are composed.

    Exactly `### {when:%B %-d, %Y} [{kind}]\\n{text}\\n<!-- {key} -->\\n`, and
    without a discriminator exactly `### {when:%B %-d, %Y} [{kind}]\\n{text}\\n` —
    the HTML comment is omitted, never emitted empty.

    This is byte-for-byte the string `routers/introduce.py` composed before the
    migration, which is what makes the largest live producer's move a refactor
    rather than a behaviour change. `%-d` is the platform-specific no-pad day
    that writer already shipped; it is inherited, not "fixed".
    """
    heading = f"### {entry.when.strftime('%B %-d, %Y')} [{entry.kind}]\n"
    body = f"{entry.text}\n"
    key = dedupe_key(entry)
    if key is None:
        return heading + body
    return f"{heading}{body}<!-- {key} -->\n"

```

`backend_fastapi/routers/introduce.py` lines 70-72 at `d54430da9547a93525c6cc1b20cf781c9a63f82e`:

```python
INTRO_KIND = "intro"                      # OUTBOUND (WI-036) — the slug this router has always written
OBSERVED_KIND_ON_INTRODUCEE = "intro-by"  # inbound, on the note of the person Dave was introduced TO
OBSERVED_KIND_ON_INTRODUCER = "intro-to"  # inbound, on the note of the person who made the intro
```

`backend_fastapi/routers/introduce.py` lines 777-815 at `d54430da9547a93525c6cc1b20cf781c9a63f82e`:

```python
def _observed_entry_text(kind, stem, other_name, source, thread_id) -> str:
    """THE declared sentence of this door, in its two role-shaped forms.

        on the introducee's note, intro-by :  Introduced by [[<stem>|<introducer>]] via <source> (thread <id>)
        on the introducer's note, intro-to :  Introduced Dave to [[<stem>|<introducee>]] via <source> (thread <id>)

    `<stem>` is the COUNTERPARTY note's own file stem as the repository reports it, so
    a note filed `@Sarah Varki.md` renders `[[@Sarah Varki|Sarah Varki]]` — a PIPED
    wikilink whose target is the real file and whose label is the canonical name. The
    bare `[[Sarah Varki]]` form is not a shorter spelling of the same thing; it is a
    link to nothing in a vault where every person note is filed `@Name.md`.

    `<source>` is the channel id VERBATIM, never translated into a prose word, so this
    door introduces no second channel vocabulary and no id→prose mapping whose
    totality would then need its own assertion. The accepted, visible consequence: an
    inbound entry reads "via gmail" where the legacy outbound writer hard-codes "via
    email". Nothing reads either — the prose is for Dave's eye, and every machine fact
    lives in the kind and discriminator slots.

    The provenance parenthetical is omitted ENTIRELY when `thread_id` is absent, never
    rendered with `None` in it: the optional field's absence is a shape the door states
    rather than a `None` it interpolates into Dave's note. It is for Dave's eye — the
    only route from the claim back to the email that produced it, since this entry is a
    machine's CONCLUSION rather than a record of something Dave did — and no machine
    reader keys on it, which is why a replay that changes or omits it still dedupes.

    `<introducer>` / `<introducee>` are the canonical `Person.name` the seam returned,
    never the caller's query string: what was resolved is what is shown.
    """
    if kind == OBSERVED_KIND_ON_INTRODUCEE:
        sentence = f"Introduced by [[{stem}|{other_name}]] via {source}"
    elif kind == OBSERVED_KIND_ON_INTRODUCER:
        sentence = f"Introduced Dave to [[{stem}|{other_name}]] via {source}"
    else:
        # Fails CLOSED. This door writes exactly two kinds and a third is a bug, not a
        # case to render generically.
        raise ValueError(f"no declared observed-intro sentence for kind {kind!r}")
    return sentence if thread_id is None else f"{sentence} (thread {thread_id})"

```

## Parity samples

```yaml
kind: intro
text: Introduced to [[@Voxleaf Arden|Voxleaf Arden]] via email
when: '2026-09-03T09:15:00'
discriminator: Voxleaf Arden
rendered: |
  ### September 3, 2026 [intro]
  Introduced to [[@Voxleaf Arden|Voxleaf Arden]] via email
  <!-- intro:2026-09-03:Voxleaf Arden -->
```

```yaml
kind: intro-by
text: Introduced by [[@Sören Wexley|Sören Wexley]] via gmail (thread 18c2f0a9d3e4b5f6)
when: '2026-09-27T18:42:07'
discriminator: Sören Wexley
rendered: |
  ### September 27, 2026 [intro-by]
  Introduced by [[@Sören Wexley|Sören Wexley]] via gmail (thread 18c2f0a9d3e4b5f6)
  <!-- intro-by:2026-09-27:Sören Wexley -->
```

```yaml
kind: intro-by
text: Introduced by [[@Tamsin Okoro-Vale|Tamsin Okoro-Vale]] via gmail
when: '2025-11-10T00:00:00'
discriminator: Tamsin Okoro-Vale
rendered: |
  ### November 10, 2025 [intro-by]
  Introduced by [[@Tamsin Okoro-Vale|Tamsin Okoro-Vale]] via gmail
  <!-- intro-by:2025-11-10:Tamsin Okoro-Vale -->
```

```yaml
kind: intro-to
text: Introduced Dave to [[@Voxleaf Arden|Voxleaf Arden]] via gmail (thread 18c2f0a9d3e4b5f6)
when: '2026-09-27T18:42:07'
discriminator: Voxleaf Arden
rendered: |
  ### September 27, 2026 [intro-to]
  Introduced Dave to [[@Voxleaf Arden|Voxleaf Arden]] via gmail (thread 18c2f0a9d3e4b5f6)
  <!-- intro-to:2026-09-27:Voxleaf Arden -->
```

```yaml
kind: note
text: Mentioned the Lisbon offsite; follow up in October.
when: '2026-12-25T23:59:59'
discriminator: null
rendered: |
  ### December 25, 2026 [note]
  Mentioned the Lisbon offsite; follow up in October.
```

```yaml
kind: merge
text: Merged duplicate note [[@Voxleaf Arden (old)|Voxleaf Arden (old)]] into this one
when: '2026-09-26T08:05:00'
discriminator: Voxleaf Arden (old)
rendered: |
  ### September 26, 2026 [merge]
  Merged duplicate note [[@Voxleaf Arden (old)|Voxleaf Arden (old)]] into this one
  <!-- merge:2026-09-26:Voxleaf Arden (old) -->
```

## Validation boundary

```yaml
field: kind
value: deal-closed
verdict: accept
```

```yaml
field: kind
value: note
verdict: accept
```

```yaml
field: kind
value: intro-by
verdict: accept
```

```yaml
field: kind
value: a
verdict: accept
```

```yaml
field: kind
value: note_x
verdict: accept
```

```yaml
field: kind
value: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
verdict: accept
```

```yaml
field: kind
value: xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
verdict: refuse
```

```yaml
field: kind
value: Note
verdict: refuse
```

```yaml
field: kind
value: deal closed
verdict: refuse
```

```yaml
field: kind
value: ''
verdict: refuse
```

```yaml
field: kind
value: 1note
verdict: refuse
```

```yaml
field: kind
value: 'note:'
verdict: refuse
```

```yaml
field: kind
value: note-->
verdict: refuse
```

```yaml
field: kind
value: <!--note
verdict: refuse
```

```yaml
field: text
value: Met for coffee
verdict: accept
```

```yaml
field: text
value: ''
verdict: refuse
```

```yaml
field: text
value: '   '
verdict: refuse
```

```yaml
field: text
value: see --> here
verdict: accept
```

```yaml
field: text
value: <!-- forged -->
verdict: accept
```

```yaml
field: text
value: Introduced by [[@Sören Wexley|Sören Wexley]] via gmail
verdict: accept
```

```yaml
field: text
value: 'line one

  line two'
verdict: accept
```

```yaml
field: discriminator
value: null
verdict: accept
```

```yaml
field: discriminator
value: ''
verdict: accept
```

```yaml
field: discriminator
value: '   '
verdict: accept
```

```yaml
field: discriminator
value: a:b
verdict: accept
```

```yaml
field: discriminator
value: Sören Wexley
verdict: accept
```

```yaml
field: discriminator
value: x-->y
verdict: refuse
```

```yaml
field: discriminator
value: <!--x
verdict: refuse
```

```yaml
field: discriminator
value: 'a

  b'
verdict: refuse
```

## Appendix — the generator, verbatim

Run from `HAL9000/backend_fastapi` with `PYTHONPATH=. /Users/davewascha/Workspaces/HAL9000/.venv/bin/python <this script> > <out>`.

```python
"""WI-033 precondition 1 generator: RUNS HAL9000's shipped timeline code and emits the capture.
Run with HAL9000's venv, cwd = HAL9000/backend_fastapi. Synthetic names only."""
import subprocess, sys, yaml
from datetime import datetime
from pathlib import Path
from core.timeline_entry import TimelineEntry, InvalidTimelineEntry, render
from routers.introduce import (INTRO_KIND, OBSERVED_KIND_ON_INTRODUCEE,
                               OBSERVED_KIND_ON_INTRODUCER, _observed_entry_text)

HAL = Path("/Users/davewascha/Workspaces/HAL9000")
HEAD = subprocess.check_output(["git", "-C", str(HAL), "rev-parse", "HEAD"], text=True).strip()
dirty_src = subprocess.check_output(["git", "-C", str(HAL), "status", "--short", "--", "backend_fastapi"], text=True)
assert dirty_src == "", f"HAL9000 backend_fastapi is dirty:\n{dirty_src}"

class Lit(str): pass
def lit_rep(d, s): return d.represent_scalar("tag:yaml.org,2002:str", s, style="|")
yaml.SafeDumper.add_representer(Lit, lit_rep)
def fence(obj): return "```yaml\n" + yaml.safe_dump(obj, allow_unicode=True, sort_keys=False, width=10**6) + "```\n"

# ---- part 2: parity samples, each produced by calling HAL9000's render on pinned inputs,
# with text composed the way the shipped producer composes it.
def s(kind, text, when, disc):
    e = TimelineEntry(kind=kind, text=text, when=datetime.fromisoformat(when), discriminator=disc)
    return {"kind": kind, "text": text, "when": when, "discriminator": disc, "rendered": Lit(render(e))}
samples = [
    # routers/introduce.py:707-712 (outbound WI-036): text f"Introduced to [[{stem}|{name}]] via email", disc = counterparty
    s(INTRO_KIND, "Introduced to [[@Voxleaf Arden|Voxleaf Arden]] via email", "2026-09-03T09:15:00", "Voxleaf Arden"),
    # routers/introduce.py:1058-1065 + _observed_entry_text (WI-077), with and without thread provenance
    s(OBSERVED_KIND_ON_INTRODUCEE, _observed_entry_text(OBSERVED_KIND_ON_INTRODUCEE, "@Sören Wexley", "Sören Wexley", "gmail", "18c2f0a9d3e4b5f6"), "2026-09-27T18:42:07", "Sören Wexley"),
    s(OBSERVED_KIND_ON_INTRODUCEE, _observed_entry_text(OBSERVED_KIND_ON_INTRODUCEE, "@Tamsin Okoro-Vale", "Tamsin Okoro-Vale", "gmail", None), "2025-11-10T00:00:00", "Tamsin Okoro-Vale"),
    s(OBSERVED_KIND_ON_INTRODUCER, _observed_entry_text(OBSERVED_KIND_ON_INTRODUCER, "@Voxleaf Arden", "Voxleaf Arden", "gmail", "18c2f0a9d3e4b5f6"), "2026-09-27T18:42:07", "Voxleaf Arden"),
    # skills/contacts_skill.py:191-193: kind="note", free text, NO discriminator
    s("note", "Mentioned the Lisbon offsite; follow up in October.", "2026-12-25T23:59:59", None),
    # `merge`: no code producer; 3 on-disk entries (2026-09-26) are in this renderer's exact shape with a
    # well-formed marker, i.e. an ad-hoc caller of the HTTP door. Text is SYNTHETIC (no producer defines one).
    s("merge", "Merged duplicate note [[@Voxleaf Arden (old)|Voxleaf Arden (old)]] into this one", "2026-09-26T08:05:00", "Voxleaf Arden (old)"),
]

# ---- part 3: validation boundary, each verdict produced by CONSTRUCTING HAL9000's TimelineEntry
BASE = dict(kind="note", text="probe", when=datetime(2026, 9, 28, 12, 0), discriminator=None)
def verdict(field, value):
    kw = dict(BASE); kw[field] = value
    try: TimelineEntry(**kw); return "accept"
    except InvalidTimelineEntry: return "refuse"
probes = [("kind", v) for v in ["deal-closed", "note", "intro-by", "a", "note_x", "x"*32, "x"*33,
                                "Note", "deal closed", "", "1note", "note:", "note-->", "<!--note"]]
probes += [("text", v) for v in ["Met for coffee", "", "   ", "see --> here", "<!-- forged -->",
                                 "Introduced by [[@Sören Wexley|Sören Wexley]] via gmail", "line one\nline two"]]
probes += [("discriminator", v) for v in [None, "", "   ", "a:b", "Sören Wexley", "x-->y", "<!--x", "a\nb"]]
boundary = [{"field": f, "value": v, "verdict": verdict(f, v)} for f, v in probes]

def excerpt(rel, a, b):
    lines = (HAL / rel).read_text().splitlines()
    return f"`{rel}` lines {a}-{b} at `{HEAD}`:\n\n```python\n" + "\n".join(lines[a-1:b]) + "\n```\n"

out = []
out.append(f"""# WI-033 precondition 1 — HAL9000's shipped timeline-entry code: source, parity samples, validation boundary

Conductor-produced 2026-09-28, committed as WI-033's first `kind: precondition` fence
(`docs/timeline-entry-relocation.md` → `## Write Targets`) BEFORE the criteria are frozen. The caged
builder cannot read HAL9000; this file is the external oracle AC-1(a), (a2), (a3) and (c2) read.

**Staleness anchor (AC-1(a3), D7).** HAL9000 HEAD: `{HEAD}`. Captured with `backend_fastapi/` clean at
that HEAD (`git status --short -- backend_fastapi` empty, asserted by the generator). The library's
`HAL9000_PARITY_ANCHOR` must equal this 40-hex value. The cutover item's re-entry condition re-runs this
capture at HAL9000's then-HEAD and diffs against it.

**How it was produced.** Every `rendered` block and every `verdict` below was produced by RUNNING
HAL9000's code, not by reading it: the generator imports `core.timeline_entry` (`TimelineEntry`,
`InvalidTimelineEntry`, `render`) and `routers.introduce` (`INTRO_KIND`, `OBSERVED_KIND_ON_INTRODUCEE`,
`OBSERVED_KIND_ON_INTRODUCER`, `_observed_entry_text`) under HAL9000's own venv with cwd
`backend_fastapi/`, and serializes the results with `yaml.safe_dump`. The generator is reproduced
verbatim in the appendix, so a re-run is one command. Every name in the samples is SYNTHETIC — no vault
note name and no live identifier appears in this file.

**Kinds HAL9000 renders (the parity universe).** Five. Four have a code producer, found by enumerating
every in-process caller of `append_timeline_entry` under `backend_fastapi/` (tests excluded): `intro`
(`routers/introduce.py:70`, written at `:707-712`), `intro-by` and `intro-to` (`:71-72`, written at
`:1058-1065` with text from `_observed_entry_text`), and `note` (`skills/contacts_skill.py:191-193`, no
discriminator). The fifth, `merge`, has NO code producer anywhere in the estate, but the live census
(`docs/wi-033-intro-corpus-baseline.md`) finds 3 `merge` entries, all dated 2026-09-26, in this renderer's
exact `Month D, YYYY` heading shape with a well-formed marker — i.e. written through the HTTP door
(`routers/entities.py:358-427`, which accepts any slug-valid kind) by an ad-hoc caller. It is therefore a
kind HAL9000 HAS rendered onto disk, and it carries a sample so AC-1(a2) holds; its sample `text` is
synthetic because no producer defines one. Two further kinds on disk, `meeting` and `email`, carry bare-ISO
headings and no marker — a pre-WI-058 writer's shape, not this renderer's — and carry no sample. The
library's `PARITY_KINDS` equals the set of `kind` values in `## Parity samples`:
{{`intro`, `intro-by`, `intro-to`, `merge`, `note`}}.

**Key format (WI-077 note 6).** `dedupe_key` is `{{kind}}:{{YYYY-MM-DD}}:{{discriminator}}` with the
discriminator VERBATIM (no slug, no case-fold); for `intro-by`/`intro-to` the discriminator is the
counterparty's canonical `Person.name` and is ALSO the datum WI-033's accessor reads
(`core/timeline_entry.py:47-63`). The embedded marker is `<!-- {{key}} -->` and is omitted, never emitted
empty, when the discriminator is `None`.

**Machine-readable shape.** `## Parity samples` holds one `yaml` fence per sample with exactly the keys
`kind`, `text`, `when` (an ISO-8601 string, naive local time, parsed by `datetime.fromisoformat`; it feeds
BOTH the heading and the marker's day slot), `discriminator` (explicit `null` where the shipped call
passes none) and `rendered` (a literal block scalar holding the verbatim bytes; its single trailing
newline is the renderer's own). `## Validation boundary` holds one `yaml` fence per probe with exactly the
keys `field`, `value` (explicit `null` for an absent discriminator) and `verdict` (`accept` | `refuse`),
each verdict being whether HAL9000's `TimelineEntry(...)` constructor raised `InvalidTimelineEntry` with
the other fields held at a valid baseline (`kind="note"`, `text="probe"`, `discriminator=None`).

**What the boundary shows, stated so no reader re-derives it.** HAL9000 validates `kind` by the slug
regex alone; it does NOT sanitize `text` (a `-->`/`<!--`-bearing text is ACCEPTED — deliberate,
`core/timeline_entry.py:41-46`); it refuses a discriminator only for a comment delimiter or a newline, so
an EMPTY, a WHITESPACE-ONLY and a `:`-bearing discriminator are all ACCEPTED. Those five accepted inputs
are exactly AC-1(c)'s deliberate guard set, which the library refuses on purpose; AC-1(c2) asserts that
set as an equality. Out of scope of these verdicts: the HTTP door's own 400 for a blank or missing
`kind`/`text` (`routers/entities.py:386-397`), which fires before the constructor.

## Part 1 — source (verbatim, with line ranges)

""")
out.append(excerpt("backend_fastapi/core/timeline_entry.py", 84, 190))
out.append("\n")
out.append(excerpt("backend_fastapi/routers/introduce.py", 70, 72))
out.append("\n")
out.append(excerpt("backend_fastapi/routers/introduce.py", 777, 815))
out.append("\n## Parity samples\n\n")
for x in samples: out.append(fence(x) + "\n")
out.append("## Validation boundary\n\n")
for x in boundary: out.append(fence(x) + "\n")
out.append("## Appendix — the generator, verbatim\n\nRun from `HAL9000/backend_fastapi` with "
           "`PYTHONPATH=. /Users/davewascha/Workspaces/HAL9000/.venv/bin/python <this script> > <out>`.\n\n```python\n"
           + Path(__file__).read_text() + "```\n")
sys.stdout.write("".join(out))
```
