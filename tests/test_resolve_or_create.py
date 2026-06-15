"""WI-125 Phase 3 — the identity engine `resolve_or_create`.

The engine reproduces `find_or_create_stub`'s **return-value** behavior
(`(resolved_name, created_new)` — the Phase-5 parity contract) plus the one
genuinely-new behavior: **Branch-A conflict detection**. Not yet wired into
`find_or_create_stub` (that's the Phase-4 adapter swap).

Coverage:
  - Branch A: email hit / phone-only hit / agreeing email+phone (no conflict) /
    disagreeing email→X,phone→Y (conflict recorded, best-hit returned, no raise) /
    a richer identifier (LinkedIn) resolving through the unified index;
  - Branch B: the Naomi Pavie reuse gate (mangled canonical, name+company);
  - Branch C: WeakIdentityError preserved; clean create;
  - a mini **parity harness** — `resolve_or_create` vs `find_or_create_stub` on
    identical twin vaults, asserting identical `(name, created)` per case (the
    Phase-5 gate in miniature).
"""

import shutil

import pytest

from obsidian_schemas import (
    PersonRepository,
    EntityRef,
    Email,
    Phone,
    LinkedInSlug,
    parse_identifiers,
)
from obsidian_schemas.name_validation import WeakIdentityError


def _note(vault, name, *, emails=None, phones=None, linkedin=None, company=None):
    lines = ["---", "type: person", f"name: {name}"]
    if emails:
        lines.append("emails:")
        lines += [f"  - {e}" for e in emails]
    if phones:
        lines.append("phones:")
        lines += [f'  - "{p}"' for p in phones]
    if linkedin:
        lines.append(f"linkedin: {linkedin}")
    if company:
        lines.append(f"company: {company}")
    lines += ["tags:", "  - person", "---", "", "## Timeline", ""]
    (vault / f"@{name}.md").write_text("\n".join(lines))


@pytest.fixture
def vault(tmp_path):
    v = tmp_path / "vault"
    v.mkdir()
    return v


# ── Branch A — identifier hits ───────────────────────────────────────────────

class TestBranchA:
    def test_email_hit_reuses_returns_entityref(self, vault):
        _note(vault, "John Smith", emails=["john@example.com"])
        repo = PersonRepository(vault)
        ref, created = repo.resolve_or_create(
            parse_identifiers(email="john@example.com"), display_name="J. Smith"
        )
        assert created is False
        assert ref == EntityRef("person", "john smith")
        assert repo._hydrate(ref).name == "John Smith"

    def test_phone_only_hit_reuses(self, vault):
        _note(vault, "Jane Doe", phones=["+15551234567"])
        repo = PersonRepository(vault)
        ref, created = repo.resolve_or_create(
            parse_identifiers(phone="+15551234567"), display_name="Jane"
        )
        assert created is False
        assert ref.canonical_key == "jane doe"

    def test_agreeing_email_and_phone_no_conflict(self, vault):
        _note(vault, "John Smith", emails=["john@example.com"], phones=["+15551234567"])
        repo = PersonRepository(vault)
        ref, created = repo.resolve_or_create(
            parse_identifiers(email="john@example.com", phone="+15551234567"),
            display_name="John",
        )
        assert created is False
        assert ref.canonical_key == "john smith"
        assert repo.conflicts == []

    def test_disagreeing_email_and_phone_is_a_conflict(self, vault):
        # email→X, phone→Y. Return the legacy best-hit (email, X); record the
        # conflict naming both; never raise, never merge.
        _note(vault, "Person X", emails=["x@a.com"])
        _note(vault, "Person Y", phones=["+15551112222"])
        repo = PersonRepository(vault)
        ref, created = repo.resolve_or_create(
            parse_identifiers(email="x@a.com", phone="+15551112222"),
            display_name="Whoever",
        )
        assert created is False
        assert ref.canonical_key == "person x"          # email wins (best-hit), parity
        conflicts = repo.conflicts
        assert len(conflicts) == 1
        c = conflicts[0]
        assert c.identifier_key.startswith("resolve:")
        assert {r.canonical_key for r in c.entities} == {"person x", "person y"}

    def test_richer_identifier_resolves_via_index(self, vault):
        # No current caller passes LinkedIn, but the engine is general: a
        # LinkedIn identifier resolves through the unified index.
        _note(vault, "Ada Lovelace", linkedin="https://linkedin.com/in/adalovelace")
        repo = PersonRepository(vault)
        ref, created = repo.resolve_or_create(
            parse_identifiers(linkedin="https://linkedin.com/in/adalovelace"),
            display_name="Ada",
        )
        assert created is False
        assert ref.canonical_key == "ada lovelace"


