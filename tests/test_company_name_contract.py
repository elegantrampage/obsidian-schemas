"""WI-022 — the company name contract: the five acceptance checks plus the
in-build oracles the frozen criteria do not reach.

Every AC-named check here is a top-level, ZERO-ARGUMENT `def test_*` that signals
failure by RAISING, because the conveyor's battery discovers it by source scan
and invokes it as `getattr(module, name)()` with no pytest fixture machinery in
the loop. Temp vaults, log capture and attribute patches come from
`tests/support.py` rather than from `tmp_path`/`caplog`.

Nothing here reads syntax (no `ast` import, no attribute access on one): that
capability is single-homed to `tests/derivations.py` by a standing set-equality
wall, which is why the character-class scan AC-1 leg one runs lives THERE and is
imported here.

CORPUS_COUPLING: `test_company_name_corpus_audit_is_complete` pins the SHAPE of
one NAMED doc — `docs/company-name-corpus-audit.md` — and consumes the property
"this artifact records the vault walk, the per-branch refusal counts, the D4
residue size and the three consumers' scan evidence". It names the file rather
than globbing `docs/**`, so its universe does not grow with the corpus; it is a
`kind: precondition` artifact a conductor amends, never a machine-mutable one.
"""

from tests.ac_interpreter import ensure_project_interpreter

ensure_project_interpreter(__file__)   # FIRST — ahead of every package import

import logging                                                  # noqa: E402
import re                                                       # noqa: E402
from pathlib import Path                                        # noqa: E402

from obsidian_schemas import (                                   # noqa: E402
    Company,
    CompanyRepository,
    NameGateRefusal,
    parse_frontmatter,
    update_frontmatter_field,
    write_frontmatter,
    write_markdown_file,
)
from obsidian_schemas.name_gate import COMPANY_TYPE, gate_write   # noqa: E402
from obsidian_schemas.name_validation import (                    # noqa: E402
    COMPANY_TIER1_BRANCHES,
    EMPTY_BRANCH,
    TIER1_BRANCHES,
    NameValidationError,
    NameValidator,
    _COMPANY_PATH_HOSTILE_RE,
    tier2_repair,
)
from obsidian_schemas.writer import (                             # noqa: E402
    roundtrip_file,
    update_frontmatter_fields,
)

from tests.derivations import (                                   # noqa: E402
    PACKAGE_ROOT,
    SCRIPTS_ROOT,
    ArmId,
    character_class_strip_sites,
    frontmatter_write_arms,
    python_files_under,
)
from tests.support import captured_logs, temp_dir                 # noqa: E402
from tests.test_name_gate_wall import assert_default_lock_home    # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent

# The one enumerated reason every gate refusal carries.
REFUSAL_REASON = "the write introduces a name this package refuses"


# ---------------------------------------------------------------------------
# Shared fixtures and helpers
# ---------------------------------------------------------------------------

def _plant_company_note(path: Path, name: str, **extra) -> Path:
    """Write a company note's BYTES directly, bypassing the package's write door.

    The ONLY way to obtain a note whose STORED name is already Tier-1 dirty —
    which is exactly the population AC-4's delta rule owes writability, and
    exactly what this fix declines to create rather than to brick. The YAML is
    produced by the package's own `write_frontmatter`, never by a rolled-own
    serializer, so the planted bytes are the bytes the package would produce.
    """
    frontmatter = {"type": "company", "name": name, "tags": ["company"]}
    frontmatter.update(extra)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("---\n" + write_frontmatter(frontmatter) + "---\n## Notes\n",
                    encoding="utf-8")
    return path


def _stored_name(path: Path) -> str:
    """The `name:` this note actually carries on disk, read back off disk."""
    frontmatter, _body = parse_frontmatter(path.read_text(encoding="utf-8"))
    return frontmatter["name"]


def _record(branches: tuple, branch_id: str):
    """The record with this `branch_id`, located BY branch_id — never by
    position and never by `pattern`, which is not unique in either table."""
    for record in branches:
        if record.branch_id == branch_id:
            return record
    raise AssertionError(
        f"no record with branch_id={branch_id!r} in "
        f"{[b.branch_id for b in branches]}"
    )


def _refusal_of(call) -> NameGateRefusal:
    """Run `call` and return the `NameGateRefusal` it raised.

    Caught by the LEAF name, never by the `LoudFailError` root: sibling leaves
    raise from the same frames and a root filter would misattribute them.
    """
    try:
        call()
    except NameGateRefusal as exc:
        return exc
    raise AssertionError("expected a NameGateRefusal; the write committed")


# ===========================================================================
# Task 2 — the character-class scan predicate's shape battery
# ===========================================================================

# Every claimed match-shape and every near-miss, driven through the SAME
# predicate the live sweep calls (WI-235: a counting wall ships its claimed
# shapes as fixtures, or its GREEN says nothing about what the matcher can see).
# `_HEAD` gives each plant a syntactically valid import line.
_HEAD = "import re\n"

MATCHING_PLANTS = {
    "bare_call": _HEAD + "def f(name):\n    return re.sub(r'[^\\w\\s-]', '', name)\n",
    "nested_in_if": _HEAD + (
        "def f(name):\n"
        "    if name:\n"
        "        return re.sub(r'[^\\w\\s-]', '', name)\n"
        "    return name\n"
    ),
    "nested_in_for": _HEAD + (
        "def f(names):\n"
        "    out = []\n"
        "    for n in names:\n"
        "        out.append(re.sub(r'[^\\w\\s-]', '', n))\n"
        "    return out\n"
    ),
    "aliased_import": (
        "from re import sub as _s\n"
        "def f(x):\n    return _s(r'[^\\w]', '', x)\n"
    ),
    "compiled_name": _HEAD + (
        "_M = re.compile(r'[^\\w\\s-]')\n"
        "def f(x):\n    return _M.sub('', x)\n"
    ),
    "inline_compiled": _HEAD + (
        "def f(x):\n    return re.compile(r'[^\\w]').sub('', x)\n"
    ),
}

