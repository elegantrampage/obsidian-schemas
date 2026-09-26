"""WI-029 — the provenance write seam and the one rename door.

Four criteria checks plus the non-AC arms the plan orders:

- Task 2 — the parse STAMPS provenance, the stamp cannot reach a note, and the
  accessor the seam reads answers the PARSED path even for a note whose own
  frontmatter forges one (M2).
- AC-1 (Task 9) — a write of an entity the library parsed lands in the note it
  was parsed FROM, through every mutating path in the package.
- AC-2 (Task 10) — exactly one door moves a note, it moves the note it was
  asked about, a moved note stays reachable, and the next write follows it —
  plus the door's IDEMPOTENCE, the half-failed rename's residual, the
  occupied-destination residual reached through `update_fields`, the
  no-provenance name change, the lock-nesting rule and the six folded
  mitigations (M1, M3, M4, M6, M7, M8), each pinned BOTH ways.
- Task 14 — every standing wall this item joins, RUN on the final text.

Every subject is bound with `repo._load_file(path)` rather than a bare
`parse_markdown_file`: `_load_file` also records the snapshot door 2u needs
(`obsidian_schemas/repositories/base.py:BaseRepository._load_file`), so a
provenance-bound write of a loaded entity lands on the 2u arm instead of being
refused by the create arm's `NoteAlreadyExists` — a RED cell against correct
code for a reason in neither the criterion nor the seam.

Nothing here reads syntax directly: that capability is single-homed in
`tests/derivations.py`, and every scan below is imported from it.
"""

# FIRST, ahead of every package import: the conveyor may run this module's checks
# under an interpreter that is not this project's, where the imports below cannot
# resolve. A no-op under the floor command and under CI (WI-021).
from tests.ac_interpreter import ensure_project_interpreter

ensure_project_interpreter(__file__)

import logging  # noqa: E402
import os  # noqa: E402
from pathlib import Path  # noqa: E402

from obsidian_schemas.errors import (  # noqa: E402
    NameGateRefusal,
    NoteAlreadyExists,
)
from obsidian_schemas.models import Book, Meeting, Person  # noqa: E402
from obsidian_schemas.name_gate import gate_write  # noqa: E402
from obsidian_schemas.parser import (  # noqa: E402
    parse_markdown_content,
    parse_markdown_file,
)
from obsidian_schemas.repositories.base import (  # noqa: E402
    FILENAME_RULE_PRECONDITION,
    NAME_DECLARATION_PRECONDITION,
    NO_PROVENANCE_PRECONDITION,
    WRITE_GUARD_PRECONDITION,
)
from obsidian_schemas.repositories.book import BookRepository  # noqa: E402
from obsidian_schemas.repositories.meeting import MeetingRepository  # noqa: E402
from obsidian_schemas.repositories.person import PersonRepository  # noqa: E402
from obsidian_schemas.writer import model_to_frontmatter, write_markdown_file  # noqa: E402
from tests.derivations import (  # noqa: E402
    FS_MODULES,
    OS_READONLY_NAMES,
    PACKAGE_ROOT,
    SCRIPTS_ROOT,
    SEAM_BUCKET,
    TESTS_ROOT,
    FunctionId,
    address_splitting_implementations,
    auto_fixable_branch_checks,
    auto_fixable_emitter_checks,
    base_repository_subclasses,
    character_class_strip_sites,
    door_calls_inside_note_lock,
    filesystem_mutation_uses,
    frontmatter_write_arms,
    functions_calling,
    functions_parsing_then_writing,
    functions_reserializing_parsed_frontmatter,
    gate_call_declarations,
    gate_call_placement,
    load_file_implementations,
    module_import_uses,
    modules_using_ast,
    non_completed_write_sites,
    os_module_attribute_uses,
    python_files_under,
    skip_reason_literal_sites,
    write_target_buckets,
)
from tests.fixture_vault import NOTES, materialize_vault  # noqa: E402
from tests.support import captured_logs, patcher, temp_dir  # noqa: E402

WRITER_PATH = PACKAGE_ROOT / "writer.py"


# ---------------------------------------------------------------------------
# Plumbing — every oracle below is a path or a byte string the test itself wrote
# ---------------------------------------------------------------------------

def _person_note(name: str, extra_lines: tuple = (), body: str = "## Notes\n") -> str:
    """A minimal person note's BYTES, composed here and never through the
    library's own writers: half the frozen corpus is gate-refused, so a plant
    routed through `write_markdown_file` would refuse before it landed."""
    lines = ["---", "type: person", f'name: "{name}"']
    lines.extend(extra_lines)
    lines.append("tags: [person]")
    lines.append("---")
    return "\n".join(lines) + "\n\n" + body


def _write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _filenames(vault: Path) -> set:
    """The vault's NOTE filename set. `*.md` and never `iterdir()`:
    `note_lock`'s sentinel home is a real directory inside the vault and a
    whole-directory oracle would be RED at every arm that legitimately takes the
    lock (`obsidian_schemas/vault_io.py:_sentinel_path`)."""
    return {p.name for p in Path(vault).rglob("*.md")}


def _bytes_of(vault: Path) -> dict:
    return {p.name: p.read_bytes() for p in Path(vault).rglob("*.md")}


def _body_of(path: Path) -> str:
    """The note's CURRENT body, read off its own file.

    `save(entity, body="")` over a note with body content raises
    `BodyTruncationError` (WI-126), which would grade the body guard rather than
    the seam.
    """
    return parse_markdown_file(path).body


def _stem_of(filename: str) -> str:
    """The filename stem less exactly ONE leading `@`."""
    stem = Path(filename).stem
    return stem[1:] if stem.startswith("@") else stem


def _divergent_person_specs() -> dict:
    """AC-1's first subject predicate, over the MANIFEST and never over
    `shape_classes`: a `declared_type="person"` entry with a declared `fields`
    mapping whose filename stem, less the leading `@`, differs RAW from its
    declared `name:`. A `NoteSpec` declaring no `fields` is SKIPPED — three
    person-owned specimens declare none, and they agree with their own stems.
    """
    return {
        filename: spec for filename, spec in NOTES.items()
        if spec.declared_type == "person" and spec.fields is not None
        and _stem_of(filename) != spec.fields.get("name")
    }


def _name_sharing_person_specs() -> dict:
    """AC-1's second subject predicate: every person `NoteSpec` whose declared
    `name:` equals another person `NoteSpec`'s. This is what brings in the
    collision third, whose stem and name AGREE — a note the divergence predicate
    structurally cannot reach."""
    people = {
        filename: spec for filename, spec in NOTES.items()
        if spec.declared_type == "person" and spec.fields is not None
    }
    counts = {}
    for spec in people.values():
        counts[spec.fields.get("name")] = counts.get(spec.fields.get("name"), 0) + 1
    return {filename: spec for filename, spec in people.items()
            if counts[spec.fields.get("name")] > 1}


def _colliding_group_of(vault: Path, filename: str) -> set:
    """Every note in the vault whose stored `name:` equals this one's — the
    group `(b)` and `(c)` quantify over. Derived from the notes on disk so a
    planted member joins by itself."""
    own = parse_markdown_file(Path(vault) / filename).frontmatter.get("name")
    group = set()
    for path in Path(vault).rglob("*.md"):
        try:
            if parse_markdown_file(path).frontmatter.get("name") == own:
                group.add(path.name)
        except Exception:                 # a corruption specimen: not in a group
            continue
    return group


def _door_refusal_pattern(frontmatter: dict):
    """THE DOOR PREDICATE, stated once in the work item and asked here with the
    payload `write_markdown_file` uses: `gate_write(fm, declared_type=...,
    whole_record=True)` over the note's OWN stored record. NOT
    `NameValidator.validate_strict(name)`, whose `allow_phone_sentinel` defaults
    to False while the door DERIVES it from the payload — the two disagree on the
    one `sentinel_exempt` branch, which the census measures at 2 live notes."""
    try:
        gate_write(frontmatter, declared_type=frontmatter.get("type"),
                   whole_record=True)
    except NameGateRefusal as exc:
        return exc.pattern
    return None


# ---------------------------------------------------------------------------
# Task 2 — the stamp: written at the parse, unwritable into a note, unforgeable
# ---------------------------------------------------------------------------

def test_the_parse_stamps_provenance_and_the_stamp_cannot_reach_a_note():
    """The stamp exists exactly where the seam reads it, and nowhere in bytes."""
    with temp_dir() as tmp:
        vault = Path(tmp) / "vault"
        vault.mkdir()
        subject = _write(vault / "@Stamped Subject.md",
                         _person_note("Stamped Subject"))

        # (1) A note parsed FROM A FILE carries the stamp; the same bytes
        # through the path-less entry point carry None.
        from_file = parse_markdown_file(subject, Person).entity
        assert from_file is not None
        assert getattr(from_file, "_source_path", None) == subject, (
            "parse_markdown_file must stamp the entity with the file it parsed")

        from_content = parse_markdown_content(
            subject.read_text(encoding="utf-8"), Person).entity
        assert from_content is not None
        assert getattr(from_content, "_source_path", None) is None, (
            "parse_markdown_content holds no path and must stamp nothing")

        # (2) The stamp is unwritable BY CONSTRUCTION. The oracle is the entity
        # the test itself built — never a hardcoded field list.
        stamped_fm = model_to_frontmatter(from_file)
        assert "_source_path" not in stamped_fm, (
            "the stamp must not appear in the frontmatter mapping")
        path_valued = {k: v for k, v in stamped_fm.items() if isinstance(v, Path)}
        assert path_valued == {}, (
            f"no frontmatter key may hold a path; found {path_valued}")
        assert set(stamped_fm) == set(model_to_frontmatter(from_content)), (
            "a stamped entity's frontmatter key set must equal an unstamped "
            "entity's built from the same bytes")

        # (3) …and a real write of a stamped entity produces the same key set.
        written = write_markdown_file(vault / "@Written Subject.md",
                                      entity=from_file, body="## Notes\n")
        written_fm = parse_markdown_file(written, Person).frontmatter
        assert "_source_path" not in written_fm, (
            "a write of a stamped entity must not serialize the stamp")
        assert set(written_fm) == set(model_to_frontmatter(from_content)), (
            "the written frontmatter's key set must equal the unstamped "
            "projection's")

        # (4) The honest boundary AC-1(f) declares: `model_copy` preserves the
        # stamp, a dict round trip drops it.
        assert getattr(from_file.model_copy(), "_source_path", None) == subject, (
            "model_copy must preserve the stamp")
        round_tripped = Person.model_validate(from_file.model_dump())
        assert getattr(round_tripped, "_source_path", None) is None, (
            "model_dump()/model_validate() drops the stamp — AC-1(f)")

        # (5) M2, THE READ DIRECTION: a note whose OWN frontmatter declares
        # `_source_path` naming a DIFFERENT file still resolves to its own.
        other = _write(vault / "@Forgery Target.md", _person_note("Forgery Target"))
        forger = _write(
            vault / "@Forging Subject.md",
            _person_note("Forging Subject",
                         extra_lines=(f'_source_path: "{other}"',)))

        repo = PersonRepository(vault, auto_load=False)
        forged_entity = parse_markdown_file(forger, Person).entity
        assert forged_entity is not None
        # Verbatim the accessor `_resolve_write_target` reads.
        assert getattr(forged_entity, "_source_path", None) == forger
        assert getattr(forged_entity, "_source_path", None) != other
        assert repo._resolve_write_target(forged_entity) == forger, (
            "the seam must answer the PARSED path, never a value read out of "
            "the note's own bytes (M2)")
        assert repo._resolve_write_target(forged_entity) != other

        # Where the forged key ENDED UP is an observation, not an assertion:
        # pinning pydantic's retention of an underscore-prefixed extra would go
        # RED against correct code on a release that stops keeping it, and M2's
        # property holds either way. Build Log records what this run observed.


