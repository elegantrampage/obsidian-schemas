"""WI-032 — the storage predicates, the index, the resolution door, the shapes.

Four checks: Task 2's predicate/classifier battery, AC-1 (the phone pivot), AC-2
(the resolution door) and AC-4 (the read/write shapes).

**EVERY ORACLE IS A CALL.** The fixture space is a table of RAW values that this
module classifies BY CALLING `WhatsAppJID.parse` and the STORABLE property, and
every expected value is derived from those calls — never from a literal read off
the same source as the implementation, and never from a restated shape. Widening
`STORABLE_DOMAINS` later therefore joins this sweep automatically.

**THE WHERE CLAUSE is honoured here rather than described.** Classes A, D and E
and every boundary probe are literals of THIS module's own temp vault and are
never written into `tests/fixtures/vault/`: WI-016's privacy wall scores every
email-shaped token in that corpus's reach against RFC 2606 / RFC 6761 and
`s.whatsapp.net` is a real domain no RFC reserves, so class A is structurally
inadmissible there — STORABLE is membership of `{"s.whatsapp.net", "lid"}`, so a
phone-bearing storable value carries exactly that domain by definition. Class B is
the corpus's person round-trip representative and class C a non-representative
corpus note; class Ø is the corpus's own 21 empty-valued notes.

Nothing here reads syntax (no `ast`): that capability is single-homed in
`tests/derivations.py`. Every skip reason is IMPORTED from
`obsidian_schemas/repositories/base.py` and never typed, because the legal homes
for such a literal are pinned to exactly two files by EQUALITY.
"""

# FIRST, ahead of every package import: the conveyor may run this module's checks
# under an interpreter that is not this project's, where the imports below cannot
# resolve. A no-op under the floor command and under CI (WI-021).
from tests.ac_interpreter import ensure_project_interpreter

ensure_project_interpreter(__file__)

import json  # noqa: E402
from pathlib import Path  # noqa: E402

import yaml  # noqa: E402

from obsidian_schemas.errors import NameGateRefusal  # noqa: E402
from obsidian_schemas.identifier import (  # noqa: E402
    IdentifierError,
    WhatsAppJID,
)
from obsidian_schemas.models import Person  # noqa: E402
from obsidian_schemas.name_gate import WHATSAPP_PATTERN  # noqa: E402
from obsidian_schemas.parser import parse_frontmatter, parse_to_model  # noqa: E402
from obsidian_schemas.repositories.base import SCHEMA_DRIFT  # noqa: E402
from obsidian_schemas.repositories.person import PersonRepository  # noqa: E402
from obsidian_schemas.writer import (  # noqa: E402
    update_frontmatter_field,
    write_markdown_file,
)

from tests.fixture_vault import NOTES, SKIPS, materialize_vault  # noqa: E402
from tests.support import temp_dir  # noqa: E402

# ---------------------------------------------------------------------------
# The class table, as RAW values. Its CELLS are computed by calling the
# predicates, never asserted from this side.
# ---------------------------------------------------------------------------

#: The representative's storable `@lid` — class B, and the ONE corpus member the
#: write door accepts. Its digits match the corpus's reserved NANP 555-01xx
#: pattern and no member of that block appears anywhere in the corpus.
CORPUS_LID = "15555550142@lid"

#: The 10-digit counterpart of `CORPUS_LID`'s digits. NOBODY in the vault holds
#: this number, and today `get_by_phone` answers it with the lid's owner through
#: the permanent fuzzy arm. That is the corruption AC-1 retires.
CORPUS_LID_TEN_DIGIT = "5555550142"

#: The corpus's class-C member, on a NON-representative note.
CORPUS_CLASS_C = "447700900789@example.com"

#: Temp-vault-only literals. Every digit run is an UNUSED member of the Ofcom
#: drama block or of NANP 555-01xx, both of which the corpus's phone predicate
#: reserves and neither of which the corpus already claims.
PLANT_A = "447700900321@s.whatsapp.net"
PLANT_D = "notaphone@s.whatsapp.net"
PLANT_E = "447700900654@lid.example"

#: The value this item was minted for: written for a real person through the PATCH
#: door and repaired by hand. `parse` ACCEPTS it, which is why the door needs the
#: second, narrower question.
KIM_FAURA_VALUE = "+44 7739 341679"

