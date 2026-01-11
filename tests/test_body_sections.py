"""Tests for body section parser and writer."""

import pytest
from collections import OrderedDict

from obsidian_schemas.body_sections import (
    parse_body_sections,
    write_body_sections,
    get_section,
    update_section,
    prepend_to_section,
    append_to_section,
    ensure_sections_exist,
    get_default_body,
    get_expected_sections,
    ENTITY_BODY_CONFIG,
    ToDiscussItem,
    parse_to_discuss_items,
    write_to_discuss_items,
)


class TestParseBodySections:
    """Tests for parse_body_sections()."""

    def test_parse_empty_body(self):
        """Empty body returns empty dict."""
        assert parse_body_sections("") == OrderedDict()
        assert parse_body_sections("   ") == OrderedDict()
        assert parse_body_sections("\n\n") == OrderedDict()

    def test_parse_single_section(self):
        """Single section is parsed correctly."""
        body = "## Notes\nSome content here.\n"
        result = parse_body_sections(body)

        assert len(result) == 1
        assert "Notes" in result
        assert result["Notes"] == "Some content here.\n"

    def test_parse_multiple_sections(self):
        """Multiple sections are parsed in order."""
        body = """## Timeline
### Jan 2026
Entry 1.

## Notes
Some notes.
"""
        result = parse_body_sections(body)

        assert len(result) == 2
        assert list(result.keys()) == ["Timeline", "Notes"]
        assert "### Jan 2026" in result["Timeline"]
        assert "Some notes" in result["Notes"]

    def test_parse_preserves_order(self):
        """Section order is preserved."""
        body = "## A\nContent A\n\n## B\nContent B\n\n## C\nContent C\n"
        result = parse_body_sections(body)

        assert list(result.keys()) == ["A", "B", "C"]

    def test_parse_empty_section(self):
        """Empty sections are captured."""
        body = "## Empty\n\n## HasContent\nSome text.\n"
        result = parse_body_sections(body)

        assert result["Empty"] == "\n"
        assert "Some text" in result["HasContent"]

    def test_parse_nested_headings(self):
        """Nested headings (###) are kept within sections."""
        body = """## Timeline
### January 2026
Met at conference.

### February 2026
Follow-up call.

## Notes
"""
        result = parse_body_sections(body)

        assert "### January 2026" in result["Timeline"]
        assert "### February 2026" in result["Timeline"]
        assert len(result) == 2

    def test_parse_no_sections(self):
        """Body without ## headings returns empty dict."""
        body = "Just some text\nwithout any sections.\n"
        result = parse_body_sections(body)

        assert result == OrderedDict()

    def test_parse_content_before_first_section(self):
        """Content before first section is ignored."""
        body = """Some preamble text.

## First Section
Actual content.
"""
        result = parse_body_sections(body)

        assert len(result) == 1
        assert "First Section" in result
        assert "preamble" not in result.get("First Section", "")


class TestWriteBodySections:
    """Tests for write_body_sections()."""

    def test_write_empty_sections(self):
        """Empty dict produces empty string."""
        assert write_body_sections(OrderedDict()) == ""

    def test_write_single_section(self):
        """Single section is written correctly."""
        sections = OrderedDict([("Notes", "Some content.\n")])
        result = write_body_sections(sections)

        assert "## Notes" in result
        assert "Some content." in result

    def test_write_multiple_sections(self):
        """Multiple sections are written with proper formatting."""
        sections = OrderedDict([
            ("Timeline", "Entry 1.\n"),
            ("Notes", "Note text.\n"),
        ])
        result = write_body_sections(sections)

        assert "## Timeline" in result
        assert "## Notes" in result
        assert result.index("## Timeline") < result.index("## Notes")

    def test_write_preserves_order(self):
        """Section order is preserved in output."""
        sections = OrderedDict([("C", "c\n"), ("A", "a\n"), ("B", "b\n")])
        result = write_body_sections(sections)

        assert result.index("## C") < result.index("## A") < result.index("## B")


class TestRoundtrip:
    """Test that parse -> write produces equivalent output."""

    def test_roundtrip_simple(self):
        """Simple body survives roundtrip."""
        original = "## Timeline\nEntry.\n\n## Notes\nText.\n"
        sections = parse_body_sections(original)
        result = write_body_sections(sections)

        # Parse result should match original parsed
        assert parse_body_sections(result) == sections

    def test_roundtrip_complex(self):
        """Complex body with nested headings survives roundtrip."""
        original = """## To Discuss
- [ ] Item one (2026-01-11)
- [x] Item two (2026-01-08)

## Timeline
### January 2026
Met at conference.

### December 2025
Email exchange.

## Notes
Some notes about this person.
"""
        sections = parse_body_sections(original)
        result = write_body_sections(sections)
        reparsed = parse_body_sections(result)

        assert list(reparsed.keys()) == list(sections.keys())
        for key in sections:
            # Content should be equivalent (whitespace may differ slightly)
            assert sections[key].strip() == reparsed[key].strip()


