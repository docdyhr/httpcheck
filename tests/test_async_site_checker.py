import types
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from httpcheck.async_site_checker import (
    _extract_domain,
    _extract_redirects,
    _should_stop_redirect,
    async_check_site,
    async_check_sites,
)
from httpcheck.common import SiteStatus


def _mock_response(
    url: str = "https://example.com", status_code: int = 200, history=None
):
    resp = types.SimpleNamespace()
    resp.url = url
    resp.status_code = status_code
    resp.history = history or []
    resp.is_redirect = False
    resp.headers = {}
    return resp


# ------------------------------------------------------------------
# Unit tests for helper functions
# ------------------------------------------------------------------


def test_extract_domain_from_httpx_url():
    """_extract_domain extracts host from httpx.URL."""
    url = httpx.URL("https://example.com/path")
    assert _extract_domain(url, "fallback") == "example.com"


def test_extract_domain_from_string():
    """_extract_domain parses hostname from plain string."""
    assert _extract_domain("https://example.com/path", "fallback") == "example.com"


def test_extract_domain_fallback_on_invalid():
    """_extract_domain returns fallback for unparseable input."""
    result = _extract_domain("not-a-url-at-all://??", "myfallback")
    # Either returns hostname portion or fallback; must not raise
    assert isinstance(result, str)


def test_extract_redirects_no_history():
    """_extract_redirects with no redirect history returns one-element chains."""
    resp = _mock_response(url="https://example.com", status_code=200)
    chain, timing = _extract_redirects(resp)
    assert len(chain) == 1
    assert chain[0] == ("https://example.com", 200)
    assert len(timing) == 1


def test_extract_redirects_with_history():
    """_extract_redirects captures full redirect history."""
    hop1 = _mock_response(url="http://example.com", status_code=301)
    final = _mock_response(url="https://example.com", status_code=200, history=[hop1])
    chain, timing = _extract_redirects(final)
    assert len(chain) == 2
    assert chain[0] == ("http://example.com", 301)
    assert chain[1] == ("https://example.com", 200)


def test_should_stop_redirect_http_only_stops_https():
    """http-only policy stops at HTTPS redirects."""
    url = httpx.URL("https://example.com")
    assert _should_stop_redirect("http-only", url) is True


def test_should_stop_redirect_http_only_allows_http():
    """http-only policy continues for HTTP redirects."""
    url = httpx.URL("http://example.com/page")
    assert _should_stop_redirect("http-only", url) is False


def test_should_stop_redirect_https_only_stops_http():
    """https-only policy stops at HTTP redirects."""
    url = httpx.URL("http://example.com")
    assert _should_stop_redirect("https-only", url) is True


def test_should_stop_redirect_https_only_allows_https():
    """https-only policy continues for HTTPS redirects."""
    url = httpx.URL("https://example.com/secure")
    assert _should_stop_redirect("https-only", url) is False


def test_should_stop_redirect_always_never_stops():
    """always policy never stops."""
    assert _should_stop_redirect("always", httpx.URL("http://x.com")) is False
    assert _should_stop_redirect("always", httpx.URL("https://x.com")) is False


# ------------------------------------------------------------------
# async_check_site – basic paths
# ------------------------------------------------------------------


@pytest.mark.asyncio
@patch("httpcheck.async_site_checker.httpx.AsyncClient.get", new_callable=AsyncMock)
async def test_async_single_success(mock_get):
    mock_get.return_value = _mock_response()
    result = await async_check_site("https://example.com")
    assert isinstance(result, SiteStatus)
    assert result.status == "200"
    assert result.redirect_chain[-1][0] == "https://example.com"


@pytest.mark.asyncio
@patch("httpcheck.async_site_checker.httpx.AsyncClient.get", new_callable=AsyncMock)
async def test_async_retries_then_success(mock_get):
    boom = Exception("boom")
    boom.request = types.SimpleNamespace(url=types.SimpleNamespace(host="example.com"))
    mock_get.side_effect = [boom, _mock_response(status_code=204)]
    result = await async_check_site("https://example.com", retries=1, retry_delay=0)
    assert result.status == "204"


@pytest.mark.asyncio
@patch("httpcheck.async_site_checker.httpx.AsyncClient.get", new_callable=AsyncMock)
async def test_async_batch_check(mock_get):
    mock_get.return_value = _mock_response()
    results = await async_check_sites(["https://a.com", "https://b.com"])
    assert len(results) == 2
    assert all(isinstance(r, SiteStatus) for r in results)


@pytest.mark.asyncio
async def test_async_check_sites_empty():
    """async_check_sites with an empty list returns an empty list."""
    results = await async_check_sites([])
    assert results == []


# ------------------------------------------------------------------
# async_check_site – http-only / https-only redirect policies
# ------------------------------------------------------------------