def test_the_seam_returns_the_stamp_only_inside_this_vault():
    """`_resolve_write_target` is a pure resolution: provenance, containment,
    and no fallback of its own."""
    with temp_dir() as tmp:
        vault = Path(tmp) / "vault"
        vault.mkdir()
        elsewhere = Path(tmp) / "other-vault"
        elsewhere.mkdir()

        subject = _write(vault / "@Inside Subject.md", _person_note("Inside Subject"))
        foreign = _write(elsewhere / "@Outside Subject.md",
                         _person_note("Outside Subject"))

        repo = PersonRepository(vault, auto_load=False)

        stamped = parse_markdown_file(subject, Person).entity
        assert repo._resolve_write_target(stamped) == subject

        unstamped = parse_markdown_content(
            subject.read_text(encoding="utf-8"), Person).entity
        assert repo._resolve_write_target(unstamped) is None, (
            "no stamp means no answer — the caller applies its own fallback")

        from_other_vault = parse_markdown_file(foreign, Person).entity
        assert repo._resolve_write_target(from_other_vault) is None, (
            "a repository must not be steerable outside its own vault by an "
            "entity it was handed")

        # Existence is deliberately NOT part of the resolution.
        subject.unlink()
        assert repo._resolve_write_target(stamped) == subject, (
            "the stamp is a path, not a promise the file is still there")


# ---------------------------------------------------------------------------
# AC-1 (Task 9) — no library write can turn one person note into two, or land
# one person's bytes in another person's file
# ---------------------------------------------------------------------------

#: The Person path set, taken from the same population AC-5 scans rather than
#: hand-listed. `save` is FIRST because it is the one cell with a second declared
#: outcome (the door predicate's refusal).
PERSON_PATHS = (
    "save",
    "update_fields",
    "append_to_timeline",
    "append_to_body_section",
    "add_to_discuss_item",
    "update_to_discuss_item",
    "remove_to_discuss_item",
)

#: The planted colliding groups' shared deriving fields, so each type's OWN rule
#: recomputes to ONE filename for two notes living at two.
BOOK_TITLE = "Colliding Ledger"
BOOK_AUTHOR = "Marrow Quillfeather"
MEETING_DATE = "2026-03-01"
MEETING_TOPIC = "Colliding Topic"


def _book_note(title: str, author: str, status: str = "to-read") -> str:
    return ("---\ntype: book\n"
            f'title: "{title}"\n'
            f'author: "{author}"\n'
            f'status: "{status}"\n'
            "tags: [book]\n---\n\n## Notes\n")


def _meeting_note(date: str, topic: str, meeting_id: str) -> str:
    return ("---\ntype: meeting\n"
            f'date: "{date}"\n'
            "attendees: []\n"
            f'topics: ["{topic}"]\n'
            f'meeting_id: "{meeting_id}"\n'
            "tags: [meeting]\n---\n\n## Notes\n")


def _seed_person_path(repo, path_name: str, entity, marker: str) -> None:
    """The two To-Discuss UPDATE paths write nothing when the item is absent, so
    their cell would assert over a no-op. The seeding add happens BEFORE the
    snapshot, so the measured call is the one the oracle grades."""
    if path_name in ("update_to_discuss_item", "remove_to_discuss_item"):
        repo.add_to_discuss_item(entity, marker)


def _drive_person_path(repo, path_name: str, entity, subject: Path,
                       marker: str) -> None:
    """Each path's MINIMAL mutation, touching none of the fields Person's
    filename rule reads (`name`): `title` is the JOB title, which names nobody
    and feeds no filename."""
    if path_name == "save":
        entity.title = marker
        repo.save(entity, body=_body_of(subject))
    elif path_name == "update_fields":
        repo.update_fields(entity, {"title": marker})
    elif path_name == "append_to_timeline":
        repo.append_to_timeline(entity, f"### 2026-09-26\n- {marker}\n")
    elif path_name == "append_to_body_section":
        repo.append_to_body_section(entity, "Notes", f"- {marker}")
    elif path_name == "add_to_discuss_item":
        repo.add_to_discuss_item(entity, marker)
    elif path_name == "update_to_discuss_item":
        repo.update_to_discuss_item(entity, marker, True)
    elif path_name == "remove_to_discuss_item":
        repo.remove_to_discuss_item(entity, marker)
    else:                                   # pragma: no cover — a new path name
        raise AssertionError(f"undriven path {path_name!r}")


def _assert_no_leak(vault: Path, changed: set) -> None:
    """AC-1(h). Bounded exactly as the work item bounds it: no note the sweep
    WRITES gains a frontmatter key holding a path. It is NOT "the package strips
    extras" — an undeclared key already in a note survives the round trip by
    design (`extra="allow"`), which is a pre-existing property this item neither
    creates nor worsens."""
    for name in sorted(changed):
        frontmatter = parse_markdown_file(Path(vault) / name).frontmatter
        assert "_source_path" not in frontmatter, (
            f"{name}: the provenance stamp reached the note's frontmatter")
        for key, value in frontmatter.items():
            assert str(vault) not in str(value), (
                f"{name}: frontmatter key {key!r} carries a path into the vault")


def test_no_library_write_can_fork_a_person_note():
    """AC-1. Zero-arg and raising, per the check contract."""
    divergent = _divergent_person_specs()
    sharing = _name_sharing_person_specs()
    subjects = sorted(set(divergent) | set(sharing))

    # The class's extension over the frozen corpus, DERIVED here and asserted so
    # the sweep cannot silently narrow: four divergent members and one
    # name-sharing group of three, whose union is five subjects.
    assert len(divergent) == 4, sorted(divergent)
    assert len(sharing) == 3, sorted(sharing)
    assert len(subjects) == 5, subjects

    # The PATH set is the same population AC-5 scans, never a hand list.
    seam_qualnames = {
        site.qualname
        for site in write_target_buckets(python_files_under(PACKAGE_ROOT),
                                         WRITER_PATH)
        if site.bucket == SEAM_BUCKET
    }
    invoked = {f"BaseRepository.{PERSON_PATHS[0]}",
               "BaseRepository.update_fields",
               "BaseRepository.rename_note",
               "BookRepository.save", "MeetingRepository.save"}
    invoked |= {f"PersonRepository.{name}" for name in PERSON_PATHS[2:]}
    assert invoked == seam_qualnames, (
        "AC-1's invoked path set plus `rename_note` must EQUAL AC-5's seam "
        f"bucket; symmetric difference {invoked ^ seam_qualnames}")

    # ---- the (subject x path) matrix over the corpus subjects ----
    for filename in subjects:
        for path_name in PERSON_PATHS:
            _person_cell(filename, path_name)

    # ---- the PLANTED subjects the corpus structurally cannot supply ----
    _sentinel_exempt_cell()
    _planted_type_general_cells()
    _absent_provenance_arms()
    _unloaded_repository_arms()


def _person_cell(filename: str, path_name: str) -> None:
    """One (subject, path) cell: assert (a) the filename SET is unchanged, (b)
    the changed bytes are in the file the subject was PARSED FROM, and (c) every
    other member of its colliding group is byte-identical.

    (b) and (c) are asserted together as the stronger property they imply: the
    ONLY note in the vault whose bytes changed is the subject's own.
    """
    with temp_dir() as tmp:
        vault = materialize_vault(Path(tmp) / "vault")
        subject = vault / filename
        group = _colliding_group_of(vault, filename)
        assert filename in group

        # `auto_load=False` and never `load()`ed, so (g)'s first half is asserted
        # at EVERY cell rather than at one: the seam needs no vault walk.
        repo = PersonRepository(vault, auto_load=False)
        entity = repo._load_file(subject)
        assert entity is not None, f"{filename} did not load"

        marker = f"wi029-{path_name}"
        _seed_person_path(repo, path_name, entity, marker)

        before_names = _filenames(vault)
        before_bytes = _bytes_of(vault)
        refusal = _door_refusal_pattern(
            parse_markdown_file(subject).frontmatter)

        if path_name == "save" and refusal is not None:
            # THE ONE CELL WITH A SECOND DECLARED OUTCOME, reached BY RULE and
            # never by a hand-list: where the DOOR refuses this note's stored
            # name, `save` raises above the lock and no file in the vault moves.
            try:
                _drive_person_path(repo, path_name, entity, subject, marker)
            except NameGateRefusal as exc:
                assert exc.pattern == refusal, (
                    f"{filename}: expected pattern {refusal!r}, got {exc.pattern!r}")
            else:
                raise AssertionError(
                    f"{filename}: the door refuses this stored name, so save() "
                    f"must raise NameGateRefusal before any write")
            assert _filenames(vault) == before_names
            assert _bytes_of(vault) == before_bytes, (
                f"{filename}: a refused save changed bytes on disk")
            assert repo._loaded is False
            return

        _drive_person_path(repo, path_name, entity, subject, marker)

        assert _filenames(vault) == before_names, (
            f"{filename}/{path_name}: the vault's filename SET moved — "
            f"{_filenames(vault) ^ before_names}")
        after_bytes = _bytes_of(vault)
        changed = {name for name, blob in after_bytes.items()
                   if before_bytes.get(name) != blob}
        assert changed == {filename}, (
            f"{filename}/{path_name}: the write landed in {sorted(changed)} "
            f"rather than in the file the entity was parsed from")
        for member in sorted(group - {filename}):
            assert after_bytes[member] == before_bytes[member], (
                f"{member}: a colliding group member was not byte-identical")
        assert repo._loaded is False, (
            f"{filename}/{path_name}: the write triggered a vault walk")
        _assert_no_leak(vault, changed)


def _sentinel_exempt_cell() -> None:
    """AC-1's PLANTED sentinel-exempt subject — the one member that tells the
    DOOR predicate apart from a bare `validate_strict`.

    A divergent phone-only stub declaring `phones`: `pure_digit` is the one
    `sentinel_exempt` Tier-1 branch, `gate_write` DERIVES the exemption from the
    payload, so the door WRITES it and its `save` cell asserts the ORDINARY
    (a)(b)(c). Asserting that it is NOT refused is the arm that fails an
    implementation built on the bare validator.
    """
    with temp_dir() as tmp:
        vault = materialize_vault(Path(tmp) / "vault")
        subject = _write(vault / "@447700900123.md",
                         _person_note("+447700900123",
                                      extra_lines=('phones: ["+447700900123"]',)))
        assert _door_refusal_pattern(
            parse_markdown_file(subject).frontmatter) is None, (
            "the DOOR writes a phone-only stub that declares `phones`; a "
            "refusal here means the predicate is the bare validator's")

        repo = PersonRepository(vault, auto_load=False)
        entity = repo._load_file(subject)
        assert entity is not None
        before_names, before_bytes = _filenames(vault), _bytes_of(vault)
        entity.title = "wi029-sentinel"
        repo.save(entity, body=_body_of(subject))
        assert _filenames(vault) == before_names
        changed = {name for name, blob in _bytes_of(vault).items()
                   if before_bytes.get(name) != blob}
        assert changed == {subject.name}, sorted(changed)
        _assert_no_leak(vault, changed)


