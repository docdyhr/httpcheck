#!/usr/bin/env python3
"""Simple command line program to check website status.

Author: Thomas Juul Dyhr thomas@dyhr.com
Purpose: Check one or more websites status
Release date: 27 April 2025
Version: 1.3.0
"""


import argparse
import concurrent.futures
import json
import os
import pickle
import platform
import re
import subprocess
import sys
import textwrap
from datetime import datetime
from typing import List, NamedTuple
from urllib.parse import urlparse

import requests
from requests.exceptions import ConnectionError as RequestsConnectionError
from requests.exceptions import HTTPError, RequestException, Timeout
from tabulate import tabulate
from tqdm import tqdm

VERSION = "1.3.0"

# HTTP status codes - https://en.wikipedia.org/wiki/List_of_HTTP_status_codes
STATUS_CODES_JSON = """{
    "100": "Continue",
    "101": "Switching Protocols",
    "102": "Processing",
    "200": "OK",
    "201": "Created",
    "202": "Accepted",
    "203": "Non-authoritative Information",
    "204": "No Content",
    "205": "Reset Content",
    "206": "Partial Content",
    "207": "Multi-Status",
    "208": "Already Reported",
    "226": "IM Used",
    "300": "Multiple Choices",
    "301": "Moved Permanently",
    "302": "Found",
    "303": "See Other",
    "304": "Not Modified",
    "305": "Use Proxy",
    "307": "Temporary Redirect",
    "308": "Permanent Redirect",
    "400": "Bad Request",
    "401": "Unauthorized",
    "402": "Payment Required",
    "403": "Forbidden",
    "404": "Not Found",
    "405": "Method Not Allowed",
    "406": "Not Acceptable",
    "407": "Proxy Authentication Required",
    "408": "Request Timeout",
    "409": "Conflict",
    "410": "Gone",
    "411": "Length Required",
    "412": "Precondition Failed",
    "413": "Payload Too Large",
    "414": "Request-URI Too Long",
    "415": "Unsupported Media Type",
    "416": "Requested Range Not Satisfiable",
    "417": "Expectation Failed",
    "418": "I'm a teapot",
    "421": "Misdirected Request",
    "422": "Unprocessable Entity",
    "423": "Locked",
    "424": "Failed Dependency",
    "426": "Upgrade Required",
    "428": "Precondition Required",
    "429": "Too Many Requests",
    "431": "Request Header Fields Too Large",
    "444": "Connection Closed Without Response",
    "451": "Unavailable For Legal Reasons",
    "499": "Client Closed Request",
    "500": "Internal Server Error",
    "501": "Not Implemented",
    "502": "Bad Gateway",
    "503": "Service Unavailable",
    "504": "Gateway Timeout",
    "505": "HTTP Version Not Supported",
    "506": "Variant Also Negotiates",
    "507": "Insufficient Storage",
    "508": "Loop Detected",
    "510": "Not Extended",
    "511": "Network Authentication Required",
    "599": "Network Connect Timeout Error"
}"""

# Parse STATUS_CODES_JSON once at module level
STATUS_CODES = json.loads(STATUS_CODES_JSON)

# https://en.wikipedia.org/wiki/List_of_HTTP_status_codes
# INFO = 'https://bit.ly/2FMMxXC'


