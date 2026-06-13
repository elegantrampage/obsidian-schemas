"""
Person repository for contact management.

Provides fast lookup of Person entities by:
- Name (exact and partial)
- Email address
- Phone number (with normalization)
- Aliases
- Slack user ID or handle

Also provides methods for managing To Discuss items.
"""

import re
import logging
from dataclasses import dataclass
from email.utils import parseaddr
from pathlib import Path
from typing import Optional, List, Literal, Tuple, Type

from ..models import Person
from ..name_validation import (
    NameValidator,
    NameValidationError,
    WeakIdentityError,
    weak_identity_reason,
)
from ..name_cleaning import clean_person_name
from ..identifier import (
    Email,
    Phone,
    WhatsAppJID,
    LinkedInSlug,
    Identifier,
    IdentifierError,
    EntityRef,
    IdentifierConflict,
)


@dataclass(frozen=True)
class ResolveCandidate:
    """One candidate match from PersonRepository.resolve_all().

    Confidence calibration (0.0-1.0, higher = stronger evidence):
      1.0   — exact identifier match (exact name, alias, email, phone)
      0.85+ — partial-name match with company hint corroboration
      0.65  — token-subset partial-name match (no company corroboration)
      <0.5  — weak signal; callers should treat as no-match

    matched_via documents which strategy fired:
      "exact-name" / "alias" / "email" / "phone" / "token-subset" / "partial-name"

    WI-018 (2026-06-01) — surfaced from orchestrator Phase 0 trace.
    """
    person: Person
    confidence: float
    matched_via: str
from ..body_sections import (
    get_default_body,
    get_section,
    update_section,
    append_to_section,
    prepend_to_section,
    ToDiscussItem,
    parse_to_discuss_items,
    write_to_discuss_items,
)
from .base import BaseRepository

logger = logging.getLogger(__name__)


def normalize_phone(phone: str) -> str:
    """
    Normalize a phone number to digits only.

    Examples:
        "+44 7990 558521" → "447990558521"
        "447990558521@s.whatsapp.net" → "447990558521"
        "(555) 123-4567" → "5551234567"
    """
    if not phone:
        return ""

    # Remove WhatsApp JID suffix
    phone = phone.split("@")[0]

    # Keep only digits
    return re.sub(r"\D", "", phone)


def phones_match(phone1: str, phone2: str) -> bool:
    """
    Check if two phone numbers represent the same person.

    Handles country code variations:
    - UK: 44... vs 0...
    - US: 1... vs 10-digit
    """
    norm1 = normalize_phone(phone1)
    norm2 = normalize_phone(phone2)

    if not norm1 or not norm2:
        return False

    # Direct match
    if norm1 == norm2:
        return True

    # UK: 44 prefix vs 0 prefix
    if norm1.startswith("44") and norm2.startswith("0"):
        return norm1[2:] == norm2[1:]
    if norm2.startswith("44") and norm1.startswith("0"):
        return norm2[2:] == norm1[1:]

    # US: 1 prefix vs 10-digit
    if norm1.startswith("1") and len(norm1) == 11:
        if norm1[1:] == norm2:
            return True
    if norm2.startswith("1") and len(norm2) == 11:
        if norm2[1:] == norm1:
            return True

    return False


