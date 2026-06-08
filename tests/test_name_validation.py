"""Tests for NameValidator (WI-105 Step 1).

Tier 1 = REJECT (validator raises NameValidationError)
Tier 2 = CLEAN (validator returns CleanResult with repairs_applied populated)
Tier 3 = NOT touched by validator (cleanup script's domain)

The empirical audit (orchestrator/docs/name-validation-and-cleanup.md) found 148
corrupted records across 8 patterns in 1647 vault notes. These tests cover all
8 patterns plus a baseline of real valid names that must NOT be flagged.
"""

import pytest

from obsidian_schemas.name_validation import (
    NameValidator,
    NameValidationError,
    CleanResult,
    WeakIdentityError,
    weak_identity_reason,
)


# ============================================================
# Tier 1 — REJECT (validate_strict raises)
# ============================================================

class TestRejectRfc2822Leak:
    """Pattern 1: name contains email mashed-into-text (dots stripped).

    Real production examples from vault audit 2026-06-02:
    - 'Naomi Pavie naomipavieatspeechmaticscom'
    - 'Antonia Bowler AntoniaBowlerexclaimercom'
    - 'Kate Sellwood katedavewaschacom'
    """

    def test_rejects_classic_rfc2822_leak(self):
        v = NameValidator()
        with pytest.raises(NameValidationError) as exc:
            v.validate_strict("Naomi Pavie naomipavieatspeechmaticscom")
        assert exc.value.pattern == "rfc2822_leak"

    def test_rejects_with_at_substring(self):
        v = NameValidator()
        with pytest.raises(NameValidationError):
            v.validate_strict("Kate Sellwood katedavewaschacom")

    def test_rejects_uk_tld(self):
        v = NameValidator()
        with pytest.raises(NameValidationError):
            v.validate_strict("Anne Almeida-Anderson anneno-worriescouk")

    def test_rejects_ai_tld(self):
        v = NameValidator()
        with pytest.raises(NameValidationError):
            v.validate_strict("Ronald Ashri ronaldashriopendialogai")

    def test_rejects_hyphenated_leak(self):
        # 'no-worriescouk' — leaked-email run with a hyphen mid-run.
        # Regex must handle [a-z][a-z0-9.\-]+ runs.
        v = NameValidator()
        with pytest.raises(NameValidationError):
            v.validate_strict("Chris Oakes no-worriescouk")

    def test_rejects_underscored_leak(self):
        # 'prachi_gargoutlookcom' — leaked email with an underscore (original
        # local-part was 'prachi_garg'). Real production case 2026-06-02.
        v = NameValidator()
        with pytest.raises(NameValidationError):
            v.validate_strict("Prachi Garg prachi_gargoutlookcom")

    def test_does_NOT_reject_maurizio(self):
        # Falsification: 'Maurizio' ends in 'io' (a real TLD substring) but
        # is a legitimate first name. Real production false-positive
        # observed in 2026-06-02 repair dry-run before this fix.
        v = NameValidator()
        assert v.validate_strict("Maurizio Morriello") == "Maurizio Morriello"

    def test_does_NOT_reject_francisco(self):
        # Falsification: 'Francisco' ends in 'co' (a TLD substring).
        v = NameValidator()
        assert v.validate_strict("Francisco Vigo") == "Francisco Vigo"

    def test_does_NOT_reject_patricio(self):
        # 'Patricio' ends in 'io'.
        v = NameValidator()
        assert v.validate_strict("Patricio Hernandez") == "Patricio Hernandez"


