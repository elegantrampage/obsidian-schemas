"""WI-020 — AC-3 and AC-6: the batch load survives, and surfaces only what it owns.

The 4x3 matrix here is NOT uniform, and that is the specification rather than an
accident of fixtures: cell (a) is must-be-listed for three classes and
must-NOT-be-listed for BookRepository, whose catch-all glob gives it no
ownership evidence at all. A quantifier with one shared expectation table would
silently assert a uniformity nobody checked.
"""

import logging
import sys

import pytest

from obsidian_schemas import (
    BookRepository,
    CompanyRepository,
    MeetingRepository,
    PersonRepository,
)
from obsidian_schemas.repositories.base import VaultPathNotConfiguredError

from tests.derivations import (
    PACKAGE_ROOT,
    base_repository_subclasses,
    python_files_under,
)
from tests.support import captured_logs, patcher, temp_dir

SHARED_SCAN_MODULE = "tests.derivations"

MALFORMED_BODY = "notes: a: b: c"      # a stray unquoted colon


def _write(vault, name, text):
    (vault / name).write_text(text, encoding="utf-8")
    return vault / name


def _build_matrix_vault(v):
    """ONE heterogeneous vault, shared by all four repositories.

    A plain builder rather than a pytest fixture: AC-3's check is invoked by
    name with no arguments (tests/support.py), so it builds its own vault.

    Shared on purpose: PersonRepository and CompanyRepository declare neither
    _load_file nor file_pattern, so they run the SAME code over the SAME `@*.md`
    glob. A fix proven only from the person side gets the company direction
    backwards, and a comparison hardcoded to one type literal instead of
    self.type_name passes it.
    """
    # matches @*.md and *.md — no legible type at all
    _write(v, "@Malformed Person.md", f"---\ntype: person\n{MALFORMED_BODY}\n---\n\nbody\n")
    # owned-and-drifted, one per class, each derived from that class's OWN model
    _write(v, "@Drifted Person.md",
           "---\ntype: person\nname: Drifted P\nemails: not-a-list\n---\n\nbody\n")
    _write(v, "@Drifted Company.md",
           "---\ntype: company\nname: Drifted C\ntags: company\n---\n\nbody\n")
    _write(v, "Meeting Drifted.md",
           "---\ntype: meeting\nname: Drifted M\nattendees: not-a-list\n---\n\nbody\n")
    _write(v, "Book Drifted.md",
           "---\ntype: book\nname: Drifted B\ntitle: T\ntags: book\n---\n\nbody\n")
    # well-formed notes of each type — the foreign-type fixtures, and the
    # no-abort witnesses
    _write(v, "@Good Person.md", "---\ntype: person\nname: Good P\n---\n\nbody\n")
    _write(v, "@Good Company.md", "---\ntype: company\nname: Good C\n---\n\nbody\n")
    _write(v, "Meeting Malformed.md",
           f"---\ntype: meeting\n{MALFORMED_BODY}\n---\n\nbody\n")
    _write(v, "Meeting Good.md",
           "---\ntype: meeting\nname: Good M\nmeeting_id: m1\n---\n\nbody\n")
    _write(v, "Meeting Foreign.md", "---\ntype: person\nname: Foreign M\n---\n\nbody\n")
    _write(v, "Book Good.md", "---\ntype: book\nname: Good B\ntitle: T\n---\n\nbody\n")
    return v


def test_batch_load_survives_and_surfaces_only_owned_bad_notes():
    """AC-3. Zero-arg: the battery calls it by name, so it builds its own
    heterogeneous vault and installs its own log capture (tests/support.py).
    """
    with temp_dir() as vault:
        _check_batch_load_survives_and_surfaces_only_owned_bad_notes(
            _build_matrix_vault(vault))