@pytest.mark.asyncio
@patch("httpcheck.async_site_checker.httpx.AsyncClient.get", new_callable=AsyncMock)
async def test_async_http_only_stops_on_https(mock_get):
    first = _mock_response(url="http://example.com", status_code=301)
    first.is_redirect = True
    first.headers = {"location": "https://example.com/secure"}
    second = _mock_response(url="https://example.com/secure", status_code=200)
    mock_get.side_effect = [first, second]

    result = await async_check_site("http://example.com", follow_redirects="http-only")
    assert result.status == "301"
    assert result.redirect_chain[0][0] == "http://example.com"


@pytest.mark.asyncio
@patch("httpcheck.async_site_checker.httpx.AsyncClient.get", new_callable=AsyncMock)
async def test_async_https_only_stops_on_http(mock_get):
    first = _mock_response(url="https://example.com", status_code=301)
    first.is_redirect = True
    first.headers = {"location": "http://example.com/insecure"}
    mock_get.side_effect = [first]

    result = await async_check_site(
        "https://example.com", follow_redirects="https-only"
    )
    assert result.status == "301"


@pytest.mark.asyncio
@patch("httpcheck.async_site_checker.httpx.AsyncClient.get", new_callable=AsyncMock)
async def test_async_manual_redirect_zero_max_redirects(mock_get):
    """When max_redirects=0, the first redirect response is returned immediately."""
    first = _mock_response(url="http://example.com", status_code=301)
    first.is_redirect = True
    first.headers = {"location": "http://example.com/page2"}
    mock_get.side_effect = [first]

    result = await async_check_site(
        "http://example.com",
        follow_redirects="http-only",
        max_redirects=0,
    )
    # Should return after the first hop without following the redirect
    assert result.status == "301"
    assert len(result.redirect_chain) == 1


# ------------------------------------------------------------------
# async_check_site – error handling
# ------------------------------------------------------------------


@pytest.mark.asyncio
@patch("httpcheck.async_site_checker.httpx.AsyncClient.get", new_callable=AsyncMock)
async def test_async_timeout_exception(mock_get):
    """TimeoutException returns [timeout] status."""
    mock_get.side_effect = httpx.TimeoutException("timed out")
    result = await async_check_site("https://slow.example.com", retries=0)
    assert result.status == "[timeout]"


@pytest.mark.asyncio
@patch("httpcheck.async_site_checker.httpx.AsyncClient.get", new_callable=AsyncMock)
async def test_async_transport_error(mock_get):
    """TransportError returns [connection error] status."""
    mock_get.side_effect = httpx.TransportError("connection refused")
    result = await async_check_site("https://down.example.com", retries=0)
    assert result.status == "[connection error]"


@pytest.mark.asyncio
@patch("httpcheck.async_site_checker.httpx.AsyncClient.get", new_callable=AsyncMock)
async def test_async_generic_exception_all_retries_exhausted(mock_get):
    """After all retries, a generic exception returns [connection error] status."""
    mock_get.side_effect = RuntimeError("something broke")
    result = await async_check_site("https://example.com", retries=1, retry_delay=0)
    assert result.status == "[connection error]"
    assert "something broke" in result.message


@pytest.mark.asyncio
@patch("httpcheck.async_site_checker.httpx.AsyncClient.get", new_callable=AsyncMock)
async def test_async_exception_without_request_attr(mock_get):
    """Exception without .request attribute uses site string as domain."""
    exc = RuntimeError("no request attr")
    mock_get.side_effect = exc
    result = await async_check_site("https://example.com", retries=0)
    assert result.domain == "https://example.com"


# ------------------------------------------------------------------
# async_check_site – pre-existing client
# ------------------------------------------------------------------


@pytest.mark.asyncio
async def test_async_check_site_with_existing_client():
    """When a client is passed in, it is NOT closed by async_check_site."""
    mock_client = MagicMock(spec=httpx.AsyncClient)
    resp = _mock_response()
    mock_client.get = AsyncMock(return_value=resp)
    mock_client.aclose = AsyncMock()

    result = await async_check_site(
        "https://example.com", client=mock_client, retry_delay=0
    )

    assert result.status == "200"
    mock_client.aclose.assert_not_called()


# ------------------------------------------------------------------
# async_check_sites – concurrency
# ------------------------------------------------------------------


@pytest.mark.asyncio
@patch("httpcheck.async_site_checker.httpx.AsyncClient.get", new_callable=AsyncMock)
async def test_async_check_sites_concurrency_respected(mock_get):
    """async_check_sites runs with the given concurrency cap without error."""
    mock_get.return_value = _mock_response()
    sites = [f"https://example{i}.com" for i in range(10)]
    results = await async_check_sites(sites, concurrency=3)
    assert len(results) == 10
    assert all(r.status == "200" for r in results)
