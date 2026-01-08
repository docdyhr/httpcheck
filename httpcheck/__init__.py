"""
httpcheck - HTTP status code checker with advanced features.

A Python CLI tool for checking HTTP status codes of websites with
threading, redirect handling, TLD validation, and system notifications.
"""

__version__ = "1.4.2"
__author__ = "Thomas Juul Dyhr"
__email__ = "thomas@dyhr.com"

# Import specific items for public API
from .cli import main
from .common import VERSION, InvalidTLDException, SiteStatus
from .file_handler import FileInputHandler, url_validation
from .notification import notify
from .output_formatter import (
    format_csv,
    format_csv_list,
    format_json,
    format_json_list,
    print_format,
)
from .site_checker import check_site
from .tld_manager import TLDManager
from .validation import (
    ArgumentValidationError,
    FileValidationError,
    HeaderValidationError,
    InputValidator,
    URLValidationError,
    ValidationError,
    validate_arguments,
    validate_file_path,
)

__all__ = [
    # Core functionality
    "check_site",
    "print_format",
    "format_json",
    "format_csv",
    "format_json_list",
    "format_csv_list",
    "notify",
    "main",
    # Classes and exceptions
    "TLDManager",
    "InvalidTLDException",
    "FileInputHandler",
    "SiteStatus",
    "InputValidator",
    "ValidationError",
    "URLValidationError",
    "FileValidationError",
    "HeaderValidationError",
    "ArgumentValidationError",
    # Utilities
    "url_validation",
    "validate_file_path",
    "validate_arguments",
    "VERSION",
]
