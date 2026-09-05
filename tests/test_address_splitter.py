"""WI-021 — AC-5: address splitting is single-homed and agrees with Email.parse.

**The property that matters is no SECOND AUTHORITY for one job.** The mint's
consolidation rider claimed RFC 2822 parsing lived in "≥4 sites"; read against
the tree those four sites did THREE different jobs and only two were duplicates.
`Email.parse` is the authority and stays. `_RFC2822_LEAK_RE` is a DETECTOR, not
a parser — it finds an address that lost its punctuation, which has no `@` and
nothing parseaddr could see — and it stays too. The two duplicates were
`create_stub`'s parseaddr and `_normalize_address_fields`' inner
`_extract_email_and_name`; both are deleted and both now route through the one
splitter.

**The sweep is keyed on the JOB SHAPE, never on the `parseaddr` symbol.** That
is not fastidiousness: the rider's own table was assembled by grepping for
`parseaddr`, so it is a LOWER BOUND on the duplication. A hand-rolled splitter —
`raw.split("<")`, a bare regex on `Name <addr>` — does the identical job and no
symbol grep can see it, and `_extract_email_and_name` was already half that
shape, reaching for a parens REGEX before it ever reached parseaddr. So the
positive controls are planted in each implementation shape and driven through
the wall's OWN predicate.

**Why `Email.parse` itself is not a member of the sweep**, stated so the
exclusion is a derived fact rather than a hand-wave: it returns a typed `Email`,
not a `(address, display)` pair, so the job-shape predicate does not resolve it.
It is the AUTHORITY the one splitter delegates to, which this module asserts
directly.

Nothing here reads syntax (no `ast`): that capability is single-homed in
`tests/derivations.py`.
"""

# FIRST, ahead of every package import: the conveyor may run this module's check
# under an interpreter that is not this project's, where the imports below cannot
# resolve. A no-op under the floor command and under CI (WI-021; see
# `tests/ac_interpreter.py` for the failure this closes).
from tests.ac_interpreter import ensure_project_interpreter

ensure_project_interpreter(__file__)

from pathlib import Path  # noqa: E402 — below runs once the interpreter is right

from obsidian_schemas.identifier import Email, IdentifierError
from obsidian_schemas.name_gate import split_address
from tests.derivations import (
    PACKAGE_ROOT,
    SCRIPTS_ROOT,
    FunctionId,
    address_splitting_implementations,
    module_id,
    python_files_under,
)
from tests.support import temp_dir
from tests.test_name_gate_wall import PLANT_SPLITTER_SHAPES, _single_sourced

THE_ONE_HOME = FunctionId("obsidian_schemas/name_gate.py", "split_address")

# Every input form the two DELETED sites accepted. The agreement clause is over
# this set, and the parens form is in it explicitly because `Email.parse` does
# not accept that form — the splitter owns it BEFORE delegating, which fixes
# which STRINGS reach the authority, not which of them it accepts.
ACCEPTED_FORMS = (
    ("a@b.com", "a@b.com", ""),
    ("A@B.com", "a@b.com", ""),
    ("Al B <a@b.com>", "a@b.com", "Al B"),
    ("Al B <A@B.com>", "a@b.com", "Al B"),
    ("<a@b.com>", "a@b.com", ""),
    ("Al B (a@b.com)", "a@b.com", "Al B"),
    ("Al B (A@B.com)", "a@b.com", "Al B"),
    ("Al.B@Example.COM", "al.b@example.com", ""),
    ("Al B <Al.B@Example.COM>", "al.b@example.com", "Al B"),
)

# The five "stops normalizing" classes: forms the LAXER deleted sites accepted
# and the authority deliberately refuses. Adopting the authority is SUPPOSED to
# change these — the point is that it is stated rather than shipped as a
# refactor.
NEWLY_REFUSED = (
    "a@b c.com",        # internal whitespace — parseaddr would silently repair
    "a@b@c.com",        # more than one `@`
    "a.b@localhost",    # a dot, but not in the domain
    "@b.com",           # empty local
    "Jane (a@localhost)",   # the parens form with a dotless domain
)


def test_address_splitting_is_single_homed_and_agrees_with_email_parse():
    """AC-5's check. Zero-arg and raising, per the check contract."""
    _single_sourced(address_splitting_implementations, python_files_under)

    # THE LIVE CLAIM FIRST, before anything is planted.
    _check_exactly_one_implementation_survives()

    with temp_dir() as scratch:
        _check_the_planted_positive_controls_and_the_near_miss(scratch)

    _check_the_agreement_clause_and_the_case_contract()
    _check_the_authority_is_not_widened()


