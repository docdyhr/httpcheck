"""Common utilities and constants for httpcheck."""

import json
from typing import NamedTuple

VERSION = "1.4.2"

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

    @property
    def final_url(self) -> str:
        """Return the final URL after redirects, or construct from domain."""
        if self.redirect_chain:
            return self.redirect_chain[-1][0]
        # Construct URL from domain (prefer HTTPS)
        if not self.domain.startswith(("http://", "https://")):
            return f"https://{self.domain}"
        return self.domain


class InvalidTLDException(Exception):
    """Raised when a domain has an invalid TLD."""


def parse_custom_headers(headers_list):
    """Parse custom headers from command line with enhanced validation.

    Args:
        headers_list: List of header strings in format "Name: Value"

    Returns:
        Dictionary of headers
    """
    if not headers_list:
        return None

    # Import here to avoid circular imports
    from .validation import HeaderValidationError, InputValidator

    validator = InputValidator()

    try:
        return validator.validate_http_headers(headers_list)
    except HeaderValidationError as e:
        print(f"Warning: Header validation failed - {e}")

        # Fallback to basic parsing for backward compatibility
        headers_dict = {}
        for header in headers_list:
            if ":" not in header:
                print(f"Warning: Invalid header format '{header}'. Use 'Name: Value'")
                continue
            name, value = header.split(":", 1)

            # Basic sanitization
            name = name.strip()
            value = value.strip()

            if name and value:
                headers_dict[name] = value

        return headers_dict if headers_dict else None
