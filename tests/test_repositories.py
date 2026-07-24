"""Tests for repository layer."""

import pytest
import tempfile
from pathlib import Path

from obsidian_schemas import (
    PersonRepository, CompanyRepository, BookRepository, MeetingRepository,
    Person, Company, Book, Meeting
)
from obsidian_schemas.name_validation import NameValidationError, WeakIdentityError
from obsidian_schemas.errors import FrontmatterParseError


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

        # Create people for substring-match testing
        (vault / "@Sandy Forster.md").write_text("""---
type: person
name: Sandy Forster
company: Motability
tags:
  - person
created: "2025-06-01"
---

## Timeline
""")

        (vault / "@Fred Ellis.md").write_text("""---
type: person
name: Fred Ellis
company: Acme Corp
tags:
  - person
created: "2025-06-01"
---

## Timeline
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
        assert len(repo) == 4

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

    def test_resolve_rejects_substring_andy(self, temp_vault):
        """Test that 'andy' does NOT match 'Sandy Forster'."""
        repo = PersonRepository(temp_vault)
        person = repo.resolve("andy")
        assert person is None

    def test_resolve_rejects_substring_ed(self, temp_vault):
        """Test that 'ed' does NOT match 'Fred Ellis'."""
        repo = PersonRepository(temp_vault)
        person = repo.resolve("ed")
        assert person is None

    def test_resolve_whole_word_sandy(self, temp_vault):
        """Test that 'sandy' matches 'Sandy Forster' (exact first name)."""
        repo = PersonRepository(temp_vault)
        person = repo.resolve("sandy")
        assert person is not None
        assert person.name == "Sandy Forster"

    def test_resolve_whole_word_fred(self, temp_vault):
        """Test that 'fred' matches 'Fred Ellis' (exact first name)."""
        repo = PersonRepository(temp_vault)
        person = repo.resolve("fred")
        assert person is not None
        assert person.name == "Fred Ellis"

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
        assert len(people) == 2
        names = {p.name for p in people}
        assert names == {"John Smith", "Fred Ellis"}

    def test_get_all(self, temp_vault):
        """Test getting all persons."""
        repo = PersonRepository(temp_vault)
        all_people = repo.get_all()
        assert len(all_people) == 4
        names = {p.name for p in all_people}
        assert names == {"John Smith", "Jane Doe", "Sandy Forster", "Fred Ellis"}

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

    # ──────────────────────────────────────────────────────────────────
    # WI-017: defensive RFC 2822 parse in create_stub
    # ──────────────────────────────────────────────────────────────────
    # Surfaced 2026-06-01: production vault contains 62 person notes with
    # corrupted names like `David Agmen-Smith davidasspeechmaticscom` —
    # produced when a caller passes the raw email sender field
    # (`"Name <email@domain>"`) to create_stub(name=...) and the regex
    # sanitizer at person.py:380 strips `<`, `>`, `@`, `.`. The defensive
    # fix detects RFC 2822 form via email.utils.parseaddr and splits
    # cleanly. These tests pin every Edge Case row from the spec.

    def test_create_stub_rfc2822_name_with_email_in_angle_brackets(self, temp_vault):
        """Caller passes 'Display Name <email>' — split cleanly."""
        repo = PersonRepository(temp_vault)
        person = repo.create_stub(name="David Smith <ds@example.com>")
        assert person.name == "David Smith"
        assert person.emails == ["ds@example.com"]
        # Filename uses only the clean name
        assert (temp_vault / "@David Smith.md").exists()
        # The corrupted form must NOT exist
        assert not (temp_vault / "@David Smith dsexamplecom.md").exists()

    def test_create_stub_rfc2822_email_only_in_angle_brackets(self, temp_vault):
        """No display name, only '<email>' — fall back to email local-part."""
        repo = PersonRepository(temp_vault)
        person = repo.create_stub(name="<ds@example.com>")
        assert person.name == "ds"
        assert person.emails == ["ds@example.com"]

    def test_create_stub_bare_email_as_name(self, temp_vault):
        """Caller passes a bare email as name — use local-part as name + email."""
        repo = PersonRepository(temp_vault)
        person = repo.create_stub(name="ds@example.com")
        assert person.name == "ds"
        assert person.emails == ["ds@example.com"]

    def test_create_stub_quoted_display_name_with_comma(self, temp_vault):
        """RFC 2822 quoted display name (e.g. 'Doe, Jane') — quotes + comma preserved in name."""
        repo = PersonRepository(temp_vault)
        person = repo.create_stub(name='"Doe, Jane" <jane@example.com>')
        # parseaddr returns 'Doe, Jane'. WI-111: the legacy re.sub (which used
        # to strip the comma) is deleted, so the comma is now preserved — a
        # comma is path-safe and validate_strict accepts it. The email is still
        # split out cleanly.
        assert "Doe" in person.name and "Jane" in person.name
        assert person.emails == ["jane@example.com"]
        # No '@' or domain should leak into the name
        assert "@" not in person.name
        assert "example" not in person.name

    def test_create_stub_phone_string_unchanged(self, temp_vault):
        """Phone-only stub (WI-083) must still work — `@` check prevents misfire."""
        repo = PersonRepository(temp_vault)
        person = repo.create_stub(name="+447739341679", phone="+447739341679")
        # WI-111: legacy re.sub deleted → the '+' is preserved (canonical E.164,
        # and what the validator's phone-sentinel path returns). Phone dedup is
        # on the normalized phone index (strips '+'), so this is duplicate-safe.
        assert person.name == "+447739341679"
        assert person.phones == ["+447739341679"]
        assert person.emails == []  # no email derived from phone

    def test_create_stub_plain_name_unchanged(self, temp_vault):
        """Plain name with no email syntax must still work — no-op for the new parse."""
        repo = PersonRepository(temp_vault)
        person = repo.create_stub(name="David Smith", email="ds@example.com", company="Acme")
        assert person.name == "David Smith"
        assert person.emails == ["ds@example.com"]
        assert person.company == "Acme"

    def test_create_stub_explicit_email_arg_wins_over_rfc2822(self, temp_vault):
        """If caller passes both RFC 2822 name AND a separate email, the explicit email wins."""
        repo = PersonRepository(temp_vault)
        person = repo.create_stub(
            name="David Smith <ds@example.com>",
            email="other@example.com",  # explicit arg
        )
        assert person.name == "David Smith"
        assert person.emails == ["other@example.com"]  # explicit arg wins

    def test_create_stub_empty_name_fallback_preserved(self, temp_vault):
        """Empty name with email — preserve existing fallback to email local-part."""
        repo = PersonRepository(temp_vault)
        person = repo.create_stub(name="", email="ds@example.com")
        assert person.name == "ds"
        assert person.emails == ["ds@example.com"]

    def test_create_stub_broken_angle_brackets_no_at_sign(self, temp_vault):
        """If <...> contents don't contain '@', leave the name alone and let
        existing regex sanitizer handle it. Guards against false positives."""
        repo = PersonRepository(temp_vault)
        person = repo.create_stub(name="David Smith <not-an-email>")
        # parseaddr returns ("David Smith", "not-an-email") — but our '@' check
        # rejects, so the regex sanitizer runs on the full string.
        # Just verify '@' didn't leak; exact name shape is whatever the regex emits.
        assert "@" not in person.name
        assert person.emails == []

    # ──────────────────────────────────────────────────────────────────
    # WI-111: single name authority — clean()'s output stored verbatim,
    # legacy re.sub mangler deleted (Decision 6 / Phase 1B)
    # ──────────────────────────────────────────────────────────────────

    def test_create_stub_preserves_apostrophe(self, temp_vault):
        """O'Brien must keep its apostrophe — the deleted re.sub stripped it."""
        repo = PersonRepository(temp_vault)
        person = repo.create_stub(name="Owen O'Brien")
        assert person.name == "Owen O'Brien"
        assert (temp_vault / "@Owen O'Brien.md").exists()

    def test_create_stub_preserves_period(self, temp_vault):
        """Dr. Smith must keep its period — the deleted re.sub stripped it."""
        repo = PersonRepository(temp_vault)
        person = repo.create_stub(name="Dr. Smith")
        assert person.name == "Dr. Smith"

    def test_create_stub_preserves_accents(self, temp_vault):
        repo = PersonRepository(temp_vault)
        person = repo.create_stub(name="José García")
        assert person.name == "José García"

    def test_create_stub_rejects_arrow_descriptor(self, temp_vault):
        """WI-111 falsification: the 2026-06-06 case must now RAISE, not write
        a corrupted note. Previously PASSED clean() then re.sub manufactured
        'Dave - Thomas Gatten Adzact'."""
        repo = PersonRepository(temp_vault)
        with pytest.raises(NameValidationError):
            repo.create_stub(name="Dave -> Thomas Gatten (Adzact)")
        # No file written for the rejected name.
        assert not any(temp_vault.glob("@Dave*.md"))

    def test_create_stub_rejects_me_to_colon_descriptor(self, temp_vault):
        """WI-111 falsification: the other 2026-06-06 case."""
        repo = PersonRepository(temp_vault)
        with pytest.raises(NameValidationError):
            repo.create_stub(name="Me to: David Field")

    def test_find_or_create_stub_rejects_descriptor(self, temp_vault):
        """The dedupe-aware entry point must also reject (it falls through to
        create_stub on Strategy 3)."""
        repo = PersonRepository(temp_vault)
        with pytest.raises(NameValidationError):
            repo.find_or_create_stub(name="Dave -> Thomas Gatten (Adzact)")

    def test_create_stub_with_phone(self, temp_vault):
        """Test creating a phone-only stub (WI-083: phone-only contact path).

        When a contact arrives via a phone-only channel (iMessage, WhatsApp
        @lid without profile name), the caller passes the phone string as
        both `name` and `phone` so the stub is identifiable until enrichment
        confirms a real name.
        """
        repo = PersonRepository(temp_vault)
        person = repo.create_stub(
            name="+447739341679",
            phone="+447739341679",
        )

        # Phone landed on the record so future enricher can find it.
        assert person.phones == ["+447739341679"]
        assert person.emails == []

        # Filename: WI-111 deleted the re.sub that stripped '+', so the file is
        # named with the verbatim validated name.
        assert (temp_vault / "@+447739341679.md").exists()

        # Phone-indexed lookup resolves the new stub.
        looked_up = repo.get_by_phone("+447739341679")
        assert looked_up is not None
        assert looked_up.phones == ["+447739341679"]

    # ==================== WI-109 — field-level RFC 2822 normalization ====================

    def test_save_normalizes_rfc2822_in_emails(self, temp_vault):
        """WI-109: emails containing raw 'Name <email>' RFC 2822 strings get
        cleaned at save time. The display-name part lands in aliases.

        Real production case: 'Ed <edwardcu@mo.co.uk>' was preserved in
        Person.emails[] as-is, breaking exact-email-match in dedupe.
        """
        from obsidian_schemas import Person
        repo = PersonRepository(temp_vault)
        person = Person(
            name="Ed Curwen",
            emails=["Ed <edwardcu@mo.co.uk>"],
            aliases=[],
            tags=["person"],
        )
        repo.save(person)

        reloaded = repo.get("Ed Curwen")
        # Email field now contains just the clean address
        assert reloaded.emails == ["edwardcu@mo.co.uk"]
        # Display-name "Ed" landed in aliases (so it's still findable by lookup)
        assert "Ed" in reloaded.aliases

    def test_save_normalizes_parens_form(self, temp_vault):
        """Some producers wrap email in parens: 'Name (email)'."""
        from obsidian_schemas import Person
        repo = PersonRepository(temp_vault)
        person = Person(
            name="Ewan Long",
            emails=["Ewan Long (ewan.long@royallondon.com)"],
            tags=["person"],
        )
        repo.save(person)

        reloaded = repo.get("Ewan Long")
        assert reloaded.emails == ["ewan.long@royallondon.com"]
        assert "Ewan Long" in reloaded.aliases

    def test_save_preserves_clean_emails_unchanged(self, temp_vault):
        """Non-corrupted emails pass through untouched."""
        from obsidian_schemas import Person
        repo = PersonRepository(temp_vault)
        person = Person(
            name="Clean Person",
            emails=["clean@example.com"],
            tags=["person"],
        )
        repo.save(person)

        reloaded = repo.get("Clean Person")
        assert reloaded.emails == ["clean@example.com"]
        # No spurious alias additions
        assert reloaded.aliases == ["clean@example.com"] or reloaded.aliases == []

    def test_save_dedups_email_after_normalization(self, temp_vault):
        """If a record has BOTH 'Name <foo>' AND 'foo' in emails, normalization
        produces 'foo' twice; the result must dedupe so we don't get duplicates."""
        from obsidian_schemas import Person
        repo = PersonRepository(temp_vault)
        person = Person(
            name="Dup Email Person",
            emails=["Dup <dup@example.com>", "dup@example.com"],
            tags=["person"],
        )
        repo.save(person)

        reloaded = repo.get("Dup Email Person")
        # Only one entry, the clean form
        assert reloaded.emails == ["dup@example.com"]

    def test_save_does_not_extract_display_name_if_no_angle_brackets(self, temp_vault):
        """An email like 'foo@bar.com' alone — no display name to extract."""
        from obsidian_schemas import Person
        repo = PersonRepository(temp_vault)
        person = Person(
            name="Plain Email",
            emails=["bare@example.com"],
            aliases=[],
            tags=["person"],
        )
        repo.save(person)

        reloaded = repo.get("Plain Email")
        # No spurious alias from parseaddr (display-name part is empty)
        assert reloaded.emails == ["bare@example.com"]
        assert "bare@example.com" not in reloaded.aliases or len(reloaded.aliases) == 0

    def test_save_handles_aliases_list_with_rfc2822(self, temp_vault):
        """Aliases can also carry RFC 2822 corruption — same normalization."""
        from obsidian_schemas import Person
        repo = PersonRepository(temp_vault)
        person = Person(
            name="Alias Test",
            aliases=["Alias Holder <alias@example.com>"],
            tags=["person"],
        )
        repo.save(person)

        reloaded = repo.get("Alias Test")
        # Email extracted to emails[]
        assert "alias@example.com" in reloaded.emails
        # Original alias-with-angle replaced by the clean display name OR clean email
        for a in reloaded.aliases:
            assert "<" not in a and ">" not in a

    def test_refresh(self, temp_vault):
        """Test refreshing the cache."""
        repo = PersonRepository(temp_vault)
        assert len(repo) == 4

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
        assert len(repo) == 5

    def test_refresh_refuses_to_clobber_when_load_returns_zero(self, temp_vault, monkeypatch):
        """If load() returns 0 while cache has entries, refresh must not wipe state.

        Guards against the macOS TCC/Full Disk Access edge case where
        Path.glob silently returns [] on a vault that previously loaded fine.
        """
        repo = PersonRepository(temp_vault)
        original_count = len(repo)
        assert original_count > 0

        # Pin one entity so we can verify identity-preservation, not just count.
        original_john = repo.get("John Smith")
        assert original_john is not None

        # Verify email index is populated before refresh.
        assert repo.get_by_email("john@example.com") is not None

        # Simulate the TCC failure mode: glob returns empty.
        monkeypatch.setattr(
            type(repo.vault_path),
            "glob",
            lambda self, pattern: iter([]),
        )

        result = repo.refresh()

        assert result == -1, "refresh() should return -1 when refusing to clobber"
        assert len(repo) == original_count, "cache must be preserved"
        assert repo.get("John Smith") is original_john, "entity identity preserved"
        # Indexes must be rebuilt after the refusal.
        assert repo.get_by_email("john@example.com") is not None

    def test_refresh_allows_legitimate_zero_when_cache_empty(self, temp_vault):
        """If both load and existing cache are empty, refresh returns 0 normally."""
        repo = PersonRepository(temp_vault, auto_load=False)
        # Don't load. Cache is empty.
        result = repo.refresh()
        # The vault has files, so load will populate. But validate the
        # empty-cache-empty-load path explicitly:
        empty_vault = temp_vault.parent / "empty_vault"
        empty_vault.mkdir(exist_ok=True)
        empty_repo = PersonRepository(empty_vault, auto_load=False)
        assert empty_repo.refresh() == 0

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

    # ──────────────────────────────────────────────────────────────────
    # WI-111 Phase 1: append_to_body_section (generic body-section writer)
    # ──────────────────────────────────────────────────────────────────

    def _write_multi_section_person(self, vault, name="Sören Winter"):
        """Write a realistic multi-section person note (real-data-shaped:
        accented name, populated frontmatter, Timeline + Notes sections)."""
        path = vault / f"@{name}.md"
        path.write_text(
            "---\n"
            "type: person\n"
            f"name: {name}\n"
            "emails:\n"
            "  - soren@example.de\n"
            "company: Beispiel GmbH\n"
            "tags:\n"
            "  - person\n"
            'created: "2025-03-01"\n'
            "---\n\n"
            "## Timeline\n\n"
            "### March 1, 2025\n[[Intro]] — first contact.\n\n"
            "## Notes\n\n"
            "- Prefers email.\n",
            encoding="utf-8",
        )
        return path

    def test_append_to_body_section_new_section_append(self, temp_vault):
        repo = PersonRepository(temp_vault)
        person = repo.get("John Smith")  # has Timeline only
        ok = repo.append_to_body_section(person, "Notes", "- Likes coffee.\n")
        assert ok is True
        content = (temp_vault / "@John Smith.md").read_text()
        assert "## Notes" in content
        assert "Likes coffee" in content

    def test_append_to_body_section_new_section_prepend(self, temp_vault):
        repo = PersonRepository(temp_vault)
        person = repo.get("John Smith")
        ok = repo.append_to_body_section(
            person, "Notes", "- Newest.\n", operation="prepend"
        )
        assert ok is True
        assert "Newest" in (temp_vault / "@John Smith.md").read_text()

    def test_append_to_body_section_existing_section_append(self, temp_vault):
        path = self._write_multi_section_person(temp_vault)
        repo = PersonRepository(temp_vault)
        person = repo.get("Sören Winter")
        ok = repo.append_to_body_section(person, "Notes", "- Second note.\n")
        assert ok is True
        body = path.read_text()
        # Appended AFTER the existing note.
        assert body.index("Prefers email") < body.index("Second note")

    def test_append_to_body_section_existing_section_prepend(self, temp_vault):
        path = self._write_multi_section_person(temp_vault)
        repo = PersonRepository(temp_vault)
        person = repo.get("Sören Winter")
        ok = repo.append_to_body_section(
            person, "Notes", "- Top note.\n", operation="prepend"
        )
        assert ok is True
        body = path.read_text()
        assert body.index("Top note") < body.index("Prefers email")

    def test_append_to_body_section_dedupe_hit_skips(self, temp_vault):
        path = self._write_multi_section_person(temp_vault)
        repo = PersonRepository(temp_vault)
        person = repo.get("Sören Winter")
        key = "Introduced by [[Dave]]"
        assert repo.append_to_body_section(
            person, "Notes", f"- {key}\n", deduplicate_key=key
        ) is True
        # Second identical append with the same key is skipped.
        assert repo.append_to_body_section(
            person, "Notes", f"- {key}\n", deduplicate_key=key
        ) is False
        assert path.read_text().count(key) == 1

    def test_append_to_body_section_dedupe_is_section_scoped(self, temp_vault):
        """The key correctness proof: a deduplicate_key present in Timeline must
        NOT suppress an append of the same key to Notes (section-scoped, not
        whole-file — unlike append_to_timeline)."""
        path = self._write_multi_section_person(temp_vault)
        repo = PersonRepository(temp_vault)
        person = repo.get("Sören Winter")
        key = "Introduced by [[Dave]]"
        # Put the key in Timeline first.
        assert repo.append_to_body_section(person, "Timeline", f"{key}\n") is True
        # Same key into Notes must still be written (different section).
        assert repo.append_to_body_section(
            person, "Notes", f"- {key}\n", deduplicate_key=key
        ) is True
        content = path.read_text()
        assert content.count(key) == 2

    def test_append_to_body_section_create_if_missing_false_noop(self, temp_vault):
        repo = PersonRepository(temp_vault)
        person = repo.get("John Smith")  # no Notes section
        ok = repo.append_to_body_section(
            person, "Notes", "- nope.\n", create_if_missing=False
        )
        assert ok is False
        assert "## Notes" not in (temp_vault / "@John Smith.md").read_text()

    def test_append_to_body_section_preserves_frontmatter_and_other_sections(self, temp_vault):
        """Body-preservation: frontmatter bytes + all OTHER sections untouched;
        only the target section changes."""
        path = self._write_multi_section_person(temp_vault)
        original = path.read_text()
        original_frontmatter = original.split("---", 2)[1]
        repo = PersonRepository(temp_vault)
        person = repo.get("Sören Winter")
        repo.append_to_body_section(person, "Notes", "- Added.\n")
        after = path.read_text()
        # Frontmatter byte-identical.
        assert after.split("---", 2)[1] == original_frontmatter
        # Timeline section untouched.
        assert "### March 1, 2025" in after
        assert "[[Intro]] — first contact." in after
        # Accented name preserved.
        assert "name: Sören Winter" in after

    def test_append_to_body_section_missing_file_raises(self, temp_vault):
        repo = PersonRepository(temp_vault)
        fake = Person(name="Ghost Person", type="person")
        with pytest.raises(ValueError, match="not found"):
            repo.append_to_body_section(fake, "Notes", "- x\n")

    def test_append_to_body_section_no_frontmatter_fence_raises(self, temp_vault):
        # Write WITH frontmatter so the note loads into the cache (get_file_path
        # resolves), then externally strip the fence — simulates a note edited
        # out-of-band between load and write.
        #
        # WI-020 AC-5 Predicate 2: the fence guard raised a silent False, which
        # a caller could not tell from "nothing to do". It now refuses loudly —
        # the caller's payload is never dropped without a signal.
        path = temp_vault / "@Nofence Person.md"
        path.write_text(
            "---\ntype: person\nname: Nofence Person\ntags:\n  - person\n---\n\n## Notes\n",
            encoding="utf-8",
        )
        repo = PersonRepository(temp_vault)
        person = repo.get("Nofence Person")
        # Now corrupt the on-disk file: remove the frontmatter fence.
        path.write_text("## Notes\n\n- no frontmatter here\n", encoding="utf-8")
        with pytest.raises(FrontmatterParseError):
            repo.append_to_body_section(person, "Notes", "- x\n")

    def test_append_to_body_section_invalid_operation_raises(self, temp_vault):
        """Loud-fail: an unknown operation must raise, not silently append."""
        repo = PersonRepository(temp_vault)
        person = repo.get("John Smith")
        with pytest.raises(ValueError, match="operation"):
            repo.append_to_body_section(person, "Notes", "- x\n", operation="insert")

    # ──────────────────────────────────────────────────────────────────
    # WI-018: resolve_all() — multi-candidate ranked resolve
    # ──────────────────────────────────────────────────────────────────
    # Surfaced 2026-06-01 from orchestrator Phase 0 trace. Today at 14:05
    # BST the exocortex Granola ingester created @Naomi Pavie.md as a
    # duplicate of the existing canonical @Naomi Pavie Speechmatics.md,
    # because PersonRepository.resolve("Naomi Pavie") failed to find the
    # canonical (whose cache key is "naomi pavie speechmatics", not
    # "naomi pavie"). resolve_all is the new multi-candidate, ranked,
    # company-hint-aware lookup that fixes this class.
    #
    # Each test pins one production-grade scenario.

    def test_resolve_all_exact_name_returns_single_candidate(self, temp_vault):
        """Exact name match should return the canonical at confidence 1.0."""
        repo = PersonRepository(temp_vault)
        candidates = repo.resolve_all("John Smith")
        assert len(candidates) >= 1
        assert candidates[0].person.name == "John Smith"
        assert candidates[0].confidence == 1.0
        assert candidates[0].matched_via in ("exact-name", "alias")

    def test_resolve_all_email_match_returns_canonical_at_1_0(self, temp_vault):
        """Email match should return canonical at 1.0."""
        repo = PersonRepository(temp_vault)
        candidates = repo.resolve_all("john@example.com")
        assert candidates
        assert candidates[0].person.name == "John Smith"
        assert candidates[0].confidence == 1.0
        assert candidates[0].matched_via == "email"

    def test_resolve_all_no_match_returns_empty_list(self, temp_vault):
        """Query that matches nothing returns []."""
        repo = PersonRepository(temp_vault)
        assert repo.resolve_all("Nobody Here") == []

    def test_resolve_all_naomi_pavie_production_case(self, temp_vault):
        """The smoking-gun case from Phase 0 trace.

        Set up: a canonical record named 'Naomi Pavie Speechmatics' (mimicking
        @Naomi Pavie Speechmatics.md). When the Granola ingester sees a new
        meeting attendee 'Naomi Pavie' and calls resolve_all('Naomi Pavie'),
        it must return the canonical with high-enough confidence to reuse.
        Optional company hint should bump confidence further.
        """
        repo = PersonRepository(temp_vault)
        repo.create_stub(name="Naomi Pavie Speechmatics", company="")  # mangled-name canonical

        # Without company hint — token-subset match should still find her
        candidates = repo.resolve_all("Naomi Pavie")
        assert candidates, "resolve_all should find Naomi via token-subset"
        assert candidates[0].person.name == "Naomi Pavie Speechmatics"
        assert candidates[0].confidence >= 0.65
        assert candidates[0].matched_via in ("token-subset", "partial-name")

        # With company hint — confidence bumps to ≥ 0.85
        candidates_hinted = repo.resolve_all("Naomi Pavie", company="Speechmatics")
        assert candidates_hinted[0].confidence >= 0.85, (
            f"company-hint should bump confidence; got {candidates_hinted[0].confidence}"
        )

    def test_resolve_all_lorna_armstrong_production_case(self, temp_vault):
        """Inverse: canonical is 'Lorna Armstrong' (clean), and a new scanner
        observes 'Lorna Armstrong Speechmatics'. resolve_all should match."""
        repo = PersonRepository(temp_vault)
        repo.create_stub(name="Lorna Armstrong", email="lorna@speechmatics.com", company="Speechmatics")

        candidates = repo.resolve_all("Lorna Armstrong Speechmatics")
        assert candidates, "resolve_all should find Lorna via token-subset (inverse direction)"
        assert candidates[0].person.name == "Lorna Armstrong"
        assert candidates[0].confidence >= 0.65

    def test_resolve_all_emily_m_short_form_with_company_hint(self, temp_vault):
        """The 'Emily M' case — 2-token query, canonical is 'Emily Mendes'.
        Without company hint: returns at partial-name confidence (≥0.6 acceptable).
        With company hint matching: bumps to ≥0.85 → reuse."""
        repo = PersonRepository(temp_vault)
        repo.create_stub(name="Emily Mendes", email="emily@speechmatics.com", company="Speechmatics")

        # "Emily M" — short form, only 2 chars on the last token; needs a
        # smarter strategy than pure exact/token-subset
        candidates_hinted = repo.resolve_all("Emily M", company="Speechmatics")
        assert candidates_hinted, "resolve_all + company hint should find Emily Mendes from 'Emily M'"
        assert candidates_hinted[0].person.name == "Emily Mendes"
        assert candidates_hinted[0].confidence >= 0.85

    def test_resolve_all_returns_ranked_list(self, temp_vault):
        """When multiple candidates match, they come back ranked by confidence."""
        repo = PersonRepository(temp_vault)
        repo.create_stub(name="Emily Mendes", email="emily@speechmatics.com", company="Speechmatics")
        repo.create_stub(name="Emily Marshall", company="Acme")

        # Query "Emily" should match both, ranked
        candidates = repo.resolve_all("Emily")
        assert len(candidates) >= 2
        # Confidences must be non-increasing
        for i in range(len(candidates) - 1):
            assert candidates[i].confidence >= candidates[i + 1].confidence

    def test_resolve_all_phone_match(self, temp_vault):
        """Phone matches return at 1.0."""
        repo = PersonRepository(temp_vault)
        candidates = repo.resolve_all("+447990558521")
        assert candidates
        assert candidates[0].person.name == "John Smith"
        assert candidates[0].confidence == 1.0
        assert candidates[0].matched_via == "phone"

    def test_resolve_all_empty_query_returns_empty(self, temp_vault):
        """Defensive: empty / None / whitespace query returns []."""
        repo = PersonRepository(temp_vault)
        assert repo.resolve_all("") == []
        assert repo.resolve_all("   ") == []

    # ──────────────────────────────────────────────────────────────────
    # WI-019: find_or_create_stub() — lookup-before-create entry point
    # ──────────────────────────────────────────────────────────────────
    # Built on resolve_all. Becomes the canonical entry point for ALL
    # stub-creating callers (orchestrator contact_normalizer, contact-
    # detector role, HAL9000 entities, exocortex Granola ingester).
    # Returns (person, created_new: bool). Optionally writes back newly-
    # observed identifiers to the canonical record when reusing.

    def test_find_or_create_stub_creates_new_when_no_match(self, temp_vault):
        """No existing match → creates new stub."""
        repo = PersonRepository(temp_vault)
        person, created = repo.find_or_create_stub(
            name="Brand New Contact",
            email="brand.new@example.com",
        )
        assert created is True
        assert person.name == "Brand New Contact"
        assert person.emails == ["brand.new@example.com"]

    def test_find_or_create_stub_reuses_via_email(self, temp_vault):
        """Existing person found by email → reuse, no new file."""
        repo = PersonRepository(temp_vault)
        person, created = repo.find_or_create_stub(
            name="J Smith",
            email="john@example.com",  # John Smith's email from fixture
        )
        assert created is False
        assert person.name == "John Smith"

    def test_find_or_create_stub_reuses_via_resolve_all_naomi(self, temp_vault):
        """The Naomi Pavie production case — exocortex Granola ingester scenario.

        Pre-existing canonical: @Naomi Pavie Speechmatics.md (mangled, no email).
        New caller: find_or_create_stub('Naomi Pavie', email='naomi@speechmatics.com', company='Speechmatics')
        Expected: REUSE the canonical (not create @Naomi Pavie.md duplicate).
        """
        repo = PersonRepository(temp_vault)
        repo.create_stub(name="Naomi Pavie Speechmatics", company="")  # mangled canonical with empty email

        person, created = repo.find_or_create_stub(
            name="Naomi Pavie",
            email="naomi.pavie@speechmatics.com",
            company="Speechmatics",
        )
        assert created is False, (
            "Should REUSE existing canonical 'Naomi Pavie Speechmatics' — this is the WI-103 acceptance gate"
        )
        assert person.name == "Naomi Pavie Speechmatics"

    def test_find_or_create_stub_writes_back_new_email(self, temp_vault):
        """On reuse, if the call supplied a new identifier not on the canonical
        record, append it (write-back). Future lookups now have stronger signal."""
        repo = PersonRepository(temp_vault)
        repo.create_stub(name="Naomi Pavie Speechmatics", company="")  # no email
        person, created = repo.find_or_create_stub(
            name="Naomi Pavie",
            email="naomi.pavie@speechmatics.com",
            company="Speechmatics",
        )
        assert created is False
        # Re-fetch from repo to see the written-back state
        canonical = repo.get("Naomi Pavie Speechmatics")
        assert canonical is not None
        assert "naomi.pavie@speechmatics.com" in canonical.emails, (
            f"write-back should have appended new email; canonical.emails = {canonical.emails}"
        )

    def test_find_or_create_stub_respects_confidence_threshold(self, temp_vault):
        """A weak match (e.g., shared first name only, no other signal) should
        NOT be treated as a reuse — better to create a new stub than wrongly merge."""
        repo = PersonRepository(temp_vault)
        repo.create_stub(name="Emily Mendes", email="emily@speechmatics.com", company="Speechmatics")

        # Calling with just "Emily" + no company hint shouldn't merge with Emily Mendes
        # (could be a different Emily). Better to create a new stub.
        person, created = repo.find_or_create_stub(
            name="Emily Watson",  # different last name
            email="emily.watson@example.com",
        )
        assert created is True, "Different person — should create new stub, not merge"
        assert person.name == "Emily Watson"


class TestFindOrCreateStubWI117:
    """WI-117 trap set — harden find_or_create_stub against NEW duplicates.

    Two new behaviours, both at this door:
      1. Corroborated name-cleaning before lookup ('Darryl Friend Kato' →
         'Darryl Friend' when corroborated → exact-match reuse), WITHOUT
         wrong-merging the uncorroborated 'Emma Roberts Kato'.
      2. Weak-identity guard: bare single-token-no-id + social-handle auto-creates
         raise WeakIdentityError instead of minting a probable duplicate.

    These are real-data shapes (Darryl Friend coaching client; Naomi Pavie /
    Speechmatics; the Emma namesake hazard the handoff flagged as the #1 risk).
    """

    # ── Gate 2: Darryl-class reuse via corroborated cleaning → exact match ──

    def test_company_suffix_cleaned_then_exact_match_reuses_via_email(self, temp_vault):
        """'Darryl Friend Kato' + @kato.app → clean to 'Darryl Friend' (email-
        domain corroborates 'Kato') → exact-name match (1.0) → REUSE. No new note.
        The canonical has NO email, so the win MUST come from cleaning→exact-match
        (not from a Strategy-1 email short-circuit)."""
        repo = PersonRepository(temp_vault)
        repo.create_stub(name="Darryl Friend", company="Kato")  # seeds 'Kato'; no email

        person, created = repo.find_or_create_stub(
            name="Darryl Friend Kato",
            email="darryl@kato.app",  # domain 'kato' corroborates the strip
        )
        assert created is False, "should reuse 'Darryl Friend' via cleaned-query exact match"
        assert person.name == "Darryl Friend"

    def test_company_suffix_cleaned_via_company_arg_reuses(self, temp_vault):
        """Same win via the company= corroboration branch (the meeting path has
        no email but does pass company)."""
        repo = PersonRepository(temp_vault)
        repo.create_stub(name="Darryl Friend", company="Kato")

        person, created = repo.find_or_create_stub(
            name="Darryl Friend Kato",
            company="Kato",  # company== corroborates the strip
        )
        assert created is False
        assert person.name == "Darryl Friend"

    # ── Gate 3: weak-identity refusal ──

    def test_bare_first_name_no_id_raises_weak_identity(self, temp_vault):
        """A bare 'Darryl' with no email/phone, auto_created, no match → refuse.
        Can't tell WHICH Darryl; almost certainly a thin mention of an existing
        canonical, so don't mint @Darryl.md."""
        repo = PersonRepository(temp_vault)
        repo.create_stub(name="Darryl Friend", company="Kato")  # a Darryl exists, but bare won't merge

        with pytest.raises(WeakIdentityError) as exc:
            repo.find_or_create_stub(name="Darryl", auto_created=True)
        assert exc.value.reason == "single-name, no email"
        # No note written.
        assert repo.get("Darryl") is None

    def test_social_handle_raises_weak_identity(self, temp_vault):
        """A social handle ('darryl_f') is not a name — refuse the auto-create."""
        repo = PersonRepository(temp_vault)
        with pytest.raises(WeakIdentityError) as exc:
            # email present so the handle branch (case 2) fires distinctly
            repo.find_or_create_stub(name="darryl_f", email="x@y.com", auto_created=True)
        assert exc.value.reason == "social handle pattern: darryl_f"

    def test_weak_identity_guard_skipped_when_not_auto_created(self, temp_vault):
        """Manual creates (auto_created=False) are NEVER refused — Dave can mint
        a single-name note by hand."""
        repo = PersonRepository(temp_vault)
        person, created = repo.find_or_create_stub(name="Cher", auto_created=False)
        assert created is True
        assert person.name == "Cher"

    # ── Gate 4: email-corroborated creation strips company from the NAME ──

    def test_creates_with_company_stripped_from_name_when_no_canonical(self, temp_vault):
        """'Naomi Pavie Speechmatics' + @speechmatics.com, NO existing canonical →
        create '@Naomi Pavie.md' (company stripped from the name), company field
        set to 'Speechmatics'."""
        repo = PersonRepository(temp_vault)
        # Seed 'Speechmatics' into known-companies without creating a Naomi.
        repo.create_stub(name="Someone Else", company="Speechmatics")

        person, created = repo.find_or_create_stub(
            name="Naomi Pavie Speechmatics",
            email="naomi.pavie@speechmatics.com",
            company="Speechmatics",
        )
        assert created is True
        assert person.name == "Naomi Pavie", "company token should be stripped from the created name"
        assert person.company == "Speechmatics"

    # ── Gate 5 + the #1 wrong-merge hazard: no surname/namesake corruption ──

    def test_surname_equal_company_word_not_stripped(self, temp_vault):
        """'Emma Kato' (2 tokens, no corroboration) is created VERBATIM — the
        2-token guard + conservative-keep means a surname that happens to equal a
        company word ('Kato') is never stripped to 'Emma'."""
        repo = PersonRepository(temp_vault)
        repo.create_stub(name="Bob Kato", company="Kato")  # seeds 'Kato'
        person, created = repo.find_or_create_stub(name="Emma Kato", email="emma@gmail.com")
        assert created is True
        assert person.name == "Emma Kato"

    def test_uncorroborated_company_token_does_not_wrong_merge(self, temp_vault):
        """THE #1 RISK. 'Emma Roberts Kato' with NO email/company corroboration
        must NOT clean to 'Emma Roberts' and merge onto a bare 'Emma Roberts'
        canonical (who may be a different human). Stays separate."""
        repo = PersonRepository(temp_vault)
        repo.create_stub(name="Emma Roberts", company="")  # bare canonical
        repo.create_stub(name="Bob Kato", company="Kato")  # 'Kato' is a known company

        person, created = repo.find_or_create_stub(name="Emma Roberts Kato")  # no email, no company
        assert created is True, "uncorroborated 3-token name must NOT merge onto bare canonical"
        assert person.name == "Emma Roberts Kato"
        # The bare canonical is untouched.
        assert repo.get("Emma Roberts").name == "Emma Roberts"

    # ── Gate 8: existing single-name canonicals still reused, never refused ──

    def test_existing_single_name_canonical_is_reused_not_refused(self, temp_vault):
        """@Adam (a manual single-name canonical) is REUSED via exact-match
        before the weak guard can fire — refusal only ever happens on no-match."""
        repo = PersonRepository(temp_vault)
        repo.create_stub(name="Adam", auto_created=False)  # manual single-name canonical

        # Auto-created lookup with the same bare name → exact-match reuse, NOT refused.
        person, created = repo.find_or_create_stub(name="Adam", auto_created=True)
        assert created is False
        assert person.name == "Adam"

    def test_unicode_arrow_prefix_dedups_to_canonical(self, temp_vault):
        """WI-117 follow-up (the 2026-06-09 production dup): a WhatsApp chat-
        direction label 'Me → Thyra October' must clean to 'Thyra October' and
        REUSE the existing canonical — not create '@Me → Thyra October.md', a
        junk duplicate (which is exactly what happened before the fix)."""
        repo = PersonRepository(temp_vault)
        repo.create_stub(name="Thyra October")  # the real canonical

        person, created = repo.find_or_create_stub(name="Me → Thyra October")
        assert created is False, "leading 'Me →' must be stripped → exact-match reuse, not a dup"
        assert person.name == "Thyra October"

    # ── Gate 6: the WI-103 company-hinted reuse mechanism still works ──

    def test_wi103_naomi_company_hinted_reuse_preserved(self, temp_vault):
        """Regression guard: the +0.25 company-hint reuse WI-103 depends on must
        still fire. Mangled canonical 'Naomi Pavie Speechmatics' (no email);
        caller 'Naomi Pavie' + company='Speechmatics' → reuse via token-subset
        (0.65) + company-hint (+0.25) = 0.90 ≥ 0.85. (Cleaning leaves 'Naomi
        Pavie' as-is here — 'Pavie' is not a known company — so this exercises
        the resolve_all path, untouched by WI-117.)"""
        repo = PersonRepository(temp_vault)
        repo.create_stub(name="Naomi Pavie Speechmatics", company="")  # mangled, no email

        person, created = repo.find_or_create_stub(
            name="Naomi Pavie",
            email="naomi.pavie@speechmatics.com",
            company="Speechmatics",
        )
        assert created is False
        assert person.name == "Naomi Pavie Speechmatics"


class TestCreatedByProvenance:
    """WI-119 — `created_by` provenance on every stub.

    `auto_created` turned out to be a workflow flag (the enricher flips it to
    false), not provenance — which is why the 2026-06-09 'mystery writer' notes
    looked unattributable. `created_by` is written once at create-time and never
    mutated. Callers that don't self-label get the loud-fail sentinel "unknown"
    plus a WARN log.
    """

    def test_create_stub_with_created_by_round_trips(self, temp_vault):
        """(i) create with created_by='x' → readback from disk shows it."""
        repo = PersonRepository(temp_vault)
        repo.create_stub(name="Prov Test", email="prov@example.com",
                         created_by="contact_normalizer")
        # Verify-by-readback: fresh repo instance loads from disk
        fresh = PersonRepository(temp_vault)
        person = fresh.get("Prov Test")
        assert person is not None
        assert (person.model_extra or {}).get("created_by") == "contact_normalizer"
        # auto_created (default True) still rides along
        assert (person.model_extra or {}).get("auto_created") is True

    def test_create_stub_without_created_by_records_unknown_and_warns(
        self, temp_vault, caplog
    ):
        """(ii) no created_by → 'unknown' sentinel + WARN log."""
        import logging
        repo = PersonRepository(temp_vault)
        with caplog.at_level(logging.WARNING):
            repo.create_stub(name="Anon Writer", email="anon@example.com")
        fresh = PersonRepository(temp_vault)
        person = fresh.get("Anon Writer")
        assert (person.model_extra or {}).get("created_by") == "unknown"
        assert any(
            "created_by" in rec.message and "Anon Writer" in rec.message
            for rec in caplog.records if rec.levelno >= logging.WARNING
        ), "expected a WARN naming the unlabeled stub"

    def test_create_stub_empty_string_created_by_is_unknown(self, temp_vault, caplog):
        """Edge case: falsy created_by ('') treated exactly like None."""
        import logging
        repo = PersonRepository(temp_vault)
        with caplog.at_level(logging.WARNING):
            repo.create_stub(name="Empty Label", created_by="")
        fresh = PersonRepository(temp_vault)
        person = fresh.get("Empty Label")
        assert (person.model_extra or {}).get("created_by") == "unknown"

    def test_create_stub_manual_no_auto_created_still_gets_created_by(self, temp_vault):
        """auto_created=False notes still carry provenance (created_by is
        unconditional; only auto_created is conditional)."""
        repo = PersonRepository(temp_vault)
        repo.create_stub(name="Manual Person", auto_created=False,
                         created_by="new-person-skill")
        fresh = PersonRepository(temp_vault)
        person = fresh.get("Manual Person")
        assert (person.model_extra or {}).get("created_by") == "new-person-skill"
        assert "auto_created" not in (person.model_extra or {})

    def test_find_or_create_stub_passes_created_by_through(self, temp_vault):
        """(iv) find_or_create_stub passthrough on the create branch."""
        repo = PersonRepository(temp_vault)
        person, created = repo.find_or_create_stub(
            name="Pass Through",
            email="pass.through@example.com",
            created_by="exocortex-meetings",
        )
        assert created is True
        fresh = PersonRepository(temp_vault)
        loaded = fresh.get("Pass Through")
        assert (loaded.model_extra or {}).get("created_by") == "exocortex-meetings"

    def test_find_or_create_stub_reuse_leaves_canonical_created_by_alone(
        self, temp_vault
    ):
        """(iii) reuse branch never writes created_by — provenance records
        creation, not reuse."""
        repo = PersonRepository(temp_vault)
        repo.create_stub(name="Original Canonical",
                         email="orig.canonical@example.com",
                         created_by="contact-detector")
        person, created = repo.find_or_create_stub(
            name="Original Canonical",
            email="orig.canonical@example.com",
            created_by="contact_normalizer",  # different label on the reuse call
        )
        assert created is False
        fresh = PersonRepository(temp_vault)
        loaded = fresh.get("Original Canonical")
        assert (loaded.model_extra or {}).get("created_by") == "contact-detector", (
            "reuse must not overwrite the canonical's original provenance"
        )


class TestAutoAliasOnNameChange:
    """Tests for automatic alias preservation when name field changes."""

    def test_alias_added_on_name_change(self, temp_vault):
        """Updating name adds old filename stem to aliases."""
        repo = PersonRepository(temp_vault)
        person = repo.get("Jane Doe")

        repo.update_fields(person, {"name": "Jane Doe-Smith"})

        updated = repo.get("jane doe-smith")
        assert updated is not None
        assert "Jane Doe" in updated.aliases

    def test_no_duplicate_alias(self, temp_vault):
        """Old stem already in aliases → no duplicate added."""
        repo = PersonRepository(temp_vault)
        person = repo.get("John Smith")

        # Pre-add the stem as an alias
        repo.update_fields(person, {"aliases": ["Johnny", "john@example.com", "John Smith"]})
        person = repo.get("John Smith")

        # Now change the name — "John Smith" is already an alias
        repo.update_fields(person, {"name": "John Smithson"})

        updated = repo.get("john smithson")
        assert updated.aliases.count("John Smith") == 1

    def test_no_alias_on_non_name_update(self, temp_vault):
        """Updating non-name fields does not touch aliases."""
        repo = PersonRepository(temp_vault)
        person = repo.get("Jane Doe")
        original_aliases = list(person.aliases)

        repo.update_fields(person, {"company": "New Corp"})

        updated = repo.get("Jane Doe")
        assert updated.aliases == original_aliases

    def test_resolve_by_old_name_after_rename(self, temp_vault):
        """After name change, resolve still finds entity by old name via alias."""
        repo = PersonRepository(temp_vault)
        person = repo.get("Jane Doe")

        repo.update_fields(person, {"name": "Jane Doe-Smith"})

        # Old name should resolve via alias
        found = repo.resolve("Jane Doe")
        assert found is not None
        assert found.name == "Jane Doe-Smith"


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


# ── WI-121: trailing-paren decoration at find_or_create_stub ─────────

from obsidian_schemas.repositories.person import _split_trailing_paren


class TestSplitTrailingParen:
    """WI-121 predicate: strip a TRAILING '(X)' for lookup + surface X as a hint."""

    def test_company_paren(self):
        assert _split_trailing_paren("Louron Pratt (Pendo)") == ("Louron Pratt", "Pendo")

    def test_role_paren(self):
        assert _split_trailing_paren("Kate Sellwood (PA)") == ("Kate Sellwood", "PA")

    def test_mid_string_paren_not_trailing(self):
        assert _split_trailing_paren("Jane (Acme) Smith") == ("Jane (Acme) Smith", None)

    def test_sequential_parens_strips_last_only(self):
        assert _split_trailing_paren("Foo (A) (B)") == ("Foo (A)", "B")

    def test_nested_parens_no_strip(self):
        assert _split_trailing_paren("Foo (A (B))") == ("Foo (A (B))", None)

    def test_paren_only_kept_verbatim(self):
        assert _split_trailing_paren("(Pendo)") == ("(Pendo)", None)

    def test_empty(self):
        assert _split_trailing_paren("") == ("", None)

    def test_plain_name(self):
        assert _split_trailing_paren("Plain Name") == ("Plain Name", None)

    def test_unbalanced_paren_kept_verbatim(self):
        assert _split_trailing_paren("Foo (Bar") == ("Foo (Bar", None)


class TestFindOrCreateStubWI121Paren:
    """WI-121 behavioural trap set — paren-strip-for-lookup + company-hint."""

    def test_paren_company_reuses_canonical(self, temp_vault):
        """'Louron Pratt (Pendo)' must REUSE @Louron Pratt.md (the 2026-06-10 dup)."""
        repo = PersonRepository(temp_vault)
        repo.create_stub(name="Louron Pratt", company="")
        person, created = repo.find_or_create_stub(name="Louron Pratt (Pendo)")
        assert created is False, "trailing-paren strip should reuse the canonical"
        assert person.name == "Louron Pratt"

    def test_paren_role_annotation_reuses(self, temp_vault):
        """'Kate Sellwood (PA)' reuses @Kate Sellwood.md (PA is a harmless hint)."""
        repo = PersonRepository(temp_vault)
        repo.create_stub(name="Kate Sellwood", company="")
        person, created = repo.find_or_create_stub(name="Kate Sellwood (PA)")
        assert created is False
        assert person.name == "Kate Sellwood"

    def test_paren_known_company_stored_on_create(self, temp_vault):
        """No canonical → create '@Naomi Pavie' + company=Speechmatics (known)."""
        repo = PersonRepository(temp_vault)
        # Make 'Speechmatics' a known company via an unrelated note.
        repo.create_stub(name="Some Speechmatics Person", company="Speechmatics")
        person, created = repo.find_or_create_stub(name="Naomi Pavie (Speechmatics)")
        assert created is True
        assert person.name == "Naomi Pavie"
        assert person.company == "Speechmatics", (
            "a known paren-company must be stored on the new note"
        )

    def test_paren_role_annotation_not_stored_as_company(self, temp_vault):
        """No canonical → create '@Jo Bloggs'; 'PA' is NOT a known company → not stored."""
        repo = PersonRepository(temp_vault)
        person, created = repo.find_or_create_stub(
            name="Jo Bloggs (PA)", email="jo@example.com"
        )
        assert created is True
        assert person.name == "Jo Bloggs"
        assert (person.company or "") == "", (
            "a role annotation must never be persisted as a company"
        )

    def test_caller_company_wins_over_paren(self, temp_vault):
        """Caller-supplied company wins over the paren-derived one (and is stored
        as-is — caller company is the stronger signal, not paren-filtered)."""
        repo = PersonRepository(temp_vault)
        person, created = repo.find_or_create_stub(
            name="Foo Bar (Wrong Co)", company="Right Co", email="foo@example.com"
        )
        assert created is True
        assert person.name == "Foo Bar"
        assert person.company == "Right Co"