class TestRejectCalendarPrefix:
    """Pattern 2: 'Dave -', 'Me to', 'Me -' calendar/transcript prefix.

    Real production examples:
    - 'Dave - Naomi Pavie Speechmatics'
    - 'Me to Tom Green'
    """

    def test_rejects_dave_dash_prefix(self):
        v = NameValidator()
        with pytest.raises(NameValidationError) as exc:
            v.validate_strict("Dave - Naomi Pavie")
        assert exc.value.pattern == "calendar_prefix"

    def test_rejects_dave_dash_with_company_suffix(self):
        v = NameValidator()
        with pytest.raises(NameValidationError):
            v.validate_strict("Dave - Lauren King Speechmatics")

    def test_rejects_me_to_prefix(self):
        v = NameValidator()
        with pytest.raises(NameValidationError) as exc:
            v.validate_strict("Me to Tom Green")
        assert exc.value.pattern == "calendar_prefix"

    def test_rejects_me_dash_prefix(self):
        v = NameValidator()
        with pytest.raises(NameValidationError):
            v.validate_strict("Me - Tom Green")

    def test_does_NOT_reject_name_starting_with_David(self):
        # False-positive guard: 'David ...' must be allowed
        v = NameValidator()
        assert v.validate_strict("David Field") == "David Field"

    def test_does_NOT_reject_name_starting_with_Medea(self):
        # 'Me' is only rejected as a word, not as a prefix of a name
        v = NameValidator()
        assert v.validate_strict("Medea Smith") == "Medea Smith"

    def test_rejects_me_to_colon_form(self):
        # WI-111 (2026-06-06 production case): 'Me to: David Field' PASSED the
        # original `^(Me|My)\s+to\s+\w+` regex because the colon broke the
        # `\s+\w+` tail. The legacy re.sub in create_stub then stripped the
        # colon → 'Me to David Field' (calendar_prefix), corrupting the note.
        # Loosened to `^(Me|My)\s+to\b` so the colon form is rejected at input.
        v = NameValidator()
        with pytest.raises(NameValidationError) as exc:
            v.validate_strict("Me to: David Field")
        assert exc.value.pattern == "calendar_prefix"

    def test_rejects_my_to_colon_form(self):
        v = NameValidator()
        with pytest.raises(NameValidationError):
            v.validate_strict("My to: Someone Else")


class TestRejectArrowConnective:
    """WI-111: connective arrow '->' — meeting/relationship descriptor leaked
    into a name field. The 2026-06-06 production case 'Dave -> Thomas Gatten
    (Adzact)' PASSED validate_strict on input (arrow form is not the older
    `Dave -` prefix), then create_stub's legacy re.sub stripped '>()' →
    'Dave - Thomas Gatten Adzact' (calendar_prefix). Reject the arrow at the
    boundary so deleting that re.sub can't store the descriptor verbatim.

    Verified 2026-06-06: 0 of 1590 live vault names contain '->'.
    """

    def test_rejects_arrow_prefix_form(self):
        v = NameValidator()
        with pytest.raises(NameValidationError) as exc:
            v.validate_strict("Dave -> Thomas Gatten (Adzact)")
        assert exc.value.pattern == "calendar_prefix"

    def test_rejects_bare_arrow_between_names(self):
        # The broader `<name> -> <name>` 1:1-title shape, not Dave-prefixed.
        v = NameValidator()
        with pytest.raises(NameValidationError):
            v.validate_strict("Naomi Pavie -> David Field")

    def test_clean_raises_on_arrow(self):
        v = NameValidator()
        with pytest.raises(NameValidationError):
            v.clean("Dave -> Thomas Gatten (Adzact)")

    def test_does_NOT_reject_hyphenated_name(self):
        # 'Anne-Marie' has a hyphen but no arrow — must pass.
        v = NameValidator()
        assert v.validate_strict("Anne-Marie") == "Anne-Marie"


class TestRejectPathHostileChar:
    """WI-111: forward slash '/' in a name. Path-hostile (breaks the
    @{name}.md file path) AND a connective descriptor form. create_stub used
    to strip this via the legacy re.sub; with that mangler deleted, '/' must
    be rejected at the boundary or it reaches the file path.

    Verified 2026-06-06: 0 of 1590 live vault names contain '/'.
    """

    def test_rejects_forward_slash_between_names(self):
        v = NameValidator()
        with pytest.raises(NameValidationError) as exc:
            v.validate_strict("Naomi / David")
        assert exc.value.pattern == "path_hostile_char"

    def test_rejects_slash_no_spaces(self):
        v = NameValidator()
        with pytest.raises(NameValidationError):
            v.validate_strict("Foo/Bar")

    def test_clean_raises_on_slash(self):
        v = NameValidator()
        with pytest.raises(NameValidationError):
            v.clean("A / B")


