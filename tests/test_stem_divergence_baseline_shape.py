"""WI-029, AC-4 — the live repair is BRACKETED and the bracket is in the tree.

The ENTRY half of that bracket is a conductor-committed artifact measured off
Dave's live vault (`docs/stem-divergence-live-baseline.md`). This module reads
the committed bytes and grades their SHAPE and INTERNAL CONSISTENCY. It executes
NOTHING against any vault — it constructs no repository, imports no repository,
and opens exactly one file, the artifact, plus whatever `Path.exists()` the
privacy rule needs to resolve a repo-relative token.

Two checks, and the readers are shared BY CONSTRUCTION rather than by
convention: `test_the_stem_divergence_live_baseline_is_committed_and_shaped`
drives them over the live artifact, and
`test_the_baseline_readers_reach_their_claimed_shapes` drives the SAME functions
over planted text. A reader re-implemented for one of them would be a second
oracle, and the two would drift.

**Why the battery exists at all.** Both of this module's live assertions are
"zero offenders" shapes — no inconsistent direction row, no leaking `.md` token
— and a zero-offender oracle is satisfied identically by a reader that resolves
every claimed shape and by one that resolves almost none (WI-235). So every
shape the live half claims to catch is planted and driven through the same
predicate, and every shape it claims to EXEMPT is planted too, so the rule
cannot pass by matching everything or by matching nothing.
"""

# FIRST, ahead of every package import: the conveyor may run this module's checks
# under an interpreter that is not this project's, where the imports below cannot
# resolve. A no-op under the floor command and under CI (WI-021).
from tests.ac_interpreter import ensure_project_interpreter

ensure_project_interpreter(__file__)

import re  # noqa: E402
from pathlib import Path  # noqa: E402

# IMPORTED and never re-spelled: a module that types `"/Users/"` to assert
# nothing contains `"/Users/"` is its own counterexample.
from tests.test_vault_path_required import FORBIDDEN_DEFAULT_PATTERNS  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
ARTIFACT = REPO_ROOT / "docs" / "stem-divergence-live-baseline.md"

# ---------------------------------------------------------------------------
# The vocabularies the artifact declares FOR ITSELF, at
# `docs/stem-divergence-live-baseline.md:155-156`. Re-stated here as the reader's
# oracle, which is the only place they are enforced.
# ---------------------------------------------------------------------------

DIRECTION_TOKENS = frozenset({"RENAME", "MERGE", "FIELD-REPAIR"})
OCCUPANCY_TOKENS = frozenset({"no", "same-file", "different-note"})

#: The ONE (b3) value that means the write door WROTE the note's stored name.
#: Every other token is read as a refusal — deliberately FAIL-CLOSED, so a typo
#: or a new spelling makes a `RENAME` row RAISE rather than silently pass the
#: consistency rule this column exists to feed. The artifact's §0 script emits
#: `WRITTEN`, `REFUSED:<pattern>` or `OTHER:<ExcName>`; only the first is a write.
GATE_WRITTEN_TOKEN = "WRITTEN"

#: The declared template literal, exempt from the `.md` filename rule because it
#: names no note — it is the filename SHAPE the library mints.
TEMPLATE_LITERAL = "@{name}.md"

#: Design §4a's character class, and the `*` in it is load-bearing: a class
#: without it captures `.md` with the `*` left OUTSIDE the token, and the glob
#: exemption below becomes unreachable.
MD_TOKEN_RE = re.compile(r"[\w@{}*./+-]+\.md")

# ---------------------------------------------------------------------------
# §1's figures. The two the criterion names are parsed as integers; the rest are
# asserted PRESENT BY LABEL ONLY. Neither figure is compared to a VALUE: the
# population is LIVE, is re-measured at exit, and an equality written today is
# stale by build time.
# ---------------------------------------------------------------------------

ENTRY_INTEGER_LABELS = (
    "divergent live person notes",
    "len(PersonRepository($VAULT).conflicts)",
)

ENTRY_PRESENT_LABELS = (
    "person notes loaded",
    "divergent rows the WRITE DOOR refuses",
    "sentinel-exempt",
    "destination `@{name}.md` occupied",
    "incoming wikilinks naming an old stem",
    "`attendees:`-carrying notes naming an old stem",
    "`company:` values naming an old stem",
    "booked repair: `type: person` note with a non-`@` (book-titled) stem",
    "booked repair: frontmatter present, no `type:`",
    "booked repair: frontmatter that does not parse",
)

