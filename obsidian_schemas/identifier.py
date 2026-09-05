"""Typed identifier union — the match key of the identity core (WI-125, Phase 1).

The keystone shift behind the Identity Model (`orchestrator/docs/identity-model-
revised-2026-06-13.md` §3): identity does NOT live *on* the entity as stringly-
typed fields (`emails: list[str]`). It lives in an index keyed by `Identifier`s —
first-class, validated, normalized value objects. Resolution becomes a dict
lookup on a clean key, never a fuzzy name match.

This module is the **pure** layer (Phase 1): the typed kinds + their parse/
normalize/validate logic + the namespaced `.key` used by the Phase-2 index.
No vault I/O, no PersonRepository, no resolution — those are Phases 2–3.

Parse, don't validate (`LESSONS` #1 — type the boundaries): each kind is built
through `.parse(raw)`, which normalizes and *raises* `IdentifierError` on
malformed input. A constructed `Identifier` is, by construction, well-formed —
downstream code never re-checks.

Design notes:
- `Email` resolves a **Person** (the full address is a person key). Its `.domain`
  property derives the `EmailDomain` that resolves a **Company** — "one parse
  resolves both" (model §2), without overloading `Email.resolves`.
- `EmailDomain` carries `.is_public_provider` (a gmail/outlook/… denylist) so a
  personal address never mints a company (WI-124's gotcha, designed in now).
- `WhatsAppJID`'s `@lid`→phone pivot (WI-035) is a *resolution-time* concern
  (it needs the vault); here a phone-bearing JID just exposes `.phone`.
- Subdomain normalization beyond a leading `www.` (e.g. `mail.acme.com`→`acme.com`)
  needs a public-suffix list to avoid butchering `co.uk` — deferred; Phase 1
  lowercases + strips `www.` only.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from email.utils import parseaddr
from typing import ClassVar, FrozenSet, Optional, Tuple

# WI-021: MODULE-SCOPE, replacing the two deferred imports `Phone.parse` and
# `WhatsAppJID.parse` carried. `phone_normalization` is a stdlib-only leaf that
# imports nothing from the package, so naming it here cannot close a cycle — it
# was `repositories.person` (which reaches `base` -> `writer`) that forced the
# lazy form. This module names one package sibling and nothing above it, so it
# is still a LEAF; it is no longer *stdlib-only*, and the docstring's "pure
# layer" claim is about vault I/O and resolution, which is untouched.
from .phone_normalization import normalize_phone


# ── Public email providers (the WI-124 denylist) ─────────────────────────────
# A personal-email domain is never an employer. An EmailDomain on this set is
# flagged so the resolver (Company, later) refuses to mint a company from it —
# almost certainly how some of the 1,466 quarantined company shells were born
# (a @gmail.com minting a "Gmail" company). Extend freely; over-inclusion is
# safe (worst case: a real company on a public domain isn't auto-derived).
PUBLIC_EMAIL_PROVIDERS: FrozenSet[str] = frozenset({
    "gmail.com", "googlemail.com",
    "outlook.com", "hotmail.com", "hotmail.co.uk", "live.com", "msn.com",
    "icloud.com", "me.com", "mac.com",
    "yahoo.com", "yahoo.co.uk", "ymail.com",
    "aol.com",
    "proton.me", "protonmail.com", "pm.me",
    "gmx.com", "gmx.net", "fastmail.com", "fastmail.fm",
    "hey.com", "zoho.com", "mail.com", "tutanota.com", "tuta.io",
    "yandex.com", "qq.com", "163.com", "126.com",
})


class IdentifierError(ValueError):
    """Raised when an Identifier constructor receives malformed input.

    Parse-don't-validate: this fires at the parse boundary, so a constructed
    Identifier is guaranteed well-formed. Mirrors NameValidationError's
    carry-the-strings pattern (`name_validation.py`): `.kind`/`.raw`/`.detail`
    let callers route and log without re-parsing the message.
    """

    def __init__(self, kind: str, raw, detail: str):
        super().__init__(f"{kind}: {detail}")
        self.kind = kind
        self.raw = raw
        self.detail = detail


@dataclass(frozen=True)
class EntityRef:
    """A reference to a resolved entity — the *value* of the Phase-2 unified
    index (model §2: `Identifier → EntityRef`). `entity_type` matches a
    repository's `type_name` ("person"/"company"/"meeting"); `canonical_key` is
    that repo's cache key (the lowercase note name today). Pure value object —
    hashable, comparable by value, no I/O. Hydrating it back into a live entity
    is the repo's job (Phase 3 `_hydrate`)."""

    entity_type: str
    canonical_key: str


