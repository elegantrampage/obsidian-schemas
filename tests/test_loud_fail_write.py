"""WI-020 — AC-4 and AC-5: the guard refuses when it cannot verify, and a write
failure stops being a legitimate no-op's return value.
"""

from pathlib import Path

import pytest

from obsidian_schemas import PersonRepository
from obsidian_schemas.errors import (
    FrontmatterParseError,
    UnverifiableBodyError,
    WriteFailedError,
)
from obsidian_schemas.models import Person
from obsidian_schemas.writer import (
    BodyTruncationError,
    update_frontmatter_field,
    update_frontmatter_fields,
    write_markdown_file,
)

from tests.derivations import (
    PACKAGE_ROOT,
    SiteId,
    non_completed_write_sites,
    python_files_under,
)
from tests.support import patcher, temp_dir

SHARED_SCAN_MODULE = "tests.derivations"
PERSON = "obsidian_schemas/repositories/person.py"

MALFORMED = "---\ntype: person\nname: Broken\nnotes: a: b: c\n---\n\n## Notes\n\n- body\n"


def _seed(vault, name="Target", body="## Timeline\n\n### old entry\n"):
    vault.mkdir(parents=True, exist_ok=True)
    path = vault / f"@{name}.md"
    path.write_text(
        f"---\ntype: person\nname: {name}\ntags:\n  - person\n---\n\n{body}",
        encoding="utf-8",
    )
    repo = PersonRepository(vault)
    return repo, repo.get(name), path


# ---------------------------------------------------------------------------
# AC-4
# ---------------------------------------------------------------------------

def test_body_guard_refuses_when_unverifiable():
    """AC-4. Zero-arg — the battery invokes it by name (tests/support.py)."""
    with temp_dir() as tmp_path, patcher() as monkeypatch:
        _check_body_guard_refuses_when_unverifiable(tmp_path, monkeypatch)