def _planted_type_general_cells() -> None:
    """Divergence is not a Person-only predicate: one COLLIDING GROUP per type
    for Book and Meeting, each a pair whose OWN rule recomputes to ONE filename
    while they live at two.

    The frozen corpus holds no divergent Book or Meeting, and for a subject whose
    deriving fields still agree with its file the two mechanisms compute the SAME
    path — so such a subject cannot discriminate a provenance-bound write from a
    `_get_file_name`-derived one, nor a correct seam from a stub that calls the
    seam and discards the return. The mutation touches NONE of the deriving
    fields, so the cell measures provenance against derivation.
    """
    cases = (
        (BookRepository, Book,
         f"{BOOK_TITLE} - {BOOK_AUTHOR}.md",          # lives AT its derived name
         "Elsewhere Ledger.md",                        # DIVERGENT member
         _book_note(BOOK_TITLE, BOOK_AUTHOR),
         "status", "read"),
        (MeetingRepository, Meeting,
         f"Meeting {MEETING_DATE.replace('-', '')} - {MEETING_TOPIC}.md",
         "Meeting Elsewhere Sibling.md",
         _meeting_note(MEETING_DATE, MEETING_TOPIC, "collide-1"),
         "tags", ["moved"]),
    )
    for repo_class, model, at_derived, elsewhere, note_text, field, value in cases:
        with temp_dir() as tmp:
            vault = Path(tmp) / "vault"
            vault.mkdir()
            sibling = _write(vault / at_derived, note_text)
            subject = _write(vault / elsewhere, note_text)

            repo = repo_class(vault, auto_load=False)
            entity = repo._load_file(subject)
            assert entity is not None, f"{elsewhere} did not load"
            # The group is REAL: both notes' own rule recomputes to one filename.
            assert repo._get_file_name(entity) == at_derived, (
                f"the planted group is not colliding: "
                f"{repo._get_file_name(entity)!r} != {at_derived!r}")

            before_names, before_bytes = _filenames(vault), _bytes_of(vault)
            setattr(entity, field, value)
            repo.save(entity, body=_body_of(subject))

            assert _filenames(vault) == before_names, (
                f"{elsewhere}: the filename SET moved")
            after_bytes = _bytes_of(vault)
            changed = {name for name, blob in after_bytes.items()
                       if before_bytes.get(name) != blob}
            assert changed == {subject.name}, (
                f"{elsewhere}: the write landed in {sorted(changed)} — today's "
                f"derivation-bound override writes over the sibling at "
                f"{at_derived!r}, a note the caller never named")
            assert after_bytes[sibling.name] == before_bytes[sibling.name]
            assert repo._loaded is False
            _assert_no_leak(vault, changed)


def _absent_provenance_arms() -> None:
    """AC-1 (d), (e) and (f) — the arms that belong to ONE path, because the
    behaviour on ABSENT provenance differs by path and must."""
    with temp_dir() as tmp:
        vault = Path(tmp) / "vault"
        vault.mkdir()

        # (d) a PLANTED divergent note whose canonical `@{name}.md` is FREE:
        # `save` creates no `@{name}.md`.
        divergent = _write(vault / "@Old Stem.md", _person_note("Fresh Name"))
        repo = PersonRepository(vault, auto_load=False)
        entity = repo._load_file(divergent)
        entity.title = "wi029-free-canonical"
        repo.save(entity, body=_body_of(divergent))
        assert not (vault / "@Fresh Name.md").exists(), (
            "save() created the canonical filename for a note it was parsed "
            "from elsewhere — the fork this item exists to end")
        assert "wi029-free-canonical" in divergent.read_text(encoding="utf-8")

        # (e) the discriminator that stops "never write anywhere" from passing: a
        # genuinely NEW entity still creates `@{name}.md`.
        created = repo.save(Person(name="Brand New Person"), body="## Notes\n")
        assert created == vault / "@Brand New Person.md"
        assert created.exists()

        # (f) NARROWED ARM — a round-tripped entity has no provenance BY DESIGN,
        # so today's behaviour holds: the target is `@{name}.md`. The declared
        # marker is asserted with it: a WARNING naming the collision, emitted
        # BEFORE `write_markdown_file` reaches its zero case and refuses.
        #
        # The occupied note is PLANTED AS BYTES and bound with
        # `parse_markdown_file` rather than `repo._load_file`, because the zero
        # case keys on whether THIS PROCESS has observed the target:
        # `_load_file` calls `remember_snapshot` and `save` records one, either
        # of which puts the write on the 2u arm instead
        # (`obsidian_schemas/writer.py:write_markdown_file`). A note nothing in
        # this process read is the population (f) is about.
        occupied = _write(vault / "@Occupied Canonical.md",
                          _person_note("Occupied Canonical"))
        round_tripped = Person.model_validate(
            parse_markdown_file(occupied, Person).entity.model_dump())
        assert getattr(round_tripped, "_source_path", None) is None
        before_bytes = _bytes_of(vault)
        with captured_logs(level=logging.WARNING) as records:
            try:
                repo.save(round_tripped, body="## Notes\n")
            except NoteAlreadyExists:
                pass
            else:
                raise AssertionError(
                    "an unstamped save onto an occupied canonical filename is "
                    "today's zero case and must refuse")
        assert any("no provenance" in record.getMessage()
                   and occupied.name in record.getMessage()
                   for record in records), (
            f"the collision WARNING was not emitted: "
            f"{[r.getMessage() for r in records]}")
        assert _bytes_of(vault) == before_bytes, (
            "the refused write changed bytes on disk")


def _unloaded_repository_arms() -> None:
    """AC-1(g)'s SECOND half — the arm that stops the seam being built as a
    uniform fallback. On a repository constructed `auto_load=False` and never
    `load()`ed, an entity carrying NO provenance still RAISES from
    `update_fields` and from each body-writer rather than creating a note."""
    with temp_dir() as tmp:
        vault = Path(tmp) / "vault"
        vault.mkdir()
        planted = _write(vault / "@Unstamped Subject.md",
                         _person_note("Unstamped Subject"))
        repo = PersonRepository(vault, auto_load=False)
        unstamped = parse_markdown_content(
            planted.read_text(encoding="utf-8"), Person).entity
        assert repo._resolve_write_target(unstamped) is None

        before_names, before_bytes = _filenames(vault), _bytes_of(vault)
        refusals = (
            lambda: repo.update_fields(unstamped, {"title": "x"}),
            lambda: repo.append_to_timeline(unstamped, "### x\n- y\n"),
            lambda: repo.append_to_body_section(unstamped, "Notes", "- y"),
            lambda: repo.add_to_discuss_item(unstamped, "y"),
            lambda: repo.update_to_discuss_item(unstamped, "y", True),
            lambda: repo.remove_to_discuss_item(unstamped, "y"),
        )
        for index, call in enumerate(refusals):
            try:
                call()
            except ValueError:
                pass
            else:
                raise AssertionError(
                    f"refusing path {index} wrote instead of raising for an "
                    f"entity with no provenance on an unloaded repository")
        assert _filenames(vault) == before_names, (
            "a refusing path CREATED a note — the uniform-fallback defect")
        assert _bytes_of(vault) == before_bytes
        assert repo._loaded is False


# ---------------------------------------------------------------------------
# AC-2 (Task 10) — exactly one door moves a note, it moves the note it was ASKED
# about, a moved note stays reachable, and the next write follows it.
#
# ONE RULE OVER EVERY ARM IN THIS CHECK: the door answers in RESOLVED paths.
# `rename_note` returns `move_note`'s `_resolved(dest)` and STAMPS that value, so
# any assertion comparing a path the door RETURNED or STAMPED against a path the
# TEST created resolves both sides — exactly the normalization
# `tests/test_lint_vault_fix_rules.py:_temp_vault` already performs for the same
# reason. Assertions over the vault's filename SET are unaffected: those read
# `.name` values out of a directory listing.
# ---------------------------------------------------------------------------

GUARD_ENV = "OBSIDIAN_SCHEMAS_WRITE_GUARD"


def _same_file(left, right) -> bool:
    return Path(left).resolve() == Path(right).resolve()


def _recording_move_note(monkey, module):
    """Wrap `move_note` in a delegate that FORWARDS to the real door and records
    every call, restored by the patcher's own `finally`."""
    calls = []
    real = module.vault_io.move_note

    def recorder(src, dest):
        calls.append((Path(src), Path(dest)))
        return real(src, dest)

    monkey.setattr(module.vault_io, "move_note", recorder)
    return calls


def _aliases_of(path: Path) -> list:
    return list(parse_markdown_file(path).frontmatter.get("aliases") or [])


def test_a_person_note_is_renamed_only_through_the_one_door_and_stays_reachable():
    """AC-2. Zero-arg and raising, per the check contract."""
    _door_resolves_through_the_seam_and_stays_reachable()      # (a), (e)
    _door_refuses_an_occupied_destination()                     # (b), (e)
    _update_fields_calls_the_door_and_nothing_else_moves()      # (c), (g)
    _door_refuses_a_symlinked_source()                          # (d)
    _door_moves_the_note_it_was_asked_about()                   # (f)
    _door_case_only_rename_with_a_filesystem_probe()            # (h)
    _door_is_idempotent_after_a_real_move()
    _half_failed_rename_leaves_a_moved_unaliased_note()
    _update_fields_occupied_destination_residual()
    _update_fields_refuses_a_no_provenance_name_change()
    _no_caller_holds_a_note_lock_across_the_door()
    _m1_the_destination_is_contained()
    _m3_the_staging_name_stays_in_the_md_namespace()
    _m4_the_audit_line_names_both_ends()
    _m6_the_door_fails_closed_under_a_non_enforcing_guard()
    _m7_update_fields_refuses_a_name_delta_on_a_type_declaring_none()
    _m8_update_fields_refuses_a_delta_that_moves_the_filename_rule()


def _door_resolves_through_the_seam_and_stays_reachable():
    """(a) — the door resolves its SOURCE through the same provenance function
    every write path uses, routes through `vault_io.move_note`, keeps the old
    stem as an alias, and leaves the person resolvable under BOTH names.
    (e), first direction — a `save()` on the SAME in-memory entity afterwards
    lands in the new file and does NOT recreate the old stem."""
    with temp_dir() as tmp:
        vault = Path(tmp) / "vault"
        vault.mkdir()
        old = _write(vault / "@Old Stem.md",
                     _person_note("Ravenna Oakhelm",
                                  extra_lines=('emails: ["ravenna@example.com"]',)))
        repo = PersonRepository(vault, auto_load=False)
        entity = repo._load_file(old)
        assert entity is not None

        with patcher() as monkey:
            monkey.setitem(os.environ, GUARD_ENV, "enforce")
            calls = _recording_move_note(monkey, _base_module())
            moved = repo.rename_note(entity, "@Ravenna Oakhelm.md")

        assert _same_file(moved, vault / "@Ravenna Oakhelm.md")
        assert not old.exists(), "the source was left behind"
        assert calls and _same_file(calls[0][0], old), (
            "the door must route through vault_io.move_note with the SOURCE the "
            f"seam resolved; recorded {calls}")
        assert "Old Stem" in _aliases_of(moved), (
            f"the old stem was not kept as an alias: {_aliases_of(moved)}")

        # Reachability as a RESOLUTION property, not the presence of a key.
        assert repo.get("Ravenna Oakhelm") is not None
        assert repo.get_by_alias("Old Stem") is not None
        assert repo.get_by_email("ravenna@example.com") is not None
        assert repo.resolve("Old Stem") is not None

        # (e) the write FOLLOWS the file: the same in-memory entity's next save
        # lands in the new note and the old stem is not recreated.
        entity.title = "wi029-follows"
        saved = repo.save(entity, body=_body_of(moved))
        assert _same_file(saved, moved)
        assert not old.exists(), "a save after the rename recreated the old stem"
        assert "wi029-follows" in moved.read_text(encoding="utf-8")