BOOKED_REPAIR_LABELS = (
    "book-titled, non-`@` stem",
    "frontmatter present, no `type:`",
    "frontmatter that does not parse",
)

ATTESTATION_FIGURE_LABELS = (
    "divergent live person notes",
    "len(PersonRepository($VAULT).conflicts)",
    "rows gate-refused",
    "destination occupied by a different note",
    "post-build HEAD",
)

ATTESTATION_COMMANDS = (
    "the §0 script",
    'scripts/lint_vault.py --vault "$VAULT" --report',
)


# ---------------------------------------------------------------------------
# The readers. Module-level and shared by both checks.
# ---------------------------------------------------------------------------


def section(text, number):
    """The body of the artifact's `## <number>.` section, up to the next `## `.

    Every table reader below is scoped to ONE section for a stated reason: §0
    carries a pipe-bearing python script and its verbatim stdout, and a reader
    that saw those lines would be parsing shell output as table rows. Scoping is
    what removed the need for fence detection anywhere in this module.
    """
    lines = text.splitlines()
    opener = f"## {number}."
    start = None
    for i, line in enumerate(lines):
        if line.startswith(opener):
            start = i + 1
            break
    if start is None:
        raise ValueError(f"the artifact carries no '{opener}' section")
    end = len(lines)
    for i in range(start, len(lines)):
        if lines[i].startswith("## "):
            end = i
            break
    return "\n".join(lines[start:end])


def table_rows(section_text):
    """Every pipe-delimited row of a section, as a list of stripped cells.

    Header and the `|---|` separator are returned along with the data rows —
    callers that need the header read it, and `read_direction_rows` below is the
    one that does.
    """
    rows = []
    for line in section_text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        rows.append(cells)
    return rows


def leading_int(cell):
    """The integer a §1 entry cell OPENS with, or None.

    LEADING extraction and never `int(cell)`: §1's other rows legitimately read
    `0 of 8` and `1 of 8 by a DIFFERENT note (row 8); 1 of 8 by the SAME file …`,
    and a whole-cell numeric rule would be RED against a correct artifact.
    Thousands separators are accepted because the artifact writes `1,171`.
    """
    match = re.match(r"\s*(\d[\d,]*)", cell)
    if match is None:
        return None
    return int(match.group(1).replace(",", ""))


def read_entry_figures(section_text):
    """{label cell: value cell} for every two-column row of §1."""
    figures = {}
    for cells in table_rows(section_text):
        if len(cells) != 2:
            continue
        if set(cells[0]) <= {"-", ":"} or cells[0] == "figure":
            continue
        figures[cells[0]] = cells[1]
    return figures


def find_labelled(figures, label):
    """The value cell of the one row whose label CONTAINS `label`.

    Raises when zero or more than one row matches: a label that stopped matching
    (the artifact was reworded) and a label that matches two rows are both
    reader faults, and neither may degrade into "figure absent, assertion
    skipped".
    """
    hits = [v for k, v in figures.items() if label in k]
    if len(hits) != 1:
        raise ValueError(
            f"expected exactly one §1 row whose label contains {label!r}; "
            f"found {len(hits)}")
    return hits[0]


#: The §2 columns this reader requires, keyed by the marker its HEADER cell
#: carries. `direction` is matched on the bare word because its header is
#: literally `direction`; the rest are the artifact's own `(bN)` / `(c)` tags.
DIRECTION_COLUMNS = {
    "b1": "(b1)",
    "b2": "(b2)",
    "b3": "(b3)",
    "c": "(c)",
    "direction": "direction",
}


