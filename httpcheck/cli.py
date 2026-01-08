"""Command-line interface for httpcheck.

This module provides the main CLI entry point for the httpcheck package.
All CLI logic is centralized here for proper package integration.
"""

import argparse
import concurrent.futures
import sys
import textwrap
from datetime import datetime
from urllib.parse import urlparse

from tqdm import tqdm

# Import from local modules
from .common import VERSION, InvalidTLDException, SiteStatus, parse_custom_headers
from .file_handler import FileInputHandler, url_validation
from .logger import get_logger, setup_logger
from .notification import notify
from .output_formatter import format_csv_list, format_json_list, print_format
from .site_checker import check_site
from .tld_manager import TLDManager

# CLI docstring for help text
CLI_DOC = """Simple command line program to check website status.

Author: Thomas Juul Dyhr thomas@dyhr.com
Purpose: Check one or more websites status
Version: 1.4.1
"""


def _create_argument_parser():
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent(CLI_DOC),
    )

    # Basic site argument
    parser.add_argument(
        "site",
        nargs="*",
        type=str,
        help="return http status codes for one or more websites",
    )

    # TLD validation options
    _add_tld_arguments(parser)

    # Request timing and retry options
    _add_request_arguments(parser)

    # File input handling options
    _add_file_arguments(parser)

    # Redirect handling options
    _add_redirect_arguments(parser)

    # Request customization options
    _add_request_customization_arguments(parser)

    # Output options
    _add_output_arguments(parser)

    parser.add_argument("--version", action="version", version=f"httpcheck {VERSION}")

    return parser


def _add_tld_arguments(parser):
    """Add TLD-related arguments to parser."""
    parser.add_argument(
        "-t",
        "--tld",
        action="store_true",
        dest="tld",
        help="check if domain is in global list of TLDs",
    )
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


def _add_request_arguments(parser):
    """Add request timing and retry arguments to parser."""
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
    parser.add_argument(
        "--retry-delay",
        type=float,
        default=1.0,
        help="delay in seconds between retry attempts (default: 1.0)",
    )


def _add_file_arguments(parser):
    """Add file input handling arguments to parser."""
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


def _add_redirect_arguments(parser):
    """Add redirect handling arguments to parser."""
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


def _add_request_customization_arguments(parser):
    """Add request customization arguments to parser."""
    parser.add_argument(
        "-H",
        "--header",
        action="append",
        dest="headers",
        metavar="HEADER",
        help="add custom HTTP header (can be used multiple times)",
    )
    parser.add_argument(
        "--no-verify-ssl",
        dest="verify_ssl",
        action="store_false",
        default=True,
        help="disable SSL certificate verification",
    )


def _add_output_arguments(parser):
    """Add output format and mode arguments to parser."""
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

    # Output format options
    parser.add_argument(
        "--output",
        dest="output_format",
        choices=["table", "json", "csv"],
        default="table",
        help="output format: table (default), json, or csv",
    )

    # Logging options
    parser.add_argument(
        "--debug",
        action="store_true",
        help="enable debug logging",
    )
    parser.add_argument(
        "--log-file",
        dest="log_file",
        type=str,
        help="write logs to file",
    )
    parser.add_argument(
        "--log-json",
        dest="log_json",
        action="store_true",
        help="output logs in JSON format",
    )


def _process_file_input(site, options):
    """Process file input with @ prefix."""
    try:
        handler = FileInputHandler(
            site[1:],
            verbose=options.file_summary or options.verbose,
            comment_style=options.comment_style,
        )
        return list(handler.parse())
    except Exception as e:
        logger = get_logger()
        logger.error("Error processing file %s: %s", site[1:], str(e))
        return []


def _process_stdin_input():
    """Process input from stdin."""
    logger = get_logger()
    validated_sites = []
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
                    logger.error(str(e))
    return validated_sites


def _validate_sites(sites):
    """Validate individual site URLs."""
    logger = get_logger()
    validated_sites = []
    for site in sites:
        if site.startswith("@"):
            continue  # Handled separately
        try:
            validated_url = url_validation(site)
            validated_sites.append(validated_url)
        except argparse.ArgumentTypeError as e:
            logger.error(str(e))
    return validated_sites