def _base_module():
    """The module object whose `vault_io` and `update_frontmatter_field` bindings
    the arms below patch — imported here so the patch target is the door's OWN
    binding and not a second one."""
    from obsidian_schemas.repositories import base
    return base


def _door_refuses_an_occupied_destination():
    """(b) — `NoteAlreadyExists` (the LEAF, not the root) with BOTH files
    byte-identical afterwards. (e), second direction — that same entity's save
    still lands in the UNMOVED original."""
    with temp_dir() as tmp:
        vault = Path(tmp) / "vault"
        vault.mkdir()
        subject = _write(vault / "@Source Note.md", _person_note("Source Note"))
        blocker = _write(vault / "@Blocking Note.md", _person_note("Blocking Note"))
        before = _bytes_of(vault)

        repo = PersonRepository(vault, auto_load=False)
        entity = repo._load_file(subject)
        with patcher() as monkey:
            monkey.setitem(os.environ, GUARD_ENV, "enforce")
            try:
                repo.rename_note(entity, blocker.name)
            except NoteAlreadyExists:
                pass
            else:
                raise AssertionError(
                    "a rename onto an occupied destination must raise "
                    "NoteAlreadyExists by syscall")
        assert _bytes_of(vault) == before, (
            "a refused rename changed bytes on disk")

        entity.title = "wi029-refused-then-saved"
        saved = repo.save(entity, body=_body_of(subject))
        assert _same_file(saved, subject), (
            "after a REFUSED rename the write must land in the unmoved original")
        assert parse_markdown_file(blocker).frontmatter["name"] == "Blocking Note"


def _update_fields_calls_the_door_and_nothing_else_moves():
    """(c) — `update_fields` with a name change calls the door rather than
    leaving the file behind, and a derived scan finds exactly ONE function in the
    package naming a rename capability. (g) — the entity it RETURNS carries
    provenance naming the file actually written."""
    movers = functions_calling(python_files_under(PACKAGE_ROOT), "move_note")
    assert movers == {FunctionId("obsidian_schemas/repositories/base.py",
                                 "BaseRepository.rename_note")}, (
        f"exactly one function in the package may move a note; found {movers}")

    with temp_dir() as tmp:
        vault = Path(tmp) / "vault"
        vault.mkdir()
        old = _write(vault / "@Thessaly Vane.md", _person_note("Thessaly Vane"))
        repo = PersonRepository(vault, auto_load=False)
        entity = repo._load_file(old)

        with patcher() as monkey:
            monkey.setitem(os.environ, GUARD_ENV, "enforce")
            updated = repo.update_fields(entity, {"name": "Thessaly Wren"})

        new = vault / "@Thessaly Wren.md"
        assert new.exists() and not old.exists(), (
            "update_fields must MOVE the note, not leave the old stem behind")
        assert "Thessaly Vane" in _aliases_of(new)
        assert _filenames(vault) == {new.name}

        # (g) the RELOAD re-stamps, so a save on the RETURNED entity lands there.
        assert _same_file(repo._resolve_write_target(updated), new)
        updated.title = "wi029-reloaded"
        assert _same_file(repo.save(updated, body=_body_of(new)), new)
        assert _filenames(vault) == {new.name}


def _door_refuses_a_symlinked_source():
    """(d) — a symlinked source is refused, unmoved, per door 3's own contract."""
    with temp_dir() as tmp:
        vault = Path(tmp) / "vault"
        vault.mkdir()
        real = _write(vault / "@Real Target.md", _person_note("Real Target"))
        link = vault / "@Linked Source.md"
        link.symlink_to(real)

        repo = PersonRepository(vault, auto_load=False)
        entity = repo._load_file(link)
        assert entity is not None
        before = _filenames(vault)
        with patcher() as monkey:
            monkey.setitem(os.environ, GUARD_ENV, "enforce")
            try:
                repo.rename_note(entity, "@Real Target Renamed.md")
            except Exception as exc:                 # WriteFailedError, a LoudFail
                assert type(exc).__name__ == "WriteFailedError", type(exc).__name__
            else:
                raise AssertionError("a symlinked source must be refused")
        assert _filenames(vault) == before
        assert link.is_symlink() and real.exists()


def _door_moves_the_note_it_was_asked_about():
    """(f) — THE RIGHT NOTE, UNDER COLLISION. For two corpus notes sharing one
    stored `name:`, renaming the entity parsed from A moves A: B is
    byte-identical, its `aliases` did not gain A's old stem, and it is still at
    its original path."""
    with temp_dir() as tmp:
        vault = materialize_vault(Path(tmp) / "vault")
        a = vault / "@Quillam Ostrivane.md"
        b = vault / "@Quillam Lumbrek.md"
        b_before = b.read_bytes()

        repo = PersonRepository(vault, auto_load=False)
        entity = repo._load_file(a)
        with patcher() as monkey:
            monkey.setitem(os.environ, GUARD_ENV, "enforce")
            moved = repo.rename_note(entity, "@Quillam Ostrivane Moved.md")

        assert _same_file(moved, vault / "@Quillam Ostrivane Moved.md")
        assert not a.exists()
        assert b.exists() and b.read_bytes() == b_before, (
            "the door moved or edited the OTHER member of the collision pair")
        assert "Quillam Ostrivane" not in _aliases_of(b)


def _door_case_only_rename_with_a_filesystem_probe():
    """(h) — asked to rename a note to a stem differing from its own only by
    letter CASE, the door MOVES it rather than refusing.

    The filesystem's case behaviour is PROBED rather than assumed: a check that
    assumed case-insensitivity would be red in a correct build on a
    case-sensitive filesystem, and one that assumed sensitivity would skip the
    arm the live vault needs (WI-149).
    """
    with temp_dir() as tmp:
        vault = Path(tmp) / "vault"
        vault.mkdir()
        probe = _write(vault / "@Probe.md", _person_note("Probe"))
        case_insensitive = (vault / "@probe.md").exists()
        probe.unlink()

        subject = _write(vault / "@ravenna oakhelm.md",
                         _person_note("Ravenna Oakhelm"))
        repo = PersonRepository(vault, auto_load=False)
        entity = repo._load_file(subject)
        with patcher() as monkey:
            monkey.setitem(os.environ, GUARD_ENV, "enforce")
            moved = repo.rename_note(entity, "@Ravenna Oakhelm.md")

        # The post-conditions are the SAME whichever branch the platform took.
        assert _filenames(vault) == {"@Ravenna Oakhelm.md"}, (
            f"exactly one directory entry for that note, spelled in the NEW "
            f"case; got {_filenames(vault)}")
        assert moved.name == "@Ravenna Oakhelm.md"
        assert "ravenna oakhelm" in _aliases_of(moved), (
            f"the old spelling must survive as an alias: {_aliases_of(moved)}")
        assert case_insensitive == (
            Path(str(vault / "@RAVENNA OAKHELM.md")).exists()), (
            "the probe and the filesystem disagree about case sensitivity")

        # The `samefile` branch is additionally driven DIRECTLY, so it is never
        # unexercised on a case-sensitive filesystem.
        second = _write(vault / "@lowercase only.md", _person_note("Lowercase Only"))
        entity2 = repo._load_file(second)
        with patcher() as monkey:
            monkey.setitem(os.environ, GUARD_ENV, "enforce")
            moved2 = repo.rename_note(entity2, "@Lowercase Only.md")
        assert moved2.name == "@Lowercase Only.md"
        assert not [p for p in vault.rglob("*.rename-tmp.md")], (
            "a staging note survived a successful two-step")


def _door_is_idempotent_after_a_real_move():
    """IDEMPOTENCE — a non-AC arm, and the ORDER is the arm.

    Drive one REAL rename first, which is what re-stamps the entity with
    `move_note`'s RESOLVED answer, and only THEN call the door with the filename
    the note now has. Calling the door twice on a filename it held from the START
    would not test this: there the stamp is `_load_file`'s and carries the
    repository's own spelling, so even a raw string compare fires and the arm is
    vacuous.

    The precondition is PLANTED, never inherited from the platform: the spelling
    divergence exists only where `repo.vault_path` differs from its resolved
    form, so the test builds a vault path that does — a real sub-directory and a
    `..` — rather than reaching for macOS's `/var` → `/private/var`, which is
    green-by-environment on one platform and vacuous on another (WI-149).
    """
    with temp_dir() as tmp:
        real = Path(tmp) / "vault"
        (real / "sub").mkdir(parents=True)
        spelled = real / "sub" / ".."
        subject = _write(real / "@Old Stem.md", _person_note("Renamed Person"))

        repo = PersonRepository(spelled, auto_load=False)
        assert repo.vault_path != repo.vault_path.resolve(), (
            "the arm is vacuous unless the vault path's spelling really does "
            f"differ from its resolved form: {repo.vault_path}")

        entity = repo._load_file(subject)
        with patcher() as monkey:
            monkey.setitem(os.environ, GUARD_ENV, "enforce")
            first = repo.rename_note(entity, "@New Stem.md")
            assert _same_file(first, real / "@New Stem.md")
            aliases_after_first = _aliases_of(first)
            names_after_first = _filenames(real)

            calls = _recording_move_note(monkey, _base_module())
            second = repo.rename_note(entity, "@New Stem.md")

        assert calls == [], (
            f"the idempotent re-run performed a move: {calls}")
        assert _same_file(second, first)
        assert _filenames(real) == names_after_first
        assert _aliases_of(first) == aliases_after_first, (
            "the re-run appended a second alias")
        assert _same_file(repo._resolve_write_target(entity), first)
        assert not [p for p in real.rglob("*.rename-tmp.md")]