def read_direction_rows(section_text):
    """§2's per-note direction table, as one dict per data row.

    RAISES when the header does not carry all five required columns, and when a
    data row has a different cell count from the header — a row missing a column
    is the artifact defect this reader exists to catch, never a row to read
    leniently and grade anyway.
    """
    rows = table_rows(section_text)
    header = None
    body = []
    for cells in rows:
        if header is None:
            header = cells
            continue
        if cells and set("".join(cells)) <= {"-", ":"}:
            continue
        body.append(cells)
    if header is None:
        raise ValueError("§2 carries no table at all")

    index = {}
    for role, marker in DIRECTION_COLUMNS.items():
        matches = [i for i, cell in enumerate(header) if marker in cell]
        if len(matches) != 1:
            raise ValueError(
                f"§2's header must carry exactly one {marker!r} column; "
                f"found {len(matches)} in {header!r}")
        index[role] = matches[0]

    parsed = []
    for cells in body:
        if len(cells) != len(header):
            raise ValueError(
                f"§2 row has {len(cells)} cells against a {len(header)}-cell "
                f"header — a row is missing a column: {cells!r}")
        parsed.append({role: cells[i] for role, i in index.items()})
    if not parsed:
        raise ValueError("§2's direction table carries no data rows")
    return parsed


def leading_token(cell):
    """The cell's first whitespace-delimited token, or '' for an empty cell."""
    parts = cell.split()
    return parts[0] if parts else ""


def is_gate_refused(row):
    """Did the WRITE DOOR refuse this row's stored name?

    Fail-closed: anything that is not exactly `WRITTEN` is a refusal. The
    consistency rule below turns a refusal into a REFUSED `rename`, so reading an
    unrecognised token as "written" would be the one direction that fails open.
    """
    return leading_token(row["b3"]) != GATE_WRITTEN_TOKEN


def direction_violations(rows):
    """Every way §2 can be internally contradictory, as a list of messages.

    The two rules are AC-4's, and both are about a `rename` the repair run could
    not actually perform:

    1. A row cannot resolve to `RENAME` while its (b3) column declares the door
       refuses its stored name — `@{name}.md` is then a filename no write path in
       the package could ever mint.
    2. A row cannot resolve to `RENAME` onto a destination occupied by a
       DIFFERENT note. A `same-file` destination is explicitly NOT occupied for
       this rule: it is the case-only divergence (row 3 live), and `RENAME` is
       the one direction that repairs it.
    """
    problems = []
    for position, row in enumerate(rows, start=1):
        direction = leading_token(row["direction"]).upper()
        if direction not in DIRECTION_TOKENS:
            problems.append(
                f"row {position}: direction {row['direction']!r} opens with "
                f"{direction!r}, which is not one of {sorted(DIRECTION_TOKENS)}")
            continue
        occupancy = leading_token(row["b2"])
        if occupancy not in OCCUPANCY_TOKENS:
            problems.append(
                f"row {position}: (b2) {row['b2']!r} opens with {occupancy!r}, "
                f"which is not one of {sorted(OCCUPANCY_TOKENS)}")
            continue
        if direction != "RENAME":
            continue
        if is_gate_refused(row):
            problems.append(
                f"row {position}: resolves to RENAME while (b3) declares a door "
                f"refusal ({row['b3']!r}) — the stored name is one the package "
                f"can never write, so a rename to it is unperformable")
        if occupancy == "different-note":
            problems.append(
                f"row {position}: resolves to RENAME onto a destination occupied "
                f"by a DIFFERENT note — the direction is MERGE")
    return problems


def md_tokens(text):
    """Every `.md` token in `text`, anywhere — inside a fence exactly as much as
    outside one. The exemption is a TOKEN CLASS and never a REGION (M5): a fenced
    block is precisely where the exit attestation's pasted output lands, and §5's
    second re-run command reports issues PER PATH and so names note filenames by
    construction."""
    return MD_TOKEN_RE.findall(text)


def privacy_offenders(text, root=REPO_ROOT):
    """Every token in `text` that leaks the artifact's privacy wall.

    WHOLE-FILE in both halves. A `.md` token is clean only if it resolves to a
    path that EXISTS in `root`, or is the declared template literal, or contains
    a `*` and is therefore a glob rather than a filename.

    A leaked filename carrying a space is captured as its TRAILING segment
    (`@Someone Real.md` yields `Real.md`), which resolves to nothing in this repo
    and so still FIRES. The wall catches it; it merely names a shorter token. The
    character class is NOT widened to spaces chasing a prettier token, because
    that would start swallowing prose.
    """
    offenders = []
    for pattern in FORBIDDEN_DEFAULT_PATTERNS:
        if pattern in text:
            offenders.append(pattern)
    for token in md_tokens(text):
        if "*" in token:
            continue
        if token == TEMPLATE_LITERAL:
            continue
        if (root / token).exists():
            continue
        offenders.append(token)
    return offenders