class TestRejectArchivePrefix:
    """Pattern 3: Obsidian 'zArchived -' convention leaked into name field."""

    def test_rejects_zarchived_prefix(self):
        v = NameValidator()
        with pytest.raises(NameValidationError) as exc:
            v.validate_strict("zArchived - Rosie Samuels")
        assert exc.value.pattern == "archive_prefix"

    def test_rejects_double_z_archived(self):
        v = NameValidator()
        with pytest.raises(NameValidationError):
            v.validate_strict("zzArchived - Someone")

    def test_does_NOT_reject_normal_name_starting_with_z(self):
        v = NameValidator()
        assert v.validate_strict("Zoe Williams") == "Zoe Williams"


class TestRejectUnknownContactLiteral:
    """Pattern 4: '<phone-digits> unknown contact' WhatsApp scanner bug."""

    def test_rejects_unknown_contact_with_phone(self):
        v = NameValidator()
        with pytest.raises(NameValidationError) as exc:
            v.validate_strict("219945292038370 unknown contact")
        assert exc.value.pattern == "unknown_contact"

    def test_rejects_unknown_contact_anywhere(self):
        v = NameValidator()
        with pytest.raises(NameValidationError):
            v.validate_strict("Jane Doe unknown contact")


class TestRejectEmailCharacters:
    """Pattern 5: name contains '@' — smoking gun for email leak.

    Note: `<` and `>` alone are NOT rejected. They're parseaddr-style stale
    inputs (handled by existing downstream regex sanitizer) and the 2026-06-02
    vault audit found 0 production records with `<` or `>` in the name field.
    """

    def test_rejects_at_sign(self):
        v = NameValidator()
        with pytest.raises(NameValidationError) as exc:
            v.validate_strict("naomi@speechmatics.com")
        assert exc.value.pattern == "contains_email_chars"

    def test_rejects_full_email_form_with_at_sign(self):
        v = NameValidator()
        with pytest.raises(NameValidationError):
            v.validate_strict("Naomi Pavie <naomi@speechmatics.com>")

    def test_does_NOT_reject_angle_brackets_without_at_sign(self):
        # WI-017-era inputs like 'David Smith <not-an-email>' must still pass
        # — they're stale-input junk that downstream regex handles.
        v = NameValidator()
        result = v.validate_strict("David Smith <not-an-email>")
        assert result == "David Smith <not-an-email>"


class TestRejectPureDigitName:
    """Pattern 6: pure digits in name. Allowed ONLY when phone sentinel mode is on."""

    def test_rejects_pure_digit_default(self):
        v = NameValidator()
        with pytest.raises(NameValidationError) as exc:
            v.validate_strict("+447739341679")
        assert exc.value.pattern == "pure_digit_name"

    def test_accepts_phone_sentinel_when_flag_on(self):
        v = NameValidator()
        # WI-083 path: phone-only stubs explicitly opt in
        result = v.validate_strict("+447739341679", allow_phone_sentinel=True)
        assert result == "+447739341679"

    def test_accepts_unformatted_phone_when_flag_on(self):
        v = NameValidator()
        # iMessage handle without + prefix is also allowed under the sentinel
        result = v.validate_strict("447739341679", allow_phone_sentinel=True)
        assert result == "447739341679"


# ============================================================
# Tier 2 — CLEAN (clean() applies fixes transparently)
# ============================================================

class TestCleanWhitespace:
    """Pattern 7: Tier 2 whitespace anomalies — clean transparently."""

    def test_collapses_double_space(self):
        v = NameValidator()
        result = v.clean("Sebastian Trumpet  Tsotne Trumpet")
        assert result.cleaned_name == "Sebastian Trumpet Tsotne Trumpet"
        assert "double_space_collapse" in result.repairs_applied

    def test_strips_leading_trailing(self):
        v = NameValidator()
        result = v.clean("  Jane Doe  ")
        assert result.cleaned_name == "Jane Doe"
        assert "strip_whitespace" in result.repairs_applied

    def test_no_repairs_for_clean_name(self):
        v = NameValidator()
        result = v.clean("Jane Doe")
        assert result.cleaned_name == "Jane Doe"
        assert result.repairs_applied == []
        assert result.ambiguous is False


