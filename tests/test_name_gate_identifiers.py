"""WI-021 — AC-4: identifiers normalize identically on every door.

**Stated as an AGREEMENT ACROSS arms, not per door.** An arm that normalizes
differently is a failure rather than a passing variant, and binding the typed
pass to AC-1's derived set is what makes it total: `write_markdown_file(entity=…)`
is a documented public entry point that bypassed `PersonRepository.save`'s
normalization entirely, and arm granularity is what makes that call actually get
issued rather than satisfied by a `frontmatter=` fixture through the same
function.

**The third field is scoped by ARM SHAPE, and the split is forced rather than
chosen.** A migration needs both fields in hand plus the destination's dedupe
set, which only the whole-record frames have; and on a dict-shaped arm an
emitted destination key would REPLACE that field's stored list, because
`update_fields` merges by key replacement. So on a dict arm "in place" must mean
BYTE-IDENTITY, and a build that splits an alias there — or emits a destination
key — is RED.

**Two cells of this criterion are VACUOUS at D8, and this module ASSERTS the
emptiness rather than skipping it.** D8's delta key set is closed at
`{auto_created, name}` by the two branches of `apply_fixes` that assign into the
frontmatter, so no `emails`, `phones` or `aliases` key can reach the gate there
at all. Both cells quantify over an empty set and are satisfied exactly as
signed — but a silently skipped cell is the vacuity shape five red-team rounds
closed, so the emptiness is pinned from what the RUN holds: the identifier-
bearing arm set is DERIVED from each arm's delta key set and asserted by
equality, and the delta D8 actually handed the gate is captured at the call. A
branch that later widens `apply_fixes` to thread an identifier key turns both
assertions RED, which is the point.

Nothing here reads syntax (no `ast`): that capability is single-homed in
`tests/derivations.py`.
"""

# FIRST, ahead of every package import: the conveyor may run this module's check
# under an interpreter that is not this project's, where the imports below cannot
# resolve. A no-op under the floor command and under CI (WI-021; see
# `tests/ac_interpreter.py` for the failure this closes).
from tests.ac_interpreter import ensure_project_interpreter

ensure_project_interpreter(__file__)

import io  # noqa: E402 — everything below runs only once the interpreter is right
from contextlib import redirect_stderr
from pathlib import Path

from obsidian_schemas.errors import NameGateRefusal
from obsidian_schemas.models import Person
from obsidian_schemas.name_gate import PERSON_TYPE, UNDECLARED_PATTERN, gate_write
from obsidian_schemas.parser import parse_frontmatter
from obsidian_schemas.repositories.person import PersonRepository
from obsidian_schemas.writer import (
    update_frontmatter_field,
    update_frontmatter_fields,
    write_markdown_file,
)
from tests.support import patcher, temp_dir
from tests.test_lint_vault_fix_gate import lint_vault
from tests.test_name_gate_wall import (
    D1A,
    D1B,
    D1C,
    D4,
    D5,
    D6,
    D7,
    D8,
    plant_note,
)

DERIVED_SET = {D1A, D1B, D1C, D4, D5, D6, D7, D8}
TYPED_PASS_EXCLUSION = {D7}

IDENTIFIER_KEYS = frozenset({"emails", "phones", "aliases"})

# The two FRAME-CLOSED arms. Every other arm's delta key set is OPEN to its
# caller, which is exactly why a criterion quantifying over "a write that
# INTRODUCES an identifier" lets D8 through — D8 introduces two keys — while D8
# can construct almost none of the subjects.
CLOSED_DELTA_KEY_SETS = {
    D7: frozenset(),
    D8: frozenset({"auto_created", "name"}),
}

# The dict-shaped arms, where `aliases[]` passes through byte-identical.
DICT_SHAPED_ARMS = {D1B, D1C, D4, D5, D6, D8}

UNDECLARED_ARMS = {D1B, D1C, D5, D6}
UNDECLARED_EXCLUSION = {D1A, D4, D7, D8}

