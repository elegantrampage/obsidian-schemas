"""Tests for the typed Identifier union (WI-125, Phase 1).

Parse-don't-validate: every kind is built via `.parse(raw)`, which normalizes
and raises IdentifierError on malformed input. These tests cover normalization,
rejection, the `.resolves` declarations, the namespaced `.key` (the Phase-2
index key), the email→domain derivation, the public-provider denylist, JID↔phone
unification, and `parse_identifiers` (the Phase-4 adapter seed).

Identifiers are name-INDEPENDENT — there is deliberately no place for a display
name in this layer (that's the whole point of the model: stop matching on names).
"""

import pytest

from obsidian_schemas.identifier import (
    Identifier,
    IdentifierError,
    Email,
    EmailDomain,
    Phone,
    WhatsAppJID,
    SlackUserId,
    LinkedInSlug,
    CalendarEventId,
    GranolaDocId,
    parse_identifiers,
    PUBLIC_EMAIL_PROVIDERS,
    ALL_IDENTIFIER_KINDS,
)


# ── Email ────────────────────────────────────────────────────────────────────

class TestEmail:
    def test_basic(self):
        e = Email.parse("Louron.Pratt@Pendo.IO")
        assert e.value == "louron.pratt@pendo.io"   # lowercased
        assert e.local == "louron.pratt"
        assert e.domain == "pendo.io"
        assert e.key == "email:louron.pratt@pendo.io"
        assert e.resolves == frozenset({"person"})

    def test_extracts_from_display_name_form(self):
        # The WI-017 create_stub bug: "Name <email>" must yield the address.
        e = Email.parse("Dave Wascha <dave@davewascha.com>")
        assert e.value == "dave@davewascha.com"

    def test_strips_surrounding_whitespace(self):
        assert Email.parse("  a@b.com  ").value == "a@b.com"

    @pytest.mark.parametrize("bad", [
        None, "", "   ", "no-at-sign", "a@@b.com", "a@b@c.com",
        "@nodomain.com", "nolocal@", "a@nodot", "a b@c.com", "a@b c.com",
    ])
    def test_malformed_raises(self, bad):
        with pytest.raises(IdentifierError):
            Email.parse(bad)

    def test_domain_derivation(self):
        e = Email.parse("a@acme.com")
        d = e.domain_id
        assert isinstance(d, EmailDomain)
        assert d.domain == "acme.com"
        assert d.resolves == frozenset({"company"})

    def test_is_an_identifier(self):
        assert isinstance(Email.parse("a@b.com"), Identifier)


# ── EmailDomain ───────────────────────────────────────────────────────────────

class TestEmailDomain:
    def test_basic(self):
        d = EmailDomain.parse("Pendo.IO")
        assert d.domain == "pendo.io"
        assert d.key == "domain:pendo.io"
        assert d.resolves == frozenset({"company"})

    def test_strips_www(self):
        assert EmailDomain.parse("www.acme.com").domain == "acme.com"

    def test_from_url(self):
        assert EmailDomain.parse("https://www.acme.com/careers").domain == "acme.com"

    def test_from_email(self):
        assert EmailDomain.parse("someone@acme.com").domain == "acme.com"

    def test_public_provider_flag(self):
        assert EmailDomain.parse("gmail.com").is_public_provider is True
        assert EmailDomain.parse("outlook.com").is_public_provider is True
        assert EmailDomain.parse("pendo.io").is_public_provider is False

    @pytest.mark.parametrize("bad", [None, "", "nodot", "a b.com", "a@b.com extra"])
    def test_malformed_raises(self, bad):
        with pytest.raises(IdentifierError):
            EmailDomain.parse(bad)


# ── Phone ─────────────────────────────────────────────────────────────────────

class TestPhone:
    @pytest.mark.parametrize("raw,expected", [
        ("+44 7990 558521", "447990558521"),
        ("447990558521@s.whatsapp.net", "447990558521"),
        ("(555) 123-4567", "5551234567"),
    ])
    def test_normalization(self, raw, expected):
        p = Phone.parse(raw)
        assert p.digits == expected
        assert p.key == f"phone:{expected}"
        assert p.resolves == frozenset({"person"})

    @pytest.mark.parametrize("bad", [None, "", "123", "abc", "+44 12"])
    def test_too_short_or_empty_raises(self, bad):
        with pytest.raises(IdentifierError):
            Phone.parse(bad)


# ── WhatsAppJID ───────────────────────────────────────────────────────────────

class TestWhatsAppJID:
    def test_phone_bearing(self):
        j = WhatsAppJID.parse("447990558521@s.whatsapp.net")
        assert j.phone_digits == "447990558521"
        assert j.phone == Phone.parse("447990558521")

    def test_phone_bearing_jid_unifies_with_bare_phone(self):
        # The key fix: a JID and a bare phone for the same number share a key,
        # so they collapse to one index entry (same person).
        j = WhatsAppJID.parse("447990558521@s.whatsapp.net")
        p = Phone.parse("+44 7990 558521")
        assert j.key == p.key == "phone:447990558521"

    def test_lid_has_no_phone(self):
        j = WhatsAppJID.parse("123456789@lid")
        assert j.phone_digits == ""
        assert j.phone is None
        assert j.key == "jid:123456789@lid"

    @pytest.mark.parametrize("bad", [None, "", "notaphone@s.whatsapp.net"])
    def test_malformed_raises(self, bad):
        with pytest.raises(IdentifierError):
            WhatsAppJID.parse(bad)


# ── SlackUserId ───────────────────────────────────────────────────────────────