class TestGetSection:
    """Tests for get_section()."""

    def test_get_existing_section(self):
        """Existing section content is returned."""
        body = "## Notes\nContent here.\n"
        result = get_section(body, "Notes")
        assert result == "Content here.\n"

    def test_get_missing_section(self):
        """Missing section returns None."""
        body = "## Notes\nContent.\n"
        result = get_section(body, "Timeline")
        assert result is None


class TestUpdateSection:
    """Tests for update_section()."""

    def test_update_existing_section(self):
        """Existing section content is replaced."""
        body = "## Notes\nOld content.\n"
        result = update_section(body, "Notes", "New content.\n")

        assert "New content" in result
        assert "Old content" not in result

    def test_update_preserves_other_sections(self):
        """Other sections are preserved when updating."""
        body = "## Timeline\nTimeline stuff.\n\n## Notes\nOld notes.\n"
        result = update_section(body, "Notes", "New notes.\n")

        assert "Timeline stuff" in result
        assert "New notes" in result
        assert "Old notes" not in result

    def test_update_missing_section_no_create(self):
        """Missing section is not created by default."""
        body = "## Notes\nContent.\n"
        result = update_section(body, "Timeline", "Entry.\n")

        assert "## Timeline" not in result

    def test_update_missing_section_create(self):
        """Missing section is created when requested."""
        body = "## Notes\nContent.\n"
        result = update_section(body, "Timeline", "Entry.\n", create_if_missing=True)

        assert "## Timeline" in result
        assert "Entry" in result


class TestPrependToSection:
    """Tests for prepend_to_section()."""

    def test_prepend_to_existing(self):
        """Content is added at start of section."""
        body = "## Notes\nExisting.\n"
        result = prepend_to_section(body, "Notes", "New first.\n")

        assert "New first" in result
        assert result.index("New first") < result.index("Existing")

    def test_prepend_preserves_existing(self):
        """Existing content is preserved."""
        body = "## Notes\nOld stuff.\n"
        result = prepend_to_section(body, "Notes", "New stuff.\n")

        assert "Old stuff" in result
        assert "New stuff" in result


class TestAppendToSection:
    """Tests for append_to_section()."""

    def test_append_to_existing(self):
        """Content is added at end of section."""
        body = "## Notes\nExisting.\n"
        result = append_to_section(body, "Notes", "New last.\n")

        assert "New last" in result
        assert result.index("Existing") < result.index("New last")

    def test_append_preserves_existing(self):
        """Existing content is preserved."""
        body = "## Notes\nOld stuff.\n"
        result = append_to_section(body, "Notes", "New stuff.\n")

        assert "Old stuff" in result
        assert "New stuff" in result


class TestEnsureSectionsExist:
    """Tests for ensure_sections_exist()."""

    def test_adds_missing_sections(self):
        """Missing sections are added."""
        body = "## Notes\nContent.\n"
        result = ensure_sections_exist(body, ["Timeline", "Notes"])

        assert "## Timeline" in result
        assert "## Notes" in result

    def test_preserves_existing_content(self):
        """Existing section content is preserved."""
        body = "## Notes\nImportant content.\n"
        result = ensure_sections_exist(body, ["Timeline", "Notes"])

        assert "Important content" in result

    def test_orders_sections_correctly(self):
        """Sections are ordered according to required list."""
        body = "## Notes\nContent.\n"
        result = ensure_sections_exist(body, ["To Discuss", "Timeline", "Notes"])

        # To Discuss should come first, then Timeline, then Notes
        assert result.index("## To Discuss") < result.index("## Timeline")
        assert result.index("## Timeline") < result.index("## Notes")


class TestEntityBodyConfig:
    """Tests for entity body configuration."""

    def test_person_config(self):
        """Person has correct sections."""
        sections = get_expected_sections("person")
        assert sections == ["To Discuss", "Timeline", "Notes"]

    def test_company_config(self):
        """Company has correct sections."""
        sections = get_expected_sections("company")
        assert sections == ["People", "Timeline", "Documents", "Notes"]

    def test_default_body_has_all_sections(self):
        """Default body includes all expected sections."""
        for entity_type, config in ENTITY_BODY_CONFIG.items():
            body = get_default_body(entity_type)
            for section in config["sections"]:
                assert f"## {section}" in body, f"{entity_type} missing {section}"

    def test_unknown_type_returns_empty(self):
        """Unknown entity type returns empty values."""
        assert get_expected_sections("unknown") == []
        assert get_default_body("unknown") == ""


