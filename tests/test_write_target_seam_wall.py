"""WI-029, AC-5 — the provenance function is the ONLY way a write target is
chosen in this package, and a tenth write path cannot route around it.

One check. Its live half classifies every mutation site under
`obsidian_schemas/**` into exactly one of two legal buckets and asserts the two
SETS, never a count. Its battery plants source files in a temp directory and
drives them through the SAME function, both ways: a wall that has never been
shown to REFUSE anything is an assertion about nothing (WI-235), and the
near-misses are what stop the refusal being a substring match.

The escape this battery exists for is one line long. `BookRepository.save` and
`MeetingRepository.save` each hold a complete name-derived write two lines from
`_get_file_name(entity)` to the write call, so "call the seam and ignore it" is a
SMALLER edit at exactly the two sites the seam was widened to reach. That is why
bucket (b) is a DATA-FLOW property and not call-presence.

This module constructs no repository and plants only into a temp directory.
Nothing here reads syntax directly: that capability is single-homed in
`tests/derivations.py`, and every scan below is imported from it.
"""

# FIRST, ahead of every package import: the conveyor may run this module's checks
# under an interpreter that is not this project's, where the imports below cannot
# resolve. A no-op under the floor command and under CI (WI-021).
from tests.ac_interpreter import ensure_project_interpreter

ensure_project_interpreter(__file__)

from pathlib import Path  # noqa: E402

from tests.derivations import (  # noqa: E402
    LEAF_BUCKET,
    PACKAGE_ROOT,
    SEAM_BUCKET,
    SEAM_FUNCTION,
    path_taking_writer_names,
    python_files_under,
    write_target_buckets,
)
from tests.support import temp_dir  # noqa: E402

WRITER_PATH = PACKAGE_ROOT / "writer.py"

# ---------------------------------------------------------------------------
# The expected classification after this build, asserted as a SET equality and
# never as a count — a tenth path joins AC-1's path set and this bucket by
# construction instead of quietly reopening the round-2 finding.
# ---------------------------------------------------------------------------

EXPECTED_LEAF = {
    ("obsidian_schemas/writer.py", "write_markdown_file"),
    ("obsidian_schemas/writer.py", "update_frontmatter_field"),
    ("obsidian_schemas/writer.py", "update_frontmatter_fields"),
    ("obsidian_schemas/writer.py", "roundtrip_file"),
}

EXPECTED_SEAM = {
    ("obsidian_schemas/repositories/base.py", "BaseRepository.save"),
    ("obsidian_schemas/repositories/base.py", "BaseRepository.update_fields"),
    ("obsidian_schemas/repositories/base.py", "BaseRepository.rename_note"),
    ("obsidian_schemas/repositories/person.py",
     "PersonRepository.append_to_timeline"),
    ("obsidian_schemas/repositories/person.py",
     "PersonRepository.append_to_body_section"),
    ("obsidian_schemas/repositories/person.py",
     "PersonRepository.add_to_discuss_item"),
    ("obsidian_schemas/repositories/person.py",
     "PersonRepository.update_to_discuss_item"),
    ("obsidian_schemas/repositories/person.py",
     "PersonRepository.remove_to_discuss_item"),
    ("obsidian_schemas/repositories/book.py", "BookRepository.save"),
    ("obsidian_schemas/repositories/meeting.py", "MeetingRepository.save"),
}


# ---------------------------------------------------------------------------
# The planted battery. Every oracle is the exact source the test itself wrote —
# never a substring of the tree.
# ---------------------------------------------------------------------------

_PROLOGUE = """from obsidian_schemas.writer import write_markdown_file
from obsidian_schemas import vault_io
"""