NEAR_MISS_PLANTS = {
    # The legitimate OPPOSITE: an ENUMERATED set stripped off a FILENAME local.
    "enumerated_filename_sanitizer": _HEAD + (
        "def f(title):\n    return re.sub(r'[<>:\"/\\\\|?*]', '', title)\n"
    ),
    "non_negated_class": _HEAD + "def f(phone):\n    return re.sub(r'\\D', '', phone)\n",
    "non_empty_replacement": _HEAD + (
        "def f(s):\n    return re.sub(r'\\s{2,}', ' ', s)\n"
    ),
    # A negated-class COMPILED pattern whose replacement is not the deletion.
    "compiled_non_empty_replacement": _HEAD + (
        "WIKILINK = re.compile(r'[^\\w\\s-]')\n"
        "def f(s):\n    return WIKILINK.sub('x', s)\n"
    ),
    "comment_only": _HEAD + (
        "def f(name):\n"
        "    # legacy: re.sub(r'[^\\w\\s-]', '', name)\n"
        "    return name\n"
    ),
    # The docstring is itself a RAW string in the plant, so the plant compiles
    # without a SyntaxWarning; what matters is that the mangler's literal text
    # sits in a `Constant` in statement position and never in a `Call`.
    "docstring_only": _HEAD + (
        "def f(name):\n"
        '    r"""The mangler was re.sub(r\'[^\\w\\s-]\', \'\', name)."""\n'
        "    return name\n"
    ),
}


def test_character_class_strip_predicate_resolves_its_claimed_shapes():
    """Task 2's verify. Zero-arg and raising, per the check contract.

    A counting wall's GREEN says nothing about what its matcher can SEE:
    `sites == []` passes identically whether the predicate resolves every shape
    AC-1 claims or almost none. So every claimed shape is driven through the
    predicate the live sweep calls — never a second copy of the matching logic —
    and every near-miss is driven through it too, so the wall cannot pass by
    matching everything.
    """
    with temp_dir() as plants:
        for label, source in MATCHING_PLANTS.items():
            path = plants / f"match_{label}.py"
            path.write_text(source, encoding="utf-8")
            sites = character_class_strip_sites([path])
            assert len(sites) == 1, (
                f"{label}: the predicate must resolve this shape; got {sites}"
            )
            assert sites[0].qualname == "f", (
                f"{label}: attributed to {sites[0].qualname!r}, not the "
                "enclosing function"
            )

        for label, source in NEAR_MISS_PLANTS.items():
            path = plants / f"miss_{label}.py"
            path.write_text(source, encoding="utf-8")
            sites = character_class_strip_sites([path])
            assert sites == [], (
                f"{label}: the predicate must NOT match this shape; got {sites}"
            )

        # And a module-scope reintroduction is reported rather than missed.
        module_scope = plants / "module_scope.py"
        module_scope.write_text(_HEAD + "X = re.sub(r'[^\\w]', '', 'a b')\n",
                                encoding="utf-8")
        sites = character_class_strip_sites([module_scope])
        assert len(sites) == 1 and sites[0].qualname == "<module>", (
            f"a module-scope strip must be reported as <module>; got {sites}"
        )


# ===========================================================================
# Task 4 — the widened path-hostile class covers every character it names
# ===========================================================================

# The thirteen characters `_COMPANY_PATH_HOSTILE_RE`'s comment names, written
# out HERE as literals. Deliberately NOT re-derived from the constant's own
# `.pattern`: a test that reads the pattern to build its own expectation asserts
# the regex against itself and is green for a class that matches nothing.
WIDENED_MEMBERS = ("/", "\\", ":", "*", "?", '"', "<", ">", "|", "[", "]", "#", "^")

# Characters a real company name carries and this class must NOT touch.
WIDENED_NON_MEMBERS = ("&", ".", "!", "'", ",", "-", "(", ")")


def test_the_widened_path_hostile_class_covers_every_character_it_names():
    """Task 4's verify. Zero-arg and raising, per the check contract.

    §8.6's SECOND wall. Task 12 pins the audit artifact to this constant's
    `.pattern`, which is satisfied if the artifact's own early-closing typo
    (`[/\\:*?"<>|[]#^]`, which closes its class at the inner `]` and matches
    nothing) were transcribed into the package and printed. Driving every named
    character individually makes a constant that cannot match what it claims RED
    without reference to the artifact at all.
    """
    assert len(WIDENED_MEMBERS) == 13, "the comment names thirteen characters"
    for char in WIDENED_MEMBERS:
        assert _COMPANY_PATH_HOSTILE_RE.search("Acme" + char + "Corp"), (
            f"the widened class silently stopped matching {char!r} — a class "
            "that closes early matches its trailing members as literals"
        )
    for char in WIDENED_NON_MEMBERS:
        assert _COMPANY_PATH_HOSTILE_RE.search("Acme" + char + "Corp") is None, (
            f"the widened class must not match {char!r}: real company names "
            "carry it (the corpus census returns `&` and `.`)"
        )
    assert _COMPANY_PATH_HOSTILE_RE.search("Acme Corp") is None


# ===========================================================================
# Task 6 — the company arm does not fall through into the person body
# ===========================================================================

def test_the_company_arm_does_not_fall_through_into_the_person_body():
    """Task 6's verify. Zero-arg and raising, per the check contract.

    The architect's Note 2 property that NO frozen acceptance criterion catches.
    Written as a widened condition (`declared_type not in (PERSON_TYPE,
    COMPANY_TYPE)`) the company judgement would let company writes fall into the
    person body and be silently subjected to the `phones[]` dedupe — a DELETION
    over stored data — and to the two alias/email migrations, none of which this
    item signs off for companies.
    """
    payload = {
        "type": "company",
        "name": "Acme Corp",
        "phones": ["+44 7990 558521", "07990558521"],   # the same number twice
        "emails": ["Jane (jane@acme.com)"],             # the parens form M2 moves
        "aliases": ["jane@acme.com"],                   # the address form M1 moves
    }
    out = gate_write(payload, declared_type=COMPANY_TYPE, whole_record=True)
    assert out == payload, (
        "a company payload comes back byte-identical: the phone list UNDEDUPED "
        f"and neither migration run. Got {out!r}"
    )
    assert set(out) == set(payload), "THE OUTPUT NEVER GROWS"

    # IDEMPOTENCE, driven with a COMPANY payload — `gate_write(gate_write(x)) ==
    # gate_write(x)`, which the gate requires of every arm and which
    # test_name_gate.py's pure-function check does not drive with this type. It
    # is structurally guaranteed by a branch that assigns to no key, which is
    # why asserting it is one line and why its absence would be the first
    # symptom of a company arm that started returning a repaired name.
    twice = gate_write(out, declared_type=COMPANY_TYPE, whole_record=True)
    assert twice == out

    # A company delta introducing NO name is the pass-through this branch had
    # before the item, unchanged.
    delta = {"industry": "logistics", "website": "https://acme.example"}
    assert gate_write(delta, declared_type=COMPANY_TYPE, whole_record=False) == delta