class TestToDiscussItem:
    """Tests for ToDiscussItem dataclass."""

    def test_to_markdown_unchecked(self):
        """Unchecked item converts to markdown correctly."""
        item = ToDiscussItem(text="Call about project", completed=False, date_added="2026-01-11")
        assert item.to_markdown() == "- [ ] Call about project (2026-01-11)"

    def test_to_markdown_checked(self):
        """Checked item converts to markdown correctly."""
        item = ToDiscussItem(text="Send proposal", completed=True, date_added="2026-01-08")
        assert item.to_markdown() == "- [x] Send proposal (2026-01-08)"

    def test_to_markdown_no_date(self):
        """Item without date converts correctly."""
        item = ToDiscussItem(text="Quick note", completed=False)
        assert item.to_markdown() == "- [ ] Quick note"

    def test_from_markdown_unchecked(self):
        """Parse unchecked item from markdown."""
        item = ToDiscussItem.from_markdown("- [ ] Call about project (2026-01-11)")
        assert item is not None
        assert item.text == "Call about project"
        assert item.completed is False
        assert item.date_added == "2026-01-11"

    def test_from_markdown_checked(self):
        """Parse checked item from markdown."""
        item = ToDiscussItem.from_markdown("- [x] Send proposal (2026-01-08)")
        assert item is not None
        assert item.text == "Send proposal"
        assert item.completed is True
        assert item.date_added == "2026-01-08"

    def test_from_markdown_uppercase_x(self):
        """Parse item with uppercase X."""
        item = ToDiscussItem.from_markdown("- [X] Done item (2026-01-08)")
        assert item is not None
        assert item.completed is True

    def test_from_markdown_no_date(self):
        """Parse item without date."""
        item = ToDiscussItem.from_markdown("- [ ] Quick note")
        assert item is not None
        assert item.text == "Quick note"
        assert item.date_added is None

    def test_from_markdown_invalid(self):
        """Invalid format returns None."""
        assert ToDiscussItem.from_markdown("Not a checkbox") is None
        assert ToDiscussItem.from_markdown("- Regular bullet") is None
        assert ToDiscussItem.from_markdown("") is None

    def test_create_with_today(self):
        """Create method sets today's date."""
        from datetime import date
        item = ToDiscussItem.create("New item")
        assert item.text == "New item"
        assert item.completed is False
        assert item.date_added == date.today().isoformat()

    def test_roundtrip(self):
        """Item survives markdown roundtrip."""
        original = ToDiscussItem(text="Test item", completed=False, date_added="2026-01-11")
        markdown = original.to_markdown()
        parsed = ToDiscussItem.from_markdown(markdown)
        assert parsed is not None
        assert parsed.text == original.text
        assert parsed.completed == original.completed
        assert parsed.date_added == original.date_added


class TestParseToDiscussItems:
    """Tests for parse_to_discuss_items()."""

    def test_parse_empty(self):
        """Empty content returns empty list."""
        assert parse_to_discuss_items("") == []
        assert parse_to_discuss_items("   ") == []
        assert parse_to_discuss_items("\n\n") == []

    def test_parse_single_item(self):
        """Single item is parsed."""
        content = "- [ ] Call about project (2026-01-11)\n"
        items = parse_to_discuss_items(content)
        assert len(items) == 1
        assert items[0].text == "Call about project"

    def test_parse_multiple_items(self):
        """Multiple items are parsed in order."""
        content = """- [ ] Call about project (2026-01-11)
- [x] Send proposal (2026-01-08)
- [ ] Review feedback (2026-01-05)
"""
        items = parse_to_discuss_items(content)
        assert len(items) == 3
        assert items[0].text == "Call about project"
        assert items[0].completed is False
        assert items[1].text == "Send proposal"
        assert items[1].completed is True
        assert items[2].text == "Review feedback"

    def test_parse_ignores_non_checkbox_lines(self):
        """Non-checkbox lines are ignored."""
        content = """- [ ] Real item (2026-01-11)
Some random text
- Another bullet without checkbox
- [x] Another real item (2026-01-08)
"""
        items = parse_to_discuss_items(content)
        assert len(items) == 2
        assert items[0].text == "Real item"
        assert items[1].text == "Another real item"


class TestWriteToDiscussItems:
    """Tests for write_to_discuss_items()."""

    def test_write_empty(self):
        """Empty list returns empty string."""
        assert write_to_discuss_items([]) == ""

    def test_write_single_item(self):
        """Single item is written correctly."""
        items = [ToDiscussItem(text="Call about project", completed=False, date_added="2026-01-11")]
        result = write_to_discuss_items(items)
        assert result == "- [ ] Call about project (2026-01-11)\n"

    def test_write_multiple_items(self):
        """Multiple items are written with newlines."""
        items = [
            ToDiscussItem(text="Call about project", completed=False, date_added="2026-01-11"),
            ToDiscussItem(text="Send proposal", completed=True, date_added="2026-01-08"),
        ]
        result = write_to_discuss_items(items)
        assert "- [ ] Call about project (2026-01-11)\n" in result
        assert "- [x] Send proposal (2026-01-08)" in result

    def test_roundtrip(self):
        """Items survive write -> parse roundtrip."""
        original = [
            ToDiscussItem(text="Item one", completed=False, date_added="2026-01-11"),
            ToDiscussItem(text="Item two", completed=True, date_added="2026-01-08"),
        ]
        markdown = write_to_discuss_items(original)
        parsed = parse_to_discuss_items(markdown)
        assert len(parsed) == len(original)
        for orig, pars in zip(original, parsed):
            assert orig.text == pars.text
            assert orig.completed == pars.completed
            assert orig.date_added == pars.date_added
