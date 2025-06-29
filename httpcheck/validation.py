"""Comprehensive input validation for httpcheck.

This module provides robust validation for all types of input to the httpcheck
application, including URLs, file inputs, HTTP headers, and command-line arguments.
It focuses on security, data integrity, and user experience.
"""

import ipaddress
import os
import re
from pathlib import Path
from typing import Optional, Union
from urllib.parse import urlparse, urlunparse


class ValidationError(Exception):
    """Base class for validation errors."""


class URLValidationError(ValidationError):
    """Raised when URL validation fails."""


class FileValidationError(ValidationError):
    """Raised when file validation fails."""


class HeaderValidationError(ValidationError):
    """Raised when HTTP header validation fails."""


class ArgumentValidationError(ValidationError):
    """Raised when command-line argument validation fails."""


class InputValidator:
    """Comprehensive input validation for httpcheck."""

    # Security patterns to detect potential attacks
    INJECTION_PATTERNS = [
        r"<script[^>]*>.*?</script>",  # XSS attempts
        r"<script[^>]*>",  # Script tags
        r"<img[^>]*onerror[^>]*>",  # Image XSS
        r"<iframe[^>]*>",  # Iframe injection
        r"<object[^>]*>",  # Object injection
        r"<embed[^>]*>",  # Embed injection
        r"javascript:",  # JavaScript protocol
        r"data:",  # Data URLs
        r"file:",  # File protocol
        r"[;&|`$]",  # Shell injection characters
        r"\.\./",  # Path traversal
        r"%2e%2e%2f",  # URL encoded path traversal
        r"%2e%2e/",  # URL encoded path traversal variant
        r"\.\.\\",  # Windows path traversal
        r"null",  # Null byte injection
        r"\x00",  # Null byte
        r"on\w+\s*=",  # Event handlers (onclick, onload, etc.)
    ]

    # Valid URL schemes
    ALLOWED_SCHEMES = {"http", "https", "ftp"}

    # Valid HTTP methods
    VALID_HTTP_METHODS = {
        "GET",
        "POST",
        "PUT",
        "DELETE",
        "HEAD",
        "OPTIONS",
        "PATCH",
        "TRACE",
    }

    # Maximum limits for security
    MAX_URL_LENGTH = 2048
    MAX_DOMAIN_LENGTH = 253
    MAX_HEADER_LENGTH = 8192
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    MAX_LINES_IN_FILE = 100000
    MAX_HEADER_COUNT = 50

    # Valid TLD patterns (basic validation)
    TLD_PATTERN = re.compile(r"^[A-Za-z]{2,}$")

    # Domain validation regex - more comprehensive than original
    DOMAIN_PATTERN = re.compile(
        r"^(?:[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?\.)*"
        r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?$"
    )

    # IP address validation
    IPV4_PATTERN = re.compile(
        r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}"
        r"(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
    )

    # Port validation
    PORT_PATTERN = re.compile(r"^[1-9][0-9]{0,4}$")

    def __init__(self, strict_mode: bool = False):
        """Initialize validator with optional strict mode.

        Args:
            strict_mode: If True, applies stricter validation rules
        """
        self.strict_mode = strict_mode
        self.compiled_injection_patterns = [
            re.compile(pattern, re.IGNORECASE) for pattern in self.INJECTION_PATTERNS
        ]

    def validate_url(self, url: str, auto_fix: bool = True) -> str:
        """Validate and sanitize a URL.

        Args:
            url: The URL to validate
            auto_fix: If True, attempts to fix common URL issues

        Returns:
            Validated and potentially fixed URL

        Raises:
            URLValidationError: If URL is invalid
        """
        url = self._preprocess_url(url, auto_fix)
        parsed = self._parse_url(url)
        self._validate_url_components(parsed)
        return urlunparse(parsed)

    def _preprocess_url(self, url: str, auto_fix: bool) -> str:
        """Preprocess URL before parsing."""
        if not url or not isinstance(url, str):
            raise URLValidationError("URL must be a non-empty string")

        url = url.strip()
        self._check_for_injection(url)

        if len(url) > self.MAX_URL_LENGTH:
            raise URLValidationError(
                f"URL too long (max {self.MAX_URL_LENGTH} characters)"
            )

        if auto_fix and not url.startswith(("http://", "https://", "ftp://")):
            url = f"http://{url}"

        return url

    def _parse_url(self, url: str):
        """Parse URL and validate scheme."""
        try:
            parsed = urlparse(url)
        except Exception as e:
            raise URLValidationError(f"Invalid URL format: {e}") from e

        if parsed.scheme.lower() not in self.ALLOWED_SCHEMES:
            if self.strict_mode:
                raise URLValidationError(f"Unsupported scheme: {parsed.scheme}")
            if not parsed.scheme:
                parsed = parsed._replace(scheme="http")

        return parsed

    def _validate_url_components(self, parsed):
        """Validate hostname and port components."""
        if not parsed.hostname:
            raise URLValidationError("URL must contain a hostname")

        hostname = parsed.hostname.lower()

        if len(hostname) > self.MAX_DOMAIN_LENGTH:
            raise URLValidationError(
                f"Domain name too long (max {self.MAX_DOMAIN_LENGTH} characters)"
            )

        if not self._is_valid_hostname(hostname):
            raise URLValidationError(f"Invalid hostname: {hostname}")

        try:
            if parsed.port is not None:
                if not 1 <= parsed.port <= 65535:
                    raise URLValidationError(f"Invalid port: {parsed.port}")
        except ValueError as e:
            raise URLValidationError(f"Invalid port in URL: {e}") from e

    def validate_file_input(self, file_path: str) -> None:
        """Validate file input for security and accessibility.

        Args:
            file_path: Path to the file to validate

        Raises:
            FileValidationError: If file validation fails
        """
        if not file_path or not isinstance(file_path, str):
            raise FileValidationError("File path must be a non-empty string")

        # Check for path traversal attempts
        self._check_for_injection(file_path)

        # Normalize path
        try:
            path = Path(file_path).resolve()
        except Exception as e:
            raise FileValidationError(f"Invalid file path: {e}") from e

        # Check if file exists
        if not path.exists():
            raise FileValidationError(f"File not found: {file_path}")

        # Check if it's actually a file
        if not path.is_file():
            raise FileValidationError(f"Path is not a file: {file_path}")

        # Check file size
        try:
            file_size = path.stat().st_size
            if file_size > self.MAX_FILE_SIZE:
                raise FileValidationError(
                    f"File too large: {file_size} bytes (max {self.MAX_FILE_SIZE})"
                )
        except OSError as e:
            raise FileValidationError(f"Cannot access file: {e}") from e

        # Check file permissions
        if not os.access(path, os.R_OK):
            raise FileValidationError(f"File is not readable: {file_path}")

        # In strict mode, check file extension
        if self.strict_mode:
            allowed_extensions = {".txt", ".list", ".domains", ".urls"}
            if path.suffix.lower() not in allowed_extensions:
                raise FileValidationError(f"File extension not allowed: {path.suffix}")

    def validate_file_content(self, content: str) -> list[str]:
        """Validate and sanitize file content.

        Args:
            content: Raw file content

        Returns:
            List of valid lines

        Raises:
            FileValidationError: If content validation fails
        """
        if not isinstance(content, str):
            raise FileValidationError("File content must be a string")

        lines = content.splitlines()

        # Check line count
        if len(lines) > self.MAX_LINES_IN_FILE:
            raise FileValidationError(
                f"Too many lines in file: {len(lines)} (max {self.MAX_LINES_IN_FILE})"
            )

        valid_lines = []
        for line_num, line in enumerate(lines, 1):
            # Remove BOM if present
            if line.startswith("\ufeff"):
                line = line[1:]

            # Basic sanitization
            line = line.strip()

            # Skip empty lines and comments
            if not line or line.startswith(("#", "//")):
                continue

            # Check for suspicious content
            try:
                self._check_for_injection(line)
            except ValidationError:
                continue  # Skip suspicious lines

            # Validate as URL
            try:
                validated_url = self.validate_url(line)
                valid_lines.append(validated_url)
            except URLValidationError:
                # Skip invalid URLs but don't raise error
                continue

        return valid_lines

    def validate_http_headers(
        self, headers: Union[dict[str, str], list[str]]
    ) -> dict[str, str]:
        """Validate HTTP headers.

        Args:
            headers: Headers as dict or list of "Name: Value" strings

        Returns:
            Validated headers dictionary

        Raises:
            HeaderValidationError: If header validation fails
        """
        if not headers:
            return {}

        if isinstance(headers, list):
            headers = self._parse_header_list(headers)
        elif not isinstance(headers, dict):
            raise HeaderValidationError("Headers must be dict or list")

        # Check header count
        if len(headers) > self.MAX_HEADER_COUNT:
            raise HeaderValidationError(
                f"Too many headers: {len(headers)} (max {self.MAX_HEADER_COUNT})"
            )

        validated_headers = {}
        for name, value in headers.items():
            # Validate header name
            if not self._is_valid_header_name(name):
                raise HeaderValidationError(f"Invalid header name: {name}")

            # Validate header value
            if not self._is_valid_header_value(value):
                raise HeaderValidationError(f"Invalid header value for {name}: {value}")

            # Check for injection attempts
            self._check_for_injection(f"{name}: {value}")

            validated_headers[name.strip()] = value.strip()

        return validated_headers

    def validate_numeric_parameter(
        self,
        value: Union[str, int, float],
        *,
        param_name: str,
        min_val: Optional[float] = None,
        max_val: Optional[float] = None,
        param_type: type = float,
    ) -> Union[int, float]:
        """Validate numeric parameters.

        Args:
            value: Value to validate
            param_name: Name of parameter (for error messages)
            min_val: Minimum allowed value
            max_val: Maximum allowed value
            param_type: Expected type (int or float)

        Returns:
            Validated numeric value

        Raises:
            ArgumentValidationError: If validation fails
        """
        if value is None:
            raise ArgumentValidationError(f"{param_name} cannot be None")

        # Convert to appropriate type
        try:
            if param_type is int:
                numeric_value = int(value)
            else:
                numeric_value = float(value)
        except (ValueError, TypeError) as e:
            raise ArgumentValidationError(f"{param_name} must be a valid number") from e

        # Check range
        if min_val is not None and numeric_value < min_val:
            raise ArgumentValidationError(
                f"{param_name} must be >= {min_val}, got {numeric_value}"
            )

        if max_val is not None and numeric_value > max_val:
            raise ArgumentValidationError(
                f"{param_name} must be <= {max_val}, got {numeric_value}"
            )

        return numeric_value

    def validate_timeout(self, timeout: Union[str, int, float]) -> float:
        """Validate timeout parameter."""
        return self.validate_numeric_parameter(
            timeout, param_name="timeout", min_val=0.1, max_val=3600.0, param_type=float
        )

    def validate_retries(self, retries: Union[str, int]) -> int:
        """Validate retries parameter."""
        result = self.validate_numeric_parameter(
            retries, param_name="retries", min_val=0, max_val=10, param_type=int
        )
        return int(result)

    def validate_workers(self, workers: Union[str, int]) -> int:
        """Validate workers parameter."""
        result = self.validate_numeric_parameter(
            workers, param_name="workers", min_val=1, max_val=100, param_type=int
        )
        return int(result)

    def validate_redirect_option(self, option: str) -> str:
        """Validate redirect handling option."""
        valid_options = {"always", "never", "http-only", "https-only"}
        if option not in valid_options:
            raise ArgumentValidationError(
                f"Invalid redirect option: {option}. Must be one of {valid_options}"
            )
        return option

    def validate_output_format(self, format_type: str) -> str:
        """Validate output format option."""
        valid_formats = {"table", "json", "csv"}
        if format_type not in valid_formats:
            raise ArgumentValidationError(
                f"Invalid output format: {format_type}. Must be one of {valid_formats}"
            )
        return format_type

    def validate_comment_style(self, style: str) -> str:
        """Validate comment style option."""
        valid_styles = {"hash", "slash", "both"}
        if style not in valid_styles:
            raise ArgumentValidationError(
                f"Invalid comment style: {style}. Must be one of {valid_styles}"
            )
        return style

    def _check_for_injection(self, text: str) -> None:
        """Check for potential injection attacks."""
        # Skip injection checks for URLs that are being auto-fixed
        if text.startswith(("http://", "https://")):
            # For URLs, only check the non-protocol part
            url_part = text.split("://", 1)[1] if "://" in text else text
            for pattern in self.compiled_injection_patterns:
                if pattern.search(url_part):
                    raise ValidationError(
                        f"Potentially malicious input detected: {text[:50]}..."
                    )
        else:
            for pattern in self.compiled_injection_patterns:
                if pattern.search(text):
                    raise ValidationError(
                        f"Potentially malicious input detected: {text[:50]}..."
                    )

    def _is_valid_hostname(self, hostname: str) -> bool:
        """Check if hostname is valid."""
        # Check for IP addresses
        try:
            ipaddress.ip_address(hostname)
            return True
        except ValueError:
            pass

        # Check for special hostnames
        if hostname in ("localhost", "localhost.localdomain"):
            return True

        # Check domain pattern
        if not self.DOMAIN_PATTERN.match(hostname):
            return False

        # Check TLD
        parts = hostname.split(".")
        if len(parts) < 2:
            return False

        tld = parts[-1]
        if not self.TLD_PATTERN.match(tld):
            return False

        return True

    def _is_valid_header_name(self, name: str) -> bool:
        """Check if HTTP header name is valid."""
        if not name or not isinstance(name, str):
            return False

        # HTTP header names are case-insensitive and can contain
        # letters, digits, and hyphens
        return re.match(r"^[A-Za-z0-9-]+$", name) is not None

    def _is_valid_header_value(self, value: str) -> bool:
        """Check if HTTP header value is valid."""
        if value is None or not isinstance(value, str):
            return False

        # Check length
        if len(value) > self.MAX_HEADER_LENGTH:
            return False

        # Check for control characters (except tab)
        for char in value:
            if ord(char) < 32 and char != "\t":
                return False

        return True

    def _parse_header_list(self, headers: list[str]) -> dict[str, str]:
        """Parse list of header strings into dictionary."""
        parsed_headers = {}

        for header in headers:
            if not isinstance(header, str):
                raise HeaderValidationError("Header must be a string")

            if ":" not in header:
                raise HeaderValidationError(f"Invalid header format: {header}")

            name, value = header.split(":", 1)
            parsed_headers[name.strip()] = value.strip()

        return parsed_headers


