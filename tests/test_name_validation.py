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
