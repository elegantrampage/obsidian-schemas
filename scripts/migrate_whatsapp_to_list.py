#!/usr/bin/env python3
"""WI-032 — migrate `Person.whatsapp` from the scalar shape onto the list shape.

Dry run, then a gated write, then a READBACK that proves no identifier moved.

**Home.** `scripts/`, beside `lint_vault.py`, for two measured reasons rather than
convention. `scripts/` is swept by `tests/test_write_routing.py`'s single-homed
filesystem-mutation wall, so a `write_text` here is RED standing; and it is
OUTSIDE `tests/test_write_target_seam_wall.py`'s universe, so a one-off vault
walker does not have to satisfy WI-029's loaded-entity provenance seam, which is
a contract about repositories and not about a migration reading bytes.

**No `DEFAULT_VAULT` and no env fallback.** `--vault` is `required=True` and this
module names `OBSIDIAN_VAULT_PATH` nowhere. That is not caution:
`tests/test_vault_path_required.py` scans every `.py` under `obsidian_schemas/`
and `scripts/` for `expanduser` / `Path.home()` / `/Users/` and asserts zero live
matches, and WI-031 closed the library's own env-fallback route. A migration that
can be pointed at the live vault by OMISSION is the one shape this repo has
already decided against twice.

**THE ACTION TABLE, keyed on `classify_field` and on nothing else.** For each
`type: person` note the run reads RAW frontmatter — never a model, because
`parse_to_model` would coerce the field before the run could see its stored shape:

    key ABSENT                        -> no write (outside the partition's domain)
    "", whitespace, null, or already []-> SHAPE-ONLY: write []
    already a list, every member A/B  -> no write (already migrated)
    scalar, member A or B             -> CONVERT: write [<member verbatim>]
    any member C, repair ENABLED      -> REPAIR then convert
    any member C, repair DISABLED     -> no write, reported (residual R)
    any member D or E                 -> no write, reported, byte-identical (R)

**THE RUN NEVER CLEARS A VALUE TO MAKE A NOTE CONVERT.** Emptying a class-D value
would move it out of the residual and reach zero-outside-R trivially, by deleting
the population this item exists to preserve. Clearing is a repair somebody ASKS
for through a delta arm, never something the run decides.

**THE WRITE IS ONE CALL**, `writer.update_frontmatter_field`, which already takes
`vault_io.note_lock`, reads inside the lock, gates the delta with the note's own
parsed `type:` and writes under a stamp precondition. So this module introduces NO
new frontmatter write arm and adds no direct `write_text`. A `NameGateRefusal` out
of that call on a note the plan classified as convertible is a LOUD failure that
aborts the run — never caught and counted.

The writer MODULE is imported and the call resolved at CALL TIME, never
`from obsidian_schemas.writer import update_frontmatter_field`: the re-run
assertion's oracle is a call count installed on the module attribute, and the bare
function binding would make that counter blind.

**THE READBACK IS A RE-READ.** `readback_migration` opens a FRESH
`PersonRepository` over the vault path itself, so the oracle is the note BYTES
parsed by a load that did not exist before the write. A readback computed through
the migrating process's own repository compares a private replica with itself and
is green by construction whatever the bytes say.

**THE RECONCILIATION IDENTITY IS OVER THE TRIPLE.** Each phase reports
`(scalar_outside_residual, migrated, residual)` and `_cli` compares them PART FOR
PART, naming the part that disagreed. One number agreeing is not the check.

Usage:

    python scripts/migrate_whatsapp_to_list.py --vault /path/to/vault
    python scripts/migrate_whatsapp_to_list.py --vault /path/to/vault --apply
    python scripts/migrate_whatsapp_to_list.py --vault /path/to/vault --apply --no-repair
"""

