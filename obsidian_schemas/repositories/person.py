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
    parse_identifiers,
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
from ..errors import (
    FrontmatterParseError,
    LoudFailError,
    NoteAlreadyExists,
    WriteFailedError,
    bounded_message,
    chainable_cause,
)
from .base import BaseRepository
# WI-021: `normalize_phone` / `phones_match` MOVED to the stdlib-only leaf
# `obsidian_schemas/phone_normalization.py` so `name_gate.py` can name the
# authority without closing writer -> gate -> person -> base -> writer. This is
# a COMPAT RE-EXPORT, not a convenience: two live consumers import these names
# from this module by path (HAL9000 `core/contact_resolver.py:13`, exocortex
# `clients/contacts.py:13`), so `obsidian_schemas.repositories.person.normalize_phone`
# must keep resolving to the relocated function object.
from ..phone_normalization import normalize_phone, phones_match
# WI-021: the gate (for the write-back RIDER on save) and the ONE address
# splitter, which replaces both duplicate parseaddr sites this module carried.
from ..name_gate import gate_write, split_address
from ..writer import model_to_frontmatter
# Module attribute call form throughout (WI-004 D7) — see writer.py's note.
from obsidian_schemas import vault_io

logger = logging.getLogger(__name__)


def _split_frontmatter_fence(content: str, file_path: Path) -> Tuple[str, str]:
    """Return (raw_frontmatter, raw_body) for a fenced note, or raise.

    Callers apply their own normalisation to the body — the writers lstrip("\\n"),
    _get_body_content strips — so this returns the raw spans and changes no bytes.
    """
    if not content.startswith("---"):
        raise FrontmatterParseError("no frontmatter fence", path=file_path)
    parts = content.split("---", 2)
    if len(parts) < 3:
        raise FrontmatterParseError("frontmatter fence not closed", path=file_path)
    return parts[1], parts[2]


# WI-121: a TRAILING parenthetical '(X)' is never part of a legal human name
# ('Louron Pratt (Pendo)', 'Kate Sellwood (PA)') — it is always an annotation.
# Trailing-only ($-anchored), single group ([^()]+ forbids nesting), strip-to-
# empty guarded.
_TRAILING_PAREN_RE = re.compile(r"^(?P<head>.*?)\s*\((?P<inner>[^()]+)\)\s*$")


def _split_trailing_paren(name: str) -> Tuple[str, Optional[str]]:
    """Split a TRAILING '(X)' off a name. Trailing-only, single group, no nesting.

    'Louron Pratt (Pendo)'  -> ('Louron Pratt', 'Pendo')
    'Kate Sellwood (PA)'     -> ('Kate Sellwood', 'PA')
    'Jane (Acme) Smith'      -> ('Jane (Acme) Smith', None)   # paren not trailing
    'Foo (A) (B)'            -> ('Foo (A)', 'B')               # strips the LAST only
    'Foo (A (B))'            -> ('Foo (A (B))', None)          # nested -> [^()] fails -> no strip
    '(Pendo)'                -> ('(Pendo)', None)              # head empty -> keep verbatim
    'Plain Name'             -> ('Plain Name', None)
    """
    if not name:
        return name, None
    m = _TRAILING_PAREN_RE.match(name)
    if not m:
        return name, None
    head = m.group("head").strip()
    inner = m.group("inner").strip()
    if not head or not inner:        # never strip to empty; never derive an empty hint
        return name, None
    return head, inner


# `resolve()`'s own cascade order, which is what breaks a 1.0 tie between two
# DIFFERENT people. `resolve_all` emits email before alias deliberately (see its
# step 2); `resolve` has always answered alias first. WI-023 Cut 3 preserves
# `resolve`'s answer without touching `resolve_all`'s ordering. This is a
# TIE-BREAK over `matched_via`, never a trial order — nothing is tried in it.
_RESOLVE_CASCADE_ORDER = ("exact-name", "alias", "email", "phone")