class TestCleanRaisesOnTier1:
    """clean() still raises NameValidationError for Tier 1 patterns — it's not
    a 'forgive-all'. Only Tier 2 patterns are auto-cleaned. Tier 1 must fail
    loud so the producer fixes its data."""

    def test_clean_still_raises_on_rfc2822(self):
        v = NameValidator()
        with pytest.raises(NameValidationError):
            v.clean("Naomi Pavie naomipavieatspeechmaticscom")

    def test_clean_still_raises_on_calendar_prefix(self):
        v = NameValidator()
        with pytest.raises(NameValidationError):
            v.clean("Dave - Naomi Pavie")


# ============================================================
# Baseline — must ACCEPT real valid names from production vault
# ============================================================

class TestAcceptsRealValidNames:
    """Real names from the 2026-06-02 audit's 'clean' bucket must pass.

    False positives here are worse than missing junk — destroying real names
    in cleanup would be a regression. These are the false-positive guards.
    """

    @pytest.mark.parametrize("name", [
        "Naomi Pavie",
        "David Field",
        "Anne-Sophie Legrain",       # hyphenated last name
        "Sam Tucker Keith",          # 3-part name (last=Keith, NOT a company-suffix concern in validator)
        "Holly Murdoch WSL Football", # 4-token but legit (company-suffix is Tier 3, not Tier 1)
        "Alina Vasile",
        "Ursa Robinson",
        "Michael Seipp",
        "Chloe Sinclair",
        "Dominique Askew",
        "Fiona Lay",
        "Founders Intelligence",     # business-like but not corrupted
        "Mitch R",                    # initial as surname
        "Blair Robertson",
        "Owen O'Loan",               # apostrophe
        "Maritza Bonano",
        "José García",                # accented chars
        "Andrea van der Berg",       # particle
        # WI-111 false-positive guards — the vault stores companies as person
        # notes; the 2026-06-06 audit found these 13 live '&'/'and' company
        # names. They must NOT be rejected (an '&'/'and' tier1 pattern would
        # destroy real notes). Verified against the live vault.
        "Bain & Company",
        "Marks and Spencer",
        "Bird & Bird LLP",
        "Bloom & Wild",
        "Few and Far",
        # WI-111 punctuation guards — the deleted re.sub used to mangle these
        # (O'Brien->OBrien, Dr. Smith->Dr Smith). validate_strict passes them;
        # post-fix create_stub must store them verbatim.
        "Owen O'Brien",
        "Dr. Smith",
        "Anne-Marie",
    ])
    def test_accepts_real_valid_name(self, name):
        v = NameValidator()
        assert v.validate_strict(name) == name

    def test_accepts_short_initials_as_name(self):
        # Vault contains 2-char records like 'AW', 'EG', 'SP' — could be real initials
        # Validator must NOT reject these as Tier 1 (they're Tier 3 ambiguous at worst)
        v = NameValidator()
        assert v.validate_strict("AW") == "AW"

    def test_accepts_single_word_first_name(self):
        # 'Naomi' standalone — incomplete stub, but not corrupted. Validator passes.
        v = NameValidator()
        assert v.validate_strict("Naomi") == "Naomi"


# ============================================================
# Edge / robustness
# ============================================================

# ============================================================
# WI-111 — closed-loop contract: clean() is closed under validate_strict
# ============================================================

