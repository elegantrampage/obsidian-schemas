"""WI-020 — AC-1 and AC-2: the parse seam refuses, and no write is built on a
failed parse.

Every derivation below is obtained BY IMPORT from `tests.derivations`, and each
test asserts of the very callables it computes with that they are homed there.
A locally re-implemented copy fails THIS criterion, not a sibling's: two
predicates that agree on today's tree diverge on the first future write path,
and that divergence is the refuse-vs-propagate collision the composition exists
to catch.
"""

import traceback

import pytest
import yaml

from obsidian_schemas import PersonRepository
from obsidian_schemas.errors import (
    FrontmatterParseError,
    LoudFailError,
    SchemaDriftError,
    WriteFailedError,
)
from obsidian_schemas.models import Book, Company, Person
from obsidian_schemas.parser import (
    parse_frontmatter,
    parse_markdown_content,
    parse_markdown_file,
    parse_book,
    parse_company,
    parse_meeting,
    parse_person,
    parse_to_model,
)
from obsidian_schemas.writer import (
    roundtrip_file,
    update_frontmatter_field,
    update_frontmatter_fields,
)

from tests.support import temp_dir

from tests.derivations import (
    PACKAGE_ROOT,
    FunctionId,
    base_repository_subclasses,
    functions_parsing_then_writing,
    functions_reserializing_parsed_frontmatter,
    load_file_implementations,
    parse_frontmatter_exit_sites,
    python_files_under,
    seam_invocation_closure,
)

SHARED_SCAN_MODULE = "tests.derivations"

# A stray unquoted colon: valid-looking frontmatter that yaml.safe_load refuses.
MALFORMED = '---\ntype: person\nname: Broken\nnotes: {sentinel}\n---\n\n## Notes\n\n- real body\n'
ABSENT = "# Just a heading\n\nNo frontmatter fence at all.\n"


def _malformed(sentinel="a: b: c"):
    return MALFORMED.format(sentinel=sentinel)


def _seeded_person(tmp_path, name="Target"):
    """A repository holding one loadable person, whose file the caller then
    corrupts on disk. That ordering is what lets update_fields be reached at
    all: a note that never parsed is not in the cache to be updated."""
    tmp_path.mkdir(parents=True, exist_ok=True)
    path = tmp_path / f"@{name}.md"
    path.write_text(
        f"---\ntype: person\nname: {name}\ntags:\n  - person\n---\n\n## Notes\n\n- original\n",
        encoding="utf-8",
    )
    repo = PersonRepository(tmp_path)
    return repo, repo.get(name), path


# ---------------------------------------------------------------------------
# AC-1
# ---------------------------------------------------------------------------

def test_no_mutation_writes_through_failed_parse():
    """AC-1. Takes no fixture: the AC battery calls this by name with no
    arguments, so the check owns its own scratch directory (tests/support.py).
    """
    with temp_dir() as tmp_path:
        _check_no_mutation_writes_through_failed_parse(tmp_path)