def _half_failed_rename_leaves_a_moved_unaliased_note():
    """THE HALF-FAILED RENAME'S RESIDUAL, asserted rather than asserted-about.

    The alias write is forced to raise. The residual the re-run table declares is
    a MOVED, correctly-stamped note missing one alias — and a re-run repairs
    NONE of it, because provenance has already moved to the destination. The
    documented recovery is one caller-side field edit.
    """
    base = _base_module()
    with temp_dir() as tmp:
        vault = Path(tmp) / "vault"
        vault.mkdir()
        old = _write(vault / "@Old Stem.md", _person_note("Halved Person"))
        repo = PersonRepository(vault, auto_load=False)
        entity = repo._load_file(old)

        raised = {"count": 0}

        def refusing_alias_writer(*args, **kwargs):
            raised["count"] += 1
            raise RuntimeError("the alias write was forced to fail")

        with patcher() as monkey:
            monkey.setitem(os.environ, GUARD_ENV, "enforce")
            monkey.setattr(base, "update_frontmatter_field", refusing_alias_writer)
            try:
                repo.rename_note(entity, "@New Stem.md")
            except RuntimeError:
                pass
            else:
                raise AssertionError("the forced alias failure did not propagate")

        assert raised["count"] == 1
        new = vault / "@New Stem.md"
        assert new.exists() and not old.exists(), (
            "the MOVE committed before the alias write, so it must have landed")
        assert _same_file(repo._resolve_write_target(entity), new), (
            "the entity is re-stamped BEFORE the alias write, so no later save "
            "can recreate the note the rename removed")
        assert "Old Stem" not in _aliases_of(new), (
            "the alias write was forced to fail; the residual is the MISSING "
            "alias and the spec says so")

        # The re-run is a safe NO-OP that repairs NOTHING.
        with patcher() as monkey:
            monkey.setitem(os.environ, GUARD_ENV, "enforce")
            calls = _recording_move_note(monkey, base)
            repo.rename_note(entity, "@New Stem.md")
        assert calls == [], f"the re-run moved the note again: {calls}"
        assert _filenames(vault) == {new.name}
        assert "Old Stem" not in _aliases_of(new), (
            "the re-run must NOT repair the missing alias — provenance has "
            "moved, so `old_stem == new_stem` and nothing is appended")

        # THE DOCUMENTED RECOVERY: one field edit, and it moves no file.
        repo.update_fields(entity, {"aliases": ["Old Stem"]})
        assert "Old Stem" in _aliases_of(new)
        assert _filenames(vault) == {new.name}


def _update_fields_occupied_destination_residual():
    """THE OCCUPIED DESTINATION, REACHED THROUGH `update_fields` — the accepted
    residual, ASSERTED rather than described.

    No other cell in this battery reaches it: AC-2(b) drives the door DIRECTLY,
    M6's `update_fields` half refuses before the write, and M7's subject is a
    Book. The guard mode is set EXPLICITLY, because an ambient `observe` would
    make this arm pass on the wrong refusal (WI-149).
    """
    with temp_dir() as tmp:
        vault = Path(tmp) / "vault"
        vault.mkdir()
        a = _write(vault / "@Old.md",
                   _person_note("Old", body="## Notes\n\n- subject A\n"))
        b = _write(vault / "@New.md",
                   _person_note("Blocker", body="## Notes\n\n- note B\n"))
        a_bytes, b_bytes = a.read_bytes(), b.read_bytes()
        names = _filenames(vault)

        repo = PersonRepository(vault, auto_load=False)
        entity = repo._load_file(a)

        with patcher() as monkey:
            monkey.setitem(os.environ, GUARD_ENV, "enforce")
            try:
                repo.update_fields(entity, {"name": "New"})
            except NoteAlreadyExists:
                pass
            except ValueError as exc:
                raise AssertionError(
                    f"a bare ValueError means the destination was PRE-CHECKED; "
                    f"the syscall is the only authority on occupancy: {exc}")
            else:
                raise AssertionError(
                    "an occupied destination must come back as NoteAlreadyExists")

            assert _filenames(vault) == names
            assert b.read_bytes() == b_bytes, (
                "os.link failed before anything was written to the destination")
            assert parse_markdown_file(a).frontmatter["name"] == "New", (
                "the content write COMMITTED — which is the residual, and the "
                "assertion an implementation refusing early would fail")
            assert a.read_bytes() != a_bytes
            assert "Old" not in _aliases_of(a)
            assert _same_file(repo._resolve_write_target(entity), a), (
                "the door raised above its re-stamp")

            # NOT-A-REPAIR: a re-run is safe and completes nothing, because the
            # trigger now reads the committed name back out of the note.
            calls = _recording_move_note(monkey, _base_module())
            repo.update_fields(entity, {"name": "New"})
            assert calls == [], f"the re-run attempted a move: {calls}"
            assert _filenames(vault) == names

            # THE DOCUMENTED RECOVERY: remove the cause (the direction table's
            # MERGE, performed here as the conductor would by hand), then call
            # the door DIRECTLY.
            b.unlink()
            moved = repo.rename_note(entity, "@New.md")

        assert _same_file(moved, vault / "@New.md")
        assert not a.exists()
        assert "Old" in _aliases_of(moved)
        assert _same_file(repo._resolve_write_target(entity), moved)


def _update_fields_refuses_a_no_provenance_name_change():
    """THE NO-PROVENANCE NAME CHANGE, REFUSED BEFORE THE WRITE — the arm no
    existing battery reaches, plus the alias reconciliation."""
    with temp_dir() as tmp:
        vault = Path(tmp) / "vault"
        vault.mkdir()
        subject = _write(vault / "@Unstamped One.md", _person_note("Unstamped One"))
        before = subject.read_bytes()
        names = _filenames(vault)

        # The repository CAN answer this name; the ENTITY carries no stamp.
        repo = PersonRepository(vault)
        unstamped = parse_markdown_content(
            subject.read_text(encoding="utf-8"), Person).entity
        assert repo._resolve_write_target(unstamped) is None
        assert repo.get_file_path("Unstamped One") is not None

        with patcher() as monkey:
            monkey.setitem(os.environ, GUARD_ENV, "enforce")
            try:
                repo.update_fields(unstamped,
                                   {"name": "Renamed One", "title": "t"})
            except ValueError as exc:
                assert NO_PROVENANCE_PRECONDITION in str(exc), str(exc)
            else:
                raise AssertionError(
                    "a name change on an entity with no provenance must refuse")
            assert _filenames(vault) == names
            assert subject.read_bytes() == before, (
                "the refusal must precede the content write — a byte-identical "
                "note is what distinguishes refusing early from refusing late")

            # NOT "refuse every unstamped update": the same entity's non-rename
            # update still writes, and so does a PATCH echoing the SAME name.
            repo.update_fields(unstamped, {"title": "still writes"})
            assert "still writes" in subject.read_text(encoding="utf-8")
            repo.update_fields(unstamped, {"name": "Unstamped One"})
            assert _filenames(vault) == names

            # THE ALIAS RECONCILIATION, pinned while a stamped subject is in hand.
            stamped_path = _write(vault / "@Alias Seed.md", _person_note("Alias Seed"))
            stamped = repo._load_file(stamped_path)
            repo.update_fields(stamped, {"name": "Alias Moved",
                                         "aliases": ["Caller Supplied"]})

        moved = vault / "@Alias Moved.md"
        assert moved.exists()
        assert set(_aliases_of(moved)) == {"Caller Supplied", "Alias Seed"}, (
            f"the door must not overwrite the caller's list with the parsed "
            f"one: {_aliases_of(moved)}")


def _no_caller_holds_a_note_lock_across_the_door():
    """THE LOCK-ORDERING RULE, STRUCTURALLY — ordering decision 5 made checkable.

    `move_note` takes two locks in a global sorted order and each path-taking
    leaf takes its OWN lock on a path the calling frame did not lock, so a held
    outer lock is the one configuration that sorted order cannot defend.
    """
    files = python_files_under(PACKAGE_ROOT)
    live = door_calls_inside_note_lock(files, WRITER_PATH)
    assert live == [], (
        f"a caller holds a note lock across a two-lock door or a path-taking "
        f"leaf: {live}")

    refused = {
        # the deadlock shape a reentrancy argument would wave through
        "refused_move_inside_lock.py": """
class Repo:
    def relocate(self, p, q):
        with vault_io.note_lock(p):
            vault_io.move_note(p, q)
""",
        # a path-taking leaf, which takes its OWN lock on a path this frame did
        # not lock
        "refused_leaf_inside_lock.py": """
class Repo:
    def touch(self, p, q):
        with vault_io.note_lock(p):
            update_frontmatter_field(q, "aliases", [])
""",
        # THE DERIVED THIRD CLAUSE — a repository method that itself calls
        # `move_note`, called from inside a lock. This is the exact placement
        # error the finding is about, refused by the scan and not by prose.
        "refused_mover_method_inside_lock.py": """
class Repo:
    def rename_note(self, entity, new_filename):
        return vault_io.move_note(entity, new_filename)

    def update_fields(self, entity, updates):
        with vault_io.note_lock(self.path):
            self.rename_note(entity, "@x.md")
""",
    }
    accepted = {
        # `write_markdown_file`'s own shape — a SINGLE-PATH door inside its own
        # lock, which MUST stay legal (`vault_io._require_lock` demands it).
        "accepted_single_path_door_inside_lock.py": """
def write_it(file_path, text):
    with vault_io.note_lock(file_path) as resolved:
        vault_io.create_note(resolved, text)
        vault_io.write_note(resolved, text, precondition=None)
""",
        # the shape Task 6 ships: the door is called AFTER the block has exited.
        "accepted_move_after_the_block.py": """
class Repo:
    def update_fields(self, entity, updates):
        with vault_io.note_lock(self.path):
            pass
        return vault_io.move_note(self.path, "@x.md")
""",
    }
    with temp_dir() as tmp:
        root = Path(tmp) / "lock-plants"
        root.mkdir()
        for name, source in {**refused, **accepted}.items():
            _write(root / name,
                   "from obsidian_schemas import vault_io\n"
                   "from obsidian_schemas.writer import update_frontmatter_field\n"
                   + source)
        found = door_calls_inside_note_lock(python_files_under(root), WRITER_PATH)
        flagged = {Path(site.module).name for site in found}
        assert flagged == set(refused), (
            f"the scan must flag exactly the refused plants; flagged {flagged}")


def _m1_the_destination_is_contained():
    """(M1) — the door refuses a destination whose RESOLVED path leaves the
    vault, in each of the escape's three reachable spellings, while an ordinary
    in-vault destination and one inside an in-vault SUBDIRECTORY both still
    move — so the clause is not "refuse everything"."""
    with temp_dir() as tmp:
        vault = Path(tmp) / "vault"
        vault.mkdir()
        outside = _write(Path(tmp) / "outside" / "@Outside Note.md",
                         _person_note("Outside Note"))
        subject = _write(vault / "@Contained Subject.md",
                         _person_note("Contained Subject"))
        repo = PersonRepository(vault, auto_load=False)
        entity = repo._load_file(subject)

        traversing = os.path.relpath(outside, vault)
        absolute = str(outside)
        symlinked = "@Symlink Destination.md"
        (vault / symlinked).symlink_to(outside)

        before = _filenames(vault)
        links_before = outside.stat().st_nlink
        with patcher() as monkey:
            monkey.setitem(os.environ, GUARD_ENV, "enforce")
            for spelling in (traversing, absolute, symlinked):
                try:
                    repo.rename_note(entity, spelling)
                except ValueError as exc:
                    assert "outside the vault" in str(exc), str(exc)
                else:
                    raise AssertionError(
                        f"an escaping destination must be refused: {spelling!r}")
            assert _filenames(vault) == before
            assert outside.stat().st_nlink == links_before, (
                "the outside file was hard-linked to")

            # ACCEPTED: an ordinary in-vault destination…
            moved = repo.rename_note(entity, "@Contained Moved.md")
            assert _same_file(moved, vault / "@Contained Moved.md")
            # …and one inside an in-vault SUBDIRECTORY. The directory must exist
            # first: `os.link` against a missing parent raises into a
            # WriteFailedError, which would redden this cell for a reason that
            # has nothing to do with M1.
            (vault / "People").mkdir()
            nested = repo.rename_note(entity, "People/@Contained Moved.md")
            assert _same_file(nested, vault / "People" / "@Contained Moved.md")