# ===========================================================================
# Task 7 — §4.1's KEPT "Unknown Company" fallback, in executable form
# ===========================================================================

def test_create_stub_empty_name_takes_the_unknown_company_fallback():
    """Task 7's verify. Zero-arg and raising, per the check contract.

    §4.1's decision is KEPT deliberately: dropping it would change
    `create_stub("")` from writing a note to RAISING, a live behaviour change on
    HAL9000's `POST /api/entities/company` route and nowhere in the frozen
    Intent. Without this check a build that dropped it satisfies every
    acceptance criterion.

    Each input gets its OWN fresh vault: all three collapse to the same stem, so
    WI-004's no-clobber door would raise `NoteAlreadyExists` on the second call
    — a collision that reads as a fallback failure and is not one.
    """
    expected_stem = "@" + "Unknown Company"
    for empty_input in ("", "   ", None):
        with temp_dir() as vault:
            company = CompanyRepository(vault).create_stub(name=empty_input)
            assert company.name == "Unknown Company", (
                f"{empty_input!r} must take the fallback, not raise; got "
                f"{company.name!r}"
            )
            path = vault / (expected_stem + ".md")
            assert path.exists(), f"{empty_input!r}: no {path.name} on disk"
            assert path.stem == expected_stem
            frontmatter, _body = parse_frontmatter(path.read_text(encoding="utf-8"))
            assert frontmatter["name"] == "Unknown Company"
            # The fallback path and the provenance path COMPOSE — each is not
            # merely proved alone.
            assert frontmatter["created_by"] == "unknown"


# ===========================================================================
# AC-2 — the derived table sweep with a per-branch correctness oracle
# ===========================================================================

COMPANY_BRANCH_IDS = {"empty", "archive_prefix", "arrow_connective",
                      "email_chars", "path_hostile"}
EXCLUDED_BRANCH_IDS = {"rfc2822_leak", "calendar_prefix", "me_to_prefix",
                       "unknown_contact", "pure_digit"}


def test_company_tier1_table_is_swept_and_each_branch_has_an_oracle():
    """AC-2. Zero-arg and raising, per the check contract.

    EVERY set-membership assertion here is keyed on `.branch_id` and NEVER on
    `.pattern`. The two fields diverge and `.pattern` is not unique: keyed on
    `.pattern`, the token `pure_digit_name` matches no record in either table so
    an exclusion check written with it passes unconditionally, and excluding
    `calendar_prefix` is FALSE against the very table the Approach specifies
    because the INCLUDED `arrow_connective` raises exactly that pattern.
    """
    swept = {record.branch_id for record in COMPANY_TIER1_BRANCHES}

    # (i) EQUALITY — the membership `## Approach` states and the audit confirms.
    # Any of the five excluded ids turns this RED by itself.
    assert swept == COMPANY_BRANCH_IDS, (
        f"company table membership is {swept}, expected {COMPANY_BRANCH_IDS}"
    )

    # (ii) NON-CONVERGENCE in the other direction: a build cannot go green by
    # SUBTRACTING the excluded branches from the person tuple in place.
    person_ids = {record.branch_id for record in TIER1_BRANCHES}
    for excluded in sorted(EXCLUDED_BRANCH_IDS):
        assert excluded in person_ids, (
            f"{excluded!r} was removed from the PERSON table; the company table "
            "is a second table, never a subtraction from the first"
        )
        assert excluded not in swept

    # (iii) The SHARED-PATTERN guard, stated as a POSITIVE required fact rather
    # than left as an absence a reader must infer: excluding the
    # `calendar_prefix` and `me_to_prefix` BRANCHES must not have removed the
    # `calendar_prefix` PATTERN.
    arrow = _record(COMPANY_TIER1_BRANCHES, "arrow_connective")
    assert arrow.pattern == "calendar_prefix"

    # §1.3's two remaining literal properties, neither reachable from the
    # per-record refusal legs below.
    for record in COMPANY_TIER1_BRANCHES:
        assert record.sentinel_exempt is False, (
            f"{record.branch_id}: the WI-083 phone-sentinel exemption "
            "suppresses `pure_digit`, which this table does not carry"
        )
    company_path_hostile = _record(COMPANY_TIER1_BRANCHES, "path_hostile")
    person_path_hostile = _record(TIER1_BRANCHES, "path_hostile")
    assert company_path_hostile.pattern == person_path_hostile.pattern, (
        "one refusal key names one class across both declared types; the regex "
        "differs, the key does not"
    )

    # ---- the per-record sweep, iterating the TUPLE and never a hand list ----
    with temp_dir() as vault:
        for record in COMPANY_TIER1_BRANCHES:
            assert record.negative_specimen, (
                f"{record.branch_id}: a derived sweep proves MEMBERSHIP and "
                "never correctness — every member owes a REAL company name the "
                "branch must decline to fire on"
            )

            # (a) the specimen is REFUSED, with this record's stable pattern.
            sweep_path = vault / "@sweep.md"
            exc = _refusal_of(lambda: write_markdown_file(
                sweep_path,
                extra_fields={"type": "company", "name": record.specimen},
            ))
            assert exc.pattern == record.pattern, (
                f"{record.branch_id}: refused with {exc.pattern!r}, expected "
                f"{record.pattern!r}"
            )
            assert str(exc) == REFUSAL_REASON, (
                f"{record.branch_id}: the ONE enumerated reason, not "
                f"{str(exc)!r}"
            )
            if record.branch_id != "empty":
                # Skipped for `empty` alone, whose specimen "" is a substring of
                # every string.
                assert record.specimen not in str(exc), (
                    f"{record.branch_id}: the refused name reached the message"
                )
            assert not sweep_path.exists(), (
                f"{record.branch_id}: the refusal must land before anything "
                "reaches disk"
            )

            # (b) the CORRECTNESS oracle: this record's negative specimen is a
            # real company name and is written successfully, byte-identically,
            # through the frame that DERIVES the stem.
            negative_home = vault / f"negative-{record.branch_id}"
            negative_home.mkdir()
            path = CompanyRepository(negative_home).save(
                Company(name=record.negative_specimen))
            assert _stored_name(path) == record.negative_specimen, (
                f"{record.branch_id}: negative specimen "
                f"{record.negative_specimen!r} stored as "
                f"{_stored_name(path)!r}"
            )
            assert path.stem == "@" + record.negative_specimen

        # ---- THE COERCION LEG ----
        #
        # The derived per-record sweep structurally cannot reach this: every
        # `specimen` in the table is already a `str`. Three non-`str` payloads
        # through the SAME raw-`extra_fields` arm, and the three together are a
        # discriminant no other leg supplies — a build that drops the coercion
        # raises TypeError out of the regex on (3); a build that writes the
        # shorter `str(raw_name)` writes a company note named `None` on (1); a
        # build that reaches for the PERSON table refuses (3) on
        # `pure_digit_name`.
        empty_record = _record(COMPANY_TIER1_BRANCHES, "empty")
        coerce_path = vault / "@coerce.md"

        exc = _refusal_of(lambda: write_markdown_file(
            coerce_path, extra_fields={"type": "company", "name": None}))
        assert exc.pattern == empty_record.pattern, (
            "a null name is the `empty` refusal, never the string 'None'"
        )
        assert not coerce_path.exists()

        exc = _refusal_of(lambda: write_markdown_file(
            coerce_path,
            extra_fields={"type": "company", "name": ["Acme/Corp"]}))
        assert exc.pattern == company_path_hostile.pattern, (
            "the table judges the COERCED text, never skipping a non-`str`"
        )
        assert not coerce_path.exists()

        committed = vault / "@coerce-ok.md"
        write_markdown_file(committed,
                            extra_fields={"type": "company", "name": 123})
        assert committed.exists(), (
            "a ticker-styled numeric name is WRITABLE: the company table "
            "deliberately excludes `pure_digit` (D2/§1.4)"
        )