# Convenience functions for backward compatibility
def url_validation(site_url: str) -> str:
    """Validate URL - backward compatible function."""
    validator = InputValidator()
    return validator.validate_url(site_url)


def validate_file_path(file_path: str) -> None:
    """Validate file path - convenience function."""
    validator = InputValidator()
    validator.validate_file_input(file_path)


def parse_custom_headers(headers_list: Optional[list[str]]) -> Optional[dict[str, str]]:
    """Parse and validate custom headers - enhanced version."""
    if not headers_list:
        return None

    validator = InputValidator()
    try:
        return validator.validate_http_headers(headers_list)
    except HeaderValidationError as e:
        print(f"Warning: {e}")
        return None


def validate_arguments(args) -> None:
    """Validate command-line arguments using the InputValidator.

    Args:
        args: Parsed arguments from argparse

    Raises:
        ArgumentValidationError: If any argument is invalid
    """
    validator = InputValidator()

    _validate_numeric_args(validator, args)
    _validate_option_args(validator, args)
    _validate_header_and_site_args(validator, args)


def _validate_numeric_args(validator, args):
    """Validate numeric arguments."""
    if hasattr(args, "timeout") and args.timeout is not None:
        args.timeout = validator.validate_timeout(args.timeout)

    if hasattr(args, "retries") and args.retries is not None:
        args.retries = validator.validate_retries(args.retries)

    if hasattr(args, "workers") and args.workers is not None:
        args.workers = validator.validate_workers(args.workers)

    if hasattr(args, "retry_delay") and args.retry_delay is not None:
        args.retry_delay = validator.validate_numeric_parameter(
            args.retry_delay,
            param_name="retry_delay",
            min_val=0.0,
            max_val=60.0,
            param_type=float,
        )

    if hasattr(args, "max_redirects") and args.max_redirects is not None:
        args.max_redirects = validator.validate_numeric_parameter(
            args.max_redirects,
            param_name="max_redirects",
            min_val=0,
            max_val=50,
            param_type=int,
        )

    if hasattr(args, "tld_cache_days") and args.tld_cache_days is not None:
        args.tld_cache_days = validator.validate_numeric_parameter(
            args.tld_cache_days,
            param_name="tld_cache_days",
            min_val=1,
            max_val=365,
            param_type=int,
        )