#: REFUSED — each of these must classify `None` at its write call.
REFUSED_PLANTS = {
    # (1a) a name-derived write, in the spelling the two `save` overrides hold.
    "refused_name_derived_inline.py": """
class Repo:
    def save(self, entity):
        file_path = self.vault_path / f"@{entity.name}.md"
        write_markdown_file(file_path, entity=entity)
""",
    # (1b) …and the same thing behind a helper, so the wall is not a match on
    # the `/` operator.
    "refused_name_derived_helper.py": """
class Repo:
    def _derive(self, entity):
        return self.vault_path / f"@{entity.name}.md"

    def save(self, entity):
        file_path = self._derive(entity)
        write_markdown_file(file_path, entity=entity)
""",
    # (2) the seam CALLED as a bare expression statement beside a separately
    # derived write — call-presence green, nothing routed.
    "refused_bare_expression_call.py": """
class Repo:
    def save(self, entity):
        self._resolve_write_target(entity)
        file_path = self.vault_path / f"@{entity.name}.md"
        write_markdown_file(file_path, entity=entity)
""",
    # (3) the return BOUND and unused — the second spelling of the same escape.
    "refused_bound_and_unused.py": """
class Repo:
    def save(self, entity):
        _ = self._resolve_write_target(entity)
        file_path = self.vault_path / f"@{entity.name}.md"
        write_markdown_file(file_path, entity=entity)
""",
    # (4) the UNCONDITIONAL rebinding: a monotone taint rule passes this and it
    # routes nothing. One line inserted into today's `BookRepository.save`.
    "refused_unconditional_rebinding.py": """
class Repo:
    def save(self, entity):
        file_path = self._resolve_write_target(entity)
        filename = self._get_file_name(entity)
        file_path = self.vault_path / filename
        write_markdown_file(file_path, entity=entity)
""",
    # (5) the resolved value passed as some OTHER argument while the path
    # argument is separately derived.
    "refused_resolved_as_other_argument.py": """
class Repo:
    def save(self, entity):
        resolved = self._resolve_write_target(entity)
        file_path = self.vault_path / f"@{entity.name}.md"
        write_markdown_file(file_path, entity=entity,
                            extra_fields={"provenance": resolved})
""",
    # (6) a write call with NO positional argument fails by the same rule rather
    # than being skipped.
    "refused_no_positional_argument.py": """
class Repo:
    def save(self, entity):
        resolved = self._resolve_write_target(entity)
        write_markdown_file(file_path=resolved, entity=entity)
""",
}

#: ACCEPTED — each of these must classify into a legal bucket at every write call
#: it holds, and a plant holding no write call must contribute no site at all.
ACCEPTED_PLANTS = {
    # (1) a module-level PATH-TAKING LEAF, including the `with … as` hop the
    # archetypal member (`write_markdown_file`) actually uses.
    "accepted_path_taking_leaf.py": """
def write_it(file_path, text):
    with vault_io.note_lock(file_path) as resolved:
        vault_io.write_note(resolved, text, precondition=None)
""",
    # (2) a seam-routed writer, in the `or` spelling `save` ships.
    "accepted_seam_routed_or_form.py": """
class Repo:
    def save(self, entity):
        resolved = self._resolve_write_target(entity)
        derived = self.vault_path / f"@{entity.name}.md"
        file_path = resolved or derived
        write_markdown_file(file_path, entity=entity)
""",
    # (3) a read-only function using `get_file_path` — no write call, no site.
    "accepted_read_only.py": """
class Repo:
    def body_of(self, entity):
        file_path = self.get_file_path(entity.name)
        if file_path is None:
            return None
        return file_path.read_text(encoding="utf-8")
""",
    # (4) the seam NAMED in a comment and a docstring without being called —
    # which is what stops the wall being a grep.
    "accepted_named_in_prose_only.py": '''
class Repo:
    def describe(self, entity):
        """Mentions _resolve_write_target and writes nothing."""
        # _resolve_write_target is named here and called nowhere.
        return str(entity)
''',
    # (5) THE LOAD-BEARING ONE: the documented fallback arm, which REBINDS THE
    # SAME LOCAL inside an `if` testing it. It must PASS, because that is the
    # asymmetry all nine call sites depend on — a wall that forced a uniform
    # fallback would convert the body-writers' loud refusals into note creation.
    "accepted_guarded_fallback_rebinding.py": """
class Repo:
    def append(self, entity):
        file_path = self._resolve_write_target(entity)
        if file_path is None:
            file_path = self.get_file_path(entity.name)
        if file_path is None:
            raise ValueError("not found")
        vault_io.write_note(file_path, "text", precondition=None)
""",
}