# ===========================================================================
# AC-1 — the zero-live-site scan and the preservation table
# ===========================================================================

# At minimum one name per character class the mangler destroyed, plus the two
# members that make the table unfakeable: "wetransfer.com" (which the PERSON
# table's `rfc2822_leak` branch refuses, so a blind copy is RED here) and
# "Acme  Corp" (Tier-2 dirty).
PRESERVATION_TABLE = (
    "O'Reilly Media",       # apostrophe
    "AT&T",                 # ampersand
    "Yahoo!",               # exclamation
    "Booking.com",          # dot
    "Alphabet, Inc.",       # comma + dot
    "wetransfer.com",       # lowercase-styled brand
    "Acme  Corp",           # Tier-2 dirty
)

# §8.4's leg map, DECLARED and asserted total over the DERIVED arm set in BOTH
# directions, so a ninth arm is RED until it is classified. The set stays
# derived; only the per-arm LEG is declared.
ARM_LEGS = {
    # create-shaped: `base.py:save:381-383` binds the stem here and nowhere else
    ArmId("obsidian_schemas/writer.py", "write_markdown_file", 1): "both",
    ArmId("obsidian_schemas/writer.py", "write_markdown_file", 2): "both",
    ArmId("obsidian_schemas/writer.py", "write_markdown_file", 3): "both",
    # update-shaped: derive no filename, so on an update the stem is whatever it
    # already was and a literal "both legs, every arm" is unsatisfiable by a
    # correct build
    ArmId("obsidian_schemas/repositories/base.py",
          "BaseRepository.update_fields", 1): "stored",
    ArmId("obsidian_schemas/writer.py", "update_frontmatter_field", 1): "stored",
    ArmId("obsidian_schemas/writer.py", "update_frontmatter_fields", 1): "stored",
    # NAMED EXCLUSIONS — neither leg. `roundtrip_file` calls
    # `gate_write({}, declared_type=None, ...)`: an empty delta, unconditionally,
    # on every invocation, so no company table can affect it. `apply_fixes`'
    # delta key set is closed at {auto_created, name} and its only name-writing
    # branch is gated on `entity_type == "person"`, so it structurally cannot
    # introduce a COMPANY name.
    ArmId("obsidian_schemas/writer.py", "roundtrip_file", 1): "excluded",
    ArmId("scripts/lint_vault.py", "apply_fixes", 1): "excluded",
}


def _drive_write_markdown_file_entity(work: Path, member: str) -> Path:
    path = work / ("@" + member + ".md")
    write_markdown_file(path, entity=Company(name=member))
    return path


def _drive_write_markdown_file_frontmatter(work: Path, member: str) -> Path:
    path = work / ("@" + member + ".md")
    write_markdown_file(path, frontmatter={"type": "company", "name": member})
    return path


def _drive_write_markdown_file_extra_fields(work: Path, member: str) -> Path:
    path = work / ("@" + member + ".md")
    write_markdown_file(path, extra_fields={"type": "company", "name": member})
    return path


def _drive_update_fields(work: Path, member: str) -> Path:
    path = _plant_company_note(work / "@Seed Co.md", "Seed Co")
    repo = CompanyRepository(work)
    repo.update_fields(repo.get("Seed Co"), {"name": member})
    return path


