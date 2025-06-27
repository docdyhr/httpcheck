"""Site checking functionality for httpcheck."""

from datetime import datetime
from urllib.parse import urlparse

import requests
from requests.exceptions import ConnectionError as RequestsConnectionError
from requests.exceptions import HTTPError, RequestException, Timeout

from .common import STATUS_CODES, VERSION, SiteStatus


def check_site(
    site, timeout=5.0, retries=2, follow_redirects="always", max_redirects=30
):
    """Check website status code with redirect tracking."""
    custom_header = {"User-Agent": f"httpcheck Agent {VERSION}"}
    redirect_chain = []
    redirect_timing = []
    start_time = datetime.now()

    # Configure redirect behavior
    allow_redirects = True
    if follow_redirects == "never":
        allow_redirects = False

    # Configure session for finer control over redirects
    session = requests.Session()

    # Set max redirects
    session.max_redirects = max_redirects

    # Custom redirect logic for http-only or https-only options
    original_get = session.get

    if follow_redirects in ("http-only", "https-only"):

        def modified_get(url, *args, **kwargs):
            response = original_get(url, allow_redirects=False, *args, **kwargs)

            # Handle redirects manually based on protocol restriction
            redirect_count = 0
            while (
                response.is_redirect
                and redirect_count < max_redirects
                and "location" in response.headers
            ):
                redirect_url = response.headers["location"]

                # Check protocol for http-only or https-only
                if (
                    follow_redirects == "http-only"
                    and redirect_url.startswith("https://")
                    or follow_redirects == "https-only"
                    and redirect_url.startswith("http://")
                ):
                    break  # Stop following redirects if protocol doesn't match preference

                # Record redirect timing
                redirect_time = datetime.now()
                redirect_chain.append((response.url, response.status_code))

                # Follow the redirect
                response = original_get(
                    redirect_url, allow_redirects=False, *args, **kwargs
                )

                # Calculate and store timing for this redirect
                redirect_elapsed = (datetime.now() - redirect_time).total_seconds()
                redirect_timing.append(
                    (redirect_url, response.status_code, redirect_elapsed)
                )

                redirect_count += 1

            return response

        session.get = modified_get

    for attempt in range(retries + 1):
        try:
            # Reset tracking for each attempt
            redirect_chain = []
            redirect_timing = []
            start_time = datetime.now()

            # Simple case: all redirects or no redirects
            if follow_redirects in ("always", "never"):
                hop_start_time = datetime.now()
                response = session.get(
                    site,
                    headers=custom_header,
                    timeout=timeout,
                    allow_redirects=allow_redirects,
                )

                # Track timing for the initial request
                initial_time = (datetime.now() - hop_start_time).total_seconds()

                # Track redirect chain if we're allowing redirects
                if allow_redirects and response.history:
                    # First, handle all the redirections that happened
                    prev_time = initial_time
                    for i, r in enumerate(response.history):
                        hop_time = (
                            prev_time if i == 0 else 0.0
                        )  # We don't have individual timing for requests history
                        redirect_chain.append((r.url, r.status_code))
                        redirect_timing.append((r.url, r.status_code, hop_time))
                        prev_time = 0.0  # Reset after first hop since we don't have detailed timing

                    # Then add the final response
                    redirect_chain.append((response.url, response.status_code))
                    redirect_timing.append((response.url, response.status_code, 0.0))
                elif not allow_redirects and response.is_redirect:
                    # If we're not following redirects but got one
                    redirect_chain.append((response.url, response.status_code))
                    redirect_timing.append(
                        (response.url, response.status_code, initial_time)
                    )
            else:
                # For http-only and https-only, we already handled this with the modified session.get
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
        except Timeout:
            if attempt == retries:
                return SiteStatus(
                    urlparse(site).hostname, "[timeout]", "Request timed out"
                )
        except RequestsConnectionError:
            if attempt == retries:
                return SiteStatus(
                    urlparse(site).hostname,
                    "[connection error]",
                    "Connection failed",
                )
        except HTTPError as e:
            return SiteStatus(
                urlparse(site).hostname, str(e.response.status_code), str(e)
            )
        except RequestException:
            if attempt == retries:
                return SiteStatus(
                    urlparse(site).hostname, "[request error]", "Request failed"
                )

    # Default return in case all retries fail
    return SiteStatus(urlparse(site).hostname, "[unknown error]", "All retries failed")