#: The named boundary-probe list AC-1's exhaustiveness is scoped over, beside the
#: enumerated table and the corpus. Literals of THIS module, never of the corpus.
BOUNDARY_PROBES = (
    PLANT_E,
    "123@lid.example.com",
    PLANT_D,
    CORPUS_CLASS_C,
    KIM_FAURA_VALUE,
    "",
    None,
    "   ",
)

#: `raw -> the cell this module EXPECTS`, used only to prove the classifier files
#: each cell non-empty. The classifier is what DECIDES; this is the enumeration
#: the exhaustiveness claim is scoped to.
TABLE = (
    (None, "Ø"),
    ("", "Ø"),
    ("   ", "Ø"),
    (PLANT_A, "A"),
    (CORPUS_LID, "B"),
    (KIM_FAURA_VALUE, "C"),
    (CORPUS_CLASS_C, "C"),
    ("n/a", "D"),
    ("ask Kate", "D"),
    (PLANT_D, "D"),
    (PLANT_E, "E"),
    ("123@lid.example.com", "E"),
)


def _cells() -> dict:
    """The table INVERTED, with each member's class taken from the classifier."""
    out: dict = {}
    for raw, _declared in TABLE:
        out.setdefault(WhatsAppJID.classify(raw), []).append(raw)
    return out


def _note_text(name: str, *, whatsapp=None, phones=None, extra="") -> str:
    """A person note, built as TEXT so the stored SHAPE is this module's choice
    and not a model's. `whatsapp` omitted means the key is ABSENT; passing the
    sentinel `"<bare>"` writes a bare valueless key, which YAML loads as null."""
    # `json.dumps` and NOT `yaml.safe_dump`: the latter appends a `...`
    # document-end marker after a bare scalar, which makes the note's frontmatter
    # unparseable and would silently turn every plant into a skipped note. JSON is
    # valid YAML flow style, so one call renders both a scalar and a list.
    lines = ["---", "type: person", f'name: "{name}"', "aliases: []", "emails: []"]
    lines.append(f"phones: {json.dumps(phones or [])}")
    if whatsapp == "<bare>":
        lines.append("whatsapp:")
    elif whatsapp is not None:
        lines.append(f"whatsapp: {json.dumps(whatsapp)}")
    lines += ['company: ""', 'title: ""', 'linkedin: ""', 'slack: ""',
              "roles: []", 'birthday: ""', 'created: "2026-01-04"',
              "tags: [person]", "---", ""]
    return "\n".join(lines) + extra


def _load_model(path: Path):
    """The note's bytes through the package's own two load steps. Returns the
    model; `parse_to_model` returns `(model, extra)`."""
    frontmatter, _ = parse_frontmatter(path.read_text(encoding="utf-8"))
    model, _extra = parse_to_model(frontmatter, path=path)
    return model


def _plant(vault: Path, name: str, **kwargs) -> Path:
    """Write one plant note as raw text. NEVER through `write_markdown_file` or
    `repo.save()` — those route through `gate_write`, which is exactly what
    refuses the class-C, class-D and class-E members these checks need PLANTED."""
    path = vault / f"@{name}.md"
    path.write_text(_note_text(name, **kwargs), encoding="utf-8")
    return path


# ==========================================================================
# Task 2 — the two predicates and the classifier
# ==========================================================================