def get_arguments():
    """Handle webiste arguments."""
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent(__doc__),
    )
    parser.add_argument(
        "site",
        nargs="*",
        type=str,  # Changed from url_validation to str to handle validation later
        help="return http status codes for one or more websites",
    )
    parser.add_argument(
        "-t",
        "--tld",
        action="store_true",
        dest="tld",
        help="check if domain is in global list of TLDs",
    )

    # TLD validation options
    parser.add_argument(
        "--disable-tld-checks",
        dest="disable_tld",
        action="store_true",
        help="disable TLD validation checks",
    )
    parser.add_argument(
        "--tld-warning-only",
        dest="tld_warning_only",
        action="store_true",
        help="show warnings for invalid TLDs without failing",
    )
    parser.add_argument(
        "--update-tld-list",
        dest="update_tld",
        action="store_true",
        help="force update of the TLD list from publicsuffix.org",
    )
    parser.add_argument(
        "--tld-cache-days",
        dest="tld_cache_days",
        type=int,
        default=30,
        help="number of days to keep the TLD cache valid (default: 30)",
    )

    parser.add_argument(
        "--timeout",
        type=float,
        default=5.0,
        help="timeout in seconds for each request",
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=2,
        help="number of retries for failed requests",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=10,
        help="number of concurrent workers for fast mode",
    )

    # File input handling options
    parser.add_argument(
        "--file-summary",
        dest="file_summary",
        action="store_true",
        help="show summary of file parsing results (valid URLs, comments, etc.)",
    )
    parser.add_argument(
        "--comment-style",
        dest="comment_style",
        choices=["hash", "slash", "both"],
        default="both",
        help="comment style to recognize: hash (#), slash (//), or both (default: both)",
    )

    # Add redirect options
    parser.add_argument(
        "--follow-redirects",
        dest="follow_redirects",
        choices=["always", "never", "http-only", "https-only"],
        default="always",
        help="control redirect following: always, never, http-only, or https-only",
    )
    parser.add_argument(
        "--max-redirects",
        dest="max_redirects",
        type=int,
        default=30,
        help="maximum number of redirects to follow (default: 30)",
    )
    parser.add_argument(
        "--show-redirect-timing",
        dest="show_redirect_timing",
        action="store_true",
        help="show detailed timing for each redirect in the chain",
    )

    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "-q",
        "--quiet",
        action="store_true",  # flag only no args stores True / False value
        dest="quiet",
        help="only print errors",
    )
    group.add_argument(
        "-v",
        "--verbose",
        action="store_true",  # flag only no args stores True / False value
        dest="verbose",
        help="increase output verbosity",
    )
    group.add_argument(
        "-c",
        "--code",
        action="store_true",  # flag only no args stores True / False value
        dest="code",
        help="only print status code",
    )
    group.add_argument(
        "-f",
        "--fast",
        action="store_true",  # flag only no args stores True / False value
        dest="fast",
        help="fast check wtih threading",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")

    options = parser.parse_args()

    # Handle file input with @ prefix
    validated_sites = []
    for site in options.site:
        if site.startswith("@"):
            try:
                handler = FileInputHandler(
                    site[1:],
                    verbose=options.file_summary or options.verbose,
                    comment_style=options.comment_style,
                )
                for validated_url in handler.parse():
                    validated_sites.append(validated_url)
            except Exception as e:
                print(f"[-] Error processing file {site[1:]}: {str(e)}")
        else:
            try:
                validated_url = url_validation(site)
                validated_sites.append(validated_url)
            except argparse.ArgumentTypeError as e:
                print(str(e))

    # Handle stdin if no sites provided
    if not validated_sites and not sys.stdin.isatty():
        for line in sys.stdin:
            line = line.strip()
            if line and not (line.startswith("#") or line.startswith("//")):
                # Basic comment handling for stdin
                if "#" in line:
                    line = line[: line.find("#")].strip()
                if "//" in line:
                    line = line[: line.find("//")].strip()

                if line:  # Check again after comment removal
                    try:
                        validated_url = url_validation(line)
                        validated_sites.append(validated_url)
                    except argparse.ArgumentTypeError as e:
                        print(str(e))

    if not validated_sites:
        parser.error(
            "[-] Please specify a website or pipe URLs to check, "
            "use --help for more info."
        )

    options.site = validated_sites
    return options


def url_validation(site_url):
    """Check if url is valid and return it."""
    site_url = site_url if site_url.startswith("http") else f"http://{site_url}"
    # check url with regex
    regex = re.compile(
        r"^(?:http|ftp)s?://"  # http:// or https://
        #  domain
        r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|"
        r"localhost|"  # localhost...
        r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # ...or ip
        r"(?::\d+)?"  # optional port
        r"(?:/?|[/?]\S+)$",
        re.IGNORECASE,
    )

    if re.match(regex, site_url) is not None:
        return site_url
    msg = f"[-] Invalid URL: '{site_url}'"
    raise argparse.ArgumentTypeError(msg)


class InvalidTLDException(Exception):
    """Exception raised for invalid top-level domain (TLD)."""


def load_tlds(file_path):
    """Load TLDs from a file and return as a list."""
    tlds = []
    with open(file_path, encoding="utf-8") as tld_file:
        for line in tld_file:
            line = line.strip()
            if line and not line.startswith("//"):
                tlds.append(line)
    return tlds


def tld_check(url, tld_file_path):
    """Check url for valid TLD against tld file."""
    tlds = load_tlds(tld_file_path)

    url_elements = urlparse(url).netloc.split(".")
    for i in range(-len(url_elements), 0):
        last_i_elements = url_elements[i:]
        candidate = ".".join(last_i_elements)
        wildcard_candidate = ".".join(["*"] + last_i_elements[1:])
        exception_candidate = f"!{candidate}"

        if exception_candidate in tlds:
            return ".".join(url_elements[i:])
        if candidate in tlds or wildcard_candidate in tlds:
            return ".".join(url_elements[i - 1 :])

    raise InvalidTLDException(f"[-] Domain not in global list of TLDs: '{url}'")


class SiteStatus(NamedTuple):
    """Represents the status of a checked website"""

    domain: str
    status: str
    message: str
    redirect_chain: list[tuple] = []
    response_time: float = 0.0
    redirect_timing: list[tuple] = (
        []
    )  # List of (url, status_code, response_time) tuples


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


def print_format(
    result: SiteStatus,
    quiet: bool,
    verbose: bool,
    code: bool,
    show_redirect_timing: bool = False,
):
    """Format & print results in columns."""
    output = ""
    if code:
        output = result.status
    elif verbose:
        headers = ["Domain", "Status", "Response Time", "Message"]
        table_data = [
            [
                result.domain,
                result.status,
                f"{result.response_time:.2f}s",
                STATUS_CODES.get(str(result.status), "Unknown"),
            ]
        ]

        output = tabulate(table_data, headers=headers, tablefmt="grid")

        if result.redirect_chain:
            output += "\nRedirect Chain:\n"
            if show_redirect_timing and result.redirect_timing:
                timing_data = []
                for i, (url, status_code, response_time) in enumerate(
                    result.redirect_timing
                ):
                    time_str = f"{response_time:.3f}s" if response_time > 0 else "–"
                    timing_data.append([i + 1, url, status_code, time_str])
                output += tabulate(
                    timing_data,
                    headers=["Step", "URL", "Status", "Time"],
                    tablefmt="grid",
                )
            else:
                redirect_data = [
                    [i + 1, url, code]
                    for i, (url, code) in enumerate(result.redirect_chain)
                ]
                output += tabulate(
                    redirect_data,
                    headers=["Step", "URL", "Status"],
                    tablefmt="grid",
                )
    elif quiet:
        if (
            result.status in ("[timeout]", "[connection error]")
            or int(result.status) >= 400
        ):
            output = f"{result.domain} {result.status}"
    else:
        output = tabulate([[result.domain, result.status]], tablefmt="simple")

    return output


def notify(title, message, failed_sites=None):
    """Send system notification using osascript on macOS."""
    if platform.system() == "Darwin":  # macOS only
        try:
            notification_message = message
            subtitle = ""
            if failed_sites:
                # Use subtitle for summary, keep message concise
                subtitle = message  # Original summary message
                if len(failed_sites) < 10:
                    failed_list = "\n".join(f"• {site}" for site in failed_sites)
                    notification_message = f"Failed sites:\n{failed_list}"
                else:
                    notification_message = (
                        f"{len(failed_sites)} sites failed. See terminal for details."
                    )

            # Construct the AppleScript command with proper escaping
            escaped_message = notification_message.replace('"', '\\"').replace(
                "\n", "\\n"
            )
            escaped_title = title.replace('"', '\\"')
            escaped_subtitle = subtitle.replace('"', '\\"')

            script = (
                f'display notification "{escaped_message}" '
                f'with title "{escaped_title}" '
                f'subtitle "{escaped_subtitle}"'
            )
            cmd = ["osascript", "-e", script]

            # Execute the command
            subprocess.run(cmd, check=True, capture_output=True)

        except FileNotFoundError:
            # This should generally not happen on macOS as osascript is standard
            print("\nWarning: 'osascript' command not found. Cannot send notification.")
        except subprocess.CalledProcessError as e:
            # Handle errors from osascript execution
            print(
                f"\nWarning: Could not send notification using osascript: {e.stderr.decode()}"
            )
        except Exception as e:
            # Catch any other unexpected errors
            print(
                f"\nWarning: An unexpected error occurred during notification: {str(e)}"
            )


def process_site_status(site_status, site_url, successful, failures, failed_sites):
    """Process a site's status and update counters."""
    if not isinstance(site_status, SiteStatus):
        failures += 1
        failed_sites.append(f"{urlparse(site_url).hostname} (Error)")
        return successful, failures

    try:
        status_code = int(site_status.status)
        if 200 <= status_code < 400:
            successful += 1
        else:
            failures += 1
            failed_sites.append(f"{site_status.domain} ({site_status.status})")
    except ValueError:
        failures += 1
        failed_sites.append(f"{site_status.domain} ({site_status.status})")
    return successful, failures


def check_sites_serial(options, successful, failures, failed_sites):
    """Check sites one at a time."""
    results = []
    with tqdm(
        total=len(options.site),
        desc="Checking sites",
        disable=options.quiet,
        position=0,
        leave=True,
    ) as pbar:
        for site in options.site:
            status = check_site(
                site,
                options.timeout,
                options.retries,
                options.follow_redirects,
                options.max_redirects,
            )
            formatted_output = print_format(
                status,
                options.quiet,
                options.verbose,
                options.code,
                show_redirect_timing=options.show_redirect_timing,
            )
            results.append(formatted_output)
            successful, failures = process_site_status(
                status, site, successful, failures, failed_sites
            )
            pbar.update(1)

    # Print results after progress bar is done
    print("\n".join(filter(None, results)))
    return successful, failures


def check_sites_parallel(options, successful, failures, failed_sites):
    """Check sites in parallel using ThreadPoolExecutor."""
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=options.workers) as executor:
        future_to_site = {
            executor.submit(
                check_site,
                site,
                options.timeout,
                options.retries,
                options.follow_redirects,
                options.max_redirects,
            ): site
            for site in options.site
        }

        with tqdm(
            total=len(future_to_site),
            desc="Checking sites",
            disable=options.quiet,
            position=0,
            leave=True,
        ) as pbar:
            for future in concurrent.futures.as_completed(future_to_site):
                site = future_to_site[future]
                try:
                    status = future.result()
                    formatted_output = print_format(
                        status,
                        options.quiet,
                        options.verbose,
                        options.code,
                        show_redirect_timing=options.show_redirect_timing,
                    )
                    results.append(formatted_output)
                    successful, failures = process_site_status(
                        status, site, successful, failures, failed_sites
                    )
                except (RequestException, RuntimeError) as e:
                    error_msg = f"[-] {site}: {str(e)}"
                    results.append(error_msg)
                    failures += 1
                    failed_sites.append(f"{urlparse(site).hostname} (Error)")
                pbar.update(1)

    # Print results after progress bar is done
    print("\n".join(filter(None, results)))
    return successful, failures