def _check_no_mutation_writes_through_failed_parse(tmp_path):
    # --- the derivation, performed HERE, at test time, against live source ---
    walk = python_files_under
    loose = functions_parsing_then_writing
    flow = functions_reserializing_parsed_frontmatter

    # Single-sourcing asserted on the SAME bindings this test computes with, so
    # a private copy carries this module's __module__ and turns THIS check red.
    for derivation in (walk, loose, flow):
        assert derivation.__module__ == SHARED_SCAN_MODULE, (
            f"{derivation.__name__} must be imported from the shared scan "
            f"module, not re-implemented here (got {derivation.__module__})"
        )

    files = walk(PACKAGE_ROOT)
    write_paths = flow(files)
    loose_paths = loose(files)

    expected = {
        FunctionId("obsidian_schemas/repositories/base.py",
                   "BaseRepository.update_fields"),
        FunctionId("obsidian_schemas/writer.py", "update_frontmatter_field"),
        FunctionId("obsidian_schemas/writer.py", "update_frontmatter_fields"),
        FunctionId("obsidian_schemas/writer.py", "roundtrip_file"),
    }
    assert write_paths == expected, (
        "the data-flow scan no longer returns exactly the paths this test "
        "exercises — a fifth such caller must be added to the map, not dropped "
        f"from the scan. Got: {sorted(write_paths)}"
    )

    # THE DISCRIMINATION PROOF. write_markdown_file must be REACHED by the
    # traversal and REJECTED BY THE PREDICATE — never excluded by name. A scan
    # asserted only against what it returns is indistinguishable from a function
    # that returns those four names.
    guard = FunctionId("obsidian_schemas/writer.py", "write_markdown_file")
    assert guard in loose_paths, (
        "write_markdown_file must be REACHED by the traversal — it does call "
        "parse_frontmatter and then write"
    )
    assert guard not in write_paths, (
        "write_markdown_file must be REJECTED by the data-flow predicate — it "
        "discards the parsed frontmatter and builds its output from its own "
        "arguments. Its malformed-input behaviour is AC-4's, not this one's."
    )
    assert loose_paths - write_paths == {guard}

    # --- the raise half: malformed YAML, and the file left byte-identical ---
    for fid in sorted(write_paths):
        repo, person, path = _seeded_person(tmp_path / fid.name, "Target")
        original = _malformed()
        path.write_text(original, encoding="utf-8")

        invoke = {
            "update_fields": lambda: repo.update_fields(person, {"role": "vip"}),
            "update_frontmatter_field": lambda: update_frontmatter_field(
                path, "role", "vip"),
            "update_frontmatter_fields": lambda: update_frontmatter_fields(
                path, {"role": "vip"}),
            "roundtrip_file": lambda: roundtrip_file(path),
        }[fid.name]

        with pytest.raises(ValueError) as caught:
            invoke()
        assert isinstance(caught.value, LoudFailError), (
            f"{fid.name} raised {type(caught.value).__name__}, not one of ours"
        )
        # The oracle is the exact string this test wrote — not a length, not a
        # substring of anything a library produced.
        assert path.read_text(encoding="utf-8") == original, (
            f"{fid.name} MUTATED a note whose frontmatter did not parse — this "
            f"is the C2 corruption chain"
        )

    # --- the absent half, over the SAME derived list, not a subset of it ---
    for fid in sorted(write_paths):
        repo, person, path = _seeded_person(tmp_path / (fid.name + "-absent"), "Target")
        path.write_text(ABSENT, encoding="utf-8")

        if fid.name == "update_fields":
            updated = repo.update_fields(person, {"role": "vip"})
            assert updated is not None
        elif fid.name == "update_frontmatter_field":
            assert update_frontmatter_field(path, "role", "vip") is True
        elif fid.name == "update_frontmatter_fields":
            assert update_frontmatter_fields(path, {"role": "vip"}) is True
        else:
            assert isinstance(roundtrip_file(path), str)

        after = path.read_text(encoding="utf-8")
        # Closed-form contract, stated from what this test passed in: the
        # original text survives after the closing fence, and every key it
        # supplied is present. Never a byte-snapshot of pre-fix output, which no
        # post-fix test can obtain.
        assert ABSENT.strip() in after, (
            f"{fid.name} lost the body of a legitimately fence-less note"
        )
        if fid.name != "roundtrip_file":
            assert "role" in after


# ---------------------------------------------------------------------------
# AC-2
# ---------------------------------------------------------------------------

def test_parse_boundaries_distinguish_failure_from_empty():
    """AC-2. Zero-arg for the same reason as AC-1 above."""
    with temp_dir() as tmp_path:
        _check_parse_boundaries_distinguish_failure_from_empty(tmp_path)