import argparse
import sys
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from obsidian_schemas import writer
from obsidian_schemas.errors import FrontmatterParseError
from obsidian_schemas.identifier import IdentifierError, WhatsAppJID
from obsidian_schemas.parser import parse_frontmatter
from obsidian_schemas.phone_normalization import normalize_phone, phones_match
from obsidian_schemas.repositories.person import PersonRepository

#: WI-032 M1. The dry run's repair disclosure. Section order is the mitigation:
#: the uncorroborated members are printed FIRST because there is exactly one of
#: them on the live corpus and it is the row the census asked a human to read.
UNCORROBORATED_HEADER = "UNCORROBORATED — digits not in this note's own phones[]:"
CORROBORATED_HEADER = "CORROBORATED — digits already in this note's own phones[]:"
NO_REPAIR_BANNER = "NO REPAIR (--no-repair): these notes are NOT rewritten and join the residual R:"

#: The STORABLE classes. Every other class is refused by the write door, which is
#: what makes the residual terminally scalar BY DESIGN.
STORABLE_CLASSES = ("A", "B")

#: The three parts of the TERMINAL-STATE PARTITION, in the order every phase
#: reports them and `_cli` compares them. Named rather than positional so the
#: non-zero exit message can say WHICH part disagreed.
PART_NAMES = ("scalar_outside_residual", "migrated", "residual")

SKIP_DIRS = {".obsidian", "Templates", "src", ".trash", "_quarantine",
             "_merged_dupes"}


# ---------------------------------------------------------------------------
# The M4 render helper — read-only, and the reason "one line per record" is a
# property of the FORMATTER rather than of the data.
# ---------------------------------------------------------------------------

def _escape_for_one_line(raw: str) -> str:
    """Render `raw` so it cannot break a line or hide inside one.

    The backslash FIRST, so the rendering is unambiguous; then every character
    whose `unicodedata.category` is `Cc`, `Cf`, `Zl` or `Zp` as a visible
    `\\xNN`/`\\uNNNN` escape. Every other character passes through unchanged.

    The rule is stated over the CLASS that generates the hazard and not over the
    four characters the finding named: `str.splitlines()` breaks on U+000B,
    U+000C, U+001C–U+001E and U+0085 NEL as well as on `\\n` and `\\r`, and on
    U+2028 / U+2029, so a four-character escape still reflows the artifact. The
    implementation is the CATEGORY test ALONE because that set CONTAINS the break
    set — the check DERIVES the break set by calling `str.splitlines()` over the
    codepoint space and proves the containment on the running interpreter rather
    than assuming it.

    Why a stored value can carry one at all: `WhatsAppJID.parse` normalizes with
    `str(raw).strip().lower()` and `.strip()` removes only the ENDS, so an
    interior newline survives into `.jid`; `normalize_phone` then splits at the
    first `@` and deletes every non-digit, so such a value is phone-bearing,
    domain-less and therefore class C — the exact population this disclosure
    prints and the repair rewrites.
    """
    out = []
    for char in str(raw):
        if char == "\\":
            out.append("\\\\")
            continue
        if unicodedata.category(char) in ("Cc", "Cf", "Zl", "Zp"):
            cp = ord(char)
            out.append(f"\\x{cp:02x}" if cp < 0x100 else f"\\u{cp:04x}")
            continue
        out.append(char)
    return "".join(out)


# ---------------------------------------------------------------------------
# The plan, the result, the readback
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class RepairDisclosure:
    """One class-C note's `(stored value -> proposed JID)` pair, plus the only
    independent witness the corpus offers that the digits are the right number.

    `corroborated` is computed by `phones_match` over that note's OWN raw
    `phones[]`. The key preservation AC-5 leg (d) asserts is TRUE BY CONSTRUCTION
    of the repair spelling — both keys derive from the same `normalize_phone`
    output — so it is not evidence the digits belong to this person.
    """
    path: Path
    stored_value: str
    proposed_jid: str
    corroborated: bool