def check_tlds(options, failures, failed_sites):
    """Check TLDs if requested."""
    # Skip TLD checks if disabled
    if options.disable_tld:
        return failures

    # Skip if TLD check not requested
    if not options.tld:
        return failures

    try:
        # Initialize TLDManager with options
        tld_manager = TLDManager(
            force_update=options.update_tld,
            cache_days=options.tld_cache_days,
            verbose=options.verbose,
            warning_only=options.tld_warning_only,
        )

        # Check each site
        for site in options.site:
            try:
                tld_manager.validate_tld(site)
            except InvalidTLDException as e:
                print(str(e))
                failures += 1
                failed_sites.append(f"{urlparse(site).hostname} (Invalid TLD)")

    except Exception as e:
        if options.verbose:
            print(f"[-] Error during TLD validation: {str(e)}")

    return failures


class FileInputHandler:
    """Handles input from domain files with enhanced features.

    Features:
    - Strips whitespace and handles empty lines
    - Supports multiple comment formats (# and //)
    - Handles inline comments
    - Performs input validation
    - Gracefully handles malformed lines
    """

    def __init__(self, file_path, verbose=False, comment_style="both"):
        """Initialize with file path and verbosity setting.

        Args:
            file_path: Path to the file to parse
            verbose: Whether to print verbose output
            comment_style: Which comment style to recognize ('hash', 'slash', or 'both')
        """
        self.file_path = file_path
        self.verbose = verbose
        self.comment_style = comment_style
        self.line_count = 0
        self.valid_count = 0
        self.comment_count = 0
        self.empty_count = 0
        self.error_count = 0

        # Set up comment markers based on style preference
        self.comment_markers = []
        if comment_style in ("hash", "both"):
            self.comment_markers.append("#")
        if comment_style in ("slash", "both"):
            self.comment_markers.append("//")

    def parse(self):
        """Parse the input file and yield valid URLs."""
        try:
            with open(self.file_path, encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    self.line_count += 1
                    result = self._process_line(line, line_num)
                    if result:
                        yield result

            if self.verbose:
                summary = (
                    f"\nFile: {self.file_path}\n"
                    f"  Lines processed: {self.line_count}\n"
                    f"  Valid URLs: {self.valid_count}\n"
                    f"  Comments: {self.comment_count}\n"
                    f"  Empty lines: {self.empty_count}\n"
                    f"  Errors: {self.error_count}\n"
                )
                print(summary)
        except OSError as e:
            print(f"[-] Error reading file {self.file_path}: {str(e)}")

    def _process_line(self, line, line_num):
        """Process a single line from the input file."""
        # Remove whitespace
        line = line.strip()

        # Handle empty lines
        if not line:
            self.empty_count += 1
            return None

        # Handle comments based on configured comment style
        for marker in self.comment_markers:
            if line.startswith(marker):
                self.comment_count += 1
                return None

        # Handle inline comments based on configured comment style
        comment_pos = -1
        for marker in self.comment_markers:
            pos = line.find(marker)
            if pos > 0 and (comment_pos == -1 or pos < comment_pos):
                comment_pos = pos

        if comment_pos > 0:
            line = line[:comment_pos].strip()
            self.comment_count += 1

        # Skip if the line became empty after removing the comment
        if not line:
            self.empty_count += 1
            return None

        # Apply URL validation
        try:
            validated_url = url_validation(line)
            self.valid_count += 1
            return validated_url
        except argparse.ArgumentTypeError as e:
            error_msg = f"[-] Line {line_num}: {str(e)}"
            if self.verbose:
                print(error_msg)
            self.error_count += 1
            return None


class TLDManager:
    """Manager for TLD (Top-Level Domain) operations with caching and auto-updates.

    This class handles TLD validation against the Public Suffix List with:
    - Memory caching for better performance
    - Disk-based caching for persistence between runs
    - Automatic updates of the TLD list
    - Flexible configuration options
    """

    # Singleton instance
    _instance = None

    # Default TLD source URL from Public Suffix List
    TLD_SOURCE_URL = "https://publicsuffix.org/list/public_suffix_list.dat"

    # Default cache settings
    DEFAULT_CACHE_PATH = os.path.join(os.path.expanduser("~"), ".httpcheck")
    DEFAULT_CACHE_FILE = "tld_cache.pickle"
    DEFAULT_CACHE_DAYS = 30

    def __new__(cls, *args, **kwargs):
        """Ensure only one instance of TLDManager exists (singleton pattern)."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(
        self,
        force_update=False,
        cache_days=None,
        verbose=False,
        warning_only=False,
    ):
        """Initialize the TLD manager.

        Args:
            force_update: Whether to force an update of the TLD list
            cache_days: Number of days to keep the cache valid (default: 30)
            verbose: Whether to print verbose output
            warning_only: If True, invalid TLDs will produce warnings instead of errors
        """
        # Skip initialization if already initialized (singleton pattern)
        if self._initialized:
            return

        self.verbose = verbose
        self.warning_only = warning_only
        self.cache_days = cache_days or self.DEFAULT_CACHE_DAYS
        self.cache_path = self.DEFAULT_CACHE_PATH
        self.cache_file = os.path.join(self.cache_path, self.DEFAULT_CACHE_FILE)
        self.tlds = set()  # Use a set for O(1) lookups
        self.update_time = None

        # Ensure cache directory exists
        os.makedirs(self.cache_path, exist_ok=True)

        # Load TLD data with optional update
        self._load_tld_data(force_update)
        self._initialized = True

    def _load_tld_data(self, force_update=False):
        """Load TLD data from cache or source file."""
        # Check if we need to update based on cache age or forced update
        if force_update or not self._load_from_cache():
            try:
                self._update_tld_list()
            except Exception as e:
                if self.verbose:
                    print(f"[-] Error updating TLD list: {str(e)}")
                # If update fails and we don't have a cache, try to load from local file
                if not self.tlds:
                    self._load_from_local_file()

    def _load_from_cache(self):
        """Load TLD data from the cache file if it exists and is not expired."""
        try:
            if not os.path.exists(self.cache_file):
                return False

            # Check if cache is expired
            cache_age = datetime.now() - datetime.fromtimestamp(
                os.path.getmtime(self.cache_file)
            )
            if cache_age.days > self.cache_days:
                if self.verbose:
                    print(
                        f"[*] TLD cache is {cache_age.days} days old (max: {self.cache_days}). Refreshing..."
                    )
                return False

            # Load cache
            with open(self.cache_file, "rb") as f:
                cache_data = pickle.load(f)
                self.tlds = cache_data["tlds"]
                self.update_time = cache_data["update_time"]

            if self.verbose:
                print(
                    f"[*] Loaded {len(self.tlds)} TLDs from cache (last updated: {self.update_time})"
                )
            return True

        except (OSError, pickle.UnpicklingError, KeyError) as e:
            if self.verbose:
                print(f"[-] Error loading TLD cache: {str(e)}")
            return False

    def _save_to_cache(self):
        """Save TLD data to the cache file."""
        try:
            cache_data = {"tlds": self.tlds, "update_time": self.update_time}
            with open(self.cache_file, "wb") as f:
                pickle.dump(cache_data, f)

            if self.verbose:
                print(f"[*] Saved {len(self.tlds)} TLDs to cache")

        except (OSError, pickle.PicklingError) as e:
            if self.verbose:
                print(f"[-] Error saving TLD cache: {str(e)}")

    def _update_tld_list(self):
        """Update the TLD list from the Public Suffix List."""
        if self.verbose:
            print("[*] Updating TLD list from Public Suffix List...")

        try:
            # Use requests instead of urllib for better error handling and timeouts
            response = requests.get(self.TLD_SOURCE_URL, timeout=10)
            response.raise_for_status()  # Raise exception for HTTP errors

            # Process the TLD list
            tlds = set()
            for line in response.text.splitlines():
                line = line.strip()
                # Skip empty lines, comments, and private domains
                if not line or line.startswith("//") or line.startswith("*."):
                    continue
                tlds.add(line)

            # Update only if we got a non-empty list
            if tlds:
                self.tlds = tlds
                self.update_time = datetime.now()
                self._save_to_cache()

                if self.verbose:
                    print(f"[*] Updated TLD list with {len(self.tlds)} entries")
            else:
                raise ValueError("Downloaded TLD list is empty")

        except Exception as e:
            if self.verbose:
                print(f"[-] Failed to update TLD list: {str(e)}")
            raise

    def _load_from_local_file(self):
        """Fall back to loading TLDs from the local effective_tld_names.dat file."""
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            tld_file = os.path.join(script_dir, "effective_tld_names.dat")

            if not os.path.exists(tld_file):
                if self.verbose:
                    print(f"[-] Local TLD file not found: {tld_file}")
                return False

            tlds = set()
            with open(tld_file, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("//"):
                        tlds.add(line)

            self.tlds = tlds
            self.update_time = datetime.fromtimestamp(os.path.getmtime(tld_file))

            if self.verbose:
                print(
                    f"[*] Loaded {len(self.tlds)} TLDs from local file (last modified: {self.update_time})"
                )

            # Save to cache for future use
            self._save_to_cache()
            return True

        except Exception as e:
            if self.verbose:
                print(f"[-] Error loading local TLD file: {str(e)}")
            return False

    def validate_tld(self, url):
        """Validate that a URL has a valid top-level domain.

        Args:
            url: The URL to validate

        Returns:
            The valid TLD if found

        Raises:
            InvalidTLDException: If the TLD is invalid and warning_only is False
        """
        if not self.tlds:
            raise InvalidTLDException("TLD list is empty. Cannot validate TLDs.")

        parsed_url = urlparse(url)
        url_elements = parsed_url.netloc.split(".")

        for i in range(-len(url_elements), 0):
            last_i_elements = url_elements[i:]
            candidate = ".".join(last_i_elements)
            wildcard_candidate = ".".join(["*"] + last_i_elements[1:])
            exception_candidate = f"!{candidate}"

            if exception_candidate in self.tlds:
                return ".".join(url_elements[i:])
            if candidate in self.tlds or wildcard_candidate in self.tlds:
                return ".".join(url_elements[i - 1 :])

        error_msg = f"[-] Domain not in global list of TLDs: '{url}'"
        if self.warning_only:
            if self.verbose:
                print(f"[!] WARNING: {error_msg}")
            return None
        else:
            raise InvalidTLDException(error_msg)


def main():
    """Check websites central."""
    options = get_arguments()
    start_time = datetime.now()
    total_sites = len(options.site)
    successful = 0
    failures = 0
    failed_sites = []

    if options.verbose:
        now = datetime.now()
        date_stamp = now.strftime("%d/%m/%Y %H:%M:%S")
        print(f"\thttpcheck {date_stamp}:")

    # Process sites from stdin if no arguments given
    if not options.site:
        if not sys.stdin.isatty():
            options.site = [line.strip() for line in sys.stdin if line.strip()]
        else:
            parser = argparse.ArgumentParser()
            parser.error(
                "[-] Please specify a website or a file with sites to check, "
                "use --help for more info."
            )

    failures = check_tlds(options, failures, failed_sites)

    if not options.fast:
        successful, failures = check_sites_serial(
            options, successful, failures, failed_sites
        )
    else:
        successful, failures = check_sites_parallel(
            options, successful, failures, failed_sites
        )

    # Send completion notification
    duration = datetime.now() - start_time
    summary = (
        f"Checked {total_sites} sites in {duration.seconds}s\n"
        f"{successful} successful, {failures} failed"
    )
    print(f"\n{summary}")

    if failures > 0:
        notify(
            "HTTP Check - Failed",
            f"{failures} of {total_sites} sites failed",
            failed_sites,
        )
    else:
        notify(
            "HTTP Check - Success",
            f"All {total_sites} sites checked successfully",
        )


if __name__ == "__main__":
    main()
