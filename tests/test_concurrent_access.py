"""WI-004's behavioural battery — the acceptance criteria that need a running
filesystem rather than a parsed one.

Every top-level `test_*` here takes ZERO arguments and signals failure by
RAISING, because the conveyor resolves a `kind: test` criterion by
`getattr(mod, name)()` and a returned False would exit 0 and read as PASS.
Helper functions carry the fixtures.

Every oracle in this module is a value the check itself wrote — the exact mode
it chmod-ed, the exact path it created, the exact bytes it planted. Never a
substring, never a shape, never an environmental absence assumed.
"""

import logging
import os
import threading
from pathlib import Path

from obsidian_schemas import vault_io
from obsidian_schemas.errors import (
    ExternalWriteConflict,
    LoudFailError,
    NoteAlreadyExists,
    StaleEntityWrite,
    WriteFailedError,
)
from tests.support import captured_logs, patcher, temp_dir


def _modes(directory: Path):
    """The permission bits of every in-flight temp file in `directory`."""
    return {p.stat().st_mode & 0o7777
            for p in directory.glob(".*.tmp")}


# --------------------------------------------------------------------------
# Task 3's four checks
# --------------------------------------------------------------------------

def test_vault_io_round_trips_and_refuses_a_stale_stamp():
    """The door's whole happy path plus both of its refusals, in one arc."""
    with temp_dir() as vault:
        vault_io.clear_snapshots()
        note = vault / "note.md"

        with vault_io.note_lock(note):
            vault_io.create_note(note, "first\n")
            assert note.read_text(encoding="utf-8") == "first\n"

            # The zero case is a no-clobber create: a second create refuses and
            # leaves the winner's bytes exactly as they were.
            try:
                vault_io.create_note(note, "second\n")
            except NoteAlreadyExists:
                pass
            else:
                raise AssertionError("a second create_note must raise NoteAlreadyExists")
            assert note.read_text(encoding="utf-8") == "first\n"

            text, stamp = vault_io.read_note(note)
            assert text == "first\n"
            vault_io.write_note(note, "second\n", precondition=stamp)
            assert note.read_text(encoding="utf-8") == "second\n"

            # The stamp is now stale against disk, so re-using it must refuse.
            try:
                vault_io.write_note(note, "third\n", precondition=stamp)
            except ExternalWriteConflict:
                pass
            else:
                raise AssertionError("a stale stamp must raise ExternalWriteConflict")
            assert note.read_text(encoding="utf-8") == "second\n"


def test_every_door_preserves_the_targets_mode():
    """AC-15. Both halves: the committed mode, and the ORDERING that a
    committed-mode oracle is structurally blind to."""
    from obsidian_schemas.writer import write_markdown_file

    with temp_dir() as vault:
        vault_io.clear_snapshots()

        # --- the committed mode, through write_note, at two different modes ---
        for bits in (0o600, 0o644):
            note = vault / f"mode{bits:o}.md"
            note.write_text("x\n", encoding="utf-8")
            os.chmod(note, bits)
            with vault_io.note_lock(note):
                _text, stamp = vault_io.read_note(note)
                vault_io.write_note(note, "y\n", precondition=stamp)
            assert note.stat().st_mode & 0o7777 == bits, (
                f"write_note must preserve {bits:o}"
            )

        # --- a fresh create takes the mode Path.write_text gives a fresh
        # sibling IN THIS RUN. The oracle is the umask-derived mode the check
        # measured, never a hardcoded 0o644: the umask is the environment's and
        # the promise is equality with today, not a constant.
        reference = vault / "reference.md"
        reference.write_text("r\n", encoding="utf-8")
        expected = reference.stat().st_mode & 0o7777
        created = vault / "created.md"
        with vault_io.note_lock(created):
            vault_io.create_note(created, "c\n")
        assert created.stat().st_mode & 0o7777 == expected

        # --- door 2 (write_markdown_file) and door 3 (move_note) ------------
        door2 = vault / "door2.md"
        door2.write_text("---\ntype: person\nname: A\n---\n\nbody\n",
                         encoding="utf-8")
        os.chmod(door2, 0o600)
        write_markdown_file(door2, frontmatter={"type": "person", "name": "A"},
                            body="body\nsecond line\n", overwrite=True,
                            allow_unverified_overwrite=True)
        assert door2.stat().st_mode & 0o7777 == 0o600

        src = vault / "src.md"
        src.write_text("m\n", encoding="utf-8")
        os.chmod(src, 0o600)
        dest = vault / "dest.md"
        vault_io.move_note(src, dest)
        assert dest.stat().st_mode & 0o7777 == 0o600

        # --- THE ORDERING HALF ---------------------------------------------
        # Every assertion above inspects the COMMITTED note, whose mode is
        # identical under mode-before-write and mode-after-write — so M1's
        # confidentiality window would stay green under the very ordering it
        # forbids. The distinguishing observation is the temp file's mode at the
        # moment the payload is on disk and NOT YET COMMITTED, and os.fsync is
        # exactly that moment.
        real = vault / "real.md"
        real.write_text("body\n", encoding="utf-8")
        os.chmod(real, 0o600)
        seen = []
        original_fsync = os.fsync

        def recording_fsync(fd):
            if not seen:
                seen.append(_modes(real.parent))
            return original_fsync(fd)

        with patcher() as p:
            p.setattr(os, "fsync", recording_fsync)
            with vault_io.note_lock(real):
                _text, stamp = vault_io.read_note(real)
                vault_io.write_note(real, "body two\n", precondition=stamp)
        assert seen, "os.fsync was never reached — the probe observed nothing"
        assert seen[0] == {0o600}, (
            "the target's mode must be on the temp descriptor BEFORE the payload "
            f"— observed {seen[0]!r} at fsync time, expected {{0o600}}"
        )

        # and once through door 2, so the claim covers its own commit.
        real2 = vault / "real2.md"
        real2.write_text("---\ntype: person\nname: B\n---\n\nbody\n",
                         encoding="utf-8")
        os.chmod(real2, 0o600)
        seen2 = []

        def recording_fsync2(fd):
            if not seen2:
                seen2.append(_modes(real2.parent))
            return original_fsync(fd)

        with patcher() as p:
            p.setattr(os, "fsync", recording_fsync2)
            write_markdown_file(real2,
                                frontmatter={"type": "person", "name": "B"},
                                body="body\nsecond line\n", overwrite=True,
                                allow_unverified_overwrite=True)
        assert seen2 and seen2[0] == {0o600}, (
            f"door 2 must carry the mode before the payload — observed {seen2!r}"
        )
        # move_note is deliberately given NO such probe: door 3 links an
        # existing inode and writes no temp payload, so there is no window.