def _m3_the_staging_name_stays_in_the_md_namespace():
    """(M3) — the case-only two-step stages through a name inside the `*.md`
    namespace, so a rename interrupted between the two moves leaves a note every
    reader still sees.

    The `samefile` branch is forced with a HARD LINK rather than with a case
    variant, so the arm runs identically on a case-sensitive and a
    case-insensitive filesystem (the same-file sweep names a second hard link as
    a member of this branch). Its second move then raises `NoteAlreadyExists` —
    which is the INTERRUPTED state M3 exists to make visible.
    """
    base = _base_module()
    with temp_dir() as tmp:
        vault = Path(tmp) / "vault"
        vault.mkdir()
        subject = _write(vault / "@Staging Subject.md",
                         _person_note("Staging Subject"))
        linked = vault / "@Staging Linked.md"
        os.link(subject, linked)

        repo = PersonRepository(vault, auto_load=False)
        entity = repo._load_file(subject)
        real = base.vault_io.move_note
        calls = []
        in_window = {}

        def recorder(src, dest):
            calls.append((Path(src), Path(dest)))
            # The window observation: while the note sits at the staging name,
            # is it matched by the very enumeration `BaseRepository.load` uses?
            in_window[len(calls)] = {p.name for p in vault.glob(repo.file_pattern)}
            return real(src, dest)

        with patcher() as monkey:
            monkey.setitem(os.environ, GUARD_ENV, "enforce")
            monkey.setattr(base.vault_io, "move_note", recorder)
            try:
                repo.rename_note(entity, linked.name)
            except NoteAlreadyExists:
                pass
            else:
                raise AssertionError(
                    "the second move of the two-step must refuse: the "
                    "destination's own directory entry is still present")

        assert len(calls) == 2, f"the two-step recorded {calls}"
        for src, dest in calls:
            assert src.suffix == ".md" and dest.suffix == ".md", (
                f"a move left the `*.md` namespace: {src} -> {dest}")
        staging = calls[1][0]
        assert staging.name.endswith(".rename-tmp.md")
        assert staging.name in in_window[2], (
            f"the staging note is invisible to `load`'s own glob "
            f"({repo.file_pattern}): {sorted(in_window[2])}")
        assert staging.exists(), (
            "M3's whole point: the interrupted residual is a VISIBLE note")

        # The near-miss, so the assertion above is shown to discriminate rather
        # than to hold vacuously.
        rejected = subject.with_name(linked.name + ".rename-tmp")
        rejected.write_text("", encoding="utf-8")
        assert rejected.name not in {p.name for p in vault.glob(repo.file_pattern)}, (
            "the REJECTED staging spelling must be invisible to that glob — "
            "which is why it is rejected")
        rejected.unlink()


def _m4_the_audit_line_names_both_ends():
    """(M4) — the audit line names the SOURCE as well as the destination, so a
    relocation performed by `update_fields` on a consumer's behalf is
    reconstructable from logs. Captured at INFO: `captured_logs` defaults to
    WARNING and the door logs at INFO, so the default would capture nothing."""
    with temp_dir() as tmp:
        vault = Path(tmp) / "vault"
        vault.mkdir()
        old = _write(vault / "@Audited Old.md", _person_note("Audited Person"))
        repo = PersonRepository(vault, auto_load=False)
        entity = repo._load_file(old)
        with patcher() as monkey:
            monkey.setitem(os.environ, GUARD_ENV, "enforce")
            with captured_logs(level=logging.INFO) as records:
                moved = repo.rename_note(entity, "@Audited New.md")
        messages = [record.getMessage() for record in records]
        assert any(old.name in message and moved.name in message
                   for message in messages), (
            f"the rename audit line must name BOTH ends: {messages}")


def _m6_the_door_fails_closed_under_a_non_enforcing_guard():
    """(M6) — the door refuses while the write guard is not enforcing, because
    every occupied-destination refusal this item relies on is conditional on it:
    under `observe`, door 3 does `os.replace` and DESTROYS the occupied note.

    Pinned BOTH ways, and the `enforce` half sets the variable EXPLICITLY rather
    than inheriting whatever the runner carries (WI-149).
    """
    with temp_dir() as tmp:
        vault = Path(tmp) / "vault"
        vault.mkdir()
        a = _write(vault / "@Guarded A.md", _person_note("Guarded A"))
        b = _write(vault / "@Guarded B.md", _person_note("Guarded B"))
        free = "@Guarded Free.md"
        a_bytes, b_bytes, names = a.read_bytes(), b.read_bytes(), _filenames(vault)

        repo = PersonRepository(vault, auto_load=False)
        entity = repo._load_file(a)

        # REFUSED, under `observe` — an occupied destination AND an ordinary one,
        # so the clause is the capability-level refusal it is specified as.
        with patcher() as monkey:
            monkey.setitem(os.environ, GUARD_ENV, "observe")
            for destination in (b.name, free):
                try:
                    repo.rename_note(entity, destination)
                except NoteAlreadyExists as exc:
                    raise AssertionError(
                        f"the door reached move_note under `observe`: {exc}")
                except ValueError as exc:
                    assert "write guard" in str(exc), str(exc)
                else:
                    raise AssertionError(
                        f"a rename under `observe` must refuse: {destination}")
            assert _filenames(vault) == names
            assert a.read_bytes() == a_bytes and b.read_bytes() == b_bytes

            # …and `update_fields` refuses the same condition EARLIER, before its
            # content write, so nothing is half-applied.
            try:
                repo.update_fields(entity, {"name": "Guarded Renamed",
                                            "title": "t"})
            except ValueError as exc:
                assert WRITE_GUARD_PRECONDITION in str(exc), str(exc)
            else:
                raise AssertionError(
                    "a name change under `observe` must refuse before the write")
            assert a.read_bytes() == a_bytes, (
                "the refusal must precede the content write")
            assert _filenames(vault) == names

            # A NON-rename update under the same mode still succeeds, so the
            # widened predicate refuses name changes and not every update.
            repo.update_fields(entity, {"title": "observe-still-writes"})
            assert "observe-still-writes" in a.read_text(encoding="utf-8")

        # ACCEPTED, under an EXPLICIT `enforce`: the occupied destination raises
        # NoteAlreadyExists with both files byte-identical, and the ordinary
        # in-vault rename MOVES.
        b_bytes = b.read_bytes()
        with patcher() as monkey:
            monkey.setitem(os.environ, GUARD_ENV, "enforce")
            a_bytes = a.read_bytes()
            try:
                repo.rename_note(entity, b.name)
            except NoteAlreadyExists:
                pass
            else:
                raise AssertionError("an occupied destination must refuse")
            assert a.read_bytes() == a_bytes and b.read_bytes() == b_bytes
            moved = repo.rename_note(entity, free)
        assert _same_file(moved, vault / free)
        assert not a.exists()


def _plant_book(vault: Path, title: str, author: str, filename=None) -> Path:
    """A book note's BYTES. `filename=None` plants it AT its own derived name."""
    name = filename or f"{title} - {author}.md"
    return _write(vault / name, _book_note(title, author))


def _m7_update_fields_refuses_a_name_delta_on_a_type_declaring_none():
    """(M7) — `update_fields` refuses a `name` delta on a type that does not
    DECLARE `name`, pinned BOTH ways, and this arm's subject is a BOOK.

    Without the disjunct that file comes back carrying the ungated caller-supplied
    `name:` at its old filename, with no alias and an exception after a successful
    write — and the new detector cannot see it, because it fires only on
    `entity_type == "person"`.
    """
    with temp_dir() as tmp:
        vault = Path(tmp) / "vault"
        vault.mkdir()
        book = _plant_book(vault, "Refusing Ledger", "Quill Marrow")
        book_bytes, names = book.read_bytes(), _filenames(vault)
        repo = BookRepository(vault, auto_load=False)
        entity = repo._load_file(book)
        assert entity is not None
        assert "name" not in type(entity).model_fields

        with patcher() as monkey:
            monkey.setitem(os.environ, GUARD_ENV, "enforce")
            for spelling in ("x/y", "a/../../x"):
                try:
                    repo.update_fields(entity, {"name": spelling,
                                                "status": "read"})
                except ValueError as exc:
                    assert NAME_DECLARATION_PRECONDITION in str(exc), (
                        f"the refusal must name the TYPE-DECLARATION "
                        f"precondition, not a sibling disjunct: {exc}")
                else:
                    raise AssertionError(
                        f"a `name` delta on a Book must refuse: {spelling!r}")
                assert book.read_bytes() == book_bytes, (
                    "the refusal must precede the content write")
                assert _filenames(vault) == names

            # ACCEPTED (1) the SAME book's non-`name` update still succeeds and
            # lands in that file.
            repo.update_fields(entity, {"status": "read"})
            assert 'status: read' in book.read_text(encoding="utf-8")
            assert _filenames(vault) == names

            # ACCEPTED (2) a PERSON's name change in the same vault still MOVES.
            person_path = _write(vault / "@Person Control.md",
                                 _person_note("Person Control"))
            people = PersonRepository(vault, auto_load=False)
            person = people._load_file(person_path)
            people.update_fields(person, {"name": "Person Moved"})
            assert (vault / "@Person Moved.md").exists()
            assert not person_path.exists()

            # ACCEPTED (3) a book note that STORES `name:` as a pydantic EXTRA is
            # ALSO refused — the arm that fails an `entity.model_fields` or
            # `hasattr(entity, "name")` spelling.
            extra = _write(vault / "Extra Ledger - Quill Marrow.md",
                           _book_note("Extra Ledger", "Quill Marrow").replace(
                               "tags: [book]", 'name: "Stored Extra"\ntags: [book]'))
            extra_bytes = extra.read_bytes()
            with_extra = repo._load_file(extra)
            assert with_extra.model_extra.get("name") == "Stored Extra"
            try:
                repo.update_fields(with_extra, {"name": "Something Else"})
            except ValueError as exc:
                assert NAME_DECLARATION_PRECONDITION in str(exc), str(exc)
            else:
                raise AssertionError(
                    "a book storing `name:` as an EXTRA must refuse too")
            assert extra.read_bytes() == extra_bytes