@dataclass
class NoteAction:
    """The one arm the action table took for one note."""
    path: Path
    stored: Any
    classes: Tuple[str, ...]
    action: str                   # "none" | "shape_only" | "convert" | "repair"
    new_value: Optional[list]
    part: str                     # a member of PART_NAMES, or "outside"


@dataclass
class MigrationPlan:
    vault_path: Path
    repair: bool
    actions: List[NoteAction] = field(default_factory=list)
    repairs: List[RepairDisclosure] = field(default_factory=list)

    @property
    def class_counts(self) -> dict:
        """Per-cell counts over the six-cell class table.

        The five non-empty cells are counted per VALUE and class Ø per NOTE,
        because Ø is a property of the FIELD and has no member to count. On a
        corpus where every note carries at most one value the two readings
        coincide, which is the live case.
        """
        counts = {c: 0 for c in WhatsAppJID.CLASSES}
        for action in self.actions:
            if not action.classes:
                counts[WhatsAppJID.CLASS_ABSENT] += 1
                continue
            for member_class in action.classes:
                counts[member_class] += 1
        return counts

    @property
    def triple(self) -> Tuple[int, int, int]:
        """The PREDICTED terminal state, under THIS plan's `repair` arm — which
        is what makes the reconciliation comparable part-for-part against the
        write's and the readback's. Under Ruling B's alternative arm class C
        joins the residual, and predicting MIGRATED for it would fail the
        identity for a reason that is a bookkeeping artefact."""
        return _triple(_effective_actions(self.actions, self.repair))


@dataclass
class MigrationResult:
    committed: int
    repaired: int
    shape_only: int
    actions: List[NoteAction] = field(default_factory=list)

    @property
    def triple(self) -> Tuple[int, int, int]:
        return _triple(self.actions)


@dataclass
class ReadbackResult:
    #: note path -> multiset (sorted tuple) of `.key` over the PARSEABLE values.
    keys_by_note: dict
    #: note path -> (parseable value count, TOTAL value count).
    counts_by_note: dict
    triple: Tuple[int, int, int]


def _effective_actions(actions, repair: bool) -> list:
    """The actions as the `repair` arm leaves them. The ONE place the alternative
    arm's re-parting is decided, so `plan.triple` and `apply_migration` cannot
    disagree about it."""
    out = []
    for action in actions:
        if action.action == "repair" and not repair:
            out.append(NoteAction(action.path, action.stored, action.classes,
                                  "none", None, PART_NAMES[2]))
            continue
        out.append(action)
    return out


def _triple(actions) -> Tuple[int, int, int]:
    """The TERMINAL-STATE PARTITION's three parts, over the notes the partition
    ranges over — every `whatsapp`-CARRYING note.

    Part 1 is notes left in the SCALAR shape OUTSIDE the residual and must be
    ZERO after a successful run. Part 2 is MIGRATED. Part 3 is the residual R.
    """
    scalar_outside = sum(1 for a in actions if a.part == PART_NAMES[0])
    migrated = sum(1 for a in actions if a.part == PART_NAMES[1])
    residual = sum(1 for a in actions if a.part == PART_NAMES[2])
    return (scalar_outside, migrated, residual)


# ---------------------------------------------------------------------------
# READ-ONLY. The dry run.
# ---------------------------------------------------------------------------

def _person_notes(vault_path: Path):
    """Every `type: person` note, by its RAW frontmatter. Never a model: the run
    has to see the STORED shape, and `parse_to_model` coerces it first."""
    for path in sorted(Path(vault_path).rglob("*.md")):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        try:
            frontmatter, _ = parse_frontmatter(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, FrontmatterParseError):
            # A note this run cannot READ is not a note it may convert, and the
            # three refusals are named rather than caught wholesale: `lint_vault`
            # is the tool that REPORTS an undecodable or unparseable note, and
            # this run leaves it byte-identical. Anything else raises and aborts
            # the run, which is the loud-fail contract.
            continue
        if frontmatter.get("type") != "person":
            continue
        yield path, frontmatter