def test_configuration_refuses_invalid_values_and_bounds_acquisition():
    """AC-16. The WHOLE configuration surface, per D6's total rule — not the one
    variable the threat model happened to name."""
    with temp_dir() as vault:
        vault_io.clear_snapshots()
        note = vault / "cfg.md"
        note.write_text("x\n", encoding="utf-8")

        def refuses(var, value):
            # A full write, so each var is exercised at its documented raise
            # point: the two lock settings refuse at first ACQUISITION, and the
            # guard setting at the first WRITE (D6).
            with patcher() as p:
                p.setitem(os.environ, var, value)
                try:
                    with vault_io.note_lock(note):
                        _text, stamp = vault_io.read_note(note)
                        vault_io.write_note(note, "y\n", precondition=stamp)
                except WriteFailedError as exc:
                    message = str(exc)
                    assert var in message, (
                        f"{var}={value!r} must name the variable; got {message!r}"
                    )
                    assert value not in message or value == "", (
                        f"{var}'s VALUE must not reach the message; got {message!r}"
                    )
                    return
            raise AssertionError(f"{var}={value!r} must raise WriteFailedError")

        a_file = vault / "not-a-dir"
        a_file.write_text("", encoding="utf-8")
        for value in ("locks", "", str(a_file)):
            refuses("OBSIDIAN_SCHEMAS_LOCK_DIR", value)
        for value in ("0", "-1", "abc"):
            refuses("OBSIDIAN_SCHEMAS_LOCK_TIMEOUT", value)
        for value in ("ENFORCE", "yes"):
            refuses("OBSIDIAN_SCHEMAS_WRITE_GUARD", value)

        # Every var UNSET yields its documented default with no raise.
        with patcher() as p:
            for var in ("OBSIDIAN_SCHEMAS_LOCK_DIR",
                        "OBSIDIAN_SCHEMAS_LOCK_TIMEOUT",
                        "OBSIDIAN_SCHEMAS_WRITE_GUARD"):
                p.setitem(os.environ, var, "")
                os.environ.pop(var, None)
            assert vault_io.guard_mode() == "enforce"
            with vault_io.note_lock(note):
                pass

        # A lock held past the configured timeout REFUSES rather than hanging.
        released = threading.Event()
        acquired = threading.Event()

        def holder():
            with vault_io.note_lock(note):
                acquired.set()
                released.wait(10)

        thread = threading.Thread(target=holder)
        thread.start()
        try:
            assert acquired.wait(10), "the holder thread never acquired"
            with patcher() as p:
                p.setitem(os.environ, "OBSIDIAN_SCHEMAS_LOCK_TIMEOUT", "0.05")
                try:
                    with vault_io.note_lock(note):
                        raise AssertionError(
                            "a lock held past the timeout must refuse, not acquire"
                        )
                except WriteFailedError:
                    pass
        finally:
            released.set()
            thread.join(10)