BLOB_FORMS = ["Al B <A@B.com>", "Al B (A@B.com)", "a@b.com"]
COLLAPSED = ["a@b.com"]

DUPLICATE_PHONES = ["447700900123", "+44 7700 900123"]
E164_WINNER = ["+44 7700 900123"]


def _identifier_bearing_arms():
    """DERIVED per arm from that arm's delta key set, never hand-listed."""
    return {arm for arm in DERIVED_SET
            if arm not in CLOSED_DELTA_KEY_SETS
            or (CLOSED_DELTA_KEY_SETS[arm] & IDENTIFIER_KEYS)}


def _read(note: Path):
    frontmatter, _body = parse_frontmatter(note.read_text(encoding="utf-8"))
    return frontmatter


def test_identifiers_normalize_identically_on_every_door():
    """AC-4's check. Zero-arg and raising, per the check contract."""
    assert TYPED_PASS_EXCLUSION == {D7}, (
        "the only arm excluded from the typed pass is the one that introduces "
        "no fields"
    )
    bearing = _identifier_bearing_arms()
    assert bearing == DERIVED_SET - {D7, D8}, (
        "the identifier-bearing fixture set is DERIVED from each arm's delta "
        f"key set, not hand-scoped; the derivation returned {sorted(bearing)}"
    )

    with temp_dir() as root:
        _check_the_typed_pass_agrees_across_arms(root / "typed", bearing)
    with temp_dir() as root:
        _check_the_third_field_is_scoped_by_arm_shape(root / "third")
    with temp_dir() as root:
        _check_the_rider_and_idempotence(root / "rider")
    with temp_dir() as root:
        _check_the_phones_leg_through_the_arms(root / "phones")
    with temp_dir() as root:
        _check_the_two_negative_legs_at_arm_granularity(root / "negatives")
    with temp_dir() as root:
        _check_the_undeclared_pass(root / "undeclared")
    with temp_dir() as root:
        _check_the_two_d8_cells_are_vacuous(root / "vacuous")


def _check_the_typed_pass_agrees_across_arms(vault: Path, bearing):
    """Three spellings of one address collapse to ONE entry, identically at
    every arm that can carry an identifier."""
    vault.mkdir(parents=True)
    reached = set()

    # D1a — the `entity=` arm, a required fixture in its own right.
    d1a = vault / "@d1a.md"
    write_markdown_file(d1a, entity=Person(name="Dave Smith",
                                           emails=list(BLOB_FORMS)))
    assert _read(d1a)["emails"] == COLLAPSED
    reached.add(D1A)

    # D1b and D1c — the two dict-shaped arms of the same function.
    d1b = vault / "@d1b.md"
    write_markdown_file(d1b, frontmatter={"type": "person", "name": "Dave Smith",
                                          "emails": list(BLOB_FORMS)})
    assert _read(d1b)["emails"] == COLLAPSED
    reached.add(D1B)

    d1c = vault / "@d1c.md"
    write_markdown_file(d1c, extra_fields={"type": "person", "name": "Dave Smith",
                                           "emails": list(BLOB_FORMS)})
    assert _read(d1c)["emails"] == COLLAPSED
    reached.add(D1C)

    # D4 — update_fields, which `_writeback_identifier`'s reuse branch reaches.
    repo_vault = vault / "repo"
    repo_vault.mkdir()
    note = plant_note(repo_vault, "@Dave Smith", type="person", name="Dave Smith")
    repo = PersonRepository(repo_vault)
    repo.update_fields(repo.get("Dave Smith"), {"emails": list(BLOB_FORMS)})
    assert _read(note)["emails"] == COLLAPSED
    reached.add(D4)

    # D5 and D6 — the public writer doors.
    d5 = plant_note(vault, "@d5", type="person", name="Dave Smith")
    update_frontmatter_field(d5, "emails", list(BLOB_FORMS))
    assert _read(d5)["emails"] == COLLAPSED
    reached.add(D5)

    d6 = plant_note(vault, "@d6", type="person", name="Dave Smith")
    update_frontmatter_fields(d6, {"emails": list(BLOB_FORMS)})
    assert _read(d6)["emails"] == COLLAPSED
    reached.add(D6)

    assert reached == bearing, (
        f"every identifier-bearing arm needs its own fixture; missing "
        f"{sorted(bearing - reached)}"
    )


