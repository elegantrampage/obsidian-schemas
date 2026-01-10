"""
Tests for writer module.
"""

import pytest
import tempfile
from pathlib import Path

from obsidian_schemas.writer import (
    model_to_frontmatter,
    write_frontmatter,
    write_markdown_file,
    update_frontmatter_field,
    update_frontmatter_fields,
    roundtrip_file,
)
from obsidian_schemas.parser import parse_frontmatter, parse_markdown_file
from obsidian_schemas.models import Person, Company, Book


class TestModelToFrontmatter:
    """Tests for model_to_frontmatter function."""

    def test_basic_conversion(self):
        """Test basic model to frontmatter conversion."""
        person = Person(
            name="John Smith",
            emails=["john@example.com"],
            company="Acme Corp",
            tags=["person"],
        )

        fm = model_to_frontmatter(person)

        assert fm["type"] == "person"
        assert fm["name"] == "John Smith"
        assert fm["emails"] == ["john@example.com"]
        assert fm["company"] == "Acme Corp"

    def test_with_extra_fields(self):
        """Test conversion with extra fields."""
        person = Person(
            name="John Smith",
            custom_field="custom value",
        )

        fm = model_to_frontmatter(person, extra_fields={"another_field": "value"})

        assert fm["name"] == "John Smith"
        assert fm["custom_field"] == "custom value"
        assert fm["another_field"] == "value"

    def test_preserves_field_order(self):
        """Test that field order is preserved."""
        person = Person(
            name="John Smith",
            emails=["john@example.com"],
            phones=["1234567890"],
        )

        fm = model_to_frontmatter(person)

        # Check that 'type' comes before 'tags' (first and last model fields)
        keys = list(fm.keys())
        assert keys.index("type") < keys.index("tags")


class TestWriteFrontmatter:
    """Tests for write_frontmatter function."""

    def test_basic_yaml(self):
        """Test basic YAML output."""
        fm = {
            "type": "person",
            "name": "John Smith",
            "emails": ["john@example.com"],
        }

        yaml_str = write_frontmatter(fm)

        assert "type: person" in yaml_str
        assert "name: John Smith" in yaml_str
        assert "john@example.com" in yaml_str

    def test_list_formatting(self):
        """Test list formatting in YAML."""
        fm = {
            "emails": ["one@example.com", "two@example.com"],
        }

        yaml_str = write_frontmatter(fm)

        assert "- one@example.com" in yaml_str
        assert "- two@example.com" in yaml_str


class TestWriteMarkdownFile:
    """Tests for write_markdown_file function."""

    def test_write_from_entity(self):
        """Test writing file from entity."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.md"

            person = Person(
                name="John Smith",
                emails=["john@example.com"],
                tags=["person"],
            )

            result_path = write_markdown_file(
                file_path,
                entity=person,
                body="# John Smith\n\nSome notes.",
            )

            assert result_path == file_path
            assert file_path.exists()

            # Verify content
            content = file_path.read_text()
            assert "---" in content
            assert "type: person" in content
            assert "name: John Smith" in content
            assert "# John Smith" in content

    def test_write_from_frontmatter_dict(self):
        """Test writing file from frontmatter dict."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.md"

            fm = {
                "type": "person",
                "name": "Jane Doe",
            }

            write_markdown_file(
                file_path,
                frontmatter=fm,
                body="# Jane Doe",
            )

            content = file_path.read_text()
            assert "name: Jane Doe" in content

    def test_no_overwrite_by_default(self):
        """Test that existing files are not overwritten by default."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.md"
            file_path.write_text("original content")

            with pytest.raises(FileExistsError):
                write_markdown_file(
                    file_path,
                    frontmatter={"type": "person"},
                )

    def test_overwrite_when_requested(self):
        """Test overwriting when overwrite=True."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.md"
            file_path.write_text("original content")

            write_markdown_file(
                file_path,
                frontmatter={"type": "person", "name": "New Person"},
                overwrite=True,
            )

            content = file_path.read_text()
            assert "name: New Person" in content

    def test_creates_parent_directories(self):
        """Test that parent directories are created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "subdir" / "deep" / "test.md"

            write_markdown_file(
                file_path,
                frontmatter={"type": "person"},
            )

            assert file_path.exists()


class TestUpdateFrontmatterField:
    """Tests for update_frontmatter_field function."""

    def test_update_existing_field(self):
        """Test updating an existing field."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.md"
            file_path.write_text("""---
type: person
name: John Smith
company: Old Company
---

# John Smith
""")

            success = update_frontmatter_field(file_path, "company", "New Company")

            assert success
            content = file_path.read_text()
            assert "company: New Company" in content
            assert "name: John Smith" in content  # Other fields preserved

    def test_add_new_field(self):
        """Test adding a new field."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.md"
            file_path.write_text("""---
type: person
name: John Smith
---

# John Smith
""")

            success = update_frontmatter_field(file_path, "linkedin", "https://linkedin.com/in/john")

            assert success
            content = file_path.read_text()
            assert "linkedin: https://linkedin.com/in/john" in content

    def test_update_nonexistent_file(self):
        """Test updating non-existent file returns False."""
        success = update_frontmatter_field(
            "/nonexistent/file.md",
            "field",
            "value",
        )
        assert not success


class TestUpdateFrontmatterFields:
    """Tests for update_frontmatter_fields function."""

    def test_update_multiple_fields(self):
        """Test updating multiple fields at once."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.md"
            file_path.write_text("""---
type: person
name: John Smith
company: ""
title: ""
---

# John Smith
""")

            success = update_frontmatter_fields(
                file_path,
                {
                    "company": "Acme Corp",
                    "title": "CTO",
                    "new_field": "new value",
                },
            )

            assert success
            content = file_path.read_text()
            assert "company: Acme Corp" in content
            assert "title: CTO" in content
            assert "new_field: new value" in content


class TestRoundtrip:
    """Tests for roundtrip functionality."""

    def test_roundtrip_preserves_data(self):
        """Test that roundtrip preserves all data."""
        original_content = """---
type: person
name: John Smith
emails:
  - john@example.com
phones: []
whatsapp: ""
company: Acme Corp
title: CTO
linkedin: ""
tags:
  - person
  - contact
created: "2025-01-01"
custom_field: custom value
---

# John Smith

## Timeline

Some notes here.
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.md"
            file_path.write_text(original_content)

            # Parse
            doc = parse_markdown_file(file_path)
            assert doc.entity is not None
            assert doc.entity.name == "John Smith"

            # Write back
            write_markdown_file(
                file_path,
                entity=doc.entity,
                body=doc.body,
                extra_fields=doc.extra_fields,
                overwrite=True,
            )

            # Parse again
            doc2 = parse_markdown_file(file_path)

            # Verify data preserved
            assert doc2.entity.name == "John Smith"
            assert doc2.entity.company == "Acme Corp"
            assert "person" in doc2.entity.tags
            assert doc2.extra_fields.get("custom_field") == "custom value"
            assert "## Timeline" in doc2.body