def get_arguments():
    """Handle website arguments."""
    parser = _create_argument_parser()
    options = parser.parse_args()

    # Setup logging based on options
    import logging

    log_level = logging.DEBUG if options.debug else logging.INFO
    setup_logger(
        level=log_level,
        log_file=options.log_file,
        json_format=options.log_json,
        quiet=options.quiet,
    )
    logger = get_logger()

    # Warn about SSL verification
    if not options.verify_ssl:
        logger.warning("SSL certificate verification is disabled!")

    # Process all inputs
    validated_sites = []

    # Handle file inputs
    for site in options.site:
        if site.startswith("@"):
            validated_sites.extend(_process_file_input(site, options))

    # Handle regular URL arguments
    validated_sites.extend(_validate_sites(options.site))

    # Handle stdin if no sites provided
    if not validated_sites and not sys.stdin.isatty():
        validated_sites.extend(_process_stdin_input())

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
    site_statuses = []
    custom_headers = parse_custom_headers(options.headers)
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
                    custom_headers=custom_headers,
                    verify_ssl=options.verify_ssl,
                    retry_delay=options.retry_delay,
                )
                site_statuses.append(status)

                # Only format for table output
                if options.output_format == "table":
                    formatted_output = print_format(
                        status,
                        options.quiet,
                        options.verbose,
                        options.code,
                        show_redirect_timing=options.show_redirect_timing,
                        output_format=options.output_format,
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

    # Print results after progress bar is done (output to stdout, not logger)
    if options.output_format == "json":
        print(format_json_list(site_statuses, options.verbose))
    elif options.output_format == "csv":
        print(format_csv_list(site_statuses, options.verbose))
    else:
        print("\n".join(filter(None, results)))
    return successful, failures


def check_sites_parallel(options, successful, failures, failed_sites):
    """Check sites in parallel using threading."""
    results = []
    site_statuses = []
    custom_headers = parse_custom_headers(options.headers)
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
                    custom_headers=custom_headers,
                    verify_ssl=options.verify_ssl,
                    retry_delay=options.retry_delay,
                ): site
                for site in options.site
            }

            # Process completed futures
            for future in concurrent.futures.as_completed(future_to_site):
                site = future_to_site[future]
                try:
                    status = future.result()
                    site_statuses.append(status)

                    # Only format for table output
                    if options.output_format == "table":
                        formatted_output = print_format(
                            status,
                            options.quiet,
                            options.verbose,
                            options.code,
                            show_redirect_timing=options.show_redirect_timing,
                            output_format=options.output_format,
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

    # Print results after progress bar is done (output to stdout, not logger)
    if options.output_format == "json":
        print(format_json_list(site_statuses, options.verbose))
    elif options.output_format == "csv":
        print(format_csv_list(site_statuses, options.verbose))
    else:
        print("\n".join(filter(None, results)))
    return successful, failures


def check_tlds(options, failures, failed_sites):
    """Check TLDs if requested."""
    logger = get_logger()

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
                logger.error(str(e))
                failures += 1
                failed_sites.append(f"{urlparse(site).hostname} (Invalid TLD)")

    except Exception as e:
        if options.verbose:
            logger.error("Error during TLD validation: %s", str(e))

    return failures


def _print_verbose_header():
    """Print verbose header with timestamp."""
    logger = get_logger()
    now = datetime.now()
    date_stamp = now.strftime("%d/%m/%Y %H:%M:%S")
    logger.info("\thttpcheck %s:", date_stamp)


def _handle_stdin_input(options):
    """Handle input from stdin if no arguments given."""
    if not options.site:
        if not sys.stdin.isatty():
            options.site = [line.strip() for line in sys.stdin if line.strip()]
        else:
            parser = argparse.ArgumentParser()
            parser.error(
                "[-] Please specify a website or a file with sites to check, "
                "use --help for more info."
            )


def _process_sites(options, successful, failures, failed_sites):
    """Process sites either serially or in parallel."""
    if not options.fast:
        return check_sites_serial(options, successful, failures, failed_sites)
    else:
        return check_sites_parallel(options, successful, failures, failed_sites)


def _send_completion_notification(total_sites, successful, failures, failed_sites):
    """Send notification about completion status."""
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


def main():
    """Main CLI entry point for httpcheck."""
    options = get_arguments()
    logger = get_logger()
    start_time = datetime.now()
    total_sites = len(options.site)
    successful = 0
    failures = 0
    failed_sites = []

    logger.debug("Starting httpcheck with %d sites", total_sites)

    if options.verbose:
        _print_verbose_header()

    _handle_stdin_input(options)
    failures = check_tlds(options, failures, failed_sites)
    successful, failures = _process_sites(options, successful, failures, failed_sites)

    # Send completion notification
    duration = datetime.now() - start_time
    summary = (
        f"Checked {total_sites} sites in {duration.seconds}s\n"
        f"{successful} successful, {failures} failed"
    )

    logger.debug("Completed in %s seconds", duration.seconds)

    # Only print summary for table format
    if options.output_format == "table":
        print(f"\n{summary}")

    _send_completion_notification(total_sites, successful, failures, failed_sites)