def _drive_update_frontmatter_field(work: Path, member: str) -> Path:
    path = _plant_company_note(work / "@Seed Co.md", "Seed Co")
    update_frontmatter_field(path, "name", member)
    return path


def _drive_update_frontmatter_fields(work: Path, member: str) -> Path:
    path = _plant_company_note(work / "@Seed Co.md", "Seed Co")
    update_frontmatter_fields(path, {"name": member})
    return path


ARM_DRIVERS = {
    ArmId("obsidian_schemas/writer.py", "write_markdown_file", 1):
        _drive_write_markdown_file_entity,
    ArmId("obsidian_schemas/writer.py", "write_markdown_file", 2):
        _drive_write_markdown_file_frontmatter,
    ArmId("obsidian_schemas/writer.py", "write_markdown_file", 3):
        _drive_write_markdown_file_extra_fields,
    ArmId("obsidian_schemas/repositories/base.py",
          "BaseRepository.update_fields", 1): _drive_update_fields,
    ArmId("obsidian_schemas/writer.py", "update_frontmatter_field", 1):
        _drive_update_frontmatter_field,
    ArmId("obsidian_schemas/writer.py", "update_frontmatter_fields", 1):
        _drive_update_frontmatter_fields,
}


def test_company_name_punctuation_survives_every_write_arm():
    """AC-1. Zero-arg and raising, per the check contract."""
    # ---- LEG ONE: the mangler is gone from the package ----
    #
    # A pattern scan over the tracked source, never a check against
    # `company.py:171` by line. The predicate is imported FROM
    # `tests.derivations` and its home asserted, so a private copy — which could
    # be narrowed to make its own site disappear — turns this check RED.
    assert character_class_strip_sites.__module__ == "tests.derivations", (
        "the scan predicate is single-homed: `ast` is named only by "
        "tests/derivations.py, and a private copy here defeats both walls"
    )
    sites = character_class_strip_sites(
        python_files_under(PACKAGE_ROOT, SCRIPTS_ROOT))
    assert sites == [], (
        f"the character-class mangler survives at {sites}"
    )

    # ---- LEG TWO: byte-identical preservation over the DERIVED arm set ----
    arms = frontmatter_write_arms(python_files_under(PACKAGE_ROOT, SCRIPTS_ROOT))
    assert set(arms) - set(ARM_LEGS) == set(), (
        f"unclassified write arms: {set(arms) - set(ARM_LEGS)} — a new arm is "
        "RED here until its leg is declared"
    )
    assert set(ARM_LEGS) - set(arms) == set(), (
        f"classified arms that no longer exist: {set(ARM_LEGS) - set(arms)}"
    )

    with temp_dir() as root:
        for arm in sorted(arms):
            leg = ARM_LEGS[arm]
            if leg == "excluded":
                continue
            driver = ARM_DRIVERS[arm]
            for index, member in enumerate(PRESERVATION_TABLE):
                work = root / f"{arm.qualname}-{arm.arm}-{index}".replace("/", "_")
                work.mkdir(parents=True)
                path = driver(work, member)
                assert _stored_name(path) == member, (
                    f"{arm}: {member!r} stored as {_stored_name(path)!r} — the "
                    "gate is a PREDICATE on `name`, never a transform"
                )
                if leg == "both":
                    assert path.stem == "@" + member, (
                        f"{arm}: stem {path.stem!r} != {'@' + member!r}"
                    )

        # `roundtrip_file` is exercised for the NARROWER property it does have:
        # a round-trip of a company note leaves the stored `name:`
        # byte-identical. It introduces no name, so no company table can affect
        # it, which is why it carries neither of AC-1's two legs.
        rt_home = root / "roundtrip"
        rt_home.mkdir()
        rt_path = _plant_company_note(rt_home / "@AT&T.md", "AT&T")
        roundtrip_file(rt_path)
        assert _stored_name(rt_path) == "AT&T"

        # ---- THE FRAME THE STEM LEG IS AN ORACLE IN ----
        #
        # On `write_markdown_file`'s three arms the CALLER supplies `file_path`,
        # so `stem == "@" + member` there is asserted against a path this test
        # itself chose and is true about nothing on its own. The discrimination
        # AC-1's `why` was written for lives at `base.py:save:381-383`, the
        # frame that DERIVES the stem — so at least one member of each of the
        # three character classes the corpus actually carries is driven through
        # it and the stem the REPOSITORY chose is the one asserted.
        save_home = root / "save-frame"
        save_home.mkdir()
        repo = CompanyRepository(save_home)
        for member in ("O'Reilly Media", "AT&T", "Booking.com"):
            saved = repo.save(Company(name=member))
            assert saved.stem == "@" + member, (
                f"save() derived stem {saved.stem!r} for {member!r}"
            )
            assert _stored_name(saved) == member

        # ---- THE TIER-2 LEG ----
        #
        # Both legs must carry the REPAIRED form consistently: a build that
        # repairs the name but not the filename is RED on the second.
        tier2_home = root / "tier2"
        tier2_home.mkdir()
        company = CompanyRepository(tier2_home).create_stub(
            name="Acme  Corp", created_by="wi-022-ac-1")
        assert company.name == "Acme Corp"
        repaired_path = tier2_home / "@Acme Corp.md"
        assert repaired_path.exists(), (
            "create_stub repaired the name but not the filename — the "
            "divergence WI-029 exists to repair on the person side"
        )
        assert _stored_name(repaired_path) == "Acme Corp"


# ===========================================================================
# AC-3 — provenance
# ===========================================================================

UNLABELLED_SHAPES = (None, "", "   ", 0, 123)