def _check_batch_load_survives_and_surfaces_only_owned_bad_notes(matrix_vault):
    walk = python_files_under
    subclasses = base_repository_subclasses
    for derivation in (walk, subclasses):
        assert derivation.__module__ == SHARED_SCAN_MODULE, (
            f"{derivation.__name__} must come from the shared scan module"
        )

    # The class list is DERIVED FROM SOURCE, never from __subclasses__(): a
    # fifth repository module that repositories/__init__.py does not import is
    # invisible to the import graph at test time, so a runtime check would
    # reproduce the green-suite/zero-coverage gap it exists to close.
    discovered = subclasses(walk(PACKAGE_ROOT))

    # The CELLS are the map; the scan supplies its KEYS; an unmapped key fails.
    # (a) malformed YAML matching this class's glob
    # (b) this class's own type, drifted on one field
    # (c) a well-formed note of a foreign readable type
    matrix = {
        PersonRepository:  {"a": ("@Malformed Person.md", True),
                            "b": ("@Drifted Person.md", True),
                            "c": ("@Good Company.md", False)},
        CompanyRepository: {"a": ("@Malformed Person.md", True),
                            "b": ("@Drifted Company.md", True),
                            "c": ("@Good Person.md", False)},
        MeetingRepository: {"a": ("Meeting Malformed.md", True),
                            "b": ("Meeting Drifted.md", True),
                            "c": ("Meeting Foreign.md", False)},
        # The ONE non-uniform cell: a catch-all `*.md` glob is not ownership
        # evidence, so a malformed note with no legible type is NOT a skipped
        # book. Its (b) cell IS listed — the glob is irrelevant once `type:
        # book` is readable, because ownership is read off the raw type.
        BookRepository:    {"a": ("@Malformed Person.md", False),
                            "b": ("Book Drifted.md", True),
                            "c": ("@Good Person.md", False)},
    }
    assert discovered == set(matrix), (
        "the discovered concrete BaseRepository subclasses and the matrix's "
        f"class keys must match exactly; discovered {sorted(c.__name__ for c in discovered)}"
    )

    for cls, cells in matrix.items():
        # One capture per class — a fresh record list per iteration is what
        # caplog.clear() bought, and it is what keeps the WARNING assertion
        # below about THIS class's load rather than a sibling's.
        with captured_logs(level=logging.WARNING) as records:
            # PersonRepository and CompanyRepository are INDEPENDENTLY
            # instantiated against this same vault, each asserting its own list.
            repo = cls(matrix_vault)
            loaded = repo.load()

        # NO-ABORT, asserted on every one of the twelve cells: load() never
        # propagates, and the healthy notes still arrive. base.load()'s loop
        # wraps _load_file in no try of its own, so each class's own except IS
        # the entire margin between one bad note and an aborted batch.
        assert loaded >= 1, f"{cls.__name__} aborted the batch instead of skipping"

        skipped = {n.path.name for n in repo.skipped_notes}
        for cell, (filename, must_be_listed) in cells.items():
            if must_be_listed:
                assert filename in skipped, (
                    f"{cls.__name__} cell ({cell}): {filename} is OURS and "
                    f"un-loadable — it must be surfaced, not vanish. "
                    f"Skipped: {sorted(skipped)}"
                )
            else:
                assert filename not in skipped, (
                    f"{cls.__name__} cell ({cell}): {filename} is not this "
                    f"repository's to report — a skip surface that fills with "
                    f"other types' notes is noise, not signal. "
                    f"Skipped: {sorted(skipped)}"
                )

        assert repo.skipped_count == len(repo.skipped_notes)
        # The surface is a WARNING, not a debug line — that is the whole of C4.
        if skipped:
            warnings = [r for r in records if r.levelno == logging.WARNING]
            assert any("Skipped" in r.getMessage() for r in warnings), (
                f"{cls.__name__} skipped {sorted(skipped)} without a WARNING"
            )