def test_every_door_uses_one_resolved_path():
    """AC-17. One resolved path per door — and the TWO-PARENTS-ONE-NOTE case,
    which neither the single-process half nor AC-8's symlink-free exclusion can
    see."""
    with temp_dir() as vault:
        vault_io.clear_snapshots()
        real = vault / "real.md"
        real.write_text("original\n", encoding="utf-8")
        link = vault / "link.md"
        link.symlink_to(real)

        with vault_io.note_lock(link):
            _text, stamp = vault_io.read_note(link)
            vault_io.write_note(link, "through the link\n", precondition=stamp)
        assert real.read_text(encoding="utf-8") == "through the link\n"
        assert link.is_symlink(), "the symlink must survive as a symlink"

        # move_note refuses a symlinked source and leaves both paths intact.
        dest = vault / "moved.md"
        try:
            vault_io.move_note(link, dest)
        except WriteFailedError:
            pass
        else:
            raise AssertionError("move_note must refuse a symlinked source")
        assert link.is_symlink() and real.exists() and not dest.exists()

        # --- TWO PARENTS, ONE NOTE -----------------------------------------
        # Its own subtree, so the sentinel count is over THIS case's writes and
        # not over the symlink case above, which locked in the vault root.
        scratch = vault / "two-parents"
        (scratch / "real").mkdir(parents=True)
        (scratch / "alias").mkdir(parents=True)
        note = scratch / "real" / "note.md"
        note.write_text("one note\n", encoding="utf-8")
        alias = scratch / "alias" / "note.md"
        alias.symlink_to(Path("..") / "real" / "note.md")

        # (a) sequentially lock each path; exactly ONE sentinel must exist, in
        # the RESOLVED note's own directory.
        with vault_io.note_lock(note):
            pass
        with vault_io.note_lock(alias):
            pass
        sentinels = sorted(scratch.rglob(f"{vault_io.SENTINEL_DIR_NAME}/*.lock"))
        assert len(sentinels) == 1, (
            "two paths naming one real note must key ONE sentinel; found "
            + ", ".join(str(s) for s in sentinels)
        )
        assert sentinels[0].parent == scratch / "real" / vault_io.SENTINEL_DIR_NAME

        # (b) and Layer 2 genuinely excludes across the two spellings.
        acquired = threading.Event()
        released = threading.Event()

        def holder():
            with vault_io.note_lock(alias):
                acquired.set()
                released.wait(10)

        thread = threading.Thread(target=holder)
        thread.start()
        try:
            assert acquired.wait(10)
            with patcher() as p:
                p.setitem(os.environ, "OBSIDIAN_SCHEMAS_LOCK_TIMEOUT", "0.05")
                try:
                    with vault_io.note_lock(note):
                        raise AssertionError(
                            "the alias and the real path must exclude each other"
                        )
                except WriteFailedError:
                    pass
        finally:
            released.set()
            thread.join(10)

        # (c) the configured-home branch, driven rather than assumed.
        home = vault / "configured-locks"
        home.mkdir()
        with patcher() as p:
            p.setitem(os.environ, "OBSIDIAN_SCHEMAS_LOCK_DIR", str(home))
            with vault_io.note_lock(note):
                pass
            assert sorted(home.glob("*.lock")), (
                "OBSIDIAN_SCHEMAS_LOCK_DIR must home the sentinel"
            )


# --------------------------------------------------------------------------
# Task 7's two checks
# --------------------------------------------------------------------------

def test_a_loader_overriding_repository_can_update_a_note_it_loaded():
    """AC-11. The class the walls are structurally blind to.

    A wall over mutation CAPABILITY cannot see a missing OBSERVATION, and no
    test in the suite saves a book or a meeting — so a stamp recorded in the
    base loader alone would leave BookRepository.save and MeetingRepository.save
    of a loaded note raising NoteAlreadyExists with every wall still green.
    """
    from obsidian_schemas.repositories.book import BookRepository
    from obsidian_schemas.repositories.meeting import MeetingRepository

    with temp_dir() as vault:
        vault_io.clear_snapshots()
        book_note = vault / "Dune - Frank Herbert.md"
        book_note.write_text(
            "---\ntype: book\ntitle: Dune\nauthor: Frank Herbert\n"
            "status: reading\n---\n\n## Notes\n\n- a note\n",
            encoding="utf-8")
        # The filename each repository DERIVES for this entity, so save() writes
        # back to the note it loaded rather than minting a sibling. The fields
        # mutated below are chosen not to move that derivation.
        meeting_note = vault / "Meeting 20260809 - Standup.md"
        meeting_note.write_text(
            "---\ntype: meeting\nname: Standup\ndate: 2026-08-09\n"
            "topics:\n  - Standup\nmeeting_id: m-1\n"
            "---\n\n## Notes\n\n- a note\n",
            encoding="utf-8")

        for repo_class, path, field, value in (
            (BookRepository, book_note, "status", "finished"),
            (MeetingRepository, meeting_note, "meeting_id", "m-2"),
        ):
            repo = repo_class(vault)
            repo.load()
            entities = repo.get_all()
            assert entities, f"{repo_class.__name__} loaded nothing"
            entity = next(e for e in entities
                          if e.model_dump().get("type") in ("book", "meeting"))
            setattr(entity, field, value)

            # A 2u UPDATE, never NoteAlreadyExists — that outcome is the defect.
            repo.save(entity, body="## Notes\n\n- a note\n", overwrite=True)
            assert value in path.read_text(encoding="utf-8"), (
                f"{repo_class.__name__}.save must land {value!r} on disk"
            )

            # ...and once the note is edited BEHIND the repository, the same
            # save refuses rather than destroying that edit. The replacement
            # body deliberately KEEPS the planted line: the WI-126 shrink guard
            # runs before the stamp precondition (D8 step 6 before step 7), so a
            # shrinking body would surface BodyTruncationError and never
            # exercise the staleness this check is about.
            path.write_text(
                path.read_text(encoding="utf-8") + "- edited behind us\n",
                encoding="utf-8")
            try:
                repo.save(entity,
                          body="## Notes\n\n- a note\n- edited behind us\n- ours\n",
                          overwrite=True)
            except StaleEntityWrite:
                pass
            else:
                raise AssertionError(
                    f"{repo_class.__name__}.save must raise StaleEntityWrite "
                    "once the note has moved on disk"
                )


