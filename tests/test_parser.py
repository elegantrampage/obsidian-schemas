"""
Tests for parser module.
"""

import pytest
import tempfile
from pathlib import Path

from obsidian_schemas.parser import (
    parse_frontmatter,
    parse_to_model,
    parse_markdown_file,
    parse_markdown_content,
    parse_person,
    ParsedDocument,
)
from obsidian_schemas.models import Person, Company, Book
from tests import support
from tests.fixture_vault import NOTES, materialize_vault


class TestParseFrontmatter:
    """Tests for parse_frontmatter function."""

    def test_parse_basic_frontmatter(self):
        """Test parsing basic frontmatter."""
        content = """---
type: person
name: John Smith
---

# John Smith

Some notes here.
"""
        frontmatter, body = parse_frontmatter(content)

        assert frontmatter["type"] == "person"
        assert frontmatter["name"] == "John Smith"
        assert "# John Smith" in body

    def test_parse_no_frontmatter(self):
        """Test parsing content without frontmatter."""
        content = "# Just a heading\n\nSome content."
        frontmatter, body = parse_frontmatter(content)

        assert frontmatter == {}
        assert body == content

    def test_parse_complex_frontmatter(self):
        """Test parsing frontmatter with lists and nested values."""
        content = """---
type: person
name: John Smith
emails:
  - john@example.com
  - john.smith@work.com
phones:
  - "447990558521"
tags:
  - person
  - contact
---

Body content.
"""
        frontmatter, body = parse_frontmatter(content)

        assert frontmatter["type"] == "person"
        assert len(frontmatter["emails"]) == 2
        assert frontmatter["emails"][0] == "john@example.com"
        assert len(frontmatter["tags"]) == 2

    def test_parse_empty_frontmatter(self):
        """Test parsing empty frontmatter."""
        content = """---
---

Some body content.
"""
        frontmatter, body = parse_frontmatter(content)

        assert frontmatter == {}
        assert "Some body content." in body


class TestParseToModel:
    """Tests for parse_to_model function."""

    def test_parse_person_model(self):
        """Test parsing to Person model."""
        frontmatter = {
            "type": "person",
            "name": "John Smith",
            "emails": ["john@example.com"],
            "company": "Acme Corp",
        }

        entity, extra = parse_to_model(frontmatter)

        assert isinstance(entity, Person)
        assert entity.name == "John Smith"
        assert entity.emails == ["john@example.com"]
        assert entity.company == "Acme Corp"
        assert extra == {}

    def test_parse_with_extra_fields(self):
        """Test parsing with extra fields preserves them."""
        frontmatter = {
            "type": "person",
            "name": "John Smith",
            "custom_field": "custom value",
            "auto_created": True,
        }

        entity, extra = parse_to_model(frontmatter)

        assert isinstance(entity, Person)
        assert entity.name == "John Smith"
        # Extra fields in model_extra and returned dict
        assert entity.model_extra.get("custom_field") == "custom value"
        assert "custom_field" in extra
        assert "auto_created" in extra

    def test_parse_unknown_type(self):
        """Test parsing unknown type returns None entity."""
        frontmatter = {
            "type": "unknown_type",
            "name": "Something",
        }

        entity, extra = parse_to_model(frontmatter)

        assert entity is None
        assert extra == frontmatter

    def test_parse_with_explicit_model_class(self):
        """Test parsing with explicit model class."""
        frontmatter = {
            "name": "John Smith",
            "emails": ["john@example.com"],
        }

        entity, extra = parse_to_model(frontmatter, Person)

        assert isinstance(entity, Person)
        assert entity.name == "John Smith"


class TestParseMarkdownContent:
    """Tests for parse_markdown_content function."""

    def test_parse_complete_person(self):
        """Test parsing a complete person file content."""
        content = """---
type: person
name: "Dave Wascha"
aliases: []
emails: ["dave@davewascha.com"]
phones: []
whatsapp: ""
company: "Elegant Rampage"
title: ""
linkedin: "https://www.linkedin.com/in/davewascha/"
tags: [person]
created: "2024-01-01"
---

## Timeline
### 2026-01-01 11:39:50 [intro]
Introduced to Dave Wascha via email
"""
        doc = parse_markdown_content(content)

        assert doc.frontmatter["type"] == "person"
        assert isinstance(doc.entity, Person)
        assert doc.entity.name == "Dave Wascha"
        assert doc.entity.emails == ["dave@davewascha.com"]
        assert doc.entity.company == "Elegant Rampage"
        assert "## Timeline" in doc.body

    def test_parse_book(self):
        """Test parsing a book file content."""
        content = """---
type: book
title: Children of Time
author: Adrian Tchaikovsky
status: read
rating: "5"
isbn: "9781447273301"
publisher: Pan Macmillan
publication_year: "2016"
tags:
  - Fiction
date_added: 2026-01-02
---

# Children of Time

## Notes

Great book!
"""
        doc = parse_markdown_content(content)

        assert isinstance(doc.entity, Book)
        assert doc.entity.title == "Children of Time"
        assert doc.entity.author == "Adrian Tchaikovsky"
        assert doc.entity.status == "read"


class TestParseMarkdownFile:
    """Tests for parse_markdown_file function."""

    def test_parse_file_not_found(self):
        """Test parsing non-existent file raises error."""
        with pytest.raises(FileNotFoundError):
            parse_markdown_file("/nonexistent/file.md")


class TestParsePerson:
    """Tests for parse_person convenience function."""

    def test_parse_person_success(self):
        """Test parsing valid person content."""
        content = """---
type: person
name: John Doe
emails: ["john@example.com"]
---
"""
        person = parse_person(content)

        assert person is not None
        assert person.name == "John Doe"

    def test_parse_person_wrong_type(self):
        """Test parsing non-person content returns None."""
        content = """---
type: company
name: Acme Corp
---
"""
        person = parse_person(content)
        assert person is None


def test_corpus_person_note_parses_to_its_declared_values():
    """WI-016 D5's proof set: the inline heredoc this replaced typed its own
    vault and its own expectations in the same breath, so it asserted only that
    the parser agrees with whoever typed the fixture. This parses the frozen
    corpus's declared `person` representative against the manifest's
    HAND-WRITTEN oracle instead."""
    name = next(n for n, spec in NOTES.items()
                if spec.roundtrip_representative and spec.declared_type == "person")
    spec = NOTES[name]
    with support.temp_dir() as tmp:
        dest = materialize_vault(tmp / "vault")
        doc = parse_markdown_file(dest / name)

        assert doc.file_path == dest / name
        assert isinstance(doc.entity, Person)
        for attribute, expected in spec.fields.items():
            assert getattr(doc.entity, attribute) == expected, (
                f"{name}.{attribute} parsed to "
                f"{getattr(doc.entity, attribute)!r}, declared {expected!r}")