# ---------------------------------------------------------------------------
# AC-4's check — the committed artifact, read
# ---------------------------------------------------------------------------


def test_the_stem_divergence_live_baseline_is_committed_and_shaped():
    """AC-4. The entry half of the bracket is in the tree and is shaped."""
    assert ARTIFACT.exists(), (
        f"AC-4's entry artifact is not in the tree: {ARTIFACT}")
    text = ARTIFACT.read_text(encoding="utf-8")

    # ---- §1: the two entry figures parse; every other row is present --------
    entry = read_entry_figures(section(text, 1))
    for label in ENTRY_INTEGER_LABELS:
        cell = find_labelled(entry, label)
        value = leading_int(cell)
        assert value is not None, (
            f"§1's {label!r} row must OPEN with an integer; cell reads {cell!r}")
        # Deliberately NOT compared to a value: the population is LIVE and is
        # re-measured at exit, so an equality written today is stale by build
        # time. The criterion asks that the figure is PRESENT and NUMERIC.
    for label in ENTRY_PRESENT_LABELS:
        find_labelled(entry, label)

    # ---- §2: the direction table's columns, vocabularies and consistency ----
    rows = read_direction_rows(section(text, 2))
    problems = direction_violations(rows)
    assert not problems, (
        "§2's direction table is internally contradictory:\n  "
        + "\n  ".join(problems))

    # ---- §4 and §5: the booked repairs and the named attestation section ----
    booked = section(text, 4)
    for label in BOOKED_REPAIR_LABELS:
        assert label in booked, (
            f"§4 must book the {label!r} repair with its entry count")
    attestation = section(text, 5)
    for label in ATTESTATION_FIGURE_LABELS:
        assert label in attestation, (
            f"§5's attestation table must name the {label!r} figure")
    for command in ATTESTATION_COMMANDS:
        assert command in attestation, (
            f"§5 must carry the re-run command {command!r} verbatim")

    # ---- M5: the privacy wall, WHOLE-FILE, both halves ----------------------
    offenders = privacy_offenders(text)
    assert not offenders, (
        "the committed baseline leaks the privacy wall: "
        f"{sorted(set(offenders))}")


# ---------------------------------------------------------------------------
# The reader battery — every claimed shape driven through the SAME readers
# ---------------------------------------------------------------------------

_HEADER = ("| row | shape | (b1) correct side | (b2) dest occupied | "
           "(b3) door | (c) refs in | direction |")
_RULE = "|---|---|---|---|---|---|---|"


def _planted_section(*rows):
    """A §2-shaped table built from cell tuples the test itself wrote."""
    lines = [_HEADER, _RULE]
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    return "\n".join(lines)


def _row(b2="no", b3="WRITTEN", direction="RENAME", number="1"):
    return (number, "some shape", "name", b2, b3, "0", direction)


