"""Site checking functionality for httpcheck."""

import time
from datetime import datetime
from urllib.parse import urlparse

import requests
from requests.exceptions import ConnectionError as RequestsConnectionError
from requests.exceptions import HTTPError, RequestException, Timeout

from .common import STATUS_CODES, VERSION, SiteStatus


def _create_custom_headers(custom_headers=None):
    """Create custom headers with User-Agent."""
    custom_header = {"User-Agent": f"httpcheck Agent {VERSION}"}
    if custom_headers:
        custom_header.update(custom_headers)
    return custom_header


def _configure_session(follow_redirects, max_redirects, verify_ssl):
    """Configure requests session with redirect and SSL settings."""
    session = requests.Session()
    session.max_redirects = max_redirects
    session.verify = verify_ssl

    allow_redirects = follow_redirects != "never"
    return session, allow_redirects


def _create_protocol_restricted_session(
    session, follow_redirects, *, max_redirects, redirect_chain, redirect_timing
):
    """Create a session with protocol-restricted redirect handling."""
    original_get = session.get

    def modified_get(url, *args, **kwargs):
        response = original_get(url, allow_redirects=False, *args, **kwargs)
        redirect_count = 0

        while (
            response.is_redirect
            and redirect_count < max_redirects
            and "location" in response.headers
        ):
            redirect_url = response.headers["location"]

            # Check protocol restrictions
            if _should_stop_redirect(follow_redirects, redirect_url):
                break

            # Record redirect timing
            redirect_time = datetime.now()
            redirect_chain.append((response.url, response.status_code))

            # Follow the redirect
            response = original_get(
                redirect_url, allow_redirects=False, *args, **kwargs
            )

            # Calculate and store timing
            redirect_elapsed = (datetime.now() - redirect_time).total_seconds()
            redirect_timing.append(
                (redirect_url, response.status_code, redirect_elapsed)
            )
            redirect_count += 1

        return response

    return modified_get


def _should_stop_redirect(follow_redirects, redirect_url):
    """Check if redirect should be stopped based on protocol restrictions."""
    if follow_redirects == "http-only" and redirect_url.startswith("https://"):
        return True
    if follow_redirects == "https-only" and redirect_url.startswith("http://"):
        return True
    return False


def _track_redirect_chain(
    response, allow_redirects, initial_time, redirect_chain, redirect_timing
):
    """Track redirect chain and timing for standard redirects."""
    if allow_redirects and response.history:
        # Handle all redirections that happened
        prev_time = initial_time
        for i, r in enumerate(response.history):
            hop_time = prev_time if i == 0 else 0.0
            redirect_chain.append((r.url, r.status_code))
            redirect_timing.append((r.url, r.status_code, hop_time))
            prev_time = 0.0

        # Add the final response
        redirect_chain.append((response.url, response.status_code))
        redirect_timing.append((response.url, response.status_code, 0.0))
    elif not allow_redirects and response.is_redirect:
        # Not following redirects but got one
        redirect_chain.append((response.url, response.status_code))
        redirect_timing.append((response.url, response.status_code, initial_time))


def _handle_request_exception(e, attempt, retries, *, retry_delay, site, verify_ssl):
    """Handle request exceptions with retry logic."""
    if attempt == retries:
        if isinstance(e, Timeout):
            return SiteStatus(urlparse(site).hostname, "[timeout]", "Request timed out")
        elif isinstance(e, RequestsConnectionError):
            return SiteStatus(
                urlparse(site).hostname, "[connection error]", "Connection failed"
            )
        elif isinstance(e, HTTPError):
            return SiteStatus(
                urlparse(site).hostname, str(e.response.status_code), str(e)
            )
        elif isinstance(e, RequestException):
            error_msg = "Request failed"
            if not verify_ssl and "SSL" in str(e):
                error_msg = "SSL verification disabled - " + str(e)
            return SiteStatus(urlparse(site).hostname, "[request error]", error_msg)

    if retry_delay > 0 and attempt < retries:
        time.sleep(retry_delay)
    return None


def check_site(
    site,
    timeout=5.0,
    retries=2,
    *,
    follow_redirects="always",
    max_redirects=30,
    custom_headers=None,
    verify_ssl=True,
    retry_delay=1.0,
):
    """Check website status code with redirect tracking.

    Args:
        site: URL to check
        timeout: Request timeout in seconds
        retries: Number of retry attempts
        follow_redirects: Redirect behavior ('always', 'never', 'http-only', 'https-only')
        max_redirects: Maximum number of redirects to follow
        custom_headers: Dictionary of custom HTTP headers
        verify_ssl: Whether to verify SSL certificates
        retry_delay: Delay between retries in seconds
    """
    custom_header = _create_custom_headers(custom_headers)
    session, allow_redirects = _configure_session(
        follow_redirects, max_redirects, verify_ssl
    )

    for attempt in range(retries + 1):
        try:
            # Reset tracking for each attempt
            redirect_chain = []
            redirect_timing = []
            start_time = datetime.now()

            # Handle protocol-restricted redirects
            if follow_redirects in ("http-only", "https-only"):
                session.get = _create_protocol_restricted_session(
                    session,
                    follow_redirects,
                    max_redirects=max_redirects,
                    redirect_chain=redirect_chain,
                    redirect_timing=redirect_timing,
                )

            # Make the request
            if follow_redirects in ("always", "never"):
                hop_start_time = datetime.now()
                response = session.get(
                    site,
                    headers=custom_header,
                    timeout=timeout,
                    allow_redirects=allow_redirects,
                )
                initial_time = (datetime.now() - hop_start_time).total_seconds()
                _track_redirect_chain(
                    response,
                    allow_redirects,
                    initial_time,
                    redirect_chain,
                    redirect_timing,
                )
            else:
                # For protocol-restricted redirects
                response = session.get(site, headers=custom_header, timeout=timeout)

            end_time = datetime.now()
            response_time = (end_time - start_time).total_seconds()

            return SiteStatus(
                domain=urlparse(site).hostname,
                status=str(response.status_code),
                message=STATUS_CODES.get(str(response.status_code), "Unknown"),
                redirect_chain=redirect_chain,
                response_time=response_time,
                redirect_timing=redirect_timing,
            )

        except (Timeout, RequestsConnectionError, HTTPError, RequestException) as e:
            error_result = _handle_request_exception(
                e,
                attempt,
                retries,
                retry_delay=retry_delay,
                site=site,
                verify_ssl=verify_ssl,
            )
            if error_result:
                return error_result

    # Default return in case all retries fail
    return SiteStatus(urlparse(site).hostname, "[unknown error]", "All retries failed")