def test_skip_surface_detail_is_bounded(tmp_path, caplog):
    """Threat Model M2 — not an AC check; the floor grades it.

    The test plants every sentinel, so each oracle is a string it authored.
    """
    a, b, c = "SENTINEL-yaml-1a2b", "SENTINEL-field-3c4d", "SENTINEL-bytes-5e6f"

    _write(tmp_path, "@Bad Fence.md",
           f'---\ntype: person\nnotes: {a}: leaked\n---\n\nbody\n')
    _write(tmp_path, "@Drifted.md",
           f'---\ntype: person\nname: D\nemails: "{b}"\n---\n\nbody\n')
    # not valid UTF-8, with the sentinel in the decodable prefix
    (tmp_path / "@Bytes.md").write_bytes(
        b"---\ntype: person\nname: " + c.encode() + b"\xff\xfe\n---\n\nbody\n")

    with caplog.at_level(logging.DEBUG, logger="obsidian_schemas"):
        repo = PersonRepository(tmp_path)
        repo.load()

    assert repo.skipped_count == 3, [n.path.name for n in repo.skipped_notes]
    assert {n.reason for n in repo.skipped_notes} == {
        "malformed-frontmatter", "schema-drift", "unreadable"}

    written = {p.name for p in tmp_path.iterdir()}
    for note in repo.skipped_notes:
        assert note.path.name in written, "SkippedNote must name a note we wrote"

    messages = [r.getMessage() for r in caplog.records]
    for sentinel in (a, b, c):
        for note in repo.skipped_notes:
            assert sentinel not in note.detail, (
                f"{sentinel} reached the PUBLIC SkippedNote.detail via "
                f"{note.path.name}: {note.detail}"
            )
        for message in messages:
            assert sentinel not in message, f"{sentinel} reached a log line: {message}"

    # The bucket M2 names by hand: an undecodable note arrives as the class name
    # alone. (On this interpreter str(UnicodeDecodeError) renders the offending
    # byte and its OFFSET rather than a snippet of the note — still note-derived,
    # and still out of bound, but it means sentinel-absence alone cannot catch a
    # regression here. Hence the log-line oracle below.)
    unreadable = [n for n in repo.skipped_notes if n.reason == "unreadable"]
    assert unreadable and unreadable[0].detail == "UnicodeDecodeError"

    # THE WARNING CARRIES THE BOUNDED PROJECTION, NOT THE RAW ONE. Without this,
    # swapping _note_skip's `detail` back to `{error}` goes UNDETECTED: for our
    # own errors str() IS the bounded message, and for the undecodable note the
    # raw rendering happens to contain no sentinel. The oracle is a value this
    # test already holds and has independently asserted bounded — SkippedNote's
    # own detail — never a substring of a library rendering.
    warnings = [r.getMessage() for r in caplog.records
                if r.levelno == logging.WARNING]
    for note in repo.skipped_notes:
        assert any(m.endswith(note.detail) for m in warnings), (
            f"no WARNING carries the bounded detail for {note.path.name!r} "
            f"({note.detail!r}) — the log line is rendering something else, "
            f"which is the M2 channel. Captured: {warnings}"
        )


# ---------------------------------------------------------------------------
# AC-6
# ---------------------------------------------------------------------------

def test_company_set_except_is_narrowed_not_just_logged():
    """AC-6. Zero-arg; the patches are undone by the context manager on the way
    out, including when an assertion raises (tests/support.py).
    """
    with temp_dir() as tmp_path, patcher() as monkeypatch:
        _check_company_set_except_is_narrowed_not_just_logged(
            tmp_path, monkeypatch)


def _check_company_set_except_is_narrowed_not_just_logged(tmp_path, monkeypatch):
    _write(tmp_path, "@P.md",
           "---\ntype: person\nname: P\ncompany: Acme\n---\n\nbody\n")

    # HALF 1: a VaultPathNotConfiguredError raised anywhere in the block must
    # PROPAGATE. A logger.debug -> logger.warning change does not satisfy this
    # criterion; only narrowing the except clause itself does.
    repo = PersonRepository(tmp_path)
    repo.load()
    monkeypatch.setattr(
        CompanyRepository, "get_all",
        lambda self: (_ for _ in ()).throw(
            VaultPathNotConfiguredError("no vault")))
    with pytest.raises(VaultPathNotConfiguredError):
        repo._known_companies()

    # HALF 2: a genuine ImportError still degrades to the person-company set.
    #
    # Against a FRESH instance constructed AFTER the monkeypatch: the company
    # repository is memoized per instance, so an instance that already resolved
    # the import never re-imports and this half would pass vacuously regardless
    # of the except clause. The absence of memoized state is by construction
    # here, never cleared by hand.
    monkeypatch.setitem(sys.modules, "obsidian_schemas.repositories.company", None)
    fresh = PersonRepository(tmp_path)
    fresh.load()
    assert fresh._known_companies() == {"Acme"}
