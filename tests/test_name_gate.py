"""WI-021 Tasks 3, 4 and 5 — the refusal leaf, the reified Tier-1 surface, and
the gate's own unit battery.

Three checks, one per task, each zero-arg and raising per the check contract.

**What lives here and what deliberately does not.** Task 3's message leg asserts
the HIERARCHY's bound on an exception THIS MODULE CONSTRUCTS, and is therefore
green under both raise-site defects — a `_refuse` with no `from` clause and a
`_refuse` handed `declared_type=`. That is stated rather than left implicit: the
raise-site's own chain and constructor legs live in Task 5's check, where a real
refusal is driven through `gate_write` and its build-produced artifacts (the
chain, the rendered traceback, the message) are read.

Nothing here reads syntax (no `ast`): that capability is single-homed in
`tests/derivations.py`.
"""

import re
import traceback
from pathlib import Path

import obsidian_schemas
import obsidian_schemas.name_gate as name_gate
from obsidian_schemas.errors import (
    REASONS,
    LoudFailError,
    NameGateRefusal,
    NoteParseError,
)
from obsidian_schemas.name_validation import (
    COMPANY_TIER1_BRANCHES,
    EMPTY_BRANCH,
    TIER1_BRANCHES,
    NameValidationError,
    NameValidator,
    _DOUBLE_SPACE_RE,
)
from obsidian_schemas.name_gate import (
    PERSON_TYPE,
    UNDECLARED_PATTERN,
    gate_write,
    split_address,
)
from obsidian_schemas.repositories.base import _skip_reason
from tests.support import temp_dir

REFUSAL_REASON = "the write introduces a name this package refuses"

# The seven DISTINCT keys nine chain branches raise, plus `empty`. Not derived
# from the table — that would be the table asserting itself — but written down
# from the pre-rewrite `if` chain, which is the thing the rewrite must preserve.
EXPECTED_PATTERNS = {
    "contains_email_chars",
    "rfc2822_leak",
    "calendar_prefix",
    "path_hostile_char",
    "archive_prefix",
    "unknown_contact",
    "pure_digit_name",
}

EXPECTED_BRANCH_IDS = (
    "email_chars", "rfc2822_leak", "arrow_connective", "calendar_prefix",
    "me_to_prefix", "path_hostile", "archive_prefix", "unknown_contact",
    "pure_digit", "empty",
)

# The pre-rewrite behaviour, written down. Each entry is (input, expected
# pattern or None, expected validate_strict output when it does not raise).
# Hand-derived from the `if` chain as it stood before Task 4 — including the two
# properties easiest to break in a table walk: `.search` vs `.match` differ per
# branch (a `calendar_prefix` in the MIDDLE of a name must NOT fire, an
# `unknown contact` in the middle MUST), and the RFC 2822 branch must match on
# ORIGINAL casing.
CHAIN_CORPUS = (
    ("Dave Smith", None, "Dave Smith"),
    ("Dave  Smith", None, "Dave Smith"),          # Tier 2, collapsed in-band
    ("  Dave Smith  ", None, "Dave Smith"),
    ("Maurizio", None, "Maurizio"),               # ends in 'io' — must NOT leak-match
    ("Francisco", None, "Francisco"),
    ("Patricio", None, "Patricio"),
    ("David Field", None, "David Field"),         # must NOT calendar-match
    ("Medea Smith", None, "Medea Smith"),
    ("O'Brien", None, "O'Brien"),
    ("dave@example.com", "contains_email_chars", None),
    ("Naomi Pavie naomipavieatspeechmaticscom", "rfc2822_leak", None),
    ("Dave -> Thomas Gatten", "calendar_prefix", None),
    ("Dave → Thomas Gatten", "calendar_prefix", None),   # unicode arrow (WI-117)
    ("Dave - Thomas Gatten", "calendar_prefix", None),
    ("Me to David Field", "calendar_prefix", None),
    ("Me to: David Field", "calendar_prefix", None),     # WI-111's colon form
    ("Smith - Dave Jones", None, "Smith - Dave Jones"),  # `.match`, not `.search`
    ("Bausch/Lomb", "path_hostile_char", None),
    ("zArchived Dave Smith", "archive_prefix", None),
    ("Dave zArchived", None, "Dave zArchived"),          # `.match`, not `.search`
    ("Unknown Contact Zeta-9", "unknown_contact", None),
    ("The unknown contact person", "unknown_contact", None),  # `.search`
    ("447700900123", "pure_digit_name", None),
    ("+447700900123", "pure_digit_name", None),
    ("", "empty", None),
    ("   ", "empty", None),
)