class PersonRepository(BaseRepository[Person]):
    """
    Repository for Person entities.

    Provides fast lookup by name, email, phone, or alias.
    Indexes are built on first load for O(1) lookups.

    Usage:
        repo = PersonRepository("/path/to/vault")
        person = repo.get("John Smith")
        person = repo.get_by_email("john@example.com")
        person = repo.get_by_phone("+447990558521")
    """

    def __init__(self, vault_path: Optional[str | Path] = None, **kwargs):
        super().__init__(vault_path, **kwargs)
        self._email_index: dict[str, str] = {}  # email -> cache_key
        self._phone_index: dict[str, str] = {}  # normalized phone -> cache_key
        self._alias_index: dict[str, str] = {}  # alias -> cache_key
        self._slack_index: dict[str, str] = {}  # slack ID/handle -> cache_key
        # WI-125 Phase 2 — the unified resolution contract (model §2:
        # `Identifier → EntityRef`). Built ALONGSIDE the per-kind dicts above,
        # not as a rewiring of them: the dicts stay the permissive lookup surface
        # (zero parity risk) while this typed index becomes the source Phase-3
        # `resolve_or_create` resolves through. Collapsing the dicts into views
        # of this map + deleting them is the strangler's later deletion cut.
        # Keyed on `identifier.key`; only PERSON-resolving identifiers land here.
        self._identifier_index: dict[str, EntityRef] = {}
        # Reconciliation findings: identifier key -> the set of EntityRefs it was
        # seen on. Only populated when a key collides (>1 entity) — a real-data
        # duplicate (the WI-119 invariant generalized). Exposed via `.conflicts`.
        self._conflict_sets: dict[str, set] = {}
        # WI-117: lazily-held CompanyRepository for corroborated name-cleaning.
        # Loaded at most once per process (same lifetime as this repo's own
        # cache); the known-companies SET is still rebuilt per-call. None until
        # first 3+-token find_or_create_stub call that needs corroboration.
        self._company_repo_for_cleaning = None

    @property
    def entity_type(self) -> Type[Person]:
        return Person

    @property
    def type_name(self) -> str:
        return "person"

    def _index_entity(self, entity: Person, cache_key: str) -> None:
        """Build email, phone, and alias indexes."""
        # Index emails
        for email in entity.emails:
            if email:
                self._email_index[email.lower()] = cache_key

        # Index phones
        for phone in entity.phones:
            norm = normalize_phone(phone)
            if norm:
                self._phone_index[norm] = cache_key

        # Index WhatsApp number
        if entity.whatsapp:
            norm = normalize_phone(entity.whatsapp)
            if norm:
                self._phone_index[norm] = cache_key

        # Index aliases
        for alias in entity.aliases:
            if alias:
                self._alias_index[alias.lower()] = cache_key

        # Index Slack
        if entity.slack:
            # Store both with and without @ prefix for flexible lookup
            slack_id = entity.slack.lstrip("@").lower()
            self._slack_index[slack_id] = cache_key

        # WI-125 Phase 2 — also project into the unified identifier index.
        self._index_identifiers(entity, cache_key)

    # ──────────────────────────────────────────────────────────────────
    # WI-125 Phase 2 — unified identifier index + reconciliation
    # ──────────────────────────────────────────────────────────────────

    def _project_identifiers(self, entity: Person) -> List[Identifier]:
        """Project a person note's frontmatter into its PERSON-resolving typed
        identifiers (model §2). Lenient by design: anything that won't parse is
        skipped, NOT raised — the legacy per-kind dicts remain the permissive
        lookup surface during transition, so a malformed-but-present field still
        resolves the old way while this typed index just omits it.

        Audited against the live vault (942 notes, 2026-06-13): email/phone/
        whatsapp/linkedin parse with ZERO failures, so this loses nothing real.
        `slack` is deliberately NOT projected: the frontmatter carries a bare
        handle with no workspace, and a typed SlackUserId requires one — only 2
        notes have slack, and they stay on `_slack_index` until frontmatter
        carries a workspace (a later cut). EmailDomain (company) is also omitted:
        this repo indexes persons, and Company isn't activated this cut.
        """
        ids: List[Identifier] = []

        def add(parser, raw):
            if raw is None or (isinstance(raw, str) and not raw.strip()):
                return
            try:
                ids.append(parser(raw))
            except IdentifierError:
                pass  # lenient — legacy per-kind dict still indexes it

        for email in (entity.emails or []):
            add(Email.parse, email)
        for phone in (entity.phones or []):
            add(Phone.parse, phone)
        if entity.whatsapp:
            add(WhatsAppJID.parse, entity.whatsapp)
        if entity.linkedin:
            add(LinkedInSlug.parse, entity.linkedin)
        return ids

    def _index_identifiers(self, entity: Person, cache_key: str) -> None:
        """Insert a person's identifiers into the unified index, detecting
        cross-entity collisions (the reconciliation check, model §2).

        On collision (a key already mapped to a DIFFERENT entity) the key is
        recorded to `_conflict_sets` naming every entity it's been seen on, and
        a loud WARN fires. The stored value is last-writer-wins — byte-identical
        to the legacy per-kind dicts' overwrite semantics (both iterate the same
        glob order in `load`), so Phase-3 resolution through this index returns
        the same entity legacy lookups do. Never merges, never raises: a conflict
        is an observability output, not a behavior change.

        Note: a person whose `whatsapp` equals one of their `phones` produces the
        same `phone:` key twice — same EntityRef, so NOT a conflict (idempotent).
        Requirement (b) of the model's check ("no entity with an identifier is
        unreachable") is subsumed here: an entity shadowed out of the index by a
        later collision is, by construction, a participant in that collision's
        `_conflict_sets` record — so naming all participants surfaces it.
        """
        ref = EntityRef(entity_type=self.type_name, canonical_key=cache_key)
        for ident in self._project_identifiers(entity):
            key = ident.key
            existing = self._identifier_index.get(key)
            if existing is not None and existing != ref:
                seen = self._conflict_sets.setdefault(key, {existing})
                seen.add(ref)
                logger.warning(
                    "identity reconciliation conflict: identifier %r maps to "
                    "multiple persons: %s (last-wins=%s)",
                    key,
                    sorted(r.canonical_key for r in seen),
                    ref.canonical_key,
                )
            self._identifier_index[key] = ref

    @property
    def conflicts(self) -> List[IdentifierConflict]:
        """The reconciliation conflicts found at index-build time (model §2).

        One record per colliding identifier key, naming every entity the key was
        seen on. The library exposes; the orchestrator persists to
        `state/identity-conflicts.json` and alarms (the WI-095 state-file split).
        Empty when the vault has no ambiguous identifiers.
        """
        self._ensure_loaded()
        return [
            IdentifierConflict(
                identifier_key=key,
                entities=tuple(
                    sorted(refs, key=lambda r: (r.entity_type, r.canonical_key))
                ),
            )
            for key, refs in sorted(self._conflict_sets.items())
        ]

    def _clear_indexes(self) -> None:
        """Clear custom indexes on refresh."""
        self._email_index.clear()
        self._phone_index.clear()
        self._alias_index.clear()
        self._slack_index.clear()
        self._identifier_index.clear()
        self._conflict_sets.clear()

    def _remove_entity_from_indexes(self, entity: Person, cache_key: str) -> None:
        """Remove a person's entries from all indexes."""
        # Remove emails from index
        for email in entity.emails:
            if email:
                email_lower = email.lower()
                if self._email_index.get(email_lower) == cache_key:
                    del self._email_index[email_lower]

        # Remove phones from index
        for phone in entity.phones:
            norm = normalize_phone(phone)
            if norm and self._phone_index.get(norm) == cache_key:
                del self._phone_index[norm]

        # Remove WhatsApp from index
        if entity.whatsapp:
            norm = normalize_phone(entity.whatsapp)
            if norm and self._phone_index.get(norm) == cache_key:
                del self._phone_index[norm]

        # Remove aliases from index
        for alias in entity.aliases:
            if alias:
                alias_lower = alias.lower()
                if self._alias_index.get(alias_lower) == cache_key:
                    del self._alias_index[alias_lower]

        # Remove Slack from index
        if entity.slack:
            slack_id = entity.slack.lstrip("@").lower()
            if self._slack_index.get(slack_id) == cache_key:
                del self._slack_index[slack_id]

        # WI-125 Phase 2 — remove from the unified identifier index. Mirrors the
        # per-kind pattern (delete only the keys still pointing at this entity).
        # `_conflict_sets` is left intact: it's load-time reconciliation forensics
        # that's rebuilt wholesale on the next load()/refresh(); a mid-session
        # update_fields is an edge case not worth partial-conflict bookkeeping.
        ref = EntityRef(entity_type=self.type_name, canonical_key=cache_key)
        for ident in self._project_identifiers(entity):
            if self._identifier_index.get(ident.key) == ref:
                del self._identifier_index[ident.key]

    def get_by_email(self, email: str) -> Optional[Person]:
        """
        Get a person by email address.

        Args:
            email: Email address to look up

        Returns:
            Person if found, None otherwise
        """
        self._ensure_loaded()
        email_lower = email.lower().strip()
        cache_key = self._email_index.get(email_lower)
        return self._cache.get(cache_key) if cache_key else None

    def get_by_phone(self, phone: str) -> Optional[Person]:
        """
        Get a person by phone number.

        Handles various formats and country code variations.

        Args:
            phone: Phone number in any format

        Returns:
            Person if found, None otherwise
        """
        self._ensure_loaded()
        digits = normalize_phone(phone)
        if not digits:
            return None

        # Direct lookup
        cache_key = self._phone_index.get(digits)
        if cache_key:
            return self._cache.get(cache_key)

        # Fuzzy match with country code handling
        for indexed_phone, cache_key in self._phone_index.items():
            if phones_match(digits, indexed_phone):
                return self._cache.get(cache_key)

        return None

    def get_by_alias(self, alias: str) -> Optional[Person]:
        """
        Get a person by alias/nickname.

        Args:
            alias: Alias to look up

        Returns:
            Person if found, None otherwise
        """
        self._ensure_loaded()
        alias_lower = alias.lower().strip()
        cache_key = self._alias_index.get(alias_lower)
        return self._cache.get(cache_key) if cache_key else None

    def get_by_slack(self, slack_id: str) -> Optional[Person]:
        """
        Get a person by Slack user ID or handle.

        Handles both formats:
        - User ID: "U052R9S0RB6"
        - Handle: "@jsmith" or "jsmith"

        Args:
            slack_id: Slack user ID or handle

        Returns:
            Person if found, None otherwise
        """
        self._ensure_loaded()
        # Normalize: strip @ and lowercase
        slack_normalized = slack_id.lstrip("@").lower().strip()
        cache_key = self._slack_index.get(slack_normalized)
        return self._cache.get(cache_key) if cache_key else None

    def resolve(self, query: str) -> Optional[Person]:
        """
        Resolve a query to a Person using multiple strategies.

        Tries in order:
        1. Exact name match
        2. Alias match
        3. Email match (if query contains @)
        4. Phone match (if query looks like phone number)
        5. Partial name match

        Args:
            query: Name, email, phone, or alias to search

        Returns:
            Person if found, None otherwise
        """
        self._ensure_loaded()

        if not query:
            return None

        query = query.strip()
        query_lower = query.lower()

        # 1. Exact name match
        if query_lower in self._cache:
            return self._cache[query_lower]

        # 2. Alias match
        if query_lower in self._alias_index:
            cache_key = self._alias_index[query_lower]
            return self._cache.get(cache_key)

        # 3. Email match
        if "@" in query_lower:
            cache_key = self._email_index.get(query_lower)
            if cache_key:
                return self._cache.get(cache_key)

        # 4. Phone match
        digits = normalize_phone(query)
        if len(digits) >= 7:
            person = self.get_by_phone(query)
            if person:
                return person

        # 5. Partial name match (whole words only)
        for name, person in self._cache.items():
            if query_lower in name.split():
                return person

        return None

    def resolve_all(
        self,
        query: str,
        company: Optional[str] = None,
    ) -> List[ResolveCandidate]:
        """Multi-candidate ranked resolve with optional company-hint disambiguation.

        WI-018 (2026-06-01) — built to fix the active dupe-creation bug surfaced
        in orchestrator Phase 0 trace. resolve() returns a single Optional[Person]
        and stops at the first cascade hit; resolve_all returns ALL plausible
        candidates ranked by confidence, with optional company-hint boost for
        the partial-name case.

        Cascade (each contributes one candidate per match; deduped by person):
          1. Exact name match (case-insensitive)      → 1.0
          2. Alias match                              → 1.0
          3. Email match (if query has '@')           → 1.0
          4. Phone match (if query is phone-shaped)   → 1.0
          5. Token-subset match: query's tokens ⊆ candidate's tokens, or
             vice versa, with ≥2 tokens shared       → 0.65
          6. Partial-name (single-token, whole-word)  → 0.6

        Company-hint bump: when `company` is provided AND a candidate's company
        matches case-insensitively, confidence is bumped by +0.25 (capped at 1.0;
        see the code at person.py:~476 — this docstring previously said +0.2, a
        drift fixed in WI-117). This catches "Emily M" + company="Speechmatics" →
        canonical Emily Mendes bumped 0.65 → 0.90 ≥ 0.85 cutoff for safe reuse,
        and is the mechanism the WI-103 Naomi Pavie acceptance gate depends on.

        Returns:
            List of ResolveCandidate sorted by confidence descending. Empty if
            no candidate scored above the noise floor (0.5).
        """
        self._ensure_loaded()

        if not query or not query.strip():
            return []

        query = query.strip()
        query_lower = query.lower()
        query_tokens = set(query_lower.split())

        # Collect candidates by (person_name, best_signal) — dedupe per-person
        # but track best signal across multiple matches.
        by_person: dict[str, ResolveCandidate] = {}

        def record(person: Person, confidence: float, matched_via: str):
            existing = by_person.get(person.name)
            if existing is None or confidence > existing.confidence:
                by_person[person.name] = ResolveCandidate(
                    person=person,
                    confidence=confidence,
                    matched_via=matched_via,
                )

        # 1. Exact name match
        if query_lower in self._cache:
            record(self._cache[query_lower], 1.0, "exact-name")

        # 2. Email match — more specific than alias; run first so it wins
        # the label race when an alias also contains the email
        if "@" in query_lower:
            cache_key = self._email_index.get(query_lower)
            if cache_key:
                person = self._cache.get(cache_key)
                if person:
                    record(person, 1.0, "email")

        # 3. Alias match
        if query_lower in self._alias_index:
            cache_key = self._alias_index[query_lower]
            person = self._cache.get(cache_key)
            if person:
                record(person, 1.0, "alias")

        # 4. Phone match
        digits = normalize_phone(query)
        if len(digits) >= 7:
            person = self.get_by_phone(query)
            if person:
                record(person, 1.0, "phone")

        # 5. Token-subset / token-overlap matching
        # For each cached name, compute token overlap with the query.
        for cache_key, person in self._cache.items():
            cache_tokens = set(cache_key.split())
            if not cache_tokens:
                continue
            if cache_tokens == query_tokens:
                continue  # already caught by exact-name
            shared = cache_tokens & query_tokens
            # Skip if shared is just trivial first-name match with no other tokens
            if not shared:
                continue
            # Token-subset (one side fully contained in the other) requires ≥2 shared
            if (query_tokens.issubset(cache_tokens) or cache_tokens.issubset(query_tokens)):
                if len(shared) >= 2:
                    record(person, 0.65, "token-subset")
                elif len(query_tokens) == 1 and shared:
                    # 1-token query that's a whole word in the cache key — partial name
                    record(person, 0.6, "partial-name")

        # 6. Short-form first-token + last-initial style match
        # E.g. query = "Emily M" against cache "emily mendes". Requires company
        # hint to confirm — without it, this match stays low confidence (< 0.5)
        # and gets filtered out below.
        if len(query_tokens) == 2:
            qparts = query_lower.split()
            if len(qparts[1]) <= 2:  # "M", "M.", "Mc"
                for cache_key, person in self._cache.items():
                    cparts = cache_key.split()
                    if len(cparts) >= 2:
                        if (cparts[0] == qparts[0]
                                and cparts[1].startswith(qparts[1].rstrip("."))):
                            record(person, 0.6, "partial-name")

        # Company-hint bump
        # Matches when:
        #   (a) canonical's company field matches case-insensitively, OR
        #   (b) canonical's name contains the company as a whole-word token
        #       (catches the mangled-stub case where company got concatenated
        #       into the name, e.g. @Naomi Pavie Speechmatics.md with
        #       company='' but "speechmatics" in the name).
        if company:
            company_lower = company.lower().strip()
            for name, cand in list(by_person.items()):
                canonical_company = (cand.person.company or "").lower().strip()
                canonical_name_tokens = set(name.lower().split())
                company_matches = (
                    canonical_company == company_lower
                    or company_lower in canonical_name_tokens
                )
                if company_matches:
                    new_conf = min(1.0, cand.confidence + 0.25)
                    if new_conf > cand.confidence:
                        by_person[name] = ResolveCandidate(
                            person=cand.person,
                            confidence=new_conf,
                            matched_via=f"{cand.matched_via}+company-hint",
                        )

        # Filter noise floor + sort
        candidates = [c for c in by_person.values() if c.confidence >= 0.5]
        candidates.sort(key=lambda c: c.confidence, reverse=True)
        return candidates

    def find_or_create_stub(
        self,
        name: str,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        company: Optional[str] = None,
        auto_created: bool = True,
        confidence_threshold: float = 0.85,
        created_by: Optional[str] = None,
    ) -> Tuple[Person, bool]:
        """Lookup-before-create entry point. Replaces ad-hoc create_stub calls
        scattered across orchestrator, HAL9000, and exocortex.

        WI-019 (2026-06-01) — surfaced from orchestrator Phase 0 trace which
        identified 4 stub-creation paths all using too-narrow lookups (just
        get_by_email + resolve), creating duplicates when canonicals have
        empty emails or mangled names. find_or_create_stub uses resolve_all
        with company-hint disambiguation, then falls through to create_stub
        only when no high-confidence match exists.

        On reuse, identifier write-back: if the call supplied a new email/phone
        not on the canonical record, append it. Future lookups have stronger
        signal.

        Returns:
            (Person, created_new: bool). created_new is True iff a new stub
            was written; False if an existing record was reused.

        Acceptance gate from orchestrator/docs/find-or-create-stub.md:
          Caller passes ('Naomi Pavie', email='naomi@speechmatics.com',
          company='Speechmatics') with existing mangled canonical
          'Naomi Pavie Speechmatics'. Must REUSE, not create a duplicate.

        WI-117 (2026-06-07) — two additions, both at this door so every channel
        gets them:
          1. Name-cleaning BEFORE lookup. The query is run through
             clean_person_name (safe recoveries: digits, calendar/archive
             prefixes, 'unknown contact') and a CORROBORATED company-suffix
             strip (only when the trailing token is a known company AND it's
             corroborated by company= or the email domain). 'Darryl Friend Kato'
             + @kato.app → 'Darryl Friend' → exact-name match (1.0) → reuse.
             The strip is corroborated-only on purpose: 'Emma Roberts Kato' with
             no corroboration is NOT stripped, so it can't wrong-merge onto a
             bare 'Emma Roberts' canonical. resolve_all's tiers/thresholds are
             untouched (the +0.25 company-hint reuse WI-103 relies on is
             preserved).
          2. Weak-identity guard. When auto_created=True and no match was found,
             a bare single-token-no-id name or a social-handle raises
             WeakIdentityError (the name is valid, the identity's just too weak
             to safely mint a new note for someone Dave likely already knows).
             Gated on auto_created so manual single-name notes are untouched;
             existing single-name canonicals (@Adam) are still REUSED via
             exact-match before the guard can fire.

        Raises:
            NameValidationError: the created name is a Tier-1 non-person string
              (only on the create path, from create_stub).
            WeakIdentityError: auto_created and the identity is too weak to
              create (no match found first).
        """
        self._ensure_loaded()

        # WI-117: clean the query before lookup. Non-company recoveries are
        # always safe; the company-suffix strip is corroborated-only (see
        # _strip_corroborated_company_suffix). The cleaned name is used for the
        # name-based lookup AND as the created name (lookup-clean == creation-
        # name; both safe — the strip is idempotent and conservative-keep on
        # no-corroboration means worst case is "no worse than today").
        lookup_name = self._clean_query_for_lookup(name, email=email, company=company)

        # Strategy 1: exact identifier matches (email/phone) — strongest signal.
        # Name-independent, so a strong identifier reuses even past a weak name.
        if email:
            existing = self.get_by_email(email)
            if existing:
                self._writeback_identifier(existing, email=email)
                return existing, False

        if phone:
            existing = self.get_by_phone(phone)
            if existing:
                self._writeback_identifier(existing, phone=phone)
                return existing, False

        # Strategy 2: resolve_all with company hint, on the CLEANED name.
        if lookup_name:
            candidates = self.resolve_all(lookup_name, company=company)
            if candidates and candidates[0].confidence >= confidence_threshold:
                existing = candidates[0].person
                self._writeback_identifier(existing, email=email, phone=phone)
                return existing, False

        # WI-117 weak-identity guard: only when about to auto-create AND no
        # match was found above. Manual creates (auto_created=False) skip it.
        if auto_created:
            reason = weak_identity_reason(lookup_name, email=email, phone=phone)
            if reason:
                logger.info(
                    "find_or_create_stub: refusing weak-identity auto-create "
                    "(%s) for name=%r email=%r phone=%r",
                    reason, name, email, phone,
                )
                raise WeakIdentityError(reason)

        # Strategy 3: no high-confidence match → create new stub (cleaned name)
        # WI-119: created_by passes through to creation only — the reuse
        # branches above never write it (provenance records creation, not reuse).
        new_person = self.create_stub(
            name=lookup_name,
            email=email,
            phone=phone,
            company=company,
            auto_created=auto_created,
            created_by=created_by,
        )
        return new_person, True

    # ──────────────────────────────────────────────────────────────────
    # WI-117 name-cleaning helpers (corroborated company-suffix strip)
    # ──────────────────────────────────────────────────────────────────

    def _clean_query_for_lookup(
        self,
        name: str,
        email: Optional[str] = None,
        company: Optional[str] = None,
    ) -> str:
        """Clean a query name for find_or_create_stub (WI-117).

        Two stages:
          1. clean_person_name WITHOUT known_companies — the unconditionally-safe
             recoveries (trailing/embedded digits, calendar/archive prefixes,
             'unknown contact' suffix). known_companies is deliberately NOT
             passed: its unconditional company strip would collapse
             'Emma Roberts Kato' onto a bare 'Emma Roberts' with no corroboration
             (a wrong merge). email is NOT passed either — clean_person_name's
             email-domain strip skips the known-company sanity check; we do the
             corroborated strip ourselves in stage 2.
          2. _strip_corroborated_company_suffix — the conservative strip
             (token ∈ known-companies AND (company== OR email-domain match)).
        """
        if not name:
            return name
        cleaned = clean_person_name(name)
        cleaned = self._strip_corroborated_company_suffix(
            cleaned, company=company, email=email
        )
        return cleaned

    def _strip_corroborated_company_suffix(
        self,
        name: str,
        company: Optional[str] = None,
        email: Optional[str] = None,
    ) -> str:
        """Strip a trailing company token from `name` ONLY when corroborated
        (WI-117 Decision 2 — the wrong-merge safety belt).

        Strips trailing token(s) T (1–3-word windows, longest first) iff:
          - T is in the vault's known-companies set, AND
          - (company == T case-insensitively) OR
            (the email domain's primary label == T, lowercased/spaces-removed),
            where primary label = domain.split('.')[0] (matching
            clean_person_name's existing convention).
        Never strips below 2 remaining tokens. If nothing is corroborated, the
        name is returned VERBATIM (no worse than today).

        Examples (T='Kato'/'Speechmatics' assumed in known-companies):
          'Darryl Friend Kato',  company='Kato'                 → 'Darryl Friend'
          'Darryl Friend Kato',  email='d@kato.app'             → 'Darryl Friend'
          'Naomi Pavie Speechmatics', email='n@speechmatics.com'→ 'Naomi Pavie'
          'Emma Roberts Kato',   (no company, no email)         → 'Emma Roberts Kato'  (no strip)
          'Emma Kato',           anything                        → 'Emma Kato'          (2 tokens, guard)
        """
        if not name:
            return name
        words = name.split()
        if len(words) < 3:
            # Need ≥3 tokens to strip ≥1 and keep ≥2. (Also avoids building the
            # company set for the common 2-token case.)
            return name

        company_lower = (company or "").lower().strip()
        domain_label = ""
        if email and "@" in email:
            domain_label = email.lower().split("@", 1)[1].split(".")[0]

        # Nothing can corroborate → keep verbatim (and skip the company scan).
        if not company_lower and not domain_label:
            return name

        known_lower = {c.lower() for c in self._known_companies()}
        if not known_lower:
            return name

        for n in (3, 2, 1):
            if len(words) - n < 2:
                continue
            suffix_lower = " ".join(words[-n:]).lower()
            if suffix_lower not in known_lower:
                continue
            suffix_nospace = suffix_lower.replace(" ", "")
            corroborated = (
                (company_lower and suffix_lower == company_lower)
                or (domain_label and (suffix_lower == domain_label
                                      or suffix_nospace == domain_label))
            )
            if corroborated:
                return " ".join(words[:-n])
        return name

    def _known_companies(self) -> set:
        """Build the known-companies set for corroborated name-cleaning (WI-117).

        Built PER-CALL (no derived-set cache, no cross-repo invalidation —
        that machinery was cut as over-engineering; exocortex builds the same
        set per-meeting and perf is fine). Union of Person.company values (free
        — this repo is already loaded) and CompanyRepository names (a lazily-held
        instance so company files are scanned at most once per process, same
        lifetime as this repo's own cache). Degrades to the person-company set
        if CompanyRepository is unavailable.
        """
        companies = {
            p.company.strip()
            for p in self.get_all()
            if p.company and p.company.strip()
        }
        try:
            if self._company_repo_for_cleaning is None:
                from .company import CompanyRepository
                self._company_repo_for_cleaning = CompanyRepository(self.vault_path)
            companies |= {
                c.name.strip()
                for c in self._company_repo_for_cleaning.get_all()
                if c.name and c.name.strip()
            }
        except Exception:
            logger.debug(
                "find_or_create_stub: CompanyRepository unavailable for "
                "name-cleaning; using person-company set only"
            )
        return companies

    def _writeback_identifier(
        self,
        person: Person,
        email: Optional[str] = None,
        phone: Optional[str] = None,
    ) -> None:
        """Append newly-observed identifier to a canonical record (WI-019).

        Called from find_or_create_stub on the reuse branch. If the supplied
        email/phone is not already present on the canonical, append it and
        save. No-op if the canonical already has the identifier.
        """
        changed = False
        if email and email not in (person.emails or []):
            person.emails = list(person.emails or []) + [email]
            changed = True
        if phone and phone not in (person.phones or []):
            person.phones = list(person.phones or []) + [phone]
            changed = True
        if changed:
            self.save(person)
            logger.info(
                "find_or_create_stub: wrote back new identifier(s) to '%s' (emails=%s, phones=%s)",
                person.name,
                person.emails,
                person.phones,
            )

    def get_by_role(self, role: str) -> List[Person]:
        """
        Get all people with a specific role.

        Args:
            role: Role to filter by (e.g., "vip", "coaching-client")

        Returns:
            List of people with that role
        """
        self._ensure_loaded()
        return [p for p in self._cache.values() if p.has_role(role)]

    def get_by_company(self, company: str) -> List[Person]:
        """
        Get all people at a company.

        Args:
            company: Company name (case-insensitive)

        Returns:
            List of people at that company
        """
        self._ensure_loaded()
        company_lower = company.lower()
        return [
            p for p in self._cache.values()
            if p.company and p.company.lower() == company_lower
        ]

    def save(self, entity, body: str = "", extra_fields=None, overwrite: bool = True):
        """Override BaseRepository.save() to normalize field-level RFC 2822
        corruption (WI-109).

        Producers sometimes append raw 'Name <email>' / 'Name (email)' strings
        into Person.emails[] and Person.aliases[]. This breaks exact-email
        match in dedupe detection. Normalize at the save boundary:
          - For each entry in emails/aliases, parseaddr it.
          - If it yields a clean (email, display_name) pair, replace the entry
            with the clean email and add the display_name to aliases.
        Dedup-aware: identical clean emails after normalization collapse to one.
        """
        self._normalize_address_fields(entity)
        return super().save(entity, body=body, extra_fields=extra_fields, overwrite=overwrite)

    @staticmethod
    def _normalize_address_fields(person: Person) -> None:
        """In-place normalization of person.emails and person.aliases.

        Walks each list, runs parseaddr on every entry; whenever an entry
        contains '<' or wrapped-in-parens email, replaces it with the clean
        email and moves the display-name to aliases. Dedupes case-insensitively
        while preserving first-seen order.
        """
        def _extract_email_and_name(entry: str) -> Tuple[str, str]:
            """Return (email, display_name). Empty strings if not extractable."""
            if not entry or not isinstance(entry, str):
                return "", ""
            # parseaddr handles 'Name <email>' form natively
            name_p, email_p = parseaddr(entry)
            if email_p and "@" in email_p and "." in email_p:
                return email_p, (name_p or "").strip()
            # Try the parens form: 'Name (email@domain)'
            m = re.match(r"^(.*?)\s*\(\s*([^@\s]+@[^\s)]+)\s*\)\s*$", entry)
            if m:
                return m.group(2).strip(), m.group(1).strip()
            return "", ""

        # Process emails[]: extract clean email, collect display names for aliases
        new_emails: List[str] = []
        extracted_names: List[str] = []
        seen_emails_lower = set()
        for entry in list(person.emails or []):
            email, display = _extract_email_and_name(entry)
            if email:
                if email.lower() not in seen_emails_lower:
                    new_emails.append(email)
                    seen_emails_lower.add(email.lower())
                if display:
                    extracted_names.append(display)
            else:
                # Couldn't parseaddr — keep as-is (rare; only if entry was malformed)
                if entry and entry.lower() not in seen_emails_lower:
                    new_emails.append(entry)
                    seen_emails_lower.add(entry.lower())
        person.emails = new_emails

        # Process aliases[]: same logic, but emails extracted go to emails[] (if not
        # already there), and the cleaned alias stays in aliases[]
        new_aliases: List[str] = []
        seen_aliases_lower = set()
        for entry in list(person.aliases or []):
            email, display = _extract_email_and_name(entry)
            if email:
                # The alias was a wrapped email — add the clean email to emails
                if email.lower() not in seen_emails_lower:
                    person.emails.append(email)
                    seen_emails_lower.add(email.lower())
                # Add display name as alias if extracted
                if display and display.lower() not in seen_aliases_lower:
                    new_aliases.append(display)
                    seen_aliases_lower.add(display.lower())
            else:
                if entry and entry.lower() not in seen_aliases_lower:
                    new_aliases.append(entry)
                    seen_aliases_lower.add(entry.lower())
        # Also add any extracted display names from emails[] that aren't already there
        for n in extracted_names:
            if n and n.lower() not in seen_aliases_lower:
                new_aliases.append(n)
                seen_aliases_lower.add(n.lower())
        person.aliases = new_aliases

    def create_stub(
        self,
        name: str,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        company: Optional[str] = None,
        auto_created: bool = True,
        created_by: Optional[str] = None,
    ) -> Person:
        """
        Create a minimal stub Person and save to vault.

        Useful for creating placeholder contacts from meeting attendees, or
        from phone-only channels (iMessage, WhatsApp) where no name signal is
        available — in which case the caller passes `name` set to the phone
        string so the stub is identifiable by phone until enrichment confirms
        a real name.

        Args:
            name: Person's name (or phone string if no name is known)
            email: Optional email address
            phone: Optional phone number (E.164 preferred, e.g. "+447739341679")
            company: Optional company name
            auto_created: Mark as auto-created for later review
            created_by: WI-119 provenance — the writer's self-label (e.g.
                "contact_normalizer", "exocortex-meetings"). Written once at
                creation, never mutated afterward (unlike auto_created, which
                the enricher flips — a workflow flag, not provenance). Falsy /
                non-string → recorded as "unknown" + WARN, the loud-fail
                sentinel for unlabeled code writers.

        Returns:
            The created Person entity
        """
        from datetime import datetime

        # WI-017: defensive RFC 2822 parse. If `name` looks like
        # "Display Name <email@domain>" form, separate it cleanly so the
        # regex sanitizer below doesn't mangle it into something like
        # "Display Name emailatdomaincom". This protects against any caller
        # passing the raw sender field from a scanner.
        parsed_name, parsed_email = parseaddr(name)
        if parsed_email and "@" in parsed_email:
            # An email was extracted from the input. The caller's explicit
            # `email` arg wins if present; otherwise we adopt the parsed one.
            if not email:
                email = parsed_email
            # Display-name part if present, else fall back to email local-part.
            name = parsed_name or parsed_email.split("@", 1)[0]

        # WI-105: boundary validation. Tier 1 patterns (calendar prefix,
        # archive prefix, 'unknown contact', RFC 2822 leak, etc.) raise
        # NameValidationError — producers must fix. Tier 2 patterns
        # (whitespace) get cleaned transparently and logged at INFO so
        # the WI-105 invariant can detect drift.
        # Phone-sentinel allowance: WI-083 path passes name="+447..." with
        # phone="+447..."; recognize that pattern and bypass digit-rejection.
        # Empty-name allowance: legacy fallback uses email local-part as the
        # name. Skip the validator in that case and let the existing
        # `if not clean_name` branch below pick up the fallback.
        if name and name.strip():
            _allow_phone_sentinel = bool(phone) and name.strip().lstrip("+").isdigit()
            clean_result = NameValidator().clean(name, allow_phone_sentinel=_allow_phone_sentinel)
            if clean_result.repairs_applied:
                logger.info(
                    "create_stub: name repairs applied %s — input=%r output=%r",
                    clean_result.repairs_applied, name, clean_result.cleaned_name,
                )
            name = clean_result.cleaned_name

        # WI-111 (Decision 6): NameValidator.clean() above is the SOLE name
        # authority and is closed under validate_strict — store its output
        # verbatim. The legacy `clean_name = re.sub(r'[^\w\s-]', '', name)`
        # mangler that used to run here is DELETED: it manufactured tier1
        # failures from validator-passing inputs ('Dave -> X (Co)' became
        # 'Dave - X Co', a calendar_prefix) and corrupted valid names
        # (O'Brien -> OBrien, Dr. Smith -> Dr Smith). Path-hostile chars are
        # now rejected at the validator boundary, not stripped here.
        clean_name = name.strip() if name else ""
        if not clean_name:
            clean_name = email.split("@")[0] if email else "Unknown"

        # Build aliases from email
        aliases = [email] if email else []

        phones = [phone] if phone else []

        person = Person(
            name=clean_name,
            aliases=aliases,
            emails=[email] if email else [],
            phones=phones,
            company=company or "",
            tags=["person"],
            created=datetime.now().strftime("%Y-%m-%d"),
        )

        # WI-119: provenance. Always written; "unknown" + WARN surfaces
        # unlabeled writers. Falsy ('' / None) and non-string values are
        # treated as unlabeled (an empty label is an unlabeled writer).
        if not created_by or not isinstance(created_by, str):
            logger.warning(
                "create_stub: no created_by provenance for %r — recording 'unknown'",
                clean_name,
            )
            created_by = "unknown"
        extra_fields = {"created_by": created_by}
        if auto_created:
            extra_fields["auto_created"] = True
        self.save(person, body=get_default_body("person"), extra_fields=extra_fields)

        return person

    def append_to_timeline(
        self,
        person: Person,
        entry: str,
        deduplicate_key: Optional[str] = None,
    ) -> bool:
        """
        Append an entry to a person's Timeline section.

        Inserts the entry at the start of the ## Timeline section,
        preserving existing content.

        Args:
            person: The person whose timeline to update
            entry: The full entry to append (e.g., "### Dec 3, 2025\\n[[Meeting]]...")
            deduplicate_key: Optional string to check for duplicates.
                            If provided and found in existing content, skip the update.

        Returns:
            True if entry was added, False if skipped (duplicate or error)

        Raises:
            ValueError: If person not found in repository
        """
        file_path = self.get_file_path(person.name)
        if not file_path or not file_path.exists():
            raise ValueError(f"Person file not found: {person.name}")

        try:
            content = file_path.read_text(encoding="utf-8")

            # Check for duplicate if key provided
            if deduplicate_key and deduplicate_key in content:
                logger.debug(f"Timeline entry already exists for {person.name}: {deduplicate_key}")
                return False

            # Find the Timeline section
            timeline_marker = "## Timeline"
            if timeline_marker not in content:
                logger.warning(f"No Timeline section found in {person.name}")
                return False

            # Ensure entry starts with newline for clean formatting
            formatted_entry = entry if entry.startswith("\n") else f"\n{entry}"

            # Insert after "## Timeline" marker
            parts = content.split(timeline_marker, 1)
            if len(parts) != 2:
                return False

            new_content = parts[0] + timeline_marker + formatted_entry + parts[1]
            file_path.write_text(new_content, encoding="utf-8")

            logger.info(f"Updated timeline for {person.name}")
            return True

        except Exception as e:
            logger.warning(f"Failed to update timeline for {person.name}: {e}")
            return False

    def append_to_body_section(
        self,
        person: Person,
        section: str,
        content: str,
        operation: Literal["append", "prepend"] = "append",
        deduplicate_key: Optional[str] = None,
        create_if_missing: bool = True,
    ) -> bool:
        """Add ``content`` to a person's ``## {section}`` body section (WI-111).

        The generic body-section writer the migrated writers (enricher, intro-
        ducer, scheduler) route through instead of MCP ``patch_vault_file``.
        Wraps the ``body_sections`` module helpers around a body-safe read/write
        that carries the frontmatter through VERBATIM (it is never re-serialized
        or re-normalized — body writes must not touch frontmatter).

        Deliberately distinct from ``append_to_timeline`` (which prepends and
        dedups whole-file): this method supports both operations and dedups
        SECTION-SCOPED, so e.g. "Introduced by [[X]]" may legitimately appear in
        both Timeline and Notes.

        Args:
            person: whose note to write (looked up by ``person.name``).
            section: section name without the leading ``## `` (e.g. "Notes").
            content: text to add (no leading ``## ``).
            operation: "append" (end of section, default) or "prepend" (start).
            deduplicate_key: if set AND already present in the TARGET section,
                skip the write and return False.
            create_if_missing: create the ``## {section}`` if absent (default
                True); when False and the section is absent, no-op returns False.

        Returns:
            True if written; False if deduped, skipped (missing section with
            ``create_if_missing=False``), or the file has no frontmatter fence.

        Raises:
            ValueError: if the person file does not exist, or ``operation`` is
                not "append"/"prepend" (loud-fail — never silently mis-write).
        """
        if operation not in ("append", "prepend"):
            raise ValueError(
                f"append_to_body_section: operation must be 'append' or "
                f"'prepend', got {operation!r}"
            )

        file_path = self.get_file_path(person.name)
        if not file_path or not file_path.exists():
            raise ValueError(f"Person file not found: {person.name}")

        try:
            content_raw = file_path.read_text(encoding="utf-8")

            # Split frontmatter and body (body-safe pattern, mirrors To-Discuss).
            if not content_raw.startswith("---"):
                logger.warning(
                    f"append_to_body_section: {person.name} has no frontmatter "
                    f"fence — skipping"
                )
                return False
            parts = content_raw.split("---", 2)
            if len(parts) < 3:
                logger.warning(
                    f"append_to_body_section: {person.name} frontmatter malformed "
                    f"— skipping"
                )
                return False
            frontmatter = parts[1]
            body = parts[2].lstrip("\n")

            # None ⇒ section absent; "" / text ⇒ present (possibly empty).
            existing_section = get_section(body, section)

            # create_if_missing=False + absent section → genuine no-op.
            if existing_section is None and not create_if_missing:
                return False

            # Section-scoped dedup (NOT whole-file — same key may live in
            # Timeline AND Notes).
            if deduplicate_key and existing_section and deduplicate_key in existing_section:
                return False

            if operation == "prepend":
                new_body = prepend_to_section(
                    body, section, content, create_if_missing=create_if_missing
                )
            else:
                new_body = append_to_section(
                    body, section, content, create_if_missing=create_if_missing
                )

            # Re-assemble carrying frontmatter through verbatim.
            new_content = f"---{frontmatter}---\n{new_body}"
            file_path.write_text(new_content, encoding="utf-8")
            logger.info(
                f"append_to_body_section: {operation} to '{section}' for {person.name}"
            )
            return True

        except Exception as e:
            logger.warning(
                f"Failed to append_to_body_section for {person.name}: {e}"
            )
            return False

    # =========================================================================
    # To Discuss Methods
    # =========================================================================

    def _get_body_content(self, person: Person) -> Optional[str]:
        """Get the body content of a person's markdown file."""
        file_path = self.get_file_path(person.name)
        if not file_path or not file_path.exists():
            return None

        content = file_path.read_text(encoding="utf-8")

        # Split frontmatter and body
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                return parts[2].strip()
        return content

    def get_to_discuss_items(self, person: Person) -> List[ToDiscussItem]:
        """
        Get all To Discuss items for a person.

        Args:
            person: The person to get items for

        Returns:
            List of ToDiscussItem objects, or empty list if none

        Raises:
            ValueError: If person not found in repository
        """
        body = self._get_body_content(person)
        if body is None:
            raise ValueError(f"Person file not found: {person.name}")

        section_content = get_section(body, "To Discuss")
        if not section_content:
            return []

        return parse_to_discuss_items(section_content)

    def add_to_discuss_item(self, person: Person, text: str) -> bool:
        """
        Add a new To Discuss item for a person.

        Creates an unchecked item with today's date.

        Args:
            person: The person to add item for
            text: The item text

        Returns:
            True if item was added, False on error

        Raises:
            ValueError: If person not found in repository
        """
        file_path = self.get_file_path(person.name)
        if not file_path or not file_path.exists():
            raise ValueError(f"Person file not found: {person.name}")

        try:
            content = file_path.read_text(encoding="utf-8")

            # Split frontmatter and body
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    frontmatter = parts[1]
                    body = parts[2].lstrip("\n")
                else:
                    return False
            else:
                return False

            # Get existing items and add new one
            section_content = get_section(body, "To Discuss")
            items = parse_to_discuss_items(section_content) if section_content else []
            new_item = ToDiscussItem.create(text)
            items.append(new_item)

            # Update section
            new_section_content = write_to_discuss_items(items)
            new_body = update_section(body, "To Discuss", new_section_content, create_if_missing=True)

            # Write back
            new_content = f"---{frontmatter}---\n{new_body}"
            file_path.write_text(new_content, encoding="utf-8")

            logger.info(f"Added To Discuss item for {person.name}: {text[:50]}")
            return True

        except Exception as e:
            logger.warning(f"Failed to add To Discuss item for {person.name}: {e}")
            return False

    def update_to_discuss_item(
        self,
        person: Person,
        text: str,
        completed: bool,
    ) -> bool:
        """
        Update a To Discuss item's completion status.

        Args:
            person: The person to update item for
            text: The item text to match (exact match)
            completed: New completion status

        Returns:
            True if item was updated, False if not found or error

        Raises:
            ValueError: If person not found in repository
        """
        file_path = self.get_file_path(person.name)
        if not file_path or not file_path.exists():
            raise ValueError(f"Person file not found: {person.name}")

        try:
            content = file_path.read_text(encoding="utf-8")

            # Split frontmatter and body
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    frontmatter = parts[1]
                    body = parts[2].lstrip("\n")
                else:
                    return False
            else:
                return False

            # Get existing items
            section_content = get_section(body, "To Discuss")
            if not section_content:
                return False

            items = parse_to_discuss_items(section_content)

            # Find and update the item
            found = False
            for item in items:
                if item.text == text:
                    item.completed = completed
                    found = True
                    break

            if not found:
                logger.debug(f"To Discuss item not found for {person.name}: {text[:50]}")
                return False

            # Update section
            new_section_content = write_to_discuss_items(items)
            new_body = update_section(body, "To Discuss", new_section_content)

            # Write back
            new_content = f"---{frontmatter}---\n{new_body}"
            file_path.write_text(new_content, encoding="utf-8")

            status = "completed" if completed else "uncompleted"
            logger.info(f"Marked To Discuss item as {status} for {person.name}: {text[:50]}")
            return True

        except Exception as e:
            logger.warning(f"Failed to update To Discuss item for {person.name}: {e}")
            return False

    def remove_to_discuss_item(self, person: Person, text: str) -> bool:
        """
        Remove a To Discuss item.

        Args:
            person: The person to remove item from
            text: The item text to match (exact match)

        Returns:
            True if item was removed, False if not found or error

        Raises:
            ValueError: If person not found in repository
        """
        file_path = self.get_file_path(person.name)
        if not file_path or not file_path.exists():
            raise ValueError(f"Person file not found: {person.name}")

        try:
            content = file_path.read_text(encoding="utf-8")

            # Split frontmatter and body
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    frontmatter = parts[1]
                    body = parts[2].lstrip("\n")
                else:
                    return False
            else:
                return False

            # Get existing items
            section_content = get_section(body, "To Discuss")
            if not section_content:
                return False

            items = parse_to_discuss_items(section_content)
            original_count = len(items)

            # Filter out the item to remove
            items = [item for item in items if item.text != text]

            if len(items) == original_count:
                logger.debug(f"To Discuss item not found for {person.name}: {text[:50]}")
                return False

            # Update section
            new_section_content = write_to_discuss_items(items)
            new_body = update_section(body, "To Discuss", new_section_content)

            # Write back
            new_content = f"---{frontmatter}---\n{new_body}"
            file_path.write_text(new_content, encoding="utf-8")

            logger.info(f"Removed To Discuss item for {person.name}: {text[:50]}")
            return True

        except Exception as e:
            logger.warning(f"Failed to remove To Discuss item for {person.name}: {e}")
            return False