def _check_parse_boundaries_distinguish_failure_from_empty(tmp_path):
    walk = python_files_under
    exits = parse_frontmatter_exit_sites
    flow = functions_reserializing_parsed_frontmatter
    loose = functions_parsing_then_writing
    subclasses = base_repository_subclasses
    loaders = load_file_implementations
    closure = seam_invocation_closure

    for derivation in (walk, exits, flow, loose, subclasses, loaders, closure):
        assert derivation.__module__ == SHARED_SCAN_MODULE, (
            f"{derivation.__name__} must come from the shared scan module"
        )

    files = walk(PACKAGE_ROOT)

    # --- (i) parse_frontmatter: sites scanned, classes exercised -------------
    sites = exits(files)
    # The map is keyed BY SITE, and a site may carry MORE THAN ONE outcome
    # class. Keying by class instead is red on a correct implementation: five
    # classes against four sites means one entry matches no site the scan can
    # return, and the cheap repair drops the empty-fence class — which is in
    # this AC precisely because it is a distinct outcome reached through a
    # SHARED return.
    site_classes = {
        sites[0]: ["no-leading-fence"],
        sites[1]: ["unclosed-fence"],
        sites[2]: ["empty-fence", "valid-frontmatter"],
        sites[3]: ["yaml-error"],
    }
    assert set(sites) == set(site_classes), (
        "the discovered exit-site set and the map's keys must match exactly; "
        f"discovered {sorted(sites)}"
    )

    exercised = set()

    fm, body = parse_frontmatter(ABSENT)
    assert (fm, body) == ({}, ABSENT)
    exercised.add("no-leading-fence")

    with pytest.raises(FrontmatterParseError):
        parse_frontmatter("---\ntype: person\n\nnever closed\n")
    exercised.add("unclosed-fence")

    fm, body = parse_frontmatter("---\n---\n\nbody text\n")
    assert fm == {} and "body text" in body
    exercised.add("empty-fence")

    fm, body = parse_frontmatter("---\ntype: person\nname: X\n---\n\nbody\n")
    assert fm["name"] == "X" and "body" in body
    exercised.add("valid-frontmatter")

    with pytest.raises(FrontmatterParseError):
        parse_frontmatter(_malformed())
    exercised.add("yaml-error")

    named = {c for classes in site_classes.values() for c in classes}
    assert exercised == named, (
        "every named outcome class must be exercised by at least one input — a "
        "site carrying two classes cannot be closed with one case"
    )

    # Malformed must never return a legitimate case's value.
    for legitimate in (ABSENT, "---\n---\n\nbody\n"):
        assert parse_frontmatter(legitimate) != ({}, _malformed())

    # --- (ii) parse_to_model: THREE fixtures, ONE test, one code path -------
    # All three are model_validate raising inside the same call with the same
    # model_class object, and they require OPPOSITE answers. A fixture set
    # containing only the drifted note reads as the whole property, which is
    # exactly what lets the foreign-type regression ship green.
    owned_drifted = {"type": "person", "name": "X", "emails": "not-a-list"}
    with pytest.raises(SchemaDriftError) as caught:
        parse_to_model(owned_drifted, Person)
    assert caught.value.declared_type == "person"

    foreign = {"type": "company", "name": "Acme", "industry": "tech"}
    assert parse_to_model(foreign, Person) == (None, foreign.copy())

    no_type_drifted = {"name": "X", "emails": "not-a-list"}
    entity, _extra = parse_to_model(no_type_drifted, Person)
    assert entity is None, (
        "a note with no readable `type` carries no ownership evidence of "
        "either kind and must keep today's None"
    )

    # The comparand is read off the class's OWN declaration, never hardcoded.
    assert Person.model_fields["type"].default == "person"
    assert Company.model_fields["type"].default == "company"

    # --- (iii) the closure, its computed stop set, and the partition --------
    write_set = flow(files)                                  # functions already
    loader_set = loaders(subclasses(files))                  # classes -> MRO -> functions
    guard_set = loose(files) - write_set                     # the set difference

    discovered_classes = subclasses(files)
    assert len(discovered_classes) == 4
    assert len(loader_set) == 3, (
        "the class->loader map is MANY-TO-ONE: PersonRepository and "
        "CompanyRepository share one inherited _load_file, so asserting one "
        "loader per discovered class is red on a correct implementation"
    )

    stop = write_set | loader_set | guard_set
    computed = closure(files, stop)

    for label, contribution in (("writers", write_set),
                                ("loaders", loader_set),
                                ("guard", guard_set)):
        assert contribution, f"the {label} contribution is EMPTY — a partition "\
                             f"over an empty contribution degenerates into "\
                             f"'everything is residue' while still reading green"
        assert contribution <= computed, (
            f"the {label} contribution is not a subset of the closure — this is "
            f"the mis-domained-conversion failure (classes where functions were "
            f"needed): {sorted(contribution - computed)}"
        )

    residue = computed - stop
    # Partition, asserted in BOTH directions.
    assert write_set | loader_set | guard_set | residue == computed
    assert not (write_set & loader_set) and not (write_set & guard_set)
    assert not (loader_set & guard_set)
    assert len(computed) == len(write_set) + len(loader_set) + len(guard_set) + len(residue), (
        "a closure member landed in two classes — the refuse-vs-propagate "
        "collision this partition exists to catch"
    )

    assert {f.name for f in residue} == {
        "parse_markdown_file", "parse_markdown_content",
        "parse_person", "parse_company", "parse_book", "parse_meeting",
    }

    # --- every propagating member actually propagates, invoked not assumed ---
    note = tmp_path / "@Broken.md"
    note.write_text(_malformed(), encoding="utf-8")
    propagators = {
        "parse_markdown_file": lambda: parse_markdown_file(note),
        "parse_markdown_content": lambda: parse_markdown_content(_malformed()),
        "parse_person": lambda: parse_person(_malformed()),
        "parse_company": lambda: parse_company(_malformed()),
        "parse_book": lambda: parse_book(_malformed()),
        "parse_meeting": lambda: parse_meeting(_malformed()),
    }
    assert set(propagators) == {f.name for f in residue}
    for name, invoke in propagators.items():
        with pytest.raises(FrontmatterParseError):
            invoke()

    # ...while keeping today's exact returns for absent frontmatter and for a
    # legitimately foreign/unknown type.
    # The conveniences return the ENTITY (or None), not a ParsedDocument.
    assert parse_person(ABSENT) is None
    assert parse_person("---\ntype: company\nname: Acme\n---\n\nbody\n") is None
    fenceless = tmp_path / "@Plain.md"
    fenceless.write_text(ABSENT, encoding="utf-8")
    assert parse_markdown_file(fenceless).entity is None