# ---------------------------------------------------------------------------
# Task 3 — the hierarchy leaf
# ---------------------------------------------------------------------------

def test_name_gate_refusal_is_a_loud_fail_leaf_carrying_a_pattern():
    """Task 3's verify. Zero-arg and raising, per the check contract."""
    # A leaf of LoudFailError DIRECTLY, never of NoteParseError: that subtree is
    # what the repository skip surface consumes, and the note here is perfectly
    # loadable — a WRITE was declined.
    assert issubclass(NameGateRefusal, LoudFailError)
    assert not issubclass(NameGateRefusal, NoteParseError)

    # No __init__ of its own — the hierarchy's ONE constructor is what bounds
    # the message, exactly as StaleEntityWrite and NoteAlreadyExists rely on.
    assert "__init__" not in NameGateRefusal.__dict__

    # REASONS is a FROZEN population, so equality is the right pin: fifteen
    # members before this item, sixteen after.
    assert REFUSAL_REASON in REASONS
    assert len(REASONS) == 16

    exc = NameGateRefusal(REFUSAL_REASON)
    assert exc.pattern is None, "`pattern` defaults to None until the gate sets it"
    assert NameGateRefusal.pattern is None

    try:
        NameGateRefusal("a reason nobody enumerated")
    except ValueError as rejected:
        assert not isinstance(rejected, LoudFailError), (
            "bounded_message's REASONS refusal is a bare ValueError, not a "
            "member of the hierarchy it guards"
        )
    else:
        raise AssertionError("a non-member reason must be refused at construction")

    # THE MESSAGE LEG, AND ITS SCOPE, DECLARED IN ONE LINE: this asserts the
    # hierarchy's bound on an exception THIS TEST constructs. It is green under
    # both raise-site defects M2 names (no `from` clause; a `declared_type=`
    # handed in for diagnostics) — those are driven through a REAL refusal in
    # Task 5's check, which is where they can fail.
    assert str(exc) == REFUSAL_REASON
    assert "path=" not in str(exc)
    assert "declared_type=" not in str(exc)
    assert "cause=" not in str(exc)

    # `_skip_reason`'s isinstance chain stays TOTAL with the new member, which
    # falls to the default rather than to a parse bucket.
    assert _skip_reason(exc) == "unreadable"

    # A consumer's `from obsidian_schemas import ...` keeps working.
    assert obsidian_schemas.NameGateRefusal is NameGateRefusal
    assert "NameGateRefusal" in obsidian_schemas.__all__


# ---------------------------------------------------------------------------
# Task 4 — the reified Tier-1 surface
# ---------------------------------------------------------------------------

def test_the_tier1_surface_is_reified_totally_and_the_chain_is_unchanged():
    """Task 4's verify. Zero-arg and raising, per the check contract."""
    _check_the_table_is_total_over_the_modules_branch_sites()
    _check_every_specimen_fires_its_own_branch_and_no_earlier_one()
    _check_the_sentinel_exemption_marks_exactly_one_record()
    _check_the_chain_behaves_exactly_as_it_did_before_the_rewrite()


