"""
Tests for Pydantic entity models.
"""

import pytest
from obsidian_schemas.models import (
    Person,
    Company,
    Book,
    Watch,
    Explore,
    GiftIdea,
    Meeting,
    get_model_for_type,
)


class TestPerson:
    """Tests for Person model."""

    def test_create_empty_person(self):
        """Test creating a person with defaults."""
        person = Person()
        assert person.type == "person"
        assert person.name == ""
        assert person.emails == []
        assert person.phones == []
        assert person.tags == []

    def test_create_person_with_data(self):
        """Test creating a person with data."""
        person = Person(
            name="John Smith",
            emails=["john@example.com", "john.smith@work.com"],
            phones=["447990558521"],
            company="Acme Corp",
            title="CTO",
            linkedin="https://linkedin.com/in/johnsmith",
            tags=["person", "contact"],
            created="2025-01-01",
        )
        assert person.name == "John Smith"
        assert len(person.emails) == 2
        assert person.get_primary_email() == "john@example.com"
        assert person.company == "Acme Corp"

    def test_person_extra_fields(self):
        """Test that extra fields are preserved."""
        person = Person(
            name="Jane Doe",
            custom_field="custom value",
            auto_created=True,
        )
        assert person.name == "Jane Doe"
        # Extra fields accessible via model_extra
        assert person.model_extra.get("custom_field") == "custom value"
        assert person.model_extra.get("auto_created") is True

    def test_person_to_entity_id(self):
        """Test entity ID generation."""
        person = Person(name="John Smith")
        assert person.to_entity_id() == "person_john_smith"

    def test_person_birthday_default(self):
        """Test that birthday defaults to empty string."""
        person = Person(name="Jane Doe")
        assert person.birthday == ""

    def test_person_birthday_full_date(self):
        """Test birthday with full date DD-MM-YYYY format."""
        person = Person(
            name="John Smith",
            birthday="15-03-1985",
        )
        assert person.birthday == "15-03-1985"

    def test_person_birthday_without_year(self):
        """Test birthday with just day and month DD-MM format."""
        person = Person(
            name="Jane Doe",
            birthday="25-12",
        )
        assert person.birthday == "25-12"

    def test_person_with_all_fields_including_birthday(self):
        """Test creating a person with all fields including birthday."""
        person = Person(
            name="John Smith",
            emails=["john@example.com"],
            phones=["447990558521"],
            company="Acme Corp",
            title="CTO",
            linkedin="https://linkedin.com/in/johnsmith",
            birthday="15-03-1985",
            roles=["vip"],
            tags=["person", "contact"],
            created="2025-01-01",
        )
        assert person.name == "John Smith"
        assert person.birthday == "15-03-1985"
        assert person.company == "Acme Corp"

    def test_person_slack_default(self):
        """Test that slack defaults to empty string."""
        person = Person(name="Jane Doe")
        assert person.slack == ""

    def test_person_slack_user_id(self):
        """Test slack field with Slack user ID format."""
        person = Person(
            name="John Smith",
            slack="U052R9S0RB6",
        )
        assert person.slack == "U052R9S0RB6"

    def test_person_slack_handle(self):
        """Test slack field with @handle format."""
        person = Person(
            name="Jane Doe",
            slack="@jdoe",
        )
        assert person.slack == "@jdoe"

    def test_person_with_all_fields_including_slack(self):
        """Test creating a person with all fields including slack."""
        person = Person(
            name="John Smith",
            emails=["john@example.com"],
            phones=["447990558521"],
            company="Acme Corp",
            title="CTO",
            linkedin="https://linkedin.com/in/johnsmith",
            slack="U052R9S0RB6",
            birthday="15-03-1985",
            roles=["vip"],
            tags=["person", "contact"],
            created="2025-01-01",
        )
        assert person.name == "John Smith"
        assert person.slack == "U052R9S0RB6"
        assert person.birthday == "15-03-1985"


class TestCompany:
    """Tests for Company model."""

    def test_create_company(self):
        """Test creating a company."""
        company = Company(
            name="Acme Corp",
            website="https://acme.com",
            industry="Technology",
            linkedin="https://linkedin.com/company/acme",
            tags=["company"],
            created="2025-01-01",
        )
        assert company.type == "company"
        assert company.name == "Acme Corp"
        assert company.website == "https://acme.com"

    def test_company_to_entity_id(self):
        """Test company entity ID generation."""
        company = Company(name="Acme-Corp")
        assert company.to_entity_id() == "company_acme_corp"


class TestBook:
    """Tests for Book model."""

    def test_create_book(self):
        """Test creating a book."""
        book = Book(
            title="Children of Time",
            author="Adrian Tchaikovsky",
            description="A sci-fi novel about spiders.",
            status="read",
            rating="5",
            isbn="9781447273301",
            publisher="Pan Macmillan",
            publication_year="2016",
            tags=["book", "Fiction"],
            date_added="2026-01-02",
        )
        assert book.type == "book"
        assert book.title == "Children of Time"
        assert book.status == "read"
        assert book.rating == "5"

    def test_book_default_status(self):
        """Test book default status."""
        book = Book(title="New Book")
        assert book.status == "to-read"


class TestWatch:
    """Tests for Watch model."""

    def test_create_watch(self):
        """Test creating a watch item."""
        watch = Watch(
            title="Inception",
            media_type="film",
            director="Christopher Nolan",
            year="2010",
            status="watched",
            rating="5",
            streaming_service="Netflix",
            tags=["watch"],
        )
        assert watch.type == "watch"
        assert watch.title == "Inception"
        assert watch.media_type == "film"


class TestExplore:
    """Tests for Explore model."""

    def test_create_explore(self):
        """Test creating an explore item."""
        explore = Explore(
            subtype="link",
            title="TRMNL - E-ink Dashboard",
            url="https://usetrmnl.com/",
            source="Todoist Explore",
            status="captured",
            tags=["explore"],
            created="2026-01-01",
        )
        assert explore.type == "explore"
        assert explore.subtype == "link"
        assert explore.url == "https://usetrmnl.com/"


class TestGiftIdea:
    """Tests for GiftIdea model."""

    def test_create_gift_idea(self):
        """Test creating a gift idea with alias."""
        gift = GiftIdea(
            **{"for": "Mom", "source": "Amazon", "date_added": "2025-12-01"}
        )
        assert gift.type == "gift-idea"
        # Access via alias
        assert gift.for_person == "Mom"


class TestMeeting:
    """Tests for Meeting model."""

    def test_create_meeting(self):
        """Test creating a meeting."""
        meeting = Meeting(
            date="2025-01-03",
            attendees=["John Smith", "Jane Doe"],
            topics=["Budget review", "Q1 planning"],
            meeting_id="meeting_20250103_john_jane",
            tags=["meeting"],
        )
        assert meeting.type == "meeting"
        assert meeting.date == "2025-01-03"
        assert len(meeting.attendees) == 2
        assert len(meeting.topics) == 2


class TestGetModelForType:
    """Tests for get_model_for_type function."""

    def test_get_person(self):
        """Test getting Person model."""
        assert get_model_for_type("person") == Person

    def test_get_company(self):
        """Test getting Company model."""
        assert get_model_for_type("company") == Company

    def test_get_book(self):
        """Test getting Book model."""
        assert get_model_for_type("book") == Book

    def test_get_unknown(self):
        """Test getting unknown type returns None."""
        assert get_model_for_type("unknown") is None
        assert get_model_for_type("") is None