def _repair_spelling(value) -> str:
    """The class-C repair, in ONE place so the test can call it rather than
    restate it. GUARDED by its one caller on `phone_digits` being non-empty."""
    return f"{WhatsAppJID.parse(value).phone_digits}@s.whatsapp.net"


def _corroborated(value, frontmatter) -> bool:
    """Recomputed the SAME way the census computed it, by calling `phones_match`
    over the note's own raw `phones[]` — never by re-deriving an equivalence."""
    digits = WhatsAppJID.parse(value).phone_digits
    raw_phones = frontmatter.get("phones") or []
    if isinstance(raw_phones, str):
        raw_phones = [raw_phones]
    for candidate in raw_phones:
        if not candidate or not str(candidate).strip():
            continue
        if phones_match(digits, normalize_phone(str(candidate))):
            return True
    return False


def plan_migration(vault_path) -> MigrationPlan:
    """READ-ONLY. Classify every person note and decide its one arm.

    Writes nothing, opens no repository, and leaves the tree byte-identical — a
    migration that writes during its dry run has already spent the only cheap
    chance to be wrong.
    """
    vault_path = Path(vault_path)
    plan = MigrationPlan(vault_path=vault_path, repair=True)

    for path, frontmatter in _person_notes(vault_path):
        present = "whatsapp" in frontmatter
        stored = frontmatter.get("whatsapp")
        classes = tuple(WhatsAppJID.classify_field(stored))

        if not present:
            # Nothing to convert, and OUTSIDE the partition's own domain, which
            # opens on "every `whatsapp`-carrying note".
            plan.actions.append(NoteAction(path, stored, classes, "none", None,
                                           "outside"))
            continue

        if not classes:
            # Class Ø with the key PRESENT. `""` -> `[]` is the one spelling of
            # this cell that is a write; a note with the key absent took the arm
            # above. Already `[]` needs no write and is already MIGRATED.
            if isinstance(stored, list):
                plan.actions.append(NoteAction(path, stored, classes, "none",
                                               None, PART_NAMES[1]))
            else:
                plan.actions.append(NoteAction(path, stored, classes,
                                               "shape_only", [], PART_NAMES[1]))
            continue

        refused = [c for c in classes if c not in STORABLE_CLASSES]

        if not refused:
            if isinstance(stored, list):
                plan.actions.append(NoteAction(path, stored, classes, "none",
                                               None, PART_NAMES[1]))
            else:
                plan.actions.append(NoteAction(path, stored, classes, "convert",
                                               [stored], PART_NAMES[1]))
            continue

        # At least one member the write door refuses. Only class C is repairable,
        # and only because every class-C value is phone-bearing by construction
        # once class E is carved out of it.
        if set(refused) == {"C"}:
            members = stored if isinstance(stored, list) else [stored]
            for member in members:
                parsed = WhatsAppJID.parse(member)
                if not parsed.phone_digits:
                    continue
                plan.repairs.append(RepairDisclosure(
                    path=path,
                    stored_value=str(member),
                    proposed_jid=_repair_spelling(member),
                    corroborated=_corroborated(member, frontmatter),
                ))
            # THE REPAIR IS GUARDED ON `phone_digits` BEING NON-EMPTY, and the
            # guard is not decoration: applying it to a phone-less unstorable
            # value would write `"@s.whatsapp.net"`, which `parse` then REFUSES,
            # turning a note the run was supposed to leave alone into one nothing
            # can read back.
            repaired = [
                _repair_spelling(m)
                if WhatsAppJID.classify(m) == "C" and WhatsAppJID.parse(m).phone_digits
                else m
                for m in members
            ]
            plan.actions.append(NoteAction(path, stored, classes, "repair",
                                           repaired, PART_NAMES[1]))
            continue

        # Class D or class E: reported, and left BYTE-IDENTICAL. Terminally
        # SCALAR by design — a conversion re-introduces the field and the door
        # refuses it in both shapes.
        plan.actions.append(NoteAction(path, stored, classes, "none", None,
                                        PART_NAMES[2]))

    return plan