def _check_the_table_is_total_over_the_modules_branch_sites():
    assert len(TIER1_BRANCHES) == 10, (
        "ten records: the nine chain branches plus `empty`. The unit is the "
        "BRANCH, not the raised key — a sweep keyed on the key yields seven "
        "fixtures and leaves two branches unexercised."
    )
    ids = tuple(record.branch_id for record in TIER1_BRANCHES)
    assert ids == EXPECTED_BRANCH_IDS, (
        "the table's ORDER is behaviour: the chain raises on the first match, "
        f"and more-specific patterns come first. Found: {ids}"
    )
    assert len(set(ids)) == len(ids), "branch_id must be unique in the table"

    keys = {record.pattern for record in TIER1_BRANCHES if record.branch_id != "empty"}
    assert keys == EXPECTED_PATTERNS, (
        "seven distinct keys over nine branches — the arrow, calendar and "
        f"'Me to' branches all raise calendar_prefix deliberately. Found: {keys}"
    )
    assert EMPTY_BRANCH.pattern == "empty" and EMPTY_BRANCH.regex is None
    assert EMPTY_BRANCH is TIER1_BRANCHES[-1]

    # COVERAGE, DERIVED rather than listed: every Tier-1 regex the module
    # compiles must be reached by exactly one record. A regex added without a
    # record is RED here, which is what "total over the module's branch sites"
    # has to mean if it is to survive the next pattern.
    #
    # WI-022 widened `tabled` to the union of BOTH tables. The module now
    # compiles a company-only regex (`_COMPANY_PATH_HOSTILE_RE`), so a
    # person-only census would be RED against correct code — and the honest
    # repair is to COVER the new member, never to narrow the census or rename
    # the constant so it dodges the `*_RE` suffix. The count follows: the person
    # table walks 9 distinct regexes, the company table adds exactly one the
    # person table does not carry (its other three are the SAME objects), so the
    # union is 10.
    import obsidian_schemas.name_validation as module
    compiled = {
        value for name, value in vars(module).items()
        if isinstance(value, re.Pattern) and name.endswith("_RE")
    }
    tier2 = {_DOUBLE_SPACE_RE}
    tabled = {record.regex
              for record in TIER1_BRANCHES + COMPANY_TIER1_BRANCHES
              if record.regex is not None}
    assert tabled == compiled - tier2, (
        "every Tier-1 regex in the module is walked by exactly one record of "
        "the person table or the company table. "
        f"Unrecorded: {compiled - tier2 - tabled}; recorded but not compiled "
        f"here: {tabled - compiled}"
    )
    assert len(tabled) == 10


def _check_every_specimen_fires_its_own_branch_and_no_earlier_one():
    for index, record in enumerate(TIER1_BRANCHES):
        firing = [other.branch_id for other in TIER1_BRANCHES
                  if other.matches(record.specimen)]
        assert firing, f"{record.branch_id}'s specimen fires no branch at all"
        assert firing[0] == record.branch_id, (
            f"{record.branch_id}'s specimen {record.specimen!r} is caught first "
            f"by {firing[0]!r} — the sweep would never exercise this branch"
        )
        # And the chain agrees with the table, which is what makes `specimen` an
        # input the refusal batteries can trust.
        if record.regex is not None:
            try:
                NameValidator().validate_strict(record.specimen)
            except NameValidationError as exc:
                assert exc.pattern == record.pattern
            else:
                raise AssertionError(
                    f"{record.branch_id}'s specimen was not refused by the chain"
                )
        assert index == TIER1_BRANCHES.index(record)


def _check_the_sentinel_exemption_marks_exactly_one_record():
    exempt = [r.branch_id for r in TIER1_BRANCHES if r.sentinel_exempt]
    assert exempt == ["pure_digit"], (
        f"the WI-083 exemption suppresses exactly one branch. Found: {exempt}"
    )
    # And it CANNOT swallow an empty name, which is why `empty` stays above the
    # chain: the pure-digit regex is `^\+?\d+$` and does not match "".
    validator = NameValidator()
    assert validator.validate_strict("447700900123",
                                     allow_phone_sentinel=True) == "447700900123"
    try:
        validator.validate_strict("", allow_phone_sentinel=True)
    except NameValidationError as exc:
        assert exc.pattern == "empty"
    else:
        raise AssertionError("the sentinel exemption must not swallow an empty name")
    try:
        validator.clean("   ", allow_phone_sentinel=True)
    except NameValidationError as exc:
        assert exc.pattern == "empty"
    else:
        raise AssertionError("clean() must refuse a whitespace-only name too")