def _m8_update_fields_refuses_a_delta_that_moves_the_filename_rule():
    """(M8) — `update_fields` refuses a delta that moves the entity type's OWN
    filename rule when no rename will follow it, pinned BOTH ways and written to
    cover the RULE rather than one field."""
    with temp_dir() as tmp:
        vault = Path(tmp) / "vault"
        vault.mkdir()
        book = _plant_book(vault, "Ruled Ledger", "Quill Marrow")
        meeting = _write(vault / f"Meeting 20260301 - {MEETING_TOPIC}.md",
                         _meeting_note(MEETING_DATE, MEETING_TOPIC, "m8-1"))
        divergent = _plant_book(vault, "Divergent Ledger", "Quill Marrow",
                                filename="Some Other Filename.md")
        names = _filenames(vault)

        books = BookRepository(vault, auto_load=False)
        meetings = MeetingRepository(vault, auto_load=False)
        book_entity = books._load_file(book)
        meeting_entity = meetings._load_file(meeting)
        divergent_entity = books._load_file(divergent)

        with patcher() as monkey:
            monkey.setitem(os.environ, GUARD_ENV, "enforce")

            # REFUSED — four cells spanning both types and four of the SIX
            # deriving fields, so the clause is shown to read the RULE and not a
            # remembered field.
            cells = (
                (books, book_entity, book, {"title": "New Title"}),
                (books, book_entity, book, {"author": "New Author"}),
                (meetings, meeting_entity, meeting, {"date": "2026-01-01"}),
                (meetings, meeting_entity, meeting, {"topics": ["Other"]}),
            )
            for repo, entity, path, delta in cells:
                before = path.read_bytes()
                try:
                    repo.update_fields(entity, delta)
                except ValueError as exc:
                    assert FILENAME_RULE_PRECONDITION in str(exc), (
                        f"the refusal must name the FILENAME-RULE precondition, "
                        f"not a sibling clause: {exc}")
                else:
                    raise AssertionError(
                        f"a delta moving the filename rule must refuse: {delta}")
                assert path.read_bytes() == before, (
                    "the refusal must precede the content write — without the "
                    "clause the file comes back carrying the new value at its "
                    "old filename with no alias and no exception")
                assert _filenames(vault) == names

            # ACCEPTED (1) and (2) — a delta the rule does not read, per type.
            books.update_fields(book_entity, {"status": "read"})
            assert "status: read" in book.read_text(encoding="utf-8")
            meetings.update_fields(meeting_entity, {"tags": ["x"]})
            assert "- x" in meeting.read_text(encoding="utf-8")
            assert _filenames(vault) == names

            # ACCEPTED (3) — an ALREADY-DIVERGENT book still accepts a delta that
            # leaves its rule where it found it. This is the arm that fails a
            # `derive(projected) != file_path.name` spelling, which would refuse
            # every write to the population this item exists to repair.
            assert books._get_file_name(divergent_entity) != divergent.name
            books.update_fields(divergent_entity, {"status": "read"})
            assert "status: read" in divergent.read_text(encoding="utf-8")

            # ACCEPTED (4) — a PERSON name change in the same vault still moves:
            # the control that fails a clause reaching a repository declaring no
            # `_get_file_name`, or one written without the `not renaming`
            # conjunct.
            person_path = _write(vault / "@M8 Control.md", _person_note("M8 Control"))
            people = PersonRepository(vault, auto_load=False)
            people.update_fields(people._load_file(person_path),
                                 {"name": "M8 Moved"})
            assert (vault / "@M8 Moved.md").exists() and not person_path.exists()

            # REFUSED, fail-CLOSED — a NON-STRING value for a deriving field is
            # refused with the SAME ValueError and never with an AttributeError
            # leaking out of `_get_file_name`.
            before = book.read_bytes()
            try:
                books.update_fields(book_entity, {"title": ["a", "b"]})
            except ValueError as exc:
                assert FILENAME_RULE_PRECONDITION in str(exc), str(exc)
            except (AttributeError, TypeError) as exc:
                raise AssertionError(
                    f"the rule's own exception leaked out of _get_file_name: {exc}")
            else:
                raise AssertionError("a non-string deriving field must refuse")
            assert book.read_bytes() == before


# ===========================================================================
# Task 14 — every standing wall this item joins, RUN on the final text
# ===========================================================================
#
# The OUTBOUND question — does this item's own wall hold? — is AC-5's check in
# `tests/test_write_target_seam_wall.py`. This is the INBOUND half: which
# STANDING walls sweep the files this item adds and edits, and does each one's
# claim hold of them.
#
# MEMBERSHIP is closed by CALLING each predicate on the files' FINAL text, never
# by reasoning about which shapes match: the outcome turns on incidental
# spellings a reader cannot see, and `## Wall Membership`'s own rule is that a
# row satisfied by reasoning is a row nobody ran.

#: The package and script files this item creates or edits, repo-relative.
#: Every one of these JOINS the standing walls' universes.
WI029_TOUCHED_PACKAGE_FILES = (
    "obsidian_schemas/models.py",
    "obsidian_schemas/parser.py",
    "obsidian_schemas/repositories/base.py",
    "obsidian_schemas/repositories/person.py",
    "obsidian_schemas/repositories/book.py",
    "obsidian_schemas/repositories/meeting.py",
    "scripts/lint_vault.py",
)

#: The test modules this item creates or edits. Only ONE standing assertion has
#: a universe that GROWS when a test file is added — the single-`ast`-home one —
#: and it is a set EQUALITY, so every module below has exactly one legal way to
#: obtain syntax: import a predicate from the shared scan module.
WI029_TOUCHED_TEST_FILES = (
    "tests/derivations.py",
    "tests/test_provenance_write_seam.py",
    "tests/test_write_target_seam_wall.py",
    "tests/test_stem_name_divergence_detector.py",
    "tests/test_stem_divergence_baseline_shape.py",
    "tests/test_company_name_contract.py",
)

#: The four modules this item AUTHORS, and the AC-named check each must expose
#: as a top-level zero-argument `def`. This is the check-contract row's oracle:
#: the conveyor discovers a `kind: test` check by SOURCE scan and invokes it with
#: no arguments, so a fixture parameter is a `TypeError` at criterion time and a
#: `return False` exits 0 and reads as PASS.
WI029_AUTHORED_MODULES = {
    "tests/test_provenance_write_seam.py": (
        "test_the_parse_stamps_provenance_and_the_stamp_cannot_reach_a_note",
        "test_the_seam_returns_the_stamp_only_inside_this_vault",
        "test_no_library_write_can_fork_a_person_note",
        "test_a_person_note_is_renamed_only_through_the_one_door_and_stays_reachable",
        "test_every_wall_this_item_joins_is_run_on_the_final_text",
    ),
    "tests/test_write_target_seam_wall.py": (
        "test_every_write_site_resolves_its_target_through_the_one_seam",
    ),
    "tests/test_stem_name_divergence_detector.py": (
        "test_lint_vault_reports_stem_name_divergence_and_never_repairs_it",
    ),
    "tests/test_stem_divergence_baseline_shape.py": (
        "test_the_stem_divergence_live_baseline_is_committed_and_shaped",
        "test_the_baseline_readers_reach_their_claimed_shapes",
    ),
}

REPO_ROOT = PACKAGE_ROOT.parent


def _touched(names):
    return [REPO_ROOT / name for name in names]


def test_every_wall_this_item_joins_is_run_on_the_final_text():
    """Task 14. Zero-arg and raising, per the check contract.

    Thirteen rows of `## Wall Membership`. Eleven are a direct predicate call
    below; the remaining two are discharged by a RUN that is not one and are
    DECLARED as such rather than skipped (WI-301's own clause) — the
    corpus-freeze row runs as `tests/test_fixture_vault.py` under the floor
    command, and the check-contract row is the conveyor's per-criterion
    invocation, for which this check asserts the contract's two MECHANICAL
    halves over the authored modules' source instead.
    """
    package = _touched(WI029_TOUCHED_PACKAGE_FILES)
    tests_touched = _touched(WI029_TOUCHED_TEST_FILES)
    for path in package + tests_touched:
        assert path.exists(), f"{path} — a Write Target that is not on disk"

    _wi029_walls_a_b_and_c(package)
    _wi029_wall_d(package)
    _wi029_ast_stays_single_homed()
    _wi029_skip_reason_vocabulary_keeps_its_two_homes()
    _wi029_gate_wall_over_the_touched_package_files(package)
    _wi029_single_home_walls_over_the_routing_slice(package)
    _wi029_lint_vault_issue_is_not_auto_fixable()
    _wi029_no_literal_vault_path_on_an_authored_line()
    _wi029_the_deleted_identity_attribute_is_named_nowhere()
    _wi029_the_check_contracts_two_mechanical_halves()
    _wi029_every_count_pin_task_one_recorded_is_unmoved()


def _wi029_walls_a_b_and_c(package):
    """Walls A/B/C — `tests/test_write_routing.py:test_filesystem_mutation_is_
    single_homed`, whose universe is (PACKAGE_ROOT, SCRIPTS_ROOT).

    The door MOVES a file, so this is the row most likely to be RED: the whole
    reason `rename_note` goes through `vault_io.move_note` rather than
    `Path.rename` is this wall. `Path.resolve`, `Path.exists`, `Path.samefile`
    and `Path.is_relative_to` are READS and legal; M6's `vault_io.guard_mode()`
    is a call on the already-imported module and names no `os` member, which is
    exactly why the mode is read through that function and not `os.environ`.
    """
    offenders = [u for u in filesystem_mutation_uses(package)
                 if u.module != "obsidian_schemas/vault_io.py"]
    assert not offenders, (
        "a filesystem-mutation capability is named outside the one permitted "
        "home. The fix is to route through vault_io — NEVER to add an "
        "exemption. Found: "
        + ", ".join(f"{u.module}:{u.lineno} ({u.qualname})" for u in offenders))

    os_offenders = [u for u in os_module_attribute_uses(package)
                    if u.module != "obsidian_schemas/vault_io.py"
                    and u.qualname.split(".", 1)[1] not in OS_READONLY_NAMES]
    assert not os_offenders, (
        "a non-read-only `os` member is reached outside the door: "
        + ", ".join(f"{u.module}:{u.lineno} ({u.qualname})"
                    for u in os_offenders))

    import_offenders = [u for u in module_import_uses(
        package, frozenset(FS_MODULES - {"os"}))
        if u.module != "obsidian_schemas/vault_io.py"]
    assert not import_offenders, (
        "a mutation-capable module is imported outside the door: "
        + ", ".join(f"{u.module}:{u.lineno} ({u.qualname})"
                    for u in import_offenders))


def _wi029_wall_d(package):
    """Wall D (`tests/test_name_gate_wall.py:_check_wall_d`) — no touched file
    gains a `parse_markdown_file` caller. The door reads nothing.

    This row was named in `## Wall Membership` and NOT called by an earlier
    draft of this task, which is the exact failure WI-301's rule exists to
    close. Running it returned something that section did not name, so the
    membership rule's other clause applies (name it, satisfy it, never narrow
    the wall): the row's requirement reads "outside
    `obsidian_schemas/repositories/base.py`", and that under-reaches — `Book`
    and `Meeting` carry standing `_load_file` OVERRIDES that parse, and both
    files joined this item's touched list at Task 5.

    The satisfying form is stronger than the one the row states, not weaker: the
    parse callers over the touched package files are asserted EQUAL to the three
    `_load_file` implementations, which `load_file_implementations` derives
    INDEPENDENTLY of this call and which Task 1 pins at three. A module-level
    permitted list would have blessed whatever happened to be there; this says
    exactly which FUNCTIONS may parse, so a parse call added to the door — or to
    `save`, or to a body-writer, in any of these files — is RED.

    The universe is the touched PACKAGE files. The test modules are excluded by
    construction and not by exemption: driving `parse_markdown_file` IS Task 2's
    battery, and wall D's own universe at its home is package-and-scripts.
    """
    callers = functions_calling(package, "parse_markdown_file")
    loaders = load_file_implementations(
        base_repository_subclasses(python_files_under(PACKAGE_ROOT)))
    assert callers, "the parse-caller scan resolved nothing — a vacuous pass"
    assert callers == loaders, (
        "the set of functions parsing through `parse_markdown_file` is no "
        "longer exactly the three `_load_file` implementations. Added: "
        f"{sorted(callers - loaders)}; removed: {sorted(loaders - callers)}")


def _wi029_ast_stays_single_homed():
    """The one standing assertion whose universe GROWS when this item adds a
    test file, and it is a set EQUALITY — so four new test modules and two new
    package functions each have exactly one legal way to obtain syntax."""
    universe = python_files_under(PACKAGE_ROOT, TESTS_ROOT)
    assert universe, "the file list is empty — the equality below is vacuous"
    homes = {u.module for u in modules_using_ast(universe)}
    assert homes == {"tests/derivations.py"}, (
        f"the `ast` capability must stay single-homed; found {sorted(homes)}")
    for name in WI029_TOUCHED_TEST_FILES + WI029_TOUCHED_PACKAGE_FILES:
        if name == "tests/derivations.py":
            continue
        assert name not in homes, f"{name} names `ast`, which it may not"