# ---------------------------------------------------------------------------
# Threat Model M1 — not an AC check; the floor grades it.
# ---------------------------------------------------------------------------

def test_seam_errors_carry_bounded_diagnostics(tmp_path):
    # (i) the YAML seam. The test PLANTS the sentinel, so the oracle is a string
    # it authored — never a substring of a library rendering it did not write.
    sentinel = "SENTINEL-fm-9f3a2b"
    block = f'type: person\nname: Broken\nnotes: {sentinel}: leaked\n'
    note = tmp_path / "@Broken.md"
    note.write_text(f"---\n{block}---\n\nbody\n", encoding="utf-8")

    with pytest.raises(FrontmatterParseError) as caught:
        parse_markdown_file(note)
    message = str(caught.value)
    assert sentinel not in message, f"the note's own bytes reached the message: {message}"
    assert str(note) in message, "the message must name the note it refused"

    # The class name is derived by RE-RUNNING the same failure, not read off
    # __cause__ (M5 suppresses the chain, so that would evaluate to "NoneType"
    # and be red against fully correct code) and not hardcoded (a PyYAML that
    # raises a differently-named subclass must move both sides together).
    try:
        yaml.safe_load(block)
        raise AssertionError("the planted block was expected to fail")
    except yaml.YAMLError as ye:
        expected = type(ye).__name__
    assert expected in message

    # (ii) the validation seam — the failing field's NAME is in, its VALUE out.
    value_sentinel = "SENTINEL-val-7c1d4e"
    with pytest.raises(SchemaDriftError) as caught:
        parse_to_model({"type": "person", "name": "X", "emails": value_sentinel},
                       Person)
    message = str(caught.value)
    assert value_sentinel not in message, message
    assert "emails" in message, "the failing field's name is the actionable part"

    # (iii) the fall-through that makes the rule total for types nobody
    # enumerated: a UnicodeDecodeError's str() is a byte snippet of the note.
    from obsidian_schemas.errors import bounded_cause
    assert bounded_cause(
        UnicodeDecodeError("utf-8", b"\xff", 0, 1, "invalid")) == "UnicodeDecodeError"