class TestSlackUserId:
    def test_kwargs(self):
        s = SlackUserId.parse(workspace="T123", user_id="U456")
        assert s.value == "T123/U456"
        assert s.key == "slack:T123/U456"
        assert s.resolves == frozenset({"person"})

    def test_string_form(self):
        assert SlackUserId.parse("T123/U456").value == "T123/U456"

    def test_case_preserved(self):
        # Slack ids are case-sensitive — must NOT be lowercased.
        assert SlackUserId.parse(workspace="T1", user_id="UAbC").user_id == "UAbC"

    def test_workspace_scoped(self):
        a = SlackUserId.parse(workspace="T1", user_id="U9")
        b = SlackUserId.parse(workspace="T2", user_id="U9")
        assert a.key != b.key  # same user id, different workspace → different key

    @pytest.mark.parametrize("kwargs", [
        {"raw": "noslash"}, {"workspace": "T1"}, {"user_id": "U1"}, {"raw": ""},
    ])
    def test_malformed_raises(self, kwargs):
        with pytest.raises(IdentifierError):
            SlackUserId.parse(**kwargs)


# ── LinkedInSlug ──────────────────────────────────────────────────────────────

class TestLinkedInSlug:
    def test_person_url(self):
        s = LinkedInSlug.parse("https://www.linkedin.com/in/johnsmith/")
        assert s.slug == "johnsmith"
        assert s.entity_hint == "person"
        assert s.key == "linkedin:in/johnsmith"

    def test_company_url(self):
        s = LinkedInSlug.parse("https://linkedin.com/company/acme")
        assert s.slug == "acme"
        assert s.entity_hint == "company"
        assert s.key == "linkedin:company/acme"

    def test_bare_slug_is_person(self):
        s = LinkedInSlug.parse("johnsmith")
        assert s.entity_hint == "person"
        assert s.key == "linkedin:in/johnsmith"

    def test_person_and_company_same_slug_dont_collide(self):
        assert LinkedInSlug.parse("/in/acme").key != LinkedInSlug.parse("/company/acme").key

    def test_resolves_both(self):
        assert LinkedInSlug.parse("johnsmith").resolves == frozenset({"person", "company"})

    @pytest.mark.parametrize("bad", [None, "", "https://linkedin.com/feed/", "  /in/  "])
    def test_malformed_raises(self, bad):
        with pytest.raises(IdentifierError):
            LinkedInSlug.parse(bad)


# ── Meeting ids ───────────────────────────────────────────────────────────────

class TestMeetingIds:
    def test_calendar_event(self):
        c = CalendarEventId.parse("evt_abc123")
        assert c.key == "calendar_event:evt_abc123"
        assert c.resolves == frozenset({"meeting"})

    def test_granola_doc(self):
        g = GranolaDocId.parse("doc_xyz")
        assert g.key == "granola_doc:doc_xyz"
        assert g.resolves == frozenset({"meeting"})

    @pytest.mark.parametrize("kind", [CalendarEventId, GranolaDocId])
    def test_empty_raises(self, kind):
        with pytest.raises(IdentifierError):
            kind.parse("")


# ── parse_identifiers (the Phase-4 adapter seed) ──────────────────────────────

class TestParseIdentifiers:
    def test_email_yields_person_and_company_identifiers(self):
        ids = parse_identifiers(email="louron.pratt@pendo.io")
        keys = {i.key for i in ids}
        assert "email:louron.pratt@pendo.io" in keys   # person
        assert "domain:pendo.io" in keys               # company (derived)

    def test_company_name_is_not_a_parameter(self):
        # A company NAME is a display hint, not an identifier. parse_identifiers
        # never mints a company-domain from a name — only derives it from email.
        import inspect
        assert "company" not in inspect.signature(parse_identifiers).parameters

    def test_combo(self):
        ids = parse_identifiers(email="a@acme.com", phone="+44 7990 558521")
        keys = {i.key for i in ids}
        assert keys == {"email:a@acme.com", "domain:acme.com", "phone:447990558521"}

    def test_none_and_empty_skipped(self):
        assert parse_identifiers(email=None, phone="   ") == set()

    def test_strict_raises_on_malformed(self):
        with pytest.raises(IdentifierError):
            parse_identifiers(email="not-an-email", strict=True)

    def test_lenient_skips_malformed(self):
        ids = parse_identifiers(email="not-an-email", phone="+44 7990 558521", strict=False)
        assert {i.key for i in ids} == {"phone:447990558521"}


# ── Cross-cutting ─────────────────────────────────────────────────────────────

class TestCrossCutting:
    def test_identifiers_are_frozen_and_hashable(self):
        # Usable as set/dict keys (the index depends on this) + value-equality.
        s = {Email.parse("a@b.com"), Email.parse("a@b.com")}
        assert len(s) == 1
        with pytest.raises(Exception):
            Email.parse("a@b.com").local = "x"   # frozen

    def test_every_kind_declares_resolves_subset(self):
        valid = {"person", "company", "meeting"}
        for kind in ALL_IDENTIFIER_KINDS:
            assert kind.resolves, f"{kind.__name__} declares no resolves"
            assert kind.resolves <= valid, f"{kind.__name__} resolves outside {valid}"

    def test_all_kinds_are_identifiers(self):
        for kind in ALL_IDENTIFIER_KINDS:
            assert issubclass(kind, Identifier)

    def test_keys_are_namespaced_and_distinct_across_kinds(self):
        # Different kinds with the same raw value must not collide in the index.
        keys = {
            Email.parse("a@acme.com").key,
            EmailDomain.parse("acme.com").key,
            LinkedInSlug.parse("acme").key,
            CalendarEventId.parse("acme").key,
        }
        assert len(keys) == 4