# ── Branch B — the Naomi Pavie reuse gate ────────────────────────────────────

class TestBranchBNaomiGate:
    def test_mangled_canonical_reused_via_name_and_company(self, vault):
        # Existing mangled canonical 'Naomi Pavie Speechmatics' (no email on it);
        # caller has name 'Naomi Pavie' + email@speechmatics.com + company hint.
        # Branch A (email) misses → Branch B: resolve_all('Naomi Pavie',
        # company='Speechmatics') token-subset 0.65 + company bump 0.25 = 0.90 ≥
        # 0.85 → REUSE. No new note.
        _note(vault, "Naomi Pavie Speechmatics", company="Speechmatics")
        repo = PersonRepository(vault)
        ref, created = repo.resolve_or_create(
            parse_identifiers(email="naomi@speechmatics.com"),
            display_name="Naomi Pavie",
            company_hint="Speechmatics",
        )
        assert created is False, "must REUSE the mangled canonical, not create a dup"
        assert ref.canonical_key == "naomi pavie speechmatics"


# ── Branch C — weak guard + create ───────────────────────────────────────────

class TestBranchC:
    def test_weak_identity_still_raises(self, vault):
        repo = PersonRepository(vault)
        with pytest.raises(WeakIdentityError):
            repo.resolve_or_create([], display_name="Cher", auto_created=True)
        assert repo.get("Cher") is None  # no note written

    def test_weak_guard_skipped_when_not_auto_created(self, vault):
        repo = PersonRepository(vault)
        ref, created = repo.resolve_or_create([], display_name="Cher", auto_created=False)
        assert created is True
        assert ref.canonical_key == "cher"

    def test_creates_new_stub_when_no_match(self, vault):
        _note(vault, "Someone Else", emails=["else@x.com"])
        repo = PersonRepository(vault)
        ref, created = repo.resolve_or_create(
            parse_identifiers(email="new@example.com"),
            display_name="Brand New Person",
            company_hint="Acme",
            provenance="test-suite",
        )
        assert created is True
        assert ref.canonical_key == "brand new person"
        assert repo._hydrate(ref).name == "Brand New Person"


# ── Parity harness: resolve_or_create vs find_or_create_stub ─────────────────

# (name, email, phone, company) → exercised against identical twin vaults.
PARITY_CASES = [
    ("J. Smith", "john@example.com", None, None),                  # A: email hit
    ("Jane", None, "+15551234567", None),                         # A: phone hit
    ("Naomi Pavie", "naomi@speechmatics.com", None, "Speechmatics"),  # B: name reuse
    ("Brand New Person", "fresh@example.com", None, "Acme"),      # C: create
    ("Louron Pratt (Pendo)", None, None, None),                  # WI-121: B reuse via paren-strip
]


def _seed(vault):
    _note(vault, "John Smith", emails=["john@example.com"])
    _note(vault, "Jane Doe", phones=["+15551234567"])
    _note(vault, "Naomi Pavie Speechmatics", company="Speechmatics")
    _note(vault, "Louron Pratt")  # WI-121: paren-strip must reuse this canonical


@pytest.mark.parametrize("name,email,phone,company", PARITY_CASES)
def test_engine_matches_legacy_return_value(tmp_path, name, email, phone, company):
    """The Phase-5 parity contract in miniature: identical `(name, created)`."""
    va, vb = tmp_path / "a", tmp_path / "b"
    va.mkdir()
    _seed(va)
    shutil.copytree(va, vb)

    legacy = PersonRepository(va)
    person, leg_created = legacy.find_or_create_stub(
        name, email=email, phone=phone, company=company
    )
    legacy_result = (person.name, leg_created)

    engine = PersonRepository(vb)
    ref, eng_created = engine.resolve_or_create(
        parse_identifiers(email=email, phone=phone, strict=False),
        display_name=name,
        company_hint=company,
    )
    engine_result = (engine._hydrate(ref).name, eng_created)

    assert engine_result == legacy_result


def test_engine_matches_legacy_on_weak_identity(tmp_path):
    """Both paths raise WeakIdentityError on the same weak input."""
    va, vb = tmp_path / "a", tmp_path / "b"
    va.mkdir()
    _seed(va)
    shutil.copytree(va, vb)

    with pytest.raises(WeakIdentityError):
        PersonRepository(va).find_or_create_stub("Cher", auto_created=True)
    with pytest.raises(WeakIdentityError):
        PersonRepository(vb).resolve_or_create([], display_name="Cher", auto_created=True)