def _check_the_chain_behaves_exactly_as_it_did_before_the_rewrite():
    validator = NameValidator()
    for name, expected_pattern, expected_output in CHAIN_CORPUS:
        for entry_point in (validator.validate_strict, validator.clean):
            try:
                result = entry_point(name)
            except NameValidationError as exc:
                assert expected_pattern is not None, (
                    f"{name!r} was refused ({exc.pattern}) and used to pass"
                )
                assert exc.pattern == expected_pattern, (
                    f"{name!r}: expected {expected_pattern}, got {exc.pattern}"
                )
                assert type(exc) is NameValidationError
                if name.strip():
                    assert repr(name.strip()) in str(exc) or repr(name) in str(exc), (
                        "each branch's own message is preserved verbatim"
                    )
            else:
                assert expected_pattern is None, (
                    f"{name!r} should have been refused with {expected_pattern}"
                )
                produced = (result if isinstance(result, str)
                            else result.cleaned_name)
                assert produced == expected_output, (
                    f"{name!r}: expected {expected_output!r}, got {produced!r}"
                )


# ---------------------------------------------------------------------------
# Task 5 — the gate itself
# ---------------------------------------------------------------------------

def test_the_gate_is_a_pure_function_of_payload_and_declaration():
    """Task 5's verify. Zero-arg and raising, per the check contract."""
    with temp_dir() as scratch:
        _check_the_gate_touches_no_filesystem(scratch)
    _check_the_key_set_and_the_declaration_rules()
    _check_the_name_is_an_identity()
    _check_the_four_phone_rules()
    _check_the_list_shape_precondition()
    _check_idempotence()
    _check_the_raise_site()
    _check_the_module_opens_no_output_channel()


def _check_the_gate_touches_no_filesystem(scratch: Path):
    # A `PersonRepository`-free tmp path: the gate is handed payloads and never
    # a path, so if it consulted the filesystem at all it could only do so by
    # globbing somewhere — and nothing may appear here.
    before = sorted(scratch.iterdir())
    payloads = (
        {"name": "Dave Smith", "type": "person"},
        {"name": "Dave  Smith", "emails": ["Al B <A@B.com>"], "aliases": ["Zed"]},
        {"emails": ["a@b.com"], "phones": ["+44 7700 900123"], "aliases": []},
    )
    for payload in payloads:
        gate_write(payload, declared_type=PERSON_TYPE, whole_record=True)
        gate_write(payload, declared_type=PERSON_TYPE, whole_record=False)
    assert sorted(scratch.iterdir()) == before == [], (
        "the gate reads only its own arguments — never the filesystem, no glob, "
        "no path shape, no sibling note. That is what makes the D1 hoist legal."
    )


def _check_the_key_set_and_the_declaration_rules():
    # The output's key set is EXACTLY the input's. Forced, not stylistic:
    # update_fields merges by key REPLACEMENT, so an emitted destination key
    # would overwrite that field's stored list rather than append to it.
    for whole_record in (True, False):
        payload = {"name": "Dave Smith", "emails": ["a@b.com"], "company": "Acme"}
        out = gate_write(payload, declared_type=PERSON_TYPE,
                         whole_record=whole_record)
        assert set(out) == set(payload)
        assert out is not payload, "a NEW dict, never the caller's own"
        assert out["company"] == "Acme", "a field with no rule is carried through"

    # Rule (ii) — an undeclared write that introduces a `name:` is refused
    # outright, whatever the name.
    for clean_name in ("Alice Example", "Dave Smith"):
        payload = {"name": clean_name}
        try:
            gate_write(payload, declared_type=None, whole_record=False)
        except NameGateRefusal as exc:
            assert exc.pattern == UNDECLARED_PATTERN
        else:
            raise AssertionError("an undeclared name write must be refused")

    # …and it precedes every pattern evaluation, so no person-derived Tier-1
    # pattern ever judges an undeclared write.
    dirty = {"name": "Bausch/Lomb"}
    try:
        gate_write(dirty, declared_type=None, whole_record=False)
    except NameGateRefusal as exc:
        assert exc.pattern == UNDECLARED_PATTERN, (
            "rule (ii) is evaluated FIRST — a Tier-1 key here means the "
            "undeclared branch runs too late"
        )

    # A DECLARED non-person type passes through untouched — demonstrated on
    # `book`, which the gate's own docstring names ("a Book write is gated and
    # handed straight back") and which no table judges.
    #
    # WI-022 moved this fixture off `company`. It used to be spelled with
    # `{"type": "company", "name": "Bausch/Lomb"}`, and `/` is now a member of
    # `_COMPANY_PATH_HOSTILE_RE` — so that payload is REFUSED, which is the item
    # rather than a regression. The pass-through claim this leg makes is about
    # the types the gate holds NO judgement for, and `book` is one; the company
    # arm's own pass-through (a delta that introduces no `name:`) is asserted in
    # `tests/test_company_name_contract.py`.
    book = {"name": "Bausch/Lomb", "emails": ["Al B <A@B.com>"], "type": "book"}
    assert gate_write(book, declared_type="book", whole_record=True) == book

    # THE `is not None` HALF, which is the one place this branch could be
    # written half a line shorter and be wrong: an UNDECLARED write introducing
    # identifiers but NO `name:` falls THROUGH and normalizes exactly as a
    # declared one, because rule (ii) speaks only to `name:`.
    identifiers_only = {"emails": ["Al B <A@B.com>"]}
    assert gate_write(identifiers_only, declared_type=None,
                      whole_record=False) == {"emails": ["a@b.com"]}