def test_the_baseline_readers_reach_their_claimed_shapes():
    """WI-235. Both live assertions are zero-offender oracles, so every shape
    they claim to catch and every shape they claim to EXEMPT is planted here and
    driven through the SAME readers the live check calls."""

    # ---- the direction reader, both ways -----------------------------------

    # ACCEPTED: a gate-REFUSED row resolving to MERGE. The refusal makes a rename
    # unperformable; it says nothing about a merge.
    accepted_merge = read_direction_rows(_planted_section(
        _row(b3="REFUSED:path_hostile_char", direction="MERGE — fold it in")))
    assert direction_violations(accepted_merge) == [], (
        "a gate-refused row resolving to MERGE is legal and must not fire")

    # REFUSED: a gate-refused row resolving to RENAME.
    refused_rename = read_direction_rows(_planted_section(
        _row(b3="REFUSED:calendar_prefix", direction="RENAME")))
    assert direction_violations(refused_rename), (
        "a gate-refused row resolving to RENAME must fire — the stored name is "
        "one no write path in the package can mint")

    # REFUSED: an occupied-by-a-DIFFERENT-note row resolving to RENAME.
    occupied_rename = read_direction_rows(_planted_section(
        _row(b2="different-note", direction="RENAME")))
    assert direction_violations(occupied_rename), (
        "a RENAME onto a destination occupied by a different note must fire — "
        "the direction is MERGE")

    # ACCEPTED: a `same-file` row resolving to RENAME. This is the case-only
    # divergence, and RENAME is the one direction that repairs it — the arm that
    # fails a reader treating every non-`no` occupancy as occupied.
    same_file_rename = read_direction_rows(_planted_section(
        _row(b2="same-file — resolves to THIS note", direction="RENAME — case")))
    assert direction_violations(same_file_rename) == [], (
        "a `same-file` destination is NOT occupied for this rule and RENAME is "
        "its correct direction")

    # REFUSED, by the READER rather than by the consistency rule: a row missing
    # a column. It must RAISE rather than be graded leniently.
    short_row = "\n".join([
        _HEADER, _RULE, "| 1 | some shape | name | no | WRITTEN | RENAME |"])
    try:
        read_direction_rows(short_row)
    except ValueError:
        pass
    else:
        raise AssertionError(
            "a §2 row missing a column must RAISE out of read_direction_rows")

    # And an unrecognised direction token is caught rather than ignored — the
    # arm that fails a reader whose vocabulary check is a no-op.
    assert direction_violations(read_direction_rows(_planted_section(
        _row(direction="RELOCATE")))), (
        "a direction outside the declared vocabulary must fire")

    # ---- the leading-integer reader ----------------------------------------
    # The shapes §1 legitimately carries, which is why the rule is LEADING and
    # not `int(cell)`.
    assert leading_int("8") == 8
    assert leading_int("0 of 8") == 0
    assert leading_int("1,171") == 1171
    assert leading_int("1 of 8 by a DIFFERENT note (row 8); 1 of 8 by the "
                       "SAME file") == 1
    assert leading_int("none recorded") is None

    # ---- the privacy scan, through the SAME token function -----------------
    # A repo-relative path the test itself confirmed exists, so the ACCEPTED arm
    # below is not asserting against a file that quietly went away.
    existing = "docs/stem-divergence-live-baseline.md"
    assert (REPO_ROOT / existing).exists(), (
        f"the battery's own control path must exist: {existing}")

    # MUST FIRE: a bare note filename on a prose line.
    assert privacy_offenders("the note at @Someone Real.md is divergent"), (
        "a leaked note filename on a prose line must fire")

    # MUST FIRE: the SAME filename INSIDE a fenced code block. This is the M5
    # arm and the one the earlier REGION form let through — a fence is precisely
    # where the exit attestation's pasted `--report` output lands.
    fenced_leak = "\n".join([
        "some prose", "```", "ERROR @Someone Real.md stem_name_divergence",
        "```", "more prose"])
    assert privacy_offenders(fenced_leak), (
        "a leaked note filename INSIDE a fence must fire exactly as much as one "
        "outside it — the exemption is a TOKEN CLASS, never a REGION")

    # MUST NOT FIRE: a `*.md` glob inside a fence — the false RED the region
    # exclusion was reaching for.
    glob_in_fence = "\n".join(["```", "files = sorted(V.rglob('*.md'))", "```"])
    assert privacy_offenders(glob_in_fence) == [], (
        "a glob is not a filename and must not fire, fenced or not")
    assert "*.md" in md_tokens(glob_in_fence), (
        "the tokenizer's character class must INCLUDE `*`, or the glob "
        "exemption is unreachable and this arm passes vacuously")

    # MUST NOT FIRE: the declared template literal.
    assert privacy_offenders(f"the library mints {TEMPLATE_LITERAL}") == [], (
        "the declared template literal names no note and must not fire")

    # MUST NOT FIRE: a repo-relative path to a file that exists.
    assert privacy_offenders(f"see {existing} for the entry figures") == [], (
        "a repo-relative path to an existing file must not fire")

    # MUST FIRE: the absolute-path half, driven through the same function.
    for pattern in FORBIDDEN_DEFAULT_PATTERNS:
        assert privacy_offenders(f"a line containing {pattern} somewhere"), (
            f"the absolute-path half must fire on {pattern!r}")