def select_resolution(query: Optional[str],
                      candidates: List[ResolveCandidate]) -> Optional[Person]:
    """The ONE selection policy resolve() applies to resolve_all()'s ranking.

    Module-level and named so it is one thing rather than a shape re-derived at
    each call site. Its inputs are the candidate list AND the query, because no
    pure function of the candidates can separate the two 0.6 `partial-name`
    sites: `resolve_all` records the SAME confidence under the SAME label for a
    one-token query that must resolve and for a two-token short-form query that
    must not. The discriminant is the query's token count.

    - No candidates → None. Checked FIRST, so a None or empty query never
      reaches the tokenizer and cannot raise.
    - **Single-token query** → the highest confidence; among candidates tied
      there, the one whose `matched_via` ranks first in `_RESOLVE_CASCADE_ORDER`
      (unknown labels last, insertion order breaking any remainder).
    - **Multi-token query** → a candidate only if its confidence is 1.0, ties
      broken the same way. A multi-token query is answerable pre-cut ONLY by the
      four exact arms, every one of which scores 1.0, because the partial-name
      test requires the whole query to be one token of a name.

    A confidence THRESHOLD is the wrong shape here and gets it backwards in both
    directions: the policy must ACCEPT 0.6 (a one-token partial name) while
    REJECTING 0.65 (a multi-token token-subset).

    `matched_via` may carry a `+company-hint` suffix, so the rank is read off
    the label BEFORE the first `+`. `resolve()` passes no company, so from that
    caller the suffix never appears; the rule is stated totally anyway, because
    this is module-level and a future caller may not be `resolve`.
    """
    if not candidates:
        return None

    single_token = len((query or "").strip().split()) <= 1
    best = max(candidate.confidence for candidate in candidates)
    if single_token:
        pool = [c for c in candidates if c.confidence == best]
    else:
        if best < 1.0:
            return None
        pool = [c for c in candidates if c.confidence == 1.0]

    def rank(entry):
        position, candidate = entry
        label = candidate.matched_via.split("+", 1)[0]
        try:
            primary = _RESOLVE_CASCADE_ORDER.index(label)
        except ValueError:
            primary = len(_RESOLVE_CASCADE_ORDER)
        return primary, position

    return min(enumerate(pool), key=rank)[1].person


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
        self._phone_index: dict[str, str] = {}  # normalized phone -> cache_key
        self._alias_index: dict[str, str] = {}  # alias -> cache_key
        self._slack_index: dict[str, str] = {}  # slack ID/handle -> cache_key
        # WI-125 Phase 2 / WI-023 — the unified resolution contract (model §2:
        # `Identifier → EntityRef`), and since WI-023 the ONE authority for
        # EMAIL: `get_by_email` is its only reader and every email-resolving
        # surface goes through that method. The three per-kind dicts above are
        # PERMANENT rather than pending. There is no `Alias` identifier type at
        # all (an alias is a name variant, not a hard identifier); `phones_match`
        # is not transitive, so no key function for it can exist and phones stay
        # on the fuzzy path by design; and `slack` needs a workspace before a
        # typed SlackUserId is constructible (see `_project_identifiers`' own
        # UNBLOCK line). Keyed on `identifier.key`; only PERSON-resolving
        # identifiers land here.
        self._identifier_index: dict[str, EntityRef] = {}
        # Reconciliation findings: identifier key -> the set of EntityRefs it was
        # seen on. Only populated when a key collides (>1 entity) — a real-data
        # duplicate (the WI-119 invariant generalized). Exposed via `.conflicts`.
        self._conflict_sets: dict[str, set] = {}
        # WI-125 Phase 3 — resolution-time conflicts: a single resolve_or_create
        # call whose identifiers point at DIFFERENT people (email→X, phone→Y).
        # Distinct from the load-time `_conflict_sets` (vault-internal dups) but
        # surfaced through the same `.conflicts` accessor (spec §3 / Gate 2). A
        # call-event log — NOT cleared by refresh (it records calls, not state).
        self._resolution_conflicts: List[IdentifierConflict] = []
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
        """Build the phone and alias indexes, and project into the unified
        identifier index — which is where email now lives."""
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
        skipped, NOT raised. For PHONE and ALIAS the per-kind dicts are still the
        permissive lookup surface, so a malformed-but-present value there is
        still reachable. For EMAIL that is no longer true and the leniency has a
        sharper meaning since WI-023: an entry this skips resolves through NO
        door at all.

        The live-corpus grounding for that leniency — how many entries this
        actually drops, per class — is `docs/identity-cutover-corpus-audit.md`.
        A POINTER rather than a figure on purpose: the number it records is a
        reading of a vault that is written to daily, and a figure copied to here
        goes stale exactly the way the one this replaced did.

        `slack` is deliberately NOT projected: the frontmatter carries a bare
        handle with no workspace, and a typed SlackUserId requires one — only 2
        notes have slack, and they stay on `_slack_index` for now.
        UNBLOCK: project `slack` when a person note's frontmatter carries the
        WORKSPACE alongside the handle (e.g. a `slack_workspace:` field, or a
        handle qualified as `<workspace>/<handle>`), since `SlackUserId.parse`
        needs both; until then a bare handle cannot be made into a typed
        identifier without inventing the half that is missing.
        EmailDomain (company) is also omitted: this repo indexes persons, and
        Company isn't activated this cut.
        """
        ids: List[Identifier] = []

        def add(parser, raw):
            if raw is None or (isinstance(raw, str) and not raw.strip()):
                return
            try:
                ids.append(parser(raw))
            except IdentifierError:
                pass  # lenient — phone/alias keep a per-kind dict; email does not

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
        a loud WARN fires. The stored value is last-writer-wins: the last note
        the load glob reaches owns the key. Never merges, never raises: a
        conflict is an observability output, not a behavior change.

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
                    "identity reconciliation conflict: an identifier maps to "
                    "multiple persons: %s (last-wins=%s; the key is on .conflicts)",
                    sorted(r.canonical_key for r in seen),
                    ref.canonical_key,
                )
            self._identifier_index[key] = ref

    @property
    def conflicts(self) -> List[IdentifierConflict]:
        """All ambiguous-identifier findings, of two kinds (spec §3 / Gate 2):

        1. **Load-time** (model §2): an identifier key on >1 note — a vault dup
           (the WI-119 invariant generalized). Keyed on the identifier (`email:…`,
           `linkedin:…`).
        2. **Resolution-time** (Phase 3, Branch A): a single `resolve_or_create`
           call whose identifiers point at different people (`email→X, phone→Y`).
           Keyed `resolve:<k1>|<k2>`.

        The library exposes; the orchestrator persists to
        `state/identity-conflicts.json` and alarms (the WI-095 state-file split).
        Empty when the vault has no ambiguous identifiers and no conflicting
        resolve has been made.
        """
        self._ensure_loaded()
        load_time = [
            IdentifierConflict(
                identifier_key=key,
                entities=tuple(
                    sorted(refs, key=lambda r: (r.entity_type, r.canonical_key))
                ),
            )
            for key, refs in sorted(self._conflict_sets.items())
        ]
        return load_time + list(self._resolution_conflicts)

    def _clear_indexes(self) -> None:
        """Clear custom indexes on refresh."""
        self._phone_index.clear()
        self._alias_index.clear()
        self._slack_index.clear()
        self._identifier_index.clear()
        self._conflict_sets.clear()

    def _remove_entity_from_indexes(self, entity: Person, cache_key: str) -> None:
        """Remove a person's entries from all indexes."""
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
        try:
            ident = Email.parse(email)
        except IdentifierError:
            return None
        ref = self._identifier_index.get(ident.key)
        return self._cache.get(ref.canonical_key) if ref else None

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

        # Fuzzy match with country-code handling. This arm is PERMANENT, and the
        # reason is arithmetic rather than preference: `phones_match` is not
        # TRANSITIVE (0790055852 matches both 44790055852 and 10790055852, which
        # do not match each other), so it is not an equivalence relation, has no
        # quotient, and therefore admits no key function — phones cannot be keyed
        # into `_identifier_index` the way email is. The witness is executable and
        # goes red if anyone "normalizes" the relation:
        # tests/test_identity_endgame.py::test_phones_stay_on_the_fuzzy_path_and_the_reason_is_executable
        #
        # The iterable is a MATERIALIZED snapshot, not the live mapping: a
        # concurrent refresh clears `_phone_index` in place (`_clear_indexes`),
        # which is the half WI-004 left explicitly open on the expectation that
        # phones would leave this path. They do not, so it is closed here.
        for indexed_phone, cache_key in list(self._phone_index.items()):
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
        Resolve a query to a Person — ONE answer, from ONE cascade.

        Since WI-023 Cut 3 this method keeps no match logic of its own. It ranks
        the whole cascade through `resolve_all` and applies `select_resolution`
        to that ranking, so there is one implementation of "what matches" in this
        class rather than two drifting copies of it.

        Nothing is tried in an order here. `resolve_all` emits email BEFORE alias
        (its step 2 comment says why), while this method has always answered the
        alias owner; `_RESOLVE_CASCADE_ORDER` restores that as a TIE-BREAK over
        `matched_via` among candidates of equal confidence. The other half of the
        policy is the query's token count — see `select_resolution`.

        Args:
            query: Name, email, phone, or alias to search

        Returns:
            Person if found, None otherwise
        """
        self._ensure_loaded()

        if not query:
            return None

        return select_resolution(query, self.resolve_all(query))

    def resolve_all(
        self,
        query: str,
        company: Optional[str] = None,
    ) -> List[ResolveCandidate]:
        """Multi-candidate ranked resolve with optional company-hint disambiguation.

        WI-018 (2026-06-01) — built to fix the active dupe-creation bug surfaced
        in orchestrator Phase 0 trace. resolve() returns a single
        Optional[Person] by applying `select_resolution` to THIS function's full
        ranking; resolve_all returns the ranking itself — ALL plausible
        candidates by confidence, with optional company-hint boost for the
        partial-name case.

        Cascade (each contributes one candidate per match; deduped by person):
          1. Exact name match (case-insensitive)      → 1.0
          2. Alias match                              → 1.0
          3. Email match (if query has '@')           → 1.0
          4. Phone match (if query is phone-shaped)   → 1.0
          5. Token-subset match: query's tokens ⊆ candidate's tokens, or
             vice versa, with ≥2 tokens shared       → 0.65
          6. Partial-name (single-token, whole-word)  → 0.6

        Company-hint bump: when `company` is provided AND a candidate's company
        matches case-insensitively, confidence is bumped by +0.25, capped at 1.0
        (the code is the "Company-hint bump" block below; this docstring once
        said +0.2, a drift fixed in WI-117). Two shapes reach it, and they are
        arithmetically different — conflating them is what this paragraph used to
        do:
          - the WI-103 "Naomi Pavie" shape shares TWO tokens with its canonical,
            so it reaches step 5's token-subset arm at 0.65 and bumps to 0.90,
            comfortably over the 0.85 reuse cutoff;
          - the "Emily M" short-form shape shares ONE token, so it CANNOT reach
            that arm (step 5 requires ≥2 shared) — it reaches step 6 at 0.6 and
            bumps to EXACTLY 0.85, landing ON the cutoff with no float slack.
        That second figure is worth stating plainly: any future re-tuning of the
        partial-name score or of the +0.25 bump flips that case from reuse to
        create.

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
            person = self.get_by_email(query)
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
        # E.g. query = "Emily M" against cache "emily mendes". This branch
        # records 0.6, which SURVIVES the >= 0.5 floor below — it is NOT filtered
        # out, and a reader auditing this cascade for inert branches must not
        # conclude otherwise. A company hint bumps an already-surviving candidate
        # (0.6 + 0.25 = exactly the 0.85 reuse threshold); without one the
        # candidate is still offered to a caller that asked for candidates, and
        # it is `resolve`'s selection policy — not this floor — that declines to
        # answer a two-token query with it.
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
        """Lookup-before-create entry point (WI-125 Phase 4 — the engine adapter).

        Same signature, same `(Person, created_new)` return, same exception set
        (`NameValidationError`, `WeakIdentityError` — no new exception; identifier
        conflicts flag to `repo.conflicts`, never raise) as the original. Parses
        the stringly args into typed `Identifier`s and delegates to the
        identifier-first engine `resolve_or_create` (model §4). WI-023 deleted
        the pre-WI-125 body: this method IS the door now, and there is one
        implementation of it.

        Callers (contact_normalizer.py:422 direct; HAL9000 entities.py:178 via
        HTTP) are unchanged — they keep their exact call sites and catch blocks.

        `strict=False` on the parse: a malformed email/phone is skipped (not
        raised), so the adapter never fails where a string path would have
        silently carried the junk to `get_by_email`/`create_stub`. An entry no
        parser accepts resolves through no door and the engine answers on the
        typed identifiers and the name path.

        The evidence that this door's answers did not move across WI-023's cuts
        is COMMITTED DATA rather than a claim: `stub_golden.json` and
        `resolve_golden.json` under `tests/fixtures/identity_endgame/` record
        what this method and `resolve` answered before any of those cuts, and
        the suite replays them on every run.
        """
        ids = parse_identifiers(email=email, phone=phone, strict=False)
        ref, created = self.resolve_or_create(
            ids,
            display_name=name,
            company_hint=company,
            provenance=created_by,
            auto_created=auto_created,
            threshold=confidence_threshold,
        )
        return self._hydrate(ref), created

    # ──────────────────────────────────────────────────────────────────
    # WI-125 Phase 3 — the identity engine: resolve_or_create
    # ──────────────────────────────────────────────────────────────────

    # Resolution priority for the Branch-A best-hit (parity: email before phone,
    # per find_or_create_stub Strategy 1 at person.py Strategy-1). Lower wins.
    # A phone-bearing WhatsAppJID resolves like a Phone (same number → same
    # person), so it shares phone's priority. Richer kinds (linkedin/slack) rank
    # below — no current caller passes them, so they never affect parity; they're
    # there so a future WI-115 producer's richer identifiers resolve generically.
    _IDENTIFIER_PRIORITY = {"email": 0, "phone": 1, "whatsapp_jid": 1}

    def resolve_or_create(
        self,
        identifiers,
        display_name: str,
        company_hint: Optional[str] = None,
        provenance: Optional[str] = None,
        auto_created: bool = True,
        threshold: float = 0.85,
    ) -> Tuple[EntityRef, bool]:
        """The identity engine (model §4) — the identifier-first core that
        `find_or_create_stub` runs through today (the Phase-4 adapter swap has
        happened; see that method's body).

        Its **return-value** behavior — `(resolved_name, created_new)`, side
        effects explicitly outside the contract — is what WI-023's committed
        goldens pin, and it carries **one behavior the string door never had:
        conflict detection** (Branch A). Operates on a typed `set[Identifier]` +
        display name + company *hint* (a company NAME is a display hint, not an
        identifier — `parse_identifiers`' own rule), and returns
        `(EntityRef, created_new)`.

        - **Branch A — identifier hit.** Resolve each PERSON-resolving identifier:
          email through `get_by_email`, which reads the unified index;
          phone through `get_by_phone`, whose UK/US country-code fuzzing stays on
          its own path permanently because `phones_match` admits no key function;
          richer kinds through the unified index directly. The best hit (email
          before phone) is the resolved entity, and it returns on that first hit.
          If hits disagree (`email→X, phone→Y`) it's a **CONFLICT**: still return
          the best hit (no merge, no raise), but record it to `.conflicts` naming
          both candidates (the new observability). No writeback on a hit: the
          matched identifier is already on the note by definition, so a
          writeback-on-hit is a no-op (or, on a fuzzy phone hit, would append a
          format-variant — exactly the dup-noise the identity model reduces);
          skipping it changes no return value and improves vault hygiene.
        - **Branch B — name + corroboration.** Clean the name,
          `resolve_all(cleaned, company_hint)`; ≥ threshold → reuse + writeback
          the supplied email/phone (the meaningful attach case).
        - **Branch C — weak guard then create.** auto_created + weak identity →
          raise `WeakIdentityError` (UNCHANGED this cut — the `needs_resolution`
          flip is a follow-on). Else `create_stub`.
        """
        self._ensure_loaded()

        ids = [i for i in (identifiers or []) if "person" in i.resolves]
        # Extract the leaf strings the existing string-typed methods take — the
        # parity bridge (the leaves stay stable; the typed identifiers are the
        # new interface producers will emit).
        email_str = next((i.value for i in ids if isinstance(i, Email)), None)
        phone_str = next((i.value for i in ids if isinstance(i, Phone)), None)
        if phone_str is None:
            phone_str = next(
                (i.phone_digits for i in ids
                 if isinstance(i, WhatsAppJID) and i.phone_digits),
                None,
            )

        cleaned, derived_company = self._clean_query_for_lookup(
            display_name, email=email_str, company=company_hint
        )
        # WI-121: caller's company_hint wins; the paren-derived company is the
        # fallback resolve hint (unfiltered). On a NEW note, only a known paren-
        # company is stored; the caller's company_hint is stored as-is.
        effective_company = company_hint or derived_company
        create_company = company_hint or self._company_if_known(derived_company)

        # ── Branch A — identifier hits ──────────────────────────────────────
        hits: List[Tuple[Identifier, EntityRef]] = []
        for ident in sorted(ids, key=lambda i: self._IDENTIFIER_PRIORITY.get(i.kind, 2)):
            ref = self._resolve_identifier(ident)
            if ref is not None:
                hits.append((ident, ref))
        if hits:
            _, best_ref = hits[0]  # highest priority wins: email before phone
            if len({r for _, r in hits}) > 1:
                self._record_resolution_conflict(hits)
            return best_ref, False

        # ── Branch B — name + corroboration ─────────────────────────────────
        if cleaned:
            candidates = self.resolve_all(cleaned, company=effective_company)
            if candidates and candidates[0].confidence >= threshold:
                existing = candidates[0].person
                self._writeback_identifier(existing, email=email_str, phone=phone_str)
                return EntityRef(self.type_name, self._get_cache_key(existing)), False

        # ── Branch C — weak guard, then create ──────────────────────────────
        if auto_created:
            reason = weak_identity_reason(cleaned, email=email_str, phone=phone_str)
            if reason:
                logger.info(
                    "resolve_or_create: refusing weak-identity auto-create (%s) "
                    "for name=%r email=%r phone=%r",
                    reason, display_name, email_str, phone_str,
                )
                raise WeakIdentityError(reason)

        new_person = self.create_stub(
            name=cleaned,
            email=email_str,
            phone=phone_str,
            company=create_company,
            auto_created=auto_created,
            created_by=provenance,
        )
        return EntityRef(self.type_name, self._get_cache_key(new_person)), True

    def _resolve_identifier(self, ident: Identifier) -> Optional[EntityRef]:
        """Resolve a single identifier to an EntityRef, or None.

        Email delegates to `get_by_email`, which since WI-023 IS the unified
        index's email reader — that delegation is what makes "one authority"
        structural rather than behavioural. Phone delegates to `get_by_phone`
        and stays on the fuzzy path PERMANENTLY: `phones_match` is not
        transitive, so no key function for it exists and none can be written. A
        phone-bearing JID pivots to `get_by_phone` (WI-035); richer kinds
        resolve through the unified index.
        """
        person = None
        if isinstance(ident, Email):
            person = self.get_by_email(ident.value)
        elif isinstance(ident, Phone):
            person = self.get_by_phone(ident.value)
        elif isinstance(ident, WhatsAppJID):
            if ident.phone_digits:
                person = self.get_by_phone(ident.phone_digits)
            else:
                return self._identifier_index.get(ident.key)
        else:
            return self._identifier_index.get(ident.key)
        return EntityRef(self.type_name, self._get_cache_key(person)) if person else None

    def _record_resolution_conflict(
        self, hits: List[Tuple[Identifier, EntityRef]]
    ) -> None:
        """Record a Branch-A conflict (identifiers in one call pointing at
        different people). Never raises, never merges — observability only."""
        distinct = sorted(
            {r for _, r in hits}, key=lambda r: (r.entity_type, r.canonical_key)
        )
        key = "resolve:" + "|".join(sorted(i.key for i, _ in hits))
        self._resolution_conflicts.append(
            IdentifierConflict(identifier_key=key, entities=tuple(distinct))
        )
        logger.warning(
            "identity resolution conflict: %d identifiers resolve to multiple "
            "persons %s — returning best-hit %s (no merge, no raise)",
            len(hits),
            [r.canonical_key for r in distinct],
            hits[0][1].canonical_key,
        )

    def _hydrate(self, ref: Optional[EntityRef]) -> Optional[Person]:
        """Turn an EntityRef back into the live Person (the Phase-4 adapter's
        last step). None-safe."""
        if ref is None:
            return None
        return self._cache.get(ref.canonical_key)

    # ──────────────────────────────────────────────────────────────────
    # WI-117 name-cleaning helpers (corroborated company-suffix strip)
    # ──────────────────────────────────────────────────────────────────

    def _clean_query_for_lookup(
        self,
        name: str,
        email: Optional[str] = None,
        company: Optional[str] = None,
    ) -> Tuple[str, Optional[str]]:
        """Clean a query name for find_or_create_stub (WI-117 + WI-121).

        Returns (cleaned_name, derived_company). `derived_company` is the inner
        text of a TRAILING parenthetical (e.g. 'Pendo' from 'Louron Pratt
        (Pendo)'), or None. It is a RAW hint — NOT filtered against known-
        companies; the caller merges it (caller-wins) for the resolve hint and
        the creation site filters it via _company_if_known.

        Stages:
          0. WI-121 — strip a trailing '(X)' FIRST (so the token-based rules
             below see paren-free ground), surfacing X as derived_company. A
             trailing parenthetical is never part of a legal name → safe to
             strip for lookup AND as the created name.
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
            return name, None
        stripped, derived_company = _split_trailing_paren(name)
        cleaned = clean_person_name(stripped)
        cleaned = self._strip_corroborated_company_suffix(
            cleaned, company=company, email=email
        )
        return cleaned, derived_company

    def _company_if_known(self, company: Optional[str]) -> Optional[str]:
        """WI-121: return `company` iff it's a known company (case-insensitive),
        else None. Used at the CREATE site for the PAREN-DERIVED company only, so
        a role-annotation ('PA', "Dave's EA") is never persisted as a company.
        A caller-supplied company is NOT routed through this (it is the stronger
        signal and is stored as-is, preserving pre-WI-121 behaviour). Empty → None."""
        if not company:
            return None
        known_lower = {c.lower() for c in self._known_companies()}
        return company if company.lower() in known_lower else None

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
        except ImportError:
            # AC-6 (WI-020, rerouted from WI-024): narrowed AT THE CLAUSE, not
            # merely logged louder. The clause exists for ONE expected-unavailable
            # case — the `from .company import CompanyRepository` above. A bare
            # `except Exception` also buried a VaultPathNotConfiguredError raised
            # by CompanyRepository's own construction, which is a misconfiguration
            # the caller must be told about, not a degradable optional feature.
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
        updates: dict = {}
        if email and email not in (person.emails or []):
            person.emails = list(person.emails or []) + [email]
            updates["emails"] = person.emails
        if phone and phone not in (person.phones or []):
            person.phones = list(person.phones or []) + [phone]
            updates["phones"] = person.phones
        if updates:
            # WI-126: route through update_fields (body-preserving), NOT save().
            # save() rebuilds the file with the default empty body and so silently
            # TRUNCATED the note body (the meeting Timeline) on every reuse — a
            # signature-less data-loss door (door A). update_fields reads the file,
            # rewrites only the named frontmatter fields, and preserves the body.
            self.update_fields(person, updates)
            logger.info(
                "find_or_create_stub: wrote back new identifier(s) to '%s' (emails=%d, phones=%d)",
                person.name,
                len(person.emails or []),
                len(person.phones or []),
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

    def save(self, entity, body: str = "", extra_fields=None, overwrite: bool = True,
             allow_body_replacement: bool = False,
             allow_unverified_overwrite: bool = False):
        """Override BaseRepository.save() to write the gate's normalized
        identifier fields back onto the ENTITY (WI-021's rider; WI-109's
        `_normalize_address_fields` is SUBSUMED here and deleted).

        This is not an eighth arm and the wall does not sweep it — `save` binds
        no frontmatter dict and serializes nothing. It is a RIDER, and it is the
        reason this method carries a gate call at all: the gate returns a dict
        and never touches the model, so no other frame can preserve the IN-PLACE
        model mutation callers observe today (`person.emails` and
        `person.aliases` were rewritten by `_normalize_address_fields`).

        `whole_record=True`, because `model_to_frontmatter` projects every
        declared field: both cross-field migrations run here exactly as they ran
        before — an address found in an `aliases[]` entry moves to `emails[]`,
        and a display half found in an `emails[]` entry moves to `aliases[]`.

        The write-back is the IDENTIFIER fields ONLY and never `name`: under the
        name-identity rule the gate returns the name it was handed byte-for-byte,
        so there is nothing on that field to write back — and the filename is
        derived from the raw name one frame below, so writing a repaired name
        here is exactly the path/field divergence this item exists to prevent.

        `phones[]` is a NEW in-place mutation a caller holding a `Person` will
        observe where it does not today: nothing in this package deduped
        `phones[]` before, and that is the behaviour the identifier criterion
        wants. Stated because it is one field wider than the consumer audit's
        grep list was written against.

        The gate runs TWICE on one save — here, then at the entity arm on the
        projection of the entity this rider just normalized — which is why
        idempotence is required of it rather than incidental.
        """
        gated = gate_write(model_to_frontmatter(entity),
                           declared_type=self.type_name, whole_record=True)
        entity.emails = gated["emails"]
        entity.phones = gated["phones"]
        entity.aliases = gated["aliases"]
        # Delegates and adopts nothing of its own, so it calls _adopt nowhere —
        # a consequence of the door rather than a per-file exemption.
        return super().save(entity, body=body, extra_fields=extra_fields,
                            overwrite=overwrite,
                            allow_body_replacement=allow_body_replacement,
                            allow_unverified_overwrite=allow_unverified_overwrite)

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
        #
        # WI-021: the JOB survives verbatim; only the parser moves. This was a
        # second, laxer copy of the address split — it trusted parseaddr on a
        # BARE input, which silently repairs `a@b c.com` into `a@bc.com` and
        # mints a wrong identity key. `split_address` is the one implementation
        # and it delegates to `Email.parse`, so this site inherits that
        # deliberate refusal: an unparseable blob is no longer adopted as an
        # address, and falls through to the NameValidator boundary below.
        parsed_email, parsed_name = split_address(name)
        if parsed_email:
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

        # WI-126 door C: reuse-on-collision. If a note already exists for this
        # exact (case-insensitive) name, REUSE it — never overwrite a rich note
        # with the empty template, which resets `created`/`created_by` and wipes
        # the Timeline (the loud door WI-119 caught on 06-14). Existence-only, no
        # content predicate: any collision is an upstream resolution miss worth
        # surfacing, and reuse is strictly safer than overwrite (the vault keys
        # on @{name}.md, so a create would clobber the same file regardless). The
        # supplied email/phone merge non-destructively via the now body-preserving
        # _writeback_identifier (door A fix). A genuinely new name → get() is None
        # → normal create below (no existing body, so R1 is a no-op).
        existing = self.get(clean_name)
        if existing is not None:
            logger.warning(
                "create_stub: '%s' already exists — reusing instead of overwriting "
                "(upstream resolution miss; created_by=%r)",
                clean_name, created_by,
            )
            self._writeback_identifier(existing, email=email, phone=phone)
            return existing

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
        try:
            self.save(person, body=get_default_body("person"),
                      extra_fields=extra_fields)
        except NoteAlreadyExists:
            # WI-004 door 2c: we LOST a cross-process create race. The winner's
            # note is on disk; re-read that ONE path (never refresh(), whose
            # whole-vault zero-entity restore guard is the wrong instrument for
            # a single note), adopt it, and take the reuse branch above — so the
            # cross-process race produces the same outcome the in-process
            # collision already produces.
            logger.warning(
                "create_stub: lost a create race for '%s' — reusing the winner's "
                "note (created_by=%r)", clean_name, created_by,
            )
            file_path = self.vault_path / f"@{clean_name}.md"
            winner = self._load_file(file_path)
            if winner is None:
                # A note that exists and does not load is not a reuse
                # candidate; WI-020's skip surface is where it belongs.
                raise
            # Through the ADOPTION DOOR, not a bare `self._cache[key] = winner`:
            # the reuse branch's _writeback_identifier routes through
            # update_fields, which resolves the path via get_file_path ->
            # self._file_map. A recovery populating _cache alone leaves
            # _file_map empty for that key, and update_fields raises ValueError
            # before the phone is ever written back.
            self._adopt(self._get_cache_key(winner), winner, file_path)
            self._writeback_identifier(winner, email=email, phone=phone)
            return winner

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
        preserving existing content. If the note has no ## Timeline section at
        all, one is CREATED at end of file and the entry inserted (WI-020 AC-5
        Predicate 3) — a raw-content check cannot tell "corrupted since
        creation" from "hand-created in Obsidian and never had one", so the
        entry lands rather than being dropped. Every pre-existing byte is
        preserved and the frontmatter stays byte-identical.

        Args:
            person: The person whose timeline to update
            entry: The full entry to append (e.g., "### Dec 3, 2025\\n[[Meeting]]...")
            deduplicate_key: Optional string to check for duplicates.
                            If provided and found in existing content, skip the update.

        Returns:
            True if the entry was added (including when the section was
            created). False ONLY for the deliberate whole-file dedup no-op —
            a failure no longer reports itself as this same False (WI-020 N4).

        Raises:
            ValueError: If person not found in repository
            WriteFailedError: If the write did not complete
        """
        file_path = self.get_file_path(person.name)
        if not file_path or not file_path.exists():
            raise ValueError(f"Person file not found: {person.name}")

        try:
            # Door 1 (WI-004): one lock spans the read, the transform and
            # every write below; each write carries the stamp of that read.
            with vault_io.note_lock(file_path):
                content, _stamp = vault_io.read_note(file_path)

                # Check for duplicate if key provided
                if deduplicate_key and deduplicate_key in content:
                    logger.debug(f"Timeline entry already exists for {person.name}: {deduplicate_key}")
                    return False

                # Find the Timeline section
                timeline_marker = "## Timeline"

                # Ensure entry starts with newline for clean formatting
                formatted_entry = entry if entry.startswith("\n") else f"\n{entry}"

                # WI-020 AC-5 Predicate 3 — ACCOMMODATE, with PRESERVATION.
                #
                # A missing "## Timeline" used to drop the caller's entry into the
                # same silent False the dedup no-op returns. A raw-content check
                # cannot tell "corrupted since creation by this package" from
                # "legitimately never had one" (hand-created in Obsidian, or
                # predating the template), so refusing would manufacture a failure
                # out of a structural variant. The section is created instead,
                # mirroring append_to_body_section's create_if_missing default.
                #
                # The mechanism is STRING INSERTION at end of file, NOT the
                # sibling's parse_body_sections/write_body_sections round-trip:
                # that round-trip keeps only `^## `-delimited spans, so it deletes
                # any preamble above the first heading and destroys a heading-less
                # body outright — on a raw write_text that writer.py deliberately
                # exempts from the WI-126 shrink guard. The note least likely to
                # have `##` headings is exactly the hand-created note this
                # accommodation exists for. End-of-file placement is the only
                # placement that preserves content without parsing structure, and
                # it makes the oracle fall out: new_content.startswith(content).
                if timeline_marker not in content:
                    suffix = "" if content.endswith("\n") else "\n"
                    new_content = content + suffix + "\n" + timeline_marker + formatted_entry
                    vault_io.write_note(file_path, new_content, precondition=_stamp)
                    logger.info(f"Created Timeline section for {person.name}")
                    return True

                # Insert after "## Timeline" marker. No split guard: str.split(sep, 1)
                # on a string containing sep returns exactly two parts, and the marker
                # was confirmed present above — the old `len(parts) != 2` branch was
                # structurally unreachable.
                parts = content.split(timeline_marker, 1)

                new_content = parts[0] + timeline_marker + formatted_entry + parts[1]
                vault_io.write_note(file_path, new_content, precondition=_stamp)

                logger.info(f"Updated timeline for {person.name}")
                return True

        except LoudFailError:
            raise                   # our own signal — never re-wrapped, never swallowed
        except Exception as e:
            logger.warning(bounded_message("failed to update timeline",
                                           path=file_path, cause=e))
            raise WriteFailedError("write did not complete",
                                   path=file_path, cause=e) from chainable_cause(e)

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
            True if written; False if deduped or skipped (missing section with
            ``create_if_missing=False``). A malformed or absent frontmatter
            fence no longer lands here — it RAISES (WI-020 AC-5 Predicate 2),
            so a False now means only "nothing to do".

        Raises:
            ValueError: if the person file does not exist, or ``operation`` is
                not "append"/"prepend" (loud-fail — never silently mis-write).
            FrontmatterParseError: if the note has no frontmatter fence, or an
                unclosed one — the caller's content is never silently dropped.
            WriteFailedError: if the write did not complete.
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
            # Door 1 (WI-004): one lock spans the read, the transform and
            # every write below; each write carries the stamp of that read.
            with vault_io.note_lock(file_path):
                content_raw, _stamp = vault_io.read_note(file_path)

                # Split frontmatter and body (body-safe pattern, mirrors To-Discuss).
                frontmatter, body_raw = _split_frontmatter_fence(content_raw, file_path)
                body = body_raw.lstrip("\n")

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
                vault_io.write_note(file_path, new_content, precondition=_stamp)
                logger.info(
                    f"append_to_body_section: {operation} to '{section}' for {person.name}"
                )
                return True

        except LoudFailError:
            raise                   # our own signal — never re-wrapped, never swallowed
        except Exception as e:
            logger.warning(bounded_message("failed to append to body section",
                                           path=file_path, cause=e))
            raise WriteFailedError("write did not complete",
                                   path=file_path, cause=e) from chainable_cause(e)

    # =========================================================================
    # To Discuss Methods
    # =========================================================================

    def _get_body_content(self, person: Person) -> Optional[str]:
        """Get the body content of a person's markdown file.

        Returns None when the note does not exist — its only caller converts
        that to a ValueError (no-op class (d)).

        Raises:
            FrontmatterParseError: If the note OPENED a frontmatter fence and
                never closed it. Before WI-020 this returned the whole file,
                frontmatter included, AS the body — which is how
                get_to_discuss_items reported a corrupted note as "no items".
                A legitimately fence-less note still returns its whole content.
        """
        file_path = self.get_file_path(person.name)
        if not file_path or not file_path.exists():
            return None

        content = file_path.read_text(encoding="utf-8")

        # Split frontmatter and body.
        #
        # The outer guard is deliberately redundant with the helper's first
        # branch and must NOT be "simplified" away: it is what routes the
        # legitimately fence-less note to `return content` instead of to the
        # helper's `FrontmatterParseError`. Dropping it turns a no-op into a
        # raise and breaks AC-5's no-op half.
        if content.startswith("---"):
            _, body_raw = _split_frontmatter_fence(content, file_path)
            return body_raw.strip()
        return content          # legitimately fence-less: the whole file IS the body

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
            True if the item was added. A malformed or absent frontmatter
            fence now RAISES rather than returning False (WI-020).

        Raises:
            ValueError: If person not found in repository
            FrontmatterParseError: If the note has no frontmatter fence, or an
                unclosed one (WI-020 AC-5 Predicate 2) — the caller's item is
                never silently dropped into the same False a legitimate
                "not found" returns.
            WriteFailedError: If the write did not complete.
        """
        file_path = self.get_file_path(person.name)
        if not file_path or not file_path.exists():
            raise ValueError(f"Person file not found: {person.name}")

        try:
            # Door 1 (WI-004): one lock spans the read, the transform and
            # every write below; each write carries the stamp of that read.
            with vault_io.note_lock(file_path):
                content, _stamp = vault_io.read_note(file_path)

                # Split frontmatter and body
                frontmatter, body_raw = _split_frontmatter_fence(content, file_path)
                body = body_raw.lstrip("\n")

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
                vault_io.write_note(file_path, new_content, precondition=_stamp)

                logger.info(f"Added To Discuss item for {person.name}: {text[:50]}")
                return True

        except LoudFailError:
            raise                   # our own signal — never re-wrapped, never swallowed
        except Exception as e:
            logger.warning(bounded_message("failed to add To Discuss item",
                                           path=file_path, cause=e))
            raise WriteFailedError("write did not complete",
                                   path=file_path, cause=e) from chainable_cause(e)

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
            True if the item was updated; False if the section or the item
            text was not found. "Not found" is the ONLY remaining False —
            a malformed fence now RAISES (WI-020).

        Raises:
            ValueError: If person not found in repository
            FrontmatterParseError: If the note has no frontmatter fence, or an
                unclosed one (WI-020 AC-5 Predicate 2) — the caller's item is
                never silently dropped into the same False a legitimate
                "not found" returns.
            WriteFailedError: If the write did not complete.
        """
        file_path = self.get_file_path(person.name)
        if not file_path or not file_path.exists():
            raise ValueError(f"Person file not found: {person.name}")

        try:
            # Door 1 (WI-004): one lock spans the read, the transform and
            # every write below; each write carries the stamp of that read.
            with vault_io.note_lock(file_path):
                content, _stamp = vault_io.read_note(file_path)

                # Split frontmatter and body
                frontmatter, body_raw = _split_frontmatter_fence(content, file_path)
                body = body_raw.lstrip("\n")

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
                vault_io.write_note(file_path, new_content, precondition=_stamp)

                status = "completed" if completed else "uncompleted"
                logger.info(f"Marked To Discuss item as {status} for {person.name}: {text[:50]}")
                return True

        except LoudFailError:
            raise                   # our own signal — never re-wrapped, never swallowed
        except Exception as e:
            logger.warning(bounded_message("failed to update To Discuss item",
                                           path=file_path, cause=e))
            raise WriteFailedError("write did not complete",
                                   path=file_path, cause=e) from chainable_cause(e)

    def remove_to_discuss_item(self, person: Person, text: str) -> bool:
        """
        Remove a To Discuss item.

        Args:
            person: The person to remove item from
            text: The item text to match (exact match)

        Returns:
            True if the item was removed; False if the section or the item
            text was not found. "Not found" is the ONLY remaining False —
            a malformed fence now RAISES (WI-020).

        Raises:
            ValueError: If person not found in repository
            FrontmatterParseError: If the note has no frontmatter fence, or an
                unclosed one (WI-020 AC-5 Predicate 2) — the caller's item is
                never silently dropped into the same False a legitimate
                "not found" returns.
            WriteFailedError: If the write did not complete.
        """
        file_path = self.get_file_path(person.name)
        if not file_path or not file_path.exists():
            raise ValueError(f"Person file not found: {person.name}")

        try:
            # Door 1 (WI-004): one lock spans the read, the transform and
            # every write below; each write carries the stamp of that read.
            with vault_io.note_lock(file_path):
                content, _stamp = vault_io.read_note(file_path)

                # Split frontmatter and body
                frontmatter, body_raw = _split_frontmatter_fence(content, file_path)
                body = body_raw.lstrip("\n")

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
                vault_io.write_note(file_path, new_content, precondition=_stamp)

                logger.info(f"Removed To Discuss item for {person.name}: {text[:50]}")
                return True

        except LoudFailError:
            raise                   # our own signal — never re-wrapped, never swallowed
        except Exception as e:
            logger.warning(bounded_message("failed to remove To Discuss item",
                                           path=file_path, cause=e))
            raise WriteFailedError("write did not complete",
                                   path=file_path, cause=e) from chainable_cause(e)