def test_company_stub_records_created_by_provenance():
    """AC-3. Zero-arg and raising, per the check contract.

    NOTE, because it is the trap this criterion was rewritten to remove: a
    VERBATIM transcription of `person.py:1387-1393` is RED on the `"   "`
    fixture BY DESIGN. Person's guard is
    `if not created_by or not isinstance(created_by, str):`, and for `"   "`
    neither conjunct fires — a non-empty string is truthy and it IS a `str` — so
    Person stores three spaces verbatim. Company's guard is that two-part check
    PLUS a `.strip()`-emptiness disjunct; the widening is deliberate and D6
    parks the Person-side repair rather than this item widening into it.
    """
    # A non-empty `str` label round-trips BYTE-IDENTICALLY — no trimming.
    with temp_dir() as vault:
        CompanyRepository(vault).create_stub(name="Labelled Co",
                                             created_by="  ingester  ")
        stored = parse_frontmatter(
            (vault / "@Labelled Co.md").read_text(encoding="utf-8"))[0]
        assert stored["created_by"] == "  ingester  ", (
            "the `.strip()` is a TEST on the guard, never a transform on the "
            f"value; got {stored['created_by']!r}"
        )

    # Every UNLABELLED shape stores the literal "unknown" AND emits a WARNING
    # naming the company.
    for index, shape in enumerate(UNLABELLED_SHAPES):
        name = f"Unlabelled {index}"
        with temp_dir() as vault:
            with captured_logs(level=logging.WARNING) as records:
                CompanyRepository(vault).create_stub(name=name, created_by=shape)
            stored = parse_frontmatter(
                (vault / f"@{name}.md").read_text(encoding="utf-8"))[0]
            assert stored["created_by"] == "unknown", (
                f"created_by={shape!r} must record 'unknown'; got "
                f"{stored['created_by']!r}"
            )
            messages = [record.getMessage() for record in records]
            assert any(name in message for message in messages), (
                f"created_by={shape!r}: no WARNING naming {name!r}. The "
                "'unknown' + WARNING sentinel is what makes an unlabelled "
                f"writer findable later. Records: {messages}"
            )

    # `created_by` is present on EVERY stub, including one where the argument is
    # omitted entirely.
    with temp_dir() as vault:
        CompanyRepository(vault).create_stub(name="Omitted Co")
        stored = parse_frontmatter(
            (vault / "@Omitted Co.md").read_text(encoding="utf-8"))[0]
        assert stored["created_by"] == "unknown"

    # `auto_created` is a SEPARATE field: provenance and the workflow flag
    # cannot be collapsed into one. One is written once at creation and never
    # mutated; the other is a flag the enricher flips.
    for auto_created in (True, False):
        with temp_dir() as vault:
            CompanyRepository(vault).create_stub(
                name="Flagged Co", auto_created=auto_created, created_by="t")
            stored = parse_frontmatter(
                (vault / "@Flagged Co.md").read_text(encoding="utf-8"))[0]
            assert stored["created_by"] == "t"
            if auto_created:
                assert stored["auto_created"] is True
            else:
                assert "auto_created" not in stored


# ===========================================================================
# AC-4 — the contract is homed in the GATE, and the delta rule holds
# ===========================================================================

DIRTY = "Acme/Corp"
# Named from the value this test HOLDS, never from an ambient directory
# listing: an oracle derived from an environmental shape assumed absent is the
# WI-149 failure.
DIRTY_FIRST_SEGMENT = "Acme"

# A company Tier-1 dirty name that IS a legal filename, so a note can be planted
# with it already STORED — which is the population D4 defers repairing and which
# this item owes writability in the meantime.
STORED_DIRTY = "Acme -> Globex"


def test_company_name_contract_is_homed_in_the_gate_not_create_stub():
    """AC-4. Zero-arg and raising, per the check contract."""
    # The no-stray-directory leg is only an oracle under the DEFAULT lock home:
    # with OBSIDIAN_SCHEMAS_LOCK_DIR set to an absolute path the sentinel lands
    # OUTSIDE the vault and no `@Acme/` ever appears, so the leg would pass
    # against un-hoisted code while production fails.
    assert_default_lock_home()

    patterns = []

    # ---- arm 1: repository save, no create_stub in the frame ----
    with temp_dir() as vault:
        repo = CompanyRepository(vault)
        exc = _refusal_of(lambda: repo.save(Company(name=DIRTY)))
        patterns.append(exc.pattern)
        assert not (vault / ("@" + DIRTY_FIRST_SEGMENT)).exists(), (
            "the lock's outermost acquisition mkdirs a sentinel home defaulting "
            "to the note's own parent, so a gate at the convergence point "
            "refuses only AFTER @Acme/ is on disk"
        )
        assert not (vault / ("@" + DIRTY_FIRST_SEGMENT + ".md")).exists()

    # ---- arm 2: the raw writer, a bare dict and no model ----
    with temp_dir() as vault:
        exc = _refusal_of(lambda: write_markdown_file(
            vault / ("@" + DIRTY + ".md"),
            extra_fields={"type": "company", "name": DIRTY}))
        patterns.append(exc.pattern)
        assert not (vault / ("@" + DIRTY_FIRST_SEGMENT)).exists()
        assert not (vault / ("@" + DIRTY_FIRST_SEGMENT + ".md")).exists()

    # ---- arm 3: an in-place field update on an existing company note ----
    #
    # Its `declared_type` is derived from the note's OWN stored `type:`, parsed
    # in-lock — a different source from arm 1's `self.type_name`, and both
    # resolve to "company" on every company write.
    with temp_dir() as vault:
        path = _plant_company_note(vault / "@Existing Co.md", "Existing Co")
        exc = _refusal_of(
            lambda: update_frontmatter_field(path, "name", DIRTY))
        patterns.append(exc.pattern)
        assert _stored_name(path) == "Existing Co", "the note was left intact"

    assert len(set(patterns)) == 1, (
        f"three doors, one refusal key — got {patterns}"
    )
    assert patterns[0] == _record(COMPANY_TIER1_BRANCHES, "path_hostile").pattern

    # ---- THE DELTA RULE ----
    #
    # Without it this item BRICKS every company note already stored with a dirty
    # name — remedy-is-the-disease — and those notes are the exact population D4
    # defers repairing, so they must stay writable in the meantime.
    with temp_dir() as vault:
        path = _plant_company_note(vault / ("@" + STORED_DIRTY + ".md"),
                                   STORED_DIRTY)
        # The stored name really does match a company Tier-1 branch.
        assert _record(COMPANY_TIER1_BRANCHES,
                       "arrow_connective").matches(STORED_DIRTY)

        repo = CompanyRepository(vault)
        repo.update_fields(repo.get(STORED_DIRTY),
                           {"website": "https://acme.example"})
        update_frontmatter_field(path, "industry", "logistics")
        roundtrip_file(path)
        assert _stored_name(path) == STORED_DIRTY, (
            "three writes that do not RE-INTRODUCE the name all commit"
        )

        # …and the one write that DOES re-introduce it — with that same stored
        # value — is refused.
        exc = _refusal_of(
            lambda: update_frontmatter_field(path, "name", STORED_DIRTY))
        assert exc.pattern == _record(COMPANY_TIER1_BRANCHES,
                                      "arrow_connective").pattern
        assert _stored_name(path) == STORED_DIRTY