def _check_the_third_field_is_scoped_by_arm_shape(vault: Path):
    """`aliases[]` is the third field, and it does NOT behave the same at every
    arm."""
    vault.mkdir(parents=True)

    # ON THE ENTITY-SHAPED ARM both migrations run — the payload guarantees both
    # a migration's source and its destination.
    entity = vault / "@entity.md"
    write_markdown_file(entity, entity=Person(
        name="Dave Smith",
        emails=["Al B <A@B.com>"],
        aliases=["x@y.com", "Zed"],
    ))
    frontmatter = _read(entity)
    assert frontmatter["emails"] == ["a@b.com", "x@y.com"], (
        "M1: an address found in an aliases[] entry moves to emails[]"
    )
    assert frontmatter["aliases"] == ["Zed", "Al B"], (
        "M2: the display half of an emails[] entry moves to aliases[]"
    )

    # ON EVERY DICT-SHAPED ARM `aliases[]` is BYTE-IDENTICAL — a build that
    # splits an alias there would discard the address half rather than
    # normalize it, and a build that emitted a destination key would REPLACE
    # that field's stored list.
    stored_aliases = ["x@y.com", "Zed"]
    dict_arms = []

    d1b = vault / "@d1b.md"
    write_markdown_file(d1b, frontmatter={"type": "person", "name": "Dave Smith",
                                          "emails": ["Al B <A@B.com>"],
                                          "aliases": list(stored_aliases)})
    dict_arms.append((D1B, d1b))

    d1c = vault / "@d1c.md"
    write_markdown_file(d1c, extra_fields={"type": "person", "name": "Dave Smith",
                                           "emails": ["Al B <A@B.com>"],
                                           "aliases": list(stored_aliases)})
    dict_arms.append((D1C, d1c))

    repo_vault = vault / "repo"
    repo_vault.mkdir()
    d4 = plant_note(repo_vault, "@Dave Smith", type="person", name="Dave Smith")
    repo = PersonRepository(repo_vault)
    repo.update_fields(repo.get("Dave Smith"),
                       {"emails": ["Al B <A@B.com>"],
                        "aliases": list(stored_aliases)})
    dict_arms.append((D4, d4))

    d5 = plant_note(vault, "@d5", type="person", name="Dave Smith")
    update_frontmatter_field(d5, "aliases", list(stored_aliases))
    update_frontmatter_field(d5, "emails", ["Al B <A@B.com>"])
    dict_arms.append((D5, d5))

    d6 = plant_note(vault, "@d6", type="person", name="Dave Smith")
    update_frontmatter_fields(d6, {"emails": ["Al B <A@B.com>"],
                                   "aliases": list(stored_aliases)})
    dict_arms.append((D6, d6))

    for arm, note in dict_arms:
        assert arm in DICT_SHAPED_ARMS
        frontmatter = _read(note)
        assert frontmatter["aliases"] == stored_aliases, (
            f"{arm.qualname}: aliases[] must be BYTE-IDENTICAL on a dict arm, "
            f"got {frontmatter['aliases']!r}"
        )
        # …and the emails[] half stores the bare address, DROPPING the display
        # half, which has no destination here. A real loss against disk, signed.
        assert frontmatter["emails"] == ["a@b.com"], arm.qualname
        # The gate emitted NO key the write did not carry.
        assert "phones" not in frontmatter or isinstance(
            frontmatter.get("phones"), (list, type(None))), arm.qualname


