"""Tests for repository layer."""

import pytest
import tempfile
from pathlib import Path

from obsidian_schemas import PersonRepository, CompanyRepository, Person, Company


@pytest.fixture
def temp_vault():
    """Create a temporary vault with test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        vault = Path(tmpdir)

        # Create test person files
        (vault / "@John Smith.md").write_text("""---
type: person
name: John Smith
aliases:
  - Johnny
  - john@example.com
emails:
  - john@example.com
  - john.smith@work.com
phones:
  - "+447990558521"
whatsapp: "447990558521"
company: Acme Corp
title: CTO
linkedin: https://linkedin.com/in/johnsmith
roles:
  - vip
  - coaching-client
tags:
  - person
created: "2025-01-01"
---

## Timeline
""")

        (vault / "@Jane Doe.md").write_text("""---
type: person
name: Jane Doe
emails:
  - jane@example.com
phones:
  - "+15551234567"
company: Tech Inc
roles:
  - investor
tags:
  - person
created: "2025-01-02"
---

## Timeline
""")

        # Create test company files
        (vault / "@Acme Corp.md").write_text("""---
type: company
name: Acme Corp
website: https://www.acme.com
industry: Technology
linkedin: https://linkedin.com/company/acme
tags:
  - company
created: "2025-01-01"
---

## People
""")

        (vault / "@Tech Inc.md").write_text("""---
type: company
name: Tech Inc
website: https://techinc.io
industry: Software
tags:
  - company
created: "2025-01-02"
---

## People
""")

        # Create a non-entity file (should be ignored)
        (vault / "Random Note.md").write_text("""---
title: Random Note
tags:
  - note
---

Just some notes.
""")

        yield vault


class TestPersonRepository:
    """Tests for PersonRepository."""

    def test_load_vault(self, temp_vault):
        """Test loading persons from vault."""
        repo = PersonRepository(temp_vault)
        assert len(repo) == 2

    def test_get_by_name(self, temp_vault):
        """Test getting person by exact name."""
        repo = PersonRepository(temp_vault)
        person = repo.get("John Smith")
        assert person is not None
        assert person.name == "John Smith"
        assert person.company == "Acme Corp"

    def test_get_by_name_case_insensitive(self, temp_vault):
        """Test case-insensitive name lookup."""
        repo = PersonRepository(temp_vault)
        person = repo.get("john smith")
        assert person is not None
        assert person.name == "John Smith"

    def test_get_by_email(self, temp_vault):
        """Test getting person by email."""
        repo = PersonRepository(temp_vault)
        person = repo.get_by_email("john@example.com")
        assert person is not None
        assert person.name == "John Smith"

    def test_get_by_email_secondary(self, temp_vault):
        """Test getting person by secondary email."""
        repo = PersonRepository(temp_vault)
        person = repo.get_by_email("john.smith@work.com")
        assert person is not None
        assert person.name == "John Smith"

    def test_get_by_phone(self, temp_vault):
        """Test getting person by phone number."""
        repo = PersonRepository(temp_vault)
        person = repo.get_by_phone("+447990558521")
        assert person is not None
        assert person.name == "John Smith"

    def test_get_by_phone_normalized(self, temp_vault):
        """Test phone lookup with different format."""
        repo = PersonRepository(temp_vault)
        person = repo.get_by_phone("447990558521")
        assert person is not None
        assert person.name == "John Smith"

    def test_get_by_phone_whatsapp_jid(self, temp_vault):
        """Test phone lookup with WhatsApp JID."""
        repo = PersonRepository(temp_vault)
        person = repo.get_by_phone("447990558521@s.whatsapp.net")
        assert person is not None
        assert person.name == "John Smith"

    def test_get_by_alias(self, temp_vault):
        """Test getting person by alias."""
        repo = PersonRepository(temp_vault)
        person = repo.get_by_alias("Johnny")
        assert person is not None
        assert person.name == "John Smith"

    def test_resolve_by_name(self, temp_vault):
        """Test resolve finds by name."""
        repo = PersonRepository(temp_vault)
        person = repo.resolve("Jane Doe")
        assert person is not None
        assert person.name == "Jane Doe"

    def test_resolve_by_email(self, temp_vault):
        """Test resolve finds by email."""
        repo = PersonRepository(temp_vault)
        person = repo.resolve("jane@example.com")
        assert person is not None
        assert person.name == "Jane Doe"

    def test_resolve_by_partial_name(self, temp_vault):
        """Test resolve finds by partial name."""
        repo = PersonRepository(temp_vault)
        person = repo.resolve("john")
        assert person is not None
        assert person.name == "John Smith"

    def test_resolve_not_found(self, temp_vault):
        """Test resolve returns None for unknown."""
        repo = PersonRepository(temp_vault)
        person = repo.resolve("Unknown Person")
        assert person is None

    def test_get_by_role(self, temp_vault):
        """Test getting people by role."""
        repo = PersonRepository(temp_vault)
        vips = repo.get_by_role("vip")
        assert len(vips) == 1
        assert vips[0].name == "John Smith"

    def test_get_by_company(self, temp_vault):
        """Test getting people by company."""
        repo = PersonRepository(temp_vault)
        people = repo.get_by_company("Acme Corp")
        assert len(people) == 1
        assert people[0].name == "John Smith"

    def test_get_all(self, temp_vault):
        """Test getting all persons."""
        repo = PersonRepository(temp_vault)
        all_people = repo.get_all()
        assert len(all_people) == 2
        names = {p.name for p in all_people}
        assert names == {"John Smith", "Jane Doe"}

    def test_contains(self, temp_vault):
        """Test __contains__ for checking existence."""
        repo = PersonRepository(temp_vault)
        assert "John Smith" in repo
        assert "Unknown" not in repo

    def test_create_stub(self, temp_vault):
        """Test creating a stub person."""
        repo = PersonRepository(temp_vault)
        person = repo.create_stub(
            name="New Contact",
            email="new@example.com",
            company="New Corp"
        )
        assert person.name == "New Contact"
        assert person.emails == ["new@example.com"]

        # Should be in cache now
        assert "New Contact" in repo

        # File should exist
        assert (temp_vault / "@New Contact.md").exists()

    def test_refresh(self, temp_vault):
        """Test refreshing the cache."""
        repo = PersonRepository(temp_vault)
        assert len(repo) == 2

        # Add a new file
        (temp_vault / "@New Person.md").write_text("""---