def _check_the_name_is_an_identity():
    # Tier-2 dirt survives byte-for-byte. RED for a build that reaches for
    # NameValidator.clean or for validate_strict's RETURN value: the filename is
    # bound from the raw name one frame above every gate call, so a repaired
    # name here writes `name: Dave Smith` into `@Dave  Smith.md`.
    for dirty in ("Dave  Smith", "  Dave Smith  ", "Dave   van  Smith"):
        payload = {"name": dirty}
        out = gate_write(payload, declared_type=PERSON_TYPE, whole_record=False)
        assert out["name"] == dirty, (
            f"the gate must emit {dirty!r} byte-for-byte, not "
            f"{out['name']!r} — Tier-2 repair belongs above the filename "
            "derivation, in create_stub, and nowhere else"
        )

    # The sentinel exemption is derived from the PAYLOAD, never from a new
    # parameter — the same expression create_stub computes.
    exempt = {"name": "447700900123", "phones": ["+447700900123"]}
    assert gate_write(exempt, declared_type=PERSON_TYPE,
                      whole_record=False)["name"] == "447700900123"
    unexempt = {"name": "447700900123", "phones": []}
    try:
        gate_write(unexempt, declared_type=PERSON_TYPE, whole_record=False)
    except NameGateRefusal as exc:
        assert exc.pattern == "pure_digit_name"
    else:
        raise AssertionError("a pure-digit name with no phone must be refused")

    # `None` is the `empty` refusal, not the string "None".
    for null_name in (None, "", "   "):
        payload = {"name": null_name}
        try:
            gate_write(payload, declared_type=PERSON_TYPE, whole_record=False)
        except NameGateRefusal as exc:
            assert exc.pattern == "empty"
        else:
            raise AssertionError(f"{null_name!r} must be refused as empty")