def test_whatsapp_storable_predicate_and_classifier():
    """`jid_domain`, `is_storable`, `classify` and `classify_field`, every oracle
    a CALL.

    `parse` is UNCHANGED and is the REACH predicate; this grades the second,
    narrower question storage asks of the SAME type.
    """
    # ---- `jid_domain` reads the NORMALIZED string, so case is free -----------
    assert WhatsAppJID.parse(PLANT_A).jid_domain == "s.whatsapp.net"
    assert WhatsAppJID.parse(PLANT_A.upper()).jid_domain == "s.whatsapp.net"
    assert WhatsAppJID.parse(PLANT_A.upper()).is_storable, (
        "the domain is computed off `self.jid`, which `parse` lowercases, so "
        "case-insensitivity is free and needs no second rule")
    assert WhatsAppJID.parse(CORPUS_LID).jid_domain == "lid"
    # `""` for a value with no `@` at all — the Kim Faura shape.
    assert WhatsAppJID.parse(KIM_FAURA_VALUE).jid_domain == ""

    # ---- MEMBERSHIP of the closed set, never a suffix test -------------------
    assert WhatsAppJID.parse(PLANT_A).is_storable
    assert WhatsAppJID.parse(CORPUS_LID).is_storable
    assert not WhatsAppJID.parse(CORPUS_CLASS_C).is_storable, (
        "under a bare `has a non-empty suffix` reading this becomes storable, "
        "class C empties and class E ceases to exist")
    assert not WhatsAppJID.parse("123@lid.example.com").is_storable
    assert not WhatsAppJID.parse(KIM_FAURA_VALUE).is_storable, (
        "the value this item was minted for parses and must not be storable")
    assert WhatsAppJID.STORABLE_DOMAINS == frozenset({"s.whatsapp.net", "lid"})

    # ---- the classification ORDER, which is the whole content of class Ø -----
    # `parse` raises on `""` and `None` through the same two lines it raises on
    # `"n/a"` with, so a classifier that asks the predicates FIRST files the live
    # corpus's 1025 default-valued notes as a defect class.
    for blank in (None, "", "   "):
        try:
            WhatsAppJID.parse(blank)
        except IdentifierError:
            pass
        else:                                       # pragma: no cover
            raise AssertionError(f"`parse` no longer raises on {blank!r} — the "
                                 f"ORDER assertion below has lost its premise")
        assert WhatsAppJID.classify(blank) == WhatsAppJID.CLASS_ABSENT, (
            f"{blank!r} must be filed as class Ø and never as D: the emptiness "
            f"test precedes BOTH predicate calls")

    # ---- the two predicates INDEPENDENT in BOTH directions ------------------
    assert WhatsAppJID.parse(PLANT_D.replace("notaphone", "447700900321")).is_storable
    try:
        WhatsAppJID.parse(PLANT_D)
    except IdentifierError:
        pass
    else:                                            # pragma: no cover
        raise AssertionError("a value carrying a JID domain must still be able "
                             "to fail `parse` — otherwise the predicates are "
                             "not independent")
    assert WhatsAppJID.classify(PLANT_D) == "D", (
        "carries a JID domain and does not parse — a build that implemented "
        "storability as `parses` is RED here")
    assert WhatsAppJID.classify(PLANT_E) == "E", (
        "parses via the `@lid` SUBSTRING and is not storable — a build that "
        "implemented storability as `contains @lid` is RED here")

    # ---- the container refusal, closed at the LEAF -------------------------
    try:
        WhatsAppJID.classify([PLANT_A])
    except IdentifierError:
        pass
    else:                                            # pragma: no cover
        raise AssertionError(
            "`parse([PLANT_A])` SUCCEEDS with the right phone digits, recovered "
            "out of the list's repr — a container reaching the per-value "
            "classifier must be REFUSED rather than answered")

    # ---- `classify_field` over BOTH stored shapes --------------------------
    for empty in (None, "", "   ", []):
        assert WhatsAppJID.classify_field(empty) == [], (
            f"{empty!r} introduces no identifier, so there is no member for any "
            f"arm to judge")
    assert WhatsAppJID.classify_field(CORPUS_LID) == ["B"]
    assert WhatsAppJID.classify_field([CORPUS_LID]) == ["B"]
    assert WhatsAppJID.classify_field([CORPUS_LID, "n/a", PLANT_E]) == ["B", "D", "E"], (
        "in stored ORDER, one class per stored member — the positional "
        "correspondence the gate's refusal uses to NAME the offending value")
    # A blank MEMBER inside a populated field is NOT a spelling of absence.
    assert WhatsAppJID.classify_field([""]) == [WhatsAppJID.CLASS_ABSENT]


# ==========================================================================
# AC-1 — a JID's digits enter `_phone_index` IFF `phone_digits` is non-empty
# ==========================================================================