@dataclass(frozen=True)
class IdentifierConflict:
    """A reconciliation finding: one identifier key maps to >1 entity (model §2
    "every identifier maps to exactly one entity"). A violation is a real-data
    collision — almost always a duplicate note pair sharing an email/LinkedIn/
    phone (the WI-119 invariant generalized from "no dup notes" to "no ambiguous
    identifier"). The library *exposes* these (`repo.conflicts`); the orchestrator
    *persists* them to `state/identity-conflicts.json` and alarms (the WI-095
    state-file-not-log-grep split). `entities` names every candidate the key was
    seen on, so a 3-way dup is one record, not two."""

    identifier_key: str
    entities: Tuple[EntityRef, ...]  # the >1 entities this key maps to


@dataclass(frozen=True)
class Identifier:
    """Base of the tagged union. Not instantiated directly — use a kind's
    `.parse(raw)`. Subclasses declare `kind` + `resolves` (ClassVars) and a
    `.key` (the namespaced string the index is keyed on, e.g. `email:a@b.com`).
    """

    kind: ClassVar[str] = "identifier"
    # Which entity type(s) this identifier can resolve. Plain strings matching
    # the repositories' `type_name` ("person" / "company" / "meeting").
    resolves: ClassVar[FrozenSet[str]] = frozenset()

    @property
    def key(self) -> str:  # pragma: no cover - overridden by every subclass
        raise NotImplementedError

    @property
    def value(self) -> str:  # pragma: no cover - overridden by every subclass
        raise NotImplementedError


@dataclass(frozen=True)
class Email(Identifier):
    """An email address. Resolves a Person (full address); `.domain` derives the
    EmailDomain that resolves a Company."""

    kind: ClassVar[str] = "email"
    resolves: ClassVar[FrozenSet[str]] = frozenset({"person"})

    local: str
    domain: str  # normalized, lowercased

    @classmethod
    def parse(cls, raw: str) -> "Email":
        if raw is None:
            raise IdentifierError("email", raw, "is None")
        raw_s = str(raw)
        # Accept "Name <a@b.com>" forms (the WI-017 create_stub bug) — extract
        # the address, never the display name. But ONLY route through parseaddr
        # for genuine angle-bracket forms: parseaddr silently *repairs* a bare
        # "a@b c.com" into "a@bc.com" (strips the internal space), which would
        # mint a wrong identity key. We loud-fail on that instead (a producer
        # emitting whitespace-in-address has a bug we want to see).
        if "<" in raw_s and ">" in raw_s:
            _, addr = parseaddr(raw_s)
            candidate = addr or raw_s
        else:
            candidate = raw_s
        s = candidate.strip().lower()
        if not s:
            raise IdentifierError("email", raw, "empty")
        if any(c.isspace() for c in s):
            raise IdentifierError("email", raw, "contains whitespace")
        if s.count("@") != 1:
            raise IdentifierError("email", raw, "must contain exactly one '@'")
        local, _, domain = s.partition("@")
        if not local or not domain or "." not in domain:
            raise IdentifierError("email", raw, "malformed local@domain")
        return cls(local=local, domain=domain)

    @property
    def value(self) -> str:
        return f"{self.local}@{self.domain}"

    @property
    def key(self) -> str:
        return f"email:{self.value}"

    @property
    def domain_id(self) -> "EmailDomain":
        """The company-resolving half of this address (model §2)."""
        return EmailDomain.parse(self.domain)


@dataclass(frozen=True)
class EmailDomain(Identifier):
    """A bare domain. Resolves a Company. Carries the public-provider flag."""

    kind: ClassVar[str] = "email_domain"
    resolves: ClassVar[FrozenSet[str]] = frozenset({"company"})

    domain: str  # normalized, lowercased, no leading www.

    @classmethod
    def parse(cls, raw: str) -> "EmailDomain":
        if raw is None:
            raise IdentifierError("email_domain", raw, "is None")
        s = str(raw).strip().lower()
        if not s:
            raise IdentifierError("email_domain", raw, "empty")
        # Tolerate a full address or URL — extract the host.
        if "@" in s:
            s = s.rsplit("@", 1)[-1]
        s = re.sub(r"^[a-z]+://", "", s)  # strip scheme
        s = s.split("/")[0]              # strip path
        if s.startswith("www."):
            s = s[4:]
        s = s.rstrip(".")
        if "." not in s or any(c.isspace() for c in s) or "@" in s:
            raise IdentifierError("email_domain", raw, "not a bare domain")
        return cls(domain=s)

    @property
    def is_public_provider(self) -> bool:
        return self.domain in PUBLIC_EMAIL_PROVIDERS

    @property
    def value(self) -> str:
        return self.domain

    @property
    def key(self) -> str:
        return f"domain:{self.domain}"


