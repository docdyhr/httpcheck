#!/usr/bin/env python3

"""Simple command line program to check website status.

Author: Thomas Juul Dyhr thomas@dyhr.com
Purpose: Check one or more websites status
Release date: 19. Marts 2024
Version: 1.2.1

"""

from __future__ import with_statement

import os
import argparse
import concurrent.futures
import json
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


# TODO:
# option -r for checking only redirects with redirects site info
# add support for piping into httpcheck, see argpase  - 'FileType objects'
# stdin
# add support for 'Customizing file parsing' to allow /remove empty lines with
# withe space to occur
#
def get_arguments():
    """Handle webiste arguments."""
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent(__doc__))
    parser.add_argument(
        'site',
        nargs='*',
        type=str,  # Changed from url_validation to str to handle validation later
        help='return http status codes for one or more websites')
    parser.add_argument(
        '-t',
        '--tld',
        action='store_true',
        dest='tld',
        help='check if domain is in global list of TLDs')
    parser.add_argument(
        '--timeout',
        type=float,
        default=5.0,
        help='timeout in seconds for each request')
    parser.add_argument(
        '--retries',
        type=int,
        default=2,
        help='number of retries for failed requests')
    parser.add_argument(
        '--workers',
        type=int,
        default=10,
        help='number of concurrent workers for fast mode')
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        '-q',
        '--quiet',
        action='store_true',  # flag only no args stores True / False value
        dest='quiet',
        help='only print errors')
    group.add_argument(
        '-v',
        '--verbose',
        action='store_true',  # flag only no args stores True / False value
        dest='verbose',
        help='increase output verbosity')
    group.add_argument(
        '-c',
        '--code',
        action='store_true',  # flag only no args stores True / False value
        dest='code',
        help='only print status code')
    group.add_argument(
        '-f',
        '--fast',
        action='store_true',  # flag only no args stores True / False value
        dest='fast',
        help='fast check wtih threading')
    parser.add_argument(
        '--version',
        action='version',
        version=f'%(prog)s {VERSION}')
    
    options = parser.parse_args()
    
    # Handle stdin if no sites provided
    if not options.site and not sys.stdin.isatty():
        stdin_sites = []
        for line in sys.stdin:
            line = line.strip()
            if line:
                try:
                    validated_url = url_validation(line)
                    stdin_sites.append(validated_url)
                except argparse.ArgumentTypeError as e:
                    print(str(e))
        if stdin_sites:
            options.site = stdin_sites
        else:
            parser.error("[-] No valid URLs provided via stdin")
    elif not options.site:
        parser.error("[-] Please specify a website or pipe URLs to check, use --help for more info.")
    else:
        # Validate command-line arguments
        validated_sites = []
        for site in options.site:
            try:
                validated_url = url_validation(site)
                validated_sites.append(validated_url)
            except argparse.ArgumentTypeError as e:
                print(str(e))
        options.site = validated_sites
        if not options.site:
            parser.error("[-] No valid URLs provided")
    
    return options


def url_validation(site_url):
    """Validate website from user."""
    # TODO: catch empty lines from @file
    # Find a more concise yet libral version of regex domain see
    # https://bit.ly/2FZLvHR
    #
    # conversion of 'no' url to url
    site_url = site_url if site_url.startswith(
        'http') else f'http://{site_url}'
    # check url with regex
    regex = re.compile(
        r'^(?:http|ftp)s?://'  # http:// or https://
        #  domain
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)

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

    url_elements = urlparse(url).netloc.split('.')
    for i in range(-len(url_elements), 0):
        last_i_elements = url_elements[i:]
        candidate = ".".join(last_i_elements)
        wildcard_candidate = ".".join(["*"] + last_i_elements[1:])
        exception_candidate = f"!{candidate}"

        if exception_candidate in tlds:
            return ".".join(url_elements[i:])
        if candidate in tlds or wildcard_candidate in tlds:
            return ".".join(url_elements[i - 1:])

    raise InvalidTLDException(f"[-] Domain not in global list of TLDs: '{url}'")

class SiteStatus(NamedTuple):
    """Represents the status of a checked website"""
    domain: str
    status: str
    message: str
    redirect_chain: List[tuple] = []
    response_time: float = 0.0

def check_site(site, timeout=5.0, retries=2):
    """Check website status code with redirect tracking."""
    custom_header = {'User-Agent': f'httpcheck Agent {VERSION}'}
    redirect_chain = []
    start_time = datetime.now()
    
    for attempt in range(retries + 1):
        try:
            response = requests.get(site, headers=custom_header, timeout=timeout, allow_redirects=True)
            end_time = datetime.now()
            response_time = (end_time - start_time).total_seconds()
            
            # Track redirects
            if response.history:
                for r in response.history:
                    redirect_chain.append((r.url, r.status_code))
                redirect_chain.append((response.url, response.status_code))
            
            return SiteStatus(
                domain=urlparse(site).hostname,
                status=str(response.status_code),
                message=STATUS_CODES.get(str(response.status_code), "Unknown"),
                redirect_chain=redirect_chain,
                response_time=response_time
            )
        except Timeout:
            if attempt == retries:
                return SiteStatus(urlparse(site).hostname, '[timeout]', 'Request timed out')
        except RequestsConnectionError:
            if attempt == retries:
                return SiteStatus(urlparse(site).hostname, '[connection error]', 'Connection failed')
        except HTTPError as e:
            return SiteStatus(urlparse(site).hostname, str(e.response.status_code), str(e))
        except RequestException:
            if attempt == retries:
                return SiteStatus(urlparse(site).hostname, '[request error]', 'Request failed')

