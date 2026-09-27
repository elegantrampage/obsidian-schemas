"""WI-032 — AC-3 across all three surfaces, plus the report-only detector.

Two checks:

* `test_whatsapp_refused_at_every_write_arm_reported_by_lint_vault_and_disclosed_append_only`
  — AC-3, named for all THREE surfaces it asserts: the write door, the lint tool
  and the frozen prose frame. A write-door test has no reason to assert anything
  about a lint tool, or about another item's prose fixture, unless the criterion
  says it does — and this one does.
* `test_whatsapp_not_storable_detector_reports_and_never_repairs` — AC-3's REPORT
  LEG, which replaced a clause that called the same consequence FREE and was
  therefore satisfied by silence.

**THE ARM SET IS DERIVED, never hand-listed**, by the existing WI-021 sweep in
`tests/derivations.py`, and asserted in scope by EQUALITY. `PersonRepository.save`
is named explicitly because that derivation excludes it BY DESIGN (it binds no
frontmatter dict and serializes nothing, so it yields zero arms), and
`write_markdown_file(entity=…)` is named beside it because the two are ONE CLASS
of arm — any arm whose payload is a whole-record PROJECTION. The `whole_record`
flag is not the discriminant; the payload containing the key is.

**EVERY MEMBER NAMED HERE IS A LITERAL OF THIS MODULE, not a corpus note.** The
corpus's own class-C member is what the `save` arm loads from a note.

Nothing here reads syntax (no `ast`): that capability is single-homed in
`tests/derivations.py`, and every scan below is imported from it.
"""

# FIRST, ahead of every package import: the conveyor may run this module's checks
# under an interpreter that is not this project's, where the imports below cannot
# resolve. A no-op under the floor command and under CI (WI-021).
from tests.ac_interpreter import ensure_project_interpreter

ensure_project_interpreter(__file__)

import importlib.util  # noqa: E402
import json  # noqa: E402
from pathlib import Path  # noqa: E402

from obsidian_schemas.errors import NameGateRefusal  # noqa: E402
from obsidian_schemas.identifier import WhatsAppJID  # noqa: E402
from obsidian_schemas.models import Person  # noqa: E402
from obsidian_schemas.name_gate import (  # noqa: E402
    WHATSAPP_KEY,
    WHATSAPP_PATTERN,
    gate_write,
)
from obsidian_schemas.name_validation import (  # noqa: E402
    COMPANY_TIER1_BRANCHES,
    TIER1_BRANCHES,
)
from obsidian_schemas.parser import parse_frontmatter  # noqa: E402
from obsidian_schemas.repositories.person import PersonRepository  # noqa: E402
from obsidian_schemas.writer import (  # noqa: E402
    update_frontmatter_field,
    update_frontmatter_fields,
    write_markdown_file,
)

from tests.derivations import (  # noqa: E402
    PACKAGE_ROOT,
    SCRIPTS_ROOT,
    auto_fixable_emitter_checks,
    frontmatter_write_arms,
    prose_lines,
    python_files_under,
)
from tests.fixture_vault import materialize_vault  # noqa: E402
from tests.support import temp_dir  # noqa: E402

LINT_VAULT_PATH = SCRIPTS_ROOT / "lint_vault.py"
PERSON_MODULE = PACKAGE_ROOT / "repositories" / "person.py"


