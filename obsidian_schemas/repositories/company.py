"""
Company repository for organization management.

Provides lookup of Company entities by name or website domain.
"""

import logging
from pathlib import Path
from typing import Optional, Type
from urllib.parse import urlparse
from datetime import datetime

from ..models import Company
from ..name_validation import tier2_repair
from .base import BaseRepository

logger = logging.getLogger(__name__)


def extract_domain(url: str) -> str:
    """
    Extract domain from a URL.

    Examples:
        "https://www.acme.com/about" → "acme.com"
        "acme.com" → "acme.com"
    """
    if not url:
        return ""

    # Add scheme if missing for urlparse
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    try:
        parsed = urlparse(url)
        domain = parsed.netloc or parsed.path.split("/")[0]
        # Remove www. prefix
        if domain.startswith("www."):
            domain = domain[4:]
        return domain.lower()
    except Exception:
        return ""


class CompanyRepository(BaseRepository[Company]):
    """
    Repository for Company entities.

    Provides lookup by name or website domain.

    Usage:
        repo = CompanyRepository("/path/to/vault")
        company = repo.get("Acme Corp")
        company = repo.get_by_domain("acme.com")
    """

    def __init__(self, vault_path: Optional[str | Path] = None, **kwargs):
        super().__init__(vault_path, **kwargs)
        self._domain_index: dict[str, str] = {}  # domain -> cache_key

    @property
    def entity_type(self) -> Type[Company]:
        return Company

    @property
    def type_name(self) -> str:
        return "company"

    def _index_entity(self, entity: Company, cache_key: str) -> None:
        """Build domain index from website field."""
        if entity.website:
            domain = extract_domain(entity.website)
            if domain:
                self._domain_index[domain] = cache_key

    def _clear_indexes(self) -> None:
        """Clear custom indexes on refresh."""
        self._domain_index.clear()

    def get_by_domain(self, domain: str) -> Optional[Company]:
        """
        Get a company by website domain.

        Args:
            domain: Domain to look up (e.g., "acme.com")

        Returns:
            Company if found, None otherwise
        """
        self._ensure_loaded()
        domain = extract_domain(domain) or domain.lower().strip()
        cache_key = self._domain_index.get(domain)
        return self._cache.get(cache_key) if cache_key else None

    def resolve(self, query: str) -> Optional[Company]:
        """
        Resolve a query to a Company.

        Tries:
        1. Exact name match
        2. Domain match (if query looks like URL/domain)
        3. Partial name match

        Args:
            query: Company name or domain

        Returns:
            Company if found, None otherwise
        """
        self._ensure_loaded()

        if not query:
            return None

        query = query.strip()
        query_lower = query.lower()

        # 1. Exact name match
        if query_lower in self._cache:
            return self._cache[query_lower]

        # 2. Domain match
        if "." in query:
            company = self.get_by_domain(query)
            if company:
                return company

        # 3. Partial name match
        for name, company in self._cache.items():
            if query_lower in name:
                return company

        return None

    def get_by_industry(self, industry: str) -> list[Company]:
        """
        Get all companies in an industry.

        Args:
            industry: Industry name (case-insensitive)

        Returns:
            List of companies in that industry
        """
        self._ensure_loaded()
        industry_lower = industry.lower()
        return [
            c for c in self._cache.values()
            if c.industry and c.industry.lower() == industry_lower
        ]

    def create_stub(
        self,
        name: str,
        website: Optional[str] = None,
        auto_created: bool = True,
        created_by: Optional[str] = None,
    ) -> Company:
        """
        Create a minimal stub Company and save to vault.

        Args:
            name: Company name. Tier-2 repaired HERE (strip + collapse, above
                the filename derivation) and judged by the semantic gate on the
                way to disk — a Tier-1 dirty name raises NameGateRefusal out of
                save(), it is never silently stripped.
            website: Optional website URL
            auto_created: Mark as auto-created for later review
            created_by: Provenance label. ALWAYS written; an absent, non-`str`
                or whitespace-only label is recorded as "unknown" with a WARNING.

        Returns:
            The created Company entity
        """
        # WI-022: the legacy `clean_name = re.sub(r'[^\w\s-]', '', name).strip()`
        # mangler is DELETED. It corrupted real company names into BOTH the
        # stored `name:` and the @{name}.md stem ("AT&T" -> "ATT",
        # "O'Reilly Media" -> "OReilly Media"), and it silently absorbed the
        # path- and wikilink-hostile characters that are now REFUSED at the gate
        # instead of stripped here. This is the WI-111 ruling (person.py:1337)
        # applied to the company side: Tier-2 repair here, Tier-1 verdict there.
        name_text = "" if name is None else str(name)
        repaired = tier2_repair(name_text)
        if repaired.repairs_applied:
            logger.info(
                "create_stub: name repairs applied %s — input=%r output=%r",
                repaired.repairs_applied, name_text, repaired.cleaned_name,
            )
        clean_name = repaired.cleaned_name
        if not clean_name:
            # KEPT deliberately (Design §4.1). Person keeps its analogous
            # fallback at person.py:1345-1347, which is why name_validation.py
            # can say `empty` "has never fired in production". Dropping it would
            # change create_stub("") from writing a note to raising, which is a
            # live behaviour change on HAL9000's POST /api/entities/company.
            clean_name = "Unknown Company"

        company = Company(
            name=clean_name,
            website=website or "",
            tags=["company"],
            created=datetime.now().strftime("%Y-%m-%d"),
        )

        body = """## People

## Timeline

## Documents

## Notes
"""

        # WI-022 provenance, mirroring WI-119's person guard (person.py:1384-1393)
        # with ONE deliberate widening: a whitespace-only label is ALSO unlabeled.
        # Person's two-part check does not catch it — `not "   "` is False (a
        # non-empty string is truthy) and `isinstance("   ", str)` is True — so
        # person.py stores three spaces verbatim, a label that looks like a value
        # and names nobody. The third disjunct is a TEST on the guard and never a
        # transform on the value: a non-empty label is stored byte-identically,
        # leading and trailing spaces included. `or` short-circuits left to
        # right, so `created_by=123` is caught by the isinstance conjunct and
        # never reaches `.strip()`.
        if (not created_by
                or not isinstance(created_by, str)
                or not created_by.strip()):
            logger.warning(
                "create_stub: no created_by provenance for %r — recording 'unknown'",
                clean_name,
            )
            created_by = "unknown"

        extra_fields: dict = {"created_by": created_by}
        if auto_created:
            extra_fields["auto_created"] = True

        self.save(company, body=body, extra_fields=extra_fields)

        return company
