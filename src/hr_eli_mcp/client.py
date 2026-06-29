"""Async httpx client for the Croatian Narodne novine gazette (narodne-novine.nn.hr) with cache.

Keyless (Open Government Data). Documents are addressed by ELI coordinate
(/eli/sluzbeni/{year}/{issue}/{doc}); metadata is JSON-LD, full text is HTML, and an issue's
documents are listed in the per-issue sitemap. We keep our own backoff + cache.
"""

from __future__ import annotations

import anyio
import httpx

from .cache import HttpCache

DEFAULT_BASE_URL = "https://narodne-novine.nn.hr"
DEFAULT_TIMEOUT = httpx.Timeout(60.0, connect=10.0)
USER_AGENT = "hr-eli-mcp/0.1.0 (+https://github.com/matematicsolutions/hr-eli-mcp)"

_RETRY_STATUS = frozenset({429, 500, 502, 503, 504})
_MAX_ATTEMPTS = 3


class NarodneNovineClient:
    """Async client. Use as ``async with NarodneNovineClient() as c: ...``."""

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        cache: HttpCache | None = None,
        timeout: httpx.Timeout = DEFAULT_TIMEOUT,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self._cache = cache or HttpCache()
        self._http = httpx.AsyncClient(
            timeout=timeout,
            headers={"User-Agent": USER_AGENT, "Accept-Language": "hr,en"},
            follow_redirects=True,
        )

    async def __aenter__(self) -> NarodneNovineClient:
        return self

    async def __aexit__(self, *_exc: object) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        await self._http.aclose()
        self._cache.close()

    async def _get(self, url: str, *, accept: str, category: str) -> str:
        cached = self._cache.get(url)
        if cached is not None and isinstance(cached, str):
            return cached
        last_exc: Exception | None = None
        for attempt in range(_MAX_ATTEMPTS):
            try:
                resp = await self._http.get(url, headers={"Accept": accept})
                resp.raise_for_status()
                self._cache.set(url, resp.text, ttl=HttpCache.ttl_for(category))
                return resp.text
            except httpx.HTTPStatusError as exc:
                last_exc = exc
                if exc.response.status_code not in _RETRY_STATUS or attempt == _MAX_ATTEMPTS - 1:
                    raise
            except (httpx.TransportError, httpx.TimeoutException) as exc:
                last_exc = exc
                if attempt == _MAX_ATTEMPTS - 1:
                    raise
            await anyio.sleep(0.5 * (2**attempt))
        assert last_exc is not None
        raise last_exc

    async def get_jsonld(self, year: int, issue: int, doc: int) -> str:
        url = f"{self.base_url}/eli/sluzbeni/{year}/{issue}/{doc}/json-ld"
        return await self._get(url, accept="application/ld+json", category="act")

    async def get_html(self, year: int, issue: int, doc: int) -> str:
        url = f"{self.base_url}/eli/sluzbeni/{year}/{issue}/{doc}/hrv/html"
        return await self._get(url, accept="text/html", category="act")

    async def get_issue_sitemap(self, year: int, issue: int) -> str:
        url = f"{self.base_url}/sitemap_1_{year}_{issue}.xml"
        return await self._get(url, accept="application/xml", category="list")