def format_repair_disclosure(plan: MigrationPlan) -> str:
    """RETURNS (never prints) the M1 disclosure, UNCORROBORATED records first.

    Every field of every record — `path`, `stored_value` and `proposed_jid`
    alike — is rendered through `_escape_for_one_line`, so ONE PHYSICAL LINE PER
    RECORD is a guarantee of this formatter over ANY stored value instead of an
    accident of the data. Routing all three through one helper makes the
    guarantee total over the RECORD and survives a later change to the repair
    spelling that a per-field fix would not.

    Returning rather than printing is what lets the disclosure be asserted
    in-process without capturing stdout, and is why this function is read-only
    and is not a member of the containment census's mutating drives.
    """
    lines: List[str] = []
    uncorroborated = [r for r in plan.repairs if not r.corroborated]
    corroborated = [r for r in plan.repairs if r.corroborated]

    def render(record: RepairDisclosure) -> str:
        return (f"  {_escape_for_one_line(str(record.path))}: "
                f"{_escape_for_one_line(record.stored_value)} -> "
                f"{_escape_for_one_line(record.proposed_jid)}")

    if not plan.repair and plan.repairs:
        lines.append(NO_REPAIR_BANNER)
    if uncorroborated:
        lines.append(UNCORROBORATED_HEADER)
        lines.extend(render(r) for r in uncorroborated)
    if corroborated:
        lines.append(CORROBORATED_HEADER)
        lines.extend(render(r) for r in corroborated)
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# The ONE mutating entry point.
# ---------------------------------------------------------------------------

def apply_migration(vault_path, plan: MigrationPlan, *,
                    repair: bool = True) -> MigrationResult:
    """Commit the plan's writes through the ONE door.

    `repair=False` is Ruling B's alternative arm made EXECUTABLE rather than
    hypothetical: class C is left untouched and JOINS the residual, so the
    scalar count the live bracket reports changes with the ruling.
    """
    vault_path = Path(vault_path)
    committed = 0
    repaired = 0
    shape_only = 0
    # Declining the repair leaves those notes scalar AND unsaveable through the
    # whole-record arms until hand repair, which is the number Dave is entitled
    # to when he rules. The re-parting is `_effective_actions`', so this frame and
    # `plan.triple` cannot disagree about it.
    actions: List[NoteAction] = _effective_actions(plan.actions, repair)

    for action in actions:
        if action.action == "none":
            continue
        # THE WRITE IS ONE CALL, and the writer MODULE is what carries it — the
        # attribute lookup happens at call time, which is what makes the re-run
        # assertion's call counter reachable at all.
        writer.update_frontmatter_field(action.path, "whatsapp", action.new_value)
        committed += 1
        if action.action == "repair":
            repaired += 1
        elif action.action == "shape_only":
            shape_only += 1

    return MigrationResult(committed=committed, repaired=repaired,
                           shape_only=shape_only, actions=actions)


# ---------------------------------------------------------------------------
# READ-ONLY. The readback, which is a RE-READ.
# ---------------------------------------------------------------------------

