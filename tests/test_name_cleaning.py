"""Tests for clean_person_name (WI-117 — moved here from exocortex).

These are the ~22 behavioural assertions that lived in
exocortex/tests/test_graph_utils.py (TestCleanPersonName +
TestCleanPersonNameWithoutEmail) before WI-117 relocated the function into the
foundation. They move WITH the function; exocortex keeps a thin re-export
coverage test that the symbol is still importable from exocortex.graph.utils.
"""

from obsidian_schemas.name_cleaning import clean_person_name


class TestCleanPersonName:
    """Tests for clean_person_name()."""

    def test_trailing_digits(self):
        assert clean_person_name("Greg Cooke98") == "Greg Cooke"

    def test_embedded_digits_between_words(self):
        assert clean_person_name("Hannah1 Gadsden") == "Hannah Gadsden"

    def test_normal_name_unchanged(self):
        assert clean_person_name("Alice Smith") == "Alice Smith"

    def test_single_name_unchanged(self):
        assert clean_person_name("Bruno") == "Bruno"

    def test_empty_string(self):
        assert clean_person_name("") == ""

    def test_only_digits_returns_original(self):
        assert clean_person_name("123") == "123"

    def test_org_suffix_stripped_via_email(self):
        assert clean_person_name("Anne-Sophie Legrain Vetup", "anne-sophie.legrain@vetup.fr") == "Anne-Sophie Legrain"

    def test_org_suffix_evidensia(self):
        assert clean_person_name("Martijn Donkersloot  Evidensia Support", "martijn.donkersloot@evidensia.nl") == "Martijn Donkersloot"

    def test_no_org_suffix_without_email(self):
        """Without email, can't detect org suffix — name unchanged."""
        assert clean_person_name("Anne-Sophie Legrain Vetup") == "Anne-Sophie Legrain Vetup"

    def test_two_word_name_not_stripped(self):
        """Two-word names should never be stripped to one word."""
        assert clean_person_name("Alice Smith", "alice@smith.com") == "Alice Smith"

    def test_double_spaces_collapsed(self):
        assert clean_person_name("Martijn  Donkersloot") == "Martijn Donkersloot"


class TestCleanPersonNameWithoutEmail:
    """WI-105 Step 2: company-suffix stripping must work WITHOUT email.

    The pre-WI-105 implementation only stripped org suffixes when the email
    arg was non-empty (used to derive domain prefix). The 2026-06-02 vault
    audit proved EVERY junky record has [no-email] — meaning the bleed all
    came in via this exact gap. New contract: pass `known_companies` set
    from PersonRepository and the cleaner uses that as the dynamic blacklist.
    """

    def test_company_suffix_stripped_via_known_companies_no_email(self):
        # Real production case: 'Naomi Pavie Speechmatics' with no email
        # arrived from Granola. After fix, suffix gets stripped using the
        # vault's company set, no email required.
        companies = {"Speechmatics", "Komi", "Kato"}
        assert clean_person_name(
            "Naomi Pavie Speechmatics", known_companies=companies
        ) == "Naomi Pavie"

    def test_company_prefix_stripped_via_known_companies_no_email(self):
        # Reverse pattern: 'Speechmatics Emily Mendes team' — company at start.
        companies = {"Speechmatics"}
        result = clean_person_name(
            "Speechmatics Emily Mendes team", known_companies=companies
        )
        # "team" is a generic org suffix (already handled); company prefix stripped
        assert result == "Emily Mendes"

    def test_calendar_prefix_dave_dash_stripped(self):
        assert clean_person_name("Dave - Naomi Pavie") == "Naomi Pavie"

    def test_calendar_prefix_with_company_suffix_stacked(self):
        # Real production case: 'Dave - Lauren King Speechmatics'.
        # Strip prefix, then strip company suffix.
        companies = {"Speechmatics"}
        assert clean_person_name(
            "Dave - Lauren King Speechmatics", known_companies=companies
        ) == "Lauren King"

    def test_me_to_prefix_stripped(self):
        assert clean_person_name("Me to Tom Green") == "Tom Green"

    def test_clean_person_name_wi111_divergence(self):
        """WI-111 single-authority decision (2026-06-06): this strip-to-recover
        pass intentionally diverges from obsidian-schemas NameValidator (a
        reject gate). It RECOVERS the old prefix forms (so create_stub gets a
        clean name) but does NOT recover the newer arrow/colon descriptor forms
        — those flow unchanged to the boundary, which rejects them, and the
        ingester skips + flags for review. This test pins that divergence so it
        stays a conscious decision, not silent drift.
        """
        # Recovered → clean name reaches the boundary and passes.
        assert clean_person_name("Dave - Naomi Pavie") == "Naomi Pavie"
        assert clean_person_name("Me to Tom Green") == "Tom Green"
        # NOT recovered → left for the boundary to reject (recovery is ambiguous).
        assert clean_person_name("Dave -> Thomas Gatten (Adzact)") == "Dave -> Thomas Gatten (Adzact)"
        assert clean_person_name("Me to: David Field") == "Me to: David Field"

    def test_archive_prefix_stripped(self):
        assert clean_person_name("zArchived - Rosie Samuels") == "Rosie Samuels"

    def test_unknown_contact_suffix_stripped(self):
        # 'X unknown contact' → 'X'. Pure-phone case: '+E164 unknown contact'.
        assert clean_person_name("Jane Doe unknown contact") == "Jane Doe"

    def test_unknown_contact_with_pure_phone_returns_phone(self):
        # WhatsApp scanner: '447950289840 unknown contact' should become
        # the phone string alone, which downstream handles as phone sentinel.
        assert clean_person_name("447950289840 unknown contact") == "447950289840"

    def test_does_NOT_strip_non_company_last_token(self):
        # False-positive guard: 'Sam Tucker Keith' — "Keith" might be a first
        # name OR a vault-company. With strict known-companies check, only
        # strip when there's a match. Keith NOT in set → preserve full name.
        assert clean_person_name(
            "Sam Tucker Keith", known_companies={"Speechmatics", "Komi"}
        ) == "Sam Tucker Keith"

    def test_short_name_not_stripped_even_with_company_match(self):
        # 'Jane Speechmatics' is 2-tokens. Stripping would leave 'Jane' alone.
        # Existing safeguard: never strip below 2 tokens.
        assert clean_person_name(
            "Jane Speechmatics", known_companies={"Speechmatics"}
        ) == "Jane Speechmatics"

    def test_multi_word_company_suffix(self):
        # 'Andrea Guariglia Dawn Capital' — last 2 words ARE the company.
        companies = {"Dawn Capital"}
        assert clean_person_name(
            "Andrea Guariglia Dawn Capital", known_companies=companies
        ) == "Andrea Guariglia"

    def test_clean_name_passes_through_unchanged(self):
        # Baseline: a clean valid name with no patterns must pass unchanged
        # even when known_companies is set.
        companies = {"Speechmatics", "Komi"}
        assert clean_person_name(
            "Alice Smith", known_companies=companies
        ) == "Alice Smith"

    def test_existing_email_path_still_works(self):
        # Regression: the original email-based behavior still works when
        # known_companies is not passed.
        assert clean_person_name(
            "Anne-Sophie Legrain Vetup", "anne-sophie.legrain@vetup.fr"
        ) == "Anne-Sophie Legrain"
