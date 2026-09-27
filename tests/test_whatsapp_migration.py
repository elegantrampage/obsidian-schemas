"""WI-032 — the migration, its containment wall, its wall memberships, and the
live bracket's shape.

Five checks:

* `test_every_whatsapp_migration_drive_is_confined_to_a_temp_vault` — Task 11.
  DEFINED FIRST so an ordinary floor run fires it ahead of every driving check.
  An ordering COURTESY and not a guarantee; the guarantee is the runtime door plus
  the clauses that close the routes around it.
* `test_whatsapp_migration_dry_run_then_write_then_readback` — AC-5, plus the
  RE-RUN leg the retry remedy rests on.
* `test_whatsapp_dry_run_discloses_each_class_c_repair_pair` — M1 and M4. M4 rides
  the SAME check because the escape is what makes that check's one-line-per-record
  oracle TOTAL rather than clean-plant-only.
* `test_whatsapp_wall_membership_is_closed_by_running_each_walls_predicate` —
  Task 12. RUNS each wall's own predicate over this item's final text rather than
  reasoning about which shapes match.
* `test_wi032_live_baseline_row_shape_and_redaction_wall` — M2 and M3.

**THE CONTAINMENT DOOR, and why the wall is the first check in the file.** This
module drives `scripts/migrate_whatsapp_to_list.py`'s ONE mutating entry point,
and a migration pointed at the live vault is irreversible. So this module ships
WI-026/WI-031's wall, in all of its clauses except ONE sub-assertion that is
DECLARED rather than dropped: WI-029's own wall asserts all THREE
`live_path_names` token shapes inside its door, reading `lint_vault.DEFAULT_VAULT`
to do it, and the migration script HAS no `DEFAULT_VAULT` by its own design rule
(`--vault` is `required=True`, no env fallback). So this door names TWO of the
three tokens and the wall asserts that set by EQUALITY plus
`not hasattr(migrate, "DEFAULT_VAULT")` — the third token's absence is a PROVEN
consequence of the script's design rather than an unexplained gap. Nothing is
narrowed: the replacement clause is strictly stronger about this module than a
silent omission.

**EVERY PLANT LITERAL IN THIS MODULE IS RESERVED-BLOCK OR SYNTHETIC.** A module
about migrating and rendering real identifiers has no business introducing one,
and the census carries none for a builder to reach for. `"+44 7739 341679"` — the
one real identifier this item names anywhere — appears in this module NOWHERE.

Nothing here reads syntax (no `ast`): that capability is single-homed in
`tests/derivations.py`, and every scan below is imported from it.
"""

# FIRST, ahead of every package import: the conveyor may run this module's checks
# under an interpreter that is not this project's, where the imports below cannot
# resolve. A no-op under the floor command and under CI (WI-021).
from tests.ac_interpreter import ensure_project_interpreter

ensure_project_interpreter(__file__)

import contextlib  # noqa: E402 — everything below runs only once the interpreter is right
import hashlib  # noqa: E402
import importlib.util  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
import re  # noqa: E402
from pathlib import Path  # noqa: E402

from obsidian_schemas import writer  # noqa: E402
from obsidian_schemas.errors import FrontmatterParseError  # noqa: E402
from obsidian_schemas.identifier import IdentifierError, WhatsAppJID  # noqa: E402
from obsidian_schemas.parser import parse_frontmatter  # noqa: E402
from obsidian_schemas.phone_normalization import (  # noqa: E402
    normalize_phone,
    phones_match,
)

from tests.derivations import (  # noqa: E402
    LIVE_PATH_ENV_KEY,
    LIVE_PATH_ENV_READ,
    PACKAGE_ROOT,
    SCRIPTS_ROOT,
    TESTS_ROOT,
    filesystem_mutation_uses,
    frontmatter_write_arms,
    functions_calling,
    gate_call_declarations,
    module_import_uses,
    modules_using_ast,
    mutating_drive_vault_args,
    phone_index_iteration_sites,
    prose_lines,
    python_files_under,
    skip_reason_literal_sites,
)
from tests.fixture_vault import materialize_vault  # noqa: E402
from tests.support import patcher, temp_dir  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
MIGRATE_PATH = SCRIPTS_ROOT / "migrate_whatsapp_to_list.py"
PERSON_MODULE = PACKAGE_ROOT / "repositories" / "person.py"

DOCS_ROOT = ROOT / "docs"
BRACKET = DOCS_ROOT / "wi-032-whatsapp-live-baseline.md"
CENSUS = DOCS_ROOT / "wi-032-whatsapp-corpus-census.md"
CONSUMER_AUDIT = DOCS_ROOT / "wi-032-consumer-audit.md"
ITEM_DOC = DOCS_ROOT / "whatsapp-jid-value-type.md"

#: The three new modules this item ships. `check_module` is driven over every
#: top-level `def test_` they DEFINE, read from their own source at test time and
#: never from a list in the plan.
NEW_TEST_MODULES = (
    TESTS_ROOT / "test_whatsapp_jid_storage.py",
    TESTS_ROOT / "test_whatsapp_write_door.py",
    TESTS_ROOT / "test_whatsapp_migration.py",
)