@dataclass(frozen=True)
class Phone(Identifier):
    """A phone number, normalized to digits (reuses the repo's normalize_phone)."""

    kind: ClassVar[str] = "phone"
    resolves: ClassVar[FrozenSet[str]] = frozenset({"person"})

    digits: str  # digits only, e.g. "447990558521"

    # Minimum plausible length — guards against junk like a 3-digit extension
    # being treated as a globally-unique person key.
    MIN_DIGITS: ClassVar[int] = 7

    @classmethod
    def parse(cls, raw: str) -> "Phone":
        if raw is None:
            raise IdentifierError("phone", raw, "is None")
        digits = normalize_phone(str(raw))
        if len(digits) < cls.MIN_DIGITS:
            raise IdentifierError("phone", raw, f"fewer than {cls.MIN_DIGITS} digits")
        return cls(digits=digits)

    @property
    def value(self) -> str:
        return self.digits

    @property
    def key(self) -> str:
        return f"phone:{self.digits}"


@dataclass(frozen=True)
class WhatsAppJID(Identifier):
    """A WhatsApp JID. A phone-bearing JID exposes `.phone`; an `@lid`
    (anonymized) JID has none — its phone is recovered at resolution time via
    the vault pivot (WI-035), which is out of this pure layer."""

    kind: ClassVar[str] = "whatsapp_jid"
    resolves: ClassVar[FrozenSet[str]] = frozenset({"person"})

    jid: str          # normalized raw JID, lowercased
    phone_digits: str  # "" for @lid JIDs

    @classmethod
    def parse(cls, raw: str) -> "WhatsAppJID":
        if raw is None:
            raise IdentifierError("whatsapp_jid", raw, "is None")
        s = str(raw).strip().lower()
        if not s:
            raise IdentifierError("whatsapp_jid", raw, "empty")
        if "@lid" in s:
            return cls(jid=s, phone_digits="")
        digits = normalize_phone(s)
        if len(digits) < Phone.MIN_DIGITS:
            raise IdentifierError("whatsapp_jid", raw, "no @lid and no usable phone")
        return cls(jid=s, phone_digits=digits)

    @property
    def phone(self) -> Optional[Phone]:
        """The phone identifier this JID pivots to, if any (WI-035 seed)."""
        return Phone.parse(self.phone_digits) if self.phone_digits else None

    @property
    def value(self) -> str:
        return self.phone_digits or self.jid

    @property
    def key(self) -> str:
        # A phone-bearing JID keys on the SAME `phone:` key a bare Phone uses, so
        # a WhatsApp number and the same phone number unify to one index entry
        # (they're the same person — the system already treats them together via
        # normalize_phone/phones_match). @lid JIDs (no phone) key on the lid.
        return f"phone:{self.phone_digits}" if self.phone_digits else f"jid:{self.jid}"


@dataclass(frozen=True)
class SlackUserId(Identifier):
    """A Slack user id, scoped to a workspace (the same id means different people
    in different workspaces). Slack ids are case-sensitive — not lowercased."""

    kind: ClassVar[str] = "slack"
    resolves: ClassVar[FrozenSet[str]] = frozenset({"person"})

    workspace: str
    user_id: str

    @classmethod
    def parse(cls, raw: Optional[str] = None, *, workspace: Optional[str] = None,
              user_id: Optional[str] = None) -> "SlackUserId":
        # Accept either kwargs or a "workspace/userid" string.
        if raw is not None:
            parts = str(raw).strip().split("/", 1)
            if len(parts) != 2:
                raise IdentifierError("slack", raw, "expected 'workspace/user_id'")
            workspace, user_id = parts
        ws = (workspace or "").strip()
        uid = (user_id or "").strip()
        if not ws or not uid:
            raise IdentifierError("slack", raw or (workspace, user_id),
                                  "workspace and user_id both required")
        return cls(workspace=ws, user_id=uid)

    @property
    def value(self) -> str:
        return f"{self.workspace}/{self.user_id}"

    @property
    def key(self) -> str:
        return f"slack:{self.value}"