def test_lid_digits_never_enter_the_phone_index():
    """AC-1. The discriminating member is PLANTED rather than hoped for.

    The frozen corpus has zero `@lid`, zero unparseable and zero storable-JID
    members of its own and would green a build that changed nothing.
    """
    cells = _cells()

    # ---- every cell asserted NON-EMPTY, so one that loses its only member is
    # RED rather than vacuously green -------------------------------------
    for cell in WhatsAppJID.CLASSES:
        assert cells.get(cell), (
            f"cell {cell} has no member — a cell that empties makes every leg "
            f"below vacuously green")

    # ---- TOTAL, with NO fall-through bucket, at the reach it actually has ----
    # (i) the enumerated table.
    for raw, declared in TABLE:
        assert WhatsAppJID.classify(raw) == declared, (
            f"{raw!r} classified {WhatsAppJID.classify(raw)}, table says {declared}")
    # (ii) every `whatsapp` value in the fixture corpus, classified without
    # exception.
    corpus_values = []
    for spec in NOTES.values():
        # A skip specimen declares raw bytes and no field mapping at all, so it
        # has no stored value for this leg to classify.
        if spec.declared_type != "person" or not spec.fields:
            continue
        corpus_values.append(spec.fields.get("whatsapp"))
    assert corpus_values, "the corpus declares no person notes — leg (ii) is vacuous"
    for stored in corpus_values:
        classes = WhatsAppJID.classify_field(stored)
        for member_class in classes:
            assert member_class in WhatsAppJID.CLASSES, (
                f"{stored!r} filed outside the declared table")
    # (iii) the named boundary-probe list.
    for probe in BOUNDARY_PROBES:
        assert WhatsAppJID.classify(probe) in WhatsAppJID.CLASSES

    # ---- the two predicates INDEPENDENT both ways, on planted members -------
    assert WhatsAppJID.classify(PLANT_D) == "D"
    assert WhatsAppJID.classify(PLANT_E) == "E"

    with temp_dir() as tmp:
        vault = materialize_vault(Path(tmp) / "vault")

        # The WHERE clause's three receiver constraints, asserted as PROPERTIES
        # of the manifest and NOT only as a filename — the receiver is a fixture
        # that can be renamed while the contracts cannot.
        receiver = None
        for name, spec in NOTES.items():
            if spec.declared_type != "person" or not spec.fields:
                continue
            if spec.fields.get("whatsapp") != [CORPUS_CLASS_C]:
                continue
            receiver = (name, spec)
        assert receiver is not None, (
            f"no corpus person note declares the class-C value {CORPUS_CLASS_C}")
        receiver_name, receiver_spec = receiver
        assert receiver_name not in SKIPS["person"], (
            "the class-C receiver must LOAD, so never one of the three declared "
            "person skip specimens: on a skipped note this check's own "
            "`get_by_phone` leg is vacuous rather than red")
        assert not receiver_spec.shape_classes and not receiver_spec.verdict, (
            "the class-C receiver must declare NO shape_classes and no verdict: "
            "the census verdict loop writes a shape-class specimen's whole "
            "declared field set through the gated door and asserts the refusal "
            "`pattern` equals the DECLARED name pattern, so a non-storable "
            "`whatsapp` there makes WHICH refusal fires depend on where the new "
            "gate arm sits relative to the name arm")
        stem = Path(receiver_name).stem
        stem = stem[1:] if stem.startswith("@") else stem
        assert stem == receiver_spec.fields["name"], (
            "the class-C receiver must NOT be stem-divergent, which the first "
            "two constraints do not imply: a divergent note routes its whole "
            "record through `_gate_refusal_pattern` and puts the same "
            "insertion-point question inside a THIRD item's set equality")

        # The representative is asserted STORABLE-CLEAN rather than left to
        # review: two tests write its whole field set through the gated
        # whole-record arm asserting NO refusal.
        representative = [spec for spec in NOTES.values()
                          if spec.roundtrip_representative
                          and spec.declared_type == "person"]
        assert len(representative) == 1
        for value in representative[0].fields["whatsapp"]:
            assert WhatsAppJID.parse(value).is_storable, (
                "the corpus must hold NO class-A and NO class-C member on the "
                "person round-trip representative")

        repo = PersonRepository(str(vault))
        repo._ensure_loaded()

        # ---- classes A and C: the index key is EXACTLY `phone_digits` --------
        plant_a = _plant(vault, "Plantwick Aynesford", whatsapp=PLANT_A)
        plant_c = _plant(vault, "Plantwick Cinderhove", whatsapp=KIM_FAURA_VALUE)
        plant_d = _plant(vault, "Plantwick Dunmarrow", whatsapp="n/a")
        plant_e = _plant(vault, "Plantwick Eskravyn", whatsapp=PLANT_E)
        plant_o = _plant(vault, "Plantwick Ovelbrook", whatsapp="")
        assert plant_a.exists() and plant_d.exists() and plant_o.exists()

        fresh = PersonRepository(str(vault))
        fresh._ensure_loaded()

        for path, value in ((plant_a, PLANT_A), (plant_c, KIM_FAURA_VALUE)):
            digits = WhatsAppJID.parse(value).phone_digits
            assert fresh._phone_index.get(digits) is not None, (
                f"a phone-bearing JID's digits must key `_phone_index`: {value}")
            found = fresh.get_by_phone(digits)
            assert found is not None and found.name == path.stem[1:], (
                f"class {WhatsAppJID.classify(value)} is in the phone arm "
                f"deliberately — a bare number in the field IS a stored phone "
                f"number and resolution stays liberal")

        # ---- classes B and E: NO key derived from the value's digits ---------
        for value in (CORPUS_LID, PLANT_E):
            parsed = WhatsAppJID.parse(value)
            assert parsed.phone_digits == "", (
                f"{value} must carry no phone digits, or this leg is testing "
                f"something else")
            leading = "".join(ch for ch in value.split("@")[0] if ch.isdigit())
            assert fresh._phone_index.get(leading) is None, (
                f"a lid's opaque internal digits must not be indexed as a "
                f"telephone number: {value}")
        assert fresh.get_by_phone(CORPUS_LID_TEN_DIGIT) is None, (
            "a query for a number NOBODY holds must return None — today it "
            "returns the lid's owner through the permanent fuzzy arm")

        # ---- class D: the NARROWING arm -------------------------------------
        # There is no right phone for a value the parser refuses, so the
        # assertion is the declared marker.
        assert fresh._phone_index.get("n/a") is None
        skipped = {Path(s.path).name for s in fresh.skipped_notes}
        assert plant_d.name not in skipped, (
            "a class-D value must not make its note unloadable — the reader is "
            "tolerant and drops nothing")
        d_person = fresh.get("Plantwick Dunmarrow")
        assert d_person is not None and d_person.whatsapp == ["n/a"]

        # ---- class Ø: the same narrowing arm PLUS no identifier at all -------
        o_person = fresh.get("Plantwick Ovelbrook")
        assert o_person is not None and o_person.whatsapp == []
        projected = fresh._project_identifiers(o_person)
        assert not [i for i in projected if isinstance(i, WhatsAppJID)], (
            "class Ø must project NO identifier of any kind from the field — a "
            "build that filed Ø as D satisfies the no-key half and fails "
            "nothing else in this criterion")

        # ---- `_remove_entity_from_indexes` is the EXACT INVERSE --------------
        before = dict(fresh._phone_index)
        for value, name in ((PLANT_A, "Plantwick Aynesford"),
                            (KIM_FAURA_VALUE, "Plantwick Cinderhove"),
                            (CORPUS_LID, None), (PLANT_E, "Plantwick Eskravyn"),
                            ("n/a", "Plantwick Dunmarrow"),
                            ("", "Plantwick Ovelbrook")):
            if name is None:
                continue
            entity = fresh.get(name)
            assert entity is not None
            fresh._remove_entity_from_indexes(entity, name.lower())
        for value in (PLANT_A, KIM_FAURA_VALUE):
            digits = WhatsAppJID.parse(value).phone_digits
            assert digits not in fresh._phone_index, (
                f"the inverse left an orphan key for {value}")
        assert set(before) - set(fresh._phone_index), (
            "the inverse removed nothing at all — a vacuously green inverse")


