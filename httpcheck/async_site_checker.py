"""Async HTTP site checking for httpcheck."""

from __future__ import annotations

import asyncio
import time
from collections.abc import Iterable
from urllib.parse import urlparse

import httpx

from .common import STATUS_CODES, VERSION, SiteStatus

DEFAULT_LIMITS = httpx.Limits(max_connections=50, max_keepalive_connections=20)


def _create_headers(custom_headers: dict | None = None) -> dict:
    """Create default headers including User-Agent."""
    headers = {"User-Agent": f"httpcheck Async Agent {VERSION}"}
    if custom_headers:
        headers.update(custom_headers)
    return headers


def _extract_domain(url_like: str | httpx.URL, fallback: str) -> str:
    """Return host component from httpx.URL or string URL."""
    try:
        if isinstance(url_like, httpx.URL):
            return str(url_like.host)
        parsed = urlparse(str(url_like))
        return parsed.hostname or fallback
    except (AttributeError, ValueError):
        return fallback


def _extract_redirects(
    response: httpx.Response,
) -> tuple[list[tuple[str, int]], list[tuple[str, int, float]]]:
    """Return redirect chain and timing from an httpx response."""
    chain: list[tuple[str, int]] = []
    timing: list[tuple[str, int, float]] = []
    for hop in response.history:
        chain.append((str(hop.url), hop.status_code))
        timing.append((str(hop.url), hop.status_code, 0.0))
    chain.append((str(response.url), response.status_code))
    timing.append((str(response.url), response.status_code, 0.0))
    return chain, timing


def _should_stop_redirect(follow_redirects: str, redirect_url: httpx.URL) -> bool:
    """Return True when protocol policy blocks following this redirect."""
    if follow_redirects == "http-only" and redirect_url.scheme == "https":
        return True
    if follow_redirects == "https-only" and redirect_url.scheme == "http":
        return True
    return False


async def _manual_redirect_flow(
    client: httpx.AsyncClient,
    url: str,
    *,
    timeout: float,
    max_redirects: int,
    follow_redirects: str,
) -> tuple[httpx.Response, float, list[tuple[str, int]], list[tuple[str, int, float]]]:
    """Follow redirects manually to enforce protocol restrictions."""
    chain: list[tuple[str, int]] = []
    timing: list[tuple[str, int, float]] = []

    current_url: httpx.URL = httpx.URL(url)
    total_start = time.monotonic()
    redirects = 0
    while True:
        hop_start = time.monotonic()
        response = await client.get(
            str(current_url),
            follow_redirects=False,
            timeout=timeout,
        )
        hop_elapsed = time.monotonic() - hop_start

        chain.append((str(response.url), response.status_code))
        timing.append((str(response.url), response.status_code, hop_elapsed))

        if not response.is_redirect or "location" not in response.headers:
            break

        if redirects >= max_redirects:
            break

        location = response.headers.get("location", "")
        base_url = (
            response.url
            if isinstance(response.url, httpx.URL)
            else httpx.URL(str(response.url))
        )
        next_url = base_url.join(location)
        if _should_stop_redirect(follow_redirects, next_url):
            break

        redirects += 1
        current_url = next_url

    total_elapsed = time.monotonic() - total_start
    return response, total_elapsed, chain, timing


async def async_check_site(
    site: str,
    timeout: float = 5.0,
    retries: int = 2,
    *,
    follow_redirects: str = "always",
    max_redirects: int = 30,
    custom_headers: dict | None = None,
    verify_ssl: bool = True,
    retry_delay: float = 1.0,
    client: httpx.AsyncClient | None = None,
) -> SiteStatus:
    """Async version of check_site with optional protocol-restricted redirects."""
    headers = _create_headers(custom_headers)
    allow_redirects = follow_redirects == "always"
    manual_redirects = follow_redirects in {"http-only", "https-only"}

    async def _execute_request(
        active_client: httpx.AsyncClient,
    ) -> tuple[httpx.Response, float]:
        start = time.monotonic()
        response = await active_client.get(
            site,
            headers=headers,
            timeout=timeout,
            follow_redirects=allow_redirects,
            max_redirects=max_redirects,
        )
        elapsed = time.monotonic() - start
        return response, elapsed

    owns_client = client is None
    active_client = client or httpx.AsyncClient(
        verify=verify_ssl, limits=DEFAULT_LIMITS, headers=headers
    )

    try:
        for attempt in range(retries + 1):
            try:
                if manual_redirects:
                    (
                        response,
                        response_time,
                        redirect_chain,
                        redirect_timing,
                    ) = await _manual_redirect_flow(
                        active_client,
                        site,
                        timeout=timeout,
                        max_redirects=max_redirects,
                        follow_redirects=follow_redirects,
                    )
                else:
                    response, response_time = await _execute_request(active_client)
                    redirect_chain, redirect_timing = _extract_redirects(response)

                domain = _extract_domain(getattr(response, "url", site), site)
                return SiteStatus(
                    domain=domain,
                    status=str(response.status_code),
                    message=STATUS_CODES.get(str(response.status_code), "Unknown"),
                    redirect_chain=redirect_chain,
                    response_time=response_time,
                    redirect_timing=redirect_timing,
                )
            except (httpx.RequestError, httpx.HTTPError, ValueError, OSError) as exc:
                if attempt == retries:
                    status = (
                        "[timeout]"
                        if isinstance(exc, httpx.TimeoutException)
                        else "[connection error]"
                    )
                    domain = site
                    try:
                        req = exc.request  # type: ignore[attr-defined]
                        domain = _extract_domain(getattr(req, "url", site), site)
                    except (AttributeError, RuntimeError):
                        pass
                    return SiteStatus(domain, status, str(exc))
                if retry_delay > 0:
                    await asyncio.sleep(retry_delay)
    finally:
        if owns_client:
            await active_client.aclose()


async def async_check_sites(
    sites: Iterable[str],
    *,
    timeout: float = 5.0,
    retries: int = 2,
    follow_redirects: str = "always",
    max_redirects: int = 30,
    custom_headers: dict | None = None,
    verify_ssl: bool = True,
    retry_delay: float = 1.0,
    concurrency: int = 50,
) -> list[SiteStatus]:
    """Check many sites concurrently with a shared client and semaphore."""
    sem = asyncio.Semaphore(concurrency)
    headers = _create_headers(custom_headers)
    async with httpx.AsyncClient(
        verify=verify_ssl, limits=DEFAULT_LIMITS, headers=headers
    ) as client:

        async def worker(url: str) -> SiteStatus:
            async with sem:
                return await async_check_site(
                    url,
                    timeout=timeout,
                    retries=retries,
                    follow_redirects=follow_redirects,
                    max_redirects=max_redirects,
                    custom_headers=None,  # headers already applied on client
                    verify_ssl=verify_ssl,
                    retry_delay=retry_delay,
                    client=client,
                )

        return await asyncio.gather(*[worker(u) for u in sites])