def _plant(root: Path, name: str, source: str) -> Path:
    path = root / name
    path.write_text(_PROLOGUE + source, encoding="utf-8")
    return path


def test_every_write_site_resolves_its_target_through_the_one_seam():
    """AC-5. Zero-arg and raising, per the check contract."""
    # ---- LEG ONE: the live classification, as two SET equalities ----
    #
    # The scan predicate is single-homed: a private copy here could be narrowed
    # until it classified everything legally, so its home is asserted first.
    assert write_target_buckets.__module__ == "tests.derivations", (
        "the scan predicate is single-homed: `ast` is named only by "
        "tests/derivations.py, and a private copy here defeats both walls")

    leaves = path_taking_writer_names(WRITER_PATH)
    assert leaves == {"write_markdown_file", "update_frontmatter_field",
                      "update_frontmatter_fields", "roundtrip_file"}, (
        f"the writer module's path-taking leaves are DERIVED; got {sorted(leaves)}")

    sites = write_target_buckets(python_files_under(PACKAGE_ROOT), WRITER_PATH)
    assert sites, "the scan enumerated NOTHING — a vacuous wall"

    unclassified = [s for s in sites if s.bucket is None]
    assert unclassified == [], (
        "these mutation sites choose a write target through neither the seam nor "
        f"a path parameter: {unclassified}")

    by_bucket = {}
    for site in sites:
        by_bucket.setdefault(site.bucket, set()).add((site.module, site.qualname))
    assert by_bucket.get(LEAF_BUCKET, set()) == EXPECTED_LEAF, (
        f"path-taking leaves moved: {by_bucket.get(LEAF_BUCKET, set())}")
    assert by_bucket.get(SEAM_BUCKET, set()) == EXPECTED_SEAM, (
        f"seam-routed writers moved: {by_bucket.get(SEAM_BUCKET, set())}")

    # ---- LEG TWO: the planted battery, driven through the SAME function ----
    with temp_dir() as tmp:
        root = Path(tmp) / "plants"
        root.mkdir()
        for name, source in {**REFUSED_PLANTS, **ACCEPTED_PLANTS}.items():
            _plant(root, name, source)

        planted = write_target_buckets(python_files_under(root), WRITER_PATH)
        planted_by_module = {}
        for site in planted:
            planted_by_module.setdefault(Path(site.module).name, []).append(site)

        for name in REFUSED_PLANTS:
            found = planted_by_module.get(name, [])
            assert found, (
                f"{name}: the enumeration missed this plant entirely — a wall "
                f"that cannot SEE the escape cannot refuse it")
            assert all(site.bucket is None for site in found), (
                f"{name}: expected bucket None at every write call, got {found}")

        for name in ACCEPTED_PLANTS:
            found = planted_by_module.get(name, [])
            assert all(site.bucket in (LEAF_BUCKET, SEAM_BUCKET)
                       for site in found), (
                f"{name}: a legal shape was refused — {found}")

        # The two plants that hold no write call must contribute NO site, which
        # is a different claim from "classified legally".
        for name in ("accepted_read_only.py", "accepted_named_in_prose_only.py"):
            assert planted_by_module.get(name, []) == [], (
                f"{name}: a function that writes nothing is not a mutation site")

        # And the two that DO write must have been seen, or the arm above is
        # satisfied by an enumeration that resolves nothing.
        for name in ("accepted_path_taking_leaf.py",
                     "accepted_seam_routed_or_form.py",
                     "accepted_guarded_fallback_rebinding.py"):
            assert planted_by_module.get(name, []), (
                f"{name}: the enumeration missed a legal write site")

        # The seam's own name is what the data-flow seed keys on, and the
        # refused plants all spell it — so a build that renamed the seam without
        # renaming the seed would pass LEG TWO vacuously.
        assert SEAM_FUNCTION == "_resolve_write_target"
        assert all(SEAM_FUNCTION in source
                   for source in ACCEPTED_PLANTS.values()
                   if "resolve_write_target" in source)
