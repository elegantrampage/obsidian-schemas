"""WI-125 Phase 2 — the unified `Identifier → EntityRef` index + reconciliation.

These exercise the index built ALONGSIDE the legacy per-kind dicts (the dicts
stay the permissive lookup surface; this typed index becomes the Phase-3
resolution contract). The headline behaviours:

  - frontmatter projects into PERSON-resolving identifiers (email/phone/
    whatsapp/linkedin); slack (no workspace) + email-domains (company) omitted;
  - a `whatsapp` that equals a `phone` unifies to ONE key (no false conflict);
  - an identifier key shared by >1 note is a reconciliation CONFLICT — recorded
    to `repo.conflicts` naming every candidate, logged loud, never raised/merged;
  - the index is last-writer-wins, byte-identical to the legacy dicts (parity);
  - a malformed field is skipped leniently here but STILL indexed by the legacy
    dict (so old-path lookups are unaffected — the strangler-safety guarantee).

Real-data shapes from the 2026-06-13 live-vault audit: the dup pairs that share
a LinkedIn/email (Emma Roberts / Emma Roberts Kato; Moises Garcia ×3; a genuinely
shared mailbox cal@…).
"""

import pytest

from obsidian_schemas import (
    PersonRepository,
    EntityRef,
    IdentifierConflict,
)


def _note(vault, name, *, emails=None, phones=None, whatsapp=None,
          linkedin=None, slack=None, company=None):
    """Write a raw person note straight to disk — bypasses find_or_create_stub's
    dedup so we can stage the pre-existing duplicates the reconciliation check
    is meant to catch."""
    lines = ["---", "type: person", f"name: {name}"]
    if emails:
        lines.append("emails:")
        lines += [f"  - {e}" for e in emails]
    if phones:
        lines.append("phones:")
        lines += [f'  - "{p}"' for p in phones]
    if whatsapp:
        lines.append(f'whatsapp: "{whatsapp}"')
    if linkedin:
        lines.append(f"linkedin: {linkedin}")
    if slack:
        lines.append(f"slack: {slack}")
    if company:
        lines.append(f"company: {company}")
    lines += ["tags:", "  - person", "---", "", "## Timeline", ""]
    (vault / f"@{name}.md").write_text("\n".join(lines))


@pytest.fixture
def vault(tmp_path):
    v = tmp_path / "vault"
    v.mkdir()
    return v


# ── projection: which frontmatter becomes which identifier key ───────────────

class TestProjection:
    def test_email_phone_whatsapp_linkedin_indexed(self, vault):
        _note(vault, "John Smith",
              emails=["john@example.com"],
              phones=["+447990558521"],
              linkedin="https://linkedin.com/in/johnsmith")
        repo = PersonRepository(vault)
        repo.load()
        idx = repo._identifier_index
        assert idx["email:john@example.com"] == EntityRef("person", "john smith")
        assert idx["phone:447990558521"] == EntityRef("person", "john smith")
        assert idx["linkedin:in/johnsmith"] == EntityRef("person", "john smith")

    def test_whatsapp_equals_phone_unifies_to_one_key_no_conflict(self, vault):
        # whatsapp digits == the phone digits → same `phone:` key, same entity →
        # idempotent, NOT a conflict.
        _note(vault, "Jane Doe",
              phones=["+447990558521"], whatsapp="447990558521")
        repo = PersonRepository(vault)
        repo.load()
        assert repo._identifier_index["phone:447990558521"] == EntityRef("person", "jane doe")
        assert repo.conflicts == []

    def test_slack_not_projected_but_legacy_lookup_works(self, vault):
        # Bare slack handle has no workspace → no typed SlackUserId → absent from
        # the unified index, but the legacy `_slack_index` still resolves it.
        _note(vault, "Slacker", slack="U052R9S0RB6")
        repo = PersonRepository(vault)
        repo.load()
        assert not any(k.startswith("slack:") for k in repo._identifier_index)
        assert repo.get_by_slack("U052R9S0RB6").name == "Slacker"

    def test_email_domain_not_in_person_index(self, vault):
        # EmailDomain resolves Company (not activated this cut) — never lands in
        # the person index.
        _note(vault, "John Smith", emails=["john@example.com"])
        repo = PersonRepository(vault)
        repo.load()
        assert not any(k.startswith("domain:") for k in repo._identifier_index)

    def test_aliases_are_not_identifiers(self, vault):
        # Aliases are name variants, not hard identifiers — legacy `_alias_index`
        # only.
        (vault / "@Bob.md").write_text(
            "---\ntype: person\nname: Bob\naliases:\n  - Bobby\ntags:\n  - person\n---\n"
        )
        repo = PersonRepository(vault)
        repo.load()
        assert repo._identifier_index == {}
        assert repo.get_by_alias("Bobby").name == "Bob"


# ── reconciliation: cross-entity collisions become conflicts ─────────────────