# ---------------------------------------------------------------------------
# Threat Model M5 — the chain bound. All of it in one function on purpose.
# ---------------------------------------------------------------------------

def test_error_chains_are_bounded(tmp_path, monkeypatch):
    from pathlib import Path as _Path

    # 1. THE SUPPRESSED CASE, asserted over a RENDERED traceback, because
    #    rendering is what M5 actually bounds.
    sentinel = "SENTINEL-chain-4b8e1f"
    note = tmp_path / "@Broken.md"
    note.write_text(f'---\ntype: person\nnotes: {sentinel}: leaked\n---\n\nbody\n',
                    encoding="utf-8")
    with pytest.raises(FrontmatterParseError) as caught:
        parse_markdown_file(note)
    error = caught.value
    text = "".join(traceback.format_exception(type(error), error, error.__traceback__))
    assert sentinel not in text, (
        "the caught library error's str() — which echoes the offending source "
        "line — was rendered above our bounded message. This is what a bare "
        "`from e` does."
    )

    # 2. THE MECHANISM, checked directly, on both seams.
    assert error.__cause__ is None
    assert error.__suppress_context__ is True

    with pytest.raises(SchemaDriftError) as caught:
        parse_to_model({"type": "person", "name": "X", "emails": "nope"}, Person)
    assert caught.value.__cause__ is None
    assert caught.value.__suppress_context__ is True

    # 3. THE CHAINED CASE — an OSError is CHAINABLE and must NOT be suppressed;
    #    Edge Cases/Retry semantics is what depends on it.
    good = tmp_path / "@Good.md"
    good.write_text("---\ntype: person\nname: Good\n---\n\nbody\n", encoding="utf-8")
    boom = OSError(13, "Permission denied")
    real_write_text = _Path.write_text

    def deny(self, *a, **k):
        raise boom

    monkeypatch.setattr(_Path, "write_text", deny)
    with pytest.raises(WriteFailedError) as caught:
        update_frontmatter_field(good, "role", "vip")
    monkeypatch.setattr(_Path, "write_text", real_write_text)
    assert caught.value.__cause__ is boom, (
        "an OSError must survive into __cause__ — a blanket `from None` would "
        "pay for M5 with Edge Cases' promise"
    )

    # 4. THE NOTE-DERIVED CAUSE AT THE SAME SITE — the case a blanket rule gets
    #    wrong in the other direction. Parts 3 and 4 together are why the spec
    #    prescribes chainable_cause rather than either blanket answer.
    undecodable = tmp_path / "@Bytes.md"
    byte_sentinel = b"SENTINEL-bytes-2a6f"
    undecodable.write_bytes(b"---\ntype: person\nname: " + byte_sentinel + b"\xff\xfe\n---\n\nbody\n")
    with pytest.raises(WriteFailedError) as caught:
        update_frontmatter_field(undecodable, "role", "vip")
    error = caught.value
    assert error.__cause__ is None
    assert error.__suppress_context__ is True
    text = "".join(traceback.format_exception(type(error), error, error.__traceback__))
    assert byte_sentinel.decode() not in text