def _check_the_rider_and_idempotence(vault: Path):
    vault.mkdir(parents=True)
    repo = PersonRepository(vault)
    person = Person(name="Dave Smith", emails=["Al B <A@B.com>"],
                    aliases=["x@y.com"], phones=list(DUPLICATE_PHONES))
    path = repo.save(person)

    # THE RIDER writes the gate's normalized identifier fields back onto the
    # ENTITY — and never `name`.
    assert person.emails == ["a@b.com", "x@y.com"]
    assert person.aliases == ["Al B"]
    assert person.phones == E164_WINNER
    assert person.name == "Dave Smith"

    # IDEMPOTENCE, exercised rather than asserted: one save invokes the gate
    # twice — the rider, then the entity arm on the projection the rider just
    # produced — so a non-idempotent gate would diverge between the two.
    before = path.read_bytes()
    repo.save(person)
    assert path.read_bytes() == before
    assert person.emails == ["a@b.com", "x@y.com"]
    assert person.aliases == ["Al B"]
    assert person.phones == E164_WINNER

    # And at the unit, on both values of whole_record.
    payload = {"name": "Dave Smith", "emails": ["Al B <A@B.com>"],
               "aliases": ["x@y.com"], "phones": list(DUPLICATE_PHONES)}
    for whole_record in (True, False):
        once = gate_write(payload, declared_type=PERSON_TYPE,
                          whole_record=whole_record)
        assert gate_write(once, declared_type=PERSON_TYPE,
                          whole_record=whole_record) == once


def _check_the_phones_leg_through_the_arms(vault: Path):
    """The dedupe is performed on the WHOLE stored list, so it is a DELETION
    over live data — carried here at arm granularity rather than only at the
    unit, because what reaches DISK is the thing being signed. Every oracle
    reads back off the COMMITTED FILE, never off the returned dict."""
    vault.mkdir(parents=True)

    # D1a and the rider, together — one `repo.save` exercises both.
    repo = PersonRepository(vault)
    person = Person(name="Dave Smith", phones=list(DUPLICATE_PHONES))
    path = repo.save(person)
    assert _read(path)["phones"] == E164_WINNER, (
        "the E.164 spelling survives byte-identical; under first-seen-wins the "
        "`+`-less entry would have won instead"
    )

    # D4, through `_writeback_identifier`'s reuse branch, which routes
    # `person.phones` — the whole stored list — through `update_fields`.
    reuse_vault = vault / "reuse"
    reuse_vault.mkdir()
    reuse_repo = PersonRepository(reuse_vault)
    reuse = Person(name="Alice Example", phones=["447700900123"])
    reuse_path = reuse_repo.save(reuse)
    reuse_repo._writeback_identifier(reuse, phone="+44 7700 900123")
    assert _read(reuse_path)["phones"] == E164_WINNER

    # RULE 2 at arm granularity: TWO genuinely digit-less entries beside a real
    # one keep all three, byte-identical and in order. Two, because a SINGLE
    # empty key collides with nothing and the leg would be green under the very
    # build rule 2 forbids.
    digitless = ["n/a", "ext.", "+44 7700 900123"]
    kept = plant_note(vault, "@Kept", type="person", name="Kept")
    update_frontmatter_field(kept, "phones", list(digitless))
    assert _read(kept)["phones"] == digitless


def _check_the_two_negative_legs_at_arm_granularity(vault: Path):
    """A build reaching for `phones_match` or `Phone.parse` would do so ONCE
    inside the gate and change every arm at once, so the negatives ride here as
    well as at the unit."""
    vault.mkdir(parents=True)

    # RED under a key built on `phones_match`, whose UK arm reports these two as
    # one number — and which is not even transitive.
    uk = ["0790 0900123", "+44 7900 900123"]
    note = plant_note(vault, "@Uk", type="person", name="Uk")
    update_frontmatter_fields(note, {"phones": list(uk)})
    assert _read(note)["phones"] == uk, "two genuinely different numbers"

    # RED under a key routed through `Phone.parse`, which RAISES below
    # MIN_DIGITS = 7 rather than collapsing.
    short = ["12345", "1 2 3 4 5"]
    note = plant_note(vault, "@Short", type="person", name="Short")
    update_frontmatter_fields(note, {"phones": list(short)})
    assert _read(note)["phones"] == ["12345"], (
        "a short duplicate COMMITS as one entry rather than raising"
    )


