"""Tests for repository layer."""

import pytest
import tempfile
from pathlib import Path

from obsidian_schemas import (
    PersonRepository, CompanyRepository, BookRepository, MeetingRepository,
    Person, Company, Book, Meeting
)


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
slack: U052R9S0RB6
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

        # Create test book files
        (vault / "4,000 Weeks - Oliver Burkeman.md").write_text("""---
type: book
title: "4,000 Weeks"
author: Oliver Burkeman
description: "A book about time management"
status: read
rating: "5"
isbn: "9781473545557"
publisher: Random House
publication_year: "2021"
tags:
  - book
  - Self-Help
source_url: ""
date_added: "2025-01-01"
date_finished: "2025-02-01"
---

# 4,000 Weeks

## Notes
Great book about productivity.
""")

        (vault / "Children of Time - Adrian Tchaikovsky.md").write_text("""---
type: book
title: Children of Time
author: Adrian Tchaikovsky
description: "Sci-fi epic about evolution"
status: reading
rating: ""
isbn: "9781447273301"
publisher: ""
publication_year: "2015"
tags:
  - book
  - Fiction
source_url: ""
date_added: "2025-03-01"
date_finished: ""
---

# Children of Time

## Notes
""")

        (vault / "Deep Work - Cal Newport.md").write_text("""---
type: book
title: Deep Work
author: Cal Newport
description: "Focus in a distracted world"
status: to-read
rating: ""
isbn: ""
publisher: ""
publication_year: ""
tags:
  - book
source_url: ""
date_added: "2025-04-01"
date_finished: ""
---

# Deep Work

## Notes
""")

        # Create test meeting files
        (vault / "Meeting 20251201 - Product Planning.md").write_text("""---
type: meeting
date: "2025-12-01"
attendees:
  - John Smith
  - Jane Doe
topics:
  - Product roadmap
  - Q1 planning
  - Budget review
meeting_id: "meeting_20251201_product"
tags:
  - meeting
---

# Product Planning Meeting

## Notes
Discussed Q1 priorities.
""")

        (vault / "Meeting 20251203 - Engineering Sync.md").write_text("""---
type: meeting
date: "2025-12-03"
attendees:
  - John Smith
  - Alice Chen
topics:
  - Technical debt
  - Sprint planning
meeting_id: "meeting_20251203_eng"
tags:
  - meeting
---

# Engineering Sync

## Notes
Sprint planning completed.
""")

        (vault / "Meeting 20251203 - Sales Review.md").write_text("""---
type: meeting
date: "2025-12-03"
attendees:
  - Jane Doe
  - Bob Wilson
topics:
  - Q4 results
  - Pipeline review
meeting_id: "meeting_20251203_sales"
tags:
  - meeting
---

# Sales Review

## Notes
Strong Q4 performance.
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

    def test_get_by_slack(self, temp_vault):
        """Test getting person by Slack user ID."""
        repo = PersonRepository(temp_vault)
        person = repo.get_by_slack("U052R9S0RB6")
        assert person is not None
        assert person.name == "John Smith"

    def test_get_by_slack_case_insensitive(self, temp_vault):
        """Test Slack lookup is case-insensitive."""
        repo = PersonRepository(temp_vault)
        person = repo.get_by_slack("u052r9s0rb6")
        assert person is not None
        assert person.name == "John Smith"

    def test_get_by_slack_with_at_prefix(self, temp_vault):
        """Test Slack lookup handles @ prefix."""
        repo = PersonRepository(temp_vault)
        # Even though stored as U052R9S0RB6, lookup with @ should work
        person = repo.get_by_slack("@U052R9S0RB6")
        assert person is not None
        assert person.name == "John Smith"

    def test_get_by_slack_not_found(self, temp_vault):
        """Test Slack lookup returns None for unknown ID."""
        repo = PersonRepository(temp_vault)
        person = repo.get_by_slack("UNOTFOUND")
        assert person is None

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

    def test_update_fields_single(self, temp_vault):
        """Test updating a single field."""
        repo = PersonRepository(temp_vault)
        person = repo.get("John Smith")
        assert person.title == "CTO"

        updated = repo.update_fields(person, {"title": "CEO"})

        assert updated.title == "CEO"
        # Cache should be updated
        assert repo.get("John Smith").title == "CEO"

    def test_update_fields_multiple(self, temp_vault):
        """Test updating multiple fields at once."""
        repo = PersonRepository(temp_vault)
        person = repo.get("John Smith")

        updated = repo.update_fields(person, {
            "title": "Founder",
            "company": "New Venture"
        })

        assert updated.title == "Founder"
        assert updated.company == "New Venture"
        # Original fields should be preserved
        assert updated.name == "John Smith"
        assert "john@example.com" in updated.emails

    def test_update_fields_preserves_body(self, temp_vault):
        """Test that updating fields preserves the markdown body."""
        # First add some content to the body
        file_path = temp_vault / "@John Smith.md"
        content = file_path.read_text()
        content = content.replace(
            "## Timeline\n",
            "## Timeline\n\n### January 2026\nMet at conference.\n"
        )
        file_path.write_text(content)

        repo = PersonRepository(temp_vault)
        person = repo.get("John Smith")

        # Update a field
        repo.update_fields(person, {"title": "Updated Title"})

        # Body should be preserved
        new_content = file_path.read_text()
        assert "Met at conference." in new_content
        assert "### January 2026" in new_content

    def test_update_fields_not_found(self, temp_vault):
        """Test update_fields raises for unknown entity."""
        repo = PersonRepository(temp_vault)
        # Create a person object not in the repo
        fake_person = Person(name="Unknown Person", type="person")

        with pytest.raises(ValueError, match="not found in repository"):
            repo.update_fields(fake_person, {"title": "Test"})

    def test_update_fields_updates_indexes(self, temp_vault):
        """Test that updating indexed fields updates the indexes."""
        repo = PersonRepository(temp_vault)
        person = repo.get("John Smith")

        # Update email
        repo.update_fields(person, {"emails": ["newemail@example.com"]})

        # Old email should not find the person
        assert repo.get_by_email("john@example.com") is None
        # New email should find the person
        assert repo.get_by_email("newemail@example.com") is not None
        assert repo.get_by_email("newemail@example.com").name == "John Smith"

    def test_update_fields_updates_slack_index(self, temp_vault):
        """Test that updating slack field updates the slack index."""
        repo = PersonRepository(temp_vault)
        person = repo.get("John Smith")

        # Verify original slack is indexed
        assert repo.get_by_slack("U052R9S0RB6") is not None

        # Update slack
        repo.update_fields(person, {"slack": "U999NEWID"})

        # Old slack should not find the person
        assert repo.get_by_slack("U052R9S0RB6") is None
        # New slack should find the person
        result = repo.get_by_slack("U999NEWID")
        assert result is not None
        assert result.name == "John Smith"

    def test_append_to_timeline(self, temp_vault):
        """Test appending an entry to the timeline section."""
        repo = PersonRepository(temp_vault)
        person = repo.get("John Smith")

        entry = "\n### December 3, 2025\n[[Meeting 20251203|Meeting]] - Discussed project.\n"
        result = repo.append_to_timeline(person, entry)

        assert result is True

        # Verify content was added
        file_path = temp_vault / "@John Smith.md"
        content = file_path.read_text()
        assert "December 3, 2025" in content
        assert "[[Meeting 20251203|Meeting]]" in content

    def test_append_to_timeline_preserves_existing(self, temp_vault):
        """Test that appending preserves existing timeline content."""
        # First add some existing content
        file_path = temp_vault / "@John Smith.md"
        content = file_path.read_text()
        content = content.replace(
            "## Timeline\n",
            "## Timeline\n\n### January 1, 2025\nExisting entry.\n"
        )
        file_path.write_text(content)

        repo = PersonRepository(temp_vault)
        person = repo.get("John Smith")

        entry = "\n### December 3, 2025\nNew entry.\n"
        repo.append_to_timeline(person, entry)

        # Both entries should exist
        new_content = file_path.read_text()
        assert "January 1, 2025" in new_content
        assert "Existing entry" in new_content
        assert "December 3, 2025" in new_content
        assert "New entry" in new_content

    def test_append_to_timeline_deduplication(self, temp_vault):
        """Test that deduplication prevents duplicate entries."""
        repo = PersonRepository(temp_vault)
        person = repo.get("John Smith")

        entry = "\n### December 3, 2025\n[[Meeting 20251203|Meeting]] - Discussion.\n"

        # First append should succeed
        result1 = repo.append_to_timeline(person, entry, deduplicate_key="Meeting 20251203")
        assert result1 is True

        # Second append with same key should be skipped
        result2 = repo.append_to_timeline(person, entry, deduplicate_key="Meeting 20251203")
        assert result2 is False

        # Verify only one entry exists
        file_path = temp_vault / "@John Smith.md"
        content = file_path.read_text()
        assert content.count("Meeting 20251203") == 1

    def test_append_to_timeline_not_found(self, temp_vault):
        """Test append_to_timeline raises for unknown person."""
        repo = PersonRepository(temp_vault)
        fake_person = Person(name="Unknown Person", type="person")

        with pytest.raises(ValueError, match="not found"):
            repo.append_to_timeline(fake_person, "### Entry\n")


class TestToDiscussMethods:
    """Tests for To Discuss repository methods."""

    @pytest.fixture
    def vault_with_to_discuss(self, tmp_path):
        """Create a vault with a person that has To Discuss items."""
        vault = tmp_path / "vault"
        vault.mkdir()

        # Person with existing To Discuss items
        (vault / "@John Smith.md").write_text("""---
type: person
name: John Smith
tags:
  - person
created: "2025-01-01"
---

## To Discuss
- [ ] Call about project proposal (2026-01-11)
- [x] Review contract terms (2026-01-08)

## Timeline

## Notes
Some notes here.
""")

        # Person without To Discuss section
        (vault / "@Jane Doe.md").write_text("""---
type: person
name: Jane Doe
tags:
  - person
created: "2025-01-01"
---

## Timeline

## Notes
""")

        return vault

    def test_get_to_discuss_items(self, vault_with_to_discuss):
        """Test getting To Discuss items."""
        repo = PersonRepository(vault_with_to_discuss)
        person = repo.get("John Smith")
        items = repo.get_to_discuss_items(person)

        assert len(items) == 2
        assert items[0].text == "Call about project proposal"
        assert items[0].completed is False
        assert items[0].date_added == "2026-01-11"
        assert items[1].text == "Review contract terms"
        assert items[1].completed is True

    def test_get_to_discuss_items_empty(self, vault_with_to_discuss):
        """Test getting items when section is empty or missing."""
        repo = PersonRepository(vault_with_to_discuss)
        person = repo.get("Jane Doe")
        items = repo.get_to_discuss_items(person)
        assert items == []

    def test_get_to_discuss_items_not_found(self, vault_with_to_discuss):
        """Test error for unknown person."""
        repo = PersonRepository(vault_with_to_discuss)
        fake_person = Person(name="Unknown", type="person")

        with pytest.raises(ValueError, match="not found"):
            repo.get_to_discuss_items(fake_person)

    def test_add_to_discuss_item(self, vault_with_to_discuss):
        """Test adding a new To Discuss item."""
        repo = PersonRepository(vault_with_to_discuss)
        person = repo.get("John Smith")

        result = repo.add_to_discuss_item(person, "New discussion topic")
        assert result is True

        # Verify item was added
        items = repo.get_to_discuss_items(person)
        assert len(items) == 3
        assert items[2].text == "New discussion topic"
        assert items[2].completed is False
        # Date should be today
        from datetime import date
        assert items[2].date_added == date.today().isoformat()

    def test_add_to_discuss_item_creates_section(self, vault_with_to_discuss):
        """Test adding item creates section if missing."""
        repo = PersonRepository(vault_with_to_discuss)
        person = repo.get("Jane Doe")

        result = repo.add_to_discuss_item(person, "First item")
        assert result is True

        items = repo.get_to_discuss_items(person)
        assert len(items) == 1
        assert items[0].text == "First item"

    def test_update_to_discuss_item_complete(self, vault_with_to_discuss):
        """Test marking an item as complete."""
        repo = PersonRepository(vault_with_to_discuss)
        person = repo.get("John Smith")

        result = repo.update_to_discuss_item(person, "Call about project proposal", completed=True)
        assert result is True

        items = repo.get_to_discuss_items(person)
        call_item = next(i for i in items if "project proposal" in i.text)
        assert call_item.completed is True

    def test_update_to_discuss_item_uncomplete(self, vault_with_to_discuss):
        """Test marking an item as not complete."""
        repo = PersonRepository(vault_with_to_discuss)
        person = repo.get("John Smith")

        result = repo.update_to_discuss_item(person, "Review contract terms", completed=False)
        assert result is True

        items = repo.get_to_discuss_items(person)
        review_item = next(i for i in items if "contract terms" in i.text)
        assert review_item.completed is False

    def test_update_to_discuss_item_not_found(self, vault_with_to_discuss):
        """Test updating non-existent item returns False."""
        repo = PersonRepository(vault_with_to_discuss)
        person = repo.get("John Smith")

        result = repo.update_to_discuss_item(person, "Non-existent item", completed=True)
        assert result is False

    def test_remove_to_discuss_item(self, vault_with_to_discuss):
        """Test removing a To Discuss item."""
        repo = PersonRepository(vault_with_to_discuss)
        person = repo.get("John Smith")

        result = repo.remove_to_discuss_item(person, "Call about project proposal")
        assert result is True

        items = repo.get_to_discuss_items(person)
        assert len(items) == 1
        assert items[0].text == "Review contract terms"

    def test_remove_to_discuss_item_not_found(self, vault_with_to_discuss):
        """Test removing non-existent item returns False."""
        repo = PersonRepository(vault_with_to_discuss)
        person = repo.get("John Smith")

        result = repo.remove_to_discuss_item(person, "Non-existent item")
        assert result is False

    def test_create_stub_has_to_discuss_section(self, vault_with_to_discuss):
        """Test that create_stub creates person with To Discuss section."""
        repo = PersonRepository(vault_with_to_discuss)
        person = repo.create_stub("New Contact", email="new@example.com")

        # Verify the file has To Discuss section
        file_path = vault_with_to_discuss / "@New Contact.md"
        content = file_path.read_text()
        assert "## To Discuss" in content
        assert "## Timeline" in content
        assert "## Notes" in content


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


class TestBookRepository:
    """Tests for BookRepository."""

    def test_load_vault(self, temp_vault):
        """Test loading books from vault."""
        repo = BookRepository(temp_vault)
        assert len(repo) == 3

    def test_get_by_title(self, temp_vault):
        """Test getting book by title."""
        repo = BookRepository(temp_vault)
        book = repo.get("4,000 Weeks")
        assert book is not None
        assert book.title == "4,000 Weeks"
        assert book.author == "Oliver Burkeman"

    def test_get_by_title_case_insensitive(self, temp_vault):
        """Test case-insensitive title lookup."""
        repo = BookRepository(temp_vault)
        book = repo.get("deep work")
        assert book is not None
        assert book.title == "Deep Work"

    def test_get_by_author(self, temp_vault):
        """Test getting books by author."""
        repo = BookRepository(temp_vault)
        books = repo.get_by_author("Oliver Burkeman")
        assert len(books) == 1
        assert books[0].title == "4,000 Weeks"

    def test_get_by_author_case_insensitive(self, temp_vault):
        """Test case-insensitive author lookup."""
        repo = BookRepository(temp_vault)
        books = repo.get_by_author("adrian tchaikovsky")
        assert len(books) == 1
        assert books[0].title == "Children of Time"

    def test_get_by_isbn(self, temp_vault):
        """Test getting book by ISBN."""
        repo = BookRepository(temp_vault)
        book = repo.get_by_isbn("9781473545557")
        assert book is not None
        assert book.title == "4,000 Weeks"

    def test_get_by_isbn_with_dashes(self, temp_vault):
        """Test ISBN lookup strips dashes."""
        repo = BookRepository(temp_vault)
        book = repo.get_by_isbn("978-1447273301")
        assert book is not None
        assert book.title == "Children of Time"

    def test_get_by_status(self, temp_vault):
        """Test getting books by status."""
        repo = BookRepository(temp_vault)

        read = repo.get_by_status("read")
        assert len(read) == 1
        assert read[0].title == "4,000 Weeks"

        reading = repo.get_by_status("reading")
        assert len(reading) == 1
        assert reading[0].title == "Children of Time"

        to_read = repo.get_by_status("to-read")
        assert len(to_read) == 1
        assert to_read[0].title == "Deep Work"

    def test_resolve_by_title(self, temp_vault):
        """Test resolve finds by title."""
        repo = BookRepository(temp_vault)
        book = repo.resolve("Children of Time")
        assert book is not None
        assert book.title == "Children of Time"

    def test_resolve_by_isbn(self, temp_vault):
        """Test resolve finds by ISBN."""
        repo = BookRepository(temp_vault)
        book = repo.resolve("9781473545557")
        assert book is not None
        assert book.title == "4,000 Weeks"

    def test_resolve_by_partial_title(self, temp_vault):
        """Test resolve finds by partial title."""
        repo = BookRepository(temp_vault)
        book = repo.resolve("Weeks")
        assert book is not None
        assert book.title == "4,000 Weeks"

    def test_resolve_by_author(self, temp_vault):
        """Test resolve finds by author (returns first book)."""
        repo = BookRepository(temp_vault)
        book = repo.resolve("Cal Newport")
        assert book is not None
        assert book.title == "Deep Work"

    def test_resolve_not_found(self, temp_vault):
        """Test resolve returns None when not found."""
        repo = BookRepository(temp_vault)
        book = repo.resolve("Nonexistent Book")
        assert book is None

    def test_create_stub(self, temp_vault):
        """Test creating a stub book."""
        repo = BookRepository(temp_vault)
        book = repo.create_stub(
            title="New Book",
            author="New Author",
            status="to-read"
        )
        assert book.title == "New Book"
        assert book.author == "New Author"
        assert book.status == "to-read"
        assert "New Book" in repo
        assert (temp_vault / "New Book - New Author.md").exists()

    def test_create_stub_without_author(self, temp_vault):
        """Test creating a stub book without author."""
        repo = BookRepository(temp_vault)
        book = repo.create_stub(title="Solo Book")
        assert book.title == "Solo Book"
        assert book.author == ""
        assert (temp_vault / "Solo Book.md").exists()


class TestMeetingRepository:
    """Tests for MeetingRepository."""

    def test_load_vault(self, temp_vault):
        """Test loading meetings from vault."""
        repo = MeetingRepository(temp_vault)
        assert len(repo) == 3

    def test_get_by_meeting_id(self, temp_vault):
        """Test getting meeting by meeting_id."""
        repo = MeetingRepository(temp_vault)
        meeting = repo.get_by_meeting_id("meeting_20251201_product")
        assert meeting is not None
        assert meeting.date == "2025-12-01"
        assert "John Smith" in meeting.attendees

    def test_get_by_meeting_id_case_insensitive(self, temp_vault):
        """Test case-insensitive meeting_id lookup."""
        repo = MeetingRepository(temp_vault)
        meeting = repo.get_by_meeting_id("MEETING_20251203_ENG")
        assert meeting is not None
        assert meeting.date == "2025-12-03"

    def test_get_by_date_single(self, temp_vault):
        """Test getting meetings on a date with one meeting."""
        repo = MeetingRepository(temp_vault)
        meetings = repo.get_by_date("2025-12-01")
        assert len(meetings) == 1
        assert meetings[0].meeting_id == "meeting_20251201_product"

    def test_get_by_date_multiple(self, temp_vault):
        """Test getting meetings on a date with multiple meetings."""
        repo = MeetingRepository(temp_vault)
        meetings = repo.get_by_date("2025-12-03")
        assert len(meetings) == 2
        meeting_ids = {m.meeting_id for m in meetings}
        assert meeting_ids == {"meeting_20251203_eng", "meeting_20251203_sales"}

    def test_get_by_date_range(self, temp_vault):
        """Test getting meetings in a date range."""
        repo = MeetingRepository(temp_vault)
        meetings = repo.get_by_date_range("2025-12-01", "2025-12-03")
        assert len(meetings) == 3

    def test_get_by_date_range_partial(self, temp_vault):
        """Test getting meetings in a partial date range."""
        repo = MeetingRepository(temp_vault)
        meetings = repo.get_by_date_range("2025-12-02", "2025-12-03")
        assert len(meetings) == 2

    def test_get_by_attendee(self, temp_vault):
        """Test getting meetings by attendee."""
        repo = MeetingRepository(temp_vault)
        meetings = repo.get_by_attendee("John Smith")
        assert len(meetings) == 2
        # John attended Product Planning and Engineering Sync

    def test_get_by_attendee_case_insensitive(self, temp_vault):
        """Test case-insensitive attendee lookup."""
        repo = MeetingRepository(temp_vault)
        meetings = repo.get_by_attendee("jane doe")
        assert len(meetings) == 2
        # Jane attended Product Planning and Sales Review

    def test_get_by_topic(self, temp_vault):
        """Test getting meetings by topic."""
        repo = MeetingRepository(temp_vault)
        meetings = repo.get_by_topic("Sprint planning")
        assert len(meetings) == 1
        assert meetings[0].meeting_id == "meeting_20251203_eng"

    def test_search_topics(self, temp_vault):
        """Test searching meetings by partial topic."""
        repo = MeetingRepository(temp_vault)
        meetings = repo.search_topics("planning")
        assert len(meetings) == 2
        # "Q1 planning" and "Sprint planning"

    def test_resolve_by_meeting_id(self, temp_vault):
        """Test resolve finds by meeting_id."""
        repo = MeetingRepository(temp_vault)
        meeting = repo.resolve("meeting_20251203_sales")
        assert meeting is not None
        assert "Bob Wilson" in meeting.attendees

    def test_resolve_by_date(self, temp_vault):
        """Test resolve finds by date."""
        repo = MeetingRepository(temp_vault)
        meeting = repo.resolve("2025-12-01")
        assert meeting is not None
        assert meeting.meeting_id == "meeting_20251201_product"

    def test_resolve_by_attendee(self, temp_vault):
        """Test resolve finds by attendee (returns most recent)."""
        repo = MeetingRepository(temp_vault)
        meeting = repo.resolve("Alice Chen")
        assert meeting is not None
        # Alice only attended Engineering Sync
        assert meeting.meeting_id == "meeting_20251203_eng"

    def test_resolve_by_topic(self, temp_vault):
        """Test resolve finds by topic search."""
        repo = MeetingRepository(temp_vault)
        meeting = repo.resolve("Technical")
        assert meeting is not None
        assert "Technical debt" in meeting.topics

    def test_resolve_not_found(self, temp_vault):
        """Test resolve returns None when not found."""
        repo = MeetingRepository(temp_vault)
        meeting = repo.resolve("Nonexistent Meeting")
        assert meeting is None

    def test_get_recent(self, temp_vault):
        """Test getting most recent meetings."""
        repo = MeetingRepository(temp_vault)
        recent = repo.get_recent(limit=2)
        assert len(recent) == 2
        # Most recent date should be first (2025-12-03)
        assert recent[0].date == "2025-12-03"
        assert recent[1].date == "2025-12-03"

    def test_get_all(self, temp_vault):
        """Test getting all meetings."""
        repo = MeetingRepository(temp_vault)
        all_meetings = repo.get_all()
        assert len(all_meetings) == 3

    def test_contains(self, temp_vault):
        """Test __contains__ for checking existence."""
        repo = MeetingRepository(temp_vault)
        # Contains uses cache_key which is meeting_id for meetings
        assert "meeting_20251201_product" in repo
        assert "nonexistent" not in repo