def _check_the_four_phone_rules():
    """Design §5's four rules at unit granularity.

    Every leg pins the WHOLE output list, in order, byte-for-byte — never a
    property (a count, "keeps all three", "collapses to one") that the wrong
    build also satisfies — and every leg names the wrong build it is RED
    against. The four wrong builds:

      (N) a naive seen-set keyed on normalize_phone's output with no empty-key
          exception;
      (F) first-seen as the winner;
      (M) the key routed through Phone.parse, which RAISES below MIN_DIGITS = 7;
      (P) the key built on phones_match, whose UK arm reports 07900900123 and
          447900900123 as one number and which is not even transitive.
    """
    legs = (
        # rule 3 — E.164 wins. RED under (F), which keeps "447700900123".
        (["447700900123", "+44 7700 900123"], ["+44 7700 900123"]),
        # rule 3's ORDER-INDEPENDENCE. RED under prefer-the-later and
        # prefer-the-`+`-less; GREEN under (F), so it is declared as the second
        # half of a PAIR with the leg above rather than as rule 3's own
        # discriminator.
        (["+44 7700 900123", "447700900123"], ["+44 7700 900123"]),
        # rule 3's FALLBACK — neither display form starts with "+", so the first
        # in source order wins. RED under a build that drops such a group,
        # raises on it, or synthesizes a "+".
        (["447700900123", "44 7700 900123"], ["447700900123"]),
        # rule 4's POSITION clause, and the only non-vacuous leg for it: every
        # other group collapses to a one-element output where every position
        # rule agrees. RED under a build storing the survivor at its OWN index
        # or appending survivors after the singletons — both of which return
        # ["0161 496 0000", "+44 7700 900123"].
        (["447700900123", "0161 496 0000", "+44 7700 900123"],
         ["+44 7700 900123", "0161 496 0000"]),
        # rule 2 — TWO genuinely digit-less entries, because a SINGLE empty key
        # collides with nothing and the leg would be green under the very build
        # the rule forbids. RED under (N), which keys both on "" and drops the
        # second.
        (["n/a", "ext.", "+44 7700 900123"], ["n/a", "ext.", "+44 7700 900123"]),
        # rule 1 — three distinct SHORT keys 4021/77/447700900123 are not
        # collapsed. RED under (M), where Phone.parse raises IdentifierError on
        # the four-digit and the two-digit entry.
        (["ext. 4021", "x77", "+44 7700 900123"],
         ["ext. 4021", "x77", "+44 7700 900123"]),
        # rule 1 — RED under (P), whose UK arm reports these as one number.
        (["0790 0900123", "+44 7900 900123"], ["0790 0900123", "+44 7900 900123"]),
        # rule 1 — RED under (M), which raises on a five-digit entry instead of
        # collapsing. The survivor is PINNED rather than left as "collapses to
        # one" because no member carries a "+" and rule 3's fallback names it.
        (["12345", "1 2 3 4 5"], ["12345"]),
    )
    for stored, expected in legs:
        payload = {"phones": list(stored)}
        out = gate_write(payload, declared_type=PERSON_TYPE, whole_record=False)
        assert out["phones"] == expected, (
            f"{stored!r} must dedupe to exactly {expected!r}, got {out['phones']!r}"
        )
        # rule 4's second half: feeding the output straight back is a no-op,
        # which is idempotence at this rule.
        again = gate_write({"phones": out["phones"]}, declared_type=PERSON_TYPE,
                           whole_record=False)
        assert again["phones"] == expected

    # The two NEGATIVES, asserted as ABSENCES of a CAPABILITY rather than only
    # through their behavioural legs above, so an edit reaching for either
    # helper is visible even before it changes an answer.
    #
    # Read off the module's NAMESPACE, not its source text. A text scan is the
    # self-match trap errors.py already documents: the gate's own docstrings
    # explain why these two are excluded, and naming the excluded symbol in the
    # explanation would make a compliant module read as a violation. The
    # namespace is exact — `Phone.parse` and `MIN_DIGITS` are unreachable
    # without binding `Phone`, and `phones_match` without binding its name.
    bound = set(vars(name_gate))
    assert "phones_match" not in bound, (
        "phones_match's country-code equivalence is WI-023 item 2's question, "
        "not this item's, and it is not transitive — not a relation a seen-set "
        "can be built on"
    )
    assert "Phone" not in bound and "MIN_DIGITS" not in bound, (
        "Phone.parse's MIN_DIGITS floor is never introduced into the dedupe "
        "path: it would make a short entry unkeyable by RAISING"
    )
    assert name_gate.normalize_phone.__module__ == (
        "obsidian_schemas.phone_normalization"
    ), "the key is normalize_phone's output and nothing else"