def _check_exactly_one_implementation_survives():
    found = address_splitting_implementations(
        python_files_under(PACKAGE_ROOT, SCRIPTS_ROOT))
    assert found == {THE_ONE_HOME}, (
        "exactly ONE implementation of the job may exist, homed in the gate. "
        f"Found: {sorted(found)}"
    )

    # `Email.parse` is the permitted AUTHORITY, and the splitter delegates to
    # it rather than re-deriving an address — asserted, because "one
    # implementation" and "built on the authority" are two different claims and
    # a splitter that rolled its own parse would satisfy the first alone.
    source = Path(
        PACKAGE_ROOT / "name_gate.py").read_text(encoding="utf-8")
    assert "Email.parse(" in source, (
        "the splitter must delegate to identifier.Email.parse, which stays the "
        "one address authority"
    )


def _check_the_planted_positive_controls_and_the_near_miss(scratch: Path):
    """Driven through the wall's OWN predicate, never a re-implementation."""
    path = scratch / "splitter_shapes.py"
    path.write_text(PLANT_SPLITTER_SHAPES, encoding="utf-8")
    module = module_id(path)

    found = {fid.qualname for fid in address_splitting_implementations([path])
             if fid.module == module}

    # One control per implementation SHAPE, because a sweep keyed on the symbol
    # sees only the first of the three.
    assert "splits_with_parseaddr" in found, "the email.utils shape"
    assert "splits_with_a_hand_rolled_regex" in found, (
        "the hand-rolled-regex shape — the one no `parseaddr` grep can see, and "
        "the one the deleted `_extract_email_and_name` already was half of"
    )
    assert "splits_on_a_bare_literal" in found, "the bare `raw.partition('<')` shape"

    # THE NEAR-MISSES, which are what stop the sweep passing by matching
    # everything: a differently-shaped return, and a pair with no address work.
    assert "returns_a_triple_not_a_pair" not in found
    assert "returns_a_pair_with_no_address_work" not in found
    assert found == {"splits_with_parseaddr", "splits_with_a_hand_rolled_regex",
                     "splits_on_a_bare_literal"}


def _check_the_agreement_clause_and_the_case_contract():
    """The surviving implementation agrees with `Email.parse` on every input
    form the deleted sites accepted, the parens form included."""
    for raw, expected_address, expected_display in ACCEPTED_FORMS:
        address, display = split_address(raw)
        assert address == expected_address, (
            f"{raw!r}: expected {expected_address!r}, got {address!r}"
        )
        assert display == expected_display, (
            f"{raw!r}: expected display {expected_display!r}, got {display!r}"
        )
        # AGREEMENT, asserted against the authority itself rather than against a
        # re-spelling of its output.
        assert address == Email.parse(expected_address).value

    # THE CASE CONTRACT, asserted explicitly because the two answers write
    # different bytes into every stored entry. The splitter returns
    # `Email.parse(...).value` — the lower-cased normalized address — and never
    # the raw slice: `Email.value` is the identity key the engine dedupes on, so
    # storing a raw-cased slice while deduping on the lowered one is the
    # corruption class this item exists to close, in miniature.
    address, display = split_address("Al B <Al.B@Example.COM>")
    assert address == "al.b@example.com", (
        "RED for a build returning the raw matched slice, which leaves the "
        "stored form and the identity key disagreeing"
    )
    assert address == Email.parse("Al.B@Example.COM").value
    assert display == "Al B", "the display half keeps its own casing"


def _check_the_authority_is_not_widened():
    """The five classes the laxer deleted sites accepted and the authority
    refuses. TOTAL: the splitter maps `IdentifierError` to "not an address" and
    raises nothing, so a caller keeps the entry verbatim rather than losing it."""
    for raw in NEWLY_REFUSED:
        assert split_address(raw) == (None, ""), (
            f"{raw!r} must map to 'not an address' rather than being repaired "
            "into a wrong identity key"
        )
        # …and the authority itself agrees, which is what makes this an
        # inherited refusal rather than a second opinion.
        candidate = raw
        if raw.startswith("Jane ("):
            candidate = "a@localhost"
        try:
            Email.parse(candidate)
        except IdentifierError:
            pass
        else:
            raise AssertionError(f"{candidate!r} was expected to be refused")

    # TOTAL — every input returns, nothing raises.
    for odd in (None, "", "   ", 447700900123, [], {}, "Zed"):
        assert split_address(odd) == (None, "")
