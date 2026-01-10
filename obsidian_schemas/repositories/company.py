"""
Company repository for organization management.

Provides lookup of Company entities by name or website domain.
"""

import re
import logging
from pathlib import Path
from typing import Optional, Type
from urllib.parse import urlparse
from datetime import datetime

from ..models import Company
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
    ) -> Company:
        """
        Create a minimal stub Company and save to vault.

        Args:
            name: Company name
            website: Optional website URL
            auto_created: Mark as auto-created for later review

        Returns:
            The created Company entity
        """
        # Clean name
        clean_name = re.sub(r'[^\w\s-]', '', name).strip()
        if not clean_name:
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

        extra_fields = {"auto_created": True} if auto_created else None
        self.save(company, body=body, extra_fields=extra_fields)

        return company