def _check_the_undeclared_pass(vault: Path):
    """Untypedness never exempts an identifier write, and it never widens one."""
    vault.mkdir(parents=True)
    assert UNDECLARED_ARMS | UNDECLARED_EXCLUSION == DERIVED_SET
    assert UNDECLARED_EXCLUSION == {D1A, D4, D7, D8}

    # Identifiers WITHOUT a `name:` — rule (ii) speaks only to `name:`, so these
    # normalize exactly as the typed pass does.
    d1b = vault / "@u-d1b.md"
    write_markdown_file(d1b, frontmatter={"emails": list(BLOB_FORMS)})
    assert _read(d1b)["emails"] == COLLAPSED

    d1c = vault / "@u-d1c.md"
    write_markdown_file(d1c, extra_fields={"emails": list(BLOB_FORMS)})
    assert _read(d1c)["emails"] == COLLAPSED

    untyped_d5 = plant_note(vault, "@u-d5", name="Untyped")
    update_frontmatter_field(untyped_d5, "emails", list(BLOB_FORMS))
    assert _read(untyped_d5)["emails"] == COLLAPSED

    untyped_d6 = plant_note(vault, "@u-d6", name="Untyped")
    update_frontmatter_fields(untyped_d6, {"emails": list(BLOB_FORMS)})
    assert _read(untyped_d6)["emails"] == COLLAPSED

    # …while identifiers TOGETHER WITH a `name:` are refused under rule (ii),
    # exactly as the refusal criterion requires.
    target = vault / "@u-with-name.md"
    try:
        write_markdown_file(target, frontmatter={"name": "Alice Example",
                                                 "emails": list(BLOB_FORMS)})
    except NameGateRefusal as exc:
        assert exc.pattern == UNDECLARED_PATTERN
    else:
        raise AssertionError("an undeclared write introducing a name must refuse")
    assert not target.exists()


def _check_the_two_d8_cells_are_vacuous(vault: Path):
    """The emptiness is pinned from the RUN, never from a paragraph."""
    vault.mkdir(parents=True)
    dirty_lists = {
        "emails": ["Al B <A@B.com>"],
        "phones": list(DUPLICATE_PHONES),
        "aliases": ["x@y.com", "Zed"],
    }
    note = plant_note(vault, "@Dave Smith", type="person", name="Dave Smith",
                      auto_created="true", **dirty_lists)
    before = _read(note)
    assert before["emails"] == dirty_lists["emails"], "planted as stored-dirty"

    issue = lint_vault.LintIssue(
        file_path=note, check="field_type_mismatch",
        severity=lint_vault.Severity.WARNING, message="planted",
        category="completeness", auto_fixable=True)

    seen = []
    real_gate = lint_vault.gate_write

    def recording_gate(introduced, **kwargs):
        seen.append(dict(introduced))
        return real_gate(introduced, **kwargs)

    captured = io.StringIO()
    with patcher() as patch:
        patch.setattr(lint_vault, "gate_write", recording_gate)
        with redirect_stderr(captured):
            outcome = lint_vault.apply_fixes([issue], vault)

    assert outcome.refused == () and outcome.fixed == 1, captured.getvalue()

    # (1) The delta the gate ACTUALLY received, captured at the call.
    assert len(seen) == 1
    assert set(seen[0]) <= CLOSED_DELTA_KEY_SETS[D8], (
        f"D8's delta key set widened to {sorted(seen[0])}; the two vacuous "
        "cells of this criterion depend on it staying closed"
    )
    assert not (set(seen[0]) & IDENTIFIER_KEYS)

    # (2) …so all three stored lists commit BYTE-IDENTICAL through this arm.
    after = _read(note)
    for key, value in dirty_lists.items():
        assert after[key] == value, (
            f"{key} was rewritten at D8, which cannot happen while that arm's "
            "delta carries no identifier key"
        )
    assert after["auto_created"] is True, "the repair itself did commit"
