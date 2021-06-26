#!/usr/bin/env python3

"""Simple command line program to check website status.

Author: Thomas Juul Dyhr thomas@dyhr.com
Purpose: Check one or more websites status
Release date: 15. Mai 2020
Version: 1.1.0

"""

from __future__ import with_statement
from datetime import datetime
from urllib.parse import urlparse
# from requests.exceptions import HTTPError
import argparse
import json
import re
import textwrap
import concurrent.futures
import requests


VERSION = "1.1.0"

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
        # epilog=f'List of HTTP status codes: {INFO}',
        fromfile_prefix_chars='@',  # read arguments from file ex. @domains.txt
        # argument_default=argparse.SUPPRESS,
        # description='%(prog)s @filename to read websites from a file',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent('''\
         additional information:
           enter sites in url or 'no' url form: '%(prog)s duckduckgo.com'
           read sites from a file: '%(prog)s @domains.txt'

           [List of HTTP status codes](https://en.wikipedia.org/wiki/List_of_HTTP_status_codes)
         '''))
    parser.add_argument(
        'site',
        type=url_validation,  # Input validation with url_validation()
        action='store',
        nargs='*',  # flexible number of values - incl. None / see parser.error
        help="return http status codes for one or more websites")
    parser.add_argument(
        '-t',
        '--tld',
        action='store_true',  # flag only no args stores True / False value
        dest='tld',
        help='check if domain is in global list of TLDs')
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
    if not options.site:
        parser.error(
            "[-] Please specify a website or a file with sites to check,"
            "use --help for more info.")
    # print(f'DEBUG: {vars(options) = }')

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


# TODO: Fix function call and exceptions handling
def tld_check(url):
    """Check url for valid TLD against tld file."""
    # load tlds, ignore comments and empty lines:
    # https://github.com/barseghyanartur/tld/blob/master/src/tld/res/effective_tld_names.dat.txt
    with open("effective_tld_names.dat.txt") as tld_file:
        tlds = [line.strip() for line in tld_file if line[0] not in "/\n"]

        url_elements = urlparse(url)[1].split('.')
    # url_elements = ["abcde","co","uk"]

    for i in range(-len(url_elements), 0):
        last_i_elements = url_elements[i:]
        #    i=-3: ["abcde","co","uk"]
        #    i=-2: ["co","uk"]
        #    i=-1: ["uk"] etc

        candidate = ".".join(last_i_elements)  # abcde.co.uk, co.uk, uk
        wildcard_candidate = ".".join(["*"] + last_i_elements[1:])  # *.co.uk
        exception_candidate = "!" + candidate

        # match tlds:
        if exception_candidate in tlds:
            return ".".join(url_elements[i:])
        if (candidate in tlds or wildcard_candidate in tlds):
            return ".".join(url_elements[i - 1:])
            # returns "abcde.co.uk"

    msg = f"[-] Domain not in global list of TLDs: '{url}'"
    raise argparse.ArgumentTypeError(msg)


def check_site(site):
    """Check webiste status code."""
    # Include headers in request to avoid false 406 positives
    custom_header = {'User-Agent': f'httpcheck Agent {VERSION}'}

    try:
        # Returns a response object
        response = requests.get(site, headers=custom_header, timeout=5)
        return response.status_code

    except requests.exceptions.Timeout:
        return '[timeout]'
    except requests.exceptions.ConnectionError:
        return '[connection error]'


# TODO:
# consider the most intuitive way to deliver different result(s)
# how to format multiline output in columns in python 3?
def print_format(status, url, quiet, verbose, code):
    """Format & print results."""
    status_codes = json.loads(STATUS_CODES_JSON)  # get staus codes from above
    # Get domain name with urlparse
    domain_parser = urlparse(url)
    domain = domain_parser.hostname

    if verbose and status in ('[timeout]', '[connection error]'):
        print(f'[-] {domain} -->  {status} Error')
    elif verbose:
        if 100 <= status < 200:
            print(f'[+] {domain} --> Info: {status} '
                  f'{status_codes.get(str(status))}')
        elif 200 <= status < 300:
            print(f'[+] {domain} --> Succes: {status} '
                  f'{status_codes.get(str(status))}')
        elif 300 <= status < 400:
            print(f'[-] {domain} --> Redirection: {status} '
                  f'{status_codes.get(str(status))}')
        elif 400 <= status < 500:
            print(f'[-] {domain} --> Client errors: {status} '
                  f'{status_codes.get(str(status))}')
        elif 500 <= status < 600:
            print(f'[-] {domain} --> Server errors: {status} '
                  f'{status_codes.get(str(status))}')
        else:
            print(f"[-] unknown error for {domain}")
    elif code:
        print(f'{status}')
    elif quiet:
        if status in ('[timeout]', '[connection error]') or status >= 400:
            print(f'{domain} {status}')
    else:
        print(f'{domain} {status}')


def main():
    """Check websites central."""
    options = get_arguments()  # Get arguments
    # print(f'DEBUG: {vars(options)}')  # DEBUG: Print arguments
    if options.tld:
        for site in options.site:
            tld_check(site)

    if options.verbose:
        now = datetime.now()
        date_stamp = now.strftime("%d/%m/%Y %H:%M:%S")
        print(f'\thttpcheck {date_stamp}:')
    if not options.fast:
        for site in options.site:
            # if options.tld:
            #     tld_check(site)
            status = check_site(site)  # Check & get HTTP Status code
            print_format(status, site, options.quiet,
                         options.verbose, options.code)
    # TODO:
    # Fix Concurrency feature executor to show site with result
    # Problem Concurrency does not deliver results sequentially
    # Ref.: https://rednafi.github.io/digressions/python/2020/04/21/python-concurrent-futures.html
    else:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            results = executor.map(check_site, options.site)
        for result in results:
            print(f'{result}')  # Print exhausts items in map ie. next item
        # print(list(results))


if __name__ == '__main__':
    main()