# ==========================================================================
# AC-2 — every PARSEABLE JID form has exactly ONE public resolution door
# ==========================================================================

def test_whatsapp_jid_resolution_door_over_every_accepted_form():
    """AC-2, over the same derived table. The expected entity is computed from
    `WhatsAppJID.parse(v).key` plus the fixture's own note-to-value map."""
    from obsidian_schemas.repositories.person import _RESOLVE_CASCADE_ORDER

    # ---- the cascade label, asserted PRESENT and ranked ahead of `phone` -----
    assert "whatsapp-jid" in _RESOLVE_CASCADE_ORDER, (
        "without the label an unknown `matched_via` sorts LAST, which is the "
        "wrong answer when an exact `jid:` hit ties a fuzzy phone hit")
    order = list(_RESOLVE_CASCADE_ORDER)
    assert order.index("whatsapp-jid") < order.index("phone")
    assert order[:order.index("whatsapp-jid")] == ["exact-name", "alias", "email"], (
        "every existing relative order must be byte-identical")

    with temp_dir() as tmp:
        vault = materialize_vault(Path(tmp) / "vault")
        note_to_value = {
            "Plantwick Aynesford": PLANT_A,          # class A
            "Plantwick Cinderhove": KIM_FAURA_VALUE,  # class C
            "Plantwick Eskravyn": PLANT_E,            # class E
        }
        for name, value in note_to_value.items():
            _plant(vault, name, whatsapp=value)
        _plant(vault, "Plantwick Dunmarrow", whatsapp="n/a")     # class D
        # Class B is the corpus's representative and arrives for free.
        note_to_value["Thrandell Ibberly"] = CORPUS_LID

        repo = PersonRepository(str(vault))
        repo._ensure_loaded()

        for name, value in note_to_value.items():
            parsed = WhatsAppJID.parse(value)
            expected_key = parsed.key

            # (1) the public door.
            person = repo.get_by_identifier(parsed)
            assert person is not None and person.name == name, (
                f"`get_by_identifier` must answer {value} ({expected_key}) with "
                f"{name}; got {None if person is None else person.name}")

            # (2) the cascade.
            resolved = repo.resolve(value)
            assert resolved is not None and resolved.name == name, (
                f"the cascade must answer {value} with {name}")

            if parsed.phone_digits:
                assert expected_key.startswith("phone:"), (
                    f"classes A and C resolve through the `phone:` key; "
                    f"{value} keyed {expected_key}")
            else:
                assert expected_key.startswith("jid:"), (
                    f"classes B and E resolve through the `jid:` key the index "
                    f"ALREADY builds; {value} keyed {expected_key}")

        # ---- class C RESOLVES even though AC-3 refuses to STORE it -----------
        c_person = repo.get_by_identifier(WhatsAppJID.parse(KIM_FAURA_VALUE))
        assert c_person is not None, (
            "a build that wired the STORABLE predicate into the RESOLVER makes "
            "class C unresolvable and is RED here — resolution stays liberal")
        assert not WhatsAppJID.parse(KIM_FAURA_VALUE).is_storable

        # ---- class E named alongside B, from the same side -------------------
        e_person = repo.get_by_identifier(WhatsAppJID.parse(PLANT_E))
        assert e_person is not None and e_person.name == "Plantwick Eskravyn", (
            "resolution keys on `parse` and class E parses")
        assert not WhatsAppJID.parse(PLANT_E).is_storable

        # ---- class D: the NARROWING arm -------------------------------------
        try:
            WhatsAppJID.parse("n/a")
        except IdentifierError:
            pass
        else:                                        # pragma: no cover
            raise AssertionError("class D must not be constructible as a typed "
                                 "identifier")
        assert repo.resolve("n/a") is None or repo.resolve("n/a").name != "Plantwick Dunmarrow"

        # ---- class Ø: a POSITION pin, not a behaviour claim ------------------
        # The behaviour is ALREADY true — `resolve_all` bails out on a blank or
        # whitespace-only query BEFORE step 1 runs — so what this guards is that
        # the new step is inserted BELOW that guard and never above it.
        for blank in ("", "   "):
            assert repo.resolve_all(blank) == [], (
                "the blank-query bail-out must still precede EVERY cascade step "
                "including the new one; 21 of 22 corpus notes carry an empty "
                "`whatsapp`, so a step comparing stored values instead of keys "
                "would match ~the whole corpus")

        # ---- guard 1: the lid answer comes from the IDENTIFIER INDEX ---------
        lid = WhatsAppJID.parse(CORPUS_LID)
        assert lid.key in repo._identifier_index, (
            "the lid must be reachable through the index the projection builds")
        assert repo.get_by_phone(CORPUS_LID_TEN_DIGIT) is None, (
            "a build that resolved lids by re-normalizing digits would green an "
            "answer-shaped test while preserving exactly the phone confusion "
            "AC-1 removes")

        # ---- guard 2: the new label OUTRANKS `phone`, proven by a TIE --------
        # A note holding the lid, and a DIFFERENT note whose phone fuzzily
        # matches the same digit run. The lid's owner must win.
        _plant(vault, "Plantwick Tiebreak", phones=["+1 " + CORPUS_LID_TEN_DIGIT])
        tie_repo = PersonRepository(str(vault))
        tie_repo._ensure_loaded()
        answer = tie_repo.resolve(CORPUS_LID)
        assert answer is not None and answer.name == "Thrandell Ibberly", (
            "an exact `jid:` hit must outrank a fuzzy phone hit")

        # ---- guard 3: README's documented `get_by_phone` route still holds ---
        digits = WhatsAppJID.parse(PLANT_A).phone_digits
        via_jid = tie_repo.get_by_phone(PLANT_A)
        assert via_jid is not None and via_jid.name == "Plantwick Aynesford", (
            "looking a phone-bearing JID up through `get_by_phone` is DOCUMENTED "
            "behaviour and the fix must not silently retract a published API")
        assert tie_repo.get_by_phone(digits) is not None


