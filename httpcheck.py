#!/usr/bin/env python3
"""Simple command line program to check website status.

Author: Thomas Juul Dyhr thomas@dyhr.com
Purpose: Check one or more websites status
Release date: 27 April 2025
Version: 1.3.1
"""

import argparse
import concurrent.futures
import sys
import textwrap
from datetime import datetime
from urllib.parse import urlparse

from tqdm import tqdm

# Import from local modules
from httpcheck.common import VERSION, InvalidTLDException, SiteStatus
from httpcheck.file_handler import FileInputHandler, url_validation
from httpcheck.notification import notify
from httpcheck.output_formatter import print_format
from httpcheck.site_checker import check_site
from httpcheck.tld_manager import TLDManager


def get_arguments():
    """Handle website arguments."""
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

    # Redirect handling options
    parser.add_argument(
        "--follow-redirects",
        dest="follow_redirects",
        choices=["always", "never", "http-only", "https-only"],
        default="always",
        help="control redirect following behavior (default: always)",
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
        help="show timing information for each redirect step",
    )

    # Output mode options (mutually exclusive)
    output_group = parser.add_mutually_exclusive_group()
    output_group.add_argument(
        "-q", "--quiet", action="store_true", help="only print errors"
    )
    output_group.add_argument(
        "-v", "--verbose", action="store_true", help="increase output verbosity"
    )
    output_group.add_argument(
        "-c", "--code", action="store_true", help="only print status code"
    )
    output_group.add_argument(
        "-f", "--fast", action="store_true", help="fast check with threading"
    )

    parser.add_argument(
        "--version", action="version", version=f"httpcheck.py {VERSION}"
    )

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
            try:
                status = check_site(
                    site,
                    timeout=options.timeout,
                    retries=options.retries,
                    follow_redirects=options.follow_redirects,
                    max_redirects=options.max_redirects,
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
            except Exception as e:
                error_msg = f"[-] {site}: {str(e)}"
                results.append(error_msg)
                failures += 1
                failed_sites.append(f"{urlparse(site).hostname} (Error)")
            pbar.update(1)

    # Print results after progress bar is done
    print("\n".join(filter(None, results)))
    return successful, failures


def check_sites_parallel(options, successful, failures, failed_sites):
    """Check sites in parallel using threading."""
    results = []
    with tqdm(
        total=len(options.site),
        desc="Checking sites",
        disable=options.quiet,
        position=0,
        leave=True,
    ) as pbar:
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=options.workers
        ) as executor:
            # Submit all tasks
            future_to_site = {
                executor.submit(
                    check_site,
                    site,
                    timeout=options.timeout,
                    retries=options.retries,
                    follow_redirects=options.follow_redirects,
                    max_redirects=options.max_redirects,
                ): site
                for site in options.site
            }

            # Process completed futures
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
                except Exception as e:
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