def _check_the_list_shape_precondition():
    """Design §1.4, whose wrong build is "iterate the value as a list of
    entries" — which turns a scalar into sixteen single-character entries and a
    YAML `emails:` with no value into a TypeError on a write that succeeds
    today. Each leg pins the WHOLE returned dict."""
    # The live shape: update_frontmatter_field(note, "phones", "+44 7700 900123")
    # constructs exactly this delta today.
    scalar = {"phones": "+44 7700 900123"}
    out = gate_write(scalar, declared_type=PERSON_TYPE, whole_record=False)
    assert out == {"phones": "+44 7700 900123"}
    assert out["phones"] is scalar["phones"], "the same object, never a repaired one"

    # A YAML `emails:` with no value parses to None. The leg asserts the RETURN
    # rather than pytest.raises(TypeError) for the same reason AC-4 mandates
    # pass-through: a write that succeeds today must still succeed.
    nulled = {"emails": None}
    assert gate_write(nulled, declared_type=PERSON_TYPE,
                      whole_record=False) == {"emails": None}

    # One non-`str` member disqualifies the WHOLE value — RED under a build
    # testing only isinstance(value, list).
    mixed = {"phones": ["+44 7700 900123", 447700900123]}
    out = gate_write(mixed, declared_type=PERSON_TYPE, whole_record=False)
    assert out == {"phones": ["+44 7700 900123", 447700900123]}
    assert out["phones"] is mixed["phones"]

    # A dict, an int and a bare str all take the same arm without being
    # enumerated — the predicate is POSITIVE.
    for odd in ({"a": 1}, 7, "solo", (), set()):
        payload = {"aliases": odd}
        assert gate_write(payload, declared_type=PERSON_TYPE,
                          whole_record=True) == {"aliases": odd}

    # PER-KEY, not a whole-payload bail-out — and both migrations are suppressed
    # when either end of their pair fails.
    pair = {"emails": ["Al B <A@B.com>"], "aliases": "Al B"}
    out = gate_write(pair, declared_type=PERSON_TYPE, whole_record=True)
    assert out == {"emails": ["a@b.com"], "aliases": "Al B"}, (
        "emails normalizes beside an untouched scalar aliases; M2 has no "
        "destination it may write, so the display half is dropped rather than "
        "migrated"
    )


def _check_idempotence():
    records = (
        ({"name": "Dave  Smith", "emails": ["Al B <A@B.com>", "a@b.com"],
          "aliases": ["x@y.com", "Zed"], "phones": ["447700900123",
                                                    "+44 7700 900123"]}, True),
        ({"emails": ["Al B (A@B.com)"], "aliases": ["Al B"], "phones": []}, True),
        ({"emails": ["Al B <A@B.com>"], "phones": ["n/a", "n/a"]}, False),
        ({"name": "Dave Smith"}, False),
    )
    for payload, whole_record in records:
        once = gate_write(payload, declared_type=PERSON_TYPE,
                          whole_record=whole_record)
        twice = gate_write(once, declared_type=PERSON_TYPE,
                           whole_record=whole_record)
        assert twice == once, (
            f"gate(gate(x)) != gate(x) for {payload!r}: {twice!r} vs {once!r}. "
            "One PersonRepository.save invokes the gate twice."
        )

    # The two migrations, pinned exactly rather than by a property.
    whole = {"name": "Dave Smith", "emails": ["Al B <A@B.com>"],
             "aliases": ["x@y.com", "Zed"], "phones": []}
    out = gate_write(whole, declared_type=PERSON_TYPE, whole_record=True)
    assert out == {
        "name": "Dave Smith",
        "emails": ["a@b.com", "x@y.com"],      # M1: the alias moved here
        "aliases": ["Zed", "Al B"],            # M2: the display half moved here
        "phones": [],
    }
    # …and on a DICT-shaped arm neither runs: aliases is byte-identical and the
    # emails display half is DELETED with no destination.
    out = gate_write(whole, declared_type=PERSON_TYPE, whole_record=False)
    assert out == {
        "name": "Dave Smith",
        "emails": ["a@b.com"],
        "aliases": ["x@y.com", "Zed"],
        "phones": [],
    }
    assert out["aliases"] is whole["aliases"], "byte-identical means the same object"