def _check_body_guard_refuses_when_unverifiable(tmp_path, monkeypatch):
    entity = Person(type="person", name="Target")

    # (a) the existing file's frontmatter is malformed YAML.
    a = tmp_path / "@A.md"
    a.write_text(MALFORMED, encoding="utf-8")
    original = a.read_text(encoding="utf-8")
    with pytest.raises(UnverifiableBodyError) as caught:
        write_markdown_file(a, entity=entity, body="", overwrite=True,
                            allow_unverified_overwrite=True)
    # Distinguishable BY TYPE: BodyTruncationError subclasses Exception and
    # UnverifiableBodyError subclasses ValueError, with neither in the other's
    # ancestry. "Could not verify" and "verified, and it would truncate" are
    # different answers and a caller must be able to tell them apart.
    assert not isinstance(caught.value, BodyTruncationError)
    assert a.read_text(encoding="utf-8") == original, "nothing may be written"

    # (b) the existing file's READ raises. monkeypatch rather than chmod:
    # deterministic and root-safe.
    b = tmp_path / "@B.md"
    b.write_text("---\ntype: person\nname: Target\n---\n\n## Notes\n\n- keep me\n",
                 encoding="utf-8")
    original = b.read_text(encoding="utf-8")
    real_read_text = Path.read_text

    def deny(self, *args, **kwargs):
        if self.name == "@B.md":
            raise PermissionError(13, "Permission denied")
        return real_read_text(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", deny)
    with pytest.raises(UnverifiableBodyError) as caught:
        write_markdown_file(b, entity=entity, body="", overwrite=True,
                            allow_unverified_overwrite=True)
    monkeypatch.setattr(Path, "read_text", real_read_text)
    assert not isinstance(caught.value, BodyTruncationError)
    assert b.read_text(encoding="utf-8") == original

    # Neither path may reach `existing_body = ""` — which is exactly what the
    # two assertions above prove: had the guard assumed empty, the overwrite
    # would have proceeded and the body would be gone.


# ---------------------------------------------------------------------------
# AC-5
# ---------------------------------------------------------------------------

def test_write_failure_raises_and_noops_keep_their_return():
    """AC-5. Zero-arg for the same reason as AC-4 above."""
    with temp_dir() as tmp_path, patcher() as monkeypatch:
        _check_write_failure_raises_and_noops_keep_their_return(
            tmp_path, monkeypatch)


def _check_write_failure_raises_and_noops_keep_their_return(tmp_path, monkeypatch):
    walk = python_files_under
    universe = non_completed_write_sites
    for derivation in (walk, universe):
        assert derivation.__module__ == SHARED_SCAN_MODULE, (
            f"{derivation.__name__} must come from the shared scan module"
        )

    # --- CLOSURE: every surviving falsy return is classified -----------------
    #
    # Evaluated against POST-FIX source, and the pre-fix 28 is a baseline rather
    # than the answer: a site this item moves to the raise side LEAVES this
    # universe entirely. So what is left is the residue, and the property worth
    # asserting is that every member of it is a LEGITIMATE no-op — nothing
    # failure-shaped still reports as one.
    sites = universe(walk(PACKAGE_ROOT))
    classification = {
        # (a) dedup-key match
        SiteId(PERSON, "PersonRepository.append_to_timeline", 0): "a",
        SiteId(PERSON, "PersonRepository.append_to_body_section", 1): "a",
        # (b) governed absence: create_if_missing=False with the section absent
        SiteId(PERSON, "PersonRepository.append_to_body_section", 0): "b",
        # (c) match-not-found in a match-mutation writer
        SiteId(PERSON, "PersonRepository.update_to_discuss_item", 0): "c",
        SiteId(PERSON, "PersonRepository.update_to_discuss_item", 1): "c",
        SiteId(PERSON, "PersonRepository.remove_to_discuss_item", 0): "c",
        SiteId(PERSON, "PersonRepository.remove_to_discuss_item", 1): "c",
        # (d) a helper's falsy return its only caller already makes loud
        SiteId(PERSON, "PersonRepository._get_body_content", 0): "d",
    }
    unclassified = set(sites) - set(classification)
    assert not unclassified, (
        "a falsy return in a write path is classified by NOTHING. It is either "
        "a legitimate no-op that belongs in this map, or a failure reporting "
        f"itself as one — which is the whole defect class: {sorted(unclassified)}"
    )
    stale = set(classification) - set(sites)
    assert not stale, f"the map names sites the scan cannot return: {sorted(stale)}"

    # --- P1: a genuine I/O failure at a blanket-except writer RAISES ---------
    repo, person, path = _seed(tmp_path / "p1")
    boom = OSError(28, "No space left on device")
    # WI-004 Table 3a row 2: the fault is injected AT THE DOOR, because
    # Path.write_text is no longer where package code commits bytes. The
    # asserted outcome is unchanged.
    from obsidian_schemas import vault_io
    real_write_note = vault_io.write_note
    monkeypatch.setattr(vault_io, "write_note",
                        lambda *a, **k: (_ for _ in ()).throw(boom))
    with pytest.raises(WriteFailedError):
        repo.append_to_timeline(person, "### new\n")
    monkeypatch.setattr(vault_io, "write_note", real_write_note)

    # --- P2: every fence case RAISES, at each of the four writers ------------
    for fence_case in ("## Notes\n\n- no fence at all\n", "---\ntype: person\n"):
        repo, person, path = _seed(tmp_path / "p2")
        path.write_text(fence_case, encoding="utf-8")
        with pytest.raises(FrontmatterParseError):
            repo.append_to_body_section(person, "Notes", "- x\n")
        with pytest.raises(FrontmatterParseError):
            repo.add_to_discuss_item(person, "topic")
        with pytest.raises(FrontmatterParseError):
            repo.update_to_discuss_item(person, "topic", True)
        with pytest.raises(FrontmatterParseError):
            repo.remove_to_discuss_item(person, "topic")

    # ...and the shared read helper stops reporting a broken note as "no items".
    repo, person, path = _seed(tmp_path / "p2r")
    path.write_text("---\ntype: person\n", encoding="utf-8")
    with pytest.raises(ValueError):
        repo.get_to_discuss_items(person)

    # --- P4: the existence pre-check RAISES ---------------------------------
    with pytest.raises(FileNotFoundError):
        update_frontmatter_field(tmp_path / "nope.md", "role", "vip")
    with pytest.raises(FileNotFoundError):
        update_frontmatter_fields(tmp_path / "nope.md", {"role": "vip"})

    # --- P3: ACCOMMODATE, with PRESERVATION ---------------------------------
    # Proved on the two bodies the accommodation actually exists for: the
    # hand-created-in-Obsidian note. Routing this through the sibling's
    # parse_body_sections/write_body_sections round-trip destroys both — it
    # keeps only `^## `-delimited spans — which is why the mechanism is string
    # insertion.
    for label, body in (("headingless", "just a paragraph, no headings at all\n"),
                        ("preamble", "preamble above the first heading\n\n## Notes\n\n- x\n")):
        repo, person, path = _seed(tmp_path / f"p3-{label}", body=body)
        original = path.read_text(encoding="utf-8")

        assert repo.append_to_timeline(person, "### entry one\n", "entry one") is True
        after = path.read_text(encoding="utf-8")

        assert after.startswith(original), (
            f"[{label}] the accommodation dropped pre-existing bytes — it traded "
            f"a silently dropped ENTRY for a silently dropped NOTE BODY"
        )
        assert "### entry one" in after, f"[{label}] the entry is not readable back"
        assert after.count("## Timeline") == 1
        # frontmatter byte-identical
        assert after.split("---", 2)[1] == original.split("---", 2)[1]

        # Idempotent: the dedup no-op is untouched by the accommodation and
        # keeps its exact False, which is why the honest claim is that
        # STRUCTURAL absence can no longer drop an entry, not that a drop is
        # impossible.
        assert repo.append_to_timeline(person, "### entry one\n", "entry one") is False
        assert path.read_text(encoding="utf-8").count("## Timeline") == 1

    # --- the no-op half: every case keeps the EXACT value it returns today ---
    repo, person, path = _seed(tmp_path / "noop",
                               body="## Timeline\n\n### old\n\n## Notes\n\n- n\n")
    # (a) dedup, both writers
    assert repo.append_to_timeline(person, "### old\n", "### old") is False
    assert repo.append_to_body_section(person, "Notes", "- n\n",
                                       deduplicate_key="- n") is False
    # (b) governed absence
    assert repo.append_to_body_section(person, "Absent Section", "- x\n",
                                       create_if_missing=False) is False
    # (c) match-not-found, both writers, both branches
    assert repo.update_to_discuss_item(person, "nothing like this", True) is False
    assert repo.remove_to_discuss_item(person, "nothing like this") is False
    repo2, person2, path2 = _seed(tmp_path / "noop2",
                                  body="## To Discuss\n\n- [ ] present\n")
    assert repo2.update_to_discuss_item(person2, "absent item", True) is False
    assert repo2.remove_to_discuss_item(person2, "absent item") is False
    # (d) the helper's missing-file None, already made loud by its only caller
    missing = Person(type="person", name="Nobody At All")
    with pytest.raises(ValueError):
        repo.get_to_discuss_items(missing)