def _validate_option_args(validator, args):
    """Validate option arguments."""
    if hasattr(args, "follow_redirects") and args.follow_redirects is not None:
        args.follow_redirects = validator.validate_redirect_option(
            args.follow_redirects
        )

    if hasattr(args, "output_format") and args.output_format is not None:
        args.output_format = validator.validate_output_format(args.output_format)

    if hasattr(args, "comment_style") and args.comment_style is not None:
        args.comment_style = validator.validate_comment_style(args.comment_style)


def _validate_header_and_site_args(validator, args):
    """Validate headers and site arguments."""
    if hasattr(args, "headers") and args.headers is not None:
        try:
            validated_headers = validator.validate_http_headers(args.headers)
            args.headers = [f"{k}: {v}" for k, v in validated_headers.items()]
        except HeaderValidationError as e:
            raise ArgumentValidationError(f"Invalid headers: {e}") from e

    if hasattr(args, "site") and args.site:
        validated_sites = []
        for site in args.site:
            try:
                validated_site = validator.validate_url(site, auto_fix=True)
                validated_sites.append(validated_site)
            except URLValidationError as e:
                raise ArgumentValidationError(f"Invalid URL '{site}': {e}") from e
        args.site = validated_sites


# Create a default validator instance
default_validator = InputValidator()