class TestReconciliation:
    def test_shared_email_recorded_as_conflict(self, vault):
        # A genuinely shared mailbox (the live-vault cal@… shape): two distinct
        # people, one email.
        _note(vault, "Cal Liddle", emails=["cal@zappistore.com"])
        _note(vault, "Cal Sheridan", emails=["cal@zappistore.com"])
        repo = PersonRepository(vault)
        repo.load()
        conflicts = repo.conflicts
        assert len(conflicts) == 1
        c = conflicts[0]
        assert c.identifier_key == "email:cal@zappistore.com"
        assert set(r.canonical_key for r in c.entities) == {"cal liddle", "cal sheridan"}

    def test_shared_linkedin_recorded_as_conflict(self, vault):
        # The dominant live-vault shape: a dup pair sharing a LinkedIn slug.
        _note(vault, "Emma Roberts", linkedin="https://linkedin.com/in/emma-roberts-96456268")
        _note(vault, "Emma Roberts Kato", linkedin="https://linkedin.com/in/emma-roberts-96456268")
        repo = PersonRepository(vault)
        repo.load()
        keys = {c.identifier_key for c in repo.conflicts}
        assert "linkedin:in/emma-roberts-96456268" in keys

    def test_three_way_collision_is_one_record_with_three_entities(self, vault):
        # Moises ×3 — dedups into a SINGLE conflict record naming all three.
        slug = "https://linkedin.com/in/moises-garcia-h"
        _note(vault, "Moises Garcia", linkedin=slug)
        _note(vault, "Moises Garcia Hernandez", linkedin=slug)
        _note(vault, "Moises 9fin", linkedin=slug)
        repo = PersonRepository(vault)
        repo.load()
        recs = [c for c in repo.conflicts if c.identifier_key == "linkedin:in/moises-garcia-h"]
        assert len(recs) == 1
        assert len(recs[0].entities) == 3

    def test_index_last_wins_matches_legacy_lookup(self, vault):
        # Parity: the unified index resolves a colliding key to the SAME entity
        # the legacy per-kind dict does (both iterate one glob order, last-wins).
        _note(vault, "Cal Liddle", emails=["cal@zappistore.com"])
        _note(vault, "Cal Sheridan", emails=["cal@zappistore.com"])
        repo = PersonRepository(vault)
        repo.load()
        legacy = repo.get_by_email("cal@zappistore.com")
        unified = repo._identifier_index["email:cal@zappistore.com"]
        assert unified.canonical_key == legacy.name.lower()

    def test_clean_vault_has_no_conflicts(self, vault):
        _note(vault, "John Smith", emails=["john@example.com"])
        _note(vault, "Jane Doe", emails=["jane@example.com"])
        repo = PersonRepository(vault)
        repo.load()
        assert repo.conflicts == []

    def test_conflict_logged_loud(self, vault, caplog):
        import logging
        _note(vault, "Cal Liddle", emails=["cal@zappistore.com"])
        _note(vault, "Cal Sheridan", emails=["cal@zappistore.com"])
        repo = PersonRepository(vault)
        with caplog.at_level(logging.WARNING):
            repo.load()
        assert any("reconciliation conflict" in r.message for r in caplog.records)


# ── leniency: malformed fields don't break load; legacy dict still has them ──

class TestLeniency:
    def test_malformed_email_skipped_but_legacy_indexes_it(self, vault):
        # Legacy `_email_index` indexes ANY non-empty string; the typed index
        # skips what won't parse. The old-path lookup must be unaffected.
        _note(vault, "Junk Holder", emails=["not-an-email"])
        repo = PersonRepository(vault)
        repo.load()  # must not raise
        assert "not-an-email" in repo._email_index           # legacy still has it
        assert not any("not-an-email" in k for k in repo._identifier_index)

    def test_clean_and_junk_in_one_list_indexes_only_the_clean(self, vault):
        # A valid note carrying one good + one malformed email: the typed index
        # gets the good one, skips the junk ("bad email" has whitespace → no
        # parse); the legacy dict keeps both.
        _note(vault, "Mixed", emails=["good@example.com", "bad email"])
        repo = PersonRepository(vault)
        repo.load()
        assert repo._identifier_index["email:good@example.com"] == EntityRef("person", "mixed")
        assert not any("bad email" in k for k in repo._identifier_index)
        assert "bad email" in repo._email_index  # legacy keeps the junk


# ── lifecycle: clear / refresh reset reconciliation state ────────────────────

class TestLifecycle:
    def test_refresh_rebuilds_conflicts_without_doubling(self, vault):
        _note(vault, "Cal Liddle", emails=["cal@zappistore.com"])
        _note(vault, "Cal Sheridan", emails=["cal@zappistore.com"])
        repo = PersonRepository(vault)
        repo.load()
        assert len(repo.conflicts) == 1
        repo.refresh()
        assert len(repo.conflicts) == 1  # not 2 — cleared then rebuilt

    def test_clear_indexes_empties_unified_index_and_conflicts(self, vault):
        _note(vault, "Cal Liddle", emails=["cal@zappistore.com"])
        _note(vault, "Cal Sheridan", emails=["cal@zappistore.com"])
        repo = PersonRepository(vault)
        repo.load()
        repo._clear_indexes()
        assert repo._identifier_index == {}
        assert repo._conflict_sets == {}

    def test_update_fields_removes_stale_identifier_from_index(self, vault):
        _note(vault, "John Smith", emails=["john@example.com"])
        repo = PersonRepository(vault)
        repo.load()
        person = repo.get("John Smith")
        repo.update_fields(person, {"emails": ["john.new@example.com"]})
        assert "email:john@example.com" not in repo._identifier_index
        assert repo._identifier_index["email:john.new@example.com"] == EntityRef("person", "john smith")


# ── value-type semantics ─────────────────────────────────────────────────────

class TestValueTypes:
    def test_entityref_value_equality_and_hashable(self):
        a = EntityRef("person", "john smith")
        b = EntityRef("person", "john smith")
        assert a == b
        assert hash(a) == hash(b)
        assert len({a, b}) == 1
        assert EntityRef("company", "john smith") != a

    def test_conflict_holds_key_and_entities(self):
        c = IdentifierConflict(
            identifier_key="email:x@y.com",
            entities=(EntityRef("person", "a"), EntityRef("person", "b")),
        )
        assert c.identifier_key == "email:x@y.com"
        assert len(c.entities) == 2