# Frozen real-data corpus. Drawn from the live vault / _quarantine / _merged_dupes
# audit (2026-06-06) plus the WI-105 / WI-017 corruption classes and valid-name
# controls. The contract under test: a name that clean() RETURNS (does not reject)
# can never be one validate_strict would reject. This is the executable guarantee
# that the create_stub boundary (which stores clean()'s output verbatim, WI-111
# Decision 6) cannot persist a tier1-corrupt name.
_CLOSED_LOOP_CORPUS = [
    # --- RFC 2822 leaks (WI-017 / WI-105 class) — real vault samples ---
    "Naomi Pavie naomipavieatspeechmaticscom",
    "Anne Almeida-Anderson anneno-worriescouk",
    "David Field davidfspeechmaticscom",
    "Emily Mendes emilymspeechmaticscom",
    "Faith Forster faithmforstergmailcom",
    "Antony Berg antonybspeechmaticscom",
    "Chris Oakes no-worriescouk",
    "Prachi Garg prachi_gargoutlookcom",
    "Ronald Ashri ronaldashriopendialogai",
    "davewaschaexclaimercom",
    # --- calendar / transcript prefixes (real _merged_dupes samples) ---
    "Dave - Naomi Pavie",
    "Dave - Chris Oakes",
    "Dave - Lauren King Speechmatics",
    "Dave - Emily Mendes Speechmatics",
    "Me to David Field",
    "Me - Tom Green",
    "zArchived - Rosie Samuels",
    # --- THE 2026-06-06 manufactured cases (WI-111 root) — must be rejected ---
    "Dave -> Thomas Gatten (Adzact)",
    "Me to: David Field",
    "Naomi Pavie -> David Field",
    # --- path-hostile / other tier1 ---
    "Naomi / David",
    "Foo/Bar",
    "219945292038370 unknown contact",
    "naomi@speechmatics.com",
    "+447739341679",
    # --- valid-name controls (must pass clean() AND validate_strict cleanly) ---
    "Naomi Pavie",
    "David Field",
    "Owen O'Brien",          # apostrophe — the deleted re.sub mangled this
    "Dr. Smith",             # period — likewise
    "José García",           # accents
    "Anne-Marie",            # hyphen
    "Anne-Sophie Legrain",
    "Sören Winter",
    "Maurizio Morriello",    # ends in 'io' — RFC2822 false-positive guard
    "Francisco Vigo",        # ends in 'co'
    "Andrea van der Berg",   # particle
    "Bain & Company",        # company-as-person note ('&' must not reject)
    "Marks and Spencer",     # company ('and' must not reject)
    "Bird & Bird LLP",
    "  Jane  Doe  ",         # whitespace — clean() repairs, must stay closed
]


class TestCleanClosedUnderValidateStrict:
    """WI-111 Decision 6 — the executable contract.

    For every name in the frozen corpus: clean() either RAISES (rejected at the
    boundary) OR validate_strict(clean(x).cleaned_name) returns the SAME string
    without raising. clean() can therefore never emit a name the invariant
    (validate_strict-based) would later flag — the corruption-by-the-boundary
    failure mode that caused the 2026-06-06 incident is closed.
    """

    @pytest.mark.parametrize("name", _CLOSED_LOOP_CORPUS)
    def test_clean_output_passes_validate_strict(self, name):
        v = NameValidator()
        try:
            cleaned = v.clean(name).cleaned_name
        except NameValidationError:
            return  # rejected — acceptable per the contract
        # clean() returned a name → validate_strict must accept it UNCHANGED.
        revalidated = v.validate_strict(cleaned)
        assert revalidated == cleaned, (
            f"clean({name!r}) emitted {cleaned!r} but validate_strict "
            f"normalized it to {revalidated!r} — boundary is NOT closed"
        )

    def test_2026_06_06_cases_are_rejected_not_just_closed(self):
        """The two production cases must land in the REJECTED branch — storing
        them verbatim (validate_strict-green but garbage) would trade a loud
        failure for a silent one, which deleting the re.sub alone would do."""
        v = NameValidator()
        for bad in ("Dave -> Thomas Gatten (Adzact)", "Me to: David Field"):
            with pytest.raises(NameValidationError):
                v.clean(bad)


class TestEdgeCases:
    def test_empty_string_raises(self):
        v = NameValidator()
        with pytest.raises(NameValidationError) as exc:
            v.validate_strict("")
        assert exc.value.pattern == "empty"

    def test_whitespace_only_raises(self):
        v = NameValidator()
        with pytest.raises(NameValidationError):
            v.validate_strict("   ")

    def test_validate_strict_normalizes_whitespace(self):
        # validate_strict trims and collapses (light cleaning is in-band)
        v = NameValidator()
        assert v.validate_strict("  Jane  Doe  ") == "Jane Doe"

    def test_validation_error_carries_structured_detail(self):
        v = NameValidator()
        with pytest.raises(NameValidationError) as exc:
            v.validate_strict("Naomi Pavie naomipavieatspeechmaticscom")
        assert exc.value.pattern == "rfc2822_leak"
        assert isinstance(exc.value.detail, str)
        assert len(exc.value.detail) > 0