@dataclass(frozen=True)
class LinkedInSlug(Identifier):
    """A LinkedIn slug. `/in/<slug>` is a person, `/company/<slug>` is a company;
    a bare slug is assumed a person (the common case). The continuity anchor of
    model §6 — used for reconnection (Branch B), never an entry key."""

    kind: ClassVar[str] = "linkedin"
    resolves: ClassVar[FrozenSet[str]] = frozenset({"person", "company"})

    slug: str
    entity_hint: str  # "person" | "company" | "unknown"

    @classmethod
    def parse(cls, raw: str) -> "LinkedInSlug":
        if raw is None:
            raise IdentifierError("linkedin", raw, "is None")
        s = str(raw).strip().lower().rstrip("/")
        if not s:
            raise IdentifierError("linkedin", raw, "empty")
        if "/company/" in s:
            hint, slug = "company", s.split("/company/", 1)[1].split("/")[0]
        elif "/in/" in s:
            hint, slug = "person", s.split("/in/", 1)[1].split("/")[0]
        elif "linkedin.com" in s or "/" in s:
            # a linkedin URL without /in/ or /company/, or some other path form
            raise IdentifierError("linkedin", raw, "unrecognized LinkedIn URL shape")
        else:
            hint, slug = "person", s  # bare slug
        if not slug or any(c.isspace() for c in slug):
            raise IdentifierError("linkedin", raw, "empty or malformed slug")
        return cls(slug=slug, entity_hint=hint)

    @property
    def value(self) -> str:
        return self.slug

    @property
    def key(self) -> str:
        # Namespaced by hint so a person-slug and a company-slug of the same
        # string don't collide in the index.
        if self.entity_hint == "person":
            return f"linkedin:in/{self.slug}"
        if self.entity_hint == "company":
            return f"linkedin:company/{self.slug}"
        return f"linkedin:{self.slug}"


@dataclass(frozen=True)
class CalendarEventId(Identifier):
    """A calendar event id. Resolves a Meeting (not activated this cut)."""

    kind: ClassVar[str] = "calendar_event"
    resolves: ClassVar[FrozenSet[str]] = frozenset({"meeting"})

    event_id: str

    @classmethod
    def parse(cls, raw: str) -> "CalendarEventId":
        s = "" if raw is None else str(raw).strip()
        if not s:
            raise IdentifierError("calendar_event", raw, "empty")
        return cls(event_id=s)

    @property
    def value(self) -> str:
        return self.event_id

    @property
    def key(self) -> str:
        return f"calendar_event:{self.event_id}"


@dataclass(frozen=True)
class GranolaDocId(Identifier):
    """A Granola transcript doc id. Resolves a Meeting (not activated this cut)."""

    kind: ClassVar[str] = "granola_doc"
    resolves: ClassVar[FrozenSet[str]] = frozenset({"meeting"})

    doc_id: str

    @classmethod
    def parse(cls, raw: str) -> "GranolaDocId":
        s = "" if raw is None else str(raw).strip()
        if not s:
            raise IdentifierError("granola_doc", raw, "empty")
        return cls(doc_id=s)

    @property
    def value(self) -> str:
        return self.doc_id

    @property
    def key(self) -> str:
        return f"granola_doc:{self.doc_id}"


def parse_identifiers(
    *,
    email: Optional[str] = None,
    phone: Optional[str] = None,
    jid: Optional[str] = None,
    slack: Optional[str] = None,
    linkedin: Optional[str] = None,
    calendar_event: Optional[str] = None,
    granola_doc: Optional[str] = None,
    strict: bool = True,
) -> set:
    """Boundary parse: turn the loose kwargs a caller has into a `set[Identifier]`.

    This is the seed of the Phase-4 adapter (`find_or_create_stub` will call it).
    Note `company` is NOT a parameter — a company *name* is a display hint, not
    an identifier; the company-resolving `EmailDomain` is *derived* from `email`
    here ("one parse resolves both", model §2), never minted from a name.

    `strict=True` raises `IdentifierError` on any malformed input (parse-don't-
    validate). `strict=False` skips malformed inputs — for lenient callers that
    must not fail on junk (the adapter chooses its policy in Phase 4).
    """
    out: set = set()

    def add(parser, raw):
        if raw is None or (isinstance(raw, str) and not raw.strip()):
            return
        try:
            out.add(parser(raw))
        except IdentifierError:
            if strict:
                raise

    add(Email.parse, email)
    # Derive the company domain from the email — the keystone of model §2.
    if email:
        try:
            out.add(Email.parse(email).domain_id)
        except IdentifierError:
            if strict:
                raise
    add(Phone.parse, phone)
    add(WhatsAppJID.parse, jid)
    add(SlackUserId.parse, slack)
    add(LinkedInSlug.parse, linkedin)
    add(CalendarEventId.parse, calendar_event)
    add(GranolaDocId.parse, granola_doc)
    return out


# The closed set of concrete kinds — handy for tests and for the Phase-2 index
# builder to iterate when projecting frontmatter into identifiers.
ALL_IDENTIFIER_KINDS = (
    Email, EmailDomain, Phone, WhatsAppJID, SlackUserId,
    LinkedInSlug, CalendarEventId, GranolaDocId,
)