def _load_lint_vault():
    """`scripts/` is not a package, so the CLI is loaded from its own path —
    through the SAME shape `tests/test_lint_vault_fix_rules.py:_load_lint_vault`
    already carries, never a second loader."""
    spec = importlib.util.spec_from_file_location(
        "wi032_lint_vault", LINT_VAULT_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


lint_vault = _load_lint_vault()

# ---------------------------------------------------------------------------
# The members. Every one a literal of THIS module.
# ---------------------------------------------------------------------------

#: The value this item was minted for, and a REQUIRED class-C member at every arm:
#: it is what a parse-only door accepts, which is the whole of VD-2.
KIM_FAURA_VALUE = "+44 7739 341679"

#: A REQUIRED class-E member at every arm: the value a door that asked
#: "contains `@lid`?" instead of "is the domain in the closed set?" would accept.
#: `.example` is a reserved TLD matched by SUFFIX, while `lid.example.com` is a
#: SUBDOMAIN of `example.com`, which the corpus's frozenset matches by EQUALITY.
CLASS_E_VALUE = "447700900654@lid.example"

CLASS_D_VALUE = "n/a"
STORABLE_PHONE = "447700900321@s.whatsapp.net"
STORABLE_LID = "15555550142@lid"

#: The corpus's own class-C member, on a NON-representative note — what the `save`
#: arm LOADS from a note rather than is handed.
CORPUS_CLASS_C = "447700900789@example.com"

#: The five spellings of class Ø at the FIELD level. `[""]`, `[None]` and
#: `["   "]` are deliberately NOT here: each is a populated field with a MEMBER
#: that carries no identifier, which is a caller defect and not a spelling of
#: absence, and each is REFUSED.
CLASS_O_SPELLINGS = (None, "", "   ", [])

#: The refused members, per class. Both SHAPES are driven at every arm: a bare
#: scalar `str` (the shape every live caller uses, and the shape `_shaped` passes
#: through untouched) and a list with one bad member among good ones.
REFUSED_MEMBERS = (
    ("C", KIM_FAURA_VALUE),
    ("C", CORPUS_CLASS_C),
    ("D", CLASS_D_VALUE),
    ("E", CLASS_E_VALUE),
)


def _note_text(name: str, *, whatsapp=None, extra_fields=None) -> str:
    """A person note as TEXT, so the stored SHAPE is this module's choice and not
    a model's. `json.dumps` and not `yaml.safe_dump`: the latter appends a `...`
    document-end marker after a bare scalar, which would make every plant an
    unparseable note and turn each leg silently vacuous."""
    lines = ["---", "type: person", f'name: "{name}"', "aliases: []",
             "emails: []", "phones: []"]
    if whatsapp is not None:
        lines.append(f"whatsapp: {json.dumps(whatsapp)}")
    for key, value in (extra_fields or {}).items():
        lines.append(f"{key}: {json.dumps(value)}")
    lines += ['company: ""', 'title: ""', 'linkedin: ""', 'slack: ""',
              "roles: []", 'birthday: ""', 'created: "2026-01-04"',
              "tags: [person]", "---", "", "## Notes", ""]
    return "\n".join(lines)


def _plant(vault: Path, name: str, **kwargs) -> Path:
    """Raw text, NEVER through `write_markdown_file` or `repo.save()` — those
    route through `gate_write`, which is exactly what refuses the members these
    checks need PLANTED."""
    path = vault / f"@{name}.md"
    path.write_text(_note_text(name, **kwargs), encoding="utf-8")
    return path


def _assert_refusal(call, *, expected_value, target: Path = None):
    """AC-3's three per-arm conjuncts (1) and (2), in one place so no arm gets a
    weaker version of them by being written out a second time."""
    before = target.read_bytes() if target is not None and target.exists() else None
    try:
        call()
    except NameGateRefusal as exc:
        # (1) REFUSED with a leaf of `LoudFailError` carrying the offending raw
        # value as an ATTRIBUTE and NOT in its message, under its own stable
        # `pattern` distinct from every NameValidator pattern.
        assert exc.pattern == WHATSAPP_PATTERN, (
            f"a bad JID must never be routed as a bad name; got {exc.pattern}")
        assert getattr(exc, "refused_value", None) == expected_value, (
            f"the refusal must NAME the value: expected {expected_value!r}, "
            f"carried {getattr(exc, 'refused_value', None)!r}")
        assert str(expected_value) not in str(exc), (
            "the value must reach no message — note bytes in a traceback is the "
            "hazard rule 2 of `_refuse` exists for")
        assert exc.__cause__ is None and exc.__suppress_context__, (
            "the chain must be suppressed, so no default traceback renders the "
            "refused note's bytes")
    else:                                            # pragma: no cover
        raise AssertionError(f"{expected_value!r} was NOT refused")
    # (2) the target note is byte-identical afterwards, and a target that did not
    # exist is not created.
    if target is not None:
        if before is None:
            assert not target.exists(), (
                f"a refused write created {target.name}")
        else:
            assert target.read_bytes() == before, (
                f"a refused write changed {target.name}'s bytes")


# ==========================================================================
# AC-3 — the write door, the lint tool, the frozen prose frame
# ==========================================================================

def test_whatsapp_refused_at_every_write_arm_reported_by_lint_vault_and_disclosed_append_only():
    """AC-3. Every write arm that can introduce a `whatsapp` value refuses a
    NON-EMPTY value that is not STORABLE — classes C, D and E — in BOTH shapes,
    with nothing written."""
    # ---- the pattern is DISTINCT from every NameValidator pattern, and is a
    # GATE-LOCAL LITERAL rather than a Tier-1 branch record. That is a clause
    # about WHERE and not only about distinctness: a branch record would join
    # WI-016's derived AC-3 class floor, which is asserted in BOTH directions, so
    # it would redden another item's signed criterion for a refusal that is not a
    # name judgement at all.
    branch_ids = {record.branch_id
                  for record in tuple(TIER1_BRANCHES) + tuple(COMPANY_TIER1_BRANCHES)}
    assert WHATSAPP_PATTERN not in branch_ids, (
        f"{WHATSAPP_PATTERN} must not be a NameValidator branch id")
    assert branch_ids, "the branch tables resolved empty — this leg is vacuous"

    # ---- THE ARM SET, DERIVED and asserted in scope by EQUALITY -------------
    derived = {(arm.module, arm.qualname)
               for arm in frontmatter_write_arms(
                   python_files_under(PACKAGE_ROOT, SCRIPTS_ROOT))}
    #: Each excluded arm carries a STRUCTURAL reason it cannot introduce the
    #: field, so the exclusion is a statement about the code and not a
    #: convenience.
    structurally_excluded = {
        # Re-serializes the note's OWN parsed frontmatter and introduces no
        # field: the gate is handed an EMPTY mapping and can never refuse.
        ("obsidian_schemas/writer.py", "roundtrip_file"):
            "hands the gate an empty mapping",
        # Gates the DELTA for an unrelated issue, so the payload carries no
        # `whatsapp` key at all and the new arm is never consulted.
        ("scripts/lint_vault.py", "apply_fixes"):
            "presents a delta with no whatsapp key",
    }
    introducing = derived - set(structurally_excluded)
    assert introducing == {
        ("obsidian_schemas/repositories/base.py", "BaseRepository.update_fields"),
        ("obsidian_schemas/writer.py", "write_markdown_file"),
        ("obsidian_schemas/writer.py", "update_frontmatter_field"),
        ("obsidian_schemas/writer.py", "update_frontmatter_fields"),
    }, (
        f"the DERIVED arm set moved: {sorted(introducing)}. A new arm is a new "
        f"place a malformed JID can enter the vault, so it is named here or the "
        f"criterion is not about the tree that shipped")
    assert set(structurally_excluded) <= derived, (
        "an exclusion names an arm the derivation no longer returns")
    # The two whole-record-projection arms the derivation cannot supply as ONE
    # class: `save` yields zero arms by design, and `write_markdown_file`'s entity
    # arm is already in the set above.
    assert ("obsidian_schemas/repositories/person.py",
            "PersonRepository.save") not in derived, (
        "the WI-021 wall excludes `save` as a rider, which is WHY this criterion "
        "names it explicitly")

    with temp_dir() as tmp:
        vault = materialize_vault(Path(tmp) / "vault")

        for member_class, value in REFUSED_MEMBERS:
            assert WhatsAppJID.classify(value) == member_class, (
                f"{value!r} is class {WhatsAppJID.classify(value)}, not "
                f"{member_class} — the member list is stale")
            for shape_name, payload in (("scalar", value),
                                        ("list", [STORABLE_LID, value])):
                # ---- arm: `update_frontmatter_field` -------------------------
                target = _plant(vault, f"Doorwick {member_class}{shape_name}")
                _assert_refusal(
                    lambda: update_frontmatter_field(target, WHATSAPP_KEY, payload),
                    expected_value=value, target=target)

                # ---- arm: `update_frontmatter_fields` ------------------------
                _assert_refusal(
                    lambda: update_frontmatter_fields(
                        target, {WHATSAPP_KEY: payload, "title": "archivist"}),
                    expected_value=value, target=target)

                # ---- arm: `BaseRepository.update_fields` ---------------------
                # A FRESH repository per lookup: the cache loads once on first
                # access, so a repository constructed before a plant cannot see
                # it and every leg after the first would be silently vacuous.
                repo = PersonRepository(str(vault))
                loaded = repo.get(f"Doorwick {member_class}{shape_name}")
                assert loaded is not None
                _assert_refusal(
                    lambda: repo.update_fields(loaded, {WHATSAPP_KEY: payload}),
                    expected_value=value, target=target)

                # ---- arm: `write_markdown_file` (the entity arm, which is the
                # OTHER whole-record projection) ------------------------------
                absent = vault / f"@Doorwick Absent {member_class}{shape_name}.md"
                person = Person(name=f"Doorwick Absent {member_class}{shape_name}")
                person.whatsapp = payload if isinstance(payload, list) else [payload]
                _assert_refusal(
                    lambda: write_markdown_file(absent, entity=person),
                    expected_value=value, target=absent)

                # ---- arm: `write_markdown_file` (the frontmatter arm) --------
                absent_fm = vault / f"@Doorwick FM {member_class}{shape_name}.md"
                _assert_refusal(
                    lambda: write_markdown_file(
                        absent_fm,
                        frontmatter={"type": "person",
                                     "name": f"Doorwick FM {member_class}{shape_name}",
                                     WHATSAPP_KEY: payload}),
                    expected_value=value, target=absent_fm)

            # ---- conjunct (3): a storable value in the SAME payload is
            # accepted and stored in the LIST shape -------------------------
            ok = _plant(vault, f"Doorwick Ok{member_class}")
            update_frontmatter_fields(ok, {WHATSAPP_KEY: STORABLE_PHONE,
                                           "title": "archivist"})
            frontmatter, _ = parse_frontmatter(ok.read_text(encoding="utf-8"))
            assert frontmatter[WHATSAPP_KEY] == [STORABLE_PHONE]
            assert frontmatter["title"] == "archivist"

        # ---- THE `save` ARM, pinned in BOTH directions ----------------------
        # Over an entity loaded from a note whose STORED value is class C, D or E.
        for member_class, value in (("C", CORPUS_CLASS_C), ("D", CLASS_D_VALUE),
                                    ("E", CLASS_E_VALUE)):
            stored_note = _plant(vault, f"Savewick {member_class}", whatsapp=value)
            save_repo = PersonRepository(str(vault))
            entity = save_repo.get(f"Savewick {member_class}")
            assert entity is not None, (
                "the reader must be TOLERANT — on a note that does not load this "
                "leg is vacuous rather than red")
            assert entity.whatsapp == [value], (
                "leg (b) of AC-4 is what makes this arm reachable at all")
            _assert_refusal(lambda: save_repo.save(entity),
                            expected_value=value, target=stored_note)
            # (ii) the value is STILL PRESENT on the model and in the note
            # afterwards, never silently emptied — the assertion an ERASING build
            # fails while passing every other leg here.
            assert entity.whatsapp == [value], (
                "the refusal must not have emptied the model's own field")
            assert value in stored_note.read_text(encoding="utf-8"), (
                "the refusal must not have emptied the note")

            # ---- the NEAR-MISS CONTROL: the same note stays writable through a
            # delta arm for a write that does NOT re-introduce the field, so the
            # remedy is not the disease.
            update_frontmatter_field(stored_note, "title", "archivist")
            text = stored_note.read_text(encoding="utf-8")
            assert "archivist" in text and value in text, (
                "a stored-dirty note must stay writable for every write that "
                "does not re-introduce the field")

            # ---- the other whole-record-projection arm agrees ---------------
            _assert_refusal(
                lambda: write_markdown_file(stored_note, entity=entity),
                expected_value=value, target=stored_note)

        # ---- THE CLEARING LEG, which makes the design's own repair promise
        # BUILDABLE — at every delta arm, in both of the package's spellings ---
        for member_class, value in (("C", CORPUS_CLASS_C), ("D", CLASS_D_VALUE),
                                    ("E", CLASS_E_VALUE)):
            first = _plant(vault, f"Clearwick A{member_class}", whatsapp=value)
            update_frontmatter_field(first, WHATSAPP_KEY, "")
            frontmatter, _ = parse_frontmatter(first.read_text(encoding="utf-8"))
            assert frontmatter[WHATSAPP_KEY] == [], (
                f"clearing must SUCCEED over a stored class-{member_class} value "
                f"— there is no delete affordance anywhere in the writer, so "
                f"this IS the hand-repair path the residual has")

            second = _plant(vault, f"Clearwick B{member_class}", whatsapp=value)
            clear_repo = PersonRepository(str(vault))
            entity = clear_repo.get(f"Clearwick B{member_class}")
            clear_repo.update_fields(entity, {WHATSAPP_KEY: None})
            frontmatter, _ = parse_frontmatter(second.read_text(encoding="utf-8"))
            assert frontmatter[WHATSAPP_KEY] == [], (
                "the second of the package's two clearing spellings must work too")

            # And writing a properly spelled JID OVER it succeeds, because the
            # door judges the value the WRITE CARRIES and never the value the
            # note used to hold — which is what makes a repair land everywhere.
            third = _plant(vault, f"Clearwick C{member_class}", whatsapp=value)
            update_frontmatter_field(third, WHATSAPP_KEY, STORABLE_LID)
            frontmatter, _ = parse_frontmatter(third.read_text(encoding="utf-8"))
            assert frontmatter[WHATSAPP_KEY] == [STORABLE_LID]

        # ---- THE CLASS-Ø LEG — at every arm, in every spelling, both shapes --
        # A build that refuses blank fails HERE and nowhere else in this set,
        # which is exactly why the leg exists.
        for index, spelling in enumerate(CLASS_O_SPELLINGS):
            assert WhatsAppJID.classify_field(spelling) == [], (
                f"{spelling!r} must introduce no identifier at the FIELD level")
            # the dict doors, directly on the gate
            accepted = gate_write({WHATSAPP_KEY: spelling},
                                  declared_type="person", whole_record=False)
            assert accepted[WHATSAPP_KEY] == [], (
                "class Ø is ACCEPTED at every arm and normalized to the empty "
                "collection")
            for whole in (True, False):
                gate_write({"type": "person", "name": "Ovelwick Test",
                            WHATSAPP_KEY: spelling, "emails": [], "phones": [],
                            "aliases": []},
                           declared_type="person", whole_record=whole)

            note = _plant(vault, f"Ovelwick {index}")
            update_frontmatter_field(note, WHATSAPP_KEY, spelling)
            frontmatter, _ = parse_frontmatter(note.read_text(encoding="utf-8"))
            assert frontmatter[WHATSAPP_KEY] == []

            o_repo = PersonRepository(str(vault))
            entity = o_repo.get(f"Ovelwick {index}")
            o_repo.update_fields(entity, {WHATSAPP_KEY: spelling})
            o_repo.save(entity)

            fresh = vault / f"@Ovelwick Fresh {index}.md"
            write_markdown_file(fresh, frontmatter={
                "type": "person", "name": f"Ovelwick Fresh {index}",
                WHATSAPP_KEY: spelling})
            assert fresh.exists(), "a class-Ø write must be WRITTEN, not refused"

        # A person note created from the template, with `whatsapp:` unset, is
        # written without complaint — which is the same rule from the other side.
        template = vault / "@Templwick Unset.md"
        write_markdown_file(template, entity=Person(name="Templwick Unset"))
        frontmatter, _ = parse_frontmatter(template.read_text(encoding="utf-8"))
        assert frontmatter[WHATSAPP_KEY] == []

    # ---- THE APPEND-ONLY CLAUSE, three conjuncts -------------------------
    # About WHERE the `save` arm's disclosure may be written rather than about
    # what the arm does, and a criterion rather than a build note because the two
    # builds it forbids are green on every other `check:` in this document.
    from tests.test_identity_endgame import (  # the SAME reader and the SAME
        AUTHORIZED_PROSE_OWNERS,               # tuple WI-024's own clause (e1)
        _golden,                               # takes — never re-spelled here
    )

    owner = "PersonRepository.save"
    golden = _golden("prose_surface_cut0.json")
    cut0_records = [row for row in golden["lines"] if row["owner"] == owner]
    live = {(record.owner, record.text)
            for record in prose_lines([PERSON_MODULE])}

    # (1) every Cut-0 pair owned by `PersonRepository.save` is PRESENT in the
    # final surface — which WI-024's own (e1) also asserts, restated HERE because
    # this is the criterion whose build would break it.
    missing = [row["text"] for row in cut0_records
               if (owner, row["text"]) not in live]
    assert not missing, (
        f"the disclosures must land APPEND-ONLY: {len(missing)} Cut-0 line(s) of "
        f"{owner} were edited or deleted — {missing[:3]}")

    # (2) THE COMPUTABLE FORM. The frozen criterion names a pre-build byte
    # comparison no post-build hermetic check has a referent for, so it is
    # satisfied by the two legs the document's own literals support. Both values
    # are READ at test time.
    #
    # Leg 1 catches the AUTHORIZATION itself: adding `save` to the tuple is the
    # move that makes (e1) stop protecting its 29 lines at all, and it is RED the
    # moment it is made rather than after the build has chosen which line to
    # sacrifice to (e2).
    assert owner not in AUTHORIZED_PROSE_OWNERS, (
        f"{owner} must NOT be authorized: clause (e2) then requires one of its "
        f"Cut-0 lines to be DELETED, so authorizing it buys a green by "
        f"destroying prose")
    assert "PersonRepository" not in AUTHORIZED_PROSE_OWNERS, (
        "the bare class owns the `_IDENTIFIER_PRIORITY` comment and is not "
        "authorized either")
    assert len(AUTHORIZED_PROSE_OWNERS) == 13, (
        f"`AUTHORIZED_PROSE_OWNERS` must still have exactly its thirteen "
        f"declared members; found {len(AUTHORIZED_PROSE_OWNERS)}")
    # Leg 2 catches the GOLDEN EDIT, which is the one move that would let
    # conjunct (1) be NEUTERED rather than satisfied: conjunct (1) computes its
    # expected pairs FROM this artifact, so deleting a record shrinks the domain
    # it checks. Counted as a LIST LENGTH and never as the size of an
    # `(owner, text)` SET — two identical texts collapse in a set and would hide
    # exactly the deletion this conjunct exists to catch. 29 is a FROZEN
    # population: the golden is recorded once against unchanged code, this item
    # declares it as no write target, so the item's own arc cannot grow it.
    assert len(cut0_records) == 29, (
        f"`prose_surface_cut0.json` must still carry exactly 29 records for "
        f"{owner}; found {len(cut0_records)}")

    # (3) the final surface for that owner carries at least one line that is NOT
    # a Cut-0 member — i.e. the disclosure actually LANDED. The conjunct that
    # fails the build which buys its green by writing no disclosure at all while
    # `### Examples of done` promises the refusal surface "says so".
    cut0_texts = {row["text"] for row in cut0_records}
    added = [text for (record_owner, text) in live
             if record_owner == owner and text not in cut0_texts]
    assert added, (
        f"no NEW prose line landed on {owner} — the refusal and write-back "
        f"disclosures were reverted rather than appended")
    joined = "\n".join(added)
    assert WHATSAPP_KEY in joined, (
        "the disclosure must actually be about the field it discloses")


# ==========================================================================
# AC-3's REPORT LEG — the report-only detector
# ==========================================================================

def test_whatsapp_not_storable_detector_reports_and_never_repairs():
    """AC-3's REPORT LEG's five conjuncts.

    The detector does NOT drive any member of `MUTATING_DRIVE_VAULT_POSITIONS`:
    this check calls `check_structural` directly, so no containment wall is owed
    over this module and no vault is ever written by it.
    """
    def issues_for(path: Path):
        """Driven through the TOOL's own read path — `read_vault` then
        `build_indexes` then `check_structural` — so the arm is graded on the
        VaultFile the linter really builds and not on one this check assembles."""
        vault_root = path.parent
        files = lint_vault.read_vault(vault_root)
        idx = lint_vault.build_indexes(files)
        return [i for i in lint_vault.check_structural(files, idx)
                if i.check == lint_vault.WHATSAPP_CHECK and i.file_path == path]

    with temp_dir() as tmp:
        vault = materialize_vault(Path(tmp) / "vault")

        # ---- (1) it FIRES on classes C, D and E ---------------------------
        # Over a materialized copy of the frozen corpus this check's issue set is
        # EXACTLY the one non-representative note carrying the class-C value.
        firing = []
        for path in sorted(vault.glob("*.md")):
            if issues_for(path):
                firing.append(path.name)
        assert firing == ["@Fennwick Drostane.md"], (
            f"over the corpus this check must fire on exactly the one "
            f"non-representative class-C note; fired on {firing}")

        for member_class, value in (("D", CLASS_D_VALUE), ("E", CLASS_E_VALUE)):
            assert WhatsAppJID.classify(value) == member_class
            plant = _plant(vault, f"Reportwick {member_class}", whatsapp=value)
            reported = issues_for(plant)
            assert len(reported) == 1, (
                f"class {member_class} must be REPORTED: {reported}")
            issue = reported[0]
            assert issue.severity is lint_vault.Severity.ERROR
            assert issue.category == "structural"
            assert value not in issue.message, (
                "the message carries a COUNT and CLASS LETTERS and no "
                "note-derived value — the same discipline `_refuse` keeps")
            assert member_class in issue.message

        # ---- (2) it is SILENT on class Ø in every spelling and on every
        # STORABLE value -------------------------------------------------
        for index, spelling in enumerate(CLASS_O_SPELLINGS + ("<absent>",)):
            if spelling == "<absent>":
                quiet = _plant(vault, f"Quietwick {index}")
            else:
                quiet = _plant(vault, f"Quietwick {index}", whatsapp=spelling)
            assert not issues_for(quiet), (
                f"class Ø spelling {spelling!r} must produce NO issue of this "
                f"check — the leg a detector keyed on `does not parse` fails")
        bare_key = vault / "@Quietwick Barekey.md"
        bare_key.write_text(
            _note_text("Quietwick Barekey").replace(
                'company: ""', "whatsapp:\ncompany: \"\""), encoding="utf-8")
        assert not issues_for(bare_key), (
            "a BARE valueless key loads as YAML null and is class Ø")
        for value in (STORABLE_PHONE, STORABLE_LID):
            assert WhatsAppJID.parse(value).is_storable
            quiet = _plant(vault, f"Quietwick S{value[:4]}", whatsapp=value)
            assert not issues_for(quiet)
        # The representative's own storable value, from the corpus itself.
        assert not issues_for(vault / "@Thrandell Ibberly.md")

        # ---- (3) it judges BOTH stored shapes ----------------------------
        # `lint_vault` reads RAW frontmatter and both shapes exist on disk
        # throughout the migration window — F2's inert-arm trap one tool over.
        scalar = _plant(vault, "Shapewick Scalar", whatsapp=CLASS_D_VALUE)
        listed = _plant(vault, "Shapewick Listed",
                        whatsapp=[STORABLE_LID, CLASS_D_VALUE])
        for path in (scalar, listed):
            assert len(issues_for(path)) == 1, (
                f"{path.name}: an arm that inspected only lists is silent for "
                f"exactly the population this item exists for")

        # ---- (4) `auto_fixable is False` PER ISSUE, and this check is NOT a
        # member of `auto_fixable_emitter_checks` -------------------------
        every = []
        for path in sorted(vault.glob("*.md")):
            every.extend(issues_for(path))
        assert every, "the per-issue leg resolved no issues at all"
        for issue in every:
            assert issue.auto_fixable is False, (
                "left at its `False` default, so the note never enters "
                "`apply_fixes` and `--fix`'s four-bucket delta contract is "
                "untouched while it still repairs that note's OTHER issues")
        emitters = auto_fixable_emitter_checks([LINT_VAULT_PATH])
        assert emitters, "the emitter derivation resolved nothing — vacuous"
        assert lint_vault.WHATSAPP_CHECK not in emitters, (
            "a report-only rule is outside that derived set by construction, "
            "which is also why it owes no repair oracle in the WI-026 floor")

        # ---- (5) the report NEVER travels as `NOT_RENAMEABLE_MARKER` ------
        for issue in every:
            assert lint_vault.NOT_RENAMEABLE_MARKER not in issue.message, (
                "the build that widens the existing marker instead is green on "
                "everything else in this set while putting a false `repair the "
                "field` message onto a defect that is a FILENAME, and moving "
                "live rows against WI-029's committed bracket")
        assert lint_vault.WHATSAPP_CHECK != "stem_name_divergence"
        # The divergence module's own marked-set equality stays green and
        # untouched: it filters on `issue.check`, so a new check name is
        # invisible to it.
        from tests.test_stem_name_divergence_detector import _divergence_issues
        assert _divergence_issues is not None

        # ---- the `except IdentifierError` arm EXERCISED rather than assumed --
        nested = vault / "@Nestwick Container.md"
        nested.write_text(
            _note_text("Nestwick Container").replace(
                'company: ""', 'whatsapp: {"a": "b"}\ncompany: ""'),
            encoding="utf-8")
        reported = issues_for(nested)
        assert len(reported) == 1, (
            "a nested container under `whatsapp:` is a shape the classifier "
            "REFUSES, and a tool whose job is finding malformed notes must not "
            "crash on one")
        assert "unclassifiable" in reported[0].message