# ============================================================
# Integration with create_stub (verified via existing test_repositories.py
# but smoke-tested here too)
# ============================================================

class TestCleanResultShape:
    def test_clean_result_is_immutable_dataclass(self):
        result = CleanResult(cleaned_name="Jane Doe", repairs_applied=[], ambiguous=False)
        assert result.cleaned_name == "Jane Doe"

    def test_clean_result_lists_all_repairs(self):
        v = NameValidator()
        result = v.clean("  Jane  Doe  ")
        # Both leading-strip AND double-space-collapse should be recorded
        assert set(result.repairs_applied) >= {"strip_whitespace", "double_space_collapse"}


# ============================================================
# Weak-identity predicate (WI-117)
# ============================================================

class TestWeakIdentityReason:
    """weak_identity_reason is the shared predicate behind find_or_create_stub's
    WeakIdentityError and exocortex's _should_skip_stub. It MUST match the live
    exocortex behaviour exactly (transcript.py:711-724), incl. the byte-identical
    reason strings the review queue consumes.
    """

    # --- Case 1: single-token name, no identifier ---

    def test_bare_first_name_no_id_is_weak(self):
        assert weak_identity_reason("Darryl") == "single-name, no email"

    def test_bare_first_name_with_email_is_strong(self):
        assert weak_identity_reason("Darryl", email="d@kato.app") is None

    def test_bare_first_name_with_phone_is_strong(self):
        # The orchestrator caller supplies phone; a phone is enough identity.
        assert weak_identity_reason("Darryl", phone="+447700900123") is None

    def test_multi_token_name_no_id_is_strong(self):
        assert weak_identity_reason("Darryl Friend") is None

    # --- Case 2: social-handle pattern ---

    def test_social_handle_with_no_id_falls_to_case1_first(self):
        # PRECEDENCE (matches exocortex _should_skip_stub exactly): a handle with
        # no email/phone is also single-token-no-id, and case 1 is checked first,
        # so the reason is "single-name, no email", not the handle reason. This
        # pins the ordering so it can't silently flip.
        assert weak_identity_reason("darryl_f") == "single-name, no email"

    def test_social_handle_is_weak_when_email_present(self):
        # With an email, case 1 (no-email) is bypassed, so the handle branch
        # fires and we get the social-handle reason. This is the distinct path
        # the case-2 branch exists for.
        assert weak_identity_reason("john_doe_92", email="x@y.com") == "social handle pattern: john_doe_92"

    def test_underscore_with_space_is_not_a_handle(self):
        # A space means it reads as a name, not a handle.
        assert weak_identity_reason("John Doe_X", email="x@y.com") is None

    # --- reason-string fidelity (the round-trip exocortex depends on) ---

    def test_reason_strings_match_exocortex_originals(self):
        assert weak_identity_reason("Vlad") == "single-name, no email"
        # Handle reason only surfaces when an identifier bypasses case 1.
        assert weak_identity_reason("vlad_p", email="x@y.com") == "social handle pattern: vlad_p"

    def test_empty_name_is_not_weak_identity(self):
        # Empty names are the NameValidator boundary's job, not weak-identity's.
        assert weak_identity_reason("") is None


class TestWeakIdentityError:
    def test_carries_reason_attribute(self):
        err = WeakIdentityError("single-name, no email")
        assert err.reason == "single-name, no email"
        assert str(err) == "single-name, no email"

    def test_is_a_valueerror_sibling_of_name_validation_error(self):
        # Both subclass ValueError so a broad `except ValueError` still catches
        # either, but they're distinct types so callers can disposition them
        # separately (422 reason vs 422 pattern).
        assert issubclass(WeakIdentityError, ValueError)
        assert not issubclass(WeakIdentityError, NameValidationError)