def _check_the_raise_site():
    """Design §2's two raise-site rules, driven through a REAL refusal.

    Task 3's message leg is green under both wrong builds this discriminates:
    a `_refuse` reached from inside the `except` with no `from` clause, and a
    `_refuse` handed `declared_type=` so an operator can see which type declared
    the write. Neither is caught by asserting a property on an exception the
    TEST constructs.

    The payload is bound to a VARIABLE rather than inlined into the call, and
    that is load-bearing: `format_exception` renders the caller's own source
    line, so an inlined specimen would appear in the rendering from the test's
    frame and the oracle would be red against a correct build.
    """
    subjects = [(record.pattern, record.specimen) for record in TIER1_BRANCHES]
    subjects.append((UNDECLARED_PATTERN, "Alice Example"))

    for expected_pattern, specimen in subjects:
        undeclared = expected_pattern == UNDECLARED_PATTERN
        payload = {"name": specimen, "type": PERSON_TYPE}
        try:
            gate_write(payload,
                       declared_type=None if undeclared else PERSON_TYPE,
                       whole_record=False)
        except NameGateRefusal as exc:
            assert exc.pattern == expected_pattern
            assert exc.__cause__ is None, (
                "chainable_cause returns None for a NameValidationError, and "
                "the `from` clause is what empties __cause__"
            )
            assert exc.__suppress_context__ is True, (
                "a `from` clause being PRESENT is what sets this — RED under a "
                "_refuse reached from inside the except with no `from` at all"
            )
            # NOT `exc.__context__ is None`: implicit chaining always happens,
            # so that is non-None on the correct build and an oracle written
            # that way is RED against correct code.
            rendered = "".join(traceback.format_exception(exc))
            assert "During handling of the above exception" not in rendered
            assert str(exc) == REFUSAL_REASON
            assert PERSON_TYPE not in str(exc), (
                "RED under a _refuse handed declared_type=, which "
                "bounded_message renders into the message"
            )
            if specimen.strip():
                # Skipped for the `empty` record alone: "" is a substring of
                # every string, so the absence oracle is unstateable there.
                assert specimen not in rendered, (
                    f"the refused name {specimen!r} reached the rendered "
                    "traceback — NameValidationError interpolates the RAW NAME "
                    "at every branch site, and for the email-shaped branches "
                    "that name IS an address"
                )
                assert specimen not in str(exc)
        else:
            raise AssertionError(f"{specimen!r} must be refused")


def _check_the_module_opens_no_output_channel():
    """§2's "no note content reaches a log line", made a statement about a
    channel the module does not open rather than an unchecked hope.

    Read off `name_gate.py`'s own source text. Its prose must therefore avoid
    these tokens — the same convention `errors.py` already carries for the
    close-out sweeps, and exact by construction rather than by a reader's eye.
    """
    source = Path(name_gate.__file__).read_text(encoding="utf-8")
    for token in ("logging", "logger", "print("):
        assert token not in source, (
            f"name_gate.py names {token!r}: the gate opens no output channel of "
            "its own, which is what bounds the note-content question to the "
            "exception it raises"
        )


# ---------------------------------------------------------------------------
# The splitter's own unit legs (Design §4) — AC-5's battery is Task 15's
# ---------------------------------------------------------------------------

def test_the_address_splitter_is_total_and_returns_the_normalized_address():
    """Not an AC check — the splitter's total-ness at unit granularity."""
    assert split_address("Al B <A@B.com>") == ("a@b.com", "Al B")
    assert split_address("Al B (A@B.com)") == ("a@b.com", "Al B")
    assert split_address("A@B.com") == ("a@b.com", "")
    assert split_address("<a@b.com>") == ("a@b.com", "")
    assert split_address("Zed") == (None, "")
    assert split_address("") == (None, "")
    assert split_address(None) == (None, "")
    assert split_address(447700900123) == (None, "")
    # The angle-bracket gate is NOT widened: parseaddr silently repairs a bare
    # "a@b c.com" into "a@bc.com", minting a wrong identity key, and this
    # refuses it instead.
    assert split_address("a@b c.com") == (None, "")
    assert split_address("a@b@c.com") == (None, "")
    assert split_address("a@localhost") == (None, "")