def test_repository_cache_is_consistent_under_concurrent_refresh():
    """AC-18 — the item's ORIGINAL March scope.

    `get_by_role` is in the loop deliberately: it ITERATES self._cache.values(),
    which is the read shape that raises RuntimeError against a live mapping
    mutated in place, while get_all()'s list(...) is the shape that silently
    returns a HALF-BUILT vault. Under a bare lock taken only by the writers both
    assertions are RED; under the replace-the-mapping rule both are GREEN.
    """
    from obsidian_schemas import PersonRepository

    with temp_dir() as vault:
        vault_io.clear_snapshots()
        # TWELVE is the number this check itself wrote — never a count read back
        # from the repository under test.
        for i in range(12):
            (vault / f"@Person{i:02d}.md").write_text(
                f"---\ntype: person\nname: Person{i:02d}\nrole: vip\n---\n\nbody\n",
                encoding="utf-8")

        repo = PersonRepository(vault)
        repo.load()

        observed = []
        errors = []
        ITERATIONS = 200

        def writer():
            try:
                for _ in range(ITERATIONS):
                    repo.refresh()
            except BaseException as exc:      # noqa: BLE001 — re-raised below
                errors.append(exc)

        def reader():
            try:
                for _ in range(ITERATIONS):
                    observed.append(len(repo.get_all()))
                    repo.get_by_role("vip")
            except BaseException as exc:      # noqa: BLE001 — re-raised below
                errors.append(exc)

        threads = [threading.Thread(target=writer), threading.Thread(target=reader)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(120)

        if errors:
            raise errors[0]
        assert set(observed) == {12}, (
            "every get_all() must see the complete pre- or post-refresh mapping, "
            f"never a half-built vault; observed {sorted(set(observed))}"
        )


# --------------------------------------------------------------------------
# Task 8's check
# --------------------------------------------------------------------------

def test_create_is_no_clobber_and_create_stub_reuses_the_winner():
    """AC-5. All three halves of the zero case, in one check."""
    from obsidian_schemas import PersonRepository
    from obsidian_schemas.repositories.book import BookRepository
    from obsidian_schemas.repositories.company import CompanyRepository

    # (a) the no-clobber create itself -------------------------------------
    with temp_dir() as vault:
        vault_io.clear_snapshots()
        note = vault / "contested.md"
        winner_bytes = "the winner got here first\n"
        note.write_text(winner_bytes, encoding="utf-8")
        with vault_io.note_lock(note):
            try:
                vault_io.create_note(note, "the loser's bytes\n")
            except NoteAlreadyExists:
                pass
            else:
                raise AssertionError("create_note must refuse an existing target")
        assert note.read_text(encoding="utf-8") == winner_bytes, (
            "the winner's bytes must be byte-identical after a lost race"
        )

    # (b) PersonRepository.create_stub reuses the winner --------------------
    with temp_dir() as vault:
        vault_io.clear_snapshots()
        repo = PersonRepository(vault)
        repo.load()                       # an EMPTY vault: no stamp for anything

        # A second writer mints the note directly on disk, behind the loaded
        # repository — so create_stub's own cache guard cannot see it.
        winner_note = vault / "@Jane Doe.md"
        winner_note.write_text(
            "---\ntype: person\nname: Jane Doe\n"
            "emails:\n  - jane@winner.example\n"
            "created_by: the-winner\ntags:\n  - person\n"
            "---\n\n## Timeline\n\n- the winner's history\n",
            encoding="utf-8")

        result = repo.create_stub("Jane Doe", phone="+441234567890",
                                  created_by="the-loser")

        assert result.created_by == "the-winner", (
            f"the WINNER's provenance must survive; got {result.created_by!r}"
        )
        assert "jane@winner.example" in result.emails, (
            f"the winner's email must survive; got {result.emails!r}"
        )
        on_disk = winner_note.read_text(encoding="utf-8")
        assert "the winner's history" in on_disk, "the winner's body must survive"
        assert "441234567890" in on_disk.replace("+", ""), (
            "the supplied phone must be written back into the winner's note; "
            f"got:\n{on_disk}"
        )

    # (c) the book and company stubs surface NoteAlreadyExists --------------
    for repo_class, filename, seeded, kwargs in (
        (BookRepository, "Dune - Frank Herbert.md",
         "---\ntype: book\ntitle: Dune\nauthor: Frank Herbert\n"
         "---\n\n## Notes\n\n- the winner's notes\n",
         {"title": "Dune", "author": "Frank Herbert"}),
        (CompanyRepository, "@Acme Corp.md",
         "---\ntype: company\nname: Acme Corp\n"
         "---\n\n## Notes\n\n- the winner's notes\n",
         {"name": "Acme Corp"}),
    ):
        with temp_dir() as vault:
            vault_io.clear_snapshots()
            repo = repo_class(vault)
            repo.load()
            note = vault / filename
            note.write_text(seeded, encoding="utf-8")
            before = note.read_text(encoding="utf-8")
            try:
                repo.create_stub(**kwargs)
            except NoteAlreadyExists:
                pass
            else:
                raise AssertionError(
                    f"{repo_class.__name__}.create_stub has no reuse branch, so a "
                    "lost race must surface NoteAlreadyExists to the caller"
                )
            assert note.read_text(encoding="utf-8") == before, (
                "the winner's note must be byte-identical"
            )


# --------------------------------------------------------------------------
# Task 9's checks
# --------------------------------------------------------------------------

def test_move_note_refuses_an_existing_destination():
    """AC-6. Door 3 refuses by SYSCALL rather than by check, and the caller's
    skip-on-collision behaviour is preserved without the TOCTOU window."""
    with temp_dir() as vault:
        vault_io.clear_snapshots()
        src = vault / "src.md"
        dest = vault / "dest.md"
        src_bytes = "the source\n"
        dest_bytes = "the destination was already here\n"
        src.write_text(src_bytes, encoding="utf-8")
        dest.write_text(dest_bytes, encoding="utf-8")

        try:
            vault_io.move_note(src, dest)
        except NoteAlreadyExists:
            pass
        else:
            raise AssertionError("move_note must refuse an existing destination")
        assert src.read_text(encoding="utf-8") == src_bytes
        assert dest.read_text(encoding="utf-8") == dest_bytes

        # ...and a free destination still moves.
        free = vault / "free.md"
        vault_io.move_note(src, free)
        assert free.read_text(encoding="utf-8") == src_bytes
        assert not src.exists()


def test_quarantine_skips_on_collision_without_clobbering():
    """The consumer half of AC-6: quarantine_garbage skips that note rather
    than clobbering the destination."""
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
    from lint_vault import quarantine_garbage, LintIssue, Severity

    with temp_dir() as vault:
        vault_io.clear_snapshots()
        src = vault / "@Garbage.md"
        src.write_text("---\ntype: person\nname: Garbage\n---\n\nbody\n",
                       encoding="utf-8")
        quarantine_dir = vault / "_quarantine"
        dest_dir = quarantine_dir / "persons"
        dest_dir.mkdir(parents=True)
        planted = "the destination was already here\n"
        (dest_dir / "@Garbage.md").write_text(planted, encoding="utf-8")

        issue = LintIssue(
            file_path=src,
            check="garbage_candidate_person",
            severity=Severity.WARNING,
            message="garbage",
            category="garbage",
        )
        moved = quarantine_garbage([issue], vault)

        assert moved == 0, "a collision must be skipped, not counted as a move"
        assert (dest_dir / "@Garbage.md").read_text(encoding="utf-8") == planted, (
            "the destination's bytes must be byte-identical to what was planted"
        )
        assert src.exists(), "the source must survive a skipped quarantine"


# --------------------------------------------------------------------------
# Task 10's check
# --------------------------------------------------------------------------

def test_refusals_are_loud_bounded_and_mode_governed():
    """AC-9. BOTH halves — loud-and-bounded, and mode-governed."""
    SENTINEL = "SENTINEL-body-4f2a-do-not-leak"

    # (a) every refusal this item mints is loud, typed and bounded -----------
    with temp_dir() as vault:
        vault_io.clear_snapshots()
        body = f"---\ntype: person\nname: X\n---\n\n{SENTINEL}\n"

        caught = []

        # StaleEntityWrite — a door-2 payload older than the target.
        stale = vault / "stale.md"
        stale.write_text(body, encoding="utf-8")
        with vault_io.note_lock(stale):
            _t, stamp = vault_io.read_note(stale)
            stale.write_text(body + "moved on\n", encoding="utf-8")
            try:
                vault_io.write_note(stale, "new\n", precondition=stamp,
                                    origin="entity")
            except StaleEntityWrite as exc:
                caught.append((exc, stale))

        # ExternalWriteConflict — the same mismatch on a door-1 write.
        conflict = vault / "conflict.md"
        conflict.write_text(body, encoding="utf-8")
        with vault_io.note_lock(conflict):
            _t, stamp = vault_io.read_note(conflict)
            conflict.write_text(body + "moved on\n", encoding="utf-8")
            try:
                vault_io.write_note(conflict, "new\n", precondition=stamp)
            except ExternalWriteConflict as exc:
                caught.append((exc, conflict))

        # NoteAlreadyExists — the zero case against an existing target.
        exists = vault / "exists.md"
        exists.write_text(body, encoding="utf-8")
        with vault_io.note_lock(exists):
            try:
                vault_io.create_note(exists, "new\n")
            except NoteAlreadyExists as exc:
                caught.append((exc, exists))

        assert len(caught) == 3, (
            f"all three refusals must fire; got {len(caught)}"
        )
        for exc, path in caught:
            assert isinstance(exc, LoudFailError), (
                f"{type(exc).__name__} must be a LoudFailError"
            )
            # Distinguishable from WriteFailedError, which is what lets a caller
            # retry a conflict without retrying a genuine IO failure.
            assert not isinstance(exc, WriteFailedError), (
                f"{type(exc).__name__} must NOT be a WriteFailedError — an "
                "`except WriteFailedError` must not swallow a write conflict"
            )
            assert exc.path == path.resolve(), (
                f"{type(exc).__name__} must carry its path; got {exc.path!r}"
            )
            # The oracle is the string the check PLANTED, never an assumed
            # absence of some shape.
            assert SENTINEL not in str(exc), (
                f"{type(exc).__name__} leaked note content into its message: "
                f"{str(exc)!r}"
            )

    # (b) mode governance, both directions, from one fixture -----------------
    with temp_dir() as vault:
        vault_io.clear_snapshots()
        note = vault / "guarded.md"
        note.write_text("original\n", encoding="utf-8")

        # An unrecognised value RAISES rather than being treated as enforce.
        with patcher() as p:
            p.setitem(os.environ, "OBSIDIAN_SCHEMAS_WRITE_GUARD", "ENFORCE")
            with vault_io.note_lock(note):
                _t, stamp = vault_io.read_note(note)
                try:
                    vault_io.write_note(note, "x\n", precondition=stamp)
                except WriteFailedError:
                    pass
                else:
                    raise AssertionError(
                        "an unrecognised guard value must raise, never be "
                        "silently treated as enforce"
                    )

        # enforce REFUSES where observe PROCEEDS, on the identical setup.
        with vault_io.note_lock(note):
            _t, stale_stamp = vault_io.read_note(note)
        note.write_text("moved on\n", encoding="utf-8")

        with vault_io.note_lock(note):
            try:
                vault_io.write_note(note, "enforced\n", precondition=stale_stamp)
            except ExternalWriteConflict:
                pass
            else:
                raise AssertionError("enforce mode must refuse a stale stamp")
        assert note.read_text(encoding="utf-8") == "moved on\n"

        # ...and observe proceeds, emitting EXACTLY ONE INFO line naming the
        # mode across TWO writes — one per process, not one per write.
        vault_io._ANNOUNCED["observe"] = False
        with patcher() as p:
            p.setitem(os.environ, "OBSIDIAN_SCHEMAS_WRITE_GUARD", "observe")
            with captured_logs(level=logging.INFO) as records:
                with vault_io.note_lock(note):
                    vault_io.write_note(note, "observed one\n",
                                        precondition=stale_stamp)
                    vault_io.write_note(note, "observed two\n",
                                        precondition=stale_stamp)
            assert note.read_text(encoding="utf-8") == "observed two\n", (
                "observe mode must PROCEED with today's semantics"
            )
            info = [r for r in records
                    if r.levelno == logging.INFO and "OBSERVE" in r.getMessage()]
            assert len(info) == 1, (
                "observe mode must announce itself exactly ONCE per process, "
                f"not once per write; got {len(info)} INFO lines"
            )


# --------------------------------------------------------------------------
# Task 13's checks
# --------------------------------------------------------------------------

def test_every_door_commits_atomically():
    """AC-1. A commit is a COMPLETE note or it is nothing.

    Two halves, because "atomic" has two failure modes and the rename only
    closes one of them:

    1. **No reader observes partial bytes.** The observation is taken at
       `os.fsync` — the moment the payload is fully on disk and NOT YET
       committed — which is exactly the instant a truncate-in-place writer would
       be exposing a half-written note. Under temp-file + os.replace the target
       still holds the COMPLETE old bytes there.
    2. **No SHORT write is committed.** `os.write` is `write(2)` and may return
       short; a volume filling mid-write writes what fits and returns that
       count rather than raising `ENOSPC`. An unchecked return would satisfy the
       rename and still falsify this criterion — a truncated note, fsynced,
       replaced over the target and stamped fresh, with nothing raised. The
       oracle is the target's OWN OLD BYTES, which the check itself wrote.
    """
    with temp_dir() as vault:
        vault_io.clear_snapshots()
        note = vault / "atomic.md"
        old = "OLD-" + ("x" * 4000) + "\n"
        new = "NEW-" + ("y" * 8000) + "\n"
        note.write_text(old, encoding="utf-8")

        observed = []
        original_fsync = os.fsync

        def recording_fsync(fd):
            observed.append(note.read_text(encoding="utf-8"))
            return original_fsync(fd)

        with patcher() as p:
            p.setattr(os, "fsync", recording_fsync)
            with vault_io.note_lock(note):
                _t, stamp = vault_io.read_note(note)
                vault_io.write_note(note, new, precondition=stamp)

        assert observed, "os.fsync was never reached — the probe observed nothing"
        for seen in observed:
            assert seen in (old, new), (
                "a reader observed a partially-written note: "
                f"{len(seen)} bytes, neither the old {len(old)} nor the new {len(new)}"
            )
        assert note.read_text(encoding="utf-8") == new
        assert not list(vault.glob(".*.tmp")), "no temp file may survive a commit"

        # --- Half 2: a short write REFUSES rather than committing a fragment.
        real_write = os.write
        before = note.read_text(encoding="utf-8")
        fragment = "FRAGMENT-" + ("z" * 9000) + "\n"
        calls = []

        def short_then_stuck(fd, data):
            # The fill-up shape: the first call takes half of what it was
            # offered, the next makes NO progress at all. Both arms have to be
            # handled — the first proves the loop resumes from the offset, the
            # second proves it refuses instead of spinning.
            calls.append(len(data))
            if len(calls) == 1:
                return real_write(fd, bytes(data)[:len(data) // 2])
            return 0

        with vault_io.note_lock(note):
            _t, stamp = vault_io.read_note(note)
            with patcher() as p:
                p.setattr(os, "write", short_then_stuck)
                try:
                    vault_io.write_note(note, fragment, precondition=stamp)
                    refused = None
                except WriteFailedError as exc:
                    refused = exc

        assert refused is not None, (
            "a write that never delivered its whole payload must raise "
            "WriteFailedError, not commit what landed"
        )
        assert len(calls) >= 2, (
            f"the short-write probe was never exercised: os.write calls={calls}"
        )
        assert note.read_text(encoding="utf-8") == before, (
            "a refused short write must leave the target's OLD bytes intact, "
            f"got {len(note.read_text(encoding='utf-8'))} bytes"
        )
        assert not list(vault.glob(".*.tmp")), (
            "a refused short write must not leave its temp file behind"
        )

        # The near-miss the refusal must NOT swallow: a writer that returns
        # short but keeps MAKING PROGRESS commits the complete payload. Without
        # this half, "raise whenever os.write returns < len(payload)" would pass
        # the assertion above while breaking every real write on a pipe-like fd.
        chunked = "CHUNKED-" + ("w" * 5000) + "\n"

        def chunked_write(fd, data):
            return real_write(fd, bytes(data)[:64])

        with vault_io.note_lock(note):
            _t, stamp = vault_io.read_note(note)
            with patcher() as p:
                p.setattr(os, "write", chunked_write)
                vault_io.write_note(note, chunked, precondition=stamp)

        assert note.read_text(encoding="utf-8") == chunked, (
            "a short-but-progressing write must still commit the COMPLETE note"
        )
        assert not list(vault.glob(".*.tmp")), "no temp file may survive a commit"


def test_door_one_refuses_a_raced_content_write():
    """AC-2. A door-1 write whose target moved since the in-lock read refuses,
    and the interloper's bytes survive byte-identically."""
    with temp_dir() as vault:
        vault_io.clear_snapshots()
        note = vault / "raced.md"
        note.write_text("original\n", encoding="utf-8")

        interloper = "the interloper got here\n"
        with vault_io.note_lock(note):
            _t, stamp = vault_io.read_note(note)
            note.write_text(interloper, encoding="utf-8")
            try:
                vault_io.write_note(note, "ours\n", precondition=stamp)
            except ExternalWriteConflict:
                pass
            else:
                raise AssertionError(
                    "a door-1 write against a changed target must raise "
                    "ExternalWriteConflict"
                )
        assert note.read_text(encoding="utf-8") == interloper

        # A DELETED target is a mismatch too, not a create: silently
        # resurrecting a note from a stale snapshot is the same loss class in
        # the other direction.
        gone = vault / "gone.md"
        gone.write_text("here\n", encoding="utf-8")
        with vault_io.note_lock(gone):
            _t, stamp = vault_io.read_note(gone)
            gone.unlink()
            try:
                vault_io.write_note(gone, "resurrected\n", precondition=stamp)
            except ExternalWriteConflict:
                pass
            else:
                raise AssertionError(
                    "a stamp whose target no longer exists is a MISMATCH, "
                    "never a create"
                )


def test_save_refuses_a_stale_snapshot_and_succeeds_after_refresh():
    """AC-3. The headline door-2u case, and its documented recovery."""
    from obsidian_schemas import PersonRepository

    with temp_dir() as vault:
        vault_io.clear_snapshots()
        note = vault / "@Stale Target.md"
        note.write_text(
            "---\ntype: person\nname: Stale Target\ntags:\n  - person\n"
            "---\n\n## Notes\n\n- original line\n", encoding="utf-8")

        repo = PersonRepository(vault)
        repo.load()
        person = repo.get("Stale Target")
        assert person is not None

        # A second writer edits the note behind the loaded repository.
        note.write_text(
            "---\ntype: person\nname: Stale Target\nrole: vip\ntags:\n  - person\n"
            "---\n\n## Notes\n\n- original line\n- the other writer's line\n",
            encoding="utf-8")

        body = "## Notes\n\n- original line\n- the other writer's line\n- ours\n"
        try:
            repo.save(person, body=body, overwrite=True)
        except StaleEntityWrite:
            pass
        else:
            raise AssertionError(
                "a save from a snapshot older than the target must raise "
                "StaleEntityWrite instead of overwriting"
            )
        assert "the other writer's line" in note.read_text(encoding="utf-8"), (
            "the other writer's edit must survive the refusal"
        )

        # refresh() + re-apply succeeds — the documented recovery.
        repo.refresh()
        refreshed = repo.get("Stale Target")
        repo.save(refreshed, body=body, overwrite=True)
        landed = note.read_text(encoding="utf-8")
        assert "- ours" in landed and "the other writer's line" in landed


def test_a_door_one_write_does_not_satisfy_a_door_two_payload():
    """AC-4 — the round-3 architect's note-#1 sequence, explicitly.

    A single path-keyed registry serving two purposes would re-open a silent
    lost update: load P (S0) -> door-1 write (disk S1, and under a
    'record on any successful write' rule the registry would ALSO advance to
    S1) -> repo.save(cached) compares S1 to S1, passes, and rebuilds the
    frontmatter from the pre-S1 snapshot. Door 1 therefore does not touch the
    registry at all, and this check is that rule's falsifier.
    """
    from obsidian_schemas import PersonRepository
    from obsidian_schemas.writer import update_frontmatter_field

    with temp_dir() as vault:
        vault_io.clear_snapshots()
        note = vault / "@Note One.md"
        note.write_text(
            "---\ntype: person\nname: Note One\ntags:\n  - person\n"
            "---\n\n## Notes\n\n- keep me\n", encoding="utf-8")

        repo = PersonRepository(vault)
        repo.load()
        cached = repo.get("Note One")
        assert cached is not None

        # The EXPORTED door-1 writer, against the same path.
        update_frontmatter_field(note, "role", "vip")
        assert "role: vip" in note.read_text(encoding="utf-8")

        try:
            repo.save(cached, body="## Notes\n\n- keep me\n", overwrite=True)
        except StaleEntityWrite:
            pass
        else:
            raise AssertionError(
                "a door-1 write must NOT satisfy a door-2 payload's "
                "precondition — silently destroying the frontmatter change is "
                "exactly what the registry rule exists to prevent"
            )
        assert "role: vip" in note.read_text(encoding="utf-8"), (
            "the door-1 frontmatter change must survive"
        )


def test_locking_excludes_and_is_reentrant():
    """AC-8. The per-note lock — NOT the repository cache lock, which is
    AC-18's."""
    with temp_dir() as vault:
        vault_io.clear_snapshots()
        note = vault / "locked.md"
        note.write_text("x\n", encoding="utf-8")

        # Reentrant within ONE thread, to arbitrary depth.
        with vault_io.note_lock(note):
            with vault_io.note_lock(note):
                with vault_io.note_lock(note):
                    assert vault_io.is_locked(note)
            assert vault_io.is_locked(note), "the outer hold must survive"
        assert not vault_io.is_locked(note), "the lock must be fully released"

        # Exclusive ACROSS threads.
        acquired = threading.Event()
        released = threading.Event()
        outcome = []

        def holder():
            with vault_io.note_lock(note):
                acquired.set()
                released.wait(10)

        thread = threading.Thread(target=holder)
        thread.start()
        try:
            assert acquired.wait(10)
            with patcher() as p:
                p.setitem(os.environ, "OBSIDIAN_SCHEMAS_LOCK_TIMEOUT", "0.05")
                try:
                    with vault_io.note_lock(note):
                        outcome.append("acquired")
                except WriteFailedError:
                    outcome.append("refused")
            assert outcome == ["refused"], (
                f"a second thread must not acquire a held lock; got {outcome}"
            )
        finally:
            released.set()
            thread.join(10)

        # A write attempted WITHOUT the lock raises rather than racing.
        _t, stamp = None, None
        with vault_io.note_lock(note):
            _t, stamp = vault_io.read_note(note)
        for call in (
            lambda: vault_io.write_note(note, "y\n", precondition=stamp),
            lambda: vault_io.create_note(vault / "unlocked.md", "y\n"),
        ):
            try:
                call()
            except WriteFailedError:
                continue
            raise AssertionError(
                "a door must refuse when the lock for its path is not held — "
                "step-skipping must be loud, never racy"
            )


def test_wi020_derivations_survive_the_routing():
    """AC-10. BOTH halves: the four derivations against their pinned sets, AND
    WI-020's own checks still PASSING over the re-routed tree."""
    import tests.test_loud_fail_write as wi020_write
    from tests.derivations import (
        PACKAGE_ROOT,
        base_repository_subclasses,
        functions_parsing_then_writing,
        functions_reserializing_parsed_frontmatter,
        load_file_implementations,
        non_completed_write_sites,
        python_files_under,
    )

    files = python_files_under(PACKAGE_ROOT)

    writers = functions_reserializing_parsed_frontmatter(files)
    assert len(writers) == 4, (
        f"the four reserializing writers must survive routing; got {sorted(writers)}"
    )
    guard = functions_parsing_then_writing(files) - writers
    assert {f.qualname for f in guard} == {"write_markdown_file"}, (
        "the discrimination proof must still reach write_markdown_file and "
        f"still reject it by data flow; got {sorted(guard)}"
    )
    assert len(non_completed_write_sites(files)) == 8, (
        "every falsy return in a write path must still be classified"
    )
    assert len(base_repository_subclasses(files)) == 4
    assert len(load_file_implementations(base_repository_subclasses(files))) == 3

    # The BEHAVIOURAL half — a predicate walk cannot see it. Both are zero-arg
    # top-level defs by construction, so they are invocable directly;
    # test_error_chains_are_bounded takes fixtures and is covered by the floor.
    wi020_write.test_body_guard_refuses_when_unverifiable()
    wi020_write.test_write_failure_raises_and_noops_keep_their_return()


def test_unobserved_overwrite_refuses_and_the_escape_still_guards_the_body():
    """AC-14. The DECLARED consumer-facing break, and the exact shape of its
    escape — which does NOT surrender the WI-126 guard."""
    from obsidian_schemas import parse_markdown_file
    from obsidian_schemas.writer import BodyTruncationError, write_markdown_file

    with temp_dir() as scratch:
        vault_io.clear_snapshots()
        # Written with Path.write_text into a directory NO repository loads, so
        # nothing in this process ever derived an entity from these bytes.
        note = scratch / "unobserved.md"
        note.write_text(
            "---\ntype: person\nname: Unobserved\ncustom_field: keep-me-1a2b\n"
            "---\n\n## Notes\n\n- a body line\n", encoding="utf-8")

        doc = parse_markdown_file(note)
        try:
            write_markdown_file(note, entity=doc.entity, body=doc.body,
                                extra_fields=doc.extra_fields, overwrite=True)
        except NoteAlreadyExists:
            pass
        else:
            raise AssertionError(
                "an overwrite of an existing note this process never observed "
                "must be refused — that is the declared break, not a defect"
            )

        # The README round-trip recipe, verbatim, under the escape.
        write_markdown_file(note, entity=doc.entity, body=doc.body,
                            extra_fields=doc.extra_fields, overwrite=True,
                            allow_unverified_overwrite=True)
        landed = note.read_text(encoding="utf-8")
        assert "custom_field: keep-me-1a2b" in landed, (
            f"the extra field the test wrote must survive; got:\n{landed}"
        )
        assert "- a body line" in landed

        # ...and the escape does NOT buy a body wipe: the WI-126 guard still
        # fires, which is the half D8(d)'s correction exists to keep.
        try:
            write_markdown_file(note, entity=doc.entity, body="",
                                extra_fields=doc.extra_fields, overwrite=True,
                                allow_unverified_overwrite=True)
        except BodyTruncationError:
            pass
        else:
            raise AssertionError(
                "allow_unverified_overwrite says 'I did not read this note', "
                "never 'I may destroy its body' — the WI-126 shrink guard must "
                "still fire"
            )
