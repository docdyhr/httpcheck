"""File input handling and URL validation for httpcheck."""

import argparse
import re
from collections.abc import Iterator
from typing import Optional

import validators

from .validation import (
    FileValidationError,
    InputValidator,
    URLValidationError,
    ValidationError,
)


def url_validation(site_url):
    """Check if url is valid and return it."""
    if not site_url.startswith(("http://", "https://")):
        site_url = f"http://{site_url}"

    if validators.url(site_url):
        return site_url
    msg = f"[-] Invalid URL: '{site_url}'"
    raise argparse.ArgumentTypeError(msg)


class FileInputHandler:
    """Handles input from domain files with enhanced security and validation.

    Features:
    - Enhanced security validation and input sanitization
    - Strips whitespace and handles empty lines
    - Supports multiple comment formats (# and //)
    - Handles inline comments
    - Performs comprehensive input validation
    - Gracefully handles malformed lines
    - File size and content validation
    - Injection attack prevention
    """

    def __init__(
        self,
        file_path: str,
        verbose: bool = False,
        comment_style: str = "both",
        strict_mode: bool = False,
    ):
        """Initialize with file path and verbosity setting.

        Args:
            file_path: Path to the file to parse
            verbose: Whether to print verbose output
            comment_style: Which comment style to recognize ('hash', 'slash', or 'both')
            strict_mode: Enable strict validation mode
        """
        self.file_path = file_path
        self.verbose = verbose
        self.comment_style = comment_style
        self.strict_mode = strict_mode
        self.line_count = 0
        self.valid_count = 0
        self.comment_count = 0
        self.empty_count = 0
        self.error_count = 0
        self.security_violations = 0

        # Initialize validator
        self.validator = InputValidator(strict_mode=strict_mode)

        # Validate comment style
        try:
            self.comment_style = self.validator.validate_comment_style(comment_style)
        except Exception as e:
            if verbose:
                print(
                    f"Warning: Invalid comment style '{comment_style}', using 'both': {e}"
                )
            self.comment_style = "both"

        # Set up comment markers based on style preference
        self.comment_markers = []
        if self.comment_style in ("hash", "both"):
            self.comment_markers.append("#")
        if self.comment_style in ("slash", "both"):
            self.comment_markers.append("//")

        # Pre-validate file
        self._validate_file_access()

    def parse(self) -> Iterator[str]:
        """Parse the input file and yield valid URLs with enhanced security validation."""
        try:
            # Read file with encoding detection and security validation
            content = self._read_file_safely()

            # Process line by line to maintain statistics and backward compatibility
            for line_num, line in enumerate(content.splitlines(), 1):
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
                    f"  Security violations: {self.security_violations}\n"
                )
                print(summary)

        except FileValidationError as e:
            print(f"[-] File validation error: {str(e)}")
        except OSError as e:
            print(f"[-] Error reading file {self.file_path}: {str(e)}")

    def _validate_file_access(self) -> None:
        """Pre-validate file accessibility and security."""
        try:
            self.validator.validate_file_input(self.file_path)
        except FileValidationError as e:
            if self.verbose:
                print(f"[-] File validation warning: {str(e)}")
            # Don't raise here to maintain backward compatibility

    def _read_file_safely(self) -> str:
        """Read file with enhanced security and encoding detection."""
        try:
            with open(self.file_path, encoding="utf-8") as f:
                return f.read()
        except UnicodeDecodeError:
            try:
                with open(self.file_path, encoding="latin-1") as f:
                    if self.verbose:
                        print(
                            f"Warning: File {self.file_path} decoded with latin-1 encoding"
                        )
                    return f.read()
            except UnicodeDecodeError as e:
                raise FileValidationError(
                    f"Could not decode file {self.file_path}"
                ) from e

    def _process_line(self, line: str, line_num: int) -> Optional[str]:
        """Process a single line from the input file with enhanced validation."""
        # Remove whitespace and BOM
        cleaned_line = self._clean_line(line)
        if not cleaned_line:
            return None

        # Security check for potentially malicious content
        if not self._check_security(cleaned_line, line_num):
            return None

        # Handle comments
        processed_line = self._handle_comments(cleaned_line)
        if not processed_line:
            return None

        # Apply enhanced URL validation
        return self._validate_url(processed_line, line_num)

    def _clean_line(self, line: str) -> Optional[str]:
        """Clean line by removing whitespace and BOM."""
        line = line.strip()
        if line.startswith("\ufeff"):
            line = line[1:]

        if not line:
            self.empty_count += 1
            return None
        return line

    def _check_security(self, line: str, line_num: int) -> bool:
        """Check for security violations in the line."""
        try:
            for pattern in self.validator.compiled_injection_patterns:
                if pattern.search(line):
                    raise ValidationError("Potentially malicious input detected")
            return True
        except Exception:
            self.security_violations += 1
            if self.verbose:
                print(f"[-] Line {line_num}: Security violation detected, skipping")
            return False

    def _handle_comments(self, line: str) -> Optional[str]:
        """Handle comment markers and remove comments from line."""
        # Handle full line comments
        for marker in self.comment_markers:
            if line.startswith(marker):
                self.comment_count += 1
                return None

        # Handle inline comments
        comment_pos = self._find_comment_position(line)
        if comment_pos > 0:
            line = line[:comment_pos].strip()
            self.comment_count += 1

        if not line:
            self.empty_count += 1
            return None
        return line

    def _find_comment_position(self, line: str) -> int:
        """Find the position of the first valid comment marker."""
        comment_pos = -1
        for marker in self.comment_markers:
            pos = line.find(marker)
            if pos > 0 and (comment_pos == -1 or pos < comment_pos):
                if marker == "//" and self._is_protocol_part(line, pos):
                    continue
                comment_pos = pos
        return comment_pos

    def _is_protocol_part(self, line: str, pos: int) -> bool:
        """Check if // is part of a protocol (http://, https://, ftp://)."""
        prefix = line[:pos].rstrip()
        return prefix.endswith(("http:", "https:", "ftp:"))

    def _validate_url(self, line: str, line_num: int) -> Optional[str]:
        """Validate and return URL or None if invalid."""
        try:
            validated_url = self.validator.validate_url(line, auto_fix=True)
            self.valid_count += 1
            return validated_url
        except URLValidationError as e:
            if self.verbose:
                print(f"[-] Line {line_num}: Invalid URL '{line}' - {str(e)}")
            self.error_count += 1
            return None