# ===========================================================================
# AC-5 — the audit artifact's shape
# ===========================================================================

AUDIT_PATH = REPO_ROOT / "docs" / "company-name-corpus-audit.md"

# Prerequisite 2 requires these headings BYTE-UNCHANGED: `_audit_section` slices
# on the FULL heading text, so re-wording one while adding a `Command:` block
# turns this check RED for a reason the builder cannot fix.
VAULT_WALK_HEADING = "0. The vault walk"
BRANCH_TABLE_HEADING = (
    "1. Would any proposed Tier-1 branch refuse a name that is legitimately on "
    "disk today?"
)
CENSUS_HEADING = (
    "2. What the mangler has been absorbing — a census of every character "
    "outside `[\\w\\s-]`"
)
RESIDUE_HEADING = "3. Already-mangled notes on disk (sizing D4)"
CONSUMERS_HEADING = (
    "4. Who writes company notes — call sites and mangler copies across the "
    "consumers"
)

CONSUMER_REPOS = ("HAL9000", "exocortex", "orchestrator")
SHA_PATTERN = re.compile(r"\b[0-9a-f]{40}\b")


def _audit_section(text: str, heading: str) -> str:
    """The body of '## <heading>' up to the next '## ' heading.

    The shipped precedent's helper shape
    (`tests/test_vault_path_required.py:_audit_section`), reused rather than
    re-invented so the two artifact checks slice identically.
    """
    match = re.search(
        rf"^## {re.escape(heading)}\s*$(.*?)(?=^## |\Z)",
        text,
        re.MULTILINE | re.DOTALL,
    )
    assert match is not None, f"audit artifact has no '## {heading}' section"
    return match.group(1)


def _fenced_blocks(section: str) -> list:
    return [block for block in re.findall(r"```(.*?)```", section, re.DOTALL)]


def _assert_command_and_output(section: str, label: str) -> list:
    """A `Command:` line + a non-empty fenced block, then an `Output` line + a
    non-empty fenced block. Returns the blocks."""
    assert re.search(r"^Command:", section, re.MULTILINE), (
        f"{label}: no 'Command:' field"
    )
    blocks = _fenced_blocks(section)
    assert blocks and blocks[0].strip(), (
        f"{label}: 'Command:' is not followed by a non-empty fenced block"
    )
    assert re.search(r"^Output", section, re.MULTILINE), (
        f"{label}: no 'Output' field"
    )
    assert len(blocks) > 1 and blocks[1].strip(), (
        f"{label}: 'Output' is not followed by a non-empty verbatim block"
    )
    return blocks


def _split_row(line: str) -> list:
    """Split a markdown table row on the `|` characters that are CELL
    SEPARATORS, never on one inside a backtick span.

    Load-bearing rather than fussy: two of §1's `regex` cells legitimately carry
    a `|` inside backticks — `arrow_connective`'s `->|[→⟶⇒➜↦⇨]` and the widened
    path-hostile class itself — so a naive `.split("|")` shifts every later cell
    and reports the tail of a regex where the refusal COUNT should be. That
    would turn this check RED against a CORRECT amended artifact, for a reason
    with nothing to do with the property it asserts.
    """
    cells, current, in_code = [], [], False
    for char in line.strip().strip("|"):
        if char == "`":
            in_code = not in_code
            current.append(char)
        elif char == "|" and not in_code:
            cells.append("".join(current).strip())
            current = []
        else:
            current.append(char)
    cells.append("".join(current).strip())
    return cells


def _table_rows(section: str) -> list:
    """Every `|`-delimited data row of the section's tables: not the separator,
    not a header naming the keying field."""
    rows = []
    for line in section.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = _split_row(stripped)
        if all(set(cell) <= set("-: ") for cell in cells):
            continue                      # the `|---|---|` separator
        if "branch_id" in cells[0]:
            continue                      # the header row names the key
        rows.append(cells)
    return rows