def _wi029_skip_reason_vocabulary_keeps_its_two_homes():
    """`skip_reason_literal_sites` over the WIDENED universe, a set EQUALITY.
    Four new test modules join that universe and none may hand-type a
    `SKIP_REASONS` member — importing it is the only legal way."""
    from obsidian_schemas.repositories.base import SKIP_REASONS

    widened = python_files_under(PACKAGE_ROOT, TESTS_ROOT, SCRIPTS_ROOT)
    names = {p.relative_to(REPO_ROOT).as_posix() for p in widened}
    assert "scripts/lint_vault.py" in names, (
        "the widened universe does not reach the script; the equality below "
        "would be green because nobody looked")
    for name in WI029_TOUCHED_TEST_FILES:
        assert name in names, f"{name} is outside the widened universe"

    homes = skip_reason_literal_sites(widened, SKIP_REASONS)
    assert homes == {
        "obsidian_schemas/repositories/base.py",
        "tests/test_fixture_vault.py",
    }, f"the skip-reason vocabulary has a third hand-typed home: {sorted(homes)}"


def _wi029_gate_wall_over_the_touched_package_files(package):
    """WI-021's arm sweep and its two gate pins, over the touched package files.

    This item adds NO frontmatter write arm: the door delegates its alias append
    to `writer.update_frontmatter_field`, which already carries a gate call, and
    `update_fields`' own arm is unchanged. So the requirement is that every arm
    these files DO carry still routes and still resolves a declaration — a
    property the door's insertion could have broken by splitting a function.
    """
    arms = set(frontmatter_write_arms(package))
    assert arms, "the arm sweep resolved nothing over the touched files"
    declarations = gate_call_declarations(package)
    placements = gate_call_placement(package)

    unrouted = arms - set(declarations)
    assert not unrouted, (
        f"these write arms reach vault bytes with no gate call: {sorted(unrouted)}")
    unplaced = arms - set(placements)
    assert not unplaced, (
        f"these write arms have no resolvable gate placement: {sorted(unplaced)}")
    absent = {arm for arm in arms if declarations.get(arm) == "absent"}
    assert absent == set(), (
        f"no arm may omit the declared_type keyword; found {sorted(absent)}")

    # `apply_fixes` must still report EXACTLY ONE arm — the new detector emits an
    # issue and writes nothing, so no branch may have acquired its own.
    script_arms = [a for a in arms if a.module == "scripts/lint_vault.py"]
    assert len(script_arms) == 1 and script_arms[0].qualname == "apply_fixes", (
        f"scripts/lint_vault.py's frontmatter arms moved: {script_arms}")


def _wi029_single_home_walls_over_the_routing_slice(package):
    """Two single-home walls whose own universe is the ROUTING one and does not
    reach `tests/`. Run over the touched files INSIDE that universe: the
    requirement is that this item adds no second implementation of either job,
    and asserting a zero over `tests/` instead would invent a wall nobody
    declared."""
    slice_ = [p for p in package
              if p.is_relative_to(PACKAGE_ROOT) or p.is_relative_to(SCRIPTS_ROOT)]
    assert slice_, "the routing-universe slice is empty"
    assert character_class_strip_sites(slice_) == [], (
        "Book's and Meeting's existing `[<>:\"/\\|?*]` strips must not be moved "
        "or copied, and no third one may appear")
    assert address_splitting_implementations(slice_) == set(), (
        "this item adds no second address splitter")


def _wi029_lint_vault_issue_is_not_auto_fixable():
    """`auto_fixable_emitter_checks` / `auto_fixable_branch_checks` over the
    script, pinned to each other. AC-3(d) says `stem_name_divergence` is never
    auto-fixable; this is the derived half of that claim, and it is what keeps
    the WI-026 baseline's §1 rows and the census-to-rule mapping green."""
    script = [SCRIPTS_ROOT / "lint_vault.py"]
    emitters = auto_fixable_emitter_checks(script)
    branches = auto_fixable_branch_checks(script)
    assert emitters, "the emitter scan resolved no auto-fixable rule at all"
    assert emitters == branches, (
        f"the advertised and the repairable rule sets disagree: "
        f"emitters-only {sorted(emitters - branches)}, "
        f"branches-only {sorted(branches - emitters)}")
    assert "stem_name_divergence" not in emitters, (
        "the new check advertises an auto-fix. Relocation is the "
        "highest-blast-radius act in this tool and the per-note repair "
        "direction is a judgement no auto-fix can make")
    assert "stem_name_divergence" not in branches, (
        "`apply_fixes` grew a branch for the new check")


def _wi029_no_literal_vault_path_on_an_authored_line():
    """`FORBIDDEN_DEFAULT_PATTERNS` via the shipped wall's own line reader, over
    the files this item AUTHORS.

    Load-bearing rather than redundant: that wall's universe stops at
    ("obsidian_schemas", "scripts") and does not reach `tests/`, so a hard-coded
    vault path in one of the four new check modules is reached by nothing else.

    SCOPED to the authored files for a reason that is a property of the
    predicate: `_code_lines` is a TEXT scan, so a line that FORBIDS one of these
    patterns necessarily contains it, and the tree already carries such lines
    (`tests/test_fixture_vault.py`'s own privacy assertion). Widening this run
    would go RED on them, and the two available greens — an exception list, or a
    narrowed oracle — are each worse than the scoping.
    """
    from tests.test_vault_path_required import (
        FORBIDDEN_DEFAULT_PATTERNS,
        _code_lines,
    )

    authored = [REPO_ROOT / "scripts" / "lint_vault.py"]
    authored += [REPO_ROOT / name for name in WI029_AUTHORED_MODULES]
    offenders = [f"{path.relative_to(REPO_ROOT)}:{lineno}"
                 for path in authored
                 for lineno, line in _code_lines(path)
                 for pattern in FORBIDDEN_DEFAULT_PATTERNS
                 if pattern in line]
    assert offenders == [], (
        f"a caller-independent vault path survives as a default: {offenders}")


def _wi029_the_deleted_identity_attribute_is_named_nowhere():
    """WI-023's zero-sites pin on the deleted per-kind identity mapping
    (`tests/test_identity_endgame.py`), whose universe GROWS with every test
    module this item adds.

    The needle is ASSEMBLED FROM PARTS at its home precisely so a module under
    those roots is not its own counterexample, and it is IMPORTED here for the
    same reason: NOTHING in this module may spell that attribute whole — not a
    function name, not a docstring, not a comment, because the pin is a TEXT
    scan and cannot tell a mention from a use. This function's own name is
    deliberately periphrastic on that account. (Written the obvious way first,
    it made this module the pin's only offender at three sites, which is the
    cheapest possible demonstration that the scan is not vacuous.)

    Predicted green, and RUN: the row was named in `## Wall Membership` and not
    called by an earlier draft of this task.
    """
    from tests.test_identity_endgame import EMAIL_INDEX_ATTR, _literal_sites

    files = python_files_under(PACKAGE_ROOT, TESTS_ROOT)
    assert files, "the file list is empty — the zero below would be vacuous"
    assert _literal_sites(EMAIL_INDEX_ATTR, files) == [], (
        "the two-authority state is over: one mapping, one reader")


def _wi029_the_check_contracts_two_mechanical_halves():
    """The check-contract row, discharged by asserting its two MECHANICAL halves
    over the authored modules' SOURCE rather than by a predicate call — the
    enforcing run is the conveyor's own per-criterion invocation at
    `building -> done`, which no in-build predicate can perform.

    (1) `ensure_project_interpreter(__file__)` is the module's first statement,
    ahead of every package import — otherwise a foreign interpreter fails at
    `import pydantic` and the criterion reports a red that says nothing about
    the property it asserts.

    (2) Every AC-named function is a top-level zero-argument `def`. The conveyor
    calls `getattr(mod, name)()`, so a fixture parameter is a `TypeError` at
    criterion time; and it signals failure by RAISING, since a returned `False`
    exits 0 and is read as PASS.

    Read as TEXT and not as syntax: `ast` is single-homed to
    `tests/derivations.py`, and `_code_lines` is the shipped executable-line
    reader this repo already uses for exactly that reason.
    """
    from tests.test_vault_path_required import _code_lines

    bridge_import = "from tests.ac_interpreter import ensure_project_interpreter"
    bridge_call = "ensure_project_interpreter(__file__)"
    for name, checks in sorted(WI029_AUTHORED_MODULES.items()):
        path = REPO_ROOT / name
        lines = list(_code_lines(path))
        assert lines, f"{name} has no executable lines at all"
        assert lines[0][1].strip() == bridge_import, (
            f"{name}'s first statement is {lines[0][1].strip()!r}, not the "
            f"interpreter bridge import")
        assert lines[1][1].strip() == bridge_call, (
            f"{name}'s second statement is {lines[1][1].strip()!r}, not "
            f"{bridge_call}")
        package_imports = [n for n, line in lines
                           if line.startswith(("from obsidian_schemas",
                                               "import obsidian_schemas"))]
        if package_imports:
            assert min(package_imports) > lines[1][0], (
                f"{name} imports the package at line {min(package_imports)}, "
                f"ahead of the bridge call at {lines[1][0]}")
        source = path.read_text(encoding="utf-8")
        for check in checks:
            assert f"\ndef {check}():\n" in source, (
                f"{name} must expose {check} as a top-level ZERO-ARGUMENT def; "
                f"a fixture parameter is a TypeError when the conveyor calls it")


def _wi029_every_count_pin_task_one_recorded_is_unmoved():
    """Task 1's pins, re-run on the final text. The obligation is the LIST Task
    1 wrote into the Build Log, not a number: a pin that MOVED is edited to NAME
    its new member, never bumped."""
    files = python_files_under(PACKAGE_ROOT)
    writers = functions_reserializing_parsed_frontmatter(files)
    assert len(writers) == 4, (
        f"the four reserializing writers must survive the seam; got "
        f"{sorted(writers)}")
    guard = functions_parsing_then_writing(files) - writers
    assert {f.qualname for f in guard} == {"write_markdown_file"}, (
        f"the discrimination proof moved; got {sorted(guard)}")

    package_sites = non_completed_write_sites(files)
    assert len(package_sites) == 8, (
        f"the falsy-return universe over the package moved — `rename_note` must "
        f"RAISE and never return falsy: {sorted(package_sites)}")
    person_sites = non_completed_write_sites(
        [PACKAGE_ROOT / "repositories" / "person.py"])
    assert {s.qualname for s in person_sites} == {
        "PersonRepository.append_to_timeline",
        "PersonRepository.append_to_body_section",
        "PersonRepository.update_to_discuss_item",
        "PersonRepository.remove_to_discuss_item",
        "PersonRepository._get_body_content",
    }, (f"the five classified functions over person.py moved: "
        f"{sorted({s.qualname for s in person_sites})}")
    assert len(person_sites) == 8, (
        f"eight classified sites over person.py, found {len(person_sites)}")

    assert len(base_repository_subclasses(files)) == 4
    assert len(load_file_implementations(base_repository_subclasses(files))) == 3
