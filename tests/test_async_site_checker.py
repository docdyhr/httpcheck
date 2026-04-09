import types
from unittest.mock import AsyncMock, patch

import pytest

from httpcheck.async_site_checker import async_check_site, async_check_sites
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
@patch("httpcheck.async_site_checker.httpx.AsyncClient.get", new_callable=AsyncMock)
async def test_async_http_only_stops_on_https(mock_get):
    first = _mock_response(url="http://example.com", status_code=301)
    first.is_redirect = True
    first.headers = {"location": "https://example.com/secure"}
    second = _mock_response(url="https://example.com/secure", status_code=200)
    second.is_redirect = False
    second.headers = {}
    mock_get.side_effect = [first, second]

    result = await async_check_site("http://example.com", follow_redirects="http-only")
    assert result.status == "301"
    assert result.redirect_chain[0][0] == "http://example.com"