def test_company_name_corpus_audit_is_complete():
    """AC-5. Zero-arg and raising, per the check contract.

    Pins the artifact's SHAPE and makes NO subprocess, network or vault call —
    the whole check is `read_text()` plus regex. The audit's teeth are the
    `kind: precondition` write fence, not this test; this stops the audit being
    discharged as one hand-waved prose sentence, and the per-branch row forces
    the answer to the only question that can make this item harmful: does a
    branch we are about to add refuse a company that is legitimately on disk
    today.

    If an assertion here is RED because a field is ABSENT rather than malformed,
    that is Prerequisite 2's conductor amendment missing. Say so in the Build
    Log and hand off; never soften the assertion.
    """
    # (a)
    assert AUDIT_PATH.exists(), f"missing corpus-audit artifact: {AUDIT_PATH}"
    text = AUDIT_PATH.read_text(encoding="utf-8")

    # (b) the vault walk
    walk = _audit_section(text, VAULT_WALK_HEADING)
    _assert_command_and_output(walk, "the vault walk")
    scanned = re.search(r"^Notes scanned:\s*\*{0,2}(\d+)", walk, re.MULTILINE)
    assert scanned, (
        "the vault walk carries no 'Notes scanned:' line — AC-5's first clause"
    )
    assert int(scanned.group(1)) > 0

    # (c) §1, §2 and §3 each carry their own Command: / Output pair
    branch_table = _audit_section(text, BRANCH_TABLE_HEADING)
    branch_blocks = _assert_command_and_output(branch_table, "§1")
    _assert_command_and_output(_audit_section(text, CENSUS_HEADING), "§2")
    residue = _audit_section(text, RESIDUE_HEADING)
    _assert_command_and_output(residue, "§3")

    # (d) ONE ROW PER MEMBER, iterated FROM THE TUPLE so a branch with no row is
    # RED. The reverse direction is asserted at the granularity the artifact
    # actually has — every branch row names SOME member — rather than as a
    # bijection, because §1 legitimately carries TWO `path_hostile` rows (the
    # current `/`-only regex and the widened candidate).
    rows = _table_rows(branch_table)
    assert rows, "§1 carries no per-branch table"
    for record in COMPANY_TIER1_BRANCHES:
        matching = [row for row in rows if record.branch_id in row[0]]
        assert matching, (
            f"§1 has no row for branch {record.branch_id!r}"
        )
        for row in matching:
            assert len(row) >= 4, f"{record.branch_id}: row is {row}"
            assert row[2].strip("*").isdigit(), (
                f"{record.branch_id}: refusal count {row[2]!r} is not an integer"
            )
            which = row[3]
            assert which and set(which) - set("—- "), (
                f"{record.branch_id}: the `which` cell is empty or an em-dash; "
                "AC-5 requires an explicit 'no matches' marker, never an absent "
                "field"
            )
            if int(row[2].strip("*")) == 0:
                assert "no matches" in which, (
                    f"{record.branch_id}: a zero row must say 'no matches', "
                    f"not {which!r}"
                )
    known_ids = {record.branch_id for record in COMPANY_TIER1_BRANCHES}
    for row in rows:
        assert any(branch_id in row[0] for branch_id in known_ids), (
            f"§1 carries a row for a branch not in COMPANY_TIER1_BRANCHES: "
            f"{row[0]!r}"
        )

    # (e) the D4 residue count
    residue_count = re.search(r"\*\*(\d+)\*\*", residue)
    assert residue_count, (
        "§3 records no count of mangler-damaged notes sizing the D4 follow-on"
    )

    # (f) per consumer: a 40-hex HEAD, a command naming that repo's workspace,
    # and a non-empty verbatim output. §4's shared-command form satisfies this;
    # three per-repo sections are NOT required (Prerequisite 2's last bullet).
    consumers = _audit_section(text, CONSUMERS_HEADING)
    consumer_blocks = _fenced_blocks(consumers)
    assert consumer_blocks, "§4 carries no fenced blocks"
    for repo in CONSUMER_REPOS:
        head_line = next(
            (line for line in consumers.splitlines()
             if repo.lower() in line.lower() and SHA_PATTERN.search(line)),
            None,
        )
        assert head_line, f"§4: no 40-hex HEAD SHA associated with {repo}"
        workspace = f"Workspaces/{repo}"
        assert any(workspace in block for block in consumer_blocks), (
            f"§4: no scan command block naming {repo}'s workspace path"
        )
    assert any(block.strip() for block in consumer_blocks[1:]), (
        "§4: no non-empty verbatim output block"
    )

    # (g) THE PATTERN AS EXECUTED. The expected string is the constant's own
    # `.pattern`, read from the module under test and never spelled here, so the
    # row measuring this item's only NEW refusal class cannot report a number
    # produced by a different pattern than the one the build ships. Substring
    # containment rather than equality: the command carries a walk around it.
    assert any(_COMPANY_PATH_HOSTILE_RE.pattern in block
               for block in branch_blocks), (
        "§1's Command: block does not carry the widened path-hostile pattern "
        f"AS EXECUTED ({_COMPANY_PATH_HOSTILE_RE.pattern!r}). The row as "
        "committed prints an early-closing class that matches nothing, so its "
        "count is guaranteed by the pattern rather than measured from the "
        "corpus (§8.6)."
    )


# ===========================================================================
# Task 13 — the dispatcher parameterization moved no person behaviour
# ===========================================================================

TIER2_FIXTURES = ("  Dave Smith  ", "Dave  Smith", "  Dave  Smith  ", "Dave Smith")


def test_the_tier1_dispatcher_parameterization_is_behaviour_preserving_for_persons():
    """Task 13's verify. Zero-arg and raising, per the check contract."""
    validator = NameValidator()

    # The DEFAULT is still the person table — asserted over the person tuple
    # derived, never a hand list, and through BOTH public entry points with no
    # `branches` argument at all.
    for record in TIER1_BRANCHES:
        for entry_point in (validator.validate_strict, validator.clean):
            try:
                entry_point(record.specimen)
            except NameValidationError as exc:
                assert exc.pattern == record.pattern, (
                    f"{record.branch_id}: {entry_point.__name__} raised "
                    f"{exc.pattern!r}, expected {record.pattern!r}"
                )
            else:
                raise AssertionError(
                    f"{record.branch_id}'s specimen was not refused by default"
                )

    # The rebinding returns the SAME OBJECT it did before, by identity.
    assert EMPTY_BRANCH is TIER1_BRANCHES[-1]

    # `clean` and `tier2_repair` agree on a fixture set spanning both repair
    # labels and neither — the executable form of §2.3's behaviour-preservation
    # argument, which is the one place this item touches code the PERSON path
    # runs.
    for fixture in TIER2_FIXTURES:
        assert validator.clean(fixture).cleaned_name == \
            tier2_repair(fixture).cleaned_name
        assert validator.clean(fixture).repairs_applied == \
            tier2_repair(fixture).repairs_applied

    # THE PHONE-SENTINEL FIXTURE. §2.3's snippet is a PARTIAL body whose omitted
    # early return is the one line a transcription drops; without this the
    # dropped return is caught only by tests/test_repositories.py's WI-083
    # stub-creation frames, one frame away from the claim §2.3 makes. Both
    # expected values are the exact strings this test passed.
    result = validator.clean("+447739341679", allow_phone_sentinel=True)
    assert result.cleaned_name == "+447739341679"
    assert result.repairs_applied == []
    assert validator.validate_strict("447700900123",
                                     allow_phone_sentinel=True) == "447700900123"