def readback_migration(vault_path, plan: MigrationPlan) -> ReadbackResult:
    """Re-READ the note bytes through a repository that did not exist before the
    write, and report the per-note key multisets and the two per-note counts.

    Constructing the repository INSIDE this module rather than in its test is
    also what lets the test module satisfy the containment wall's
    zero-construction clause.
    """
    vault_path = Path(vault_path)
    repo = PersonRepository(str(vault_path))
    repo._ensure_loaded()

    keys_by_note = {}
    counts_by_note = {}
    actions: List[NoteAction] = []

    for path, frontmatter in _person_notes(vault_path):
        stored = frontmatter.get("whatsapp")
        members = WhatsAppJID.classify_field(stored)
        raw_members = (list(stored) if isinstance(stored, (list, tuple))
                       else ([] if not members else [stored]))
        keys = []
        for member in raw_members:
            # The parseable/unparseable split is itself computed by CALLING
            # `parse` and catching, never from a hand-kept list — so a class-D
            # value contributes no key to either side instead of raising.
            try:
                keys.append(WhatsAppJID.parse(member).key)
            except IdentifierError:
                continue
        keys_by_note[path] = tuple(sorted(keys))
        counts_by_note[path] = (len(keys), len(raw_members))

        present = "whatsapp" in frontmatter
        if not present:
            part = "outside"
        elif not members:
            part = PART_NAMES[1] if isinstance(stored, list) else PART_NAMES[0]
        elif all(c in STORABLE_CLASSES for c in members):
            part = PART_NAMES[1] if isinstance(stored, list) else PART_NAMES[0]
        else:
            part = PART_NAMES[2]
        actions.append(NoteAction(path, stored, tuple(members), "none", None, part))

    return ReadbackResult(keys_by_note=keys_by_note,
                          counts_by_note=counts_by_note,
                          triple=_triple(actions))


# ---------------------------------------------------------------------------
# The CLI. Verified by the conductor in the live bracket, which is where a CLI's
# real audience is anyway.
# ---------------------------------------------------------------------------

def _cli(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Migrate Person.whatsapp from the scalar shape to the list "
                    "shape (WI-032).")
    parser.add_argument("--vault", required=True,
                        help="the vault to walk — REQUIRED, with no default and "
                             "no environment fallback")
    parser.add_argument("--apply", action="store_true",
                        help="commit the writes; absent, this is a dry run")
    parser.add_argument("--no-repair", action="store_true",
                        help="leave class C untouched (Ruling B's alternative "
                             "arm); those notes join the residual R")
    args = parser.parse_args(argv)

    root = Path(args.vault)
    if not root.is_dir():
        print(f"--vault is not an existing directory: {root}", file=sys.stderr)
        return 2

    repair = not args.no_repair
    plan = plan_migration(root)
    plan.repair = repair

    print("per-cell counts over the six-cell class table:")
    for member_class, count in plan.class_counts.items():
        print(f"  class {member_class}: {count}")

    # The disclosure prints on EVERY run, BEFORE any write — under `--apply` and
    # under `--no-repair` alike, so the conductor sees the same pairs either way
    # and Ruling B's alternative arm is readable rather than hypothetical.
    disclosure = format_repair_disclosure(plan)
    if disclosure:
        print(disclosure)

    print(f"plan triple: {dict(zip(PART_NAMES, plan.triple))}")

    if not args.apply:
        print("DRY RUN — nothing written.")
        return 0

    result = apply_migration(root, plan, repair=repair)
    print(f"committed: {result.committed} (shape-only {result.shape_only}, "
          f"repairs {result.repaired})")
    print(f"write triple: {dict(zip(PART_NAMES, result.triple))}")

    readback = readback_migration(root, plan)
    print(f"readback triple: {dict(zip(PART_NAMES, readback.triple))}")

    # PART FOR PART, naming the part that disagreed. One number agreeing is not
    # the check.
    for index, name in enumerate(PART_NAMES):
        values = (plan.triple[index], result.triple[index], readback.triple[index])
        if len(set(values)) != 1:
            print(f"RECONCILIATION FAILED on part `{name}`: "
                  f"plan={values[0]} write={values[1]} readback={values[2]}",
                  file=sys.stderr)
            return 1
    print("reconciled part-for-part over the three-part partition.")
    return 0


if __name__ == "__main__":       # pragma: no cover — exercised in the live bracket
    sys.exit(_cli())