def _load_migrate():
    """`scripts/` is not a package, so the module is loaded from its own path —
    through the SAME shape `tests/test_lint_vault_fix_rules.py:_load_lint_vault`
    already carries, never a second loader."""
    spec = importlib.util.spec_from_file_location(
        "wi032_migrate_whatsapp", MIGRATE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


migrate = _load_migrate()

# ---------------------------------------------------------------------------
# The plants. Every literal reserved-block or synthetic.
# ---------------------------------------------------------------------------

CLASS_A_VALUE = "447700900321@s.whatsapp.net"
CLASS_D_VALUE = "n/a"
CLASS_E_VALUE = "447700900654@lid.example"

#: The two-JID note's halves, PINNED by AC-5 itself: reusing the class-A and
#: class-B literals printed elsewhere would plant a SECOND entity in the same
#: materialized copy carrying the class-A plant's `phone:` key and the round-trip
#: representative's `jid:` key — an identifier collision `_index_identifiers` does
#: not raise on, so this criterion's own readback oracle would be computed against
#: an ambiguous index and would not go red, it would just be wrong.
TWO_JID_PHONE = "447700900987@s.whatsapp.net"
TWO_JID_LID = "15555550163@lid"

#: The corpus's own members, which arrive in the materialized copy for free: the
#: person round-trip representative's storable lid (class B) and the one
#: non-representative note carrying a value that parses, is phone-bearing and the
#: door still refuses (class C).
CORPUS_CLASS_B_NOTE = "@Thrandell Ibberly.md"
CORPUS_CLASS_C_NOTE = "@Fennwick Drostane.md"
CORPUS_CLASS_C_VALUE = "447700900789@example.com"

#: The class-C plants of the M1/M4 check, one per sub-cell of the 2x2
#: {corroborated, uncorroborated} x {clean, control-bearing}. Corroboration is
#: never written beside a plant — every expectation is computed by CALLING
#: `phones_match` over the plant's own values.
C_CORROBORATED_CLEAN = "447700900201"
C_UNCORROBORATED_CLEAN = "447700900202"
C_CORROBORATED_CONTROL = "447700900204\tX"
#: The adversarial plant, whose number M4 prescribes: an interior newline
#: followed by the TEXT of `CORROBORATED_HEADER`, so an unescaped render would
#: forge a section header into the one artifact an irreversible 82-note go/no-go
#: is read against.
C_ADVERSARIAL = "447700900321\n" + migrate.CORROBORATED_HEADER

#: Every temp root this process took from `tests.support.temp_dir()`, by resolved
#: path. `_temp_vault` asserts membership rather than guessing at a path SHAPE.
_ISSUED_TEMP_ROOTS: set = set()


@contextlib.contextmanager
def _temp_root():
    """This module's ONLY source of a temp directory, and the issuing register
    `_temp_vault`'s second assertion reads."""
    with temp_dir() as root:
        resolved = Path(root).resolve()
        _ISSUED_TEMP_ROOTS.add(resolved)
        try:
            yield root
        finally:
            _ISSUED_TEMP_ROOTS.discard(resolved)


def _temp_vault(tmp):
    """The ONE door. Every mutating drive in this module takes its vault path
    from here, and the syntax half asserts that every binding of the identifier
    those drives pass is a call to this function.

    The negative assertions below are MANDATORY rather than defensive: they are
    what makes the SOURCE clause's non-empty arm true, and they are why that
    clause's exemption is scoped to this function's own body. The environment key
    is spelled HERE, as a bare literal, and nowhere else in this module — the
    wall's expected token set is IMPORTED at the assertion site rather than
    re-typed, because a second copy outside this body would redden the very clause
    the assertion states.
    """
    built = materialize_vault(Path(tmp) / "vault")
    resolved = Path(built).resolve()
    root = Path(tmp).resolve()

    assert resolved.relative_to(root) != Path("."), (
        f"the vault must be a strict descendant of {root}, not the root itself")
    assert root in _ISSUED_TEMP_ROOTS, (
        f"{root} is not a directory this process took from temp_dir()")

    # `.get(..., "")` and NEVER a subscript: the variable is UNSET in the graded
    # and CI environments, where `os.environ[...]` raises KeyError and reddens the
    # door itself rather than a drive.
    live = os.environ.get("OBSIDIAN_VAULT_PATH", "")
    if live:
        assert resolved != Path(live).resolve(), (
            "a drive was about to be pointed at the LIVE vault")
    return built


# ---------------------------------------------------------------------------
# Plant / census helpers. None of them binds the identifier `vault`.
# ---------------------------------------------------------------------------

def _note_text(name: str, *, whatsapp=None, phones=None) -> str:
    """A person note as TEXT, so the stored SHAPE is this module's choice and not
    a model's. `json.dumps` and not `yaml.safe_dump`: the latter appends a `...`
    document-end marker after a bare scalar, which would make every plant an
    unparseable note and turn each leg silently vacuous. A `str` value therefore
    lands as a YAML DOUBLE-QUOTED scalar, which is what lets the adversarial plant
    carry its `\\n` as an escape."""
    lines = ["---", "type: person", f'name: "{name}"', "aliases: []",
             "emails: []", f"phones: {json.dumps(phones or [])}"]
    if whatsapp is not None:
        lines.append(f"whatsapp: {json.dumps(whatsapp)}")
    lines += ['company: ""', 'title: ""', 'linkedin: ""', 'slack: ""',
              "roles: []", 'birthday: ""', 'created: "2026-01-04"',
              "tags: [person]", "---", "", "## Notes", ""]
    return "\n".join(lines)


def _plant(vault_dir, name: str, **kwargs) -> Path:
    """Raw text, NEVER through `write_markdown_file` or a repository save — those
    route through `gate_write`, which is exactly what refuses the members these
    checks need PLANTED."""
    path = Path(vault_dir) / f"@{name}.md"
    path.write_text(_note_text(name, **kwargs), encoding="utf-8")
    return path


def _tree_digest(vault_dir) -> str:
    """`sha256` over the sorted sequence of (relative POSIX path, file bytes),
    each field NUL-framed — the same framing `CORPUS_DIGEST` uses. A digest
    catches a re-write that REFORMATS; it cannot tell "no write" from "re-write
    the same bytes", which is why the re-run leg's discriminator is a CALL COUNT
    and this is only beside it."""
    root = Path(vault_dir)
    hasher = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        hasher.update(path.relative_to(root).as_posix().encode("utf-8"))
        hasher.update(b"\x00")
        hasher.update(path.read_bytes())
        hasher.update(b"\x00")
    return hasher.hexdigest()


def _person_frontmatter(vault_dir):
    """Every `type: person` note by its RAW frontmatter, read the way a
    pre-migration census must read it: never through a model, because the
    tolerant reader coerces the field before a census could see its stored
    shape."""
    for path in sorted(Path(vault_dir).rglob("*.md")):
        try:
            frontmatter, _ = parse_frontmatter(
                path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, FrontmatterParseError):
            continue
        if frontmatter.get("type") != "person":
            continue
        yield path, frontmatter


def _raw_members(stored, classes) -> list:
    """The stored members, in stored order, under `classify_field`'s OWN shape
    rules — so the census and the classifier cannot disagree about how many
    values a field holds."""
    if isinstance(stored, (list, tuple)):
        return list(stored)
    return [] if not classes else [stored]


def _key_census(vault_dir):
    """The PRE-migration half of AC-5 leg (c)'s oracle: per note, the multiset of
    `.key` over the PARSEABLE values, and the two counts.

    The parseable/unparseable split is computed by CALLING `parse` and catching
    `IdentifierError`, never from a hand-kept list — so a class-D value
    contributes no key to either side instead of making the oracle RAISE on its
    own mandated fixture.

    This side is computed HERE and the post-migration side comes out of
    `readback_migration`, which re-READS the note bytes through a load that did
    not exist before the write. The asymmetry is the point: a readback computed
    through the migrating process's own repository compares a private replica
    with itself and is green by construction whatever the bytes say.
    """
    keys = {}
    counts = {}
    for path, frontmatter in _person_frontmatter(vault_dir):
        stored = frontmatter.get("whatsapp")
        classes = WhatsAppJID.classify_field(stored)
        members = _raw_members(stored, classes)
        parsed_keys = []
        for member in members:
            try:
                parsed_keys.append(WhatsAppJID.parse(member).key)
            except IdentifierError:
                continue
        keys[path] = tuple(sorted(parsed_keys))
        counts[path] = (len(parsed_keys), len(members))
    return keys, counts


def _stored(path) -> object:
    frontmatter, _ = parse_frontmatter(Path(path).read_text(encoding="utf-8"))
    return frontmatter.get("whatsapp")


def _top_level_checks(module_path) -> list:
    """Every top-level `def test_` a module DEFINES, read off its own source.

    A source read and not an `ast` walk, because that capability is single-homed
    in `tests/derivations.py`; `startswith` at column zero is exactly the
    top-level test the conveyor's own `def <name>(` substring scan resolves.
    """
    found = []
    for line in Path(module_path).read_text(encoding="utf-8").splitlines():
        if line.startswith("def test_"):
            found.append(line[len("def "):].split("(", 1)[0])
    return found


# ==========================================================================
# Task 11 — the containment wall, made non-vacuous
# ==========================================================================

#: The two match-shapes the containment scan must RESOLVE, planted as source
#: text and driven through the wall's OWN predicate (WI-235): a counting wall's
#: `matches == 0` says nothing about what its matcher can see. As SYNTAX a string
#: literal is a Constant, so the planter below cannot match itself.
PLANT_COLLECTED = '''\
vault = _temp_vault(tmp)
apply_migration(vault, plan)
'''

PLANT_UNREDUCIBLE = '''\
apply_migration(build_a_path(), plan)
'''


def test_every_whatsapp_migration_drive_is_confined_to_a_temp_vault():
    """Task 11's verify. The six clauses `## Design` §8 enumerates over this
    module's own source, the two-token `live_path_names` equality that replaces
    WI-029's three-token one, the runtime door EXERCISED, and both of the scan's
    claimed match-shapes driven through the scan itself.

    Zero-arg and raising, per the check contract.
    """
    scan = mutating_drive_vault_args([Path(__file__)])

    # (i) SPELLING — every collected drive's vault argument is the identifier
    # `vault`, which is what makes the provenance clause below able to say
    # anything at all.
    wrong = sorted(t for t in scan.drives if t[2] != "vault")
    assert not wrong, (
        f"a mutating drive takes a vault argument that is not `vault`: {wrong}")

    # (ii) NON-VACUITY — the wall is VACUOUS over a new module until the census
    # names its mutating entry point AND that module actually drives it.
    assert scan.drives, "this module drives nothing — the wall would be vacuous"

    # (iii) PROVENANCE — what makes the wall a claim about where the path CAME
    # FROM rather than how it is spelled.
    strays = sorted(b for b in scan.bindings if b[3] != "_temp_vault")
    assert not strays, (
        f"`vault` is bound by something other than the one door: {strays}")

    # (iv) SOURCE — and the ONE sub-assertion WI-029's wall takes that this
    # module cannot, DECLARED rather than dropped. The script has no
    # `DEFAULT_VAULT` by `## Design` §7's own rule, so this door names TWO tokens
    # and the absence of the third is PROVEN from the script rather than left as
    # an unexplained gap in a wall. The expected set is IMPORTED, never re-typed:
    # a bare copy of the env key outside `_temp_vault`'s body would redden this
    # very clause.
    outside = sorted(n for n in scan.live_path_names if n[3] != "_temp_vault")
    assert not outside, (
        f"this module names the live vault path outside `_temp_vault`'s own "
        f"body: {outside}")
    assert scan.live_path_names, (
        "the source census resolved nothing — the door's own negative "
        "assertions must be visible to it")
    assert {n[2] for n in scan.live_path_names} == {
        LIVE_PATH_ENV_READ, LIVE_PATH_ENV_KEY,
    }, ("the door must exercise both token shapes available to it, so the "
        "clause's green is a statement about a matcher that reaches each one")
    assert not hasattr(migrate, "DEFAULT_VAULT"), (
        "the third token's absence must be a PROPERTY of the script — a "
        "`DEFAULT_VAULT` here would be a live vault reachable by OMISSION, "
        "which this repo has decided against twice")

    # (v) LIBRARY (WI-031) — zero repository constructions, because the
    # library's own env fallback runs inside every constructor, so a construction
    # reaches the live vault without spelling any token at all. This is the clause
    # `readback_migration`'s design exists to make satisfiable: the repository is
    # constructed INSIDE the script, not here.
    constructed = sorted(scan.repository_constructions)
    assert not constructed, (
        f"this module constructs an obsidian_schemas repository, which resolves "
        f"the live vault from the environment inside the library: {constructed}")

    # (vi) IMPORT — refused at the import, because a child process is graded by
    # none of the in-process clauses above.
    from tests.test_name_gate_wall import WALL_C_MODULES
    widened = WALL_C_MODULES | {"subprocess", "runpy"}
    assert not module_import_uses([Path(__file__).resolve()], widened), (
        "this module imports a subprocess-capable module and can therefore "
        "re-enter the CLI as a child process")

    # THE CLAIMED MATCH-SHAPES, driven through the scan's OWN predicate. A wall
    # that passes by matching nothing and a wall that passes by matching
    # everything are both closed by this pair.
    with _temp_root() as root:
        planted = Path(root) / "plant_collected.py"
        planted.write_text(PLANT_COLLECTED, encoding="utf-8")
        plant_scan = mutating_drive_vault_args([planted])
        assert {t[2] for t in plant_scan.drives} == {"vault"}, (
            "the scan does not COLLECT an `apply_migration(vault, …)` call — the "
            "census member would be present and the wall still vacuous")
        assert {b[3] for b in plant_scan.bindings} == {"_temp_vault"}, (
            "the scan does not resolve the planted drive's PROVENANCE")

        near_miss = Path(root) / "plant_unreducible.py"
        near_miss.write_text(PLANT_UNREDUCIBLE, encoding="utf-8")
        try:
            mutating_drive_vault_args([near_miss])
        except AssertionError:
            pass
        else:                                          # pragma: no cover
            raise AssertionError(
                "the scan did not RAISE on a drive whose vault argument it "
                "cannot reduce to a bound name — the one case that must never "
                "pass silently")

    # (1) RUNTIME — the door EXERCISED, not left to whichever drive runs first.
    with _temp_root() as root:
        vault = _temp_vault(root)
        assert (Path(vault) / CORPUS_CLASS_B_NOTE).exists(), (
            "the door must return a materialized corpus, not merely a "
            "contained path")


# ==========================================================================
# AC-5 — dry run, gated write, readback, and the RE-RUN no-op
# ==========================================================================

def _plant_every_cell(vault_dir) -> dict:
    """One note per NON-Ø cell, plus the two-JID note. Classes B and C arrive
    from the corpus edits for free and are NAMED rather than re-planted, so the
    frozen corpus is what carries them and this module carries no `s.whatsapp.net`
    literal into it."""
    return {
        "A": _plant(vault_dir, "Migrant Alpha", whatsapp=CLASS_A_VALUE),
        "B": Path(vault_dir) / CORPUS_CLASS_B_NOTE,
        "C": Path(vault_dir) / CORPUS_CLASS_C_NOTE,
        "D": _plant(vault_dir, "Migrant Delta", whatsapp=CLASS_D_VALUE),
        "E": _plant(vault_dir, "Migrant Echo", whatsapp=CLASS_E_VALUE),
        "two": _plant(vault_dir, "Migrant Duo",
                      whatsapp=[TWO_JID_PHONE, TWO_JID_LID]),
    }


def test_whatsapp_migration_dry_run_then_write_then_readback():
    """AC-5. The migration is a dry run, then a gated write, then a readback —
    and it proves no identifier moved. Zero-arg and raising, per the check
    contract."""
    # ---- leg (b), STRUCTURAL: the write goes through `vault_io` and the gate,
    # asserted about the module's CALL GRAPH rather than by observing a result.
    # The module carries no frontmatter write ARM at all (no `write_frontmatter`
    # call), reaches no filesystem-mutation capability, and its one write is the
    # ONE door — which already takes the note lock, reads inside it, gates the
    # delta with the note's own parsed `type:` and writes under a stamp
    # precondition.
    assert not [arm for arm in frontmatter_write_arms([MIGRATE_PATH])], (
        "the migration must introduce NO new frontmatter write arm — its write "
        "is `writer.update_frontmatter_field`, an arm the standing wall already "
        "routes and declares")
    assert not filesystem_mutation_uses([MIGRATE_PATH]), (
        "the migration reaches a filesystem-mutation capability directly; every "
        "write must route through `vault_io` via the writer")
    writers = {f.qualname for f in
               functions_calling([MIGRATE_PATH], "update_frontmatter_field")}
    assert writers == {"apply_migration"}, (
        f"exactly ONE frame may write, and it must be the declared mutating "
        f"entry point; found {sorted(writers)}")

    with _temp_root() as root:
        vault = _temp_vault(root)
        plants = _plant_every_cell(vault)

        # Every cell asserted NON-EMPTY, and its class computed BY CALLING the
        # classifier rather than by trusting the plant's name — a cell that lost
        # its only member must be RED rather than vacuously green.
        for cell, path in plants.items():
            classes = WhatsAppJID.classify_field(_stored(path))
            assert classes, f"cell {cell} planted no value at all"
            if cell == "two":
                assert classes == ["A", "B"], (
                    f"the two-JID note must carry a phone-bearing JID and an "
                    f"`@lid`; classified {classes}")
            else:
                assert classes == [cell], (
                    f"cell {cell} classified {classes} — the plant is not the "
                    f"member this criterion requires")
        assert _stored(plants["C"]) == CORPUS_CLASS_C_VALUE

        before_keys, before_counts = _key_census(vault)
        before_bytes = {cell: path.read_bytes() for cell, path in plants.items()}

        # ---- leg (a) DRY RUN — reports counts per cell and leaves the tree
        # byte-identical. A migration that writes during its dry run has already
        # spent the only cheap chance to be wrong.
        digest_before = _tree_digest(vault)
        plan = migrate.plan_migration(vault)
        assert _tree_digest(vault) == digest_before, (
            "the dry run WROTE — leg (a)'s whole purpose")
        counts = plan.class_counts
        assert set(counts) == set(WhatsAppJID.CLASSES), (
            f"the dry run must report one cell per declared class; got "
            f"{sorted(counts)}")
        for cell in ("A", "B", "C", "D", "E"):
            assert counts[cell] >= 1, (
                f"the dry run reports no class-{cell} value, so this run's "
                f"oracle would be vacuous for that cell")
        assert counts[WhatsAppJID.CLASS_ABSENT] >= 1, (
            "class Ø is the corpus's dominant cell and must be counted")

        # ---- the WRITE.
        result = migrate.apply_migration(vault, plan)
        assert result.committed >= 1
        assert result.repaired >= 1, (
            "the class-C repair must be COUNTED as its own class, not folded "
            "into the shape-only conversions")
        assert result.shape_only >= 1

        # ---- leg (c) READBACK ORACLE, over KEYS, computed over the PARSEABLE
        # values ONLY, and read from the note BYTES by a load that did not exist
        # before the write.
        readback = migrate.readback_migration(vault, plan)
        assert set(readback.keys_by_note) == set(before_keys), (
            "the readback's note domain differs from the pre-migration "
            "census's — a note left the population")
        for path, keys in before_keys.items():
            assert readback.keys_by_note[path] == keys, (
                f"{path.name}: the `.key` multiset MOVED — "
                f"{keys} -> {readback.keys_by_note[path]}")
            assert readback.counts_by_note[path] == before_counts[path], (
                f"{path.name}: the per-note counts moved — the first number "
                f"catches a dropped JID and the second catches a quietly "
                f"deleted unparseable value")

        # A person with TWO JIDs keeps BOTH, which is the fixture whose whole
        # purpose is this.
        assert len(readback.keys_by_note[plants["two"]]) == 2, (
            "the two-JID note lost an identifier — the one failure mode this "
            "item exists to prevent")

        # ---- leg (d) CLASS-C REPAIR, key-preserving and PHONE-BEARING-guarded.
        repaired_stored = _stored(plants["C"])
        assert repaired_stored == [
            f"{WhatsAppJID.parse(CORPUS_CLASS_C_VALUE).phone_digits}"
            f"@s.whatsapp.net"], (
            f"the class-C repair must rewrite to the canonical spelling; found "
            f"{repaired_stored!r}")
        assert (WhatsAppJID.parse(repaired_stored[0]).key
                == WhatsAppJID.parse(CORPUS_CLASS_C_VALUE).key), (
            "the repair must be KEY-PRESERVING — both keys derive from the same "
            "`normalize_phone` output")
        assert WhatsAppJID.classify(repaired_stored[0]) == "A", (
            "a repaired value must be STORABLE, or the note is unsaveable")
        # The guard asserted rather than assumed: applying the repair to a
        # phone-LESS unstorable value would write `"@s.whatsapp.net"`, which
        # `parse` then REFUSES, turning a leave-alone note into one nothing can
        # read back.
        assert plants["E"].read_bytes() == before_bytes["E"], (
            "the class-E note was rewritten by a repair-ENABLED run — the "
            "`phone_digits` guard is missing")
        assert not WhatsAppJID.parse(CLASS_E_VALUE).phone_digits

        # ---- leg (e) COUNTS RECONCILE OVER THE TERMINAL-STATE PARTITION, part
        # for part. One number agreeing is not the check.
        for index, part in enumerate(migrate.PART_NAMES):
            assert (plan.triple[index] == result.triple[index]
                    == readback.triple[index]), (
                f"part `{part}` disagrees: plan={plan.triple[index]} "
                f"write={result.triple[index]} "
                f"readback={readback.triple[index]}")
        assert readback.triple[0] == 0, (
            "part (1) — notes left in the SCALAR shape OUTSIDE the residual — "
            "must be ZERO after a successful run")
        # Part (3) IS the class-D and class-E plants under the recommended arm:
        # a conversion re-introduces the field and the door refuses it in both
        # shapes, so those notes are terminally scalar BY DESIGN.
        assert readback.triple[2] == 2, (
            f"the residual must be exactly the class-D and class-E plants; "
            f"found {readback.triple[2]}")

        # THE RUN NEVER CLEARS A VALUE TO MAKE A NOTE CONVERT — asserted PER
        # PLANT, because emptying the class-D plant would move it out of the
        # residual into part (2) and reach part (1)'s zero trivially, by deleting
        # the population this item exists to preserve.
        for cell, path in plants.items():
            after = WhatsAppJID.classify_field(_stored(path))
            assert after, f"the run CLEARED cell {cell}'s value"
        for cell in ("D", "E"):
            assert plants[cell].read_bytes() == before_bytes[cell], (
                f"the class-{cell} note must be left BYTE-IDENTICAL")

        # ---- THE RE-RUN IS A NO-OP, and it is ASSERTED rather than argued from
        # the action table's shape. It is the property `## Edge Cases`' retry
        # remedy rests on and the only remedy this design offers a conductor
        # whose live run aborted mid-vault.
        digest_after_first = _tree_digest(vault)
        second_plan = migrate.plan_migration(vault)
        calls = []
        real_write = writer.update_frontmatter_field

        def _counting_write(*args, **kwargs):            # pragma: no cover
            calls.append(args[:2])
            return real_write(*args, **kwargs)

        with patcher() as p:
            # The DISCRIMINATING oracle is a CALL COUNT: a digest cannot tell
            # "no write" from "re-write the same bytes", and the two-JID plant is
            # list-shaped from the start so it discriminates only "does not ABORT
            # on a list". The migration imports the writer MODULE and resolves
            # the attribute at CALL TIME, which is what makes this counter
            # reachable at all.
            p.setattr(writer, "update_frontmatter_field", _counting_write)
            second = migrate.apply_migration(vault, second_plan)

        assert calls == [], (
            f"the re-run wrote {len(calls)} time(s) — the retry remedy promises "
            f"that the same command computes the correct REMAINING work")
        assert _tree_digest(vault) == digest_after_first, (
            "the re-run changed the tree — a re-write that merely REFORMATS is "
            "what this digest leg catches beside the call count")
        assert second.committed == 0 and second.repaired == 0
        # The TRIPLE is UNCHANGED rather than ZEROED: an already-list-shaped note
        # is MIGRATED by the action table. "Nothing was written" and "nothing is
        # migrated" are different claims and only the first is true of a re-run.
        assert second.triple == result.triple, (
            f"the re-run's triple must equal the first pass's, not be zeroed; "
            f"{second.triple} vs {result.triple}")

        # ---- THE RESIDUAL'S REPAIR PATH, EXERCISED rather than promised. A
        # class-D note CLEARED through a delta arm and a class-E note REWRITTEN
        # through one, both succeeding — so "reported and left for hand repair"
        # names a door this suite has opened.
        writer.update_frontmatter_field(plants["D"], "whatsapp", "")
        assert WhatsAppJID.classify_field(_stored(plants["D"])) == [], (
            "clearing the field is the only repair a class-D value has and it "
            "must SUCCEED")
        writer.update_frontmatter_field(plants["E"], "whatsapp", [TWO_JID_LID])
        assert _stored(plants["E"]) == [TWO_JID_LID], (
            "writing a properly spelled JID over a class-E value must SUCCEED")

    # ---- BOTH ARMS OF RULING B. The alternative arm must be EXECUTABLE rather
    # than hypothetical, and it changes the number Dave is shown.
    with _temp_root() as root:
        vault = _temp_vault(root)
        plants = _plant_every_cell(vault)
        class_c_before = plants["C"].read_bytes()

        plan = migrate.plan_migration(vault)
        plan.repair = False
        declined = migrate.apply_migration(vault, plan, repair=False)
        readback = migrate.readback_migration(vault, plan)

        assert declined.repaired == 0, (
            "`--no-repair` must attempt NO repair")
        assert plants["C"].read_bytes() == class_c_before, (
            "under the alternative arm the class-C note is left BYTE-IDENTICAL")
        # Under the alternative arm class C JOINS the residual: those notes stay
        # scalar AND unsaveable through the whole-record arms until hand repair,
        # and the residual grows by the class-C row.
        assert readback.triple[2] == 3, (
            f"with the repair declined the residual is the class-C, class-D and "
            f"class-E notes; found {readback.triple[2]}")
        for index, part in enumerate(migrate.PART_NAMES):
            assert (plan.triple[index] == declined.triple[index]
                    == readback.triple[index]), (
                f"part `{part}` disagrees under the alternative arm")
        assert readback.triple[0] == 0


# ==========================================================================
# M1 and M4 — the repair disclosure, and the render that makes its oracle total
# ==========================================================================

#: M4 leg (1)'s DERIVED break set, computed ONCE at module level (~1s). DERIVED
#: and never hand-listed: escaping `\n`, `\r`, `\t` and `\x1b` alone leaves
#: U+000B, U+000C, U+001C–U+001E, U+0085 NEL, U+2028 and U+2029 as the next
#: round's finding, and a hand list IS the defect this leg exists to prevent. A
#: builder must not "optimize" this into one.
BREAK_CODEPOINTS = frozenset(
    cp for cp in range(0x110000) if len(f"a{chr(cp)}b".splitlines()) > 1)

#: The ESC, which is not a line breaker and so is not in the set above, but is
#: the character that rewrites a terminal. Asserted alongside.
ESCAPE_CODEPOINT = 0x1b


def _disclosure_plants(vault_dir) -> dict:
    """The 2x2 of class-C sub-cells — {corroborated, uncorroborated} x {clean,
    control-bearing} — plus one note per OTHER class, including a class-A note
    whose digits are absent from its own `phones[]` (the population is class C
    ONLY, so the disclosure is not a corroboration report)."""
    return {
        "c_corr_clean": _plant(vault_dir, "Discloser One",
                               whatsapp=C_CORROBORATED_CLEAN,
                               phones=[f"+{C_CORROBORATED_CLEAN}"]),
        "c_unco_clean": _plant(vault_dir, "Discloser Two",
                               whatsapp=C_UNCORROBORATED_CLEAN, phones=[]),
        "c_corr_ctrl": _plant(vault_dir, "Discloser Three",
                              whatsapp=C_CORROBORATED_CONTROL,
                              phones=[f"+{C_CORROBORATED_CLEAN[:9]}204"]),
        "c_unco_ctrl": _plant(vault_dir, "Discloser Four",
                              whatsapp=C_ADVERSARIAL, phones=[]),
        "a": _plant(vault_dir, "Discloser Alpha", whatsapp=CLASS_A_VALUE,
                    phones=[]),
        "d": _plant(vault_dir, "Discloser Delta", whatsapp=CLASS_D_VALUE),
        "e": _plant(vault_dir, "Discloser Echo", whatsapp=CLASS_E_VALUE),
        "o": _plant(vault_dir, "Discloser Empty", whatsapp=""),
    }


def test_whatsapp_dry_run_discloses_each_class_c_repair_pair():
    """M1 and M4 (`## Design` §10(a) and §10(d)). The dry run puts every
    `(stored value -> proposed JID)` pair in front of the human who authorizes 82
    irreversible re-spellings, uncorroborated members FIRST — and the render is
    what makes "one line per record" a property of the FORMATTER rather than an
    accident of the data.

    Zero-arg and raising, per the check contract.
    """
    # ---- M4 leg (1) TOTALITY. The rule is stated over the CLASS that generates
    # the hazard, so the oracle is DERIVED over the whole codepoint space rather
    # than sampled. The second half proves the CONTAINMENT this implementation
    # rests on: the category test alone is the implementation because the
    # category set CONTAINS the break set, and if a future Python breaks on a
    # character outside those four categories this leg goes RED and says so.
    assert len(BREAK_CODEPOINTS) > 1, (
        "the derived break set is empty or degenerate — the leg would be "
        "vacuous")
    for cp in sorted(BREAK_CODEPOINTS) + [ESCAPE_CODEPOINT]:
        rendered = migrate._escape_for_one_line(f"a{chr(cp)}b")
        assert len(rendered.splitlines()) == 1, (
            f"U+{cp:04X} still breaks the render into "
            f"{len(rendered.splitlines())} lines")
        assert chr(cp) not in rendered, (
            f"U+{cp:04X} survives the render RAW — the escape must be visible")

    # The backslash FIRST, so the rendering is unambiguous.
    assert migrate._escape_for_one_line("a\\b") == "a\\\\b"

    with _temp_root() as root:
        vault = _temp_vault(root)
        plants = _disclosure_plants(vault)

        # ---- THE ADVERSARIAL PLANT IS ASSERTED TO BE THE SHAPE IT CLAIMS, or
        # the leg is vacuous. A plant that silently became clean proves nothing.
        adversarial_stored = _stored(plants["c_unco_ctrl"])
        assert "\n" in str(adversarial_stored), (
            "the adversarial plant lost its interior control character on the "
            "way through YAML")
        assert migrate.CORROBORATED_HEADER in str(adversarial_stored), (
            "the adversarial plant must carry the TEXT of a header constant, "
            "which is the forgery this leg exists to close")
        assert WhatsAppJID.classify_field(adversarial_stored) == ["C"], (
            "the adversarial plant must be class C — the exact population the "
            "disclosure prints and the repair rewrites")

        # Corroboration is computed by CALLING `phones_match` over each plant's
        # OWN values, never read off a flag written beside the plant.
        def corroborated(path) -> bool:
            frontmatter, _ = parse_frontmatter(
                Path(path).read_text(encoding="utf-8"))
            value = frontmatter.get("whatsapp")
            digits = WhatsAppJID.parse(value).phone_digits
            return any(
                phones_match(digits, normalize_phone(str(candidate)))
                for candidate in (frontmatter.get("phones") or [])
                if str(candidate).strip())

        assert corroborated(plants["c_corr_clean"])
        assert corroborated(plants["c_corr_ctrl"])
        assert not corroborated(plants["c_unco_clean"])
        assert not corroborated(plants["c_unco_ctrl"]), (
            "the adversarial plant must land in the UNCORROBORATED section — "
            "the section where a forged header would do the most damage, by "
            "appearing to move the one row the census asked a human to read "
            "into the safe half")

        # ---- THE DISCLOSURE IS READ-ONLY, by the same tree digest leg (a)
        # takes.
        digest_before = _tree_digest(vault)
        plan = migrate.plan_migration(vault)
        rendered = migrate.format_repair_disclosure(plan)
        assert _tree_digest(vault) == digest_before, (
            "the disclosure WROTE — `format_repair_disclosure` returns a string "
            "and `_cli` prints it, which is also why it is not a member of the "
            "containment census's mutating drives")

        # ---- THE POPULATION IS CLASS C ONLY, with the expected count DERIVED by
        # calling `classify_field` over the vault rather than written as a
        # literal.
        expected_records = []
        for path, frontmatter in _person_frontmatter(vault):
            stored = frontmatter.get("whatsapp")
            classes = WhatsAppJID.classify_field(stored)
            for member, member_class in zip(_raw_members(stored, classes),
                                            classes):
                if member_class == "C" and WhatsAppJID.parse(member).phone_digits:
                    expected_records.append((path, member))
        assert len(expected_records) >= 4, (
            "the 2x2 of class-C sub-cells is not planted — the oracle would be "
            "partial over its own input space")
        assert len(plan.repairs) == len(expected_records), (
            f"the disclosure must carry one record per class-C value; "
            f"{len(plan.repairs)} vs {len(expected_records)}")

        # Each record's proposed JID computed in THIS test by calling the same
        # repair spelling on the plant's own stored value.
        by_path = {}
        for record in plan.repairs:
            by_path.setdefault(Path(record.path), []).append(record)
        for path, member in expected_records:
            records = by_path[path]
            assert any(r.stored_value == str(member)
                       and r.proposed_jid == migrate._repair_spelling(member)
                       for r in records), (
                f"{path.name}: the disclosed pair does not match the repair the "
                f"run would actually make")

        # A class-A plant whose digits are absent from its `phones[]` yields NO
        # line: the disclosure is not a corroboration report.
        assert Path(plants["a"]) not in by_path, (
            "a class-A note reached the repair disclosure — the population is "
            "class C ONLY")

        # ---- M4 leg (2) NO-OP ON CLEAN. The escape is the identity wherever
        # verbatim is safe, so the 82 live bare digit runs render exactly as a
        # verbatim render would — which is why nobody should later "restore
        # verbatim as a fidelity improvement".
        clean_paths = {Path(plants["c_corr_clean"]), Path(plants["c_unco_clean"]),
                       Path(plants["c_corr_ctrl"]), Path(plants["c_unco_ctrl"])}
        for record in plan.repairs:
            assert (migrate._escape_for_one_line(record.proposed_jid)
                    == record.proposed_jid), (
                "the proposed JID is digits plus a fixed domain and the escape "
                "must be a no-op on it")
            if Path(record.path) not in clean_paths or record.stored_value in (
                    C_CORROBORATED_CLEAN, C_UNCORROBORATED_CLEAN):
                assert (migrate._escape_for_one_line(record.stored_value)
                        == record.stored_value), (
                    f"the escape changed a CLEAN stored value: "
                    f"{record.stored_value!r}")
            assert (migrate._escape_for_one_line(str(record.path))
                    == str(record.path)), (
                "the escape changed a clean note path — `path` is routed "
                "through the same helper so the guarantee is total over the "
                "RECORD, and it must be the identity where nothing would break")

        # ---- UNCORROBORATED FIRST, under its own header. Section ORDER is the
        # mitigation: on the live corpus there is exactly ONE uncorroborated
        # member and it is the row the census asked a human to read.
        lines = rendered.splitlines()
        assert lines[0] == migrate.UNCORROBORATED_HEADER, (
            f"the UNCORROBORATED header must come FIRST; got {lines[0]!r}")
        unco_index = lines.index(migrate.UNCORROBORATED_HEADER)
        corr_index = lines.index(migrate.CORROBORATED_HEADER)
        assert unco_index < corr_index
        unco_block = "\n".join(lines[unco_index + 1:corr_index])
        corr_block = "\n".join(lines[corr_index + 1:])
        assert migrate._escape_for_one_line(C_UNCORROBORATED_CLEAN) in unco_block
        assert migrate._escape_for_one_line(C_CORROBORATED_CLEAN) in corr_block
        assert C_UNCORROBORATED_CLEAN not in corr_block

        # ---- M4 leg (4) LINE COUNT STILL EQUALS RECORD COUNT, with BOTH terms
        # DERIVED: the record count by calling `classify_field` over the plants,
        # the header term by calling the formatter over the same plan with the
        # adversarial plant removed and counting the header lines it produced.
        header_constants = {migrate.UNCORROBORATED_HEADER,
                            migrate.CORROBORATED_HEADER,
                            migrate.NO_REPAIR_BANNER}
        control_free = migrate.MigrationPlan(
            vault_path=plan.vault_path, repair=plan.repair,
            actions=list(plan.actions),
            repairs=[r for r in plan.repairs
                     if "\n" not in r.stored_value])
        control_lines = migrate.format_repair_disclosure(
            control_free).splitlines()
        header_term = sum(1 for line in control_lines
                          if line in header_constants)
        assert len(lines) == len(expected_records) + header_term, (
            f"the render is {len(lines)} lines for {len(expected_records)} "
            f"records plus {header_term} header(s) — a record that reflowed is "
            f"exactly what breaks a conductor's line count")

        # ---- M4 leg (5) NO FORGED HEADER. The set of output lines EQUAL to any
        # imported header constant is exactly the set THIS run produced, so a
        # header appearing only because the DATA spelled one is RED.
        emitted = [line for line in lines if line in header_constants]
        assert emitted == [migrate.UNCORROBORATED_HEADER,
                           migrate.CORROBORATED_HEADER], (
            f"a header line appeared that the formatter did not emit — the "
            f"disclosure can be steered by the very data it exists to "
            f"disclose; found {emitted}")

        # ---- THE ALTERNATIVE ARM PRINTS THE SAME PAIRS, under a banner stating
        # that no repair will be attempted and that those notes join the
        # residual — which is what makes Ruling B's alternative arm readable
        # rather than hypothetical.
        plan.repair = False
        declined = migrate.format_repair_disclosure(plan)
        assert declined.splitlines()[0] == migrate.NO_REPAIR_BANNER
        assert len(declined.splitlines()) == len(lines) + 1


# ==========================================================================
# Task 12 — every wall membership closed by RUNNING the wall's own predicate
# ==========================================================================

def test_whatsapp_wall_membership_is_closed_by_running_each_walls_predicate():
    """Task 12's verify. Each wall named in `## Verification`'s inbound census,
    RUN over this item's FINAL text — never reasoned about. The census there is a
    FLOOR measured on 2026-09-27 and never a total, which is why this check runs
    the predicates instead of trusting the list.

    Zero-arg and raising, per the check contract.
    """
    from obsidian_schemas.repositories.base import SKIP_REASONS
    from tests.test_ac_interpreter import check_module
    from tests.test_identity_endgame import AUTHORIZED_PROSE_OWNERS, _golden
    from tests.test_name_gate_wall import EDITED_FUNCTION_ARM_COUNTS
    from tests.test_vault_path_required import NO_ARG_CONSTRUCTION

    universe = python_files_under(PACKAGE_ROOT, TESTS_ROOT, SCRIPTS_ROOT)
    relative = {p.relative_to(ROOT).as_posix() for p in universe}
    for shipped in ("scripts/migrate_whatsapp_to_list.py",
                    "tests/test_whatsapp_migration.py",
                    "tests/test_whatsapp_write_door.py",
                    "tests/test_whatsapp_jid_storage.py"):
        assert shipped in relative, (
            f"the universe does not reach {shipped} — every equality below "
            f"would be about a tree that is not the one this item ships")

    # (1) the `ast` capability stays SINGLE-HOMED. This item ships three new test
    # modules and a new script and none of them may name it.
    homes = {use.module for use in modules_using_ast(universe)}
    assert homes == {"tests/derivations.py"}, (
        f"the `ast` capability must stay single-homed to the shared scan "
        f"module; found {sorted(homes)}")

    # (2) the skip vocabulary's legal homes stay at EXACTLY two, which is the
    # statement that proves this item's new modules IMPORT a reason rather than
    # transcribing one.
    assert skip_reason_literal_sites(universe, SKIP_REASONS) == {
        "obsidian_schemas/repositories/base.py",
        "tests/test_fixture_vault.py",
    }

    # (3) `check_module` resolves EVERY top-level `def test_` this item's three
    # new modules define, READ from those modules' own source at test time and
    # never from a list in the plan. The conveyor's discovery rule raises on
    # anything but exactly one match, so a name colliding with an existing module
    # is RED here rather than at a transition.
    for module_path in NEW_TEST_MODULES:
        names = _top_level_checks(module_path)
        assert names, f"{module_path.name} defines no top-level check at all"
        for name in names:
            assert check_module(name) == module_path, (
                f"{name} does not resolve to {module_path.name}")

    # (4) every frontmatter write arm in the package AND in `scripts/` is routed
    # and DECLARED, with `absent` empty BY EQUALITY. The new script adds no arm —
    # its write is the one door — so this answer is unchanged with it in scope.
    live_files = python_files_under(PACKAGE_ROOT, SCRIPTS_ROOT)
    arms = frontmatter_write_arms(live_files)
    declarations = gate_call_declarations(live_files)
    absent = {arm for arm in arms if declarations.get(arm) == "absent"}
    assert absent == set(), (
        f"no arm may omit the declared_type keyword; found {sorted(absent)}")
    assert not [arm for arm in arms
                if arm.module == "scripts/migrate_whatsapp_to_list.py"], (
        "the migration must contribute NO write arm")

    # (5) `EDITED_FUNCTION_ARM_COUNTS`'s six per-function equalities, unchanged.
    counts = {}
    for arm in arms:
        counts[(arm.module, arm.qualname)] = counts.get(
            (arm.module, arm.qualname), 0) + 1
    for key, expected in EDITED_FUNCTION_ARM_COUNTS.items():
        assert counts.get(key, 0) == expected, (
            f"{key[1]} must still contribute EXACTLY {expected} arm(s), found "
            f"{counts.get(key, 0)}")

    # (6) every phone-index iteration site in the package is `materialized`. This
    # item rewrites both sides of the whatsapp pivot, and `## Design` §5(b)
    # prescribes a LOOKUP rather than a loop for exactly this reason.
    live = [site for site in phone_index_iteration_sites(
        python_files_under(PACKAGE_ROOT)) if site.classification != "materialized"]
    assert not live, (
        f"a phone-index iteration site is not materialized: {live}")

    # (7) WI-024's clause (e1) over `person.py`, recomputed here through
    # `prose_lines`: every Cut-0 `(owner, text)` pair whose owner is OUTSIDE
    # `AUTHORIZED_PROSE_OWNERS` still PRESENT. This item appends two paragraphs
    # to `PersonRepository.save`'s docstring and edits two comments it is
    # authorized to edit, so the whole clause is re-run rather than only the
    # `save` half AC-3 asserts.
    golden = _golden("prose_surface_cut0.json")
    surface = {(record.owner, record.text)
               for record in prose_lines([PERSON_MODULE])}
    lost = [(row["owner"], row["text"]) for row in golden["lines"]
            if row["owner"] not in AUTHORIZED_PROSE_OWNERS
            and (row["owner"], row["text"]) not in surface]
    assert not lost, (
        f"{len(lost)} frozen Cut-0 prose line(s) of an UNAUTHORIZED owner were "
        f"edited or deleted: {lost[:3]}")

    # (8) VOLUNTARY, and DECLARED as such so the next reader does not read it as
    # a membership the wall imposes: `docs` is a member of `DOC_SCAN_EXCLUDED`
    # and is intersected against every path part, so NO file under `docs/**`
    # joins the repo-wide markdown scan's population at all — the same fact M2
    # rests on. Run here anyway over the ONE `docs/wi-032-*` file this item
    # writes plus this item's own document; the other two `docs/wi-032-*`
    # artifacts are conductor preconditions this build does not author.
    for doc in (BRACKET, ITEM_DOC):
        offenders = [line for line in
                     doc.read_text(encoding="utf-8").splitlines()
                     if NO_ARG_CONSTRUCTION.search(line)]
        assert not offenders, (
            f"{doc.name} advertises no-arg repository construction: "
            f"{offenders[:2]}")


# ==========================================================================
# M2 and M3 — the live bracket's redaction wall, figures and row shape
# ==========================================================================

#: M2's predicate, stated exactly. The 40-hex STRIP is not caution: every HEAD
#: the bracket's entry row copies is a 40-hex token and two of the ones recorded
#: in `docs/wi-032-consumer-audit.md` carry nine-digit runs INSIDE them, so an
#: unstripped scan fires on correct content, gets read as noise, and is narrowed
#: back under pressure with nothing checking that the narrowing kept the claimed
#: shapes — the WI-235 failure, closed in advance.
COMMIT_TOKEN = re.compile(r"\b[0-9a-f]{40}\b")
DIGIT_RUN = re.compile(r"\d{9,}")
JID_SHAPED = re.compile(r"\d@[A-Za-z0-9-]+")


def _redaction_offenders(text: str) -> list:
    """The wall's OWN predicate, in ONE place so the claimed match-shapes below
    are driven through the same function the live scan calls rather than through
    a second copy of the matching logic."""
    stripped = COMMIT_TOKEN.sub("", text)
    return sorted(set(DIGIT_RUN.findall(stripped))
                  | set(JID_SHAPED.findall(stripped)))


def test_wi032_live_baseline_row_shape_and_redaction_wall():
    """M2 and M3 (`## Design` §10(b) and §10(c)). Three duties over the live
    bracket's FINAL text: REDACTION, FIGURES and SHAPE.

    Zero-arg and raising, per the check contract.
    """
    # ---- (i) REDACTION, with the claimed match-shapes driven through the wall's
    # OWN predicate as GREEN fixtures. Every literal RESERVED-block or synthetic:
    # a wall over live identifiers has no business introducing one, and the
    # predicate cannot tell a reserved eleven-digit run from a real one.
    for must_match in ("15555550142", "123456789012@s.whatsapp.net",
                       "15555550142@lid"):
        assert _redaction_offenders(must_match), (
            f"the redaction predicate does not see {must_match!r} — a wall that "
            f"passes by matching NOTHING")
    for must_not in ("27cb78cc5a2099972dccea984664193e69414def",
                     "1168", "1025", "82", "663-665", "2026-09-27",
                     "@s.whatsapp.net"):
        assert not _redaction_offenders(must_not), (
            f"the redaction predicate fires on {must_not!r} — a wall that "
            f"passes by matching EVERYTHING, and the shape that gets it "
            f"narrowed back under pressure")

    # Run over all THREE `docs/wi-032-*` artifacts — this bracket and both
    # grounding artifacts — which closes the CLASS this item's docs form instead
    # of the one instance. Deliberately NOT over `docs/whatsapp-jid-value-type.md`:
    # `## Design` §9 line 5 and F18 leg 6 keep one real number in it on purpose,
    # already committed twice in this tree, and a predicate run over that file
    # would be RED against a state two gates ratified.
    for doc in (BRACKET, CENSUS, CONSUMER_AUDIT):
        offenders = _redaction_offenders(doc.read_text(encoding="utf-8"))
        assert not offenders, (
            f"{doc.name} carries what may be a live identifier: {offenders}")

    bracket = BRACKET.read_text(encoding="utf-8")

    # ---- (ii) FIGURES. §1's rows and the five derived partition figures equal
    # values DERIVED by parsing the census's OWN verbatim stdout block — never
    # literals re-typed from the plan — so the bracket is PROVEN to agree with the
    # artifact it copies from. This check does not re-measure the live vault and
    # no hermetic check can.
    #
    # CORPUS_COUPLING: this leg pins `docs/wi-032-whatsapp-corpus-census.md`'s
    # machine-output block and consumes the property that its `(a)`, `(c)` and
    # `(c')` lines are its census script's stdout. That artifact is a committed
    # conductor precondition, not a machine-mutable corpus member, so the
    # coupling is to a frozen file and is declared here rather than derived.
    census = CENSUS.read_text(encoding="utf-8")
    # The STDOUT BLOCK is isolated FIRST, and that is not tidiness: the artifact
    # carries its census SCRIPT above its output, so every `(a)`/`(c)`/`(c')`
    # marker appears TWICE — once as an f-string in the source and once as the
    # line it printed. A bare `re.search` over the whole file reads the SOURCE,
    # which is the shape that made this leg green against a number it never found.
    stdout_block = re.search(
        r"stdout, verbatim:\s*\n+```\n(.*?)\n```", census, re.S).group(1)
    people = int(
        re.search(r"^\(a\).*type: person: (\d+)", stdout_block, re.M).group(1))
    rows = {name: int(count) for name, count in
            re.findall(r"^\(c\) class ([^:]+): (\d+)", stdout_block, re.M)}
    splits = dict(re.findall(
        r"'([^']+)': (\d+)",
        re.search(r"^\(c'\) splits: \{([^}]*)\}", stdout_block, re.M).group(1)))
    absent_key = int(splits["Ø:absent-key"])
    empty_string = int(splits["Ø:empty-string"])
    for cell in ("Ø", "A", "B", "C", "D", "E"):
        assert cell in rows, (
            f"the census's stdout block has no `(c) class {cell}` line — the "
            f"figures below would be derived from a parse that missed a cell")

    carrying = people - absent_key
    residual = rows["D"] + rows["E"]
    migrated = carrying - residual

    for figure in (people, rows["Ø"], rows["A"], rows["B"], rows["C"],
                   absent_key, empty_string, carrying, migrated,
                   empty_string, rows["C"], residual):
        assert re.search(rf"\|\s*{figure}\s*\|", bracket), (
            f"the bracket's §1 does not carry the census-derived figure "
            f"{figure} in a table cell — a transcription nobody proved")
    # The two ZERO rows are asserted by NAME rather than by a bare `| 0 |` cell,
    # which any table would satisfy.
    for name, count in (("class **D**", rows["D"]), ("class **E**", rows["E"])):
        assert re.search(rf"\|\s*{re.escape(name)}[^|]*\|\s*{count}\s*\|",
                         bracket), f"§1's {name} row does not read {count}"

    # ---- (iii) SHAPE (M3). The ordered list is the TWO LOUD breaks and only
    # those two; the raw-file writer stands OUTSIDE it in its own row. Three
    # consequences in one list read as three annoyances to be weighed together,
    # and a conductor reading a flat list cannot see that two of them announce
    # themselves while the third is silent and destructive.
    assert "### DATA-LOSS HOLD" in bracket, (
        "the silent destructive break must have its OWN row, not be item three "
        "of a list")
    section_three = bracket.split("## 3.", 1)[1].split("## 4.", 1)[0]
    before_hold, _, hold_row = section_three.partition("### DATA-LOSS HOLD")

    ordered = [line for line in before_hold.splitlines()
               if re.match(r"^\d+\. ", line)]
    assert len(ordered) == 2, (
        f"§3's ordered list must have EXACTLY two items — the two LOUD breaks; "
        f"found {len(ordered)}: {ordered}")
    joined = "\n".join(ordered)
    assert "invariants.py:663-665" in joined, (
        "the red vault-wide invariant is not named in the ordered list")
    assert "contacts.py:41,50" in joined, (
        "the 500ing endpoint is not named in the ordered list")
    assert "merge-duplicate-persons.py" not in before_hold, (
        "the raw-file writer appears INSIDE §3's ordered list — the separation "
        "IS the mitigation")
    assert "merge-duplicate-persons.py:380-384" in hold_row, (
        "the DATA-LOSS HOLD row does not name the site it holds")
    assert "apply-vault-review.py" in hold_row, (
        "the HOLD row must name the reaching callers")
    assert re.search(r"not to be run|is to be run|do not run", hold_row,
                     re.IGNORECASE), (
        "the HOLD row must carry the conductor instruction that makes it a HOLD "
        "rather than a note")
    assert "wi-032-consumer-audit.md:227-239" in section_three, (
        "items 4-7 of the audit's seven-site list must be carried as a pointer")
    assert "26" in section_three, (
        "§3 must carry the 26-lid sentence — the census's own §2 is over-broad "
        "about the resolution fix's blast radius")

    # The check asserts the §5 HEADING exists and asserts NOTHING about its
    # content: the conductor writes the exit figures there after the build, and a
    # check pinning §5 empty would redden the floor at exactly the moment the
    # item closes. The redaction predicate above still holds over §5, because
    # what §5 carries is the partition's three parts as counts.
    assert re.search(r"^## 5\. ", bracket, re.MULTILINE), (
        "the bracket must carry a named §5 for the conductor's exit figures")