# ==========================================================================
# AC-4 — both shapes load, nothing is dropped, one shape is written
# ==========================================================================

def test_whatsapp_read_write_shape_and_no_silent_drop():
    """AC-4's four legs, over every cell of the six-cell table."""
    with temp_dir() as tmp:
        vault = Path(tmp) / "vault"
        vault.mkdir(parents=True)

        # ---- (a) TOLERANT READ ---------------------------------------------
        scalar = _plant(vault, "Readwick Scalarine", whatsapp=CORPUS_LID)
        listed = _plant(vault, "Readwick Listerby", whatsapp=[CORPUS_LID])
        empty = _plant(vault, "Readwick Emptonby", whatsapp="")
        absent = _plant(vault, "Readwick Absentia")
        bare = _plant(vault, "Readwick Barekey", whatsapp="<bare>")

        for path in (scalar, listed, empty, absent, bare):
            model = _load_model(path)
            assert model is not None, f"{path.name} did not load"

        assert _load_model(scalar).whatsapp == [CORPUS_LID]
        assert _load_model(listed).whatsapp == [CORPUS_LID], (
            "both stored shapes must present the SAME field value")
        for path in (empty, absent, bare):
            model = _load_model(path)
            assert model.whatsapp == [], (
                f"{path.name} must present the empty collection — that is class "
                f"Ø on the READ side")

        # The bare-key spelling is the one that does NOT work today: it loads as
        # YAML null and the old `str` annotation rejected it, so such a note
        # raised and landed on the load skip surface — INVISIBLE rather than
        # empty. The skip reason is IMPORTED, never typed.
        bare_repo = PersonRepository(str(vault))
        bare_repo._ensure_loaded()
        drifted = [s for s in bare_repo.skipped_notes if s.reason == SCHEMA_DRIFT]
        assert bare.name not in {Path(s.path).name for s in drifted}, (
            f"the bare valueless key must no longer land on the "
            f"{SCHEMA_DRIFT} skip surface")

        # Leg (a)'s class-Ø ROUND TRIP goes THROUGH a gated delta write and
        # back, so the read side and the write side MEET — a build accepting
        # empty on read while refusing it on write fails HERE too.
        update_frontmatter_field(empty, "whatsapp", "")
        round_tripped = _load_model(empty)
        assert round_tripped.whatsapp == []
        frontmatter, _ = parse_frontmatter(empty.read_text(encoding="utf-8"))
        assert frontmatter["whatsapp"] == [], (
            "the gate's ONE WRITTEN SHAPE turns the accepted empty value into "
            "the empty list")

        # ---- (b) NO SILENT DROP --------------------------------------------
        for name, value, parses in (("Dropwick Cinderline", KIM_FAURA_VALUE, True),
                                    ("Dropwick Dunmore", "n/a", False),
                                    ("Dropwick Eskerly", PLANT_E, True)):
            path = _plant(vault, name, whatsapp=value)
            raw = path.read_text(encoding="utf-8")
            model = _load_model(path)
            assert value in raw
            assert model.whatsapp == [value], (
                f"the RAW stored string must still be on the loaded model for "
                f"class {WhatsAppJID.classify(value)} — a reader that filtered "
                f"unparseable values out of the stored field fails here, and "
                f"this is the leg that makes AC-3's `save` arm reachable at all")
            typed = [j.jid for j in model.whatsapp_jids]
            if parses:
                assert typed == [WhatsAppJID.parse(value).jid], (
                    f"classes C and E parse and appear in the typed view — they "
                    f"are merely unstorable; a build that filtered the typed "
                    f"view on STORABILITY is RED here")
            else:
                assert typed == [], (
                    "class D does not parse and appears only in the raw field")

        # ---- (c) ONE WRITTEN SHAPE, asserted BOTH ways over a class-D note ---
        d_note = _plant(vault, "Shapewick Dunhollow", whatsapp="n/a")
        before = d_note.read_bytes()

        # An unrelated delta write leaves its scalar bytes untouched, because the
        # merge is over the RAW parsed frontmatter where `whatsapp` is still the
        # stored scalar.
        update_frontmatter_field(d_note, "title", "archivist")
        after = d_note.read_text(encoding="utf-8")
        assert "whatsapp: n/a" in after or 'whatsapp: "n/a"' in after or \
               "whatsapp: 'n/a'" in after, (
            "a scalar-carrying note written for an unrelated reason must NOT be "
            "silently rewritten")
        assert "archivist" in after

        # A write that RE-INTRODUCES the field is refused with the bytes
        # unchanged. On a note in the residual there IS no succeeding write that
        # introduces the field, which is why leg (c) is SILENT about it rather
        # than violated by it.
        before = d_note.read_bytes()
        try:
            update_frontmatter_field(d_note, "whatsapp", "n/a")
        except NameGateRefusal as exc:
            assert exc.pattern == WHATSAPP_PATTERN
        else:                                        # pragma: no cover
            raise AssertionError("re-introducing a class-D value must be refused")
        assert d_note.read_bytes() == before, (
            "the bytes must be unchanged, so no build can read `one written "
            "shape` as a licence to convert a residual note")

        # No `!!python/object` tag anywhere in a written note's bytes — the one
        # assertion that catches a typed object reaching `yaml.dump` whichever
        # way the implementation goes.
        good = _plant(vault, "Shapewick Goodwin", whatsapp="")
        update_frontmatter_field(good, "whatsapp", CORPUS_LID)
        text = good.read_text(encoding="utf-8")
        assert "!!python/object" not in text
        frontmatter, _ = parse_frontmatter(text)
        assert frontmatter["whatsapp"] == [CORPUS_LID], (
            "after a gated write that SUCCEEDS and introduces the field the "
            "bytes carry the LIST form")
        assert yaml.safe_load(text.split("---")[1]) is not None

        # ---- (d) ROUND TRIP as a fixed point -------------------------------
        for value in (PLANT_A, CORPUS_LID):
            path = _plant(vault, f"Fixwick {value[:4]}", whatsapp="")
            update_frontmatter_field(path, "whatsapp", value)
            first = path.read_bytes()
            update_frontmatter_field(path, "whatsapp", value)
            assert path.read_bytes() == first, (
                f"load, save, load again must be a fixed point on the field for "
                f"every member the door ACCEPTS: {value}")

        # For members the door REFUSES the fixed point is the refusal with the
        # bytes unchanged.
        refused_note = _plant(vault, "Fixwick Refusal", whatsapp=PLANT_E)
        snapshot = refused_note.read_bytes()
        for _ in range(2):
            try:
                update_frontmatter_field(refused_note, "whatsapp", PLANT_E)
            except NameGateRefusal:
                pass
            else:                                    # pragma: no cover
                raise AssertionError("class E must be refused at the write door")
            assert refused_note.read_bytes() == snapshot

        # The entity arm is the other whole-record projection, and it must agree.
        person = Person(name="Fixwick Entity", whatsapp=[CORPUS_LID])
        entity_path = vault / "@Fixwick Entity.md"
        write_markdown_file(entity_path, entity=person, body="\n## Notes\n")
        frontmatter, _ = parse_frontmatter(entity_path.read_text(encoding="utf-8"))
        assert frontmatter["whatsapp"] == [CORPUS_LID]