def print_format(result: SiteStatus, quiet: bool, verbose: bool, code: bool):
    """Format & print results in columns."""
    if code:
        print(result.status)
        return
        
    if verbose:
        headers = ["Domain", "Status", "Response Time", "Message"]
        table_data = [[
            result.domain,
            result.status,
            f"{result.response_time:.2f}s",
            STATUS_CODES.get(str(result.status), "Unknown")
        ]]
        
        print(tabulate(table_data, headers=headers, tablefmt="grid"))
        
        if result.redirect_chain:
            print("\nRedirect Chain:")
            redirect_data = [[i+1, url, code] for i, (url, code) in enumerate(result.redirect_chain)]
            print(tabulate(redirect_data, headers=["Step", "URL", "Status"], tablefmt="grid"))
            print()
    elif quiet:
        if result.status in ('[timeout]', '[connection error]') or int(result.status) >= 400:
            print(f'{result.domain} {result.status}')
    else:
        print(tabulate([[result.domain, result.status]], tablefmt="simple"))

def notify(title, message, failed_sites=None):
    """Send system notification using terminal-notifier."""
    if platform.system() == 'Darwin':  # macOS only
        try:
            notifier_paths = [
                '/opt/homebrew/bin/terminal-notifier',  # Apple Silicon
                '/usr/local/bin/terminal-notifier'      # Intel Mac
            ]
            
            notifier_path = next((path for path in notifier_paths if os.path.exists(path)), None)
            
            if not notifier_path:
                print("\nWarning: terminal-notifier not found. Please install it with: brew install terminal-notifier")
                return

            notification_message = message
            if failed_sites and len(failed_sites) < 10:
                failed_list = "\n".join(f"• {site}" for site in failed_sites)
                notification_message = f"{message}\n\nFailed sites:\n{failed_list}"

            cmd = [
                notifier_path,
                '-title', title,
                '-message', notification_message,
                '-group', 'httpcheck'
            ]

            subprocess.run(cmd, check=False)

        except subprocess.SubprocessError as e:
            print(f"\nWarning: Could not send notification: {str(e)}")
            print("Please ensure terminal-notifier is installed: brew install terminal-notifier")

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
        print(f'\thttpcheck {date_stamp}:')

    # Process sites from stdin if no arguments given
    if not options.site:
        if not sys.stdin.isatty():
            options.site = [line.strip() for line in sys.stdin if line.strip()]
        else:
            parser = argparse.ArgumentParser()  # Create parser instance here
            parser.error("[-] Please specify a website or a file with sites to check, use --help for more info.")

    if options.tld:
        tld_file = "effective_tld_names.dat.txt"  # Default TLD file
        for site in options.site:
            try:
                tld_check(site, tld_file)
            except InvalidTLDException as e:
                print(str(e))
                failures += 1
                failed_sites.append(f"{urlparse(site).hostname} (Invalid TLD)")
                continue

    if not options.fast:
        for site in tqdm(options.site, desc="Checking sites", disable=options.quiet):
            status = check_site(site, options.timeout, options.retries)
            print_format(status, options.quiet, options.verbose, options.code)
            if isinstance(status, SiteStatus):
                try:
                    status_code = int(status.status)
                    if 200 <= status_code < 400:
                        successful += 1
                    else:
                        failures += 1
                        failed_sites.append(f"{status.domain} ({status.status})")
                except ValueError:
                    failures += 1
                    failed_sites.append(f"{status.domain} ({status.status})")
            else:
                failures += 1
                failed_sites.append(f"{urlparse(site).hostname} (Error)")
    else:
        with concurrent.futures.ThreadPoolExecutor(max_workers=options.workers) as executor:
            future_to_site = {executor.submit(check_site, site, options.timeout, options.retries): site 
                            for site in options.site}
            
            with tqdm(total=len(future_to_site), desc="Checking sites", disable=options.quiet) as pbar:
                for future in concurrent.futures.as_completed(future_to_site):
                    site = future_to_site[future]
                    try:
                        status = future.result()
                        print_format(status, options.quiet, options.verbose, options.code)
                        if isinstance(status, SiteStatus):
                            try:
                                status_code = int(status.status)
                                if 200 <= status_code < 400:
                                    successful += 1
                                else:
                                    failures += 1
                                    failed_sites.append(f"{status.domain} ({status.status})")
                            except ValueError:
                                failures += 1
                                failed_sites.append(f"{status.domain} ({status.status})")
                        else:
                            failures += 1
                            failed_sites.append(f"{urlparse(site).hostname} (Error)")
                    except (RequestException, RuntimeError) as e:
                        print(f"[-] {site}: {str(e)}")
                        failures += 1
                        failed_sites.append(f"{urlparse(site).hostname} (Error)")
                    pbar.update(1)

    # Send completion notification
    duration = datetime.now() - start_time
    summary = f"Checked {total_sites} sites in {duration.seconds}s\n{successful} successful, {failures} failed"
    print(f"\n{summary}")
    
    if failures > 0:
        notify("HTTP Check - Failed", f"{failures} of {total_sites} sites failed", failed_sites)
    else:
        notify("HTTP Check - Success", f"All {total_sites} sites checked successfully")


if __name__ == '__main__':
    main()