type: person
name: New Person
tags:
  - person
---
""")

        # Not visible yet
        assert "New Person" not in repo

        # Refresh
        repo.refresh()
        assert "New Person" in repo
        assert len(repo) == 3


class TestCompanyRepository:
    """Tests for CompanyRepository."""

    def test_load_vault(self, temp_vault):
        """Test loading companies from vault."""
        repo = CompanyRepository(temp_vault)
        assert len(repo) == 2

    def test_get_by_name(self, temp_vault):
        """Test getting company by name."""
        repo = CompanyRepository(temp_vault)
        company = repo.get("Acme Corp")
        assert company is not None
        assert company.name == "Acme Corp"
        assert company.industry == "Technology"

    def test_get_by_domain(self, temp_vault):
        """Test getting company by domain."""
        repo = CompanyRepository(temp_vault)
        company = repo.get_by_domain("acme.com")
        assert company is not None
        assert company.name == "Acme Corp"

    def test_get_by_domain_with_www(self, temp_vault):
        """Test domain lookup strips www."""
        repo = CompanyRepository(temp_vault)
        company = repo.get_by_domain("www.acme.com")
        assert company is not None
        assert company.name == "Acme Corp"

    def test_get_by_domain_full_url(self, temp_vault):
        """Test domain lookup from full URL."""
        repo = CompanyRepository(temp_vault)
        company = repo.get_by_domain("https://www.acme.com/about")
        assert company is not None
        assert company.name == "Acme Corp"

    def test_resolve_by_name(self, temp_vault):
        """Test resolve finds by name."""
        repo = CompanyRepository(temp_vault)
        company = repo.resolve("Tech Inc")
        assert company is not None
        assert company.name == "Tech Inc"

    def test_resolve_by_domain(self, temp_vault):
        """Test resolve finds by domain."""
        repo = CompanyRepository(temp_vault)
        company = repo.resolve("techinc.io")
        assert company is not None
        assert company.name == "Tech Inc"

    def test_get_by_industry(self, temp_vault):
        """Test getting companies by industry."""
        repo = CompanyRepository(temp_vault)
        tech = repo.get_by_industry("Technology")
        assert len(tech) == 1
        assert tech[0].name == "Acme Corp"

    def test_create_stub(self, temp_vault):
        """Test creating a stub company."""
        repo = CompanyRepository(temp_vault)
        company = repo.create_stub(
            name="New Startup",
            website="https://newstartup.com"
        )
        assert company.name == "New Startup"
        assert "New Startup" in repo
        assert (temp_vault / "@New Startup.md").exists()


class TestPhoneNormalization:
    """Tests for phone number normalization."""

    def test_normalize_with_plus(self):
        from obsidian_schemas.repositories.person import normalize_phone
        assert normalize_phone("+447990558521") == "447990558521"

    def test_normalize_with_spaces(self):
        from obsidian_schemas.repositories.person import normalize_phone
        assert normalize_phone("+44 7990 558521") == "447990558521"

    def test_normalize_with_dashes(self):
        from obsidian_schemas.repositories.person import normalize_phone
        assert normalize_phone("555-123-4567") == "5551234567"

    def test_normalize_whatsapp_jid(self):
        from obsidian_schemas.repositories.person import normalize_phone
        assert normalize_phone("447990558521@s.whatsapp.net") == "447990558521"

    def test_phones_match_exact(self):
        from obsidian_schemas.repositories.person import phones_match
        assert phones_match("447990558521", "447990558521")

    def test_phones_match_uk_format(self):
        from obsidian_schemas.repositories.person import phones_match
        assert phones_match("447990558521", "07990558521")

    def test_phones_match_us_format(self):
        from obsidian_schemas.repositories.person import phones_match
        assert phones_match("15551234567", "5551234567")
